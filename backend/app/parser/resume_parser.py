"""
Structured Resume Parser module for AI Resume ATS.
Extracts contact details (Email, Phone, Name) and structural resume sections.
"""
import re
from typing import Dict, Any, List
from app.utils.skills import extract_skills

EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
PHONE_REGEX = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'

SECTION_HEADERS = {
    "education": ["education", "academic background", "qualification", "qualifications"],
    "experience": ["experience", "work experience", "employment history", "professional experience", "internships"],
    "projects": ["projects", "personal projects", "academic projects", "key projects"],
    "certifications": ["certifications", "certificates", "courses", "licenses"]
}

def extract_email(text: str) -> str:
    match = re.search(EMAIL_REGEX, text)
    return match.group(0) if match else "Not Found"

def extract_phone(text: str) -> str:
    match = re.search(PHONE_REGEX, text)
    return match.group(0) if match else "Not Found"

def extract_candidate_name(text: str) -> str:
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        first_line = lines[0]
        # Heuristic: Candidate name is often on the first non-empty line if short
        if len(first_line.split()) <= 4 and not re.search(r'@|http|resume|curriculum', first_line, re.IGNORECASE):
            return first_line.title()
    return "Candidate"

def parse_resume_sections(text: str) -> Dict[str, str]:
    """Segment resume into major sections based on standard section headings."""
    lines = text.split('\n')
    sections = {
        "education": "",
        "experience": "",
        "projects": "",
        "certifications": ""
    }
    
    current_section = None
    for line in lines:
        cleaned_line = line.strip().lower()
        # Check if line matches a header
        matched_hdr = None
        for sec_name, keywords in SECTION_HEADERS.items():
            if any(cleaned_line == kw or cleaned_line.startswith(kw + ":") for kw in keywords):
                matched_hdr = sec_name
                break
                
        if matched_hdr:
            current_section = matched_hdr
        elif current_section:
            sections[current_section] += line + "\n"
            
    return sections

def parse_resume(raw_text: str) -> Dict[str, Any]:
    """
    Parse raw resume text into structured components.
    """
    email = extract_email(raw_text)
    phone = extract_phone(raw_text)
    name = extract_candidate_name(raw_text)
    skills = sorted(list(extract_skills(raw_text)))
    sections = parse_resume_sections(raw_text)
    
    return {
        "candidate_name": name,
        "email": email,
        "phone": phone,
        "extracted_skills": skills,
        "sections": sections,
        "raw_text": raw_text
    }
