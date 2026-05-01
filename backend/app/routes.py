import uuid
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from app.rag import generate_response, ingest_pdf, ingest_image, ingest_audio

router = APIRouter()

class Query(BaseModel):
    text: str

@router.post("/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = f"temp_{uuid.uuid4().hex}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    ingest_pdf(file_path)
    return {"message": "PDF processed"}

@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    file_path = f"temp_{uuid.uuid4().hex}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    ingest_image(file_path)
    return {"message": "Image processed"}

@router.post("/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    file_path = f"temp_{uuid.uuid4().hex}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    ingest_audio(file_path)
    return {"message": "Audio processed"}

@router.post("/query")
def query(data: Query):
    return {"response": generate_response(data.text)}
