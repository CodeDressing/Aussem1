"""
============================================================
AUSSEM REAL ESTATE
PHASE 5.30 - SOURCE EXPLANATION ENGINE
FILE: app/property_intelligence/source_explanation_engine.py

PURPOSE:
Enterprise provenance, source attribution, evidence lineage, citation
assembly, conflict explanation, confidence rationale, model-output
explanation, and user-facing "why this result" reporting for the Aussem
Real Estate property-intelligence platform.

DESIGN PRINCIPLES:
1. Every material result should be explainable.
2. Every explanation should identify supporting and conflicting sources.
3. Every source should retain provenance and lineage.
4. User-facing narratives should remain grounded in machine-readable facts.
5. Confidence, disagreement, freshness, and quality must be explicit.
6. The engine must work without external APIs.
7. The engine must integrate without circular imports.
8. Outputs must support APIs, audit logs, reports, and UI rendering.
9. All explanations must be deterministic and reproducible.
10. No fabricated citations or unsupported claims.
============================================================
"""

from __future__ import annotations

import enum
import hashlib
import json
import math
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Optional, Protocol, Sequence


# ============================================================
# SECTION 01 - CONSTANTS
# ============================================================

ZERO = Decimal("0")
ONE = Decimal("1")
HALF = Decimal("0.5")
SCORE_QUANTUM = Decimal("0.000001")

DEFAULT_SOURCE_RELIABILITY = Decimal("0.60")
DEFAULT_EXPLANATION_CONFIDENCE = Decimal("0.50")
DEFAULT_MAX_CITATIONS = 10
DEFAULT_MAX_SUPPORTING_FACTS = 12
DEFAULT_MAX_CONFLICTS = 8
DEFAULT_MAX_LINEAGE_DEPTH = 12

WHITESPACE_RE = re.compile(r"\s+")
SAFE_IDENTIFIER_RE = re.compile(r"[^A-Za-z0-9_.:\-/]+")


# ============================================================
# SECTION 02 - GENERIC HELPERS
# ============================================================

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_decimal(value: Any, default: Decimal = ZERO) -> Decimal:
    if value is None or value == "":
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return default


def clamp_score(value: Any) -> Decimal:
    number = to_decimal(value)
    number = max(ZERO, min(ONE, number))
    return number.quantize(SCORE_QUANTUM, rounding=ROUND_HALF_UP)


def weighted_mean(
    values: Iterable[tuple[Any, Any]],
    *,
    default: Decimal = DEFAULT_EXPLANATION_CONFIDENCE,
) -> Decimal:
    numerator = ZERO
    denominator = ZERO

    for value, weight in values:
        decimal_value = to_decimal(value)
        decimal_weight = to_decimal(weight)
        if decimal_weight <= ZERO:
            continue
        numerator += decimal_value * decimal_weight
        denominator += decimal_weight

    if denominator == ZERO:
        return clamp_score(default)
    return clamp_score(numerator / denominator)


def stable_hash(value: Any) -> str:
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return WHITESPACE_RE.sub(" ", str(value).strip())


def safe_identifier(value: Any) -> str:
    normalized = SAFE_IDENTIFIER_RE.sub("-", normalize_text(value))
    return normalized.strip("-") or "unknown"


def isoformat_or_none(value: Any) -> Optional[str]:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return None


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


def sentence_join(parts: Iterable[str]) -> str:
    values = [normalize_text(part) for part in parts if normalize_text(part)]
    return " ".join(
        value if value.endswith((".", "!", "?")) else f"{value}."
        for value in values
    )


# ============================================================
# SECTION 03 - ENUMERATIONS
# ============================================================

class StringEnum(str, enum.Enum):
    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]


class SourceCategory(StringEnum):
    MLS = "mls"
    PUBLIC_RECORD = "public_record"
    TAX_ASSESSOR = "tax_assessor"
    DEED = "deed"
    COUNTY = "county"
    MUNICIPAL = "municipal"
    STATE = "state"
    FEDERAL = "federal"
    GEOSPATIAL = "geospatial"
    PROPERTY_PROVIDER = "property_provider"
    USER = "user"
    BROKER = "broker"
    INTERNAL = "internal"
    MODEL = "model"
    DERIVED = "derived"
    MANUAL_REVIEW = "manual_review"
    OTHER = "other"


class SourceAuthority(StringEnum):
    PRIMARY = "primary"
    OFFICIAL = "official"
    AUTHORITATIVE = "authoritative"
    SECONDARY = "secondary"
    DERIVED = "derived"
    USER_SUPPLIED = "user_supplied"
    UNKNOWN = "unknown"


class CitationType(StringEnum):
    RECORD = "record"
    URL = "url"
    DOCUMENT = "document"
    DATASET = "dataset"
    MODEL = "model"
    CALCULATION = "calculation"
    HUMAN_REVIEW = "human_review"
    INTERNAL_EVENT = "internal_event"


class ClaimType(StringEnum):
    FACT = "fact"
    ESTIMATE = "estimate"
    PREDICTION = "prediction"
    INFERENCE = "inference"
    RISK = "risk"
    MARKET = "market"
    VALUATION = "valuation"
    COMPARABLE = "comparable"
    ADDRESS = "address"
    OWNERSHIP = "ownership"
    TAX = "tax"
    OTHER = "other"


