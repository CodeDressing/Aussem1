# ============================================================
# AUSSEM1
# PHASE 1.00 PART 9.03
# ENTERPRISE WEB EXPERIENCE AND API CONTROL ROUTER
# FILE: app/web/routes.py
# PURPOSE:
# Serve the Aussem1 visual intelligence dashboard and expose the
# API control layer for chatbot, memory, training, diagnostics,
# prompt validation, and future property intelligence systems.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# ENTERPRISE VISUAL APPLICATION ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

from dataclasses import asdict
from dataclasses import is_dataclass
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pydantic import Field

from app.chatbot.chat_engine import ChatEngine
from app.chatbot.chat_engine import ChatRequest

try:
    from app.chatbot.prompts import validate_prompts
except Exception:
    validate_prompts = None


# ============================================================
# SECTION 02 - ROUTER METADATA
# ============================================================

ROUTES_NAME = "Aussem1 Enterprise Web Experience Router"

ROUTES_VERSION = "0.4.0"

ROUTES_PHASE = "PHASE 1.00 PART 9.03"

ROUTES_STATUS = "enterprise_visual_application_active"

ROUTES_DESCRIPTION = (
    "Enterprise routing layer for Aussem1 dashboard, chatbot API, "
    "training intelligence, memory intelligence, diagnostics, and "
    "future property intelligence workflows."
)


# ============================================================
# SECTION 03 - PATH CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

APP_DIRECTORY = PROJECT_ROOT / "app"

TEMPLATE_DIRECTORY = APP_DIRECTORY / "templates"

DATA_DIRECTORY = APP_DIRECTORY / "data"


# ============================================================
# SECTION 04 - TEMPLATE ENGINE CONFIGURATION
# ============================================================

templates = Jinja2Templates(
    directory=str(TEMPLATE_DIRECTORY),
)


# ============================================================
# SECTION 05 - ROUTER INSTANCE
# ============================================================

router = APIRouter()


# ============================================================
# SECTION 06 - CHATBOT ENGINE INSTANCE
# ============================================================

chat_engine = ChatEngine()


# ============================================================
# SECTION 07 - REQUEST MODELS
# ============================================================

class ChatRequestBody(BaseModel):
    """
    Request body for live chatbot messages.
    """

    message: str = Field(
        ...,
        min_length=1,
        description="User message sent to Aussem1.",
    )

    session_id: str | None = Field(
        default=None,
        description="Existing chat session identifier.",
    )

    property_address: str | None = Field(
        default=None,
        description="Optional property address context.",
    )

    user_id: str | None = Field(
        default=None,
        description="Optional user identifier.",
    )


class FeedbackRequestBody(BaseModel):
    """
    Request body for user feedback on chatbot output.
    """

    record_id: str

    feedback: str

    corrected_answer: str | None = None


class MemorySearchRequestBody(BaseModel):
    """
    Request body for memory search.
    """

    query: str

    limit: int = 20


class PropertyPreviewRequestBody(BaseModel):
    """
    Early property intelligence preview body.

    This does not perform live public-record lookup yet.
    It prepares the route contract for future property engines.
    """

    property_address: str

    question: str | None = None


# ============================================================
# SECTION 08 - RESPONSE ENVELOPE UTILITIES
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(UTC).isoformat()


def request_id() -> str:
    """
    Create request trace identifier.
    """

    return f"aussem1-request-{uuid4()}"


def serialize_response(value: Any) -> Any:
    """
    Convert dataclass objects to dictionaries.
    """

    if is_dataclass(value):
        return asdict(value)

    return value


def enterprise_response(
    *,
    module: str,
    status: str,
    data: Any,
    message: str | None = None,
) -> dict:
    """
    Standard API response envelope.
    """

    return {
        "platform": "Aussem1",
        "module": module,
        "status": status,
        "message": message,
        "data": data,
        "request_id": request_id(),
        "timestamp": utc_now(),
        "routes": {
            "name": ROUTES_NAME,
            "version": ROUTES_VERSION,
            "phase": ROUTES_PHASE,
            "status": ROUTES_STATUS,
        },
    }


def safe_call(
    callable_object: Any,
    fallback: Any,
) -> Any:
    """
    Call evolving subsystem methods safely.
    """

    try:
        return callable_object()
    except Exception as error:
        return {
            "status": "unavailable",
            "error": str(error),
            "fallback": fallback,
        }


# ============================================================
# SECTION 09 - VISUAL ROUTES
# ============================================================

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
) -> HTMLResponse:
    """
    Render the Aussem1 live intelligence dashboard.
    """

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "platform_name": "Aussem1",
            "routes_name": ROUTES_NAME,
            "routes_version": ROUTES_VERSION,
            "routes_phase": ROUTES_PHASE,
            "routes_status": ROUTES_STATUS,
            "generated_at": utc_now(),
        },
    )


