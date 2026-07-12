# ============================================================
# AUSSEM1
# PHASE 2.40 PART 1.02
# ENTERPRISE APPLICATION ENTRY POINT WITH PROPERTY INTELLIGENCE ROUTING
# FILE: main.py
# PURPOSE:
# Bootstrap the complete Aussem1 FastAPI application with:
# - root dashboard redirect
# - static file serving
# - dashboard routing
# - chatbot routing
# - public records readiness visibility
# - property intelligence route registration
# - health checks
# - diagnostics
# - route registry
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
# ENTERPRISE APPLICATION ACTIVE WITH PROPERTY INTELLIGENCE ROUTING
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

PLATFORM_VERSION = "0.2.2"

PLATFORM_PHASE = "PHASE 2.40 PART 1.02"

PLATFORM_STATUS = "enterprise_application_property_intelligence_routing_active"

PLATFORM_DESCRIPTION = (
    "Aussem1 is an AI-first residential real estate intelligence "
    "platform designed to turn one property address into complete, "
    "source-backed real estate intelligence."
)

PLATFORM_ENVIRONMENT = "development"

PLATFORM_OWNER = "Ryan Schuren"

PLATFORM_ASSISTANT = "Alfred"


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

WEB_DIRECTORY = APP_DIRECTORY / "web"

PUBLIC_RECORDS_DIRECTORY = APP_DIRECTORY / "public_records"

PROPERTY_INTELLIGENCE_DIRECTORY = APP_DIRECTORY / "property_intelligence"

DASHBOARD_TEMPLATE = TEMPLATE_DIRECTORY / "dashboard.html"

DASHBOARD_CSS = STATIC_CSS_DIRECTORY / "dashboard.css"

DASHBOARD_JS = STATIC_JS_DIRECTORY / "dashboard.js"

WEB_ROUTES_FILE = WEB_DIRECTORY / "routes.py"

PROPERTY_ROUTES_FILE = WEB_DIRECTORY / "property_routes.py"

PUBLIC_RECORDS_ENGINE_FILE = PUBLIC_RECORDS_DIRECTORY / "public_records_engine.py"

PROPERTY_INTELLIGENCE_MODELS_FILE = PROPERTY_INTELLIGENCE_DIRECTORY / "models.py"

PROPERTY_INTELLIGENCE_ADDRESS_FILE = (
    PROPERTY_INTELLIGENCE_DIRECTORY / "address_intelligence.py"
)

PROPERTY_INTELLIGENCE_CONFIDENCE_FILE = (
    PROPERTY_INTELLIGENCE_DIRECTORY / "confidence_engine.py"
)

PROPERTY_INTELLIGENCE_SOURCE_EXPLANATION_FILE = (
    PROPERTY_INTELLIGENCE_DIRECTORY / "source_explanation_engine.py"
)

PROPERTY_INTELLIGENCE_PROFILE_FILE = (
    PROPERTY_INTELLIGENCE_DIRECTORY / "property_profile_engine.py"
)


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

    initialize_application_state(application)
    ensure_runtime_directories()
    register_lifecycle_events(application)
    register_exception_handlers(application)
    register_static_files(application)
    register_web_router(application)
    register_property_router(application)
    register_core_routes(application)
    register_fallback_visual_routes(application)

    return application


# ============================================================
# SECTION 05 - APPLICATION STATE INITIALIZATION
# ============================================================

def initialize_application_state(application: FastAPI) -> None:
    """
    Initialize runtime state flags before router registration.

    These flags are intentionally explicit so diagnostics can show
    exactly what loaded and exactly what failed.
    """

    application.state.web_router_loaded = False
    application.state.web_router_error = None

    application.state.property_router_loaded = False
    application.state.property_router_error = None

    application.state.public_records_engine_available = False
    application.state.public_records_engine_error = None

    application.state.property_intelligence_models_available = False
    application.state.property_intelligence_models_error = None

    application.state.started_at = datetime.now(UTC).isoformat()


# ============================================================
# SECTION 06 - RUNTIME DIRECTORY CREATION
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
    WEB_DIRECTORY.mkdir(parents=True, exist_ok=True)
    PUBLIC_RECORDS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    PROPERTY_INTELLIGENCE_DIRECTORY.mkdir(parents=True, exist_ok=True)


# ============================================================
# SECTION 07 - TIME AND SERIALIZATION UTILITIES
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(UTC).isoformat()


def path_status(path: Path) -> dict[str, Any]:
    """
    Return standardized file/path status.
    """

    return {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "is_directory": path.is_dir(),
    }


