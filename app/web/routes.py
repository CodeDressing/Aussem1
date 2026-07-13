# ============================================================
# AUSSEM1
# PHASE 2.45 PART 2.00
# ENTERPRISE WEB ROUTER STABILIZATION UPGRADE
# FILE: app/web/routes.py
# PURPOSE:
# Stable production-ready web routing layer for Aussem1 dashboard,
# chatbot API, dashboard metrics, memory inspection, training
# intelligence, prompt validation, property-intelligence status
# visibility, deployment diagnostics, and frontend bootstrap data.
#
# IMPORTANT ROUTING RULE:
# This file owns dashboard, chatbot, memory, training, prompt,
# and web diagnostics routes.
#
# This file does NOT own /properties/* anymore.
# Dedicated property-intelligence API routes belong in:
# app/web/property_routes.py
#
# CORE GOVERNANCE:
# - Routes stay thin.
# - Domain logic stays in engines.
# - Property routes stay in property_routes.py.
# - This file never fabricates property facts.
# - This file never fabricates valuation.
# - This file never fabricates listing status.
# - Dashboard payloads must stay stable for dashboard.js.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# ENTERPRISE WEB ROUTER ACTIVE
# ============================================================


from __future__ import annotations

# ============================================================
# SECTION 01 - STANDARD LIBRARY IMPORTS
# ============================================================

import hashlib
import json
import traceback
from dataclasses import asdict
from dataclasses import is_dataclass
from datetime import UTC
from datetime import date
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence
from uuid import uuid4


# ============================================================
# SECTION 02 - FASTAPI / PYDANTIC IMPORTS
# ============================================================

from fastapi import APIRouter
from fastapi import Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator


# ============================================================
# SECTION 03 - SAFE CHATBOT IMPORTS
# ============================================================

IMPORT_ERRORS: dict[str, str] = {}


try:
    from app.chatbot.chat_engine import ChatEngine
    from app.chatbot.chat_engine import ChatRequest
except Exception as exc:  # pragma: no cover
    ChatEngine = None  # type: ignore
    ChatRequest = None  # type: ignore
    IMPORT_ERRORS["chat_engine"] = f"{type(exc).__name__}: {exc}"


try:
    from app.chatbot.prompts import validate_prompts
except Exception as exc:  # pragma: no cover
    validate_prompts = None  # type: ignore
    IMPORT_ERRORS["prompt_registry"] = f"{type(exc).__name__}: {exc}"


# ============================================================
# SECTION 04 - SAFE PROPERTY STATUS IMPORTS
# ============================================================

try:
    from app.property_intelligence.address_intelligence import (
        get_address_intelligence_health,
        get_address_intelligence_metadata,
    )
except Exception as exc:  # pragma: no cover
    get_address_intelligence_health = None  # type: ignore
    get_address_intelligence_metadata = None  # type: ignore
    IMPORT_ERRORS["address_intelligence"] = f"{type(exc).__name__}: {exc}"


try:
    from app.property_intelligence.property_profile_engine import (
        get_property_profile_engine_health,
        get_property_profile_engine_metadata,
        get_property_profile_engine_readiness,
    )
except Exception as exc:  # pragma: no cover
    get_property_profile_engine_health = None  # type: ignore
    get_property_profile_engine_metadata = None  # type: ignore
    get_property_profile_engine_readiness = None  # type: ignore
    IMPORT_ERRORS["property_profile_engine"] = f"{type(exc).__name__}: {exc}"


try:
    from app.property_intelligence.confidence_engine import (
        get_confidence_engine_health,
        get_confidence_engine_metadata,
        get_confidence_engine_readiness,
    )
except Exception as exc:  # pragma: no cover
    get_confidence_engine_health = None  # type: ignore
    get_confidence_engine_metadata = None  # type: ignore
    get_confidence_engine_readiness = None  # type: ignore
    IMPORT_ERRORS["confidence_engine"] = f"{type(exc).__name__}: {exc}"


try:
    from app.property_intelligence.source_explanation_engine import (
        get_source_explanation_engine_health,
        get_source_explanation_engine_metadata,
        get_source_explanation_engine_readiness,
    )
except Exception as exc:  # pragma: no cover
    get_source_explanation_engine_health = None  # type: ignore
    get_source_explanation_engine_metadata = None  # type: ignore
    get_source_explanation_engine_readiness = None  # type: ignore
    IMPORT_ERRORS["source_explanation_engine"] = f"{type(exc).__name__}: {exc}"


try:
    from app.public_records.public_records_engine import (
        get_public_records_engine_health,
        get_public_records_engine_metadata,
        get_public_records_engine_readiness,
    )
