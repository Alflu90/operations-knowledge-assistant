import os
from pathlib import Path

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemma3:12b")

PDF_DIR = Path("data/pdfs")
CHROMA_DIR = Path("chroma_db")
COLLECTION_NAME = "operations_docs"
DB_PATH = Path("rag.db")
MAX_DISTANCE = float(os.getenv("MAX_DISTANCE", "0.5"))
