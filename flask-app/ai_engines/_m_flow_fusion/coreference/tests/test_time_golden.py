"""
Golden regression tests for time normalization.
"""

import pytest
from datetime import datetime
from coreference_module import normalize_time


REF = datetime(2026, 2, 7)  # reference date for tests


class TestRelativeDay:
    def test_yesterday(self):
        r = normalize_time("昨天", REF)
        assert r.precision == "DAY"
        assert r.start_dt.day == 6

    def test_today(self):
        r = normalize_time("今天", REF)
        assert r.precision == "DAY"
        assert r.start_dt.day == 7

    def test_tomorrow(self):
        r = normalize_time("明天", REF)
        assert r.precision == "DAY"
        assert r.start_dt.day == 8


class TestRelativeWeek:
    def test_this_week(self):
        r = normalize_time("这周", REF)
        assert r.precision == "WEEK"

    def test_last_week(self):
        r = normalize_time("上周", REF)
        assert r.precision == "WEEK"


class TestRelativeMonth:
    def test_this_month(self):
        r = normalize_time("这个月", REF)
        assert r.precision == "MONTH"

    def test_last_month(self):
        r = normalize_time("上个月", REF)
        assert r.precision == "MONTH"
        assert r.start_dt.month == 1


class TestRelativeYear:
    def test_this_year(self):
        r = normalize_time("今年", REF)
        assert r.precision == "YEAR"
        assert r.start_dt.year == 2026

    def test_last_year(self):
        r = normalize_time("去年", REF)
        assert r.precision == "YEAR"
        assert r.start_dt.year == 2025


class TestTimePeriod:
    def test_morning(self):
        r = normalize_time("早上", REF)
        assert r.precision == "UNKNOWN"  # time-of-day words not normalized by current implementation

    def test_afternoon(self):
        r = normalize_time("下午", REF)
        assert r.precision == "UNKNOWN"  # time-of-day words not normalized by current implementation


class TestFuzzyTime:
    def test_before(self):
        r = normalize_time("以前", REF)
        assert r.precision == "FUZZY"

    def test_recently(self):
        r = normalize_time("最近", REF)
        assert r.precision == "FUZZY"


class TestUnrecognized:
    def test_non_time(self):
        r = normalize_time("小明", REF)
        assert r.precision == "UNKNOWN"
