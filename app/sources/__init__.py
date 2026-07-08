# ============================================================
# AUSSEM1
# PHASE 2.10 PART 1.00
# ENTERPRISE SOURCE PACKAGE INITIALIZATION
# FILE: app/sources/__init__.py
# PURPOSE:
# Initialize the Aussem1 source intelligence package.
#
# This package is the official source-governance foundation for
# public records, county records, parcel data, tax data, listing
# feeds, market data, valuation inputs, comparable data, and
# future real-estate intelligence connectors.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# REAL DATA SOURCE FOUNDATION ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path


# ============================================================
# SECTION 02 - SOURCE PACKAGE IDENTITY
# ============================================================

SOURCE_PACKAGE_NAME = "Aussem1 Enterprise Source Intelligence"

SOURCE_PACKAGE_VERSION = "0.1.0"

SOURCE_PACKAGE_PHASE = "PHASE 2.10 PART 1.00"

SOURCE_PACKAGE_STATUS = "real_data_source_foundation_active"

SOURCE_PACKAGE_RELEASE_CHANNEL = "development"

SOURCE_PACKAGE_DESCRIPTION = (
    "Enterprise source-governance package for official public "
    "records, property data, parcel data, tax data, listing data, "
    "market data, comparable data, and future real-estate data "
    "connectors."
)


# ============================================================
# SECTION 03 - SOURCE PACKAGE MISSION
# ============================================================

SOURCE_PACKAGE_MISSION = (
    "Ensure every property fact, valuation input, public-record "
    "claim, listing-status claim, comparable property, and market "
    "insight in Aussem1 is traceable to a source, labeled by source "
    "status, and never fabricated."
)


SOURCE_PACKAGE_PRINCIPLES = [
    "No mock homes.",
    "No fake property facts.",
    "No invented valuation data.",
    "No unsupported listing-status claims.",
    "No active/sold/under-contract claims without source support.",
    "Every sourced fact must carry attribution.",
    "Every unavailable source must be labeled unavailable.",
    "Every connector must return source status.",
    "Every record must expose confidence and retrieval metadata.",
    "Public records are not the same as MLS listing data.",
    "Public records can support tax, parcel, deed, sale-history, and assessment context.",
    "Listing feeds are required for reliable active or under-contract status.",
]


# ============================================================
# SECTION 04 - SOURCE STATUS CONSTANTS
# ============================================================

SOURCE_STATUS_ACTIVE = "active"

SOURCE_STATUS_PLANNED = "planned"

SOURCE_STATUS_DISABLED = "disabled"

SOURCE_STATUS_UNAVAILABLE = "unavailable"

SOURCE_STATUS_ERROR = "error"

SOURCE_STATUS_RATE_LIMITED = "rate_limited"

SOURCE_STATUS_AUTH_REQUIRED = "auth_required"

SOURCE_STATUS_NOT_IMPLEMENTED = "not_implemented"

SOURCE_STATUS_MANUAL_REVIEW_REQUIRED = "manual_review_required"


# ============================================================
# SECTION 05 - SOURCE TYPE CONSTANTS
# ============================================================

SOURCE_TYPE_PUBLIC_RECORD = "public_record"

SOURCE_TYPE_COUNTY_ASSESSOR = "county_assessor"

SOURCE_TYPE_COUNTY_CLERK = "county_clerk"

SOURCE_TYPE_COUNTY_RECORDER = "county_recorder"

SOURCE_TYPE_TAX_BOARD = "tax_board"

SOURCE_TYPE_PARCEL_GIS = "parcel_gis"

SOURCE_TYPE_STATE_PARCEL_DATA = "state_parcel_data"

SOURCE_TYPE_STATE_ASSESSMENT_DATA = "state_assessment_data"

SOURCE_TYPE_MLS_RESO = "mls_reso"

SOURCE_TYPE_IDX = "idx"

SOURCE_TYPE_BROKER_FEED = "broker_feed"

