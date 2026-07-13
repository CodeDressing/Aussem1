# ============================================================
# AUSSEM1
# PHASE 2.41 PART 1.00
# ENTERPRISE ADDRESS INTELLIGENCE ENGINE
# FILE: app/property_intelligence/address_intelligence.py
# PURPOSE:
# Convert a user-entered property address, block/lot signal, owner
# reference, or location-style query into a clean, normalized,
# confidence-scored, public-record-ready property search request.
#
# This engine provides:
# - deterministic address parsing
# - municipality detection
# - county detection
# - state detection
# - ZIP detection
# - block / lot / qualifier detection
# - Morris County routing
# - New Jersey routing
# - public-record search preparation
# - address confidence scoring
# - ambiguous-address manual-review flags
# - property-intelligence request generation
# - stable address fingerprints
# - safe no-network operation
#
# CORE GOVERNANCE:
# - No mock property facts.
# - No fabricated property values.
# - No fabricated listing status.
# - No fabricated owner conclusions.
# - No fabricated sale history.
# - Address intelligence prepares source-backed lookup.
# - It does not claim public-record facts by itself.
# - It does not estimate market value by itself.
# - It does not claim active listing status.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# ENTERPRISE ADDRESS INTELLIGENCE ENGINE ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from enum import StrEnum
from typing import Any
from typing import Iterable
from typing import Mapping
from typing import Sequence


# ============================================================
# SECTION 02 - MODULE METADATA
# ============================================================

ADDRESS_INTELLIGENCE_ENGINE_NAME = (
    "Aussem1 Enterprise Address Intelligence Engine"
)

ADDRESS_INTELLIGENCE_ENGINE_VERSION = "0.2.0"

ADDRESS_INTELLIGENCE_ENGINE_PHASE = "PHASE 2.41 PART 1.00"

ADDRESS_INTELLIGENCE_ENGINE_STATUS = (
    "enterprise_address_intelligence_engine_active"
)

ADDRESS_INTELLIGENCE_RELEASE_CHANNEL = "development"


# ============================================================
# SECTION 03 - GOVERNANCE
# ============================================================

ADDRESS_INTELLIGENCE_GOVERNANCE = {
    "mock_property_facts_allowed": False,
    "fabricated_property_values_allowed": False,
    "fabricated_listing_status_allowed": False,
    "fabricated_owner_conclusions_allowed": False,
    "fabricated_sale_history_allowed": False,
    "network_required": False,
    "address_intelligence_can_estimate_value": False,
    "address_intelligence_can_claim_listing_status": False,
    "address_intelligence_can_claim_public_records": False,
    "address_intelligence_can_prepare_public_record_search": True,
    "manual_review_for_ambiguous_input": True,
    "manual_review_for_missing_search_signal": True,
    "source_attribution_required_downstream": True,
}


# ============================================================
# SECTION 04 - REGEX CONSTANTS
# ============================================================

WHITESPACE_RE = re.compile(r"\s+")

NON_ADDRESS_TEXT_RE = re.compile(r"[^A-Z0-9#&/\-., ]+")

ZIP_RE = re.compile(
    r"(?P<zip5>\b\d{5}\b)(?:[-\s]?(?P<zip4>\d{4}))?"
)

STATE_ZIP_RE = re.compile(
    r"\b(?P<state>[A-Z]{2})\s+(?P<zip>\d{5}(?:-\d{4})?)\b"
)

HOUSE_NUMBER_RE = re.compile(
    r"^(?P<number>\d+[A-Z]?(?:-\d+[A-Z]?)?)(?:\s+|$)",
    re.IGNORECASE,
)

UNIT_RE = re.compile(
    r"(?:\s|,)+(?:APT|APARTMENT|UNIT|STE|SUITE|#|FL|FLOOR|BLDG|BUILDING)\s*([A-Z0-9\-]+)\s*$",
    re.IGNORECASE,
)

PO_BOX_RE = re.compile(
    r"^(?:P(?:OST)?\.?\s*O(?:FFICE)?\.?\s+BOX|PO\s+BOX)\s+([A-Z0-9\-]+)$",
    re.IGNORECASE,
)

RURAL_ROUTE_RE = re.compile(
    r"^(?:RR|RURAL\s+ROUTE)\s*([A-Z0-9\-]+)\s+(?:BOX\s*)?([A-Z0-9\-]+)$",
    re.IGNORECASE,
)

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

MUNICIPALITY_HINT_RE = re.compile(
    r"\b(?:BOROUGH|TOWNSHIP|TWP|TOWN|CITY|VILLAGE)\b",
    re.IGNORECASE,
)


# ============================================================
# SECTION 05 - NEW JERSEY / MORRIS COUNTY CONTEXT
# ============================================================

DEFAULT_COUNTRY_CODE = "US"

DEFAULT_STATE_CODE = "NJ"

DEFAULT_COUNTY = "Morris"

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
    "PASSAIC": "Passaic Township",
    "PASSAIC TOWNSHIP": "Passaic Township",
    "PEQUANNOCK": "Pequannock",
    "PEQUANNOCK TOWNSHIP": "Pequannock Township",
    "RANDOLPH": "Randolph",
    "RANDOLPH TOWNSHIP": "Randolph Township",
    "RIVERDALE": "Riverdale",
    "ROCKAWAY": "Rockaway",
    "ROCKAWAY BOROUGH": "Rockaway Borough",
    "ROCKAWAY TOWNSHIP": "Rockaway Township",
    "ROXBURY": "Roxbury",
    "ROXBURY TOWNSHIP": "Roxbury Township",
    "VICTORY GARDENS": "Victory Gardens",
    "WASHINGTON": "Washington Township",
    "WASHINGTON TOWNSHIP": "Washington Township",
    "WHARTON": "Wharton",
}

MORRIS_COUNTY_ZIP_HINTS = {
    "07005",
    "07034",
    "07035",
    "07045",
    "07046",
    "07054",
    "07058",
    "07082",
    "07405",
    "07435",
    "07801",
    "07803",
    "07828",
    "07834",
    "07836",
    "07840",
    "07842",
    "07845",
    "07847",
    "07849",
    "07850",
    "07852",
    "07853",
    "07856",
    "07857",
    "07866",
    "07869",
    "07876",
    "07878",
    "07885",
    "07920",
    "07924",
    "07926",
    "07927",
    "07928",
    "07930",
    "07932",
    "07933",
    "07935",
    "07936",
    "07940",
    "07945",
    "07946",
    "07950",
    "07960",
    "07970",
    "07976",
    "07980",
    "07981",
}

STATE_NAME_TO_CODE = {
    "ALABAMA": "AL",
    "ALASKA": "AK",
    "ARIZONA": "AZ",
    "ARKANSAS": "AR",
    "CALIFORNIA": "CA",
    "COLORADO": "CO",
    "CONNECTICUT": "CT",
    "DELAWARE": "DE",
    "DISTRICT OF COLUMBIA": "DC",
    "FLORIDA": "FL",
    "GEORGIA": "GA",
    "HAWAII": "HI",
    "IDAHO": "ID",
    "ILLINOIS": "IL",
    "INDIANA": "IN",
    "IOWA": "IA",
    "KANSAS": "KS",
    "KENTUCKY": "KY",
    "LOUISIANA": "LA",
    "MAINE": "ME",
    "MARYLAND": "MD",
    "MASSACHUSETTS": "MA",
    "MICHIGAN": "MI",
    "MINNESOTA": "MN",
    "MISSISSIPPI": "MS",
    "MISSOURI": "MO",
    "MONTANA": "MT",
    "NEBRASKA": "NE",
    "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH",
    "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM",
    "NEW YORK": "NY",
    "NORTH CAROLINA": "NC",
    "NORTH DAKOTA": "ND",
    "OHIO": "OH",
    "OKLAHOMA": "OK",
    "OREGON": "OR",
    "PENNSYLVANIA": "PA",
    "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD",
    "TENNESSEE": "TN",
    "TEXAS": "TX",
    "UTAH": "UT",
    "VERMONT": "VT",
    "VIRGINIA": "VA",
    "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV",
    "WISCONSIN": "WI",
    "WYOMING": "WY",
}

VALID_STATE_CODES = set(STATE_NAME_TO_CODE.values())


# ============================================================
# SECTION 06 - NORMALIZATION TABLES
# ============================================================

