import os
import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.security import is_allowed_file, ALLOWED_DOCUMENT_EXTENSIONS
from backend.db.database import get_db
from backend.db.models import Document, DocumentChunk, Conversation
from backend.schemas.documents import (
    DocumentResponse,
    DocumentDetailResponse,
    DocumentChunkResponse,
    DocumentAskRequest,
    DocumentAskResponse,
    DocumentCreateRequest
)
from backend.services.document_service import DocumentService
from backend.services.embedding_service import EmbeddingService
from backend.services.llm_service import llm_service

logger = logging.getLogger("uvicorn.error")
router = APIRouter()
settings = get_settings()
embedding_service = EmbeddingService()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: Optional[uuid.UUID] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Uploads a document (PDF, DOCX, TXT), extracts text, generates sliding-window
    chunks and dense vector embeddings, and stores them in the database for RAG.
    """
    if not is_allowed_file(file.filename, ALLOWED_DOCUMENT_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported formats: {', '.join(ALLOWED_DOCUMENT_EXTENSIONS)}"
        )

    file_bytes = await file.read()
    if len(file_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # 1. Save file to storage
    file_path = DocumentService.save_uploaded_file(file_bytes, file.filename)

    # 2. Extract textual content
    try:
        extracted_text = DocumentService.extract_text_from_bytes(file_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to extract document text: {str(e)}")

    # 3. Create document record
    doc_record = Document(
        conversation_id=conversation_id,
        filename=file.filename,
        file_type=file.filename.split(".")[-1].lower(),
        file_path=file_path,
        extracted_text=extracted_text,
        version=1
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # 4. Chunk text and generate vector embeddings
    text_chunks = DocumentService.chunk_text(extracted_text, chunk_size=500, overlap=100)
    if text_chunks:
        embeddings = embedding_service.get_embeddings_batch(text_chunks)
        chunk_objects = []
        for i, (chunk_str, emb) in enumerate(zip(text_chunks, embeddings)):
            chunk_objects.append(
                DocumentChunk(
                    document_id=doc_record.id,
                    chunk_index=i + 1,
                    chunk_text=chunk_str,
                    embedding=emb
                )
            )
        db.add_all(chunk_objects)
        db.commit()

    chunk_count = len(text_chunks)
    preview = (extracted_text[:150] + "...") if len(extracted_text) > 150 else extracted_text

    return DocumentResponse(
        id=doc_record.id,
        filename=doc_record.filename,
        file_type=doc_record.file_type,
        version=doc_record.version,
        chunk_count=chunk_count,
        text_preview=preview,
        created_at=doc_record.created_at,
        updated_at=doc_record.updated_at
    )


@router.get("", response_model=List[DocumentResponse])
def list_documents(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Lists all uploaded documents with chunk count and preview."""
    docs = db.query(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    out = []
    for d in docs:
        c_count = len(d.chunks)
        preview = (d.extracted_text[:150] + "...") if d.extracted_text and len(d.extracted_text) > 150 else (d.extracted_text or "")
        out.append(
            DocumentResponse(
                id=d.id,
                filename=d.filename,
                file_type=d.file_type,
                version=d.version,
                chunk_count=c_count,
                text_preview=preview,
                created_at=d.created_at,
                updated_at=d.updated_at
            )
        )
    return out


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document_details(document_id: uuid.UUID, db: Session = Depends(get_db)):
    """Fetches details and all constituent chunks of a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunk_responses = [
        DocumentChunkResponse(
            id=c.id,
            chunk_index=c.chunk_index,
            chunk_text=c.chunk_text,
            created_at=c.created_at
        )
        for c in doc.chunks
    ]

    return DocumentDetailResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_path=doc.file_path,
        extracted_text=doc.extracted_text,
        version=doc.version,
        chunks=chunk_responses,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )


@router.post("/{document_id}/ask", response_model=DocumentAskResponse)
def ask_document(
    document_id: uuid.UUID,
    req: DocumentAskRequest,
    db: Session = Depends(get_db)
):
    """
    Answers a question specifically grounded in the chunks of a single document.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc.chunks:
        raise HTTPException(status_code=400, detail="Document has no indexed text chunks.")

    # Compute similarity against document's chunks
    q_emb = embedding_service.get_embedding(req.question)
    scored = []
    for chunk in doc.chunks:
        if chunk.embedding:
            sim = llm_service._cosine_similarity(q_emb, chunk.embedding)
            scored.append((chunk, sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    top_chunks = scored[:req.top_k]

    context_text = "\n\n".join([f"[Chunk #{c.chunk_index}]: {c.chunk_text}" for c, _ in top_chunks])
    sources = [f"{doc.filename} - Chunk #{c.chunk_index}" for c, _ in top_chunks]

    # Generate answer
    system_prompt = (
        f"You are a document analysis assistant. Answer the user's question using ONLY the following excerpts "
        f"from '{doc.filename}'. If the answer cannot be found, politely state that the document does not contain that information.\n\n"
        f"Document Excerpts:\n{context_text}"
    )

    answer = ""
    if llm_service.openai_client:
        answer = llm_service._call_openai(
            system_prompt=system_prompt,
            user_content=req.question,
            history=[]
        )
    elif llm_service.gemini_client:
        answer = llm_service._call_gemini(
            system_prompt=system_prompt,
            user_content=req.question,
            history=[]
        )

    if not answer:
        answer = (
            f"Based on '{doc.filename}', here are the most relevant sections found:\n\n"
            + "\n\n".join([f"- **Chunk #{c.chunk_index}**: {c.chunk_text[:200]}..." for c, _ in top_chunks])
        )

    return DocumentAskResponse(
        document_id=doc.id,
        filename=doc.filename,
        question=req.question,
        answer=answer,
        sources=sources
    )


@router.post("/generate")
def generate_document_file(req: DocumentCreateRequest):
    """
    Generates a new downloadable document (.txt or .docx) from text.
    """
    try:
        out_path, out_filename = DocumentService.create_document_file(
            title=req.title,
            content=req.content,
            file_format=req.file_format
        )
        return {
            "title": req.title,
            "filename": out_filename,
            "file_path": out_path,
            "download_url": f"/storage/generated/{out_filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate document file: {e}")


@router.delete("/{document_id}")
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    """Deletes a document and its stored chunks."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully", "id": str(document_id)}

