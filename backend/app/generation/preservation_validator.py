"""
Preservation Validator & AI Sanitizer — Layer E / Core Data Integrity.

Enforces zero-data-loss architecture across AI upgrade, tailoring, and rendering.
Guarantees that:
  1. The original resume is the immutable SOURCE OF TRUTH.
  2. All factual entities (contact, education, experience, bullets, projects,
     certifications, skills, URLs) are strictly preserved unless the user explicitly
     approves a deletion.
  3. ZERO AI commentary, internal instructions, or reasoning leakage ever reaches
     the final canonical resume, markdown, or PDF.
"""

import copy
import re
import logging
from typing import Dict, Any, List, Tuple, Set, Optional

logger = logging.getLogger(__name__)

# Patterns that indicate leaked AI reasoning, commentary, or instructions
FORBIDDEN_COMMENTARY_PATTERNS = [
    r"^\s*note\s*:\s*i(?:'ve|\s+have)?\s+.*$",
    r"^\s*note\s*:\s*.*$",
    r"^\s*please\s+note\s*:.*$",
    r"^\s*here\s+(?:is|are)\s+(?:the|your)\s+.*$",
    r"^\s*i\s+(?:have\s+)?(?:maintained|used|updated|improved|added|refrained|did\s+not|removed|selected)\s+.*$",
    r"^\s*according\s+to\s+(?:the\s+)?instructions\s*:?.*$",
    r"^\s*ai\s+reasoning\s*:?.*$",
    r"^\s*explanation\s*:?.*$",
    r"^\s*why\s+this\s+was\s+changed\s*:?.*$",
    r"^\s*changes\s+made\s*:?.*$",
    r"^\s*improvements\s+made\s*:?.*$",
    r"^\s*disclaimer\s*:?.*$",
    r"^\s*\*{0,2}rationale\*{0,2}\s*:?.*$",
    r"^\s*\*{0,2}summary\s+of\s+changes\*{0,2}\s*:?.*$",
    r"^\s*\*{0,2}alternatively\*{0,2}\s*,?\s*:?.*$",
    r"^\s*\*{0,2}option\s+\d+\*{0,2}\s*:?.*$",
    r"^\s*(?:sure|certainly|absolutely|of\s+course)\s*,?\s*(?:i(?:'d|'ll|\s+will|\s+can|\s+would))?\s+.*$",
    r"^\s*below\s+is\s+(?:the|your|an|a)?\s+.*$",
    r"^\s*as\s+an?\s+(?:ai|language\s+model|assistant).*$",
    r"^\s*the\s+following\s+(?:is|are)\s+(?:the|your|an|a)?\s+.*(?:resume|bullet|suggestion|version).*$",
]

_COMPILED_COMMENTARY_PATTERNS = [
    re.compile(p, re.IGNORECASE | re.MULTILINE) for p in FORBIDDEN_COMMENTARY_PATTERNS
]


def contains_ai_leakage(text: Optional[str]) -> bool:
    """Return True if text contains leaked AI instructions, reasoning, or meta-commentary."""
    if not text:
        return False
    s = str(text)
    for pat in _COMPILED_COMMENTARY_PATTERNS:
        if pat.search(s):
            return True
    return False


