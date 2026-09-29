# backend/app/generation/rag_retriever.py

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[2]
DB_DIR = ROOT / "data" / "vector_store"

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path=str(DB_DIR))

guidance_collection = client.get_or_create_collection(
    name="resume_guidance",
    metadata={"hnsw:space": "cosine"},
)

def retrieve_guidance(query: str, top_k: int = 4) -> list[dict]:
    query_vector = embedding_model.encode(
        [query],
        normalize_embeddings=True,
    ).tolist()[0]

    result = guidance_collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
    )

    retrieved = []
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]

    for document, metadata in zip(docs, metas):
        retrieved.append({
            "text": document,
            "source": metadata.get("source", "unknown"),
        })

    return retrieved