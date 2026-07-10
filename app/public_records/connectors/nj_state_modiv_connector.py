# ============================================================
# AUSSEM1
# PHASE 2.30 PART 3.00
# ENTERPRISE NEW JERSEY STATE MOD-IV CONNECTOR
# FILE: app/public_records/connectors/nj_state_modiv_connector.py
# PURPOSE:
# Provide the official-source connector scaffold for New Jersey
# statewide parcel and MOD-IV composite public-record data.
#
# This connector is designed to support:
# - statewide parcel identity
# - MOD-IV assessment context
# - block / lot / qualifier references
# - municipality / county / state parcel context
# - property class references
# - land / improvement / total assessment references
# - public-record source attribution
# - explicit unavailable/manual-review states
#
# This file does not create mock property records.
# This file does not fabricate parcel records.
# This file does not fabricate MOD-IV fields.
# This file does not fabricate assessment values.
# This file does not fabricate owner conclusions.
# This file does not claim MLS active status.
# This file does not claim under-contract status.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# REAL STATE MOD-IV PUBLIC RECORD CONNECTOR FOUNDATION ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from urllib.parse import quote_plus

from app.public_records.connectors.base_connector import BasePublicRecordConnector
from app.public_records.connectors.base_connector import collapse_whitespace
from app.public_records.connectors.base_connector import infer_query_mode
from app.public_records.connectors.base_connector import normalize_html_text
from app.public_records.connectors.base_connector import normalize_public_record_key
from app.public_records.connectors.base_connector import utc_now
from app.public_records.models import BuildingFactsRecord
from app.public_records.models import ModIVRecord
from app.public_records.models import OwnerReferenceRecord
from app.public_records.models import ParcelIdentifier
from app.public_records.models import ParcelRecord
from app.public_records.models import PropertyClass
from app.public_records.models import PropertyTaxRecord
from app.public_records.models import PublicRecordAddress
from app.public_records.models import PublicRecordConnectorResult
from app.public_records.models import PublicRecordConnectorStatus
from app.public_records.models import PublicRecordSearchRequest
from app.public_records.models import PublicRecordStatus
from app.public_records.models import TaxAssessmentRecord
from app.public_records.models import make_public_record_id
from app.public_records.models import normalize_area
from app.public_records.models import normalize_money
from app.public_records.models import normalize_year
from app.sources.source_client import SourceHttpResponse
from app.sources.source_models import SourceAccessMethod
from app.sources.source_models import SourceDataFormat
from app.sources.source_models import SourceError
from app.sources.source_models import SourceErrorType
from app.sources.source_models import SourceRequestPolicy
from app.sources.source_models import SourceType
from app.sources.source_models import SourceWarning


# ============================================================
# SECTION 02 - CONNECTOR METADATA
# ============================================================

NJ_STATE_MODIV_CONNECTOR_NAME = (
    "Aussem1 New Jersey State MOD-IV Parcel Connector"
)

NJ_STATE_MODIV_CONNECTOR_VERSION = "0.1.0"

NJ_STATE_MODIV_CONNECTOR_PHASE = "PHASE 2.30 PART 3.00"

NJ_STATE_MODIV_CONNECTOR_STATUS = (
    "real_public_record_state_modiv_connector_foundation_active"
)

NJ_STATE_MODIV_SOURCE_ID = "nj_state_parcels_modiv_composite"

NJ_STATE_MODIV_SOURCE_NAME = "New Jersey Parcels and MOD-IV Composite"

NJ_STATE_MODIV_SOURCE_URL = (
    "https://njogis-newjersey.opendata.arcgis.com/documents/"
    "newjersey%3A%3Aparcels-and-mod-iv-composite-of-nj-download/about"
)

NJ_STATE_MODIV_JURISDICTION = "State of New Jersey"

NJ_STATE_MODIV_STATE = "NJ"

NJ_STATE_MODIV_COUNTY_SCOPE = "statewide"


# ============================================================
# SECTION 03 - CONNECTOR GOVERNANCE
# ============================================================

NJ_STATE_MODIV_GOVERNANCE = {
    "official_source": True,
    "statewide_public_record_source": True,
    "mock_records_allowed": False,
    "fabricated_records_allowed": False,
    "fabricated_parcel_allowed": False,
    "fabricated_assessment_allowed": False,
    "fabricated_modiv_allowed": False,
    "fabricated_owner_allowed": False,
    "fabricated_market_value_allowed": False,
    "fabricated_listing_status_allowed": False,
    "active_listing_status_allowed": False,
    "under_contract_status_allowed": False,
    "source_attribution_required": True,
    "manual_review_for_ambiguous_matches": True,
    "manual_review_for_conflicting_records": True,
    "public_records_only": True,
    "listing_feed_required_for_listing_status": True,
    "assessment_is_not_market_value": True,
    "modiv_context_is_not_legal_advice": True,
}


# ============================================================
# SECTION 04 - SUPPORTED AND UNSUPPORTED CLAIMS
# ============================================================

NJ_STATE_MODIV_SUPPORTED_CLAIMS = [
    "address_identity",
    "parcel_identity",
    "pams_pin_reference",
    "block_lot_reference",
    "municipality",
    "county",
    "state",
    "statewide_parcel_context",
    "modiv_context",
    "tax_assessment",
    "land_value",
    "improvement_value",
    "total_assessed_value",
    "property_class",
    "building_facts_where_source_supported",
    "year_built_where_source_supported",
    "building_area_where_source_supported",
    "lot_size_where_source_supported",
    "owner_reference_where_source_supported",
]


NJ_STATE_MODIV_UNSUPPORTED_CLAIMS = [
    "active_listing_status",
    "under_contract_status",
    "pending_status",
    "current_listing_price",
    "current_days_on_market",
    "current_showing_availability",
    "current_offer_deadline",
    "current_mls_status",
    "current_broker_confirmation",
    "legal_boundary_survey",
    "title_clearance",
    "current_market_value",
    "current_owner_without_crosscheck",
    "mortgage_status",
    "lien_status",
]


NJ_STATE_MODIV_SUPPORTED_QUERY_MODES = [
    "address",
    "block_lot",
    "owner_reference",
]


# ============================================================
# SECTION 05 - MOD-IV FIELD ALIASES
# ============================================================

