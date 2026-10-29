import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from backend.db.database import get_db
from backend.db.models import Conversation, Message

router = APIRouter()


class MessageOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    modality: str
    extra_metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailOut(ConversationOut):
    messages: List[MessageOut] = []


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"


@router.get("", response_model=List[ConversationOut])
def get_conversations(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all saved conversations sorted by recent activity."""
    return (
        db.query(Conversation)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("", response_model=ConversationOut)
def create_conversation(req: ConversationCreate, db: Session = Depends(get_db)):
    """Creates a new conversation thread."""
    conv = Conversation(title=req.title or "New Conversation")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
def get_conversation(conversation_id: uuid.UUID, db: Session = Depends(get_db)):
    """Fetches details and message history for a specific conversation."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: uuid.UUID, db: Session = Depends(get_db)):
    """Deletes a conversation and its messages."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return {"message": "Conversation deleted successfully", "id": str(conversation_id)}

