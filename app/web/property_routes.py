============================================================
AUSSEM REAL ESTATE
PHASE 5.50 - ENTERPRISE PROPERTY ROUTES
FILE: app/web/property_routes.py

PURPOSE:
Production-grade FastAPI routing for property address intelligence,
property-profile construction, confidence evaluation, source-grounded
explanations, batch processing, diagnostics, and future persistence.

ARCHITECTURE:
- app/web/routes.py remains the general dashboard and chatbot router.
- this module owns only property-intelligence HTTP contracts.
- business logic remains in app/property_intelligence service modules.
- persistence is abstracted behind a repository interface.
- optional imports fail safely and surface readiness diagnostics.

ENTERPRISE GUARANTEES:
1. Thin routes with delegated domain logic.
2. Strict Pydantic validation.
3. Deterministic request and result fingerprints.
4. Explicit confidence and limitation disclosure.
5. No fabricated MLS, deed, tax, assessor, or parcel records.
6. Graceful degradation when optional modules are unavailable.
7. Traceable request and correlation identifiers.
8. Stable response envelopes for frontend and API consumers.
9. Batch size and timeout safeguards.
10. Future database integration without route-contract changes.
============================================================
"""

from __future__ import annotations

import asyncio
import enum
import hashlib
import json
import logging
import time
from dataclasses import asdict, is_dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from functools import lru_cache
from typing import Any, Callable, Iterable, Mapping, Optional, Protocol, Sequence
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ============================================================
# SECTION 01 - LOGGING
# ============================================================

logger = logging.getLogger("aussem.property_routes")


# ============================================================
# SECTION 02 - ROUTER METADATA
# ============================================================

PROPERTY_ROUTES_NAME = "Aussem Enterprise Property Intelligence Router"
PROPERTY_ROUTES_VERSION = "1.0.0"
PROPERTY_ROUTES_PHASE = "PHASE 5 PART 1.5"
PROPERTY_ROUTES_STATUS = "enterprise_property_routes_active"
PROPERTY_ROUTES_PREFIX = "/properties"

PROPERTY_ROUTES_DESCRIPTION = (
    "Dedicated property-intelligence routing for address analysis, "
    "profile construction, confidence evaluation, source explanations, "
    "batch processing, diagnostics, readiness, and future persistence."
)

DEFAULT_REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_MAX_BATCH_SIZE = 100
DEFAULT_MAX_EVIDENCE_ITEMS = 5000
DEFAULT_COUNTRY_CODE = "US"
DEFAULT_CURRENCY_CODE = "USD"


# ============================================================
# SECTION 03 - OPTIONAL DOMAIN IMPORTS
# ============================================================

IMPORT_ERRORS: dict[str, str] = {}

try:
    from app.property_intelligence.address_intelligence import (
        AddressIntelligenceEngine,
    )
except Exception as exc:  # pragma: no cover
    AddressIntelligenceEngine = None  # type: ignore[assignment]
    IMPORT_ERRORS["address_intelligence"] = str(exc)

try:
    from app.property_intelligence.confidence_engine import (
        AggregationMethod,
        ConfidenceDecisionEngine,
        ConfidenceEngine,
        EvidenceItem,
        EvidenceStatus,
        EvidenceType,
        PolicyMode,
        default_policy,
    )
except Exception as exc:  # pragma: no cover
    AggregationMethod = None  # type: ignore[assignment]
    ConfidenceDecisionEngine = None  # type: ignore[assignment]
    ConfidenceEngine = None  # type: ignore[assignment]
    EvidenceItem = None  # type: ignore[assignment]
    EvidenceStatus = None  # type: ignore[assignment]
    EvidenceType = None  # type: ignore[assignment]
    PolicyMode = None  # type: ignore[assignment]
    default_policy = None  # type: ignore[assignment]
    IMPORT_ERRORS["confidence_engine"] = str(exc)

try:
    from app.property_intelligence.source_explanation_engine import (
        Claim,
        ClaimType,
        ExplanationAudience,
        ExplanationDepth,
        ExplanationOptions,
        ExplanationTone,
        SourceAuthority,
        SourceCategory,
        SourceDescriptor,
        SourceExplanationEngine,
        SupportDirection,
        build_citation,
    )
except Exception as exc:  # pragma: no cover
    Claim = None  # type: ignore[assignment]
    ClaimType = None  # type: ignore[assignment]
    ExplanationAudience = None  # type: ignore[assignment]
    ExplanationDepth = None  # type: ignore[assignment]
    ExplanationOptions = None  # type: ignore[assignment]
    ExplanationTone = None  # type: ignore[assignment]
    SourceAuthority = None  # type: ignore[assignment]
    SourceCategory = None  # type: ignore[assignment]
    SourceDescriptor = None  # type: ignore[assignment]
    SourceExplanationEngine = None  # type: ignore[assignment]
    SupportDirection = None  # type: ignore[assignment]
    build_citation = None  # type: ignore[assignment]
    IMPORT_ERRORS["source_explanation_engine"] = str(exc)

try:
    from app.property_intelligence.property_profile_engine import (
        FieldEvidence,
        ProfileBuildMode,
        PropertyProfile,
        PropertyProfileEngine,
        RiskItem,
        SaleRecord,
    )
except Exception as exc:  # pragma: no cover
    FieldEvidence = None  # type: ignore[assignment]
    ProfileBuildMode = None  # type: ignore[assignment]
    PropertyProfile = None  # type: ignore[assignment]
    PropertyProfileEngine = None  # type: ignore[assignment]
    RiskItem = None  # type: ignore[assignment]
    SaleRecord = None  # type: ignore[assignment]
    IMPORT_ERRORS["property_profile_engine"] = str(exc)


# ============================================================
# SECTION 04 - ROUTER INSTANCE
# ============================================================

router = APIRouter(
    prefix=PROPERTY_ROUTES_PREFIX,
    tags=["Property Intelligence"],
    responses={
        422: {"description": "Property request validation failed"},
        500: {"description": "Property-intelligence operation failed"},
        503: {"description": "Property-intelligence module unavailable"},
    },
)


# ============================================================
# SECTION 05 - INTERNAL ENUMERATIONS
# ============================================================

class StringEnum(str, enum.Enum):
    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]


class PropertyResponseStatus(StringEnum):
    OK = "ok"
    PARTIAL = "partial"
    PLANNED = "planned"
    INVALID = "invalid"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class PersistenceMode(StringEnum):
    NONE = "none"
    DRY_RUN = "dry_run"
    COMMIT = "commit"


class PropertyOperation(StringEnum):
    ROOT = "root"
    HEALTH = "health"
    READINESS = "readiness"
    DIAGNOSTICS = "diagnostics"
    ROUTE_REGISTRY = "route_registry"
    ADDRESS_ANALYSIS = "address_analysis"
    ADDRESS_COMPARISON = "address_comparison"
    PROFILE_BUILD = "profile_build"
    PROFILE_REFRESH = "profile_refresh"
    PROFILE_MERGE = "profile_merge"
    PROFILE_LOOKUP = "profile_lookup"
    CONFIDENCE_EVALUATION = "confidence_evaluation"
    SOURCE_EXPLANATION = "source_explanation"
    BATCH_PROFILE_BUILD = "batch_profile_build"


# ============================================================
# SECTION 06 - BASE REQUEST MODEL
# ============================================================

class EnterpriseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


# ============================================================
# SECTION 07 - REQUEST CONTEXT
# ============================================================

class RequestContextBody(EnterpriseModel):
    request_id: str | None = Field(default=None, max_length=128)
    correlation_id: str | None = Field(default=None, max_length=128)
    session_id: str | None = Field(default=None, max_length=128)
    user_id: str | None = Field(default=None, max_length=128)
    source_channel: str | None = Field(default=None, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================
# SECTION 08 - ADDRESS REQUEST MODELS
# ============================================================

class PropertyAddressBody(EnterpriseModel):
    raw_address: str = Field(..., min_length=3, max_length=500)
    city: str | None = Field(default=None, max_length=128)
    state_code: str | None = Field(default=None, max_length=64)
    postal_code: str | None = Field(default=None, max_length=20)
    county: str | None = Field(default=None, max_length=128)
    country_code: str = Field(default=DEFAULT_COUNTRY_CODE, max_length=8)
    enrich: bool = False

    @field_validator("state_code", "country_code")
    @classmethod
    def uppercase_codes(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class AddressAnalysisRequest(EnterpriseModel):
    address: PropertyAddressBody
    context: RequestContextBody = Field(default_factory=RequestContextBody)


class AddressComparisonRequest(EnterpriseModel):
    left: PropertyAddressBody
    right: PropertyAddressBody
    match_threshold: Decimal = Field(default=Decimal("0.84"), ge=0, le=1)
    context: RequestContextBody = Field(default_factory=RequestContextBody)


# ============================================================
# SECTION 09 - PROFILE IDENTITY AND EVIDENCE MODELS
# ============================================================

class PropertyIdentityBody(EnterpriseModel):
    property_id: str = Field(..., min_length=1, max_length=128)
    external_ids: dict[str, str] = Field(default_factory=dict)
    parcel_number: str | None = Field(default=None, max_length=128)
    tax_account_number: str | None = Field(default=None, max_length=128)


class FieldEvidenceBody(EnterpriseModel):
    field_path: str = Field(..., min_length=1, max_length=255)
    value: Any = None
    source_name: str = Field(..., min_length=1, max_length=255)
    source_id: str | None = Field(default=None, max_length=255)
    confidence: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    quality: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    freshness: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    authority: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    observed_at: datetime | None = None
    retrieved_at: datetime | None = None
    effective_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SaleRecordBody(EnterpriseModel):
    sale_date: date | None = None
    sale_price: Decimal | None = Field(default=None, ge=0)
    document_id: str | None = Field(default=None, max_length=255)
    buyer_names: list[str] = Field(default_factory=list)
    seller_names: list[str] = Field(default_factory=list)
    transaction_type: str | None = Field(default=None, max_length=128)
    arms_length: bool | None = None
    source_name: str | None = Field(default=None, max_length=255)
    confidence: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)


class RiskItemBody(EnterpriseModel):
    category: str = Field(..., min_length=1, max_length=128)
    severity: str = Field(..., min_length=1, max_length=64)
    score: Decimal = Field(..., ge=0, le=1)
    title: str = Field(..., min_length=1, max_length=255)
    summary: str | None = Field(default=None, max_length=5000)
    evidence: list[Any] = Field(default_factory=list)
    mitigations: list[Any] = Field(default_factory=list)
    confidence: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    expires_at: datetime | None = None


# ============================================================
# SECTION 10 - PROFILE BUILD REQUESTS
# ============================================================

class PropertyProfileBuildRequest(EnterpriseModel):
    identity: PropertyIdentityBody
    evidence: list[FieldEvidenceBody] = Field(default_factory=list)
    address: PropertyAddressBody | None = None
    sales_history: list[SaleRecordBody] = Field(default_factory=list)
    risks: list[RiskItemBody] = Field(default_factory=list)
    mode: str = Field(default="create")
    persistence: PersistenceMode = PersistenceMode.NONE
    metadata: dict[str, Any] = Field(default_factory=dict)
    context: RequestContextBody = Field(default_factory=RequestContextBody)

    @field_validator("evidence")
    @classmethod
    def validate_evidence_size(
        cls,
        value: list[FieldEvidenceBody],
    ) -> list[FieldEvidenceBody]:
        if len(value) > DEFAULT_MAX_EVIDENCE_ITEMS:
            raise ValueError(
                f"evidence exceeds maximum of {DEFAULT_MAX_EVIDENCE_ITEMS} items"
            )
        return value


class PropertyProfileRefreshRequest(EnterpriseModel):
    profile: dict[str, Any]
    evidence: list[FieldEvidenceBody] = Field(default_factory=list)
    address: PropertyAddressBody | None = None
    sales_history: list[SaleRecordBody] | None = None
    risks: list[RiskItemBody] | None = None
    persistence: PersistenceMode = PersistenceMode.NONE
    metadata: dict[str, Any] = Field(default_factory=dict)
    context: RequestContextBody = Field(default_factory=RequestContextBody)


class PropertyProfileMergeRequest(EnterpriseModel):
    left_profile: dict[str, Any]
    right_profile: dict[str, Any]
    persistence: PersistenceMode = PersistenceMode.NONE
    context: RequestContextBody = Field(default_factory=RequestContextBody)


class BatchPropertyProfileBuildRequest(EnterpriseModel):
    requests: dict[str, PropertyProfileBuildRequest]
    fail_fast: bool = False
    context: RequestContextBody = Field(default_factory=RequestContextBody)

    @model_validator(mode="after")
    def validate_batch_size(self) -> "BatchPropertyProfileBuildRequest":
        if len(self.requests) > DEFAULT_MAX_BATCH_SIZE:
            raise ValueError(
                f"batch exceeds maximum of {DEFAULT_MAX_BATCH_SIZE} requests"
            )
        return self


# ============================================================
# SECTION 11 - CONFIDENCE REQUEST MODELS
# ============================================================

class ConfidenceEvidenceBody(EnterpriseModel):
    evidence_id: str = Field(..., min_length=1, max_length=255)
    evidence_type: str = Field(default="derived")
    source_name: str = Field(..., min_length=1, max_length=255)
    value: Any = None
    confidence: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    reliability: Decimal = Field(default=Decimal("0.60"), ge=0, le=1)
    quality: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    freshness: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    relevance: Decimal = Field(default=Decimal("1.00"), ge=0, le=1)
    independence: Decimal = Field(default=Decimal("1.00"), ge=0, le=1)
    status: str = Field(default="active")
    observed_at: datetime | None = None
    retrieved_at: datetime | None = None
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    source_record_id: str | None = None
    field_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConfidenceEvaluationRequest(EnterpriseModel):
    evidence: list[ConfidenceEvidenceBody]
    aggregation_method: str = Field(default="weighted_mean")
    prior: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    minimum_desired_evidence: int = Field(default=2, ge=0, le=1000)
    impact: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    field_path: str | None = None
    policy_mode: str = Field(default="balanced")
    context: RequestContextBody = Field(default_factory=RequestContextBody)

    @field_validator("evidence")
    @classmethod
    def validate_confidence_evidence(
        cls,
        value: list[ConfidenceEvidenceBody],
    ) -> list[ConfidenceEvidenceBody]:
        if not value:
            raise ValueError("at least one confidence evidence item is required")
        if len(value) > DEFAULT_MAX_EVIDENCE_ITEMS:
            raise ValueError(
                f"confidence evidence exceeds {DEFAULT_MAX_EVIDENCE_ITEMS} items"
            )
        return value


# ============================================================
# SECTION 12 - SOURCE EXPLANATION REQUEST MODELS
# ============================================================

class SourceDescriptorBody(EnterpriseModel):
    source_id: str = Field(..., min_length=1, max_length=255)
    source_name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(default="other")
    authority: str = Field(default="unknown")
    provider_name: str | None = None
    record_id: str | None = None
    record_type: str | None = None
    source_url: str | None = None
    document_name: str | None = None
    dataset_name: str | None = None
    jurisdiction: str | None = None
    observed_at: datetime | None = None
    retrieved_at: datetime | None = None
    effective_at: datetime | None = None
    reliability: Decimal = Field(default=Decimal("0.60"), ge=0, le=1)
    quality: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    freshness: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    payload_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CitationBody(EnterpriseModel):
    source: SourceDescriptorBody
    label: str | None = None
    locator: str | None = None
    excerpt: str | None = Field(default=None, max_length=4000)
    field_path: str | None = None
    value: Any = None
    confidence: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    relevance: Decimal = Field(default=Decimal("1.00"), ge=0, le=1)
    support_direction: str = Field(default="supports")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExplanationClaimBody(EnterpriseModel):
    claim_id: str | None = None
    statement: str = Field(..., min_length=1, max_length=10000)
    claim_type: str = Field(default="fact")
    field_path: str | None = None
    value: Any = None
    unit: str | None = None
    currency_code: str | None = DEFAULT_CURRENCY_CODE
    confidence: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    effective_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExplanationRequest(EnterpriseModel):
    subject_type: str = Field(default="property", max_length=128)
    subject_id: str = Field(..., min_length=1, max_length=255)
    claim: ExplanationClaimBody
    citations: list[CitationBody] = Field(default_factory=list)
    audience: str = Field(default="consumer")
    depth: str = Field(default="standard")
    tone: str = Field(default="professional")
    include_sources: bool = True
    include_conflicts: bool = True
    include_confidence: bool = True
    include_lineage: bool = False
    include_limitations: bool = True
    limitations: list[str] = Field(default_factory=list)
    transformations: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    context: RequestContextBody = Field(default_factory=RequestContextBody)


# ============================================================
# SECTION 13 - RESPONSE CONTRACTS
# ============================================================

class EnterpriseErrorBody(EnterpriseModel):
    code: str
    message: str
    details: Any = None
    retryable: bool = False


class EnterpriseResponseBody(EnterpriseModel):
    platform: str = "Aussem1"
    module: str
    operation: str
    status: str
    message: str | None = None
    data: Any = None
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    error: EnterpriseErrorBody | None = None
    request_id: str
    correlation_id: str | None = None
    timestamp: str
    duration_ms: int
    router: dict[str, Any]
    fingerprint: str | None = None


# ============================================================
# SECTION 14 - SERVICE CONTAINER
# ============================================================

class PropertyServiceContainer:
    def __init__(self) -> None:
        self.address_engine = (
            AddressIntelligenceEngine()
            if AddressIntelligenceEngine is not None
            else None
        )
        self.confidence_engine = (
            ConfidenceEngine()
            if ConfidenceEngine is not None
            else None
        )
        self.confidence_decision_engine = (
            ConfidenceDecisionEngine()
            if ConfidenceDecisionEngine is not None
            else None
        )
        self.explanation_engine = (
            SourceExplanationEngine()
            if SourceExplanationEngine is not None
            else None
        )
        self.profile_engine = (
            PropertyProfileEngine(
                address_engine=self.address_engine,
                confidence_engine=self.confidence_engine,
                explanation_engine=self.explanation_engine,
            )
            if PropertyProfileEngine is not None
            else None
        )

    def module_status(self) -> dict[str, Any]:
        return {
            "address_intelligence": {
                "available": self.address_engine is not None,
                "import_error": IMPORT_ERRORS.get("address_intelligence"),
            },
            "confidence_engine": {
                "available": self.confidence_engine is not None,
                "decision_engine_available": (
                    self.confidence_decision_engine is not None
                ),
                "import_error": IMPORT_ERRORS.get("confidence_engine"),
            },
            "source_explanation_engine": {
                "available": self.explanation_engine is not None,
                "import_error": IMPORT_ERRORS.get(
                    "source_explanation_engine"
                ),
            },
            "property_profile_engine": {
                "available": self.profile_engine is not None,
                "import_error": IMPORT_ERRORS.get("property_profile_engine"),
            },
        }

    def required_ready(self) -> bool:
        return all(
            (
                self.address_engine is not None,
                self.confidence_engine is not None,
                self.confidence_decision_engine is not None,
                self.explanation_engine is not None,
                self.profile_engine is not None,
            )
        )


@lru_cache(maxsize=1)
def get_services() -> PropertyServiceContainer:
    return PropertyServiceContainer()


# ============================================================
# SECTION 15 - SERIALIZATION UTILITIES
# ============================================================

def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def generate_request_id() -> str:
    return f"aussem-property-{uuid4()}"


def serialize(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value):
        return serialize(asdict(value))
    if isinstance(value, BaseModel):
        return serialize(value.model_dump())
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [serialize(item) for item in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return serialize(value.to_dict())
    return value


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        jsonable_encoder(serialize(value)),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ============================================================
# SECTION 16 - RESPONSE FACTORY
# ============================================================

def build_response(
    *,
    operation: PropertyOperation,
    response_status: PropertyResponseStatus | str,
    data: Any,
    started_at: float,
    request_id_value: str,
    correlation_id: str | None = None,
    message: str | None = None,
    warnings: Optional[Sequence[str]] = None,
    limitations: Optional[Sequence[str]] = None,
    error: EnterpriseErrorBody | None = None,
    fingerprint_payload: Any = None,
) -> dict[str, Any]:
    duration_ms = int((time.perf_counter() - started_at) * 1000)
    status_text = (
        response_status.value
        if isinstance(response_status, PropertyResponseStatus)
        else str(response_status)
    )
    serialized_data = serialize(data)
    fingerprint = (
        stable_hash(
            fingerprint_payload
            if fingerprint_payload is not None
            else serialized_data
        )
        if serialized_data is not None
        else None
    )

    return EnterpriseResponseBody(
        module="property_intelligence",
        operation=operation.value,
        status=status_text,
        message=message,
        data=serialized_data,
        warnings=list(warnings or []),
        limitations=list(limitations or []),
        error=error,
        request_id=request_id_value,
        correlation_id=correlation_id,
        timestamp=utc_now_iso(),
        duration_ms=duration_ms,
        router={
            "name": PROPERTY_ROUTES_NAME,
            "version": PROPERTY_ROUTES_VERSION,
            "phase": PROPERTY_ROUTES_PHASE,
            "status": PROPERTY_ROUTES_STATUS,
        },
        fingerprint=fingerprint,
    ).model_dump()


# ============================================================
# SECTION 17 - ROUTE ERROR TYPE
# ============================================================

class PropertyRouteError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        details: Any = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.retryable = retryable


# ============================================================
# SECTION 18 - ERROR RESPONSE HANDLER
# ============================================================

def route_exception_response(
    *,
    operation: PropertyOperation,
    error: Exception,
    started_at: float,
    request_id_value: str,
    correlation_id: str | None,
) -> JSONResponse:
    if isinstance(error, PropertyRouteError):
        status_code = error.status_code
        error_body = EnterpriseErrorBody(
            code=error.code,
            message=error.message,
            details=serialize(error.details),
            retryable=error.retryable,
        )
        response_status = (
            PropertyResponseStatus.UNAVAILABLE
            if status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            else PropertyResponseStatus.INVALID
        )
    elif isinstance(error, asyncio.TimeoutError):
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
        error_body = EnterpriseErrorBody(
            code="property_operation_timeout",
            message=(
                "Property intelligence operation exceeded the allowed timeout."
            ),
            retryable=True,
        )
        response_status = PropertyResponseStatus.ERROR
    else:
        logger.exception("Unhandled property route error", exc_info=error)
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_body = EnterpriseErrorBody(
            code="property_internal_error",
            message="An internal property-intelligence error occurred.",
            details={
                "type": error.__class__.__name__,
                "message": str(error),
            },
            retryable=False,
        )
        response_status = PropertyResponseStatus.ERROR

    payload = build_response(
        operation=operation,
        response_status=response_status,
        data=None,
        started_at=started_at,
        request_id_value=request_id_value,
        correlation_id=correlation_id,
        message=error_body.message,
        error=error_body,
    )
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(payload),
    )


# ============================================================
# SECTION 19 - MODULE AND ENUM VALIDATION
# ============================================================

def require_module(module_name: str, module_value: Any) -> Any:
    if module_value is None:
        raise PropertyRouteError(
            code="module_unavailable",
            message=f"Required module is unavailable: {module_name}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={
                "module": module_name,
                "import_error": IMPORT_ERRORS.get(module_name),
            },
        )
    return module_value


def enum_value(enum_type: Any, value: str, field_name: str) -> Any:
    try:
        return enum_type(value)
    except Exception as exc:
        valid_values = (
            [member.value for member in enum_type]
            if enum_type is not None
            else []
        )
        raise PropertyRouteError(
            code="invalid_enum_value",
            message=f"Invalid value for {field_name}: {value}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={
                "field": field_name,
                "received": value,
                "valid_values": valid_values,
            },
        ) from exc


# ============================================================
# SECTION 20 - SERVICE EXECUTION SAFEGUARD
# ============================================================

async def execute_service_call(
    callback: Callable[[], Any],
    *,
    timeout_seconds: int = DEFAULT_REQUEST_TIMEOUT_SECONDS,
) -> Any:
    return await asyncio.wait_for(
        asyncio.to_thread(callback),
        timeout=timeout_seconds,
    )


# ============================================================
# SECTION 21 - REQUEST IDENTIFIER HELPERS
# ============================================================

def resolve_request_id(
    context: RequestContextBody | None,
    header_request_id: str | None,
) -> str:
    return (
        header_request_id
        or (context.request_id if context else None)
        or generate_request_id()
    )


def resolve_correlation_id(
    context: RequestContextBody | None,
    header_correlation_id: str | None,
) -> str | None:
    return (
        header_correlation_id
        or (context.correlation_id if context else None)
    )


# ============================================================
# SECTION 22 - DOMAIN CONVERSION HELPERS
# ============================================================

def to_field_evidence(items: Sequence[FieldEvidenceBody]) -> list[Any]:
    domain_type = require_module("property_profile_engine", FieldEvidence)
    return [
        domain_type(
            field_path=item.field_path,
            value=item.value,
            source_name=item.source_name,
            source_id=item.source_id,
            confidence=item.confidence,
            quality=item.quality,
            freshness=item.freshness,
            authority=item.authority,
            observed_at=item.observed_at,
            retrieved_at=item.retrieved_at,
            effective_at=item.effective_at,
            metadata=item.metadata,
        )
        for item in items
    ]


def to_sale_records(items: Sequence[SaleRecordBody]) -> list[Any]:
    domain_type = require_module("property_profile_engine", SaleRecord)
    return [
        domain_type(
            sale_date=item.sale_date,
            sale_price=item.sale_price,
            document_id=item.document_id,
            buyer_names=item.buyer_names,
            seller_names=item.seller_names,
            transaction_type=item.transaction_type,
            arms_length=item.arms_length,
            source_name=item.source_name,
            confidence=item.confidence,
        )
        for item in items
    ]


def to_risk_items(items: Sequence[RiskItemBody]) -> list[Any]:
    domain_type = require_module("property_profile_engine", RiskItem)
    return [
        domain_type(
            category=item.category,
            severity=item.severity,
            score=item.score,
            title=item.title,
            summary=item.summary,
            evidence=item.evidence,
            mitigations=item.mitigations,
            confidence=item.confidence,
            expires_at=item.expires_at,
        )
        for item in items
    ]


def to_confidence_evidence(
    items: Sequence[ConfidenceEvidenceBody],
) -> list[Any]:
    domain_type = require_module("confidence_engine", EvidenceItem)
    type_enum = require_module("confidence_engine", EvidenceType)
    status_enum = require_module("confidence_engine", EvidenceStatus)

    return [
        domain_type(
            evidence_id=item.evidence_id,
            evidence_type=enum_value(
                type_enum,
                item.evidence_type,
                "evidence_type",
            ),
            source_name=item.source_name,
            value=item.value,
            confidence=item.confidence,
            reliability=item.reliability,
            quality=item.quality,
            freshness=item.freshness,
            relevance=item.relevance,
            independence=item.independence,
            status=enum_value(status_enum, item.status, "status"),
            observed_at=item.observed_at,
            retrieved_at=item.retrieved_at,
            effective_at=item.effective_at,
            expires_at=item.expires_at,
            source_record_id=item.source_record_id,
            field_path=item.field_path,
            metadata=item.metadata,
        )
        for item in items
    ]


def to_source_descriptor(item: SourceDescriptorBody) -> Any:
    domain_type = require_module(
        "source_explanation_engine",
        SourceDescriptor,
    )
    category_enum = require_module(
        "source_explanation_engine",
        SourceCategory,
    )
    authority_enum = require_module(
        "source_explanation_engine",
        SourceAuthority,
    )

    return domain_type(
        source_id=item.source_id,
        source_name=item.source_name,
        category=enum_value(category_enum, item.category, "category"),
        authority=enum_value(authority_enum, item.authority, "authority"),
        provider_name=item.provider_name,
        record_id=item.record_id,
        record_type=item.record_type,
        source_url=item.source_url,
        document_name=item.document_name,
        dataset_name=item.dataset_name,
        jurisdiction=item.jurisdiction,
        observed_at=item.observed_at,
        retrieved_at=item.retrieved_at,
        effective_at=item.effective_at,
        reliability=item.reliability,
        quality=item.quality,
        freshness=item.freshness,
        payload_hash=item.payload_hash,
        metadata=item.metadata,
    )


def to_citations(items: Sequence[CitationBody]) -> list[Any]:
    builder = require_module("source_explanation_engine", build_citation)
    direction_enum = require_module(
        "source_explanation_engine",
        SupportDirection,
    )

    return [
        builder(
            source=to_source_descriptor(item.source),
            label=item.label,
            locator=item.locator,
            excerpt=item.excerpt,
            field_path=item.field_path,
            value=item.value,
            confidence=item.confidence,
            relevance=item.relevance,
            support_direction=enum_value(
                direction_enum,
                item.support_direction,
                "support_direction",
            ),
            metadata=item.metadata,
        )
        for item in items
    ]


# ============================================================
# SECTION 23 - PROFILE DESERIALIZATION
# ============================================================

def profile_from_dict(payload: Mapping[str, Any]) -> Any:
    require_module("property_profile_engine", PropertyProfile)

    from app.property_intelligence.property_profile_engine import (
        AddressProfile,
        FieldDecision,
        FieldEvidence as DomainFieldEvidence,
        FieldResolution,
        ListingProfile,
        MarketProfile,
        OwnershipProfile,
        ProfileQuality,
        ProfileQualityLevel,
        ProfileStatus,
        PropertyIdentity,
        RiskItem as DomainRiskItem,
        SaleRecord as DomainSaleRecord,
        StructuralProfile,
        TaxProfile,
        ValuationProfile,
    )

    def decimal_or_none(value: Any) -> Decimal | None:
        if value is None or value == "":
            return None
        return Decimal(str(value))

    def parse_date(value: Any) -> date | None:
        if not value:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        return date.fromisoformat(str(value))

    def parse_datetime(value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value))

    identity_payload = dict(payload["identity"])
    identity = PropertyIdentity(**identity_payload)

    address_payload = dict(payload.get("address", {}))
    for key in ("latitude", "longitude", "address_confidence"):
        if key in address_payload:
            address_payload[key] = decimal_or_none(address_payload[key])
    address = AddressProfile(**address_payload)

    structure_payload = dict(payload.get("structure", {}))
    for key in (
        "bedrooms",
        "bathrooms",
        "living_area_sqft",
        "lot_size_sqft",
        "stories",
        "garage_spaces",
    ):
        if key in structure_payload:
            structure_payload[key] = decimal_or_none(structure_payload[key])
    structure = StructuralProfile(**structure_payload)

    ownership_payload = dict(payload.get("ownership", {}))
    if ownership_payload.get("deed_date"):
        ownership_payload["deed_date"] = parse_date(
            ownership_payload["deed_date"]
        )
    if "ownership_confidence" in ownership_payload:
        ownership_payload["ownership_confidence"] = Decimal(
            str(ownership_payload["ownership_confidence"])
        )
    ownership = OwnershipProfile(**ownership_payload)

    listing_payload = dict(payload.get("listing", {}))
    for key in ("list_price", "original_list_price"):
        if key in listing_payload:
            listing_payload[key] = decimal_or_none(listing_payload[key])
    for key in ("listing_date", "pending_date", "expiration_date"):
        if listing_payload.get(key):
            listing_payload[key] = parse_date(listing_payload[key])
    listing = ListingProfile(**listing_payload)

    tax_payload = dict(payload.get("tax", {}))
    for key in (
        "assessed_value",
        "land_value",
        "improvement_value",
        "annual_tax_amount",
        "assessment_ratio",
        "exemption_amount",
        "tax_rate",
    ):
        if key in tax_payload:
            tax_payload[key] = decimal_or_none(tax_payload[key])
    tax = TaxProfile(**tax_payload)

    valuation_payload = dict(payload.get("valuation", {}))
    for key in (
        "estimated_value",
        "value_low",
        "value_high",
        "price_per_sqft",
        "confidence",
    ):
        if key in valuation_payload:
            valuation_payload[key] = decimal_or_none(valuation_payload[key])
    if valuation_payload.get("valuation_date"):
        valuation_payload["valuation_date"] = parse_datetime(
            valuation_payload["valuation_date"]
        )
    valuation = ValuationProfile(**valuation_payload)

    market_payload = dict(payload.get("market", {}))
    for key in (
        "median_sale_price",
        "median_price_per_sqft",
        "median_days_on_market",
        "months_of_supply",
        "year_over_year_appreciation",
        "sale_to_list_ratio",
        "confidence",
    ):
        if key in market_payload:
            market_payload[key] = decimal_or_none(market_payload[key])
    if market_payload.get("as_of_date"):
        market_payload["as_of_date"] = parse_date(
            market_payload["as_of_date"]
        )
    market = MarketProfile(**market_payload)

    sales_history = []
    for item in payload.get("sales_history", []):
        record = dict(item)
        record["sale_date"] = parse_date(record.get("sale_date"))
        record["sale_price"] = decimal_or_none(record.get("sale_price"))
        record["confidence"] = Decimal(str(record.get("confidence", "0.5")))
        sales_history.append(DomainSaleRecord(**record))

    risks = []
    for item in payload.get("risks", []):
        risk = dict(item)
        risk["score"] = Decimal(str(risk.get("score", "0")))
        risk["confidence"] = Decimal(str(risk.get("confidence", "0.5")))
        risk["expires_at"] = parse_datetime(risk.get("expires_at"))
        risks.append(DomainRiskItem(**risk))

    resolutions: dict[str, Any] = {}
    for field_path, item in payload.get("resolutions", {}).items():
        candidates = []
        for candidate_payload in item.get("candidates", []):
            candidate = dict(candidate_payload)
            for key in ("confidence", "quality", "freshness", "authority"):
                candidate[key] = Decimal(str(candidate.get(key, "0.5")))
            for key in ("observed_at", "retrieved_at", "effective_at"):
                candidate[key] = parse_datetime(candidate.get(key))
            candidates.append(DomainFieldEvidence(**candidate))

        resolutions[field_path] = FieldResolution(
            field_path=item["field_path"],
            selected_value=item.get("selected_value"),
            selected_source_name=item.get("selected_source_name"),
            selected_source_id=item.get("selected_source_id"),
            confidence=Decimal(str(item.get("confidence", "0.5"))),
            decision=FieldDecision(item.get("decision", "deferred")),
            candidates=candidates,
            reason=item.get("reason", ""),
            conflict_score=Decimal(str(item.get("conflict_score", "0"))),
            metadata=item.get("metadata", {}),
        )

    quality_payload = payload.get("quality")
    quality = None
    if quality_payload:
        quality = ProfileQuality(
            completeness_score=Decimal(
                str(quality_payload.get("completeness_score", "0"))
            ),
            freshness_score=Decimal(
                str(quality_payload.get("freshness_score", "0"))
            ),
            confidence_score=Decimal(
                str(quality_payload.get("confidence_score", "0"))
            ),
            consistency_score=Decimal(
                str(quality_payload.get("consistency_score", "0"))
            ),
            source_diversity_score=Decimal(
                str(quality_payload.get("source_diversity_score", "0"))
            ),
            overall_score=Decimal(
                str(quality_payload.get("overall_score", "0"))
            ),
            level=ProfileQualityLevel(
                quality_payload.get("level", "invalid")
            ),
            missing_fields=quality_payload.get("missing_fields", []),
            stale_fields=quality_payload.get("stale_fields", []),
            conflicted_fields=quality_payload.get("conflicted_fields", []),
            warnings=quality_payload.get("warnings", []),
        )

    return PropertyProfile(
        identity=identity,
        address=address,
        structure=structure,
        ownership=ownership,
        listing=listing,
        sales_history=sales_history,
        tax=tax,
        valuation=valuation,
        market=market,
        risks=risks,
        resolutions=resolutions,
        quality=quality,
        status=ProfileStatus(payload.get("status", "draft")),
        profile_version=payload.get("profile_version", "1.0"),
        built_at=parse_datetime(payload.get("built_at")) or datetime.now(UTC),
        refreshed_at=parse_datetime(payload.get("refreshed_at")),
        expires_at=parse_datetime(payload.get("expires_at")),
        fingerprint=payload.get("fingerprint"),
        metadata=payload.get("metadata", {}),
    )


# ============================================================
# SECTION 24 - PERSISTENCE PROTOCOL
# ============================================================

class PropertyProfileRepositoryProtocol(Protocol):
    async def get(self, property_id: str) -> Any | None:
        ...

    async def save(self, profile: Any) -> Mapping[str, Any]:
        ...

    async def delete(self, property_id: str) -> bool:
        ...


# ============================================================
# SECTION 25 - DEFAULT NON-PERSISTENT REPOSITORY
# ============================================================

class PropertyProfileRepository:
    async def get(self, property_id: str) -> Any | None:
        return None

    async def save(self, profile: Any) -> Mapping[str, Any]:
        property_id = getattr(
            getattr(profile, "identity", None),
            "property_id",
            None,
        )
        return {
            "persisted": False,
            "mode": "repository_not_configured",
            "property_id": property_id,
        }

    async def delete(self, property_id: str) -> bool:
        return False


_repository = PropertyProfileRepository()


def get_profile_repository() -> PropertyProfileRepository:
    return _repository


# ============================================================
# SECTION 26 - OPTIONAL PERSISTENCE EXECUTION
# ============================================================

async def persist_profile_if_requested(
    *,
    mode: PersistenceMode,
    profile: Any,
    repository: PropertyProfileRepositoryProtocol,
) -> dict[str, Any]:
    if mode == PersistenceMode.NONE:
        return {
            "requested": False,
            "persisted": False,
            "mode": mode.value,
        }

    if mode == PersistenceMode.DRY_RUN:
        return {
            "requested": True,
            "persisted": False,
            "validated": True,
            "mode": mode.value,
        }

    result = dict(await repository.save(profile))
    return {
        "requested": True,
        "persisted": bool(result.get("persisted")),
        "mode": mode.value,
        "repository_result": result,
    }


# ============================================================
# SECTION 27 - ROOT ROUTE
# ============================================================

@router.get("")
async def property_root(
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> dict[str, Any]:
    started = time.perf_counter()
    request_id_value = x_request_id or generate_request_id()
    services = get_services()

    return build_response(
        operation=PropertyOperation.ROOT,
        response_status=PropertyResponseStatus.OK,
        data={
            "name": PROPERTY_ROUTES_NAME,
            "description": PROPERTY_ROUTES_DESCRIPTION,
            "version": PROPERTY_ROUTES_VERSION,
            "phase": PROPERTY_ROUTES_PHASE,
            "status": PROPERTY_ROUTES_STATUS,
            "prefix": PROPERTY_ROUTES_PREFIX,
            "modules": services.module_status(),
        },
        started_at=started,
        request_id_value=request_id_value,
        message="Property intelligence router is active.",
    )


# ============================================================
# SECTION 28 - HEALTH ROUTE
# ============================================================

@router.get("/health")
async def property_health(
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> dict[str, Any]:
    started = time.perf_counter()
    request_id_value = x_request_id or generate_request_id()
    services = get_services()

    return build_response(
        operation=PropertyOperation.HEALTH,
        response_status=PropertyResponseStatus.OK,
        data={
            "alive": True,
            "router_active": True,
            "required_modules_ready": services.required_ready(),
            "modules": services.module_status(),
        },
        started_at=started,
        request_id_value=request_id_value,
        message="Property route health check completed.",
    )


# ============================================================
# SECTION 29 - READINESS ROUTE
# ============================================================

@router.get("/readiness")
async def property_readiness(
    response: Response,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> dict[str, Any]:
    started = time.perf_counter()
    request_id_value = x_request_id or generate_request_id()
    services = get_services()
    ready = services.required_ready()

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return build_response(
        operation=PropertyOperation.READINESS,
        response_status=(
            PropertyResponseStatus.OK
            if ready
            else PropertyResponseStatus.UNAVAILABLE
        ),
        data={
            "ready": ready,
            "modules": services.module_status(),
            "import_errors": IMPORT_ERRORS,
        },
        started_at=started,
        request_id_value=request_id_value,
        message=(
            "Property intelligence is ready."
            if ready
            else "Property intelligence is not fully ready."
        ),
    )


# ============================================================
# SECTION 30 - DIAGNOSTICS ROUTE
# ============================================================

@router.get("/diagnostics")
async def property_diagnostics(
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
    ),
) -> dict[str, Any]:
    started = time.perf_counter()
    request_id_value = x_request_id or generate_request_id()
    services = get_services()

    return build_response(
        operation=PropertyOperation.DIAGNOSTICS,
        response_status=PropertyResponseStatus.OK,
        data={
            "router": {
                "name": PROPERTY_ROUTES_NAME,
                "version": PROPERTY_ROUTES_VERSION,
                "phase": PROPERTY_ROUTES_PHASE,
                "status": PROPERTY_ROUTES_STATUS,
                "prefix": PROPERTY_ROUTES_PREFIX,
            },
            "runtime": {
                "timestamp": utc_now_iso(),
                "default_timeout_seconds": (
                    DEFAULT_REQUEST_TIMEOUT_SECONDS
                ),
                "maximum_batch_size": DEFAULT_MAX_BATCH_SIZE,
                "maximum_evidence_items": DEFAULT_MAX_EVIDENCE_ITEMS,
            },
            "modules": services.module_status(),
            "import_errors": IMPORT_ERRORS,
            "persistence": {
                "configured": False,
                "repository": _repository.__class__.__name__,
            },
            "external_connectivity": {
                "live_mls": False,
                "live_assessor": False,
                "live_deed": False,
                "live_tax": False,
                "live_geocoder": False,
                "live_parcel_gis": False,
            },
            "safety": {
                "fabricated_records_allowed": False,
                "confidence_disclosure_required": True,
                "source_disclosure_required": True,
            },
        },
        started_at=started,
        request_id_value=request_id_value,
        correlation_id=x_correlation_id,
        message="Property diagnostics generated.",
    )


# ============================================================
# SECTION 31 - ROUTE REGISTRY
# ============================================================

@router.get("/registry/routes")
async def property_route_registry(
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> dict[str, Any]:
    started = time.perf_counter()
    request_id_value = x_request_id or generate_request_id()

    return build_response(
        operation=PropertyOperation.ROUTE_REGISTRY,
        response_status=PropertyResponseStatus.OK,
        data={
            "system_routes": [
                {"method": "GET", "path": "/properties"},
                {"method": "GET", "path": "/properties/health"},
                {"method": "GET", "path": "/properties/readiness"},
                {"method": "GET", "path": "/properties/diagnostics"},
                {"method": "GET", "path": "/properties/registry/routes"},
            ],
            "address_routes": [
                {"method": "POST", "path": "/properties/address/analyze"},
                {"method": "POST", "path": "/properties/address/compare"},
            ],
            "profile_routes": [
                {"method": "POST", "path": "/properties/profile/build"},
                {"method": "POST", "path": "/properties/profile/refresh"},
                {"method": "POST", "path": "/properties/profile/merge"},
                {"method": "GET", "path": "/properties/{property_id}"},
            ],
            "confidence_routes": [
                {
                    "method": "POST",
                    "path": "/properties/confidence/evaluate",
                },
            ],
            "explanation_routes": [
                {"method": "POST", "path": "/properties/explain"},
            ],
            "batch_routes": [
                {
                    "method": "POST",
                    "path": "/properties/batch/profile/build",
                },
            ],
        },
        started_at=started,
        request_id_value=request_id_value,
        message="Property route registry loaded.",
    )


# ============================================================
# SECTION 32 - ADDRESS ANALYSIS ROUTE
# ============================================================

@router.post("/address/analyze")
async def property_address_analyze(
    request_body: AddressAnalysisRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
    ),
    services: PropertyServiceContainer = Depends(get_services),
) -> JSONResponse | dict[str, Any]:
    started = time.perf_counter()
    request_id_value = resolve_request_id(
        request_body.context,
        x_request_id,
    )
    correlation_id = resolve_correlation_id(
        request_body.context,
        x_correlation_id,
    )

    try:
        engine = require_module(
            "address_intelligence",
            services.address_engine,
        )
        analysis = await execute_service_call(
            lambda: engine.analyze(
                request_body.address.raw_address,
                city=request_body.address.city,
                state_code=request_body.address.state_code,
                postal_code=request_body.address.postal_code,
                county=request_body.address.county,
                country_code=request_body.address.country_code,
                enrich=request_body.address.enrich,
            )
        )

        warnings = [
            item.message
            for item in getattr(analysis, "issues", [])
            if getattr(item, "severity", "") == "warning"
        ]
        limitations: list[str] = []
        if request_body.address.enrich and not getattr(
            engine,
            "geocoding_providers",
            [],
        ):
            limitations.append(
                "Enrichment was requested, but no geocoding providers are configured."
            )

        return build_response(
            operation=PropertyOperation.ADDRESS_ANALYSIS,
            response_status=(
                PropertyResponseStatus.OK
                if getattr(analysis, "is_valid", True)
                else PropertyResponseStatus.PARTIAL
            ),
            data=analysis,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message="Address intelligence analysis completed.",
            warnings=warnings,
            limitations=limitations,
        )
    except Exception as exc:
        return route_exception_response(
            operation=PropertyOperation.ADDRESS_ANALYSIS,
            error=exc,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
        )


# ============================================================
# SECTION 33 - ADDRESS COMPARISON ROUTE
# ============================================================

@router.post("/address/compare")
async def property_address_compare(
    request_body: AddressComparisonRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
    ),
    services: PropertyServiceContainer = Depends(get_services),
) -> JSONResponse | dict[str, Any]:
    started = time.perf_counter()
    request_id_value = resolve_request_id(
        request_body.context,
        x_request_id,
    )
    correlation_id = resolve_correlation_id(
        request_body.context,
        x_correlation_id,
    )

    try:
        engine = require_module(
            "address_intelligence",
            services.address_engine,
        )
        left = await execute_service_call(
            lambda: engine.analyze(
                request_body.left.raw_address,
                city=request_body.left.city,
                state_code=request_body.left.state_code,
                postal_code=request_body.left.postal_code,
                county=request_body.left.county,
                country_code=request_body.left.country_code,
                enrich=request_body.left.enrich,
            )
        )
        right = await execute_service_call(
            lambda: engine.analyze(
                request_body.right.raw_address,
                city=request_body.right.city,
                state_code=request_body.right.state_code,
                postal_code=request_body.right.postal_code,
                county=request_body.right.county,
                country_code=request_body.right.country_code,
                enrich=request_body.right.enrich,
            )
        )
        comparison = await execute_service_call(
            lambda: engine.matcher.compare(
                left,
                right,
                match_threshold=request_body.match_threshold,
            )
        )

        return build_response(
            operation=PropertyOperation.ADDRESS_COMPARISON,
            response_status=PropertyResponseStatus.OK,
            data={
                "left": left,
                "right": right,
                "comparison": comparison,
            },
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message="Address comparison completed.",
        )
    except Exception as exc:
        return route_exception_response(
            operation=PropertyOperation.ADDRESS_COMPARISON,
            error=exc,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
        )


# ============================================================
# SECTION 34 - PROFILE BUILD ROUTE
# ============================================================

@router.post("/profile/build")
async def property_profile_build(
    request_body: PropertyProfileBuildRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
    ),
    services: PropertyServiceContainer = Depends(get_services),
    repository: PropertyProfileRepositoryProtocol = Depends(
        get_profile_repository
    ),
) -> JSONResponse | dict[str, Any]:
    started = time.perf_counter()
    request_id_value = resolve_request_id(
        request_body.context,
        x_request_id,
    )
    correlation_id = resolve_correlation_id(
        request_body.context,
        x_correlation_id,
    )

    try:
        engine = require_module(
            "property_profile_engine",
            services.profile_engine,
        )
        mode_enum = require_module(
            "property_profile_engine",
            ProfileBuildMode,
        )
        mode = enum_value(mode_enum, request_body.mode, "mode")

        raw_address = (
            request_body.address.raw_address
            if request_body.address
            else None
        )
        address_context = (
            {
                "city": request_body.address.city,
                "state_code": request_body.address.state_code,
                "postal_code": request_body.address.postal_code,
                "county": request_body.address.county,
                "country_code": request_body.address.country_code,
                "enrich": request_body.address.enrich,
            }
            if request_body.address
            else None
        )

        result = await execute_service_call(
            lambda: engine.build(
                property_id=request_body.identity.property_id,
                evidence=to_field_evidence(request_body.evidence),
                mode=mode,
                raw_address=raw_address,
                address_context=address_context,
                external_ids=request_body.identity.external_ids,
                sales_history=to_sale_records(
                    request_body.sales_history
                ),
                risks=to_risk_items(request_body.risks),
                metadata={
                    **request_body.metadata,
                    "request_context": request_body.context.model_dump(),
                },
            )
        )

        persistence = await persist_profile_if_requested(
            mode=request_body.persistence,
            profile=result.profile,
            repository=repository,
        )

        return build_response(
            operation=PropertyOperation.PROFILE_BUILD,
            response_status=(
                PropertyResponseStatus.OK
                if result.succeeded
                else PropertyResponseStatus.PARTIAL
            ),
            data={
                "build_result": result,
                "persistence": persistence,
            },
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message="Property profile build completed.",
            warnings=result.warnings,
            limitations=[
                "The profile reflects only evidence supplied to this request.",
                "No live public-record or MLS lookup occurs in this route.",
            ],
        )
    except Exception as exc:
        return route_exception_response(
            operation=PropertyOperation.PROFILE_BUILD,
            error=exc,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
        )


# ============================================================
# SECTION 35 - PROFILE REFRESH ROUTE
# ============================================================

@router.post("/profile/refresh")
async def property_profile_refresh(
    request_body: PropertyProfileRefreshRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
    ),
    services: PropertyServiceContainer = Depends(get_services),
    repository: PropertyProfileRepositoryProtocol = Depends(
        get_profile_repository
    ),
) -> JSONResponse | dict[str, Any]:
    started = time.perf_counter()
    request_id_value = resolve_request_id(
        request_body.context,
        x_request_id,
    )
    correlation_id = resolve_correlation_id(
        request_body.context,
        x_correlation_id,
    )

    try:
        engine = require_module(
            "property_profile_engine",
            services.profile_engine,
        )
        profile = profile_from_dict(request_body.profile)

        raw_address = (
            request_body.address.raw_address
            if request_body.address
            else None
        )
        address_context = (
            {
                "city": request_body.address.city,
                "state_code": request_body.address.state_code,
                "postal_code": request_body.address.postal_code,
                "county": request_body.address.county,
                "country_code": request_body.address.country_code,
                "enrich": request_body.address.enrich,
            }
            if request_body.address
            else None
        )

        result = await execute_service_call(
            lambda: engine.refresh(
                profile,
                evidence=to_field_evidence(request_body.evidence),
                raw_address=raw_address,
                address_context=address_context,
                sales_history=(
                    to_sale_records(request_body.sales_history)
                    if request_body.sales_history is not None
                    else None
                ),
                risks=(
                    to_risk_items(request_body.risks)
                    if request_body.risks is not None
                    else None
                ),
                metadata=request_body.metadata,
            )
        )

        persistence = await persist_profile_if_requested(
            mode=request_body.persistence,
            profile=result.profile,
            repository=repository,
        )

        return build_response(
            operation=PropertyOperation.PROFILE_REFRESH,
            response_status=(
                PropertyResponseStatus.OK
                if result.succeeded
                else PropertyResponseStatus.PARTIAL
            ),
            data={
                "refresh_result": result,
                "persistence": persistence,
            },
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message="Property profile refresh completed.",
            warnings=result.warnings,
        )
    except Exception as exc:
        return route_exception_response(
            operation=PropertyOperation.PROFILE_REFRESH,
            error=exc,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
        )


# ============================================================
# SECTION 36 - PROFILE MERGE ROUTE
# ============================================================

@router.post("/profile/merge")
async def property_profile_merge(
    request_body: PropertyProfileMergeRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
    ),
    services: PropertyServiceContainer = Depends(get_services),
    repository: PropertyProfileRepositoryProtocol = Depends(
        get_profile_repository
    ),
) -> JSONResponse | dict[str, Any]:
    started = time.perf_counter()
    request_id_value = resolve_request_id(
        request_body.context,
        x_request_id,
    )
    correlation_id = resolve_correlation_id(
        request_body.context,
        x_correlation_id,
    )

    try:
        engine = require_module(
            "property_profile_engine",
            services.profile_engine,
        )
        left = profile_from_dict(request_body.left_profile)
        right = profile_from_dict(request_body.right_profile)

        result = await execute_service_call(
            lambda: engine.merge(left, right)
        )

        persistence = await persist_profile_if_requested(
            mode=request_body.persistence,
            profile=result.profile,
            repository=repository,
        )

        return build_response(
            operation=PropertyOperation.PROFILE_MERGE,
            response_status=(
                PropertyResponseStatus.OK
                if result.succeeded
                else PropertyResponseStatus.PARTIAL
            ),
            data={
                "merge_result": result,
                "persistence": persistence,
            },
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message="Property profile merge completed.",
            warnings=result.warnings,
        )
    except Exception as exc:
        return route_exception_response(
            operation=PropertyOperation.PROFILE_MERGE,
            error=exc,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
        )


# ============================================================
# SECTION 37 - CONFIDENCE EVALUATION ROUTE
# ============================================================

@router.post("/confidence/evaluate")
async def property_confidence_evaluate(
    request_body: ConfidenceEvaluationRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
    ),
    services: PropertyServiceContainer = Depends(get_services),
) -> JSONResponse | dict[str, Any]:
    started = time.perf_counter()
    request_id_value = resolve_request_id(
        request_body.context,
        x_request_id,
    )
    correlation_id = resolve_correlation_id(
        request_body.context,
        x_correlation_id,
    )

    try:
        engine = require_module(
            "confidence_engine",
            services.confidence_engine,
        )
        decision_engine = require_module(
            "confidence_engine",
            services.confidence_decision_engine,
        )
        aggregation_enum = require_module(
            "confidence_engine",
            AggregationMethod,
        )
        policy_enum = require_module(
            "confidence_engine",
            PolicyMode,
        )
        policy_factory = require_module(
            "confidence_engine",
            default_policy,
        )

        aggregation = enum_value(
            aggregation_enum,
            request_body.aggregation_method,
            "aggregation_method",
        )
        policy_mode = enum_value(
            policy_enum,
            request_body.policy_mode,
            "policy_mode",
        )

        result = await execute_service_call(
            lambda: engine.evaluate(
                to_confidence_evidence(request_body.evidence),
                method=aggregation,
                prior=request_body.prior,
                minimum_desired_evidence=(
                    request_body.minimum_desired_evidence
                ),
                metadata={
                    "request_context": request_body.context.model_dump(),
                },
            )
        )

        decision = await execute_service_call(
            lambda: decision_engine.decide(
                result,
                impact=request_body.impact,
                field_path=request_body.field_path,
                policy=policy_factory(policy_mode),
            )
        )

        return build_response(
            operation=PropertyOperation.CONFIDENCE_EVALUATION,
            response_status=PropertyResponseStatus.OK,
            data={
                "confidence_result": result,
                "decision": decision,
            },
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message="Confidence evaluation completed.",
            warnings=getattr(result, "warnings", []),
        )
    except Exception as exc:
        return route_exception_response(
            operation=PropertyOperation.CONFIDENCE_EVALUATION,
            error=exc,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
        )


# ============================================================
# SECTION 38 - SOURCE EXPLANATION ROUTE
# ============================================================

@router.post("/explain")
async def property_explain(
    request_body: ExplanationRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
    ),
    services: PropertyServiceContainer = Depends(get_services),
) -> JSONResponse | dict[str, Any]:
    started = time.perf_counter()
    request_id_value = resolve_request_id(
        request_body.context,
        x_request_id,
    )
    correlation_id = resolve_correlation_id(
        request_body.context,
        x_correlation_id,
    )

    try:
        engine = require_module(
            "source_explanation_engine",
            services.explanation_engine,
        )
        claim_class = require_module("source_explanation_engine", Claim)
        claim_type_enum = require_module(
            "source_explanation_engine",
            ClaimType,
        )
        options_class = require_module(
            "source_explanation_engine",
            ExplanationOptions,
        )
        audience_enum = require_module(
            "source_explanation_engine",
            ExplanationAudience,
        )
        depth_enum = require_module(
            "source_explanation_engine",
            ExplanationDepth,
        )
        tone_enum = require_module(
            "source_explanation_engine",
            ExplanationTone,
        )

        claim_id = request_body.claim.claim_id or stable_hash(
            {
                "subject_id": request_body.subject_id,
                "statement": request_body.claim.statement,
                "value": request_body.claim.value,
            }
        )[:24]

        claim = claim_class(
            claim_id=claim_id,
            statement=request_body.claim.statement,
            claim_type=enum_value(
                claim_type_enum,
                request_body.claim.claim_type,
                "claim_type",
            ),
            field_path=request_body.claim.field_path,
            value=request_body.claim.value,
            unit=request_body.claim.unit,
            currency_code=request_body.claim.currency_code,
            confidence=request_body.claim.confidence,
            effective_at=request_body.claim.effective_at,
            metadata=request_body.claim.metadata,
        )

        options = options_class(
            audience=enum_value(
                audience_enum,
                request_body.audience,
                "audience",
            ),
            depth=enum_value(
                depth_enum,
                request_body.depth,
                "depth",
            ),
            tone=enum_value(
                tone_enum,
                request_body.tone,
                "tone",
            ),
            include_sources=request_body.include_sources,
            include_conflicts=request_body.include_conflicts,
            include_confidence=request_body.include_confidence,
            include_lineage=request_body.include_lineage,
            include_limitations=request_body.include_limitations,
        )

        report = await execute_service_call(
            lambda: engine.explain_claim(
                claim=claim,
                citations=to_citations(request_body.citations),
                subject_type=request_body.subject_type,
                subject_id=request_body.subject_id,
                options=options,
                transformations=request_body.transformations,
                limitations=request_body.limitations,
                metadata={
                    **request_body.metadata,
                    "request_context": request_body.context.model_dump(),
                },
            )
        )

        return build_response(
            operation=PropertyOperation.SOURCE_EXPLANATION,
            response_status=PropertyResponseStatus.OK,
            data=report,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message="Source explanation generated.",
            limitations=getattr(report, "limitations", []),
        )
    except Exception as exc:
        return route_exception_response(
            operation=PropertyOperation.SOURCE_EXPLANATION,
            error=exc,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
        )


# ============================================================
# SECTION 39 - BATCH PROFILE BUILD ROUTE
# ============================================================

@router.post("/batch/profile/build")
async def property_batch_profile_build(
    request_body: BatchPropertyProfileBuildRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
    ),
    services: PropertyServiceContainer = Depends(get_services),
) -> JSONResponse | dict[str, Any]:
    started = time.perf_counter()
    request_id_value = resolve_request_id(
        request_body.context,
        x_request_id,
    )
    correlation_id = resolve_correlation_id(
        request_body.context,
        x_correlation_id,
    )

    try:
        engine = require_module(
            "property_profile_engine",
            services.profile_engine,
        )
        mode_enum = require_module(
            "property_profile_engine",
            ProfileBuildMode,
        )

        results: dict[str, Any] = {}
        failures: dict[str, Any] = {}

        for key, item in request_body.requests.items():
            try:
                mode = enum_value(mode_enum, item.mode, "mode")
                raw_address = (
                    item.address.raw_address
                    if item.address
                    else None
                )
                address_context = (
                    {
                        "city": item.address.city,
                        "state_code": item.address.state_code,
                        "postal_code": item.address.postal_code,
                        "county": item.address.county,
                        "country_code": item.address.country_code,
                        "enrich": item.address.enrich,
                    }
                    if item.address
                    else None
                )

                result = await execute_service_call(
                    lambda current=item, current_mode=mode, current_raw=raw_address, current_context=address_context: engine.build(
                        property_id=current.identity.property_id,
                        evidence=to_field_evidence(current.evidence),
                        mode=current_mode,
                        raw_address=current_raw,
                        address_context=current_context,
                        external_ids=current.identity.external_ids,
                        sales_history=to_sale_records(
                            current.sales_history
                        ),
                        risks=to_risk_items(current.risks),
                        metadata=current.metadata,
                    )
                )
                results[key] = result
            except Exception as item_error:
                failures[key] = {
                    "type": item_error.__class__.__name__,
                    "message": str(item_error),
                }
                if request_body.fail_fast:
                    raise

        return build_response(
            operation=PropertyOperation.BATCH_PROFILE_BUILD,
            response_status=(
                PropertyResponseStatus.OK
                if not failures
                else PropertyResponseStatus.PARTIAL
            ),
            data={
                "total": len(request_body.requests),
                "succeeded": len(results),
                "failed": len(failures),
                "results": results,
                "failures": failures,
            },
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message="Batch property profile build completed.",
            warnings=(
                [f"{len(failures)} batch item(s) failed."]
                if failures
                else []
            ),
        )
    except Exception as exc:
        return route_exception_response(
            operation=PropertyOperation.BATCH_PROFILE_BUILD,
            error=exc,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
        )


# ============================================================
# SECTION 40 - STORED PROFILE LOOKUP ROUTE
# ============================================================

@router.get("/{property_id}")
async def property_lookup(
    property_id: str,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    repository: PropertyProfileRepositoryProtocol = Depends(
        get_profile_repository
    ),
) -> dict[str, Any]:
    started = time.perf_counter()
    request_id_value = x_request_id or generate_request_id()
    profile = await repository.get(property_id)

    if profile is None:
        return build_response(
            operation=PropertyOperation.PROFILE_LOOKUP,
            response_status=PropertyResponseStatus.PLANNED,
            data={
                "property_id": property_id,
                "found": False,
                "persistence_configured": False,
            },
            started_at=started,
            request_id_value=request_id_value,
            message=(
                "Property persistence is not configured. Use "
                "POST /properties/profile/build to construct a profile."
            ),
            limitations=[
                "This endpoint will not fabricate a stored property profile."
            ],
        )

    return build_response(
        operation=PropertyOperation.PROFILE_LOOKUP,
        response_status=PropertyResponseStatus.OK,
        data={
            "property_id": property_id,
            "found": True,
            "profile": profile,
        },
        started_at=started,
        request_id_value=request_id_value,
        message="Stored property profile loaded.",
    )


# ============================================================
# SECTION 41 - ROUTER GOVERNANCE NOTES
# ============================================================

# This router must remain free of:
# - public-record scraping algorithms
# - valuation mathematics
# - machine-learning training loops
# - ORM transaction orchestration
# - HTML/CSS/JavaScript rendering logic
# - hard-coded property facts
# - fabricated MLS or government records
#
# Those responsibilities belong in dedicated service, repository,
# connector, model-serving, or frontend modules.


# ============================================================
# SECTION 42 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "router",
    "PropertyServiceContainer",
    "PropertyProfileRepository",
    "PropertyProfileRepositoryProtocol",
    "get_services",
    "get_profile_repository",
    "RequestContextBody",
    "PropertyAddressBody",
    "AddressAnalysisRequest",
    "AddressComparisonRequest",
    "PropertyIdentityBody",
    "FieldEvidenceBody",
    "SaleRecordBody",
    "RiskItemBody",
    "PropertyProfileBuildRequest",
    "PropertyProfileRefreshRequest",
    "PropertyProfileMergeRequest",
    "BatchPropertyProfileBuildRequest",
    "ConfidenceEvidenceBody",
    "ConfidenceEvaluationRequest",
    "SourceDescriptorBody",
    "CitationBody",
    "ExplanationClaimBody",
    "ExplanationRequest",
]


# ============================================================
# END OF FILE
# ============================================================