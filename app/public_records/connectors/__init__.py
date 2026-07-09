# ============================================================
# AUSSEM1
# PHASE 2.20 PART 3.00
# ENTERPRISE PUBLIC RECORD CONNECTORS PACKAGE INITIALIZATION
# FILE: app/public_records/connectors/__init__.py
# PURPOSE:
# Initialize the Aussem1 public-record connector package.
#
# This package contains the real-data connector layer for official
# public records, including county tax board records, county clerk
# records, GIS parcel records, and statewide MOD-IV / parcel data.
#
# This file does not execute live lookups.
# This file does not create mock property records.
# This file does not fabricate property facts.
# This file does not claim active listing status from public records.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# REAL PUBLIC RECORD CONNECTOR PACKAGE ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Any


# ============================================================
# SECTION 02 - CONNECTOR PACKAGE IDENTITY
# ============================================================

PUBLIC_RECORD_CONNECTORS_PACKAGE_NAME = (
    "Aussem1 Enterprise Public Record Connectors"
)

PUBLIC_RECORD_CONNECTORS_PACKAGE_VERSION = "0.1.0"

PUBLIC_RECORD_CONNECTORS_PACKAGE_PHASE = "PHASE 2.20 PART 3.00"

PUBLIC_RECORD_CONNECTORS_PACKAGE_STATUS = (
    "real_public_record_connector_package_active"
)

PUBLIC_RECORD_CONNECTORS_RELEASE_CHANNEL = "development"

PUBLIC_RECORD_CONNECTORS_DESCRIPTION = (
    "Connector package for official public-record source integrations, "
    "including county tax-board records, county clerk recorded documents, "
    "GIS parcel data, and New Jersey statewide MOD-IV parcel data."
)


# ============================================================
# SECTION 03 - CONNECTOR PACKAGE MISSION
# ============================================================

PUBLIC_RECORD_CONNECTORS_MISSION = (
    "Provide a safe, source-governed, real-data-first connector layer "
    "that lets Aussem1 retrieve and normalize public records while "
    "preserving source attribution, source status, confidence, and "
    "manual-review requirements."
)


# ============================================================
# SECTION 04 - CONNECTOR PRINCIPLES
# ============================================================

PUBLIC_RECORD_CONNECTOR_PRINCIPLES = [
    "No mock connector responses.",
    "No fabricated public-record data.",
    "No fabricated tax assessments.",
    "No fabricated deeds.",
    "No fabricated parcel facts.",
    "No fabricated sale-history records.",
    "No fabricated owner conclusions.",
    "No active listing status from public records alone.",
    "No under-contract status from public records alone.",
    "Every connector must return a standard connector result.",
    "Every connector must return source status.",
    "Every connector must preserve source attribution.",
    "Every connector must return errors in a standard structure.",
    "Every connector must support unavailable/not-implemented status.",
    "Every ambiguous record must be marked for manual review.",
    "Every future connector must inherit the base connector contract.",
    "Official source paths are preferred over unofficial scraping.",
    "Public web access must be respectful, bounded, and source-governed.",
]


# ============================================================
# SECTION 05 - CONNECTOR STATUS CONSTANTS
# ============================================================

CONNECTOR_STATUS_READY = "ready"

CONNECTOR_STATUS_PLANNED = "planned"

CONNECTOR_STATUS_NOT_IMPLEMENTED = "not_implemented"

CONNECTOR_STATUS_AVAILABLE = "available"

CONNECTOR_STATUS_PARTIAL = "partial"

CONNECTOR_STATUS_EMPTY = "empty"

CONNECTOR_STATUS_ERROR = "error"

CONNECTOR_STATUS_AUTH_REQUIRED = "auth_required"

CONNECTOR_STATUS_RATE_LIMITED = "rate_limited"

CONNECTOR_STATUS_MANUAL_REVIEW_REQUIRED = "manual_review_required"

CONNECTOR_STATUS_DISABLED = "disabled"

CONNECTOR_STATUS_UNKNOWN = "unknown"


# ============================================================
# SECTION 06 - CONNECTOR DOMAIN CONSTANTS
# ============================================================

CONNECTOR_DOMAIN_TAX_BOARD = "tax_board"

CONNECTOR_DOMAIN_COUNTY_CLERK = "county_clerk"

