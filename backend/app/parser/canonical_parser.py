"""
Canonical Parser Orchestrator.
Coordinates:
  PyMuPDF Byte Extraction -> Positional Blocks -> Markdown Pipeline -> CanonicalResume
Emits confidence warnings when sections or key metadata are missing.
"""
from typing import Dict, Any, List, Optional, Tuple
import fitz  # PyMuPDF
from app.models.canonical_resume import (
    CanonicalResume, Profile, ExperienceItem, ProjectItem,
    EducationItem, CategorizedSkills, CertificationItem, AchievementItem,
    generate_id
)
from app.parser.pdf_parser import extract_text_and_links_from_bytes
from app.parser.markdown_pipeline import (
    blocks_to_markdown, markdown_to_canonical, canonical_to_markdown
)


def parse_pdf_bytes_to_canonical(
    pdf_bytes: bytes,
    additional_links: Optional[List[str]] = None
) -> Tuple[CanonicalResume, str, List[str]]:
    """
    Ingest raw PDF bytes, convert to structured Markdown (.md), and construct CanonicalResume.
    Returns:
      (canonical_resume, markdown_text, warnings)
    """
    warnings: List[str] = []

    if not pdf_bytes:
        warnings.append("Uploaded file is empty.")
        return CanonicalResume(), "", warnings

    doc = None
    all_blocks = []
    pdf_links: List[str] = []
    plain_text = ""

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            plain_text += page.get_text() + "\n"
            page_blocks = page.get_text("blocks")
            all_blocks.extend(page_blocks)

            # Extract embedded URIs
            for link in page.get_links():
                uri = link.get("uri")
                if uri and uri.startswith("http") and uri not in pdf_links:
                    pdf_links.append(uri)
    except Exception as e:
        warnings.append(f"PyMuPDF block extraction failed: {str(e)}. Falling back to plain text.")
    finally:
        if doc:
            doc.close()

    combined_links = list(set((additional_links or []) + pdf_links))

    # 1. Convert blocks to structured Markdown
    if all_blocks:
        markdown_text = blocks_to_markdown(all_blocks)
    else:
        # Fallback to plain text
        markdown_text = plain_text

    if not markdown_text.strip():
        warnings.append("No readable text found in document. Ensure the PDF is not an image scan.")
        return CanonicalResume(), "", warnings

    # 2. Convert Markdown to Canonical Resume JSON
    resume = markdown_to_canonical(markdown_text, additional_links=combined_links)

    # 3. Quality warnings
    if not resume.profile.name or resume.profile.name.lower() in ["candidate", "resume", "curriculum vitae"]:
        warnings.append("Could not confidently identify candidate name. Please review profile.")
    if not resume.profile.email:
        warnings.append("No email address detected. An ATS may reject resumes without contact info.")
    if not resume.skills.all_skills():
        warnings.append("No technical skills explicitly detected in document.")
    if not resume.experience:
        warnings.append("No structured work experience entries could be parsed.")

    # Generate final clean markdown representation from canonical object
    clean_md = canonical_to_markdown(resume)
    return resume, clean_md, warnings


def parse_text_to_canonical(
    text: str,
    additional_links: Optional[List[str]] = None
) -> Tuple[CanonicalResume, str, List[str]]:
    """
    Parse raw text or markdown directly into CanonicalResume.
    """
    warnings: List[str] = []
    if not text.strip():
        warnings.append("Provided text is empty.")
        return CanonicalResume(), "", warnings

    resume = markdown_to_canonical(text, additional_links)

    if not resume.profile.name:
        warnings.append("Could not identify candidate name from text.")
    if not resume.profile.email:
        warnings.append("No email address found.")

    clean_md = canonical_to_markdown(resume)
    return resume, clean_md, warnings


