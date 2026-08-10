"""Retrieval-Augmented Generation orchestration for the onboarding assistant.

The flow, per the project design:
  1. Retrieve  — find policy chunks relevant to the question (Azure AI Search
     hybrid search in prod; keyword search over the local corpus otherwise).
  2. Augment   — combine retrieved chunks with the asking employee's structured
     context (role, department, task progress) pulled from the repository.
  3. Generate  — send the augmented prompt to Azure OpenAI and stream the answer
     (a deterministic template answer is used when OpenAI isn't configured).

Answers are grounded only in retrieved context; the assistant is instructed to
say when it doesn't know rather than invent policy.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from app.core.config import get_settings
from app.db.repository import NotFoundError, Repository
from app.schemas.chat import ChatRequest, ChatResponse, Citation
from app.services import knowledge_base
from app.services.knowledge_base import Chunk

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are the Employee Onboarding Assistant. Answer new hires' questions "
    "about company policies and their onboarding using ONLY the provided policy "
    "context and employee context. If the answer is not in the context, say you "
    "don't have that information and suggest contacting HR. Be concise and "
    "friendly. Cite the policy document titles you used."
)


# --- Retrieval ------------------------------------------------------------
def _retrieve(query: str, top_k: int = 3) -> list[Chunk]:
    settings = get_settings()
    if settings.search_configured:
        try:
            return _search_retrieve(query, top_k)
        except Exception:  # pragma: no cover - fall back if Search is unavailable
            logger.exception("Azure AI Search retrieval failed; falling back to keyword")
    return knowledge_base.keyword_search(query, top_k)


def _search_retrieve(query: str, top_k: int) -> list[Chunk]:
    """Hybrid (keyword + vector) retrieval from Azure AI Search."""
    from azure.search.documents import SearchClient

    from app.core.azure_clients import get_credential

    settings = get_settings()
    client = SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index,
        credential=get_credential(),
    )
    results = client.search(search_text=query, top=top_k)
    chunks: list[Chunk] = []
    for doc in results:
        chunks.append(
            Chunk(
                doc_title=doc.get("title", "Policy"),
                source=doc.get("source", ""),
                heading=doc.get("heading", ""),
                text=doc.get("content", ""),
            )
        )
    return chunks


# --- Augmentation ---------------------------------------------------------
def _employee_context(repo: Repository, employee_id: int) -> str:
    """Build a compact, structured context block about the asking employee."""
    try:
        employee = repo.get_employee(employee_id)
        checklist = repo.get_checklist(employee_id)
    except NotFoundError:
        return "Employee context: unknown employee."

    total = len(checklist)
    completed = sum(1 for t in checklist if t["status"] == "Completed")
    pending = [t["title"] for t in checklist if t["status"] != "Completed"][:5]

    lines = [
        f"Name: {employee['first_name']} {employee['last_name']}",
        f"Role: {employee.get('job_title') or 'unknown'}",
        f"Department: {employee.get('department') or 'unknown'}",
        f"Region: {employee.get('region') or 'unknown'}",
        f"Onboarding progress: {completed}/{total} tasks complete",
    ]
    if pending:
        lines.append("Next pending tasks: " + "; ".join(pending))
    return "\n".join(lines)


def _format_context(chunks: list[Chunk]) -> str:
    if not chunks:
        return "(no relevant policy documents found)"
    blocks = [
        f"[{i + 1}] {c.doc_title} — {c.heading}\n{c.text}" for i, c in enumerate(chunks)
    ]
    return "\n\n".join(blocks)


def _citations(chunks: list[Chunk]) -> list[Citation]:
    seen: set[str] = set()
    citations: list[Citation] = []
    for chunk in chunks:
        if chunk.doc_title in seen:
            continue
        seen.add(chunk.doc_title)
        snippet = chunk.text.strip().replace("\n", " ")
        citations.append(
            Citation(
                title=chunk.doc_title,
                source=chunk.source,
                snippet=snippet[:200] + ("…" if len(snippet) > 200 else ""),
            )
        )
    return citations


def _build_messages(request: ChatRequest, repo: Repository, chunks: list[Chunk]) -> list[dict]:
    context = _format_context(chunks)
    employee_ctx = _employee_context(repo, request.employee_id)
    system = (
        f"{SYSTEM_PROMPT}\n\n"
        f"=== Employee context ===\n{employee_ctx}\n\n"
        f"=== Policy context ===\n{context}"
    )
    messages = [{"role": "system", "content": system}]
    messages += [{"role": m.role.value, "content": m.content} for m in request.history]
    messages.append({"role": "user", "content": request.message})
    return messages


# --- Generation -----------------------------------------------------------
def _stub_answer(request: ChatRequest, chunks: list[Chunk]) -> str:
    """Deterministic grounded answer used when Azure OpenAI isn't configured."""
    if not chunks:
        return (
            "I don't have information about that in the onboarding policies I can "
            "see. Please reach out to HR and they'll be able to help."
        )
    lead = {
        "leave": "Here's what our leave policy says:",
        "document": "Here are the documents you need to submit:",
        "handbook": "Here's a summary from the company handbook:",
    }
    lower = request.message.lower()
    intro = next((v for k, v in lead.items() if k in lower), "Here's what I found:")

    parts = [intro, ""]
    for chunk in chunks:
        summary = chunk.text.strip().split("\n\n")[0].replace("\n", " ")
        parts.append(f"• **{chunk.doc_title} — {chunk.heading}**: {summary}")
    parts.append("")
    parts.append(
        "Sources: " + ", ".join(sorted({c.doc_title for c in chunks})) + "."
    )
    return "\n".join(parts)


