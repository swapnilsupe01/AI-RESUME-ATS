# """
# ATS-Compliant PDF Generator — Swapnil Supe Perfect Resume Design.
# Renders clean, ATS-parseable resume PDFs matching the golden reference layout:

#   PROFILE → TECHNICAL SKILLS (2-col) → PROJECTS → EXPERIENCE (2-col bullets)
#   → EDUCATION (compact) → CERTIFICATIONS (inline I./II.) → HOBBIES (inline)

# Visual rules (from golden PDF):
# - US Letter, ~25pt side margins
# - Centered bold name (~19pt), centered contact, links line
# - Blue section headings rgb(55,80,120) with gray underline
# - Skills: 2-column Category: items grid
# - Projects: bold title, italic tech stack, bullets
# - Experience: bold title; bullets zig-zag in 2 columns
# - Education: School — Degree | score | years (single line)
# - Certs/Hobbies: inline labeled rows (no underline)
# - Footer: tiny centered candidate name
# """

# from typing import Dict, Any, List, Optional, Tuple
# import re
# import pymupdf as fitz

# try:
#     from app.parser.markdown_pipeline import parse_education_entry_line
# except ImportError:
#     try:
#         from backend.app.parser.markdown_pipeline import parse_education_entry_line
#     except ImportError:
#         parse_education_entry_line = None  # type: ignore


# # ---------------------------------------------------------------------------
# # Unicode & Character Normalization
# # ---------------------------------------------------------------------------

# _CHAR_REPLACEMENTS = {
#     "\u2014": " - ", "\u2013": " - ", "\u2012": " - ", "\u2015": " - ",
#     "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',
#     "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
#     "\u00a0": " ", "\t": "    ",
#     "\u2022": "*", "\u25cf": "*", "\u25aa": "*", "\u2023": "*",
#     "\u2219": "*", "\u00b7": "*", "\u2756": "*", "\u25c6": "*", "\u25c8": "*",
#     "\u2026": "...",
#     "\u2192": "->", "\u21d2": "=>", "\u2794": "->", "\u27a4": "->",
#     "\u2713": "[x]", "\u2714": "[x]", "\u2717": "[ ]", "\u2718": "[ ]",
#     "\u200b": "", "\ufeff": "",
# }

# _ROMAN = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
#           "XI", "XII", "XIII", "XIV", "XV")


# def _clean_str(val: Any) -> str:
#     """Sanitize, normalize unicode characters, and strip leading bullet artifacts."""
#     if val is None:
#         return ""
#     s = str(val).strip()
#     if not s:
#         return ""

#     s = re.sub(r'^[❖●•\-\*\s]+', '', s)

#     for orig, rep in _CHAR_REPLACEMENTS.items():
#         s = s.replace(orig, rep)

#     # Filter non-latin characters that standard Type-1 Helvetica cannot render
#     clean = []
#     for ch in s:
#         code = ord(ch)
#         if code < 128 or (160 <= code <= 255):
#             clean.append(ch)
#         else:
#             clean.append(" ")
#     return re.sub(r'\s+', ' ', ''.join(clean)).strip()


# def _ensure_list(val: Any) -> List[str]:
#     """Ensure highlight/bullet inputs are cleanly parsed into a list of strings."""
#     if val is None:
#         return []
#     if isinstance(val, list):
#         out = []
#         for item in val:
#             if isinstance(item, dict):
#                 text = item.get("text") or item.get("name") or str(item)
#                 cleaned = _clean_str(text)
#                 if cleaned and cleaned.lower() not in ('*', '•', '-', 'bullet'):
#                     out.append(cleaned)
#             elif item is not None:
#                 cleaned = _clean_str(str(item))
#                 if cleaned and cleaned.lower() not in ('*', '•', '-', 'bullet'):
#                     out.append(cleaned)
#         return out
#     if isinstance(val, (str, bytes)):
#         s = _clean_str(str(val))
#         if not s:
#             return []
#         if "\n" in s:
#             return [
#                 _clean_str(line) for line in s.splitlines()
#                 if _clean_str(line) and _clean_str(line).lower() not in ('*', '•', '-', 'bullet')
#             ]
#         return [s]
#     cleaned = _clean_str(str(val))
#     return [cleaned] if cleaned else []


# def _get_val(d: Any, *keys: str, default: str = "") -> str:
#     """Fetch the first non-empty string value across multiple potential keys."""
#     if not isinstance(d, dict):
#         return default
#     for k in keys:
#         v = d.get(k)
#         if v is not None:
#             sv = _clean_str(v)
#             if sv:
#                 return sv
#     return default


# def _wrap_text_lines(text: str, fs: float, max_w: float, fn: str = "helv") -> List[str]:
#     """Wrap text into lines accurately using fitz.get_text_length."""
#     if not text:
#         return []
#     words = text.split()
#     if not words:
#         return []

#     lines = []
#     curr = []
#     for w in words:
#         cand = " ".join(curr + [w])
#         if fitz.get_text_length(cand, fontname=fn, fontsize=fs) <= max_w:
#             curr.append(w)
#         else:
#             if curr:
#                 lines.append(" ".join(curr))
#             curr = [w]
#     if curr:
#         lines.append(" ".join(curr))
#     return lines if lines else [text]


# def _strip_url(url: str) -> str:
#     u = _clean_str(url)
#     u = re.sub(r'^https?://', '', u, flags=re.I).rstrip("/")
#     return u


# def _roman(n: int) -> str:
#     if 1 <= n <= len(_ROMAN):
#         return _ROMAN[n - 1]
#     return str(n)


# def _format_gpa_label(gpa: str) -> str:
#     """Normalize GPA/percentage for golden education lines."""
#     gpa = _clean_str(gpa)
#     if not gpa:
#         return ""
#     nums = re.findall(r"[\d.]+", gpa)
#     if "%" in gpa:
#         return gpa if gpa.endswith("%") else f"{gpa}%"
#     if nums:
#         try:
#             val = float(nums[0])
#             if val > 10:
#                 return gpa if "%" in gpa else f"{nums[0]}%"
#         except ValueError:
#             pass
#     if "cgpa" in gpa.lower() or "gpa" in gpa.lower():
#         return gpa
#     return f"{gpa} CGPA"


# def _coerce_to_dict(item: Any) -> Optional[Dict[str, Any]]:
#     """Accept dicts, pydantic models, or skip junk."""
#     if item is None:
#         return None
#     if isinstance(item, dict):
#         return item
#     if hasattr(item, "model_dump"):
#         try:
#             return item.model_dump()
#         except Exception:
#             pass
#     if hasattr(item, "dict"):
#         try:
#             return item.dict()
#         except Exception:
#             pass
#     return None


# _PLACEHOLDER_ROLES = {
#     "role", "title", "position", "job title", "job role", "designation",
# }
# _PLACEHOLDER_COMPS = {
#     "company", "organization", "employer", "org", "company name",
# }


# def _is_placeholder_experience(role: str, comp: str) -> bool:
#     r = (role or "").strip().lower()
#     c = (comp or "").strip().lower()
#     if not r and not c:
#         return True
#     if r in _PLACEHOLDER_ROLES and (not c or c in _PLACEHOLDER_COMPS):
#         return True
#     if c in _PLACEHOLDER_COMPS and (not r or r in _PLACEHOLDER_ROLES):
#         return True
#     if r in _PLACEHOLDER_ROLES and c in _PLACEHOLDER_COMPS:
#         return True
#     return False


# def _normalize_education_item(edu: Any) -> Optional[Dict[str, str]]:
#     """
#     Recover institution / degree / GPA / years even when the parser merged them
#     into a single institution string (common cause of missing college years).
#     """
#     if isinstance(edu, str):
#         raw_line = _clean_str(edu)
#         base: Dict[str, Any] = {}
#     else:
#         base = _coerce_to_dict(edu) or {}
#         if not base and not isinstance(edu, dict):
#             return None
#         raw_line = ""

#     school = _get_val(base, "institution", "school", "university", "college", "institute", "academy")
#     deg = _get_val(base, "degree", "qualification")
#     field = _get_val(base, "field_of_study", "major", "stream", "branch")
#     start = _get_val(base, "start_date")
#     end = _get_val(base, "end_date", "year", "graduation_year")
#     dates = _get_val(base, "dates", "period")
#     gpa = _get_val(base, "gpa", "percentage", "score", "cgpa", "grade")

#     # Rebuild a golden-style line so the shared parser can split merged fields
#     if not raw_line:
#         if school and deg:
#             if field and field.lower() not in deg.lower():
#                 deg_part = f"{deg} in {field}" if "in" not in deg.lower() else f"{deg} {field}"
#             else:
#                 deg_part = deg
#             raw_line = f"{school} - {deg_part}"
#         elif school:
#             raw_line = school
#         elif deg:
#             raw_line = f"{deg} in {field}" if field else deg
#         meta = []
#         if gpa:
#             meta.append(gpa)
#         if dates:
#             meta.append(dates)
#         elif start and end:
#             meta.append(f"{start}-{end}")
#         elif end:
#             meta.append(end)
#         elif start:
#             meta.append(start)
#         if raw_line and meta:
#             raw_line = f"{raw_line} | {' | '.join(meta)}"

#     parsed: Dict[str, str] = {}
#     if raw_line and parse_education_entry_line is not None:
#         try:
#             parsed = parse_education_entry_line(raw_line) or {}
#         except Exception:
#             parsed = {}

#     # If institution looks like a full golden line, prefer parser split
#     school_looks_merged = bool(
#         school and (
#             " | " in school
#             or re.search(r'\s[-–—]\s', school)
#             or re.search(r'\b(20\d{2})\b', school)
#             or re.search(r'\b\d{1,2}(?:\.\d+)?\s*%|\bcgpa\b', school, re.I)
#         )
#     )
#     if school_looks_merged and parse_education_entry_line is not None:
#         try:
#             parsed_school = parse_education_entry_line(school) or {}
#             if parsed_school.get("institution"):
#                 for k, v in parsed_school.items():
#                     if v and not parsed.get(k):
#                         parsed[k] = v
#                 if parsed_school.get("institution"):
#                     school = _clean_str(parsed_school.get("institution"))
#                 if parsed_school.get("degree") and not deg:
#                     deg = _clean_str(parsed_school.get("degree"))
#                 if parsed_school.get("field_of_study") and not field:
#                     field = _clean_str(parsed_school.get("field_of_study"))
#                 if parsed_school.get("gpa") and not gpa:
#                     gpa = _clean_str(parsed_school.get("gpa"))
#                 if parsed_school.get("start_date") and not start:
#                     start = _clean_str(parsed_school.get("start_date"))
#                 if parsed_school.get("end_date") and not end:
#                     end = _clean_str(parsed_school.get("end_date"))
#         except Exception:
#             pass

#     # Structured fields win when present; parser fills gaps (esp. years/GPA)
#     out = {
#         "institution": school or _clean_str(parsed.get("institution")),
#         "degree": deg or _clean_str(parsed.get("degree")),
#         "field_of_study": field or _clean_str(parsed.get("field_of_study")),
#         "start_date": start or _clean_str(parsed.get("start_date")),
#         "end_date": end or _clean_str(parsed.get("end_date")),
#         "gpa": gpa or _clean_str(parsed.get("gpa")),
#         "dates": dates,
#     }

#     # If institution still contains "School - Degree" and degree empty, split again
#     inst = out["institution"]
#     if inst and not out["degree"] and re.search(r'\s[-–—]\s', inst):
#         if parse_education_entry_line is not None:
#             try:
#                 again = parse_education_entry_line(inst) or {}
#                 if again.get("institution"):
#                     out["institution"] = _clean_str(again.get("institution"))
#                 if again.get("degree") and not out["degree"]:
#                     out["degree"] = _clean_str(again.get("degree"))
#                 if again.get("field_of_study") and not out["field_of_study"]:
#                     out["field_of_study"] = _clean_str(again.get("field_of_study"))
#                 if again.get("gpa") and not out["gpa"]:
#                     out["gpa"] = _clean_str(again.get("gpa"))
#                 if again.get("start_date") and not out["start_date"]:
#                     out["start_date"] = _clean_str(again.get("start_date"))
#                 if again.get("end_date") and not out["end_date"]:
#                     out["end_date"] = _clean_str(again.get("end_date"))
#             except Exception:
#                 pass

#     if not out["institution"] and not out["degree"] and not out["field_of_study"]:
#         return None
#     return out


# def _is_junk_education(edu: Dict[str, str]) -> bool:
#     """Drop mis-parsed CERTIFICATIONS / HOBBIES / footer-name rows from education."""
#     inst = (edu.get("institution") or "").strip()
#     deg = (edu.get("degree") or "").strip()
#     field = (edu.get("field_of_study") or "").strip()
#     blob = f"{inst} {deg} {field}".strip().lower()
#     if not blob:
#         return True
#     if re.search(r'\b(certifications?|hobbies|interests)\s*:', blob):
#         return True
#     if re.match(r'^(certifications?|hobbies|interests)\b', blob):
#         return True
#     # Footer / name leakage into education
#     if re.match(r'^[a-z]+\s+[a-z]+$', deg.lower()) and not inst:
#         return True
#     if deg.lower() in {"swapnil supe", "candidate name", "candidate"}:
#         return True
#     if "hobbies:" in inst.lower() or "certifications:" in inst.lower():
#         return True
#     return False


# def _format_degree_display(deg: str, field: str) -> str:
#     deg = _clean_str(deg)
#     field = _clean_str(field)
#     if not deg:
#         return field
#     if not field or field.lower() in deg.lower():
#         return deg
#     # "B.Tech Computer" + "Engineering" → "B.Tech Computer Engineering"
#     if re.search(r'\b(b\.?tech|b\.?e\.?|m\.?tech|m\.?e\.?|diploma|bachelor|master|b\.?sc|m\.?sc)\b', deg, re.I):
#         if field.lower() in {
#             "engineering", "technology", "science", "arts", "commerce",
#             "computer engineering", "computer technology", "information technology",
#         }:
#             return f"{deg} {field}"
#     if " in " in deg.lower():
#         return f"{deg} {field}"
#     return f"{deg} in {field}"


# def _education_sort_key(edu: Dict[str, str]) -> Tuple[int, int, str]:
#     """Current/higher education first; board exams (HSC/SSC) last."""
#     inst = (edu.get("institution") or "").lower()
#     deg = (edu.get("degree") or "").lower()
#     blob = f"{inst} {deg}"
#     if re.search(r'\b(hsc|ssc|cbse|icse|xii|class\s*12|class\s*10)\b', blob):
#         board = 2
#     else:
#         board = 0
#     end = edu.get("end_date") or ""
#     years = re.findall(r"\d{4}", end)
#     year_num = int(years[-1]) if years else 0
#     # Present / ongoing ranks highest
#     if re.search(r'present|current|ongoing', f"{edu.get('end_date','')} {edu.get('dates','')}", re.I):
#         year_num = 9999
#     return (board, -year_num, inst)


# # ---------------------------------------------------------------------------
# # ATS PDF Generator Class (Swapnil Supe Perfect Resume Design)
# # ---------------------------------------------------------------------------

# class ATSPdfGenerator:
#     """
#     Renders structured resume data into an ATS-friendly PDF following the
#     Swapnil Supe Perfect Resume layout.
#     """

#     PAGE_W = 612.0   # US Letter
#     PAGE_H = 792.0
#     MX     = 26.0    # Side margin (golden ~25.2)
#     MT     = 24.0    # Top margin
#     MB     = 18.0    # Bottom margin (no footer)

#     # Colors — matching golden PDF
#     C_NAME    = (0.0, 0.0, 0.0)
#     C_TEXT    = (0.0, 0.0, 0.0)
#     C_HEADER  = (55 / 255.0, 80 / 255.0, 120 / 255.0)   # #375078
#     C_RULE    = (183 / 255.0, 183 / 255.0, 183 / 255.0) # gray underline
#     C_MUTED   = (0.20, 0.20, 0.22)

#     COL_GAP = 14.0
#     BODY_FS = 9.0
#     HEAD_FS = 10.0
#     NAME_FS = 18.0
#     LH = 11.0

#     def __init__(self):
#         self.cw = self.PAGE_W - (2 * self.MX)
#         self.mid_x = self.PAGE_W / 2.0
#         self.col_w = (self.cw - self.COL_GAP) / 2.0

#     def generate_pdf(self, resume_data: Dict[str, Any]) -> bytes:
#         if not isinstance(resume_data, dict):
#             resume_data = {}

#         doc = fitz.open()
#         page = doc.new_page(width=self.PAGE_W, height=self.PAGE_H)
#         cw = self.cw
#         y = self.MT
#         candidate_name = "CANDIDATE NAME"

#         def ensure_space(needed: float) -> fitz.Page:
#             nonlocal page, y
#             if y + needed > self.PAGE_H - self.MB:
#                 page = doc.new_page(width=self.PAGE_W, height=self.PAGE_H)
#                 y = self.MT
#             return page

