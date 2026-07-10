"""
============================================================
AUSSEM REAL ESTATE
PHASE 5.40 - PROPERTY PROFILE ENGINE
FILE: app/property_intelligence/property_profile_engine.py

PURPOSE:
Enterprise property-profile orchestration, normalization, aggregation,
merging, scoring, feature construction, snapshot generation, lifecycle
management, and report-ready profile assembly for the Aussem Real Estate
property-intelligence platform.

DESIGN PRINCIPLES:
1. Build one canonical profile from heterogeneous property evidence.
2. Preserve provenance, confidence, conflicts, and freshness.
3. Avoid circular imports through dependency injection and duck typing.
4. Support deterministic batch and API workflows.
5. Keep business rules explicit, testable, and explainable.
6. Provide safe merge behavior for incomplete and conflicting records.
7. Support machine-learning feature extraction and future model serving.
8. Remain usable without external services or network access.
9. Produce stable fingerprints for idempotency and audit.
10. Integrate with models.py, address_intelligence.py,
    confidence_engine.py, and source_explanation_engine.py.
============================================================
"""

from __future__ import annotations

import enum
import hashlib
import json
import math
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Optional, Protocol, Sequence


# ============================================================
# SECTION 01 - NUMERIC CONTEXT AND CONSTANTS
# ============================================================

getcontext().prec = 34

ZERO = Decimal("0")
ONE = Decimal("1")
HALF = Decimal("0.5")
SCORE_QUANTUM = Decimal("0.000001")
MONEY_QUANTUM = Decimal("0.01")

DEFAULT_COUNTRY_CODE = "US"
DEFAULT_CURRENCY_CODE = "USD"
DEFAULT_PROFILE_VERSION = "1.0"
DEFAULT_COMPLETENESS_TARGET = Decimal("0.85")
DEFAULT_FRESHNESS_TARGET = Decimal("0.80")
DEFAULT_PROFILE_CONFIDENCE = Decimal("0.50")
DEFAULT_MAX_PROFILE_AGE_DAYS = 30
DEFAULT_HISTORY_LIMIT = 100
DEFAULT_CONFLICT_PENALTY = Decimal("0.20")


# ============================================================
# SECTION 02 - GENERIC HELPERS
# ============================================================

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_decimal(value: Any, default: Optional[Decimal] = None) -> Optional[Decimal]:
    if value is None or value == "":
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return default


def clamp_score(value: Any) -> Decimal:
    number = to_decimal(value, ZERO) or ZERO
    number = max(ZERO, min(ONE, number))
    return number.quantize(SCORE_QUANTUM, rounding=ROUND_HALF_UP)


def money(value: Any) -> Optional[Decimal]:
    number = to_decimal(value)
    if number is None:
        return None
    return number.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def normalize_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = " ".join(str(value).strip().split())
    return text or None


def normalize_code(value: Any) -> Optional[str]:
    text = normalize_text(value)
    return text.upper() if text else None


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def weighted_mean(
    values: Iterable[tuple[Any, Any]],
    *,
    default: Decimal = DEFAULT_PROFILE_CONFIDENCE,
) -> Decimal:
    numerator = ZERO
    denominator = ZERO
    for value, weight in values:
        number = to_decimal(value)
        factor = to_decimal(weight)
        if number is None or factor is None or factor <= ZERO:
            continue
        numerator += number * factor
        denominator += factor
    if denominator == ZERO:
        return clamp_score(default)
    return clamp_score(numerator / denominator)


def safe_ratio(numerator: Any, denominator: Any) -> Optional[Decimal]:
    num = to_decimal(numerator)
    den = to_decimal(denominator)
    if num is None or den in (None, ZERO):
        return None
    return num / den


def serialize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [serialize_value(item) for item in value]
    return value


def get_attr_or_key(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


# ============================================================
# SECTION 03 - ENUMERATIONS
# ============================================================

class StringEnum(str, enum.Enum):
    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]


