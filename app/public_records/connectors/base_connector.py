# ============================================================
# AUSSEM1
# PHASE 2.20 PART 4.00
# ENTERPRISE PUBLIC RECORD BASE CONNECTOR
# FILE: app/public_records/connectors/base_connector.py
# PURPOSE:
# Define the base connector contract used by every Aussem1
# public-record connector.
#
# This file provides:
# - source-governed connector lifecycle
# - safe request execution
# - standard connector metadata
# - standard search request handling
# - standard empty/not-implemented/error responses
# - parser extension hooks
# - source attribution helpers
# - public-record normalization helpers
# - confidence scaffolding
# - connector diagnostics
#
# This file does not create mock property records.
# This file does not fabricate property facts.
# This file does not fabricate tax assessments.
# This file does not fabricate sale history.
# This file does not claim active listing status from public records.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# REAL PUBLIC RECORD BASE CONNECTOR ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from typing import Any

from app.public_records.models import BuildingFactsRecord
from app.public_records.models import DeedRecord
from app.public_records.models import GISContextRecord
from app.public_records.models import LienRecord
from app.public_records.models import ModIVRecord
from app.public_records.models import MortgageRecord
from app.public_records.models import MunicipalContextRecord
from app.public_records.models import OwnerReferenceRecord
from app.public_records.models import ParcelIdentifier
from app.public_records.models import ParcelRecord
from app.public_records.models import PropertyTaxRecord
from app.public_records.models import PublicRecordAddress
from app.public_records.models import PublicRecordConnectorResult
from app.public_records.models import PublicRecordConnectorStatus
from app.public_records.models import PublicRecordSearchRequest
from app.public_records.models import PublicRecordSourceContext
from app.public_records.models import PublicRecordStatus
from app.public_records.models import RecordedDocumentReference
from app.public_records.models import SaleHistoryRecord
from app.public_records.models import TaxAssessmentRecord
from app.public_records.models import make_public_record_id
from app.public_records.models import make_public_record_source_context
from app.public_records.models import make_unavailable_connector_result
from app.public_records.models import normalize_block_lot
from app.public_records.models import normalize_county
from app.public_records.models import normalize_municipality
from app.public_records.models import normalize_state
from app.sources.source_client import SourceClient
from app.sources.source_client import SourceHttpResponse
from app.sources.source_client import governed_get
from app.sources.source_models import SourceAccessMethod
from app.sources.source_models import SourceAttribution
from app.sources.source_models import SourceConfidenceBand
from app.sources.source_models import SourceConfidenceReport
from app.sources.source_models import SourceDataFormat
from app.sources.source_models import SourceError
from app.sources.source_models import SourceErrorType
from app.sources.source_models import SourceRecordReference
from app.sources.source_models import SourceRequestPolicy
from app.sources.source_models import SourceResult
from app.sources.source_models import SourceStatus
from app.sources.source_models import SourceType
from app.sources.source_models import SourceWarning
from app.sources.source_models import clamp_confidence
from app.sources.source_models import confidence_band
from app.sources.source_models import stable_hash


# ============================================================
# SECTION 02 - MODULE METADATA
# ============================================================

BASE_CONNECTOR_NAME = "Aussem1 Enterprise Base Public Record Connector"

BASE_CONNECTOR_VERSION = "0.1.0"

BASE_CONNECTOR_PHASE = "PHASE 2.20 PART 4.00"

BASE_CONNECTOR_STATUS = "real_public_record_base_connector_active"


# ============================================================
# SECTION 03 - BASE CONNECTOR GOVERNANCE
# ============================================================

BASE_CONNECTOR_GOVERNANCE = {
    "mock_records_allowed": False,
    "mock_connector_responses_allowed": False,
    "fabricated_property_facts_allowed": False,
    "fabricated_tax_assessments_allowed": False,
    "fabricated_deeds_allowed": False,
    "fabricated_sale_history_allowed": False,
    "fabricated_listing_status_allowed": False,
    "active_listing_status_from_public_records_allowed": False,
    "under_contract_status_from_public_records_allowed": False,
    "source_attribution_required": True,
    "source_status_required": True,
    "retrieved_at_required": True,
    "confidence_required": True,
    "manual_review_for_ambiguity": True,
    "manual_review_for_conflicts": True,
    "safe_http_client_required": True,
    "respect_source_terms_required": True,
    "bypass_access_controls_allowed": False,
    "uncontrolled_scraping_allowed": False,
}


# ============================================================
# SECTION 04 - PUBLIC RECORD CLAIM GOVERNANCE
# ============================================================

BASE_PUBLIC_RECORD_SUPPORTED_CLAIMS = [
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
    "state",
    "gis_context",
    "modiv_context",
]

BASE_PUBLIC_RECORD_UNSUPPORTED_LISTING_CLAIMS = [
    "active_listing_status",
    "under_contract_status",
    "pending_status",
    "current_listing_price",
    "current_days_on_market",
    "current_showing_availability",
    "current_offer_deadline",
    "current_mls_status",
    "current_broker_confirmation",
]


# ============================================================
# SECTION 05 - UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(UTC).isoformat()


def safe_string(value: Any) -> str:
    """
    Convert an unknown value to a safe stripped string.
    """

    if value is None:
        return ""

    return str(value).strip()


def collapse_whitespace(value: Any) -> str:
    """
    Collapse repeated whitespace.
    """

    return " ".join(safe_string(value).split())


def normalize_html_text(value: Any) -> str:
    """
    Normalize text extracted from HTML.
    """

    text = safe_string(value)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_money_text(value: Any) -> str:
    """
    Normalize money-like text before model conversion.
    """

    text = safe_string(value)

    text = text.replace("$", "")
    text = text.replace(",", "")
    text = text.replace("USD", "")
    text = text.replace("usd", "")

    return text.strip()


def normalize_percent_text(value: Any) -> str:
    """
    Normalize percent-like text.
    """

    text = safe_string(value)

    text = text.replace("%", "")

    return text.strip()


