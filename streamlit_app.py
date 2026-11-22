import httpx
import ollama
import streamlit as st

from app import config, db
from app.rag import answer
from app.vectorstore import IndexNotReady

st.set_page_config(page_title="Operations Knowledge Assistant", layout="wide")
st.title("Operations Knowledge Assistant")
st.caption(
    "Risposte basate esclusivamente sui documenti indicizzati (documenti di esempio a contenuto fittizio)."
)

db.init_db()
with st.sidebar:
    st.header("Stato")
    counts = db.catalog_counts()
    st.metric("Documenti", counts["documents"])
    st.metric("Chunk", counts["chunks"])
    st.caption(f"Modello: {config.CHAT_MODEL}  \nEmbeddings: {config.EMBEDDING_MODEL}")
    top_k = st.slider("Passaggi da recuperare", 1, 6, 3)

question = st.text_input(
    "Fai una domanda sui documenti",
    placeholder="Chi può autorizzare lo sbarco dei passeggeri?",
)

if st.button("Chiedi", type="primary") and question.strip():
    with st.spinner("Cerco nei documenti..."):
        try:
            result = answer(question.strip(), k=top_k)
        except IndexNotReady:
            st.error("Indice non trovato: esegui prima `python -m scripts.index_documents`.")
        except (ConnectionError, httpx.HTTPError, ollama.ResponseError):
            st.error("Il modello linguistico (Ollama) non è raggiungibile. Controlla OLLAMA_BASE_URL.")
        else:
            st.subheader("Risposta")
            st.write(result["answer"])
            st.caption(f"Tempo di risposta: {result['latency_ms'] / 1000:.1f} s")
            if result["sources"]:
                st.subheader("Fonti")
                for i, s in enumerate(result["sources"], start=1):
                    with st.expander(f"[{i}] {s['source']}, pagina {s['page']} (distanza {s['distance']:.3f})"):
                        st.text(s["text"])
