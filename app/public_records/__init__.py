# ============================================================
# AUSSEM1
# PHASE 2.20 PART 1.00
# ENTERPRISE PUBLIC RECORDS PACKAGE INITIALIZATION
# FILE: app/public_records/__init__.py
# PURPOSE:
# Initialize the Aussem1 public records intelligence package.
#
# This package is responsible for the real-data-first public
# records layer used by Aussem1 property intelligence.
#
# Public records may support:
# - parcel identity
# - tax assessment context
# - property tax context
# - deed references
# - mortgage references
# - sale-history references
# - municipal/county/state property context
#
# Public records do not, by themselves, prove:
# - current active MLS status
# - under-contract status
# - current listing price
# - current showing availability
# - current offer deadline
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# REAL PUBLIC RECORDS FOUNDATION ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any


# ============================================================
# SECTION 02 - PACKAGE IDENTITY
# ============================================================

PUBLIC_RECORDS_PACKAGE_NAME = "Aussem1 Enterprise Public Records Intelligence"

PUBLIC_RECORDS_PACKAGE_VERSION = "0.1.0"

PUBLIC_RECORDS_PACKAGE_PHASE = "PHASE 2.20 PART 1.00"

PUBLIC_RECORDS_PACKAGE_STATUS = "real_public_records_foundation_active"

PUBLIC_RECORDS_RELEASE_CHANNEL = "development"

PUBLIC_RECORDS_DESCRIPTION = (
    "Public records intelligence package for parcel, tax, deed, "
    "assessment, sale-history, municipal, county, and state-level "
    "property data used by Aussem1."
)


# ============================================================
# SECTION 03 - PACKAGE MISSION
# ============================================================

PUBLIC_RECORDS_MISSION = (
    "Build a real-data-first public records foundation that lets "
    "Aussem1 retrieve, normalize, attribute, and explain official "
    "property records without fabricating homes, facts, values, "
    "listing status, or comparable sales."
)


# ============================================================
# SECTION 04 - PUBLIC RECORDS PRINCIPLES
# ============================================================

PUBLIC_RECORDS_PRINCIPLES = [
    "No mock public records.",
    "No fake parcel records.",
    "No fake tax records.",
    "No fake deed records.",
    "No fake sale-history records.",
    "No fake ownership conclusions.",
    "No fake assessment values.",
    "No fake active listing status from public records.",
    "No fake under-contract status from public records.",
    "Every retrieved record must carry source attribution.",
    "Every source lookup must carry source status.",
    "Every unavailable record must be labeled unavailable.",
    "Every ambiguous record must be marked for review.",
    "Every connector must follow the common connector contract.",
    "Public records support property context; they do not replace MLS/listing feeds.",
]


# ============================================================
# SECTION 05 - PUBLIC RECORD DOMAIN CONSTANTS
# ============================================================

PUBLIC_RECORD_DOMAIN_PARCEL = "parcel"

PUBLIC_RECORD_DOMAIN_TAX_ASSESSMENT = "tax_assessment"

PUBLIC_RECORD_DOMAIN_PROPERTY_TAX = "property_tax"

PUBLIC_RECORD_DOMAIN_DEED = "deed"

PUBLIC_RECORD_DOMAIN_MORTGAGE = "mortgage"

PUBLIC_RECORD_DOMAIN_LIEN = "lien"

PUBLIC_RECORD_DOMAIN_SALE_HISTORY = "sale_history"

PUBLIC_RECORD_DOMAIN_OWNER_REFERENCE = "owner_reference"

PUBLIC_RECORD_DOMAIN_BUILDING_FACTS = "building_facts"

PUBLIC_RECORD_DOMAIN_MUNICIPAL = "municipal"

PUBLIC_RECORD_DOMAIN_COUNTY = "county"

PUBLIC_RECORD_DOMAIN_STATE = "state"

PUBLIC_RECORD_DOMAIN_GIS = "gis"

