"""Chunk storage + similarity search.

Portable-first: embeddings are stored as JSON and searched with python cosine — works on
SQLite (tests) AND PostgreSQL with zero extensions. For large corpora, swap `search` to a
pgvector `<=>` query (the storage schema already fits; see the TODO below).
"""
import json
from typing import List, Tuple

from sqlalchemy.orm import Session

from ai.embeddings import cosine, get_embedding
from database.models import DocumentChunk


def store_chunks(db: Session, document_id: str, chunks: List[str],
                 embeddings: List[List[float]]) -> None:
    for idx, (content, emb) in enumerate(zip(chunks, embeddings)):
        db.add(DocumentChunk(
            document_id=document_id,
            chunk_index=idx,
            content=content,
            embedding=json.dumps(emb),
        ))
    db.commit()


def search(db: Session, query: str, top_k: int = 5,
           document_id: str = None) -> List[Tuple[DocumentChunk, float]]:
    """Return the top_k most similar chunks with scores, best first.
    TODO(scale): replace the in-python scan with pgvector `ORDER BY embedding <=> :q`."""
    q_emb = get_embedding(query)
    qry = db.query(DocumentChunk)
    if document_id:
        qry = qry.filter(DocumentChunk.document_id == document_id)
    scored = []
    for chunk in qry.all():
        try:
            emb = json.loads(chunk.embedding)
        except (TypeError, ValueError):
            continue
        scored.append((chunk, cosine(q_emb, emb)))
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored[:top_k]