SOURCE_TYPE_LISTING_PROVIDER = "listing_provider"

SOURCE_TYPE_MARKET_DATA = "market_data"

SOURCE_TYPE_SCHOOL_DATA = "school_data"

SOURCE_TYPE_RISK_DATA = "risk_data"

SOURCE_TYPE_USER_PROVIDED = "user_provided"

SOURCE_TYPE_INTERNAL_MEMORY = "internal_memory"

SOURCE_TYPE_UNKNOWN = "unknown"


# ============================================================
# SECTION 06 - SOURCE RELIABILITY TIERS
# ============================================================

SOURCE_RELIABILITY_TIERS = {
    "tier_1_official": {
        "label": "Official Source",
        "description": (
            "Government, county, municipal, state, MLS/RESO, or "
            "authorized provider source with direct source attribution."
        ),
        "expected_confidence": "high",
    },
    "tier_2_authorized": {
        "label": "Authorized Data Provider",
        "description": (
            "Permitted data provider, broker feed, official API, or "
            "licensed data channel."
        ),
        "expected_confidence": "medium_to_high",
    },
    "tier_3_user_provided": {
        "label": "User Provided",
        "description": (
            "User-entered facts, property notes, renovation details, "
            "condition notes, or manual context requiring review."
        ),
        "expected_confidence": "low_to_medium",
    },
    "tier_4_internal_inference": {
        "label": "Internal Inference",
        "description": (
            "Aussem1-generated reasoning based on available context. "
            "Must never be treated as verified source truth."
        ),
        "expected_confidence": "variable",
    },
    "tier_5_unverified": {
        "label": "Unverified",
        "description": (
            "Unverified, unavailable, unclear, stale, or unsupported data."
        ),
        "expected_confidence": "low",
    },
}


# ============================================================
# SECTION 07 - INITIAL REAL-DATA GEOGRAPHIC PRIORITY
# ============================================================

INITIAL_GEOGRAPHIC_PRIORITY = {
    "primary_state": "New Jersey",
    "primary_county": "Morris County",
    "primary_focus": [
        "tax board records",
        "county clerk records",
        "parcel GIS records",
        "state parcel and MOD-IV data",
        "sale-history references",
        "assessment records",
        "deed references",
    ],
    "expansion_states": [
        "New Jersey statewide",
        "New York",
        "Pennsylvania",
        "Connecticut",
        "Florida",
        "Texas",
        "California",
    ],
}


# ============================================================
# SECTION 08 - INITIAL OFFICIAL SOURCE SEED REGISTRY
# ============================================================

