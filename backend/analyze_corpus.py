# -*- coding: utf-8 -*-
"""
Corpus Analysis Script - runs resume text through the full deterministic pipeline:
  - Weak verb detection and upgrade
  - Bullet length check
  - Missing metrics check
  - spaCy comma structure fix
  - LanguageTool grammar corrections

Generates a side-by-side diff for each bullet.
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(__file__))

from app.generation.resume_rules import (
    check_weak_verbs,
    upgrade_weak_verbs,
    check_bullet_length,
    check_metrics,
    analyze_resume_bullet,
)
from app.generation.structure_parser import clean_compound_predicate_commas_spacy
from app.generation.grammar_checker import correct_grammar, is_grammar_tool_available


CORPUS = {
    "About Me": [
        "Dedicated final-year Computer Engineering student currently pursuing a B.Tech in Computer Engineering, with skills in full-stack development, database management, machine learning, cybersecurity, and FASTPANEL server deployment. Passionate about building scalable, intelligent systems that solve real-world problems and exploring the practical application of AI and emerging technologies.",
    ],
    "Projects — 1D Collision Simulator": [
        "I Build this to understand how elastic collisions work. It shows real-time animation of two objects colliding and calculates their speed after impact.",
    ],
    "Projects — Blood Bank Application": [
        "Build this app so people can easily donate blood or search for it when needed. It keeps track of donor records, blood inventory and requests with a secure login.",
    ],
    "Projects — Techy Store": [
        "Made a shopping app for electronics like desktops, keyboards, monitors and accessories. It runs on both Android and iOS since I used Flutter.",
    ],
    "Projects — Diabetes Prediction": [
        "Developed a machine learning-based web application to predict diabetes risk using patient health parameters, providing quick and accurate health assessments through an Easy-to-use interface.",
    ],
    "Projects — Juice Scanner": [
        "Developed a Python-based web vulnerability scanner that automatically identifies security flaws in OWASP Juice Shop and generates an intuitive web dashboard to display the detected vulnerabilities.",
    ],
    "Internship — Bullet 1": [
        "Serving as the Team Lead for the BIGISO SaaS project, coordinating task assignments, tracking progress, and collaborating with team members to ensure timely project delivery.",
    ],
    "Internship — Bullet 2": [
        "Contributing to the development and maintenance of the BIGISO SaaS platform by implementing both frontend and backend features.",
    ],
    "Internship — Bullet 3": [
        "Deploying and managing web applications using FastPanel, including server setup, domain configuration, SSL installation, and application hosting.",
    ],
    "Internship — Bullet 4": [
        "Collaborating with the development team to integrate new features, fix bugs, and improve application performance.",
    ],
    "Internship — Bullet 5": [
        "Gaining practical exposure to ISO 27001 concepts, including Information Security Management System (ISMS) documentation and compliance processes.",
    ],
    "Internship — Bullet 6": [
        "Participating in code reviews, testing, and debugging to maintain software quality and reliability.",
    ],
}


def pipeline(text: str) -> str:
    """Run text through deterministic layers."""
    s = text.strip()
    s = upgrade_weak_verbs(s)
    s = clean_compound_predicate_commas_spacy(s)
    s = correct_grammar(s)
    return s


def show_diff_inline(original: str, suggested: str) -> str:
    """Show changed words highlighted inline."""
    import difflib
    orig_words = original.split()
    sugg_words = suggested.split()
    matcher = difflib.SequenceMatcher(None, orig_words, sugg_words)
    result = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            result.append(" ".join(orig_words[i1:i2]))
        elif op in ("replace", "insert", "delete"):
            if i1 < i2:
                result.append(f"[-{' '.join(orig_words[i1:i2])}-]")
            if j1 < j2:
                result.append(f"[+{' '.join(sugg_words[j1:j2])}+]")
    return " ".join(result)


SEP = "=" * 72
SUBSEP = "-" * 72

print(f"\n{SEP}")
print("  AI RESUME PIPELINE - CORPUS ANALYSIS REPORT")
print(f"{SEP}")
print(f"  LanguageTool available: {is_grammar_tool_available()}")
print(f"{SEP}\n")

for section, bullets in CORPUS.items():
    print(f"\n{SUBSEP}")
    print(f"  SECTION: {section}")
    print(f"{SUBSEP}")
    for i, bullet in enumerate(bullets, 1):
        audit = analyze_resume_bullet(bullet)
        suggested = pipeline(bullet)
        changed = (suggested.strip() != bullet.strip())

        print(f"\n  ORIGINAL  : {bullet}")
        print(f"  SUGGESTED : {suggested}")
        if changed:
            print(f"\n  DIFF      : {show_diff_inline(bullet, suggested)}")
        else:
            print(f"\n  DIFF      : (no change by deterministic layers)")

        print(f"\n  -- Rule Analysis --")
        print(f"  Quality Score   : {audit['score']}/100")

        wv = check_weak_verbs(bullet)
        print(f"  Weak Verbs      : {wv if wv else 'None (OK)'}")

        lres = check_bullet_length(bullet, min_words=8, max_words=32)
        print(f"  Length          : {lres['word_count']} words - {lres['status']}")

        mres = check_metrics(bullet)
        if mres["has_metrics"]:
            print(f"  Metrics         : {mres['metrics_found']} (OK)")
        else:
            print(f"  Metrics         : [!] None -- add numbers/% for impact")

        if audit["issues"]:
            for iss in audit["issues"]:
                print(f"  Issue           : {iss}")

print(f"\n{SEP}")
print("  REPORT COMPLETE")
print(f"{SEP}\n")
