"""
27-Check Resume Quality Engine.
Evaluates a Canonical Resume JSON across six audit dimensions:
  1. ATS Essentials (5 checks)     — Machine parseability and format compliance
  2. Structure (5 checks)          — Section completeness and ordering
  3. Content (6 checks)            — Bullet quality, depth, and specificity
  4. Tailoring (4 checks)          — JD keyword alignment and relevance signals
  5. Credibility (4 checks)        — Evidence, links, and verifiability
  6. Career Progression (3 checks) — Title trajectory, tenure, and growth signals

Each check returns: PASS | WARNING | FAIL + a human-readable explanation.
"""
import re
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


class CheckStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass
class QualityCheck:
    id: str
    category: str
    name: str
    status: CheckStatus
    explanation: str
    recommendation: Optional[str] = None
    score_impact: float = 0.0  # Positive = bonus, negative = penalty


@dataclass
class QualityReport:
    overall_score: float
    grade: str
    checks: List[QualityCheck] = field(default_factory=list)
    pass_count: int = 0
    warning_count: int = 0
    fail_count: int = 0
    summary: str = ""
    top_actions: List[str] = field(default_factory=list)


def _count_words(text: str) -> int:
    return len(text.split()) if text.strip() else 0


def _has_quantification(text: str) -> bool:
    return bool(re.search(
        r'\d+[%$kKmMbB]?|\$\d+|\d+\s*(?:users|requests|ms|seconds|hours|days|percent|%|million|billion|thousand)',
        text, re.IGNORECASE
    ))


def _starts_with_weak_verb(bullet: str) -> bool:
    WEAK_OPENERS = {
        "worked", "helped", "assisted", "was responsible", "did", "made",
        "handled", "participated", "involved", "contributed", "supported"
    }
    first_word = bullet.strip().split()[0].lower() if bullet.strip() else ""
    return first_word in WEAK_OPENERS or bullet.lower().startswith("was responsible")


def _has_action_verb(bullet: str) -> bool:
    ACTION_VERBS = {
        "architected", "engineered", "developed", "implemented", "designed",
        "optimized", "automated", "deployed", "migrated", "refactored",
        "championed", "spearheaded", "led", "mentored", "directed",
        "analyzed", "modeled", "forecasted", "launched", "shipped",
        "delivered", "reduced", "increased", "generated", "drove",
        "enabled", "transformed", "scaled", "built", "created",
        "established", "initiated", "resolved", "integrated", "streamlined"
    }
    first_word = bullet.strip().split()[0].lower() if bullet.strip() else ""
    return first_word in ACTION_VERBS


# ── Category 1: ATS Essentials ────────────────────────────────────────────────

def check_contact_completeness(resume: Dict[str, Any]) -> QualityCheck:
    """Check 1: Contact information completeness."""
    profile = resume.get("profile", {})
    name = profile.get("name", "").strip()
    email = profile.get("email", "").strip()
    phone = profile.get("phone", "").strip()
    location = profile.get("location", "").strip()

    missing = []
    if not name or name.lower() == "not found":
        missing.append("full name")
    if not email or email.lower() == "not found":
        missing.append("email address")
    if not phone or phone.lower() == "not found":
        missing.append("phone number")

    if not missing:
        status, expl, score = CheckStatus.PASS, "All essential contact fields are present.", 5.0
        rec = None
    elif len(missing) == 1:
        status, expl, score = CheckStatus.WARNING, f"Missing: {missing[0]}.", -2.0
        rec = f"Add your {missing[0]} to ensure recruiters can reach you."
    else:
        status, expl, score = CheckStatus.FAIL, f"Missing critical contact info: {', '.join(missing)}.", -8.0
        rec = "Your resume must include name, email, and phone number."

    return QualityCheck("ats_01", "ATS Essentials", "Contact Completeness", status, expl, rec, score)


def check_email_format(resume: Dict[str, Any]) -> QualityCheck:
    """Check 2: Email address format validity."""
    email = resume.get("profile", {}).get("email", "").strip()
    email_re = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not email or email.lower() == "not found":
        return QualityCheck("ats_02", "ATS Essentials", "Email Format",
                            CheckStatus.FAIL, "No email address detected.", "Add a professional email address.", -5.0)

    if re.match(email_re, email):
        return QualityCheck("ats_02", "ATS Essentials", "Email Format",
                            CheckStatus.PASS, f"Email '{email}' is properly formatted.", None, 3.0)

    return QualityCheck("ats_02", "ATS Essentials", "Email Format",
                        CheckStatus.WARNING, f"Email '{email}' may not be correctly formatted.",
                        "Verify your email address format.", -3.0)