INITIAL_SOURCE_SEED_REGISTRY = {
    "nj_morris_tax_board": {
        "display_name": "Morris County Tax Board",
        "source_type": SOURCE_TYPE_TAX_BOARD,
        "status": SOURCE_STATUS_PLANNED,
        "implementation_file": (
            "app/public_records/connectors/"
            "nj_morris_tax_board_connector.py"
        ),
        "expected_records": [
            "property_location_search",
            "owner_search_where_available",
            "block_lot_search",
            "assessment_data",
            "tax_record_context",
            "sale_record_context_where_available",
        ],
        "official_source_required": True,
        "mock_data_allowed": False,
    },
    "nj_morris_county_clerk": {
        "display_name": "Morris County Clerk Property Records",
        "source_type": SOURCE_TYPE_COUNTY_CLERK,
        "status": SOURCE_STATUS_PLANNED,
        "implementation_file": (
            "app/public_records/connectors/"
            "nj_morris_clerk_connector.py"
        ),
        "expected_records": [
            "deed_references",
            "mortgage_references",
            "recorded_documents",
            "lien_references_where_available",
            "sale_transfer_document_context",
        ],
        "official_source_required": True,
        "mock_data_allowed": False,
    },
    "nj_morris_gis": {
        "display_name": "Morris County GIS Parcel Data",
        "source_type": SOURCE_TYPE_PARCEL_GIS,
        "status": SOURCE_STATUS_PLANNED,
        "implementation_file": (
            "app/public_records/connectors/"
            "nj_morris_gis_connector.py"
        ),
        "expected_records": [
            "parcel_boundaries",
            "block_lot_context",
            "municipality_context",
            "parcel_attribute_context",
            "map_reference_context",
        ],
        "official_source_required": True,
        "mock_data_allowed": False,
    },
    "nj_state_modiv": {
        "display_name": "New Jersey Parcel and MOD-IV Data",
        "source_type": SOURCE_TYPE_STATE_ASSESSMENT_DATA,
        "status": SOURCE_STATUS_PLANNED,
        "implementation_file": (
            "app/public_records/connectors/"
            "nj_state_modiv_connector.py"
        ),
        "expected_records": [
            "statewide_parcel_baseline",
            "assessment_attributes",
            "municipality_code",
            "block_lot_identifiers",
            "property_tax_context",
        ],
        "official_source_required": True,
        "mock_data_allowed": False,
    },
    "mls_reso_future": {
        "display_name": "MLS / RESO Listing Feed",
        "source_type": SOURCE_TYPE_MLS_RESO,
        "status": SOURCE_STATUS_AUTH_REQUIRED,
        "implementation_file": None,
        "expected_records": [
            "active_listing_status",
            "pending_status",
            "under_contract_status",
            "closed_sale_status",
            "listing_price",
            "days_on_market",
            "listing_photos",
            "agent_broker_metadata",
        ],
        "official_source_required": True,
        "mock_data_allowed": False,
    },
}


# ============================================================
# SECTION 09 - SOURCE CLAIM GOVERNANCE
# ============================================================

SOURCE_CLAIM_GOVERNANCE = {
    "can_claim_tax_assessment": [
        SOURCE_TYPE_TAX_BOARD,
        SOURCE_TYPE_COUNTY_ASSESSOR,
        SOURCE_TYPE_STATE_ASSESSMENT_DATA,
    ],
    "can_claim_parcel_context": [
        SOURCE_TYPE_PARCEL_GIS,
        SOURCE_TYPE_STATE_PARCEL_DATA,
    ],
    "can_claim_deed_context": [
        SOURCE_TYPE_COUNTY_CLERK,
        SOURCE_TYPE_COUNTY_RECORDER,
    ],
    "can_claim_sale_history": [
        SOURCE_TYPE_COUNTY_CLERK,
        SOURCE_TYPE_COUNTY_RECORDER,
        SOURCE_TYPE_TAX_BOARD,
        SOURCE_TYPE_MLS_RESO,
        SOURCE_TYPE_LISTING_PROVIDER,
    ],
    "can_claim_active_listing_status": [
        SOURCE_TYPE_MLS_RESO,
        SOURCE_TYPE_IDX,
        SOURCE_TYPE_BROKER_FEED,
        SOURCE_TYPE_LISTING_PROVIDER,
    ],
    "can_claim_under_contract_status": [
        SOURCE_TYPE_MLS_RESO,
        SOURCE_TYPE_IDX,
        SOURCE_TYPE_BROKER_FEED,
        SOURCE_TYPE_LISTING_PROVIDER,
    ],
    "cannot_claim_from_public_records_alone": [
        "currently_active_listing",
        "currently_under_contract",
        "current_showing_availability",
        "current_offer_deadline",
        "current_listing_agent_confirmation",
    ],
}


# ============================================================
# SECTION 10 - DATA INTEGRITY RULES
# ============================================================

DATA_INTEGRITY_RULES = {
    "mock_property_data_allowed": False,
    "fabricated_addresses_allowed": False,
    "fabricated_values_allowed": False,
    "fabricated_comparables_allowed": False,
    "fabricated_public_records_allowed": False,
    "source_attribution_required": True,
    "retrieved_at_required": True,
    "source_status_required": True,
    "confidence_required": True,
    "error_reporting_required": True,
    "manual_review_for_conflicts_required": True,
}