MODIV_FIELD_ALIASES = {
    "address": [
        "address",
        "property address",
        "location",
        "property location",
        "site address",
        "prop loc",
    ],
    "municipality": [
        "municipality",
        "muni",
        "muni name",
        "tax district",
        "district",
        "town",
        "city",
        "borough",
        "township",
    ],
    "municipality_code": [
        "municipality code",
        "muni code",
        "district code",
        "tax district code",
    ],
    "county": [
        "county",
        "county name",
    ],
    "county_code": [
        "county code",
        "cnty code",
    ],
    "block": [
        "block",
        "blk",
        "tax block",
    ],
    "lot": [
        "lot",
        "lt",
        "tax lot",
    ],
    "qualifier": [
        "qualifier",
        "qual",
        "q",
    ],
    "parcel_id": [
        "parcel",
        "parcel id",
        "parcel identifier",
        "pin",
        "pams pin",
        "pams_pin",
        "gis pin",
    ],
    "property_class": [
        "class",
        "property class",
        "prop class",
        "property_class",
        "land use",
    ],
    "owner": [
        "owner",
        "owner name",
        "taxpayer",
        "assessed owner",
    ],
    "land_value": [
        "land",
        "land value",
        "land assessment",
        "assessed land",
    ],
    "improvement_value": [
        "improvement",
        "improvements",
        "improvement value",
        "building value",
        "improvement assessment",
        "assessed improvement",
    ],
    "total_assessed_value": [
        "total",
        "total value",
        "total assessment",
        "total assessed",
        "assessment",
        "net value",
    ],
    "tax_year": [
        "tax year",
        "year",
        "assessment year",
        "mod4 year",
        "mod iv year",
    ],
    "lot_size": [
        "lot size",
        "land area",
        "area",
        "acreage",
        "acres",
        "sq ft",
        "square feet",
    ],
    "lot_size_acres": [
        "acres",
        "acreage",
        "lot acres",
    ],
    "lot_size_sqft": [
        "sq ft",
        "square feet",
        "lot sqft",
        "lot square feet",
    ],
    "year_built": [
        "year built",
        "yr built",
        "built",
        "construction year",
    ],
    "building_area_sqft": [
        "building area",
        "living area",
        "gross area",
        "sq ft building",
        "building square feet",
    ],
    "latitude": [
        "latitude",
        "lat",
        "y",
    ],
    "longitude": [
        "longitude",
        "lon",
        "lng",
        "x",
    ],
    "geometry_reference": [
        "geometry",
        "shape",
        "shape id",
        "map reference",
        "geometry reference",
    ],
}


# ============================================================
# SECTION 06 - MOD-IV SEARCH TARGET MODEL
# ============================================================

@dataclass
class ModIVSearchTarget:
    """
    Search target representation for NJ statewide MOD-IV source.
    """

    mode: str
    base_url: str
    query_label: str
    query_value: str | None = None
    municipality: str | None = None
    county: str | None = None
    block: str | None = None
    lot: str | None = None
    qualifier: str | None = None
    owner_reference: str | None = None
    raw_query: str | None = None
    url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert target to dictionary.
        """

        return {
            "mode": self.mode,
            "base_url": self.base_url,
            "query_label": self.query_label,
            "query_value": self.query_value,
            "municipality": self.municipality,
            "county": self.county,
            "block": self.block,
            "lot": self.lot,
            "qualifier": self.qualifier,
            "owner_reference": self.owner_reference,
            "raw_query": self.raw_query,
            "url": self.url,
            "metadata": self.metadata,
        }


# ============================================================
# SECTION 07 - MOD-IV PARSE RESULT MODEL
# ============================================================

@dataclass
class ModIVParseResult:
    """
    Conservative parse result for NJ MOD-IV responses.
    """

    parsed: bool = False
    raw_text_available: bool = False
    candidate_count: int = 0
    normalized_fields: dict[str, Any] = field(default_factory=dict)
    candidate_records: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)
    errors: list[SourceError] = field(default_factory=list)
    manual_review_required: bool = False
    parser_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert parse result to dictionary.
        """

        return {
            "parsed": self.parsed,
            "raw_text_available": self.raw_text_available,
            "candidate_count": self.candidate_count,
            "normalized_fields": self.normalized_fields,
            "candidate_records": self.candidate_records,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
            "errors": [
                error.to_dict()
                for error in self.errors
            ],
            "manual_review_required": self.manual_review_required,
            "parser_notes": self.parser_notes,
        }


# ============================================================
# SECTION 08 - UTILITY FUNCTIONS
# ============================================================

def clean_modiv_text(
    value: Any,
) -> str:
    """
    Clean text from MOD-IV response.
    """

    text = normalize_html_text(value)

    text = text.replace("\xa0", " ")

    return collapse_whitespace(text)


def normalize_modiv_money(
    value: Any,
) -> float | None:
    """
    Normalize MOD-IV money/assessment field.
    """

    return normalize_money(value)


def normalize_modiv_area(
    value: Any,
) -> float | None:
    """
    Normalize MOD-IV area field.
    """

    return normalize_area(value)


def normalize_modiv_year(
    value: Any,
) -> int | None:
    """
    Normalize MOD-IV year field.
    """

    return normalize_year(value)


def normalize_modiv_coordinate(
    value: Any,
) -> float | None:
    """
    Normalize MOD-IV coordinate field.
    """

    if value is None:
        return None

    text = clean_modiv_text(value)
    text = text.replace(",", "")

    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def make_modiv_warning(
    *,
    warning_code: str,
    message: str,
    severity: str = "medium",
) -> SourceWarning:
    """
    Build standardized MOD-IV warning.
    """

    return SourceWarning(
        warning_code=warning_code,
        message=message,
        severity=severity,
        source_id=NJ_STATE_MODIV_SOURCE_ID,
    )


def make_modiv_error(
    *,
    error_type: str,
    message: str,
    recoverable: bool = True,
    retry_recommended: bool = False,
    manual_review_required: bool = False,
) -> SourceError:
    """
    Build standardized MOD-IV error.
    """

    return SourceError(
        error_type=error_type,
        message=message,
        source_id=NJ_STATE_MODIV_SOURCE_ID,
        source_name=NJ_STATE_MODIV_SOURCE_NAME,
        recoverable=recoverable,
        retry_recommended=retry_recommended,
        manual_review_required=manual_review_required,
    )


def alias_matches(
    key: str,
    aliases: list[str],
) -> bool:
    """
    Return whether normalized key matches aliases.
    """

    normalized_key = normalize_public_record_key(key)

    normalized_aliases = {
        normalize_public_record_key(alias)
        for alias in aliases
    }

    return normalized_key in normalized_aliases


def resolve_modiv_field(
    key: str,
) -> str | None:
    """
    Resolve MOD-IV field alias into canonical field.
    """

    for canonical, aliases in MODIV_FIELD_ALIASES.items():
        if alias_matches(key, aliases):
            return canonical

    return None


def extract_label_value_pairs_from_text(
    text: str,
) -> dict[str, str]:
    """
    Extract conservative label-value pairs from visible text.

    This does not guess missing values.
    It only extracts explicit label/value patterns.
    """

    pairs: dict[str, str] = {}

    if not text:
        return pairs

    lines = [
        clean_modiv_text(line)
        for line in text.splitlines()
        if clean_modiv_text(line)
    ]

    for line in lines:
        if ":" in line:
            raw_key, raw_value = line.split(":", 1)
            key = normalize_public_record_key(raw_key)
            value = clean_modiv_text(raw_value)

            if key and value:
                pairs[key] = value

    return pairs


