# ============================================================
# AUSSEM1
# PHASE 2.20 PART 2.00
# ENTERPRISE PUBLIC RECORDS MODELS
# FILE: app/public_records/models.py
# PURPOSE:
# Define the official public-record data models used by Aussem1
# for parcel records, tax assessments, property taxes, deeds,
# mortgages, liens, sale-history references, GIS parcel context,
# MOD-IV assessment context, connector results, source attribution,
# confidence scoring, and public-record intelligence reports.
#
# This file contains no mock property data.
# This file contains no fake homes.
# This file contains no fake valuations.
# This file contains no fake sale history.
# This file contains no fake active listing status.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# REAL PUBLIC RECORDS MODELS ACTIVE
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

from app.sources.source_models import SourceAttribution
from app.sources.source_models import SourceConfidenceBand
from app.sources.source_models import SourceConfidenceReport
from app.sources.source_models import SourceError
from app.sources.source_models import SourceErrorType
from app.sources.source_models import SourceField
from app.sources.source_models import SourceRecordReference
from app.sources.source_models import SourceResult
from app.sources.source_models import SourceStatus
from app.sources.source_models import SourceTimestamp
from app.sources.source_models import SourceWarning
from app.sources.source_models import clamp_confidence
from app.sources.source_models import confidence_band


# ============================================================
# SECTION 02 - MODULE METADATA
# ============================================================

PUBLIC_RECORD_MODELS_NAME = "Aussem1 Enterprise Public Records Models"

PUBLIC_RECORD_MODELS_VERSION = "0.1.0"

PUBLIC_RECORD_MODELS_PHASE = "PHASE 2.20 PART 2.00"

PUBLIC_RECORD_MODELS_STATUS = "real_public_records_models_active"


# ============================================================
# SECTION 03 - PUBLIC RECORD TYPE ENUMERATION
# ============================================================

class PublicRecordType(StrEnum):
    """
    Public-record category.
    """

    PARCEL = "parcel"
    TAX_ASSESSMENT = "tax_assessment"
    PROPERTY_TAX = "property_tax"
    DEED = "deed"
    MORTGAGE = "mortgage"
    LIEN = "lien"
    SALE_HISTORY = "sale_history"
    OWNER_REFERENCE = "owner_reference"
    BUILDING_FACTS = "building_facts"
    MUNICIPAL = "municipal"
    COUNTY = "county"
    STATE = "state"
    GIS = "gis"
    MODIV = "modiv"
    TAX_MAP = "tax_map"
    PERMIT = "permit"
    ZONING = "zoning"
    FLOOD = "flood"
    SCHOOL = "school"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 04 - PUBLIC RECORD STATUS ENUMERATION
# ============================================================

class PublicRecordStatus(StrEnum):
    """
    Processing and availability status for public records.
    """

    AVAILABLE = "available"
    VERIFIED = "verified"
    PARTIAL = "partial"
    AMBIGUOUS = "ambiguous"
    UNAVAILABLE = "unavailable"
    NOT_CONNECTED = "not_connected"
    NOT_IMPLEMENTED = "not_implemented"
    SOURCE_ERROR = "source_error"
    EMPTY = "empty"
    STALE = "stale"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 05 - PUBLIC RECORD CONFIDENCE ENUMERATION
# ============================================================

class PublicRecordConfidence(StrEnum):
    """
    Public-record confidence band.
    """

    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 06 - PROPERTY CLASS ENUMERATION
# ============================================================

class PropertyClass(StrEnum):
    """
    General property class category.
    """

    RESIDENTIAL = "residential"
    SINGLE_FAMILY = "single_family"
    TWO_FAMILY = "two_family"
    MULTI_FAMILY = "multi_family"
    CONDOMINIUM = "condominium"
    TOWNHOUSE = "townhouse"
    COOPERATIVE = "cooperative"
    VACANT_LAND = "vacant_land"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    FARM = "farm"
    EXEMPT = "exempt"
    PUBLIC = "public"
    MIXED_USE = "mixed_use"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 07 - DOCUMENT TYPE ENUMERATION
# ============================================================

class RecordedDocumentType(StrEnum):
    """
    Recorded document type.
    """

    DEED = "deed"
    MORTGAGE = "mortgage"
    SATISFACTION = "satisfaction"
    LIEN = "lien"
    RELEASE = "release"
    ASSIGNMENT = "assignment"
    EASEMENT = "easement"
    MAP = "map"
    TAX_SALE_CERTIFICATE = "tax_sale_certificate"
    NOTICE = "notice"
    OTHER = "other"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 08 - SALE TYPE ENUMERATION
# ============================================================

class SaleType(StrEnum):
    """
    Sale transaction classification.
    """

    ARMS_LENGTH = "arms_length"
    NON_ARMS_LENGTH = "non_arms_length"
    FAMILY_TRANSFER = "family_transfer"
    SHERIFF_SALE = "sheriff_sale"
    ESTATE = "estate"
    FORECLOSURE = "foreclosure"
    REO = "reo"
    QUITCLAIM = "quitclaim"
    CORRECTION = "correction"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 09 - CONNECTOR RESULT STATUS ENUMERATION
# ============================================================

class PublicRecordConnectorStatus(StrEnum):
    """
    Connector-level status.
    """

    READY = "ready"
    PLANNED = "planned"
    NOT_IMPLEMENTED = "not_implemented"
    AVAILABLE = "available"
    PARTIAL = "partial"
    EMPTY = "empty"
    ERROR = "error"
    AUTH_REQUIRED = "auth_required"
    RATE_LIMITED = "rate_limited"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    DISABLED = "disabled"


# ============================================================
# SECTION 10 - NORMALIZATION UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(UTC).isoformat()


def stable_hash(value: Any) -> str:
    """
    Create a stable SHA-256 hash.
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


def safe_string(value: Any) -> str:
    """
    Convert unknown value to safe string.
    """

    if value is None:
        return ""

    return str(value).strip()


def safe_upper(value: Any) -> str:
    """
    Convert unknown value to uppercase safe string.
    """

    return safe_string(value).upper()


def safe_float(value: Any) -> float | None:
    """
    Convert unknown value to float where possible.
    """

    if value is None:
        return None

    if isinstance(value, float):
        return value

    if isinstance(value, int):
        return float(value)

    cleaned = (
        str(value)
        .replace("$", "")
        .replace(",", "")
        .replace("sqft", "")
        .replace("sq ft", "")
        .strip()
    )

    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def safe_int(value: Any) -> int | None:
    """
    Convert unknown value to integer where possible.
    """

    numeric = safe_float(value)

    if numeric is None:
        return None

    return int(round(numeric))


def normalize_block_lot(
    block: Any = None,
    lot: Any = None,
    qualifier: Any = None,
) -> dict[str, str | None]:
    """
    Normalize block, lot, and qualifier identifiers.
    """

    block_value = safe_string(block) or None
    lot_value = safe_string(lot) or None
    qualifier_value = safe_string(qualifier) or None

    return {
        "block": block_value,
        "lot": lot_value,
        "qualifier": qualifier_value,
    }


def normalize_state(value: Any) -> str | None:
    """
    Normalize state value.
    """

    normalized = safe_upper(value)

    if not normalized:
        return None

    if normalized in {"NEW JERSEY", "NJ"}:
        return "NJ"

    return normalized


def normalize_county(value: Any) -> str | None:
    """
    Normalize county value.
    """

    normalized = safe_string(value)

    if not normalized:
        return None

    if normalized.lower().endswith(" county"):
        normalized = normalized[:-7]

    return normalized.strip().title()


def normalize_municipality(value: Any) -> str | None:
    """
    Normalize municipality.
    """

    normalized = safe_string(value)

    if not normalized:
        return None

    return " ".join(normalized.split()).title()


def normalize_money(value: Any) -> float | None:
    """
    Normalize money values.
    """

    return safe_float(value)


def normalize_area(value: Any) -> float | None:
    """
    Normalize area values.
    """

    return safe_float(value)


def normalize_year(value: Any) -> int | None:
    """
    Normalize year values.
    """

    year = safe_int(value)

    if year is None:
        return None

    if year < 1600 or year > 2200:
        return None

    return year


def make_public_record_id(
    *,
    record_type: str,
    source_id: str | None = None,
    address: str | None = None,
    municipality: str | None = None,
    county: str | None = None,
    state: str | None = None,
    block: str | None = None,
    lot: str | None = None,
    document_id: str | None = None,
    tax_year: int | None = None,
) -> str:
    """
    Create stable public record ID.
    """

    payload = {
        "record_type": record_type,
        "source_id": source_id,
        "address": address,
        "municipality": municipality,
        "county": county,
        "state": state,
        "block": block,
        "lot": lot,
        "document_id": document_id,
        "tax_year": tax_year,
    }

    return f"public-record-{stable_hash(payload)[:20]}"


# ============================================================
# SECTION 11 - PUBLIC RECORD SOURCE CONTEXT
# ============================================================

@dataclass
class PublicRecordSourceContext:
    """
    Source context for public-record data.
    """

    source_id: str
    source_name: str
    source_type: str
    source_url: str | None = None
    source_status: str = SourceStatus.PLANNED.value
    attribution: SourceAttribution | None = None
    retrieved_at: str = field(default_factory=utc_now)
    source_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert source context to dictionary.
        """

        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "source_status": self.source_status,
            "attribution": (
                self.attribution.to_dict()
                if self.attribution
                else None
            ),
            "retrieved_at": self.retrieved_at,
            "source_notes": self.source_notes,
        }


