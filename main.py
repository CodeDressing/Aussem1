# ============================================================
# AUSSEM1
# PHASE 1.00 PART 9.05
# ENTERPRISE APPLICATION ENTRY POINT
# FILE: main.py
# PURPOSE:
# Central FastAPI application entry point for Aussem1.
#
# This file bootstraps:
# - FastAPI runtime
# - platform health checks
# - static file serving
# - dashboard template support
# - web router registration
# - chatbot route registration
# - Render deployment readiness
# - enterprise diagnostics
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

from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles


# ============================================================
# SECTION 02 - PLATFORM VERSION CONFIGURATION
# ============================================================

PLATFORM_NAME = "Aussem1"

PLATFORM_VERSION = "0.2.0"

PLATFORM_PHASE = "PHASE 1.00 PART 9.05"

PLATFORM_STATUS = "enterprise_visual_application_active"

PLATFORM_DESCRIPTION = (
    "Aussem1 is an AI-first residential real estate intelligence "
    "platform designed to turn one property address into complete "
    "real estate intelligence."
)


# ============================================================
# SECTION 03 - FILESYSTEM CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

APP_DIRECTORY = PROJECT_ROOT / "app"

STATIC_DIRECTORY = APP_DIRECTORY / "static"

TEMPLATE_DIRECTORY = APP_DIRECTORY / "templates"

DATA_DIRECTORY = APP_DIRECTORY / "data"


# ============================================================
# SECTION 04 - APPLICATION FACTORY
# ============================================================

def create_application() -> FastAPI:
    """
    Create and configure the Aussem1 FastAPI application.
    """

    application = FastAPI(
        title=PLATFORM_NAME,
        version=PLATFORM_VERSION,
        description=PLATFORM_DESCRIPTION,
    )

    register_lifecycle_events(application)
    register_exception_handlers(application)
    register_static_files(application)
    register_web_routes(application)
    register_core_routes(application)

    return application


# ============================================================
# SECTION 05 - LIFECYCLE REGISTRATION
# ============================================================

def register_lifecycle_events(application: FastAPI) -> None:
    """
    Attach startup and shutdown behavior.
    """

    @application.on_event("startup")
    async def startup_event() -> None:
        """
        Execute platform startup checks.
        """

        print(
            f"{PLATFORM_NAME} startup complete | "
            f"version={PLATFORM_VERSION} | "
            f"phase={PLATFORM_PHASE}"
        )

    @application.on_event("shutdown")
    async def shutdown_event() -> None:
        """
        Execute platform shutdown procedures.
        """

        print(
            f"{PLATFORM_NAME} shutdown complete | "
            f"version={PLATFORM_VERSION}"
        )


# ============================================================
# SECTION 06 - EXCEPTION HANDLER REGISTRATION
# ============================================================

def register_exception_handlers(application: FastAPI) -> None:
    """
    Register global exception handlers.
    """

    @application.exception_handler(Exception)
    async def global_exception_handler(
        request: Request,
        error: Exception,
    ) -> JSONResponse:
        """
        Return standardized unexpected-error response.
        """

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "platform": PLATFORM_NAME,
                "version": PLATFORM_VERSION,
                "phase": PLATFORM_PHASE,
                "message": "Unexpected platform error.",
                "path": str(request.url.path),
                "detail": str(error),
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )


# ============================================================
# SECTION 07 - STATIC FILE REGISTRATION
# ============================================================

def register_static_files(application: FastAPI) -> None:
    """
    Mount static files for dashboard CSS, JavaScript, images,
    and future frontend assets.
    """

    STATIC_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    application.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIRECTORY)),
        name="static",
    )


# ============================================================
# SECTION 08 - WEB ROUTER REGISTRATION
# ============================================================

def register_web_routes(application: FastAPI) -> None:
    """
    Register the enterprise web/dashboard/chat router.
    """

    try:
        from app.web.routes import router as web_router

        application.include_router(web_router)

    except Exception as error:
        print(
            f"{PLATFORM_NAME} web router registration failed: {error}"
        )


