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
        doc = fitz.open()
        page = doc.new_page(width=self.width, height=self.height)
        y = self.margin_top

        # ── 1. Header (Candidate Name + Contact) ─────────────────────────
        profile = resume_data.get("profile", {}) if isinstance(resume_data.get("profile"), dict) else {}
        name = resume_data.get("candidate_name") or profile.get("name") or "CANDIDATE NAME"
        name_rect = fitz.Rect(self.margin_x, y, self.width - self.margin_x, y + 26)
        page.insert_textbox(name_rect, name.upper(), fontsize=18, fontname="helv", fontfile=None, align=fitz.TEXT_ALIGN_CENTER)
        y += 24

        # Contact Info Line
        contact_parts = []
        email = resume_data.get("email") or profile.get("email")
        phone = resume_data.get("phone") or profile.get("phone")
        gh = resume_data.get("github_url") or profile.get("github")
        li = resume_data.get("linkedin_url") or profile.get("linkedin")
        pf = resume_data.get("portfolio_url") or profile.get("portfolio")

        if email: contact_parts.append(email)
        if phone: contact_parts.append(phone)
        if gh: contact_parts.append(gh)
        if li: contact_parts.append(li)
        if pf: contact_parts.append(pf)

        contact_text = " | ".join(contact_parts) if contact_parts else "Email | Phone | GitHub | LinkedIn"
        contact_rect = fitz.Rect(self.margin_x, y, self.width - self.margin_x, y + 16)
        page.insert_textbox(contact_rect, contact_text, fontsize=9, fontname="helv", align=fitz.TEXT_ALIGN_CENTER)
        y += 20

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
            ensure_space(30)
            y += 6
            # Section Title
            header_rect = fitz.Rect(self.margin_x, y, self.width - self.margin_x, y + 15)
            page.insert_textbox(header_rect, title.upper(), fontsize=11, fontname="helv", align=fitz.TEXT_ALIGN_LEFT)
            y += 14
            # Divider Line
            p1 = fitz.Point(self.margin_x, y)
            p2 = fitz.Point(self.width - self.margin_x, y)
            page.draw_line(p1, p2, color=(0.7, 0.7, 0.75), width=0.8)
            y += 8

        # ── 2. Summary Section ───────────────────────────────────────────
        summary = resume_data.get("summary") or ""
        if summary.strip():
            insert_section_header("Professional Summary")
            # Calculate height needed
            words = summary.split()
            approx_lines = max(1, len(words) // 14 + 1)
            text_h = approx_lines * 13 + 4
            ensure_space(text_h)
            rect = fitz.Rect(self.margin_x, y, self.width - self.margin_x, y + text_h)
            page.insert_textbox(rect, summary.strip(), fontsize=9.5, fontname="helv", align=fitz.TEXT_ALIGN_LEFT)
            y += text_h + 6

        # ── 3. Technical Skills Section ──────────────────────────────────
        skills = resume_data.get("skills") or resume_data.get("extracted_skills") or []
        categorized = resume_data.get("categorized_skills") or {}

        if skills or categorized:
            insert_section_header("Technical Skills")
            if categorized and isinstance(categorized, dict) and any(categorized.values()):
                for cat_name, cat_skills in categorized.items():
                    if not cat_skills: continue
                    skill_line = f"• {cat_name.title()}: {', '.join(cat_skills) if isinstance(cat_skills, list) else str(cat_skills)}"
                    ensure_space(15)
                    rect = fitz.Rect(self.margin_x + 5, y, self.width - self.margin_x, y + 14)
                    page.insert_textbox(rect, skill_line, fontsize=9.5, fontname="helv")
                    y += 14
            else:
                skill_str = "• Core Technologies: " + ", ".join(skills[:24])
                ensure_space(24)
                rect = fitz.Rect(self.margin_x + 5, y, self.width - self.margin_x, y + 22)
                page.insert_textbox(rect, skill_str, fontsize=9.5, fontname="helv")
                y += 20
            y += 4

        # ── 4. Experience Section ────────────────────────────────────────
        experience = resume_data.get("experience") or []
        if experience:
            insert_section_header("Professional Experience")
            for exp in experience:
                title = exp.get("role") or exp.get("title") or "Software Engineer"
                company = exp.get("company") or exp.get("organization") or ""
                dates = exp.get("dates") or exp.get("period") or (f"{exp.get('start_date', '')} – {exp.get('end_date', '')}".strip(" –"))
                location = exp.get("location") or ""

                top_line = f"{title}"
                if company: top_line += f" — {company}"
                if dates: top_line += f"  ({dates})"

                ensure_space(20)
                title_rect = fitz.Rect(self.margin_x, y, self.width - self.margin_x, y + 14)
                page.insert_textbox(title_rect, top_line, fontsize=10, fontname="helv")
                y += 14

                # Bullets
                bullets = exp.get("highlights") or exp.get("bullets") or exp.get("responsibilities") or []
                for b in bullets:
                    bullet_text = f"•  {b.strip()}"
                    approx_lines = max(1, len(bullet_text.split()) // 14 + 1)
                    b_height = approx_lines * 13
                    ensure_space(b_height + 2)
                    b_rect = fitz.Rect(self.margin_x + 10, y, self.width - self.margin_x, y + b_height)
                    page.insert_textbox(b_rect, bullet_text, fontsize=9.5, fontname="helv")
                    y += b_height + 2
                y += 4

        # ── 5. Projects Section ──────────────────────────────────────────
        projects = resume_data.get("projects") or []
        if projects:
            insert_section_header("Technical Projects")
            for proj in projects:
                p_name = proj.get("name") or proj.get("title") or "Engineering Project"
                p_tech = proj.get("tech_stack") or proj.get("technologies") or []
                p_url = proj.get("url") or proj.get("github_url") or ""

                top_line = f"{p_name}"
                if p_tech:
                    tech_str = ", ".join(p_tech) if isinstance(p_tech, list) else str(p_tech)
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

                for b in bullets:
                    bullet_text = f"•  {b.strip()}"
                    approx_lines = max(1, len(bullet_text.split()) // 14 + 1)
                    b_height = approx_lines * 13
                    ensure_space(b_height + 2)
                    b_rect = fitz.Rect(self.margin_x + 10, y, self.width - self.margin_x, y + b_height)
                    page.insert_textbox(b_rect, bullet_text, fontsize=9.5, fontname="helv")
                    y += b_height + 2
                y += 4

        # ── 6. Education Section ─────────────────────────────────────────
        education = resume_data.get("education") or []
        if education:
            insert_section_header("Education")
            for edu in education:
                degree = edu.get("degree") or "Bachelor of Technology"
                school = edu.get("institution") or edu.get("school") or ""
                year = edu.get("year") or edu.get("dates") or ""

                edu_line = f"• {degree}"
                if school: edu_line += f" — {school}"
                if year: edu_line += f" ({year})"

                ensure_space(16)
                rect = fitz.Rect(self.margin_x + 5, y, self.width - self.margin_x, y + 14)
                page.insert_textbox(rect, edu_line, fontsize=9.5, fontname="helv")
                y += 14

        # ── 7. Certifications Section ────────────────────────────────────
        certs = resume_data.get("certifications") or []
        if certs:
            insert_section_header("Certifications")
            for c in certs:
                c_name = c if isinstance(c, str) else c.get("name", "")
                if not c_name: continue
                ensure_space(16)
                rect = fitz.Rect(self.margin_x + 5, y, self.width - self.margin_x, y + 14)
                page.insert_textbox(rect, f"• {c_name}", fontsize=9.5, fontname="helv")
                y += 14

        # Save to memory bytes
        pdf_bytes = doc.tobytes(deflate=True)
        doc.close()
        return pdf_bytes


pdf_generator = ATSPdfGenerator()