class SupportDirection(StringEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    PARTIALLY_SUPPORTS = "partially_supports"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class ExplanationAudience(StringEnum):
    CONSUMER = "consumer"
    SELLER = "seller"
    BUYER = "buyer"
    BROKER = "broker"
    ANALYST = "analyst"
    ADMIN = "admin"
    AUDITOR = "auditor"
    MODEL_DEVELOPER = "model_developer"


class ExplanationDepth(StringEnum):
    SUMMARY = "summary"
    STANDARD = "standard"
    DETAILED = "detailed"
    AUDIT = "audit"


class ExplanationTone(StringEnum):
    PLAIN = "plain"
    PROFESSIONAL = "professional"
    TECHNICAL = "technical"
    REGULATORY = "regulatory"


class ConflictResolutionStatus(StringEnum):
    UNRESOLVED = "unresolved"
    AUTO_RESOLVED = "auto_resolved"
    HUMAN_RESOLVED = "human_resolved"
    DEFERRED = "deferred"
    REJECTED = "rejected"


class LineageNodeType(StringEnum):
    SOURCE = "source"
    RECORD = "record"
    OBSERVATION = "observation"
    FEATURE = "feature"
    MODEL = "model"
    PREDICTION = "prediction"
    VALUATION = "valuation"
    REPORT = "report"
    REVIEW = "review"
    TRANSFORMATION = "transformation"
    CLAIM = "claim"


class LineageEdgeType(StringEnum):
    PRODUCED = "produced"
    DERIVED_FROM = "derived_from"
    TRANSFORMED_INTO = "transformed_into"
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    REVIEWED = "reviewed"
    SUPERSEDED = "superseded"
    USED_BY = "used_by"


class ExplanationStatus(StringEnum):
    DRAFT = "draft"
    COMPLETE = "complete"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    INVALID = "invalid"


# ============================================================
# SECTION 04 - SOURCE AND CITATION DATA CONTRACTS
# ============================================================

@dataclass(slots=True)
class SourceDescriptor:
    source_id: str
    source_name: str
    category: SourceCategory = SourceCategory.OTHER
    authority: SourceAuthority = SourceAuthority.UNKNOWN
    provider_name: Optional[str] = None
    record_id: Optional[str] = None
    record_type: Optional[str] = None
    source_url: Optional[str] = None
    document_name: Optional[str] = None
    dataset_name: Optional[str] = None
    jurisdiction: Optional[str] = None
    observed_at: Optional[datetime] = None
    retrieved_at: Optional[datetime] = None
    effective_at: Optional[datetime] = None
    reliability: Decimal = DEFAULT_SOURCE_RELIABILITY
    quality: Decimal = DEFAULT_EXPLANATION_CONFIDENCE
    freshness: Decimal = DEFAULT_EXPLANATION_CONFIDENCE
    license_name: Optional[str] = None
    terms_version: Optional[str] = None
    payload_hash: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def composite_score(self) -> Decimal:
        authority_weight = {
            SourceAuthority.PRIMARY: Decimal("1.00"),
            SourceAuthority.OFFICIAL: Decimal("0.95"),
            SourceAuthority.AUTHORITATIVE: Decimal("0.90"),
            SourceAuthority.SECONDARY: Decimal("0.72"),
            SourceAuthority.DERIVED: Decimal("0.62"),
            SourceAuthority.USER_SUPPLIED: Decimal("0.55"),
            SourceAuthority.UNKNOWN: Decimal("0.45"),
        }[self.authority]

        return weighted_mean(
            (
                (self.reliability, Decimal("0.35")),
                (self.quality, Decimal("0.25")),
                (self.freshness, Decimal("0.20")),
                (authority_weight, Decimal("0.20")),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "category": self.category.value,
            "authority": self.authority.value,
            "provider_name": self.provider_name,
            "record_id": self.record_id,
            "record_type": self.record_type,
            "source_url": self.source_url,
            "document_name": self.document_name,
            "dataset_name": self.dataset_name,
            "jurisdiction": self.jurisdiction,
            "observed_at": isoformat_or_none(self.observed_at),
            "retrieved_at": isoformat_or_none(self.retrieved_at),
            "effective_at": isoformat_or_none(self.effective_at),
            "reliability": str(clamp_score(self.reliability)),
            "quality": str(clamp_score(self.quality)),
            "freshness": str(clamp_score(self.freshness)),
            "composite_score": str(self.composite_score),
            "license_name": self.license_name,
            "terms_version": self.terms_version,
            "payload_hash": self.payload_hash,
            "metadata": serialize_value(self.metadata),
        }


@dataclass(slots=True)
class Citation:
    citation_id: str
    citation_type: CitationType
    source: SourceDescriptor
    label: str
    locator: Optional[str] = None
    excerpt: Optional[str] = None
    field_path: Optional[str] = None
    value: Any = None
    confidence: Decimal = DEFAULT_EXPLANATION_CONFIDENCE
    relevance: Decimal = ONE
    support_direction: SupportDirection = SupportDirection.SUPPORTS
    created_at: datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def rank_score(self) -> Decimal:
        direction_weight = {
            SupportDirection.SUPPORTS: Decimal("1.00"),
            SupportDirection.PARTIALLY_SUPPORTS: Decimal("0.80"),
            SupportDirection.NEUTRAL: Decimal("0.60"),
            SupportDirection.CONTRADICTS: Decimal("0.75"),
            SupportDirection.UNKNOWN: Decimal("0.50"),
        }[self.support_direction]

        return weighted_mean(
            (
                (self.source.composite_score, Decimal("0.45")),
                (self.confidence, Decimal("0.25")),
                (self.relevance, Decimal("0.20")),
                (direction_weight, Decimal("0.10")),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "citation_id": self.citation_id,
            "citation_type": self.citation_type.value,
            "source": self.source.to_dict(),
            "label": self.label,
            "locator": self.locator,
            "excerpt": self.excerpt,
            "field_path": self.field_path,
            "value": serialize_value(self.value),
            "confidence": str(clamp_score(self.confidence)),
            "relevance": str(clamp_score(self.relevance)),
            "support_direction": self.support_direction.value,
            "rank_score": str(self.rank_score),
            "created_at": self.created_at.isoformat(),
            "metadata": serialize_value(self.metadata),
        }


# ============================================================
# SECTION 05 - CLAIMS, SUPPORT, AND CONFLICTS
# ============================================================

@dataclass(slots=True)
class Claim:
    claim_id: str
    statement: str
    claim_type: ClaimType
    field_path: Optional[str] = None
    value: Any = None
    unit: Optional[str] = None
    currency_code: Optional[str] = None
    confidence: Decimal = DEFAULT_EXPLANATION_CONFIDENCE
    effective_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "claim_type": self.claim_type.value,
            "field_path": self.field_path,
            "value": serialize_value(self.value),
            "unit": self.unit,
            "currency_code": self.currency_code,
            "confidence": str(clamp_score(self.confidence)),
            "effective_at": isoformat_or_none(self.effective_at),
            "metadata": serialize_value(self.metadata),
        }


@dataclass(slots=True)
class ClaimSupport:
    claim_id: str
    citation_id: str
    direction: SupportDirection
    strength: Decimal
    rationale: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "citation_id": self.citation_id,
            "direction": self.direction.value,
            "strength": str(clamp_score(self.strength)),
            "rationale": self.rationale,
            "metadata": serialize_value(self.metadata),
        }


@dataclass(slots=True)
class SourceConflict:
    conflict_id: str
    field_path: Optional[str]
    claim_id: Optional[str]
    source_ids: list[str]
    citation_ids: list[str]
    values: list[Any]
    disagreement_score: Decimal
    status: ConflictResolutionStatus = ConflictResolutionStatus.UNRESOLVED
    winning_source_id: Optional[str] = None
    winning_value: Any = None
    resolution_reason: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def severity_label(self) -> str:
        score = clamp_score(self.disagreement_score)
        if score >= Decimal("0.80"):
            return "critical"
        if score >= Decimal("0.60"):
            return "high"
        if score >= Decimal("0.35"):
            return "moderate"
        if score > ZERO:
            return "low"
        return "none"

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "field_path": self.field_path,
            "claim_id": self.claim_id,
            "source_ids": list(self.source_ids),
            "citation_ids": list(self.citation_ids),
            "values": serialize_value(self.values),
            "disagreement_score": str(clamp_score(self.disagreement_score)),
            "severity_label": self.severity_label,
            "status": self.status.value,
            "winning_source_id": self.winning_source_id,
            "winning_value": serialize_value(self.winning_value),
            "resolution_reason": self.resolution_reason,
            "resolved_by": self.resolved_by,
            "resolved_at": isoformat_or_none(self.resolved_at),
            "metadata": serialize_value(self.metadata),
        }


# ============================================================
# SECTION 06 - LINEAGE GRAPH CONTRACTS
# ============================================================

@dataclass(slots=True)
class LineageNode:
    node_id: str
    node_type: LineageNodeType
    label: str
    entity_id: Optional[str] = None
    field_path: Optional[str] = None
    payload_hash: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "label": self.label,
            "entity_id": self.entity_id,
            "field_path": self.field_path,
            "payload_hash": self.payload_hash,
            "created_at": isoformat_or_none(self.created_at),
            "metadata": serialize_value(self.metadata),
        }


@dataclass(slots=True)
class LineageEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: LineageEdgeType
    transformation: Optional[str] = None
    confidence: Decimal = DEFAULT_EXPLANATION_CONFIDENCE
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "edge_type": self.edge_type.value,
            "transformation": self.transformation,
            "confidence": str(clamp_score(self.confidence)),
            "metadata": serialize_value(self.metadata),
        }


@dataclass(slots=True)
class LineageGraph:
    nodes: dict[str, LineageNode] = field(default_factory=dict)
    edges: dict[str, LineageEdge] = field(default_factory=dict)

    def add_node(self, node: LineageNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: LineageEdge) -> None:
        if edge.source_node_id not in self.nodes:
            raise ValueError(f"unknown lineage source node: {edge.source_node_id}")
        if edge.target_node_id not in self.nodes:
            raise ValueError(f"unknown lineage target node: {edge.target_node_id}")
        self.edges[edge.edge_id] = edge

    def parents(self, node_id: str) -> list[LineageNode]:
        parent_ids = [
            edge.source_node_id
            for edge in self.edges.values()
            if edge.target_node_id == node_id
        ]
        return [self.nodes[parent_id] for parent_id in parent_ids if parent_id in self.nodes]

    def children(self, node_id: str) -> list[LineageNode]:
        child_ids = [
            edge.target_node_id
            for edge in self.edges.values()
            if edge.source_node_id == node_id
        ]
        return [self.nodes[child_id] for child_id in child_ids if child_id in self.nodes]

    def ancestors(
        self,
        node_id: str,
        *,
        maximum_depth: int = DEFAULT_MAX_LINEAGE_DEPTH,
    ) -> list[LineageNode]:
        visited: set[str] = set()
        output: list[LineageNode] = []
        frontier: list[tuple[str, int]] = [(node_id, 0)]

        while frontier:
            current_id, depth = frontier.pop(0)
            if depth >= maximum_depth:
                continue

            for parent in self.parents(current_id):
                if parent.node_id in visited:
                    continue
                visited.add(parent.node_id)
                output.append(parent)
                frontier.append((parent.node_id, depth + 1))

        return output

    def trace(
        self,
        node_id: str,
        *,
        maximum_depth: int = DEFAULT_MAX_LINEAGE_DEPTH,
    ) -> dict[str, Any]:
        if node_id not in self.nodes:
            raise ValueError(f"unknown lineage node: {node_id}")

        ancestors = self.ancestors(node_id, maximum_depth=maximum_depth)
        ancestor_ids = {node.node_id for node in ancestors}
        ancestor_ids.add(node_id)

        edges = [
            edge
            for edge in self.edges.values()
            if edge.source_node_id in ancestor_ids
            and edge.target_node_id in ancestor_ids
        ]

        return {
            "target": self.nodes[node_id].to_dict(),
            "ancestors": [node.to_dict() for node in ancestors],
            "edges": [edge.to_dict() for edge in edges],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges.values()],
        }


# ============================================================
# SECTION 07 - EXPLANATION OPTIONS AND OUTPUTS
# ============================================================

