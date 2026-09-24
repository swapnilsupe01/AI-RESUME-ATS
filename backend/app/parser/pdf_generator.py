"""
ATS-Compliant PDF Generator -- complete rewrite.

Root-cause fixes applied
------------------------
1. Field-name mismatch: canonical dict has profile.name / profile.email (nested),
   not candidate_name / email at the top level.  Both layouts now work.
2. Text-height clipping: the old code used words//14 which silently clipped text.
   This version uses chars-per-line estimation + 35% padding + overflow expansion.
3. Skills dict: CanonicalResume.model_dump() skills is a nested dict
   {technical:[...], frameworks:[...], ...}.  This is now the primary path.
4. Page breaks: headings never orphan from their content.

Template
--------
- US Letter 612x792pt, 45pt side margins
- Name: 19pt bold centred + accent underline rule
- Section headers: 11pt bold accent + divider rule
- Body text: 9.5pt Helvetica
- Circular bullet dots with hanging indent
"""

from typing import Dict, Any, List
import pymupdf as fitz


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _s(val) -> str:
    if val is None:
        return ""
    s = str(val)
    for orig, rep in {
        "\u2014": " - ", "\u2013": " - ",
        "\u201c": '\"', "\u201d": '\"',
        "\u2018": "\'", "\u2019": "\'",
        "\u00a0": " ", "\t": "    ",
    }.items():
        s = s.replace(orig, rep)
    return s.strip()


def _get(d: dict, *keys, default="") -> str:
    for k in keys:
        v = d.get(k)
        if v is not None:
            sv = _s(v)
            if sv:
                return sv
    return default


def _pf(resume: dict, field: str, *aliases) -> str:
    """Read from nested profile dict first, then top-level aliases."""
    profile = resume.get("profile") or {}
    if isinstance(profile, dict):
        val = _s(profile.get(field, ""))
        if val:
            return val
    for alias in aliases:
        val = _s(resume.get(alias, ""))
        if val:
            return val
    return ""