# ============================================================
# SECTION 12 - PUBLIC RECORD ADDRESS MODEL
# ============================================================

@dataclass
class PublicRecordAddress:
    """
    Public-record address identity.
    """

    raw_address: str | None = None
    street_address: str | None = None
    unit: str | None = None
    municipality: str | None = None
    county: str | None = None
    state: str | None = None
    postal_code: str | None = None
    normalized_address: str | None = None
    address_confidence: float = 0.0
    source_context: PublicRecordSourceContext | None = None
    source_fields: list[SourceField] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.state = normalize_state(self.state)
        self.county = normalize_county(self.county)
        self.municipality = normalize_municipality(self.municipality)
        self.address_confidence = clamp_confidence(self.address_confidence)

        if not self.normalized_address:
            parts = [
                self.street_address,
                self.unit,
                self.municipality,
                self.state,
                self.postal_code,
            ]

            self.normalized_address = ", ".join(
                safe_string(part)
                for part in parts
                if safe_string(part)
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_address": self.raw_address,
            "street_address": self.street_address,
            "unit": self.unit,
            "municipality": self.municipality,
            "county": self.county,
            "state": self.state,
            "postal_code": self.postal_code,
            "normalized_address": self.normalized_address,
            "address_confidence": self.address_confidence,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "source_fields": [
                source_field.to_dict()
                for source_field in self.source_fields
            ],
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }


# ============================================================
# SECTION 13 - PARCEL IDENTIFIER MODEL
# ============================================================

@dataclass
class ParcelIdentifier:
    """
    Parcel identifier model.
    """

    parcel_id: str | None = None
    pams_pin: str | None = None
    block: str | None = None
    lot: str | None = None
    qualifier: str | None = None
    municipality_code: str | None = None
    county_code: str | None = None
    state_code: str | None = None
    tax_map_page: str | None = None
    source_context: PublicRecordSourceContext | None = None

    def __post_init__(self) -> None:
        normalized = normalize_block_lot(
            self.block,
            self.lot,
            self.qualifier,
        )

        self.block = normalized["block"]
        self.lot = normalized["lot"]
        self.qualifier = normalized["qualifier"]
        self.state_code = normalize_state(self.state_code)

    def to_dict(self) -> dict[str, Any]:
        return {
            "parcel_id": self.parcel_id,
            "pams_pin": self.pams_pin,
            "block": self.block,
            "lot": self.lot,
            "qualifier": self.qualifier,
            "municipality_code": self.municipality_code,
            "county_code": self.county_code,
            "state_code": self.state_code,
            "tax_map_page": self.tax_map_page,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
        }

    def display_key(self) -> str:
        """
        Return human-friendly parcel key.
        """

        parts = []

        if self.block:
            parts.append(f"Block {self.block}")

        if self.lot:
            parts.append(f"Lot {self.lot}")

        if self.qualifier:
            parts.append(f"Qual {self.qualifier}")

        if parts:
            return " / ".join(parts)

        if self.parcel_id:
            return self.parcel_id

        if self.pams_pin:
            return self.pams_pin

        return "Unknown Parcel"


# ============================================================
# SECTION 14 - PARCEL RECORD MODEL
# ============================================================

@dataclass
class ParcelRecord:
    """
    Parcel-level public record.
    """

    record_id: str
    parcel_identifier: ParcelIdentifier
    address: PublicRecordAddress | None = None
    municipality: str | None = None
    county: str | None = None
    state: str | None = None
    property_class: str = PropertyClass.UNKNOWN.value
    land_description: str | None = None
    lot_size_acres: float | None = None
    lot_size_sqft: float | None = None
    frontage: float | None = None
    depth: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    geometry_reference: str | None = None
    source_context: PublicRecordSourceContext | None = None
    source_reference: SourceRecordReference | None = None
    confidence: float = 0.0
    status: str = PublicRecordStatus.UNKNOWN.value
    retrieved_at: str = field(default_factory=utc_now)
    notes: list[str] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.state = normalize_state(self.state)
        self.county = normalize_county(self.county)
        self.municipality = normalize_municipality(self.municipality)
        self.lot_size_acres = normalize_area(self.lot_size_acres)
        self.lot_size_sqft = normalize_area(self.lot_size_sqft)
        self.frontage = normalize_area(self.frontage)
        self.depth = normalize_area(self.depth)
        self.confidence = clamp_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "parcel_identifier": self.parcel_identifier.to_dict(),
            "address": self.address.to_dict() if self.address else None,
            "municipality": self.municipality,
            "county": self.county,
            "state": self.state,
            "property_class": self.property_class,
            "land_description": self.land_description,
            "lot_size_acres": self.lot_size_acres,
            "lot_size_sqft": self.lot_size_sqft,
            "frontage": self.frontage,
            "depth": self.depth,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "geometry_reference": self.geometry_reference,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "source_reference": (
                self.source_reference.to_dict()
                if self.source_reference
                else None
            ),
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "status": self.status,
            "retrieved_at": self.retrieved_at,
            "notes": self.notes,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }


# ============================================================
# SECTION 15 - TAX ASSESSMENT RECORD MODEL
# ============================================================

@dataclass
class TaxAssessmentRecord:
    """
    Tax assessment public record.
    """

    record_id: str
    tax_year: int | None = None
    parcel_identifier: ParcelIdentifier | None = None
    address: PublicRecordAddress | None = None
    owner_reference: str | None = None
    property_class: str = PropertyClass.UNKNOWN.value
    land_value: float | None = None
    improvement_value: float | None = None
    total_assessed_value: float | None = None
    exempt_value: float | None = None
    taxable_value: float | None = None
    assessment_ratio: float | None = None
    equalized_value: float | None = None
    source_context: PublicRecordSourceContext | None = None
    source_reference: SourceRecordReference | None = None
    timestamp: SourceTimestamp | None = None
    confidence: float = 0.0
    status: str = PublicRecordStatus.UNKNOWN.value
    notes: list[str] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.tax_year = normalize_year(self.tax_year)
        self.land_value = normalize_money(self.land_value)
        self.improvement_value = normalize_money(self.improvement_value)
        self.total_assessed_value = normalize_money(self.total_assessed_value)
        self.exempt_value = normalize_money(self.exempt_value)
        self.taxable_value = normalize_money(self.taxable_value)
        self.assessment_ratio = safe_float(self.assessment_ratio)
        self.equalized_value = normalize_money(self.equalized_value)
        self.confidence = clamp_confidence(self.confidence)

        if self.timestamp is None:
            self.timestamp = SourceTimestamp(
                tax_year=self.tax_year,
            )

        if self.total_assessed_value is None:
            values = [
                self.land_value or 0.0,
                self.improvement_value or 0.0,
            ]

            if any(values):
                self.total_assessed_value = sum(values)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "tax_year": self.tax_year,
            "parcel_identifier": (
                self.parcel_identifier.to_dict()
                if self.parcel_identifier
                else None
            ),
            "address": self.address.to_dict() if self.address else None,
            "owner_reference": self.owner_reference,
            "property_class": self.property_class,
            "land_value": self.land_value,
            "improvement_value": self.improvement_value,
            "total_assessed_value": self.total_assessed_value,
            "exempt_value": self.exempt_value,
            "taxable_value": self.taxable_value,
            "assessment_ratio": self.assessment_ratio,
            "equalized_value": self.equalized_value,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "source_reference": (
                self.source_reference.to_dict()
                if self.source_reference
                else None
            ),
            "timestamp": (
                self.timestamp.to_dict()
                if self.timestamp
                else None
            ),
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "status": self.status,
            "notes": self.notes,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }


# ============================================================
# SECTION 16 - PROPERTY TAX RECORD MODEL
# ============================================================

