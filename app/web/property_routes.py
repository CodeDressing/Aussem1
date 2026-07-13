# ============================================================
# AUSSEM1
# PHASE 2.45 PART 1.00
# ENTERPRISE PROPERTY INTELLIGENCE ROUTER
# FILE: app/web/property_routes.py
# PURPOSE:
# FastAPI property-intelligence HTTP routing layer for:
# - address analysis
# - address comparison
# - property profile construction
# - confidence evaluation
# - source explanation
# - estimate readiness preview
# - batch profile construction
# - diagnostics
# - readiness
# - route registry
#
# THIS ROUTER CONNECTS:
# - app.property_intelligence.address_intelligence
# - app.property_intelligence.property_profile_engine
# - app.property_intelligence.confidence_engine
# - app.property_intelligence.source_explanation_engine
#
# CORE GOVERNANCE:
# - Routes must stay thin.
# - Domain logic belongs in engines.
# - No fabricated homes.
# - No fabricated valuation.
# - No fabricated listing status.
# - No fabricated public records.
# - Public records can support parcel/tax/deed/GIS/MOD-IV context.
# - Public records cannot prove current active/under-contract/listing price.
# - Valuation preview may explain readiness, but must not invent value.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# ENTERPRISE PROPERTY ROUTER ACTIVE
# ============================================================


from __future__ import annotations

# ============================================================
# SECTION 01 - STANDARD LIBRARY IMPORTS
# ============================================================

import asyncio
import hashlib
import json
import logging
import time
import traceback
from dataclasses import asdict
from dataclasses import is_dataclass
from datetime import UTC
from datetime import date
from datetime import datetime
from enum import StrEnum
from functools import lru_cache
from typing import Any
from typing import Callable
from typing import Mapping
from typing import Sequence
from uuid import uuid4


# ============================================================
# SECTION 02 - FASTAPI / PYDANTIC IMPORTS
# ============================================================

from fastapi import APIRouter
from fastapi import Depends
from fastapi import FastAPI
from fastapi import Header
from fastapi import Response
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator


# ============================================================
# SECTION 03 - SAFE OPTIONAL DOMAIN IMPORTS
# ============================================================

IMPORT_ERRORS: dict[str, str] = {}


try:
    from app.property_intelligence.address_intelligence import (
        AddressIntelligenceEngine,
        address_fingerprint,
        analyze_address,
        compare_addresses,
        get_address_intelligence_diagnostics,
        get_address_intelligence_health,
        get_address_intelligence_metadata,
        make_property_intelligence_request_payload,
        normalize_address,
        prepare_public_record_search,
    )
except Exception as exc:  # pragma: no cover
    AddressIntelligenceEngine = None  # type: ignore
    address_fingerprint = None  # type: ignore
    analyze_address = None  # type: ignore
    compare_addresses = None  # type: ignore
    get_address_intelligence_diagnostics = None  # type: ignore
    get_address_intelligence_health = None  # type: ignore
    get_address_intelligence_metadata = None  # type: ignore
    make_property_intelligence_request_payload = None  # type: ignore
    normalize_address = None  # type: ignore
    prepare_public_record_search = None  # type: ignore
    IMPORT_ERRORS["address_intelligence"] = f"{type(exc).__name__}: {exc}"


try:
    from app.property_intelligence.property_profile_engine import (
        PropertyProfileEngine,
        build_property_profile,
        build_property_profile_dict,
        get_property_profile_engine_diagnostics,
        get_property_profile_engine_health,
        get_property_profile_engine_metadata,
        get_property_profile_engine_readiness,
        profile_to_public_api_payload,
    )
except Exception as exc:  # pragma: no cover
    PropertyProfileEngine = None  # type: ignore
    build_property_profile = None  # type: ignore
    build_property_profile_dict = None  # type: ignore
    get_property_profile_engine_diagnostics = None  # type: ignore
    get_property_profile_engine_health = None  # type: ignore
    get_property_profile_engine_metadata = None  # type: ignore
    get_property_profile_engine_readiness = None  # type: ignore
    profile_to_public_api_payload = None  # type: ignore
    IMPORT_ERRORS["property_profile_engine"] = f"{type(exc).__name__}: {exc}"


try:
    from app.property_intelligence.confidence_engine import (
        ConfidenceEngine,
        build_confidence_report,
        evaluate_fact_confidence,
        evaluate_profile_confidence,
        evaluate_section_confidence,
        evaluate_source_confidence,
        get_confidence_engine_diagnostics,
        get_confidence_engine_health,
        get_confidence_engine_metadata,
        get_confidence_engine_readiness,
    )
except Exception as exc:  # pragma: no cover
    ConfidenceEngine = None  # type: ignore
    build_confidence_report = None  # type: ignore
    evaluate_fact_confidence = None  # type: ignore
    evaluate_profile_confidence = None  # type: ignore
    evaluate_section_confidence = None  # type: ignore
    evaluate_source_confidence = None  # type: ignore
    get_confidence_engine_diagnostics = None  # type: ignore
    get_confidence_engine_health = None  # type: ignore
    get_confidence_engine_metadata = None  # type: ignore
    get_confidence_engine_readiness = None  # type: ignore
    IMPORT_ERRORS["confidence_engine"] = f"{type(exc).__name__}: {exc}"


