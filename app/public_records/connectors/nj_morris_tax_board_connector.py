# ============================================================
# AUSSEM1
# PHASE 2.47 PART 1.00
# ENTERPRISE MORRIS COUNTY TAX BOARD CONNECTOR
# FILE: app/public_records/connectors/nj_morris_tax_board_connector.py
# PURPOSE:
# Strengthen Morris County tax-board style public-record extraction
# for source-governed property intelligence workflows.
#
# THIS CONNECTOR FOCUSES ON:
# - tax year
# - block
# - lot
# - qualifier
# - municipality
# - property class
# - land assessment
# - improvement assessment
# - total assessment
# - owner reference if source-backed
# - sale reference if source-backed
# - source attribution
# - manual-review flags
#
# CORE GOVERNANCE:
# - No fabricated tax records.
# - No fabricated owner facts.
# - No fabricated sale history.
# - No fabricated assessment values.
# - No live scraping unless a future approved source client is connected.
# - Assessment is not market value.
# - Assessment is not listing price.
# - Assessment is not an appraisal.
# - Missing source-backed fields remain unavailable.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# ENTERPRISE MORRIS COUNTY TAX BOARD CONNECTOR ACTIVE
# ============================================================


from __future__ import annotations

# ============================================================
# SECTION 01 - STANDARD LIBRARY IMPORTS
# ============================================================

import hashlib
import json
import math
import re
import traceback
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import date
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

CONNECTOR_NAME = "Aussem1 Morris County Tax Board Connector"

CONNECTOR_VERSION = "0.2.0"

CONNECTOR_PHASE = "PHASE 2.47 PART 1.00"

CONNECTOR_STATUS = "enterprise_morris_county_tax_board_connector_active"

CONNECTOR_KEY = "nj_morris_tax_board"

CONNECTOR_SOURCE_TYPE = "morris_tax_board"

CONNECTOR_AUTHORITY = "county_tax_board_public_record"

CONNECTOR_JURISDICTION = "Morris County, NJ"

CONNECTOR_RELEASE_CHANNEL = "development"


# ============================================================
# SECTION 03 - GOVERNANCE
# ============================================================

TAX_BOARD_CONNECTOR_GOVERNANCE = {
    "fabricated_tax_records_allowed": False,
    "fabricated_assessment_values_allowed": False,
    "fabricated_owner_references_allowed": False,
    "fabricated_sale_references_allowed": False,
    "fabricated_market_value_allowed": False,
    "assessment_as_market_value_allowed": False,
    "assessment_as_listing_price_allowed": False,
    "assessment_as_appraisal_allowed": False,
    "source_attribution_required": True,
    "manual_review_for_ambiguous_records": True,
    "missing_fields_must_remain_unavailable": True,
    "partial_source_backed_results_allowed": True,
}


SUPPORTED_FIELDS = [
    "tax_year",
    "block",
    "lot",
    "qualifier",
    "municipality",
    "county",
    "state_code",
    "property_class",
    "land_assessment",
    "improvement_assessment",
    "total_assessment",
    "owner_reference",
    "sale_reference",
    "source_attribution",
    "manual_review_flags",
]


UNSUPPORTED_CLAIMS = [
    "current_market_value",
    "active_listing_status",
    "under_contract_status",
    "current_listing_price",
    "appraisal_value",
    "legal_title_opinion",
    "survey_boundary",
]


STANDARD_LIMITATIONS = [
    "Tax assessment is public-record context and is not current market value.",
    "Tax assessment is not a listing price.",
    "Tax assessment is not an appraisal.",
    "Owner reference is public-record context and may require manual review.",
    "Sale reference from tax data is historical context only when source-backed.",
    "Current listing status requires an authorized MLS, RESO, IDX, broker-authorized feed, or listing-provider source.",
]


# ============================================================
# SECTION 04 - REGEX / NORMALIZATION CONSTANTS
# ============================================================

MONEY_RE = re.compile(r"[-+]?\$?\s*([0-9]{1,3}(?:,[0-9]{3})*|[0-9]+)(?:\.[0-9]+)?")

YEAR_RE = re.compile(r"\b(19[0-9]{2}|20[0-9]{2}|21[0-9]{2})\b")

BLOCK_LOT_RE = re.compile(
    r"\b(?:BLOCK|BLK)\s*[:#\-]?\s*(?P<block>[A-Z0-9.\-]+)\b.*?\b(?:LOT|LT)\s*[:#\-]?\s*(?P<lot>[A-Z0-9.\-]+)\b",
    re.IGNORECASE,
)

LOT_BLOCK_RE = re.compile(
    r"\b(?:LOT|LT)\s*[:#\-]?\s*(?P<lot>[A-Z0-9.\-]+)\b.*?\b(?:BLOCK|BLK)\s*[:#\-]?\s*(?P<block>[A-Z0-9.\-]+)\b",
    re.IGNORECASE,
)

QUALIFIER_RE = re.compile(
    r"\b(?:QUALIFIER|QUAL|Q)\s*[:#\-]?\s*(?P<qualifier>[A-Z0-9.\-]+)\b",
    re.IGNORECASE,
)

WHITESPACE_RE = re.compile(r"\s+")


# ============================================================
# SECTION 05 - MORRIS COUNTY MUNICIPALITY HINTS
# ============================================================

MORRIS_COUNTY_MUNICIPALITIES = {
    "BOONTON": "Boonton",
    "BOONTON TOWNSHIP": "Boonton Township",
    "BUTLER": "Butler",
    "CHATHAM": "Chatham",
    "CHATHAM BOROUGH": "Chatham Borough",
    "CHATHAM TOWNSHIP": "Chatham Township",
    "CHESTER": "Chester",
    "CHESTER BOROUGH": "Chester Borough",
    "CHESTER TOWNSHIP": "Chester Township",
    "DENVILLE": "Denville",
    "DOVER": "Dover",
    "EAST HANOVER": "East Hanover",
    "FLORHAM PARK": "Florham Park",
    "HANOVER": "Hanover",
    "HANOVER TOWNSHIP": "Hanover Township",
    "HARDING": "Harding",
    "HARDING TOWNSHIP": "Harding Township",
    "JEFFERSON": "Jefferson",
    "JEFFERSON TOWNSHIP": "Jefferson Township",
    "KINNELON": "Kinnelon",
    "LINCOLN PARK": "Lincoln Park",
    "LONG HILL": "Long Hill",
    "LONG HILL TOWNSHIP": "Long Hill Township",
    "MADISON": "Madison",
    "MENDHAM": "Mendham",
    "MENDHAM BOROUGH": "Mendham Borough",
    "MENDHAM TOWNSHIP": "Mendham Township",
    "MINE HILL": "Mine Hill",
    "MONTVILLE": "Montville",
    "MONTVILLE TOWNSHIP": "Montville Township",
    "MORRIS": "Morris Township",
    "MORRIS TOWNSHIP": "Morris Township",
    "MORRIS PLAINS": "Morris Plains",
    "MORRISTOWN": "Morristown",
    "MOUNT ARLINGTON": "Mount Arlington",
    "MOUNT OLIVE": "Mount Olive",
    "MOUNT OLIVE TOWNSHIP": "Mount Olive Township",
    "MOUNTAIN LAKES": "Mountain Lakes",
    "NETCONG": "Netcong",
    "PARSIPPANY": "Parsippany-Troy Hills",
    "PARSIPPANY TROY HILLS": "Parsippany-Troy Hills",
    "PARSIPPANY-TROY HILLS": "Parsippany-Troy Hills",
    "PASSAIC TOWNSHIP": "Passaic Township",
    "PEQUANNOCK": "Pequannock Township",
    "PEQUANNOCK TOWNSHIP": "Pequannock Township",
    "RANDOLPH": "Randolph",
    "RANDOLPH TOWNSHIP": "Randolph Township",
    "RIVERDALE": "Riverdale",
    "ROCKAWAY": "Rockaway",
    "ROCKAWAY BOROUGH": "Rockaway Borough",
    "ROCKAWAY TOWNSHIP": "Rockaway Township",
    "ROXBURY": "Roxbury Township",
    "ROXBURY TOWNSHIP": "Roxbury Township",
    "VICTORY GARDENS": "Victory Gardens",
    "WASHINGTON": "Washington Township",
    "WASHINGTON TOWNSHIP": "Washington Township",
    "WHARTON": "Wharton",
}


# ============================================================
# SECTION 06 - ENUMERATIONS
# ============================================================

class TaxBoardConnectorStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    SKIPPED = "skipped"
    ERROR = "error"


class TaxBoardFactStatus(StrEnum):
    SOURCE_BACKED = "source_backed"
    INFERRED = "inferred"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    CONFLICTED = "conflicted"


class TaxBoardQueryMode(StrEnum):
    ADDRESS = "address"
    BLOCK_LOT = "block_lot"
    PARCEL_ID = "parcel_id"
    OWNER_REFERENCE = "owner_reference"
    UNKNOWN = "unknown"


class ManualReviewSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================
# SECTION 07 - UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def safe_string(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def normalize_text(value: Any) -> str:
    text = safe_string(value).upper()
    text = WHITESPACE_RE.sub(" ", text).strip()

    return text


def normalize_key(value: Any) -> str:
    text = safe_string(value).lower()
    output: list[str] = []

    for character in text:
        if character.isalnum():
            output.append(character)
        elif output and output[-1] != "_":
            output.append("_")

    return "".join(output).strip("_")


def clean_value(value: Any) -> str | None:
    text = safe_string(value)

    return text or None


def normalize_state(value: Any) -> str | None:
    text = normalize_text(value)

    if not text:
        return None

    if text in {"NJ", "NEW JERSEY"}:
        return "NJ"

    return text


def normalize_county(value: Any) -> str | None:
    text = safe_string(value)

    if not text:
        return None

    text = text.replace("County", "").replace("county", "").strip()

    return text.title()


def normalize_municipality(value: Any) -> str | None:
    text = normalize_text(value)

    if not text:
        return None

    if text in MORRIS_COUNTY_MUNICIPALITIES:
        return MORRIS_COUNTY_MUNICIPALITIES[text]

    return safe_string(value).title()


def normalize_block_lot(value: Any) -> str | None:
    text = normalize_text(value)

    if not text:
        return None

    cleaned = re.sub(r"[^A-Z0-9.\-]", "", text)

    return cleaned or None


def parse_money(value: Any) -> float | None:
    if value in (None, ""):
        return None

    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)

    text = safe_string(value)

    if not text:
        return None

    match = MONEY_RE.search(text)

    if not match:
        return None

    try:
        return float(match.group(1).replace(",", ""))
    except Exception:
        return None


def parse_year(value: Any) -> str | None:
    text = safe_string(value)

    if not text:
        return None

    match = YEAR_RE.search(text)

    if not match:
        return None

    return match.group(1)


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

    if isinstance(value, (datetime, date)):
        return value.isoformat()

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
        full_key = f"{prefix}.{normalize_key(key)}" if prefix else normalize_key(key)

        if isinstance(value, Mapping):
            result.update(flatten_mapping(value, prefix=full_key))
        else:
            result[full_key] = value

    return result


def first_value(payload: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, "", [], {}):
            return payload[key]

    return None


# ============================================================
# SECTION 08 - DATA CONTRACTS
# ============================================================