#         def draw_centered(text: str, fs: float = 9.0, fn: str = "helv",
#                           col: Any = None, space_after: float = 3.0):
#             nonlocal y
#             if col is None:
#                 col = self.C_TEXT
#             text = _clean_str(text)
#             if not text:
#                 return
#             ensure_space(fs + space_after + 2.0)
#             tw = fitz.get_text_length(text, fontname=fn, fontsize=fs)
#             x = max(self.MX, (self.PAGE_W - tw) / 2.0)
#             page.insert_text(fitz.Point(x, y + fs * 0.85), text,
#                              fontsize=fs, fontname=fn, color=col)
#             y += fs + space_after

#         def draw_header(title: str, with_rule: bool = True, keep_with: float = 0.0):
#             """Section header. keep_with reserves space so header is not orphaned alone."""
#             nonlocal y
#             title = _clean_str(title).upper()
#             if not title:
#                 return
#             header_h = 28.0 + max(0.0, keep_with)
#             ensure_space(header_h)
#             y += 5.0
#             page.insert_text(fitz.Point(self.MX, y + self.HEAD_FS * 0.85), title,
#                              fontsize=self.HEAD_FS, fontname="hebo", color=self.C_HEADER)
#             y += self.HEAD_FS + 2.0
#             if with_rule:
#                 page.draw_line(
#                     fitz.Point(self.MX - 2.0, y),
#                     fitz.Point(self.PAGE_W - self.MX + 2.0, y),
#                     color=self.C_RULE, width=0.6,
#                 )
#                 y += 4.0
#             else:
#                 y += 2.0

#         def draw_paragraph(text: str, fs: float = None, indent: float = 0.0,
#                            space_after: float = 3.0, fn: str = "helv", col: Any = None):
#             nonlocal y
#             if fs is None:
#                 fs = self.BODY_FS
#             if col is None:
#                 col = self.C_TEXT
#             text = _clean_str(text)
#             if not text:
#                 return
#             max_w = cw - indent
#             lines = _wrap_text_lines(text, fs=fs, max_w=max_w, fn=fn)
#             needed = len(lines) * self.LH + space_after
#             ensure_space(needed)
#             for l in lines:
#                 page.insert_text(fitz.Point(self.MX + indent, y + fs * 0.85), l,
#                                  fontsize=fs, fontname=fn, color=col)
#                 y += self.LH
#             y += space_after

#         def draw_bullet(text: str, indent: float = 8.0, space_after: float = 1.5,
#                         max_width: float = None, x_left: float = None):
#             """Single-column bullet. Returns height used (for 2-col pairing)."""
#             nonlocal y
#             text = _clean_str(text)
#             if not text or text.lower() in ('*', '•', '-', 'bullet'):
#                 return 0.0

#             x0 = self.MX if x_left is None else x_left
#             mw = (cw - indent - 10.0) if max_width is None else max_width
#             lines = _wrap_text_lines(text, fs=self.BODY_FS, max_w=mw, fn="helv")
#             if not lines:
#                 return 0.0

#             needed = len(lines) * self.LH + space_after
#             ensure_space(needed)

#             bx = x0 + indent
#             tx = bx + 8.0
#             page.insert_text(fitz.Point(bx, y + self.BODY_FS * 0.85), "*",
#                              fontsize=self.BODY_FS, fontname="hebo", color=self.C_TEXT)
#             for l in lines:
#                 page.insert_text(fitz.Point(tx, y + self.BODY_FS * 0.85), l,
#                                  fontsize=self.BODY_FS, fontname="helv", color=self.C_TEXT)
#                 y += self.LH
#             y += space_after
#             return needed

#         def measure_bullet_height(text: str, max_width: float) -> float:
#             text = _clean_str(text)
#             if not text:
#                 return 0.0
#             lines = _wrap_text_lines(text, fs=self.BODY_FS, max_w=max_width, fn="helv")
#             return len(lines) * self.LH + 1.5

#         def draw_bullet_at(text: str, x_left: float, y_pos: float, max_width: float) -> float:
#             """Draw bullet at absolute y; returns new y after drawing."""
#             text = _clean_str(text)
#             if not text:
#                 return y_pos
#             lines = _wrap_text_lines(text, fs=self.BODY_FS, max_w=max_width, fn="helv")
#             bx = x_left
#             tx = bx + 8.0
#             cy = y_pos
#             page.insert_text(fitz.Point(bx, cy + self.BODY_FS * 0.85), "*",
#                              fontsize=self.BODY_FS, fontname="hebo", color=self.C_TEXT)
#             for l in lines:
#                 page.insert_text(fitz.Point(tx, cy + self.BODY_FS * 0.85), l,
#                                  fontsize=self.BODY_FS, fontname="helv", color=self.C_TEXT)
#                 cy += self.LH
#             return cy + 1.5

#         # ── 1. Header ────────────────────────────────────────────────────────
#         profile = resume_data.get("profile") if isinstance(resume_data.get("profile"), dict) else {}
#         name = (
#             _get_val(resume_data, "candidate_name")
#             or _get_val(profile, "name")
#             or "CANDIDATE NAME"
#         ).upper()
#         candidate_name = name

#         email = _get_val(resume_data, "email") or _get_val(profile, "email")
#         phone = _get_val(resume_data, "phone") or _get_val(profile, "phone")
#         loc = _get_val(resume_data, "location") or _get_val(profile, "location")
#         github = _get_val(resume_data, "github_url") or _get_val(profile, "github")
#         linkedin = _get_val(resume_data, "linkedin_url") or _get_val(profile, "linkedin")
#         portfolio = _get_val(resume_data, "portfolio_url") or _get_val(profile, "portfolio")

#         draw_centered(name, fs=self.NAME_FS, fn="hebo", col=self.C_NAME, space_after=4.0)

#         # Contact: email  |  phone   (two spaces around |)  — location optional trailing
#         contact_parts = [p for p in [email, phone] if p]
#         if loc and not contact_parts:
#             contact_parts = [loc]
#         elif loc and contact_parts:
#             # Golden contact line is email | phone only; keep location if no phone/email gap
#             pass
#         if contact_parts:
#             draw_centered("  |  ".join(contact_parts), fs=self.BODY_FS, fn="helv",
#                           col=self.C_TEXT, space_after=2.5)

#         links_parts = []
#         if linkedin:
#             links_parts.append(f"LinkedIn: {_strip_url(linkedin)}")
#         if github:
#             links_parts.append(f"GitHub: {_strip_url(github)}")
#         if portfolio:
#             links_parts.append(f"Portfolio: {_strip_url(portfolio)}")
#         if links_parts:
#             draw_centered("  |  ".join(links_parts), fs=self.BODY_FS, fn="helv",
#                           col=self.C_TEXT, space_after=2.0)

#         y += 2.0

#         # ── 2. PROFILE ───────────────────────────────────────────────────────
#         summary = _get_val(resume_data, "summary") or _get_val(profile, "summary")
#         if summary:
#             draw_header("PROFILE")
#             draw_paragraph(summary, fs=self.BODY_FS, space_after=2.0)

#         # ── 3. TECHNICAL SKILLS (2-column grid) ───────────────────────────────
#         skill_rows = self._collect_skill_rows(resume_data)
#         if skill_rows:
#             draw_header("TECHNICAL SKILLS")
#             # Pair into (left, right) rows
#             pairs: List[Tuple[Optional[Tuple[str, str]], Optional[Tuple[str, str]]]] = []
#             for i in range(0, len(skill_rows), 2):
#                 left = skill_rows[i]
#                 right = skill_rows[i + 1] if i + 1 < len(skill_rows) else None
#                 pairs.append((left, right))

#             left_x = self.MX
#             right_x = self.mid_x + 1.0
#             label_fs = self.BODY_FS
#             item_max_left = self.col_w - 4.0
#             item_max_right = self.col_w - 4.0

#             for left, right in pairs:
#                 # Measure heights for both columns (label + wrapped items)
#                 def _block_lines(pair: Optional[Tuple[str, str]], max_w: float) -> List[Tuple[str, str, str]]:
#                     """Return list of (font, text, kind) drawing ops for one skill cell."""
#                     if not pair:
#                         return []
#                     label, items = pair
#                     prefix = f"{label}: "
#                     # First line tries label+items; wrap rest under column
#                     full = prefix + items
#                     # Draw label bold + items on first line, wrap remaining as regular
#                     ops: List[Tuple[str, str, str]] = []
#                     # Use wrapping on full string then re-attach bold label on line 0
#                     words = items.split()
#                     # First line capacity after label
#                     label_w = fitz.get_text_length(prefix, fontname="hebo", fontsize=label_fs)
#                     first_max = max(20.0, max_w - label_w)
#                     curr = []
#                     first_line_items = ""
#                     rest_words = []
#                     placed_first = False
#                     for w in words:
#                         cand = " ".join(curr + [w])
#                         if fitz.get_text_length(cand, fontname="helv", fontsize=label_fs) <= first_max:
#                             curr.append(w)
#                         else:
#                             if not placed_first:
#                                 first_line_items = " ".join(curr)
#                                 placed_first = True
#                                 curr = [w]
#                             else:
#                                 rest_words.append(" ".join(curr))
#                                 curr = [w]
#                     if curr:
#                         if not placed_first:
#                             first_line_items = " ".join(curr)
#                         else:
#                             rest_words.append(" ".join(curr))

#                     ops.append(("hebo+helv", prefix, first_line_items))
#                     for rw in rest_words:
#                         for wl in _wrap_text_lines(rw, fs=label_fs, max_w=max_w, fn="helv"):
#                             ops.append(("helv", wl, ""))
#                     return ops

#                 left_ops = _block_lines(left, item_max_left)
#                 right_ops = _block_lines(right, item_max_right)
#                 n_lines = max(len(left_ops), len(right_ops), 1)
#                 ensure_space(n_lines * self.LH + 2.0)
#                 row_y = y

#                 def _paint(ops, x0):
#                     cy = row_y
#                     for kind, a, b in ops:
#                         if kind == "hebo+helv":
#                             page.insert_text(fitz.Point(x0, cy + label_fs * 0.85), a,
#                                              fontsize=label_fs, fontname="hebo", color=self.C_TEXT)
#                             lw = fitz.get_text_length(a, fontname="hebo", fontsize=label_fs)
#                             if b:
#                                 page.insert_text(fitz.Point(x0 + lw, cy + label_fs * 0.85), b,
#                                                  fontsize=label_fs, fontname="helv", color=self.C_TEXT)
#                         else:
#                             page.insert_text(fitz.Point(x0, cy + label_fs * 0.85), a,
#                                              fontsize=label_fs, fontname="helv", color=self.C_TEXT)
#                         cy += self.LH
#                     return cy

#                 y_l = _paint(left_ops, left_x) if left_ops else row_y
#                 y_r = _paint(right_ops, right_x) if right_ops else row_y
#                 y = max(y_l, y_r) + 1.0

#         # ── 4. PROJECTS ──────────────────────────────────────────────────────
#         proj_list = resume_data.get("projects") or []
#         if isinstance(proj_list, list) and proj_list:
#             drawn = False
#             for proj in proj_list:
#                 if not isinstance(proj, dict):
#                     continue
#                 pname = _get_val(proj, "name", "title")
#                 if not pname or pname.lower() in ('*', '•', '-', 'project', 'projects', '[github]'):
#                     continue
#                 if not drawn:
#                     draw_header("PROJECTS")
#                     drawn = True

#                 purl = _get_val(proj, "github_url", "url", "live_url")
#                 subtitle = _get_val(proj, "subtitle", "tagline")
#                 title = pname
#                 if subtitle and subtitle.lower() not in title.lower():
#                     title = f"{pname} - {subtitle}"

#                 ensure_space(self.LH + 2.0)
#                 page.insert_text(fitz.Point(self.MX, y + self.BODY_FS * 0.85), title,
#                                  fontsize=self.BODY_FS, fontname="hebo", color=self.C_NAME)
#                 if purl:
#                     link_txt = f"[{_strip_url(purl)}]"
#                     # Only show short marker if room; skip long URLs to avoid clutter
#                     if fitz.get_text_length(link_txt, fontname="helv", fontsize=8.0) < 160:
#                         tw = fitz.get_text_length(link_txt, fontname="helv", fontsize=8.0)
#                         page.insert_text(
#                             fitz.Point(self.PAGE_W - self.MX - tw, y + self.BODY_FS * 0.85),
#                             link_txt, fontsize=8.0, fontname="helv", color=self.C_MUTED,
#                         )
#                 y += self.LH

#                 techs = _ensure_list(proj.get("technologies") or proj.get("tech_stack"))
#                 if techs:
#                     draw_paragraph(", ".join(techs), fs=self.BODY_FS, space_after=1.0, fn="heit")

#                 desc = _get_val(proj, "description")
#                 bullets = _ensure_list(proj.get("highlights") or proj.get("bullets"))
#                 if desc and desc not in bullets:
#                     # Prefer structured bullets; include desc only if no bullets
#                     if not bullets:
#                         draw_bullet(desc, indent=6.0)
#                 for b in bullets:
#                     draw_bullet(b, indent=6.0)

#                 y += 2.0

#         # ── 5. EXPERIENCE (title full-width; bullets in 2 columns) ────────────
#         exp_list = resume_data.get("experience") or []
#         if isinstance(exp_list, list) and exp_list:
#             drawn = False
#             for exp in exp_list:
#                 exp = _coerce_to_dict(exp)
#                 if not exp:
#                     continue
#                 role = _get_val(exp, "role", "title", default="")
#                 comp = _get_val(exp, "company", "organization")
#                 if _is_placeholder_experience(role, comp):
#                     continue
#                 if role.lower() in ('*', '•', '-', 'bullet', 'experience'):
#                     continue
#                 if not drawn:
#                     draw_header("EXPERIENCE")
#                     drawn = True

#                 dates = _get_val(exp, "dates", "period")
#                 if not dates:
#                     start = _get_val(exp, "start_date")
#                     end = _get_val(exp, "end_date")
#                     if start and end:
#                         dates = f"{start} - {end}"
#                     elif start:
#                         dates = f"{start} - Present"
#                     elif end:
#                         dates = end

#                 # Golden: "Role — Company | dates"
#                 if role and comp:
#                     title_line = f"{role} - {comp}"
#                 else:
#                     title_line = role or comp
#                 if dates:
#                     title_line = f"{title_line} | {dates}"

#                 ensure_space(self.LH + 2.0)
#                 page.insert_text(fitz.Point(self.MX, y + self.BODY_FS * 0.85), title_line,
#                                  fontsize=self.BODY_FS, fontname="hebo", color=self.C_NAME)
#                 y += self.LH + 1.0

#                 bullets = _ensure_list(
#                     exp.get("highlights") or exp.get("bullets")
#                     or exp.get("responsibilities") or exp.get("description")
#                 )
#                 # Single-column bullets (stable ATS layout; avoids broken 2-col wraps)
#                 for b in bullets:
#                     draw_bullet(b, indent=6.0, space_after=1.2)

#                 techs = _ensure_list(exp.get("technologies") or exp.get("tech_stack"))
#                 if techs:
#                     draw_paragraph(", ".join(techs), fs=8.5, indent=6.0, space_after=2.0, fn="heit")
#                 y += 1.5

#         # ── 6. EDUCATION (compact single lines — recover years/GPA/college) ───
#         edu_list = resume_data.get("education") or []
#         normalized_edu: List[Dict[str, str]] = []
#         if isinstance(edu_list, list):
#             for edu in edu_list:
#                 norm = _normalize_education_item(edu)
#                 if norm and not _is_junk_education(norm):
#                     normalized_edu.append(norm)
#             # De-dupe by institution(+degree) keeping the richest entry
#             deduped: List[Dict[str, str]] = []
#             seen_keys = set()
#             for edu in normalized_edu:
#                 key = (
#                     _clean_str(edu.get("institution")).lower(),
#                     _clean_str(edu.get("degree")).lower(),
#                 )
#                 if key in seen_keys and key != ("", ""):
#                     # Prefer entry that has GPA/dates
#                     for i, prev in enumerate(deduped):
#                         pk = (
#                             _clean_str(prev.get("institution")).lower(),
#                             _clean_str(prev.get("degree")).lower(),
#                         )
#                         if pk == key:
#                             prev_score = bool(prev.get("gpa")) + bool(prev.get("start_date") or prev.get("end_date"))
#                             new_score = bool(edu.get("gpa")) + bool(edu.get("start_date") or edu.get("end_date"))
#                             if new_score > prev_score:
#                                 deduped[i] = edu
#                             break
#                     continue
#                 seen_keys.add(key)
#                 deduped.append(edu)
#             normalized_edu = sorted(deduped, key=_education_sort_key)