# ============================================================
# SECTION 11 - CONNECTOR GOVERNANCE
# ============================================================

CONNECTOR_GOVERNANCE = {
    "respect_robots_and_terms": True,
    "bypass_access_controls_allowed": False,
    "credential_stuffing_allowed": False,
    "rate_limit_handling_required": True,
    "timeouts_required": True,
    "user_agent_required": True,
    "uncontrolled_scraping_allowed": False,
    "official_api_preferred": True,
    "manual_review_for_ambiguous_records": True,
    "store_raw_sensitive_data_by_default": False,
}


# ============================================================
# SECTION 12 - SOURCE PACKAGE BUILD ORDER
# ============================================================

SOURCE_PACKAGE_BUILD_ORDER = [
    "app/sources/__init__.py",
    "app/sources/source_models.py",
    "app/sources/source_registry.py",
    "app/sources/source_client.py",
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
# SECTION 13 - PACKAGE PATHS
# ============================================================

SOURCE_PACKAGE_ROOT = Path("app/sources")

PUBLIC_RECORDS_PACKAGE_ROOT = Path("app/public_records")

PUBLIC_RECORDS_CONNECTORS_ROOT = Path("app/public_records/connectors")


SOURCE_PACKAGE_PATHS = {
    "sources_root": str(SOURCE_PACKAGE_ROOT),
    "public_records_root": str(PUBLIC_RECORDS_PACKAGE_ROOT),
    "public_records_connectors": str(PUBLIC_RECORDS_CONNECTORS_ROOT),
    "source_models": "app/sources/source_models.py",
    "source_registry": "app/sources/source_registry.py",
    "source_client": "app/sources/source_client.py",
}


# ============================================================
# SECTION 14 - PACKAGE DIAGNOSTICS
# ============================================================

def get_source_package_metadata() -> dict:
    """
    Return source package metadata.
    """

    return {
        "package": SOURCE_PACKAGE_NAME,
        "version": SOURCE_PACKAGE_VERSION,
        "phase": SOURCE_PACKAGE_PHASE,
        "status": SOURCE_PACKAGE_STATUS,
        "release_channel": SOURCE_PACKAGE_RELEASE_CHANNEL,
        "description": SOURCE_PACKAGE_DESCRIPTION,
        "mission": SOURCE_PACKAGE_MISSION,
    }


def get_source_package_principles() -> list[str]:
    """
    Return source package principles.
    """

    return list(SOURCE_PACKAGE_PRINCIPLES)


def get_initial_source_seed_registry() -> dict:
    """
    Return initial source seed registry.
    """

    return INITIAL_SOURCE_SEED_REGISTRY.copy()


def get_source_claim_governance() -> dict:
    """
    Return source claim governance rules.
    """

    return SOURCE_CLAIM_GOVERNANCE.copy()


def get_data_integrity_rules() -> dict:
    """
    Return data integrity rules.
    """

    return DATA_INTEGRITY_RULES.copy()


def get_connector_governance() -> dict:
    """
    Return connector governance rules.
    """

    return CONNECTOR_GOVERNANCE.copy()


def get_source_package_build_order() -> list[str]:
    """
    Return source package build order.
    """

    return list(SOURCE_PACKAGE_BUILD_ORDER)


def get_source_package_paths() -> dict:
    """
    Return source package path registry.
    """

    return SOURCE_PACKAGE_PATHS.copy()


def is_mock_data_allowed() -> bool:
    """
    Return whether mock property data is allowed.
    """

    return bool(DATA_INTEGRITY_RULES["mock_property_data_allowed"])


def can_source_type_claim(
    source_type: str,
    claim_type: str,
) -> bool:
    """
    Return whether a source type can support a claim type.
    """

    allowed_source_types = SOURCE_CLAIM_GOVERNANCE.get(
        claim_type,
        [],
    )

    return source_type in allowed_source_types


def get_source_package_health() -> dict:
    """
    Return lightweight source package health.
    """

    return {
        "package": SOURCE_PACKAGE_NAME,
        "version": SOURCE_PACKAGE_VERSION,
        "phase": SOURCE_PACKAGE_PHASE,
        "status": SOURCE_PACKAGE_STATUS,
        "seed_sources": len(INITIAL_SOURCE_SEED_REGISTRY),
        "source_principles": len(SOURCE_PACKAGE_PRINCIPLES),
        "mock_data_allowed": is_mock_data_allowed(),
        "source_attribution_required": DATA_INTEGRITY_RULES[
            "source_attribution_required"
        ],
        "connector_governance_loaded": bool(CONNECTOR_GOVERNANCE),
        "build_order_loaded": bool(SOURCE_PACKAGE_BUILD_ORDER),
        "generated_at": datetime.now(UTC).isoformat(),
    }


# ============================================================
# SECTION 15 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "SOURCE_PACKAGE_NAME",
    "SOURCE_PACKAGE_VERSION",
    "SOURCE_PACKAGE_PHASE",
    "SOURCE_PACKAGE_STATUS",
    "SOURCE_PACKAGE_RELEASE_CHANNEL",
    "SOURCE_PACKAGE_DESCRIPTION",
    "SOURCE_PACKAGE_MISSION",
    "SOURCE_PACKAGE_PRINCIPLES",
    "SOURCE_STATUS_ACTIVE",
    "SOURCE_STATUS_PLANNED",
    "SOURCE_STATUS_DISABLED",
    "SOURCE_STATUS_UNAVAILABLE",
    "SOURCE_STATUS_ERROR",
    "SOURCE_STATUS_RATE_LIMITED",
    "SOURCE_STATUS_AUTH_REQUIRED",
    "SOURCE_STATUS_NOT_IMPLEMENTED",
    "SOURCE_STATUS_MANUAL_REVIEW_REQUIRED",
    "SOURCE_TYPE_PUBLIC_RECORD",
    "SOURCE_TYPE_COUNTY_ASSESSOR",
    "SOURCE_TYPE_COUNTY_CLERK",
    "SOURCE_TYPE_COUNTY_RECORDER",
    "SOURCE_TYPE_TAX_BOARD",
    "SOURCE_TYPE_PARCEL_GIS",
    "SOURCE_TYPE_STATE_PARCEL_DATA",
    "SOURCE_TYPE_STATE_ASSESSMENT_DATA",
    "SOURCE_TYPE_MLS_RESO",
    "SOURCE_TYPE_IDX",
    "SOURCE_TYPE_BROKER_FEED",
    "SOURCE_TYPE_LISTING_PROVIDER",
    "SOURCE_TYPE_MARKET_DATA",
    "SOURCE_TYPE_SCHOOL_DATA",
    "SOURCE_TYPE_RISK_DATA",
    "SOURCE_TYPE_USER_PROVIDED",
    "SOURCE_TYPE_INTERNAL_MEMORY",
    "SOURCE_TYPE_UNKNOWN",
    "SOURCE_RELIABILITY_TIERS",
    "INITIAL_GEOGRAPHIC_PRIORITY",
    "INITIAL_SOURCE_SEED_REGISTRY",
    "SOURCE_CLAIM_GOVERNANCE",
    "DATA_INTEGRITY_RULES",
    "CONNECTOR_GOVERNANCE",
    "SOURCE_PACKAGE_BUILD_ORDER",
    "SOURCE_PACKAGE_PATHS",
    "get_source_package_metadata",
    "get_source_package_principles",
    "get_initial_source_seed_registry",
    "get_source_claim_governance",
    "get_data_integrity_rules",
    "get_connector_governance",
    "get_source_package_build_order",
    "get_source_package_paths",
    "is_mock_data_allowed",
    "can_source_type_claim",
    "get_source_package_health",
]


# ============================================================
# END OF FILE
# ============================================================