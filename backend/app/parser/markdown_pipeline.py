"""
Markdown Pipeline for AI Resume Intelligence & Evidence Platform.
Provides bi-directional conversion:
  - Positional PDF blocks -> Structured Markdown (.md)
  - Markdown (.md) -> Canonical Resume JSON (CanonicalResume)
  - Canonical Resume JSON -> Clean Standardized Markdown (.md)
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from app.models.canonical_resume import (
    CanonicalResume, Profile, ExperienceItem, ProjectItem,
    EducationItem, CategorizedSkills, CertificationItem, AchievementItem,
    CustomSectionItem, generate_id
)
from app.utils.skills import extract_skills, SKILL_CATEGORIES, ALL_SKILLS, get_skill_category, normalize_skill
from app.parser.resume_parser import (
    extract_email, extract_phone, extract_github_urls,
    extract_linkedin_urls, extract_portfolio_urls,
    SECTION_HEADERS as _BASE_SECTION_HEADERS
)

# Extra heading wordings seen in real resumes. Merged with the parser's own list
# so variants like "Professional Experience" / "Academic Projects" are recognised
# as section breaks instead of being swallowed by the previous section.
_EXTRA_SECTION_HEADERS = {
    "experience": [
        "experience", "work experience", "professional experience", "work history",
        "employment history", "employment", "internship", "internships",
        "internship experience", "experience & internships", "experience and internships",
        "industrial experience", "relevant experience",
    ],
    "projects": [
        "projects", "project", "key projects", "personal projects", "academic projects",
        "technical projects", "major projects", "selected projects", "side projects",
        "projects & research", "projects and research", "project experience",
    ],
}


def _merge_section_headers(base, extra):
    merged = {k: list(v) for k, v in dict(base).items()}
    for key, words in extra.items():
        cur = merged.setdefault(key, [])
        for w in words:
            if w not in cur:
                cur.append(w)
    return merged


SECTION_HEADERS = _merge_section_headers(_BASE_SECTION_HEADERS, _EXTRA_SECTION_HEADERS)


def categorize_skill(skill: str) -> str:
    """Categorize a skill into technical, frameworks, tools, databases, cloud, or other."""
    return get_skill_category(skill)


_EDU_DEG_KW = (
    r'\b(bachelor|master|b\.?tech|m\.?tech|b\.?e\.?|m\.?e\.?|b\.?s\.?|m\.?s\.?|b\.?sc|m\.?sc|'
    r'bca|mca|ph\.?d|doctorate|diploma|associate|higher secondary|secondary school|'
    r'hsc|ssc|bba|mba|b\.?com|m\.?com|b\.?a|m\.?a|degree)\b'
)
_EDU_INST_KW = (
    r'\b(university|institute|college|school|academy|vidyalaya|polytechnic|campus|'
    r'iit|nit|iiit|bits)\b'
)


def parse_education_entry_line(line: str) -> Dict[str, str]:
    """
    Parse golden / ATS education lines into structured fields.

    Supported forms:
      Vidyalankar Institute of Technology, Mumbai — B.Tech Computer Engineering | 8.5 CGPA | 2024–2027
      Bharati Vidyapeeth Institute of Technology, Kharghar — Diploma Computer Technology | 83.83% | 2022–2024
      HSC – 46.31%
      SSC – 70.55%
      ### B.Tech in Computer Engineering — Vidyalankar Institute of Technology (2024 – 2027)
    """
    raw = (line or "").strip()
    raw = re.sub(r'^###\s*', '', raw).strip()
    out: Dict[str, str] = {
        "institution": "",
        "degree": "",
        "field_of_study": "",
        "start_date": "",
        "end_date": "",
        "gpa": "",
    }
    if not raw:
        return out

    # Parenthetical dates: (2024 – 2027) / (2024-Present)
    date_paren = re.search(
        r'\(([^)]*(?:\d{4}|present|current|ongoing|expected)[^)]*)\)',
        raw, re.IGNORECASE,
    )
    if date_paren:
        start, end = _split_date_range(date_paren.group(1))
        out["start_date"], out["end_date"] = start, end
        raw = raw.replace(date_paren.group(0), " ").strip()

    # Pipe-separated trailing meta: Degree-or-School | 8.5 CGPA | 2024–2027
    pipe_parts = [p.strip(" -–—|") for p in re.split(r'\s*\|\s*', raw) if p.strip()]
    meta_parts: List[str] = []
    if len(pipe_parts) >= 2:
        raw = pipe_parts[0]
        meta_parts = pipe_parts[1:]
    for meta in meta_parts:
        gpa_val = _extract_gpa_token(meta)
        if gpa_val and not out["gpa"]:
            out["gpa"] = gpa_val
            continue
        if re.search(r'\d{4}', meta):
            start, end = _split_date_range(meta)
            if start and not out["start_date"]:
                out["start_date"] = start
            if end and not out["end_date"]:
                out["end_date"] = end
            continue
        # Unknown meta — keep attached to raw if short
        if not out["gpa"] and re.search(r'\d', meta):
            out["gpa"] = meta

    # Em-dash / en-dash / " - " split between school and degree (or HSC – 46.31%)
    parts = [
        p.strip()
        for p in re.split(r'\s*(?:—|–)\s*|(?<=\w)\s+-\s+(?=\w)', raw)
        if p.strip()
    ]
    if len(parts) >= 2:
        part_a, part_b = parts[0], parts[1]
        # Board exam: HSC – 46.31%
        gpa_b = _extract_gpa_token(part_b)
        if gpa_b and re.search(r'\b(hsc|ssc|cbse|icse|xii|x)\b', part_a, re.I):
            out["institution"] = part_a
            out["degree"] = part_a.upper() if len(part_a) <= 4 else part_a
            out["gpa"] = out["gpa"] or gpa_b
        elif re.search(_EDU_DEG_KW, part_b, re.I) and not re.search(_EDU_DEG_KW, part_a, re.I):
            out["institution"], deg_cand = part_a, part_b
            _fill_degree_fields(out, deg_cand)
        elif re.search(_EDU_INST_KW, part_a, re.I) and not re.search(_EDU_INST_KW, part_b, re.I):
            out["institution"], deg_cand = part_a, part_b
            _fill_degree_fields(out, deg_cand)
        elif re.search(_EDU_DEG_KW, part_a, re.I):
            _fill_degree_fields(out, part_a)
            out["institution"] = part_b
        else:
            out["institution"], deg_cand = part_a, part_b
            _fill_degree_fields(out, deg_cand)
    else:
        if re.search(_EDU_DEG_KW, raw, re.I) and not re.search(_EDU_INST_KW, raw, re.I):
            _fill_degree_fields(out, raw)
        else:
            out["institution"] = raw

    return out


def _fill_degree_fields(out: Dict[str, str], deg_cand: str) -> None:
    deg_cand = deg_cand.strip()
    if not deg_cand:
        return
    if re.search(r'\s+in\s+', deg_cand, re.I):
        deg_split = re.split(r'\s+in\s+', deg_cand, maxsplit=1, flags=re.I)
        out["degree"] = deg_split[0].strip()
        out["field_of_study"] = deg_split[1].strip() if len(deg_split) > 1 else ""
    else:
        # "B.Tech Computer Engineering" → degree + field
        m = re.match(
            r"^((?:Bachelor(?:'s)?|Master(?:'s)?)\s+of\s+\w+)\s+(.+)$", deg_cand, re.I
        ) or re.match(
            r'^((?:B\.?Tech|M\.?Tech|B\.?E\.?|M\.?E\.?|B\.?S\.?|M\.?S\.?|B\.?Sc|M\.?Sc|'
            r'Diploma|Bachelor(?:\'s)?|Master(?:\'s)?|Ph\.?D\.?)[^,]*?)\s+(.+)$',
            deg_cand, re.I,
        )
        if m and len(m.group(2).split()) <= 6:
            out["degree"] = m.group(1).strip()
            out["field_of_study"] = m.group(2).strip()
        else:
            out["degree"] = deg_cand


def _extract_gpa_token(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    m = re.search(
        r'(?:cgpa|gpa|percentage|score|grade)\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?\s*%?(?:\s*(?:out of|/)\s*[0-9.]+)?)',
        t, re.I,
    )
    if m:
        val = m.group(1).strip()
        if "cgpa" in t.lower() and "cgpa" not in val.lower() and "%" not in val:
            return f"{val} CGPA"
        if "gpa" in t.lower() and "gpa" not in val.lower() and "%" not in val and "cgpa" not in t.lower():
            return f"{val} GPA"
        return val
    m2 = re.match(r'^([0-9]+(?:\.[0-9]+)?\s*%)(?:\s*cgpa|\s*gpa)?$', t, re.I)
    if m2:
        return m2.group(1).replace(" ", "")
    m3 = re.match(r'^([0-9]+(?:\.[0-9]+)?)\s*(cgpa|gpa)$', t, re.I)
    if m3:
        return f"{m3.group(1)} {m3.group(2).upper()}"
    m4 = re.match(r'^([0-9]+(?:\.[0-9]+)?)$', t)
    if m4:
        num = float(m4.group(1))
        if num <= 10:
            return f"{m4.group(1)} CGPA"
        if num <= 100:
            return f"{m4.group(1)}%"
    return ""


def _split_date_range(text: str) -> Tuple[str, str]:
    clean = re.sub(r'^(?:expected|batch|class of|duration|period|dates?):\s*', '', text.strip(), flags=re.I)
    dates = [d.strip() for d in re.split(r'[-–—\ufffd/|]+|\bto\b', clean, flags=re.I) if d.strip()]
    start = dates[0] if dates else ""
    end = dates[1] if len(dates) > 1 else ""
    if start.lower() in ("present", "current", "ongoing") and not end:
        return "", "Present"
    if end and any(k in end.lower() for k in ("present", "ongoing", "current")):
        end = "Present"
    return start, end


_LEGAL_SUFFIX_RE = re.compile(
    r'\b(pvt\.?|private|ltd\.?|limited|llp|llc|inc\.?|corp\.?|corporation|gmbh)\b', re.IGNORECASE
)
_COMPANY_WORD_RE = re.compile(
    r'\b(technologies|technology|solutions?|systems|labs|softwares?|infotech|consultancy|'
    r'consulting|services|enterprises|industries|studio|studios)\b', re.IGNORECASE
)
_WORK_SIGNAL_RE = re.compile(
    r'\b(team|client|clients|intern|internship|stakeholder|stakeholders|production|'
    r'deployment|deployed|collaborat\w*|saas|compliance|company|employer|organization)\b', re.IGNORECASE
)


def _attach_continuation(item: Dict[str, Any], text: str) -> bool:
    """
    A wrapped bullet can reach the parser as a separate line that starts in lower case
    ("design, development, testing ..."). Glue it to the most recent highlight that was
    cut off mid-sentence (does not end with . ! ?) instead of making a new item.
    """
    hl = item.get("highlights") if item else None
    if not hl or not text or not text[0].islower():
        return False
    for i in range(len(hl) - 1, -1, -1):
        if not hl[i].rstrip().endswith((".", "!", "?")):
            hl[i] = f"{hl[i].rstrip()} {text.strip()}"
            return True
    return False


_SIM_STOP = frozenset(
    "a an the and or of to in on for with by as at from into using utilizing leveraging "
    "enabling ensuring through across between up its their this that is are was were be "
    "been being implemented developed designed built added".split()
)


def _content_tokens(text: str) -> set:
    out = set()
    for w in re.findall(r"[a-z0-9][a-z0-9\-\./+#]*", (text or "").lower()):
        w = w.strip("./-")
        if w in _SIM_STOP or len(w) < 2:
            continue
        if len(w) > 4 and w.endswith("s"):
            w = w[:-1]
        out.add(w)
    return out


def _similar_text(a: str, b: str) -> bool:
    """
    True if `b` is a re-worded copy of `a` (same facts, different wording).
    Either close character similarity, or most content words of the shorter bullet
    appear in the other one. Measured on real data: re-worded bullets score
    0.60-1.00, unrelated bullets <= 0.30.
    """
    import difflib
    a, b = (a or "").lower().strip(), (b or "").lower().strip()
    if not a or not b:
        return False
    if difflib.SequenceMatcher(None, a, b).ratio() >= 0.6:
        return True
    ta, tb = _content_tokens(a), _content_tokens(b)
    if min(len(ta), len(tb)) < 4:
        return False
    return len(ta & tb) / min(len(ta), len(tb)) >= 0.5


def _is_work_entry(name: str, texts: List[str]) -> bool:
    """True if a 'project' is really a job: company-style name (+ work-like content)."""
    name = (name or "").strip()
    if not name:
        return False
    if _LEGAL_SUFFIX_RE.search(name):
        return True
    if _COMPANY_WORD_RE.search(name):
        return any(_WORK_SIGNAL_RE.search(t or "") for t in texts)
    return False


_ROLE_WORDS = (
    "lead|developer|engineer|intern|manager|analyst|designer|architect|administrator|"
    "consultant|head|owner|member|coordinator|associate|tester|trainee|executive|officer"
)
_ROLE_FROM_TEXT_RE = re.compile(
    r"\bas\s+(?:(?:a|an|the)\s+)?((?:[A-Z][A-Za-z&/+.-]*)(?:\s+(?:&\s+)?[A-Z][A-Za-z&/+.-]*){0,4})"
)
_EDU_HEADINGS = {
    "education", "academic background", "academics", "academic qualification",
    "academic qualifications", "educational qualification", "educational qualifications",
    "qualification", "qualifications",
}
_PLACEHOLDER_TITLES = {
    "experience", "work experience", "professional experience", "work history",
    "employment history", "projects", "key projects", "project",
}
_INLINE_LABEL_RE = re.compile(
    r'^(?:#+\s*)?(CERTIFICATIONS?|HOBBIES|INTERESTS|ACHIEVEMENTS?|AWARDS)\s*:', re.IGNORECASE
)


def _split_inline_bullets(text: str) -> List[str]:
    """'A * B * C' (bullets flattened into one line) -> ['A', 'B', 'C']."""
    t = (text or "").strip()
    if not t:
        return []
    t = re.sub(r'^[•\-*▪◦]\s+', '', t)
    return [p.strip() for p in re.split(r'\s+[*•▪◦]\s+', t) if p.strip()]


def _infer_role(highlights: List[str]) -> str:
    """Pick a job title out of wording like '... project as Team Lead, ...'."""
    for h in highlights[:3]:
        for m in _ROLE_FROM_TEXT_RE.finditer(h):
            cand = m.group(1).strip(" .,-")
            if re.search(rf"\b({_ROLE_WORDS})\b", cand, re.IGNORECASE):
                return cand
    return ""


def _fix_start_year(start: str, end: str) -> str:
    """'February' + 'April 2026' -> 'February 2026'."""
    if start and end and not re.search(r'\d{4}', start):
        m = re.search(r'\d{4}', end)
        if m:
            return f"{start} {m.group(0)}"
    return start


def _clean_head(line: str) -> str:
    return re.sub(r'^[#\s*]+', '', line.strip()).rstrip(':* ').strip().lower()


def _normalize_education_lines(block: List[str]) -> List[str]:
    """
    Turn raw education lines such as
        Vidyalankar Institute of Technology, Mumbai CGPA: 8.5 | | 2024-2027
        Pursuing B.Tech in Computer Engineering
        HSC (Maharashtra State Board), Mulund 46.31%
        Completed Higher Secondary School Certificate
    into golden lines:
        ### Vidyalankar Institute of Technology, Mumbai — B.Tech Computer Engineering | 8.5 CGPA | 2024–2027
        ### HSC – 46.31%
    Lines that are already golden (contain an em dash) pass through unchanged.
    """
    entries: List[Dict[str, Any]] = []
    for raw in block:
        s = raw.strip()
        if not s:
            continue
        s = re.sub(r'^(?:#{1,6}\s*|[-*•]\s+)', '', s).strip()
        if not s:
            continue
        if '—' in s:
            entries.append({"kind": "raw", "text": s})
            continue

        board = re.match(r'^(hsc|ssc|10th|12th)\b', s, re.IGNORECASE)
        if board:
            pct = re.search(r'(\d{1,3}(?:\.\d+)?)\s*%', s)
            if pct:
                label = board.group(1)
                label = label.upper() if len(label) <= 3 else label
                entries.append({"kind": "board", "label": label, "pct": pct.group(1)})
                continue

        comp = re.match(
            r'^(completed|pursuing|persuing|pursued|studying|currently pursuing|currently studying)\s+(.*)$',
            s, re.IGNORECASE,
        )
        if comp:
            verb, rest = comp.group(1).lower(), comp.group(2).strip()
            last = entries[-1] if entries else None
            if verb == "completed" and (last is None or last["kind"] == "board"
                                        or re.search(r'certificate', rest, re.IGNORECASE)):
                continue  # filler such as "Completed Secondary School Certificate (SSC)"
            if last and last["kind"] == "school" and not last["degree"]:
                last["degree"] = rest
                continue
            entries.append({"kind": "raw", "text": s})
            continue

        if re.search(_EDU_INST_KW, s, re.IGNORECASE):
            parts = [p.strip() for p in s.split('|') if p.strip()]
            head, meta = parts[0], parts[1:]
            gpa, dates = "", ""
            m = re.search(r'\b(?:cgpa|gpa)\s*[:\-]?\s*(\d+(?:\.\d+)?)', head, re.IGNORECASE)
            if m:
                gpa = f"{m.group(1)} CGPA"
                head = head.replace(m.group(0), ' ')
            else:
                m = re.search(r'(\d{1,3}(?:\.\d+)?)\s*%', head)
                if m:
                    gpa = f"{m.group(1)}%"
                    head = head.replace(m.group(0), ' ')
            m = re.search(r'(\d{4})\s*[-–—]\s*(\d{4}|present)', head, re.IGNORECASE)
            if m:
                dates = f"{m.group(1)}–{m.group(2)}"
                head = head.replace(m.group(0), ' ')
            for mt in meta:
                if re.search(r'\d{4}', mt) and not dates:
                    dates = re.sub(r'\s*[-–—]\s*', '–', mt)
                elif not gpa:
                    gpa = _extract_gpa_token(mt)
            head = re.sub(r'\s+', ' ', head).strip(' ,-–—|')
            entries.append({"kind": "school", "inst": head, "degree": "", "gpa": gpa, "dates": dates})
            continue

        if re.search(_EDU_DEG_KW, s, re.IGNORECASE):
            last = entries[-1] if entries else None
            if last and last["kind"] == "school" and not last["degree"]:
                last["degree"] = s
                continue

        entries.append({"kind": "raw", "text": s})

    out: List[str] = []
    for e in entries:
        if e["kind"] == "raw":
            out.append(e["text"])
        elif e["kind"] == "board":
            out.append(f"### {e['label']} – {e['pct']}%")
        else:
            deg = re.sub(r'\s+in\s+', ' ', e["degree"], count=1, flags=re.IGNORECASE).strip()
            head = f"{e['inst']} — {deg}" if deg else e["inst"]
            meta = [x for x in (e["gpa"], e["dates"]) if x]
            out.append("### " + head + (" | " + " | ".join(meta) if meta else ""))
    return out


def _is_section_break(line: str, all_heads: set) -> bool:
    """
    True if `line` starts a new section, so the Education block must stop here.
    Handles exact keywords, '## Any Heading', and plain-text PDF headings such as
    'Professional Experience' that are not exact keyword matches.
    """
    s = line.strip()
    if not s:
        return False
    head = _clean_head(line)
    if head in all_heads or _INLINE_LABEL_RE.match(s):
        return True
    if s.startswith("## "):
        return True
    if s.startswith(("#", "-", "*", "•", "–", "—")) or len(s.split()) > 4:
        return False
    if s.endswith((".", ";", ",")) or re.search(r"\d", s):
        return False
    return any(kw in head for kw in all_heads if len(kw) > 4)


def _normalize_markdown(text: str) -> str:
    """Rewrite the Education block into golden one-line entries before parsing."""
    lines = text.splitlines()
    all_heads = {k for kws in SECTION_HEADERS.values() for k in kws}
    out: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        if _clean_head(line) in _EDU_HEADINGS and len(line.split()) <= 4:
            j, block = i + 1, []
            while j < len(lines):
                nxt = lines[j]
                if _is_section_break(nxt, all_heads):
                    break
                block.append(nxt)
                j += 1
            out.extend(_normalize_education_lines(block))
            i = j
            continue
        i += 1
    return "\n".join(out)


def build_categorized_skills(skills_list: List[str]) -> CategorizedSkills:
    """Group a flat list of skills into CategorizedSkills."""
    cat = CategorizedSkills()
    for s in skills_list:
        clean_s = s.strip()
        if not clean_s:
            continue
        group = categorize_skill(clean_s)
        target = getattr(cat, group, cat.other)
        formatted = clean_s if (len(clean_s) <= 4 and clean_s.isupper()) else clean_s
        if formatted not in target and formatted.lower() not in [t.lower() for t in target]:
            target.append(formatted)
    return cat


def canonical_to_markdown(resume: CanonicalResume) -> str:
    """
    Format a CanonicalResume object into human-readable, ATS-safe GitHub Flavored Markdown.
    """
    lines: List[str] = []

    # 1. Header & Profile
    name = resume.profile.name.strip() or "Candidate"
    lines.append(f"# {name}")

    if resume.profile.headline.strip():
        lines.append(f"**{resume.profile.headline.strip()}**")

    contact_parts: List[str] = []
    if resume.profile.email.strip():
        contact_parts.append(f"Email: {resume.profile.email.strip()}")
    if resume.profile.phone.strip():
        contact_parts.append(f"Phone: {resume.profile.phone.strip()}")
    if resume.profile.location.strip():
        contact_parts.append(f"Location: {resume.profile.location.strip()}")

    if contact_parts:
        lines.append(" | ".join(contact_parts))

    link_parts: List[str] = []
    if resume.profile.github.strip():
        link_parts.append(f"[GitHub]({resume.profile.github.strip()})")
    if resume.profile.linkedin.strip():
        link_parts.append(f"[LinkedIn]({resume.profile.linkedin.strip()})")
    if resume.profile.portfolio.strip():
        link_parts.append(f"[Portfolio]({resume.profile.portfolio.strip()})")

    if link_parts:
        lines.append(" | ".join(link_parts))

    lines.append("")

    # 2. Career Objective / Professional Summary
    if resume.summary.strip():
        lines.append("## Professional Summary")
        lines.append(resume.summary.strip())
        lines.append("")

    # 3. Education (golden inline form: School — Degree | GPA | years)
    if resume.education:
        lines.append("## Education")
        for edu in resume.education:
            degree = edu.degree.strip()
            field = edu.field_of_study.strip()
            if degree and field and field.lower() not in degree.lower():
                joiner = " " if (len(degree.split()) <= 2 and " of " not in degree.lower()) else " in "
                degree_str = f"{degree}{joiner}{field}"
            else:
                degree_str = degree or field or ""
            inst = edu.institution.strip()
            if not inst and not degree_str:
                continue

            date_bits = []
            if edu.start_date and edu.end_date:
                date_bits.append(f"{edu.start_date}–{edu.end_date}")
            elif edu.start_date and getattr(edu, "current", False):
                date_bits.append(f"{edu.start_date}–Present")
            elif edu.start_date:
                date_bits.append(edu.start_date)
            elif edu.end_date:
                date_bits.append(edu.end_date)

            # Prefer golden single-line: School — Degree | GPA | years
            if inst and degree_str and inst.lower() == degree_str.lower():
                # Board exams: "HSC – 46.31%"
                line = f"{inst} – {edu.gpa.strip()}" if edu.gpa else inst
                if date_bits:
                    line += f" | {date_bits[0]}"
            else:
                head = f"{inst} — {degree_str}" if (inst and degree_str) else (inst or degree_str)
                meta = []
                if edu.gpa:
                    meta.append(edu.gpa.strip())
                if date_bits:
                    meta.append(date_bits[0])
                line = head if not meta else f"{head} | {' | '.join(meta)}"
            lines.append(f"### {line}")
            if edu.honors:
                lines.append(f"*Honors: {', '.join(edu.honors)}*")
            lines.append("")

    # 4. Technical and Relevant Skills
    skills = resume.skills
    has_skills = any([
        skills.technical, skills.frameworks, skills.cloud,
        skills.databases, skills.tools, skills.cybersecurity,
        skills.soft, skills.other
    ])
    if has_skills:
        lines.append("## Technical Skills")
        if skills.technical:
            lines.append(f"- **Languages:** {', '.join(skills.technical)}")
        if skills.frameworks:
            lines.append(f"- **Frameworks & Libraries:** {', '.join(skills.frameworks)}")
        if skills.cloud:
            lines.append(f"- **Cloud & DevOps:** {', '.join(skills.cloud)}")
        if skills.databases:
            lines.append(f"- **Databases:** {', '.join(skills.databases)}")
        if skills.tools:
            lines.append(f"- **Tools:** {', '.join(skills.tools)}")
        if skills.cybersecurity:
            lines.append(f"- **Cybersecurity:** {', '.join(skills.cybersecurity)}")
        if skills.soft:
            lines.append(f"- **Soft Skills:** {', '.join(skills.soft)}")
        if skills.other:
            lines.append(f"- **Other:** {', '.join(skills.other)}")
        lines.append("")

    # 5. Key Projects (Priority for Freshers)
    if resume.projects:
        lines.append("## Key Projects")
        for proj in resume.projects:
            pname = proj.name.strip()
            psub = (proj.subtitle or "").strip()
            # Fall back: use description as subtitle only when it is a single short line
            if not psub and proj.description and len(proj.description.splitlines()) == 1 and len(proj.description) < 120:
                psub = proj.description.strip().lstrip("*").rstrip("*").strip()

            # If name already carries "Name — Subtitle", split it apart
            if not psub and any(sep in pname for sep in (" — ", " – ")):
                parts = re.split(r'\s*(?:—|–)\s*', pname, maxsplit=1)
                if len(parts) >= 2:
                    pname = parts[0].strip()
                    psub = parts[1].strip()
            elif psub and psub.lower() in pname.lower():
                # subtitle is already embedded in name — strip it so we don't duplicate
                pname = re.sub(re.escape(psub), "", pname, flags=re.IGNORECASE).rstrip(" —-– ").strip()

            title_part = f"{pname} — {psub}" if psub else pname

            # Technologies: separate italic line (never inline, never repeated as subtitle)
            techs = [t.strip() for t in (proj.technologies or [])
                     if t.strip() and t.strip().lower() != psub.lower()]

            link_tags = []
            if proj.github_url:
                link_tags.append(f"[Code]({proj.github_url})")
            if proj.live_url:
                link_tags.append(f"[Live Demo]({proj.live_url})")
            link_str = f" ({' | '.join(link_tags)})" if link_tags else ""

            # Heading: ### **Name — Subtitle** (links if any)
            lines.append(f"### **{title_part}**{link_str}")

            # Italic technology stack line (only when technologies exist)
            if techs:
                lines.append(f"*{', '.join(techs)}*")

            # Description body only when it is distinct from the subtitle AND longer than a tagline
            if proj.description:
                desc_clean = proj.description.strip().lstrip("*").rstrip("*").strip()
                if desc_clean and desc_clean.lower() != psub.lower() and desc_clean.lower() != pname.lower() and len(desc_clean) > 120:
                    lines.append(f"{desc_clean}")

            bullets = proj.description_bullets or proj.highlights
            for hl in bullets:
                clean_hl = hl.strip().lstrip("•-* ")
                if clean_hl:
                    lines.append(f"- {clean_hl}")
            lines.append("")


    # 6. Professional Experience & Internships (if applicable)
    if resume.experience:
        lines.append("## Work Experience")
        for exp in resume.experience:
            role = exp.role.strip()
            company = exp.company.strip()
            date_str = " – ".join(d.strip() for d in (exp.start_date, exp.end_date) if d and d.strip())
            if role and company:
                title = f"{role} — {company}"
            else:
                title = role or company
            if title:
                lines.append(f"### {title}" + (f" | {date_str}" if date_str else ""))
            # (an untitled item is written as bare bullets - never a fake "Experience" title)
            if exp.location.strip():
                lines.append(f"*{exp.location.strip()}*")
            for hl in exp.highlights:
                clean_hl = hl.strip().lstrip("•-* ")
                if clean_hl:
                    lines.append(f"- {clean_hl}")
            if exp.technologies:
                lines.append(f"*Technologies: {', '.join(exp.technologies)}*")
            lines.append("")

    # 7. Certifications
    if resume.certifications:
        lines.append("## Certifications")
        for cert in resume.certifications:
            issuer_str = f" — {cert.issuer}" if cert.issuer else ""
            date_str = f" ({cert.issue_date})" if cert.issue_date else ""
            link_str = f" [Credential]({cert.credential_url})" if cert.credential_url else ""
            lines.append(f"- **{cert.name}**{issuer_str}{date_str}{link_str}")
        lines.append("")

    # 8. Achievements & Activities
    if resume.achievements:
        lines.append("## Achievements & Activities")
        for ach in resume.achievements:
            date_str = f" ({ach.date})" if ach.date else ""
            desc_str = f": {ach.description}" if ach.description else ""
            lines.append(f"- **{ach.title}**{date_str}{desc_str}")
        lines.append("")

    # 9. Custom Sections / Leadership & Volunteering / Hobbies
    for cs in resume.custom_sections:
        if cs.title.strip() and cs.items:
            lines.append(f"## {cs.title.strip()}")
            for item in cs.items:
                lines.append(f"- {item.strip().lstrip('•-* ')}")
            lines.append("")

    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Bullet-level routing helpers
# These detect bullets that look like certifications or separate internship
# entries mixed into an experience section, and route them to their own
# canonical fields instead of dumping them into job highlights.
# ---------------------------------------------------------------------------

_CERT_BULLET_RE = re.compile(
    r"""(?xi)
    \b(
        course | courses | certification | certifications |
        certificate | certified | training | workshop | bootcamp |
        program | programme | nanodegree | specialization | mooc
    )\b
    """
)

_KNOWN_CERT_ISSUERS = {
    "nptel", "cdac", "c-dac", "aws", "amazon", "google", "coursera", "udemy",
    "microsoft", "oracle", "cisco", "meta", "ibm", "aicte", "skillsbuild",
    "csrbox", "infosys", "tcs", "nasscom", "simplilearn", "edx", "linkedin learning",
    "jetbrains", "hackerrank", "codecademy", "pluralsight", "alison",
}


def _is_cert_bullet(bullet: str) -> bool:
    """
    Return True if an experience-section bullet is actually a certification
    or training course entry that should go to resume.certifications.

    Patterns it catches:
      - "Cloud Computing Course - CDAC; Cloud Computing Certification Course (6 months)"
      - "Applied AI Internship - CSRBOX Foundation, AICTE, IBM SkillsBuild"
      - "Google Data Analytics Certification – Coursera"
    """
    b = (bullet or "").strip()
    b_lower = b.lower()

    # Must contain a certification-related keyword
    if not _CERT_BULLET_RE.search(b_lower):
        # Or reference a well-known issuer by name
        if not any(iss in b_lower for iss in _KNOWN_CERT_ISSUERS):
            return False

    # Exclude lines that are clearly work actions (start with an action verb)
    action_verb_re = re.compile(
        r"^(?:developed|designed|built|implemented|engineered|deployed|led|managed|"
        r"spearheaded|created|maintained|tested|debugged|collaborated|analyzed|"
        r"automated|optimized|integrated|conducted|coordinated|delivered)\b",
        re.IGNORECASE,
    )
    if action_verb_re.match(b):
        return False

    # Exclude lines that look like a pure work-task sentence (long, no issuer/dash pattern)
    # A cert bullet tends to be short and noun-phrase-like, not a full sentence
    # with more than one finite clause.
    if len(b.split()) > 20 and not any(sep in b for sep in ("-", "–", "—", ";", "|")):
        return False

    return True


def _parse_cert_from_bullet(bullet: str) -> dict:
    """
    Parse a certification bullet text into {name, issuer, issue_date} dict.
    Handles:
      "Cloud Computing Course - CDAC; Cloud Computing Certification Course (6 months)"
      "Applied AI Internship - CSRBOX Foundation, AICTE, IBM SkillsBuild"
      "Google Data Analytics Certification – Coursera (2024)"
    """
    b = bullet.strip()
    # Extract trailing date in parens
    date_m = re.search(r"\(([^)]*(?:\d{4}|\d+\s*months?)[^)]*)\)", b, re.IGNORECASE)
    issue_date = date_m.group(1).strip() if date_m else ""
    if date_m:
        b = b[: date_m.start()].strip().rstrip(";,")

    # Split on first separator: " - ", " – ", " — ", ";", " | "
    parts = [p.strip() for p in re.split(r"\s*(?:—|–|-|;|\|)\s*", b, maxsplit=1) if p.strip()]
    if len(parts) >= 2:
        name, issuer = parts[0], parts[1]
    else:
        name, issuer = parts[0] if parts else b, ""

    return {"name": name.strip(), "issuer": issuer.strip(), "issue_date": issue_date}


_INTERNSHIP_BULLET_RE = re.compile(
    r"""(?xi)
    ^                           # anchor — must start the bullet text
    (?P<role>
        [A-Z][A-Za-z0-9\s&/,.-]{0,60}
    )
    \s*[-–—]\s*                 # separator between role and company
    (?P<company>
        [A-Z][A-Za-z0-9\s&/,.-]{1,80}
    )
    $
    """
)

_INTERN_ROLE_KW = re.compile(
    r"\b(intern|internship|trainee|industrial\s+trainee|summer\s+trainee|"
    r"apprentice|co-op|placement|vocational)\b",
    re.IGNORECASE,
)


def _is_separate_internship_bullet(bullet: str) -> bool:
    """
    Return True if a bullet that appears inside an experience section is actually
    a SEPARATE internship entry (not a work-task of the current job).

    Matches lines like:
      "Web Data Scraping & Content Strategy Internship - Flying Stone Films"
      "Software Trainee – XYZ Technologies Pvt. Ltd."

    Does NOT match normal work-task bullets that happen to mention "intern":
      "Mentored 3 interns on React best practices"
    """
    b = (bullet or "").strip()
    if not _INTERN_ROLE_KW.search(b):
        return False

    # Must look like "<Role> - <Company>" (noun phrase, not an action sentence)
    m = _INTERNSHIP_BULLET_RE.match(b)
    if not m:
        return False

    # Role part must contain the internship keyword (not just the company)
    if not _INTERN_ROLE_KW.search(m.group("role")):
        return False

    # Reject if it starts with a work action verb
    action_start_re = re.compile(
        r"^(?:mentored|trained|supervised|managed|led|developed|built|"
        r"implemented|debugged|tested|collaborated|conducted)\b",
        re.IGNORECASE,
    )
    if action_start_re.match(b):
        return False

    return True


def _parse_internship_from_bullet(bullet: str) -> dict:
    """
    Parse a separate-internship bullet into {role, company} dict.
    """
    b = bullet.strip()
    m = _INTERNSHIP_BULLET_RE.match(b)
    if m:
        return {"role": m.group("role").strip(), "company": m.group("company").strip()}
    # Fallback: take the whole text as the role
    return {"role": b, "company": ""}


def markdown_to_canonical(markdown_text: str, additional_links: Optional[List[str]] = None) -> CanonicalResume:
    """
    Parse a Markdown resume into the structured CanonicalResume model.
    Extracts sections by heading hierarchy:
      # Candidate Name
      ## Sections (Experience, Projects, Education, Skills, Summary, etc.)
      ### Items (Role / Company, Project, Degree)
      - Bullet points
    """
    resume = CanonicalResume()
    markdown_text = _normalize_markdown(markdown_text)
    lines = markdown_text.splitlines()

    # Link extraction
    all_links = extract_github_urls(markdown_text, additional_links) + \
                extract_linkedin_urls(markdown_text, additional_links) + \
                extract_portfolio_urls(markdown_text, additional_links)
    resume.links = sorted(list(set(all_links)))

    # Profile contact detection
    resume.profile.email = extract_email(markdown_text)
    if resume.profile.email == "Not Found":
        resume.profile.email = ""
    resume.profile.phone = extract_phone(markdown_text)
    if resume.profile.phone == "Not Found":
        resume.profile.phone = ""

    gh_urls = extract_github_urls(markdown_text, additional_links)
    if gh_urls:
        resume.profile.github = gh_urls[0]

    li_urls = extract_linkedin_urls(markdown_text, additional_links)
    if li_urls:
        resume.profile.linkedin = li_urls[0]

    pf_urls = extract_portfolio_urls(markdown_text, additional_links)
    if pf_urls:
        resume.profile.portfolio = pf_urls[0]

    # Section Parser State
    current_section: Optional[str] = None
    current_sub_item: Optional[Dict[str, Any]] = None
    current_section_lines: List[str] = []
    raw_section_titles: Dict[str, str] = {}

    orphan_exp: List[str] = []  # experience bullets that had no role/company header

    def commit_sub_item(sec: str, item: Dict[str, Any]):
        if not item:
            return
        # A job listed under PROJECTS (company-style name) is really experience
        if sec == "projects" and _is_work_entry(
            item.get("name", ""),
            list(item.get("highlights", [])) + [item.get("description", "")],
        ):
            hl = list(item.get("highlights", []))
            desc = (item.get("description") or "").strip()
            if desc:
                hl = _split_inline_bullets(desc) + hl
            item = {**item, "company": item.get("name", "").strip(), "role": "", "highlights": hl}
            sec = "experience"

        if sec == "experience":
            start = item.get("start_date", "") or ""
            end = item.get("end_date", "") or ""
            highlights: List[str] = []
            for h in item.get("highlights", []):
                for piece in _split_inline_bullets(h):
                    # a flattened "February - April 2026 * ..." puts the dates first
                    if not (start or end) and is_date_str(piece):
                        start, end = extract_dates(piece)
                        continue
                    highlights.append(piece)
            start = _fix_start_year(start, end)
            role = (item.get("role", "") or "").strip() or _infer_role(highlights)
            if not role and not (item.get("company", "") or "").strip():
                # No title at all -> do not create an item literally called "Experience";
                # these bullets are attached to the real job at the end of parsing.
                orphan_exp.extend(highlights)
                return
            resume.experience.append(ExperienceItem(
                id=generate_id("exp"),
                company=item.get("company", ""),
                role=role,
                location=item.get("location", ""),
                start_date=start,
                end_date=end,
                current="present" in end.lower(),
                highlights=highlights,
                technologies=item.get("technologies", [])
            ))
        elif sec == "projects":
            p_name = item.get("name", "").strip()
            p_sub = item.get("subtitle", "").strip()
            p_desc = item.get("description", "").strip()
            p_hl = item.get("highlights", [])
            p_bullets = item.get("description_bullets", []) or p_hl
            p_tech = item.get("technologies", [])
            if not p_sub and any(sep in p_name for sep in (" — ", " – ")):
                parts = re.split(r'\s*(?:—|–)\s*', p_name, maxsplit=1)
                if len(parts) >= 2:
                    p_name = parts[0].strip()
                    p_sub = parts[1].strip()
            elif p_sub and p_sub.lower() in p_name.lower():
                p_name = re.sub(re.escape(p_sub), "", p_name, flags=re.IGNORECASE).rstrip(" —-– ").strip()

            if not p_sub and p_desc and len(p_desc.splitlines()) == 1 and len(p_desc) < 120:
                p_sub = p_desc
            if not p_desc and p_sub:
                p_desc = p_sub

            if p_sub and p_tech:
                p_tech = [t for t in p_tech if t.strip() and t.strip().lower() != p_sub.lower()]

            resume.projects.append(ProjectItem(
                id=generate_id("proj"),
                name=p_name,
                subtitle=p_sub,
                description=p_desc,
                highlights=p_hl,
                description_bullets=p_bullets,
                technologies=p_tech,
                github_url=item.get("github_url", ""),
                live_url=item.get("live_url", "")
            ))
        elif sec == "education":
            resume.education.append(EducationItem(
                id=generate_id("edu"),
                institution=item.get("institution", ""),
                degree=item.get("degree", ""),
                field_of_study=item.get("field_of_study", ""),
                start_date=item.get("start_date", ""),
                end_date=item.get("end_date", ""),
                gpa=item.get("gpa", ""),
                honors=item.get("honors", [])
            ))

    def commit_section():
        nonlocal current_sub_item, current_section_lines
        if not current_section:
            return

        if current_sub_item:
            commit_sub_item(current_section, current_sub_item)
            current_sub_item = None

        text_block = "\n".join(current_section_lines).strip()

        if current_section == "summary":
            resume.summary = text_block

        elif current_section == "skills":
            cat = CategorizedSkills()
            categorized_found = False

            for line in current_section_lines:
                clean = line.strip().lstrip("-*• ")
                if not clean:
                    continue
                m = re.match(r'^(?:\*\*)?([A-Za-z0-9\s/&,]+?)(?:\*\*)?\s*:\s*(.+)$', clean)
                if m:
                    cat_header = m.group(1).strip().lower()
                    items_str = m.group(2).strip()
                    raw_items = [re.sub(r'[*_`]', '', item).strip() for item in re.split(r'[,;|/]+', items_str) if item.strip()]
                    if raw_items:
                        categorized_found = True
                        for item in raw_items:
                            clean_item = item.strip()
                            if not clean_item:
                                continue
                            group = get_skill_category(clean_item)
                            if group == "other":
                                if any(kw in cat_header for kw in ["programming", "language", "languages", "core"]):
                                    group = "technical"
                                elif any(kw in cat_header for kw in ["framework", "library", "libraries", "web", "ml", "ai"]):
                                    group = "frameworks"
                                elif any(kw in cat_header for kw in ["database", "storage", "sql", "nosql"]):
                                    group = "databases"
                                elif any(kw in cat_header for kw in ["cloud", "devops", "infra", "aws", "gcp", "azure"]):
                                    group = "cloud"
                                elif any(kw in cat_header for kw in ["tool", "tools", "platform", "platforms", "utilities", "developer"]):
                                    group = "tools"
                            
                            target = getattr(cat, group, cat.other)
                            formatted = clean_item if (len(clean_item) <= 4 and clean_item.isupper()) else clean_item
                            if formatted not in target and formatted.lower() not in [t.lower() for t in target]:
                                target.append(formatted)

            if not categorized_found or not cat.all_skills():
                all_tokens = []
                for line in current_section_lines:
                    clean = line.strip().lstrip("-*• ")
                    clean = re.sub(r'^\*\*[^*]+\*\*:\s*', '', clean)
                    items = [re.sub(r'[*_`]', '', item).strip() for item in re.split(r'[,;|/]+', clean) if item.strip()]
                    all_tokens.extend(items)

                found_skills = extract_skills(text_block)
                for s in found_skills:
                    if s.lower() not in [t.lower() for t in all_tokens]:
                        all_tokens.append(s)

                for item in all_tokens:
                    clean_item = item.strip()
                    if not clean_item:
                        continue
                    group = get_skill_category(clean_item)
                    target = getattr(cat, group, cat.other)
                    formatted = clean_item if (len(clean_item) <= 4 and clean_item.isupper()) else clean_item
                    if formatted not in target and formatted.lower() not in [t.lower() for t in target]:
                        target.append(formatted)

            resume.skills = cat

        elif current_section == "certifications":
            expanded_lines = []
            for line in current_section_lines:
                clean_raw = line.strip()
                if not clean_raw:
                    continue
                # Split if multiple certs concatenated with ' * ' or ' • '
                sub_parts = [p.strip() for p in re.split(r'\s+[*•]\s+|\s+(?=(?:[IVX]{1,4}|\d{1,2})[.)]\s+[A-Z])', clean_raw) if p.strip()]
                expanded_lines.extend(sub_parts if sub_parts else [clean_raw])

            for line in expanded_lines:
                clean = line.strip().lstrip("-*• ")
                clean = re.sub(r'^(?:[IVX]{1,4}|\d{1,2})[.)]\s+', '', clean)  # "I. NPTEL" -> "NPTEL"
                if not clean:
                    continue
                # Extract date if present, e.g. (2023) or (2022–2024)
                date_match = re.search(r'\(([^)]*(?:\d{4}|present|current)[^)]*)\)', clean, re.IGNORECASE)
                issue_date = date_match.group(1).strip() if date_match else ""
                clean_no_date = clean.replace(date_match.group(0), "").strip() if date_match else clean

                # Extract credential URL if present
                url_match = re.search(r'\[(?:Verify|Credential|Link|Certificate)\]\((https?://[^\)]+)\)|(https?://\S+)', clean, re.IGNORECASE)
                cred_url = (url_match.group(1) or url_match.group(2)).strip() if url_match else ""
                if cred_url:
                    clean_no_date = re.sub(r'\[(?:Verify|Credential|Link|Certificate)\]\([^\)]+\)|https?://\S+', '', clean_no_date).strip()

                name_bold_match = re.search(r'\*\*(.*?)\*\*', clean_no_date)
                parts = [p.strip() for p in re.split(r'\s*(?:—|–|\|)\s*|(?<=\w)\s+-\s+(?=\w)|:\s+', clean_no_date) if p.strip()]

                known_issuers = {"nptel", "c-dac", "cdac", "aws", "amazon", "google", "coursera", "udemy", "microsoft", "oracle", "cisco", "meta", "ibm"}

                if name_bold_match:
                    cert_name = re.sub(r'[*_`•]', '', name_bold_match.group(1)).strip()
                    issuer = ""
                    for p in parts:
                        p_clean = re.sub(r'[*_`•]', '', p).strip()
                        if p_clean and p_clean != cert_name:
                            issuer = p_clean
                            break
                elif len(parts) >= 2:
                    p0_clean = re.sub(r'[*_`•]', '', parts[0]).strip()
                    p1_clean = re.sub(r'[*_`•]', '', parts[1]).strip()
                    if p0_clean.lower() in known_issuers and p1_clean.lower() not in known_issuers:
                        issuer = p0_clean
                        cert_name = p1_clean
                    elif p1_clean.lower() in known_issuers:
                        issuer = p1_clean
                        cert_name = p0_clean
                    else:
                        cert_name = p0_clean
                        issuer = p1_clean
                else:
                    cert_name = re.sub(r'[*_`•]', '', clean_no_date).strip()
                    issuer = ""

                cert_name = re.sub(r'\s+', ' ', re.sub(r'[*_`•]', '', cert_name)).strip()
                issuer = re.sub(r'\s+', ' ', re.sub(r'[*_`•]', '', issuer)).strip()

                if cert_name:
                    resume.certifications.append(CertificationItem(
                        id=generate_id("cert"),
                        name=cert_name,
                        issuer=issuer,
                        issue_date=issue_date,
                        credential_url=cred_url
                    ))

        elif current_section == "achievements":
            for line in current_section_lines:
                clean = line.strip().lstrip("-*• ")
                if not clean:
                    continue
                # Check for explicit **Bold Title**: description pattern
                title_match = re.search(r'\*\*(.*?)\*\*', clean)
                if title_match:
                    ach_title = title_match.group(1)
                    desc = clean.split(":", 1)[1].strip() if ":" in clean else ""
                elif ":" in clean:
                    # Only split on ":" if the part before it is a short label (≤5 words).
                    # Full sentences like "Built REST APIs; completed internship at CDAC"
                    # must NOT be split — the colon may appear mid-sentence.
                    before_colon = clean.split(":", 1)[0].strip()
                    if len(before_colon.split()) <= 5:
                        ach_title = before_colon
                        desc = clean.split(":", 1)[1].strip()
                    else:
                        ach_title = clean   # keep full sentence intact
                        desc = ""
                else:
                    ach_title = clean
                    desc = ""
                resume.achievements.append(AchievementItem(
                    id=generate_id("ach"),
                    title=ach_title,
                    description=desc
                ))

        elif current_section in ("hobbies", "interests"):
            hobbies_items = []
            for line in current_section_lines:
                clean = line.strip().lstrip("-*• ")
                if clean:
                    hobbies_items.append(clean)
            if hobbies_items:
                resume.custom_sections.append(CustomSectionItem(
                    id=generate_id("sec"),
                    title="Hobbies & Interests",
                    items=hobbies_items
                ))
        elif current_section:
            custom_items = []
            for line in current_section_lines:
                clean = line.strip().lstrip("-*• ")
                if clean:
                    custom_items.append(clean)
            if custom_items:
                sec_title = raw_section_titles.get(current_section, current_section.replace("_", " ").title())
                resume.custom_sections.append(CustomSectionItem(
                    id=generate_id("sec"),
                    title=sec_title,
                    items=custom_items
                ))

        current_section_lines = []

    # Ensure name extraction fallback
    from app.parser.resume_parser import extract_candidate_name
    detected_cand_name = extract_candidate_name(markdown_text)
    if detected_cand_name and detected_cand_name != "Candidate":
        resume.profile.name = detected_cand_name

    def is_date_str(s: str) -> bool:
        clean = re.sub(r'^[#\s*_\(\)\[\]\-–—\|]+|[#\s*_\(\)\[\]\-–—\|]+$', '', s.strip())
        has_year = bool(re.search(r'\b(?:\d{4}|present|current|ongoing|expected)\b', clean, re.IGNORECASE))
        has_sep = bool(re.search(r'[-–—\ufffd/|]|to', clean, re.IGNORECASE))
        is_month_year = bool(re.search(r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{2,4}\b', clean, re.IGNORECASE))
        return (has_year or is_month_year) and (has_sep or is_month_year or any(kw in clean.lower() for kw in ["present", "current", "ongoing", "expected", "year", "batch", "class of"])) and len(clean.split()) <= 8

    def extract_dates(s: str) -> Tuple[str, str]:
        clean = re.sub(r'^[#\s*_\(\)\[\]\-–—\|]+|[#\s*_\(\)\[\]\-–—\|]+$', '', s.strip())
        clean_dates = re.sub(r'^(?:expected|batch|class of|duration|period|dates?):\s*', '', clean, flags=re.IGNORECASE)
        dates = [d.strip() for d in re.split(r'[-–—\ufffd/|]+|\bto\b', clean_dates, flags=re.IGNORECASE) if d.strip()]
        start = dates[0] if len(dates) > 0 else ""
        end = dates[1] if len(dates) > 1 else ""
        if start.lower() in ("present", "current", "ongoing") and not end:
            end = "Present"
            start = ""
        elif "present" in end.lower() or "ongoing" in end.lower() or "current" in end.lower():
            end = "Present"
        return start, end

    # Iterate lines
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # # Candidate Name
        if stripped.startswith("# ") and not stripped.startswith("## "):
            name_cand = stripped[2:].strip()
            if not re.search(r'@|http|phone', name_cand, re.IGNORECASE):
                resume.profile.name = name_cand
            continue

        # Location heuristic in top lines
        if not current_section and ("location:" in stripped.lower() or "city" in stripped.lower()):
            loc_match = re.search(r'Location:\s*([^|]+)', stripped, re.IGNORECASE)
            if loc_match:
                resume.profile.location = loc_match.group(1).strip()

        # Check for Major Section Header
        clean_sec_cand = re.sub(r'^[#\s*]+', '', stripped).rstrip(':* ').strip().lower()
        matched_sec = None

        if "certif" in clean_sec_cand:
            matched_sec = "certifications"
        else:
            for sec_name, keywords in SECTION_HEADERS.items():
                if clean_sec_cand in keywords or any(clean_sec_cand == kw for kw in keywords):
                    matched_sec = sec_name
                    break
            if not matched_sec:
                for sec_name, keywords in SECTION_HEADERS.items():
                    if any(kw in clean_sec_cand for kw in keywords if len(kw) > 4):
                        matched_sec = sec_name
                        break
            if not matched_sec:
                if any(kw in clean_sec_cand for kw in ["summary", "about", "bio", "profile", "professional summary", "career objective", "objective"]):
                    matched_sec = "summary"
                elif any(kw in clean_sec_cand for kw in ["achievement", "achievements", "awards", "honors"]):
                    matched_sec = "achievements"

        is_heading_line = False
        if stripped.startswith("## "):
            is_heading_line = True
        elif stripped.endswith(":") and len(stripped.split()) <= 5 and not stripped.startswith(("-", "*", "•", "–", "—")) and matched_sec:
            is_heading_line = True
        elif stripped.isupper() and len(stripped.split()) <= 4 and not stripped.startswith(("-", "*", "•", "–", "—")) and len(stripped) >= 3:
            if matched_sec:
                is_heading_line = True
            elif any(w in clean_sec_cand for w in ["summary", "skill", "project", "experience", "education", "certif", "achievement", "strength", "language", "hobbi", "interest", "award", "activity"]):
                is_heading_line = True
        elif not stripped.startswith(("-", "*", "•", "–", "—", "#", "(")) and len(stripped.split()) <= 3 and matched_sec:
            is_heading_line = True

        # Golden template inline rows: "CERTIFICATIONS: I. ..." / "HOBBIES: Cricket, Badminton."
        # These must switch section even when content follows on the same line.
        inline_labeled = re.match(
            r'^(?:#+\s*)?(CERTIFICATIONS?|HOBBIES|INTERESTS|ACHIEVEMENTS?|AWARDS)\s*:\s*(.*)$',
            stripped,
            re.IGNORECASE,
        )
        if inline_labeled:
            label = inline_labeled.group(1).lower()
            rest = (inline_labeled.group(2) or "").strip()
            if label.startswith("cert"):
                matched_sec = "certifications"
            elif label.startswith("hobb") or label.startswith("interest"):
                matched_sec = "hobbies"
            else:
                matched_sec = "achievements"
            commit_section()
            current_section = matched_sec
            if rest:
                current_section_lines.append(rest)
            continue

        if is_heading_line:
            if not matched_sec:
                matched_sec = clean_sec_cand
            raw_title = stripped.lstrip('#* ').rstrip(':* ').strip()
            raw_section_titles[matched_sec] = raw_title
            commit_section()
            current_section = matched_sec
            continue

        # Bullet point detection
        is_bullet = bool(re.match(r'^[•\-\–\—\u2022]\s+|^\*\s+|^\d+[\.\)]\s+', stripped))
        if is_bullet:
            bullet_text = re.sub(r'^[•\-\*\–\—\u2022\d\.\)\s]+', '', stripped).strip()
            clean_bullet_lower = bullet_text.strip(" *_\t").lower()
            if current_section == "education":
                # Check for GPA / CGPA / Percentage / Grade in bullet
                if any(kw in clean_bullet_lower for kw in ["gpa", "cgpa", "percentage", "score", "grade"]):
                    gpa_match = re.search(r'(?:cgpa|gpa|percentage|score|grade)[:\s*]+([0-9\.\/%]+(?:\s*(?:out of|/)\s*[0-9\.]+)?%?)', bullet_text, re.IGNORECASE)
                    if gpa_match:
                        val = gpa_match.group(1).strip()
                        if current_sub_item:
                            current_sub_item["gpa"] = val
                        elif resume.education:
                            resume.education[-1].gpa = val
                        continue
                if any(kw in clean_bullet_lower for kw in ["honors", "awards", "coursework"]):
                    honors_part = re.search(r'(?:honors?|awards?|coursework)[:\s*]+(.*)', bullet_text, re.IGNORECASE)
                    if honors_part:
                        h_list = [h.strip() for h in honors_part.group(1).split(",") if h.strip()]
                        if current_sub_item:
                            current_sub_item["honors"].extend(h_list)
                        elif resume.education:
                            resume.education[-1].honors.extend(h_list)
                        continue
                if not current_sub_item:
                    current_sub_item = {"highlights": [], "technologies": []}
                current_sub_item["highlights"].append(bullet_text)
            elif current_section in ("experience", "projects"):
                if not current_sub_item:
                    current_sub_item = {"highlights": [], "technologies": []}

                # ── Certification bullet detected inside experience/projects ──────
                # e.g. "Cloud Computing Course - CDAC; Cloud Computing Certification Course (6 months)"
                # Route to resume.certifications instead of job highlights.
                if current_section == "experience" and _is_cert_bullet(bullet_text):
                    cert_data = _parse_cert_from_bullet(bullet_text)
                    if cert_data["name"]:
                        resume.certifications.append(CertificationItem(
                            id=generate_id("cert"),
                            name=cert_data["name"],
                            issuer=cert_data["issuer"],
                            issue_date=cert_data["issue_date"],
                            credential_url="",
                        ))
                    continue

                # ── Separate internship bullet detected inside experience ──────────
                # e.g. "Web Data Scraping & Content Strategy Internship - Flying Stone Films"
                # Route to a new ExperienceItem instead of the current job's highlights.
                if current_section == "experience" and _is_separate_internship_bullet(bullet_text):
                    # Commit pending item first so the new internship gets its own entry
                    if current_sub_item and (current_sub_item.get("role") or current_sub_item.get("company")):
                        commit_sub_item(current_section, current_sub_item)
                        current_sub_item = {"highlights": [], "technologies": []}
                    parsed_intern = _parse_internship_from_bullet(bullet_text)
                    resume.experience.append(ExperienceItem(
                        id=generate_id("exp"),
                        company=parsed_intern["company"],
                        role=parsed_intern["role"],
                        location="",
                        start_date="",
                        end_date="",
                        current=False,
                        highlights=[],
                        technologies=[],
                    ))
                    continue

                current_sub_item["highlights"].append(bullet_text)
            elif current_section:
                current_section_lines.append(bullet_text)
            continue

        # Date line detection within experience/projects/education
        check_dt = re.sub(r'^[#\s*_\(\)\[\]]+', '', stripped).strip()
        if current_section in ("experience", "projects", "education") and (is_date_str(stripped) or is_date_str(check_dt)):
            s_date, e_date = extract_dates(check_dt)
            if current_sub_item:
                if not current_sub_item.get("start_date"):
                    current_sub_item["start_date"] = s_date
                if not current_sub_item.get("end_date"):
                    current_sub_item["end_date"] = e_date
            elif current_section == "experience" and resume.experience:
                if not resume.experience[-1].start_date:
                    resume.experience[-1].start_date = s_date
                if not resume.experience[-1].end_date:
                    resume.experience[-1].end_date = e_date
            elif current_section == "education" and resume.education:
                if not resume.education[-1].start_date:
                    resume.education[-1].start_date = s_date
                if not resume.education[-1].end_date:
                    resume.education[-1].end_date = e_date
            continue

        # Technologies / GPA / Honors line check
        clean_stripped_lower = stripped.strip(" *_\t").lower()
        if clean_stripped_lower.startswith(("technologies:", "tech:", "stack:")):
            tech_text = re.sub(r'^[*_\s]*(?:technologies|tech|stack):[*_\s]*', '', stripped, flags=re.IGNORECASE).strip(" *_\r\n")
            tech_list = [t.strip() for t in tech_text.split(",") if t.strip()]
            if current_sub_item:
                current_sub_item["technologies"] = tech_list
            continue

        pct_match = re.match(r'^[*\s_]*(\d{1,2}(?:\.\d+)?%)[*\s_]*$', stripped)
        if pct_match and current_section == "education":
            val = pct_match.group(1).strip()
            if current_sub_item:
                current_sub_item["gpa"] = val
            elif resume.education:
                resume.education[-1].gpa = val
            continue

        # Education entry detection (must not be dropped by standalone GPA/grade checks)
        deg_kws = r'\b(bachelor|master|b\.?tech|m\.?tech|b\.?e\.?|m\.?e\.?|b\.?s\.?|m\.?s\.?|b\.?sc|m\.?sc|bca|mca|ph\.?d|diploma|associate|higher secondary|secondary school|hsc|ssc|bba|mba|degree)\b'
        inst_kws = r'\b(university|institute|college|school|academy|vidyalaya|polytechnic|campus|iit|nit|iiit|bits)\b'
        has_inst = bool(re.search(inst_kws, stripped, re.IGNORECASE))
        has_deg = bool(re.search(deg_kws, stripped, re.IGNORECASE))
        is_edu_header_candidate = current_section == "education" and (
            has_inst or has_deg or stripped.startswith("### ")
            or (len(stripped.split()) > 6 and any(sep in stripped for sep in ("—", "–", "|")))
        )

        if not is_edu_header_candidate and (
            clean_stripped_lower.startswith(("gpa:", "cgpa:", "percentage:", "grade:", "score:"))
            or (len(stripped.split()) <= 6 and ("gpa:" in clean_stripped_lower or "cgpa:" in clean_stripped_lower or "grade:" in clean_stripped_lower or "score:" in clean_stripped_lower))
        ):
            gpa_match = re.search(r'(?:cgpa|gpa|percentage|score|grade)[:\s*]+([0-9\.\/%]+(?:\s*(?:out of|/)\s*[0-9\.]+)?%?)', stripped, re.IGNORECASE)
            if gpa_match:
                val = gpa_match.group(1).strip()
                if current_sub_item:
                    current_sub_item["gpa"] = val
                elif resume.education:
                    resume.education[-1].gpa = val
            if "honors:" in clean_stripped_lower and current_sub_item:
                honors_part = re.search(r'honors?:\s*(.*)', stripped, re.IGNORECASE)
                if honors_part:
                    current_sub_item["honors"] = [h.strip() for h in honors_part.group(1).split(",") if h.strip()]
            continue

        # Sub-item header detection
        is_sub_header = stripped.startswith("### ")
        if not is_sub_header and current_section in ("experience", "projects", "education"):
            if current_section == "education":
                if current_sub_item:
                    # If current item already has both degree and institution, a new college/degree line is a new sub-header
                    if current_sub_item.get("institution") and current_sub_item.get("degree"):
                        if has_inst or has_deg:
                            is_sub_header = True
                    # If current item already has institution, and new line has another institution, it's a new college!
                    elif current_sub_item.get("institution") and has_inst:
                        is_sub_header = True
                    # If current item already has degree, and new line has another degree, it's a new degree!
                    elif current_sub_item.get("degree") and has_deg:
                        is_sub_header = True
                    elif has_inst or has_deg:
                        is_sub_header = True
                    else:
                        is_sub_header = False
                elif has_inst or has_deg or is_edu_header_candidate:
                    is_sub_header = True
            elif "### " not in markdown_text or current_section in ("experience", "projects"):
                has_sep = bool(re.search(r'\s*(?:—|–|\||\bat\b|@)\s*|(?<=\w)\s+-\s+(?=\w)', stripped, re.IGNORECASE))
                is_bold_header = stripped.startswith("**") and ("**" in stripped[2:])
                not_sentence = not stripped.rstrip().endswith((".", ";", ","))
                is_action_verb = bool(re.match(r'^(?:architected|developed|built|designed|implemented|spearheaded|created|managed|led|integrated|engineered|optimized|reduced|increased)\b', clean_stripped_lower))
                if (has_sep or is_bold_header) and not_sentence and not is_action_verb and len(stripped.split()) <= 20 and not clean_stripped_lower.startswith(("note:", "location:", "cgpa:", "gpa:", "tech:", "technologies:")):
                    is_sub_header = True

        # Never let a date line or percentage be treated as a sub-header
        if is_sub_header and (is_date_str(stripped) or is_date_str(check_dt) or pct_match):
            is_sub_header = False
            s_date, e_date = extract_dates(check_dt)
            if current_sub_item:
                if not current_sub_item.get("start_date"): current_sub_item["start_date"] = s_date
                if not current_sub_item.get("end_date"): current_sub_item["end_date"] = e_date
            elif current_section == "experience" and resume.experience:
                if not resume.experience[-1].start_date: resume.experience[-1].start_date = s_date
                if not resume.experience[-1].end_date: resume.experience[-1].end_date = e_date
            continue

        if (is_sub_header and current_section in ("experience", "projects")
                and _clean_head(stripped) in _PLACEHOLDER_TITLES):
            # "### Experience" is a placeholder, not a real entry: close the current item and let
            # the bullets below it be handled as title-less bullets (merged at the end).
            if current_sub_item:
                commit_sub_item(current_section, current_sub_item)
                current_sub_item = None
            continue

        if (is_sub_header and current_section in ("experience", "projects") and current_sub_item
                and _attach_continuation(
                    current_sub_item,
                    stripped[4:].strip() if stripped.startswith("### ") else stripped)):
            continue

        if is_sub_header:
            if current_sub_item and current_section:
                commit_sub_item(current_section, current_sub_item)
                current_sub_item = None

            sub_title = stripped[4:].strip() if stripped.startswith("### ") else stripped

            current_sub_item = {
                "highlights": [],
                "technologies": []
            }

            # Dates pattern in parentheses
            date_match = re.search(r'\(([^)]*(?:\d{4}|present|current|ongoing|expected)[^)]*)\)', sub_title, re.IGNORECASE)
            if date_match:
                date_str = date_match.group(1).strip()
                s_date, e_date = extract_dates(date_str)
                current_sub_item["start_date"] = s_date
                current_sub_item["end_date"] = e_date
                sub_title = sub_title.replace(date_match.group(0), "").strip()

            # Clean markdown links [label](url)
            sub_clean = re.sub(r'\[.*?\]\(.*?\)', '', sub_title)
            sub_clean = re.sub(r'\(.*?\)', '', sub_clean).strip().rstrip(":")

            if current_section == "experience":
                segs = [sg.strip() for sg in sub_clean.split("|")]
                if len(segs) > 1 and is_date_str(segs[-1]):
                    s_d, e_d = extract_dates(segs[-1])
                    if not current_sub_item.get("start_date"):
                        current_sub_item["start_date"] = s_d
                    if not current_sub_item.get("end_date"):
                        current_sub_item["end_date"] = e_d
                    sub_clean = " | ".join(segs[:-1])
                parts = [p.strip() for p in re.split(r'\s*(?:—|–|\||\bat\b|@)\s*|(?<=\w)\s+-\s+(?=\w)', sub_clean, flags=re.IGNORECASE) if p.strip()]
                if len(parts) >= 2:
                    current_sub_item["role"] = parts[0]
                    current_sub_item["company"] = parts[1]
                elif _LEGAL_SUFFIX_RE.search(sub_clean) or _COMPANY_WORD_RE.search(sub_clean):
                    current_sub_item["role"] = ""
                    current_sub_item["company"] = sub_clean
                else:
                    current_sub_item["role"] = sub_clean
                    current_sub_item["company"] = ""

            elif current_section == "projects":
                gh_match = re.search(r'\[(?:Code|GitHub)\]\((https?://github\.com/[^\)]+)\)', sub_title, re.IGNORECASE)
                if gh_match:
                    current_sub_item["github_url"] = gh_match.group(1)
                live_match = re.search(r'\[(?:Demo|Live|Link)\]\((https?://[^\)]+)\)', sub_title, re.IGNORECASE)
                if live_match:
                    current_sub_item["live_url"] = live_match.group(1)

                clean_p_header = re.sub(r'[*_`]', '', sub_clean).strip()

                # Check if '|' is used to separate title/subtitle from technologies
                if "|" in clean_p_header:
                    p_segs = [s.strip() for s in clean_p_header.split("|") if s.strip()]
                    title_block = p_segs[0]
                    tech_tokens = []
                    for seg in p_segs[1:]:
                        tech_tokens.extend([t.strip() for t in seg.split(",") if t.strip()])
                    current_sub_item["technologies"] = tech_tokens

                    dash_parts = [p.strip() for p in re.split(r'\s*(?:—|–)\s*|(?<=\S)\s+-\s+(?=\S)', title_block) if p.strip()]
                    if len(dash_parts) >= 2:
                        current_sub_item["name"] = dash_parts[0]
                        current_sub_item["subtitle"] = " — ".join(dash_parts[1:])
                        current_sub_item["description"] = current_sub_item["subtitle"]
                    else:
                        current_sub_item["name"] = title_block
                else:
                    dash_parts = [p.strip() for p in re.split(r'\s*(?:—|–)\s*|(?<=\S)\s+-\s+(?=\S)', clean_p_header) if p.strip()]
                    if len(dash_parts) >= 3:
                        current_sub_item["name"] = dash_parts[0]
                        current_sub_item["subtitle"] = dash_parts[1]
                        current_sub_item["description"] = dash_parts[1]
                        current_sub_item["technologies"] = [t.strip() for t in dash_parts[2].split(",") if t.strip()]
                    elif len(dash_parts) == 2:
                        p0, p1 = dash_parts[0], dash_parts[1]
                        is_tech_list = (
                            p1.lower().startswith(("tech:", "technologies:", "stack:"))
                            or ("," in p1 and any(t in p1.lower() for t in ["react", "node", "python", "flask", "fastapi", "sql", "java", "docker", "aws", "gcp"]))
                        )
                        is_subtitle_phrase = any(w in p1.lower() for w in [
                            "platform", "debugger", "engine", "system", "tool", "analyzer", "scanner",
                            "dashboard", "app", "application", "service", "assistant", "generator",
                            "ai-powered", "intelligence", "framework", "cache", "client", "extension", "pipeline"
                        ])
                        if is_tech_list and not is_subtitle_phrase:
                            current_sub_item["name"] = p0
                            current_sub_item["technologies"] = [t.strip() for t in re.sub(r'^(?:tech|technologies|stack):\s*', '', p1, flags=re.IGNORECASE).split(",") if t.strip()]
                        else:
                            current_sub_item["name"] = p0
                            current_sub_item["subtitle"] = p1
                            current_sub_item["description"] = p1
                    elif dash_parts:
                        current_sub_item["name"] = dash_parts[0]

            elif current_section == "education":
                # Use full-line parser so "| 8.5 CGPA | 2024–2027" is not dropped
                parsed = parse_education_entry_line(sub_title)
                for k in ("institution", "degree", "field_of_study", "gpa", "start_date", "end_date"):
                    val = parsed.get(k) or ""
                    if val and not current_sub_item.get(k):
                        current_sub_item[k] = val
                # Fallback if parser got nothing useful
                if not current_sub_item.get("institution") and not current_sub_item.get("degree"):
                    current_sub_item["institution"] = sub_clean
            continue

        # Subsequent lines handling
        if current_section == "education" and stripped:
            deg_keywords = r'\b(bachelor|master|b\.?tech|m\.?tech|b\.?e\.?|m\.?e\.?|b\.?s\.?|m\.?s\.?|b\.?sc|m\.?sc|bca|mca|ph\.?d|doctorate|diploma|associate|higher secondary|secondary school|hsc|ssc|bba|mba|degree)\b'
            inst_keywords = r'\b(university|institute|college|school|academy|vidyalaya|polytechnic|campus|iit|nit|iiit|bits)\b'
            has_inst = bool(re.search(inst_keywords, stripped, re.IGNORECASE))
            has_deg = bool(re.search(deg_keywords, stripped, re.IGNORECASE))
            
            if current_sub_item:
                # If current sub-item already has both institution and degree, and a new institution/degree arrives:
                if current_sub_item.get("institution") and current_sub_item.get("degree") and (has_inst or has_deg):
                    commit_sub_item("education", current_sub_item)
                    current_sub_item = {"highlights": [], "technologies": []}
                    if has_deg and " in " in stripped.lower():
                        deg_split = re.split(r'\s+in\s+', stripped, flags=re.IGNORECASE)
                        current_sub_item["degree"] = deg_split[0].strip()
                        current_sub_item["field_of_study"] = deg_split[1].strip()
                    elif has_deg:
                        current_sub_item["degree"] = stripped
                    elif has_inst:
                        current_sub_item["institution"] = stripped
                elif re.search(deg_keywords, stripped, re.IGNORECASE) and not current_sub_item.get("degree"):
                    if " in " in stripped.lower():
                        deg_split = re.split(r'\s+in\s+', stripped, flags=re.IGNORECASE)
                        current_sub_item["degree"] = deg_split[0].strip()
                        current_sub_item["field_of_study"] = deg_split[1].strip()
                    else:
                        current_sub_item["degree"] = stripped
                elif re.search(inst_keywords, stripped, re.IGNORECASE) and not current_sub_item.get("institution"):
                    current_sub_item["institution"] = stripped
                elif not current_sub_item.get("degree") and not current_sub_item.get("institution"):
                    current_sub_item["institution"] = stripped
                elif not current_sub_item.get("degree"):
                    current_sub_item["degree"] = stripped
                elif not current_sub_item.get("institution"):
                    current_sub_item["institution"] = stripped
                elif has_inst or has_deg:
                    commit_sub_item("education", current_sub_item)
                    current_sub_item = {"highlights": [], "technologies": []}
                    if has_inst:
                        current_sub_item["institution"] = stripped
                    else:
                        current_sub_item["degree"] = stripped
            elif current_section:
                current_section_lines.append(stripped)

        elif stripped:
            # Check if this is an italic-wrapped line
            # e.g. *Tech1, Tech2...* or *AI-Powered Platform*
            _is_italic_line = (
                stripped.startswith("*") and stripped.endswith("*")
                and not stripped.startswith("**")
                and len(stripped) > 2
            )
            if (current_sub_item and current_section in ("projects", "experience")
                    and current_sub_item.get("highlights")):
                current_sub_item["highlights"][-1] += f" {stripped}"
            elif current_sub_item and current_section == "projects" and _is_italic_line:
                # Italic line immediately after project heading.
                # Distinguish: tech list (*Python, FastAPI, Docker*) vs subtitle (*AI-Powered Platform*)
                italic_content = stripped[1:-1].strip()
                tokens = [t.strip() for t in italic_content.split(",")]
                # Heuristic: ≥2 short, mostly-capitalized tokens → technology stack line
                looks_like_tech = (
                    len(tokens) >= 2
                    and all(len(t) < 40 for t in tokens)
                    and not any(t[0].islower() for t in tokens[:2] if t)
                )
                # Also treat as tech list when the subtitle is already populated from the heading
                has_subtitle_already = bool(current_sub_item.get("subtitle"))
                if looks_like_tech or (has_subtitle_already and len(tokens) >= 2):
                    # Merge into technologies, deduplicating
                    existing = current_sub_item.get("technologies") or []
                    merged = list(existing)
                    for t in tokens:
                        if t and t not in merged:
                            merged.append(t)
                    current_sub_item["technologies"] = merged
                else:
                    # Treat as subtitle/tagline
                    if not current_sub_item.get("subtitle"):
                        current_sub_item["subtitle"] = italic_content
                    if not current_sub_item.get("description"):
                        current_sub_item["description"] = italic_content
            elif current_sub_item and current_section == "projects":
                clean_line = stripped.lstrip("*").rstrip("*").strip()
                if not current_sub_item.get("subtitle") and len(clean_line.splitlines()) == 1 and len(clean_line) < 120:
                    current_sub_item["subtitle"] = clean_line
                if not current_sub_item.get("description"):
                    current_sub_item["description"] = clean_line
                else:
                    current_sub_item["description"] += f" {stripped}"
            elif current_sub_item and not current_sub_item.get("description"):
                current_sub_item["description"] = stripped
            elif current_section:
                current_section_lines.append(stripped)



    # Commit any trailing section
    commit_section()

    if orphan_exp:
        real = next((e for e in resume.experience if (e.company or e.role)), None)
        if real is None:
            resume.experience.append(ExperienceItem(
                id=generate_id("exp"), company="", role="", location="",
                start_date="", end_date="", current=False,
                highlights=orphan_exp, technologies=[]
            ))
        else:
            for h in orphan_exp:
                if not any(_similar_text(h, x) for x in real.highlights):
                    real.highlights.append(h)

    # Fallback skill extraction if skills section wasn't explicitly structured
    if not resume.skills.all_skills():
        raw_skills = extract_skills(markdown_text)
        resume.skills = build_categorized_skills(list(raw_skills))

    return resume


def pdf_dict_to_markdown(pages_dict: List[Dict[str, Any]]) -> str:
    """
    Convert PyMuPDF structured page dictionaries with span-level typography 
    (font size, bold flags, font families, bounding boxes) into semantic Markdown.
    
    Identifies:
    1. Candidate Name (largest font size at top of document) -> # Name
    2. Major Section Headers (larger font size or bold uppercase matching section keywords) -> ## Section
    3. Sub-Item Headers (bold font or distinct styling for project titles, job roles, colleges) -> ### Item Title
    4. Bullet items & details (regular font size / weights below bold titles) -> - Bullet text
    """
    if not pages_dict:
        return ""

    from collections import Counter

    # Collect all text spans across all pages to calculate typography statistics
    all_spans = []
    for page in pages_dict:
        for block in page.get("blocks", []):
            if block.get("type") == 0:  # text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        txt = span.get("text", "").strip()
                        if txt:
                            all_spans.append(span)

    if not all_spans:
        return ""

    # Calculate baseline typography metrics
    sizes = [round(s.get("size", 10.0), 1) for s in all_spans]
    size_counts = Counter(sizes)
    body_size = size_counts.most_common(1)[0][0] if size_counts else 10.0
    max_size = max(sizes) if sizes else 12.0

    lines_out: List[str] = []
    current_section = None
    first_non_empty = True

    for page_idx, page in enumerate(pages_dict):
        # Sort blocks vertically, then horizontally
        blocks = page.get("blocks", [])
        sorted_blocks = sorted(
            [b for b in blocks if b.get("type") == 0],
            key=lambda b: (round(b.get("bbox", (0, 0, 0, 0))[1], -1), b.get("bbox", (0, 0, 0, 0))[0])
        )

        for block in sorted_blocks:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue

                line_text = "".join(s.get("text", "") for s in spans).strip()
                if not line_text:
                    continue

                # Typography analysis of current line
                line_sizes = [s.get("size", body_size) for s in spans if s.get("text", "").strip()]
                line_max_size = max(line_sizes) if line_sizes else body_size

                # Check bold: flag bit 2 set, or font name containing bold/black/heavy/semibold/medium
                is_bold = any(
                    ((s.get("flags", 0) & 16) != 0) or 
                    any(b in s.get("font", "").lower() for b in ["bold", "black", "heavy", "semibold", "medium"])
                    for s in spans if s.get("text", "").strip()
                )

                # 1. Candidate Name detection: Top of first page, largest font
                if first_non_empty and page_idx == 0:
                    if (line_max_size >= max_size - 1.0 or line_max_size >= body_size + 2.5) and len(line_text.split()) <= 5 and not re.search(r'@|http|phone', line_text, re.IGNORECASE):
                        lines_out.append(f"# {line_text.title()}")
                        first_non_empty = False
                        continue
                    first_non_empty = False

                # 2. Major Section Heading detection (e.g. Education, Projects, Experience)
                clean_sec_cand = re.sub(r'^[#\s*•-]+', '', line_text).rstrip(':* ').strip().lower()
                matched_sec = None
                for sec_name, keywords in SECTION_HEADERS.items():
                    if clean_sec_cand in keywords or any(clean_sec_cand == kw for kw in keywords):
                        matched_sec = sec_name
                        break
                if not matched_sec and len(line_text.split()) <= 4 and (
                    line_text.isupper() or line_max_size >= body_size + 0.8
                ):
                    # e.g. "Professional Experience", "Academic Projects"
                    for sec_name, keywords in SECTION_HEADERS.items():
                        if any(kw in clean_sec_cand for kw in keywords if len(kw) > 4):
                            matched_sec = sec_name
                            break
                if not matched_sec:
                    if any(clean_sec_cand == kw for kw in ["summary", "about", "bio", "profile", "professional summary", "career objective", "objective"]):
                        matched_sec = "summary"
                    elif any(clean_sec_cand == kw for kw in ["achievement", "achievements", "awards", "honors"]):
                        matched_sec = "achievements"

                if matched_sec and (line_max_size >= body_size + 0.8 or is_bold or line_text.isupper() or len(line_text.split()) <= 4):
                    lines_out.append(f"\n## {matched_sec.title()}")
                    current_section = matched_sec
                    continue

                # 3. Sub-Item Header Detection (Bold Project Titles, Roles, Colleges)
                # e.g., "ISO Audit AI — AI-Powered ISO Audit Gap Analysis Platform"
                # "Pune Institute of Computer Technology"
                is_bullet = bool(re.match(r'^[•\-\*\–\—\u2022]\s*', line_text))

                if current_section in ("experience", "projects", "education") and not is_bullet:
                    # Distinguish titles (bold or larger size than body) from descriptions/bullets below
                    # NEVER convert a date line, location line, score, or tech line into a sub-item header (###)
                    clean_text_check = re.sub(r'^[#\s*_\(\)\[\]\-–—\|]+|[#\s*_\(\)\[\]\-–—\|]+$', '', line_text).strip()
                    is_date_cand = bool(re.search(r'\b(?:\d{4}|present|current|ongoing|expected)\b', clean_text_check, re.IGNORECASE)) and (
                        bool(re.search(r'[-–—/|]|to', clean_text_check, re.IGNORECASE)) or any(kw in clean_text_check.lower() for kw in ["present", "current", "ongoing", "expected", "year", "batch"])
                    ) and len(clean_text_check.split()) <= 8
                    is_pct = bool(re.match(r'^\d{1,2}(?:\.\d+)?%$', clean_text_check))
                    is_labeled = clean_text_check.lower().startswith(("cgpa:", "gpa:", "location:", "tech:", "technologies:", "stack:", "dates:", "period:"))
                    if is_date_cand or is_pct or is_labeled:
                        lines_out.append(line_text)
                        continue

                    if (is_bold or line_max_size >= body_size + 0.4) and len(line_text.split()) <= 20 \
                            and not line_text[:1].islower():
                        lines_out.append(f"\n### {line_text}")
                        continue

                # 4. Standard bullet or body line
                if is_bullet:
                    cleaned_bullet = re.sub(r'^[•\-\*\–\—\u2022]\s*', '', line_text)
                    lines_out.append(f"- {cleaned_bullet}")
                else:
                    lines_out.append(line_text)

    return "\n".join(lines_out).strip()


def blocks_to_markdown(blocks: List[Tuple[float, float, float, float, str, int, int]]) -> str:
    """
    Convert PyMuPDF extracted positional text blocks into standardized Markdown.
    Identifies headings based on capitalization and length, and bullets based on leading symbols.
    """
    if not blocks:
        return ""

    # Sort blocks vertically top-to-bottom, then left-to-right
    sorted_blocks = sorted(blocks, key=lambda b: (round(b[1], -1), b[0]))
    md_lines: List[str] = []

    first_block = True
    for b in sorted_blocks:
        text = b[4].strip()
        if not text:
            continue

        for line in text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            # First non-trivial line is likely candidate name
            if first_block and len(line_str.split()) <= 4 and not re.search(r'@|http|phone', line_str, re.IGNORECASE):
                md_lines.append(f"# {line_str.title()}")
                first_block = False
                continue
            first_block = False

            # Check if line is a major section heading
            line_lower = line_str.lower().rstrip(":")
            is_section = False
            for sec_name, keywords in SECTION_HEADERS.items():
                if line_lower in keywords or any(line_lower == kw for kw in keywords):
                    md_lines.append(f"\n## {sec_name.title()}")
                    is_section = True
                    break

            if is_section:
                continue

            # Check if bullet point
            if re.match(r'^[•\-\*\–\—\u2022]\s*', line_str):
                cleaned_bullet = re.sub(r'^[•\-\*\–\—\u2022]\s*', '', line_str)
                md_lines.append(f"- {cleaned_bullet}")
            else:
                md_lines.append(line_str)

    return "\n".join(md_lines).strip()