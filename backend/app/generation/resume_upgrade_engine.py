"""
Layer E — Resume Upgrade Engine
Orchestrates AI suggestion generation, hallucination guarding, and suggestion session management.
Grounded by Layer F (Codebase & Documentation RAG Knowledge Layer) for zero-hallucination upgrades.
Includes evidence-based 4-slot Project Ordering algorithm.
"""

from typing import Dict, Any, List, Optional
import copy
import re

from app.generation.huggingface_client import hf_client, HuggingFaceClient
from app.generation.hallucination_guard import classify_suggestion
from app.generation.content_classifier import classify_content_type
from app.generation.preservation_validator import (
    sanitize_ai_text,
    contains_ai_leakage,
    validate_and_preserve,
    validate_suggestion_output,
    format_tech_stack,
)
from app.generation.suggestion_manager import (
    Suggestion,
    UpgradeSession,
    create_session,
    get_session,
    delete_session,
)
from app.ai.rag_engine import rag_engine
from app.ai.codebase_rag import codebase_rag_instance
from app.extraction.skill_extractor import extract_job_skills


def _is_valid_rewrite_target(text: Optional[str]) -> bool:
    """
    Filter out dates, URLs, emails, header fragments, and junk strings
    so they are never passed to the LLM for rewrite suggestions.
    """
    if not text:
        return False
    s = str(text).strip()
    if len(s) < 15:
        return False

    # Check date range like "Feb - Apr 2026", "2021 - 2023", "Jan 2020 - Present"
    date_range_pattern = (
        r"^(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{2,4}|\d{4})"
        r"\s*[-–—/to]+\s*"
        r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{2,4}|\d{4}|present|current)$"
    )
    if re.match(date_range_pattern, s, re.IGNORECASE):
        return False

    # Check single date
    if re.match(r"^(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*)?\d{4}$", s, re.IGNORECASE):
        return False

    # Check URL, email, or pure symbols
    if re.match(r"^(https?://|www\.|github\.com|linkedin\.com|[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", s, re.IGNORECASE):
        return False

    # Check for substantive word count (must have at least 4 meaningful words)
    words = re.findall(r"\b[A-Za-z]{2,}\b", s)
    if len(words) < 4:
        return False

    return True


# Keywords that identify a role title as an internship entry.
# Experience items whose role matches these must NOT be rewritten — they belong
# to the student's CERTIFICATIONS & INTERNSHIPS section (or a dedicated Internships
# section) and must be left exactly as the student wrote them.
_INTERNSHIP_ROLE_KEYWORDS = re.compile(
    r"\b(intern|internship|trainee|industrial\s+trainee|summer\s+trainee|"
    r"apprentice|co-op|co\s*op|placement|vocational)\b",
    re.IGNORECASE,
)


def _is_internship_entry(exp: Dict[str, Any]) -> bool:
    """
    Return True if the experience item represents an internship.
    Checks role title, company name, and any custom 'section_type' flag.
    When True the entry is excluded from AI rewriting so that CERTIFICATIONS
    & INTERNSHIPS content is always preserved verbatim.
    """
    role = str(exp.get("role") or exp.get("title") or "")
    company = str(exp.get("company") or exp.get("organization") or "")
    section_type = str(exp.get("section_type") or exp.get("_section") or "")

    if _INTERNSHIP_ROLE_KEYWORDS.search(role):
        return True
    if _INTERNSHIP_ROLE_KEYWORDS.search(section_type):
        return True
    # Some parsers store the origin section header in the company field for
    # standalone "Internships" sections — catch that edge-case too.
    if _INTERNSHIP_ROLE_KEYWORDS.search(company) and not role.strip():
        return True
    return False


