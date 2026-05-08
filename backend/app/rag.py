import os
import numpy as np
import faiss
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.embeddings import embed_text, embed_image, embed_clip_text, transcribe_audio
from app.llm import generate_chat_answer
from app.graph import init_graph, query_graph

TEXT_DIM = 384
IMAGE_DIM = 512

text_index = None
image_index = None

documents = []
text_metadatas = []
image_metadatas = []


def _ensure_text_index():
    global text_index
    if text_index is None:
        text_index = faiss.IndexFlatL2(TEXT_DIM)


def _ensure_image_index():
    global image_index
    if image_index is None:
        image_index = faiss.IndexFlatL2(IMAGE_DIM)


def add_text_document(text: str, source: str):
    _ensure_text_index()
    embedding = embed_text(text)
    if embedding.ndim == 1:
        embedding = np.expand_dims(embedding, axis=0)
    text_index.add(embedding)
    documents.append(text)
    text_metadatas.append({"source": source})


def add_image_document(path: str):
    _ensure_image_index()
    embedding = embed_image(path)
    if embedding.ndim == 1:
        embedding = np.expand_dims(embedding, axis=0)
    image_index.add(embedding)
    image_metadatas.append({"source": os.path.basename(path)})


def ingest_pdf(path: str):
    init_graph()
    loader = PyPDFLoader(path)
    pages = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    chunks = splitter.split_documents(pages)
    for idx, chunk in enumerate(chunks):
        source = f"pdf:{os.path.basename(path)}:{idx}"
        add_text_document(chunk.page_content, source)
    return {
        "page_count": len(pages),
        "chunk_count": len(chunks),
    }


def ingest_image(path: str):
    init_graph()
    add_image_document(path)


def ingest_audio(path: str):
    init_graph()
    transcript = transcribe_audio(path)
    add_text_document(transcript, f"audio:{os.path.basename(path)}")


def retrieve_text(query: str, top_k: int = 3):
    if text_index is None or text_index.ntotal == 0:
        return []
    query_vector = embed_text(query)
    if query_vector.ndim == 1:
        query_vector = np.expand_dims(query_vector, axis=0)
    distances, indices = text_index.search(query_vector, min(top_k, text_index.ntotal))
    hits = []
    for distance, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(documents):
            continue
        hits.append({
            "text": documents[idx],
            "source": text_metadatas[idx]["source"],
            "score": float(distance),
        })
    return hits


def retrieve_images(query: str, top_k: int = 2):
    if image_index is None or image_index.ntotal == 0:
        return []
    query_vector = embed_clip_text(query)
    if query_vector.ndim == 1:
        query_vector = np.expand_dims(query_vector, axis=0)
    distances, indices = image_index.search(query_vector, min(top_k, image_index.ntotal))
    hits = []
    for distance, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(image_metadatas):
            continue
        hits.append({
            "image": image_metadatas[idx]["source"],
            "score": float(distance),
        })
    return hits


def generate_response(query: str, chat_messages: list | None = None):
    text_hits = retrieve_text(query)
    image_hits = retrieve_images(query)
    graph_hits = query_graph(query)

    context_blocks = []
    if text_hits:
        context_blocks.append("Text snippets")
        for hit in text_hits:
            context_blocks.append(f"[{hit['source']}] {hit['text'][:250]}...")
    if image_hits:
        context_blocks.append("Image matches")
        for hit in image_hits:
            context_blocks.append(f"{hit['image']} (score={hit['score']:.3f})")
    if graph_hits:
        context_blocks.append("Graph matches")
        for hit in graph_hits:
            context_blocks.append(f"{hit}")

    if not context_blocks:
        return {
            "answer": "No retrieved data found. Upload documents first.",
            "context": [],
            "query": query,
            "text_hits": [],
            "image_hits": [],
            "graph_hits": [],
        }

    answer = generate_chat_answer(query, chat_messages, context_blocks)

    return {
        "answer": answer,
        "query": query,
        "context": context_blocks,
        "text_hits": text_hits,
        "image_hits": image_hits,
        "graph_hits": graph_hits,
    }
