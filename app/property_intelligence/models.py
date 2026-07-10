"""
============================================================
AUSSEM REAL ESTATE
PHASE 5.00 - PROPERTY INTELLIGENCE DOMAIN
FILE: app/property_intelligence/models.py

PURPOSE:
Enterprise SQLAlchemy persistence models for property intelligence,
automated valuation, comparable-property analysis, market analytics,
public-record reconciliation, risk scoring, feature engineering,
machine-learning inference, model governance, explanations, and auditability.

DESIGN PRINCIPLES:
1. SQLAlchemy 2.x typed declarative mappings.
2. PostgreSQL-first, SQLite-compatible development behavior.
3. UUID string identifiers for service portability.
4. Decimal monetary storage; no floating-point currency.
5. Immutable observation/history records where appropriate.
6. JSON payloads for evolving provider- and model-specific metadata.
7. Explicit timestamps, provenance, confidence, and quality controls.
8. No hard foreign key to a project-wide Property table, allowing this
   module to integrate without creating circular imports.
9. Soft deletion and optimistic versioning on mutable aggregates.
10. ML governance fields sufficient for reproducibility and audit review.

IMPORTANT INTEGRATION NOTE:
The module attempts to import the project's shared SQLAlchemy Base from
common locations. If your project uses another Base path, change only the
Base import block in SECTION 03.
============================================================
"""

from __future__ import annotations

import enum
import hashlib
import json
import math
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, ClassVar, Iterable, Mapping, Optional, Sequence

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    event,
    func,
)
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, validates
from sqlalchemy.types import TypeDecorator


# ============================================================
# SECTION 01 - MODULE CONSTANTS
# ============================================================

MONEY_PRECISION = 18
MONEY_SCALE = 2
RATE_PRECISION = 12
RATE_SCALE = 8
SCORE_PRECISION = 7
SCORE_SCALE = 6
AREA_PRECISION = 14
AREA_SCALE = 4
COORDINATE_PRECISION = 11
COORDINATE_SCALE = 8
DEFAULT_CURRENCY = "USD"
DEFAULT_COUNTRY_CODE = "US"
MAX_PROVIDER_NAME_LENGTH = 120
MAX_MODEL_NAME_LENGTH = 180
MAX_EXTERNAL_ID_LENGTH = 255


# ============================================================
# SECTION 02 - GENERIC HELPERS
# ============================================================

def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    """Return a canonical UUID4 string."""
    return str(uuid.uuid4())


def decimal_or_none(value: Any, *, scale: int = MONEY_SCALE) -> Optional[Decimal]:
    """Safely normalize a numeric value to Decimal."""
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        number = value
    else:
        number = Decimal(str(value))
    quantum = Decimal("1").scaleb(-scale)
    return number.quantize(quantum, rounding=ROUND_HALF_UP)


def bounded_decimal(
    value: Any,
    *,
    minimum: Decimal = Decimal("0"),
    maximum: Decimal = Decimal("1"),
    scale: int = SCORE_SCALE,
) -> Optional[Decimal]:
    """Normalize a decimal and enforce inclusive bounds."""
    number = decimal_or_none(value, scale=scale)
    if number is None:
        return None
    if number < minimum or number > maximum:
        raise ValueError(f"value must be between {minimum} and {maximum}")
    return number


def canonical_json(value: Any) -> str:
    """Serialize a value deterministically for hashing."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def payload_sha256(value: Any) -> str:
    """Create a SHA-256 fingerprint for structured payloads."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalize_string(value: Optional[str]) -> Optional[str]:
    """Strip a string and convert empty values to None."""
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def normalize_code(value: Optional[str]) -> Optional[str]:
    """Normalize codes used for state, currency, and classifications."""
    normalized = normalize_string(value)
    return normalized.upper() if normalized else None


def safe_ratio(numerator: Any, denominator: Any) -> Optional[Decimal]:
    """Return a precise ratio or None for invalid/zero denominators."""
    if numerator is None or denominator in (None, 0, Decimal("0")):
        return None
    return Decimal(str(numerator)) / Decimal(str(denominator))


# ============================================================
# SECTION 03 - SHARED DECLARATIVE BASE IMPORT
# ============================================================

try:
    from app.database.base import Base  # type: ignore
except ImportError:
    try:
        from app.database import Base  # type: ignore
    except ImportError:
        try:
            from app.core.database import Base  # type: ignore
        except ImportError:
            class Base(DeclarativeBase):
                """Fallback Base used only when no shared project Base is available."""
                pass


# ============================================================
# SECTION 04 - PORTABLE TYPES
# ============================================================

class GUID(TypeDecorator[str]):
    """
    Portable UUID type.

    UUIDs are stored as CHAR(36)-compatible strings so the same schema works
    in PostgreSQL, SQLite, and test environments without dialect branching.
    """

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value: Any, dialect: Any) -> Optional[str]:
        return str(value) if value is not None else None