CONNECTOR_DOMAIN_GIS = "gis"

CONNECTOR_DOMAIN_MODIV = "modiv"

CONNECTOR_DOMAIN_PARCEL = "parcel"

CONNECTOR_DOMAIN_ASSESSMENT = "assessment"

CONNECTOR_DOMAIN_DEED = "deed"

CONNECTOR_DOMAIN_MORTGAGE = "mortgage"

CONNECTOR_DOMAIN_LIEN = "lien"

CONNECTOR_DOMAIN_SALE_HISTORY = "sale_history"

CONNECTOR_DOMAIN_OWNER_REFERENCE = "owner_reference"

CONNECTOR_DOMAIN_PUBLIC_RECORDS = "public_records"

CONNECTOR_DOMAIN_UNKNOWN = "unknown"


# ============================================================
# SECTION 07 - CONNECTOR FILE PATHS
# ============================================================

CONNECTORS_ROOT = Path("app/public_records/connectors")

BASE_CONNECTOR_FILE = CONNECTORS_ROOT / "base_connector.py"

NJ_MORRIS_TAX_BOARD_CONNECTOR_FILE = (
    CONNECTORS_ROOT / "nj_morris_tax_board_connector.py"
)

NJ_MORRIS_CLERK_CONNECTOR_FILE = (
    CONNECTORS_ROOT / "nj_morris_clerk_connector.py"
)

NJ_MORRIS_GIS_CONNECTOR_FILE = (
    CONNECTORS_ROOT / "nj_morris_gis_connector.py"
)

NJ_STATE_MODIV_CONNECTOR_FILE = (
    CONNECTORS_ROOT / "nj_state_modiv_connector.py"
)


# ============================================================
# SECTION 08 - CONNECTOR MODULE REGISTRY
# ============================================================

CONNECTOR_MODULE_REGISTRY = {
    "base_connector": {
        "module": "app.public_records.connectors.base_connector",
        "file": str(BASE_CONNECTOR_FILE),
        "class_name": "BasePublicRecordConnector",
        "source_id": None,
        "connector_id": "base_public_record_connector",
        "status": CONNECTOR_STATUS_PLANNED,
        "domains": [
            CONNECTOR_DOMAIN_PUBLIC_RECORDS,
        ],
        "priority": 0,
        "required_for_batch": True,
    },
    "nj_morris_tax_board_connector": {
        "module": "app.public_records.connectors.nj_morris_tax_board_connector",
        "file": str(NJ_MORRIS_TAX_BOARD_CONNECTOR_FILE),
        "class_name": "NJMorrisTaxBoardConnector",
        "source_id": "nj_morris_tax_board",
        "connector_id": "nj_morris_tax_board_connector",
        "status": CONNECTOR_STATUS_PLANNED,
        "domains": [
            CONNECTOR_DOMAIN_TAX_BOARD,
            CONNECTOR_DOMAIN_ASSESSMENT,
            CONNECTOR_DOMAIN_PARCEL,
            CONNECTOR_DOMAIN_SALE_HISTORY,
            CONNECTOR_DOMAIN_OWNER_REFERENCE,
        ],
        "priority": 1,
        "required_for_batch": True,
    },
    "nj_morris_clerk_connector": {
        "module": "app.public_records.connectors.nj_morris_clerk_connector",
        "file": str(NJ_MORRIS_CLERK_CONNECTOR_FILE),
        "class_name": "NJMorrisClerkConnector",
        "source_id": "nj_morris_county_clerk_property_records",
        "connector_id": "nj_morris_clerk_connector",
        "status": CONNECTOR_STATUS_PLANNED,
        "domains": [
            CONNECTOR_DOMAIN_COUNTY_CLERK,
            CONNECTOR_DOMAIN_DEED,
            CONNECTOR_DOMAIN_MORTGAGE,
            CONNECTOR_DOMAIN_LIEN,
            CONNECTOR_DOMAIN_SALE_HISTORY,
            CONNECTOR_DOMAIN_OWNER_REFERENCE,
        ],
        "priority": 2,
        "required_for_batch": False,
    },
    "nj_morris_gis_connector": {
        "module": "app.public_records.connectors.nj_morris_gis_connector",
        "file": str(NJ_MORRIS_GIS_CONNECTOR_FILE),
        "class_name": "NJMorrisGISConnector",
        "source_id": "nj_morris_gis_parcel_searcher",
        "connector_id": "nj_morris_gis_connector",
        "status": CONNECTOR_STATUS_PLANNED,
        "domains": [
            CONNECTOR_DOMAIN_GIS,
            CONNECTOR_DOMAIN_PARCEL,
        ],
        "priority": 3,
        "required_for_batch": False,
    },
    "nj_state_modiv_connector": {
        "module": "app.public_records.connectors.nj_state_modiv_connector",
        "file": str(NJ_STATE_MODIV_CONNECTOR_FILE),
        "class_name": "NJStateModIVConnector",
        "source_id": "nj_state_parcels_modiv_composite",
        "connector_id": "nj_state_modiv_connector",
        "status": CONNECTOR_STATUS_PLANNED,
        "domains": [
            CONNECTOR_DOMAIN_MODIV,
            CONNECTOR_DOMAIN_PARCEL,
            CONNECTOR_DOMAIN_ASSESSMENT,
        ],
        "priority": 4,
        "required_for_batch": False,
    },
}


