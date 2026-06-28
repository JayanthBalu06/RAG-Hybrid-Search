from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel, Field

from normalizer import normalize
from chunker import chunk, Strategy, Chunk
from indexer import index_chunks

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


class ChunkInput(BaseModel):
    text: str
    index: int
    strategy: str
    metadata: dict = {}


class IndexRequest(BaseModel):
    source: str
    chunks: List[ChunkInput]


class ChunkRequest(BaseModel):
    text: str
    strategy: Strategy = "fixed"
    chunk_size: int = Field(512, gt=0)
    chunk_overlap: int = Field(50, ge=0)
    similarity_threshold: float = Field(0.75, gt=0, le=1)
    min_chunk_chars: int = Field(100, gt=0)


@app.post("/documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        content = await file.read()
        try:
            text = normalize(file.filename, content)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        results.append({
            "filename": file.filename,
            "char_count": len(text),
            "word_count": len(text.split()),
            "text": text,
        })
    return {"documents": results}


@app.post("/chunk")
async def chunk_text(req: ChunkRequest):
    try:
        chunks = chunk(
            text=req.text,
            strategy=req.strategy,
            chunk_size=req.chunk_size,
            chunk_overlap=req.chunk_overlap,
            similarity_threshold=req.similarity_threshold,
            min_chunk_chars=req.min_chunk_chars,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {
        "strategy": req.strategy,
        "chunk_count": len(chunks),
        "chunks": [c.to_dict() for c in chunks],
    }


@app.post("/index")
async def index_documents(req: IndexRequest):
    chunks = [
        Chunk(text=c.text, index=c.index, strategy=c.strategy, metadata=c.metadata)
        for c in req.chunks
    ]
    try:
        result = await index_chunks(chunks, req.source)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return result.to_dict()
