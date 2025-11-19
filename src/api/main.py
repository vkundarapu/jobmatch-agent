from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict
from pathlib import Path
import io
from pypdf import PdfReader

from ..agent import run_jobmatch_agent

app = FastAPI(title="JobMatch Agent API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobMatchRequest(BaseModel):
    jd_text: str
    resume_text: str


@app.post("/api/jobmatch")
def jobmatch_endpoint(payload: JobMatchRequest) -> Dict[str, Any]:
    """Legacy JSON endpoint (still useful for testing)."""
    result = run_jobmatch_agent(
        jd_text=payload.jd_text,
        resume_text=payload.resume_text,
    )
    jd = result["jd"]
    resume = result["resume"]
    match = result["match"]
    advice = result.get("advice", {})

    return {
        "match": match,
        "jd": {
            "title": jd.title,
            "company": jd.company,
            "location": jd.location,
            "required_skills": jd.required_skills,
            "nice_to_have_skills": jd.nice_to_have_skills,
            "responsibilities": jd.responsibilities,
            "keywords": jd.keywords,
        },
        "resume": {
            "name": resume.name,
            "headline": resume.headline,
            "skills": resume.skills,
            "tools": resume.tools,
        },
        "advice": advice,
    }


@app.post("/api/jobmatch_pdf")
async def jobmatch_pdf_endpoint(
    jd_text: str = Form(...),
    resume_file: UploadFile = File(...),
) -> Dict[str, Any]:
    """
    New endpoint: accepts a job description string + a PDF resume upload.
    """
    if resume_file.content_type not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF resumes are supported.",
        )

    contents = await resume_file.read()

    try:
        reader = PdfReader(io.BytesIO(contents))
        extracted_text = "\n\n".join(
            (page.extract_text() or "") for page in reader.pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read PDF: {e}",
        )

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract any text from the PDF. "
                   "Make sure it is not a scanned image-only resume.",
        )

    result = run_jobmatch_agent(
        jd_text=jd_text,
        resume_text=extracted_text,
    )

    jd = result["jd"]
    resume = result["resume"]
    match = result["match"]
    advice = result.get("advice", {})

    return {
        "match": match,
        "jd": {
            "title": jd.title,
            "company": jd.company,
            "location": jd.location,
            "required_skills": jd.required_skills,
            "nice_to_have_skills": jd.nice_to_have_skills,
            "responsibilities": jd.responsibilities,
            "keywords": jd.keywords,
        },
        "resume": {
            "name": resume.name,
            "headline": resume.headline,
            "skills": resume.skills,
            "tools": resume.tools,
        },
        "advice": advice,
    }
