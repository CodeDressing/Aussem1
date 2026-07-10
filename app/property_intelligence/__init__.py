# ============================================================
# AUSSEM1
# PHASE 2.30 PART 5.00
# ENTERPRISE PROPERTY INTELLIGENCE PACKAGE INITIALIZATION
# FILE: app/property_intelligence/__init__.py
# PURPOSE:
# Initialize the Aussem1 Property Intelligence package.
#
# This package will become the real-estate intelligence layer that
# sits above public records, future MLS / RESO feeds, valuation
# engines, confidence engines, address intelligence, source
# explanations, and property profile generation.
#
# This file provides:
# - package identity
# - package governance
# - build-order tracking
# - public-record integration declarations
# - property intelligence capability declarations
# - unsupported-claim protection
# - source-trust rules
# - diagnostics
# - safe lazy import helpers
#
# This file does not create mock homes.
# This file does not fabricate property values.
# This file does not fabricate listing status.
# This file does not fabricate sale history.
# This file does not fabricate owner conclusions.
# This file does not claim MLS active status without a listing feed.
# This file does not claim under-contract status without a listing feed.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# PROPERTY INTELLIGENCE PACKAGE FOUNDATION ACTIVE
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
# SECTION 02 - PACKAGE IDENTITY
# ============================================================

PROPERTY_INTELLIGENCE_PACKAGE_NAME = (
    "Aussem1 Enterprise Property Intelligence"
)

PROPERTY_INTELLIGENCE_PACKAGE_VERSION = "0.1.0"

PROPERTY_INTELLIGENCE_PACKAGE_PHASE = "PHASE 2.30 PART 5.00"

PROPERTY_INTELLIGENCE_PACKAGE_STATUS = (
    "property_intelligence_foundation_active"
)

PROPERTY_INTELLIGENCE_RELEASE_CHANNEL = "development"

PROPERTY_INTELLIGENCE_DESCRIPTION = (
    "Enterprise property intelligence package for source-backed "
    "residential real estate profiles, public-record synthesis, "
    "future valuation support, future listing-feed support, confidence "
    "scoring, source explanations, and property-profile generation."
)


# ============================================================
# SECTION 03 - PACKAGE MISSION
# ============================================================

PROPERTY_INTELLIGENCE_MISSION = (
    "Transform real, source-backed property data into reliable, "
    "explainable, confidence-scored property intelligence without "
    "fabricating property facts, listing status, valuation, ownership, "
    "or transaction claims."
)


# ============================================================
# SECTION 04 - PACKAGE PRINCIPLES
# ============================================================

PROPERTY_INTELLIGENCE_PRINCIPLES = [
    "Use real source-backed property data only.",
    "Do not create mock properties.",
    "Do not fabricate estimated values.",
    "Do not fabricate active listing status.",
    "Do not fabricate under-contract status.",
    "Do not fabricate ownership conclusions.",
    "Do not fabricate sale-history records.",
    "Do not fabricate tax assessments.",
    "Do not claim current listing price from public records.",
    "Do not claim current market value from assessment alone.",
    "Do not treat public records as legal advice.",
    "Do not treat GIS geometry as a legal boundary survey.",
    "Always separate public-record facts from listing-feed facts.",
    "Always preserve source attribution.",
    "Always expose unavailable/partial/manual-review status.",
    "Always attach confidence and source explanation to profile output.",
    "Mark ambiguous or conflicting source results for manual review.",
    "MLS/listing status requires a future authorized MLS, IDX, RESO, broker, or listing-provider feed.",
]


# ============================================================
# SECTION 05 - PACKAGE PATHS
# ============================================================

PROPERTY_INTELLIGENCE_ROOT = Path("app/property_intelligence")

PROPERTY_INTELLIGENCE_INIT_FILE = (
    PROPERTY_INTELLIGENCE_ROOT / "__init__.py"
)

PROPERTY_INTELLIGENCE_MODELS_FILE = (
    PROPERTY_INTELLIGENCE_ROOT / "models.py"
)

ADDRESS_INTELLIGENCE_FILE = (
    PROPERTY_INTELLIGENCE_ROOT / "address_intelligence.py"
)

CONFIDENCE_ENGINE_FILE = (
    PROPERTY_INTELLIGENCE_ROOT / "confidence_engine.py"
)

SOURCE_EXPLANATION_ENGINE_FILE = (
    PROPERTY_INTELLIGENCE_ROOT / "source_explanation_engine.py"
)

PROPERTY_PROFILE_ENGINE_FILE = (
    PROPERTY_INTELLIGENCE_ROOT / "property_profile_engine.py"
)


# ============================================================
# SECTION 06 - PACKAGE BUILD ORDER
# ============================================================

PROPERTY_INTELLIGENCE_BUILD_ORDER = [
    "app/property_intelligence/__init__.py",
    "app/property_intelligence/models.py",
    "app/property_intelligence/address_intelligence.py",
    "app/property_intelligence/confidence_engine.py",
    "app/property_intelligence/source_explanation_engine.py",
    "app/property_intelligence/property_profile_engine.py",
]


