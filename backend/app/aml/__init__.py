"""
AML (Applied Machine Learning) & Research Intelligence Package.
Integrates:
  - ESCO Hierarchical Skill Taxonomy (Paper 5: CareerBERT 2025)
  - Latent Dirichlet Allocation (LDA) Topic Modeler (Paper 4: Bian et al. CIKM 2020 & CO6)
  - Supervised Candidate Fit Classifier (SVM & Gradient Boosting / XGBoost) (Paper 2 & CO2)
  - SHAP Explainable AI Attribution Engine (Problem Statement & CO6)
  - Advanced Recruitment Evaluation Metrics (ROC-AUC, PR Curves, F-beta) (Paper 3 & CO3)
"""
from app.aml.taxonomy_esco import (
    canonicalize_skill,
    map_skills_to_esco_taxonomy,
    compare_esco_taxonomy_alignment,
    ESCO_HIERARCHY
)
from app.aml.lda_topic_model import (
    analyze_lda_topics,
    get_lda_topic_engine,
    LDATopicEngine
)
from app.aml.classifier import (
    classify_candidate,
    get_candidate_classifier,
    CandidateFitClassifier
)
from app.aml.shap_explainer import (
    calculate_shap_attributions
)
from app.aml.evaluation import (
    evaluate_classifier_metrics,
    run_model_benchmark_comparison
)

__all__ = [
    "canonicalize_skill",
    "map_skills_to_esco_taxonomy",
    "compare_esco_taxonomy_alignment",
    "ESCO_HIERARCHY",
    "analyze_lda_topics",
    "get_lda_topic_engine",
    "LDATopicEngine",
    "classify_candidate",
    "get_candidate_classifier",
    "CandidateFitClassifier",
    "calculate_shap_attributions",
    "evaluate_classifier_metrics",
    "run_model_benchmark_comparison"
]
