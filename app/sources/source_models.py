# ============================================================
# AUSSEM1
# PHASE 2.10 PART 2.00
# ENTERPRISE SOURCE MODELS
# FILE: app/sources/source_models.py
# PURPOSE:
# Define the official source data models used across Aussem1 for
# public records, tax records, parcel data, clerk records, listing
# sources, market data, comparable data, valuation inputs, and
# future machine-learning source attribution.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# REAL DATA SOURCE MODELS ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from enum import StrEnum
from typing import Any


# ============================================================
# SECTION 02 - MODEL VERSION CONFIGURATION
# ============================================================

SOURCE_MODELS_NAME = "Aussem1 Enterprise Source Models"

SOURCE_MODELS_VERSION = "0.1.0"

SOURCE_MODELS_PHASE = "PHASE 2.10 PART 2.00"

SOURCE_MODELS_STATUS = "real_data_source_models_active"


# ============================================================
# SECTION 03 - SOURCE TYPE ENUMERATION
# ============================================================

class SourceType(StrEnum):
    """
    High-level source category.

    These categories govern what a source may reasonably support.
    For example, public records may support tax, parcel, deed,
    sale-history, or assessment context, but they do not reliably
    support current active or under-contract listing status.
    """

    PUBLIC_RECORD = "public_record"
    COUNTY_ASSESSOR = "county_assessor"
    COUNTY_CLERK = "county_clerk"
    COUNTY_RECORDER = "county_recorder"
    TAX_BOARD = "tax_board"
    TAX_COLLECTOR = "tax_collector"
    PARCEL_GIS = "parcel_gis"
    STATE_PARCEL_DATA = "state_parcel_data"
    STATE_ASSESSMENT_DATA = "state_assessment_data"
    MUNICIPAL_RECORD = "municipal_record"
    SCHOOL_DATA = "school_data"
    MARKET_DATA = "market_data"
    RISK_DATA = "risk_data"
    MLS_RESO = "mls_reso"
    IDX = "idx"
    BROKER_FEED = "broker_feed"
    LISTING_PROVIDER = "listing_provider"
    USER_PROVIDED = "user_provided"
    INTERNAL_MEMORY = "internal_memory"
    INTERNAL_INFERENCE = "internal_inference"
    MACHINE_LEARNING_MODEL = "machine_learning_model"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 04 - SOURCE STATUS ENUMERATION
# ============================================================

class SourceStatus(StrEnum):
    """
    Runtime status of a source lookup or source connector.
    """

    ACTIVE = "active"
    PLANNED = "planned"
    CONNECTED = "connected"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    NOT_IMPLEMENTED = "not_implemented"
    AUTH_REQUIRED = "auth_required"
    RATE_LIMITED = "rate_limited"
    FAILED = "failed"
    ERROR = "error"
    EMPTY = "empty"
    PARTIAL = "partial"
    STALE = "stale"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    DISABLED = "disabled"


# ============================================================
# SECTION 05 - SOURCE RELIABILITY ENUMERATION
# ============================================================

class SourceReliability(StrEnum):
    """
    Reliability tier used to rank source trust.
    """

    OFFICIAL = "official"
    AUTHORIZED = "authorized"
    LICENSED = "licensed"
    USER_PROVIDED = "user_provided"
    INTERNAL_INFERENCE = "internal_inference"
    UNVERIFIED = "unverified"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 06 - SOURCE ACCESS METHOD ENUMERATION
# ============================================================

class SourceAccessMethod(StrEnum):
    """
    How Aussem1 accesses the source.
    """

    OFFICIAL_API = "official_api"
    PUBLIC_WEB_PORTAL = "public_web_portal"
    DOWNLOADABLE_DATASET = "downloadable_dataset"
    DOCUMENT_SEARCH = "document_search"
    GIS_SERVICE = "gis_service"
    MANUAL_ENTRY = "manual_entry"
    LICENSED_FEED = "licensed_feed"
    INTERNAL_FILE = "internal_file"
    FUTURE_CONNECTOR = "future_connector"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 07 - SOURCE DATA FORMAT ENUMERATION
