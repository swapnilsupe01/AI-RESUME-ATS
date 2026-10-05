"""
Resume-Based Academic-Year & Educational Stage Detector for Layer F.
Provides deterministic calculation of academic stage, degree duration analysis,
explicit statement detection, college/institution extraction, educational pathway
(After 12th vs After Diploma / Lateral Entry), timeline extraction, and contradiction flagging.
"""

from datetime import datetime, timezone
import re
from typing import Dict, Any, List, Optional, Tuple, Literal
from pydantic import BaseModel, Field

# Standard degree duration mappings (in years)
DEGREE_DURATION_MAP: Dict[str, int] = {
    # 4-year undergraduate engineering & technology
    "b.tech": 4,
    "btech": 4,
    "b.e.": 4,
    "be": 4,
    "bachelor of technology": 4,
    "bachelor of engineering": 4,
    "b.s.": 4,
    "bs": 4,
    "bachelor of science": 3,  # Refined if 4-year BS in US vs 3-year BSc in India/UK
    "b.sc": 3,
    "bsc": 3,
    "bca": 3,
    "bachelor of computer applications": 3,
    "bba": 3,
    "b.com": 3,
    "bcom": 3,
    "b.a.": 3,
    "ba": 3,
    "b.des": 4,
    "b.arch": 5,
    # 2-year postgraduate
    "m.tech": 2,
    "mtech": 2,
    "m.e.": 2,
    "me": 2,
    "master of technology": 2,
    "master of engineering": 2,
    "m.s.": 2,
    "ms": 2,
    "master of science": 2,
    "m.sc": 2,
    "msc": 2,
    "mca": 2,
    "master of computer applications": 2,
    "mba": 2,
    # 3-year diploma / polytechnic
    "diploma": 3,
    "polytechnic": 3,
    # 5-year integrated / dual
    "integrated m.tech": 5,
    "dual degree": 5,
    "b.tech + m.tech": 5,
    "b.a. ll.b": 5,
    # Research
    "ph.d": 4,
    "phd": 4,
}

AcademicStage = Literal[
    "first_year",
    "second_year",
    "third_year",
    "final_year",
    "graduated",
    "postgraduate",
    "unknown"
]


class AcademicYearResult(BaseModel):
    academic_stage: AcademicStage = "unknown"
    academic_year: Optional[int] = Field(default=None, description="1, 2, 3, 4, 5 if currently enrolled")
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    institution: Optional[str] = None
    college_name: Optional[str] = None
    start_year: Optional[int] = None
    graduation_year: Optional[int] = None
    timeline: Optional[str] = None
    duration_years: Optional[int] = None
    pathway: Optional[str] = None
    is_currently_enrolled: bool = False
    is_lateral_entry: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    has_conflict: bool = False
    confirmed_by_student: bool = False


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _extract_years_from_string(text: str) -> List[int]:
    """Find 4-digit years between 1990 and 2040."""
    matches = re.findall(r"\b(19\d\d|20\d\d)\b", text)
    return [int(m) for m in matches]


def _match_degree_pattern(text: str) -> Tuple[Optional[str], int]:
    """Identify degree name and standard duration."""
    lower = _normalize_text(text)
    
    # Check integrated / dual first
    if "integrated" in lower or "dual degree" in lower:
        return ("Integrated Dual Degree", 5)
    
    if "b.arch" in lower or "architecture" in lower:
        return ("B.Arch", 5)

    for key, duration in DEGREE_DURATION_MAP.items():
        # Match whole word or punctuated degree
        pattern = r"\b" + re.escape(key) + r"\b"
        if re.search(pattern, lower):
            deg_display = key.upper().replace("B.", "B.").replace("M.", "M.")
            return (deg_display, duration)
            
    if "bachelor" in lower or "b.e" in lower or "b.tech" in lower or "engineering" in lower:
        return ("Bachelor of Technology (B.Tech / B.E.)", 4)
    if "master" in lower or "post graduate" in lower or "m.tech" in lower:
        return ("Master's Degree", 2)
    if "diploma" in lower or "polytechnic" in lower:
        return ("Diploma in Engineering", 3)
        
    return (None, 4)


