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
from app.utils.skills import extract_skills, SKILL_CATEGORIES, ALL_SKILLS
from app.parser.resume_parser import (
    extract_email, extract_phone, extract_github_urls,
    extract_linkedin_urls, extract_portfolio_urls, SECTION_HEADERS
)


def categorize_skill(skill: str) -> str:
    """Categorize a skill into technical, tools, cloud, databases, frameworks, or other."""
    skill_lower = skill.strip().lower()
    for cat_name, skill_list in SKILL_CATEGORIES.items():
        if skill_lower in [s.lower() for s in skill_list]:
            if "Cloud" in cat_name or "DevOps" in cat_name:
                return "cloud"
            elif "Databases" in cat_name:
                return "databases"
            elif "Frameworks" in cat_name:
                return "frameworks"
            elif "Programming Languages" in cat_name:
                return "technical"
            elif "AI" in cat_name or "Machine Learning" in cat_name:
                return "technical"
            elif "Methodologies" in cat_name:
                return "tools"
    return "other"


def build_categorized_skills(skills_list: List[str]) -> CategorizedSkills:
    """Group a flat list of skills into CategorizedSkills."""
    cat = CategorizedSkills()
    for s in skills_list:
        clean_s = s.strip()
        if not clean_s:
            continue
        group = categorize_skill(clean_s)
        target = getattr(cat, group, cat.other)
        # Format skill title
        formatted = clean_s if len(clean_s) <= 4 and clean_s.isupper() else clean_s.title()
        if formatted not in target:
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

    # 2. Professional Summary
    if resume.summary.strip():
        lines.append("## Professional Summary")
        lines.append(resume.summary.strip())
        lines.append("")

    # 3. Technical Skills
    skills = resume.skills
    has_skills = any([
        skills.technical, skills.frameworks, skills.cloud,
        skills.databases, skills.tools, skills.soft, skills.other
    ])
    if has_skills:
        lines.append("## Technical Skills")
        if skills.technical:
            lines.append(f"- **Languages & Core:** {', '.join(skills.technical)}")
        if skills.frameworks:
            lines.append(f"- **Frameworks & Libraries:** {', '.join(skills.frameworks)}")
        if skills.cloud:
            lines.append(f"- **Cloud & DevOps:** {', '.join(skills.cloud)}")
        if skills.databases:
            lines.append(f"- **Databases & Storage:** {', '.join(skills.databases)}")
        if skills.tools:
            lines.append(f"- **Tools & Platforms:** {', '.join(skills.tools)}")
        if skills.soft:
            lines.append(f"- **Leadership & Soft Skills:** {', '.join(skills.soft)}")
        if skills.other:
            lines.append(f"- **Other Competencies:** {', '.join(skills.other)}")
        lines.append("")

    # 4. Work Experience
    if resume.experience:
        lines.append("## Work Experience")
        for exp in resume.experience:
            role = exp.role.strip() or "Role"
            company = exp.company.strip() or "Company"
            dates = f"({exp.start_date} – {exp.end_date})" if exp.start_date or exp.end_date else ""
            lines.append(f"### {role} — {company} {dates}".strip())
            if exp.location.strip():
                lines.append(f"*{exp.location.strip()}*")
            for hl in exp.highlights:
                clean_hl = hl.strip().lstrip("•-* ")
                if clean_hl:
                    lines.append(f"- {clean_hl}")
            if exp.technologies:
                lines.append(f"*Technologies: {', '.join(exp.technologies)}*")
            lines.append("")

    # 5. Projects
    if resume.projects:
        lines.append("## Key Projects")
        for proj in resume.projects:
            name_header = f"### {proj.name.strip()}"
            link_tags = []
            if proj.github_url:
                link_tags.append(f"[Code]({proj.github_url})")
            if proj.live_url:
                link_tags.append(f"[Live Demo]({proj.live_url})")
            if link_tags:
                name_header += f" ({' | '.join(link_tags)})"
            lines.append(name_header)

            if proj.description.strip():
                lines.append(proj.description.strip())
            for hl in proj.highlights:
                clean_hl = hl.strip().lstrip("•-* ")
                if clean_hl:
                    lines.append(f"- {clean_hl}")
            if proj.technologies:
                lines.append(f"*Technologies: {', '.join(proj.technologies)}*")
            lines.append("")

    # 6. Education
    if resume.education:
        lines.append("## Education")
        for edu in resume.education:
            degree = edu.degree.strip()
            field = edu.field_of_study.strip()
            degree_str = f"{degree} in {field}".strip(" in ") if (degree or field) else "Degree"
            inst = edu.institution.strip() or "Institution"
            dates = f"({edu.start_date} – {edu.end_date})" if edu.start_date or edu.end_date else ""
            lines.append(f"### {degree_str} — {inst} {dates}".strip())
            extras = []
            if edu.gpa:
                extras.append(f"GPA: {edu.gpa}")
            if edu.honors:
                extras.append(f"Honors: {', '.join(edu.honors)}")
            if extras:
                lines.append(" | ".join(extras))
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

    # 8. Achievements
    if resume.achievements:
        lines.append("## Achievements & Honors")
        for ach in resume.achievements:
            date_str = f" ({ach.date})" if ach.date else ""
            desc_str = f": {ach.description}" if ach.description else ""
            lines.append(f"- **{ach.title}**{date_str}{desc_str}")
        lines.append("")

    # 9. Custom Sections
    for cs in resume.custom_sections:
        if cs.title.strip() and cs.items:
            lines.append(f"## {cs.title.strip()}")
            for item in cs.items:
                lines.append(f"- {item.strip().lstrip('•-* ')}")
            lines.append("")

    return "\n".join(lines).strip()


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

    def commit_sub_item(sec: str, item: Dict[str, Any]):
        if not item:
            return
        if sec == "experience":
            resume.experience.append(ExperienceItem(
                id=generate_id("exp"),
                company=item.get("company", ""),
                role=item.get("role", ""),
                location=item.get("location", ""),
                start_date=item.get("start_date", ""),
                end_date=item.get("end_date", ""),
                current="present" in item.get("end_date", "").lower(),
                highlights=item.get("highlights", []),
                technologies=item.get("technologies", [])
            ))
        elif sec == "projects":
            resume.projects.append(ProjectItem(
                id=generate_id("proj"),
                name=item.get("name", ""),
                description=item.get("description", ""),
                highlights=item.get("highlights", []),
                technologies=item.get("technologies", []),
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
        nonlocal current_section, current_sub_item, current_section_lines
        if not current_section:
            return

        if current_sub_item:
            commit_sub_item(current_section, current_sub_item)
            current_sub_item = None

        text_block = "\n".join(current_section_lines).strip()

        if current_section == "summary":
            resume.summary = text_block

        elif current_section == "skills":
            # Extract skills from bullets or comma lists
            found_skills = extract_skills(text_block)
            resume.skills = build_categorized_skills(list(found_skills))

        elif current_section == "certifications":
            for line in current_section_lines:
                clean = line.strip().lstrip("-*• ")
                if clean:
                    name_match = re.search(r'\*\*(.*?)\*\*', clean)
                    cert_name = name_match.group(1) if name_match else clean.split("—")[0].strip()
                    issuer = clean.split("—")[1].split("(")[0].strip() if "—" in clean else ""
                    resume.certifications.append(CertificationItem(
                        id=generate_id("cert"),
                        name=cert_name,
                        issuer=issuer
                    ))

        elif current_section == "achievements":
            for line in current_section_lines:
                clean = line.strip().lstrip("-*• ")
                if clean:
                    title_match = re.search(r'\*\*(.*?)\*\*', clean)
                    ach_title = title_match.group(1) if title_match else clean.split(":")[0].strip()
                    desc = clean.split(":", 1)[1].strip() if ":" in clean else ""
                    resume.achievements.append(AchievementItem(
                        id=generate_id("ach"),
                        title=ach_title,
                        description=desc
                    ))

        current_section_lines = []

    # Ensure name extraction fallback
    from app.parser.resume_parser import extract_candidate_name
    detected_cand_name = extract_candidate_name(markdown_text)
    if detected_cand_name and detected_cand_name != "Candidate":
        resume.profile.name = detected_cand_name

    def is_date_str(s: str) -> bool:
        clean = s.strip("() ")
        has_year = bool(re.search(r'\b(?:\d{4}|present|current)\b', clean, re.IGNORECASE))
        has_sep = bool(re.search(r'[-–—\ufffd/]|to', clean, re.IGNORECASE))
        return has_year and (has_sep or "present" in clean.lower()) and len(clean.split()) <= 6

    def extract_dates(s: str) -> Tuple[str, str]:
        clean = s.strip("() ")
        dates = [d.strip() for d in re.split(r'[-–—\ufffd/]+|\bto\b', clean, flags=re.IGNORECASE) if d.strip()]
        start = dates[0] if len(dates) > 0 else ""
        end = dates[1] if len(dates) > 1 else ""
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
        # Match '## Section', 'SECTION:', 'SECTION', or recognized keywords
        clean_sec_cand = re.sub(r'^[#\s*]+', '', stripped).rstrip(':* ').strip().lower()
        matched_sec = None
        for sec_name, keywords in SECTION_HEADERS.items():
            if clean_sec_cand in keywords or any(clean_sec_cand == kw for kw in keywords):
                matched_sec = sec_name
                break
        if not matched_sec:
            if any(clean_sec_cand == kw for kw in ["summary", "about", "bio", "profile", "professional summary", "career objective", "objective"]):
                matched_sec = "summary"
            elif any(clean_sec_cand == kw for kw in ["achievement", "achievements", "awards", "honors"]):
                matched_sec = "achievements"

        is_heading_line = False
        if matched_sec:
            if stripped.startswith("## "):
                is_heading_line = True
            elif stripped.endswith(":") and len(stripped.split()) <= 5:
                is_heading_line = True
            elif stripped.isupper() and len(stripped.split()) <= 4:
                is_heading_line = True
            elif not stripped.startswith(("-", "*", "•", "–", "—", "#", "(")) and len(stripped.split()) <= 3:
                is_heading_line = True

        if is_heading_line:
            commit_section()
            current_section = matched_sec
            continue

        # Bullet point detection: starts with -, *, •, –, —, or bullet symbols
        is_bullet = bool(re.match(r'^[•\-\*\–\—\u2022]\s*', stripped) or re.match(r'^\d+[\.\)]\s+', stripped))
        if is_bullet:
            bullet_text = re.sub(r'^[•\-\*\–\—\u2022\d\.\)\s]+', '', stripped).strip()
            if current_section in ("experience", "projects", "education"):
                if not current_sub_item:
                    current_sub_item = {"highlights": [], "technologies": []}
                current_sub_item["highlights"].append(bullet_text)
            elif current_section:
                current_section_lines.append(bullet_text)
            continue

        # Date line detection within experience/projects/education
        if current_section in ("experience", "projects", "education") and is_date_str(stripped):
            if current_sub_item:
                s_date, e_date = extract_dates(stripped)
                if not current_sub_item.get("start_date"):
                    current_sub_item["start_date"] = s_date
                if not current_sub_item.get("end_date"):
                    current_sub_item["end_date"] = e_date
                continue

        # Sub-item header detection (e.g. ### Role — Company, or Role — Company line, or Project Name)
        is_sub_header = stripped.startswith("### ")
        if not is_sub_header and current_section in ("experience", "projects", "education"):
            if len(stripped.split()) <= 15 and not stripped.lower().startswith(("technologies:", "gpa:", "note:", "location:")):
                is_sub_header = True

        if is_sub_header:
            if current_sub_item and current_section:
                commit_sub_item(current_section, current_sub_item)
                current_sub_item = None

            sub_title = stripped[4:].strip() if stripped.startswith("### ") else stripped

            current_sub_item = {
                "highlights": [],
                "technologies": []
            }

            # Dates pattern in parentheses: extract any parenthesized text containing years or 'present'
            date_match = re.search(r'\(([^)]*(?:\d{4}|present)[^)]*)\)', sub_title, re.IGNORECASE)
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
                # Split role and company using — , – , - , | , at , @
                parts = [p.strip() for p in re.split(r'\s*(?:—|–|\||\bat\b|@)\s*|(?<=\w)\s+-\s+(?=\w)', sub_clean, flags=re.IGNORECASE) if p.strip()]
                if len(parts) >= 2:
                    current_sub_item["role"] = parts[0]
                    current_sub_item["company"] = parts[1]
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

                parts = [p.strip() for p in re.split(r'\s*(?:—|–|\|)\s*', sub_clean) if p.strip()]
                current_sub_item["name"] = parts[0]
                if len(parts) > 1:
                    current_sub_item["description"] = parts[1]

            elif current_section == "education":
                parts = [p.strip() for p in re.split(r'[\s]*[-–—|@\ufffd][\s]*', sub_clean) if p.strip()]
                if len(parts) >= 2:
                    deg_part = parts[0].strip()
                    if " in " in deg_part:
                        deg_split = deg_part.split(" in ")
                        current_sub_item["degree"] = deg_split[0].strip()
                        current_sub_item["field_of_study"] = deg_split[1].strip()
                    else:
                        current_sub_item["degree"] = deg_part
                    current_sub_item["institution"] = parts[1].strip()
                else:
                    current_sub_item["institution"] = sub_title
            continue

        # Technologies line
        if stripped.lower().startswith("*technologies:") or stripped.lower().startswith("technologies:"):
            tech_text = re.sub(r'^\*?technologies:\*?\s*', '', stripped, flags=re.IGNORECASE).strip(" *")
            tech_list = [t.strip() for t in tech_text.split(",") if t.strip()]
            if current_sub_item:
                current_sub_item["technologies"] = tech_list
        elif stripped.lower().startswith("gpa:") or "gpa:" in stripped.lower():
            gpa_match = re.search(r'gpa:\s*([0-9\.\/]+)', stripped, re.IGNORECASE)
            if gpa_match and current_sub_item:
                current_sub_item["gpa"] = gpa_match.group(1).strip()
            if "honors:" in stripped.lower() and current_sub_item:
                honors_part = re.search(r'honors?:\s*(.*)', stripped, re.IGNORECASE)
                if honors_part:
                    current_sub_item["honors"] = [h.strip() for h in honors_part.group(1).split(",") if h.strip()]
        elif stripped:
            if current_sub_item and not current_sub_item.get("description"):
                current_sub_item["description"] = stripped
            elif current_section:
                current_section_lines.append(stripped)

    # Commit any trailing section
    commit_section()

    # Fallback skill extraction if skills section wasn't explicitly structured
    if not resume.skills.all_skills():
        raw_skills = extract_skills(markdown_text)
        resume.skills = build_categorized_skills(list(raw_skills))

    return resume


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