PUBLIC_RECORD_DOMAIN_MODIV = "modiv"

PUBLIC_RECORD_DOMAIN_UNKNOWN = "unknown"


# ============================================================
# SECTION 06 - PUBLIC RECORD STATUS CONSTANTS
# ============================================================

PUBLIC_RECORD_STATUS_AVAILABLE = "available"

PUBLIC_RECORD_STATUS_PARTIAL = "partial"

PUBLIC_RECORD_STATUS_UNAVAILABLE = "unavailable"

PUBLIC_RECORD_STATUS_NOT_CONNECTED = "not_connected"

PUBLIC_RECORD_STATUS_NOT_IMPLEMENTED = "not_implemented"

PUBLIC_RECORD_STATUS_SOURCE_ERROR = "source_error"

PUBLIC_RECORD_STATUS_MANUAL_REVIEW_REQUIRED = "manual_review_required"

PUBLIC_RECORD_STATUS_AMBIGUOUS = "ambiguous"

PUBLIC_RECORD_STATUS_EMPTY = "empty"

PUBLIC_RECORD_STATUS_UNKNOWN = "unknown"


# ============================================================
# SECTION 07 - ACTIVE PACKAGE FILE REGISTRY
# ============================================================

PUBLIC_RECORDS_FILE_REGISTRY = {
    "package_init": "app/public_records/__init__.py",
    "models": "app/public_records/models.py",
    "connectors_init": "app/public_records/connectors/__init__.py",
    "base_connector": "app/public_records/connectors/base_connector.py",
    "morris_tax_board_connector": (
        "app/public_records/connectors/"
        "nj_morris_tax_board_connector.py"
    ),
    "morris_clerk_connector": (
        "app/public_records/connectors/"
        "nj_morris_clerk_connector.py"
    ),
    "morris_gis_connector": (
        "app/public_records/connectors/"
        "nj_morris_gis_connector.py"
    ),
    "nj_state_modiv_connector": (
        "app/public_records/connectors/"
        "nj_state_modiv_connector.py"
    ),
    "public_records_engine": "app/public_records/public_records_engine.py",
}


# ============================================================
# SECTION 08 - INITIAL CONNECTOR PRIORITY
# ============================================================

INITIAL_PUBLIC_RECORD_CONNECTOR_PRIORITY = [
    {
        "connector_id": "nj_morris_tax_board_connector",
        "file": (
            "app/public_records/connectors/"
            "nj_morris_tax_board_connector.py"
        ),
        "source_id": "nj_morris_tax_board",
        "status": PUBLIC_RECORD_STATUS_NOT_IMPLEMENTED,
        "priority": 1,
        "domains": [
            PUBLIC_RECORD_DOMAIN_TAX_ASSESSMENT,
            PUBLIC_RECORD_DOMAIN_PROPERTY_TAX,
            PUBLIC_RECORD_DOMAIN_PARCEL,
            PUBLIC_RECORD_DOMAIN_SALE_HISTORY,
            PUBLIC_RECORD_DOMAIN_OWNER_REFERENCE,
        ],
    },
    {
        "connector_id": "nj_morris_clerk_connector",
        "file": (
            "app/public_records/connectors/"
            "nj_morris_clerk_connector.py"
        ),
        "source_id": "nj_morris_county_clerk_property_records",
        "status": PUBLIC_RECORD_STATUS_NOT_IMPLEMENTED,
        "priority": 2,
        "domains": [
            PUBLIC_RECORD_DOMAIN_DEED,
            PUBLIC_RECORD_DOMAIN_MORTGAGE,
            PUBLIC_RECORD_DOMAIN_LIEN,
            PUBLIC_RECORD_DOMAIN_SALE_HISTORY,
            PUBLIC_RECORD_DOMAIN_OWNER_REFERENCE,
        ],
    },
    {
        "connector_id": "nj_morris_gis_connector",
        "file": (
            "app/public_records/connectors/"
            "nj_morris_gis_connector.py"
        ),
        "source_id": "nj_morris_gis_parcel_searcher",
        "status": PUBLIC_RECORD_STATUS_NOT_IMPLEMENTED,
        "priority": 3,
        "domains": [
            PUBLIC_RECORD_DOMAIN_GIS,
            PUBLIC_RECORD_DOMAIN_PARCEL,
            PUBLIC_RECORD_DOMAIN_BUILDING_FACTS,
            PUBLIC_RECORD_DOMAIN_MUNICIPAL,
        ],
    },
    {
        "connector_id": "nj_state_modiv_connector",
        "file": (
            "app/public_records/connectors/"
            "nj_state_modiv_connector.py"
        ),
        "source_id": "nj_state_parcels_modiv_composite",
        "status": PUBLIC_RECORD_STATUS_NOT_IMPLEMENTED,
        "priority": 4,
        "domains": [
            PUBLIC_RECORD_DOMAIN_MODIV,
            PUBLIC_RECORD_DOMAIN_STATE,
            PUBLIC_RECORD_DOMAIN_PARCEL,
            PUBLIC_RECORD_DOMAIN_TAX_ASSESSMENT,
        ],
    },
]