STREET_SUFFIXES = {
    "AV": "AVE",
    "AVE": "AVE",
    "AVENUE": "AVE",
    "BLVD": "BLVD",
    "BOULEVARD": "BLVD",
    "CIR": "CIR",
    "CIRCLE": "CIR",
    "CT": "CT",
    "COURT": "CT",
    "DR": "DR",
    "DRIVE": "DR",
    "HWY": "HWY",
    "HIGHWAY": "HWY",
    "LANE": "LN",
    "LN": "LN",
    "PL": "PL",
    "PLACE": "PL",
    "PKWY": "PKWY",
    "PARKWAY": "PKWY",
    "RD": "RD",
    "ROAD": "RD",
    "ST": "ST",
    "STREET": "ST",
    "TER": "TER",
    "TERRACE": "TER",
    "TRL": "TRL",
    "TRAIL": "TRL",
    "WAY": "WAY",
    "WY": "WAY",
}

DIRECTIONALS = {
    "N": "N",
    "NORTH": "N",
    "S": "S",
    "SOUTH": "S",
    "E": "E",
    "EAST": "E",
    "W": "W",
    "WEST": "W",
    "NE": "NE",
    "NORTHEAST": "NE",
    "NW": "NW",
    "NORTHWEST": "NW",
    "SE": "SE",
    "SOUTHEAST": "SE",
    "SW": "SW",
    "SOUTHWEST": "SW",
}

UNIT_DESIGNATORS = {
    "APARTMENT": "APT",
    "APT": "APT",
    "BUILDING": "BLDG",
    "BLDG": "BLDG",
    "FLOOR": "FL",
    "FL": "FL",
    "SUITE": "STE",
    "STE": "STE",
    "UNIT": "UNIT",
    "#": "UNIT",
}


# ============================================================
# SECTION 07 - ENUMERATIONS
# ============================================================

class AddressInputType(StrEnum):
    STREET_ADDRESS = "street_address"
    BLOCK_LOT = "block_lot"
    OWNER_REFERENCE = "owner_reference"
    PO_BOX = "po_box"
    RURAL_ROUTE = "rural_route"
    INTERSECTION = "intersection"
    LANDMARK = "landmark"
    UNKNOWN = "unknown"


class AddressQuality(StrEnum):
    VERIFIED = "verified"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class AddressMatchLevel(StrEnum):
    EXACT = "exact"
    CANONICAL = "canonical"
    PARCEL = "parcel"
    STRONG = "strong"
    FUZZY = "fuzzy"
    NONE = "none"


class AddressComponentStatus(StrEnum):
    PRESENT = "present"
    NORMALIZED = "normalized"
    INFERRED = "inferred"
    MISSING = "missing"
    INVALID = "invalid"


class PublicRecordRoutingStatus(StrEnum):
    READY = "ready"
    PARTIAL = "partial"
    OUTSIDE_INITIAL_SCOPE = "outside_initial_scope"
    MISSING_SEARCH_SIGNAL = "missing_search_signal"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    UNKNOWN = "unknown"


class PublicRecordConnectorTarget(StrEnum):
    MORRIS_TAX_BOARD = "nj_morris_tax_board_connector"
    MORRIS_CLERK = "nj_morris_clerk_connector"
    MORRIS_GIS = "nj_morris_gis_connector"
    NJ_STATE_MODIV = "nj_state_modiv_connector"


class ManualReviewReason(StrEnum):
    MISSING_HOUSE_NUMBER = "missing_house_number"
    MISSING_STREET_NAME = "missing_street_name"
    MISSING_MUNICIPALITY = "missing_municipality"
    MISSING_STATE = "missing_state"
    MISSING_SEARCH_SIGNAL = "missing_search_signal"
    AMBIGUOUS_MUNICIPALITY = "ambiguous_municipality"
    OUTSIDE_INITIAL_SCOPE = "outside_initial_scope"
    BLOCK_WITHOUT_LOT = "block_without_lot"
    LOT_WITHOUT_BLOCK = "lot_without_block"
    LOW_CONFIDENCE = "low_confidence"
    PO_BOX_NOT_PROPERTY_PARCEL = "po_box_not_property_parcel"
    OWNER_REFERENCE_ONLY = "owner_reference_only"


# ============================================================
# SECTION 08 - UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(UTC).isoformat()


def strip_accents(value: str) -> str:
    """
    Remove accents from text.
    """

    normalized = unicodedata.normalize("NFKD", value)

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )


def safe_string(value: Any) -> str:
    """
    Convert value to stripped string.
    """

    if value is None:
        return ""

    return str(value).strip()


def normalize_text(value: Any) -> str | None:
    """
    Normalize address text for parsing.
    """

    text = safe_string(value)

    if not text:
        return None

    text = strip_accents(text)
    text = text.upper().strip()
    text = text.replace("’", "'").replace("`", "'")
    text = text.replace(".", " ")
    text = NON_ADDRESS_TEXT_RE.sub(" ", text)
    text = WHITESPACE_RE.sub(" ", text).strip()

    return text or None


def normalize_display_text(value: Any) -> str | None:
    """
    Normalize display text into title case.
    """

    text = safe_string(value)

    if not text:
        return None

    return " ".join(text.split()).title()


def normalize_identifier(value: Any) -> str | None:
    """
    Normalize value into alphanumeric identifier.
    """

    text = normalize_text(value)

    if not text:
        return None

    normalized = re.sub(r"[^A-Z0-9]", "", text)

    return normalized or None


def normalize_state(value: Any) -> str | None:
    """
    Normalize state name or code.
    """

    text = normalize_text(value)

    if not text:
        return None

    if text in VALID_STATE_CODES:
        return text

    return STATE_NAME_TO_CODE.get(text)


def normalize_county(value: Any) -> str | None:
    """
    Normalize county name.
    """

    text = normalize_text(value)

    if not text:
        return None

    if text.endswith(" COUNTY"):
        text = text[:-7].strip()

    return text.title()


def normalize_municipality(value: Any) -> str | None:
    """
    Normalize municipality name.
    """

    text = normalize_text(value)

    if not text:
        return None

    if text in MORRIS_COUNTY_MUNICIPALITIES:
        return MORRIS_COUNTY_MUNICIPALITIES[text]

    return text.title()


def normalize_postal_code(value: Any) -> tuple[str | None, str | None]:
    """
    Normalize ZIP or ZIP+4.
    """

    text = normalize_text(value)

    if not text:
        return None, None

    compact = text.replace(" ", "")

    match = ZIP_RE.search(compact)

    if not match:
        return None, None

    return match.group("zip5"), match.group("zip4")


def normalize_suffix(value: Any) -> str | None:
    """
    Normalize street suffix.
    """

    text = normalize_text(value)

    if not text:
        return None

    return STREET_SUFFIXES.get(text, text)


def normalize_directional(value: Any) -> str | None:
    """
    Normalize street directional.
    """

    text = normalize_text(value)

    if not text:
        return None

    return DIRECTIONALS.get(text, text)


def normalize_unit_type(value: Any) -> str | None:
    """
    Normalize unit designator.
    """

    text = normalize_text(value)

    if not text:
        return None

    return UNIT_DESIGNATORS.get(text, text)


def normalize_block_lot_value(value: Any) -> str | None:
    """
    Normalize block, lot, or qualifier value.
    """

    text = normalize_text(value)

    if not text:
        return None

    cleaned = re.sub(r"[^A-Z0-9.\-]", "", text)

    return cleaned or None


def stable_hash(value: Any) -> str:
    """
    Create deterministic SHA-256 hash.
    """

    payload = json.dumps(
        value,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def clamp_confidence(value: float) -> float:
    """
    Clamp confidence to 0..1.
    """

    if not math.isfinite(float(value)):
        return 0.0

    return max(0.0, min(1.0, float(value)))


def confidence_quality(score: float) -> AddressQuality:
    """
    Convert confidence to quality.
    """

    score = clamp_confidence(score)

    if score >= 0.95:
        return AddressQuality.VERIFIED

    if score >= 0.82:
        return AddressQuality.HIGH

    if score >= 0.62:
        return AddressQuality.MEDIUM

    if score > 0:
        return AddressQuality.LOW

    return AddressQuality.UNKNOWN


def levenshtein_distance(left: str, right: str) -> int:
    """
    Compute Levenshtein edit distance.
    """

    if left == right:
        return 0

    if not left:
        return len(right)

    if not right:
        return len(left)

    previous = list(range(len(right) + 1))

    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]

        for right_index, right_char in enumerate(right, start=1):
            insert_cost = current[right_index - 1] + 1
            delete_cost = previous[right_index] + 1
            substitute_cost = previous[right_index - 1] + (
                left_char != right_char
            )
            current.append(
                min(insert_cost, delete_cost, substitute_cost)
            )

        previous = current

    return previous[-1]


