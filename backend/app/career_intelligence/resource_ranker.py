from difflib import SequenceMatcher
from typing import List
from .schemas import Resource, ResourceQuery

def similarity(a, b):
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def rank_resources(resources: List[Resource], query: ResourceQuery) -> List[dict]:
    results, seen = [], []
    for r in resources:
        if similarity(r.skill, query.skill) < 0.45: continue
        if query.language != "Both" and r.language not in (query.language, "Both"): continue
        if query.level != "all" and r.difficulty not in (query.level, "all"): continue
        title = r.title.lower().strip()
        if any(similarity(title, old) >= 0.90 for old in seen): continue
        seen.append(title)
        score = (
            0.30 * similarity(r.skill, query.skill) + 0.20 * r.authority_score
            + 0.15 * (1.0 if query.language == "Both" or r.language == query.language else 0.6)
            + 0.10 * (1.0 if query.level == "all" or r.difficulty == query.level else 0.5)
            + 0.10 * (1.0 if r.hands_on else 0.5) + 0.10 * r.freshness_score
            + 0.05 * r.popularity_score
        )
        results.append({"resource": r.model_dump(), "ranking_score": round(score, 3),
                        "caveat": "Heuristic ranking; verify link and resource quality. Popularity is not proof of quality."})
    return sorted(results, key=lambda x: x["ranking_score"], reverse=True)[:query.limit]