# ============================================================
# SECTION 09 - CONNECTOR BUILD ORDER
# ============================================================

CONNECTOR_BUILD_ORDER = [
    "app/public_records/connectors/__init__.py",
    "app/public_records/connectors/base_connector.py",
    "app/public_records/connectors/nj_morris_tax_board_connector.py",
    "app/public_records/connectors/nj_morris_clerk_connector.py",
    "app/public_records/connectors/nj_morris_gis_connector.py",
    "app/public_records/connectors/nj_state_modiv_connector.py",
]


# ============================================================
# SECTION 10 - BATCH 2 TRACKER
# ============================================================

BATCH_2_PUBLIC_RECORDS_FOUNDATION = {
    "batch_name": "BATCH 2 - Public Records Foundation",
    "commit_after_file_count": 5,
    "files": [
        {
            "order": 1,
            "file": "app/public_records/__init__.py",
            "status": "done",
        },
        {
            "order": 2,
            "file": "app/public_records/models.py",
            "status": "done",
        },
        {
            "order": 3,
            "file": "app/public_records/connectors/__init__.py",
            "status": "done",
        },
        {
            "order": 4,
            "file": "app/public_records/connectors/base_connector.py",
            "status": "next",
        },
        {
            "order": 5,
            "file": (
                "app/public_records/connectors/"
                "nj_morris_tax_board_connector.py"
            ),
            "status": "pending",
        },
    ],
    "commit_message": (
        "PHASE 2.20 PART 5.00 - Complete Public Records Foundation Batch"
    ),
}


# ============================================================
# SECTION 11 - CONNECTOR CLAIM MATRIX
# ============================================================

CONNECTOR_CLAIM_MATRIX = {
    "nj_morris_tax_board_connector": {
        "can_support": [
            "address_identity",
            "parcel_identity",
            "tax_assessment",
            "property_tax",
            "land_value",
            "improvement_value",
            "sale_history",
            "owner_reference",
            "property_class",
            "municipality",
            "county",
        ],
        "cannot_support": [
            "active_listing_status",
            "under_contract_status",
            "current_listing_price",
            "current_days_on_market",
            "current_showing_availability",
        ],
    },
    "nj_morris_clerk_connector": {
        "can_support": [
            "deed_reference",
            "mortgage_reference",
            "lien_reference",
            "sale_history",
            "owner_reference",
            "recorded_document_reference",
        ],
        "cannot_support": [
            "active_listing_status",
            "under_contract_status",
            "current_listing_price",
            "current_days_on_market",
            "current_showing_availability",
        ],
    },
    "nj_morris_gis_connector": {
        "can_support": [
            "address_identity",
            "parcel_identity",
            "lot_size",
            "municipality",
            "county",
            "gis_context",
            "tax_map_context",
            "geometry_context",
        ],
        "cannot_support": [
            "active_listing_status",
            "under_contract_status",
            "current_listing_price",
            "current_days_on_market",
            "current_showing_availability",
        ],
    },
    "nj_state_modiv_connector": {
        "can_support": [
            "address_identity",
            "parcel_identity",
            "tax_assessment",
            "property_tax",
            "land_value",
            "improvement_value",
            "property_class",
            "municipality",
            "county",
            "statewide_parcel_context",
        ],
        "cannot_support": [
            "active_listing_status",
            "under_contract_status",
            "current_listing_price",
            "current_days_on_market",
            "current_showing_availability",
        ],
    },
}


