"""
Project Extractor module.
Extracts project entries, project names, descriptions, and linked repository URLs from resume text.
"""
import re
from typing import List, Dict, Any
from app.utils.skills import extract_skills
from app.utils.text_utils import extract_all_urls

def extract_projects(resume_text: str, projects_section_text: str = "") -> List[Dict[str, Any]]:
    """
    Extract individual project entries from the resume.
    """
    target_text = projects_section_text.strip() if projects_section_text.strip() else resume_text
    lines = target_text.split('\n')
    
    projects: List[Dict[str, Any]] = []
    current_project: Dict[str, Any] = {}
    
    # Project header regex patterns (e.g. "1. AI Resume ATS:", "Project: Smart Hospital", "AI Resume Screening System - ")
    project_header_pattern = re.compile(
        r'^(?:(?:\d+[\.\)]\s*)|(?:Project\s*[\d:]*\s*)|(?:•\s*))?([A-Za-z0-9\s\-_/&]+)(?:[:\-\|]|\s{2,})',
        re.IGNORECASE
    )
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        # Ignore generic headers
        if line_str.lower() in ["projects", "personal projects", "academic projects", "key projects"]:
            continue

        match = project_header_pattern.match(line_str)
        # Check if line looks like a project title (short line, ending with colon/dash, or starting with number)
        is_title = False
        title_candidate = ""
        
        if (line_str.startswith("1.") or line_str.startswith("2.") or line_str.startswith("3.") or 
            line_str.startswith("4.") or line_str.startswith("5.") or line_str.startswith("• Project") or
            ("project" in line_str.lower() and len(line_str.split()) <= 6)):
            is_title = True
            title_candidate = line_str.lstrip("1234567890.•- ")
        elif match and len(match.group(1).split()) <= 5 and not line_str.lower().startswith("built") and not line_str.lower().startswith("developed"):
            is_title = True
            title_candidate = match.group(1).strip()

        if is_title and title_candidate:
            if current_project and (current_project.get("description") or current_project.get("technologies")):
                projects.append(current_project)
                
            current_project = {
                "title": title_candidate.split(":")[0].split("-")[0].strip(),
                "raw_lines": [line_str],
                "description": line_str,
                "technologies": sorted(list(extract_skills(line_str))),
                "urls": extract_all_urls(line_str)
            }
        elif current_project:
            current_project["raw_lines"].append(line_str)
            current_project["description"] += " " + line_str
            current_project["technologies"] = sorted(list(set(current_project["technologies"]).union(extract_skills(line_str))))
            current_project["urls"].extend(extract_all_urls(line_str))

    if current_project and (current_project.get("description") or current_project.get("technologies")):
        projects.append(current_project)

    # If no structured projects detected by regex, fallback to section chunks
    if not projects and projects_section_text.strip():
        paragraphs = [p.strip() for p in projects_section_text.split('\n\n') if p.strip()]
        for i, p in enumerate(paragraphs):
            first_line = p.split('\n')[0]
            title = first_line[:40].strip()
            projects.append({
                "title": title if len(title) > 3 else f"Project {i+1}",
                "raw_lines": [p],
                "description": p,
                "technologies": sorted(list(extract_skills(p))),
                "urls": extract_all_urls(p)
            })

    return projects
