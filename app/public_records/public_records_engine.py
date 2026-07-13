# ============================================================
# AUSSEM1
# PHASE 2.46 PART 1.00
# ENTERPRISE PUBLIC RECORDS ORCHESTRATION ENGINE
# FILE: app/public_records/public_records_engine.py
# PURPOSE:
# Coordinate public-record connector results for New Jersey and
# Morris County property-intelligence workflows.
#
# THIS ENGINE:
# - routes NJ / Morris County requests correctly
# - runs all available public-record connectors safely
# - merges connector outputs
# - deduplicates parcel and address facts
# - preserves source attribution
# - handles unavailable connectors
# - handles partial data
# - scores connector results
# - labels unsupported claims
# - prepares public-record facts for the property profile engine
#
# CORE GOVERNANCE:
# - No fabricated public records.
# - No fabricated parcel facts.
# - No fabricated owner conclusions.
# - No fabricated sale history.
# - No fabricated listing status.
# - No fabricated valuation.
# - Public records can support parcel/tax/deed/GIS/MOD-IV context.
# - Public records cannot prove current active listing status.
# - Public records cannot prove under-contract status.
# - Public records cannot prove current list price.
# - Tax assessment is not market value.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# ENTERPRISE PUBLIC RECORDS ENGINE ACTIVE
# ============================================================


from __future__ import annotations

# ============================================================
# SECTION 01 - STANDARD LIBRARY IMPORTS
# ============================================================

import hashlib
import importlib
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
# SECTION 02 - MODULE METADATA
# ============================================================

PUBLIC_RECORDS_ENGINE_NAME = "Aussem1 Enterprise Public Records Engine"

PUBLIC_RECORDS_ENGINE_VERSION = "0.2.0"

PUBLIC_RECORDS_ENGINE_PHASE = "PHASE 2.46 PART 1.00"

PUBLIC_RECORDS_ENGINE_STATUS = "enterprise_public_records_engine_active"

PUBLIC_RECORDS_RELEASE_CHANNEL = "development"


# ============================================================
# SECTION 03 - GOVERNANCE
# ============================================================

PUBLIC_RECORDS_GOVERNANCE = {
    "fabricated_public_records_allowed": False,
    "fabricated_parcel_facts_allowed": False,
    "fabricated_tax_facts_allowed": False,
    "fabricated_owner_conclusions_allowed": False,
    "fabricated_sale_history_allowed": False,
    "fabricated_listing_status_allowed": False,
    "fabricated_valuation_allowed": False,
    "public_records_can_support_parcel_context": True,
    "public_records_can_support_tax_context": True,
    "public_records_can_support_deed_context": True,
    "public_records_can_support_gis_context": True,
    "public_records_can_support_modiv_context": True,
    "public_records_cannot_prove_current_listing_status": True,
    "public_records_cannot_prove_under_contract_status": True,
    "public_records_cannot_prove_current_listing_price": True,
    "tax_assessment_is_not_market_value": True,
    "source_attribution_required": True,
    "partial_results_allowed": True,
    "unavailable_sources_must_be_labeled": True,
}


SUPPORTED_PUBLIC_RECORD_CLAIMS = [
    "address_identity",
    "parcel_identity",
    "block_lot",
    "tax_assessment_context",
    "property_tax_context",
    "county_clerk_references",
    "deed_references",
    "sale_history_references",
    "owner_references",
    "gis_context",
    "modiv_context",
    "building_facts_when_source_backed",
]


UNSUPPORTED_PUBLIC_RECORD_CLAIMS = [
    "active_listing_status",
    "under_contract_status",
    "pending_status",
    "current_listing_price",
    "current_days_on_market",
    "showing_availability",
    "offer_deadline",
    "broker_confirmation",
    "current_mls_status",
    "market_value_estimate_without_valuation_engine",
]


STANDARD_PUBLIC_RECORD_LIMITATIONS = [
    "Public records may lag current listing, contract, or closing activity.",
    "Tax assessment is not current market value.",
    "GIS context is not a legal boundary survey.",
    "County clerk records may require manual review for document meaning and party interpretation.",
    "Owner references are public-record context and are not a legal title opinion.",
    "Current listing status requires an authorized MLS, RESO, IDX, broker-authorized feed, or listing-provider source.",
    "Valuation requires source-backed property facts, comparable-sales data, valuation logic, and confidence calibration.",
]


# ============================================================
# SECTION 04 - CONNECTOR REGISTRY
# ============================================================

CONNECTOR_SPECS = [
    {
        "connector_key": "nj_morris_tax_board",
        "module_path": "app.public_records.connectors.nj_morris_tax_board_connector",
        "class_candidates": [
            "NJMorrisTaxBoardConnector",
            "MorrisTaxBoardConnector",
            "TaxBoardConnector",
            "PublicRecordConnector",
        ],
        "source_type": "morris_tax_board",
        "authority": "county_tax_board_public_record",
        "jurisdiction": "Morris County, NJ",
        "supports": [
            "parcel_identity",
            "tax_assessment_context",
            "property_tax_context",
            "owner_references",
        ],
    },
    {
        "connector_key": "nj_morris_clerk",
        "module_path": "app.public_records.connectors.nj_morris_clerk_connector",
        "class_candidates": [
            "NJMorrisClerkConnector",
            "MorrisClerkConnector",
            "CountyClerkConnector",
            "PublicRecordConnector",
        ],
        "source_type": "morris_clerk",
        "authority": "county_clerk_public_record",
        "jurisdiction": "Morris County, NJ",
        "supports": [
            "county_clerk_references",
            "deed_references",
            "sale_history_references",
            "mortgage_references",
            "lien_references",
        ],
    },
    {
        "connector_key": "nj_morris_gis",
        "module_path": "app.public_records.connectors.nj_morris_gis_connector",
        "class_candidates": [
            "NJMorrisGISConnector",
            "MorrisGISConnector",
            "GISConnector",
            "PublicRecordConnector",
        ],
        "source_type": "morris_gis",
        "authority": "county_gis_public_record",
        "jurisdiction": "Morris County, NJ",
        "supports": [
            "parcel_identity",
            "gis_context",
            "lot_size_context",
            "location_context",
        ],
    },
    {
        "connector_key": "nj_state_modiv",
        "module_path": "app.public_records.connectors.nj_state_modiv_connector",
        "class_candidates": [
            "NJStateMODIVConnector",
            "NJMODIVConnector",
            "MODIVConnector",
            "PublicRecordConnector",
        ],
        "source_type": "nj_state_modiv",
        "authority": "state_public_record",
        "jurisdiction": "New Jersey",
        "supports": [
            "modiv_context",
            "tax_assessment_context",
            "property_class",
            "building_facts_when_source_backed",
        ],
    },
]


# ============================================================
# SECTION 05 - ENUMERATIONS
# ============================================================

class PublicRecordEngineStatus(StrEnum):
    READY = "ready"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class PublicRecordConnectorStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"
    SKIPPED = "skipped"


class PublicRecordFactStatus(StrEnum):
    SOURCE_BACKED = "source_backed"
    INFERRED = "inferred"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    CONFLICTED = "conflicted"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class PublicRecordQueryMode(StrEnum):
    ADDRESS = "address"
    BLOCK_LOT = "block_lot"
    OWNER_REFERENCE = "owner_reference"
    PARCEL_ID = "parcel_id"
    UNKNOWN = "unknown"


class PublicRecordJurisdiction(StrEnum):
    NJ_MORRIS = "nj_morris"
    NJ_OTHER = "nj_other"
    OUTSIDE_INITIAL_SCOPE = "outside_initial_scope"
    UNKNOWN = "unknown"


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


def normalize_key(value: Any) -> str:
    text = safe_string(value).lower()
    output: list[str] = []

    for character in text:
        if character.isalnum():
            output.append(character)
        elif output and output[-1] != "_":
            output.append("_")

    return "".join(output).strip("_")