def check_no_tables_or_graphics(resume: Dict[str, Any]) -> QualityCheck:
    """Check 3: ATS parseability — no graphics/table dependency."""
    # We infer this from the parsing warnings and markdown quality
    warnings = resume.get("_parsing_warnings", [])
    has_table_warning = any("table" in w.lower() or "graphic" in w.lower() or "column" in w.lower() for w in warnings)

    if has_table_warning:
        return QualityCheck("ats_03", "ATS Essentials", "ATS Parseability",
                            CheckStatus.WARNING,
                            "Possible multi-column or graphical layout detected — some ATS systems may misparse this.",
                            "Use a single-column plain layout for maximum ATS compatibility.", -5.0)
    return QualityCheck("ats_03", "ATS Essentials", "ATS Parseability",
                        CheckStatus.PASS, "Resume appears to use a standard text layout parseable by ATS.", None, 4.0)


def check_resume_length(resume: Dict[str, Any]) -> QualityCheck:
    """Check 4: Resume length appropriateness."""
    experience = resume.get("experience", [])
    all_text = []
    for exp in experience:
        all_text.extend(exp.get("bullets", []))

    total_bullets = len(all_text)
    total_sections = sum(1 for s in ["experience", "education", "skills", "projects", "certifications"]
                         if resume.get(s))

    if total_bullets > 25:
        return QualityCheck("ats_04", "ATS Essentials", "Resume Length",
                            CheckStatus.WARNING,
                            f"Resume has {total_bullets} bullet points — may exceed 2-page limit.",
                            "Target 3–5 impactful bullets per role. Remove older/irrelevant bullets.", -3.0)
    elif total_bullets < 3 and len(experience) > 0:
        return QualityCheck("ats_04", "ATS Essentials", "Resume Length",
                            CheckStatus.WARNING,
                            "Very few bullets detected — resume may appear sparse.",
                            "Add 3–5 achievement-focused bullets per relevant role.", -4.0)

    return QualityCheck("ats_04", "ATS Essentials", "Resume Length",
                        CheckStatus.PASS, f"Resume length is appropriate ({total_bullets} bullets, {total_sections} sections).", None, 3.0)


def check_section_headers(resume: Dict[str, Any]) -> QualityCheck:
    """Check 5: Standard section headers present."""
    present = []
    missing = []
    for section in ["experience", "education", "skills"]:
        if resume.get(section) and len(resume[section]) > 0:
            present.append(section)
        else:
            missing.append(section)

    if not missing:
        return QualityCheck("ats_05", "ATS Essentials", "Standard Section Headers",
                            CheckStatus.PASS, f"All core sections present: {', '.join(present)}.", None, 5.0)
    return QualityCheck("ats_05", "ATS Essentials", "Standard Section Headers",
                        CheckStatus.WARNING,
                        f"Missing standard sections: {', '.join(missing)}.",
                        f"Add {', '.join(missing)} section(s) for complete ATS coverage.", -4.0)


# ── Category 2: Structure ─────────────────────────────────────────────────────

def check_summary_quality(resume: Dict[str, Any]) -> QualityCheck:
    """Check 6: Professional summary — length and quality."""
    summary = resume.get("profile", {}).get("summary", "").strip()

    if not summary:
        return QualityCheck("str_01", "Structure", "Professional Summary",
                            CheckStatus.WARNING, "No professional summary detected.",
                            "Add a 2–4 sentence summary highlighting your value proposition and expertise.", -3.0)

    word_count = _count_words(summary)
    if word_count < 20:
        return QualityCheck("str_01", "Structure", "Professional Summary",
                            CheckStatus.WARNING, f"Summary is too short ({word_count} words).",
                            "Expand to 40–80 words covering your role, experience, and key value.", -2.0)
    if word_count > 120:
        return QualityCheck("str_01", "Structure", "Professional Summary",
                            CheckStatus.WARNING, f"Summary is too long ({word_count} words).",
                            "Tighten to 40–80 words. Recruiters skim summaries.", -1.0)

    return QualityCheck("str_01", "Structure", "Professional Summary",
                        CheckStatus.PASS, f"Summary is well-sized ({word_count} words).", None, 4.0)


