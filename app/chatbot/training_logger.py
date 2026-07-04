# ============================================================
# AUSSEM1
# PHASE 1.00 PART 6.00
# ENTERPRISE TRAINING INTELLIGENCE LOGGER
# FILE: app/chatbot/training_logger.py
# PURPOSE:
# Record, classify, analyze, and prepare every chatbot
# interaction for supervised learning, quality review,
# confidence analytics, and future AI improvement.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# ENTERPRISE FOUNDATION ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4


# ============================================================
# SECTION 02 - LOGGER VERSION CONFIGURATION
# ============================================================

LOGGER_NAME = "Aussem1 Enterprise Training Intelligence Logger"

LOGGER_VERSION = "0.2.0"

LOGGER_PHASE = "PHASE 1.00 PART 6.00"

LOGGER_STATUS = "enterprise_foundation_active"


# ============================================================
# SECTION 03 - FILE SYSTEM CONFIGURATION
# ============================================================

TRAINING_DIRECTORY = Path("app/data")

TRAINING_LOG_FILE = TRAINING_DIRECTORY / "training_log.json"

TRAINING_REVIEW_QUEUE_FILE = TRAINING_DIRECTORY / "training_review_queue.json"

TRAINING_EXPORT_FILE = TRAINING_DIRECTORY / "training_export.json"


# ============================================================
# SECTION 04 - LEARNING CLASSIFICATION ENUMS
# ============================================================

class TrainingReviewStatus(StrEnum):
    """
    Human-review status for a training record.
    """

    NOT_REQUIRED = "not_required"
    REVIEW_REQUIRED = "review_required"
    REVIEWED = "reviewed"
    APPROVED_FOR_DATASET = "approved_for_dataset"
    REJECTED = "rejected"


