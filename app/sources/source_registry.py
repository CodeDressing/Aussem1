# ============================================================
# AUSSEM1
# PHASE 2.10 PART 3.00
# ENTERPRISE SOURCE REGISTRY
# FILE: app/sources/source_registry.py
# PURPOSE:
# Central registry of official, public, authorized, planned, and
# future real-estate data sources for Aussem1.
#
# This registry is intentionally source-first and real-data-first.
# It does not contain mock homes, fake property values, fake listing
# status, fake comparable sales, or invented public records.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# REAL DATA SOURCE REGISTRY ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from typing import Any

from app.sources.source_models import SourceAccessMethod
from app.sources.source_models import SourceAccessPolicy
from app.sources.source_models import SourceClaimType
from app.sources.source_models import SourceConnectorCapability
from app.sources.source_models import SourceDataFormat
from app.sources.source_models import SourceRegistryEntry
from app.sources.source_models import SourceReliability
from app.sources.source_models import SourceRequestPolicy
from app.sources.source_models import SourceStatus
from app.sources.source_models import SourceType
from app.sources.source_models import SourceValidationReport
from app.sources.source_models import SourceValidationIssue
from app.sources.source_models import validate_registry_entry


# ============================================================
# SECTION 02 - REGISTRY METADATA
# ============================================================

SOURCE_REGISTRY_NAME = "Aussem1 Enterprise Real Data Source Registry"

SOURCE_REGISTRY_VERSION = "0.1.0"

SOURCE_REGISTRY_PHASE = "PHASE 2.10 PART 3.00"

SOURCE_REGISTRY_STATUS = "real_data_source_registry_active"

SOURCE_REGISTRY_DESCRIPTION = (
    "Official registry of source systems used by Aussem1 for "
    "public records, tax data, parcel data, clerk records, listing "
    "data, market data, risk data, school data, comparable data, "
    "and future valuation inputs."
)


# ============================================================
# SECTION 03 - REGISTRY OPERATING RULES
# ============================================================

REGISTRY_OPERATING_RULES = {
    "mock_sources_allowed": False,
    "mock_homes_allowed": False,
    "fabricated_addresses_allowed": False,
    "fabricated_property_values_allowed": False,
    "fabricated_listing_status_allowed": False,
    "fabricated_comparables_allowed": False,
    "fabricated_public_records_allowed": False,
    "official_sources_preferred": True,
    "authorized_sources_preferred": True,
    "source_attribution_required": True,
    "retrieval_timestamp_required": True,
    "source_status_required": True,
    "confidence_required": True,
    "public_records_are_not_listing_status": True,
    "mls_or_listing_feed_required_for_active_status": True,
}


# ============================================================
# SECTION 04 - SAFE REQUEST POLICIES
# ============================================================

PUBLIC_PORTAL_POLICY = SourceRequestPolicy(
    timeout_seconds=25,
    max_retries=1,
    respect_rate_limits=True,
    user_agent_required=True,
    uncontrolled_scraping_allowed=False,
    bypass_access_controls_allowed=False,
    store_raw_payload=False,
    manual_review_on_ambiguity=True,
    notes=[
        "Use only public pages and lawful access paths.",
        "Do not bypass controls.",
        "Do not create high-volume scraping behavior.",
        "Prefer official APIs or downloadable datasets when available.",
    ],
)


GIS_SERVICE_POLICY = SourceRequestPolicy(
    timeout_seconds=30,
    max_retries=1,
    respect_rate_limits=True,
    user_agent_required=True,
    uncontrolled_scraping_allowed=False,
    bypass_access_controls_allowed=False,
    store_raw_payload=False,
    manual_review_on_ambiguity=True,
    notes=[
        "Use official GIS services and public map endpoints only.",
        "Preserve source attribution and service metadata.",
        "Do not infer parcel facts without source confidence.",
    ],
)


DOWNLOADABLE_DATASET_POLICY = SourceRequestPolicy(
    timeout_seconds=60,
    max_retries=1,
    respect_rate_limits=True,
    user_agent_required=True,
    uncontrolled_scraping_allowed=False,
    bypass_access_controls_allowed=False,
    store_raw_payload=False,
    manual_review_on_ambiguity=True,
    notes=[
        "Use official open-data download endpoints where available.",
        "Track dataset publication and retrieval dates.",
        "Normalize fields before property intelligence use.",
    ],
)


LICENSED_FEED_POLICY = SourceRequestPolicy(
    timeout_seconds=30,
    max_retries=1,
    respect_rate_limits=True,
    user_agent_required=True,
    uncontrolled_scraping_allowed=False,
    bypass_access_controls_allowed=False,
    store_raw_payload=False,
    manual_review_on_ambiguity=True,
    notes=[
        "Requires license, credentials, or authorized access.",
        "Do not implement until access agreement is in place.",
        "Listing status claims require this class of source.",
    ],
)


# ============================================================
# SECTION 05 - CAPABILITY HELPERS
# ============================================================

def capability(
    claim_type: SourceClaimType,
    *,
    supported: bool = True,
    requires_auth: bool = False,
    requires_license: bool = False,
    notes: list[str] | None = None,
) -> SourceConnectorCapability:
    """
    Build a connector capability.
    """

    return SourceConnectorCapability(
        claim_type=claim_type.value,
        supported=supported,
        requires_auth=requires_auth,
        requires_license=requires_license,
        notes=notes or [],
    )


# ============================================================
# SECTION 06 - NEW JERSEY / MORRIS COUNTY SOURCE ENTRIES
# ============================================================

