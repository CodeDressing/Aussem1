"""
============================================================
AUSSEM REAL ESTATE
PHASE 5.10 - ADDRESS INTELLIGENCE ENGINE
FILE: app/property_intelligence/address_intelligence.py

PURPOSE:
Enterprise address normalization, parsing, validation, matching,
deduplication, confidence scoring, geographic enrichment preparation,
parcel-resolution support, and deterministic address fingerprinting for
the Aussem Real Estate property-intelligence platform.

DESIGN GOALS:
1. Work without paid APIs or network access.
2. Produce deterministic canonical address representations.
3. Preserve original input and parsing provenance.
4. Support U.S. residential real-estate workflows.
5. Handle common abbreviations, unit formats, punctuation, and casing.
6. Generate match keys for property/entity resolution.
7. Expose typed, testable service interfaces.
8. Remain compatible with future USPS, geocoder, parcel, and MLS adapters.
============================================================
"""

from __future__ import annotations

import enum
import hashlib
import json
import math
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any, Iterable, Mapping, Optional, Protocol, Sequence


# ============================================================
# SECTION 01 - CONSTANTS
# ============================================================

DEFAULT_COUNTRY_CODE = "US"
DEFAULT_CONFIDENCE = Decimal("0.50")
HIGH_CONFIDENCE = Decimal("0.90")
MEDIUM_CONFIDENCE = Decimal("0.70")
LOW_CONFIDENCE = Decimal("0.40")

WHITESPACE_RE = re.compile(r"\s+")
NON_ALNUM_SPACE_RE = re.compile(r"[^A-Z0-9#\-/ ]+")
ZIP_RE = re.compile(r"^(?P<zip5>\d{5})(?:[-\s]?(?P<zip4>\d{4}))?$")
HOUSE_NUMBER_RE = re.compile(
    r"^(?P<number>\d+[A-Z]?(?:-\d+[A-Z]?)?)(?:\s+|$)",
    re.IGNORECASE,
)
UNIT_RE = re.compile(
    r"(?:\s|,)+(?:APT|APARTMENT|UNIT|STE|SUITE|#)\s*([A-Z0-9\-]+)\s*$",
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


# ============================================================
# SECTION 02 - ENUMERATIONS
# ============================================================

class StringEnum(str, enum.Enum):
    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]


class AddressType(StringEnum):
    STREET = "street"
    PO_BOX = "po_box"
    RURAL_ROUTE = "rural_route"
    INTERSECTION = "intersection"
    LANDMARK = "landmark"
    UNKNOWN = "unknown"


class AddressQuality(StringEnum):
    VERIFIED = "verified"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class MatchLevel(StringEnum):
    EXACT = "exact"
    CANONICAL = "canonical"
    STREET = "street"
    PARCEL = "parcel"
    FUZZY = "fuzzy"
    NONE = "none"


class ComponentStatus(StringEnum):
    PRESENT = "present"
    NORMALIZED = "normalized"
    INFERRED = "inferred"
    MISSING = "missing"
    INVALID = "invalid"


class GeocodePrecision(StringEnum):
    ROOFTOP = "rooftop"
    PARCEL = "parcel"
    BUILDING = "building"
    STREET = "street"
    ZIP_CODE = "zip_code"
    CITY = "city"
    COUNTY = "county"
    STATE = "state"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 03 - NORMALIZATION TABLES
# ============================================================