def similarity(left: Any, right: Any) -> float:
    """
    Return normalized text similarity.
    """

    left_value = normalize_text(left) or ""
    right_value = normalize_text(right) or ""

    if not left_value and not right_value:
        return 1.0

    if not left_value or not right_value:
        return 0.0

    distance = levenshtein_distance(left_value, right_value)
    maximum = max(len(left_value), len(right_value))

    return clamp_confidence(1.0 - (distance / maximum))


def object_to_dict(value: Any) -> Any:
    """
    Serialize dataclasses and nested structures.
    """

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


# ============================================================
# SECTION 09 - DATA CONTRACTS
# ============================================================

@dataclass
class AddressIssue:
    """
    Address parsing, normalization, or routing issue.
    """

    code: str
    message: str
    severity: str = "warning"
    component: str | None = None
    manual_review_required: bool = False
    suggested_value: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class AddressComponents:
    """
    Parsed normalized address components.
    """

    original: str
    input_type: str = AddressInputType.UNKNOWN.value
    house_number: str | None = None
    predirectional: str | None = None
    street_name: str | None = None
    street_suffix: str | None = None
    postdirectional: str | None = None
    unit_type: str | None = None
    unit_number: str | None = None
    po_box: str | None = None
    rural_route: str | None = None
    rural_box: str | None = None
    municipality: str | None = None
    county: str | None = None
    state_code: str | None = None
    postal_code: str | None = None
    postal_code_plus4: str | None = None
    country_code: str = DEFAULT_COUNTRY_CODE
    block: str | None = None
    lot: str | None = None
    qualifier: str | None = None
    owner_reference: str | None = None
    raw_query: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    parcel_id: str | None = None

    def street_line(self, include_unit: bool = True) -> str:
        """
        Return normalized street line.
        """

        if self.input_type == AddressInputType.PO_BOX.value and self.po_box:
            return f"PO BOX {self.po_box}"

        if self.input_type == AddressInputType.RURAL_ROUTE.value:
            pieces = [
                "RR",
                self.rural_route,
                "BOX",
                self.rural_box,
            ]

            return " ".join(piece for piece in pieces if piece)

        pieces = [
            self.house_number,
            self.predirectional,
            self.street_name,
            self.street_suffix,
            self.postdirectional,
        ]

        line = " ".join(piece for piece in pieces if piece)

        if include_unit and self.unit_number:
            unit_type = self.unit_type or "UNIT"
            line = f"{line} {unit_type} {self.unit_number}".strip()

        return line

    def locality_line(self) -> str:
        """
        Return locality line.
        """

        postal = self.postal_code or ""

        if self.postal_code and self.postal_code_plus4:
            postal = f"{self.postal_code}-{self.postal_code_plus4}"

        return " ".join(
            part
            for part in [
                self.municipality,
                self.state_code,
                postal,
            ]
            if part
        )

    def canonical_address(self, include_unit: bool = True) -> str:
        """
        Return canonical display address.
        """

        if self.block and self.lot and not self.street_line():
            parts = [
                f"Block {self.block}",
                f"Lot {self.lot}",
                f"Qual {self.qualifier}" if self.qualifier else None,
                self.municipality,
                self.county,
                self.state_code,
            ]

            return ", ".join(part for part in parts if part)

        return ", ".join(
            part
            for part in [
                self.street_line(include_unit=include_unit),
                self.municipality,
                " ".join(
                    part
                    for part in [
                        self.state_code,
                        (
                            f"{self.postal_code}-{self.postal_code_plus4}"
                            if self.postal_code and self.postal_code_plus4
                            else self.postal_code
                        ),
                    ]
                    if part
                ),
            ]
            if part
        )

    def has_street_signal(self) -> bool:
        """
        Return whether components have street address signal.
        """

        return bool(self.house_number and self.street_name)

    def has_block_lot_signal(self) -> bool:
        """
        Return whether components have block and lot.
        """

        return bool(self.block and self.lot)

    def has_owner_signal(self) -> bool:
        """
        Return whether components have owner reference only.
        """

        return bool(self.owner_reference)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class PublicRecordSearchPreparation:
    """
    Public-record lookup preparation output.
    """

    routing_status: str
    state_code: str | None = None
    county: str | None = None
    municipality: str | None = None
    jurisdiction_label: str | None = None
    primary_query_mode: str = "unknown"
    connector_targets: list[str] = field(default_factory=list)
    raw_query: str | None = None
    street_address: str | None = None
    normalized_address: str | None = None
    block: str | None = None
    lot: str | None = None
    qualifier: str | None = None
    owner_reference: str | None = None
    postal_code: str | None = None
    morris_county_ready: bool = False
    nj_state_ready: bool = False
    manual_review_required: bool = False
    unavailable_reasons: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class AddressAnalysis:
    """
    Complete address intelligence result.
    """

    request_id: str
    components: AddressComponents
    quality: str
    confidence: float
    canonical_address: str
    normalized_street_address: str
    match_key: str
    property_match_key: str
    fingerprint: str
    public_record_search: PublicRecordSearchPreparation
    issues: list[AddressIssue] = field(default_factory=list)
    transformations: list[str] = field(default_factory=list)
    component_status: dict[str, str] = field(default_factory=dict)
    manual_review_required: bool = False
    created_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """
        Return whether address analysis is usable.
        """

        return self.quality != AddressQuality.INVALID.value

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class AddressMatchResult:
    """
    Address match comparison result.
    """

    level: str
    score: float
    is_match: bool
    component_scores: dict[str, float]
    reasons: list[str]
    left: AddressAnalysis
    right: AddressAnalysis

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


@dataclass
class BatchAddressResult:
    """
    Batch address processing result.
    """

    total: int
    valid: int
    invalid: int
    duplicate_groups: int
    analyses: list[AddressAnalysis]
    groups: list[list[AddressAnalysis]]

    def to_dict(self) -> dict[str, Any]:
        return object_to_dict(asdict(self))


# ============================================================
# SECTION 10 - PARSER
# ============================================================