def _extract_institution_from_text(text: str) -> Optional[str]:
    """Extract college or university name from text or education blocks."""
    if not text:
        return None
        
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    # Keywords indicating a college or educational institution
    college_pattern = re.compile(
        r"(?:college\s+of\s+engineering|institute\s+of\s+technology|polytechnic|"
        r"engineering\s+college|technology\s+and\s+management|institute\s+of\s+science\s+and\s+technology|"
        r"university|faculty\s+of\s+technology|school\s+of\s+engineering|vidyapeeth|"
        r"academy\s+of\s+engineering|iit\b|nit\b|iiit\b|bits\b|vit\b|mit\b|coep\b|vjti\b|pict\b|pccoep?\b)",
        re.IGNORECASE
    )
    
    for line in lines:
        if college_pattern.search(line) and not line.lower().startswith("education") and len(line) < 120:
            cleaned = re.sub(r"^[#*\-•\d\.\s]+", "", line).strip()
            # Remove trailing dates if attached
            cleaned = re.sub(r"\(?\b(?:19|20)\d{2}\s*[-–—to]+\s*(?:(?:19|20)\d{2}|Present)\b\)?", "", cleaned, flags=re.IGNORECASE).strip()
            cleaned = cleaned.rstrip(" ,|-")
            if len(cleaned) > 5:
                return cleaned
                
    # Regex search across text chunk if not found by line
    match = re.search(
        r"([A-Z][A-Za-z\s,&.-]{3,60}(?:College of Engineering|Institute of Technology|Polytechnic|University|Engineering College|Academy of Engineering)[A-Za-z\s,&.-]{0,30})",
        text
    )
    if match:
        inst = match.group(1).strip().rstrip(" ,|-")
        if len(inst) > 5:
            return inst

    return None


def _detect_field_of_study(text: str) -> Optional[str]:
    """Detect engineering/technology specialization or branch."""
    lower = _normalize_text(text)
    
    branches = [
        ("Computer Science & Engineering", r"\b(computer\s*science(?:\s*(?:and|&)\s*engineering)?|cse|cs)\b"),
        ("Computer Engineering", r"\b(computer\s*engineering|computer\s*technology)\b"),
        ("Information Technology", r"\b(information\s*technology|it)\b"),
        ("Artificial Intelligence & Data Science", r"\b(artificial\s*intelligence(?:\s*(?:and|&)\s*data\s*science)?|ai\s*(&|and)\s*ds|ai\s*(&|and)\s*ml|aiml)\b"),
        ("Data Science", r"\b(data\s*science|data\s*analytics)\b"),
        ("Electronics & Telecommunication", r"\b(electronics(?:\s*(?:and|&)\s*telecommunication)?|entc|ece)\b"),
        ("Electrical Engineering", r"\b(electrical\s*engineering|eee)\b"),
        ("Mechanical Engineering", r"\b(mechanical\s*engineering|mech)\b"),
        ("Civil Engineering", r"\b(civil\s*engineering)\b"),
        ("Software Engineering", r"\b(software\s*engineering)\b"),
        ("Robotics & Automation", r"\b(robotics(?:\s*(?:and|&)\s*automation)?)\b"),
    ]
    
    for name, pattern in branches:
        if re.search(pattern, lower):
            return name
            
    return None


