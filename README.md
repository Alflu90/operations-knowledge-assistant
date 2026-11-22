# Operations Knowledge Assistant

Assistente RAG (Retrieval-Augmented Generation) che risponde a domande sulle procedure operative di una compagnia aerea **citando i documenti e la pagina da cui prende le informazioni**. Funziona interamente in locale, senza API a pagamento: embeddings e modello linguistico girano su Ollama.

> I documenti inclusi (`data/pdfs/`) sono **di esempio a contenuto fittizio**, generati da `scripts/make_sample_pdfs.py`. Non rappresentano le procedure di alcuna compagnia reale.

## Come funziona

1. **Lettura PDF** con PyMuPDF, pagina per pagina.
2. **Chunking**: il testo è diviso per paragrafi in segmenti di circa 800 caratteri. Un chunk non attraversa mai due pagine, e ogni chunk che inizia a metà sezione riceve davanti il titolo della sezione, così è comprensibile da solo.
3. **Embeddings** con `bge-m3` (multilingue) tramite Ollama.
4. **Archivio vettoriale**: ChromaDB, con distanza coseno.
5. **Recupero** dei passaggi più vicini alla domanda (default 3).
6. **Generazione** con `gemma3:12b`, istruito a rispondere solo con i passaggi forniti e a indicare la fonte con `[1]`, `[2]`.
7. **Fonti**: l'elenco finale (file e pagina) è costruito dal codice a partire dai passaggi recuperati, non dal modello, quindi i riferimenti sono reali. Comprende tutti i passaggi forniti al modello, non solo quelli citati nel testo della risposta, e viene mostrato solo quando il sistema ha effettivamente risposto.
8. **Filtro di sicurezza**: se il passaggio più vicino ha distanza superiore a `MAX_DISTANCE` (0,5), il modello non viene nemmeno interpellato e la risposta è "Nei documenti forniti non trovo questa informazione."

## Livello SQL

Oltre a ChromaDB, un database SQLite (`rag.db`) contiene il livello relazionale (`sql/schema.sql`):

| Tabella | Contenuto |
|---|---|
| `documents` | file indicizzati e numero di pagine |
| `chunks` | testo, pagina e lunghezza di ogni chunk (stesso id usato in ChromaDB) |
| `query_log` | ogni domanda, risposta, esito, tempo di risposta e distanza migliore |
| `query_sources` | i chunk recuperati per ogni domanda, con posizione e distanza |

Le query di analisi sono in `sql/analytics.sql` (riepilogo domande, documenti più recuperati, chunk mai recuperati, distanza per esito, domande senza risposta) e si eseguono con `python -m scripts.analytics`. Lo storico delle domande non viene cancellato quando si reindicizzano i documenti.

## Valutazione

`python -m scripts.evaluate` misura il recupero su 14 domande con risposta nei documenti (per ognuna è indicata una frase che deve comparire nel chunk giusto) e 4 domande fuori argomento. Non usa il modello linguistico.

| Metrica | Risultato |
|---|---|
| Chunk giusto al primo posto | 11/14 (79%) |
| Chunk giusto entro i primi 3 | 14/14 (100%) |
| Chunk giusto entro i primi 5 | 14/14 (100%) |
| Distanza del primo risultato, domande con risposta | da 0,219 a 0,427 |
| Distanza del primo risultato, fuori argomento | da 0,375 a 0,741 |

**Cosa ne ricavo**
- Con 3 passaggi recuperati il chunk giusto è sempre presente.
- La distanza da sola **non** separa tutti i casi: la domanda "Dopo quanto ritardo si può ottenere un rimborso?" (vicina al tema ma assente dai documenti) ha distanza 0,375, dentro l'intervallo delle domande valide. In quel caso il rifiuto dipende dal prompt di sistema, non dalla soglia.
- Le altre tre domande fuori argomento hanno distanza 0,547 o più, sopra ogni domanda valida: la soglia di 0,5 le intercetta prima del modello.

## Limiti

