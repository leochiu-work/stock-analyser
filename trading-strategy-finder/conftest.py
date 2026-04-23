"""
Root conftest: set required env vars before any app module is imported.
This file is processed by pytest before test collection begins.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("CHROMA_HOST", "localhost")
os.environ.setdefault("CHROMA_PORT", "8000")
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("OLLAMA_MODEL", "gemma3")
os.environ.setdefault("OLLAMA_EMBED_MODEL", "nomic-embed-text")
os.environ.setdefault("PRICE_SERVICE_BASE_URL", "http://localhost:8004")
os.environ.setdefault("TA_SERVICE_BASE_URL", "http://localhost:8005")
