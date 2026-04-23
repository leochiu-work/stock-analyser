from __future__ import annotations

from fastapi import APIRouter
from starlette.responses import Response

from app.chroma import get_collection
from app.schemas.document import DocumentAdd, DocumentResponse
from app.services import document_service

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("/", response_model=DocumentResponse, status_code=201)
def add_document(body: DocumentAdd):
    collection = get_collection()
    metadata = {"investor": body.investor, "source": body.source}
    doc_id = document_service.add_document(collection, text=body.text, metadata=metadata)
    return DocumentResponse(id=doc_id, investor=body.investor, source=body.source)


@router.get("/", response_model=list[DocumentResponse])
def list_documents():
    collection = get_collection()
    docs = document_service.list_documents(collection)
    return [
        DocumentResponse(
            id=d["id"],
            investor=d.get("investor", ""),
            source=d.get("source", ""),
        )
        for d in docs
    ]


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str):
    collection = get_collection()
    document_service.delete_document(collection, document_id)
    return Response(status_code=204)
