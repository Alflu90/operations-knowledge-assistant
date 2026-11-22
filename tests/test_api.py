from fastapi.testclient import TestClient

from app import db, main, rag
from app.vectorstore import IndexNotReady

FAKE_HITS = [
    {"chunk_id": "a.pdf:1:0", "text": "Testo di prova", "source": "a.pdf", "page": 1, "distance": 0.3}
]


def fake_answer(question, k=3):
    return {"answer": "Risposta [1]", "answered": True, "latency_ms": 12, "sources": FAKE_HITS}


def test_ask_returns_answer_and_sources(monkeypatch):
    monkeypatch.setattr(main, "answer", fake_answer)
    with TestClient(main.app) as client:
        resp = client.post("/ask", json={"question": "  Chi decide lo sbarco?  "})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answered"] is True
    assert body["sources"][0]["page"] == 1


def test_ask_rejects_short_question():
    with TestClient(main.app) as client:
        assert client.post("/ask", json={"question": "ab"}).status_code == 422


def test_ask_without_index_returns_503(monkeypatch):
    def no_index(question, k=3):
        raise IndexNotReady("Indice non trovato")

    monkeypatch.setattr(main, "answer", no_index)
    with TestClient(main.app) as client:
        resp = client.post("/ask", json={"question": "Domanda di prova"})
    assert resp.status_code == 503


def test_ask_with_ollama_down_returns_503(monkeypatch):
    def ollama_down(question, k=3):
        raise ConnectionError("Ollama spento")

    monkeypatch.setattr(main, "answer", ollama_down)
    with TestClient(main.app) as client:
        resp = client.post("/ask", json={"question": "Domanda di prova"})
    assert resp.status_code == 503


def test_stats_after_logged_queries():
    with TestClient(main.app) as client:
        db.log_query("D1", "R1", True, 100, 0.3, FAKE_HITS)
        db.log_query("D2", "Nei documenti forniti non trovo questa informazione.", False, 200, 0.7, [])
        stats = client.get("/stats").json()
    summary = stats["riepilogo_domande"][0]
    assert summary["domande"] == 2
    assert summary["con_risposta"] == 1


def test_health(monkeypatch):
    class FakeClient:
        def __init__(self, host=None):
            pass

        def list(self):
            return {}

    monkeypatch.setattr(main.ollama, "Client", FakeClient)
    with TestClient(main.app) as client:
        body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["ollama"] is True
    assert body["chunks"] == 0


def test_answer_flags_not_found_and_logs(monkeypatch):
    class FakeClient:
        def __init__(self, host=None):
            pass

        def chat(self, **kwargs):
            return {"message": {"content": rag.NOT_FOUND}}

    monkeypatch.setattr(rag, "search", lambda question, k=3: FAKE_HITS)
    monkeypatch.setattr(rag.ollama, "Client", FakeClient)
    result = rag.answer("Quanto costa un biglietto?")
    assert result["answered"] is False
    with db.connect() as conn:
        row = conn.execute("SELECT answered, best_distance FROM query_log").fetchone()
    assert row["answered"] == 0
    assert row["best_distance"] == 0.3

def test_answer_skips_model_when_sources_too_far(monkeypatch):
    far_hits = [{**FAKE_HITS[0], "distance": 0.9}]

    class ExplodingClient:
        def __init__(self, host=None):
            raise AssertionError("il modello non deve essere chiamato")

    monkeypatch.setattr(rag, "search", lambda question, k=3: far_hits)
    monkeypatch.setattr(rag.ollama, "Client", ExplodingClient)
    result = rag.answer("Qual è la capitale della Francia?")
    assert result["answered"] is False
    assert result["answer"] == rag.NOT_FOUND
    assert result["sources"] == []

def test_answer_returns_sources_only_when_answered(monkeypatch):
    class FakeClient:
        def __init__(self, host=None):
            pass

        def chat(self, **kwargs):
            return {"message": {"content": "Risposta [1]"}}

    monkeypatch.setattr(rag, "search", lambda question, k=3: FAKE_HITS)
    monkeypatch.setattr(rag.ollama, "Client", FakeClient)
    result = rag.answer("Chi decide lo sbarco?")
    assert result["answered"] is True
    assert result["sources"] == FAKE_HITS
