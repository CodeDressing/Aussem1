# ============================================================
# AUSSEM1
# PHASE 1.00 PART 9.00
# ENTERPRISE VISUAL INTELLIGENCE DASHBOARD ROUTES
# FILE: app/web/routes.py
# PURPOSE:
# Expose API routes and the first live visual dashboard for
# Aussem1's chatbot, memory system, training logger, prompt
# architecture, and property intelligence foundation.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# ENTERPRISE VISUAL FOUNDATION ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

from dataclasses import asdict
from dataclasses import is_dataclass
from datetime import UTC
from datetime import datetime
from typing import Any

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.chatbot.chat_engine import ChatEngine
from app.chatbot.chat_engine import ChatRequest


# ============================================================
# SECTION 02 - ROUTER CONFIGURATION
# ============================================================

router = APIRouter()

ROUTES_NAME = "Aussem1 Enterprise Web Routes"

ROUTES_VERSION = "0.2.0"

ROUTES_PHASE = "PHASE 1.00 PART 9.00"

ROUTES_STATUS = "enterprise_visual_foundation_active"


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


class FeedbackRequestBody(BaseModel):
    """
    HTTP request body for future feedback capture.
    """

    record_id: str
    feedback: str
    corrected_answer: str | None = None


# ============================================================
# SECTION 05 - UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(UTC).isoformat()


def serialize_response(value: Any) -> Any:
    """
    Safely serialize dataclass or plain objects.
    """

    if is_dataclass(value):
        return asdict(value)

    return value


def safe_call(
    callable_object: Any,
    fallback: Any,
) -> Any:
    """
    Safely call optional enterprise methods during early
    development while modules are evolving.
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
# SECTION 06 - WEB HEALTH CHECK
# ============================================================

@router.get("/web/health")
def web_health() -> dict:
    """
    Verify that the Aussem1 web routing layer is active.
    """

    return {
        "module": "web",
        "status": "ok",
        "routes_name": ROUTES_NAME,
        "version": ROUTES_VERSION,
        "phase": ROUTES_PHASE,
        "routes_status": ROUTES_STATUS,
        "timestamp": utc_now(),
    }


# ============================================================
# SECTION 07 - DASHBOARD PAGE
# ============================================================

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    """
    Return the first live visual dashboard for Aussem1.

    This dashboard is intentionally self-contained for Phase 1 so
    Render can display a working product immediately.

    Future phases should extract:
    - app/templates/dashboard.html
    - app/static/css/dashboard.css
    - app/static/js/dashboard.js
    """

    return HTMLResponse(content=DASHBOARD_HTML)


# ============================================================
# SECTION 08 - DASHBOARD BOOTSTRAP API
# ============================================================

@router.get("/api/dashboard/bootstrap")
def dashboard_bootstrap() -> dict:
    """
    Return dashboard bootstrap data.
    """

    return {
        "platform": "Aussem1",
        "routes_name": ROUTES_NAME,
        "routes_version": ROUTES_VERSION,
        "routes_phase": ROUTES_PHASE,
        "routes_status": ROUTES_STATUS,
        "dashboard": {
            "name": "Aussem1 Intelligence Dashboard",
            "status": "active",
            "purpose": (
                "Visualize the live chatbot, memory system, training logger, "
                "and property intelligence foundation."
            ),
        },
        "active_modules": [
            "FastAPI Runtime",
            "Chat Engine",
            "Memory Store",
            "Training Logger",
            "Prompt Registry",
            "Property Knowledge Foundation",
            "Render Deployment",
        ],
        "planned_modules": [
            "Property Lookup Engine",
            "Public Records Engine",
            "Comparable Analysis Engine",
            "Valuation Engine",
            "Learning Engine",
            "PostgreSQL Persistence",
            "AI Review Dashboard",
        ],
        "timestamp": utc_now(),
    }


# ============================================================
# SECTION 09 - DASHBOARD STATUS API
# ============================================================

@router.get("/api/dashboard/status")
def dashboard_status() -> dict:
    """
    Return live dashboard status across all core systems.
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

    return {
        "platform": "Aussem1",
        "status": "online",
        "phase": ROUTES_PHASE,
        "timestamp": utc_now(),
        "systems": {
            "web_routes": {
                "status": "active",
                "version": ROUTES_VERSION,
            },
            "chat_engine": engine_status,
            "training_logger": training_summary,
            "memory_store": memory_health,
        },
    }