class UTCDateTime(TypeDecorator[datetime]):
    """Timezone-safe DateTime that normalizes values to UTC."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: Optional[datetime], dialect: Any) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value: Optional[datetime], dialect: Any) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


# ============================================================
# SECTION 05 - DOMAIN ENUMERATIONS
# ============================================================

class StringEnum(str, enum.Enum):
    """Base enum whose values serialize cleanly to JSON and APIs."""

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]


class RecordStatus(StringEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"


class IntelligenceRunStatus(StringEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IntelligenceRunType(StringEnum):
    FULL = "full"
    VALUATION = "valuation"
    COMPARABLES = "comparables"
    MARKET = "market"
    RISK = "risk"
    PUBLIC_RECORDS = "public_records"
    FEATURE_REFRESH = "feature_refresh"
    MODEL_RESCORING = "model_rescoring"


class PropertyType(StringEnum):
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    COOP = "coop"
    MANUFACTURED = "manufactured"
    LAND = "land"
    FARM = "farm"
    MIXED_USE = "mixed_use"
    COMMERCIAL = "commercial"
    OTHER = "other"
    UNKNOWN = "unknown"


class ListingStatus(StringEnum):
    ACTIVE = "active"
    COMING_SOON = "coming_soon"
    PENDING = "pending"
    UNDER_CONTRACT = "under_contract"
    CONTINGENT = "contingent"
    SOLD = "sold"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    OFF_MARKET = "off_market"
    UNKNOWN = "unknown"


class OccupancyStatus(StringEnum):
    OWNER_OCCUPIED = "owner_occupied"
    TENANT_OCCUPIED = "tenant_occupied"
    VACANT = "vacant"
    SEASONAL = "seasonal"
    UNKNOWN = "unknown"


class DataSourceType(StringEnum):
    MLS = "mls"
    COUNTY = "county"
    MUNICIPAL = "municipal"
    STATE = "state"
    FEDERAL = "federal"
    TAX_ASSESSOR = "tax_assessor"
    DEED = "deed"
    GEOSPATIAL = "geospatial"
    PROVIDER = "provider"
    USER = "user"
    INTERNAL = "internal"
    MODEL = "model"
    WEB = "web"
    OTHER = "other"


class DataQualityStatus(StringEnum):
    VERIFIED = "verified"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CONFLICTED = "conflicted"
    STALE = "stale"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


class ObservationType(StringEnum):
    PROPERTY_FACT = "property_fact"
    LISTING = "listing"
    SALE = "sale"
    TAX = "tax"
    ASSESSMENT = "assessment"
    DEED = "deed"
    MORTGAGE = "mortgage"
    LIEN = "lien"
    PERMIT = "permit"
    VIOLATION = "violation"
    FLOOD = "flood"
    HAZARD = "hazard"
    SCHOOL = "school"
    NEIGHBORHOOD = "neighborhood"
    MARKET = "market"
    OTHER = "other"


class ValuationMethod(StringEnum):
    AUTOMATED_VALUATION_MODEL = "automated_valuation_model"
    COMPARABLE_SALES = "comparable_sales"
    HEDONIC_REGRESSION = "hedonic_regression"
    GRADIENT_BOOSTING = "gradient_boosting"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"
    BROKER_PRICE_OPINION = "broker_price_opinion"
    APPRAISAL = "appraisal"
    MANUAL = "manual"
    OTHER = "other"


class ValuationPurpose(StringEnum):
    CONSUMER_ESTIMATE = "consumer_estimate"
    LIST_PRICE = "list_price"
    OFFER_ANALYSIS = "offer_analysis"
    PORTFOLIO = "portfolio"
    UNDERWRITING = "underwriting"
    TAX_APPEAL = "tax_appeal"
    QUALITY_ASSURANCE = "quality_assurance"
    OTHER = "other"


class ComparableStatus(StringEnum):
    CANDIDATE = "candidate"
    SELECTED = "selected"
    EXCLUDED = "excluded"
    OVERRIDDEN = "overridden"


class AdjustmentType(StringEnum):
    LOCATION = "location"
    TIME = "time"
    LIVING_AREA = "living_area"
    LOT_SIZE = "lot_size"
    BEDROOMS = "bedrooms"
    BATHROOMS = "bathrooms"
    AGE = "age"
    CONDITION = "condition"
    QUALITY = "quality"
    GARAGE = "garage"
    BASEMENT = "basement"
    POOL = "pool"
    VIEW = "view"
    WATERFRONT = "waterfront"
    HOA = "hoa"
    OTHER = "other"


class MarketGranularity(StringEnum):
    PARCEL = "parcel"
    ZIP_CODE = "zip_code"
    CITY = "city"
    COUNTY = "county"
    METRO = "metro"
    STATE = "state"
    NATIONAL = "national"
    CUSTOM = "custom"


class MarketTrend(StringEnum):
    RAPIDLY_APPRECIATING = "rapidly_appreciating"
    APPRECIATING = "appreciating"
    STABLE = "stable"
    DEPRECIATING = "depreciating"
    RAPIDLY_DEPRECIATING = "rapidly_depreciating"
    INSUFFICIENT_DATA = "insufficient_data"


class MarketTemperature(StringEnum):
    STRONG_SELLERS = "strong_sellers"
    SELLERS = "sellers"
    BALANCED = "balanced"
    BUYERS = "buyers"
    STRONG_BUYERS = "strong_buyers"
    UNKNOWN = "unknown"


class RiskCategory(StringEnum):
    FLOOD = "flood"
    WILDFIRE = "wildfire"
    HURRICANE = "hurricane"
    EARTHQUAKE = "earthquake"
    TORNADO = "tornado"
    CLIMATE = "climate"
    ENVIRONMENTAL = "environmental"
    TITLE = "title"
    LIEN = "lien"
    TAX = "tax"
    PERMIT = "permit"
    STRUCTURAL = "structural"
    INSURANCE = "insurance"
    MARKET = "market"
    LIQUIDITY = "liquidity"
    FRAUD = "fraud"
    DATA_QUALITY = "data_quality"
    OTHER = "other"


class RiskSeverity(StringEnum):
    INFO = "info"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class FeatureValueType(StringEnum):
    NUMERIC = "numeric"
    BOOLEAN = "boolean"
    CATEGORICAL = "categorical"
    TEXT = "text"
    VECTOR = "vector"
    JSON = "json"
    DATE = "date"
    DATETIME = "datetime"


class FeatureOrigin(StringEnum):
    RAW = "raw"
    DERIVED = "derived"
    AGGREGATED = "aggregated"
    EMBEDDING = "embedding"
    MODEL_OUTPUT = "model_output"
    MANUAL = "manual"


class ModelLifecycleStatus(StringEnum):
    DRAFT = "draft"
    VALIDATING = "validating"
    STAGING = "staging"
    PRODUCTION = "production"
    CHALLENGER = "challenger"
    RETIRED = "retired"
    REJECTED = "rejected"


class ModelFramework(StringEnum):
    SCIKIT_LEARN = "scikit_learn"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    CATBOOST = "catboost"
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    ONNX = "onnx"
    STATISTICAL = "statistical"
    RULES = "rules"
    ENSEMBLE = "ensemble"
    EXTERNAL = "external"
    OTHER = "other"


class PredictionType(StringEnum):
    PROPERTY_VALUE = "property_value"
    VALUE_RANGE = "value_range"
    SALE_PROBABILITY = "sale_probability"
    DAYS_ON_MARKET = "days_on_market"
    LIST_TO_SALE_RATIO = "list_to_sale_ratio"
    APPRECIATION = "appreciation"
    RENT = "rent"
    RISK = "risk"
    LIQUIDITY = "liquidity"
    LEAD_SCORE = "lead_score"
    OTHER = "other"


class ExplanationMethod(StringEnum):
    SHAP = "shap"
    LIME = "lime"
    FEATURE_IMPORTANCE = "feature_importance"
    ATTENTION = "attention"
    COUNTERFACTUAL = "counterfactual"
    RULE_TRACE = "rule_trace"
    COMPARABLES = "comparables"
    HUMAN = "human"
    OTHER = "other"


class ReviewDecision(StringEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    ESCALATED = "escalated"


class DriftType(StringEnum):
    DATA = "data"
    FEATURE = "feature"
    PREDICTION = "prediction"
    PERFORMANCE = "performance"
    CONCEPT = "concept"


class DriftSeverity(StringEnum):
    NORMAL = "normal"
    WATCH = "watch"
    WARNING = "warning"
    CRITICAL = "critical"


class EntityResolutionStatus(StringEnum):
    UNRESOLVED = "unresolved"
    MATCHED = "matched"
    CONFLICTED = "conflicted"
    MERGED = "merged"
    REJECTED = "rejected"


# ============================================================
# SECTION 06 - ENUM COLUMN FACTORY
# ============================================================

def enum_column(enum_type: type[StringEnum], *, default: Any, nullable: bool = False):
    """Create a non-native string Enum column with validation."""
    return mapped_column(
        SAEnum(
            enum_type,
            native_enum=False,
            validate_strings=True,
            values_callable=lambda members: [member.value for member in members],
            length=max(len(item.value) for item in enum_type),
        ),
        default=default,
        nullable=nullable,
    )


# ============================================================
# SECTION 07 - REUSABLE MIXINS
# ============================================================

class UUIDPrimaryKeyMixin:
    id: Mapped[str] = mapped_column(GUID(), primary_key=True, default=new_uuid)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        server_default=func.now(),
    )


class SoftDeleteMixin:
    deleted_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, actor_id: Optional[str] = None) -> None:
        self.deleted_at = utcnow()
        self.deleted_by = actor_id

    def restore(self) -> None:
        self.deleted_at = None
        self.deleted_by = None


class VersionedMixin:
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __mapper_args__: ClassVar[dict[str, Any]] = {
        "version_id_col": row_version,
        "version_id_generator": lambda version: (version or 0) + 1,
    }


class TenantMixin:
    tenant_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        nullable=True,
        index=True,
        doc="Optional tenant/account boundary for multi-tenant deployments.",
    )


class ProvenanceMixin:
    source_type: Mapped[DataSourceType] = enum_column(
        DataSourceType,
        default=DataSourceType.INTERNAL,
    )
    source_name: Mapped[Optional[str]] = mapped_column(
        String(MAX_PROVIDER_NAME_LENGTH),
        nullable=True,
        index=True,
    )
    source_record_id: Mapped[Optional[str]] = mapped_column(
        String(MAX_EXTERNAL_ID_LENGTH),
        nullable=True,
        index=True,
    )
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_observed_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    source_retrieved_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    source_payload_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)


class QualityMixin:
    quality_status: Mapped[DataQualityStatus] = enum_column(
        DataQualityStatus,
        default=DataQualityStatus.UNKNOWN,
    )
    quality_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    quality_flags: Mapped[list[Any]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
        default=list,
    )

    @validates("quality_score", "confidence_score")
    def _validate_score(self, key: str, value: Any) -> Optional[Decimal]:
        return bounded_decimal(value)


class MetadataMixin:
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )


class PropertyReferenceMixin:
    property_id: Mapped[str] = mapped_column(
        GUID(),
        nullable=False,
        index=True,
        doc="Canonical project property identifier.",
    )


# ============================================================
# SECTION 08 - PROPERTY INTELLIGENCE PROFILE
# ============================================================

class PropertyIntelligenceProfile(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    VersionedMixin,
    TenantMixin,
    MetadataMixin,
):
    """
    Canonical intelligence aggregate for one property.

    This table does not replace the core Property entity. It stores the
    intelligence subsystem's normalized snapshot, latest scores, and workflow
    state while preserving the core property's independent lifecycle.
    """

    __tablename__ = "property_intelligence_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "property_id", name="uq_pi_profile_tenant_property"),
        CheckConstraint("bedrooms IS NULL OR bedrooms >= 0", name="ck_pi_profile_bedrooms"),
        CheckConstraint("bathrooms IS NULL OR bathrooms >= 0", name="ck_pi_profile_bathrooms"),
        CheckConstraint("year_built IS NULL OR year_built >= 1600", name="ck_pi_profile_year_built"),
        Index("ix_pi_profile_location", "state_code", "postal_code", "city"),
        Index("ix_pi_profile_status", "listing_status", "record_status"),
    )

    property_id: Mapped[str] = mapped_column(GUID(), nullable=False, index=True)
    record_status: Mapped[RecordStatus] = enum_column(
        RecordStatus,
        default=RecordStatus.ACTIVE,
    )
    intelligence_version: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="1.0",
    )
    canonical_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    address_line_1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line_2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    county: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    state_code: Mapped[Optional[str]] = mapped_column(String(12), nullable=True, index=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    country_code: Mapped[str] = mapped_column(String(3), nullable=False, default=DEFAULT_COUNTRY_CODE)
    latitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(COORDINATE_PRECISION, COORDINATE_SCALE),
        nullable=True,
    )
    longitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(COORDINATE_PRECISION, COORDINATE_SCALE),
        nullable=True,
    )
    parcel_number: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    tax_account_number: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    property_type: Mapped[PropertyType] = enum_column(
        PropertyType,
        default=PropertyType.UNKNOWN,
    )
    listing_status: Mapped[ListingStatus] = enum_column(
        ListingStatus,
        default=ListingStatus.UNKNOWN,
    )
    occupancy_status: Mapped[OccupancyStatus] = enum_column(
        OccupancyStatus,
        default=OccupancyStatus.UNKNOWN,
    )
    bedrooms: Mapped[Optional[Decimal]] = mapped_column(Numeric(7, 2), nullable=True)
    bathrooms: Mapped[Optional[Decimal]] = mapped_column(Numeric(7, 2), nullable=True)
    living_area_sqft: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(AREA_PRECISION, AREA_SCALE),
        nullable=True,
    )
    lot_size_sqft: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(AREA_PRECISION, AREA_SCALE),
        nullable=True,
    )
    year_built: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_sale_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_sale_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    current_list_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    latest_estimated_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    latest_value_low: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    latest_value_high: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    latest_value_confidence: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    overall_risk_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    data_completeness_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    data_freshness_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    last_intelligence_run_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    next_refresh_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    search_document: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    runs: Mapped[list["PropertyIntelligenceRun"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    observations: Mapped[list["PropertyObservation"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    valuations: Mapped[list["PropertyValuation"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    risk_assessments: Mapped[list["PropertyRiskAssessment"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    feature_snapshots: Mapped[list["PropertyFeatureSnapshot"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    predictions: Mapped[list["ModelPrediction"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @validates("state_code", "country_code")
    def _normalize_codes(self, key: str, value: Optional[str]) -> Optional[str]:
        return normalize_code(value)

    @validates("latest_value_confidence", "overall_risk_score", "data_completeness_score", "data_freshness_score")
    def _validate_profile_score(self, key: str, value: Any) -> Optional[Decimal]:
        return bounded_decimal(value)

    @property
    def value_range_width(self) -> Optional[Decimal]:
        if self.latest_value_low is None or self.latest_value_high is None:
            return None
        return self.latest_value_high - self.latest_value_low

    @property
    def age(self) -> Optional[int]:
        if not self.year_built:
            return None
        return max(date.today().year - self.year_built, 0)

    def synchronize_latest_valuation(self, valuation: "PropertyValuation") -> None:
        """Copy a completed valuation into the profile's fast-access fields."""
        self.latest_estimated_value = valuation.estimated_value
        self.latest_value_low = valuation.value_low
        self.latest_value_high = valuation.value_high
        self.latest_value_confidence = valuation.confidence_score
        self.last_intelligence_run_at = valuation.valuation_date


