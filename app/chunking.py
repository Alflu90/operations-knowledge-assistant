"""Lettura dei PDF e suddivisione del testo in chunk con riferimento alla pagina."""
import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf

MAX_CHARS = 800


@dataclass
class Chunk:
    source: str  # nome del file PDF
    page: int    # numero di pagina (da 1)
    index: int   # posizione progressiva del chunk nel documento
    text: str


@dataclass
class _Unit:
    heading: str        # titolo della sezione a cui appartiene il paragrafo
    text: str           # testo del paragrafo
    with_heading: bool  # True se è il primo paragrafo sotto quel titolo


def _is_heading(text: str) -> bool:
    # Titoli e domande delle FAQ: brevi e senza punto finale (euristica)
    return len(text) <= 120 and not text.endswith(".")


def _render(unit: _Unit, force_heading: bool = False) -> str:
    if (unit.with_heading or force_heading) and unit.heading:
        return f"{unit.heading}\n{unit.text}"
    return unit.text


def _page_units(page: "pymupdf.Page", heading: str) -> tuple[list[_Unit], str]:
    """Paragrafi della pagina con il loro titolo; restituisce anche il titolo corrente a fine pagina."""
    units: list[_Unit] = []
    pending = False  # c'è un titolo non ancora seguito da un paragrafo
    for block in page.get_text("blocks", sort=True):
        if block[6] != 0:  # salta le immagini
            continue
        text = " ".join(block[4].split())
        if not text:
            continue
        if _is_heading(text):
            heading = f"{heading} {text}" if pending else text  # titoli su più righe: uniti
            pending = True
        else:
            units.append(_Unit(heading, text, with_heading=pending))
            pending = False
    return units, heading


def _split_long(text: str, max_chars: int) -> list[str]:
    """Divide un testo troppo lungo per frasi."""
    parts, current = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if current and len(current) + 1 + len(sentence) > max_chars:
            parts.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        parts.append(current)
    return parts


def _expand(unit: _Unit, max_chars: int) -> list[_Unit]:
    if len(_render(unit)) <= max_chars:
        return [unit]
    pieces = _split_long(unit.text, max_chars)
    return [
        _Unit(unit.heading, piece, with_heading=unit.with_heading and i == 0)
        for i, piece in enumerate(pieces)
    ]


def _pack(units: list[_Unit], max_chars: int) -> list[str]:
    """Raggruppa i paragrafi in chunk; un chunk che inizia a metà sezione riceve il titolo."""
    chunks, current = [], ""
    for unit in units:
        for piece in _expand(unit, max_chars):
            joined = _render(piece)
            if current and len(current) + 2 + len(joined) > max_chars:
                chunks.append(current)
                current = _render(piece, force_heading=True)
            elif current:
                current = f"{current}\n\n{joined}"
            else:
                current = _render(piece, force_heading=True)
    if current:
        chunks.append(current)
    return chunks


def chunk_pdf(pdf_path: Path | str, max_chars: int = MAX_CHARS) -> list[Chunk]:
    pdf_path = Path(pdf_path)
    chunks: list[Chunk] = []
    heading = ""
    with pymupdf.open(pdf_path) as doc:
        for page_number, page in enumerate(doc, start=1):
            units, heading = _page_units(page, heading)
            for text in _pack(units, max_chars):
                chunks.append(Chunk(pdf_path.name, page_number, len(chunks), text))
    return chunks
