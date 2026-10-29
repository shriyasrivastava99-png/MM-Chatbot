import uuid
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class ChatSourceCitation(BaseModel):
    """
    Source citation indicating whether an answer was derived
    from an uploaded document or live web search.
    """
    source_type: Literal["document", "web"]
    title: str
    url_or_id: Optional[str] = None
    snippet: Optional[str] = None


class MessageResponse(BaseModel):
    """
    Message container matching frontend expectations.
    """
    content: str
    role: str = "assistant"
    modality: str = "text"
    audio_path: Optional[str] = None
    image_path: Optional[str] = None
    sources: List[ChatSourceCitation] = []


class ChatRequest(BaseModel):
    """
    Incoming chat message request schema.
    """
    message: str = Field(..., description="User message text or prompt")
    conversation_id: Optional[uuid.UUID] = Field(None, description="Existing conversation UUID")
    modality: Literal["text", "image", "audio", "document"] = Field("text", description="Input modality")
    enable_web_search: bool = Field(False, description="Trigger real-time web search for recent or external knowledge")
    enable_rag: bool = Field(True, description="Retrieve answers from uploaded documents in database")
    is_emotional_mode: bool = Field(False, description="Activate dedicated empathetic support mode")
    generate_audio_tts: bool = Field(False, description="Synthesize output to audio speech via TTS")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image string if modality is image")


class ChatResponse(BaseModel):
    """
    Outgoing chatbot response schema supporting both flat and nested message formats.
    """
    conversation_id: uuid.UUID
    response_text: str
    message: Optional[MessageResponse] = None
    modality: str = "text"
    audio_path: Optional[str] = None
    image_path: Optional[str] = None
    sources: List[ChatSourceCitation] = []
    emotional_safety_flag: bool = False
    crisis_help_info: Optional[Dict[str, Any]] = None
