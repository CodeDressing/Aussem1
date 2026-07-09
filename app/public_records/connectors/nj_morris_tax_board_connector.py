# ============================================================
# AUSSEM1
# PHASE 2.20 PART 5.00
# ENTERPRISE NJ MORRIS COUNTY TAX BOARD CONNECTOR
# FILE: app/public_records/connectors/nj_morris_tax_board_connector.py
# PURPOSE:
# Provide the official-source connector scaffold for Morris County,
# New Jersey tax-board public-record property lookups.
#
# This connector is designed to support:
# - parcel identity
# - address identity
# - tax assessment references
# - property tax context where source-supported
# - owner references where source-supported
# - sale-history references where source-supported
# - public-record source attribution
# - explicit unavailable/manual-review states
#
# This file does not create mock property records.
# This file does not fabricate tax data.
# This file does not fabricate sale history.
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
# REAL PUBLIC RECORD CONNECTOR FOUNDATION ACTIVE
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
from app.public_records.models import SaleHistoryRecord
from app.public_records.models import SaleType
from app.public_records.models import TaxAssessmentRecord
from app.public_records.models import make_public_record_id
from app.public_records.models import normalize_area
from app.public_records.models import normalize_money
from app.public_records.models import normalize_year
from app.sources.source_client import SourceHttpResponse
from app.sources.source_models import SourceAccessMethod
from app.sources.source_models import SourceConfidenceBand
from app.sources.source_models import SourceConfidenceReport
from app.sources.source_models import SourceDataFormat
from app.sources.source_models import SourceError
from app.sources.source_models import SourceErrorType
from app.sources.source_models import SourceRequestPolicy
from app.sources.source_models import SourceStatus
from app.sources.source_models import SourceType
from app.sources.source_models import SourceWarning
from app.sources.source_models import confidence_band


# ============================================================
# SECTION 02 - CONNECTOR METADATA
# ============================================================

NJ_MORRIS_TAX_BOARD_CONNECTOR_NAME = (
    "Aussem1 Morris County NJ Tax Board Connector"
)

NJ_MORRIS_TAX_BOARD_CONNECTOR_VERSION = "0.1.0"

NJ_MORRIS_TAX_BOARD_CONNECTOR_PHASE = "PHASE 2.20 PART 5.00"

NJ_MORRIS_TAX_BOARD_CONNECTOR_STATUS = (
    "real_public_record_tax_board_connector_foundation_active"
)

NJ_MORRIS_TAX_BOARD_SOURCE_ID = "nj_morris_tax_board"

NJ_MORRIS_TAX_BOARD_SOURCE_NAME = "Morris County Tax Board"

NJ_MORRIS_TAX_BOARD_SOURCE_URL = (
    "https://mcweb1.co.morris.nj.us/MCTaxBoard/SearchTaxRecords.aspx"
)

NJ_MORRIS_TAX_BOARD_JURISDICTION = "Morris County, New Jersey"

NJ_MORRIS_TAX_BOARD_STATE = "NJ"

NJ_MORRIS_TAX_BOARD_COUNTY = "Morris"


# ============================================================
# SECTION 03 - CONNECTOR GOVERNANCE
# ============================================================

NJ_MORRIS_TAX_BOARD_GOVERNANCE = {
    "official_source": True,
    "mock_records_allowed": False,
    "fabricated_records_allowed": False,
    "fabricated_values_allowed": False,
    "fabricated_owners_allowed": False,
    "fabricated_sale_history_allowed": False,
    "active_listing_status_allowed": False,
    "under_contract_status_allowed": False,
    "source_attribution_required": True,
    "manual_review_for_ambiguous_matches": True,
    "manual_review_for_conflicting_records": True,
    "public_records_only": True,
    "listing_feed_required_for_listing_status": True,
}


# ============================================================
# SECTION 04 - SUPPORTED AND UNSUPPORTED CLAIMS
# ============================================================

NJ_MORRIS_TAX_BOARD_SUPPORTED_CLAIMS = [
    "address_identity",
    "parcel_identity",
    "tax_assessment",
    "property_tax",
    "land_value",
    "improvement_value",
    "total_assessed_value",
    "property_class",
    "sale_history",
    "owner_reference",
    "municipality",
    "county",
    "state",
]