def check_experience_dates(resume: Dict[str, Any]) -> QualityCheck:
    """Check 7: Work experience date completeness."""
    experience = resume.get("experience", [])
    if not experience:
        return QualityCheck("str_02", "Structure", "Experience Dates",
                            CheckStatus.WARNING, "No work experience entries detected.", None, -5.0)

    missing_dates = []
    for exp in experience:
        if not exp.get("duration", "").strip() and not exp.get("start_date", "").strip():
            missing_dates.append(exp.get("company", exp.get("title", "Unknown")))

    if missing_dates:
        return QualityCheck("str_02", "Structure", "Experience Dates",
                            CheckStatus.WARNING,
                            f"Missing dates for: {', '.join(missing_dates[:3])}.",
                            "Add start/end dates for all experience entries.", -3.0)

    return QualityCheck("str_02", "Structure", "Experience Dates",
                        CheckStatus.PASS, "All experience entries include date ranges.", None, 4.0)


def check_skills_categorization(resume: Dict[str, Any]) -> QualityCheck:
    """Check 8: Skills section presence and organization."""
    skills_groups = resume.get("skills", [])
    total_skills = sum(len(g.get("skills", [])) for g in skills_groups)

    if total_skills == 0:
        return QualityCheck("str_03", "Structure", "Skills Section",
                            CheckStatus.FAIL, "No skills section detected.",
                            "Add a categorized skills section (Languages, Frameworks, Tools, etc.).", -8.0)
    elif total_skills < 5:
        return QualityCheck("str_03", "Structure", "Skills Section",
                            CheckStatus.WARNING, f"Only {total_skills} skills listed — sparse.",
                            "List 10–25 relevant technical and soft skills.", -3.0)

    return QualityCheck("str_03", "Structure", "Skills Section",
                        CheckStatus.PASS, f"Skills section has {total_skills} skills across {len(skills_groups)} categories.", None, 5.0)


def check_education_completeness(resume: Dict[str, Any]) -> QualityCheck:
    """Check 9: Education section presence and detail."""
    education = resume.get("education", [])
    if not education:
        return QualityCheck("str_04", "Structure", "Education Section",
                            CheckStatus.WARNING, "No education entries detected.",
                            "Add your highest degree with institution and graduation year.", -3.0)

    missing_year = [e for e in education if not e.get("year", "").strip() and not e.get("duration", "").strip()]
    if missing_year:
        return QualityCheck("str_04", "Structure", "Education Section",
                            CheckStatus.WARNING, "Some education entries are missing graduation year.",
                            "Include graduation year for all degrees.", -1.0)

    return QualityCheck("str_04", "Structure", "Education Section",
                        CheckStatus.PASS, f"Education section has {len(education)} entr{'y' if len(education)==1 else 'ies'} with dates.", None, 3.0)


def check_projects_presence(resume: Dict[str, Any]) -> QualityCheck:
    """Check 10: Projects section for technical candidates."""
    projects = resume.get("projects", [])
    has_github = bool(resume.get("profile", {}).get("github_url", ""))

    if not projects and not has_github:
        return QualityCheck("str_05", "Structure", "Projects Section",
                            CheckStatus.WARNING,
                            "No projects section or GitHub profile detected.",
                            "Add 2–3 key projects with tech stack and measurable outcomes.", -3.0)
    if not projects and has_github:
        return QualityCheck("str_05", "Structure", "Projects Section",
                            CheckStatus.PASS,
                            "GitHub profile is linked — projects are externally verifiable.", None, 3.0)

    return QualityCheck("str_05", "Structure", "Projects Section",
                        CheckStatus.PASS, f"{len(projects)} project(s) listed.", None, 4.0)


# ── Category 3: Content ───────────────────────────────────────────────────────

def check_bullet_action_verbs(resume: Dict[str, Any]) -> QualityCheck:
    """Check 11: Percentage of bullets starting with strong action verbs."""
    all_bullets = []
    for exp in resume.get("experience", []):
        all_bullets.extend(exp.get("bullets", []))
    for proj in resume.get("projects", []):
        all_bullets.extend(proj.get("bullets", []) if isinstance(proj.get("bullets"), list) else [])

    if not all_bullets:
        return QualityCheck("cnt_01", "Content", "Action Verb Usage",
                            CheckStatus.FAIL, "No bullet points detected.", "Add achievement-focused bullets to your experience.", -8.0)

    strong_count = sum(1 for b in all_bullets if _has_action_verb(b))
    pct = strong_count / len(all_bullets) * 100

    if pct >= 75:
        return QualityCheck("cnt_01", "Content", "Action Verb Usage",
                            CheckStatus.PASS, f"{pct:.0f}% of bullets use strong action verbs.", None, 6.0)
    if pct >= 40:
        return QualityCheck("cnt_01", "Content", "Action Verb Usage",
                            CheckStatus.WARNING, f"Only {pct:.0f}% of bullets start with action verbs.",
                            "Use the AI Action-Verb Booster to strengthen remaining bullets.", -3.0)
    return QualityCheck("cnt_01", "Content", "Action Verb Usage",
                        CheckStatus.FAIL, f"Only {pct:.0f}% of bullets use action verbs — most bullets are weak.",
                        "Apply Action-Verb mode to all bullets via the AI toolbar.", -6.0)