# ============================================================

class SourceDataFormat(StrEnum):
    """
    Expected data format returned by the source.
    """

    JSON = "json"
    HTML = "html"
    XML = "xml"
    CSV = "csv"
    PDF = "pdf"
    IMAGE = "image"
    GIS_LAYER = "gis_layer"
    DOCUMENT = "document"
    TEXT = "text"
    MIXED = "mixed"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 08 - SOURCE CLAIM TYPE ENUMERATION
# ============================================================

class SourceClaimType(StrEnum):
    """
    Claim categories that source records may support.
    """

    ADDRESS_IDENTITY = "address_identity"
    PARCEL_IDENTITY = "parcel_identity"
    TAX_ASSESSMENT = "tax_assessment"
    PROPERTY_TAX = "property_tax"
    LAND_VALUE = "land_value"
    IMPROVEMENT_VALUE = "improvement_value"
    DEED_REFERENCE = "deed_reference"
    MORTGAGE_REFERENCE = "mortgage_reference"
    LIEN_REFERENCE = "lien_reference"
    SALE_HISTORY = "sale_history"
    OWNER_REFERENCE = "owner_reference"
    BUILDING_FACTS = "building_facts"
    LOT_SIZE = "lot_size"
    YEAR_BUILT = "year_built"
    PROPERTY_CLASS = "property_class"
    MUNICIPALITY = "municipality"
    COUNTY = "county"
    SCHOOL_DISTRICT = "school_district"
    ZONING_CONTEXT = "zoning_context"
    FLOOD_CONTEXT = "flood_context"
    ACTIVE_LISTING_STATUS = "active_listing_status"
    UNDER_CONTRACT_STATUS = "under_contract_status"
    SOLD_STATUS = "sold_status"
    LISTING_PRICE = "listing_price"
    DAYS_ON_MARKET = "days_on_market"
    COMPARABLE_SALE = "comparable_sale"
    VALUATION_INPUT = "valuation_input"
    MARKET_TREND = "market_trend"
    INTERNAL_REASONING = "internal_reasoning"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 09 - CONFIDENCE BAND ENUMERATION
# ============================================================

class SourceConfidenceBand(StrEnum):
    """
    Human-readable confidence band.
    """

    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 10 - SOURCE ERROR TYPE ENUMERATION
# ============================================================

class SourceErrorType(StrEnum):
    """
    Standard source error categories.
    """

    NONE = "none"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    AUTH_REQUIRED = "auth_required"
    RATE_LIMITED = "rate_limited"
    NOT_FOUND = "not_found"
    EMPTY_RESULT = "empty_result"
    PARSE_ERROR = "parse_error"
    INVALID_QUERY = "invalid_query"
    SOURCE_UNAVAILABLE = "source_unavailable"
    CONNECTOR_NOT_IMPLEMENTED = "connector_not_implemented"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 11 - SOURCE FRESHNESS ENUMERATION
# ============================================================

class SourceFreshness(StrEnum):
    """
    Freshness of source data.
    """

    LIVE = "live"
    RECENT = "recent"
    CURRENT_YEAR = "current_year"
    HISTORICAL = "historical"
    STALE = "stale"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 12 - SOURCE LEGAL / ACCESS POLICY ENUMERATION
# ============================================================

class SourceAccessPolicy(StrEnum):
    """
    Access policy classification.
    """

    PUBLIC = "public"
    PUBLIC_WITH_TERMS = "public_with_terms"
    AUTHENTICATED = "authenticated"
    LICENSED = "licensed"
    PERMISSION_REQUIRED = "permission_required"
    INTERNAL_ONLY = "internal_only"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 13 - UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(UTC).isoformat()


def stable_hash(value: Any) -> str:
    """
    Create a stable SHA-256 hash for a source object.
    """

    serialized = json.dumps(
        value,
        sort_keys=True,
        default=str,
        ensure_ascii=False,
    )

    return hashlib.sha256(
        serialized.encode("utf-8"),
    ).hexdigest()


