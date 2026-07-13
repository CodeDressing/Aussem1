# ============================================================
# AUSSEM1
# PHASE 2.42 PART 1.00
# ENTERPRISE PROPERTY PROFILE ENGINE
# FILE: app/property_intelligence/property_profile_engine.py
# PURPOSE:
# Build the actual source-governed property intelligence profile
# from a user-entered address, normalized address intelligence,
# public-record connector outputs, confidence scoring, source
# explanation, unavailable-field labeling, and future valuation
# readiness rules.
#
# THIS ENGINE CALLS:
# - app.property_intelligence.address_intelligence
# - app.public_records.public_records_engine
# - app.property_intelligence.confidence_engine when available
# - app.property_intelligence.source_explanation_engine when available
#
# THIS ENGINE OUTPUTS:
# - canonical address
# - parcel identity
# - tax assessment context
# - property tax context
# - sale-history references
# - owner references
# - county clerk references
# - GIS context
# - MOD-IV context
# - building facts when source-backed
# - unavailable fields clearly labeled
# - confidence report
# - source explanation report
# - valuation readiness report
#
# CORE GOVERNANCE:
# - No mock homes.
# - No fake property values.
# - No fake listing status.
# - No fake owner conclusions.
# - No fake sale history.
# - No fake comparable properties.
# - No valuation without source-backed inputs.
# - No listing status without authorized listing feed.
# - Public records can support parcel/tax/deed/GIS/MOD-IV context.
# - Public records cannot prove current MLS/listing status alone.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# ENTERPRISE PROPERTY PROFILE ENGINE ACTIVE
# ============================================================


from __future__ import annotations

# ============================================================
# SECTION 01 - STANDARD LIBRARY IMPORTS
# ============================================================

import hashlib
import inspect
import json
import math
import traceback
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from enum import StrEnum
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Mapping
from typing import Sequence


# ============================================================
# SECTION 02 - SAFE OPTIONAL INTERNAL IMPORTS
# ============================================================

try:
    from app.property_intelligence.address_intelligence import (
        AddressAnalysis,
        AddressIntelligenceEngine,
        analyze_address,
        analysis_to_public_record_search_payload,
        make_property_intelligence_request_payload,
        prepare_public_record_search,
    )
except Exception:  # pragma: no cover - fail-safe import protection
    AddressAnalysis = Any  # type: ignore
    AddressIntelligenceEngine = None  # type: ignore
    analyze_address = None  # type: ignore
    analysis_to_public_record_search_payload = None  # type: ignore
    make_property_intelligence_request_payload = None  # type: ignore
    prepare_public_record_search = None  # type: ignore


try:
    from app.public_records.public_records_engine import PublicRecordsEngine
except Exception:  # pragma: no cover - public records engine may still evolve
    PublicRecordsEngine = None  # type: ignore


try:
    from app.property_intelligence.confidence_engine import (
        ConfidenceEngine,
    )
except Exception:  # pragma: no cover - confidence engine may still evolve
    ConfidenceEngine = None  # type: ignore


try:
    from app.property_intelligence.source_explanation_engine import (
        SourceExplanationEngine,
    )
except Exception:  # pragma: no cover - source explanation engine may still evolve
    SourceExplanationEngine = None  # type: ignore


# ============================================================
# SECTION 03 - MODULE METADATA
# ============================================================

PROPERTY_PROFILE_ENGINE_NAME = "Aussem1 Enterprise Property Profile Engine"

PROPERTY_PROFILE_ENGINE_VERSION = "0.2.0"

PROPERTY_PROFILE_ENGINE_PHASE = "PHASE 2.42 PART 1.00"

PROPERTY_PROFILE_ENGINE_STATUS = "enterprise_property_profile_engine_active"

PROPERTY_PROFILE_RELEASE_CHANNEL = "development"


# ============================================================
# SECTION 04 - GOVERNANCE CONSTANTS
# ============================================================

PROPERTY_PROFILE_GOVERNANCE = {
    "mock_property_facts_allowed": False,
    "fabricated_property_values_allowed": False,
    "fabricated_listing_status_allowed": False,
    "fabricated_owner_conclusions_allowed": False,
    "fabricated_sale_history_allowed": False,
    "fabricated_comparables_allowed": False,
    "valuation_without_source_backing_allowed": False,
    "listing_status_without_authorized_feed_allowed": False,
    "public_records_can_support_parcel_context": True,
    "public_records_can_support_tax_context": True,
    "public_records_can_support_deed_references": True,
    "public_records_can_support_sale_references": True,
    "public_records_can_support_gis_context": True,
    "public_records_can_support_modiv_context": True,
    "public_records_cannot_prove_current_listing_status": True,
    "public_records_cannot_prove_current_listing_price": True,
    "public_records_cannot_prove_under_contract_status": True,
    "source_attribution_required": True,
    "confidence_required": True,
    "manual_review_required_for_conflicts": True,
    "unavailable_fields_must_be_labeled": True,
}


PUBLIC_RECORD_SUPPORTED_DOMAINS = [
    "address_identity",
    "parcel_identity",
    "block_lot",
    "tax_assessment",
    "property_tax_context",
    "county_clerk_references",
    "deed_references",
    "mortgage_references",
    "lien_references",
    "sale_history_references",
    "owner_references",
    "gis_context",
    "modiv_context",
    "municipality",
    "county",
    "state",
    "building_facts_when_source_backed",
]


AUTHORIZED_FEED_REQUIRED_DOMAINS = [
    "active_listing_status",
    "under_contract_status",
    "pending_status",
    "current_listing_price",
    "current_days_on_market",
    "showing_availability",
    "offer_deadline",
    "broker_confirmation",
    "current_mls_status",
]


VALUATION_REQUIRED_DOMAINS = [
    "market_value_estimate",
    "confidence_band",
    "comparable_sales_adjustment",
    "appreciation_forecast",
    "investment_return_forecast",
]


PROFILE_REQUIRED_FIELDS = [
    "canonical_address",
    "parcel_identity",
    "tax_assessment_context",
    "public_record_search",
    "confidence_report",
    "source_explanation",
    "unavailable_fields",
]


# ============================================================
# SECTION 05 - ENUMERATIONS
# ============================================================

class PropertyProfileStatus(StrEnum):
    CREATED = "created"
    PARTIAL = "partial"
    SOURCE_LIMITED = "source_limited"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class PropertyFactStatus(StrEnum):
    SOURCE_BACKED = "source_backed"
    INFERRED = "inferred"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    CONFLICTED = "conflicted"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class PropertySourceType(StrEnum):
    ADDRESS_INTELLIGENCE = "address_intelligence"
    PUBLIC_RECORDS_ENGINE = "public_records_engine"
    MORRIS_TAX_BOARD = "morris_tax_board"
    MORRIS_CLERK = "morris_clerk"
    MORRIS_GIS = "morris_gis"
    NJ_STATE_MODIV = "nj_state_modiv"
    AUTHORIZED_LISTING_FEED = "authorized_listing_feed"
    VALUATION_ENGINE = "valuation_engine"
    MANUAL_REVIEW = "manual_review"
    UNKNOWN = "unknown"


class ValuationReadinessStatus(StrEnum):
    READY_FOR_PREVIEW = "ready_for_preview"
    PARTIAL = "partial"
    NOT_READY = "not_ready"
    REQUIRES_COMPARABLES = "requires_comparables"
    REQUIRES_AUTHORIZED_DATA = "requires_authorized_data"


class ListingStatusReadiness(StrEnum):
    NOT_CONNECTED = "not_connected"
    AUTHORIZED_FEED_REQUIRED = "authorized_feed_required"
    AVAILABLE_FROM_FEED = "available_from_feed"


class ManualReviewSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================
# SECTION 06 - UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def safe_string(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def is_blank(value: Any) -> bool:
    return safe_string(value) == ""


def normalize_key(value: Any) -> str:
    text = safe_string(value).lower()
    chars = []

    for character in text:
        if character.isalnum():
            chars.append(character)
        elif chars and chars[-1] != "_":
            chars.append("_")

    normalized = "".join(chars).strip("_")

    return normalized


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def clamp_confidence(value: float) -> float:
    if not math.isfinite(float(value)):
        return 0.0

    return max(0.0, min(1.0, float(value)))


def object_to_dict(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, StrEnum):
        return value.value

    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()

    if hasattr(value, "__dataclass_fields__"):
        return {
            key: object_to_dict(item)
            for key, item in asdict(value).items()
        }

    if isinstance(value, Mapping):
        return {
            str(key): object_to_dict(item)
            for key, item in value.items()
        }

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return [
            object_to_dict(item)
            for item in value
        ]

    return value


def extract_nested_value(payload: Mapping[str, Any], paths: Sequence[str]) -> Any:
    for path in paths:
        current: Any = payload
        found = True

        for part in path.split("."):
            if isinstance(current, Mapping) and part in current:
                current = current[part]
            else:
                found = False
                break

        if found and current not in (None, ""):
            return current

    return None


