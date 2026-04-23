import uuid
from pathlib import Path

from app.chroma import get_collection

SEED_DIR = Path(__file__).parent / "data" / "seed"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50


def chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def seed_if_empty():
    collection = get_collection()
    if collection.count() > 0:
        return
    for md_file in SEED_DIR.glob("*.md"):
        investor = md_file.stem
        text = md_file.read_text()
        chunks = chunk_text(text)
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [
            {"investor": investor, "source": md_file.name, "chunk_index": i}
            for i, _ in enumerate(chunks)
        ]
        collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