#         if normalized_edu:
#             drawn = False
#             for edu in normalized_edu:
#                 school = _clean_str(edu.get("institution"))
#                 deg = _clean_str(edu.get("degree"))
#                 field = _clean_str(edu.get("field_of_study"))
#                 degree_display = _format_degree_display(deg, field)

#                 # Avoid "School - School" when board exam sets both institution & degree to HSC/SSC
#                 if school and degree_display and school.lower() == degree_display.lower():
#                     degree_display = ""

#                 dates = _clean_str(edu.get("dates"))
#                 if not dates:
#                     start = _clean_str(edu.get("start_date"))
#                     end = _clean_str(edu.get("end_date"))
#                     if start and end:
#                         dates = f"{start}-{end}" if len(start) <= 4 and len(end) <= 4 else f"{start} - {end}"
#                     elif end:
#                         dates = end
#                     elif start:
#                         dates = start

#                 gpa_label = _format_gpa_label(edu.get("gpa") or "")

#                 if not school and not degree_display:
#                     continue
#                 if not drawn:
#                     # Keep header with first education line (prevent orphan header / footer clash)
#                     draw_header("EDUCATION", keep_with=self.LH + 4.0)
#                     drawn = True

#                 # Golden: School — Degree | score | years
#                 # Board: HSC - 46.31%
#                 is_board = bool(re.search(r'\b(hsc|ssc|cbse|icse)\b', f"{school} {degree_display}", re.I))
#                 if is_board and gpa_label and school:
#                     line = f"{school} - {gpa_label}"
#                 else:
#                     parts = []
#                     if school and degree_display:
#                         parts.append(f"{school} - {degree_display}")
#                     elif school:
#                         parts.append(school)
#                     else:
#                         parts.append(degree_display)
#                     if gpa_label:
#                         parts.append(gpa_label)
#                     if dates:
#                         parts.append(dates)
#                     line = " | ".join(parts) if len(parts) > 1 else parts[0]

#                 draw_paragraph(line, fs=self.BODY_FS, space_after=1.2)

#         # ── 7. Achievements (optional, not in golden but keep if present) ─────
#         ach_list = resume_data.get("achievements") or []
#         if isinstance(ach_list, list) and ach_list:
#             drawn = False
#             for ach in ach_list:
#                 if isinstance(ach, dict):
#                     title = _get_val(ach, "title", "name", "role")
#                     org = _get_val(ach, "organization", "institution", "company")
#                     det = _get_val(ach, "description", "details")
#                     date = _get_val(ach, "date", "year")
#                     top = f"{title} | {org}" if (title and org) else (title or org or det or "")
#                     if not top:
#                         continue
#                     if date:
#                         top += f" ({date})"
#                     if det and det != top and det not in top:
#                         top += f" - {det}"
#                     if not drawn:
#                         draw_header("ACHIEVEMENTS")
#                         drawn = True
#                     draw_bullet(top, indent=6.0)
#                 elif isinstance(ach, str) and _clean_str(ach):
#                     cl = _clean_str(ach)
#                     if cl.lower() not in ('*', '•', '-'):
#                         if not drawn:
#                             draw_header("ACHIEVEMENTS")
#                             drawn = True
#                         draw_bullet(cl, indent=6.0)

#         # ── 8. Custom sections (optional) ─────────────────────────────────────
#         custom_secs = resume_data.get("custom_sections") or []
#         if isinstance(custom_secs, list) and custom_secs:
#             for sec in custom_secs:
#                 if not isinstance(sec, dict):
#                     continue
#                 sec_title = _clean_str(_get_val(sec, "title", "heading", "name") or "ADDITIONAL")
#                 if "hobby" in sec_title.lower() or "interest" in sec_title.lower():
#                     continue
#                 items = sec.get("items") or sec.get("bullets") or []
#                 if isinstance(items, str):
#                     items = [it.strip() for it in items.splitlines() if it.strip()]
#                 if not isinstance(items, list) or not items:
#                     continue
#                 drawn = False
#                 for item in items:
#                     if isinstance(item, dict):
#                         it_text = _get_val(item, "text", "description", "name")
#                     else:
#                         it_text = _clean_str(str(item))
#                     if it_text and it_text.lower() not in ('*', '•', '-'):
#                         if not drawn:
#                             draw_header(sec_title)
#                             drawn = True
#                         draw_bullet(it_text, indent=6.0)

#         # ── 9. CERTIFICATIONS: I. ... II. ... (inline, no underline) ──────────
#         cert_lines = self._collect_cert_lines(resume_data)
#         if cert_lines:
#             ensure_space(self.LH * 2 + 8.0)
#             y += 6.0
#             label = "CERTIFICATIONS: "
#             page.insert_text(fitz.Point(self.MX, y + self.HEAD_FS * 0.85), label,
#                              fontsize=self.HEAD_FS, fontname="hebo", color=self.C_HEADER)
#             label_w = fitz.get_text_length(label, fontname="hebo", fontsize=self.HEAD_FS)

#             # Pack roman-numbered certs on one or more lines
#             x = self.MX + label_w
#             line_y = y
#             max_x = self.PAGE_W - self.MX
#             gap = "     "
#             for idx, cl in enumerate(cert_lines, start=1):
#                 chunk = f"{_roman(idx)}. {cl}"
#                 tw = fitz.get_text_length(chunk, fontname="helv", fontsize=self.BODY_FS)
#                 if x > self.MX + label_w and x + tw > max_x:
#                     line_y += self.LH
#                     ensure_space(self.LH + 2.0)
#                     x = self.MX + label_w
#                     y = max(y, line_y)
#                 page.insert_text(fitz.Point(x, line_y + self.BODY_FS * 0.85), chunk,
#                                  fontsize=self.BODY_FS, fontname="helv", color=self.C_TEXT)
#                 x += tw + fitz.get_text_length(gap, fontname="helv", fontsize=self.BODY_FS)
#             y = line_y + self.LH + 2.0

#         # ── 10. HOBBIES: inline ───────────────────────────────────────────────
#         hobbies = self._collect_hobbies(resume_data, custom_secs, candidate_name)
#         if hobbies:
#             ensure_space(self.LH + 8.0)
#             y += 3.0
#             label = "HOBBIES: "
#             page.insert_text(fitz.Point(self.MX, y + self.HEAD_FS * 0.85), label,
#                              fontsize=self.HEAD_FS, fontname="hebo", color=self.C_HEADER)
#             label_w = fitz.get_text_length(label, fontname="hebo", fontsize=self.HEAD_FS)
#             body = ", ".join(hobbies)
#             if not body.endswith("."):
#                 body += "."
#             # Wrap if needed
#             max_w = cw - label_w
#             lines = _wrap_text_lines(body, fs=self.BODY_FS, max_w=max_w, fn="helv")
#             if lines:
#                 page.insert_text(fitz.Point(self.MX + label_w, y + self.BODY_FS * 0.85), lines[0],
#                                  fontsize=self.BODY_FS, fontname="helv", color=self.C_TEXT)
#                 y += self.LH
#                 for extra in lines[1:]:
#                     ensure_space(self.LH)
#                     page.insert_text(fitz.Point(self.MX + label_w, y + self.BODY_FS * 0.85), extra,
#                                      fontsize=self.BODY_FS, fontname="helv", color=self.C_TEXT)
#                     y += self.LH

#         # No footer — keeps resume to one page and matches clean ATS export

#         try:
#             pdf_bytes = doc.tobytes(deflate=True)
#         except Exception:
#             pdf_bytes = doc.write(deflate=True)
#         doc.close()
#         return pdf_bytes

#     def _collect_skill_rows(self, resume_data: Dict[str, Any]) -> List[Tuple[str, str]]:
#         raw_skills = resume_data.get("skills") or resume_data.get("extracted_skills") or {}
#         skill_rows: List[Tuple[str, str]] = []

#         LABELS = [
#             ("technical", "Languages"),
#             ("languages", "Languages"),
#             ("frontend", "Frontend"),
#             ("frameworks", "Frontend"),
#             ("backend", "Backend"),
#             ("databases", "Databases"),
#             ("ai_ml", "AI / ML"),
#             ("aiml", "AI / ML"),
#             ("ml", "AI / ML"),
#             ("cybersecurity", "Cybersecurity"),
#             ("security", "Cybersecurity"),
#             ("cloud", "Cloud / DevOps"),
#             ("devops", "Cloud / DevOps"),
#             ("tools", "Tools"),
#             ("soft", "Professional Skills"),
#             ("other", "Other"),
#         ]

#         if isinstance(raw_skills, dict):
#             seen_labels = set()
#             # Prefer ordered known keys first
#             used_keys = set()
#             for key, label in LABELS:
#                 if key in used_keys:
#                     continue
#                 items = raw_skills.get(key)
#                 if items is None:
#                     continue
#                 used_keys.add(key)
#                 if label in seen_labels and key in ("frameworks", "languages", "devops", "aiml", "ml", "security"):
#                     # Merge into existing label row if duplicate
#                     pass
#                 clean_items: List[str] = []
#                 if isinstance(items, list):
#                     clean_items = [_clean_str(x) for x in items if _clean_str(x)]
#                 elif isinstance(items, str) and items.strip():
#                     clean_items = [_clean_str(items)]
#                 if not clean_items:
#                     continue
#                 # Merge into existing same label
#                 merged = False
#                 for i, (lab, existing) in enumerate(skill_rows):
#                     if lab == label:
#                         combined = existing + ", " + ", ".join(clean_items)
#                         skill_rows[i] = (lab, combined)
#                         merged = True
#                         break
#                 if not merged:
#                     skill_rows.append((label, ", ".join(clean_items)))
#                     seen_labels.add(label)

#             # Any remaining custom keys
#             for k, items in raw_skills.items():
#                 if k in used_keys or k.startswith("_"):
#                     continue
#                 label = _clean_str(k).replace("_", " ").title() or "Other"
#                 clean_items = []
#                 if isinstance(items, list):
#                     clean_items = [_clean_str(x) for x in items if _clean_str(x)]
#                 elif isinstance(items, str) and items.strip():
#                     clean_items = [_clean_str(items)]
#                 if clean_items:
#                     skill_rows.append((label, ", ".join(clean_items)))

#         elif isinstance(raw_skills, list) and raw_skills:
#             clean_items = []
#             for s in raw_skills:
#                 if isinstance(s, dict):
#                     clean_items.extend([_clean_str(x) for x in s.get("skills", []) if _clean_str(x)])
#                 elif s:
#                     clean_items.append(_clean_str(s))
#             if clean_items:
#                 skill_rows.append(("Languages", ", ".join(clean_items[:40])))

#         return skill_rows

#     def _collect_cert_lines(self, resume_data: Dict[str, Any]) -> List[str]:
#         certs = resume_data.get("certifications") or []
#         out: List[str] = []
#         if not isinstance(certs, list):
#             return out
#         for c in certs:
#             if isinstance(c, dict):
#                 cname = _get_val(c, "name", "title")
#                 issuer = _get_val(c, "issuer", "authority")
#                 date = _get_val(c, "issue_date", "date", "year", "dates")
#                 if not cname:
#                     continue
#                 # Strip accidental roman/section prefixes from bad parses
#                 cname = re.sub(r'^(?:[IVXLC]+\.|CERTIFICATIONS?:)\s*', '', cname, flags=re.I).strip()
#                 issuer = re.sub(r'^(?:[IVXLC]+\.|CERTIFICATIONS?:)\s*', '', issuer, flags=re.I).strip()
#                 if not cname or cname.lower() in ("certifications", "hobbies", "education"):
#                     continue
#                 if issuer and issuer.lower() not in cname.lower():
#                     line = f"{issuer} - {cname}"
#                 else:
#                     line = cname
#                 if date:
#                     line += f" ({date})"
#                 # De-dupe near-identical lines
#                 if any(line.lower() == x.lower() or line.lower() in x.lower() or x.lower() in line.lower() for x in out):
#                     continue
#                 out.append(line)
#             elif isinstance(c, str) and _clean_str(c):
#                 cl = _clean_str(c)
#                 cl = re.sub(r'^(?:[IVXLC]+\.|CERTIFICATIONS?:)\s*', '', cl, flags=re.I).strip()
#                 if cl.lower() not in ('*', '•', '-', 'certifications', 'hobbies'):
#                     if not any(cl.lower() == x.lower() or cl.lower() in x.lower() for x in out):
#                         out.append(cl)
#         return out

#     def _collect_hobbies(self, resume_data: Dict[str, Any], custom_secs: Any, candidate_name: str = "") -> List[str]:
#         hobbies_list = resume_data.get("hobbies") or resume_data.get("interests") or []
#         if not hobbies_list and isinstance(custom_secs, list):
#             for sec in custom_secs:
#                 if isinstance(sec, dict) and (
#                     "hobby" in str(sec.get("title", "")).lower()
#                     or "interest" in str(sec.get("title", "")).lower()
#                 ):
#                     hobbies_list = sec.get("items") or []
#                     break

#         name_l = _clean_str(candidate_name).lower()
#         out: List[str] = []
#         if isinstance(hobbies_list, str) and hobbies_list.strip():
#             hobbies_list = [h.strip() for h in re.split(r'[\n;,•]+', hobbies_list) if h.strip()]
#         if isinstance(hobbies_list, list):
#             for h in hobbies_list:
#                 if isinstance(h, dict):
#                     h_val = _get_val(h, "name", "title", "hobby", "interest", "description")
#                 else:
#                     h_val = _clean_str(str(h))
#                 if not h_val or h_val.lower() in ('*', '•', '-'):
#                     continue
#                 h_val = h_val.rstrip(".")
#                 hl = h_val.lower()
#                 # Drop footer/name leakage and section labels
#                 if name_l and (hl == name_l or hl.replace(" ", "") == name_l.replace(" ", "")):
#                     continue
#                 if hl in ("candidate name", "candidate", "hobbies", "interests", "certifications"):
#                     continue
#                 if name_l and name_l in hl and len(hl.split()) <= 4:
#                     continue
#                 out.append(h_val)
#         return out


# pdf_generator = ATSPdfGenerator()


# def generate_pdf(resume_data: Dict[str, Any]) -> bytes:
#     """Module-level convenience wrapper for ATSPdfGenerator.generate_pdf."""
#     return pdf_generator.generate_pdf(resume_data)





























































# """
# ATS-Compliant PDF Generator — Swapnil Supe Perfect Resume Design.
# Renders clean, ATS-parseable resume PDFs matching the golden reference layout:

#   PROFILE → TECHNICAL SKILLS (2-col) → PROJECTS → EXPERIENCE (2-col bullets)
#   → EDUCATION (compact) → CERTIFICATIONS (inline I./II.) → HOBBIES (inline)

# Visual rules (from golden PDF):
# - US Letter, ~25pt side margins
# - Centered bold name (~19pt), centered contact, links line
# - Blue section headings rgb(55,80,120) with gray underline
# - Skills: 2-column Category: items grid
# - Projects: bold title, italic tech stack, bullets
# - Experience: bold title; bullets zig-zag in 2 columns
# - Education: School — Degree | score | years (single line)
# - Certs/Hobbies: inline labeled rows (no underline)
# - Footer: tiny centered candidate name
# """

# from typing import Dict, Any, List, Optional, Tuple
# import re
# import pymupdf as fitz

# try:
#     from app.parser.markdown_pipeline import parse_education_entry_line
# except ImportError:
#     try:
#         from backend.app.parser.markdown_pipeline import parse_education_entry_line
#     except ImportError:
#         parse_education_entry_line = None  # type: ignore


# # ---------------------------------------------------------------------------
# # Unicode & Character Normalization
# # ---------------------------------------------------------------------------

# _CHAR_REPLACEMENTS = {
#     "\u2014": " - ", "\u2013": " - ", "\u2012": " - ", "\u2015": " - ",
#     "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',
#     "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
#     "\u00a0": " ", "\t": "    ",
#     "\u2022": "*", "\u25cf": "*", "\u25aa": "*", "\u2023": "*",
#     "\u2219": "*", "\u00b7": "*", "\u2756": "*", "\u25c6": "*", "\u25c8": "*",
#     "\u2026": "...",
#     "\u2192": "->", "\u21d2": "=>", "\u2794": "->", "\u27a4": "->",
#     "\u2713": "[x]", "\u2714": "[x]", "\u2717": "[ ]", "\u2718": "[ ]",
#     "\u200b": "", "\ufeff": "",
# }

# _ROMAN = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
#           "XI", "XII", "XIII", "XIV", "XV")


# def _clean_str(val: Any) -> str:
#     """Sanitize, normalize unicode characters, and strip leading bullet artifacts."""
#     if val is None:
#         return ""
#     s = str(val).strip()
#     if not s:
#         return ""

#     s = re.sub(r'^[❖●•\-\*\s]+', '', s)

#     for orig, rep in _CHAR_REPLACEMENTS.items():
#         s = s.replace(orig, rep)