class AddressParser:
    """
    Deterministic parser for U.S. residential property address input.
    """

    def parse(
        self,
        raw_address: str,
        *,
        municipality: str | None = None,
        county: str | None = None,
        state_code: str | None = None,
        postal_code: str | None = None,
        owner_reference: str | None = None,
        country_code: str = DEFAULT_COUNTRY_CODE,
    ) -> AddressComponents:
        """
        Parse raw input into normalized address components.
        """

        if not safe_string(raw_address):
            raise ValueError("raw_address is required")

        original = safe_string(raw_address)
        normalized = normalize_text(original) or ""

        block, lot, qualifier = self.extract_block_lot(normalized)

        if block or lot:
            zip5, zip4 = normalize_postal_code(postal_code)
            inferred_state = normalize_state(state_code) or self.extract_state(
                normalized
            )
            inferred_municipality = (
                normalize_municipality(municipality)
                or self.detect_morris_municipality(normalized)
            )
            inferred_county = (
                normalize_county(county)
                or self.detect_county(normalized)
            )

            return AddressComponents(
                original=original,
                input_type=AddressInputType.BLOCK_LOT.value,
                municipality=inferred_municipality,
                county=inferred_county,
                state_code=inferred_state or DEFAULT_STATE_CODE,
                postal_code=zip5,
                postal_code_plus4=zip4,
                country_code=country_code,
                block=block,
                lot=lot,
                qualifier=qualifier,
                owner_reference=normalize_display_text(owner_reference),
                raw_query=original,
            )

        street, inline_municipality, inline_state, inline_zip = (
            self.split_full_address(normalized)
        )

        municipality_value = (
            normalize_municipality(municipality)
            or normalize_municipality(inline_municipality)
            or self.detect_morris_municipality(normalized)
        )

        state_value = (
            normalize_state(state_code)
            or normalize_state(inline_state)
            or self.extract_state(normalized)
        )

        zip5, zip4 = normalize_postal_code(postal_code or inline_zip)

        county_value = (
            normalize_county(county)
            or self.detect_county(normalized)
            or self.infer_county_from_zip(zip5)
            or self.infer_county_from_municipality(municipality_value)
        )

        po_box = PO_BOX_RE.match(street)

        if po_box:
            return AddressComponents(
                original=original,
                input_type=AddressInputType.PO_BOX.value,
                po_box=po_box.group(1),
                municipality=municipality_value,
                county=county_value,
                state_code=state_value,
                postal_code=zip5,
                postal_code_plus4=zip4,
                country_code=country_code,
                raw_query=original,
            )

        rural = RURAL_ROUTE_RE.match(street)

        if rural:
            return AddressComponents(
                original=original,
                input_type=AddressInputType.RURAL_ROUTE.value,
                rural_route=rural.group(1),
                rural_box=rural.group(2),
                municipality=municipality_value,
                county=county_value,
                state_code=state_value,
                postal_code=zip5,
                postal_code_plus4=zip4,
                country_code=country_code,
                raw_query=original,
            )

        if " & " in f" {street} " or " AND " in f" {street} ":
            return AddressComponents(
                original=original,
                input_type=AddressInputType.INTERSECTION.value,
                street_name=street,
                municipality=municipality_value,
                county=county_value,
                state_code=state_value,
                postal_code=zip5,
                postal_code_plus4=zip4,
                country_code=country_code,
                raw_query=original,
            )

        return self.parse_street(
            original=original,
            street_line=street,
            municipality=municipality_value,
            county=county_value,
            state_code=state_value,
            postal_code=zip5,
            postal_code_plus4=zip4,
            country_code=country_code,
            owner_reference=owner_reference,
        )

    def split_full_address(
        self,
        normalized: str,
    ) -> tuple[str, str | None, str | None, str | None]:
        """
        Split full address into street, municipality, state, ZIP.
        """

        parts = [
            part.strip()
            for part in normalized.split(",")
            if part.strip()
        ]

        if len(parts) >= 3:
            street = parts[0]
            municipality = parts[1]
            state_zip = " ".join(parts[2:])
            state, postal = self.split_state_zip(state_zip)

            return street, municipality, state, postal

        tokens = normalized.split()

        if len(tokens) >= 3:
            possible_zip = tokens[-1]
            zip5, _ = normalize_postal_code(possible_zip)

            if zip5:
                possible_state = tokens[-2]
                state = normalize_state(possible_state)

                if state:
                    body = tokens[:-2]
                    street_end = self.guess_street_end(body)
                    street = " ".join(body[:street_end])
                    municipality = " ".join(body[street_end:]) or None

                    return street, municipality, state, possible_zip

        return normalized, None, None, None

    @staticmethod
    def split_state_zip(value: str) -> tuple[str | None, str | None]:
        """
        Split state and ZIP segment.
        """

        tokens = value.split()

        if not tokens:
            return None, None

        if len(tokens) == 1:
            state = normalize_state(tokens[0])
            zip5, _ = normalize_postal_code(tokens[0])

            return state, tokens[0] if zip5 else None

        postal = tokens[-1]
        state_text = " ".join(tokens[:-1])
        state = normalize_state(state_text)
        zip5, _ = normalize_postal_code(postal)

        if state:
            return state, postal if zip5 else None

        state = normalize_state(tokens[0])

        return state, postal if zip5 else None

    @staticmethod
    def guess_street_end(tokens: Sequence[str]) -> int:
        """
        Guess where street ends before municipality.
        """

        for index, token in enumerate(tokens):
            if normalize_suffix(token) in set(STREET_SUFFIXES.values()):
                return index + 1

        return min(3, len(tokens))

    def parse_street(
        self,
        *,
        original: str,
        street_line: str,
        municipality: str | None,
        county: str | None,
        state_code: str | None,
        postal_code: str | None,
        postal_code_plus4: str | None,
        country_code: str,
        owner_reference: str | None = None,
    ) -> AddressComponents:
        """
        Parse a normalized street line.
        """

        unit_type, unit_number, without_unit = self.extract_unit(street_line)

        number_match = HOUSE_NUMBER_RE.match(without_unit)
        house_number = None
        remaining = without_unit.strip()

        if number_match:
            house_number = number_match.group("number").upper()
            remaining = without_unit[number_match.end():].strip()

        tokens = remaining.split()

        predirectional = None
        postdirectional = None
        street_suffix = None

        if tokens and normalize_directional(tokens[0]) in DIRECTIONALS.values():
            predirectional = normalize_directional(tokens.pop(0))

        if tokens and normalize_directional(tokens[-1]) in DIRECTIONALS.values():
            postdirectional = normalize_directional(tokens.pop())

        if tokens and normalize_suffix(tokens[-1]) in STREET_SUFFIXES.values():
            street_suffix = normalize_suffix(tokens.pop())

        street_name = " ".join(tokens) or None

        return AddressComponents(
            original=original,
            input_type=AddressInputType.STREET_ADDRESS.value,
            house_number=house_number,
            predirectional=predirectional,
            street_name=street_name,
            street_suffix=street_suffix,
            postdirectional=postdirectional,
            unit_type=unit_type,
            unit_number=unit_number,
            municipality=municipality,
            county=county,
            state_code=state_code,
            postal_code=postal_code,
            postal_code_plus4=postal_code_plus4,
            country_code=country_code,
            owner_reference=normalize_display_text(owner_reference),
            raw_query=original,
        )

    @staticmethod
    def extract_unit(
        street_line: str,
    ) -> tuple[str | None, str | None, str]:
        """
        Extract unit from street line.
        """

        match = UNIT_RE.search(street_line)

        if not match:
            return None, None, street_line

        matched_text = match.group(0).strip()
        unit_number = match.group(1).upper()
        prefix = matched_text[: matched_text.upper().find(unit_number)].strip(
            " ,"
        )
        unit_type = normalize_unit_type(prefix or "UNIT")
        without_unit = street_line[: match.start()].strip(" ,")

        return unit_type, unit_number, without_unit

    @staticmethod
    def extract_block_lot(
        normalized: str,
    ) -> tuple[str | None, str | None, str | None]:
        """
        Extract block, lot, qualifier from query.
        """

        match = BLOCK_LOT_RE.search(normalized) or LOT_BLOCK_RE.search(
            normalized
        )

        if not match:
            return None, None, None

        block = normalize_block_lot_value(match.group("block"))
        lot = normalize_block_lot_value(match.group("lot"))

        qualifier_match = QUALIFIER_RE.search(normalized)
        qualifier = (
            normalize_block_lot_value(qualifier_match.group("qualifier"))
            if qualifier_match
            else None
        )

        return block, lot, qualifier

    @staticmethod
    def extract_state(normalized: str) -> str | None:
        """
        Extract state from normalized text.
        """

        match = STATE_ZIP_RE.search(normalized)

        if match:
            return normalize_state(match.group("state"))

        tokens = normalized.split()

        for token in tokens:
            state = normalize_state(token)

            if state:
                return state

        for state_name, state_code in STATE_NAME_TO_CODE.items():
            if state_name in normalized:
                return state_code

        return None

    @staticmethod
    def detect_county(normalized: str) -> str | None:
        """
        Detect county from input.
        """

        if "MORRIS COUNTY" in normalized or " MORRIS " in f" {normalized} ":
            return "Morris"

        return None

    @staticmethod
    def infer_county_from_zip(zip5: str | None) -> str | None:
        """
        Infer Morris County from ZIP hint.
        """

        if zip5 in MORRIS_COUNTY_ZIP_HINTS:
            return "Morris"

        return None

    @staticmethod
    def infer_county_from_municipality(
        municipality: str | None,
    ) -> str | None:
        """
        Infer county from known Morris municipality.
        """

        if not municipality:
            return None

        normalized = normalize_text(municipality)

        if normalized in MORRIS_COUNTY_MUNICIPALITIES:
            return "Morris"

        return None

    @staticmethod
    def detect_morris_municipality(normalized: str) -> str | None:
        """
        Detect Morris County municipality in address text.
        """

        best_match: str | None = None
        best_length = 0

        for key, display in MORRIS_COUNTY_MUNICIPALITIES.items():
            pattern = f" {key} "

            if pattern in f" {normalized} " and len(key) > best_length:
                best_match = display
                best_length = len(key)

        return best_match


# ============================================================
# SECTION 11 - VALIDATOR
# ============================================================

