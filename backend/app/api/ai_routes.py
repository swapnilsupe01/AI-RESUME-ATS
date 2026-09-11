"""
AI Assistant & Canonical Resume API Routes.
Provides endpoints for:
  - POST /api/ai/parse-to-canvas: Ingest PDF or text, returns Canonical Resume JSON + Markdown
  - GET  /api/ai/resume/schema: Returns the Canonical Resume JSON Schema
  - GET  /api/ai/resume/sample: Returns a rich synthetic sample Canonical Resume JSON
  - POST /api/ai/optimize-bullet: Optimize a single bullet (action_verb, star_metric, polish, jd_inject, full)
  - POST /api/ai/live-keyword-audit: Real-time keyword gap analysis between resume text and JD
  - POST /api/ai/tailor-resume: Generate tailored bullets for a specific job description
  - GET  /api/ai/provider-info: Returns current active AI provider info
"""
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse, Response
from typing import Optional, List
import json

from app.models.canonical_resume import CanonicalResume
from app.parser.canonical_parser import (
    parse_pdf_bytes_to_canonical, parse_text_to_canonical, get_synthetic_sample_resume
)
from app.parser.pdf_generator import pdf_generator
from app.ai.factory import get_provider

router = APIRouter(prefix="/api/ai", tags=["AI Resume Intelligence"])


@router.get("/resume/schema")
async def get_resume_schema():
    """Returns the Canonical Resume JSON Schema for client synchronization."""
    return JSONResponse(content=CanonicalResume.model_json_schema())


@router.get("/resume/sample")
async def get_sample_resume():
    """Returns a rich synthetic demonstration resume in Canonical JSON + Markdown format."""
    sample = get_synthetic_sample_resume()
    from app.parser.markdown_pipeline import canonical_to_markdown
    return JSONResponse(content={
        "status": "success",
        "canonical_resume": sample.model_dump(),
        "markdown_text": canonical_to_markdown(sample)
    })


@router.post("/parse-to-canvas")
async def parse_to_canvas(
    resume_file: Optional[UploadFile] = File(None, description="Optional resume PDF file"),
    resume_text: Optional[str] = Form(None, description="Optional raw resume text or Markdown"),
    additional_links: Optional[str] = Form(None, description="Comma-separated external URLs")
):
    """
    Parse uploaded PDF or raw text into Canonical Resume JSON and clean Markdown.
    Never hallucinates unprovided data; returns warnings when sections cannot be parsed.
    """
    links_list: List[str] = []
    if additional_links and additional_links.strip():
        links_list = [l.strip() for l in additional_links.split(",") if l.strip()]

    if resume_file:
        if not resume_file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported for resume file upload.")
        try:
            pdf_bytes = await resume_file.read()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read PDF file: {str(e)}")

        resume_obj, md_text, warnings = parse_pdf_bytes_to_canonical(pdf_bytes, additional_links=links_list)

    elif resume_text and resume_text.strip():
        resume_obj, md_text, warnings = parse_text_to_canonical(resume_text.strip(), additional_links=links_list)

    else:
        raise HTTPException(
            status_code=400,
            detail="Please provide either a resume PDF file or resume text/markdown to parse."
        )

    return JSONResponse(content={
        "status": "success",
        "canonical_resume": resume_obj.model_dump(),
        "markdown_text": md_text,
        "warnings": warnings,
        "confidence_score": max(20.0, 100.0 - len(warnings) * 15.0)
    })


@router.post("/optimize-bullet")
async def optimize_bullet(
    bullet_text: str = Form(..., description="The original bullet point text to optimize"),
    mode: str = Form("full", description="Optimization mode: action_verb | star_metric | polish | jd_inject | full"),
    jd_keywords: Optional[str] = Form(None, description="Comma-separated JD keywords for jd_inject mode")
):
    """
    Optimize a single resume bullet point using the active AI provider.
    Modes:
    - action_verb: Replace weak verbs with power action verbs
    - star_metric: Inject quantification placeholders
    - polish: Remove filler words and passive voice
    - jd_inject: Insert relevant JD keywords
    - full: Apply all modes sequentially
    """
    valid_modes = {"action_verb", "star_metric", "polish", "jd_inject", "full"}
    if mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Choose from: {', '.join(valid_modes)}")

    if not bullet_text.strip():
        raise HTTPException(status_code=400, detail="bullet_text cannot be empty.")

    context = {}
    if jd_keywords and jd_keywords.strip():
        context["jd_keywords"] = [kw.strip() for kw in jd_keywords.split(",") if kw.strip()]

    provider = get_provider()
    result = provider.optimize_bullet(bullet_text, mode, context)

    return JSONResponse(content={
        "status": "success",
        "provider": provider.get_provider_name(),
        **result
    })