def check_bullet_quantification(resume: Dict[str, Any]) -> QualityCheck:
    """Check 12: Percentage of bullets containing quantifiable achievements."""
    all_bullets = []
    for exp in resume.get("experience", []):
        all_bullets.extend(exp.get("bullets", []))

    if not all_bullets:
        return QualityCheck("cnt_02", "Content", "Quantified Achievements",
                            CheckStatus.FAIL, "No experience bullets to evaluate.", None, -5.0)

    quantified = sum(1 for b in all_bullets if _has_quantification(b))
    pct = quantified / len(all_bullets) * 100

    if pct >= 50:
        return QualityCheck("cnt_02", "Content", "Quantified Achievements",
                            CheckStatus.PASS, f"{pct:.0f}% of bullets contain metrics or percentages.", None, 7.0)
    if pct >= 25:
        return QualityCheck("cnt_02", "Content", "Quantified Achievements",
                            CheckStatus.WARNING, f"Only {pct:.0f}% of bullets are quantified.",
                            "Target: at least 1–2 bullets with real numbers per role. Use STAR Metric mode.", -3.0)
    return QualityCheck("cnt_02", "Content", "Quantified Achievements",
                        CheckStatus.FAIL, f"Only {pct:.0f}% of bullets have quantifiable results.",
                        "Apply STAR Metric mode to add impact numbers to your bullets.", -7.0)


def check_bullet_length(resume: Dict[str, Any]) -> QualityCheck:
    """Check 13: Bullet point length — too long or too short."""
    all_bullets = []
    for exp in resume.get("experience", []):
        all_bullets.extend(exp.get("bullets", []))

    if not all_bullets:
        return QualityCheck("cnt_03", "Content", "Bullet Length",
                            CheckStatus.WARNING, "No bullets to evaluate.", None, -2.0)

    too_short = [b for b in all_bullets if _count_words(b) < 8]
    too_long = [b for b in all_bullets if _count_words(b) > 30]
    ideal = len(all_bullets) - len(too_short) - len(too_long)

    if len(too_short) == 0 and len(too_long) == 0:
        return QualityCheck("cnt_03", "Content", "Bullet Length",
                            CheckStatus.PASS, f"All {len(all_bullets)} bullets are within ideal length (8–30 words).", None, 4.0)

    issues = []
    score = 0.0
    if too_short:
        issues.append(f"{len(too_short)} too short (<8 words)")
        score -= 2.0
    if too_long:
        issues.append(f"{len(too_long)} too long (>30 words)")
        score -= 2.0

    return QualityCheck("cnt_03", "Content", "Bullet Length",
                        CheckStatus.WARNING, f"Length issues: {', '.join(issues)}.",
                        "Keep bullets 10–20 words. Short = vague; long = unfocused.", score)


def check_no_personal_pronouns(resume: Dict[str, Any]) -> QualityCheck:
    """Check 14: Bullet points should not use first-person pronouns."""
    all_bullets = []
    for exp in resume.get("experience", []):
        all_bullets.extend(exp.get("bullets", []))

    pronoun_bullets = [b for b in all_bullets if re.search(r'\bI\b|\bme\b|\bmy\b|\bwe\b|\bour\b', b)]
    if not pronoun_bullets:
        return QualityCheck("cnt_04", "Content", "No Personal Pronouns",
                            CheckStatus.PASS, "No personal pronouns found in bullets.", None, 3.0)

    return QualityCheck("cnt_04", "Content", "No Personal Pronouns",
                        CheckStatus.WARNING, f"{len(pronoun_bullets)} bullets contain personal pronouns (I/me/we/our).",
                        "Remove pronouns — start directly with the action verb. Use Polish mode.", -3.0)


def check_consistency(resume: Dict[str, Any]) -> QualityCheck:
    """Check 15: Tense consistency in bullets (past tense for past roles)."""
    experience = resume.get("experience", [])
    if not experience:
        return QualityCheck("cnt_05", "Content", "Tense Consistency",
                            CheckStatus.WARNING, "No experience to check for tense consistency.", None, 0.0)

    present_tense_in_past = 0
    for exp in experience:
        duration = exp.get("duration", "").lower()
        is_past = "present" not in duration and "current" not in duration
        bullets = exp.get("bullets", [])
        for b in bullets:
            first_word = b.strip().split()[0].lower() if b.strip() else ""
            present_verbs = {"build", "develop", "design", "create", "manage", "lead", "work", "handle"}
            if is_past and first_word in present_verbs:
                present_tense_in_past += 1

    if present_tense_in_past == 0:
        return QualityCheck("cnt_05", "Content", "Tense Consistency",
                            CheckStatus.PASS, "Verb tense appears consistent across roles.", None, 3.0)

    return QualityCheck("cnt_05", "Content", "Tense Consistency",
                        CheckStatus.WARNING,
                        f"{present_tense_in_past} bullets in past roles use present tense.",
                        "Past roles should use past tense (Developed, Led, Built). Use Polish mode to correct.", -2.0)