def get_synthetic_sample_resume() -> CanonicalResume:
    """
    Generate a high-caliber synthetic sample resume for product demonstration.
    Contains realistic claims, metrics, and public GitHub repository links.
    """
    return CanonicalResume(
        profile=Profile(
            name="Alex Chen",
            headline="Staff Machine Learning & Full-Stack Systems Engineer",
            email="alex.chen.dev@example.com",
            phone="+1 (555) 382-9104",
            location="San Francisco, CA (Remote)",
            github="https://github.com/swapnilsupe01",
            linkedin="https://linkedin.com/in/swapnilsupe01",
            portfolio="https://alexchen.dev"
        ),
        summary=(
            "Staff Software Engineer with 7+ years of experience architecting distributed AI systems, "
            "production ML microservices, and high-concurrency cloud infrastructure. Specialized in "
            "Sentence-BERT semantic search, real-time streaming pipelines, and explainable AI applications."
        ),
        experience=[
            ExperienceItem(
                id=generate_id("exp"),
                company="Nexus AI Systems",
                role="Senior ML Infrastructure Engineer",
                location="San Francisco, CA",
                start_date="Jan 2022",
                end_date="Present",
                current=True,
                highlights=[
                    "Architected distributed real-time embedding inference cluster processing 45M daily vector queries with sub-25ms p99 latency.",
                    "Reduced cloud compute expenses by 38% ($140k/yr) by optimizing PyTorch models via ONNX quantization and TensorRT runtime.",
                    "Spearheaded multi-tenant vector retrieval architecture using FastAPI, Redis caching, and PostgreSQL pgvector."
                ],
                technologies=["Python", "FastAPI", "PyTorch", "Docker", "Kubernetes", "PostgreSQL", "Redis", "AWS"]
            ),
            ExperienceItem(
                id=generate_id("exp"),
                company="CloudScale Networks",
                role="Full Stack Software Engineer",
                location="Seattle, WA",
                start_date="Jun 2018",
                end_date="Dec 2021",
                current=False,
                highlights=[
                    "Engineered REST microservices and WebSocket endpoints in Go and Python serving 1.2M active enterprise users.",
                    "Pioneered automated CI/CD deployment workflows in GitHub Actions and Docker, reducing release cycle time by 65%.",
                    "Built reactive management dashboards in TypeScript and React with 99.98% operational uptime."
                ],
                technologies=["Go", "Python", "React", "TypeScript", "Docker", "CI/CD", "PostgreSQL"]
            )
        ],
        projects=[
            ProjectItem(
                id=generate_id("proj"),
                name="AI Resume ATS Intelligence Engine",
                description="Explainable semantic ATS matching and public project evidence verification platform.",
                highlights=[
                    "Implemented multi-model semantic pipeline combining Sentence-BERT embeddings, TF-IDF, and n-gram phrase scoring.",
                    "Built automated public GitHub forensics analyzer auditing commit history, languages, and technical dependencies.",
                    "Designed interactive WYSIWYG resume canvas with real-time keyword gap auditing."
                ],
                technologies=["Python", "FastAPI", "Sentence-BERT", "PyTorch", "Docker", "Tailwind CSS"],
                github_url="https://github.com/swapnilsupe01/AI-RESUME-ATS",
                live_url="https://ai-resume-ats.demo.app"
            ),
            ProjectItem(
                id=generate_id("proj"),
                name="Distributed Vector Cache",
                description="High-throughput in-memory embedding cache with LRU eviction and cosine similarity search.",
                highlights=[
                    "Benchmarked vector retrieval achieving 12,000 queries per second with 4ms latency.",
                    "Integrated Prometheus observability metrics and structured JSON logging."
                ],
                technologies=["Python", "Redis", "NumPy", "Prometheus"],
                github_url="https://github.com/swapnilsupe01",
                live_url=""
            )
        ],
        education=[
            EducationItem(
                id=generate_id("edu"),
                institution="University of Washington",
                degree="B.S.",
                field_of_study="Computer Science",
                start_date="2014",
                end_date="2018",
                gpa="3.85 / 4.0",
                honors=["Dean's Honor List", "ACM Collegiate Programming Finalist"]
            )
        ],
        skills=CategorizedSkills(
            technical=["Python", "Go", "TypeScript", "SQL", "C++", "PyTorch", "NumPy", "Pandas", "Scikit-Learn"],
            frameworks=["FastAPI", "Flask", "React", "Next.js", "Django"],
            cloud=["AWS", "Docker", "Kubernetes", "CI/CD", "Linux", "Terraform", "GitHub Actions"],
            databases=["PostgreSQL", "Redis", "MongoDB", "Elasticsearch"],
            tools=["Git", "Pytest", "Jira", "Prometheus", "Grafana"],
            soft=["System Design", "Engineering Leadership", "Agile Architecture", "Mentorship"]
        ),
        certifications=[
            CertificationItem(
                id=generate_id("cert"),
                name="AWS Certified Solutions Architect – Professional",
                issuer="Amazon Web Services",
                issue_date="2023",
                credential_url="https://aws.amazon.com/verification"
            )
        ],
        achievements=[
            AchievementItem(
                id=generate_id("ach"),
                title="Engineering Impact Award",
                description="Recognized for reducing company-wide cloud compute infrastructure spend by 38%",
                date="2023"
            )
        ],
        links=[
            "https://github.com/swapnilsupe01/AI-RESUME-ATS",
            "https://linkedin.com/in/swapnilsupe01"
        ]
    )