# ============================================================
# SECTION 10 - WEB HEALTH ENDPOINTS
# ============================================================

@router.get("/web/health")
def web_health() -> dict:
    """
    Web routing health check.
    """

    return enterprise_response(
        module="web_routes",
        status="ok",
        message="Aussem1 web routing layer is active.",
        data={
            "routes_name": ROUTES_NAME,
            "version": ROUTES_VERSION,
            "phase": ROUTES_PHASE,
            "template_directory": str(TEMPLATE_DIRECTORY),
            "template_directory_exists": TEMPLATE_DIRECTORY.exists(),
            "dashboard_template_exists": (
                TEMPLATE_DIRECTORY / "dashboard.html"
            ).exists(),
        },
    )


@router.get("/web/readiness")
def web_readiness() -> dict:
    """
    Readiness check for dashboard operation.
    """

    checks = {
        "template_directory": TEMPLATE_DIRECTORY.exists(),
        "dashboard_template": (TEMPLATE_DIRECTORY / "dashboard.html").exists(),
        "data_directory": DATA_DIRECTORY.exists(),
        "chat_engine": chat_engine is not None,
        "memory_store": hasattr(chat_engine, "memory_store"),
        "training_logger": hasattr(chat_engine, "training_logger"),
    }

    ready = all(checks.values())

    return enterprise_response(
        module="web_readiness",
        status="ready" if ready else "not_ready",
        message="Dashboard readiness inspection complete.",
        data={
            "ready": ready,
            "checks": checks,
        },
    )


# ============================================================
# SECTION 11 - DASHBOARD BOOTSTRAP API
# ============================================================

@router.get("/api/dashboard/bootstrap")
def dashboard_bootstrap() -> dict:
    """
    Return initial dashboard configuration.
    """

    return enterprise_response(
        module="dashboard_bootstrap",
        status="active",
        message="Dashboard bootstrap data loaded.",
        data={
            "dashboard": {
                "name": "Aussem1 Intelligence Dashboard",
                "status": "active",
                "template": "app/templates/dashboard.html",
                "purpose": (
                    "Visualize the live chatbot, memory system, training "
                    "logger, prompt architecture, and property intelligence "
                    "foundation."
                ),
            },
            "active_modules": [
                "FastAPI Runtime",
                "Dashboard Template",
                "Chat Engine",
                "Memory Store",
                "Training Logger",
                "Prompt Registry",
                "Property Knowledge Foundation",
                "Render Deployment",
            ],
            "planned_modules": [
                "Dashboard CSS Split",
                "Dashboard JavaScript Split",
                "Property Lookup Engine",
                "Public Records Engine",
                "Comparable Analysis Engine",
                "Valuation Engine",
                "Learning Engine",
                "PostgreSQL Persistence",
                "Review Dashboard",
            ],
        },
    )


# ============================================================
# SECTION 12 - DASHBOARD LIVE STATUS API
# ============================================================

@router.get("/api/dashboard/status")
def dashboard_status() -> dict:
    """
    Return live platform status for visual dashboard.
    """

    training_summary = safe_call(
        chat_engine.training_logger.training_summary,
        fallback={},
    )

    memory_health = safe_call(
        chat_engine.memory_store.memory_health_report,
        fallback={},
    )

    engine_status = safe_call(
        chat_engine.status,
        fallback={},
    )

    prompt_status = (
        safe_call(validate_prompts, fallback={})
        if validate_prompts
        else {
            "status": "unavailable",
            "reason": "validate_prompts not importable",
        }
    )

    return enterprise_response(
        module="dashboard_status",
        status="online",
        message="Live Aussem1 dashboard status loaded.",
        data={
            "systems": {
                "web_routes": {
                    "status": "active",
                    "version": ROUTES_VERSION,
                    "phase": ROUTES_PHASE,
                    "dashboard": "active",
                },
                "chat_engine": engine_status,
                "training_logger": training_summary,
                "memory_store": memory_health,
                "prompt_registry": prompt_status,
            },
            "visual_layers": {
                "template": "active",
                "css": "embedded_or_pending_static_split",
                "javascript": "embedded_or_pending_static_split",
            },
        },
    )


# ============================================================
# SECTION 13 - CHAT HEALTH ENDPOINT
# ============================================================

@router.get("/chat/health")
def chat_health() -> dict:
    """
    Verify chatbot route availability.
    """

    return enterprise_response(
        module="chatbot",
        status="ok",
        message="Chatbot HTTP layer is active.",
        data={
            "engine": "ChatEngine",
            "chat_endpoint": "/chat",
            "supports_session_id": True,
            "supports_property_address": True,
            "supports_training_logging": True,
            "supports_memory_storage": True,
        },
    )