# ============================================================
# SECTION 09 - INTELLIGENCE RUN ORCHESTRATION
# ============================================================

class PropertyIntelligenceRun(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "property_intelligence_runs"
    __table_args__ = (
        Index("ix_pi_run_profile_status", "profile_id", "status"),
        Index("ix_pi_run_requested", "requested_at", "run_type"),
    )

    profile_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    property_id: Mapped[str] = mapped_column(GUID(), nullable=False, index=True)
    run_type: Mapped[IntelligenceRunType] = enum_column(
        IntelligenceRunType,
        default=IntelligenceRunType.FULL,
    )
    status: Mapped[IntelligenceRunStatus] = enum_column(
        IntelligenceRunStatus,
        default=IntelligenceRunStatus.QUEUED,
    )
    correlation_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(180), nullable=True, unique=True)
    requested_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    pipeline_version: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    input_fingerprint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    records_read: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_written: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warnings: Mapped[list[Any]] = mapped_column(MutableList.as_mutable(JSON), nullable=False, default=list)
    errors: Mapped[list[Any]] = mapped_column(MutableList.as_mutable(JSON), nullable=False, default=list)
    metrics: Mapped[dict[str, Any]] = mapped_column(MutableDict.as_mutable(JSON), nullable=False, default=dict)

    profile: Mapped["PropertyIntelligenceProfile"] = relationship(back_populates="runs")

    @property
    def duration_seconds(self) -> Optional[float]:
        if not self.started_at:
            return None
        ending = self.completed_at or utcnow()
        return max((ending - self.started_at).total_seconds(), 0.0)

    def start(self) -> None:
        if self.status not in {IntelligenceRunStatus.QUEUED, IntelligenceRunStatus.FAILED}:
            raise ValueError(f"cannot start run from status {self.status}")
        self.status = IntelligenceRunStatus.RUNNING
        self.started_at = utcnow()
        self.completed_at = None

    def succeed(self, *, partial: bool = False) -> None:
        self.status = (
            IntelligenceRunStatus.PARTIAL
            if partial
            else IntelligenceRunStatus.SUCCEEDED
        )
        self.completed_at = utcnow()

    def fail(self, error: Any) -> None:
        self.status = IntelligenceRunStatus.FAILED
        self.completed_at = utcnow()
        self.error_count += 1
        self.errors.append(error if isinstance(error, dict) else {"message": str(error)})


# ============================================================
# SECTION 10 - DATA SOURCE REGISTRY AND RAW OBSERVATIONS
# ============================================================