STREET_SUFFIXES: dict[str, str] = {
    "ALLEY": "ALY",
    "ALLY": "ALY",
    "ALY": "ALY",
    "ANNEX": "ANX",
    "ANEX": "ANX",
    "ANX": "ANX",
    "ARCADE": "ARC",
    "ARC": "ARC",
    "AV": "AVE",
    "AVE": "AVE",
    "AVEN": "AVE",
    "AVENU": "AVE",
    "AVENUE": "AVE",
    "BAYOO": "BYU",
    "BAYOU": "BYU",
    "BEACH": "BCH",
    "BEND": "BND",
    "BLF": "BLF",
    "BLUFF": "BLF",
    "BLUFFS": "BLFS",
    "BOT": "BTM",
    "BOTTOM": "BTM",
    "BOUL": "BLVD",
    "BOULEVARD": "BLVD",
    "BR": "BR",
    "BRANCH": "BR",
    "BRDGE": "BRG",
    "BRIDGE": "BRG",
    "BROOK": "BRK",
    "BROOKS": "BRKS",
    "BURG": "BG",
    "BURGS": "BGS",
    "BYP": "BYP",
    "BYPASS": "BYP",
    "BYPA": "BYP",
    "CAMP": "CP",
    "CANYON": "CYN",
    "CAPE": "CPE",
    "CAUSEWAY": "CSWY",
    "CENTER": "CTR",
    "CENTERS": "CTRS",
    "CENTRE": "CTR",
    "CIRCLE": "CIR",
    "CIRCLES": "CIRS",
    "CLIFF": "CLF",
    "CLIFFS": "CLFS",
    "CLUB": "CLB",
    "COMMON": "CMN",
    "COMMONS": "CMNS",
    "CORNER": "COR",
    "CORNERS": "CORS",
    "COURSE": "CRSE",
    "COURT": "CT",
    "COURTS": "CTS",
    "COVE": "CV",
    "COVES": "CVS",
    "CREEK": "CRK",
    "CRESCENT": "CRES",
    "CREST": "CRST",
    "CROSSING": "XING",
    "CROSSROAD": "XRD",
    "CURVE": "CURV",
    "DALE": "DL",
    "DAM": "DM",
    "DIVIDE": "DV",
    "DR": "DR",
    "DRIVE": "DR",
    "DRIVES": "DRS",
    "ESTATE": "EST",
    "ESTATES": "ESTS",
    "EXPRESSWAY": "EXPY",
    "EXTENSION": "EXT",
    "EXTENSIONS": "EXTS",
    "FALL": "FALL",
    "FALLS": "FLS",
    "FERRY": "FRY",
    "FIELD": "FLD",
    "FIELDS": "FLDS",
    "FLAT": "FLT",
    "FLATS": "FLTS",
    "FORD": "FRD",
    "FORDS": "FRDS",
    "FOREST": "FRST",
    "FORGE": "FRG",
    "FORGES": "FRGS",
    "FORK": "FRK",
    "FORKS": "FRKS",
    "FORT": "FT",
    "FREEWAY": "FWY",
    "GARDEN": "GDN",
    "GARDENS": "GDNS",
    "GATEWAY": "GTWY",
    "GLEN": "GLN",
    "GLENS": "GLNS",
    "GREEN": "GRN",
    "GREENS": "GRNS",
    "GROVE": "GRV",
    "GROVES": "GRVS",
    "HARBOR": "HBR",
    "HARBORS": "HBRS",
    "HAVEN": "HVN",
    "HEIGHTS": "HTS",
    "HIGHWAY": "HWY",
    "HILL": "HL",
    "HILLS": "HLS",
    "HOLLOW": "HOLW",
    "INLET": "INLT",
    "ISLAND": "IS",
    "ISLANDS": "ISS",
    "ISLE": "ISLE",
    "JUNCTION": "JCT",
    "JUNCTIONS": "JCTS",
    "KEY": "KY",
    "KEYS": "KYS",
    "KNOLL": "KNL",
    "KNOLLS": "KNLS",
    "LAKE": "LK",
    "LAKES": "LKS",
    "LAND": "LAND",
    "LANDING": "LNDG",
    "LANE": "LN",
    "LIGHT": "LGT",
    "LIGHTS": "LGTS",
    "LOAF": "LF",
    "LOCK": "LCK",
    "LOCKS": "LCKS",
    "LODGE": "LDG",
    "LOOP": "LOOP",
    "MALL": "MALL",
    "MANOR": "MNR",
    "MANORS": "MNRS",
    "MEADOW": "MDW",
    "MEADOWS": "MDWS",
    "MEWS": "MEWS",
    "MILL": "ML",
    "MILLS": "MLS",
    "MISSION": "MSN",
    "MOTORWAY": "MTWY",
    "MOUNT": "MT",
    "MOUNTAIN": "MTN",
    "MOUNTAINS": "MTNS",
    "NECK": "NCK",
    "ORCHARD": "ORCH",
    "OVAL": "OVAL",
    "OVERPASS": "OPAS",
    "PARK": "PARK",
    "PARKS": "PARK",
    "PARKWAY": "PKWY",
    "PARKWAYS": "PKWY",
    "PASS": "PASS",
    "PASSAGE": "PSGE",
    "PATH": "PATH",
    "PIKE": "PIKE",
    "PINE": "PNE",
    "PINES": "PNES",
    "PLACE": "PL",
    "PLAIN": "PLN",
    "PLAINS": "PLNS",
    "PLAZA": "PLZ",
    "POINT": "PT",
    "POINTS": "PTS",
    "PORT": "PRT",
    "PORTS": "PRTS",
    "PRAIRIE": "PR",
    "RADIAL": "RADL",
    "RANCH": "RNCH",
    "RAPID": "RPD",
    "RAPIDS": "RPDS",
    "REST": "RST",
    "RIDGE": "RDG",
    "RIDGES": "RDGS",
    "RIVER": "RIV",
    "ROAD": "RD",
    "ROADS": "RDS",
    "ROUTE": "RTE",
    "ROW": "ROW",
    "RUE": "RUE",
    "RUN": "RUN",
    "SHOAL": "SHL",
    "SHOALS": "SHLS",
    "SHORE": "SHR",
    "SHORES": "SHRS",
    "SKYWAY": "SKWY",
    "SPRING": "SPG",
    "SPRINGS": "SPGS",
    "SPUR": "SPUR",
    "SPURS": "SPUR",
    "SQUARE": "SQ",
    "SQUARES": "SQS",
    "ST": "ST",
    "STATION": "STA",
    "STRAVENUE": "STRA",
    "STREAM": "STRM",
    "STREET": "ST",
    "STREETS": "STS",
    "SUMMIT": "SMT",
    "TERRACE": "TER",
    "THROUGHWAY": "TRWY",
    "TRACE": "TRCE",
    "TRACK": "TRAK",
    "TRAFFICWAY": "TRFY",
    "TRAIL": "TRL",
    "TRAILER": "TRLR",
    "TUNNEL": "TUNL",
    "TURNPIKE": "TPKE",
    "UNDERPASS": "UPAS",
    "UNION": "UN",
    "UNIONS": "UNS",
    "VALLEY": "VLY",
    "VALLEYS": "VLYS",
    "VIADUCT": "VIA",
    "VIEW": "VW",
    "VIEWS": "VWS",
    "VILLAGE": "VLG",
    "VILLAGES": "VLGS",
    "VILLE": "VL",
    "VISTA": "VIS",
    "WALK": "WALK",
    "WALKS": "WALK",
    "WALL": "WALL",
    "WAY": "WAY",
    "WAYS": "WAYS",
    "WELL": "WL",
    "WELLS": "WLS",
}

DIRECTIONALS: dict[str, str] = {
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
    "NORTH EAST": "NE",
    "NW": "NW",
    "NORTHWEST": "NW",
    "NORTH WEST": "NW",
    "SE": "SE",
    "SOUTHEAST": "SE",
    "SOUTH EAST": "SE",
    "SW": "SW",
    "SOUTHWEST": "SW",
    "SOUTH WEST": "SW",
}

UNIT_DESIGNATORS: dict[str, str] = {
    "APARTMENT": "APT",
    "APT": "APT",
    "BUILDING": "BLDG",
    "BLDG": "BLDG",
    "DEPARTMENT": "DEPT",
    "DEPT": "DEPT",
    "FLOOR": "FL",
    "FL": "FL",
    "HANGAR": "HNGR",
    "HNGR": "HNGR",
    "LOT": "LOT",
    "OFFICE": "OFC",
    "OFC": "OFC",
    "PENTHOUSE": "PH",
    "PH": "PH",
    "ROOM": "RM",
    "RM": "RM",
    "SPACE": "SPC",
    "SPC": "SPC",
    "STOP": "STOP",
    "SUITE": "STE",
    "STE": "STE",
    "TRAILER": "TRLR",
    "TRLR": "TRLR",
    "UNIT": "UNIT",
    "#": "UNIT",
}