# ============================================================
# SECTION 07 - BATCH 3 COMPLETION TRACKER
# ============================================================

BATCH_3_PUBLIC_RECORDS_CONNECTORS_AND_ENGINE = {
    "batch_name": "BATCH 3 - Public Records Connectors + Engine",
    "commit_after_file_count": 5,
    "files": [
        {
            "order": 1,
            "file": "app/public_records/connectors/nj_morris_clerk_connector.py",
            "status": "done",
        },
        {
            "order": 2,
            "file": "app/public_records/connectors/nj_morris_gis_connector.py",
            "status": "done",
        },
        {
            "order": 3,
            "file": "app/public_records/connectors/nj_state_modiv_connector.py",
            "status": "done",
        },
        {
            "order": 4,
            "file": "app/public_records/public_records_engine.py",
            "status": "done",
        },
        {
            "order": 5,
            "file": "app/property_intelligence/__init__.py",
            "status": "done",
        },
    ],
    "commit_message": (
        "PHASE 2.30 PART 5.00 - Complete Public Records Connectors and Engine Batch"
    ),
}


# ============================================================
# SECTION 08 - NEXT BATCH TRACKER
# ============================================================

BATCH_4_PROPERTY_INTELLIGENCE_CORE = {
    "batch_name": "BATCH 4 - Property Intelligence Core",
    "commit_after_file_count": 5,
    "files": [
        {
            "order": 1,
            "file": "app/property_intelligence/models.py",
            "status": "next",
        },
        {
            "order": 2,
            "file": "app/property_intelligence/address_intelligence.py",
            "status": "pending",
        },
        {
            "order": 3,
            "file": "app/property_intelligence/confidence_engine.py",
            "status": "pending",
        },
        {
            "order": 4,
            "file": "app/property_intelligence/source_explanation_engine.py",
            "status": "pending",
        },
        {
            "order": 5,
            "file": "app/property_intelligence/property_profile_engine.py",
            "status": "pending",
        },
    ],
    "commit_message": (
        "PHASE 2.40 PART 5.00 - Complete Property Intelligence Core Batch"
    ),
}


# ============================================================
# SECTION 09 - DATA DOMAIN CONSTANTS
# ============================================================

PROPERTY_DOMAIN_ADDRESS = "address"

PROPERTY_DOMAIN_PARCEL = "parcel"

PROPERTY_DOMAIN_PUBLIC_RECORDS = "public_records"

PROPERTY_DOMAIN_TAX_ASSESSMENT = "tax_assessment"

PROPERTY_DOMAIN_PROPERTY_TAX = "property_tax"

PROPERTY_DOMAIN_DEED = "deed"

PROPERTY_DOMAIN_MORTGAGE = "mortgage"

PROPERTY_DOMAIN_LIEN = "lien"

PROPERTY_DOMAIN_SALE_HISTORY = "sale_history"

PROPERTY_DOMAIN_OWNER_REFERENCE = "owner_reference"

PROPERTY_DOMAIN_BUILDING_FACTS = "building_facts"

PROPERTY_DOMAIN_GIS_CONTEXT = "gis_context"

PROPERTY_DOMAIN_MODIV_CONTEXT = "modiv_context"

PROPERTY_DOMAIN_LISTING_STATUS = "listing_status"

PROPERTY_DOMAIN_MARKET_VALUE = "market_value"

PROPERTY_DOMAIN_VALUATION = "valuation"

PROPERTY_DOMAIN_COMPARABLE_SALES = "comparable_sales"

PROPERTY_DOMAIN_RISK_CONTEXT = "risk_context"

PROPERTY_DOMAIN_SCHOOL_CONTEXT = "school_context"

PROPERTY_DOMAIN_TRANSIT_CONTEXT = "transit_context"

PROPERTY_DOMAIN_UNKNOWN = "unknown"


# ============================================================
# SECTION 10 - INTELLIGENCE STATUS CONSTANTS
# ============================================================

PROPERTY_INTELLIGENCE_STATUS_READY = "ready"

PROPERTY_INTELLIGENCE_STATUS_AVAILABLE = "available"

PROPERTY_INTELLIGENCE_STATUS_PARTIAL = "partial"

PROPERTY_INTELLIGENCE_STATUS_UNAVAILABLE = "unavailable"

PROPERTY_INTELLIGENCE_STATUS_EMPTY = "empty"

PROPERTY_INTELLIGENCE_STATUS_ERROR = "error"

PROPERTY_INTELLIGENCE_STATUS_NOT_CONNECTED = "not_connected"

PROPERTY_INTELLIGENCE_STATUS_NOT_IMPLEMENTED = "not_implemented"

PROPERTY_INTELLIGENCE_STATUS_MANUAL_REVIEW_REQUIRED = (
    "manual_review_required"
)