#     # Filter non-latin characters that standard Type-1 Helvetica cannot render
#     clean = []
#     for ch in s:
#         code = ord(ch)
#         if code < 128 or (160 <= code <= 255):
#             clean.append(ch)
#         else:
#             clean.append(" ")
#     return re.sub(r'\s+', ' ', ''.join(clean)).strip()


# def _ensure_list(val: Any) -> List[str]:
#     """Ensure highlight/bullet inputs are cleanly parsed into a list of strings."""
#     if val is None:
#         return []
#     if isinstance(val, list):
#         out = []
#         for item in val:
#             if isinstance(item, dict):
#                 text = item.get("text") or item.get("name") or str(item)
#                 cleaned = _clean_str(text)
#                 if cleaned and cleaned.lower() not in ('*', '•', '-', 'bullet'):
#                     out.append(cleaned)
#             elif item is not None:
#                 cleaned = _clean_str(str(item))
#                 if cleaned and cleaned.lower() not in ('*', '•', '-', 'bullet'):
#                     out.append(cleaned)
#         return out
#     if isinstance(val, (str, bytes)):
#         s = _clean_str(str(val))
#         if not s:
#             return []
#         if "\n" in s:
#             return [
#                 _clean_str(line) for line in s.splitlines()
#                 if _clean_str(line) and _clean_str(line).lower() not in ('*', '•', '-', 'bullet')
#             ]
#         return [s]
#     cleaned = _clean_str(str(val))
#     return [cleaned] if cleaned else []


# def _get_val(d: Any, *keys: str, default: str = "") -> str:
#     """Fetch the first non-empty string value across multiple potential keys."""
#     if not isinstance(d, dict):
#         return default
#     for k in keys:
#         v = d.get(k)
#         if v is not None:
#             sv = _clean_str(v)
#             if sv:
#                 return sv
#     return default


# def _wrap_text_lines(text: str, fs: float, max_w: float, fn: str = "helv") -> List[str]:
#     """Wrap text into lines accurately using fitz.get_text_length."""
#     if not text:
#         return []
#     words = text.split()
#     if not words:
#         return []

#     lines = []
#     curr = []
#     for w in words:
#         cand = " ".join(curr + [w])
#         if fitz.get_text_length(cand, fontname=fn, fontsize=fs) <= max_w:
#             curr.append(w)
#         else:
#             if curr:
#                 lines.append(" ".join(curr))
#             curr = [w]
#     if curr:
#         lines.append(" ".join(curr))
#     return lines if lines else [text]


# def _strip_url(url: str) -> str:
#     u = _clean_str(url)
#     u = re.sub(r'^https?://', '', u, flags=re.I).rstrip("/")
#     return u


# def _roman(n: int) -> str:
#     if 1 <= n <= len(_ROMAN):
#         return _ROMAN[n - 1]
#     return str(n)


# def _format_gpa_label(gpa: str) -> str:
#     """Normalize GPA/percentage for golden education lines."""
#     gpa = _clean_str(gpa)
#     if not gpa:
#         return ""
#     nums = re.findall(r"[\d.]+", gpa)
#     if "%" in gpa:
#         return gpa if gpa.endswith("%") else f"{gpa}%"
#     if nums:
#         try:
#             val = float(nums[0])
#             if val > 10:
#                 return gpa if "%" in gpa else f"{nums[0]}%"
#         except ValueError:
#             pass
#     if "cgpa" in gpa.lower() or "gpa" in gpa.lower():
#         return gpa
#     return f"{gpa} CGPA"


# def _coerce_to_dict(item: Any) -> Optional[Dict[str, Any]]:
#     """Accept dicts, pydantic models, or skip junk."""
#     if item is None:
#         return None
#     if isinstance(item, dict):
#         return item
#     if hasattr(item, "model_dump"):
#         try:
#             return item.model_dump()
#         except Exception:
#             pass
#     if hasattr(item, "dict"):
#         try:
#             return item.dict()
#         except Exception:
#             pass
#     return None


# _PLACEHOLDER_ROLES = {
#     "role", "title", "position", "job title", "job role", "designation",
# }
# _PLACEHOLDER_COMPS = {
#     "company", "organization", "employer", "org", "company name",
# }


# def _is_placeholder_experience(role: str, comp: str) -> bool:
#     r = (role or "").strip().lower()
#     c = (comp or "").strip().lower()
#     if not r and not c:
#         return True
#     if r in _PLACEHOLDER_ROLES and (not c or c in _PLACEHOLDER_COMPS):
#         return True
#     if c in _PLACEHOLDER_COMPS and (not r or r in _PLACEHOLDER_ROLES):
#         return True
#     if r in _PLACEHOLDER_ROLES and c in _PLACEHOLDER_COMPS:
#         return True
#     return False


# def _normalize_education_item(edu: Any) -> Optional[Dict[str, str]]:
#     """
#     Recover institution / degree / GPA / years even when the parser merged them
#     into a single institution string (common cause of missing college years).
#     """
#     if isinstance(edu, str):
#         raw_line = _clean_str(edu)
#         base: Dict[str, Any] = {}
#     else:
#         base = _coerce_to_dict(edu) or {}
#         if not base and not isinstance(edu, dict):
#             return None
#         raw_line = ""

#     school = _get_val(base, "institution", "school", "university", "college", "institute", "academy")
#     deg = _get_val(base, "degree", "qualification")
#     field = _get_val(base, "field_of_study", "major", "stream", "branch")
#     start = _get_val(base, "start_date")
#     end = _get_val(base, "end_date", "year", "graduation_year")
#     dates = _get_val(base, "dates", "period")
#     gpa = _get_val(base, "gpa", "percentage", "score", "cgpa", "grade")

#     # Rebuild a golden-style line so the shared parser can split merged fields
#     if not raw_line:
#         if school and deg:
#             if field and field.lower() not in deg.lower():
#                 deg_part = f"{deg} in {field}" if "in" not in deg.lower() else f"{deg} {field}"
#             else:
#                 deg_part = deg
#             raw_line = f"{school} - {deg_part}"
#         elif school:
#             raw_line = school
#         elif deg:
#             raw_line = f"{deg} in {field}" if field else deg
#         meta = []
#         if gpa:
#             meta.append(gpa)
#         if dates:
#             meta.append(dates)
#         elif start and end:
#             meta.append(f"{start}-{end}")
#         elif end:
#             meta.append(end)
#         elif start:
#             meta.append(start)
#         if raw_line and meta:
#             raw_line = f"{raw_line} | {' | '.join(meta)}"

#     parsed: Dict[str, str] = {}
#     if raw_line and parse_education_entry_line is not None:
#         try:
#             parsed = parse_education_entry_line(raw_line) or {}
#         except Exception:
#             parsed = {}

#     # If institution looks like a full golden line, prefer parser split
#     school_looks_merged = bool(
#         school and (
#             " | " in school
#             or re.search(r'\s[-–—]\s', school)
#             or re.search(r'\b(20\d{2})\b', school)
#             or re.search(r'\b\d{1,2}(?:\.\d+)?\s*%|\bcgpa\b', school, re.I)
#         )
#     )
#     if school_looks_merged and parse_education_entry_line is not None:
#         try:
#             parsed_school = parse_education_entry_line(school) or {}
#             if parsed_school.get("institution"):
#                 for k, v in parsed_school.items():
#                     if v and not parsed.get(k):
#                         parsed[k] = v
#                 if parsed_school.get("institution"):
#                     school = _clean_str(parsed_school.get("institution"))
#                 if parsed_school.get("degree") and not deg:
#                     deg = _clean_str(parsed_school.get("degree"))
#                 if parsed_school.get("field_of_study") and not field:
#                     field = _clean_str(parsed_school.get("field_of_study"))
#                 if parsed_school.get("gpa") and not gpa:
#                     gpa = _clean_str(parsed_school.get("gpa"))
#                 if parsed_school.get("start_date") and not start:
#                     start = _clean_str(parsed_school.get("start_date"))
#                 if parsed_school.get("end_date") and not end:
#                     end = _clean_str(parsed_school.get("end_date"))
#         except Exception:
#             pass

#     # Structured fields win when present; parser fills gaps (esp. years/GPA)
#     out = {
#         "institution": school or _clean_str(parsed.get("institution")),
#         "degree": deg or _clean_str(parsed.get("degree")),
#         "field_of_study": field or _clean_str(parsed.get("field_of_study")),
#         "start_date": start or _clean_str(parsed.get("start_date")),
#         "end_date": end or _clean_str(parsed.get("end_date")),
#         "gpa": gpa or _clean_str(parsed.get("gpa")),
#         "dates": dates,
#     }

#     # If institution still contains "School - Degree" and degree empty, split again
#     inst = out["institution"]
#     if inst and not out["degree"] and re.search(r'\s[-–—]\s', inst):
#         if parse_education_entry_line is not None:
#             try:
#                 again = parse_education_entry_line(inst) or {}
#                 if again.get("institution"):
#                     out["institution"] = _clean_str(again.get("institution"))
#                 if again.get("degree") and not out["degree"]:
#                     out["degree"] = _clean_str(again.get("degree"))
#                 if again.get("field_of_study") and not out["field_of_study"]:
#                     out["field_of_study"] = _clean_str(again.get("field_of_study"))
#                 if again.get("gpa") and not out["gpa"]:
#                     out["gpa"] = _clean_str(again.get("gpa"))
#                 if again.get("start_date") and not out["start_date"]:
#                     out["start_date"] = _clean_str(again.get("start_date"))
#                 if again.get("end_date") and not out["end_date"]:
#                     out["end_date"] = _clean_str(again.get("end_date"))
#             except Exception:
#                 pass

#     if not out["institution"] and not out["degree"] and not out["field_of_study"]:
#         return None
#     return out


# def _is_junk_education(edu: Dict[str, str]) -> bool:
#     """Drop mis-parsed CERTIFICATIONS / HOBBIES / footer-name rows from education."""
#     inst = (edu.get("institution") or "").strip()
#     deg = (edu.get("degree") or "").strip()
#     field = (edu.get("field_of_study") or "").strip()
#     blob = f"{inst} {deg} {field}".strip().lower()
#     if not blob:
#         return True
#     if re.search(r'\b(certifications?|hobbies|interests)\s*:', blob):
#         return True
#     if re.match(r'^(certifications?|hobbies|interests)\b', blob):
#         return True
#     # Footer / name leakage into education
#     if re.match(r'^[a-z]+\s+[a-z]+$', deg.lower()) and not inst:
#         return True
#     if deg.lower() in {"swapnil supe", "candidate name", "candidate"}:
#         return True
#     if "hobbies:" in inst.lower() or "certifications:" in inst.lower():
#         return True
#     return False


# def _format_degree_display(deg: str, field: str) -> str:
#     deg = _clean_str(deg)
#     field = _clean_str(field)
#     if not deg:
#         return field
#     if not field or field.lower() in deg.lower():
#         return deg
#     # "B.Tech Computer" + "Engineering" → "B.Tech Computer Engineering"
#     if re.search(r'\b(b\.?tech|b\.?e\.?|m\.?tech|m\.?e\.?|diploma|bachelor|master|b\.?sc|m\.?sc)\b', deg, re.I):
#         if field.lower() in {
#             "engineering", "technology", "science", "arts", "commerce",
#             "computer engineering", "computer technology", "information technology",
#         }:
#             return f"{deg} {field}"
#     if " in " in deg.lower():
#         return f"{deg} {field}"
#     return f"{deg} in {field}"


# def _education_sort_key(edu: Dict[str, str]) -> Tuple[int, int, str]:
#     """Current/higher education first; board exams (HSC/SSC) last."""
#     inst = (edu.get("institution") or "").lower()
#     deg = (edu.get("degree") or "").lower()
#     blob = f"{inst} {deg}"
#     if re.search(r'\b(hsc|ssc|cbse|icse|xii|class\s*12|class\s*10)\b', blob):
#         board = 2
#     else:
#         board = 0
#     end = edu.get("end_date") or ""
#     years = re.findall(r"\d{4}", end)
#     year_num = int(years[-1]) if years else 0
#     # Present / ongoing ranks highest
#     if re.search(r'present|current|ongoing', f"{edu.get('end_date','')} {edu.get('dates','')}", re.I):
#         year_num = 9999
#     return (board, -year_num, inst)


# # ---------------------------------------------------------------------------
# # ATS PDF Generator Class (Swapnil Supe Perfect Resume Design)
# # ---------------------------------------------------------------------------

# class ATSPdfGenerator:
#     """
#     Renders structured resume data into an ATS-friendly PDF following the
#     Swapnil Supe Perfect Resume layout.
#     """

#     PAGE_W = 612.0   # US Letter
#     PAGE_H = 792.0
#     MX     = 26.0    # Side margin (golden ~25.2)
#     MT     = 24.0    # Top margin
#     MB     = 18.0    # Bottom margin (no footer)

#     # Colors — matching golden PDF
#     C_NAME    = (0.0, 0.0, 0.0)
#     C_TEXT    = (0.0, 0.0, 0.0)
#     C_HEADER  = (55 / 255.0, 80 / 255.0, 120 / 255.0)   # #375078
#     C_RULE    = (183 / 255.0, 183 / 255.0, 183 / 255.0) # gray underline
#     C_MUTED   = (0.20, 0.20, 0.22)

#     COL_GAP = 14.0
#     BODY_FS = 9.0
#     HEAD_FS = 10.0
#     NAME_FS = 18.0
#     LH = 11.0

#     def __init__(self):
#         self.cw = self.PAGE_W - (2 * self.MX)
#         self.mid_x = self.PAGE_W / 2.0
#         self.col_w = (self.cw - self.COL_GAP) / 2.0

#     def generate_pdf(self, resume_data: Dict[str, Any]) -> bytes:
#         if not isinstance(resume_data, dict):
#             resume_data = {}

#         doc = fitz.open()
#         page = doc.new_page(width=self.PAGE_W, height=self.PAGE_H)
#         cw = self.cw
#         y = self.MT
#         candidate_name = "CANDIDATE NAME"

#         def ensure_space(needed: float) -> fitz.Page:
#             nonlocal page, y
#             if y + needed > self.PAGE_H - self.MB:
#                 page = doc.new_page(width=self.PAGE_W, height=self.PAGE_H)
#                 y = self.MT
#             return page

#         def draw_centered(text: str, fs: float = 9.0, fn: str = "helv",
#                           col: Any = None, space_after: float = 3.0):
#             nonlocal y
#             if col is None:
#                 col = self.C_TEXT
#             text = _clean_str(text)
#             if not text:
#                 return
#             ensure_space(fs + space_after + 2.0)
#             tw = fitz.get_text_length(text, fontname=fn, fontsize=fs)
#             x = max(self.MX, (self.PAGE_W - tw) / 2.0)
#             page.insert_text(fitz.Point(x, y + fs * 0.85), text,
#                              fontsize=fs, fontname=fn, color=col)
#             y += fs + space_after

#         def draw_header(title: str, with_rule: bool = True, keep_with: float = 0.0):
#             """Section header. keep_with reserves space so header is not orphaned alone."""
#             nonlocal y
#             title = _clean_str(title).upper()
#             if not title:
#                 return
#             header_h = 28.0 + max(0.0, keep_with)
#             ensure_space(header_h)
#             y += 5.0
#             page.insert_text(fitz.Point(self.MX, y + self.HEAD_FS * 0.85), title,
#                              fontsize=self.HEAD_FS, fontname="hebo", color=self.C_HEADER)
#             y += self.HEAD_FS + 2.0
#             if with_rule:
#                 page.draw_line(
#                     fitz.Point(self.MX - 2.0, y),
#                     fitz.Point(self.PAGE_W - self.MX + 2.0, y),
#                     color=self.C_RULE, width=0.6,
#                 )
#                 y += 4.0
#             else:
#                 y += 2.0

#         def draw_paragraph(text: str, fs: float = None, indent: float = 0.0,
#                            space_after: float = 3.0, fn: str = "helv", col: Any = None):
#             nonlocal y
#             if fs is None:
#                 fs = self.BODY_FS
#             if col is None:
#                 col = self.C_TEXT
#             text = _clean_str(text)
#             if not text:
#                 return
#             max_w = cw - indent
#             lines = _wrap_text_lines(text, fs=fs, max_w=max_w, fn=fn)
#             needed = len(lines) * self.LH + space_after
#             ensure_space(needed)
#             for l in lines:
#                 page.insert_text(fitz.Point(self.MX + indent, y + fs * 0.85), l,
#                                  fontsize=fs, fontname=fn, color=col)
#                 y += self.LH
#             y += space_after

#         def draw_bullet(text: str, indent: float = 8.0, space_after: float = 1.5,
#                         max_width: float = None, x_left: float = None):
#             """Single-column bullet. Returns height used (for 2-col pairing)."""
#             nonlocal y
#             text = _clean_str(text)
#             if not text or text.lower() in ('*', '•', '-', 'bullet'):
#                 return 0.0

