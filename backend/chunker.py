from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter

Strategy = Literal["fixed", "recursive", "semantic"]

HEADER_SEPARATORS = [
    "\n# ", "\n## ", "\n### ", "\n#### ",
    "\n\n", "\n", ". ", " ", "",
]


@dataclass
class Chunk:
    text: str
    index: int
    strategy: Strategy
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "text": self.text,
            "strategy": self.strategy,
            "metadata": self.metadata,
        }


def chunk(
    text: str,
    strategy: Strategy = "fixed",
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    similarity_threshold: float = 0.75,
    min_chunk_chars: int = 100,
) -> list[Chunk]:
    if strategy == "fixed":
        return _fixed(text, chunk_size, chunk_overlap)
    if strategy == "recursive":
        return _recursive(text, chunk_size, chunk_overlap)
    if strategy == "semantic":
        return _semantic(text, similarity_threshold, min_chunk_chars)
    raise ValueError(f"Unknown strategy '{strategy}'. Choose: fixed, recursive, semantic")


# ── strategy implementations ──────────────────────────────────────────────────

def _fixed(text: str, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    return [
        Chunk(
            text=t,
            index=i,
            strategy="fixed",
            metadata={"chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
        )
        for i, t in enumerate(splitter.split_text(text))
    ]


def _recursive(text: str, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=HEADER_SEPARATORS,
    )
    return [
        Chunk(
            text=t,
            index=i,
            strategy="recursive",
            metadata={"chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
        )
        for i, t in enumerate(splitter.split_text(text))
    ]


def _semantic(text: str, threshold: float, min_chunk_chars: int) -> list[Chunk]:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
    if not sentences:
        return []

    response = client.embeddings.create(model="text-embedding-3-small", input=sentences)
    embeddings = [np.array(item.embedding) for item in response.data]

    def cosine(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

    chunks: list[Chunk] = []
    current: list[str] = [sentences[0]]

    for i in range(1, len(sentences)):
        sim = cosine(embeddings[i - 1], embeddings[i])
        accumulated = ". ".join(current)
        if sim < threshold and len(accumulated) >= min_chunk_chars:
            chunks.append(Chunk(
                text=accumulated + ".",
                index=len(chunks),
                strategy="semantic",
                metadata={"similarity_threshold": threshold, "sentence_count": len(current)},
            ))
            current = [sentences[i]]
        else:
            current.append(sentences[i])

    if current:
        chunks.append(Chunk(
            text=". ".join(current) + ".",
            index=len(chunks),
            strategy="semantic",
            metadata={"similarity_threshold": threshold, "sentence_count": len(current)},
        ))

    return chunks
