"""
Latent Dirichlet Allocation (LDA) Topic Modeler & Domain Divergence Analyzer.
Academic Foundation:
  - Paper 4: Learning to Match Jobs with Resumes from Sparse Interaction Data
    using Multi-View Co-Teaching Network (Bian, Chen, Zhao, Zhou, Hou, Song, Zhang, Wen; CIKM 2020).
  - AML Course Outcome CO6: Topic Modeling (LDA), High-Dimensional NLP Representations.

Provides:
  1. Latent Dirichlet Allocation (LDA) topic decomposition for candidate resumes and vacancies.
  2. Topic probability distribution calculation: θ_resume and θ_jd.
  3. Domain congruence measurement using Jensen-Shannon Divergence and Cosine Topic Similarity.
  4. Interpretable topic keyword identification for recruitment explanations.
"""
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from scipy.spatial.distance import jensenshannon

# Default Topic Names based on typical software engineering & data roles
TOPIC_LABELS: Dict[int, str] = {
    0: "Artificial Intelligence, Machine Learning & Deep Learning",
    1: "Cloud Infrastructure, Containerization & DevOps",
    2: "Full-Stack Web Development & Microservices",
    3: "Data Engineering, Big Data & Database Systems"
}

# Domain seed documents to anchor LDA topics reliably
DOMAIN_SEED_CORPUS = [
    # Topic 0: AI / ML
    "machine learning deep learning pytorch tensorflow neural networks scikit-learn transformers huggingface nlp computer vision model training evaluation cross-validation hyperparameter tuning algorithms",
    # Topic 1: DevOps / Cloud
    "docker kubernetes aws amazon web services terraform ci cd continuous integration deployment linux prometheus grafana ansible bash cloud architecture infrastructure monitoring",
    # Topic 2: Web / Full-Stack
    "fastapi python django react javascript typescript rest api microservices graphql html css postgresql redis node frontend backend web development frontend",
    # Topic 3: Data / Database
    "sql etl spark pyspark hadoop data pipelines database mongodb postgresql warehousing bigquery snowflake analytics queries modeling kafka streaming"
]


class LDATopicEngine:
    """
    Topic Modeling Engine using Latent Dirichlet Allocation (scikit-learn).
    """

    def __init__(self, n_topics: int = 4, max_features: int = 500):
        self.n_topics = n_topics
        self.max_features = max_features
        self.vectorizer = CountVectorizer(
            max_features=self.max_features,
            stop_words='english',
            token_pattern=r'(?u)\b[a-zA-Z][a-zA-Z0-9_\-\.]{1,}\b'
        )
        self.lda_model = LatentDirichletAllocation(
            n_components=self.n_topics,
            random_state=42,
            learning_method='batch',
            max_iter=30
        )
        self._is_fitted = False
        self._initialize_engine()

    def _initialize_engine(self):
        """Fit on domain seed documents to guarantee stable topic definitions."""
        try:
            dtm = self.vectorizer.fit_transform(DOMAIN_SEED_CORPUS)
            self.lda_model.fit(dtm)
            self._is_fitted = True
        except Exception:
            self._is_fitted = False

    def get_topic_keywords(self, top_n: int = 6) -> Dict[str, List[str]]:
        """Return the most important keywords for each discovered topic."""
        if not self._is_fitted:
            return {}
        feature_names = self.vectorizer.get_feature_names_out()
        topic_dict = {}
        for idx, topic in enumerate(self.lda_model.components_):
            top_features_ind = topic.argsort()[:-top_n - 1:-1]
            top_words = [feature_names[i] for i in top_features_ind]
            label = TOPIC_LABELS.get(idx, f"Topic {idx}")
            topic_dict[label] = top_words
        return topic_dict

    def infer_topic_distribution(self, text: str) -> np.ndarray:
        """
        Infers the topic mixture vector θ for a given document.
        Returns a normalized probability distribution of length `n_topics`.
        """
        if not self._is_fitted or not text or len(text.strip()) < 10:
            return np.ones(self.n_topics) / self.n_topics

        # If document introduces novel technical tokens, combine and transform
        dtm = self.vectorizer.transform([text])
        dist = self.lda_model.transform(dtm)[0]
        # Normalize to ensure proper simplex probability
        s = np.sum(dist)
        return dist / s if s > 0 else np.ones(self.n_topics) / self.n_topics

    def compare_resume_and_jd_topics(
        self,
        resume_text: str,
        jd_text: str
    ) -> Dict[str, Any]:
        """
        Compares the LDA topic distribution of a resume against a job description.
        Computes Jensen-Shannon divergence, Cosine topic similarity, and dominant themes.
        """
        theta_resume = self.infer_topic_distribution(resume_text)
        theta_jd = self.infer_topic_distribution(jd_text)

        # 1. Cosine similarity between topic distributions
        norm_r = np.linalg.norm(theta_resume)
        norm_j = np.linalg.norm(theta_jd)
        if norm_r > 0 and norm_j > 0:
            cosine_sim = float(np.dot(theta_resume, theta_jd) / (norm_r * norm_j))
        else:
            cosine_sim = 0.5
        cosine_sim = max(0.0, min(1.0, cosine_sim))

        # 2. Jensen-Shannon Divergence (bounded [0, 1] for base 2)
        js_div = float(jensenshannon(theta_resume, theta_jd, base=2))
        js_similarity = max(0.0, min(1.0, 1.0 - js_div))

        # Unified Topic Overlap Score (0-100)
        topic_match_score = round(((0.6 * cosine_sim) + (0.4 * js_similarity)) * 100, 1)

        # Dominant topics
        res_dominant_idx = int(np.argmax(theta_resume))
        jd_dominant_idx = int(np.argmax(theta_jd))

        topics_breakdown = []
        for i in range(self.n_topics):
            label = TOPIC_LABELS.get(i, f"Topic {i}")
            topics_breakdown.append({
                "topic_id": i,
                "label": label,
                "resume_weight": round(float(theta_resume[i]), 3),
                "vacancy_weight": round(float(theta_jd[i]), 3),
                "delta": round(float(abs(theta_resume[i] - theta_jd[i])), 3)
            })

        return {
            "topic_match_score": topic_match_score,
            "cosine_topic_similarity": round(cosine_sim, 3),
            "jensen_shannon_similarity": round(js_similarity, 3),
            "resume_dominant_topic": TOPIC_LABELS.get(res_dominant_idx, f"Topic {res_dominant_idx}"),
            "vacancy_dominant_topic": TOPIC_LABELS.get(jd_dominant_idx, f"Topic {jd_dominant_idx}"),
            "domain_congruence": "High" if topic_match_score >= 75 else ("Moderate" if topic_match_score >= 55 else "Low"),
            "topics_breakdown": topics_breakdown,
            "topic_keywords": self.get_topic_keywords(top_n=5)
        }


# Singleton engine instance
_lda_engine_instance: Optional[LDATopicEngine] = None


def get_lda_topic_engine() -> LDATopicEngine:
    global _lda_engine_instance
    if _lda_engine_instance is None:
        _lda_engine_instance = LDATopicEngine()
    return _lda_engine_instance


def analyze_lda_topics(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """Convenience helper to analyze LDA topics."""
    engine = get_lda_topic_engine()
    return engine.compare_resume_and_jd_topics(resume_text, jd_text)