except Exception as exc:  # pragma: no cover
    get_public_records_engine_health = None  # type: ignore
    get_public_records_engine_metadata = None  # type: ignore
    get_public_records_engine_readiness = None  # type: ignore
    IMPORT_ERRORS["public_records_engine"] = f"{type(exc).__name__}: {exc}"


# ============================================================
# SECTION 05 - ROUTER METADATA
# ============================================================

ROUTES_NAME = "Aussem1 Enterprise Web Router"

ROUTES_VERSION = "0.6.0"

ROUTES_PHASE = "PHASE 2.45 PART 2.00"

ROUTES_STATUS = "enterprise_web_router_active"

ROUTES_DESCRIPTION = (
    "Stable routing layer for dashboard rendering, chatbot API, memory analytics, "
    "training intelligence, prompt validation, frontend bootstrap data, property "
    "intelligence visibility, and deployment diagnostics."
)


# ============================================================
# SECTION 06 - GOVERNANCE
# ============================================================

WEB_ROUTER_GOVERNANCE = {
    "owns_dashboard_routes": True,
    "owns_chat_routes": True,
    "owns_memory_routes": True,
    "owns_training_routes": True,
    "owns_prompt_routes": True,
    "owns_property_api_routes": False,
    "property_api_routes_owned_by": "app/web/property_routes.py",
    "fabricated_property_facts_allowed": False,
    "fabricated_listing_status_allowed": False,
    "fabricated_valuation_allowed": False,
    "dashboard_js_shape_stability_required": True,
    "safe_degradation_required": True,
}


STANDARD_PROPERTY_LIMITATIONS = [
    "Property facts are not fabricated.",
    "Public records can support parcel, tax, deed, GIS, and MOD-IV context.",
    "Public records alone cannot prove active listing status, under-contract status, current list price, or days on market.",
    "Tax assessment is public-record context and is not current market value.",
    "Valuation output requires source-backed facts, comparable sales, valuation logic, and confidence metadata.",
]


# ============================================================
# SECTION 07 - PATH CONFIGURATION
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
# SECTION 08 - TEMPLATE CONFIGURATION
# ============================================================

templates = Jinja2Templates(
    directory=str(TEMPLATE_DIRECTORY),
)


# ============================================================
# SECTION 09 - ROUTER INSTANCE
# ============================================================

router = APIRouter()


# ============================================================
# SECTION 10 - CHAT ENGINE INSTANCE
# ============================================================

def build_chat_engine() -> Any:
    if ChatEngine is None:
        return None

    try:
        return ChatEngine()
    except Exception as exc:  # pragma: no cover
        IMPORT_ERRORS["chat_engine_instance"] = f"{type(exc).__name__}: {exc}"
        return None


chat_engine = build_chat_engine()


# ============================================================
# SECTION 11 - ENUMERATIONS
# ============================================================

class WebRouteStatus(StrEnum):
    OK = "ok"
    READY = "ready"
    ACTIVE = "active"
    PARTIAL = "partial"
    PLANNED = "planned"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class WebRouteModule(StrEnum):
    WEB_ROUTES = "web_routes"
    DASHBOARD = "dashboard"
    CHATBOT = "chatbot"
    TRAINING_LOGGER = "training_logger"
    MEMORY_STORE = "memory_store"
    PROMPT_REGISTRY = "prompt_registry"
    PROPERTY_INTELLIGENCE_VISIBILITY = "property_intelligence_visibility"
    WEB_DIAGNOSTICS = "web_diagnostics"


# ============================================================
# SECTION 12 - PYDANTIC BASE MODEL
# ============================================================

class EnterpriseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


# ============================================================
# SECTION 13 - REQUEST MODELS
# ============================================================

class ChatRequestBody(EnterpriseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=12000,
        description="User message sent to Aussem1.",
    )
    session_id: str | None = Field(
        default=None,
        max_length=160,
        description="Existing chat session identifier.",
    )
    property_address: str | None = Field(
        default=None,
        max_length=700,
        description="Optional property address context.",
    )
    user_id: str | None = Field(
        default=None,
        max_length=160,
        description="Optional user identifier.",
    )


class FeedbackRequestBody(EnterpriseModel):
    record_id: str = Field(..., min_length=1, max_length=160)
    feedback: str = Field(..., min_length=1, max_length=4000)
    corrected_answer: str | None = Field(default=None, max_length=12000)


