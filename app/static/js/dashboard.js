/* ============================================================
AUSSEM1
PHASE 2.00 PART 2.01
ENTERPRISE REAL ESTATE DASHBOARD CONTROL SYSTEM
FILE: app/static/js/dashboard.js
PURPOSE:
Browser-side control system for the Aussem1 real estate dashboard.

This file controls:
- live AI chat
- hero property search
- property preview workflow
- dashboard metrics
- memory status
- training status
- route diagnostics
- health checks
- system payload rendering
- user feedback states
- future AI / ML / RAG dashboard hooks

AUTHOR:
Ryan Schuren

ASSISTANT:
Alfred

STATUS:
ENTERPRISE DASHBOARD CONTROL SYSTEM ACTIVE
============================================================ */


/* ============================================================
SECTION 01 - ENTERPRISE RUNTIME CONFIGURATION
============================================================ */

const AUSSEM1_DASHBOARD = {
    platform: "Aussem1",
    phase: "PHASE 2.00 PART 2.01",
    version: "0.2.1",
    status: "enterprise_dashboard_control_system_active",

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
        diagnostics: "/diagnostics",

        dashboardCss: "/static/css/dashboard.css",
        dashboardJs: "/static/js/dashboard.js"
    },

    refresh: {
        statusMs: 10000,
        healthMs: 20000,
        maxChatMessages: 100,
        diagnosticTimeoutMs: 12000
    },

    selectors: {
        chatStream: "chatStream",
        chatForm: "chatForm",
        messageInput: "messageInput",
        propertyAddress: "propertyAddress",
        sessionId: "sessionId",

        heroPropertyForm: "heroPropertyForm",
        heroPropertyAddress: "heroPropertyAddress",
        heroPropertyQuestion: "heroPropertyQuestion",

        lastUpdated: "lastUpdated",
        metricMessages: "metricMessages",
        metricSessions: "metricSessions",
        metricTraining: "metricTraining",
        metricReview: "metricReview",

        trainingPanel: "trainingPanel",
        memoryPanel: "memoryPanel",
        rawPayload: "rawPayload",
        liveChat: "live-chat"
    },

    defaults: {
        userId: "dashboard-user",
        welcomeMessage:
            "Aussem1 is online. Ask about a property address, value drivers, public records, comparable homes, market context, or platform status.",
        emptyAddressPrompt:
            "Enter an address or ask a general real estate intelligence question.",
        propertyQuestionTemplate:
            "Analyze this property and explain what records, comparable homes, valuation factors, and market signals should be reviewed:"
    }
};


/* ============================================================
SECTION 02 - APPLICATION STATE
============================================================ */

const dashboardState = {
    initialized: false,

    currentSessionId: null,
    currentUserId: AUSSEM1_DASHBOARD.defaults.userId,
    currentPropertyAddress: null,

    lastStatusPayload: null,
    lastBootstrapPayload: null,
    lastHealthPayload: null,
    lastDiagnosticsPayload: null,
    lastPropertyPreviewPayload: null,
    lastError: null,

    polling: {
        statusIntervalId: null,
        healthIntervalId: null
    },

    counters: {
        messagesSent: 0,
        messagesReceived: 0,
        refreshes: 0,
        diagnosticsRun: 0,
        healthChecks: 0,
        propertyPreviews: 0,
        errors: 0
    },

    ui: {
        isChatBusy: false,
        isRefreshing: false,
        isDiagnosticsBusy: false,
        isPropertyPreviewBusy: false
    }
};


/* ============================================================
SECTION 03 - SAFE DOM UTILITIES
============================================================ */

function byId(id) {
    return document.getElementById(id);
}


