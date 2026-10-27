from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, HRFlowable

def _dates(d):
    s = d.get("start_date", "")
    e = "Present" if d.get("current") else d.get("end_date", "")
    return f"{s} – {e}".strip(" –") if (s or e) else ""

def _build(r, k):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=12*mm, bottomMargin=12*mm)
    body = ParagraphStyle("b", fontName="Helvetica", fontSize=9.5*k, leading=12*k)
    bold = ParagraphStyle("t", parent=body, fontName="Helvetica-Bold")
    head = ParagraphStyle("h", parent=body, fontName="Helvetica-Bold", fontSize=11*k, spaceBefore=6*k)
    name = ParagraphStyle("n", parent=body, fontName="Helvetica-Bold", fontSize=16*k, leading=19*k)
    bul = ParagraphStyle("bl", parent=body, leftIndent=10, bulletIndent=0)
    out = []
    P = lambda t, s=body: out.append(Paragraph(escape(t), s))
    def H(t):
        out.append(Paragraph(escape(t.upper()), head)); out.append(HRFlowable(width="100%", thickness=0.5))
    def B(items):
        for b in items:
            if b and b.strip(): out.append(Paragraph(escape(b.strip()), bul, bulletText="•"))
    p = r.get("profile") or {}
    P(p.get("name", ""), name)
    P(" | ".join(x for x in [p.get("email"), p.get("phone"), p.get("location"),
                             p.get("github"), p.get("linkedin"), p.get("portfolio")] if x))
    if r.get("summary"): H("Summary"); P(r["summary"])
    edu = r.get("education") or []
    if edu:
        H("Education")
        for e in edu:
            P(", ".join(x for x in [e.get("institution"), e.get("degree"), e.get("field_of_study")] if x), bold)
            extra = " | ".join(x for x in [_dates(e), ("GPA: " + e["gpa"]) if e.get("gpa") else ""] if x)
            if extra: P(extra)
            B(e.get("honors") or [])
    sk = r.get("skills") or {}
    rows = [(l, sk.get(key) or []) for l, key in [("Languages & Core","technical"),("Frameworks","frameworks"),
            ("Databases","databases"),("Cloud & DevOps","cloud"),("Tools","tools"),
            ("Security","cybersecurity"),("Other","other")]]
    if any(v for _, v in rows):
        H("Skills")
        for l, v in rows:
            if v: P(f"{l}: {', '.join(v)}")
    exp = r.get("experience") or []
    if exp:
        H("Experience")
        for x in exp:
            P(" – ".join(a for a in [x.get("role"), x.get("company")] if a), bold)
            meta = " | ".join(a for a in [_dates(x), x.get("location")] if a)
            if meta: P(meta)
            B(x.get("highlights") or [])
    prj = r.get("projects") or []
    if prj:
        H("Projects")
        for x in prj:
            P(x.get("name", ""), bold)
            tech = ", ".join(x.get("technologies") or [])
            if tech: P("Tech: " + tech)
            B(x.get("highlights") or x.get("description_bullets") or [])
    for key, title, fmt in [
        ("certifications", "Certifications", lambda c: f"{c.get('name','')} – {c.get('issuer','')}".strip(" –")),
        ("achievements", "Achievements", lambda a: a.get("title","") + (": " + a["description"] if a.get("description") else ""))]:
        items = r.get(key) or []
        if items: H(title); B([fmt(i) for i in items])
    for c in r.get("custom_sections") or []:
        if c.get("items"): H(c.get("title") or "Other"); B(c["items"])
    doc.build(out)
    return buf.getvalue(), doc.page

def build_ats_pdf(resume: dict, max_pages: int = 2) -> bytes:
    data = b""
    for k in (1.0, 0.93, 0.86, 0.8):
        data, pages = _build(resume, k)
        if pages <= max_pages: return data
    return data
