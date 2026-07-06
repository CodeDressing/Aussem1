# ============================================================
# AUSSEM1
# PHASE 2.00 PART 1.09
# ENTERPRISE DATA PACKAGE INITIALIZATION
# FILE: app/data/__init__.py
# PURPOSE:
# Initialize the Aussem1 data package for local JSON storage,
# chatbot memory, property knowledge, training records, review
# queues, exports, and future migration into PostgreSQL.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# ENTERPRISE DATA PACKAGE ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - DATA PACKAGE IDENTITY
# ============================================================

DATA_PACKAGE_NAME = "Aussem1 Enterprise Data Layer"

DATA_PACKAGE_VERSION = "0.2.0"

DATA_PACKAGE_PHASE = "PHASE 2.00 PART 1.09"

DATA_PACKAGE_STATUS = "enterprise_data_package_active"

DATA_PACKAGE_DESCRIPTION = (
    "Local data package for Aussem1 JSON-backed memory, training, "
    "property knowledge, review queues, diagnostics, and future "
    "database migration preparation."
)


# ============================================================
# SECTION 02 - DATA LAYER MISSION
# ============================================================

DATA_LAYER_MISSION = (
    "Provide a stable early-development data foundation while "
    "preserving clean migration paths to PostgreSQL, vector search, "
    "object storage, and future enterprise analytics."
)


DATA_LAYER_PRINCIPLES = [
    "JSON storage is acceptable for early prototype persistence.",
    "Production traffic should eventually migrate to PostgreSQL.",
    "Training records must remain reviewable.",
    "Memory records must preserve source and confidence metadata.",
    "Property facts must not be treated as verified unless sourced.",
    "Data files should remain readable, structured, and exportable.",
    "No secrets should be stored in app/data.",
]


# ============================================================
# SECTION 03 - ACTIVE DATA FILE REGISTRY
# ============================================================

DATA_FILES = {
    "property_knowledge": {
        "path": "app/data/property_knowledge.json",
        "status": "active",
        "purpose": "Static property knowledge and early domain intelligence.",
    },
    "training_log": {
        "path": "app/data/training_log.json",
        "status": "active",
        "purpose": "Chatbot interaction records for supervised review.",
    },
    "training_review_queue": {
        "path": "app/data/training_review_queue.json",
        "status": "active",
        "purpose": "Low-confidence or review-required training records.",
    },
    "training_export": {
        "path": "app/data/training_export.json",
        "status": "active",
        "purpose": "Export-ready reviewed training dataset preview.",
    },
    "chat_memory": {
        "path": "app/data/chat_memory.json",
        "status": "active",
        "purpose": "Conversation-level chatbot memory.",
    },
    "session_memory": {
        "path": "app/data/session_memory.json",
        "status": "active",
        "purpose": "Session summaries, intents, and context.",
    },
    "property_memory": {
        "path": "app/data/property_memory.json",
        "status": "active",
        "purpose": "Memory connected to normalized property addresses.",
    },
    "user_memory": {
        "path": "app/data/user_memory.json",
        "status": "foundation_active",
        "purpose": "Non-sensitive user-level context.",
    },
    "knowledge_memory": {
        "path": "app/data/knowledge_memory.json",
        "status": "foundation_active",
        "purpose": "Reviewed reusable knowledge items.",
    },
    "memory_index": {
        "path": "app/data/memory_index.json",
        "status": "active",
        "purpose": "Keyword-searchable memory index.",
    },
    "memory_summaries": {
        "path": "app/data/memory_summaries.json",
        "status": "active",
        "purpose": "Session, property, user, and topic summaries.",
    },
    "memory_export": {
        "path": "app/data/memory_export.json",
        "status": "active",
        "purpose": "Memory backup and migration export.",
    },
}


# ============================================================
# SECTION 04 - DATA DOMAINS
# ============================================================

DATA_DOMAINS = {
    "chatbot_memory": "Conversation, session, and contextual memory.",
    "training": "Interaction logs, review queues, and supervised datasets.",
    "property_knowledge": "Static real estate knowledge and early property intelligence.",
    "property_memory": "Address-linked contextual intelligence.",
    "diagnostics": "Runtime, route, and dashboard inspection data.",
    "future_public_records": "County, assessor, deed, parcel, and tax data.",
    "future_valuation": "Valuation inputs, outputs, confidence, and explanations.",
    "future_comparables": "Comparable properties, similarity scores, and adjustments.",
    "future_market": "Market trend and demand/supply datasets.",
}