def check_content_depth(resume: Dict[str, Any]) -> QualityCheck:
    """Check 16: Overall content depth and technical specificity."""
    all_bullets = []
    for exp in resume.get("experience", []):
        all_bullets.extend(exp.get("bullets", []))

    if not all_bullets:
        return QualityCheck("cnt_06", "Content", "Content Depth",
                            CheckStatus.FAIL, "No experience content to evaluate.", None, -5.0)

    # Check for tech specificity: mentions of actual tool/tech names
    tech_pattern = re.compile(
        r'\b(?:Python|Java|React|Node|Docker|Kubernetes|AWS|GCP|Azure|SQL|NoSQL|GraphQL|REST|API|'
        r'TensorFlow|PyTorch|Spark|Kafka|Redis|PostgreSQL|MongoDB|Git|CI/CD|Jenkins|'
        r'TypeScript|JavaScript|Go|Rust|Scala|C\+\+|C#|Swift|Kotlin|Ruby)\b',
        re.IGNORECASE
    )
    tech_bullets = [b for b in all_bullets if tech_pattern.search(b)]
    tech_pct = len(tech_bullets) / len(all_bullets) * 100

    if tech_pct >= 30:
        return QualityCheck("cnt_06", "Content", "Content Depth",
                            CheckStatus.PASS, f"{tech_pct:.0f}% of bullets reference specific technologies.", None, 5.0)
    if tech_pct >= 10:
        return QualityCheck("cnt_06", "Content", "Content Depth",
                            CheckStatus.WARNING, f"Only {tech_pct:.0f}% of bullets mention specific tools/technologies.",
                            "Add specific technology names, frameworks, and methodologies.", -2.0)

    return QualityCheck("cnt_06", "Content", "Content Depth",
                        CheckStatus.FAIL, f"Bullets lack technical specificity ({tech_pct:.0f}% name tech).",
                        "Be explicit: name programming languages, frameworks, databases, and tools.", -5.0)


# ── Category 4: Tailoring ─────────────────────────────────────────────────────

def check_title_alignment(resume: Dict[str, Any], target_title: Optional[str] = None) -> QualityCheck:
    """Check 17: Resume title/role alignment with target position."""
    if not target_title:
        return QualityCheck("tai_01", "Tailoring", "Target Role Alignment",
                            CheckStatus.WARNING, "No target job title provided for alignment check.",
                            "Provide a job description to enable tailoring checks.", 0.0)

    profile = resume.get("profile", {})
    title = profile.get("title", "").lower()
    target_lower = target_title.lower()
    target_words = set(target_lower.split()) - {"senior", "junior", "lead", "staff", "principal", "the", "and", "or"}

    if any(w in title for w in target_words):
        return QualityCheck("tai_01", "Tailoring", "Target Role Alignment",
                            CheckStatus.PASS, f"Resume title aligns with target role '{target_title}'.", None, 5.0)

    return QualityCheck("tai_01", "Tailoring", "Target Role Alignment",
                        CheckStatus.WARNING, f"Resume title '{title}' does not clearly align with '{target_title}'.",
                        "Update your title or summary to reflect the target role.", -3.0)


def check_keyword_coverage(resume: Dict[str, Any], jd_keywords: Optional[List[str]] = None) -> QualityCheck:
    """Check 18: JD keyword coverage in resume text."""
    if not jd_keywords:
        return QualityCheck("tai_02", "Tailoring", "JD Keyword Coverage",
                            CheckStatus.WARNING, "No job description keywords provided for keyword check.", None, 0.0)

    resume_text = " ".join([
        resume.get("profile", {}).get("summary", ""),
        *[b for exp in resume.get("experience", []) for b in exp.get("bullets", [])],
        *[" ".join(g.get("skills", [])) for g in resume.get("skills", [])]
    ]).lower()

    matched = [kw for kw in jd_keywords if kw.lower() in resume_text]
    coverage = len(matched) / len(jd_keywords) * 100 if jd_keywords else 0.0

    if coverage >= 60:
        return QualityCheck("tai_02", "Tailoring", "JD Keyword Coverage",
                            CheckStatus.PASS, f"{coverage:.0f}% of JD keywords are present in the resume.", None, 7.0)
    if coverage >= 30:
        return QualityCheck("tai_02", "Tailoring", "JD Keyword Coverage",
                            CheckStatus.WARNING, f"Only {coverage:.0f}% of JD keywords covered.",
                            "Use JD Keyword Injector or Tailor Resume to improve coverage.", -3.0)
    return QualityCheck("tai_02", "Tailoring", "JD Keyword Coverage",
                        CheckStatus.FAIL, f"Low keyword coverage: {coverage:.0f}%.",
                        "Run Tailor Resume to automatically inject relevant JD keywords.", -6.0)


