# ============================================================
# AUSSEM1
# PHASE 2.30 PART 4.00
# ENTERPRISE PUBLIC RECORDS ENGINE
# FILE: app/public_records/public_records_engine.py
# PURPOSE:
# Coordinate official public-record connectors for Aussem1.
#
# This engine provides:
# - connector orchestration
# - governed public-record lookup lifecycle
# - connector health checks
# - connector diagnostics
# - source-backed public-record aggregation
# - confidence-aware public-record result handling
# - manual-review routing
# - no-mock / no-fabrication enforcement
#
# This file does not create mock property records.
# This file does not fabricate property values.
# This file does not fabricate owner conclusions.
# This file does not fabricate listing status.
# This file does not claim active MLS status from public records.
# This file does not claim under-contract status from public records.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# REAL PUBLIC RECORDS ENGINE FOUNDATION ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from importlib import import_module
from typing import Any

from app.public_records.models import PublicRecordConnectorResult
from app.public_records.models import PublicRecordConnectorStatus
from app.public_records.models import PublicRecordReport
from app.public_records.models import PublicRecordSearchRequest
from app.public_records.models import PublicRecordStatus
from app.public_records.models import PublicRecordSummaryCard
from app.public_records.models import aggregate_connector_results
from app.public_records.models import build_public_record_summary_cards
from app.public_records.models import make_empty_public_record_report
from app.public_records.models import make_public_record_search_request
from app.sources.source_models import SourceConfidenceBand
from app.sources.source_models import SourceConfidenceReport
from app.sources.source_models import SourceError
from app.sources.source_models import SourceErrorType
from app.sources.source_models import SourceWarning
from app.sources.source_models import stable_hash


# ============================================================
# SECTION 02 - ENGINE METADATA
# ============================================================

PUBLIC_RECORDS_ENGINE_NAME = "Aussem1 Enterprise Public Records Engine"

PUBLIC_RECORDS_ENGINE_VERSION = "0.1.0"

PUBLIC_RECORDS_ENGINE_PHASE = "PHASE 2.30 PART 4.00"

PUBLIC_RECORDS_ENGINE_STATUS = "real_public_records_engine_foundation_active"

PUBLIC_RECORDS_ENGINE_RELEASE_CHANNEL = "development"


# ============================================================
# SECTION 03 - ENGINE GOVERNANCE
# ============================================================

PUBLIC_RECORDS_ENGINE_GOVERNANCE = {
    "mock_records_allowed": False,
    "mock_connector_responses_allowed": False,
    "fabricated_property_facts_allowed": False,
    "fabricated_property_values_allowed": False,
    "fabricated_owner_conclusions_allowed": False,
    "fabricated_sale_history_allowed": False,
    "fabricated_listing_status_allowed": False,
    "active_listing_status_from_public_records_allowed": False,
    "under_contract_status_from_public_records_allowed": False,
    "current_listing_price_from_public_records_allowed": False,
    "current_days_on_market_from_public_records_allowed": False,
    "source_attribution_required": True,
    "connector_status_required": True,
    "confidence_required": True,
    "manual_review_for_ambiguity": True,
    "manual_review_for_conflicts": True,
    "listing_feed_required_for_listing_status": True,
    "public_records_are_not_legal_advice": True,
    "tax_assessment_is_not_market_value": True,
    "gis_is_not_legal_survey": True,
}


# ============================================================
# SECTION 04 - CONNECTOR REGISTRY
# ============================================================

PUBLIC_RECORD_CONNECTOR_REGISTRY = {
    "nj_morris_tax_board_connector": {
        "connector_id": "nj_morris_tax_board_connector",
        "source_id": "nj_morris_tax_board",
        "source_name": "Morris County Tax Board",
        "module": "app.public_records.connectors.nj_morris_tax_board_connector",
        "class_name": "NJMorrisTaxBoardConnector",
        "factory_name": "create_nj_morris_tax_board_connector",
        "priority": 10,
        "jurisdiction": "Morris County, New Jersey",
        "state": "NJ",
        "county": "Morris",
        "domains": [
            "tax_board",
            "assessment",
            "parcel",
            "owner_reference",
            "sale_history",
        ],
        "enabled": True,
        "required": True,
    },
    "nj_morris_clerk_connector": {
        "connector_id": "nj_morris_clerk_connector",
        "source_id": "nj_morris_county_clerk_property_records",
        "source_name": "Morris County Clerk Online Property Records",
        "module": "app.public_records.connectors.nj_morris_clerk_connector",
        "class_name": "NJMorrisClerkConnector",
        "factory_name": "create_nj_morris_clerk_connector",
        "priority": 20,
        "jurisdiction": "Morris County, New Jersey",
        "state": "NJ",
        "county": "Morris",
        "domains": [
            "county_clerk",
            "deeds",
            "mortgages",
            "liens",
            "recorded_documents",
            "sale_history",
        ],
        "enabled": True,
        "required": False,
    },
    "nj_morris_gis_connector": {
        "connector_id": "nj_morris_gis_connector",
        "source_id": "nj_morris_gis_parcel_searcher",
        "source_name": "Morris County GIS Parcel Searcher",
        "module": "app.public_records.connectors.nj_morris_gis_connector",
        "class_name": "NJMorrisGISConnector",
        "factory_name": "create_nj_morris_gis_connector",
        "priority": 30,
        "jurisdiction": "Morris County, New Jersey",
        "state": "NJ",
        "county": "Morris",
        "domains": [
            "gis",
            "parcel",
            "municipal_context",
            "map_context",
            "building_facts",
        ],
        "enabled": True,
        "required": False,
    },
    "nj_state_modiv_connector": {
        "connector_id": "nj_state_modiv_connector",
        "source_id": "nj_state_parcels_modiv_composite",
        "source_name": "New Jersey Parcels and MOD-IV Composite",
        "module": "app.public_records.connectors.nj_state_modiv_connector",
        "class_name": "NJStateModIVConnector",
        "factory_name": "create_nj_state_modiv_connector",
        "priority": 40,
        "jurisdiction": "State of New Jersey",
        "state": "NJ",
        "county": None,
        "domains": [
            "statewide_parcel",
            "modiv",
            "assessment",
            "parcel",
        ],
        "enabled": True,
        "required": False,
    },
}