def flatten_mapping(
    payload: Mapping[str, Any],
    *,
    prefix: str = "",
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in payload.items():
        clean_key = normalize_key(key)
        full_key = f"{prefix}.{clean_key}" if prefix else clean_key

        if isinstance(value, Mapping):
            result.update(flatten_mapping(value, prefix=full_key))
        else:
            result[full_key] = value

    return result


def safe_call(
    callable_object: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> tuple[bool, Any, str | None]:
    try:
        return True, callable_object(*args, **kwargs), None
    except Exception as exc:  # pragma: no cover - runtime protection
        return False, None, f"{type(exc).__name__}: {exc}"


# ============================================================
# SECTION 07 - DATA CONTRACTS
# ============================================================

@dataclass
class PropertyProfileRequest:
    raw_address: str
    municipality: str | None = None
    county: str | None = None
    state_code: str | None = None
    postal_code: str | None = None
    block: str | None = None
    lot: str | None = None
    qualifier: str | None = None
    owner_reference: str | None = None
    include_public_records: bool = True
    include_listing: bool = True
    include_valuation: bool = True
    include_comparables: bool = True
    include_location_context: bool = True
    include_ai_summary: bool = True
    strict_source_mode: bool = True
    allow_manual_review_results: bool = True
    requested_domains: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class SourceReference:
    source_name: str
    source_type: str
    source_authority: str = "unknown"
    source_url: str | None = None
    connector_name: str | None = None
    retrieved_at: str | None = None
    field_path: str | None = None
    record_id: str | None = None
    confidence: float = 0.0
    raw_payload_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class PropertyFact:
    field_name: str
    field_path: str
    value: Any
    status: str
    confidence: float = 0.0
    source_references: list[SourceReference] = field(default_factory=list)
    explanation: str | None = None
    unavailable_reason: str | None = None
    manual_review_required: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class ParcelIdentity:
    parcel_id: str | None = None
    block: str | None = None
    lot: str | None = None
    qualifier: str | None = None
    municipality: str | None = None
    county: str | None = None
    state_code: str | None = None
    property_class: str | None = None
    land_use: str | None = None
    source_status: str = PropertyFactStatus.UNAVAILABLE.value
    confidence: float = 0.0
    sources: list[SourceReference] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class TaxAssessmentContext:
    tax_year: str | None = None
    land_assessment: float | None = None
    improvement_assessment: float | None = None
    total_assessment: float | None = None
    property_class: str | None = None
    equalization_ratio: float | None = None
    assessment_source_note: str = (
        "Tax assessment is public-record context and is not current market value."
    )
    source_status: str = PropertyFactStatus.UNAVAILABLE.value
    confidence: float = 0.0
    sources: list[SourceReference] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class PropertyTaxContext:
    tax_year: str | None = None
    tax_amount: float | None = None
    tax_rate: float | None = None
    estimated_annual_tax: float | None = None
    source_status: str = PropertyFactStatus.UNAVAILABLE.value
    confidence: float = 0.0
    sources: list[SourceReference] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class SaleHistoryReference:
    sale_date: str | None = None
    sale_price: float | None = None
    deed_book: str | None = None
    deed_page: str | None = None
    document_number: str | None = None
    buyer_reference: str | None = None
    seller_reference: str | None = None
    source_status: str = PropertyFactStatus.UNAVAILABLE.value
    confidence: float = 0.0
    sources: list[SourceReference] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class CountyClerkReference:
    document_type: str | None = None
    document_number: str | None = None
    book: str | None = None
    page: str | None = None
    recorded_date: str | None = None
    party_one: str | None = None
    party_two: str | None = None
    source_status: str = PropertyFactStatus.UNAVAILABLE.value
    confidence: float = 0.0
    sources: list[SourceReference] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class OwnerReference:
    owner_name: str | None = None
    mailing_address: str | None = None
    owner_source_note: str = (
        "Owner reference is public-record context and may require manual review."
    )
    source_status: str = PropertyFactStatus.UNAVAILABLE.value
    confidence: float = 0.0
    sources: list[SourceReference] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class GISContext:
    gis_parcel_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    lot_size_acres: float | None = None
    lot_size_square_feet: float | None = None
    geometry_reference: str | None = None
    map_reference: str | None = None
    gis_source_note: str = (
        "GIS context is not a legal boundary survey or title opinion."
    )
    source_status: str = PropertyFactStatus.UNAVAILABLE.value
    confidence: float = 0.0
    sources: list[SourceReference] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class MODIVContext:
    modiv_property_class: str | None = None
    building_description: str | None = None
    year_built: str | None = None
    building_square_feet: float | None = None
    land_description: str | None = None
    source_status: str = PropertyFactStatus.UNAVAILABLE.value
    confidence: float = 0.0
    sources: list[SourceReference] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class BuildingFacts:
    year_built: str | None = None
    bedrooms: float | None = None
    bathrooms: float | None = None
    building_square_feet: float | None = None
    lot_size_acres: float | None = None
    property_type: str | None = None
    source_status: str = PropertyFactStatus.UNAVAILABLE.value
    confidence: float = 0.0
    sources: list[SourceReference] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class ListingStatusContext:
    active_status: str | None = None
    listing_price: float | None = None
    days_on_market: int | None = None
    feed_status: str = ListingStatusReadiness.AUTHORIZED_FEED_REQUIRED.value
    source_status: str = PropertyFactStatus.UNAVAILABLE.value
    explanation: str = (
        "Current listing status requires an authorized MLS, RESO, IDX, "
        "broker-authorized feed, or listing-provider source. Public records "
        "alone cannot prove active, pending, under-contract, or current list price."
    )

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class ValuationReadiness:
    status: str
    ready: bool
    confidence: float
    required_missing_inputs: list[str] = field(default_factory=list)
    available_inputs: list[str] = field(default_factory=list)
    explanation: str = ""
    estimate_allowed: bool = False
    estimate_value: float | None = None
    estimate_low: float | None = None
    estimate_high: float | None = None
    source_status: str = PropertyFactStatus.UNAVAILABLE.value

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class UnavailableField:
    field_name: str
    field_path: str
    reason: str
    required_source: str | None = None
    can_public_records_support: bool = False
    manual_review_required: bool = False
    severity: str = ManualReviewSeverity.INFO.value

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class ManualReviewItem:
    code: str
    message: str
    severity: str = ManualReviewSeverity.WARNING.value
    field_path: str | None = None
    required_action: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class ConfidenceReport:
    overall_confidence: float
    address_confidence: float = 0.0
    public_record_confidence: float = 0.0
    parcel_confidence: float = 0.0
    assessment_confidence: float = 0.0
    source_coverage_score: float = 0.0
    conflict_score: float = 0.0
    manual_review_required: bool = False
    explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class SourceExplanationReport:
    summary: str
    supported_claims: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    public_record_limitations: list[str] = field(default_factory=list)
    required_future_sources: list[str] = field(default_factory=list)
    source_notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class PropertyProfile:
    profile_id: str
    status: str
    request: PropertyProfileRequest
    canonical_address: str | None = None
    normalized_street_address: str | None = None
    address_analysis: dict[str, Any] = field(default_factory=dict)
    public_record_search: dict[str, Any] = field(default_factory=dict)
    parcel_identity: ParcelIdentity = field(default_factory=ParcelIdentity)
    tax_assessment_context: TaxAssessmentContext = field(
        default_factory=TaxAssessmentContext
    )
    property_tax_context: PropertyTaxContext = field(
        default_factory=PropertyTaxContext
    )
    sale_history_references: list[SaleHistoryReference] = field(
        default_factory=list
    )
    county_clerk_references: list[CountyClerkReference] = field(
        default_factory=list
    )
    owner_references: list[OwnerReference] = field(default_factory=list)
    gis_context: GISContext = field(default_factory=GISContext)
    modiv_context: MODIVContext = field(default_factory=MODIVContext)
    building_facts: BuildingFacts = field(default_factory=BuildingFacts)
    listing_status_context: ListingStatusContext = field(
        default_factory=ListingStatusContext
    )
    valuation_readiness: ValuationReadiness = field(
        default_factory=lambda: ValuationReadiness(
            status=ValuationReadinessStatus.NOT_READY.value,
            ready=False,
            confidence=0.0,
            required_missing_inputs=[
                "source_backed_property_profile",
                "comparable_sales",
                "valuation_engine",
            ],
            explanation=(
                "Valuation is not ready until source-backed property facts, "
                "comparable sales, and valuation model metadata are available."
            ),
        )
    )
    facts: list[PropertyFact] = field(default_factory=list)
    unavailable_fields: list[UnavailableField] = field(default_factory=list)
    manual_review_items: list[ManualReviewItem] = field(default_factory=list)
    confidence_report: ConfidenceReport = field(
        default_factory=lambda: ConfidenceReport(
            overall_confidence=0.0,
            explanation="Confidence has not been calculated.",
        )
    )
    source_explanation: SourceExplanationReport = field(
        default_factory=lambda: SourceExplanationReport(
            summary="Source explanation has not been generated.",
        )
    )
    raw_public_record_payload: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class PropertyProfileResult:
    success: bool
    profile: PropertyProfile
    message: str
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


# Backward-compatible aliases for routes or older imports.
PropertyProfileResponse = PropertyProfileResult
PropertyIntelligenceProfile = PropertyProfile


# ============================================================
# SECTION 08 - REQUEST FACTORY
# ============================================================

class PropertyProfileRequestFactory:
    @staticmethod
    def from_raw_address(
        raw_address: str,
        *,
        municipality: str | None = None,
        city: str | None = None,
        county: str | None = None,
        state_code: str | None = None,
        postal_code: str | None = None,
        block: str | None = None,
        lot: str | None = None,
        qualifier: str | None = None,
        owner_reference: str | None = None,
        include_public_records: bool = True,
        include_listing: bool = True,
        include_valuation: bool = True,
        include_comparables: bool = True,
        include_location_context: bool = True,
        include_ai_summary: bool = True,
        strict_source_mode: bool = True,
        allow_manual_review_results: bool = True,
        requested_domains: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PropertyProfileRequest:
        return PropertyProfileRequest(
            raw_address=raw_address,
            municipality=municipality or city,
            county=county,
            state_code=state_code,
            postal_code=postal_code,
            block=block,
            lot=lot,
            qualifier=qualifier,
            owner_reference=owner_reference,
            include_public_records=include_public_records,
            include_listing=include_listing,
            include_valuation=include_valuation,
            include_comparables=include_comparables,
            include_location_context=include_location_context,
            include_ai_summary=include_ai_summary,
            strict_source_mode=strict_source_mode,
            allow_manual_review_results=allow_manual_review_results,
            requested_domains=requested_domains or [],
            metadata=metadata or {},
        )

    @staticmethod
    def from_mapping(payload: Mapping[str, Any]) -> PropertyProfileRequest:
        return PropertyProfileRequest(
            raw_address=safe_string(
                payload.get("raw_address")
                or payload.get("address")
                or payload.get("query")
                or payload.get("raw_query")
            ),
            municipality=payload.get("municipality") or payload.get("city"),
            county=payload.get("county"),
            state_code=payload.get("state_code") or payload.get("state"),
            postal_code=payload.get("postal_code") or payload.get("zip"),
            block=payload.get("block"),
            lot=payload.get("lot"),
            qualifier=payload.get("qualifier"),
            owner_reference=payload.get("owner_reference"),
            include_public_records=bool(
                payload.get("include_public_records", True)
            ),
            include_listing=bool(payload.get("include_listing", True)),
            include_valuation=bool(payload.get("include_valuation", True)),
            include_comparables=bool(payload.get("include_comparables", True)),
            include_location_context=bool(
                payload.get("include_location_context", True)
            ),
            include_ai_summary=bool(payload.get("include_ai_summary", True)),
            strict_source_mode=bool(payload.get("strict_source_mode", True)),
            allow_manual_review_results=bool(
                payload.get("allow_manual_review_results", True)
            ),
            requested_domains=list(payload.get("requested_domains") or []),
            metadata=dict(payload.get("metadata") or {}),
        )


# ============================================================
# SECTION 09 - SOURCE REFERENCE BUILDER
# ============================================================

class SourceReferenceBuilder:
    @staticmethod
    def from_payload(
        *,
        source_name: str,
        source_type: str,
        payload: Mapping[str, Any] | None = None,
        field_path: str | None = None,
        confidence: float = 0.0,
    ) -> SourceReference:
        payload = payload or {}

        return SourceReference(
            source_name=source_name,
            source_type=source_type,
            source_authority=safe_string(
                payload.get("source_authority")
                or payload.get("authority")
                or "public_record"
            ),
            source_url=payload.get("source_url") or payload.get("url"),
            connector_name=payload.get("connector_name")
            or payload.get("connector")
            or source_name,
            retrieved_at=payload.get("retrieved_at") or utc_now(),
            field_path=field_path,
            record_id=payload.get("record_id") or payload.get("id"),
            confidence=clamp_confidence(confidence),
            raw_payload_hash=stable_hash(payload) if payload else None,
            metadata=dict(payload.get("metadata") or {}),
        )

    @staticmethod
    def address_intelligence(
        analysis_payload: Mapping[str, Any],
        *,
        field_path: str | None = None,
    ) -> SourceReference:
        return SourceReference(
            source_name="Address Intelligence",
            source_type=PropertySourceType.ADDRESS_INTELLIGENCE.value,
            source_authority="internal_parser",
            retrieved_at=utc_now(),
            field_path=field_path,
            confidence=clamp_confidence(
                float(analysis_payload.get("confidence") or 0.0)
            ),
            raw_payload_hash=stable_hash(analysis_payload),
            metadata={
                "phase": PROPERTY_PROFILE_ENGINE_PHASE,
                "note": "Address intelligence normalizes lookup input only.",
            },
        )


# ============================================================
# SECTION 10 - PUBLIC RECORDS ADAPTER
# ============================================================

class PublicRecordsAdapter:
    """
    Compatibility layer around app.public_records.public_records_engine.

    This adapter is intentionally defensive because the public-record engine
    is still evolving. It tries several common method names and gracefully
    returns an unavailable payload when the engine cannot be called yet.
    """

    def __init__(
        self,
        engine: Any | None = None,
    ) -> None:
        self.engine = engine if engine is not None else self.create_default_engine()

    @staticmethod
    def create_default_engine() -> Any | None:
        if PublicRecordsEngine is None:
            return None

        try:
            return PublicRecordsEngine()
        except Exception:
            return None

    def collect(
        self,
        search_payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        if self.engine is None:
            return {
                "success": False,
                "status": "public_records_engine_unavailable",
                "records": [],
                "facts": {},
                "sources": [],
                "errors": [
                    {
                        "code": "public_records_engine_unavailable",
                        "message": (
                            "PublicRecordsEngine could not be imported or "
                            "instantiated yet."
                        ),
                    }
                ],
                "metadata": {
                    "adapter": "PublicRecordsAdapter",
                    "generated_at": utc_now(),
                },
            }

        methods = [
            "build_profile",
            "build_public_record_profile",
            "search_public_records",
            "lookup_property",
            "collect",
            "run",
            "execute",
        ]

        for method_name in methods:
            method = getattr(self.engine, method_name, None)

            if not callable(method):
                continue

            success, result, error = self.safe_invoke(method, search_payload)

            if success:
                return self.normalize_result(result, method_name=method_name)

            if error:
                continue

        return {
            "success": False,
            "status": "public_records_method_unavailable",
            "records": [],
            "facts": {},
            "sources": [],
            "errors": [
                {
                    "code": "public_records_method_unavailable",
                    "message": (
                        "PublicRecordsEngine is present, but no compatible "
                        "lookup method was available."
                    ),
                }
            ],
            "metadata": {
                "adapter": "PublicRecordsAdapter",
                "available_methods": [
                    name
                    for name in dir(self.engine)
                    if not name.startswith("_")
                ],
                "generated_at": utc_now(),
            },
        }

    @staticmethod
    def safe_invoke(
        method: Callable[..., Any],
        search_payload: Mapping[str, Any],
    ) -> tuple[bool, Any, str | None]:
        try:
            signature = inspect.signature(method)
            parameter_names = list(signature.parameters)

            if len(parameter_names) == 0:
                return True, method(), None

            if "payload" in parameter_names:
                return True, method(payload=search_payload), None

            if "request" in parameter_names:
                return True, method(request=search_payload), None

            if "search_payload" in parameter_names:
                return True, method(search_payload=search_payload), None

            if "raw_address" in parameter_names:
                return True, method(
                    raw_address=search_payload.get("raw_query")
                    or search_payload.get("street_address")
                    or ""
                ), None

            return True, method(search_payload), None

        except Exception as exc:
            return False, None, f"{type(exc).__name__}: {exc}"

    @staticmethod
    def normalize_result(
        result: Any,
        *,
        method_name: str,
    ) -> dict[str, Any]:
        payload = object_to_dict(result)

        if isinstance(payload, Mapping):
            normalized = dict(payload)
        else:
            normalized = {
                "raw_result": payload,
            }

        normalized.setdefault("success", True)
        normalized.setdefault("status", "public_records_result_collected")
        normalized.setdefault("records", [])
        normalized.setdefault("facts", {})
        normalized.setdefault("sources", [])
        normalized.setdefault("errors", [])
        normalized.setdefault("metadata", {})
        normalized["metadata"]["adapter_method"] = method_name
        normalized["metadata"]["normalized_at"] = utc_now()

        return normalized


# ============================================================
# SECTION 11 - PUBLIC RECORD FACT EXTRACTOR
# ============================================================

class PublicRecordFactExtractor:
    """
    Extract profile sections from public-record payloads.
    """

    def extract_all(
        self,
        payload: Mapping[str, Any],
        address_analysis_payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        flattened = flatten_mapping(payload)

        return {
            "parcel_identity": self.extract_parcel_identity(
                payload,
                flattened,
            ),
            "tax_assessment_context": self.extract_tax_assessment(
                payload,
                flattened,
            ),
            "property_tax_context": self.extract_property_tax(
                payload,
                flattened,
            ),
            "sale_history_references": self.extract_sale_history(
                payload,
                flattened,
            ),
            "county_clerk_references": self.extract_county_clerk(
                payload,
                flattened,
            ),
            "owner_references": self.extract_owner_references(
                payload,
                flattened,
            ),
            "gis_context": self.extract_gis_context(
                payload,
                flattened,
                address_analysis_payload,
            ),
            "modiv_context": self.extract_modiv_context(
                payload,
                flattened,
            ),
            "building_facts": self.extract_building_facts(
                payload,
                flattened,
            ),
        }

    def extract_parcel_identity(
        self,
        payload: Mapping[str, Any],
        flattened: Mapping[str, Any],
    ) -> ParcelIdentity:
        source = SourceReferenceBuilder.from_payload(
            source_name="Public Records Engine",
            source_type=PropertySourceType.PUBLIC_RECORDS_ENGINE.value,
            payload=payload,
            field_path="parcel_identity",
            confidence=0.70,
        )

        parcel_id = self.first_value(
            flattened,
            [
                "parcel_id",
                "parcel.parcel_id",
                "parcel.parcel_number",
                "facts.parcel_id",
                "facts.parcel_number",
                "property.parcel_id",
                "gis.parcel_id",
                "modiv.parcel_id",
            ],
        )

        block = self.first_value(
            flattened,
            [
                "block",
                "parcel.block",
                "facts.block",
                "tax.block",
                "assessment.block",
                "modiv.block",
            ],
        )

        lot = self.first_value(
            flattened,
            [
                "lot",
                "parcel.lot",
                "facts.lot",
                "tax.lot",
                "assessment.lot",
                "modiv.lot",
            ],
        )

        qualifier = self.first_value(
            flattened,
            [
                "qualifier",
                "parcel.qualifier",
                "facts.qualifier",
                "tax.qualifier",
                "assessment.qualifier",
            ],
        )

        municipality = self.first_value(
            flattened,
            [
                "municipality",
                "city",
                "parcel.municipality",
                "facts.municipality",
                "tax.municipality",
            ],
        )

        county = self.first_value(
            flattened,
            [
                "county",
                "parcel.county",
                "facts.county",
            ],
        )

        state_code = self.first_value(
            flattened,
            [
                "state",
                "state_code",
                "parcel.state",
                "parcel.state_code",
            ],
        )

        property_class = self.first_value(
            flattened,
            [
                "property_class",
                "parcel.property_class",
                "assessment.property_class",
                "modiv.property_class",
            ],
        )

        has_data = any(
            value not in (None, "")
            for value in [
                parcel_id,
                block,
                lot,
                municipality,
                county,
                state_code,
                property_class,
            ]
        )

        return ParcelIdentity(
            parcel_id=self.clean_value(parcel_id),
            block=self.clean_value(block),
            lot=self.clean_value(lot),
            qualifier=self.clean_value(qualifier),
            municipality=self.clean_value(municipality),
            county=self.clean_value(county),
            state_code=self.clean_value(state_code),
            property_class=self.clean_value(property_class),
            land_use=self.clean_value(
                self.first_value(
                    flattened,
                    [
                        "land_use",
                        "parcel.land_use",
                        "modiv.land_use",
                    ],
                )
            ),
            source_status=(
                PropertyFactStatus.SOURCE_BACKED.value
                if has_data
                else PropertyFactStatus.UNAVAILABLE.value
            ),
            confidence=0.70 if has_data else 0.0,
            sources=[source] if has_data else [],
        )

    def extract_tax_assessment(
        self,
        payload: Mapping[str, Any],
        flattened: Mapping[str, Any],
    ) -> TaxAssessmentContext:
        source = SourceReferenceBuilder.from_payload(
            source_name="Public Records Engine",
            source_type=PropertySourceType.PUBLIC_RECORDS_ENGINE.value,
            payload=payload,
            field_path="tax_assessment_context",
            confidence=0.70,
        )

        tax_year = self.clean_value(
            self.first_value(
                flattened,
                [
                    "tax_year",
                    "assessment.tax_year",
                    "tax.tax_year",
                    "facts.tax_year",
                ],
            )
        )

        land = self.to_float(
            self.first_value(
                flattened,
                [
                    "land_assessment",
                    "assessment.land_assessment",
                    "tax.land_assessment",
                    "facts.land_assessment",
                    "land_value",
                ],
            )
        )

        improvement = self.to_float(
            self.first_value(
                flattened,
                [
                    "improvement_assessment",
                    "assessment.improvement_assessment",
                    "tax.improvement_assessment",
                    "facts.improvement_assessment",
                    "improvement_value",
                ],
            )
        )

        total = self.to_float(
            self.first_value(
                flattened,
                [
                    "total_assessment",
                    "assessment.total_assessment",
                    "tax.total_assessment",
                    "facts.total_assessment",
                    "assessed_value",
                ],
            )
        )

        property_class = self.clean_value(
            self.first_value(
                flattened,
                [
                    "property_class",
                    "assessment.property_class",
                    "tax.property_class",
                    "modiv.property_class",
                ],
            )
        )

        has_data = any(
            value is not None
            for value in [
                land,
                improvement,
                total,
                property_class,
                tax_year,
            ]
        )

        return TaxAssessmentContext(
            tax_year=tax_year,
            land_assessment=land,
            improvement_assessment=improvement,
            total_assessment=total,
            property_class=property_class,
            equalization_ratio=self.to_float(
                self.first_value(
                    flattened,
                    [
                        "equalization_ratio",
                        "assessment.equalization_ratio",
                        "tax.equalization_ratio",
                    ],
                )
            ),
            source_status=(
                PropertyFactStatus.SOURCE_BACKED.value
                if has_data
                else PropertyFactStatus.UNAVAILABLE.value
            ),
            confidence=0.72 if has_data else 0.0,
            sources=[source] if has_data else [],
        )

    def extract_property_tax(
        self,
        payload: Mapping[str, Any],
        flattened: Mapping[str, Any],
    ) -> PropertyTaxContext:
        source = SourceReferenceBuilder.from_payload(
            source_name="Public Records Engine",
            source_type=PropertySourceType.PUBLIC_RECORDS_ENGINE.value,
            payload=payload,
            field_path="property_tax_context",
            confidence=0.66,
        )

        tax_year = self.clean_value(
            self.first_value(
                flattened,
                [
                    "property_tax.tax_year",
                    "tax.tax_year",
                    "tax_year",
                ],
            )
        )

        tax_amount = self.to_float(
            self.first_value(
                flattened,
                [
                    "tax_amount",
                    "annual_tax",
                    "property_tax.tax_amount",
                    "property_tax.annual_tax",
                    "tax.annual_tax",
                    "tax.tax_amount",
                ],
            )
        )

        tax_rate = self.to_float(
            self.first_value(
                flattened,
                [
                    "tax_rate",
                    "property_tax.tax_rate",
                    "tax.tax_rate",
                ],
            )
        )

        has_data = any(
            value is not None
            for value in [
                tax_amount,
                tax_rate,
                tax_year,
            ]
        )

        return PropertyTaxContext(
            tax_year=tax_year,
            tax_amount=tax_amount,
            tax_rate=tax_rate,
            estimated_annual_tax=tax_amount,
            source_status=(
                PropertyFactStatus.SOURCE_BACKED.value
                if has_data
                else PropertyFactStatus.UNAVAILABLE.value
            ),
            confidence=0.66 if has_data else 0.0,
            sources=[source] if has_data else [],
        )

    def extract_sale_history(
        self,
        payload: Mapping[str, Any],
        flattened: Mapping[str, Any],
    ) -> list[SaleHistoryReference]:
        sale_records = self.extract_record_list(
            payload,
            [
                "sale_history",
                "sales",
                "deed_history",
                "records.sales",
                "facts.sale_history",
            ],
        )

        references: list[SaleHistoryReference] = []

        if not sale_records:
            sale_date = self.clean_value(
                self.first_value(
                    flattened,
                    [
                        "sale_date",
                        "last_sale_date",
                        "facts.sale_date",
                        "deed.sale_date",
                    ],
                )
            )

            sale_price = self.to_float(
                self.first_value(
                    flattened,
                    [
                        "sale_price",
                        "last_sale_price",
                        "facts.sale_price",
                        "deed.sale_price",
                    ],
                )
            )

            if sale_date or sale_price:
                sale_records = [
                    {
                        "sale_date": sale_date,
                        "sale_price": sale_price,
                    }
                ]

        for record in sale_records:
            if not isinstance(record, Mapping):
                continue

            source = SourceReferenceBuilder.from_payload(
                source_name="Public Records Engine",
                source_type=PropertySourceType.PUBLIC_RECORDS_ENGINE.value,
                payload=record,
                field_path="sale_history_references",
                confidence=0.65,
            )

            references.append(
                SaleHistoryReference(
                    sale_date=self.clean_value(
                        record.get("sale_date")
                        or record.get("date")
                        or record.get("recorded_date")
                    ),
                    sale_price=self.to_float(
                        record.get("sale_price")
                        or record.get("price")
                        or record.get("consideration")
                    ),
                    deed_book=self.clean_value(
                        record.get("deed_book") or record.get("book")
                    ),
                    deed_page=self.clean_value(
                        record.get("deed_page") or record.get("page")
                    ),
                    document_number=self.clean_value(
                        record.get("document_number")
                        or record.get("instrument_number")
                        or record.get("id")
                    ),
                    buyer_reference=self.clean_value(
                        record.get("buyer")
                        or record.get("buyer_reference")
                    ),
                    seller_reference=self.clean_value(
                        record.get("seller")
                        or record.get("seller_reference")
                    ),
                    source_status=PropertyFactStatus.SOURCE_BACKED.value,
                    confidence=0.65,
                    sources=[source],
                    metadata=dict(record.get("metadata") or {}),
                )
            )

        return references

    def extract_county_clerk(
        self,
        payload: Mapping[str, Any],
        flattened: Mapping[str, Any],
    ) -> list[CountyClerkReference]:
        records = self.extract_record_list(
            payload,
            [
                "county_clerk",
                "clerk_records",
                "documents",
                "recorded_documents",
                "records.documents",
            ],
        )

        references: list[CountyClerkReference] = []

        for record in records:
            if not isinstance(record, Mapping):
                continue

            source = SourceReferenceBuilder.from_payload(
                source_name="County Clerk Records",
                source_type=PropertySourceType.MORRIS_CLERK.value,
                payload=record,
                field_path="county_clerk_references",
                confidence=0.64,
            )

            references.append(
                CountyClerkReference(
                    document_type=self.clean_value(
                        record.get("document_type") or record.get("type")
                    ),
                    document_number=self.clean_value(
                        record.get("document_number")
                        or record.get("instrument_number")
                        or record.get("id")
                    ),
                    book=self.clean_value(record.get("book")),
                    page=self.clean_value(record.get("page")),
                    recorded_date=self.clean_value(
                        record.get("recorded_date") or record.get("date")
                    ),
                    party_one=self.clean_value(
                        record.get("party_one")
                        or record.get("grantor")
                        or record.get("buyer")
                    ),
                    party_two=self.clean_value(
                        record.get("party_two")
                        or record.get("grantee")
                        or record.get("seller")
                    ),
                    source_status=PropertyFactStatus.SOURCE_BACKED.value,
                    confidence=0.64,
                    sources=[source],
                    metadata=dict(record.get("metadata") or {}),
                )
            )

        return references

    def extract_owner_references(
        self,
        payload: Mapping[str, Any],
        flattened: Mapping[str, Any],
    ) -> list[OwnerReference]:
        owner_records = self.extract_record_list(
            payload,
            [
                "owners",
                "owner_references",
                "records.owners",
            ],
        )

        references: list[OwnerReference] = []

        if not owner_records:
            owner_name = self.clean_value(
                self.first_value(
                    flattened,
                    [
                        "owner",
                        "owner_name",
                        "owner_reference",
                        "facts.owner",
                        "tax.owner",
                    ],
                )
            )

            mailing_address = self.clean_value(
                self.first_value(
                    flattened,
                    [
                        "owner_mailing_address",
                        "mailing_address",
                        "tax.mailing_address",
                    ],
                )
            )

            if owner_name or mailing_address:
                owner_records = [
                    {
                        "owner_name": owner_name,
                        "mailing_address": mailing_address,
                    }
                ]

        for record in owner_records:
            if not isinstance(record, Mapping):
                continue

            source = SourceReferenceBuilder.from_payload(
                source_name="Public Owner Reference",
                source_type=PropertySourceType.PUBLIC_RECORDS_ENGINE.value,
                payload=record,
                field_path="owner_references",
                confidence=0.62,
            )

            references.append(
                OwnerReference(
                    owner_name=self.clean_value(
                        record.get("owner_name") or record.get("name")
                    ),
                    mailing_address=self.clean_value(
                        record.get("mailing_address")
                        or record.get("address")
                    ),
                    source_status=PropertyFactStatus.SOURCE_BACKED.value,
                    confidence=0.62,
                    sources=[source],
                )
            )

        return references

    def extract_gis_context(
        self,
        payload: Mapping[str, Any],
        flattened: Mapping[str, Any],
        address_analysis_payload: Mapping[str, Any],
    ) -> GISContext:
        source = SourceReferenceBuilder.from_payload(
            source_name="GIS Context",
            source_type=PropertySourceType.MORRIS_GIS.value,
            payload=payload,
            field_path="gis_context",
            confidence=0.62,
        )

        latitude = self.to_float(
            self.first_value(
                flattened,
                [
                    "latitude",
                    "lat",
                    "gis.latitude",
                    "gis.lat",
                    "geometry.latitude",
                ],
            )
        )

        longitude = self.to_float(
            self.first_value(
                flattened,
                [
                    "longitude",
                    "lng",
                    "lon",
                    "gis.longitude",
                    "gis.lng",
                    "geometry.longitude",
                ],
            )
        )

        if latitude is None:
            latitude = self.to_float(
                extract_nested_value(
                    address_analysis_payload,
                    [
                        "components.latitude",
                    ],
                )
            )

        if longitude is None:
            longitude = self.to_float(
                extract_nested_value(
                    address_analysis_payload,
                    [
                        "components.longitude",
                    ],
                )
            )

        lot_size_acres = self.to_float(
            self.first_value(
                flattened,
                [
                    "lot_size_acres",
                    "gis.lot_size_acres",
                    "parcel.lot_size_acres",
                ],
            )
        )

        lot_size_square_feet = self.to_float(
            self.first_value(
                flattened,
                [
                    "lot_size_square_feet",
                    "lot_sqft",
                    "gis.lot_size_square_feet",
                    "parcel.lot_size_square_feet",
                ],
            )
        )

        has_data = any(
            value is not None
            for value in [
                latitude,
                longitude,
                lot_size_acres,
                lot_size_square_feet,
            ]
        )

        return GISContext(
            gis_parcel_id=self.clean_value(
                self.first_value(
                    flattened,
                    [
                        "gis.parcel_id",
                        "gis_parcel_id",
                        "parcel_id",
                    ],
                )
            ),
            latitude=latitude,
            longitude=longitude,
            lot_size_acres=lot_size_acres,
            lot_size_square_feet=lot_size_square_feet,
            geometry_reference=self.clean_value(
                self.first_value(
                    flattened,
                    [
                        "geometry_reference",
                        "gis.geometry_reference",
                        "geometry.id",
                    ],
                )
            ),
            map_reference=self.clean_value(
                self.first_value(
                    flattened,
                    [
                        "map_reference",
                        "gis.map_reference",
                        "gis.map_url",
                    ],
                )
            ),
            source_status=(
                PropertyFactStatus.SOURCE_BACKED.value
                if has_data
                else PropertyFactStatus.UNAVAILABLE.value
            ),
            confidence=0.62 if has_data else 0.0,
            sources=[source] if has_data else [],
        )

    def extract_modiv_context(
        self,
        payload: Mapping[str, Any],
        flattened: Mapping[str, Any],
    ) -> MODIVContext:
        source = SourceReferenceBuilder.from_payload(
            source_name="NJ State MOD-IV",
            source_type=PropertySourceType.NJ_STATE_MODIV.value,
            payload=payload,
            field_path="modiv_context",
            confidence=0.60,
        )

        modiv_property_class = self.clean_value(
            self.first_value(
                flattened,
                [
                    "modiv.property_class",
                    "modiv_property_class",
                    "property_class",
                ],
            )
        )

        year_built = self.clean_value(
            self.first_value(
                flattened,
                [
                    "modiv.year_built",
                    "year_built",
                    "building.year_built",
                ],
            )
        )

        building_square_feet = self.to_float(
            self.first_value(
                flattened,
                [
                    "modiv.building_square_feet",
                    "building_square_feet",
                    "building.sqft",
                    "building.area",
                ],
            )
        )

        has_data = any(
            value not in (None, "")
            for value in [
                modiv_property_class,
                year_built,
                building_square_feet,
            ]
        )

        return MODIVContext(
            modiv_property_class=modiv_property_class,
            building_description=self.clean_value(
                self.first_value(
                    flattened,
                    [
                        "modiv.building_description",
                        "building_description",
                    ],
                )
            ),
            year_built=year_built,
            building_square_feet=building_square_feet,
            land_description=self.clean_value(
                self.first_value(
                    flattened,
                    [
                        "modiv.land_description",
                        "land_description",
                    ],
                )
            ),
            source_status=(
                PropertyFactStatus.SOURCE_BACKED.value
                if has_data
                else PropertyFactStatus.UNAVAILABLE.value
            ),
            confidence=0.60 if has_data else 0.0,
            sources=[source] if has_data else [],
        )

    def extract_building_facts(
        self,
        payload: Mapping[str, Any],
        flattened: Mapping[str, Any],
    ) -> BuildingFacts:
        source = SourceReferenceBuilder.from_payload(
            source_name="Public Record Building Facts",
            source_type=PropertySourceType.PUBLIC_RECORDS_ENGINE.value,
            payload=payload,
            field_path="building_facts",
            confidence=0.58,
        )

        year_built = self.clean_value(
            self.first_value(
                flattened,
                [
                    "year_built",
                    "building.year_built",
                    "modiv.year_built",
                ],
            )
        )

        building_square_feet = self.to_float(
            self.first_value(
                flattened,
                [
                    "building_square_feet",
                    "building.sqft",
                    "living_area",
                    "modiv.building_square_feet",
                ],
            )
        )

        lot_size_acres = self.to_float(
            self.first_value(
                flattened,
                [
                    "lot_size_acres",
                    "parcel.lot_size_acres",
                    "gis.lot_size_acres",
                ],
            )
        )

        property_type = self.clean_value(
            self.first_value(
                flattened,
                [
                    "property_type",
                    "building.property_type",
                    "property_class",
                    "modiv.property_class",
                ],
            )
        )

        has_data = any(
            value not in (None, "")
            for value in [
                year_built,
                building_square_feet,
                lot_size_acres,
                property_type,
            ]
        )

        return BuildingFacts(
            year_built=year_built,
            bedrooms=self.to_float(
                self.first_value(
                    flattened,
                    [
                        "bedrooms",
                        "building.bedrooms",
                    ],
                )
            ),
            bathrooms=self.to_float(
                self.first_value(
                    flattened,
                    [
                        "bathrooms",
                        "building.bathrooms",
                    ],
                )
            ),
            building_square_feet=building_square_feet,
            lot_size_acres=lot_size_acres,
            property_type=property_type,
            source_status=(
                PropertyFactStatus.SOURCE_BACKED.value
                if has_data
                else PropertyFactStatus.UNAVAILABLE.value
            ),
            confidence=0.58 if has_data else 0.0,
            sources=[source] if has_data else [],
        )

    @staticmethod
    def first_value(
        payload: Mapping[str, Any],
        keys: Sequence[str],
    ) -> Any:
        for key in keys:
            if key in payload and payload[key] not in (None, ""):
                return payload[key]

        return None

    @staticmethod
    def clean_value(value: Any) -> str | None:
        if value is None:
            return None

        text = safe_string(value)

        return text or None

    @staticmethod
    def to_float(value: Any) -> float | None:
        if value in (None, ""):
            return None

        try:
            text = safe_string(value)
            text = text.replace("$", "").replace(",", "")
            return float(text)
        except Exception:
            return None

    @staticmethod
    def extract_record_list(
        payload: Mapping[str, Any],
        paths: Sequence[str],
    ) -> list[Any]:
        for path in paths:
            value = extract_nested_value(payload, [path])

            if isinstance(value, list):
                return value

        return []


# ============================================================
# SECTION 12 - FACT BUILDER
# ============================================================

class PropertyFactBuilder:
    def build_facts(self, profile: PropertyProfile) -> list[PropertyFact]:
        facts: list[PropertyFact] = []

        facts.extend(self.from_dataclass("parcel_identity", profile.parcel_identity))
        facts.extend(
            self.from_dataclass(
                "tax_assessment_context",
                profile.tax_assessment_context,
            )
        )
        facts.extend(
            self.from_dataclass(
                "property_tax_context",
                profile.property_tax_context,
            )
        )
        facts.extend(self.from_dataclass("gis_context", profile.gis_context))
        facts.extend(self.from_dataclass("modiv_context", profile.modiv_context))
        facts.extend(
            self.from_dataclass("building_facts", profile.building_facts)
        )

        facts.append(
            PropertyFact(
                field_name="listing_status",
                field_path="listing_status_context",
                value=None,
                status=PropertyFactStatus.UNAVAILABLE.value,
                confidence=0.0,
                explanation=profile.listing_status_context.explanation,
                unavailable_reason=(
                    "Authorized listing feed is required for current listing status."
                ),
                manual_review_required=False,
            )
        )

        facts.append(
            PropertyFact(
                field_name="valuation",
                field_path="valuation_readiness",
                value=None,
                status=PropertyFactStatus.UNAVAILABLE.value,
                confidence=profile.valuation_readiness.confidence,
                explanation=profile.valuation_readiness.explanation,
                unavailable_reason=(
                    "Valuation engine and comparable-sales data are not connected yet."
                ),
                manual_review_required=False,
            )
        )

        return facts

    @staticmethod
    def from_dataclass(
        base_path: str,
        section: Any,
    ) -> list[PropertyFact]:
        section_payload = object_to_dict(section)

        if not isinstance(section_payload, Mapping):
            return []

        facts: list[PropertyFact] = []
        status = str(
            section_payload.get("source_status")
            or PropertyFactStatus.UNAVAILABLE.value
        )
        confidence = clamp_confidence(
            float(section_payload.get("confidence") or 0.0)
        )
        sources_payload = section_payload.get("sources") or []
        sources: list[SourceReference] = []

        for source_payload in sources_payload:
            if isinstance(source_payload, Mapping):
                sources.append(
                    SourceReference(
                        source_name=safe_string(
                            source_payload.get("source_name")
                        ),
                        source_type=safe_string(
                            source_payload.get("source_type")
                        ),
                        source_authority=safe_string(
                            source_payload.get("source_authority")
                            or "unknown"
                        ),
                        source_url=source_payload.get("source_url"),
                        connector_name=source_payload.get("connector_name"),
                        retrieved_at=source_payload.get("retrieved_at"),
                        field_path=source_payload.get("field_path"),
                        record_id=source_payload.get("record_id"),
                        confidence=clamp_confidence(
                            float(source_payload.get("confidence") or 0.0)
                        ),
                        raw_payload_hash=source_payload.get("raw_payload_hash"),
                        metadata=dict(source_payload.get("metadata") or {}),
                    )
                )

        for key, value in section_payload.items():
            if key in {
                "source_status",
                "confidence",
                "sources",
                "metadata",
            }:
                continue

            field_path = f"{base_path}.{key}"

            if value in (None, "", []):
                facts.append(
                    PropertyFact(
                        field_name=key,
                        field_path=field_path,
                        value=None,
                        status=PropertyFactStatus.UNAVAILABLE.value,
                        confidence=0.0,
                        unavailable_reason=(
                            f"{field_path} was not available from current sources."
                        ),
                    )
                )
            else:
                facts.append(
                    PropertyFact(
                        field_name=key,
                        field_path=field_path,
                        value=value,
                        status=status,
                        confidence=confidence,
                        source_references=sources,
                    )
                )

        return facts


# ============================================================
# SECTION 13 - UNAVAILABLE FIELD BUILDER
# ============================================================

class UnavailableFieldBuilder:
    def build(self, profile: PropertyProfile) -> list[UnavailableField]:
        fields: list[UnavailableField] = []

        for fact in profile.facts:
            if fact.status == PropertyFactStatus.UNAVAILABLE.value:
                fields.append(
                    UnavailableField(
                        field_name=fact.field_name,
                        field_path=fact.field_path,
                        reason=(
                            fact.unavailable_reason
                            or "Field was unavailable from current source set."
                        ),
                        required_source=self.required_source_for_field(
                            fact.field_path
                        ),
                        can_public_records_support=self.public_records_can_support(
                            fact.field_path
                        ),
                        manual_review_required=fact.manual_review_required,
                        severity=ManualReviewSeverity.INFO.value,
                    )
                )

        for domain in AUTHORIZED_FEED_REQUIRED_DOMAINS:
            fields.append(
                UnavailableField(
                    field_name=domain,
                    field_path=f"listing.{domain}",
                    reason=(
                        "Current listing data requires authorized MLS, RESO, IDX, "
                        "broker feed, or listing-provider integration."
                    ),
                    required_source="authorized_listing_feed",
                    can_public_records_support=False,
                    manual_review_required=False,
                    severity=ManualReviewSeverity.WARNING.value,
                )
            )

        for domain in VALUATION_REQUIRED_DOMAINS:
            fields.append(
                UnavailableField(
                    field_name=domain,
                    field_path=f"valuation.{domain}",
                    reason=(
                        "Valuation output requires valuation engine, comparable-sales "
                        "data, feature set, and confidence metadata."
                    ),
                    required_source="valuation_engine_and_comparable_sales",
                    can_public_records_support=False,
                    manual_review_required=False,
                    severity=ManualReviewSeverity.WARNING.value,
                )
            )

        return self.deduplicate(fields)

    @staticmethod
    def required_source_for_field(field_path: str) -> str | None:
        if field_path.startswith("listing."):
            return "authorized_listing_feed"

        if field_path.startswith("valuation."):
            return "valuation_engine"

        if "county_clerk" in field_path:
            return "county_clerk_public_records"

        if "tax" in field_path or "assessment" in field_path:
            return "tax_board_public_records"

        if "gis" in field_path:
            return "county_gis_public_records"

        if "modiv" in field_path:
            return "nj_state_modiv_public_records"

        return "public_records"

    @staticmethod
    def public_records_can_support(field_path: str) -> bool:
        public_record_paths = [
            "parcel",
            "tax",
            "assessment",
            "owner",
            "sale_history",
            "county_clerk",
            "gis",
            "modiv",
            "building_facts",
        ]

        return any(path in field_path for path in public_record_paths)

    @staticmethod
    def deduplicate(fields: list[UnavailableField]) -> list[UnavailableField]:
        seen: set[str] = set()
        result: list[UnavailableField] = []

        for field_item in fields:
            key = f"{field_item.field_path}:{field_item.reason}"

            if key in seen:
                continue

            seen.add(key)
            result.append(field_item)

        return result


# ============================================================
# SECTION 14 - MANUAL REVIEW BUILDER
# ============================================================

class ManualReviewBuilder:
    def build(self, profile: PropertyProfile) -> list[ManualReviewItem]:
        items: list[ManualReviewItem] = []

        address_payload = profile.address_analysis or {}
        public_record_search = profile.public_record_search or {}

        if address_payload.get("manual_review_required"):
            items.append(
                ManualReviewItem(
                    code="address_manual_review_required",
                    message=(
                        "Address intelligence marked the input for manual review."
                    ),
                    severity=ManualReviewSeverity.WARNING.value,
                    field_path="address_analysis",
                    required_action=(
                        "Confirm street address, municipality, ZIP, or block/lot."
                    ),
                    metadata={
                        "issues": address_payload.get("issues") or [],
                    },
                )
            )

        if public_record_search.get("manual_review_required"):
            items.append(
                ManualReviewItem(
                    code="public_record_search_manual_review_required",
                    message=(
                        "Public-record search preparation requires manual review."
                    ),
                    severity=ManualReviewSeverity.WARNING.value,
                    field_path="public_record_search",
                    required_action=(
                        "Confirm jurisdiction and available public-record connector targets."
                    ),
                    metadata=public_record_search,
                )
            )

        if profile.parcel_identity.source_status == PropertyFactStatus.UNAVAILABLE.value:
            items.append(
                ManualReviewItem(
                    code="parcel_identity_unavailable",
                    message="Parcel identity is not available from current sources.",
                    severity=ManualReviewSeverity.WARNING.value,
                    field_path="parcel_identity",
                    required_action=(
                        "Run tax-board, GIS, MOD-IV, or block/lot lookup."
                    ),
                )
            )

        if profile.confidence_report.overall_confidence < 0.62:
            items.append(
                ManualReviewItem(
                    code="low_profile_confidence",
                    message="Overall profile confidence is below production threshold.",
                    severity=ManualReviewSeverity.WARNING.value,
                    field_path="confidence_report.overall_confidence",
                    required_action=(
                        "Collect more source-backed records before relying on profile."
                    ),
                )
            )

        if profile.errors:
            items.append(
                ManualReviewItem(
                    code="profile_errors_present",
                    message="Profile build recorded one or more runtime errors.",
                    severity=ManualReviewSeverity.ERROR.value,
                    field_path="errors",
                    required_action="Review errors and connector status.",
                    metadata={"errors": profile.errors},
                )
            )

        return items


# ============================================================
# SECTION 15 - CONFIDENCE REPORT BUILDER
# ============================================================

class ProfileConfidenceBuilder:
    def __init__(
        self,
        external_engine: Any | None = None,
    ) -> None:
        self.external_engine = external_engine or self.create_external_engine()

    @staticmethod
    def create_external_engine() -> Any | None:
        if ConfidenceEngine is None:
            return None

        try:
            return ConfidenceEngine()
        except Exception:
            return None

    def build(self, profile: PropertyProfile) -> ConfidenceReport:
        external = self.try_external(profile)

        if external:
            return external

        address_confidence = clamp_confidence(
            float(
                extract_nested_value(
                    profile.address_analysis,
                    ["confidence"],
                )
                or 0.0
            )
        )

        parcel_confidence = clamp_confidence(profile.parcel_identity.confidence)
        assessment_confidence = clamp_confidence(
            profile.tax_assessment_context.confidence
        )

        source_backed_count = sum(
            1
            for fact in profile.facts
            if fact.status == PropertyFactStatus.SOURCE_BACKED.value
        )

        fact_count = max(len(profile.facts), 1)

        source_coverage_score = clamp_confidence(
            source_backed_count / fact_count
        )

        conflict_score = 0.0

        public_record_confidence = clamp_confidence(
            (
                parcel_confidence
                + assessment_confidence
                + profile.gis_context.confidence
                + profile.modiv_context.confidence
                + profile.building_facts.confidence
            )
            / 5
        )

        overall = clamp_confidence(
            (
                address_confidence * 0.30
                + public_record_confidence * 0.35
                + source_coverage_score * 0.25
                + (1.0 - conflict_score) * 0.10
            )
        )

        manual_review_required = (
            overall < 0.62
            or any(item.severity in {"error", "critical"} for item in profile.manual_review_items)
            or bool(profile.errors)
        )

        explanation = (
            "Profile confidence is calculated from address confidence, public-record "
            "coverage, parcel/assessment/GIS/MOD-IV availability, source coverage, "
            "and conflict/manual-review state."
        )

        return ConfidenceReport(
            overall_confidence=round(overall, 6),
            address_confidence=round(address_confidence, 6),
            public_record_confidence=round(public_record_confidence, 6),
            parcel_confidence=round(parcel_confidence, 6),
            assessment_confidence=round(assessment_confidence, 6),
            source_coverage_score=round(source_coverage_score, 6),
            conflict_score=round(conflict_score, 6),
            manual_review_required=manual_review_required,
            explanation=explanation,
            metadata={
                "source_backed_fact_count": source_backed_count,
                "fact_count": len(profile.facts),
                "external_engine_used": False,
                "generated_at": utc_now(),
            },
        )

    def try_external(self, profile: PropertyProfile) -> ConfidenceReport | None:
        if self.external_engine is None:
            return None

        method_names = [
            "evaluate_profile",
            "score_profile",
            "build_confidence_report",
            "evaluate",
        ]

        for method_name in method_names:
            method = getattr(self.external_engine, method_name, None)

            if not callable(method):
                continue

            success, result, error = safe_call(method, profile.to_dict())

            if not success:
                success, result, error = safe_call(method, profile)

            if not success:
                continue

            payload = object_to_dict(result)

            if isinstance(payload, Mapping):
                return ConfidenceReport(
                    overall_confidence=clamp_confidence(
                        float(
                            payload.get("overall_confidence")
                            or payload.get("confidence")
                            or 0.0
                        )
                    ),
                    address_confidence=clamp_confidence(
                        float(payload.get("address_confidence") or 0.0)
                    ),
                    public_record_confidence=clamp_confidence(
                        float(payload.get("public_record_confidence") or 0.0)
                    ),
                    parcel_confidence=clamp_confidence(
                        float(payload.get("parcel_confidence") or 0.0)
                    ),
                    assessment_confidence=clamp_confidence(
                        float(payload.get("assessment_confidence") or 0.0)
                    ),
                    source_coverage_score=clamp_confidence(
                        float(payload.get("source_coverage_score") or 0.0)
                    ),
                    conflict_score=clamp_confidence(
                        float(payload.get("conflict_score") or 0.0)
                    ),
                    manual_review_required=bool(
                        payload.get("manual_review_required", False)
                    ),
                    explanation=safe_string(
                        payload.get("explanation")
                        or "External confidence engine produced this report."
                    ),
                    metadata={
                        "external_engine_used": True,
                        "external_method": method_name,
                        "raw_payload": payload,
                    },
                )

        return None


# ============================================================
# SECTION 16 - SOURCE EXPLANATION BUILDER
# ============================================================

class ProfileSourceExplanationBuilder:
    def __init__(
        self,
        external_engine: Any | None = None,
    ) -> None:
        self.external_engine = external_engine or self.create_external_engine()

    @staticmethod
    def create_external_engine() -> Any | None:
        if SourceExplanationEngine is None:
            return None

        try:
            return SourceExplanationEngine()
        except Exception:
            return None

    def build(self, profile: PropertyProfile) -> SourceExplanationReport:
        external = self.try_external(profile)

        if external:
            return external

        supported_claims: list[str] = []

        if profile.parcel_identity.source_status == PropertyFactStatus.SOURCE_BACKED.value:
            supported_claims.append("Parcel identity is supported by public-record context.")

        if profile.tax_assessment_context.source_status == PropertyFactStatus.SOURCE_BACKED.value:
            supported_claims.append("Tax assessment context is supported by public-record context.")

        if profile.gis_context.source_status == PropertyFactStatus.SOURCE_BACKED.value:
            supported_claims.append("GIS context is supported by public-record context.")

        if profile.modiv_context.source_status == PropertyFactStatus.SOURCE_BACKED.value:
            supported_claims.append("MOD-IV context is supported by public-record context.")

        if profile.sale_history_references:
            supported_claims.append("Sale-history references were found in available public-record context.")

        if profile.owner_references:
            supported_claims.append("Owner references were found in available public-record context.")

        unsupported_claims = [
            "Current active listing status is not proven by public records alone.",
            "Current under-contract or pending status is not proven by public records alone.",
            "Current listing price is not proven by public records alone.",
            "Market value estimate is not produced until valuation engine inputs are ready.",
            "Comparable sales are not fabricated and require a connected comparable-sales source.",
        ]

        public_record_limitations = [
            "Tax assessment is not current market value.",
            "GIS context is not a legal survey.",
            "County clerk records may require manual review for party names and document meaning.",
            "Public records may lag current transaction or listing activity.",
        ]

        required_future_sources = [
            "authorized_mls_reso_idx_or_broker_feed",
            "comparable_sales_dataset",
            "valuation_engine",
            "geocoder_or_parcel_resolution_provider",
            "persistent_property_database",
        ]

        if not supported_claims:
            summary = (
                "The property profile was created, but current public-record facts "
                "are unavailable or not yet connected. The system labeled missing "
                "fields explicitly instead of fabricating property facts."
            )
        else:
            summary = (
                "The property profile was created with source-governed sections. "
                "Available public-record context was separated from unavailable "
                "listing and valuation claims."
            )

        return SourceExplanationReport(
            summary=summary,
            supported_claims=supported_claims,
            unsupported_claims=unsupported_claims,
            public_record_limitations=public_record_limitations,
            required_future_sources=required_future_sources,
            source_notes=[
                "Address intelligence prepares lookup input and does not prove property facts by itself.",
                "Public records support historical and administrative property context.",
                "Listing feed integration is required for current market activity.",
            ],
            metadata={
                "external_engine_used": False,
                "generated_at": utc_now(),
            },
        )

    def try_external(self, profile: PropertyProfile) -> SourceExplanationReport | None:
        if self.external_engine is None:
            return None

        method_names = [
            "explain_profile",
            "build_profile_explanation",
            "explain",
            "generate",
        ]

        for method_name in method_names:
            method = getattr(self.external_engine, method_name, None)

            if not callable(method):
                continue

            success, result, error = safe_call(method, profile.to_dict())

            if not success:
                success, result, error = safe_call(method, profile)

            if not success:
                continue

            payload = object_to_dict(result)

            if isinstance(payload, Mapping):
                return SourceExplanationReport(
                    summary=safe_string(
                        payload.get("summary")
                        or payload.get("explanation")
                        or "External source explanation engine generated this report."
                    ),
                    supported_claims=list(payload.get("supported_claims") or []),
                    unsupported_claims=list(payload.get("unsupported_claims") or []),
                    public_record_limitations=list(
                        payload.get("public_record_limitations") or []
                    ),
                    required_future_sources=list(
                        payload.get("required_future_sources") or []
                    ),
                    source_notes=list(payload.get("source_notes") or []),
                    metadata={
                        "external_engine_used": True,
                        "external_method": method_name,
                        "raw_payload": payload,
                    },
                )

        return None


# ============================================================
# SECTION 17 - VALUATION READINESS BUILDER
# ============================================================

class ValuationReadinessBuilder:
    def build(self, profile: PropertyProfile) -> ValuationReadiness:
        available_inputs: list[str] = []
        missing_inputs: list[str] = []

        if profile.parcel_identity.source_status == PropertyFactStatus.SOURCE_BACKED.value:
            available_inputs.append("parcel_identity")
        else:
            missing_inputs.append("parcel_identity")

        if profile.tax_assessment_context.total_assessment is not None:
            available_inputs.append("tax_assessment")
        else:
            missing_inputs.append("tax_assessment")

        if profile.building_facts.building_square_feet is not None:
            available_inputs.append("building_square_feet")
        else:
            missing_inputs.append("building_square_feet")

        if profile.gis_context.lot_size_acres is not None or profile.gis_context.lot_size_square_feet is not None:
            available_inputs.append("lot_size")
        else:
            missing_inputs.append("lot_size")

        missing_inputs.extend(
            [
                "comparable_sales",
                "valuation_model",
                "valuation_confidence_calibration",
            ]
        )

        source_backed_base = len(available_inputs) >= 2

        confidence = clamp_confidence(len(available_inputs) / 7)

        if source_backed_base:
            status = ValuationReadinessStatus.REQUIRES_COMPARABLES.value
            explanation = (
                "A partial source-backed base exists, but valuation remains unavailable "
                "until comparable sales and valuation model logic are connected."
            )
        else:
            status = ValuationReadinessStatus.NOT_READY.value
            explanation = (
                "Valuation is not ready because core property facts and comparable-sales "
                "inputs are unavailable."
            )

        return ValuationReadiness(
            status=status,
            ready=False,
            confidence=round(confidence, 6),
            required_missing_inputs=missing_inputs,
            available_inputs=available_inputs,
            explanation=explanation,
            estimate_allowed=False,
            estimate_value=None,
            estimate_low=None,
            estimate_high=None,
            source_status=PropertyFactStatus.UNAVAILABLE.value,
        )


# ============================================================
# SECTION 18 - PROFILE STATUS RESOLVER
# ============================================================

class PropertyProfileStatusResolver:
    @staticmethod
    def resolve(profile: PropertyProfile) -> str:
        if profile.errors:
            return PropertyProfileStatus.ERROR.value

        if profile.manual_review_items:
            return PropertyProfileStatus.MANUAL_REVIEW_REQUIRED.value

        if profile.confidence_report.overall_confidence >= 0.82:
            return PropertyProfileStatus.CREATED.value

        if profile.confidence_report.overall_confidence >= 0.50:
            return PropertyProfileStatus.PARTIAL.value

        if profile.address_analysis:
            return PropertyProfileStatus.SOURCE_LIMITED.value

        return PropertyProfileStatus.UNAVAILABLE.value


# ============================================================
# SECTION 19 - ENTERPRISE PROPERTY PROFILE ENGINE
# ============================================================

class PropertyProfileEngine:
    def __init__(
        self,
        *,
        address_engine: Any | None = None,
        public_records_adapter: PublicRecordsAdapter | None = None,
        fact_extractor: PublicRecordFactExtractor | None = None,
        fact_builder: PropertyFactBuilder | None = None,
        unavailable_field_builder: UnavailableFieldBuilder | None = None,
        manual_review_builder: ManualReviewBuilder | None = None,
        confidence_builder: ProfileConfidenceBuilder | None = None,
        source_explanation_builder: ProfileSourceExplanationBuilder | None = None,
        valuation_readiness_builder: ValuationReadinessBuilder | None = None,
    ) -> None:
        if address_engine is not None:
            self.address_engine = address_engine
        elif AddressIntelligenceEngine is not None:
            self.address_engine = AddressIntelligenceEngine()
        else:
            self.address_engine = None

        self.public_records_adapter = public_records_adapter or PublicRecordsAdapter()
        self.fact_extractor = fact_extractor or PublicRecordFactExtractor()
        self.fact_builder = fact_builder or PropertyFactBuilder()
        self.unavailable_field_builder = (
            unavailable_field_builder or UnavailableFieldBuilder()
        )
        self.manual_review_builder = manual_review_builder or ManualReviewBuilder()
        self.confidence_builder = confidence_builder or ProfileConfidenceBuilder()
        self.source_explanation_builder = (
            source_explanation_builder or ProfileSourceExplanationBuilder()
        )
        self.valuation_readiness_builder = (
            valuation_readiness_builder or ValuationReadinessBuilder()
        )

    def build_profile(
        self,
        request: PropertyProfileRequest | Mapping[str, Any] | str,
        **kwargs: Any,
    ) -> PropertyProfileResult:
        profile_request = self.normalize_request(request, **kwargs)

        profile_id = self.make_profile_id(profile_request)

        profile = PropertyProfile(
            profile_id=profile_id,
            status=PropertyProfileStatus.CREATED.value,
            request=profile_request,
            metadata={
                "engine": PROPERTY_PROFILE_ENGINE_NAME,
                "version": PROPERTY_PROFILE_ENGINE_VERSION,
                "phase": PROPERTY_PROFILE_ENGINE_PHASE,
                "governance": PROPERTY_PROFILE_GOVERNANCE.copy(),
                "started_at": utc_now(),
            },
        )

        try:
            self.apply_address_intelligence(profile)

            if profile_request.include_public_records:
                self.apply_public_records(profile)
            else:
                profile.manual_review_items.append(
                    ManualReviewItem(
                        code="public_records_not_requested",
                        message="Public-record collection was disabled for this request.",
                        severity=ManualReviewSeverity.INFO.value,
                        field_path="request.include_public_records",
                    )
                )

            profile.facts = self.fact_builder.build_facts(profile)
            profile.valuation_readiness = self.valuation_readiness_builder.build(
                profile
            )
            profile.facts = self.fact_builder.build_facts(profile)
            profile.unavailable_fields = self.unavailable_field_builder.build(
                profile
            )
            profile.manual_review_items.extend(
                self.manual_review_builder.build(profile)
            )
            profile.confidence_report = self.confidence_builder.build(profile)
            profile.source_explanation = self.source_explanation_builder.build(
                profile
            )
            profile.status = PropertyProfileStatusResolver.resolve(profile)
            profile.updated_at = utc_now()
            profile.metadata["completed_at"] = utc_now()

            return PropertyProfileResult(
                success=not profile.errors,
                profile=profile,
                message=(
                    "Property profile created with source-governed facts. "
                    "Unavailable listing and valuation claims were labeled instead "
                    "of fabricated."
                ),
                errors=profile.errors,
                warnings=[
                    item.message
                    for item in profile.manual_review_items
                    if item.severity in {
                        ManualReviewSeverity.WARNING.value,
                        ManualReviewSeverity.ERROR.value,
                        ManualReviewSeverity.CRITICAL.value,
                    }
                ],
                metadata={
                    "engine": PROPERTY_PROFILE_ENGINE_NAME,
                    "version": PROPERTY_PROFILE_ENGINE_VERSION,
                    "phase": PROPERTY_PROFILE_ENGINE_PHASE,
                    "generated_at": utc_now(),
                },
            )

        except Exception as exc:  # pragma: no cover - runtime protection
            error_payload = {
                "code": "property_profile_engine_error",
                "message": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "created_at": utc_now(),
            }
            profile.errors.append(error_payload)
            profile.status = PropertyProfileStatus.ERROR.value
            profile.updated_at = utc_now()

            return PropertyProfileResult(
                success=False,
                profile=profile,
                message="Property profile build failed.",
                errors=profile.errors,
                warnings=[],
                metadata={
                    "engine": PROPERTY_PROFILE_ENGINE_NAME,
                    "version": PROPERTY_PROFILE_ENGINE_VERSION,
                    "phase": PROPERTY_PROFILE_ENGINE_PHASE,
                    "generated_at": utc_now(),
                },
            )

    def apply_address_intelligence(self, profile: PropertyProfile) -> None:
        request = profile.request

        if self.address_engine is None and analyze_address is None:
            raise RuntimeError("Address intelligence engine is unavailable.")

        if self.address_engine is not None:
            address_result = self.address_engine.analyze(
                request.raw_address,
                municipality=request.municipality,
                county=request.county,
                state_code=request.state_code,
                postal_code=request.postal_code,
                owner_reference=request.owner_reference,
            )
        else:
            address_result = analyze_address(  # type: ignore[misc]
                request.raw_address,
                municipality=request.municipality,
                county=request.county,
                state_code=request.state_code,
                postal_code=request.postal_code,
                owner_reference=request.owner_reference,
            )

        address_payload = object_to_dict(address_result)

        profile.address_analysis = address_payload
        profile.canonical_address = safe_string(
            address_payload.get("canonical_address")
        ) or None
        profile.normalized_street_address = safe_string(
            address_payload.get("normalized_street_address")
        ) or None
        profile.public_record_search = dict(
            address_payload.get("public_record_search") or {}
        )

        self.apply_address_to_sections(profile, address_payload)

    def apply_address_to_sections(
        self,
        profile: PropertyProfile,
        address_payload: Mapping[str, Any],
    ) -> None:
        components = address_payload.get("components") or {}

        if not isinstance(components, Mapping):
            return

        address_source = SourceReferenceBuilder.address_intelligence(
            address_payload,
            field_path="canonical_address",
        )

        block = components.get("block")
        lot = components.get("lot")
        qualifier = components.get("qualifier")
        municipality = components.get("municipality")
        county = components.get("county")
        state_code = components.get("state_code")

        if any(value not in (None, "") for value in [block, lot, municipality, county, state_code]):
            profile.parcel_identity.block = block
            profile.parcel_identity.lot = lot
            profile.parcel_identity.qualifier = qualifier
            profile.parcel_identity.municipality = municipality
            profile.parcel_identity.county = county
            profile.parcel_identity.state_code = state_code
            profile.parcel_identity.source_status = PropertyFactStatus.INFERRED.value
            profile.parcel_identity.confidence = clamp_confidence(
                float(address_payload.get("confidence") or 0.0)
            )
            profile.parcel_identity.sources = [address_source]

        latitude = components.get("latitude")
        longitude = components.get("longitude")

        if latitude not in (None, "") or longitude not in (None, ""):
            profile.gis_context.latitude = self.safe_float(latitude)
            profile.gis_context.longitude = self.safe_float(longitude)
            profile.gis_context.source_status = PropertyFactStatus.INFERRED.value
            profile.gis_context.confidence = clamp_confidence(
                float(address_payload.get("confidence") or 0.0)
            )
            profile.gis_context.sources = [address_source]

    def apply_public_records(self, profile: PropertyProfile) -> None:
        search_payload = self.build_public_record_search_payload(profile)

        payload = self.public_records_adapter.collect(search_payload)

        profile.raw_public_record_payload = payload

        if not payload.get("success"):
            profile.errors.extend(
                [
                    {
                        "code": error.get("code", "public_record_error"),
                        "message": error.get("message", "Public record error."),
                        "metadata": error,
                    }
                    for error in payload.get("errors", [])
                    if isinstance(error, Mapping)
                ]
            )

            return

        sections = self.fact_extractor.extract_all(
            payload,
            profile.address_analysis,
        )

        self.merge_extracted_sections(profile, sections)

    def build_public_record_search_payload(
        self,
        profile: PropertyProfile,
    ) -> dict[str, Any]:
        if analysis_to_public_record_search_payload is not None:
            try:
                payload = analysis_to_public_record_search_payload(  # type: ignore[misc]
                    self.reconstruct_address_analysis_payload(
                        profile.address_analysis
                    )
                )
                if isinstance(payload, Mapping):
                    return dict(payload)
            except Exception:
                pass

        search = profile.public_record_search or {}
        request = profile.request

        return {
            "raw_query": search.get("raw_query") or request.raw_address,
            "street_address": search.get("street_address")
            or profile.normalized_street_address,
            "municipality": search.get("municipality") or request.municipality,
            "county": search.get("county") or request.county,
            "state": search.get("state_code") or request.state_code,
            "postal_code": search.get("postal_code") or request.postal_code,
            "block": search.get("block") or request.block,
            "lot": search.get("lot") or request.lot,
            "qualifier": search.get("qualifier") or request.qualifier,
            "owner_reference": search.get("owner_reference")
            or request.owner_reference,
            "metadata": {
                "source": "property_profile_engine",
                "profile_id": profile.profile_id,
                "address_analysis": profile.address_analysis,
                "public_record_search": search,
                "generated_at": utc_now(),
            },
        }

    @staticmethod
    def reconstruct_address_analysis_payload(payload: Mapping[str, Any]) -> Any:
        return payload

    def merge_extracted_sections(
        self,
        profile: PropertyProfile,
        sections: Mapping[str, Any],
    ) -> None:
        parcel_identity = sections.get("parcel_identity")

        if isinstance(parcel_identity, ParcelIdentity):
            profile.parcel_identity = self.prefer_source_backed_parcel(
                profile.parcel_identity,
                parcel_identity,
            )

        tax_assessment = sections.get("tax_assessment_context")

        if isinstance(tax_assessment, TaxAssessmentContext):
            profile.tax_assessment_context = tax_assessment

        property_tax = sections.get("property_tax_context")

        if isinstance(property_tax, PropertyTaxContext):
            profile.property_tax_context = property_tax

        sale_history = sections.get("sale_history_references")

        if isinstance(sale_history, list):
            profile.sale_history_references = sale_history

        county_clerk = sections.get("county_clerk_references")

        if isinstance(county_clerk, list):
            profile.county_clerk_references = county_clerk

        owner_references = sections.get("owner_references")

        if isinstance(owner_references, list):
            profile.owner_references = owner_references

        gis_context = sections.get("gis_context")

        if isinstance(gis_context, GISContext):
            profile.gis_context = self.prefer_source_backed_gis(
                profile.gis_context,
                gis_context,
            )

        modiv_context = sections.get("modiv_context")

        if isinstance(modiv_context, MODIVContext):
            profile.modiv_context = modiv_context

        building_facts = sections.get("building_facts")

        if isinstance(building_facts, BuildingFacts):
            profile.building_facts = building_facts

    @staticmethod
    def prefer_source_backed_parcel(
        current: ParcelIdentity,
        candidate: ParcelIdentity,
    ) -> ParcelIdentity:
        if candidate.source_status == PropertyFactStatus.SOURCE_BACKED.value:
            return candidate

        return current

    @staticmethod
    def prefer_source_backed_gis(
        current: GISContext,
        candidate: GISContext,
    ) -> GISContext:
        if candidate.source_status == PropertyFactStatus.SOURCE_BACKED.value:
            return candidate

        return current

    @staticmethod
    def normalize_request(
        request: PropertyProfileRequest | Mapping[str, Any] | str,
        **kwargs: Any,
    ) -> PropertyProfileRequest:
        if isinstance(request, PropertyProfileRequest):
            return request

        if isinstance(request, Mapping):
            merged = dict(request)
            merged.update(kwargs)

            return PropertyProfileRequestFactory.from_mapping(merged)

        if isinstance(request, str):
            return PropertyProfileRequestFactory.from_raw_address(
                request,
                **kwargs,
            )

        raise TypeError(
            "request must be PropertyProfileRequest, mapping, or raw address string"
        )

    @staticmethod
    def make_profile_id(request: PropertyProfileRequest) -> str:
        return f"property-profile-{stable_hash(request.to_dict())[:18]}"

    @staticmethod
    def safe_float(value: Any) -> float | None:
        if value in (None, ""):
            return None

        try:
            return float(value)
        except Exception:
            return None


# Backward-compatible class alias.
PropertyProfileBuilder = PropertyProfileEngine


# ============================================================
# SECTION 20 - CONVENIENCE API
# ============================================================

_default_property_profile_engine = PropertyProfileEngine()


def build_property_profile(
    raw_address: str | Mapping[str, Any] | PropertyProfileRequest,
    **kwargs: Any,
) -> PropertyProfileResult:
    return _default_property_profile_engine.build_profile(
        raw_address,
        **kwargs,
    )


def build_property_profile_dict(
    raw_address: str | Mapping[str, Any] | PropertyProfileRequest,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_property_profile(raw_address, **kwargs).to_dict()


def build_profile(
    raw_address: str | Mapping[str, Any] | PropertyProfileRequest,
    **kwargs: Any,
) -> PropertyProfileResult:
    return build_property_profile(raw_address, **kwargs)


def create_property_profile(
    raw_address: str | Mapping[str, Any] | PropertyProfileRequest,
    **kwargs: Any,
) -> PropertyProfileResult:
    return build_property_profile(raw_address, **kwargs)


def profile_to_public_api_payload(
    result: PropertyProfileResult | PropertyProfile,
) -> dict[str, Any]:
    if isinstance(result, PropertyProfileResult):
        profile = result.profile
        success = result.success
        message = result.message
        errors = result.errors
        warnings = result.warnings
    else:
        profile = result
        success = not profile.errors
        message = "Property profile payload generated."
        errors = profile.errors
        warnings = [
            item.message
            for item in profile.manual_review_items
        ]

    return {
        "success": success,
        "message": message,
        "profile_id": profile.profile_id,
        "status": profile.status,
        "canonical_address": profile.canonical_address,
        "normalized_street_address": profile.normalized_street_address,
        "parcel_identity": profile.parcel_identity.to_dict(),
        "tax_assessment_context": profile.tax_assessment_context.to_dict(),
        "property_tax_context": profile.property_tax_context.to_dict(),
        "sale_history_references": [
            item.to_dict()
            for item in profile.sale_history_references
        ],
        "county_clerk_references": [
            item.to_dict()
            for item in profile.county_clerk_references
        ],
        "owner_references": [
            item.to_dict()
            for item in profile.owner_references
        ],
        "gis_context": profile.gis_context.to_dict(),
        "modiv_context": profile.modiv_context.to_dict(),
        "building_facts": profile.building_facts.to_dict(),
        "listing_status_context": profile.listing_status_context.to_dict(),
        "valuation_readiness": profile.valuation_readiness.to_dict(),
        "confidence_report": profile.confidence_report.to_dict(),
        "source_explanation": profile.source_explanation.to_dict(),
        "unavailable_fields": [
            item.to_dict()
            for item in profile.unavailable_fields
        ],
        "manual_review_items": [
            item.to_dict()
            for item in profile.manual_review_items
        ],
        "errors": errors,
        "warnings": warnings,
        "metadata": {
            "engine": PROPERTY_PROFILE_ENGINE_NAME,
            "version": PROPERTY_PROFILE_ENGINE_VERSION,
            "phase": PROPERTY_PROFILE_ENGINE_PHASE,
            "generated_at": utc_now(),
        },
    }


# ============================================================
# SECTION 21 - HEALTH, READINESS, AND DIAGNOSTICS
# ============================================================

def validate_property_profile_governance() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    false_keys = [
        "mock_property_facts_allowed",
        "fabricated_property_values_allowed",
        "fabricated_listing_status_allowed",
        "fabricated_owner_conclusions_allowed",
        "fabricated_sale_history_allowed",
        "fabricated_comparables_allowed",
        "valuation_without_source_backing_allowed",
        "listing_status_without_authorized_feed_allowed",
    ]

    for key in false_keys:
        if PROPERTY_PROFILE_GOVERNANCE.get(key):
            issues.append(
                {
                    "issue_code": f"{key}_must_remain_false",
                    "severity": "critical",
                    "message": f"{key} must remain False.",
                }
            )

    true_keys = [
        "public_records_can_support_parcel_context",
        "public_records_can_support_tax_context",
        "public_records_can_support_deed_references",
        "public_records_can_support_sale_references",
        "public_records_can_support_gis_context",
        "public_records_can_support_modiv_context",
        "public_records_cannot_prove_current_listing_status",
        "public_records_cannot_prove_current_listing_price",
        "public_records_cannot_prove_under_contract_status",
        "source_attribution_required",
        "confidence_required",
        "manual_review_required_for_conflicts",
        "unavailable_fields_must_be_labeled",
    ]

    for key in true_keys:
        if not PROPERTY_PROFILE_GOVERNANCE.get(key):
            issues.append(
                {
                    "issue_code": f"{key}_must_remain_true",
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


def get_property_profile_engine_metadata() -> dict[str, Any]:
    return {
        "name": PROPERTY_PROFILE_ENGINE_NAME,
        "version": PROPERTY_PROFILE_ENGINE_VERSION,
        "phase": PROPERTY_PROFILE_ENGINE_PHASE,
        "status": PROPERTY_PROFILE_ENGINE_STATUS,
        "release_channel": PROPERTY_PROFILE_RELEASE_CHANNEL,
        "generated_at": utc_now(),
    }


def get_property_profile_engine_health() -> dict[str, Any]:
    governance = validate_property_profile_governance()

    sample_result = build_property_profile(
        "43 Wetmore Ave, Morristown, NJ 07960",
        include_public_records=False,
    )

    return {
        "name": PROPERTY_PROFILE_ENGINE_NAME,
        "version": PROPERTY_PROFILE_ENGINE_VERSION,
        "phase": PROPERTY_PROFILE_ENGINE_PHASE,
        "status": PROPERTY_PROFILE_ENGINE_STATUS,
        "governance_valid": governance["valid"],
        "governance_issue_count": governance["issue_count"],
        "address_intelligence_available": analyze_address is not None,
        "public_records_engine_available": PublicRecordsEngine is not None,
        "confidence_engine_available": ConfidenceEngine is not None,
        "source_explanation_engine_available": SourceExplanationEngine is not None,
        "sample_success": sample_result.success,
        "sample_profile_status": sample_result.profile.status,
        "sample_canonical_address": sample_result.profile.canonical_address,
        "sample_confidence": sample_result.profile.confidence_report.overall_confidence,
        "mock_property_facts_allowed": False,
        "fabricated_listing_status_allowed": False,
        "fabricated_property_values_allowed": False,
        "generated_at": utc_now(),
    }


def get_property_profile_engine_readiness() -> dict[str, Any]:
    health = get_property_profile_engine_health()

    required = {
        "address_intelligence_available": health["address_intelligence_available"],
        "governance_valid": health["governance_valid"],
        "sample_success": health["sample_success"],
    }

    optional = {
        "public_records_engine_available": health["public_records_engine_available"],
        "confidence_engine_available": health["confidence_engine_available"],
        "source_explanation_engine_available": health["source_explanation_engine_available"],
    }

    return {
        "ready": all(required.values()),
        "required": required,
        "optional": optional,
        "missing_required": [
            key
            for key, value in required.items()
            if not value
        ],
        "missing_optional": [
            key
            for key, value in optional.items()
            if not value
        ],
        "next_required_files": [
            "app/property_intelligence/confidence_engine.py",
            "app/property_intelligence/source_explanation_engine.py",
            "app/web/property_routes.py",
            "app/public_records/public_records_engine.py",
        ],
        "generated_at": utc_now(),
    }


def get_property_profile_engine_diagnostics() -> dict[str, Any]:
    return {
        "metadata": get_property_profile_engine_metadata(),
        "health": get_property_profile_engine_health(),
        "readiness": get_property_profile_engine_readiness(),
        "governance": PROPERTY_PROFILE_GOVERNANCE.copy(),
        "governance_validation": validate_property_profile_governance(),
        "public_record_supported_domains": PUBLIC_RECORD_SUPPORTED_DOMAINS,
        "authorized_feed_required_domains": AUTHORIZED_FEED_REQUIRED_DOMAINS,
        "valuation_required_domains": VALUATION_REQUIRED_DOMAINS,
        "profile_required_fields": PROFILE_REQUIRED_FIELDS,
        "exports": __all__,
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 22 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "PROPERTY_PROFILE_ENGINE_NAME",
    "PROPERTY_PROFILE_ENGINE_VERSION",
    "PROPERTY_PROFILE_ENGINE_PHASE",
    "PROPERTY_PROFILE_ENGINE_STATUS",
    "PROPERTY_PROFILE_RELEASE_CHANNEL",
    "PROPERTY_PROFILE_GOVERNANCE",
    "PUBLIC_RECORD_SUPPORTED_DOMAINS",
    "AUTHORIZED_FEED_REQUIRED_DOMAINS",
    "VALUATION_REQUIRED_DOMAINS",
    "PROFILE_REQUIRED_FIELDS",
    "PropertyProfileStatus",
    "PropertyFactStatus",
    "PropertySourceType",
    "ValuationReadinessStatus",
    "ListingStatusReadiness",
    "ManualReviewSeverity",
    "PropertyProfileRequest",
    "SourceReference",
    "PropertyFact",
    "ParcelIdentity",
    "TaxAssessmentContext",
    "PropertyTaxContext",
    "SaleHistoryReference",
    "CountyClerkReference",
    "OwnerReference",
    "GISContext",
    "MODIVContext",
    "BuildingFacts",
    "ListingStatusContext",
    "ValuationReadiness",
    "UnavailableField",
    "ManualReviewItem",
    "ConfidenceReport",
    "SourceExplanationReport",
    "PropertyProfile",
    "PropertyProfileResult",
    "PropertyProfileResponse",
    "PropertyIntelligenceProfile",
    "PropertyProfileRequestFactory",
    "SourceReferenceBuilder",
    "PublicRecordsAdapter",
    "PublicRecordFactExtractor",
    "PropertyFactBuilder",
    "UnavailableFieldBuilder",
    "ManualReviewBuilder",
    "ProfileConfidenceBuilder",
    "ProfileSourceExplanationBuilder",
    "ValuationReadinessBuilder",
    "PropertyProfileStatusResolver",
    "PropertyProfileEngine",
    "PropertyProfileBuilder",
    "build_property_profile",
    "build_property_profile_dict",
    "build_profile",
    "create_property_profile",
    "profile_to_public_api_payload",
    "validate_property_profile_governance",
    "get_property_profile_engine_metadata",
    "get_property_profile_engine_health",
    "get_property_profile_engine_readiness",
    "get_property_profile_engine_diagnostics",
]


# ============================================================
# END OF FILE
# ============================================================