def answer(request: ChatRequest, repo: Repository) -> ChatResponse:
    """Produce a single (non-streaming) grounded answer."""
    chunks = _retrieve(request.message)
    settings = get_settings()

    if settings.openai_configured:
        text = _openai_complete(_build_messages(request, repo, chunks))
    else:
        text = _stub_answer(request, chunks)

    repo.save_message(request.employee_id, "user", request.message)
    repo.save_message(request.employee_id, "assistant", text)
    return ChatResponse(answer=text, citations=_citations(chunks))


def _openai_complete(messages: list[dict]) -> str:
    from openai import AzureOpenAI

    from app.core.azure_clients import get_credential

    settings = get_settings()
    token_provider = _bearer_token_provider(get_credential())
    client = AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        azure_ad_token_provider=token_provider,
    )
    completion = client.chat.completions.create(
        model=settings.azure_openai_chat_deployment,
        messages=messages,
        temperature=0.2,
    )
    return completion.choices[0].message.content or ""


async def stream_answer(request: ChatRequest, repo: Repository) -> AsyncIterator[str]:
    """Yield Server-Sent Events with the answer, chunk by chunk."""
    chunks = _retrieve(request.message)
    settings = get_settings()
    repo.save_message(request.employee_id, "user", request.message)

    collected: list[str] = []
    if settings.openai_configured:
        for piece in _openai_stream(_build_messages(request, repo, chunks)):
            collected.append(piece)
            yield _sse({"delta": piece})
    else:
        # Stream the stub answer word-by-word so the UI can render progressively.
        text = _stub_answer(request, chunks)
        for word in text.split(" "):
            collected.append(word + " ")
            yield _sse({"delta": word + " "})

    repo.save_message(request.employee_id, "assistant", "".join(collected))
    citations = [c.model_dump() for c in _citations(chunks)]
    yield _sse({"citations": citations})
    yield "event: done\ndata: {}\n\n"


def _openai_stream(messages: list[dict]):
    from openai import AzureOpenAI

    from app.core.azure_clients import get_credential

    settings = get_settings()
    client = AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        azure_ad_token_provider=_bearer_token_provider(get_credential()),
    )
    stream = client.chat.completions.create(
        model=settings.azure_openai_chat_deployment,
        messages=messages,
        temperature=0.2,
        stream=True,
    )
    for event in stream:
        if event.choices and event.choices[0].delta.content:
            yield event.choices[0].delta.content


def _bearer_token_provider(credential):
    from azure.identity import get_bearer_token_provider

    return get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )


def _sse(data: dict) -> str:
    import json

    return f"data: {json.dumps(data)}\n\n"
