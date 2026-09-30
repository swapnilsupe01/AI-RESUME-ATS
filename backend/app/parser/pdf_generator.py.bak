"""
ATS-Compliant PDF Generator — Arav Standard Design.
Renders clean, single-column, ATS-parseable resume PDFs matching the Arav Mahind reference layout.

Features:
- Standard US Letter format (612 x 792 pt) with 38pt balanced margins.
- Clean Arav Design hierarchy:
  * Centered bold candidate header with contact & platform links (GitHub, LinkedIn, LeetCode, Twitter, Portfolio).
  * Uppercase bold section headings with subtle horizontal divider rules.
  * Structured categorized skills layout with bold labels.
  * Left-aligned job/project titles with right-aligned dates & metadata.
  * Crisp bullet points with precise typography (12.5pt line-height) preventing bloated page overflows.
  * Smart orphan-prevention & keep-with-next logic for section headers.
  * 100% defensive: handles raw strings, nested canonical structures, missing fields, and unicode symbols without 500 errors.
"""

from typing import Dict, Any, List, Optional, Tuple
import re
import pymupdf as fitz


# ---------------------------------------------------------------------------
# Unicode & Character Normalization
# ---------------------------------------------------------------------------

_CHAR_REPLACEMENTS = {
    "\u2014": " - ", "\u2013": " - ", "\u2012": " - ", "\u2015": " - ",
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
    "\u00a0": " ", "\t": "    ",
    "\u2022": "*", "\u25cf": "*", "\u25aa": "*", "\u2023": "*",
    "\u2219": "*", "\u00b7": "*", "\u2756": "*", "\u25c6": "*", "\u25c8": "*",
    "\u2026": "...",
    "\u2192": "->", "\u21d2": "=>", "\u2794": "->", "\u27a4": "->",
    "\u2713": "[x]", "\u2714": "[x]", "\u2717": "[ ]", "\u2718": "[ ]",
    "\u200b": "", "\ufeff": "",
}


def _clean_str(val: Any) -> str:
    """Sanitize, normalize unicode characters, and strip leading bullet artifacts."""
    if val is None:
        return ""
    s = str(val).strip()
    if not s:
        return ""

    # Strip leading bullet/symbol markers like ❖, ●, •, -, *
    s = re.sub(r'^[❖●•\-\*\s]+', '', s)

    for orig, rep in _CHAR_REPLACEMENTS.items():
        s = s.replace(orig, rep)

    # Filter non-latin characters that standard Type-1 Helvetica cannot render
    clean = []
    for ch in s:
        code = ord(ch)
        if code < 128 or (160 <= code <= 255):
            clean.append(ch)
        else:
            clean.append(" ")
    return re.sub(r'\s+', ' ', ''.join(clean)).strip()


def _ensure_list(val: Any) -> List[str]:
    """Ensure highlight/bullet inputs are cleanly parsed into a list of strings."""
    if val is None:
        return []
    if isinstance(val, list):
        out = []
        for item in val:
            if isinstance(item, dict):
                text = item.get("text") or item.get("name") or str(item)
                cleaned = _clean_str(text)
                if cleaned and cleaned.lower() not in ('*', '•', '-', 'bullet'):
                    out.append(cleaned)
            elif item is not None:
                cleaned = _clean_str(str(item))
                if cleaned and cleaned.lower() not in ('*', '•', '-', 'bullet'):
                    out.append(cleaned)
        return out
    if isinstance(val, (str, bytes)):
        s = _clean_str(str(val))
        if not s:
            return []
        if "\n" in s:
            return [_clean_str(line) for line in s.splitlines() if _clean_str(line) and _clean_str(line).lower() not in ('*', '•', '-', 'bullet')]
        return [s]
    cleaned = _clean_str(str(val))
    return [cleaned] if cleaned else []


def _get_val(d: Any, *keys: str, default: str = "") -> str:
    """Fetch the first non-empty string value across multiple potential keys."""
    if not isinstance(d, dict):
        return default
    for k in keys:
        v = d.get(k)
        if v is not None:
            sv = _clean_str(v)
            if sv:
                return sv
    return default


