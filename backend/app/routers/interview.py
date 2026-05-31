from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import os
import json
import re
from datetime import datetime
from difflib import SequenceMatcher

from ..db import SessionLocal, init_db
from sqlalchemy.orm import Session
from .. import models

init_db()

router = APIRouter(prefix="/interview", tags=["interview"])

# Note: we keep an in-memory map for quick lookups but persist interviews/messages in SQLite
SESSIONS: Dict[str, Dict[str, Any]] = {}

GENERIC_FOLLOWUPS = [
    "Can you walk me through one project from your resume?",
    "What was your exact contribution in that project?",
    "Which technical challenge there was hardest to solve?",
    "What tools or technologies did you use most there?",
    "How did you measure the impact of that work?",
    "What would you improve if you built it again?",
]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class StartRequest(BaseModel):
    user_name: Optional[str] = None
    resume_id: Optional[str] = None


class StartResponse(BaseModel):
    sessionId: str
    message: str
    initial_question: str


class RetrieveResponse(BaseModel):
    contexts: List[Dict[str, Any]]


class MessageRequest(BaseModel):
    sessionId: str
    message: str


class MessageResponse(BaseModel):
    reply: str
    follow_up: Optional[str] = None


def _normalize_question(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def _looks_repeated(candidate: str, asked_questions: List[str]) -> bool:
    candidate_norm = _normalize_question(candidate)
    if not candidate_norm:
        return True

    for previous in asked_questions:
        previous_norm = _normalize_question(previous)
        if not previous_norm:
            continue
        if candidate_norm == previous_norm:
            return True
        if SequenceMatcher(None, candidate_norm, previous_norm).ratio() >= 0.84:
            return True

    return False


def _fallback_question(asked_questions: List[str]) -> str:
    index = len(asked_questions) % len(GENERIC_FOLLOWUPS)
    for offset in range(len(GENERIC_FOLLOWUPS)):
        candidate = GENERIC_FOLLOWUPS[(index + offset) % len(GENERIC_FOLLOWUPS)]
        if not _looks_repeated(candidate, asked_questions):
            return candidate
    return GENERIC_FOLLOWUPS[0]


def _extract_question_text(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""

    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE).strip()
    if cleaned.startswith("{"):
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                value = parsed.get("question") or parsed.get("reply") or parsed.get("text")
                if isinstance(value, str):
                    cleaned = value.strip()
        except Exception:
            pass

    # Do not strip out context sentences. Just return the whole cleaned text.
    # If the LLM generates multiple sentences, we want them all to make sense of the question.
    return cleaned


@router.post("/start", response_model=StartResponse)
def start_interview(req: StartRequest, db: Session = Depends(get_db)):
    sid = str(uuid.uuid4())
    # create DB interview record
    interview = models.Interview(session_uuid=sid, user_name=req.user_name)
    if req.resume_id:
        # try to associate resume DB row by resume_id
        res = db.query(models.Resume).filter(models.Resume.resume_id == req.resume_id).first()
        if res:
            interview.resume_id = res.id
    db.add(interview)
    db.commit()
    db.refresh(interview)

    initial_question = _compose_initial_question(db, req.resume_id, req.user_name)

    SESSIONS[sid] = {
        "started": datetime.utcnow().isoformat(),
        "history": [{"role": "AI", "text": initial_question, "ts": datetime.utcnow().isoformat()}],
        "user_name": req.user_name,
        "resume_id": req.resume_id,
        "interview_id": interview.id,
        "asked_questions": [initial_question],
    }

    try:
        db.add(models.Message(interview_id=interview.id, role="AI", text=initial_question))
        db.commit()
    except Exception as e:
        print("DB save initial AI message failed:", e)

    return StartResponse(sessionId=sid, message="Interview started", initial_question=initial_question)


def _generate_question_from_gemini(prompt: str, asked_questions: Optional[List[str]] = None) -> str:
    asked_questions = asked_questions or []
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("_generate_question_from_gemini: no GOOGLE_API_KEY set, using fallback")
        return _fallback_question(asked_questions)

    try:
        import google.generativeai as genai
    except Exception as e:
        print("_generate_question_from_gemini: genai import failed:", e)
        return _fallback_question(asked_questions)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Try a few times to get a non-repeated, valid question
    attempt = 0
    last_err = None
    while attempt < 3:
        attempt += 1
        try:
            tweak = ""
            if attempt > 1:
                tweak = "\nPlease ask a different question than previously asked. Keep it concise."

            response = model.generate_content(
                prompt + tweak,
                generation_config={
                    "temperature": 0.85,
                    "top_p": 0.95,
                    "max_output_tokens": 150,
                },
            )
            raw = getattr(response, "text", None) or getattr(response, "content", None) or ""
            text = _extract_question_text(raw)
            if not text:
                last_err = "empty text"
                continue
            if _looks_repeated(text, asked_questions):
                last_err = f"repeated: {text}"
                continue
            if not text.endswith("?"):
                text = f"{text}?"
            return text
        except Exception as e:
            print(f"Gemini attempt {attempt} failed:", e)
            last_err = str(e)
            continue

    print("Gemini failed after attempts, last error:", last_err)
    return _fallback_question(asked_questions)


def _compose_initial_question(db: Session, resume_id: Optional[str], user_name: Optional[str]) -> str:
    if resume_id:
        resume = db.query(models.Resume).filter(models.Resume.resume_id == resume_id).first()
        if resume:
            chunks = (
                db.query(models.ResumeChunk)
                .filter(models.ResumeChunk.resume_id == resume.id)
                .order_by(models.ResumeChunk.chunk_index.asc())
                .limit(4)
                .all()
            )
            resume_context = "\n".join(chunk.text for chunk in chunks if chunk.text) or (resume.raw_text or "")
            prompt = (
                "You are a robot-like interview assistant. Ask one short, friendly first interview question based on the candidate resume. "
                "Keep it direct, natural, and specific to the resume. Do not mention that you are an AI.\n"
                f"Candidate name: {user_name or 'Unknown'}\n"
                f"Resume context:\n{resume_context[:2500]}"
            )
            return _generate_question_from_gemini(prompt, asked_questions=[])

    return "Tell me about yourself and the role you are preparing for."


@router.post("/message", response_model=MessageResponse)
def message(req: MessageRequest):
    sid = req.sessionId
    if sid not in SESSIONS:
        try:
            db = next(get_db())
            interview = db.query(models.Interview).filter(models.Interview.session_uuid == sid).first()
            if not interview:
                raise HTTPException(status_code=404, detail="Session not found in DB")
                
            # Reconstruct session
            messages = db.query(models.Message).filter(models.Message.interview_id == interview.id).order_by(models.Message.id.asc()).all()
            history = []
            asked_qs = []
            for m in messages:
                history.append({"role": m.role, "text": m.text, "ts": datetime.utcnow().isoformat()})
                if m.role == "AI":
                    asked_qs.append(m.text)
            
            # Find associated resume
            resume_uuid = None
            if interview.resume_id:
                res = db.query(models.Resume).filter(models.Resume.id == interview.resume_id).first()
                if res:
                    resume_uuid = res.resume_id
                    
            SESSIONS[sid] = {
                "started": datetime.utcnow().isoformat(),
                "history": history,
                "user_name": interview.user_name,
                "resume_id": resume_uuid,
                "interview_id": interview.id,
                "asked_questions": asked_qs,
            }
        except Exception as e:
            print("Session recovery failed:", e)
            raise HTTPException(status_code=404, detail="Session not found and recovery failed")

    SESSIONS[sid]["history"].append({"role": "You", "text": req.message, "ts": datetime.utcnow().isoformat()})
    SESSIONS[sid].setdefault("asked_questions", [])
    # persist message to DB
    interview_id = SESSIONS[sid].get("interview_id")
    if interview_id:
        try:
            db = next(get_db())
            msg = models.Message(interview_id=interview_id, role="You", text=req.message)
            db.add(msg)
            db.commit()
        except Exception as e:
            print("DB save message failed:", e)

    # retrieve resume context if available
    resume_id = SESSIONS[sid].get("resume_id")
    retrieved = []
    if resume_id:
        try:
            from ..services import rag as ragsvc
            retrieved = ragsvc.retrieve(req.message, top_k=5)
        except Exception as e:
            print("RAG retrieval failed:", e)

    context_text = "\n\n".join([r.get("text") for r in retrieved])
    asked_questions = [item["text"] for item in SESSIONS[sid]["history"] if item["role"] == "AI"]

    # Format the entire conversation nicely for better context
    conversation_str = "\n".join([f"{h['role']}: {h['text']}" for h in SESSIONS[sid]["history"]])

    prompt = (
        "You are a senior technical interviewer conducting a voice interview. "
        "First, briefly acknowledge and evaluate the candidate's previous answer (e.g., 'That's a great explanation', 'You are correct', or gently correct them if they are wrong). "
        "Then, ask a completely NEW and targeted cross-question based directly on what they just said, or from their resume context. "
        "CRITICAL RULE: DO NOT ask about a topic or project that has already been asked about. Look closely at the 'Already asked questions' list and avoid those subjects entirely.\n"
    )
    if context_text:
        prompt += f"\nResume context:\n{context_text}\n"
    
    prompt += f"\nAlready asked questions:\n" + "\n".join(f"- {q}" for q in asked_questions)
    prompt += f"\n\nFull Conversation History:\n{conversation_str}\n\nCandidate last said: {req.message}\n\nAsk one concise, completely new follow-up question."
    
    reply = _generate_question_from_gemini(prompt, asked_questions=asked_questions)
    if _looks_repeated(reply, asked_questions):
        reply = _fallback_question(asked_questions)

    SESSIONS[sid]["history"].append({"role": "AI", "text": reply, "ts": datetime.utcnow().isoformat()})
    SESSIONS[sid]["asked_questions"].append(reply)
    # persist AI message
    if interview_id:
        try:
            db = next(get_db())
            msg = models.Message(interview_id=interview_id, role="AI", text=reply)
            db.add(msg)
            db.commit()
        except Exception as e:
            print("DB save AI message failed:", e)

    return MessageResponse(reply=reply)