def normalize_state(value: Any) -> str | None:
    text = safe_string(value).upper()

    if not text:
        return None

    if text in {"NJ", "NEW JERSEY"}:
        return "NJ"

    return text


def normalize_county(value: Any) -> str | None:
    text = safe_string(value)

    if not text:
        return None

    cleaned = text.replace(" County", "").replace(" county", "").strip()

    return cleaned.title()


def clamp_score(value: Any) -> float:
    try:
        number = float(value)
    except Exception:
        return 0.0

    if not math.isfinite(number):
        return 0.0

    return max(0.0, min(1.0, number))


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


def extract_nested_value(
    payload: Mapping[str, Any],
    paths: Sequence[str],
) -> Any:
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


def to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None

    try:
        return float(str(value).replace("$", "").replace(",", ""))
    except Exception:
        return None


def clean_value(value: Any) -> str | None:
    text = safe_string(value)

    return text or None


# ============================================================
# SECTION 07 - DATA CONTRACTS
# ============================================================

@dataclass
class PublicRecordRequest:
    raw_query: str | None = None
    street_address: str | None = None
    normalized_address: str | None = None
    municipality: str | None = None
    county: str | None = None
    state: str | None = None
    state_code: str | None = None
    postal_code: str | None = None
    block: str | None = None
    lot: str | None = None
    qualifier: str | None = None
    parcel_id: str | None = None
    owner_reference: str | None = None
    query_mode: str = PublicRecordQueryMode.UNKNOWN.value
    include_tax: bool = True
    include_clerk: bool = True
    include_gis: bool = True
    include_modiv: bool = True
    strict_source_mode: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class PublicRecordSourceReference:
    source_name: str
    source_type: str
    connector_key: str | None = None
    source_authority: str = "public_record"
    jurisdiction: str | None = None
    source_url: str | None = None
    record_id: str | None = None
    field_path: str | None = None
    retrieved_at: str = field(default_factory=utc_now)
    confidence: float = 0.0
    raw_payload_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class PublicRecordFact:
    field_name: str
    field_path: str
    value: Any
    status: str
    confidence: float = 0.0
    source_references: list[PublicRecordSourceReference] = field(default_factory=list)
    unavailable_reason: str | None = None
    unsupported_reason: str | None = None
    manual_review_required: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class ConnectorExecutionResult:
    connector_key: str
    connector_name: str
    source_type: str
    status: str
    success: bool
    confidence: float = 0.0
    records: list[dict[str, Any]] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)
    sources: list[PublicRecordSourceReference] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: int = 0
    raw_payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class ConnectorReadiness:
    connector_key: str
    module_path: str
    available: bool
    class_name: str | None = None
    status: str = PublicRecordConnectorStatus.UNAVAILABLE.value
    import_error: str | None = None
    supports: list[str] = field(default_factory=list)
    jurisdiction: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class PublicRecordMergeResult:
    facts: dict[str, Any] = field(default_factory=dict)
    records: list[dict[str, Any]] = field(default_factory=list)
    sources: list[PublicRecordSourceReference] = field(default_factory=list)
    fact_objects: list[PublicRecordFact] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    unavailable_fields: list[dict[str, Any]] = field(default_factory=list)
    unsupported_claims: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    source_coverage_score: float = 0.0
    completeness_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class PublicRecordEngineResult:
    success: bool
    status: str
    request: PublicRecordRequest
    jurisdiction: str
    query_mode: str
    facts: dict[str, Any] = field(default_factory=dict)
    records: list[dict[str, Any]] = field(default_factory=list)
    sources: list[PublicRecordSourceReference] = field(default_factory=list)
    fact_objects: list[PublicRecordFact] = field(default_factory=list)
    connector_results: list[ConnectorExecutionResult] = field(default_factory=list)
    connector_readiness: list[ConnectorReadiness] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    unavailable_fields: list[dict[str, Any]] = field(default_factory=list)
    unsupported_claims: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    source_coverage_score: float = 0.0
    completeness_score: float = 0.0
    limitations: list[str] = field(default_factory=lambda: list(STANDARD_PUBLIC_RECORD_LIMITATIONS))
    governance: dict[str, Any] = field(default_factory=lambda: PUBLIC_RECORDS_GOVERNANCE.copy())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = object_to_dict(asdict(self))

        # PropertyProfileEngine compatibility: keep facts and major sections top-level.
        if isinstance(payload.get("facts"), Mapping):
            for key, value in payload["facts"].items():
                payload.setdefault(key, value)

        return payload


# ============================================================
# SECTION 08 - REQUEST NORMALIZER
# ============================================================

class PublicRecordRequestNormalizer:
    def normalize(
        self,
        request: PublicRecordRequest | Mapping[str, Any] | str,
        **kwargs: Any,
    ) -> PublicRecordRequest:
        if isinstance(request, PublicRecordRequest):
            base = request
        elif isinstance(request, Mapping):
            base = self.from_mapping(request)
        elif isinstance(request, str):
            base = PublicRecordRequest(
                raw_query=request,
                street_address=request,
                normalized_address=request,
            )
        else:
            raise TypeError(
                "request must be PublicRecordRequest, mapping, or raw query string"
            )

        for key, value in kwargs.items():
            if hasattr(base, key) and value not in (None, ""):
                setattr(base, key, value)

        base.state_code = normalize_state(base.state_code or base.state)
        base.state = base.state_code
        base.county = normalize_county(base.county)

        if base.query_mode == PublicRecordQueryMode.UNKNOWN.value:
            base.query_mode = self.detect_query_mode(base)

        return base

    @staticmethod
    def from_mapping(payload: Mapping[str, Any]) -> PublicRecordRequest:
        metadata = dict(payload.get("metadata") or {})

        return PublicRecordRequest(
            raw_query=payload.get("raw_query")
            or payload.get("query")
            or payload.get("address")
            or payload.get("raw_address"),
            street_address=payload.get("street_address")
            or payload.get("address_line_1")
            or payload.get("normalized_street_address"),
            normalized_address=payload.get("normalized_address")
            or payload.get("canonical_address"),
            municipality=payload.get("municipality") or payload.get("city"),
            county=payload.get("county"),
            state=payload.get("state") or payload.get("state_code"),
            state_code=payload.get("state_code") or payload.get("state"),
            postal_code=payload.get("postal_code") or payload.get("zip"),
            block=payload.get("block"),
            lot=payload.get("lot"),
            qualifier=payload.get("qualifier"),
            parcel_id=payload.get("parcel_id") or payload.get("parcel_number"),
            owner_reference=payload.get("owner_reference") or payload.get("owner"),
            query_mode=payload.get("primary_query_mode")
            or payload.get("query_mode")
            or PublicRecordQueryMode.UNKNOWN.value,
            include_tax=bool(payload.get("include_tax", True)),
            include_clerk=bool(payload.get("include_clerk", True)),
            include_gis=bool(payload.get("include_gis", True)),
            include_modiv=bool(payload.get("include_modiv", True)),
            strict_source_mode=bool(payload.get("strict_source_mode", True)),
            metadata=metadata,
        )

    @staticmethod
    def detect_query_mode(request: PublicRecordRequest) -> str:
        if request.block and request.lot:
            return PublicRecordQueryMode.BLOCK_LOT.value

        if request.parcel_id:
            return PublicRecordQueryMode.PARCEL_ID.value

        if request.street_address or request.normalized_address or request.raw_query:
            return PublicRecordQueryMode.ADDRESS.value

        if request.owner_reference:
            return PublicRecordQueryMode.OWNER_REFERENCE.value

        return PublicRecordQueryMode.UNKNOWN.value


# ============================================================
# SECTION 09 - JURISDICTION ROUTER
# ============================================================

