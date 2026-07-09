# ============================================================
# AUSSEM1
# PHASE 2.10 PART 4.00
# ENTERPRISE SOURCE CLIENT
# FILE: app/sources/source_client.py
# PURPOSE:
# Provide the safe, source-governed HTTP client foundation for
# Aussem1 public-record, parcel, tax, clerk, GIS, open-data,
# listing-feed, and future property-data connectors.
#
# This client does not create mock property data.
# This client does not invent records.
# This client does not bypass access controls.
# This client only provides controlled request, response,
# error, metadata, and source-status handling.
#
# AUTHOR:
# Ryan Schuren
#
# ASSISTANT:
# Alfred
#
# STATUS:
# REAL DATA SOURCE CLIENT ACTIVE
# ============================================================


# ============================================================
# SECTION 01 - ENTERPRISE IMPORTS
# ============================================================

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from typing import Any

from app.sources.source_models import SourceAccessMethod
from app.sources.source_models import SourceDataFormat
from app.sources.source_models import SourceError
from app.sources.source_models import SourceErrorType
from app.sources.source_models import SourceRequestPolicy
from app.sources.source_models import SourceStatus
from app.sources.source_models import SourceWarning
from app.sources.source_models import stable_hash


# ============================================================
# SECTION 02 - CLIENT METADATA
# ============================================================

SOURCE_CLIENT_NAME = "Aussem1 Enterprise Source Client"

SOURCE_CLIENT_VERSION = "0.1.0"

SOURCE_CLIENT_PHASE = "PHASE 2.10 PART 4.00"

SOURCE_CLIENT_STATUS = "real_data_source_client_active"

DEFAULT_USER_AGENT = (
    "Aussem1-RealEstateIntelligence/0.1 "
    "(Source-governed public-record research client; "
    "contact: project-owner)"
)

DEFAULT_TIMEOUT_SECONDS = 25

DEFAULT_MAX_RETRIES = 1

DEFAULT_RETRY_DELAY_SECONDS = 1.25

MAX_RESPONSE_BYTES = 5_000_000


# ============================================================
# SECTION 03 - CLIENT GOVERNANCE
# ============================================================

SOURCE_CLIENT_GOVERNANCE = {
    "mock_data_allowed": False,
    "fabricated_response_allowed": False,
    "bypass_access_controls_allowed": False,
    "credential_stuffing_allowed": False,
    "uncontrolled_scraping_allowed": False,
    "respect_rate_limits_required": True,
    "timeouts_required": True,
    "user_agent_required": True,
    "source_status_required": True,
    "error_capture_required": True,
    "raw_response_storage_default": False,
    "public_records_are_not_listing_status": True,
    "listing_feed_required_for_active_listing_status": True,
}


# ============================================================
# SECTION 04 - UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.now(UTC).isoformat()


def normalize_url(
    url: str,
) -> str:
    """
    Normalize a URL string without changing its meaning.
    """

    return str(url or "").strip()


def is_http_url(
    url: str,
) -> bool:
    """
    Return whether URL is HTTP or HTTPS.
    """

    parsed = urllib.parse.urlparse(url)

    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def encode_query_parameters(
    params: dict[str, Any] | None,
) -> str:
    """
    Encode query parameters safely.
    """

    if not params:
        return ""

    clean_params: dict[str, str] = {}

    for key, value in params.items():
        if value is None:
            continue

        clean_params[str(key)] = str(value)

    return urllib.parse.urlencode(clean_params)


def append_query_parameters(
    url: str,
    params: dict[str, Any] | None,
) -> str:
    """
    Append query parameters to URL.
    """

    if not params:
        return url

    encoded = encode_query_parameters(params)

    if not encoded:
        return url

    separator = "&" if "?" in url else "?"

    return f"{url}{separator}{encoded}"


def safe_decode_bytes(
    payload: bytes,
    encoding: str | None = None,
) -> str:
    """
    Decode bytes safely.
    """

    if encoding:
        try:
            return payload.decode(encoding, errors="replace")
        except LookupError:
            pass

    return payload.decode("utf-8", errors="replace")


