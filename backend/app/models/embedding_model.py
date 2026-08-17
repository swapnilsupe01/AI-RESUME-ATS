"""
Word & Sentence Embedding Model using Sentence Transformers (all-MiniLM-L6-v2).
Computes deep semantic similarity between resume and job description.
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.preprocessing.text_preprocessor import preprocess_text

class EmbeddingModel:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_attempts = False

    def _ensure_loaded(self):
        if not self._load_attempts:
            self._load_attempts = True
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                print(f"[Warning] SentenceTransformer load failed: {e}. Fallback embedding will be used.")
                self.model = None

    def compute_similarity(self, resume_text: str, jd_text: str) -> float:
        """
        Encode raw/preprocessed text using SentenceTransformer and compute cosine similarity.
        
        Returns:
            float: Score from 0.0 to 100.0
        """
        self._ensure_loaded()
        
        clean_resume = preprocess_text(resume_text, remove_stopwords=False)
        clean_jd = preprocess_text(jd_text, remove_stopwords=False)

        if not clean_resume.strip() or not clean_jd.strip():
            return 0.0

        if self.model is not None:
            try:
                embeddings = self.model.encode([clean_resume, clean_jd])
                sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                return float(round(max(0.0, min(1.0, float(sim))) * 100, 2))
            except Exception as e:
                print(f"[Embedding Error]: {e}")

        # Fallback to character/word n-gram vector semantic approximation if transformer fails
        return self._fallback_similarity(clean_resume, clean_jd)

    def _fallback_similarity(self, text1: str, text2: str) -> float:
        from sklearn.feature_extraction.text import CountVectorizer
        try:
            cv = CountVectorizer(analyzer="char_wb", ngram_range=(3, 5))
            mat = cv.fit_transform([text1, text2])
            sim = cosine_similarity(mat[0], mat[1])[0][0]
            return float(round(max(0.0, min(1.0, float(sim))) * 100, 2))
        except Exception:
            return 0.0

embedding_model_instance = EmbeddingModel()

def get_embedding_similarity(resume_text: str, jd_text: str) -> float:
    return embedding_model_instance.compute_similarity(resume_text, jd_text)