#             x0 = self.MX if x_left is None else x_left
#             mw = (cw - indent - 10.0) if max_width is None else max_width
#             lines = _wrap_text_lines(text, fs=self.BODY_FS, max_w=mw, fn="helv")
#             if not lines:
#                 return 0.0

#             needed = len(lines) * self.LH + space_after
#             ensure_space(needed)

#             bx = x0 + indent
#             tx = bx + 8.0
#             page.insert_text(fitz.Point(bx, y + self.BODY_FS * 0.85), "*",
#                              fontsize=self.BODY_FS, fontname="hebo", color=self.C_TEXT)
#             for l in lines:
#                 page.insert_text(fitz.Point(tx, y + self.BODY_FS * 0.85), l,
#                                  fontsize=self.BODY_FS, fontname="helv", color=self.C_TEXT)
#                 y += self.LH
#             y += space_after
#             return needed

#         def measure_bullet_height(text: str, max_width: float) -> float:
#             text = _clean_str(text)
#             if not text:
#                 return 0.0
#             lines = _wrap_text_lines(text, fs=self.BODY_FS, max_w=max_width, fn="helv")
#             return len(lines) * self.LH + 1.5

#         def draw_bullet_at(text: str, x_left: float, y_pos: float, max_width: float) -> float:
#             """Draw bullet at absolute y; returns new y after drawing."""
#             text = _clean_str(text)
#             if not text:
#                 return y_pos
#             lines = _wrap_text_lines(text, fs=self.BODY_FS, max_w=max_width, fn="helv")
#             bx = x_left
#             tx = bx + 8.0
#             cy = y_pos
#             page.insert_text(fitz.Point(bx, cy + self.BODY_FS * 0.85), "*",
#                              fontsize=self.BODY_FS, fontname="hebo", color=self.C_TEXT)
#             for l in lines:
#                 page.insert_text(fitz.Point(tx, cy + self.BODY_FS * 0.85), l,
#                                  fontsize=self.BODY_FS, fontname="helv", color=self.C_TEXT)
#                 cy += self.LH
#             return cy + 1.5

#         # ── 1. Header ────────────────────────────────────────────────────────
#         profile = resume_data.get("profile") if isinstance(resume_data.get("profile"), dict) else {}
#         name = (
#             _get_val(resume_data, "candidate_name")
#             or _get_val(profile, "name")
#             or "CANDIDATE NAME"
#         ).upper()
#         candidate_name = name

#         email = _get_val(resume_data, "email") or _get_val(profile, "email")
#         phone = _get_val(resume_data, "phone") or _get_val(profile, "phone")
#         loc = _get_val(resume_data, "location") or _get_val(profile, "location")
#         github = _get_val(resume_data, "github_url") or _get_val(profile, "github")
#         linkedin = _get_val(resume_data, "linkedin_url") or _get_val(profile, "linkedin")
#         portfolio = _get_val(resume_data, "portfolio_url") or _get_val(profile, "portfolio")

#         draw_centered(name, fs=self.NAME_FS, fn="hebo", col=self.C_NAME, space_after=4.0)

#         # Contact: email  |  phone   (two spaces around |)  — location optional trailing
#         contact_parts = [p for p in [email, phone] if p]
#         if loc and not contact_parts:
#             contact_parts = [loc]
#         elif loc and contact_parts:
#             # Golden contact line is email | phone only; keep location if no phone/email gap
#             pass
#         if contact_parts:
#             draw_centered("  |  ".join(contact_parts), fs=self.BODY_FS, fn="helv",
#                           col=self.C_TEXT, space_after=2.5)

#         links_parts = []
#         if linkedin:
#             links_parts.append(f"LinkedIn: {_strip_url(linkedin)}")
#         if github:
#             links_parts.append(f"GitHub: {_strip_url(github)}")
#         if portfolio:
#             links_parts.append(f"Portfolio: {_strip_url(portfolio)}")
#         if links_parts:
#             draw_centered("  |  ".join(links_parts), fs=self.BODY_FS, fn="helv",
#                           col=self.C_TEXT, space_after=2.0)

#         y += 2.0

#         # ── 2. PROFILE ───────────────────────────────────────────────────────
#         summary = _get_val(resume_data, "summary") or _get_val(profile, "summary")
#         if summary:
#             draw_header("PROFILE")
#             draw_paragraph(summary, fs=self.BODY_FS, space_after=2.0)

#         # ── 3. TECHNICAL SKILLS (2-column grid) ───────────────────────────────
#         skill_rows = self._collect_skill_rows(resume_data)
#         if skill_rows:
#             draw_header("TECHNICAL SKILLS")
#             # Pair into (left, right) rows
#             pairs: List[Tuple[Optional[Tuple[str, str]], Optional[Tuple[str, str]]]] = []
#             for i in range(0, len(skill_rows), 2):
#                 left = skill_rows[i]
#                 right = skill_rows[i + 1] if i + 1 < len(skill_rows) else None
#                 pairs.append((left, right))

#             left_x = self.MX
#             right_x = self.mid_x + 1.0
#             label_fs = self.BODY_FS
#             item_max_left = self.col_w - 4.0
#             item_max_right = self.col_w - 4.0

#             for left, right in pairs:
#                 # Measure heights for both columns (label + wrapped items)
#                 def _block_lines(pair: Optional[Tuple[str, str]], max_w: float) -> List[Tuple[str, str, str]]:
#                     """Return list of (font, text, kind) drawing ops for one skill cell."""
#                     if not pair:
#                         return []
#                     label, items = pair
#                     prefix = f"{label}: "
#                     # First line tries label+items; wrap rest under column
#                     full = prefix + items
#                     # Draw label bold + items on first line, wrap remaining as regular
#                     ops: List[Tuple[str, str, str]] = []
#                     # Use wrapping on full string then re-attach bold label on line 0
#                     words = items.split()
#                     # First line capacity after label
#                     label_w = fitz.get_text_length(prefix, fontname="hebo", fontsize=label_fs)
#                     first_max = max(20.0, max_w - label_w)
#                     curr = []
#                     first_line_items = ""
#                     rest_words = []
#                     placed_first = False
#                     for w in words:
#                         cand = " ".join(curr + [w])
#                         if fitz.get_text_length(cand, fontname="helv", fontsize=label_fs) <= first_max:
#                             curr.append(w)
#                         else:
#                             if not placed_first:
#                                 first_line_items = " ".join(curr)
#                                 placed_first = True
#                                 curr = [w]
#                             else:
#                                 rest_words.append(" ".join(curr))
#                                 curr = [w]
#                     if curr:
#                         if not placed_first:
#                             first_line_items = " ".join(curr)
#                         else:
#                             rest_words.append(" ".join(curr))

#                     ops.append(("hebo+helv", prefix, first_line_items))
#                     for rw in rest_words:
#                         for wl in _wrap_text_lines(rw, fs=label_fs, max_w=max_w, fn="helv"):
#                             ops.append(("helv", wl, ""))
#                     return ops

#                 left_ops = _block_lines(left, item_max_left)
#                 right_ops = _block_lines(right, item_max_right)
#                 n_lines = max(len(left_ops), len(right_ops), 1)
#                 ensure_space(n_lines * self.LH + 2.0)
#                 row_y = y

#                 def _paint(ops, x0):
#                     cy = row_y
#                     for kind, a, b in ops:
#                         if kind == "hebo+helv":
#                             page.insert_text(fitz.Point(x0, cy + label_fs * 0.85), a,
#                                              fontsize=label_fs, fontname="hebo", color=self.C_TEXT)
#                             lw = fitz.get_text_length(a, fontname="hebo", fontsize=label_fs)
#                             if b:
#                                 page.insert_text(fitz.Point(x0 + lw, cy + label_fs * 0.85), b,
#                                                  fontsize=label_fs, fontname="helv", color=self.C_TEXT)
#                         else:
#                             page.insert_text(fitz.Point(x0, cy + label_fs * 0.85), a,
#                                              fontsize=label_fs, fontname="helv", color=self.C_TEXT)
#                         cy += self.LH
#                     return cy

#                 y_l = _paint(left_ops, left_x) if left_ops else row_y
#                 y_r = _paint(right_ops, right_x) if right_ops else row_y
#                 y = max(y_l, y_r) + 1.0

#         # ── 4. PROJECTS ──────────────────────────────────────────────────────
#         proj_list = resume_data.get("projects") or []
#         if isinstance(proj_list, list) and proj_list:
#             drawn = False
#             for proj in proj_list:
#                 if not isinstance(proj, dict):
#                     continue
#                 pname = _get_val(proj, "name", "title")
#                 if not pname or pname.lower() in ('*', '•', '-', 'project', 'projects', '[github]'):
#                     continue
#                 if not drawn:
#                     draw_header("PROJECTS")
#                     drawn = True

#                 purl = _get_val(proj, "github_url", "url", "live_url")
#                 subtitle = _get_val(proj, "subtitle", "tagline")
#                 title = pname
#                 if subtitle and subtitle.lower() not in title.lower():
#                     title = f"{pname} - {subtitle}"

#                 ensure_space(self.LH + 2.0)
#                 page.insert_text(fitz.Point(self.MX, y + self.BODY_FS * 0.85), title,
#                                  fontsize=self.BODY_FS, fontname="hebo", color=self.C_NAME)
#                 if purl:
#                     link_txt = f"[{_strip_url(purl)}]"
#                     # Only show short marker if room; skip long URLs to avoid clutter
#                     if fitz.get_text_length(link_txt, fontname="helv", fontsize=8.0) < 160:
#                         tw = fitz.get_text_length(link_txt, fontname="helv", fontsize=8.0)
#                         page.insert_text(
#                             fitz.Point(self.PAGE_W - self.MX - tw, y + self.BODY_FS * 0.85),
#                             link_txt, fontsize=8.0, fontname="helv", color=self.C_MUTED,
#                         )
#                 y += self.LH

#                 techs = _ensure_list(proj.get("technologies") or proj.get("tech_stack"))
#                 if techs:
#                     draw_paragraph(", ".join(techs), fs=self.BODY_FS, space_after=1.0, fn="heit")

#                 desc = _get_val(proj, "description")
#                 bullets = _ensure_list(proj.get("highlights") or proj.get("bullets"))
#                 if desc and desc not in bullets:
#                     # Prefer structured bullets; include desc only if no bullets
#                     if not bullets:
#                         draw_bullet(desc, indent=6.0)
#                 for b in bullets:
#                     draw_bullet(b, indent=6.0)

#                 y += 2.0

#         # ── 5. EXPERIENCE (title full-width; bullets in 2 columns) ────────────
#         exp_list = resume_data.get("experience") or []
#         if isinstance(exp_list, list) and exp_list:
#             drawn = False
#             for exp in exp_list:
#                 exp = _coerce_to_dict(exp)
#                 if not exp:
#                     continue
#                 role = _get_val(exp, "role", "title", default="")
#                 comp = _get_val(exp, "company", "organization")
#                 if _is_placeholder_experience(role, comp):
#                     continue
#                 if role.lower() in ('*', '•', '-', 'bullet', 'experience'):
#                     continue
#                 if not drawn:
#                     draw_header("EXPERIENCE")
#                     drawn = True

#                 dates = _get_val(exp, "dates", "period")
#                 if not dates:
#                     start = _get_val(exp, "start_date")
#                     end = _get_val(exp, "end_date")
#                     if start and end:
#                         dates = f"{start} - {end}"
#                     elif start:
#                         dates = f"{start} - Present"
#                     elif end:
#                         dates = end

#                 # Golden: "Role — Company | dates"
#                 if role and comp:
#                     title_line = f"{role} - {comp}"
#                 else:
#                     title_line = role or comp
#                 if dates:
#                     title_line = f"{title_line} | {dates}"

#                 ensure_space(self.LH + 2.0)
#                 page.insert_text(fitz.Point(self.MX, y + self.BODY_FS * 0.85), title_line,
#                                  fontsize=self.BODY_FS, fontname="hebo", color=self.C_NAME)
#                 y += self.LH + 1.0

#                 bullets = _ensure_list(
#                     exp.get("highlights") or exp.get("bullets")
#                     or exp.get("responsibilities") or exp.get("description")
#                 )
#                 # Single-column bullets (stable ATS layout; avoids broken 2-col wraps)
#                 for b in bullets:
#                     draw_bullet(b, indent=6.0, space_after=1.2)

#                 techs = _ensure_list(exp.get("technologies") or exp.get("tech_stack"))
#                 if techs:
#                     draw_paragraph(", ".join(techs), fs=8.5, indent=6.0, space_after=2.0, fn="heit")
#                 y += 1.5

#         # ── 6. EDUCATION (compact single lines — recover years/GPA/college) ───
#         edu_list = resume_data.get("education") or []
#         normalized_edu: List[Dict[str, str]] = []
#         if isinstance(edu_list, list):
#             for edu in edu_list:
#                 norm = _normalize_education_item(edu)
#                 if norm and not _is_junk_education(norm):
#                     normalized_edu.append(norm)
#             # De-dupe by institution(+degree) keeping the richest entry
#             deduped: List[Dict[str, str]] = []
#             seen_keys = set()
#             for edu in normalized_edu:
#                 key = (
#                     _clean_str(edu.get("institution")).lower(),
#                     _clean_str(edu.get("degree")).lower(),
#                 )
#                 if key in seen_keys and key != ("", ""):
#                     # Prefer entry that has GPA/dates
#                     for i, prev in enumerate(deduped):
#                         pk = (
#                             _clean_str(prev.get("institution")).lower(),
#                             _clean_str(prev.get("degree")).lower(),
#                         )
#                         if pk == key:
#                             prev_score = bool(prev.get("gpa")) + bool(prev.get("start_date") or prev.get("end_date"))
#                             new_score = bool(edu.get("gpa")) + bool(edu.get("start_date") or edu.get("end_date"))
#                             if new_score > prev_score:
#                                 deduped[i] = edu
#                             break
#                     continue
#                 seen_keys.add(key)
#                 deduped.append(edu)
#             normalized_edu = sorted(deduped, key=_education_sort_key)

#         if normalized_edu:
#             drawn = False
#             for edu in normalized_edu:
#                 school = _clean_str(edu.get("institution"))
#                 deg = _clean_str(edu.get("degree"))
#                 field = _clean_str(edu.get("field_of_study"))
#                 degree_display = _format_degree_display(deg, field)

#                 # Avoid "School - School" when board exam sets both institution & degree to HSC/SSC
#                 if school and degree_display and school.lower() == degree_display.lower():
#                     degree_display = ""

#                 dates = _clean_str(edu.get("dates"))
#                 if not dates:
#                     start = _clean_str(edu.get("start_date"))
#                     end = _clean_str(edu.get("end_date"))
#                     if start and end:
#                         dates = f"{start}-{end}" if len(start) <= 4 and len(end) <= 4 else f"{start} - {end}"
#                     elif end:
#                         dates = end
#                     elif start:
#                         dates = start

#                 gpa_label = _format_gpa_label(edu.get("gpa") or "")

#                 if not school and not degree_display:
#                     continue
#                 if not drawn:
#                     # Keep header with first education line (prevent orphan header / footer clash)
#                     draw_header("EDUCATION", keep_with=self.LH + 4.0)
#                     drawn = True

#                 # Golden: School — Degree | score | years
#                 # Board: HSC - 46.31%
#                 is_board = bool(re.search(r'\b(hsc|ssc|cbse|icse)\b', f"{school} {degree_display}", re.I))
#                 if is_board and gpa_label and school:
#                     line = f"{school} - {gpa_label}"
#                 else:
#                     parts = []
#                     if school and degree_display:
#                         parts.append(f"{school} - {degree_display}")
#                     elif school:
#                         parts.append(school)
#                     else:
#                         parts.append(degree_display)
#                     if gpa_label:
#                         parts.append(gpa_label)
#                     if dates:
#                         parts.append(dates)
#                     line = " | ".join(parts) if len(parts) > 1 else parts[0]

#                 draw_paragraph(line, fs=self.BODY_FS, space_after=1.2)

#         # ── 7. Achievements (optional, not in golden but keep if present) ─────
#         ach_list = resume_data.get("achievements") or []
#         if isinstance(ach_list, list) and ach_list:
#             drawn = False
#             for ach in ach_list:
#                 if isinstance(ach, dict):
#                     title = _get_val(ach, "title", "name", "role")
#                     org = _get_val(ach, "organization", "institution", "company")
#                     det = _get_val(ach, "description", "details")
#                     date = _get_val(ach, "date", "year")
#                     top = f"{title} | {org}" if (title and org) else (title or org or det or "")
#                     if not top:
#                         continue
#                     if date:
#                         top += f" ({date})"
#                     if det and det != top and det not in top:
#                         top += f" - {det}"
#                     if not drawn:
#                         draw_header("ACHIEVEMENTS")
#                         drawn = True
#                     draw_bullet(top, indent=6.0)
#                 elif isinstance(ach, str) and _clean_str(ach):
#                     cl = _clean_str(ach)
#                     if cl.lower() not in ('*', '•', '-'):
#                         if not drawn:
#                             draw_header("ACHIEVEMENTS")
#                             drawn = True
#                         draw_bullet(cl, indent=6.0)

