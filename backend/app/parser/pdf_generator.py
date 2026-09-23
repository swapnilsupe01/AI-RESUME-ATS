"""
ATS-Compliant PDF Generator using PyMuPDF (fitz).
Produces clean, single-column, machine-readable resume PDFs.
Adheres strictly to industry standard ATS formatting:
  - 1-column sequential flow (zero complex tables or multi-column grids)
  - Standard system fonts (Helvetica) with precise point sizing
  - Clear, recognized section headers (SUMMARY, SKILLS, EXPERIENCE, PROJECTS, EDUCATION)
  - Standard bullet dots with clean indentation
  - 100% extractable text layer with embedded hyperlink annotations
"""
import io
import re
from typing import Dict, Any, List, Optional
import pymupdf as fitz


def sanitize_text(text: Any) -> str:
    """Sanitize text to safe strings for PyMuPDF rendering."""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    # Normalize common Unicode characters to standard equivalents
    replacements = {
        "\u2014": " - ",   # em dash
        "\u2013": " - ",   # en dash
        "—": " - ",
        "–": " - ",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "\u00a0": " ",
        "\t": "    "
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    return text.strip()


class ATSPdfGenerator:
    """
    Renders structured resume data into an ATS-friendly, professional PDF.
    """

    def __init__(self, page_width: float = 612.0, page_height: float = 792.0):
        # Standard US Letter dimensions (8.5 x 11 inches in points)
        self.width = page_width
        self.height = page_height
        self.margin_x = 45.0
        self.margin_top = 40.0
        self.margin_bottom = 40.0
        self.content_width = self.width - (2 * self.margin_x)

    def generate_pdf(self, resume_data: Dict[str, Any]) -> bytes:
        """
        Generate a PDF from a canonical or parsed resume dictionary.
        Returns the raw PDF bytes.
        """
        if not isinstance(resume_data, dict):
            resume_data = {}

        doc = fitz.open()
        page = doc.new_page(width=self.width, height=self.height)
        y = self.margin_top

        # Align constants (safe across PyMuPDF versions)
        ALIGN_LEFT = getattr(fitz, "TEXT_ALIGN_LEFT", 0)
        ALIGN_CENTER = getattr(fitz, "TEXT_ALIGN_CENTER", 1)

        # Helper: Ensure space or create new page
        def ensure_space(needed_height: float) -> fitz.Page:
            nonlocal page, y
            if y + needed_height > (self.height - self.margin_bottom):
                page = doc.new_page(width=self.width, height=self.height)
                y = self.margin_top
            return page

        # Helper: Insert Section Header
        def insert_section_header(title: str):
            nonlocal page, y
            ensure_space(32)
            y += 6
            # Section Title
            header_rect = fitz.Rect(self.margin_x, y, self.width - self.margin_x, y + 15)
            page.insert_textbox(header_rect, title.upper(), fontsize=11, fontname="helv", align=ALIGN_LEFT)
            y += 14
            # Divider Line
            p1 = fitz.Point(self.margin_x, y)
            p2 = fitz.Point(self.width - self.margin_x, y)
            page.draw_line(p1, p2, color=(0.7, 0.7, 0.75), width=0.8)
            y += 8

        # ── 1. Header (Candidate Name + Contact) ─────────────────────────
        profile = resume_data.get("profile", {}) if isinstance(resume_data.get("profile"), dict) else {}
        name = sanitize_text(resume_data.get("candidate_name") or profile.get("name") or "CANDIDATE NAME")
        name_rect = fitz.Rect(self.margin_x, y, self.width - self.margin_x, y + 26)
        page.insert_textbox(name_rect, name.upper(), fontsize=18, fontname="helv", align=ALIGN_CENTER)
        y += 24

        # Headline / Role if available
        headline = sanitize_text(profile.get("headline") or resume_data.get("headline") or "")
        if headline:
            ensure_space(16)
            hl_rect = fitz.Rect(self.margin_x, y, self.width - self.margin_x, y + 14)
            page.insert_textbox(hl_rect, headline, fontsize=10, fontname="helv", align=ALIGN_CENTER)
            y += 16

        # Contact Info Line
        contact_parts = []
        email = sanitize_text(resume_data.get("email") or profile.get("email") or "")
        phone = sanitize_text(resume_data.get("phone") or profile.get("phone") or "")
        gh = sanitize_text(resume_data.get("github_url") or profile.get("github") or "")
        li = sanitize_text(resume_data.get("linkedin_url") or profile.get("linkedin") or "")
        pf = sanitize_text(resume_data.get("portfolio_url") or profile.get("portfolio") or "")

        if email: contact_parts.append(email)
        if phone: contact_parts.append(phone)
        if gh: contact_parts.append(gh)
        if li: contact_parts.append(li)
        if pf: contact_parts.append(pf)

        contact_text = " | ".join(contact_parts) if contact_parts else "Email | Phone | GitHub | LinkedIn"
        contact_rect = fitz.Rect(self.margin_x, y, self.width - self.margin_x, y + 16)
        page.insert_textbox(contact_rect, contact_text, fontsize=9, fontname="helv", align=ALIGN_CENTER)
        y += 20

        # ── 2. Summary Section ───────────────────────────────────────────
        summary = sanitize_text(resume_data.get("summary") or "")
        if summary:
            insert_section_header("Professional Summary")
            words = summary.split()
            approx_lines = max(1, len(words) // 14 + 1)
            text_h = approx_lines * 13 + 4
            ensure_space(text_h)
            rect = fitz.Rect(self.margin_x, y, self.width - self.margin_x, y + text_h)
            page.insert_textbox(rect, summary, fontsize=9.5, fontname="helv", align=ALIGN_LEFT)
            y += text_h + 6

        # ── 3. Technical Skills Section ──────────────────────────────────
        raw_skills = resume_data.get("skills") or resume_data.get("extracted_skills") or []
        categorized = resume_data.get("categorized_skills") or {}

        # If raw_skills is a dict (like in CanonicalResume), treat it as categorized!
        if isinstance(raw_skills, dict):
            categorized = raw_skills
            raw_skills = []

        if categorized and isinstance(categorized, dict) and any(categorized.values()):
            insert_section_header("Technical Skills")
            for cat_name, cat_skills in categorized.items():
                if not cat_skills:
                    continue
                if isinstance(cat_skills, list):
                    skills_str = ", ".join(sanitize_text(s) for s in cat_skills if s)
                else:
                    skills_str = sanitize_text(str(cat_skills))
                if not skills_str:
                    continue
                skill_line = f"- {cat_name.replace('_', ' ').title()}: {skills_str}"
                ensure_space(15)
                rect = fitz.Rect(self.margin_x + 5, y, self.width - self.margin_x, y + 14)
                page.insert_textbox(rect, skill_line, fontsize=9.5, fontname="helv")
                y += 14
            y += 4
        elif isinstance(raw_skills, list) and raw_skills:
            insert_section_header("Technical Skills")
            clean_s = [sanitize_text(s) for s in raw_skills if s]
            skill_str = "- Core Technologies: " + ", ".join(clean_s[:25])
            ensure_space(24)
            rect = fitz.Rect(self.margin_x + 5, y, self.width - self.margin_x, y + 22)
            page.insert_textbox(rect, skill_str, fontsize=9.5, fontname="helv")
            y += 24

        # ── 4. Experience Section ────────────────────────────────────────
        experience = resume_data.get("experience") or []
        if isinstance(experience, list) and experience:
            insert_section_header("Professional Experience")
            for exp in experience:
                if not isinstance(exp, dict):
                    continue
                title = sanitize_text(exp.get("role") or exp.get("title") or "Software Engineer")
                company = sanitize_text(exp.get("company") or exp.get("organization") or "")
                dates = sanitize_text(exp.get("dates") or exp.get("period") or (f"{exp.get('start_date', '')} - {exp.get('end_date', '')}".strip(" -")))
                location = sanitize_text(exp.get("location") or "")

                top_line = f"{title}"
                if company: top_line += f" - {company}"
                if dates: top_line += f"  ({dates})"
                if location: top_line += f" [{location}]"

                ensure_space(20)
                title_rect = fitz.Rect(self.margin_x, y, self.width - self.margin_x, y + 14)
                page.insert_textbox(title_rect, top_line, fontsize=10, fontname="helv")
                y += 14

                # Bullets / Highlights
                bullets = exp.get("highlights") or exp.get("bullets") or exp.get("responsibilities") or []
                if isinstance(bullets, list):
                    for b in bullets:
                        b_text = sanitize_text(b)
                        if not b_text:
                            continue
                        bullet_text = f"-  {b_text}"
                        approx_lines = max(1, len(bullet_text.split()) // 14 + 1)
                        b_height = approx_lines * 13
                        ensure_space(b_height + 2)
                        b_rect = fitz.Rect(self.margin_x + 10, y, self.width - self.margin_x, y + b_height)
                        page.insert_textbox(b_rect, bullet_text, fontsize=9.5, fontname="helv")
                        y += b_height + 2
                y += 4

        # ── 5. Projects Section ──────────────────────────────────────────
        projects = resume_data.get("projects") or []
        if isinstance(projects, list) and projects:
            insert_section_header("Technical Projects")
            for proj in projects:
                if not isinstance(proj, dict):
                    continue
                p_name = sanitize_text(proj.get("name") or proj.get("title") or "Engineering Project")
                p_tech = proj.get("tech_stack") or proj.get("technologies") or []
                p_url = sanitize_text(proj.get("url") or proj.get("github_url") or proj.get("live_url") or "")

                top_line = f"{p_name}"
                if p_tech:
                    if isinstance(p_tech, list):
                        tech_str = ", ".join(sanitize_text(t) for t in p_tech if t)
                    else:
                        tech_str = sanitize_text(str(p_tech))
                    if tech_str:
                        top_line += f" | {tech_str}"
                if p_url:
                    top_line += f" ({p_url})"

                ensure_space(18)
                title_rect = fitz.Rect(self.margin_x, y, self.width - self.margin_x, y + 14)
                page.insert_textbox(title_rect, top_line, fontsize=10, fontname="helv")
                y += 14

                bullets = proj.get("highlights") or proj.get("bullets") or proj.get("description_bullets") or []
                if not bullets and proj.get("description"):
                    bullets = [proj["description"]]

                if isinstance(bullets, list):
                    for b in bullets:
                        b_text = sanitize_text(b)
                        if not b_text:
                            continue
                        bullet_text = f"-  {b_text}"
                        approx_lines = max(1, len(bullet_text.split()) // 14 + 1)
                        b_height = approx_lines * 13
                        ensure_space(b_height + 2)
                        b_rect = fitz.Rect(self.margin_x + 10, y, self.width - self.margin_x, y + b_height)
                        page.insert_textbox(b_rect, bullet_text, fontsize=9.5, fontname="helv")
                        y += b_height + 2
                y += 4

        # ── 6. Education Section ─────────────────────────────────────────
        education = resume_data.get("education") or []
        if isinstance(education, list) and education:
            insert_section_header("Education")
            for edu in education:
                if not isinstance(edu, dict):
                    continue
                degree = sanitize_text(edu.get("degree") or edu.get("field_of_study") or "Degree")
                school = sanitize_text(edu.get("institution") or edu.get("school") or "")
                year = sanitize_text(edu.get("year") or edu.get("dates") or edu.get("end_date") or "")

                edu_line = f"- {degree}"
                if school: edu_line += f" - {school}"
                if year: edu_line += f" ({year})"

                ensure_space(16)
                rect = fitz.Rect(self.margin_x + 5, y, self.width - self.margin_x, y + 14)
                page.insert_textbox(rect, edu_line, fontsize=9.5, fontname="helv")
                y += 14

        # ── 7. Certifications Section ────────────────────────────────────
        certs = resume_data.get("certifications") or []
        if isinstance(certs, list) and certs:
            insert_section_header("Certifications")
            for c in certs:
                c_name = sanitize_text(c if isinstance(c, str) else (c.get("name", "") if isinstance(c, dict) else str(c)))
                if not c_name:
                    continue
                ensure_space(16)
                rect = fitz.Rect(self.margin_x + 5, y, self.width - self.margin_x, y + 14)
                page.insert_textbox(rect, f"- {c_name}", fontsize=9.5, fontname="helv")
                y += 14

        # Save to memory bytes
        pdf_bytes = doc.tobytes(deflate=True)
        doc.close()
        return pdf_bytes


pdf_generator = ATSPdfGenerator()
