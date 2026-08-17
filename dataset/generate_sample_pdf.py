"""
Helper script to generate a sample resume PDF for local testing.
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

SUMMARY:
Passionate Computer Engineering student with expertise in Python, Machine Learning, FastAPI, and Web Development. Strong foundation in NLP and Data Science.

SKILLS:
• Programming: Python, Java, SQL, C++, JavaScript
• Frameworks & Web: FastAPI, React, Node.js, REST API
• AI / ML: Machine Learning, NLP, scikit-learn, TensorFlow, PyTorch, Pandas, NumPy
• Tools: Git, Docker, Linux, VS Code

EDUCATION:
B.Tech Computer Engineering - Current (Senior Year)
Relevant Coursework: Data Structures, Machine Learning, Database Management Systems, NLP.

PROJECTS:
1. AI Resume Screening System:
   Built an automated ATS candidate evaluation tool comparing TF-IDF, N-Grams, and Sentence Transformers embeddings.
2. Smart Hospital Management App:
   Developed a full-stack health platform using FastAPI, React, and SQL database.

CERTIFICATIONS:
• Machine Learning Specialization by DeepLearning.AI
• Python Developer Certificate
"""

    rect = fitz.Rect(50, 50, 550, 800)
    page.insert_textbox(rect, text, fontsize=11, fontname="helv")
    doc.save(output_path)
    doc.close()
    print(f"Sample PDF created at {output_path}")

if __name__ == "__main__":
    generate_sample_pdf("dataset/resumes/swapnil_resume.pdf")