@dataclass
class TaxBoardRequest:
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
    tax_year: str | None = None
    query_mode: str = TaxBoardQueryMode.UNKNOWN.value
    strict_source_mode: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class TaxBoardSourceReference:
    source_name: str = CONNECTOR_NAME
    source_type: str = CONNECTOR_SOURCE_TYPE
    connector_key: str = CONNECTOR_KEY
    source_authority: str = CONNECTOR_AUTHORITY
    jurisdiction: str = CONNECTOR_JURISDICTION
    record_id: str | None = None
    source_url: str | None = None
    retrieved_at: str = field(default_factory=utc_now)
    field_path: str | None = None
    confidence: float = 0.0
    raw_payload_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class TaxAssessmentRecord:
    tax_year: str | None = None
    block: str | None = None
    lot: str | None = None
    qualifier: str | None = None
    municipality: str | None = None
    county: str | None = "Morris"
    state_code: str | None = "NJ"
    property_class: str | None = None
    land_assessment: float | None = None
    improvement_assessment: float | None = None
    total_assessment: float | None = None
    owner_reference: str | None = None
    sale_date: str | None = None
    sale_price: float | None = None
    deed_book: str | None = None
    deed_page: str | None = None
    document_number: str | None = None
    source_status: str = TaxBoardFactStatus.UNAVAILABLE.value
    confidence: float = 0.0
    manual_review_required: bool = False
    manual_review_reasons: list[str] = field(default_factory=list)
    source: TaxBoardSourceReference = field(default_factory=TaxBoardSourceReference)
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class TaxBoardManualReviewItem:
    code: str
    message: str
    severity: str = ManualReviewSeverity.WARNING.value
    field_path: str | None = None
    required_action: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class TaxBoardConnectorResult:
    success: bool
    status: str
    query_mode: str
    request: TaxBoardRequest
    records: list[dict[str, Any]] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)
    sources: list[TaxBoardSourceReference] = field(default_factory=list)
    manual_review_items: list[TaxBoardManualReviewItem] = field(default_factory=list)
    unavailable_fields: list[dict[str, Any]] = field(default_factory=list)
    unsupported_claims: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    completeness_score: float = 0.0
    source_coverage_score: float = 0.0
    limitations: list[str] = field(default_factory=lambda: list(STANDARD_LIMITATIONS))
    governance: dict[str, Any] = field(default_factory=lambda: TAX_BOARD_CONNECTOR_GOVERNANCE.copy())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = object_to_dict(asdict(self))

        if isinstance(payload.get("facts"), Mapping):
            for key, value in payload["facts"].items():
                payload.setdefault(key, value)

        return payload


# ============================================================
# SECTION 09 - REQUEST NORMALIZER
# ============================================================