@dataclass
class PropertyTaxRecord:
    """
    Property tax public record.
    """

    record_id: str
    tax_year: int | None = None
    parcel_identifier: ParcelIdentifier | None = None
    address: PublicRecordAddress | None = None
    assessed_value: float | None = None
    tax_rate: float | None = None
    annual_tax_amount: float | None = None
    municipal_tax_amount: float | None = None
    county_tax_amount: float | None = None
    school_tax_amount: float | None = None
    special_assessment_amount: float | None = None
    source_context: PublicRecordSourceContext | None = None
    source_reference: SourceRecordReference | None = None
    timestamp: SourceTimestamp | None = None
    confidence: float = 0.0
    status: str = PublicRecordStatus.UNKNOWN.value
    notes: list[str] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.tax_year = normalize_year(self.tax_year)
        self.assessed_value = normalize_money(self.assessed_value)
        self.tax_rate = safe_float(self.tax_rate)
        self.annual_tax_amount = normalize_money(self.annual_tax_amount)
        self.municipal_tax_amount = normalize_money(self.municipal_tax_amount)
        self.county_tax_amount = normalize_money(self.county_tax_amount)
        self.school_tax_amount = normalize_money(self.school_tax_amount)
        self.special_assessment_amount = normalize_money(
            self.special_assessment_amount
        )
        self.confidence = clamp_confidence(self.confidence)

        if self.timestamp is None:
            self.timestamp = SourceTimestamp(
                tax_year=self.tax_year,
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "tax_year": self.tax_year,
            "parcel_identifier": (
                self.parcel_identifier.to_dict()
                if self.parcel_identifier
                else None
            ),
            "address": self.address.to_dict() if self.address else None,
            "assessed_value": self.assessed_value,
            "tax_rate": self.tax_rate,
            "annual_tax_amount": self.annual_tax_amount,
            "municipal_tax_amount": self.municipal_tax_amount,
            "county_tax_amount": self.county_tax_amount,
            "school_tax_amount": self.school_tax_amount,
            "special_assessment_amount": self.special_assessment_amount,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "source_reference": (
                self.source_reference.to_dict()
                if self.source_reference
                else None
            ),
            "timestamp": (
                self.timestamp.to_dict()
                if self.timestamp
                else None
            ),
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "status": self.status,
            "notes": self.notes,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }


# ============================================================
# SECTION 17 - BUILDING FACTS RECORD MODEL
# ============================================================

@dataclass
class BuildingFactsRecord:
    """
    Building facts sourced from public records where available.
    """

    record_id: str
    parcel_identifier: ParcelIdentifier | None = None
    address: PublicRecordAddress | None = None
    property_class: str = PropertyClass.UNKNOWN.value
    year_built: int | None = None
    building_area_sqft: float | None = None
    living_area_sqft: float | None = None
    gross_area_sqft: float | None = None
    bedrooms: int | None = None
    bathrooms: float | None = None
    stories: float | None = None
    construction_type: str | None = None
    style: str | None = None
    exterior: str | None = None
    basement: str | None = None
    garage: str | None = None
    source_context: PublicRecordSourceContext | None = None
    source_reference: SourceRecordReference | None = None
    confidence: float = 0.0
    status: str = PublicRecordStatus.UNKNOWN.value
    notes: list[str] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.year_built = normalize_year(self.year_built)
        self.building_area_sqft = normalize_area(self.building_area_sqft)
        self.living_area_sqft = normalize_area(self.living_area_sqft)
        self.gross_area_sqft = normalize_area(self.gross_area_sqft)
        self.bedrooms = safe_int(self.bedrooms)
        self.bathrooms = safe_float(self.bathrooms)
        self.stories = safe_float(self.stories)
        self.confidence = clamp_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "parcel_identifier": (
                self.parcel_identifier.to_dict()
                if self.parcel_identifier
                else None
            ),
            "address": self.address.to_dict() if self.address else None,
            "property_class": self.property_class,
            "year_built": self.year_built,
            "building_area_sqft": self.building_area_sqft,
            "living_area_sqft": self.living_area_sqft,
            "gross_area_sqft": self.gross_area_sqft,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "stories": self.stories,
            "construction_type": self.construction_type,
            "style": self.style,
            "exterior": self.exterior,
            "basement": self.basement,
            "garage": self.garage,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "source_reference": (
                self.source_reference.to_dict()
                if self.source_reference
                else None
            ),
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "status": self.status,
            "notes": self.notes,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }


# ============================================================
# SECTION 18 - RECORDED DOCUMENT REFERENCE MODEL
# ============================================================

@dataclass
class RecordedDocumentReference:
    """
    Recorded document reference from clerk/recorder source.
    """

    record_id: str
    document_type: str = RecordedDocumentType.UNKNOWN.value
    document_id: str | None = None
    instrument_number: str | None = None
    book: str | None = None
    page: str | None = None
    recording_date: str | None = None
    document_date: str | None = None
    grantor_reference: str | None = None
    grantee_reference: str | None = None
    consideration_amount: float | None = None
    parcel_identifier: ParcelIdentifier | None = None
    address: PublicRecordAddress | None = None
    source_context: PublicRecordSourceContext | None = None
    source_reference: SourceRecordReference | None = None
    confidence: float = 0.0
    status: str = PublicRecordStatus.UNKNOWN.value
    notes: list[str] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.consideration_amount = normalize_money(self.consideration_amount)
        self.confidence = clamp_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "document_type": self.document_type,
            "document_id": self.document_id,
            "instrument_number": self.instrument_number,
            "book": self.book,
            "page": self.page,
            "recording_date": self.recording_date,
            "document_date": self.document_date,
            "grantor_reference": self.grantor_reference,
            "grantee_reference": self.grantee_reference,
            "consideration_amount": self.consideration_amount,
            "parcel_identifier": (
                self.parcel_identifier.to_dict()
                if self.parcel_identifier
                else None
            ),
            "address": self.address.to_dict() if self.address else None,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "source_reference": (
                self.source_reference.to_dict()
                if self.source_reference
                else None
            ),
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "status": self.status,
            "notes": self.notes,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }


# ============================================================
# SECTION 19 - DEED RECORD MODEL
# ============================================================

@dataclass
class DeedRecord:
    """
    Deed public record reference.
    """

    record_id: str
    document: RecordedDocumentReference
    sale_type: str = SaleType.UNKNOWN.value
    sale_price: float | None = None
    transfer_date: str | None = None
    seller_reference: str | None = None
    buyer_reference: str | None = None
    deed_book: str | None = None
    deed_page: str | None = None
    source_context: PublicRecordSourceContext | None = None
    confidence: float = 0.0
    status: str = PublicRecordStatus.UNKNOWN.value
    notes: list[str] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.sale_price = normalize_money(self.sale_price)
        self.confidence = clamp_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "document": self.document.to_dict(),
            "sale_type": self.sale_type,
            "sale_price": self.sale_price,
            "transfer_date": self.transfer_date,
            "seller_reference": self.seller_reference,
            "buyer_reference": self.buyer_reference,
            "deed_book": self.deed_book,
            "deed_page": self.deed_page,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "status": self.status,
            "notes": self.notes,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }


# ============================================================
# SECTION 20 - MORTGAGE RECORD MODEL
# ============================================================

@dataclass
class MortgageRecord:
    """
    Mortgage public record reference.
    """

    record_id: str
    document: RecordedDocumentReference
    mortgage_amount: float | None = None
    lender_reference: str | None = None
    borrower_reference: str | None = None
    recording_date: str | None = None
    maturity_date: str | None = None
    source_context: PublicRecordSourceContext | None = None
    confidence: float = 0.0
    status: str = PublicRecordStatus.UNKNOWN.value
    notes: list[str] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.mortgage_amount = normalize_money(self.mortgage_amount)
        self.confidence = clamp_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "document": self.document.to_dict(),
            "mortgage_amount": self.mortgage_amount,
            "lender_reference": self.lender_reference,
            "borrower_reference": self.borrower_reference,
            "recording_date": self.recording_date,
            "maturity_date": self.maturity_date,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "status": self.status,
            "notes": self.notes,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }


# ============================================================
# SECTION 21 - LIEN RECORD MODEL
# ============================================================

@dataclass
class LienRecord:
    """
    Lien public record reference.
    """

    record_id: str
    document: RecordedDocumentReference
    lien_type: str | None = None
    lien_amount: float | None = None
    creditor_reference: str | None = None
    debtor_reference: str | None = None
    recording_date: str | None = None
    release_reference: str | None = None
    source_context: PublicRecordSourceContext | None = None
    confidence: float = 0.0
    status: str = PublicRecordStatus.UNKNOWN.value
    notes: list[str] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.lien_amount = normalize_money(self.lien_amount)
        self.confidence = clamp_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "document": self.document.to_dict(),
            "lien_type": self.lien_type,
            "lien_amount": self.lien_amount,
            "creditor_reference": self.creditor_reference,
            "debtor_reference": self.debtor_reference,
            "recording_date": self.recording_date,
            "release_reference": self.release_reference,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "status": self.status,
            "notes": self.notes,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }


# ============================================================
# SECTION 22 - SALE HISTORY RECORD MODEL
# ============================================================

@dataclass
class SaleHistoryRecord:
    """
    Sale-history record built from tax board, deed, clerk, or other official sources.
    """

    record_id: str
    sale_date: str | None = None
    sale_price: float | None = None
    sale_type: str = SaleType.UNKNOWN.value
    seller_reference: str | None = None
    buyer_reference: str | None = None
    deed_record: DeedRecord | None = None
    parcel_identifier: ParcelIdentifier | None = None
    address: PublicRecordAddress | None = None
    source_context: PublicRecordSourceContext | None = None
    source_reference: SourceRecordReference | None = None
    confidence: float = 0.0
    status: str = PublicRecordStatus.UNKNOWN.value
    notes: list[str] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.sale_price = normalize_money(self.sale_price)
        self.confidence = clamp_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "sale_date": self.sale_date,
            "sale_price": self.sale_price,
            "sale_type": self.sale_type,
            "seller_reference": self.seller_reference,
            "buyer_reference": self.buyer_reference,
            "deed_record": (
                self.deed_record.to_dict()
                if self.deed_record
                else None
            ),
            "parcel_identifier": (
                self.parcel_identifier.to_dict()
                if self.parcel_identifier
                else None
            ),
            "address": self.address.to_dict() if self.address else None,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "source_reference": (
                self.source_reference.to_dict()
                if self.source_reference
                else None
            ),
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "status": self.status,
            "notes": self.notes,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }


# ============================================================
# SECTION 23 - OWNER REFERENCE MODEL
# ============================================================

@dataclass
class OwnerReferenceRecord:
    """
    Public owner reference.

    This is intentionally called a reference because public-record
    ownership context may require manual/legal review before being
    treated as authoritative platform truth.
    """

    record_id: str
    owner_reference: str | None = None
    owner_mailing_city: str | None = None
    owner_mailing_state: str | None = None
    owner_mailing_postal_code: str | None = None
    ownership_type: str | None = None
    parcel_identifier: ParcelIdentifier | None = None
    address: PublicRecordAddress | None = None
    source_context: PublicRecordSourceContext | None = None
    source_reference: SourceRecordReference | None = None
    confidence: float = 0.0
    status: str = PublicRecordStatus.UNKNOWN.value
    notes: list[str] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.owner_mailing_state = normalize_state(self.owner_mailing_state)
        self.confidence = clamp_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "owner_reference": self.owner_reference,
            "owner_mailing_city": self.owner_mailing_city,
            "owner_mailing_state": self.owner_mailing_state,
            "owner_mailing_postal_code": self.owner_mailing_postal_code,
            "ownership_type": self.ownership_type,
            "parcel_identifier": (
                self.parcel_identifier.to_dict()
                if self.parcel_identifier
                else None
            ),
            "address": self.address.to_dict() if self.address else None,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "source_reference": (
                self.source_reference.to_dict()
                if self.source_reference
                else None
            ),
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "status": self.status,
            "notes": self.notes,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }


# ============================================================
# SECTION 24 - MUNICIPAL CONTEXT RECORD MODEL
# ============================================================

@dataclass
class MunicipalContextRecord:
    """
    Municipal context public record.
    """

    record_id: str
    municipality: str | None = None
    county: str | None = None
    state: str | None = None
    municipality_code: str | None = None
    tax_district_code: str | None = None
    school_district: str | None = None
    zoning_reference: str | None = None
    source_context: PublicRecordSourceContext | None = None
    source_reference: SourceRecordReference | None = None
    confidence: float = 0.0
    status: str = PublicRecordStatus.UNKNOWN.value
    notes: list[str] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.municipality = normalize_municipality(self.municipality)
        self.county = normalize_county(self.county)
        self.state = normalize_state(self.state)
        self.confidence = clamp_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "municipality": self.municipality,
            "county": self.county,
            "state": self.state,
            "municipality_code": self.municipality_code,
            "tax_district_code": self.tax_district_code,
            "school_district": self.school_district,
            "zoning_reference": self.zoning_reference,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "source_reference": (
                self.source_reference.to_dict()
                if self.source_reference
                else None
            ),
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "status": self.status,
            "notes": self.notes,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }


# ============================================================
# SECTION 25 - GIS CONTEXT RECORD MODEL
# ============================================================

@dataclass
class GISContextRecord:
    """
    GIS parcel context.
    """

    record_id: str
    parcel_identifier: ParcelIdentifier | None = None
    address: PublicRecordAddress | None = None
    layer_name: str | None = None
    geometry_type: str | None = None
    centroid_latitude: float | None = None
    centroid_longitude: float | None = None
    map_url: str | None = None
    feature_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    source_context: PublicRecordSourceContext | None = None
    source_reference: SourceRecordReference | None = None
    confidence: float = 0.0
    status: str = PublicRecordStatus.UNKNOWN.value
    notes: list[str] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.centroid_latitude = safe_float(self.centroid_latitude)
        self.centroid_longitude = safe_float(self.centroid_longitude)
        self.confidence = clamp_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "parcel_identifier": (
                self.parcel_identifier.to_dict()
                if self.parcel_identifier
                else None
            ),
            "address": self.address.to_dict() if self.address else None,
            "layer_name": self.layer_name,
            "geometry_type": self.geometry_type,
            "centroid_latitude": self.centroid_latitude,
            "centroid_longitude": self.centroid_longitude,
            "map_url": self.map_url,
            "feature_id": self.feature_id,
            "attributes": self.attributes,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "source_reference": (
                self.source_reference.to_dict()
                if self.source_reference
                else None
            ),
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "status": self.status,
            "notes": self.notes,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }


# ============================================================
# SECTION 26 - MOD-IV CONTEXT RECORD MODEL
# ============================================================

@dataclass
class ModIVRecord:
    """
    New Jersey MOD-IV assessment/parcel context.
    """

    record_id: str
    tax_year: int | None = None
    municipality_code: str | None = None
    county_code: str | None = None
    parcel_identifier: ParcelIdentifier | None = None
    address: PublicRecordAddress | None = None
    property_class: str = PropertyClass.UNKNOWN.value
    land_value: float | None = None
    improvement_value: float | None = None
    total_assessed_value: float | None = None
    property_location: str | None = None
    owner_reference: str | None = None
    raw_attributes: dict[str, Any] = field(default_factory=dict)
    source_context: PublicRecordSourceContext | None = None
    source_reference: SourceRecordReference | None = None
    confidence: float = 0.0
    status: str = PublicRecordStatus.UNKNOWN.value
    notes: list[str] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.tax_year = normalize_year(self.tax_year)
        self.land_value = normalize_money(self.land_value)
        self.improvement_value = normalize_money(self.improvement_value)
        self.total_assessed_value = normalize_money(self.total_assessed_value)
        self.confidence = clamp_confidence(self.confidence)

        if self.total_assessed_value is None:
            land = self.land_value or 0.0
            improvement = self.improvement_value or 0.0

            if land or improvement:
                self.total_assessed_value = land + improvement

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "tax_year": self.tax_year,
            "municipality_code": self.municipality_code,
            "county_code": self.county_code,
            "parcel_identifier": (
                self.parcel_identifier.to_dict()
                if self.parcel_identifier
                else None
            ),
            "address": self.address.to_dict() if self.address else None,
            "property_class": self.property_class,
            "land_value": self.land_value,
            "improvement_value": self.improvement_value,
            "total_assessed_value": self.total_assessed_value,
            "property_location": self.property_location,
            "owner_reference": self.owner_reference,
            "raw_attributes": self.raw_attributes,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "source_reference": (
                self.source_reference.to_dict()
                if self.source_reference
                else None
            ),
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "status": self.status,
            "notes": self.notes,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
        }


# ============================================================
# SECTION 27 - PUBLIC RECORD SEARCH REQUEST MODEL
# ============================================================