class IntelligenceDataSource(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    VersionedMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "property_intelligence_data_sources"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_pi_source_tenant_slug"),
        Index("ix_pi_source_type_enabled", "source_type", "is_enabled"),
    )

    name: Mapped[str] = mapped_column(String(MAX_PROVIDER_NAME_LENGTH), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    source_type: Mapped[DataSourceType] = enum_column(
        DataSourceType,
        default=DataSourceType.PROVIDER,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    authority_rank: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    default_confidence: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    terms_version: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    license_name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    base_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    freshness_sla_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_success_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)

    @validates("default_confidence")
    def _validate_confidence(self, key: str, value: Any) -> Optional[Decimal]:
        return bounded_decimal(value)


class PropertyObservation(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    ProvenanceMixin,
    QualityMixin,
    MetadataMixin,
):
    """
    Append-oriented normalized observation.

    `field_path` identifies a canonical field such as
    ``property.living_area_sqft`` or ``tax.assessed_value``.
    Exactly one or several value columns may be populated depending on the
    observation type; `value_json` supports complex provider payloads.
    """

    __tablename__ = "property_intelligence_observations"
    __table_args__ = (
        Index("ix_pi_observation_property_field", "property_id", "field_path"),
        Index("ix_pi_observation_profile_type", "profile_id", "observation_type"),
        Index("ix_pi_observation_effective", "effective_from", "effective_to"),
        Index("ix_pi_observation_source", "source_name", "source_record_id"),
    )

    profile_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    property_id: Mapped[str] = mapped_column(GUID(), nullable=False, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    observation_type: Mapped[ObservationType] = enum_column(
        ObservationType,
        default=ObservationType.PROPERTY_FACT,
    )
    field_path: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    value_type: Mapped[FeatureValueType] = enum_column(
        FeatureValueType,
        default=FeatureValueType.JSON,
    )
    value_numeric: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8), nullable=True)
    value_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_boolean: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    value_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    value_datetime: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    value_json: Mapped[Optional[dict[str, Any]]] = mapped_column(MutableDict.as_mutable(JSON), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    effective_from: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    effective_to: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    supersedes_observation_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_observations.id", ondelete="SET NULL"),
        nullable=True,
    )

    profile: Mapped["PropertyIntelligenceProfile"] = relationship(back_populates="observations")

    @validates("currency_code")
    def _normalize_currency(self, key: str, value: Optional[str]) -> Optional[str]:
        return normalize_code(value)

    def materialized_value(self) -> Any:
        """Return the populated value according to the declared type."""
        mapping = {
            FeatureValueType.NUMERIC: self.value_numeric,
            FeatureValueType.BOOLEAN: self.value_boolean,
            FeatureValueType.TEXT: self.value_text,
            FeatureValueType.CATEGORICAL: self.value_text,
            FeatureValueType.DATE: self.value_date,
            FeatureValueType.DATETIME: self.value_datetime,
            FeatureValueType.JSON: self.value_json,
            FeatureValueType.VECTOR: self.value_json,
        }
        return mapping.get(self.value_type)


# ============================================================
# SECTION 11 - ENTITY RESOLUTION AND CONFLICT MANAGEMENT
# ============================================================

class PropertyEntityResolution(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "property_entity_resolutions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_name",
            "source_property_id",
            name="uq_pi_resolution_external_property",
        ),
        Index("ix_pi_resolution_canonical", "canonical_property_id", "status"),
    )

    source_name: Mapped[str] = mapped_column(String(MAX_PROVIDER_NAME_LENGTH), nullable=False)
    source_property_id: Mapped[str] = mapped_column(String(MAX_EXTERNAL_ID_LENGTH), nullable=False)
    canonical_property_id: Mapped[Optional[str]] = mapped_column(GUID(), nullable=True, index=True)
    status: Mapped[EntityResolutionStatus] = enum_column(
        EntityResolutionStatus,
        default=EntityResolutionStatus.UNRESOLVED,
    )
    match_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    match_method: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    normalized_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    parcel_number: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    candidate_property_ids: Mapped[list[Any]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
        default=list,
    )
    conflicting_fields: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)

    @validates("match_score")
    def _validate_match_score(self, key: str, value: Any) -> Optional[Decimal]:
        return bounded_decimal(value)


class PropertyDataConflict(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "property_data_conflicts"
    __table_args__ = (
        Index("ix_pi_conflict_property_status", "property_id", "is_resolved"),
        Index("ix_pi_conflict_field", "field_path", "severity"),
    )

    property_id: Mapped[str] = mapped_column(GUID(), nullable=False, index=True)
    profile_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    field_path: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[RiskSeverity] = enum_column(
        RiskSeverity,
        default=RiskSeverity.MODERATE,
    )
    candidate_values: Mapped[list[Any]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
        default=list,
    )
    winning_value: Mapped[Optional[dict[str, Any]]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=True,
    )
    resolution_strategy: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    resolution_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)


# ============================================================
# SECTION 12 - PROPERTY VALUATION
# ============================================================

class PropertyValuation(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    ProvenanceMixin,
    QualityMixin,
    MetadataMixin,
):
    __tablename__ = "property_valuations"
    __table_args__ = (
        CheckConstraint("estimated_value >= 0", name="ck_pi_valuation_estimated_nonnegative"),
        CheckConstraint("value_low IS NULL OR value_low >= 0", name="ck_pi_valuation_low_nonnegative"),
        CheckConstraint("value_high IS NULL OR value_high >= 0", name="ck_pi_valuation_high_nonnegative"),
        CheckConstraint(
            "value_low IS NULL OR value_high IS NULL OR value_low <= value_high",
            name="ck_pi_valuation_range_order",
        ),
        Index("ix_pi_valuation_property_date", "property_id", "valuation_date"),
        Index("ix_pi_valuation_profile_purpose", "profile_id", "purpose"),
        Index("ix_pi_valuation_model", "model_version_id", "valuation_date"),
    )

    profile_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    property_id: Mapped[str] = mapped_column(GUID(), nullable=False, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model_version_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("ml_model_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    method: Mapped[ValuationMethod] = enum_column(
        ValuationMethod,
        default=ValuationMethod.AUTOMATED_VALUATION_MODEL,
    )
    purpose: Mapped[ValuationPurpose] = enum_column(
        ValuationPurpose,
        default=ValuationPurpose.CONSUMER_ESTIMATE,
    )
    valuation_date: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default=DEFAULT_CURRENCY)
    estimated_value: Mapped[Decimal] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=False,
    )
    value_low: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    value_high: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    standard_error: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)
    prediction_interval: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    price_per_sqft: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    comparable_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    feature_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_snapshot_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    model_output: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    assumptions: Mapped[list[Any]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
        default=list,
    )
    limitations: Mapped[list[Any]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
        default=list,
    )
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)

    profile: Mapped["PropertyIntelligenceProfile"] = relationship(back_populates="valuations")
    comparables: Mapped[list["ValuationComparable"]] = relationship(
        back_populates="valuation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    explanations: Mapped[list["PredictionExplanation"]] = relationship(
        primaryjoin="and_(PropertyValuation.id == foreign(PredictionExplanation.valuation_id))",
        viewonly=True,
    )

    @validates("currency_code")
    def _normalize_currency(self, key: str, value: Optional[str]) -> str:
        return normalize_code(value) or DEFAULT_CURRENCY

    @validates("prediction_interval")
    def _validate_interval(self, key: str, value: Any) -> Optional[Decimal]:
        return bounded_decimal(value)

    @property
    def range_width(self) -> Optional[Decimal]:
        if self.value_low is None or self.value_high is None:
            return None
        return self.value_high - self.value_low

    @property
    def range_width_ratio(self) -> Optional[Decimal]:
        return safe_ratio(self.range_width, self.estimated_value)

    def publish(self) -> None:
        self.is_published = True
        self.published_at = utcnow()


