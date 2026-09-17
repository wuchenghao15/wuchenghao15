"""
Time Normalization Module

Core Features:
1. Convert relative time expressions (e.g. "yesterday", "last year") to absolute time ranges
2. Does not modify original text, only produces structured TimeSpan

Design Principles:
- Rules must be deterministic to avoid "reference frame drift"
- Fuzzy time (e.g. "recently") outputs FUZZY precision for soft weighting, not hard filtering
"""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Tuple
import re


@dataclass
class TimeSpan:
    """Time span"""

    source_text: str  # original time expression
    start_dt: Optional[datetime] = None  # start time
    end_dt: Optional[datetime] = None  # end time
    precision: str = "UNKNOWN"  # precision: HOUR, DAY, WEEK, MONTH, YEAR, FUZZY, UNKNOWN
    start: int = -1  # start position in source text
    end: int = -1  # end position in source text


class TimeNormalizer:
    """Time normalizer"""

    # === Day-relative time ===
    DAY_RELATIVE = {
        "今天": 0,
        "今日": 0,
        "昨天": -1,
        "昨日": -1,
        "前天": -2,
        "前日": -2,
        "大前天": -3,
        "明天": 1,
        "明日": 1,
        "后天": 2,
        "后日": 2,
        "大后天": 3,
    }

    # === Week-relative time ===
    WEEK_RELATIVE = {
        "这周": 0,
        "本周": 0,
        "这个星期": 0,
        "上周": -1,
        "上个星期": -1,
        "上上周": -2,
        "下周": 1,
        "下个星期": 1,
        "下下周": 2,
    }

    # === Month-relative time ===
    MONTH_RELATIVE = {
        "这个月": 0,
        "本月": 0,
        "当月": 0,
        "上个月": -1,
        "下个月": 1,
    }

    # === Year-relative time ===
    YEAR_RELATIVE = {
        "今年": 0,
        "去年": -1,
        "前年": -2,
        "明年": 1,
        "后年": 2,
    }

    # === Day of week ===
    WEEKDAY_MAP = {
        "周一": 0,
        "星期一": 0,
        "周二": 1,
        "星期二": 1,
        "周三": 2,
        "星期三": 2,
        "周四": 3,
        "星期四": 3,
        "周五": 4,
        "星期五": 4,
        "周六": 5,
        "星期六": 5,
        "周日": 6,
        "星期日": 6,
        "星期天": 6,
        "周末": 5,  # weekend defaults to Saturday
    }

    # === Time periods ===
    TIME_PERIOD = {
        "早上": (6, 9),
        "上午": (9, 12),
        "中午": (11, 13),
        "下午": (13, 18),
        "傍晚": (17, 19),
        "晚上": (19, 23),
        "深夜": (23, 3),
        "凌晨": (0, 6),
        "半夜": (0, 3),
        "早晨": (5, 8),
        "清晨": (5, 7),
        "黄昏": (17, 19),
    }

    # === Seasons ===
    SEASON_MAP = {
        "春天": (3, 5),
        "春季": (3, 5),
        "夏天": (6, 8),
        "夏季": (6, 8),
        "秋天": (9, 11),
        "秋季": (9, 11),
        "冬天": (12, 2),
        "冬季": (12, 2),
    }

    # === Holidays (approximate dates) ===
    HOLIDAY_MAP = {
        "元旦": (1, 1),
        "元旦节": (1, 1),
        "春节": (1, 28),  # lunar calendar, approximate Gregorian
        "过年": (1, 28),
        "元宵节": (2, 15),  # lunar 1st month 15th, approximate
        "清明": (4, 5),
        "清明节": (4, 5),
        "五一": (5, 1),
        "五一节": (5, 1),
        "劳动节": (5, 1),
        "端午": (6, 10),
        "端午节": (6, 10),  # lunar 5th month 5th, approximate
        "七夕": (8, 14),
        "七夕节": (8, 14),  # lunar 7th month 7th, approximate
        "中秋": (9, 21),
        "中秋节": (9, 21),  # lunar 8th month 15th, approximate
        "国庆": (10, 1),
        "国庆节": (10, 1),
        "十一": (10, 1),
        "重阳": (10, 25),
        "重阳节": (10, 25),  # lunar 9th month 9th, approximate
        "圣诞": (12, 25),
        "圣诞节": (12, 25),
        "平安夜": (12, 24),
        "除夕": (1, 27),  # lunar New Year's Eve, approximate
        "大年三十": (1, 27),
        "大年初一": (1, 28),
    }

    # === Fuzzy time ===
    FUZZY_TIME = {
        "以前",
        "之前",
        "从前",
        "过去",
        "曾经",
        "以后",
        "之后",
        "将来",
        "未来",
        "日后",
        "现在",
        "目前",
        "当前",
        "此刻",
        "眼下",
        "如今",
        "刚才",
        "刚刚",
        "方才",
        "适才",
        "最近",
        "近来",
        "近期",
        "近日",
        "这段时间",
        "那段时间",
    }

    def normalize(
        self, time_text: str, reference: datetime = None, text_start: int = -1, text_end: int = -1
    ) -> TimeSpan:
        """Normalize a time expression

        Args:
            time_text: time text
            reference: reference time (defaults to current time)
            text_start: start position in source text
            text_end: end position in source text

        Returns:
            TimeSpan: normalization result
        """
        if reference is None:
            reference = datetime.now()

        # Try various normalization rules
        result = (
            self._normalize_day_relative(time_text, reference)
            or self._normalize_week_relative(time_text, reference)
            or self._normalize_month_relative(time_text, reference)
            or self._normalize_year_relative(time_text, reference)
            or self._normalize_weekday(time_text, reference)
            or self._normalize_season(time_text, reference)
            or self._normalize_holiday(time_text, reference)
            or self._normalize_fuzzy(time_text, reference)
            or self._normalize_explicit_date(time_text, reference)
        )

        if result:
            result.source_text = time_text
            result.start = text_start
            result.end = text_end
            return result

        # Cannot normalize
        return TimeSpan(source_text=time_text, precision="UNKNOWN", start=text_start, end=text_end)

    def _normalize_day_relative(self, text: str, ref: datetime) -> Optional[TimeSpan]:
        """Normalize day-relative time (yesterday, today, tomorrow, etc.)"""
        if text in self.DAY_RELATIVE:
            delta = self.DAY_RELATIVE[text]
            target = ref.date() + timedelta(days=delta)
            return TimeSpan(
                source_text=text,
                start_dt=datetime.combine(target, datetime.min.time()),
                end_dt=datetime.combine(target + timedelta(days=1), datetime.min.time()),
                precision="DAY",
            )
        return None

    def _normalize_week_relative(self, text: str, ref: datetime) -> Optional[TimeSpan]:
        """Normalize week-relative time (last week, this week, next week, etc.)"""
        if text in self.WEEK_RELATIVE:
            delta = self.WEEK_RELATIVE[text]
            # Calculate target week's Monday
            current_monday = ref.date() - timedelta(days=ref.weekday())
            target_monday = current_monday + timedelta(weeks=delta)
            next_monday = target_monday + timedelta(weeks=1)
            return TimeSpan(
                source_text=text,
                start_dt=datetime.combine(target_monday, datetime.min.time()),
                end_dt=datetime.combine(next_monday, datetime.min.time()),
                precision="WEEK",
            )
        return None

    def _normalize_month_relative(self, text: str, ref: datetime) -> Optional[TimeSpan]:
        """Normalize month-relative time (last month, this month, next month, etc.)"""
        if text in self.MONTH_RELATIVE:
            delta = self.MONTH_RELATIVE[text]
            year = ref.year
            month = ref.month + delta

            # Handle year overflow
            while month < 1:
                month += 12
                year -= 1
            while month > 12:
                month -= 12
                year += 1

            start_dt = datetime(year, month, 1)

            # Calculate next month
            next_month = month + 1
            next_year = year
            if next_month > 12:
                next_month = 1
                next_year += 1
            end_dt = datetime(next_year, next_month, 1)

            return TimeSpan(source_text=text, start_dt=start_dt, end_dt=end_dt, precision="MONTH")
        return None

    def _normalize_year_relative(self, text: str, ref: datetime) -> Optional[TimeSpan]:
        """Normalize year-relative time (last year, this year, next year, etc.)"""
        if text in self.YEAR_RELATIVE:
            delta = self.YEAR_RELATIVE[text]
            target_year = ref.year + delta
            return TimeSpan(
                source_text=text,
                start_dt=datetime(target_year, 1, 1),
                end_dt=datetime(target_year + 1, 1, 1),
                precision="YEAR",
            )
        return None

    def _normalize_weekday(self, text: str, ref: datetime) -> Optional[TimeSpan]:
        """Normalize day of week"""
        if text in self.WEEKDAY_MAP:
            target_weekday = self.WEEKDAY_MAP[text]
            current_weekday = ref.weekday()

            # Calculate the nearest occurrence of this weekday (could be past or future)
            delta = target_weekday - current_weekday
            if delta > 0:
                delta -= 7  # default to past occurrence

            target = ref.date() + timedelta(days=delta)
            return TimeSpan(
                source_text=text,
                start_dt=datetime.combine(target, datetime.min.time()),
                end_dt=datetime.combine(target + timedelta(days=1), datetime.min.time()),
                precision="DAY",
            )
        return None

    def _normalize_season(self, text: str, ref: datetime) -> Optional[TimeSpan]:
        """Normalize season"""
        if text in self.SEASON_MAP:
            start_month, end_month = self.SEASON_MAP[text]
            year = ref.year

            # Handle winter crossing year boundary
            if start_month > end_month:  # winter 12-2
                if ref.month < 6:
                    # Currently first half of year: winter = last Dec to this Feb
                    start_dt = datetime(year - 1, start_month, 1)
                    end_dt = datetime(year, end_month + 1, 1)
                else:
                    # Currently second half of year: winter = this Dec to next Feb
                    start_dt = datetime(year, start_month, 1)
                    end_dt = datetime(year + 1, end_month + 1, 1)
            else:
                start_dt = datetime(year, start_month, 1)
                end_dt = datetime(year, end_month + 1, 1)

            return TimeSpan(source_text=text, start_dt=start_dt, end_dt=end_dt, precision="MONTH")
        return None

    def _normalize_holiday(self, text: str, ref: datetime) -> Optional[TimeSpan]:
        """Normalize holiday"""
        if text in self.HOLIDAY_MAP:
            month, day = self.HOLIDAY_MAP[text]
            year = ref.year

            # If holiday has passed, may refer to this year or last year
            holiday_date = datetime(year, month, day)
            if holiday_date > ref:
                # Holiday hasn't occurred yet, use this year's
                pass
            else:
                # Holiday has passed, but default to this year's (more contextually relevant)
                pass

            return TimeSpan(
                source_text=text, start_dt=holiday_date, end_dt=holiday_date + timedelta(days=1), precision="DAY"
            )
        return None

    def _normalize_fuzzy(self, text: str, ref: datetime) -> Optional[TimeSpan]:
        """Normalize fuzzy time"""
        if text in self.FUZZY_TIME:
            # Fuzzy time outputs a range for soft weighting
            if text in {"最近", "近来", "近期", "近日", "这段时间"}:
                # Last 30 days
                return TimeSpan(source_text=text, start_dt=ref - timedelta(days=30), end_dt=ref, precision="FUZZY")
            elif text in {"以前", "之前", "从前", "过去", "曾经", "那段时间"}:
                # Some time in the past, no specific range
                return TimeSpan(source_text=text, end_dt=ref, precision="FUZZY")
            elif text in {"以后", "之后", "将来", "未来", "日后"}:
                # Some time in the future
                return TimeSpan(source_text=text, start_dt=ref, precision="FUZZY")
            elif text in {"现在", "目前", "当前", "此刻", "眼下", "如今"}:
                # Current moment
                return TimeSpan(source_text=text, start_dt=ref, end_dt=ref + timedelta(hours=1), precision="HOUR")
            elif text in {"刚才", "刚刚", "方才", "适才"}:
                # Just now (past few minutes to 1 hour)
                return TimeSpan(source_text=text, start_dt=ref - timedelta(hours=1), end_dt=ref, precision="HOUR")
        return None

    def _normalize_explicit_date(self, text: str, ref: datetime) -> Optional[TimeSpan]:
        """Normalize explicit date formats

        Supported formats:
        - 2024-01-15, 2024/01/15
        - 1月15日 (Chinese month-day)
        - 1月 (Chinese month only)
        """
        # ISO format: 2024-01-15 or 2024/01/15
        iso_match = re.match(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
        if iso_match:
            year, month, day = map(int, iso_match.groups())
            try:
                target = datetime(year, month, day)
                return TimeSpan(source_text=text, start_dt=target, end_dt=target + timedelta(days=1), precision="DAY")
            except ValueError:
                pass

        # Chinese date: X月X日
        cn_date_match = re.match(r"(\d{1,2})月(\d{1,2})日?", text)
        if cn_date_match:
            month, day = map(int, cn_date_match.groups())
            year = ref.year
            try:
                target = datetime(year, month, day)
                return TimeSpan(source_text=text, start_dt=target, end_dt=target + timedelta(days=1), precision="DAY")
            except ValueError:
                pass

        # Month only: X月
        month_match = re.match(r"(\d{1,2})月$", text)
        if month_match:
            month = int(month_match.group(1))
            year = ref.year
            if 1 <= month <= 12:
                start_dt = datetime(year, month, 1)
                next_month = month + 1
                next_year = year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                end_dt = datetime(next_year, next_month, 1)
                return TimeSpan(source_text=text, start_dt=start_dt, end_dt=end_dt, precision="MONTH")

        return None


# === Convenience Functions ===

_normalizer = None


def normalize_time(time_text: str, reference: datetime = None) -> TimeSpan:
    """Quick time normalization"""
    global _normalizer
    if _normalizer is None:
        _normalizer = TimeNormalizer()
    return _normalizer.normalize(time_text, reference)


# === Test ===

if __name__ == "__main__":
    print("=" * 70)
    print("Time Normalization Test")
    print("=" * 70)

    normalizer = TimeNormalizer()
    ref = datetime(2026, 1, 12, 10, 30)  # reference time

    tests = [
        # day-relative
        "今天",
        "昨天",
        "前天",
        "明天",
        "后天",
        # week-relative
        "这周",
        "上周",
        "下周",
        # month-relative
        "这个月",
        "上个月",
        "下个月",
        # year-relative
        "今年",
        "去年",
        "明年",
        # day of week
        "周一",
        "周五",
        "周末",
        # seasons
        "春天",
        "夏天",
        "秋天",
        "冬天",
        # holidays
        "春节",
        "国庆节",
        "圣诞节",
        "中秋节",
        # fuzzy
        "最近",
        "以前",
        "将来",
        "刚才",
        "现在",
        # explicit
        "2024-01-15",
        "1月15日",
        "3月",
    ]

    print(f"Reference time: {ref}")
    print()

    for text in tests:
        result = normalizer.normalize(text, ref)
        if result.start_dt:
            start_str = result.start_dt.strftime("%Y-%m-%d %H:%M")
        else:
            start_str = "None"
        if result.end_dt:
            end_str = result.end_dt.strftime("%Y-%m-%d %H:%M")
        else:
            end_str = "None"
        print(f"  {text:12} -> [{start_str}, {end_str}) precision={result.precision}")
