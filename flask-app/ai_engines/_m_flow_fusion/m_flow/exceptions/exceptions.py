"""
Unified exception taxonomy for the M-Flow platform.

All API-level errors derive from :class:`ServiceFault` and carry an HTTP
status code plus an optional structured payload for rich client diagnostics.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, Dict, Literal

from m_flow.shared.logging_utils import get_logger

_log = get_logger()

LogSeverity = Literal["debug", "info", "warning", "error"]


class ServiceFault(Exception):
    """
    Root of the M-Flow exception hierarchy.

    Parameters
    ----------
    detail
        Human-readable description of the problem.
    kind
        Short classifier (used in structured responses).
    http_status
        HTTP status code to return if the exception propagates to the API layer.
    log
        Whether to log this exception automatically.
    log_level
        Logging level for automatic on-raise logging.
    """

    def __init__(
        self,
        detail: str = "An unexpected fault occurred.",
        kind: str = "ServiceFault",
        http_status: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        log: bool = True,
        log_level: str = "ERROR",
    ) -> None:
        super().__init__(detail)
        self.message = detail
        self.detail = detail
        self.kind = kind
        self.name = kind
        self.http_status = http_status
        self.status_code = http_status

        if log:
            severity = log_level.lower()
            self._emit_log(severity)

    def _emit_log(self, sev: str) -> None:
        msg = f"{self.kind}: {self.detail} (Status code: {self.http_status})"
        log_fn = getattr(_log, sev, _log.error)
        log_fn(msg)

    def __repr__(self) -> str:
        detail = getattr(self, "detail", getattr(self, "message", ""))
        code = getattr(self, "http_status", getattr(self, "status_code", "?"))
        return f"{self.__class__.__name__}({detail!r}, http_status={code})"

    def __str__(self) -> str:
        kind = getattr(self, "kind", getattr(self, "name", self.__class__.__name__))
        detail = getattr(self, "detail", getattr(self, "message", ""))
        code = getattr(self, "http_status", getattr(self, "status_code", "?"))
        return f"{kind}: {detail} (Status code: {code})"

    def as_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "detail": self.detail, "http_status": self.http_status}


# ---------------------------------------------------------------------------
# Concrete fault classes
# ---------------------------------------------------------------------------


class InternalError(ServiceFault):
    """Unexpected server-side failure."""

    def __init__(
        self,
        detail: str = "Internal server error.",
        kind: str = "InternalError",
        http_status: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        log: bool = True,
        log_level: str = "ERROR",
    ) -> None:
        super().__init__(detail, kind, http_status, log, log_level)


class BadInputError(ServiceFault):
    """Client provided malformed or invalid input."""

    def __init__(
        self,
        detail: str = "Invalid input.",
        kind: str = "BadInputError",
        http_status: int = HTTPStatus.UNPROCESSABLE_ENTITY,
        log: bool = True,
        log_level: str = "ERROR",
    ) -> None:
        super().__init__(detail, kind, http_status, log, log_level)


class ConfigError(ServiceFault):
    """Server misconfiguration detected at runtime."""

    def __init__(
        self,
        detail: str = "Configuration error.",
        kind: str = "ConfigError",
        http_status: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        log: bool = True,
        log_level: str = "ERROR",
    ) -> None:
        super().__init__(detail, kind, http_status, log, log_level)


class TransientError(ServiceFault):
    """Temporary failure; client may retry."""

    def __init__(
        self,
        detail: str = "Service temporarily unavailable.",
        kind: str = "TransientError",
        http_status: int = HTTPStatus.SERVICE_UNAVAILABLE,
        log: bool = True,
        log_level: str = "ERROR",
    ) -> None:
        super().__init__(detail, kind, http_status, log, log_level)


# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------

ServiceFault = ServiceFault
InternalError = InternalError
BadInputError = BadInputError
ConfigError = ConfigError
TransientError = TransientError