class ProfileStatus(StringEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PARTIAL = "partial"
    CONFLICTED = "conflicted"
    STALE = "stale"
    ARCHIVED = "archived"
    INVALID = "invalid"


class ProfileBuildMode(StringEnum):
    CREATE = "create"
    REFRESH = "refresh"
    MERGE = "merge"
    REPAIR = "repair"
    REPLAY = "replay"


class ProfileSection(StringEnum):
    IDENTITY = "identity"
    ADDRESS = "address"
    STRUCTURE = "structure"
    OWNERSHIP = "ownership"
    LISTING = "listing"
    SALES = "sales"
    TAX = "tax"
    VALUATION = "valuation"
    MARKET = "market"
    RISK = "risk"
    FEATURES = "features"
    SOURCES = "sources"
    EXPLANATION = "explanation"


class FieldDecision(StringEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    CONFLICTED = "conflicted"
    PRESERVED = "preserved"
    CLEARED = "cleared"


class MergeStrategy(StringEnum):
    PREFER_HIGHER_CONFIDENCE = "prefer_higher_confidence"
    PREFER_NEWER = "prefer_newer"
    PREFER_AUTHORITATIVE = "prefer_authoritative"
    PREFER_EXISTING = "prefer_existing"
    PREFER_INCOMING = "prefer_incoming"
    NON_NULL = "non_null"
    MANUAL = "manual"


class ProfileQualityLevel(StringEnum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"


class RefreshReason(StringEnum):
    EXPIRED = "expired"
    SOURCE_UPDATE = "source_update"
    USER_REQUEST = "user_request"
    MODEL_UPDATE = "model_update"
    CONFLICT_REPAIR = "conflict_repair"
    MISSING_DATA = "missing_data"
    SCHEDULED = "scheduled"
    OTHER = "other"


class ChangeType(StringEnum):
    CREATED = "created"
    UPDATED = "updated"
    REMOVED = "removed"
    CONFLICTED = "conflicted"
    RESOLVED = "resolved"
    UNCHANGED = "unchanged"


# ============================================================
# SECTION 04 - CORE DATA CONTRACTS
# ============================================================

@dataclass(slots=True)
class FieldEvidence:
    field_path: str
    value: Any
    source_name: str
    source_id: Optional[str] = None
    confidence: Decimal = DEFAULT_PROFILE_CONFIDENCE
    quality: Decimal = DEFAULT_PROFILE_CONFIDENCE
    freshness: Decimal = DEFAULT_PROFILE_CONFIDENCE
    authority: Decimal = DEFAULT_PROFILE_CONFIDENCE
    observed_at: Optional[datetime] = None
    retrieved_at: Optional[datetime] = None
    effective_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def composite_score(self) -> Decimal:
        return weighted_mean(
            (
                (self.confidence, Decimal("0.35")),
                (self.quality, Decimal("0.25")),
                (self.freshness, Decimal("0.20")),
                (self.authority, Decimal("0.20")),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_path": self.field_path,
            "value": serialize_value(self.value),
            "source_name": self.source_name,
            "source_id": self.source_id,
            "confidence": str(clamp_score(self.confidence)),
            "quality": str(clamp_score(self.quality)),
            "freshness": str(clamp_score(self.freshness)),
            "authority": str(clamp_score(self.authority)),
            "composite_score": str(self.composite_score),
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "retrieved_at": self.retrieved_at.isoformat() if self.retrieved_at else None,
            "effective_at": self.effective_at.isoformat() if self.effective_at else None,
            "metadata": serialize_value(self.metadata),
        }


@dataclass(slots=True)
class FieldResolution:
    field_path: str
    selected_value: Any
    selected_source_name: Optional[str]
    selected_source_id: Optional[str]
    confidence: Decimal
    decision: FieldDecision
    candidates: list[FieldEvidence]
    reason: str
    conflict_score: Decimal = ZERO
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_path": self.field_path,
            "selected_value": serialize_value(self.selected_value),
            "selected_source_name": self.selected_source_name,
            "selected_source_id": self.selected_source_id,
            "confidence": str(clamp_score(self.confidence)),
            "decision": self.decision.value,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "reason": self.reason,
            "conflict_score": str(clamp_score(self.conflict_score)),
            "metadata": serialize_value(self.metadata),
        }


@dataclass(slots=True)
class PropertyIdentity:
    property_id: str
    external_ids: dict[str, str] = field(default_factory=dict)
    parcel_number: Optional[str] = None
    tax_account_number: Optional[str] = None
    canonical_key: Optional[str] = None
    fingerprint: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return serialize_value(asdict(self))


@dataclass(slots=True)
class AddressProfile:
    canonical_address: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    state_code: Optional[str] = None
    postal_code: Optional[str] = None
    country_code: str = DEFAULT_COUNTRY_CODE
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    address_confidence: Decimal = DEFAULT_PROFILE_CONFIDENCE
    address_fingerprint: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return serialize_value(asdict(self))


@dataclass(slots=True)
class StructuralProfile:
    property_type: Optional[str] = None
    bedrooms: Optional[Decimal] = None
    bathrooms: Optional[Decimal] = None
    living_area_sqft: Optional[Decimal] = None
    lot_size_sqft: Optional[Decimal] = None
    year_built: Optional[int] = None
    stories: Optional[Decimal] = None
    garage_spaces: Optional[Decimal] = None
    basement_type: Optional[str] = None
    condition: Optional[str] = None
    quality_grade: Optional[str] = None
    construction_type: Optional[str] = None
    roof_type: Optional[str] = None
    heating_type: Optional[str] = None
    cooling_type: Optional[str] = None
    features: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return serialize_value(asdict(self))


@dataclass(slots=True)
class OwnershipProfile:
    owner_names: list[str] = field(default_factory=list)
    ownership_type: Optional[str] = None
    owner_occupied: Optional[bool] = None
    mailing_address: Optional[str] = None
    deed_date: Optional[date] = None
    deed_book: Optional[str] = None
    deed_page: Optional[str] = None
    transfer_type: Optional[str] = None
    ownership_confidence: Decimal = DEFAULT_PROFILE_CONFIDENCE

    def to_dict(self) -> dict[str, Any]:
        return serialize_value(asdict(self))


@dataclass(slots=True)
class ListingProfile:
    listing_status: Optional[str] = None
    list_price: Optional[Decimal] = None
    original_list_price: Optional[Decimal] = None
    listing_date: Optional[date] = None
    pending_date: Optional[date] = None
    expiration_date: Optional[date] = None
    days_on_market: Optional[int] = None
    cumulative_days_on_market: Optional[int] = None
    mls_number: Optional[str] = None
    brokerage_name: Optional[str] = None
    agent_name: Optional[str] = None
    remarks: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return serialize_value(asdict(self))


@dataclass(slots=True)
class SaleRecord:
    sale_date: Optional[date]
    sale_price: Optional[Decimal]
    document_id: Optional[str] = None
    buyer_names: list[str] = field(default_factory=list)
    seller_names: list[str] = field(default_factory=list)
    transaction_type: Optional[str] = None
    arms_length: Optional[bool] = None
    source_name: Optional[str] = None
    confidence: Decimal = DEFAULT_PROFILE_CONFIDENCE

    def to_dict(self) -> dict[str, Any]:
        return serialize_value(asdict(self))


@dataclass(slots=True)
class TaxProfile:
    assessed_value: Optional[Decimal] = None
    land_value: Optional[Decimal] = None
    improvement_value: Optional[Decimal] = None
    annual_tax_amount: Optional[Decimal] = None
    tax_year: Optional[int] = None
    assessment_ratio: Optional[Decimal] = None
    exemption_amount: Optional[Decimal] = None
    delinquent: Optional[bool] = None
    tax_rate: Optional[Decimal] = None

    def to_dict(self) -> dict[str, Any]:
        return serialize_value(asdict(self))


@dataclass(slots=True)
class ValuationProfile:
    estimated_value: Optional[Decimal] = None
    value_low: Optional[Decimal] = None
    value_high: Optional[Decimal] = None
    price_per_sqft: Optional[Decimal] = None
    valuation_date: Optional[datetime] = None
    method: Optional[str] = None
    model_version: Optional[str] = None
    confidence: Decimal = DEFAULT_PROFILE_CONFIDENCE
    comparable_count: int = 0
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return serialize_value(asdict(self))


@dataclass(slots=True)
class MarketProfile:
    market_area_id: Optional[str] = None
    market_name: Optional[str] = None
    market_temperature: Optional[str] = None
    market_trend: Optional[str] = None
    median_sale_price: Optional[Decimal] = None
    median_price_per_sqft: Optional[Decimal] = None
    median_days_on_market: Optional[Decimal] = None
    months_of_supply: Optional[Decimal] = None
    year_over_year_appreciation: Optional[Decimal] = None
    sale_to_list_ratio: Optional[Decimal] = None
    as_of_date: Optional[date] = None
    confidence: Decimal = DEFAULT_PROFILE_CONFIDENCE

    def to_dict(self) -> dict[str, Any]:
        return serialize_value(asdict(self))


@dataclass(slots=True)
class RiskItem:
    category: str
    severity: str
    score: Decimal
    title: str
    summary: Optional[str] = None
    evidence: list[Any] = field(default_factory=list)
    mitigations: list[Any] = field(default_factory=list)
    confidence: Decimal = DEFAULT_PROFILE_CONFIDENCE
    expires_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return serialize_value(asdict(self))


@dataclass(slots=True)
class ProfileQuality:
    completeness_score: Decimal
    freshness_score: Decimal
    confidence_score: Decimal
    consistency_score: Decimal
    source_diversity_score: Decimal
    overall_score: Decimal
    level: ProfileQualityLevel
    missing_fields: list[str] = field(default_factory=list)
    stale_fields: list[str] = field(default_factory=list)
    conflicted_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "completeness_score": str(self.completeness_score),
            "freshness_score": str(self.freshness_score),
            "confidence_score": str(self.confidence_score),
            "consistency_score": str(self.consistency_score),
            "source_diversity_score": str(self.source_diversity_score),
            "overall_score": str(self.overall_score),
            "level": self.level.value,
            "missing_fields": list(self.missing_fields),
            "stale_fields": list(self.stale_fields),
            "conflicted_fields": list(self.conflicted_fields),
            "warnings": list(self.warnings),
        }


@dataclass(slots=True)
class PropertyProfile:
    identity: PropertyIdentity
    address: AddressProfile = field(default_factory=AddressProfile)
    structure: StructuralProfile = field(default_factory=StructuralProfile)
    ownership: OwnershipProfile = field(default_factory=OwnershipProfile)
    listing: ListingProfile = field(default_factory=ListingProfile)
    sales_history: list[SaleRecord] = field(default_factory=list)
    tax: TaxProfile = field(default_factory=TaxProfile)
    valuation: ValuationProfile = field(default_factory=ValuationProfile)
    market: MarketProfile = field(default_factory=MarketProfile)
    risks: list[RiskItem] = field(default_factory=list)
    resolutions: dict[str, FieldResolution] = field(default_factory=dict)
    quality: Optional[ProfileQuality] = None
    status: ProfileStatus = ProfileStatus.DRAFT
    profile_version: str = DEFAULT_PROFILE_VERSION
    built_at: datetime = field(default_factory=utcnow)
    refreshed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    fingerprint: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "address": self.address.to_dict(),
            "structure": self.structure.to_dict(),
            "ownership": self.ownership.to_dict(),
            "listing": self.listing.to_dict(),
            "sales_history": [record.to_dict() for record in self.sales_history],
            "tax": self.tax.to_dict(),
            "valuation": self.valuation.to_dict(),
            "market": self.market.to_dict(),
            "risks": [risk.to_dict() for risk in self.risks],
            "resolutions": {
                path: resolution.to_dict()
                for path, resolution in self.resolutions.items()
            },
            "quality": self.quality.to_dict() if self.quality else None,
            "status": self.status.value,
            "profile_version": self.profile_version,
            "built_at": self.built_at.isoformat(),
            "refreshed_at": self.refreshed_at.isoformat() if self.refreshed_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "fingerprint": self.fingerprint,
            "metadata": serialize_value(self.metadata),
        }


@dataclass(slots=True)
class ProfileChange:
    field_path: str
    change_type: ChangeType
    old_value: Any
    new_value: Any
    reason: str
    confidence: Decimal = DEFAULT_PROFILE_CONFIDENCE

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_path": self.field_path,
            "change_type": self.change_type.value,
            "old_value": serialize_value(self.old_value),
            "new_value": serialize_value(self.new_value),
            "reason": self.reason,
            "confidence": str(clamp_score(self.confidence)),
        }


@dataclass(slots=True)
class ProfileBuildResult:
    profile: PropertyProfile
    mode: ProfileBuildMode
    changes: list[ProfileChange]
    warnings: list[str]
    errors: list[str]
    source_count: int
    evidence_count: int
    conflict_count: int
    duration_ms: int
    fingerprint: str

    @property
    def succeeded(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile.to_dict(),
            "mode": self.mode.value,
            "changes": [change.to_dict() for change in self.changes],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "source_count": self.source_count,
            "evidence_count": self.evidence_count,
            "conflict_count": self.conflict_count,
            "duration_ms": self.duration_ms,
            "fingerprint": self.fingerprint,
            "succeeded": self.succeeded,
        }


# ============================================================
# SECTION 05 - FIELD CONFIGURATION
# ============================================================

