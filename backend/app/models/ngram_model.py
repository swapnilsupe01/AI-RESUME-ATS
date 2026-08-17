"""
N-Gram Similarity Model (Unigrams, Bigrams, Trigrams).
"""
from typing import Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.preprocessing.text_preprocessor import preprocess_text

class NGramModel:
    def __init__(self):
        pass

    def compute_similarity(self, resume_text: str, jd_text: str, ngram_range: Tuple[int, int] = (1, 2)) -> float:
        """
        Compute N-Gram TF-IDF similarity between resume and JD.
        
        Args:
            resume_text (str): Raw or preprocessed resume.
            jd_text (str): Raw or preprocessed job description.
            ngram_range (Tuple[int, int]): (1, 2) for Bigrams, (1, 3) for Trigrams.
            
        Returns:
            float: Score from 0.0 to 100.0
        """
        clean_resume = preprocess_text(resume_text)
        clean_jd = preprocess_text(jd_text)

        if not clean_resume.strip() or not clean_jd.strip():
            return 0.0

        try:
            vectorizer = TfidfVectorizer(ngram_range=ngram_range)
            tfidf_matrix = vectorizer.fit_transform([clean_resume, clean_jd])
            sim_score = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
            return float(round(max(0.0, min(1.0, sim_score)) * 100, 2))
        except Exception:
            return 0.0

    def compute_all_ngram_breakdowns(self, resume_text: str, jd_text: str) -> Dict[str, float]:
        """
        Computes similarity for Unigram, Bigram, and Trigram individually and combined.
        """
        return {
            "unigram_score": self.compute_similarity(resume_text, jd_text, (1, 1)),
            "bigram_score": self.compute_similarity(resume_text, jd_text, (1, 2)),
            "trigram_score": self.compute_similarity(resume_text, jd_text, (1, 3)),
        }

ngram_model_instance = NGramModel()

def get_ngram_similarity(resume_text: str, jd_text: str, ngram_range: Tuple[int, int] = (1, 2)) -> float:
    return ngram_model_instance.compute_similarity(resume_text, jd_text, ngram_range)

def get_ngram_breakdowns(resume_text: str, jd_text: str) -> Dict[str, float]:
    return ngram_model_instance.compute_all_ngram_breakdowns(resume_text, jd_text)
