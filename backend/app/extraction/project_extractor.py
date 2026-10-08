"""
Project Extractor: splits the projects section into
{title, bullets[], technologies[], urls[]} entries.
Bullets are kept separate; titles never contain URLs or "(GitHub:".
"""
import re
from typing import List, Dict, Any
from app.utils.skills import extract_skills
from app.utils.text_utils import extract_all_urls

_HEADERS = {"projects", "personal projects", "academic projects", "key projects", "project"}
_ALL_SECTION_HEADERS = {
    "projects", "personal projects", "academic projects", "key projects", "project",
    "work experience", "experience", "education", "certifications", "skills",
    "technical skills", "professional summary", "summary", "achievements",
    "professional experience", "employment history", "career history"
}

_BULLET_START = re.compile(r'^\s*(?:[•●▪◦►·*]|[–—-])\s+')
_TECH_LINE = re.compile(r'^\s*(?:tech(?:nologies| stack)?|tools|stack)\s*[:\-]\s*(.+)$', re.I)
_LABELLED_URL = re.compile(r'\(\s*(?:github|live|demo|link|repo|code)\s*:?\s*https?://[^\s)]+\s*\)', re.I)
_BARE_URL = re.compile(r'https?://\S+')
_END_PUNCT = re.compile(r'[.!?]$')
_NUMBERED_PREFIX = re.compile(r'^\s*(?:\d+[\.\)]|project\s*\d*[:\-]|\[\d+\])\s*', re.I)
_TITLE_CLEAN_PREFIX = re.compile(r'^\s*(?:\d+[\.\)]|project\s*\d*[:\-]|\[\d+\])\s*', re.I)


def _normalize(text: str) -> str:
    # PDF text often puts several bullets on one line: force one bullet per line
    text = re.sub(r'[ \t]*([•●▪◦►])[ \t]*', r'\n\1 ', text)
    # " – " / " — " right after a sentence end or ")" is a bullet marker
    text = re.sub(r'(?<=[.!?)])[ \t]+([–—])[ \t]+', r'\n\1 ', text)
    return text


def _new_project(line: str) -> Dict[str, Any]:
    urls = extract_all_urls(line)
    clean = _LABELLED_URL.sub("", line)
    clean = _BARE_URL.sub("", clean)
    clean = re.sub(r'[§]+', '', clean)
    clean = _TITLE_CLEAN_PREFIX.sub("", clean)
    title, _, tech = clean.partition("|")
    title = title.strip(" -–—:,()\"'")
    return {
        "title": title or "Project",
        "raw_lines": [line],
        "bullets": [],
        "urls": list(urls),
        "_tech_text": tech,
    }


def _finish(p: Dict[str, Any]) -> Dict[str, Any]:
    text = " ".join([p["title"], p.pop("_tech_text", "")] + p["bullets"])
    p["technologies"] = sorted(set(extract_skills(text)))
    p["description"] = "\n".join(f"• {b}" for b in p["bullets"])
    p["urls"] = list(dict.fromkeys(p["urls"]))
    return p


def _is_explicit_title(line: str) -> bool:
    if _NUMBERED_PREFIX.match(line):
        return True
    if _LABELLED_URL.search(line):
        return True
    if " | " in line:
        return True
    return False


def extract_projects(resume_text: str, projects_section_text: str = "") -> List[Dict[str, Any]]:
    target = projects_section_text.strip() or resume_text
    lines = [l.strip() for l in _normalize(target).split("\n") if l.strip()]

    projects: List[Dict[str, Any]] = []
    cur = None

    def flush():
        nonlocal cur
        if cur and (cur["bullets"] or _tech_present(cur)):
            projects.append(_finish(cur))
        cur = None

    def _tech_present(p):
        return bool(p.get("_tech_text", "").strip())

    for line in lines:
        normalized_line = line.lower().strip(": ")
        if normalized_line in _ALL_SECTION_HEADERS:
            flush()
            continue

        m = _TECH_LINE.match(line)
        if m and cur is not None:
            cur["_tech_text"] += " " + m.group(1)
            cur["raw_lines"].append(line)
            continue

        if _BULLET_START.match(line):
            if cur is None:
                cur = _new_project("Project")
            cur["bullets"].append(_BULLET_START.sub("", line, count=1).strip())
            cur["urls"].extend(extract_all_urls(line))
            cur["raw_lines"].append(line)
            continue

        if _is_explicit_title(line):
            flush()
            cur = _new_project(line)
            continue

        # If cur is active and has bullets...
        if cur and cur["bullets"]:
            # If the last bullet doesn't end with sentence punctuation, it's a wrapped line continuation!
            if not _END_PUNCT.search(cur["bullets"][-1]):
                cur["bullets"][-1] += " " + line
                cur["raw_lines"].append(line)
                continue

        # If cur is active but has NO bullets yet, line is description/bullet for cur!
        if cur and not cur["bullets"]:
            cur["bullets"].append(line)
            cur["raw_lines"].append(line)
            continue

        # otherwise: a new project title
        flush()
        cur = _new_project(line)

    flush()

    # fallback: paragraphs
    if not projects and projects_section_text.strip():
        for i, para in enumerate(p.strip() for p in projects_section_text.split("\n\n") if p.strip()):
            first = para.split("\n")[0]
            proj = _new_project(first if len(first) > 3 else f"Project {i+1}")
            proj["bullets"] = [b.strip() for b in para.split("\n")[1:] if b.strip()] or [para]
            projects.append(_finish(proj))

    return projects
