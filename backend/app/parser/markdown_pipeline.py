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
    extract_linkedin_urls, extract_portfolio_urls, SECTION_HEADERS
)


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
            r'^((?:B\.?Tech|M\.?Tech|B\.?E\.?|M\.?E\.?|B\.?S\.?|M\.?S\.?|B\.?Sc|M\.?Sc|'
            r'Diploma|Bachelor(?:\'s)?|Master(?:\'s)?|Ph\.?D\.?)[^,]*)\s+(.+)$',
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
                degree_str = f"{degree} in {field}"
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
        skills.databases, skills.tools, skills.soft, skills.other
    ])
    if has_skills:
        lines.append("## Technical Skills")
        if skills.technical:
            lines.append(f"- **Programming Languages:** {', '.join(skills.technical)}")
        if skills.frameworks:
            lines.append(f"- **Frameworks & Libraries:** {', '.join(skills.frameworks)}")
        if skills.cloud:
            lines.append(f"- **Cloud & DevOps:** {', '.join(skills.cloud)}")
        if skills.databases:
            lines.append(f"- **Databases & Storage:** {', '.join(skills.databases)}")
        if skills.tools:
            lines.append(f"- **Developer Tools & Platforms:** {', '.join(skills.tools)}")
        if skills.soft:
            lines.append(f"- **Leadership & Soft Skills:** {', '.join(skills.soft)}")
        if skills.other:
            lines.append(f"- **Other Competencies:** {', '.join(skills.other)}")
        lines.append("")

    # 5. Key Projects (Priority for Freshers)
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

    # 6. Professional Experience & Internships (if applicable)
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
                sub_parts = [p.strip() for p in re.split(r'\s+[*•]\s+', clean_raw) if p.strip()]
                expanded_lines.extend(sub_parts if sub_parts else [clean_raw])

            for line in expanded_lines:
                clean = line.strip().lstrip("-*• ")
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
                if clean:
                    title_match = re.search(r'\*\*(.*?)\*\*', clean)
                    ach_title = title_match.group(1) if title_match else clean.split(":")[0].strip()
                    desc = clean.split(":", 1)[1].strip() if ":" in clean else ""
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
        for sec_name, keywords in SECTION_HEADERS.items():
            if clean_sec_cand in keywords or any(clean_sec_cand == kw for kw in keywords):
                matched_sec = sec_name
                break
        # Fuzzy fallback: check if any keyword is a substring of the heading
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
        if matched_sec:
            if stripped.startswith("## "):
                is_heading_line = True
            elif stripped.endswith(":") and len(stripped.split()) <= 5:
                is_heading_line = True
            elif stripped.isupper() and len(stripped.split()) <= 4:
                is_heading_line = True
            elif not stripped.startswith(("-", "*", "•", "–", "—", "#", "(")) and len(stripped.split()) <= 3:
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
            elif "### " not in markdown_text or current_section == "experience":
                has_sep = bool(re.search(r'\s*(?:—|–|\||\bat\b|@)\s*|(?<=\w)\s+-\s+(?=\w)', stripped, re.IGNORECASE))
                is_bold_header = stripped.startswith("**") and ("**" in stripped[2:])
                not_sentence = not stripped.rstrip().endswith((".", ";", ","))
                is_action_verb = bool(re.match(r'^(?:architected|developed|built|designed|implemented|spearheaded|created|managed|led|integrated|engineered|optimized|reduced|increased)\b', clean_stripped_lower))
                if (has_sep or is_bold_header) and not_sentence and not is_action_verb and len(stripped.split()) <= 15 and not clean_stripped_lower.startswith(("note:", "location:", "cgpa:", "gpa:", "tech:", "technologies:")):
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
            if current_sub_item and current_section == "projects":
                if not current_sub_item.get("description"):
                    current_sub_item["description"] = stripped
                else:
                    current_sub_item["description"] += f" {stripped}"
            elif current_sub_item and not current_sub_item.get("description"):
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
                    (s.get("flags", 0) & 2 != 0) or 
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

                    if (is_bold or line_max_size >= body_size + 0.4) and len(line_text.split()) <= 20:
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
