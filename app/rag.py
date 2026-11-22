"""Domanda -> recupero dei chunk -> risposta del modello con riferimenti alle fonti."""
import time

import ollama

from app import config
from app.db import init_db, log_query
from app.vectorstore import search

NOT_FOUND = "Nei documenti forniti non trovo questa informazione."

SYSTEM_PROMPT = f"""Sei un assistente per il personale operativo di una compagnia aerea. \
Rispondi in italiano usando SOLO le informazioni contenute nei passaggi forniti.
- Dopo ogni affermazione indica la fonte con il numero del passaggio tra parentesi quadre, ad esempio [1] o [2].
- Se i passaggi non contengono la risposta, rispondi esattamente: "{NOT_FOUND}"
- Non aggiungere informazioni che non sono presenti nei passaggi."""


def build_context(hits: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] (fonte: {h['source']}, pagina {h['page']})\n{h['text']}" for i, h in enumerate(hits, start=1)
    )


def answer(question: str, k: int = 3) -> dict:
    start = time.perf_counter()
    hits = search(question, k=k)

    if not hits or hits[0]["distance"] > config.MAX_DISTANCE:
        # Nessun passaggio abbastanza vicino alla domanda: non interpelliamo il modello
        text = NOT_FOUND
    else:
        client = ollama.Client(host=config.OLLAMA_BASE_URL)
        response = client.chat(
            model=config.CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Passaggi:\n{build_context(hits)}\n\nDomanda: {question}"},
            ],
            options={"temperature": 0},
        )
        text = response["message"]["content"].strip()

    latency_ms = int((time.perf_counter() - start) * 1000)
    answered = NOT_FOUND.lower() not in text.lower()

    init_db()
    log_query(question, text, answered, latency_ms, hits[0]["distance"] if hits else None, hits)
    return {
        "answer": text,
        "answered": answered,
        "latency_ms": latency_ms,
        "sources": hits if answered else [],  # le fonti si mostrano solo se c'è una risposta
        "retrieved": hits,                    # per debug; l'API non lo espone
    }
