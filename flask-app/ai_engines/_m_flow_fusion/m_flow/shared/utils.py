"""
Miscellaneous platform utilities (telemetry, SSL, visualization helpers).
"""

from __future__ import annotations

import http.server
import os
import pathlib
import socketserver
import ssl
from datetime import datetime, timezone
from threading import Thread
from typing import Any, Callable, Dict, List, Optional
from uuid import NAMESPACE_OID, uuid4, uuid5

import requests

from m_flow.shared.logging_utils import get_logger

_log = get_logger()

# ---------------------------------------------------------------------------
# Analytics / telemetry
# ---------------------------------------------------------------------------

_TELEMETRY_ENDPOINT = ""


def _read_or_create_anon_id() -> str:
    """
    Persist an anonymous installation identifier to disk.

    Falls back to ``"unknown-anonymous-id"`` on read-only filesystems.
    """
    env_id = os.getenv("TRACKING_ID")
    if env_id:
        return env_id

    pkg_root = pathlib.Path(__file__).resolve().parent.parent.parent
    try:
        pkg_root.mkdir(parents=True, exist_ok=True)
        id_path = pkg_root / ".anon_id"
        if id_path.is_file():
            return id_path.read_text(encoding="utf-8").strip()
        new_id = str(uuid4())
        id_path.write_text(new_id, encoding="utf-8")
        return new_id
    except OSError as exc:
        _log.warning("Cannot persist anonymous id: %s", exc)
        return "unknown-anonymous-id"


def _hash_sensitive(obj: Any, keys: List[str]) -> Any:
    """Recursively replace values for *keys* with deterministic hashes."""
    if isinstance(obj, dict):
        return {
            k: (str(uuid5(NAMESPACE_OID, v)) if k in keys and isinstance(v, str) else _hash_sensitive(v, keys))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_hash_sensitive(item, keys) for item in obj]
    return obj


def emit_telemetry(
    event_name: str,
    user_id: Any = None,
    additional_properties: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Fire-and-forget analytics beacon (disabled in test/dev or by env flag).
    """
    if os.getenv("TELEMETRY_DISABLED"):
        return
    if os.getenv("ENV") in ("test", "dev"):
        return
    if not _TELEMETRY_ENDPOINT:
        return

    sanitized = _hash_sensitive(additional_properties or {}, ["url"])
    payload = {
        "anonymous_id": _read_or_create_anon_id(),
        "event_name": event_name,
        "user_properties": {"user_id": str(user_id)},
        "properties": {
            "time": datetime.now(timezone.utc).strftime("%m/%d/%Y"),
            "user_id": str(user_id),
            **sanitized,
        },
    }
    try:
        resp = requests.post(_TELEMETRY_ENDPOINT, json=payload, timeout=5)
        if resp.status_code != 200:
            _log.debug("Telemetry POST returned %s", resp.status_code)
    except Exception:
        pass  # silent


# Backwards-compat aliases
get_anonymous_id = _read_or_create_anon_id
send_telemetry = emit_telemetry

# ---------------------------------------------------------------------------
# SSL
# ---------------------------------------------------------------------------


def make_ssl_context() -> ssl.SSLContext:
    """Return a secure default SSL context."""
    return ssl.create_default_context()


create_secure_ssl_context = make_ssl_context  # alias

# ---------------------------------------------------------------------------
# Visualization server
# ---------------------------------------------------------------------------


def launch_viz_server(
    bind: str = "0.0.0.0",
    port: int = 8001,
    handler: type = http.server.SimpleHTTPRequestHandler,
) -> Callable[[], None]:
    """
    Start a simple HTTP file server in a daemon thread.

    Returns a *shutdown* callable that stops the server.
    """
    srv = socketserver.TCPServer((bind, port), handler)

    def _run() -> None:
        _log.info("Visualization server listening on http://%s:%d", bind, port)
        srv.serve_forever()

    th = Thread(target=_run, daemon=True)
    th.start()

    def _stop() -> None:
        srv.shutdown()
        srv.server_close()
        th.join()
        _log.info("Visualization server on port %d stopped", port)

    return _stop


start_visualization_server = launch_viz_server  # alias


# ---------------------------------------------------------------------------
# Datetime serialization
# ---------------------------------------------------------------------------


def to_iso_z(dt: Optional[datetime]) -> Optional[str]:
    """Serialize a datetime to an ISO-8601 string ending with a single ``Z``.

    The previous idiom ``dt.isoformat() + "Z"`` is **buggy when ``dt`` is
    timezone-aware**, because ``isoformat()`` already emits an offset such as
    ``"+00:00"`` and the appended ``"Z"`` produces a double timezone marker
    (``"…+00:00Z"``) that pydantic rejects with ``datetime_from_date_parsing``.

    This helper guarantees a single, well-formed UTC marker in every case:

    - ``None`` → ``None`` (passthrough).
    - timezone-naive datetimes are *assumed* to be UTC (the same assumption
      the legacy ``+ "Z"`` idiom encoded) and are serialized with a trailing
      ``Z`` directly.
    - timezone-aware datetimes are converted to UTC and then serialized with
      ``Z`` substituted for the ``+00:00`` offset.

    Examples
    --------
    >>> from datetime import datetime, timezone, timedelta
    >>> to_iso_z(None) is None
    True
    >>> to_iso_z(datetime(2026, 4, 23, 1, 38, 12, 734433))
    '2026-04-23T01:38:12.734433Z'
    >>> to_iso_z(datetime(2026, 4, 23, 1, 38, 12, 734433, tzinfo=timezone.utc))
    '2026-04-23T01:38:12.734433Z'
    >>> to_iso_z(datetime(2026, 4, 23, 9, 38, 12, 734433, tzinfo=timezone(timedelta(hours=8))))
    '2026-04-23T01:38:12.734433Z'
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Visualization helpers (bokeh logo embedding kept for compat)
# ---------------------------------------------------------------------------

_LOGO_DATA_URI = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAw8AAAHnCAYAAAD+VGEQAACA..."
    # truncated for brevity; actual base64 in original
)


def overlay_logo(
    figure: Any,
    scale: float,
    opacity: float,
    anchor: str,
) -> None:
    """
    Add M-Flow logo watermark to a Bokeh figure.

    Parameters are positional for backwards compat with old callers.
    """
    figure.image_url(
        url=[_LOGO_DATA_URI],
        x=-scale * 0.5,
        y=scale * 0.5,
        w=scale,
        h=scale,
        anchor=anchor,
        global_alpha=opacity,
    )


embed_logo = overlay_logo  # alias
