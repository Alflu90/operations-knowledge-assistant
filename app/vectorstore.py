"""Embeddings (via Ollama) e archivio vettoriale (ChromaDB)."""
import chromadb
import ollama

from app import config
from app.chunking import Chunk


def _ollama() -> ollama.Client:
    return ollama.Client(host=config.OLLAMA_BASE_URL)


def embed(texts: list[str]) -> list[list[float]]:
    return _ollama().embed(model=config.EMBEDDING_MODEL, input=texts)["embeddings"]


def _client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=str(config.CHROMA_DIR))


def rebuild_index(chunks: list[Chunk]) -> int:
    """Ricostruisce da zero la collezione con i chunk dati."""
    client = _client()
    try:
        client.delete_collection(config.COLLECTION_NAME)
    except Exception:
        pass  # la collezione non esisteva ancora
    collection = client.create_collection(config.COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    if not chunks:
        return 0
    collection.add(
        ids=[f"{c.source}:{c.page}:{c.index}" for c in chunks],
        documents=[c.text for c in chunks],
        embeddings=embed([c.text for c in chunks]),
        metadatas=[{"source": c.source, "page": c.page, "chunk_index": c.index} for c in chunks],
    )
    return len(chunks)


class IndexNotReady(RuntimeError):
    """La collezione vettoriale non esiste: i documenti non sono stati indicizzati."""


def search(question: str, k: int = 3) -> list[dict]:
    try:
        collection = _client().get_collection(config.COLLECTION_NAME)
    except Exception as exc:  # il tipo di errore varia tra le versioni di chromadb
        raise IndexNotReady("Indice non trovato: esegui prima scripts.index_documents") from exc
    result = collection.query(query_embeddings=embed([question]), n_results=k)
    hits = []
    for chunk_id, text, meta, distance in zip(
        result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        hits.append(
            {"chunk_id": chunk_id, "text": text, "source": meta["source"], "page": meta["page"], "distance": distance}
        )
    return hits