PROPERTY_INTELLIGENCE_STATUS_AMBIGUOUS = "ambiguous"

PROPERTY_INTELLIGENCE_STATUS_CONFLICTING = "conflicting"

PROPERTY_INTELLIGENCE_STATUS_UNKNOWN = "unknown"


# ============================================================
# SECTION 11 - SOURCE LAYER CONSTANTS
# ============================================================

SOURCE_LAYER_PUBLIC_RECORDS = "public_records"

SOURCE_LAYER_PUBLIC_RECORDS_ENGINE = "public_records_engine"

SOURCE_LAYER_LISTING_FEED = "listing_feed"

SOURCE_LAYER_MLS_RESO = "mls_reso"

SOURCE_LAYER_BROKER_FEED = "broker_feed"

SOURCE_LAYER_VALUATION_ENGINE = "valuation_engine"

SOURCE_LAYER_AI_SUMMARY = "ai_summary"

SOURCE_LAYER_USER_PROVIDED_CONTEXT = "user_provided_context"

SOURCE_LAYER_INTERNAL_INFERENCE = "internal_inference"

SOURCE_LAYER_UNKNOWN = "unknown"


# ============================================================
# SECTION 12 - PUBLIC RECORD SOURCE CAPABILITIES
# ============================================================

PUBLIC_RECORD_SOURCE_CAPABILITIES = {
    "can_support": [
        "address_identity",
        "parcel_identity",
        "tax_assessment",
        "property_tax_context",
        "land_value",
        "improvement_value",
        "total_assessed_value",
        "deed_reference",
        "mortgage_reference",
        "lien_reference",
        "sale_history_reference",
        "owner_reference",
        "building_facts_where_source_supported",
        "lot_size_where_source_supported",
        "year_built_where_source_supported",
        "municipality",
        "county",
        "state",
        "gis_context",
        "modiv_context",
    ],
    "cannot_support_alone": [
        "active_listing_status",
        "under_contract_status",
        "pending_status",
        "current_listing_price",
        "current_days_on_market",
        "current_showing_availability",
        "current_offer_deadline",
        "current_broker_confirmation",
        "current_mls_status",
        "current_market_value",
        "legal_boundary_survey",
        "title_clearance",
        "legal_ownership_opinion",
    ],
    "requires_manual_review_when": [
        "address match is ambiguous",
        "multiple parcel candidates exist",
        "public record sources conflict",
        "owner reference is stale or unclear",
        "deed and tax sources disagree",
        "GIS and tax records disagree",
        "source response is partial",
        "connector returned candidate records only",
    ],
}


# ============================================================
# SECTION 13 - FUTURE LISTING SOURCE CAPABILITIES
# ============================================================

FUTURE_LISTING_SOURCE_CAPABILITIES = {
    "future_source_types": [
        "MLS RESO Web API",
        "IDX feed",
        "broker-authorized listing feed",
        "listing-provider API",
        "internal brokerage listing source",
    ],
    "will_support_when_connected": [
        "active_listing_status",
        "under_contract_status",
        "pending_status",
        "current_listing_price",
        "current_days_on_market",
        "current_showing_availability",
        "current_offer_deadline",
        "current_broker_confirmation",
        "current_mls_status",
    ],
    "current_status": "not_connected",
    "current_rule": (
        "Listing status claims are unavailable until an authorized listing "
        "source is connected."
    ),
}


# ============================================================
# SECTION 14 - UNSUPPORTED CLAIMS WITHOUT LISTING FEED
# ============================================================

PROPERTY_INTELLIGENCE_UNSUPPORTED_WITHOUT_LISTING_FEED = [
    "active_listing_status",
    "under_contract_status",
    "pending_status",
    "current_listing_price",
    "current_days_on_market",
    "current_showing_availability",
    "current_offer_deadline",
    "current_broker_confirmation",
    "current_mls_status",
    "current_broker_remarks",
    "current_mls_agent_remarks",
]


# ============================================================
# SECTION 15 - UNSUPPORTED CLAIMS WITHOUT VALUATION ENGINE
# ============================================================

PROPERTY_INTELLIGENCE_UNSUPPORTED_WITHOUT_VALUATION_ENGINE = [
    "current_market_value",
    "automated_valuation_model_value",
    "avm_value",
    "confidence_backed_market_value",
    "current_equity_estimate",
    "investment_return_projection",
]


# ============================================================
# SECTION 16 - SOURCE TRUST POLICY
# ============================================================

