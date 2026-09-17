"""Unit tests for ``m_flow.shared.utils.to_iso_z`` (issue #116).

The legacy idiom ``dt.isoformat() + "Z"`` produced a malformed double timezone
marker (``"…+00:00Z"``) when the datetime was timezone-aware — for example
when read from a Postgres ``timestamp with time zone`` column. Pydantic
rejected those strings with ``datetime_from_date_parsing``, causing
``ActivityDTO``, ``DatasetDTO`` and ``Dataset.to_json()`` callers to crash
with HTTP 500.

These tests pin the corrected behaviour: a single, well-formed UTC marker in
every input case.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from m_flow.shared.utils import to_iso_z


class TestToIsoZ:
    """Pinning ``to_iso_z`` semantics across naive / aware inputs."""

    def test_returns_none_for_none_input(self) -> None:
        assert to_iso_z(None) is None

    def test_naive_datetime_keeps_isoformat_and_appends_single_z(self) -> None:
        # The same shape the legacy ``+ "Z"`` idiom produced for naive values.
        assert to_iso_z(datetime(2026, 4, 23, 1, 38, 12, 734433)) == "2026-04-23T01:38:12.734433Z"

    def test_naive_datetime_without_microseconds(self) -> None:
        assert to_iso_z(datetime(2026, 4, 23, 12, 30, 0)) == "2026-04-23T12:30:00Z"

    def test_aware_utc_datetime_does_not_emit_double_marker(self) -> None:
        # Regression for issue #116: a Postgres ``timestamp with time zone``
        # column yields a tzinfo-aware datetime in UTC; the legacy idiom
        # produced ``2026-04-23T01:38:12.734433+00:00Z``.
        result = to_iso_z(datetime(2026, 4, 23, 1, 38, 12, 734433, tzinfo=timezone.utc))
        assert result == "2026-04-23T01:38:12.734433Z"
        assert "+00:00" not in (result or "")
        assert (result or "").count("Z") == 1

    def test_aware_non_utc_datetime_is_normalised_to_utc(self) -> None:
        # 09:38 +08:00 is the same instant as 01:38 UTC.
        beijing = timezone(timedelta(hours=8))
        result = to_iso_z(datetime(2026, 4, 23, 9, 38, 12, 734433, tzinfo=beijing))
        assert result == "2026-04-23T01:38:12.734433Z"

    def test_negative_offset_is_normalised(self) -> None:
        eastern = timezone(timedelta(hours=-5))
        result = to_iso_z(datetime(2026, 4, 22, 20, 38, 12, 734433, tzinfo=eastern))
        assert result == "2026-04-23T01:38:12.734433Z"

    @pytest.mark.parametrize(
        "dt",
        [
            datetime(2026, 1, 1, 0, 0, 0),
            datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone(timedelta(hours=8))),
        ],
    )
    def test_output_is_pydantic_parseable(self, dt: datetime) -> None:
        # The original failure mode in #116 was pydantic refusing to accept the
        # serialized string; verify any output ``to_iso_z`` produces survives a
        # full parse round-trip.
        from pydantic import TypeAdapter

        s = to_iso_z(dt)
        assert s is not None
        parsed = TypeAdapter(datetime).validate_python(s)
        assert parsed.tzinfo is not None
        assert parsed.utcoffset() == timedelta(0)