@router.post("/live-keyword-audit")
async def live_keyword_audit(
    resume_text: str = Form(..., description="Full resume text or Markdown"),
    jd_text: str = Form(..., description="Full job description text")
):
    """
    Perform a real-time keyword gap audit between the resume and job description.
    Returns matched keywords, critical gaps, keyword density, and recommendations.
    """
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="resume_text cannot be empty.")
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text cannot be empty.")

    provider = get_provider()
    audit_result = provider.live_keyword_audit(resume_text, jd_text)

    return JSONResponse(content={
        "status": "success",
        "provider": provider.get_provider_name(),
        **audit_result
    })


@router.post("/tailor-resume")
async def tailor_resume(
    canonical_resume_json: str = Form(..., description="Canonical Resume JSON string"),
    jd_text: str = Form(..., description="Target job description text")
):
    """
    Generate a tailored version of the resume for a specific job description.
    Returns per-section tailored bullets, keyword suggestions, and tailoring score.
    """
    if not canonical_resume_json.strip():
        raise HTTPException(status_code=400, detail="canonical_resume_json cannot be empty.")
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text cannot be empty.")

    try:
        canonical_data = json.loads(canonical_resume_json)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid canonical_resume_json: {str(e)}")

    provider = get_provider()
    result = provider.tailor_resume(canonical_data, jd_text)

    return JSONResponse(content={
        "status": "success",
        "provider": provider.get_provider_name(),
        **result
    })


@router.get("/provider-info")
async def get_provider_info():
    """Returns the name and availability of the currently active AI provider and Ollama."""
    import os
    provider = get_provider()

    ollama_online = False
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        import httpx
        with httpx.Client(timeout=0.6) as client:
            r = client.get(f"{ollama_url}/api/tags")
            ollama_online = (r.status_code == 200)
    except Exception:
        ollama_online = False

    return JSONResponse(content={
        "provider_name": provider.get_provider_name(),
        "is_available": provider.is_available(),
        "ollama_online": ollama_online,
        "ollama_url": ollama_url,
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3"),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY", "")),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY", ""))
    })


@router.post("/diagnose")
async def diagnose_cv(
    resume_text: str = Form(..., description="Full resume text"),
    jd_text: str = Form(..., description="Target Job Description text")
):
    """
    Comprehensive CV diagnostics: identifies weak action verbs, unquantified bullets,
    missing target job skills, and structural gaps.
    """
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="resume_text cannot be empty.")
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text cannot be empty.")

    provider = get_provider()
    diagnostics = provider.diagnose_cv_weaknesses(resume_text, jd_text)

    return JSONResponse(content={
        "status": "success",
        "provider": provider.get_provider_name(),
        **diagnostics
    })


@router.post("/transform-cv")
async def transform_cv(
    canonical_resume_json: str = Form(..., description="Canonical Resume JSON string"),
    jd_text: str = Form(..., description="Target Job Description text")
):
    """
    Transforms the resume using Sentence-BERT RAG knowledge base:
    - Restructures sentences into high-impact STAR phrasing
    - Upgrades weak action verbs to strong technical leadership verbs
    - Enhances Professional Summary
    - Strict Anti-Hallucination: Never invents tools not present in candidate's background.
    """
    if not canonical_resume_json.strip():
        raise HTTPException(status_code=400, detail="canonical_resume_json cannot be empty.")
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text cannot be empty.")

    try:
        canonical_data = json.loads(canonical_resume_json)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid canonical_resume_json: {str(e)}")

    provider = get_provider()
    result = provider.transform_entire_resume(canonical_data, jd_text)

    return JSONResponse(content={
        "status": "success",
        "provider": provider.get_provider_name(),
        **result
    })


@router.post("/generate-pdf")
async def generate_enhanced_pdf(
    canonical_resume_json: str = Form(..., description="Canonical or structured resume JSON string")
):
    """
    Renders the enhanced resume into an ATS-compliant, single-column downloadable PDF.
    """
    if not canonical_resume_json.strip():
        raise HTTPException(status_code=400, detail="canonical_resume_json cannot be empty.")

    try:
        resume_data = json.loads(canonical_resume_json)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    pdf_bytes = pdf_generator.generate_pdf(resume_data)

    candidate_name = resume_data.get("candidate_name", "Enhanced").replace(" ", "_")
    filename = f"{candidate_name}_ATS_Enhanced_Resume.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Cache-Control": "no-cache"
        }
    )


@router.post("/compare-scores")
async def compare_scores(
    original_text: str = Form(..., description="Original resume plain text"),
    enhanced_text: str = Form(..., description="Enhanced resume plain text"),
    jd_text: str = Form(..., description="Target Job Description text")
):
    """
    Computes Before vs After ATS score comparison against the same JD.
    Returns overall score jump, metric deltas, and list of resolved weaknesses.
    """
    if not original_text.strip() or not enhanced_text.strip():
        raise HTTPException(status_code=400, detail="original_text and enhanced_text cannot be empty.")
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text cannot be empty.")

    provider = get_provider()
    comparison = provider.compare_cv_scores(original_text, enhanced_text, jd_text)

    return JSONResponse(content={
        "status": "success",
        "provider": provider.get_provider_name(),
        **comparison
    })
