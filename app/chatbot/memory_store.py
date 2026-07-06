# ============================================================
# AUSSEM1
# PHASE 1.00 PART 7.00
# ENTERPRISE AI MEMORY STORE
# FILE: app/chatbot/memory_store.py
# PURPOSE:
# Permanent enterprise memory architecture for the Aussem1 AI
# chatbot, property intelligence system, future RAG layer,
# training pipeline, and long-term contextual reasoning engine.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# ENTERPRISE FOUNDATION ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4


# ============================================================
# SECTION 02 - MEMORY VERSION CONFIGURATION
# ============================================================

MEMORY_SYSTEM_NAME = "Aussem1 Enterprise Memory Store"

MEMORY_SYSTEM_VERSION = "0.2.0"

MEMORY_SYSTEM_PHASE = "PHASE 1.00 PART 7.00"

MEMORY_SYSTEM_STATUS = "enterprise_foundation_active"


# ============================================================
# SECTION 03 - MEMORY FILESYSTEM CONFIGURATION
# ============================================================

MEMORY_DIRECTORY = Path("app/data")

MEMORY_FILE = MEMORY_DIRECTORY / "chat_memory.json"

SESSION_MEMORY_FILE = MEMORY_DIRECTORY / "session_memory.json"

PROPERTY_MEMORY_FILE = MEMORY_DIRECTORY / "property_memory.json"

USER_MEMORY_FILE = MEMORY_DIRECTORY / "user_memory.json"

KNOWLEDGE_MEMORY_FILE = MEMORY_DIRECTORY / "knowledge_memory.json"

MEMORY_INDEX_FILE = MEMORY_DIRECTORY / "memory_index.json"

MEMORY_SUMMARY_FILE = MEMORY_DIRECTORY / "memory_summaries.json"

MEMORY_EXPORT_FILE = MEMORY_DIRECTORY / "memory_export.json"


# ============================================================
# SECTION 04 - MEMORY ROLE ENUMERATION
# ============================================================

class MemoryRole(StrEnum):
    """
    Supported conversation roles.

    These roles allow the memory system to distinguish between
    user input, assistant responses, future system prompts, tool
    output, human review notes, and future broker/admin feedback.
    """

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    REVIEWER = "reviewer"
    ADMIN = "admin"


# ============================================================
# SECTION 05 - MEMORY TYPE ENUMERATION
# ============================================================

class MemoryType(StrEnum):
    """
    Memory type classification.

    This allows Aussem1 to organize memory into multiple durable
    layers instead of treating all messages as flat chat history.
    """

    CONVERSATION = "conversation"
    SESSION = "session"
    PROPERTY = "property"
    USER = "user"
    KNOWLEDGE = "knowledge"
    TRAINING_SIGNAL = "training_signal"
    SYSTEM_EVENT = "system_event"


# ============================================================
# SECTION 06 - MEMORY IMPORTANCE ENUMERATION
# ============================================================

class MemoryImportance(StrEnum):
    """
    Importance levels used for prioritizing future retrieval.
    """

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# SECTION 07 - MEMORY CONFIDENCE ENUMERATION
# ============================================================

class MemoryConfidence(StrEnum):
    """
    Confidence level for stored memory.
    """

    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"


# ============================================================
# SECTION 08 - MEMORY VISIBILITY ENUMERATION
# ============================================================

class MemoryVisibility(StrEnum):
    """
    Controls how memory may be used in future systems.
    """

    INTERNAL = "internal"
    CHAT_CONTEXT = "chat_context"
    TRAINING = "training"
    ADMIN_ONLY = "admin_only"
    DISABLED = "disabled"


# ============================================================
# SECTION 09 - MEMORY LIFECYCLE ENUMERATION
# ============================================================

class MemoryLifecycle(StrEnum):
    """
    Lifecycle status for stored memory.
    """

    ACTIVE = "active"
    ARCHIVED = "archived"
    REVIEW_REQUIRED = "review_required"
    DEPRECATED = "deprecated"
    DELETED = "deleted"


# ============================================================
# SECTION 10 - CORE MEMORY MESSAGE MODEL
# ============================================================

@dataclass
class MemoryMessage:
    """
    Represents one stored chatbot message.

    This model remains compatible with the original Phase 1
    chat engine but adds enough metadata to support future
    contextual retrieval, semantic search, property memory, and
    training intelligence.
    """

    memory_id: str
    timestamp: str
    memory_version: str
    memory_phase: str

    session_id: str
    role: str
    content: str

    property_address: str | None
    normalized_property_address: str | None

    intent: str | None
    user_id: str | None

    memory_type: str
    importance: str
    confidence: str
    visibility: str
    lifecycle: str

    tags: list[str]
    entities: list[str]
    source: str

    metadata: dict[str, Any]


# ============================================================
# SECTION 11 - SESSION MEMORY MODEL
# ============================================================

@dataclass
class SessionMemory:
    """
    Represents persistent metadata for one chat session.
    """

    session_id: str
    created_at: str
    updated_at: str

    user_id: str | None
    first_message: str | None
    last_message: str | None

    message_count: int
    property_addresses: list[str]
    detected_intents: list[str]
    session_summary: str | None

    confidence_average: float | None
    needs_review: bool

    metadata: dict[str, Any]


# ============================================================
# SECTION 12 - PROPERTY MEMORY MODEL
# ============================================================