try:
    from app.property_intelligence.source_explanation_engine import (
        SourceExplanationEngine,
        build_source_explanation_report,
        explain_profile,
        explain_profile_sources,
        explain_sources,
        get_source_explanation_engine_diagnostics,
        get_source_explanation_engine_health,
        get_source_explanation_engine_metadata,
        get_source_explanation_engine_readiness,
        source_explanation_to_public_api_payload,
    )
except Exception as exc:  # pragma: no cover
    SourceExplanationEngine = None  # type: ignore
    build_source_explanation_report = None  # type: ignore
    explain_profile = None  # type: ignore
    explain_profile_sources = None  # type: ignore
    explain_sources = None  # type: ignore
    get_source_explanation_engine_diagnostics = None  # type: ignore
    get_source_explanation_engine_health = None  # type: ignore
    get_source_explanation_engine_metadata = None  # type: ignore
    get_source_explanation_engine_readiness = None  # type: ignore
    source_explanation_to_public_api_payload = None  # type: ignore
    IMPORT_ERRORS["source_explanation_engine"] = f"{type(exc).__name__}: {exc}"


# ============================================================
# SECTION 04 - LOGGER
# ============================================================

logger = logging.getLogger("aussem1.property_routes")


# ============================================================
# SECTION 05 - ROUTER METADATA
# ============================================================

PROPERTY_ROUTES_NAME = "Aussem1 Enterprise Property Intelligence Router"

PROPERTY_ROUTES_VERSION = "0.2.0"

PROPERTY_ROUTES_PHASE = "PHASE 2.45 PART 1.00"

PROPERTY_ROUTES_STATUS = "enterprise_property_intelligence_router_active"

PROPERTY_ROUTES_PREFIX = "/properties"

PROPERTY_ROUTES_DESCRIPTION = (
    "Dedicated source-governed property-intelligence API for address analysis, "
    "profile construction, confidence evaluation, source explanation, estimate "
    "readiness preview, diagnostics, route registry, and future persistence."
)

DEFAULT_REQUEST_TIMEOUT_SECONDS = 30

DEFAULT_MAX_BATCH_SIZE = 50

DEFAULT_COUNTRY_CODE = "US"

DEFAULT_STATE_CODE = "NJ"

DEFAULT_COUNTY = "Morris"


# ============================================================
# SECTION 06 - ROUTER GOVERNANCE
# ============================================================

PROPERTY_ROUTER_GOVERNANCE = {
    "mock_property_facts_allowed": False,
    "fabricated_public_records_allowed": False,
    "fabricated_listing_status_allowed": False,
    "fabricated_property_values_allowed": False,
    "fabricated_market_estimates_allowed": False,
    "public_records_can_support_parcel_tax_deed_gis_modiv": True,
    "public_records_cannot_prove_current_listing_status": True,
    "authorized_listing_feed_required_for_current_status": True,
    "valuation_engine_required_for_estimates": True,
    "source_attribution_required": True,
    "confidence_required": True,
    "unavailable_fields_must_be_labeled": True,
}


STANDARD_LIMITATIONS = [
    "This router does not fabricate property facts.",
    "Public records can support parcel, tax, deed, GIS, and MOD-IV context.",
    "Public records alone cannot prove active listing status, under-contract status, current list price, or days on market.",
    "Tax assessment is public-record context and is not current market value.",
    "GIS context is not a legal survey.",
    "Valuation output requires source-backed facts, comparable sales, valuation logic, and confidence metadata.",
]


# ============================================================
# SECTION 07 - ROUTER INSTANCE
# ============================================================

router = APIRouter(
    prefix=PROPERTY_ROUTES_PREFIX,
    tags=["Property Intelligence"],
    responses={
        400: {"description": "Property request is invalid."},
        422: {"description": "Property request validation failed."},
        500: {"description": "Property intelligence operation failed."},
        503: {"description": "Required property intelligence module unavailable."},
    },
)


# ============================================================
# SECTION 08 - ENUMERATIONS
# ============================================================

class PropertyResponseStatus(StrEnum):
    OK = "ok"
    PARTIAL = "partial"
    PLANNED = "planned"
    INVALID = "invalid"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class PropertyOperation(StrEnum):
    ROOT = "root"
    HEALTH = "health"
    READINESS = "readiness"
    DIAGNOSTICS = "diagnostics"
    ROUTE_REGISTRY = "route_registry"
    ADDRESS_ANALYZE = "address_analyze"
    ADDRESS_COMPARE = "address_compare"
    PROFILE_BUILD = "profile_build"
    PROFILE_REFRESH = "profile_refresh"
    PROFILE_MERGE = "profile_merge"
    PROFILE_LOOKUP = "profile_lookup"
    CONFIDENCE_EVALUATE = "confidence_evaluate"
    SOURCE_EXPLAIN = "source_explain"
    ESTIMATE_PREVIEW = "estimate_preview"
    PROPERTY_PREVIEW = "property_preview"
    BATCH_PROFILE_BUILD = "batch_profile_build"


class PersistenceMode(StrEnum):
    NONE = "none"
    DRY_RUN = "dry_run"
    COMMIT = "commit"


class EstimatePreviewStatus(StrEnum):
    NOT_READY = "not_ready"
    REQUIRES_PROFILE = "requires_profile"
    REQUIRES_PUBLIC_RECORDS = "requires_public_records"
    REQUIRES_COMPARABLES = "requires_comparables"
    REQUIRES_VALUATION_ENGINE = "requires_valuation_engine"
    READY = "ready"


