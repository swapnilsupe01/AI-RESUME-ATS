"""
Layer E — AI Resume Upgrade Routes.
Endpoints for generating, reviewing (accept/edit/reject), previewing,
and exporting AI-suggested resume upgrades.
"""

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from typing import Optional, List
import json
import logging

from app.generation.suggestion_manager import get_session, delete_session
from app.generation.resume_upgrade_engine import resume_upgrade_engine
from app.generation.huggingface_client import hf_client
from app.parser.canonical_parser import (
    parse_pdf_bytes_to_canonical,
    parse_text_to_canonical,
)
from app.parser.markdown_pipeline import canonical_to_markdown
from app.parser.pdf_generator import pdf_generator
from app.models.canonical_resume import CanonicalResume

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upgrade", tags=["Layer E — Resume Upgrade"])


def _canonical_dict_to_markdown(d: dict) -> str:
    """
    Lightweight fallback that converts a raw canonical resume dict to human-readable
    ATS markdown when Pydantic model_validate fails (e.g. on minor schema mismatches).
    Produces the same section order as canonical_to_markdown().
    """
    lines = []

    # Header
    profile = d.get("profile") or {}
    name = (d.get("candidate_name") or profile.get("name") or "Candidate").strip()
    lines.append(f"# {name}")

    headline = (profile.get("headline") or "").strip()
    if headline:
        lines.append(f"**{headline}**")

    contact_parts = []
    email = (d.get("email") or profile.get("email") or "").strip()
    phone = (d.get("phone") or profile.get("phone") or "").strip()
    location = (profile.get("location") or "").strip()
    if email: contact_parts.append(f"Email: {email}")
    if phone: contact_parts.append(f"Phone: {phone}")
    if location: contact_parts.append(f"Location: {location}")
    if contact_parts:
        lines.append(" | ".join(contact_parts))

    gh = (d.get("github_url") or profile.get("github") or "").strip()
    li = (d.get("linkedin_url") or profile.get("linkedin") or "").strip()
    link_parts = []
    if gh: link_parts.append(f"[GitHub]({gh})")
    if li: link_parts.append(f"[LinkedIn]({li})")
    if link_parts:
        lines.append(" | ".join(link_parts))
    lines.append("")

    # Summary / Objective
    summary = (d.get("summary") or profile.get("summary") or "").strip()
    if summary:
        lines.append("## Professional Summary")
        lines.append(summary)
        lines.append("")

    # Education (Fresher Priority)
    education = d.get("education") or []
    if education:
        lines.append("## Education")
        for edu in education:
            degree = (edu.get("degree") or "").strip()
            field = (edu.get("field_of_study") or "").strip()
            institution = (edu.get("institution") or edu.get("school") or "").strip()
            deg_str = f"{degree} in {field}".strip(" in ") if (degree or field) else "Degree"
            end_date = (edu.get("end_date") or edu.get("year") or "").strip()
            grade = (edu.get("grade") or edu.get("gpa") or edu.get("cgpa") or "").strip()
            header = f"### {deg_str}"
            if institution: header += f" — {institution}"
            if end_date: header += f" ({end_date})"
            lines.append(header)
            if grade:
                lines.append(f"- **CGPA/Grade:** {grade}")
            lines.append("")

    # Technical Skills
    raw_skills = d.get("skills") or {}
    if isinstance(raw_skills, dict) and any(raw_skills.values()):
        lines.append("## Technical Skills")
        for cat, items in raw_skills.items():
            if items and isinstance(items, list):
                lines.append(f"- **{cat.replace('_', ' ').title()}:** {', '.join(str(s) for s in items)}")
        lines.append("")
    elif isinstance(raw_skills, list) and raw_skills:
        lines.append("## Technical Skills")
        lines.append("- " + ", ".join(str(s) for s in raw_skills[:30]))
        lines.append("")

    # Projects
    projects = d.get("projects") or []
    if projects:
        lines.append("## Key Projects")
        for proj in projects:
            proj_name = (proj.get("name") or proj.get("title") or "Project").strip()
            proj_header = f"### {proj_name}"
            lines.append(proj_header)
            desc = (proj.get("description") or "").strip()
            if desc:
                lines.append(desc)
            for hl in (proj.get("highlights") or proj.get("bullets") or []):
                lines.append(f"- {str(hl).strip()}")
            techs = proj.get("technologies") or proj.get("tech_stack") or []
            if techs:
                lines.append(f"*Technologies: {', '.join(str(t) for t in techs)}*")
            lines.append("")

    # Work Experience / Internships (Optional for Freshers)
    experience = d.get("experience") or []
    if experience:
        lines.append("## Work Experience")
        for exp in experience:
            role = (exp.get("role") or exp.get("title") or "Role").strip()
            company = (exp.get("company") or exp.get("organization") or "").strip()
            start = exp.get("start_date") or ""
            end = exp.get("end_date") or ""
            dates = f"({start} – {end})".strip(" (–)") if (start or end) else ""
            header = f"### {role}"
            if company: header += f" — {company}"
            if dates: header += f" {dates}"
            lines.append(header)
            for hl in (exp.get("highlights") or exp.get("bullets") or []):
                lines.append(f"- {str(hl).strip()}")
            techs = exp.get("technologies") or []
            if techs:
                lines.append(f"*Technologies: {', '.join(str(t) for t in techs)}*")
            lines.append("")

    # Certifications
    certs = d.get("certifications") or []
    if certs:
        lines.append("## Certifications")
        for c in certs:
            c_name = (c.get("name") or str(c)).strip() if isinstance(c, dict) else str(c).strip()
            if c_name:
                lines.append(f"- **{c_name}**")
        lines.append("")

    # Achievements & Activities
    achievements = d.get("achievements") or []
    if achievements:
        lines.append("## Achievements & Activities")
        for a in achievements:
            lines.append(f"- {str(a).strip()}")
        lines.append("")

    # Leadership & Volunteering
    leadership = d.get("leadership") or []
    if leadership:
        lines.append("## Leadership & Volunteering")
        for l in leadership:
            lines.append(f"- {str(l).strip()}")
        lines.append("")

    # Interests / Hobbies
    interests = d.get("interests") or []
    if interests:
        lines.append("## Interests")
        lines.append("- " + ", ".join(str(i) for i in interests))
        lines.append("")

    return "\n".join(lines).strip()


