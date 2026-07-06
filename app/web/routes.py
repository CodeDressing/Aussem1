# ============================================================
# AUSSEM1
# PHASE 1.00 PART 9.09
# ENTERPRISE WEB ROUTER STABILIZATION UPGRADE
# FILE: app/web/routes.py
# PURPOSE:
# Stable production-ready web routing layer for Aussem1 dashboard,
# chatbot API, dashboard metrics, memory inspection, training
# intelligence, prompt validation, property preview contracts,
# and deployment diagnostics.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# ENTERPRISE DASHBOARD ROUTER ACTIVE
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

ROUTES_NAME = "Aussem1 Enterprise Web Router"

ROUTES_VERSION = "0.5.0"

ROUTES_PHASE = "PHASE 1.00 PART 9.09"

ROUTES_STATUS = "enterprise_dashboard_router_active"

ROUTES_DESCRIPTION = (
    "Stable routing layer for dashboard rendering, chatbot API, "
    "memory analytics, training intelligence, prompt validation, "
    "property preview contracts, and deployment diagnostics."
)


# ============================================================
# SECTION 03 - PATH CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

APP_DIRECTORY = PROJECT_ROOT / "app"

TEMPLATE_DIRECTORY = APP_DIRECTORY / "templates"

STATIC_DIRECTORY = APP_DIRECTORY / "static"

STATIC_CSS_DIRECTORY = STATIC_DIRECTORY / "css"

STATIC_JS_DIRECTORY = STATIC_DIRECTORY / "js"

DATA_DIRECTORY = APP_DIRECTORY / "data"

DASHBOARD_TEMPLATE_FILE = TEMPLATE_DIRECTORY / "dashboard.html"

DASHBOARD_CSS_FILE = STATIC_CSS_DIRECTORY / "dashboard.css"

DASHBOARD_JS_FILE = STATIC_JS_DIRECTORY / "dashboard.js"


# ============================================================
# SECTION 04 - TEMPLATE CONFIGURATION
# ============================================================

templates = Jinja2Templates(
    directory=str(TEMPLATE_DIRECTORY),
)


# ============================================================
# SECTION 05 - ROUTER INSTANCE
# ============================================================

router = APIRouter()


# ============================================================
# SECTION 06 - ENGINE INSTANCE
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
    Request body for future user feedback capture.
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
    Early property intelligence preview request.

    This does not perform live public-record lookup yet.
    It defines the stable route contract for future property engines.
    """

    property_address: str

    question: str | None = None


# ============================================================
# SECTION 08 - UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(UTC).isoformat()


def request_id() -> str:
    """
    Create a request trace identifier.
    """

    return f"aussem1-request-{uuid4()}"


def serialize_response(value: Any) -> Any:
    """
    Convert dataclass responses to dictionaries.
    """

    if is_dataclass(value):
        return asdict(value)

    return value


def safe_call(
    callable_object: Any,
    fallback: Any,
) -> Any:
    """
    Safely call subsystem methods while modules evolve.
    """

    try:
        return callable_object()
    except Exception as error:
        return {
            "status": "unavailable",
            "error": str(error),
            "fallback": fallback,
        }


def enterprise_response(
    *,
    module: str,
    status: str,
    data: Any,
    message: str | None = None,
) -> dict[str, Any]:
    """
    Standard enterprise API response envelope.
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