# ============================================================
# SECTION 12 - CONNECTOR GOVERNANCE RULES
# ============================================================

CONNECTOR_GOVERNANCE_RULES = {
    "mock_connector_responses_allowed": False,
    "mock_public_records_allowed": False,
    "fabricated_property_facts_allowed": False,
    "fabricated_listing_status_allowed": False,
    "source_attribution_required": True,
    "source_status_required": True,
    "retrieved_at_required": True,
    "confidence_required": True,
    "manual_review_for_ambiguity": True,
    "manual_review_for_conflicts": True,
    "base_connector_contract_required": True,
    "uncontrolled_scraping_allowed": False,
    "bypass_access_controls_allowed": False,
    "official_source_paths_preferred": True,
    "listing_status_requires_listing_feed": True,
}


# ============================================================
# SECTION 13 - UNSUPPORTED PUBLIC RECORD LISTING CLAIMS
# ============================================================

PUBLIC_RECORD_UNSUPPORTED_LISTING_CLAIMS = [
    "active_listing_status",
    "under_contract_status",
    "pending_status",
    "current_listing_price",
    "current_days_on_market",
    "current_showing_availability",
    "current_offer_deadline",
    "current_broker_confirmation",
    "current_mls_status",
]


# ============================================================
# SECTION 14 - UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(UTC).isoformat()


def normalize_connector_key(
    value: str | None,
) -> str:
    """
    Normalize connector key.
    """

    if not value:
        return ""

    return "_".join(
        str(value).strip().lower().replace("-", " ").split()
    )


def connector_exists(
    connector_key: str,
) -> bool:
    """
    Return whether connector exists in registry.
    """

    normalized = normalize_connector_key(connector_key)

    return normalized in CONNECTOR_MODULE_REGISTRY


def get_connector_metadata(
    connector_key: str,
) -> dict[str, Any] | None:
    """
    Return connector metadata.
    """

    normalized = normalize_connector_key(connector_key)

    connector = CONNECTOR_MODULE_REGISTRY.get(normalized)

    if connector is None:
        return None

    return connector.copy()


def get_all_connector_metadata() -> dict[str, dict[str, Any]]:
    """
    Return all connector metadata.
    """

    return {
        key: value.copy()
        for key, value in CONNECTOR_MODULE_REGISTRY.items()
    }


def get_connector_build_order() -> list[str]:
    """
    Return connector build order.
    """

    return list(CONNECTOR_BUILD_ORDER)


def get_batch_2_tracker() -> dict[str, Any]:
    """
    Return Batch 2 tracker.
    """

    return {
        "batch_name": BATCH_2_PUBLIC_RECORDS_FOUNDATION["batch_name"],
        "commit_after_file_count": BATCH_2_PUBLIC_RECORDS_FOUNDATION[
            "commit_after_file_count"
        ],
        "files": [
            item.copy()
            for item in BATCH_2_PUBLIC_RECORDS_FOUNDATION["files"]
        ],
        "commit_message": BATCH_2_PUBLIC_RECORDS_FOUNDATION[
            "commit_message"
        ],
    }


def get_connector_claim_matrix() -> dict[str, dict[str, list[str]]]:
    """
    Return connector claim matrix.
    """

    return {
        connector_id: {
            "can_support": list(claims["can_support"]),
            "cannot_support": list(claims["cannot_support"]),
        }
        for connector_id, claims in CONNECTOR_CLAIM_MATRIX.items()
    }


def get_connector_governance_rules() -> dict[str, Any]:
    """
    Return connector governance rules.
    """

    return CONNECTOR_GOVERNANCE_RULES.copy()


def get_unsupported_listing_claims() -> list[str]:
    """
    Return listing claims that public records cannot prove.
    """

    return list(PUBLIC_RECORD_UNSUPPORTED_LISTING_CLAIMS)