class MemorySearchRequestBody(EnterpriseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    limit: int = Field(default=20, ge=1, le=100)


class PropertyStatusRequestBody(EnterpriseModel):
    property_address: str = Field(..., min_length=1, max_length=700)
    question: str | None = Field(default=None, max_length=4000)

    @field_validator("property_address")
    @classmethod
    def validate_property_address(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("property_address cannot be blank")

        return cleaned


# ============================================================
# SECTION 14 - GENERAL UTILITIES
# ============================================================

def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def request_id() -> str:
    return f"aussem1-request-{uuid4()}"


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        serialize_response(value),
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def serialize_response(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, BaseModel):
        return serialize_response(value.model_dump())

    if is_dataclass(value):
        return serialize_response(asdict(value))

    if isinstance(value, StrEnum):
        return value.value

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, Mapping):
        return {
            str(key): serialize_response(item)
            for key, item in value.items()
        }

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return [
            serialize_response(item)
            for item in value
        ]

    if hasattr(value, "to_dict") and callable(value.to_dict):
        return serialize_response(value.to_dict())

    return value


def safe_call(
    callable_object: Any,
    fallback: Any,
    *,
    label: str | None = None,
) -> Any:
    if not callable(callable_object):
        return fallback

    try:
        return callable_object()
    except Exception as error:  # pragma: no cover
        return {
            "status": "unavailable",
            "label": label,
            "error": f"{type(error).__name__}: {error}",
            "traceback": traceback.format_exc(),
            "fallback": fallback,
        }


def safe_count(value: Any) -> int:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value)

    if isinstance(value, Mapping):
        return len(value)

    if isinstance(value, int):
        return value

    return 0


def enterprise_response(
    *,
    module: str,
    status: str,
    data: Any,
    message: str | None = None,
    warnings: Sequence[str] | None = None,
    limitations: Sequence[str] | None = None,
) -> dict[str, Any]:
    payload = {
        "platform": "Aussem1",
        "module": module,
        "status": status,
        "message": message,
        "data": serialize_response(data),
        "warnings": list(warnings or []),
        "limitations": list(limitations or []),
        "request_id": request_id(),
        "timestamp": utc_now(),
        "routes": {
            "name": ROUTES_NAME,
            "version": ROUTES_VERSION,
            "phase": ROUTES_PHASE,
            "status": ROUTES_STATUS,
        },
    }

    payload["fingerprint"] = stable_hash(
        {
            "module": module,
            "status": status,
            "data": payload["data"],
            "timestamp": payload["timestamp"],
        }
    )

    return payload


# ============================================================
# SECTION 15 - CHAT SUBSYSTEM HELPERS
# ============================================================

def chat_available() -> bool:
    return chat_engine is not None and ChatRequest is not None


def chat_engine_status() -> Any:
    if chat_engine is None:
        return {
            "status": WebRouteStatus.UNAVAILABLE.value,
            "reason": "ChatEngine could not be initialized.",
            "import_error": IMPORT_ERRORS.get("chat_engine")
            or IMPORT_ERRORS.get("chat_engine_instance"),
        }

    return safe_call(
        chat_engine.status,
        fallback={
            "status": WebRouteStatus.PARTIAL.value,
            "reason": "chat_engine.status unavailable",
        },
        label="chat_engine.status",
    )


def training_summary_payload() -> Any:
    if chat_engine is None or not hasattr(chat_engine, "training_logger"):
        return {
            "status": WebRouteStatus.UNAVAILABLE.value,
            "reason": "training_logger unavailable",
        }

    return safe_call(
        chat_engine.training_logger.training_summary,
        fallback={},
        label="training_logger.training_summary",
    )


def memory_health_payload() -> Any:
    if chat_engine is None or not hasattr(chat_engine, "memory_store"):
        return {
            "status": WebRouteStatus.UNAVAILABLE.value,
            "reason": "memory_store unavailable",
        }

    return safe_call(
        chat_engine.memory_store.memory_health_report,
        fallback={},
        label="memory_store.memory_health_report",
    )


def prompt_status_payload() -> Any:
    if validate_prompts is None:
        return {
            "status": WebRouteStatus.UNAVAILABLE.value,
            "reason": "validate_prompts could not be imported",
            "import_error": IMPORT_ERRORS.get("prompt_registry"),
        }

    return safe_call(
        validate_prompts,
        fallback={},
        label="validate_prompts",
    )


# ============================================================
# SECTION 16 - PROPERTY VISIBILITY HELPERS
# ============================================================