@dataclass(slots=True)
class ExplanationOptions:
    audience: ExplanationAudience = ExplanationAudience.CONSUMER
    depth: ExplanationDepth = ExplanationDepth.STANDARD
    tone: ExplanationTone = ExplanationTone.PROFESSIONAL
    include_sources: bool = True
    include_conflicts: bool = True
    include_confidence: bool = True
    include_lineage: bool = False
    include_limitations: bool = True
    max_citations: int = DEFAULT_MAX_CITATIONS
    max_supporting_facts: int = DEFAULT_MAX_SUPPORTING_FACTS
    max_conflicts: int = DEFAULT_MAX_CONFLICTS
    redact_internal_metadata: bool = True
    currency_code: str = "USD"
    locale: str = "en-US"


@dataclass(slots=True)
class ExplanationSection:
    section_id: str
    title: str
    narrative: str
    claims: list[Claim] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    conflicts: list[SourceConflict] = field(default_factory=list)
    confidence: Optional[Decimal] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "narrative": self.narrative,
            "claims": [claim.to_dict() for claim in self.claims],
            "citations": [citation.to_dict() for citation in self.citations],
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
            "confidence": str(self.confidence) if self.confidence is not None else None,
            "metadata": serialize_value(self.metadata),
        }


@dataclass(slots=True)
class ExplanationReport:
    report_id: str
    subject_type: str
    subject_id: str
    title: str
    summary: str
    status: ExplanationStatus
    confidence: Decimal
    sections: list[ExplanationSection]
    citations: list[Citation]
    claims: list[Claim]
    conflicts: list[SourceConflict]
    limitations: list[str]
    lineage: Optional[LineageGraph]
    generated_at: datetime
    fingerprint: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "title": self.title,
            "summary": self.summary,
            "status": self.status.value,
            "confidence": str(clamp_score(self.confidence)),
            "sections": [section.to_dict() for section in self.sections],
            "citations": [citation.to_dict() for citation in self.citations],
            "claims": [claim.to_dict() for claim in self.claims],
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
            "limitations": list(self.limitations),
            "lineage": self.lineage.to_dict() if self.lineage else None,
            "generated_at": self.generated_at.isoformat(),
            "fingerprint": self.fingerprint,
            "metadata": serialize_value(self.metadata),
        }


# ============================================================
# SECTION 08 - SOURCE RANKING
# ============================================================

class SourceRanker:
    AUTHORITY_WEIGHT: Mapping[SourceAuthority, Decimal] = {
        SourceAuthority.PRIMARY: Decimal("1.00"),
        SourceAuthority.OFFICIAL: Decimal("0.95"),
        SourceAuthority.AUTHORITATIVE: Decimal("0.90"),
        SourceAuthority.SECONDARY: Decimal("0.70"),
        SourceAuthority.DERIVED: Decimal("0.60"),
        SourceAuthority.USER_SUPPLIED: Decimal("0.50"),
        SourceAuthority.UNKNOWN: Decimal("0.40"),
    }

    CATEGORY_WEIGHT: Mapping[SourceCategory, Decimal] = {
        SourceCategory.DEED: Decimal("1.00"),
        SourceCategory.COUNTY: Decimal("0.96"),
        SourceCategory.TAX_ASSESSOR: Decimal("0.95"),
        SourceCategory.MUNICIPAL: Decimal("0.93"),
        SourceCategory.STATE: Decimal("0.93"),
        SourceCategory.FEDERAL: Decimal("0.93"),
        SourceCategory.MLS: Decimal("0.90"),
        SourceCategory.GEOSPATIAL: Decimal("0.86"),
        SourceCategory.PUBLIC_RECORD: Decimal("0.85"),
        SourceCategory.PROPERTY_PROVIDER: Decimal("0.72"),
        SourceCategory.BROKER: Decimal("0.70"),
        SourceCategory.MANUAL_REVIEW: Decimal("0.88"),
        SourceCategory.INTERNAL: Decimal("0.75"),
        SourceCategory.MODEL: Decimal("0.65"),
        SourceCategory.DERIVED: Decimal("0.62"),
        SourceCategory.USER: Decimal("0.50"),
        SourceCategory.OTHER: Decimal("0.45"),
    }

    def score(self, source: SourceDescriptor) -> Decimal:
        return weighted_mean(
            (
                (source.reliability, Decimal("0.25")),
                (source.quality, Decimal("0.20")),
                (source.freshness, Decimal("0.15")),
                (self.AUTHORITY_WEIGHT[source.authority], Decimal("0.20")),
                (self.CATEGORY_WEIGHT[source.category], Decimal("0.20")),
            )
        )

    def rank(self, sources: Iterable[SourceDescriptor]) -> list[SourceDescriptor]:
        return sorted(
            sources,
            key=lambda source: (
                self.score(source),
                source.source_name,
                source.source_id,
            ),
            reverse=True,
        )


# ============================================================
# SECTION 09 - CITATION BUILDER
# ============================================================