class PublicRecordJurisdictionRouter:
    def resolve(self, request: PublicRecordRequest) -> str:
        state = normalize_state(request.state_code or request.state)
        county = normalize_county(request.county)

        if state == "NJ" and county == "Morris":
            return PublicRecordJurisdiction.NJ_MORRIS.value

        if state == "NJ":
            return PublicRecordJurisdiction.NJ_OTHER.value

        if state:
            return PublicRecordJurisdiction.OUTSIDE_INITIAL_SCOPE.value

        return PublicRecordJurisdiction.UNKNOWN.value

    def allowed_connectors(
        self,
        request: PublicRecordRequest,
        jurisdiction: str,
    ) -> list[dict[str, Any]]:
        if jurisdiction == PublicRecordJurisdiction.NJ_MORRIS.value:
            allowed = []

            for spec in CONNECTOR_SPECS:
                if spec["connector_key"] == "nj_morris_tax_board" and request.include_tax:
                    allowed.append(spec)
                elif spec["connector_key"] == "nj_morris_clerk" and request.include_clerk:
                    allowed.append(spec)
                elif spec["connector_key"] == "nj_morris_gis" and request.include_gis:
                    allowed.append(spec)
                elif spec["connector_key"] == "nj_state_modiv" and request.include_modiv:
                    allowed.append(spec)

            return allowed

        if jurisdiction == PublicRecordJurisdiction.NJ_OTHER.value:
            return [
                spec
                for spec in CONNECTOR_SPECS
                if spec["connector_key"] == "nj_state_modiv"
                and request.include_modiv
            ]

        return []


# ============================================================
# SECTION 10 - CONNECTOR LOADER
# ============================================================

class PublicRecordConnectorLoader:
    def load(self, spec: Mapping[str, Any]) -> tuple[Any | None, ConnectorReadiness]:
        module_path = safe_string(spec.get("module_path"))
        connector_key = safe_string(spec.get("connector_key"))

        try:
            module = importlib.import_module(module_path)
        except Exception as exc:
            return None, ConnectorReadiness(
                connector_key=connector_key,
                module_path=module_path,
                available=False,
                status=PublicRecordConnectorStatus.UNAVAILABLE.value,
                import_error=f"{type(exc).__name__}: {exc}",
                supports=list(spec.get("supports") or []),
                jurisdiction=spec.get("jurisdiction"),
            )

        class_name = None
        connector_class = None

        for candidate in spec.get("class_candidates") or []:
            value = getattr(module, candidate, None)

            if value is not None:
                connector_class = value
                class_name = candidate
                break

        if connector_class is None:
            factory = getattr(module, "get_connector", None)

            if callable(factory):
                try:
                    connector = factory()
                    return connector, ConnectorReadiness(
                        connector_key=connector_key,
                        module_path=module_path,
                        available=True,
                        class_name=connector.__class__.__name__,
                        status=PublicRecordConnectorStatus.AVAILABLE.value,
                        supports=list(spec.get("supports") or []),
                        jurisdiction=spec.get("jurisdiction"),
                    )
                except Exception as exc:
                    return None, ConnectorReadiness(
                        connector_key=connector_key,
                        module_path=module_path,
                        available=False,
                        status=PublicRecordConnectorStatus.ERROR.value,
                        import_error=f"{type(exc).__name__}: {exc}",
                        supports=list(spec.get("supports") or []),
                        jurisdiction=spec.get("jurisdiction"),
                    )

            return None, ConnectorReadiness(
                connector_key=connector_key,
                module_path=module_path,
                available=False,
                status=PublicRecordConnectorStatus.UNAVAILABLE.value,
                import_error="No supported connector class or factory was found.",
                supports=list(spec.get("supports") or []),
                jurisdiction=spec.get("jurisdiction"),
            )

        try:
            connector = connector_class()
        except Exception as exc:
            return None, ConnectorReadiness(
                connector_key=connector_key,
                module_path=module_path,
                available=False,
                class_name=class_name,
                status=PublicRecordConnectorStatus.ERROR.value,
                import_error=f"{type(exc).__name__}: {exc}",
                supports=list(spec.get("supports") or []),
                jurisdiction=spec.get("jurisdiction"),
            )

        return connector, ConnectorReadiness(
            connector_key=connector_key,
            module_path=module_path,
            available=True,
            class_name=class_name,
            status=PublicRecordConnectorStatus.AVAILABLE.value,
            supports=list(spec.get("supports") or []),
            jurisdiction=spec.get("jurisdiction"),
        )


# ============================================================
# SECTION 11 - CONNECTOR EXECUTOR
# ============================================================