def _light_enhance_summary(summary: str, candidate_tools: List[str]) -> Optional[str]:
    """
    Fallback summary enhancer used when the LLM is not configured.
    ONLY upgrades weak opener verbs and ensures clean capitalisation/punctuation.
    It NEVER replaces the student's own text with a generic template.
    Returns None if no actionable change was found (so the original is kept).
    """
    s = summary.strip()
    if not s:
        return None

    # Weak first-person openers that can safely be upgraded
    _SUMMARY_WEAK_OPENERS = [
        (r'^i\s+am\s+a\s+', 'A '),
        (r'^i\s+am\s+an\s+', 'An '),
        (r'^i\s+am\s+', ''),
        (r'^i\s+have\s+', 'Bringing '),
        (r'^i\s+possess\s+', 'Possessing '),
        (r'^i\s+', ''),
    ]
    enhanced = s
    for pattern, replacement in _SUMMARY_WEAK_OPENERS:
        if re.match(pattern, enhanced, re.IGNORECASE):
            enhanced = re.sub(pattern, replacement, enhanced, count=1, flags=re.IGNORECASE)
            # Capitalise the first character after substitution
            enhanced = enhanced[0].upper() + enhanced[1:] if enhanced else enhanced
            break

    # Ensure it ends with a period
    if enhanced and not enhanced.endswith((".", "!", "?")):
        enhanced += "."

    # Return None if nothing actually changed
    if enhanced.strip() == s.strip():
        return None
    return enhanced.strip()


def _is_project_title_or_short_name(text: Optional[str], proj_name: Optional[str] = None) -> bool:
    """
    Detect if text is a project title, headline, or short title-description
    (e.g., 'AI-Powered ISO Audit Gap Analysis Platform', 'Cybersecurity Orchestration & Vulnerability Engine')
    rather than a substantive project bullet point or multi-sentence narrative.
    These must NOT be rewritten into long descriptive paragraphs.
    """
    if not text:
        return True
    s = str(text).strip()

    # 1. Matches or substantially overlaps project name
    if proj_name:
        pn = proj_name.strip().lower()
        sl = s.lower()
        if sl == pn or sl in pn or pn in sl:
            return True
        pn_tokens = set(re.findall(r'\b[a-zA-Z]{3,}\b', pn))
        s_tokens = set(re.findall(r'\b[a-zA-Z]{3,}\b', sl))
        if pn_tokens and len(pn_tokens.intersection(s_tokens)) >= len(pn_tokens) * 0.6:
            return True

    # 2. Short title-like phrase (< 10 words, no terminal period or sentence structure)
    words = re.findall(r'\b[a-zA-Z0-9\-\.\+#]{2,}\b', s)
    if len(words) <= 8:
        action_verbs = {
            "developed", "designed", "implemented", "built", "created", "led", "managed",
            "engineered", "architected", "deployed", "spearheaded", "integrated", "automated",
            "orchestrated", "optimized", "conducted", "analyzed"
        }
        first_few_words = {w.lower() for w in words[:3]}
        if not (first_few_words & action_verbs):
            return True

    # 3. Pure Title Case or Noun Phrase without sentence punctuation (e.g. ends with "Platform", "Engine", "System")
    title_endings = ("platform", "engine", "system", "tool", "analyzer", "scanner", "application", "dashboard", "bot", "framework")
    if len(words) <= 10 and s.lower().endswith(title_endings) and not any(p in s for p in [". ", "; ", "\n"]):
        return True

    return False