PROPERTY_INTELLIGENCE_SOURCE_TRUST_POLICY = {
    "public_records": {
        "trust_level": "official_context",
        "confidence_floor": 0.25,
        "confidence_ceiling": 0.85,
        "requires_attribution": True,
        "requires_status": True,
        "requires_confidence": True,
        "can_establish_listing_status": False,
        "can_establish_market_value": False,
        "manual_review_on_conflict": True,
    },
    "listing_feed": {
        "trust_level": "listing_authority_when_authorized",
        "confidence_floor": 0.40,
        "confidence_ceiling": 0.95,
        "requires_attribution": True,
        "requires_status": True,
        "requires_confidence": True,
        "can_establish_listing_status": True,
        "can_establish_market_value": False,
        "manual_review_on_conflict": True,
        "current_status": "not_connected",
    },
    "valuation_engine": {
        "trust_level": "statistical_estimate_when_connected",
        "confidence_floor": 0.20,
        "confidence_ceiling": 0.90,
        "requires_model_version": True,
        "requires_source_inputs": True,
        "requires_confidence": True,
        "can_establish_listing_status": False,
        "can_establish_market_value": True,
        "current_status": "not_connected",
    },
    "ai_summary": {
        "trust_level": "derived_explanation",
        "confidence_floor": 0.0,
        "confidence_ceiling": 0.75,
        "requires_source_inputs": True,
        "must_not_create_new_facts": True,
        "must_explain_limitations": True,
        "manual_review_on_low_confidence": True,
    },
}


# ============================================================
# SECTION 17 - GOVERNANCE RULES
# ============================================================

PROPERTY_INTELLIGENCE_GOVERNANCE = {
    "mock_properties_allowed": False,
    "mock_public_record_results_allowed": False,
    "fabricated_property_facts_allowed": False,
    "fabricated_property_values_allowed": False,
    "fabricated_market_values_allowed": False,
    "fabricated_listing_status_allowed": False,
    "fabricated_owner_conclusions_allowed": False,
    "fabricated_sale_history_allowed": False,
    "active_listing_status_requires_listing_feed": True,
    "under_contract_status_requires_listing_feed": True,
    "current_listing_price_requires_listing_feed": True,
    "market_value_requires_valuation_engine": True,
    "assessment_value_is_not_market_value": True,
    "public_records_are_not_legal_advice": True,
    "gis_geometry_is_not_legal_survey": True,
    "source_attribution_required": True,
    "confidence_required": True,
    "source_explanation_required": True,
    "manual_review_for_ambiguity": True,
    "manual_review_for_conflicts": True,
    "unavailable_data_must_be_labeled_unavailable": True,
}


# ============================================================
# SECTION 18 - MODULE REGISTRY
# ============================================================

PROPERTY_INTELLIGENCE_MODULE_REGISTRY = {
    "models": {
        "module": "app.property_intelligence.models",
        "file": str(PROPERTY_INTELLIGENCE_MODELS_FILE),
        "status": "planned",
        "required": True,
        "phase": "PHASE 2.40 PART 1.00",
        "purpose": "Property intelligence dataclasses, enums, and response models.",
    },
    "address_intelligence": {
        "module": "app.property_intelligence.address_intelligence",
        "file": str(ADDRESS_INTELLIGENCE_FILE),
        "status": "planned",
        "required": True,
        "phase": "PHASE 2.40 PART 2.00",
        "purpose": "Address normalization, address confidence, and geographic routing.",
    },
    "confidence_engine": {
        "module": "app.property_intelligence.confidence_engine",
        "file": str(CONFIDENCE_ENGINE_FILE),
        "status": "planned",
        "required": True,
        "phase": "PHASE 2.40 PART 3.00",
        "purpose": "Property-profile confidence scoring across sources.",
    },
    "source_explanation_engine": {
        "module": "app.property_intelligence.source_explanation_engine",
        "file": str(SOURCE_EXPLANATION_ENGINE_FILE),
        "status": "planned",
        "required": True,
        "phase": "PHASE 2.40 PART 4.00",
        "purpose": "Human-readable source explanation, source limitations, and review notes.",
    },
    "property_profile_engine": {
        "module": "app.property_intelligence.property_profile_engine",
        "file": str(PROPERTY_PROFILE_ENGINE_FILE),
        "status": "planned",
        "required": True,
        "phase": "PHASE 2.40 PART 5.00",
        "purpose": "High-level property profile orchestration and public API payload generation.",
    },
}


# ============================================================
# SECTION 19 - UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(UTC).isoformat()


def safe_string(value: Any) -> str:
    """
    Convert any value into a stripped string.
    """

    if value is None:
        return ""

    return str(value).strip()


def normalize_property_intelligence_key(value: Any) -> str:
    """
    Normalize property intelligence key.
    """

    text = safe_string(value).lower()

    return "_".join(text.replace("-", " ").split())


def get_property_intelligence_metadata() -> dict[str, Any]:
    """
    Return package metadata.
    """

    return {
        "package": PROPERTY_INTELLIGENCE_PACKAGE_NAME,
        "version": PROPERTY_INTELLIGENCE_PACKAGE_VERSION,
        "phase": PROPERTY_INTELLIGENCE_PACKAGE_PHASE,
        "status": PROPERTY_INTELLIGENCE_PACKAGE_STATUS,
        "release_channel": PROPERTY_INTELLIGENCE_RELEASE_CHANNEL,
        "description": PROPERTY_INTELLIGENCE_DESCRIPTION,
        "mission": PROPERTY_INTELLIGENCE_MISSION,
        "generated_at": utc_now(),
    }