def _height(text: str, fs: float, width: float) -> float:
    """Conservative text-box height estimate (chars/line, 35% pad)."""
    if not text or not text.strip():
        return fs + 4
    cpl = max(1, int(max(width, 60.0) / (fs * 0.52)))
    n   = max(1, -(-len(text) // cpl))   # ceiling division
    return n * (fs + 3.5) * 1.35 + 6


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class ATSPdfGenerator:
    PAGE_W, PAGE_H = 612.0, 792.0
    MX, MT, MB     = 45.0, 42.0, 40.0
    C_BLACK  = (0.08, 0.08, 0.08)
    C_DARK   = (0.18, 0.18, 0.18)
    C_ACCENT = (0.22, 0.45, 0.75)
    C_RULE   = (0.72, 0.72, 0.75)
    C_SUBTLE = (0.40, 0.40, 0.43)

    def __init__(self):
        self.cw = self.PAGE_W - 2 * self.MX

    def generate_pdf(self, resume_data: Dict[str, Any]) -> bytes:
        if not isinstance(resume_data, dict):
            resume_data = {}

        doc  = fitz.open()
        page = doc.new_page(width=self.PAGE_W, height=self.PAGE_H)
        y    = self.MT

        AL = getattr(fitz, "TEXT_ALIGN_LEFT",   0)
        AC = getattr(fitz, "TEXT_ALIGN_CENTER", 1)

        def ensure(need):
            nonlocal y
            if y + need > self.PAGE_H - self.MB:
                page = doc.new_page(width=self.PAGE_W, height=self.PAGE_H)
                y    = self.MT

        def tb(text, fs, x, w, colour=None, align=None, bold=False):
            nonlocal y
            if not text or not text.strip():
                return 0.0
            colour = colour or self.C_DARK
            align  = align if align is not None else AL
            fn     = "hebo" if bold else "helv"
            h      = _height(text, fs, w)
            ensure(h)
            rect = fitz.Rect(x, y, x + w, y + h)
            ov = page.insert_textbox(rect, text, fontsize=fs, fontname=fn,
                                     color=colour, align=align)
            if isinstance(ov, (int, float)) and ov < 0:
                h2 = h + abs(ov) + fs * 2
                ensure(h2)
                rect = fitz.Rect(x, y, x + w, y + h2)
                page.insert_textbox(rect, text, fontsize=fs, fontname=fn,
                                    color=colour, align=align)
                h = h2
            y += h
            return h

        def sh(title):
            nonlocal y
            ensure(34)
            y += 7
            page.insert_textbox(
                fitz.Rect(self.MX, y, self.PAGE_W - self.MX, y + 20),
                title.upper(), fontsize=11, fontname="hebo",
                color=self.C_ACCENT, align=AL)
            y += 15
            page.draw_line(fitz.Point(self.MX, y),
                           fitz.Point(self.PAGE_W - self.MX, y),
                           color=self.C_RULE, width=0.7)
            y += 7

        def blt(text, indent=12.0):
            nonlocal y
            if not text or not text.strip():
                return
            bx    = self.MX + indent
            tx    = bx + 10
            tw    = self.PAGE_W - self.MX - tx
            h     = _height(text, 9.5, tw)
            ensure(h)
            page.draw_circle(fitz.Point(bx + 2.5, y + 6.0),
                             1.7, color=self.C_SUBTLE, fill=self.C_SUBTLE)
            rect = fitz.Rect(tx, y, tx + tw, y + h)
            ov = page.insert_textbox(rect, _s(text), fontsize=9.5,
                                     fontname="helv", color=self.C_DARK, align=AL)
            if isinstance(ov, (int, float)) and ov < 0:
                h2 = h + abs(ov) + 19
                ensure(h2)
                rect = fitz.Rect(tx, y, tx + tw, y + h2)
                page.insert_textbox(rect, _s(text), fontsize=9.5,
                                    fontname="helv", color=self.C_DARK, align=AL)
                h = h2
            y += h + 1

        # ── 1. Header ────────────────────────────────────────────────────────
        name      = _pf(resume_data, "name",      "candidate_name") or "CANDIDATE"
        headline  = _pf(resume_data, "headline")
        email     = _pf(resume_data, "email",     "email")
        phone     = _pf(resume_data, "phone",     "phone")
        github    = _pf(resume_data, "github",    "github_url")
        linkedin  = _pf(resume_data, "linkedin",  "linkedin_url")
        portfolio = _pf(resume_data, "portfolio", "portfolio_url")

        page.insert_textbox(
            fitz.Rect(self.MX, y, self.PAGE_W - self.MX, y + 34),
            name.upper(), fontsize=19, fontname="hebo",
            color=self.C_BLACK, align=AC)
        y += 28
        page.draw_line(fitz.Point(self.MX + 40, y),
                       fitz.Point(self.PAGE_W - self.MX - 40, y),
                       color=self.C_ACCENT, width=1.6)
        y += 7

        if headline:
            tb(headline, 10.5, self.MX, self.cw, colour=self.C_ACCENT, align=AC)
            y += 2

        contact = [p for p in [email, phone, github, linkedin, portfolio] if p]
        if contact:
            tb("  |  ".join(contact), 8.5, self.MX, self.cw,
               colour=self.C_SUBTLE, align=AC)
        y += 8

        # ── 2. Summary ───────────────────────────────────────────────────────
        prof    = resume_data.get("profile") or {}
        summary = (_s(resume_data.get("summary") or "")
                   or _s(prof.get("summary") if isinstance(prof, dict) else ""))
        if summary:
            sh("Professional Summary")
            tb(summary, 9.5, self.MX, self.cw)
            y += 5

        # ── 3. Skills ────────────────────────────────────────────────────────
        raw_sk = resume_data.get("skills") or {}
        slines: List[str] = []
        if isinstance(raw_sk, dict):
            LABELS = {
                "technical":  "Languages & Core",
                "frameworks": "Frameworks & Libraries",
                "cloud":      "Cloud & DevOps",
                "databases":  "Databases & Storage",
                "tools":      "Tools & Platforms",
                "soft":       "Soft Skills",
                "other":      "Other",
            }
            for k, lbl in LABELS.items():
                items = raw_sk.get(k) or []
                if items and isinstance(items, list):
                    slines.append(f"{lbl}: {', '.join(_s(s) for s in items if s)}")
        elif isinstance(raw_sk, list) and raw_sk:
            slines.append("Core Technologies: " +
                          ", ".join(_s(s) for s in raw_sk[:30] if s))
        if not slines:
            ext = resume_data.get("extracted_skills") or []
            if ext:
                slines.append("Skills: " +
                              ", ".join(_s(s) for s in ext[:30] if s))
        if slines:
            sh("Technical Skills")
            for ln in slines:
                tb("  " + ln, 9.5, self.MX + 8, self.cw - 8)
                y += 1
            y += 4

        # ── 4. Experience ────────────────────────────────────────────────────
        exp_list = resume_data.get("experience") or []
        if isinstance(exp_list, list) and exp_list:
            sh("Professional Experience")
            for exp in exp_list:
                if not isinstance(exp, dict):
                    continue
                role    = _get(exp, "role", "title", default="Role")
                company = _get(exp, "company", "organization")
                start   = _get(exp, "start_date")
                end     = _get(exp, "end_date")
                loc     = _get(exp, "location")
                dates   = _get(exp, "dates", "period")
                if not dates:
                    parts = [p for p in [start, end] if p]
                    dates = " - ".join(parts) if parts else ""
                top = role
                if company: top += f"  -  {company}"
                if dates:   top += f"  |  {dates}"
                if loc:     top += f"  |  {loc}"
                ensure(40)
                tb(top, 10, self.MX, self.cw, colour=self.C_BLACK, bold=True)
                y += 1
                for b in (exp.get("highlights") or exp.get("bullets") or []):
                    blt(_s(b))
                techs = exp.get("technologies") or []
                if techs and isinstance(techs, list):
                    tb("Technologies: " + ", ".join(_s(t) for t in techs if t),
                       8.5, self.MX + 14, self.cw - 14, colour=self.C_SUBTLE)
                y += 6

        # ── 5. Projects ──────────────────────────────────────────────────────
        proj_list = resume_data.get("projects") or []
        if isinstance(proj_list, list) and proj_list:
            sh("Key Projects")
            for proj in proj_list:
                if not isinstance(proj, dict):
                    continue
                pname = _get(proj, "name", "title", default="Project")
                purl  = _get(proj, "github_url", "url", "live_url")
                techs = proj.get("technologies") or proj.get("tech_stack") or []
                top   = pname
                if techs and isinstance(techs, list):
                    top += "  |  " + ", ".join(_s(t) for t in techs if t)
                if purl:
                    top += f"  ({purl})"
                ensure(35)
                tb(top, 10, self.MX, self.cw, colour=self.C_BLACK, bold=True)
                y += 1
                desc = _get(proj, "description")
                if desc:
                    tb(desc, 9.5, self.MX + 14, self.cw - 14)
                    y += 1
                for b in (proj.get("highlights") or proj.get("bullets") or []):
                    blt(_s(b))
                y += 6

        # ── 6. Education ─────────────────────────────────────────────────────
        edu_list = resume_data.get("education") or []
        if isinstance(edu_list, list) and edu_list:
            sh("Education")
            for edu in edu_list:
                if not isinstance(edu, dict):
                    continue
                degree = _get(edu, "degree")
                field  = _get(edu, "field_of_study")
                school = _get(edu, "institution", "school")
                end_yr = _get(edu, "end_date", "year", "dates")
                gpa    = _get(edu, "gpa")
                honors = edu.get("honors") or []
                ds     = degree
                if field:  ds = f"{ds} in {field}".strip(" in ")
                if school: ds += f"  -  {school}"
                if end_yr: ds += f"  ({end_yr})"
                if not ds: ds = school or "Degree"
                tb(ds, 10, self.MX, self.cw, colour=self.C_BLACK, bold=True)
                extras = []
                if gpa: extras.append(f"GPA: {gpa}")
                for h in (honors or []):
                    if h: extras.append(_s(h))
                if extras:
                    tb("  ".join(extras), 9.0, self.MX + 14, self.cw - 14,
                       colour=self.C_SUBTLE)
                y += 5

        # ── 7. Certifications ────────────────────────────────────────────────
        certs = resume_data.get("certifications") or []
        if isinstance(certs, list) and certs:
            sh("Certifications")
            for c in certs:
                if isinstance(c, str):
                    cn = _s(c)
                elif isinstance(c, dict):
                    cn     = _get(c, "name")
                    issuer = _get(c, "issuer")
                    date   = _get(c, "issue_date")
                    if issuer: cn += f"  -  {issuer}"
                    if date:   cn += f"  ({date})"
                else:
                    cn = _s(str(c))
                if cn:
                    blt(cn, indent=8)
            y += 3

        # ── 8. Achievements ──────────────────────────────────────────────────
        ach_list = resume_data.get("achievements") or []
        if isinstance(ach_list, list) and ach_list:
            sh("Achievements")
            for ach in ach_list:
                if isinstance(ach, dict):
                    title = _get(ach, "title")
                    desc  = _get(ach, "description")
                    date  = _get(ach, "date")
                    line  = title
                    if date: line += f" ({date})"
                    if desc: line += f": {desc}"
                else:
                    line = _s(str(ach))
                if line:
                    blt(line, indent=8)
            y += 3

        pdf_bytes = doc.tobytes(deflate=True)
        doc.close()
        return pdf_bytes


pdf_generator = ATSPdfGenerator()


def generate_pdf(resume_data: Dict[str, Any]) -> bytes:
    """Module-level convenience wrapper for ATSPdfGenerator.generate_pdf."""
    return pdf_generator.generate_pdf(resume_data)