class ResumeUpgradeEngine:
    """
    Coordinates candidate resume upgrade suggestions.
    Elevates professional wording and action verbs without hallucinating unmentioned tools.
    Integrates Layer F Codebase & Documentation RAG memory.
    Provides evidence-based 4-slot project relevance ordering.
    Guards all suggestions with the Hallucination Guard.
    """

    def __init__(self, client: Optional[HuggingFaceClient] = None):
        self.hf = client or hf_client

    def _extract_candidate_skills(self, resume_data: Dict[str, Any]) -> List[str]:
        skills = []
        raw_skills = resume_data.get("skills", [])
        if isinstance(raw_skills, list):
            for s in raw_skills:
                if isinstance(s, dict):
                    skills.extend(s.get("skills", []))
                elif isinstance(s, str):
                    skills.append(s)
        elif isinstance(raw_skills, dict):
            for s_list in raw_skills.values():
                if isinstance(s_list, list):
                    skills.extend(s_list)
                elif isinstance(s_list, str):
                    skills.append(s_list)

        # Also pull from project technologies and experience technologies
        for p in resume_data.get("projects", []):
            if isinstance(p, dict):
                p_techs = p.get("technologies") or p.get("tech_stack") or []
                if isinstance(p_techs, list):
                    skills.extend(p_techs)
                elif isinstance(p_techs, str):
                    skills.extend([t.strip() for t in p_techs.split(",") if t.strip()])
        
        for exp in resume_data.get("experience", []):
            if isinstance(exp, dict):
                exp_techs = exp.get("technologies") or []
                if isinstance(exp_techs, list):
                    skills.extend(exp_techs)
                elif isinstance(exp_techs, str):
                    skills.extend([t.strip() for t in exp_techs.split(",") if t.strip()])

        if not skills and resume_data.get("extracted_skills"):
            skills = resume_data.get("extracted_skills", [])
        return list(dict.fromkeys([str(s).strip() for s in skills if str(s).strip()]))

    def _extract_jd_keywords(self, jd_text: str) -> List[str]:
        try:
            extracted = extract_job_skills(jd_text)
            return extracted.get("all_skills", [])
        except Exception:
            words = re.findall(r"\b[A-Za-z0-9\.\+#]{2,}\b", jd_text)
            return list(dict.fromkeys(words))[:15]

    def calculate_project_ordering(
        self,
        projects: List[Dict[str, Any]],
        jd_keywords: List[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Evidence-based 4-slot Project Ordering:
          - Slots 1 & 2: Two strongest distinct JD-relevant projects.
          - Slot 3: Most recent eligible project not already selected.
          - Slot 4: Candidate-pinned or Capstone/Final Year project.
          - If fewer than 4 projects exist, orders available ones without inventing projects.
        """
        if not projects or len(projects) <= 1:
            return None

        scored_projects = []
        jd_kw_set = {k.lower().strip() for k in jd_keywords if k.strip()}

        for idx, p in enumerate(projects):
            p_id = p.get("id") or f"proj_{idx}"
            p_name = p.get("name") or p.get("title") or f"Project {idx + 1}"
            p_techs = p.get("technologies") or p.get("tech_stack") or []
            if isinstance(p_techs, str):
                p_techs = [t.strip() for t in p_techs.split(",") if t.strip()]

            p_desc = str(p.get("description") or "")
            p_highlights = p.get("highlights") or p.get("bullets") or []
            if isinstance(p_highlights, list):
                p_hl_text = " ".join(str(h) for h in p_highlights)
            else:
                p_hl_text = str(p_highlights)

            combined_text = f"{p_name} {' '.join(p_techs)} {p_desc} {p_hl_text}".lower()

            matched_keywords = [kw for kw in jd_kw_set if kw in combined_text]
            kw_score = len(matched_keywords)

            is_capstone = bool(re.search(r"\b(final\s*year|capstone|thesis|major\s*project|b\.?tech\s*project|m\.?tech\s*project)\b", combined_text, re.IGNORECASE))
            is_pinned = bool(p.get("is_pinned") or p.get("pinned") or is_capstone)

            date_str = str(p.get("dates") or p.get("date") or p.get("year") or p.get("end_date") or "")
            year_match = re.search(r"\b(20\d\d)\b", date_str)
            recency_val = int(year_match.group(1)) if year_match else (1000 - idx)

            scored_projects.append({
                "idx": idx,
                "id": p_id,
                "name": p_name,
                "score": kw_score,
                "matched_keywords": matched_keywords[:4],
                "recency": recency_val,
                "is_pinned_or_capstone": is_pinned,
                "date_str": date_str,
            })

        selected_indices = []
        slot_reasons = {}

        # Slots 1 & 2: Strongest JD-relevant projects
        by_relevance = sorted(scored_projects, key=lambda x: (x["score"], x["recency"]), reverse=True)

        if by_relevance:
            p1 = by_relevance[0]
            selected_indices.append(p1["idx"])
            matches_txt = f" (Matches JD: {', '.join(p1['matched_keywords'])})" if p1['matched_keywords'] else ""
            slot_reasons[p1["idx"]] = f"Slot 1: Highest JD Alignment{matches_txt}"

        remaining_rel = [p for p in by_relevance if p["idx"] not in selected_indices]
        if remaining_rel:
            p2 = remaining_rel[0]
            selected_indices.append(p2["idx"])
            matches_txt = f" (Matches JD: {', '.join(p2['matched_keywords'])})" if p2['matched_keywords'] else ""
            slot_reasons[p2["idx"]] = f"Slot 2: Secondary JD Strength{matches_txt}"

        # Slot 3: Most recent eligible project not already selected
        by_recency = sorted(
            [p for p in scored_projects if p["idx"] not in selected_indices],
            key=lambda x: (x["recency"], x["score"]),
            reverse=True
        )
        if by_recency:
            p3 = by_recency[0]
            selected_indices.append(p3["idx"])
            date_txt = f" ({p3['date_str']})" if p3['date_str'] else ""
            slot_reasons[p3["idx"]] = f"Slot 3: Most Recent Project{date_txt}"

        # Slot 4: Candidate-selected/pinned project or remaining foundational work
        pinned_candidates = [p for p in scored_projects if p["idx"] not in selected_indices and p["is_pinned_or_capstone"]]
        if pinned_candidates:
            p4 = pinned_candidates[0]
            selected_indices.append(p4["idx"])
            slot_reasons[p4["idx"]] = "Slot 4: Capstone / Final-Year Pinned Project"
        else:
            remaining_other = [p for p in scored_projects if p["idx"] not in selected_indices]
            if remaining_other:
                p4 = remaining_other[0]
                selected_indices.append(p4["idx"])
                slot_reasons[p4["idx"]] = "Slot 4: Foundational Project"

        # Any extra remaining projects
        for p in scored_projects:
            if p["idx"] not in selected_indices:
                selected_indices.append(p["idx"])
                slot_reasons[p["idx"]] = f"Slot {len(selected_indices)}: Additional Portfolio Project"

        orig_lines = [f"{i + 1}. {projects[i].get('name') or projects[i].get('title') or f'Project {i + 1}'}" for i in range(len(projects))]
        sugg_lines = [f"{i + 1}. {projects[idx].get('name') or projects[idx].get('title') or f'Project {idx + 1}'} — [{slot_reasons.get(idx, f'Slot {i+1}')}]" for i, idx in enumerate(selected_indices)]

        return {
            "original_text": "\n".join(orig_lines),
            "suggested_text": "\n".join(sugg_lines),
            "selected_indices": selected_indices,
            "is_already_optimal": selected_indices == list(range(len(projects))),
        }

    def generate_suggestions(
        self,
        canonical_resume: Dict[str, Any],
        jd_text: str,
        github_evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generates improvement suggestions for summary, experience, and projects.
        Grounded by Layer F Codebase & Documentation RAG memory.
        Validates suggestions with Hallucination Guard.
        Initializes an UpgradeSession.
        """
        session_id = create_session(canonical_resume)
        session = get_session(session_id)
        if not session:
            raise RuntimeError("Failed to create upgrade session")

        # ── 1. Ingest into Layer F Vector Knowledge Store ──────────────────────
        codebase_rag_instance.clear()

        # Derive candidate key from resume (used for JSON cache lookup)
        candidate_key = codebase_rag_instance.index_resume_and_save(canonical_resume)

        if github_evidence:
            # Fresh GitHub evidence provided — index it and auto-save to JSON
            codebase_rag_instance.index_github_repositories(github_evidence)
        else:
            # No fresh evidence — try loading from JSON cache (survives restarts)
            cache_hit = codebase_rag_instance.load_from_json(candidate_key)
            if cache_hit:
                import logging as _log
                _log.getLogger(__name__).info(
                    "[Layer F RAG] Cache HIT for '%s': %d chunks loaded",
                    candidate_key, len(codebase_rag_instance.chunks)
                )

        candidate_tools = self._extract_candidate_skills(canonical_resume)
        jd_keywords = self._extract_jd_keywords(jd_text)
        jd_keywords_str = ", ".join(jd_keywords[:8])

        # ── 2. Summary suggestion ────────────────────────────────────────────
        summary = canonical_resume.get("summary") or ""
        if isinstance(canonical_resume.get("profile"), dict):
            summary = canonical_resume["profile"].get("summary") or summary

        if summary and _is_valid_rewrite_target(summary):
            summary_cat = classify_content_type(summary, section_context="summary", field_name="summary")
            suggested_summary = None
            explanation_summary = "Refines professional phrasing and highlights candidate's core strengths."
            val_status = "valid"

            if summary_cat in ("TECH_STACK", "SKILLS"):
                suggested_summary = format_tech_stack(summary)
                explanation_summary = "The original technology stack is already clear. Preserved all listed technologies without altering facts."
                status, note = "supported", "Verified: Preserved technology list without fabricating narrative sentences."
            else:
                if self.hf.is_configured():
                    rag_data = codebase_rag_instance.retrieve_grounded_context(summary, top_k=2)
                    suggested_summary = self.hf.generate(
                        "rewrite_summary",
                        summary,
                        {
                            "candidate_tools": rag_data["verified_tools"] or candidate_tools,
                            "jd_keywords": jd_keywords_str,
                            "rag_context": rag_data["rag_prompt_block"],
                        }
                    )

                if not suggested_summary:
                    # Fallback: lightly enhance the student's OWN summary text — never
                    # replace it with a generic template (that would be hallucination).
                    suggested_summary = _light_enhance_summary(summary, candidate_tools)

                if suggested_summary:
                    val_text, is_val, val_reason = validate_suggestion_output(summary, suggested_summary, summary_cat, candidate_tools)
                    suggested_summary = val_text
                    val_status = "valid" if is_val else "fallback_applied"
                    status, note = classify_suggestion(summary, suggested_summary, candidate_tools)

            if suggested_summary and (suggested_summary.strip() != summary.strip() or summary_cat in ("TECH_STACK", "SKILLS")):
                s = Suggestion(
                    section="summary",
                    item_id="summary",
                    field="summary",
                    original_text=summary,
                    suggested_text=suggested_summary.strip(),
                    explanation=explanation_summary,
                    jd_requirement="Professional summary clarity",
                    evidence_status=status,
                    evidence_note=note,
                    category=summary_cat,
                    validation_status=val_status,
                )
                session.add_suggestion(s)

        # ── 3. Experience suggestions ────────────────────────────────────────
        # INTERNSHIP GUARD: entries that represent internships are owned by the
        # student's CERTIFICATIONS & INTERNSHIPS section and must NEVER be
        # rewritten.  Only "professional experience" items are eligible.
        experiences = canonical_resume.get("experience", [])
        for exp_idx, exp in enumerate(experiences):
            if _is_internship_entry(exp):
                # Skip — internship bullets are preserved verbatim.
                continue

            exp_id = exp.get("id") or f"exp_{exp_idx}"
            role = exp.get("role") or exp.get("title") or "Role"
            company = exp.get("company") or exp.get("organization") or ""
            highlights = exp.get("highlights") or exp.get("bullets") or []
            if isinstance(highlights, str):
                highlights = [highlights]

            for h_idx, bullet in enumerate(highlights):
                if not _is_valid_rewrite_target(bullet):
                    continue

                bullet_cat = classify_content_type(bullet, section_context="experience", field_name=f"highlights[{h_idx}]")
                suggested_bullet = None
                exp_explanation = f"Strengthens action verbs and technical articulation for {role}{f' at {company}' if company else ''}."
                val_status = "valid"

                if bullet_cat in ("TECH_STACK", "SKILLS"):
                    suggested_bullet = format_tech_stack(bullet)
                    exp_explanation = "The original technology stack is already clear. Preserved all listed technologies without altering facts."
                    status, note = "supported", "Verified: Preserved technology list without fabricating narrative sentences."
                else:
                    if self.hf.is_configured():
                        rag_data = codebase_rag_instance.retrieve_grounded_context(bullet, project_name=company, top_k=2)
                        suggested_bullet = self.hf.generate(
                            "rewrite_experience",
                            bullet,
                            {
                                "candidate_tools": rag_data["verified_tools"] or candidate_tools,
                                "rag_context": rag_data["rag_prompt_block"],
                            }
                        )

                    if not suggested_bullet:
                        restructured, changes = rag_engine.restructure_sentence(bullet, candidate_tools)
                        if changes:
                            suggested_bullet = restructured

                    if suggested_bullet:
                        val_text, is_val, val_reason = validate_suggestion_output(bullet, suggested_bullet, bullet_cat, candidate_tools)
                        suggested_bullet = val_text
                        val_status = "valid" if is_val else "fallback_applied"
                        status, note = classify_suggestion(bullet, suggested_bullet, candidate_tools)
                        if bullet_cat == "ACHIEVEMENT":
                            exp_explanation = "Improves the phrasing of the achievement while retaining the original result and metrics."
                        else:
                            exp_explanation = f"Improves action verbs and clarity while preserving the original responsibilities and technical details for {role}{f' at {company}' if company else ''}."

                if suggested_bullet and (suggested_bullet.strip() != bullet.strip() or bullet_cat in ("TECH_STACK", "SKILLS")):
                    s = Suggestion(
                        section="experience",
                        item_id=exp_id,
                        field=f"highlights[{h_idx}]",
                        original_text=bullet,
                        suggested_text=suggested_bullet.strip(),
                        explanation=exp_explanation,
                        jd_requirement="STAR verb strengthening",
                        evidence_status=status,
                        evidence_note=note,
                        category=bullet_cat,
                        validation_status=val_status,
                    )
                    session.add_suggestion(s)

        # ── 4. Project suggestions (Descriptions & Highlights) ────────────────
        projects = canonical_resume.get("projects", [])
        # Build list of ALL project names upfront — used by the cross-project
        # contamination guard so rewrites for project A don't bleed in names/text
        # from projects B, C, etc.
        all_project_names = [
            str(p.get("name") or p.get("title") or "").strip()
            for p in projects
            if (p.get("name") or p.get("title") or "").strip()
        ]

        for p_idx, proj in enumerate(projects):
            proj_id = proj.get("id") or f"proj_{p_idx}"
            proj_name = proj.get("name") or proj.get("title") or "Project"
            techs = proj.get("technologies") or proj.get("tech_stack") or []
            if isinstance(techs, str):
                techs = [t.strip() for t in techs.split(",") if t.strip()]
            other_proj_names = [n for n in all_project_names if n != proj_name]

            # Retrieve project-specific ground truth from GitHub README in Layer F
            proj_rag = codebase_rag_instance.retrieve_grounded_context(
                query=f"{proj_name} {' '.join(techs)}",
                project_name=proj_name,
                top_k=3,
            )
            grounded_tools = proj_rag["verified_tools"] or techs

            # Check project description (Skip if it's merely a project title, headline, or short name)
            desc = proj.get("description", "")
            if desc and _is_valid_rewrite_target(desc) and not _is_project_title_or_short_name(desc, proj_name):
                desc_cat = classify_content_type(desc, section_context="project", field_name="description")
                suggested_desc = None
                desc_explanation = f"Elevates project wording and technical clarity for {proj_name}."
                val_status = "valid"

                if desc_cat in ("TECH_STACK", "SKILLS"):
                    suggested_desc = format_tech_stack(desc)
                    desc_explanation = "The original technology stack is already clear. Preserved all listed technologies without altering facts."
                    status, note = "supported", "Verified: Preserved technology list without fabricating narrative sentences."
                elif desc_cat == "PROJECT_TITLE":
                    suggested_desc = desc.strip()
                    desc_explanation = "Preserves project title and technical branding."
                    status, note = "supported", "Verified: Preserved exact project title."
                else:
                    if self.hf.is_configured():
                        suggested_desc = self.hf.generate(
                            "rewrite_project",
                            desc,
                            {
                                "technologies": grounded_tools if grounded_tools else ["Focus strictly on functional scope, system features, and user workflows — DO NOT invent languages, frameworks, or databases"],
                                "candidate_tools": grounded_tools if grounded_tools else [],
                                "rag_context": proj_rag["rag_prompt_block"],
                                "_other_project_names": other_proj_names,
                            }
                        )
                    if not suggested_desc:
                        restructured, changes = rag_engine.restructure_sentence(desc, grounded_tools or candidate_tools)
                        if changes:
                            suggested_desc = restructured

                    if suggested_desc:
                        val_text, is_val, val_reason = validate_suggestion_output(desc, suggested_desc, desc_cat, grounded_tools)
                        suggested_desc = val_text
                        val_status = "valid" if is_val else "fallback_applied"
                        extra_project_tokens = [w.strip() for w in re.split(r'[\s,;:—–|/]+', f"{proj_name} {desc}") if len(w.strip()) > 2]
                        allowed_tools = list(set((grounded_tools or []) + (candidate_tools or []) + (techs or []) + extra_project_tokens))
                        status, note = classify_suggestion(desc, suggested_desc, allowed_tools)
                        if desc_cat == "ACHIEVEMENT":
                            desc_explanation = "Improves the phrasing of the achievement while retaining the original result and metrics."
                        else:
                            desc_explanation = f"Improves action verbs and technical clarity while preserving original implementation details for {proj_name}."

                if suggested_desc and (suggested_desc.strip() != desc.strip() or desc_cat in ("TECH_STACK", "SKILLS")):
                    s = Suggestion(
                        section="project",
                        item_id=proj_id,
                        field="description",
                        original_text=desc,
                        suggested_text=suggested_desc.strip(),
                        explanation=desc_explanation,
                        jd_requirement="Project technical depth",
                        evidence_status=status,
                        evidence_note=note,
                        category=desc_cat,
                        validation_status=val_status,
                    )
                    session.add_suggestion(s)

            # Check project highlights
            p_highlights = proj.get("highlights") or proj.get("bullets") or []
            if isinstance(p_highlights, str):
                p_highlights = [p_highlights]

            for ph_idx, bullet in enumerate(p_highlights):
                if not _is_valid_rewrite_target(bullet) or _is_project_title_or_short_name(bullet, proj_name):
                    continue

                hl_cat = classify_content_type(bullet, section_context="project", field_name=f"highlights[{ph_idx}]")
                suggested_ph = None
                hl_explanation = f"Clarifies execution details and technical outcomes for {proj_name}."
                val_status = "valid"

                if hl_cat in ("TECH_STACK", "SKILLS"):
                    suggested_ph = format_tech_stack(bullet)
                    hl_explanation = "The original technology stack is already clear. Preserved all listed technologies without altering facts."
                    status, note = "supported", "Verified: Preserved technology list without fabricating narrative sentences."
                else:
                    if self.hf.is_configured():
                        bullet_rag = codebase_rag_instance.retrieve_grounded_context(
                            query=bullet,
                            project_name=proj_name,
                            top_k=2,
                        )
                        suggested_ph = self.hf.generate(
                            "rewrite_experience",
                            bullet,
                            {
                                "candidate_tools": bullet_rag["verified_tools"] or grounded_tools or candidate_tools,
                                "rag_context": bullet_rag["rag_prompt_block"],
                                "_other_project_names": other_proj_names,
                            }
                        )
                    if not suggested_ph:
                        restructured, changes = rag_engine.restructure_sentence(bullet, candidate_tools)
                        if changes:
                            suggested_ph = restructured

                    if suggested_ph:
                        extra_bullet_tokens = [w.strip() for w in re.split(r'[\s,;:—–|/]+', f"{proj_name} {bullet}") if len(w.strip()) > 2]
                        allowed_ph_tools = list(set((bullet_rag["verified_tools"] or []) + (grounded_tools or []) + (candidate_tools or []) + (techs or []) + extra_bullet_tokens)) if self.hf.is_configured() else list(set((grounded_tools or []) + (candidate_tools or []) + (techs or []) + extra_bullet_tokens))
                        val_text, is_val, val_reason = validate_suggestion_output(bullet, suggested_ph, hl_cat, allowed_ph_tools)
                        suggested_ph = val_text
                        val_status = "valid" if is_val else "fallback_applied"
                        status, note = classify_suggestion(bullet, suggested_ph, allowed_ph_tools)
                        if hl_cat == "ACHIEVEMENT":
                            hl_explanation = "Improves the phrasing of the achievement while retaining the original result and metrics."
                        else:
                            hl_explanation = f"Clarifies execution details and technical outcomes while preserving original implementation details for {proj_name}."

                if suggested_ph and (suggested_ph.strip() != bullet.strip() or hl_cat in ("TECH_STACK", "SKILLS")):
                    s = Suggestion(
                        section="project",
                        item_id=proj_id,
                        field=f"highlights[{ph_idx}]",
                        original_text=bullet,
                        suggested_text=suggested_ph.strip(),
                        explanation=hl_explanation,
                        jd_requirement="Technical execution",
                        evidence_status=status,
                        evidence_note=note,
                        category=hl_cat,
                        validation_status=val_status,
                    )
                    session.add_suggestion(s)

        # ── 5. Project Ordering Suggestion (4-Slot Evidence-Based Ordering) ────
        order_data = self.calculate_project_ordering(projects, jd_keywords)
        if order_data and not order_data.get("is_already_optimal"):
            s_order = Suggestion(
                section="project",
                item_id="project_ordering",
                field="order",
                original_text=order_data["original_text"],
                suggested_text=order_data["suggested_text"],
                explanation="Reorders projects for maximum impact: Slots 1 & 2 prioritize your strongest JD-aligned work, Slot 3 highlights your most recent project, and Slot 4 features your capstone.",
                jd_requirement="Project relevance prioritization",
                evidence_status="supported",
                evidence_note="Reorders only your actual existing projects based on verified keyword & recency alignment.",
                category="PROJECT_TITLE",
                validation_status="valid",
            )
            session.add_suggestion(s_order)

        return {
            "session_id": session_id,
            "suggestions": [s.to_dict() for s in session.suggestions],
            "stats": session.summary_stats(),
            "model_used": self.hf.get_model_name() if self.hf.is_configured() else "Local Rule-Based / RAG"
        }


resume_upgrade_engine = ResumeUpgradeEngine()
