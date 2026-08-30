"""
AI Resume ATS — Explainable Resume & Project Intelligence API Routes.
Endpoints:
  POST /api/analyze        — Upload resume PDF + JD text, returns Multi-Source Intelligence Report JSON
  POST /api/verify-project — Verify project claims directly against public GitHub repo
  GET  /api/sample-data    — Retrieve pre-loaded sample resume & JD for quick demo
  GET  /api/health         — Health check endpoint
"""
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List

from app.parser.pdf_parser import extract_text_from_bytes
from app.scoring.final_scorer import analyze_resume_intelligence
from app.evidence.github_analyzer import fetch_github_repo_evidence
from app.evidence.project_verifier import verify_project_claims

router = APIRouter(prefix="/api")

@router.get("/health")
async def health_check():
    """Health check endpoint for Docker, Kubernetes, and Jenkins smoke tests."""
    return {
        "status": "ok",
        "service": "AI Resume & Multi-Source Project Intelligence ATS",
        "version": "2.1.0",
        "models": ["Sentence-BERT (all-MiniLM-L6-v2)", "GitHub Multi-Repo Discovery", "LinkedIn Career Intelligence", "TF-IDF", "N-Gram"]
    }

@router.get("/sample-data")
async def get_sample_data():
    """Returns sample pre-filled JD and candidate profiles for instant UI demonstration."""
    sample_jd = """Machine Learning Engineer

We are seeking a skilled Machine Learning Engineer to join our AI team.

Required Skills & Experience:
• Strong expertise in Python programming
• Experience building REST APIs with FastAPI or Flask
• Solid understanding of Machine Learning algorithms, NLP (Natural Language Processing), and Deep Learning
• Proficiency with SQL and relational databases
• Familiarity with containerization using Docker and deployment on AWS (Amazon Web Services)
• Practical knowledge of Git, Linux, PyTorch, and scikit-learn
• Bachelor's degree in Computer Engineering, Computer Science, or related field

Key Responsibilities:
• Design, train, and evaluate NLP models and feature extraction algorithms (TF-IDF, Embeddings)
• Integrate ML models into production REST API microservices
• Collaborate with software developers and cloud infrastructure teams"""

    return {
        "sample_jd": sample_jd,
        "sample_candidate_summary": "Swapnil Supe - ML Engineer (Includes GitHub multi-repo & LinkedIn profile)",
        "sample_github_repo": "https://github.com/swapnilsupe01",
        "sample_linkedin_url": "https://linkedin.com/in/swapnilsupe01"
    }

@router.post("/analyze")
async def analyze_resume(
    resume_file: UploadFile = File(..., description="Resume PDF file"),
    jd_text: str = Form(..., description="Job Description plain text"),
    github_url: Optional[str] = Form(None, description="Optional explicit GitHub profile or repository URL"),
    linkedin_url: Optional[str] = Form(None, description="Optional explicit LinkedIn profile URL"),
    portfolio_url: Optional[str] = Form(None, description="Optional explicit Portfolio URL")
):
    """
    Analyze a resume PDF against a job description and verify public GitHub & LinkedIn evidence.
    """
    # 1. Validate file extension
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

    # 2. Read PDF bytes
    try:
        pdf_bytes = await resume_file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")

    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded PDF file is empty.")

    # 3. Extract text from PDF
    try:
        resume_text = extract_text_from_bytes(pdf_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract text from PDF: {str(e)}. Ensure the PDF contains selectable text."
        )

    if not resume_text or not resume_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text found in the uploaded PDF. Ensure the PDF is not image-only or password-protected."
        )

    override_gh = [github_url.strip()] if github_url and github_url.strip() else []
    override_li = [linkedin_url.strip()] if linkedin_url and linkedin_url.strip() else []
    override_pf = [portfolio_url.strip()] if portfolio_url and portfolio_url.strip() else []

    # 4. Run Multi-Source Intelligence Engine
    try:
        report = await analyze_resume_intelligence(
            resume_text=resume_text,
            jd_text=jd_text.strip(),
            override_github_urls=override_gh,
            override_linkedin_urls=override_li,
            override_portfolio_urls=override_pf
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intelligence engine error: {str(e)}")

    return JSONResponse(content=report)

@router.post("/verify-project")
async def verify_single_project(
    github_url: str = Form(..., description="GitHub repository URL"),
    project_title: str = Form(..., description="Project Title"),
    claimed_technologies: str = Form(..., description="Comma-separated list of claimed technologies")
):
    """
    Directly verify claimed technical skills against a public GitHub repository.
    """
    if not github_url or "github.com" not in github_url:
        raise HTTPException(status_code=400, detail="Valid GitHub URL is required.")

    from app.evidence.url_extractor import parse_github_url
    parsed = parse_github_url(github_url)
    if not parsed or parsed.get("type") != "repository":
        raise HTTPException(status_code=400, detail="Please provide a valid GitHub repository URL (e.g. https://github.com/owner/repo).")

    gh_evidence = await fetch_github_repo_evidence(parsed["owner"], parsed["repo"])
    
    tech_list = [t.strip() for t in claimed_technologies.split(",") if t.strip()]
    claims = [{
        "claim_type": "Technology / Skill",
        "claim": tech.title() if len(tech) > 3 else tech.upper(),
        "source_snippet": f"Claimed technology {tech}",
        "category": "Skill"
    } for tech in tech_list]

    project_data = [{
        "project_title": project_title,
        "technologies": tech_list,
        "claims": claims,
        "urls": [github_url]
    }]

    verification = verify_project_claims(
        resume_project_claims=project_data,
        github_evidence_list=[gh_evidence],
        portfolio_evidence_list=[]
    )

    return JSONResponse(content={
        "project_title": project_title,
        "github_repository": gh_evidence,
        "verification": verification
    })