def check_custom_summary(resume: Dict[str, Any], jd_text: Optional[str] = None) -> QualityCheck:
    """Check 19: Is the summary tailored to the JD?"""
    summary = resume.get("profile", {}).get("summary", "").lower()
    if not summary:
        return QualityCheck("tai_03", "Tailoring", "Tailored Summary",
                            CheckStatus.FAIL, "No summary to check for JD tailoring.", None, -4.0)

    if not jd_text:
        return QualityCheck("tai_03", "Tailoring", "Tailored Summary",
                            CheckStatus.WARNING, "Summary exists but no JD provided for tailoring verification.", None, 1.0)

    jd_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', jd_text.lower()))
    summary_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', summary))
    overlap = len(jd_words.intersection(summary_words))

    if overlap >= 5:
        return QualityCheck("tai_03", "Tailoring", "Tailored Summary",
                            CheckStatus.PASS, f"Summary shows {overlap} shared terms with the JD — well tailored.", None, 5.0)
    return QualityCheck("tai_03", "Tailoring", "Tailored Summary",
                        CheckStatus.WARNING, f"Summary shares only {overlap} terms with the JD.",
                        "Update your summary to reflect the specific role and company context.", -2.0)


def check_no_generic_phrases(resume: Dict[str, Any]) -> QualityCheck:
    """Check 20: Detect and flag overused generic phrases."""
    GENERIC = [
        "team player", "hard worker", "fast learner", "detail-oriented",
        "self-starter", "go-getter", "results-driven", "dynamic", "synergy",
        "leverage", "passionate about", "strong communication skills",
        "able to work independently", "proven track record",
        "excellent communication", "out-of-the-box"
    ]
    all_text = (
        resume.get("profile", {}).get("summary", "") + " " +
        " ".join(b for exp in resume.get("experience", []) for b in exp.get("bullets", []))
    ).lower()

    found = [phrase for phrase in GENERIC if phrase in all_text]
    if not found:
        return QualityCheck("tai_04", "Tailoring", "No Generic Phrases",
                            CheckStatus.PASS, "No overused generic phrases detected.", None, 4.0)

    return QualityCheck("tai_04", "Tailoring", "No Generic Phrases",
                        CheckStatus.WARNING, f"Generic phrases detected: {', '.join(found[:4])}.",
                        "Replace generic phrases with specific, evidence-backed statements.", -4.0)


# ── Category 5: Credibility ───────────────────────────────────────────────────

def check_github_presence(resume: Dict[str, Any]) -> QualityCheck:
    """Check 21: GitHub profile presence for technical roles."""
    github = resume.get("profile", {}).get("github_url", "").strip()
    if github and "github.com" in github.lower():
        return QualityCheck("crd_01", "Credibility", "GitHub Profile",
                            CheckStatus.PASS, f"GitHub profile linked: {github}", None, 5.0)
    return QualityCheck("crd_01", "Credibility", "GitHub Profile",
                        CheckStatus.WARNING, "No GitHub profile linked.",
                        "Add your GitHub profile URL to provide verifiable project evidence.", -3.0)


def check_linkedin_presence(resume: Dict[str, Any]) -> QualityCheck:
    """Check 22: LinkedIn profile presence."""
    linkedin = resume.get("profile", {}).get("linkedin_url", "").strip()
    if linkedin and "linkedin.com" in linkedin.lower():
        return QualityCheck("crd_02", "Credibility", "LinkedIn Profile",
                            CheckStatus.PASS, f"LinkedIn profile linked: {linkedin}", None, 4.0)
    return QualityCheck("crd_02", "Credibility", "LinkedIn Profile",
                        CheckStatus.WARNING, "No LinkedIn profile linked.",
                        "Add your LinkedIn URL to boost recruiter confidence.", -2.0)