# ============================================================
# SECTION 09 - CORE ROUTE REGISTRATION
# ============================================================

def register_core_routes(application: FastAPI) -> None:
    """
    Register core platform routes.
    """

    # --------------------------------------------------------
    # SECTION 09.01 - ROOT HEALTH ENDPOINT
    # --------------------------------------------------------

    @application.get("/")
    def root_health() -> dict[str, Any]:
        """
        Root health endpoint.
        """

        return {
            "platform": PLATFORM_NAME,
            "version": PLATFORM_VERSION,
            "phase": PLATFORM_PHASE,
            "status": "ok",
            "message": "Aussem1 API is running.",
            "dashboard": "/dashboard",
            "health": "/health",
            "routes": "/routes",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # --------------------------------------------------------
    # SECTION 09.02 - RENDER HEALTH ENDPOINT
    # --------------------------------------------------------

    @application.get("/health")
    def render_health() -> dict[str, Any]:
        """
        Dedicated Render health endpoint.
        """

        return {
            "status": "ok",
            "service": PLATFORM_NAME,
            "version": PLATFORM_VERSION,
            "phase": PLATFORM_PHASE,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # --------------------------------------------------------
    # SECTION 09.03 - PLATFORM INFORMATION ENDPOINT
    # --------------------------------------------------------

    @application.get("/platform")
    def platform_information() -> dict[str, Any]:
        """
        Return platform metadata.
        """

        return {
            "name": PLATFORM_NAME,
            "version": PLATFORM_VERSION,
            "phase": PLATFORM_PHASE,
            "status": PLATFORM_STATUS,
            "description": PLATFORM_DESCRIPTION,
            "core_mission": (
                "Turn one property address into complete residential "
                "real estate intelligence."
            ),
            "active_systems": [
                "FastAPI Runtime",
                "Static File Serving",
                "Dashboard Template Layer",
                "Web Router",
                "AI Chatbot",
                "Training Logger",
                "Conversation Memory",
                "Prompt Registry",
                "Property Knowledge Foundation",
            ],
            "planned_systems": [
                "Property Intelligence Engine",
                "Public Records Engine",
                "Comparable Analysis Engine",
                "Valuation Intelligence Engine",
                "Market Intelligence Engine",
                "Enterprise Learning Engine",
                "PostgreSQL Persistence",
                "Admin Review Dashboard",
            ],
        }

    # --------------------------------------------------------
    # SECTION 09.04 - AI STATUS ENDPOINT
    # --------------------------------------------------------

    @application.get("/ai/status")
    def ai_status() -> dict[str, Any]:
        """
        Return AI subsystem readiness.
        """

        return {
            "platform": PLATFORM_NAME,
            "ai_system": "Aussem1 Intelligence Layer",
            "status": "foundation_active",
            "chatbot": "active",
            "memory": "active",
            "training_logger": "active",
            "prompt_registry": "active",
            "property_reasoning": "planned",
            "confidence_scoring": "foundation_active",
            "valuation_engine": "planned",
            "public_records_engine": "planned",
            "dashboard": "/dashboard",
            "message": (
                "Aussem1 AI foundation is online with visual dashboard, "
                "chat routing, memory, training logging, and prompt architecture."
            ),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # --------------------------------------------------------
    # SECTION 09.05 - STATIC STATUS ENDPOINT
    # --------------------------------------------------------

    @application.get("/static/status")
    def static_status() -> dict[str, Any]:
        """
        Return static asset serving status.
        """

        dashboard_css = STATIC_DIRECTORY / "css" / "dashboard.css"
        dashboard_js = STATIC_DIRECTORY / "js" / "dashboard.js"

        return {
            "platform": PLATFORM_NAME,
            "static_directory": str(STATIC_DIRECTORY),
            "static_directory_exists": STATIC_DIRECTORY.exists(),
            "dashboard_css": str(dashboard_css),
            "dashboard_css_exists": dashboard_css.exists(),
            "dashboard_js": str(dashboard_js),
            "dashboard_js_exists": dashboard_js.exists(),
            "mounted_path": "/static",
            "status": "active",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # --------------------------------------------------------
    # SECTION 09.06 - TEMPLATE STATUS ENDPOINT
    # --------------------------------------------------------

    @application.get("/templates/status")
    def template_status() -> dict[str, Any]:
        """
        Return dashboard template status.
        """

        dashboard_template = TEMPLATE_DIRECTORY / "dashboard.html"

        return {
            "platform": PLATFORM_NAME,
            "template_directory": str(TEMPLATE_DIRECTORY),
            "template_directory_exists": TEMPLATE_DIRECTORY.exists(),
            "dashboard_template": str(dashboard_template),
            "dashboard_template_exists": dashboard_template.exists(),
            "status": "active",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # --------------------------------------------------------
    # SECTION 09.07 - ENTERPRISE ROUTE REGISTRY
    # --------------------------------------------------------

    @application.get("/routes")
    def route_registry() -> dict[str, Any]:
        """
        Return enterprise route registry.
        """

        return {
            "platform": PLATFORM_NAME,
            "version": PLATFORM_VERSION,
            "phase": PLATFORM_PHASE,
            "registry_status": "active",
            "active_routes": {
                "core": [
                    {
                        "path": "/",
                        "method": "GET",
                        "purpose": "Root health and entry endpoint.",
                    },
                    {
                        "path": "/health",
                        "method": "GET",
                        "purpose": "Render health check.",
                    },
                    {
                        "path": "/platform",
                        "method": "GET",
                        "purpose": "Platform metadata.",
                    },
                    {
                        "path": "/ai/status",
                        "method": "GET",
                        "purpose": "AI readiness status.",
                    },
                    {
                        "path": "/routes",
                        "method": "GET",
                        "purpose": "Enterprise route registry.",
                    },
                    {
                        "path": "/static/status",
                        "method": "GET",
                        "purpose": "Static asset serving status.",
                    },
                    {
                        "path": "/templates/status",
                        "method": "GET",
                        "purpose": "Template availability status.",
                    },
                ],
                "visual": [
                    {
                        "path": "/dashboard",
                        "method": "GET",
                        "purpose": "Live Aussem1 visual intelligence dashboard.",
                    },
                ],
                "dashboard_api": [
                    {
                        "path": "/api/dashboard/bootstrap",
                        "method": "GET",
                        "purpose": "Dashboard initialization metadata.",
                    },
                    {
                        "path": "/api/dashboard/status",
                        "method": "GET",
                        "purpose": "Live dashboard system status.",
                    },
                ],
                "chatbot": [
                    {
                        "path": "/chat",
                        "method": "POST",
                        "purpose": "Primary chatbot endpoint.",
                    },
                    {
                        "path": "/chat/trace",
                        "method": "POST",
                        "purpose": "Chat response with diagnostic trace.",
                    },
                    {
                        "path": "/chat/health",
                        "method": "GET",
                        "purpose": "Chatbot route health check.",
                    },
                    {
                        "path": "/chat/training-status",
                        "method": "GET",
                        "purpose": "Training logger status.",
                    },
                    {
                        "path": "/chat/memory-status",
                        "method": "GET",
                        "purpose": "Memory store status.",
                    },
                    {
                        "path": "/chat/review-queue",
                        "method": "GET",
                        "purpose": "Training review queue.",
                    },
                    {
                        "path": "/chat/training-export",
                        "method": "GET",
                        "purpose": "Training dataset export preview.",
                    },
                    {
                        "path": "/chat/memory-search",
                        "method": "GET/POST",
                        "purpose": "Memory search endpoint.",
                    },
                    {
                        "path": "/chat/prompt-status",
                        "method": "GET",
                        "purpose": "Prompt registry validation status.",
                    },
                ],
                "property_preview": [
                    {
                        "path": "/properties/preview",
                        "method": "POST",
                        "purpose": "Future property intelligence route contract.",
                    },
                ],
            },
            "planned_routes": {
                "property_intelligence": [
                    "/properties/lookup",
                    "/properties/status",
                    "/properties/profile",
                    "/properties/history",
                ],
                "valuation": [
                    "/valuation/estimate",
                    "/valuation/confidence",
                    "/valuation/explain",
                ],
                "comparables": [
                    "/comparables/search",
                    "/comparables/rank",
                    "/comparables/report",
                ],
                "public_records": [
                    "/public-records/search",
                    "/public-records/assessor",
                    "/public-records/deeds",
                    "/public-records/taxes",
                    "/public-records/parcel",
                ],
                "market_intelligence": [
                    "/market/status",
                    "/market/trends",
                    "/market/neighborhood",
                    "/market/demand",
                ],
            },
            "governance": {
                "rule_1": "Every new route must be added to this registry.",
                "rule_2": "Routes must stay thin and delegate intelligence to service modules.",
                "rule_3": "Visual structure belongs in templates.",
                "rule_4": "CSS and JavaScript belong in static assets.",
                "rule_5": "AI routes must expose uncertainty and source status.",
                "rule_6": "AI routes must support supervised learning logging.",
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # --------------------------------------------------------
    # SECTION 09.08 - ENTERPRISE DIAGNOSTICS
    # --------------------------------------------------------

    @application.get("/diagnostics")
    def diagnostics() -> dict[str, Any]:
        """
        Return platform diagnostics for deployment debugging.
        """

        return {
            "platform": PLATFORM_NAME,
            "version": PLATFORM_VERSION,
            "phase": PLATFORM_PHASE,
            "status": PLATFORM_STATUS,
            "paths": {
                "project_root": str(PROJECT_ROOT),
                "app_directory": str(APP_DIRECTORY),
                "static_directory": str(STATIC_DIRECTORY),
                "template_directory": str(TEMPLATE_DIRECTORY),
                "data_directory": str(DATA_DIRECTORY),
            },
            "exists": {
                "project_root": PROJECT_ROOT.exists(),
                "app_directory": APP_DIRECTORY.exists(),
                "static_directory": STATIC_DIRECTORY.exists(),
                "template_directory": TEMPLATE_DIRECTORY.exists(),
                "data_directory": DATA_DIRECTORY.exists(),
                "dashboard_template": (
                    TEMPLATE_DIRECTORY / "dashboard.html"
                ).exists(),
                "dashboard_css": (
                    STATIC_DIRECTORY / "css" / "dashboard.css"
                ).exists(),
                "dashboard_js": (
                    STATIC_DIRECTORY / "js" / "dashboard.js"
                ).exists(),
            },
            "render": {
                "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
                "build_command": "pip install -r requirements.txt",
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }


# ============================================================
# SECTION 10 - APPLICATION INSTANCE
# ============================================================

app = create_application()


# ============================================================
# SECTION 11 - LOCAL DEVELOPMENT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


# ============================================================
# SECTION 12 - FUTURE EXPANSION NOTES
# ============================================================

#
# Immediate next requirements:
#
# 1. app/templates/dashboard.html must include:
#
#    <link rel="stylesheet" href="/static/css/dashboard.css" />
#
# 2. app/static/css/dashboard.css must exist.
#
# 3. app/static/js/dashboard.js should be created next and linked with:
#
#    <script src="/static/js/dashboard.js"></script>
#
# 4. requirements.txt must include:
#
#    fastapi
#    uvicorn
#    jinja2
#
# Current responsibility of main.py:
#
# - App creation
# - lifecycle hooks
# - global exception handler
# - static file mounting
# - web router registration
# - core platform endpoints
# - Render health
# - diagnostics
#
# main.py should not contain:
#
# - dashboard HTML
# - dashboard CSS
# - dashboard JavaScript
# - valuation logic
# - public-record lookup logic
# - machine learning model training
#
# ============================================================


# ============================================================
# END OF FILE
# ============================================================