@router.get("/hf-status")
async def get_hf_status():
    """Returns Hugging Face client configuration and model readiness status."""
    return JSONResponse(
        content={
            "is_configured": hf_client.is_configured(),
            "model_name": hf_client.get_model_name(),
            "is_available": hf_client.is_available() if hf_client.is_configured() else False,
        }
    )


from app.github.oauth_service import get_current_session, get_current_token
from app.github.repository_service import fetch_user_repositories_evidence


@router.post("/generate-suggestions")
async def generate_suggestions(
    canonical_resume_json: Optional[str] = Form(None, description="Canonical resume JSON string"),
    resume_file: Optional[UploadFile] = File(None, description="Optional resume PDF file"),
    resume_text: Optional[str] = Form(None, description="Optional raw or Markdown resume text"),
    jd_text: str = Form(..., description="Target Job Description text"),
    github_evidence_json: Optional[str] = Form(None, description="Optional verified GitHub repositories JSON"),
    github_username: Optional[str] = Form(None, description="Optional GitHub username for live README indexing"),
):
    """
    Generate structured, evidence-guarded AI upgrade suggestions for
    summary, experience bullets, and project descriptions.
    Integrates Layer F Codebase & Documentation RAG memory.
    """
    if not jd_text or not jd_text.strip():
        raise HTTPException(status_code=400, detail="Target job description (jd_text) is required.")

    canonical_data = None

    if canonical_resume_json and canonical_resume_json.strip():
        try:
            canonical_data = json.loads(canonical_resume_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid canonical_resume_json format: {str(exc)}",
            )
    elif resume_file:
        if not resume_file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported for file upload.")
        try:
            pdf_bytes = await resume_file.read()
            resume_obj, _, _ = parse_pdf_bytes_to_canonical(pdf_bytes)
            canonical_data = resume_obj.model_dump()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to parse resume PDF: {str(exc)}")
    elif resume_text and resume_text.strip():
        try:
            resume_obj, _, _ = parse_text_to_canonical(resume_text.strip())
            canonical_data = resume_obj.model_dump()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to parse resume text: {str(exc)}")
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide canonical_resume_json, resume_file, or resume_text.",
        )

    # Ingest GitHub Codebase Evidence for Layer F RAG Knowledge Base
    github_evidence = None
    if github_evidence_json and github_evidence_json.strip():
        try:
            github_evidence = json.loads(github_evidence_json)
        except Exception:
            github_evidence = None

    if not github_evidence:
        # Determine candidate GitHub username from parameters, active session, or resume
        target_gh_user = github_username or ""
        if not target_gh_user:
            session = get_current_session()
            if session and session.get("username"):
                target_gh_user = session["username"]

        if not target_gh_user and isinstance(canonical_data, dict):
            gh_url = canonical_data.get("github_url") or ""
            if not gh_url and isinstance(canonical_data.get("profile"), dict):
                gh_url = canonical_data["profile"].get("github") or ""
            if "github.com/" in str(gh_url):
                target_gh_user = str(gh_url).split("github.com/")[-1].strip("/").split("/")[0]

        if target_gh_user:
            try:
                token = get_current_token()
                github_evidence = await fetch_user_repositories_evidence(target_gh_user, token=token, max_repos=10)
            except Exception as exc:
                logger.debug("[generate-suggestions] Live GitHub evidence fetch note: %s", exc)

    try:
        result = resume_upgrade_engine.generate_suggestions(
            canonical_data,
            jd_text.strip(),
            github_evidence=github_evidence,
        )
        result["canonical_resume"] = canonical_data
        result["status"] = "success"
        return JSONResponse(content=result)
    except Exception as exc:
        logger.exception("[generate-suggestions] Error generating suggestions: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(exc)}")