def check_project_links(resume: Dict[str, Any]) -> QualityCheck:
    """Check 23: Projects have live URLs or repo links."""
    projects = resume.get("projects", [])
    if not projects:
        return QualityCheck("crd_03", "Credibility", "Project Links",
                            CheckStatus.WARNING, "No projects listed to verify links.", None, 0.0)

    with_links = [p for p in projects if p.get("url", "").strip() or p.get("github_url", "").strip()]
    pct = len(with_links) / len(projects) * 100

    if pct >= 60:
        return QualityCheck("crd_03", "Credibility", "Project Links",
                            CheckStatus.PASS, f"{pct:.0f}% of projects have verifiable URLs.", None, 5.0)
    return QualityCheck("crd_03", "Credibility", "Project Links",
                        CheckStatus.WARNING, f"Only {pct:.0f}% of projects have GitHub/live links.",
                        "Add GitHub or live demo URLs to all projects for verifiability.", -3.0)


def check_certification_recency(resume: Dict[str, Any]) -> QualityCheck:
    """Check 24: Certification recency — flag if certifications may be expired."""
    certs = resume.get("certifications", [])
    if not certs:
        return QualityCheck("crd_04", "Credibility", "Certification Recency",
                            CheckStatus.WARNING, "No certifications detected.",
                            "Consider adding relevant industry certifications.", -1.0)

    old_certs = []
    import datetime
    current_year = datetime.datetime.now().year
    for cert in certs:
        year_match = re.search(r'20(\d{2})', cert.get("year", cert.get("date", "")))
        if year_match:
            cert_year = 2000 + int(year_match.group(1))
            if current_year - cert_year > 4:
                old_certs.append(cert.get("name", "Unknown cert"))

    if old_certs:
        return QualityCheck("crd_04", "Credibility", "Certification Recency",
                            CheckStatus.WARNING,
                            f"Potentially outdated certifications (>4 years): {', '.join(old_certs[:3])}.",
                            "Renew or replace outdated certifications with current industry credentials.", -2.0)

    return QualityCheck("crd_04", "Credibility", "Certification Recency",
                        CheckStatus.PASS, f"All {len(certs)} certifications appear recent.", None, 3.0)


# ── Category 6: Career Progression ───────────────────────────────────────────

def check_job_count_and_tenure(resume: Dict[str, Any]) -> QualityCheck:
    """Check 25: Job hopping — assess average tenure."""
    experience = resume.get("experience", [])
    if len(experience) < 2:
        return QualityCheck("car_01", "Career Progression", "Job Tenure",
                            CheckStatus.WARNING, "Insufficient experience entries to assess tenure.", None, 0.0)

    short_tenures = 0
    for exp in experience:
        duration = exp.get("duration", "").lower()
        # Simple heuristic: if duration contains "months" without multi-year
        if re.search(r'(\d+)\s*month', duration):
            months_match = re.search(r'(\d+)\s*month', duration)
            if months_match and int(months_match.group(1)) < 12:
                short_tenures += 1

    if short_tenures > 2:
        return QualityCheck("car_01", "Career Progression", "Job Tenure",
                            CheckStatus.WARNING,
                            f"{short_tenures} roles appear to have tenure under 1 year.",
                            "Be prepared to explain short tenures. Focus on achievements per role.", -3.0)

    return QualityCheck("car_01", "Career Progression", "Job Tenure",
                        CheckStatus.PASS, "No concerning job-hopping pattern detected.", None, 4.0)


def check_career_growth(resume: Dict[str, Any]) -> QualityCheck:
    """Check 26: Evidence of career growth in title progression."""
    experience = resume.get("experience", [])
    if len(experience) < 2:
        return QualityCheck("car_02", "Career Progression", "Career Growth",
                            CheckStatus.WARNING, "Not enough experience entries to assess growth.", None, 0.0)

    titles = [exp.get("title", "").lower() for exp in experience if exp.get("title")]
    growth_indicators = ["senior", "lead", "principal", "staff", "head", "director", "manager", "vp", "chief"]
    growth_titles = [t for t in titles if any(g in t for g in growth_indicators)]

    if growth_titles:
        return QualityCheck("car_02", "Career Progression", "Career Growth",
                            CheckStatus.PASS, f"Career progression evident with senior-level titles: {', '.join(growth_titles[:2])}.", None, 6.0)
    return QualityCheck("car_02", "Career Progression", "Career Growth",
                        CheckStatus.WARNING,
                        "No clear title progression detected.",
                        "Ensure your titles reflect promotions and increased responsibilities.", -2.0)