class ValuationComparable(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "valuation_comparables"
    __table_args__ = (
        UniqueConstraint("valuation_id", "comparable_property_id", name="uq_pi_valuation_comp"),
        Index("ix_pi_comp_valuation_rank", "valuation_id", "selection_rank"),
        Index("ix_pi_comp_property", "comparable_property_id", "sale_date"),
    )

    valuation_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("property_valuations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_property_id: Mapped[str] = mapped_column(GUID(), nullable=False, index=True)
    comparable_property_id: Mapped[str] = mapped_column(GUID(), nullable=False, index=True)
    status: Mapped[ComparableStatus] = enum_column(
        ComparableStatus,
        default=ComparableStatus.CANDIDATE,
    )
    selection_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    selection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exclusion_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    distance_miles: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6), nullable=True)
    similarity_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    recency_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    location_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    sale_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sale_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    sale_price_per_sqft: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    gross_adjustment: Mapped[Decimal] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=False,
        default=Decimal("0"),
    )
    net_adjustment: Mapped[Decimal] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=False,
        default=Decimal("0"),
    )
    adjusted_sale_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    weight: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    is_manual_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    selected_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    valuation: Mapped["PropertyValuation"] = relationship(back_populates="comparables")
    adjustments: Mapped[list["ComparableAdjustment"]] = relationship(
        back_populates="comparable",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @validates("similarity_score", "recency_score", "location_score", "weight")
    def _validate_comp_score(self, key: str, value: Any) -> Optional[Decimal]:
        return bounded_decimal(value)

    def recalculate_adjusted_price(self) -> Optional[Decimal]:
        if self.sale_price is None:
            self.adjusted_sale_price = None
        else:
            self.adjusted_sale_price = self.sale_price + self.net_adjustment
        return self.adjusted_sale_price


class ComparableAdjustment(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "comparable_adjustments"
    __table_args__ = (
        Index("ix_pi_adjustment_comp_type", "comparable_id", "adjustment_type"),
    )

    comparable_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("valuation_comparables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    adjustment_type: Mapped[AdjustmentType] = enum_column(
        AdjustmentType,
        default=AdjustmentType.OTHER,
    )
    feature_name: Mapped[str] = mapped_column(String(180), nullable=False)
    subject_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comparable_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    adjustment_amount: Mapped[Decimal] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=False,
        default=Decimal("0"),
    )
    adjustment_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 8), nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    methodology: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )

    comparable: Mapped["ValuationComparable"] = relationship(back_populates="adjustments")

    @validates("confidence_score")
    def _validate_confidence(self, key: str, value: Any) -> Optional[Decimal]:
        return bounded_decimal(value)


# ============================================================
# SECTION 13 - MARKET INTELLIGENCE
# ============================================================

class MarketArea(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    VersionedMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "market_areas"
    __table_args__ = (
        UniqueConstraint("tenant_id", "granularity", "external_code", name="uq_pi_market_area_code"),
        Index("ix_pi_market_area_location", "state_code", "county", "city", "postal_code"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    granularity: Mapped[MarketGranularity] = enum_column(
        MarketGranularity,
        default=MarketGranularity.CUSTOM,
    )
    external_code: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    state_code: Mapped[Optional[str]] = mapped_column(String(12), nullable=True, index=True)
    county: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    boundary_geojson: Mapped[Optional[dict[str, Any]]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=True,
    )
    centroid_latitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(COORDINATE_PRECISION, COORDINATE_SCALE),
        nullable=True,
    )
    centroid_longitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(COORDINATE_PRECISION, COORDINATE_SCALE),
        nullable=True,
    )
    parent_area_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("market_areas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    parent_area: Mapped[Optional["MarketArea"]] = relationship(
        remote_side="MarketArea.id",
        back_populates="child_areas",
    )
    child_areas: Mapped[list["MarketArea"]] = relationship(back_populates="parent_area")
    snapshots: Mapped[list["MarketSnapshot"]] = relationship(
        back_populates="market_area",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @validates("state_code")
    def _normalize_state(self, key: str, value: Optional[str]) -> Optional[str]:
        return normalize_code(value)


class MarketSnapshot(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    ProvenanceMixin,
    QualityMixin,
    MetadataMixin,
):
    __tablename__ = "market_snapshots"
    __table_args__ = (
        UniqueConstraint("market_area_id", "period_start", "period_end", name="uq_pi_market_period"),
        Index("ix_pi_market_snapshot_period", "period_end", "market_temperature"),
    )

    market_area_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("market_areas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    market_temperature: Mapped[MarketTemperature] = enum_column(
        MarketTemperature,
        default=MarketTemperature.UNKNOWN,
    )
    market_trend: Mapped[MarketTrend] = enum_column(
        MarketTrend,
        default=MarketTrend.INSUFFICIENT_DATA,
    )
    active_inventory: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    new_listings: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pending_sales: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    closed_sales: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    median_list_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    median_sale_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    average_sale_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    median_price_per_sqft: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    median_days_on_market: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    months_of_supply: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    sale_to_list_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 8), nullable=True)
    year_over_year_appreciation: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 8), nullable=True)
    month_over_month_change: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 8), nullable=True)
    absorption_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 8), nullable=True)
    price_reduction_share: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 8), nullable=True)
    cash_sale_share: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 8), nullable=True)
    distressed_sale_share: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 8), nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    market_area: Mapped["MarketArea"] = relationship(back_populates="snapshots")