NJ_MORRIS_TAX_BOARD = SourceRegistryEntry(
    source_id="nj_morris_tax_board",
    display_name="Morris County Board of Taxation - Search Tax Records",
    source_type=SourceType.TAX_BOARD.value,
    status=SourceStatus.PLANNED.value,
    reliability=SourceReliability.OFFICIAL.value,
    access_method=SourceAccessMethod.PUBLIC_WEB_PORTAL.value,
    access_policy=SourceAccessPolicy.PUBLIC_WITH_TERMS.value,
    data_format=SourceDataFormat.HTML.value,
    jurisdiction="Morris County, New Jersey",
    state="NJ",
    county="Morris",
    municipality=None,
    source_url="https://mcweb1.co.morris.nj.us/MCTaxBoard/SearchTaxRecords.aspx",
    documentation_url="https://mcweb1.co.morris.nj.us/MCTaxBoard/",
    implementation_file=(
        "app/public_records/connectors/"
        "nj_morris_tax_board_connector.py"
    ),
    capabilities=[
        capability(
            SourceClaimType.ADDRESS_IDENTITY,
            notes=["Tax-record search supports property-location lookup."],
        ),
        capability(
            SourceClaimType.TAX_ASSESSMENT,
            notes=["Supports tax-year search workflow and assessment context."],
        ),
        capability(
            SourceClaimType.PROPERTY_TAX,
            notes=["Supports property tax record context where available."],
        ),
        capability(
            SourceClaimType.PARCEL_IDENTITY,
            notes=["Supports block/lot search workflow."],
        ),
        capability(
            SourceClaimType.SALE_HISTORY,
            notes=[
                "May support sale-record context through tax board "
                "records and SR1A-related data where exposed."
            ],
        ),
        capability(
            SourceClaimType.OWNER_REFERENCE,
            notes=[
                "Owner search exists in the public tax-record interface. "
                "Use carefully and preserve source context."
            ],
        ),
        capability(
            SourceClaimType.ACTIVE_LISTING_STATUS,
            supported=False,
            notes=[
                "Tax records do not establish current active MLS/listing status."
            ],
        ),
        capability(
            SourceClaimType.UNDER_CONTRACT_STATUS,
            supported=False,
            notes=[
                "Tax records do not establish current under-contract status."
            ],
        ),
        capability(
            SourceClaimType.LISTING_PRICE,
            supported=False,
            notes=[
                "Tax records do not establish current listing price."
            ],
        ),
    ],
    request_policy=PUBLIC_PORTAL_POLICY,
    expected_claims=[
        SourceClaimType.ADDRESS_IDENTITY.value,
        SourceClaimType.TAX_ASSESSMENT.value,
        SourceClaimType.PROPERTY_TAX.value,
        SourceClaimType.PARCEL_IDENTITY.value,
        SourceClaimType.SALE_HISTORY.value,
        SourceClaimType.OWNER_REFERENCE.value,
    ],
    unsupported_claims=[
        SourceClaimType.ACTIVE_LISTING_STATUS.value,
        SourceClaimType.UNDER_CONTRACT_STATUS.value,
        SourceClaimType.LISTING_PRICE.value,
        SourceClaimType.DAYS_ON_MARKET.value,
    ],
    official_source_required=True,
    mock_data_allowed=False,
    notes=[
        "Initial Morris County tax source.",
        "Search modes include property location, owner, block/lot, and tax year.",
        "Public records should not be treated as current listing feed data.",
    ],
    metadata={
        "source_family": "morris_county_public_records",
        "priority": 1,
        "first_connector_target": True,
        "source_verification": "web_verified",
    },
)


NJ_MORRIS_COUNTY_CLERK = SourceRegistryEntry(
    source_id="nj_morris_county_clerk_property_records",
    display_name="Morris County Clerk - Online Property Records Search",
    source_type=SourceType.COUNTY_CLERK.value,
    status=SourceStatus.PLANNED.value,
    reliability=SourceReliability.OFFICIAL.value,
    access_method=SourceAccessMethod.PUBLIC_WEB_PORTAL.value,
    access_policy=SourceAccessPolicy.PUBLIC_WITH_TERMS.value,
    data_format=SourceDataFormat.MIXED.value,
    jurisdiction="Morris County, New Jersey",
    state="NJ",
    county="Morris",
    municipality=None,
    source_url="https://www.morriscountyclerk.org/Services/Online-Property-Records-Search",
    documentation_url="https://www.morriscountyclerk.org/Home",
    implementation_file=(
        "app/public_records/connectors/"
        "nj_morris_clerk_connector.py"
    ),
    capabilities=[
        capability(
            SourceClaimType.DEED_REFERENCE,
            notes=["County Clerk manages recorded deed references."],
        ),
        capability(
            SourceClaimType.MORTGAGE_REFERENCE,
            notes=["County Clerk manages recorded mortgage references."],
        ),
        capability(
            SourceClaimType.LIEN_REFERENCE,
            notes=["County Clerk may expose lien document references."],
        ),
        capability(
            SourceClaimType.SALE_HISTORY,
            notes=[
                "Recorded deed/transfer documents can support sale-history context."
            ],
        ),
        capability(
            SourceClaimType.OWNER_REFERENCE,
            notes=[
                "Recorded documents may contain party references. "
                "Use only as public-record context."
            ],
        ),
        capability(
            SourceClaimType.ACTIVE_LISTING_STATUS,
            supported=False,
            notes=[
                "County Clerk records do not establish current active listing status."
            ],
        ),
        capability(
            SourceClaimType.UNDER_CONTRACT_STATUS,
            supported=False,
            notes=[
                "County Clerk records do not establish current under-contract status."
            ],
        ),
        capability(
            SourceClaimType.LISTING_PRICE,
            supported=False,
            notes=[
                "County Clerk records do not establish current listing price."
            ],
        ),
    ],
    request_policy=PUBLIC_PORTAL_POLICY,
    expected_claims=[
        SourceClaimType.DEED_REFERENCE.value,
        SourceClaimType.MORTGAGE_REFERENCE.value,
        SourceClaimType.LIEN_REFERENCE.value,
        SourceClaimType.SALE_HISTORY.value,
        SourceClaimType.OWNER_REFERENCE.value,
    ],
    unsupported_claims=[
        SourceClaimType.ACTIVE_LISTING_STATUS.value,
        SourceClaimType.UNDER_CONTRACT_STATUS.value,
        SourceClaimType.LISTING_PRICE.value,
        SourceClaimType.DAYS_ON_MARKET.value,
    ],
    official_source_required=True,
    mock_data_allowed=False,
    notes=[
        "Initial Morris County deed and recorded-document source.",
        "Online property records search provides access to many recorded records.",
        "Recorded legal documents are not equivalent to current listing status.",
    ],
    metadata={
        "source_family": "morris_county_public_records",
        "priority": 2,
        "source_verification": "web_verified",
    },
)