@dataclass(slots=True)
class FieldRule:
    field_path: str
    required: bool = False
    weight: Decimal = ONE
    strategy: MergeStrategy = MergeStrategy.PREFER_HIGHER_CONFIDENCE
    maximum_age_days: Optional[int] = None
    conflict_tolerance: Decimal = Decimal("0.02")
    allow_clear: bool = False
    validator: Optional[Callable[[Any], bool]] = None
    normalizer: Optional[Callable[[Any], Any]] = None
    metadata: dict[str, Any] = field(default_factory=dict)


DEFAULT_FIELD_RULES: tuple[FieldRule, ...] = (
    FieldRule("address.canonical_address", required=True, weight=Decimal("1.5"), maximum_age_days=3650),
    FieldRule("address.city", required=True, weight=Decimal("1.0"), maximum_age_days=3650),
    FieldRule("address.state_code", required=True, weight=Decimal("1.0"), maximum_age_days=3650),
    FieldRule("address.postal_code", required=True, weight=Decimal("1.0"), maximum_age_days=3650),
    FieldRule("identity.parcel_number", required=False, weight=Decimal("1.2"), maximum_age_days=3650),
    FieldRule("structure.property_type", required=True, weight=Decimal("1.0"), maximum_age_days=3650),
    FieldRule("structure.bedrooms", required=False, weight=Decimal("0.8"), maximum_age_days=1825),
    FieldRule("structure.bathrooms", required=False, weight=Decimal("0.8"), maximum_age_days=1825),
    FieldRule("structure.living_area_sqft", required=True, weight=Decimal("1.2"), maximum_age_days=1825),
    FieldRule("structure.lot_size_sqft", required=False, weight=Decimal("0.8"), maximum_age_days=1825),
    FieldRule("structure.year_built", required=False, weight=Decimal("0.7"), maximum_age_days=3650),
    FieldRule("listing.listing_status", required=False, weight=Decimal("0.8"), maximum_age_days=30),
    FieldRule("listing.list_price", required=False, weight=Decimal("1.0"), maximum_age_days=30),
    FieldRule("tax.assessed_value", required=False, weight=Decimal("0.8"), maximum_age_days=730),
    FieldRule("valuation.estimated_value", required=False, weight=Decimal("1.2"), maximum_age_days=180),
    FieldRule("market.median_sale_price", required=False, weight=Decimal("0.6"), maximum_age_days=90),
)


class FieldRuleRegistry:
    def __init__(self, rules: Optional[Iterable[FieldRule]] = None) -> None:
        self._rules = {
            rule.field_path: rule
            for rule in (rules or DEFAULT_FIELD_RULES)
        }

    def get(self, field_path: str) -> FieldRule:
        return self._rules.get(field_path, FieldRule(field_path=field_path))

    def all(self) -> list[FieldRule]:
        return list(self._rules.values())


# ============================================================
# SECTION 06 - VALUE NORMALIZATION
# ============================================================

class ProfileValueNormalizer:
    MONEY_FIELDS = {
        "listing.list_price",
        "listing.original_list_price",
        "tax.assessed_value",
        "tax.land_value",
        "tax.improvement_value",
        "tax.annual_tax_amount",
        "valuation.estimated_value",
        "valuation.value_low",
        "valuation.value_high",
        "valuation.price_per_sqft",
        "market.median_sale_price",
        "market.median_price_per_sqft",
    }

    DECIMAL_FIELDS = {
        "structure.bedrooms",
        "structure.bathrooms",
        "structure.living_area_sqft",
        "structure.lot_size_sqft",
        "structure.stories",
        "structure.garage_spaces",
        "tax.assessment_ratio",
        "tax.tax_rate",
        "market.median_days_on_market",
        "market.months_of_supply",
        "market.year_over_year_appreciation",
        "market.sale_to_list_ratio",
    }

    CODE_FIELDS = {
        "address.state_code",
        "address.country_code",
    }

    TEXT_FIELDS = {
        "address.canonical_address",
        "address.address_line_1",
        "address.address_line_2",
        "address.city",
        "address.county",
        "address.postal_code",
        "identity.parcel_number",
        "identity.tax_account_number",
        "structure.property_type",
        "listing.listing_status",
        "listing.mls_number",
    }

    def normalize(self, field_path: str, value: Any) -> Any:
        if value is None:
            return None
        if field_path in self.MONEY_FIELDS:
            return money(value)
        if field_path in self.DECIMAL_FIELDS:
            return to_decimal(value)
        if field_path in self.CODE_FIELDS:
            return normalize_code(value)
        if field_path in self.TEXT_FIELDS:
            return normalize_text(value)
        if field_path.endswith("_date") and isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                return value
        return value


# ============================================================
# SECTION 07 - CONFLICT AND FIELD RESOLUTION
# ============================================================

class FieldResolver:
    def __init__(
        self,
        *,
        rules: Optional[FieldRuleRegistry] = None,
        normalizer: Optional[ProfileValueNormalizer] = None,
    ) -> None:
        self.rules = rules or FieldRuleRegistry()
        self.normalizer = normalizer or ProfileValueNormalizer()

    def resolve(
        self,
        field_path: str,
        candidates: Sequence[FieldEvidence],
        *,
        existing_value: Any = None,
    ) -> FieldResolution:
        rule = self.rules.get(field_path)
        normalized = [
            FieldEvidence(
                field_path=item.field_path,
                value=self.normalizer.normalize(field_path, item.value),
                source_name=item.source_name,
                source_id=item.source_id,
                confidence=clamp_score(item.confidence),
                quality=clamp_score(item.quality),
                freshness=clamp_score(item.freshness),
                authority=clamp_score(item.authority),
                observed_at=item.observed_at,
                retrieved_at=item.retrieved_at,
                effective_at=item.effective_at,
                metadata=dict(item.metadata),
            )
            for item in candidates
            if item.value is not None
        ]

        if not normalized:
            if existing_value is not None:
                return FieldResolution(
                    field_path=field_path,
                    selected_value=existing_value,
                    selected_source_name=None,
                    selected_source_id=None,
                    confidence=DEFAULT_PROFILE_CONFIDENCE,
                    decision=FieldDecision.PRESERVED,
                    candidates=[],
                    reason="No incoming evidence was available; existing value was preserved.",
                )
            return FieldResolution(
                field_path=field_path,
                selected_value=None,
                selected_source_name=None,
                selected_source_id=None,
                confidence=ZERO,
                decision=FieldDecision.DEFERRED,
                candidates=[],
                reason="No usable evidence was available.",
            )

        conflict_score = self._conflict_score(normalized, rule.conflict_tolerance)
        selected = self._select_candidate(
            normalized,
            strategy=rule.strategy,
            existing_value=existing_value,
        )

        decision = (
            FieldDecision.CONFLICTED
            if conflict_score > rule.conflict_tolerance
            else FieldDecision.ACCEPTED
        )

        confidence = clamp_score(
            selected.composite_score
            - conflict_score * DEFAULT_CONFLICT_PENALTY
        )

        return FieldResolution(
            field_path=field_path,
            selected_value=selected.value,
            selected_source_name=selected.source_name,
            selected_source_id=selected.source_id,
            confidence=confidence,
            decision=decision,
            candidates=list(normalized),
            reason=self._reason(
                rule.strategy,
                selected,
                conflict_score,
            ),
            conflict_score=conflict_score,
        )

    def _select_candidate(
        self,
        candidates: Sequence[FieldEvidence],
        *,
        strategy: MergeStrategy,
        existing_value: Any,
    ) -> FieldEvidence:
        if strategy == MergeStrategy.PREFER_EXISTING and existing_value is not None:
            return FieldEvidence(
                field_path=candidates[0].field_path,
                value=existing_value,
                source_name="existing_profile",
                confidence=DEFAULT_PROFILE_CONFIDENCE,
                quality=DEFAULT_PROFILE_CONFIDENCE,
                freshness=DEFAULT_PROFILE_CONFIDENCE,
                authority=DEFAULT_PROFILE_CONFIDENCE,
            )

        if strategy == MergeStrategy.PREFER_NEWER:
            return max(
                candidates,
                key=lambda item: (
                    item.effective_at
                    or item.observed_at
                    or item.retrieved_at
                    or datetime.min.replace(tzinfo=timezone.utc)
                ),
            )

        if strategy == MergeStrategy.PREFER_AUTHORITATIVE:
            return max(
                candidates,
                key=lambda item: (
                    item.authority,
                    item.quality,
                    item.confidence,
                    item.freshness,
                ),
            )

        if strategy == MergeStrategy.PREFER_INCOMING:
            return candidates[-1]

        if strategy == MergeStrategy.NON_NULL:
            return max(candidates, key=lambda item: item.composite_score)

        return max(
            candidates,
            key=lambda item: (
                item.composite_score,
                item.authority,
                item.freshness,
            ),
        )

    @staticmethod
    def _conflict_score(
        candidates: Sequence[FieldEvidence],
        tolerance: Decimal,
    ) -> Decimal:
        if len(candidates) < 2:
            return ZERO

        maximum = ZERO
        for index, left in enumerate(candidates):
            for right in candidates[index + 1:]:
                disagreement = FieldResolver._value_disagreement(
                    left.value,
                    right.value,
                )
                if disagreement > tolerance:
                    maximum = max(maximum, disagreement)
        return clamp_score(maximum)

    @staticmethod
    def _value_disagreement(left: Any, right: Any) -> Decimal:
        if left == right:
            return ZERO

        left_number = to_decimal(left)
        right_number = to_decimal(right)
        if left_number is not None and right_number is not None:
            denominator = max(abs(left_number), abs(right_number), ONE)
            return clamp_score(abs(left_number - right_number) / denominator)

        left_text = (normalize_text(left) or "").upper()
        right_text = (normalize_text(right) or "").upper()
        if left_text == right_text:
            return ZERO

        left_tokens = set(left_text.split())
        right_tokens = set(right_text.split())
        union = left_tokens | right_tokens
        if not union:
            return ZERO
        similarity = Decimal(len(left_tokens & right_tokens)) / Decimal(len(union))
        return clamp_score(ONE - similarity)

    @staticmethod
    def _reason(
        strategy: MergeStrategy,
        selected: FieldEvidence,
        conflict_score: Decimal,
    ) -> str:
        if conflict_score > ZERO:
            return (
                f"Selected {selected.source_name} using {strategy.value}; "
                f"candidate disagreement score was {conflict_score}."
            )
        return (
            f"Selected {selected.source_name} using {strategy.value} "
            "with no material conflict."
        )