def safe_import_status(
    *,
    module_name: str,
    attribute_name: str | None = None,
) -> dict[str, Any]:
    """
    Safely check whether a module or module attribute can be imported.
    """

    try:
        module = __import__(module_name, fromlist=[attribute_name] if attribute_name else [])
    except Exception as error:
        return {
            "module": module_name,
            "attribute": attribute_name,
            "available": False,
            "error": str(error),
        }

    if attribute_name:
        available = hasattr(module, attribute_name)

        return {
            "module": module_name,
            "attribute": attribute_name,
            "available": available,
            "error": None if available else f"Missing attribute: {attribute_name}",
        }

    return {
        "module": module_name,
        "attribute": attribute_name,
        "available": True,
        "error": None,
    }


# ============================================================
# SECTION 08 - LIFECYCLE EVENTS
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
        print(f"dashboard_js_exists: {DASHBOARD_JS.exists()}")
        print(f"web_router_loaded: {application.state.web_router_loaded}")
        print(f"property_router_loaded: {application.state.property_router_loaded}")
        print("=" * 72)

    @application.on_event("shutdown")
    async def shutdown_event() -> None:
        """
        Print shutdown diagnostics.
        """

        print(f"{PLATFORM_NAME} shutdown complete | version={PLATFORM_VERSION}")


# ============================================================
# SECTION 09 - EXCEPTION HANDLERS
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
                "timestamp": utc_now(),
            },
        )


# ============================================================
# SECTION 10 - STATIC FILE REGISTRATION
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
# SECTION 11 - WEB ROUTER REGISTRATION
# ============================================================