class CitationBuilder:
    def build(
        self,
        *,
        source: SourceDescriptor,
        label: Optional[str] = None,
        citation_type: Optional[CitationType] = None,
        locator: Optional[str] = None,
        excerpt: Optional[str] = None,
        field_path: Optional[str] = None,
        value: Any = None,
        confidence: Any = DEFAULT_EXPLANATION_CONFIDENCE,
        relevance: Any = ONE,
        support_direction: SupportDirection = SupportDirection.SUPPORTS,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Citation:
        resolved_type = citation_type or self._infer_type(source)
        resolved_label = label or self._default_label(source)

        citation_id = stable_hash(
            {
                "source_id": source.source_id,
                "citation_type": resolved_type.value,
                "locator": locator,
                "field_path": field_path,
                "value": serialize_value(value),
                "support_direction": support_direction.value,
            }
        )[:24]

        return Citation(
            citation_id=citation_id,
            citation_type=resolved_type,
            source=source,
            label=resolved_label,
            locator=locator,
            excerpt=normalize_text(excerpt) or None,
            field_path=field_path,
            value=value,
            confidence=clamp_score(confidence),
            relevance=clamp_score(relevance),
            support_direction=support_direction,
            metadata=dict(metadata or {}),
        )

    @staticmethod
    def _infer_type(source: SourceDescriptor) -> CitationType:
        if source.source_url:
            return CitationType.URL
        if source.document_name:
            return CitationType.DOCUMENT
        if source.dataset_name:
            return CitationType.DATASET
        if source.category == SourceCategory.MODEL:
            return CitationType.MODEL
        if source.category == SourceCategory.MANUAL_REVIEW:
            return CitationType.HUMAN_REVIEW
        return CitationType.RECORD

    @staticmethod
    def _default_label(source: SourceDescriptor) -> str:
        parts = [source.source_name]
        if source.record_type:
            parts.append(source.record_type)
        if source.record_id:
            parts.append(source.record_id)
        return " - ".join(parts)


# ============================================================
# SECTION 10 - CLAIM SUPPORT EVALUATION
# ============================================================

class ClaimSupportEvaluator:
    def evaluate(
        self,
        claim: Claim,
        citation: Citation,
    ) -> ClaimSupport:
        direction = citation.support_direction

        if direction == SupportDirection.UNKNOWN:
            direction = self._infer_direction(claim.value, citation.value)

        strength = weighted_mean(
            (
                (citation.confidence, Decimal("0.35")),
                (citation.relevance, Decimal("0.30")),
                (citation.source.composite_score, Decimal("0.35")),
            )
        )

        rationale = self._rationale(claim, citation, direction, strength)

        return ClaimSupport(
            claim_id=claim.claim_id,
            citation_id=citation.citation_id,
            direction=direction,
            strength=strength,
            rationale=rationale,
        )

    @staticmethod
    def _infer_direction(claim_value: Any, citation_value: Any) -> SupportDirection:
        if claim_value is None or citation_value is None:
            return SupportDirection.NEUTRAL

        if str(claim_value).strip().upper() == str(citation_value).strip().upper():
            return SupportDirection.SUPPORTS

        claim_number = ClaimSupportEvaluator._to_number(claim_value)
        citation_number = ClaimSupportEvaluator._to_number(citation_value)

        if claim_number is not None and citation_number is not None:
            denominator = max(abs(claim_number), abs(citation_number), ONE)
            relative_difference = abs(claim_number - citation_number) / denominator
            if relative_difference <= Decimal("0.02"):
                return SupportDirection.SUPPORTS
            if relative_difference <= Decimal("0.10"):
                return SupportDirection.PARTIALLY_SUPPORTS
            return SupportDirection.CONTRADICTS

        return SupportDirection.CONTRADICTS

    @staticmethod
    def _to_number(value: Any) -> Optional[Decimal]:
        try:
            return Decimal(str(value))
        except Exception:
            return None

    @staticmethod
    def _rationale(
        claim: Claim,
        citation: Citation,
        direction: SupportDirection,
        strength: Decimal,
    ) -> str:
        source_name = citation.source.source_name
        if direction == SupportDirection.SUPPORTS:
            return f"{source_name} directly supports the claim with strength {strength}."
        if direction == SupportDirection.PARTIALLY_SUPPORTS:
            return f"{source_name} partially supports the claim with strength {strength}."
        if direction == SupportDirection.CONTRADICTS:
            return f"{source_name} conflicts with the claim with strength {strength}."
        if direction == SupportDirection.NEUTRAL:
            return f"{source_name} is relevant but does not directly establish the claim."
        return f"Support from {source_name} could not be determined."


# ============================================================
# SECTION 11 - CONFLICT DETECTION AND RESOLUTION
# ============================================================

class SourceConflictDetector:
    def detect(
        self,
        *,
        claim: Optional[Claim],
        citations: Sequence[Citation],
        disagreement_threshold: Decimal = Decimal("0.10"),
    ) -> list[SourceConflict]:
        grouped: MutableMapping[Optional[str], list[Citation]] = defaultdict(list)
        for citation in citations:
            grouped[citation.field_path].append(citation)

        conflicts: list[SourceConflict] = []

        for field_path, field_citations in grouped.items():
            usable = [
                citation
                for citation in field_citations
                if citation.value is not None
            ]
            if len(usable) < 2:
                continue

            maximum_disagreement = ZERO
            involved: set[str] = set()
            source_ids: set[str] = set()
            values: list[Any] = []

            for index, left in enumerate(usable):
                for right in usable[index + 1:]:
                    disagreement = self._disagreement(left.value, right.value)
                    if disagreement >= disagreement_threshold:
                        maximum_disagreement = max(maximum_disagreement, disagreement)
                        involved.update((left.citation_id, right.citation_id))
                        source_ids.update((left.source.source_id, right.source.source_id))
                        values.extend((left.value, right.value))

            if not involved:
                continue

            conflict_id = stable_hash(
                {
                    "field_path": field_path,
                    "claim_id": claim.claim_id if claim else None,
                    "citation_ids": sorted(involved),
                }
            )[:24]

            conflicts.append(
                SourceConflict(
                    conflict_id=conflict_id,
                    field_path=field_path,
                    claim_id=claim.claim_id if claim else None,
                    source_ids=sorted(source_ids),
                    citation_ids=sorted(involved),
                    values=list(dict.fromkeys(str(value) for value in values)),
                    disagreement_score=clamp_score(maximum_disagreement),
                )
            )

        return conflicts

    @staticmethod
    def _disagreement(left: Any, right: Any) -> Decimal:
        try:
            left_number = Decimal(str(left))
            right_number = Decimal(str(right))
            denominator = max(abs(left_number), abs(right_number), ONE)
            return clamp_score(abs(left_number - right_number) / denominator)
        except Exception:
            left_text = normalize_text(left).upper()
            right_text = normalize_text(right).upper()
            if left_text == right_text:
                return ZERO

            left_tokens = set(left_text.split())
            right_tokens = set(right_text.split())
            union = left_tokens | right_tokens
            if not union:
                return ZERO
            similarity = Decimal(len(left_tokens & right_tokens)) / Decimal(len(union))
            return clamp_score(ONE - similarity)


class SourceConflictResolver:
    def __init__(self, *, source_ranker: Optional[SourceRanker] = None) -> None:
        self.source_ranker = source_ranker or SourceRanker()

    def resolve(
        self,
        conflict: SourceConflict,
        citations: Sequence[Citation],
        *,
        minimum_margin: Decimal = Decimal("0.08"),
    ) -> SourceConflict:
        relevant = [
            citation
            for citation in citations
            if citation.citation_id in conflict.citation_ids
        ]
        if not relevant:
            return conflict

        ranked = sorted(
            relevant,
            key=lambda citation: citation.rank_score,
            reverse=True,
        )
        winner = ranked[0]
        runner_up_score = ranked[1].rank_score if len(ranked) > 1 else ZERO
        margin = winner.rank_score - runner_up_score

        if margin < minimum_margin:
            conflict.status = ConflictResolutionStatus.DEFERRED
            conflict.resolution_reason = (
                "No source exceeded the next-best source by the required authority margin."
            )
            return conflict

        conflict.status = ConflictResolutionStatus.AUTO_RESOLVED
        conflict.winning_source_id = winner.source.source_id
        conflict.winning_value = winner.value
        conflict.resolution_reason = (
            f"{winner.source.source_name} ranked highest based on authority, "
            "quality, freshness, reliability, and relevance."
        )
        conflict.resolved_by = "source_explanation_engine"
        conflict.resolved_at = utcnow()
        return conflict


# ============================================================
# SECTION 12 - LINEAGE BUILDER
# ============================================================

class LineageBuilder:
    def build_for_claim(
        self,
        *,
        claim: Claim,
        citations: Sequence[Citation],
        supports: Sequence[ClaimSupport],
        transformations: Optional[Sequence[Mapping[str, Any]]] = None,
        target_node_type: LineageNodeType = LineageNodeType.CLAIM,
    ) -> LineageGraph:
        graph = LineageGraph()

        claim_node_id = f"claim:{safe_identifier(claim.claim_id)}"
        graph.add_node(
            LineageNode(
                node_id=claim_node_id,
                node_type=target_node_type,
                label=claim.statement,
                entity_id=claim.claim_id,
                field_path=claim.field_path,
                payload_hash=stable_hash(claim.to_dict()),
                created_at=utcnow(),
            )
        )

        citation_by_id = {citation.citation_id: citation for citation in citations}

        for citation in citations:
            source_node_id = f"source:{safe_identifier(citation.source.source_id)}"
            if source_node_id not in graph.nodes:
                graph.add_node(
                    LineageNode(
                        node_id=source_node_id,
                        node_type=LineageNodeType.SOURCE,
                        label=citation.source.source_name,
                        entity_id=citation.source.source_id,
                        payload_hash=citation.source.payload_hash,
                        created_at=citation.source.retrieved_at,
                        metadata={
                            "category": citation.source.category.value,
                            "authority": citation.source.authority.value,
                        },
                    )
                )

            record_node_id = f"record:{safe_identifier(citation.citation_id)}"
            graph.add_node(
                LineageNode(
                    node_id=record_node_id,
                    node_type=LineageNodeType.RECORD,
                    label=citation.label,
                    entity_id=citation.citation_id,
                    field_path=citation.field_path,
                    payload_hash=stable_hash(citation.to_dict()),
                    created_at=citation.created_at,
                )
            )

            graph.add_edge(
                LineageEdge(
                    edge_id=stable_hash(
                        {
                            "source": source_node_id,
                            "target": record_node_id,
                            "type": LineageEdgeType.PRODUCED.value,
                        }
                    )[:24],
                    source_node_id=source_node_id,
                    target_node_id=record_node_id,
                    edge_type=LineageEdgeType.PRODUCED,
                    confidence=citation.source.composite_score,
                )
            )

        transformation_nodes: list[str] = []
        for index, transformation in enumerate(transformations or []):
            node_id = f"transformation:{safe_identifier(transformation.get('name', index))}"
            graph.add_node(
                LineageNode(
                    node_id=node_id,
                    node_type=LineageNodeType.TRANSFORMATION,
                    label=str(transformation.get("name", f"Transformation {index + 1}")),
                    payload_hash=stable_hash(transformation),
                    created_at=utcnow(),
                    metadata=dict(transformation),
                )
            )
            transformation_nodes.append(node_id)

        for support in supports:
            citation = citation_by_id.get(support.citation_id)
            if citation is None:
                continue

            source_record_node = f"record:{safe_identifier(citation.citation_id)}"
            edge_type = (
                LineageEdgeType.CONTRADICTED
                if support.direction == SupportDirection.CONTRADICTS
                else LineageEdgeType.SUPPORTED
            )

            if transformation_nodes:
                first = transformation_nodes[0]
                graph.add_edge(
                    LineageEdge(
                        edge_id=stable_hash(
                            {
                                "source": source_record_node,
                                "target": first,
                                "type": LineageEdgeType.DERIVED_FROM.value,
                            }
                        )[:24],
                        source_node_id=source_record_node,
                        target_node_id=first,
                        edge_type=LineageEdgeType.DERIVED_FROM,
                        confidence=support.strength,
                    )
                )

                for left, right in zip(transformation_nodes, transformation_nodes[1:]):
                    graph.add_edge(
                        LineageEdge(
                            edge_id=stable_hash(
                                {
                                    "source": left,
                                    "target": right,
                                    "type": LineageEdgeType.TRANSFORMED_INTO.value,
                                }
                            )[:24],
                            source_node_id=left,
                            target_node_id=right,
                            edge_type=LineageEdgeType.TRANSFORMED_INTO,
                            confidence=support.strength,
                        )
                    )

                graph.add_edge(
                    LineageEdge(
                        edge_id=stable_hash(
                            {
                                "source": transformation_nodes[-1],
                                "target": claim_node_id,
                                "type": edge_type.value,
                            }
                        )[:24],
                        source_node_id=transformation_nodes[-1],
                        target_node_id=claim_node_id,
                        edge_type=edge_type,
                        confidence=support.strength,
                    )
                )
            else:
                graph.add_edge(
                    LineageEdge(
                        edge_id=stable_hash(
                            {
                                "source": source_record_node,
                                "target": claim_node_id,
                                "type": edge_type.value,
                            }
                        )[:24],
                        source_node_id=source_record_node,
                        target_node_id=claim_node_id,
                        edge_type=edge_type,
                        confidence=support.strength,
                    )
                )

        return graph


# ============================================================
# SECTION 13 - NARRATIVE TEMPLATES
# ============================================================

class ExplanationTemplateRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, Callable[..., str]] = {
            "fact": self._fact_template,
            "valuation": self._valuation_template,
            "market": self._market_template,
            "risk": self._risk_template,
            "conflict": self._conflict_template,
            "confidence": self._confidence_template,
        }

    def render(self, template_name: str, **context: Any) -> str:
        renderer = self._templates.get(template_name)
        if renderer is None:
            raise KeyError(f"unknown explanation template: {template_name}")
        return renderer(**context)

    @staticmethod
    def _fact_template(
        *,
        claim: Claim,
        citations: Sequence[Citation],
        confidence: Decimal,
        **_: Any,
    ) -> str:
        source_names = sorted({citation.source.source_name for citation in citations})
        source_phrase = ", ".join(source_names[:3])
        if len(source_names) > 3:
            source_phrase += f", and {len(source_names) - 3} additional source(s)"

        return sentence_join(
            (
                claim.statement,
                (
                    f"This conclusion is supported by {source_phrase}"
                    if source_names
                    else "No external source citation was available"
                ),
                f"The resulting confidence is {confidence}",
            )
        )

    @staticmethod
    def _valuation_template(
        *,
        claim: Claim,
        citations: Sequence[Citation],
        confidence: Decimal,
        metadata: Optional[Mapping[str, Any]] = None,
        **_: Any,
    ) -> str:
        comparable_count = (metadata or {}).get("comparable_count")
        model_name = (metadata or {}).get("model_name")
        parts = [claim.statement]

        if model_name:
            parts.append(f"The estimate was produced using {model_name}")
        if comparable_count is not None:
            parts.append(f"{comparable_count} comparable property record(s) contributed")
        parts.append(f"Overall valuation confidence is {confidence}")
        if citations:
            parts.append(f"{len(citations)} source citation(s) support the estimate")

        return sentence_join(parts)

    @staticmethod
    def _market_template(
        *,
        claim: Claim,
        citations: Sequence[Citation],
        confidence: Decimal,
        **_: Any,
    ) -> str:
        return sentence_join(
            (
                claim.statement,
                f"The market conclusion uses {len(citations)} supporting source(s)",
                f"Confidence is {confidence}",
            )
        )

    @staticmethod
    def _risk_template(
        *,
        claim: Claim,
        citations: Sequence[Citation],
        confidence: Decimal,
        **_: Any,
    ) -> str:
        return sentence_join(
            (
                claim.statement,
                f"The risk assessment references {len(citations)} evidence source(s)",
                f"Confidence is {confidence}",
                "Risk scores are indicators and should not replace professional inspection, legal review, or insurance underwriting",
            )
        )

    @staticmethod
    def _conflict_template(
        *,
        conflicts: Sequence[SourceConflict],
        **_: Any,
    ) -> str:
        if not conflicts:
            return "No material source conflicts were identified."
        unresolved = sum(
            1
            for conflict in conflicts
            if conflict.status == ConflictResolutionStatus.UNRESOLVED
        )
        return sentence_join(
            (
                f"{len(conflicts)} material source conflict(s) were identified",
                f"{unresolved} remain unresolved",
            )
        )

    @staticmethod
    def _confidence_template(
        *,
        confidence: Decimal,
        support_count: int,
        conflict_count: int,
        **_: Any,
    ) -> str:
        return sentence_join(
            (
                f"Confidence is {confidence}",
                f"{support_count} supporting item(s) were evaluated",
                f"{conflict_count} conflict(s) were considered",
            )
        )