NJ_MORRIS_GIS_PARCEL_SEARCHER = SourceRegistryEntry(
    source_id="nj_morris_gis_parcel_searcher",
    display_name="Morris County Tax Board Parcel Searcher / MCPRIMA",
    source_type=SourceType.PARCEL_GIS.value,
    status=SourceStatus.PLANNED.value,
    reliability=SourceReliability.OFFICIAL.value,
    access_method=SourceAccessMethod.GIS_SERVICE.value,
    access_policy=SourceAccessPolicy.PUBLIC_WITH_TERMS.value,
    data_format=SourceDataFormat.GIS_LAYER.value,
    jurisdiction="Morris County, New Jersey",
    state="NJ",
    county="Morris",
    municipality=None,
    source_url="https://morrisgisapps.co.morris.nj.us/apps/parcelsearcher/",
    documentation_url="https://morrisgisapps.co.morris.nj.us/",
    implementation_file=(
        "app/public_records/connectors/"
        "nj_morris_gis_connector.py"
    ),
    capabilities=[
        capability(
            SourceClaimType.PARCEL_IDENTITY,
            notes=["Supports parcel boundary and parcel identity context."],
        ),
        capability(
            SourceClaimType.ADDRESS_IDENTITY,
            notes=["Can support address-to-parcel context where exposed."],
        ),
        capability(
            SourceClaimType.MUNICIPALITY,
            notes=["Can support municipal context from parcel data."],
        ),
        capability(
            SourceClaimType.COUNTY,
            notes=["Can support county context."],
        ),
        capability(
            SourceClaimType.LOT_SIZE,
            notes=["May support land/parcel attributes where exposed."],
        ),
        capability(
            SourceClaimType.BUILDING_FACTS,
            notes=[
                "May expose MOD-IV property attributes depending on available fields."
            ],
        ),
        capability(
            SourceClaimType.ACTIVE_LISTING_STATUS,
            supported=False,
            notes=["Parcel GIS does not establish current active listing status."],
        ),
        capability(
            SourceClaimType.UNDER_CONTRACT_STATUS,
            supported=False,
            notes=["Parcel GIS does not establish current under-contract status."],
        ),
    ],
    request_policy=GIS_SERVICE_POLICY,
    expected_claims=[
        SourceClaimType.PARCEL_IDENTITY.value,
        SourceClaimType.ADDRESS_IDENTITY.value,
        SourceClaimType.MUNICIPALITY.value,
        SourceClaimType.COUNTY.value,
        SourceClaimType.LOT_SIZE.value,
        SourceClaimType.BUILDING_FACTS.value,
    ],
    unsupported_claims=[
        SourceClaimType.ACTIVE_LISTING_STATUS.value,
        SourceClaimType.UNDER_CONTRACT_STATUS.value,
        SourceClaimType.LISTING_PRICE.value,
        SourceClaimType.DAYS_ON_MARKET.value,
    ],
    official_source_required=True,
    mock_data_allowed=False,
    notes=[
        "Initial GIS parcel source for Morris County.",
        "Useful for block/lot, parcel, municipal, and map context.",
        "Must not be treated as listing-status source.",
    ],
    metadata={
        "source_family": "morris_county_gis",
        "priority": 3,
        "source_verification": "web_verified",
    },
)


