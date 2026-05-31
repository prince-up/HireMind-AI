from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import fitz  # PyMuPDF
import tempfile
import os
import re

router = APIRouter(prefix="/resume", tags=["resume"])


class ResumeParseResponse(BaseModel):
    skills: List[str]
    projects: List[str]
    education: List[str]
    experience: List[str]
    rawText: str


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

        return ResumeParseResponse(
            skills=skills_list,
            projects=projects,
            education=education,
            experience=experience,
            rawText=text,
        )
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
