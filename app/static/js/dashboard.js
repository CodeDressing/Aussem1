/* ============================================================
AUSSEM1
PHASE 2.00 PART 1.00
ENTERPRISE DASHBOARD CONTROL SYSTEM
FILE: app/static/js/dashboard.js
PURPOSE:
Browser-side control system for the Aussem1 live dashboard,
chat console, memory monitor, training monitor, route diagnostics,
property preview workflow, API health checks, and future AI/ML
dashboard operations.

AUTHOR:
Ryan Schuren

ASSISTANT:
Alfred

STATUS:
PHASE 2 DASHBOARD CONTROL ACTIVE
============================================================ */


/* ============================================================
SECTION 01 - ENTERPRISE RUNTIME CONFIGURATION
============================================================ */

const AUSSEM1_DASHBOARD = {
    platform: "Aussem1",
    phase: "PHASE 2.00 PART 1.00",
    version: "0.1.0",
    status: "phase_2_dashboard_control_active",
    api: {
        dashboardStatus: "/api/dashboard/status",
        dashboardBootstrap: "/api/dashboard/bootstrap",
        chat: "/chat",
        chatTrace: "/chat/trace",
        chatHealth: "/chat/health",
        trainingStatus: "/chat/training-status",
        reviewQueue: "/chat/review-queue",
        trainingExport: "/chat/training-export",
        memoryStatus: "/chat/memory-status",
        memorySearch: "/chat/memory-search",
        promptStatus: "/chat/prompt-status",
        propertyPreview: "/properties/preview",
        webReadiness: "/web/readiness",
        webDiagnostics: "/web/diagnostics",
        routeRegistry: "/web/route-registry",
        health: "/health",
        platform: "/platform",
        aiStatus: "/ai/status",
        diagnostics: "/diagnostics"
    },
    refresh: {
        statusMs: 10000,
        healthMs: 20000,
        maxChatMessages: 80
    },
    selectors: {
        chatStream: "chatStream",
        chatForm: "chatForm",
        messageInput: "messageInput",
        propertyAddress: "propertyAddress",
        sessionId: "sessionId",
        lastUpdated: "lastUpdated",
        metricMessages: "metricMessages",
        metricSessions: "metricSessions",
        metricTraining: "metricTraining",
        metricReview: "metricReview",
        trainingPanel: "trainingPanel",
        memoryPanel: "memoryPanel",
        rawPayload: "rawPayload"
    }
};


/* ============================================================
SECTION 02 - APPLICATION STATE
============================================================ */

const dashboardState = {
    initialized: false,
    currentSessionId: null,
    currentUserId: "dashboard-user",
    currentPropertyAddress: null,
    lastStatusPayload: null,
    lastBootstrapPayload: null,
    lastHealthPayload: null,
    lastError: null,
    polling: {
        statusIntervalId: null,
        healthIntervalId: null
    },
    counters: {
        messagesSent: 0,
        messagesReceived: 0,
        refreshes: 0,
        errors: 0
    },
    ui: {
        isChatBusy: false,
        isRefreshing: false
    }
};


/* ============================================================
SECTION 03 - SAFE DOM UTILITIES
============================================================ */

function byId(id) {
    return document.getElementById(id);
}


function exists(id) {
    return byId(id) !== null;
}


function setText(id, value) {
    const element = byId(id);

    if (!element) {
        return;
    }

    element.textContent = String(value ?? "");
}


function setHTML(id, value) {
    const element = byId(id);

    if (!element) {
        return;
    }

    element.innerHTML = value;
}


function safeNumber(value, fallback = 0) {
    if (value === undefined || value === null || Number.isNaN(Number(value))) {
        return fallback;
    }

    return value;
}


function safeString(value, fallback = "") {
    if (value === undefined || value === null) {
        return fallback;
    }

    return String(value);
}


function prettyJson(value) {
    try {
        return JSON.stringify(value, null, 2);
    } catch (error) {
        return String(value);
    }
}


function nowLabel() {
    return new Date().toLocaleTimeString();
}


/* ============================================================
SECTION 04 - NETWORK UTILITIES
============================================================ */

