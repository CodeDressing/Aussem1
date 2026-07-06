# ============================================================
# AUSSEM1
# PHASE 1.00 PART 9.07
# ENTERPRISE VISUAL APPLICATION ENTRY POINT
# FILE: main.py
# PURPOSE:
# Bootstrap the complete Aussem1 FastAPI application with:
# - root dashboard redirect
# - static file serving
# - dashboard routing
# - router registration
# - health checks
# - diagnostics
# - fallback visual dashboard support
# - Render deployment readiness
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
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles


# ============================================================
# SECTION 02 - PLATFORM CONFIGURATION
# ============================================================

PLATFORM_NAME = "Aussem1"

PLATFORM_VERSION = "0.2.1"

PLATFORM_PHASE = "PHASE 1.00 PART 9.07"

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

STATIC_CSS_DIRECTORY = STATIC_DIRECTORY / "css"

STATIC_JS_DIRECTORY = STATIC_DIRECTORY / "js"

TEMPLATE_DIRECTORY = APP_DIRECTORY / "templates"

DATA_DIRECTORY = APP_DIRECTORY / "data"

DASHBOARD_TEMPLATE = TEMPLATE_DIRECTORY / "dashboard.html"

DASHBOARD_CSS = STATIC_CSS_DIRECTORY / "dashboard.css"

DASHBOARD_JS = STATIC_JS_DIRECTORY / "dashboard.js"


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

    ensure_runtime_directories()
    register_lifecycle_events(application)
    register_exception_handlers(application)
    register_static_files(application)
    register_web_router(application)
    register_core_routes(application)
    register_fallback_visual_routes(application)

    return application


# ============================================================
# SECTION 05 - RUNTIME DIRECTORY CREATION
# ============================================================

def ensure_runtime_directories() -> None:
    """
    Ensure all required application runtime directories exist.
    """

    APP_DIRECTORY.mkdir(parents=True, exist_ok=True)
    STATIC_DIRECTORY.mkdir(parents=True, exist_ok=True)
    STATIC_CSS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    STATIC_JS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    TEMPLATE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)


# ============================================================
# SECTION 06 - LIFECYCLE EVENTS
# ============================================================

def register_lifecycle_events(application: FastAPI) -> None:
    """
    Register application startup and shutdown behavior.
    """

    @application.on_event("startup")
    async def startup_event() -> None:
        """
        Print startup diagnostics.
        """

        print("=" * 72)
        print(f"{PLATFORM_NAME} startup complete")
        print(f"version: {PLATFORM_VERSION}")
        print(f"phase: {PLATFORM_PHASE}")
        print(f"status: {PLATFORM_STATUS}")
        print(f"project_root: {PROJECT_ROOT}")
        print(f"dashboard_template_exists: {DASHBOARD_TEMPLATE.exists()}")
        print(f"dashboard_css_exists: {DASHBOARD_CSS.exists()}")
        print("=" * 72)

    @application.on_event("shutdown")
    async def shutdown_event() -> None:
        """
        Print shutdown diagnostics.
        """

        print(f"{PLATFORM_NAME} shutdown complete | version={PLATFORM_VERSION}")


# ============================================================
# SECTION 07 - EXCEPTION HANDLERS
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
                "platform": PLATFORM_NAME,
                "version": PLATFORM_VERSION,
                "phase": PLATFORM_PHASE,
                "status": "error",
                "message": "Unexpected Aussem1 platform error.",
                "path": str(request.url.path),
                "detail": str(error),
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )


# ============================================================
# SECTION 08 - STATIC FILE REGISTRATION
# ============================================================

def register_static_files(application: FastAPI) -> None:
    """
    Mount static assets for CSS, JavaScript, images, and future UI assets.
    """

    application.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIRECTORY)),
        name="static",
    )


# ============================================================
# SECTION 09 - WEB ROUTER REGISTRATION
# ============================================================

def register_web_router(application: FastAPI) -> None:
    """
    Register the enterprise web router.

    Important:
    This should register /dashboard, /chat, /api/dashboard/status,
    and related visual/API endpoints.
    """

    try:
        from app.web.routes import router as web_router

        application.include_router(web_router)

        application.state.web_router_loaded = True
        application.state.web_router_error = None

    except Exception as error:
        application.state.web_router_loaded = False
        application.state.web_router_error = str(error)

        print("=" * 72)
        print(f"{PLATFORM_NAME} web router registration failed")
        print(str(error))
        print("=" * 72)


# ============================================================
# SECTION 10 - CORE ROUTES
# ============================================================