NJ_STATE_PARCELS_MODIV = SourceRegistryEntry(
    source_id="nj_state_parcels_modiv_composite",
    display_name="NJGIN Parcels and MOD-IV Composite of New Jersey",
    source_type=SourceType.STATE_ASSESSMENT_DATA.value,
    status=SourceStatus.PLANNED.value,
    reliability=SourceReliability.OFFICIAL.value,
    access_method=SourceAccessMethod.DOWNLOADABLE_DATASET.value,
    access_policy=SourceAccessPolicy.PUBLIC_WITH_TERMS.value,
    data_format=SourceDataFormat.GIS_LAYER.value,
    jurisdiction="State of New Jersey",
    state="NJ",
    county=None,
    municipality=None,
    source_url=(
        "https://njogis-newjersey.opendata.arcgis.com/documents/"
        "newjersey%3A%3Aparcels-and-mod-iv-composite-of-nj-download/about"
    ),
    documentation_url=(
        "https://njogis-newjersey.opendata.arcgis.com/"
    ),
    implementation_file=(
        "app/public_records/connectors/"
        "nj_state_modiv_connector.py"
    ),
    capabilities=[
        capability(
            SourceClaimType.PARCEL_IDENTITY,
            notes=["Statewide parcel identity and parcel/MOD-IV baseline."],
        ),
        capability(
            SourceClaimType.TAX_ASSESSMENT,
            notes=["MOD-IV assessment attributes where matched."],
        ),
        capability(
            SourceClaimType.PROPERTY_TAX,
            notes=["Property tax context from MOD-IV-derived records."],
        ),
        capability(
            SourceClaimType.ADDRESS_IDENTITY,
            notes=["Property location context where available."],
        ),
        capability(
            SourceClaimType.PROPERTY_CLASS,
            notes=["Property class context where provided by MOD-IV attributes."],
        ),
        capability(
            SourceClaimType.MUNICIPALITY,
            notes=["Municipal coding and property location context."],
        ),
        capability(
            SourceClaimType.ACTIVE_LISTING_STATUS,
            supported=False,
            notes=[
                "State parcel/MOD-IV records do not establish active listing status."
            ],
        ),
        capability(
            SourceClaimType.UNDER_CONTRACT_STATUS,
            supported=False,
            notes=[
                "State parcel/MOD-IV records do not establish under-contract status."
            ],
        ),
    ],
    request_policy=DOWNLOADABLE_DATASET_POLICY,
    expected_claims=[
        SourceClaimType.PARCEL_IDENTITY.value,
        SourceClaimType.TAX_ASSESSMENT.value,
        SourceClaimType.PROPERTY_TAX.value,
        SourceClaimType.ADDRESS_IDENTITY.value,
        SourceClaimType.PROPERTY_CLASS.value,
        SourceClaimType.MUNICIPALITY.value,
    ],
    unsupported_claims=[
        SourceClaimType.ACTIVE_LISTING_STATUS.value,
        SourceClaimType.UNDER_CONTRACT_STATUS.value,
        SourceClaimType.LISTING_PRICE.value,
        SourceClaimType.DAYS_ON_MARKET.value,
    ],
    official_source_required=True,
    mock_data_allowed=False,
    notes=[
        "Statewide New Jersey parcel and MOD-IV source foundation.",
        "Useful for expanding beyond Morris County.",
        "Should be normalized before property-intelligence use.",
    ],
    metadata={
        "source_family": "new_jersey_state_open_data",
        "priority": 4,
        "source_verification": "web_verified",
    },
)


# ============================================================
# SECTION 07 - FUTURE LISTING SOURCE ENTRIES
# ============================================================

MLS_RESO_FUTURE = SourceRegistryEntry(
    source_id="mls_reso_future",
    display_name="MLS / RESO Authorized Listing Feed",
    source_type=SourceType.MLS_RESO.value,
    status=SourceStatus.AUTH_REQUIRED.value,
    reliability=SourceReliability.LICENSED.value,
    access_method=SourceAccessMethod.LICENSED_FEED.value,
    access_policy=SourceAccessPolicy.LICENSED.value,
    data_format=SourceDataFormat.JSON.value,
    jurisdiction="United States",
    state=None,
    county=None,
    municipality=None,
    source_url=None,
    documentation_url="https://www.reso.org/",
    implementation_file=None,
    capabilities=[
        capability(
            SourceClaimType.ACTIVE_LISTING_STATUS,
            requires_auth=True,
            requires_license=True,
            notes=["Required for reliable active listing status at scale."],
        ),
        capability(
            SourceClaimType.UNDER_CONTRACT_STATUS,
            requires_auth=True,
            requires_license=True,
            notes=["Required for reliable under-contract status at scale."],
        ),
        capability(
            SourceClaimType.SOLD_STATUS,
            requires_auth=True,
            requires_license=True,
            notes=["Can support closed-listing status where feed permits."],
        ),
        capability(
            SourceClaimType.LISTING_PRICE,
            requires_auth=True,
            requires_license=True,
            notes=["Can support current listing price where feed permits."],
        ),
        capability(
            SourceClaimType.DAYS_ON_MARKET,
            requires_auth=True,
            requires_license=True,
            notes=["Can support days-on-market where feed permits."],
        ),
        capability(
            SourceClaimType.COMPARABLE_SALE,
            requires_auth=True,
            requires_license=True,
            notes=["Can support comparable sales where permitted by feed."],
        ),
    ],
    request_policy=LICENSED_FEED_POLICY,
    expected_claims=[
        SourceClaimType.ACTIVE_LISTING_STATUS.value,
        SourceClaimType.UNDER_CONTRACT_STATUS.value,
        SourceClaimType.SOLD_STATUS.value,
        SourceClaimType.LISTING_PRICE.value,
        SourceClaimType.DAYS_ON_MARKET.value,
        SourceClaimType.COMPARABLE_SALE.value,
    ],
    unsupported_claims=[],
    official_source_required=True,
    mock_data_allowed=False,
    notes=[
        "Future authorized listing feed.",
        "Do not implement without credentials, permissions, and compliance review.",
        "This source class is required for reliable current listing status.",
    ],
    metadata={
        "source_family": "listing_data",
        "priority": 10,
        "requires_business_access": True,
    },
)


