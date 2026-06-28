from __future__ import annotations

import asyncio
import json
import os
import pickle
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from rank_bm25 import BM25Okapi

from chunker import Chunk

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
CHROMA_DIR = DATA_DIR / "chroma"
BM25_INDEX_PATH = DATA_DIR / "bm25_index.pkl"
BM25_CORPUS_PATH = DATA_DIR / "bm25_corpus.json"

COLLECTION_NAME = "chunks"


@dataclass
class IndexResult:
    indexed: int
    source: str
    chroma_collection: str
    bm25_corpus_size: int

    def to_dict(self) -> dict:
        return {
            "indexed": self.indexed,
            "source": self.source,
            "chroma_collection": self.chroma_collection,
            "bm25_corpus_size": self.bm25_corpus_size,
        }


def _get_collection():
    ef = OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"],
        model_name="text-embedding-3-small",
    )
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(COLLECTION_NAME, embedding_function=ef)


def _extract_heading(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return ""


def _make_metadata(c: Chunk, source: str) -> dict:
    return {
        "source": source,
        "chunk_index": c.index,
        "strategy": c.strategy,
        "char_count": len(c.text),
        "section_heading": _extract_heading(c.text),
        **{k: str(v) for k, v in c.metadata.items()},
    }


# ── chroma ────────────────────────────────────────────────────────────────────

def _index_chroma(collection, chunks: list[Chunk], source: str) -> None:
    existing = collection.get(where={"source": source})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    collection.add(
        ids=[f"{source}__{c.index}" for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[_make_metadata(c, source) for c in chunks],
    )


# ── bm25 ──────────────────────────────────────────────────────────────────────

def _load_corpus() -> list[dict]:
    if BM25_CORPUS_PATH.exists():
        return json.loads(BM25_CORPUS_PATH.read_text())
    return []


def _index_bm25(chunks: list[Chunk], source: str) -> int:
    corpus = [e for e in _load_corpus() if e["source"] != source]
    for c in chunks:
        corpus.append({
            "id": f"{source}__{c.index}",
            "source": source,
            "text": c.text,
            **_make_metadata(c, source),
        })

    BM25_CORPUS_PATH.write_text(json.dumps(corpus, ensure_ascii=False))

    bm25 = BM25Okapi([e["text"].lower().split() for e in corpus])
    with open(BM25_INDEX_PATH, "wb") as f:
        pickle.dump(bm25, f)

    return len(corpus)


# ── public api ────────────────────────────────────────────────────────────────

def load_bm25() -> tuple[BM25Okapi | None, list[dict]]:
    corpus = _load_corpus()
    if BM25_INDEX_PATH.exists() and corpus:
        with open(BM25_INDEX_PATH, "rb") as f:
            return pickle.load(f), corpus
    return None, corpus


async def index_chunks(chunks: list[Chunk], source: str) -> IndexResult:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    # Collection created once here — passed into the chroma thread to avoid
    # two threads racing to open the same SQLite file.
    collection = _get_collection()

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=2) as pool:
        chroma_task = loop.run_in_executor(pool, _index_chroma, collection, chunks, source)
        bm25_task = loop.run_in_executor(pool, _index_bm25, chunks, source)
        _, corpus_size = await asyncio.gather(chroma_task, bm25_task)

    return IndexResult(
        indexed=len(chunks),
        source=source,
        chroma_collection=COLLECTION_NAME,
        bm25_corpus_size=corpus_size,
    )