async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
        cache: "no-store",
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    const contentType = response.headers.get("content-type") || "";

    let payload;

    if (contentType.includes("application/json")) {
        payload = await response.json();
    } else {
        payload = await response.text();
    }

    if (!response.ok) {
        throw new Error(
            `Request failed ${response.status}: ${safeString(payload.detail || payload)}`
        );
    }

    return payload;
}


async function postJson(url, body) {
    return fetchJson(url, {
        method: "POST",
        body: JSON.stringify(body)
    });
}


/* ============================================================
SECTION 05 - MESSAGE RENDERING
============================================================ */

function createMessageElement(role, text, metadata = {}) {
    const wrapper = document.createElement("div");
    wrapper.className = `message ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    if (metadata.intent || metadata.confidence || metadata.timestamp) {
        const meta = document.createElement("div");
        meta.className = "message-meta";

        const pieces = [];

        if (metadata.intent) {
            pieces.push(`Intent: ${metadata.intent}`);
        }

        if (metadata.confidence !== undefined && metadata.confidence !== null) {
            pieces.push(`Confidence: ${metadata.confidence}`);
        }

        if (metadata.timestamp) {
            pieces.push(metadata.timestamp);
        }

        meta.textContent = pieces.join(" · ");
        bubble.appendChild(meta);
    }

    wrapper.appendChild(bubble);

    return wrapper;
}


function addMessage(role, text, metadata = {}) {
    const chatStream = byId(AUSSEM1_DASHBOARD.selectors.chatStream);

    if (!chatStream) {
        return;
    }

    const messageElement = createMessageElement(role, text, metadata);
    chatStream.appendChild(messageElement);

    while (chatStream.children.length > AUSSEM1_DASHBOARD.refresh.maxChatMessages) {
        chatStream.removeChild(chatStream.firstElementChild);
    }

    chatStream.scrollTop = chatStream.scrollHeight;
}


function addSystemMessage(text) {
    addMessage("assistant", text, {
        intent: "system",
        timestamp: nowLabel()
    });
}


function clearChat() {
    const chatStream = byId(AUSSEM1_DASHBOARD.selectors.chatStream);

    if (!chatStream) {
        return;
    }

    chatStream.innerHTML = "";

    addSystemMessage(
        "Aussem1 chat console reset. Ask about property value, status, public records, comparable homes, or market intelligence."
    );
}


/* ============================================================
SECTION 06 - RESPONSE NORMALIZATION
============================================================ */

function normalizeChatResponse(payload) {
    if (!payload || typeof payload !== "object") {
        return {
            response: safeString(payload, "No response returned."),
            session_id: dashboardState.currentSessionId,
            intent: null,
            confidence: null
        };
    }

    return {
        response:
            payload.response ||
            payload.answer ||
            payload.message ||
            payload.data?.response ||
            payload.data?.answer ||
            prettyJson(payload),
        session_id:
            payload.session_id ||
            payload.data?.session_id ||
            dashboardState.currentSessionId,
        intent:
            payload.intent ||
            payload.data?.intent ||
            null,
        confidence:
            payload.confidence ||
            payload.data?.confidence ||
            null,
        raw: payload
    };
}


function normalizeDashboardStatus(payload) {
    const systems = payload?.systems || payload?.data?.systems || {};
    const memoryStore = systems.memory_store || {};
    const trainingLogger = systems.training_logger || {};
    const chatEngine = systems.chat_engine || {};
    const promptRegistry = systems.prompt_registry || {};

    return {
        raw: payload,
        systems,
        memoryHealth: memoryStore.health || memoryStore || {},
        trainingSummary: trainingLogger || {},
        chatEngine,
        promptRegistry,
        timestamp: payload?.timestamp || payload?.data?.timestamp || null
    };
}


/* ============================================================
SECTION 07 - METRIC RENDERING
============================================================ */

function renderMetric(id, value) {
    setText(id, safeNumber(value));
}


function renderDashboardMetrics(status) {
    const memory = status.memoryHealth || {};
    const training = status.trainingSummary || {};

    renderMetric(
        AUSSEM1_DASHBOARD.selectors.metricMessages,
        memory.total_messages
    );

    renderMetric(
        AUSSEM1_DASHBOARD.selectors.metricSessions,
        memory.total_sessions
    );

    renderMetric(
        AUSSEM1_DASHBOARD.selectors.metricTraining,
        training.total_interactions
    );

    renderMetric(
        AUSSEM1_DASHBOARD.selectors.metricReview,
        training.review_queue_size
    );

    setText(
        AUSSEM1_DASHBOARD.selectors.lastUpdated,
        `Updated ${nowLabel()}`
    );
}


function renderTrainingPanel(training) {
    setHTML(
        AUSSEM1_DASHBOARD.selectors.trainingPanel,
        `
        <div class="log-item">
            <strong>Total interactions:</strong> ${safeNumber(training.total_interactions)}
        </div>
        <div class="log-item">
            <strong>Failed interactions:</strong> ${safeNumber(training.failed_interactions)}
        </div>
        <div class="log-item">
            <strong>Average confidence:</strong> ${safeNumber(training.average_confidence)}
        </div>
        <div class="log-item">
            <strong>Review queue size:</strong> ${safeNumber(training.review_queue_size)}
        </div>
        `
    );
}


function renderMemoryPanel(memory) {
    setHTML(
        AUSSEM1_DASHBOARD.selectors.memoryPanel,
        `
        <div class="log-item">
            <strong>Total messages:</strong> ${safeNumber(memory.total_messages)}
        </div>
        <div class="log-item">
            <strong>Total sessions:</strong> ${safeNumber(memory.total_sessions)}
        </div>
        <div class="log-item">
            <strong>Total properties:</strong> ${safeNumber(memory.total_properties)}
        </div>
        <div class="log-item">
            <strong>Knowledge items:</strong> ${safeNumber(memory.total_knowledge_items)}
        </div>
        `
    );
}


function renderRawPayload(payload) {
    setText(
        AUSSEM1_DASHBOARD.selectors.rawPayload,
        prettyJson(payload)
    );
}


/* ============================================================
SECTION 08 - DASHBOARD REFRESH ENGINE
============================================================ */

async function refreshDashboard() {
    if (dashboardState.ui.isRefreshing) {
        return;
    }

    dashboardState.ui.isRefreshing = true;

    try {
        const payload = await fetchJson(AUSSEM1_DASHBOARD.api.dashboardStatus);
        const status = normalizeDashboardStatus(payload);

        dashboardState.lastStatusPayload = payload;
        dashboardState.counters.refreshes += 1;

        renderDashboardMetrics(status);
        renderTrainingPanel(status.trainingSummary);
        renderMemoryPanel(status.memoryHealth);
        renderRawPayload(payload);

        dashboardState.lastError = null;
    } catch (error) {
        dashboardState.counters.errors += 1;
        dashboardState.lastError = error;

        renderRawPayload({
            status: "dashboard_refresh_failed",
            error: error.message,
            timestamp: new Date().toISOString()
        });
    } finally {
        dashboardState.ui.isRefreshing = false;
    }
}


async function loadBootstrap() {
    try {
        const payload = await fetchJson(AUSSEM1_DASHBOARD.api.dashboardBootstrap);
        dashboardState.lastBootstrapPayload = payload;
        return payload;
    } catch (error) {
        dashboardState.lastError = error;
        return null;
    }
}


/* ============================================================
SECTION 09 - CHAT CONTROL SYSTEM
============================================================ */

function getChatInputPayload() {
    const messageInput = byId(AUSSEM1_DASHBOARD.selectors.messageInput);
    const propertyAddressInput = byId(AUSSEM1_DASHBOARD.selectors.propertyAddress);

    const message = messageInput ? messageInput.value.trim() : "";
    const propertyAddress = propertyAddressInput ? propertyAddressInput.value.trim() : "";

    return {
        message,
        property_address: propertyAddress || null,
        session_id: dashboardState.currentSessionId,
        user_id: dashboardState.currentUserId
    };
}


function updateSessionLabel() {
    const label = dashboardState.currentSessionId
        ? `Session: ${dashboardState.currentSessionId}`
        : "Session: new";

    setText(AUSSEM1_DASHBOARD.selectors.sessionId, label);
}


async function submitChatMessage(event) {
    if (event) {
        event.preventDefault();
    }

    if (dashboardState.ui.isChatBusy) {
        return;
    }

    const payload = getChatInputPayload();

    if (!payload.message) {
        return;
    }

    dashboardState.ui.isChatBusy = true;
    dashboardState.currentPropertyAddress = payload.property_address;
    dashboardState.counters.messagesSent += 1;

    addMessage("user", payload.message, {
        timestamp: nowLabel()
    });

    const messageInput = byId(AUSSEM1_DASHBOARD.selectors.messageInput);

    if (messageInput) {
        messageInput.value = "";
    }

    try {
        const responsePayload = await postJson(AUSSEM1_DASHBOARD.api.chat, payload);
        const normalized = normalizeChatResponse(responsePayload);

        dashboardState.currentSessionId = normalized.session_id;
        dashboardState.counters.messagesReceived += 1;

        updateSessionLabel();

        addMessage("assistant", normalized.response, {
            intent: normalized.intent,
            confidence: normalized.confidence,
            timestamp: nowLabel()
        });

        await refreshDashboard();
    } catch (error) {
        dashboardState.counters.errors += 1;

        addMessage(
            "assistant",
            `Chat request failed: ${error.message}`,
            {
                intent: "error",
                timestamp: nowLabel()
            }
        );
    } finally {
        dashboardState.ui.isChatBusy = false;
    }
}


function bindChatForm() {
    const form = byId(AUSSEM1_DASHBOARD.selectors.chatForm);

    if (!form) {
        return;
    }

    form.addEventListener("submit", submitChatMessage);
}


/* ============================================================
SECTION 10 - PROPERTY PREVIEW SYSTEM
============================================================ */

async function runPropertyPreview(address, question = null) {
    if (!address) {
        return {
            status: "missing_address",
            message: "A property address is required."
        };
    }

    return postJson(AUSSEM1_DASHBOARD.api.propertyPreview, {
        property_address: address,
        question
    });
}


/* ============================================================
SECTION 11 - MEMORY SEARCH SYSTEM
============================================================ */

async function searchMemory(query, limit = 20) {
    if (!query) {
        return {
            status: "missing_query",
            results: []
        };
    }

    return postJson(AUSSEM1_DASHBOARD.api.memorySearch, {
        query,
        limit
    });
}


/* ============================================================
SECTION 12 - HEALTH AND DIAGNOSTIC SYSTEM
============================================================ */

async function runHealthCheck() {
    try {
        const payload = await fetchJson(AUSSEM1_DASHBOARD.api.health);
        dashboardState.lastHealthPayload = payload;
        return payload;
    } catch (error) {
        dashboardState.lastError = error;
        return {
            status: "health_check_failed",
            error: error.message
        };
    }
}


async function runFullDiagnostics() {
    const endpoints = [
        ["health", AUSSEM1_DASHBOARD.api.health],
        ["platform", AUSSEM1_DASHBOARD.api.platform],
        ["ai_status", AUSSEM1_DASHBOARD.api.aiStatus],
        ["diagnostics", AUSSEM1_DASHBOARD.api.diagnostics],
        ["web_readiness", AUSSEM1_DASHBOARD.api.webReadiness],
        ["web_diagnostics", AUSSEM1_DASHBOARD.api.webDiagnostics],
        ["route_registry", AUSSEM1_DASHBOARD.api.routeRegistry],
        ["chat_health", AUSSEM1_DASHBOARD.api.chatHealth],
        ["prompt_status", AUSSEM1_DASHBOARD.api.promptStatus]
    ];

    const results = {};

    for (const [name, url] of endpoints) {
        try {
            results[name] = await fetchJson(url);
        } catch (error) {
            results[name] = {
                status: "failed",
                error: error.message
            };
        }
    }

    renderRawPayload({
        diagnostics: results,
        timestamp: new Date().toISOString()
    });

    return results;
}


/* ============================================================
SECTION 13 - DYNAMIC UI ENHANCEMENT
============================================================ */

function createControlButton(label, onClick, className = "button-secondary") {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className;
    button.textContent = label;
    button.addEventListener("click", onClick);
    return button;
}


function injectDashboardControlBar() {
    const heroActions = document.querySelector(".hero-actions");

    if (!heroActions) {
        return;
    }

    const refreshButton = createControlButton(
        "Refresh Systems",
        refreshDashboard,
        "button-secondary"
    );

    const diagnosticsButton = createControlButton(
        "Run Diagnostics",
        runFullDiagnostics,
        "button-secondary"
    );

    const resetButton = createControlButton(
        "Reset Chat",
        clearChat,
        "button-secondary"
    );

    heroActions.appendChild(refreshButton);
    heroActions.appendChild(diagnosticsButton);
    heroActions.appendChild(resetButton);
}


function injectMlVisualHooks() {
    const propertyFoundationPanel = document.querySelector(".panel .tag-wrap");

    if (!propertyFoundationPanel) {
        return;
    }

    const mlTag = document.createElement("span");
    mlTag.className = "tag purple";
    mlTag.textContent = "Future ML Ops";

    const ragTag = document.createElement("span");
    ragTag.className = "tag purple";
    ragTag.textContent = "Future RAG";

    propertyFoundationPanel.appendChild(mlTag);
    propertyFoundationPanel.appendChild(ragTag);
}


/* ============================================================
SECTION 14 - STATIC ASSET VERIFICATION
============================================================ */

async function verifyStaticAssets() {
    const checks = {
        css: "/static/css/dashboard.css",
        js: "/static/js/dashboard.js"
    };

    const results = {};

    for (const [key, url] of Object.entries(checks)) {
        try {
            const response = await fetch(url, {
                method: "HEAD",
                cache: "no-store"
            });

            results[key] = {
                url,
                ok: response.ok,
                status: response.status
            };
        } catch (error) {
            results[key] = {
                url,
                ok: false,
                error: error.message
            };
        }
    }

    return results;
}


/* ============================================================
SECTION 15 - POLLING SYSTEM
============================================================ */

function startPolling() {
    stopPolling();

    dashboardState.polling.statusIntervalId = setInterval(
        refreshDashboard,
        AUSSEM1_DASHBOARD.refresh.statusMs
    );

    dashboardState.polling.healthIntervalId = setInterval(
        runHealthCheck,
        AUSSEM1_DASHBOARD.refresh.healthMs
    );
}


function stopPolling() {
    if (dashboardState.polling.statusIntervalId) {
        clearInterval(dashboardState.polling.statusIntervalId);
        dashboardState.polling.statusIntervalId = null;
    }

    if (dashboardState.polling.healthIntervalId) {
        clearInterval(dashboardState.polling.healthIntervalId);
        dashboardState.polling.healthIntervalId = null;
    }
}


/* ============================================================
SECTION 16 - KEYBOARD SHORTCUTS
============================================================ */

function bindKeyboardShortcuts() {
    document.addEventListener("keydown", async (event) => {
        const isControl = event.ctrlKey || event.metaKey;

        if (!isControl) {
            return;
        }

        if (event.key.toLowerCase() === "r") {
            event.preventDefault();
            await refreshDashboard();
        }

        if (event.key.toLowerCase() === "d") {
            event.preventDefault();
            await runFullDiagnostics();
        }

        if (event.key.toLowerCase() === "k") {
            event.preventDefault();

            const input = byId(AUSSEM1_DASHBOARD.selectors.messageInput);

            if (input) {
                input.focus();
            }
        }
    });
}


/* ============================================================
SECTION 17 - STARTUP SEQUENCE
============================================================ */

async function initializeDashboard() {
    if (dashboardState.initialized) {
        return;
    }

    dashboardState.initialized = true;

    bindChatForm();
    bindKeyboardShortcuts();
    injectDashboardControlBar();
    injectMlVisualHooks();

    await loadBootstrap();
    await verifyStaticAssets();
    await refreshDashboard();
    await runHealthCheck();

    startPolling();

    addSystemMessage(
        "Phase 2 dashboard control system is active. Live chat, system metrics, diagnostics, memory, and training status are now controlled by dashboard.js."
    );
}


/* ============================================================
SECTION 18 - SAFE DOM READY BOOT
============================================================ */

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeDashboard);
} else {
    initializeDashboard();
}


/* ============================================================
SECTION 19 - DEVELOPER CONSOLE EXPORTS
============================================================ */

window.AUSSEM1_DASHBOARD = AUSSEM1_DASHBOARD;

window.aussem1DashboardState = dashboardState;

window.aussem1DashboardControls = {
    refreshDashboard,
    runHealthCheck,
    runFullDiagnostics,
    runPropertyPreview,
    searchMemory,
    clearChat,
    stopPolling,
    startPolling
};


/* ============================================================
END OF FILE
============================================================ */