BROKER_FEED_FUTURE = SourceRegistryEntry(
    source_id="broker_feed_future",
    display_name="Authorized Broker Listing Feed",
    source_type=SourceType.BROKER_FEED.value,
    status=SourceStatus.AUTH_REQUIRED.value,
    reliability=SourceReliability.AUTHORIZED.value,
    access_method=SourceAccessMethod.LICENSED_FEED.value,
    access_policy=SourceAccessPolicy.PERMISSION_REQUIRED.value,
    data_format=SourceDataFormat.JSON.value,
    jurisdiction="United States",
    state=None,
    county=None,
    municipality=None,
    source_url=None,
    documentation_url=None,
    implementation_file=None,
    capabilities=[
        capability(
            SourceClaimType.ACTIVE_LISTING_STATUS,
            requires_auth=True,
            notes=["Broker-authorized feed may support listing status."],
        ),
        capability(
            SourceClaimType.LISTING_PRICE,
            requires_auth=True,
            notes=["Broker-authorized feed may support listing price."],
        ),
        capability(
            SourceClaimType.DAYS_ON_MARKET,
            requires_auth=True,
            notes=["Broker-authorized feed may support DOM if provided."],
        ),
    ],
    request_policy=LICENSED_FEED_POLICY,
    expected_claims=[
        SourceClaimType.ACTIVE_LISTING_STATUS.value,
        SourceClaimType.LISTING_PRICE.value,
        SourceClaimType.DAYS_ON_MARKET.value,
    ],
    unsupported_claims=[],
    official_source_required=True,
    mock_data_allowed=False,
    notes=[
        "Future broker-authorized feed.",
        "Potential source for Aussem broker, seller, and listing workflows.",
    ],
    metadata={
        "source_family": "listing_data",
        "priority": 11,
        "requires_business_access": True,
    },
)


# ============================================================
# SECTION 08 - RISK / SCHOOL / MARKET FUTURE SOURCES
# ============================================================

FEMA_FLOOD_FUTURE = SourceRegistryEntry(
    source_id="fema_flood_future",
    display_name="FEMA Flood Risk / Flood Map Data",
    source_type=SourceType.RISK_DATA.value,
    status=SourceStatus.PLANNED.value,
    reliability=SourceReliability.OFFICIAL.value,
    access_method=SourceAccessMethod.OFFICIAL_API.value,
    access_policy=SourceAccessPolicy.PUBLIC_WITH_TERMS.value,
    data_format=SourceDataFormat.GIS_LAYER.value,
    jurisdiction="United States",
    source_url=None,
    documentation_url="https://www.fema.gov/flood-maps",
    implementation_file=None,
    capabilities=[
        capability(
            SourceClaimType.FLOOD_CONTEXT,
            notes=["Future flood-context source for property risk panels."],
        ),
    ],
    request_policy=GIS_SERVICE_POLICY,
    expected_claims=[
        SourceClaimType.FLOOD_CONTEXT.value,
    ],
    unsupported_claims=[],
    official_source_required=True,
    mock_data_allowed=False,
    notes=[
        "Future flood risk connector.",
        "Not implemented in Phase 2.10.",
    ],
    metadata={
        "source_family": "risk_data",
        "priority": 30,
    },
)


SCHOOL_DATA_FUTURE = SourceRegistryEntry(
    source_id="school_data_future",
    display_name="School Data Source",
    source_type=SourceType.SCHOOL_DATA.value,
    status=SourceStatus.PLANNED.value,
    reliability=SourceReliability.AUTHORIZED.value,
    access_method=SourceAccessMethod.FUTURE_CONNECTOR.value,
    access_policy=SourceAccessPolicy.UNKNOWN.value,
    data_format=SourceDataFormat.JSON.value,
    jurisdiction="United States",
    source_url=None,
    documentation_url=None,
    implementation_file=None,
    capabilities=[
        capability(
            SourceClaimType.SCHOOL_DISTRICT,
            notes=["Future source for school district and school context."],
        ),
    ],
    request_policy=PUBLIC_PORTAL_POLICY,
    expected_claims=[
        SourceClaimType.SCHOOL_DISTRICT.value,
    ],
    unsupported_claims=[],
    official_source_required=False,
    mock_data_allowed=False,
    notes=[
        "Future school-data connector.",
        "Must be reviewed for permitted data use before implementation.",
    ],
    metadata={
        "source_family": "school_data",
        "priority": 31,
    },
)


# ============================================================
# SECTION 09 - MASTER SOURCE REGISTRY
# ============================================================

SOURCE_REGISTRY: dict[str, SourceRegistryEntry] = {
    NJ_MORRIS_TAX_BOARD.source_id: NJ_MORRIS_TAX_BOARD,
    NJ_MORRIS_COUNTY_CLERK.source_id: NJ_MORRIS_COUNTY_CLERK,
    NJ_MORRIS_GIS_PARCEL_SEARCHER.source_id: NJ_MORRIS_GIS_PARCEL_SEARCHER,
    NJ_STATE_PARCELS_MODIV.source_id: NJ_STATE_PARCELS_MODIV,
    MLS_RESO_FUTURE.source_id: MLS_RESO_FUTURE,
    BROKER_FEED_FUTURE.source_id: BROKER_FEED_FUTURE,
    FEMA_FLOOD_FUTURE.source_id: FEMA_FLOOD_FUTURE,
    SCHOOL_DATA_FUTURE.source_id: SCHOOL_DATA_FUTURE,
}


# ============================================================
# SECTION 10 - SOURCE GROUPS
# ============================================================

SOURCE_GROUPS = {
    "morris_county_public_records": [
        "nj_morris_tax_board",
        "nj_morris_county_clerk_property_records",
        "nj_morris_gis_parcel_searcher",
    ],
    "new_jersey_statewide_public_records": [
        "nj_state_parcels_modiv_composite",
    ],
    "future_listing_status_sources": [
        "mls_reso_future",
        "broker_feed_future",
    ],
    "future_risk_sources": [
        "fema_flood_future",
    ],
    "future_school_sources": [
        "school_data_future",
    ],
}


# ============================================================
# SECTION 11 - CLAIM SOURCE GOVERNANCE
# ============================================================

