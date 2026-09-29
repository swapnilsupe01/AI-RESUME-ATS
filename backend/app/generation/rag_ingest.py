# backend/app/generation/rag_ingest.py

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[2]
GUIDANCE_DIR = ROOT / "data" / "resume_guidance"
DB_DIR = ROOT / "data" / "vector_store"

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=str(DB_DIR))
collection = client.get_or_create_collection(
    name="resume_guidance",
    metadata={"hnsw:space": "cosine"},
)

def split_text(text: str, chunk_size: int = 700, overlap: int = 100):
    """Basic character chunking for an initial prototype."""
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks

def ingest_guidance():
    ids, documents, metadatas = [], [], []

    for path in GUIDANCE_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")

        for index, chunk in enumerate(split_text(text)):
            ids.append(f"{path.stem}-{index}")
            documents.append(chunk)
            metadatas.append({
                "source": path.name,
                "chunk_index": index,
                "kind": "guidance",
            })

    if not documents:
        return

    vectors = embedding_model.encode(
        documents,
        normalize_embeddings=True,
    ).tolist()

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=vectors,
    )

if __name__ == "__main__":
    ingest_guidance()
    print("Guidance indexing complete.")