def can_connector_support_claim(
    connector_id: str,
    claim: str,
) -> bool:
    """
    Return whether connector can support a claim.
    """

    normalized_connector = normalize_connector_key(connector_id)
    normalized_claim = str(claim or "").strip().lower()

    claim_info = CONNECTOR_CLAIM_MATRIX.get(normalized_connector)

    if not claim_info:
        return False

    return normalized_claim in claim_info["can_support"]


def connector_cannot_support_claim(
    connector_id: str,
    claim: str,
) -> bool:
    """
    Return whether connector explicitly cannot support a claim.
    """

    normalized_connector = normalize_connector_key(connector_id)
    normalized_claim = str(claim or "").strip().lower()

    claim_info = CONNECTOR_CLAIM_MATRIX.get(normalized_connector)

    if not claim_info:
        return False

    return normalized_claim in claim_info["cannot_support"]


def claim_requires_listing_feed(
    claim: str,
) -> bool:
    """
    Return whether claim requires MLS/IDX/broker/listing feed data.
    """

    normalized_claim = str(claim or "").strip().lower()

    return normalized_claim in PUBLIC_RECORD_UNSUPPORTED_LISTING_CLAIMS


# ============================================================
# SECTION 15 - LAZY CONNECTOR IMPORTS
# ============================================================

def load_connector_class(
    connector_key: str,
) -> type[Any] | None:
    """
    Lazily load a connector class.

    This avoids import failures while future connector files are still
    being created one by one.
    """

    normalized = normalize_connector_key(connector_key)

    connector_metadata = CONNECTOR_MODULE_REGISTRY.get(normalized)

    if connector_metadata is None:
        return None

    module_name = connector_metadata["module"]
    class_name = connector_metadata["class_name"]

    try:
        module = import_module(module_name)
    except Exception:
        return None

    connector_class = getattr(
        module,
        class_name,
        None,
    )

    if connector_class is None:
        return None

    return connector_class


def load_available_connector_classes() -> dict[str, type[Any]]:
    """
    Load connector classes that currently exist.
    """

    loaded: dict[str, type[Any]] = {}

    for connector_key in CONNECTOR_MODULE_REGISTRY:
        connector_class = load_connector_class(connector_key)

        if connector_class is not None:
            loaded[connector_key] = connector_class

    return loaded


def get_connector_import_status() -> dict[str, dict[str, Any]]:
    """
    Return connector import status without raising.
    """

    status: dict[str, dict[str, Any]] = {}

    for connector_key, metadata in CONNECTOR_MODULE_REGISTRY.items():
        connector_class = load_connector_class(connector_key)

        status[connector_key] = {
            "connector_key": connector_key,
            "module": metadata["module"],
            "class_name": metadata["class_name"],
            "file": metadata["file"],
            "loaded": connector_class is not None,
            "source_id": metadata["source_id"],
            "declared_status": metadata["status"],
        }

    return status


# ============================================================
# SECTION 16 - CONNECTOR PACKAGE VALIDATION
# ============================================================

def validate_connector_registry() -> dict[str, Any]:
    """
    Validate connector registry metadata.
    """

    issues: list[dict[str, Any]] = []

    for connector_key, metadata in CONNECTOR_MODULE_REGISTRY.items():
        if not metadata.get("module"):
            issues.append(
                {
                    "connector_key": connector_key,
                    "issue_code": "missing_module",
                    "severity": "high",
                    "message": "Connector metadata is missing module path.",
                }
            )

        if not metadata.get("class_name"):
            issues.append(
                {
                    "connector_key": connector_key,
                    "issue_code": "missing_class_name",
                    "severity": "high",
                    "message": "Connector metadata is missing class name.",
                }
            )

        if metadata.get("source_id") is None and connector_key != "base_connector":
            issues.append(
                {
                    "connector_key": connector_key,
                    "issue_code": "missing_source_id",
                    "severity": "medium",
                    "message": "Connector metadata is missing source_id.",
                }
            )

        if not metadata.get("connector_id"):
            issues.append(
                {
                    "connector_key": connector_key,
                    "issue_code": "missing_connector_id",
                    "severity": "medium",
                    "message": "Connector metadata is missing connector_id.",
                }
            )

        if not metadata.get("domains"):
            issues.append(
                {
                    "connector_key": connector_key,
                    "issue_code": "missing_domains",
                    "severity": "medium",
                    "message": "Connector metadata is missing domains.",
                }
            )

    return {
        "valid": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "checked_at": utc_now(),
    }


