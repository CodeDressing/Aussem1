# ============================================================
# AUSSEM1
# PHASE 2.30 PART 2.00
# ENTERPRISE NJ MORRIS COUNTY GIS CONNECTOR
# FILE: app/public_records/connectors/nj_morris_gis_connector.py
# PURPOSE:
# Provide the official-source connector scaffold for Morris County,
# New Jersey GIS / parcel-map public records.
#
# This connector is designed to support:
# - parcel identity
# - address identity
# - block / lot / qualifier references
# - lot and land-context references where source-supported
# - municipal GIS context
# - geometry / map reference context where source-supported
# - public-record source attribution
# - explicit unavailable/manual-review states
#
# This file does not create mock property records.
# This file does not fabricate parcel geometry.
# This file does not fabricate lot size.
# This file does not fabricate owner conclusions.
# This file does not fabricate tax assessments.
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
# REAL COUNTY GIS PUBLIC RECORD CONNECTOR FOUNDATION ACTIVE
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
from app.public_records.models import GISContextRecord
from app.public_records.models import MunicipalContextRecord
from app.public_records.models import ParcelIdentifier
from app.public_records.models import ParcelRecord
from app.public_records.models import PropertyClass
from app.public_records.models import PublicRecordAddress
from app.public_records.models import PublicRecordConnectorResult
from app.public_records.models import PublicRecordConnectorStatus
from app.public_records.models import PublicRecordSearchRequest
from app.public_records.models import PublicRecordStatus
from app.public_records.models import make_public_record_id
from app.public_records.models import normalize_area
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

NJ_MORRIS_GIS_CONNECTOR_NAME = (
    "Aussem1 Morris County NJ GIS Parcel Connector"
)

NJ_MORRIS_GIS_CONNECTOR_VERSION = "0.1.0"

NJ_MORRIS_GIS_CONNECTOR_PHASE = "PHASE 2.30 PART 2.00"

NJ_MORRIS_GIS_CONNECTOR_STATUS = (
    "real_public_record_county_gis_connector_foundation_active"
)

NJ_MORRIS_GIS_SOURCE_ID = "nj_morris_gis_parcel_searcher"

NJ_MORRIS_GIS_SOURCE_NAME = "Morris County GIS Parcel Searcher"

NJ_MORRIS_GIS_SOURCE_URL = (
    "https://morrisgisapps.co.morris.nj.us/apps/parcelsearcher/"
)

NJ_MORRIS_GIS_JURISDICTION = "Morris County, New Jersey"

NJ_MORRIS_GIS_STATE = "NJ"

NJ_MORRIS_GIS_COUNTY = "Morris"


# ============================================================
# SECTION 03 - CONNECTOR GOVERNANCE
# ============================================================

NJ_MORRIS_GIS_GOVERNANCE = {
    "official_source": True,
    "mock_records_allowed": False,
    "fabricated_records_allowed": False,
    "fabricated_geometry_allowed": False,
    "fabricated_lot_size_allowed": False,
    "fabricated_address_allowed": False,
    "fabricated_owner_allowed": False,
    "fabricated_tax_assessment_allowed": False,
    "active_listing_status_allowed": False,
    "under_contract_status_allowed": False,
    "source_attribution_required": True,
    "manual_review_for_ambiguous_matches": True,
    "manual_review_for_conflicting_records": True,
    "public_records_only": True,
    "listing_feed_required_for_listing_status": True,
    "gis_context_is_not_boundary_survey": True,
    "gis_context_is_not_legal_advice": True,
}


# ============================================================
# SECTION 04 - SUPPORTED AND UNSUPPORTED CLAIMS
# ============================================================

NJ_MORRIS_GIS_SUPPORTED_CLAIMS = [
    "address_identity",
    "parcel_identity",
    "block_lot_reference",
    "municipality",
    "county",
    "state",
    "gis_context",
    "parcel_map_context",
    "geometry_context",
    "tax_map_context",
    "lot_size",
    "land_area",
    "latitude",
    "longitude",
    "property_class",
    "building_facts_where_source_supported",
]


NJ_MORRIS_GIS_UNSUPPORTED_CLAIMS = [
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
]


