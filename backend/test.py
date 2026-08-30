"""
End-to-End Verification Test Script for AI Resume ATS.
Tests:
  1. PDF text extraction & structured parsing
  2. Multi-model similarity (Sentence-BERT, TF-IDF, N-Grams)
  3. Layer A: Job Compatibility & Skill-level Semantic Matching
  4. Layer B: Public GitHub Project Evidence Extraction & Claim Verification (3-state confidence)
  5. Dual-Intelligence Scoring Synthesis & Explainable Recommendations
"""
import os
import sys
import asyncio

# Fix Windows console UTF-8 encoding
if sys.platform == "win32" and sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend and project root directories are in python sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
backend_app = os.path.abspath(os.path.join(os.path.dirname(__file__), "app"))

for p in [project_root, backend_dir, backend_app]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.parser.pdf_parser import extract_text_from_pdf
from app.parser.resume_parser import parse_resume
from app.scoring.final_scorer import analyze_resume_intelligence
from dataset.generate_sample_pdf import generate_sample_pdf

async def run_end_to_end_test():
    print("\n========================================================")
    print(" [*] AI RESUME ATS -- DUAL-INTELLIGENCE VERIFICATION TEST")
    print("========================================================")

    pdf_path = os.path.join(project_root, "dataset", "resumes", "swapnil_resume.pdf")
    jd_path = os.path.join(project_root, "dataset", "job_descriptions", "ml_engineer_jd.txt")

    # 1. Generate sample PDF if missing
    if not os.path.exists(pdf_path):
        generate_sample_pdf(pdf_path)

    # 2. Read Job Description
    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()

    # 3. PDF Extraction
    print("\n[STEP 1] PDF TEXT EXTRACTION & LINK PARSING")
    print("--------------------------------------------------------")
    resume_text = extract_text_from_pdf(pdf_path)
    parsed = parse_resume(resume_text)
    print(f"Candidate Name:  {parsed['candidate_name']}")
    print(f"Email:           {parsed['email']}")
    print(f"Phone:           {parsed['phone']}")
    print(f"GitHub Links:    {parsed['github_urls']}")
    print(f"Portfolio Links: {parsed['portfolio_urls']}")
    print(f"Extracted Skills:{len(parsed['extracted_skills'])} skills detected")

    # 4. Run Full Dual-Layer Intelligence Engine
    print("\n[STEP 2] RUNNING DUAL-LAYER AI INTELLIGENCE ENGINE...")
    print("--------------------------------------------------------")
    report = await analyze_resume_intelligence(resume_text, jd_text)

    print("\n========================================================")
    print(f" [+] OVERALL PROFILE SCORE: {report['overall_profile_score']}%")
    print("========================================================")
    
    # Layer A Breakdown
    jm = report["job_match"]
    print(f"\n[LAYER A: JOB MATCH INTELLIGENCE]")
    print(f"  * Job Match Score:         {jm['score']}% ({jm['match_level']})")
    print(f"  * Skill Match Score:       {jm['skill_match_score']}%")
    print(f"  * Semantic Skill Score:    {jm['semantic_skill_score']}%")
    print(f"  * Sentence-BERT Alignment: {jm['document_semantic_score']}%")
    print(f"  * TF-IDF Unigram Match:    {jm['tfidf_score']}%")
    print(f"  * Experience Alignment:    {jm['experience_match_score']}%")
    print(f"  * Matched Skills ({len(jm['matched_skills'])}): {', '.join(jm['matched_skills'][:6])}...")
    print(f"  * Missing Skills ({len(jm['missing_skills'])}): {', '.join(jm['missing_skills'][:4])}...")

    # Layer B Breakdown
    pe = report["project_evidence"]
    print(f"\n[LAYER B: PUBLIC PROJECT EVIDENCE INTELLIGENCE]")
    print(f"  * Evidence Score:          {pe['score']}% ({pe['evidence_level']})")
    print(f"  * Total Claims Verified:   {pe['total_claims_analyzed']}")
    print(f"  * [V] Verified Claims:     {pe['verified_claims_count']}")
    print(f"  * [~] Partial Claims:      {pe['partial_claims_count']}")
    print(f"  * [X] Unsupported Claims:  {pe['unsupported_claims_count']}")
    print(f"  * GitHub Repos Analyzed:   {len(pe['github_repositories'])}")

    print("\n[CLAIMS <-> EVIDENCE SAMPLE VERIFICATION]")
    for proj in pe["project_reports"]:
        print(f"\n  Project: {proj['project_title']} (Score: {proj['verification_score']}%)")
        for c in proj["claims_breakdown"][:3]:
            badge = "[V]" if c["badge"] == "verified" else ("[~]" if c["badge"] == "partial" else "[X]")
            print(f"    {badge} [{c['similarity_score']}%] {c['claim']} -> {c['status']}")

    print("\n[ACTIONABLE RECOMMENDATIONS]")
    for i, rec in enumerate(report["recommendations"][:4], 1):
        print(f"  {i}. {rec}")

    print("\n========================================================")
    print(" [V] ALL PIPELINE TESTS COMPLETED SUCCESSFULLY!")
    print("========================================================\n")

if __name__ == "__main__":
    asyncio.run(run_end_to_end_test())
