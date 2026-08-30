"""
Individual Skill & Technical Claim Embedding Model.
Uses Sentence Transformers (all-MiniLM-L6-v2) for granular semantic matching
between individual skills/claims and reference texts or project evidence.
"""
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.models.embedding_model import embedding_model_instance

class SkillEmbeddingModel:
    def __init__(self):
        self.base_model = embedding_model_instance

    def compute_skill_similarity(self, skill_a: str, skill_b: str) -> float:
        """
        Compute cosine similarity between two skill terms or phrases (0.0 - 100.0).
        """
        if not skill_a or not skill_b:
            return 0.0
            
        if skill_a.strip().lower() == skill_b.strip().lower():
            return 100.0

        self.base_model._ensure_loaded()
        if self.base_model.model is not None:
            try:
                embeddings = self.base_model.model.encode([skill_a, skill_b])
                sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                return float(round(max(0.0, min(1.0, float(sim))) * 100, 2))
            except Exception as e:
                print(f"[SkillEmbedding Error]: {e}")

        # Fallback character n-gram similarity
        return self.base_model._fallback_similarity(skill_a, skill_b)

    def match_skills_semantic(
        self, 
        candidate_skills: List[str], 
        target_skills: List[str], 
        threshold: float = 65.0
    ) -> List[Dict[str, Any]]:
        """
        Match each target skill against candidate skills using Sentence-BERT cosine similarity.
        
        Returns a list of match records with highest similarity scores.
        """
        if not target_skills:
            return []

        results = []
        for target in target_skills:
            best_match = None
            best_score = 0.0

            # Check exact match first
            for cand in candidate_skills:
                if cand.lower() == target.lower():
                    best_match = cand
                    best_score = 100.0
                    break

            # If no exact match, compute semantic similarity against all candidate skills
            if best_score < 100.0 and candidate_skills:
                for cand in candidate_skills:
                    score = self.compute_skill_similarity(target, cand)
                    if score > best_score:
                        best_score = score
                        best_match = cand

            results.append({
                "target_skill": target,
                "matched_skill": best_match if best_score >= threshold else None,
                "similarity": best_score,
                "is_matched": best_score >= threshold,
                "match_type": "Exact" if best_score >= 99.0 else ("Semantic" if best_score >= threshold else "Missing")
            })

        return results

    def verify_claim_against_evidence(
        self,
        claim: str,
        evidence_snippets: List[str]
    ) -> Tuple[float, str]:
        """
        Compare a single technical claim against a list of project evidence sentences/tokens.
        Returns: (highest_similarity_score, best_matching_evidence_snippet)
        """
        if not claim or not evidence_snippets:
            return 0.0, ""

        best_score = 0.0
        best_snippet = ""

        # Direct token presence check
        claim_clean = claim.lower().strip()
        for snippet in evidence_snippets:
            snippet_clean = snippet.lower().strip()
            if claim_clean in snippet_clean or snippet_clean in claim_clean:
                return 100.0, snippet

        # Semantic Sentence-BERT embedding check
        self.base_model._ensure_loaded()
        if self.base_model.model is not None:
            try:
                claim_emb = self.base_model.model.encode([claim])[0]
                evidence_embs = self.base_model.model.encode(evidence_snippets)
                similarities = cosine_similarity([claim_emb], evidence_embs)[0]
                
                max_idx = int(np.argmax(similarities))
                best_score = float(round(max(0.0, min(1.0, float(similarities[max_idx]))) * 100, 2))
                best_snippet = evidence_snippets[max_idx]
                return best_score, best_snippet
            except Exception as e:
                print(f"[Claim Verification Error]: {e}")

        # Fallback comparison
        for snippet in evidence_snippets:
            score = self.base_model._fallback_similarity(claim, snippet)
            if score > best_score:
                best_score = score
                best_snippet = snippet

        return best_score, best_snippet

skill_embedding_model_instance = SkillEmbeddingModel()
