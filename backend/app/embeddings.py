import os
import numpy as np
from PIL import Image
import torch
import clip
import whisper
from sentence_transformers import SentenceTransformer

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

text_model = None
clip_model = None
clip_preprocess = None
whisper_model = None


def _get_text_model():
    global text_model
    if text_model is None:
        text_model = SentenceTransformer("all-MiniLM-L6-v2")
    return text_model


def _get_clip_model():
    global clip_model, clip_preprocess
    if clip_model is None or clip_preprocess is None:
        clip_model, clip_preprocess = clip.load("ViT-B/32", device=DEVICE)
    return clip_model, clip_preprocess


def _get_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = whisper.load_model("base", device=DEVICE)
    return whisper_model


def embed_text(text: str) -> np.ndarray:
    model = _get_text_model()
    embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return embedding.astype("float32")


def embed_clip_text(text: str) -> np.ndarray:
    model, _preprocess = _get_clip_model()
    text_tokens = clip.tokenize([text]).to(DEVICE)
    with torch.no_grad():
        text_embedding = model.encode_text(text_tokens)
    text_embedding = text_embedding / text_embedding.norm(dim=-1, keepdim=True)
    return text_embedding.cpu().numpy().astype("float32")[0]


def embed_image(path: str) -> np.ndarray:
    model, preprocess = _get_clip_model()
    image = Image.open(path).convert("RGB")
    processed = preprocess(image).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        image_embedding = model.encode_image(processed)
    image_embedding = image_embedding / image_embedding.norm(dim=-1, keepdim=True)
    return image_embedding.cpu().numpy().astype("float32")[0]


def transcribe_audio(path: str) -> str:
    model = _get_whisper_model()
    transcription = model.transcribe(path)
    return transcription.get("text", "")