def get_property_intelligence_principles() -> list[str]:
    """
    Return property intelligence principles.
    """

    return list(PROPERTY_INTELLIGENCE_PRINCIPLES)


def get_property_intelligence_build_order() -> list[str]:
    """
    Return property intelligence build order.
    """

    return list(PROPERTY_INTELLIGENCE_BUILD_ORDER)


def get_batch_3_tracker() -> dict[str, Any]:
    """
    Return Batch 3 tracker.
    """

    return {
        "batch_name": BATCH_3_PUBLIC_RECORDS_CONNECTORS_AND_ENGINE[
            "batch_name"
        ],
        "commit_after_file_count": BATCH_3_PUBLIC_RECORDS_CONNECTORS_AND_ENGINE[
            "commit_after_file_count"
        ],
        "files": [
            item.copy()
            for item in BATCH_3_PUBLIC_RECORDS_CONNECTORS_AND_ENGINE[
                "files"
            ]
        ],
        "commit_message": BATCH_3_PUBLIC_RECORDS_CONNECTORS_AND_ENGINE[
            "commit_message"
        ],
    }


def get_batch_4_tracker() -> dict[str, Any]:
    """
    Return Batch 4 tracker.
    """

    return {
        "batch_name": BATCH_4_PROPERTY_INTELLIGENCE_CORE[
            "batch_name"
        ],
        "commit_after_file_count": BATCH_4_PROPERTY_INTELLIGENCE_CORE[
            "commit_after_file_count"
        ],
        "files": [
            item.copy()
            for item in BATCH_4_PROPERTY_INTELLIGENCE_CORE["files"]
        ],
        "commit_message": BATCH_4_PROPERTY_INTELLIGENCE_CORE[
            "commit_message"
        ],
    }


def get_public_record_source_capabilities() -> dict[str, list[str]]:
    """
    Return public-record source capability map.
    """

    return {
        "can_support": list(PUBLIC_RECORD_SOURCE_CAPABILITIES["can_support"]),
        "cannot_support_alone": list(
            PUBLIC_RECORD_SOURCE_CAPABILITIES["cannot_support_alone"]
        ),
        "requires_manual_review_when": list(
            PUBLIC_RECORD_SOURCE_CAPABILITIES[
                "requires_manual_review_when"
            ]
        ),
    }


def get_future_listing_source_capabilities() -> dict[str, Any]:
    """
    Return future listing source capability map.
    """

    return {
        "future_source_types": list(
            FUTURE_LISTING_SOURCE_CAPABILITIES["future_source_types"]
        ),
        "will_support_when_connected": list(
            FUTURE_LISTING_SOURCE_CAPABILITIES[
                "will_support_when_connected"
            ]
        ),
        "current_status": FUTURE_LISTING_SOURCE_CAPABILITIES[
            "current_status"
        ],
        "current_rule": FUTURE_LISTING_SOURCE_CAPABILITIES["current_rule"],
    }


def get_source_trust_policy() -> dict[str, dict[str, Any]]:
    """
    Return source trust policy.
    """

    return {
        source_layer: policy.copy()
        for source_layer, policy in PROPERTY_INTELLIGENCE_SOURCE_TRUST_POLICY.items()
    }


def get_property_intelligence_governance() -> dict[str, Any]:
    """
    Return package governance.
    """

    return PROPERTY_INTELLIGENCE_GOVERNANCE.copy()


def get_property_intelligence_module_registry() -> dict[str, dict[str, Any]]:
    """
    Return module registry.
    """

    return {
        module_key: metadata.copy()
        for module_key, metadata in PROPERTY_INTELLIGENCE_MODULE_REGISTRY.items()
    }


def property_claim_requires_listing_feed(claim: str) -> bool:
    """
    Return whether property claim requires a listing feed.
    """

    normalized = normalize_property_intelligence_key(claim)

    return normalized in PROPERTY_INTELLIGENCE_UNSUPPORTED_WITHOUT_LISTING_FEED


def property_claim_requires_valuation_engine(claim: str) -> bool:
    """
    Return whether property claim requires valuation engine.
    """

    normalized = normalize_property_intelligence_key(claim)

    return normalized in PROPERTY_INTELLIGENCE_UNSUPPORTED_WITHOUT_VALUATION_ENGINE


def can_public_records_support_property_claim(claim: str) -> bool:
    """
    Return whether public records can support a property claim.
    """

    normalized = normalize_property_intelligence_key(claim)

    return normalized in PUBLIC_RECORD_SOURCE_CAPABILITIES["can_support"]