STATE_CODES: dict[str, str] = {
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

VALID_STATE_CODES = frozenset(STATE_CODES.values())

NUMBER_WORDS: dict[str, str] = {
    "ZERO": "0",
    "ONE": "1",
    "TWO": "2",
    "THREE": "3",
    "FOUR": "4",
    "FIVE": "5",
    "SIX": "6",
    "SEVEN": "7",
    "EIGHT": "8",
    "NINE": "9",
    "TEN": "10",
    "ELEVEN": "11",
    "TWELVE": "12",
    "THIRTEEN": "13",
    "FOURTEEN": "14",
    "FIFTEEN": "15",
    "SIXTEEN": "16",
    "SEVENTEEN": "17",
    "EIGHTEEN": "18",
    "NINETEEN": "19",
    "TWENTY": "20",
}


# ============================================================
# SECTION 04 - DATA CONTRACTS
# ============================================================

@dataclass(slots=True)
class AddressComponents:
    original: str
    address_type: AddressType = AddressType.UNKNOWN
    house_number: Optional[str] = None
    predirectional: Optional[str] = None
    street_name: Optional[str] = None
    street_suffix: Optional[str] = None
    postdirectional: Optional[str] = None
    unit_type: Optional[str] = None
    unit_number: Optional[str] = None
    po_box: Optional[str] = None
    rural_route: Optional[str] = None
    rural_box: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    state_code: Optional[str] = None
    postal_code: Optional[str] = None
    postal_code_plus4: Optional[str] = None
    country_code: str = DEFAULT_COUNTRY_CODE
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    parcel_number: Optional[str] = None

    def street_line(self, include_unit: bool = True) -> str:
        if self.address_type == AddressType.PO_BOX and self.po_box:
            return f"PO BOX {self.po_box}"
        if self.address_type == AddressType.RURAL_ROUTE:
            pieces = ["RR", self.rural_route or "", "BOX", self.rural_box or ""]
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
        city_state = " ".join(
            value for value in [self.city, self.state_code] if value
        )
        postal = self.postal_code or ""
        if self.postal_code and self.postal_code_plus4:
            postal = f"{self.postal_code}-{self.postal_code_plus4}"
        return " ".join(value for value in [city_state, postal] if value)

    def canonical(self, include_unit: bool = True) -> str:
        return ", ".join(
            part
            for part in [
                self.street_line(include_unit=include_unit),
                self.city,
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
                self.country_code if self.country_code != DEFAULT_COUNTRY_CODE else None,
            ]
            if part
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["address_type"] = self.address_type.value
        for key in ("latitude", "longitude"):
            if result[key] is not None:
                result[key] = str(result[key])
        return result


@dataclass(slots=True)
class AddressIssue:
    code: str
    message: str
    severity: str = "warning"
    component: Optional[str] = None
    suggested_value: Optional[str] = None


@dataclass(slots=True)
class AddressAnalysis:
    components: AddressComponents
    quality: AddressQuality
    confidence: Decimal
    canonical_address: str
    normalized_street_address: str
    match_key: str
    property_match_key: str
    fingerprint: str
    issues: list[AddressIssue] = field(default_factory=list)
    transformations: list[str] = field(default_factory=list)
    component_status: dict[str, ComponentStatus] = field(default_factory=dict)
    provider_payload: dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        return self.quality != AddressQuality.INVALID

    def to_dict(self) -> dict[str, Any]:
        return {
            "components": self.components.to_dict(),
            "quality": self.quality.value,
            "confidence": str(self.confidence),
            "canonical_address": self.canonical_address,
            "normalized_street_address": self.normalized_street_address,
            "match_key": self.match_key,
            "property_match_key": self.property_match_key,
            "fingerprint": self.fingerprint,
            "issues": [asdict(issue) for issue in self.issues],
            "transformations": list(self.transformations),
            "component_status": {
                key: value.value for key, value in self.component_status.items()
            },
            "provider_payload": dict(self.provider_payload),
        }


@dataclass(slots=True)
class AddressMatchResult:
    level: MatchLevel
    score: Decimal
    is_match: bool
    component_scores: dict[str, Decimal]
    reasons: list[str]
    left: AddressAnalysis
    right: AddressAnalysis

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.value,
            "score": str(self.score),
            "is_match": self.is_match,
            "component_scores": {
                key: str(value) for key, value in self.component_scores.items()
            },
            "reasons": list(self.reasons),
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }


@dataclass(slots=True)
class GeocodeResult:
    latitude: Decimal
    longitude: Decimal
    precision: GeocodePrecision
    confidence: Decimal
    provider: str
    formatted_address: Optional[str] = None
    parcel_number: Optional[str] = None
    county: Optional[str] = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


# ============================================================
# SECTION 05 - PROVIDER PROTOCOLS
# ============================================================

class AddressValidationProvider(Protocol):
    name: str

    def validate(self, components: AddressComponents) -> Mapping[str, Any]:
        ...


class GeocodingProvider(Protocol):
    name: str

    def geocode(self, components: AddressComponents) -> Optional[GeocodeResult]:
        ...


class ParcelLookupProvider(Protocol):
    name: str

    def lookup_parcel(self, components: AddressComponents) -> Mapping[str, Any]:
        ...


# ============================================================
# SECTION 06 - LOW-LEVEL TEXT HELPERS
# ============================================================

def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(character for character in normalized if not unicodedata.combining(character))


def normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = strip_accents(str(value)).upper().strip()
    normalized = normalized.replace("’", "'").replace("`", "'")
    normalized = normalized.replace(".", " ")
    normalized = NON_ALNUM_SPACE_RE.sub(" ", normalized)
    normalized = WHITESPACE_RE.sub(" ", normalized).strip()
    return normalized or None


def normalize_identifier(value: Optional[str]) -> Optional[str]:
    normalized = normalize_text(value)
    if not normalized:
        return None
    return re.sub(r"[^A-Z0-9]", "", normalized)


def normalize_state(value: Optional[str]) -> Optional[str]:
    normalized = normalize_text(value)
    if not normalized:
        return None
    if normalized in VALID_STATE_CODES:
        return normalized
    return STATE_CODES.get(normalized)


def normalize_postal_code(value: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    normalized = normalize_text(value)
    if not normalized:
        return None, None
    compact = normalized.replace(" ", "")
    match = ZIP_RE.match(compact)
    if not match:
        return None, None
    return match.group("zip5"), match.group("zip4")


def normalize_unit_type(value: Optional[str]) -> Optional[str]:
    normalized = normalize_text(value)
    if not normalized:
        return None
    return UNIT_DESIGNATORS.get(normalized, normalized)


def normalize_directional(value: Optional[str]) -> Optional[str]:
    normalized = normalize_text(value)
    if not normalized:
        return None
    return DIRECTIONALS.get(normalized, normalized)


def normalize_suffix(value: Optional[str]) -> Optional[str]:
    normalized = normalize_text(value)
    if not normalized:
        return None
    return STREET_SUFFIXES.get(normalized, normalized)


def stable_hash(value: Any) -> str:
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def clamp_score(value: Decimal) -> Decimal:
    return max(Decimal("0"), min(Decimal("1"), value))


def levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for index_left, char_left in enumerate(left, start=1):
        current = [index_left]
        for index_right, char_right in enumerate(right, start=1):
            insert_cost = current[index_right - 1] + 1
            delete_cost = previous[index_right] + 1
            substitute_cost = previous[index_right - 1] + (char_left != char_right)
            current.append(min(insert_cost, delete_cost, substitute_cost))
        previous = current
    return previous[-1]


def similarity(left: Optional[str], right: Optional[str]) -> Decimal:
    left_value = normalize_text(left) or ""
    right_value = normalize_text(right) or ""
    if not left_value and not right_value:
        return Decimal("1")
    if not left_value or not right_value:
        return Decimal("0")
    distance = levenshtein_distance(left_value, right_value)
    maximum = max(len(left_value), len(right_value))
    return clamp_score(Decimal("1") - (Decimal(distance) / Decimal(maximum)))


# ============================================================
# SECTION 07 - ADDRESS PARSER
# ============================================================

class AddressParser:
    """Deterministic parser for common U.S. property-address formats."""

    def parse(
        self,
        raw_address: str,
        *,
        city: Optional[str] = None,
        state_code: Optional[str] = None,
        postal_code: Optional[str] = None,
        county: Optional[str] = None,
        country_code: str = DEFAULT_COUNTRY_CODE,
    ) -> AddressComponents:
        if not raw_address or not str(raw_address).strip():
            raise ValueError("raw_address is required")

        original = str(raw_address).strip()
        normalized = normalize_text(original) or ""
        inline_street, inline_city, inline_state, inline_zip = self._split_full_address(normalized)

        city_value = normalize_text(city) or inline_city
        state_value = normalize_state(state_code) or normalize_state(inline_state)
        zip5, zip4 = normalize_postal_code(postal_code or inline_zip)

        po_box = PO_BOX_RE.match(inline_street)
        if po_box:
            return AddressComponents(
                original=original,
                address_type=AddressType.PO_BOX,
                po_box=po_box.group(1),
                city=city_value,
                county=normalize_text(county),
                state_code=state_value,
                postal_code=zip5,
                postal_code_plus4=zip4,
                country_code=normalize_text(country_code) or DEFAULT_COUNTRY_CODE,
            )

        rural = RURAL_ROUTE_RE.match(inline_street)
        if rural:
            return AddressComponents(
                original=original,
                address_type=AddressType.RURAL_ROUTE,
                rural_route=rural.group(1),
                rural_box=rural.group(2),
                city=city_value,
                county=normalize_text(county),
                state_code=state_value,
                postal_code=zip5,
                postal_code_plus4=zip4,
                country_code=normalize_text(country_code) or DEFAULT_COUNTRY_CODE,
            )

        if " & " in f" {inline_street} " or " AND " in f" {inline_street} ":
            return AddressComponents(
                original=original,
                address_type=AddressType.INTERSECTION,
                street_name=inline_street,
                city=city_value,
                county=normalize_text(county),
                state_code=state_value,
                postal_code=zip5,
                postal_code_plus4=zip4,
                country_code=normalize_text(country_code) or DEFAULT_COUNTRY_CODE,
            )

        return self._parse_street(
            original=original,
            street_line=inline_street,
            city=city_value,
            county=normalize_text(county),
            state_code=state_value,
            zip5=zip5,
            zip4=zip4,
            country_code=normalize_text(country_code) or DEFAULT_COUNTRY_CODE,
        )

    def _split_full_address(
        self,
        normalized: str,
    ) -> tuple[str, Optional[str], Optional[str], Optional[str]]:
        parts = [part.strip() for part in normalized.split(",") if part.strip()]

        if len(parts) >= 3:
            street = parts[0]
            city = parts[1]
            state_zip = " ".join(parts[2:])
            state, postal = self._split_state_zip(state_zip)
            return street, city, state, postal

        tokens = normalized.split()
        if len(tokens) >= 3:
            possible_zip = tokens[-1]
            zip5, _ = normalize_postal_code(possible_zip)
            if zip5:
                possible_state = tokens[-2]
                state = normalize_state(possible_state)
                if state:
                    body = tokens[:-2]
                    if len(body) >= 3:
                        street_end = self._guess_street_end(body)
                        street = " ".join(body[:street_end])
                        city = " ".join(body[street_end:]) or None
                        return street, city, state, possible_zip

        return normalized, None, None, None

    @staticmethod
    def _split_state_zip(value: str) -> tuple[Optional[str], Optional[str]]:
        tokens = value.split()
        if not tokens:
            return None, None
        if len(tokens) == 1:
            state = normalize_state(tokens[0])
            if state:
                return state, None
            zip5, _ = normalize_postal_code(tokens[0])
            return None, tokens[0] if zip5 else None

        postal = tokens[-1]
        state_text = " ".join(tokens[:-1])
        state = normalize_state(state_text)
        zip5, _ = normalize_postal_code(postal)
        if state:
            return state, postal if zip5 else None

        state = normalize_state(tokens[0])
        return state, postal if zip5 else None

    @staticmethod
    def _guess_street_end(tokens: Sequence[str]) -> int:
        for index, token in enumerate(tokens):
            if normalize_suffix(token) in set(STREET_SUFFIXES.values()):
                return index + 1
        return min(3, len(tokens))

    def _parse_street(
        self,
        *,
        original: str,
        street_line: str,
        city: Optional[str],
        county: Optional[str],
        state_code: Optional[str],
        zip5: Optional[str],
        zip4: Optional[str],
        country_code: str,
    ) -> AddressComponents:
        unit_type, unit_number, without_unit = self._extract_unit(street_line)
        number_match = HOUSE_NUMBER_RE.match(without_unit)
        house_number = number_match.group("number").upper() if number_match else None
        remaining = (
            without_unit[number_match.end():].strip()
            if number_match
            else without_unit.strip()
        )

        tokens = remaining.split()
        predirectional = None
        postdirectional = None
        suffix = None

        if tokens and normalize_directional(tokens[0]) in DIRECTIONALS.values():
            predirectional = normalize_directional(tokens.pop(0))

        if tokens and normalize_directional(tokens[-1]) in DIRECTIONALS.values():
            postdirectional = normalize_directional(tokens.pop())

        if tokens and normalize_suffix(tokens[-1]) in STREET_SUFFIXES.values():
            suffix = normalize_suffix(tokens.pop())

        street_name = " ".join(tokens) or None

        return AddressComponents(
            original=original,
            address_type=AddressType.STREET,
            house_number=house_number,
            predirectional=predirectional,
            street_name=street_name,
            street_suffix=suffix,
            postdirectional=postdirectional,
            unit_type=unit_type,
            unit_number=unit_number,
            city=city,
            county=county,
            state_code=state_code,
            postal_code=zip5,
            postal_code_plus4=zip4,
            country_code=country_code,
        )

    @staticmethod
    def _extract_unit(street_line: str) -> tuple[Optional[str], Optional[str], str]:
        match = UNIT_RE.search(street_line)
        if not match:
            return None, None, street_line

        matched_text = match.group(0).strip()
        unit_number = match.group(1).upper()
        prefix = matched_text[: matched_text.upper().find(unit_number)].strip(" ,")
        unit_type = normalize_unit_type(prefix or "UNIT")
        without_unit = street_line[: match.start()].strip(" ,")
        return unit_type, unit_number, without_unit


# ============================================================
# SECTION 08 - ADDRESS VALIDATOR
# ============================================================

class AddressValidator:
    def validate(self, components: AddressComponents) -> list[AddressIssue]:
        issues: list[AddressIssue] = []

        if components.address_type == AddressType.STREET:
            if not components.house_number:
                issues.append(
                    AddressIssue(
                        code="missing_house_number",
                        message="Street address is missing a house number.",
                        severity="error",
                        component="house_number",
                    )
                )
            if not components.street_name:
                issues.append(
                    AddressIssue(
                        code="missing_street_name",
                        message="Street address is missing a street name.",
                        severity="error",
                        component="street_name",
                    )
                )

        if components.address_type == AddressType.PO_BOX and not components.po_box:
            issues.append(
                AddressIssue(
                    code="missing_po_box",
                    message="PO Box address is missing its box number.",
                    severity="error",
                    component="po_box",
                )
            )

        if components.state_code and components.state_code not in VALID_STATE_CODES:
            issues.append(
                AddressIssue(
                    code="invalid_state",
                    message="State code is not recognized.",
                    severity="error",
                    component="state_code",
                )
            )

        if components.postal_code and not ZIP_RE.match(
            components.postal_code
            + (
                f"-{components.postal_code_plus4}"
                if components.postal_code_plus4
                else ""
            )
        ):
            issues.append(
                AddressIssue(
                    code="invalid_postal_code",
                    message="Postal code is not a valid ZIP or ZIP+4 format.",
                    severity="error",
                    component="postal_code",
                )
            )

        if components.latitude is not None and not (
            Decimal("-90") <= components.latitude <= Decimal("90")
        ):
            issues.append(
                AddressIssue(
                    code="invalid_latitude",
                    message="Latitude must be between -90 and 90.",
                    severity="error",
                    component="latitude",
                )
            )

        if components.longitude is not None and not (
            Decimal("-180") <= components.longitude <= Decimal("180")
        ):
            issues.append(
                AddressIssue(
                    code="invalid_longitude",
                    message="Longitude must be between -180 and 180.",
                    severity="error",
                    component="longitude",
                )
            )

        if not components.city:
            issues.append(
                AddressIssue(
                    code="missing_city",
                    message="City is missing.",
                    severity="warning",
                    component="city",
                )
            )

        if not components.state_code:
            issues.append(
                AddressIssue(
                    code="missing_state",
                    message="State is missing.",
                    severity="warning",
                    component="state_code",
                )
            )

        if not components.postal_code:
            issues.append(
                AddressIssue(
                    code="missing_postal_code",
                    message="Postal code is missing.",
                    severity="warning",
                    component="postal_code",
                )
            )

        return issues


# ============================================================
# SECTION 09 - CONFIDENCE SCORING
# ============================================================

class AddressConfidenceScorer:
    COMPONENT_WEIGHTS: Mapping[str, Decimal] = {
        "house_number": Decimal("0.20"),
        "street_name": Decimal("0.25"),
        "street_suffix": Decimal("0.08"),
        "city": Decimal("0.15"),
        "state_code": Decimal("0.12"),
        "postal_code": Decimal("0.15"),
        "unit_number": Decimal("0.05"),
    }

    def score(
        self,
        components: AddressComponents,
        issues: Sequence[AddressIssue],
        *,
        provider_verified: bool = False,
        geocoded: bool = False,
        parcel_resolved: bool = False,
    ) -> Decimal:
        score = Decimal("0")
        for component, weight in self.COMPONENT_WEIGHTS.items():
            if getattr(components, component, None):
                score += weight

        for issue in issues:
            if issue.severity == "error":
                score -= Decimal("0.18")
            elif issue.severity == "warning":
                score -= Decimal("0.04")

        if provider_verified:
            score += Decimal("0.10")
        if geocoded:
            score += Decimal("0.06")
        if parcel_resolved:
            score += Decimal("0.08")

        return clamp_score(score.quantize(Decimal("0.000001")))

    @staticmethod
    def quality(score: Decimal, issues: Sequence[AddressIssue]) -> AddressQuality:
        if any(issue.severity == "error" for issue in issues):
            return AddressQuality.INVALID
        if score >= Decimal("0.95"):
            return AddressQuality.VERIFIED
        if score >= Decimal("0.82"):
            return AddressQuality.HIGH
        if score >= Decimal("0.62"):
            return AddressQuality.MEDIUM
        if score > Decimal("0"):
            return AddressQuality.LOW
        return AddressQuality.UNKNOWN


# ============================================================
# SECTION 10 - KEY AND FINGERPRINT GENERATION
# ============================================================

class AddressKeyBuilder:
    @staticmethod
    def match_key(components: AddressComponents, *, include_unit: bool = True) -> str:
        values = [
            components.house_number,
            components.predirectional,
            components.street_name,
            components.street_suffix,
            components.postdirectional,
            components.unit_type if include_unit else None,
            components.unit_number if include_unit else None,
            components.city,
            components.state_code,
            components.postal_code,
        ]
        return "|".join(normalize_identifier(value) or "" for value in values)

    @staticmethod
    def property_match_key(components: AddressComponents) -> str:
        return AddressKeyBuilder.match_key(components, include_unit=False)

    @staticmethod
    def parcel_key(components: AddressComponents) -> Optional[str]:
        if not components.parcel_number:
            return None
        return "|".join(
            value
            for value in [
                normalize_identifier(components.state_code),
                normalize_identifier(components.county),
                normalize_identifier(components.parcel_number),
            ]
            if value
        )

    @staticmethod
    def fingerprint(components: AddressComponents) -> str:
        return stable_hash(
            {
                "property_match_key": AddressKeyBuilder.property_match_key(components),
                "unit": normalize_identifier(components.unit_number),
                "parcel": AddressKeyBuilder.parcel_key(components),
                "country": normalize_identifier(components.country_code),
            }
        )


# ============================================================
# SECTION 11 - ADDRESS MATCHER
# ============================================================

class AddressMatcher:
    WEIGHTS: Mapping[str, Decimal] = {
        "house_number": Decimal("0.24"),
        "street_name": Decimal("0.26"),
        "street_suffix": Decimal("0.06"),
        "city": Decimal("0.12"),
        "state_code": Decimal("0.10"),
        "postal_code": Decimal("0.14"),
        "unit_number": Decimal("0.08"),
    }

    def compare(
        self,
        left: AddressAnalysis,
        right: AddressAnalysis,
        *,
        match_threshold: Decimal = Decimal("0.84"),
    ) -> AddressMatchResult:
        left_components = left.components
        right_components = right.components
        reasons: list[str] = []

        if (
            left_components.parcel_number
            and right_components.parcel_number
            and normalize_identifier(left_components.parcel_number)
            == normalize_identifier(right_components.parcel_number)
        ):
            return AddressMatchResult(
                level=MatchLevel.PARCEL,
                score=Decimal("1"),
                is_match=True,
                component_scores={"parcel_number": Decimal("1")},
                reasons=["Parcel numbers match exactly."],
                left=left,
                right=right,
            )

        if left.fingerprint == right.fingerprint:
            return AddressMatchResult(
                level=MatchLevel.EXACT,
                score=Decimal("1"),
                is_match=True,
                component_scores={"fingerprint": Decimal("1")},
                reasons=["Canonical address fingerprints are identical."],
                left=left,
                right=right,
            )

        component_scores: dict[str, Decimal] = {}
        weighted_total = Decimal("0")
        available_weight = Decimal("0")

        for component, weight in self.WEIGHTS.items():
            left_value = getattr(left_components, component)
            right_value = getattr(right_components, component)

            if left_value is None and right_value is None:
                continue

            component_score = similarity(
                str(left_value) if left_value is not None else None,
                str(right_value) if right_value is not None else None,
            )
            component_scores[component] = component_score
            weighted_total += component_score * weight
            available_weight += weight

        total_score = (
            weighted_total / available_weight
            if available_weight
            else Decimal("0")
        )

        if left.property_match_key == right.property_match_key:
            level = MatchLevel.CANONICAL
            total_score = max(total_score, Decimal("0.96"))
            reasons.append("Property-level canonical keys match.")
        elif (
            component_scores.get("house_number", Decimal("0")) == Decimal("1")
            and component_scores.get("street_name", Decimal("0")) >= Decimal("0.90")
            and component_scores.get("state_code", Decimal("0")) == Decimal("1")
        ):
            level = MatchLevel.STREET
            reasons.append("House number, street name, and state strongly agree.")
        elif total_score >= match_threshold:
            level = MatchLevel.FUZZY
            reasons.append("Weighted component similarity exceeds the match threshold.")
        else:
            level = MatchLevel.NONE
            reasons.append("Address similarity is below the match threshold.")

        if (
            left_components.unit_number
            and right_components.unit_number
            and normalize_identifier(left_components.unit_number)
            != normalize_identifier(right_components.unit_number)
        ):
            total_score -= Decimal("0.12")
            reasons.append("Unit numbers conflict.")

        total_score = clamp_score(total_score.quantize(Decimal("0.000001")))

        return AddressMatchResult(
            level=level,
            score=total_score,
            is_match=total_score >= match_threshold and level != MatchLevel.NONE,
            component_scores=component_scores,
            reasons=reasons,
            left=left,
            right=right,
        )


# ============================================================
# SECTION 12 - GEOGRAPHIC UTILITIES
# ============================================================

class GeoMath:
    EARTH_RADIUS_MILES = 3958.7613

    @classmethod
    def haversine_miles(
        cls,
        latitude_1: Decimal | float,
        longitude_1: Decimal | float,
        latitude_2: Decimal | float,
        longitude_2: Decimal | float,
    ) -> Decimal:
        lat1 = math.radians(float(latitude_1))
        lon1 = math.radians(float(longitude_1))
        lat2 = math.radians(float(latitude_2))
        lon2 = math.radians(float(longitude_2))

        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        value = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1)
            * math.cos(lat2)
            * math.sin(delta_lon / 2) ** 2
        )
        distance = 2 * cls.EARTH_RADIUS_MILES * math.asin(math.sqrt(value))
        return Decimal(str(round(distance, 6)))

    @staticmethod
    def bounding_box(
        latitude: Decimal | float,
        longitude: Decimal | float,
        radius_miles: Decimal | float,
    ) -> dict[str, Decimal]:
        latitude = float(latitude)
        longitude = float(longitude)
        radius = float(radius_miles)

        latitude_delta = radius / 69.0
        longitude_scale = max(math.cos(math.radians(latitude)), 0.01)
        longitude_delta = radius / (69.172 * longitude_scale)

        return {
            "minimum_latitude": Decimal(str(latitude - latitude_delta)),
            "maximum_latitude": Decimal(str(latitude + latitude_delta)),
            "minimum_longitude": Decimal(str(longitude - longitude_delta)),
            "maximum_longitude": Decimal(str(longitude + longitude_delta)),
        }