# ============================================================
# SECTION 14 - CHAT ENDPOINT
# ============================================================

@router.post("/chat")
def chat(
    request_body: ChatRequestBody,
) -> dict:
    """
    Process a chatbot request through Aussem1.
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

    serialized = serialize_response(response)

    return serialized


# ============================================================
# SECTION 15 - CHAT TRACE ENDPOINT
# ============================================================

@router.post("/chat/trace")
def chat_trace(
    request_body: ChatRequestBody,
) -> dict:
    """
    Process a chat request and return an enterprise diagnostic trace.
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

    serialized = serialize_response(response)

    return enterprise_response(
        module="chat_trace",
        status="complete",
        message="Chat request processed with diagnostic trace.",
        data={
            "request": request_body.model_dump(),
            "response": serialized,
            "trace": {
                "memory_enabled": True,
                "training_enabled": True,
                "property_context_enabled": True,
                "confidence_enabled": "confidence" in serialized,
                "intent_enabled": "intent" in serialized,
            },
        },
    )


# ============================================================
# SECTION 16 - TRAINING STATUS ENDPOINTS
# ============================================================

@router.get("/chat/training-status")
def training_status() -> dict:
    """
    Return chatbot training data status.
    """

    summary = safe_call(
        chat_engine.training_logger.training_summary,
        fallback={},
    )

    return enterprise_response(
        module="training_logger",
        status="active",
        message="Training logger status loaded.",
        data={
            "summary": summary,
            "total_interactions": chat_engine.training_logger.total_interactions(),
            "failed_interactions": chat_engine.training_logger.failed_interactions(),
            "unanswered_questions": chat_engine.training_logger.unanswered_questions(),
        },
    )


@router.get("/chat/review-queue")
def training_review_queue() -> dict:
    """
    Return training review queue.
    """

    queue = safe_call(
        lambda: chat_engine.training_logger.review_queue(limit=25),
        fallback=[],
    )

    return enterprise_response(
        module="training_review_queue",
        status="active",
        message="Training review queue loaded.",
        data={
            "items": queue,
            "count": len(queue) if isinstance(queue, list) else 0,
        },
    )


@router.get("/chat/training-export")
def training_export() -> dict:
    """
    Export current training dataset preview.
    """

    dataset = safe_call(
        chat_engine.training_logger.export_training_dataset,
        fallback=[],
    )

    return enterprise_response(
        module="training_export",
        status="active",
        message="Training dataset export generated.",
        data={
            "dataset": dataset,
            "count": len(dataset) if isinstance(dataset, list) else 0,
        },
    )


# ============================================================
# SECTION 17 - MEMORY ENDPOINTS
# ============================================================

@router.get("/chat/memory-status")
def memory_status() -> dict:
    """
    Return chatbot memory status.
    """

    memory_health = safe_call(
        chat_engine.memory_store.memory_health_report,
        fallback={},
    )

    return enterprise_response(
        module="memory_store",
        status="active",
        message="Memory store status loaded.",
        data={
            "health": memory_health,
            "total_messages": chat_engine.memory_store.total_messages(),
            "total_sessions": chat_engine.memory_store.total_sessions(),
        },
    )


@router.get("/chat/memory-search")
def memory_search(
    query: str,
    limit: int = 20,
) -> dict:
    """
    Search chatbot memory by query.
    """

    results = safe_call(
        lambda: chat_engine.memory_store.search_memory(
            query=query,
            limit=limit,
        ),
        fallback=[],
    )

    return enterprise_response(
        module="memory_search",
        status="active",
        message="Memory search complete.",
        data={
            "query": query,
            "limit": limit,
            "results": results,
            "count": len(results) if isinstance(results, list) else 0,
        },
    )


@router.post("/chat/memory-search")
def memory_search_post(
    request_body: MemorySearchRequestBody,
) -> dict:
    """
    POST variant of memory search.
    """

    return memory_search(
        query=request_body.query,
        limit=request_body.limit,
    )


# ============================================================
# SECTION 18 - PROMPT STATUS ENDPOINT
# ============================================================

@router.get("/chat/prompt-status")
def prompt_status() -> dict:
    """
    Return prompt registry validation status.
    """

    status_payload = (
        safe_call(validate_prompts, fallback={})
        if validate_prompts
        else {
            "status": "unavailable",
            "reason": "validate_prompts could not be imported",
        }
    )

    return enterprise_response(
        module="prompt_registry",
        status="active" if validate_prompts else "unavailable",
        message="Prompt registry status loaded.",
        data=status_payload,
    )


# ============================================================
# SECTION 19 - PROPERTY INTELLIGENCE PREVIEW
# ============================================================