def public_records_cannot_support_property_claim_alone(
    claim: str,
) -> bool:
    """
    Return whether public records cannot support claim alone.
    """

    normalized = normalize_property_intelligence_key(claim)

    return normalized in PUBLIC_RECORD_SOURCE_CAPABILITIES[
        "cannot_support_alone"
    ]


def is_mock_property_allowed() -> bool:
    """
    Return whether mock properties are allowed.
    """

    return bool(PROPERTY_INTELLIGENCE_GOVERNANCE["mock_properties_allowed"])


def is_fabricated_listing_status_allowed() -> bool:
    """
    Return whether fabricated listing status is allowed.
    """

    return bool(
        PROPERTY_INTELLIGENCE_GOVERNANCE[
            "fabricated_listing_status_allowed"
        ]
    )


def is_fabricated_property_value_allowed() -> bool:
    """
    Return whether fabricated property values are allowed.
    """

    return bool(
        PROPERTY_INTELLIGENCE_GOVERNANCE[
            "fabricated_property_values_allowed"
        ]
    )


# ============================================================
# SECTION 20 - LAZY IMPORT HELPERS
# ============================================================

def load_property_intelligence_module(
    module_key: str,
) -> Any | None:
    """
    Lazily load a property intelligence module.

    This avoids runtime crashes while future modules are being built
    one file at a time.
    """

    normalized = normalize_property_intelligence_key(module_key)

    metadata = PROPERTY_INTELLIGENCE_MODULE_REGISTRY.get(normalized)

    if metadata is None:
        return None

    module_name = metadata.get("module")

    if not module_name:
        return None

    try:
        return import_module(module_name)
    except Exception:
        return None


def get_property_intelligence_import_status() -> dict[str, dict[str, Any]]:
    """
    Return lazy import status for property intelligence modules.
    """

    status: dict[str, dict[str, Any]] = {}

    for module_key, metadata in PROPERTY_INTELLIGENCE_MODULE_REGISTRY.items():
        module = load_property_intelligence_module(module_key)

        status[module_key] = {
            "module_key": module_key,
            "module": metadata["module"],
            "file": metadata["file"],
            "phase": metadata["phase"],
            "required": metadata["required"],
            "declared_status": metadata["status"],
            "loaded": module is not None,
            "purpose": metadata["purpose"],
        }

    return status


# ============================================================
# SECTION 21 - GOVERNANCE VALIDATION
# ============================================================

def validate_property_intelligence_governance() -> dict[str, Any]:
    """
    Validate property intelligence governance.
    """

    issues: list[dict[str, Any]] = []

    false_keys = [
        "mock_properties_allowed",
        "mock_public_record_results_allowed",
        "fabricated_property_facts_allowed",
        "fabricated_property_values_allowed",
        "fabricated_market_values_allowed",
        "fabricated_listing_status_allowed",
        "fabricated_owner_conclusions_allowed",
        "fabricated_sale_history_allowed",
    ]

    for key in false_keys:
        if PROPERTY_INTELLIGENCE_GOVERNANCE.get(key):
            issues.append(
                {
                    "issue_code": f"{key}_enabled",
                    "severity": "critical",
                    "message": f"{key} must remain False.",
                }
            )

    true_keys = [
        "active_listing_status_requires_listing_feed",
        "under_contract_status_requires_listing_feed",
        "current_listing_price_requires_listing_feed",
        "market_value_requires_valuation_engine",
        "assessment_value_is_not_market_value",
        "public_records_are_not_legal_advice",
        "gis_geometry_is_not_legal_survey",
        "source_attribution_required",
        "confidence_required",
        "source_explanation_required",
        "manual_review_for_ambiguity",
        "manual_review_for_conflicts",
        "unavailable_data_must_be_labeled_unavailable",
    ]

    for key in true_keys:
        if not PROPERTY_INTELLIGENCE_GOVERNANCE.get(key):
            issues.append(
                {
                    "issue_code": f"{key}_disabled",
                    "severity": "critical",
                    "message": f"{key} must remain True.",
                }
            )

    return {
        "valid": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "checked_at": utc_now(),
    }


def validate_property_intelligence_module_registry() -> dict[str, Any]:
    """
    Validate module registry shape.
    """

    issues: list[dict[str, Any]] = []

    for module_key, metadata in PROPERTY_INTELLIGENCE_MODULE_REGISTRY.items():
        if not metadata.get("module"):
            issues.append(
                {
                    "module_key": module_key,
                    "issue_code": "missing_module",
                    "severity": "high",
                    "message": "Module registry entry is missing module path.",
                }
            )

        if not metadata.get("file"):
            issues.append(
                {
                    "module_key": module_key,
                    "issue_code": "missing_file",
                    "severity": "medium",
                    "message": "Module registry entry is missing file path.",
                }
            )

        if not metadata.get("phase"):
            issues.append(
                {
                    "module_key": module_key,
                    "issue_code": "missing_phase",
                    "severity": "medium",
                    "message": "Module registry entry is missing phase.",
                }
            )

        if not metadata.get("purpose"):
            issues.append(
                {
                    "module_key": module_key,
                    "issue_code": "missing_purpose",
                    "severity": "low",
                    "message": "Module registry entry is missing purpose.",
                }
            )

    return {
        "valid": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "checked_at": utc_now(),
    }


