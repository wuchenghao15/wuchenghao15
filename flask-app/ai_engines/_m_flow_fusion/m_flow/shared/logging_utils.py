"""
Centralised logging bootstrap for the **m_flow** framework.

Provides:

* :func:`setup_logging`          – one-shot initialisation (structlog + stdlib)
* :func:`get_logger`             – convenience accessor used across the codebase
* :func:`get_log_file_location`  – path of the currently active log on disk
* Level aliases: ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL``

Internal details
~~~~~~~~~~~~~~~~
The module keeps a thin layer between *structlog* and the rest of the
application so that callers never need to decide between ``structlog``
and ``logging`` themselves.  Before ``setup_logging`` is invoked for the
first time, :func:`get_logger` silently returns a plain stdlib logger so
that import-time logging still works.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import platform
import sys
import traceback as _tb_mod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

import structlog

from m_flow import __version__ as _pkg_version

# ---------------------------------------------------------------------------
# Public level re-exports – keeps callers from importing ``logging`` directly.
# ---------------------------------------------------------------------------
DEBUG: int = logging.DEBUG
INFO: int = logging.INFO
WARNING: int = logging.WARNING
ERROR: int = logging.ERROR
CRITICAL: int = logging.CRITICAL

log_levels: Dict[str, int] = {
    "DEBUG": DEBUG,
    "INFO": INFO,
    "WARNING": WARNING,
    "ERROR": ERROR,
    "CRITICAL": CRITICAL,
    "NOTSET": logging.NOTSET,
}

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------
_structlog_ready: bool = False

# Caps how many rotated log files we retain.
_RETAINED_LOGS: int = 10


# ===================================================================
# Logger protocol & accessor
# ===================================================================


class LoggerInterface(Protocol):
    """Structural sub-type that every logger returned by :func:`get_logger` satisfies."""

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None: ...


def get_logger(name: Optional[str] = None, level: Optional[int] = None) -> LoggerInterface:  # type: ignore[return]
    """Obtain a logger bound to *name*.

    After :func:`setup_logging` has been called the returned object is a
    *structlog* bound-logger; otherwise a plain :mod:`logging` logger is
    given back so that import-time messages are not lost.
    """
    identifier = name or __name__
    if _structlog_ready:
        return structlog.get_logger(identifier)
    fallback = logging.getLogger(identifier)
    if level is not None:
        fallback.setLevel(level)
    return fallback


# ===================================================================
# Timestamp helper
# ===================================================================


def _pick_timestamp_fmt() -> str:
    """Return the richest timestamp pattern the platform supports.

    A few embedded Python environments raise ``ValueError`` when ``%f``
    (microseconds) appears in a *strftime* call.  We probe once and fall
    back to second-level granularity when that happens.
    """
    candidate = "%Y-%m-%dT%H:%M:%S.%f"
    try:
        datetime.now().strftime(candidate)
        return candidate
    except (ValueError, OSError):
        return "%Y-%m-%dT%H:%M:%S"


# Keep the old name available for any in-tree callers.
get_timestamp_format = _pick_timestamp_fmt


# ===================================================================
# External-library noise reduction
# ===================================================================

_NOISY_LOGGERS: List[str] = [
    "litellm",
    "litellm.litellm_core_utils",
    "litellm.litellm_core_utils.logging_worker",
    "litellm.logging_worker",
    "litellm.proxy",
    "litellm.router",
    "LiteLLM",
    "LiteLLM.core",
    "LiteLLM.logging_worker",
    "openai._base_client",
]

_SUPPRESSED_PHRASES: List[str] = [
    "loggingworker cancelled",
    "logging_worker.py",
    "cancellederror",
    "litellm:error",
    "loggingerror",
]


def _silence_third_party_loggers() -> None:
    """Dial external libraries down to CRITICAL-only and set env hints."""
    os.environ.setdefault("LITELLM_LOG", "ERROR")
    os.environ.setdefault("LITELLM_SET_VERBOSE", "False")
    try:
        import litellm  # type: ignore[import-untyped]

        litellm.set_verbose = False
        for attr in ("suppress_debug_info", "turn_off_message"):
            if hasattr(litellm, attr):
                setattr(litellm, attr, True)
        if hasattr(litellm, "_turn_on_debug"):
            litellm._turn_on_debug = False

        for lgr_name in _NOISY_LOGGERS:
            ref = logging.getLogger(lgr_name)
            ref.setLevel(logging.CRITICAL)
            ref.disabled = True
    except ImportError:
        pass


class _ThirdPartyNoiseGate(logging.Filter):
    """Drop log records that originate from (or mention) noisy libraries."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        if getattr(record, "name", "") and "litellm" in record.name.lower():
            return False
        raw = str(getattr(record, "msg", "")).lower()
        if any(p in raw for p in _SUPPRESSED_PHRASES):
            return False
        try:
            full = record.getMessage().lower()
            if any(p in full for p in _SUPPRESSED_PHRASES):
                return False
        except Exception:
            pass
        return True