@dataclass
class PublicRecordSearchRequest:
    """
    Search request for public-record connectors.
    """

    request_id: str
    raw_query: str | None = None
    address: PublicRecordAddress | None = None
    street_address: str | None = None
    municipality: str | None = None
    county: str | None = None
    state: str | None = None
    postal_code: str | None = None
    block: str | None = None
    lot: str | None = None
    qualifier: str | None = None
    owner_reference: str | None = None
    tax_year: int | None = None
    source_ids: list[str] = field(default_factory=list)
    requested_record_types: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.municipality = normalize_municipality(self.municipality)
        self.county = normalize_county(self.county)
        self.state = normalize_state(self.state)
        self.tax_year = normalize_year(self.tax_year)

        normalized = normalize_block_lot(
            self.block,
            self.lot,
            self.qualifier,
        )

        self.block = normalized["block"]
        self.lot = normalized["lot"]
        self.qualifier = normalized["qualifier"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "raw_query": self.raw_query,
            "address": self.address.to_dict() if self.address else None,
            "street_address": self.street_address,
            "municipality": self.municipality,
            "county": self.county,
            "state": self.state,
            "postal_code": self.postal_code,
            "block": self.block,
            "lot": self.lot,
            "qualifier": self.qualifier,
            "owner_reference": self.owner_reference,
            "tax_year": self.tax_year,
            "source_ids": self.source_ids,
            "requested_record_types": self.requested_record_types,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    def fingerprint(self) -> str:
        """
        Return stable request fingerprint.
        """

        return stable_hash(self.to_dict())


# ============================================================
# SECTION 28 - PUBLIC RECORD CONNECTOR RESULT MODEL
# ============================================================

@dataclass
class PublicRecordConnectorResult:
    """
    Standard result returned by public-record connectors.
    """

    connector_id: str
    source_id: str
    source_name: str
    status: str
    request: PublicRecordSearchRequest | None = None
    source_result: SourceResult | None = None
    parcel_records: list[ParcelRecord] = field(default_factory=list)
    tax_assessment_records: list[TaxAssessmentRecord] = field(default_factory=list)
    property_tax_records: list[PropertyTaxRecord] = field(default_factory=list)
    building_facts_records: list[BuildingFactsRecord] = field(default_factory=list)
    recorded_document_references: list[RecordedDocumentReference] = field(default_factory=list)
    deed_records: list[DeedRecord] = field(default_factory=list)
    mortgage_records: list[MortgageRecord] = field(default_factory=list)
    lien_records: list[LienRecord] = field(default_factory=list)
    sale_history_records: list[SaleHistoryRecord] = field(default_factory=list)
    owner_reference_records: list[OwnerReferenceRecord] = field(default_factory=list)
    municipal_context_records: list[MunicipalContextRecord] = field(default_factory=list)
    gis_context_records: list[GISContextRecord] = field(default_factory=list)
    modiv_records: list[ModIVRecord] = field(default_factory=list)
    errors: list[SourceError] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)
    confidence_report: SourceConfidenceReport | None = None
    raw_payload_reference: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    retrieved_at: str = field(default_factory=utc_now)

    def records_found(self) -> int:
        """
        Return total normalized records found.
        """

        return sum(
            [
                len(self.parcel_records),
                len(self.tax_assessment_records),
                len(self.property_tax_records),
                len(self.building_facts_records),
                len(self.recorded_document_references),
                len(self.deed_records),
                len(self.mortgage_records),
                len(self.lien_records),
                len(self.sale_history_records),
                len(self.owner_reference_records),
                len(self.municipal_context_records),
                len(self.gis_context_records),
                len(self.modiv_records),
            ]
        )

    def is_successful(self) -> bool:
        """
        Return whether connector result is useful.
        """

        return self.status in {
            PublicRecordConnectorStatus.AVAILABLE.value,
            PublicRecordConnectorStatus.PARTIAL.value,
        } and not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "status": self.status,
            "request": self.request.to_dict() if self.request else None,
            "source_result": (
                self.source_result.to_dict()
                if self.source_result
                else None
            ),
            "records_found": self.records_found(),
            "parcel_records": [
                record.to_dict()
                for record in self.parcel_records
            ],
            "tax_assessment_records": [
                record.to_dict()
                for record in self.tax_assessment_records
            ],
            "property_tax_records": [
                record.to_dict()
                for record in self.property_tax_records
            ],
            "building_facts_records": [
                record.to_dict()
                for record in self.building_facts_records
            ],
            "recorded_document_references": [
                record.to_dict()
                for record in self.recorded_document_references
            ],
            "deed_records": [
                record.to_dict()
                for record in self.deed_records
            ],
            "mortgage_records": [
                record.to_dict()
                for record in self.mortgage_records
            ],
            "lien_records": [
                record.to_dict()
                for record in self.lien_records
            ],
            "sale_history_records": [
                record.to_dict()
                for record in self.sale_history_records
            ],
            "owner_reference_records": [
                record.to_dict()
                for record in self.owner_reference_records
            ],
            "municipal_context_records": [
                record.to_dict()
                for record in self.municipal_context_records
            ],
            "gis_context_records": [
                record.to_dict()
                for record in self.gis_context_records
            ],
            "modiv_records": [
                record.to_dict()
                for record in self.modiv_records
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
            "raw_payload_reference": self.raw_payload_reference,
            "metadata": self.metadata,
            "retrieved_at": self.retrieved_at,
        }


# ============================================================
# SECTION 29 - PUBLIC RECORD AGGREGATE REPORT MODEL
# ============================================================

@dataclass
class PublicRecordReport:
    """
    Aggregated public-record report for one property/address query.
    """

    report_id: str
    request: PublicRecordSearchRequest
    status: str = PublicRecordStatus.UNKNOWN.value
    connector_results: list[PublicRecordConnectorResult] = field(default_factory=list)
    primary_address: PublicRecordAddress | None = None
    primary_parcel: ParcelRecord | None = None
    parcel_records: list[ParcelRecord] = field(default_factory=list)
    tax_assessment_records: list[TaxAssessmentRecord] = field(default_factory=list)
    property_tax_records: list[PropertyTaxRecord] = field(default_factory=list)
    building_facts_records: list[BuildingFactsRecord] = field(default_factory=list)
    recorded_document_references: list[RecordedDocumentReference] = field(default_factory=list)
    deed_records: list[DeedRecord] = field(default_factory=list)
    mortgage_records: list[MortgageRecord] = field(default_factory=list)
    lien_records: list[LienRecord] = field(default_factory=list)
    sale_history_records: list[SaleHistoryRecord] = field(default_factory=list)
    owner_reference_records: list[OwnerReferenceRecord] = field(default_factory=list)
    municipal_context_records: list[MunicipalContextRecord] = field(default_factory=list)
    gis_context_records: list[GISContextRecord] = field(default_factory=list)
    modiv_records: list[ModIVRecord] = field(default_factory=list)
    confidence_report: SourceConfidenceReport | None = None
    errors: list[SourceError] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)
    unavailable_sources: list[str] = field(default_factory=list)
    manual_review_required: bool = False
    generated_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def total_records_found(self) -> int:
        """
        Return total normalized public records found.
        """

        return sum(
            [
                len(self.parcel_records),
                len(self.tax_assessment_records),
                len(self.property_tax_records),
                len(self.building_facts_records),
                len(self.recorded_document_references),
                len(self.deed_records),
                len(self.mortgage_records),
                len(self.lien_records),
                len(self.sale_history_records),
                len(self.owner_reference_records),
                len(self.municipal_context_records),
                len(self.gis_context_records),
                len(self.modiv_records),
            ]
        )

    def summarize_source_status(self) -> dict[str, Any]:
        """
        Summarize source status across connector results.
        """

        summary: dict[str, Any] = {
            "connectors_run": len(self.connector_results),
            "available": [],
            "partial": [],
            "empty": [],
            "error": [],
            "not_implemented": [],
            "unavailable": list(self.unavailable_sources),
        }

        for result in self.connector_results:
            if result.status == PublicRecordConnectorStatus.AVAILABLE.value:
                summary["available"].append(result.source_id)
            elif result.status == PublicRecordConnectorStatus.PARTIAL.value:
                summary["partial"].append(result.source_id)
            elif result.status == PublicRecordConnectorStatus.EMPTY.value:
                summary["empty"].append(result.source_id)
            elif result.status == PublicRecordConnectorStatus.ERROR.value:
                summary["error"].append(result.source_id)
            elif result.status == PublicRecordConnectorStatus.NOT_IMPLEMENTED.value:
                summary["not_implemented"].append(result.source_id)
            else:
                summary["unavailable"].append(result.source_id)

        return summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "request": self.request.to_dict(),
            "status": self.status,
            "connector_results": [
                result.to_dict()
                for result in self.connector_results
            ],
            "primary_address": (
                self.primary_address.to_dict()
                if self.primary_address
                else None
            ),
            "primary_parcel": (
                self.primary_parcel.to_dict()
                if self.primary_parcel
                else None
            ),
            "parcel_records": [
                record.to_dict()
                for record in self.parcel_records
            ],
            "tax_assessment_records": [
                record.to_dict()
                for record in self.tax_assessment_records
            ],
            "property_tax_records": [
                record.to_dict()
                for record in self.property_tax_records
            ],
            "building_facts_records": [
                record.to_dict()
                for record in self.building_facts_records
            ],
            "recorded_document_references": [
                record.to_dict()
                for record in self.recorded_document_references
            ],
            "deed_records": [
                record.to_dict()
                for record in self.deed_records
            ],
            "mortgage_records": [
                record.to_dict()
                for record in self.mortgage_records
            ],
            "lien_records": [
                record.to_dict()
                for record in self.lien_records
            ],
            "sale_history_records": [
                record.to_dict()
                for record in self.sale_history_records
            ],
            "owner_reference_records": [
                record.to_dict()
                for record in self.owner_reference_records
            ],
            "municipal_context_records": [
                record.to_dict()
                for record in self.municipal_context_records
            ],
            "gis_context_records": [
                record.to_dict()
                for record in self.gis_context_records
            ],
            "modiv_records": [
                record.to_dict()
                for record in self.modiv_records
            ],
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
            "unavailable_sources": self.unavailable_sources,
            "manual_review_required": self.manual_review_required,
            "source_status_summary": self.summarize_source_status(),
            "total_records_found": self.total_records_found(),
            "generated_at": self.generated_at,
            "metadata": self.metadata,
        }


