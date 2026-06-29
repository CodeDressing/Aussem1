# ============================================================
# AUSSEM1
# PHASE 1.00 PART 13
# ENTERPRISE WEB ROUTES
# FILE: app/web/routes.py
# PURPOSE:
# Expose HTTP routes for the Aussem1 chatbot foundation.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# FOUNDATION ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel

from app.chatbot.chat_engine import ChatEngine
from app.chatbot.chat_engine import ChatRequest


# ============================================================
# SECTION 02 - ROUTER CONFIGURATION
# ============================================================

router = APIRouter()

ROUTES_VERSION = "0.1.0"

ROUTES_PHASE = "PHASE 1.00 PART 13"


# ============================================================
# SECTION 03 - CHATBOT ENGINE INSTANCE
# ============================================================

chat_engine = ChatEngine()


# ============================================================
# SECTION 04 - REQUEST MODELS
# ============================================================

class ChatRequestBody(BaseModel):
    """
    HTTP request body for chatbot messages.
    """

    message: str

    session_id: str | None = None

    property_address: str | None = None

    user_id: str | None = None


# ============================================================
# SECTION 05 - ROUTE HEALTH CHECK
# ============================================================

@router.get("/web/health")
def web_health() -> dict:
    """
    Verify that the Aussem1 web routing layer is active.
    """

    return {
        "module": "web",
        "status": "ok",
        "version": ROUTES_VERSION,
        "phase": ROUTES_PHASE,
    }


# ============================================================
# SECTION 06 - CHAT HEALTH CHECK
# ============================================================

@router.get("/chat/health")
def chat_health() -> dict:
    """
    Verify that the chatbot HTTP layer is active.
    """

    return {
        "module": "chatbot",
        "status": "ok",
        "engine": "ChatEngine",
        "version": ROUTES_VERSION,
        "phase": ROUTES_PHASE,
    }


# ============================================================
# SECTION 07 - CHAT ENDPOINT
# ============================================================

@router.post("/chat")
def chat(
    request_body: ChatRequestBody,
) -> dict:
    """
    Process a chatbot request.

    This route is the first public interface for the Aussem1
    intelligence layer.
    """

    chat_request = ChatRequest(
        message=request_body.message,
        session_id=request_body.session_id,
        property_address=request_body.property_address,
        user_id=request_body.user_id,
    )

    response = chat_engine.respond(
        request=chat_request,
    )

    return asdict(response)


# ============================================================
# SECTION 08 - TRAINING STATUS ENDPOINT
# ============================================================

@router.get("/chat/training-status")
def training_status() -> dict:
    """
    Return early chatbot training data status.
    """

    return {
        "module": "training_logger",
        "total_interactions": chat_engine.training_logger.total_interactions(),
        "failed_interactions": chat_engine.training_logger.failed_interactions(),
        "unanswered_questions": chat_engine.training_logger.unanswered_questions(),
        "status": "active",
    }


# ============================================================
# SECTION 09 - MEMORY STATUS ENDPOINT
# ============================================================

@router.get("/chat/memory-status")
def memory_status() -> dict:
    """
    Return early chatbot memory status.
    """

    return {
        "module": "memory_store",
        "total_messages": chat_engine.memory_store.total_messages(),
        "total_sessions": chat_engine.memory_store.total_sessions(),
        "status": "active",
    }


# ============================================================
# SECTION 10 - FUTURE EXPANSION NOTES
# ============================================================
#
# Planned future routes:
#
# POST /chat/feedback
# GET  /chat/history/{session_id}
# POST /properties/lookup
# POST /properties/value
# POST /properties/status
# POST /properties/compare
# GET  /training/export
# GET  /training/review-queue
#
# ============================================================


# ============================================================
# END OF FILE
# ============================================================