class AddressValidator:
    """
    Validate parsed address components.
    """

    def validate(self, components: AddressComponents) -> list[AddressIssue]:
        """
        Validate address and routing readiness.
        """

        issues: list[AddressIssue] = []

        if not (
            components.has_street_signal()
            or components.has_block_lot_signal()
            or components.has_owner_signal()
        ):
            issues.append(
                AddressIssue(
                    code=ManualReviewReason.MISSING_SEARCH_SIGNAL.value,
                    message=(
                        "Address intelligence needs a street address, "
                        "block/lot, or owner reference to prepare lookup."
                    ),
                    severity="error",
                    component="raw_query",
                    manual_review_required=True,
                )
            )

        if components.input_type == AddressInputType.STREET_ADDRESS.value:
            if not components.house_number:
                issues.append(
                    AddressIssue(
                        code=ManualReviewReason.MISSING_HOUSE_NUMBER.value,
                        message="Street address is missing a house number.",
                        severity="error",
                        component="house_number",
                        manual_review_required=True,
                    )
                )

            if not components.street_name:
                issues.append(
                    AddressIssue(
                        code=ManualReviewReason.MISSING_STREET_NAME.value,
                        message="Street address is missing a street name.",
                        severity="error",
                        component="street_name",
                        manual_review_required=True,
                    )
                )

        if components.input_type == AddressInputType.PO_BOX.value:
            issues.append(
                AddressIssue(
                    code=ManualReviewReason.PO_BOX_NOT_PROPERTY_PARCEL.value,
                    message=(
                        "PO Box input may not identify a residential parcel. "
                        "A street address or block/lot may be required."
                    ),
                    severity="warning",
                    component="po_box",
                    manual_review_required=True,
                )
            )

        if components.block and not components.lot:
            issues.append(
                AddressIssue(
                    code=ManualReviewReason.BLOCK_WITHOUT_LOT.value,
                    message="Block was detected without lot.",
                    severity="warning",
                    component="lot",
                    manual_review_required=True,
                )
            )

        if components.lot and not components.block:
            issues.append(
                AddressIssue(
                    code=ManualReviewReason.LOT_WITHOUT_BLOCK.value,
                    message="Lot was detected without block.",
                    severity="warning",
                    component="block",
                    manual_review_required=True,
                )
            )

        if not components.municipality:
            issues.append(
                AddressIssue(
                    code=ManualReviewReason.MISSING_MUNICIPALITY.value,
                    message="Municipality could not be confidently detected.",
                    severity="warning",
                    component="municipality",
                    manual_review_required=True,
                )
            )

        if not components.state_code:
            issues.append(
                AddressIssue(
                    code=ManualReviewReason.MISSING_STATE.value,
                    message="State could not be confidently detected.",
                    severity="warning",
                    component="state_code",
                    suggested_value=DEFAULT_STATE_CODE,
                )
            )

        if components.state_code and components.state_code != DEFAULT_STATE_CODE:
            issues.append(
                AddressIssue(
                    code=ManualReviewReason.OUTSIDE_INITIAL_SCOPE.value,
                    message=(
                        "Current public-record connector priority is New "
                        "Jersey first."
                    ),
                    severity="info",
                    component="state_code",
                )
            )

        return issues


# ============================================================
# SECTION 12 - CONFIDENCE SCORER
# ============================================================

class AddressConfidenceScorer:
    """
    Score parsed address confidence.
    """

    COMPONENT_WEIGHTS = {
        "house_number": 0.18,
        "street_name": 0.22,
        "street_suffix": 0.06,
        "municipality": 0.16,
        "county": 0.10,
        "state_code": 0.10,
        "postal_code": 0.12,
        "block_lot": 0.16,
    }

    def score(
        self,
        components: AddressComponents,
        issues: Sequence[AddressIssue],
    ) -> float:
        """
        Score address confidence.
        """

        score = 0.0

        if components.house_number:
            score += self.COMPONENT_WEIGHTS["house_number"]

        if components.street_name:
            score += self.COMPONENT_WEIGHTS["street_name"]

        if components.street_suffix:
            score += self.COMPONENT_WEIGHTS["street_suffix"]

        if components.municipality:
            score += self.COMPONENT_WEIGHTS["municipality"]

        if components.county:
            score += self.COMPONENT_WEIGHTS["county"]

        if components.state_code:
            score += self.COMPONENT_WEIGHTS["state_code"]

        if components.postal_code:
            score += self.COMPONENT_WEIGHTS["postal_code"]

        if components.block and components.lot:
            score += self.COMPONENT_WEIGHTS["block_lot"]

        if components.state_code == DEFAULT_STATE_CODE:
            score += 0.04

        if components.county == DEFAULT_COUNTY:
            score += 0.04

        if components.postal_code in MORRIS_COUNTY_ZIP_HINTS:
            score += 0.04

        for issue in issues:
            if issue.severity == "error":
                score -= 0.20
            elif issue.severity == "warning":
                score -= 0.06
            elif issue.severity == "info":
                score -= 0.02

        return round(clamp_confidence(score), 6)

    @staticmethod
    def quality(score: float, issues: Sequence[AddressIssue]) -> AddressQuality:
        """
        Convert score and issues into quality.
        """

        if any(issue.severity == "error" for issue in issues):
            return AddressQuality.INVALID

        return confidence_quality(score)


# ============================================================
# SECTION 13 - KEY BUILDER
# ============================================================

class AddressKeyBuilder:
    """
    Build deterministic address keys.
    """

    @staticmethod
    def match_key(
        components: AddressComponents,
        *,
        include_unit: bool = True,
    ) -> str:
        """
        Build unit-sensitive match key.
        """

        values = [
            components.house_number,
            components.predirectional,
            components.street_name,
            components.street_suffix,
            components.postdirectional,
            components.unit_type if include_unit else None,
            components.unit_number if include_unit else None,
            components.municipality,
            components.state_code,
            components.postal_code,
        ]

        return "|".join(normalize_identifier(value) or "" for value in values)

    @staticmethod
    def property_match_key(components: AddressComponents) -> str:
        """
        Build property-level match key without unit.
        """

        return AddressKeyBuilder.match_key(
            components,
            include_unit=False,
        )

    @staticmethod
    def block_lot_key(components: AddressComponents) -> str | None:
        """
        Build block/lot key.
        """

        if not components.block or not components.lot:
            return None

        return "|".join(
            value
            for value in [
                normalize_identifier(components.state_code),
                normalize_identifier(components.county),
                normalize_identifier(components.municipality),
                normalize_identifier(components.block),
                normalize_identifier(components.lot),
                normalize_identifier(components.qualifier),
            ]
            if value
        )

    @staticmethod
    def fingerprint(components: AddressComponents) -> str:
        """
        Build stable address fingerprint.
        """

        return stable_hash(
            {
                "input_type": components.input_type,
                "property_match_key": AddressKeyBuilder.property_match_key(
                    components
                ),
                "block_lot_key": AddressKeyBuilder.block_lot_key(components),
                "unit_number": normalize_identifier(components.unit_number),
                "owner_reference": normalize_identifier(
                    components.owner_reference
                ),
                "country": normalize_identifier(components.country_code),
            }
        )


# ============================================================
# SECTION 14 - PUBLIC RECORD ROUTER
# ============================================================

class PublicRecordSearchPreparer:
    """
    Prepare address analysis for public-record lookup.
    """

    UNSUPPORTED_WITH_PUBLIC_RECORDS_ONLY = [
        "active_listing_status",
        "under_contract_status",
        "pending_status",
        "current_listing_price",
        "current_days_on_market",
        "showing_availability",
        "broker_confirmation",
        "current_mls_status",
        "market_value_without_valuation_engine",
    ]

    def prepare(
        self,
        components: AddressComponents,
        issues: Sequence[AddressIssue],
    ) -> PublicRecordSearchPreparation:
        """
        Prepare public-record routing payload.
        """

        state_code = components.state_code or DEFAULT_STATE_CODE
        county = components.county
        municipality = components.municipality

        if not county and state_code == "NJ":
            county = self.infer_county(components)

        morris_ready = (
            state_code == "NJ"
            and county == "Morris"
            and (
                components.has_street_signal()
                or components.has_block_lot_signal()
                or components.has_owner_signal()
            )
        )

        nj_ready = (
            state_code == "NJ"
            and (
                components.has_street_signal()
                or components.has_block_lot_signal()
                or components.has_owner_signal()
            )
        )

        connector_targets: list[str] = []

        if morris_ready:
            connector_targets.extend(
                [
                    PublicRecordConnectorTarget.MORRIS_TAX_BOARD.value,
                    PublicRecordConnectorTarget.MORRIS_CLERK.value,
                    PublicRecordConnectorTarget.MORRIS_GIS.value,
                ]
            )

        if nj_ready:
            connector_targets.append(
                PublicRecordConnectorTarget.NJ_STATE_MODIV.value
            )

        connector_targets = list(dict.fromkeys(connector_targets))

        manual_review_required = any(
            issue.manual_review_required
            for issue in issues
        )

        unavailable_reasons: list[str] = []

        if not nj_ready:
            unavailable_reasons.append(
                "New Jersey public-record routing is not ready for this input."
            )

        if state_code != "NJ":
            unavailable_reasons.append(
                "Initial connector set is optimized for New Jersey first."
            )

        if county and county != "Morris":
            unavailable_reasons.append(
                "County-specific connector set is currently Morris County first."
            )

        if not connector_targets:
            manual_review_required = True

        if components.has_block_lot_signal():
            primary_query_mode = "block_lot"
        elif components.has_street_signal():
            primary_query_mode = "address"
        elif components.has_owner_signal():
            primary_query_mode = "owner_reference"
        else:
            primary_query_mode = "unknown"

        if not connector_targets:
            routing_status = PublicRecordRoutingStatus.MISSING_SEARCH_SIGNAL.value
        elif manual_review_required:
            routing_status = (
                PublicRecordRoutingStatus.MANUAL_REVIEW_REQUIRED.value
            )
        elif morris_ready:
            routing_status = PublicRecordRoutingStatus.READY.value
        else:
            routing_status = PublicRecordRoutingStatus.PARTIAL.value

        return PublicRecordSearchPreparation(
            routing_status=routing_status,
            state_code=state_code,
            county=county,
            municipality=municipality,
            jurisdiction_label=self.build_jurisdiction_label(
                state_code=state_code,
                county=county,
                municipality=municipality,
            ),
            primary_query_mode=primary_query_mode,
            connector_targets=connector_targets,
            raw_query=components.raw_query or components.original,
            street_address=components.street_line(include_unit=False) or None,
            normalized_address=components.canonical_address(include_unit=True),
            block=components.block,
            lot=components.lot,
            qualifier=components.qualifier,
            owner_reference=components.owner_reference,
            postal_code=components.postal_code,
            morris_county_ready=morris_ready,
            nj_state_ready=nj_ready,
            manual_review_required=manual_review_required,
            unavailable_reasons=unavailable_reasons,
            unsupported_claims=list(self.UNSUPPORTED_WITH_PUBLIC_RECORDS_ONLY),
            metadata={
                "prepared_at": utc_now(),
                "governance": ADDRESS_INTELLIGENCE_GOVERNANCE.copy(),
            },
        )

    @staticmethod
    def infer_county(components: AddressComponents) -> str | None:
        """
        Infer county from municipality or ZIP.
        """

        if components.county:
            return components.county

        if components.postal_code in MORRIS_COUNTY_ZIP_HINTS:
            return "Morris"

        normalized_municipality = normalize_text(components.municipality)

        if normalized_municipality in MORRIS_COUNTY_MUNICIPALITIES:
            return "Morris"

        return None

    @staticmethod
    def build_jurisdiction_label(
        *,
        state_code: str | None,
        county: str | None,
        municipality: str | None,
    ) -> str | None:
        """
        Build display jurisdiction label.
        """

        parts = [
            municipality,
            f"{county} County" if county else None,
            state_code,
        ]

        label = ", ".join(part for part in parts if part)

        return label or None