# ============================================================
# SECTION 09 - BASE PYDANTIC MODEL
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
# SECTION 10 - REQUEST CONTEXT MODEL
# ============================================================

class RequestContextBody(EnterpriseModel):
    request_id: str | None = Field(default=None, max_length=128)
    correlation_id: str | None = Field(default=None, max_length=128)
    session_id: str | None = Field(default=None, max_length=128)
    user_id: str | None = Field(default=None, max_length=128)
    source_channel: str | None = Field(default=None, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================
# SECTION 11 - ADDRESS REQUEST MODELS
# ============================================================

class PropertyAddressBody(EnterpriseModel):
    raw_address: str = Field(..., min_length=1, max_length=700)
    municipality: str | None = Field(default=None, max_length=128)
    city: str | None = Field(default=None, max_length=128)
    county: str | None = Field(default=None, max_length=128)
    state_code: str | None = Field(default=DEFAULT_STATE_CODE, max_length=64)
    postal_code: str | None = Field(default=None, max_length=20)
    owner_reference: str | None = Field(default=None, max_length=255)
    country_code: str = Field(default=DEFAULT_COUNTRY_CODE, max_length=8)

    @field_validator("state_code", "country_code")
    @classmethod
    def uppercase_codes(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class AddressAnalysisRequest(EnterpriseModel):
    address: PropertyAddressBody
    include_property_request_payload: bool = True
    include_public_record_search: bool = True
    context: RequestContextBody = Field(default_factory=RequestContextBody)


class AddressComparisonRequest(EnterpriseModel):
    left: PropertyAddressBody
    right: PropertyAddressBody
    match_threshold: float = Field(default=0.84, ge=0, le=1)
    context: RequestContextBody = Field(default_factory=RequestContextBody)


# ============================================================
# SECTION 12 - PROFILE REQUEST MODELS
# ============================================================

class PropertyProfileBuildRequest(EnterpriseModel):
    raw_address: str = Field(..., min_length=1, max_length=700)
    municipality: str | None = Field(default=None, max_length=128)
    city: str | None = Field(default=None, max_length=128)
    county: str | None = Field(default=None, max_length=128)
    state_code: str | None = Field(default=DEFAULT_STATE_CODE, max_length=64)
    postal_code: str | None = Field(default=None, max_length=20)
    block: str | None = Field(default=None, max_length=64)
    lot: str | None = Field(default=None, max_length=64)
    qualifier: str | None = Field(default=None, max_length=64)
    owner_reference: str | None = Field(default=None, max_length=255)
    include_public_records: bool = True
    include_listing: bool = True
    include_valuation: bool = True
    include_comparables: bool = True
    include_location_context: bool = True
    include_ai_summary: bool = True
    strict_source_mode: bool = True
    allow_manual_review_results: bool = True
    requested_domains: list[str] = Field(default_factory=list)
    persistence: PersistenceMode = PersistenceMode.NONE
    metadata: dict[str, Any] = Field(default_factory=dict)
    context: RequestContextBody = Field(default_factory=RequestContextBody)

    @field_validator("state_code")
    @classmethod
    def uppercase_state(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class PropertyProfileRefreshRequest(PropertyProfileBuildRequest):
    profile_id: str | None = Field(default=None, max_length=160)
    prior_profile: dict[str, Any] = Field(default_factory=dict)


class PropertyProfileMergeRequest(EnterpriseModel):
    left_profile: dict[str, Any]
    right_profile: dict[str, Any]
    context: RequestContextBody = Field(default_factory=RequestContextBody)


class BatchPropertyProfileBuildRequest(EnterpriseModel):
    requests: list[PropertyProfileBuildRequest]
    fail_fast: bool = False
    context: RequestContextBody = Field(default_factory=RequestContextBody)

    @model_validator(mode="after")
    def validate_batch_size(self) -> "BatchPropertyProfileBuildRequest":
        if len(self.requests) > DEFAULT_MAX_BATCH_SIZE:
            raise ValueError(
                f"Batch exceeds maximum of {DEFAULT_MAX_BATCH_SIZE} requests."
            )

        return self


# ============================================================
# SECTION 13 - CONFIDENCE / EXPLANATION REQUEST MODELS
# ============================================================

class ConfidenceEvaluationRequest(EnterpriseModel):
    profile: dict[str, Any] = Field(default_factory=dict)
    fact: dict[str, Any] | None = None
    section_name: str | None = Field(default=None, max_length=160)
    section_payload: dict[str, Any] | None = None
    source_payload: dict[str, Any] | None = None
    mode: str = Field(default="profile", max_length=64)
    context: RequestContextBody = Field(default_factory=RequestContextBody)


class SourceExplanationRequest(EnterpriseModel):
    profile: dict[str, Any] = Field(default_factory=dict)
    include_public_api_payload: bool = True
    context: RequestContextBody = Field(default_factory=RequestContextBody)


class EstimatePreviewRequest(EnterpriseModel):
    raw_address: str = Field(..., min_length=1, max_length=700)
    municipality: str | None = Field(default=None, max_length=128)
    city: str | None = Field(default=None, max_length=128)
    county: str | None = Field(default=None, max_length=128)
    state_code: str | None = Field(default=DEFAULT_STATE_CODE, max_length=64)
    postal_code: str | None = Field(default=None, max_length=20)
    include_public_records: bool = True
    include_profile: bool = True
    context: RequestContextBody = Field(default_factory=RequestContextBody)


# ============================================================
# SECTION 14 - RESPONSE MODELS
# ============================================================

class EnterpriseErrorBody(EnterpriseModel):
    code: str
    message: str
    details: Any = None
    retryable: bool = False


class EnterpriseResponseBody(EnterpriseModel):
    platform: str = "Aussem1"
    module: str = "property_intelligence"
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
# SECTION 15 - SERIALIZATION HELPERS
# ============================================================

def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def generate_request_id() -> str:
    return f"aussem-property-{uuid4()}"


def serialize(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, BaseModel):
        return serialize(value.model_dump())

    if is_dataclass(value):
        return serialize(asdict(value))

    if isinstance(value, StrEnum):
        return value.value

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, Mapping):
        return {
            str(key): serialize(item)
            for key, item in value.items()
        }

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return [
            serialize(item)
            for item in value
        ]

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


def safe_string(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


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
    warnings: Sequence[str] | None = None,
    limitations: Sequence[str] | None = None,
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
        operation=operation.value,
        status=status_text,
        message=message,
        data=serialized_data,
        warnings=list(warnings or []),
        limitations=list(limitations or STANDARD_LIMITATIONS),
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
            "prefix": PROPERTY_ROUTES_PREFIX,
        },
        fingerprint=fingerprint,
    ).model_dump()


# ============================================================
# SECTION 17 - ERROR HANDLING
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
            message="Property intelligence operation exceeded the allowed timeout.",
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
                "traceback": traceback.format_exc(),
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


def require_callable(name: str, value: Any) -> Any:
    if not callable(value):
        module_name = name.split(".")[0]
        raise PropertyRouteError(
            code="module_or_function_unavailable",
            message=f"Required property intelligence function is unavailable: {name}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={
                "name": name,
                "import_error": IMPORT_ERRORS.get(module_name),
                "import_errors": IMPORT_ERRORS,
            },
        )

    return value