# ============================================================
# SECTION 09 - CLAIM SUPPORT MATRIX
# ============================================================

PUBLIC_RECORD_CLAIM_SUPPORT_MATRIX = {
    "supported_by_public_records": [
        "address_identity",
        "parcel_identity",
        "tax_assessment",
        "property_tax",
        "land_value",
        "improvement_value",
        "deed_reference",
        "mortgage_reference",
        "lien_reference",
        "sale_history",
        "owner_reference",
        "building_facts",
        "lot_size",
        "year_built",
        "property_class",
        "municipality",
        "county",
    ],
    "sometimes_supported_by_public_records": [
        "school_district",
        "zoning_context",
        "flood_context",
        "building_permit_context",
        "renovation_context",
    ],
    "not_supported_by_public_records_alone": [
        "active_listing_status",
        "under_contract_status",
        "current_listing_price",
        "current_days_on_market",
        "current_showing_availability",
        "current_offer_deadline",
        "current_broker_confirmation",
    ],
}


# ============================================================
# SECTION 10 - REAL DATA ENFORCEMENT RULES
# ============================================================

PUBLIC_RECORDS_REAL_DATA_RULES = {
    "mock_records_allowed": False,
    "mock_properties_allowed": False,
    "fabricated_addresses_allowed": False,
    "fabricated_assessments_allowed": False,
    "fabricated_deeds_allowed": False,
    "fabricated_sales_allowed": False,
    "fabricated_owners_allowed": False,
    "fabricated_parcels_allowed": False,
    "source_attribution_required": True,
    "source_status_required": True,
    "retrieved_at_required": True,
    "confidence_required": True,
    "manual_review_for_ambiguity": True,
    "manual_review_for_conflicts": True,
    "listing_status_requires_listing_source": True,
}


# ============================================================
# SECTION 11 - PACKAGE PATHS
# ============================================================

PUBLIC_RECORDS_ROOT = Path("app/public_records")

PUBLIC_RECORDS_CONNECTORS_ROOT = Path("app/public_records/connectors")

PUBLIC_RECORDS_MODELS_FILE = PUBLIC_RECORDS_ROOT / "models.py"

PUBLIC_RECORDS_ENGINE_FILE = PUBLIC_RECORDS_ROOT / "public_records_engine.py"


# ============================================================
# SECTION 12 - BUILD ORDER
# ============================================================

PUBLIC_RECORDS_BUILD_ORDER = [
    "app/public_records/__init__.py",
    "app/public_records/models.py",
    "app/public_records/connectors/__init__.py",
    "app/public_records/connectors/base_connector.py",
    "app/public_records/connectors/nj_morris_tax_board_connector.py",
    "app/public_records/connectors/nj_morris_clerk_connector.py",
    "app/public_records/connectors/nj_morris_gis_connector.py",
    "app/public_records/connectors/nj_state_modiv_connector.py",
    "app/public_records/public_records_engine.py",
]