@router.post("/accept-suggestion")
async def accept_suggestion(
    session_id: str = Form(..., description="Active upgrade session ID"),
    suggestion_id: str = Form(..., description="ID of suggestion to accept"),
    edited_text: Optional[str] = Form("", description="Optional user-edited text override"),
):
    """
    Accept an AI suggestion, optionally with custom user modifications.
    Only accepted suggestions will appear in the final approved resume.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Upgrade session not found or expired.")

    success = session.accept(suggestion_id, edited_text or "")
    if not success:
        raise HTTPException(status_code=404, detail=f"Suggestion {suggestion_id} not found in session.")

    s = session.get_suggestion(suggestion_id)
    return JSONResponse(
        content={
            "status": "success",
            "suggestion": s.to_dict() if s else None,
            "stats": session.summary_stats(),
        }
    )


@router.post("/reject-suggestion")
async def reject_suggestion(
    session_id: str = Form(..., description="Active upgrade session ID"),
    suggestion_id: str = Form(..., description="ID of suggestion to reject"),
):
    """
    Reject an AI suggestion. The original resume text will be preserved.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Upgrade session not found or expired.")

    success = session.reject(suggestion_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Suggestion {suggestion_id} not found in session.")

    s = session.get_suggestion(suggestion_id)
    return JSONResponse(
        content={
            "status": "success",
            "suggestion": s.to_dict() if s else None,
            "stats": session.summary_stats(),
        }
    )


@router.get("/approved-resume")
async def get_approved_resume(
    session_id: str = Query(..., description="Active upgrade session ID")
):
    """
    Returns the canonical resume dictionary with ONLY accepted suggestions applied.
    Unapproved and rejected suggestions are omitted.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Upgrade session not found or expired.")

    approved_canonical = session.build_approved_resume()
    md_text = ""
    try:
        canon_obj = CanonicalResume.model_validate(approved_canonical)
        md_text = canonical_to_markdown(canon_obj)
    except Exception:
        # Robust dict-based markdown fallback so the Enhanced ATS panel always shows content
        try:
            md_text = _canonical_dict_to_markdown(approved_canonical)
        except Exception:
            md_text = ""

    return JSONResponse(
        content={
            "status": "success",
            "approved_canonical": approved_canonical,
            "markdown_text": md_text,
            "stats": session.summary_stats(),
        }
    )


@router.post("/export-pdf")
async def export_approved_pdf(
    session_id: Optional[str] = Form(None, description="Active upgrade session ID"),
    canonical_resume_json: Optional[str] = Form(None, description="Direct canonical JSON fallback"),
    resume_text: Optional[str] = Form(None, description="Direct markdown text from editor"),
):
    """
    Renders the approved resume into an ATS-compliant, single-column PDF.
    Priority order:
      1. Session canonical (most reliable — preserves all sections including Experience & Certifications)
      2. Direct canonical JSON
      3. Re-parse editor markdown (last resort — may lose some sections on round-trip)
    """
    resume_data = None

    # ── Primary: Use session canonical (preserves all sections) ─────────────
    if session_id:
        session = get_session(session_id)
        if session:
            resume_data = session.build_approved_resume()
            logger.info("[export-pdf] Using session canonical for %s", session_id)

    # ── Secondary: Direct canonical JSON ────────────────────────────────────
    if not resume_data and canonical_resume_json and canonical_resume_json.strip():
        try:
            resume_data = json.loads(canonical_resume_json)
            logger.info("[export-pdf] Using canonical_resume_json fallback")
        except Exception:
            pass

    # ── Last Resort: Re-parse editor markdown ────────────────────────────────
    if not resume_data and resume_text and resume_text.strip():
        try:
            from app.parser.canonical_parser import parse_text_to_canonical
            canonical_obj, _, _ = parse_text_to_canonical(resume_text.strip())
            resume_data = canonical_obj.model_dump()
            logger.info("[export-pdf] Last-resort: re-parsed resume_text")
        except Exception as e:
            logger.warning("[export-pdf] Parse resume_text fallback warning: %s", e)

    if not resume_data:
        raise HTTPException(
            status_code=400,
            detail="Valid session_id, resume_text, or canonical_resume_json required to generate PDF.",
        )

    try:
        pdf_bytes = pdf_generator.generate_pdf(resume_data)
    except Exception as exc:
        logger.exception("[export-pdf] PDF generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"PDF rendering error: {str(exc)}")

    name_str = (
        resume_data.get("candidate_name")
        or (resume_data.get("profile", {}).get("name") if isinstance(resume_data.get("profile"), dict) else "")
        or "Approved"
    ).replace(" ", "_")
    filename = f"{name_str}_Upgraded_Resume.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@router.get("/session-status")
async def get_session_status(
    session_id: str = Query(..., description="Active upgrade session ID")
):
    """Returns current review statistics and count of pending suggestions."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Upgrade session not found or expired.")

    return JSONResponse(
        content={
            "status": "success",
            "session_id": session_id,
            "stats": session.summary_stats(),
            "model_used": hf_client.get_model_name() if hf_client.is_configured() else "Local Rule-Based / RAG",
        }
    )