async def execute_service_call(
    callback: Callable[[], Any],
    *,
    timeout_seconds: int = DEFAULT_REQUEST_TIMEOUT_SECONDS,
) -> Any:
    return await asyncio.wait_for(
        asyncio.to_thread(callback),
        timeout=timeout_seconds,
    )


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
# SECTION 18 - SERVICE CONTAINER
# ============================================================

class PropertyServiceContainer:
    def __init__(self) -> None:
        self.address_engine_available = AddressIntelligenceEngine is not None
        self.profile_engine_available = PropertyProfileEngine is not None
        self.confidence_engine_available = ConfidenceEngine is not None
        self.source_explanation_engine_available = (
            SourceExplanationEngine is not None
        )

    def module_status(self) -> dict[str, Any]:
        return {
            "address_intelligence": {
                "available": self.address_engine_available,
                "import_error": IMPORT_ERRORS.get("address_intelligence"),
            },
            "property_profile_engine": {
                "available": self.profile_engine_available,
                "import_error": IMPORT_ERRORS.get("property_profile_engine"),
            },
            "confidence_engine": {
                "available": self.confidence_engine_available,
                "import_error": IMPORT_ERRORS.get("confidence_engine"),
            },
            "source_explanation_engine": {
                "available": self.source_explanation_engine_available,
                "import_error": IMPORT_ERRORS.get("source_explanation_engine"),
            },
        }

    def required_ready(self) -> bool:
        return all(
            [
                self.address_engine_available,
                self.profile_engine_available,
                self.confidence_engine_available,
                self.source_explanation_engine_available,
            ]
        )


@lru_cache(maxsize=1)
def get_services() -> PropertyServiceContainer:
    return PropertyServiceContainer()


# ============================================================
# SECTION 19 - ROUTE PAYLOAD HELPERS
# ============================================================

def address_body_to_kwargs(address: PropertyAddressBody) -> dict[str, Any]:
    return {
        "municipality": address.municipality,
        "city": address.city,
        "county": address.county,
        "state_code": address.state_code,
        "postal_code": address.postal_code,
        "owner_reference": address.owner_reference,
        "country_code": address.country_code,
    }


def profile_request_to_kwargs(
    request_body: PropertyProfileBuildRequest,
) -> dict[str, Any]:
    return {
        "municipality": request_body.municipality,
        "city": request_body.city,
        "county": request_body.county,
        "state_code": request_body.state_code,
        "postal_code": request_body.postal_code,
        "block": request_body.block,
        "lot": request_body.lot,
        "qualifier": request_body.qualifier,
        "owner_reference": request_body.owner_reference,
        "include_public_records": request_body.include_public_records,
        "include_listing": request_body.include_listing,
        "include_valuation": request_body.include_valuation,
        "include_comparables": request_body.include_comparables,
        "include_location_context": request_body.include_location_context,
        "include_ai_summary": request_body.include_ai_summary,
        "strict_source_mode": request_body.strict_source_mode,
        "allow_manual_review_results": request_body.allow_manual_review_results,
        "requested_domains": request_body.requested_domains,
        "metadata": {
            **request_body.metadata,
            "request_context": request_body.context.model_dump(),
            "router_phase": PROPERTY_ROUTES_PHASE,
        },
    }


def extract_profile_payload(result: Any) -> dict[str, Any]:
    payload = serialize(result)

    if isinstance(payload, Mapping):
        if "profile" in payload and isinstance(payload["profile"], Mapping):
            return dict(payload["profile"])

        return dict(payload)

    return {
        "raw_result": payload,
    }


