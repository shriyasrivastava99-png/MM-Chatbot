import os
import uuid
import base64
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.core.security import is_allowed_file, ALLOWED_IMAGE_EXTENSIONS, ALLOWED_DOCUMENT_EXTENSIONS
from backend.db.database import get_db
from backend.db.models import Conversation, Message
from backend.schemas.chat import ChatRequest, ChatResponse, MessageResponse
from backend.services.llm_service import llm_service
from backend.services.document_service import DocumentService

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.post("", response_model=ChatResponse)
def handle_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main chat endpoint handling text, vision multimodal, RAG document grounding,
    web search grounding, emotional assistance, and text-to-speech audio generation.
    """
    conversation = None
    if request.conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        title_snippet = request.message.strip()[:40] if request.message else "New Chat"
        conversation = Conversation(title=title_snippet)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    user_metadata = {}
    if request.image_base64:
        user_metadata["has_image"] = True

    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
        modality=request.modality,
        extra_metadata=user_metadata
    )
    db.add(user_msg)
    db.commit()

    response = llm_service.generate_chat_response(
        request=request,
        db=db,
        conversation=conversation
    )

    # Attach nested message for web frontend compatibility
    response.message = MessageResponse(
        content=response.response_text,
        role="assistant",
        modality=response.modality,
        audio_path=response.audio_path,
        image_path=response.image_path,
        sources=response.sources
    )

    assistant_metadata = {
        "sources": [s.model_dump() for s in response.sources],
        "emotional_safety_flag": response.emotional_safety_flag,
        "audio_path": response.audio_path,
        "image_path": response.image_path
    }
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response.response_text,
        modality=response.modality,
        extra_metadata=assistant_metadata
    )
    db.add(assistant_msg)
    db.commit()

    return response


@router.post("/multimodal", response_model=ChatResponse)
async def chat_multimodal(
    message: str = Form(""),
    conversation_id: Optional[uuid.UUID] = Form(None),
    file: UploadFile = File(None),
    enable_web_search: bool = Form(False),
    enable_rag: bool = Form(True),
    is_emotional_mode: bool = Form(False),
    generate_audio_tts: bool = Form(False),
    db: Session = Depends(get_db)
):
    """
    Multimodal multipart/form-data chat endpoint for file and voice attachments.
    """
    image_b64 = None
    modality = "text"
    extracted_file_text = ""

    if file and file.filename:
        filename = file.filename
        file_bytes = await file.read()

        if is_allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS):
            modality = "image"
            b64_data = base64.b64encode(file_bytes).decode("utf-8")
            content_type = file.content_type or "image/jpeg"
            image_b64 = f"data:{content_type};base64,{b64_data}"
        elif is_allowed_file(filename, ALLOWED_DOCUMENT_EXTENSIONS):
            try:
                extracted_file_text = DocumentService.extract_text_from_bytes(file_bytes, filename)
            except Exception as e:
                logger.warning(f"Could not extract text from attached file: {e}")

    full_message = message
    if extracted_file_text:
        full_message += f"\n\n[Attached Document '{file.filename}' Content]:\n{extracted_file_text[:3000]}"

    chat_req = ChatRequest(
        message=full_message or "Analyze this input.",
        conversation_id=conversation_id,
        modality=modality,
        enable_web_search=enable_web_search,
        enable_rag=enable_rag,
        is_emotional_mode=is_emotional_mode,
        generate_audio_tts=generate_audio_tts,
        image_base64=image_b64
    )

    return handle_chat(request=chat_req, db=db)