def sanitize_ai_text(text: Optional[str]) -> str:
    """
    Strip any leaked AI commentary, notes, preambles, or postscripts from generated text.
    Leaves only the pure resume content.
    """
    if not text:
        return ""
    s = str(text).strip()

    # 1. Remove conversational preambles
    s = re.sub(
        r"^(?:(?:Sure,?\s*)?(?:Here(?:'s|\s+is)|This\s+is|Below\s+is|A|An|The)\s+)?(?:the\s+)?(?:rewritten|improved|suggested|updated|new)?\s*(?:project\s+description|project\s+summary|project|bullet\s+point|bullet|summary|description|text|achievement|resume\s+bullet)?\s*:+\s*",
        "",
        s,
        flags=re.IGNORECASE,
    ).strip()

    # 2. Split lines and remove any line matching commentary patterns
    clean_lines = []
    for line in s.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue
        is_commentary = False
        for pat in _COMPILED_COMMENTARY_PATTERNS:
            if pat.match(line_clean):
                is_commentary = True
                break
        if not is_commentary:
            clean_lines.append(line)

    cleaned = "\n".join(clean_lines).strip()

    # 3. Strip trailing note blocks (e.g. "... achievement. (Note: I used ...)")
    cleaned = re.sub(r"\s*\(Note:\s*[^)]+\)\s*$", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s*\[Note:\s*[^\]]+\]\s*$", "", cleaned, flags=re.IGNORECASE).strip()

    # 4. Remove enclosing quotes if the entire text was wrapped in quotes
    if (cleaned.startswith('"') and cleaned.endswith('"')) or \
       (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()

    return cleaned


def _normalize_token(t: str) -> str:
    return re.sub(r"[^\w\d]", "", str(t)).lower().strip()


def validate_and_preserve(
    original: Dict[str, Any],
    updated: Dict[str, Any],
    allowed_deletions: Optional[Set[str]] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Deep verification and automatic preservation of original factual data.

    Compares the original canonical resume against the updated resume.
    If any factual data (contact, education, experience, bullets, projects,
    certifications, skills) was silently dropped, automatically restores it.
    Also strips any AI instruction/commentary leakage.

    Args:
        original: Original canonical resume dictionary (immutable source of truth).
        updated: Updated canonical resume dictionary after suggestions / edits.
        allowed_deletions: Set of target_ids or field keys explicitly accepted
                           by the user for deletion.

    Returns:
        (preserved_updated_dict, list_of_warnings)
    """
    warnings: List[str] = []
    if not isinstance(original, dict):
        return updated, warnings
    if not isinstance(updated, dict):
        return copy.deepcopy(original), ["Updated resume was not a valid dictionary — restored original."]

    out = copy.deepcopy(updated)
    del_set = allowed_deletions or set()

    # ── 1. Contact / Profile Preservation ────────────────────────────────────
    orig_prof = original.get("profile") if isinstance(original.get("profile"), dict) else {}
    upd_prof = out.get("profile") if isinstance(out.get("profile"), dict) else {}
    if not isinstance(out.get("profile"), dict):
        out["profile"] = copy.deepcopy(orig_prof)
        upd_prof = out["profile"]

    # Factual contact keys that MUST never disappear silently
    contact_fields = ["name", "email", "phone", "location", "github", "linkedin", "portfolio"]
    for field in contact_fields:
        # Check both top-level and profile-level
        orig_val = original.get(f"{field}_url") or original.get(field) or orig_prof.get(field) or ""
        upd_val = out.get(f"{field}_url") or out.get(field) or upd_prof.get(field) or ""

        if orig_val and str(orig_val).strip() and not (upd_val and str(upd_val).strip()):
            upd_prof[field] = str(orig_val).strip()
            if field in ("email", "phone", "location"):
                out[field] = str(orig_val).strip()
            elif field in ("github", "linkedin", "portfolio"):
                out[f"{field}_url"] = str(orig_val).strip()
            warnings.append(f"Restored missing contact field: '{field}' ({orig_val})")

    # Name preservation: candidate name must never be cleared or corrupted
    orig_name = original.get("candidate_name") or orig_prof.get("name") or ""
    upd_name = out.get("candidate_name") or upd_prof.get("name") or ""
    if orig_name and (not upd_name or upd_name.lower() in ("candidate", "enhanced", "unknown", "approved")):
        out["candidate_name"] = orig_name
        upd_prof["name"] = orig_name
        warnings.append(f"Restored candidate name: '{orig_name}'")

    # ── 2. Education Preservation ────────────────────────────────────────────
    orig_edu = original.get("education") or []
    upd_edu = out.get("education") or []
    if not isinstance(upd_edu, list):
        upd_edu = []

    # Map updated education by ID or normalized degree/institution
    preserved_edu = []
    upd_edu_matched = set()

    for o_idx, o_edu in enumerate(orig_edu):
        if not isinstance(o_edu, dict):
            continue
        o_id = o_edu.get("id") or f"edu_{o_idx}"
        if o_id in del_set:
            continue  # User explicitly approved deleting this education

        o_deg = str(o_edu.get("degree") or "").strip()
        o_inst = str(o_edu.get("institution") or o_edu.get("school") or "").strip()
        o_field = str(o_edu.get("field_of_study") or "").strip()
        o_start = str(o_edu.get("start_date") or "").strip()
        o_end = str(o_edu.get("end_date") or o_edu.get("year") or "").strip()
        o_gpa = str(o_edu.get("gpa") or o_edu.get("grade") or o_edu.get("cgpa") or "").strip()

        # Find matching item in updated
        matched_item = None
        for u_idx, u_edu in enumerate(upd_edu):
            if u_idx in upd_edu_matched or not isinstance(u_edu, dict):
                continue
            u_id = u_edu.get("id")
            if u_id and u_id == o_id:
                matched_item = u_edu
                upd_edu_matched.add(u_idx)
                break
            # Fuzzy match by institution, or by degree ONLY if institution is missing or matches
            u_deg = str(u_edu.get("degree") or "").strip()
            u_inst = str(u_edu.get("institution") or u_edu.get("school") or "").strip()
            inst_matches = bool(o_inst and u_inst and (_normalize_token(o_inst) in _normalize_token(u_inst) or _normalize_token(u_inst) in _normalize_token(o_inst)))
            deg_matches = bool(o_deg and u_deg and (_normalize_token(o_deg) in _normalize_token(u_deg) or _normalize_token(u_deg) in _normalize_token(o_deg)))
            if inst_matches or (deg_matches and (not u_inst or not o_inst or inst_matches)):
                matched_item = u_edu
                upd_edu_matched.add(u_idx)
                break

        if matched_item:
            # Preserve missing fields
            m_item = copy.deepcopy(matched_item)
            if not m_item.get("institution") and o_inst:
                m_item["institution"] = o_inst
            elif o_inst and len(o_inst) > len(str(m_item.get("institution") or "")):
                m_item["institution"] = o_inst
            if not m_item.get("degree") and o_deg:
                m_item["degree"] = o_deg
            if not m_item.get("field_of_study") and o_field:
                m_item["field_of_study"] = o_field
            if not m_item.get("start_date") and o_start:
                m_item["start_date"] = o_start
            if not m_item.get("end_date") and o_end:
                m_item["end_date"] = o_end
            if not (m_item.get("gpa") or m_item.get("grade")) and o_gpa:
                m_item["gpa"] = o_gpa
            preserved_edu.append(m_item)
        else:
            # Restoring dropped education entry!
            preserved_edu.append(copy.deepcopy(o_edu))
            warnings.append(f"Restored silently dropped education: '{o_deg} at {o_inst}'")

    # Keep genuinely new education items added in updated (skip if duplicate of existing institution)
    for u_idx, u_edu in enumerate(upd_edu):
        if u_idx not in upd_edu_matched and isinstance(u_edu, dict):
            u_inst = str(u_edu.get("institution") or u_edu.get("school") or "").strip()
            if not any(_normalize_token(str(o.get("institution", ""))) == _normalize_token(u_inst) for o in orig_edu if isinstance(o, dict)):
                preserved_edu.append(u_edu)

    out["education"] = preserved_edu

    # ── 3. Experience Preservation ───────────────────────────────────────────
    orig_exp = original.get("experience") or []
    upd_exp = out.get("experience") or []
    if not isinstance(upd_exp, list):
        upd_exp = []

    preserved_exp = []
    upd_exp_matched = set()

    for e_idx, o_exp in enumerate(orig_exp):
        if not isinstance(o_exp, dict):
            continue
        e_id = o_exp.get("id") or f"exp_{e_idx}"
        if e_id in del_set:
            continue

        o_comp = str(o_exp.get("company") or o_exp.get("organization") or "").strip()
        o_role = str(o_exp.get("role") or o_exp.get("title") or "").strip()
        o_start = str(o_exp.get("start_date") or "").strip()
        o_end = str(o_exp.get("end_date") or "").strip()
        o_bullets = o_exp.get("highlights") or o_exp.get("bullets") or []
        if isinstance(o_bullets, str):
            o_bullets = [o_bullets]

        matched_item = None
        for u_idx, u_exp in enumerate(upd_exp):
            if u_idx in upd_exp_matched or not isinstance(u_exp, dict):
                continue
            u_id = u_exp.get("id")
            if u_id and u_id == e_id:
                matched_item = u_exp
                upd_exp_matched.add(u_idx)
                break
            u_comp = str(u_exp.get("company") or u_exp.get("organization") or "").strip()
            u_role = str(u_exp.get("role") or u_exp.get("title") or "").strip()
            if (o_comp and u_comp and (_normalize_token(o_comp) in _normalize_token(u_comp) or _normalize_token(u_comp) in _normalize_token(o_comp))) or \
               (o_role and u_role and (_normalize_token(o_role) in _normalize_token(u_role) or _normalize_token(u_role) in _normalize_token(o_role))):
                matched_item = u_exp
                upd_exp_matched.add(u_idx)
                break

        if matched_item:
            m_item = copy.deepcopy(matched_item)
            if not m_item.get("company") and o_comp:
                m_item["company"] = o_comp
            if not m_item.get("role") and o_role:
                m_item["role"] = o_role
            if not m_item.get("start_date") and o_start:
                m_item["start_date"] = o_start
            if not m_item.get("end_date") and o_end:
                m_item["end_date"] = o_end

            # Verify bullets: must not silently drop original bullets
            u_bullets = m_item.get("highlights") or m_item.get("bullets") or []
            if isinstance(u_bullets, str):
                u_bullets = [u_bullets]

            # If updated bullets dropped items without user approval, restore missing
            if len(u_bullets) < len(o_bullets):
                # Restore bullets up to original count
                restored_bullets = list(u_bullets)
                for b_i in range(len(u_bullets), len(o_bullets)):
                    bullet_del_key = f"{e_id}_b{b_i}"
                    if bullet_del_key not in del_set:
                        restored_bullets.append(o_bullets[b_i])
                        warnings.append(f"Restored dropped experience bullet in '{o_role}': '{o_bullets[b_i][:40]}...'")
                m_item["highlights"] = restored_bullets
                m_item["bullets"] = restored_bullets

            # Sanitize each bullet from AI commentary
            cleaned_b = [sanitize_ai_text(b) for b in (m_item.get("highlights") or []) if sanitize_ai_text(b)]
            m_item["highlights"] = cleaned_b
            m_item["bullets"] = cleaned_b

            preserved_exp.append(m_item)
        else:
            preserved_exp.append(copy.deepcopy(o_exp))
            warnings.append(f"Restored silently dropped experience: '{o_role} at {o_comp}'")

    for u_idx, u_exp in enumerate(upd_exp):
        if u_idx not in upd_exp_matched and isinstance(u_exp, dict):
            preserved_exp.append(u_exp)

    out["experience"] = preserved_exp

    # ── 4. Project Preservation ──────────────────────────────────────────────
    orig_proj = original.get("projects") or []
    upd_proj = out.get("projects") or []
    if not isinstance(upd_proj, list):
        upd_proj = []

    preserved_proj = []
    upd_proj_matched = set()

    for p_idx, o_p in enumerate(orig_proj):
        if not isinstance(o_p, dict):
            continue
        p_id = o_p.get("id") or f"proj_{p_idx}"
        if p_id in del_set:
            continue

        o_name = str(o_p.get("name") or o_p.get("title") or "").strip()
        o_techs = o_p.get("technologies") or o_p.get("tech_stack") or []
        if isinstance(o_techs, str):
            o_techs = [t.strip() for t in o_techs.split(",") if t.strip()]

        matched_item = None
        for u_idx, u_p in enumerate(upd_proj):
            if u_idx in upd_proj_matched or not isinstance(u_p, dict):
                continue
            u_id = u_p.get("id")
            if u_id and u_id == p_id:
                matched_item = u_p
                upd_proj_matched.add(u_idx)
                break
            u_name = str(u_p.get("name") or u_p.get("title") or "").strip()
            if o_name and u_name and (_normalize_token(o_name) in _normalize_token(u_name) or _normalize_token(u_name) in _normalize_token(o_name)):
                matched_item = u_p
                upd_proj_matched.add(u_idx)
                break

        if matched_item:
            m_p = copy.deepcopy(matched_item)
            # Technologies must never disappear
            u_techs = m_p.get("technologies") or m_p.get("tech_stack") or []
            if isinstance(u_techs, str):
                u_techs = [t.strip() for t in u_techs.split(",") if t.strip()]
            for ot in o_techs:
                if ot.lower() not in [t.lower() for t in u_techs]:
                    u_techs.append(ot)
            m_p["technologies"] = u_techs

            # Sanitize description & bullets
            if m_p.get("description"):
                m_p["description"] = sanitize_ai_text(m_p["description"])
            clean_hl = [sanitize_ai_text(h) for h in (m_p.get("highlights") or m_p.get("bullets") or []) if sanitize_ai_text(h)]
            m_p["highlights"] = clean_hl
            m_p["bullets"] = clean_hl

            # Preserve URLs
            if not m_p.get("github_url") and o_p.get("github_url"):
                m_p["github_url"] = o_p["github_url"]
            if not m_p.get("live_url") and o_p.get("live_url"):
                m_p["live_url"] = o_p["live_url"]

            preserved_proj.append(m_p)
        else:
            preserved_proj.append(copy.deepcopy(o_p))
            warnings.append(f"Restored silently dropped project: '{o_name}'")

    for u_idx, u_p in enumerate(upd_proj):
        if u_idx not in upd_proj_matched and isinstance(u_p, dict):
            preserved_proj.append(u_p)

    out["projects"] = preserved_proj

    # ── 5. Certifications Preservation ───────────────────────────────────────
    orig_cert = original.get("certifications") or []
    upd_cert = out.get("certifications") or []
    if not isinstance(upd_cert, list):
        upd_cert = []

    preserved_cert = []
    upd_cert_matched = set()

    for c_idx, o_c in enumerate(orig_cert):
        o_name = str(o_c.get("name") if isinstance(o_c, dict) else o_c).strip()
        c_id = o_c.get("id") if isinstance(o_c, dict) else f"cert_{c_idx}"
        if c_id in del_set:
            continue

        matched_c = None
        for u_idx, u_c in enumerate(upd_cert):
            if u_idx in upd_cert_matched:
                continue
            u_name = str(u_c.get("name") if isinstance(u_c, dict) else u_c).strip()
            if o_name and u_name and (_normalize_token(o_name) in _normalize_token(u_name) or _normalize_token(u_name) in _normalize_token(o_name)):
                matched_c = u_c
                upd_cert_matched.add(u_idx)
                break

        if matched_c:
            m_c = copy.deepcopy(matched_c) if isinstance(matched_c, dict) else {"name": str(matched_c)}
            if isinstance(o_c, dict):
                if not m_c.get("issuer") and o_c.get("issuer"):
                    m_c["issuer"] = o_c["issuer"]
                if not m_c.get("issue_date") and o_c.get("issue_date"):
                    m_c["issue_date"] = o_c["issue_date"]
                if not m_c.get("credential_url") and o_c.get("credential_url"):
                    m_c["credential_url"] = o_c["credential_url"]
            preserved_cert.append(m_c)
        else:
            preserved_cert.append(copy.deepcopy(o_c) if isinstance(o_c, dict) else {"name": str(o_c)})
            warnings.append(f"Restored silently dropped certification: '{o_name}'")

    for u_idx, u_c in enumerate(upd_cert):
        if u_idx not in upd_cert_matched:
            preserved_cert.append(u_c)

    out["certifications"] = preserved_cert

    # ── 6. Skills Preservation ───────────────────────────────────────────────
    # Ensure all original skills remain present
    orig_skills_flat: Set[str] = set()
    raw_os = original.get("skills") or {}
    if isinstance(raw_os, dict):
        for s_list in raw_os.values():
            if isinstance(s_list, list):
                orig_skills_flat.update([str(s).strip() for s in s_list if str(s).strip()])
    elif isinstance(raw_os, list):
        orig_skills_flat.update([str(s).strip() for s in raw_os if str(s).strip()])

    upd_skills = out.get("skills") or {}
    if isinstance(upd_skills, dict):
        current_upd_skills = set()
        for s_list in upd_skills.values():
            if isinstance(s_list, list):
                current_upd_skills.update([str(s).strip().lower() for s in s_list if str(s).strip()])
        # If any original skill is missing, add to technical category
        tech_target = upd_skills.setdefault("technical", [])
        if isinstance(tech_target, list):
            for os_item in orig_skills_flat:
                if os_item.lower() not in current_upd_skills:
                    tech_target.append(os_item)
    elif isinstance(upd_skills, list):
        upd_lower = {str(s).strip().lower() for s in upd_skills}
        for os_item in orig_skills_flat:
            if os_item.lower() not in upd_lower:
                upd_skills.append(os_item)
        out["skills"] = upd_skills

    # ── 7. Summary AI Commentary Sanitization ────────────────────────────────
    if out.get("summary"):
        out["summary"] = sanitize_ai_text(out["summary"])
    if isinstance(out.get("profile"), dict) and out["profile"].get("summary"):
        out["profile"]["summary"] = sanitize_ai_text(out["profile"]["summary"])

    return out, warnings
