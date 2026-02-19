from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from services import llm, memory
import crud
import shutil
import os
import uuid
from typing import List, Optional

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

# Ensure upload directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    session_id: int

class SessionCreate(BaseModel):
    title: str

class SessionResponse(BaseModel):
    id: int
    title: str
    updated_at: str

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: str
    attachment_url: Optional[str] = None

@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    sessions = crud.get_chat_sessions(db, user_id=1)
    return [{"id": s.id, "title": s.title, "updated_at": s.updated_at.isoformat()} for s in sessions]

@router.delete("/sessions/all")
def clear_all_history(db: Session = Depends(get_db)):
    """Clear all chat history and vector memory for the user."""
    user_id = 1
    
    # Clear SQL chat history
    sessions_deleted = crud.clear_all_chat_history(db, user_id)
    
    # Clear vector memory
    memory.MemoryService.clear_all_memory()
    
    return {
        "status": "success", 
        "message": f"Cleared {sessions_deleted} chat sessions and all vector memory.",
        "sessions_deleted": sessions_deleted
    }

@router.post("/sessions", response_model=SessionResponse)
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    new_session = crud.create_chat_session(db, user_id=1, title=session.title)
    return {"id": new_session.id, "title": new_session.title, "updated_at": new_session.updated_at.isoformat()}

@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_session_messages(session_id: int, db: Session = Depends(get_db)):
    messages = crud.get_chat_messages(db, session_id)
    return [
        {
            "id": m.id, 
            "role": m.role, 
            "content": m.content, 
            "timestamp": m.timestamp.isoformat(),
            "attachment_url": m.attachment_url
        } 
        for m in messages
    ]

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_ext = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"url": f"/uploads/{file_name}", "filename": file.filename}

from fastapi.responses import StreamingResponse

@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Stream a chat message response via the Ultron LLM Orchestrator.
    """
    try:
        user_id = 1
        # Note: Session management is handled inside process_user_message_streaming for now
        # to keep it consistent with the non-streaming version's logic flow.
        
        return StreamingResponse(
            llm.process_user_message_streaming(request.message, db, user_id=user_id, session_id=request.session_id),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Process a chat message via the Ultron LLM Orchestrator.
    """
    try:
        user_id = 1
        session_id = request.session_id
        
        # Create session if not exists
        if not session_id:
            session = crud.create_chat_session(db, user_id, title=request.message[:30] + "...")
            session_id = session.id
        
        # Store User Message
        crud.add_chat_message(db, session_id, "user", request.message)
        
        # Process with LLM
        # We need to pass session history to LLM ideally, but for now we stick to the existing logic
        # which uses Vector DB for context. 
        # TODO: Pass recent session messages to LLM context window.
        reply = await llm.process_user_message(request.message, db, user_id=user_id)
        
        # Store Assistant Message
        crud.add_chat_message(db, session_id, "assistant", reply)
        
        return ChatResponse(response=reply, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
