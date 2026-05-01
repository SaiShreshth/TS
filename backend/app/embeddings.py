import os
import numpy as np
from PIL import Image
import torch
import clip
import whisper
from sentence_transformers import SentenceTransformer

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

text_model = SentenceTransformer("all-MiniLM-L6-v2")
clip_model, clip_preprocess = clip.load("ViT-B/32", device=DEVICE)
whisper_model = whisper.load_model("base", device=DEVICE)


def embed_text(text: str) -> np.ndarray:
    embedding = text_model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return embedding.astype("float32")


def embed_clip_text(text: str) -> np.ndarray:
    text_tokens = clip.tokenize([text]).to(DEVICE)
    with torch.no_grad():
        text_embedding = clip_model.encode_text(text_tokens)
    text_embedding = text_embedding / text_embedding.norm(dim=-1, keepdim=True)
    return text_embedding.cpu().numpy().astype("float32")[0]


def embed_image(path: str) -> np.ndarray:
    image = Image.open(path).convert("RGB")
    processed = clip_preprocess(image).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        image_embedding = clip_model.encode_image(processed)
    image_embedding = image_embedding / image_embedding.norm(dim=-1, keepdim=True)
    return image_embedding.cpu().numpy().astype("float32")[0]


def transcribe_audio(path: str) -> str:
    transcription = whisper_model.transcribe(path)
    return transcription.get("text", "")