# ============================================================
# SECTION 13 - DIAGNOSTIC FUNCTIONS
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(UTC).isoformat()


def get_public_records_metadata() -> dict[str, Any]:
    """
    Return public records package metadata.
    """

    return {
        "package": PUBLIC_RECORDS_PACKAGE_NAME,
        "version": PUBLIC_RECORDS_PACKAGE_VERSION,
        "phase": PUBLIC_RECORDS_PACKAGE_PHASE,
        "status": PUBLIC_RECORDS_PACKAGE_STATUS,
        "release_channel": PUBLIC_RECORDS_RELEASE_CHANNEL,
        "description": PUBLIC_RECORDS_DESCRIPTION,
        "mission": PUBLIC_RECORDS_MISSION,
        "generated_at": utc_now(),
    }


def get_public_records_principles() -> list[str]:
    """
    Return public records package principles.
    """

    return list(PUBLIC_RECORDS_PRINCIPLES)


def get_public_records_file_registry() -> dict[str, str]:
    """
    Return package file registry.
    """

    return PUBLIC_RECORDS_FILE_REGISTRY.copy()


def get_public_records_build_order() -> list[str]:
    """
    Return public records build order.
    """

    return list(PUBLIC_RECORDS_BUILD_ORDER)


def get_initial_connector_priority() -> list[dict[str, Any]]:
    """
    Return initial connector priority.
    """

    return [
        connector.copy()
        for connector in INITIAL_PUBLIC_RECORD_CONNECTOR_PRIORITY
    ]


def get_public_record_claim_support_matrix() -> dict[str, list[str]]:
    """
    Return public record claim support matrix.
    """

    return {
        key: list(value)
        for key, value in PUBLIC_RECORD_CLAIM_SUPPORT_MATRIX.items()
    }


def get_public_records_real_data_rules() -> dict[str, Any]:
    """
    Return real data rules.
    """

    return PUBLIC_RECORDS_REAL_DATA_RULES.copy()


def are_mock_public_records_allowed() -> bool:
    """
    Return whether mock public records are allowed.
    """

    return bool(PUBLIC_RECORDS_REAL_DATA_RULES["mock_records_allowed"])


def can_public_records_support_claim(
    claim_type: str,
) -> bool:
    """
    Return whether public records can support a claim type.
    """

    normalized = str(claim_type or "").strip().lower()

    supported = PUBLIC_RECORD_CLAIM_SUPPORT_MATRIX[
        "supported_by_public_records"
    ]

    sometimes = PUBLIC_RECORD_CLAIM_SUPPORT_MATRIX[
        "sometimes_supported_by_public_records"
    ]

    return normalized in supported or normalized in sometimes


def requires_listing_source(
    claim_type: str,
) -> bool:
    """
    Return whether claim requires a listing source.
    """

    normalized = str(claim_type or "").strip().lower()

    not_supported = PUBLIC_RECORD_CLAIM_SUPPORT_MATRIX[
        "not_supported_by_public_records_alone"
    ]

    return normalized in not_supported


