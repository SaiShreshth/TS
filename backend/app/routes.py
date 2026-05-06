import uuid
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from app.rag import generate_response, ingest_pdf, ingest_image, ingest_audio

router = APIRouter()


def _build_stage(name: str, status: str = "done", detail: str | None = None):
    stage = {"name": name, "status": status}
    if detail:
        stage["detail"] = detail
    return stage

class Query(BaseModel):
    text: str

@router.post("/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = f"temp_{uuid.uuid4().hex}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    result = ingest_pdf(file_path)
    stages = [
        _build_stage("Upload", "done"),
        _build_stage("RAG indexing", "done", f"{result['chunk_count']} chunks"),
        _build_stage("Knowledge graph update", "done"),
        _build_stage("Summary", "done"),
    ]
    return {
        "message": "PDF processed",
        "summary": result["summary"],
        "stages": stages,
        "stats": {
            "pages": result["page_count"],
            "chunks": result["chunk_count"],
        },
    }

@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    file_path = f"temp_{uuid.uuid4().hex}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    ingest_image(file_path)
    stages = [
        _build_stage("Upload", "done"),
        _build_stage("Image embedding", "done"),
        _build_stage("Knowledge graph update", "done"),
    ]
    return {"message": "Image processed", "stages": stages}

@router.post("/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    file_path = f"temp_{uuid.uuid4().hex}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    ingest_audio(file_path)
    stages = [
        _build_stage("Upload", "done"),
        _build_stage("Transcription", "done"),
        _build_stage("RAG indexing", "done"),
        _build_stage("Knowledge graph update", "done"),
    ]
    return {"message": "Audio processed", "stages": stages}

@router.post("/query")
def query(data: Query):
    return {"response": generate_response(data.text)}
