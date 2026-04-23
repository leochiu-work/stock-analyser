from __future__ import annotations

import uuid


def add_document(collection, text: str, metadata: dict) -> str:
    doc_id = str(uuid.uuid4())
    collection.upsert(
        documents=[text],
        ids=[doc_id],
        metadatas=[metadata],
    )
    return doc_id


def list_documents(collection) -> list[dict]:
    result = collection.get(include=["metadatas"])
    ids = result.get("ids", [])
    metadatas = result.get("metadatas", [])
    documents = []
    for doc_id, meta in zip(ids, metadatas):
        entry = {"id": doc_id}
        entry.update(meta or {})
        documents.append(entry)
    return documents


def delete_document(collection, doc_id: str) -> None:
    collection.delete(ids=[doc_id])