# ============================================================
# SECTION 14 - EXPLANATION QUALITY CONTROL
# ============================================================

@dataclass(slots=True)
class ExplanationQualityResult:
    score: Decimal
    complete: bool
    warnings: list[str]
    missing_elements: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": str(clamp_score(self.score)),
            "complete": self.complete,
            "warnings": list(self.warnings),
            "missing_elements": list(self.missing_elements),
        }


class ExplanationQualityChecker:
    def evaluate(
        self,
        *,
        claims: Sequence[Claim],
        citations: Sequence[Citation],
        conflicts: Sequence[SourceConflict],
        report_summary: str,
        limitations: Sequence[str],
    ) -> ExplanationQualityResult:
        factors: list[tuple[Decimal, Decimal]] = []
        warnings: list[str] = []
        missing: list[str] = []

        claim_score = ONE if claims else ZERO
        factors.append((claim_score, Decimal("0.20")))
        if not claims:
            missing.append("claims")

        citation_score = ONE if citations else ZERO
        factors.append((citation_score, Decimal("0.25")))
        if not citations:
            missing.append("citations")
            warnings.append("The explanation contains no source citations.")

        linked_claims = {
            citation.field_path
            for citation in citations
            if citation.field_path
        }
        claim_paths = {
            claim.field_path
            for claim in claims
            if claim.field_path
        }
        linkage_score = (
            Decimal(len(linked_claims & claim_paths)) / Decimal(len(claim_paths))
            if claim_paths
            else HALF
        )
        factors.append((clamp_score(linkage_score), Decimal("0.20")))

        summary_score = ONE if normalize_text(report_summary) else ZERO
        factors.append((summary_score, Decimal("0.15")))
        if summary_score == ZERO:
            missing.append("summary")

        limitations_score = ONE if limitations else Decimal("0.50")
        factors.append((limitations_score, Decimal("0.10")))
        if not limitations:
            warnings.append("No limitations were disclosed.")

        conflict_score = ONE
        if conflicts:
            resolved = sum(
                1
                for conflict in conflicts
                if conflict.status
                in {
                    ConflictResolutionStatus.AUTO_RESOLVED,
                    ConflictResolutionStatus.HUMAN_RESOLVED,
                }
            )
            conflict_score = Decimal(resolved) / Decimal(len(conflicts))
            if resolved < len(conflicts):
                warnings.append("One or more source conflicts remain unresolved.")
        factors.append((clamp_score(conflict_score), Decimal("0.10")))

        score = weighted_mean(factors, default=ZERO)
        return ExplanationQualityResult(
            score=score,
            complete=score >= Decimal("0.80") and not missing,
            warnings=warnings,
            missing_elements=missing,
        )


# ============================================================
# SECTION 15 - SOURCE EXPLANATION ENGINE
# ============================================================