# ===================================================================
# Plain-text file handler
# ===================================================================


class PlainFileHandler(logging.handlers.RotatingFileHandler):
    """Writes human-readable single-line entries with automatic rotation.

    *structlog* passes records whose ``msg`` attribute is a dict; stdlib
    records carry a plain string.  This handler normalises both styles
    into a uniform ``TIMESTAMP [LEVEL   ] message [logger]`` layout.

    Rotates at *maxBytes* (default 100 MB) keeping *backupCount* old files.
    """

    def __init__(self, filename, mode="a", maxBytes=0, backupCount=0, encoding=None, **kwargs):
        _max = int(os.getenv("LOG_FILE_MAX_BYTES", str(maxBytes or 100_000_000)))
        _keep = int(os.getenv("LOG_FILE_BACKUP_COUNT", str(backupCount or 5)))
        super().__init__(filename, mode=mode, maxBytes=_max, backupCount=_keep, encoding=encoding, **kwargs)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if self.stream is None:
                self.stream = self._open()
            if isinstance(record.msg, dict) and "event" in record.msg:
                self._write_structured(record)
            else:
                self._write_plain(record)
            if self.shouldRollover(record):
                self.doRollover()
        except Exception:
            self.handleError(record)
            try:
                self.stream.write(f"Error in log handler: {sys.exc_info()[1]}\n")
                self.flush()
            except Exception:
                pass

    # -- private helpers --------------------------------------------------

    def _write_structured(self, record: logging.LogRecord) -> None:
        payload: Dict[str, Any] = record.msg  # type: ignore[assignment]
        event_text = payload.get("event", "")
        extras = {k: v for k, v in payload.items() if k not in {"event", "logger", "level", "timestamp", "exc_info"}}
        extra_segment = (" " + " ".join(f"{k}={v}" for k, v in extras.items())) if extras else ""
        origin = payload.get("logger", record.name)
        ts = datetime.now().strftime(_pick_timestamp_fmt())

        self.stream.write(f"{ts} [{record.levelname.ljust(8)}] {event_text}{extra_segment} [{origin}]\n")
        self.flush()
        self._maybe_write_traceback(record, payload)

    def _write_plain(self, record: logging.LogRecord) -> None:
        formatted = self.format(record)
        self.stream.write(formatted + self.terminator)
        self.flush()
        if record.exc_info and record.exc_info != (None, None, None):
            self.stream.write("".join(_tb_mod.format_exception(*record.exc_info)) + "\n")
            self.flush()

    def _maybe_write_traceback(
        self,
        record: logging.LogRecord,
        payload: Dict[str, Any],
    ) -> None:
        exc_from_record = record.exc_info and record.exc_info != (None, None, None)
        exc_in_payload = payload.get("exc_info")

        if exc_from_record:
            self.stream.write("".join(_tb_mod.format_exception(*record.exc_info)) + "\n")
            self.flush()
        elif isinstance(exc_in_payload, tuple):
            self.stream.write("".join(_tb_mod.format_exception(*exc_in_payload)) + "\n")
            self.flush()
        elif exc_in_payload and hasattr(exc_in_payload, "__traceback__"):
            exc_obj = exc_in_payload
            self.stream.write("".join(_tb_mod.format_exception(type(exc_obj), exc_obj, exc_obj.__traceback__)) + "\n")
            self.flush()