function hasElement(id) {
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


function getValue(id) {
    const element = byId(id);

    if (!element) {
        return "";
    }

    return String(element.value || "").trim();
}


function setValue(id, value) {
    const element = byId(id);

    if (!element) {
        return;
    }

    element.value = value ?? "";
}


function disableElement(element, disabled = true) {
    if (!element) {
        return;
    }

    element.disabled = disabled;
    element.setAttribute("aria-busy", disabled ? "true" : "false");
}


function scrollToElement(id) {
    const element = byId(id);

    if (!element) {
        return;
    }

    element.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


function safeNumber(value, fallback = 0) {
    const numberValue = Number(value);

    if (value === undefined || value === null || Number.isNaN(numberValue)) {
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


function isoNow() {
    return new Date().toISOString();
}


/* ============================================================
SECTION 04 - NETWORK UTILITIES
============================================================ */

async function fetchJson(url, options = {}) {
    const controller = new AbortController();
    const timeout = options.timeoutMs || AUSSEM1_DASHBOARD.refresh.diagnosticTimeoutMs;

    const timeoutId = setTimeout(() => {
        controller.abort();
    }, timeout);

    try {
        const response = await fetch(url, {
            cache: "no-store",
            signal: controller.signal,
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
            const detail = payload?.detail || payload?.message || payload;
            throw new Error(`Request failed ${response.status}: ${safeString(detail)}`);
        }

        return payload;
    } finally {
        clearTimeout(timeoutId);
    }
}


async function postJson(url, body, options = {}) {
    return fetchJson(url, {
        method: "POST",
        body: JSON.stringify(body),
        ...options
    });
}


/* ============================================================
SECTION 05 - NOTIFICATION AND STATUS RENDERING
============================================================ */

function renderRawPayload(payload) {
    setText(
        AUSSEM1_DASHBOARD.selectors.rawPayload,
        prettyJson(payload)
    );
}


function renderDeveloperEvent(title, payload) {
    renderRawPayload({
        event: title,
        payload,
        dashboard_state: {
            session_id: dashboardState.currentSessionId,
            property_address: dashboardState.currentPropertyAddress,
            counters: dashboardState.counters
        },
        timestamp: isoNow()
    });
}


function setLastUpdated(label = null) {
    setText(
        AUSSEM1_DASHBOARD.selectors.lastUpdated,
        label || `Updated ${nowLabel()}`
    );
}


function renderError(error, context = "dashboard") {
    dashboardState.counters.errors += 1;
    dashboardState.lastError = error;

    renderRawPayload({
        status: "error",
        context,
        error: error?.message || String(error),
        timestamp: isoNow()
    });
}


function renderSoftNotice(message, context = "system") {
    addMessage("assistant", message, {
        intent: context,
        timestamp: nowLabel()
    });
}


/* ============================================================
SECTION 06 - MESSAGE RENDERING
============================================================ */

function createMessageElement(role, text, metadata = {}) {
    const wrapper = document.createElement("div");
    wrapper.className = `message ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    const metaPieces = [];

    if (metadata.intent) {
        metaPieces.push(`Intent: ${metadata.intent}`);
    }

    if (metadata.confidence !== undefined && metadata.confidence !== null) {
        metaPieces.push(`Confidence: ${metadata.confidence}`);
    }

    if (metadata.sourceStatus) {
        metaPieces.push(`Sources: ${metadata.sourceStatus}`);
    }

    if (metadata.timestamp) {
        metaPieces.push(metadata.timestamp);
    }

    if (metaPieces.length > 0) {
        const meta = document.createElement("div");
        meta.className = "message-meta";
        meta.textContent = metaPieces.join(" · ");
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


function addPropertyMessage(text) {
    addMessage("assistant", text, {
        intent: "property_intelligence",
        timestamp: nowLabel()
    });
}


function clearChat() {
    const chatStream = byId(AUSSEM1_DASHBOARD.selectors.chatStream);

    if (!chatStream) {
        return;
    }

    chatStream.innerHTML = "";

    dashboardState.currentSessionId = null;
    dashboardState.currentPropertyAddress = null;

    updateSessionLabel();

    addSystemMessage(AUSSEM1_DASHBOARD.defaults.welcomeMessage);
}


/* ============================================================
SECTION 07 - RESPONSE NORMALIZATION
============================================================ */

function normalizeChatResponse(payload) {
    if (!payload || typeof payload !== "object") {
        return {
            response: safeString(payload, "No response returned."),
            session_id: dashboardState.currentSessionId,
            intent: null,
            confidence: null,
            sourceStatus: null,
            raw: payload
        };
    }

    return {
        response:
            payload.response ||
            payload.answer ||
            payload.message ||
            payload.data?.response ||
            payload.data?.answer ||
            payload.data?.message ||
            prettyJson(payload),

        session_id:
            payload.session_id ||
            payload.data?.session_id ||
            dashboardState.currentSessionId,

        intent:
            payload.intent ||
            payload.data?.intent ||
            payload.intent_label ||
            null,

        confidence:
            payload.confidence ||
            payload.data?.confidence ||
            payload.confidence_score ||
            null,

        sourceStatus:
            payload.source_status ||
            payload.data?.source_status ||
            payload.sources?.status ||
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
    const webRoutes = systems.web_routes || {};

    return {
        raw: payload,
        systems,
        memoryHealth: memoryStore.health || memoryStore || {},
        trainingSummary: trainingLogger || {},
        chatEngine,
        promptRegistry,
        webRoutes,
        timestamp: payload?.timestamp || payload?.data?.timestamp || null
    };
}


function normalizeEnterpriseData(payload) {
    if (!payload || typeof payload !== "object") {
        return payload;
    }

    return payload.data || payload;
}


/* ============================================================
SECTION 08 - METRIC RENDERING
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

    setLastUpdated();
}


function renderTrainingPanel(training) {
    const totalInteractions = safeNumber(training.total_interactions);
    const failedInteractions = safeNumber(training.failed_interactions);
    const averageConfidence = safeNumber(training.average_confidence);
    const reviewQueueSize = safeNumber(training.review_queue_size);

    setHTML(
        AUSSEM1_DASHBOARD.selectors.trainingPanel,
        `
        <div class="log-item">
            <strong>Total interactions:</strong> ${totalInteractions}
        </div>
        <div class="log-item">
            <strong>Failed interactions:</strong> ${failedInteractions}
        </div>
        <div class="log-item">
            <strong>Average confidence:</strong> ${averageConfidence}
        </div>
        <div class="log-item">
            <strong>Review queue size:</strong> ${reviewQueueSize}
        </div>
        `
    );
}


function renderMemoryPanel(memory) {
    const totalMessages = safeNumber(memory.total_messages);
    const totalSessions = safeNumber(memory.total_sessions);
    const totalProperties = safeNumber(memory.total_properties);
    const totalKnowledgeItems = safeNumber(memory.total_knowledge_items);

    setHTML(
        AUSSEM1_DASHBOARD.selectors.memoryPanel,
        `
        <div class="log-item">
            <strong>Total messages:</strong> ${totalMessages}
        </div>
        <div class="log-item">
            <strong>Total sessions:</strong> ${totalSessions}
        </div>
        <div class="log-item">
            <strong>Total properties:</strong> ${totalProperties}
        </div>
        <div class="log-item">
            <strong>Knowledge items:</strong> ${totalKnowledgeItems}
        </div>
        `
    );
}


/* ============================================================
SECTION 09 - DASHBOARD REFRESH ENGINE
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
        renderError(error, "dashboard_refresh");
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
        renderError(error, "dashboard_bootstrap");
        return null;
    }
}


/* ============================================================
SECTION 10 - CHAT CONTROL SYSTEM
============================================================ */

function getChatInputPayload() {
    const message = getValue(AUSSEM1_DASHBOARD.selectors.messageInput);
    const propertyAddress = getValue(AUSSEM1_DASHBOARD.selectors.propertyAddress);

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
        renderSoftNotice("Ask a real estate question first.", "input");
        return;
    }

    dashboardState.ui.isChatBusy = true;
    dashboardState.currentPropertyAddress = payload.property_address;
    dashboardState.counters.messagesSent += 1;

    addMessage("user", payload.message, {
        timestamp: nowLabel()
    });

    setValue(AUSSEM1_DASHBOARD.selectors.messageInput, "");

    try {
        const responsePayload = await postJson(AUSSEM1_DASHBOARD.api.chat, payload);
        const normalized = normalizeChatResponse(responsePayload);

        dashboardState.currentSessionId = normalized.session_id;
        dashboardState.counters.messagesReceived += 1;

        updateSessionLabel();

        addMessage("assistant", normalized.response, {
            intent: normalized.intent,
            confidence: normalized.confidence,
            sourceStatus: normalized.sourceStatus,
            timestamp: nowLabel()
        });

        renderRawPayload(normalized.raw);
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

        renderError(error, "chat_request");
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
SECTION 11 - HERO PROPERTY SEARCH SYSTEM
============================================================ */

function buildHeroPropertyQuestion(address, question) {
    if (question) {
        return question;
    }

    if (address) {
        return `${AUSSEM1_DASHBOARD.defaults.propertyQuestionTemplate} ${address}`;
    }

    return AUSSEM1_DASHBOARD.defaults.emptyAddressPrompt;
}


async function submitHeroPropertyForm(event) {
    if (event) {
        event.preventDefault();
    }

    const address = getValue(AUSSEM1_DASHBOARD.selectors.heroPropertyAddress);
    const question = getValue(AUSSEM1_DASHBOARD.selectors.heroPropertyQuestion);
    const finalQuestion = buildHeroPropertyQuestion(address, question);

    if (address) {
        setValue(AUSSEM1_DASHBOARD.selectors.propertyAddress, address);
        dashboardState.currentPropertyAddress = address;
    }

    setValue(AUSSEM1_DASHBOARD.selectors.messageInput, finalQuestion);

    scrollToElement(AUSSEM1_DASHBOARD.selectors.liveChat);

    const form = byId(AUSSEM1_DASHBOARD.selectors.chatForm);

    if (form) {
        form.requestSubmit();
    }

    if (address) {
        await runPropertyPreview(address, finalQuestion);
    }
}


function bindHeroPropertyForm() {
    const form = byId(AUSSEM1_DASHBOARD.selectors.heroPropertyForm);

    if (!form) {
        return;
    }

    form.addEventListener("submit", submitHeroPropertyForm);
}


/* ============================================================
SECTION 12 - PROPERTY PREVIEW SYSTEM
============================================================ */

async function runPropertyPreview(address, question = null) {
    if (!address) {
        return {
            status: "missing_address",
            message: "A property address is required."
        };
    }

    if (dashboardState.ui.isPropertyPreviewBusy) {
        return {
            status: "busy",
            message: "Property preview already running."
        };
    }

    dashboardState.ui.isPropertyPreviewBusy = true;

    try {
        const payload = await postJson(AUSSEM1_DASHBOARD.api.propertyPreview, {
            property_address: address,
            question
        });

        dashboardState.lastPropertyPreviewPayload = payload;
        dashboardState.counters.propertyPreviews += 1;

        const data = normalizeEnterpriseData(payload);

        addPropertyMessage(
            [
                `Property preview initialized for: ${address}`,
                "",
                "Current phase:",
                "Aussem1 can route this property question, preserve the address context, and prepare the future records/comps/valuation pipeline.",
                "",
                "Next engine:",
                "Address Intelligence and canonical property profile construction."
            ].join("\n")
        );

        renderDeveloperEvent("property_preview", data);

        return payload;
    } catch (error) {
        renderError(error, "property_preview");
        return {
            status: "failed",
            error: error.message
        };
    } finally {
        dashboardState.ui.isPropertyPreviewBusy = false;
    }
}


/* ============================================================
SECTION 13 - MEMORY SEARCH SYSTEM
============================================================ */

async function searchMemory(query, limit = 20) {
    if (!query) {
        return {
            status: "missing_query",
            results: []
        };
    }

    try {
        const payload = await postJson(AUSSEM1_DASHBOARD.api.memorySearch, {
            query,
            limit
        });

        renderDeveloperEvent("memory_search", payload);

        return payload;
    } catch (error) {
        renderError(error, "memory_search");
        return {
            status: "failed",
            error: error.message,
            results: []
        };
    }
}


/* ============================================================
SECTION 14 - HEALTH AND DIAGNOSTIC SYSTEM
============================================================ */

async function runHealthCheck() {
    try {
        const payload = await fetchJson(AUSSEM1_DASHBOARD.api.health);

        dashboardState.lastHealthPayload = payload;
        dashboardState.counters.healthChecks += 1;

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
    if (dashboardState.ui.isDiagnosticsBusy) {
        return dashboardState.lastDiagnosticsPayload;
    }

    dashboardState.ui.isDiagnosticsBusy = true;

    const endpoints = [
        ["health", AUSSEM1_DASHBOARD.api.health],
        ["platform", AUSSEM1_DASHBOARD.api.platform],
        ["ai_status", AUSSEM1_DASHBOARD.api.aiStatus],
        ["diagnostics", AUSSEM1_DASHBOARD.api.diagnostics],
        ["web_readiness", AUSSEM1_DASHBOARD.api.webReadiness],
        ["web_diagnostics", AUSSEM1_DASHBOARD.api.webDiagnostics],
        ["route_registry", AUSSEM1_DASHBOARD.api.routeRegistry],
        ["chat_health", AUSSEM1_DASHBOARD.api.chatHealth],
        ["prompt_status", AUSSEM1_DASHBOARD.api.promptStatus],
        ["training_status", AUSSEM1_DASHBOARD.api.trainingStatus],
        ["memory_status", AUSSEM1_DASHBOARD.api.memoryStatus]
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

    const payload = {
        diagnostics: results,
        counters: dashboardState.counters,
        timestamp: isoNow()
    };

    dashboardState.lastDiagnosticsPayload = payload;
    dashboardState.counters.diagnosticsRun += 1;

    renderRawPayload(payload);
    renderSoftNotice("Diagnostics complete. Review the developer payload panel.", "diagnostics");

    dashboardState.ui.isDiagnosticsBusy = false;

    return payload;
}


/* ============================================================
SECTION 15 - STATIC ASSET VERIFICATION
============================================================ */

async function verifyStaticAssets() {
    const checks = {
        css: AUSSEM1_DASHBOARD.api.dashboardCss,
        js: AUSSEM1_DASHBOARD.api.dashboardJs
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
SECTION 16 - DYNAMIC UI ENHANCEMENT
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

    const existing = document.querySelector("[data-dashboard-control='true']");

    if (existing) {
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

    refreshButton.dataset.dashboardControl = "true";
    diagnosticsButton.dataset.dashboardControl = "true";
    resetButton.dataset.dashboardControl = "true";

    heroActions.appendChild(refreshButton);
    heroActions.appendChild(diagnosticsButton);
    heroActions.appendChild(resetButton);
}


function injectMlVisualHooks() {
    const capabilityPanel = document.querySelector(".panel .tag-wrap");

    if (!capabilityPanel) {
        return;
    }

    const existing = capabilityPanel.querySelector("[data-generated-tag='ml-runtime']");

    if (existing) {
        return;
    }

    const mlTag = document.createElement("span");
    mlTag.className = "tag purple";
    mlTag.textContent = "Future ML Ops";
    mlTag.dataset.generatedTag = "ml-runtime";

    const ragTag = document.createElement("span");
    ragTag.className = "tag purple";
    ragTag.textContent = "Future RAG";
    ragTag.dataset.generatedTag = "rag-runtime";

    capabilityPanel.appendChild(mlTag);
    capabilityPanel.appendChild(ragTag);
}


/* ============================================================
SECTION 17 - POLLING SYSTEM
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
SECTION 18 - KEYBOARD SHORTCUTS
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

        if (event.key.toLowerCase() === "l") {
            event.preventDefault();
            clearChat();
        }
    });
}


/* ============================================================
SECTION 19 - STARTUP SEQUENCE
============================================================ */

async function initializeDashboard() {
    if (dashboardState.initialized) {
        return;
    }

    dashboardState.initialized = true;

    bindChatForm();
    bindHeroPropertyForm();
    bindKeyboardShortcuts();

    injectDashboardControlBar();
    injectMlVisualHooks();

    await loadBootstrap();
    await verifyStaticAssets();
    await refreshDashboard();
    await runHealthCheck();

    startPolling();

    addSystemMessage(
        "Aussem1 dashboard control system is active. Live chat, property preview, metrics, memory, training status, and diagnostics are connected."
    );
}


/* ============================================================
SECTION 20 - SAFE DOM READY BOOT
============================================================ */

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeDashboard);
} else {
    initializeDashboard();
}


/* ============================================================
SECTION 21 - DEVELOPER CONSOLE EXPORTS
============================================================ */

window.AUSSEM1_DASHBOARD = AUSSEM1_DASHBOARD;

window.aussem1DashboardState = dashboardState;

window.aussem1DashboardControls = {
    refreshDashboard,
    loadBootstrap,
    runHealthCheck,
    runFullDiagnostics,
    runPropertyPreview,
    searchMemory,
    clearChat,
    stopPolling,
    startPolling,
    submitChatMessage
};


/* ============================================================
END OF FILE
============================================================ */