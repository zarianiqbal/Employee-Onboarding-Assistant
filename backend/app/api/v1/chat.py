"""AI onboarding assistant chat endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import repository
from app.db.repository import Repository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import rag_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, repo: Repository = Depends(repository)) -> ChatResponse:
    """Answer an onboarding question (non-streaming) with grounded citations."""
    return rag_service.answer(payload, repo)


@router.post("/stream")
async def chat_stream(payload: ChatRequest, repo: Repository = Depends(repository)):
    """Stream the answer as Server-Sent Events for real-time UI rendering."""
    return StreamingResponse(
        rag_service.stream_answer(payload, repo),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