def register_web_router(application: FastAPI) -> None:
    """
    Register the general enterprise web router.

    Expected ownership:
    - /dashboard
    - /chat
    - /api/dashboard/status
    - /web/readiness
    - visual dashboard API support
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
# SECTION 12 - PROPERTY ROUTER REGISTRATION
# ============================================================

def register_property_router(application: FastAPI) -> None:
    """
    Register the dedicated property intelligence router.

    Expected ownership:
    - /properties
    - /properties/health
    - /properties/readiness
    - /properties/diagnostics
    - /properties/address/analyze
    - /properties/profile/build
    - /properties/confidence/evaluate
    - /properties/explain
    """

    try:
        from app.web.property_routes import router as property_router

        application.include_router(property_router)

        application.state.property_router_loaded = True
        application.state.property_router_error = None

    except Exception as error:
        application.state.property_router_loaded = False
        application.state.property_router_error = str(error)

        print("=" * 72)
        print(f"{PLATFORM_NAME} property router registration failed")
        print(str(error))
        print("=" * 72)


# ============================================================
# SECTION 13 - CORE ROUTES
# ============================================================

def register_core_routes(application: FastAPI) -> None:
    """
    Register core platform routes.
    """

    # --------------------------------------------------------
    # SECTION 13.01 - ROOT DASHBOARD REDIRECT
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
    # SECTION 13.02 - HEALTH CHECK
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
            "property_health": "/properties/health",
            "property_readiness": "/properties/readiness",
            "timestamp": utc_now(),
        }

    # --------------------------------------------------------
    # SECTION 13.03 - PLATFORM METADATA
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
            "environment": PLATFORM_ENVIRONMENT,
            "owner": PLATFORM_OWNER,
            "assistant": PLATFORM_ASSISTANT,
            "description": PLATFORM_DESCRIPTION,
            "core_mission": (
                "Turn one property address into complete residential "
                "real estate intelligence with strict source attribution."
            ),
            "active_systems": [
                "FastAPI Runtime",
                "Static File Serving",
                "Template Dashboard",
                "General Web Router",
                "Chatbot API",
                "Memory Store",
                "Training Logger",
                "Prompt Registry",
                "Dashboard Diagnostics",
                "Public Records Connector Foundation",
                "Public Records Engine Foundation",
                "Property Intelligence Model Layer",
                "Property Intelligence HTTP Router",
            ],
            "planned_systems": [
                "Address Intelligence Engine",
                "Confidence Engine",
                "Source Explanation Engine",
                "Property Profile Engine",
                "Authorized MLS / RESO Feed",
                "Comparable Analysis Engine",
                "Valuation Engine",
                "PostgreSQL Persistence",
                "Review Dashboard",
                "Machine Learning Operations",
            ],
            "timestamp": utc_now(),
        }

    # --------------------------------------------------------
    # SECTION 13.04 - AI STATUS
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
            "public_records_engine": (
                "foundation_active"
                if PUBLIC_RECORDS_ENGINE_FILE.exists()
                else "missing"
            ),
            "property_intelligence_models": (
                "active"
                if PROPERTY_INTELLIGENCE_MODELS_FILE.exists()
                else "missing"
            ),
            "property_router": (
                "active"
                if getattr(application.state, "property_router_loaded", False)
                else "not_loaded"
            ),
            "valuation_engine": "planned",
            "authorized_listing_feed": "not_connected",
            "message": (
                "Aussem1 AI foundation is online with visual dashboard, "
                "chat routing, public-record foundations, property model "
                "contracts, and route-level property intelligence support."
            ),
            "timestamp": utc_now(),
        }

    # --------------------------------------------------------
    # SECTION 13.05 - STATIC STATUS
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
            "timestamp": utc_now(),
        }

    # --------------------------------------------------------
    # SECTION 13.06 - TEMPLATE STATUS
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
            "timestamp": utc_now(),
        }

    # --------------------------------------------------------
    # SECTION 13.07 - PROPERTY INTELLIGENCE STATUS
    # --------------------------------------------------------

    @application.get("/property-intelligence/status")
    def property_intelligence_status() -> dict[str, Any]:
        """
        Return property-intelligence filesystem and import status.
        """

        return {
            "platform": PLATFORM_NAME,
            "phase": PLATFORM_PHASE,
            "status": "active",
            "router": {
                "loaded": getattr(application.state, "property_router_loaded", False),
                "error": getattr(application.state, "property_router_error", None),
                "file": path_status(PROPERTY_ROUTES_FILE),
            },
            "files": {
                "property_models": path_status(PROPERTY_INTELLIGENCE_MODELS_FILE),
                "address_intelligence": path_status(PROPERTY_INTELLIGENCE_ADDRESS_FILE),
                "confidence_engine": path_status(PROPERTY_INTELLIGENCE_CONFIDENCE_FILE),
                "source_explanation_engine": path_status(
                    PROPERTY_INTELLIGENCE_SOURCE_EXPLANATION_FILE
                ),
                "property_profile_engine": path_status(
                    PROPERTY_INTELLIGENCE_PROFILE_FILE
                ),
                "public_records_engine": path_status(PUBLIC_RECORDS_ENGINE_FILE),
            },
            "imports": {
                "property_models": safe_import_status(
                    module_name="app.property_intelligence.models"
                ),
                "public_records_engine": safe_import_status(
                    module_name="app.public_records.public_records_engine"
                ),
                "property_routes": safe_import_status(
                    module_name="app.web.property_routes",
                    attribute_name="router",
                ),
            },
            "governance": {
                "mock_properties_allowed": False,
                "fabricated_listing_status_allowed": False,
                "fabricated_property_values_allowed": False,
                "public_records_are_not_listing_status": True,
                "listing_status_requires_authorized_feed": True,
                "assessment_is_not_market_value": True,
            },
            "timestamp": utc_now(),
        }

    # --------------------------------------------------------
    # SECTION 13.08 - FULL DIAGNOSTICS
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
            "started_at": getattr(application.state, "started_at", None),
            "web_router": {
                "loaded": getattr(application.state, "web_router_loaded", False),
                "error": getattr(application.state, "web_router_error", None),
                "file": path_status(WEB_ROUTES_FILE),
            },
            "property_router": {
                "loaded": getattr(
                    application.state,
                    "property_router_loaded",
                    False,
                ),
                "error": getattr(
                    application.state,
                    "property_router_error",
                    None,
                ),
                "file": path_status(PROPERTY_ROUTES_FILE),
            },
            "paths": {
                "project_root": str(PROJECT_ROOT),
                "app_directory": str(APP_DIRECTORY),
                "static_directory": str(STATIC_DIRECTORY),
                "static_css_directory": str(STATIC_CSS_DIRECTORY),
                "static_js_directory": str(STATIC_JS_DIRECTORY),
                "template_directory": str(TEMPLATE_DIRECTORY),
                "data_directory": str(DATA_DIRECTORY),
                "web_directory": str(WEB_DIRECTORY),
                "public_records_directory": str(PUBLIC_RECORDS_DIRECTORY),
                "property_intelligence_directory": str(
                    PROPERTY_INTELLIGENCE_DIRECTORY
                ),
                "dashboard_template": str(DASHBOARD_TEMPLATE),
                "dashboard_css": str(DASHBOARD_CSS),
                "dashboard_js": str(DASHBOARD_JS),
                "property_routes": str(PROPERTY_ROUTES_FILE),
                "public_records_engine": str(PUBLIC_RECORDS_ENGINE_FILE),
                "property_intelligence_models": str(
                    PROPERTY_INTELLIGENCE_MODELS_FILE
                ),
            },
            "exists": {
                "project_root": PROJECT_ROOT.exists(),
                "app_directory": APP_DIRECTORY.exists(),
                "static_directory": STATIC_DIRECTORY.exists(),
                "static_css_directory": STATIC_CSS_DIRECTORY.exists(),
                "static_js_directory": STATIC_JS_DIRECTORY.exists(),
                "template_directory": TEMPLATE_DIRECTORY.exists(),
                "data_directory": DATA_DIRECTORY.exists(),
                "web_directory": WEB_DIRECTORY.exists(),
                "public_records_directory": PUBLIC_RECORDS_DIRECTORY.exists(),
                "property_intelligence_directory": (
                    PROPERTY_INTELLIGENCE_DIRECTORY.exists()
                ),
                "dashboard_template": DASHBOARD_TEMPLATE.exists(),
                "dashboard_css": DASHBOARD_CSS.exists(),
                "dashboard_js": DASHBOARD_JS.exists(),
                "property_routes": PROPERTY_ROUTES_FILE.exists(),
                "public_records_engine": PUBLIC_RECORDS_ENGINE_FILE.exists(),
                "property_intelligence_models": (
                    PROPERTY_INTELLIGENCE_MODELS_FILE.exists()
                ),
            },
            "render": {
                "build_command": "pip install -r requirements.txt",
                "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            },
            "timestamp": utc_now(),
        }

    # --------------------------------------------------------
    # SECTION 13.09 - ENTERPRISE ROUTE REGISTRY
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
            "router_status": {
                "web_router_loaded": getattr(
                    application.state,
                    "web_router_loaded",
                    False,
                ),
                "web_router_error": getattr(
                    application.state,
                    "web_router_error",
                    None,
                ),
                "property_router_loaded": getattr(
                    application.state,
                    "property_router_loaded",
                    False,
                ),
                "property_router_error": getattr(
                    application.state,
                    "property_router_error",
                    None,
                ),
            },
            "active_routes": {
                "core": [
                    "/",
                    "/health",
                    "/platform",
                    "/ai/status",
                    "/property-intelligence/status",
                    "/routes",
                    "/diagnostics",
                    "/static/status",
                    "/templates/status",
                ],
                "visual": [
                    "/dashboard",
                ],
                "general_web_router": [
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
                "property_intelligence_router": [
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
                    "/properties/batch/profile/build",
                    "/properties/{property_id}",
                ],
            },
            "governance": {
                "rule_1": "Root route must show or redirect to a visual application.",
                "rule_2": "Static files must be mounted at /static.",
                "rule_3": "Dashboard template must live in app/templates.",
                "rule_4": "Dashboard CSS must live in app/static/css.",
                "rule_5": "Dashboard JavaScript must live in app/static/js.",
                "rule_6": "Routes must stay thin and delegate intelligence to service modules.",
                "rule_7": "Property routes must not fabricate MLS, public-record, or valuation facts.",
                "rule_8": "Listing status requires authorized listing-source integration.",
                "rule_9": "Assessment data is not current market value.",
            },
            "timestamp": utc_now(),
        }


# ============================================================
# SECTION 14 - FALLBACK VISUAL ROUTES
# ============================================================

def register_fallback_visual_routes(application: FastAPI) -> None:
    """
    Register fallback /dashboard route if the web router failed.

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
                    width: min(940px, calc(100% - 40px));
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
                .grid {{
                    display: grid;
                    gap: 12px;
                    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                    margin-top: 22px;
                }}
                .pill {{
                    border: 1px solid rgba(148,163,184,.18);
                    background: rgba(2,6,23,.55);
                    border-radius: 16px;
                    padding: 14px;
                    color: #cbd5e1;
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
                <div class="grid">
                    <div class="pill">
                        <a href="/diagnostics">Diagnostics</a>
                    </div>
                    <div class="pill">
                        <a href="/templates/status">Template Status</a>
                    </div>
                    <div class="pill">
                        <a href="/static/status">Static Status</a>
                    </div>
                    <div class="pill">
                        <a href="/property-intelligence/status">Property Status</a>
                    </div>
                </div>
            </main>
        </body>
        </html>
        """

        return HTMLResponse(content=html)


# ============================================================
# SECTION 15 - APPLICATION INSTANCE
# ============================================================

app = create_application()


# ============================================================
# SECTION 16 - LOCAL DEVELOPMENT ENTRY POINT
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
# SECTION 17 - OPERATIONAL NOTES
# ============================================================

#
# This file now guarantees:
#
# - / redirects to /dashboard
# - /health remains Render-safe JSON
# - /static is mounted
# - /diagnostics shows filesystem and router readiness
# - /property-intelligence/status shows property-intelligence readiness
# - /properties routes are registered when app/web/property_routes.py imports
# - /dashboard will always show either the real dashboard or a fallback page
#
# Important source-governance rule:
#
# Public records can support parcel, tax, GIS, MOD-IV, recorded-document,
# and ownership-reference context. They do not prove active listing status,
# under-contract status, current listing price, or days on market.
#
# ============================================================


# ============================================================
# END OF FILE
# ============================================================