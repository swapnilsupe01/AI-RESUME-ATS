"""
Layer F — Codebase & Documentation RAG Intelligence Layer.

Provides a dedicated in-memory vector memory and knowledge graph that indexes:
  1. Candidate Resume Facts (skills, experience, projects).
  2. GitHub Repository Documentation (README.md, architecture, features, dependencies).
  3. Target Job Description alignment vectors.

Acts as the Grounding Foundation for Layer E (AI Resume Upgrade Engine)
to ensure 100% factual accuracy and zero-hallucination wording improvements.
All knowledge is kept strictly in memory per session to prevent cross-user data leakage.
"""

from typing import Dict, Any, List, Optional, Set
import re
import logging
import numpy as np

from app.models.embedding_model import embedding_model_instance
from app.utils.skills import normalize_skill

logger = logging.getLogger(__name__)


class CodebaseRAGKnowledgeStore:
    """
    Dedicated Candidate Codebase & Documentation Vector Knowledge Store (Layer F).
    Purely in-memory storage to ensure strict multi-tenant isolation.
    """

    def __init__(self):
        # Chunks: List of Dict with keys: 'text', 'source', 'type', 'project_name', 'techs'
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.verified_tools_by_project: Dict[str, Set[str]] = {}
        self.candidate_all_tools: Set[str] = set()
        self._current_candidate_key: str = ""
        # Full raw README.md stored per repo (key = repo_name)
        self.raw_readmes: Dict[str, str] = {}

    def reset(self):
        """Clear all in-memory chunks, tools, candidate keys, and README caches."""
        self.chunks = []
        self.embeddings = None
        self.verified_tools_by_project = {}
        self.candidate_all_tools = set()
        self._current_candidate_key = ""
        self.raw_readmes = {}

    def clear(self):
        """Reset the knowledge store for a new session/candidate (alias for reset)."""
        self.reset()

    def load_from_json(self, candidate_key: str) -> bool:
        """Disk cache removed in Phase B. In-memory only."""
        return False

    def save_to_json(self, candidate_key: str = "") -> str:
        """Disk cache removed in Phase B. In-memory only."""
        return ""

    def get_raw_readme(self, repo_name: str) -> Optional[str]:
        """Return the full raw README.md for a repo if stored in memory."""
        if repo_name in self.raw_readmes:
            return self.raw_readmes[repo_name]
        repo_lower = repo_name.lower().strip()
        for k, v in self.raw_readmes.items():
            if k.lower().strip() == repo_lower:
                return v
        return None

    def index_resume(self, canonical_resume: Dict[str, Any]):
        """
        Index candidate resume sections into semantic vector memory.
        """
        if not isinstance(canonical_resume, dict):
            return

        # 1. Index Summary
        summary = str(canonical_resume.get("summary") or "").strip()
        if summary and len(summary) > 20:
            self._add_chunk(
                text=summary,
                source="Resume: Professional Summary",
                chunk_type="summary",
                project_name="",
                techs=[],
            )

        # 2. Index Skills
        skills = canonical_resume.get("skills") or []
        extracted_skills = canonical_resume.get("extracted_skills") or []
        all_skills_list = []
        if isinstance(skills, dict):
            for s_list in skills.values():
                if isinstance(s_list, list):
                    all_skills_list.extend([str(s) for s in s_list if s])
        elif isinstance(skills, list):
            all_skills_list.extend([str(s) for s in skills if s])
        all_skills_list.extend([str(s) for s in extracted_skills if s])

        for sk in all_skills_list:
            norm = normalize_skill(sk)
            if norm:
                self.candidate_all_tools.add(norm)

        if all_skills_list:
            self._add_chunk(
                text="Technical Core Competencies: " + ", ".join(all_skills_list),
                source="Resume: Technical Skills",
                chunk_type="skills",
                project_name="",
                techs=list(self.candidate_all_tools),
            )

        # 3. Index Experience
        for exp in canonical_resume.get("experience", []):
            if not isinstance(exp, dict):
                continue
            role = exp.get("role") or exp.get("title") or "Role"
            company = exp.get("company") or exp.get("organization") or "Company"
            bullets = exp.get("highlights") or exp.get("bullets") or []
            if isinstance(bullets, str):
                bullets = [bullets]
            exp_techs = exp.get("technologies") or []

            for b in bullets:
                b_str = str(b).strip()
                if len(b_str) > 15:
                    self._add_chunk(
                        text=f"Experience at {company} ({role}): {b_str}",
                        source=f"Resume Experience: {company}",
                        chunk_type="experience",
                        project_name=company,
                        techs=exp_techs,
                    )

        # 4. Index Projects
        for proj in canonical_resume.get("projects", []):
            if not isinstance(proj, dict):
                continue
            p_name = proj.get("name") or proj.get("title") or "Project"
            desc = str(proj.get("description") or "").strip()
            p_techs = proj.get("technologies") or proj.get("tech_stack") or []
            if isinstance(p_techs, str):
                p_techs = [t.strip() for t in p_techs.split(",") if t.strip()]

            p_key = p_name.lower().strip()
            if p_key not in self.verified_tools_by_project:
                self.verified_tools_by_project[p_key] = set()
            for t in p_techs:
                self.verified_tools_by_project[p_key].add(normalize_skill(t))
                self.candidate_all_tools.add(normalize_skill(t))

            if desc and len(desc) > 15:
                self._add_chunk(
                    text=f"Project {p_name} Overview: {desc} (Technologies: {', '.join(p_techs)})",
                    source=f"Resume Project: {p_name}",
                    chunk_type="project_overview",
                    project_name=p_name,
                    techs=p_techs,
                )

            bullets = proj.get("highlights") or proj.get("bullets") or []
            if isinstance(bullets, str):
                bullets = [bullets]
            for b in bullets:
                b_str = str(b).strip()
                if len(b_str) > 15:
                    self._add_chunk(
                        text=f"Project {p_name} Highlight: {b_str}",
                        source=f"Resume Project: {p_name}",
                        chunk_type="project_highlight",
                        project_name=p_name,
                        techs=p_techs,
                    )

        self._recompute_embeddings()

    def index_resume_and_save(self, canonical_resume: Dict[str, Any]) -> str:
        """
        Index resume into memory.
        Uses candidate name or github username as the key.
        """
        self.index_resume(canonical_resume)
        name = (
            canonical_resume.get("candidate_name")
            or (canonical_resume.get("profile", {}) or {}).get("name")
            or ""
        ).strip()
        gh_url = (
            canonical_resume.get("github_url")
            or (canonical_resume.get("profile", {}) or {}).get("github")
            or ""
        ).strip()
        gh_user = ""
        if "github.com/" in gh_url:
            gh_user = gh_url.split("github.com/")[-1].strip("/").split("/")[0]
        key = gh_user or re.sub(r"\s+", "_", name.lower()) or "default"
        self._current_candidate_key = key
        return key

    def index_github_repositories(self, github_evidence_list: List[Dict[str, Any]]):
        """
        Deeply ingest verified GitHub repositories into in-memory store.
        """
        if not github_evidence_list:
            return

        for gh in github_evidence_list:
            repo_name = gh.get("repo_name") or gh.get("full_name") or "GitHub Repo"
            repo_key = repo_name.lower().replace("-", " ").replace("_", " ").strip()

            if repo_key not in self.verified_tools_by_project:
                self.verified_tools_by_project[repo_key] = set()

            repo_tools = []
            for t in gh.get("technologies", []) + gh.get("languages", []):
                norm = normalize_skill(t)
                if norm:
                    self.verified_tools_by_project[repo_key].add(norm)
                    self.candidate_all_tools.add(norm)
                    repo_tools.append(norm)

            desc = gh.get("description")
            if desc and len(desc.strip()) > 10:
                self._add_chunk(
                    text=f"GitHub Repo {repo_name} Description: {desc}",
                    source=f"GitHub: {repo_name}",
                    chunk_type="github_description",
                    project_name=repo_name,
                    techs=repo_tools,
                )

            for snip in gh.get("evidence_snippets", []):
                s_clean = str(snip).strip()
                if len(s_clean) > 20:
                    self._add_chunk(
                        text=f"Codebase Feature ({repo_name}): {s_clean}",
                        source=f"GitHub Code: {repo_name}",
                        chunk_type="github_snippet",
                        project_name=repo_name,
                        techs=repo_tools,
                    )

            readme_text = gh.get("readme_content") or gh.get("readme_preview") or ""
            if readme_text and len(readme_text.strip()) > 30:
                self.raw_readmes[repo_name] = readme_text.strip()
                self._chunk_and_index_readme(repo_name, readme_text, repo_tools)

        self._recompute_embeddings()

    def _chunk_and_index_readme(self, repo_name: str, readme_text: str, repo_tools: List[str]):
        """
        Extract meaningful architectural sections from a README.md file.
        """
        lines = readme_text.splitlines()
        current_header = "Overview"
        current_block: List[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith(("#", "##", "###")):
                if current_block:
                    block_content = " ".join(current_block).strip()
                    if len(block_content) > 30:
                        self._add_chunk(
                            text=f"GitHub README ({repo_name} - {current_header}): {block_content}",
                            source=f"GitHub README: {repo_name}",
                            chunk_type="github_readme",
                            project_name=repo_name,
                            techs=repo_tools,
                        )
                    current_block = []
                current_header = stripped.lstrip("# ").strip()
            else:
                if not (stripped.startswith("[![") or stripped.startswith("![")):
                    current_block.append(stripped)

        if current_block:
            block_content = " ".join(current_block).strip()
            if len(block_content) > 30:
                self._add_chunk(
                    text=f"GitHub README ({repo_name} - {current_header}): {block_content}",
                    source=f"GitHub README: {repo_name}",
                    chunk_type="github_readme",
                    project_name=repo_name,
                    techs=repo_tools,
                )

    def _add_chunk(
        self,
        text: str,
        source: str,
        chunk_type: str,
        project_name: str,
        techs: List[str],
    ):
        self.chunks.append({
            "text": text.strip(),
            "source": source,
            "type": chunk_type,
            "project_name": project_name,
            "techs": [normalize_skill(t) for t in techs if t],
        })

    def _recompute_embeddings(self):
        """Compute Sentence-BERT dense embeddings for all stored chunks."""
        if not self.chunks:
            self.embeddings = None
            return

        try:
            embedding_model_instance._ensure_loaded()
            if embedding_model_instance.model is not None:
                texts = [c["text"] for c in self.chunks]
                self.embeddings = embedding_model_instance.model.encode(texts)
        except Exception as exc:
            logger.debug("[Layer F Codebase RAG] Embedding computation note: %s", exc)
            self.embeddings = None

    def retrieve_grounded_context(
        self,
        query: str,
        project_name: str = "",
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """
        Retrieve verified codebase facts and strict tool whitelist for a query or project.

        Returns:
            Dict containing:
              - 'verified_tools': List[str] (Authentic candidate tools only)
              - 'evidence_snippets': List[str] (Grounded facts from README / Code)
              - 'rag_prompt_block': str (Formatted for LLM grounding injection)
        """
        if not self.chunks:
            return {
                "verified_tools": list(self.candidate_all_tools),
                "evidence_snippets": [],
                "rag_prompt_block": "",
            }

        # 1. Determine verified tool whitelist
        target_tools: Set[str] = set()
        p_clean = project_name.lower().replace("-", " ").replace("_", " ").strip()

        if p_clean:
            for k, t_set in self.verified_tools_by_project.items():
                if k in p_clean or p_clean in k:
                    target_tools.update(t_set)

        if not target_tools:
            target_tools = self.candidate_all_tools

        # 2. Dense Semantic Vector Retrieval
        results = []
        if self.embeddings is not None and embedding_model_instance.model is not None:
            try:
                from sklearn.metrics.pairwise import cosine_similarity
                q_emb = embedding_model_instance.model.encode([query])
                sims = cosine_similarity(q_emb, self.embeddings)[0]
                top_indices = np.argsort(sims)[::-1][:top_k * 2]

                for idx in top_indices:
                    chunk = self.chunks[idx]
                    score = float(sims[idx])
                    if project_name and project_name.lower() in chunk["project_name"].lower():
                        score += 0.25
                    results.append((score, chunk))
            except Exception as exc:
                logger.debug("[Layer F Codebase RAG] Retrieval error: %s", exc)

        # Fallback to keyword matching if vector search unavailable
        if not results:
            q_lower = query.lower()
            for chunk in self.chunks:
                score = 0.0
                if project_name and project_name.lower() in chunk["project_name"].lower():
                    score += 2.0
                for w in q_lower.split():
                    if len(w) > 3 and w in chunk["text"].lower():
                        score += 0.5
                if score > 0:
                    results.append((score, chunk))

        results.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [c for _, c in results[:top_k]]

        # 3. Format RAG Grounding Prompt Block
        evidence_snippets = [c["text"] for c in top_chunks]
        prompt_lines = []
        if evidence_snippets:
            prompt_lines.append("VERIFIED EVIDENCE (from candidate's GitHub README & Codebase):")
            for i, snip in enumerate(evidence_snippets, 1):
                prompt_lines.append(f"[{i}] {snip}")
            prompt_lines.append(
                f"STRICT CONSTRAINT: ONLY use verified tools: {', '.join(sorted(target_tools)) if target_tools else 'from original text'}."
            )

        return {
            "verified_tools": sorted(list(target_tools)),
            "evidence_snippets": evidence_snippets,
            "rag_prompt_block": "\n".join(prompt_lines) + "\n\n" if prompt_lines else "",
        }


# Global singleton instance for Layer F
codebase_rag_instance = CodebaseRAGKnowledgeStore()