@router.get("/rag-cache-status")
async def get_rag_cache_status():
    """
    Returns the Layer F RAG JSON knowledge cache status.
    Lists all cached candidates with their chunk and repo counts.
    """
    from app.ai.codebase_rag import codebase_rag_instance
    cached = codebase_rag_instance.list_cached_candidates()
    active = {
        "candidate_key": codebase_rag_instance._current_candidate_key,
        "chunks_in_memory": len(codebase_rag_instance.chunks),
        "repos_in_memory": len({
            c["project_name"] for c in codebase_rag_instance.chunks
            if c.get("type", "").startswith("github")
        }),
        "all_tools": sorted(list(codebase_rag_instance.candidate_all_tools)),
    }
    return JSONResponse(content={
        "status": "success",
        "active_store": active,
        "cached_candidates": cached,
        "cache_dir": str(codebase_rag_instance._cache_path("").parent),
    })


@router.delete("/rag-cache/{candidate_key}")
async def clear_rag_cache(candidate_key: str):
    """
    Delete a candidate's Layer F RAG JSON cache file.
    Forces a fresh GitHub README re-fetch on next suggestion generation.
    """
    from app.ai.codebase_rag import codebase_rag_instance
    import os
    path = codebase_rag_instance._cache_path(candidate_key)
    if path.exists():
        os.remove(path)
        return JSONResponse(content={"status": "deleted", "candidate_key": candidate_key, "file": str(path)})
    raise HTTPException(status_code=404, detail=f"No RAG cache found for '{candidate_key}'.")


@router.get("/rag-readme/{candidate_key}/{repo_name}")
async def get_cached_readme(candidate_key: str, repo_name: str):
    """
    Retrieve the full raw README.md content for a specific repository
    from the candidate's Layer F RAG JSON cache.
    """
    from app.ai.codebase_rag import codebase_rag_instance
    # Load from disk if not already active
    if codebase_rag_instance._current_candidate_key != candidate_key:
        loaded = codebase_rag_instance.load_from_json(candidate_key)
        if not loaded:
            raise HTTPException(status_code=404, detail=f"No RAG cache for '{candidate_key}'.")

    readme = codebase_rag_instance.get_raw_readme(repo_name)
    if readme is None:
        available = list(codebase_rag_instance.raw_readmes.keys())
        raise HTTPException(
            status_code=404,
            detail=f"README not found for repo '{repo_name}'. Available repos: {available}"
        )

    return JSONResponse(content={
        "candidate_key": candidate_key,
        "repo_name": repo_name,
        "readme_length": len(readme),
        "readme_content": readme,
    })