# ===================================================================
# Log-directory resolution & rotation
# ===================================================================


def resolve_logs_dir() -> Optional[Path]:
    """Find (or create) a writable directory for log files.

    Resolution order:

    1. ``BaseConfig.logs_root_directory`` (honours ``MFLOW_LOGS_DIR``)
    2. ``/tmp/m_flow_logs`` as a best-effort fallback
    """
    from m_flow.base_config import get_base_config

    primary = Path(get_base_config().logs_root_directory)
    for candidate in (primary, Path("/tmp/m_flow_logs")):
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            if os.access(candidate, os.W_OK):
                return candidate
        except OSError:
            continue
    return None


def _prune_stale_logs(directory: Path, keep: int) -> None:
    """Delete the oldest ``*.log`` files so that at most *keep* remain."""
    log_entries = sorted(
        (p for p in directory.glob("*.log") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if len(log_entries) <= keep:
        return
    is_cli = os.getenv("MFLOW_CLI_MODE") == "true"
    removed = 0
    for stale in log_entries[keep:]:
        try:
            stale.unlink()
            removed += 1
            if not is_cli:
                structlog.get_logger().info("Deleted old log file: %s", stale)
        except OSError as exc:
            structlog.get_logger().error("Failed to delete old log file %s: %s", stale, exc)
    if is_cli and removed:
        structlog.get_logger().info("Cleaned up %d old log files", removed)


# Keep the old name available for any in-tree callers.
def cleanup_old_logs(logs_dir, max_files):
    return _prune_stale_logs(logs_dir, max_files)


# ===================================================================
# Database-info logging helper
# ===================================================================


def log_database_configuration(logger: Any) -> None:
    """Emit a summary line about the active storage backends."""

    try:
        from m_flow.base_config import get_base_config

        db_root = os.path.join(get_base_config().system_root_directory, "databases")
        logger.info("Database storage: %s", db_root)
    except Exception as err:
        logger.debug("Could not retrieve database configuration: %s", err)


# ===================================================================
# Main entry-point
# ===================================================================


def setup_logging(
    log_level: Optional[int] = None,
    name: Optional[str] = None,
) -> Any:
    """Bootstrap the entire logging subsystem (structlog + stdlib).

    This function is meant to be called **once** at application start.
    Subsequent calls are safe but will reconfigure handlers.

    Parameters
    ----------
    log_level:
        Effective level for console output.  Defaults to the ``LOG_LEVEL``
        environment variable (or ``INFO``).
    name:
        Logger name used in the initial banner messages.

    Returns
    -------
    A fully configured *structlog* bound-logger.
    """
    global _structlog_ready

    effective_level = log_level or log_levels.get(os.getenv("LOG_LEVEL", "INFO").upper(), INFO)

    # 1. Hush noisy third-party libraries *before* touching handlers.
    _silence_third_party_loggers()

    # 2. Install filters on the root logger.
    noise_gate = _ThirdPartyNoiseGate()
    logging.getLogger().addFilter(noise_gate)
    logging.getLogger("litellm").addFilter(noise_gate)

    # 3. structlog processor pipeline.
    def _enrich_exception(_logger: Any, _method: str, event: Dict[str, Any]) -> Dict[str, Any]:
        exc_info = event.get("exc_info")
        if not exc_info:
            return event
        if isinstance(exc_info, tuple):
            etype, evalue, _tb = exc_info
        else:
            etype, evalue, _tb = sys.exc_info()
        if etype is not None and hasattr(etype, "__name__"):
            event["exception_type"] = etype.__name__
        event["exception_message"] = str(evalue)
        event["traceback"] = True
        return event

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt=_pick_timestamp_fmt(), utc=True),
            structlog.processors.StackInfoRenderer(),
            _enrich_exception,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 4. Global exception hook – log and re-raise via the default hook.
    def _unhandled(exc_type: type, exc_val: BaseException, exc_tb: Any) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_val, exc_tb)
            return
        structlog.get_logger().error(
            "Exception",
            exc_info=(exc_type, exc_val, exc_tb),
        )
        sys.__excepthook__(exc_type, exc_val, exc_tb)

    sys.excepthook = _unhandled

    # 5. Console handler (coloured, via structlog renderer).
    _colour_map = {
        "critical": structlog.dev.RED,
        "exception": structlog.dev.RED,
        "error": structlog.dev.RED,
        "warn": structlog.dev.YELLOW,
        "warning": structlog.dev.YELLOW,
        "info": structlog.dev.GREEN,
        "debug": structlog.dev.BLUE,
    }
    renderer = structlog.dev.ConsoleRenderer(
        colors=True,
        force_colors=True,
        level_styles=_colour_map,
    )
    console_fmt = structlog.stdlib.ProcessorFormatter(processor=renderer)

    class _PaddedStreamHandler(logging.StreamHandler):
        """Prepend a newline so that structlog output never collides with prompts."""

        def emit(self, record: logging.LogRecord) -> None:
            try:
                text = self.format(record)
                dest = self.stream
                if getattr(dest, "closed", False):
                    return
                dest.write("\n" + text + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)

    console_handler = _PaddedStreamHandler(sys.stderr)
    console_handler.setFormatter(console_fmt)
    console_handler.setLevel(effective_level)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(console_handler)
    root.setLevel(logging.NOTSET)

    # 6. File handler (plain text, DEBUG level).
    logs_dir = resolve_logs_dir()
    log_file = os.environ.get("LOG_FILE_NAME")
    if not log_file and logs_dir is not None:
        ts_tag = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = str((logs_dir / f"{ts_tag}.log").resolve())
        os.environ["LOG_FILE_NAME"] = log_file
    try:
        disk_handler = PlainFileHandler(log_file, encoding="utf-8")
        file_log_level = log_levels.get(os.getenv("LOG_FILE_LEVEL", "DEBUG").upper(), DEBUG)
        disk_handler.setLevel(file_log_level)
        root.addHandler(disk_handler)
    except Exception as file_err:
        root.warning("Could not create log file handler at %s: %s", log_file, file_err)

    # 7. Housekeeping – trim old log files.
    if logs_dir is not None:
        _prune_stale_logs(logs_dir, _RETAINED_LOGS)

    _structlog_ready = True

    # 9. Collect runtime metadata and emit the startup banner.
    from m_flow.adapters.relational.config import get_relational_config
    from m_flow.adapters.vector.config import get_vectordb_config
    from m_flow.adapters.graph.config import get_graph_config
    from m_flow.base_config import get_base_config

    graph_cfg = get_graph_config()
    vec_cfg = get_vectordb_config()
    rel_cfg = get_relational_config()

    try:
        databases_root = os.path.join(get_base_config().system_root_directory, "databases")
    except Exception as exc:
        raise ValueError from exc

    banner_logger = structlog.get_logger(name or __name__)

    banner_logger.warning(
        "Multi-user access control is enabled. Each user's data is isolated — "
        "content ingested before this mode was activated may not be visible. "
        "Set ENABLE_BACKEND_ACCESS_CONTROL=false to revert to single-user mode."
    )

    if logs_dir is not None:
        banner_logger.info("Log file created at: %s", log_file, log_file=log_file)

    banner_logger.info(
        "Logging initialized",
        python_version=platform.python_version(),
        structlog_version=structlog.__version__,
        m_flow_version=_pkg_version,
        os_info=f"{platform.system()} {platform.release()} ({platform.version()})",
        database_path=databases_root,
        graph_database_name=graph_cfg.graph_database_name,
        vector_config=vec_cfg.vector_db_provider,
        relational_config=rel_cfg.db_name,
    )

    log_database_configuration(banner_logger)
    return banner_logger


# ===================================================================
# Utility
# ===================================================================


def get_log_file_location() -> Optional[str]:
    """Return the absolute path of the current on-disk log, if any."""
    for h in logging.getLogger().handlers:
        if isinstance(h, logging.FileHandler):
            return h.baseFilename
    return None
