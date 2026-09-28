"""
Skill Taxonomy & Dictionary for AI Resume ATS.
Powered by tree.json hierarchical software taxonomy.
Accurately categorizes Programming Languages, Frameworks & Libraries (AI/ML, Web, etc.),
Developer Tools & Platforms, Databases & Storage, and Cloud & DevOps.
"""
import os
import json
import re
from typing import Set, Dict, List, Optional, Any

# Path to the taxonomy tree JSON
_TREE_PATH = os.path.join(os.path.dirname(__file__), "tree.json")

SKILL_CATEGORIES: Dict[str, List[str]] = {}
ALL_SKILLS: Set[str] = set()
SKILL_ALIASES: Dict[str, str] = {}
SKILL_INDEX: Dict[str, Dict[str, Any]] = {}


def _load_and_build_index():
    """Load tree.json and build the inverted search index."""
    global SKILL_CATEGORIES, ALL_SKILLS, SKILL_ALIASES, SKILL_INDEX

    data = None
    if os.path.exists(_TREE_PATH):
        try:
            with open(_TREE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = None

    categories = data.get("categories", {}) if data else {}

    temp_categories: Dict[str, List[str]] = {}
    temp_aliases: Dict[str, str] = {
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
        "golang": "go",
        "k8s": "kubernetes",
        "reactjs": "react",
        "nodejs": "node.js",
        "vuejs": "vue",
        "nextjs": "next.js",
        "amazon web services": "aws",
        "google cloud platform": "gcp",
        "google cloud": "gcp",
        "natural language processing": "nlp",
        "postgres": "postgresql",
        "sentence-bert": "sentence transformers",
        "sbert": "sentence transformers",
        "sklearn": "scikit-learn",
        "tf": "tensorflow",
        "tailwind": "tailwind css",
        "fast api": "fastapi",
    }
    temp_index: Dict[str, Dict[str, Any]] = {}
    temp_all_skills: Set[str] = set()

    for cat_key, cat_val in categories.items():
        cat_display = cat_val.get("display_name", cat_key)
        canonical_field = cat_val.get("canonical_field", "other")
        
        items_list = []
        
        # Direct items
        for item in cat_val.get("items", []):
            name = item.get("name", "")
            if not name:
                continue
            name_lower = name.lower()
            items_list.append(name_lower)
            temp_all_skills.add(name_lower)
            
            meta = {
                "name": name,
                "category_key": cat_key,
                "category_display": cat_display,
                "canonical_field": canonical_field,
                "type": item.get("type", "tool"),
                "host_language": item.get("host_language"),
                "description": item.get("description", "")
            }
            temp_index[name_lower] = meta

            for alias in item.get("aliases", []):
                alias_lower = alias.lower()
                temp_aliases[alias_lower] = name_lower
                temp_all_skills.add(alias_lower)
                temp_index[alias_lower] = meta

        # Subcategories
        for sub_key, sub_val in cat_val.get("subcategories", {}).items():
            for item in sub_val.get("items", []):
                name = item.get("name", "")
                if not name:
                    continue
                name_lower = name.lower()
                items_list.append(name_lower)
                temp_all_skills.add(name_lower)
                
                meta = {
                    "name": name,
                    "category_key": cat_key,
                    "subcategory_key": sub_key,
                    "category_display": cat_display,
                    "subcategory_display": sub_val.get("display_name", sub_key),
                    "canonical_field": canonical_field,
                    "type": item.get("type", "library"),
                    "host_language": item.get("host_language"),
                    "description": item.get("description", "")
                }
                temp_index[name_lower] = meta

                for alias in item.get("aliases", []):
                    alias_lower = alias.lower()
                    temp_aliases[alias_lower] = name_lower
                    temp_all_skills.add(alias_lower)
                    temp_index[alias_lower] = meta

        temp_categories[cat_display] = list(dict.fromkeys(items_list))

    SKILL_CATEGORIES = temp_categories
    SKILL_ALIASES = temp_aliases
    ALL_SKILLS = temp_all_skills
    SKILL_INDEX = temp_index


# Build initial index
_load_and_build_index()


def normalize_skill(skill: str) -> str:
    """Normalize skill name to standard canonical form."""
    cleaned = skill.strip().lower()
    return SKILL_ALIASES.get(cleaned, cleaned)


def get_skill_info(skill: str) -> Optional[Dict[str, Any]]:
    """Return taxonomy metadata for a skill from the tree index."""
    cleaned = skill.strip().lower()
    norm = normalize_skill(cleaned)
    return SKILL_INDEX.get(cleaned) or SKILL_INDEX.get(norm)


def get_skill_category(skill: str) -> str:
    """
    Categorize a skill into:
      'technical' (Programming Languages)
      'frameworks' (Frameworks & Libraries: ML, Web, etc.)
      'tools' (Developer Tools & Platforms)
      'databases' (Databases & Storage)
      'cloud' (Cloud & DevOps)
      'other' (General / Custom)
    """
    info = get_skill_info(skill)
    if info:
        return info.get("canonical_field", "other")

    normalized = normalize_skill(skill)
    norm_lower = normalized.lower()

    for cat_name, skill_list in SKILL_CATEGORIES.items():
        if norm_lower in [s.lower() for s in skill_list]:
            if "Programming Languages" in cat_name:
                return "technical"
            elif "Frameworks" in cat_name or "Libraries" in cat_name:
                return "frameworks"
            elif "Developer Tools" in cat_name or "Methodologies" in cat_name:
                return "tools"
            elif "Databases" in cat_name:
                return "databases"
            elif "Cloud" in cat_name or "DevOps" in cat_name:
                return "cloud"
    return "other"


def extract_skills(text: str) -> Set[str]:
    """
    Extract recognized technical skills from text using multi-word and single-word matching.
    """
    if not text:
        return set()

    found_skills: Set[str] = set()
    normalized_text = re.sub(r'[,;:|/()\[\]{}]', ' ', text.lower())
    cleaned_lower = f" {' '.join(normalized_text.split())} "

    for skill in ALL_SKILLS:
        pattern = f" {skill} "
        if pattern in cleaned_lower:
            found_skills.add(normalize_skill(skill))
        elif f"\n{skill}\n" in cleaned_lower or f"• {skill}" in cleaned_lower or f"- {skill}" in cleaned_lower:
            found_skills.add(normalize_skill(skill))

    return found_skills