# ============================================================
# SECTION 08 - PROFILE QUALITY SCORING
# ============================================================

class ProfileQualityScorer:
    def __init__(
        self,
        *,
        rules: Optional[FieldRuleRegistry] = None,
    ) -> None:
        self.rules = rules or FieldRuleRegistry()

    def score(
        self,
        profile: PropertyProfile,
        *,
        as_of: Optional[datetime] = None,
    ) -> ProfileQuality:
        now = as_of or utcnow()
        weighted_present = ZERO
        weighted_total = ZERO
        freshness_values: list[tuple[Decimal, Decimal]] = []
        confidence_values: list[tuple[Decimal, Decimal]] = []
        conflicted_fields: list[str] = []
        missing_fields: list[str] = []
        stale_fields: list[str] = []
        source_names: set[str] = set()

        for rule in self.rules.all():
            weighted_total += rule.weight
            value = self._get_profile_value(profile, rule.field_path)
            resolution = profile.resolutions.get(rule.field_path)

            if value is None:
                if rule.required:
                    missing_fields.append(rule.field_path)
                continue

            weighted_present += rule.weight

            confidence = (
                resolution.confidence
                if resolution is not None
                else DEFAULT_PROFILE_CONFIDENCE
            )
            confidence_values.append((confidence, rule.weight))

            if resolution is not None:
                if resolution.decision == FieldDecision.CONFLICTED:
                    conflicted_fields.append(rule.field_path)
                if resolution.selected_source_name:
                    source_names.add(resolution.selected_source_name)

                latest = self._latest_evidence_time(resolution.candidates)
                if latest and rule.maximum_age_days is not None:
                    age = now - latest
                    if age > timedelta(days=rule.maximum_age_days):
                        stale_fields.append(rule.field_path)
                        freshness_values.append((ZERO, rule.weight))
                    else:
                        ratio = Decimal(age.total_seconds()) / Decimal(
                            rule.maximum_age_days * 86400
                        )
                        freshness_values.append(
                            (clamp_score(ONE - ratio), rule.weight)
                        )
                else:
                    freshness_values.append(
                        (DEFAULT_PROFILE_CONFIDENCE, rule.weight)
                    )
            else:
                freshness_values.append(
                    (DEFAULT_PROFILE_CONFIDENCE, rule.weight)
                )

        completeness = (
            clamp_score(weighted_present / weighted_total)
            if weighted_total > ZERO
            else ZERO
        )
        freshness = weighted_mean(
            freshness_values,
            default=DEFAULT_PROFILE_CONFIDENCE,
        )
        confidence = weighted_mean(
            confidence_values,
            default=DEFAULT_PROFILE_CONFIDENCE,
        )
        consistency = clamp_score(
            ONE
            - (
                Decimal(len(conflicted_fields))
                / Decimal(max(len(self.rules.all()), 1))
            )
        )
        diversity = clamp_score(
            Decimal(str(math.log1p(len(source_names))))
            / Decimal(str(math.log1p(8)))
        )

        overall = weighted_mean(
            (
                (completeness, Decimal("0.30")),
                (freshness, Decimal("0.20")),
                (confidence, Decimal("0.25")),
                (consistency, Decimal("0.15")),
                (diversity, Decimal("0.10")),
            )
        )

        warnings: list[str] = []
        if missing_fields:
            warnings.append("Required property-profile fields are missing.")
        if stale_fields:
            warnings.append("One or more profile fields are stale.")
        if conflicted_fields:
            warnings.append("One or more profile fields contain unresolved conflicts.")

        return ProfileQuality(
            completeness_score=completeness,
            freshness_score=freshness,
            confidence_score=confidence,
            consistency_score=consistency,
            source_diversity_score=diversity,
            overall_score=overall,
            level=self._level(overall, missing_fields),
            missing_fields=missing_fields,
            stale_fields=stale_fields,
            conflicted_fields=conflicted_fields,
            warnings=warnings,
        )

    @staticmethod
    def _get_profile_value(profile: PropertyProfile, field_path: str) -> Any:
        current: Any = profile
        for segment in field_path.split("."):
            if current is None:
                return None
            current = get_attr_or_key(current, segment)
        return current

    @staticmethod
    def _latest_evidence_time(
        candidates: Sequence[FieldEvidence],
    ) -> Optional[datetime]:
        times = [
            item.effective_at or item.observed_at or item.retrieved_at
            for item in candidates
            if item.effective_at or item.observed_at or item.retrieved_at
        ]
        return max(times) if times else None

    @staticmethod
    def _level(
        overall: Decimal,
        missing_fields: Sequence[str],
    ) -> ProfileQualityLevel:
        if missing_fields and overall < Decimal("0.40"):
            return ProfileQualityLevel.INVALID
        if overall >= Decimal("0.90"):
            return ProfileQualityLevel.EXCELLENT
        if overall >= Decimal("0.75"):
            return ProfileQualityLevel.GOOD
        if overall >= Decimal("0.55"):
            return ProfileQualityLevel.FAIR
        if overall > ZERO:
            return ProfileQualityLevel.POOR
        return ProfileQualityLevel.INVALID


# ============================================================
# SECTION 09 - PROFILE CHANGE DETECTION
# ============================================================

class ProfileChangeDetector:
    def compare(
        self,
        old_profile: Optional[PropertyProfile],
        new_profile: PropertyProfile,
    ) -> list[ProfileChange]:
        if old_profile is None:
            return [
                ProfileChange(
                    field_path="profile",
                    change_type=ChangeType.CREATED,
                    old_value=None,
                    new_value=new_profile.to_dict(),
                    reason="A new property profile was created.",
                    confidence=(
                        new_profile.quality.confidence_score
                        if new_profile.quality
                        else DEFAULT_PROFILE_CONFIDENCE
                    ),
                )
            ]

        old_flat = self._flatten(old_profile.to_dict())
        new_flat = self._flatten(new_profile.to_dict())
        ignored = {
            "built_at",
            "refreshed_at",
            "expires_at",
            "fingerprint",
        }

        changes: list[ProfileChange] = []
        for field_path in sorted(set(old_flat) | set(new_flat)):
            if any(field_path.endswith(item) for item in ignored):
                continue

            old_value = old_flat.get(field_path)
            new_value = new_flat.get(field_path)

            if old_value == new_value:
                continue

            if old_value is None and new_value is not None:
                change_type = ChangeType.CREATED
            elif old_value is not None and new_value is None:
                change_type = ChangeType.REMOVED
            else:
                change_type = ChangeType.UPDATED

            changes.append(
                ProfileChange(
                    field_path=field_path,
                    change_type=change_type,
                    old_value=old_value,
                    new_value=new_value,
                    reason=f"Profile field {field_path} changed.",
                )
            )

        return changes

    def _flatten(
        self,
        value: Any,
        *,
        prefix: str = "",
    ) -> dict[str, Any]:
        output: dict[str, Any] = {}

        if isinstance(value, Mapping):
            for key, item in value.items():
                path = f"{prefix}.{key}" if prefix else str(key)
                output.update(self._flatten(item, prefix=path))
            return output

        if isinstance(value, list):
            output[prefix] = value
            return output

        output[prefix] = value
        return output


# ============================================================
# SECTION 10 - PROFILE FEATURE EXTRACTION
# ============================================================

