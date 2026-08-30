"""
Structured Resume Parser module for AI Resume ATS.
Extracts contact details, GitHub/Portfolio URLs, LinkedIn, and structural resume sections.
"""
import re
from typing import Dict, Any, List
from app.utils.skills import extract_skills
from app.utils.text_utils import extract_all_urls

EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
PHONE_REGEX = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
GITHUB_REGEX = r'(?:https?:\/\/)?(?:www\.)?github\.com\/[a-zA-Z0-9_-]+(?:\/[a-zA-Z0-9_\.-]+)?'
LINKEDIN_REGEX = r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[a-zA-Z0-9_\-\.]+'

SECTION_HEADERS = {
    "education": ["education", "academic background", "qualification", "qualifications", "academics"],
    "experience": ["experience", "work experience", "employment history", "professional experience", "internships", "work history"],
    "projects": ["projects", "personal projects", "academic projects", "key projects", "technical projects"],
    "skills": ["skills", "technical skills", "technologies", "core competencies", "skills & tools"],
    "certifications": ["certifications", "certificates", "courses", "licenses", "achievements"]
}

def extract_email(text: str) -> str:
    match = re.search(EMAIL_REGEX, text)
    return match.group(0) if match else "Not Found"

def extract_phone(text: str) -> str:
    match = re.search(PHONE_REGEX, text)
    return match.group(0) if match else "Not Found"

def extract_github_urls(text: str) -> List[str]:
    """Extract all GitHub profile and repository links."""
    matches = re.findall(GITHUB_REGEX, text, re.IGNORECASE)
    normalized = []
    for m in matches:
        url = m if m.startswith("http") else f"https://{m}"
        if url not in normalized:
            normalized.append(url)
    return normalized

def extract_linkedin_urls(text: str) -> List[str]:
    """Extract all LinkedIn profile links."""
    matches = re.findall(LINKEDIN_REGEX, text, re.IGNORECASE)
    normalized = []
    for m in matches:
        url = m if m.startswith("http") else f"https://{m}"
        if url not in normalized:
            normalized.append(url)
    return normalized

def extract_portfolio_urls(text: str) -> List[str]:
    """Extract personal portfolio / live demo website links (non-github, non-linkedin)."""
    all_urls = extract_all_urls(text)
    portfolios = []
    for url in all_urls:
        u_lower = url.lower()
        if "github.com" not in u_lower and "linkedin.com" not in u_lower and "twitter.com" not in u_lower:
            portfolios.append(url)
    return portfolios

def extract_candidate_name(text: str) -> str:
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        first_line = lines[0]
        # Heuristic: Candidate name is often on the first non-empty line if short
        if len(first_line.split()) <= 4 and not re.search(r'@|http|resume|curriculum|phone|\+?\d', first_line, re.IGNORECASE):
            return first_line.title()
    return "Candidate"

def parse_resume_sections(text: str) -> Dict[str, str]:
    """Segment resume into major sections based on standard section headings."""
    lines = text.split('\n')
    sections = {
        "education": "",
        "experience": "",
        "projects": "",
        "skills": "",
        "certifications": ""
    }
    
    current_section = None
    for line in lines:
        cleaned_line = line.strip().lower()
        matched_hdr = None
        for sec_name, keywords in SECTION_HEADERS.items():
            if any(cleaned_line == kw or cleaned_line.startswith(kw + ":") or cleaned_line.startswith(kw.upper()) for kw in keywords):
                matched_hdr = sec_name
                break
                
        if matched_hdr:
            current_section = matched_hdr
        elif current_section:
            sections[current_section] += line + "\n"
            
    return sections

def parse_resume(raw_text: str) -> Dict[str, Any]:
    """
    Parse raw resume text into structured components with links, LinkedIn, and sections.
    """
    email = extract_email(raw_text)
    phone = extract_phone(raw_text)
    name = extract_candidate_name(raw_text)
    skills = sorted(list(extract_skills(raw_text)))
    sections = parse_resume_sections(raw_text)
    github_urls = extract_github_urls(raw_text)
    linkedin_urls = extract_linkedin_urls(raw_text)
    portfolio_urls = extract_portfolio_urls(raw_text)
    
    return {
        "candidate_name": name,
        "email": email,
        "phone": phone,
        "extracted_skills": skills,
        "sections": sections,
        "github_urls": github_urls,
        "linkedin_urls": linkedin_urls,
        "portfolio_urls": portfolio_urls,
        "raw_text": raw_text
    }