def extract_candidate_modiv_rows(
    text: str,
) -> list[dict[str, Any]]:
    """
    Extract conservative candidate MOD-IV rows from text.

    This function only returns candidates when explicit block/lot or
    parcel-like signals are found. It does not generate final records.
    """

    candidates: list[dict[str, Any]] = []

    if not text:
        return candidates

    cleaned = clean_modiv_text(text)

    block_lot_pattern = re.compile(
        r"\b(?:block|blk)\s*[:#]?\s*([A-Za-z0-9.\-]+)\s+"
        r"(?:lot|lt)\s*[:#]?\s*([A-Za-z0-9.\-]+)",
        re.IGNORECASE,
    )

    parcel_pattern = re.compile(
        r"\b(?:parcel|pin|pams\s*pin)\s*[:#]?\s*([A-Za-z0-9.\-]+)",
        re.IGNORECASE,
    )

    assessment_pattern = re.compile(
        r"\b(?:assessment|total\s+assessment|total\s+assessed)"
        r"\s*[:#]?\s*\$?\s*([0-9,]+(?:\.[0-9]{1,2})?)",
        re.IGNORECASE,
    )

    for match in block_lot_pattern.finditer(cleaned):
        candidates.append(
            {
                "block": match.group(1),
                "lot": match.group(2),
                "evidence": match.group(0),
                "confidence_hint": 0.35,
                "manual_review_required": True,
            }
        )

    for match in parcel_pattern.finditer(cleaned):
        candidates.append(
            {
                "parcel_id": match.group(1),
                "evidence": match.group(0),
                "confidence_hint": 0.35,
                "manual_review_required": True,
            }
        )

    for match in assessment_pattern.finditer(cleaned):
        candidates.append(
            {
                "total_assessed_value": match.group(1),
                "evidence": match.group(0),
                "confidence_hint": 0.35,
                "manual_review_required": True,
            }
        )

    return candidates


