import pymupdf

from app import config
from app.chunking import chunk_pdf
from app.db import init_db, replace_catalog
from app.vectorstore import rebuild_index

init_db()
documents, chunks = [], []
for pdf in sorted(config.PDF_DIR.glob("*.pdf")):
    with pymupdf.open(pdf) as doc:
        documents.append((pdf.name, len(doc)))
    chunks.extend(chunk_pdf(pdf))

replace_catalog(documents, chunks)
print(f"Documenti: {len(documents)} - chunk indicizzati: {rebuild_index(chunks)}")