def property_intelligence_module_status() -> dict[str, Any]:
    return {
        "address_intelligence": {
            "available": callable(get_address_intelligence_health),
            "metadata": safe_call(
                get_address_intelligence_metadata,
                fallback=None,
                label="get_address_intelligence_metadata",
            ),
            "health": safe_call(
                get_address_intelligence_health,
                fallback=None,
                label="get_address_intelligence_health",
            ),
            "import_error": IMPORT_ERRORS.get("address_intelligence"),
        },
        "property_profile_engine": {
            "available": callable(get_property_profile_engine_health),
            "metadata": safe_call(
                get_property_profile_engine_metadata,
                fallback=None,
                label="get_property_profile_engine_metadata",
            ),
            "health": safe_call(
                get_property_profile_engine_health,
                fallback=None,
                label="get_property_profile_engine_health",
            ),
            "readiness": safe_call(
                get_property_profile_engine_readiness,
                fallback=None,
                label="get_property_profile_engine_readiness",
            ),
            "import_error": IMPORT_ERRORS.get("property_profile_engine"),
        },
        "confidence_engine": {
            "available": callable(get_confidence_engine_health),
            "metadata": safe_call(
                get_confidence_engine_metadata,
                fallback=None,
                label="get_confidence_engine_metadata",
            ),
            "health": safe_call(
                get_confidence_engine_health,
                fallback=None,
                label="get_confidence_engine_health",
            ),
            "readiness": safe_call(
                get_confidence_engine_readiness,
                fallback=None,
                label="get_confidence_engine_readiness",
            ),
            "import_error": IMPORT_ERRORS.get("confidence_engine"),
        },
        "source_explanation_engine": {
            "available": callable(get_source_explanation_engine_health),
            "metadata": safe_call(
                get_source_explanation_engine_metadata,
                fallback=None,
                label="get_source_explanation_engine_metadata",
            ),
            "health": safe_call(
                get_source_explanation_engine_health,
                fallback=None,
                label="get_source_explanation_engine_health",
            ),
            "readiness": safe_call(
                get_source_explanation_engine_readiness,
                fallback=None,
                label="get_source_explanation_engine_readiness",
            ),
            "import_error": IMPORT_ERRORS.get("source_explanation_engine"),
        },
        "public_records_engine": {
            "available": callable(get_public_records_engine_health),
            "metadata": safe_call(
                get_public_records_engine_metadata,
                fallback=None,
                label="get_public_records_engine_metadata",
            ),
            "health": safe_call(
                get_public_records_engine_health,
                fallback=None,
                label="get_public_records_engine_health",
            ),
            "readiness": safe_call(
                get_public_records_engine_readiness,
                fallback=None,
                label="get_public_records_engine_readiness",
            ),
            "import_error": IMPORT_ERRORS.get("public_records_engine"),
        },
    }


def property_status_summary() -> dict[str, Any]:
    modules = property_intelligence_module_status()

    ready_flags = [
        bool(item.get("available"))
        for item in modules.values()
    ]

    ready_count = sum(1 for item in ready_flags if item)

    return {
        "status": (
            WebRouteStatus.READY.value
            if ready_count == len(ready_flags)
            else WebRouteStatus.PARTIAL.value
        ),
        "ready": ready_count == len(ready_flags),
        "ready_count": ready_count,
        "module_count": len(ready_flags),
        "modules": modules,
        "owned_routes": {
            "property_api_router_file": "app/web/property_routes.py",
            "property_api_prefix": "/properties",
            "web_router_owns_properties_prefix": False,
        },
        "limitations": STANDARD_PROPERTY_LIMITATIONS,
    }


# ============================================================
# SECTION 17 - DASHBOARD STATUS PAYLOAD
# ============================================================

def dashboard_status_payload() -> dict[str, Any]:
    training_summary = training_summary_payload()
    memory_health = memory_health_payload()
    engine_status = chat_engine_status()
    prompt_status = prompt_status_payload()
    property_status = property_status_summary()

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
                "property_preview_route_removed_from_web_router": True,
                "property_routes_owned_by": "app/web/property_routes.py",
            },
            "chat_engine": engine_status,
            "training_logger": training_summary,
            "memory_store": {
                "status": (
                    "active"
                    if isinstance(memory_health, Mapping)
                    else "partial"
                ),
                "health": memory_health,
            },
            "prompt_registry": prompt_status,
            "property_intelligence": property_status,
        },
        "metrics": {
            "memory_messages": extract_metric(
                memory_health,
                [
                    "total_messages",
                    "message_count",
                    "messages",
                ],
            ),
            "sessions": extract_metric(
                memory_health,
                [
                    "total_sessions",
                    "session_count",
                    "sessions",
                ],
            ),
            "training_records": extract_metric(
                training_summary,
                [
                    "total_interactions",
                    "records",
                    "count",
                ],
            ),
            "review_queue": extract_metric(
                training_summary,
                [
                    "review_queue_count",
                    "review_count",
                    "needs_review",
                ],
            ),
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
        "router": {
            "name": ROUTES_NAME,
            "version": ROUTES_VERSION,
            "phase": ROUTES_PHASE,
            "status": ROUTES_STATUS,
            "governance": WEB_ROUTER_GOVERNANCE,
        },
    }