# ============================================================
# SECTION 15 - MATCHER
# ============================================================

class AddressMatcher:
    """
    Compare two address analyses.
    """

    WEIGHTS = {
        "house_number": 0.24,
        "street_name": 0.26,
        "street_suffix": 0.06,
        "municipality": 0.14,
        "state_code": 0.10,
        "postal_code": 0.12,
        "unit_number": 0.08,
    }

    def compare(
        self,
        left: AddressAnalysis,
        right: AddressAnalysis,
        *,
        match_threshold: float = 0.84,
    ) -> AddressMatchResult:
        """
        Compare two analyses.
        """

        left_components = left.components
        right_components = right.components
        reasons: list[str] = []

        left_block_lot = AddressKeyBuilder.block_lot_key(left_components)
        right_block_lot = AddressKeyBuilder.block_lot_key(right_components)

        if left_block_lot and right_block_lot and left_block_lot == right_block_lot:
            return AddressMatchResult(
                level=AddressMatchLevel.PARCEL.value,
                score=1.0,
                is_match=True,
                component_scores={"block_lot": 1.0},
                reasons=["Block/lot/municipality keys match."],
                left=left,
                right=right,
            )

        if left.fingerprint == right.fingerprint:
            return AddressMatchResult(
                level=AddressMatchLevel.EXACT.value,
                score=1.0,
                is_match=True,
                component_scores={"fingerprint": 1.0},
                reasons=["Address fingerprints are identical."],
                left=left,
                right=right,
            )

        component_scores: dict[str, float] = {}
        weighted_total = 0.0
        available_weight = 0.0

        for component, weight in self.WEIGHTS.items():
            left_value = getattr(left_components, component)
            right_value = getattr(right_components, component)

            if left_value is None and right_value is None:
                continue

            component_score = similarity(left_value, right_value)
            component_scores[component] = component_score
            weighted_total += component_score * weight
            available_weight += weight

        total_score = weighted_total / available_weight if available_weight else 0.0

        if left.property_match_key == right.property_match_key:
            level = AddressMatchLevel.CANONICAL.value
            total_score = max(total_score, 0.96)
            reasons.append("Property-level canonical keys match.")
        elif total_score >= match_threshold:
            level = AddressMatchLevel.FUZZY.value
            reasons.append("Weighted component similarity exceeds threshold.")
        else:
            level = AddressMatchLevel.NONE.value
            reasons.append("Weighted component similarity is below threshold.")

        if (
            left_components.unit_number
            and right_components.unit_number
            and normalize_identifier(left_components.unit_number)
            != normalize_identifier(right_components.unit_number)
        ):
            total_score -= 0.12
            reasons.append("Unit numbers conflict.")

        total_score = round(clamp_confidence(total_score), 6)

        return AddressMatchResult(
            level=level,
            score=total_score,
            is_match=total_score >= match_threshold
            and level != AddressMatchLevel.NONE.value,
            component_scores=component_scores,
            reasons=reasons,
            left=left,
            right=right,
        )


# ============================================================
# SECTION 16 - ADDRESS INTELLIGENCE ENGINE
# ============================================================