def normalize_public_record_key(value: Any) -> str:
    """
    Normalize a generic public-record key.
    """

    text = safe_string(value).lower()

    text = re.sub(r"[^a-z0-9]+", "_", text)

    return text.strip("_")


def make_connector_run_id(
    *,
    connector_id: str,
    source_id: str,
    request: PublicRecordSearchRequest | None = None,
) -> str:
    """
    Create stable connector run ID.
    """

    payload = {
        "connector_id": connector_id,
        "source_id": source_id,
        "request": request.to_dict() if request else None,
        "timestamp_bucket": utc_now()[:16],
    }

    return f"connector-run-{stable_hash(payload)[:18]}"


def make_connector_record_id(
    *,
    connector_id: str,
    source_id: str,
    record_type: str,
    raw_key: str | None = None,
    request: PublicRecordSearchRequest | None = None,
) -> str:
    """
    Create stable record ID for parsed connector output.
    """

    payload = {
        "connector_id": connector_id,
        "source_id": source_id,
        "record_type": record_type,
        "raw_key": raw_key,
        "request": request.to_dict() if request else None,
    }

    return f"{record_type}-{stable_hash(payload)[:18]}"


def request_has_address(
    request: PublicRecordSearchRequest,
) -> bool:
    """
    Return whether request has address-style search data.
    """

    return bool(
        request.raw_query
        or request.street_address
        or (
            request.address
            and (
                request.address.raw_address
                or request.address.street_address
                or request.address.normalized_address
            )
        )
    )


def request_has_block_lot(
    request: PublicRecordSearchRequest,
) -> bool:
    """
    Return whether request has block/lot data.
    """

    return bool(request.block and request.lot)


def request_has_owner_reference(
    request: PublicRecordSearchRequest,
) -> bool:
    """
    Return whether request has owner reference data.
    """

    return bool(request.owner_reference)


def infer_query_mode(
    request: PublicRecordSearchRequest,
) -> str:
    """
    Infer query mode from request.
    """

    if request_has_block_lot(request):
        return "block_lot"

    if request_has_owner_reference(request):
        return "owner_reference"

    if request_has_address(request):
        return "address"

    return "unknown"


# ============================================================
# SECTION 06 - CONNECTOR METADATA MODEL
# ============================================================

@dataclass
class PublicRecordConnectorMetadata:
    """
    Metadata describing one public-record connector.
    """

    connector_id: str
    connector_name: str
    connector_version: str
    connector_phase: str
    source_id: str
    source_name: str
    source_type: str
    source_url: str | None = None
    documentation_url: str | None = None
    jurisdiction: str | None = None
    state: str | None = None
    county: str | None = None
    municipality: str | None = None
    access_method: str = SourceAccessMethod.PUBLIC_WEB_PORTAL.value
    data_format: str = SourceDataFormat.HTML.value
    status: str = PublicRecordConnectorStatus.NOT_IMPLEMENTED.value
    supported_claims: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    supported_query_modes: list[str] = field(default_factory=list)
    request_policy: SourceRequestPolicy = field(default_factory=SourceRequestPolicy)
    notes: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert metadata to dictionary.
        """

        return asdict(self)

    def supports_claim(
        self,
        claim: str,
    ) -> bool:
        """
        Return whether connector supports a claim.
        """

        normalized = normalize_public_record_key(claim)

        return normalized in self.supported_claims

    def rejects_claim(
        self,
        claim: str,
    ) -> bool:
        """
        Return whether connector explicitly rejects a claim.
        """

        normalized = normalize_public_record_key(claim)

        return normalized in self.unsupported_claims

    def supports_query_mode(
        self,
        query_mode: str,
    ) -> bool:
        """
        Return whether connector supports query mode.
        """

        normalized = normalize_public_record_key(query_mode)

        return normalized in self.supported_query_modes


# ============================================================
# SECTION 07 - CONNECTOR EXECUTION CONTEXT MODEL
# ============================================================

@dataclass
class PublicRecordConnectorExecutionContext:
    """
    Runtime context for a connector operation.
    """

    run_id: str
    connector_id: str
    source_id: str
    request: PublicRecordSearchRequest
    query_mode: str
    started_at: str = field(default_factory=utc_now)
    finished_at: str | None = None
    elapsed_ms: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def complete(
        self,
        *,
        elapsed_ms: float | None = None,
    ) -> None:
        """
        Mark execution context complete.
        """

        self.finished_at = utc_now()
        self.elapsed_ms = elapsed_ms

    def to_dict(self) -> dict[str, Any]:
        """
        Convert context to dictionary.
        """

        return {
            "run_id": self.run_id,
            "connector_id": self.connector_id,
            "source_id": self.source_id,
            "request": self.request.to_dict(),
            "query_mode": self.query_mode,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed_ms": self.elapsed_ms,
            "metadata": self.metadata,
        }


# ============================================================
# SECTION 08 - CONNECTOR VALIDATION RESULT MODEL
# ============================================================

@dataclass
class PublicRecordConnectorValidationResult:
    """
    Validation result for connector request and governance checks.
    """

    valid: bool
    status: str
    errors: list[SourceError] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)
    query_mode: str = "unknown"
    manual_review_required: bool = False
    checked_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert validation result to dictionary.
        """

        return {
            "valid": self.valid,
            "status": self.status,
            "errors": [
                error.to_dict()
                for error in self.errors
            ],
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
            "query_mode": self.query_mode,
            "manual_review_required": self.manual_review_required,
            "checked_at": self.checked_at,
        }


# ============================================================
# SECTION 09 - BASE CONNECTOR CLASS
# ============================================================