NJ_MORRIS_GIS_SUPPORTED_QUERY_MODES = [
    "address",
    "block_lot",
    "owner_reference",
]


# ============================================================
# SECTION 05 - GIS FIELD ALIASES
# ============================================================

GIS_FIELD_ALIASES = {
    "address": [
        "address",
        "property address",
        "location",
        "property location",
        "site address",
    ],
    "municipality": [
        "municipality",
        "town",
        "city",
        "borough",
        "township",
        "tax district",
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
    ],
    "property_class": [
        "class",
        "property class",
        "prop class",
        "property_class",
    ],
    "owner": [
        "owner",
        "owner name",
        "taxpayer",
        "assessed owner",
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
    "frontage": [
        "frontage",
        "front ft",
        "front feet",
    ],
    "depth": [
        "depth",
        "depth ft",
        "depth feet",
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
    "tax_map_page": [
        "tax map",
        "tax map page",
        "map page",
        "sheet",
    ],
    "year_built": [
        "year built",
        "yr built",
        "built",
    ],
    "building_area_sqft": [
        "building area",
        "living area",
        "gross area",
        "sq ft building",
        "building square feet",
    ],
}


# ============================================================
# SECTION 06 - GIS SEARCH TARGET MODEL
# ============================================================

@dataclass
class GISSearchTarget:
    """
    Search target representation for the Morris County GIS portal.
    """

    mode: str
    base_url: str
    query_label: str
    query_value: str | None = None
    municipality: str | None = None
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
            "block": self.block,
            "lot": self.lot,
            "qualifier": self.qualifier,
            "owner_reference": self.owner_reference,
            "raw_query": self.raw_query,
            "url": self.url,
            "metadata": self.metadata,
        }


# ============================================================
# SECTION 07 - GIS PARSE RESULT MODEL
# ============================================================

@dataclass
class GISParseResult:
    """
    Conservative parse result for Morris County GIS responses.
    """

    parsed: bool = False
    raw_text_available: bool = False
    candidate_count: int = 0
    normalized_fields: dict[str, Any] = field(default_factory=dict)
    candidate_parcels: list[dict[str, Any]] = field(default_factory=list)
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
            "candidate_parcels": self.candidate_parcels,
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

def clean_gis_text(
    value: Any,
) -> str:
    """
    Clean text from GIS response.
    """

    text = normalize_html_text(value)

    text = text.replace("\xa0", " ")

    return collapse_whitespace(text)


def normalize_gis_area(
    value: Any,
) -> float | None:
    """
    Normalize GIS area field.
    """

    return normalize_area(value)


def normalize_gis_year(
    value: Any,
) -> int | None:
    """
    Normalize GIS year field.
    """

    return normalize_year(value)


def normalize_gis_coordinate(
    value: Any,
) -> float | None:
    """
    Normalize GIS coordinate field.
    """

    if value is None:
        return None

    text = clean_gis_text(value)
    text = text.replace(",", "")

    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def make_gis_warning(
    *,
    warning_code: str,
    message: str,
    severity: str = "medium",
) -> SourceWarning:
    """
    Build standardized GIS warning.
    """

    return SourceWarning(
        warning_code=warning_code,
        message=message,
        severity=severity,
        source_id=NJ_MORRIS_GIS_SOURCE_ID,
    )


def make_gis_error(
    *,
    error_type: str,
    message: str,
    recoverable: bool = True,
    retry_recommended: bool = False,
    manual_review_required: bool = False,
) -> SourceError:
    """
    Build standardized GIS error.
    """

    return SourceError(
        error_type=error_type,
        message=message,
        source_id=NJ_MORRIS_GIS_SOURCE_ID,
        source_name=NJ_MORRIS_GIS_SOURCE_NAME,
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


def resolve_gis_field(
    key: str,
) -> str | None:
    """
    Resolve GIS field alias into canonical field.
    """

    for canonical, aliases in GIS_FIELD_ALIASES.items():
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
        clean_gis_text(line)
        for line in text.splitlines()
        if clean_gis_text(line)
    ]

    for line in lines:
        if ":" in line:
            raw_key, raw_value = line.split(":", 1)
            key = normalize_public_record_key(raw_key)
            value = clean_gis_text(raw_value)

            if key and value:
                pairs[key] = value

    return pairs


def extract_candidate_parcel_rows(
    text: str,
) -> list[dict[str, Any]]:
    """
    Extract conservative candidate GIS parcel rows from text.

    This function only returns candidates when explicit block/lot or
    parcel-like signals are found. It does not generate final records.
    """

    candidates: list[dict[str, Any]] = []

    if not text:
        return candidates

    cleaned = clean_gis_text(text)

    block_lot_pattern = re.compile(
        r"\b(?:block|blk)\s*[:#]?\s*([A-Za-z0-9.\-]+)\s+"
        r"(?:lot|lt)\s*[:#]?\s*([A-Za-z0-9.\-]+)",
        re.IGNORECASE,
    )

    parcel_pattern = re.compile(
        r"\b(?:parcel|pin|pams\s*pin)\s*[:#]?\s*([A-Za-z0-9.\-]+)",
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

    return candidates


def normalize_gis_fields(
    raw_fields: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize raw GIS fields into canonical keys.
    """

    normalized: dict[str, Any] = {}

    for raw_key, raw_value in raw_fields.items():
        canonical = resolve_gis_field(raw_key)

        if not canonical:
            continue

        value = clean_gis_text(raw_value)

        if not value:
            continue

        normalized[canonical] = value

    return normalized


def build_gis_confidence(
    *,
    has_parcel: bool,
    has_address: bool,
    has_municipality: bool,
    has_geometry: bool,
    has_area: bool,
    parser_manual_review: bool,
    source_successful: bool,
) -> float:
    """
    Build conservative confidence score for GIS parse.
    """

    if not source_successful:
        return 0.0

    score = 0.20

    if has_parcel:
        score += 0.25

    if has_address:
        score += 0.15

    if has_municipality:
        score += 0.10

    if has_geometry:
        score += 0.10

    if has_area:
        score += 0.10

    if parser_manual_review:
        score -= 0.20

    return max(0.0, min(0.85, score))


# ============================================================
# SECTION 09 - CONNECTOR CLASS
# ============================================================

class NJMorrisGISConnector(BasePublicRecordConnector):
    """
    Morris County GIS connector.

    This connector provides source-governed access and conservative
    parsing scaffolding for the Morris County GIS parcel-search system.

    It does not fabricate records. If records cannot be confidently
    parsed, it returns an empty or manual-review result.
    """

    connector_id = "nj_morris_gis_connector"
    connector_name = NJ_MORRIS_GIS_CONNECTOR_NAME
    connector_version = NJ_MORRIS_GIS_CONNECTOR_VERSION
    connector_phase = NJ_MORRIS_GIS_CONNECTOR_PHASE

    source_id = NJ_MORRIS_GIS_SOURCE_ID
    source_name = NJ_MORRIS_GIS_SOURCE_NAME
    source_type = SourceType.PUBLIC_RECORD.value
    source_url = NJ_MORRIS_GIS_SOURCE_URL
    documentation_url = NJ_MORRIS_GIS_SOURCE_URL

    jurisdiction = NJ_MORRIS_GIS_JURISDICTION
    state = NJ_MORRIS_GIS_STATE
    county = NJ_MORRIS_GIS_COUNTY
    municipality = None

    access_method = SourceAccessMethod.PUBLIC_WEB_PORTAL.value
    data_format = SourceDataFormat.HTML.value
    status = PublicRecordConnectorStatus.READY.value

    supported_claims = NJ_MORRIS_GIS_SUPPORTED_CLAIMS
    unsupported_claims = NJ_MORRIS_GIS_UNSUPPORTED_CLAIMS
    supported_query_modes = NJ_MORRIS_GIS_SUPPORTED_QUERY_MODES

    def __init__(
        self,
        *,
        request_policy: SourceRequestPolicy | None = None,
    ) -> None:
        super().__init__(
            request_policy=request_policy
            or SourceRequestPolicy(
                timeout_seconds=25,
                max_retries=1,
                respect_rate_limits=True,
                user_agent_required=True,
                uncontrolled_scraping_allowed=False,
                bypass_access_controls_allowed=False,
                store_raw_payload=False,
                manual_review_on_ambiguity=True,
                notes=[
                    "Morris County GIS governed public portal connector.",
                    "No fake parcel records.",
                    "No fake parcel geometry.",
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

        return "nj_morris_gis_connector"

    def get_governance(
        self,
    ) -> dict[str, Any]:
        """
        Return connector governance rules.
        """

        governance = super().get_governance()

        governance.update(NJ_MORRIS_GIS_GOVERNANCE)

        return governance

    # ========================================================
    # SECTION 09.02 - SEARCH TARGET BUILDERS
    # ========================================================

    def build_search_target(
        self,
        request: PublicRecordSearchRequest,
    ) -> GISSearchTarget:
        """
        Build conservative GIS search target.
        """

        query_mode = infer_query_mode(request)

        if query_mode == "block_lot":
            query_value = f"{request.block} / {request.lot}"

            if request.qualifier:
                query_value = f"{query_value} / {request.qualifier}"

            return GISSearchTarget(
                mode=query_mode,
                base_url=self.source_url or NJ_MORRIS_GIS_SOURCE_URL,
                query_label="block_lot",
                query_value=query_value,
                municipality=request.municipality,
                block=request.block,
                lot=request.lot,
                qualifier=request.qualifier,
                raw_query=request.raw_query,
                url=self.source_url,
                metadata={
                    "source_note": (
                        "GIS parcel search may require interactive map behavior. "
                        "Connector preserves source context and search target."
                    ),
                },
            )

        if query_mode == "owner_reference":
            return GISSearchTarget(
                mode=query_mode,
                base_url=self.source_url or NJ_MORRIS_GIS_SOURCE_URL,
                query_label="owner_reference",
                query_value=request.owner_reference,
                municipality=request.municipality,
                owner_reference=request.owner_reference,
                raw_query=request.raw_query,
                url=self.source_url,
                metadata={
                    "encoded_owner_reference": quote_plus(
                        request.owner_reference or ""
                    ),
                    "source_note": (
                        "Owner search may be source-dependent and should be "
                        "treated as a public-record reference only."
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

        return GISSearchTarget(
            mode=query_mode,
            base_url=self.source_url or NJ_MORRIS_GIS_SOURCE_URL,
            query_label="address",
            query_value=address_value,
            municipality=request.municipality,
            raw_query=request.raw_query,
            url=self.source_url,
            metadata={
                "encoded_address": quote_plus(address_value or ""),
                "source_note": (
                    "Address-based GIS lookup may require future source-specific "
                    "automation or manual review."
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
        Execute GIS lookup lifecycle.

        This version safely probes the official source URL and returns
        conservative normalized data only when explicit parseable facts
        exist in the response.

        If the GIS application requires interactive map workflow or
        returns no parseable parcel data, the connector returns an empty
        or manual-review result rather than fabricating a parcel record.
        """

        validation = self.validate_request(request)

        if not validation.valid:
            return self.make_error_result(
                request=request,
                errors=validation.errors,
                warnings=validation.warnings,
                status=PublicRecordConnectorStatus.ERROR.value,
                explanation="Morris County GIS request validation failed.",
            )

        search_target = self.build_search_target(request)

        response = self.get_source_homepage()

        if response is None:
            return self.make_error_result(
                request=request,
                errors=[
                    make_gis_error(
                        error_type=SourceErrorType.SOURCE_UNAVAILABLE.value,
                        message="Morris County GIS source URL is unavailable.",
                        recoverable=True,
                        retry_recommended=True,
                    )
                ],
                status=PublicRecordConnectorStatus.ERROR.value,
                explanation="GIS source URL is unavailable.",
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
                    make_gis_error(
                        error_type=SourceErrorType.SOURCE_UNAVAILABLE.value,
                        message="Morris County GIS source request failed.",
                        recoverable=True,
                        retry_recommended=True,
                    )
                ],
                warnings=list(response.warnings),
                status=PublicRecordConnectorStatus.ERROR.value,
                explanation="GIS source request did not complete successfully.",
            )

        parsed = self.parse_gis_response(
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
                explanation="GIS response parsing returned errors.",
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

    def parse_gis_response(
        self,
        *,
        response: SourceHttpResponse,
        request: PublicRecordSearchRequest,
        search_target: GISSearchTarget,
    ) -> GISParseResult:
        """
        Parse GIS source response conservatively.
        """

        result = GISParseResult()

        text = response.text or ""

        if not text:
            result.warnings.append(
                make_gis_warning(
                    warning_code="empty_gis_response",
                    message="Morris County GIS source response contained no text.",
                    severity="medium",
                )
            )
            result.parser_notes.append(
                "No text available from source response."
            )
            return result

        result.raw_text_available = True

        pairs = extract_label_value_pairs_from_text(text)
        normalized_fields = normalize_gis_fields(pairs)
        candidates = extract_candidate_parcel_rows(text)

        result.normalized_fields = normalized_fields
        result.candidate_parcels = candidates
        result.candidate_count = len(candidates)

        has_direct_fields = bool(normalized_fields)
        has_candidates = bool(candidates)

        if has_direct_fields:
            result.parsed = True
            result.parser_notes.append(
                "Explicit label/value GIS parcel fields were found."
            )

        if has_candidates:
            result.parsed = True
            result.manual_review_required = True
            result.warnings.append(
                make_gis_warning(
                    warning_code="candidate_parcels_require_review",
                    message=(
                        "Potential GIS parcel candidates were found but require "
                        "manual review before being treated as authoritative."
                    ),
                    severity="medium",
                )
            )

        if not has_direct_fields and not has_candidates:
            result.warnings.append(
                make_gis_warning(
                    warning_code="no_parseable_gis_record",
                    message=(
                        "GIS source responded, but no explicit parseable parcel "
                        "record fields were found."
                    ),
                    severity="medium",
                )
            )
            result.parser_notes.append(
                "GIS landing page or interactive map shell likely returned."
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

        parse_result = self.parse_gis_response(
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
        search_target: GISSearchTarget,
        parse_result: GISParseResult,
    ) -> PublicRecordConnectorResult:
        """
        Convert conservative parse result into connector result.
        """

        fields = parse_result.normalized_fields

        if not fields and not parse_result.candidate_parcels:
            return self.empty_result(
                request=request,
                explanation=(
                    "Morris County GIS responded, but no explicit parcel "
                    "data was available to normalize."
                ),
                warnings=parse_result.warnings
                + [
                    make_gis_warning(
                        warning_code="manual_gis_lookup_recommended",
                        message=(
                            "Manual review or future source-specific GIS "
                            "automation may be required for this parcel source."
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

        has_geometry = bool(
            fields.get("geometry_reference")
            or fields.get("latitude")
            or fields.get("longitude")
        )

        has_area = bool(
            fields.get("lot_size")
            or fields.get("lot_size_acres")
            or fields.get("lot_size_sqft")
        )

        confidence = build_gis_confidence(
            has_parcel=has_parcel,
            has_address=has_address,
            has_municipality=has_municipality,
            has_geometry=has_geometry,
            has_area=has_area,
            parser_manual_review=parse_result.manual_review_required,
            source_successful=response.is_successful(),
        )

        parcel_records: list[ParcelRecord] = []
        gis_context_records: list[GISContextRecord] = []
        municipal_context_records: list[MunicipalContextRecord] = []
        building_facts_records: list[BuildingFactsRecord] = []

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

        gis_context_records.append(
            self.build_gis_context_record_from_fields(
                request=request,
                fields=fields,
                parcel_identifier=parcel_identifier,
                address=address,
                confidence=confidence,
                manual_review_required=parse_result.manual_review_required,
            )
        )

        if has_municipality:
            municipal_context_records.append(
                self.build_municipal_context_record_from_fields(
                    request=request,
                    fields=fields,
                    parcel_identifier=parcel_identifier,
                    address=address,
                    confidence=min(confidence, 0.65),
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

        warnings = list(parse_result.warnings)

        if parse_result.manual_review_required:
            warnings.append(
                make_gis_warning(
                    warning_code="gis_manual_review_required",
                    message=(
                        "GIS connector found candidate data that requires "
                        "manual review before platform-level reliance."
                    ),
                    severity="high",
                )
            )

        warnings.append(
            make_gis_warning(
                warning_code="gis_not_legal_survey",
                message=(
                    "GIS parcel context is not a legal boundary survey and "
                    "should not be treated as title or survey advice."
                ),
                severity="medium",
            )
        )

        warnings.append(
            make_gis_warning(
                warning_code="gis_does_not_prove_listing_status",
                message=(
                    "GIS parcel data can support parcel/map context, but it "
                    "does not prove current MLS listing status."
                ),
                severity="medium",
            )
        )

        return self.make_partial_result(
            request=request,
            source_result=source_result,
            parcel_records=parcel_records,
            building_facts_records=building_facts_records,
            municipal_context_records=municipal_context_records,
            gis_context_records=gis_context_records,
            errors=list(parse_result.errors),
            warnings=warnings,
            explanation=(
                "Morris County GIS data was parsed conservatively. "
                "No listing-status claims were made."
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
        search_target: GISSearchTarget,
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
        tax_map_page = fields.get("tax_map_page")

        if not parcel_id and block and lot:
            parcel_id = f"NJ-MORRIS-{block}-{lot}"

            if qualifier:
                parcel_id = f"{parcel_id}-{qualifier}"

        return self.build_parcel_identifier(
            parcel_id=parcel_id,
            pams_pin=pams_pin,
            block=block,
            lot=lot,
            qualifier=qualifier,
            state_code=NJ_MORRIS_GIS_STATE,
            tax_map_page=tax_map_page,
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
            county=NJ_MORRIS_GIS_COUNTY,
            state=NJ_MORRIS_GIS_STATE,
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
        Build parcel record from explicit GIS fields.
        """

        lot_size_acres = normalize_gis_area(fields.get("lot_size_acres"))
        lot_size_sqft = normalize_gis_area(fields.get("lot_size_sqft"))
        generic_lot_size = normalize_gis_area(fields.get("lot_size"))

        if lot_size_acres is None and lot_size_sqft is None:
            lot_size_acres = generic_lot_size

        latitude = normalize_gis_coordinate(fields.get("latitude"))
        longitude = normalize_gis_coordinate(fields.get("longitude"))
        frontage = normalize_gis_area(fields.get("frontage"))
        depth = normalize_gis_area(fields.get("depth"))

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
            frontage=frontage,
            depth=depth,
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
                "Parcel context parsed from Morris County GIS response where explicit.",
                "GIS context should be cross-checked with tax and deed records.",
            ],
            warnings=[
                make_gis_warning(
                    warning_code="gis_parcel_not_legal_survey",
                    message=(
                        "GIS parcel geometry and map context are not a legal survey."
                    ),
                    severity="medium",
                )
            ],
        )

    def build_gis_context_record_from_fields(
        self,
        *,
        request: PublicRecordSearchRequest,
        fields: dict[str, Any],
        parcel_identifier: ParcelIdentifier,
        address: PublicRecordAddress,
        confidence: float,
        manual_review_required: bool,
    ) -> GISContextRecord:
        """
        Build GIS context record from explicit GIS fields.
        """

        latitude = normalize_gis_coordinate(fields.get("latitude"))
        longitude = normalize_gis_coordinate(fields.get("longitude"))

        record_id = make_public_record_id(
            record_type="gis_context",
            source_id=self.source_id,
            address=address.normalized_address,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
        )

        source_reference = self.build_source_record_reference(
            record_type="gis_context",
            display_label="Morris County GIS Parcel Context",
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
        )

        return GISContextRecord(
            record_id=record_id,
            parcel_identifier=parcel_identifier,
            address=address,
            gis_source_name=NJ_MORRIS_GIS_SOURCE_NAME,
            map_reference=fields.get("geometry_reference"),
            tax_map_page=fields.get("tax_map_page"),
            latitude=latitude,
            longitude=longitude,
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
                "GIS context record derived from explicit Morris County GIS source fields.",
            ],
            warnings=[
                make_gis_warning(
                    warning_code="gis_context_requires_crosscheck",
                    message=(
                        "GIS context should be cross-checked with tax-board "
                        "and county-clerk public records."
                    ),
                    severity="medium",
                )
            ],
        )

    def build_municipal_context_record_from_fields(
        self,
        *,
        request: PublicRecordSearchRequest,
        fields: dict[str, Any],
        parcel_identifier: ParcelIdentifier,
        address: PublicRecordAddress,
        confidence: float,
        manual_review_required: bool,
    ) -> MunicipalContextRecord:
        """
        Build municipal context record.
        """

        municipality = (
            fields.get("municipality")
            or address.municipality
            or request.municipality
        )

        record_id = make_public_record_id(
            record_type="municipal_context",
            source_id=self.source_id,
            address=address.normalized_address,
            municipality=municipality,
            county=NJ_MORRIS_GIS_COUNTY,
            state=NJ_MORRIS_GIS_STATE,
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
        )

        source_reference = self.build_source_record_reference(
            record_type="municipal_context",
            display_label="Morris County GIS Municipal Context",
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
            municipality=municipality,
            county=NJ_MORRIS_GIS_COUNTY,
            state=NJ_MORRIS_GIS_STATE,
        )

        return MunicipalContextRecord(
            record_id=record_id,
            municipality=municipality,
            county=NJ_MORRIS_GIS_COUNTY,
            state=NJ_MORRIS_GIS_STATE,
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
                "Municipal context derived from explicit Morris County GIS source fields.",
            ],
            warnings=[
                make_gis_warning(
                    warning_code="municipal_context_not_zoning_opinion",
                    message=(
                        "Municipal context is not a zoning opinion or legal determination."
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
        Build building facts record if explicit GIS fields exist.
        """

        year_built = normalize_gis_year(fields.get("year_built"))
        building_area_sqft = normalize_gis_area(
            fields.get("building_area_sqft")
        )

        if year_built is None and building_area_sqft is None:
            return None

        record_id = make_public_record_id(
            record_type="building_facts",
            source_id=self.source_id,
            address=address.normalized_address,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
        )

        source_reference = self.build_source_record_reference(
            record_type="building_facts",
            display_label="Morris County GIS Building Facts Reference",
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
                "Building facts parsed only from explicit GIS source fields.",
            ],
            warnings=[
                make_gis_warning(
                    warning_code="building_facts_require_crosscheck",
                    message=(
                        "Building facts should be cross-checked with MOD-IV, "
                        "tax-board, or municipal records where available."
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
        Return Morris County GIS connector diagnostics.
        """

        base = super().diagnostics()

        base.update(
            {
                "morris_county_gis": {
                    "source_url": NJ_MORRIS_GIS_SOURCE_URL,
                    "jurisdiction": NJ_MORRIS_GIS_JURISDICTION,
                    "state": NJ_MORRIS_GIS_STATE,
                    "county": NJ_MORRIS_GIS_COUNTY,
                    "supported_claims": list(
                        NJ_MORRIS_GIS_SUPPORTED_CLAIMS
                    ),
                    "unsupported_claims": list(
                        NJ_MORRIS_GIS_UNSUPPORTED_CLAIMS
                    ),
                    "supported_query_modes": list(
                        NJ_MORRIS_GIS_SUPPORTED_QUERY_MODES
                    ),
                    "governance": NJ_MORRIS_GIS_GOVERNANCE.copy(),
                    "field_alias_count": len(GIS_FIELD_ALIASES),
                    "generated_at": utc_now(),
                }
            }
        )

        return base


# ============================================================
# SECTION 10 - FACTORY FUNCTIONS
# ============================================================

def create_nj_morris_gis_connector() -> NJMorrisGISConnector:
    """
    Create Morris County GIS connector.
    """

    return NJMorrisGISConnector()


def get_nj_morris_gis_connector_metadata() -> dict[str, Any]:
    """
    Return connector metadata.
    """

    connector = create_nj_morris_gis_connector()

    return connector.get_metadata().to_dict()


def get_nj_morris_gis_connector_health() -> dict[str, Any]:
    """
    Return connector health.
    """

    connector = create_nj_morris_gis_connector()

    health = connector.health()

    health.update(
        {
            "official_source": True,
            "source_url": NJ_MORRIS_GIS_SOURCE_URL,
            "jurisdiction": NJ_MORRIS_GIS_JURISDICTION,
            "mock_records_allowed": False,
            "active_listing_status_allowed": False,
            "generated_at": utc_now(),
        }
    )

    return health


def get_nj_morris_gis_connector_diagnostics() -> dict[str, Any]:
    """
    Return connector diagnostics.
    """

    connector = create_nj_morris_gis_connector()

    return connector.diagnostics()


def validate_nj_morris_gis_connector_governance() -> dict[str, Any]:
    """
    Validate connector governance.
    """

    issues: list[dict[str, Any]] = []

    for key in [
        "mock_records_allowed",
        "fabricated_records_allowed",
        "fabricated_geometry_allowed",
        "fabricated_lot_size_allowed",
        "fabricated_address_allowed",
        "fabricated_owner_allowed",
        "fabricated_tax_assessment_allowed",
        "active_listing_status_allowed",
        "under_contract_status_allowed",
    ]:
        if NJ_MORRIS_GIS_GOVERNANCE.get(key):
            issues.append(
                {
                    "issue_code": f"{key}_enabled",
                    "severity": "critical",
                    "message": f"{key} must remain False.",
                }
            )

    for key in [
        "official_source",
        "source_attribution_required",
        "manual_review_for_ambiguous_matches",
        "public_records_only",
        "listing_feed_required_for_listing_status",
        "gis_context_is_not_boundary_survey",
        "gis_context_is_not_legal_advice",
    ]:
        if not NJ_MORRIS_GIS_GOVERNANCE.get(key):
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


def build_nj_morris_gis_manual_lookup_payload(
    request: PublicRecordSearchRequest,
) -> dict[str, Any]:
    """
    Build manual lookup payload for operations review.
    """

    connector = create_nj_morris_gis_connector()

    target = connector.build_search_target(request)

    return {
        "connector_id": connector.connector_id,
        "source_id": connector.source_id,
        "source_name": connector.source_name,
        "source_url": connector.source_url,
        "request": request.to_dict(),
        "search_target": target.to_dict(),
        "manual_steps": [
            "Open the official Morris County GIS Parcel Searcher.",
            "Search by property address, block/lot, or owner where supported.",
            "Verify municipality when available.",
            "Record only explicit source-backed parcel and GIS values.",
            "Do not infer legal boundary conclusions from GIS geometry.",
            "Do not infer listing status from GIS parcel data.",
            "Mark ambiguous parcel matches for manual review.",
        ],
        "unsupported_claims": list(NJ_MORRIS_GIS_UNSUPPORTED_CLAIMS),
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 11 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "NJ_MORRIS_GIS_CONNECTOR_NAME",
    "NJ_MORRIS_GIS_CONNECTOR_VERSION",
    "NJ_MORRIS_GIS_CONNECTOR_PHASE",
    "NJ_MORRIS_GIS_CONNECTOR_STATUS",
    "NJ_MORRIS_GIS_SOURCE_ID",
    "NJ_MORRIS_GIS_SOURCE_NAME",
    "NJ_MORRIS_GIS_SOURCE_URL",
    "NJ_MORRIS_GIS_JURISDICTION",
    "NJ_MORRIS_GIS_STATE",
    "NJ_MORRIS_GIS_COUNTY",
    "NJ_MORRIS_GIS_GOVERNANCE",
    "NJ_MORRIS_GIS_SUPPORTED_CLAIMS",
    "NJ_MORRIS_GIS_UNSUPPORTED_CLAIMS",
    "NJ_MORRIS_GIS_SUPPORTED_QUERY_MODES",
    "GIS_FIELD_ALIASES",
    "GISSearchTarget",
    "GISParseResult",
    "NJMorrisGISConnector",
    "clean_gis_text",
    "normalize_gis_area",
    "normalize_gis_year",
    "normalize_gis_coordinate",
    "make_gis_warning",
    "make_gis_error",
    "alias_matches",
    "resolve_gis_field",
    "extract_label_value_pairs_from_text",
    "extract_candidate_parcel_rows",
    "normalize_gis_fields",
    "build_gis_confidence",
    "create_nj_morris_gis_connector",
    "get_nj_morris_gis_connector_metadata",
    "get_nj_morris_gis_connector_health",
    "get_nj_morris_gis_connector_diagnostics",
    "validate_nj_morris_gis_connector_governance",
    "build_nj_morris_gis_manual_lookup_payload",
]


# ============================================================
# END OF FILE
# ============================================================