@dataclass
class PropertyMemory:
    """
    Represents persistent memory tied to a property address.

    This is crucial for Aussem1 because the whole product centers
    on turning one address into complete real estate intelligence.
    """

    property_memory_id: str
    created_at: str
    updated_at: str

    raw_address: str
    normalized_address: str

    sessions: list[str]
    user_ids: list[str]
    intents: list[str]

    questions_asked: list[str]
    known_facts: list[dict[str, Any]]
    missing_information: list[str]

    valuation_notes: list[str]
    public_record_notes: list[str]
    comparable_notes: list[str]

    confidence_notes: list[str]
    review_required: bool

    metadata: dict[str, Any]


# ============================================================
# SECTION 13 - USER MEMORY MODEL
# ============================================================

@dataclass
class UserMemory:
    """
    Represents non-sensitive user-level memory.

    Sensitive personal data should not be placed here without
    clear user consent and future privacy controls.
    """

    user_id: str
    created_at: str
    updated_at: str

    session_ids: list[str]
    property_addresses: list[str]
    common_intents: list[str]

    preferences: dict[str, Any]
    saved_context: list[dict[str, Any]]

    review_required: bool
    metadata: dict[str, Any]


# ============================================================
# SECTION 14 - KNOWLEDGE MEMORY MODEL
# ============================================================

@dataclass
class KnowledgeMemory:
    """
    Represents a reusable knowledge item learned from repeated
    questions, reviewed corrections, or future expert input.
    """

    knowledge_id: str
    created_at: str
    updated_at: str

    topic: str
    content: str
    source_type: str
    confidence: str

    related_intents: list[str]
    related_properties: list[str]
    tags: list[str]

    approved_for_reuse: bool
    review_required: bool

    metadata: dict[str, Any]


# ============================================================
# SECTION 15 - MEMORY SUMMARY MODEL
# ============================================================

@dataclass
class MemorySummary:
    """
    Represents a generated or manually curated summary of memory.
    """

    summary_id: str
    created_at: str
    updated_at: str

    scope: str
    scope_id: str

    summary: str
    key_points: list[str]
    open_questions: list[str]
    property_addresses: list[str]
    intents: list[str]

    confidence: str
    metadata: dict[str, Any]


# ============================================================
# SECTION 16 - MEMORY INDEX ITEM MODEL
# ============================================================

@dataclass
class MemoryIndexItem:
    """
    Lightweight index entry for faster future lookup.

    This is a JSON-phase substitute for future vector indexes,
    PostgreSQL indexes, and knowledge graph edges.
    """

    index_id: str
    memory_id: str
    created_at: str

    session_id: str
    user_id: str | None
    property_address: str | None
    intent: str | None

    tags: list[str]
    entities: list[str]
    searchable_text: str
    importance: str


# ============================================================
# SECTION 17 - MEMORY STORE CLASS
# ============================================================

class MemoryStore:
    """
    Enterprise memory store for Aussem1.

    This class is responsible for storing and retrieving:

    • Conversation memory
    • Session memory
    • Property memory
    • User memory
    • Knowledge memory
    • Memory summaries
    • Memory indexes
    • Future RAG context

    Current storage:
    • JSON files for early development

    Future storage:
    • PostgreSQL
    • Vector database
    • Redis cache
    • Knowledge graph
    • Object storage
    """

    def __init__(self) -> None:
        """
        Initialize memory storage files.
        """

        MEMORY_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._ensure_json_array_file(MEMORY_FILE)
        self._ensure_json_array_file(SESSION_MEMORY_FILE)
        self._ensure_json_array_file(PROPERTY_MEMORY_FILE)
        self._ensure_json_array_file(USER_MEMORY_FILE)
        self._ensure_json_array_file(KNOWLEDGE_MEMORY_FILE)
        self._ensure_json_array_file(MEMORY_INDEX_FILE)
        self._ensure_json_array_file(MEMORY_SUMMARY_FILE)
        self._ensure_json_array_file(MEMORY_EXPORT_FILE)


