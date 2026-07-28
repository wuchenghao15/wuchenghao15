#!/usr/bin/env python3
# pyright: reportMissingImports=false, reportReturnType=false, reportUnboundVariable=false, reportInvalidTypeForm=false, reportUnusedVariable=false, reportGeneralTypeIssues=false
# basedpyright: reportMissingImports=false, reportReturnType=false, reportUnboundVariable=false, reportInvalidTypeForm=false, reportUnusedVariable=false, reportGeneralTypeIssues=false, reportUnknownMemberType=false
"""农历服务：提供公历→农历转换、初一/十五倒计时、前端展示文本。

运行期兼容 Python 3.9+（因此不使用仅 3.10+ 的 typing.TypeAlias）。
预查表覆盖 2021–2027 年区间，实际使用会先排序。
"""

from __future__ import annotations

import datetime as _dt_mod
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 类型别名（全部写为注释以避免 3.9 缺少 TypeAlias）：
#   LunarTripleT  = Tuple[int, int, int]
#   DateOptT      = Optional[_dt_mod.datetime]
#   MonthTableT   = List[Tuple[int, int, int]]
#   StrIntMapT    = Dict[int, str]
#   StrListAliasT = List[str]                      # 原 StrListT
#   CountdownDict = Dict[str, Any]
# ---------------------------------------------------------------------------