def extract_metric(payload: Any, keys: Sequence[str]) -> int:
    if not isinstance(payload, Mapping):
        return 0

    for key in keys:
        value = payload.get(key)

        if isinstance(value, int):
            return value

        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return len(value)

    return 0


# ============================================================
# SECTION 18 - VISUAL DASHBOARD ROUTES
# ============================================================

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    if not DASHBOARD_TEMPLATE_FILE.exists():
        return HTMLResponse(
            content="""
            <html>
                <body style="background:#020617;color:white;font-family:system-ui;padding:40px;">
                    <h1>Aussem1 Dashboard Template Missing</h1>
                    <p>Expected file: app/templates/dashboard.html</p>
                </body>
            </html>
            """,
            status_code=500,
        )

    html = DASHBOARD_TEMPLATE_FILE.read_text(
        encoding="utf-8",
    )

    return HTMLResponse(
        content=html,
        status_code=200,
    )


# ============================================================
# SECTION 19 - WEB HEALTH AND READINESS
# ============================================================

@router.get("/web/health")
def web_health() -> dict[str, Any]:
    return enterprise_response(
        module=WebRouteModule.WEB_ROUTES.value,
        status=WebRouteStatus.OK.value,
        message="Aussem1 web routing layer is active.",
        data={
            "routes_name": ROUTES_NAME,
            "version": ROUTES_VERSION,
            "phase": ROUTES_PHASE,
            "status": ROUTES_STATUS,
            "template_directory": str(TEMPLATE_DIRECTORY),
            "template_directory_exists": TEMPLATE_DIRECTORY.exists(),
            "dashboard_template_exists": DASHBOARD_TEMPLATE_FILE.exists(),
            "dashboard_css_exists": DASHBOARD_CSS_FILE.exists(),
            "dashboard_js_exists": DASHBOARD_JS_FILE.exists(),
            "chat_available": chat_available(),
            "import_errors": IMPORT_ERRORS,
            "governance": WEB_ROUTER_GOVERNANCE,
        },
    )


@router.get("/web/readiness")
def web_readiness() -> dict[str, Any]:
    checks = {
        "template_directory": TEMPLATE_DIRECTORY.exists(),
        "dashboard_template": DASHBOARD_TEMPLATE_FILE.exists(),
        "static_directory": STATIC_DIRECTORY.exists(),
        "dashboard_css": DASHBOARD_CSS_FILE.exists(),
        "dashboard_js": DASHBOARD_JS_FILE.exists(),
        "data_directory": DATA_DIRECTORY.exists(),
        "chat_engine": chat_engine is not None,
        "chat_request_class": ChatRequest is not None,
        "memory_store": bool(chat_engine is not None and hasattr(chat_engine, "memory_store")),
        "training_logger": bool(chat_engine is not None and hasattr(chat_engine, "training_logger")),
    }

    ready = all(checks.values())

    return enterprise_response(
        module="web_readiness",
        status=WebRouteStatus.READY.value if ready else WebRouteStatus.PARTIAL.value,
        message="Dashboard readiness inspection complete.",
        data={
            "ready": ready,
            "checks": checks,
            "import_errors": IMPORT_ERRORS,
            "property_routes_note": (
                "The web router does not own /properties/*; those routes are "
                "registered by app/web/property_routes.py."
            ),
        },
    )


# ============================================================
# SECTION 20 - DASHBOARD APIS
# ============================================================