def clamp_confidence(value: float | int | None) -> float:
    """
    Clamp confidence to 0.0 through 1.0.
    """

    if value is None:
        return 0.0

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0

    if numeric < 0.0:
        return 0.0

    if numeric > 1.0:
        return 1.0

    return numeric


def confidence_band(value: float | int | None) -> SourceConfidenceBand:
    """
    Convert numeric confidence into a confidence band.
    """

    numeric = clamp_confidence(value)

    if numeric >= 0.90:
        return SourceConfidenceBand.VERY_HIGH

    if numeric >= 0.75:
        return SourceConfidenceBand.HIGH

    if numeric >= 0.55:
        return SourceConfidenceBand.MEDIUM

    if numeric >= 0.35:
        return SourceConfidenceBand.LOW

    if numeric > 0:
        return SourceConfidenceBand.VERY_LOW

    return SourceConfidenceBand.UNKNOWN


def safe_string(value: Any) -> str:
    """
    Convert unknown value to safe string.
    """

    if value is None:
        return ""

    return str(value).strip()


def normalize_key(value: str | None) -> str:
    """
    Normalize source keys for comparisons.
    """

    if not value:
        return ""

    return "_".join(
        value.lower().strip().replace("-", " ").split()
    )


# ============================================================
# SECTION 14 - SOURCE ATTRIBUTION MODEL
# ============================================================