def build_estimate_preview_payload(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    valuation = profile_payload.get("valuation_readiness") or {}

    if not isinstance(valuation, Mapping):
        valuation = {}

    confidence = profile_payload.get("confidence_report") or {}

    if not isinstance(confidence, Mapping):
        confidence = {}

    source_explanation = profile_payload.get("source_explanation") or {}

    if not isinstance(source_explanation, Mapping):
        source_explanation = {}

    available_inputs = list(valuation.get("available_inputs") or [])
    missing_inputs = list(
        valuation.get("required_missing_inputs")
        or valuation.get("missing_inputs")
        or []
    )

    ready = bool(valuation.get("ready", False))
    estimate_allowed = bool(valuation.get("estimate_allowed", False))

    if ready and estimate_allowed:
        status_value = EstimatePreviewStatus.READY.value
    elif available_inputs:
        status_value = EstimatePreviewStatus.REQUIRES_COMPARABLES.value
    else:
        status_value = EstimatePreviewStatus.NOT_READY.value

    return {
        "estimate_status": status_value,
        "estimate_available": False,
        "estimate_value": None,
        "estimate_low": None,
        "estimate_high": None,
        "estimate_allowed": False,
        "valuation_readiness": valuation,
        "available_inputs": available_inputs,
        "missing_inputs": missing_inputs,
        "confidence_report": confidence,
        "source_explanation_summary": source_explanation.get("summary"),
        "message": (
            "Aussem1 will not fabricate a property estimate. The valuation "
            "engine, comparable-sales data, source-backed features, and confidence "
            "calibration must be connected before a market estimate is returned."
        ),
        "required_next_sources": [
            "public_records_engine",
            "tax_assessment_source",
            "gis_or_modiv_property_facts",
            "comparable_sales_dataset",
            "valuation_engine",
        ],
    }


# ============================================================
# SECTION 20 - ROOT ROUTE
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
            "governance": PROPERTY_ROUTER_GOVERNANCE,
        },
        started_at=started,
        request_id_value=request_id_value,
        message="Property intelligence router is active.",
    )


# ============================================================
# SECTION 21 - HEALTH ROUTE
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
            "import_errors": IMPORT_ERRORS,
            "governance": PROPERTY_ROUTER_GOVERNANCE,
        },
        started_at=started,
        request_id_value=request_id_value,
        message="Property route health check completed.",
    )


# ============================================================
# SECTION 22 - READINESS ROUTE
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

    data = {
        "ready": ready,
        "modules": services.module_status(),
        "import_errors": IMPORT_ERRORS,
        "engine_readiness": {
            "address_intelligence": (
                get_address_intelligence_health()
                if callable(get_address_intelligence_health)
                else None
            ),
            "property_profile": (
                get_property_profile_engine_readiness()
                if callable(get_property_profile_engine_readiness)
                else None
            ),
            "confidence": (
                get_confidence_engine_readiness()
                if callable(get_confidence_engine_readiness)
                else None
            ),
            "source_explanation": (
                get_source_explanation_engine_readiness()
                if callable(get_source_explanation_engine_readiness)
                else None
            ),
        },
    }

    return build_response(
        operation=PropertyOperation.READINESS,
        response_status=(
            PropertyResponseStatus.OK
            if ready
            else PropertyResponseStatus.UNAVAILABLE
        ),
        data=data,
        started_at=started,
        request_id_value=request_id_value,
        message=(
            "Property intelligence is ready."
            if ready
            else "Property intelligence is not fully ready."
        ),
    )


# ============================================================
# SECTION 23 - DIAGNOSTICS ROUTE
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

    data = {
        "router": {
            "name": PROPERTY_ROUTES_NAME,
            "version": PROPERTY_ROUTES_VERSION,
            "phase": PROPERTY_ROUTES_PHASE,
            "status": PROPERTY_ROUTES_STATUS,
            "prefix": PROPERTY_ROUTES_PREFIX,
        },
        "runtime": {
            "timestamp": utc_now_iso(),
            "default_timeout_seconds": DEFAULT_REQUEST_TIMEOUT_SECONDS,
            "maximum_batch_size": DEFAULT_MAX_BATCH_SIZE,
        },
        "modules": services.module_status(),
        "import_errors": IMPORT_ERRORS,
        "governance": PROPERTY_ROUTER_GOVERNANCE,
        "limitations": STANDARD_LIMITATIONS,
        "engine_diagnostics": {
            "address_intelligence": (
                get_address_intelligence_diagnostics()
                if callable(get_address_intelligence_diagnostics)
                else None
            ),
            "property_profile": (
                get_property_profile_engine_diagnostics()
                if callable(get_property_profile_engine_diagnostics)
                else None
            ),
            "confidence": (
                get_confidence_engine_diagnostics()
                if callable(get_confidence_engine_diagnostics)
                else None
            ),
            "source_explanation": (
                get_source_explanation_engine_diagnostics()
                if callable(get_source_explanation_engine_diagnostics)
                else None
            ),
        },
        "external_connectivity": {
            "live_mls": False,
            "live_reso": False,
            "live_idx": False,
            "live_broker_feed": False,
            "live_comparable_sales": False,
            "live_valuation_engine": False,
        },
    }

    return build_response(
        operation=PropertyOperation.DIAGNOSTICS,
        response_status=PropertyResponseStatus.OK,
        data=data,
        started_at=started,
        request_id_value=request_id_value,
        correlation_id=x_correlation_id,
        message="Property diagnostics generated.",
    )