class PropertyMarketMembership(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "property_market_memberships"
    __table_args__ = (
        UniqueConstraint("property_id", "market_area_id", "membership_type", name="uq_pi_property_market"),
        Index("ix_pi_membership_property_primary", "property_id", "is_primary"),
    )

    property_id: Mapped[str] = mapped_column(GUID(), nullable=False, index=True)
    market_area_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("market_areas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    membership_type: Mapped[str] = mapped_column(String(80), nullable=False, default="geographic")
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    match_confidence: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )

    @validates("match_confidence")
    def _validate_confidence(self, key: str, value: Any) -> Optional[Decimal]:
        return bounded_decimal(value)


# ============================================================
# SECTION 14 - PROPERTY RISK INTELLIGENCE
# ============================================================

class PropertyRiskAssessment(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    ProvenanceMixin,
    QualityMixin,
    MetadataMixin,
):
    __tablename__ = "property_risk_assessments"
    __table_args__ = (
        Index("ix_pi_risk_property_category", "property_id", "risk_category"),
        Index("ix_pi_risk_profile_severity", "profile_id", "severity"),
        Index("ix_pi_risk_expiration", "expires_at", "is_active"),
    )

    profile_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    property_id: Mapped[str] = mapped_column(GUID(), nullable=False, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    risk_category: Mapped[RiskCategory] = enum_column(
        RiskCategory,
        default=RiskCategory.OTHER,
    )
    severity: Mapped[RiskSeverity] = enum_column(
        RiskSeverity,
        default=RiskSeverity.INFO,
    )
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=False,
        default=Decimal("0"),
    )
    probability: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    impact_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    exposure_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[list[Any]] = mapped_column(MutableList.as_mutable(JSON), nullable=False, default=list)
    mitigations: Mapped[list[Any]] = mapped_column(MutableList.as_mutable(JSON), nullable=False, default=list)
    assessed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    profile: Mapped["PropertyIntelligenceProfile"] = relationship(back_populates="risk_assessments")

    @validates("risk_score", "probability", "impact_score")
    def _validate_risk_score(self, key: str, value: Any) -> Optional[Decimal]:
        return bounded_decimal(value)


# ============================================================
# SECTION 15 - FEATURE STORE
# ============================================================

class FeatureDefinition(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    VersionedMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "ml_feature_definitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", "version", name="uq_pi_feature_name_version"),
        Index("ix_pi_feature_active_origin", "is_active", "origin"),
    )

    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(40), nullable=False, default="1")
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_type: Mapped[FeatureValueType] = enum_column(
        FeatureValueType,
        default=FeatureValueType.NUMERIC,
    )
    origin: Mapped[FeatureOrigin] = enum_column(
        FeatureOrigin,
        default=FeatureOrigin.DERIVED,
    )
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False, default="property")
    unit: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    expression: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_fields: Mapped[list[Any]] = mapped_column(MutableList.as_mutable(JSON), nullable=False, default=list)
    allowed_values: Mapped[list[Any]] = mapped_column(MutableList.as_mutable(JSON), nullable=False, default=list)
    default_value: Mapped[Optional[dict[str, Any]]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=True,
    )
    minimum_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8), nullable=True)
    maximum_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8), nullable=True)
    missing_value_strategy: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    freshness_sla_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_leakage_risk: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tags: Mapped[list[Any]] = mapped_column(MutableList.as_mutable(JSON), nullable=False, default=list)

    values: Mapped[list["PropertyFeatureValue"]] = relationship(
        back_populates="feature_definition",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PropertyFeatureSnapshot(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    QualityMixin,
    MetadataMixin,
):
    __tablename__ = "property_feature_snapshots"
    __table_args__ = (
        UniqueConstraint("property_id", "snapshot_at", "feature_set_version", name="uq_pi_feature_snapshot"),
        Index("ix_pi_feature_snapshot_profile_time", "profile_id", "snapshot_at"),
        Index("ix_pi_feature_snapshot_hash", "payload_hash"),
    )

    profile_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    property_id: Mapped[str] = mapped_column(GUID(), nullable=False, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    snapshot_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)
    feature_set_name: Mapped[str] = mapped_column(String(180), nullable=False, default="property_core")
    feature_set_version: Mapped[str] = mapped_column(String(40), nullable=False, default="1")
    point_in_time_cutoff: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    payload_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    feature_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    missing_feature_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    freshness_lag_seconds: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    feature_payload: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )

    profile: Mapped["PropertyIntelligenceProfile"] = relationship(back_populates="feature_snapshots")
    values: Mapped[list["PropertyFeatureValue"]] = relationship(
        back_populates="snapshot",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def refresh_hash(self) -> str:
        self.payload_hash = payload_sha256(self.feature_payload)
        self.feature_count = len(self.feature_payload)
        return self.payload_hash


class PropertyFeatureValue(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    ProvenanceMixin,
    QualityMixin,
    MetadataMixin,
):
    __tablename__ = "property_feature_values"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "feature_definition_id", name="uq_pi_snapshot_feature"),
        Index("ix_pi_feature_value_property_feature", "property_id", "feature_definition_id"),
        Index("ix_pi_feature_value_effective", "effective_at", "expires_at"),
    )

    snapshot_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("property_feature_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_definition_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("ml_feature_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    property_id: Mapped[str] = mapped_column(GUID(), nullable=False, index=True)
    value_numeric: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8), nullable=True)
    value_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_boolean: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    value_json: Mapped[Optional[dict[str, Any]]] = mapped_column(MutableDict.as_mutable(JSON), nullable=True)
    vector_values: Mapped[Optional[list[Any]]] = mapped_column(MutableList.as_mutable(JSON), nullable=True)
    is_missing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    missing_reason: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    effective_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)

    snapshot: Mapped["PropertyFeatureSnapshot"] = relationship(back_populates="values")
    feature_definition: Mapped["FeatureDefinition"] = relationship(back_populates="values")


# ============================================================
# SECTION 16 - MACHINE LEARNING MODEL REGISTRY
# ============================================================

class MLModel(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    VersionedMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "ml_models"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_pi_model_tenant_name"),
        Index("ix_pi_model_prediction_type_status", "prediction_type", "status"),
    )

    name: Mapped[str] = mapped_column(String(MAX_MODEL_NAME_LENGTH), nullable=False, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prediction_type: Mapped[PredictionType] = enum_column(
        PredictionType,
        default=PredictionType.PROPERTY_VALUE,
    )
    status: Mapped[ModelLifecycleStatus] = enum_column(
        ModelLifecycleStatus,
        default=ModelLifecycleStatus.DRAFT,
    )
    owner: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    business_owner: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    risk_tier: Mapped[str] = mapped_column(String(40), nullable=False, default="medium")
    tags: Mapped[list[Any]] = mapped_column(MutableList.as_mutable(JSON), nullable=False, default=list)

    versions: Mapped[list["MLModelVersion"]] = relationship(
        back_populates="model",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class MLModelVersion(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "ml_model_versions"
    __table_args__ = (
        UniqueConstraint("model_id", "version", name="uq_pi_model_version"),
        Index("ix_pi_model_version_stage", "lifecycle_status", "deployed_at"),
        Index("ix_pi_model_artifact_hash", "artifact_sha256"),
    )

    model_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    lifecycle_status: Mapped[ModelLifecycleStatus] = enum_column(
        ModelLifecycleStatus,
        default=ModelLifecycleStatus.DRAFT,
    )
    framework: Mapped[ModelFramework] = enum_column(
        ModelFramework,
        default=ModelFramework.OTHER,
    )
    framework_version: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    python_version: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    algorithm: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    artifact_uri: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    artifact_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    container_image: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_commit_sha: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    training_run_id: Mapped[Optional[str]] = mapped_column(String(180), nullable=True, index=True)
    training_dataset_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    feature_set_name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    feature_set_version: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    hyperparameters: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    training_metrics: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    validation_metrics: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    test_metrics: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    baseline_statistics: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    model_card: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    fairness_report: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    approved_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    deployed_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    retired_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)

    model: Mapped["MLModel"] = relationship(back_populates="versions")
    predictions: Mapped[list["ModelPrediction"]] = relationship(back_populates="model_version")

    def promote(self, status: ModelLifecycleStatus, actor_id: Optional[str] = None) -> None:
        allowed = {
            ModelLifecycleStatus.DRAFT: {
                ModelLifecycleStatus.VALIDATING,
                ModelLifecycleStatus.REJECTED,
            },
            ModelLifecycleStatus.VALIDATING: {
                ModelLifecycleStatus.STAGING,
                ModelLifecycleStatus.REJECTED,
            },
            ModelLifecycleStatus.STAGING: {
                ModelLifecycleStatus.PRODUCTION,
                ModelLifecycleStatus.CHALLENGER,
                ModelLifecycleStatus.REJECTED,
            },
            ModelLifecycleStatus.CHALLENGER: {
                ModelLifecycleStatus.PRODUCTION,
                ModelLifecycleStatus.RETIRED,
            },
            ModelLifecycleStatus.PRODUCTION: {
                ModelLifecycleStatus.RETIRED,
            },
        }
        if status not in allowed.get(self.lifecycle_status, set()):
            raise ValueError(f"invalid model transition: {self.lifecycle_status} -> {status}")
        self.lifecycle_status = status
        if status == ModelLifecycleStatus.PRODUCTION:
            self.approved_by = actor_id
            self.approved_at = utcnow()
            self.deployed_at = utcnow()
        elif status == ModelLifecycleStatus.RETIRED:
            self.retired_at = utcnow()


# ============================================================
# SECTION 17 - MODEL PREDICTIONS AND EXPLANATIONS
# ============================================================

class ModelPrediction(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    QualityMixin,
    MetadataMixin,
):
    __tablename__ = "ml_model_predictions"
    __table_args__ = (
        Index("ix_pi_prediction_property_type_time", "property_id", "prediction_type", "predicted_at"),
        Index("ix_pi_prediction_model_time", "model_version_id", "predicted_at"),
        Index("ix_pi_prediction_profile_published", "profile_id", "is_published"),
        Index("ix_pi_prediction_request", "request_id"),
    )

    profile_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    property_id: Mapped[str] = mapped_column(GUID(), nullable=False, index=True)
    model_version_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("ml_model_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    feature_snapshot_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("property_feature_snapshots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    run_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    request_id: Mapped[Optional[str]] = mapped_column(String(180), nullable=True, index=True)
    prediction_type: Mapped[PredictionType] = enum_column(
        PredictionType,
        default=PredictionType.PROPERTY_VALUE,
    )
    predicted_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    numeric_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8), nullable=True)
    lower_bound: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8), nullable=True)
    upper_bound: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8), nullable=True)
    categorical_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    probability: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )
    output_payload: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    input_fingerprint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_shadow: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)

    profile: Mapped["PropertyIntelligenceProfile"] = relationship(back_populates="predictions")
    model_version: Mapped["MLModelVersion"] = relationship(back_populates="predictions")
    explanations: Mapped[list["PredictionExplanation"]] = relationship(
        back_populates="prediction",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reviews: Mapped[list["PredictionReview"]] = relationship(
        back_populates="prediction",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @validates("probability")
    def _validate_probability(self, key: str, value: Any) -> Optional[Decimal]:
        return bounded_decimal(value)

    def publish(self) -> None:
        self.is_published = True
        self.published_at = utcnow()


class PredictionExplanation(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "ml_prediction_explanations"
    __table_args__ = (
        Index("ix_pi_explanation_prediction_method", "prediction_id", "method"),
        Index("ix_pi_explanation_valuation", "valuation_id"),
    )

    prediction_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("ml_model_predictions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    valuation_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("property_valuations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    method: Mapped[ExplanationMethod] = enum_column(
        ExplanationMethod,
        default=ExplanationMethod.FEATURE_IMPORTANCE,
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    baseline_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8), nullable=True)
    explained_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8), nullable=True)
    feature_contributions: Mapped[list[Any]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
        default=list,
    )
    local_explanation: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    global_explanation: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    visualization_payload: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )

    prediction: Mapped[Optional["ModelPrediction"]] = relationship(back_populates="explanations")


