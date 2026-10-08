"""
TF-IDF Similarity Model (Unigram baseline).
"""
import functools
from app.preprocessing.text_preprocessor import preprocess_text

@functools.lru_cache(maxsize=1)
def _get_sklearn_ops():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    return TfidfVectorizer, cosine_similarity

class TFIDFModel:
    def __init__(self):
        self._vectorizer = None

    @property
    def vectorizer(self):
        if self._vectorizer is None:
            TfidfVectorizer, _ = _get_sklearn_ops()
            self._vectorizer = TfidfVectorizer(ngram_range=(1, 1))
        return self._vectorizer

    def compute_similarity(self, resume_text: str, jd_text: str) -> float:
        """
        Compute TF-IDF cosine similarity between resume text and job description text.
        
        Returns:
            float: Similarity score between 0.0 and 100.0
        """
        clean_resume = preprocess_text(resume_text)
        clean_jd = preprocess_text(jd_text)

        if not clean_resume.strip() or not clean_jd.strip():
            return 0.0

        try:
            _, cosine_similarity = _get_sklearn_ops()
            tfidf_matrix = self.vectorizer.fit_transform([clean_resume, clean_jd])
            sim_score = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
            # Convert float 0-1 to 0-100 percentage
            return float(round(max(0.0, min(1.0, sim_score)) * 100, 2))
        except Exception:
            return 0.0


tfidf_model_instance = TFIDFModel()

def get_tfidf_similarity(resume_text: str, jd_text: str) -> float:
    return tfidf_model_instance.compute_similarity(resume_text, jd_text)