def register_core_routes(application: FastAPI) -> None:
    """
    Register core platform routes.
    """

    # --------------------------------------------------------
    # SECTION 10.01 - ROOT DASHBOARD REDIRECT
    # --------------------------------------------------------

    @application.get("/")
    def root_dashboard_redirect() -> RedirectResponse:
        """
        Redirect root traffic to the live visual dashboard.
        """

        return RedirectResponse(
            url="/dashboard",
            status_code=307,
        )

    # --------------------------------------------------------
    # SECTION 10.02 - HEALTH CHECK
    # --------------------------------------------------------

    @application.get("/health")
    def health_check() -> dict[str, Any]:
        """
        Render-compatible health endpoint.
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
    # SECTION 10.03 - PLATFORM METADATA
    # --------------------------------------------------------

    @application.get("/platform")
    def platform_information() -> dict[str, Any]:
        """
        Return Aussem1 platform metadata.
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
                "Template Dashboard",
                "Web Router",
                "Chatbot API",
                "Memory Store",
                "Training Logger",
                "Prompt Registry",
                "Dashboard Diagnostics",
            ],
            "planned_systems": [
                "Property Lookup Engine",
                "Public Records Engine",
                "Comparable Analysis Engine",
                "Valuation Engine",
                "Market Intelligence Engine",
                "PostgreSQL Persistence",
                "Review Dashboard",
                "Machine Learning Operations",
            ],
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # --------------------------------------------------------
    # SECTION 10.04 - AI STATUS
    # --------------------------------------------------------

    @application.get("/ai/status")
    def ai_status() -> dict[str, Any]:
        """
        Return AI subsystem status.
        """

        return {
            "platform": PLATFORM_NAME,
            "ai_system": "Aussem1 Intelligence Layer",
            "status": "foundation_active",
            "chatbot": "active",
            "memory": "active",
            "training_logger": "active",
            "prompt_registry": "active",
            "dashboard": "active",
            "property_reasoning": "planned",
            "valuation_engine": "planned",
            "public_records_engine": "planned",
            "message": (
                "Aussem1 AI foundation is online with visual dashboard, "
                "chat routing, memory, training logging, and prompt governance."
            ),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # --------------------------------------------------------
    # SECTION 10.05 - STATIC STATUS
    # --------------------------------------------------------

    @application.get("/static/status")
    def static_status() -> dict[str, Any]:
        """
        Return static asset status.
        """

        return {
            "platform": PLATFORM_NAME,
            "status": "active",
            "mounted_path": "/static",
            "static_directory": str(STATIC_DIRECTORY),
            "static_directory_exists": STATIC_DIRECTORY.exists(),
            "dashboard_css": str(DASHBOARD_CSS),
            "dashboard_css_exists": DASHBOARD_CSS.exists(),
            "dashboard_js": str(DASHBOARD_JS),
            "dashboard_js_exists": DASHBOARD_JS.exists(),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # --------------------------------------------------------
    # SECTION 10.06 - TEMPLATE STATUS
    # --------------------------------------------------------

    @application.get("/templates/status")
    def template_status() -> dict[str, Any]:
        """
        Return template availability status.
        """

        return {
            "platform": PLATFORM_NAME,
            "status": "active",
            "template_directory": str(TEMPLATE_DIRECTORY),
            "template_directory_exists": TEMPLATE_DIRECTORY.exists(),
            "dashboard_template": str(DASHBOARD_TEMPLATE),
            "dashboard_template_exists": DASHBOARD_TEMPLATE.exists(),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # --------------------------------------------------------
    # SECTION 10.07 - FULL DIAGNOSTICS
    # --------------------------------------------------------

    @application.get("/diagnostics")
    def diagnostics() -> dict[str, Any]:
        """
        Return full deployment diagnostics.
        """

        return {
            "platform": PLATFORM_NAME,
            "version": PLATFORM_VERSION,
            "phase": PLATFORM_PHASE,
            "status": PLATFORM_STATUS,
            "web_router": {
                "loaded": getattr(application.state, "web_router_loaded", False),
                "error": getattr(application.state, "web_router_error", None),
            },
            "paths": {
                "project_root": str(PROJECT_ROOT),
                "app_directory": str(APP_DIRECTORY),
                "static_directory": str(STATIC_DIRECTORY),
                "static_css_directory": str(STATIC_CSS_DIRECTORY),
                "static_js_directory": str(STATIC_JS_DIRECTORY),
                "template_directory": str(TEMPLATE_DIRECTORY),
                "data_directory": str(DATA_DIRECTORY),
                "dashboard_template": str(DASHBOARD_TEMPLATE),
                "dashboard_css": str(DASHBOARD_CSS),
                "dashboard_js": str(DASHBOARD_JS),
            },
            "exists": {
                "project_root": PROJECT_ROOT.exists(),
                "app_directory": APP_DIRECTORY.exists(),
                "static_directory": STATIC_DIRECTORY.exists(),
                "static_css_directory": STATIC_CSS_DIRECTORY.exists(),
                "static_js_directory": STATIC_JS_DIRECTORY.exists(),
                "template_directory": TEMPLATE_DIRECTORY.exists(),
                "data_directory": DATA_DIRECTORY.exists(),
                "dashboard_template": DASHBOARD_TEMPLATE.exists(),
                "dashboard_css": DASHBOARD_CSS.exists(),
                "dashboard_js": DASHBOARD_JS.exists(),
            },
            "render": {
                "build_command": "pip install -r requirements.txt",
                "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # --------------------------------------------------------
    # SECTION 10.08 - ENTERPRISE ROUTE REGISTRY
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
            "root_behavior": {
                "path": "/",
                "behavior": "redirects_to_dashboard",
                "target": "/dashboard",
            },
            "active_routes": {
                "core": [
                    "/",
                    "/health",
                    "/platform",
                    "/ai/status",
                    "/routes",
                    "/diagnostics",
                    "/static/status",
                    "/templates/status",
                ],
                "visual": [
                    "/dashboard",
                ],
                "expected_web_router_routes": [
                    "/chat",
                    "/chat/health",
                    "/chat/trace",
                    "/chat/training-status",
                    "/chat/memory-status",
                    "/chat/review-queue",
                    "/chat/training-export",
                    "/chat/memory-search",
                    "/chat/prompt-status",
                    "/api/dashboard/bootstrap",
                    "/api/dashboard/status",
                    "/properties/preview",
                    "/web/route-registry",
                    "/web/diagnostics",
                    "/web/readiness",
                ],
            },
            "governance": {
                "rule_1": "Root route must show or redirect to a visual application.",
                "rule_2": "Static files must be mounted at /static.",
                "rule_3": "Dashboard template must live in app/templates.",
                "rule_4": "Dashboard CSS must live in app/static/css.",
                "rule_5": "Dashboard JavaScript must live in app/static/js.",
                "rule_6": "Routes must stay thin and delegate intelligence to service modules.",
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }


# ============================================================
# SECTION 11 - FALLBACK VISUAL ROUTES
# ============================================================

def register_fallback_visual_routes(application: FastAPI) -> None:
    """
    Register a fallback /dashboard route if the web router failed.

    If app.web.routes loads correctly, its /dashboard route is used.
    If it fails, this route still gives the browser a visual screen
    explaining what is missing instead of leaving the user with JSON.
    """

    if getattr(application.state, "web_router_loaded", False):
        return

    @application.get("/dashboard", response_class=HTMLResponse)
    def fallback_dashboard() -> HTMLResponse:
        """
        Fallback visual dashboard for router failure diagnostics.
        """

        error_message = getattr(
            application.state,
            "web_router_error",
            "Unknown web router error.",
        )

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Aussem1 Dashboard Diagnostic</title>
            <style>
                body {{
                    margin: 0;
                    min-height: 100vh;
                    display: grid;
                    place-items: center;
                    background:
                        radial-gradient(circle at top left, rgba(56,189,248,.22), transparent 35%),
                        linear-gradient(135deg, #020617, #0f172a);
                    color: #f8fafc;
                    font-family: Inter, system-ui, sans-serif;
                }}
                .card {{
                    width: min(900px, calc(100% - 40px));
                    padding: 38px;
                    border-radius: 28px;
                    background: rgba(15,23,42,.92);
                    border: 1px solid rgba(148,163,184,.22);
                    box-shadow: 0 30px 90px rgba(0,0,0,.45);
                }}
                h1 {{
                    margin: 0 0 16px;
                    font-size: clamp(34px, 7vw, 70px);
                    line-height: .95;
                    letter-spacing: -.06em;
                }}
                p {{
                    color: #94a3b8;
                    line-height: 1.7;
                    font-size: 16px;
                }}
                code, pre {{
                    display: block;
                    padding: 16px;
                    border-radius: 16px;
                    background: rgba(2,6,23,.72);
                    border: 1px solid rgba(148,163,184,.18);
                    color: #cbd5e1;
                    white-space: pre-wrap;
                    overflow: auto;
                }}
                a {{
                    color: #38bdf8;
                    font-weight: 800;
                }}
            </style>
        </head>
        <body>
            <main class="card">
                <h1>Aussem1 Dashboard Diagnostic</h1>
                <p>
                    The root route is working, but the enterprise web router did not load.
                    This fallback page proves the visual runtime is active while showing
                    exactly what needs to be fixed.
                </p>
                <p><strong>Router error:</strong></p>
                <pre>{error_message}</pre>
                <p>
                    Check <a href="/diagnostics">/diagnostics</a>,
                    <a href="/templates/status">/templates/status</a>,
                    and <a href="/static/status">/static/status</a>.
                </p>
            </main>
        </body>
        </html>
        """

        return HTMLResponse(content=html)


# ============================================================
# SECTION 12 - APPLICATION INSTANCE
# ============================================================

app = create_application()


# ============================================================
# SECTION 13 - LOCAL DEVELOPMENT ENTRY POINT
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
# SECTION 14 - FUTURE EXPANSION NOTES
# ============================================================

#
# This file now correctly guarantees:
#
# - / redirects to /dashboard
# - /health remains Render-safe JSON
# - /static is mounted
# - /diagnostics shows whether files exist
# - /dashboard will always show either the real dashboard or
#   a visual diagnostic fallback
#
# Next required checks:
#
# - app/templates/dashboard.html must exist.
# - app/templates/dashboard.html must link:
#       <link rel="stylesheet" href="/static/css/dashboard.css" />
# - app/static/css/dashboard.css must exist.
# - requirements.txt must include:
#       fastapi
#       uvicorn
#       jinja2
#
# ============================================================


# ============================================================
# END OF FILE
# ============================================================