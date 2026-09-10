"""
Supervised Candidate Fit Classifier (SVM & Gradient Boosting / XGBoost Ensemble).
Academic Foundation:
  - Paper 2: conSultantBERT: Fine-tuned Siamese Sentence-BERT for Matching Jobs and Job Seekers
    (Lavi, Medentsiy, Graus; arXiv 2021).
  - AML Course Outcome CO2: Classification Models (SVM with Kernel Functions, Ensemble Methods:
    Gradient Boosting / XGBoost).

Provides:
  1. Feature Vector Construction from Multi-Layer ATS Signals.
  2. Dual-Model Evaluation: Support Vector Classifier (SVC with RBF kernel) and
     Gradient Boosting Ensemble (scikit-learn / XGBoost-compatible).
  3. Calibrated Shortlist/Reject Probabilities and Decision Verdicts.
"""
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from sklearn.svm import SVC
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

FEATURE_NAMES = [
    "sbert_semantic_similarity",
    "skill_match_ratio",
    "exact_skill_matches",
    "lda_topic_congruence",
    "public_evidence_score",
    "years_of_experience"
]

# Baseline training calibration dataset representing diverse applicant profiles
# Format: [sbert (0-100), skill_ratio (0-1), exact_matches, lda (0-100), evidence (0-100), exp_yrs] -> Label (1=Shortlist, 0=Reject)
_BOOTSTRAP_TRAIN_X = np.array([
    # High fit candidates (Label 1)
    [88.0, 0.90, 8, 85.0, 92.0, 4.0],
    [82.0, 0.85, 6, 80.0, 88.0, 3.5],
    [92.0, 0.95, 9, 90.0, 95.0, 5.0],
    [78.0, 0.80, 5, 75.0, 80.0, 3.0],
    [85.0, 0.82, 7, 82.0, 85.0, 4.5],
    [90.0, 0.88, 8, 86.0, 90.0, 6.0],
    [75.0, 0.78, 5, 78.0, 75.0, 2.5],
    [80.0, 0.84, 6, 81.0, 82.0, 3.0],

    # Borderline candidates (Mixed labels)
    [65.0, 0.60, 4, 65.0, 60.0, 2.0],  # 1
    [68.0, 0.65, 4, 70.0, 65.0, 2.5],  # 1
    [58.0, 0.50, 3, 60.0, 50.0, 1.5],  # 0
    [62.0, 0.55, 3, 58.0, 55.0, 2.0],  # 0

    # Low fit / Discrepant candidates (Label 0)
    [40.0, 0.30, 2, 45.0, 30.0, 1.0],
    [35.0, 0.25, 1, 40.0, 20.0, 0.5],
    [48.0, 0.35, 2, 50.0, 40.0, 1.0],
    [25.0, 0.15, 1, 30.0, 15.0, 0.0],
    [30.0, 0.20, 1, 35.0, 25.0, 1.0],
    [45.0, 0.40, 2, 42.0, 35.0, 1.5],
    [20.0, 0.10, 0, 25.0, 10.0, 0.0],
    [50.0, 0.38, 2, 48.0, 42.0, 1.0]
])

_BOOTSTRAP_TRAIN_Y = np.array([
    1, 1, 1, 1, 1, 1, 1, 1,  # Strong
    1, 1, 0, 0,              # Borderline
    0, 0, 0, 0, 0, 0, 0, 0   # Weak
])


class CandidateFitClassifier:
    """
    Supervised Machine Learning Classifier evaluating candidate hiring fit.
    Combines SVM (RBF Kernel) and Gradient Boosting Ensemble.
    """

    def __init__(self):
        # SVM with RBF Kernel and probability output
        self.svm_pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('svm', SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, random_state=42))
        ])

        # Gradient Boosting / XGBoost equivalent
        self.gb_pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('gb', GradientBoostingClassifier(
                n_estimators=40,
                learning_rate=0.1,
                max_depth=3,
                random_state=42
            ))
        ])

        self._fit_models()

    def _fit_models(self):
        """Train models on the bootstrap training dataset."""
        self.svm_pipeline.fit(_BOOTSTRAP_TRAIN_X, _BOOTSTRAP_TRAIN_Y)
        self.gb_pipeline.fit(_BOOTSTRAP_TRAIN_X, _BOOTSTRAP_TRAIN_Y)

    @staticmethod
    def build_feature_vector(
        sbert_score: float,
        matched_skills_count: int,
        total_required_skills: int,
        exact_matches_count: int,
        lda_topic_score: float,
        evidence_score: float,
        experience_years: Optional[int] = None
    ) -> np.ndarray:
        """Constructs the normalized 6-dimensional feature vector."""
        skill_ratio = matched_skills_count / max(1, total_required_skills)
        exp_yrs = float(experience_years if experience_years is not None else 2.0)

        vec = np.array([
            float(sbert_score),
            float(skill_ratio),
            float(exact_matches_count),
            float(lda_topic_score),
            float(evidence_score),
            float(exp_yrs)
        ]).reshape(1, -1)
        return vec

    def predict_candidate_fit(self, feature_vector: np.ndarray) -> Dict[str, Any]:
        """
        Executes inference using both SVM and Gradient Boosting models.
        Returns unified prediction probabilities and recommendation verdict.
        """
        # SVM Inference
        svm_proba = float(self.svm_pipeline.predict_proba(feature_vector)[0][1])

        # Gradient Boosting Inference
        gb_proba = float(self.gb_pipeline.predict_proba(feature_vector)[0][1])

        # Ensemble weighted probability
        ensemble_proba = round((0.45 * svm_proba) + (0.55 * gb_proba), 3)

        if ensemble_proba >= 0.70:
            verdict = "Shortlisted"
            action_code = "INTERVIEW_RECOMMENDED"
            confidence = "High"
        elif ensemble_proba >= 0.45:
            verdict = "Review Required"
            action_code = "MANUAL_RECRUITER_AUDIT"
            confidence = "Medium"
        else:
            verdict = "Rejected"
            action_code = "UNFIT_CRITERIA"
            confidence = "High"

        # Feature vector dictionary for interpretability
        raw_vals = feature_vector[0].tolist()
        features_dict = {
            FEATURE_NAMES[i]: round(raw_vals[i], 2)
            for i in range(len(FEATURE_NAMES))
        }

        return {
            "verdict": verdict,
            "action_code": action_code,
            "shortlist_probability": ensemble_proba,
            "svm_probability": round(svm_proba, 3),
            "gradient_boosting_probability": round(gb_proba, 3),
            "confidence_band": confidence,
            "model_features": features_dict
        }


# Singleton classifier instance
_classifier_instance: Optional[CandidateFitClassifier] = None


def get_candidate_classifier() -> CandidateFitClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = CandidateFitClassifier()
    return _classifier_instance


def classify_candidate(
    sbert_score: float,
    matched_skills_count: int,
    total_required_skills: int,
    exact_matches_count: int,
    lda_topic_score: float,
    evidence_score: float,
    experience_years: Optional[int] = None
) -> Dict[str, Any]:
    """Convenience helper to classify candidate."""
    clf = get_candidate_classifier()
    feat_vec = clf.build_feature_vector(
        sbert_score,
        matched_skills_count,
        total_required_skills,
        exact_matches_count,
        lda_topic_score,
        evidence_score,
        experience_years
    )
    return clf.predict_candidate_fit(feat_vec)