# ============================================================
# SECTION 05 - UNSUPPORTED LISTING CLAIMS
# ============================================================

PUBLIC_RECORDS_ENGINE_UNSUPPORTED_LISTING_CLAIMS = [
    "active_listing_status",
    "under_contract_status",
    "pending_status",
    "current_listing_price",
    "current_days_on_market",
    "current_showing_availability",
    "current_offer_deadline",
    "current_mls_status",
    "current_broker_confirmation",
    "current_broker_remarks",
    "current_offer_deadline",
]


# ============================================================
# SECTION 06 - UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(UTC).isoformat()


def safe_string(value: Any) -> str:
    """
    Convert unknown value into safe stripped string.
    """

    if value is None:
        return ""

    return str(value).strip()


def normalize_engine_key(value: Any) -> str:
    """
    Normalize engine key.
    """

    text = safe_string(value).lower()

    return "_".join(text.replace("-", " ").split())


def make_engine_run_id(
    *,
    request: PublicRecordSearchRequest | None = None,
    connector_ids: list[str] | None = None,
) -> str:
    """
    Create stable engine run ID.
    """

    payload = {
        "request": request.to_dict() if request else None,
        "connector_ids": connector_ids or [],
        "timestamp_bucket": utc_now()[:16],
    }

    return f"public-records-run-{stable_hash(payload)[:18]}"


def public_records_claim_requires_listing_feed(claim: str) -> bool:
    """
    Return whether claim requires a listing feed.
    """

    normalized = normalize_engine_key(claim)

    return normalized in PUBLIC_RECORDS_ENGINE_UNSUPPORTED_LISTING_CLAIMS


def is_morris_county_request(
    request: PublicRecordSearchRequest,
) -> bool:
    """
    Return whether request appears to target Morris County.
    """

    request_state = safe_string(request.state).upper()
    request_county = safe_string(request.county).lower()

    if request_state and request_state != "NJ":
        return False

    if request_county and "morris" not in request_county:
        return False

    return True


def request_has_any_search_signal(
    request: PublicRecordSearchRequest,
) -> bool:
    """
    Return whether request has enough data to run connectors.
    """

    if request.raw_query:
        return True

    if request.street_address:
        return True

    if request.block and request.lot:
        return True

    if request.owner_reference:
        return True

    if request.address and (
        request.address.raw_address
        or request.address.street_address
        or request.address.normalized_address
    ):
        return True

    return False


def connector_result_to_dict(
    result: PublicRecordConnectorResult,
) -> dict[str, Any]:
    """
    Convert connector result to dictionary safely.
    """

    if hasattr(result, "to_dict"):
        return result.to_dict()

    if hasattr(result, "__dict__"):
        return asdict(result)

    return {
        "status": "unknown",
        "value": str(result),
    }


def safe_report_to_dict(
    report: PublicRecordReport | Any,
) -> dict[str, Any]:
    """
    Convert public-record report to dictionary safely.
    """

    if report is None:
        return {}

    if hasattr(report, "to_dict"):
        return report.to_dict()

    if hasattr(report, "__dict__"):
        try:
            return asdict(report)
        except TypeError:
            return dict(report.__dict__)

    return {
        "value": str(report),
    }


def get_connector_record_count(
    result: PublicRecordConnectorResult,
) -> int:
    """
    Count normalized records on connector result.
    """

    record_fields = [
        "parcel_records",
        "tax_assessment_records",
        "property_tax_records",
        "building_facts_records",
        "recorded_document_references",
        "deed_records",
        "mortgage_records",
        "lien_records",
        "sale_history_records",
        "owner_reference_records",
        "municipal_context_records",
        "gis_context_records",
        "modiv_records",
    ]

    total = 0

    for field_name in record_fields:
        value = getattr(result, field_name, None)

        if isinstance(value, list):
            total += len(value)

    return total


def result_manual_review_required(
    result: PublicRecordConnectorResult,
) -> bool:
    """
    Return whether result needs manual review.
    """

    confidence_report = getattr(result, "confidence_report", None)

    if confidence_report is not None:
        if getattr(confidence_report, "manual_review_required", False):
            return True

    errors = getattr(result, "errors", []) or []

    for error in errors:
        if getattr(error, "manual_review_required", False):
            return True

    status = getattr(result, "status", "")

    if status == PublicRecordStatus.MANUAL_REVIEW_REQUIRED.value:
        return True

    if status == PublicRecordConnectorStatus.MANUAL_REVIEW_REQUIRED.value:
        return True

    return False


# ============================================================
# SECTION 07 - ENGINE CONFIGURATION MODEL
# ============================================================