@dataclass
class SourceAttribution:
    """
    Describes where a fact or record came from.
    """

    source_id: str
    source_name: str
    source_type: str
    reliability: str
    access_method: str
    source_url: str | None = None
    source_agency: str | None = None
    source_jurisdiction: str | None = None
    source_description: str | None = None
    retrieved_at: str = field(default_factory=utc_now)
    terms_note: str | None = None
    citation_note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert attribution to dictionary.
        """

        return asdict(self)

    def fingerprint(self) -> str:
        """
        Return stable attribution fingerprint.
        """

        return stable_hash(self.to_dict())


# ============================================================
# SECTION 15 - SOURCE TIMESTAMP MODEL
# ============================================================

@dataclass
class SourceTimestamp:
    """
    Tracks data recency.
    """

    retrieved_at: str = field(default_factory=utc_now)
    source_updated_at: str | None = None
    source_effective_date: str | None = None
    record_date: str | None = None
    tax_year: int | None = None
    freshness: str = SourceFreshness.UNKNOWN.value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# SECTION 16 - SOURCE ERROR MODEL
# ============================================================

@dataclass
class SourceError:
    """
    Standardized source error.
    """

    error_type: str
    message: str
    source_id: str | None = None
    source_name: str | None = None
    recoverable: bool = True
    retry_recommended: bool = False
    manual_review_required: bool = False
    raw_error: str | None = None
    occurred_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# SECTION 17 - SOURCE WARNING MODEL
# ============================================================

@dataclass
class SourceWarning:
    """
    Warning emitted during source processing.
    """

    warning_code: str
    message: str
    severity: str = "medium"
    field_name: str | None = None
    source_id: str | None = None
    generated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# SECTION 18 - SOURCE QUERY MODEL
# ============================================================

@dataclass
class SourceQuery:
    """
    Represents a query sent to a source connector.
    """

    query_id: str
    source_id: str
    query_type: str
    raw_query: str
    normalized_query: str | None = None
    address: str | None = None
    municipality: str | None = None
    county: str | None = None
    state: str | None = None
    block: str | None = None
    lot: str | None = None
    qualifier: str | None = None
    owner_name: str | None = None
    tax_year: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def fingerprint(self) -> str:
        return stable_hash(self.to_dict())


# ============================================================
# SECTION 19 - SOURCE FIELD MODEL
# ============================================================

@dataclass
class SourceField:
    """
    Represents one field extracted from a source.
    """

    field_name: str
    value: Any
    claim_type: str
    attribution: SourceAttribution
    confidence: float
    confidence_band: str | None = None
    raw_value: Any | None = None
    normalized_value: Any | None = None
    unit: str | None = None
    data_format: str | None = None
    timestamp: SourceTimestamp | None = None
    notes: list[str] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.confidence = clamp_confidence(self.confidence)

        if self.confidence_band is None:
            self.confidence_band = confidence_band(self.confidence).value

        if self.timestamp is None:
            self.timestamp = SourceTimestamp()

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "value": self.value,
            "claim_type": self.claim_type,
            "attribution": self.attribution.to_dict(),
            "confidence": self.confidence,
            "confidence_band": self.confidence_band,
            "raw_value": self.raw_value,
            "normalized_value": self.normalized_value,
            "unit": self.unit,
            "data_format": self.data_format,
            "timestamp": (
                self.timestamp.to_dict()
                if self.timestamp
                else None
            ),
            "notes": self.notes,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }

    def fingerprint(self) -> str:
        return stable_hash(self.to_dict())


# ============================================================
# SECTION 20 - SOURCE RECORD REFERENCE MODEL
# ============================================================

@dataclass
class SourceRecordReference:
    """
    Lightweight reference to a source record.
    """

    record_id: str
    source_id: str
    source_name: str
    record_type: str
    display_label: str
    source_url: str | None = None
    document_id: str | None = None
    book: str | None = None
    page: str | None = None
    instrument_number: str | None = None
    block: str | None = None
    lot: str | None = None
    municipality: str | None = None
    county: str | None = None
    state: str | None = None
    record_date: str | None = None
    retrieved_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def fingerprint(self) -> str:
        return stable_hash(self.to_dict())


# ============================================================
# SECTION 21 - SOURCE CONFIDENCE REPORT MODEL
# ============================================================

@dataclass
class SourceConfidenceReport:
    """
    Confidence report for one source result.
    """

    confidence: float
    confidence_band: str | None = None
    positive_factors: list[str] = field(default_factory=list)
    negative_factors: list[str] = field(default_factory=list)
    missing_factors: list[str] = field(default_factory=list)
    source_agreement: str | None = None
    manual_review_required: bool = False
    explanation: str | None = None

    def __post_init__(self) -> None:
        self.confidence = clamp_confidence(self.confidence)

        if self.confidence_band is None:
            self.confidence_band = confidence_band(self.confidence).value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# SECTION 22 - SOURCE RESULT MODEL
# ============================================================

@dataclass
class SourceResult:
    """
    Standard result returned by every source connector.
    """

    result_id: str
    source_id: str
    source_name: str
    source_type: str
    status: str
    query: SourceQuery | None = None
    attribution: SourceAttribution | None = None
    records_found: int = 0
    fields: list[SourceField] = field(default_factory=list)
    record_references: list[SourceRecordReference] = field(default_factory=list)
    raw_payload: Any | None = None
    parsed_payload: Any | None = None
    confidence_report: SourceConfidenceReport | None = None
    errors: list[SourceError] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    retrieved_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "status": self.status,
            "query": (
                self.query.to_dict()
                if self.query
                else None
            ),
            "attribution": (
                self.attribution.to_dict()
                if self.attribution
                else None
            ),
            "records_found": self.records_found,
            "fields": [
                source_field.to_dict()
                for source_field in self.fields
            ],
            "record_references": [
                reference.to_dict()
                for reference in self.record_references
            ],
            "raw_payload": self.raw_payload,
            "parsed_payload": self.parsed_payload,
            "confidence_report": (
                self.confidence_report.to_dict()
                if self.confidence_report
                else None
            ),
            "errors": [
                error.to_dict()
                for error in self.errors
            ],
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
            "metadata": self.metadata,
            "retrieved_at": self.retrieved_at,
        }

    def fingerprint(self) -> str:
        return stable_hash(self.to_dict())

    def has_errors(self) -> bool:
        """
        Return whether result has errors.
        """

        return len(self.errors) > 0

    def is_successful(self) -> bool:
        """
        Return whether result is successful enough to use.
        """

        return self.status in {
            SourceStatus.ACTIVE.value,
            SourceStatus.CONNECTED.value,
            SourceStatus.AVAILABLE.value,
            SourceStatus.PARTIAL.value,
        } and not self.has_errors()


# ============================================================
# SECTION 23 - SOURCE CONNECTOR CAPABILITY MODEL
# ============================================================

@dataclass
class SourceConnectorCapability:
    """
    Declares what a connector can support.
    """

    claim_type: str
    supported: bool
    requires_auth: bool = False
    requires_license: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# SECTION 24 - SOURCE REQUEST POLICY MODEL
# ============================================================

@dataclass
class SourceRequestPolicy:
    """
    Safe request policy for a connector.
    """

    timeout_seconds: int = 20
    max_retries: int = 1
    respect_rate_limits: bool = True
    user_agent_required: bool = True
    uncontrolled_scraping_allowed: bool = False
    bypass_access_controls_allowed: bool = False
    store_raw_payload: bool = False
    manual_review_on_ambiguity: bool = True
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# SECTION 25 - SOURCE REGISTRY ENTRY MODEL
# ============================================================

@dataclass
class SourceRegistryEntry:
    """
    Registry entry for an official or planned source.
    """

    source_id: str
    display_name: str
    source_type: str
    status: str
    reliability: str
    access_method: str
    access_policy: str
    data_format: str
    jurisdiction: str | None = None
    state: str | None = None
    county: str | None = None
    municipality: str | None = None
    source_url: str | None = None
    documentation_url: str | None = None
    implementation_file: str | None = None
    capabilities: list[SourceConnectorCapability] = field(default_factory=list)
    request_policy: SourceRequestPolicy = field(default_factory=SourceRequestPolicy)
    expected_claims: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    official_source_required: bool = True
    mock_data_allowed: bool = False
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "display_name": self.display_name,
            "source_type": self.source_type,
            "status": self.status,
            "reliability": self.reliability,
            "access_method": self.access_method,
            "access_policy": self.access_policy,
            "data_format": self.data_format,
            "jurisdiction": self.jurisdiction,
            "state": self.state,
            "county": self.county,
            "municipality": self.municipality,
            "source_url": self.source_url,
            "documentation_url": self.documentation_url,
            "implementation_file": self.implementation_file,
            "capabilities": [
                capability.to_dict()
                for capability in self.capabilities
            ],
            "request_policy": self.request_policy.to_dict(),
            "expected_claims": self.expected_claims,
            "unsupported_claims": self.unsupported_claims,
            "official_source_required": self.official_source_required,
            "mock_data_allowed": self.mock_data_allowed,
            "notes": self.notes,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def fingerprint(self) -> str:
        return stable_hash(self.to_dict())

    def supports_claim(self, claim_type: str) -> bool:
        """
        Return whether this source supports a claim type.
        """

        if claim_type in self.expected_claims:
            return True

        for capability in self.capabilities:
            if capability.claim_type == claim_type:
                return capability.supported

        return False


# ============================================================
# SECTION 26 - SOURCE VALIDATION ISSUE MODEL
# ============================================================

@dataclass
class SourceValidationIssue:
    """
    Validation issue for source records or connectors.
    """

    issue_code: str
    message: str
    severity: str = "medium"
    source_id: str | None = None
    field_name: str | None = None
    claim_type: str | None = None
    manual_review_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# SECTION 27 - SOURCE VALIDATION REPORT MODEL
# ============================================================

@dataclass
class SourceValidationReport:
    """
    Validation report for a source result or registry entry.
    """

    valid: bool
    issues: list[SourceValidationIssue] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)
    checked_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
            "checked_at": self.checked_at,
        }


# ============================================================
# SECTION 28 - SOURCE BATCH RESULT MODEL
# ============================================================

@dataclass
class SourceBatchResult:
    """
    Aggregated result across multiple source connectors.
    """

    batch_id: str
    query: SourceQuery
    results: list[SourceResult] = field(default_factory=list)
    started_at: str = field(default_factory=utc_now)
    completed_at: str | None = None
    status: str = SourceStatus.PARTIAL.value
    errors: list[SourceError] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def complete(self) -> None:
        """
        Mark batch complete.
        """

        self.completed_at = utc_now()

        if self.errors:
            self.status = SourceStatus.ERROR.value
            return

        if not self.results:
            self.status = SourceStatus.EMPTY.value
            return

        if all(result.is_successful() for result in self.results):
            self.status = SourceStatus.AVAILABLE.value
            return

        self.status = SourceStatus.PARTIAL.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "query": self.query.to_dict(),
            "results": [
                result.to_dict()
                for result in self.results
            ],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "errors": [
                error.to_dict()
                for error in self.errors
            ],
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
            "metadata": self.metadata,
        }


# ============================================================
# SECTION 29 - SOURCE FACT MODEL
# ============================================================

@dataclass
class SourceFact:
    """
    One claimable fact backed by one or more source fields.
    """

    fact_id: str
    claim_type: str
    label: str
    value: Any
    confidence: float
    confidence_band: str | None = None
    primary_source: SourceAttribution | None = None
    supporting_fields: list[SourceField] = field(default_factory=list)
    supporting_record_references: list[SourceRecordReference] = field(
        default_factory=list
    )
    conflicts: list[str] = field(default_factory=list)
    missing_context: list[str] = field(default_factory=list)
    manual_review_required: bool = False
    generated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.confidence = clamp_confidence(self.confidence)

        if self.confidence_band is None:
            self.confidence_band = confidence_band(self.confidence).value

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "claim_type": self.claim_type,
            "label": self.label,
            "value": self.value,
            "confidence": self.confidence,
            "confidence_band": self.confidence_band,
            "primary_source": (
                self.primary_source.to_dict()
                if self.primary_source
                else None
            ),
            "supporting_fields": [
                field_item.to_dict()
                for field_item in self.supporting_fields
            ],
            "supporting_record_references": [
                reference.to_dict()
                for reference in self.supporting_record_references
            ],
            "conflicts": self.conflicts,
            "missing_context": self.missing_context,
            "manual_review_required": self.manual_review_required,
            "generated_at": self.generated_at,
        }

    def fingerprint(self) -> str:
        return stable_hash(self.to_dict())


# ============================================================
# SECTION 30 - SOURCE MERGE REPORT MODEL
# ============================================================

@dataclass
class SourceMergeReport:
    """
    Report created when multiple source results are combined.
    """

    merge_id: str
    subject: str
    source_results: list[SourceResult]
    facts: list[SourceFact] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    missing_sources: list[str] = field(default_factory=list)
    confidence_report: SourceConfidenceReport | None = None
    manual_review_required: bool = False
    generated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "merge_id": self.merge_id,
            "subject": self.subject,
            "source_results": [
                result.to_dict()
                for result in self.source_results
            ],
            "facts": [
                fact.to_dict()
                for fact in self.facts
            ],
            "conflicts": self.conflicts,
            "missing_sources": self.missing_sources,
            "confidence_report": (
                self.confidence_report.to_dict()
                if self.confidence_report
                else None
            ),
            "manual_review_required": self.manual_review_required,
            "generated_at": self.generated_at,
        }


# ============================================================
# SECTION 31 - SOURCE MODEL VALIDATION HELPERS
# ============================================================

def validate_registry_entry(
    entry: SourceRegistryEntry,
) -> SourceValidationReport:
    """
    Validate source registry entry.
    """

    issues: list[SourceValidationIssue] = []

    if not entry.source_id:
        issues.append(
            SourceValidationIssue(
                issue_code="missing_source_id",
                message="Source registry entry is missing source_id.",
                severity="high",
            )
        )

    if not entry.display_name:
        issues.append(
            SourceValidationIssue(
                issue_code="missing_display_name",
                message="Source registry entry is missing display name.",
                severity="medium",
                source_id=entry.source_id,
            )
        )

    if entry.mock_data_allowed:
        issues.append(
            SourceValidationIssue(
                issue_code="mock_data_not_allowed",
                message="Mock property data is not allowed in real-data-first architecture.",
                severity="critical",
                source_id=entry.source_id,
                manual_review_required=True,
            )
        )

    if not entry.expected_claims and not entry.capabilities:
        issues.append(
            SourceValidationIssue(
                issue_code="missing_capabilities",
                message="Source registry entry does not declare supported claims.",
                severity="medium",
                source_id=entry.source_id,
            )
        )

    return SourceValidationReport(
        valid=not issues,
        issues=issues,
    )


def validate_source_result(
    result: SourceResult,
) -> SourceValidationReport:
    """
    Validate source result.
    """

    issues: list[SourceValidationIssue] = []

    if not result.source_id:
        issues.append(
            SourceValidationIssue(
                issue_code="missing_source_id",
                message="Source result is missing source_id.",
                severity="high",
            )
        )

    if not result.source_name:
        issues.append(
            SourceValidationIssue(
                issue_code="missing_source_name",
                message="Source result is missing source_name.",
                severity="high",
                source_id=result.source_id,
            )
        )

    if result.status in {
        SourceStatus.ERROR.value,
        SourceStatus.FAILED.value,
    } and not result.errors:
        issues.append(
            SourceValidationIssue(
                issue_code="missing_error_details",
                message="Source result failed but contains no error details.",
                severity="medium",
                source_id=result.source_id,
            )
        )

    if result.fields and not result.attribution:
        issues.append(
            SourceValidationIssue(
                issue_code="missing_attribution",
                message="Source result has fields but no result-level attribution.",
                severity="medium",
                source_id=result.source_id,
            )
        )

    return SourceValidationReport(
        valid=not issues,
        issues=issues,
    )


# ============================================================
# SECTION 32 - FACTORY HELPERS
# ============================================================

def make_source_query(
    *,
    source_id: str,
    query_type: str,
    raw_query: str,
    **kwargs: Any,
) -> SourceQuery:
    """
    Create source query with stable ID.
    """

    payload = {
        "source_id": source_id,
        "query_type": query_type,
        "raw_query": raw_query,
        "kwargs": kwargs,
    }

    query_id = f"source-query-{stable_hash(payload)[:16]}"

    return SourceQuery(
        query_id=query_id,
        source_id=source_id,
        query_type=query_type,
        raw_query=raw_query,
        normalized_query=kwargs.get("normalized_query"),
        address=kwargs.get("address"),
        municipality=kwargs.get("municipality"),
        county=kwargs.get("county"),
        state=kwargs.get("state"),
        block=kwargs.get("block"),
        lot=kwargs.get("lot"),
        qualifier=kwargs.get("qualifier"),
        owner_name=kwargs.get("owner_name"),
        tax_year=kwargs.get("tax_year"),
        metadata=kwargs.get("metadata", {}),
    )


def make_source_error(
    *,
    error_type: SourceErrorType,
    message: str,
    source_id: str | None = None,
    source_name: str | None = None,
    raw_error: str | None = None,
) -> SourceError:
    """
    Create source error.
    """

    return SourceError(
        error_type=error_type.value,
        message=message,
        source_id=source_id,
        source_name=source_name,
        raw_error=raw_error,
    )


def make_empty_source_result(
    *,
    source_id: str,
    source_name: str,
    source_type: SourceType,
    query: SourceQuery | None = None,
    message: str | None = None,
) -> SourceResult:
    """
    Create empty source result.
    """

    warning = SourceWarning(
        warning_code="empty_result",
        message=message or "Source returned no records.",
        severity="medium",
        source_id=source_id,
    )

    return SourceResult(
        result_id=f"source-result-{stable_hash({'source_id': source_id, 'query': query.to_dict() if query else None})[:16]}",
        source_id=source_id,
        source_name=source_name,
        source_type=source_type.value,
        status=SourceStatus.EMPTY.value,
        query=query,
        records_found=0,
        confidence_report=SourceConfidenceReport(
            confidence=0.0,
            negative_factors=["No records found."],
            missing_factors=["Source record unavailable."],
            explanation=message or "No source records were returned.",
        ),
        warnings=[warning],
    )


# ============================================================
# SECTION 33 - MODEL REGISTRY
# ============================================================

SOURCE_MODEL_REGISTRY = {
    "SourceAttribution": SourceAttribution,
    "SourceTimestamp": SourceTimestamp,
    "SourceError": SourceError,
    "SourceWarning": SourceWarning,
    "SourceQuery": SourceQuery,
    "SourceField": SourceField,
    "SourceRecordReference": SourceRecordReference,
    "SourceConfidenceReport": SourceConfidenceReport,
    "SourceResult": SourceResult,
    "SourceConnectorCapability": SourceConnectorCapability,
    "SourceRequestPolicy": SourceRequestPolicy,
    "SourceRegistryEntry": SourceRegistryEntry,
    "SourceValidationIssue": SourceValidationIssue,
    "SourceValidationReport": SourceValidationReport,
    "SourceBatchResult": SourceBatchResult,
    "SourceFact": SourceFact,
    "SourceMergeReport": SourceMergeReport,
}


# ============================================================
# SECTION 34 - MODULE DIAGNOSTICS
# ============================================================

def get_source_models_metadata() -> dict[str, Any]:
    """
    Return source models module metadata.
    """

    return {
        "name": SOURCE_MODELS_NAME,
        "version": SOURCE_MODELS_VERSION,
        "phase": SOURCE_MODELS_PHASE,
        "status": SOURCE_MODELS_STATUS,
        "model_count": len(SOURCE_MODEL_REGISTRY),
        "generated_at": utc_now(),
    }


def get_source_model_names() -> list[str]:
    """
    Return registered model names.
    """

    return list(SOURCE_MODEL_REGISTRY.keys())


def get_source_enum_summary() -> dict[str, list[str]]:
    """
    Return enum values for diagnostics.
    """

    return {
        "SourceType": [item.value for item in SourceType],
        "SourceStatus": [item.value for item in SourceStatus],
        "SourceReliability": [item.value for item in SourceReliability],
        "SourceAccessMethod": [item.value for item in SourceAccessMethod],
        "SourceDataFormat": [item.value for item in SourceDataFormat],
        "SourceClaimType": [item.value for item in SourceClaimType],
        "SourceConfidenceBand": [item.value for item in SourceConfidenceBand],
        "SourceErrorType": [item.value for item in SourceErrorType],
        "SourceFreshness": [item.value for item in SourceFreshness],
        "SourceAccessPolicy": [item.value for item in SourceAccessPolicy],
    }


# ============================================================
# SECTION 35 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "SOURCE_MODELS_NAME",
    "SOURCE_MODELS_VERSION",
    "SOURCE_MODELS_PHASE",
    "SOURCE_MODELS_STATUS",
    "SourceType",
    "SourceStatus",
    "SourceReliability",
    "SourceAccessMethod",
    "SourceDataFormat",
    "SourceClaimType",
    "SourceConfidenceBand",
    "SourceErrorType",
    "SourceFreshness",
    "SourceAccessPolicy",
    "SourceAttribution",
    "SourceTimestamp",
    "SourceError",
    "SourceWarning",
    "SourceQuery",
    "SourceField",
    "SourceRecordReference",
    "SourceConfidenceReport",
    "SourceResult",
    "SourceConnectorCapability",
    "SourceRequestPolicy",
    "SourceRegistryEntry",
    "SourceValidationIssue",
    "SourceValidationReport",
    "SourceBatchResult",
    "SourceFact",
    "SourceMergeReport",
    "SOURCE_MODEL_REGISTRY",
    "utc_now",
    "stable_hash",
    "clamp_confidence",
    "confidence_band",
    "safe_string",
    "normalize_key",
    "validate_registry_entry",
    "validate_source_result",
    "make_source_query",
    "make_source_error",
    "make_empty_source_result",
    "get_source_models_metadata",
    "get_source_model_names",
    "get_source_enum_summary",
]


# ============================================================
# END OF FILE
# ============================================================