class PredictionReview(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "ml_prediction_reviews"
    __table_args__ = (
        Index("ix_pi_review_prediction_decision", "prediction_id", "decision"),
        Index("ix_pi_review_reviewer", "reviewer_id", "reviewed_at"),
    )

    prediction_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("ml_model_predictions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision: Mapped[ReviewDecision] = enum_column(
        ReviewDecision,
        default=ReviewDecision.PENDING,
    )
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrected_numeric_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8), nullable=True)
    corrected_categorical_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    review_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(SCORE_PRECISION, SCORE_SCALE),
        nullable=True,
    )

    prediction: Mapped["ModelPrediction"] = relationship(back_populates="reviews")

    @validates("review_score")
    def _validate_review_score(self, key: str, value: Any) -> Optional[Decimal]:
        return bounded_decimal(value)

    def decide(
        self,
        decision: ReviewDecision,
        *,
        reviewer_id: str,
        reason: Optional[str] = None,
    ) -> None:
        if decision == ReviewDecision.PENDING:
            raise ValueError("a completed review cannot be reset to pending")
        self.decision = decision
        self.reviewer_id = reviewer_id
        self.reason = reason
        self.reviewed_at = utcnow()


# ============================================================
# SECTION 18 - MODEL MONITORING, OUTCOMES, AND DRIFT
# ============================================================

class PredictionOutcome(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    ProvenanceMixin,
    MetadataMixin,
):
    __tablename__ = "ml_prediction_outcomes"
    __table_args__ = (
        UniqueConstraint("prediction_id", "outcome_type", name="uq_pi_prediction_outcome_type"),
        Index("ix_pi_outcome_observed", "observed_at", "outcome_type"),
    )

    prediction_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("ml_model_predictions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    outcome_type: Mapped[PredictionType] = enum_column(
        PredictionType,
        default=PredictionType.PROPERTY_VALUE,
    )
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)
    actual_numeric_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8), nullable=True)
    actual_categorical_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    absolute_error: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8), nullable=True)
    percentage_error: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 10), nullable=True)
    squared_error: Mapped[Optional[Decimal]] = mapped_column(Numeric(30, 10), nullable=True)
    is_within_interval: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    outcome_payload: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )

    def calculate_errors(self, prediction_value: Optional[Decimal]) -> None:
        if prediction_value is None or self.actual_numeric_value is None:
            return
        difference = prediction_value - self.actual_numeric_value
        self.absolute_error = abs(difference)
        self.squared_error = difference * difference
        if self.actual_numeric_value != 0:
            self.percentage_error = abs(difference / self.actual_numeric_value)


class ModelMetricSnapshot(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "ml_model_metric_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "model_version_id",
            "window_start",
            "window_end",
            "segment_key",
            name="uq_pi_model_metric_window",
        ),
        Index("ix_pi_metric_model_window", "model_version_id", "window_end"),
    )

    model_version_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("ml_model_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    window_start: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    window_end: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    segment_key: Mapped[str] = mapped_column(String(255), nullable=False, default="all")
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metrics: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    thresholds: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    passed_quality_gate: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)


class ModelDriftReport(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "ml_model_drift_reports"
    __table_args__ = (
        Index("ix_pi_drift_model_type_time", "model_version_id", "drift_type", "detected_at"),
        Index("ix_pi_drift_severity_open", "severity", "is_resolved"),
    )

    model_version_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("ml_model_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    drift_type: Mapped[DriftType] = enum_column(
        DriftType,
        default=DriftType.DATA,
    )
    severity: Mapped[DriftSeverity] = enum_column(
        DriftSeverity,
        default=DriftSeverity.NORMAL,
    )
    detected_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utcnow)
    window_start: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    window_end: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    drift_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 10), nullable=True)
    threshold: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 10), nullable=True)
    affected_features: Mapped[list[Any]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
        default=list,
    )
    statistics: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict,
    )
    recommended_actions: Mapped[list[Any]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
        default=list,
    )
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ============================================================
# SECTION 19 - INTELLIGENCE NARRATIVES AND REPORTS
# ============================================================