@router.get("/api/dashboard/bootstrap")
def dashboard_bootstrap() -> dict[str, Any]:
    return {
        "platform": "Aussem1",
        "module": "dashboard_bootstrap",
        "status": "active",
        "timestamp": utc_now(),
        "dashboard": {
            "name": "Aussem1 Property Intelligence Command Center",
            "status": "active",
            "template": "app/templates/dashboard.html",
            "css": "/static/css/dashboard.css",
            "javascript": "/static/js/dashboard.js",
            "purpose": (
                "Visualize the live chatbot, memory system, training logger, "
                "prompt architecture, property intelligence foundation, public "
                "records status, source-governed profile logic, and future "
                "AI learning pipeline."
            ),
        },
        "active_modules": [
            "FastAPI Runtime",
            "Dashboard Template",
            "Static CSS Runtime",
            "Dashboard JavaScript Controller",
            "Chat Engine",
            "Memory Store",
            "Training Logger",
            "Prompt Registry",
            "Address Intelligence Visibility",
            "Property Profile Visibility",
            "Confidence Engine Visibility",
            "Source Explanation Visibility",
            "Public Records Visibility",
            "Render Deployment",
        ],
        "property_intelligence_stack": [
            {
                "module": "Address Intelligence",
                "route_owner": "app/web/property_routes.py",
                "api": "/properties/address/analyze",
                "status": "connected" if callable(get_address_intelligence_health) else "unavailable",
            },
            {
                "module": "Property Profile Engine",
                "route_owner": "app/web/property_routes.py",
                "api": "/properties/profile/build",
                "status": "connected" if callable(get_property_profile_engine_health) else "unavailable",
            },
            {
                "module": "Confidence Engine",
                "route_owner": "app/web/property_routes.py",
                "api": "/properties/confidence/evaluate",
                "status": "connected" if callable(get_confidence_engine_health) else "unavailable",
            },
            {
                "module": "Source Explanation Engine",
                "route_owner": "app/web/property_routes.py",
                "api": "/properties/explain",
                "status": "connected" if callable(get_source_explanation_engine_health) else "unavailable",
            },
            {
                "module": "Public Records Engine",
                "route_owner": "app/public_records/public_records_engine.py",
                "api": "called by profile engine",
                "status": "connected" if callable(get_public_records_engine_health) else "unavailable",
            },
        ],
        "planned_modules": [
            "Live Morris County Tax Board Source Client",
            "Live Morris County GIS Source Client",
            "Live County Clerk Source Client",
            "Comparable Sales Dataset",
            "Valuation Engine",
            "Persistent Property Repository",
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
        "governance": WEB_ROUTER_GOVERNANCE,
    }


@router.get("/api/dashboard/status")
def dashboard_status() -> dict[str, Any]:
    return dashboard_status_payload()


# ============================================================
# SECTION 21 - CHATBOT ENDPOINTS
# ============================================================

@router.get("/chat/health")
def chat_health() -> dict[str, Any]:
    return enterprise_response(
        module=WebRouteModule.CHATBOT.value,
        status=WebRouteStatus.OK.value if chat_available() else WebRouteStatus.UNAVAILABLE.value,
        message=(
            "Chatbot HTTP layer is active."
            if chat_available()
            else "Chatbot HTTP layer is unavailable."
        ),
        data={
            "engine": "ChatEngine",
            "chat_endpoint": "/chat",
            "supports_session_id": True,
            "supports_property_address": True,
            "supports_training_logging": bool(
                chat_engine is not None and hasattr(chat_engine, "training_logger")
            ),
            "supports_memory_storage": bool(
                chat_engine is not None and hasattr(chat_engine, "memory_store")
            ),
            "available": chat_available(),
            "import_errors": IMPORT_ERRORS,
        },
    )


@router.post("/chat")
def chat(
    request_body: ChatRequestBody,
) -> dict[str, Any]:
    if not chat_available():
        return enterprise_response(
            module=WebRouteModule.CHATBOT.value,
            status=WebRouteStatus.UNAVAILABLE.value,
            message="Chat engine is unavailable.",
            data={
                "request": request_body.model_dump(),
                "import_errors": IMPORT_ERRORS,
            },
        )

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
    if not chat_available():
        return enterprise_response(
            module="chat_trace",
            status=WebRouteStatus.UNAVAILABLE.value,
            message="Chat engine is unavailable.",
            data={
                "request": request_body.model_dump(),
                "import_errors": IMPORT_ERRORS,
            },
        )

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
                    isinstance(serialized, Mapping)
                    and "confidence" in serialized
                ),
                "intent_enabled": (
                    isinstance(serialized, Mapping)
                    and "intent" in serialized
                ),
                "property_api_owner": "app/web/property_routes.py",
                "web_router_property_preview_removed": True,
            },
        },
    )


# ============================================================
# SECTION 22 - TRAINING ENDPOINTS
# ============================================================