# ============================================================
# SECTION 24 - ROUTE REGISTRY
# ============================================================

@router.get("/registry/routes")
async def property_route_registry(
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> dict[str, Any]:
    started = time.perf_counter()
    request_id_value = x_request_id or generate_request_id()

    route_groups = {
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
            {"method": "POST", "path": "/properties/confidence/evaluate"},
        ],
        "source_explanation_routes": [
            {"method": "POST", "path": "/properties/explain"},
        ],
        "estimate_routes": [
            {"method": "POST", "path": "/properties/estimate/preview"},
            {"method": "POST", "path": "/properties/preview"},
        ],
        "batch_routes": [
            {"method": "POST", "path": "/properties/batch/profile/build"},
        ],
    }

    return build_response(
        operation=PropertyOperation.ROUTE_REGISTRY,
        response_status=PropertyResponseStatus.OK,
        data=route_groups,
        started_at=started,
        request_id_value=request_id_value,
        message="Property route registry loaded.",
    )


# ============================================================
# SECTION 25 - ADDRESS ANALYSIS ROUTE
# ============================================================

@router.post("/address/analyze")
async def property_address_analyze(
    request_body: AddressAnalysisRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
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
        analyzer = require_callable(
            "address_intelligence.analyze_address",
            analyze_address,
        )

        analysis = await execute_service_call(
            lambda: analyzer(
                request_body.address.raw_address,
                **address_body_to_kwargs(request_body.address),
            )
        )

        data = {
            "analysis": analysis,
        }

        if request_body.include_public_record_search:
            search_preparer = require_callable(
                "address_intelligence.prepare_public_record_search",
                prepare_public_record_search,
            )
            data["public_record_search"] = await execute_service_call(
                lambda: search_preparer(
                    request_body.address.raw_address,
                    **address_body_to_kwargs(request_body.address),
                )
            )

        if request_body.include_property_request_payload:
            payload_builder = require_callable(
                "address_intelligence.make_property_intelligence_request_payload",
                make_property_intelligence_request_payload,
            )
            data["property_intelligence_request"] = await execute_service_call(
                lambda: payload_builder(
                    request_body.address.raw_address,
                    **address_body_to_kwargs(request_body.address),
                )
            )

        warnings = []
        analysis_payload = serialize(analysis)

        if isinstance(analysis_payload, Mapping):
            for issue in analysis_payload.get("issues") or []:
                if isinstance(issue, Mapping) and issue.get("severity") in {
                    "warning",
                    "error",
                }:
                    warnings.append(safe_string(issue.get("message")))

        return build_response(
            operation=PropertyOperation.ADDRESS_ANALYZE,
            response_status=PropertyResponseStatus.OK,
            data=data,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message="Address intelligence analysis completed.",
            warnings=[warning for warning in warnings if warning],
        )

    except Exception as exc:
        return route_exception_response(
            operation=PropertyOperation.ADDRESS_ANALYZE,
            error=exc,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
        )


# ============================================================
# SECTION 26 - ADDRESS COMPARISON ROUTE
# ============================================================

@router.post("/address/compare")
async def property_address_compare(
    request_body: AddressComparisonRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
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
        comparer = require_callable(
            "address_intelligence.compare_addresses",
            compare_addresses,
        )

        comparison = await execute_service_call(
            lambda: comparer(
                request_body.left.raw_address,
                request_body.right.raw_address,
                match_threshold=request_body.match_threshold,
            )
        )

        return build_response(
            operation=PropertyOperation.ADDRESS_COMPARE,
            response_status=PropertyResponseStatus.OK,
            data={
                "comparison": comparison,
            },
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message="Address comparison completed.",
        )

    except Exception as exc:
        return route_exception_response(
            operation=PropertyOperation.ADDRESS_COMPARE,
            error=exc,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
        )


# ============================================================
# SECTION 27 - PROFILE BUILD ROUTE
# ============================================================

@router.post("/profile/build")
async def property_profile_build(
    request_body: PropertyProfileBuildRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
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
        builder = require_callable(
            "property_profile_engine.build_property_profile",
            build_property_profile,
        )

        result = await execute_service_call(
            lambda: builder(
                request_body.raw_address,
                **profile_request_to_kwargs(request_body),
            )
        )

        public_payload = None

        if callable(profile_to_public_api_payload):
            try:
                public_payload = profile_to_public_api_payload(result)
            except Exception:
                public_payload = None

        result_payload = serialize(result)
        warnings = []

        if isinstance(result_payload, Mapping):
            warnings = list(result_payload.get("warnings") or [])

        return build_response(
            operation=PropertyOperation.PROFILE_BUILD,
            response_status=PropertyResponseStatus.OK,
            data={
                "profile_result": result,
                "public_payload": public_payload,
            },
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message=(
                "Property profile build completed. Unavailable listing and valuation "
                "claims are labeled instead of fabricated."
            ),
            warnings=warnings,
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
# SECTION 28 - PROFILE REFRESH ROUTE
# ============================================================

@router.post("/profile/refresh")
async def property_profile_refresh(
    request_body: PropertyProfileRefreshRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
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
        builder = require_callable(
            "property_profile_engine.build_property_profile",
            build_property_profile,
        )

        result = await execute_service_call(
            lambda: builder(
                request_body.raw_address,
                **profile_request_to_kwargs(request_body),
            )
        )

        return build_response(
            operation=PropertyOperation.PROFILE_REFRESH,
            response_status=PropertyResponseStatus.OK,
            data={
                "profile_id": request_body.profile_id,
                "prior_profile_received": bool(request_body.prior_profile),
                "refresh_result": result,
            },
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message="Property profile refresh completed using current source-governed engine.",
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
# SECTION 29 - PROFILE MERGE ROUTE
# ============================================================

@router.post("/profile/merge")
async def property_profile_merge(
    request_body: PropertyProfileMergeRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
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
        merged = {
            "left_profile": request_body.left_profile,
            "right_profile": request_body.right_profile,
            "merge_status": "planned",
            "message": (
                "Profile merge endpoint is active, but durable profile merge logic "
                "will be completed after persistence and conflict-resolution engines."
            ),
            "governance": PROPERTY_ROUTER_GOVERNANCE,
        }

        return build_response(
            operation=PropertyOperation.PROFILE_MERGE,
            response_status=PropertyResponseStatus.PLANNED,
            data=merged,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message="Property profile merge route is available as a planned contract.",
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
# SECTION 30 - CONFIDENCE EVALUATION ROUTE
# ============================================================

@router.post("/confidence/evaluate")
async def property_confidence_evaluate(
    request_body: ConfidenceEvaluationRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
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
        mode = request_body.mode.lower().strip()

        if mode == "fact":
            evaluator = require_callable(
                "confidence_engine.evaluate_fact_confidence",
                evaluate_fact_confidence,
            )
            data = await execute_service_call(
                lambda: evaluator(request_body.fact or {})
            )
        elif mode == "section":
            evaluator = require_callable(
                "confidence_engine.evaluate_section_confidence",
                evaluate_section_confidence,
            )
            data = await execute_service_call(
                lambda: evaluator(
                    request_body.section_name or "section",
                    request_body.section_payload or {},
                )
            )
        elif mode == "source":
            evaluator = require_callable(
                "confidence_engine.evaluate_source_confidence",
                evaluate_source_confidence,
            )
            data = await execute_service_call(
                lambda: evaluator(request_body.source_payload or {})
            )
        else:
            evaluator = require_callable(
                "confidence_engine.evaluate_profile_confidence",
                evaluate_profile_confidence,
            )
            data = await execute_service_call(
                lambda: evaluator(request_body.profile)
            )

        return build_response(
            operation=PropertyOperation.CONFIDENCE_EVALUATE,
            response_status=PropertyResponseStatus.OK,
            data={
                "mode": mode,
                "confidence_result": data,
            },
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message="Confidence evaluation completed.",
        )

    except Exception as exc:
        return route_exception_response(
            operation=PropertyOperation.CONFIDENCE_EVALUATE,
            error=exc,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
        )


# ============================================================
# SECTION 31 - SOURCE EXPLANATION ROUTE
# ============================================================

@router.post("/explain")
async def property_explain(
    request_body: SourceExplanationRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
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
        explainer = require_callable(
            "source_explanation_engine.explain_profile_sources",
            explain_profile_sources,
        )

        report = await execute_service_call(
            lambda: explainer(request_body.profile)
        )

        public_payload = None

        if request_body.include_public_api_payload and callable(
            source_explanation_to_public_api_payload
        ):
            try:
                public_payload = source_explanation_to_public_api_payload(report)
            except Exception:
                public_payload = None

        return build_response(
            operation=PropertyOperation.SOURCE_EXPLAIN,
            response_status=PropertyResponseStatus.OK,
            data={
                "source_explanation": report,
                "public_payload": public_payload,
            },
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message="Source explanation generated.",
        )

    except Exception as exc:
        return route_exception_response(
            operation=PropertyOperation.SOURCE_EXPLAIN,
            error=exc,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
        )


# ============================================================
# SECTION 32 - ESTIMATE PREVIEW ROUTE
# ============================================================

@router.post("/estimate/preview")
async def property_estimate_preview(
    request_body: EstimatePreviewRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
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
        builder = require_callable(
            "property_profile_engine.build_property_profile",
            build_property_profile,
        )

        profile_result = await execute_service_call(
            lambda: builder(
                request_body.raw_address,
                municipality=request_body.municipality,
                city=request_body.city,
                county=request_body.county,
                state_code=request_body.state_code,
                postal_code=request_body.postal_code,
                include_public_records=request_body.include_public_records,
                include_listing=True,
                include_valuation=True,
                include_comparables=True,
                include_location_context=True,
                include_ai_summary=True,
                strict_source_mode=True,
                allow_manual_review_results=True,
                metadata={
                    "request_context": request_body.context.model_dump(),
                    "route": "/properties/estimate/preview",
                },
            )
        )

        profile_payload = extract_profile_payload(profile_result)
        preview = build_estimate_preview_payload(profile_payload)

        return build_response(
            operation=PropertyOperation.ESTIMATE_PREVIEW,
            response_status=PropertyResponseStatus.PARTIAL,
            data={
                "profile_result": profile_result if request_body.include_profile else None,
                "estimate_preview": preview,
            },
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message=(
                "Estimate readiness preview completed. No market estimate was "
                "fabricated because valuation/comparable-sales systems are not fully connected."
            ),
            warnings=[
                "Estimate value is unavailable until valuation engine and comparable-sales source are connected."
            ],
        )

    except Exception as exc:
        return route_exception_response(
            operation=PropertyOperation.ESTIMATE_PREVIEW,
            error=exc,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
        )


# ============================================================
# SECTION 33 - PROPERTY PREVIEW ROUTE
# COMPATIBILITY:
# This supports dashboard controllers that call /properties/preview.
# ============================================================

@router.post("/preview")
async def property_preview(
    request_body: EstimatePreviewRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
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
        builder = require_callable(
            "property_profile_engine.build_property_profile",
            build_property_profile,
        )

        profile_result = await execute_service_call(
            lambda: builder(
                request_body.raw_address,
                municipality=request_body.municipality,
                city=request_body.city,
                county=request_body.county,
                state_code=request_body.state_code,
                postal_code=request_body.postal_code,
                include_public_records=request_body.include_public_records,
                include_listing=True,
                include_valuation=True,
                include_comparables=True,
                include_location_context=True,
                include_ai_summary=True,
                strict_source_mode=True,
                allow_manual_review_results=True,
                metadata={
                    "request_context": request_body.context.model_dump(),
                    "route": "/properties/preview",
                },
            )
        )

        profile_payload = extract_profile_payload(profile_result)
        estimate_preview = build_estimate_preview_payload(profile_payload)

        return build_response(
            operation=PropertyOperation.PROPERTY_PREVIEW,
            response_status=PropertyResponseStatus.PARTIAL,
            data={
                "property_preview": profile_result,
                "estimate_preview": estimate_preview,
            },
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
            message=(
                "Property preview completed. Estimate value remains unavailable "
                "until valuation and comparable-sales inputs are connected."
            ),
            warnings=[
                "No fabricated property estimate was returned."
            ],
        )

    except Exception as exc:
        return route_exception_response(
            operation=PropertyOperation.PROPERTY_PREVIEW,
            error=exc,
            started_at=started,
            request_id_value=request_id_value,
            correlation_id=correlation_id,
        )


# ============================================================
# SECTION 34 - BATCH PROFILE BUILD ROUTE
# ============================================================

@router.post("/batch/profile/build")
async def property_batch_profile_build(
    request_body: BatchPropertyProfileBuildRequest,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-ID",
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
        builder = require_callable(
            "property_profile_engine.build_property_profile",
            build_property_profile,
        )

        results: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []

        for index, item in enumerate(request_body.requests):
            try:
                result = await execute_service_call(
                    lambda current=item: builder(
                        current.raw_address,
                        **profile_request_to_kwargs(current),
                    )
                )
                results.append(
                    {
                        "index": index,
                        "raw_address": item.raw_address,
                        "success": True,
                        "result": result,
                    }
                )
            except Exception as item_error:
                failures.append(
                    {
                        "index": index,
                        "raw_address": item.raw_address,
                        "success": False,
                        "type": item_error.__class__.__name__,
                        "message": str(item_error),
                    }
                )

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
# SECTION 35 - STORED PROFILE LOOKUP ROUTE
# ============================================================

@router.get("/{property_id}")
async def property_lookup(
    property_id: str,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> dict[str, Any]:
    started = time.perf_counter()
    request_id_value = x_request_id or generate_request_id()

    return build_response(
        operation=PropertyOperation.PROFILE_LOOKUP,
        response_status=PropertyResponseStatus.PLANNED,
        data={
            "property_id": property_id,
            "found": False,
            "persistence_configured": False,
            "message": (
                "Persistent property lookup is not connected yet. Use "
                "POST /properties/profile/build or POST /properties/preview "
                "to construct a source-governed live profile."
            ),
        },
        started_at=started,
        request_id_value=request_id_value,
        message="Property persistence is planned and not yet configured.",
        limitations=[
            "This endpoint will not fabricate a stored property profile.",
            "Persistent database lookup requires the future property repository layer.",
        ],
    )


# ============================================================
# SECTION 36 - ROUTER REGISTRATION HELPER
# ============================================================

def register_property_router(app: FastAPI) -> FastAPI:
    """
    Register property intelligence router on a FastAPI app.

    main.py can safely call:
        register_property_router(application)
    """

    app.include_router(router)

    return app


# ============================================================
# SECTION 37 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "router",
    "register_property_router",
    "PropertyServiceContainer",
    "get_services",
    "PropertyResponseStatus",
    "PropertyOperation",
    "PersistenceMode",
    "EstimatePreviewStatus",
    "RequestContextBody",
    "PropertyAddressBody",
    "AddressAnalysisRequest",
    "AddressComparisonRequest",
    "PropertyProfileBuildRequest",
    "PropertyProfileRefreshRequest",
    "PropertyProfileMergeRequest",
    "BatchPropertyProfileBuildRequest",
    "ConfidenceEvaluationRequest",
    "SourceExplanationRequest",
    "EstimatePreviewRequest",
    "EnterpriseErrorBody",
    "EnterpriseResponseBody",
    "property_root",
    "property_health",
    "property_readiness",
    "property_diagnostics",
    "property_route_registry",
    "property_address_analyze",
    "property_address_compare",
    "property_profile_build",
    "property_profile_refresh",
    "property_profile_merge",
    "property_confidence_evaluate",
    "property_explain",
    "property_estimate_preview",
    "property_preview",
    "property_batch_profile_build",
    "property_lookup",
]


# ============================================================
# END OF FILE
Cc