def _wrap_text_lines(text: str, fs: float, max_w: float, fn: str = "helv") -> List[str]:
    """Wrap text into lines accurately using fitz.get_text_length."""
    if not text:
        return []
    words = text.split()
    if not words:
        return []

    lines = []
    curr = []
    for w in words:
        cand = " ".join(curr + [w])
        if fitz.get_text_length(cand, fontname=fn, fontsize=fs) <= max_w:
            curr.append(w)
        else:
            if curr:
                lines.append(" ".join(curr))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))
    return lines if lines else [text]


# ---------------------------------------------------------------------------
# ATS PDF Generator Class (Arav Design Standard)
# ---------------------------------------------------------------------------

class ATSPdfGenerator:
    """
    Renders structured resume data into an ATS-friendly, 2-page or 1-page PDF
    following the Arav Mahind professional resume standard.
    """

    PAGE_W = 612.0  # US Letter Width
    PAGE_H = 792.0  # US Letter Height
    MX = 38.0       # Left/Right Margin
    MT = 34.0       # Top Margin
    MB = 34.0       # Bottom Margin

    # Palette
    C_NAME    = (0.05, 0.05, 0.05)
    C_TEXT    = (0.12, 0.12, 0.14)
    C_HEADER  = (0.08, 0.08, 0.10)
    C_RULE    = (0.68, 0.68, 0.72)
    C_MUTED   = (0.35, 0.35, 0.40)

    def __init__(self):
        self.cw = self.PAGE_W - (2 * self.MX)

    def generate_pdf(self, resume_data: Dict[str, Any]) -> bytes:
        if not isinstance(resume_data, dict):
            resume_data = {}

        doc = fitz.open()
        page = doc.new_page(width=self.PAGE_W, height=self.PAGE_H)
        cw = self.cw
        y = self.MT

        def ensure_space(needed: float) -> fitz.Page:
            nonlocal page, y
            if y + needed > self.PAGE_H - self.MB:
                page = doc.new_page(width=self.PAGE_W, height=self.PAGE_H)
                y = self.MT
            return page

        def draw_centered(text: str, fs: float = 10.0, fn: str = "helv", col: Any = self.C_TEXT, space_after: float = 3.0):
            nonlocal y
            text = _clean_str(text)
            if not text:
                return
            ensure_space(fs + space_after + 2.0)
            tw = fitz.get_text_length(text, fontname=fn, fontsize=fs)
            x = max(self.MX, (self.PAGE_W - tw) / 2.0)
            page.insert_text(fitz.Point(x, y + fs * 0.9), text, fontsize=fs, fontname=fn, color=col)
            y += fs + space_after

        def draw_header(title: str):
            nonlocal y
            title = _clean_str(title).upper()
            if not title:
                return
            ensure_space(34.0)
            y += 7.0
            page.insert_text(fitz.Point(self.MX, y + 10.0), title, fontsize=11.0, fontname="hebo", color=self.C_HEADER)
            y += 12.0
            page.draw_line(fitz.Point(self.MX, y), fitz.Point(self.PAGE_W - self.MX, y), color=self.C_RULE, width=0.65)
            y += 5.0

        def draw_two_col_item(left_bold: str, right_muted: str = "", sub_left: str = "", sub_right: str = "", space_after: float = 2.5):
            nonlocal y
            left = _clean_str(left_bold)
            right = _clean_str(right_muted)
            sub_l = _clean_str(sub_left)
            sub_r = _clean_str(sub_right)
            if not left and not sub_l:
                return

            needed = 14.0 + (13.0 if sub_l or sub_r else 0.0) + space_after
            ensure_space(needed)

            # Line 1
            if left:
                page.insert_text(fitz.Point(self.MX, y + 9.5), left, fontsize=10.0, fontname="hebo", color=self.C_NAME)
            if right:
                rw = fitz.get_text_length(right, fontname="hebi", fontsize=9.0)
                page.insert_text(fitz.Point(self.PAGE_W - self.MX - rw, y + 9.5), right, fontsize=9.0, fontname="hebi", color=self.C_MUTED)
            y += 13.0

            # Line 2 (optional sub info)
            if sub_l or sub_r:
                if sub_l:
                    page.insert_text(fitz.Point(self.MX, y + 8.5), sub_l, fontsize=9.0, fontname="helv", color=self.C_TEXT)
                if sub_r:
                    srw = fitz.get_text_length(sub_r, fontname="helv", fontsize=9.0)
                    page.insert_text(fitz.Point(self.PAGE_W - self.MX - srw, y + 8.5), sub_r, fontsize=9.0, fontname="helv", color=self.C_MUTED)
                y += 12.0
            y += space_after

        def draw_bullet(text: str, indent: float = 10.0, space_after: float = 2.0):
            nonlocal y
            text = _clean_str(text)
            if not text or text.lower() in ('*', '•', '-', 'bullet'):
                return

            max_w = cw - indent - 10.0
            lines = _wrap_text_lines(text, fs=9.5, max_w=max_w, fn="helv")
            if not lines:
                return

            needed = len(lines) * 12.5 + space_after
            ensure_space(needed)

            bx = self.MX + indent
            tx = bx + 9.0
            page.draw_circle(fitz.Point(bx + 2.0, y + 6.0), 1.5, color=self.C_TEXT, fill=self.C_TEXT)
            for l in lines:
                page.insert_text(fitz.Point(tx, y + 8.5), l, fontsize=9.5, fontname="helv", color=self.C_TEXT)
                y += 12.5
            y += space_after

        def draw_paragraph(text: str, fs: float = 9.5, indent: float = 0.0, space_after: float = 3.0):
            nonlocal y
            text = _clean_str(text)
            if not text:
                return
            max_w = cw - indent
            lines = _wrap_text_lines(text, fs=fs, max_w=max_w, fn="helv")
            needed = len(lines) * 12.5 + space_after
            ensure_space(needed)
            for l in lines:
                page.insert_text(fitz.Point(self.MX + indent, y + 8.5), l, fontsize=fs, fontname="helv", color=self.C_TEXT)
                y += 12.5
            y += space_after

        # ── 1. Header (Arav Mahind Style Centered) ───────────────────────────
        profile = resume_data.get("profile") if isinstance(resume_data.get("profile"), dict) else {}
        name = (
            _get_val(resume_data, "candidate_name")
            or _get_val(profile, "name")
            or "CANDIDATE NAME"
        ).upper()

        email = _get_val(resume_data, "email") or _get_val(profile, "email")
        phone = _get_val(resume_data, "phone") or _get_val(profile, "phone")
        loc = _get_val(resume_data, "location") or _get_val(profile, "location")
        github = _get_val(resume_data, "github_url") or _get_val(profile, "github")
        linkedin = _get_val(resume_data, "linkedin_url") or _get_val(profile, "linkedin")
        portfolio = _get_val(resume_data, "portfolio_url") or _get_val(profile, "portfolio")

        draw_centered(name, fs=15.0, fn="hebo", col=self.C_NAME, space_after=3.5)

        contact_line1 = " | ".join([p for p in [email, phone, loc] if p])
        if contact_line1:
            draw_centered(contact_line1, fs=10.0, fn="helv", col=self.C_TEXT, space_after=3.0)

        links_line_parts = []
        if github:
            gh_clean = github.replace("https://", "").replace("http://", "").rstrip("/")
            links_line_parts.append(f"GitHub: {gh_clean}")
        if linkedin:
            li_clean = linkedin.replace("https://", "").replace("http://", "").rstrip("/")
            links_line_parts.append(f"LinkedIn: {li_clean}")
        if portfolio:
            pf_clean = portfolio.replace("https://", "").replace("http://", "").rstrip("/")
            links_line_parts.append(f"Portfolio: {pf_clean}")

        if links_line_parts:
            draw_centered(" | ".join(links_line_parts), fs=9.0, fn="helv", col=self.C_MUTED, space_after=3.5)

        y += 2.0

        # ── 2. Career Objective / Professional Summary (if present) ───────────
        summary = _get_val(resume_data, "summary") or _get_val(profile, "summary")
        if summary:
            draw_header("Professional Summary")
            draw_paragraph(summary, fs=9.5, indent=0.0, space_after=3.0)

        # ── 3. Education Section (Fresher Recommended Priority) ───────────────
        edu_list = resume_data.get("education") or []
        if isinstance(edu_list, list) and edu_list:
            drawn_edu_hdr = False
            for edu in edu_list:
                if not isinstance(edu, dict):
                    continue
                school = _get_val(edu, "institution", "school", "university", "college", "institute", "academy")
                deg = _get_val(edu, "degree", "qualification")
                field = _get_val(edu, "field_of_study", "major", "stream", "branch")
                
                # Combine degree and field of study if both exist
                if deg and field and field.lower() not in deg.lower():
                    degree_display = f"{deg} in {field}"
                else:
                    degree_display = deg or field or ""

                # Format full dates (start - end / Present)
                dates = _get_val(edu, "dates", "period")
                if not dates:
                    start = _get_val(edu, "start_date")
                    end = _get_val(edu, "end_date", "year", "graduation_year")
                    is_curr = _get_val(edu, "current")
                    if start and end:
                        dates = f"{start} – {end}"
                    elif start and is_curr:
                        dates = f"{start} – Present"
                    elif start:
                        dates = f"{start} – Present" if (isinstance(start, str) and ("present" in start.lower() or "current" in start.lower() or "ongoing" in start.lower())) else start
                    elif end:
                        dates = end

                gpa = _get_val(edu, "gpa", "percentage", "score", "cgpa")

                if not school and not degree_display:
                    continue

                if not drawn_edu_hdr:
                    draw_header("Education")
                    drawn_edu_hdr = True

                sub = f"{degree_display} | CGPA/Score: {gpa}" if (degree_display and gpa) else (degree_display or (f"CGPA/Score: {gpa}" if gpa else ""))
                draw_two_col_item(school or degree_display, f"({dates})" if dates else "", sub_left=sub, space_after=3.0)

        # ── 4. Technical and Relevant Skills ─────────────────────────────────
        raw_skills = resume_data.get("skills") or resume_data.get("extracted_skills") or {}
        skill_rows: List[Tuple[str, str]] = []

        if isinstance(raw_skills, dict):
            LABELS = {
                "technical":  "Programming Languages",
                "frameworks": "Frameworks & Libraries",
                "databases":  "Databases & Storage",
                "cloud":      "Cloud & DevOps",
                "tools":      "Developer Tools & Platforms",
                "soft":       "Professional Skills",
                "other":      "Other Competencies",
            }
            for k, label in LABELS.items():
                items = raw_skills.get(k) or []
                if isinstance(items, list):
                    clean_items = [_clean_str(x) for x in items if _clean_str(x)]
                    if clean_items:
                        skill_rows.append((label, ", ".join(clean_items)))
                elif isinstance(items, str) and items.strip():
                    skill_rows.append((label, _clean_str(items)))
        elif isinstance(raw_skills, list) and raw_skills:
            clean_items = []
            for s in raw_skills:
                if isinstance(s, dict):
                    clean_items.extend([_clean_str(x) for x in s.get("skills", []) if _clean_str(x)])
                elif s:
                    clean_items.append(_clean_str(s))
            if clean_items:
                skill_rows.append(("Technical Skills", ", ".join(clean_items[:35])))

        if skill_rows:
            draw_header("Technical Skills")
            for label, items_str in skill_rows:
                full_line = f"{label}: {items_str}"
                draw_bullet(full_line, indent=6.0, space_after=2.0)

        # ── 5. Academic & Technical Projects (Priority for Freshers) ─────────
        proj_list = resume_data.get("projects") or []
        if isinstance(proj_list, list) and proj_list:
            drawn_proj_hdr = False
            for proj in proj_list:
                if not isinstance(proj, dict):
                    continue
                pname = _get_val(proj, "name", "title")
                purl = _get_val(proj, "github_url", "url", "live_url")
                techs = _ensure_list(proj.get("technologies") or proj.get("tech_stack"))
                desc = _get_val(proj, "description")

                # Filter out garbage placeholder parsed lines
                if not pname or pname.lower() in ('*', '•', '-', 'project', 'projects', '[github]'):
                    continue

                if not drawn_proj_hdr:
                    draw_header("Key Projects")
                    drawn_proj_hdr = True

                right_link = f"[{purl}]" if purl else ""
                draw_two_col_item(pname, right_link, space_after=1.5)

                if techs:
                    draw_paragraph("Tech Stack: " + ", ".join(techs), fs=9.0, indent=8.0, space_after=1.5)

                if desc:
                    draw_bullet(desc, indent=8.0, space_after=2.0)

                bullets = _ensure_list(proj.get("highlights") or proj.get("bullets"))
                for b in bullets:
                    draw_bullet(b, indent=8.0, space_after=2.0)

        # ── 6. Internship / Work Experience (included only if applicable) ────
        exp_list = resume_data.get("experience") or []
        if isinstance(exp_list, list) and exp_list:
            drawn_exp_hdr = False
            for exp in exp_list:
                if not isinstance(exp, dict):
                    continue
                role = _get_val(exp, "role", "title", default="")
                comp = _get_val(exp, "company", "organization")
                dates = _get_val(exp, "dates", "period")
                if not dates:
                    start = _get_val(exp, "start_date")
                    end = _get_val(exp, "end_date")
                    parts = [p for p in [start, end] if p]
                    dates = " - ".join(parts) if parts else ""
                loc_val = _get_val(exp, "location")

                # Filter out pure symbol lines or bullet artifacts
                if not role and not comp:
                    continue
                if role.lower() in ('*', '•', '-', 'bullet', 'experience'):
                    continue

                if not drawn_exp_hdr:
                    draw_header("Professional Experience & Internships")
                    drawn_exp_hdr = True

                title_line = f"{role} | {comp}" if (role and comp) else (role or comp)
                date_line = f"({dates})" if dates else ""
                if loc_val and date_line:
                    date_line = f"{loc_val} | {date_line}"
                elif loc_val:
                    date_line = loc_val

                draw_two_col_item(title_line, date_line, space_after=2.0)

                # Bullets
                bullets = _ensure_list(exp.get("highlights") or exp.get("bullets") or exp.get("responsibilities") or exp.get("description"))
                for b in bullets:
                    draw_bullet(b, indent=8.0)

                techs = _ensure_list(exp.get("technologies") or exp.get("tech_stack"))
                if techs:
                    draw_paragraph("Tech Stack: " + ", ".join(techs), fs=8.5, indent=8.0, space_after=2.0)

        # ── 7. Certifications (if present) ───────────────────────────────────
        certs = resume_data.get("certifications") or []
        if isinstance(certs, list) and certs:
            drawn_cert_hdr = False
            for c in certs:
                if isinstance(c, dict):
                    cname = _get_val(c, "name", "title")
                    issuer = _get_val(c, "issuer", "authority")
                    date = _get_val(c, "issue_date", "date", "year")
                    if not cname:
                        continue
                    line = f"{cname} - {issuer}" if issuer else cname
                    if date:
                        line += f" ({date})"
                    if not drawn_cert_hdr:
                        draw_header("Certifications")
                        drawn_cert_hdr = True
                    draw_bullet(line, indent=6.0)
                elif isinstance(c, str) and _clean_str(c):
                    cl = _clean_str(c)
                    if cl.lower() not in ('*', '•', '-'):
                        if not drawn_cert_hdr:
                            draw_header("Certifications")
                            drawn_cert_hdr = True
                        draw_bullet(cl, indent=6.0)

        # ── 8. Achievements & Activities (if present) ────────────────────────
        ach_list = resume_data.get("achievements") or []
        if isinstance(ach_list, list) and ach_list:
            drawn_ach_hdr = False
            for ach in ach_list:
                if isinstance(ach, dict):
                    title = _get_val(ach, "title", "name", "role")
                    org = _get_val(ach, "organization", "institution", "company")
                    det = _get_val(ach, "description", "details")
                    date = _get_val(ach, "date", "year")
                    top = f"{title} | {org}" if (title and org) else (title or org or det or "")
                    if not top:
                        continue
                    if date:
                        top += f" ({date})"
                    if det and det != top:
                        top += f" - {det}"
                    if not drawn_ach_hdr:
                        draw_header("Achievements & Activities")
                        drawn_ach_hdr = True
                    draw_bullet(top, indent=6.0)
                elif isinstance(ach, str) and _clean_str(ach):
                    cl = _clean_str(ach)
                    if cl.lower() not in ('*', '•', '-'):
                        if not drawn_ach_hdr:
                            draw_header("Achievements & Activities")
                            drawn_ach_hdr = True
                        draw_bullet(cl, indent=6.0)

        # ── 9. Leadership / Volunteering / Custom Sections ───────────────────
        custom_secs = resume_data.get("custom_sections") or []
        if isinstance(custom_secs, list) and custom_secs:
            for sec in custom_secs:
                if not isinstance(sec, dict):
                    continue
                sec_title = _clean_str(_get_val(sec, "title", "heading", "name") or "Leadership & Activities")
                # Exclude pure hobbies from custom sections as they are drawn in step 10
                if "hobby" in sec_title.lower() or "interest" in sec_title.lower():
                    continue
                items = sec.get("items") or sec.get("bullets") or []
                if isinstance(items, str):
                    items = [it.strip() for it in items.splitlines() if it.strip()]
                if not isinstance(items, list) or not items:
                    continue
                drawn_sec_hdr = False
                for item in items:
                    if isinstance(item, dict):
                        it_text = _get_val(item, "text", "description", "name")
                    else:
                        it_text = _clean_str(str(item))
                    if it_text and it_text.lower() not in ('*', '•', '-'):
                        if not drawn_sec_hdr:
                            draw_header(sec_title)
                            drawn_sec_hdr = True
                        draw_bullet(it_text, indent=6.0)

        # ── 10. Interests & Hobbies (if present) ─────────────────────────────
        hobbies_list = resume_data.get("hobbies") or resume_data.get("interests") or []
        # Also check custom sections for hobbies
        if not hobbies_list and isinstance(custom_secs, list):
            for sec in custom_secs:
                if isinstance(sec, dict) and ("hobby" in str(sec.get("title", "")).lower() or "interest" in str(sec.get("title", "")).lower()):
                    hobbies_list = sec.get("items") or []
                    break

        drawn_hobbies_hdr = False
        if isinstance(hobbies_list, str) and hobbies_list.strip():
            hobbies_list = [h.strip() for h in re.split(r'[\n;•]+', hobbies_list) if h.strip()]
        if isinstance(hobbies_list, list) and hobbies_list:
            for h in hobbies_list:
                if isinstance(h, dict):
                    h_val = _get_val(h, "name", "title", "hobby", "interest", "description")
                else:
                    h_val = _clean_str(str(h))
                if h_val and h_val.lower() not in ('*', '•', '-'):
                    if not drawn_hobbies_hdr:
                        draw_header("Hobbies & Interests")
                        drawn_hobbies_hdr = True
                    draw_bullet(h_val, indent=6.0)

        # Final PDF byte compilation with fallback safety
        try:
            pdf_bytes = doc.tobytes(deflate=True)
        except Exception:
            pdf_bytes = doc.write(deflate=True)
        doc.close()
        return pdf_bytes


pdf_generator = ATSPdfGenerator()


def generate_pdf(resume_data: Dict[str, Any]) -> bytes:
    """Module-level convenience wrapper for ATSPdfGenerator.generate_pdf."""
    return pdf_generator.generate_pdf(resume_data)