class AddressIntelligenceEngine:
    """
    High-level deterministic address intelligence orchestration service.
    """

    def __init__(
        self,
        *,
        parser: AddressParser | None = None,
        validator: AddressValidator | None = None,
        scorer: AddressConfidenceScorer | None = None,
        public_record_preparer: PublicRecordSearchPreparer | None = None,
        matcher: AddressMatcher | None = None,
    ) -> None:
        self.parser = parser or AddressParser()
        self.validator = validator or AddressValidator()
        self.scorer = scorer or AddressConfidenceScorer()
        self.public_record_preparer = (
            public_record_preparer or PublicRecordSearchPreparer()
        )
        self.matcher = matcher or AddressMatcher()

    def analyze(
        self,
        raw_address: str,
        *,
        municipality: str | None = None,
        city: str | None = None,
        county: str | None = None,
        state_code: str | None = None,
        postal_code: str | None = None,
        owner_reference: str | None = None,
        country_code: str = DEFAULT_COUNTRY_CODE,
    ) -> AddressAnalysis:
        """
        Analyze address and prepare public-record search.
        """

        request_id = self.make_request_id(
            raw_address=raw_address,
            municipality=municipality or city,
            county=county,
            state_code=state_code,
            postal_code=postal_code,
            owner_reference=owner_reference,
        )

        components = self.parser.parse(
            raw_address,
            municipality=municipality or city,
            county=county,
            state_code=state_code,
            postal_code=postal_code,
            owner_reference=owner_reference,
            country_code=country_code,
        )

        transformations = self.build_transformations(raw_address, components)
        issues = self.validator.validate(components)
        confidence = self.scorer.score(components, issues)
        quality = self.scorer.quality(confidence, issues)

        public_record_search = self.public_record_preparer.prepare(
            components,
            issues,
        )

        manual_review_required = (
            public_record_search.manual_review_required
            or any(issue.manual_review_required for issue in issues)
            or confidence < 0.62
        )

        if confidence < 0.62:
            issues.append(
                AddressIssue(
                    code=ManualReviewReason.LOW_CONFIDENCE.value,
                    message="Address confidence is below production-ready threshold.",
                    severity="warning",
                    component="confidence",
                    manual_review_required=True,
                )
            )

        canonical_address = components.canonical_address(include_unit=True)
        normalized_street_address = components.street_line(include_unit=True)
        match_key = AddressKeyBuilder.match_key(
            components,
            include_unit=True,
        )
        property_match_key = AddressKeyBuilder.property_match_key(components)
        fingerprint = AddressKeyBuilder.fingerprint(components)

        return AddressAnalysis(
            request_id=request_id,
            components=components,
            quality=quality.value,
            confidence=confidence,
            canonical_address=canonical_address,
            normalized_street_address=normalized_street_address,
            match_key=match_key,
            property_match_key=property_match_key,
            fingerprint=fingerprint,
            public_record_search=public_record_search,
            issues=issues,
            transformations=transformations,
            component_status=self.component_status(components),
            manual_review_required=manual_review_required,
            metadata={
                "engine": ADDRESS_INTELLIGENCE_ENGINE_NAME,
                "version": ADDRESS_INTELLIGENCE_ENGINE_VERSION,
                "phase": ADDRESS_INTELLIGENCE_ENGINE_PHASE,
                "analyzed_at": utc_now(),
                "governance": ADDRESS_INTELLIGENCE_GOVERNANCE.copy(),
            },
        )

    def compare(
        self,
        left_address: str | AddressAnalysis,
        right_address: str | AddressAnalysis,
        *,
        match_threshold: float = 0.84,
    ) -> AddressMatchResult:
        """
        Compare two addresses.
        """

        left = (
            left_address
            if isinstance(left_address, AddressAnalysis)
            else self.analyze(left_address)
        )

        right = (
            right_address
            if isinstance(right_address, AddressAnalysis)
            else self.analyze(right_address)
        )

        return self.matcher.compare(
            left,
            right,
            match_threshold=match_threshold,
        )

    def deduplicate(
        self,
        addresses: Iterable[str],
        *,
        match_threshold: float = 0.90,
    ) -> list[list[AddressAnalysis]]:
        """
        Deduplicate address list.
        """

        groups: list[list[AddressAnalysis]] = []

        for raw_address in addresses:
            candidate = self.analyze(raw_address)
            placed = False

            for group in groups:
                comparison = self.matcher.compare(
                    group[0],
                    candidate,
                    match_threshold=match_threshold,
                )

                if comparison.is_match:
                    group.append(candidate)
                    placed = True
                    break

            if not placed:
                groups.append([candidate])

        return groups

    def to_property_intelligence_request_payload(
        self,
        analysis: AddressAnalysis,
    ) -> dict[str, Any]:
        """
        Convert address analysis to property-intelligence request payload.
        """

        components = analysis.components
        public_records = analysis.public_record_search

        return {
            "request_id": analysis.request_id,
            "raw_query": components.raw_query or components.original,
            "street_address": components.street_line(include_unit=False) or None,
            "municipality": components.municipality,
            "county": components.county,
            "state": components.state_code,
            "postal_code": components.postal_code,
            "block": components.block,
            "lot": components.lot,
            "qualifier": components.qualifier,
            "parcel_id": components.parcel_id,
            "owner_reference": components.owner_reference,
            "include_public_records": True,
            "include_listing": True,
            "include_valuation": True,
            "include_comparables": True,
            "include_location_context": True,
            "include_ai_summary": True,
            "strict_source_mode": True,
            "allow_manual_review_results": True,
            "requested_domains": [
                "address",
                "parcel",
                "public_records",
                "tax_assessment",
                "sale_history",
                "owner_reference",
                "building_facts",
                "gis_context",
                "modiv_context",
                "valuation",
            ],
            "metadata": {
                "address_intelligence": analysis.to_dict(),
                "public_record_search": public_records.to_dict(),
            },
        }

    @staticmethod
    def make_request_id(**components: Any) -> str:
        """
        Build deterministic address request ID.
        """

        return f"address-request-{stable_hash(components)[:18]}"

    @staticmethod
    def build_transformations(
        original: str,
        components: AddressComponents,
    ) -> list[str]:
        """
        Build transformation labels.
        """

        transformations: list[str] = []

        normalized_original = normalize_text(original) or ""

        if normalized_original != original:
            transformations.append("normalized_case_whitespace_and_punctuation")

        if components.street_suffix:
            transformations.append("standardized_street_suffix")

        if components.predirectional or components.postdirectional:
            transformations.append("standardized_directional")

        if components.unit_number:
            transformations.append("standardized_unit_designator")

        if components.state_code:
            transformations.append("standardized_state_code")

        if components.postal_code:
            transformations.append("standardized_postal_code")

        if components.county == "Morris":
            transformations.append("inferred_or_detected_morris_county")

        if components.block and components.lot:
            transformations.append("detected_block_lot_search_signal")

        return list(dict.fromkeys(transformations))

    @staticmethod
    def component_status(
        components: AddressComponents,
    ) -> dict[str, str]:
        """
        Build component status map.
        """

        fields = [
            "house_number",
            "predirectional",
            "street_name",
            "street_suffix",
            "postdirectional",
            "unit_type",
            "unit_number",
            "municipality",
            "county",
            "state_code",
            "postal_code",
            "postal_code_plus4",
            "block",
            "lot",
            "qualifier",
            "owner_reference",
            "latitude",
            "longitude",
            "parcel_id",
        ]

        result: dict[str, str] = {}

        for field_name in fields:
            value = getattr(components, field_name)

            result[field_name] = (
                AddressComponentStatus.PRESENT.value
                if value not in (None, "")
                else AddressComponentStatus.MISSING.value
            )

        return result


# ============================================================
# SECTION 17 - BATCH PROCESSOR
# ============================================================

class BatchAddressProcessor:
    """
    Process multiple addresses.
    """

    def __init__(
        self,
        engine: AddressIntelligenceEngine | None = None,
    ) -> None:
        self.engine = engine or AddressIntelligenceEngine()

    def process(
        self,
        addresses: Iterable[str],
        *,
        deduplicate: bool = True,
        match_threshold: float = 0.90,
    ) -> BatchAddressResult:
        """
        Process address batch.
        """

        analyses = [
            self.engine.analyze(address)
            for address in addresses
        ]

        if deduplicate:
            groups = self.engine.deduplicate(
                [
                    analysis.components.original
                    for analysis in analyses
                ],
                match_threshold=match_threshold,
            )
        else:
            groups = [[analysis] for analysis in analyses]

        valid_count = sum(1 for analysis in analyses if analysis.is_valid)
        duplicate_groups = sum(1 for group in groups if len(group) > 1)

        return BatchAddressResult(
            total=len(analyses),
            valid=valid_count,
            invalid=len(analyses) - valid_count,
            duplicate_groups=duplicate_groups,
            analyses=analyses,
            groups=groups,
        )


# ============================================================
# SECTION 18 - PROFILE AND PUBLIC RECORD BRIDGE HELPERS
# ============================================================

def analysis_to_public_record_search_payload(
    analysis: AddressAnalysis,
) -> dict[str, Any]:
    """
    Convert analysis into public records engine payload.
    """

    search = analysis.public_record_search

    return {
        "raw_query": search.raw_query,
        "street_address": search.street_address,
        "municipality": search.municipality,
        "county": search.county,
        "state": search.state_code,
        "postal_code": search.postal_code,
        "block": search.block,
        "lot": search.lot,
        "qualifier": search.qualifier,
        "owner_reference": search.owner_reference,
        "metadata": {
            "source": "address_intelligence",
            "address_request_id": analysis.request_id,
            "address_fingerprint": analysis.fingerprint,
            "routing_status": search.routing_status,
            "connector_targets": search.connector_targets,
            "manual_review_required": search.manual_review_required,
        },
    }


def analysis_to_property_identity_payload(
    analysis: AddressAnalysis,
) -> dict[str, Any]:
    """
    Convert analysis into property identity payload.
    """

    components = analysis.components

    return {
        "raw_address": components.original,
        "street_address": components.street_line(include_unit=False) or None,
        "unit": (
            f"{components.unit_type or 'UNIT'} {components.unit_number}"
            if components.unit_number
            else None
        ),
        "municipality": components.municipality,
        "county": components.county,
        "state": components.state_code,
        "postal_code": components.postal_code,
        "normalized_address": analysis.canonical_address,
        "latitude": components.latitude,
        "longitude": components.longitude,
        "confidence": analysis.confidence,
        "match_quality": analysis.quality,
        "metadata": {
            "fingerprint": analysis.fingerprint,
            "match_key": analysis.match_key,
            "property_match_key": analysis.property_match_key,
            "public_record_search": analysis.public_record_search.to_dict(),
        },
    }


def analysis_to_observation_payload(
    analysis: AddressAnalysis,
) -> dict[str, Any]:
    """
    Create normalized observation payload for future persistence.
    """

    return {
        "field_path": "property.address",
        "value_type": "json",
        "value_json": analysis.to_dict(),
        "quality_status": analysis.quality,
        "confidence_score": analysis.confidence,
        "source_payload_hash": analysis.fingerprint,
    }


def apply_analysis_to_profile(
    profile: Any,
    analysis: AddressAnalysis,
    *,
    overwrite_existing: bool = False,
) -> Any:
    """
    Apply normalized address fields to a profile-like object.

    Duck typing avoids import cycles with property_intelligence.models.
    """

    components = analysis.components

    assignments = {
        "canonical_address": analysis.canonical_address,
        "address_line_1": components.street_line(include_unit=False),
        "address_line_2": (
            f"{components.unit_type or 'UNIT'} {components.unit_number}"
            if components.unit_number
            else None
        ),
        "city": components.municipality,
        "municipality": components.municipality,
        "county": components.county,
        "state_code": components.state_code,
        "postal_code": components.postal_code,
        "country_code": components.country_code,
        "latitude": components.latitude,
        "longitude": components.longitude,
        "block": components.block,
        "lot": components.lot,
        "qualifier": components.qualifier,
    }

    for attribute, value in assignments.items():
        if not hasattr(profile, attribute):
            continue

        current = getattr(profile, attribute)

        if overwrite_existing or current in (None, ""):
            setattr(profile, attribute, value)

    metadata = getattr(profile, "metadata", None) or getattr(
        profile,
        "metadata_json",
        None,
    )

    if isinstance(metadata, dict):
        metadata["address_intelligence"] = analysis.to_dict()

    return profile