NJ_MORRIS_TAX_BOARD_UNSUPPORTED_CLAIMS = [
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


NJ_MORRIS_TAX_BOARD_SUPPORTED_QUERY_MODES = [
    "address",
    "block_lot",
    "owner_reference",
]


# ============================================================
# SECTION 05 - FIELD ALIASES
# ============================================================

TAX_BOARD_FIELD_ALIASES = {
    "address": [
        "address",
        "location",
        "property_location",
        "property address",
        "property location",
    ],
    "owner": [
        "owner",
        "owner name",
        "taxpayer",
        "tax payer",
        "assessed owner",
    ],
    "municipality": [
        "municipality",
        "district",
        "town",
        "tax district",
    ],
    "block": [
        "block",
        "blk",
    ],
    "lot": [
        "lot",
        "lt",
    ],
    "qualifier": [
        "qualifier",
        "qual",
        "q",
    ],
    "property_class": [
        "class",
        "property class",
        "prop class",
        "property_class",
    ],
    "land_value": [
        "land",
        "land value",
        "assessed land",
        "land assessment",
    ],
    "improvement_value": [
        "improvement",
        "improvements",
        "improvement value",
        "building value",
        "assessed improvement",
    ],
    "total_assessed_value": [
        "total",
        "total value",
        "total assessed",
        "total assessment",
        "assessment",
    ],
    "tax_year": [
        "year",
        "tax year",
        "assessment year",
    ],
    "sale_date": [
        "sale date",
        "deed date",
        "transfer date",
    ],
    "sale_price": [
        "sale price",
        "consideration",
        "sales price",
    ],
    "year_built": [
        "year built",
        "yr built",
    ],
    "building_area_sqft": [
        "building area",
        "living area",
        "sq ft",
        "square feet",
    ],
    "lot_size": [
        "lot size",
        "acreage",
        "acres",
        "land area",
    ],
}


# ============================================================
# SECTION 06 - TAX BOARD SEARCH URL MODEL
# ============================================================

@dataclass
class TaxBoardSearchTarget:
    """
    Search target representation for the Morris County Tax Board portal.
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
# SECTION 07 - TAX BOARD PARSE RESULT MODEL
# ============================================================

@dataclass
class TaxBoardParseResult:
    """
    Conservative parse result for Tax Board responses.
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

def clean_tax_board_text(
    value: Any,
) -> str:
    """
    Clean text from Tax Board response.
    """

    text = normalize_html_text(value)

    text = text.replace("\xa0", " ")

    return collapse_whitespace(text)


def normalize_tax_board_money(
    value: Any,
) -> float | None:
    """
    Normalize Tax Board money field.
    """

    return normalize_money(value)


def normalize_tax_board_year(
    value: Any,
) -> int | None:
    """
    Normalize Tax Board year field.
    """

    return normalize_year(value)


def normalize_tax_board_area(
    value: Any,
) -> float | None:
    """
    Normalize Tax Board area field.
    """

    return normalize_area(value)


def make_tax_board_warning(
    *,
    warning_code: str,
    message: str,
    severity: str = "medium",
) -> SourceWarning:
    """
    Build standardized Tax Board warning.
    """

    return SourceWarning(
        warning_code=warning_code,
        message=message,
        severity=severity,
        source_id=NJ_MORRIS_TAX_BOARD_SOURCE_ID,
    )


def make_tax_board_error(
    *,
    error_type: str,
    message: str,
    recoverable: bool = True,
    retry_recommended: bool = False,
    manual_review_required: bool = False,
) -> SourceError:
    """
    Build standardized Tax Board error.
    """

    return SourceError(
        error_type=error_type,
        message=message,
        source_id=NJ_MORRIS_TAX_BOARD_SOURCE_ID,
        source_name=NJ_MORRIS_TAX_BOARD_SOURCE_NAME,
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


def resolve_tax_board_field(
    key: str,
) -> str | None:
    """
    Resolve Tax Board field alias into canonical field.
    """

    for canonical, aliases in TAX_BOARD_FIELD_ALIASES.items():
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
        clean_tax_board_text(line)
        for line in text.splitlines()
        if clean_tax_board_text(line)
    ]

    for line in lines:
        if ":" in line:
            raw_key, raw_value = line.split(":", 1)
            key = normalize_public_record_key(raw_key)
            value = clean_tax_board_text(raw_value)

            if key and value:
                pairs[key] = value

    return pairs


def extract_candidate_assessment_rows(
    text: str,
) -> list[dict[str, Any]]:
    """
    Extract conservative candidate rows from text.

    This is intentionally cautious. It only returns row-like candidates
    when there is enough explicit signal to warrant manual review.
    """

    candidates: list[dict[str, Any]] = []

    if not text:
        return candidates

    cleaned = clean_tax_board_text(text)

    block_lot_pattern = re.compile(
        r"\b(?:block|blk)\s*[:#]?\s*([A-Za-z0-9.\-]+)\s+"
        r"(?:lot|lt)\s*[:#]?\s*([A-Za-z0-9.\-]+)",
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

    return candidates


def normalize_tax_board_fields(
    raw_fields: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize raw Tax Board fields into canonical keys.
    """

    normalized: dict[str, Any] = {}

    for raw_key, raw_value in raw_fields.items():
        canonical = resolve_tax_board_field(raw_key)

        if not canonical:
            continue

        value = clean_tax_board_text(raw_value)

        if not value:
            continue

        normalized[canonical] = value

    return normalized


def build_tax_board_confidence(
    *,
    has_parcel: bool,
    has_address: bool,
    has_assessment: bool,
    has_owner: bool,
    has_sale: bool,
    parser_manual_review: bool,
    source_successful: bool,
) -> float:
    """
    Build conservative confidence score for Tax Board parse.
    """

    if not source_successful:
        return 0.0

    score = 0.25

    if has_parcel:
        score += 0.20

    if has_address:
        score += 0.15

    if has_assessment:
        score += 0.20

    if has_owner:
        score += 0.05

    if has_sale:
        score += 0.05

    if parser_manual_review:
        score -= 0.20

    return max(0.0, min(0.85, score))


# ============================================================
# SECTION 09 - CONNECTOR CLASS
# ============================================================

class NJMorrisTaxBoardConnector(BasePublicRecordConnector):
    """
    Morris County Tax Board connector.

    This connector provides source-governed access and conservative
    parsing scaffolding for the Morris County Tax Board public portal.

    It does not fabricate records. If records cannot be confidently
    parsed, it returns an empty or manual-review result.
    """

    connector_id = "nj_morris_tax_board_connector"
    connector_name = NJ_MORRIS_TAX_BOARD_CONNECTOR_NAME
    connector_version = NJ_MORRIS_TAX_BOARD_CONNECTOR_VERSION
    connector_phase = NJ_MORRIS_TAX_BOARD_CONNECTOR_PHASE

    source_id = NJ_MORRIS_TAX_BOARD_SOURCE_ID
    source_name = NJ_MORRIS_TAX_BOARD_SOURCE_NAME
    source_type = SourceType.PUBLIC_RECORD.value
    source_url = NJ_MORRIS_TAX_BOARD_SOURCE_URL
    documentation_url = NJ_MORRIS_TAX_BOARD_SOURCE_URL

    jurisdiction = NJ_MORRIS_TAX_BOARD_JURISDICTION
    state = NJ_MORRIS_TAX_BOARD_STATE
    county = NJ_MORRIS_TAX_BOARD_COUNTY
    municipality = None

    access_method = SourceAccessMethod.PUBLIC_WEB_PORTAL.value
    data_format = SourceDataFormat.HTML.value
    status = PublicRecordConnectorStatus.READY.value

    supported_claims = NJ_MORRIS_TAX_BOARD_SUPPORTED_CLAIMS
    unsupported_claims = NJ_MORRIS_TAX_BOARD_UNSUPPORTED_CLAIMS
    supported_query_modes = NJ_MORRIS_TAX_BOARD_SUPPORTED_QUERY_MODES

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
                    "Morris County Tax Board governed public portal connector.",
                    "No fake property records.",
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

        return "nj_morris_tax_board_connector"

    def get_governance(
        self,
    ) -> dict[str, Any]:
        """
        Return connector governance rules.
        """

        governance = super().get_governance()

        governance.update(NJ_MORRIS_TAX_BOARD_GOVERNANCE)

        return governance

    # ========================================================
    # SECTION 09.02 - SEARCH TARGET BUILDERS
    # ========================================================

    def build_search_target(
        self,
        request: PublicRecordSearchRequest,
    ) -> TaxBoardSearchTarget:
        """
        Build conservative search target.
        """

        query_mode = infer_query_mode(request)

        if query_mode == "block_lot":
            query_label = "block_lot"
            query_value = f"{request.block} / {request.lot}"

            if request.qualifier:
                query_value = f"{query_value} / {request.qualifier}"

            return TaxBoardSearchTarget(
                mode=query_mode,
                base_url=self.source_url or NJ_MORRIS_TAX_BOARD_SOURCE_URL,
                query_label=query_label,
                query_value=query_value,
                municipality=request.municipality,
                block=request.block,
                lot=request.lot,
                qualifier=request.qualifier,
                raw_query=request.raw_query,
                url=self.source_url,
                metadata={
                    "source_note": (
                        "Portal may require interactive form submission. "
                        "Connector preserves request context and source URL."
                    ),
                },
            )

        if query_mode == "owner_reference":
            return TaxBoardSearchTarget(
                mode=query_mode,
                base_url=self.source_url or NJ_MORRIS_TAX_BOARD_SOURCE_URL,
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
                        "Portal may require interactive form submission. "
                        "Owner reference search is source-dependent."
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

        return TaxBoardSearchTarget(
            mode=query_mode,
            base_url=self.source_url or NJ_MORRIS_TAX_BOARD_SOURCE_URL,
            query_label="address",
            query_value=address_value,
            municipality=request.municipality,
            raw_query=request.raw_query,
            url=self.source_url,
            metadata={
                "encoded_address": quote_plus(address_value or ""),
                "source_note": (
                    "Portal may require interactive form submission. "
                    "Address search is preserved for manual or future automated lookup."
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
        Execute Tax Board lookup lifecycle.

        This version safely probes the official source URL and returns
        conservative normalized data only when explicit parseable facts
        exist in the response.

        If the portal requires interactive workflow or returns no
        parseable record data, the connector returns an empty/manual
        review result rather than fabricating a property record.
        """

        validation = self.validate_request(request)

        if not validation.valid:
            return self.make_error_result(
                request=request,
                errors=validation.errors,
                warnings=validation.warnings,
                status=PublicRecordConnectorStatus.ERROR.value,
                explanation="Morris County Tax Board request validation failed.",
            )

        search_target = self.build_search_target(request)

        response = self.get_source_homepage()

        if response is None:
            return self.make_error_result(
                request=request,
                errors=[
                    make_tax_board_error(
                        error_type=SourceErrorType.SOURCE_UNAVAILABLE.value,
                        message="Morris County Tax Board source URL is unavailable.",
                        recoverable=True,
                        retry_recommended=True,
                    )
                ],
                status=PublicRecordConnectorStatus.ERROR.value,
                explanation="Tax Board source URL is unavailable.",
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
                    make_tax_board_error(
                        error_type=SourceErrorType.SOURCE_UNAVAILABLE.value,
                        message="Morris County Tax Board source request failed.",
                        recoverable=True,
                        retry_recommended=True,
                    )
                ],
                warnings=list(response.warnings),
                status=PublicRecordConnectorStatus.ERROR.value,
                explanation="Tax Board source request did not complete successfully.",
            )

        parsed = self.parse_tax_board_response(
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
                explanation="Tax Board response parsing returned errors.",
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

    def parse_tax_board_response(
        self,
        *,
        response: SourceHttpResponse,
        request: PublicRecordSearchRequest,
        search_target: TaxBoardSearchTarget,
    ) -> TaxBoardParseResult:
        """
        Parse Tax Board source response conservatively.
        """

        result = TaxBoardParseResult()

        text = response.text or ""

        if not text:
            result.warnings.append(
                make_tax_board_warning(
                    warning_code="empty_tax_board_response",
                    message="Tax Board source response contained no text.",
                    severity="medium",
                )
            )
            result.parser_notes.append(
                "No text available from source response."
            )
            return result

        result.raw_text_available = True

        pairs = extract_label_value_pairs_from_text(text)
        normalized_fields = normalize_tax_board_fields(pairs)
        candidates = extract_candidate_assessment_rows(text)

        result.normalized_fields = normalized_fields
        result.candidate_records = candidates
        result.candidate_count = len(candidates)

        has_direct_fields = bool(normalized_fields)
        has_candidates = bool(candidates)

        if has_direct_fields:
            result.parsed = True
            result.parser_notes.append(
                "Explicit label/value public-record fields were found."
            )

        if has_candidates:
            result.parsed = True
            result.manual_review_required = True
            result.warnings.append(
                make_tax_board_warning(
                    warning_code="candidate_rows_require_review",
                    message=(
                        "Potential Tax Board row candidates were found but "
                        "require manual review before being treated as authoritative."
                    ),
                    severity="medium",
                )
            )

        if not has_direct_fields and not has_candidates:
            result.warnings.append(
                make_tax_board_warning(
                    warning_code="no_parseable_tax_board_record",
                    message=(
                        "Tax Board source responded, but no explicit parseable "
                        "property record fields were found."
                    ),
                    severity="medium",
                )
            )
            result.parser_notes.append(
                "Portal homepage or interactive form likely returned instead of a property record."
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

        parse_result = self.parse_tax_board_response(
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
        search_target: TaxBoardSearchTarget,
        parse_result: TaxBoardParseResult,
    ) -> PublicRecordConnectorResult:
        """
        Convert conservative parse result into connector result.
        """

        fields = parse_result.normalized_fields

        if not fields and not parse_result.candidate_records:
            return self.empty_result(
                request=request,
                explanation=(
                    "Morris County Tax Board responded, but no explicit "
                    "property record data was available to normalize."
                ),
                warnings=parse_result.warnings
                + [
                    make_tax_board_warning(
                        warning_code="manual_source_lookup_recommended",
                        message=(
                            "Manual review or future form-submission automation "
                            "may be required for this Tax Board source."
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

        parcel_records: list[ParcelRecord] = []
        tax_assessment_records: list[TaxAssessmentRecord] = []
        property_tax_records: list[PropertyTaxRecord] = []
        building_facts_records: list[BuildingFactsRecord] = []
        sale_history_records: list[SaleHistoryRecord] = []
        owner_reference_records: list[OwnerReferenceRecord] = []

        has_parcel = bool(
            parcel_identifier.parcel_id
            or parcel_identifier.block
            or parcel_identifier.lot
            or parcel_identifier.pams_pin
        )

        has_address = bool(
            address.normalized_address
            or address.street_address
            or address.raw_address
        )

        has_assessment = any(
            fields.get(key)
            for key in [
                "land_value",
                "improvement_value",
                "total_assessed_value",
            ]
        )

        has_owner = bool(fields.get("owner"))

        has_sale = bool(fields.get("sale_date") or fields.get("sale_price"))

        confidence = build_tax_board_confidence(
            has_parcel=has_parcel,
            has_address=has_address,
            has_assessment=has_assessment,
            has_owner=has_owner,
            has_sale=has_sale,
            parser_manual_review=parse_result.manual_review_required,
            source_successful=response.is_successful(),
        )

        if has_parcel:
            parcel_records.append(
                self.build_parcel_record(
                    request=request,
                    parcel_identifier=parcel_identifier,
                    address=address,
                    property_class=fields.get(
                        "property_class",
                        PropertyClass.UNKNOWN.value,
                    ),
                    confidence=confidence,
                    status=(
                        PublicRecordStatus.MANUAL_REVIEW_REQUIRED.value
                        if parse_result.manual_review_required
                        else PublicRecordStatus.PARTIAL.value
                    ),
                    notes=[
                        "Parcel identity parsed from Morris County Tax Board response.",
                    ],
                    warnings=list(parse_result.warnings),
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

        if has_sale:
            sale_history_records.append(
                self.build_sale_history_record_from_fields(
                    request=request,
                    fields=fields,
                    parcel_identifier=parcel_identifier,
                    address=address,
                    confidence=min(confidence, 0.65),
                    manual_review_required=parse_result.manual_review_required,
                )
            )

        if has_owner:
            owner_reference_records.append(
                self.build_owner_reference_record_from_fields(
                    request=request,
                    fields=fields,
                    parcel_identifier=parcel_identifier,
                    address=address,
                    confidence=min(confidence, 0.60),
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

        warnings = list(parse_result.warnings)

        if parse_result.manual_review_required:
            warnings.append(
                make_tax_board_warning(
                    warning_code="tax_board_manual_review_required",
                    message=(
                        "Tax Board connector found candidate data that requires "
                        "manual review before platform-level reliance."
                    ),
                    severity="high",
                )
            )

        return self.make_partial_result(
            request=request,
            source_result=source_result,
            parcel_records=parcel_records,
            tax_assessment_records=tax_assessment_records,
            property_tax_records=property_tax_records,
            building_facts_records=building_facts_records,
            sale_history_records=sale_history_records,
            owner_reference_records=owner_reference_records,
            errors=list(parse_result.errors),
            warnings=warnings,
            explanation=(
                "Morris County Tax Board data was parsed conservatively. "
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
        search_target: TaxBoardSearchTarget,
    ) -> ParcelIdentifier:
        """
        Build parcel identifier from normalized fields and request fallback.
        """

        block = fields.get("block") or request.block or search_target.block
        lot = fields.get("lot") or request.lot or search_target.lot
        qualifier = (
            fields.get("qualifier")
            or request.qualifier
            or search_target.qualifier
        )

        parcel_id = None

        if block and lot:
            parcel_id = f"NJ-MORRIS-{block}-{lot}"

            if qualifier:
                parcel_id = f"{parcel_id}-{qualifier}"

        return self.build_parcel_identifier(
            parcel_id=parcel_id,
            block=block,
            lot=lot,
            qualifier=qualifier,
            state_code=NJ_MORRIS_TAX_BOARD_STATE,
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
            county=NJ_MORRIS_TAX_BOARD_COUNTY,
            state=NJ_MORRIS_TAX_BOARD_STATE,
            postal_code=postal_code,
            confidence=confidence,
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
        Build tax assessment record from normalized Tax Board fields.
        """

        tax_year = normalize_tax_board_year(
            fields.get("tax_year") or request.tax_year
        )

        land_value = normalize_tax_board_money(fields.get("land_value"))
        improvement_value = normalize_tax_board_money(
            fields.get("improvement_value")
        )
        total_assessed_value = normalize_tax_board_money(
            fields.get("total_assessed_value")
        )

        if total_assessed_value is None and (
            land_value is not None or improvement_value is not None
        ):
            total_assessed_value = (land_value or 0.0) + (
                improvement_value or 0.0
            )

        record_id = make_public_record_id(
            record_type="tax_assessment",
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
            record_type="tax_assessment",
            display_label=(
                f"Morris County Tax Board Assessment"
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
                "Assessment record parsed from Morris County Tax Board response.",
                "Values are source-dependent and require attribution.",
            ],
            warnings=[
                make_tax_board_warning(
                    warning_code="assessment_public_record_not_market_value",
                    message=(
                        "Tax assessment is not the same as current market value "
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
        Build property tax record if explicit tax fields exist.
        """

        tax_year = normalize_tax_board_year(
            fields.get("tax_year") or request.tax_year
        )

        assessed_value = normalize_tax_board_money(
            fields.get("total_assessed_value")
        )

        if assessed_value is None:
            return None

        record_id = make_public_record_id(
            record_type="property_tax",
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
            record_type="property_tax",
            display_label=(
                f"Morris County Tax Board Property Tax Context"
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
                "Property tax context created from explicit assessment fields.",
                "Annual tax amount requires explicit source support and is not inferred.",
            ],
            warnings=[
                make_tax_board_warning(
                    warning_code="tax_amount_not_inferred",
                    message=(
                        "Annual property tax amount was not inferred from assessment."
                    ),
                    severity="low",
                )
            ],
        )

    def build_sale_history_record_from_fields(
        self,
        *,
        request: PublicRecordSearchRequest,
        fields: dict[str, Any],
        parcel_identifier: ParcelIdentifier,
        address: PublicRecordAddress,
        confidence: float,
        manual_review_required: bool,
    ) -> SaleHistoryRecord:
        """
        Build sale-history record from explicit Tax Board fields.
        """

        sale_date = fields.get("sale_date")
        sale_price = normalize_tax_board_money(fields.get("sale_price"))

        record_id = make_public_record_id(
            record_type="sale_history",
            source_id=self.source_id,
            address=address.normalized_address,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
        )

        source_reference = self.build_source_record_reference(
            record_type="sale_history",
            display_label="Morris County Tax Board Sale History Reference",
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
            record_date=sale_date,
        )

        return SaleHistoryRecord(
            record_id=record_id,
            sale_date=sale_date,
            sale_price=sale_price,
            sale_type=SaleType.UNKNOWN.value,
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
                "Sale-history reference parsed from Tax Board response where explicit.",
            ],
            warnings=[
                make_tax_board_warning(
                    warning_code="sale_type_not_inferred",
                    message=(
                        "Sale type was not inferred. Clerk/deed records are "
                        "needed for stronger transaction classification."
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
    ) -> OwnerReferenceRecord:
        """
        Build owner reference record from explicit Tax Board field.
        """

        owner_reference = fields.get("owner") or request.owner_reference

        record_id = make_public_record_id(
            record_type="owner_reference",
            source_id=self.source_id,
            address=address.normalized_address,
            municipality=address.municipality,
            county=address.county,
            state=address.state,
            block=parcel_identifier.block,
            lot=parcel_identifier.lot,
        )

        source_reference = self.build_source_record_reference(
            record_type="owner_reference",
            display_label="Morris County Tax Board Owner Reference",
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
                make_tax_board_warning(
                    warning_code="owner_reference_requires_review",
                    message=(
                        "Owner data from public records should be treated as "
                        "a source-backed reference and may require review."
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
        Build building facts record if explicit fields exist.
        """

        year_built = normalize_tax_board_year(fields.get("year_built"))
        building_area_sqft = normalize_tax_board_area(
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
            display_label="Morris County Tax Board Building Facts Reference",
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
                "Building facts parsed only from explicit source fields.",
            ],
            warnings=[
                make_tax_board_warning(
                    warning_code="building_facts_are_source_dependent",
                    message=(
                        "Building facts should be cross-checked with GIS, MOD-IV, "
                        "or municipal records where available."
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
        Return Morris County Tax Board connector diagnostics.
        """

        base = super().diagnostics()

        base.update(
            {
                "morris_tax_board": {
                    "source_url": NJ_MORRIS_TAX_BOARD_SOURCE_URL,
                    "jurisdiction": NJ_MORRIS_TAX_BOARD_JURISDICTION,
                    "state": NJ_MORRIS_TAX_BOARD_STATE,
                    "county": NJ_MORRIS_TAX_BOARD_COUNTY,
                    "supported_claims": list(
                        NJ_MORRIS_TAX_BOARD_SUPPORTED_CLAIMS
                    ),
                    "unsupported_claims": list(
                        NJ_MORRIS_TAX_BOARD_UNSUPPORTED_CLAIMS
                    ),
                    "supported_query_modes": list(
                        NJ_MORRIS_TAX_BOARD_SUPPORTED_QUERY_MODES
                    ),
                    "governance": NJ_MORRIS_TAX_BOARD_GOVERNANCE.copy(),
                    "field_alias_count": len(TAX_BOARD_FIELD_ALIASES),
                    "generated_at": utc_now(),
                }
            }
        )

        return base


# ============================================================
# SECTION 10 - FACTORY FUNCTIONS
# ============================================================

def create_nj_morris_tax_board_connector() -> NJMorrisTaxBoardConnector:
    """
    Create Morris County Tax Board connector.
    """

    return NJMorrisTaxBoardConnector()


def get_nj_morris_tax_board_connector_metadata() -> dict[str, Any]:
    """
    Return connector metadata.
    """

    connector = create_nj_morris_tax_board_connector()

    return connector.get_metadata().to_dict()


def get_nj_morris_tax_board_connector_health() -> dict[str, Any]:
    """
    Return connector health.
    """

    connector = create_nj_morris_tax_board_connector()

    health = connector.health()

    health.update(
        {
            "official_source": True,
            "source_url": NJ_MORRIS_TAX_BOARD_SOURCE_URL,
            "jurisdiction": NJ_MORRIS_TAX_BOARD_JURISDICTION,
            "mock_records_allowed": False,
            "active_listing_status_allowed": False,
            "generated_at": utc_now(),
        }
    )

    return health


def get_nj_morris_tax_board_connector_diagnostics() -> dict[str, Any]:
    """
    Return connector diagnostics.
    """

    connector = create_nj_morris_tax_board_connector()

    return connector.diagnostics()


def validate_nj_morris_tax_board_connector_governance() -> dict[str, Any]:
    """
    Validate connector governance.
    """

    issues: list[dict[str, Any]] = []

    for key in [
        "mock_records_allowed",
        "fabricated_records_allowed",
        "fabricated_values_allowed",
        "fabricated_owners_allowed",
        "fabricated_sale_history_allowed",
        "active_listing_status_allowed",
        "under_contract_status_allowed",
    ]:
        if NJ_MORRIS_TAX_BOARD_GOVERNANCE.get(key):
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
    ]:
        if not NJ_MORRIS_TAX_BOARD_GOVERNANCE.get(key):
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


def build_nj_morris_tax_board_manual_lookup_payload(
    request: PublicRecordSearchRequest,
) -> dict[str, Any]:
    """
    Build manual lookup payload for operations review.
    """

    connector = create_nj_morris_tax_board_connector()

    target = connector.build_search_target(request)

    return {
        "connector_id": connector.connector_id,
        "source_id": connector.source_id,
        "source_name": connector.source_name,
        "source_url": connector.source_url,
        "request": request.to_dict(),
        "search_target": target.to_dict(),
        "manual_steps": [
            "Open the official Morris County Tax Board search URL.",
            "Use the request address, owner reference, or block/lot.",
            "Verify municipality when available.",
            "Record only explicit source-backed values.",
            "Do not infer listing status from this source.",
            "Mark ambiguous matches for manual review.",
        ],
        "unsupported_claims": list(NJ_MORRIS_TAX_BOARD_UNSUPPORTED_CLAIMS),
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 11 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "NJ_MORRIS_TAX_BOARD_CONNECTOR_NAME",
    "NJ_MORRIS_TAX_BOARD_CONNECTOR_VERSION",
    "NJ_MORRIS_TAX_BOARD_CONNECTOR_PHASE",
    "NJ_MORRIS_TAX_BOARD_CONNECTOR_STATUS",
    "NJ_MORRIS_TAX_BOARD_SOURCE_ID",
    "NJ_MORRIS_TAX_BOARD_SOURCE_NAME",
    "NJ_MORRIS_TAX_BOARD_SOURCE_URL",
    "NJ_MORRIS_TAX_BOARD_JURISDICTION",
    "NJ_MORRIS_TAX_BOARD_STATE",
    "NJ_MORRIS_TAX_BOARD_COUNTY",
    "NJ_MORRIS_TAX_BOARD_GOVERNANCE",
    "NJ_MORRIS_TAX_BOARD_SUPPORTED_CLAIMS",
    "NJ_MORRIS_TAX_BOARD_UNSUPPORTED_CLAIMS",
    "NJ_MORRIS_TAX_BOARD_SUPPORTED_QUERY_MODES",
    "TAX_BOARD_FIELD_ALIASES",
    "TaxBoardSearchTarget",
    "TaxBoardParseResult",
    "NJMorrisTaxBoardConnector",
    "clean_tax_board_text",
    "normalize_tax_board_money",
    "normalize_tax_board_year",
    "normalize_tax_board_area",
    "make_tax_board_warning",
    "make_tax_board_error",
    "alias_matches",
    "resolve_tax_board_field",
    "extract_label_value_pairs_from_text",
    "extract_candidate_assessment_rows",
    "normalize_tax_board_fields",
    "build_tax_board_confidence",
    "create_nj_morris_tax_board_connector",
    "get_nj_morris_tax_board_connector_metadata",
    "get_nj_morris_tax_board_connector_health",
    "get_nj_morris_tax_board_connector_diagnostics",
    "validate_nj_morris_tax_board_connector_governance",
    "build_nj_morris_tax_board_manual_lookup_payload",
]


# ============================================================
# END OF FILE
# ============================================================