def dashboard_status_payload() -> dict[str, Any]:
    """
    Build dashboard status payload in a JavaScript-compatible shape.

    Important:
    The dashboard template currently expects:
        data.systems.memory_store.health
        data.systems.training_logger
        data.systems.chat_engine

    Therefore this route returns systems at the top level, not only
    inside a nested enterprise envelope.
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
            "reason": "validate_prompts could not be imported",
        }
    )

    return {
        "platform": "Aussem1",
        "module": "dashboard_status",
        "status": "online",
        "phase": ROUTES_PHASE,
        "timestamp": utc_now(),
        "systems": {
            "web_routes": {
                "status": "active",
                "name": ROUTES_NAME,
                "version": ROUTES_VERSION,
                "phase": ROUTES_PHASE,
                "dashboard_template_exists": DASHBOARD_TEMPLATE_FILE.exists(),
                "dashboard_css_exists": DASHBOARD_CSS_FILE.exists(),
                "dashboard_js_exists": DASHBOARD_JS_FILE.exists(),
            },
            "chat_engine": engine_status,
            "training_logger": training_summary,
            "memory_store": {
                "status": "active",
                "health": memory_health,
            },
            "prompt_registry": prompt_status,
        },
        "visual_layers": {
            "template": {
                "path": str(DASHBOARD_TEMPLATE_FILE),
                "exists": DASHBOARD_TEMPLATE_FILE.exists(),
            },
            "css": {
                "path": str(DASHBOARD_CSS_FILE),
                "url": "/static/css/dashboard.css",
                "exists": DASHBOARD_CSS_FILE.exists(),
            },
            "javascript": {
                "path": str(DASHBOARD_JS_FILE),
                "url": "/static/js/dashboard.js",
                "exists": DASHBOARD_JS_FILE.exists(),
            },
        },
    }


# ============================================================
# SECTION 09 - VISUAL DASHBOARD ROUTES
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
            "dashboard_css_url": "/static/css/dashboard.css",
            "dashboard_js_url": "/static/js/dashboard.js",
        },
    )


# ============================================================
# SECTION 10 - WEB HEALTH AND READINESS
# ============================================================

@router.get("/web/health")
def web_health() -> dict[str, Any]:
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
            "dashboard_template_exists": DASHBOARD_TEMPLATE_FILE.exists(),
            "dashboard_css_exists": DASHBOARD_CSS_FILE.exists(),
            "dashboard_js_exists": DASHBOARD_JS_FILE.exists(),
        },
    )


@router.get("/web/readiness")
def web_readiness() -> dict[str, Any]:
    """
    Readiness check for dashboard operation.
    """

    checks = {
        "template_directory": TEMPLATE_DIRECTORY.exists(),
        "dashboard_template": DASHBOARD_TEMPLATE_FILE.exists(),
        "static_directory": STATIC_DIRECTORY.exists(),
        "dashboard_css": DASHBOARD_CSS_FILE.exists(),
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
# SECTION 11 - DASHBOARD APIS
# ============================================================

@router.get("/api/dashboard/bootstrap")
def dashboard_bootstrap() -> dict[str, Any]:
    """
    Return dashboard bootstrap metadata.
    """

    return {
        "platform": "Aussem1",
        "module": "dashboard_bootstrap",
        "status": "active",
        "timestamp": utc_now(),
        "dashboard": {
            "name": "Aussem1 Intelligence Dashboard",
            "status": "active",
            "template": "app/templates/dashboard.html",
            "css": "/static/css/dashboard.css",
            "javascript": "/static/js/dashboard.js",
            "purpose": (
                "Visualize the live chatbot, memory system, training logger, "
                "prompt architecture, property intelligence foundation, and "
                "future AI learning pipeline."
            ),
        },
        "active_modules": [
            "FastAPI Runtime",
            "Dashboard Template",
            "Static CSS Runtime",
            "Chat Engine",
            "Memory Store",
            "Training Logger",
            "Prompt Registry",
            "Property Knowledge Foundation",
            "Render Deployment",
        ],
        "planned_modules": [
            "Dashboard JavaScript Split",
            "Property Lookup Engine",
            "Public Records Engine",
            "Comparable Analysis Engine",
            "Valuation Engine",
            "Learning Engine",
            "PostgreSQL Persistence",
            "Review Dashboard",
            "Machine Learning Operations",
        ],
        "routes": {
            "name": ROUTES_NAME,
            "version": ROUTES_VERSION,
            "phase": ROUTES_PHASE,
            "status": ROUTES_STATUS,
        },
    }


@router.get("/api/dashboard/status")
def dashboard_status() -> dict[str, Any]:
    """
    Return live dashboard status.

    This intentionally returns the direct shape expected by
    the browser dashboard JavaScript.
    """

    return dashboard_status_payload()


# ============================================================
# SECTION 12 - CHATBOT ENDPOINTS
# ============================================================

@router.get("/chat/health")
def chat_health() -> dict[str, Any]:
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


@router.post("/chat")
def chat(
    request_body: ChatRequestBody,
) -> dict[str, Any]:
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

    return serialize_response(response)


@router.post("/chat/trace")
def chat_trace(
    request_body: ChatRequestBody,
) -> dict[str, Any]:
    """
    Process a chatbot request and return a diagnostic trace.
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
                "memory_enabled": hasattr(chat_engine, "memory_store"),
                "training_enabled": hasattr(chat_engine, "training_logger"),
                "property_context_enabled": bool(request_body.property_address),
                "confidence_enabled": (
                    isinstance(serialized, dict)
                    and "confidence" in serialized
                ),
                "intent_enabled": (
                    isinstance(serialized, dict)
                    and "intent" in serialized
                ),
            },
        },
    )


# ============================================================
# SECTION 13 - TRAINING ENDPOINTS
# ============================================================

@router.get("/chat/training-status")
def training_status() -> dict[str, Any]:
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
            "total_interactions": safe_call(
                chat_engine.training_logger.total_interactions,
                fallback=0,
            ),
            "failed_interactions": safe_call(
                chat_engine.training_logger.failed_interactions,
                fallback=0,
            ),
            "unanswered_questions": safe_call(
                chat_engine.training_logger.unanswered_questions,
                fallback=[],
            ),
        },
    )


