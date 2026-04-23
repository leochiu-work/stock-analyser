from __future__ import annotations

import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from app.config import settings

_client: chromadb.HttpClient | None = None


def get_client() -> chromadb.HttpClient:
    global _client
    if _client is None:
        _client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    return _client


def get_collection():
    ef = OllamaEmbeddingFunction(
        url=settings.ollama_base_url,
        model_name=settings.ollama_embed_model,
    )
    return get_client().get_or_create_collection("investor_philosophies", embedding_function=ef)
