from typing import List, Dict, Any, Optional
import os
import uuid
import math

try:
    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams, Batch, PointStruct
except Exception:
    SentenceTransformer = None
    QdrantClient = None
    Distance = None
    VectorParams = None
    Batch = None
    PointStruct = None

# Initialize embedding model (global)
_EMBED_MODEL = None
_QDRANT = None


def get_embed_model():
    global _EMBED_MODEL
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers is not installed")
    if _EMBED_MODEL is None:
        model_name = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        _EMBED_MODEL = SentenceTransformer(model_name)
    return _EMBED_MODEL


def get_qdrant_client():
    global _QDRANT
    if QdrantClient is None:
        raise RuntimeError("qdrant-client is not installed")
    if _QDRANT is None:
        url = os.environ.get("QDRANT_URL")
        api_key = os.environ.get("QDRANT_API_KEY")
        if not url:
            raise RuntimeError("QDRANT_URL not configured")
        _QDRANT = QdrantClient(url=url, api_key=api_key)
    return _QDRANT


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    # naive chunk by characters/words
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def index_resume(resume_id: str, text: str, metadata: Optional[Dict[str, Any]] = None):
    if SentenceTransformer is None or QdrantClient is None:
        return
    model = get_embed_model()
    qclient = get_qdrant_client()

    collection_name = "resumes"
    # ensure collection exists
    dim = model.get_sentence_embedding_dimension()
    try:
        qclient.recreate_collection(collection_name, vectors_config=VectorParams(size=dim, distance=Distance.COSINE))
    except Exception:
        # if recreate fails, try to create if not exists
        try:
            qclient.recreate_collection(collection_name, vectors_config=VectorParams(size=dim, distance=Distance.COSINE))
        except Exception:
            pass

    chunks = chunk_text(text)
    embeddings = model.encode(chunks, show_progress_bar=False, convert_to_numpy=True)

    points: List[PointStruct] = []
    for idx, emb in enumerate(embeddings):
        pid = f"{resume_id}__{idx}"
        payload = {"resume_id": resume_id, "chunk_index": idx, "text": chunks[idx]}
        points.append(PointStruct(id=pid, vector=emb.tolist(), payload=payload))

    # upsert in batches
    batch_size = 64
    for i in range(0, len(points), batch_size):
        qclient.upsert(collection_name=collection_name, points=points[i : i + batch_size])


def retrieve(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    if SentenceTransformer is None or QdrantClient is None:
        return []
    model = get_embed_model()
    qclient = get_qdrant_client()
    emb = model.encode([query], show_progress_bar=False)
    collection_name = "resumes"
    hits = qclient.search(collection_name=collection_name, query_vector=emb[0].tolist(), limit=top_k)
    results = []
    for h in hits:
        payload = h.payload or {}
        results.append({"id": h.id, "score": h.score, "text": payload.get("text"), "metadata": payload})
    return results