def normalize_modiv_fields(
    raw_fields: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize raw MOD-IV fields into canonical keys.
    """

    normalized: dict[str, Any] = {}

    for raw_key, raw_value in raw_fields.items():
        canonical = resolve_modiv_field(raw_key)

        if not canonical:
            continue

        value = clean_modiv_text(raw_value)

        if not value:
            continue

        normalized[canonical] = value

    return normalized


def build_modiv_confidence(
    *,
    has_parcel: bool,
    has_address: bool,
    has_municipality: bool,
    has_assessment: bool,
    has_property_class: bool,
    parser_manual_review: bool,
    source_successful: bool,
) -> float:
    """
    Build conservative confidence score for MOD-IV parse.
    """

    if not source_successful:
        return 0.0

    score = 0.20

    if has_parcel:
        score += 0.25

    if has_address:
        score += 0.10

    if has_municipality:
        score += 0.10

    if has_assessment:
        score += 0.20

    if has_property_class:
        score += 0.05

    if parser_manual_review:
        score -= 0.20

    return max(0.0, min(0.85, score))


# ============================================================
# SECTION 09 - CONNECTOR CLASS
# ============================================================

class NJStateModIVConnector(BasePublicRecordConnector):
    """
    New Jersey State MOD-IV connector.

    This connector provides source-governed access and conservative
    parsing scaffolding for the New Jersey statewide Parcels and MOD-IV
    composite public-record source.

    It does not fabricate records. If records cannot be confidently
    parsed, it returns an empty or manual-review result.
    """

    connector_id = "nj_state_modiv_connector"
    connector_name = NJ_STATE_MODIV_CONNECTOR_NAME
    connector_version = NJ_STATE_MODIV_CONNECTOR_VERSION
    connector_phase = NJ_STATE_MODIV_CONNECTOR_PHASE

    source_id = NJ_STATE_MODIV_SOURCE_ID
    source_name = NJ_STATE_MODIV_SOURCE_NAME
    source_type = SourceType.PUBLIC_RECORD.value
    source_url = NJ_STATE_MODIV_SOURCE_URL
    documentation_url = NJ_STATE_MODIV_SOURCE_URL

    jurisdiction = NJ_STATE_MODIV_JURISDICTION
    state = NJ_STATE_MODIV_STATE
    county = None
    municipality = None

    access_method = SourceAccessMethod.OPEN_DATA_PORTAL.value
    data_format = SourceDataFormat.HTML.value
    status = PublicRecordConnectorStatus.READY.value

    supported_claims = NJ_STATE_MODIV_SUPPORTED_CLAIMS
    unsupported_claims = NJ_STATE_MODIV_UNSUPPORTED_CLAIMS
    supported_query_modes = NJ_STATE_MODIV_SUPPORTED_QUERY_MODES

    def __init__(
        self,
        *,
        request_policy: SourceRequestPolicy | None = None,
    ) -> None:
        super().__init__(
            request_policy=request_policy
            or SourceRequestPolicy(
                timeout_seconds=30,
                max_retries=1,
                respect_rate_limits=True,
                user_agent_required=True,
                uncontrolled_scraping_allowed=False,
                bypass_access_controls_allowed=False,
                store_raw_payload=False,
                manual_review_on_ambiguity=True,
                notes=[
                    "New Jersey statewide MOD-IV governed public data connector.",
                    "No fake parcel records.",
                    "No fake assessment values.",
                    "No active listing status claims.",
                    "Manual review required when parsing is ambiguous.",
                ],
            )
        )

    # ========================================================
    # SECTION 09.01 - CONNECTOR IDENTITY
    # ========================================================

    def connector_key(
        self,
    ) -> str:
        """
        Return connector key.
        """

        return "nj_state_modiv_connector"

    def get_governance(
        self,
    ) -> dict[str, Any]:
        """
        Return connector governance rules.
        """

        governance = super().get_governance()

        governance.update(NJ_STATE_MODIV_GOVERNANCE)

        return governance

    # ========================================================
    # SECTION 09.02 - SEARCH TARGET BUILDERS
    # ========================================================

    def build_search_target(
        self,
        request: PublicRecordSearchRequest,
    ) -> ModIVSearchTarget:
        """
        Build conservative MOD-IV search target.
        """

        query_mode = infer_query_mode(request)

        if query_mode == "block_lot":
            query_value = f"{request.block} / {request.lot}"

            if request.qualifier:
                query_value = f"{query_value} / {request.qualifier}"

            return ModIVSearchTarget(
                mode=query_mode,
                base_url=self.source_url or NJ_STATE_MODIV_SOURCE_URL,
                query_label="block_lot",
                query_value=query_value,
                municipality=request.municipality,
                county=request.county,
                block=request.block,
                lot=request.lot,
                qualifier=request.qualifier,
                raw_query=request.raw_query,
                url=self.source_url,
                metadata={
                    "source_note": (
                        "Statewide MOD-IV source may require dataset download, "
                        "API layer access, or future ETL indexing. Connector "
                        "preserves source context and search target."
                    ),
                },
            )

        if query_mode == "owner_reference":
            return ModIVSearchTarget(
                mode=query_mode,
                base_url=self.source_url or NJ_STATE_MODIV_SOURCE_URL,
                query_label="owner_reference",
                query_value=request.owner_reference,
                municipality=request.municipality,
                county=request.county,
                owner_reference=request.owner_reference,
                raw_query=request.raw_query,
                url=self.source_url,
                metadata={
                    "encoded_owner_reference": quote_plus(
                        request.owner_reference or ""
                    ),
                    "source_note": (
                        "Owner reference lookup in statewide MOD-IV data "
                        "requires source-supported fields or local indexing."
                    ),
                },
            )

        address_value = (
            request.street_address
            or request.raw_query
            or (
                request.address.normalized_address
                if request.address
                else None
            )
        )

        return ModIVSearchTarget(
            mode=query_mode,
            base_url=self.source_url or NJ_STATE_MODIV_SOURCE_URL,
            query_label="address",
            query_value=address_value,
            municipality=request.municipality,
            county=request.county,
            raw_query=request.raw_query,
            url=self.source_url,
            metadata={
                "encoded_address": quote_plus(address_value or ""),
                "source_note": (
                    "Address-based MOD-IV lookup may require future ETL "
                    "indexing or source-specific query automation."
                ),
            },
        )

    # ========================================================
    # SECTION 09.03 - MAIN SEARCH
    # ========================================================

    def search(
        self,
        request: PublicRecordSearchRequest,
    ) -> PublicRecordConnectorResult:
        """
        Execute MOD-IV lookup lifecycle.

        This version safely probes the official open-data source URL and
        returns conservative normalized data only when explicit parseable
        facts exist in the response.

        If the source page is only a dataset landing page or returns no
        parseable parcel data, the connector returns an empty/manual-review
        result rather than fabricating a MOD-IV record.
        """

        validation = self.validate_request(request)

        if not validation.valid:
            return self.make_error_result(
                request=request,
                errors=validation.errors,
                warnings=validation.warnings,
                status=PublicRecordConnectorStatus.ERROR.value,
                explanation="New Jersey MOD-IV request validation failed.",
            )

        search_target = self.build_search_target(request)

        response = self.get_source_homepage()

        if response is None:
            return self.make_error_result(
                request=request,
                errors=[
                    make_modiv_error(
                        error_type=SourceErrorType.SOURCE_UNAVAILABLE.value,
                        message="New Jersey MOD-IV source URL is unavailable.",
                        recoverable=True,
                        retry_recommended=True,
                    )
                ],
                status=PublicRecordConnectorStatus.ERROR.value,
                explanation="MOD-IV source URL is unavailable.",
            )

        source_result = self.make_source_result_from_http_response(
            response=response,
            request=request,
        )

        if not response.is_successful():
            return self.make_error_result(
                request=request,
                errors=list(response.errors)
                or [
                    make_modiv_error(
                        error_type=SourceErrorType.SOURCE_UNAVAILABLE.value,
                        message="New Jersey MOD-IV source request failed.",
                        recoverable=True,
                        retry_recommended=True,
                    )
                ],
                warnings=list(response.warnings),
                status=PublicRecordConnectorStatus.ERROR.value,
                explanation="MOD-IV source request did not complete successfully.",
            )

        parsed = self.parse_modiv_response(
            response=response,
            request=request,
            search_target=search_target,
        )

        if parsed.errors:
            return self.make_error_result(
                request=request,
                errors=parsed.errors,
                warnings=parsed.warnings,
                status=PublicRecordConnectorStatus.ERROR.value,
                explanation="MOD-IV response parsing returned errors.",
            )

        normalized_result = self.build_connector_result_from_parse(
            request=request,
            response=response,
            source_result=source_result,
            search_target=search_target,
            parse_result=parsed,
        )

        return normalized_result

    # ========================================================
    # SECTION 09.04 - PARSER
    # ========================================================

    def parse_modiv_response(
        self,
        *,
        response: SourceHttpResponse,
        request: PublicRecordSearchRequest,
        search_target: ModIVSearchTarget,
    ) -> ModIVParseResult:
        """
        Parse MOD-IV source response conservatively.
        """

        result = ModIVParseResult()

        text = response.text or ""

        if not text:
            result.warnings.append(
                make_modiv_warning(
                    warning_code="empty_modiv_response",
                    message="New Jersey MOD-IV source response contained no text.",
                    severity="medium",
                )
            )
            result.parser_notes.append(
                "No text available from source response."
            )
            return result

        result.raw_text_available = True

        pairs = extract_label_value_pairs_from_text(text)
        normalized_fields = normalize_modiv_fields(pairs)
        candidates = extract_candidate_modiv_rows(text)

        result.normalized_fields = normalized_fields
        result.candidate_records = candidates
        result.candidate_count = len(candidates)

        has_direct_fields = bool(normalized_fields)
        has_candidates = bool(candidates)

        if has_direct_fields:
            result.parsed = True
            result.parser_notes.append(
                "Explicit label/value MOD-IV fields were found."
            )

        if has_candidates:
            result.parsed = True
            result.manual_review_required = True
            result.warnings.append(
                make_modiv_warning(
                    warning_code="candidate_modiv_records_require_review",
                    message=(
                        "Potential MOD-IV record candidates were found but "
                        "require manual review before being treated as authoritative."
                    ),
                    severity="medium",
                )
            )

        if not has_direct_fields and not has_candidates:
            result.warnings.append(
                make_modiv_warning(
                    warning_code="no_parseable_modiv_record",
                    message=(
                        "MOD-IV source responded, but no explicit parseable "
                        "parcel or assessment fields were found."
                    ),
                    severity="medium",
                )
            )
            result.parser_notes.append(
                "Dataset landing page or metadata page likely returned."
            )

        query_mode = infer_query_mode(request)

        result.parser_notes.append(
            f"Query mode: {query_mode}."
        )

        result.parser_notes.append(
            f"Search target: {search_target.query_label}."
        )

        return result

    def parse_source_response(
        self,
        *,
        response: SourceHttpResponse,
        request: PublicRecordSearchRequest,
    ) -> PublicRecordConnectorResult:
        """
        Base connector parser bridge.
        """

        search_target = self.build_search_target(request)

        parse_result = self.parse_modiv_response(
            response=response,
            request=request,
            search_target=search_target,
        )

        source_result = self.make_source_result_from_http_response(
            response=response,
            request=request,
        )

        return self.build_connector_result_from_parse(
            request=request,
            response=response,
            source_result=source_result,
            search_target=search_target,
            parse_result=parse_result,
        )

    # ========================================================
    # SECTION 09.05 - NORMALIZATION FROM PARSE
    # ========================================================

    def build_connector_result_from_parse(
        self,
        *,
        request: PublicRecordSearchRequest,
        response: SourceHttpResponse,
        source_result: Any,
        search_target: ModIVSearchTarget,
        parse_result: ModIVParseResult,
    ) -> PublicRecordConnectorResult:
        """
        Convert conservative parse result into connector result.
        """

        fields = parse_result.normalized_fields

        if not fields and not parse_result.candidate_records:
            return self.empty_result(
                request=request,
                explanation=(
                    "New Jersey MOD-IV source responded, but no explicit "
                    "parcel or assessment data was available to normalize."
                ),
                warnings=parse_result.warnings
                + [
                    make_modiv_warning(
                        warning_code="modiv_etl_or_manual_lookup_recommended",
                        message=(
                            "Manual review, dataset download, or future ETL "
                            "indexing may be required for this MOD-IV source."
                        ),
                        severity="medium",
                    )
                ],
            )

        parcel_identifier = self.build_parcel_identifier_from_fields(
            request=request,
            fields=fields,
            search_target=search_target,
        )

        address = self.build_address_from_fields(
            request=request,
            fields=fields,
            confidence=0.50,
        )

        has_parcel = bool(
            parcel_identifier.parcel_id
            or parcel_identifier.pams_pin
            or parcel_identifier.block
            or parcel_identifier.lot
        )

        has_address = bool(
            address.normalized_address
            or address.street_address
            or address.raw_address
        )

        has_municipality = bool(
            fields.get("municipality")
            or request.municipality
            or address.municipality
        )

        has_assessment = any(
            fields.get(key)
            for key in [
                "land_value",
                "improvement_value",
                "total_assessed_value",
            ]
        )

        has_property_class = bool(fields.get("property_class"))

        confidence = build_modiv_confidence(
            has_parcel=has_parcel,
            has_address=has_address,
            has_municipality=has_municipality,
            has_assessment=has_assessment,
            has_property_class=has_property_class,
            parser_manual_review=parse_result.manual_review_required,
            source_successful=response.is_successful(),
        )

        parcel_records: list[ParcelRecord] = []
        tax_assessment_records: list[TaxAssessmentRecord] = []
        property_tax_records: list[PropertyTaxRecord] = []
        building_facts_records: list[BuildingFactsRecord] = []
        owner_reference_records: list[OwnerReferenceRecord] = []
        modiv_records: list[ModIVRecord] = []

        if has_parcel:
            parcel_records.append(
                self.build_parcel_record_from_fields(
                    request=request,
                    fields=fields,
                    parcel_identifier=parcel_identifier,
                    address=address,
                    confidence=confidence,
                    manual_review_required=parse_result.manual_review_required,
                )
            )

        if has_assessment:
            tax_assessment_records.append(
                self.build_tax_assessment_record_from_fields(
                    request=request,
                    fields=fields,
                    parcel_identifier=parcel_identifier,
                    address=address,
                    confidence=confidence,
                    manual_review_required=parse_result.manual_review_required,
                )
            )

            property_tax_record = self.build_property_tax_record_from_fields(
                request=request,
                fields=fields,
                parcel_identifier=parcel_identifier,
                address=address,
                confidence=min(confidence, 0.55),
                manual_review_required=parse_result.manual_review_required,
            )

            if property_tax_record:
                property_tax_records.append(property_tax_record)

        modiv_records.append(
            self.build_modiv_record_from_fields(
                request=request,
                fields=fields,
                parcel_identifier=parcel_identifier,
                address=address,
                confidence=confidence,
                manual_review_required=parse_result.manual_review_required,
            )
        )

        building_record = self.build_building_facts_record_from_fields(
            request=request,
            fields=fields,
            parcel_identifier=parcel_identifier,
            address=address,
            confidence=min(confidence, 0.55),
            manual_review_required=parse_result.manual_review_required,
        )

        if building_record:
            building_facts_records.append(building_record)

        owner_reference = self.build_owner_reference_record_from_fields(
            request=request,
            fields=fields,
            parcel_identifier=parcel_identifier,
            address=address,
            confidence=min(confidence, 0.50),
            manual_review_required=parse_result.manual_review_required,
        )

        if owner_reference:
            owner_reference_records.append(owner_reference)

        warnings = list(parse_result.warnings)

        if parse_result.manual_review_required:
            warnings.append(
                make_modiv_warning(
                    warning_code="modiv_manual_review_required",
                    message=(
                        "MOD-IV connector found candidate data that requires "
                        "manual review before platform-level reliance."
                    ),
                    severity="high",
                )
            )

        warnings.append(
            make_modiv_warning(
                warning_code="assessment_not_market_value",
                message=(
                    "MOD-IV assessment values are public tax assessment context, "
                    "not current market value or current listing price."
                ),
                severity="medium",
            )
        )

        warnings.append(
            make_modiv_warning(
                warning_code="modiv_does_not_prove_listing_status",
                message=(
                    "MOD-IV data can support parcel and assessment context, "
                    "but it does not prove current MLS listing status."
                ),
                severity="medium",
            )
        )

        return self.make_partial_result(
            request=request,
            source_result=source_result,
            parcel_records=parcel_records,
            tax_assessment_records=tax_assessment_records,
            property_tax_records=property_tax_records,
            building_facts_records=building_facts_records,
            owner_reference_records=owner_reference_records,
            modiv_records=modiv_records,
            errors=list(parse_result.errors),
            warnings=warnings,
            explanation=(
                "New Jersey MOD-IV data was parsed conservatively. "
                "No listing-status or market-value claims were made."
            ),
            metadata={
                "search_target": search_target.to_dict(),
                "parse_result": parse_result.to_dict(),
                "source_http_status_code": response.http_status_code,
                "source_detected_format": response.detected_format,
                "source_byte_length": response.byte_length,
                "manual_review_required": parse_result.manual_review_required,
            },
        )

    # ========================================================
    # SECTION 09.06 - RECORD BUILDERS
    # ========================================================

    def build_parcel_identifier_from_fields(
        self,
        *,
        request: PublicRecordSearchRequest,
        fields: dict[str, Any],
        search_target: ModIVSearchTarget,
    ) -> ParcelIdentifier:
        """
        Build parcel identifier from normalized fields and request fallback.
        """

        parcel_id = fields.get("parcel_id")
        pams_pin = fields.get("parcel_id")
        block = fields.get("block") or request.block or search_target.block
        lot = fields.get("lot") or request.lot or search_target.lot
        qualifier = (
            fields.get("qualifier")
            or request.qualifier
            or search_target.qualifier
        )
        municipality_code = fields.get("municipality_code")
        county_code = fields.get("county_code")

        if not parcel_id and block and lot:
            county_part = (
                fields.get("county")
                or request.county
                or "UNKNOWN-COUNTY"
            )
            municipality_part = (
                fields.get("municipality")
                or request.municipality
                or "UNKNOWN-MUNI"
            )
            parcel_id = (
                f"NJ-{county_part}-{municipality_part}-{block}-{lot}"
            )

            if qualifier:
                parcel_id = f"{parcel_id}-{qualifier}"

        return self.build_parcel_identifier(
            parcel_id=parcel_id,
            pams_pin=pams_pin,
            block=block,
            lot=lot,
            qualifier=qualifier,
            municipality_code=municipality_code,
            county_code=county_code,
            state_code=NJ_STATE_MODIV_STATE,
        )

    def build_address_from_fields(
        self,
        *,
        request: PublicRecordSearchRequest,
        fields: dict[str, Any],
        confidence: float = 0.50,
    ) -> PublicRecordAddress:
        """
        Build public-record address from fields and request fallback.
        """

        raw_address = (
            fields.get("address")
            or request.street_address
            or request.raw_query
            or (
                request.address.raw_address
                if request.address
                else None
            )
        )

        municipality = (
            fields.get("municipality")
            or request.municipality
            or (
                request.address.municipality
                if request.address
                else None
            )
        )

        county = (
            fields.get("county")
            or request.county
            or (
                request.address.county
                if request.address
                else None
            )
        )

        postal_code = (
            request.postal_code
            or (
                request.address.postal_code
                if request.address
                else None
            )
        )

        return self.build_public_record_address(
            raw_address=raw_address,
            street_address=raw_address,
            municipality=municipality,
            county=county,
            state=NJ_STATE_MODIV_STATE,
            postal_code=postal_code,
            confidence=confidence,
        )

    def build_parcel_record_from_fields(
        self,
        *,
        request: PublicRecordSearchRequest,
        fields: dict[str, Any],
        parcel_identifier: ParcelIdentifier,
        address: PublicRecordAddress,
        confidence: float,
        manual_review_required: bool,
    ) -> ParcelRecord:
        """
        Build parcel record from explicit MOD-IV fields.
        """

        lot_size_acres = normalize_modiv_area(fields.get("lot_size_acres"))
        lot_size_sqft = normalize_modiv_area(fields.get("lot_size_sqft"))
        generic_lot_size = normalize_modiv_area(fields.get("lot_size"))

        if lot_size_acres is None and lot_size_sqft is None:
            lot_size_acres = generic_lot_size

        latitude = normalize_modiv_coordinate(fields.get("latitude"))
        longitude = normalize_modiv_coordinate(fields.get("longitude"))

        return self.build_parcel_record(
            request=request,
            parcel_identifier=parcel_identifier,
            address=address,
            property_class=fields.get(
                "property_class",
                PropertyClass.UNKNOWN.value,
            ),
            land_description=fields.get("land_description"),
            lot_size_acres=lot_size_acres,
            lot_size_sqft=lot_size_sqft,
            latitude=latitude,
            longitude=longitude,
            geometry_reference=fields.get("geometry_reference"),
            confidence=confidence,
            status=(
                PublicRecordStatus.MANUAL_REVIEW_REQUIRED.value
                if manual_review_required
                else PublicRecordStatus.PARTIAL.value
            ),
            notes=[
                "Parcel context parsed from New Jersey MOD-IV response where explicit.",
                "MOD-IV parcel context should be cross-checked with county sources.",
            ],
            warnings=[
                make_modiv_warning(
                    warning_code="modiv_parcel_not_legal_survey",
                    message=(
                        "MOD-IV parcel context is not a legal boundary survey."
                    ),
                    severity="medium",
                )
            ],
        )

    def build_tax_assessment_record_from_fields(
        self,
        *,
        request: PublicRecordSearchRequest,
        fields: dict[str, Any],
        parcel_identifier: ParcelIdentifier,
        address: PublicRecordAddress,
        confidence: float,
        manual_review_required: bool,
    ) -> TaxAssessmentRecord:
        """
        Build tax assessment record from normalized MOD-IV fields.
        """

        tax_year = normalize_modiv_year(
            fields.get("tax_year") or request.tax_year
        )

        land_value = normalize_modiv_money(fields.get("land_value"))
        improvement_value = normalize_modiv_money(
            fields.get("improvement_value")
        )
        total_assessed_value = normalize_modiv_money(
            fields.get("total_assessed_value")
        )

        if total_assessed_value is None and (
            land_value is not None or improvement_value is not None
        ):
            total_assessed_value = (land_value or 0.0) + (
                improvement_value or 0.0
            )

        record_id = make_public_record_id(
            record_type="modiv_tax_assessment",
            source_id=self.source_id,
            address=address.normalized_address,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
            tax_year=tax_year,
        )

        source_reference = self.build_source_record_reference(
            record_type="modiv_tax_assessment",
            display_label=(
                f"NJ MOD-IV Assessment"
                f"{f' {tax_year}' if tax_year else ''}"
            ),
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
            record_date=str(tax_year) if tax_year else None,
        )

        return TaxAssessmentRecord(
            record_id=record_id,
            tax_year=tax_year,
            parcel_identifier=parcel_identifier,
            address=address,
            owner_reference=fields.get("owner"),
            property_class=fields.get(
                "property_class",
                PropertyClass.UNKNOWN.value,
            ),
            land_value=land_value,
            improvement_value=improvement_value,
            total_assessed_value=total_assessed_value,
            source_context=self.get_source_context(
                source_status=(
                    PublicRecordStatus.MANUAL_REVIEW_REQUIRED.value
                    if manual_review_required
                    else PublicRecordStatus.PARTIAL.value
                ),
            ),
            source_reference=source_reference,
            confidence=confidence,
            status=(
                PublicRecordStatus.MANUAL_REVIEW_REQUIRED.value
                if manual_review_required
                else PublicRecordStatus.PARTIAL.value
            ),
            notes=[
                "Assessment record parsed from New Jersey MOD-IV source where explicit.",
                "Assessment values are public tax context, not market value.",
            ],
            warnings=[
                make_modiv_warning(
                    warning_code="modiv_assessment_not_market_value",
                    message=(
                        "MOD-IV assessment value is not current market value "
                        "or current listing price."
                    ),
                    severity="medium",
                )
            ],
        )

    def build_property_tax_record_from_fields(
        self,
        *,
        request: PublicRecordSearchRequest,
        fields: dict[str, Any],
        parcel_identifier: ParcelIdentifier,
        address: PublicRecordAddress,
        confidence: float,
        manual_review_required: bool,
    ) -> PropertyTaxRecord | None:
        """
        Build property tax record if explicit assessment fields exist.
        """

        tax_year = normalize_modiv_year(
            fields.get("tax_year") or request.tax_year
        )

        assessed_value = normalize_modiv_money(
            fields.get("total_assessed_value")
        )

        if assessed_value is None:
            return None

        record_id = make_public_record_id(
            record_type="modiv_property_tax_context",
            source_id=self.source_id,
            address=address.normalized_address,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
            tax_year=tax_year,
        )

        source_reference = self.build_source_record_reference(
            record_type="modiv_property_tax_context",
            display_label=(
                f"NJ MOD-IV Property Tax Context"
                f"{f' {tax_year}' if tax_year else ''}"
            ),
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
            record_date=str(tax_year) if tax_year else None,
        )

        return PropertyTaxRecord(
            record_id=record_id,
            tax_year=tax_year,
            parcel_identifier=parcel_identifier,
            address=address,
            assessed_value=assessed_value,
            source_context=self.get_source_context(
                source_status=(
                    PublicRecordStatus.MANUAL_REVIEW_REQUIRED.value
                    if manual_review_required
                    else PublicRecordStatus.PARTIAL.value
                ),
            ),
            source_reference=source_reference,
            confidence=confidence,
            status=(
                PublicRecordStatus.MANUAL_REVIEW_REQUIRED.value
                if manual_review_required
                else PublicRecordStatus.PARTIAL.value
            ),
            notes=[
                "Property tax context created from explicit MOD-IV assessment fields.",
                "Annual tax amount is not inferred unless explicitly sourced.",
            ],
            warnings=[
                make_modiv_warning(
                    warning_code="modiv_tax_amount_not_inferred",
                    message=(
                        "Annual property tax amount was not inferred from assessment."
                    ),
                    severity="low",
                )
            ],
        )

    def build_modiv_record_from_fields(
        self,
        *,
        request: PublicRecordSearchRequest,
        fields: dict[str, Any],
        parcel_identifier: ParcelIdentifier,
        address: PublicRecordAddress,
        confidence: float,
        manual_review_required: bool,
    ) -> ModIVRecord:
        """
        Build MOD-IV context record from explicit fields.
        """

        tax_year = normalize_modiv_year(
            fields.get("tax_year") or request.tax_year
        )
        land_value = normalize_modiv_money(fields.get("land_value"))
        improvement_value = normalize_modiv_money(
            fields.get("improvement_value")
        )
        total_assessed_value = normalize_modiv_money(
            fields.get("total_assessed_value")
        )

        if total_assessed_value is None and (
            land_value is not None or improvement_value is not None
        ):
            total_assessed_value = (land_value or 0.0) + (
                improvement_value or 0.0
            )

        record_id = make_public_record_id(
            record_type="modiv",
            source_id=self.source_id,
            address=address.normalized_address,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
            tax_year=tax_year,
        )

        source_reference = self.build_source_record_reference(
            record_type="modiv",
            display_label=(
                f"NJ MOD-IV Parcel Composite"
                f"{f' {tax_year}' if tax_year else ''}"
            ),
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
            record_date=str(tax_year) if tax_year else None,
        )

        return ModIVRecord(
            record_id=record_id,
            tax_year=tax_year,
            parcel_identifier=parcel_identifier,
            address=address,
            municipality=address.municipality,
            county=address.county,
            state=NJ_STATE_MODIV_STATE,
            owner_reference=fields.get("owner"),
            property_class=fields.get(
                "property_class",
                PropertyClass.UNKNOWN.value,
            ),
            land_value=land_value,
            improvement_value=improvement_value,
            total_assessed_value=total_assessed_value,
            source_context=self.get_source_context(
                source_status=(
                    PublicRecordStatus.MANUAL_REVIEW_REQUIRED.value
                    if manual_review_required
                    else PublicRecordStatus.PARTIAL.value
                ),
            ),
            source_reference=source_reference,
            confidence=confidence,
            status=(
                PublicRecordStatus.MANUAL_REVIEW_REQUIRED.value
                if manual_review_required
                else PublicRecordStatus.PARTIAL.value
            ),
            notes=[
                "MOD-IV record derived from explicit New Jersey statewide source fields.",
                "Dataset may require ETL indexing for production-grade lookups.",
            ],
            warnings=[
                make_modiv_warning(
                    warning_code="modiv_requires_county_crosscheck",
                    message=(
                        "State MOD-IV context should be cross-checked with "
                        "county tax board and county clerk records."
                    ),
                    severity="medium",
                )
            ],
        )

    def build_building_facts_record_from_fields(
        self,
        *,
        request: PublicRecordSearchRequest,
        fields: dict[str, Any],
        parcel_identifier: ParcelIdentifier,
        address: PublicRecordAddress,
        confidence: float,
        manual_review_required: bool,
    ) -> BuildingFactsRecord | None:
        """
        Build building facts record if explicit MOD-IV fields exist.
        """

        year_built = normalize_modiv_year(fields.get("year_built"))
        building_area_sqft = normalize_modiv_area(
            fields.get("building_area_sqft")
        )

        if year_built is None and building_area_sqft is None:
            return None

        record_id = make_public_record_id(
            record_type="modiv_building_facts",
            source_id=self.source_id,
            address=address.normalized_address,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
        )

        source_reference = self.build_source_record_reference(
            record_type="modiv_building_facts",
            display_label="NJ MOD-IV Building Facts Reference",
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
        )

        return BuildingFactsRecord(
            record_id=record_id,
            parcel_identifier=parcel_identifier,
            address=address,
            property_class=fields.get(
                "property_class",
                PropertyClass.UNKNOWN.value,
            ),
            year_built=year_built,
            building_area_sqft=building_area_sqft,
            source_context=self.get_source_context(
                source_status=(
                    PublicRecordStatus.MANUAL_REVIEW_REQUIRED.value
                    if manual_review_required
                    else PublicRecordStatus.PARTIAL.value
                ),
            ),
            source_reference=source_reference,
            confidence=confidence,
            status=(
                PublicRecordStatus.MANUAL_REVIEW_REQUIRED.value
                if manual_review_required
                else PublicRecordStatus.PARTIAL.value
            ),
            notes=[
                "Building facts parsed only from explicit MOD-IV source fields.",
            ],
            warnings=[
                make_modiv_warning(
                    warning_code="modiv_building_facts_require_crosscheck",
                    message=(
                        "Building facts should be cross-checked with county "
                        "GIS, tax-board, or municipal records where available."
                    ),
                    severity="medium",
                )
            ],
        )

    def build_owner_reference_record_from_fields(
        self,
        *,
        request: PublicRecordSearchRequest,
        fields: dict[str, Any],
        parcel_identifier: ParcelIdentifier,
        address: PublicRecordAddress,
        confidence: float,
        manual_review_required: bool,
    ) -> OwnerReferenceRecord | None:
        """
        Build owner reference record if explicit owner field exists.
        """

        owner_reference = fields.get("owner") or request.owner_reference

        if not owner_reference:
            return None

        record_id = make_public_record_id(
            record_type="modiv_owner_reference",
            source_id=self.source_id,
            address=address.normalized_address,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
        )

        source_reference = self.build_source_record_reference(
            record_type="modiv_owner_reference",
            display_label="NJ MOD-IV Owner Reference",
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
        )

        return OwnerReferenceRecord(
            record_id=record_id,
            owner_reference=owner_reference,
            parcel_identifier=parcel_identifier,
            address=address,
            source_context=self.get_source_context(
                source_status=(
                    PublicRecordStatus.MANUAL_REVIEW_REQUIRED.value
                    if manual_review_required
                    else PublicRecordStatus.PARTIAL.value
                ),
            ),
            source_reference=source_reference,
            confidence=confidence,
            status=(
                PublicRecordStatus.MANUAL_REVIEW_REQUIRED.value
                if manual_review_required
                else PublicRecordStatus.PARTIAL.value
            ),
            notes=[
                "Owner field is treated as a public-record reference, not a legal conclusion.",
            ],
            warnings=[
                make_modiv_warning(
                    warning_code="modiv_owner_reference_requires_review",
                    message=(
                        "Owner data from statewide public records should be "
                        "cross-checked with county records."
                    ),
                    severity="medium",
                )
            ],
        )

    # ========================================================
    # SECTION 09.07 - DIAGNOSTICS
    # ========================================================

    def diagnostics(
        self,
    ) -> dict[str, Any]:
        """
        Return New Jersey MOD-IV connector diagnostics.
        """

        base = super().diagnostics()

        base.update(
            {
                "new_jersey_modiv": {
                    "source_url": NJ_STATE_MODIV_SOURCE_URL,
                    "jurisdiction": NJ_STATE_MODIV_JURISDICTION,
                    "state": NJ_STATE_MODIV_STATE,
                    "county_scope": NJ_STATE_MODIV_COUNTY_SCOPE,
                    "supported_claims": list(
                        NJ_STATE_MODIV_SUPPORTED_CLAIMS
                    ),
                    "unsupported_claims": list(
                        NJ_STATE_MODIV_UNSUPPORTED_CLAIMS
                    ),
                    "supported_query_modes": list(
                        NJ_STATE_MODIV_SUPPORTED_QUERY_MODES
                    ),
                    "governance": NJ_STATE_MODIV_GOVERNANCE.copy(),
                    "field_alias_count": len(MODIV_FIELD_ALIASES),
                    "generated_at": utc_now(),
                }
            }
        )

        return base


# ============================================================
# SECTION 10 - FACTORY FUNCTIONS
# ============================================================

def create_nj_state_modiv_connector() -> NJStateModIVConnector:
    """
    Create New Jersey MOD-IV connector.
    """

    return NJStateModIVConnector()


def get_nj_state_modiv_connector_metadata() -> dict[str, Any]:
    """
    Return connector metadata.
    """

    connector = create_nj_state_modiv_connector()

    return connector.get_metadata().to_dict()


def get_nj_state_modiv_connector_health() -> dict[str, Any]:
    """
    Return connector health.
    """

    connector = create_nj_state_modiv_connector()

    health = connector.health()

    health.update(
        {
            "official_source": True,
            "source_url": NJ_STATE_MODIV_SOURCE_URL,
            "jurisdiction": NJ_STATE_MODIV_JURISDICTION,
            "statewide_public_record_source": True,
            "mock_records_allowed": False,
            "active_listing_status_allowed": False,
            "generated_at": utc_now(),
        }
    )

    return health


def get_nj_state_modiv_connector_diagnostics() -> dict[str, Any]:
    """
    Return connector diagnostics.
    """

    connector = create_nj_state_modiv_connector()

    return connector.diagnostics()


def validate_nj_state_modiv_connector_governance() -> dict[str, Any]:
    """
    Validate connector governance.
    """

    issues: list[dict[str, Any]] = []

    for key in [
        "mock_records_allowed",
        "fabricated_records_allowed",
        "fabricated_parcel_allowed",
        "fabricated_assessment_allowed",
        "fabricated_modiv_allowed",
        "fabricated_owner_allowed",
        "fabricated_market_value_allowed",
        "fabricated_listing_status_allowed",
        "active_listing_status_allowed",
        "under_contract_status_allowed",
    ]:
        if NJ_STATE_MODIV_GOVERNANCE.get(key):
            issues.append(
                {
                    "issue_code": f"{key}_enabled",
                    "severity": "critical",
                    "message": f"{key} must remain False.",
                }
            )

    for key in [
        "official_source",
        "statewide_public_record_source",
        "source_attribution_required",
        "manual_review_for_ambiguous_matches",
        "public_records_only",
        "listing_feed_required_for_listing_status",
        "assessment_is_not_market_value",
        "modiv_context_is_not_legal_advice",
    ]:
        if not NJ_STATE_MODIV_GOVERNANCE.get(key):
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


def build_nj_state_modiv_manual_lookup_payload(
    request: PublicRecordSearchRequest,
) -> dict[str, Any]:
    """
    Build manual lookup payload for operations review.
    """

    connector = create_nj_state_modiv_connector()

    target = connector.build_search_target(request)

    return {
        "connector_id": connector.connector_id,
        "source_id": connector.source_id,
        "source_name": connector.source_name,
        "source_url": connector.source_url,
        "request": request.to_dict(),
        "search_target": target.to_dict(),
        "manual_steps": [
            "Open the official New Jersey Parcels and MOD-IV Composite source.",
            "Confirm whether direct download, API layer, or GIS dataset access is available.",
            "Search or filter by address, municipality, county, block, lot, or PAMS PIN where supported.",
            "Record only explicit source-backed parcel and assessment values.",
            "Do not treat assessment as current market value.",
            "Do not infer current listing status from MOD-IV data.",
            "Cross-check with county tax-board, county clerk, and GIS records.",
            "Mark ambiguous matches for manual review.",
        ],
        "unsupported_claims": list(NJ_STATE_MODIV_UNSUPPORTED_CLAIMS),
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 11 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "NJ_STATE_MODIV_CONNECTOR_NAME",
    "NJ_STATE_MODIV_CONNECTOR_VERSION",
    "NJ_STATE_MODIV_CONNECTOR_PHASE",
    "NJ_STATE_MODIV_CONNECTOR_STATUS",
    "NJ_STATE_MODIV_SOURCE_ID",
    "NJ_STATE_MODIV_SOURCE_NAME",
    "NJ_STATE_MODIV_SOURCE_URL",
    "NJ_STATE_MODIV_JURISDICTION",
    "NJ_STATE_MODIV_STATE",
    "NJ_STATE_MODIV_COUNTY_SCOPE",
    "NJ_STATE_MODIV_GOVERNANCE",
    "NJ_STATE_MODIV_SUPPORTED_CLAIMS",
    "NJ_STATE_MODIV_UNSUPPORTED_CLAIMS",
    "NJ_STATE_MODIV_SUPPORTED_QUERY_MODES",
    "MODIV_FIELD_ALIASES",
    "ModIVSearchTarget",
    "ModIVParseResult",
    "NJStateModIVConnector",
    "clean_modiv_text",
    "normalize_modiv_money",
    "normalize_modiv_area",
    "normalize_modiv_year",
    "normalize_modiv_coordinate",
    "make_modiv_warning",
    "make_modiv_error",
    "alias_matches",
    "resolve_modiv_field",
    "extract_label_value_pairs_from_text",
    "extract_candidate_modiv_rows",
    "normalize_modiv_fields",
    "build_modiv_confidence",
    "create_nj_state_modiv_connector",
    "get_nj_state_modiv_connector_metadata",
    "get_nj_state_modiv_connector_health",
    "get_nj_state_modiv_connector_diagnostics",
    "validate_nj_state_modiv_connector_governance",
    "build_nj_state_modiv_manual_lookup_payload",
]


# ============================================================
# END OF FILE
# ============================================================