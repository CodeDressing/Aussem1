# ============================================================
# AUSSEM1
# PHASE 2.44 PART 1.00
# ENTERPRISE SOURCE EXPLANATION ENGINE
# FILE: app/property_intelligence/source_explanation_engine.py
# PURPOSE:
# Explain what each source supports, what each source cannot prove,
# what data remains unavailable, what future source is required,
# and which property facts require manual review.
#
# THIS ENGINE EXPLAINS:
# - why public records support parcel / tax / deed / GIS / MOD-IV context
# - why public records cannot prove active listing status
# - why public records cannot prove under-contract status
# - why assessment is not market value
# - why valuation may be unavailable
# - what future source is required
# - which facts require manual review
#
# CORE GOVERNANCE:
# - Does not fabricate facts.
# - Does not fabricate source support.
# - Does not turn assessment into market value.
# - Does not claim listing status without an authorized feed.
# - Does not claim valuation without valuation inputs.
# - Clearly separates supported, unsupported, unavailable, and review-required claims.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# ENTERPRISE SOURCE EXPLANATION ENGINE ACTIVE
# ============================================================


from __future__ import annotations

# ============================================================
# SECTION 01 - STANDARD LIBRARY IMPORTS
# ============================================================

import hashlib
import json
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from enum import StrEnum
from typing import Any
from typing import Mapping
from typing import Sequence


# ============================================================
# SECTION 02 - MODULE METADATA
# ============================================================

SOURCE_EXPLANATION_ENGINE_NAME = (
    "Aussem1 Enterprise Source Explanation Engine"
)

SOURCE_EXPLANATION_ENGINE_VERSION = "0.2.0"

SOURCE_EXPLANATION_ENGINE_PHASE = "PHASE 2.44 PART 1.00"

SOURCE_EXPLANATION_ENGINE_STATUS = (
    "enterprise_source_explanation_engine_active"
)

SOURCE_EXPLANATION_RELEASE_CHANNEL = "development"


# ============================================================
# SECTION 03 - SOURCE GOVERNANCE
# ============================================================

SOURCE_EXPLANATION_GOVERNANCE = {
    "fabricated_source_support_allowed": False,
    "fabricated_property_facts_allowed": False,
    "fabricated_listing_status_allowed": False,
    "fabricated_market_value_allowed": False,
    "assessment_as_market_value_allowed": False,
    "public_records_as_listing_feed_allowed": False,
    "manual_review_disclosure_required": True,
    "unsupported_claims_must_be_labeled": True,
    "unavailable_fields_must_be_labeled": True,
    "future_required_sources_must_be_named": True,
    "source_limitations_must_be_explained": True,
    "confidence_context_required": True,
}


PUBLIC_RECORD_SUPPORTED_CLAIMS = {
    "address_identity": (
        "Public records can support address identity when the address appears "
        "in tax, parcel, GIS, MOD-IV, deed, or municipal records."
    ),
    "parcel_identity": (
        "Public records can support parcel identity through block, lot, qualifier, "
        "parcel ID, municipality, county, and state references."
    ),
    "tax_assessment": (
        "Public records can support tax assessment context such as land assessment, "
        "improvement assessment, total assessment, tax year, and property class."
    ),
    "property_tax_context": (
        "Public records can support property tax context when tax amount, tax rate, "
        "tax year, or municipal tax fields are available."
    ),
    "deed_references": (
        "County clerk and recorded-document sources can support deed references, "
        "book/page, document number, recorded date, party references, and sale-history context."
    ),
    "mortgage_references": (
        "County clerk records may support mortgage references when those documents "
        "are available from the public document source."
    ),
    "lien_references": (
        "County clerk records may support lien references when those documents "
        "are available from the public document source."
    ),
    "owner_references": (
        "Tax and public-record sources may support owner references, but owner data "
        "should be treated as public-record context and may require manual review."
    ),
    "sale_history_references": (
        "Public records can support historical sale references when deed, tax, "
        "or recorded-document data provides date, consideration, buyer/seller reference, "
        "book/page, or document number."
    ),
    "gis_context": (
        "County GIS sources can support parcel map context, geometry references, "
        "lot-size context, and location context, but GIS is not a legal boundary survey."
    ),
    "modiv_context": (
        "NJ MOD-IV style public-record context can support assessment and property "
        "classification fields when available."
    ),
    "building_facts_when_source_backed": (
        "Building facts can be presented only when a public record or authorized "
        "source provides them. Missing building facts must remain unavailable."
    ),
}


PUBLIC_RECORD_UNSUPPORTED_CLAIMS = {
    "active_listing_status": (
        "Public records alone cannot prove whether a property is currently active "
        "on the market."
    ),
    "under_contract_status": (
        "Public records alone cannot prove whether a property is currently under "
        "contract."
    ),
    "pending_status": (
        "Public records alone cannot prove whether a property is currently pending."
    ),
    "current_listing_price": (
        "Public records alone cannot prove current listing price."
    ),
    "current_days_on_market": (
        "Public records alone cannot prove current days on market."
    ),
    "showing_availability": (
        "Public records alone cannot prove showing availability."
    ),
    "offer_deadline": (
        "Public records alone cannot prove current offer deadline."
    ),
    "broker_confirmation": (
        "Public records alone cannot replace broker confirmation."
    ),
    "current_mls_status": (
        "Public records alone cannot prove current MLS status."
    ),
    "market_value_estimate": (
        "Public records alone do not produce market value. A valuation engine, "
        "comparable-sales data, feature extraction, and confidence calibration are required."
    ),
}


FUTURE_REQUIRED_SOURCES = {
    "active_listing_status": "authorized MLS / RESO / IDX / broker-authorized listing feed",
    "under_contract_status": "authorized MLS / RESO / IDX / broker-authorized listing feed",
    "pending_status": "authorized MLS / RESO / IDX / broker-authorized listing feed",
    "current_listing_price": "authorized MLS / RESO / IDX / broker-authorized listing feed",
    "current_days_on_market": "authorized MLS / RESO / IDX / broker-authorized listing feed",
    "showing_availability": "authorized listing feed or broker confirmation",
    "offer_deadline": "authorized listing feed or broker confirmation",
    "broker_confirmation": "broker-authorized source",
    "current_mls_status": "authorized MLS / RESO / IDX feed",
    "market_value_estimate": "valuation engine and comparable-sales dataset",
    "confidence_band": "valuation engine and confidence calibration model",
    "comparable_sales_adjustment": "comparable-sales source and valuation feature builder",
    "appreciation_forecast": "market trend model and historical sales dataset",
}


STANDARD_SOURCE_LIMITATIONS = [
    "Tax assessment is not current market value.",
    "GIS parcel context is not a legal boundary survey.",
    "Public records may lag current listing, contract, or closing activity.",
    "County clerk records may require manual review to interpret parties and document type.",
    "Owner references from public records should be treated as administrative context, not a legal title opinion.",
    "Public records cannot replace an authorized MLS, RESO, IDX, broker, or listing-provider feed for current listing status.",
    "Valuation requires comparable sales, source-backed features, model metadata, and confidence calibration.",
]


