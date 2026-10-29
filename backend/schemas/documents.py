import uuid
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class DocumentChunkResponse(BaseModel):
    id: uuid.UUID
    chunk_index: int
    chunk_text: str
    created_at: datetime


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    file_type: str
    version: int
    chunk_count: int
    status: str = "ready"
    text_preview: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(BaseModel):
    id: uuid.UUID
    filename: str
    file_type: str
    file_path: Optional[str]
    extracted_text: Optional[str]
    version: int
    status: str = "ready"
    chunks: List[DocumentChunkResponse] = []
    created_at: datetime
    updated_at: datetime


class DocumentUpdateRequest(BaseModel):
    extracted_text: str = Field(..., description="Updated text content for document reindexing")


class DocumentCreateRequest(BaseModel):
    title: str = Field(..., description="Document filename/title without extension")
    content: str = Field(..., description="Document content text")
    file_format: Literal["txt", "docx"] = Field("txt", description="Desired export format")


class DocumentAskRequest(BaseModel):
    question: str = Field(..., description="Question to answer using document context")
    top_k: int = Field(4, description="Number of relevant chunks to retrieve")


class DocumentAskResponse(BaseModel):
    document_id: uuid.UUID
    filename: str
    question: str
    answer: str
    sources: List[str] = []
