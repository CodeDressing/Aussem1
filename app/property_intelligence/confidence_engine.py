"""
============================================================
AUSSEM REAL ESTATE
PHASE 5.20 - CONFIDENCE ENGINE
FILE: app/property_intelligence/confidence_engine.py

PURPOSE:
Enterprise confidence scoring, uncertainty calibration, evidence fusion,
provider reliability weighting, disagreement analysis, data-quality
aggregation, model-confidence normalization, human-review routing, and
decision policy enforcement for the Aussem Real Estate property-
intelligence platform.

DESIGN PRINCIPLES:
1. Deterministic and reproducible scoring.
2. Decimal arithmetic for stable business logic.
3. Explicit separation of evidence quality, model certainty, and policy.
4. Safe defaults when evidence is sparse or contradictory.
5. Support for Bayesian-style updates without hard dependency on ML libs.
6. Calibration hooks for statistical and machine-learning models.
7. Human-review escalation for high-impact or low-confidence decisions.
8. Portable, dependency-light implementation suitable for APIs, jobs,
   tests, notebooks, and model-serving workflows.
9. Transparent explanations for every score and decision.
10. Compatible with app/property_intelligence/models.py without creating
    circular imports.
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
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Optional, Protocol, Sequence


# ============================================================
# SECTION 01 - NUMERIC CONTEXT AND CONSTANTS
# ============================================================

getcontext().prec = 34

ZERO = Decimal("0")
ONE = Decimal("1")
HALF = Decimal("0.5")
EPSILON = Decimal("0.000001")

DEFAULT_CONFIDENCE = Decimal("0.50")
DEFAULT_PROVIDER_RELIABILITY = Decimal("0.60")
DEFAULT_MODEL_RELIABILITY = Decimal("0.65")
DEFAULT_FRESHNESS_HALF_LIFE_DAYS = Decimal("180")
DEFAULT_REVIEW_THRESHOLD = Decimal("0.65")
DEFAULT_PUBLISH_THRESHOLD = Decimal("0.80")
DEFAULT_AUTO_APPROVE_THRESHOLD = Decimal("0.92")
DEFAULT_CONFLICT_THRESHOLD = Decimal("0.20")
DEFAULT_HIGH_IMPACT_THRESHOLD = Decimal("0.75")

SCORE_SCALE = Decimal("0.000001")
PERCENT_SCALE = Decimal("0.0001")


# ============================================================
# SECTION 02 - GENERIC HELPERS
# ============================================================

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_decimal(value: Any, *, default: Optional[Decimal] = None) -> Optional[Decimal]:
    if value is None or value == "":
        return default
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return ONE if value else ZERO
    try:
        return Decimal(str(value))
    except Exception as exc:
        if default is not None:
            return default
        raise ValueError(f"cannot convert value to Decimal: {value!r}") from exc


def quantize_score(value: Decimal) -> Decimal:
    return value.quantize(SCORE_SCALE, rounding=ROUND_HALF_UP)


def clamp(value: Decimal, minimum: Decimal = ZERO, maximum: Decimal = ONE) -> Decimal:
    return max(minimum, min(maximum, value))


def clamp_score(value: Any) -> Decimal:
    return quantize_score(clamp(to_decimal(value, default=ZERO) or ZERO))


def safe_divide(numerator: Any, denominator: Any, *, default: Decimal = ZERO) -> Decimal:
    num = to_decimal(numerator, default=ZERO) or ZERO
    den = to_decimal(denominator, default=ZERO) or ZERO
    if den == ZERO:
        return default
    return num / den


def weighted_mean(items: Iterable[tuple[Any, Any]], *, default: Decimal = DEFAULT_CONFIDENCE) -> Decimal:
    numerator = ZERO
    denominator = ZERO

    for value, weight in items:
        decimal_value = to_decimal(value)
        decimal_weight = to_decimal(weight)
        if decimal_value is None or decimal_weight is None or decimal_weight <= ZERO:
            continue
        numerator += decimal_value * decimal_weight
        denominator += decimal_weight

    if denominator == ZERO:
        return clamp_score(default)
    return clamp_score(numerator / denominator)


def geometric_mean(values: Iterable[Any], *, default: Decimal = DEFAULT_CONFIDENCE) -> Decimal:
    normalized = [clamp_score(value) for value in values if value is not None]
    if not normalized:
        return clamp_score(default)
    if any(value == ZERO for value in normalized):
        return ZERO

    log_sum = sum(math.log(float(value)) for value in normalized)
    return clamp_score(math.exp(log_sum / len(normalized)))


def harmonic_mean(values: Iterable[Any], *, default: Decimal = DEFAULT_CONFIDENCE) -> Decimal:
    normalized = [clamp_score(value) for value in values if value is not None]
    if not normalized:
        return clamp_score(default)
    if any(value == ZERO for value in normalized):
        return ZERO

    denominator = sum(ONE / value for value in normalized)
    return clamp_score(Decimal(len(normalized)) / denominator)


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sigmoid(value: Any) -> Decimal:
    x = float(to_decimal(value, default=ZERO) or ZERO)
    if x >= 0:
        z = math.exp(-x)
        return clamp_score(1 / (1 + z))
    z = math.exp(x)
    return clamp_score(z / (1 + z))


def logit(probability: Any) -> Decimal:
    p = float(clamp(to_decimal(probability, default=HALF) or HALF, EPSILON, ONE - EPSILON))
    return Decimal(str(math.log(p / (1 - p))))


def entropy_binary(probability: Any) -> Decimal:
    p = float(clamp(to_decimal(probability, default=HALF) or HALF, EPSILON, ONE - EPSILON))
    entropy = -(p * math.log2(p) + (1 - p) * math.log2(1 - p))
    return clamp_score(entropy)


def normalized_entropy(probabilities: Sequence[Any]) -> Decimal:
    values = [float(clamp_score(value)) for value in probabilities if value is not None]
    total = sum(values)
    if total <= 0 or len(values) <= 1:
        return ZERO

    normalized = [value / total for value in values if value > 0]
    entropy = -sum(value * math.log(value) for value in normalized)
    maximum = math.log(len(values))
    return clamp_score(entropy / maximum if maximum else 0)


def percentile(values: Sequence[Any], q: float) -> Optional[Decimal]:
    normalized = sorted(float(to_decimal(value) or ZERO) for value in values if value is not None)
    if not normalized:
        return None
    if len(normalized) == 1:
        return Decimal(str(normalized[0]))

    position = (len(normalized) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return Decimal(str(normalized[lower]))

    fraction = position - lower
    value = normalized[lower] + (normalized[upper] - normalized[lower]) * fraction
    return Decimal(str(value))


def median_absolute_deviation(values: Sequence[Any]) -> Decimal:
    normalized = [float(to_decimal(value) or ZERO) for value in values if value is not None]
    if not normalized:
        return ZERO
    median = statistics.median(normalized)
    deviations = [abs(value - median) for value in normalized]
    return Decimal(str(statistics.median(deviations)))


# ============================================================
# SECTION 03 - ENUMERATIONS
# ============================================================

class StringEnum(str, enum.Enum):
    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]


class ConfidenceLevel(StringEnum):
    CERTAIN = "certain"
    VERY_HIGH = "very_high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"
    UNKNOWN = "unknown"


class EvidenceType(StringEnum):
    PUBLIC_RECORD = "public_record"
    MLS = "mls"
    ASSESSOR = "assessor"
    DEED = "deed"
    TAX = "tax"
    PERMIT = "permit"
    GEOSPATIAL = "geospatial"
    USER_PROVIDED = "user_provided"
    BROKER_PROVIDED = "broker_provided"
    MODEL_OUTPUT = "model_output"
    DERIVED = "derived"
    THIRD_PARTY = "third_party"
    MANUAL_REVIEW = "manual_review"
    OTHER = "other"


class EvidenceStatus(StringEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    STALE = "stale"
    CONFLICTED = "conflicted"
    UNKNOWN = "unknown"


class DecisionOutcome(StringEnum):
    AUTO_APPROVE = "auto_approve"
    APPROVE = "approve"
    REVIEW = "review"
    ESCALATE = "escalate"
    REJECT = "reject"
    HOLD = "hold"


class ReviewPriority(StringEnum):
    NONE = "none"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictSeverity(StringEnum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class CalibrationMethod(StringEnum):
    NONE = "none"
    PLATT = "platt"
    ISOTONIC = "isotonic"
    TEMPERATURE = "temperature"
    BETA = "beta"
    HISTOGRAM = "histogram"
    MANUAL = "manual"


class AggregationMethod(StringEnum):
    WEIGHTED_MEAN = "weighted_mean"
    GEOMETRIC_MEAN = "geometric_mean"
    HARMONIC_MEAN = "harmonic_mean"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    BAYESIAN = "bayesian"
    DEMPSTER_SHAFER = "dempster_shafer"
    ROBUST_MEDIAN = "robust_median"


class UncertaintyType(StringEnum):
    ALEATORIC = "aleatoric"
    EPISTEMIC = "epistemic"
    DATA_QUALITY = "data_quality"
    MODEL = "model"
    PROVIDER = "provider"
    CONFLICT = "conflict"
    TEMPORAL = "temporal"
    TOTAL = "total"


class PolicyMode(StringEnum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    MANUAL = "manual"


class ImpactLevel(StringEnum):
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# SECTION 04 - CORE DATA CONTRACTS
# ============================================================

@dataclass(slots=True)
class ConfidenceBand:
    minimum: Decimal
    maximum: Decimal
    level: ConfidenceLevel
    label: str

    def contains(self, score: Decimal) -> bool:
        return self.minimum <= score <= self.maximum


DEFAULT_CONFIDENCE_BANDS: tuple[ConfidenceBand, ...] = (
    ConfidenceBand(Decimal("0.98"), ONE, ConfidenceLevel.CERTAIN, "Certain"),
    ConfidenceBand(Decimal("0.93"), Decimal("0.979999"), ConfidenceLevel.VERY_HIGH, "Very high"),
    ConfidenceBand(Decimal("0.82"), Decimal("0.929999"), ConfidenceLevel.HIGH, "High"),
    ConfidenceBand(Decimal("0.65"), Decimal("0.819999"), ConfidenceLevel.MODERATE, "Moderate"),
    ConfidenceBand(Decimal("0.40"), Decimal("0.649999"), ConfidenceLevel.LOW, "Low"),
    ConfidenceBand(ZERO, Decimal("0.399999"), ConfidenceLevel.VERY_LOW, "Very low"),
)


@dataclass(slots=True)
class EvidenceItem:
    evidence_id: str
    evidence_type: EvidenceType
    source_name: str
    value: Any = None
    confidence: Decimal = DEFAULT_CONFIDENCE
    reliability: Decimal = DEFAULT_PROVIDER_RELIABILITY
    quality: Decimal = DEFAULT_CONFIDENCE
    freshness: Decimal = DEFAULT_CONFIDENCE
    relevance: Decimal = ONE
    independence: Decimal = ONE
    status: EvidenceStatus = EvidenceStatus.ACTIVE
    observed_at: Optional[datetime] = None
    retrieved_at: Optional[datetime] = None
    effective_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    source_record_id: Optional[str] = None
    field_path: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def normalized(self) -> "EvidenceItem":
        self.confidence = clamp_score(self.confidence)
        self.reliability = clamp_score(self.reliability)
        self.quality = clamp_score(self.quality)
        self.freshness = clamp_score(self.freshness)
        self.relevance = clamp_score(self.relevance)
        self.independence = clamp_score(self.independence)
        return self

    @property
    def active(self) -> bool:
        return self.status == EvidenceStatus.ACTIVE

    @property
    def composite_weight(self) -> Decimal:
        if not self.active:
            return ZERO
        return clamp_score(
            self.reliability
            * self.quality
            * self.freshness
            * self.relevance
            * self.independence
        )

    @property
    def weighted_confidence(self) -> Decimal:
        return clamp_score(self.confidence * self.composite_weight)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["evidence_type"] = self.evidence_type.value
        result["status"] = self.status.value
        for key in (
            "confidence",
            "reliability",
            "quality",
            "freshness",
            "relevance",
            "independence",
        ):
            result[key] = str(result[key])
        for key in ("observed_at", "retrieved_at", "effective_at", "expires_at"):
            if result[key] is not None:
                result[key] = result[key].isoformat()
        return result


@dataclass(slots=True)
class ConfidenceFactor:
    name: str
    score: Decimal
    weight: Decimal
    contribution: Decimal
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": str(self.score),
            "weight": str(self.weight),
            "contribution": str(self.contribution),
            "reason": self.reason,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class ConflictSignal:
    field_path: Optional[str]
    severity: ConflictSeverity
    disagreement_score: Decimal
    conflicting_values: list[Any]
    evidence_ids: list[str]
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_path": self.field_path,
            "severity": self.severity.value,
            "disagreement_score": str(self.disagreement_score),
            "conflicting_values": self.conflicting_values,
            "evidence_ids": self.evidence_ids,
            "explanation": self.explanation,
        }


@dataclass(slots=True)
class UncertaintyEstimate:
    uncertainty_type: UncertaintyType
    score: Decimal
    variance: Optional[Decimal] = None
    standard_deviation: Optional[Decimal] = None
    lower_bound: Optional[Decimal] = None
    upper_bound: Optional[Decimal] = None
    explanation: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def confidence_equivalent(self) -> Decimal:
        return clamp_score(ONE - self.score)

    def to_dict(self) -> dict[str, Any]:
        return {
            "uncertainty_type": self.uncertainty_type.value,
            "score": str(self.score),
            "variance": str(self.variance) if self.variance is not None else None,
            "standard_deviation": (
                str(self.standard_deviation)
                if self.standard_deviation is not None
                else None
            ),
            "lower_bound": str(self.lower_bound) if self.lower_bound is not None else None,
            "upper_bound": str(self.upper_bound) if self.upper_bound is not None else None,
            "explanation": self.explanation,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class ConfidenceResult:
    score: Decimal
    level: ConfidenceLevel
    method: AggregationMethod
    evidence_count: int
    active_evidence_count: int
    effective_evidence_weight: Decimal
    factors: list[ConfidenceFactor]
    conflicts: list[ConflictSignal]
    uncertainties: list[UncertaintyEstimate]
    explanation: str
    fingerprint: str
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def uncertainty(self) -> Decimal:
        return clamp_score(ONE - self.score)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": str(self.score),
            "level": self.level.value,
            "method": self.method.value,
            "evidence_count": self.evidence_count,
            "active_evidence_count": self.active_evidence_count,
            "effective_evidence_weight": str(self.effective_evidence_weight),
            "factors": [factor.to_dict() for factor in self.factors],
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
            "uncertainties": [item.to_dict() for item in self.uncertainties],
            "explanation": self.explanation,
            "fingerprint": self.fingerprint,
            "warnings": list(self.warnings),
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class ConfidenceDecision:
    outcome: DecisionOutcome
    review_priority: ReviewPriority
    confidence: Decimal
    impact: Decimal
    threshold_used: Decimal
    reasons: list[str]
    policy_name: str
    requires_human_review: bool
    can_publish: bool
    can_auto_approve: bool
    fingerprint: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "review_priority": self.review_priority.value,
            "confidence": str(self.confidence),
            "impact": str(self.impact),
            "threshold_used": str(self.threshold_used),
            "reasons": list(self.reasons),
            "policy_name": self.policy_name,
            "requires_human_review": self.requires_human_review,
            "can_publish": self.can_publish,
            "can_auto_approve": self.can_auto_approve,
            "fingerprint": self.fingerprint,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class CalibrationPoint:
    predicted_confidence: Decimal
    observed_accuracy: Decimal
    sample_count: int
    lower_bound: Optional[Decimal] = None
    upper_bound: Optional[Decimal] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "predicted_confidence": str(self.predicted_confidence),
            "observed_accuracy": str(self.observed_accuracy),
            "sample_count": self.sample_count,
            "lower_bound": str(self.lower_bound) if self.lower_bound is not None else None,
            "upper_bound": str(self.upper_bound) if self.upper_bound is not None else None,
        }


@dataclass(slots=True)
class CalibrationReport:
    method: CalibrationMethod
    points: list[CalibrationPoint]
    expected_calibration_error: Decimal
    maximum_calibration_error: Decimal
    brier_score: Optional[Decimal]
    sample_count: int
    is_well_calibrated: bool
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method.value,
            "points": [point.to_dict() for point in self.points],
            "expected_calibration_error": str(self.expected_calibration_error),
            "maximum_calibration_error": str(self.maximum_calibration_error),
            "brier_score": str(self.brier_score) if self.brier_score is not None else None,
            "sample_count": self.sample_count,
            "is_well_calibrated": self.is_well_calibrated,
            "warnings": list(self.warnings),
        }


# ============================================================
# SECTION 05 - PROVIDER RELIABILITY
# ============================================================

@dataclass(slots=True)
class ProviderReliabilityProfile:
    provider_name: str
    base_reliability: Decimal = DEFAULT_PROVIDER_RELIABILITY
    authority_score: Decimal = DEFAULT_PROVIDER_RELIABILITY
    historical_accuracy: Decimal = DEFAULT_PROVIDER_RELIABILITY
    coverage_score: Decimal = DEFAULT_PROVIDER_RELIABILITY
    latency_score: Decimal = DEFAULT_PROVIDER_RELIABILITY
    freshness_score: Decimal = DEFAULT_PROVIDER_RELIABILITY
    consistency_score: Decimal = DEFAULT_PROVIDER_RELIABILITY
    sample_count: int = 0
    last_evaluated_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def composite(self) -> Decimal:
        weighted = weighted_mean(
            (
                (self.base_reliability, Decimal("0.10")),
                (self.authority_score, Decimal("0.20")),
                (self.historical_accuracy, Decimal("0.30")),
                (self.coverage_score, Decimal("0.10")),
                (self.latency_score, Decimal("0.05")),
                (self.freshness_score, Decimal("0.15")),
                (self.consistency_score, Decimal("0.10")),
            ),
            default=self.base_reliability,
        )

        sample_factor = clamp_score(
            Decimal(str(math.log1p(max(self.sample_count, 0)))) / Decimal("10")
        )
        return clamp_score(
            weighted * Decimal("0.85")
            + self.base_reliability * Decimal("0.15") * (ONE - sample_factor)
            + weighted * sample_factor * Decimal("0.15")
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for key in (
            "base_reliability",
            "authority_score",
            "historical_accuracy",
            "coverage_score",
            "latency_score",
            "freshness_score",
            "consistency_score",
        ):
            result[key] = str(result[key])
        result["composite_reliability"] = str(self.composite())
        if result["last_evaluated_at"] is not None:
            result["last_evaluated_at"] = result["last_evaluated_at"].isoformat()
        return result


class ProviderReliabilityRegistry:
    def __init__(
        self,
        profiles: Optional[Iterable[ProviderReliabilityProfile]] = None,
        *,
        default_reliability: Decimal = DEFAULT_PROVIDER_RELIABILITY,
    ) -> None:
        self.default_reliability = clamp_score(default_reliability)
        self._profiles: dict[str, ProviderReliabilityProfile] = {}
        for profile in profiles or []:
            self.register(profile)

    @staticmethod
    def _key(provider_name: str) -> str:
        return provider_name.strip().lower()

    def register(self, profile: ProviderReliabilityProfile) -> None:
        self._profiles[self._key(profile.provider_name)] = profile

    def get(self, provider_name: Optional[str]) -> Optional[ProviderReliabilityProfile]:
        if not provider_name:
            return None
        return self._profiles.get(self._key(provider_name))

    def score(self, provider_name: Optional[str]) -> Decimal:
        profile = self.get(provider_name)
        return profile.composite() if profile else self.default_reliability

    def update_accuracy(
        self,
        provider_name: str,
        *,
        correct_count: int,
        total_count: int,
        smoothing_strength: Decimal = Decimal("20"),
    ) -> ProviderReliabilityProfile:
        if total_count < 0 or correct_count < 0 or correct_count > total_count:
            raise ValueError("invalid provider accuracy counts")

        profile = self.get(provider_name)
        if profile is None:
            profile = ProviderReliabilityProfile(provider_name=provider_name)
            self.register(profile)

        prior = profile.historical_accuracy
        prior_weight = smoothing_strength
        observed = (
            Decimal(correct_count) / Decimal(total_count)
            if total_count
            else prior
        )
        profile.historical_accuracy = clamp_score(
            (prior * prior_weight + observed * Decimal(total_count))
            / (prior_weight + Decimal(total_count))
        )
        profile.sample_count += total_count
        profile.last_evaluated_at = utcnow()
        return profile

    def to_dict(self) -> dict[str, Any]:
        return {
            "default_reliability": str(self.default_reliability),
            "providers": {
                key: profile.to_dict()
                for key, profile in sorted(self._profiles.items())
            },
        }


# ============================================================
# SECTION 06 - FRESHNESS AND TEMPORAL DECAY
# ============================================================

@dataclass(slots=True)
class FreshnessPolicy:
    half_life_days: Decimal = DEFAULT_FRESHNESS_HALF_LIFE_DAYS
    maximum_age_days: Optional[Decimal] = None
    minimum_score: Decimal = ZERO
    future_tolerance_minutes: Decimal = Decimal("5")

    def score(
        self,
        observed_at: Optional[datetime],
        *,
        as_of: Optional[datetime] = None,
    ) -> Decimal:
        if observed_at is None:
            return clamp_score(self.minimum_score)

        now = as_of or utcnow()
        observed = observed_at
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        age_seconds = Decimal(str((now - observed).total_seconds()))
        future_tolerance = self.future_tolerance_minutes * Decimal("60")

        if age_seconds < -future_tolerance:
            return ZERO
        if age_seconds <= ZERO:
            return ONE

        age_days = age_seconds / Decimal("86400")
        if self.maximum_age_days is not None and age_days >= self.maximum_age_days:
            return clamp_score(self.minimum_score)

        half_life = max(self.half_life_days, EPSILON)
        decay = math.exp(-math.log(2) * float(age_days / half_life))
        return clamp_score(max(Decimal(str(decay)), self.minimum_score))


class FreshnessPolicyRegistry:
    def __init__(
        self,
        policies: Optional[Mapping[str, FreshnessPolicy]] = None,
        *,
        default_policy: Optional[FreshnessPolicy] = None,
    ) -> None:
        self.default_policy = default_policy or FreshnessPolicy()
        self._policies = {
            key.strip().lower(): policy
            for key, policy in (policies or {}).items()
        }

    def get(self, field_path: Optional[str]) -> FreshnessPolicy:
        if not field_path:
            return self.default_policy

        key = field_path.strip().lower()
        if key in self._policies:
            return self._policies[key]

        candidates = sorted(
            (
                (prefix, policy)
                for prefix, policy in self._policies.items()
                if key.startswith(prefix)
            ),
            key=lambda item: len(item[0]),
            reverse=True,
        )
        return candidates[0][1] if candidates else self.default_policy

    def score(
        self,
        field_path: Optional[str],
        observed_at: Optional[datetime],
        *,
        as_of: Optional[datetime] = None,
    ) -> Decimal:
        return self.get(field_path).score(observed_at, as_of=as_of)


DEFAULT_FRESHNESS_POLICIES = FreshnessPolicyRegistry(
    {
        "property.address": FreshnessPolicy(
            half_life_days=Decimal("3650"),
            maximum_age_days=Decimal("7300"),
            minimum_score=Decimal("0.40"),
        ),
        "property.living_area": FreshnessPolicy(
            half_life_days=Decimal("1825"),
            maximum_age_days=Decimal("7300"),
            minimum_score=Decimal("0.35"),
        ),
        "listing": FreshnessPolicy(
            half_life_days=Decimal("7"),
            maximum_age_days=Decimal("90"),
        ),
        "market": FreshnessPolicy(
            half_life_days=Decimal("30"),
            maximum_age_days=Decimal("365"),
        ),
        "valuation": FreshnessPolicy(
            half_life_days=Decimal("60"),
            maximum_age_days=Decimal("365"),
        ),
        "risk": FreshnessPolicy(
            half_life_days=Decimal("180"),
            maximum_age_days=Decimal("1095"),
        ),
        "tax": FreshnessPolicy(
            half_life_days=Decimal("365"),
            maximum_age_days=Decimal("1095"),
        ),
        "deed": FreshnessPolicy(
            half_life_days=Decimal("3650"),
            minimum_score=Decimal("0.60"),
        ),
    }
)


# ============================================================
# SECTION 07 - EVIDENCE NORMALIZATION
# ============================================================

class EvidenceNormalizer:
    def __init__(
        self,
        *,
        provider_registry: Optional[ProviderReliabilityRegistry] = None,
        freshness_registry: Optional[FreshnessPolicyRegistry] = None,
    ) -> None:
        self.provider_registry = provider_registry or ProviderReliabilityRegistry()
        self.freshness_registry = freshness_registry or DEFAULT_FRESHNESS_POLICIES

    def normalize(
        self,
        evidence: EvidenceItem,
        *,
        as_of: Optional[datetime] = None,
    ) -> EvidenceItem:
        evidence.normalized()

        if evidence.reliability == DEFAULT_PROVIDER_RELIABILITY:
            evidence.reliability = self.provider_registry.score(evidence.source_name)

        freshness_time = (
            evidence.effective_at
            or evidence.observed_at
            or evidence.retrieved_at
        )
        evidence.freshness = self.freshness_registry.score(
            evidence.field_path,
            freshness_time,
            as_of=as_of,
        )

        if evidence.expires_at:
            expires_at = evidence.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            now = as_of or utcnow()
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            if expires_at <= now:
                evidence.status = EvidenceStatus.STALE
                evidence.freshness = ZERO

        return evidence


# ============================================================
# SECTION 08 - CONFLICT AND DISAGREEMENT ANALYSIS
# ============================================================

class ValueComparator(Protocol):
    def similarity(self, left: Any, right: Any) -> Decimal:
        ...


class GenericValueComparator:
    def __init__(self, *, numeric_tolerance: Decimal = Decimal("0.02")) -> None:
        self.numeric_tolerance = numeric_tolerance

    def similarity(self, left: Any, right: Any) -> Decimal:
        if left is None and right is None:
            return ONE
        if left is None or right is None:
            return ZERO

        left_decimal = self._maybe_decimal(left)
        right_decimal = self._maybe_decimal(right)
        if left_decimal is not None and right_decimal is not None:
            denominator = max(abs(left_decimal), abs(right_decimal), ONE)
            relative_difference = abs(left_decimal - right_decimal) / denominator
            if relative_difference <= self.numeric_tolerance:
                return ONE
            return clamp_score(ONE - relative_difference)

        left_text = self._normalize_text(left)
        right_text = self._normalize_text(right)
        if left_text == right_text:
            return ONE
        if not left_text or not right_text:
            return ZERO

        left_tokens = set(left_text.split())
        right_tokens = set(right_text.split())
        union = left_tokens | right_tokens
        if not union:
            return ONE
        return clamp_score(Decimal(len(left_tokens & right_tokens)) / Decimal(len(union)))

    @staticmethod
    def _maybe_decimal(value: Any) -> Optional[Decimal]:
        if isinstance(value, bool):
            return None
        try:
            return Decimal(str(value))
        except Exception:
            return None

    @staticmethod
    def _normalize_text(value: Any) -> str:
        return " ".join(str(value).strip().upper().split())


class ConflictDetector:
    def __init__(
        self,
        *,
        comparator: Optional[ValueComparator] = None,
        conflict_threshold: Decimal = DEFAULT_CONFLICT_THRESHOLD,
    ) -> None:
        self.comparator = comparator or GenericValueComparator()
        self.conflict_threshold = clamp_score(conflict_threshold)

    def detect(self, evidence_items: Sequence[EvidenceItem]) -> list[ConflictSignal]:
        active = [
            evidence
            for evidence in evidence_items
            if evidence.active and evidence.value is not None
        ]
        if len(active) < 2:
            return []

        groups: MutableMapping[Optional[str], list[EvidenceItem]] = defaultdict(list)
        for item in active:
            groups[item.field_path].append(item)

        conflicts: list[ConflictSignal] = []
        for field_path, field_items in groups.items():
            if len(field_items) < 2:
                continue

            pair_disagreements: list[Decimal] = []
            conflict_ids: set[str] = set()
            conflict_values: list[Any] = []

            for index, left in enumerate(field_items):
                for right in field_items[index + 1:]:
                    similarity_score = self.comparator.similarity(left.value, right.value)
                    disagreement = clamp_score(ONE - similarity_score)
                    if disagreement >= self.conflict_threshold:
                        pair_disagreements.append(disagreement)
                        conflict_ids.update((left.evidence_id, right.evidence_id))
                        conflict_values.extend((left.value, right.value))

            if not pair_disagreements:
                continue

            disagreement_score = clamp_score(
                sum(pair_disagreements, ZERO) / Decimal(len(pair_disagreements))
            )
            severity = self._severity(disagreement_score)
            unique_values = list(dict.fromkeys(str(value) for value in conflict_values))

            conflicts.append(
                ConflictSignal(
                    field_path=field_path,
                    severity=severity,
                    disagreement_score=disagreement_score,
                    conflicting_values=unique_values,
                    evidence_ids=sorted(conflict_ids),
                    explanation=(
                        f"{len(conflict_ids)} evidence records disagree for "
                        f"{field_path or 'the evaluated field'}."
                    ),
                )
            )

        return conflicts

    @staticmethod
    def _severity(disagreement: Decimal) -> ConflictSeverity:
        if disagreement >= Decimal("0.80"):
            return ConflictSeverity.CRITICAL
        if disagreement >= Decimal("0.60"):
            return ConflictSeverity.HIGH
        if disagreement >= Decimal("0.35"):
            return ConflictSeverity.MODERATE
        if disagreement > ZERO:
            return ConflictSeverity.LOW
        return ConflictSeverity.NONE


# ============================================================
# SECTION 09 - EVIDENCE AGGREGATION
# ============================================================

class EvidenceAggregator:
    def aggregate(
        self,
        evidence_items: Sequence[EvidenceItem],
        *,
        method: AggregationMethod = AggregationMethod.WEIGHTED_MEAN,
        prior: Decimal = DEFAULT_CONFIDENCE,
    ) -> Decimal:
        active = [item for item in evidence_items if item.active]
        if not active:
            return clamp_score(prior)

        if method == AggregationMethod.WEIGHTED_MEAN:
            return weighted_mean(
                (item.confidence, item.composite_weight)
                for item in active
            )

        if method == AggregationMethod.GEOMETRIC_MEAN:
            return geometric_mean(
                item.confidence * max(item.composite_weight, EPSILON)
                for item in active
            )

        if method == AggregationMethod.HARMONIC_MEAN:
            return harmonic_mean(
                item.confidence * max(item.composite_weight, EPSILON)
                for item in active
            )

        if method == AggregationMethod.MINIMUM:
            return min(
                (clamp_score(item.confidence * item.composite_weight) for item in active),
                default=clamp_score(prior),
            )

        if method == AggregationMethod.MAXIMUM:
            return max(
                (clamp_score(item.confidence * item.composite_weight) for item in active),
                default=clamp_score(prior),
            )

        if method == AggregationMethod.ROBUST_MEDIAN:
            scores = sorted(
                clamp_score(item.confidence * item.composite_weight)
                for item in active
            )
            midpoint = len(scores) // 2
            if len(scores) % 2:
                return scores[midpoint]
            return clamp_score((scores[midpoint - 1] + scores[midpoint]) / Decimal("2"))

        if method == AggregationMethod.BAYESIAN:
            return self._bayesian(active, prior=prior)

        if method == AggregationMethod.DEMPSTER_SHAFER:
            return self._dempster_shafer(active)

        raise ValueError(f"unsupported aggregation method: {method}")

    @staticmethod
    def _bayesian(
        evidence_items: Sequence[EvidenceItem],
        *,
        prior: Decimal,
    ) -> Decimal:
        posterior_log_odds = logit(prior)

        for item in evidence_items:
            confidence = clamp(item.confidence, EPSILON, ONE - EPSILON)
            weight = item.composite_weight
            evidence_log_odds = logit(confidence)
            posterior_log_odds += evidence_log_odds * weight

        return sigmoid(posterior_log_odds)

    @staticmethod
    def _dempster_shafer(evidence_items: Sequence[EvidenceItem]) -> Decimal:
        belief = ZERO
        disbelief = ZERO
        uncertainty = ONE

        for item in evidence_items:
            weight = item.composite_weight
            support = clamp_score(item.confidence * weight)
            oppose = clamp_score((ONE - item.confidence) * weight)
            unknown = clamp_score(ONE - support - oppose)

            conflict = belief * oppose + disbelief * support
            normalization = max(ONE - conflict, EPSILON)

            new_belief = (
                belief * support
                + belief * unknown
                + uncertainty * support
            ) / normalization
            new_disbelief = (
                disbelief * oppose
                + disbelief * unknown
                + uncertainty * oppose
            ) / normalization
            new_uncertainty = (uncertainty * unknown) / normalization

            belief = clamp_score(new_belief)
            disbelief = clamp_score(new_disbelief)
            uncertainty = clamp_score(new_uncertainty)

        return clamp_score(belief + uncertainty * HALF)


# ============================================================
# SECTION 10 - UNCERTAINTY ESTIMATION
# ============================================================

class UncertaintyEstimator:
    def estimate(
        self,
        evidence_items: Sequence[EvidenceItem],
        conflicts: Sequence[ConflictSignal],
        *,
        aggregated_confidence: Decimal,
    ) -> list[UncertaintyEstimate]:
        active = [item for item in evidence_items if item.active]
        estimates: list[UncertaintyEstimate] = []

        if active:
            confidences = [float(item.confidence) for item in active]
            variance = (
                Decimal(str(statistics.pvariance(confidences)))
                if len(confidences) > 1
                else ZERO
            )
            standard_deviation = Decimal(str(math.sqrt(float(variance))))
            estimates.append(
                UncertaintyEstimate(
                    uncertainty_type=UncertaintyType.MODEL,
                    score=clamp_score(standard_deviation * Decimal("2")),
                    variance=variance,
                    standard_deviation=standard_deviation,
                    explanation="Dispersion among evidence confidence values.",
                )
            )

            provider_uncertainty = clamp_score(
                ONE
                - weighted_mean(
                    (item.reliability, item.relevance)
                    for item in active
                )
            )
            estimates.append(
                UncertaintyEstimate(
                    uncertainty_type=UncertaintyType.PROVIDER,
                    score=provider_uncertainty,
                    explanation="Uncertainty derived from provider reliability.",
                )
            )

            quality_uncertainty = clamp_score(
                ONE
                - weighted_mean(
                    (item.quality, item.relevance)
                    for item in active
                )
            )
            estimates.append(
                UncertaintyEstimate(
                    uncertainty_type=UncertaintyType.DATA_QUALITY,
                    score=quality_uncertainty,
                    explanation="Uncertainty derived from evidence quality.",
                )
            )

            temporal_uncertainty = clamp_score(
                ONE
                - weighted_mean(
                    (item.freshness, item.relevance)
                    for item in active
                )
            )
            estimates.append(
                UncertaintyEstimate(
                    uncertainty_type=UncertaintyType.TEMPORAL,
                    score=temporal_uncertainty,
                    explanation="Uncertainty derived from evidence age and staleness.",
                )
            )

        conflict_uncertainty = (
            max((conflict.disagreement_score for conflict in conflicts), default=ZERO)
        )
        estimates.append(
            UncertaintyEstimate(
                uncertainty_type=UncertaintyType.CONFLICT,
                score=clamp_score(conflict_uncertainty),
                explanation="Uncertainty derived from conflicting evidence.",
            )
        )

        total = clamp_score(
            ONE
            - geometric_mean(
                estimate.confidence_equivalent
                for estimate in estimates
            )
        )
        total = max(total, clamp_score(ONE - aggregated_confidence))
        estimates.append(
            UncertaintyEstimate(
                uncertainty_type=UncertaintyType.TOTAL,
                score=total,
                explanation="Combined uncertainty across all evaluated dimensions.",
            )
        )

        return estimates


# ============================================================
# SECTION 11 - CONFIDENCE CALIBRATION
# ============================================================

class ConfidenceCalibrator:
    def __init__(
        self,
        *,
        method: CalibrationMethod = CalibrationMethod.NONE,
        parameters: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.method = method
        self.parameters = dict(parameters or {})

    def calibrate(self, raw_confidence: Any) -> Decimal:
        value = clamp_score(raw_confidence)

        if self.method == CalibrationMethod.NONE:
            return value

        if self.method == CalibrationMethod.PLATT:
            a = float(self.parameters.get("a", 1.0))
            b = float(self.parameters.get("b", 0.0))
            return sigmoid(Decimal(str(a)) * logit(value) + Decimal(str(b)))

        if self.method == CalibrationMethod.TEMPERATURE:
            temperature = max(float(self.parameters.get("temperature", 1.0)), 1e-6)
            return sigmoid(logit(value) / Decimal(str(temperature)))

        if self.method == CalibrationMethod.BETA:
            alpha = float(self.parameters.get("alpha", 1.0))
            beta = float(self.parameters.get("beta", 1.0))
            intercept = float(self.parameters.get("intercept", 0.0))
            p = float(clamp(value, EPSILON, ONE - EPSILON))
            calibrated_logit = (
                alpha * math.log(p)
                - beta * math.log(1 - p)
                + intercept
            )
            return sigmoid(calibrated_logit)

        if self.method == CalibrationMethod.HISTOGRAM:
            bins = list(self.parameters.get("bins", []))
            values = list(self.parameters.get("values", []))
            if not bins or len(values) != len(bins) - 1:
                return value
            numeric = float(value)
            for index in range(len(bins) - 1):
                if float(bins[index]) <= numeric <= float(bins[index + 1]):
                    return clamp_score(values[index])
            return value

        if self.method == CalibrationMethod.ISOTONIC:
            x_values = [float(item) for item in self.parameters.get("x", [])]
            y_values = [float(item) for item in self.parameters.get("y", [])]
            if len(x_values) != len(y_values) or not x_values:
                return value
            return clamp_score(self._interpolate(float(value), x_values, y_values))

        if self.method == CalibrationMethod.MANUAL:
            scale = to_decimal(self.parameters.get("scale"), default=ONE) or ONE
            offset = to_decimal(self.parameters.get("offset"), default=ZERO) or ZERO
            return clamp_score(value * scale + offset)

        raise ValueError(f"unsupported calibration method: {self.method}")

    @staticmethod
    def _interpolate(value: float, x_values: Sequence[float], y_values: Sequence[float]) -> float:
        if value <= x_values[0]:
            return y_values[0]
        if value >= x_values[-1]:
            return y_values[-1]

        for index in range(len(x_values) - 1):
            left_x, right_x = x_values[index], x_values[index + 1]
            if left_x <= value <= right_x:
                if right_x == left_x:
                    return y_values[index]
                fraction = (value - left_x) / (right_x - left_x)
                return y_values[index] + fraction * (y_values[index + 1] - y_values[index])
        return value

    @staticmethod
    def evaluate(
        predictions: Sequence[Any],
        outcomes: Sequence[Any],
        *,
        bins: int = 10,
        method: CalibrationMethod = CalibrationMethod.NONE,
    ) -> CalibrationReport:
        if len(predictions) != len(outcomes):
            raise ValueError("predictions and outcomes must have equal length")
        if bins <= 0:
            raise ValueError("bins must be positive")

        pairs = [
            (float(clamp_score(prediction)), int(bool(outcome)))
            for prediction, outcome in zip(predictions, outcomes)
        ]
        if not pairs:
            return CalibrationReport(
                method=method,
                points=[],
                expected_calibration_error=ZERO,
                maximum_calibration_error=ZERO,
                brier_score=None,
                sample_count=0,
                is_well_calibrated=False,
                warnings=["No calibration samples were provided."],
            )

        buckets: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
        for prediction, outcome in pairs:
            index = min(int(prediction * bins), bins - 1)
            buckets[index].append((prediction, outcome))

        points: list[CalibrationPoint] = []
        weighted_error = ZERO
        max_error = ZERO

        for bucket in buckets:
            if not bucket:
                continue

            mean_prediction = Decimal(str(statistics.mean(item[0] for item in bucket)))
            observed_accuracy = Decimal(str(statistics.mean(item[1] for item in bucket)))
            error = abs(mean_prediction - observed_accuracy)
            weighted_error += error * Decimal(len(bucket))
            max_error = max(max_error, error)

            points.append(
                CalibrationPoint(
                    predicted_confidence=clamp_score(mean_prediction),
                    observed_accuracy=clamp_score(observed_accuracy),
                    sample_count=len(bucket),
                )
            )

        ece = weighted_error / Decimal(len(pairs))
        brier = Decimal(
            str(
                statistics.mean(
                    (prediction - outcome) ** 2
                    for prediction, outcome in pairs
                )
            )
        )

        warnings: list[str] = []
        if len(pairs) < 100:
            warnings.append("Calibration sample size is below 100.")
        if any(point.sample_count < 5 for point in points):
            warnings.append("One or more calibration bins contain fewer than five samples.")

        return CalibrationReport(
            method=method,
            points=points,
            expected_calibration_error=clamp_score(ece),
            maximum_calibration_error=clamp_score(max_error),
            brier_score=quantize_score(brier),
            sample_count=len(pairs),
            is_well_calibrated=ece <= Decimal("0.05"),
            warnings=warnings,
        )


# ============================================================
# SECTION 12 - DECISION POLICY
# ============================================================

@dataclass(slots=True)
class ConfidencePolicy:
    name: str = "balanced"
    mode: PolicyMode = PolicyMode.BALANCED
    reject_below: Decimal = Decimal("0.25")
    escalate_below: Decimal = Decimal("0.50")
    review_below: Decimal = DEFAULT_REVIEW_THRESHOLD
    publish_at_or_above: Decimal = DEFAULT_PUBLISH_THRESHOLD
    auto_approve_at_or_above: Decimal = DEFAULT_AUTO_APPROVE_THRESHOLD
    high_impact_threshold: Decimal = DEFAULT_HIGH_IMPACT_THRESHOLD
    conflict_escalation_threshold: Decimal = Decimal("0.60")
    minimum_evidence_count: int = 1
    minimum_effective_weight: Decimal = Decimal("0.25")
    critical_fields: frozenset[str] = frozenset()
    require_review_for_high_impact: bool = True
    require_review_for_conflict: bool = True
    allow_publish_with_review: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def normalized(self) -> "ConfidencePolicy":
        self.reject_below = clamp_score(self.reject_below)
        self.escalate_below = clamp_score(self.escalate_below)
        self.review_below = clamp_score(self.review_below)
        self.publish_at_or_above = clamp_score(self.publish_at_or_above)
        self.auto_approve_at_or_above = clamp_score(self.auto_approve_at_or_above)
        self.high_impact_threshold = clamp_score(self.high_impact_threshold)
        self.conflict_escalation_threshold = clamp_score(self.conflict_escalation_threshold)

        thresholds = [
            self.reject_below,
            self.escalate_below,
            self.review_below,
            self.publish_at_or_above,
            self.auto_approve_at_or_above,
        ]
        if thresholds != sorted(thresholds):
            raise ValueError("confidence policy thresholds must be monotonically increasing")
        return self


def default_policy(mode: PolicyMode = PolicyMode.BALANCED) -> ConfidencePolicy:
    if mode == PolicyMode.CONSERVATIVE:
        return ConfidencePolicy(
            name="conservative",
            mode=mode,
            reject_below=Decimal("0.35"),
            escalate_below=Decimal("0.60"),
            review_below=Decimal("0.78"),
            publish_at_or_above=Decimal("0.88"),
            auto_approve_at_or_above=Decimal("0.97"),
            minimum_evidence_count=2,
            minimum_effective_weight=Decimal("0.50"),
        )

    if mode == PolicyMode.AGGRESSIVE:
        return ConfidencePolicy(
            name="aggressive",
            mode=mode,
            reject_below=Decimal("0.15"),
            escalate_below=Decimal("0.35"),
            review_below=Decimal("0.55"),
            publish_at_or_above=Decimal("0.70"),
            auto_approve_at_or_above=Decimal("0.88"),
            minimum_evidence_count=1,
            minimum_effective_weight=Decimal("0.15"),
            allow_publish_with_review=True,
        )

    return ConfidencePolicy(name="balanced", mode=mode)


class ConfidenceDecisionEngine:
    def decide(
        self,
        result: ConfidenceResult,
        *,
        impact: Any = DEFAULT_CONFIDENCE,
        field_path: Optional[str] = None,
        policy: Optional[ConfidencePolicy] = None,
    ) -> ConfidenceDecision:
        active_policy = (policy or default_policy()).normalized()
        confidence = result.score
        impact_score = clamp_score(impact)
        reasons: list[str] = []

        conflict_score = max(
            (conflict.disagreement_score for conflict in result.conflicts),
            default=ZERO,
        )
        critical_conflict = conflict_score >= active_policy.conflict_escalation_threshold
        high_impact = impact_score >= active_policy.high_impact_threshold
        critical_field = field_path in active_policy.critical_fields if field_path else False

        if result.active_evidence_count < active_policy.minimum_evidence_count:
            reasons.append("Insufficient active evidence.")
        if result.effective_evidence_weight < active_policy.minimum_effective_weight:
            reasons.append("Effective evidence weight is below policy minimum.")
        if critical_conflict:
            reasons.append("Evidence conflict exceeds the policy escalation threshold.")
        if high_impact:
            reasons.append("Decision impact is high.")
        if critical_field:
            reasons.append("The evaluated field is designated as critical.")

        requires_review = False
        outcome = DecisionOutcome.APPROVE
        threshold_used = active_policy.publish_at_or_above

        if confidence < active_policy.reject_below:
            outcome = DecisionOutcome.REJECT
            threshold_used = active_policy.reject_below
        elif confidence < active_policy.escalate_below:
            outcome = DecisionOutcome.ESCALATE
            threshold_used = active_policy.escalate_below
            requires_review = True
        elif confidence < active_policy.review_below:
            outcome = DecisionOutcome.REVIEW
            threshold_used = active_policy.review_below
            requires_review = True
        elif critical_conflict and active_policy.require_review_for_conflict:
            outcome = DecisionOutcome.ESCALATE
            threshold_used = active_policy.conflict_escalation_threshold
            requires_review = True
        elif (
            (high_impact or critical_field)
            and active_policy.require_review_for_high_impact
            and confidence < active_policy.auto_approve_at_or_above
        ):
            outcome = DecisionOutcome.REVIEW
            threshold_used = active_policy.auto_approve_at_or_above
            requires_review = True
        elif confidence >= active_policy.auto_approve_at_or_above:
            outcome = DecisionOutcome.AUTO_APPROVE
            threshold_used = active_policy.auto_approve_at_or_above
        else:
            outcome = DecisionOutcome.APPROVE
            threshold_used = active_policy.publish_at_or_above

        if result.active_evidence_count < active_policy.minimum_evidence_count:
            outcome = DecisionOutcome.HOLD
            requires_review = True
        elif result.effective_evidence_weight < active_policy.minimum_effective_weight:
            outcome = DecisionOutcome.HOLD
            requires_review = True

        can_auto_approve = (
            outcome == DecisionOutcome.AUTO_APPROVE
            and not requires_review
            and not critical_conflict
        )
        can_publish = (
            confidence >= active_policy.publish_at_or_above
            and outcome not in {
                DecisionOutcome.REJECT,
                DecisionOutcome.HOLD,
                DecisionOutcome.ESCALATE,
            }
            and (
                not requires_review
                or active_policy.allow_publish_with_review
            )
        )

        review_priority = self._review_priority(
            outcome=outcome,
            confidence=confidence,
            impact=impact_score,
            conflict_score=conflict_score,
        )

        if not reasons:
            reasons.append("Confidence and evidence satisfy the active policy.")

        fingerprint = stable_hash(
            {
                "result_fingerprint": result.fingerprint,
                "policy": active_policy.name,
                "outcome": outcome.value,
                "field_path": field_path,
                "impact": str(impact_score),
            }
        )

        return ConfidenceDecision(
            outcome=outcome,
            review_priority=review_priority,
            confidence=confidence,
            impact=impact_score,
            threshold_used=threshold_used,
            reasons=reasons,
            policy_name=active_policy.name,
            requires_human_review=requires_review,
            can_publish=can_publish,
            can_auto_approve=can_auto_approve,
            fingerprint=fingerprint,
            metadata={
                "field_path": field_path,
                "conflict_score": str(conflict_score),
                "high_impact": high_impact,
                "critical_field": critical_field,
            },
        )

    @staticmethod
    def _review_priority(
        *,
        outcome: DecisionOutcome,
        confidence: Decimal,
        impact: Decimal,
        conflict_score: Decimal,
    ) -> ReviewPriority:
        if outcome == DecisionOutcome.REJECT and impact >= Decimal("0.80"):
            return ReviewPriority.CRITICAL
        if outcome in {DecisionOutcome.ESCALATE, DecisionOutcome.HOLD}:
            if impact >= Decimal("0.75") or conflict_score >= Decimal("0.75"):
                return ReviewPriority.CRITICAL
            return ReviewPriority.HIGH
        if outcome == DecisionOutcome.REVIEW:
            if impact >= Decimal("0.75") or confidence < Decimal("0.45"):
                return ReviewPriority.HIGH
            return ReviewPriority.NORMAL
        if outcome == DecisionOutcome.APPROVE and impact >= Decimal("0.80"):
            return ReviewPriority.LOW
        return ReviewPriority.NONE


# ============================================================
# SECTION 13 - CONFIDENCE ENGINE
# ============================================================

class ConfidenceEngine:
    """
    Main orchestration service for confidence evaluation.

    Processing stages:
    1. Normalize evidence.
    2. Apply provider reliability and freshness.
    3. Detect disagreement and conflicts.
    4. Aggregate raw evidence confidence.
    5. Apply sparsity and conflict penalties.
    6. Estimate uncertainty.
    7. Calibrate the final confidence.
    8. Produce transparent factors and explanations.
    """

    def __init__(
        self,
        *,
        provider_registry: Optional[ProviderReliabilityRegistry] = None,
        freshness_registry: Optional[FreshnessPolicyRegistry] = None,
        aggregator: Optional[EvidenceAggregator] = None,
        conflict_detector: Optional[ConflictDetector] = None,
        uncertainty_estimator: Optional[UncertaintyEstimator] = None,
        calibrator: Optional[ConfidenceCalibrator] = None,
        confidence_bands: Sequence[ConfidenceBand] = DEFAULT_CONFIDENCE_BANDS,
    ) -> None:
        self.provider_registry = provider_registry or ProviderReliabilityRegistry()
        self.freshness_registry = freshness_registry or DEFAULT_FRESHNESS_POLICIES
        self.normalizer = EvidenceNormalizer(
            provider_registry=self.provider_registry,
            freshness_registry=self.freshness_registry,
        )
        self.aggregator = aggregator or EvidenceAggregator()
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.uncertainty_estimator = uncertainty_estimator or UncertaintyEstimator()
        self.calibrator = calibrator or ConfidenceCalibrator()
        self.confidence_bands = tuple(confidence_bands)

    def evaluate(
        self,
        evidence_items: Sequence[EvidenceItem],
        *,
        method: AggregationMethod = AggregationMethod.WEIGHTED_MEAN,
        prior: Decimal = DEFAULT_CONFIDENCE,
        minimum_desired_evidence: int = 2,
        as_of: Optional[datetime] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> ConfidenceResult:
        normalized = [
            self.normalizer.normalize(item, as_of=as_of)
            for item in evidence_items
        ]
        active = [item for item in normalized if item.active]
        conflicts = self.conflict_detector.detect(active)

        raw_score = self.aggregator.aggregate(
            active,
            method=method,
            prior=prior,
        )

        factors: list[ConfidenceFactor] = []
        warnings: list[str] = []

        evidence_factor = self._evidence_volume_factor(
            len(active),
            minimum_desired_evidence,
        )
        factors.append(
            ConfidenceFactor(
                name="evidence_volume",
                score=evidence_factor,
                weight=Decimal("0.15"),
                contribution=evidence_factor * Decimal("0.15"),
                reason=(
                    f"{len(active)} active evidence records were available; "
                    f"{minimum_desired_evidence} were desired."
                ),
            )
        )

        average_reliability = weighted_mean(
            (item.reliability, item.relevance)
            for item in active
        )
        factors.append(
            ConfidenceFactor(
                name="provider_reliability",
                score=average_reliability,
                weight=Decimal("0.20"),
                contribution=average_reliability * Decimal("0.20"),
                reason="Weighted average reliability of contributing providers.",
            )
        )

        average_quality = weighted_mean(
            (item.quality, item.relevance)
            for item in active
        )
        factors.append(
            ConfidenceFactor(
                name="data_quality",
                score=average_quality,
                weight=Decimal("0.20"),
                contribution=average_quality * Decimal("0.20"),
                reason="Weighted average evidence quality.",
            )
        )

        average_freshness = weighted_mean(
            (item.freshness, item.relevance)
            for item in active
        )
        factors.append(
            ConfidenceFactor(
                name="freshness",
                score=average_freshness,
                weight=Decimal("0.15"),
                contribution=average_freshness * Decimal("0.15"),
                reason="Weighted freshness after temporal decay.",
            )
        )

        average_independence = weighted_mean(
            (item.independence, item.relevance)
            for item in active
        )
        factors.append(
            ConfidenceFactor(
                name="independence",
                score=average_independence,
                weight=Decimal("0.10"),
                contribution=average_independence * Decimal("0.10"),
                reason="Independence of evidence sources.",
            )
        )

        conflict_score = max(
            (conflict.disagreement_score for conflict in conflicts),
            default=ZERO,
        )
        agreement_score = clamp_score(ONE - conflict_score)
        factors.append(
            ConfidenceFactor(
                name="agreement",
                score=agreement_score,
                weight=Decimal("0.20"),
                contribution=agreement_score * Decimal("0.20"),
                reason="Agreement across evidence values.",
            )
        )

        structural_score = weighted_mean(
            (factor.score, factor.weight)
            for factor in factors
        )

        score = clamp_score(
            raw_score * Decimal("0.70")
            + structural_score * Decimal("0.30")
        )

        if len(active) < minimum_desired_evidence:
            sparsity_penalty = min(
                Decimal("0.20"),
                Decimal(minimum_desired_evidence - len(active))
                * Decimal("0.05"),
            )
            score = clamp_score(score - sparsity_penalty)
            warnings.append("Evidence volume is below the desired minimum.")

        if conflicts:
            conflict_penalty = conflict_score * Decimal("0.30")
            score = clamp_score(score - conflict_penalty)
            warnings.append("Conflicting evidence reduced the final confidence.")

        effective_weight = sum(
            (item.composite_weight for item in active),
            ZERO,
        )
        if effective_weight < Decimal("0.25"):
            score = min(score, Decimal("0.50"))
            warnings.append("Effective evidence weight is very low.")

        calibrated = self.calibrator.calibrate(score)
        uncertainties = self.uncertainty_estimator.estimate(
            active,
            conflicts,
            aggregated_confidence=calibrated,
        )
        level = self.level_for(calibrated)

        fingerprint = stable_hash(
            {
                "method": method.value,
                "prior": str(prior),
                "score": str(calibrated),
                "evidence": [item.to_dict() for item in normalized],
                "conflicts": [conflict.to_dict() for conflict in conflicts],
                "metadata": dict(metadata or {}),
            }
        )

        explanation = self._explain(
            score=calibrated,
            level=level,
            active_count=len(active),
            total_count=len(normalized),
            conflicts=conflicts,
            average_reliability=average_reliability,
            average_quality=average_quality,
            average_freshness=average_freshness,
        )

        return ConfidenceResult(
            score=calibrated,
            level=level,
            method=method,
            evidence_count=len(normalized),
            active_evidence_count=len(active),
            effective_evidence_weight=quantize_score(effective_weight),
            factors=factors,
            conflicts=conflicts,
            uncertainties=uncertainties,
            explanation=explanation,
            fingerprint=fingerprint,
            warnings=warnings,
            metadata=dict(metadata or {}),
        )

    def evaluate_scalar(
        self,
        confidence_values: Sequence[Any],
        *,
        weights: Optional[Sequence[Any]] = None,
        method: AggregationMethod = AggregationMethod.WEIGHTED_MEAN,
        prior: Decimal = DEFAULT_CONFIDENCE,
    ) -> ConfidenceResult:
        if weights is not None and len(weights) != len(confidence_values):
            raise ValueError("weights must match confidence_values length")

        evidence = []
        for index, value in enumerate(confidence_values):
            weight = (
                clamp_score(weights[index])
                if weights is not None
                else ONE
            )
            evidence.append(
                EvidenceItem(
                    evidence_id=f"scalar-{index}",
                    evidence_type=EvidenceType.DERIVED,
                    source_name="scalar_input",
                    confidence=clamp_score(value),
                    reliability=weight,
                    quality=ONE,
                    freshness=ONE,
                    relevance=ONE,
                    independence=ONE,
                )
            )

        return self.evaluate(
            evidence,
            method=method,
            prior=prior,
            minimum_desired_evidence=1,
        )

    def level_for(self, score: Any) -> ConfidenceLevel:
        normalized = clamp_score(score)
        for band in self.confidence_bands:
            if band.contains(normalized):
                return band.level
        return ConfidenceLevel.UNKNOWN

    @staticmethod
    def _evidence_volume_factor(count: int, desired: int) -> Decimal:
        if desired <= 0:
            return ONE
        return clamp_score(Decimal(count) / Decimal(desired))

    @staticmethod
    def _explain(
        *,
        score: Decimal,
        level: ConfidenceLevel,
        active_count: int,
        total_count: int,
        conflicts: Sequence[ConflictSignal],
        average_reliability: Decimal,
        average_quality: Decimal,
        average_freshness: Decimal,
    ) -> str:
        parts = [
            f"Final confidence is {score} ({level.value}).",
            f"{active_count} of {total_count} evidence records were active.",
            f"Provider reliability averaged {average_reliability}.",
            f"Data quality averaged {average_quality}.",
            f"Freshness averaged {average_freshness}.",
        ]
        if conflicts:
            parts.append(f"{len(conflicts)} conflict group(s) were detected.")
        else:
            parts.append("No material evidence conflicts were detected.")
        return " ".join(parts)


# ============================================================
# SECTION 14 - DOMAIN-SPECIFIC CONFIDENCE BUILDERS
# ============================================================

class PropertyFactConfidenceBuilder:
    def build(
        self,
        *,
        field_path: str,
        source_name: str,
        value: Any,
        source_confidence: Any = DEFAULT_CONFIDENCE,
        quality_score: Any = DEFAULT_CONFIDENCE,
        observed_at: Optional[datetime] = None,
        evidence_id: Optional[str] = None,
        evidence_type: EvidenceType = EvidenceType.PUBLIC_RECORD,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=evidence_id or stable_hash(
                {
                    "field_path": field_path,
                    "source_name": source_name,
                    "value": value,
                    "observed_at": observed_at,
                }
            )[:24],
            evidence_type=evidence_type,
            source_name=source_name,
            value=value,
            confidence=clamp_score(source_confidence),
            quality=clamp_score(quality_score),
            observed_at=observed_at,
            field_path=field_path,
            metadata=dict(metadata or {}),
        )


class ValuationConfidenceBuilder:
    def build(
        self,
        *,
        estimated_value: Any,
        lower_bound: Optional[Any] = None,
        upper_bound: Optional[Any] = None,
        model_confidence: Any = DEFAULT_MODEL_RELIABILITY,
        comparable_count: int = 0,
        feature_completeness: Any = DEFAULT_CONFIDENCE,
        market_freshness: Any = DEFAULT_CONFIDENCE,
        model_reliability: Any = DEFAULT_MODEL_RELIABILITY,
        residual_error_ratio: Optional[Any] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> list[EvidenceItem]:
        estimate = to_decimal(estimated_value)
        if estimate is None or estimate <= ZERO:
            raise ValueError("estimated_value must be positive")

        evidence: list[EvidenceItem] = []

        interval_confidence = self._interval_confidence(
            estimate,
            to_decimal(lower_bound),
            to_decimal(upper_bound),
        )
        evidence.append(
            EvidenceItem(
                evidence_id="valuation-model-confidence",
                evidence_type=EvidenceType.MODEL_OUTPUT,
                source_name="valuation_model",
                value=estimated_value,
                confidence=clamp_score(model_confidence),
                reliability=clamp_score(model_reliability),
                quality=interval_confidence,
                freshness=clamp_score(market_freshness),
                field_path="valuation.estimated_value",
                metadata=dict(metadata or {}),
            )
        )

        comp_confidence = clamp_score(
            Decimal(str(math.log1p(max(comparable_count, 0))))
            / Decimal(str(math.log1p(10)))
        )
        evidence.append(
            EvidenceItem(
                evidence_id="valuation-comparable-support",
                evidence_type=EvidenceType.DERIVED,
                source_name="comparable_analysis",
                value=comparable_count,
                confidence=comp_confidence,
                reliability=Decimal("0.85"),
                quality=clamp_score(feature_completeness),
                freshness=clamp_score(market_freshness),
                field_path="valuation.comparable_support",
            )
        )

        if residual_error_ratio is not None:
            residual = abs(to_decimal(residual_error_ratio, default=ONE) or ONE)
            residual_confidence = clamp_score(ONE - min(residual, ONE))
            evidence.append(
                EvidenceItem(
                    evidence_id="valuation-residual-error",
                    evidence_type=EvidenceType.DERIVED,
                    source_name="model_validation",
                    value=residual_error_ratio,
                    confidence=residual_confidence,
                    reliability=clamp_score(model_reliability),
                    quality=ONE,
                    freshness=ONE,
                    field_path="valuation.residual_error",
                )
            )

        return evidence

    @staticmethod
    def _interval_confidence(
        estimate: Decimal,
        lower_bound: Optional[Decimal],
        upper_bound: Optional[Decimal],
    ) -> Decimal:
        if lower_bound is None or upper_bound is None:
            return DEFAULT_CONFIDENCE
        if lower_bound > upper_bound:
            return ZERO

        width = upper_bound - lower_bound
        width_ratio = safe_divide(width, estimate, default=ONE)
        return clamp_score(ONE - min(width_ratio, ONE))


class ComparableConfidenceBuilder:
    def build(
        self,
        *,
        similarity_score: Any,
        distance_miles: Optional[Any] = None,
        age_days: Optional[int] = None,
        adjustment_ratio: Optional[Any] = None,
        source_name: str = "comparable_engine",
        evidence_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> EvidenceItem:
        similarity_score = clamp_score(similarity_score)

        distance_score = ONE
        if distance_miles is not None:
            distance = max(to_decimal(distance_miles, default=ZERO) or ZERO, ZERO)
            distance_score = clamp_score(
                Decimal(str(math.exp(-float(distance) / 5.0)))
            )

        recency_score = ONE
        if age_days is not None:
            recency_score = clamp_score(
                Decimal(str(math.exp(-max(age_days, 0) / 365.0)))
            )

        adjustment_score = ONE
        if adjustment_ratio is not None:
            adjustment = abs(to_decimal(adjustment_ratio, default=ONE) or ONE)
            adjustment_score = clamp_score(ONE - min(adjustment, ONE))

        confidence = weighted_mean(
            (
                (similarity_score, Decimal("0.50")),
                (distance_score, Decimal("0.20")),
                (recency_score, Decimal("0.20")),
                (adjustment_score, Decimal("0.10")),
            )
        )

        return EvidenceItem(
            evidence_id=evidence_id or stable_hash(
                {
                    "similarity_score": str(similarity_score),
                    "distance_miles": distance_miles,
                    "age_days": age_days,
                    "adjustment_ratio": adjustment_ratio,
                }
            )[:24],
            evidence_type=EvidenceType.DERIVED,
            source_name=source_name,
            confidence=confidence,
            reliability=Decimal("0.85"),
            quality=similarity_score,
            freshness=recency_score,
            relevance=distance_score,
            field_path="valuation.comparable",
            metadata={
                **dict(metadata or {}),
                "distance_score": str(distance_score),
                "recency_score": str(recency_score),
                "adjustment_score": str(adjustment_score),
            },
        )


class ModelPredictionConfidenceBuilder:
    def build(
        self,
        *,
        prediction_confidence: Any,
        model_reliability: Any = DEFAULT_MODEL_RELIABILITY,
        feature_completeness: Any = DEFAULT_CONFIDENCE,
        out_of_distribution_score: Any = ZERO,
        drift_score: Any = ZERO,
        ensemble_agreement: Any = DEFAULT_CONFIDENCE,
        latency_quality: Any = ONE,
        prediction_value: Any = None,
        source_name: str = "model_prediction",
        evidence_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> EvidenceItem:
        ood_penalty = clamp_score(out_of_distribution_score)
        drift_penalty = clamp_score(drift_score)

        confidence = weighted_mean(
            (
                (clamp_score(prediction_confidence), Decimal("0.40")),
                (clamp_score(model_reliability), Decimal("0.20")),
                (clamp_score(feature_completeness), Decimal("0.15")),
                (clamp_score(ensemble_agreement), Decimal("0.15")),
                (clamp_score(latency_quality), Decimal("0.10")),
            )
        )
        confidence = clamp_score(
            confidence
            * (ONE - ood_penalty * Decimal("0.50"))
            * (ONE - drift_penalty * Decimal("0.50"))
        )

        return EvidenceItem(
            evidence_id=evidence_id or stable_hash(
                {
                    "source_name": source_name,
                    "prediction_value": prediction_value,
                    "prediction_confidence": str(prediction_confidence),
                }
            )[:24],
            evidence_type=EvidenceType.MODEL_OUTPUT,
            source_name=source_name,
            value=prediction_value,
            confidence=confidence,
            reliability=clamp_score(model_reliability),
            quality=clamp_score(feature_completeness),
            freshness=clamp_score(ONE - drift_penalty),
            relevance=clamp_score(ONE - ood_penalty),
            field_path="model.prediction",
            metadata={
                **dict(metadata or {}),
                "out_of_distribution_score": str(ood_penalty),
                "drift_score": str(drift_penalty),
                "ensemble_agreement": str(clamp_score(ensemble_agreement)),
            },
        )


# ============================================================
# SECTION 15 - MODEL INTEGRATION HELPERS
# ============================================================

def result_to_model_fields(result: ConfidenceResult) -> dict[str, Any]:
    return {
        "confidence_score": result.score,
        "quality_score": weighted_mean(
            (
                (factor.score, factor.weight)
                for factor in result.factors
                if factor.name in {"data_quality", "freshness", "agreement"}
            )
        ),
        "quality_flags": list(result.warnings),
        "metadata_json": {
            "confidence_engine": result.to_dict(),
        },
    }


def apply_confidence_to_object(
    target: Any,
    result: ConfidenceResult,
    *,
    metadata_attribute: str = "metadata_json",
) -> Any:
    if hasattr(target, "confidence_score"):
        setattr(target, "confidence_score", result.score)

    if hasattr(target, "quality_score"):
        quality = weighted_mean(
            (
                (factor.score, factor.weight)
                for factor in result.factors
                if factor.name in {"data_quality", "freshness", "agreement"}
            )
        )
        setattr(target, "quality_score", quality)

    if hasattr(target, "quality_flags"):
        flags = getattr(target, "quality_flags")
        if isinstance(flags, list):
            flags.extend(
                warning for warning in result.warnings
                if warning not in flags
            )

    metadata = getattr(target, metadata_attribute, None)
    if isinstance(metadata, dict):
        metadata["confidence_engine"] = result.to_dict()

    return target


def evidence_from_model_object(
    obj: Any,
    *,
    evidence_id: Optional[str] = None,
    evidence_type: EvidenceType = EvidenceType.DERIVED,
    source_name: Optional[str] = None,
    field_path: Optional[str] = None,
    value_attribute: Optional[str] = None,
) -> EvidenceItem:
    value = getattr(obj, value_attribute, None) if value_attribute else None
    source = source_name or getattr(obj, "source_name", None) or obj.__class__.__name__

    return EvidenceItem(
        evidence_id=evidence_id or str(getattr(obj, "id", stable_hash(repr(obj))[:24])),
        evidence_type=evidence_type,
        source_name=source,
        value=value,
        confidence=clamp_score(getattr(obj, "confidence_score", DEFAULT_CONFIDENCE)),
        reliability=DEFAULT_PROVIDER_RELIABILITY,
        quality=clamp_score(getattr(obj, "quality_score", DEFAULT_CONFIDENCE)),
        observed_at=getattr(obj, "source_observed_at", None),
        retrieved_at=getattr(obj, "source_retrieved_at", None),
        field_path=field_path,
        metadata={
            "object_type": obj.__class__.__name__,
            "object_id": str(getattr(obj, "id", "")),
        },
    )


# ============================================================
# SECTION 16 - BATCH PROCESSING
# ============================================================

@dataclass(slots=True)
class BatchConfidenceRecord:
    key: str
    result: ConfidenceResult
    decision: Optional[ConfidenceDecision] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "result": self.result.to_dict(),
            "decision": self.decision.to_dict() if self.decision else None,
        }


@dataclass(slots=True)
class BatchConfidenceResult:
    total: int
    average_confidence: Decimal
    minimum_confidence: Decimal
    maximum_confidence: Decimal
    review_count: int
    reject_count: int
    records: list[BatchConfidenceRecord]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "average_confidence": str(self.average_confidence),
            "minimum_confidence": str(self.minimum_confidence),
            "maximum_confidence": str(self.maximum_confidence),
            "review_count": self.review_count,
            "reject_count": self.reject_count,
            "records": [record.to_dict() for record in self.records],
        }


class BatchConfidenceProcessor:
    def __init__(
        self,
        *,
        engine: Optional[ConfidenceEngine] = None,
        decision_engine: Optional[ConfidenceDecisionEngine] = None,
    ) -> None:
        self.engine = engine or ConfidenceEngine()
        self.decision_engine = decision_engine or ConfidenceDecisionEngine()

    def process(
        self,
        groups: Mapping[str, Sequence[EvidenceItem]],
        *,
        method: AggregationMethod = AggregationMethod.WEIGHTED_MEAN,
        policy: Optional[ConfidencePolicy] = None,
        impact_by_key: Optional[Mapping[str, Any]] = None,
        field_path_by_key: Optional[Mapping[str, str]] = None,
    ) -> BatchConfidenceResult:
        records: list[BatchConfidenceRecord] = []

        for key, evidence in groups.items():
            result = self.engine.evaluate(
                evidence,
                method=method,
                metadata={"batch_key": key},
            )
            decision = self.decision_engine.decide(
                result,
                impact=(impact_by_key or {}).get(key, DEFAULT_CONFIDENCE),
                field_path=(field_path_by_key or {}).get(key),
                policy=policy,
            )
            records.append(
                BatchConfidenceRecord(
                    key=key,
                    result=result,
                    decision=decision,
                )
            )

        scores = [record.result.score for record in records]
        average = (
            sum(scores, ZERO) / Decimal(len(scores))
            if scores
            else ZERO
        )

        return BatchConfidenceResult(
            total=len(records),
            average_confidence=clamp_score(average),
            minimum_confidence=min(scores, default=ZERO),
            maximum_confidence=max(scores, default=ZERO),
            review_count=sum(
                1
                for record in records
                if record.decision
                and record.decision.requires_human_review
            ),
            reject_count=sum(
                1
                for record in records
                if record.decision
                and record.decision.outcome == DecisionOutcome.REJECT
            ),
            records=records,
        )


# ============================================================
# SECTION 17 - MONITORING AND QUALITY METRICS
# ============================================================

@dataclass(slots=True)
class ConfidenceMonitoringSnapshot:
    window_start: datetime
    window_end: datetime
    sample_count: int
    mean_confidence: Decimal
    median_confidence: Decimal
    minimum_confidence: Decimal
    maximum_confidence: Decimal
    standard_deviation: Decimal
    review_rate: Decimal
    rejection_rate: Decimal
    conflict_rate: Decimal
    low_confidence_rate: Decimal
    calibration_error: Optional[Decimal] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "sample_count": self.sample_count,
            "mean_confidence": str(self.mean_confidence),
            "median_confidence": str(self.median_confidence),
            "minimum_confidence": str(self.minimum_confidence),
            "maximum_confidence": str(self.maximum_confidence),
            "standard_deviation": str(self.standard_deviation),
            "review_rate": str(self.review_rate),
            "rejection_rate": str(self.rejection_rate),
            "conflict_rate": str(self.conflict_rate),
            "low_confidence_rate": str(self.low_confidence_rate),
            "calibration_error": (
                str(self.calibration_error)
                if self.calibration_error is not None
                else None
            ),
            "metadata": self.metadata,
        }


class ConfidenceMonitor:
    def snapshot(
        self,
        records: Sequence[BatchConfidenceRecord],
        *,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
        calibration_error: Optional[Any] = None,
    ) -> ConfidenceMonitoringSnapshot:
        end = window_end or utcnow()
        start = window_start or (end - timedelta(days=1))

        scores = [float(record.result.score) for record in records]
        if scores:
            mean_value = Decimal(str(statistics.mean(scores)))
            median_value = Decimal(str(statistics.median(scores)))
            minimum_value = Decimal(str(min(scores)))
            maximum_value = Decimal(str(max(scores)))
            std_value = (
                Decimal(str(statistics.pstdev(scores)))
                if len(scores) > 1
                else ZERO
            )
        else:
            mean_value = median_value = minimum_value = maximum_value = std_value = ZERO

        total = Decimal(len(records)) if records else ONE

        review_count = sum(
            1
            for record in records
            if record.decision
            and record.decision.requires_human_review
        )
        reject_count = sum(
            1
            for record in records
            if record.decision
            and record.decision.outcome == DecisionOutcome.REJECT
        )
        conflict_count = sum(
            1
            for record in records
            if record.result.conflicts
        )
        low_count = sum(
            1
            for record in records
            if record.result.score < Decimal("0.65")
        )

        return ConfidenceMonitoringSnapshot(
            window_start=start,
            window_end=end,
            sample_count=len(records),
            mean_confidence=clamp_score(mean_value),
            median_confidence=clamp_score(median_value),
            minimum_confidence=clamp_score(minimum_value),
            maximum_confidence=clamp_score(maximum_value),
            standard_deviation=quantize_score(std_value),
            review_rate=clamp_score(Decimal(review_count) / total),
            rejection_rate=clamp_score(Decimal(reject_count) / total),
            conflict_rate=clamp_score(Decimal(conflict_count) / total),
            low_confidence_rate=clamp_score(Decimal(low_count) / total),
            calibration_error=(
                clamp_score(calibration_error)
                if calibration_error is not None
                else None
            ),
        )


# ============================================================
# SECTION 18 - DEFAULT ENGINE AND CONVENIENCE API
# ============================================================

_default_engine = ConfidenceEngine()
_default_decision_engine = ConfidenceDecisionEngine()


def evaluate_confidence(
    evidence_items: Sequence[EvidenceItem],
    *,
    method: AggregationMethod = AggregationMethod.WEIGHTED_MEAN,
    prior: Decimal = DEFAULT_CONFIDENCE,
    minimum_desired_evidence: int = 2,
    as_of: Optional[datetime] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> ConfidenceResult:
    return _default_engine.evaluate(
        evidence_items,
        method=method,
        prior=prior,
        minimum_desired_evidence=minimum_desired_evidence,
        as_of=as_of,
        metadata=metadata,
    )


def decide_confidence(
    result: ConfidenceResult,
    *,
    impact: Any = DEFAULT_CONFIDENCE,
    field_path: Optional[str] = None,
    policy: Optional[ConfidencePolicy] = None,
) -> ConfidenceDecision:
    return _default_decision_engine.decide(
        result,
        impact=impact,
        field_path=field_path,
        policy=policy,
    )


def combine_confidences(
    values: Sequence[Any],
    *,
    weights: Optional[Sequence[Any]] = None,
    method: AggregationMethod = AggregationMethod.WEIGHTED_MEAN,
) -> Decimal:
    return _default_engine.evaluate_scalar(
        values,
        weights=weights,
        method=method,
    ).score


def confidence_level(score: Any) -> ConfidenceLevel:
    return _default_engine.level_for(score)


# ============================================================
# SECTION 19 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    # constants and helpers
    "DEFAULT_CONFIDENCE",
    "DEFAULT_PROVIDER_RELIABILITY",
    "DEFAULT_MODEL_RELIABILITY",
    "clamp_score",
    "weighted_mean",
    "geometric_mean",
    "harmonic_mean",
    "stable_hash",
    "sigmoid",
    "logit",
    "entropy_binary",
    "normalized_entropy",
    "percentile",
    "median_absolute_deviation",
    # enums
    "ConfidenceLevel",
    "EvidenceType",
    "EvidenceStatus",
    "DecisionOutcome",
    "ReviewPriority",
    "ConflictSeverity",
    "CalibrationMethod",
    "AggregationMethod",
    "UncertaintyType",
    "PolicyMode",
    "ImpactLevel",
    # data contracts
    "ConfidenceBand",
    "EvidenceItem",
    "ConfidenceFactor",
    "ConflictSignal",
    "UncertaintyEstimate",
    "ConfidenceResult",
    "ConfidenceDecision",
    "CalibrationPoint",
    "CalibrationReport",
    "ProviderReliabilityProfile",
    "FreshnessPolicy",
    "ConfidencePolicy",
    "BatchConfidenceRecord",
    "BatchConfidenceResult",
    "ConfidenceMonitoringSnapshot",
    # services
    "ProviderReliabilityRegistry",
    "FreshnessPolicyRegistry",
    "EvidenceNormalizer",
    "GenericValueComparator",
    "ConflictDetector",
    "EvidenceAggregator",
    "UncertaintyEstimator",
    "ConfidenceCalibrator",
    "ConfidenceDecisionEngine",
    "ConfidenceEngine",
    "PropertyFactConfidenceBuilder",
    "ValuationConfidenceBuilder",
    "ComparableConfidenceBuilder",
    "ModelPredictionConfidenceBuilder",
    "BatchConfidenceProcessor",
    "ConfidenceMonitor",
    # integration and convenience
    "result_to_model_fields",
    "apply_confidence_to_object",
    "evidence_from_model_object",
    "default_policy",
    "evaluate_confidence",
    "decide_confidence",
    "combine_confidences",
    "confidence_level",
]