class LunarCalendarService:
    """农历日历服务类（基于预查表）。"""

    # 正月 ~ 腊月 的中文名
    CHN_MONTH_NAME: List[str] = [
        "正", "二", "三", "四", "五", "六",
        "七", "八", "九", "十", "冬", "腊",
    ]

    # 农历日的中文数字映射（1 至 10），供日中文拼名使用
    CHN_DAY_DIGIT: Dict[int, str] = {
        1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
        6: "六", 7: "七", 8: "八", 9: "九", 10: "十",
    }

    # 各农历月份初一对应的公历日期（顺序故意打乱，使用时会 sorted）
    # 覆盖年份：2021 2022 2023 2024 2025 2026 2027
    RAW_FIRST_OF_MONTH: List[Tuple[int, int, int]] = [
        (2024, 10, 4), (2024, 11, 2), (2024, 12, 2), (2024, 12, 31),
        (2025, 1, 29), (2025, 3, 2), (2025, 3, 31), (2025, 4, 30),
        (2025, 5, 29), (2025, 6, 28), (2025, 7, 27), (2025, 8, 26),
        (2025, 9, 24), (2025, 10, 24), (2025, 11, 22), (2025, 12, 22),
        (2026, 1, 29), (2026, 3, 1), (2026, 3, 31), (2026, 4, 29),
        (2026, 5, 29), (2026, 6, 16), (2026, 7, 16), (2026, 8, 14),
        (2026, 9, 12), (2026, 10, 12), (2026, 11, 10), (2026, 12, 10),
        (2027, 1, 8), (2027, 2, 7), (2027, 3, 8), (2027, 4, 7),
        (2027, 5, 7), (2027, 6, 5), (2027, 7, 5), (2027, 8, 3),
        (2027, 9, 2), (2027, 10, 1), (2027, 10, 31), (2027, 11, 29),
        (2021, 2, 12), (2021, 3, 14), (2021, 4, 12), (2021, 5, 12),
        (2021, 6, 10), (2021, 7, 10), (2021, 8, 8), (2021, 9, 7),
        (2021, 10, 6), (2021, 11, 5), (2021, 12, 4), (2021, 12, 31),
        (2022, 2, 1), (2022, 3, 3), (2022, 4, 1), (2022, 5, 1),
        (2022, 5, 30), (2022, 6, 29), (2022, 7, 29), (2022, 8, 27),
        (2022, 9, 26), (2022, 10, 25), (2022, 11, 24), (2022, 12, 23),
        (2023, 1, 22), (2023, 2, 20), (2023, 3, 22), (2023, 4, 20),
        (2023, 5, 20), (2023, 6, 18), (2023, 7, 18), (2023, 8, 16),
        (2023, 9, 15), (2023, 10, 14), (2023, 11, 13), (2023, 12, 12),
        (2024, 2, 10), (2024, 3, 11), (2024, 4, 10), (2024, 5, 10),
        (2024, 6, 8), (2024, 7, 7), (2024, 8, 6), (2024, 9, 4),
    ]

    # ==================================================================
    # 初始化
    # ==================================================================
    def __init__(self) -> None:
        # key: YYYYMMDD 字符串； value: (农历年, 农历月, 农历日)
        self._triple_cache: Dict[str, Tuple[int, int, int]] = {}

    # ==================================================================
    # 内部小工具
    # ==================================================================
    @staticmethod
    def _pick_date(value: Optional[_dt_mod.datetime]) -> _dt_mod.datetime:
        """None → 今天；否则直接返回传入值。"""
        return _dt_mod.datetime.now() if value is None else value

    def _sorted_first_timestamps(self) -> List[_dt_mod.datetime]:
        """将 RAW_FIRST_OF_MONTH 表转换为升序 datetime 列表（每次重新计算避免全局可变状态）。"""
        out: List[_dt_mod.datetime] = []
        for (y, m, d) in self.RAW_FIRST_OF_MONTH:
            out.append(_dt_mod.datetime(y, m, d))
        out.sort()
        return out

    # ==================================================================
    # 核心：公历日期 → (农历年, 农历月, 农历日)
    # ==================================================================
    def _calc_lunar_triple(self, maybe_date: Optional[_dt_mod.datetime] = None) -> Tuple[int, int, int]:
        the_date = self._pick_date(maybe_date)
        ckey = the_date.strftime("%Y%m%d")
        if ckey in self._triple_cache:
            cached_tuple = self._triple_cache[ckey]
            return cached_tuple

        target_dt = _dt_mod.datetime(the_date.year, the_date.month, the_date.day)
        sorted_firsts = self._sorted_first_timestamps()
        count = len(sorted_firsts)

        out_year: int = target_dt.year
        out_month: int = 1
        out_day: int = 1

        # 1) 在预查表中找到第一个 >= target 的位置
        hit_idx = -1
        for pos in range(count):
            if sorted_firsts[pos] >= target_dt:
                hit_idx = pos
                break

        if hit_idx >= 0:
            first_day = sorted_firsts[hit_idx]
            if first_day == target_dt:
                out_day = 1
                out_month = (hit_idx % 12) + 1
                out_year = first_day.year
                if out_month == 1 and first_day.month == 12:
                    out_year = first_day.year + 1
            elif hit_idx > 0:
                prev_first = sorted_firsts[hit_idx - 1]
                out_day = (target_dt - prev_first).days + 1
                next_first = sorted_firsts[hit_idx]
                len_month = (next_first - prev_first).days
                if out_day > len_month:
                    out_day = len_month
                out_month = ((hit_idx - 1) % 12) + 1
                out_year = prev_first.year
                if out_month == 1 and prev_first.month == 12:
                    out_year = prev_first.year + 1
        else:
            # 2) target 在所有预查表项之后（使用最后一项兜底）
            if count > 0:
                last_first = sorted_firsts[-1]
                out_day = (target_dt - last_first).days + 1
                out_month = ((count - 1) % 12) + 1
                out_year = last_first.year
                if out_month == 1 and last_first.month == 12:
                    out_year = last_first.year + 1

        final: Tuple[int, int, int] = (out_year, out_month, out_day)
        self._triple_cache[ckey] = final
        return final

    # ==================================================================
    # 农历日数字 → 中文日字符串
    # ==================================================================
    @staticmethod
    def _render_day_string(day: int) -> str:
        if day == 1:
            return "初一"
        if day == 10:
            return "初十"
        if day == 15:
            return "十五"
        if day == 20:
            return "二十"
        if day == 30:
            return "三十"
        if 1 < day < 10:
            return "初" + LunarCalendarService.CHN_DAY_DIGIT[day]
        if 10 < day < 20:
            return "十" + LunarCalendarService.CHN_DAY_DIGIT[day - 10]
        if 20 < day < 30:
            return "廿" + LunarCalendarService.CHN_DAY_DIGIT[day - 20]
        return str(day)

    # ==================================================================
    # 公共 API
    # ==================================================================
    def get_lunar_date_string(self, maybe_date: Optional[_dt_mod.datetime] = None) -> str:
        """返回形如「农历正月十五」的字符串；越界则退化为公历表示。"""
        _, month, day = self._calc_lunar_triple(maybe_date)

        if month < 1 or month > 12:
            d = self._pick_date(maybe_date)
            return "公历%d年%d月%d日" % (d.year, d.month, d.day)

        m_name = self.CHN_MONTH_NAME[month - 1]
        d_name = self._render_day_string(day)
        return "农历%s月%s" % (m_name, d_name)

    def is_first_or_fifteenth(self, maybe_date: Optional[_dt_mod.datetime] = None) -> bool:
        """今天是不是农历初一或十五。"""
        _, _, d = self._calc_lunar_triple(maybe_date)
        return d == 1 or d == 15

    def get_first_or_fifteenth_countdown(
        self, maybe_date: Optional[_dt_mod.datetime] = None
    ) -> Dict[str, Any]:
        """返回 {type, days, is_today} 的倒计时字典。

        所有分支均会显式返回 dict，不产生 None 返回路径。
        """
        today_dt = self._pick_date(maybe_date)
        target_dt = _dt_mod.datetime(today_dt.year, today_dt.month, today_dt.day)
        _, _, d = self._calc_lunar_triple(today_dt)

        # ---- 初一 / 十五当日 ----
        if d == 1:
            return {"type": "初一", "days": 0, "is_today": True}
        if d == 15:
            return {"type": "十五", "days": 0, "is_today": True}

        # ---- 还未到十五 ----
        if d < 15:
            diff = 15 - d
            return {"type": "十五", "days": diff, "is_today": False}

        # ---- 已过十五 → 找下一个初一 ----
        first_days_sorted = self._sorted_first_timestamps()
        n_total = len(first_days_sorted)
        for j in range(n_total):
            candidate_first = first_days_sorted[j]
            if candidate_first <= target_dt:
                continue
            if j > 0:
                gap_days = (candidate_first - target_dt).days
                return {"type": "初一", "days": gap_days, "is_today": False}
            break  # j==0 且 candidate_first 就 > target 的异常场景，跳兜底

        # 兜底：查表找不到（日期超出预查区间）
        if n_total > 0:
            last_entry = first_days_sorted[-1]
            default_len = 30
            if n_total > 1:
                prev_entry = first_days_sorted[-2]
                default_len = (last_entry - prev_entry).days
            fallback_days = default_len - d + 1
            return {"type": "初一", "days": fallback_days, "is_today": False}

        return {"type": "初一", "days": (30 - d + 1), "is_today": False}

    def get_display_text(self, maybe_date: Optional[_dt_mod.datetime] = None) -> str:
        """前端直接展示的一句话。"""
        info = self.get_first_or_fifteenth_countdown(maybe_date)
        is_today_flag = bool(info.get("is_today", False))
        if is_today_flag:
            t = str(info.get("type", "初一"))
            return "今天是农历【%s】" % t
        kind = str(info.get("type", "初一"))
        num = int(info.get("days", 0))
        return "农历%s还有【%d】天" % (kind, num)


# ---------------------------------------------------------------------------
# 全局单例（对外保持模块级导出名不变）
# ---------------------------------------------------------------------------
lunar_calendar_service = LunarCalendarService()