def _detect_explicit_stage(text: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Detect explicit mentions of academic year or semester.
    Returns: (year_number, stage_name, evidence_snippet)
    """
    lower = _normalize_text(text)
    
    # 1. First year / Semester 1-2
    if re.search(r"\b(1st\s*year|first\s*year|freshman|1st\s*sem|sem(?:ester)?\s*1|sem(?:ester)?\s*2)\b", lower):
        return (1, "first_year", "Explicitly stated 1st year / semester 1-2")
        
    # 2. Second year / Semester 3-4 / Direct Second Year
    if re.search(r"\b(2nd\s*year|second\s*year|sophomore|2nd\s*sem|sem(?:ester)?\s*3|sem(?:ester)?\s*4|direct\s*second\s*year|dsy)\b", lower):
        return (2, "second_year", "Explicitly stated 2nd year / semester 3-4")
        
    # 3. Third year / Semester 5-6 / Penultimate
    if re.search(r"\b(3rd\s*year|third\s*year|junior|sem(?:ester)?\s*5|sem(?:ester)?\s*6|penultimate\s*year)\b", lower):
        return (3, "third_year", "Explicitly stated 3rd year / semester 5-6")
        
    # 4. Final year / 4th year / Semester 7-8 / Senior
    if re.search(r"\b(4th\s*year|fourth\s*year|final\s*year|senior|sem(?:ester)?\s*7|sem(?:ester)?\s*8|graduating\s*year)\b", lower):
        return (4, "final_year", "Explicitly stated 4th / final year")
        
    # 5. Graduated / Alumni
    if re.search(r"\b(graduated|fresh\s*graduate|alumnus|alumna|passed\s*out)\b", lower):
        return (None, "graduated", "Explicitly stated graduated / alumni")

    return (None, None, None)


def _detect_pathway(
    education_entries: List[Dict[str, Any]],
    raw_text: str,
    is_lateral: bool,
    degree_display: str
) -> str:
    """Determine whether student joined after 12th (HSC) or after 3-Year Diploma (Polytechnic Lateral Entry)."""
    full_text = " ".join([
        f"{e.get('degree', '')} {e.get('institution', '')} {e.get('field_of_study', '')}"
        for e in education_entries
    ]) + " " + raw_text
    
    lower = full_text.lower()
    
    has_diploma = bool(re.search(r"\b(diploma|polytechnic|lateral|direct\s*second\s*year|dsy|diploma\s*to\s*degree)\b", lower))
    has_12th = bool(re.search(r"\b(12th|hsc|higher\s*secondary|intermediate|cbse\s*-\s*class\s*xii|class\s*12|senior\s*secondary)\b", lower))
    is_pg = any(m in degree_display.lower() for m in ["master", "m.tech", "m.s.", "m.sc", "mca", "mba"])
    
    if is_pg:
        return "Postgraduate (Master's Degree Program)"
    if has_diploma or is_lateral:
        return "After Diploma (Polytechnic Lateral Entry / Direct 2nd Year B.Tech)"
    if has_12th:
        return "After 12th (Standard 4-Year B.Tech / B.E. Degree)"
    
    # Default for 4-year degree
    return "After 12th / Standard 4-Year Undergraduate Degree"


def detect_academic_year(
    education_entries: Optional[List[Dict[str, Any]]] = None,
    raw_text: str = "",
    reference_date: Optional[datetime] = None,
    confirmed_stage: Optional[str] = None
) -> AcademicYearResult:
    """
    Deterministically detect the student's academic year, college, degree, pathway, and stage.
    
    Parameters:
    - education_entries: List of dicts representing education items (institution, degree, start_date, end_date, etc.)
    - raw_text: Raw resume text for explicit statement and section detection.
    - reference_date: Reference current date (defaults to UTC current date).
    - confirmed_stage: Student manual override if they confirmed their stage.
    """
    ref_dt = reference_date or datetime.now(timezone.utc)
    current_year = ref_dt.year
    # In academic systems, the new academic year typically begins around July/August (month >= 7)
    current_academic_start_year = current_year if ref_dt.month >= 7 else (current_year - 1)
    
    evidence: List[str] = []
    assumptions: List[str] = []
    warnings: List[str] = []
    
    # If student manually confirmed their academic stage
    if confirmed_stage and confirmed_stage in ("first_year", "second_year", "third_year", "final_year", "graduated", "postgraduate"):
        stage_map = {"first_year": 1, "second_year": 2, "third_year": 3, "final_year": 4}
        return AcademicYearResult(
            academic_stage=confirmed_stage,  # type: ignore
            academic_year=stage_map.get(confirmed_stage),
            confidence=1.0,
            evidence=[f"Student explicitly confirmed stage as: {confirmed_stage}"],
            confirmed_by_student=True
        )

    # 1. Search for explicit stage in raw text
    explicit_yr, explicit_stage, explicit_evidence = _detect_explicit_stage(raw_text)
    if explicit_evidence:
        evidence.append(explicit_evidence)

    # 2. Inspect education entries
    parsed_entries = education_entries or []
    
    # Filter for the most relevant/recent university-level degree
    target_edu = None
    for edu in parsed_entries:
        deg = edu.get("degree", "") or ""
        inst = edu.get("institution", "") or ""
        text_block = f"{deg} {inst} {edu.get('field_of_study', '')}"
        
        # Skip 10th / 12th / High school if higher education is present
        if any(h in text_block.lower() for h in ["10th", "12th", "ssc", "hsc", "high school", "secondary school", "cbse - class x", "cbse - class xii"]):
            continue
            
        target_edu = edu
        break
        
    # If all were skipped or none matched, fallback to first entry
    if not target_edu and parsed_entries:
        target_edu = parsed_entries[0]

    # If no target_edu, parse from raw text
    if not target_edu:
        edu_sec_match = re.search(r"(?:education|academic background|qualifications|academic qualifications)([\s\S]{1,1500})", raw_text, re.IGNORECASE)
        search_block = edu_sec_match.group(1) if edu_sec_match else raw_text
        
        years = _extract_years_from_string(search_block)
        deg, duration = _match_degree_pattern(search_block)
        detected_inst = _extract_institution_from_text(search_block)
        detected_fos = _detect_field_of_study(search_block)
        
        if years or deg or detected_inst:
            target_edu = {
                "degree": deg or "B.Tech / Bachelor of Engineering",
                "field_of_study": detected_fos or "Engineering & Technology",
                "start_date": str(years[0]) if years else "",
                "end_date": str(years[1]) if len(years) > 1 else ("Present" if "present" in search_block.lower() else ""),
                "institution": detected_inst or ""
            }
            evidence.append(f"Extracted education from resume text: {deg or 'Engineering Degree'} at {detected_inst or 'Engineering College'} ({years})")

    if not target_edu and not explicit_stage:
        return AcademicYearResult(
            academic_stage="unknown",
            confidence=0.0,
            warnings=["No structured education entries or academic year statements detected."],
            assumptions=["Academic stage cannot be reliably determined without education records."]
        )

    # Analyze target_edu
    deg_name = target_edu.get("degree", "") if target_edu else ""
    inst_name = target_edu.get("institution", "") if target_edu else ""
    field_of_study = target_edu.get("field_of_study", "") if target_edu else ""
    start_str = str(target_edu.get("start_date", "") or "") if target_edu else ""
    end_str = str(target_edu.get("end_date", "") or "") if target_edu else ""
    
    # Fallback institution extraction from raw text if missing in target_edu
    if not inst_name:
        inst_name = _extract_institution_from_text(raw_text) or ""
    if not field_of_study:
        field_of_study = _detect_field_of_study(f"{deg_name} {raw_text}") or ""

    deg_matched, default_duration = _match_degree_pattern(f"{deg_name} {field_of_study}")
    degree_display = deg_matched or (deg_name if deg_name else "Bachelor of Technology (B.Tech / B.E.)")
    
    # Check for lateral entry / diploma background
    is_lateral = bool(re.search(r"\b(lateral|direct\s*second\s*year|dsy|diploma\s*to\s*degree)\b", f"{deg_name} {field_of_study} {raw_text}", re.IGNORECASE))
    
    # Check if any prior education entry was a Diploma
    has_prior_diploma = any("diploma" in str(e.get("degree", "")).lower() or "polytechnic" in str(e.get("institution", "")).lower() for e in parsed_entries)
    if has_prior_diploma:
        is_lateral = True
        
    if is_lateral and default_duration == 4:
        default_duration = 3
        assumptions.append("Adjusted degree duration to 3 years due to Lateral Entry / Direct Second Year admission after Diploma.")

    start_years = _extract_years_from_string(start_str)
    end_years = _extract_years_from_string(end_str)
    
    # If dates are in combined string like "2025 - 2029"
    if not start_years and not end_years:
        all_yrs = _extract_years_from_string(f"{start_str} {end_str}")
        if len(all_yrs) >= 2:
            start_years = [all_yrs[0]]
            end_years = [all_yrs[1]]
        elif len(all_yrs) == 1:
            if "present" in end_str.lower() or "current" in end_str.lower():
                start_years = [all_yrs[0]]
            else:
                end_years = [all_yrs[0]]

    # If still no start/end years, search raw text for education year patterns (e.g., 2025-2029)
    if not start_years and not end_years:
        all_raw_years = _extract_years_from_string(raw_text)
        if len(all_raw_years) >= 2:
            start_years = [all_raw_years[0]]
            end_years = [all_raw_years[1]]

    has_present = "present" in end_str.lower() or "current" in end_str.lower() or (target_edu.get("current", False) if target_edu else False)
    
    start_yr = start_years[0] if start_years else None
    end_yr = end_years[0] if end_years else None
    
    pathway_str = _detect_pathway(parsed_entries, raw_text, is_lateral, degree_display)
    
    timeline_str = None
    if start_yr and end_yr:
        timeline_str = f"{start_yr} – {end_yr}"
    elif start_yr and has_present:
        timeline_str = f"{start_yr} – Present"
    elif end_yr:
        timeline_str = f"Class of {end_yr}"

    evidence.append(f"Identified program: {degree_display} ({field_of_study or 'Engineering'}) at {inst_name or 'College of Engineering / Technology'}")
    evidence.append(f"Educational Pathway: {pathway_str} (Standard duration: {default_duration} years)")
    if start_yr:
        evidence.append(f"Course start year: {start_yr}")
    if end_yr:
        evidence.append(f"Expected graduation year: {end_yr}")
    elif has_present:
        evidence.append("Graduation date listed as 'Present' (in-progress enrollment).")

    # Date-based calculation
    calculated_stage: Optional[AcademicStage] = None
    calculated_year_num: Optional[int] = None
    has_conflict = False

    if start_yr and end_yr and not has_present:
        # Full date span provided e.g., 2025 - 2029
        if end_yr < current_year or (end_yr == current_year and ref_dt.month >= 7):
            calculated_stage = "graduated"
            calculated_year_num = None
            evidence.append(f"Graduation year {end_yr} has passed relative to reference date ({ref_dt.strftime('%B %Y')}).")
        else:
            # Currently enrolled
            # Elapsed academic years since start
            elapsed = current_academic_start_year - start_yr + 1
            calculated_year_num = max(1, min(default_duration, elapsed))
            
            if calculated_year_num == 1:
                calculated_stage = "first_year"
            elif calculated_year_num == 2:
                calculated_stage = "second_year"
            elif calculated_year_num == 3:
                calculated_stage = "third_year" if default_duration >= 4 else "final_year"
            elif calculated_year_num >= 4:
                calculated_stage = "final_year"
                
    elif start_yr and (has_present or not end_yr):
        # Start year known, end is Present or unspecified
        elapsed = current_academic_start_year - start_yr + 1
        if elapsed > default_duration:
            calculated_stage = "graduated"
            calculated_year_num = None
            assumptions.append(f"Elapsed time ({elapsed} years) exceeds standard {default_duration}-year duration; provisionally classified as graduated.")
        else:
            calculated_year_num = max(1, min(default_duration, elapsed))
            if calculated_year_num == 1:
                calculated_stage = "first_year"
            elif calculated_year_num == 2:
                calculated_stage = "second_year"
            elif calculated_year_num == 3:
                calculated_stage = "third_year" if default_duration >= 4 else "final_year"
            elif calculated_year_num >= 4:
                calculated_stage = "final_year"
            end_yr = start_yr + default_duration
            assumptions.append(f"Estimated expected graduation year as {end_yr} based on standard {default_duration}-year duration from {start_yr}.")

    elif end_yr and not start_yr:
        # Only graduation year known e.g., "Expected May 2029"
        if end_yr < current_year or (end_yr == current_year and ref_dt.month >= 7):
            calculated_stage = "graduated"
            calculated_year_num = None
        else:
            remaining_years = end_yr - current_academic_start_year
            calc_yr = default_duration - remaining_years + 1
            calculated_year_num = max(1, min(default_duration, calc_yr))
            if calculated_year_num == 1:
                calculated_stage = "first_year"
            elif calculated_year_num == 2:
                calculated_stage = "second_year"
            elif calculated_year_num == 3:
                calculated_stage = "third_year" if default_duration >= 4 else "final_year"
            elif calculated_year_num >= 4:
                calculated_stage = "final_year"
            start_yr = end_yr - default_duration
            assumptions.append(f"Inferred course start year as {start_yr} based on graduation year {end_yr}.")

    # Reconcile explicit statement vs calculated dates
    final_stage: AcademicStage = "unknown"
    final_year_num: Optional[int] = None
    confidence = 0.5

    if explicit_stage and calculated_stage:
        if explicit_stage == calculated_stage:
            final_stage = calculated_stage
            final_year_num = calculated_year_num or explicit_yr
            confidence = 0.95
            evidence.append("Explicit academic-year statement perfectly aligns with date calculations.")
        else:
            # Conflict detected
            has_conflict = True
            warnings.append(
                f"Contradiction detected: Resume explicitly states '{explicit_stage.replace('_', ' ').title()}' "
                f"({explicit_evidence}), but education dates ({start_yr or '?'}–{end_yr or '?'}) calculate to '{calculated_stage.replace('_', ' ').title()}'. "
                f"Using verified date calculation ({calculated_stage}) provisionally. Student confirmation recommended."
            )
            final_stage = calculated_stage
            final_year_num = calculated_year_num
            confidence = 0.65
    elif explicit_stage and not calculated_stage:
        final_stage = explicit_stage  # type: ignore
        final_year_num = explicit_yr
        confidence = 0.85
        evidence.append("Derived academic stage from explicit text statements in resume.")
    elif calculated_stage:
        final_stage = calculated_stage
        final_year_num = calculated_year_num
        confidence = 0.85 if (start_yr and end_yr) else 0.70
    else:
        final_stage = "unknown"
        confidence = 0.1
        warnings.append("Insufficient date and section evidence to establish academic year.")

    # Postgraduate adjustment
    if final_stage != "unknown" and any(m in degree_display.lower() for m in ["m.tech", "m.s.", "m.sc", "mca", "master", "ph.d", "phd"]):
        if final_stage != "graduated":
            assumptions.append(f"Candidate is pursuing a postgraduate degree ({degree_display}).")

    return AcademicYearResult(
        academic_stage=final_stage,
        academic_year=final_year_num,
        degree=degree_display,
        field_of_study=field_of_study or None,
        institution=inst_name or None,
        college_name=inst_name or None,
        start_year=start_yr,
        graduation_year=end_yr,
        timeline=timeline_str,
        duration_years=default_duration,
        pathway=pathway_str,
        is_currently_enrolled=(final_stage not in ("graduated", "unknown")),
        is_lateral_entry=is_lateral,
        confidence=round(confidence, 2),
        evidence=evidence,
        assumptions=assumptions,
        warnings=warnings,
        has_conflict=has_conflict,
        confirmed_by_student=False
    )