class SourceExplanationEngine:
    """
    Main orchestration service for source-grounded explanations.

    Responsibilities:
    - Register claims and citations.
    - Evaluate support and contradiction.
    - Detect and optionally resolve source conflicts.
    - Rank citations.
    - Build lineage.
    - Generate user-facing and audit-facing narratives.
    - Enforce explanation quality checks.
    """

    def __init__(
        self,
        *,
        source_ranker: Optional[SourceRanker] = None,
        citation_builder: Optional[CitationBuilder] = None,
        support_evaluator: Optional[ClaimSupportEvaluator] = None,
        conflict_detector: Optional[SourceConflictDetector] = None,
        conflict_resolver: Optional[SourceConflictResolver] = None,
        lineage_builder: Optional[LineageBuilder] = None,
        templates: Optional[ExplanationTemplateRegistry] = None,
        quality_checker: Optional[ExplanationQualityChecker] = None,
    ) -> None:
        self.source_ranker = source_ranker or SourceRanker()
        self.citation_builder = citation_builder or CitationBuilder()
        self.support_evaluator = support_evaluator or ClaimSupportEvaluator()
        self.conflict_detector = conflict_detector or SourceConflictDetector()
        self.conflict_resolver = conflict_resolver or SourceConflictResolver(
            source_ranker=self.source_ranker
        )
        self.lineage_builder = lineage_builder or LineageBuilder()
        self.templates = templates or ExplanationTemplateRegistry()
        self.quality_checker = quality_checker or ExplanationQualityChecker()

    def explain_claim(
        self,
        *,
        claim: Claim,
        citations: Sequence[Citation],
        subject_type: str,
        subject_id: str,
        options: Optional[ExplanationOptions] = None,
        transformations: Optional[Sequence[Mapping[str, Any]]] = None,
        limitations: Optional[Sequence[str]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> ExplanationReport:
        active_options = options or ExplanationOptions()
        ranked_citations = sorted(
            citations,
            key=lambda citation: citation.rank_score,
            reverse=True,
        )[: active_options.max_citations]

        supports = [
            self.support_evaluator.evaluate(claim, citation)
            for citation in ranked_citations
        ]

        conflicts = (
            self.conflict_detector.detect(
                claim=claim,
                citations=ranked_citations,
            )
            if active_options.include_conflicts
            else []
        )

        conflicts = [
            self.conflict_resolver.resolve(conflict, ranked_citations)
            for conflict in conflicts
        ][: active_options.max_conflicts]

        confidence = self._claim_confidence(
            claim=claim,
            citations=ranked_citations,
            supports=supports,
            conflicts=conflicts,
        )

        narrative = self._render_claim_narrative(
            claim=claim,
            citations=ranked_citations,
            confidence=confidence,
            conflicts=conflicts,
            options=active_options,
            metadata=metadata,
        )

        sections = self._build_sections(
            claim=claim,
            citations=ranked_citations,
            conflicts=conflicts,
            confidence=confidence,
            narrative=narrative,
            options=active_options,
        )

        lineage = (
            self.lineage_builder.build_for_claim(
                claim=claim,
                citations=ranked_citations,
                supports=supports,
                transformations=transformations,
            )
            if active_options.include_lineage
            else None
        )

        report_limitations = list(limitations or [])
        if active_options.include_limitations and not report_limitations:
            report_limitations = self._default_limitations(claim.claim_type)

        summary = self._build_summary(
            claim=claim,
            confidence=confidence,
            citations=ranked_citations,
            conflicts=conflicts,
            options=active_options,
        )

        quality = self.quality_checker.evaluate(
            claims=[claim],
            citations=ranked_citations,
            conflicts=conflicts,
            report_summary=summary,
            limitations=report_limitations,
        )

        status = (
            ExplanationStatus.COMPLETE
            if quality.complete
            else ExplanationStatus.PARTIAL
        )

        report_payload = {
            "subject_type": subject_type,
            "subject_id": subject_id,
            "claim": claim.to_dict(),
            "citations": [citation.to_dict() for citation in ranked_citations],
            "conflicts": [conflict.to_dict() for conflict in conflicts],
            "confidence": str(confidence),
            "options": asdict(active_options),
            "metadata": dict(metadata or {}),
        }
        fingerprint = stable_hash(report_payload)
        report_id = fingerprint[:24]

        return ExplanationReport(
            report_id=report_id,
            subject_type=subject_type,
            subject_id=subject_id,
            title=self._title_for_claim(claim),
            summary=summary,
            status=status,
            confidence=confidence,
            sections=sections,
            citations=ranked_citations,
            claims=[claim],
            conflicts=conflicts,
            limitations=report_limitations,
            lineage=lineage,
            generated_at=utcnow(),
            fingerprint=fingerprint,
            metadata={
                **dict(metadata or {}),
                "quality": quality.to_dict(),
                "support": [support.to_dict() for support in supports],
                "options": serialize_value(asdict(active_options)),
            },
        )

    def explain_multiple_claims(
        self,
        *,
        claims: Sequence[Claim],
        citations: Sequence[Citation],
        subject_type: str,
        subject_id: str,
        title: str,
        options: Optional[ExplanationOptions] = None,
        transformations_by_claim: Optional[
            Mapping[str, Sequence[Mapping[str, Any]]]
        ] = None,
        limitations: Optional[Sequence[str]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> ExplanationReport:
        active_options = options or ExplanationOptions()
        child_reports = [
            self.explain_claim(
                claim=claim,
                citations=[
                    citation
                    for citation in citations
                    if (
                        citation.field_path == claim.field_path
                        or citation.field_path is None
                    )
                ],
                subject_type=subject_type,
                subject_id=subject_id,
                options=active_options,
                transformations=(transformations_by_claim or {}).get(claim.claim_id),
                limitations=[],
                metadata=metadata,
            )
            for claim in claims
        ]

        sections = [
            section
            for report in child_reports
            for section in report.sections
        ]
        combined_citations = self._deduplicate_citations(
            citation
            for report in child_reports
            for citation in report.citations
        )[: active_options.max_citations]
        combined_conflicts = [
            conflict
            for report in child_reports
            for conflict in report.conflicts
        ][: active_options.max_conflicts]

        confidence = weighted_mean(
            (
                (report.confidence, Decimal("1"))
                for report in child_reports
            )
        )

        report_limitations = list(limitations or [])
        if active_options.include_limitations and not report_limitations:
            report_limitations = [
                "The report combines multiple claims with different source coverage and confidence levels.",
                "Estimates and predictions may change when newer records or model versions become available.",
            ]

        summary = sentence_join(
            (
                f"{len(claims)} material claim(s) were evaluated",
                f"{len(combined_citations)} unique source citation(s) were used",
                f"Overall confidence is {confidence}",
                (
                    f"{len(combined_conflicts)} source conflict(s) were identified"
                    if combined_conflicts
                    else "No material source conflicts were identified"
                ),
            )
        )

        combined_lineage = None
        if active_options.include_lineage:
            combined_lineage = LineageGraph()
            for report in child_reports:
                if report.lineage is None:
                    continue
                combined_lineage.nodes.update(report.lineage.nodes)
                combined_lineage.edges.update(report.lineage.edges)

        quality = self.quality_checker.evaluate(
            claims=claims,
            citations=combined_citations,
            conflicts=combined_conflicts,
            report_summary=summary,
            limitations=report_limitations,
        )

        fingerprint = stable_hash(
            {
                "subject_type": subject_type,
                "subject_id": subject_id,
                "title": title,
                "claims": [claim.to_dict() for claim in claims],
                "citations": [citation.to_dict() for citation in combined_citations],
                "conflicts": [conflict.to_dict() for conflict in combined_conflicts],
                "confidence": str(confidence),
            }
        )

        return ExplanationReport(
            report_id=fingerprint[:24],
            subject_type=subject_type,
            subject_id=subject_id,
            title=title,
            summary=summary,
            status=(
                ExplanationStatus.COMPLETE
                if quality.complete
                else ExplanationStatus.PARTIAL
            ),
            confidence=confidence,
            sections=sections,
            citations=combined_citations,
            claims=list(claims),
            conflicts=combined_conflicts,
            limitations=report_limitations,
            lineage=combined_lineage,
            generated_at=utcnow(),
            fingerprint=fingerprint,
            metadata={
                **dict(metadata or {}),
                "quality": quality.to_dict(),
                "child_report_ids": [report.report_id for report in child_reports],
            },
        )

    def _claim_confidence(
        self,
        *,
        claim: Claim,
        citations: Sequence[Citation],
        supports: Sequence[ClaimSupport],
        conflicts: Sequence[SourceConflict],
    ) -> Decimal:
        support_score = weighted_mean(
            (
                (
                    support.strength
                    if support.direction
                    in {
                        SupportDirection.SUPPORTS,
                        SupportDirection.PARTIALLY_SUPPORTS,
                    }
                    else ZERO,
                    Decimal("1"),
                )
                for support in supports
            )
        )

        citation_score = weighted_mean(
            (
                (citation.rank_score, citation.relevance)
                for citation in citations
            )
        )

        conflict_penalty = max(
            (conflict.disagreement_score for conflict in conflicts),
            default=ZERO,
        )

        score = weighted_mean(
            (
                (claim.confidence, Decimal("0.35")),
                (support_score, Decimal("0.35")),
                (citation_score, Decimal("0.30")),
            )
        )
        return clamp_score(score - conflict_penalty * Decimal("0.30"))

    def _render_claim_narrative(
        self,
        *,
        claim: Claim,
        citations: Sequence[Citation],
        confidence: Decimal,
        conflicts: Sequence[SourceConflict],
        options: ExplanationOptions,
        metadata: Optional[Mapping[str, Any]],
    ) -> str:
        template_name = {
            ClaimType.VALUATION: "valuation",
            ClaimType.MARKET: "market",
            ClaimType.RISK: "risk",
        }.get(claim.claim_type, "fact")

        narrative = self.templates.render(
            template_name,
            claim=claim,
            citations=citations,
            confidence=confidence,
            metadata=metadata,
        )

        if options.include_conflicts and conflicts:
            narrative = sentence_join(
                (
                    narrative,
                    self.templates.render("conflict", conflicts=conflicts),
                )
            )

        if options.tone == ExplanationTone.TECHNICAL:
            narrative = sentence_join(
                (
                    narrative,
                    f"Explanation fingerprint inputs include {len(citations)} citation record(s)",
                )
            )

        return narrative

    def _build_sections(
        self,
        *,
        claim: Claim,
        citations: Sequence[Citation],
        conflicts: Sequence[SourceConflict],
        confidence: Decimal,
        narrative: str,
        options: ExplanationOptions,
    ) -> list[ExplanationSection]:
        sections = [
            ExplanationSection(
                section_id=f"{claim.claim_id}:conclusion",
                title="Conclusion",
                narrative=narrative,
                claims=[claim],
                citations=list(citations),
                conflicts=list(conflicts),
                confidence=confidence,
            )
        ]

        if options.depth in {ExplanationDepth.DETAILED, ExplanationDepth.AUDIT}:
            supporting = [
                citation
                for citation in citations
                if citation.support_direction
                in {
                    SupportDirection.SUPPORTS,
                    SupportDirection.PARTIALLY_SUPPORTS,
                }
            ][: options.max_supporting_facts]

            sections.append(
                ExplanationSection(
                    section_id=f"{claim.claim_id}:support",
                    title="Supporting evidence",
                    narrative=self._supporting_evidence_narrative(supporting),
                    claims=[claim],
                    citations=supporting,
                    confidence=weighted_mean(
                        (
                            (citation.rank_score, citation.relevance)
                            for citation in supporting
                        )
                    ),
                )
            )

        if options.include_conflicts and conflicts:
            sections.append(
                ExplanationSection(
                    section_id=f"{claim.claim_id}:conflicts",
                    title="Conflicting evidence",
                    narrative=self.templates.render(
                        "conflict",
                        conflicts=conflicts,
                    ),
                    claims=[claim],
                    conflicts=list(conflicts),
                    confidence=clamp_score(
                        ONE
                        - max(
                            (
                                conflict.disagreement_score
                                for conflict in conflicts
                            ),
                            default=ZERO,
                        )
                    ),
                )
            )

        if options.include_confidence:
            sections.append(
                ExplanationSection(
                    section_id=f"{claim.claim_id}:confidence",
                    title="Confidence",
                    narrative=self.templates.render(
                        "confidence",
                        confidence=confidence,
                        support_count=len(citations),
                        conflict_count=len(conflicts),
                    ),
                    claims=[claim],
                    confidence=confidence,
                )
            )

        return sections

    @staticmethod
    def _supporting_evidence_narrative(
        citations: Sequence[Citation],
    ) -> str:
        if not citations:
            return "No direct supporting citations were available."

        source_names = sorted(
            {citation.source.source_name for citation in citations}
        )
        return sentence_join(
            (
                f"{len(citations)} supporting citation(s) were selected",
                f"Sources include {', '.join(source_names)}",
            )
        )

    @staticmethod
    def _build_summary(
        *,
        claim: Claim,
        confidence: Decimal,
        citations: Sequence[Citation],
        conflicts: Sequence[SourceConflict],
        options: ExplanationOptions,
    ) -> str:
        parts = [
            claim.statement,
            f"Confidence is {confidence}",
        ]

        if options.include_sources:
            parts.append(f"{len(citations)} source citation(s) were evaluated")

        if options.include_conflicts:
            if conflicts:
                parts.append(f"{len(conflicts)} source conflict(s) were identified")
            else:
                parts.append("No material source conflicts were identified")

        return sentence_join(parts)

    @staticmethod
    def _default_limitations(claim_type: ClaimType) -> list[str]:
        common = [
            "Source records may be incomplete, delayed, corrected, or superseded.",
            "Confidence reflects available evidence and does not guarantee factual or future accuracy.",
        ]

        if claim_type == ClaimType.VALUATION:
            common.extend(
                [
                    "Automated valuations are estimates and are not licensed appraisals.",
                    "Property condition, renovations, concessions, and off-market information may not be fully represented.",
                ]
            )
        elif claim_type == ClaimType.RISK:
            common.extend(
                [
                    "Risk indicators do not replace legal, environmental, engineering, insurance, or inspection review.",
                ]
            )
        elif claim_type == ClaimType.MARKET:
            common.extend(
                [
                    "Market conditions can change quickly and may differ by property segment.",
                ]
            )

        return common

    @staticmethod
    def _title_for_claim(claim: Claim) -> str:
        return {
            ClaimType.VALUATION: "Property Valuation Explanation",
            ClaimType.MARKET: "Market Intelligence Explanation",
            ClaimType.RISK: "Property Risk Explanation",
            ClaimType.ADDRESS: "Address Intelligence Explanation",
            ClaimType.OWNERSHIP: "Ownership Record Explanation",
            ClaimType.TAX: "Tax Record Explanation",
            ClaimType.PREDICTION: "Prediction Explanation",
            ClaimType.ESTIMATE: "Estimate Explanation",
        }.get(claim.claim_type, "Property Intelligence Explanation")

    @staticmethod
    def _deduplicate_citations(
        citations: Iterable[Citation],
    ) -> list[Citation]:
        output: dict[str, Citation] = {}
        for citation in citations:
            existing = output.get(citation.citation_id)
            if existing is None or citation.rank_score > existing.rank_score:
                output[citation.citation_id] = citation
        return sorted(
            output.values(),
            key=lambda item: item.rank_score,
            reverse=True,
        )


# ============================================================
# SECTION 16 - DOMAIN-SPECIFIC EXPLANATION BUILDERS
# ============================================================

class ValuationExplanationBuilder:
    def build_claim(
        self,
        *,
        property_id: str,
        estimated_value: Any,
        confidence: Any,
        currency_code: str = "USD",
        as_of: Optional[datetime] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Claim:
        value = to_decimal(estimated_value)
        statement = (
            f"The estimated property value is {currency_code} "
            f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}."
        )
        return Claim(
            claim_id=stable_hash(
                {
                    "property_id": property_id,
                    "estimated_value": str(value),
                    "as_of": as_of,
                }
            )[:24],
            statement=statement,
            claim_type=ClaimType.VALUATION,
            field_path="valuation.estimated_value",
            value=value,
            currency_code=currency_code,
            confidence=clamp_score(confidence),
            effective_at=as_of,
            metadata=dict(metadata or {}),
        )


class MarketExplanationBuilder:
    def build_claim(
        self,
        *,
        market_area_id: str,
        statement: str,
        value: Any = None,
        confidence: Any = DEFAULT_EXPLANATION_CONFIDENCE,
        field_path: str = "market.summary",
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Claim:
        return Claim(
            claim_id=stable_hash(
                {
                    "market_area_id": market_area_id,
                    "statement": statement,
                    "value": serialize_value(value),
                }
            )[:24],
            statement=statement,
            claim_type=ClaimType.MARKET,
            field_path=field_path,
            value=value,
            confidence=clamp_score(confidence),
            metadata=dict(metadata or {}),
        )


class RiskExplanationBuilder:
    def build_claim(
        self,
        *,
        property_id: str,
        risk_category: str,
        risk_score: Any,
        statement: Optional[str] = None,
        confidence: Any = DEFAULT_EXPLANATION_CONFIDENCE,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Claim:
        normalized_score = clamp_score(risk_score)
        resolved_statement = statement or (
            f"The {risk_category} risk score is {normalized_score}."
        )

        return Claim(
            claim_id=stable_hash(
                {
                    "property_id": property_id,
                    "risk_category": risk_category,
                    "risk_score": str(normalized_score),
                }
            )[:24],
            statement=resolved_statement,
            claim_type=ClaimType.RISK,
            field_path=f"risk.{safe_identifier(risk_category)}",
            value=normalized_score,
            confidence=clamp_score(confidence),
            metadata=dict(metadata or {}),
        )


class PropertyFactExplanationBuilder:
    def build_claim(
        self,
        *,
        property_id: str,
        field_path: str,
        value: Any,
        statement: Optional[str] = None,
        confidence: Any = DEFAULT_EXPLANATION_CONFIDENCE,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Claim:
        resolved_statement = statement or (
            f"The property record indicates {field_path} is {value}."
        )
        return Claim(
            claim_id=stable_hash(
                {
                    "property_id": property_id,
                    "field_path": field_path,
                    "value": serialize_value(value),
                }
            )[:24],
            statement=resolved_statement,
            claim_type=ClaimType.FACT,
            field_path=field_path,
            value=value,
            confidence=clamp_score(confidence),
            metadata=dict(metadata or {}),
        )


# ============================================================
# SECTION 17 - MODEL AND ORM INTEGRATION HELPERS
# ============================================================

def source_from_model_object(
    obj: Any,
    *,
    category: SourceCategory = SourceCategory.OTHER,
    authority: SourceAuthority = SourceAuthority.UNKNOWN,
    source_name: Optional[str] = None,
) -> SourceDescriptor:
    resolved_name = (
        source_name
        or getattr(obj, "source_name", None)
        or getattr(obj, "name", None)
        or obj.__class__.__name__
    )

    return SourceDescriptor(
        source_id=str(
            getattr(
                obj,
                "id",
                stable_hash(
                    {
                        "class": obj.__class__.__name__,
                        "repr": repr(obj),
                    }
                )[:24],
            )
        ),
        source_name=resolved_name,
        category=category,
        authority=authority,
        provider_name=getattr(obj, "provider_name", None),
        record_id=getattr(obj, "source_record_id", None),
        record_type=obj.__class__.__name__,
        source_url=getattr(obj, "source_url", None),
        observed_at=getattr(obj, "source_observed_at", None),
        retrieved_at=getattr(obj, "source_retrieved_at", None),
        effective_at=getattr(obj, "effective_at", None),
        reliability=clamp_score(
            getattr(obj, "confidence_score", DEFAULT_SOURCE_RELIABILITY)
        ),
        quality=clamp_score(
            getattr(obj, "quality_score", DEFAULT_EXPLANATION_CONFIDENCE)
        ),
        freshness=clamp_score(
            getattr(
                obj,
                "freshness_score",
                DEFAULT_EXPLANATION_CONFIDENCE,
            )
        ),
        payload_hash=getattr(obj, "source_payload_hash", None),
        metadata={
            "object_type": obj.__class__.__name__,
            "object_id": str(getattr(obj, "id", "")),
        },
    )


def citation_from_observation(
    observation: Any,
    *,
    source: Optional[SourceDescriptor] = None,
    label: Optional[str] = None,
    support_direction: SupportDirection = SupportDirection.SUPPORTS,
) -> Citation:
    resolved_source = source or source_from_model_object(
        observation,
        category=SourceCategory.PUBLIC_RECORD,
        authority=SourceAuthority.AUTHORITATIVE,
    )

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

    builder = CitationBuilder()
    return builder.build(
        source=resolved_source,
        label=label,
        field_path=getattr(observation, "field_path", None),
        value=value,
        confidence=getattr(
            observation,
            "confidence_score",
            DEFAULT_EXPLANATION_CONFIDENCE,
        ),
        support_direction=support_direction,
        metadata={
            "observation_id": str(getattr(observation, "id", "")),
            "observation_type": serialize_value(
                getattr(observation, "observation_type", None)
            ),
        },
    )


def apply_explanation_to_report_model(
    target: Any,
    report: ExplanationReport,
) -> Any:
    if hasattr(target, "title"):
        target.title = report.title
    if hasattr(target, "executive_summary"):
        target.executive_summary = report.summary
    if hasattr(target, "sections"):
        target.sections = [section.to_dict() for section in report.sections]
    if hasattr(target, "citations"):
        target.citations = [citation.to_dict() for citation in report.citations]
    if hasattr(target, "content_hash"):
        target.content_hash = report.fingerprint
    if hasattr(target, "metadata_json") and isinstance(target.metadata_json, dict):
        target.metadata_json["source_explanation_engine"] = report.to_dict()
    return target


def explanation_to_audit_payload(
    report: ExplanationReport,
) -> dict[str, Any]:
    return {
        "entity_type": "property_intelligence_explanation",
        "entity_id": report.report_id,
        "action": "generated",
        "after_state": report.to_dict(),
        "change_summary": [
            f"Generated {len(report.claims)} claim explanation(s).",
            f"Attached {len(report.citations)} citation(s).",
            f"Detected {len(report.conflicts)} conflict(s).",
        ],
        "metadata": {
            "fingerprint": report.fingerprint,
            "status": report.status.value,
            "confidence": str(report.confidence),
        },
    }


# ============================================================
# SECTION 18 - BATCH EXPLANATION PROCESSING
# ============================================================

@dataclass(slots=True)
class BatchExplanationItem:
    key: str
    report: ExplanationReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "report": self.report.to_dict(),
        }


@dataclass(slots=True)
class BatchExplanationResult:
    total: int
    complete: int
    partial: int
    average_confidence: Decimal
    citation_count: int
    conflict_count: int
    items: list[BatchExplanationItem]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "complete": self.complete,
            "partial": self.partial,
            "average_confidence": str(clamp_score(self.average_confidence)),
            "citation_count": self.citation_count,
            "conflict_count": self.conflict_count,
            "items": [item.to_dict() for item in self.items],
        }


class BatchSourceExplanationProcessor:
    def __init__(
        self,
        *,
        engine: Optional[SourceExplanationEngine] = None,
    ) -> None:
        self.engine = engine or SourceExplanationEngine()

    def process(
        self,
        requests: Mapping[
            str,
            Mapping[str, Any],
        ],
    ) -> BatchExplanationResult:
        items: list[BatchExplanationItem] = []

        for key, request in requests.items():
            report = self.engine.explain_claim(
                claim=request["claim"],
                citations=request.get("citations", []),
                subject_type=request.get("subject_type", "property"),
                subject_id=request.get("subject_id", key),
                options=request.get("options"),
                transformations=request.get("transformations"),
                limitations=request.get("limitations"),
                metadata=request.get("metadata"),
            )
            items.append(BatchExplanationItem(key=key, report=report))

        total = len(items)
        average_confidence = (
            sum((item.report.confidence for item in items), ZERO)
            / Decimal(total)
            if total
            else ZERO
        )

        return BatchExplanationResult(
            total=total,
            complete=sum(
                1
                for item in items
                if item.report.status == ExplanationStatus.COMPLETE
            ),
            partial=sum(
                1
                for item in items
                if item.report.status == ExplanationStatus.PARTIAL
            ),
            average_confidence=clamp_score(average_confidence),
            citation_count=sum(len(item.report.citations) for item in items),
            conflict_count=sum(len(item.report.conflicts) for item in items),
            items=items,
        )


# ============================================================
# SECTION 19 - DEFAULT ENGINE AND CONVENIENCE API
# ============================================================

_default_engine = SourceExplanationEngine()
_default_citation_builder = CitationBuilder()


def explain_claim(
    *,
    claim: Claim,
    citations: Sequence[Citation],
    subject_type: str,
    subject_id: str,
    options: Optional[ExplanationOptions] = None,
    transformations: Optional[Sequence[Mapping[str, Any]]] = None,
    limitations: Optional[Sequence[str]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> ExplanationReport:
    return _default_engine.explain_claim(
        claim=claim,
        citations=citations,
        subject_type=subject_type,
        subject_id=subject_id,
        options=options,
        transformations=transformations,
        limitations=limitations,
        metadata=metadata,
    )


def build_citation(
    *,
    source: SourceDescriptor,
    label: Optional[str] = None,
    citation_type: Optional[CitationType] = None,
    locator: Optional[str] = None,
    excerpt: Optional[str] = None,
    field_path: Optional[str] = None,
    value: Any = None,
    confidence: Any = DEFAULT_EXPLANATION_CONFIDENCE,
    relevance: Any = ONE,
    support_direction: SupportDirection = SupportDirection.SUPPORTS,
    metadata: Optional[Mapping[str, Any]] = None,
) -> Citation:
    return _default_citation_builder.build(
        source=source,
        label=label,
        citation_type=citation_type,
        locator=locator,
        excerpt=excerpt,
        field_path=field_path,
        value=value,
        confidence=confidence,
        relevance=relevance,
        support_direction=support_direction,
        metadata=metadata,
    )


# ============================================================
# SECTION 20 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    # constants and helpers
    "DEFAULT_SOURCE_RELIABILITY",
    "DEFAULT_EXPLANATION_CONFIDENCE",
    "clamp_score",
    "weighted_mean",
    "stable_hash",
    "normalize_text",
    "safe_identifier",
    # enums
    "SourceCategory",
    "SourceAuthority",
    "CitationType",
    "ClaimType",
    "SupportDirection",
    "ExplanationAudience",
    "ExplanationDepth",
    "ExplanationTone",
    "ConflictResolutionStatus",
    "LineageNodeType",
    "LineageEdgeType",
    "ExplanationStatus",
    # contracts
    "SourceDescriptor",
    "Citation",
    "Claim",
    "ClaimSupport",
    "SourceConflict",
    "LineageNode",
    "LineageEdge",
    "LineageGraph",
    "ExplanationOptions",
    "ExplanationSection",
    "ExplanationReport",
    "ExplanationQualityResult",
    "BatchExplanationItem",
    "BatchExplanationResult",
    # services
    "SourceRanker",
    "CitationBuilder",
    "ClaimSupportEvaluator",
    "SourceConflictDetector",
    "SourceConflictResolver",
    "LineageBuilder",
    "ExplanationTemplateRegistry",
    "ExplanationQualityChecker",
    "SourceExplanationEngine",
    "ValuationExplanationBuilder",
    "MarketExplanationBuilder",
    "RiskExplanationBuilder",
    "PropertyFactExplanationBuilder",
    "BatchSourceExplanationProcessor",
    # integration
    "source_from_model_object",
    "citation_from_observation",
    "apply_explanation_to_report_model",
    "explanation_to_audit_payload",
    # convenience
    "explain_claim",
    "build_citation",
]