# ============================================================
# SECTION 22 - PACKAGE HEALTH AND DIAGNOSTICS
# ============================================================

def get_property_intelligence_health() -> dict[str, Any]:
    """
    Return package health.
    """

    governance_validation = validate_property_intelligence_governance()
    registry_validation = validate_property_intelligence_module_registry()
    import_status = get_property_intelligence_import_status()

    loaded_count = sum(
        1
        for item in import_status.values()
        if item["loaded"]
    )

    return {
        "package": PROPERTY_INTELLIGENCE_PACKAGE_NAME,
        "version": PROPERTY_INTELLIGENCE_PACKAGE_VERSION,
        "phase": PROPERTY_INTELLIGENCE_PACKAGE_PHASE,
        "status": PROPERTY_INTELLIGENCE_PACKAGE_STATUS,
        "release_channel": PROPERTY_INTELLIGENCE_RELEASE_CHANNEL,
        "governance_valid": governance_validation["valid"],
        "governance_issue_count": governance_validation["issue_count"],
        "registry_valid": registry_validation["valid"],
        "registry_issue_count": registry_validation["issue_count"],
        "declared_module_count": len(PROPERTY_INTELLIGENCE_MODULE_REGISTRY),
        "loaded_module_count": loaded_count,
        "mock_properties_allowed": PROPERTY_INTELLIGENCE_GOVERNANCE[
            "mock_properties_allowed"
        ],
        "fabricated_listing_status_allowed": (
            PROPERTY_INTELLIGENCE_GOVERNANCE[
                "fabricated_listing_status_allowed"
            ]
        ),
        "active_listing_status_requires_listing_feed": (
            PROPERTY_INTELLIGENCE_GOVERNANCE[
                "active_listing_status_requires_listing_feed"
            ]
        ),
        "market_value_requires_valuation_engine": (
            PROPERTY_INTELLIGENCE_GOVERNANCE[
                "market_value_requires_valuation_engine"
            ]
        ),
        "generated_at": utc_now(),
    }