# ============================================================
# SECTION 05 - STORAGE GOVERNANCE
# ============================================================

DATA_GOVERNANCE = {
    "json_storage_allowed": True,
    "json_storage_phase": "prototype_and_foundation",
    "postgresql_required_before_production_scale": True,
    "private_api_keys_allowed": False,
    "secrets_allowed": False,
    "raw_sensitive_user_data_allowed": False,
    "training_review_required": True,
    "source_metadata_required_for_property_facts": True,
    "confidence_metadata_required_for_ai_outputs": True,
    "migration_path_required": True,
}


# ============================================================
# SECTION 06 - FUTURE DATABASE ROADMAP
# ============================================================

FUTURE_DATABASE_TABLES = {
    "chat_messages": "Persistent conversation records.",
    "chat_sessions": "Session metadata and summaries.",
    "property_profiles": "Structured property profiles.",
    "property_memory": "Property-linked memory and intelligence.",
    "training_records": "Supervised training interaction records.",
    "training_review_queue": "Human review workflow records.",
    "knowledge_memory": "Approved reusable knowledge.",
    "memory_embeddings": "Vector-search memory records.",
    "public_records": "County, assessor, deed, tax, and parcel records.",
    "valuation_outputs": "Estimated value ranges and confidence explanations.",
    "comparable_sets": "Comparable property groups and adjustments.",
    "market_snapshots": "Market trend snapshots.",
}


# ============================================================
# SECTION 07 - DATA PACKAGE DIAGNOSTICS
# ============================================================

def get_data_package_metadata() -> dict:
    """
    Return data package metadata.
    """

    return {
        "package": DATA_PACKAGE_NAME,
        "version": DATA_PACKAGE_VERSION,
        "phase": DATA_PACKAGE_PHASE,
        "status": DATA_PACKAGE_STATUS,
        "description": DATA_PACKAGE_DESCRIPTION,
        "mission": DATA_LAYER_MISSION,
    }


def get_data_files() -> dict:
    """
    Return active data file registry.
    """

    return DATA_FILES.copy()


def get_data_domains() -> dict:
    """
    Return data domain registry.
    """

    return DATA_DOMAINS.copy()


def get_data_governance() -> dict:
    """
    Return data governance rules.
    """

    return DATA_GOVERNANCE.copy()


def get_future_database_tables() -> dict:
    """
    Return future database table roadmap.
    """

    return FUTURE_DATABASE_TABLES.copy()


def get_data_package_health() -> dict:
    """
    Return lightweight data package health.
    """

    return {
        "package": DATA_PACKAGE_NAME,
        "version": DATA_PACKAGE_VERSION,
        "phase": DATA_PACKAGE_PHASE,
        "status": DATA_PACKAGE_STATUS,
        "registered_files": len(DATA_FILES),
        "registered_domains": len(DATA_DOMAINS),
        "future_database_tables": len(FUTURE_DATABASE_TABLES),
        "json_storage_active": DATA_GOVERNANCE["json_storage_allowed"],
        "production_database_planned": DATA_GOVERNANCE[
            "postgresql_required_before_production_scale"
        ],
    }


# ============================================================
# SECTION 08 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "DATA_PACKAGE_NAME",
    "DATA_PACKAGE_VERSION",
    "DATA_PACKAGE_PHASE",
    "DATA_PACKAGE_STATUS",
    "DATA_PACKAGE_DESCRIPTION",
    "DATA_LAYER_MISSION",
    "DATA_LAYER_PRINCIPLES",
    "DATA_FILES",
    "DATA_DOMAINS",
    "DATA_GOVERNANCE",
    "FUTURE_DATABASE_TABLES",
    "get_data_package_metadata",
    "get_data_files",
    "get_data_domains",
    "get_data_governance",
    "get_future_database_tables",
    "get_data_package_health",
]


# ============================================================
# END OF FILE
# ============================================================