def get_public_records_health() -> dict[str, Any]:
    """
    Return lightweight public records package health.
    """

    return {
        "package": PUBLIC_RECORDS_PACKAGE_NAME,
        "version": PUBLIC_RECORDS_PACKAGE_VERSION,
        "phase": PUBLIC_RECORDS_PACKAGE_PHASE,
        "status": PUBLIC_RECORDS_PACKAGE_STATUS,
        "connector_count": len(INITIAL_PUBLIC_RECORD_CONNECTOR_PRIORITY),
        "build_order_count": len(PUBLIC_RECORDS_BUILD_ORDER),
        "mock_records_allowed": are_mock_public_records_allowed(),
        "source_attribution_required": PUBLIC_RECORDS_REAL_DATA_RULES[
            "source_attribution_required"
        ],
        "listing_status_requires_listing_source": PUBLIC_RECORDS_REAL_DATA_RULES[
            "listing_status_requires_listing_source"
        ],
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 14 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "PUBLIC_RECORDS_PACKAGE_NAME",
    "PUBLIC_RECORDS_PACKAGE_VERSION",
    "PUBLIC_RECORDS_PACKAGE_PHASE",
    "PUBLIC_RECORDS_PACKAGE_STATUS",
    "PUBLIC_RECORDS_RELEASE_CHANNEL",
    "PUBLIC_RECORDS_DESCRIPTION",
    "PUBLIC_RECORDS_MISSION",
    "PUBLIC_RECORDS_PRINCIPLES",
    "PUBLIC_RECORD_DOMAIN_PARCEL",
    "PUBLIC_RECORD_DOMAIN_TAX_ASSESSMENT",
    "PUBLIC_RECORD_DOMAIN_PROPERTY_TAX",
    "PUBLIC_RECORD_DOMAIN_DEED",
    "PUBLIC_RECORD_DOMAIN_MORTGAGE",
    "PUBLIC_RECORD_DOMAIN_LIEN",
    "PUBLIC_RECORD_DOMAIN_SALE_HISTORY",
    "PUBLIC_RECORD_DOMAIN_OWNER_REFERENCE",
    "PUBLIC_RECORD_DOMAIN_BUILDING_FACTS",
    "PUBLIC_RECORD_DOMAIN_MUNICIPAL",
    "PUBLIC_RECORD_DOMAIN_COUNTY",
    "PUBLIC_RECORD_DOMAIN_STATE",
    "PUBLIC_RECORD_DOMAIN_GIS",
    "PUBLIC_RECORD_DOMAIN_MODIV",
    "PUBLIC_RECORD_DOMAIN_UNKNOWN",
    "PUBLIC_RECORD_STATUS_AVAILABLE",
    "PUBLIC_RECORD_STATUS_PARTIAL",
    "PUBLIC_RECORD_STATUS_UNAVAILABLE",
    "PUBLIC_RECORD_STATUS_NOT_CONNECTED",
    "PUBLIC_RECORD_STATUS_NOT_IMPLEMENTED",
    "PUBLIC_RECORD_STATUS_SOURCE_ERROR",
    "PUBLIC_RECORD_STATUS_MANUAL_REVIEW_REQUIRED",
    "PUBLIC_RECORD_STATUS_AMBIGUOUS",
    "PUBLIC_RECORD_STATUS_EMPTY",
    "PUBLIC_RECORD_STATUS_UNKNOWN",
    "PUBLIC_RECORDS_FILE_REGISTRY",
    "INITIAL_PUBLIC_RECORD_CONNECTOR_PRIORITY",
    "PUBLIC_RECORD_CLAIM_SUPPORT_MATRIX",
    "PUBLIC_RECORDS_REAL_DATA_RULES",
    "PUBLIC_RECORDS_ROOT",
    "PUBLIC_RECORDS_CONNECTORS_ROOT",
    "PUBLIC_RECORDS_MODELS_FILE",
    "PUBLIC_RECORDS_ENGINE_FILE",
    "PUBLIC_RECORDS_BUILD_ORDER",
    "utc_now",
    "get_public_records_metadata",
    "get_public_records_principles",
    "get_public_records_file_registry",
    "get_public_records_build_order",
    "get_initial_connector_priority",
    "get_public_record_claim_support_matrix",
    "get_public_records_real_data_rules",
    "are_mock_public_records_allowed",
    "can_public_records_support_claim",
    "requires_listing_source",
    "get_public_records_health",
]


# ============================================================
# END OF FILE
# ============================================================