@dataclass
class PublicRecordsEngineConfig:
    """
    Public Records Engine configuration.
    """

    enabled: bool = True
    strict_no_mock_mode: bool = True
    allow_partial_results: bool = True
    stop_on_required_connector_failure: bool = False
    manual_review_on_conflict: bool = True
    include_connector_diagnostics: bool = True
    include_raw_connector_results: bool = False
    default_state: str = "NJ"
    default_county: str | None = "Morris"
    connector_timeout_seconds: int = 30
    enabled_connector_ids: list[str] = field(
        default_factory=lambda: [
            "nj_morris_tax_board_connector",
            "nj_morris_clerk_connector",
            "nj_morris_gis_connector",
            "nj_state_modiv_connector",
        ]
    )
    disabled_connector_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(
        default_factory=lambda: [
            "Public records engine uses real source-governed connectors only.",
            "No fake property facts are allowed.",
            "Listing status requires a future authorized listing feed.",
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert config to dictionary.
        """

        return asdict(self)


# ============================================================
# SECTION 08 - ENGINE VALIDATION MODELS
# ============================================================

@dataclass
class PublicRecordsEngineValidationResult:
    """
    Validation result for engine requests and governance.
    """

    valid: bool
    status: str
    errors: list[SourceError] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)
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
            "manual_review_required": self.manual_review_required,
            "checked_at": self.checked_at,
        }


@dataclass
class PublicRecordsConnectorExecution:
    """
    Execution metadata for one connector run.
    """

    connector_id: str
    source_id: str | None = None
    source_name: str | None = None
    started_at: str = field(default_factory=utc_now)
    finished_at: str | None = None
    status: str = "pending"
    elapsed_ms: float | None = None
    record_count: int = 0
    manual_review_required: bool = False
    error_count: int = 0
    warning_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def finish(
        self,
        *,
        status: str,
        record_count: int = 0,
        manual_review_required: bool = False,
        error_count: int = 0,
        warning_count: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Finish execution record.
        """

        self.finished_at = utc_now()
        self.status = status
        self.record_count = record_count
        self.manual_review_required = manual_review_required
        self.error_count = error_count
        self.warning_count = warning_count

        if metadata:
            self.metadata.update(metadata)

        try:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.finished_at)
            self.elapsed_ms = (end - start).total_seconds() * 1000
        except ValueError:
            self.elapsed_ms = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert execution to dictionary.
        """

        return asdict(self)


@dataclass
class PublicRecordsEngineResult:
    """
    Result of a complete public-record engine run.
    """

    run_id: str
    status: str
    request: PublicRecordSearchRequest
    connector_results: list[PublicRecordConnectorResult] = field(
        default_factory=list
    )
    public_record_report: PublicRecordReport | Any | None = None
    summary_cards: list[PublicRecordSummaryCard] = field(default_factory=list)
    executions: list[PublicRecordsConnectorExecution] = field(
        default_factory=list
    )
    errors: list[SourceError] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)
    confidence_report: SourceConfidenceReport | None = None
    manual_review_required: bool = False
    started_at: str = field(default_factory=utc_now)
    finished_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def finish(self) -> None:
        """
        Mark engine result complete.
        """

        self.finished_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert engine result to dictionary.
        """

        return {
            "run_id": self.run_id,
            "status": self.status,
            "request": self.request.to_dict(),
            "connector_results": [
                connector_result_to_dict(result)
                for result in self.connector_results
            ],
            "public_record_report": safe_report_to_dict(
                self.public_record_report
            ),
            "summary_cards": [
                card.to_dict() if hasattr(card, "to_dict") else asdict(card)
                for card in self.summary_cards
            ],
            "executions": [
                execution.to_dict()
                for execution in self.executions
            ],
            "errors": [
                error.to_dict()
                for error in self.errors
            ],
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
            "confidence_report": (
                self.confidence_report.to_dict()
                if self.confidence_report
                else None
            ),
            "manual_review_required": self.manual_review_required,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "metadata": self.metadata,
        }


# ============================================================
# SECTION 09 - ENGINE WARNING AND ERROR FACTORIES
# ============================================================

def make_engine_warning(
    *,
    warning_code: str,
    message: str,
    severity: str = "medium",
) -> SourceWarning:
    """
    Build standardized engine warning.
    """

    return SourceWarning(
        warning_code=warning_code,
        message=message,
        severity=severity,
        source_id="public_records_engine",
    )


def make_engine_error(
    *,
    error_type: str,
    message: str,
    recoverable: bool = True,
    retry_recommended: bool = False,
    manual_review_required: bool = False,
) -> SourceError:
    """
    Build standardized engine error.
    """

    return SourceError(
        error_type=error_type,
        message=message,
        source_id="public_records_engine",
        source_name=PUBLIC_RECORDS_ENGINE_NAME,
        recoverable=recoverable,
        retry_recommended=retry_recommended,
        manual_review_required=manual_review_required,
    )


# ============================================================
# SECTION 10 - CONNECTOR LOADING
# ============================================================

def get_public_record_connector_registry() -> dict[str, dict[str, Any]]:
    """
    Return connector registry copy.
    """

    return {
        connector_id: metadata.copy()
        for connector_id, metadata in PUBLIC_RECORD_CONNECTOR_REGISTRY.items()
    }


def get_enabled_connector_metadata(
    config: PublicRecordsEngineConfig | None = None,
) -> list[dict[str, Any]]:
    """
    Return enabled connector metadata sorted by priority.
    """

    active_config = config or PublicRecordsEngineConfig()

    enabled: list[dict[str, Any]] = []

    for connector_id, metadata in PUBLIC_RECORD_CONNECTOR_REGISTRY.items():
        if not metadata.get("enabled"):
            continue

        if connector_id in active_config.disabled_connector_ids:
            continue

        if connector_id not in active_config.enabled_connector_ids:
            continue

        enabled.append(metadata.copy())

    return sorted(
        enabled,
        key=lambda item: int(item.get("priority", 999)),
    )


def load_connector_factory(
    connector_metadata: dict[str, Any],
) -> Any | None:
    """
    Load connector factory from metadata.
    """

    module_name = connector_metadata.get("module")
    factory_name = connector_metadata.get("factory_name")

    if not module_name or not factory_name:
        return None

    try:
        module = import_module(module_name)
    except Exception:
        return None

    return getattr(module, factory_name, None)


def load_connector_instance(
    connector_metadata: dict[str, Any],
) -> Any | None:
    """
    Load connector instance from metadata.
    """

    factory = load_connector_factory(connector_metadata)

    if factory is None:
        return None

    try:
        return factory()
    except Exception:
        return None


def load_enabled_connectors(
    config: PublicRecordsEngineConfig | None = None,
) -> list[Any]:
    """
    Load enabled connector instances.
    """

    connectors: list[Any] = []

    for metadata in get_enabled_connector_metadata(config):
        connector = load_connector_instance(metadata)

        if connector is not None:
            connectors.append(connector)

    return connectors


def get_connector_import_status(
    config: PublicRecordsEngineConfig | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Return connector import status.
    """

    status: dict[str, dict[str, Any]] = {}

    for metadata in get_enabled_connector_metadata(config):
        connector_id = metadata["connector_id"]

        factory = load_connector_factory(metadata)
        connector = None

        if factory is not None:
            try:
                connector = factory()
            except Exception as exc:
                status[connector_id] = {
                    "connector_id": connector_id,
                    "loaded": False,
                    "factory_loaded": True,
                    "instance_loaded": False,
                    "error": str(exc),
                    "metadata": metadata,
                }
                continue

        status[connector_id] = {
            "connector_id": connector_id,
            "loaded": connector is not None,
            "factory_loaded": factory is not None,
            "instance_loaded": connector is not None,
            "error": None,
            "metadata": metadata,
        }

    return status


# ============================================================
# SECTION 11 - PUBLIC RECORDS ENGINE
# ============================================================

class PublicRecordsEngine:
    """
    Enterprise public-record orchestration engine.

    This class coordinates source-governed public-record connectors.
    It never fabricates missing property facts. If a connector cannot
    retrieve or parse records, the engine preserves the unavailable,
    partial, empty, or manual-review status.
    """

    def __init__(
        self,
        *,
        config: PublicRecordsEngineConfig | None = None,
    ) -> None:
        self.config = config or PublicRecordsEngineConfig()

    # ========================================================
    # SECTION 11.01 - GOVERNANCE
    # ========================================================

    def get_governance(self) -> dict[str, Any]:
        """
        Return engine governance.
        """

        return PUBLIC_RECORDS_ENGINE_GOVERNANCE.copy()

    def validate_governance(self) -> PublicRecordsEngineValidationResult:
        """
        Validate public-record engine governance.
        """

        errors: list[SourceError] = []
        warnings: list[SourceWarning] = []

        false_keys = [
            "mock_records_allowed",
            "mock_connector_responses_allowed",
            "fabricated_property_facts_allowed",
            "fabricated_property_values_allowed",
            "fabricated_owner_conclusions_allowed",
            "fabricated_sale_history_allowed",
            "fabricated_listing_status_allowed",
            "active_listing_status_from_public_records_allowed",
            "under_contract_status_from_public_records_allowed",
            "current_listing_price_from_public_records_allowed",
            "current_days_on_market_from_public_records_allowed",
        ]

        for key in false_keys:
            if PUBLIC_RECORDS_ENGINE_GOVERNANCE.get(key):
                errors.append(
                    make_engine_error(
                        error_type=SourceErrorType.MANUAL_REVIEW_REQUIRED.value,
                        message=f"Governance violation: {key} must remain False.",
                        recoverable=False,
                        manual_review_required=True,
                    )
                )

        true_keys = [
            "source_attribution_required",
            "connector_status_required",
            "confidence_required",
            "manual_review_for_ambiguity",
            "manual_review_for_conflicts",
            "listing_feed_required_for_listing_status",
            "public_records_are_not_legal_advice",
            "tax_assessment_is_not_market_value",
            "gis_is_not_legal_survey",
        ]

        for key in true_keys:
            if not PUBLIC_RECORDS_ENGINE_GOVERNANCE.get(key):
                errors.append(
                    make_engine_error(
                        error_type=SourceErrorType.MANUAL_REVIEW_REQUIRED.value,
                        message=f"Governance violation: {key} must remain True.",
                        recoverable=False,
                        manual_review_required=True,
                    )
                )

        if not self.config.strict_no_mock_mode:
            errors.append(
                make_engine_error(
                    error_type=SourceErrorType.MANUAL_REVIEW_REQUIRED.value,
                    message="Engine strict_no_mock_mode must remain enabled.",
                    recoverable=False,
                    manual_review_required=True,
                )
            )

        if not self.config.enabled:
            warnings.append(
                make_engine_warning(
                    warning_code="engine_disabled",
                    message="Public Records Engine is currently disabled.",
                    severity="high",
                )
            )

        return PublicRecordsEngineValidationResult(
            valid=not errors,
            status="valid" if not errors else "error",
            errors=errors,
            warnings=warnings,
            manual_review_required=bool(errors),
        )

    # ========================================================
    # SECTION 11.02 - REQUEST VALIDATION
    # ========================================================

    def validate_request(
        self,
        request: PublicRecordSearchRequest,
    ) -> PublicRecordsEngineValidationResult:
        """
        Validate public-record search request.
        """

        errors: list[SourceError] = []
        warnings: list[SourceWarning] = []

        governance = self.validate_governance()

        errors.extend(governance.errors)
        warnings.extend(governance.warnings)

        if not self.config.enabled:
            errors.append(
                make_engine_error(
                    error_type=SourceErrorType.SOURCE_UNAVAILABLE.value,
                    message="Public Records Engine is disabled.",
                    recoverable=True,
                    retry_recommended=False,
                )
            )

        if not request_has_any_search_signal(request):
            errors.append(
                make_engine_error(
                    error_type=SourceErrorType.INVALID_QUERY.value,
                    message=(
                        "Public-record lookup requires address, block/lot, "
                        "owner reference, or raw query."
                    ),
                    recoverable=True,
                )
            )

        if request.state:
            request_state = safe_string(request.state).upper()

            if request_state != "NJ":
                warnings.append(
                    make_engine_warning(
                        warning_code="state_outside_initial_scope",
                        message=(
                            "Current public-record connector set is optimized "
                            "for New Jersey first."
                        ),
                        severity="medium",
                    )
                )

        if request.county:
            request_county = safe_string(request.county).lower()

            if "morris" not in request_county:
                warnings.append(
                    make_engine_warning(
                        warning_code="county_outside_initial_scope",
                        message=(
                            "Current county connector set is optimized for "
                            "Morris County, NJ first."
                        ),
                        severity="medium",
                    )
                )

        return PublicRecordsEngineValidationResult(
            valid=not errors,
            status="valid" if not errors else "error",
            errors=errors,
            warnings=warnings,
            manual_review_required=any(
                error.manual_review_required
                for error in errors
            ),
        )

    # ========================================================
    # SECTION 11.03 - REQUEST FACTORY
    # ========================================================

    def make_request(
        self,
        *,
        raw_query: str | None = None,
        street_address: str | None = None,
        municipality: str | None = None,
        county: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
        block: str | None = None,
        lot: str | None = None,
        qualifier: str | None = None,
        owner_reference: str | None = None,
        tax_year: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PublicRecordSearchRequest:
        """
        Create public-record search request.
        """

        return make_public_record_search_request(
            raw_query=raw_query,
            street_address=street_address,
            municipality=municipality,
            county=county or self.config.default_county,
            state=state or self.config.default_state,
            postal_code=postal_code,
            block=block,
            lot=lot,
            qualifier=qualifier,
            owner_reference=owner_reference,
            tax_year=tax_year,
            metadata=metadata or {},
        )

    # ========================================================
    # SECTION 11.04 - CONNECTOR SELECTION
    # ========================================================

    def get_connector_metadata_for_request(
        self,
        request: PublicRecordSearchRequest,
    ) -> list[dict[str, Any]]:
        """
        Select connector metadata for request.
        """

        connector_metadata = get_enabled_connector_metadata(self.config)

        selected: list[dict[str, Any]] = []

        for metadata in connector_metadata:
            connector_state = safe_string(metadata.get("state")).upper()
            connector_county = safe_string(metadata.get("county")).lower()

            if request.state and connector_state:
                if safe_string(request.state).upper() != connector_state:
                    continue

            if request.county and connector_county:
                if "morris" not in safe_string(request.county).lower():
                    continue

            selected.append(metadata)

        return selected

    def load_connectors_for_request(
        self,
        request: PublicRecordSearchRequest,
    ) -> list[Any]:
        """
        Load connector instances for request.
        """

        connectors: list[Any] = []

        for metadata in self.get_connector_metadata_for_request(request):
            connector = load_connector_instance(metadata)

            if connector is not None:
                connectors.append(connector)

        return connectors

    # ========================================================
    # SECTION 11.05 - CONNECTOR EXECUTION
    # ========================================================

    def execute_connector(
        self,
        *,
        connector: Any,
        request: PublicRecordSearchRequest,
    ) -> tuple[PublicRecordConnectorResult | None, PublicRecordsConnectorExecution]:
        """
        Execute one connector safely.
        """

        connector_id = getattr(connector, "connector_id", "unknown_connector")
        source_id = getattr(connector, "source_id", None)
        source_name = getattr(connector, "source_name", None)

        execution = PublicRecordsConnectorExecution(
            connector_id=connector_id,
            source_id=source_id,
            source_name=source_name,
        )

        try:
            result = connector.search(request)
        except Exception as exc:
            execution.finish(
                status=PublicRecordConnectorStatus.ERROR.value,
                error_count=1,
                manual_review_required=True,
                metadata={
                    "exception": str(exc),
                    "exception_type": exc.__class__.__name__,
                },
            )

            return None, execution

        record_count = get_connector_record_count(result)
        errors = getattr(result, "errors", []) or []
        warnings = getattr(result, "warnings", []) or []
        status = getattr(
            result,
            "status",
            PublicRecordConnectorStatus.UNKNOWN.value,
        )

        execution.finish(
            status=status,
            record_count=record_count,
            manual_review_required=result_manual_review_required(result),
            error_count=len(errors),
            warning_count=len(warnings),
            metadata={
                "result_status": status,
            },
        )

        return result, execution

    # ========================================================
    # SECTION 11.06 - MAIN SEARCH
    # ========================================================

    def search(
        self,
        request: PublicRecordSearchRequest,
    ) -> PublicRecordsEngineResult:
        """
        Execute full public-record lookup across selected connectors.
        """

        connector_metadata = self.get_connector_metadata_for_request(request)
        connector_ids = [
            metadata["connector_id"]
            for metadata in connector_metadata
        ]

        run_id = make_engine_run_id(
            request=request,
            connector_ids=connector_ids,
        )

        engine_result = PublicRecordsEngineResult(
            run_id=run_id,
            status="started",
            request=request,
            metadata={
                "engine": PUBLIC_RECORDS_ENGINE_NAME,
                "phase": PUBLIC_RECORDS_ENGINE_PHASE,
                "connector_ids": connector_ids,
                "connector_count": len(connector_ids),
            },
        )

        validation = self.validate_request(request)

        engine_result.errors.extend(validation.errors)
        engine_result.warnings.extend(validation.warnings)

        if not validation.valid:
            engine_result.status = "error"
            engine_result.manual_review_required = (
                validation.manual_review_required
            )
            engine_result.confidence_report = self.build_engine_confidence_report(
                connector_results=[],
                errors=engine_result.errors,
                warnings=engine_result.warnings,
                manual_review_required=engine_result.manual_review_required,
            )
            engine_result.public_record_report = make_empty_public_record_report(
                request=request,
                reason="Public Records Engine request validation failed.",
            )
            engine_result.finish()
            return engine_result

        connectors = self.load_connectors_for_request(request)

        if not connectors:
            engine_result.status = "empty"
            engine_result.warnings.append(
                make_engine_warning(
                    warning_code="no_connectors_loaded",
                    message="No public-record connectors could be loaded.",
                    severity="high",
                )
            )
            engine_result.public_record_report = make_empty_public_record_report(
                request=request,
                reason="No public-record connectors could be loaded.",
            )
            engine_result.confidence_report = self.build_engine_confidence_report(
                connector_results=[],
                errors=engine_result.errors,
                warnings=engine_result.warnings,
                manual_review_required=True,
            )
            engine_result.manual_review_required = True
            engine_result.finish()
            return engine_result

        for connector in connectors:
            result, execution = self.execute_connector(
                connector=connector,
                request=request,
            )

            engine_result.executions.append(execution)

            if result is not None:
                engine_result.connector_results.append(result)

                engine_result.errors.extend(
                    getattr(result, "errors", []) or []
                )
                engine_result.warnings.extend(
                    getattr(result, "warnings", []) or []
                )

            elif self.config.stop_on_required_connector_failure:
                engine_result.errors.append(
                    make_engine_error(
                        error_type=SourceErrorType.SOURCE_UNAVAILABLE.value,
                        message=(
                            f"Required connector failed: "
                            f"{execution.connector_id}"
                        ),
                        recoverable=True,
                        retry_recommended=True,
                        manual_review_required=True,
                    )
                )
                break

        engine_result.public_record_report = self.aggregate_results(
            request=request,
            connector_results=engine_result.connector_results,
        )

        engine_result.summary_cards = self.build_summary_cards(
            report=engine_result.public_record_report,
            connector_results=engine_result.connector_results,
        )

        engine_result.manual_review_required = self.should_require_manual_review(
            connector_results=engine_result.connector_results,
            errors=engine_result.errors,
            warnings=engine_result.warnings,
        )

        engine_result.confidence_report = self.build_engine_confidence_report(
            connector_results=engine_result.connector_results,
            errors=engine_result.errors,
            warnings=engine_result.warnings,
            manual_review_required=engine_result.manual_review_required,
        )

        engine_result.status = self.determine_engine_status(
            connector_results=engine_result.connector_results,
            errors=engine_result.errors,
        )

        engine_result.metadata.update(
            {
                "record_count": sum(
                    get_connector_record_count(result)
                    for result in engine_result.connector_results
                ),
                "manual_review_required": (
                    engine_result.manual_review_required
                ),
                "unsupported_listing_claims": list(
                    PUBLIC_RECORDS_ENGINE_UNSUPPORTED_LISTING_CLAIMS
                ),
                "governance": self.get_governance(),
            }
        )

        engine_result.finish()

        return engine_result

    # ========================================================
    # SECTION 11.07 - ADDRESS SEARCH CONVENIENCE
    # ========================================================

    def search_by_address(
        self,
        *,
        address: str,
        municipality: str | None = None,
        county: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PublicRecordsEngineResult:
        """
        Search public records by address.
        """

        request = self.make_request(
            raw_query=address,
            street_address=address,
            municipality=municipality,
            county=county,
            state=state,
            postal_code=postal_code,
            metadata=metadata or {},
        )

        return self.search(request)

    def search_by_block_lot(
        self,
        *,
        block: str,
        lot: str,
        qualifier: str | None = None,
        municipality: str | None = None,
        county: str | None = None,
        state: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PublicRecordsEngineResult:
        """
        Search public records by block and lot.
        """

        request = self.make_request(
            block=block,
            lot=lot,
            qualifier=qualifier,
            municipality=municipality,
            county=county,
            state=state,
            metadata=metadata or {},
        )

        return self.search(request)

    def search_by_owner_reference(
        self,
        *,
        owner_reference: str,
        municipality: str | None = None,
        county: str | None = None,
        state: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PublicRecordsEngineResult:
        """
        Search public records by owner reference.
        """

        request = self.make_request(
            owner_reference=owner_reference,
            municipality=municipality,
            county=county,
            state=state,
            metadata=metadata or {},
        )

        return self.search(request)

    # ========================================================
    # SECTION 11.08 - AGGREGATION
    # ========================================================

    def aggregate_results(
        self,
        *,
        request: PublicRecordSearchRequest,
        connector_results: list[PublicRecordConnectorResult],
    ) -> PublicRecordReport | Any:
        """
        Aggregate connector results into a public-record report.
        """

        if not connector_results:
            return make_empty_public_record_report(
                request=request,
                reason="No connector results were available.",
            )

        try:
            return aggregate_connector_results(
                request=request,
                connector_results=connector_results,
            )
        except TypeError:
            return aggregate_connector_results(
                connector_results=connector_results,
                request=request,
            )
        except Exception:
            return make_empty_public_record_report(
                request=request,
                reason=(
                    "Connector results were available, but aggregation failed."
                ),
            )

    def build_summary_cards(
        self,
        *,
        report: PublicRecordReport | Any,
        connector_results: list[PublicRecordConnectorResult],
    ) -> list[PublicRecordSummaryCard]:
        """
        Build summary cards from report.
        """

        try:
            return build_public_record_summary_cards(report)
        except Exception:
            return []

    # ========================================================
    # SECTION 11.09 - STATUS AND CONFIDENCE
    # ========================================================

    def determine_engine_status(
        self,
        *,
        connector_results: list[PublicRecordConnectorResult],
        errors: list[SourceError],
    ) -> str:
        """
        Determine final engine status.
        """

        if not connector_results and errors:
            return PublicRecordConnectorStatus.ERROR.value

        if not connector_results:
            return PublicRecordConnectorStatus.EMPTY.value

        total_records = sum(
            get_connector_record_count(result)
            for result in connector_results
        )

        if total_records > 0 and errors:
            return PublicRecordConnectorStatus.PARTIAL.value

        if total_records > 0:
            return PublicRecordConnectorStatus.AVAILABLE.value

        if errors:
            return PublicRecordConnectorStatus.ERROR.value

        return PublicRecordConnectorStatus.EMPTY.value

    def should_require_manual_review(
        self,
        *,
        connector_results: list[PublicRecordConnectorResult],
        errors: list[SourceError],
        warnings: list[SourceWarning],
    ) -> bool:
        """
        Determine whether manual review should be required.
        """

        if any(error.manual_review_required for error in errors):
            return True

        if any(result_manual_review_required(result) for result in connector_results):
            return True

        high_warnings = [
            warning
            for warning in warnings
            if getattr(warning, "severity", "") == "high"
        ]

        if high_warnings:
            return True

        return False

    def build_engine_confidence_report(
        self,
        *,
        connector_results: list[PublicRecordConnectorResult],
        errors: list[SourceError],
        warnings: list[SourceWarning],
        manual_review_required: bool,
    ) -> SourceConfidenceReport:
        """
        Build confidence report for full engine run.
        """

        if not connector_results:
            confidence = 0.0
        else:
            total_records = sum(
                get_connector_record_count(result)
                for result in connector_results
            )
            successful_connectors = [
                result
                for result in connector_results
                if getattr(result, "status", None)
                in [
                    PublicRecordConnectorStatus.AVAILABLE.value,
                    PublicRecordConnectorStatus.PARTIAL.value,
                    PublicRecordConnectorStatus.EMPTY.value,
                ]
            ]

            confidence = 0.20

            if successful_connectors:
                confidence += 0.20

            if total_records > 0:
                confidence += 0.30

            if len(successful_connectors) >= 2:
                confidence += 0.15

            if errors:
                confidence -= 0.20

            if manual_review_required:
                confidence -= 0.15

            confidence = max(0.0, min(0.85, confidence))

        if confidence >= 0.75:
            band = SourceConfidenceBand.HIGH.value
        elif confidence >= 0.50:
            band = SourceConfidenceBand.MEDIUM.value
        elif confidence > 0:
            band = SourceConfidenceBand.LOW.value
        else:
            band = SourceConfidenceBand.UNKNOWN.value

        positive_factors: list[str] = []
        negative_factors: list[str] = []
        missing_factors: list[str] = []

        if connector_results:
            positive_factors.append(
                "One or more public-record connectors executed."
            )
        else:
            missing_factors.append(
                "No public-record connector results were available."
            )

        if sum(get_connector_record_count(result) for result in connector_results):
            positive_factors.append(
                "One or more normalized public-record records were returned."
            )
        else:
            missing_factors.append(
                "No normalized public-record records were returned."
            )

        if errors:
            negative_factors.append(
                "One or more errors occurred during public-record lookup."
            )

        if manual_review_required:
            negative_factors.append(
                "Manual review is required before relying on these results."
            )

        missing_factors.append(
            "Current MLS/listing status requires a future authorized listing feed."
        )

        return SourceConfidenceReport(
            confidence=confidence,
            confidence_band=band,
            positive_factors=positive_factors,
            negative_factors=negative_factors,
            missing_factors=missing_factors,
            manual_review_required=manual_review_required,
            explanation=(
                "Public-record confidence is based on connector execution, "
                "normalized record availability, errors, and manual-review flags. "
                "It is not a market-value confidence score."
            ),
        )

    # ========================================================
    # SECTION 11.10 - DIAGNOSTICS
    # ========================================================

    def health(self) -> dict[str, Any]:
        """
        Return public-record engine health.
        """

        governance = self.validate_governance()
        import_status = get_connector_import_status(self.config)

        loaded_count = sum(
            1
            for item in import_status.values()
            if item["loaded"]
        )

        return {
            "name": PUBLIC_RECORDS_ENGINE_NAME,
            "version": PUBLIC_RECORDS_ENGINE_VERSION,
            "phase": PUBLIC_RECORDS_ENGINE_PHASE,
            "status": PUBLIC_RECORDS_ENGINE_STATUS,
            "enabled": self.config.enabled,
            "governance_valid": governance.valid,
            "governance_error_count": len(governance.errors),
            "connector_count": len(import_status),
            "loaded_connector_count": loaded_count,
            "mock_records_allowed": PUBLIC_RECORDS_ENGINE_GOVERNANCE[
                "mock_records_allowed"
            ],
            "fabricated_listing_status_allowed": (
                PUBLIC_RECORDS_ENGINE_GOVERNANCE[
                    "fabricated_listing_status_allowed"
                ]
            ),
            "listing_feed_required_for_listing_status": (
                PUBLIC_RECORDS_ENGINE_GOVERNANCE[
                    "listing_feed_required_for_listing_status"
                ]
            ),
            "generated_at": utc_now(),
        }

    def diagnostics(self) -> dict[str, Any]:
        """
        Return full engine diagnostics.
        """

        return {
            "metadata": get_public_records_engine_metadata(),
            "health": self.health(),
            "config": self.config.to_dict(),
            "governance": self.get_governance(),
            "connector_registry": get_public_record_connector_registry(),
            "connector_import_status": get_connector_import_status(self.config),
            "enabled_connectors": get_enabled_connector_metadata(self.config),
            "unsupported_listing_claims": list(
                PUBLIC_RECORDS_ENGINE_UNSUPPORTED_LISTING_CLAIMS
            ),
            "governance_validation": self.validate_governance().to_dict(),
            "generated_at": utc_now(),
        }


# ============================================================
# SECTION 12 - FACTORY FUNCTIONS
# ============================================================

def create_public_records_engine(
    *,
    config: PublicRecordsEngineConfig | None = None,
) -> PublicRecordsEngine:
    """
    Create Public Records Engine.
    """

    return PublicRecordsEngine(config=config)


def search_public_records(
    request: PublicRecordSearchRequest,
    *,
    config: PublicRecordsEngineConfig | None = None,
) -> PublicRecordsEngineResult:
    """
    Search public records using default engine.
    """

    engine = create_public_records_engine(config=config)

    return engine.search(request)


def search_public_records_by_address(
    *,
    address: str,
    municipality: str | None = None,
    county: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    metadata: dict[str, Any] | None = None,
    config: PublicRecordsEngineConfig | None = None,
) -> PublicRecordsEngineResult:
    """
    Search public records by address using default engine.
    """

    engine = create_public_records_engine(config=config)

    return engine.search_by_address(
        address=address,
        municipality=municipality,
        county=county,
        state=state,
        postal_code=postal_code,
        metadata=metadata,
    )


def search_public_records_by_block_lot(
    *,
    block: str,
    lot: str,
    qualifier: str | None = None,
    municipality: str | None = None,
    county: str | None = None,
    state: str | None = None,
    metadata: dict[str, Any] | None = None,
    config: PublicRecordsEngineConfig | None = None,
) -> PublicRecordsEngineResult:
    """
    Search public records by block/lot using default engine.
    """

    engine = create_public_records_engine(config=config)

    return engine.search_by_block_lot(
        block=block,
        lot=lot,
        qualifier=qualifier,
        municipality=municipality,
        county=county,
        state=state,
        metadata=metadata,
    )


def search_public_records_by_owner_reference(
    *,
    owner_reference: str,
    municipality: str | None = None,
    county: str | None = None,
    state: str | None = None,
    metadata: dict[str, Any] | None = None,
    config: PublicRecordsEngineConfig | None = None,
) -> PublicRecordsEngineResult:
    """
    Search public records by owner reference using default engine.
    """

    engine = create_public_records_engine(config=config)

    return engine.search_by_owner_reference(
        owner_reference=owner_reference,
        municipality=municipality,
        county=county,
        state=state,
        metadata=metadata,
    )


# ============================================================
# SECTION 13 - MODULE DIAGNOSTICS
# ============================================================

def get_public_records_engine_metadata() -> dict[str, Any]:
    """
    Return public records engine metadata.
    """

    return {
        "name": PUBLIC_RECORDS_ENGINE_NAME,
        "version": PUBLIC_RECORDS_ENGINE_VERSION,
        "phase": PUBLIC_RECORDS_ENGINE_PHASE,
        "status": PUBLIC_RECORDS_ENGINE_STATUS,
        "release_channel": PUBLIC_RECORDS_ENGINE_RELEASE_CHANNEL,
        "generated_at": utc_now(),
    }


def get_public_records_engine_health() -> dict[str, Any]:
    """
    Return public records engine health.
    """

    engine = create_public_records_engine()

    return engine.health()


def get_public_records_engine_diagnostics() -> dict[str, Any]:
    """
    Return public records engine diagnostics.
    """

    engine = create_public_records_engine()

    return engine.diagnostics()


def validate_public_records_engine_governance() -> dict[str, Any]:
    """
    Validate public records engine governance.
    """

    engine = create_public_records_engine()

    return engine.validate_governance().to_dict()


# ============================================================
# SECTION 14 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "PUBLIC_RECORDS_ENGINE_NAME",
    "PUBLIC_RECORDS_ENGINE_VERSION",
    "PUBLIC_RECORDS_ENGINE_PHASE",
    "PUBLIC_RECORDS_ENGINE_STATUS",
    "PUBLIC_RECORDS_ENGINE_RELEASE_CHANNEL",
    "PUBLIC_RECORDS_ENGINE_GOVERNANCE",
    "PUBLIC_RECORD_CONNECTOR_REGISTRY",
    "PUBLIC_RECORDS_ENGINE_UNSUPPORTED_LISTING_CLAIMS",
    "PublicRecordsEngineConfig",
    "PublicRecordsEngineValidationResult",
    "PublicRecordsConnectorExecution",
    "PublicRecordsEngineResult",
    "PublicRecordsEngine",
    "utc_now",
    "safe_string",
    "normalize_engine_key",
    "make_engine_run_id",
    "public_records_claim_requires_listing_feed",
    "is_morris_county_request",
    "request_has_any_search_signal",
    "connector_result_to_dict",
    "safe_report_to_dict",
    "get_connector_record_count",
    "result_manual_review_required",
    "make_engine_warning",
    "make_engine_error",
    "get_public_record_connector_registry",
    "get_enabled_connector_metadata",
    "load_connector_factory",
    "load_connector_instance",
    "load_enabled_connectors",
    "get_connector_import_status",
    "create_public_records_engine",
    "search_public_records",
    "search_public_records_by_address",
    "search_public_records_by_block_lot",
    "search_public_records_by_owner_reference",
    "get_public_records_engine_metadata",
    "get_public_records_engine_health",
    "get_public_records_engine_diagnostics",
    "validate_public_records_engine_governance",
]


# ============================================================
# END OF FILE
# ============================================================