def get_property_intelligence_diagnostics() -> dict[str, Any]:
    """
    Return full package diagnostics.
    """

    return {
        "metadata": get_property_intelligence_metadata(),
        "health": get_property_intelligence_health(),
        "principles": get_property_intelligence_principles(),
        "build_order": get_property_intelligence_build_order(),
        "batch_3_tracker": get_batch_3_tracker(),
        "batch_4_tracker": get_batch_4_tracker(),
        "public_record_source_capabilities": (
            get_public_record_source_capabilities()
        ),
        "future_listing_source_capabilities": (
            get_future_listing_source_capabilities()
        ),
        "source_trust_policy": get_source_trust_policy(),
        "governance": get_property_intelligence_governance(),
        "module_registry": get_property_intelligence_module_registry(),
        "import_status": get_property_intelligence_import_status(),
        "governance_validation": (
            validate_property_intelligence_governance()
        ),
        "module_registry_validation": (
            validate_property_intelligence_module_registry()
        ),
        "unsupported_without_listing_feed": list(
            PROPERTY_INTELLIGENCE_UNSUPPORTED_WITHOUT_LISTING_FEED
        ),
        "unsupported_without_valuation_engine": list(
            PROPERTY_INTELLIGENCE_UNSUPPORTED_WITHOUT_VALUATION_ENGINE
        ),
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 23 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "PROPERTY_INTELLIGENCE_PACKAGE_NAME",
    "PROPERTY_INTELLIGENCE_PACKAGE_VERSION",
    "PROPERTY_INTELLIGENCE_PACKAGE_PHASE",
    "PROPERTY_INTELLIGENCE_PACKAGE_STATUS",
    "PROPERTY_INTELLIGENCE_RELEASE_CHANNEL",
    "PROPERTY_INTELLIGENCE_DESCRIPTION",
    "PROPERTY_INTELLIGENCE_MISSION",
    "PROPERTY_INTELLIGENCE_PRINCIPLES",
    "PROPERTY_INTELLIGENCE_ROOT",
    "PROPERTY_INTELLIGENCE_INIT_FILE",
    "PROPERTY_INTELLIGENCE_MODELS_FILE",
    "ADDRESS_INTELLIGENCE_FILE",
    "CONFIDENCE_ENGINE_FILE",
    "SOURCE_EXPLANATION_ENGINE_FILE",
    "PROPERTY_PROFILE_ENGINE_FILE",
    "PROPERTY_INTELLIGENCE_BUILD_ORDER",
    "BATCH_3_PUBLIC_RECORDS_CONNECTORS_AND_ENGINE",
    "BATCH_4_PROPERTY_INTELLIGENCE_CORE",
    "PROPERTY_DOMAIN_ADDRESS",
    "PROPERTY_DOMAIN_PARCEL",
    "PROPERTY_DOMAIN_PUBLIC_RECORDS",
    "PROPERTY_DOMAIN_TAX_ASSESSMENT",
    "PROPERTY_DOMAIN_PROPERTY_TAX",
    "PROPERTY_DOMAIN_DEED",
    "PROPERTY_DOMAIN_MORTGAGE",
    "PROPERTY_DOMAIN_LIEN",
    "PROPERTY_DOMAIN_SALE_HISTORY",
    "PROPERTY_DOMAIN_OWNER_REFERENCE",
    "PROPERTY_DOMAIN_BUILDING_FACTS",
    "PROPERTY_DOMAIN_GIS_CONTEXT",
    "PROPERTY_DOMAIN_MODIV_CONTEXT",
    "PROPERTY_DOMAIN_LISTING_STATUS",
    "PROPERTY_DOMAIN_MARKET_VALUE",
    "PROPERTY_DOMAIN_VALUATION",
    "PROPERTY_DOMAIN_COMPARABLE_SALES",
    "PROPERTY_DOMAIN_RISK_CONTEXT",
    "PROPERTY_DOMAIN_SCHOOL_CONTEXT",
    "PROPERTY_DOMAIN_TRANSIT_CONTEXT",
    "PROPERTY_DOMAIN_UNKNOWN",
    "PROPERTY_INTELLIGENCE_STATUS_READY",
    "PROPERTY_INTELLIGENCE_STATUS_AVAILABLE",
    "PROPERTY_INTELLIGENCE_STATUS_PARTIAL",
    "PROPERTY_INTELLIGENCE_STATUS_UNAVAILABLE",
    "PROPERTY_INTELLIGENCE_STATUS_EMPTY",
    "PROPERTY_INTELLIGENCE_STATUS_ERROR",
    "PROPERTY_INTELLIGENCE_STATUS_NOT_CONNECTED",
    "PROPERTY_INTELLIGENCE_STATUS_NOT_IMPLEMENTED",
    "PROPERTY_INTELLIGENCE_STATUS_MANUAL_REVIEW_REQUIRED",
    "PROPERTY_INTELLIGENCE_STATUS_AMBIGUOUS",
    "PROPERTY_INTELLIGENCE_STATUS_CONFLICTING",
    "PROPERTY_INTELLIGENCE_STATUS_UNKNOWN",
    "SOURCE_LAYER_PUBLIC_RECORDS",
    "SOURCE_LAYER_PUBLIC_RECORDS_ENGINE",
    "SOURCE_LAYER_LISTING_FEED",
    "SOURCE_LAYER_MLS_RESO",
    "SOURCE_LAYER_BROKER_FEED",
    "SOURCE_LAYER_VALUATION_ENGINE",
    "SOURCE_LAYER_AI_SUMMARY",
    "SOURCE_LAYER_USER_PROVIDED_CONTEXT",
    "SOURCE_LAYER_INTERNAL_INFERENCE",
    "SOURCE_LAYER_UNKNOWN",
    "PUBLIC_RECORD_SOURCE_CAPABILITIES",
    "FUTURE_LISTING_SOURCE_CAPABILITIES",
    "PROPERTY_INTELLIGENCE_UNSUPPORTED_WITHOUT_LISTING_FEED",
    "PROPERTY_INTELLIGENCE_UNSUPPORTED_WITHOUT_VALUATION_ENGINE",
    "PROPERTY_INTELLIGENCE_SOURCE_TRUST_POLICY",
    "PROPERTY_INTELLIGENCE_GOVERNANCE",
    "PROPERTY_INTELLIGENCE_MODULE_REGISTRY",
    "utc_now",
    "safe_string",
    "normalize_property_intelligence_key",
    "get_property_intelligence_metadata",
    "get_property_intelligence_principles",
    "get_property_intelligence_build_order",
    "get_batch_3_tracker",
    "get_batch_4_tracker",
    "get_public_record_source_capabilities",
    "get_future_listing_source_capabilities",
    "get_source_trust_policy",
    "get_property_intelligence_governance",
    "get_property_intelligence_module_registry",
    "property_claim_requires_listing_feed",
    "property_claim_requires_valuation_engine",
    "can_public_records_support_property_claim",
    "public_records_cannot_support_property_claim_alone",
    "is_mock_property_allowed",
    "is_fabricated_listing_status_allowed",
    "is_fabricated_property_value_allowed",
    "load_property_intelligence_module",
    "get_property_intelligence_import_status",
    "validate_property_intelligence_governance",
    "validate_property_intelligence_module_registry",
    "get_property_intelligence_health",
    "get_property_intelligence_diagnostics",
]


# ============================================================
# END OF FILE
# ============================================================