@router.get("/chat/training-status")
def training_status() -> dict[str, Any]:
    summary = training_summary_payload()

    total_interactions = 0
    failed_interactions = 0
    unanswered_questions: Any = []

    if chat_engine is not None and hasattr(chat_engine, "training_logger"):
        total_interactions = safe_call(
            chat_engine.training_logger.total_interactions,
            fallback=0,
            label="training_logger.total_interactions",
        )
        failed_interactions = safe_call(
            chat_engine.training_logger.failed_interactions,
            fallback=0,
            label="training_logger.failed_interactions",
        )
        unanswered_questions = safe_call(
            chat_engine.training_logger.unanswered_questions,
            fallback=[],
            label="training_logger.unanswered_questions",
        )

    return enterprise_response(
        module=WebRouteModule.TRAINING_LOGGER.value,
        status=WebRouteStatus.ACTIVE.value,
        message="Training logger status loaded.",
        data={
            "summary": summary,
            "total_interactions": total_interactions,
            "failed_interactions": failed_interactions,
            "unanswered_questions": unanswered_questions,
        },
    )


@router.get("/chat/review-queue")
def training_review_queue() -> dict[str, Any]:
    queue: Any = []

    if chat_engine is not None and hasattr(chat_engine, "training_logger"):
        queue = safe_call(
            lambda: chat_engine.training_logger.review_queue(limit=25),
            fallback=[],
            label="training_logger.review_queue",
        )

    return enterprise_response(
        module="training_review_queue",
        status=WebRouteStatus.ACTIVE.value,
        message="Training review queue loaded.",
        data={
            "items": queue,
            "count": safe_count(queue),
        },
    )


@router.get("/chat/training-export")
def training_export() -> dict[str, Any]:
    dataset: Any = []

    if chat_engine is not None and hasattr(chat_engine, "training_logger"):
        dataset = safe_call(
            chat_engine.training_logger.export_training_dataset,
            fallback=[],
            label="training_logger.export_training_dataset",
        )

    return enterprise_response(
        module="training_export",
        status=WebRouteStatus.ACTIVE.value,
        message="Training dataset export generated.",
        data={
            "dataset": dataset,
            "count": safe_count(dataset),
        },
    )


# ============================================================
# SECTION 23 - MEMORY ENDPOINTS
# ============================================================

@router.get("/chat/memory-status")
def memory_status() -> dict[str, Any]:
    memory_health = memory_health_payload()

    total_messages = 0
    total_sessions = 0

    if chat_engine is not None and hasattr(chat_engine, "memory_store"):
        total_messages = safe_call(
            chat_engine.memory_store.total_messages,
            fallback=0,
            label="memory_store.total_messages",
        )
        total_sessions = safe_call(
            chat_engine.memory_store.total_sessions,
            fallback=0,
            label="memory_store.total_sessions",
        )

    return enterprise_response(
        module=WebRouteModule.MEMORY_STORE.value,
        status=WebRouteStatus.ACTIVE.value,
        message="Memory store status loaded.",
        data={
            "health": memory_health,
            "total_messages": total_messages,
            "total_sessions": total_sessions,
        },
    )


