from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import fitz  # PyMuPDF
import tempfile
import os
import re
from ..services import rag
from ..db import SessionLocal, init_db
from .. import models

init_db()
import uuid


router = APIRouter(prefix="/resume", tags=["resume"])


class ResumeParseResponse(BaseModel):
    skills: List[str]
    projects: List[str]
    education: List[str]
    experience: List[str]
    rawText: str
    resume_id: Optional[str] = None


@router.post("/upload", response_model=ResumeParseResponse)
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files supported")

    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        doc = fitz.open(tmp_path)
        text = "\n".join([p.get_text() for p in doc])

        # naive extraction heuristics
        skills = re.findall(r"Skills[:\n\r]+([\s\S]*?)(?:\n\n|Experience|Education|Projects|$)", text, flags=re.IGNORECASE)
        skills_list = []
        if skills:
            # split by commas or newlines
            skills_list = re.split(r"[;,\n]",
                                   skills[0])
            skills_list = [s.strip() for s in skills_list if s.strip()]

        # projects/education/experience simple section splits
        def extract_section(name):
            m = re.findall(rf"{name}[:\n\r]*([\s\S]*?)(?:\n\n|$)", text, flags=re.IGNORECASE)
            if not m:
                return []
            # take lines
            lines = [l.strip() for l in m[0].splitlines() if l.strip()]
            return lines[:10]

        projects = extract_section("Projects")
        education = extract_section("Education")
        experience = extract_section("Experience")

        # persist resume to DB
        db = SessionLocal()
        resume_uuid = str(uuid.uuid4())
        resume_row = models.Resume(resume_id=resume_uuid, filename=file.filename, raw_text=text)
        db.add(resume_row)
        db.commit()
        db.refresh(resume_row)

        # store chunks in DB as well
        chunks = rag.chunk_text(text)
        for idx, chunk in enumerate(chunks):
            rc = models.ResumeChunk(resume_id=resume_row.id, chunk_index=idx, text=chunk)
            db.add(rc)
        db.commit()

        # index into vector store (async/optional)
        try:
            rag.index_resume(resume_uuid, text)
        except Exception as e:
            print("RAG indexing failed:", e)

        return ResumeParseResponse(
            skills=skills_list,
            projects=projects,
            education=education,
            experience=experience,
            rawText=text,
            resume_id=resume_uuid,
        )
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