- Documenti e domande di valutazione sono scritti dallo stesso autore e con lo stesso lessico: le percentuali sono una stima ottimistica. Il corpus è di soli 2 documenti e 8 chunk, e la soglia è calibrata su 18 domande, quindi con più documenti va ricalcolata.
- I titoli sono riconosciuti con un'euristica (righe brevi senza punto finale): funziona sui PDF di esempio, ma su documenti reali sarebbe più affidabile usare la dimensione o il grassetto del carattere.
- Lo slider "Passaggi da recuperare" di Streamlit ha poco effetto con un corpus così piccolo.
- L'esito "con risposta" nel registro si calcola cercando la frase di rifiuto nel testo della risposta.
- Nei test manuali la prima richiesta dopo un periodo di inattività ha impiegato circa 54 secondi, perché Ollama deve ricaricare i modelli in GPU; quelle successive circa 2 secondi.

## Struttura

```
app/
  config.py             impostazioni (modelli, indirizzo di Ollama, soglia)
  chunking.py           lettura PDF e suddivisione in chunk
  vectorstore.py        embeddings e ChromaDB
  rag.py                recupero, generazione, registro delle domande
  db.py                 SQLite: catalogo e query di analisi
  schemas.py            validazione Pydantic
  main.py               API FastAPI
streamlit_app.py        interfaccia web
scripts/                PDF di esempio, indicizzazione, domande da terminale, valutazione, analisi
sql/                    schema e query di analisi
tests/                  test automatici (non richiedono Ollama)
data/
  pdfs/                 documenti di esempio (fittizi)
  eval_questions.json   domande per la valutazione del recupero
```

## Come eseguirlo

Prerequisiti: Python 3.12 e [Ollama](https://ollama.com).

```bash
pip install -r requirements.txt
ollama pull gemma3:12b
ollama pull bge-m3

python -m scripts.make_sample_pdfs      # genera i PDF di esempio
python -m scripts.index_documents       # crea indice vettoriale e catalogo SQL
python -m scripts.ask "Chi può autorizzare lo sbarco dei passeggeri?"
```

Interfaccia web e API:

```bash
streamlit run streamlit_app.py
uvicorn app.main:app --reload           # documentazione interattiva su /docs
```

| Endpoint | Descrizione |
|---|---|
| `POST /ask` | domanda → risposta con fonti |
| `GET /stats` | risultati delle query di analisi SQL |
| `GET /health` | stato di Ollama e numero di documenti e chunk |

Test: `pytest -q`.

### Configurazione

Variabili d'ambiente (tutte opzionali): `OLLAMA_BASE_URL` (default `http://localhost:11434`), `CHAT_MODEL` (default `gemma3:12b`), `EMBEDDING_MODEL` (default `bge-m3`), `MAX_DISTANCE` (default `0.5`).

Se usi Ollama su Windows e il codice in WSL (la configurazione con cui è stato sviluppato, con una GPU AMD), imposta `OLLAMA_BASE_URL` all'indirizzo di Windows visto da WSL e avvia Ollama con `OLLAMA_HOST=0.0.0.0`.

## Possibili sviluppi

- Mostrare solo le fonti realmente citate nella risposta (leggendo i numeri `[n]` dal testo).
- Riconoscere i titoli dei PDF dalla dimensione o dal grassetto del carattere.
- Ricerca ibrida: combinare la ricerca semantica con la ricerca per parole chiave (FTS5 di SQLite).
- Ampliare il corpus con documenti pubblici e rifare la valutazione con domande scritte da altri.

## Ambiente

Sviluppato con Python 3.12 su WSL2 (Ubuntu 24.04), in un ambiente virtuale condiviso con altri progetti, con Ollama su Windows e una GPU AMD. Le dipendenze non hanno versioni fissate e il progetto non è stato verificato su un ambiente pulito: se manca qualcosa, aggiungilo a `requirements.txt`.

## Tecnologie

Python, FastAPI, Pydantic, SQLite, ChromaDB, PyMuPDF, Ollama (`gemma3:12b`, `bge-m3`), Streamlit, pytest.