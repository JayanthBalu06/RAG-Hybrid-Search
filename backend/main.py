from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from normalizer import normalize

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


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