# ============================================================
# SECTION 10 - CHAT HEALTH CHECK
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
        "timestamp": utc_now(),
    }


# ============================================================
# SECTION 11 - CHAT ENDPOINT
# ============================================================

@router.post("/chat")
def chat(
    request_body: ChatRequestBody,
) -> dict:
    """
    Process a chatbot request.
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


# ============================================================
# SECTION 12 - TRAINING STATUS ENDPOINT
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

    return {
        "module": "training_logger",
        "status": "active",
        "summary": summary,
        "total_interactions": chat_engine.training_logger.total_interactions(),
        "failed_interactions": chat_engine.training_logger.failed_interactions(),
        "unanswered_questions": chat_engine.training_logger.unanswered_questions(),
        "timestamp": utc_now(),
    }


# ============================================================
# SECTION 13 - TRAINING REVIEW QUEUE ENDPOINT
# ============================================================

@router.get("/chat/review-queue")
def training_review_queue() -> dict:
    """
    Return training review queue.
    """

    queue = safe_call(
        lambda: chat_engine.training_logger.review_queue(limit=25),
        fallback=[],
    )

    return {
        "module": "training_review_queue",
        "status": "active",
        "items": queue,
        "count": len(queue) if isinstance(queue, list) else 0,
        "timestamp": utc_now(),
    }


# ============================================================
# SECTION 14 - TRAINING EXPORT ENDPOINT
# ============================================================

@router.get("/chat/training-export")
def training_export() -> dict:
    """
    Export current training dataset.
    """

    dataset = safe_call(
        chat_engine.training_logger.export_training_dataset,
        fallback=[],
    )

    return {
        "module": "training_export",
        "status": "active",
        "dataset": dataset,
        "count": len(dataset) if isinstance(dataset, list) else 0,
        "timestamp": utc_now(),
    }


# ============================================================
# SECTION 15 - MEMORY STATUS ENDPOINT
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

    return {
        "module": "memory_store",
        "status": "active",
        "health": memory_health,
        "total_messages": chat_engine.memory_store.total_messages(),
        "total_sessions": chat_engine.memory_store.total_sessions(),
        "timestamp": utc_now(),
    }


# ============================================================
# SECTION 16 - MEMORY SEARCH ENDPOINT
# ============================================================

@router.get("/chat/memory-search")
def memory_search(
    query: str,
) -> dict:
    """
    Search chatbot memory.
    """

    results = safe_call(
        lambda: chat_engine.memory_store.search_memory(query=query, limit=20),
        fallback=[],
    )

    return {
        "module": "memory_search",
        "query": query,
        "results": results,
        "count": len(results) if isinstance(results, list) else 0,
        "timestamp": utc_now(),
    }


# ============================================================
# SECTION 17 - ROUTE REGISTRY ENDPOINT
# ============================================================

@router.get("/web/route-registry")
def web_route_registry() -> dict:
    """
    Return enterprise route registry for the web module.
    """

    return {
        "routes_name": ROUTES_NAME,
        "version": ROUTES_VERSION,
        "phase": ROUTES_PHASE,
        "status": ROUTES_STATUS,
        "visual_routes": [
            {
                "path": "/dashboard",
                "method": "GET",
                "purpose": "Live Aussem1 visual intelligence dashboard.",
            },
        ],
        "api_routes": [
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
            {
                "path": "/chat",
                "method": "POST",
                "purpose": "Primary chatbot endpoint.",
            },
            {
                "path": "/chat/training-status",
                "method": "GET",
                "purpose": "Training logger analytics.",
            },
            {
                "path": "/chat/memory-status",
                "method": "GET",
                "purpose": "Memory store analytics.",
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
                "method": "GET",
                "purpose": "Basic memory search.",
            },
        ],
        "timestamp": utc_now(),
    }


# ============================================================
# SECTION 18 - ENTERPRISE DASHBOARD HTML
# ============================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Aussem1 Intelligence Dashboard</title>

    <style>
        :root {
            --bg: #020617;
            --panel: rgba(15, 23, 42, 0.92);
            --panel-2: rgba(30, 41, 59, 0.82);
            --line: rgba(148, 163, 184, 0.18);
            --text: #f8fafc;
            --muted: #94a3b8;
            --blue: #38bdf8;
            --green: #34d399;
            --yellow: #fbbf24;
            --red: #fb7185;
            --purple: #a78bfa;
            --shadow: 0 30px 90px rgba(0,0,0,.45);
            --radius: 26px;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.24), transparent 32%),
                radial-gradient(circle at top right, rgba(167, 139, 250, 0.18), transparent 30%),
                linear-gradient(135deg, #020617, #0f172a 46%, #020617);
            color: var(--text);
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .shell {
            width: min(1500px, calc(100% - 40px));
            margin: 0 auto;
            padding: 34px 0 60px;
        }

        .hero {
            display: grid;
            grid-template-columns: 1.25fr .75fr;
            gap: 22px;
            align-items: stretch;
            margin-bottom: 22px;
        }

        .hero-card,
        .panel {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            backdrop-filter: blur(18px);
        }

        .hero-card {
            padding: 38px;
            position: relative;
            overflow: hidden;
        }

        .hero-card::after {
            content: "";
            position: absolute;
            inset: auto -120px -180px auto;
            width: 360px;
            height: 360px;
            background: radial-gradient(circle, rgba(56,189,248,.22), transparent 68%);
            pointer-events: none;
        }

        .eyebrow {
            color: var(--blue);
            letter-spacing: .18em;
            text-transform: uppercase;
            font-size: 12px;
            font-weight: 800;
            margin-bottom: 16px;
        }

        h1 {
            margin: 0;
            font-size: clamp(38px, 6vw, 74px);
            line-height: .95;
            letter-spacing: -0.06em;
        }

        .lead {
            margin: 22px 0 0;
            color: var(--muted);
            max-width: 760px;
            font-size: 18px;
            line-height: 1.7;
        }

        .status-card {
            padding: 28px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .live-pill {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 10px 14px;
            border-radius: 999px;
            background: rgba(52, 211, 153, .10);
            border: 1px solid rgba(52, 211, 153, .24);
            color: var(--green);
            font-weight: 800;
            width: fit-content;
        }

        .pulse {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: var(--green);
            box-shadow: 0 0 0 7px rgba(52,211,153,.11);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 22px;
        }

        .panel {
            padding: 24px;
        }

        .span-4 { grid-column: span 4; }
        .span-5 { grid-column: span 5; }
        .span-7 { grid-column: span 7; }
        .span-8 { grid-column: span 8; }
        .span-12 { grid-column: span 12; }

        .panel-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 14px;
            margin-bottom: 18px;
        }

        .panel-title h2 {
            margin: 0;
            font-size: 18px;
            letter-spacing: -0.02em;
        }

        .subtle {
            color: var(--muted);
            font-size: 13px;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 14px;
        }

        .metric {
            padding: 18px;
            border-radius: 20px;
            background: var(--panel-2);
            border: 1px solid var(--line);
        }

        .metric .label {
            color: var(--muted);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: .12em;
            font-weight: 800;
        }

        .metric .value {
            font-size: 30px;
            font-weight: 900;
            margin-top: 8px;
            letter-spacing: -0.04em;
        }

        .chat-box {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .chat-stream {
            min-height: 360px;
            max-height: 520px;
            overflow-y: auto;
            padding: 18px;
            border-radius: 22px;
            background: rgba(2, 6, 23, .55);
            border: 1px solid var(--line);
        }

        .message {
            margin-bottom: 14px;
            display: flex;
        }

        .message.user {
            justify-content: flex-end;
        }

        .bubble {
            max-width: 82%;
            padding: 14px 16px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.55;
            white-space: pre-wrap;
        }

        .user .bubble {
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: white;
        }

        .assistant .bubble {
            background: rgba(30, 41, 59, .95);
            border: 1px solid var(--line);
            color: #e2e8f0;
        }

        .chat-form {
            display: grid;
            grid-template-columns: 1fr 1fr auto;
            gap: 12px;
        }

        input,
        button {
            border: 0;
            border-radius: 16px;
            font: inherit;
        }

        input {
            padding: 16px 16px;
            background: rgba(15, 23, 42, .92);
            border: 1px solid var(--line);
            color: var(--text);
            outline: none;
        }

        input:focus {
            border-color: rgba(56,189,248,.7);
            box-shadow: 0 0 0 4px rgba(56,189,248,.12);
        }

        button {
            padding: 16px 22px;
            background: linear-gradient(135deg, #38bdf8, #2563eb);
            color: white;
            font-weight: 900;
            cursor: pointer;
        }

        button:hover {
            filter: brightness(1.1);
        }

        .log-list {
            display: grid;
            gap: 10px;
        }

        .log-item {
            padding: 14px;
            border-radius: 18px;
            background: rgba(15, 23, 42, .66);
            border: 1px solid var(--line);
            color: var(--muted);
            font-size: 13px;
            line-height: 1.5;
        }

        .tag {
            display: inline-flex;
            padding: 7px 10px;
            border-radius: 999px;
            border: 1px solid var(--line);
            color: var(--muted);
            font-size: 12px;
            margin: 4px 5px 4px 0;
        }

        .tag.green { color: var(--green); border-color: rgba(52,211,153,.25); }
        .tag.blue { color: var(--blue); border-color: rgba(56,189,248,.25); }
        .tag.yellow { color: var(--yellow); border-color: rgba(251,191,36,.25); }
        .tag.purple { color: var(--purple); border-color: rgba(167,139,250,.25); }

        pre {
            margin: 0;
            white-space: pre-wrap;
            word-break: break-word;
            color: #cbd5e1;
            font-size: 12px;
            line-height: 1.5;
            max-height: 390px;
            overflow: auto;
        }

        .footer {
            margin-top: 24px;
            color: var(--muted);
            font-size: 13px;
            text-align: center;
        }

        @media (max-width: 1000px) {
            .hero {
                grid-template-columns: 1fr;
            }

            .span-4,
            .span-5,
            .span-7,
            .span-8,
            .span-12 {
                grid-column: span 12;
            }

            .chat-form {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>

<body>
    <main class="shell">
        <section class="hero">
            <div class="hero-card">
                <div class="eyebrow">Aussem1 Live Intelligence System</div>
                <h1>One Address.<br />Unlimited Intelligence.</h1>
                <p class="lead">
                    This dashboard proves the deployed Aussem1 platform is not only online,
                    but actively routing conversations through the chatbot, memory store,
                    training logger, and real estate intelligence foundation.
                </p>
            </div>

            <div class="status-card hero-card">
                <div>
                    <div class="live-pill"><span class="pulse"></span> LIVE ON RENDER</div>
                    <p class="lead" style="font-size:15px;">
                        FastAPI, chatbot routing, memory analytics, training metrics,
                        and visual monitoring are connected.
                    </p>
                </div>
                <div>
                    <span class="tag green">API Online</span>
                    <span class="tag blue">Chat Active</span>
                    <span class="tag purple">Memory Active</span>
                    <span class="tag yellow">Training Active</span>
                </div>
            </div>
        </section>

        <section class="grid">
            <div class="panel span-7">
                <div class="panel-title">
                    <h2>Live AI Chat Console</h2>
                    <span class="subtle" id="sessionId">Session: new</span>
                </div>

                <div class="chat-box">
                    <div class="chat-stream" id="chatStream">
                        <div class="message assistant">
                            <div class="bubble">
                                Welcome to Aussem1. Ask about property value, status,
                                public records, comparable homes, or market intelligence.
                            </div>
                        </div>
                    </div>

                    <form class="chat-form" id="chatForm">
                        <input id="propertyAddress" placeholder="Optional property address" />
                        <input id="messageInput" placeholder="Ask Aussem1 a real estate question..." required />
                        <button type="submit">Analyze</button>
                    </form>
                </div>
            </div>

            <div class="panel span-5">
                <div class="panel-title">
                    <h2>System Metrics</h2>
                    <span class="subtle" id="lastUpdated">Loading...</span>
                </div>

                <div class="metric-grid">
                    <div class="metric">
                        <div class="label">Messages</div>
                        <div class="value" id="metricMessages">0</div>
                    </div>

                    <div class="metric">
                        <div class="label">Sessions</div>
                        <div class="value" id="metricSessions">0</div>
                    </div>

                    <div class="metric">
                        <div class="label">Training</div>
                        <div class="value" id="metricTraining">0</div>
                    </div>

                    <div class="metric">
                        <div class="label">Review Queue</div>
                        <div class="value" id="metricReview">0</div>
                    </div>
                </div>
            </div>

            <div class="panel span-4">
                <div class="panel-title">
                    <h2>Active Modules</h2>
                </div>
                <div id="moduleList">
                    <span class="tag green">FastAPI Runtime</span>
                    <span class="tag blue">Chat Engine</span>
                    <span class="tag purple">Memory Store</span>
                    <span class="tag yellow">Training Logger</span>
                </div>
            </div>

            <div class="panel span-4">
                <div class="panel-title">
                    <h2>Training Intelligence</h2>
                </div>
                <div class="log-list" id="trainingPanel">
                    <div class="log-item">Loading training data...</div>
                </div>
            </div>

            <div class="panel span-4">
                <div class="panel-title">
                    <h2>Memory Intelligence</h2>
                </div>
                <div class="log-list" id="memoryPanel">
                    <div class="log-item">Loading memory data...</div>
                </div>
            </div>

            <div class="panel span-12">
                <div class="panel-title">
                    <h2>Live System Payload</h2>
                    <span class="subtle">Diagnostic view</span>
                </div>
                <pre id="rawPayload">Loading...</pre>
            </div>
        </section>

        <div class="footer">
            Aussem1 · Enterprise Real Estate Intelligence Platform · Phase 1 Visual Foundation
        </div>
    </main>

    <script>
        let currentSessionId = null;

        const chatStream = document.getElementById("chatStream");
        const chatForm = document.getElementById("chatForm");
        const messageInput = document.getElementById("messageInput");
        const propertyAddress = document.getElementById("propertyAddress");
        const sessionIdLabel = document.getElementById("sessionId");

        function addMessage(role, text) {
            const wrapper = document.createElement("div");
            wrapper.className = `message ${role}`;

            const bubble = document.createElement("div");
            bubble.className = "bubble";
            bubble.textContent = text;

            wrapper.appendChild(bubble);
            chatStream.appendChild(wrapper);
            chatStream.scrollTop = chatStream.scrollHeight;
        }

        async function refreshDashboard() {
            try {
                const response = await fetch("/api/dashboard/status");
                const data = await response.json();

                document.getElementById("rawPayload").textContent =
                    JSON.stringify(data, null, 2);

                const memory = data.systems?.memory_store?.health || {};
                const training = data.systems?.training_logger || {};

                document.getElementById("metricMessages").textContent =
                    memory.total_messages ?? 0;

                document.getElementById("metricSessions").textContent =
                    memory.total_sessions ?? 0;

                document.getElementById("metricTraining").textContent =
                    training.total_interactions ?? 0;

                document.getElementById("metricReview").textContent =
                    training.review_queue_size ?? 0;

                document.getElementById("lastUpdated").textContent =
                    new Date().toLocaleTimeString();

                document.getElementById("trainingPanel").innerHTML = `
                    <div class="log-item">Total interactions: ${training.total_interactions ?? 0}</div>
                    <div class="log-item">Failed interactions: ${training.failed_interactions ?? 0}</div>
                    <div class="log-item">Average confidence: ${training.average_confidence ?? 0}</div>
                    <div class="log-item">Review queue size: ${training.review_queue_size ?? 0}</div>
                `;

                document.getElementById("memoryPanel").innerHTML = `
                    <div class="log-item">Total messages: ${memory.total_messages ?? 0}</div>
                    <div class="log-item">Total sessions: ${memory.total_sessions ?? 0}</div>
                    <div class="log-item">Total properties: ${memory.total_properties ?? 0}</div>
                    <div class="log-item">Knowledge items: ${memory.total_knowledge_items ?? 0}</div>
                `;
            } catch (error) {
                document.getElementById("rawPayload").textContent =
                    "Dashboard refresh failed: " + error;
            }
        }

        chatForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const message = messageInput.value.trim();
            const address = propertyAddress.value.trim();

            if (!message) return;

            addMessage("user", message);
            messageInput.value = "";

            try {
                const response = await fetch("/chat", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        message: message,
                        property_address: address || null,
                        session_id: currentSessionId,
                        user_id: "dashboard-user"
                    })
                });

                const data = await response.json();

                currentSessionId = data.session_id || currentSessionId;
                sessionIdLabel.textContent = "Session: " + currentSessionId;

                const answer = data.response || JSON.stringify(data, null, 2);

                addMessage("assistant", answer);

                await refreshDashboard();
            } catch (error) {
                addMessage("assistant", "Chat request failed: " + error);
            }
        });

        refreshDashboard();
        setInterval(refreshDashboard, 10000);
    </script>
</body>
</html>
"""


# ============================================================
# SECTION 19 - FUTURE EXPANSION NOTES
# ============================================================

#
# Planned next split:
#
# app/templates/dashboard.html
# app/static/css/dashboard.css
# app/static/js/dashboard.js
#
# This Phase 1 file intentionally keeps the dashboard embedded so
# the live Render deployment immediately shows a working visual
# application without requiring template/static routing first.
#
# ============================================================


# ============================================================
# END OF FILE
# ============================================================