# ============================================================
# SECTION 18 - PUBLIC SAVE MESSAGE INTERFACE
# ============================================================

    def save_message(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        property_address: str | None = None,
        intent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryMessage:
        """
        Save a single conversation message.

        This method preserves backward compatibility with the
        existing ChatEngine while adding enterprise memory indexing.
        """

        safe_metadata = metadata or {}

        user_id = safe_metadata.get("user_id")

        normalized_address = self._normalize_address(
            property_address,
        )

        tags = self._build_tags(
            role=role,
            intent=intent,
            property_address=normalized_address,
            metadata=safe_metadata,
        )

        entities = self._extract_entities(
            content=content,
            property_address=normalized_address,
        )

        importance = self._classify_importance(
            role=role,
            content=content,
            intent=intent,
            property_address=normalized_address,
            metadata=safe_metadata,
        )

        confidence = self._classify_memory_confidence(
            metadata=safe_metadata,
        )

        message = MemoryMessage(
            memory_id=self._new_memory_id(),
            timestamp=self._now(),
            memory_version=MEMORY_SYSTEM_VERSION,
            memory_phase=MEMORY_SYSTEM_PHASE,
            session_id=session_id,
            role=role,
            content=content,
            property_address=property_address,
            normalized_property_address=normalized_address,
            intent=intent,
            user_id=user_id,
            memory_type=MemoryType.CONVERSATION.value,
            importance=importance.value,
            confidence=confidence.value,
            visibility=MemoryVisibility.CHAT_CONTEXT.value,
            lifecycle=MemoryLifecycle.ACTIVE.value,
            tags=tags,
            entities=entities,
            source="chatbot",
            metadata=safe_metadata,
        )

        messages = self._load_json_array(MEMORY_FILE)

        messages.append(asdict(message))

        self._save_json_array(
            path=MEMORY_FILE,
            records=messages,
        )

        self._update_session_memory(
            message=message,
        )

        if normalized_address:
            self._update_property_memory(
                message=message,
            )

        if user_id:
            self._update_user_memory(
                message=message,
            )

        self._add_memory_index_item(
            message=message,
        )

        return message


# ============================================================
# SECTION 19 - SESSION MEMORY RETRIEVAL
# ============================================================

    def get_session_messages(
        self,
        session_id: str,
    ) -> list[dict]:
        """
        Return all active messages for a single session.
        """

        return [
            message
            for message in self._load_json_array(MEMORY_FILE)
            if message.get("session_id") == session_id
            and message.get("lifecycle") != MemoryLifecycle.DELETED.value
        ]


# ============================================================
# SECTION 20 - RECENT SESSION MEMORY
# ============================================================

    def get_recent_messages(
        self,
        *,
        session_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Return most recent messages for a session.
        """

        session_messages = self.get_session_messages(
            session_id=session_id,
        )

        return session_messages[-limit:]


# ============================================================
# SECTION 21 - PROPERTY MEMORY RETRIEVAL
# ============================================================

    def get_property_history(
        self,
        property_address: str,
    ) -> list[dict]:
        """
        Return conversation records tied to a property address.
        """

        normalized_address = self._normalize_address(
            property_address,
        )

        if not normalized_address:
            return []

        return [
            message
            for message in self._load_json_array(MEMORY_FILE)
            if message.get("normalized_property_address") == normalized_address
            and message.get("lifecycle") != MemoryLifecycle.DELETED.value
        ]


# ============================================================
# SECTION 22 - PROPERTY MEMORY PROFILE
# ============================================================

    def get_property_memory_profile(
        self,
        property_address: str,
    ) -> dict | None:
        """
        Return the persistent property memory profile.
        """

        normalized_address = self._normalize_address(
            property_address,
        )

        if not normalized_address:
            return None

        for profile in self._load_json_array(PROPERTY_MEMORY_FILE):
            if profile.get("normalized_address") == normalized_address:
                return profile

        return None


# ============================================================
# SECTION 23 - SESSION PROFILE RETRIEVAL
# ============================================================

    def get_session_profile(
        self,
        session_id: str,
    ) -> dict | None:
        """
        Return persistent session profile.
        """

        for session in self._load_json_array(SESSION_MEMORY_FILE):
            if session.get("session_id") == session_id:
                return session

        return None


# ============================================================
# SECTION 24 - USER MEMORY RETRIEVAL
# ============================================================

    def get_user_memory(
        self,
        user_id: str,
    ) -> dict | None:
        """
        Return non-sensitive user memory profile.
        """

        for user_memory in self._load_json_array(USER_MEMORY_FILE):
            if user_memory.get("user_id") == user_id:
                return user_memory

        return None


# ============================================================
# SECTION 25 - CONTEXT WINDOW BUILDER
# ============================================================

    def build_context_window(
        self,
        *,
        session_id: str,
        property_address: str | None = None,
        user_id: str | None = None,
        message_limit: int = 12,
    ) -> dict[str, Any]:
        """
        Build a structured memory context window for future LLM calls.

        This is the early JSON-backed version of what will later
        become a true RAG context builder.
        """

        recent_messages = self.get_recent_messages(
            session_id=session_id,
            limit=message_limit,
        )

        property_memory = None

        if property_address:
            property_memory = self.get_property_memory_profile(
                property_address=property_address,
            )

        user_memory = None

        if user_id:
            user_memory = self.get_user_memory(
                user_id=user_id,
            )

        session_profile = self.get_session_profile(
            session_id=session_id,
        )

        summaries = self.get_summaries_for_scope(
            scope="session",
            scope_id=session_id,
        )

        return {
            "memory_system": MEMORY_SYSTEM_NAME,
            "version": MEMORY_SYSTEM_VERSION,
            "phase": MEMORY_SYSTEM_PHASE,
            "session_id": session_id,
            "recent_messages": recent_messages,
            "session_profile": session_profile,
            "property_memory": property_memory,
            "user_memory": user_memory,
            "session_summaries": summaries,
            "generated_at": self._now(),
        }


# ============================================================
# SECTION 26 - SESSION MEMORY UPDATE
# ============================================================

    def _update_session_memory(
        self,
        *,
        message: MemoryMessage,
    ) -> None:
        """
        Update or create the session memory profile.
        """

        sessions = self._load_json_array(SESSION_MEMORY_FILE)

        existing = None

        for session in sessions:
            if session.get("session_id") == message.session_id:
                existing = session
                break

        if existing is None:
            new_session = SessionMemory(
                session_id=message.session_id,
                created_at=self._now(),
                updated_at=self._now(),
                user_id=message.user_id,
                first_message=message.content,
                last_message=message.content,
                message_count=1,
                property_addresses=self._unique_list(
                    [message.normalized_property_address]
                    if message.normalized_property_address
                    else []
                ),
                detected_intents=self._unique_list(
                    [message.intent]
                    if message.intent
                    else []
                ),
                session_summary=None,
                confidence_average=self._metadata_confidence(
                    message.metadata,
                ),
                needs_review=self._message_needs_review(message),
                metadata={
                    "source": "memory_store",
                    "created_from_memory_id": message.memory_id,
                },
            )

            sessions.append(asdict(new_session))

        else:
            existing["updated_at"] = self._now()
            existing["last_message"] = message.content
            existing["message_count"] = int(existing.get("message_count", 0)) + 1

            if message.user_id and not existing.get("user_id"):
                existing["user_id"] = message.user_id

            if message.normalized_property_address:
                existing["property_addresses"] = self._unique_list(
                    existing.get("property_addresses", [])
                    + [message.normalized_property_address]
                )

            if message.intent:
                existing["detected_intents"] = self._unique_list(
                    existing.get("detected_intents", [])
                    + [message.intent]
                )

            existing["needs_review"] = bool(
                existing.get("needs_review")
                or self._message_needs_review(message)
            )

            existing["confidence_average"] = self._calculate_session_confidence_average(
                session_id=message.session_id,
            )

        self._save_json_array(
            path=SESSION_MEMORY_FILE,
            records=sessions,
        )


# ============================================================
# SECTION 27 - PROPERTY MEMORY UPDATE
# ============================================================

    def _update_property_memory(
        self,
        *,
        message: MemoryMessage,
    ) -> None:
        """
        Update or create persistent property memory profile.
        """

        if not message.normalized_property_address:
            return

        properties = self._load_json_array(PROPERTY_MEMORY_FILE)

        existing = None

        for property_profile in properties:
            if (
                property_profile.get("normalized_address")
                == message.normalized_property_address
            ):
                existing = property_profile
                break

        question_text = message.content if message.role == MemoryRole.USER.value else None

        known_fact = self._extract_known_fact_from_message(
            message=message,
        )

        missing_items = self._extract_missing_information(
            message=message,
        )

        if existing is None:
            new_property = PropertyMemory(
                property_memory_id=self._new_property_memory_id(),
                created_at=self._now(),
                updated_at=self._now(),
                raw_address=message.property_address
                or message.normalized_property_address,
                normalized_address=message.normalized_property_address,
                sessions=[message.session_id],
                user_ids=self._unique_list(
                    [message.user_id]
                    if message.user_id
                    else []
                ),
                intents=self._unique_list(
                    [message.intent]
                    if message.intent
                    else []
                ),
                questions_asked=self._unique_list(
                    [question_text]
                    if question_text
                    else []
                ),
                known_facts=(
                    [known_fact]
                    if known_fact
                    else []
                ),
                missing_information=missing_items,
                valuation_notes=self._extract_note_by_intent(
                    message=message,
                    target_intent="property_value",
                ),
                public_record_notes=self._extract_note_by_intent(
                    message=message,
                    target_intent="public_records",
                ),
                comparable_notes=self._extract_note_by_intent(
                    message=message,
                    target_intent="comparable_analysis",
                ),
                confidence_notes=self._extract_confidence_notes(
                    message=message,
                ),
                review_required=self._message_needs_review(message),
                metadata={
                    "created_from_memory_id": message.memory_id,
                    "source": "memory_store",
                },
            )

            properties.append(asdict(new_property))

        else:
            existing["updated_at"] = self._now()
            existing["sessions"] = self._unique_list(
                existing.get("sessions", [])
                + [message.session_id]
            )

            if message.user_id:
                existing["user_ids"] = self._unique_list(
                    existing.get("user_ids", [])
                    + [message.user_id]
                )

            if message.intent:
                existing["intents"] = self._unique_list(
                    existing.get("intents", [])
                    + [message.intent]
                )

            if question_text:
                existing["questions_asked"] = self._unique_list(
                    existing.get("questions_asked", [])
                    + [question_text]
                )

            if known_fact:
                existing["known_facts"] = existing.get("known_facts", []) + [known_fact]

            existing["missing_information"] = self._unique_list(
                existing.get("missing_information", [])
                + missing_items
            )

            existing["valuation_notes"] = self._unique_list(
                existing.get("valuation_notes", [])
                + self._extract_note_by_intent(
                    message=message,
                    target_intent="property_value",
                )
            )

            existing["public_record_notes"] = self._unique_list(
                existing.get("public_record_notes", [])
                + self._extract_note_by_intent(
                    message=message,
                    target_intent="public_records",
                )
            )

            existing["comparable_notes"] = self._unique_list(
                existing.get("comparable_notes", [])
                + self._extract_note_by_intent(
                    message=message,
                    target_intent="comparable_analysis",
                )
            )

            existing["confidence_notes"] = self._unique_list(
                existing.get("confidence_notes", [])
                + self._extract_confidence_notes(message=message)
            )

            existing["review_required"] = bool(
                existing.get("review_required")
                or self._message_needs_review(message)
            )

        self._save_json_array(
            path=PROPERTY_MEMORY_FILE,
            records=properties,
        )


# ============================================================
# SECTION 28 - USER MEMORY UPDATE
# ============================================================

    def _update_user_memory(
        self,
        *,
        message: MemoryMessage,
    ) -> None:
        """
        Update or create non-sensitive user memory profile.
        """

        if not message.user_id:
            return

        users = self._load_json_array(USER_MEMORY_FILE)

        existing = None

        for user_memory in users:
            if user_memory.get("user_id") == message.user_id:
                existing = user_memory
                break

        if existing is None:
            new_user = UserMemory(
                user_id=message.user_id,
                created_at=self._now(),
                updated_at=self._now(),
                session_ids=[message.session_id],
                property_addresses=self._unique_list(
                    [message.normalized_property_address]
                    if message.normalized_property_address
                    else []
                ),
                common_intents=self._unique_list(
                    [message.intent]
                    if message.intent
                    else []
                ),
                preferences={},
                saved_context=[],
                review_required=self._message_needs_review(message),
                metadata={
                    "created_from_memory_id": message.memory_id,
                    "source": "memory_store",
                },
            )

            users.append(asdict(new_user))

        else:
            existing["updated_at"] = self._now()
            existing["session_ids"] = self._unique_list(
                existing.get("session_ids", [])
                + [message.session_id]
            )

            if message.normalized_property_address:
                existing["property_addresses"] = self._unique_list(
                    existing.get("property_addresses", [])
                    + [message.normalized_property_address]
                )

            if message.intent:
                existing["common_intents"] = self._unique_list(
                    existing.get("common_intents", [])
                    + [message.intent]
                )

            existing["review_required"] = bool(
                existing.get("review_required")
                or self._message_needs_review(message)
            )

        self._save_json_array(
            path=USER_MEMORY_FILE,
            records=users,
        )


# ============================================================
# SECTION 29 - MEMORY INDEXING
# ============================================================

    def _add_memory_index_item(
        self,
        *,
        message: MemoryMessage,
    ) -> None:
        """
        Add lightweight index record for future retrieval.
        """

        index_items = self._load_json_array(MEMORY_INDEX_FILE)

        index_item = MemoryIndexItem(
            index_id=self._new_index_id(),
            memory_id=message.memory_id,
            created_at=self._now(),
            session_id=message.session_id,
            user_id=message.user_id,
            property_address=message.normalized_property_address,
            intent=message.intent,
            tags=message.tags,
            entities=message.entities,
            searchable_text=self._build_searchable_text(message),
            importance=message.importance,
        )

        index_items.append(asdict(index_item))

        self._save_json_array(
            path=MEMORY_INDEX_FILE,
            records=index_items,
        )


# ============================================================
# SECTION 30 - MEMORY SEARCH
# ============================================================

    def search_memory(
        self,
        *,
        query: str,
        limit: int = 20,
    ) -> list[dict]:
        """
        Basic keyword search across memory index.

        Future versions will replace or supplement this with
        embeddings and semantic retrieval.
        """

        normalized_query = query.lower().strip()

        if not normalized_query:
            return []

        index_items = self._load_json_array(MEMORY_INDEX_FILE)

        matched_items = [
            item
            for item in index_items
            if normalized_query in item.get("searchable_text", "").lower()
        ]

        memory_ids = {
            item.get("memory_id")
            for item in matched_items[:limit]
        }

        return [
            message
            for message in self._load_json_array(MEMORY_FILE)
            if message.get("memory_id") in memory_ids
        ]


# ============================================================
# SECTION 31 - INTENT MEMORY SEARCH
# ============================================================

    def search_by_intent(
        self,
        *,
        intent: str,
        limit: int = 50,
    ) -> list[dict]:
        """
        Return messages matching a given intent.
        """

        matches = [
            message
            for message in self._load_json_array(MEMORY_FILE)
            if message.get("intent") == intent
        ]

        return matches[-limit:]


# ============================================================
# SECTION 32 - PROPERTY INTENT MEMORY
# ============================================================

    def search_property_intent_memory(
        self,
        *,
        property_address: str,
        intent: str,
        limit: int = 25,
    ) -> list[dict]:
        """
        Return messages for a property and intent.
        """

        normalized_address = self._normalize_address(
            property_address,
        )

        if not normalized_address:
            return []

        matches = [
            message
            for message in self._load_json_array(MEMORY_FILE)
            if message.get("normalized_property_address") == normalized_address
            and message.get("intent") == intent
        ]

        return matches[-limit:]


# ============================================================
# SECTION 33 - KNOWLEDGE MEMORY CREATION
# ============================================================

    def save_knowledge_memory(
        self,
        *,
        topic: str,
        content: str,
        source_type: str = "human_review",
        confidence: MemoryConfidence = MemoryConfidence.MEDIUM,
        related_intents: list[str] | None = None,
        related_properties: list[str] | None = None,
        tags: list[str] | None = None,
        approved_for_reuse: bool = False,
        review_required: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeMemory:
        """
        Save reusable knowledge memory.

        This is not for raw property facts.
        It is for reviewed learning, reusable rules, repeated
        explanations, and future knowledge graph inputs.
        """

        knowledge = KnowledgeMemory(
            knowledge_id=self._new_knowledge_id(),
            created_at=self._now(),
            updated_at=self._now(),
            topic=topic,
            content=content,
            source_type=source_type,
            confidence=confidence.value,
            related_intents=related_intents or [],
            related_properties=[
                self._normalize_address(address) or address
                for address in (related_properties or [])
            ],
            tags=tags or [],
            approved_for_reuse=approved_for_reuse,
            review_required=review_required,
            metadata=metadata or {},
        )

        knowledge_items = self._load_json_array(KNOWLEDGE_MEMORY_FILE)

        knowledge_items.append(asdict(knowledge))

        self._save_json_array(
            path=KNOWLEDGE_MEMORY_FILE,
            records=knowledge_items,
        )

        return knowledge


# ============================================================
# SECTION 34 - KNOWLEDGE MEMORY RETRIEVAL
# ============================================================

    def get_knowledge_by_topic(
        self,
        *,
        topic: str,
    ) -> list[dict]:
        """
        Return knowledge memory items matching a topic.
        """

        normalized_topic = topic.lower().strip()

        return [
            item
            for item in self._load_json_array(KNOWLEDGE_MEMORY_FILE)
            if normalized_topic in item.get("topic", "").lower()
        ]


# ============================================================
# SECTION 35 - MEMORY SUMMARY CREATION
# ============================================================

    def save_summary(
        self,
        *,
        scope: str,
        scope_id: str,
        summary: str,
        key_points: list[str] | None = None,
        open_questions: list[str] | None = None,
        property_addresses: list[str] | None = None,
        intents: list[str] | None = None,
        confidence: MemoryConfidence = MemoryConfidence.MEDIUM,
        metadata: dict[str, Any] | None = None,
    ) -> MemorySummary:
        """
        Save a memory summary.

        Scope examples:
        - session
        - property
        - user
        - topic
        """

        memory_summary = MemorySummary(
            summary_id=self._new_summary_id(),
            created_at=self._now(),
            updated_at=self._now(),
            scope=scope,
            scope_id=scope_id,
            summary=summary,
            key_points=key_points or [],
            open_questions=open_questions or [],
            property_addresses=[
                self._normalize_address(address) or address
                for address in (property_addresses or [])
            ],
            intents=intents or [],
            confidence=confidence.value,
            metadata=metadata or {},
        )

        summaries = self._load_json_array(MEMORY_SUMMARY_FILE)

        summaries.append(asdict(memory_summary))

        self._save_json_array(
            path=MEMORY_SUMMARY_FILE,
            records=summaries,
        )

        return memory_summary


# ============================================================
# SECTION 36 - MEMORY SUMMARY RETRIEVAL
# ============================================================

    def get_summaries_for_scope(
        self,
        *,
        scope: str,
        scope_id: str,
    ) -> list[dict]:
        """
        Return summaries for a scope and scope ID.
        """

        return [
            summary
            for summary in self._load_json_array(MEMORY_SUMMARY_FILE)
            if summary.get("scope") == scope
            and summary.get("scope_id") == scope_id
        ]


# ============================================================
# SECTION 37 - SESSION SUMMARY GENERATION
# ============================================================

    def generate_basic_session_summary(
        self,
        *,
        session_id: str,
    ) -> MemorySummary | None:
        """
        Generate a simple deterministic session summary.

        Future versions will use an LLM summary engine.
        """

        messages = self.get_session_messages(
            session_id=session_id,
        )

        if not messages:
            return None

        property_addresses = self._unique_list(
            [
                message.get("normalized_property_address")
                for message in messages
                if message.get("normalized_property_address")
            ]
        )

        intents = self._unique_list(
            [
                message.get("intent")
                for message in messages
                if message.get("intent")
            ]
        )

        user_questions = [
            message.get("content", "")
            for message in messages
            if message.get("role") == MemoryRole.USER.value
        ]

        summary_text = (
            f"Session {session_id} contains {len(messages)} messages. "
            f"Detected intents: {', '.join(intents) if intents else 'none'}. "
            f"Property addresses discussed: "
            f"{', '.join(property_addresses) if property_addresses else 'none'}."
        )

        return self.save_summary(
            scope="session",
            scope_id=session_id,
            summary=summary_text,
            key_points=user_questions[-5:],
            open_questions=[],
            property_addresses=property_addresses,
            intents=intents,
            confidence=MemoryConfidence.MEDIUM,
            metadata={
                "generated_by": "generate_basic_session_summary",
                "message_count": len(messages),
            },
        )


# ============================================================
# SECTION 38 - MEMORY ANALYTICS
# ============================================================

    def total_messages(self) -> int:
        """
        Return total stored conversation messages.
        """

        return len(self._load_json_array(MEMORY_FILE))


    def total_sessions(self) -> int:
        """
        Return total unique sessions.
        """

        return len(
            {
                message.get("session_id")
                for message in self._load_json_array(MEMORY_FILE)
                if message.get("session_id")
            }
        )


    def total_properties(self) -> int:
        """
        Return total unique property memory profiles.
        """

        return len(self._load_json_array(PROPERTY_MEMORY_FILE))


    def total_users(self) -> int:
        """
        Return total user memory profiles.
        """

        return len(self._load_json_array(USER_MEMORY_FILE))


    def total_knowledge_items(self) -> int:
        """
        Return total saved knowledge memory items.
        """

        return len(self._load_json_array(KNOWLEDGE_MEMORY_FILE))


# ============================================================
# SECTION 39 - MEMORY HEALTH REPORT
# ============================================================

    def memory_health_report(self) -> dict[str, Any]:
        """
        Return enterprise memory health report.
        """

        return {
            "memory_system": MEMORY_SYSTEM_NAME,
            "version": MEMORY_SYSTEM_VERSION,
            "phase": MEMORY_SYSTEM_PHASE,
            "status": MEMORY_SYSTEM_STATUS,
            "total_messages": self.total_messages(),
            "total_sessions": self.total_sessions(),
            "total_properties": self.total_properties(),
            "total_users": self.total_users(),
            "total_knowledge_items": self.total_knowledge_items(),
            "total_summaries": len(self._load_json_array(MEMORY_SUMMARY_FILE)),
            "total_index_items": len(self._load_json_array(MEMORY_INDEX_FILE)),
            "generated_at": self._now(),
        }


# ============================================================
# SECTION 40 - MEMORY EXPORT
# ============================================================

    def export_memory(
        self,
        *,
        include_messages: bool = True,
        include_sessions: bool = True,
        include_properties: bool = True,
        include_users: bool = False,
        include_knowledge: bool = True,
    ) -> dict[str, Any]:
        """
        Export memory for backup, diagnostics, or migration.
        """

        export_payload: dict[str, Any] = {
            "memory_system": MEMORY_SYSTEM_NAME,
            "version": MEMORY_SYSTEM_VERSION,
            "phase": MEMORY_SYSTEM_PHASE,
            "exported_at": self._now(),
        }

        if include_messages:
            export_payload["messages"] = self._load_json_array(MEMORY_FILE)

        if include_sessions:
            export_payload["sessions"] = self._load_json_array(SESSION_MEMORY_FILE)

        if include_properties:
            export_payload["properties"] = self._load_json_array(PROPERTY_MEMORY_FILE)

        if include_users:
            export_payload["users"] = self._load_json_array(USER_MEMORY_FILE)

        if include_knowledge:
            export_payload["knowledge"] = self._load_json_array(KNOWLEDGE_MEMORY_FILE)

        self._save_json_array(
            path=MEMORY_EXPORT_FILE,
            records=[export_payload],
        )

        return export_payload


# ============================================================
# SECTION 41 - TAG BUILDER
# ============================================================

    def _build_tags(
        self,
        *,
        role: str,
        intent: str | None,
        property_address: str | None,
        metadata: dict[str, Any],
    ) -> list[str]:
        """
        Build memory tags.
        """

        tags = [
            f"role:{role}",
        ]

        if intent:
            tags.append(f"intent:{intent}")

        if property_address:
            tags.append("property_context")

        if metadata.get("confidence") is not None:
            tags.append("confidence_scored")

        if metadata.get("engine_version"):
            tags.append(f"engine:{metadata.get('engine_version')}")

        return self._unique_list(tags)


# ============================================================
# SECTION 42 - ENTITY EXTRACTION
# ============================================================

    def _extract_entities(
        self,
        *,
        content: str,
        property_address: str | None,
    ) -> list[str]:
        """
        Basic entity extraction.

        Future versions will use proper NER and property-specific
        extraction.
        """

        entities: list[str] = []

        if property_address:
            entities.append(property_address)

        real_estate_terms = [
            "value",
            "status",
            "active",
            "sold",
            "under contract",
            "public records",
            "comparable",
            "comps",
            "tax",
            "assessment",
            "deed",
            "owner",
            "market",
            "investment",
        ]

        normalized_content = content.lower()

        for term in real_estate_terms:
            if term in normalized_content:
                entities.append(term)

        return self._unique_list(entities)


# ============================================================
# SECTION 43 - IMPORTANCE CLASSIFICATION
# ============================================================

    def _classify_importance(
        self,
        *,
        role: str,
        content: str,
        intent: str | None,
        property_address: str | None,
        metadata: dict[str, Any],
    ) -> MemoryImportance:
        """
        Classify memory importance.
        """

        confidence = metadata.get("confidence")

        if metadata.get("review_required"):
            return MemoryImportance.CRITICAL

        if property_address and intent in [
            "property_value",
            "property_status",
            "public_records",
            "comparable_analysis",
        ]:
            return MemoryImportance.HIGH

        if confidence is not None:
            try:
                if float(confidence) < 0.50:
                    return MemoryImportance.HIGH
            except (TypeError, ValueError):
                pass

        if role == MemoryRole.USER.value and len(content) > 120:
            return MemoryImportance.NORMAL

        return MemoryImportance.LOW


# ============================================================
# SECTION 44 - MEMORY CONFIDENCE CLASSIFICATION
# ============================================================

    def _classify_memory_confidence(
        self,
        *,
        metadata: dict[str, Any],
    ) -> MemoryConfidence:
        """
        Classify confidence from metadata.
        """

        confidence = metadata.get("confidence")

        if confidence is None:
            return MemoryConfidence.UNKNOWN

        try:
            value = float(confidence)
        except (TypeError, ValueError):
            return MemoryConfidence.UNKNOWN

        if value >= 0.90:
            return MemoryConfidence.VERIFIED

        if value >= 0.75:
            return MemoryConfidence.HIGH

        if value >= 0.55:
            return MemoryConfidence.MEDIUM

        return MemoryConfidence.LOW


# ============================================================
# SECTION 45 - KNOWN FACT EXTRACTION
# ============================================================

    def _extract_known_fact_from_message(
        self,
        *,
        message: MemoryMessage,
    ) -> dict[str, Any] | None:
        """
        Extract early known-fact candidate from a message.

        This does not mean the fact is verified.
        It creates a reviewable memory item.
        """

        if message.role != MemoryRole.ASSISTANT.value:
            return None

        if not message.intent:
            return None

        return {
            "memory_id": message.memory_id,
            "timestamp": message.timestamp,
            "intent": message.intent,
            "content": message.content,
            "confidence": message.confidence,
            "verified": False,
            "source": "assistant_response",
        }


# ============================================================
# SECTION 46 - MISSING INFORMATION EXTRACTION
# ============================================================

    def _extract_missing_information(
        self,
        *,
        message: MemoryMessage,
    ) -> list[str]:
        """
        Extract missing information from message metadata.
        """

        missing = message.metadata.get("missing_information")

        if isinstance(missing, list):
            return self._unique_list(missing)

        confidence_report = message.metadata.get("confidence_report")

        if isinstance(confidence_report, dict):
            factors_negative = confidence_report.get("factors_negative", [])

            if isinstance(factors_negative, list):
                return self._unique_list(
                    [
                        str(item)
                        for item in factors_negative
                    ]
                )

        return []


# ============================================================
# SECTION 47 - INTENT NOTES
# ============================================================

    def _extract_note_by_intent(
        self,
        *,
        message: MemoryMessage,
        target_intent: str,
    ) -> list[str]:
        """
        Extract notes for a target intent.
        """

        if message.intent != target_intent:
            return []

        return [
            message.content,
        ]


# ============================================================
# SECTION 48 - CONFIDENCE NOTES
# ============================================================

    def _extract_confidence_notes(
        self,
        *,
        message: MemoryMessage,
    ) -> list[str]:
        """
        Extract confidence notes from metadata.
        """

        confidence = message.metadata.get("confidence")

        if confidence is None:
            return []

        return [
            f"Memory {message.memory_id} confidence: {confidence}"
        ]


# ============================================================
# SECTION 49 - REVIEW DETECTION
# ============================================================

    def _message_needs_review(
        self,
        message: MemoryMessage,
    ) -> bool:
        """
        Determine whether a message should be reviewed.
        """

        if message.importance == MemoryImportance.CRITICAL.value:
            return True

        if message.confidence == MemoryConfidence.LOW.value:
            return True

        if message.metadata.get("review_required"):
            return True

        return False


# ============================================================
# SECTION 50 - SESSION CONFIDENCE AVERAGE
# ============================================================

    def _calculate_session_confidence_average(
        self,
        *,
        session_id: str,
    ) -> float | None:
        """
        Calculate average confidence for session messages.
        """

        values: list[float] = []

        for message in self.get_session_messages(session_id):
            confidence = message.get("metadata", {}).get("confidence")

            if confidence is None:
                continue

            try:
                values.append(float(confidence))
            except (TypeError, ValueError):
                continue

        if not values:
            return None

        return round(
            sum(values) / len(values),
            3,
        )


# ============================================================
# SECTION 51 - METADATA CONFIDENCE
# ============================================================

    def _metadata_confidence(
        self,
        metadata: dict[str, Any],
    ) -> float | None:
        """
        Extract confidence from metadata.
        """

        confidence = metadata.get("confidence")

        if confidence is None:
            return None

        try:
            return float(confidence)
        except (TypeError, ValueError):
            return None


# ============================================================
# SECTION 52 - SEARCHABLE TEXT BUILDER
# ============================================================

    def _build_searchable_text(
        self,
        message: MemoryMessage,
    ) -> str:
        """
        Build searchable memory text.
        """

        pieces = [
            message.content,
            message.session_id,
            message.role,
            message.intent or "",
            message.normalized_property_address or "",
            " ".join(message.tags),
            " ".join(message.entities),
        ]

        return " ".join(
            piece
            for piece in pieces
            if piece
        )


# ============================================================
# SECTION 53 - ADDRESS NORMALIZATION
# ============================================================

    def _normalize_address(
        self,
        address: str | None,
    ) -> str | None:
        """
        Normalize property address for matching.
        """

        if not address:
            return None

        return " ".join(
            address.lower().strip().split()
        )


# ============================================================
# SECTION 54 - UNIQUE LIST UTILITY
# ============================================================

    def _unique_list(
        self,
        values: list[Any],
    ) -> list[Any]:
        """
        Return stable unique list without empty values.
        """

        output: list[Any] = []

        for value in values:
            if value is None:
                continue

            if value == "":
                continue

            if value not in output:
                output.append(value)

        return output


# ============================================================
# SECTION 55 - JSON FILE OPERATIONS
# ============================================================

    def _ensure_json_array_file(
        self,
        path: Path,
    ) -> None:
        """
        Ensure file exists and contains a JSON array.
        """

        if not path.exists():
            path.write_text(
                "[]",
                encoding="utf-8",
            )
            return

        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8",
                )
            )

            if not isinstance(data, list):
                path.write_text(
                    "[]",
                    encoding="utf-8",
                )

        except json.JSONDecodeError:
            path.write_text(
                "[]",
                encoding="utf-8",
            )


    def _load_json_array(
        self,
        path: Path,
    ) -> list[dict]:
        """
        Load JSON array.
        """

        self._ensure_json_array_file(path)

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, list):
            return []

        return data


    def _save_json_array(
        self,
        *,
        path: Path,
        records: list[dict],
    ) -> None:
        """
        Save JSON array.
        """

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                records,
                file,
                indent=4,
                ensure_ascii=False,
            )


# ============================================================
# SECTION 56 - IDENTIFIER UTILITIES
# ============================================================

    def _new_memory_id(self) -> str:
        return f"memory-{uuid4()}"


    def _new_property_memory_id(self) -> str:
        return f"property-memory-{uuid4()}"


    def _new_knowledge_id(self) -> str:
        return f"knowledge-{uuid4()}"


    def _new_summary_id(self) -> str:
        return f"summary-{uuid4()}"


    def _new_index_id(self) -> str:
        return f"memory-index-{uuid4()}"


    def _now(self) -> str:
        return datetime.now(UTC).isoformat()


# ============================================================
# SECTION 57 - FUTURE POSTGRESQL MIGRATION NOTES
# ============================================================

#
# Planned PostgreSQL Tables:
#
# • chat_messages
# • chat_sessions
# • property_memory
# • user_memory
# • knowledge_memory
# • memory_summaries
# • memory_index
# • memory_embeddings
#
# Current JSON storage is acceptable for early architecture and
# live prototype deployment. It should be migrated before serious
# production traffic.
#
# ============================================================


# ============================================================
# SECTION 58 - FUTURE VECTOR DATABASE NOTES
# ============================================================

#
# Future Vector Memory:
#
# • Generate embeddings for each message.
# • Store semantic vectors.
# • Retrieve memory by meaning instead of keyword.
# • Rank by recency, relevance, confidence, and property context.
# • Combine with property intelligence and public records.
#
# ============================================================


# ============================================================
# SECTION 59 - FUTURE KNOWLEDGE GRAPH NOTES
# ============================================================

#
# Future Graph Relationships:
#
# User -> Session
# Session -> Property
# Property -> Question
# Property -> Valuation
# Property -> Comparable
# Property -> Public Record
# Question -> Intent
# Intent -> Data Source
# Data Source -> Confidence
#
# ============================================================


# ============================================================
# SECTION 60 - FUTURE PRIVACY AND GOVERNANCE NOTES
# ============================================================

#
# Future Controls:
#
# • User memory opt-out
# • Memory deletion requests
# • Sensitive data filters
# • Admin review dashboard
# • Data retention policies
# • Property data source attribution
# • Human approval before durable knowledge promotion
#
# ============================================================


# ============================================================
# END OF FILE
# ============================================================