# ============================================================
# SECTION 19 - DEFAULT SINGLETON AND CONVENIENCE API
# ============================================================

_default_engine = AddressIntelligenceEngine()


def analyze_address(
    raw_address: str,
    *,
    municipality: str | None = None,
    city: str | None = None,
    county: str | None = None,
    state_code: str | None = None,
    postal_code: str | None = None,
    owner_reference: str | None = None,
    country_code: str = DEFAULT_COUNTRY_CODE,
) -> AddressAnalysis:
    """
    Analyze address using default engine.
    """

    return _default_engine.analyze(
        raw_address,
        municipality=municipality,
        city=city,
        county=county,
        state_code=state_code,
        postal_code=postal_code,
        owner_reference=owner_reference,
        country_code=country_code,
    )


def normalize_address(raw_address: str, **kwargs: Any) -> str:
    """
    Return canonical normalized address.
    """

    return analyze_address(raw_address, **kwargs).canonical_address


def compare_addresses(
    left_address: str | AddressAnalysis,
    right_address: str | AddressAnalysis,
    *,
    match_threshold: float = 0.84,
) -> AddressMatchResult:
    """
    Compare addresses using default engine.
    """

    return _default_engine.compare(
        left_address,
        right_address,
        match_threshold=match_threshold,
    )


def address_fingerprint(raw_address: str, **kwargs: Any) -> str:
    """
    Return deterministic address fingerprint.
    """

    return analyze_address(raw_address, **kwargs).fingerprint


def prepare_public_record_search(
    raw_address: str,
    **kwargs: Any,
) -> PublicRecordSearchPreparation:
    """
    Analyze address and return public-record search preparation.
    """

    return analyze_address(raw_address, **kwargs).public_record_search


def make_property_intelligence_request_payload(
    raw_address: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Analyze address and return property-intelligence request payload.
    """

    analysis = analyze_address(raw_address, **kwargs)

    return _default_engine.to_property_intelligence_request_payload(analysis)


# ============================================================
# SECTION 20 - MODULE HEALTH AND DIAGNOSTICS
# ============================================================

def get_address_intelligence_metadata() -> dict[str, Any]:
    """
    Return module metadata.
    """

    return {
        "name": ADDRESS_INTELLIGENCE_ENGINE_NAME,
        "version": ADDRESS_INTELLIGENCE_ENGINE_VERSION,
        "phase": ADDRESS_INTELLIGENCE_ENGINE_PHASE,
        "status": ADDRESS_INTELLIGENCE_ENGINE_STATUS,
        "release_channel": ADDRESS_INTELLIGENCE_RELEASE_CHANNEL,
        "generated_at": utc_now(),
    }


def validate_address_intelligence_governance() -> dict[str, Any]:
    """
    Validate no-fabrication address governance.
    """

    issues: list[dict[str, Any]] = []

    false_keys = [
        "mock_property_facts_allowed",
        "fabricated_property_values_allowed",
        "fabricated_listing_status_allowed",
        "fabricated_owner_conclusions_allowed",
        "fabricated_sale_history_allowed",
        "address_intelligence_can_estimate_value",
        "address_intelligence_can_claim_listing_status",
        "address_intelligence_can_claim_public_records",
    ]

    for key in false_keys:
        if ADDRESS_INTELLIGENCE_GOVERNANCE.get(key):
            issues.append(
                {
                    "issue_code": f"{key}_must_remain_false",
                    "severity": "critical",
                    "message": f"{key} must remain False.",
                }
            )

    true_keys = [
        "address_intelligence_can_prepare_public_record_search",
        "manual_review_for_ambiguous_input",
        "manual_review_for_missing_search_signal",
        "source_attribution_required_downstream",
    ]

    for key in true_keys:
        if not ADDRESS_INTELLIGENCE_GOVERNANCE.get(key):
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


def get_address_intelligence_health() -> dict[str, Any]:
    """
    Return engine health.
    """

    governance = validate_address_intelligence_governance()

    sample = analyze_address(
        "43 Wetmore Ave, Morristown, NJ 07960"
    )

    return {
        "name": ADDRESS_INTELLIGENCE_ENGINE_NAME,
        "version": ADDRESS_INTELLIGENCE_ENGINE_VERSION,
        "phase": ADDRESS_INTELLIGENCE_ENGINE_PHASE,
        "status": ADDRESS_INTELLIGENCE_ENGINE_STATUS,
        "governance_valid": governance["valid"],
        "governance_issue_count": governance["issue_count"],
        "sample_address_quality": sample.quality,
        "sample_address_confidence": sample.confidence,
        "sample_public_record_routing_status": (
            sample.public_record_search.routing_status
        ),
        "sample_connector_targets": (
            sample.public_record_search.connector_targets
        ),
        "network_required": False,
        "mock_property_facts_allowed": False,
        "fabricated_listing_status_allowed": False,
        "fabricated_property_values_allowed": False,
        "generated_at": utc_now(),
    }


def get_address_intelligence_diagnostics() -> dict[str, Any]:
    """
    Return full diagnostics.
    """

    return {
        "metadata": get_address_intelligence_metadata(),
        "health": get_address_intelligence_health(),
        "governance": ADDRESS_INTELLIGENCE_GOVERNANCE.copy(),
        "governance_validation": validate_address_intelligence_governance(),
        "morris_county_municipality_count": len(MORRIS_COUNTY_MUNICIPALITIES),
        "morris_county_zip_hint_count": len(MORRIS_COUNTY_ZIP_HINTS),
        "connector_targets": [
            target.value
            for target in PublicRecordConnectorTarget
        ],
        "unsupported_public_record_claims": (
            PublicRecordSearchPreparer.UNSUPPORTED_WITH_PUBLIC_RECORDS_ONLY
        ),
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 21 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "ADDRESS_INTELLIGENCE_ENGINE_NAME",
    "ADDRESS_INTELLIGENCE_ENGINE_VERSION",
    "ADDRESS_INTELLIGENCE_ENGINE_PHASE",
    "ADDRESS_INTELLIGENCE_ENGINE_STATUS",
    "ADDRESS_INTELLIGENCE_RELEASE_CHANNEL",
    "ADDRESS_INTELLIGENCE_GOVERNANCE",
    "DEFAULT_COUNTRY_CODE",
    "DEFAULT_STATE_CODE",
    "DEFAULT_COUNTY",
    "MORRIS_COUNTY_MUNICIPALITIES",
    "MORRIS_COUNTY_ZIP_HINTS",
    "AddressInputType",
    "AddressQuality",
    "AddressMatchLevel",
    "AddressComponentStatus",
    "PublicRecordRoutingStatus",
    "PublicRecordConnectorTarget",
    "ManualReviewReason",
    "AddressIssue",
    "AddressComponents",
    "PublicRecordSearchPreparation",
    "AddressAnalysis",
    "AddressMatchResult",
    "BatchAddressResult",
    "utc_now",
    "safe_string",
    "normalize_text",
    "normalize_display_text",
    "normalize_identifier",
    "normalize_state",
    "normalize_county",
    "normalize_municipality",
    "normalize_postal_code",
    "normalize_suffix",
    "normalize_directional",
    "normalize_unit_type",
    "normalize_block_lot_value",
    "stable_hash",
    "clamp_confidence",
    "confidence_quality",
    "similarity",
    "AddressParser",
    "AddressValidator",
    "AddressConfidenceScorer",
    "AddressKeyBuilder",
    "PublicRecordSearchPreparer",
    "AddressMatcher",
    "AddressIntelligenceEngine",
    "BatchAddressProcessor",
    "analysis_to_public_record_search_payload",
    "analysis_to_property_identity_payload",
    "analysis_to_observation_payload",
    "apply_analysis_to_profile",
    "analyze_address",
    "normalize_address",
    "compare_addresses",
    "address_fingerprint",
    "prepare_public_record_search",
    "make_property_intelligence_request_payload",
    "get_address_intelligence_metadata",
    "validate_address_intelligence_governance",
    "get_address_intelligence_health",
    "get_address_intelligence_diagnostics",
]


# ============================================================
# END OF FILE
# ============================================================