#         # ── 8. Custom sections (optional) ─────────────────────────────────────
#         custom_secs = resume_data.get("custom_sections") or []
#         if isinstance(custom_secs, list) and custom_secs:
#             for sec in custom_secs:
#                 if not isinstance(sec, dict):
#                     continue
#                 sec_title = _clean_str(_get_val(sec, "title", "heading", "name") or "ADDITIONAL")
#                 if "hobby" in sec_title.lower() or "interest" in sec_title.lower():
#                     continue
#                 items = sec.get("items") or sec.get("bullets") or []
#                 if isinstance(items, str):
#                     items = [it.strip() for it in items.splitlines() if it.strip()]
#                 if not isinstance(items, list) or not items:
#                     continue
#                 drawn = False
#                 for item in items:
#                     if isinstance(item, dict):
#                         it_text = _get_val(item, "text", "description", "name")
#                     else:
#                         it_text = _clean_str(str(item))
#                     if it_text and it_text.lower() not in ('*', '•', '-'):
#                         if not drawn:
#                             draw_header(sec_title)
#                             drawn = True
#                         draw_bullet(it_text, indent=6.0)

#         # ── 9. CERTIFICATIONS: I. ... II. ... (inline, no underline) ──────────
#         cert_lines = self._collect_cert_lines(resume_data)
#         if cert_lines:
#             ensure_space(self.LH * 2 + 8.0)
#             y += 6.0
#             label = "CERTIFICATIONS: "
#             page.insert_text(fitz.Point(self.MX, y + self.HEAD_FS * 0.85), label,
#                              fontsize=self.HEAD_FS, fontname="hebo", color=self.C_HEADER)
#             label_w = fitz.get_text_length(label, fontname="hebo", fontsize=self.HEAD_FS)

#             # Pack roman-numbered certs on one or more lines
#             x = self.MX + label_w
#             line_y = y
#             max_x = self.PAGE_W - self.MX
#             gap = "     "
#             for idx, cl in enumerate(cert_lines, start=1):
#                 chunk = f"{_roman(idx)}. {cl}"
#                 tw = fitz.get_text_length(chunk, fontname="helv", fontsize=self.BODY_FS)
#                 if x > self.MX + label_w and x + tw > max_x:
#                     line_y += self.LH
#                     ensure_space(self.LH + 2.0)
#                     x = self.MX + label_w
#                     y = max(y, line_y)
#                 page.insert_text(fitz.Point(x, line_y + self.BODY_FS * 0.85), chunk,
#                                  fontsize=self.BODY_FS, fontname="helv", color=self.C_TEXT)
#                 x += tw + fitz.get_text_length(gap, fontname="helv", fontsize=self.BODY_FS)
#             y = line_y + self.LH + 2.0

#         # ── 10. HOBBIES: inline ───────────────────────────────────────────────
#         hobbies = self._collect_hobbies(resume_data, custom_secs, candidate_name)
#         if hobbies:
#             ensure_space(self.LH + 8.0)
#             y += 3.0
#             label = "HOBBIES: "
#             page.insert_text(fitz.Point(self.MX, y + self.HEAD_FS * 0.85), label,
#                              fontsize=self.HEAD_FS, fontname="hebo", color=self.C_HEADER)
#             label_w = fitz.get_text_length(label, fontname="hebo", fontsize=self.HEAD_FS)
#             body = ", ".join(hobbies)
#             if not body.endswith("."):
#                 body += "."
#             # Wrap if needed
#             max_w = cw - label_w
#             lines = _wrap_text_lines(body, fs=self.BODY_FS, max_w=max_w, fn="helv")
#             if lines:
#                 page.insert_text(fitz.Point(self.MX + label_w, y + self.BODY_FS * 0.85), lines[0],
#                                  fontsize=self.BODY_FS, fontname="helv", color=self.C_TEXT)
#                 y += self.LH
#                 for extra in lines[1:]:
#                     ensure_space(self.LH)
#                     page.insert_text(fitz.Point(self.MX + label_w, y + self.BODY_FS * 0.85), extra,
#                                      fontsize=self.BODY_FS, fontname="helv", color=self.C_TEXT)
#                     y += self.LH

#         # No footer — keeps resume to one page and matches clean ATS export

#         try:
#             pdf_bytes = doc.tobytes(deflate=True)
#         except Exception:
#             pdf_bytes = doc.write(deflate=True)
#         doc.close()
#         return pdf_bytes

#     def _collect_skill_rows(self, resume_data: Dict[str, Any]) -> List[Tuple[str, str]]:
#         raw_skills = resume_data.get("skills") or resume_data.get("extracted_skills") or {}
#         skill_rows: List[Tuple[str, str]] = []

#         LABELS = [
#             ("technical", "Languages"),
#             ("languages", "Languages"),
#             ("frontend", "Frontend"),
#             ("frameworks", "Frontend"),
#             ("backend", "Backend"),
#             ("databases", "Databases"),
#             ("ai_ml", "AI / ML"),
#             ("aiml", "AI / ML"),
#             ("ml", "AI / ML"),
#             ("cybersecurity", "Cybersecurity"),
#             ("security", "Cybersecurity"),
#             ("cloud", "Cloud / DevOps"),
#             ("devops", "Cloud / DevOps"),
#             ("tools", "Tools"),
#             ("soft", "Professional Skills"),
#             ("other", "Other"),
#         ]

#         if isinstance(raw_skills, dict):
#             seen_labels = set()
#             # Prefer ordered known keys first
#             used_keys = set()
#             for key, label in LABELS:
#                 if key in used_keys:
#                     continue
#                 items = raw_skills.get(key)
#                 if items is None:
#                     continue
#                 used_keys.add(key)
#                 if label in seen_labels and key in ("frameworks", "languages", "devops", "aiml", "ml", "security"):
#                     # Merge into existing label row if duplicate
#                     pass
#                 clean_items: List[str] = []
#                 if isinstance(items, list):
#                     clean_items = [_clean_str(x) for x in items if _clean_str(x)]
#                 elif isinstance(items, str) and items.strip():
#                     clean_items = [_clean_str(items)]
#                 if not clean_items:
#                     continue
#                 # Merge into existing same label
#                 merged = False
#                 for i, (lab, existing) in enumerate(skill_rows):
#                     if lab == label:
#                         combined = existing + ", " + ", ".join(clean_items)
#                         skill_rows[i] = (lab, combined)
#                         merged = True
#                         break
#                 if not merged:
#                     skill_rows.append((label, ", ".join(clean_items)))
#                     seen_labels.add(label)

#             # Any remaining custom keys
#             for k, items in raw_skills.items():
#                 if k in used_keys or k.startswith("_"):
#                     continue
#                 label = _clean_str(k).replace("_", " ").title() or "Other"
#                 clean_items = []
#                 if isinstance(items, list):
#                     clean_items = [_clean_str(x) for x in items if _clean_str(x)]
#                 elif isinstance(items, str) and items.strip():
#                     clean_items = [_clean_str(items)]
#                 if clean_items:
#                     skill_rows.append((label, ", ".join(clean_items)))

#         elif isinstance(raw_skills, list) and raw_skills:
#             clean_items = []
#             for s in raw_skills:
#                 if isinstance(s, dict):
#                     clean_items.extend([_clean_str(x) for x in s.get("skills", []) if _clean_str(x)])
#                 elif s:
#                     clean_items.append(_clean_str(s))
#             if clean_items:
#                 skill_rows.append(("Languages", ", ".join(clean_items[:40])))

#         return skill_rows

#     def _collect_cert_lines(self, resume_data: Dict[str, Any]) -> List[str]:
#         certs = resume_data.get("certifications") or []
#         out: List[str] = []
#         if not isinstance(certs, list):
#             return out
#         for c in certs:
#             if isinstance(c, dict):
#                 cname = _get_val(c, "name", "title")
#                 issuer = _get_val(c, "issuer", "authority")
#                 date = _get_val(c, "issue_date", "date", "year", "dates")
#                 if not cname:
#                     continue
#                 # Strip accidental roman/section prefixes from bad parses
#                 cname = re.sub(r'^(?:[IVXLC]+\.|CERTIFICATIONS?:)\s*', '', cname, flags=re.I).strip()
#                 issuer = re.sub(r'^(?:[IVXLC]+\.|CERTIFICATIONS?:)\s*', '', issuer, flags=re.I).strip()
#                 if not cname or cname.lower() in ("certifications", "hobbies", "education"):
#                     continue
#                 if issuer and issuer.lower() not in cname.lower():
#                     line = f"{issuer} - {cname}"
#                 else:
#                     line = cname
#                 if date:
#                     line += f" ({date})"
#                 # De-dupe near-identical lines
#                 if any(line.lower() == x.lower() or line.lower() in x.lower() or x.lower() in line.lower() for x in out):
#                     continue
#                 out.append(line)
#             elif isinstance(c, str) and _clean_str(c):
#                 cl = _clean_str(c)
#                 cl = re.sub(r'^(?:[IVXLC]+\.|CERTIFICATIONS?:)\s*', '', cl, flags=re.I).strip()
#                 if cl.lower() not in ('*', '•', '-', 'certifications', 'hobbies'):
#                     if not any(cl.lower() == x.lower() or cl.lower() in x.lower() for x in out):
#                         out.append(cl)
#         return out

#     def _collect_hobbies(self, resume_data: Dict[str, Any], custom_secs: Any, candidate_name: str = "") -> List[str]:
#         hobbies_list = resume_data.get("hobbies") or resume_data.get("interests") or []
#         if not hobbies_list and isinstance(custom_secs, list):
#             for sec in custom_secs:
#                 if isinstance(sec, dict) and (
#                     "hobby" in str(sec.get("title", "")).lower()
#                     or "interest" in str(sec.get("title", "")).lower()
#                 ):
#                     hobbies_list = sec.get("items") or []
#                     break

#         name_l = _clean_str(candidate_name).lower()
#         out: List[str] = []
#         if isinstance(hobbies_list, str) and hobbies_list.strip():
#             hobbies_list = [h.strip() for h in re.split(r'[\n;,•]+', hobbies_list) if h.strip()]
#         if isinstance(hobbies_list, list):
#             for h in hobbies_list:
#                 if isinstance(h, dict):
#                     h_val = _get_val(h, "name", "title", "hobby", "interest", "description")
#                 else:
#                     h_val = _clean_str(str(h))
#                 if not h_val or h_val.lower() in ('*', '•', '-'):
#                     continue
#                 h_val = h_val.rstrip(".")
#                 hl = h_val.lower()
#                 # Drop footer/name leakage and section labels
#                 if name_l and (hl == name_l or hl.replace(" ", "") == name_l.replace(" ", "")):
#                     continue
#                 if hl in ("candidate name", "candidate", "hobbies", "interests", "certifications"):
#                     continue
#                 if name_l and name_l in hl and len(hl.split()) <= 4:
#                     continue
#                 out.append(h_val)
#         return out


# pdf_generator = ATSPdfGenerator()


# def generate_pdf(resume_data: Dict[str, Any]) -> bytes:
#     """Module-level convenience wrapper for ATSPdfGenerator.generate_pdf."""
#     return pdf_generator.generate_pdf(resume_data)





