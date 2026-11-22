from contextlib import asynccontextmanager

import httpx
import ollama
from fastapi import FastAPI, HTTPException, status

from app import config, db, schemas
from app.rag import answer
from app.vectorstore import IndexNotReady


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Operations Knowledge Assistant", version="0.1.0", lifespan=lifespan)


@app.post("/ask", response_model=schemas.AskResponse)
def ask(request: schemas.AskRequest):
    try:
        return answer(request.question, k=request.top_k)
    except IndexNotReady as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except (ConnectionError, httpx.HTTPError, ollama.ResponseError):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Il modello linguistico (Ollama) non è raggiungibile",
        )


@app.get("/stats")
def stats():
    return db.run_analytics()


@app.get("/health")
def health():
    try:
        ollama.Client(host=config.OLLAMA_BASE_URL).list()
        ollama_ok = True
    except Exception:
        ollama_ok = False
    try:
        counts = db.catalog_counts()
    except Exception:
        counts = {"documents": None, "chunks": None}
    return {"status": "ok" if ollama_ok else "degraded", "ollama": ollama_ok, **counts}
