"""
Canonical Resume Data Model for AI Resume Intelligence & Evidence Platform.
Pydantic v2 schemas representing the single internal source of truth for resume data.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


def generate_id(prefix: str = "item") -> str:
    """Generate a stable unique identifier for resume items."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class Profile(BaseModel):
    name: str = Field(default="", description="Candidate's full name")
    headline: str = Field(default="", description="Target job title or professional headline")
    email: str = Field(default="", description="Contact email address")
    phone: str = Field(default="", description="Contact phone number")
    location: str = Field(default="", description="City, State / Country or Remote")
    github: str = Field(default="", description="Primary GitHub profile URL or username")
    linkedin: str = Field(default="", description="LinkedIn profile URL or handle")
    portfolio: str = Field(default="", description="Personal portfolio or website URL")


class ExperienceItem(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("exp"))
    company: str = Field(default="", description="Company or organization name")
    role: str = Field(default="", description="Position or title held")
    location: str = Field(default="", description="Company location or Remote")
    start_date: str = Field(default="", description="Start date (e.g., 'Jan 2022')")
    end_date: str = Field(default="", description="End date (e.g., 'Present' or 'Dec 2023')")
    current: bool = Field(default=False, description="Whether currently working here")
    highlights: List[str] = Field(default_factory=list, description="Measurable achievements / bullet points")
    technologies: List[str] = Field(default_factory=list, description="Technologies / frameworks used")


class ProjectItem(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("proj"))
    name: str = Field(default="", description="Project title")
    description: str = Field(default="", description="Brief summary of project purpose and architecture")
    highlights: List[str] = Field(default_factory=list, description="Bullet points detailing implementation & metrics")
    technologies: List[str] = Field(default_factory=list, description="Key languages, frameworks, tools used")
    github_url: str = Field(default="", description="Public GitHub repository URL")
    live_url: str = Field(default="", description="Live deployment or demo URL")


class EducationItem(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("edu"))
    institution: str = Field(default="", description="University or institution name")
    degree: str = Field(default="", description="Degree type (e.g., 'B.S.', 'M.S.')")
    field_of_study: str = Field(default="", description="Major / field of study")
    start_date: str = Field(default="", description="Start year / date")
    end_date: str = Field(default="", description="Graduation year / date")
    gpa: str = Field(default="", description="GPA or grade score if provided")
    honors: List[str] = Field(default_factory=list, description="Academic honors, awards, or coursework")


class CategorizedSkills(BaseModel):
    technical: List[str] = Field(default_factory=list, description="Core programming languages & libraries")
    tools: List[str] = Field(default_factory=list, description="Developer tools, IDEs, CI/CD, Git")
    cloud: List[str] = Field(default_factory=list, description="Cloud platforms & infrastructure (AWS, GCP, Azure)")
    databases: List[str] = Field(default_factory=list, description="Databases & caching systems (PostgreSQL, Redis, MongoDB)")
    frameworks: List[str] = Field(default_factory=list, description="Application frameworks (FastAPI, React, Spring Boot)")
    soft: List[str] = Field(default_factory=list, description="Leadership, collaboration, communication skills")
    other: List[str] = Field(default_factory=list, description="Other recognized competencies")

    def all_skills(self) -> List[str]:
        """Return a deduplicated, flattened list of all categorized skills."""
        combined = []
        for group in [self.technical, self.tools, self.cloud, self.databases, self.frameworks, self.soft, self.other]:
            for s in group:
                if s and s.strip() and s.strip() not in combined:
                    combined.append(s.strip())
        return combined


class CertificationItem(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("cert"))
    name: str = Field(default="", description="Certification name")
    issuer: str = Field(default="", description="Issuing organization (e.g., AWS, Google Cloud, CKA)")
    issue_date: str = Field(default="", description="Date issued")
    credential_url: str = Field(default="", description="Verification URL or credential ID")


class AchievementItem(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("ach"))
    title: str = Field(default="", description="Award or achievement title")
    description: str = Field(default="", description="Context, scope, or impact")
    date: str = Field(default="", description="Date or year achieved")


class CustomSectionItem(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("sec"))
    title: str = Field(default="", description="Section header")
    items: List[str] = Field(default_factory=list, description="Lines or bullet points")


class CanonicalResume(BaseModel):
    """
    Canonical Resume JSON schema.
    The single internal representation consumed by editors, templates, AI assistants, and analyzers.
    """
    profile: Profile = Field(default_factory=Profile)
    summary: str = Field(default="", description="Professional summary or bio")
    experience: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    skills: CategorizedSkills = Field(default_factory=CategorizedSkills)
    certifications: List[CertificationItem] = Field(default_factory=list)
    achievements: List[AchievementItem] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list, description="All detected external URLs")
    custom_sections: List[CustomSectionItem] = Field(default_factory=list)