class PropertyProfileFeatureExtractor:
    def extract(self, profile: PropertyProfile) -> dict[str, Any]:
        current_year = date.today().year
        features: dict[str, Any] = {
            "property_type": profile.structure.property_type,
            "bedrooms": serialize_value(profile.structure.bedrooms),
            "bathrooms": serialize_value(profile.structure.bathrooms),
            "living_area_sqft": serialize_value(profile.structure.living_area_sqft),
            "lot_size_sqft": serialize_value(profile.structure.lot_size_sqft),
            "year_built": profile.structure.year_built,
            "property_age_years": (
                max(current_year - profile.structure.year_built, 0)
                if profile.structure.year_built
                else None
            ),
            "garage_spaces": serialize_value(profile.structure.garage_spaces),
            "has_basement": bool(profile.structure.basement_type),
            "listing_status": profile.listing.listing_status,
            "list_price": serialize_value(profile.listing.list_price),
            "assessed_value": serialize_value(profile.tax.assessed_value),
            "annual_tax_amount": serialize_value(profile.tax.annual_tax_amount),
            "estimated_value": serialize_value(profile.valuation.estimated_value),
            "valuation_confidence": str(profile.valuation.confidence),
            "market_temperature": profile.market.market_temperature,
            "market_trend": profile.market.market_trend,
            "median_sale_price": serialize_value(profile.market.median_sale_price),
            "months_of_supply": serialize_value(profile.market.months_of_supply),
            "overall_risk_score": str(self._overall_risk(profile.risks)),
            "risk_count": len(profile.risks),
            "profile_completeness": (
                str(profile.quality.completeness_score)
                if profile.quality
                else None
            ),
            "profile_confidence": (
                str(profile.quality.confidence_score)
                if profile.quality
                else None
            ),
            "profile_quality_score": (
                str(profile.quality.overall_score)
                if profile.quality
                else None
            ),
            "source_count": len(
                {
                    resolution.selected_source_name
                    for resolution in profile.resolutions.values()
                    if resolution.selected_source_name
                }
            ),
            "conflicted_field_count": (
                len(profile.quality.conflicted_fields)
                if profile.quality
                else 0
            ),
        }

        price_per_sqft = safe_ratio(
            profile.valuation.estimated_value,
            profile.structure.living_area_sqft,
        )
        features["estimated_price_per_sqft"] = (
            str(price_per_sqft) if price_per_sqft is not None else None
        )

        tax_to_value = safe_ratio(
            profile.tax.annual_tax_amount,
            profile.valuation.estimated_value,
        )
        features["tax_to_value_ratio"] = (
            str(tax_to_value) if tax_to_value is not None else None
        )

        list_to_value = safe_ratio(
            profile.listing.list_price,
            profile.valuation.estimated_value,
        )
        features["list_to_estimated_value_ratio"] = (
            str(list_to_value) if list_to_value is not None else None
        )

        return features

    @staticmethod
    def _overall_risk(risks: Sequence[RiskItem]) -> Decimal:
        active_scores = [
            risk.score
            for risk in risks
            if risk.expires_at is None or risk.expires_at > utcnow()
        ]
        if not active_scores:
            return ZERO
        return clamp_score(sum(active_scores, ZERO) / Decimal(len(active_scores)))


# ============================================================
# SECTION 11 - PROFILE REFRESH POLICY
# ============================================================

@dataclass(slots=True)
class ProfileRefreshPolicy:
    maximum_profile_age_days: int = DEFAULT_MAX_PROFILE_AGE_DAYS
    minimum_completeness: Decimal = DEFAULT_COMPLETENESS_TARGET
    minimum_freshness: Decimal = DEFAULT_FRESHNESS_TARGET
    refresh_on_conflict: bool = True
    refresh_on_model_change: bool = True
    refresh_on_source_change: bool = True

    def should_refresh(
        self,
        profile: PropertyProfile,
        *,
        now: Optional[datetime] = None,
        source_changed: bool = False,
        model_changed: bool = False,
    ) -> tuple[bool, list[RefreshReason]]:
        current = now or utcnow()
        reasons: list[RefreshReason] = []

        reference_time = profile.refreshed_at or profile.built_at
        if current - reference_time > timedelta(days=self.maximum_profile_age_days):
            reasons.append(RefreshReason.EXPIRED)

        if profile.quality:
            if profile.quality.completeness_score < self.minimum_completeness:
                reasons.append(RefreshReason.MISSING_DATA)
            if profile.quality.freshness_score < self.minimum_freshness:
                reasons.append(RefreshReason.EXPIRED)
            if (
                self.refresh_on_conflict
                and profile.quality.conflicted_fields
            ):
                reasons.append(RefreshReason.CONFLICT_REPAIR)

        if source_changed and self.refresh_on_source_change:
            reasons.append(RefreshReason.SOURCE_UPDATE)

        if model_changed and self.refresh_on_model_change:
            reasons.append(RefreshReason.MODEL_UPDATE)

        return bool(reasons), list(dict.fromkeys(reasons))


# ============================================================
# SECTION 12 - EXTERNAL DEPENDENCY PROTOCOLS
# ============================================================

class AddressEngineProtocol(Protocol):
    def analyze(self, raw_address: str, **kwargs: Any) -> Any:
        ...


class ConfidenceEngineProtocol(Protocol):
    def evaluate(self, evidence_items: Sequence[Any], **kwargs: Any) -> Any:
        ...


class ExplanationEngineProtocol(Protocol):
    def explain_multiple_claims(self, **kwargs: Any) -> Any:
        ...


# ============================================================
# SECTION 13 - PROPERTY PROFILE ENGINE
# ============================================================