def validate_connector_governance() -> dict[str, Any]:
    """
    Validate connector governance.
    """

    issues: list[dict[str, Any]] = []

    if CONNECTOR_GOVERNANCE_RULES["mock_connector_responses_allowed"]:
        issues.append(
            {
                "issue_code": "mock_connector_responses_enabled",
                "severity": "critical",
                "message": "Mock connector responses are not allowed.",
            }
        )

    if CONNECTOR_GOVERNANCE_RULES["mock_public_records_allowed"]:
        issues.append(
            {
                "issue_code": "mock_public_records_enabled",
                "severity": "critical",
                "message": "Mock public records are not allowed.",
            }
        )

    if CONNECTOR_GOVERNANCE_RULES["fabricated_listing_status_allowed"]:
        issues.append(
            {
                "issue_code": "fabricated_listing_status_enabled",
                "severity": "critical",
                "message": "Fabricated listing status is not allowed.",
            }
        )

    if not CONNECTOR_GOVERNANCE_RULES["source_attribution_required"]:
        issues.append(
            {
                "issue_code": "source_attribution_not_required",
                "severity": "critical",
                "message": "Source attribution must be required.",
            }
        )

    if not CONNECTOR_GOVERNANCE_RULES["listing_status_requires_listing_feed"]:
        issues.append(
            {
                "issue_code": "listing_feed_requirement_disabled",
                "severity": "critical",
                "message": "Listing status must require listing-feed source support.",
            }
        )

    return {
        "valid": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "checked_at": utc_now(),
    }


# ============================================================
# SECTION 17 - CONNECTOR PACKAGE DIAGNOSTICS
# ============================================================

def get_public_record_connectors_metadata() -> dict[str, Any]:
    """
    Return connector package metadata.
    """

    return {
        "package": PUBLIC_RECORD_CONNECTORS_PACKAGE_NAME,
        "version": PUBLIC_RECORD_CONNECTORS_PACKAGE_VERSION,
        "phase": PUBLIC_RECORD_CONNECTORS_PACKAGE_PHASE,
        "status": PUBLIC_RECORD_CONNECTORS_PACKAGE_STATUS,
        "release_channel": PUBLIC_RECORD_CONNECTORS_RELEASE_CHANNEL,
        "description": PUBLIC_RECORD_CONNECTORS_DESCRIPTION,
        "mission": PUBLIC_RECORD_CONNECTORS_MISSION,
        "generated_at": utc_now(),
    }


def get_public_record_connectors_health() -> dict[str, Any]:
    """
    Return lightweight connector package health.
    """

    registry_validation = validate_connector_registry()
    governance_validation = validate_connector_governance()
    import_status = get_connector_import_status()

    loaded_count = sum(
        1
        for item in import_status.values()
        if item["loaded"]
    )

    return {
        "package": PUBLIC_RECORD_CONNECTORS_PACKAGE_NAME,
        "version": PUBLIC_RECORD_CONNECTORS_PACKAGE_VERSION,
        "phase": PUBLIC_RECORD_CONNECTORS_PACKAGE_PHASE,
        "status": PUBLIC_RECORD_CONNECTORS_PACKAGE_STATUS,
        "connector_count": len(CONNECTOR_MODULE_REGISTRY),
        "loaded_connector_count": loaded_count,
        "registry_valid": registry_validation["valid"],
        "governance_valid": governance_validation["valid"],
        "mock_connector_responses_allowed": CONNECTOR_GOVERNANCE_RULES[
            "mock_connector_responses_allowed"
        ],
        "mock_public_records_allowed": CONNECTOR_GOVERNANCE_RULES[
            "mock_public_records_allowed"
        ],
        "listing_status_requires_listing_feed": CONNECTOR_GOVERNANCE_RULES[
            "listing_status_requires_listing_feed"
        ],
        "generated_at": utc_now(),
    }