class TaxBoardRequestNormalizer:
    def normalize(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> TaxBoardRequest:
        if isinstance(request, TaxBoardRequest):
            normalized = request
        elif isinstance(request, Mapping):
            normalized = self.from_mapping(request)
        elif isinstance(request, str):
            normalized = TaxBoardRequest(
                raw_query=request,
                street_address=request,
                normalized_address=request,
            )
        else:
            normalized = self.from_mapping(kwargs)

        for key, value in kwargs.items():
            if hasattr(normalized, key) and value not in (None, ""):
                setattr(normalized, key, value)

        normalized.state_code = normalize_state(normalized.state_code or normalized.state) or "NJ"
        normalized.state = normalized.state_code
        normalized.county = normalize_county(normalized.county) or "Morris"
        normalized.municipality = normalize_municipality(normalized.municipality)
        normalized.block = normalize_block_lot(normalized.block)
        normalized.lot = normalize_block_lot(normalized.lot)
        normalized.qualifier = normalize_block_lot(normalized.qualifier)
        normalized.tax_year = parse_year(normalized.tax_year)

        self.extract_block_lot_from_query(normalized)
        self.detect_municipality_from_query(normalized)

        if normalized.query_mode == TaxBoardQueryMode.UNKNOWN.value:
            normalized.query_mode = self.detect_query_mode(normalized)

        return normalized

    @staticmethod
    def from_mapping(payload: Mapping[str, Any]) -> TaxBoardRequest:
        return TaxBoardRequest(
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
            tax_year=payload.get("tax_year"),
            query_mode=payload.get("query_mode")
            or payload.get("primary_query_mode")
            or TaxBoardQueryMode.UNKNOWN.value,
            strict_source_mode=bool(payload.get("strict_source_mode", True)),
            metadata=dict(payload.get("metadata") or {}),
        )

    @staticmethod
    def detect_query_mode(request: TaxBoardRequest) -> str:
        if request.block and request.lot:
            return TaxBoardQueryMode.BLOCK_LOT.value

        if request.parcel_id:
            return TaxBoardQueryMode.PARCEL_ID.value

        if request.owner_reference and not (request.street_address or request.raw_query):
            return TaxBoardQueryMode.OWNER_REFERENCE.value

        if request.street_address or request.normalized_address or request.raw_query:
            return TaxBoardQueryMode.ADDRESS.value

        return TaxBoardQueryMode.UNKNOWN.value

    @staticmethod
    def extract_block_lot_from_query(request: TaxBoardRequest) -> None:
        text = " ".join(
            value
            for value in [
                request.raw_query,
                request.street_address,
                request.normalized_address,
            ]
            if value
        )

        if not text:
            return

        match = BLOCK_LOT_RE.search(text) or LOT_BLOCK_RE.search(text)

        if match:
            request.block = request.block or normalize_block_lot(match.group("block"))
            request.lot = request.lot or normalize_block_lot(match.group("lot"))

        qualifier_match = QUALIFIER_RE.search(text)

        if qualifier_match:
            request.qualifier = request.qualifier or normalize_block_lot(
                qualifier_match.group("qualifier")
            )

    @staticmethod
    def detect_municipality_from_query(request: TaxBoardRequest) -> None:
        if request.municipality:
            return

        text = normalize_text(
            " ".join(
                value
                for value in [
                    request.raw_query,
                    request.street_address,
                    request.normalized_address,
                ]
                if value
            )
        )

        best: tuple[int, str] | None = None

        for key, display in MORRIS_COUNTY_MUNICIPALITIES.items():
            if f" {key} " in f" {text} ":
                length = len(key)
                if best is None or length > best[0]:
                    best = (length, display)

        if best:
            request.municipality = best[1]


# ============================================================
# SECTION 10 - SOURCE-BACKED RECORD NORMALIZER
# ============================================================

class TaxBoardRecordNormalizer:
    FIELD_CANDIDATES = {
        "tax_year": [
            "tax_year",
            "year",
            "assessment_year",
            "tax.assessment_year",
            "assessment.tax_year",
        ],
        "block": [
            "block",
            "blk",
            "tax.block",
            "assessment.block",
            "parcel.block",
        ],
        "lot": [
            "lot",
            "lt",
            "tax.lot",
            "assessment.lot",
            "parcel.lot",
        ],
        "qualifier": [
            "qualifier",
            "qual",
            "q",
            "tax.qualifier",
            "assessment.qualifier",
        ],
        "municipality": [
            "municipality",
            "muni",
            "city",
            "town",
            "tax.municipality",
            "assessment.municipality",
        ],
        "property_class": [
            "property_class",
            "class",
            "prop_class",
            "tax.property_class",
            "assessment.property_class",
        ],
        "land_assessment": [
            "land_assessment",
            "land_value",
            "land_assessed_value",
            "tax.land_assessment",
            "assessment.land_assessment",
        ],
        "improvement_assessment": [
            "improvement_assessment",
            "improvement_value",
            "improvements",
            "building_assessment",
            "tax.improvement_assessment",
            "assessment.improvement_assessment",
        ],
        "total_assessment": [
            "total_assessment",
            "assessed_value",
            "total_assessed_value",
            "tax.total_assessment",
            "assessment.total_assessment",
        ],
        "owner_reference": [
            "owner",
            "owner_name",
            "owner_reference",
            "tax.owner",
            "assessment.owner",
        ],
        "sale_date": [
            "sale_date",
            "last_sale_date",
            "deed_date",
            "tax.sale_date",
        ],
        "sale_price": [
            "sale_price",
            "last_sale_price",
            "consideration",
            "tax.sale_price",
        ],
        "deed_book": [
            "deed_book",
            "book",
            "sale_book",
        ],
        "deed_page": [
            "deed_page",
            "page",
            "sale_page",
        ],
        "document_number": [
            "document_number",
            "instrument_number",
            "doc_number",
            "id",
        ],
    }

    def normalize_record(
        self,
        record_payload: Mapping[str, Any],
        *,
        request: TaxBoardRequest,
        source: TaxBoardSourceReference | None = None,
    ) -> TaxAssessmentRecord:
        flattened = flatten_mapping(record_payload)

        tax_year = parse_year(self.extract(flattened, "tax_year")) or request.tax_year
        block = normalize_block_lot(self.extract(flattened, "block") or request.block)
        lot = normalize_block_lot(self.extract(flattened, "lot") or request.lot)
        qualifier = normalize_block_lot(
            self.extract(flattened, "qualifier") or request.qualifier
        )
        municipality = normalize_municipality(
            self.extract(flattened, "municipality") or request.municipality
        )
        property_class = clean_value(self.extract(flattened, "property_class"))
        land_assessment = parse_money(self.extract(flattened, "land_assessment"))
        improvement_assessment = parse_money(
            self.extract(flattened, "improvement_assessment")
        )
        total_assessment = parse_money(self.extract(flattened, "total_assessment"))
        owner_reference = clean_value(self.extract(flattened, "owner_reference"))
        sale_date = clean_value(self.extract(flattened, "sale_date"))
        sale_price = parse_money(self.extract(flattened, "sale_price"))
        deed_book = clean_value(self.extract(flattened, "deed_book"))
        deed_page = clean_value(self.extract(flattened, "deed_page"))
        document_number = clean_value(self.extract(flattened, "document_number"))

        source = source or TaxBoardSourceReference(
            confidence=0.0,
            raw_payload_hash=stable_hash(record_payload),
        )

        confidence = self.score_record(
            tax_year=tax_year,
            block=block,
            lot=lot,
            municipality=municipality,
            property_class=property_class,
            land_assessment=land_assessment,
            improvement_assessment=improvement_assessment,
            total_assessment=total_assessment,
            owner_reference=owner_reference,
            sale_date=sale_date,
            sale_price=sale_price,
        )

        manual_review_reasons = self.manual_review_reasons(
            tax_year=tax_year,
            block=block,
            lot=lot,
            municipality=municipality,
            total_assessment=total_assessment,
            record_payload=record_payload,
        )

        status_value = (
            TaxBoardFactStatus.SOURCE_BACKED.value
            if confidence > 0
            else TaxBoardFactStatus.UNAVAILABLE.value
        )

        if manual_review_reasons and confidence > 0:
            status_value = TaxBoardFactStatus.MANUAL_REVIEW_REQUIRED.value

        source.confidence = confidence
        source.raw_payload_hash = stable_hash(record_payload)

        return TaxAssessmentRecord(
            tax_year=tax_year,
            block=block,
            lot=lot,
            qualifier=qualifier,
            municipality=municipality,
            county="Morris",
            state_code="NJ",
            property_class=property_class,
            land_assessment=land_assessment,
            improvement_assessment=improvement_assessment,
            total_assessment=total_assessment,
            owner_reference=owner_reference,
            sale_date=sale_date,
            sale_price=sale_price,
            deed_book=deed_book,
            deed_page=deed_page,
            document_number=document_number,
            source_status=status_value,
            confidence=confidence,
            manual_review_required=bool(manual_review_reasons),
            manual_review_reasons=manual_review_reasons,
            source=source,
            raw_payload=dict(record_payload),
        )

    def normalize_records(
        self,
        records: Sequence[Mapping[str, Any]],
        *,
        request: TaxBoardRequest,
    ) -> list[TaxAssessmentRecord]:
        normalized: list[TaxAssessmentRecord] = []

        for index, record in enumerate(records):
            source = TaxBoardSourceReference(
                record_id=clean_value(
                    record.get("record_id")
                    or record.get("id")
                    or f"tax-board-record-{index + 1}"
                ),
                field_path="tax_assessment_context",
                confidence=0.0,
                raw_payload_hash=stable_hash(record),
                metadata={
                    "record_index": index,
                },
            )
            normalized.append(
                self.normalize_record(
                    record,
                    request=request,
                    source=source,
                )
            )

        return normalized

    def extract(self, flattened: Mapping[str, Any], field_name: str) -> Any:
        return first_value(flattened, self.FIELD_CANDIDATES.get(field_name, []))

    @staticmethod
    def score_record(
        *,
        tax_year: str | None,
        block: str | None,
        lot: str | None,
        municipality: str | None,
        property_class: str | None,
        land_assessment: float | None,
        improvement_assessment: float | None,
        total_assessment: float | None,
        owner_reference: str | None,
        sale_date: str | None,
        sale_price: float | None,
    ) -> float:
        score = 0.0

        if tax_year:
            score += 0.10

        if block:
            score += 0.12

        if lot:
            score += 0.12

        if municipality:
            score += 0.10

        if property_class:
            score += 0.08

        if land_assessment is not None:
            score += 0.12

        if improvement_assessment is not None:
            score += 0.12

        if total_assessment is not None:
            score += 0.16

        if owner_reference:
            score += 0.05

        if sale_date or sale_price is not None:
            score += 0.03

        return round(clamp_score(score), 6)

    @staticmethod
    def manual_review_reasons(
        *,
        tax_year: str | None,
        block: str | None,
        lot: str | None,
        municipality: str | None,
        total_assessment: float | None,
        record_payload: Mapping[str, Any],
    ) -> list[str]:
        reasons: list[str] = []

        if not tax_year:
            reasons.append("tax_year_missing")

        if not block:
            reasons.append("block_missing")

        if not lot:
            reasons.append("lot_missing")

        if not municipality:
            reasons.append("municipality_missing")

        if total_assessment is None:
            reasons.append("total_assessment_missing")

        if record_payload.get("conflict") or record_payload.get("conflicted"):
            reasons.append("source_payload_marked_conflicted")

        return reasons


# ============================================================
# SECTION 11 - RAW SOURCE CLIENT PLACEHOLDER
# ============================================================

class MorrisTaxBoardSourceClient:
    """
    Source client abstraction.

    This class intentionally does not scrape or fabricate records.
    Future approved integrations can inject a client with source-backed
    data retrieval. The default client returns unavailable.
    """

    def search(
        self,
        request: TaxBoardRequest,
    ) -> dict[str, Any]:
        return {
            "success": False,
            "status": TaxBoardConnectorStatus.UNAVAILABLE.value,
            "records": [],
            "facts": {},
            "warnings": [
                "No live Morris County tax-board source client is configured."
            ],
            "errors": [],
            "metadata": {
                "client": self.__class__.__name__,
                "generated_at": utc_now(),
                "no_fabrication": True,
            },
        }


# ============================================================
# SECTION 12 - RESULT BUILDER
# ============================================================

class TaxBoardResultBuilder:
    def build(
        self,
        *,
        request: TaxBoardRequest,
        records: Sequence[TaxAssessmentRecord],
        warnings: Sequence[str] | None = None,
        errors: Sequence[Mapping[str, Any]] | None = None,
        raw_payload: Mapping[str, Any] | None = None,
    ) -> TaxBoardConnectorResult:
        warnings_list = list(warnings or [])
        errors_list = [dict(error) for error in errors or []]
        records_list = [record.to_dict() for record in records]
        facts = self.build_facts(records)
        sources = self.deduplicate_sources([record.source for record in records])
        manual_review_items = self.build_manual_review_items(request, records)
        unavailable_fields = self.build_unavailable_fields(facts)
        unsupported_claims = self.build_unsupported_claims()
        completeness_score = self.score_completeness(facts)
        source_coverage_score = self.score_source_coverage(facts, sources)
        confidence = self.score_confidence(
            records=records,
            completeness_score=completeness_score,
            source_coverage_score=source_coverage_score,
            manual_review_items=manual_review_items,
            errors=errors_list,
        )

        if errors_list and not records:
            status_value = TaxBoardConnectorStatus.ERROR.value
        elif records and manual_review_items:
            status_value = TaxBoardConnectorStatus.PARTIAL.value
        elif records:
            status_value = TaxBoardConnectorStatus.SUCCESS.value
        else:
            status_value = TaxBoardConnectorStatus.PARTIAL.value

        success = status_value in {
            TaxBoardConnectorStatus.SUCCESS.value,
            TaxBoardConnectorStatus.PARTIAL.value,
        }

        if not records:
            warnings_list.append(
                "No source-backed Morris County tax assessment records were returned."
            )

        return TaxBoardConnectorResult(
            success=success,
            status=status_value,
            query_mode=request.query_mode,
            request=request,
            records=records_list,
            facts=facts,
            sources=sources,
            manual_review_items=manual_review_items,
            unavailable_fields=unavailable_fields,
            unsupported_claims=unsupported_claims,
            warnings=list(dict.fromkeys([warning for warning in warnings_list if warning])),
            errors=errors_list,
            confidence=confidence,
            completeness_score=completeness_score,
            source_coverage_score=source_coverage_score,
            metadata={
                "connector": CONNECTOR_NAME,
                "version": CONNECTOR_VERSION,
                "phase": CONNECTOR_PHASE,
                "generated_at": utc_now(),
                "record_count": len(records),
                "raw_payload_hash": stable_hash(raw_payload or {}),
            },
        )

    def build_facts(
        self,
        records: Sequence[TaxAssessmentRecord],
    ) -> dict[str, Any]:
        best = self.select_best_record(records)

        if best is None:
            return self.empty_facts()

        return {
            "parcel_identity": {
                "block": best.block,
                "lot": best.lot,
                "qualifier": best.qualifier,
                "municipality": best.municipality,
                "county": best.county,
                "state_code": best.state_code,
                "property_class": best.property_class,
                "source_status": best.source_status,
                "confidence": best.confidence,
            },
            "tax_assessment_context": {
                "tax_year": best.tax_year,
                "land_assessment": best.land_assessment,
                "improvement_assessment": best.improvement_assessment,
                "total_assessment": best.total_assessment,
                "property_class": best.property_class,
                "assessment_source_note": (
                    "Tax assessment is public-record context and is not current market value."
                ),
                "source_status": best.source_status,
                "confidence": best.confidence,
            },
            "property_tax_context": {
                "tax_year": best.tax_year,
                "tax_amount": None,
                "tax_rate": None,
                "estimated_annual_tax": None,
                "source_status": TaxBoardFactStatus.UNAVAILABLE.value,
                "confidence": 0.0,
            },
            "owner_references": (
                [
                    {
                        "owner_name": best.owner_reference,
                        "mailing_address": None,
                        "owner_source_note": (
                            "Owner reference is public-record context and may require manual review."
                        ),
                        "source_status": best.source_status,
                        "confidence": min(best.confidence, 0.62),
                    }
                ]
                if best.owner_reference
                else []
            ),
            "sale_history_references": (
                [
                    {
                        "sale_date": best.sale_date,
                        "sale_price": best.sale_price,
                        "deed_book": best.deed_book,
                        "deed_page": best.deed_page,
                        "document_number": best.document_number,
                        "source_status": best.source_status,
                        "confidence": min(best.confidence, 0.60),
                    }
                ]
                if best.sale_date or best.sale_price is not None
                else []
            ),
        }

    @staticmethod
    def empty_facts() -> dict[str, Any]:
        return {
            "parcel_identity": {
                "block": None,
                "lot": None,
                "qualifier": None,
                "municipality": None,
                "county": "Morris",
                "state_code": "NJ",
                "property_class": None,
                "source_status": TaxBoardFactStatus.UNAVAILABLE.value,
                "confidence": 0.0,
            },
            "tax_assessment_context": {
                "tax_year": None,
                "land_assessment": None,
                "improvement_assessment": None,
                "total_assessment": None,
                "property_class": None,
                "assessment_source_note": (
                    "Tax assessment is public-record context and is not current market value."
                ),
                "source_status": TaxBoardFactStatus.UNAVAILABLE.value,
                "confidence": 0.0,
            },
            "property_tax_context": {
                "tax_year": None,
                "tax_amount": None,
                "tax_rate": None,
                "estimated_annual_tax": None,
                "source_status": TaxBoardFactStatus.UNAVAILABLE.value,
                "confidence": 0.0,
            },
            "owner_references": [],
            "sale_history_references": [],
        }

    @staticmethod
    def select_best_record(
        records: Sequence[TaxAssessmentRecord],
    ) -> TaxAssessmentRecord | None:
        if not records:
            return None

        return sorted(
            records,
            key=lambda item: (
                item.confidence,
                int(item.tax_year or 0) if item.tax_year else 0,
            ),
            reverse=True,
        )[0]

    @staticmethod
    def deduplicate_sources(
        sources: Sequence[TaxBoardSourceReference],
    ) -> list[TaxBoardSourceReference]:
        seen: set[str] = set()
        output: list[TaxBoardSourceReference] = []

        for source in sources:
            key = stable_hash(source.to_dict())

            if key in seen:
                continue

            seen.add(key)
            output.append(source)

        return output

    @staticmethod
    def build_manual_review_items(
        request: TaxBoardRequest,
        records: Sequence[TaxAssessmentRecord],
    ) -> list[TaxBoardManualReviewItem]:
        items: list[TaxBoardManualReviewItem] = []

        if request.query_mode == TaxBoardQueryMode.UNKNOWN.value:
            items.append(
                TaxBoardManualReviewItem(
                    code="unknown_tax_board_query_mode",
                    message="Tax-board query mode could not be determined.",
                    field_path="request.query_mode",
                    required_action="Provide address, block/lot, parcel ID, or owner reference.",
                )
            )

        if request.county != "Morris" or request.state_code != "NJ":
            items.append(
                TaxBoardManualReviewItem(
                    code="outside_morris_county_scope",
                    message="Morris County tax-board connector received an out-of-scope request.",
                    field_path="request.county",
                    required_action="Route non-Morris requests to the proper county/state connector.",
                )
            )

        if not records:
            items.append(
                TaxBoardManualReviewItem(
                    code="no_source_backed_tax_records",
                    message="No source-backed tax assessment records were returned.",
                    field_path="records",
                    required_action="Connect approved tax-board source client or manually verify public record.",
                )
            )

        for record in records:
            for reason in record.manual_review_reasons:
                items.append(
                    TaxBoardManualReviewItem(
                        code=reason,
                        message=f"Tax assessment record requires review: {reason}.",
                        field_path="tax_assessment_context",
                        required_action="Verify tax-board source record before relying on this field.",
                        metadata={
                            "record_hash": stable_hash(record.to_dict()),
                        },
                    )
                )

        return items

    @staticmethod
    def build_unavailable_fields(
        facts: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        unavailable: list[dict[str, Any]] = []

        for section_name, section_payload in facts.items():
            if isinstance(section_payload, Mapping):
                for field_name, value in section_payload.items():
                    if field_name in {"source_status", "confidence", "assessment_source_note"}:
                        continue

                    if value in (None, "", [], {}):
                        unavailable.append(
                            {
                                "field_name": field_name,
                                "field_path": f"{section_name}.{field_name}",
                                "reason": (
                                    f"{section_name}.{field_name} is unavailable from current Morris County tax-board source data."
                                ),
                                "required_source": "morris_county_tax_board_public_record",
                                "can_public_records_support": True,
                                "manual_review_required": False,
                            }
                        )

            if isinstance(section_payload, list) and not section_payload:
                unavailable.append(
                    {
                        "field_name": section_name,
                        "field_path": section_name,
                        "reason": (
                            f"{section_name} is unavailable from current Morris County tax-board source data."
                        ),
                        "required_source": "morris_county_tax_board_public_record",
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
                "status": TaxBoardFactStatus.UNSUPPORTED.value,
                "reason": (
                    "Morris County tax-board assessment data cannot prove this claim."
                ),
                "required_source": (
                    "valuation_engine_and_comparable_sales"
                    if "market_value" in claim or "appraisal" in claim
                    else "authorized_listing_feed_or_legal_source"
                ),
            }
            for claim in UNSUPPORTED_CLAIMS
        ]

    @staticmethod
    def score_completeness(facts: Mapping[str, Any]) -> float:
        values: list[Any] = []

        for section_payload in facts.values():
            if isinstance(section_payload, Mapping):
                for key, value in section_payload.items():
                    if key in {"source_status", "confidence", "assessment_source_note"}:
                        continue
                    values.append(value)
            elif isinstance(section_payload, list):
                values.append(section_payload)

        if not values:
            return 0.0

        present = [
            value
            for value in values
            if value not in (None, "", [], {})
        ]

        return round(clamp_score(len(present) / len(values)), 6)

    @staticmethod
    def score_source_coverage(
        facts: Mapping[str, Any],
        sources: Sequence[TaxBoardSourceReference],
    ) -> float:
        if not sources:
            return 0.0

        source_scores = [
            source.confidence
            for source in sources
        ]

        return round(clamp_score(sum(source_scores) / len(source_scores)), 6)

    @staticmethod
    def score_confidence(
        *,
        records: Sequence[TaxAssessmentRecord],
        completeness_score: float,
        source_coverage_score: float,
        manual_review_items: Sequence[TaxBoardManualReviewItem],
        errors: Sequence[Mapping[str, Any]],
    ) -> float:
        record_score = 0.0

        if records:
            record_score = sum(record.confidence for record in records) / len(records)

        review_penalty = min(len(manual_review_items) * 0.04, 0.35)
        error_penalty = min(len(errors) * 0.08, 0.40)

        score = (
            record_score * 0.45
            + completeness_score * 0.30
            + source_coverage_score * 0.25
            - review_penalty
            - error_penalty
        )

        return round(clamp_score(score), 6)


# ============================================================
# SECTION 13 - ENTERPRISE CONNECTOR
# ============================================================

class NJMorrisTaxBoardConnector:
    def __init__(
        self,
        *,
        source_client: MorrisTaxBoardSourceClient | None = None,
        normalizer: TaxBoardRequestNormalizer | None = None,
        record_normalizer: TaxBoardRecordNormalizer | None = None,
        result_builder: TaxBoardResultBuilder | None = None,
    ) -> None:
        self.source_client = source_client or MorrisTaxBoardSourceClient()
        self.normalizer = normalizer or TaxBoardRequestNormalizer()
        self.record_normalizer = record_normalizer or TaxBoardRecordNormalizer()
        self.result_builder = result_builder or TaxBoardResultBuilder()

    def collect(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        normalized_request = self.normalizer.normalize(request, **kwargs)

        if normalized_request.state_code != "NJ" or normalized_request.county != "Morris":
            result = self.result_builder.build(
                request=normalized_request,
                records=[],
                warnings=[
                    "Request is outside Morris County, NJ scope for this connector."
                ],
                errors=[],
                raw_payload={},
            )
            result.status = TaxBoardConnectorStatus.SKIPPED.value
            result.success = True

            return result.to_dict()

        try:
            raw_payload = self.source_client.search(normalized_request)
            raw_records = self.extract_raw_records(raw_payload)

            normalized_records = self.record_normalizer.normalize_records(
                raw_records,
                request=normalized_request,
            )

            warnings = list(raw_payload.get("warnings") or [])
            errors = list(raw_payload.get("errors") or [])

            return self.result_builder.build(
                request=normalized_request,
                records=normalized_records,
                warnings=warnings,
                errors=errors,
                raw_payload=raw_payload,
            ).to_dict()

        except Exception as exc:
            return self.result_builder.build(
                request=normalized_request,
                records=[],
                warnings=[],
                errors=[
                    {
                        "code": "tax_board_connector_error",
                        "message": f"{type(exc).__name__}: {exc}",
                        "traceback": traceback.format_exc(),
                    }
                ],
                raw_payload={},
            ).to_dict()

    def search(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def lookup(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def lookup_property(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def search_public_records(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def run(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def execute(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    @staticmethod
    def extract_raw_records(raw_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
        records = raw_payload.get("records")

        if isinstance(records, list):
            return [
                dict(record)
                for record in records
                if isinstance(record, Mapping)
            ]

        data = raw_payload.get("data")

        if isinstance(data, list):
            return [
                dict(record)
                for record in data
                if isinstance(record, Mapping)
            ]

        if isinstance(data, Mapping):
            return [dict(data)]

        facts = raw_payload.get("facts")

        if isinstance(facts, Mapping):
            return [dict(facts)]

        return []


# Backward-compatible aliases expected by the orchestration engine.
MorrisTaxBoardConnector = NJMorrisTaxBoardConnector
TaxBoardConnector = NJMorrisTaxBoardConnector
PublicRecordConnector = NJMorrisTaxBoardConnector


# ============================================================
# SECTION 14 - CONVENIENCE API
# ============================================================

_default_connector = NJMorrisTaxBoardConnector()


def get_connector() -> NJMorrisTaxBoardConnector:
    return NJMorrisTaxBoardConnector()


def collect_tax_board_records(
    request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return _default_connector.collect(request, **kwargs)


def search_tax_board_records(
    request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return _default_connector.search(request, **kwargs)


def lookup_tax_board_property(
    request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return _default_connector.lookup_property(request, **kwargs)


# ============================================================
# SECTION 15 - HEALTH / READINESS / DIAGNOSTICS
# ============================================================

def validate_tax_board_connector_governance() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    false_keys = [
        "fabricated_tax_records_allowed",
        "fabricated_assessment_values_allowed",
        "fabricated_owner_references_allowed",
        "fabricated_sale_references_allowed",
        "fabricated_market_value_allowed",
        "assessment_as_market_value_allowed",
        "assessment_as_listing_price_allowed",
        "assessment_as_appraisal_allowed",
    ]

    for key in false_keys:
        if TAX_BOARD_CONNECTOR_GOVERNANCE.get(key):
            issues.append(
                {
                    "issue_code": f"{key}_must_remain_false",
                    "severity": "critical",
                    "message": f"{key} must remain False.",
                }
            )

    true_keys = [
        "source_attribution_required",
        "manual_review_for_ambiguous_records",
        "missing_fields_must_remain_unavailable",
        "partial_source_backed_results_allowed",
    ]

    for key in true_keys:
        if not TAX_BOARD_CONNECTOR_GOVERNANCE.get(key):
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


def get_tax_board_connector_metadata() -> dict[str, Any]:
    return {
        "name": CONNECTOR_NAME,
        "version": CONNECTOR_VERSION,
        "phase": CONNECTOR_PHASE,
        "status": CONNECTOR_STATUS,
        "connector_key": CONNECTOR_KEY,
        "source_type": CONNECTOR_SOURCE_TYPE,
        "authority": CONNECTOR_AUTHORITY,
        "jurisdiction": CONNECTOR_JURISDICTION,
        "release_channel": CONNECTOR_RELEASE_CHANNEL,
        "generated_at": utc_now(),
    }


def get_tax_board_connector_health() -> dict[str, Any]:
    governance = validate_tax_board_connector_governance()
    sample = collect_tax_board_records(
        {
            "raw_query": "43 Wetmore Ave, Morristown, NJ 07960",
            "municipality": "Morristown",
            "county": "Morris",
            "state_code": "NJ",
        }
    )

    return {
        "name": CONNECTOR_NAME,
        "version": CONNECTOR_VERSION,
        "phase": CONNECTOR_PHASE,
        "status": CONNECTOR_STATUS,
        "governance_valid": governance["valid"],
        "governance_issue_count": governance["issue_count"],
        "sample_status": sample.get("status"),
        "sample_success": sample.get("success"),
        "sample_confidence": sample.get("confidence"),
        "source_client": _default_connector.source_client.__class__.__name__,
        "live_source_client_configured": not isinstance(
            _default_connector.source_client,
            MorrisTaxBoardSourceClient,
        ),
        "fabricated_tax_records_allowed": False,
        "assessment_as_market_value_allowed": False,
        "generated_at": utc_now(),
    }


def get_tax_board_connector_readiness() -> dict[str, Any]:
    health = get_tax_board_connector_health()

    required = {
        "governance_valid": health["governance_valid"],
        "connector_importable": True,
    }

    optional = {
        "live_source_client_configured": health["live_source_client_configured"],
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
            "app/public_records/connectors/nj_morris_gis_connector.py",
            "app/property_intelligence/valuation_engine.py",
            "app/static/js/dashboard.js",
        ],
        "generated_at": utc_now(),
    }


def get_tax_board_connector_diagnostics() -> dict[str, Any]:
    return {
        "metadata": get_tax_board_connector_metadata(),
        "health": get_tax_board_connector_health(),
        "readiness": get_tax_board_connector_readiness(),
        "governance": TAX_BOARD_CONNECTOR_GOVERNANCE.copy(),
        "governance_validation": validate_tax_board_connector_governance(),
        "supported_fields": SUPPORTED_FIELDS,
        "unsupported_claims": UNSUPPORTED_CLAIMS,
        "standard_limitations": STANDARD_LIMITATIONS,
        "municipality_hint_count": len(MORRIS_COUNTY_MUNICIPALITIES),
        "exports": __all__,
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 16 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "CONNECTOR_NAME",
    "CONNECTOR_VERSION",
    "CONNECTOR_PHASE",
    "CONNECTOR_STATUS",
    "CONNECTOR_KEY",
    "CONNECTOR_SOURCE_TYPE",
    "CONNECTOR_AUTHORITY",
    "CONNECTOR_JURISDICTION",
    "CONNECTOR_RELEASE_CHANNEL",
    "TAX_BOARD_CONNECTOR_GOVERNANCE",
    "SUPPORTED_FIELDS",
    "UNSUPPORTED_CLAIMS",
    "STANDARD_LIMITATIONS",
    "MORRIS_COUNTY_MUNICIPALITIES",
    "TaxBoardConnectorStatus",
    "TaxBoardFactStatus",
    "TaxBoardQueryMode",
    "ManualReviewSeverity",
    "TaxBoardRequest",
    "TaxBoardSourceReference",
    "TaxAssessmentRecord",
    "TaxBoardManualReviewItem",
    "TaxBoardConnectorResult",
    "TaxBoardRequestNormalizer",
    "TaxBoardRecordNormalizer",
    "MorrisTaxBoardSourceClient",
    "TaxBoardResultBuilder",
    "NJMorrisTaxBoardConnector",
    "MorrisTaxBoardConnector",
    "TaxBoardConnector",
    "PublicRecordConnector",
    "get_connector",
    "collect_tax_board_records",
    "search_tax_board_records",
    "lookup_tax_board_property",
    "validate_tax_board_connector_governance",
    "get_tax_board_connector_metadata",
    "get_tax_board_connector_health",
    "get_tax_board_connector_readiness",
    "get_tax_board_connector_diagnostics",
]


# ============================================================
# END OF FILE
# ============================================================
# AUSSEM1
# PHASE 2.47 PART 1.00
# ENTERPRISE MORRIS COUNTY TAX BOARD CONNECTOR
# FILE: app/public_records/connectors/nj_morris_tax_board_connector.py
# PURPOSE:
# Strengthen Morris County tax-board style public-record extraction
# for source-governed property intelligence workflows.
#
# THIS CONNECTOR FOCUSES ON:
# - tax year
# - block
# - lot
# - qualifier
# - municipality
# - property class
# - land assessment
# - improvement assessment
# - total assessment
# - owner reference if source-backed
# - sale reference if source-backed
# - source attribution
# - manual-review flags
#
# CORE GOVERNANCE:
# - No fabricated tax records.
# - No fabricated owner facts.
# - No fabricated sale history.
# - No fabricated assessment values.
# - No live scraping unless a future approved source client is connected.
# - Assessment is not market value.
# - Assessment is not listing price.
# - Assessment is not an appraisal.
# - Missing source-backed fields remain unavailable.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# ENTERPRISE MORRIS COUNTY TAX BOARD CONNECTOR ACTIVE
# ============================================================


from __future__ import annotations

# ============================================================
# SECTION 01 - STANDARD LIBRARY IMPORTS
# ============================================================

import hashlib
import json
import math
import re
import traceback
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import date
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

CONNECTOR_NAME = "Aussem1 Morris County Tax Board Connector"

CONNECTOR_VERSION = "0.2.0"

CONNECTOR_PHASE = "PHASE 2.47 PART 1.00"

CONNECTOR_STATUS = "enterprise_morris_county_tax_board_connector_active"

CONNECTOR_KEY = "nj_morris_tax_board"

CONNECTOR_SOURCE_TYPE = "morris_tax_board"

CONNECTOR_AUTHORITY = "county_tax_board_public_record"

CONNECTOR_JURISDICTION = "Morris County, NJ"

CONNECTOR_RELEASE_CHANNEL = "development"


# ============================================================
# SECTION 03 - GOVERNANCE
# ============================================================

TAX_BOARD_CONNECTOR_GOVERNANCE = {
    "fabricated_tax_records_allowed": False,
    "fabricated_assessment_values_allowed": False,
    "fabricated_owner_references_allowed": False,
    "fabricated_sale_references_allowed": False,
    "fabricated_market_value_allowed": False,
    "assessment_as_market_value_allowed": False,
    "assessment_as_listing_price_allowed": False,
    "assessment_as_appraisal_allowed": False,
    "source_attribution_required": True,
    "manual_review_for_ambiguous_records": True,
    "missing_fields_must_remain_unavailable": True,
    "partial_source_backed_results_allowed": True,
}


SUPPORTED_FIELDS = [
    "tax_year",
    "block",
    "lot",
    "qualifier",
    "municipality",
    "county",
    "state_code",
    "property_class",
    "land_assessment",
    "improvement_assessment",
    "total_assessment",
    "owner_reference",
    "sale_reference",
    "source_attribution",
    "manual_review_flags",
]


UNSUPPORTED_CLAIMS = [
    "current_market_value",
    "active_listing_status",
    "under_contract_status",
    "current_listing_price",
    "appraisal_value",
    "legal_title_opinion",
    "survey_boundary",
]


STANDARD_LIMITATIONS = [
    "Tax assessment is public-record context and is not current market value.",
    "Tax assessment is not a listing price.",
    "Tax assessment is not an appraisal.",
    "Owner reference is public-record context and may require manual review.",
    "Sale reference from tax data is historical context only when source-backed.",
    "Current listing status requires an authorized MLS, RESO, IDX, broker-authorized feed, or listing-provider source.",
]


# ============================================================
# SECTION 04 - REGEX / NORMALIZATION CONSTANTS
# ============================================================

MONEY_RE = re.compile(r"[-+]?\$?\s*([0-9]{1,3}(?:,[0-9]{3})*|[0-9]+)(?:\.[0-9]+)?")

YEAR_RE = re.compile(r"\b(19[0-9]{2}|20[0-9]{2}|21[0-9]{2})\b")

BLOCK_LOT_RE = re.compile(
    r"\b(?:BLOCK|BLK)\s*[:#\-]?\s*(?P<block>[A-Z0-9.\-]+)\b.*?\b(?:LOT|LT)\s*[:#\-]?\s*(?P<lot>[A-Z0-9.\-]+)\b",
    re.IGNORECASE,
)

LOT_BLOCK_RE = re.compile(
    r"\b(?:LOT|LT)\s*[:#\-]?\s*(?P<lot>[A-Z0-9.\-]+)\b.*?\b(?:BLOCK|BLK)\s*[:#\-]?\s*(?P<block>[A-Z0-9.\-]+)\b",
    re.IGNORECASE,
)

QUALIFIER_RE = re.compile(
    r"\b(?:QUALIFIER|QUAL|Q)\s*[:#\-]?\s*(?P<qualifier>[A-Z0-9.\-]+)\b",
    re.IGNORECASE,
)

WHITESPACE_RE = re.compile(r"\s+")


# ============================================================
# SECTION 05 - MORRIS COUNTY MUNICIPALITY HINTS
# ============================================================

MORRIS_COUNTY_MUNICIPALITIES = {
    "BOONTON": "Boonton",
    "BOONTON TOWNSHIP": "Boonton Township",
    "BUTLER": "Butler",
    "CHATHAM": "Chatham",
    "CHATHAM BOROUGH": "Chatham Borough",
    "CHATHAM TOWNSHIP": "Chatham Township",
    "CHESTER": "Chester",
    "CHESTER BOROUGH": "Chester Borough",
    "CHESTER TOWNSHIP": "Chester Township",
    "DENVILLE": "Denville",
    "DOVER": "Dover",
    "EAST HANOVER": "East Hanover",
    "FLORHAM PARK": "Florham Park",
    "HANOVER": "Hanover",
    "HANOVER TOWNSHIP": "Hanover Township",
    "HARDING": "Harding",
    "HARDING TOWNSHIP": "Harding Township",
    "JEFFERSON": "Jefferson",
    "JEFFERSON TOWNSHIP": "Jefferson Township",
    "KINNELON": "Kinnelon",
    "LINCOLN PARK": "Lincoln Park",
    "LONG HILL": "Long Hill",
    "LONG HILL TOWNSHIP": "Long Hill Township",
    "MADISON": "Madison",
    "MENDHAM": "Mendham",
    "MENDHAM BOROUGH": "Mendham Borough",
    "MENDHAM TOWNSHIP": "Mendham Township",
    "MINE HILL": "Mine Hill",
    "MONTVILLE": "Montville",
    "MONTVILLE TOWNSHIP": "Montville Township",
    "MORRIS": "Morris Township",
    "MORRIS TOWNSHIP": "Morris Township",
    "MORRIS PLAINS": "Morris Plains",
    "MORRISTOWN": "Morristown",
    "MOUNT ARLINGTON": "Mount Arlington",
    "MOUNT OLIVE": "Mount Olive",
    "MOUNT OLIVE TOWNSHIP": "Mount Olive Township",
    "MOUNTAIN LAKES": "Mountain Lakes",
    "NETCONG": "Netcong",
    "PARSIPPANY": "Parsippany-Troy Hills",
    "PARSIPPANY TROY HILLS": "Parsippany-Troy Hills",
    "PARSIPPANY-TROY HILLS": "Parsippany-Troy Hills",
    "PASSAIC TOWNSHIP": "Passaic Township",
    "PEQUANNOCK": "Pequannock Township",
    "PEQUANNOCK TOWNSHIP": "Pequannock Township",
    "RANDOLPH": "Randolph",
    "RANDOLPH TOWNSHIP": "Randolph Township",
    "RIVERDALE": "Riverdale",
    "ROCKAWAY": "Rockaway",
    "ROCKAWAY BOROUGH": "Rockaway Borough",
    "ROCKAWAY TOWNSHIP": "Rockaway Township",
    "ROXBURY": "Roxbury Township",
    "ROXBURY TOWNSHIP": "Roxbury Township",
    "VICTORY GARDENS": "Victory Gardens",
    "WASHINGTON": "Washington Township",
    "WASHINGTON TOWNSHIP": "Washington Township",
    "WHARTON": "Wharton",
}


# ============================================================
# SECTION 06 - ENUMERATIONS
# ============================================================

class TaxBoardConnectorStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    SKIPPED = "skipped"
    ERROR = "error"


class TaxBoardFactStatus(StrEnum):
    SOURCE_BACKED = "source_backed"
    INFERRED = "inferred"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    CONFLICTED = "conflicted"


class TaxBoardQueryMode(StrEnum):
    ADDRESS = "address"
    BLOCK_LOT = "block_lot"
    PARCEL_ID = "parcel_id"
    OWNER_REFERENCE = "owner_reference"
    UNKNOWN = "unknown"


class ManualReviewSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================
# SECTION 07 - UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def safe_string(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def normalize_text(value: Any) -> str:
    text = safe_string(value).upper()
    text = WHITESPACE_RE.sub(" ", text).strip()

    return text


def normalize_key(value: Any) -> str:
    text = safe_string(value).lower()
    output: list[str] = []

    for character in text:
        if character.isalnum():
            output.append(character)
        elif output and output[-1] != "_":
            output.append("_")

    return "".join(output).strip("_")


def clean_value(value: Any) -> str | None:
    text = safe_string(value)

    return text or None


def normalize_state(value: Any) -> str | None:
    text = normalize_text(value)

    if not text:
        return None

    if text in {"NJ", "NEW JERSEY"}:
        return "NJ"

    return text


def normalize_county(value: Any) -> str | None:
    text = safe_string(value)

    if not text:
        return None

    text = text.replace("County", "").replace("county", "").strip()

    return text.title()


def normalize_municipality(value: Any) -> str | None:
    text = normalize_text(value)

    if not text:
        return None

    if text in MORRIS_COUNTY_MUNICIPALITIES:
        return MORRIS_COUNTY_MUNICIPALITIES[text]

    return safe_string(value).title()


def normalize_block_lot(value: Any) -> str | None:
    text = normalize_text(value)

    if not text:
        return None

    cleaned = re.sub(r"[^A-Z0-9.\-]", "", text)

    return cleaned or None


def parse_money(value: Any) -> float | None:
    if value in (None, ""):
        return None

    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)

    text = safe_string(value)

    if not text:
        return None

    match = MONEY_RE.search(text)

    if not match:
        return None

    try:
        return float(match.group(1).replace(",", ""))
    except Exception:
        return None


def parse_year(value: Any) -> str | None:
    text = safe_string(value)

    if not text:
        return None

    match = YEAR_RE.search(text)

    if not match:
        return None

    return match.group(1)


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

    if isinstance(value, (datetime, date)):
        return value.isoformat()

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
        full_key = f"{prefix}.{normalize_key(key)}" if prefix else normalize_key(key)

        if isinstance(value, Mapping):
            result.update(flatten_mapping(value, prefix=full_key))
        else:
            result[full_key] = value

    return result


def first_value(payload: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, "", [], {}):
            return payload[key]

    return None


# ============================================================
# SECTION 08 - DATA CONTRACTS
# ============================================================

@dataclass
class TaxBoardRequest:
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
    tax_year: str | None = None
    query_mode: str = TaxBoardQueryMode.UNKNOWN.value
    strict_source_mode: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class TaxBoardSourceReference:
    source_name: str = CONNECTOR_NAME
    source_type: str = CONNECTOR_SOURCE_TYPE
    connector_key: str = CONNECTOR_KEY
    source_authority: str = CONNECTOR_AUTHORITY
    jurisdiction: str = CONNECTOR_JURISDICTION
    record_id: str | None = None
    source_url: str | None = None
    retrieved_at: str = field(default_factory=utc_now)
    field_path: str | None = None
    confidence: float = 0.0
    raw_payload_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class TaxAssessmentRecord:
    tax_year: str | None = None
    block: str | None = None
    lot: str | None = None
    qualifier: str | None = None
    municipality: str | None = None
    county: str | None = "Morris"
    state_code: str | None = "NJ"
    property_class: str | None = None
    land_assessment: float | None = None
    improvement_assessment: float | None = None
    total_assessment: float | None = None
    owner_reference: str | None = None
    sale_date: str | None = None
    sale_price: float | None = None
    deed_book: str | None = None
    deed_page: str | None = None
    document_number: str | None = None
    source_status: str = TaxBoardFactStatus.UNAVAILABLE.value
    confidence: float = 0.0
    manual_review_required: bool = False
    manual_review_reasons: list[str] = field(default_factory=list)
    source: TaxBoardSourceReference = field(default_factory=TaxBoardSourceReference)
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class TaxBoardManualReviewItem:
    code: str
    message: str
    severity: str = ManualReviewSeverity.WARNING.value
    field_path: str | None = None
    required_action: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class TaxBoardConnectorResult:
    success: bool
    status: str
    query_mode: str
    request: TaxBoardRequest
    records: list[dict[str, Any]] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)
    sources: list[TaxBoardSourceReference] = field(default_factory=list)
    manual_review_items: list[TaxBoardManualReviewItem] = field(default_factory=list)
    unavailable_fields: list[dict[str, Any]] = field(default_factory=list)
    unsupported_claims: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    completeness_score: float = 0.0
    source_coverage_score: float = 0.0
    limitations: list[str] = field(default_factory=lambda: list(STANDARD_LIMITATIONS))
    governance: dict[str, Any] = field(default_factory=lambda: TAX_BOARD_CONNECTOR_GOVERNANCE.copy())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = object_to_dict(asdict(self))

        if isinstance(payload.get("facts"), Mapping):
            for key, value in payload["facts"].items():
                payload.setdefault(key, value)

        return payload


# ============================================================
# SECTION 09 - REQUEST NORMALIZER
# ============================================================

class TaxBoardRequestNormalizer:
    def normalize(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> TaxBoardRequest:
        if isinstance(request, TaxBoardRequest):
            normalized = request
        elif isinstance(request, Mapping):
            normalized = self.from_mapping(request)
        elif isinstance(request, str):
            normalized = TaxBoardRequest(
                raw_query=request,
                street_address=request,
                normalized_address=request,
            )
        else:
            normalized = self.from_mapping(kwargs)

        for key, value in kwargs.items():
            if hasattr(normalized, key) and value not in (None, ""):
                setattr(normalized, key, value)

        normalized.state_code = normalize_state(normalized.state_code or normalized.state) or "NJ"
        normalized.state = normalized.state_code
        normalized.county = normalize_county(normalized.county) or "Morris"
        normalized.municipality = normalize_municipality(normalized.municipality)
        normalized.block = normalize_block_lot(normalized.block)
        normalized.lot = normalize_block_lot(normalized.lot)
        normalized.qualifier = normalize_block_lot(normalized.qualifier)
        normalized.tax_year = parse_year(normalized.tax_year)

        self.extract_block_lot_from_query(normalized)
        self.detect_municipality_from_query(normalized)

        if normalized.query_mode == TaxBoardQueryMode.UNKNOWN.value:
            normalized.query_mode = self.detect_query_mode(normalized)

        return normalized

    @staticmethod
    def from_mapping(payload: Mapping[str, Any]) -> TaxBoardRequest:
        return TaxBoardRequest(
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
            tax_year=payload.get("tax_year"),
            query_mode=payload.get("query_mode")
            or payload.get("primary_query_mode")
            or TaxBoardQueryMode.UNKNOWN.value,
            strict_source_mode=bool(payload.get("strict_source_mode", True)),
            metadata=dict(payload.get("metadata") or {}),
        )

    @staticmethod
    def detect_query_mode(request: TaxBoardRequest) -> str:
        if request.block and request.lot:
            return TaxBoardQueryMode.BLOCK_LOT.value

        if request.parcel_id:
            return TaxBoardQueryMode.PARCEL_ID.value

        if request.owner_reference and not (request.street_address or request.raw_query):
            return TaxBoardQueryMode.OWNER_REFERENCE.value

        if request.street_address or request.normalized_address or request.raw_query:
            return TaxBoardQueryMode.ADDRESS.value

        return TaxBoardQueryMode.UNKNOWN.value

    @staticmethod
    def extract_block_lot_from_query(request: TaxBoardRequest) -> None:
        text = " ".join(
            value
            for value in [
                request.raw_query,
                request.street_address,
                request.normalized_address,
            ]
            if value
        )

        if not text:
            return

        match = BLOCK_LOT_RE.search(text) or LOT_BLOCK_RE.search(text)

        if match:
            request.block = request.block or normalize_block_lot(match.group("block"))
            request.lot = request.lot or normalize_block_lot(match.group("lot"))

        qualifier_match = QUALIFIER_RE.search(text)

        if qualifier_match:
            request.qualifier = request.qualifier or normalize_block_lot(
                qualifier_match.group("qualifier")
            )

    @staticmethod
    def detect_municipality_from_query(request: TaxBoardRequest) -> None:
        if request.municipality:
            return

        text = normalize_text(
            " ".join(
                value
                for value in [
                    request.raw_query,
                    request.street_address,
                    request.normalized_address,
                ]
                if value
            )
        )

        best: tuple[int, str] | None = None

        for key, display in MORRIS_COUNTY_MUNICIPALITIES.items():
            if f" {key} " in f" {text} ":
                length = len(key)
                if best is None or length > best[0]:
                    best = (length, display)

        if best:
            request.municipality = best[1]


# ============================================================
# SECTION 10 - SOURCE-BACKED RECORD NORMALIZER
# ============================================================

class TaxBoardRecordNormalizer:
    FIELD_CANDIDATES = {
        "tax_year": [
            "tax_year",
            "year",
            "assessment_year",
            "tax.assessment_year",
            "assessment.tax_year",
        ],
        "block": [
            "block",
            "blk",
            "tax.block",
            "assessment.block",
            "parcel.block",
        ],
        "lot": [
            "lot",
            "lt",
            "tax.lot",
            "assessment.lot",
            "parcel.lot",
        ],
        "qualifier": [
            "qualifier",
            "qual",
            "q",
            "tax.qualifier",
            "assessment.qualifier",
        ],
        "municipality": [
            "municipality",
            "muni",
            "city",
            "town",
            "tax.municipality",
            "assessment.municipality",
        ],
        "property_class": [
            "property_class",
            "class",
            "prop_class",
            "tax.property_class",
            "assessment.property_class",
        ],
        "land_assessment": [
            "land_assessment",
            "land_value",
            "land_assessed_value",
            "tax.land_assessment",
            "assessment.land_assessment",
        ],
        "improvement_assessment": [
            "improvement_assessment",
            "improvement_value",
            "improvements",
            "building_assessment",
            "tax.improvement_assessment",
            "assessment.improvement_assessment",
        ],
        "total_assessment": [
            "total_assessment",
            "assessed_value",
            "total_assessed_value",
            "tax.total_assessment",
            "assessment.total_assessment",
        ],
        "owner_reference": [
            "owner",
            "owner_name",
            "owner_reference",
            "tax.owner",
            "assessment.owner",
        ],
        "sale_date": [
            "sale_date",
            "last_sale_date",
            "deed_date",
            "tax.sale_date",
        ],
        "sale_price": [
            "sale_price",
            "last_sale_price",
            "consideration",
            "tax.sale_price",
        ],
        "deed_book": [
            "deed_book",
            "book",
            "sale_book",
        ],
        "deed_page": [
            "deed_page",
            "page",
            "sale_page",
        ],
        "document_number": [
            "document_number",
            "instrument_number",
            "doc_number",
            "id",
        ],
    }

    def normalize_record(
        self,
        record_payload: Mapping[str, Any],
        *,
        request: TaxBoardRequest,
        source: TaxBoardSourceReference | None = None,
    ) -> TaxAssessmentRecord:
        flattened = flatten_mapping(record_payload)

        tax_year = parse_year(self.extract(flattened, "tax_year")) or request.tax_year
        block = normalize_block_lot(self.extract(flattened, "block") or request.block)
        lot = normalize_block_lot(self.extract(flattened, "lot") or request.lot)
        qualifier = normalize_block_lot(
            self.extract(flattened, "qualifier") or request.qualifier
        )
        municipality = normalize_municipality(
            self.extract(flattened, "municipality") or request.municipality
        )
        property_class = clean_value(self.extract(flattened, "property_class"))
        land_assessment = parse_money(self.extract(flattened, "land_assessment"))
        improvement_assessment = parse_money(
            self.extract(flattened, "improvement_assessment")
        )
        total_assessment = parse_money(self.extract(flattened, "total_assessment"))
        owner_reference = clean_value(self.extract(flattened, "owner_reference"))
        sale_date = clean_value(self.extract(flattened, "sale_date"))
        sale_price = parse_money(self.extract(flattened, "sale_price"))
        deed_book = clean_value(self.extract(flattened, "deed_book"))
        deed_page = clean_value(self.extract(flattened, "deed_page"))
        document_number = clean_value(self.extract(flattened, "document_number"))

        source = source or TaxBoardSourceReference(
            confidence=0.0,
            raw_payload_hash=stable_hash(record_payload),
        )

        confidence = self.score_record(
            tax_year=tax_year,
            block=block,
            lot=lot,
            municipality=municipality,
            property_class=property_class,
            land_assessment=land_assessment,
            improvement_assessment=improvement_assessment,
            total_assessment=total_assessment,
            owner_reference=owner_reference,
            sale_date=sale_date,
            sale_price=sale_price,
        )

        manual_review_reasons = self.manual_review_reasons(
            tax_year=tax_year,
            block=block,
            lot=lot,
            municipality=municipality,
            total_assessment=total_assessment,
            record_payload=record_payload,
        )

        status_value = (
            TaxBoardFactStatus.SOURCE_BACKED.value
            if confidence > 0
            else TaxBoardFactStatus.UNAVAILABLE.value
        )

        if manual_review_reasons and confidence > 0:
            status_value = TaxBoardFactStatus.MANUAL_REVIEW_REQUIRED.value

        source.confidence = confidence
        source.raw_payload_hash = stable_hash(record_payload)

        return TaxAssessmentRecord(
            tax_year=tax_year,
            block=block,
            lot=lot,
            qualifier=qualifier,
            municipality=municipality,
            county="Morris",
            state_code="NJ",
            property_class=property_class,
            land_assessment=land_assessment,
            improvement_assessment=improvement_assessment,
            total_assessment=total_assessment,
            owner_reference=owner_reference,
            sale_date=sale_date,
            sale_price=sale_price,
            deed_book=deed_book,
            deed_page=deed_page,
            document_number=document_number,
            source_status=status_value,
            confidence=confidence,
            manual_review_required=bool(manual_review_reasons),
            manual_review_reasons=manual_review_reasons,
            source=source,
            raw_payload=dict(record_payload),
        )

    def normalize_records(
        self,
        records: Sequence[Mapping[str, Any]],
        *,
        request: TaxBoardRequest,
    ) -> list[TaxAssessmentRecord]:
        normalized: list[TaxAssessmentRecord] = []

        for index, record in enumerate(records):
            source = TaxBoardSourceReference(
                record_id=clean_value(
                    record.get("record_id")
                    or record.get("id")
                    or f"tax-board-record-{index + 1}"
                ),
                field_path="tax_assessment_context",
                confidence=0.0,
                raw_payload_hash=stable_hash(record),
                metadata={
                    "record_index": index,
                },
            )
            normalized.append(
                self.normalize_record(
                    record,
                    request=request,
                    source=source,
                )
            )

        return normalized

    def extract(self, flattened: Mapping[str, Any], field_name: str) -> Any:
        return first_value(flattened, self.FIELD_CANDIDATES.get(field_name, []))

    @staticmethod
    def score_record(
        *,
        tax_year: str | None,
        block: str | None,
        lot: str | None,
        municipality: str | None,
        property_class: str | None,
        land_assessment: float | None,
        improvement_assessment: float | None,
        total_assessment: float | None,
        owner_reference: str | None,
        sale_date: str | None,
        sale_price: float | None,
    ) -> float:
        score = 0.0

        if tax_year:
            score += 0.10

        if block:
            score += 0.12

        if lot:
            score += 0.12

        if municipality:
            score += 0.10

        if property_class:
            score += 0.08

        if land_assessment is not None:
            score += 0.12

        if improvement_assessment is not None:
            score += 0.12

        if total_assessment is not None:
            score += 0.16

        if owner_reference:
            score += 0.05

        if sale_date or sale_price is not None:
            score += 0.03

        return round(clamp_score(score), 6)

    @staticmethod
    def manual_review_reasons(
        *,
        tax_year: str | None,
        block: str | None,
        lot: str | None,
        municipality: str | None,
        total_assessment: float | None,
        record_payload: Mapping[str, Any],
    ) -> list[str]:
        reasons: list[str] = []

        if not tax_year:
            reasons.append("tax_year_missing")

        if not block:
            reasons.append("block_missing")

        if not lot:
            reasons.append("lot_missing")

        if not municipality:
            reasons.append("municipality_missing")

        if total_assessment is None:
            reasons.append("total_assessment_missing")

        if record_payload.get("conflict") or record_payload.get("conflicted"):
            reasons.append("source_payload_marked_conflicted")

        return reasons


# ============================================================
# SECTION 11 - RAW SOURCE CLIENT PLACEHOLDER
# ============================================================

class MorrisTaxBoardSourceClient:
    """
    Source client abstraction.

    This class intentionally does not scrape or fabricate records.
    Future approved integrations can inject a client with source-backed
    data retrieval. The default client returns unavailable.
    """

    def search(
        self,
        request: TaxBoardRequest,
    ) -> dict[str, Any]:
        return {
            "success": False,
            "status": TaxBoardConnectorStatus.UNAVAILABLE.value,
            "records": [],
            "facts": {},
            "warnings": [
                "No live Morris County tax-board source client is configured."
            ],
            "errors": [],
            "metadata": {
                "client": self.__class__.__name__,
                "generated_at": utc_now(),
                "no_fabrication": True,
            },
        }


# ============================================================
# SECTION 12 - RESULT BUILDER
# ============================================================

class TaxBoardResultBuilder:
    def build(
        self,
        *,
        request: TaxBoardRequest,
        records: Sequence[TaxAssessmentRecord],
        warnings: Sequence[str] | None = None,
        errors: Sequence[Mapping[str, Any]] | None = None,
        raw_payload: Mapping[str, Any] | None = None,
    ) -> TaxBoardConnectorResult:
        warnings_list = list(warnings or [])
        errors_list = [dict(error) for error in errors or []]
        records_list = [record.to_dict() for record in records]
        facts = self.build_facts(records)
        sources = self.deduplicate_sources([record.source for record in records])
        manual_review_items = self.build_manual_review_items(request, records)
        unavailable_fields = self.build_unavailable_fields(facts)
        unsupported_claims = self.build_unsupported_claims()
        completeness_score = self.score_completeness(facts)
        source_coverage_score = self.score_source_coverage(facts, sources)
        confidence = self.score_confidence(
            records=records,
            completeness_score=completeness_score,
            source_coverage_score=source_coverage_score,
            manual_review_items=manual_review_items,
            errors=errors_list,
        )

        if errors_list and not records:
            status_value = TaxBoardConnectorStatus.ERROR.value
        elif records and manual_review_items:
            status_value = TaxBoardConnectorStatus.PARTIAL.value
        elif records:
            status_value = TaxBoardConnectorStatus.SUCCESS.value
        else:
            status_value = TaxBoardConnectorStatus.PARTIAL.value

        success = status_value in {
            TaxBoardConnectorStatus.SUCCESS.value,
            TaxBoardConnectorStatus.PARTIAL.value,
        }

        if not records:
            warnings_list.append(
                "No source-backed Morris County tax assessment records were returned."
            )

        return TaxBoardConnectorResult(
            success=success,
            status=status_value,
            query_mode=request.query_mode,
            request=request,
            records=records_list,
            facts=facts,
            sources=sources,
            manual_review_items=manual_review_items,
            unavailable_fields=unavailable_fields,
            unsupported_claims=unsupported_claims,
            warnings=list(dict.fromkeys([warning for warning in warnings_list if warning])),
            errors=errors_list,
            confidence=confidence,
            completeness_score=completeness_score,
            source_coverage_score=source_coverage_score,
            metadata={
                "connector": CONNECTOR_NAME,
                "version": CONNECTOR_VERSION,
                "phase": CONNECTOR_PHASE,
                "generated_at": utc_now(),
                "record_count": len(records),
                "raw_payload_hash": stable_hash(raw_payload or {}),
            },
        )

    def build_facts(
        self,
        records: Sequence[TaxAssessmentRecord],
    ) -> dict[str, Any]:
        best = self.select_best_record(records)

        if best is None:
            return self.empty_facts()

        return {
            "parcel_identity": {
                "block": best.block,
                "lot": best.lot,
                "qualifier": best.qualifier,
                "municipality": best.municipality,
                "county": best.county,
                "state_code": best.state_code,
                "property_class": best.property_class,
                "source_status": best.source_status,
                "confidence": best.confidence,
            },
            "tax_assessment_context": {
                "tax_year": best.tax_year,
                "land_assessment": best.land_assessment,
                "improvement_assessment": best.improvement_assessment,
                "total_assessment": best.total_assessment,
                "property_class": best.property_class,
                "assessment_source_note": (
                    "Tax assessment is public-record context and is not current market value."
                ),
                "source_status": best.source_status,
                "confidence": best.confidence,
            },
            "property_tax_context": {
                "tax_year": best.tax_year,
                "tax_amount": None,
                "tax_rate": None,
                "estimated_annual_tax": None,
                "source_status": TaxBoardFactStatus.UNAVAILABLE.value,
                "confidence": 0.0,
            },
            "owner_references": (
                [
                    {
                        "owner_name": best.owner_reference,
                        "mailing_address": None,
                        "owner_source_note": (
                            "Owner reference is public-record context and may require manual review."
                        ),
                        "source_status": best.source_status,
                        "confidence": min(best.confidence, 0.62),
                    }
                ]
                if best.owner_reference
                else []
            ),
            "sale_history_references": (
                [
                    {
                        "sale_date": best.sale_date,
                        "sale_price": best.sale_price,
                        "deed_book": best.deed_book,
                        "deed_page": best.deed_page,
                        "document_number": best.document_number,
                        "source_status": best.source_status,
                        "confidence": min(best.confidence, 0.60),
                    }
                ]
                if best.sale_date or best.sale_price is not None
                else []
            ),
        }

    @staticmethod
    def empty_facts() -> dict[str, Any]:
        return {
            "parcel_identity": {
                "block": None,
                "lot": None,
                "qualifier": None,
                "municipality": None,
                "county": "Morris",
                "state_code": "NJ",
                "property_class": None,
                "source_status": TaxBoardFactStatus.UNAVAILABLE.value,
                "confidence": 0.0,
            },
            "tax_assessment_context": {
                "tax_year": None,
                "land_assessment": None,
                "improvement_assessment": None,
                "total_assessment": None,
                "property_class": None,
                "assessment_source_note": (
                    "Tax assessment is public-record context and is not current market value."
                ),
                "source_status": TaxBoardFactStatus.UNAVAILABLE.value,
                "confidence": 0.0,
            },
            "property_tax_context": {
                "tax_year": None,
                "tax_amount": None,
                "tax_rate": None,
                "estimated_annual_tax": None,
                "source_status": TaxBoardFactStatus.UNAVAILABLE.value,
                "confidence": 0.0,
            },
            "owner_references": [],
            "sale_history_references": [],
        }

    @staticmethod
    def select_best_record(
        records: Sequence[TaxAssessmentRecord],
    ) -> TaxAssessmentRecord | None:
        if not records:
            return None

        return sorted(
            records,
            key=lambda item: (
                item.confidence,
                int(item.tax_year or 0) if item.tax_year else 0,
            ),
            reverse=True,
        )[0]

    @staticmethod
    def deduplicate_sources(
        sources: Sequence[TaxBoardSourceReference],
    ) -> list[TaxBoardSourceReference]:
        seen: set[str] = set()
        output: list[TaxBoardSourceReference] = []

        for source in sources:
            key = stable_hash(source.to_dict())

            if key in seen:
                continue

            seen.add(key)
            output.append(source)

        return output

    @staticmethod
    def build_manual_review_items(
        request: TaxBoardRequest,
        records: Sequence[TaxAssessmentRecord],
    ) -> list[TaxBoardManualReviewItem]:
        items: list[TaxBoardManualReviewItem] = []

        if request.query_mode == TaxBoardQueryMode.UNKNOWN.value:
            items.append(
                TaxBoardManualReviewItem(
                    code="unknown_tax_board_query_mode",
                    message="Tax-board query mode could not be determined.",
                    field_path="request.query_mode",
                    required_action="Provide address, block/lot, parcel ID, or owner reference.",
                )
            )

        if request.county != "Morris" or request.state_code != "NJ":
            items.append(
                TaxBoardManualReviewItem(
                    code="outside_morris_county_scope",
                    message="Morris County tax-board connector received an out-of-scope request.",
                    field_path="request.county",
                    required_action="Route non-Morris requests to the proper county/state connector.",
                )
            )

        if not records:
            items.append(
                TaxBoardManualReviewItem(
                    code="no_source_backed_tax_records",
                    message="No source-backed tax assessment records were returned.",
                    field_path="records",
                    required_action="Connect approved tax-board source client or manually verify public record.",
                )
            )

        for record in records:
            for reason in record.manual_review_reasons:
                items.append(
                    TaxBoardManualReviewItem(
                        code=reason,
                        message=f"Tax assessment record requires review: {reason}.",
                        field_path="tax_assessment_context",
                        required_action="Verify tax-board source record before relying on this field.",
                        metadata={
                            "record_hash": stable_hash(record.to_dict()),
                        },
                    )
                )

        return items

    @staticmethod
    def build_unavailable_fields(
        facts: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        unavailable: list[dict[str, Any]] = []

        for section_name, section_payload in facts.items():
            if isinstance(section_payload, Mapping):
                for field_name, value in section_payload.items():
                    if field_name in {"source_status", "confidence", "assessment_source_note"}:
                        continue

                    if value in (None, "", [], {}):
                        unavailable.append(
                            {
                                "field_name": field_name,
                                "field_path": f"{section_name}.{field_name}",
                                "reason": (
                                    f"{section_name}.{field_name} is unavailable from current Morris County tax-board source data."
                                ),
                                "required_source": "morris_county_tax_board_public_record",
                                "can_public_records_support": True,
                                "manual_review_required": False,
                            }
                        )

            if isinstance(section_payload, list) and not section_payload:
                unavailable.append(
                    {
                        "field_name": section_name,
                        "field_path": section_name,
                        "reason": (
                            f"{section_name} is unavailable from current Morris County tax-board source data."
                        ),
                        "required_source": "morris_county_tax_board_public_record",
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
                "status": TaxBoardFactStatus.UNSUPPORTED.value,
                "reason": (
                    "Morris County tax-board assessment data cannot prove this claim."
                ),
                "required_source": (
                    "valuation_engine_and_comparable_sales"
                    if "market_value" in claim or "appraisal" in claim
                    else "authorized_listing_feed_or_legal_source"
                ),
            }
            for claim in UNSUPPORTED_CLAIMS
        ]

    @staticmethod
    def score_completeness(facts: Mapping[str, Any]) -> float:
        values: list[Any] = []

        for section_payload in facts.values():
            if isinstance(section_payload, Mapping):
                for key, value in section_payload.items():
                    if key in {"source_status", "confidence", "assessment_source_note"}:
                        continue
                    values.append(value)
            elif isinstance(section_payload, list):
                values.append(section_payload)

        if not values:
            return 0.0

        present = [
            value
            for value in values
            if value not in (None, "", [], {})
        ]

        return round(clamp_score(len(present) / len(values)), 6)

    @staticmethod
    def score_source_coverage(
        facts: Mapping[str, Any],
        sources: Sequence[TaxBoardSourceReference],
    ) -> float:
        if not sources:
            return 0.0

        source_scores = [
            source.confidence
            for source in sources
        ]

        return round(clamp_score(sum(source_scores) / len(source_scores)), 6)

    @staticmethod
    def score_confidence(
        *,
        records: Sequence[TaxAssessmentRecord],
        completeness_score: float,
        source_coverage_score: float,
        manual_review_items: Sequence[TaxBoardManualReviewItem],
        errors: Sequence[Mapping[str, Any]],
    ) -> float:
        record_score = 0.0

        if records:
            record_score = sum(record.confidence for record in records) / len(records)

        review_penalty = min(len(manual_review_items) * 0.04, 0.35)
        error_penalty = min(len(errors) * 0.08, 0.40)

        score = (
            record_score * 0.45
            + completeness_score * 0.30
            + source_coverage_score * 0.25
            - review_penalty
            - error_penalty
        )

        return round(clamp_score(score), 6)


# ============================================================
# SECTION 13 - ENTERPRISE CONNECTOR
# ============================================================

class NJMorrisTaxBoardConnector:
    def __init__(
        self,
        *,
        source_client: MorrisTaxBoardSourceClient | None = None,
        normalizer: TaxBoardRequestNormalizer | None = None,
        record_normalizer: TaxBoardRecordNormalizer | None = None,
        result_builder: TaxBoardResultBuilder | None = None,
    ) -> None:
        self.source_client = source_client or MorrisTaxBoardSourceClient()
        self.normalizer = normalizer or TaxBoardRequestNormalizer()
        self.record_normalizer = record_normalizer or TaxBoardRecordNormalizer()
        self.result_builder = result_builder or TaxBoardResultBuilder()

    def collect(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        normalized_request = self.normalizer.normalize(request, **kwargs)

        if normalized_request.state_code != "NJ" or normalized_request.county != "Morris":
            result = self.result_builder.build(
                request=normalized_request,
                records=[],
                warnings=[
                    "Request is outside Morris County, NJ scope for this connector."
                ],
                errors=[],
                raw_payload={},
            )
            result.status = TaxBoardConnectorStatus.SKIPPED.value
            result.success = True

            return result.to_dict()

        try:
            raw_payload = self.source_client.search(normalized_request)
            raw_records = self.extract_raw_records(raw_payload)

            normalized_records = self.record_normalizer.normalize_records(
                raw_records,
                request=normalized_request,
            )

            warnings = list(raw_payload.get("warnings") or [])
            errors = list(raw_payload.get("errors") or [])

            return self.result_builder.build(
                request=normalized_request,
                records=normalized_records,
                warnings=warnings,
                errors=errors,
                raw_payload=raw_payload,
            ).to_dict()

        except Exception as exc:
            return self.result_builder.build(
                request=normalized_request,
                records=[],
                warnings=[],
                errors=[
                    {
                        "code": "tax_board_connector_error",
                        "message": f"{type(exc).__name__}: {exc}",
                        "traceback": traceback.format_exc(),
                    }
                ],
                raw_payload={},
            ).to_dict()

    def search(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def lookup(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def lookup_property(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def search_public_records(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def run(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    def execute(
        self,
        request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.collect(request, **kwargs)

    @staticmethod
    def extract_raw_records(raw_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
        records = raw_payload.get("records")

        if isinstance(records, list):
            return [
                dict(record)
                for record in records
                if isinstance(record, Mapping)
            ]

        data = raw_payload.get("data")

        if isinstance(data, list):
            return [
                dict(record)
                for record in data
                if isinstance(record, Mapping)
            ]

        if isinstance(data, Mapping):
            return [dict(data)]

        facts = raw_payload.get("facts")

        if isinstance(facts, Mapping):
            return [dict(facts)]

        return []


# Backward-compatible aliases expected by the orchestration engine.
MorrisTaxBoardConnector = NJMorrisTaxBoardConnector
TaxBoardConnector = NJMorrisTaxBoardConnector
PublicRecordConnector = NJMorrisTaxBoardConnector


# ============================================================
# SECTION 14 - CONVENIENCE API
# ============================================================

_default_connector = NJMorrisTaxBoardConnector()


def get_connector() -> NJMorrisTaxBoardConnector:
    return NJMorrisTaxBoardConnector()


def collect_tax_board_records(
    request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return _default_connector.collect(request, **kwargs)


def search_tax_board_records(
    request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return _default_connector.search(request, **kwargs)


def lookup_tax_board_property(
    request: TaxBoardRequest | Mapping[str, Any] | str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return _default_connector.lookup_property(request, **kwargs)


# ============================================================
# SECTION 15 - HEALTH / READINESS / DIAGNOSTICS
# ============================================================

def validate_tax_board_connector_governance() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    false_keys = [
        "fabricated_tax_records_allowed",
        "fabricated_assessment_values_allowed",
        "fabricated_owner_references_allowed",
        "fabricated_sale_references_allowed",
        "fabricated_market_value_allowed",
        "assessment_as_market_value_allowed",
        "assessment_as_listing_price_allowed",
        "assessment_as_appraisal_allowed",
    ]

    for key in false_keys:
        if TAX_BOARD_CONNECTOR_GOVERNANCE.get(key):
            issues.append(
                {
                    "issue_code": f"{key}_must_remain_false",
                    "severity": "critical",
                    "message": f"{key} must remain False.",
                }
            )

    true_keys = [
        "source_attribution_required",
        "manual_review_for_ambiguous_records",
        "missing_fields_must_remain_unavailable",
        "partial_source_backed_results_allowed",
    ]

    for key in true_keys:
        if not TAX_BOARD_CONNECTOR_GOVERNANCE.get(key):
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


def get_tax_board_connector_metadata() -> dict[str, Any]:
    return {
        "name": CONNECTOR_NAME,
        "version": CONNECTOR_VERSION,
        "phase": CONNECTOR_PHASE,
        "status": CONNECTOR_STATUS,
        "connector_key": CONNECTOR_KEY,
        "source_type": CONNECTOR_SOURCE_TYPE,
        "authority": CONNECTOR_AUTHORITY,
        "jurisdiction": CONNECTOR_JURISDICTION,
        "release_channel": CONNECTOR_RELEASE_CHANNEL,
        "generated_at": utc_now(),
    }


def get_tax_board_connector_health() -> dict[str, Any]:
    governance = validate_tax_board_connector_governance()
    sample = collect_tax_board_records(
        {
            "raw_query": "43 Wetmore Ave, Morristown, NJ 07960",
            "municipality": "Morristown",
            "county": "Morris",
            "state_code": "NJ",
        }
    )

    return {
        "name": CONNECTOR_NAME,
        "version": CONNECTOR_VERSION,
        "phase": CONNECTOR_PHASE,
        "status": CONNECTOR_STATUS,
        "governance_valid": governance["valid"],
        "governance_issue_count": governance["issue_count"],
        "sample_status": sample.get("status"),
        "sample_success": sample.get("success"),
        "sample_confidence": sample.get("confidence"),
        "source_client": _default_connector.source_client.__class__.__name__,
        "live_source_client_configured": not isinstance(
            _default_connector.source_client,
            MorrisTaxBoardSourceClient,
        ),
        "fabricated_tax_records_allowed": False,
        "assessment_as_market_value_allowed": False,
        "generated_at": utc_now(),
    }


def get_tax_board_connector_readiness() -> dict[str, Any]:
    health = get_tax_board_connector_health()

    required = {
        "governance_valid": health["governance_valid"],
        "connector_importable": True,
    }

    optional = {
        "live_source_client_configured": health["live_source_client_configured"],
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
            "app/public_records/connectors/nj_morris_gis_connector.py",
            "app/property_intelligence/valuation_engine.py",
            "app/static/js/dashboard.js",
        ],
        "generated_at": utc_now(),
    }


def get_tax_board_connector_diagnostics() -> dict[str, Any]:
    return {
        "metadata": get_tax_board_connector_metadata(),
        "health": get_tax_board_connector_health(),
        "readiness": get_tax_board_connector_readiness(),
        "governance": TAX_BOARD_CONNECTOR_GOVERNANCE.copy(),
        "governance_validation": validate_tax_board_connector_governance(),
        "supported_fields": SUPPORTED_FIELDS,
        "unsupported_claims": UNSUPPORTED_CLAIMS,
        "standard_limitations": STANDARD_LIMITATIONS,
        "municipality_hint_count": len(MORRIS_COUNTY_MUNICIPALITIES),
        "exports": __all__,
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 16 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "CONNECTOR_NAME",
    "CONNECTOR_VERSION",
    "CONNECTOR_PHASE",
    "CONNECTOR_STATUS",
    "CONNECTOR_KEY",
    "CONNECTOR_SOURCE_TYPE",
    "CONNECTOR_AUTHORITY",
    "CONNECTOR_JURISDICTION",
    "CONNECTOR_RELEASE_CHANNEL",
    "TAX_BOARD_CONNECTOR_GOVERNANCE",
    "SUPPORTED_FIELDS",
    "UNSUPPORTED_CLAIMS",
    "STANDARD_LIMITATIONS",
    "MORRIS_COUNTY_MUNICIPALITIES",
    "TaxBoardConnectorStatus",
    "TaxBoardFactStatus",
    "TaxBoardQueryMode",
    "ManualReviewSeverity",
    "TaxBoardRequest",
    "TaxBoardSourceReference",
    "TaxAssessmentRecord",
    "TaxBoardManualReviewItem",
    "TaxBoardConnectorResult",
    "TaxBoardRequestNormalizer",
    "TaxBoardRecordNormalizer",
    "MorrisTaxBoardSourceClient",
    "TaxBoardResultBuilder",
    "NJMorrisTaxBoardConnector",
    "MorrisTaxBoardConnector",
    "TaxBoardConnector",
    "PublicRecordConnector",
    "get_connector",
    "collect_tax_board_records",
    "search_tax_board_records",
    "lookup_tax_board_property",
    "validate_tax_board_connector_governance",
    "get_tax_board_connector_metadata",
    "get_tax_board_connector_health",
    "get_tax_board_connector_readiness",
    "get_tax_board_connector_diagnostics",
]


# ============================================================
# END OF FILE
# ============================================================