CLAIM_SOURCE_GOVERNANCE = {
    SourceClaimType.TAX_ASSESSMENT.value: [
        "nj_morris_tax_board",
        "nj_state_parcels_modiv_composite",
    ],
    SourceClaimType.PROPERTY_TAX.value: [
        "nj_morris_tax_board",
        "nj_state_parcels_modiv_composite",
    ],
    SourceClaimType.PARCEL_IDENTITY.value: [
        "nj_morris_gis_parcel_searcher",
        "nj_state_parcels_modiv_composite",
        "nj_morris_tax_board",
    ],
    SourceClaimType.ADDRESS_IDENTITY.value: [
        "nj_morris_tax_board",
        "nj_morris_gis_parcel_searcher",
        "nj_state_parcels_modiv_composite",
    ],
    SourceClaimType.DEED_REFERENCE.value: [
        "nj_morris_county_clerk_property_records",
    ],
    SourceClaimType.MORTGAGE_REFERENCE.value: [
        "nj_morris_county_clerk_property_records",
    ],
    SourceClaimType.LIEN_REFERENCE.value: [
        "nj_morris_county_clerk_property_records",
    ],
    SourceClaimType.SALE_HISTORY.value: [
        "nj_morris_county_clerk_property_records",
        "nj_morris_tax_board",
        "mls_reso_future",
    ],
    SourceClaimType.OWNER_REFERENCE.value: [
        "nj_morris_tax_board",
        "nj_morris_county_clerk_property_records",
    ],
    SourceClaimType.ACTIVE_LISTING_STATUS.value: [
        "mls_reso_future",
        "broker_feed_future",
    ],
    SourceClaimType.UNDER_CONTRACT_STATUS.value: [
        "mls_reso_future",
        "broker_feed_future",
    ],
    SourceClaimType.LISTING_PRICE.value: [
        "mls_reso_future",
        "broker_feed_future",
    ],
    SourceClaimType.DAYS_ON_MARKET.value: [
        "mls_reso_future",
        "broker_feed_future",
    ],
    SourceClaimType.FLOOD_CONTEXT.value: [
        "fema_flood_future",
    ],
    SourceClaimType.SCHOOL_DISTRICT.value: [
        "school_data_future",
    ],
}


CLAIMS_PUBLIC_RECORDS_CANNOT_PROVE = [
    SourceClaimType.ACTIVE_LISTING_STATUS.value,
    SourceClaimType.UNDER_CONTRACT_STATUS.value,
    SourceClaimType.LISTING_PRICE.value,
    SourceClaimType.DAYS_ON_MARKET.value,
]


# ============================================================
# SECTION 12 - REGISTRY ACCESS FUNCTIONS
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(UTC).isoformat()


def get_source_registry_metadata() -> dict[str, Any]:
    """
    Return source registry metadata.
    """

    return {
        "name": SOURCE_REGISTRY_NAME,
        "version": SOURCE_REGISTRY_VERSION,
        "phase": SOURCE_REGISTRY_PHASE,
        "status": SOURCE_REGISTRY_STATUS,
        "description": SOURCE_REGISTRY_DESCRIPTION,
        "source_count": len(SOURCE_REGISTRY),
        "group_count": len(SOURCE_GROUPS),
        "generated_at": utc_now(),
    }


def get_all_sources() -> dict[str, dict[str, Any]]:
    """
    Return all registered sources as dictionaries.
    """

    return {
        source_id: entry.to_dict()
        for source_id, entry in SOURCE_REGISTRY.items()
    }


def get_source_entry(
    source_id: str,
) -> SourceRegistryEntry | None:
    """
    Return source registry entry by ID.
    """

    return SOURCE_REGISTRY.get(source_id)


def get_source(
    source_id: str,
) -> dict[str, Any] | None:
    """
    Return source registry entry as dictionary.
    """

    entry = get_source_entry(source_id)

    if entry is None:
        return None

    return entry.to_dict()


def source_exists(
    source_id: str,
) -> bool:
    """
    Return whether source exists.
    """

    return source_id in SOURCE_REGISTRY


def get_sources_by_type(
    source_type: SourceType | str,
) -> dict[str, dict[str, Any]]:
    """
    Return registered sources by source type.
    """

    source_type_value = (
        source_type.value
        if isinstance(source_type, SourceType)
        else str(source_type)
    )

    return {
        source_id: entry.to_dict()
        for source_id, entry in SOURCE_REGISTRY.items()
        if entry.source_type == source_type_value
    }


def get_sources_by_status(
    status: SourceStatus | str,
) -> dict[str, dict[str, Any]]:
    """
    Return registered sources by status.
    """

    status_value = (
        status.value
        if isinstance(status, SourceStatus)
        else str(status)
    )

    return {
        source_id: entry.to_dict()
        for source_id, entry in SOURCE_REGISTRY.items()
        if entry.status == status_value
    }


def get_sources_by_state(
    state: str,
) -> dict[str, dict[str, Any]]:
    """
    Return registered sources by state.
    """

    normalized_state = state.upper().strip()

    return {
        source_id: entry.to_dict()
        for source_id, entry in SOURCE_REGISTRY.items()
        if (entry.state or "").upper() == normalized_state
    }


