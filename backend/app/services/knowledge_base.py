"""Local policy corpus + chunking used for retrieval in local mode.

In production these documents are ingested into Azure AI Search (see
scripts/ingest_policies.py) and retrieval is served from there. In local mode we
load the same markdown files, chunk them, and do a lightweight keyword search so
the chatbot works without any cloud dependency.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_POLICY_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "policies"

# Common English stop-words to ignore when scoring keyword overlap.
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "for", "on",
    "do", "i", "you", "my", "me", "what", "how", "explain", "summarize", "can",
    "need", "submit", "your", "our", "with", "about", "this", "that", "please",
}


@dataclass
class Chunk:
    """A retrievable slice of a policy document."""

    doc_title: str
    source: str
    heading: str
    text: str


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in _STOP_WORDS and len(w) > 1}


def _chunk_markdown(path: Path) -> list[Chunk]:
    """Split a markdown file into chunks, one per section heading."""
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    doc_title = lines[0].lstrip("# ").strip() if lines else path.stem

    chunks: list[Chunk] = []
    heading = doc_title
    buffer: list[str] = []

    def flush() -> None:
        body = "\n".join(buffer).strip()
        if body:
            chunks.append(
                Chunk(doc_title=doc_title, source=path.name, heading=heading, text=body)
            )

    for line in lines[1:]:
        if line.startswith("## "):
            flush()
            heading = line.lstrip("# ").strip()
            buffer = []
        else:
            buffer.append(line)
    flush()
    return chunks


@lru_cache
def load_chunks() -> list[Chunk]:
    """Load and chunk every policy document (cached)."""
    if not _POLICY_DIR.exists():
        return []
    chunks: list[Chunk] = []
    for path in sorted(_POLICY_DIR.glob("*.md")):
        chunks.extend(_chunk_markdown(path))
    return chunks


def keyword_search(query: str, top_k: int = 3) -> list[Chunk]:
    """Score chunks by keyword overlap with the query; return the best matches."""
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []

    scored: list[tuple[int, Chunk]] = []
    for chunk in load_chunks():
        haystack = _tokenize(f"{chunk.doc_title} {chunk.heading} {chunk.text}")
        overlap = len(q_tokens & haystack)
        if overlap:
            scored.append((overlap, chunk))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]