class PropertyProfileEngine:
    """
    Main orchestration service for canonical property-profile creation.

    The engine accepts normalized or raw evidence, resolves field-level
    candidates, applies optional address/confidence/explanation engines,
    calculates profile quality, generates ML-ready features, detects changes,
    and emits an idempotent build result.
    """

    def __init__(
        self,
        *,
        field_rules: Optional[FieldRuleRegistry] = None,
        field_resolver: Optional[FieldResolver] = None,
        quality_scorer: Optional[ProfileQualityScorer] = None,
        change_detector: Optional[ProfileChangeDetector] = None,
        feature_extractor: Optional[PropertyProfileFeatureExtractor] = None,
        refresh_policy: Optional[ProfileRefreshPolicy] = None,
        address_engine: Optional[AddressEngineProtocol] = None,
        confidence_engine: Optional[ConfidenceEngineProtocol] = None,
        explanation_engine: Optional[ExplanationEngineProtocol] = None,
    ) -> None:
        self.field_rules = field_rules or FieldRuleRegistry()
        self.field_resolver = field_resolver or FieldResolver(
            rules=self.field_rules
        )
        self.quality_scorer = quality_scorer or ProfileQualityScorer(
            rules=self.field_rules
        )
        self.change_detector = change_detector or ProfileChangeDetector()
        self.feature_extractor = feature_extractor or PropertyProfileFeatureExtractor()
        self.refresh_policy = refresh_policy or ProfileRefreshPolicy()
        self.address_engine = address_engine
        self.confidence_engine = confidence_engine
        self.explanation_engine = explanation_engine

    def build(
        self,
        *,
        property_id: str,
        evidence: Sequence[FieldEvidence],
        mode: ProfileBuildMode = ProfileBuildMode.CREATE,
        existing_profile: Optional[PropertyProfile] = None,
        raw_address: Optional[str] = None,
        address_context: Optional[Mapping[str, Any]] = None,
        external_ids: Optional[Mapping[str, str]] = None,
        sales_history: Optional[Sequence[SaleRecord]] = None,
        risks: Optional[Sequence[RiskItem]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        now: Optional[datetime] = None,
    ) -> ProfileBuildResult:
        started = utcnow()
        current_time = now or started
        warnings: list[str] = []
        errors: list[str] = []

        identity = PropertyIdentity(
            property_id=property_id,
            external_ids=dict(external_ids or {}),
        )
        profile = PropertyProfile(
            identity=identity,
            profile_version=DEFAULT_PROFILE_VERSION,
            built_at=current_time,
            refreshed_at=current_time,
            expires_at=current_time + timedelta(
                days=self.refresh_policy.maximum_profile_age_days
            ),
            metadata=dict(metadata or {}),
        )

        if existing_profile is not None:
            profile = self._clone_profile(existing_profile)
            profile.refreshed_at = current_time
            profile.expires_at = current_time + timedelta(
                days=self.refresh_policy.maximum_profile_age_days
            )
            profile.metadata.update(dict(metadata or {}))

        grouped: MutableMapping[str, list[FieldEvidence]] = defaultdict(list)
        for item in evidence:
            grouped[item.field_path].append(item)

        if raw_address:
            self._inject_address_evidence(
                grouped,
                raw_address=raw_address,
                address_context=address_context or {},
                warnings=warnings,
            )

        all_paths = set(grouped)
        all_paths.update(rule.field_path for rule in self.field_rules.all())

        for field_path in sorted(all_paths):
            existing_value = self._get_profile_value(profile, field_path)
            resolution = self.field_resolver.resolve(
                field_path,
                grouped.get(field_path, []),
                existing_value=existing_value,
            )
            profile.resolutions[field_path] = resolution
            if resolution.decision in {
                FieldDecision.ACCEPTED,
                FieldDecision.CONFLICTED,
            }:
                self._set_profile_value(
                    profile,
                    field_path,
                    resolution.selected_value,
                )
            if resolution.decision == FieldDecision.CONFLICTED:
                warnings.append(f"Conflict detected for {field_path}.")

        profile.sales_history = list(sales_history or profile.sales_history)
        profile.risks = list(risks or profile.risks)

        self._synchronize_identity(profile)
        self._synchronize_derived_fields(profile)
        profile.quality = self.quality_scorer.score(
            profile,
            as_of=current_time,
        )
        profile.status = self._determine_status(profile)
        profile.metadata["features"] = self.feature_extractor.extract(profile)
        profile.metadata["source_count"] = len(
            {
                item.source_name
                for item in evidence
                if item.source_name
            }
        )
        profile.metadata["evidence_count"] = len(evidence)

        profile.fingerprint = stable_hash(
            {
                "identity": profile.identity.to_dict(),
                "address": profile.address.to_dict(),
                "structure": profile.structure.to_dict(),
                "ownership": profile.ownership.to_dict(),
                "listing": profile.listing.to_dict(),
                "sales_history": [record.to_dict() for record in profile.sales_history],
                "tax": profile.tax.to_dict(),
                "valuation": profile.valuation.to_dict(),
                "market": profile.market.to_dict(),
                "risks": [risk.to_dict() for risk in profile.risks],
                "resolutions": {
                    key: value.to_dict()
                    for key, value in profile.resolutions.items()
                },
                "quality": profile.quality.to_dict() if profile.quality else None,
                "profile_version": profile.profile_version,
            }
        )

        changes = self.change_detector.compare(existing_profile, profile)
        duration_ms = int((utcnow() - started).total_seconds() * 1000)

        result_fingerprint = stable_hash(
            {
                "profile_fingerprint": profile.fingerprint,
                "mode": mode.value,
                "changes": [change.to_dict() for change in changes],
                "warnings": warnings,
                "errors": errors,
            }
        )

        return ProfileBuildResult(
            profile=profile,
            mode=mode,
            changes=changes,
            warnings=warnings,
            errors=errors,
            source_count=profile.metadata["source_count"],
            evidence_count=len(evidence),
            conflict_count=(
                len(profile.quality.conflicted_fields)
                if profile.quality
                else 0
            ),
            duration_ms=duration_ms,
            fingerprint=result_fingerprint,
        )

    def refresh(
        self,
        profile: PropertyProfile,
        *,
        evidence: Sequence[FieldEvidence],
        raw_address: Optional[str] = None,
        address_context: Optional[Mapping[str, Any]] = None,
        sales_history: Optional[Sequence[SaleRecord]] = None,
        risks: Optional[Sequence[RiskItem]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> ProfileBuildResult:
        return self.build(
            property_id=profile.identity.property_id,
            evidence=evidence,
            mode=ProfileBuildMode.REFRESH,
            existing_profile=profile,
            raw_address=raw_address,
            address_context=address_context,
            external_ids=profile.identity.external_ids,
            sales_history=sales_history,
            risks=risks,
            metadata=metadata,
        )

    def merge(
        self,
        left: PropertyProfile,
        right: PropertyProfile,
    ) -> ProfileBuildResult:
        evidence = self._profile_to_evidence(left, "left_profile")
        evidence.extend(self._profile_to_evidence(right, "right_profile"))

        merged_external_ids = {
            **left.identity.external_ids,
            **right.identity.external_ids,
        }

        sales = self._merge_sales_history(
            left.sales_history,
            right.sales_history,
        )
        risks = self._merge_risks(left.risks, right.risks)

        return self.build(
            property_id=left.identity.property_id,
            evidence=evidence,
            mode=ProfileBuildMode.MERGE,
            existing_profile=left,
            external_ids=merged_external_ids,
            sales_history=sales,
            risks=risks,
            metadata={
                "merged_profile_ids": [
                    left.identity.property_id,
                    right.identity.property_id,
                ],
            },
        )

    def should_refresh(
        self,
        profile: PropertyProfile,
        *,
        source_changed: bool = False,
        model_changed: bool = False,
    ) -> tuple[bool, list[RefreshReason]]:
        return self.refresh_policy.should_refresh(
            profile,
            source_changed=source_changed,
            model_changed=model_changed,
        )

    def _inject_address_evidence(
        self,
        grouped: MutableMapping[str, list[FieldEvidence]],
        *,
        raw_address: str,
        address_context: Mapping[str, Any],
        warnings: list[str],
    ) -> None:
        if self.address_engine is None:
            warnings.append(
                "Raw address was provided but no address engine was configured."
            )
            return

        try:
            analysis = self.address_engine.analyze(
                raw_address,
                **dict(address_context),
            )
            components = get_attr_or_key(analysis, "components")
            confidence = clamp_score(
                get_attr_or_key(analysis, "confidence", DEFAULT_PROFILE_CONFIDENCE)
            )
            source_name = "address_intelligence_engine"

            mapping = {
                "address.canonical_address": get_attr_or_key(
                    analysis,
                    "canonical_address",
                ),
                "address.address_line_1": (
                    components.street_line(include_unit=False)
                    if components is not None
                    and hasattr(components, "street_line")
                    else None
                ),
                "address.address_line_2": (
                    f"{get_attr_or_key(components, 'unit_type') or 'UNIT'} "
                    f"{get_attr_or_key(components, 'unit_number')}"
                    if get_attr_or_key(components, "unit_number")
                    else None
                ),
                "address.city": get_attr_or_key(components, "city"),
                "address.county": get_attr_or_key(components, "county"),
                "address.state_code": get_attr_or_key(components, "state_code"),
                "address.postal_code": get_attr_or_key(components, "postal_code"),
                "address.country_code": get_attr_or_key(
                    components,
                    "country_code",
                    DEFAULT_COUNTRY_CODE,
                ),
                "address.latitude": get_attr_or_key(components, "latitude"),
                "address.longitude": get_attr_or_key(components, "longitude"),
                "identity.parcel_number": get_attr_or_key(
                    components,
                    "parcel_number",
                ),
            }

            for field_path, value in mapping.items():
                if value is None:
                    continue
                grouped[field_path].append(
                    FieldEvidence(
                        field_path=field_path,
                        value=value,
                        source_name=source_name,
                        confidence=confidence,
                        quality=confidence,
                        freshness=ONE,
                        authority=Decimal("0.85"),
                        observed_at=utcnow(),
                        metadata={
                            "address_fingerprint": get_attr_or_key(
                                analysis,
                                "fingerprint",
                            )
                        },
                    )
                )
        except Exception as exc:
            warnings.append(f"Address analysis failed: {exc}")

    def _synchronize_identity(self, profile: PropertyProfile) -> None:
        profile.identity.parcel_number = profile.identity.parcel_number or (
            profile.resolutions.get("identity.parcel_number").selected_value
            if profile.resolutions.get("identity.parcel_number")
            else None
        )
        profile.identity.tax_account_number = (
            profile.identity.tax_account_number
            or (
                profile.resolutions.get("identity.tax_account_number").selected_value
                if profile.resolutions.get("identity.tax_account_number")
                else None
            )
        )
        profile.identity.canonical_key = "|".join(
            value
            for value in [
                normalize_code(profile.address.state_code),
                normalize_text(profile.address.postal_code),
                normalize_text(profile.identity.parcel_number),
                normalize_text(profile.address.canonical_address),
            ]
            if value
        )
        profile.identity.fingerprint = stable_hash(
            {
                "canonical_key": profile.identity.canonical_key,
                "external_ids": profile.identity.external_ids,
            }
        )

    @staticmethod
    def _synchronize_derived_fields(profile: PropertyProfile) -> None:
        if (
            profile.valuation.price_per_sqft is None
            and profile.valuation.estimated_value is not None
            and profile.structure.living_area_sqft not in (None, ZERO)
        ):
            ratio = safe_ratio(
                profile.valuation.estimated_value,
                profile.structure.living_area_sqft,
            )
            profile.valuation.price_per_sqft = money(ratio)

        if profile.listing.days_on_market is None and profile.listing.listing_date:
            end = (
                profile.listing.pending_date
                or profile.listing.expiration_date
                or date.today()
            )
            profile.listing.days_on_market = max(
                (end - profile.listing.listing_date).days,
                0,
            )

        if profile.sales_history:
            latest = max(
                (
                    record
                    for record in profile.sales_history
                    if record.sale_date is not None
                ),
                key=lambda record: record.sale_date,
                default=None,
            )
            if latest:
                profile.metadata["last_sale_date"] = latest.sale_date.isoformat()
                profile.metadata["last_sale_price"] = (
                    str(latest.sale_price)
                    if latest.sale_price is not None
                    else None
                )

    @staticmethod
    def _determine_status(profile: PropertyProfile) -> ProfileStatus:
        if profile.quality is None:
            return ProfileStatus.INVALID
        if profile.quality.level == ProfileQualityLevel.INVALID:
            return ProfileStatus.INVALID
        if profile.quality.conflicted_fields:
            return ProfileStatus.CONFLICTED
        if profile.quality.stale_fields:
            return ProfileStatus.STALE
        if profile.quality.missing_fields:
            return ProfileStatus.PARTIAL
        return ProfileStatus.ACTIVE

    @staticmethod
    def _get_profile_value(
        profile: PropertyProfile,
        field_path: str,
    ) -> Any:
        current: Any = profile
        for segment in field_path.split("."):
            if current is None:
                return None
            current = get_attr_or_key(current, segment)
        return current

    @staticmethod
    def _set_profile_value(
        profile: PropertyProfile,
        field_path: str,
        value: Any,
    ) -> None:
        segments = field_path.split(".")
        current: Any = profile

        for segment in segments[:-1]:
            current = getattr(current, segment, None)
            if current is None:
                return

        final = segments[-1]
        if hasattr(current, final):
            setattr(current, final, value)

    @staticmethod
    def _clone_profile(profile: PropertyProfile) -> PropertyProfile:
        return PropertyProfile(
            identity=PropertyIdentity(**asdict(profile.identity)),
            address=AddressProfile(**asdict(profile.address)),
            structure=StructuralProfile(**asdict(profile.structure)),
            ownership=OwnershipProfile(**asdict(profile.ownership)),
            listing=ListingProfile(**asdict(profile.listing)),
            sales_history=[
                SaleRecord(**asdict(record))
                for record in profile.sales_history
            ],
            tax=TaxProfile(**asdict(profile.tax)),
            valuation=ValuationProfile(**asdict(profile.valuation)),
            market=MarketProfile(**asdict(profile.market)),
            risks=[
                RiskItem(**asdict(risk))
                for risk in profile.risks
            ],
            resolutions={
                key: FieldResolution(
                    field_path=value.field_path,
                    selected_value=value.selected_value,
                    selected_source_name=value.selected_source_name,
                    selected_source_id=value.selected_source_id,
                    confidence=value.confidence,
                    decision=value.decision,
                    candidates=[
                        FieldEvidence(**asdict(candidate))
                        for candidate in value.candidates
                    ],
                    reason=value.reason,
                    conflict_score=value.conflict_score,
                    metadata=dict(value.metadata),
                )
                for key, value in profile.resolutions.items()
            },
            quality=(
                ProfileQuality(
                    completeness_score=profile.quality.completeness_score,
                    freshness_score=profile.quality.freshness_score,
                    confidence_score=profile.quality.confidence_score,
                    consistency_score=profile.quality.consistency_score,
                    source_diversity_score=profile.quality.source_diversity_score,
                    overall_score=profile.quality.overall_score,
                    level=profile.quality.level,
                    missing_fields=list(profile.quality.missing_fields),
                    stale_fields=list(profile.quality.stale_fields),
                    conflicted_fields=list(profile.quality.conflicted_fields),
                    warnings=list(profile.quality.warnings),
                )
                if profile.quality
                else None
            ),
            status=profile.status,
            profile_version=profile.profile_version,
            built_at=profile.built_at,
            refreshed_at=profile.refreshed_at,
            expires_at=profile.expires_at,
            fingerprint=profile.fingerprint,
            metadata=dict(profile.metadata),
        )

    def _profile_to_evidence(
        self,
        profile: PropertyProfile,
        source_name: str,
    ) -> list[FieldEvidence]:
        output: list[FieldEvidence] = []
        for rule in self.field_rules.all():
            value = self._get_profile_value(profile, rule.field_path)
            if value is None:
                continue

            resolution = profile.resolutions.get(rule.field_path)
            output.append(
                FieldEvidence(
                    field_path=rule.field_path,
                    value=value,
                    source_name=source_name,
                    source_id=profile.identity.property_id,
                    confidence=(
                        resolution.confidence
                        if resolution
                        else (
                            profile.quality.confidence_score
                            if profile.quality
                            else DEFAULT_PROFILE_CONFIDENCE
                        )
                    ),
                    quality=(
                        profile.quality.overall_score
                        if profile.quality
                        else DEFAULT_PROFILE_CONFIDENCE
                    ),
                    freshness=(
                        profile.quality.freshness_score
                        if profile.quality
                        else DEFAULT_PROFILE_CONFIDENCE
                    ),
                    authority=Decimal("0.80"),
                    effective_at=profile.refreshed_at or profile.built_at,
                )
            )
        return output

    @staticmethod
    def _merge_sales_history(
        left: Sequence[SaleRecord],
        right: Sequence[SaleRecord],
    ) -> list[SaleRecord]:
        records: dict[str, SaleRecord] = {}
        for record in [*left, *right]:
            key = stable_hash(
                {
                    "sale_date": record.sale_date,
                    "sale_price": record.sale_price,
                    "document_id": record.document_id,
                }
            )
            existing = records.get(key)
            if existing is None or record.confidence > existing.confidence:
                records[key] = record
        return sorted(
            records.values(),
            key=lambda record: record.sale_date or date.min,
            reverse=True,
        )

    @staticmethod
    def _merge_risks(
        left: Sequence[RiskItem],
        right: Sequence[RiskItem],
    ) -> list[RiskItem]:
        records: dict[str, RiskItem] = {}
        for item in [*left, *right]:
            key = stable_hash(
                {
                    "category": item.category,
                    "title": item.title,
                }
            )
            existing = records.get(key)
            if existing is None or item.confidence > existing.confidence:
                records[key] = item
        return sorted(
            records.values(),
            key=lambda item: (item.score, item.confidence),
            reverse=True,
        )


# ============================================================
# SECTION 14 - ORM AND MODEL INTEGRATION HELPERS
# ============================================================

def evidence_from_observation(
    observation: Any,
    *,
    authority: Any = DEFAULT_PROFILE_CONFIDENCE,
) -> FieldEvidence:
    value = None
    if hasattr(observation, "materialized_value"):
        try:
            value = observation.materialized_value()
        except Exception:
            value = None

    if value is None:
        for attribute in (
            "value_numeric",
            "value_text",
            "value_boolean",
            "value_date",
            "value_datetime",
            "value_json",
        ):
            possible = getattr(observation, attribute, None)
            if possible is not None:
                value = possible
                break

    return FieldEvidence(
        field_path=getattr(observation, "field_path", "unknown"),
        value=value,
        source_name=getattr(observation, "source_name", None) or "observation",
        source_id=getattr(observation, "source_record_id", None),
        confidence=clamp_score(
            getattr(
                observation,
                "confidence_score",
                DEFAULT_PROFILE_CONFIDENCE,
            )
        ),
        quality=clamp_score(
            getattr(
                observation,
                "quality_score",
                DEFAULT_PROFILE_CONFIDENCE,
            )
        ),
        freshness=DEFAULT_PROFILE_CONFIDENCE,
        authority=clamp_score(authority),
        observed_at=getattr(observation, "source_observed_at", None),
        retrieved_at=getattr(observation, "source_retrieved_at", None),
        effective_at=getattr(observation, "effective_from", None),
        metadata={
            "observation_id": str(getattr(observation, "id", "")),
            "observation_type": serialize_value(
                getattr(observation, "observation_type", None)
            ),
        },
    )


def apply_profile_to_model(
    target: Any,
    profile: PropertyProfile,
) -> Any:
    mappings = {
        "property_id": profile.identity.property_id,
        "canonical_address": profile.address.canonical_address,
        "address_line_1": profile.address.address_line_1,
        "address_line_2": profile.address.address_line_2,
        "city": profile.address.city,
        "county": profile.address.county,
        "state_code": profile.address.state_code,
        "postal_code": profile.address.postal_code,
        "country_code": profile.address.country_code,
        "latitude": profile.address.latitude,
        "longitude": profile.address.longitude,
        "parcel_number": profile.identity.parcel_number,
        "tax_account_number": profile.identity.tax_account_number,
        "property_type": profile.structure.property_type,
        "listing_status": profile.listing.listing_status,
        "bedrooms": profile.structure.bedrooms,
        "bathrooms": profile.structure.bathrooms,
        "living_area_sqft": profile.structure.living_area_sqft,
        "lot_size_sqft": profile.structure.lot_size_sqft,
        "year_built": profile.structure.year_built,
        "current_list_price": profile.listing.list_price,
        "latest_estimated_value": profile.valuation.estimated_value,
        "latest_value_low": profile.valuation.value_low,
        "latest_value_high": profile.valuation.value_high,
        "latest_value_confidence": profile.valuation.confidence,
        "overall_risk_score": PropertyProfileFeatureExtractor._overall_risk(
            profile.risks
        ),
        "data_completeness_score": (
            profile.quality.completeness_score
            if profile.quality
            else None
        ),
        "data_freshness_score": (
            profile.quality.freshness_score
            if profile.quality
            else None
        ),
        "last_intelligence_run_at": profile.refreshed_at or profile.built_at,
        "next_refresh_at": profile.expires_at,
    }

    for attribute, value in mappings.items():
        if hasattr(target, attribute):
            setattr(target, attribute, value)

    metadata = getattr(target, "metadata_json", None)
    if isinstance(metadata, dict):
        metadata["property_profile_engine"] = profile.to_dict()

    return target


def profile_to_feature_snapshot_payload(
    profile: PropertyProfile,
) -> dict[str, Any]:
    features = PropertyProfileFeatureExtractor().extract(profile)
    return {
        "property_id": profile.identity.property_id,
        "snapshot_at": (
            profile.refreshed_at or profile.built_at
        ).isoformat(),
        "feature_set_name": "property_profile",
        "feature_set_version": profile.profile_version,
        "feature_payload": features,
        "payload_hash": stable_hash(features),
        "feature_count": len(features),
        "missing_feature_count": sum(
            1 for value in features.values() if value is None
        ),
        "quality_score": (
            str(profile.quality.overall_score)
            if profile.quality
            else None
        ),
        "confidence_score": (
            str(profile.quality.confidence_score)
            if profile.quality
            else None
        ),
    }


def profile_to_audit_payload(
    result: ProfileBuildResult,
) -> dict[str, Any]:
    return {
        "property_id": result.profile.identity.property_id,
        "entity_type": "property_profile",
        "entity_id": result.profile.identity.property_id,
        "action": result.mode.value,
        "after_state": result.profile.to_dict(),
        "change_summary": [
            f"{change.change_type.value}: {change.field_path}"
            for change in result.changes[:50]
        ],
        "metadata": {
            "build_fingerprint": result.fingerprint,
            "profile_fingerprint": result.profile.fingerprint,
            "source_count": result.source_count,
            "evidence_count": result.evidence_count,
            "conflict_count": result.conflict_count,
            "duration_ms": result.duration_ms,
            "warnings": result.warnings,
            "errors": result.errors,
        },
    }


# ============================================================
# SECTION 15 - BATCH PROCESSING
# ============================================================

@dataclass(slots=True)
class BatchProfileItem:
    key: str
    result: ProfileBuildResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "result": self.result.to_dict(),
        }


@dataclass(slots=True)
class BatchProfileResult:
    total: int
    succeeded: int
    failed: int
    active: int
    partial: int
    conflicted: int
    average_quality: Decimal
    average_confidence: Decimal
    items: list[BatchProfileItem]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "active": self.active,
            "partial": self.partial,
            "conflicted": self.conflicted,
            "average_quality": str(self.average_quality),
            "average_confidence": str(self.average_confidence),
            "items": [item.to_dict() for item in self.items],
        }


class BatchPropertyProfileProcessor:
    def __init__(
        self,
        *,
        engine: Optional[PropertyProfileEngine] = None,
    ) -> None:
        self.engine = engine or PropertyProfileEngine()

    def process(
        self,
        requests: Mapping[str, Mapping[str, Any]],
    ) -> BatchProfileResult:
        items: list[BatchProfileItem] = []

        for key, request in requests.items():
            result = self.engine.build(
                property_id=request["property_id"],
                evidence=request.get("evidence", []),
                mode=request.get("mode", ProfileBuildMode.CREATE),
                existing_profile=request.get("existing_profile"),
                raw_address=request.get("raw_address"),
                address_context=request.get("address_context"),
                external_ids=request.get("external_ids"),
                sales_history=request.get("sales_history"),
                risks=request.get("risks"),
                metadata=request.get("metadata"),
            )
            items.append(BatchProfileItem(key=key, result=result))

        quality_scores = [
            item.result.profile.quality.overall_score
            for item in items
            if item.result.profile.quality
        ]
        confidence_scores = [
            item.result.profile.quality.confidence_score
            for item in items
            if item.result.profile.quality
        ]

        return BatchProfileResult(
            total=len(items),
            succeeded=sum(1 for item in items if item.result.succeeded),
            failed=sum(1 for item in items if not item.result.succeeded),
            active=sum(
                1
                for item in items
                if item.result.profile.status == ProfileStatus.ACTIVE
            ),
            partial=sum(
                1
                for item in items
                if item.result.profile.status == ProfileStatus.PARTIAL
            ),
            conflicted=sum(
                1
                for item in items
                if item.result.profile.status == ProfileStatus.CONFLICTED
            ),
            average_quality=(
                clamp_score(
                    sum(quality_scores, ZERO)
                    / Decimal(len(quality_scores))
                )
                if quality_scores
                else ZERO
            ),
            average_confidence=(
                clamp_score(
                    sum(confidence_scores, ZERO)
                    / Decimal(len(confidence_scores))
                )
                if confidence_scores
                else ZERO
            ),
            items=items,
        )


# ============================================================
# SECTION 16 - DEFAULT ENGINE AND CONVENIENCE API
# ============================================================

_default_engine = PropertyProfileEngine()


def build_property_profile(
    *,
    property_id: str,
    evidence: Sequence[FieldEvidence],
    mode: ProfileBuildMode = ProfileBuildMode.CREATE,
    existing_profile: Optional[PropertyProfile] = None,
    raw_address: Optional[str] = None,
    address_context: Optional[Mapping[str, Any]] = None,
    external_ids: Optional[Mapping[str, str]] = None,
    sales_history: Optional[Sequence[SaleRecord]] = None,
    risks: Optional[Sequence[RiskItem]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> ProfileBuildResult:
    return _default_engine.build(
        property_id=property_id,
        evidence=evidence,
        mode=mode,
        existing_profile=existing_profile,
        raw_address=raw_address,
        address_context=address_context,
        external_ids=external_ids,
        sales_history=sales_history,
        risks=risks,
        metadata=metadata,
    )


def refresh_property_profile(
    profile: PropertyProfile,
    *,
    evidence: Sequence[FieldEvidence],
    raw_address: Optional[str] = None,
    address_context: Optional[Mapping[str, Any]] = None,
    sales_history: Optional[Sequence[SaleRecord]] = None,
    risks: Optional[Sequence[RiskItem]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> ProfileBuildResult:
    return _default_engine.refresh(
        profile,
        evidence=evidence,
        raw_address=raw_address,
        address_context=address_context,
        sales_history=sales_history,
        risks=risks,
        metadata=metadata,
    )


def merge_property_profiles(
    left: PropertyProfile,
    right: PropertyProfile,
) -> ProfileBuildResult:
    return _default_engine.merge(left, right)


# ============================================================
# SECTION 17 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    # constants and helpers
    "DEFAULT_PROFILE_VERSION",
    "DEFAULT_PROFILE_CONFIDENCE",
    "clamp_score",
    "stable_hash",
    "weighted_mean",
    "money",
    # enums
    "ProfileStatus",
    "ProfileBuildMode",
    "ProfileSection",
    "FieldDecision",
    "MergeStrategy",
    "ProfileQualityLevel",
    "RefreshReason",
    "ChangeType",
    # contracts
    "FieldEvidence",
    "FieldResolution",
    "PropertyIdentity",
    "AddressProfile",
    "StructuralProfile",
    "OwnershipProfile",
    "ListingProfile",
    "SaleRecord",
    "TaxProfile",
    "ValuationProfile",
    "MarketProfile",
    "RiskItem",
    "ProfileQuality",
    "PropertyProfile",
    "ProfileChange",
    "ProfileBuildResult",
    "FieldRule",
    "ProfileRefreshPolicy",
    "BatchProfileItem",
    "BatchProfileResult",
    # services
    "FieldRuleRegistry",
    "ProfileValueNormalizer",
    "FieldResolver",
    "ProfileQualityScorer",
    "ProfileChangeDetector",
    "PropertyProfileFeatureExtractor",
    "PropertyProfileEngine",
    "BatchPropertyProfileProcessor",
    # integration
    "evidence_from_observation",
    "apply_profile_to_model",
    "profile_to_feature_snapshot_payload",
    "profile_to_audit_payload",
    # convenience
    "build_property_profile",
    "refresh_property_profile",
    "merge_property_profiles",
]