# ============================================================
# SECTION 30 - PUBLIC RECORD FACT MODEL
# ============================================================

@dataclass
class PublicRecordFact:
    """
    Claimable public-record fact.
    """

    fact_id: str
    label: str
    value: Any
    record_type: str
    confidence: float
    source_context: PublicRecordSourceContext | None = None
    source_reference: SourceRecordReference | None = None
    supporting_record_ids: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    missing_context: list[str] = field(default_factory=list)
    manual_review_required: bool = False
    generated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.confidence = clamp_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "label": self.label,
            "value": self.value,
            "record_type": self.record_type,
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "source_context": (
                self.source_context.to_dict()
                if self.source_context
                else None
            ),
            "source_reference": (
                self.source_reference.to_dict()
                if self.source_reference
                else None
            ),
            "supporting_record_ids": self.supporting_record_ids,
            "conflicts": self.conflicts,
            "missing_context": self.missing_context,
            "manual_review_required": self.manual_review_required,
            "generated_at": self.generated_at,
        }


# ============================================================
# SECTION 31 - PUBLIC RECORD SUMMARY CARD MODEL
# ============================================================

@dataclass
class PublicRecordSummaryCard:
    """
    Dashboard-ready public-record summary card.
    """

    title: str
    status: str
    value: Any = None
    subtitle: str | None = None
    confidence: float = 0.0
    source_label: str | None = None
    source_status: str | None = None
    explanation: str | None = None
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.confidence = clamp_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "status": self.status,
            "value": self.value,
            "subtitle": self.subtitle,
            "confidence": self.confidence,
            "confidence_band": confidence_band(self.confidence).value,
            "source_label": self.source_label,
            "source_status": self.source_status,
            "explanation": self.explanation,
            "warnings": self.warnings,
        }


# ============================================================
# SECTION 32 - PUBLIC RECORD VALIDATION ISSUE MODEL
# ============================================================

@dataclass
class PublicRecordValidationIssue:
    """
    Validation issue for public-record data.
    """

    issue_code: str
    message: str
    severity: str = "medium"
    record_id: str | None = None
    record_type: str | None = None
    source_id: str | None = None
    manual_review_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================
# SECTION 33 - PUBLIC RECORD VALIDATION REPORT MODEL
# ============================================================

@dataclass
class PublicRecordValidationReport:
    """
    Public-record validation report.
    """

    valid: bool
    issues: list[PublicRecordValidationIssue] = field(default_factory=list)
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
# SECTION 34 - VALIDATION FUNCTIONS
# ============================================================

def validate_parcel_record(
    record: ParcelRecord,
) -> PublicRecordValidationReport:
    """
    Validate a parcel record.
    """

    issues: list[PublicRecordValidationIssue] = []

    parcel = record.parcel_identifier

    if not parcel:
        issues.append(
            PublicRecordValidationIssue(
                issue_code="missing_parcel_identifier",
                message="Parcel record is missing parcel identifier.",
                severity="high",
                record_id=record.record_id,
                record_type=PublicRecordType.PARCEL.value,
                manual_review_required=True,
            )
        )

    if parcel and not any([parcel.parcel_id, parcel.pams_pin, parcel.block and parcel.lot]):
        issues.append(
            PublicRecordValidationIssue(
                issue_code="weak_parcel_identifier",
                message=(
                    "Parcel identifier does not contain parcel_id, PAMS PIN, "
                    "or block/lot."
                ),
                severity="medium",
                record_id=record.record_id,
                record_type=PublicRecordType.PARCEL.value,
                manual_review_required=True,
            )
        )

    if record.confidence <= 0:
        issues.append(
            PublicRecordValidationIssue(
                issue_code="missing_confidence",
                message="Parcel record has no confidence score.",
                severity="medium",
                record_id=record.record_id,
                record_type=PublicRecordType.PARCEL.value,
            )
        )

    return PublicRecordValidationReport(
        valid=not issues,
        issues=issues,
    )


def validate_tax_assessment_record(
    record: TaxAssessmentRecord,
) -> PublicRecordValidationReport:
    """
    Validate a tax assessment record.
    """

    issues: list[PublicRecordValidationIssue] = []

    if record.tax_year is None:
        issues.append(
            PublicRecordValidationIssue(
                issue_code="missing_tax_year",
                message="Tax assessment record is missing tax year.",
                severity="medium",
                record_id=record.record_id,
                record_type=PublicRecordType.TAX_ASSESSMENT.value,
            )
        )

    if record.total_assessed_value is None:
        issues.append(
            PublicRecordValidationIssue(
                issue_code="missing_total_assessed_value",
                message="Tax assessment record is missing total assessed value.",
                severity="medium",
                record_id=record.record_id,
                record_type=PublicRecordType.TAX_ASSESSMENT.value,
            )
        )

    if record.source_context is None:
        issues.append(
            PublicRecordValidationIssue(
                issue_code="missing_source_context",
                message="Tax assessment record is missing source context.",
                severity="medium",
                record_id=record.record_id,
                record_type=PublicRecordType.TAX_ASSESSMENT.value,
            )
        )

    return PublicRecordValidationReport(
        valid=not issues,
        issues=issues,
    )


def validate_public_record_report(
    report: PublicRecordReport,
) -> PublicRecordValidationReport:
    """
    Validate public-record report.
    """

    issues: list[PublicRecordValidationIssue] = []

    if report.total_records_found() == 0:
        issues.append(
            PublicRecordValidationIssue(
                issue_code="no_public_records_found",
                message="Public record report contains no normalized records.",
                severity="medium",
                manual_review_required=False,
            )
        )

    if report.status == PublicRecordStatus.AVAILABLE.value and report.errors:
        issues.append(
            PublicRecordValidationIssue(
                issue_code="available_report_has_errors",
                message="Report is marked available but contains errors.",
                severity="high",
                manual_review_required=True,
            )
        )

    if report.primary_parcel is None and report.parcel_records:
        issues.append(
            PublicRecordValidationIssue(
                issue_code="missing_primary_parcel",
                message=(
                    "Report contains parcel records but no primary parcel selected."
                ),
                severity="medium",
                manual_review_required=True,
            )
        )

    return PublicRecordValidationReport(
        valid=not issues,
        issues=issues,
    )


# ============================================================
# SECTION 35 - FACTORY FUNCTIONS
# ============================================================

