/* ============================================================
AUSSEM1
PHASE 2.40 PART 3.00
ENTERPRISE PROPERTY INTELLIGENCE DASHBOARD CONTROLLER
FILE: app/static/js/dashboard.js
PURPOSE:
Browser-side controller for the Aussem1 property intelligence dashboard.

This file provides:
- live dashboard bootstrap
- health/readiness diagnostics
- property intelligence status checks
- property router visibility
- chat console control
- hero property form bridge support
- memory/training/review metric rendering
- public-record/property-governance payload visibility
- defensive fetch handling
- no fabricated frontend property facts
- source limitation disclosure
- resilient Render-safe frontend behavior

AUTHOR:
Ryan Schuren

ASSISTANT:
Alfred

STATUS:
ENTERPRISE PROPERTY INTELLIGENCE DASHBOARD JAVASCRIPT ACTIVE
============================================================ */


/* ============================================================
SECTION 01 - GLOBAL DASHBOARD CONSTANTS
============================================================ */

(function () {
    "use strict";

    const AUSSEM_DASHBOARD = {
        name: "Aussem1 Enterprise Property Intelligence Dashboard",
        version: "0.3.0",
        phase: "PHASE 2.40 PART 3.00",
        status: "enterprise_property_intelligence_dashboard_js_active",
        generatedAt: new Date().toISOString()
    };

    const API = {
        health: "/health",
        platform: "/platform",
        routes: "/routes",
        diagnostics: "/diagnostics",
        aiStatus: "/ai/status",
        staticStatus: "/static/status",
        templateStatus: "/templates/status",
        propertyStatus: "/property-intelligence/status",

        dashboardBootstrap: "/api/dashboard/bootstrap",
        dashboardStatus: "/api/dashboard/status",

        webReadiness: "/web/readiness",
        webDiagnostics: "/web/diagnostics",
        webRouteRegistry: "/web/route-registry",

        chat: "/chat",
        chatTrace: "/chat/trace",
        chatHealth: "/chat/health",
        chatTrainingStatus: "/chat/training-status",
        chatReviewQueue: "/chat/review-queue",
        chatTrainingExport: "/chat/training-export",
        chatMemoryStatus: "/chat/memory-status",
        chatMemorySearch: "/chat/memory-search",
        chatPromptStatus: "/chat/prompt-status",

        propertiesRoot: "/properties",
        propertiesHealth: "/properties/health",
        propertiesReadiness: "/properties/readiness",
        propertiesDiagnostics: "/properties/diagnostics",
        propertiesRoutes: "/properties/registry/routes",
        propertyPreview: "/properties/preview"
    };

    const DEFAULTS = {
        fetchTimeoutMs: 12000,
        refreshIntervalMs: 45000,
        maxRenderedMessages: 100,
        maxPanelItems: 8,
        defaultSessionPrefix: "aussem1-session",
        emptyValue: "Unavailable",
        dashboardAnchor: "#live-chat"
    };


    /* ============================================================
    SECTION 02 - DOM SELECTORS
    ============================================================ */

    const SELECTORS = {
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
    };


    /* ============================================================
    SECTION 03 - STATE
    ============================================================ */

    const state = {
        initialized: false,
        sessionId: null,
        currentPropertyAddress: "",
        busy: false,
        lastBootstrapPayload: null,
        lastStatusPayload: null,
        lastHealthPayload: null,
        lastDiagnosticsPayload: null,
        lastPropertyStatusPayload: null,
        lastPropertyRouterPayload: null,
        lastTrainingPayload: null,
        lastMemoryPayload: null,
        lastReviewPayload: null,
        lastPromptPayload: null,
        messageCount: 0,
        refreshTimer: null,
        endpointResults: {},
        errors: [],
        warnings: []
    };


    /* ============================================================
    SECTION 04 - BASIC UTILITIES
    ============================================================ */

    function nowIso() {
        return new Date().toISOString();
    }

    function nowLabel() {
        return new Date().toLocaleString();
    }

    function safeString(value) {
        if (value === null || value === undefined) {
            return "";
        }

        return String(value).trim();
    }

    function safeNumber(value, fallback = 0) {
        const number = Number(value);

        if (Number.isFinite(number)) {
            return number;
        }

        return fallback;
    }

    function isObject(value) {
        return Boolean(
            value &&
            typeof value === "object" &&
            !Array.isArray(value)
        );
    }

    function byId(id) {
        return document.getElementById(id);
    }

    function setText(id, value) {
        const element = byId(id);

        if (!element) {
            return;
        }

        element.textContent = safeString(value);
    }

    function setHtml(id, value) {
        const element = byId(id);

        if (!element) {
            return;
        }

        element.innerHTML = value;
    }

    function formatInteger(value) {
        return new Intl.NumberFormat("en-US").format(
            safeNumber(value, 0)
        );
    }

    function truncateText(value, maxLength = 180) {
        const text = safeString(value);

        if (text.length <= maxLength) {
            return text;
        }

        return `${text.slice(0, maxLength - 1)}…`;
    }

    function escapeHtml(value) {
        return safeString(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function prettyJson(value) {
        try {
            return JSON.stringify(value, null, 2);
        } catch (error) {
            return String(value);
        }
    }

    function makeSessionId() {
        const existing = window.localStorage.getItem("aussem1_session_id");

        if (existing) {
            return existing;
        }

        const generated = `${DEFAULTS.defaultSessionPrefix}-${Date.now()}-${Math.random()
            .toString(16)
            .slice(2)}`;

        window.localStorage.setItem("aussem1_session_id", generated);

        return generated;
    }

    function normalizeStatus(value) {
        const text = safeString(value).toLowerCase();

        if (!text) {
            return "unknown";
        }

        return text;
    }

    function isSuccessfulStatus(value) {
        const status = normalizeStatus(value);

        return [
            "ok",
            "active",
            "ready",
            "available",
            "foundation_active",
            "enterprise_application_property_intelligence_routing_active",
            "enterprise_property_intelligence_dashboard_js_active"
        ].includes(status);
    }


    /* ============================================================
    SECTION 05 - NETWORK UTILITIES
    ============================================================ */

    async function fetchJson(url, options = {}) {
        const controller = new AbortController();
        const timeoutMs = options.timeoutMs || DEFAULTS.fetchTimeoutMs;

        const timeout = window.setTimeout(function () {
            controller.abort();
        }, timeoutMs);

        const requestOptions = {
            method: options.method || "GET",
            headers: {
                "Accept": "application/json",
                ...(options.headers || {})
            },
            signal: controller.signal
        };

        if (options.body !== undefined) {
            requestOptions.headers["Content-Type"] = "application/json";
            requestOptions.body = JSON.stringify(options.body);
        }

        const startedAt = performance.now();

        try {
            const response = await fetch(url, requestOptions);
            const text = await response.text();

            let payload = null;

            if (text) {
                try {
                    payload = JSON.parse(text);
                } catch (error) {
                    payload = {
                        raw_text: text,
                        parse_error: error.message
                    };
                }
            }

            const durationMs = Math.round(performance.now() - startedAt);

            return {
                ok: response.ok,
                status: response.status,
                statusText: response.statusText,
                url,
                durationMs,
                payload,
                error: null,
                retrievedAt: nowIso()
            };
        } catch (error) {
            return {
                ok: false,
                status: 0,
                statusText: "network_error",
                url,
                durationMs: Math.round(performance.now() - startedAt),
                payload: null,
                error: error.name === "AbortError"
                    ? `Request timed out after ${timeoutMs}ms`
                    : error.message,
                retrievedAt: nowIso()
            };
        } finally {
            window.clearTimeout(timeout);
        }
    }

    async function safeEndpoint(name, url, options = {}) {
        const result = await fetchJson(url, options);

        state.endpointResults[name] = result;

        if (!result.ok) {
            state.warnings.push({
                endpoint: name,
                url,
                status: result.status,
                error: result.error,
                at: nowIso()
            });
        }

        return result;
    }


    /* ============================================================
    SECTION 06 - MESSAGE RENDERING
    ============================================================ */

    function getChatStream() {
        return byId(SELECTORS.chatStream);
    }

    function renderMessage(role, content, metadata = {}) {
        const stream = getChatStream();

        if (!stream) {
            return;
        }

        const wrapper = document.createElement("div");
        wrapper.className = `message ${role === "user" ? "user" : "assistant"}`;

        const bubble = document.createElement("div");
        bubble.className = "bubble";

        const body = document.createElement("div");
        body.className = "message-body";
        body.textContent = safeString(content);

        bubble.appendChild(body);

        if (metadata && Object.keys(metadata).length > 0) {
            const meta = document.createElement("div");
            meta.className = "message-meta";
            meta.textContent = buildMessageMeta(metadata);
            bubble.appendChild(meta);
        }

        wrapper.appendChild(bubble);
        stream.appendChild(wrapper);

        trimMessages();
        scrollChatToBottom();
    }

    function buildMessageMeta(metadata) {
        const pieces = [];

        if (metadata.status) {
            pieces.push(`status: ${metadata.status}`);
        }

        if (metadata.confidence !== undefined && metadata.confidence !== null) {
            pieces.push(`confidence: ${metadata.confidence}`);
        }

        if (metadata.source) {
            pieces.push(`source: ${metadata.source}`);
        }

        if (metadata.timestamp) {
            pieces.push(metadata.timestamp);
        }

        return pieces.join(" · ");
    }

    function trimMessages() {
        const stream = getChatStream();

        if (!stream) {
            return;
        }

        const messages = stream.querySelectorAll(".message");

        if (messages.length <= DEFAULTS.maxRenderedMessages) {
            return;
        }

        const removeCount = messages.length - DEFAULTS.maxRenderedMessages;

        for (let index = 0; index < removeCount; index += 1) {
            messages[index].remove();
        }
    }

    function scrollChatToBottom() {
        const stream = getChatStream();

        if (!stream) {
            return;
        }

        stream.scrollTop = stream.scrollHeight;
    }

    function renderSystemNotice(message, severity = "info") {
        renderMessage("assistant", message, {
            status: severity,
            timestamp: nowLabel()
        });
    }


    /* ============================================================
    SECTION 07 - CHAT PAYLOAD NORMALIZATION
    ============================================================ */

    function normalizeChatResponse(payload) {
        if (!payload) {
            return {
                answer: "The chat endpoint returned no response payload.",
                status: "empty",
                confidence: null,
                raw: payload
            };
        }

        if (typeof payload === "string") {
            return {
                answer: payload,
                status: "ok",
                confidence: null,
                raw: payload
            };
        }

        const candidates = [
            payload.answer,
            payload.response,
            payload.message,
            payload.content,
            payload.text,
            payload.data && payload.data.answer,
            payload.data && payload.data.response,
            payload.data && payload.data.message,
            payload.result && payload.result.answer,
            payload.result && payload.result.response
        ];

        const answer = candidates.find(function (candidate) {
            return safeString(candidate);
        });

        return {
            answer: answer || prettyJson(payload),
            status: payload.status || payload.data?.status || "ok",
            confidence: payload.confidence || payload.data?.confidence || null,
            raw: payload
        };
    }

    function buildChatRequest(message, propertyAddress) {
        return {
            message,
            property_address: propertyAddress || null,
            address: propertyAddress || null,
            session_id: state.sessionId,
            context: {
                source: "aussem1_dashboard",
                phase: AUSSEM_DASHBOARD.phase,
                strict_source_mode: true,
                no_mock_property_facts: true,
                unsupported_without_listing_feed: [
                    "active_listing_status",
                    "under_contract_status",
                    "current_listing_price",
                    "days_on_market",
                    "showing_availability"
                ],
                timestamp: nowIso()
            }
        };
    }


    /* ============================================================
    SECTION 08 - CHAT CONTROLLER
    ============================================================ */

    async function submitChat(message, propertyAddress = "") {
        const cleanMessage = safeString(message);
        const cleanAddress = safeString(propertyAddress);

        if (!cleanMessage) {
            return;
        }

        if (state.busy) {
            renderSystemNotice(
                "Aussem1 is still processing the previous request. Please wait one moment.",
                "busy"
            );
            return;
        }

        state.busy = true;
        state.messageCount += 1;

        if (cleanAddress) {
            state.currentPropertyAddress = cleanAddress;
        }

        renderMessage("user", cleanMessage, {
            source: cleanAddress || "general",
            timestamp: nowLabel()
        });

        const payload = buildChatRequest(cleanMessage, cleanAddress);

        const result = await safeEndpoint("chat", API.chat, {
            method: "POST",
            body: payload,
            timeoutMs: 25000
        });

        if (!result.ok) {
            renderMessage(
                "assistant",
                [
                    "The Aussem1 chat endpoint is unavailable or returned an error.",
                    "",
                    `Endpoint: ${API.chat}`,
                    `Status: ${result.status || "network error"}`,
                    `Detail: ${result.error || result.statusText || "unknown"}`
                ].join("\n"),
                {
                    status: "error",
                    timestamp: nowLabel()
                }
            );
            state.busy = false;
            renderRawPayload();
            return;
        }

        const normalized = normalizeChatResponse(result.payload);

        renderMessage(
            "assistant",
            normalized.answer,
            {
                status: normalized.status,
                confidence: normalized.confidence,
                timestamp: nowLabel()
            }
        );

        state.busy = false;
        await refreshDashboard();
    }

    function bindChatForm() {
        const form = byId(SELECTORS.chatForm);

        if (!form) {
            return;
        }

        form.addEventListener("submit", function (event) {
            event.preventDefault();

            const messageInput = byId(SELECTORS.messageInput);
            const propertyInput = byId(SELECTORS.propertyAddress);

            const message = messageInput ? messageInput.value : "";
            const propertyAddress = propertyInput ? propertyInput.value : "";

            if (messageInput) {
                messageInput.value = "";
            }

            submitChat(message, propertyAddress);
        });
    }

    function bindHeroForm() {
        const form = byId(SELECTORS.heroPropertyForm);

        if (!form) {
            return;
        }

        if (form.dataset.aussemBound === "true") {
            return;
        }

        form.dataset.aussemBound = "true";

        form.addEventListener("submit", function (event) {
            event.preventDefault();

            const heroAddress = byId(SELECTORS.heroPropertyAddress);
            const heroQuestion = byId(SELECTORS.heroPropertyQuestion);
            const propertyAddress = byId(SELECTORS.propertyAddress);
            const messageInput = byId(SELECTORS.messageInput);
            const liveChat = byId(SELECTORS.liveChat);

            const addressValue = heroAddress ? heroAddress.value.trim() : "";
            const questionValue = heroQuestion ? heroQuestion.value.trim() : "";

            const finalQuestion = questionValue ||
                `Analyze this property using source-backed rules: ${addressValue}`;

            if (propertyAddress) {
                propertyAddress.value = addressValue;
            }

            if (messageInput) {
                messageInput.value = finalQuestion;
            }

            if (liveChat) {
                liveChat.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }

            submitChat(finalQuestion, addressValue);
        });
    }


    /* ============================================================
    SECTION 09 - METRIC EXTRACTION
    ============================================================ */

    function pickNumber(...values) {
        for (const value of values) {
            const number = Number(value);

            if (Number.isFinite(number)) {
                return number;
            }
        }

        return 0;
    }

    function extractMetric(payload, paths) {
        for (const path of paths) {
            const value = getPath(payload, path);

            if (value !== undefined && value !== null) {
                return value;
            }
        }

        return 0;
    }

    function getPath(object, path) {
        if (!object || !path) {
            return undefined;
        }

        const parts = path.split(".");
        let current = object;

        for (const part of parts) {
            if (current === null || current === undefined) {
                return undefined;
            }

            current = current[part];
        }

        return current;
    }

    function extractDashboardMetrics() {
        const statusPayload = state.lastStatusPayload || {};
        const bootstrapPayload = state.lastBootstrapPayload || {};
        const memoryPayload = state.lastMemoryPayload || {};
        const trainingPayload = state.lastTrainingPayload || {};
        const reviewPayload = state.lastReviewPayload || {};

        return {
            messages: pickNumber(
                extractMetric(statusPayload, [
                    "data.memory.message_count",
                    "memory.message_count",
                    "memory_messages",
                    "message_count"
                ]),
                extractMetric(bootstrapPayload, [
                    "data.memory.message_count",
                    "memory.message_count"
                ]),
                extractMetric(memoryPayload, [
                    "data.message_count",
                    "message_count",
                    "total_messages",
                    "memory.total_messages"
                ])
            ),
            sessions: pickNumber(
                extractMetric(statusPayload, [
                    "data.memory.session_count",
                    "memory.session_count",
                    "session_count"
                ]),
                extractMetric(memoryPayload, [
                    "data.session_count",
                    "session_count",
                    "total_sessions",
                    "memory.total_sessions"
                ])
            ),
            training: pickNumber(
                extractMetric(statusPayload, [
                    "data.training.record_count",
                    "training.record_count",
                    "training_records"
                ]),
                extractMetric(trainingPayload, [
                    "data.record_count",
                    "record_count",
                    "total_records",
                    "training.total_records"
                ])
            ),
            review: pickNumber(
                extractMetric(statusPayload, [
                    "data.training.review_queue_count",
                    "training.review_queue_count",
                    "review_queue_count"
                ]),
                extractMetric(reviewPayload, [
                    "data.review_count",
                    "review_count",
                    "queue_count",
                    "items.length"
                ])
            )
        };
    }


    /* ============================================================
    SECTION 10 - METRIC RENDERING
    ============================================================ */

    function renderMetrics() {
        const metrics = extractDashboardMetrics();

        setText(SELECTORS.metricMessages, formatInteger(metrics.messages));
        setText(SELECTORS.metricSessions, formatInteger(metrics.sessions));
        setText(SELECTORS.metricTraining, formatInteger(metrics.training));
        setText(SELECTORS.metricReview, formatInteger(metrics.review));
        setText(SELECTORS.lastUpdated, `Updated ${nowLabel()}`);
    }

    function buildTag(label, type = "blue") {
        return `<span class="tag ${escapeHtml(type)}">${escapeHtml(label)}</span>`;
    }

    function renderPanelItems(panelId, items, fallback) {
        const panel = byId(panelId);

        if (!panel) {
            return;
        }

        if (!items || items.length === 0) {
            panel.innerHTML = `<div class="log-item">${escapeHtml(fallback)}</div>`;
            return;
        }

        panel.innerHTML = items
            .slice(0, DEFAULTS.maxPanelItems)
            .map(function (item) {
                return `<div class="log-item">${escapeHtml(item)}</div>`;
            })
            .join("");
    }

    function renderTrainingPanel() {
        const payload = state.lastTrainingPayload || {};
        const reviewPayload = state.lastReviewPayload || {};

        const items = [];

        const status = getPath(payload, "status") ||
            getPath(payload, "data.status") ||
            getPath(payload, "training.status");

        if (status) {
            items.push(`Training status: ${status}`);
        }

        const count = pickNumber(
            getPath(payload, "record_count"),
            getPath(payload, "data.record_count"),
            getPath(payload, "training.record_count")
        );

        items.push(`Training records: ${formatInteger(count)}`);

        const reviewCount = pickNumber(
            getPath(reviewPayload, "review_count"),
            getPath(reviewPayload, "data.review_count"),
            getPath(reviewPayload, "queue_count")
        );

        items.push(`Review queue: ${formatInteger(reviewCount)}`);

        items.push("Low-confidence answers remain review-gated before learning.");

        renderPanelItems(
            SELECTORS.trainingPanel,
            items,
            "Training intelligence unavailable."
        );
    }

    function renderMemoryPanel() {
        const payload = state.lastMemoryPayload || {};
        const items = [];

        const status = getPath(payload, "status") ||
            getPath(payload, "data.status") ||
            getPath(payload, "memory.status");

        if (status) {
            items.push(`Memory status: ${status}`);
        }

        const messageCount = pickNumber(
            getPath(payload, "message_count"),
            getPath(payload, "data.message_count"),
            getPath(payload, "memory.message_count"),
            getPath(payload, "total_messages")
        );

        const sessionCount = pickNumber(
            getPath(payload, "session_count"),
            getPath(payload, "data.session_count"),
            getPath(payload, "memory.session_count"),
            getPath(payload, "total_sessions")
        );

        items.push(`Stored messages: ${formatInteger(messageCount)}`);
        items.push(`Tracked sessions: ${formatInteger(sessionCount)}`);

        if (state.currentPropertyAddress) {
            items.push(`Current property context: ${state.currentPropertyAddress}`);
        } else {
            items.push("Current property context: none selected");
        }

        renderPanelItems(
            SELECTORS.memoryPanel,
            items,
            "Memory intelligence unavailable."
        );
    }


    /* ============================================================
    SECTION 11 - RAW PAYLOAD RENDERING
    ============================================================ */

    function buildRawPayload() {
        return {
            dashboard: AUSSEM_DASHBOARD,
            session: {
                session_id: state.sessionId,
                current_property_address: state.currentPropertyAddress,
                message_count: state.messageCount,
                busy: state.busy
            },
            endpoints: {
                health: compactEndpointResult(state.endpointResults.health),
                platform: compactEndpointResult(state.endpointResults.platform),
                routes: compactEndpointResult(state.endpointResults.routes),
                diagnostics: compactEndpointResult(state.endpointResults.diagnostics),
                ai_status: compactEndpointResult(state.endpointResults.aiStatus),
                property_status: compactEndpointResult(state.endpointResults.propertyStatus),
                properties_health: compactEndpointResult(state.endpointResults.propertiesHealth),
                properties_readiness: compactEndpointResult(state.endpointResults.propertiesReadiness),
                dashboard_status: compactEndpointResult(state.endpointResults.dashboardStatus),
                memory_status: compactEndpointResult(state.endpointResults.memoryStatus),
                training_status: compactEndpointResult(state.endpointResults.trainingStatus)
            },
            property_intelligence: extractPropertyStatusSummary(),
            governance: {
                mock_properties_allowed: false,
                fabricated_listing_status_allowed: false,
                fabricated_property_values_allowed: false,
                public_records_are_not_listing_status: true,
                listing_status_requires_authorized_feed: true,
                assessment_is_not_market_value: true,
                gis_is_not_legal_survey: true
            },
            warnings: state.warnings.slice(-10),
            errors: state.errors.slice(-10),
            updated_at: nowIso()
        };
    }

    function compactEndpointResult(result) {
        if (!result) {
            return {
                checked: false
            };
        }

        return {
            checked: true,
            ok: result.ok,
            status: result.status,
            statusText: result.statusText,
            durationMs: result.durationMs,
            error: result.error,
            retrievedAt: result.retrievedAt,
            payload: result.payload
        };
    }

    function extractPropertyStatusSummary() {
        const payload = state.lastPropertyStatusPayload || {};
        const propertyRouter = getPath(payload, "router") || {};
        const files = getPath(payload, "files") || {};
        const governance = getPath(payload, "governance") || {};

        return {
            router_loaded: propertyRouter.loaded ?? null,
            router_error: propertyRouter.error ?? null,
            models_exists: getPath(files, "property_models.exists") ?? null,
            public_records_engine_exists: getPath(files, "public_records_engine.exists") ?? null,
            governance
        };
    }

    function renderRawPayload() {
        const element = byId(SELECTORS.rawPayload);

        if (!element) {
            return;
        }

        element.textContent = prettyJson(buildRawPayload());
    }


    /* ============================================================
    SECTION 12 - DASHBOARD REFRESH
    ============================================================ */

    async function refreshCoreStatus() {
        const results = await Promise.allSettled([
            safeEndpoint("health", API.health),
            safeEndpoint("platform", API.platform),
            safeEndpoint("routes", API.routes),
            safeEndpoint("diagnostics", API.diagnostics),
            safeEndpoint("aiStatus", API.aiStatus),
            safeEndpoint("propertyStatus", API.propertyStatus),
            safeEndpoint("propertiesHealth", API.propertiesHealth),
            safeEndpoint("propertiesReadiness", API.propertiesReadiness),
            safeEndpoint("dashboardStatus", API.dashboardStatus),
            safeEndpoint("dashboardBootstrap", API.dashboardBootstrap),
            safeEndpoint("memoryStatus", API.chatMemoryStatus),
            safeEndpoint("trainingStatus", API.chatTrainingStatus),
            safeEndpoint("reviewQueue", API.chatReviewQueue),
            safeEndpoint("promptStatus", API.chatPromptStatus)
        ]);

        for (const result of results) {
            if (result.status === "rejected") {
                state.errors.push({
                    type: "refresh_error",
                    message: result.reason ? String(result.reason) : "Unknown refresh error",
                    at: nowIso()
                });
            }
        }

        state.lastHealthPayload = state.endpointResults.health?.payload || null;
        state.lastDiagnosticsPayload = state.endpointResults.diagnostics?.payload || null;
        state.lastPropertyStatusPayload = state.endpointResults.propertyStatus?.payload || null;
        state.lastPropertyRouterPayload = state.endpointResults.propertiesHealth?.payload || null;
        state.lastStatusPayload = state.endpointResults.dashboardStatus?.payload || null;
        state.lastBootstrapPayload = state.endpointResults.dashboardBootstrap?.payload || null;
        state.lastMemoryPayload = state.endpointResults.memoryStatus?.payload || null;
        state.lastTrainingPayload = state.endpointResults.trainingStatus?.payload || null;
        state.lastReviewPayload = state.endpointResults.reviewQueue?.payload || null;
        state.lastPromptPayload = state.endpointResults.promptStatus?.payload || null;
    }

    async function refreshDashboard() {
        await refreshCoreStatus();

        renderMetrics();
        renderTrainingPanel();
        renderMemoryPanel();
        renderRawPayload();
        renderReadinessNotices();
    }

    function renderReadinessNotices() {
        const propertyStatus = state.lastPropertyStatusPayload;
        const propertyHealth = state.endpointResults.propertiesHealth;

        if (!state.initialized) {
            return;
        }

        if (propertyStatus && propertyStatus.router && propertyStatus.router.loaded === false) {
            renderSystemNotice(
                `Property router is not loaded: ${propertyStatus.router.error || "unknown error"}`,
                "warning"
            );
        }

        if (propertyHealth && propertyHealth.ok === false) {
            renderSystemNotice(
                "Property API health endpoint is not currently available. Check /diagnostics and /property-intelligence/status.",
                "warning"
            );
        }
    }


    /* ============================================================
    SECTION 13 - PROPERTY PREVIEW SUPPORT
    ============================================================ */

    async function previewProperty(address) {
        const cleanAddress = safeString(address);

        if (!cleanAddress) {
            return null;
        }

        const result = await safeEndpoint("propertyPreview", API.propertyPreview, {
            method: "POST",
            body: {
                address: cleanAddress,
                strict_source_mode: true,
                source: "dashboard_preview"
            }
        });

        return result;
    }

    async function propertyRouterHealthCheck() {
        const health = await safeEndpoint("propertiesHealth", API.propertiesHealth);
        const readiness = await safeEndpoint("propertiesReadiness", API.propertiesReadiness);

        return {
            health,
            readiness
        };
    }


    /* ============================================================
    SECTION 14 - KEYBOARD AND UI SHORTCUTS
    ============================================================ */

    function bindKeyboardShortcuts() {
        document.addEventListener("keydown", function (event) {
            const isMac = navigator.platform.toUpperCase().includes("MAC");
            const commandPressed = isMac ? event.metaKey : event.ctrlKey;

            if (commandPressed && event.key.toLowerCase() === "k") {
                event.preventDefault();

                const messageInput = byId(SELECTORS.messageInput);

                if (messageInput) {
                    messageInput.focus();
                }
            }

            if (commandPressed && event.key.toLowerCase() === "r") {
                event.preventDefault();
                refreshDashboard();
            }
        });
    }

    function bindDynamicActionButtons() {
        document.addEventListener("click", function (event) {
            const target = event.target;

            if (!target || !target.matches) {
                return;
            }

            if (target.matches("[data-aussem-refresh]")) {
                event.preventDefault();
                refreshDashboard();
            }

            if (target.matches("[data-aussem-property-health]")) {
                event.preventDefault();
                propertyRouterHealthCheck().then(renderRawPayload);
            }
        });
    }


    /* ============================================================
    SECTION 15 - STARTUP SELF TESTS
    ============================================================ */

    async function verifyStaticAssets() {
        const checks = await Promise.allSettled([
            fetch("/static/css/dashboard.css", { method: "HEAD" }),
            fetch("/static/js/dashboard.js", { method: "HEAD" })
        ]);

        const cssOk = checks[0].status === "fulfilled" && checks[0].value.ok;
        const jsOk = checks[1].status === "fulfilled" && checks[1].value.ok;

        state.endpointResults.staticAssets = {
            checked: true,
            cssOk,
            jsOk,
            checkedAt: nowIso()
        };

        if (!cssOk) {
            state.warnings.push({
                type: "static_asset_warning",
                message: "Dashboard CSS did not pass HEAD verification.",
                at: nowIso()
            });
        }

        if (!jsOk) {
            state.warnings.push({
                type: "static_asset_warning",
                message: "Dashboard JS did not pass HEAD verification.",
                at: nowIso()
            });
        }
    }

    function renderStartupMessage() {
        renderSystemNotice(
            [
                "Aussem1 dashboard controller loaded.",
                "Strict source mode is active.",
                "Public records can support parcel, tax, deed, GIS, MOD-IV, and ownership-reference context.",
                "Current listing status and current listing price require a future authorized listing feed."
            ].join("\n"),
            "ready"
        );
    }


    /* ============================================================
    SECTION 16 - INITIALIZATION
    ============================================================ */

    async function initializeDashboard() {
        state.sessionId = makeSessionId();

        setText(SELECTORS.sessionId, `Session: ${state.sessionId.slice(0, 18)}…`);

        bindChatForm();
        bindHeroForm();
        bindKeyboardShortcuts();
        bindDynamicActionButtons();

        renderStartupMessage();

        await verifyStaticAssets();
        await refreshDashboard();

        if (state.refreshTimer) {
            window.clearInterval(state.refreshTimer);
        }

        state.refreshTimer = window.setInterval(function () {
            refreshDashboard();
        }, DEFAULTS.refreshIntervalMs);

        state.initialized = true;

        window.AussemDashboard = {
            state,
            api: API,
            refresh: refreshDashboard,
            submitChat,
            previewProperty,
            propertyRouterHealthCheck,
            version: AUSSEM_DASHBOARD.version,
            phase: AUSSEM_DASHBOARD.phase
        };
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeDashboard);
    } else {
        initializeDashboard();
    }
}());