"""
ATS-Compliant PDF Generator
Swapnil Supe Perfect Resume — strict canonical-data renderer.

Design:
    HEADER
    PROFILE
    TECHNICAL SKILLS (2-column)
    PROJECTS
    EXPERIENCE (title full width + bullets in 2 columns)
    EDUCATION (10 / 12 / Diploma / Degree — render whatever exists)
    CERTIFICATIONS (inline I., II., III...)
    HOBBIES (inline)

Important architecture rule:
    This file is a RENDERER, not a parser or AI repair engine.

It must render the canonical resume data it receives. It should not:
    - invent missing information
    - merge separate certifications
    - create education entries
    - delete education entries
    - rewrite experience bullets
    - infer dates/GPA from unrelated fields

Upstream parser/validator/AI layers are responsible for producing validated
canonical resume data. This renderer only formats that data into the golden
PDF layout.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import re

import pymupdf as fitz


# ---------------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------------

_CHAR_REPLACEMENTS = {
    "\u2014": " - ",
    "\u2013": " - ",
    "\u2012": " - ",
    "\u2015": " - ",
    "\u201c": '"',
    "\u201d": '"',
    "\u201e": '"',
    "\u201f": '"',
    "\u2018": "'",
    "\u2019": "'",
    "\u201a": "'",
    "\u201b": "'",
    "\u00a0": " ",
    "\u2022": "*",
    "\u25cf": "*",
    "\u25aa": "*",
    "\u2023": "*",
    "\u2219": "*",
    "\u00b7": "*",
    "\u2756": "*",
    "\u25c6": "*",
    "\u25c8": "*",
    "\u2026": "...",
    "\u2192": "->",
    "\u21d2": "=>",
    "\u2794": "->",
    "\u27a4": "->",
    "\u2713": "[x]",
    "\u2714": "[x]",
    "\u2717": "[ ]",
    "\u2718": "[ ]",
    "\u200b": "",
    "\ufeff": "",
}

_ROMAN = (
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "XI", "XII", "XIII", "XIV", "XV",
)


def _clean_str(value: Any) -> str:
    """Clean display text without changing its semantic content, stripping raw markdown syntax."""
    if value is None:
        return ""

    text = str(value).strip()
    if not text:
        return ""

    # Strip raw markdown formatting markers (**bold**, *italic*, `code`, etc.)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'\1', text)
    text = re.sub(r'`([^`\n]+)`', r'\1', text)
    text = text.replace("**", "").replace("__", "")

    for old, new in _CHAR_REPLACEMENTS.items():
        text = text.replace(old, new)

    # Remove accidental leading markdown/list markers only.
    text = re.sub(r"^[\s*\-•●]+", "", text)

    # Helvetica is intentionally used for ATS-safe output.
    clean = []
    for char in text:
        code = ord(char)
        if code < 128 or 160 <= code <= 255:
            clean.append(char)
        else:
            clean.append(" ")

    return re.sub(r"\s+", " ", "".join(clean)).strip()


def _value(data: Any, *keys: str) -> str:
    """Return the first non-empty value from a dictionary."""
    if not isinstance(data, dict):
        return ""

    for key in keys:
        value = data.get(key)
        if value is None:
            continue
        cleaned = _clean_str(value)
        if cleaned:
            return cleaned

    return ""


def _as_dict(value: Any) -> Optional[Dict[str, Any]]:
    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        try:
            result = value.model_dump()
            return result if isinstance(result, dict) else None
        except Exception:
            pass

    if hasattr(value, "dict"):
        try:
            result = value.dict()
            return result if isinstance(result, dict) else None
        except Exception:
            pass

    return None


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, str):
        # Newlines represent separate bullets/items.
        lines = [line.strip() for line in value.splitlines() if line.strip()]
        return lines or [value]

    return [value]


def _clean_items(value: Any) -> List[str]:
    result: List[str] = []

    for item in _as_list(value):
        if isinstance(item, dict):
            text = (
                item.get("text")
                or item.get("name")
                or item.get("title")
                or item.get("description")
            )
        else:
            text = item

        cleaned = _clean_str(text)

        if cleaned and cleaned.lower() not in {
            "*", "•", "-", "bullet", "none", "null"
        }:
            result.append(cleaned)

    return result


def _wrap_text(text: str, fontsize: float, width: float,
                fontname: str = "helv") -> List[str]:
    if not text:
        return []

    words = text.split()
    lines: List[str] = []
    current: List[str] = []

    for word in words:
        candidate = " ".join(current + [word])
        if fitz.get_text_length(
            candidate, fontname=fontname, fontsize=fontsize
        ) <= width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]

    if current:
        lines.append(" ".join(current))

    return lines


def _strip_url(url: str) -> str:
    value = _clean_str(url)
    value = re.sub(r"^https?://", "", value, flags=re.IGNORECASE)
    return value.rstrip("/")


def _roman(number: int) -> str:
    if 1 <= number <= len(_ROMAN):
        return _ROMAN[number - 1]
    return str(number)


# ---------------------------------------------------------------------------
# Colors & Typography Constants
# ---------------------------------------------------------------------------

PAGE_W = 612.0
PAGE_H = 792.0
MARGIN_X = 26.0
MARGIN_TOP = 24.0
MARGIN_BOTTOM = 18.0
COLUMN_GAP = 14.0

BODY_FS = 9.0
HEADER_FS = 10.0
NAME_FS = 18.0
LINE_HEIGHT = 11.0

BLACK = (0.0, 0.0, 0.0)
BLUE = (55 / 255.0, 80 / 255.0, 120 / 255.0)
GRAY = (183 / 255.0, 183 / 255.0, 183 / 255.0)


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class ATSPdfGenerator:
    """
    Strict renderer for the Swapnil Supe Perfect Resume design.

    The renderer intentionally does not parse or repair resume content.
    """

    PAGE_W = PAGE_W
    PAGE_H = PAGE_H

    MARGIN_X = MARGIN_X
    MARGIN_TOP = MARGIN_TOP
    MARGIN_BOTTOM = MARGIN_BOTTOM

    COLUMN_GAP = COLUMN_GAP

    BODY_FS = BODY_FS
    HEADER_FS = HEADER_FS
    NAME_FS = NAME_FS

    LINE_HEIGHT = LINE_HEIGHT

    BLACK = BLACK
    BLUE = BLUE
    GRAY = GRAY

    def __init__(self) -> None:
        self.content_width = self.PAGE_W - (2 * self.MARGIN_X)
        self.middle_x = self.PAGE_W / 2.0
        self.column_width = (
            self.content_width - self.COLUMN_GAP
        ) / 2.0

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def generate_pdf(self, resume_data: Dict[str, Any]) -> bytes:
        if not isinstance(resume_data, dict):
            raise TypeError("resume_data must be a dictionary")

        doc = fitz.open()
        page = doc.new_page(width=self.PAGE_W, height=self.PAGE_H)
        y = self.MARGIN_TOP

        def new_page_if_needed(height: float) -> None:
            nonlocal page, y

            if y + height > self.PAGE_H - self.MARGIN_BOTTOM:
                page = doc.new_page(
                    width=self.PAGE_W,
                    height=self.PAGE_H,
                )
                y = self.MARGIN_TOP

        def draw_text(
            text: str,
            x: float,
            baseline_y: float,
            fontsize: float = self.BODY_FS,
            fontname: str = "helv",
            color: Tuple[float, float, float] = self.BLACK,
        ) -> None:
            if not text:
                return

            page.insert_text(
                fitz.Point(x, baseline_y),
                text,
                fontsize=fontsize,
                fontname=fontname,
                color=color,
            )

        def draw_centered(
            text: str,
            fontsize: float = self.BODY_FS,
            fontname: str = "helv",
            color: Tuple[float, float, float] = self.BLACK,
            gap: float = 2.0,
        ) -> None:
            nonlocal y

            text = _clean_str(text)
            if not text:
                return

            new_page_if_needed(fontsize + gap + 2)

            width = fitz.get_text_length(
                text,
                fontname=fontname,
                fontsize=fontsize,
            )
            x = max(
                self.MARGIN_X,
                (self.PAGE_W - width) / 2.0,
            )

            draw_text(
                text,
                x,
                y + fontsize * 0.85,
                fontsize,
                fontname,
                color,
            )
            y += fontsize + gap

        def draw_section_header(title: str) -> None:
            nonlocal y

            title = _clean_str(title).upper()
            if not title:
                return

            new_page_if_needed(27)

            y += 4.0

            draw_text(
                title,
                self.MARGIN_X,
                y + self.HEADER_FS * 0.85,
                self.HEADER_FS,
                "hebo",
                self.BLUE,
            )

            y += self.HEADER_FS + 2.0

            page.draw_line(
                fitz.Point(self.MARGIN_X - 2.0, y),
                fitz.Point(self.PAGE_W - self.MARGIN_X + 2.0, y),
                color=self.GRAY,
                width=0.6,
            )

            y += 4.0

        def draw_paragraph(
            text: str,
            fontsize: float = self.BODY_FS,
            indent: float = 0.0,
            gap: float = 2.0,
            fontname: str = "helv",
        ) -> None:
            nonlocal y

            text = _clean_str(text)
            if not text:
                return

            width = self.content_width - indent
            lines = _wrap_text(text, fontsize, width, fontname)

            if not lines:
                return

            new_page_if_needed(
                len(lines) * self.LINE_HEIGHT + gap
            )

            for line in lines:
                draw_text(
                    line,
                    self.MARGIN_X + indent,
                    y + fontsize * 0.85,
                    fontsize,
                    fontname,
                    self.BLACK,
                )
                y += self.LINE_HEIGHT

            y += gap

        def draw_bullet_at(
            text: str,
            x: float,
            start_y: float,
            width: float,
        ) -> float:
            text = _clean_str(text)
            if not text:
                return start_y

            bullet_width = 8.0
            lines = _wrap_text(
                text,
                self.BODY_FS,
                width - bullet_width,
                "helv",
            )

            cy = start_y

            draw_text(
                "*",
                x,
                cy + self.BODY_FS * 0.85,
                self.BODY_FS,
                "hebo",
                self.BLACK,
            )

            for line in lines:
                draw_text(
                    line,
                    x + bullet_width,
                    cy + self.BODY_FS * 0.85,
                    self.BODY_FS,
                    "helv",
                    self.BLACK,
                )
                cy += self.LINE_HEIGHT

            return cy + 1.2

        def draw_bullet(
            text: str,
            indent: float = 6.0,
            gap: float = 1.2,
        ) -> None:
            nonlocal y

            text = _clean_str(text)
            if not text:
                return

            width = self.content_width - indent
            lines = _wrap_text(
                text,
                self.BODY_FS,
                width - 8.0,
                "helv",
            )

            new_page_if_needed(
                len(lines) * self.LINE_HEIGHT + gap
            )

            y = draw_bullet_at(
                text,
                self.MARGIN_X + indent,
                y,
                width,
            )

            y += gap

        # ==============================================================
        # 1. HEADER
        # ==============================================================

        profile = _as_dict(resume_data.get("profile")) or {}

        name = (
            _value(resume_data, "candidate_name", "name")
            or _value(profile, "name", "candidate_name")
            or "CANDIDATE NAME"
        ).upper()

        email = (
            _value(resume_data, "email")
            or _value(profile, "email")
        )

        phone = (
            _value(resume_data, "phone", "mobile")
            or _value(profile, "phone", "mobile")
        )

        linkedin = (
            _value(resume_data, "linkedin_url", "linkedin")
            or _value(profile, "linkedin_url", "linkedin")
        )

        github = (
            _value(resume_data, "github_url", "github")
            or _value(profile, "github_url", "github")
        )

        portfolio = (
            _value(resume_data, "portfolio_url", "portfolio")
            or _value(profile, "portfolio_url", "portfolio")
        )

        draw_centered(
            name,
            self.NAME_FS,
            "hebo",
            self.BLACK,
            4.0,
        )

        contact = [
            value for value in (email, phone)
            if value
        ]

        if contact:
            draw_centered(
                "  |  ".join(contact),
                self.BODY_FS,
                "helv",
                self.BLACK,
                2.0,
            )

        links = []

        if linkedin:
            links.append(f"LinkedIn: {_strip_url(linkedin)}")

        if github:
            links.append(f"GitHub: {_strip_url(github)}")

        if portfolio:
            links.append(f"Portfolio: {_strip_url(portfolio)}")

        if links:
            draw_centered(
                "  |  ".join(links),
                self.BODY_FS,
                "helv",
                self.BLACK,
                2.0,
            )

        y += 2.0

        # ==============================================================
        # 2. PROFILE
        # ==============================================================

        summary = (
            _value(resume_data, "summary", "profile_summary")
            or _value(profile, "summary", "profile_summary")
        )

        if summary:
            draw_section_header("PROFILE")
            draw_paragraph(summary, gap=2.0)

        # ==============================================================
        # 3. TECHNICAL SKILLS  — two-column layout
        # ==============================================================

        skill_rows = self._collect_skill_rows(resume_data)

        if skill_rows:
            draw_section_header("TECHNICAL SKILLS")

            # Pair up rows: left column gets even indices, right gets odd.
            # If there is an odd number of rows the last left row has no
            # right partner (right=None).
            paired: List[Tuple[Tuple[str, str], Optional[Tuple[str, str]]]] = []
            for i in range(0, len(skill_rows), 2):
                left = skill_rows[i]
                right = skill_rows[i + 1] if i + 1 < len(skill_rows) else None
                paired.append((left, right))

            for left, right in paired:
                # Estimate height needed for this pair using actual category labels
                left_h = self._skill_line_count(left[0], left[1], self.column_width) * self.LINE_HEIGHT + 2.0
                right_h = (
                    self._skill_line_count(right[0], right[1], self.column_width) * self.LINE_HEIGHT + 2.0
                    if right else 0.0
                )
                row_height = max(left_h, right_h, self.LINE_HEIGHT + 2.0)
                new_page_if_needed(row_height)

                self._draw_skill_row(page, left, right, y, new_page_if_needed, draw_text)
                y += row_height

        # ==============================================================
        # 4. PROJECTS
        # ==============================================================

        projects = _as_list(resume_data.get("projects"))

        valid_projects = [
            _as_dict(project)
            for project in projects
            if _as_dict(project)
        ]

        valid_projects = [
            project
            for project in valid_projects
            if project and _value(project, "name", "title")
        ]

        if valid_projects:
            draw_section_header("PROJECTS")

            for project in valid_projects:
                pname = _value(project, "name", "title")
                psub = _value(project, "subtitle", "tagline")
                pdesc = _value(project, "description")

                # If subtitle not provided, check if description is a subtitle
                if not psub and pdesc and len(pdesc.splitlines()) == 1 and len(pdesc) < 120:
                    psub = pdesc

                # Check if pname already combined name and subtitle
                if not psub and any(sep in pname for sep in (" — ", " – ")):
                    parts = re.split(r'\s*(?:—|–)\s*', pname, maxsplit=1)
                    if len(parts) >= 2:
                        pname = parts[0].strip()
                        psub = parts[1].strip()
                elif psub and psub.lower() in pname.lower():
                    pname = re.sub(re.escape(psub), "", pname, flags=re.IGNORECASE).rstrip(" —-– ").strip()

                title_part = f"{pname} — {psub}" if psub else pname

                # Technologies: separate italic line directly below the heading
                raw_tech = _clean_items(
                    project.get("technologies") or project.get("tech_stack")
                )
                techs = [t for t in raw_tech if t and t.lower() != psub.lower()]

                # ── Heading: bold "Name — Subtitle" ───────────────────────
                new_page_if_needed(self.LINE_HEIGHT + 3)
                for hline in _wrap_text(title_part, self.BODY_FS, self.content_width, "hebo"):
                    new_page_if_needed(self.LINE_HEIGHT)
                    draw_text(
                        hline,
                        self.MARGIN_X,
                        y + self.BODY_FS * 0.85,
                        self.BODY_FS,
                        "hebo",
                        self.BLACK,
                    )
                    y += self.LINE_HEIGHT

                # ── Italic technology line (only when technologies exist) ──
                if techs:
                    tech_str = ", ".join(techs)
                    TECH_COLOR = (0.25, 0.35, 0.5)   # muted blue, readable
                    for tline in _wrap_text(tech_str, self.BODY_FS - 0.5, self.content_width, "hebi"):
                        new_page_if_needed(self.LINE_HEIGHT)
                        draw_text(
                            tline,
                            self.MARGIN_X,
                            y + (self.BODY_FS - 0.5) * 0.85,
                            self.BODY_FS - 0.5,
                            "hebi",        # Helvetica Bold Italic for a clean italic look
                            TECH_COLOR,
                        )
                        y += self.LINE_HEIGHT

                # ── Description (only when distinct from subtitle) ─────────
                if pdesc:
                    pdesc_clean = pdesc.strip().lstrip("*").rstrip("*").strip()
                    if pdesc_clean and pdesc_clean.lower() != psub.lower() and pdesc_clean.lower() != pname.lower() and len(pdesc_clean) > 120:
                        draw_paragraph(
                            pdesc_clean,
                            fontsize=self.BODY_FS,
                            gap=1.0,
                            fontname="helv",
                        )

                # ── Bullet points ──────────────────────────────────────────
                bullets = _clean_items(
                    project.get("highlights")
                    or project.get("description_bullets")
                    or project.get("bullets")
                )

                for bullet in bullets:
                    draw_bullet(bullet, indent=6.0)

                y += 1.5




        # ==============================================================
        # 5. EXPERIENCE
        # ==============================================================
        #
        # Golden layout:
        #
        # EXPERIENCE
        # Role — Company                                  Dates
        #
        # * bullet 1                         * bullet 3
        # * bullet 2                         * bullet 4
        # * bullet 5
        #
        # The title is full width. Only the bullets are two-column.
        # ==============================================================

        experiences = _as_list(resume_data.get("experience"))

        valid_experiences = [
            _as_dict(experience)
            for experience in experiences
            if _as_dict(experience)
        ]

        valid_experiences = [
            experience
            for experience in valid_experiences
            if experience
            and (
                _value(experience, "role", "title", "position")
                or _value(experience, "company", "organization", "employer")
            )
            and not (
                _value(experience, "role", "title", "position").strip().lower()
                in {"role", "title", "position", "job title", "job role", "designation"}
                and
                _value(experience, "company", "organization", "employer").strip().lower()
                in {"company", "organization", "employer", "company name", "org"}
            )
        ]

        if valid_experiences:
            draw_section_header("EXPERIENCE")

            for experience in valid_experiences:
                role = _value(
                    experience,
                    "role",
                    "title",
                    "position",
                )

                company = _value(
                    experience,
                    "company",
                    "organization",
                    "employer",
                )

                dates = _value(
                    experience,
                    "dates",
                    "period",
                    "date_range",
                )

                if not dates:
                    start = _value(
                        experience,
                        "start_date",
                        "from_date",
                    )
                    end = _value(
                        experience,
                        "end_date",
                        "to_date",
                    )

                    if start and end:
                        dates = f"{start} - {end}"
                    elif start:
                        dates = f"{start} - Present"
                    elif end:
                        dates = end

                if role and company:
                    title = f"{role} - {company}"
                else:
                    title = role or company

                bullets = _clean_items(
                    experience.get("highlights")
                    or experience.get("bullets")
                    or experience.get("responsibilities")
                )

                if not bullets:
                    description = _value(
                        experience,
                        "description",
                    )
                    if description:
                        bullets = [description]

                # Keep the title together with its bullets. The page break
                # must happen BEFORE anything is drawn: the old code drew the
                # title, then broke the page inside the bullet helper, which
                # kept drawing at the stale y of the previous page.
                usable_height = (
                    self.PAGE_H - self.MARGIN_BOTTOM - self.MARGIN_TOP
                )
                block_height = self._experience_block_bottom(bullets, 0.0)
                two_column_fits = (
                    self.LINE_HEIGHT + 3.0 + block_height + 2.0
                ) <= usable_height

                if two_column_fits:
                    new_page_if_needed(
                        self.LINE_HEIGHT + 3.0 + block_height + 2.0
                    )
                else:
                    # Very long block: title + first bullet, rest flows.
                    new_page_if_needed(self.LINE_HEIGHT * 3)

                # Full-width title.
                draw_text(
                    title,
                    self.MARGIN_X,
                    y + self.BODY_FS * 0.85,
                    self.BODY_FS,
                    "hebo",
                    self.BLACK,
                )

                if dates:
                    date_width = fitz.get_text_length(
                        dates,
                        fontname="heit",
                        fontsize=self.BODY_FS,
                    )

                    draw_text(
                        dates,
                        self.PAGE_W
                        - self.MARGIN_X
                        - date_width,
                        y + self.BODY_FS * 0.85,
                        self.BODY_FS,
                        "heit",
                        self.BLACK,
                    )

                y += self.LINE_HEIGHT + 1.0

                for bullet in bullets:
                    draw_bullet(bullet, indent=6.0)

                technologies = _clean_items(
                    experience.get("technologies")
                    or experience.get("tech_stack")
                )

                if technologies:
                    draw_paragraph(
                        ", ".join(technologies),
                        fontsize=8.5,
                        indent=6.0,
                        gap=2.0,
                        fontname="heit",
                    )

                y += 1.5

        # ==============================================================
        # 6. EDUCATION
        # ==============================================================

        education = _as_list(resume_data.get("education"))

        valid_education = [
            _as_dict(item)
            for item in education
            if _as_dict(item)
        ]

        valid_education = [
            item for item in valid_education
            if item
            and (
                _value(
                    item,
                    "institution",
                    "school",
                    "college",
                    "university",
                    "institute",
                )
                or _value(
                    item,
                    "degree",
                    "qualification",
                    "program",
                )
            )
        ]

        if valid_education:
            draw_section_header("EDUCATION")

            # IMPORTANT:
            # Preserve the order supplied by the frontend/canonical parser.
            # Do not sort or merge 10/12/diploma/degree entries.
            for item in valid_education:
                line = self._format_education(item)

                if line:
                    draw_paragraph(
                        line,
                        fontsize=self.BODY_FS,
                        gap=1.2,
                    )

        # ==============================================================
        # 7. CERTIFICATIONS
        # ==============================================================

        certifications = self._collect_certifications(
            resume_data
        )

        if certifications:
            new_page_if_needed(
                self.LINE_HEIGHT * 2 + 8
            )

            y += 5.0

            label = "CERTIFICATIONS: "

            draw_text(
                label,
                self.MARGIN_X,
                y + self.HEADER_FS * 0.85,
                self.HEADER_FS,
                "hebo",
                self.BLUE,
            )

            label_width = fitz.get_text_length(
                label,
                fontname="hebo",
                fontsize=self.HEADER_FS,
            )

            x = self.MARGIN_X + label_width
            line_y = y
            max_x = self.PAGE_W - self.MARGIN_X

            for index, certification in enumerate(
                certifications,
                start=1,
            ):
                chunk = f"{_roman(index)}. {certification}"

                width = fitz.get_text_length(
                    chunk,
                    fontname="helv",
                    fontsize=self.BODY_FS,
                )

                if x > self.MARGIN_X + label_width and (
                    x + width > max_x
                ):
                    line_y += self.LINE_HEIGHT
                    x = self.MARGIN_X + label_width

                draw_text(
                    chunk,
                    x,
                    line_y + self.BODY_FS * 0.85,
                    self.BODY_FS,
                    "helv",
                    self.BLACK,
                )

                x += width + 16.0

            y = line_y + self.LINE_HEIGHT + 2.0

        # ==============================================================
        # 8. HOBBIES
        # ==============================================================

        hobbies = self._collect_hobbies(resume_data)

        if hobbies:
            new_page_if_needed(
                self.LINE_HEIGHT * 2 + 8
            )

            y += 3.0

            label = "HOBBIES: "

            draw_text(
                label,
                self.MARGIN_X,
                y + self.HEADER_FS * 0.85,
                self.HEADER_FS,
                "hebo",
                self.BLUE,
            )

            label_width = fitz.get_text_length(
                label,
                fontname="hebo",
                fontsize=self.HEADER_FS,
            )

            body = ", ".join(hobbies)

            lines = _wrap_text(
                body,
                self.BODY_FS,
                self.content_width - label_width,
                "helv",
            )

            for index, line in enumerate(lines):
                if index == 0:
                    x = self.MARGIN_X + label_width
                else:
                    x = self.MARGIN_X + label_width

                draw_text(
                    line,
                    x,
                    y + self.BODY_FS * 0.85,
                    self.BODY_FS,
                    "helv",
                    self.BLACK,
                )
                y += self.LINE_HEIGHT

        # ==============================================================
        # 9. ACHIEVEMENTS
        # ==============================================================

        raw_achievements = (
            resume_data.get("achievements")
            or resume_data.get("key_achievements")
            or resume_data.get("accomplishments")
            or []
        )
        achievements_list: List[str] = []
        if isinstance(raw_achievements, list):
            for item in raw_achievements:
                if isinstance(item, dict):
                    title = (item.get("title") or item.get("name") or "").strip()
                    desc  = (item.get("description") or "").strip()
                    # Re-combine title + description so full sentences are preserved
                    if title and desc:
                        txt = f"{title}: {desc}"
                    else:
                        txt = title or desc
                else:
                    txt = str(item).strip()
                if txt:
                    achievements_list.append(txt)

        if achievements_list:
            draw_section_header("ACHIEVEMENTS")
            for ach in achievements_list:
                draw_bullet(ach, indent=6.0)

        # ==============================================================
        # 10. STRENGTHS & LANGUAGES
        # ==============================================================

        strengths = _clean_items(resume_data.get("strengths") or resume_data.get("core_strengths"))
        languages = _clean_items(resume_data.get("languages") or resume_data.get("languages_known"))

        if strengths or languages:
            draw_section_header("STRENGTHS & LANGUAGES")
            if strengths:
                draw_paragraph(" • ".join(strengths), gap=1.5)
            if languages:
                draw_paragraph(f"Languages: {', '.join(languages)}", gap=1.5)

        # ==============================================================
        # 11. CUSTOM SECTIONS (e.g. STRENGTHS & LANGUAGES)
        # ==============================================================

        custom_sections = _as_list(resume_data.get("custom_sections"))
        for cs in custom_sections:
            if not isinstance(cs, dict):
                continue
            title = _value(cs, "title", "name", "header")
            items = _clean_items(cs.get("items") or cs.get("bullets"))
            if title and items:
                draw_section_header(title.upper())
                for item in items:
                    if len(items) <= 3 and len(item) < 120 and not item.startswith(("•", "-", "*")):
                        draw_paragraph(item, gap=1.5)
                    else:
                        draw_bullet(item, indent=6.0)

        # --------------------------------------------------------------
        # Finish PDF
        # --------------------------------------------------------------

        pdf_bytes = doc.tobytes(deflate=True)
        doc.close()
        return pdf_bytes

    # ------------------------------------------------------------------
    # Skills
    # ------------------------------------------------------------------

    def _collect_skill_rows(
        self,
        resume_data: Dict[str, Any],
    ) -> List[Tuple[str, str]]:
        """
        Collect skill rows in display order with human-readable labels.

        Canonical field  ->  display label (left column rows first):
          technical       ->  Languages
          frameworks      ->  Frameworks & Libraries
          cloud           ->  Cloud & DevOps
          databases       ->  Databases
          tools           ->  Tools
          cybersecurity   ->  Cybersecurity
          soft            ->  Soft Skills
          other           ->  Other
        """
        raw = (
            resume_data.get("skills")
            or resume_data.get("extracted_skills")
            or {}
        )

        if isinstance(raw, list):
            clean_list = _clean_items(raw)
            if clean_list:
                return [("Technical Skills", ", ".join(clean_list))]
            return []

        if not isinstance(raw, dict):
            return []

        # Ordered: canonical_key -> display_label
        _FIELD_ORDER: List[Tuple[str, str]] = [
            ("technical",     "Languages"),
            ("frameworks",    "Frameworks & Libraries"),
            ("cloud",         "Cloud & DevOps"),
            ("databases",     "Databases"),
            ("tools",         "Tools"),
            ("cybersecurity", "Cybersecurity"),
            ("soft",          "Soft Skills"),
            ("other",         "Other"),
        ]

        rows: List[Tuple[str, str]] = []
        seen: set = set()

        for field_key, display_label in _FIELD_ORDER:
            value = raw.get(field_key)
            if not value:
                continue
            seen.add(field_key)
            if isinstance(value, list):
                values = _clean_items(value)
            elif isinstance(value, str):
                values = [v.strip() for v in value.split(",") if v.strip()]
            else:
                values = [str(value).strip()] if value else []
            values = [v for v in values if v]
            if values:
                rows.append((display_label, ", ".join(values)))

        # Any extra custom keys not in the canonical list
        for key, value in raw.items():
            if str(key).startswith("_") or key in seen:
                continue
            if isinstance(value, list):
                values = _clean_items(value)
            elif isinstance(value, str):
                values = [v.strip() for v in value.split(",") if v.strip()]
            else:
                values = [str(value).strip()] if value else []
            values = [v for v in values if v]
            if not values:
                continue
            label = str(key).strip()
            if "_" in label or label.islower():
                label = label.replace("_", " ").title()
            rows.append((label, ", ".join(values)))

        return rows


    def _skill_line_count(
        self,
        label_or_text: str,
        text_or_width: Any,
        width: Optional[float] = None,
    ) -> int:
        if width is None:
            # Called as _skill_line_count(text, width)
            label = ""
            text = str(label_or_text)
            w = float(text_or_width)
        else:
            label = str(label_or_text)
            text = str(text_or_width)
            w = float(width)

        prefix = f"{label}: " if label else "Languages: "
        label_width = fitz.get_text_length(
            prefix,
            fontname="hebo",
            fontsize=self.BODY_FS,
        )

        first_width = max(
            20.0,
            w - label_width,
        )

        words = text.split()

        if not words:
            return 1

        first = []
        remaining = []

        for word in words:
            candidate = " ".join(first + [word])
            if fitz.get_text_length(
                candidate,
                fontname="helv",
                fontsize=self.BODY_FS,
            ) <= first_width:
                first.append(word)
            else:
                remaining.append(word)

        count = 1

        if remaining:
            rest = " ".join(remaining)
            count += len(
                _wrap_text(
                    rest,
                    self.BODY_FS,
                    w,
                    "helv",
                )
            )

        return count

    def _draw_skill_row(
        self,
        page: fitz.Page,
        left: Tuple[str, str],
        right: Optional[Tuple[str, str]],
        y: float,
        new_page_if_needed,
        draw_text,
    ) -> None:

        def paint(
            row: Tuple[str, str],
            x: float,
        ) -> None:
            label, values = row

            prefix = f"{label}: "

            label_width = fitz.get_text_length(
                prefix,
                fontname="hebo",
                fontsize=self.BODY_FS,
            )

            available = self.column_width - label_width

            words = values.split()
            first: List[str] = []
            rest: List[str] = []

            for word in words:
                candidate = " ".join(first + [word])

                if fitz.get_text_length(
                    candidate,
                    fontname="helv",
                    fontsize=self.BODY_FS,
                ) <= available:
                    first.append(word)
                else:
                    rest.append(word)

            first_text = " ".join(first)

            draw_text(
                prefix,
                x,
                y + self.BODY_FS * 0.85,
                self.BODY_FS,
                "hebo",
                self.BLACK,
            )

            if first_text:
                draw_text(
                    first_text,
                    x + label_width,
                    y + self.BODY_FS * 0.85,
                    self.BODY_FS,
                    "helv",
                    self.BLACK,
                )

            cy = y + self.LINE_HEIGHT

            if rest:
                remaining_text = " ".join(rest)

                for line in _wrap_text(
                    remaining_text,
                    self.BODY_FS,
                    self.column_width,
                    "helv",
                ):
                    draw_text(
                        line,
                        x,
                        cy + self.BODY_FS * 0.85,
                        self.BODY_FS,
                        "helv",
                        self.BLACK,
                    )
                    cy += self.LINE_HEIGHT

        paint(left, self.MARGIN_X)

        if right:
            paint(
                right,
                self.middle_x + self.COLUMN_GAP / 2.0,
            )

    # ------------------------------------------------------------------
    # Experience
    # ------------------------------------------------------------------

    def _draw_experience_bullets(
        self,
        page: fitz.Page,
        bullets: List[str],
        start_y: float,
        new_page_if_needed,
        draw_bullet_at,
    ) -> None:
        if not bullets:
            return

        left_x = self.MARGIN_X + 6.0
        right_x = (
            self.middle_x
            + self.COLUMN_GAP / 2.0
        )

        bullet_width = self.column_width - 6.0

        # Zig-zag distribution:
        # 1 -> left
        # 2 -> right
        # 3 -> left
        # 4 -> right
        #
        # This keeps the two columns compact while preserving every bullet.
        left_items: List[str] = []
        right_items: List[str] = []

        for index, bullet in enumerate(bullets):
         if index % 2 == 0:
          left_items.append(bullet)
         else:
          right_items.append(bullet)

        left_y = start_y
        right_y = start_y

        left_heights = []
        right_heights = []

        for bullet in left_items:
            lines = _wrap_text(
                bullet,
                self.BODY_FS,
                bullet_width - 8.0,
                "helv",
            )
            left_heights.append(
                len(lines) * self.LINE_HEIGHT + 1.2
            )

        for bullet in right_items:
            lines = _wrap_text(
                bullet,
                self.BODY_FS,
                bullet_width - 8.0,
                "helv",
            )
            right_heights.append(
                len(lines) * self.LINE_HEIGHT + 1.2
            )

        needed = max(
            sum(left_heights),
            sum(right_heights),
            self.LINE_HEIGHT,
        )

        # NOTE: no page break here. The caller reserves space before drawing;
        # breaking inside this helper drew the bullets at the previous page's y.

        for bullet in left_items:
            left_y = draw_bullet_at(
                bullet,
                left_x,
                left_y,
                bullet_width,
            )

        for bullet in right_items:
            right_y = draw_bullet_at(
                bullet,
                right_x,
                right_y,
                bullet_width,
            )

    def _experience_block_bottom(
        self,
        bullets: List[str],
        start_y: float,
    ) -> float:
        if not bullets:
            return start_y

        left_height = 0.0
        right_height = 0.0

        width = self.column_width - 14.0

        for index, bullet in enumerate(bullets):
            lines = _wrap_text(
                bullet,
                self.BODY_FS,
                width,
                "helv",
            )

            height = (
                len(lines) * self.LINE_HEIGHT + 1.2
            )

            if index % 2 == 0:
                left_height += height
            else:
                right_height += height

        return start_y + max(
            left_height,
            right_height,
        )

    # ------------------------------------------------------------------
    # Education
    # ------------------------------------------------------------------

    def _format_education(
        self,
        item: Dict[str, Any],
    ) -> str:
        """
        Flexible education formatter.

        Supported entries include:
            Class 10
            Class 12
            Diploma
            Degree
            Any combination of the above.

        The renderer does NOT decide which education level should exist.
        It renders whatever the frontend/canonical parser supplies.
        """

        institution = _value(
            item,
            "institution",
            "school",
            "college",
            "university",
            "institute",
        )

        education_type = _value(
            item,
            "education_type",
            "level",
            "type",
        )

        degree = _value(
            item,
            "degree",
            "qualification",
            "program",
        )

        field = _value(
            item,
            "field_of_study",
            "major",
            "stream",
            "branch",
        )

        score = _value(
            item,
            "gpa",
            "cgpa",
            "percentage",
            "score",
            "grade",
        )

        dates = _value(
            item,
            "dates",
            "period",
        )

        if not dates:
            start = _value(
                item,
                "start_date",
                "from_date",
            )
            end = _value(
                item,
                "end_date",
                "to_date",
                "graduation_year",
            )

            if start and end:
                dates = f"{start}-{end}"
            elif end:
                dates = end
            elif start:
                dates = start

        # If degree and field are separately supplied, display them together.
        qualification = degree

        if field:
            if qualification:
                if field.lower() not in qualification.lower():
                    qualification = (
                        f"{qualification} in {field}"
                    )
            else:
                qualification = field

        # For 10/12 entries, education_type can be the main label.
        if education_type and not qualification:
            qualification = education_type

        parts: List[str] = []

        if institution and qualification:
            parts.append(
                f"{institution} - {qualification}"
            )
        elif institution:
            parts.append(institution)
        elif qualification:
            parts.append(qualification)

        if score:
            score_clean = score

            # Keep explicit percentage/CGPA formatting.
            if "%" not in score_clean and not re.search(
                r"\b(cgpa|gpa)\b",
                score_clean,
                flags=re.IGNORECASE,
            ):
                # Percentages above 10 are normally percentage values.
                numbers = re.findall(
                    r"\d+(?:\.\d+)?",
                    score_clean,
                )

                if numbers:
                    try:
                        numeric = float(numbers[0])
                        if numeric > 10:
                            score_clean += "%"
                        else:
                            score_clean += " CGPA"
                    except ValueError:
                        pass

            parts.append(score_clean)

        if dates:
            parts.append(dates)

        return " | ".join(
            part for part in parts if part
        )

    # ------------------------------------------------------------------
    # Certifications
    # ------------------------------------------------------------------

    def _collect_certifications(
        self,
        resume_data: Dict[str, Any],
    ) -> List[str]:
        certifications = _as_list(
            resume_data.get("certifications")
        )

        result: List[str] = []

        for certification in certifications:
            if isinstance(certification, dict):
                name = _value(
                    certification,
                    "name",
                    "title",
                    "certification",
                )

                issuer = _value(
                    certification,
                    "issuer",
                    "authority",
                    "organization",
                    "institution",
                )

                date = _value(
                    certification,
                    "issue_date",
                    "date",
                    "year",
                    "dates",
                )

                if not name:
                    continue

                if issuer:
                    line = f"{issuer} - {name}"
                else:
                    line = name

                if date:
                    line += f" ({date})"

            else:
                line = _clean_str(certification)

            if line:
                result.append(line)

        # IMPORTANT:
        # Do not substring-deduplicate certifications.
        #
        # Example:
        #   "NPTEL - Programming in Java"
        #   "C-DAC - Cloud Computing"
        #
        # must always remain two separate certifications.
        unique: List[str] = []
        seen = set()

        for line in result:
            key = line.casefold()

            if key not in seen:
                seen.add(key)
                unique.append(line)

        return unique

    # ------------------------------------------------------------------
    # Hobbies
    # ------------------------------------------------------------------

    def _collect_hobbies(
        self,
        resume_data: Dict[str, Any],
    ) -> List[str]:
        hobbies = (
            resume_data.get("hobbies")
            or resume_data.get("interests")
            or []
        )

        return _clean_items(hobbies)


# ---------------------------------------------------------------------------
# Backwards-compatible module-level API
# ---------------------------------------------------------------------------

pdf_generator = ATSPdfGenerator()


def generate_pdf(resume_data: Dict[str, Any]) -> bytes:
    """Generate the ATS-compliant Swapnil Supe Perfect Resume PDF."""
    return pdf_generator.generate_pdf(resume_data)