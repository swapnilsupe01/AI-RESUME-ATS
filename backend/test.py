"""
End-to-end verification script for AI Resume ATS ML & NLP pipeline.
Tests PDF extraction, model comparison (TF-IDF vs N-Grams vs Sentence Embeddings),
skill extraction, and ATS Score report generation.
"""
import os
import sys

# Ensure backend and project root directories are in python sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_app = os.path.abspath(os.path.join(os.path.dirname(__file__), "app"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_app not in sys.path:
    sys.path.insert(0, backend_app)

from app.parser.pdf_parser import extract_text_from_pdf
from app.parser.resume_parser import parse_resume
from app.scoring.ats_scorer import calculate_ats_score
from dataset.generate_sample_pdf import generate_sample_pdf

def run_test():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pdf_path = os.path.join(project_root, "dataset", "resumes", "swapnil_resume.pdf")
    jd_path = os.path.join(project_root, "dataset", "job_descriptions", "ml_engineer_jd.txt")

    # Generate sample PDF if missing
    if not os.path.exists(pdf_path):
        generate_sample_pdf(pdf_path)

    # Read Job Description
    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()

    print("\n========================================================")
    print(" 1. PDF TEXT EXTRACTION TEST")
    print("========================================================")
    resume_text = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(resume_text)} characters from PDF.")
    print("Preview:\n" + resume_text[:250] + "...\n")

    print("========================================================")
    print(" 2. STRUCTURED RESUME PARSING TEST")
    print("========================================================")
    parsed = parse_resume(resume_text)
    print(f"Candidate Name: {parsed['candidate_name']}")
    print(f"Email:          {parsed['email']}")
    print(f"Phone:          {parsed['phone']}")
    print(f"Skills Found:   {parsed['extracted_skills']}")

    print("\n========================================================")
    print(" 3. COMPARATIVE MODEL ANALYSIS & ATS SCORING REPORT")
    print("========================================================")
    result = calculate_ats_score(resume_text, jd_text)

    print(f"\n[+] OVERALL ATS SCORE:    {result['ats_score']}% ({result['match_level']})")
    print("--------------------------------------------------------")
    print(f"[*] TF-IDF Similarity:      {result['tfidf_score']}%")
    print(f"[*] N-Gram (Bigram):        {result['ngram_score']}%")
    print(f"[*] N-Gram Breakdown:       Unigram: {result['ngram_breakdown']['unigram_score']}%, Bigram: {result['ngram_breakdown']['bigram_score']}%, Trigram: {result['ngram_breakdown']['trigram_score']}%")
    print(f"[*] Word Embedding (Semantic): {result['semantic_score']}%")
    print(f"[*] Skill Match Score:       {result['skill_match_score']}%")

    print("\n--------------------------------------------------------")
    print("MATCHED SKILLS:")
    for s in result['matched_skills']:
        print(f"   [V] {s}")

    print("\nMISSING SKILLS:")
    for s in result['missing_skills']:
        print(f"   [X] {s}")

    print("\nRECOMMENDATIONS:")
    for r in result['recommendations']:
        print(f"   - {r}")
    print("========================================================\n")

if __name__ == "__main__":
    run_test()
