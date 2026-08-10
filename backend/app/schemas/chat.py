"""Pydantic schemas for the AI onboarding assistant chat."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ChatRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class ChatMessage(BaseModel):
    role: ChatRole
    content: str


class ChatRequest(BaseModel):
    """A user turn plus optional prior history and the asking employee's id."""

    employee_id: int
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list)


class Citation(BaseModel):
    """A source document chunk referenced in the answer."""

    title: str
    source: str
    snippet: str


class ChatResponse(BaseModel):
    """Non-streaming chat response (streaming uses text/event-stream)."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