# ============================================================
# SECTION 04 - ENUMERATIONS
# ============================================================

class ClaimSupportStatus(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNAVAILABLE = "unavailable"
    PARTIAL = "partial"
    REQUIRES_AUTHORIZED_SOURCE = "requires_authorized_source"
    REQUIRES_MANUAL_REVIEW = "requires_manual_review"
    REQUIRES_VALUATION_ENGINE = "requires_valuation_engine"


class ExplanationSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SourceCategory(StrEnum):
    ADDRESS_INTELLIGENCE = "address_intelligence"
    PUBLIC_RECORD = "public_record"
    TAX_BOARD = "tax_board"
    COUNTY_CLERK = "county_clerk"
    GIS = "gis"
    MODIV = "modiv"
    AUTHORIZED_LISTING_FEED = "authorized_listing_feed"
    VALUATION_ENGINE = "valuation_engine"
    COMPARABLE_SALES = "comparable_sales"
    MANUAL_REVIEW = "manual_review"
    UNKNOWN = "unknown"


class RequiredSourceType(StrEnum):
    PUBLIC_RECORDS = "public_records"
    COUNTY_TAX_BOARD = "county_tax_board"
    COUNTY_CLERK = "county_clerk"
    COUNTY_GIS = "county_gis"
    NJ_STATE_MODIV = "nj_state_modiv"
    AUTHORIZED_LISTING_FEED = "authorized_listing_feed"
    BROKER_CONFIRMATION = "broker_confirmation"
    VALUATION_ENGINE = "valuation_engine"
    COMPARABLE_SALES = "comparable_sales"
    MANUAL_REVIEW = "manual_review"


# ============================================================
# SECTION 05 - UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def safe_string(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def normalize_key(value: Any) -> str:
    text = safe_string(value).lower()
    output: list[str] = []

    for character in text:
        if character.isalnum():
            output.append(character)
        elif output and output[-1] != "_":
            output.append("_")

    return "".join(output).strip("_")


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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

        if found and current not in (None, "", [], {}):
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


def clamp_confidence(value: Any) -> float:
    try:
        number = float(value)
    except Exception:
        return 0.0

    return max(0.0, min(1.0, number))


# ============================================================
# SECTION 06 - DATA CONTRACTS
# ============================================================

@dataclass
class SourceCapability:
    source_category: str
    can_support: list[str] = field(default_factory=list)
    cannot_support: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    required_future_sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class ClaimExplanation:
    claim: str
    status: str
    explanation: str
    can_public_records_support: bool = False
    required_source: str | None = None
    source_names: list[str] = field(default_factory=list)
    confidence: float = 0.0
    severity: str = ExplanationSeverity.INFO.value
    manual_review_required: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class SourceExplanation:
    source_name: str
    source_category: str
    source_authority: str = "unknown"
    supported_claims: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    retrieved_at: str | None = None
    record_id: str | None = None
    source_url: str | None = None
    raw_payload_hash: str | None = None
    explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class UnavailableDataExplanation:
    field_name: str
    field_path: str
    reason: str
    required_source: str | None = None
    can_public_records_support: bool = False
    manual_review_required: bool = False
    severity: str = ExplanationSeverity.INFO.value
    explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class ManualReviewExplanation:
    code: str
    message: str
    severity: str = ExplanationSeverity.WARNING.value
    field_path: str | None = None
    required_action: str | None = None
    why_review_is_needed: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class AssessmentExplanation:
    has_assessment: bool
    total_assessment: float | None = None
    land_assessment: float | None = None
    improvement_assessment: float | None = None
    tax_year: str | None = None
    explanation: str = (
        "Tax assessment is public-record context and is not current market value."
    )
    cannot_be_used_as_market_value: bool = True
    valuation_required_source: str = "valuation_engine_and_comparable_sales"

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class ListingStatusExplanation:
    listing_feed_connected: bool = False
    active_status_supported: bool = False
    under_contract_supported: bool = False
    current_price_supported: bool = False
    explanation: str = (
        "Current listing status requires an authorized MLS, RESO, IDX, "
        "broker-authorized feed, or listing-provider source."
    )
    required_source: str = "authorized_listing_feed"

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class ValuationExplanation:
    valuation_available: bool = False
    estimate_allowed: bool = False
    valuation_readiness_status: str = "not_ready"
    available_inputs: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    explanation: str = (
        "Valuation is unavailable until source-backed property facts, "
        "comparable sales, valuation logic, and confidence metadata are available."
    )
    required_source: str = "valuation_engine_and_comparable_sales"

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class SourceExplanationReport:
    summary: str
    supported_claims: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    unavailable_claims: list[str] = field(default_factory=list)
    public_record_limitations: list[str] = field(default_factory=list)
    required_future_sources: list[str] = field(default_factory=list)
    source_notes: list[str] = field(default_factory=list)
    claim_explanations: list[ClaimExplanation] = field(default_factory=list)
    source_explanations: list[SourceExplanation] = field(default_factory=list)
    unavailable_data: list[UnavailableDataExplanation] = field(default_factory=list)
    manual_review_explanations: list[ManualReviewExplanation] = field(default_factory=list)
    assessment_explanation: AssessmentExplanation | None = None
    listing_status_explanation: ListingStatusExplanation | None = None
    valuation_explanation: ValuationExplanation | None = None
    confidence_context: dict[str, Any] = field(default_factory=dict)
    governance: dict[str, Any] = field(default_factory=dict)
    report_id: str | None = None
    created_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


# Backward-compatible aliases.
PropertySourceExplanationReport = SourceExplanationReport
SourceExplanationResult = SourceExplanationReport


# ============================================================
# SECTION 07 - SOURCE CAPABILITY REGISTRY
# ============================================================

class SourceCapabilityRegistry:
    def __init__(self) -> None:
        self.capabilities = self.build_default_capabilities()

    @staticmethod
    def build_default_capabilities() -> dict[str, SourceCapability]:
        return {
            SourceCategory.ADDRESS_INTELLIGENCE.value: SourceCapability(
                source_category=SourceCategory.ADDRESS_INTELLIGENCE.value,
                can_support=[
                    "address_normalization",
                    "address_parse",
                    "jurisdiction_detection",
                    "public_record_search_preparation",
                ],
                cannot_support=[
                    "parcel_fact_proof",
                    "active_listing_status",
                    "market_value",
                    "owner_legal_conclusion",
                ],
                limitations=[
                    "Address intelligence prepares lookup input and does not prove property facts by itself.",
                ],
                required_future_sources=[
                    "public_records",
                    "authorized_listing_feed",
                    "valuation_engine",
                ],
            ),
            SourceCategory.TAX_BOARD.value: SourceCapability(
                source_category=SourceCategory.TAX_BOARD.value,
                can_support=[
                    "parcel_identity",
                    "block_lot",
                    "tax_assessment",
                    "property_class",
                    "owner_reference",
                    "tax_context",
                ],
                cannot_support=[
                    "active_listing_status",
                    "under_contract_status",
                    "current_listing_price",
                    "market_value_estimate",
                ],
                limitations=[
                    "Tax assessment is not current market value.",
                    "Tax data may lag ownership or transaction changes.",
                ],
                required_future_sources=[
                    "authorized_listing_feed",
                    "valuation_engine",
                    "comparable_sales",
                ],
            ),
            SourceCategory.COUNTY_CLERK.value: SourceCapability(
                source_category=SourceCategory.COUNTY_CLERK.value,
                can_support=[
                    "deed_references",
                    "mortgage_references",
                    "lien_references",
                    "recorded_documents",
                    "sale_history_references",
                ],
                cannot_support=[
                    "active_listing_status",
                    "under_contract_status",
                    "current_listing_price",
                    "market_value_estimate",
                ],
                limitations=[
                    "Recorded documents may require manual interpretation.",
                    "Recorded documents may lag current transaction status.",
                ],
                required_future_sources=[
                    "authorized_listing_feed",
                    "broker_confirmation",
                    "valuation_engine",
                ],
            ),
            SourceCategory.GIS.value: SourceCapability(
                source_category=SourceCategory.GIS.value,
                can_support=[
                    "parcel_map_context",
                    "geometry_reference",
                    "lot_size_context",
                    "location_context",
                ],
                cannot_support=[
                    "legal_boundary_survey",
                    "title_opinion",
                    "active_listing_status",
                    "market_value_estimate",
                ],
                limitations=[
                    "GIS context is not a legal survey.",
                    "GIS geometry can differ from legal boundary records.",
                ],
                required_future_sources=[
                    "survey",
                    "title_source",
                    "valuation_engine",
                ],
            ),
            SourceCategory.MODIV.value: SourceCapability(
                source_category=SourceCategory.MODIV.value,
                can_support=[
                    "assessment_context",
                    "property_class",
                    "land_description",
                    "building_description_when_available",
                ],
                cannot_support=[
                    "active_listing_status",
                    "under_contract_status",
                    "current_listing_price",
                    "market_value_estimate",
                ],
                limitations=[
                    "MOD-IV context is administrative assessment data.",
                    "MOD-IV is not a listing feed or market valuation model.",
                ],
                required_future_sources=[
                    "authorized_listing_feed",
                    "valuation_engine",
                    "comparable_sales",
                ],
            ),
            SourceCategory.AUTHORIZED_LISTING_FEED.value: SourceCapability(
                source_category=SourceCategory.AUTHORIZED_LISTING_FEED.value,
                can_support=[
                    "active_listing_status",
                    "under_contract_status",
                    "pending_status",
                    "current_listing_price",
                    "days_on_market",
                    "showing_availability_when_provided",
                    "mls_status",
                ],
                cannot_support=[
                    "legal_title_opinion",
                    "tax_assessment_truth",
                    "survey_boundary",
                ],
                limitations=[
                    "Listing feeds must be authorized and current.",
                    "Listing data must respect feed license and attribution requirements.",
                ],
                required_future_sources=[
                    "public_records",
                    "valuation_engine",
                    "broker_confirmation_when_needed",
                ],
            ),
            SourceCategory.VALUATION_ENGINE.value: SourceCapability(
                source_category=SourceCategory.VALUATION_ENGINE.value,
                can_support=[
                    "market_value_estimate",
                    "confidence_band",
                    "estimate_low_high",
                    "feature_based_valuation",
                ],
                cannot_support=[
                    "guaranteed_sale_price",
                    "appraisal_certification",
                    "legal_value_conclusion",
                ],
                limitations=[
                    "Valuation is an estimate, not an appraisal.",
                    "Valuation requires source-backed inputs and comparable-sales support.",
                ],
                required_future_sources=[
                    "comparable_sales",
                    "public_records",
                    "listing_feed_when_available",
                ],
            ),
        }

    def get(self, category: str) -> SourceCapability:
        normalized = normalize_key(category)

        if normalized in self.capabilities:
            return self.capabilities[normalized]

        return SourceCapability(
            source_category=SourceCategory.UNKNOWN.value,
            can_support=[],
            cannot_support=[
                "active_listing_status",
                "market_value_estimate",
                "legal_conclusions",
            ],
            limitations=[
                "Unknown source category cannot be treated as authoritative."
            ],
            required_future_sources=[
                "manual_review",
                "source_classification",
            ],
        )


# ============================================================
# SECTION 08 - CLAIM CLASSIFIER
# ============================================================

class ClaimClassifier:
    def classify_claim(
        self,
        claim: str,
    ) -> tuple[str, bool, str | None, str]:
        key = normalize_key(claim)

        if key in PUBLIC_RECORD_SUPPORTED_CLAIMS:
            return (
                ClaimSupportStatus.SUPPORTED.value,
                True,
                RequiredSourceType.PUBLIC_RECORDS.value,
                PUBLIC_RECORD_SUPPORTED_CLAIMS[key],
            )

        if key in PUBLIC_RECORD_UNSUPPORTED_CLAIMS:
            required = FUTURE_REQUIRED_SOURCES.get(key)

            if "valuation" in key or "market_value" in key:
                status = ClaimSupportStatus.REQUIRES_VALUATION_ENGINE.value
            else:
                status = ClaimSupportStatus.REQUIRES_AUTHORIZED_SOURCE.value

            return (
                status,
                False,
                required,
                PUBLIC_RECORD_UNSUPPORTED_CLAIMS[key],
            )

        if any(field in key for field in ["listing", "mls", "under_contract", "pending"]):
            return (
                ClaimSupportStatus.REQUIRES_AUTHORIZED_SOURCE.value,
                False,
                RequiredSourceType.AUTHORIZED_LISTING_FEED.value,
                "This claim requires an authorized listing source and cannot be proven by public records alone.",
            )

        if any(field in key for field in ["value", "valuation", "estimate", "price_forecast"]):
            return (
                ClaimSupportStatus.REQUIRES_VALUATION_ENGINE.value,
                False,
                RequiredSourceType.VALUATION_ENGINE.value,
                "This claim requires valuation logic, comparable sales, source-backed inputs, and confidence metadata.",
            )

        return (
            ClaimSupportStatus.PARTIAL.value,
            False,
            RequiredSourceType.MANUAL_REVIEW.value,
            "This claim requires source classification or manual review before support can be determined.",
        )


# ============================================================
# SECTION 09 - SOURCE EXTRACTOR
# ============================================================

class SourceExtractor:
    def extract_sources(self, profile_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
        sources: list[dict[str, Any]] = []

        self.extract_from_facts(profile_payload, sources)
        self.extract_from_sections(profile_payload, sources)
        self.extract_from_raw_public_records(profile_payload, sources)

        return self.deduplicate_sources(sources)

    def extract_from_facts(
        self,
        profile_payload: Mapping[str, Any],
        sources: list[dict[str, Any]],
    ) -> None:
        facts = profile_payload.get("facts") or []

        if not isinstance(facts, Sequence) or isinstance(facts, (str, bytes)):
            return

        for fact in facts:
            fact_payload = object_to_dict(fact)

            if not isinstance(fact_payload, Mapping):
                continue

            for source in fact_payload.get("source_references") or []:
                source_payload = object_to_dict(source)

                if isinstance(source_payload, Mapping):
                    sources.append(dict(source_payload))

    def extract_from_sections(
        self,
        profile_payload: Mapping[str, Any],
        sources: list[dict[str, Any]],
    ) -> None:
        section_names = [
            "parcel_identity",
            "tax_assessment_context",
            "property_tax_context",
            "gis_context",
            "modiv_context",
            "building_facts",
            "owner_references",
            "sale_history_references",
            "county_clerk_references",
        ]

        for section_name in section_names:
            section = profile_payload.get(section_name)

            if isinstance(section, Mapping):
                for source in section.get("sources") or []:
                    source_payload = object_to_dict(source)

                    if isinstance(source_payload, Mapping):
                        sources.append(dict(source_payload))

            if isinstance(section, Sequence) and not isinstance(section, (str, bytes)):
                for item in section:
                    item_payload = object_to_dict(item)

                    if not isinstance(item_payload, Mapping):
                        continue

                    for source in item_payload.get("sources") or []:
                        source_payload = object_to_dict(source)

                        if isinstance(source_payload, Mapping):
                            sources.append(dict(source_payload))

    def extract_from_raw_public_records(
        self,
        profile_payload: Mapping[str, Any],
        sources: list[dict[str, Any]],
    ) -> None:
        raw = profile_payload.get("raw_public_record_payload") or {}

        if not isinstance(raw, Mapping):
            return

        for source in raw.get("sources") or []:
            source_payload = object_to_dict(source)

            if isinstance(source_payload, Mapping):
                sources.append(dict(source_payload))

    @staticmethod
    def deduplicate_sources(
        sources: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        seen: set[str] = set()
        result: list[dict[str, Any]] = []

        for source in sources:
            key = stable_hash(source)

            if key in seen:
                continue

            seen.add(key)
            result.append(source)

        return result


# ============================================================
# SECTION 10 - SOURCE EXPLANATION BUILDER
# ============================================================

class SourceExplanationBuilder:
    def __init__(
        self,
        capability_registry: SourceCapabilityRegistry | None = None,
    ) -> None:
        self.capability_registry = capability_registry or SourceCapabilityRegistry()

    def build_source_explanations(
        self,
        sources: Sequence[Mapping[str, Any]],
    ) -> list[SourceExplanation]:
        explanations: list[SourceExplanation] = []

        for source in sources:
            source_category = self.classify_source_category(source)
            capability = self.capability_registry.get(source_category)
            source_name = safe_string(
                source.get("source_name")
                or source.get("name")
                or source.get("connector_name")
                or source.get("connector")
                or source_category
            )
            confidence = clamp_confidence(source.get("confidence") or 0.0)

            explanation = (
                f"{source_name} can support {', '.join(capability.can_support) or 'classified source facts'}; "
                f"it cannot support {', '.join(capability.cannot_support) or 'unsupported claims'}."
            )

            explanations.append(
                SourceExplanation(
                    source_name=source_name,
                    source_category=source_category,
                    source_authority=safe_string(
                        source.get("source_authority")
                        or source.get("authority")
                        or "unknown"
                    ),
                    supported_claims=capability.can_support,
                    unsupported_claims=capability.cannot_support,
                    limitations=capability.limitations,
                    confidence=confidence,
                    retrieved_at=source.get("retrieved_at"),
                    record_id=source.get("record_id") or source.get("id"),
                    source_url=source.get("source_url") or source.get("url"),
                    raw_payload_hash=source.get("raw_payload_hash")
                    or stable_hash(source),
                    explanation=explanation,
                    metadata={
                        "required_future_sources": capability.required_future_sources,
                    },
                )
            )

        return explanations

    @staticmethod
    def classify_source_category(source: Mapping[str, Any]) -> str:
        source_type = normalize_key(
            source.get("source_type")
            or source.get("type")
            or source.get("connector_name")
            or source.get("connector")
            or source.get("source_name")
        )

        if "address" in source_type:
            return SourceCategory.ADDRESS_INTELLIGENCE.value

        if "tax" in source_type:
            return SourceCategory.TAX_BOARD.value

        if "clerk" in source_type or "deed" in source_type or "document" in source_type:
            return SourceCategory.COUNTY_CLERK.value

        if "gis" in source_type:
            return SourceCategory.GIS.value

        if "modiv" in source_type:
            return SourceCategory.MODIV.value

        if source_type in {"mls", "reso", "idx", "broker_feed", "authorized_listing_feed"}:
            return SourceCategory.AUTHORIZED_LISTING_FEED.value

        if "valuation" in source_type:
            return SourceCategory.VALUATION_ENGINE.value

        if "public" in source_type:
            return SourceCategory.PUBLIC_RECORD.value

        return SourceCategory.UNKNOWN.value


# ============================================================
# SECTION 11 - CLAIM EXPLANATION BUILDER
# ============================================================

class ClaimExplanationBuilder:
    def __init__(
        self,
        classifier: ClaimClassifier | None = None,
    ) -> None:
        self.classifier = classifier or ClaimClassifier()

    def build_claim_explanations(
        self,
        profile_payload: Mapping[str, Any],
        source_explanations: Sequence[SourceExplanation],
    ) -> list[ClaimExplanation]:
        claims = self.collect_claims(profile_payload)

        explanations: list[ClaimExplanation] = []

        available_source_names = [
            source.source_name
            for source in source_explanations
        ]

        for claim in claims:
            status, public_support, required_source, explanation = (
                self.classifier.classify_claim(claim)
            )

            explanations.append(
                ClaimExplanation(
                    claim=claim,
                    status=status,
                    explanation=explanation,
                    can_public_records_support=public_support,
                    required_source=required_source,
                    source_names=available_source_names if public_support else [],
                    confidence=self.claim_confidence(
                        claim,
                        profile_payload,
                        public_support=public_support,
                    ),
                    severity=self.claim_severity(status),
                    manual_review_required=(
                        status
                        in {
                            ClaimSupportStatus.REQUIRES_MANUAL_REVIEW.value,
                            ClaimSupportStatus.PARTIAL.value,
                        }
                    ),
                )
            )

        return explanations

    @staticmethod
    def collect_claims(profile_payload: Mapping[str, Any]) -> list[str]:
        claims = list(PUBLIC_RECORD_SUPPORTED_CLAIMS.keys())
        claims.extend(PUBLIC_RECORD_UNSUPPORTED_CLAIMS.keys())

        facts = profile_payload.get("facts") or []

        if isinstance(facts, Sequence) and not isinstance(facts, (str, bytes)):
            for fact in facts:
                fact_payload = object_to_dict(fact)

                if isinstance(fact_payload, Mapping):
                    field_name = safe_string(
                        fact_payload.get("field_name")
                        or fact_payload.get("field_path")
                    )

                    if field_name:
                        claims.append(normalize_key(field_name))

        return list(dict.fromkeys(claims))

    @staticmethod
    def claim_confidence(
        claim: str,
        profile_payload: Mapping[str, Any],
        *,
        public_support: bool,
    ) -> float:
        if not public_support:
            return 0.0

        flattened = flatten_mapping(profile_payload)
        claim_key = normalize_key(claim)

        for key, value in flattened.items():
            if claim_key in normalize_key(key) and value not in (None, "", [], {}):
                return 0.70

        return 0.25

    @staticmethod
    def claim_severity(status: str) -> str:
        if status in {
            ClaimSupportStatus.UNSUPPORTED.value,
            ClaimSupportStatus.REQUIRES_AUTHORIZED_SOURCE.value,
            ClaimSupportStatus.REQUIRES_VALUATION_ENGINE.value,
        }:
            return ExplanationSeverity.WARNING.value

        if status == ClaimSupportStatus.UNAVAILABLE.value:
            return ExplanationSeverity.INFO.value

        if status == ClaimSupportStatus.REQUIRES_MANUAL_REVIEW.value:
            return ExplanationSeverity.WARNING.value

        return ExplanationSeverity.INFO.value


# ============================================================
# SECTION 12 - UNAVAILABLE DATA EXPLANATION BUILDER
# ============================================================

class UnavailableDataExplanationBuilder:
    def build(
        self,
        profile_payload: Mapping[str, Any],
    ) -> list[UnavailableDataExplanation]:
        unavailable = []

        unavailable.extend(self.from_unavailable_fields(profile_payload))
        unavailable.extend(self.from_required_listing_fields(profile_payload))
        unavailable.extend(self.from_required_valuation_fields(profile_payload))

        return self.deduplicate(unavailable)

    def from_unavailable_fields(
        self,
        profile_payload: Mapping[str, Any],
    ) -> list[UnavailableDataExplanation]:
        fields = profile_payload.get("unavailable_fields") or []
        results: list[UnavailableDataExplanation] = []

        if not isinstance(fields, Sequence) or isinstance(fields, (str, bytes)):
            return results

        for field_item in fields:
            payload = object_to_dict(field_item)

            if not isinstance(payload, Mapping):
                continue

            field_name = safe_string(payload.get("field_name") or "unknown_field")
            field_path = safe_string(payload.get("field_path") or field_name)
            required_source = payload.get("required_source")

            results.append(
                UnavailableDataExplanation(
                    field_name=field_name,
                    field_path=field_path,
                    reason=safe_string(
                        payload.get("reason")
                        or "Field is unavailable from current source set."
                    ),
                    required_source=required_source,
                    can_public_records_support=bool(
                        payload.get("can_public_records_support", False)
                    ),
                    manual_review_required=bool(
                        payload.get("manual_review_required", False)
                    ),
                    severity=safe_string(
                        payload.get("severity") or ExplanationSeverity.INFO.value
                    ),
                    explanation=self.explain_unavailable_field(
                        field_path,
                        required_source,
                    ),
                    metadata=dict(payload.get("metadata") or {}),
                )
            )

        return results

    def from_required_listing_fields(
        self,
        profile_payload: Mapping[str, Any],
    ) -> list[UnavailableDataExplanation]:
        results: list[UnavailableDataExplanation] = []

        for field_name, explanation in PUBLIC_RECORD_UNSUPPORTED_CLAIMS.items():
            if field_name not in FUTURE_REQUIRED_SOURCES:
                continue

            if "listing" not in field_name and "contract" not in field_name and "pending" not in field_name and "mls" not in field_name:
                continue

            results.append(
                UnavailableDataExplanation(
                    field_name=field_name,
                    field_path=f"listing.{field_name}",
                    reason=explanation,
                    required_source=FUTURE_REQUIRED_SOURCES.get(field_name),
                    can_public_records_support=False,
                    manual_review_required=False,
                    severity=ExplanationSeverity.WARNING.value,
                    explanation=(
                        f"{field_name} cannot be produced from public records alone. "
                        f"Required source: {FUTURE_REQUIRED_SOURCES.get(field_name)}."
                    ),
                )
            )

        return results

    def from_required_valuation_fields(
        self,
        profile_payload: Mapping[str, Any],
    ) -> list[UnavailableDataExplanation]:
        valuation = profile_payload.get("valuation_readiness") or {}

        if not isinstance(valuation, Mapping):
            valuation = {}

        if valuation.get("ready") is True and valuation.get("estimate_allowed") is True:
            return []

        fields = [
            "market_value_estimate",
            "estimate_low",
            "estimate_high",
            "confidence_band",
            "comparable_sales_adjustment",
        ]

        results = []

        for field_name in fields:
            results.append(
                UnavailableDataExplanation(
                    field_name=field_name,
                    field_path=f"valuation.{field_name}",
                    reason=(
                        "Valuation output is unavailable until valuation inputs, "
                        "comparable sales, model logic, and confidence calibration are connected."
                    ),
                    required_source="valuation_engine_and_comparable_sales",
                    can_public_records_support=False,
                    manual_review_required=False,
                    severity=ExplanationSeverity.WARNING.value,
                    explanation=(
                        "Aussem1 must not fabricate valuation output. "
                        "The system can explain valuation readiness but cannot produce "
                        "market value without the valuation engine and comparable-sales data."
                    ),
                )
            )

        return results

    @staticmethod
    def explain_unavailable_field(
        field_path: str,
        required_source: Any,
    ) -> str:
        field_key = normalize_key(field_path)

        if "listing" in field_key or "mls" in field_key:
            return (
                f"{field_path} requires an authorized listing feed. "
                "Public records cannot prove current listing status."
            )

        if "valuation" in field_key or "estimate" in field_key:
            return (
                f"{field_path} requires valuation logic and comparable-sales data. "
                "Assessment cannot be treated as market value."
            )

        if "tax" in field_key or "assessment" in field_key:
            return (
                f"{field_path} requires tax-board or assessment public records."
            )

        if "gis" in field_key:
            return (
                f"{field_path} requires GIS source context. GIS is not a legal survey."
            )

        if "modiv" in field_key:
            return (
                f"{field_path} requires NJ MOD-IV style public-record context."
            )

        return (
            f"{field_path} is unavailable from the current source set. "
            f"Required source: {required_source or 'source-backed public record or manual review'}."
        )

    @staticmethod
    def deduplicate(
        items: list[UnavailableDataExplanation],
    ) -> list[UnavailableDataExplanation]:
        seen: set[str] = set()
        result: list[UnavailableDataExplanation] = []

        for item in items:
            key = f"{item.field_path}:{item.reason}"

            if key in seen:
                continue

            seen.add(key)
            result.append(item)

        return result


# ============================================================
# SECTION 13 - MANUAL REVIEW EXPLANATION BUILDER
# ============================================================

class ManualReviewExplanationBuilder:
    def build(
        self,
        profile_payload: Mapping[str, Any],
    ) -> list[ManualReviewExplanation]:
        items = profile_payload.get("manual_review_items") or []
        results: list[ManualReviewExplanation] = []

        if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
            return results

        for item in items:
            payload = object_to_dict(item)

            if not isinstance(payload, Mapping):
                continue

            code = safe_string(payload.get("code") or "manual_review_required")
            message = safe_string(payload.get("message") or "Manual review is required.")
            field_path = payload.get("field_path")
            required_action = payload.get("required_action")
            severity = safe_string(
                payload.get("severity") or ExplanationSeverity.WARNING.value
            )

            results.append(
                ManualReviewExplanation(
                    code=code,
                    message=message,
                    severity=severity,
                    field_path=field_path,
                    required_action=required_action,
                    why_review_is_needed=self.explain_manual_review_need(
                        code=code,
                        field_path=field_path,
                        message=message,
                    ),
                    metadata=dict(payload.get("metadata") or {}),
                )
            )

        return results

    @staticmethod
    def explain_manual_review_need(
        *,
        code: str,
        field_path: Any,
        message: str,
    ) -> str:
        key = normalize_key(code)

        if "address" in key:
            return (
                "Address manual review is needed because the lookup signal may be "
                "ambiguous, incomplete, or missing jurisdiction details."
            )

        if "parcel" in key:
            return (
                "Parcel manual review is needed because block, lot, qualifier, "
                "or parcel identity could not be source-confirmed."
            )

        if "confidence" in key:
            return (
                "Manual review is needed because the confidence level is below "
                "production reliability threshold."
            )

        if "error" in key:
            return (
                "Manual review is needed because the profile contains runtime or "
                "connector errors."
            )

        return (
            message
            or "Manual review is needed to prevent unsupported property claims."
        )


# ============================================================
# SECTION 14 - SPECIAL EXPLANATION BUILDERS
# ============================================================

class AssessmentExplanationBuilder:
    def build(
        self,
        profile_payload: Mapping[str, Any],
    ) -> AssessmentExplanation:
        assessment = profile_payload.get("tax_assessment_context") or {}

        if not isinstance(assessment, Mapping):
            assessment = {}

        total = self.to_float(assessment.get("total_assessment"))
        land = self.to_float(assessment.get("land_assessment"))
        improvement = self.to_float(assessment.get("improvement_assessment"))
        tax_year = assessment.get("tax_year")

        has_assessment = any(
            value is not None
            for value in [
                total,
                land,
                improvement,
                tax_year,
            ]
        )

        if has_assessment:
            explanation = (
                "Tax assessment is available as public-record context. "
                "It can help describe the assessed land, improvement, and total "
                "assessment, but it is not current market value, not a listing price, "
                "and not an appraisal."
            )
        else:
            explanation = (
                "Tax assessment is unavailable from the current source set. "
                "A county tax-board or assessment source is required."
            )

        return AssessmentExplanation(
            has_assessment=has_assessment,
            total_assessment=total,
            land_assessment=land,
            improvement_assessment=improvement,
            tax_year=safe_string(tax_year) or None,
            explanation=explanation,
            cannot_be_used_as_market_value=True,
        )

    @staticmethod
    def to_float(value: Any) -> float | None:
        if value in (None, ""):
            return None

        try:
            return float(str(value).replace("$", "").replace(",", ""))
        except Exception:
            return None


class ListingStatusExplanationBuilder:
    def build(
        self,
        profile_payload: Mapping[str, Any],
        source_explanations: Sequence[SourceExplanation],
    ) -> ListingStatusExplanation:
        has_feed = any(
            source.source_category == SourceCategory.AUTHORIZED_LISTING_FEED.value
            for source in source_explanations
        )

        listing_context = profile_payload.get("listing_status_context") or {}

        if not isinstance(listing_context, Mapping):
            listing_context = {}

        active_status = listing_context.get("active_status")
        listing_price = listing_context.get("listing_price")

        if has_feed:
            explanation = (
                "Authorized listing source appears connected. Current listing "
                "fields may be supported only to the extent that the feed provides "
                "them and licensing allows display."
            )
        else:
            explanation = (
                "Current listing status is not available from public records. "
                "Aussem1 requires an authorized MLS, RESO, IDX, broker-authorized "
                "feed, or listing-provider source before it can report active, "
                "pending, under-contract, days-on-market, or current list price."
            )

        return ListingStatusExplanation(
            listing_feed_connected=has_feed,
            active_status_supported=bool(has_feed and active_status),
            under_contract_supported=has_feed,
            current_price_supported=bool(has_feed and listing_price),
            explanation=explanation,
            required_source="authorized_listing_feed",
        )


class ValuationExplanationBuilder:
    def build(
        self,
        profile_payload: Mapping[str, Any],
    ) -> ValuationExplanation:
        valuation = profile_payload.get("valuation_readiness") or {}

        if not isinstance(valuation, Mapping):
            valuation = {}

        ready = bool(valuation.get("ready", False))
        estimate_allowed = bool(valuation.get("estimate_allowed", False))
        available_inputs = list(valuation.get("available_inputs") or [])
        missing_inputs = list(
            valuation.get("required_missing_inputs")
            or valuation.get("missing_inputs")
            or []
        )
        status = safe_string(
            valuation.get("status") or "not_ready"
        )

        if ready and estimate_allowed:
            explanation = (
                "Valuation appears ready because required valuation inputs are available. "
                "The estimate must still include confidence, source attribution, and "
                "limitations."
            )
        elif available_inputs:
            explanation = (
                "Some valuation inputs are available, but Aussem1 must not produce a "
                "market estimate until comparable sales, valuation model logic, and "
                "confidence calibration are connected."
            )
        else:
            explanation = (
                "Valuation is unavailable. Public records can help prepare valuation "
                "features, but assessment alone is not market value and cannot be "
                "presented as an estimate."
            )

        return ValuationExplanation(
            valuation_available=bool(ready and estimate_allowed),
            estimate_allowed=estimate_allowed,
            valuation_readiness_status=status,
            available_inputs=available_inputs,
            missing_inputs=missing_inputs,
            explanation=explanation,
            required_source="valuation_engine_and_comparable_sales",
        )


# ============================================================
# SECTION 15 - ENTERPRISE SOURCE EXPLANATION ENGINE
# ============================================================

class SourceExplanationEngine:
    def __init__(
        self,
        *,
        source_extractor: SourceExtractor | None = None,
        source_builder: SourceExplanationBuilder | None = None,
        claim_builder: ClaimExplanationBuilder | None = None,
        unavailable_builder: UnavailableDataExplanationBuilder | None = None,
        manual_review_builder: ManualReviewExplanationBuilder | None = None,
        assessment_builder: AssessmentExplanationBuilder | None = None,
        listing_builder: ListingStatusExplanationBuilder | None = None,
        valuation_builder: ValuationExplanationBuilder | None = None,
    ) -> None:
        self.source_extractor = source_extractor or SourceExtractor()
        self.source_builder = source_builder or SourceExplanationBuilder()
        self.claim_builder = claim_builder or ClaimExplanationBuilder()
        self.unavailable_builder = (
            unavailable_builder or UnavailableDataExplanationBuilder()
        )
        self.manual_review_builder = (
            manual_review_builder or ManualReviewExplanationBuilder()
        )
        self.assessment_builder = (
            assessment_builder or AssessmentExplanationBuilder()
        )
        self.listing_builder = (
            listing_builder or ListingStatusExplanationBuilder()
        )
        self.valuation_builder = (
            valuation_builder or ValuationExplanationBuilder()
        )

    def explain_profile(self, profile: Any) -> SourceExplanationReport:
        profile_payload = self.normalize_profile(profile)
        sources = self.source_extractor.extract_sources(profile_payload)
        source_explanations = self.source_builder.build_source_explanations(sources)
        claim_explanations = self.claim_builder.build_claim_explanations(
            profile_payload,
            source_explanations,
        )
        unavailable_data = self.unavailable_builder.build(profile_payload)
        manual_review_explanations = self.manual_review_builder.build(
            profile_payload
        )
        assessment_explanation = self.assessment_builder.build(profile_payload)
        listing_status_explanation = self.listing_builder.build(
            profile_payload,
            source_explanations,
        )
        valuation_explanation = self.valuation_builder.build(profile_payload)

        supported_claims = [
            claim.claim
            for claim in claim_explanations
            if claim.status == ClaimSupportStatus.SUPPORTED.value
        ]

        unsupported_claims = [
            claim.claim
            for claim in claim_explanations
            if claim.status
            in {
                ClaimSupportStatus.UNSUPPORTED.value,
                ClaimSupportStatus.REQUIRES_AUTHORIZED_SOURCE.value,
                ClaimSupportStatus.REQUIRES_VALUATION_ENGINE.value,
            }
        ]

        unavailable_claims = [
            item.field_path
            for item in unavailable_data
        ]

        required_future_sources = self.collect_required_future_sources(
            claim_explanations,
            unavailable_data,
            valuation_explanation,
            listing_status_explanation,
        )

        confidence_context = self.extract_confidence_context(profile_payload)

        summary = self.build_summary(
            supported_claims=supported_claims,
            unsupported_claims=unsupported_claims,
            unavailable_data=unavailable_data,
            manual_review_explanations=manual_review_explanations,
            assessment_explanation=assessment_explanation,
            listing_status_explanation=listing_status_explanation,
            valuation_explanation=valuation_explanation,
        )

        report = SourceExplanationReport(
            summary=summary,
            supported_claims=supported_claims,
            unsupported_claims=unsupported_claims,
            unavailable_claims=unavailable_claims,
            public_record_limitations=list(STANDARD_SOURCE_LIMITATIONS),
            required_future_sources=required_future_sources,
            source_notes=self.build_source_notes(source_explanations),
            claim_explanations=claim_explanations,
            source_explanations=source_explanations,
            unavailable_data=unavailable_data,
            manual_review_explanations=manual_review_explanations,
            assessment_explanation=assessment_explanation,
            listing_status_explanation=listing_status_explanation,
            valuation_explanation=valuation_explanation,
            confidence_context=confidence_context,
            governance=SOURCE_EXPLANATION_GOVERNANCE.copy(),
            metadata={
                "engine": SOURCE_EXPLANATION_ENGINE_NAME,
                "version": SOURCE_EXPLANATION_ENGINE_VERSION,
                "phase": SOURCE_EXPLANATION_ENGINE_PHASE,
                "source_count": len(source_explanations),
                "claim_count": len(claim_explanations),
                "unavailable_count": len(unavailable_data),
                "manual_review_count": len(manual_review_explanations),
                "generated_at": utc_now(),
            },
        )

        report.report_id = f"source-explanation-{stable_hash(report.to_dict())[:18]}"

        return report

    def explain(self, profile: Any) -> SourceExplanationReport:
        return self.explain_profile(profile)

    def build_profile_explanation(self, profile: Any) -> SourceExplanationReport:
        return self.explain_profile(profile)

    def generate(self, profile: Any) -> SourceExplanationReport:
        return self.explain_profile(profile)

    @staticmethod
    def normalize_profile(profile: Any) -> dict[str, Any]:
        payload = object_to_dict(profile)

        if isinstance(payload, Mapping):
            return dict(payload)

        return {
            "raw_profile": payload,
        }

    @staticmethod
    def collect_required_future_sources(
        claim_explanations: Sequence[ClaimExplanation],
        unavailable_data: Sequence[UnavailableDataExplanation],
        valuation_explanation: ValuationExplanation,
        listing_status_explanation: ListingStatusExplanation,
    ) -> list[str]:
        sources: list[str] = []

        for claim in claim_explanations:
            if claim.required_source:
                sources.append(claim.required_source)

        for item in unavailable_data:
            if item.required_source:
                sources.append(item.required_source)

        if not valuation_explanation.valuation_available:
            sources.append(valuation_explanation.required_source)

        if not listing_status_explanation.listing_feed_connected:
            sources.append(listing_status_explanation.required_source)

        return list(dict.fromkeys(sources))

    @staticmethod
    def extract_confidence_context(
        profile_payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        confidence = profile_payload.get("confidence_report") or {}

        if not isinstance(confidence, Mapping):
            return {
                "available": False,
                "explanation": "Confidence report is not available.",
            }

        return {
            "available": True,
            "overall_confidence": confidence.get("overall_confidence")
            or confidence.get("confidence"),
            "band": confidence.get("band"),
            "decision": confidence.get("decision"),
            "manual_review_required": confidence.get("manual_review_required"),
            "explanation": confidence.get("explanation"),
        }

    @staticmethod
    def build_source_notes(
        source_explanations: Sequence[SourceExplanation],
    ) -> list[str]:
        notes = [
            "Address intelligence prepares lookup input and does not prove property facts by itself.",
            "Source explanations are generated from available evidence and source-governance rules.",
        ]

        if not source_explanations:
            notes.append(
                "No source-backed public-record source payloads were available in this profile."
            )

        for source in source_explanations:
            notes.append(source.explanation)

        return list(dict.fromkeys(notes))

    @staticmethod
    def build_summary(
        *,
        supported_claims: Sequence[str],
        unsupported_claims: Sequence[str],
        unavailable_data: Sequence[UnavailableDataExplanation],
        manual_review_explanations: Sequence[ManualReviewExplanation],
        assessment_explanation: AssessmentExplanation,
        listing_status_explanation: ListingStatusExplanation,
        valuation_explanation: ValuationExplanation,
    ) -> str:
        pieces = []

        if supported_claims:
            pieces.append(
                f"{len(supported_claims)} claim categories have some source-support context."
            )
        else:
            pieces.append(
                "No source-backed public-record claim categories are fully supported yet."
            )

        if unsupported_claims:
            pieces.append(
                f"{len(unsupported_claims)} claim categories are unsupported by public records alone."
            )

        if unavailable_data:
            pieces.append(
                f"{len(unavailable_data)} fields remain unavailable and are labeled explicitly."
            )

        if manual_review_explanations:
            pieces.append(
                f"{len(manual_review_explanations)} manual-review items require attention."
            )

        pieces.append(assessment_explanation.explanation)
        pieces.append(listing_status_explanation.explanation)
        pieces.append(valuation_explanation.explanation)

        return " ".join(piece for piece in pieces if piece)


# ============================================================
# SECTION 16 - CONVENIENCE API
# ============================================================

_default_source_explanation_engine = SourceExplanationEngine()


def explain_profile_sources(profile: Any) -> SourceExplanationReport:
    return _default_source_explanation_engine.explain_profile(profile)


def build_source_explanation_report(profile: Any) -> SourceExplanationReport:
    return _default_source_explanation_engine.explain_profile(profile)


def explain_sources(profile: Any) -> SourceExplanationReport:
    return _default_source_explanation_engine.explain_profile(profile)


def explain_profile(profile: Any) -> SourceExplanationReport:
    return _default_source_explanation_engine.explain_profile(profile)


def source_explanation_to_public_api_payload(
    report: SourceExplanationReport,
) -> dict[str, Any]:
    return report.to_dict()


# ============================================================
# SECTION 17 - HEALTH, READINESS, AND DIAGNOSTICS
# ============================================================

def validate_source_explanation_governance() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    false_keys = [
        "fabricated_source_support_allowed",
        "fabricated_property_facts_allowed",
        "fabricated_listing_status_allowed",
        "fabricated_market_value_allowed",
        "assessment_as_market_value_allowed",
        "public_records_as_listing_feed_allowed",
    ]

    for key in false_keys:
        if SOURCE_EXPLANATION_GOVERNANCE.get(key):
            issues.append(
                {
                    "issue_code": f"{key}_must_remain_false",
                    "severity": "critical",
                    "message": f"{key} must remain False.",
                }
            )

    true_keys = [
        "manual_review_disclosure_required",
        "unsupported_claims_must_be_labeled",
        "unavailable_fields_must_be_labeled",
        "future_required_sources_must_be_named",
        "source_limitations_must_be_explained",
        "confidence_context_required",
    ]

    for key in true_keys:
        if not SOURCE_EXPLANATION_GOVERNANCE.get(key):
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


def get_source_explanation_engine_metadata() -> dict[str, Any]:
    return {
        "name": SOURCE_EXPLANATION_ENGINE_NAME,
        "version": SOURCE_EXPLANATION_ENGINE_VERSION,
        "phase": SOURCE_EXPLANATION_ENGINE_PHASE,
        "status": SOURCE_EXPLANATION_ENGINE_STATUS,
        "release_channel": SOURCE_EXPLANATION_RELEASE_CHANNEL,
        "generated_at": utc_now(),
    }


def get_source_explanation_engine_health() -> dict[str, Any]:
    governance = validate_source_explanation_governance()

    sample_profile = {
        "canonical_address": "43 Wetmore Ave, Morristown, NJ 07960",
        "tax_assessment_context": {
            "total_assessment": 500000,
            "tax_year": "2026",
            "source_status": "source_backed",
            "sources": [
                {
                    "source_name": "Sample Tax Board Source",
                    "source_type": "morris_tax_board",
                    "confidence": 0.75,
                    "retrieved_at": utc_now(),
                }
            ],
        },
        "listing_status_context": {},
        "valuation_readiness": {
            "ready": False,
            "estimate_allowed": False,
            "available_inputs": ["tax_assessment"],
            "required_missing_inputs": ["comparable_sales", "valuation_model"],
        },
        "manual_review_items": [],
        "unavailable_fields": [],
    }

    sample = explain_profile_sources(sample_profile)

    return {
        "name": SOURCE_EXPLANATION_ENGINE_NAME,
        "version": SOURCE_EXPLANATION_ENGINE_VERSION,
        "phase": SOURCE_EXPLANATION_ENGINE_PHASE,
        "status": SOURCE_EXPLANATION_ENGINE_STATUS,
        "governance_valid": governance["valid"],
        "governance_issue_count": governance["issue_count"],
        "sample_report_created": bool(sample.report_id),
        "sample_supported_claim_count": len(sample.supported_claims),
        "sample_unsupported_claim_count": len(sample.unsupported_claims),
        "fabricated_source_support_allowed": False,
        "fabricated_listing_status_allowed": False,
        "assessment_as_market_value_allowed": False,
        "generated_at": utc_now(),
    }


def get_source_explanation_engine_readiness() -> dict[str, Any]:
    health = get_source_explanation_engine_health()

    required = {
        "governance_valid": health["governance_valid"],
        "sample_report_created": health["sample_report_created"],
    }

    return {
        "ready": all(required.values()),
        "required": required,
        "missing_required": [
            key
            for key, value in required.items()
            if not value
        ],
        "next_files": [
            "app/web/property_routes.py",
            "app/public_records/public_records_engine.py",
            "app/public_records/connectors/nj_morris_tax_board_connector.py",
            "app/public_records/connectors/nj_morris_gis_connector.py",
        ],
        "generated_at": utc_now(),
    }


def get_source_explanation_engine_diagnostics() -> dict[str, Any]:
    return {
        "metadata": get_source_explanation_engine_metadata(),
        "health": get_source_explanation_engine_health(),
        "readiness": get_source_explanation_engine_readiness(),
        "governance": SOURCE_EXPLANATION_GOVERNANCE.copy(),
        "governance_validation": validate_source_explanation_governance(),
        "public_record_supported_claims": PUBLIC_RECORD_SUPPORTED_CLAIMS,
        "public_record_unsupported_claims": PUBLIC_RECORD_UNSUPPORTED_CLAIMS,
        "future_required_sources": FUTURE_REQUIRED_SOURCES,
        "standard_source_limitations": STANDARD_SOURCE_LIMITATIONS,
        "exports": __all__,
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 18 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "SOURCE_EXPLANATION_ENGINE_NAME",
    "SOURCE_EXPLANATION_ENGINE_VERSION",
    "SOURCE_EXPLANATION_ENGINE_PHASE",
    "SOURCE_EXPLANATION_ENGINE_STATUS",
    "SOURCE_EXPLANATION_RELEASE_CHANNEL",
    "SOURCE_EXPLANATION_GOVERNANCE",
    "PUBLIC_RECORD_SUPPORTED_CLAIMS",
    "PUBLIC_RECORD_UNSUPPORTED_CLAIMS",
    "FUTURE_REQUIRED_SOURCES",
    "STANDARD_SOURCE_LIMITATIONS",
    "ClaimSupportStatus",
    "ExplanationSeverity",
    "SourceCategory",
    "RequiredSourceType",
    "SourceCapability",
    "ClaimExplanation",
    "SourceExplanation",
    "UnavailableDataExplanation",
    "ManualReviewExplanation",
    "AssessmentExplanation",
    "ListingStatusExplanation",
    "ValuationExplanation",
    "SourceExplanationReport",
    "PropertySourceExplanationReport",
    "SourceExplanationResult",
    "SourceCapabilityRegistry",
    "ClaimClassifier",
    "SourceExtractor",
    "SourceExplanationBuilder",
    "ClaimExplanationBuilder",
    "UnavailableDataExplanationBuilder",
    "ManualReviewExplanationBuilder",
    "AssessmentExplanationBuilder",
    "ListingStatusExplanationBuilder",
    "ValuationExplanationBuilder",
    "SourceExplanationEngine",
    "explain_profile_sources",
    "build_source_explanation_report",
    "explain_sources",
    "explain_profile",
    "source_explanation_to_public_api_payload",
    "validate_source_explanation_governance",
    "get_source_explanation_engine_metadata",
    "get_source_explanation_engine_health",
    "get_source_explanation_engine_readiness",
    "get_source_explanation_engine_diagnostics",
]


# ============================================================
# END OF FILE
# ============================================================