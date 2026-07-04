"""RAG answering: retrieve top chunks → prompt the LLM → answer with [chunk-N] citations.
TESTING=1 uses a FakeLLM (canned, cites the top chunk) so tests need no API key.

The chat LLM is any OpenAI-compatible provider, switched by configuration only:
  LLM_BASE_URL — empty = api.openai.com; https://api.groq.com/openai/v1 for Groq;
                 Gemini's OpenAI-compat endpoint for Gemini
  LLM_API_KEY  — falls back to OPENAI_API_KEY
  RUNTIME_LLM  — model name, e.g. gpt-4o / llama-3.3-70b-versatile / gemini-2.0-flash
"""
import os
from typing import Dict, Generator, List, Tuple

from sqlalchemy.orm import Session

from ai.vector_store import search
from database.models import DocumentChunk

TESTING = os.getenv("TESTING") == "1"
RUNTIME_LLM = os.getenv("RUNTIME_LLM", "gpt-4o")
TOP_K = int(os.getenv("RAG_TOP_K", "5"))


def _client():
    from openai import OpenAI
    base_url = os.getenv("LLM_BASE_URL") or None
    api_key = os.getenv("LLM_API_KEY") or os.environ["OPENAI_API_KEY"]
    return OpenAI(api_key=api_key, base_url=base_url)

ANSWER_PROMPT = """You are a helpful assistant. Answer the question using ONLY the context.
Cite sources inline as [chunk-N]. If the context is insufficient, say so.

Context:
{context}

Question: {question}

Answer:"""


def _build_context(hits: List[Tuple[DocumentChunk, float]]) -> str:
    return "\n\n".join(f"[chunk-{c.chunk_index}] {c.content}" for c, _ in hits)


def answer_question(db: Session, question: str, document_id: str = None) -> Dict:
    hits = search(db, question, top_k=TOP_K, document_id=document_id)
    if not hits:
        return {"answer": "No documents have been ingested yet.", "citations": []}
    citations = [
        {"chunk_index": c.chunk_index, "document_id": c.document_id,
         "score": round(s, 4), "preview": c.content[:160]}
        for c, s in hits
    ]
    if TESTING:
        top = hits[0][0]
        answer = f"Based on the documents: {top.content[:200]} [chunk-{top.chunk_index}]"
        return {"answer": answer, "citations": citations}

    resp = _client().chat.completions.create(
        model=RUNTIME_LLM,
        messages=[{"role": "user", "content": ANSWER_PROMPT.format(
            context=_build_context(hits), question=question)}],
        max_tokens=600,
    )
    return {"answer": resp.choices[0].message.content, "citations": citations}


def stream_answer(db: Session, question: str, document_id: str = None) -> Generator[str, None, None]:
    """Yield answer tokens (for SSE). Same retrieval as answer_question."""
    hits = search(db, question, top_k=TOP_K, document_id=document_id)
    if not hits:
        yield "No documents have been ingested yet."
        return
    if TESTING:
        top = hits[0][0]
        for word in f"Based on the documents: {top.content[:120]} [chunk-{top.chunk_index}]".split():
            yield word + " "
        return
    stream = _client().chat.completions.create(
        model=RUNTIME_LLM,
        messages=[{"role": "user", "content": ANSWER_PROMPT.format(
            context=_build_context(hits), question=question)}],
        max_tokens=600,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