def get_public_record_connectors_diagnostics() -> dict[str, Any]:
    """
    Return complete connector package diagnostics.
    """

    return {
        "metadata": get_public_record_connectors_metadata(),
        "health": get_public_record_connectors_health(),
        "principles": list(PUBLIC_RECORD_CONNECTOR_PRINCIPLES),
        "module_registry": get_all_connector_metadata(),
        "claim_matrix": get_connector_claim_matrix(),
        "governance_rules": get_connector_governance_rules(),
        "unsupported_listing_claims": get_unsupported_listing_claims(),
        "build_order": get_connector_build_order(),
        "batch_2_tracker": get_batch_2_tracker(),
        "import_status": get_connector_import_status(),
        "registry_validation": validate_connector_registry(),
        "governance_validation": validate_connector_governance(),
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 18 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "PUBLIC_RECORD_CONNECTORS_PACKAGE_NAME",
    "PUBLIC_RECORD_CONNECTORS_PACKAGE_VERSION",
    "PUBLIC_RECORD_CONNECTORS_PACKAGE_PHASE",
    "PUBLIC_RECORD_CONNECTORS_PACKAGE_STATUS",
    "PUBLIC_RECORD_CONNECTORS_RELEASE_CHANNEL",
    "PUBLIC_RECORD_CONNECTORS_DESCRIPTION",
    "PUBLIC_RECORD_CONNECTORS_MISSION",
    "PUBLIC_RECORD_CONNECTOR_PRINCIPLES",
    "CONNECTOR_STATUS_READY",
    "CONNECTOR_STATUS_PLANNED",
    "CONNECTOR_STATUS_NOT_IMPLEMENTED",
    "CONNECTOR_STATUS_AVAILABLE",
    "CONNECTOR_STATUS_PARTIAL",
    "CONNECTOR_STATUS_EMPTY",
    "CONNECTOR_STATUS_ERROR",
    "CONNECTOR_STATUS_AUTH_REQUIRED",
    "CONNECTOR_STATUS_RATE_LIMITED",
    "CONNECTOR_STATUS_MANUAL_REVIEW_REQUIRED",
    "CONNECTOR_STATUS_DISABLED",
    "CONNECTOR_STATUS_UNKNOWN",
    "CONNECTOR_DOMAIN_TAX_BOARD",
    "CONNECTOR_DOMAIN_COUNTY_CLERK",
    "CONNECTOR_DOMAIN_GIS",
    "CONNECTOR_DOMAIN_MODIV",
    "CONNECTOR_DOMAIN_PARCEL",
    "CONNECTOR_DOMAIN_ASSESSMENT",
    "CONNECTOR_DOMAIN_DEED",
    "CONNECTOR_DOMAIN_MORTGAGE",
    "CONNECTOR_DOMAIN_LIEN",
    "CONNECTOR_DOMAIN_SALE_HISTORY",
    "CONNECTOR_DOMAIN_OWNER_REFERENCE",
    "CONNECTOR_DOMAIN_PUBLIC_RECORDS",
    "CONNECTOR_DOMAIN_UNKNOWN",
    "CONNECTORS_ROOT",
    "BASE_CONNECTOR_FILE",
    "NJ_MORRIS_TAX_BOARD_CONNECTOR_FILE",
    "NJ_MORRIS_CLERK_CONNECTOR_FILE",
    "NJ_MORRIS_GIS_CONNECTOR_FILE",
    "NJ_STATE_MODIV_CONNECTOR_FILE",
    "CONNECTOR_MODULE_REGISTRY",
    "CONNECTOR_BUILD_ORDER",
    "BATCH_2_PUBLIC_RECORDS_FOUNDATION",
    "CONNECTOR_CLAIM_MATRIX",
    "CONNECTOR_GOVERNANCE_RULES",
    "PUBLIC_RECORD_UNSUPPORTED_LISTING_CLAIMS",
    "utc_now",
    "normalize_connector_key",
    "connector_exists",
    "get_connector_metadata",
    "get_all_connector_metadata",
    "get_connector_build_order",
    "get_batch_2_tracker",
    "get_connector_claim_matrix",
    "get_connector_governance_rules",
    "get_unsupported_listing_claims",
    "can_connector_support_claim",
    "connector_cannot_support_claim",
    "claim_requires_listing_feed",
    "load_connector_class",
    "load_available_connector_classes",
    "get_connector_import_status",
    "validate_connector_registry",
    "validate_connector_governance",
    "get_public_record_connectors_metadata",
    "get_public_record_connectors_health",
    "get_public_record_connectors_diagnostics",
]


# ============================================================
# END OF FILE
# ============================================================