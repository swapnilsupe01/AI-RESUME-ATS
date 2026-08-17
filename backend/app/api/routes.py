"""
AI Resume ATS — FastAPI API Routes.
Endpoints:
  POST /api/analyze  — Upload resume PDF + JD text, returns ATS report JSON
  GET  /api/health   — Health check
"""
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from app.parser.pdf_parser import extract_text_from_bytes
from app.scoring.ats_scorer import calculate_ats_score

router = APIRouter(prefix="/api")


@router.get("/health")
async def health_check():
    """Returns server health status."""
    return {"status": "ok", "service": "AI Resume ATS"}


@router.post("/analyze")
async def analyze_resume(
    resume_file: UploadFile = File(..., description="Resume PDF file"),
    jd_text: str = Form(..., description="Job Description plain text"),
):
    """
    Analyze a resume PDF against a job description.

    - **resume_file**: PDF file upload (multipart/form-data)
    - **jd_text**: Raw job description text

    Returns a comprehensive ATS evaluation report including:
    - Overall ATS score & match level
    - Skill match analysis (matched + missing skills)
    - Semantic embedding similarity score
    - TF-IDF and N-Gram similarity breakdowns
    - Section structure score
    - Actionable improvement recommendations
    """
    # Validate file type
    if not resume_file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported. Please upload a valid .pdf resume."
        )

    if not jd_text or not jd_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Job Description text cannot be empty."
        )

    # Read PDF bytes
    try:
        pdf_bytes = await resume_file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")

    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded PDF file is empty.")

    # Extract text from PDF
    try:
        resume_text = extract_text_from_bytes(pdf_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract text from PDF: {str(e)}. Ensure the PDF contains selectable text (not a scanned image)."
        )

    if not resume_text or not resume_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text found in the uploaded PDF. Ensure the PDF is not image-only or password-protected."
        )

    # Run ATS scoring engine
    try:
        report = calculate_ats_score(resume_text, jd_text.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ATS scoring engine error: {str(e)}")

    return JSONResponse(content=report)
