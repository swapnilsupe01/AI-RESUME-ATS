"""
Semantic Matcher module.
Computes deep sentence and whole-document semantic similarity using Sentence-BERT embeddings.
"""
from typing import Dict, Any
from app.models.embedding_model import embedding_model_instance

def compute_semantic_alignment(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """
    Compute dense Sentence-BERT cosine similarity between resume and job description.
    """
    similarity = embedding_model_instance.compute_similarity(resume_text, jd_text)
    
    if similarity >= 80.0:
        alignment_level = "High Alignment"
    elif similarity >= 65.0:
        alignment_level = "Moderate Alignment"
    else:
        alignment_level = "Low Alignment"

    return {
        "semantic_score": similarity,
        "alignment_level": alignment_level
    }