class LearningPriority(StrEnum):
    """
    Priority level for future learning attention.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InteractionQuality(StrEnum):
    """
    Quality classification for chatbot interaction.
    """

    STRONG = "strong"
    ACCEPTABLE = "acceptable"
    WEAK = "weak"
    FAILED = "failed"


class TrainingCategory(StrEnum):
    """
    Business-domain category for training records.
    """

    PROPERTY_VALUE = "property_value"
    PROPERTY_STATUS = "property_status"
    PUBLIC_RECORDS = "public_records"
    COMPARABLE_ANALYSIS = "comparable_analysis"
    MARKET_ANALYSIS = "market_analysis"
    INVESTMENT_ANALYSIS = "investment_analysis"
    GENERAL_REAL_ESTATE = "general_real_estate"
    SYSTEM = "system"
    UNKNOWN = "unknown"


# ============================================================
# SECTION 05 - TRAINING RECORD MODEL
# ============================================================

@dataclass
class TrainingRecord:
    """
    Represents one chatbot interaction.

    This model is intentionally verbose because the training
    logger is the foundation for future supervised learning.
    """

    record_id: str
    timestamp: str
    logger_version: str
    logger_phase: str

    session_id: str
    user_question: str
    chatbot_response: str

    confidence: float
    confidence_band: str
    intent: str
    training_category: str

    property_address: str | None
    missing_information: list[str]

    user_feedback: str | None
    corrected_answer: str | None

    successful: bool
    interaction_quality: str
    review_status: str
    learning_priority: str

    needs_human_review: bool
    review_reasons: list[str]

    metadata: dict[str, Any]


# ============================================================
# SECTION 06 - REVIEW QUEUE ITEM MODEL
# ============================================================

@dataclass
class ReviewQueueItem:
    """
    Represents an item that should be reviewed by a human before
    being used for supervised learning or knowledge expansion.
    """

    queue_id: str
    created_at: str
    record_id: str
    session_id: str
    user_question: str
    chatbot_response: str
    intent: str
    confidence: float
    learning_priority: str
    review_reasons: list[str]
    missing_information: list[str]
    status: str


# ============================================================
# SECTION 07 - TRAINING LOGGER CLASS
# ============================================================

class TrainingLogger:
    """
    Enterprise training intelligence logger.

    Responsibilities:

    • Record every chatbot interaction.
    • Classify interaction quality.
    • Identify low-confidence responses.
    • Identify missing-information patterns.
    • Create human review queue items.
    • Prepare future supervised learning datasets.
    • Support analytics for continuous AI improvement.
    """

    def __init__(self) -> None:
        """
        Initialize required training storage files.
        """

        TRAINING_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._ensure_json_array_file(TRAINING_LOG_FILE)
        self._ensure_json_array_file(TRAINING_REVIEW_QUEUE_FILE)
        self._ensure_json_array_file(TRAINING_EXPORT_FILE)


# ============================================================
# SECTION 08 - PUBLIC LOGGING INTERFACE
# ============================================================

    def log_interaction(
        self,
        *,
        session_id: str,
        user_question: str,
        chatbot_response: str,
        confidence: float,
        intent: str,
        property_address: str | None = None,
        missing_information: list[str] | None = None,
        user_feedback: str | None = None,
        corrected_answer: str | None = None,
        successful: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> TrainingRecord:
        """
        Save a single chatbot interaction and return the created
        training record.
        """

        missing_items = missing_information or []

        confidence_band = self._confidence_band(confidence)

        training_category = self._classify_training_category(intent)

        interaction_quality = self._classify_interaction_quality(
            confidence=confidence,
            successful=successful,
            missing_information=missing_items,
            corrected_answer=corrected_answer,
        )

        review_reasons = self._detect_review_reasons(
            confidence=confidence,
            successful=successful,
            missing_information=missing_items,
            user_feedback=user_feedback,
            corrected_answer=corrected_answer,
            intent=intent,
        )

        needs_review = bool(review_reasons)

        learning_priority = self._calculate_learning_priority(
            confidence=confidence,
            successful=successful,
            missing_information=missing_items,
            review_reasons=review_reasons,
        )

        record = TrainingRecord(
            record_id=self._new_record_id(),
            timestamp=self._now(),
            logger_version=LOGGER_VERSION,
            logger_phase=LOGGER_PHASE,
            session_id=session_id,
            user_question=user_question,
            chatbot_response=chatbot_response,
            confidence=confidence,
            confidence_band=confidence_band,
            intent=intent,
            training_category=training_category.value,
            property_address=property_address,
            missing_information=missing_items,
            user_feedback=user_feedback,
            corrected_answer=corrected_answer,
            successful=successful,
            interaction_quality=interaction_quality.value,
            review_status=(
                TrainingReviewStatus.REVIEW_REQUIRED.value
                if needs_review
                else TrainingReviewStatus.NOT_REQUIRED.value
            ),
            learning_priority=learning_priority.value,
            needs_human_review=needs_review,
            review_reasons=review_reasons,
            metadata=metadata or {},
        )

        records = self._load_json_array(TRAINING_LOG_FILE)

        records.append(asdict(record))

        self._save_json_array(
            path=TRAINING_LOG_FILE,
            records=records,
        )

        if needs_review:
            self._add_to_review_queue(record)

        return record


# ============================================================
# SECTION 09 - HUMAN FEEDBACK INTERFACE
# ============================================================

    def log_feedback(
        self,
        *,
        record_id: str,
        user_feedback: str,
        corrected_answer: str | None = None,
    ) -> bool:
        """
        Attach user feedback or a corrected answer to an existing
        training record.
        """

        records = self._load_json_array(TRAINING_LOG_FILE)

        changed = False

        for record in records:
            if record.get("record_id") == record_id:
                record["user_feedback"] = user_feedback
                record["corrected_answer"] = corrected_answer
                record["needs_human_review"] = True
                record["review_status"] = TrainingReviewStatus.REVIEW_REQUIRED.value

                if "user_feedback_received" not in record["review_reasons"]:
                    record["review_reasons"].append("user_feedback_received")

                changed = True
                break

        if changed:
            self._save_json_array(
                path=TRAINING_LOG_FILE,
                records=records,
            )

        return changed


# ============================================================
# SECTION 10 - REVIEW QUEUE CREATION
# ============================================================

    def _add_to_review_queue(
        self,
        record: TrainingRecord,
    ) -> None:
        """
        Add a record to the human review queue.
        """

        queue = self._load_json_array(TRAINING_REVIEW_QUEUE_FILE)

        existing_record_ids = {
            item.get("record_id")
            for item in queue
        }

        if record.record_id in existing_record_ids:
            return

        queue_item = ReviewQueueItem(
            queue_id=self._new_queue_id(),
            created_at=self._now(),
            record_id=record.record_id,
            session_id=record.session_id,
            user_question=record.user_question,
            chatbot_response=record.chatbot_response,
            intent=record.intent,
            confidence=record.confidence,
            learning_priority=record.learning_priority,
            review_reasons=record.review_reasons,
            missing_information=record.missing_information,
            status=TrainingReviewStatus.REVIEW_REQUIRED.value,
        )

        queue.append(asdict(queue_item))

        self._save_json_array(
            path=TRAINING_REVIEW_QUEUE_FILE,
            records=queue,
        )


# ============================================================
# SECTION 11 - REVIEW QUEUE PUBLIC ACCESS
# ============================================================

    def review_queue(
        self,
        *,
        limit: int | None = None,
    ) -> list[dict]:
        """
        Return review queue items.
        """

        queue = self._load_json_array(TRAINING_REVIEW_QUEUE_FILE)

        if limit is None:
            return queue

        return queue[:limit]


# ============================================================
# SECTION 12 - TRAINING ANALYTICS
# ============================================================

    def total_interactions(self) -> int:
        """
        Return total recorded chatbot interactions.
        """

        return len(self._load_json_array(TRAINING_LOG_FILE))


    def failed_interactions(self) -> int:
        """
        Return number of failed or low-quality interactions.
        """

        return sum(
            1
            for record in self._load_json_array(TRAINING_LOG_FILE)
            if not record.get("successful", False)
            or record.get("interaction_quality") == InteractionQuality.FAILED.value
        )


    def unanswered_questions(self) -> list[str]:
        """
        Return questions where missing information prevented a strong answer.
        """

        return [
            record.get("user_question", "")
            for record in self._load_json_array(TRAINING_LOG_FILE)
            if record.get("missing_information")
        ]


    def low_confidence_questions(self) -> list[dict]:
        """
        Return low-confidence training records.
        """

        return [
            record
            for record in self._load_json_array(TRAINING_LOG_FILE)
            if float(record.get("confidence", 0.0)) < 0.50
        ]


    def interactions_by_intent(self) -> dict[str, int]:
        """
        Count interactions grouped by intent.
        """

        counts: dict[str, int] = {}

        for record in self._load_json_array(TRAINING_LOG_FILE):
            intent = record.get("intent", "unknown")

            counts[intent] = counts.get(intent, 0) + 1

        return counts


    def missing_information_frequency(self) -> dict[str, int]:
        """
        Count how often each missing-information field appears.
        """

        counts: dict[str, int] = {}

        for record in self._load_json_array(TRAINING_LOG_FILE):
            for item in record.get("missing_information", []):
                counts[item] = counts.get(item, 0) + 1

        return counts


# ============================================================
# SECTION 13 - ENTERPRISE TRAINING SUMMARY
# ============================================================

    def training_summary(self) -> dict[str, Any]:
        """
        Return an enterprise training health summary.
        """

        records = self._load_json_array(TRAINING_LOG_FILE)

        total = len(records)

        review_queue = self._load_json_array(TRAINING_REVIEW_QUEUE_FILE)

        if total == 0:
            average_confidence = 0.0
        else:
            average_confidence = round(
                sum(
                    float(record.get("confidence", 0.0))
                    for record in records
                ) / total,
                3,
            )

        return {
            "logger_name": LOGGER_NAME,
            "version": LOGGER_VERSION,
            "phase": LOGGER_PHASE,
            "status": LOGGER_STATUS,
            "total_interactions": total,
            "failed_interactions": self.failed_interactions(),
            "average_confidence": average_confidence,
            "review_queue_size": len(review_queue),
            "intent_counts": self.interactions_by_intent(),
            "missing_information_frequency": self.missing_information_frequency(),
            "generated_at": self._now(),
        }


# ============================================================
# SECTION 14 - TRAINING DATA EXPORT
# ============================================================

    def export_training_dataset(
        self,
        *,
        include_review_required: bool = False,
    ) -> list[dict]:
        """
        Export training records into a cleaner future dataset format.
        """

        records = self._load_json_array(TRAINING_LOG_FILE)

        dataset: list[dict] = []

        for record in records:
            if (
                record.get("needs_human_review")
                and not include_review_required
            ):
                continue

            dataset.append(
                {
                    "input": record.get("user_question"),
                    "output": record.get("corrected_answer")
                    or record.get("chatbot_response"),
                    "intent": record.get("intent"),
                    "confidence": record.get("confidence"),
                    "property_address": record.get("property_address"),
                    "metadata": {
                        "record_id": record.get("record_id"),
                        "training_category": record.get("training_category"),
                        "interaction_quality": record.get("interaction_quality"),
                        "source_logger": LOGGER_NAME,
                        "source_version": LOGGER_VERSION,
                    },
                }
            )

        self._save_json_array(
            path=TRAINING_EXPORT_FILE,
            records=dataset,
        )

        return dataset


# ============================================================
# SECTION 15 - REVIEW REASON DETECTION
# ============================================================

    def _detect_review_reasons(
        self,
        *,
        confidence: float,
        successful: bool,
        missing_information: list[str],
        user_feedback: str | None,
        corrected_answer: str | None,
        intent: str,
    ) -> list[str]:
        """
        Determine whether a record needs human review.
        """

        reasons: list[str] = []

        if confidence < 0.50:
            reasons.append("low_confidence")

        if not successful:
            reasons.append("unsuccessful_interaction")

        if missing_information:
            reasons.append("missing_information")

        if user_feedback:
            reasons.append("user_feedback_received")

        if corrected_answer:
            reasons.append("corrected_answer_available")

        if intent in ["unknown", "general_real_estate"]:
            reasons.append("weak_intent_specificity")

        return reasons


# ============================================================
# SECTION 16 - LEARNING PRIORITY CALCULATION
# ============================================================

    def _calculate_learning_priority(
        self,
        *,
        confidence: float,
        successful: bool,
        missing_information: list[str],
        review_reasons: list[str],
    ) -> LearningPriority:
        """
        Calculate priority for future learning.
        """

        score = 0

        if confidence < 0.35:
            score += 3
        elif confidence < 0.50:
            score += 2
        elif confidence < 0.65:
            score += 1

        if not successful:
            score += 2

        if len(missing_information) >= 4:
            score += 2
        elif missing_information:
            score += 1

        if "corrected_answer_available" in review_reasons:
            score += 3

        if score >= 6:
            return LearningPriority.CRITICAL

        if score >= 4:
            return LearningPriority.HIGH

        if score >= 2:
            return LearningPriority.MEDIUM

        return LearningPriority.LOW


# ============================================================
# SECTION 17 - INTERACTION QUALITY CLASSIFICATION
# ============================================================

    def _classify_interaction_quality(
        self,
        *,
        confidence: float,
        successful: bool,
        missing_information: list[str],
        corrected_answer: str | None,
    ) -> InteractionQuality:
        """
        Classify the quality of one interaction.
        """

        if corrected_answer:
            return InteractionQuality.WEAK

        if not successful:
            return InteractionQuality.FAILED

        if confidence >= 0.75 and not missing_information:
            return InteractionQuality.STRONG

        if confidence >= 0.50:
            return InteractionQuality.ACCEPTABLE

        return InteractionQuality.WEAK


# ============================================================
# SECTION 18 - TRAINING CATEGORY CLASSIFICATION
# ============================================================

    def _classify_training_category(
        self,
        intent: str,
    ) -> TrainingCategory:
        """
        Convert intent string into durable training category.
        """

        normalized = intent.lower().strip()

        mapping = {
            "property_value": TrainingCategory.PROPERTY_VALUE,
            "property_status": TrainingCategory.PROPERTY_STATUS,
            "public_records": TrainingCategory.PUBLIC_RECORDS,
            "comparable_analysis": TrainingCategory.COMPARABLE_ANALYSIS,
            "property_comparables": TrainingCategory.COMPARABLE_ANALYSIS,
            "market_analysis": TrainingCategory.MARKET_ANALYSIS,
            "investment_analysis": TrainingCategory.INVESTMENT_ANALYSIS,
            "general_real_estate": TrainingCategory.GENERAL_REAL_ESTATE,
            "system_help": TrainingCategory.SYSTEM,
        }

        return mapping.get(
            normalized,
            TrainingCategory.UNKNOWN,
        )


# ============================================================
# SECTION 19 - CONFIDENCE BAND
# ============================================================

    def _confidence_band(
        self,
        confidence: float,
    ) -> str:
        """
        Convert numeric confidence into a durable band.
        """

        if confidence >= 0.90:
            return "very_high"

        if confidence >= 0.75:
            return "high"

        if confidence >= 0.60:
            return "medium"

        if confidence >= 0.40:
            return "low"

        return "very_low"


# ============================================================
# SECTION 20 - FILE OPERATIONS
# ============================================================

    def _ensure_json_array_file(
        self,
        path: Path,
    ) -> None:
        """
        Ensure a JSON file exists and contains an array.
        """

        if not path.exists():
            path.write_text(
                "[]",
                encoding="utf-8",
            )
            return

        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8",
                )
            )

            if not isinstance(data, list):
                path.write_text(
                    "[]",
                    encoding="utf-8",
                )

        except json.JSONDecodeError:
            path.write_text(
                "[]",
                encoding="utf-8",
            )


    def _load_json_array(
        self,
        path: Path,
    ) -> list[dict]:
        """
        Load a JSON array from disk.
        """

        self._ensure_json_array_file(path)

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, list):
            return []

        return data


    def _save_json_array(
        self,
        *,
        path: Path,
        records: list[dict],
    ) -> None:
        """
        Save records as formatted JSON.
        """

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                records,
                file,
                indent=4,
                ensure_ascii=False,
            )


# ============================================================
# SECTION 21 - IDENTIFIER UTILITIES
# ============================================================

    def _new_record_id(self) -> str:
        """
        Create stable training record identifier.
        """

        return f"training-{uuid4()}"


    def _new_queue_id(self) -> str:
        """
        Create stable review queue identifier.
        """

        return f"review-{uuid4()}"


    def _now(self) -> str:
        """
        Return current UTC timestamp.
        """

        return datetime.now(UTC).isoformat()


# ============================================================
# SECTION 22 - FUTURE ENTERPRISE EXPANSION
# ============================================================

#
# Planned Future Features:
#
# • PostgreSQL-backed training records
# • User-specific feedback histories
# • Human review dashboard
# • Training dataset versioning
# • Prompt quality scoring
# • Model comparison scoring
# • Hallucination detection
# • Semantic clustering of failed questions
# • Property-specific training memory
# • Export to fine-tuning JSONL
# • Admin approval workflow
# • Reinforcement learning preparation
#
# ============================================================


# ============================================================
# END OF FILE
# ============================================================