class PublicRecordConnectorExecutor:
    METHOD_CANDIDATES = [
        "collect",
        "search",
        "lookup",
        "lookup_property",
        "search_public_records",
        "run",
        "execute",
        "fetch",
        "query",
    ]

    def execute(
        self,
        connector: Any,
        spec: Mapping[str, Any],
        request: PublicRecordRequest,
    ) -> ConnectorExecutionResult:
        started = time.perf_counter()
        connector_key = safe_string(spec.get("connector_key"))
        connector_name = connector.__class__.__name__
        source_type = safe_string(spec.get("source_type"))

        for method_name in self.METHOD_CANDIDATES:
            method = getattr(connector, method_name, None)

            if not callable(method):
                continue

            success, result, error = self.invoke_method(method, request)

            if success:
                payload = self.normalize_connector_payload(
                    result,
                    connector_key=connector_key,
                    connector_name=connector_name,
                    source_type=source_type,
                    spec=spec,
                )
                payload.duration_ms = int((time.perf_counter() - started) * 1000)
                return payload

            if error:
                continue

        return ConnectorExecutionResult(
            connector_key=connector_key,
            connector_name=connector_name,
            source_type=source_type,
            status=PublicRecordConnectorStatus.ERROR.value,
            success=False,
            errors=[
                {
                    "code": "connector_method_unavailable",
                    "message": (
                        "Connector is available, but no compatible method could be executed."
                    ),
                }
            ],
            duration_ms=int((time.perf_counter() - started) * 1000),
            metadata={
                "available_methods": [
                    name for name in dir(connector) if not name.startswith("_")
                ],
            },
        )

    @staticmethod
    def invoke_method(
        method: Callable[..., Any],
        request: PublicRecordRequest,
    ) -> tuple[bool, Any, str | None]:
        try:
            signature = inspect.signature(method)
            parameters = signature.parameters
            payload = request.to_dict()

            if "request" in parameters:
                return True, method(request=request), None

            if "payload" in parameters:
                return True, method(payload=payload), None

            if "search_payload" in parameters:
                return True, method(search_payload=payload), None

            if "raw_address" in parameters:
                return True, method(raw_address=request.raw_query or request.street_address or ""), None

            if "address" in parameters:
                return True, method(address=request.raw_query or request.street_address or ""), None

            if "block" in parameters and "lot" in parameters:
                return True, method(
                    block=request.block,
                    lot=request.lot,
                    qualifier=request.qualifier,
                    municipality=request.municipality,
                ), None

            return True, method(payload), None

        except Exception as exc:
            return False, None, f"{type(exc).__name__}: {exc}"

    def normalize_connector_payload(
        self,
        result: Any,
        *,
        connector_key: str,
        connector_name: str,
        source_type: str,
        spec: Mapping[str, Any],
    ) -> ConnectorExecutionResult:
        payload = object_to_dict(result)

        if not isinstance(payload, Mapping):
            payload = {
                "raw_result": payload,
            }

        records = self.extract_records(payload)
        facts = self.extract_facts(payload)
        warnings = list(payload.get("warnings") or [])
        errors = list(payload.get("errors") or [])

        source = PublicRecordSourceReference(
            source_name=connector_name,
            source_type=source_type,
            connector_key=connector_key,
            source_authority=safe_string(spec.get("authority")) or "public_record",
            jurisdiction=spec.get("jurisdiction"),
            confidence=self.score_payload(payload),
            raw_payload_hash=stable_hash(payload),
            metadata={
                "supports": list(spec.get("supports") or []),
                "connector_key": connector_key,
            },
        )

        success = bool(payload.get("success", True)) and not errors
        status_value = (
            PublicRecordConnectorStatus.SUCCESS.value
            if success
            else PublicRecordConnectorStatus.PARTIAL.value
        )

        if not records and not facts and success:
            status_value = PublicRecordConnectorStatus.PARTIAL.value
            warnings.append(
                "Connector executed but did not return source-backed facts."
            )

        return ConnectorExecutionResult(
            connector_key=connector_key,
            connector_name=connector_name,
            source_type=source_type,
            status=status_value,
            success=success,
            confidence=source.confidence,
            records=records,
            facts=facts,
            sources=[source],
            warnings=warnings,
            errors=errors,
            raw_payload=dict(payload),
            metadata={
                "normalized_at": utc_now(),
                "payload_hash": stable_hash(payload),
            },
        )

    @staticmethod
    def extract_records(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
        records = payload.get("records")

        if isinstance(records, list):
            return [
                dict(record)
                for record in records
                if isinstance(record, Mapping)
            ]

        data = payload.get("data")

        if isinstance(data, list):
            return [
                dict(record)
                for record in data
                if isinstance(record, Mapping)
            ]

        if isinstance(data, Mapping):
            return [dict(data)]

        return []

    @staticmethod
    def extract_facts(payload: Mapping[str, Any]) -> dict[str, Any]:
        facts = payload.get("facts")

        if isinstance(facts, Mapping):
            return dict(facts)

        data = payload.get("data")

        if isinstance(data, Mapping):
            return dict(data)

        result = payload.get("result")

        if isinstance(result, Mapping):
            return dict(result)

        return {}

    @staticmethod
    def score_payload(payload: Mapping[str, Any]) -> float:
        if not payload:
            return 0.0

        useful_count = len(
            [
                value
                for value in payload.values()
                if value not in (None, "", [], {})
            ]
        )

        base = min(useful_count / 12, 1.0)

        if payload.get("success") is False:
            base *= 0.50

        if payload.get("errors"):
            base *= 0.60

        if payload.get("sources"):
            base += 0.10

        if payload.get("records") or payload.get("facts") or payload.get("data"):
            base += 0.20

        return round(clamp_score(base), 6)


# ============================================================
# SECTION 12 - FACT EXTRACTOR
# ============================================================

class PublicRecordFactExtractor:
    def extract_sections(
        self,
        request: PublicRecordRequest,
        connector_results: Sequence[ConnectorExecutionResult],
    ) -> dict[str, Any]:
        payloads = [
            result.to_dict()
            for result in connector_results
        ]

        combined = {
            "request": request.to_dict(),
            "connector_results": payloads,
            "facts": {},
            "records": [],
        }

        for result in connector_results:
            combined["records"].extend(result.records)

            for key, value in result.facts.items():
                combined["facts"].setdefault(key, value)

            for record in result.records:
                for key, value in record.items():
                    combined["facts"].setdefault(key, value)

        flattened = flatten_mapping(combined)

        return {
            "address_identity": self.extract_address_identity(request, flattened),
            "parcel_identity": self.extract_parcel_identity(request, flattened),
            "tax_assessment_context": self.extract_tax_assessment(flattened),
            "property_tax_context": self.extract_property_tax(flattened),
            "county_clerk_references": self.extract_clerk_references(connector_results),
            "sale_history_references": self.extract_sale_history(connector_results, flattened),
            "owner_references": self.extract_owner_references(flattened),
            "gis_context": self.extract_gis_context(flattened),
            "modiv_context": self.extract_modiv_context(flattened),
            "building_facts": self.extract_building_facts(flattened),
        }

    def extract_address_identity(
        self,
        request: PublicRecordRequest,
        flattened: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "raw_query": request.raw_query,
            "street_address": request.street_address,
            "normalized_address": request.normalized_address,
            "municipality": request.municipality,
            "county": request.county,
            "state_code": request.state_code,
            "postal_code": request.postal_code,
            "source_status": PublicRecordFactStatus.INFERRED.value,
            "confidence": 0.50,
        }

    def extract_parcel_identity(
        self,
        request: PublicRecordRequest,
        flattened: Mapping[str, Any],
    ) -> dict[str, Any]:
        parcel_id = self.first_value(
            flattened,
            [
                "facts.parcel_id",
                "facts.parcel_number",
                "records.parcel_id",
                "records.parcel_number",
                "parcel.parcel_id",
                "parcel.parcel_number",
                "gis.parcel_id",
                "modiv.parcel_id",
            ],
        )

        block = (
            request.block
            or self.first_value(
                flattened,
                [
                    "facts.block",
                    "records.block",
                    "parcel.block",
                    "tax.block",
                    "assessment.block",
                    "modiv.block",
                ],
            )
        )

        lot = (
            request.lot
            or self.first_value(
                flattened,
                [
                    "facts.lot",
                    "records.lot",
                    "parcel.lot",
                    "tax.lot",
                    "assessment.lot",
                    "modiv.lot",
                ],
            )
        )

        qualifier = (
            request.qualifier
            or self.first_value(
                flattened,
                [
                    "facts.qualifier",
                    "records.qualifier",
                    "parcel.qualifier",
                    "tax.qualifier",
                    "assessment.qualifier",
                ],
            )
        )

        has_data = any(
            value not in (None, "")
            for value in [
                parcel_id,
                block,
                lot,
                request.municipality,
                request.county,
                request.state_code,
            ]
        )

        return {
            "parcel_id": clean_value(parcel_id),
            "block": clean_value(block),
            "lot": clean_value(lot),
            "qualifier": clean_value(qualifier),
            "municipality": clean_value(
                self.first_value(
                    flattened,
                    [
                        "facts.municipality",
                        "records.municipality",
                        "parcel.municipality",
                        "tax.municipality",
                    ],
                )
                or request.municipality
            ),
            "county": clean_value(
                self.first_value(
                    flattened,
                    [
                        "facts.county",
                        "records.county",
                        "parcel.county",
                    ],
                )
                or request.county
            ),
            "state_code": clean_value(
                self.first_value(
                    flattened,
                    [
                        "facts.state_code",
                        "records.state_code",
                        "parcel.state_code",
                        "facts.state",
                    ],
                )
                or request.state_code
            ),
            "property_class": clean_value(
                self.first_value(
                    flattened,
                    [
                        "facts.property_class",
                        "records.property_class",
                        "assessment.property_class",
                        "modiv.property_class",
                    ],
                )
            ),
            "source_status": (
                PublicRecordFactStatus.SOURCE_BACKED.value
                if has_data
                else PublicRecordFactStatus.UNAVAILABLE.value
            ),
            "confidence": 0.70 if has_data else 0.0,
        }

    def extract_tax_assessment(
        self,
        flattened: Mapping[str, Any],
    ) -> dict[str, Any]:
        total = to_float(
            self.first_value(
                flattened,
                [
                    "facts.total_assessment",
                    "records.total_assessment",
                    "assessment.total_assessment",
                    "tax.total_assessment",
                    "facts.assessed_value",
                    "records.assessed_value",
                ],
            )
        )
        land = to_float(
            self.first_value(
                flattened,
                [
                    "facts.land_assessment",
                    "records.land_assessment",
                    "assessment.land_assessment",
                    "tax.land_assessment",
                    "facts.land_value",
                ],
            )
        )
        improvement = to_float(
            self.first_value(
                flattened,
                [
                    "facts.improvement_assessment",
                    "records.improvement_assessment",
                    "assessment.improvement_assessment",
                    "tax.improvement_assessment",
                    "facts.improvement_value",
                ],
            )
        )
        tax_year = clean_value(
            self.first_value(
                flattened,
                [
                    "facts.tax_year",
                    "records.tax_year",
                    "assessment.tax_year",
                    "tax.tax_year",
                ],
            )
        )
        property_class = clean_value(
            self.first_value(
                flattened,
                [
                    "facts.property_class",
                    "records.property_class",
                    "assessment.property_class",
                    "modiv.property_class",
                ],
            )
        )

        has_data = any(
            value is not None
            for value in [
                total,
                land,
                improvement,
                tax_year,
                property_class,
            ]
        )

        return {
            "tax_year": tax_year,
            "land_assessment": land,
            "improvement_assessment": improvement,
            "total_assessment": total,
            "property_class": property_class,
            "assessment_source_note": (
                "Tax assessment is public-record context and is not current market value."
            ),
            "source_status": (
                PublicRecordFactStatus.SOURCE_BACKED.value
                if has_data
                else PublicRecordFactStatus.UNAVAILABLE.value
            ),
            "confidence": 0.72 if has_data else 0.0,
        }

    def extract_property_tax(
        self,
        flattened: Mapping[str, Any],
    ) -> dict[str, Any]:
        tax_amount = to_float(
            self.first_value(
                flattened,
                [
                    "facts.tax_amount",
                    "records.tax_amount",
                    "property_tax.tax_amount",
                    "tax.tax_amount",
                    "tax.annual_tax",
                    "facts.annual_tax",
                ],
            )
        )
        tax_rate = to_float(
            self.first_value(
                flattened,
                [
                    "facts.tax_rate",
                    "records.tax_rate",
                    "property_tax.tax_rate",
                    "tax.tax_rate",
                ],
            )
        )
        tax_year = clean_value(
            self.first_value(
                flattened,
                [
                    "facts.tax_year",
                    "records.tax_year",
                    "property_tax.tax_year",
                    "tax.tax_year",
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

        return {
            "tax_year": tax_year,
            "tax_amount": tax_amount,
            "tax_rate": tax_rate,
            "estimated_annual_tax": tax_amount,
            "source_status": (
                PublicRecordFactStatus.SOURCE_BACKED.value
                if has_data
                else PublicRecordFactStatus.UNAVAILABLE.value
            ),
            "confidence": 0.66 if has_data else 0.0,
        }

    def extract_clerk_references(
        self,
        connector_results: Sequence[ConnectorExecutionResult],
    ) -> list[dict[str, Any]]:
        references: list[dict[str, Any]] = []

        for result in connector_results:
            if result.source_type != "morris_clerk":
                continue

            for record in result.records:
                references.append(
                    {
                        "document_type": clean_value(
                            record.get("document_type")
                            or record.get("type")
                        ),
                        "document_number": clean_value(
                            record.get("document_number")
                            or record.get("instrument_number")
                            or record.get("id")
                        ),
                        "book": clean_value(record.get("book")),
                        "page": clean_value(record.get("page")),
                        "recorded_date": clean_value(
                            record.get("recorded_date")
                            or record.get("date")
                        ),
                        "party_one": clean_value(
                            record.get("party_one")
                            or record.get("grantor")
                            or record.get("buyer")
                        ),
                        "party_two": clean_value(
                            record.get("party_two")
                            or record.get("grantee")
                            or record.get("seller")
                        ),
                        "source_status": PublicRecordFactStatus.SOURCE_BACKED.value,
                        "confidence": result.confidence,
                        "metadata": {
                            "connector_key": result.connector_key,
                        },
                    }
                )

        return references

    def extract_sale_history(
        self,
        connector_results: Sequence[ConnectorExecutionResult],
        flattened: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        sale_records: list[dict[str, Any]] = []

        for result in connector_results:
            for record in result.records:
                sale_date = record.get("sale_date") or record.get("last_sale_date")
                sale_price = record.get("sale_price") or record.get("last_sale_price")

                if sale_date or sale_price:
                    sale_records.append(
                        {
                            "sale_date": clean_value(sale_date),
                            "sale_price": to_float(sale_price),
                            "deed_book": clean_value(record.get("deed_book") or record.get("book")),
                            "deed_page": clean_value(record.get("deed_page") or record.get("page")),
                            "document_number": clean_value(
                                record.get("document_number")
                                or record.get("instrument_number")
                                or record.get("id")
                            ),
                            "buyer_reference": clean_value(record.get("buyer")),
                            "seller_reference": clean_value(record.get("seller")),
                            "source_status": PublicRecordFactStatus.SOURCE_BACKED.value,
                            "confidence": result.confidence,
                            "metadata": {
                                "connector_key": result.connector_key,
                            },
                        }
                    )

        if not sale_records:
            sale_date = clean_value(
                self.first_value(
                    flattened,
                    [
                        "facts.sale_date",
                        "facts.last_sale_date",
                        "records.sale_date",
                        "records.last_sale_date",
                    ],
                )
            )
            sale_price = to_float(
                self.first_value(
                    flattened,
                    [
                        "facts.sale_price",
                        "facts.last_sale_price",
                        "records.sale_price",
                        "records.last_sale_price",
                    ],
                )
            )

            if sale_date or sale_price:
                sale_records.append(
                    {
                        "sale_date": sale_date,
                        "sale_price": sale_price,
                        "source_status": PublicRecordFactStatus.SOURCE_BACKED.value,
                        "confidence": 0.55,
                    }
                )

        return sale_records

    def extract_owner_references(
        self,
        flattened: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        owner_name = clean_value(
            self.first_value(
                flattened,
                [
                    "facts.owner_name",
                    "facts.owner",
                    "records.owner_name",
                    "records.owner",
                    "tax.owner",
                    "assessment.owner",
                ],
            )
        )
        mailing_address = clean_value(
            self.first_value(
                flattened,
                [
                    "facts.mailing_address",
                    "facts.owner_mailing_address",
                    "records.mailing_address",
                    "tax.mailing_address",
                ],
            )
        )

        if not owner_name and not mailing_address:
            return []

        return [
            {
                "owner_name": owner_name,
                "mailing_address": mailing_address,
                "owner_source_note": (
                    "Owner reference is public-record context and may require manual review."
                ),
                "source_status": PublicRecordFactStatus.SOURCE_BACKED.value,
                "confidence": 0.62,
            }
        ]

    def extract_gis_context(
        self,
        flattened: Mapping[str, Any],
    ) -> dict[str, Any]:
        latitude = to_float(
            self.first_value(
                flattened,
                [
                    "facts.latitude",
                    "facts.lat",
                    "records.latitude",
                    "records.lat",
                    "gis.latitude",
                    "gis.lat",
                ],
            )
        )
        longitude = to_float(
            self.first_value(
                flattened,
                [
                    "facts.longitude",
                    "facts.lng",
                    "facts.lon",
                    "records.longitude",
                    "records.lng",
                    "records.lon",
                    "gis.longitude",
                    "gis.lng",
                ],
            )
        )
        lot_size_acres = to_float(
            self.first_value(
                flattened,
                [
                    "facts.lot_size_acres",
                    "records.lot_size_acres",
                    "gis.lot_size_acres",
                    "parcel.lot_size_acres",
                ],
            )
        )
        lot_size_square_feet = to_float(
            self.first_value(
                flattened,
                [
                    "facts.lot_size_square_feet",
                    "facts.lot_sqft",
                    "records.lot_size_square_feet",
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

        return {
            "gis_parcel_id": clean_value(
                self.first_value(
                    flattened,
                    [
                        "facts.gis_parcel_id",
                        "records.gis_parcel_id",
                        "gis.parcel_id",
                    ],
                )
            ),
            "latitude": latitude,
            "longitude": longitude,
            "lot_size_acres": lot_size_acres,
            "lot_size_square_feet": lot_size_square_feet,
            "geometry_reference": clean_value(
                self.first_value(
                    flattened,
                    [
                        "facts.geometry_reference",
                        "records.geometry_reference",
                        "gis.geometry_reference",
                        "geometry.id",
                    ],
                )
            ),
            "map_reference": clean_value(
                self.first_value(
                    flattened,
                    [
                        "facts.map_reference",
                        "records.map_reference",
                        "gis.map_reference",
                    ],
                )
            ),
            "gis_source_note": "GIS context is not a legal boundary survey.",
            "source_status": (
                PublicRecordFactStatus.SOURCE_BACKED.value
                if has_data
                else PublicRecordFactStatus.UNAVAILABLE.value
            ),
            "confidence": 0.62 if has_data else 0.0,
        }

    def extract_modiv_context(
        self,
        flattened: Mapping[str, Any],
    ) -> dict[str, Any]:
        property_class = clean_value(
            self.first_value(
                flattened,
                [
                    "facts.modiv_property_class",
                    "facts.property_class",
                    "records.property_class",
                    "modiv.property_class",
                ],
            )
        )
        year_built = clean_value(
            self.first_value(
                flattened,
                [
                    "facts.year_built",
                    "records.year_built",
                    "modiv.year_built",
                    "building.year_built",
                ],
            )
        )
        building_square_feet = to_float(
            self.first_value(
                flattened,
                [
                    "facts.building_square_feet",
                    "records.building_square_feet",
                    "modiv.building_square_feet",
                    "building.sqft",
                ],
            )
        )

        has_data = any(
            value not in (None, "")
            for value in [
                property_class,
                year_built,
                building_square_feet,
            ]
        )

        return {
            "modiv_property_class": property_class,
            "building_description": clean_value(
                self.first_value(
                    flattened,
                    [
                        "facts.building_description",
                        "records.building_description",
                        "modiv.building_description",
                    ],
                )
            ),
            "year_built": year_built,
            "building_square_feet": building_square_feet,
            "land_description": clean_value(
                self.first_value(
                    flattened,
                    [
                        "facts.land_description",
                        "records.land_description",
                        "modiv.land_description",
                    ],
                )
            ),
            "source_status": (
                PublicRecordFactStatus.SOURCE_BACKED.value
                if has_data
                else PublicRecordFactStatus.UNAVAILABLE.value
            ),
            "confidence": 0.60 if has_data else 0.0,
        }

    def extract_building_facts(
        self,
        flattened: Mapping[str, Any],
    ) -> dict[str, Any]:
        year_built = clean_value(
            self.first_value(
                flattened,
                [
                    "facts.year_built",
                    "records.year_built",
                    "building.year_built",
                    "modiv.year_built",
                ],
            )
        )
        building_square_feet = to_float(
            self.first_value(
                flattened,
                [
                    "facts.building_square_feet",
                    "facts.living_area",
                    "records.building_square_feet",
                    "building.sqft",
                    "building.area",
                    "modiv.building_square_feet",
                ],
            )
        )
        lot_size_acres = to_float(
            self.first_value(
                flattened,
                [
                    "facts.lot_size_acres",
                    "records.lot_size_acres",
                    "gis.lot_size_acres",
                    "parcel.lot_size_acres",
                ],
            )
        )
        property_type = clean_value(
            self.first_value(
                flattened,
                [
                    "facts.property_type",
                    "records.property_type",
                    "building.property_type",
                    "modiv.property_class",
                    "facts.property_class",
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

        return {
            "year_built": year_built,
            "bedrooms": to_float(
                self.first_value(
                    flattened,
                    [
                        "facts.bedrooms",
                        "records.bedrooms",
                        "building.bedrooms",
                    ],
                )
            ),
            "bathrooms": to_float(
                self.first_value(
                    flattened,
                    [
                        "facts.bathrooms",
                        "records.bathrooms",
                        "building.bathrooms",
                    ],
                )
            ),
            "building_square_feet": building_square_feet,
            "lot_size_acres": lot_size_acres,
            "property_type": property_type,
            "source_status": (
                PublicRecordFactStatus.SOURCE_BACKED.value
                if has_data
                else PublicRecordFactStatus.UNAVAILABLE.value
            ),
            "confidence": 0.58 if has_data else 0.0,
        }

    @staticmethod
    def first_value(
        payload: Mapping[str, Any],
        keys: Sequence[str],
    ) -> Any:
        for key in keys:
            if key in payload and payload[key] not in (None, "", [], {}):
                return payload[key]

        return None


# ============================================================
# SECTION 13 - MERGER
# ============================================================

class PublicRecordMerger:
    def merge(
        self,
        request: PublicRecordRequest,
        connector_results: Sequence[ConnectorExecutionResult],
    ) -> PublicRecordMergeResult:
        extractor = PublicRecordFactExtractor()
        facts = extractor.extract_sections(request, connector_results)
        records = self.deduplicate_records(
            [
                record
                for result in connector_results
                for record in result.records
            ]
        )
        sources = self.deduplicate_sources(
            [
                source
                for result in connector_results
                for source in result.sources
            ]
        )
        fact_objects = self.build_fact_objects(facts, sources)
        conflicts = self.detect_conflicts(facts)
        unavailable_fields = self.build_unavailable_fields(facts)
        unsupported_claims = self.build_unsupported_claims()
        source_coverage = self.score_source_coverage(fact_objects)
        completeness = self.score_completeness(fact_objects)
        confidence = self.score_overall(
            source_coverage=source_coverage,
            completeness=completeness,
            conflicts=conflicts,
            connector_results=connector_results,
        )

        return PublicRecordMergeResult(
            facts=facts,
            records=records,
            sources=sources,
            fact_objects=fact_objects,
            conflicts=conflicts,
            unavailable_fields=unavailable_fields,
            unsupported_claims=unsupported_claims,
            confidence=confidence,
            source_coverage_score=source_coverage,
            completeness_score=completeness,
            metadata={
                "merged_at": utc_now(),
                "connector_count": len(connector_results),
                "successful_connector_count": len(
                    [result for result in connector_results if result.success]
                ),
            },
        )

    @staticmethod
    def deduplicate_records(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        output: list[dict[str, Any]] = []

        for record in records:
            key = stable_hash(record)

            if key in seen:
                continue

            seen.add(key)
            output.append(dict(record))

        return output

    @staticmethod
    def deduplicate_sources(
        sources: Sequence[PublicRecordSourceReference],
    ) -> list[PublicRecordSourceReference]:
        seen: set[str] = set()
        output: list[PublicRecordSourceReference] = []

        for source in sources:
            key = stable_hash(source.to_dict())

            if key in seen:
                continue

            seen.add(key)
            output.append(source)

        return output

    def build_fact_objects(
        self,
        facts: Mapping[str, Any],
        sources: Sequence[PublicRecordSourceReference],
    ) -> list[PublicRecordFact]:
        fact_objects: list[PublicRecordFact] = []

        for section_name, section_payload in facts.items():
            if isinstance(section_payload, Mapping):
                for field_name, value in section_payload.items():
                    if field_name in {"source_status", "confidence", "sources", "metadata"}:
                        continue

                    status_value = safe_string(
                        section_payload.get("source_status")
                        or (
                            PublicRecordFactStatus.SOURCE_BACKED.value
                            if value not in (None, "", [], {})
                            else PublicRecordFactStatus.UNAVAILABLE.value
                        )
                    )
                    confidence = clamp_score(section_payload.get("confidence") or 0.0)

                    fact_objects.append(
                        PublicRecordFact(
                            field_name=field_name,
                            field_path=f"{section_name}.{field_name}",
                            value=value,
                            status=status_value,
                            confidence=confidence,
                            source_references=list(sources) if value not in (None, "", [], {}) else [],
                            unavailable_reason=(
                                None
                                if value not in (None, "", [], {})
                                else f"{section_name}.{field_name} was unavailable from current public-record sources."
                            ),
                        )
                    )
            elif isinstance(section_payload, list):
                fact_objects.append(
                    PublicRecordFact(
                        field_name=section_name,
                        field_path=section_name,
                        value=section_payload,
                        status=(
                            PublicRecordFactStatus.SOURCE_BACKED.value
                            if section_payload
                            else PublicRecordFactStatus.UNAVAILABLE.value
                        ),
                        confidence=0.60 if section_payload else 0.0,
                        source_references=list(sources) if section_payload else [],
                    )
                )

        return fact_objects

    @staticmethod
    def detect_conflicts(facts: Mapping[str, Any]) -> list[dict[str, Any]]:
        conflicts: list[dict[str, Any]] = []

        parcel = facts.get("parcel_identity") or {}
        address = facts.get("address_identity") or {}

        if isinstance(parcel, Mapping) and isinstance(address, Mapping):
            for field_name in ["municipality", "county", "state_code"]:
                left = parcel.get(field_name)
                right = address.get(field_name)

                if left not in (None, "") and right not in (None, ""):
                    if normalize_key(left) != normalize_key(right):
                        conflicts.append(
                            {
                                "field_path": f"parcel_identity.{field_name}",
                                "severity": ManualReviewSeverity.WARNING.value,
                                "values": [left, right],
                                "message": (
                                    f"Parcel {field_name} conflicts with address identity."
                                ),
                            }
                        )

        return conflicts

    @staticmethod
    def build_unavailable_fields(
        facts: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        unavailable: list[dict[str, Any]] = []

        for section_name, section_payload in facts.items():
            if isinstance(section_payload, Mapping):
                for field_name, value in section_payload.items():
                    if field_name in {"source_status", "confidence", "sources", "metadata"}:
                        continue

                    if value in (None, "", [], {}):
                        unavailable.append(
                            {
                                "field_name": field_name,
                                "field_path": f"{section_name}.{field_name}",
                                "reason": (
                                    f"{section_name}.{field_name} is unavailable from current public-record sources."
                                ),
                                "required_source": PublicRecordMerger.required_source_for_field(
                                    f"{section_name}.{field_name}"
                                ),
                                "can_public_records_support": True,
                                "manual_review_required": False,
                            }
                        )

        return unavailable

    @staticmethod
    def build_unsupported_claims() -> list[dict[str, Any]]:
        return [
            {
                "claim": claim,
                "status": PublicRecordFactStatus.UNSUPPORTED.value,
                "reason": (
                    "This claim cannot be proven by public records alone."
                    if "market_value" not in claim
                    else "This claim requires valuation engine and comparable-sales inputs."
                ),
                "required_source": (
                    "valuation_engine_and_comparable_sales"
                    if "market_value" in claim
                    else "authorized_listing_feed"
                ),
            }
            for claim in UNSUPPORTED_PUBLIC_RECORD_CLAIMS
        ]

    @staticmethod
    def required_source_for_field(field_path: str) -> str:
        key = normalize_key(field_path)

        if "tax" in key or "assessment" in key:
            return "county_tax_board_public_records"

        if "clerk" in key or "sale_history" in key or "deed" in key:
            return "county_clerk_public_records"

        if "gis" in key:
            return "county_gis_public_records"

        if "modiv" in key:
            return "nj_state_modiv_public_records"

        if "parcel" in key:
            return "tax_board_or_gis_public_records"

        return "public_records_or_manual_review"

    @staticmethod
    def score_source_coverage(facts: Sequence[PublicRecordFact]) -> float:
        if not facts:
            return 0.0

        source_backed = [
            fact
            for fact in facts
            if fact.status == PublicRecordFactStatus.SOURCE_BACKED.value
            and fact.value not in (None, "", [], {})
        ]

        return round(clamp_score(len(source_backed) / len(facts)), 6)

    @staticmethod
    def score_completeness(facts: Sequence[PublicRecordFact]) -> float:
        if not facts:
            return 0.0

        present = [
            fact
            for fact in facts
            if fact.value not in (None, "", [], {})
        ]

        return round(clamp_score(len(present) / len(facts)), 6)

    @staticmethod
    def score_overall(
        *,
        source_coverage: float,
        completeness: float,
        conflicts: Sequence[Mapping[str, Any]],
        connector_results: Sequence[ConnectorExecutionResult],
    ) -> float:
        connector_score = 0.0

        if connector_results:
            connector_score = sum(
                result.confidence for result in connector_results
            ) / len(connector_results)

        conflict_penalty = min(len(conflicts) * 0.10, 0.40)

        score = (
            source_coverage * 0.35
            + completeness * 0.35
            + connector_score * 0.30
            - conflict_penalty
        )

        return round(clamp_score(score), 6)


# ============================================================
# SECTION 14 - ENTERPRISE PUBLIC RECORDS ENGINE
# ============================================================

class PublicRecordsEngine:
    def __init__(
        self,
        *,
        normalizer: PublicRecordRequestNormalizer | None = None,
        jurisdiction_router: PublicRecordJurisdictionRouter | None = None,
        connector_loader: PublicRecordConnectorLoader | None = None,
        connector_executor: PublicRecordConnectorExecutor | None = None,
        merger: PublicRecordMerger | None = None,
    ) -> None:
        self.normalizer = normalizer or PublicRecordRequestNormalizer()
        self.jurisdiction_router = jurisdiction_router or PublicRecordJurisdictionRouter()
        self.connector_loader = connector_loader or PublicRecordConnectorLoader()
        self.connector_executor = connector_executor or PublicRecordConnectorExecutor()
        self.merger = merger or PublicRecordMerger()

    def collect(
        self,
        request: PublicRecordRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        normalized_request = self.normalizer.normalize(
            request or kwargs,
            **kwargs,
        )
        jurisdiction = self.jurisdiction_router.resolve(normalized_request)
        connector_specs = self.jurisdiction_router.allowed_connectors(
            normalized_request,
            jurisdiction,
        )

        connector_results: list[ConnectorExecutionResult] = []
        connector_readiness: list[ConnectorReadiness] = []
        warnings: list[str] = []
        errors: list[dict[str, Any]] = []

        if not connector_specs:
            warnings.append(
                "No connector targets were available for this jurisdiction or query."
            )

        for spec in connector_specs:
            connector, readiness = self.connector_loader.load(spec)
            connector_readiness.append(readiness)

            if connector is None:
                warnings.append(
                    f"Connector unavailable: {readiness.connector_key}"
                )
                continue

            try:
                result = self.connector_executor.execute(
                    connector,
                    spec,
                    normalized_request,
                )
                connector_results.append(result)

                warnings.extend(result.warnings)
                errors.extend(result.errors)
            except Exception as exc:
                errors.append(
                    {
                        "code": "connector_execution_error",
                        "connector_key": spec.get("connector_key"),
                        "message": f"{type(exc).__name__}: {exc}",
                        "traceback": traceback.format_exc(),
                    }
                )

        merge_result = self.merger.merge(
            normalized_request,
            connector_results,
        )

        if errors and merge_result.facts:
            status_value = PublicRecordEngineStatus.PARTIAL.value
        elif errors and not merge_result.facts:
            status_value = PublicRecordEngineStatus.ERROR.value
        elif merge_result.confidence > 0:
            status_value = PublicRecordEngineStatus.READY.value
        else:
            status_value = PublicRecordEngineStatus.PARTIAL.value

        success = status_value in {
            PublicRecordEngineStatus.READY.value,
            PublicRecordEngineStatus.PARTIAL.value,
        }

        result = PublicRecordEngineResult(
            success=success,
            status=status_value,
            request=normalized_request,
            jurisdiction=jurisdiction,
            query_mode=normalized_request.query_mode,
            facts=merge_result.facts,
            records=merge_result.records,
            sources=merge_result.sources,
            fact_objects=merge_result.fact_objects,
            connector_results=connector_results,
            connector_readiness=connector_readiness,
            conflicts=merge_result.conflicts,
            unavailable_fields=merge_result.unavailable_fields,
            unsupported_claims=merge_result.unsupported_claims,
            warnings=list(dict.fromkeys([warning for warning in warnings if warning])),
            errors=errors,
            confidence=merge_result.confidence,
            source_coverage_score=merge_result.source_coverage_score,
            completeness_score=merge_result.completeness_score,
            metadata={
                "engine": PUBLIC_RECORDS_ENGINE_NAME,
                "version": PUBLIC_RECORDS_ENGINE_VERSION,
                "phase": PUBLIC_RECORDS_ENGINE_PHASE,
                "generated_at": utc_now(),
                "connector_target_count": len(connector_specs),
                "connector_success_count": len(
                    [item for item in connector_results if item.success]
                ),
                "result_hash": stable_hash(merge_result.to_dict()),
            },
        )

        return result.to_dict()

    def search_public_records(
        self,
        request: PublicRecordRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def build_profile(
        self,
        request: PublicRecordRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def build_public_record_profile(
        self,
        request: PublicRecordRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def lookup_property(
        self,
        request: PublicRecordRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def run(
        self,
        request: PublicRecordRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def execute(
        self,
        request: PublicRecordRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)


# Backward-compatible aliases.
PublicRecordEngine = PublicRecordsEngine
PublicRecordsOrchestrator = PublicRecordsEngine
PublicRecordOrchestrator = PublicRecordsEngine


# ============================================================
# SECTION 15 - CONVENIENCE API
# ============================================================

_default_public_records_engine = PublicRecordsEngine()


def collect_public_records(
    request: PublicRecordRequest | Mapping[str, Any] | str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return _default_public_records_engine.collect(request, **kwargs)


def search_public_records(
    request: PublicRecordRequest | Mapping[str, Any] | str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return _default_public_records_engine.search_public_records(
        request,
        **kwargs,
    )


def build_public_record_profile(
    request: PublicRecordRequest | Mapping[str, Any] | str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return _default_public_records_engine.build_public_record_profile(
        request,
        **kwargs,
    )


def lookup_public_property(
    request: PublicRecordRequest | Mapping[str, Any] | str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return _default_public_records_engine.lookup_property(request, **kwargs)


# ============================================================
# SECTION 16 - HEALTH / READINESS / DIAGNOSTICS
# ============================================================

def validate_public_records_governance() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    false_keys = [
        "fabricated_public_records_allowed",
        "fabricated_parcel_facts_allowed",
        "fabricated_tax_facts_allowed",
        "fabricated_owner_conclusions_allowed",
        "fabricated_sale_history_allowed",
        "fabricated_listing_status_allowed",
        "fabricated_valuation_allowed",
    ]

    for key in false_keys:
        if PUBLIC_RECORDS_GOVERNANCE.get(key):
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
        "public_records_can_support_deed_context",
        "public_records_can_support_gis_context",
        "public_records_can_support_modiv_context",
        "public_records_cannot_prove_current_listing_status",
        "public_records_cannot_prove_under_contract_status",
        "public_records_cannot_prove_current_listing_price",
        "tax_assessment_is_not_market_value",
        "source_attribution_required",
        "partial_results_allowed",
        "unavailable_sources_must_be_labeled",
    ]

    for key in true_keys:
        if not PUBLIC_RECORDS_GOVERNANCE.get(key):
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


def get_public_records_engine_metadata() -> dict[str, Any]:
    return {
        "name": PUBLIC_RECORDS_ENGINE_NAME,
        "version": PUBLIC_RECORDS_ENGINE_VERSION,
        "phase": PUBLIC_RECORDS_ENGINE_PHASE,
        "status": PUBLIC_RECORDS_ENGINE_STATUS,
        "release_channel": PUBLIC_RECORDS_RELEASE_CHANNEL,
        "generated_at": utc_now(),
    }


def get_public_records_connector_readiness() -> list[dict[str, Any]]:
    loader = PublicRecordConnectorLoader()
    readiness: list[dict[str, Any]] = []

    for spec in CONNECTOR_SPECS:
        connector, result = loader.load(spec)
        readiness.append(result.to_dict())

    return readiness


def get_public_records_engine_health() -> dict[str, Any]:
    governance = validate_public_records_governance()
    readiness = get_public_records_connector_readiness()

    return {
        "name": PUBLIC_RECORDS_ENGINE_NAME,
        "version": PUBLIC_RECORDS_ENGINE_VERSION,
        "phase": PUBLIC_RECORDS_ENGINE_PHASE,
        "status": PUBLIC_RECORDS_ENGINE_STATUS,
        "governance_valid": governance["valid"],
        "governance_issue_count": governance["issue_count"],
        "connector_count": len(readiness),
        "available_connector_count": len(
            [item for item in readiness if item.get("available")]
        ),
        "connectors": readiness,
        "fabricated_public_records_allowed": False,
        "fabricated_listing_status_allowed": False,
        "fabricated_valuation_allowed": False,
        "generated_at": utc_now(),
    }


def get_public_records_engine_readiness() -> dict[str, Any]:
    health = get_public_records_engine_health()

    required = {
        "governance_valid": health["governance_valid"],
        "engine_importable": True,
    }

    optional = {
        "one_or_more_connectors_available": health["available_connector_count"] > 0,
        "morris_tax_board_available": any(
            item.get("connector_key") == "nj_morris_tax_board"
            and item.get("available")
            for item in health["connectors"]
        ),
        "morris_clerk_available": any(
            item.get("connector_key") == "nj_morris_clerk"
            and item.get("available")
            for item in health["connectors"]
        ),
        "morris_gis_available": any(
            item.get("connector_key") == "nj_morris_gis"
            and item.get("available")
            for item in health["connectors"]
        ),
        "nj_modiv_available": any(
            item.get("connector_key") == "nj_state_modiv"
            and item.get("available")
            for item in health["connectors"]
        ),
    }

    return {
        "ready": all(required.values()),
        "required": required,
        "optional": optional,
        "missing_required": [
            key for key, value in required.items() if not value
        ],
        "missing_optional": [
            key for key, value in optional.items() if not value
        ],
        "next_files": [
            "app/public_records/connectors/nj_morris_tax_board_connector.py",
            "app/public_records/connectors/nj_morris_gis_connector.py",
            "app/property_intelligence/valuation_engine.py",
            "app/static/js/dashboard.js",
        ],
        "generated_at": utc_now(),
    }


def get_public_records_engine_diagnostics() -> dict[str, Any]:
    return {
        "metadata": get_public_records_engine_metadata(),
        "health": get_public_records_engine_health(),
        "readiness": get_public_records_engine_readiness(),
        "governance": PUBLIC_RECORDS_GOVERNANCE.copy(),
        "governance_validation": validate_public_records_governance(),
        "connector_specs": CONNECTOR_SPECS,
        "supported_public_record_claims": SUPPORTED_PUBLIC_RECORD_CLAIMS,
        "unsupported_public_record_claims": UNSUPPORTED_PUBLIC_RECORD_CLAIMS,
        "standard_limitations": STANDARD_PUBLIC_RECORD_LIMITATIONS,
        "exports": __all__,
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 17 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "PUBLIC_RECORDS_ENGINE_NAME",
    "PUBLIC_RECORDS_ENGINE_VERSION",
    "PUBLIC_RECORDS_ENGINE_PHASE",
    "PUBLIC_RECORDS_ENGINE_STATUS",
    "PUBLIC_RECORDS_RELEASE_CHANNEL",
    "PUBLIC_RECORDS_GOVERNANCE",
    "SUPPORTED_PUBLIC_RECORD_CLAIMS",
    "UNSUPPORTED_PUBLIC_RECORD_CLAIMS",
    "STANDARD_PUBLIC_RECORD_LIMITATIONS",
    "CONNECTOR_SPECS",
    "PublicRecordEngineStatus",
    "PublicRecordConnectorStatus",
    "PublicRecordFactStatus",
    "PublicRecordQueryMode",
    "PublicRecordJurisdiction",
    "ManualReviewSeverity",
    "PublicRecordRequest",
    "PublicRecordSourceReference",
    "PublicRecordFact",
    "ConnectorExecutionResult",
    "ConnectorReadiness",
    "PublicRecordMergeResult",
    "PublicRecordEngineResult",
    "PublicRecordRequestNormalizer",
    "PublicRecordJurisdictionRouter",
    "PublicRecordConnectorLoader",
    "PublicRecordConnectorExecutor",
    "PublicRecordFactExtractor",
    "PublicRecordMerger",
    "PublicRecordsEngine",
    "PublicRecordEngine",
    "PublicRecordsOrchestrator",
    "PublicRecordOrchestrator",
    "collect_public_records",
    "search_public_records",
    "build_public_record_profile",
    "lookup_public_property",
    "validate_public_records_governance",
    "get_public_records_engine_metadata",
    "get_public_records_connector_readiness",
    "get_public_records_engine_health",
    "get_public_records_engine_readiness",
    "get_public_records_engine_diagnostics",
]


# ============================================================
# END OF FILE
# ============================================================