# ============================================================
# SECTION 13 - ADDRESS INTELLIGENCE ENGINE
# ============================================================

class AddressIntelligenceEngine:
    """
    High-level orchestration service.

    Network-backed providers are optional. The deterministic parser,
    normalization, validation, fingerprinting, and matching pipeline works
    independently and can be used in tests, ingestion jobs, API routes, and
    database services.
    """

    def __init__(
        self,
        *,
        parser: Optional[AddressParser] = None,
        validator: Optional[AddressValidator] = None,
        scorer: Optional[AddressConfidenceScorer] = None,
        matcher: Optional[AddressMatcher] = None,
        validation_providers: Optional[Sequence[AddressValidationProvider]] = None,
        geocoding_providers: Optional[Sequence[GeocodingProvider]] = None,
        parcel_providers: Optional[Sequence[ParcelLookupProvider]] = None,
    ) -> None:
        self.parser = parser or AddressParser()
        self.validator = validator or AddressValidator()
        self.scorer = scorer or AddressConfidenceScorer()
        self.matcher = matcher or AddressMatcher()
        self.validation_providers = list(validation_providers or [])
        self.geocoding_providers = list(geocoding_providers or [])
        self.parcel_providers = list(parcel_providers or [])

    def analyze(
        self,
        raw_address: str,
        *,
        city: Optional[str] = None,
        state_code: Optional[str] = None,
        postal_code: Optional[str] = None,
        county: Optional[str] = None,
        country_code: str = DEFAULT_COUNTRY_CODE,
        enrich: bool = False,
    ) -> AddressAnalysis:
        components = self.parser.parse(
            raw_address,
            city=city,
            state_code=state_code,
            postal_code=postal_code,
            county=county,
            country_code=country_code,
        )
        transformations = self._build_transformations(raw_address, components)
        provider_payload: dict[str, Any] = {}

        provider_verified = False
        geocoded = False
        parcel_resolved = False

        if enrich:
            provider_verified = self._run_validation_providers(
                components,
                provider_payload,
            )
            geocoded = self._run_geocoding_providers(
                components,
                provider_payload,
            )
            parcel_resolved = self._run_parcel_providers(
                components,
                provider_payload,
            )

        issues = self.validator.validate(components)
        confidence = self.scorer.score(
            components,
            issues,
            provider_verified=provider_verified,
            geocoded=geocoded,
            parcel_resolved=parcel_resolved,
        )
        quality = self.scorer.quality(confidence, issues)

        canonical_address = components.canonical(include_unit=True)
        normalized_street_address = components.street_line(include_unit=True)
        match_key = AddressKeyBuilder.match_key(components, include_unit=True)
        property_match_key = AddressKeyBuilder.property_match_key(components)
        fingerprint = AddressKeyBuilder.fingerprint(components)

        return AddressAnalysis(
            components=components,
            quality=quality,
            confidence=confidence,
            canonical_address=canonical_address,
            normalized_street_address=normalized_street_address,
            match_key=match_key,
            property_match_key=property_match_key,
            fingerprint=fingerprint,
            issues=issues,
            transformations=transformations,
            component_status=self._component_status(components),
            provider_payload=provider_payload,
        )

    def compare(
        self,
        left_address: str | AddressAnalysis,
        right_address: str | AddressAnalysis,
        *,
        match_threshold: Decimal = Decimal("0.84"),
    ) -> AddressMatchResult:
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
        match_threshold: Decimal = Decimal("0.90"),
    ) -> list[list[AddressAnalysis]]:
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

    def _run_validation_providers(
        self,
        components: AddressComponents,
        payload: dict[str, Any],
    ) -> bool:
        verified = False
        for provider in self.validation_providers:
            try:
                result = dict(provider.validate(components))
                payload[f"validation:{provider.name}"] = result
                if result.get("verified") is True:
                    verified = True
                self._merge_provider_components(components, result)
            except Exception as exc:
                payload[f"validation:{provider.name}"] = {
                    "error": str(exc),
                    "provider": provider.name,
                }
        return verified

    def _run_geocoding_providers(
        self,
        components: AddressComponents,
        payload: dict[str, Any],
    ) -> bool:
        for provider in self.geocoding_providers:
            try:
                result = provider.geocode(components)
                if result is None:
                    continue

                components.latitude = result.latitude
                components.longitude = result.longitude
                components.parcel_number = (
                    components.parcel_number or result.parcel_number
                )
                components.county = components.county or normalize_text(result.county)

                payload[f"geocode:{provider.name}"] = {
                    "latitude": str(result.latitude),
                    "longitude": str(result.longitude),
                    "precision": result.precision.value,
                    "confidence": str(result.confidence),
                    "formatted_address": result.formatted_address,
                    "parcel_number": result.parcel_number,
                    "county": result.county,
                    "raw_payload": result.raw_payload,
                }
                return True
            except Exception as exc:
                payload[f"geocode:{provider.name}"] = {
                    "error": str(exc),
                    "provider": provider.name,
                }
        return False

    def _run_parcel_providers(
        self,
        components: AddressComponents,
        payload: dict[str, Any],
    ) -> bool:
        for provider in self.parcel_providers:
            try:
                result = dict(provider.lookup_parcel(components))
                payload[f"parcel:{provider.name}"] = result

                parcel_number = result.get("parcel_number")
                if parcel_number:
                    components.parcel_number = normalize_text(str(parcel_number))
                    if result.get("county") and not components.county:
                        components.county = normalize_text(str(result["county"]))
                    return True
            except Exception as exc:
                payload[f"parcel:{provider.name}"] = {
                    "error": str(exc),
                    "provider": provider.name,
                }
        return False

    @staticmethod
    def _merge_provider_components(
        components: AddressComponents,
        result: Mapping[str, Any],
    ) -> None:
        field_map = {
            "house_number": "house_number",
            "predirectional": "predirectional",
            "street_name": "street_name",
            "street_suffix": "street_suffix",
            "postdirectional": "postdirectional",
            "unit_type": "unit_type",
            "unit_number": "unit_number",
            "city": "city",
            "county": "county",
            "state_code": "state_code",
            "postal_code": "postal_code",
            "postal_code_plus4": "postal_code_plus4",
        }
        for source_key, target_key in field_map.items():
            value = result.get(source_key)
            if value not in (None, ""):
                setattr(components, target_key, normalize_text(str(value)))

        components.state_code = normalize_state(components.state_code)
        components.street_suffix = normalize_suffix(components.street_suffix)
        components.predirectional = normalize_directional(components.predirectional)
        components.postdirectional = normalize_directional(components.postdirectional)
        components.unit_type = normalize_unit_type(components.unit_type)

    @staticmethod
    def _build_transformations(
        original: str,
        components: AddressComponents,
    ) -> list[str]:
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

        return transformations

    @staticmethod
    def _component_status(
        components: AddressComponents,
    ) -> dict[str, ComponentStatus]:
        result: dict[str, ComponentStatus] = {}
        fields = [
            "house_number",
            "predirectional",
            "street_name",
            "street_suffix",
            "postdirectional",
            "unit_type",
            "unit_number",
            "city",
            "county",
            "state_code",
            "postal_code",
            "postal_code_plus4",
            "latitude",
            "longitude",
            "parcel_number",
        ]
        for field_name in fields:
            value = getattr(components, field_name)
            result[field_name] = (
                ComponentStatus.PRESENT
                if value not in (None, "")
                else ComponentStatus.MISSING
            )
        return result


