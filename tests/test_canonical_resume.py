"""
Unit tests for Canonical Resume Schema and Pydantic Model Validation.
"""
import pytest
import json
from app.models.canonical_resume import (
    CanonicalResume, Profile, ExperienceItem, ProjectItem,
    EducationItem, CategorizedSkills, generate_id
)
from app.parser.canonical_parser import get_synthetic_sample_resume


def test_canonical_resume_creation_and_defaults():
    resume = CanonicalResume()
    assert resume.profile.name == ""
    assert resume.summary == ""
    assert len(resume.experience) == 0
    assert len(resume.projects) == 0
    assert len(resume.skills.technical) == 0


def test_canonical_resume_serialization_roundtrip():
    sample = get_synthetic_sample_resume()
    json_data = sample.model_dump_json()
    assert "Alex Chen" in json_data
    assert "Nexus AI Systems" in json_data

    # Deserialize back
    restored = CanonicalResume.model_validate_json(json_data)
    assert restored.profile.name == "Alex Chen"
    assert restored.profile.email == "alex.chen.dev@example.com"
    assert len(restored.experience) == 2
    assert len(restored.projects) == 2
    assert "Python" in restored.skills.technical


def test_categorized_skills_all_skills():
    skills = CategorizedSkills(
        technical=["Python", "Go"],
        frameworks=["FastAPI", "React"],
        cloud=["AWS", "Docker"],
        databases=["PostgreSQL"]
    )
    flat = skills.all_skills()
    assert "Python" in flat
    assert "FastAPI" in flat
    assert "AWS" in flat
    assert "PostgreSQL" in flat
    assert len(flat) == 7


def test_unique_id_generation():
    id1 = generate_id("exp")
    id2 = generate_id("exp")
    assert id1.startswith("exp_")
    assert id2.startswith("exp_")
    assert id1 != id2
