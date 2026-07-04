"""Embeddings — any OpenAI-compatible provider in production, a deterministic
FakeEmbedder when TESTING=1.

Provider is pure configuration (no code changes needed to switch):
  EMBEDDING_BASE_URL  — empty = api.openai.com; or e.g. Gemini's OpenAI-compat endpoint
  EMBEDDING_API_KEY   — falls back to OPENAI_API_KEY
  EMBEDDING_MODEL     — e.g. text-embedding-3-small (OpenAI) / text-embedding-004 (Gemini)
(Note: Groq has no embeddings API — pair Groq chat with OpenAI/Gemini embeddings.)

The fake produces stable pseudo-vectors from token hashes, so similarity search behaves
consistently in tests with no API key and no network.
"""
import hashlib
import math
import os
from typing import List

TESTING = os.getenv("TESTING") == "1"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))
_FAKE_DIM = 64


def _client():
    from openai import OpenAI
    base_url = os.getenv("EMBEDDING_BASE_URL") or None
    api_key = os.getenv("EMBEDDING_API_KEY") or os.environ["OPENAI_API_KEY"]
    return OpenAI(api_key=api_key, base_url=base_url)


def _fake_embed(text: str) -> List[float]:
    vec = [0.0] * _FAKE_DIM
    for word in text.lower().split():
        # NOT a security hash — just a stable way to bucket a word into the fake vector
        # (test-only embedder). usedforsecurity=False tells scanners this is benign.
        h = int(hashlib.md5(word.encode(), usedforsecurity=False).hexdigest(), 16)
        vec[h % _FAKE_DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def get_embeddings(texts: List[str]) -> List[List[float]]:
    if TESTING:
        return [_fake_embed(t) for t in texts]
    resp = _client().embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in resp.data]


def get_embedding(text: str) -> List[float]:
    return get_embeddings([text])[0]


def cosine(a: List[float], b: List[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    da = math.sqrt(sum(x * x for x in a)) or 1.0
    db = math.sqrt(sum(y * y for y in b)) or 1.0
    return num / (da * db)