# ============================================================
# SECTION 14 - MODEL INTEGRATION HELPERS
# ============================================================

def apply_analysis_to_profile(
    profile: Any,
    analysis: AddressAnalysis,
    *,
    overwrite_existing: bool = False,
) -> Any:
    """
    Apply normalized address fields to a PropertyIntelligenceProfile-like object.

    The helper uses duck typing so this module does not create an import cycle
    with app.property_intelligence.models.
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
        "city": components.city,
        "county": components.county,
        "state_code": components.state_code,
        "postal_code": components.postal_code,
        "country_code": components.country_code,
        "latitude": components.latitude,
        "longitude": components.longitude,
        "parcel_number": components.parcel_number,
    }

    for attribute, value in assignments.items():
        if not hasattr(profile, attribute):
            continue
        current = getattr(profile, attribute)
        if overwrite_existing or current in (None, ""):
            setattr(profile, attribute, value)

    metadata = getattr(profile, "metadata_json", None)
    if isinstance(metadata, dict):
        metadata["address_intelligence"] = {
            "quality": analysis.quality.value,
            "confidence": str(analysis.confidence),
            "match_key": analysis.match_key,
            "property_match_key": analysis.property_match_key,
            "fingerprint": analysis.fingerprint,
            "issues": [asdict(issue) for issue in analysis.issues],
            "transformations": analysis.transformations,
        }

    return profile


def analysis_to_observation_payload(
    analysis: AddressAnalysis,
) -> dict[str, Any]:
    """Create a normalized payload suitable for a PropertyObservation record."""
    return {
        "field_path": "property.address",
        "value_type": "json",
        "value_json": analysis.to_dict(),
        "quality_status": analysis.quality.value,
        "confidence_score": str(analysis.confidence),
        "source_payload_hash": analysis.fingerprint,
    }


# ============================================================
# SECTION 15 - BATCH OPERATIONS
# ============================================================

@dataclass(slots=True)
class BatchAddressResult:
    total: int
    valid: int
    invalid: int
    duplicate_groups: int
    analyses: list[AddressAnalysis]
    groups: list[list[AddressAnalysis]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "valid": self.valid,
            "invalid": self.invalid,
            "duplicate_groups": self.duplicate_groups,
            "analyses": [analysis.to_dict() for analysis in self.analyses],
            "groups": [
                [analysis.to_dict() for analysis in group]
                for group in self.groups
            ],
        }


class BatchAddressProcessor:
    def __init__(self, engine: Optional[AddressIntelligenceEngine] = None) -> None:
        self.engine = engine or AddressIntelligenceEngine()

    def process(
        self,
        addresses: Iterable[str],
        *,
        deduplicate: bool = True,
        match_threshold: Decimal = Decimal("0.90"),
    ) -> BatchAddressResult:
        analyses = [self.engine.analyze(address) for address in addresses]
        groups = (
            self.engine.deduplicate(
                [analysis.components.original for analysis in analyses],
                match_threshold=match_threshold,
            )
            if deduplicate
            else [[analysis] for analysis in analyses]
        )

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
# SECTION 16 - DEFAULT SINGLETON AND CONVENIENCE API
# ============================================================

_default_engine = AddressIntelligenceEngine()


def analyze_address(
    raw_address: str,
    *,
    city: Optional[str] = None,
    state_code: Optional[str] = None,
    postal_code: Optional[str] = None,
    county: Optional[str] = None,
    country_code: str = DEFAULT_COUNTRY_CODE,
    enrich: bool = False,
) -> AddressAnalysis:
    return _default_engine.analyze(
        raw_address,
        city=city,
        state_code=state_code,
        postal_code=postal_code,
        county=county,
        country_code=country_code,
        enrich=enrich,
    )


def normalize_address(raw_address: str, **kwargs: Any) -> str:
    return analyze_address(raw_address, **kwargs).canonical_address


def compare_addresses(
    left_address: str | AddressAnalysis,
    right_address: str | AddressAnalysis,
    *,
    match_threshold: Decimal = Decimal("0.84"),
) -> AddressMatchResult:
    return _default_engine.compare(
        left_address,
        right_address,
        match_threshold=match_threshold,
    )


def address_fingerprint(raw_address: str, **kwargs: Any) -> str:
    return analyze_address(raw_address, **kwargs).fingerprint


# ============================================================
# SECTION 17 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "AddressType",
    "AddressQuality",
    "MatchLevel",
    "ComponentStatus",
    "GeocodePrecision",
    "AddressComponents",
    "AddressIssue",
    "AddressAnalysis",
    "AddressMatchResult",
    "GeocodeResult",
    "AddressValidationProvider",
    "GeocodingProvider",
    "ParcelLookupProvider",
    "AddressParser",
    "AddressValidator",
    "AddressConfidenceScorer",
    "AddressKeyBuilder",
    "AddressMatcher",
    "GeoMath",
    "AddressIntelligenceEngine",
    "BatchAddressResult",
    "BatchAddressProcessor",
    "apply_analysis_to_profile",
    "analysis_to_observation_payload",
    "analyze_address",
    "normalize_address",
    "compare_addresses",
    "address_fingerprint",
]