@router.get("/chat/memory-search")
def memory_search(
    query: str = Query(..., min_length=1, max_length=2000),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    results: Any = []

    if chat_engine is not None and hasattr(chat_engine, "memory_store"):
        results = safe_call(
            lambda: chat_engine.memory_store.search_memory(
                query=query,
                limit=limit,
            ),
            fallback=[],
            label="memory_store.search_memory",
        )

    return enterprise_response(
        module="memory_search",
        status=WebRouteStatus.ACTIVE.value,
        message="Memory search complete.",
        data={
            "query": query,
            "limit": limit,
            "results": results,
            "count": safe_count(results),
        },
    )


@router.post("/chat/memory-search")
def memory_search_post(
    request_body: MemorySearchRequestBody,
) -> dict[str, Any]:
    return memory_search(
        query=request_body.query,
        limit=request_body.limit,
    )


# ============================================================
# SECTION 24 - PROMPT ENDPOINTS
# ============================================================

@router.get("/chat/prompt-status")
def prompt_status() -> dict[str, Any]:
    status_payload = prompt_status_payload()

    return enterprise_response(
        module=WebRouteModule.PROMPT_REGISTRY.value,
        status=(
            WebRouteStatus.ACTIVE.value
            if validate_prompts
            else WebRouteStatus.UNAVAILABLE.value
        ),
        message="Prompt registry status loaded.",
        data=status_payload,
    )


# ============================================================
# SECTION 25 - PROPERTY INTELLIGENCE VISIBILITY ENDPOINTS
# NOTE:
# These are web-visibility status endpoints only.
# Real /properties/* APIs live in app/web/property_routes.py.
# ============================================================

@router.get("/property-intelligence/web-status")
def property_intelligence_web_status() -> dict[str, Any]:
    return enterprise_response(
        module=WebRouteModule.PROPERTY_INTELLIGENCE_VISIBILITY.value,
        status=WebRouteStatus.ACTIVE.value,
        message="Property intelligence web visibility status loaded.",
        data=property_status_summary(),
        limitations=STANDARD_PROPERTY_LIMITATIONS,
    )


@router.post("/web/property-preview")
def web_property_preview(
    request_body: PropertyStatusRequestBody,
) -> dict[str, Any]:
    return enterprise_response(
        module="web_property_preview",
        status=WebRouteStatus.PLANNED.value,
        message=(
            "This web preview endpoint is only a dashboard-safe compatibility route. "
            "Use /properties/preview for the real property intelligence API."
        ),
        data={
            "property_address": request_body.property_address,
            "question": request_body.question,
            "real_property_api": "/properties/preview",
            "property_api_owner": "app/web/property_routes.py",
            "pipeline": [
                "Address Intelligence",
                "Public Records Engine",
                "Property Profile Engine",
                "Confidence Engine",
                "Source Explanation Engine",
                "Future Valuation Engine",
            ],
            "not_returned_here": [
                "fabricated estimate",
                "fabricated listing status",
                "fabricated public records",
                "fabricated owner facts",
            ],
        },
        limitations=STANDARD_PROPERTY_LIMITATIONS,
    )


# ============================================================
# SECTION 26 - ROUTE REGISTRY
# ============================================================

@router.get("/web/route-registry")
def web_route_registry() -> dict[str, Any]:
    return enterprise_response(
        module="web_route_registry",
        status=WebRouteStatus.ACTIVE.value,
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
            "web_property_visibility_routes": [
                "/property-intelligence/web-status",
                "/web/property-preview",
            ],
            "dedicated_property_api_routes_owned_elsewhere": [
                "/properties",
                "/properties/health",
                "/properties/readiness",
                "/properties/diagnostics",
                "/properties/registry/routes",
                "/properties/address/analyze",
                "/properties/address/compare",
                "/properties/profile/build",
                "/properties/profile/refresh",
                "/properties/profile/merge",
                "/properties/confidence/evaluate",
                "/properties/explain",
                "/properties/estimate/preview",
                "/properties/preview",
                "/properties/batch/profile/build",
            ],
            "governance": WEB_ROUTER_GOVERNANCE,
        },
    )


# ============================================================
# SECTION 27 - DIAGNOSTICS
# ============================================================

@router.get("/web/diagnostics")
def web_diagnostics() -> dict[str, Any]:
    return enterprise_response(
        module=WebRouteModule.WEB_DIAGNOSTICS.value,
        status=WebRouteStatus.ACTIVE.value,
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
            "import_errors": IMPORT_ERRORS,
            "chat": {
                "available": chat_available(),
                "engine_initialized": chat_engine is not None,
                "chat_request_class_available": ChatRequest is not None,
            },
            "property_intelligence_visibility": property_status_summary(),
            "governance": WEB_ROUTER_GOVERNANCE,
            "note": (
                "This web router intentionally does not define /properties/* routes. "
                "Dedicated property API routes are registered from app/web/property_routes.py."
            ),
        },
    )


# ============================================================
# SECTION 28 - ROUTER REGISTRATION HELPER
# ============================================================

def register_web_router(app: Any) -> Any:
    app.include_router(router)

    return app


# ============================================================
# SECTION 29 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "router",
    "register_web_router",
    "ROUTES_NAME",
    "ROUTES_VERSION",
    "ROUTES_PHASE",
    "ROUTES_STATUS",
    "ROUTES_DESCRIPTION",
    "WEB_ROUTER_GOVERNANCE",
    "PROJECT_ROOT",
    "APP_DIRECTORY",
    "TEMPLATE_DIRECTORY",
    "STATIC_DIRECTORY",
    "STATIC_CSS_DIRECTORY",
    "STATIC_JS_DIRECTORY",
    "DATA_DIRECTORY",
    "DASHBOARD_TEMPLATE_FILE",
    "DASHBOARD_CSS_FILE",
    "DASHBOARD_JS_FILE",
    "ChatRequestBody",
    "FeedbackRequestBody",
    "MemorySearchRequestBody",
    "PropertyStatusRequestBody",
    "dashboard",
    "web_health",
    "web_readiness",
    "dashboard_bootstrap",
    "dashboard_status",
    "chat_health",
    "chat",
    "chat_trace",
    "training_status",
    "training_review_queue",
    "training_export",
    "memory_status",
    "memory_search",
    "memory_search_post",
    "prompt_status",
    "property_intelligence_web_status",
    "web_property_preview",
    "web_route_registry",
    "web_diagnostics",
]


# ============================================================
# END OF FILE
# ============================================================