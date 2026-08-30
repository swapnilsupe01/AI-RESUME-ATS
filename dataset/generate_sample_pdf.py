"""
Helper script to generate a sample resume PDF with Public GitHub and LinkedIn Evidence.
"""
import os
import pymupdf as fitz

def generate_sample_pdf(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = fitz.open()
    page = doc.new_page()
    
    text = """SWAPNIL SUPE
Computer Engineering Student | ML & Software Developer
Email: swapnil@example.com | Phone: (555) 019-2834
GitHub: https://github.com/swapnilsupe01 | LinkedIn: https://linkedin.com/in/swapnilsupe01 | Portfolio: https://swapnilsupe.dev

SUMMARY:
Passionate Computer Engineering student with expertise in Python, Machine Learning, FastAPI, and Cloud Containerization. Strong foundation in NLP, Sentence-BERT, and Full-Stack development.

SKILLS:
• Programming: Python, Java, SQL, C++, JavaScript, TypeScript
• AI / ML: Machine Learning, NLP, Sentence Transformers, scikit-learn, PyTorch, Pandas, NumPy, TF-IDF
• Web & Frameworks: FastAPI, React, Node.js, REST API, HTML/CSS
• DevOps & Cloud: Docker, Kubernetes, Linux, Git, GitHub Actions, AWS

EDUCATION:
B.Tech Computer Engineering - Senior Year
Relevant Coursework: Data Structures & Algorithms, Machine Learning, Database Management Systems, NLP.

EXPERIENCE:
Machine Learning & Software Developer Intern (2023 - Present)
• Designed and developed AI-powered ATS resume screening system utilizing Sentence-BERT embeddings, PyMuPDF, and FastAPI.
• Integrated Docker multi-stage containerization and automated Jenkins CI/CD testing pipelines.

PROJECTS:
1. AI Resume ATS (GitHub: https://github.com/swapnilsupe01/ai-resume-ats):
   Built an intelligent Explainable Resume Screening System using Python, FastAPI, Sentence Transformers, PyMuPDF, scikit-learn, and Docker. Implemented skill-level semantic matching and public project evidence verification.
2. Smart Hospital Management App (GitHub: https://github.com/swapnilsupe01/smart-hospital):
   Developed a full-stack health platform using FastAPI, React, and PostgreSQL database. Containerized with Docker Compose.

CERTIFICATIONS:
• Machine Learning Specialization by DeepLearning.AI
• Python Developer Professional Certificate
• Docker & Containerization Fundamentals
"""

    rect = fitz.Rect(50, 50, 550, 800)
    page.insert_textbox(rect, text, fontsize=11, fontname="helv")
    doc.save(output_path)
    doc.close()
    print(f"[+] Sample PDF created at: {output_path}")

if __name__ == "__main__":
    generate_sample_pdf("dataset/resumes/swapnil_resume.pdf")