def detect_response_format(
    content_type: str | None,
    url: str | None = None,
) -> str:
    """
    Detect source data format from content type and URL.
    """

    content_type_value = (content_type or "").lower()
    url_value = (url or "").lower()

    if "application/json" in content_type_value or url_value.endswith(".json"):
        return SourceDataFormat.JSON.value

    if "text/html" in content_type_value or "application/xhtml" in content_type_value:
        return SourceDataFormat.HTML.value

    if "text/csv" in content_type_value or url_value.endswith(".csv"):
        return SourceDataFormat.CSV.value

    if "application/xml" in content_type_value or "text/xml" in content_type_value:
        return SourceDataFormat.XML.value

    if "application/pdf" in content_type_value or url_value.endswith(".pdf"):
        return SourceDataFormat.PDF.value

    if "image/" in content_type_value:
        return SourceDataFormat.IMAGE.value

    if "text/plain" in content_type_value:
        return SourceDataFormat.TEXT.value

    return SourceDataFormat.UNKNOWN.value


def parse_json_safely(
    text: str,
) -> tuple[Any | None, str | None]:
    """
    Parse JSON safely and return payload plus error.
    """

    try:
        return json.loads(text), None
    except json.JSONDecodeError as error:
        return None, str(error)


def make_request_id(
    method: str,
    url: str,
    params: dict[str, Any] | None = None,
) -> str:
    """
    Create stable request ID.
    """

    payload = {
        "method": method.upper().strip(),
        "url": url,
        "params": params or {},
        "timestamp_bucket": int(time.time() // 60),
    }

    return f"source-request-{stable_hash(payload)[:18]}"


# ============================================================
# SECTION 05 - CLIENT CONFIGURATION MODEL
# ============================================================

@dataclass
class SourceClientConfig:
    """
    Source client configuration.
    """

    user_agent: str = DEFAULT_USER_AGENT
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS
    max_response_bytes: int = MAX_RESPONSE_BYTES
    allow_raw_response_storage: bool = False
    allow_uncontrolled_scraping: bool = False
    allow_access_control_bypass: bool = False
    default_headers: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert config to dictionary.
        """

        return asdict(self)


# ============================================================
# SECTION 06 - REQUEST MODEL
# ============================================================

@dataclass
class SourceHttpRequest:
    """
    Structured source HTTP request.
    """

    request_id: str
    method: str
    url: str
    source_id: str | None = None
    source_name: str | None = None
    access_method: str = SourceAccessMethod.PUBLIC_WEB_PORTAL.value
    params: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | str | None = None
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    created_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert request to dictionary.
        """

        body_preview: str | None = None

        if isinstance(self.body, bytes):
            body_preview = f"<bytes:{len(self.body)}>"
        elif isinstance(self.body, str):
            body_preview = self.body[:500]

        return {
            "request_id": self.request_id,
            "method": self.method,
            "url": self.url,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "access_method": self.access_method,
            "params": self.params,
            "headers": self.headers,
            "body_preview": body_preview,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


# ============================================================
# SECTION 07 - RESPONSE MODEL
# ============================================================

@dataclass
class SourceHttpResponse:
    """
    Structured source HTTP response.
    """

    request_id: str
    url: str
    status: str
    http_status_code: int | None = None
    final_url: str | None = None
    content_type: str | None = None
    detected_format: str = SourceDataFormat.UNKNOWN.value
    text: str | None = None
    json_payload: Any | None = None
    byte_length: int = 0
    elapsed_ms: float | None = None
    headers: dict[str, str] = field(default_factory=dict)
    errors: list[SourceError] = field(default_factory=list)
    warnings: list[SourceWarning] = field(default_factory=list)
    retrieved_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(
        self,
        *,
        include_text: bool = False,
    ) -> dict[str, Any]:
        """
        Convert response to dictionary.
        """

        return {
            "request_id": self.request_id,
            "url": self.url,
            "status": self.status,
            "http_status_code": self.http_status_code,
            "final_url": self.final_url,
            "content_type": self.content_type,
            "detected_format": self.detected_format,
            "text": self.text if include_text else None,
            "json_payload": self.json_payload,
            "byte_length": self.byte_length,
            "elapsed_ms": self.elapsed_ms,
            "headers": self.headers,
            "errors": [
                error.to_dict()
                for error in self.errors
            ],
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
            "retrieved_at": self.retrieved_at,
            "metadata": self.metadata,
        }

    def is_successful(self) -> bool:
        """
        Return whether response is usable.
        """

        return (
            self.status in {
                SourceStatus.AVAILABLE.value,
                SourceStatus.PARTIAL.value,
            }
            and not self.errors
            and self.http_status_code is not None
            and 200 <= self.http_status_code < 300
        )


# ============================================================
# SECTION 08 - POLICY VALIDATION MODEL
# ============================================================

@dataclass
class SourceClientPolicyDecision:
    """
    Policy decision before request execution.
    """

    allowed: bool
    reason: str
    warnings: list[SourceWarning] = field(default_factory=list)
    errors: list[SourceError] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert decision to dictionary.
        """

        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "warnings": [
                warning.to_dict()
                for warning in self.warnings
            ],
            "errors": [
                error.to_dict()
                for error in self.errors
            ],
        }


# ============================================================
# SECTION 09 - SOURCE CLIENT CLASS
# ============================================================

class SourceClient:
    """
    Enterprise source-governed HTTP client.

    This is deliberately conservative. It gives future connectors a
    shared request layer without encouraging uncontrolled scraping or
    unsupported data claims.
    """

    def __init__(
        self,
        config: SourceClientConfig | None = None,
    ) -> None:
        self.config = config or SourceClientConfig()

    # ========================================================
    # SECTION 09.01 - POLICY VALIDATION
    # ========================================================

    def validate_policy(
        self,
        *,
        url: str,
        request_policy: SourceRequestPolicy | None = None,
    ) -> SourceClientPolicyDecision:
        """
        Validate whether request is allowed.
        """

        normalized = normalize_url(url)

        errors: list[SourceError] = []
        warnings: list[SourceWarning] = []

        if not normalized:
            errors.append(
                SourceError(
                    error_type=SourceErrorType.INVALID_QUERY.value,
                    message="Source request URL is empty.",
                    recoverable=True,
                    retry_recommended=False,
                    manual_review_required=False,
                )
            )

            return SourceClientPolicyDecision(
                allowed=False,
                reason="empty_url",
                errors=errors,
            )

        if not is_http_url(normalized):
            errors.append(
                SourceError(
                    error_type=SourceErrorType.INVALID_QUERY.value,
                    message="Only HTTP and HTTPS source URLs are supported.",
                    recoverable=True,
                    retry_recommended=False,
                    manual_review_required=False,
                    raw_error=normalized,
                )
            )

            return SourceClientPolicyDecision(
                allowed=False,
                reason="unsupported_url_scheme",
                errors=errors,
            )

        if self.config.allow_access_control_bypass:
            errors.append(
                SourceError(
                    error_type=SourceErrorType.MANUAL_REVIEW_REQUIRED.value,
                    message=(
                        "Client configuration attempts to allow access-control "
                        "bypass, which is not permitted."
                    ),
                    recoverable=False,
                    retry_recommended=False,
                    manual_review_required=True,
                )
            )

            return SourceClientPolicyDecision(
                allowed=False,
                reason="access_control_bypass_not_allowed",
                errors=errors,
            )

        if self.config.allow_uncontrolled_scraping:
            errors.append(
                SourceError(
                    error_type=SourceErrorType.MANUAL_REVIEW_REQUIRED.value,
                    message=(
                        "Client configuration attempts to allow uncontrolled "
                        "scraping, which is not permitted."
                    ),
                    recoverable=False,
                    retry_recommended=False,
                    manual_review_required=True,
                )
            )

            return SourceClientPolicyDecision(
                allowed=False,
                reason="uncontrolled_scraping_not_allowed",
                errors=errors,
            )

        if request_policy:
            if request_policy.bypass_access_controls_allowed:
                errors.append(
                    SourceError(
                        error_type=SourceErrorType.MANUAL_REVIEW_REQUIRED.value,
                        message=(
                            "Request policy attempts to allow bypassing "
                            "access controls."
                        ),
                        recoverable=False,
                        retry_recommended=False,
                        manual_review_required=True,
                    )
                )

            if request_policy.uncontrolled_scraping_allowed:
                errors.append(
                    SourceError(
                        error_type=SourceErrorType.MANUAL_REVIEW_REQUIRED.value,
                        message=(
                            "Request policy attempts to allow uncontrolled "
                            "scraping."
                        ),
                        recoverable=False,
                        retry_recommended=False,
                        manual_review_required=True,
                    )
                )

            if request_policy.timeout_seconds <= 0:
                warnings.append(
                    SourceWarning(
                        warning_code="invalid_timeout",
                        message=(
                            "Request policy timeout was invalid. "
                            "Default timeout will be used."
                        ),
                        severity="medium",
                    )
                )

        if errors:
            return SourceClientPolicyDecision(
                allowed=False,
                reason="policy_validation_failed",
                warnings=warnings,
                errors=errors,
            )

        return SourceClientPolicyDecision(
            allowed=True,
            reason="policy_validated",
            warnings=warnings,
        )

    # ========================================================
    # SECTION 09.02 - REQUEST BUILDING
    # ========================================================

    def build_headers(
        self,
        headers: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """
        Build request headers.
        """

        merged: dict[str, str] = {}

        merged.update(self.config.default_headers)

        if headers:
            merged.update(headers)

        if "User-Agent" not in merged:
            merged["User-Agent"] = self.config.user_agent

        if "Accept" not in merged:
            merged["Accept"] = (
                "application/json,text/html,application/xhtml+xml,"
                "text/plain,*/*;q=0.8"
            )

        return merged

    def build_request(
        self,
        *,
        method: str,
        url: str,
        source_id: str | None = None,
        source_name: str | None = None,
        access_method: str = SourceAccessMethod.PUBLIC_WEB_PORTAL.value,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        body: bytes | str | None = None,
        timeout_seconds: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SourceHttpRequest:
        """
        Build a source request.
        """

        normalized_url = normalize_url(url)

        request_id = make_request_id(
            method=method,
            url=normalized_url,
            params=params,
        )

        return SourceHttpRequest(
            request_id=request_id,
            method=method.upper().strip(),
            url=normalized_url,
            source_id=source_id,
            source_name=source_name,
            access_method=access_method,
            params=params or {},
            headers=self.build_headers(headers),
            body=body,
            timeout_seconds=timeout_seconds or self.config.timeout_seconds,
            metadata=metadata or {},
        )

    # ========================================================
    # SECTION 09.03 - LOW LEVEL EXECUTION
    # ========================================================

    def execute_request(
        self,
        request: SourceHttpRequest,
        *,
        request_policy: SourceRequestPolicy | None = None,
    ) -> SourceHttpResponse:
        """
        Execute a source request.
        """

        policy_decision = self.validate_policy(
            url=request.url,
            request_policy=request_policy,
        )

        if not policy_decision.allowed:
            return SourceHttpResponse(
                request_id=request.request_id,
                url=request.url,
                status=SourceStatus.ERROR.value,
                errors=policy_decision.errors,
                warnings=policy_decision.warnings,
                metadata={
                    "policy_decision": policy_decision.to_dict(),
                },
            )

        full_url = append_query_parameters(
            request.url,
            request.params,
        )

        body_bytes: bytes | None = None

        if isinstance(request.body, str):
            body_bytes = request.body.encode("utf-8")
        elif isinstance(request.body, bytes):
            body_bytes = request.body

        urllib_request = urllib.request.Request(
            url=full_url,
            data=body_bytes,
            headers=request.headers,
            method=request.method,
        )

        started = time.perf_counter()

        try:
            with urllib.request.urlopen(
                urllib_request,
                timeout=request.timeout_seconds,
            ) as response:
                raw_payload = response.read(
                    self.config.max_response_bytes + 1,
                )

                elapsed_ms = round(
                    (time.perf_counter() - started) * 1000,
                    3,
                )

                warnings = list(policy_decision.warnings)

                if len(raw_payload) > self.config.max_response_bytes:
                    raw_payload = raw_payload[: self.config.max_response_bytes]

                    warnings.append(
                        SourceWarning(
                            warning_code="response_truncated",
                            message=(
                                "Source response exceeded max_response_bytes "
                                "and was truncated."
                            ),
                            severity="medium",
                        )
                    )

                headers = {
                    str(key): str(value)
                    for key, value in response.headers.items()
                }

                content_type = headers.get("Content-Type")

                detected_format = detect_response_format(
                    content_type=content_type,
                    url=response.geturl(),
                )

                text = safe_decode_bytes(
                    raw_payload,
                    response.headers.get_content_charset(),
                )

                json_payload = None

                if detected_format == SourceDataFormat.JSON.value:
                    json_payload, parse_error = parse_json_safely(text)

                    if parse_error:
                        warnings.append(
                            SourceWarning(
                                warning_code="json_parse_warning",
                                message=parse_error,
                                severity="medium",
                            )
                        )

                return SourceHttpResponse(
                    request_id=request.request_id,
                    url=request.url,
                    status=SourceStatus.AVAILABLE.value,
                    http_status_code=response.status,
                    final_url=response.geturl(),
                    content_type=content_type,
                    detected_format=detected_format,
                    text=text,
                    json_payload=json_payload,
                    byte_length=len(raw_payload),
                    elapsed_ms=elapsed_ms,
                    headers=headers,
                    warnings=warnings,
                    metadata={
                        "source_id": request.source_id,
                        "source_name": request.source_name,
                        "method": request.method,
                        "params_present": bool(request.params),
                        "access_method": request.access_method,
                    },
                )

        except urllib.error.HTTPError as error:
            elapsed_ms = round(
                (time.perf_counter() - started) * 1000,
                3,
            )

            error_type = SourceErrorType.NETWORK_ERROR

            if error.code == 401 or error.code == 403:
                error_type = SourceErrorType.AUTH_REQUIRED
            elif error.code == 404:
                error_type = SourceErrorType.NOT_FOUND
            elif error.code == 429:
                error_type = SourceErrorType.RATE_LIMITED
            elif error.code >= 500:
                error_type = SourceErrorType.SOURCE_UNAVAILABLE

            return SourceHttpResponse(
                request_id=request.request_id,
                url=request.url,
                status=SourceStatus.ERROR.value,
                http_status_code=error.code,
                elapsed_ms=elapsed_ms,
                errors=[
                    SourceError(
                        error_type=error_type.value,
                        message=f"HTTP error from source: {error.code}",
                        source_id=request.source_id,
                        source_name=request.source_name,
                        recoverable=error.code in {429, 500, 502, 503, 504},
                        retry_recommended=error.code in {429, 500, 502, 503, 504},
                        manual_review_required=error.code in {401, 403},
                        raw_error=str(error),
                    )
                ],
                metadata={
                    "source_id": request.source_id,
                    "source_name": request.source_name,
                    "method": request.method,
                },
            )

        except urllib.error.URLError as error:
            elapsed_ms = round(
                (time.perf_counter() - started) * 1000,
                3,
            )

            reason = str(error.reason)

            error_type = SourceErrorType.NETWORK_ERROR

            if "timed out" in reason.lower():
                error_type = SourceErrorType.TIMEOUT

            return SourceHttpResponse(
                request_id=request.request_id,
                url=request.url,
                status=SourceStatus.ERROR.value,
                elapsed_ms=elapsed_ms,
                errors=[
                    SourceError(
                        error_type=error_type.value,
                        message="URL/network error while contacting source.",
                        source_id=request.source_id,
                        source_name=request.source_name,
                        recoverable=True,
                        retry_recommended=True,
                        manual_review_required=False,
                        raw_error=reason,
                    )
                ],
                metadata={
                    "source_id": request.source_id,
                    "source_name": request.source_name,
                    "method": request.method,
                },
            )

        except TimeoutError as error:
            elapsed_ms = round(
                (time.perf_counter() - started) * 1000,
                3,
            )

            return SourceHttpResponse(
                request_id=request.request_id,
                url=request.url,
                status=SourceStatus.ERROR.value,
                elapsed_ms=elapsed_ms,
                errors=[
                    SourceError(
                        error_type=SourceErrorType.TIMEOUT.value,
                        message="Source request timed out.",
                        source_id=request.source_id,
                        source_name=request.source_name,
                        recoverable=True,
                        retry_recommended=True,
                        raw_error=str(error),
                    )
                ],
            )

        except Exception as error:
            elapsed_ms = round(
                (time.perf_counter() - started) * 1000,
                3,
            )

            return SourceHttpResponse(
                request_id=request.request_id,
                url=request.url,
                status=SourceStatus.ERROR.value,
                elapsed_ms=elapsed_ms,
                errors=[
                    SourceError(
                        error_type=SourceErrorType.UNKNOWN.value,
                        message="Unexpected source client error.",
                        source_id=request.source_id,
                        source_name=request.source_name,
                        recoverable=False,
                        retry_recommended=False,
                        manual_review_required=True,
                        raw_error=str(error),
                    )
                ],
            )

    # ========================================================
    # SECTION 09.04 - RETRY WRAPPER
    # ========================================================

    def execute_with_retries(
        self,
        request: SourceHttpRequest,
        *,
        request_policy: SourceRequestPolicy | None = None,
    ) -> SourceHttpResponse:
        """
        Execute request with conservative retry behavior.
        """

        max_retries = self.config.max_retries

        if request_policy:
            max_retries = request_policy.max_retries

        attempts = 0
        last_response: SourceHttpResponse | None = None

        while attempts <= max_retries:
            attempts += 1

            response = self.execute_request(
                request,
                request_policy=request_policy,
            )

            response.metadata["attempt"] = attempts
            response.metadata["max_retries"] = max_retries

            if response.is_successful():
                return response

            last_response = response

            retry_recommended = any(
                error.retry_recommended
                for error in response.errors
            )

            if not retry_recommended:
                break

            if attempts <= max_retries:
                time.sleep(self.config.retry_delay_seconds)

        if last_response is None:
            return SourceHttpResponse(
                request_id=request.request_id,
                url=request.url,
                status=SourceStatus.ERROR.value,
                errors=[
                    SourceError(
                        error_type=SourceErrorType.UNKNOWN.value,
                        message="Request retry loop ended without response.",
                        source_id=request.source_id,
                        source_name=request.source_name,
                    )
                ],
            )

        return last_response

    # ========================================================
    # SECTION 09.05 - PUBLIC GET / POST HELPERS
    # ========================================================

    def get(
        self,
        url: str,
        *,
        source_id: str | None = None,
        source_name: str | None = None,
        access_method: str = SourceAccessMethod.PUBLIC_WEB_PORTAL.value,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        request_policy: SourceRequestPolicy | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SourceHttpResponse:
        """
        Execute governed GET request.
        """

        timeout = (
            request_policy.timeout_seconds
            if request_policy
            else self.config.timeout_seconds
        )

        request = self.build_request(
            method="GET",
            url=url,
            source_id=source_id,
            source_name=source_name,
            access_method=access_method,
            params=params,
            headers=headers,
            timeout_seconds=timeout,
            metadata=metadata,
        )

        return self.execute_with_retries(
            request,
            request_policy=request_policy,
        )

    def post(
        self,
        url: str,
        *,
        source_id: str | None = None,
        source_name: str | None = None,
        access_method: str = SourceAccessMethod.PUBLIC_WEB_PORTAL.value,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        body: bytes | str | None = None,
        request_policy: SourceRequestPolicy | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SourceHttpResponse:
        """
        Execute governed POST request.
        """

        timeout = (
            request_policy.timeout_seconds
            if request_policy
            else self.config.timeout_seconds
        )

        request = self.build_request(
            method="POST",
            url=url,
            source_id=source_id,
            source_name=source_name,
            access_method=access_method,
            params=params,
            headers=headers,
            body=body,
            timeout_seconds=timeout,
            metadata=metadata,
        )

        return self.execute_with_retries(
            request,
            request_policy=request_policy,
        )


# ============================================================
# SECTION 10 - DEFAULT CLIENT INSTANCE
# ============================================================

DEFAULT_SOURCE_CLIENT = SourceClient()


# ============================================================
# SECTION 11 - PUBLIC HELPER FUNCTIONS
# ============================================================

def governed_get(
    url: str,
    *,
    source_id: str | None = None,
    source_name: str | None = None,
    access_method: str = SourceAccessMethod.PUBLIC_WEB_PORTAL.value,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    request_policy: SourceRequestPolicy | None = None,
    metadata: dict[str, Any] | None = None,
) -> SourceHttpResponse:
    """
    Execute governed GET request with default client.
    """

    return DEFAULT_SOURCE_CLIENT.get(
        url,
        source_id=source_id,
        source_name=source_name,
        access_method=access_method,
        params=params,
        headers=headers,
        request_policy=request_policy,
        metadata=metadata,
    )


def governed_post(
    url: str,
    *,
    source_id: str | None = None,
    source_name: str | None = None,
    access_method: str = SourceAccessMethod.PUBLIC_WEB_PORTAL.value,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    body: bytes | str | None = None,
    request_policy: SourceRequestPolicy | None = None,
    metadata: dict[str, Any] | None = None,
) -> SourceHttpResponse:
    """
    Execute governed POST request with default client.
    """

    return DEFAULT_SOURCE_CLIENT.post(
        url,
        source_id=source_id,
        source_name=source_name,
        access_method=access_method,
        params=params,
        headers=headers,
        body=body,
        request_policy=request_policy,
        metadata=metadata,
    )


# ============================================================
# SECTION 12 - SOURCE URL PROBE
# ============================================================

def probe_source_url(
    url: str,
    *,
    source_id: str | None = None,
    source_name: str | None = None,
    request_policy: SourceRequestPolicy | None = None,
) -> dict[str, Any]:
    """
    Probe a source URL and return a compact health payload.
    """

    response = governed_get(
        url,
        source_id=source_id,
        source_name=source_name,
        request_policy=request_policy,
        metadata={
            "probe": True,
        },
    )

    return {
        "source_id": source_id,
        "source_name": source_name,
        "url": url,
        "status": response.status,
        "http_status_code": response.http_status_code,
        "content_type": response.content_type,
        "detected_format": response.detected_format,
        "byte_length": response.byte_length,
        "elapsed_ms": response.elapsed_ms,
        "error_count": len(response.errors),
        "warning_count": len(response.warnings),
        "errors": [
            error.to_dict()
            for error in response.errors
        ],
        "warnings": [
            warning.to_dict()
            for warning in response.warnings
        ],
        "retrieved_at": response.retrieved_at,
    }


# ============================================================
# SECTION 13 - CLIENT DIAGNOSTICS
# ============================================================

def get_source_client_metadata() -> dict[str, Any]:
    """
    Return source client metadata.
    """

    return {
        "name": SOURCE_CLIENT_NAME,
        "version": SOURCE_CLIENT_VERSION,
        "phase": SOURCE_CLIENT_PHASE,
        "status": SOURCE_CLIENT_STATUS,
        "default_timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "default_max_retries": DEFAULT_MAX_RETRIES,
        "max_response_bytes": MAX_RESPONSE_BYTES,
        "generated_at": utc_now(),
    }


def get_source_client_governance() -> dict[str, Any]:
    """
    Return source client governance.
    """

    return SOURCE_CLIENT_GOVERNANCE.copy()


def get_source_client_health() -> dict[str, Any]:
    """
    Return source client health.
    """

    return {
        "name": SOURCE_CLIENT_NAME,
        "version": SOURCE_CLIENT_VERSION,
        "phase": SOURCE_CLIENT_PHASE,
        "status": SOURCE_CLIENT_STATUS,
        "mock_data_allowed": SOURCE_CLIENT_GOVERNANCE["mock_data_allowed"],
        "fabricated_response_allowed": SOURCE_CLIENT_GOVERNANCE[
            "fabricated_response_allowed"
        ],
        "bypass_access_controls_allowed": SOURCE_CLIENT_GOVERNANCE[
            "bypass_access_controls_allowed"
        ],
        "uncontrolled_scraping_allowed": SOURCE_CLIENT_GOVERNANCE[
            "uncontrolled_scraping_allowed"
        ],
        "default_client_loaded": isinstance(
            DEFAULT_SOURCE_CLIENT,
            SourceClient,
        ),
        "generated_at": utc_now(),
    }


# ============================================================
# SECTION 14 - PUBLIC EXPORTS
# ============================================================

__all__ = [
    "SOURCE_CLIENT_NAME",
    "SOURCE_CLIENT_VERSION",
    "SOURCE_CLIENT_PHASE",
    "SOURCE_CLIENT_STATUS",
    "DEFAULT_USER_AGENT",
    "DEFAULT_TIMEOUT_SECONDS",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_RETRY_DELAY_SECONDS",
    "MAX_RESPONSE_BYTES",
    "SOURCE_CLIENT_GOVERNANCE",
    "SourceClientConfig",
    "SourceHttpRequest",
    "SourceHttpResponse",
    "SourceClientPolicyDecision",
    "SourceClient",
    "DEFAULT_SOURCE_CLIENT",
    "utc_now",
    "normalize_url",
    "is_http_url",
    "encode_query_parameters",
    "append_query_parameters",
    "safe_decode_bytes",
    "detect_response_format",
    "parse_json_safely",
    "make_request_id",
    "governed_get",
    "governed_post",
    "probe_source_url",
    "get_source_client_metadata",
    "get_source_client_governance",
    "get_source_client_health",
]


# ============================================================
# END OF FILE
# ============================================================