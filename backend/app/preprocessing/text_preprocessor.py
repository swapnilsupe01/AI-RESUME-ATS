"""
Text preprocessor module for AI Resume ATS.
Normalizes text while preserving technical terminology and symbols.
"""
import re
from typing import List

# Common English stopwords to remove for TF-IDF / N-gram preprocessing
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't",
    "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll",
    "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's",
    "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on",
    "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
    "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some",
    "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we",
    "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with",
    "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your",
    "yours", "yourself", "yourselves", "resume", "curriculum", "vitae", "summary", "profile",
    "looking", "seeking", "opportunity", "role", "position", "worked", "working", "responsible"
}

# Protected technical tokens mapping to avoid punctuation strip errors
PROTECTED_TERMS = {
    "c++": "cpptoken",
    "c#": "csharptoken",
    ".net": "dotnettoken",
    "node.js": "nodejstoken",
    "react.js": "reactjstoken",
    "vue.js": "vuejstoken",
    "next.js": "nextjstoken",
    "express.js": "expressjstoken",
    "ci/cd": "cicdtoken",
}

REVERSE_PROTECTED_TERMS = {v: k for k, v in PROTECTED_TERMS.items()}

def preprocess_text(text: str, remove_stopwords: bool = True) -> str:
    """
    Clean and normalize text for TF-IDF and N-Gram extraction.
    
    1. Lowercases text
    2. Protects technical symbols (C++, C#, .NET, Node.js)
    3. Removes non-alphanumeric characters (except protected placeholders)
    4. Removes custom stopwords
    5. Re-instates canonical technical tokens
    """
    if not text:
        return ""

    lowered = text.lower()

    # Step 1: Protect technical terms
    for term, placeholder in PROTECTED_TERMS.items():
        lowered = re.sub(r'(?<![a-z0-9])' + re.escape(term) + r'(?![a-z0-9])', f" {placeholder} ", lowered)

    # Step 2: Replace special punctuation with space
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', lowered)

    # Step 3: Tokenize
    tokens = cleaned.split()

    # Step 4: Stopword removal
    if remove_stopwords:
        tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]

    # Step 5: Restore protected terms
    final_tokens = []
    for t in tokens:
        if t in REVERSE_PROTECTED_TERMS:
            final_tokens.append(REVERSE_PROTECTED_TERMS[t])
        else:
            final_tokens.append(t)

    return " ".join(final_tokens)