class BasePublicRecordConnector(ABC):
    """
    Base contract for every Aussem1 public-record connector.

    Subclasses should implement:
    - connector metadata
    - source-specific lookup logic
    - source-specific parsing
    - normalized PublicRecordConnectorResult output
    """

    connector_id = "base_public_record_connector"
    connector_name = "Base Public Record Connector"
    connector_version = "0.1.0"
    connector_phase = "PHASE 2.20 PART 4.00"

    source_id = "base_public_record_source"
    source_name = "Base Public Record Source"
    source_type = SourceType.PUBLIC_RECORD.value
    source_url: str | None = None
    documentation_url: str | None = None

    jurisdiction: str | None = None
    state: str | None = None
    county: str | None = None
    municipality: str | None = None

    access_method = SourceAccessMethod.PUBLIC_WEB_PORTAL.value
    data_format = SourceDataFormat.HTML.value
    status = PublicRecordConnectorStatus.NOT_IMPLEMENTED.value

    supported_claims = BASE_PUBLIC_RECORD_SUPPORTED_CLAIMS
    unsupported_claims = BASE_PUBLIC_RECORD_UNSUPPORTED_LISTING_CLAIMS
    supported_query_modes = [
        "address",
        "block_lot",
        "owner_reference",
    ]

    def __init__(
        self,
        *,
        client: SourceClient | None = None,
        request_policy: SourceRequestPolicy | None = None,
    ) -> None:
        self.client = client or SourceClient()
        self.request_policy = request_policy or SourceRequestPolicy(
            timeout_seconds=25,
            max_retries=1,
            respect_rate_limits=True,
            user_agent_required=True,
            uncontrolled_scraping_allowed=False,
            bypass_access_controls_allowed=False,
            store_raw_payload=False,
            manual_review_on_ambiguity=True,
            notes=[
                "Base connector default request policy.",
                "No uncontrolled scraping.",
                "No access-control bypassing.",
                "No fabricated response data.",
            ],
        )

    # ========================================================
    # SECTION 09.01 - METADATA
    # ========================================================

    def get_metadata(
        self,
    ) -> PublicRecordConnectorMetadata:
        """
        Return connector metadata.
        """

        return PublicRecordConnectorMetadata(
            connector_id=self.connector_id,
            connector_name=self.connector_name,
            connector_version=self.connector_version,
            connector_phase=self.connector_phase,
            source_id=self.source_id,
            source_name=self.source_name,
            source_type=self.source_type,
            source_url=self.source_url,
            documentation_url=self.documentation_url,
            jurisdiction=self.jurisdiction,
            state=self.state,
            county=self.county,
            municipality=self.municipality,
            access_method=self.access_method,
            data_format=self.data_format,
            status=self.status,
            supported_claims=list(self.supported_claims),
            unsupported_claims=list(self.unsupported_claims),
            supported_query_modes=list(self.supported_query_modes),
            request_policy=self.request_policy,
            notes=[
                "Connector metadata generated from class configuration.",
            ],
        )

    def get_source_context(
        self,
        *,
        source_status: str | None = None,
        notes: list[str] | None = None,
    ) -> PublicRecordSourceContext:
        """
        Build source context for normalized public-record models.
        """

        attribution = self.make_source_attribution()

        return make_public_record_source_context(
            source_id=self.source_id,
            source_name=self.source_name,
            source_type=self.source_type,
            source_url=self.source_url,
            source_status=source_status or self.status,
            attribution=attribution,
            source_notes=notes or [],
        )

    def make_source_attribution(
        self,
    ) -> SourceAttribution:
        """
        Build standard source attribution.
        """

        return SourceAttribution(
            source_id=self.source_id,
            source_name=self.source_name,
            source_type=self.source_type,
            reliability="official",
            access_method=self.access_method,
            source_url=self.source_url,
            source_agency=self.source_name,
            source_jurisdiction=self.jurisdiction,
            source_description=f"{self.connector_name} source attribution.",
            terms_note=(
                "Use governed public-record access only. "
                "Do not bypass access controls."
            ),
            citation_note=(
                "Facts from this connector must be presented with "
                "source status and confidence."
            ),
        )

    # ========================================================
    # SECTION 09.02 - GOVERNANCE CHECKS
    # ========================================================

    def get_governance(
        self,
    ) -> dict[str, Any]:
        """
        Return connector governance rules.
        """

        return BASE_CONNECTOR_GOVERNANCE.copy()

    def validate_governance(
        self,
    ) -> PublicRecordConnectorValidationResult:
        """
        Validate connector governance.
        """

        errors: list[SourceError] = []
        warnings: list[SourceWarning] = []

        if BASE_CONNECTOR_GOVERNANCE["mock_records_allowed"]:
            errors.append(
                SourceError(
                    error_type=SourceErrorType.MANUAL_REVIEW_REQUIRED.value,
                    message="Mock public records are not allowed.",
                    source_id=self.source_id,
                    source_name=self.source_name,
                    recoverable=False,
                    manual_review_required=True,
                )
            )

        if BASE_CONNECTOR_GOVERNANCE["fabricated_listing_status_allowed"]:
            errors.append(
                SourceError(
                    error_type=SourceErrorType.MANUAL_REVIEW_REQUIRED.value,
                    message="Fabricated listing status is not allowed.",
                    source_id=self.source_id,
                    source_name=self.source_name,
                    recoverable=False,
                    manual_review_required=True,
                )
            )

        if self.request_policy.bypass_access_controls_allowed:
            errors.append(
                SourceError(
                    error_type=SourceErrorType.MANUAL_REVIEW_REQUIRED.value,
                    message="Connector policy may not bypass access controls.",
                    source_id=self.source_id,
                    source_name=self.source_name,
                    recoverable=False,
                    manual_review_required=True,
                )
            )

        if self.request_policy.uncontrolled_scraping_allowed:
            errors.append(
                SourceError(
                    error_type=SourceErrorType.MANUAL_REVIEW_REQUIRED.value,
                    message="Connector policy may not allow uncontrolled scraping.",
                    source_id=self.source_id,
                    source_name=self.source_name,
                    recoverable=False,
                    manual_review_required=True,
                )
            )

        if not self.source_id:
            errors.append(
                SourceError(
                    error_type=SourceErrorType.INVALID_QUERY.value,
                    message="Connector source_id is missing.",
                    recoverable=False,
                    manual_review_required=True,
                )
            )

        if not self.connector_id:
            errors.append(
                SourceError(
                    error_type=SourceErrorType.INVALID_QUERY.value,
                    message="Connector connector_id is missing.",
                    recoverable=False,
                    manual_review_required=True,
                )
            )

        return PublicRecordConnectorValidationResult(
            valid=not errors,
            status=(
                PublicRecordConnectorStatus.READY.value
                if not errors
                else PublicRecordConnectorStatus.ERROR.value
            ),
            errors=errors,
            warnings=warnings,
            manual_review_required=bool(errors),
        )

    # ========================================================
    # SECTION 09.03 - REQUEST VALIDATION
    # ========================================================

    def validate_request(
        self,
        request: PublicRecordSearchRequest,
    ) -> PublicRecordConnectorValidationResult:
        """
        Validate search request for this connector.
        """

        errors: list[SourceError] = []
        warnings: list[SourceWarning] = []

        query_mode = infer_query_mode(request)

        governance_result = self.validate_governance()

        errors.extend(governance_result.errors)
        warnings.extend(governance_result.warnings)

        if query_mode == "unknown":
            errors.append(
                SourceError(
                    error_type=SourceErrorType.INVALID_QUERY.value,
                    message=(
                        "Public-record search request must include an address, "
                        "block/lot, or owner reference."
                    ),
                    source_id=self.source_id,
                    source_name=self.source_name,
                    recoverable=True,
                    manual_review_required=False,
                )
            )

        if query_mode not in self.supported_query_modes:
            errors.append(
                SourceError(
                    error_type=SourceErrorType.INVALID_QUERY.value,
                    message=f"Connector does not support query mode: {query_mode}",
                    source_id=self.source_id,
                    source_name=self.source_name,
                    recoverable=True,
                    manual_review_required=False,
                )
            )

        if request.state and self.state:
            request_state = normalize_state(request.state)
            connector_state = normalize_state(self.state)

            if request_state and connector_state and request_state != connector_state:
                warnings.append(
                    SourceWarning(
                        warning_code="state_mismatch",
                        message=(
                            f"Request state {request_state} does not match "
                            f"connector state {connector_state}."
                        ),
                        severity="medium",
                        source_id=self.source_id,
                    )
                )

        if request.county and self.county:
            request_county = normalize_county(request.county)
            connector_county = normalize_county(self.county)

            if (
                request_county
                and connector_county
                and request_county != connector_county
            ):
                warnings.append(
                    SourceWarning(
                        warning_code="county_mismatch",
                        message=(
                            f"Request county {request_county} does not match "
                            f"connector county {connector_county}."
                        ),
                        severity="medium",
                        source_id=self.source_id,
                    )
                )

        return PublicRecordConnectorValidationResult(
            valid=not errors,
            status=(
                PublicRecordConnectorStatus.READY.value
                if not errors
                else PublicRecordConnectorStatus.ERROR.value
            ),
            errors=errors,
            warnings=warnings,
            query_mode=query_mode,
            manual_review_required=any(
                error.manual_review_required
                for error in errors
            ),
        )

    # ========================================================
    # SECTION 09.04 - SEARCH CONTRACT
    # ========================================================

    def search(
        self,
        request: PublicRecordSearchRequest,
    ) -> PublicRecordConnectorResult:
        """
        Main search entrypoint.

        Subclasses may override this method. The base version returns
        not-implemented status without fabricating data.
        """

        validation = self.validate_request(request)

        if not validation.valid:
            return self.make_error_result(
                request=request,
                errors=validation.errors,
                warnings=validation.warnings,
                status=PublicRecordConnectorStatus.ERROR.value,
                explanation="Public-record connector request validation failed.",
            )

        return self.not_implemented_result(
            request=request,
            reason=f"{self.connector_name} has not implemented live search yet.",
        )

    @abstractmethod
    def connector_key(
        self,
    ) -> str:
        """
        Return short connector key.

        Every concrete connector must implement this.
        """

    # ========================================================
    # SECTION 09.05 - HTTP HELPERS
    # ========================================================

    def governed_get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SourceHttpResponse:
        """
        Execute a governed GET request for this connector.
        """

        return governed_get(
            url,
            source_id=self.source_id,
            source_name=self.source_name,
            access_method=self.access_method,
            params=params,
            headers=headers,
            request_policy=self.request_policy,
            metadata=metadata,
        )

    def get_source_homepage(
        self,
    ) -> SourceHttpResponse | None:
        """
        Request source homepage if source_url exists.
        """

        if not self.source_url:
            return None

        return self.governed_get(
            self.source_url,
            metadata={
                "purpose": "source_homepage_probe",
                "connector_id": self.connector_id,
            },
        )

    # ========================================================
    # SECTION 09.06 - SOURCE RESULT HELPERS
    # ========================================================

    def make_source_result_from_http_response(
        self,
        *,
        response: SourceHttpResponse,
        request: PublicRecordSearchRequest | None = None,
        parsed_payload: Any | None = None,
    ) -> SourceResult:
        """
        Convert governed HTTP response into SourceResult.
        """

        record_count = 1 if response.is_successful() else 0

        return SourceResult(
            result_id=f"source-result-{stable_hash(response.to_dict(include_text=False))[:18]}",
            source_id=self.source_id,
            source_name=self.source_name,
            source_type=self.source_type,
            status=(
                SourceStatus.AVAILABLE.value
                if response.is_successful()
                else SourceStatus.ERROR.value
            ),
            attribution=self.make_source_attribution(),
            records_found=record_count,
            raw_payload=(
                None
                if not self.request_policy.store_raw_payload
                else response.text
            ),
            parsed_payload=parsed_payload or response.json_payload,
            confidence_report=SourceConfidenceReport(
                confidence=0.60 if response.is_successful() else 0.0,
                confidence_band=(
                    SourceConfidenceBand.MEDIUM.value
                    if response.is_successful()
                    else SourceConfidenceBand.UNKNOWN.value
                ),
                positive_factors=[
                    "Governed source request completed successfully."
                ] if response.is_successful() else [],
                negative_factors=[
                    "Governed source request did not complete successfully."
                ] if not response.is_successful() else [],
                missing_factors=[
                    "Source-specific parser must normalize records."
                ],
                explanation=(
                    "HTTP source response was retrieved and wrapped as a source result."
                ),
            ),
            errors=list(response.errors),
            warnings=list(response.warnings),
            metadata={
                "connector_id": self.connector_id,
                "http_status_code": response.http_status_code,
                "detected_format": response.detected_format,
                "byte_length": response.byte_length,
                "elapsed_ms": response.elapsed_ms,
                "request": request.to_dict() if request else None,
            },
        )

    # ========================================================
    # SECTION 09.07 - RESULT FACTORIES
    # ========================================================

    def not_implemented_result(
        self,
        *,
        request: PublicRecordSearchRequest | None = None,
        reason: str | None = None,
    ) -> PublicRecordConnectorResult:
        """
        Return standard not-implemented connector result.
        """

        return make_unavailable_connector_result(
            connector_id=self.connector_id,
            source_id=self.source_id,
            source_name=self.source_name,
            request=request,
            reason=reason or f"{self.connector_name} is not implemented yet.",
        )

    def empty_result(
        self,
        *,
        request: PublicRecordSearchRequest | None = None,
        explanation: str | None = None,
        warnings: list[SourceWarning] | None = None,
    ) -> PublicRecordConnectorResult:
        """
        Return standard empty connector result.
        """

        return PublicRecordConnectorResult(
            connector_id=self.connector_id,
            source_id=self.source_id,
            source_name=self.source_name,
            status=PublicRecordConnectorStatus.EMPTY.value,
            request=request,
            warnings=warnings or [
                SourceWarning(
                    warning_code="empty_connector_result",
                    message=explanation or "No records were found.",
                    severity="medium",
                    source_id=self.source_id,
                )
            ],
            confidence_report=SourceConfidenceReport(
                confidence=0.0,
                confidence_band=SourceConfidenceBand.UNKNOWN.value,
                negative_factors=[
                    "No normalized records found."
                ],
                missing_factors=[
                    "Source did not return usable records for this request."
                ],
                explanation=explanation or "No public records found.",
            ),
            metadata={
                "connector_id": self.connector_id,
                "source_id": self.source_id,
                "query_mode": infer_query_mode(request) if request else "unknown",
            },
        )

    def make_error_result(
        self,
        *,
        request: PublicRecordSearchRequest | None = None,
        errors: list[SourceError] | None = None,
        warnings: list[SourceWarning] | None = None,
        status: str = PublicRecordConnectorStatus.ERROR.value,
        explanation: str | None = None,
    ) -> PublicRecordConnectorResult:
        """
        Return standard connector error result.
        """

        error_list = errors or [
            SourceError(
                error_type=SourceErrorType.UNKNOWN.value,
                message=explanation or "Unknown connector error.",
                source_id=self.source_id,
                source_name=self.source_name,
                recoverable=False,
                retry_recommended=False,
                manual_review_required=True,
            )
        ]

        return PublicRecordConnectorResult(
            connector_id=self.connector_id,
            source_id=self.source_id,
            source_name=self.source_name,
            status=status,
            request=request,
            errors=error_list,
            warnings=warnings or [],
            confidence_report=SourceConfidenceReport(
                confidence=0.0,
                confidence_band=SourceConfidenceBand.UNKNOWN.value,
                negative_factors=[
                    "Connector returned errors."
                ],
                missing_factors=[
                    "Usable public-record data is unavailable from this connector."
                ],
                manual_review_required=any(
                    error.manual_review_required
                    for error in error_list
                ),
                explanation=explanation or "Connector failed.",
            ),
            metadata={
                "connector_id": self.connector_id,
                "source_id": self.source_id,
                "query_mode": infer_query_mode(request) if request else "unknown",
            },
        )

    def make_partial_result(
        self,
        *,
        request: PublicRecordSearchRequest | None = None,
        source_result: SourceResult | None = None,
        parcel_records: list[ParcelRecord] | None = None,
        tax_assessment_records: list[TaxAssessmentRecord] | None = None,
        property_tax_records: list[PropertyTaxRecord] | None = None,
        building_facts_records: list[BuildingFactsRecord] | None = None,
        recorded_document_references: list[RecordedDocumentReference] | None = None,
        deed_records: list[DeedRecord] | None = None,
        mortgage_records: list[MortgageRecord] | None = None,
        lien_records: list[LienRecord] | None = None,
        sale_history_records: list[SaleHistoryRecord] | None = None,
        owner_reference_records: list[OwnerReferenceRecord] | None = None,
        municipal_context_records: list[MunicipalContextRecord] | None = None,
        gis_context_records: list[GISContextRecord] | None = None,
        modiv_records: list[ModIVRecord] | None = None,
        errors: list[SourceError] | None = None,
        warnings: list[SourceWarning] | None = None,
        explanation: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PublicRecordConnectorResult:
        """
        Return normalized partial/available connector result.
        """

        parcels = parcel_records or []
        assessments = tax_assessment_records or []
        taxes = property_tax_records or []
        building = building_facts_records or []
        docs = recorded_document_references or []
        deeds = deed_records or []
        mortgages = mortgage_records or []
        liens = lien_records or []
        sales = sale_history_records or []
        owners = owner_reference_records or []
        municipal = municipal_context_records or []
        gis = gis_context_records or []
        modiv = modiv_records or []
        error_list = errors or []
        warning_list = warnings or []

        total_records = sum(
            [
                len(parcels),
                len(assessments),
                len(taxes),
                len(building),
                len(docs),
                len(deeds),
                len(mortgages),
                len(liens),
                len(sales),
                len(owners),
                len(municipal),
                len(gis),
                len(modiv),
            ]
        )

        if total_records and not error_list:
            status = PublicRecordConnectorStatus.AVAILABLE.value
            confidence = 0.75
        elif total_records:
            status = PublicRecordConnectorStatus.PARTIAL.value
            confidence = 0.55
        elif error_list:
            status = PublicRecordConnectorStatus.ERROR.value
            confidence = 0.0
        else:
            status = PublicRecordConnectorStatus.EMPTY.value
            confidence = 0.0

        return PublicRecordConnectorResult(
            connector_id=self.connector_id,
            source_id=self.source_id,
            source_name=self.source_name,
            status=status,
            request=request,
            source_result=source_result,
            parcel_records=parcels,
            tax_assessment_records=assessments,
            property_tax_records=taxes,
            building_facts_records=building,
            recorded_document_references=docs,
            deed_records=deeds,
            mortgage_records=mortgages,
            lien_records=liens,
            sale_history_records=sales,
            owner_reference_records=owners,
            municipal_context_records=municipal,
            gis_context_records=gis,
            modiv_records=modiv,
            errors=error_list,
            warnings=warning_list,
            confidence_report=SourceConfidenceReport(
                confidence=confidence,
                confidence_band=confidence_band(confidence).value,
                positive_factors=[
                    "Connector returned normalized public-record data."
                ] if total_records else [],
                negative_factors=[
                    "Connector returned one or more errors."
                ] if error_list else [],
                missing_factors=[
                    "No normalized public-record data was returned."
                ] if not total_records else [],
                manual_review_required=bool(error_list),
                explanation=explanation or (
                    "Connector produced normalized public-record data."
                    if total_records
                    else "Connector produced no normalized public-record data."
                ),
            ),
            metadata={
                "connector_id": self.connector_id,
                "source_id": self.source_id,
                "query_mode": infer_query_mode(request) if request else "unknown",
                "total_records": total_records,
                **(metadata or {}),
            },
        )

    # ========================================================
    # SECTION 09.08 - RECORD NORMALIZATION HELPERS
    # ========================================================

    def build_public_record_address(
        self,
        *,
        raw_address: str | None = None,
        street_address: str | None = None,
        unit: str | None = None,
        municipality: str | None = None,
        county: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
        confidence: float = 0.50,
        warnings: list[SourceWarning] | None = None,
    ) -> PublicRecordAddress:
        """
        Build normalized public-record address.
        """

        return PublicRecordAddress(
            raw_address=raw_address,
            street_address=street_address,
            unit=unit,
            municipality=municipality or self.municipality,
            county=county or self.county,
            state=state or self.state,
            postal_code=postal_code,
            address_confidence=confidence,
            source_context=self.get_source_context(
                source_status=PublicRecordStatus.AVAILABLE.value,
            ),
            warnings=warnings or [],
        )

    def build_parcel_identifier(
        self,
        *,
        parcel_id: str | None = None,
        pams_pin: str | None = None,
        block: str | None = None,
        lot: str | None = None,
        qualifier: str | None = None,
        municipality_code: str | None = None,
        county_code: str | None = None,
        state_code: str | None = None,
        tax_map_page: str | None = None,
    ) -> ParcelIdentifier:
        """
        Build normalized parcel identifier.
        """

        normalized = normalize_block_lot(
            block,
            lot,
            qualifier,
        )

        return ParcelIdentifier(
            parcel_id=parcel_id,
            pams_pin=pams_pin,
            block=normalized["block"],
            lot=normalized["lot"],
            qualifier=normalized["qualifier"],
            municipality_code=municipality_code,
            county_code=county_code,
            state_code=state_code or self.state,
            tax_map_page=tax_map_page,
            source_context=self.get_source_context(
                source_status=PublicRecordStatus.AVAILABLE.value,
            ),
        )

    def build_source_record_reference(
        self,
        *,
        record_type: str,
        display_label: str,
        source_url: str | None = None,
        document_id: str | None = None,
        book: str | None = None,
        page: str | None = None,
        instrument_number: str | None = None,
        block: str | None = None,
        lot: str | None = None,
        municipality: str | None = None,
        county: str | None = None,
        state: str | None = None,
        record_date: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SourceRecordReference:
        """
        Build source record reference.
        """

        payload = {
            "source_id": self.source_id,
            "record_type": record_type,
            "display_label": display_label,
            "document_id": document_id,
            "book": book,
            "page": page,
            "instrument_number": instrument_number,
            "block": block,
            "lot": lot,
            "municipality": municipality,
            "county": county,
            "state": state,
            "record_date": record_date,
        }

        return SourceRecordReference(
            record_id=f"source-record-{stable_hash(payload)[:18]}",
            source_id=self.source_id,
            source_name=self.source_name,
            record_type=record_type,
            display_label=display_label,
            source_url=source_url or self.source_url,
            document_id=document_id,
            book=book,
            page=page,
            instrument_number=instrument_number,
            block=block,
            lot=lot,
            municipality=municipality or self.municipality,
            county=county or self.county,
            state=state or self.state,
            record_date=record_date,
            metadata=metadata or {},
        )

    def build_parcel_record(
        self,
        *,
        request: PublicRecordSearchRequest | None = None,
        parcel_identifier: ParcelIdentifier,
        address: PublicRecordAddress | None = None,
        property_class: str = "unknown",
        land_description: str | None = None,
        lot_size_acres: float | None = None,
        lot_size_sqft: float | None = None,
        frontage: float | None = None,
        depth: float | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        geometry_reference: str | None = None,
        confidence: float = 0.60,
        status: str = PublicRecordStatus.AVAILABLE.value,
        notes: list[str] | None = None,
        warnings: list[SourceWarning] | None = None,
    ) -> ParcelRecord:
        """
        Build parcel record.
        """

        record_id = make_public_record_id(
            record_type="parcel",
            source_id=self.source_id,
            address=(
                address.normalized_address
                if address
                else request.raw_query if request else None
            ),
            municipality=self.municipality,
            county=self.county,
            state=self.state,
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
        )

        source_reference = self.build_source_record_reference(
            record_type="parcel",
            display_label=parcel_identifier.display_key(),
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
            municipality=self.municipality,
            county=self.county,
            state=self.state,
        )

        return ParcelRecord(
            record_id=record_id,
            parcel_identifier=parcel_identifier,
            address=address,
            municipality=self.municipality,
            county=self.county,
            state=self.state,
            property_class=property_class,
            land_description=land_description,
            lot_size_acres=lot_size_acres,
            lot_size_sqft=lot_size_sqft,
            frontage=frontage,
            depth=depth,
            latitude=latitude,
            longitude=longitude,
            geometry_reference=geometry_reference,
            source_context=self.get_source_context(
                source_status=status,
            ),
            source_reference=source_reference,
            confidence=confidence,
            status=status,
            notes=notes or [],
            warnings=warnings or [],
        )

    # ========================================================
    # SECTION 09.09 - PARSER EXTENSION HOOKS
    # ========================================================

    def parse_source_response(
        self,
        *,
        response: SourceHttpResponse,
        request: PublicRecordSearchRequest,
    ) -> PublicRecordConnectorResult:
        """
        Parse source response.

        Base implementation returns not implemented.
        Concrete connectors should override this method.
        """

        return self.not_implemented_result(
            request=request,
            reason=f"{self.connector_name} has no parser implementation yet.",
        )

    def extract_tables_from_text(
        self,
        text: str,
    ) -> list[dict[str, Any]]:
        """
        Basic placeholder table extraction hook.

        This intentionally does not fabricate structured records.
        It only gives connector subclasses a safe override point.
        """

        if not text:
            return []

        return []

    def extract_key_value_pairs(
        self,
        text: str,
    ) -> dict[str, str]:
        """
        Extract simple key/value pairs from text.

        Conservative utility for connector subclasses. It only extracts
        explicit colon-separated or label/value patterns.
        """

        pairs: dict[str, str] = {}

        for line in text.splitlines():
            cleaned = normalize_html_text(line)

            if not cleaned:
                continue

            if ":" not in cleaned:
                continue

            key, value = cleaned.split(":", 1)

            normalized_key = normalize_public_record_key(key)

            if not normalized_key:
                continue

            pairs[normalized_key] = value.strip()

        return pairs

    # ========================================================
    # SECTION 09.10 - DIAGNOSTICS
    # ========================================================

    def health(
        self,
    ) -> dict[str, Any]:
        """
        Return connector health.
        """

        governance = self.validate_governance()
        metadata = self.get_metadata()

        return {
            "connector_id": self.connector_id,
            "connector_name": self.connector_name,
            "connector_version": self.connector_version,
            "connector_phase": self.connector_phase,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "status": self.status,
            "metadata": metadata.to_dict(),
            "governance_valid": governance.valid,
            "governance_errors": [
                error.to_dict()
                for error in governance.errors
            ],
            "governance_warnings": [
                warning.to_dict()
                for warning in governance.warnings
            ],
            "mock_records_allowed": BASE_CONNECTOR_GOVERNANCE[
                "mock_records_allowed"
            ],
            "fabricated_listing_status_allowed": BASE_CONNECTOR_GOVERNANCE[
                "fabricated_listing_status_allowed"
            ],
            "source_attribution_required": BASE_CONNECTOR_GOVERNANCE[
                "source_attribution_required"
            ],
            "generated_at": utc_now(),
        }

    def diagnostics(
        self,
    ) -> dict[str, Any]:
        """
        Return detailed connector diagnostics.
        """

        return {
            "health": self.health(),
            "metadata": self.get_metadata().to_dict(),
            "governance": self.get_governance(),
            "supported_claims": list(self.supported_claims),
            "unsupported_claims": list(self.unsupported_claims),
            "supported_query_modes": list(self.supported_query_modes),
            "request_policy": self.request_policy.to_dict(),
            "source_context": self.get_source_context().to_dict(),
            "generated_at": utc_now(),
        }


# ============================================================
# SECTION 10 - NON-ABSTRACT DIAGNOSTIC CONNECTOR
# ============================================================

class DiagnosticPublicRecordConnector(BasePublicRecordConnector):
    """
    Non-abstract diagnostic connector.

    This is not a data source and does not create records.
    It is useful for checking the base connector lifecycle.
    """

    connector_id = "diagnostic_public_record_connector"
    connector_name = "Diagnostic Public Record Connector"
    connector_version = BASE_CONNECTOR_VERSION
    connector_phase = BASE_CONNECTOR_PHASE

    source_id = "diagnostic_public_record_source"
    source_name = "Diagnostic Public Record Source"
    source_type = SourceType.INTERNAL_INFERENCE.value
    source_url = None
    documentation_url = None

    jurisdiction = "Internal"
    state = None
    county = None
    municipality = None

    access_method = SourceAccessMethod.INTERNAL_FILE.value
    data_format = SourceDataFormat.JSON.value
    status = PublicRecordConnectorStatus.READY.value

    supported_claims: list[str] = []
    unsupported_claims = BASE_PUBLIC_RECORD_UNSUPPORTED_LISTING_CLAIMS
    supported_query_modes = [
        "address",
        "block_lot",
        "owner_reference",
        "unknown",
    ]

    def connector_key(
        self,
    ) -> str:
        """
        Return connector key.
        """

        return "diagnostic_public_record_connector"

    def search(
        self,
        request: PublicRecordSearchRequest,
    ) -> PublicRecordConnectorResult:
        """
        Return an empty diagnostic result.

        This does not fabricate records.
        """

        return self.empty_result(
            request=request,
            explanation=(
                "Diagnostic connector executed successfully. "
                "No public records are produced by this connector."
            ),
            warnings=[
                SourceWarning(
                    warning_code="diagnostic_connector_no_records",
                    message=(
                        "Diagnostic connector is not a public-record data source."
                    ),
                    severity="low",
                    source_id=self.source_id,
                )
            ],
        )


# ============================================================
# SECTION 11 - FACTORY FUNCTIONS
# ============================================================

def create_diagnostic_connector() -> DiagnosticPublicRecordConnector:
    """
    Create diagnostic connector instance.
    """

    return DiagnosticPublicRecordConnector()


def make_base_connector_not_implemented_result(
    *,
    connector_id: str,
    source_id: str,
    source_name: str,
    request: PublicRecordSearchRequest | None = None,
    reason: str | None = None,
) -> PublicRecordConnectorResult:
    """
    Create standard not-implemented result without instantiating connector.
    """

    return make_unavailable_connector_result(
        connector_id=connector_id,
        source_id=source_id,
        source_name=source_name,
        request=request,
        reason=reason or "Public-record connector is not implemented.",
    )


def validate_base_connector_governance() -> dict[str, Any]:
    """
    Validate base connector governance.
    """

    issues: list[dict[str, Any]] = []

    for key in [
        "mock_records_allowed",
        "mock_connector_responses_allowed",
        "fabricated_property_facts_allowed",
        "fabricated_tax_assessments_allowed",
        "fabricated_deeds_allowed",
        "fabricated_sale_history_allowed",
        "fabricated_listing_status_allowed",
        "active_listing_status_from_public_records_allowed",
        "under_contract_status_from_public_records_allowed",
        "bypass_access_controls_allowed",
        "uncontrolled_scraping_allowed",
    ]:
        if BASE_CONNECTOR_GOVERNANCE.get(key):
            issues.append(
                {
                    "issue_code": f"{key}_enabled",
                    "severity": "critical",
                    "message": f"{key} must remain False.",
                }
            )

    for key in [
        "source_attribution_required",
        "source_status_required",
        "retrieved_at_required",
        "confidence_required",
        "safe_http_client_required",
        "respect_source_terms_required",
    ]:
        if not BASE_CONNECTOR_GOVERNANCE.get(key):
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


# ============================================================
# SECTION 12 - MODULE DIAGNOSTICS
# ============================================================

def get_base_connector_metadata() -> dict[str, Any]:
    """
    Return base connector module metadata.
    """

    return {
        "name": BASE_CONNECTOR_NAME,
        "version": BASE_CONNECTOR_VERSION,
        "phase": BASE_CONNECTOR_PHASE,
        "status": BASE_CONNECTOR_STATUS,
        "generated_at": utc_now(),
    }


def get_base_connector_health() -> dict[str, Any]:
    """
    Return base connector health.
    """

    governance_validation = validate_base_connector_governance()
    diagnostic_connector = create_diagnostic_connector()

    return {
        "name": BASE_CONNECTOR_NAME,
        "version": BASE_CONNECTOR_VERSION,
        "phase": BASE_CONNECTOR_PHASE,
        "status": BASE_CONNECTOR_STATUS,
        "governance_valid": governance_validation["valid"],
        "governance_issue_count": governance_validation["issue_count"],
        "diagnostic_connector_loaded": isinstance(
            diagnostic_connector,
            DiagnosticPublicRecordConnector,
        ),
        "mock_records_allowed": BASE_CONNECTOR_GOVERNANCE[
            "mock_records_allowed"
        ],
        "fabricated_listing_status_allowed": BASE_CONNECTOR_GOVERNANCE[
            "fabricated_listing_status_allowed"
        ],
        "source_attribution_required": BASE_CONNECTOR_GOVERNANCE[
            "source_attribution_required"
        ],
        "generated_at": utc_now(),
    }


def get_base_connector_diagnostics() -> dict[str, Any]:
    """
    Return full base connector diagnostics.
    """

    diagnostic_connector = create_diagnostic_connector()

    return {
        "metadata": get_base_connector_metadata(),
        "health": get_base_connector_health(),
        "governance": BASE_CONNECTOR_GOVERNANCE.copy(),
        "supported_claims": list(BASE_PUBLIC_RECORD_SUPPORTED_CLAIMS),
        "unsupported_listing_claims": list(
            BASE_PUBLIC_RECORD_UNSUPPORTED_LISTING_CLAIMS
        ),
        "governance_validation": validate_base_connector_governance(),
        "diagnostic_connector": diagnostic_connector.diagnostics(),
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 13 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "BASE_CONNECTOR_NAME",
    "BASE_CONNECTOR_VERSION",
    "BASE_CONNECTOR_PHASE",
    "BASE_CONNECTOR_STATUS",
    "BASE_CONNECTOR_GOVERNANCE",
    "BASE_PUBLIC_RECORD_SUPPORTED_CLAIMS",
    "BASE_PUBLIC_RECORD_UNSUPPORTED_LISTING_CLAIMS",
    "PublicRecordConnectorMetadata",
    "PublicRecordConnectorExecutionContext",
    "PublicRecordConnectorValidationResult",
    "BasePublicRecordConnector",
    "DiagnosticPublicRecordConnector",
    "utc_now",
    "safe_string",
    "collapse_whitespace",
    "normalize_html_text",
    "normalize_money_text",
    "normalize_percent_text",
    "normalize_public_record_key",
    "make_connector_run_id",
    "make_connector_record_id",
    "request_has_address",
    "request_has_block_lot",
    "request_has_owner_reference",
    "infer_query_mode",
    "create_diagnostic_connector",
    "make_base_connector_not_implemented_result",
    "validate_base_connector_governance",
    "get_base_connector_metadata",
    "get_base_connector_health",
    "get_base_connector_diagnostics",
]


# ============================================================
# END OF FILE
# ============================================================