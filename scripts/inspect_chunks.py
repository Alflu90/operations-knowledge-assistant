from pathlib import Path

from app.chunking import chunk_pdf

for pdf in sorted(Path("data/pdfs").glob("*.pdf")):
    chunks = chunk_pdf(pdf)
    print(f"\n=== {pdf.name}: {len(chunks)} chunk ===")
    for c in chunks:
        preview = c.text.replace("\n", " | ")[:110]
        print(f"[p.{c.page} #{c.index} {len(c.text)} car.] {preview}...")