def check_recent_experience_first(resume: Dict[str, Any]) -> QualityCheck:
    """Check 27: Reverse chronological order (most recent job first)."""
    experience = resume.get("experience", [])
    if len(experience) < 2:
        return QualityCheck("car_03", "Career Progression", "Reverse Chronological Order",
                            CheckStatus.PASS, "Not enough entries to check order.", None, 1.0)

    # Check if any "Present" / "Current" entry is at the top
    first_duration = experience[0].get("duration", "").lower()
    has_present_first = "present" in first_duration or "current" in first_duration

    if has_present_first:
        return QualityCheck("car_03", "Career Progression", "Reverse Chronological Order",
                            CheckStatus.PASS, "Most recent (current) role appears first — correct order.", None, 3.0)

    return QualityCheck("car_03", "Career Progression", "Reverse Chronological Order",
                        CheckStatus.WARNING,
                        "Most recent role may not appear first in the resume.",
                        "List experience in reverse chronological order (newest first).", -2.0)


# ── Quality Engine Entry Point ────────────────────────────────────────────────

def run_quality_engine(
    resume: Dict[str, Any],
    jd_text: Optional[str] = None,
    target_title: Optional[str] = None
) -> QualityReport:
    """
    Run all 27 quality checks on a Canonical Resume dictionary.

    Args:
        resume: Canonical Resume JSON as a Python dict.
        jd_text: Optional job description text for tailoring checks.
        target_title: Optional target job title for alignment check.

    Returns:
        QualityReport with overall score, grade, all checks, and top action items.
    """
    # Inject JD keywords if provided
    jd_keywords = []
    if jd_text:
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\+\#\.]*[a-zA-Z0-9]\b', jd_text)
        jd_keywords = list(set(
            w.lower() for w in words
            if len(w) > 3 and w.lower() not in {
                "the", "and", "or", "for", "with", "that", "this", "will", "have",
                "from", "your", "our", "are", "you", "they", "their", "what"
            }
        ))[:50]

    checks: List[QualityCheck] = [
        # ATS Essentials
        check_contact_completeness(resume),
        check_email_format(resume),
        check_no_tables_or_graphics(resume),
        check_resume_length(resume),
        check_section_headers(resume),
        # Structure
        check_summary_quality(resume),
        check_experience_dates(resume),
        check_skills_categorization(resume),
        check_education_completeness(resume),
        check_projects_presence(resume),
        # Content
        check_bullet_action_verbs(resume),
        check_bullet_quantification(resume),
        check_bullet_length(resume),
        check_no_personal_pronouns(resume),
        check_consistency(resume),
        check_content_depth(resume),
        # Tailoring
        check_title_alignment(resume, target_title),
        check_keyword_coverage(resume, jd_keywords if jd_keywords else None),
        check_custom_summary(resume, jd_text),
        check_no_generic_phrases(resume),
        # Credibility
        check_github_presence(resume),
        check_linkedin_presence(resume),
        check_project_links(resume),
        check_certification_recency(resume),
        # Career Progression
        check_job_count_and_tenure(resume),
        check_career_growth(resume),
        check_recent_experience_first(resume),
    ]

    pass_count = sum(1 for c in checks if c.status == CheckStatus.PASS)
    warning_count = sum(1 for c in checks if c.status == CheckStatus.WARNING)
    fail_count = sum(1 for c in checks if c.status == CheckStatus.FAIL)

    # Score: 50 base + weighted by check outcomes
    base_score = 50.0
    bonus = sum(c.score_impact for c in checks if c.score_impact > 0)
    penalty = sum(abs(c.score_impact) for c in checks if c.score_impact < 0)
    raw_score = base_score + bonus - penalty
    overall_score = round(max(0.0, min(100.0, raw_score)), 1)

    if overall_score >= 85:
        grade = "A"
    elif overall_score >= 70:
        grade = "B"
    elif overall_score >= 55:
        grade = "C"
    elif overall_score >= 40:
        grade = "D"
    else:
        grade = "F"

    # Top 3 action items (highest-impact failures/warnings)
    actionable = [c for c in checks if c.status != CheckStatus.PASS and c.recommendation]
    actionable.sort(key=lambda c: abs(c.score_impact), reverse=True)
    top_actions = [c.recommendation for c in actionable[:3] if c.recommendation]

    summary_parts = [f"{pass_count}/27 checks passed"]
    if fail_count:
        summary_parts.append(f"{fail_count} critical issues")
    if warning_count:
        summary_parts.append(f"{warning_count} warnings")

    return QualityReport(
        overall_score=overall_score,
        grade=grade,
        checks=checks,
        pass_count=pass_count,
        warning_count=warning_count,
        fail_count=fail_count,
        summary=". ".join(summary_parts) + ".",
        top_actions=top_actions
    )
