"""Document ingestion: extract text (.pdf via pypdf, else UTF-8 text), chunk with overlap,
embed, store chunks. Word-based chunking approximates the token sizes from the contract."""
import io
import os
from typing import List

from sqlalchemy.orm import Session

from ai.embeddings import get_embeddings
from ai.vector_store import store_chunks

CHUNK_WORDS = int(os.getenv("CHUNK_WORDS", "300"))       # ~1000 tokens ≈ 750 words; conservative
OVERLAP_WORDS = int(os.getenv("OVERLAP_WORDS", "60"))


def extract_text(filename: str, data: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    return data.decode("utf-8", errors="replace")


def chunk_text(text: str) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks, start = [], 0
    while start < len(words):
        end = min(start + CHUNK_WORDS, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - OVERLAP_WORDS
    return chunks


def ingest_document(db: Session, document_id: str, filename: str, data: bytes) -> int:
    """Extract → chunk → embed → store. Returns the number of chunks indexed."""
    text = extract_text(filename, data)
    chunks = chunk_text(text)
    if not chunks:
        return 0
    embeddings = get_embeddings(chunks)
    store_chunks(db, document_id, chunks, embeddings)
    return len(chunks)