def make_public_record_search_request(
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
    source_ids: list[str] | None = None,
    requested_record_types: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> PublicRecordSearchRequest:
    """
    Create a public-record search request.
    """

    payload = {
        "raw_query": raw_query,
        "street_address": street_address,
        "municipality": municipality,
        "county": county,
        "state": state,
        "postal_code": postal_code,
        "block": block,
        "lot": lot,
        "qualifier": qualifier,
        "owner_reference": owner_reference,
        "tax_year": tax_year,
        "source_ids": source_ids or [],
        "requested_record_types": requested_record_types or [],
    }

    request_id = f"public-record-request-{stable_hash(payload)[:18]}"

    return PublicRecordSearchRequest(
        request_id=request_id,
        raw_query=raw_query,
        street_address=street_address,
        municipality=municipality,
        county=county,
        state=state,
        postal_code=postal_code,
        block=block,
        lot=lot,
        qualifier=qualifier,
        owner_reference=owner_reference,
        tax_year=tax_year,
        source_ids=source_ids or [],
        requested_record_types=requested_record_types or [],
        metadata=metadata or {},
    )


def make_public_record_source_context(
    *,
    source_id: str,
    source_name: str,
    source_type: str,
    source_url: str | None = None,
    source_status: str = SourceStatus.PLANNED.value,
    attribution: SourceAttribution | None = None,
    source_notes: list[str] | None = None,
) -> PublicRecordSourceContext:
    """
    Create public-record source context.
    """

    return PublicRecordSourceContext(
        source_id=source_id,
        source_name=source_name,
        source_type=source_type,
        source_url=source_url,
        source_status=source_status,
        attribution=attribution,
        source_notes=source_notes or [],
    )


def make_unavailable_connector_result(
    *,
    connector_id: str,
    source_id: str,
    source_name: str,
    request: PublicRecordSearchRequest | None = None,
    reason: str = "Connector is unavailable or not implemented.",
) -> PublicRecordConnectorResult:
    """
    Create unavailable connector result.
    """

    return PublicRecordConnectorResult(
        connector_id=connector_id,
        source_id=source_id,
        source_name=source_name,
        status=PublicRecordConnectorStatus.NOT_IMPLEMENTED.value,
        request=request,
        errors=[
            SourceError(
                error_type=SourceErrorType.CONNECTOR_NOT_IMPLEMENTED.value,
                message=reason,
                source_id=source_id,
                source_name=source_name,
                recoverable=True,
                retry_recommended=False,
                manual_review_required=False,
            )
        ],
        confidence_report=SourceConfidenceReport(
            confidence=0.0,
            confidence_band=SourceConfidenceBand.UNKNOWN.value,
            negative_factors=[
                "Connector not implemented.",
            ],
            missing_factors=[
                "Real source connector must be built before records are available.",
            ],
            explanation=reason,
        ),
    )


def make_empty_public_record_report(
    *,
    request: PublicRecordSearchRequest,
    reason: str = "No public records were found from connected sources.",
) -> PublicRecordReport:
    """
    Create empty public-record report.
    """

    report_id = f"public-record-report-{stable_hash(request.to_dict())[:18]}"

    warning = SourceWarning(
        warning_code="empty_public_record_report",
        message=reason,
        severity="medium",
    )

    return PublicRecordReport(
        report_id=report_id,
        request=request,
        status=PublicRecordStatus.EMPTY.value,
        confidence_report=SourceConfidenceReport(
            confidence=0.0,
            confidence_band=SourceConfidenceBand.UNKNOWN.value,
            negative_factors=[
                "No normalized records found.",
            ],
            missing_factors=[
                "Public-record source data unavailable.",
            ],
            explanation=reason,
        ),
        warnings=[warning],
        unavailable_sources=list(request.source_ids),
        generated_at=utc_now(),
    )


# ============================================================
# SECTION 36 - REPORT AGGREGATION FUNCTIONS
# ============================================================

def aggregate_connector_results(
    *,
    request: PublicRecordSearchRequest,
    connector_results: list[PublicRecordConnectorResult],
) -> PublicRecordReport:
    """
    Aggregate connector results into a public-record report.
    """

    report_id = f"public-record-report-{stable_hash({'request': request.to_dict(), 'connectors': [result.source_id for result in connector_results]})[:18]}"

    parcel_records: list[ParcelRecord] = []
    tax_assessment_records: list[TaxAssessmentRecord] = []
    property_tax_records: list[PropertyTaxRecord] = []
    building_facts_records: list[BuildingFactsRecord] = []
    recorded_document_references: list[RecordedDocumentReference] = []
    deed_records: list[DeedRecord] = []
    mortgage_records: list[MortgageRecord] = []
    lien_records: list[LienRecord] = []
    sale_history_records: list[SaleHistoryRecord] = []
    owner_reference_records: list[OwnerReferenceRecord] = []
    municipal_context_records: list[MunicipalContextRecord] = []
    gis_context_records: list[GISContextRecord] = []
    modiv_records: list[ModIVRecord] = []
    errors: list[SourceError] = []
    warnings: list[SourceWarning] = []
    unavailable_sources: list[str] = []

    for result in connector_results:
        parcel_records.extend(result.parcel_records)
        tax_assessment_records.extend(result.tax_assessment_records)
        property_tax_records.extend(result.property_tax_records)
        building_facts_records.extend(result.building_facts_records)
        recorded_document_references.extend(result.recorded_document_references)
        deed_records.extend(result.deed_records)
        mortgage_records.extend(result.mortgage_records)
        lien_records.extend(result.lien_records)
        sale_history_records.extend(result.sale_history_records)
        owner_reference_records.extend(result.owner_reference_records)
        municipal_context_records.extend(result.municipal_context_records)
        gis_context_records.extend(result.gis_context_records)
        modiv_records.extend(result.modiv_records)
        errors.extend(result.errors)
        warnings.extend(result.warnings)

        if result.status not in {
            PublicRecordConnectorStatus.AVAILABLE.value,
            PublicRecordConnectorStatus.PARTIAL.value,
        }:
            unavailable_sources.append(result.source_id)

    total_records = sum(
        [
            len(parcel_records),
            len(tax_assessment_records),
            len(property_tax_records),
            len(building_facts_records),
            len(recorded_document_references),
            len(deed_records),
            len(mortgage_records),
            len(lien_records),
            len(sale_history_records),
            len(owner_reference_records),
            len(municipal_context_records),
            len(gis_context_records),
            len(modiv_records),
        ]
    )

    if total_records > 0 and not errors:
        status = PublicRecordStatus.AVAILABLE.value
        confidence = 0.75
    elif total_records > 0 and errors:
        status = PublicRecordStatus.PARTIAL.value
        confidence = 0.55
    elif errors:
        status = PublicRecordStatus.SOURCE_ERROR.value
        confidence = 0.10
    else:
        status = PublicRecordStatus.EMPTY.value
        confidence = 0.0

    primary_parcel = parcel_records[0] if parcel_records else None
    primary_address = None

    if primary_parcel and primary_parcel.address:
        primary_address = primary_parcel.address
    elif tax_assessment_records and tax_assessment_records[0].address:
        primary_address = tax_assessment_records[0].address
    elif request.address:
        primary_address = request.address

    confidence_report = SourceConfidenceReport(
        confidence=confidence,
        confidence_band=confidence_band(confidence).value,
        positive_factors=[
            "At least one public-record connector returned normalized records."
        ] if total_records else [],
        negative_factors=[
            "One or more public-record connectors returned errors."
        ] if errors else [],
        missing_factors=[
            "No normalized public records were found."
        ] if total_records == 0 else [],
        manual_review_required=bool(errors),
        explanation=(
            "Public-record report was built from connected source results."
            if total_records
            else "No public-record facts are available from connected sources yet."
        ),
    )

    return PublicRecordReport(
        report_id=report_id,
        request=request,
        status=status,
        connector_results=connector_results,
        primary_address=primary_address,
        primary_parcel=primary_parcel,
        parcel_records=parcel_records,
        tax_assessment_records=tax_assessment_records,
        property_tax_records=property_tax_records,
        building_facts_records=building_facts_records,
        recorded_document_references=recorded_document_references,
        deed_records=deed_records,
        mortgage_records=mortgage_records,
        lien_records=lien_records,
        sale_history_records=sale_history_records,
        owner_reference_records=owner_reference_records,
        municipal_context_records=municipal_context_records,
        gis_context_records=gis_context_records,
        modiv_records=modiv_records,
        confidence_report=confidence_report,
        errors=errors,
        warnings=warnings,
        unavailable_sources=unavailable_sources,
        manual_review_required=bool(errors),
        metadata={
            "total_records": total_records,
            "connector_count": len(connector_results),
        },
    )


# ============================================================
# SECTION 37 - DASHBOARD SUMMARY FUNCTIONS
# ============================================================

def build_public_record_summary_cards(
    report: PublicRecordReport,
) -> list[PublicRecordSummaryCard]:
    """
    Build dashboard-ready summary cards.
    """

    cards: list[PublicRecordSummaryCard] = []

    cards.append(
        PublicRecordSummaryCard(
            title="Public Records",
            status=report.status,
            value=report.total_records_found(),
            subtitle="Normalized records found",
            confidence=(
                report.confidence_report.confidence
                if report.confidence_report
                else 0.0
            ),
            source_label="Connected public-record sources",
            source_status=report.status,
            explanation=(
                "Public-record data is available."
                if report.total_records_found()
                else "No public-record data is available from connected sources yet."
            ),
        )
    )

    cards.append(
        PublicRecordSummaryCard(
            title="Parcel",
            status=(
                PublicRecordStatus.AVAILABLE.value
                if report.parcel_records
                else PublicRecordStatus.UNAVAILABLE.value
            ),
            value=(
                report.primary_parcel.parcel_identifier.display_key()
                if report.primary_parcel
                else None
            ),
            subtitle="Primary parcel identity",
            confidence=(
                report.primary_parcel.confidence
                if report.primary_parcel
                else 0.0
            ),
            source_label=(
                report.primary_parcel.source_context.source_name
                if report.primary_parcel and report.primary_parcel.source_context
                else None
            ),
            source_status=(
                report.primary_parcel.status
                if report.primary_parcel
                else PublicRecordStatus.UNAVAILABLE.value
            ),
            explanation=(
                "Parcel record found."
                if report.primary_parcel
                else "No parcel record has been confirmed yet."
            ),
        )
    )

    latest_assessment = None

    if report.tax_assessment_records:
        latest_assessment = sorted(
            report.tax_assessment_records,
            key=lambda item: item.tax_year or 0,
            reverse=True,
        )[0]

    cards.append(
        PublicRecordSummaryCard(
            title="Assessment",
            status=(
                PublicRecordStatus.AVAILABLE.value
                if latest_assessment
                else PublicRecordStatus.UNAVAILABLE.value
            ),
            value=(
                latest_assessment.total_assessed_value
                if latest_assessment
                else None
            ),
            subtitle=(
                f"Tax year {latest_assessment.tax_year}"
                if latest_assessment and latest_assessment.tax_year
                else "Tax assessment"
            ),
            confidence=(
                latest_assessment.confidence
                if latest_assessment
                else 0.0
            ),
            source_label=(
                latest_assessment.source_context.source_name
                if latest_assessment and latest_assessment.source_context
                else None
            ),
            source_status=(
                latest_assessment.status
                if latest_assessment
                else PublicRecordStatus.UNAVAILABLE.value
            ),
            explanation=(
                "Tax assessment found."
                if latest_assessment
                else "Tax assessment has not been confirmed yet."
            ),
        )
    )

    latest_sale = None

    if report.sale_history_records:
        latest_sale = sorted(
            report.sale_history_records,
            key=lambda item: item.sale_date or "",
            reverse=True,
        )[0]

    cards.append(
        PublicRecordSummaryCard(
            title="Sale History",
            status=(
                PublicRecordStatus.AVAILABLE.value
                if latest_sale
                else PublicRecordStatus.UNAVAILABLE.value
            ),
            value=(
                latest_sale.sale_price
                if latest_sale
                else None
            ),
            subtitle=(
                latest_sale.sale_date
                if latest_sale and latest_sale.sale_date
                else "Recorded sales"
            ),
            confidence=latest_sale.confidence if latest_sale else 0.0,
            source_label=(
                latest_sale.source_context.source_name
                if latest_sale and latest_sale.source_context
                else None
            ),
            source_status=(
                latest_sale.status
                if latest_sale
                else PublicRecordStatus.UNAVAILABLE.value
            ),
            explanation=(
                "Sale-history reference found."
                if latest_sale
                else "No sale-history reference has been confirmed yet."
            ),
        )
    )

    cards.append(
        PublicRecordSummaryCard(
            title="Listing Status",
            status=PublicRecordStatus.UNAVAILABLE.value,
            value=None,
            subtitle="Requires MLS, IDX, broker feed, or listing provider",
            confidence=0.0,
            source_label="Public records cannot prove current listing status",
            source_status=PublicRecordStatus.UNAVAILABLE.value,
            explanation=(
                "Public records may support parcel, tax, deed, and sale-history "
                "context, but they do not prove active or under-contract status."
            ),
        )
    )

    return cards


# ============================================================
# SECTION 38 - MODEL REGISTRY
# ============================================================

PUBLIC_RECORD_MODEL_REGISTRY = {
    "PublicRecordSourceContext": PublicRecordSourceContext,
    "PublicRecordAddress": PublicRecordAddress,
    "ParcelIdentifier": ParcelIdentifier,
    "ParcelRecord": ParcelRecord,
    "TaxAssessmentRecord": TaxAssessmentRecord,
    "PropertyTaxRecord": PropertyTaxRecord,
    "BuildingFactsRecord": BuildingFactsRecord,
    "RecordedDocumentReference": RecordedDocumentReference,
    "DeedRecord": DeedRecord,
    "MortgageRecord": MortgageRecord,
    "LienRecord": LienRecord,
    "SaleHistoryRecord": SaleHistoryRecord,
    "OwnerReferenceRecord": OwnerReferenceRecord,
    "MunicipalContextRecord": MunicipalContextRecord,
    "GISContextRecord": GISContextRecord,
    "ModIVRecord": ModIVRecord,
    "PublicRecordSearchRequest": PublicRecordSearchRequest,
    "PublicRecordConnectorResult": PublicRecordConnectorResult,
    "PublicRecordReport": PublicRecordReport,
    "PublicRecordFact": PublicRecordFact,
    "PublicRecordSummaryCard": PublicRecordSummaryCard,
    "PublicRecordValidationIssue": PublicRecordValidationIssue,
    "PublicRecordValidationReport": PublicRecordValidationReport,
}


# ============================================================
# SECTION 39 - MODULE DIAGNOSTICS
# ============================================================

def get_public_record_models_metadata() -> dict[str, Any]:
    """
    Return module metadata.
    """

    return {
        "name": PUBLIC_RECORD_MODELS_NAME,
        "version": PUBLIC_RECORD_MODELS_VERSION,
        "phase": PUBLIC_RECORD_MODELS_PHASE,
        "status": PUBLIC_RECORD_MODELS_STATUS,
        "model_count": len(PUBLIC_RECORD_MODEL_REGISTRY),
        "generated_at": utc_now(),
    }


def get_public_record_model_names() -> list[str]:
    """
    Return public-record model names.
    """

    return list(PUBLIC_RECORD_MODEL_REGISTRY.keys())


def get_public_record_enum_summary() -> dict[str, list[str]]:
    """
    Return enum summary.
    """

    return {
        "PublicRecordType": [item.value for item in PublicRecordType],
        "PublicRecordStatus": [item.value for item in PublicRecordStatus],
        "PublicRecordConfidence": [item.value for item in PublicRecordConfidence],
        "PropertyClass": [item.value for item in PropertyClass],
        "RecordedDocumentType": [item.value for item in RecordedDocumentType],
        "SaleType": [item.value for item in SaleType],
        "PublicRecordConnectorStatus": [
            item.value
            for item in PublicRecordConnectorStatus
        ],
    }


def get_public_record_models_health() -> dict[str, Any]:
    """
    Return lightweight health payload.
    """

    return {
        "name": PUBLIC_RECORD_MODELS_NAME,
        "version": PUBLIC_RECORD_MODELS_VERSION,
        "phase": PUBLIC_RECORD_MODELS_PHASE,
        "status": PUBLIC_RECORD_MODELS_STATUS,
        "model_count": len(PUBLIC_RECORD_MODEL_REGISTRY),
        "no_mock_data": True,
        "listing_status_requires_listing_source": True,
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 40 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "PUBLIC_RECORD_MODELS_NAME",
    "PUBLIC_RECORD_MODELS_VERSION",
    "PUBLIC_RECORD_MODELS_PHASE",
    "PUBLIC_RECORD_MODELS_STATUS",
    "PublicRecordType",
    "PublicRecordStatus",
    "PublicRecordConfidence",
    "PropertyClass",
    "RecordedDocumentType",
    "SaleType",
    "PublicRecordConnectorStatus",
    "PublicRecordSourceContext",
    "PublicRecordAddress",
    "ParcelIdentifier",
    "ParcelRecord",
    "TaxAssessmentRecord",
    "PropertyTaxRecord",
    "BuildingFactsRecord",
    "RecordedDocumentReference",
    "DeedRecord",
    "MortgageRecord",
    "LienRecord",
    "SaleHistoryRecord",
    "OwnerReferenceRecord",
    "MunicipalContextRecord",
    "GISContextRecord",
    "ModIVRecord",
    "PublicRecordSearchRequest",
    "PublicRecordConnectorResult",
    "PublicRecordReport",
    "PublicRecordFact",
    "PublicRecordSummaryCard",
    "PublicRecordValidationIssue",
    "PublicRecordValidationReport",
    "PUBLIC_RECORD_MODEL_REGISTRY",
    "utc_now",
    "stable_hash",
    "safe_string",
    "safe_upper",
    "safe_float",
    "safe_int",
    "normalize_block_lot",
    "normalize_state",
    "normalize_county",
    "normalize_municipality",
    "normalize_money",
    "normalize_area",
    "normalize_year",
    "make_public_record_id",
    "validate_parcel_record",
    "validate_tax_assessment_record",
    "validate_public_record_report",
    "make_public_record_search_request",
    "make_public_record_source_context",
    "make_unavailable_connector_result",
    "make_empty_public_record_report",
    "aggregate_connector_results",
    "build_public_record_summary_cards",
    "get_public_record_models_metadata",
    "get_public_record_model_names",
    "get_public_record_enum_summary",
    "get_public_record_models_health",
]


# ============================================================
# END OF FILE
# ============================================================