@router.get("/chat/review-queue")
def training_review_queue() -> dict[str, Any]:
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
def training_export() -> dict[str, Any]:
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
# SECTION 14 - MEMORY ENDPOINTS
# ============================================================

@router.get("/chat/memory-status")
def memory_status() -> dict[str, Any]:
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
            "total_messages": safe_call(
                chat_engine.memory_store.total_messages,
                fallback=0,
            ),
            "total_sessions": safe_call(
                chat_engine.memory_store.total_sessions,
                fallback=0,
            ),
        },
    )


@router.get("/chat/memory-search")
def memory_search(
    query: str,
    limit: int = 20,
) -> dict[str, Any]:
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
) -> dict[str, Any]:
    """
    POST variant of memory search.
    """

    return memory_search(
        query=request_body.query,
        limit=request_body.limit,
    )


# ============================================================
# SECTION 15 - PROMPT ENDPOINTS
# ============================================================

@router.get("/chat/prompt-status")
def prompt_status() -> dict[str, Any]:
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
# SECTION 16 - PROPERTY PREVIEW ENDPOINT
# ============================================================

@router.post("/properties/preview")
def property_preview(
    request_body: PropertyPreviewRequestBody,
) -> dict[str, Any]:
    """
    Preview the future property intelligence flow.

    This does not claim live public-record, MLS, valuation, or
    comparable access. It demonstrates the route contract and
    expected future analysis pipeline.
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
                "Prompt governance",
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
# SECTION 17 - ROUTE REGISTRY
# ============================================================

@router.get("/web/route-registry")
def web_route_registry() -> dict[str, Any]:
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
                "rule_1": "Routes stay thin and delegate intelligence to service modules.",
                "rule_2": "Visual structure belongs in templates.",
                "rule_3": "CSS belongs in static stylesheets.",
                "rule_4": "JavaScript belongs in static scripts.",
                "rule_5": "AI endpoints must expose uncertainty and source status.",
                "rule_6": "Dashboard status must remain compatible with frontend JavaScript.",
            },
        },
    )


# ============================================================
# SECTION 18 - DIAGNOSTICS
# ============================================================

@router.get("/web/diagnostics")
def web_diagnostics() -> dict[str, Any]:
    """
    Return complete web diagnostic state.
    """

    return enterprise_response(
        module="web_diagnostics",
        status="active",
        message="Web diagnostics loaded.",
        data={
            "paths": {
                "project_root": str(PROJECT_ROOT),
                "app_directory": str(APP_DIRECTORY),
                "template_directory": str(TEMPLATE_DIRECTORY),
                "static_directory": str(STATIC_DIRECTORY),
                "static_css_directory": str(STATIC_CSS_DIRECTORY),
                "static_js_directory": str(STATIC_JS_DIRECTORY),
                "data_directory": str(DATA_DIRECTORY),
                "dashboard_template": str(DASHBOARD_TEMPLATE_FILE),
                "dashboard_css": str(DASHBOARD_CSS_FILE),
                "dashboard_js": str(DASHBOARD_JS_FILE),
            },
            "exists": {
                "project_root": PROJECT_ROOT.exists(),
                "app_directory": APP_DIRECTORY.exists(),
                "template_directory": TEMPLATE_DIRECTORY.exists(),
                "static_directory": STATIC_DIRECTORY.exists(),
                "static_css_directory": STATIC_CSS_DIRECTORY.exists(),
                "static_js_directory": STATIC_JS_DIRECTORY.exists(),
                "data_directory": DATA_DIRECTORY.exists(),
                "dashboard_template": DASHBOARD_TEMPLATE_FILE.exists(),
                "dashboard_css": DASHBOARD_CSS_FILE.exists(),
                "dashboard_js": DASHBOARD_JS_FILE.exists(),
            },
            "routes_version": ROUTES_VERSION,
            "routes_phase": ROUTES_PHASE,
            "routes_status": ROUTES_STATUS,
        },
    )


# ============================================================
# SECTION 19 - FUTURE EXPANSION NOTES
# ============================================================

#
# Next correct file:
#
# app/static/js/dashboard.js
#
# Why:
# The dashboard currently has visual structure and CSS, but its
# browser behavior should be moved out of dashboard.html into a
# dedicated JavaScript controller.
#
# Future router expansion:
#
# - /properties/lookup
# - /properties/status
# - /valuation/estimate
# - /comparables/search
# - /public-records/search
# - /market/trends
#
# Rule:
# This router must never contain valuation algorithms, public-record
# scraping logic, ML training logic, or frontend styling.
#
# ============================================================


# ============================================================
# END OF FILE
# ============================================================