@router.post("/properties/preview")
def property_preview(
    request_body: PropertyPreviewRequestBody,
) -> dict:
    """
    Preview the future property intelligence flow.

    This does not claim live public-record, MLS, or valuation access.
    It demonstrates the future routing contract.
    """

    return enterprise_response(
        module="property_intelligence_preview",
        status="planned",
        message=(
            "Property intelligence preview generated. Live public-record, "
            "MLS, valuation, and comparable engines are planned but not "
            "connected in this phase."
        ),
        data={
            "property_address": request_body.property_address,
            "question": request_body.question,
            "future_pipeline": [
                "Normalize property address",
                "Identify municipality and county",
                "Check connected public-record sources",
                "Check listing/status sources",
                "Build property profile",
                "Run comparable analysis",
                "Run valuation estimate",
                "Return confidence-scored explanation",
            ],
            "current_capabilities": [
                "Chatbot reasoning",
                "Memory logging",
                "Training logging",
                "Missing data detection",
                "Dashboard visualization",
            ],
            "not_yet_connected": [
                "MLS/RESO",
                "County assessor",
                "County recorder",
                "Parcel GIS",
                "Comparable sales database",
                "Automated valuation model",
            ],
        },
    )


# ============================================================
# SECTION 20 - ENTERPRISE ROUTE REGISTRY
# ============================================================

@router.get("/web/route-registry")
def web_route_registry() -> dict:
    """
    Return enterprise route registry for this web module.
    """

    return enterprise_response(
        module="web_route_registry",
        status="active",
        message="Enterprise web route registry loaded.",
        data={
            "visual_routes": [
                {
                    "path": "/dashboard",
                    "method": "GET",
                    "purpose": "Live Aussem1 intelligence dashboard.",
                    "template": "app/templates/dashboard.html",
                },
            ],
            "dashboard_api_routes": [
                "/api/dashboard/bootstrap",
                "/api/dashboard/status",
            ],
            "chat_routes": [
                "/chat",
                "/chat/trace",
                "/chat/health",
                "/chat/training-status",
                "/chat/review-queue",
                "/chat/training-export",
                "/chat/memory-status",
                "/chat/memory-search",
                "/chat/prompt-status",
            ],
            "property_routes": [
                "/properties/preview",
            ],
            "governance": {
                "rule_1": "Routes should stay thin and delegate intelligence to service modules.",
                "rule_2": "Visual structure belongs in templates.",
                "rule_3": "CSS belongs in static stylesheets after the split.",
                "rule_4": "JavaScript belongs in static scripts after the split.",
                "rule_5": "AI endpoints must expose uncertainty and source status.",
            },
        },
    )


# ============================================================
# SECTION 21 - ENTERPRISE DIAGNOSTICS
# ============================================================

@router.get("/web/diagnostics")
def web_diagnostics() -> dict:
    """
    Return complete diagnostic state for early deployment debugging.
    """

    files = {
        "project_root": str(PROJECT_ROOT),
        "app_directory": str(APP_DIRECTORY),
        "template_directory": str(TEMPLATE_DIRECTORY),
        "data_directory": str(DATA_DIRECTORY),
        "dashboard_template": str(TEMPLATE_DIRECTORY / "dashboard.html"),
    }

    existence = {
        "project_root_exists": PROJECT_ROOT.exists(),
        "app_directory_exists": APP_DIRECTORY.exists(),
        "template_directory_exists": TEMPLATE_DIRECTORY.exists(),
        "data_directory_exists": DATA_DIRECTORY.exists(),
        "dashboard_template_exists": (
            TEMPLATE_DIRECTORY / "dashboard.html"
        ).exists(),
    }

    return enterprise_response(
        module="web_diagnostics",
        status="active",
        message="Web diagnostics loaded.",
        data={
            "paths": files,
            "existence": existence,
            "routes_version": ROUTES_VERSION,
            "routes_phase": ROUTES_PHASE,
            "routes_status": ROUTES_STATUS,
        },
    )


# ============================================================
# SECTION 22 - FUTURE EXPANSION NOTES
# ============================================================

#
# Immediate next files:
#
# app/static/css/dashboard.css
# app/static/js/dashboard.js
#
# Required future main.py upgrade:
#
# Mount static files:
#
# from fastapi.staticfiles import StaticFiles
#
# application.mount(
#     "/static",
#     StaticFiles(directory="app/static"),
#     name="static",
# )
#
# This router is now responsible for:
#
# • template rendering
# • dashboard bootstrap APIs
# • dashboard status APIs
# • chatbot API
# • training API
# • memory API
# • prompt validation API
# • property preview API
# • route registry
# • diagnostics
#
# It is intentionally not responsible for:
#
# • CSS implementation
# • JavaScript behavior
# • property valuation logic
# • public-record lookup logic
# • ML model training
# • database persistence
#
# ============================================================


# ============================================================
# END OF FILE
# ============================================================