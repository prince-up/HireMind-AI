from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uuid
import os
from datetime import datetime

router = APIRouter(prefix="/interview", tags=["interview"])

# Simple in-memory session store for MVP
SESSIONS = {}


class StartRequest(BaseModel):
    user_name: Optional[str] = None


class StartResponse(BaseModel):
    sessionId: str
    message: str


class MessageRequest(BaseModel):
    sessionId: str
    message: str


class MessageResponse(BaseModel):
    reply: str
    follow_up: Optional[str] = None


@router.post("/start", response_model=StartResponse)
def start_interview(req: StartRequest):
    sid = str(uuid.uuid4())
    SESSIONS[sid] = {
        "started": datetime.utcnow().isoformat(),
        "history": [],
        "user_name": req.user_name,
    }
    return StartResponse(sessionId=sid, message="Interview started")


def _generate_question_from_gemini(prompt: str) -> str:
    # Placeholder: integrate with Google Gemini SDK if available and configured
    try:
        import google.generativeai as genai

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("No GOOGLE_API_KEY configured")

        genai.configure(api_key=api_key)
        # Use a conservative prompt to request a single targeted follow-up question
        system = (
            "You are a senior technical interviewer. Ask one concise, targeted follow-up question "
            "based on the candidate's recent answers. Keep it short (<= 25 words), technical, and relevant. "
            "Do not produce multiple questions."
        )
        response = genai.generate_text(model="gemini-1.0", prompt=system + "\n" + prompt)
        # genai returns different shapes; try to extract text
        text = getattr(response, "text", None) or (response.get("candidates") and response["candidates"][0].get("content"))
        return text or "Can you explain that in more detail?"
    except Exception as e:
        # Fallback heuristic
        return "Can you explain that in more detail?"


@router.post("/message", response_model=MessageResponse)
def message(req: MessageRequest):
    sid = req.sessionId
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    SESSIONS[sid]["history"].append({"role": "You", "text": req.message, "ts": datetime.utcnow().isoformat()})

    # create a prompt using conversation context
    recent = "\n".join([h["text"] for h in SESSIONS[sid]["history"][-5:]])
    prompt = f"You are a senior technical interviewer. Based on the candidate's answers: {recent}\nAsk one targeted follow-up question."
    reply = _generate_question_from_gemini(prompt)

    SESSIONS[sid]["history"].append({"role": "AI", "text": reply, "ts": datetime.utcnow().isoformat()})

    return MessageResponse(reply=reply)