def get_sources_by_county(
    county: str,
    state: str | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Return registered sources by county and optional state.
    """

    normalized_county = county.lower().strip()
    normalized_state = state.upper().strip() if state else None

    results: dict[str, dict[str, Any]] = {}

    for source_id, entry in SOURCE_REGISTRY.items():
        entry_county = (entry.county or "").lower().strip()
        entry_state = (entry.state or "").upper().strip()

        if entry_county != normalized_county:
            continue

        if normalized_state and entry_state != normalized_state:
            continue

        results[source_id] = entry.to_dict()

    return results


def get_source_group(
    group_name: str,
) -> dict[str, dict[str, Any]]:
    """
    Return all sources in a named source group.
    """

    source_ids = SOURCE_GROUPS.get(group_name, [])

    return {
        source_id: SOURCE_REGISTRY[source_id].to_dict()
        for source_id in source_ids
        if source_id in SOURCE_REGISTRY
    }


def get_all_source_groups() -> dict[str, list[str]]:
    """
    Return source group mapping.
    """

    return {
        group_name: list(source_ids)
        for group_name, source_ids in SOURCE_GROUPS.items()
    }


# ============================================================
# SECTION 13 - CLAIM GOVERNANCE FUNCTIONS
# ============================================================

def get_sources_for_claim(
    claim_type: SourceClaimType | str,
) -> dict[str, dict[str, Any]]:
    """
    Return sources that may support a claim type.
    """

    claim_value = (
        claim_type.value
        if isinstance(claim_type, SourceClaimType)
        else str(claim_type)
    )

    source_ids = CLAIM_SOURCE_GOVERNANCE.get(claim_value, [])

    return {
        source_id: SOURCE_REGISTRY[source_id].to_dict()
        for source_id in source_ids
        if source_id in SOURCE_REGISTRY
    }


def can_source_support_claim(
    source_id: str,
    claim_type: SourceClaimType | str,
) -> bool:
    """
    Return whether a source can support a claim type.
    """

    entry = get_source_entry(source_id)

    if entry is None:
        return False

    claim_value = (
        claim_type.value
        if isinstance(claim_type, SourceClaimType)
        else str(claim_type)
    )

    return entry.supports_claim(claim_value)


def is_claim_public_record_safe(
    claim_type: SourceClaimType | str,
) -> bool:
    """
    Return whether public records can reasonably support a claim.
    """

    claim_value = (
        claim_type.value
        if isinstance(claim_type, SourceClaimType)
        else str(claim_type)
    )

    return claim_value not in CLAIMS_PUBLIC_RECORDS_CANNOT_PROVE


def requires_listing_source(
    claim_type: SourceClaimType | str,
) -> bool:
    """
    Return whether a claim requires listing feed support.
    """

    claim_value = (
        claim_type.value
        if isinstance(claim_type, SourceClaimType)
        else str(claim_type)
    )

    return claim_value in CLAIMS_PUBLIC_RECORDS_CANNOT_PROVE


def get_unsupported_public_record_claims() -> list[str]:
    """
    Return claims that public records cannot prove.
    """

    return list(CLAIMS_PUBLIC_RECORDS_CANNOT_PROVE)


# ============================================================
# SECTION 14 - REGISTRY VALIDATION
# ============================================================

def validate_all_sources() -> SourceValidationReport:
    """
    Validate all source registry entries.
    """

    issues: list[SourceValidationIssue] = []

    for source_id, entry in SOURCE_REGISTRY.items():
        report = validate_registry_entry(entry)

        for issue in report.issues:
            issues.append(issue)

        if not entry.mock_data_allowed:
            continue

        issues.append(
            SourceValidationIssue(
                issue_code="mock_data_enabled",
                message=(
                    f"Source {source_id} has mock_data_allowed=True, "
                    "which violates real-data-first registry rules."
                ),
                severity="critical",
                source_id=source_id,
                manual_review_required=True,
            )
        )

    return SourceValidationReport(
        valid=not issues,
        issues=issues,
    )


def get_registry_integrity_report() -> dict[str, Any]:
    """
    Return complete source registry integrity report.
    """

    validation_report = validate_all_sources()

    status_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    reliability_counts: dict[str, int] = {}

    for entry in SOURCE_REGISTRY.values():
        status_counts[entry.status] = status_counts.get(entry.status, 0) + 1
        type_counts[entry.source_type] = type_counts.get(entry.source_type, 0) + 1
        reliability_counts[entry.reliability] = (
            reliability_counts.get(entry.reliability, 0) + 1
        )

    return {
        "metadata": get_source_registry_metadata(),
        "valid": validation_report.valid,
        "issues": [
            issue.to_dict()
            for issue in validation_report.issues
        ],
        "status_counts": status_counts,
        "type_counts": type_counts,
        "reliability_counts": reliability_counts,
        "mock_sources_allowed": REGISTRY_OPERATING_RULES[
            "mock_sources_allowed"
        ],
        "mock_homes_allowed": REGISTRY_OPERATING_RULES[
            "mock_homes_allowed"
        ],
        "listing_source_required_for_active_status": REGISTRY_OPERATING_RULES[
            "mls_or_listing_feed_required_for_active_status"
        ],
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 15 - MORRIS COUNTY STARTER SOURCE FUNCTIONS
# ============================================================

def get_morris_county_sources() -> dict[str, dict[str, Any]]:
    """
    Return Morris County source set.
    """

    return get_source_group("morris_county_public_records")


def get_new_jersey_state_sources() -> dict[str, dict[str, Any]]:
    """
    Return New Jersey statewide source set.
    """

    return get_source_group("new_jersey_statewide_public_records")


def get_initial_real_data_sources() -> dict[str, dict[str, Any]]:
    """
    Return initial real-data source set for the first build.
    """

    initial_ids = [
        "nj_morris_tax_board",
        "nj_morris_county_clerk_property_records",
        "nj_morris_gis_parcel_searcher",
        "nj_state_parcels_modiv_composite",
    ]

    return {
        source_id: SOURCE_REGISTRY[source_id].to_dict()
        for source_id in initial_ids
        if source_id in SOURCE_REGISTRY
    }


def get_listing_status_sources() -> dict[str, dict[str, Any]]:
    """
    Return sources that may support active listing status.
    """

    return get_source_group("future_listing_status_sources")


def get_public_record_source_status_summary() -> dict[str, Any]:
    """
    Return high-level public-record source summary.
    """

    public_source_ids = [
        "nj_morris_tax_board",
        "nj_morris_county_clerk_property_records",
        "nj_morris_gis_parcel_searcher",
        "nj_state_parcels_modiv_composite",
    ]

    return {
        "public_record_sources": {
            source_id: SOURCE_REGISTRY[source_id].status
            for source_id in public_source_ids
            if source_id in SOURCE_REGISTRY
        },
        "can_support": [
            SourceClaimType.TAX_ASSESSMENT.value,
            SourceClaimType.PROPERTY_TAX.value,
            SourceClaimType.PARCEL_IDENTITY.value,
            SourceClaimType.DEED_REFERENCE.value,
            SourceClaimType.SALE_HISTORY.value,
            SourceClaimType.ADDRESS_IDENTITY.value,
        ],
        "cannot_support_without_listing_feed": get_unsupported_public_record_claims(),
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 16 - REGISTRY SEARCH FUNCTIONS
# ============================================================

def search_sources(
    query: str,
) -> dict[str, dict[str, Any]]:
    """
    Search source registry by text.
    """

    normalized_query = query.lower().strip()

    if not normalized_query:
        return {}

    results: dict[str, dict[str, Any]] = {}

    for source_id, entry in SOURCE_REGISTRY.items():
        haystack = " ".join(
            [
                source_id,
                entry.display_name,
                entry.source_type,
                entry.status,
                entry.reliability,
                entry.jurisdiction or "",
                entry.state or "",
                entry.county or "",
                entry.municipality or "",
                " ".join(entry.expected_claims),
                " ".join(entry.notes),
            ]
        ).lower()

        if normalized_query in haystack:
            results[source_id] = entry.to_dict()

    return results


def list_source_ids() -> list[str]:
    """
    Return all source IDs.
    """

    return list(SOURCE_REGISTRY.keys())


def list_source_display_names() -> dict[str, str]:
    """
    Return source ID to display-name mapping.
    """

    return {
        source_id: entry.display_name
        for source_id, entry in SOURCE_REGISTRY.items()
    }


# ============================================================
# SECTION 17 - DASHBOARD / API SERIALIZATION
# ============================================================

def get_source_registry_dashboard_payload() -> dict[str, Any]:
    """
    Return source registry payload suitable for dashboard/API use.
    """

    return {
        "registry": get_source_registry_metadata(),
        "integrity": get_registry_integrity_report(),
        "initial_sources": get_initial_real_data_sources(),
        "morris_county_sources": get_morris_county_sources(),
        "new_jersey_state_sources": get_new_jersey_state_sources(),
        "listing_status_sources": get_listing_status_sources(),
        "public_record_summary": get_public_record_source_status_summary(),
        "groups": get_all_source_groups(),
        "operating_rules": REGISTRY_OPERATING_RULES,
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 18 - MODULE HEALTH
# ============================================================

def get_source_registry_health() -> dict[str, Any]:
    """
    Return lightweight source registry health.
    """

    validation_report = validate_all_sources()

    return {
        "name": SOURCE_REGISTRY_NAME,
        "version": SOURCE_REGISTRY_VERSION,
        "phase": SOURCE_REGISTRY_PHASE,
        "status": SOURCE_REGISTRY_STATUS,
        "source_count": len(SOURCE_REGISTRY),
        "source_group_count": len(SOURCE_GROUPS),
        "claim_governance_count": len(CLAIM_SOURCE_GOVERNANCE),
        "valid": validation_report.valid,
        "issue_count": len(validation_report.issues),
        "mock_data_allowed": REGISTRY_OPERATING_RULES[
            "mock_sources_allowed"
        ],
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 19 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "SOURCE_REGISTRY_NAME",
    "SOURCE_REGISTRY_VERSION",
    "SOURCE_REGISTRY_PHASE",
    "SOURCE_REGISTRY_STATUS",
    "SOURCE_REGISTRY_DESCRIPTION",
    "REGISTRY_OPERATING_RULES",
    "PUBLIC_PORTAL_POLICY",
    "GIS_SERVICE_POLICY",
    "DOWNLOADABLE_DATASET_POLICY",
    "LICENSED_FEED_POLICY",
    "NJ_MORRIS_TAX_BOARD",
    "NJ_MORRIS_COUNTY_CLERK",
    "NJ_MORRIS_GIS_PARCEL_SEARCHER",
    "NJ_STATE_PARCELS_MODIV",
    "MLS_RESO_FUTURE",
    "BROKER_FEED_FUTURE",
    "FEMA_FLOOD_FUTURE",
    "SCHOOL_DATA_FUTURE",
    "SOURCE_REGISTRY",
    "SOURCE_GROUPS",
    "CLAIM_SOURCE_GOVERNANCE",
    "CLAIMS_PUBLIC_RECORDS_CANNOT_PROVE",
    "capability",
    "utc_now",
    "get_source_registry_metadata",
    "get_all_sources",
    "get_source_entry",
    "get_source",
    "source_exists",
    "get_sources_by_type",
    "get_sources_by_status",
    "get_sources_by_state",
    "get_sources_by_county",
    "get_source_group",
    "get_all_source_groups",
    "get_sources_for_claim",
    "can_source_support_claim",
    "is_claim_public_record_safe",
    "requires_listing_source",
    "get_unsupported_public_record_claims",
    "validate_all_sources",
    "get_registry_integrity_report",
    "get_morris_county_sources",
    "get_new_jersey_state_sources",
    "get_initial_real_data_sources",
    "get_listing_status_sources",
    "get_public_record_source_status_summary",
    "search_sources",
    "list_source_ids",
    "list_source_display_names",
    "get_source_registry_dashboard_payload",
    "get_source_registry_health",
]


# ============================================================
# END OF FILE
# ============================================================