# ============================================================
# AUSSEM1
# PHASE 1.00 PART 10
# ENTERPRISE CHATBOT MEMORY STORE
# FILE: app/chatbot/memory_store.py
# PURPOSE:
# Store chatbot session memory, recent conversation context,
# property-address context, and future training signals.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# FOUNDATION ACTIVE
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
from pathlib import Path
from typing import Any


# ============================================================
# SECTION 02 - MEMORY CONFIGURATION
# ============================================================

MEMORY_DIRECTORY = Path("app/data")

MEMORY_FILE = MEMORY_DIRECTORY / "chat_memory.json"

MEMORY_VERSION = "0.1.0"

MEMORY_PHASE = "PHASE 1.00 PART 10"


# ============================================================
# SECTION 03 - MEMORY MESSAGE MODEL
# ============================================================

@dataclass
class MemoryMessage:
    """
    Represents one stored chatbot message.

    This model preserves the role, message content, timestamp,
    property context, and metadata needed for future AI context
    building.
    """

    timestamp: str

    session_id: str

    role: str

    content: str

    property_address: str | None

    intent: str | None

    metadata: dict[str, Any]


# ============================================================
# SECTION 04 - MEMORY STORE CLASS
# ============================================================

class MemoryStore:
    """
    Enterprise memory store for chatbot conversations.

    Current Storage:
    • JSON file storage for early development

    Future Storage:
    • SQLite
    • PostgreSQL
    • Vector database
    • Semantic memory index
    • User-specific memory permissions
    """

    def __init__(self) -> None:

        MEMORY_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not MEMORY_FILE.exists():
            MEMORY_FILE.write_text(
                "[]",
                encoding="utf-8",
            )


# ============================================================
# SECTION 05 - SAVE MESSAGE
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
    ) -> None:
        """
        Save a single conversation message.
        """

        message = MemoryMessage(
            timestamp=datetime.now(UTC).isoformat(),

            session_id=session_id,

            role=role,

            content=content,

            property_address=property_address,

            intent=intent,

            metadata=metadata or {},
        )

        messages = self._load_messages()

        messages.append(asdict(message))

        self._save_messages(messages)


# ============================================================
# SECTION 06 - LOAD SESSION MEMORY
# ============================================================

    def get_session_messages(
        self,
        session_id: str,
    ) -> list[dict]:
        """
        Return all messages for a single session.
        """

        return [

            message

            for message in self._load_messages()

            if message["session_id"] == session_id

        ]


# ============================================================
# SECTION 07 - LOAD RECENT MEMORY
# ============================================================

    def get_recent_messages(
        self,
        *,
        session_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Return the most recent messages from a session.
        """

        session_messages = self.get_session_messages(
            session_id=session_id,
        )

        return session_messages[-limit:]


# ============================================================
# SECTION 08 - PROPERTY ADDRESS MEMORY
# ============================================================

    def get_property_history(
        self,
        property_address: str,
    ) -> list[dict]:
        """
        Return memory records tied to a specific property address.
        """

        normalized_address = property_address.lower().strip()

        return [

            message

            for message in self._load_messages()

            if message.get("property_address")
            and message["property_address"].lower().strip()
            == normalized_address

        ]


# ============================================================
# SECTION 09 - MEMORY ANALYTICS
# ============================================================

    def total_messages(self) -> int:
        """
        Return total stored messages.
        """

        return len(self._load_messages())


    def total_sessions(self) -> int:
        """
        Return total unique chatbot sessions.
        """

        return len(
            {
                message["session_id"]

                for message in self._load_messages()
            }
        )


# ============================================================
# SECTION 10 - INTERNAL LOAD METHOD
# ============================================================

    def _load_messages(self) -> list[dict]:

        with MEMORY_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)


# ============================================================
# SECTION 11 - INTERNAL SAVE METHOD
# ============================================================

    def _save_messages(
        self,
        messages: list[dict],
    ) -> None:

        with MEMORY_FILE.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                messages,
                file,
                indent=4,
                ensure_ascii=False,
            )


# ============================================================
# SECTION 12 - FUTURE ENTERPRISE EXPANSION
# ============================================================

#
# Planned Memory System Expansion
#
# • User-scoped memory
#
# • Property-scoped memory
#
# • Session summarization
#
# • Semantic memory retrieval
#
# • Vector embeddings
#
# • Memory expiration policies
#
# • Privacy controls
#
# • Admin review dashboard
#
# • Training dataset export
#
# • Long-term real estate knowledge graph
#
# ============================================================


# ============================================================
# END OF FILE
# ============================================================