class PropertyIntelligenceReport(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    VersionedMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "property_intelligence_reports"
    __table_args__ = (
        Index("ix_pi_report_property_created", "property_id", "created_at"),
        Index("ix_pi_report_profile_published", "profile_id", "is_published"),
    )

    profile_id: Mapped[str] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    property_id: Mapped[str] = mapped_column(GUID(), nullable=False, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(
        GUID(),
        ForeignKey("property_intelligence_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    report_type: Mapped[str] = mapped_column(String(120), nullable=False, default="property_intelligence")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    executive_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    valuation_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    market_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comparable_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    public_record_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sections: Mapped[list[Any]] = mapped_column(MutableList.as_mutable(JSON), nullable=False, default=list)
    citations: Mapped[list[Any]] = mapped_column(MutableList.as_mutable(JSON), nullable=False, default=list)
    generated_by_model: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)

    def refresh_hash(self) -> str:
        payload = {
            "executive_summary": self.executive_summary,
            "valuation_summary": self.valuation_summary,
            "market_summary": self.market_summary,
            "risk_summary": self.risk_summary,
            "comparable_summary": self.comparable_summary,
            "public_record_summary": self.public_record_summary,
            "sections": self.sections,
            "citations": self.citations,
        }
        self.content_hash = payload_sha256(payload)
        return self.content_hash


# ============================================================
# SECTION 20 - AUDIT EVENTS
# ============================================================

class PropertyIntelligenceAuditEvent(
    Base,
    UUIDPrimaryKeyMixin,
    TenantMixin,
    MetadataMixin,
):
    __tablename__ = "property_intelligence_audit_events"
    __table_args__ = (
        Index("ix_pi_audit_entity", "entity_type", "entity_id", "occurred_at"),
        Index("ix_pi_audit_property", "property_id", "occurred_at"),
        Index("ix_pi_audit_actor", "actor_id", "occurred_at"),
    )

    occurred_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )
    property_id: Mapped[Optional[str]] = mapped_column(GUID(), nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(80), nullable=False, default="system")
    actor_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    ip_address_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    before_state: Mapped[Optional[dict[str, Any]]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=True,
    )
    after_state: Mapped[Optional[dict[str, Any]]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=True,
    )
    change_summary: Mapped[list[Any]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
        default=list,
    )


# ============================================================
# SECTION 21 - DOMAIN SERVICE HELPERS
# ============================================================

class ValuationMath:
    """Pure helpers used by services and tests; no database session required."""

    @staticmethod
    def weighted_estimate(
        values_and_weights: Sequence[tuple[Decimal, Decimal]],
    ) -> Optional[Decimal]:
        valid = [
            (Decimal(str(value)), Decimal(str(weight)))
            for value, weight in values_and_weights
            if value is not None and weight is not None and Decimal(str(weight)) > 0
        ]
        if not valid:
            return None
        total_weight = sum(weight for _, weight in valid)
        estimate = sum(value * weight for value, weight in valid) / total_weight
        return decimal_or_none(estimate)

    @staticmethod
    def confidence_interval(
        estimate: Decimal,
        standard_error: Decimal,
        z_score: Decimal = Decimal("1.96"),
    ) -> tuple[Decimal, Decimal]:
        estimate = Decimal(str(estimate))
        margin = Decimal(str(standard_error)) * Decimal(str(z_score))
        return (
            decimal_or_none(max(estimate - margin, Decimal("0"))) or Decimal("0"),
            decimal_or_none(estimate + margin) or Decimal("0"),
        )

    @staticmethod
    def calculate_price_per_sqft(
        price: Optional[Decimal],
        living_area_sqft: Optional[Decimal],
    ) -> Optional[Decimal]:
        ratio = safe_ratio(price, living_area_sqft)
        return decimal_or_none(ratio) if ratio is not None else None

    @staticmethod
    def aggregate_risk(
        assessments: Iterable[PropertyRiskAssessment],
    ) -> Optional[Decimal]:
        scores: list[Decimal] = []
        weights = {
            RiskSeverity.INFO: Decimal("0.25"),
            RiskSeverity.LOW: Decimal("0.50"),
            RiskSeverity.MODERATE: Decimal("1.00"),
            RiskSeverity.HIGH: Decimal("1.50"),
            RiskSeverity.CRITICAL: Decimal("2.00"),
        }
        weighted_sum = Decimal("0")
        total_weight = Decimal("0")
        for assessment in assessments:
            if not assessment.is_active:
                continue
            score = Decimal(str(assessment.risk_score))
            weight = weights[assessment.severity]
            scores.append(score)
            weighted_sum += score * weight
            total_weight += weight
        if not scores or total_weight == 0:
            return None
        return bounded_decimal(weighted_sum / total_weight)


class FeaturePayloadBuilder:
    """Deterministic feature payload construction and validation helper."""

    @staticmethod
    def build(
        values: Mapping[str, Any],
        *,
        exclude_none: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for key in sorted(values):
            value = values[key]
            if exclude_none and value is None:
                continue
            if isinstance(value, Decimal):
                payload[key] = str(value)
            elif isinstance(value, (date, datetime)):
                payload[key] = value.isoformat()
            elif isinstance(value, enum.Enum):
                payload[key] = value.value
            else:
                payload[key] = value
        return payload

    @staticmethod
    def fingerprint(values: Mapping[str, Any]) -> str:
        return payload_sha256(FeaturePayloadBuilder.build(values))


# ============================================================
# SECTION 22 - AUTOMATIC CONSISTENCY EVENTS
# ============================================================

@event.listens_for(PropertyFeatureSnapshot, "before_insert")
@event.listens_for(PropertyFeatureSnapshot, "before_update")
def _refresh_feature_snapshot_metadata(mapper: Any, connection: Any, target: PropertyFeatureSnapshot) -> None:
    target.refresh_hash()
    target.missing_feature_count = sum(
        1 for value in target.feature_payload.values() if value is None
    )


@event.listens_for(PropertyIntelligenceReport, "before_insert")
@event.listens_for(PropertyIntelligenceReport, "before_update")
def _refresh_report_hash(mapper: Any, connection: Any, target: PropertyIntelligenceReport) -> None:
    target.refresh_hash()


@event.listens_for(PropertyObservation, "before_insert")
@event.listens_for(PropertyObservation, "before_update")
def _refresh_observation_hash(mapper: Any, connection: Any, target: PropertyObservation) -> None:
    if target.source_payload_hash:
        return
    payload = {
        "field_path": target.field_path,
        "value_type": target.value_type.value if target.value_type else None,
        "value": target.materialized_value(),
        "source_name": target.source_name,
        "source_record_id": target.source_record_id,
    }
    target.source_payload_hash = payload_sha256(payload)


@event.listens_for(PropertyValuation, "before_insert")
@event.listens_for(PropertyValuation, "before_update")
def _synchronize_valuation_fields(mapper: Any, connection: Any, target: PropertyValuation) -> None:
    if target.value_low is not None and target.value_high is not None:
        if target.value_low > target.value_high:
            raise ValueError("valuation value_low cannot exceed value_high")
    if target.price_per_sqft is None:
        living_area = target.metadata_json.get("living_area_sqft")
        if living_area:
            target.price_per_sqft = ValuationMath.calculate_price_per_sqft(
                target.estimated_value,
                Decimal(str(living_area)),
            )


# ============================================================
# SECTION 23 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    # Base and utilities
    "Base",
    "GUID",
    "UTCDateTime",
    "utcnow",
    "new_uuid",
    "decimal_or_none",
    "bounded_decimal",
    "payload_sha256",
    "ValuationMath",
    "FeaturePayloadBuilder",
    # Enums
    "RecordStatus",
    "IntelligenceRunStatus",
    "IntelligenceRunType",
    "PropertyType",
    "ListingStatus",
    "OccupancyStatus",
    "DataSourceType",
    "DataQualityStatus",
    "ObservationType",
    "ValuationMethod",
    "ValuationPurpose",
    "ComparableStatus",
    "AdjustmentType",
    "MarketGranularity",
    "MarketTrend",
    "MarketTemperature",
    "RiskCategory",
    "RiskSeverity",
    "FeatureValueType",
    "FeatureOrigin",
    "ModelLifecycleStatus",
    "ModelFramework",
    "PredictionType",
    "ExplanationMethod",
    "ReviewDecision",
    "DriftType",
    "DriftSeverity",
    "EntityResolutionStatus",
    # Persistence models
    "PropertyIntelligenceProfile",
    "PropertyIntelligenceRun",
    "IntelligenceDataSource",
    "PropertyObservation",
    "PropertyEntityResolution",
    "PropertyDataConflict",
    "PropertyValuation",
    "ValuationComparable",
    "ComparableAdjustment",
    "MarketArea",
    "MarketSnapshot",
    "PropertyMarketMembership",
    "PropertyRiskAssessment",
    "FeatureDefinition",
    "PropertyFeatureSnapshot",
    "PropertyFeatureValue",
    "MLModel",
    "MLModelVersion",
    "ModelPrediction",
    "PredictionExplanation",
    "PredictionReview",
    "PredictionOutcome",
    "ModelMetricSnapshot",
    "ModelDriftReport",
    "PropertyIntelligenceReport",
    "PropertyIntelligenceAuditEvent",
]
