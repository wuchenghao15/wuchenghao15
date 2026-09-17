#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日出日落时间计算服务
====================
基于 astral 库计算指定坐标和日期的日出日落时间；
若 astral 不可用，降级为固定时间 06:00 / 18:00。

纯 Python 实现，无网络依赖。

使用示例::

    from core.services.sunrise_sunset import calculate_sunrise_sunset, get_city_coordinates
    coords = get_city_coordinates("北京")
    result = calculate_sunrise_sunset(coords["latitude"], coords["longitude"], date.today())
    # -> {"sunrise": "06:23", "sunset": "18:45"}
"""
from __future__ import annotations

import datetime
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# 中国主要城市坐标字典（纬度, 经度）
# 数据来源：国家测绘局公开坐标，精度满足主题切换需求
# ============================================================================
DEFAULT_CITY_COORDINATES: dict[str, dict[str, float]] = {
    "北京": {"latitude": 39.9042, "longitude": 116.4074},
    "上海": {"latitude": 31.2304, "longitude": 121.4737},
    "广州": {"latitude": 23.1291, "longitude": 113.2644},
    "深圳": {"latitude": 22.5431, "longitude": 114.0579},
    "成都": {"latitude": 30.5728, "longitude": 104.0668},
    "武汉": {"latitude": 30.5928, "longitude": 114.3055},
    "西安": {"latitude": 34.3416, "longitude": 108.9398},
    "杭州": {"latitude": 30.2741, "longitude": 120.1551},
    "南京": {"latitude": 32.0603, "longitude": 118.7969},
    "重庆": {"latitude": 29.5630, "longitude": 106.5516},
    "天津": {"latitude": 39.0850, "longitude": 117.2009},
    "苏州": {"latitude": 31.2989, "longitude": 120.5853},
    "长沙": {"latitude": 28.2282, "longitude": 112.9388},
    "郑州": {"latitude": 34.7466, "longitude": 113.6253},
    "青岛": {"latitude": 36.0671, "longitude": 120.3826},
    "沈阳": {"latitude": 41.8057, "longitude": 123.4315},
    "哈尔滨": {"latitude": 45.8038, "longitude": 126.5350},
    "长春": {"latitude": 43.8868, "longitude": 125.3245},
    "大连": {"latitude": 38.9140, "longitude": 121.6147},
    "昆明": {"latitude": 25.0389, "longitude": 102.7183},
    "济南": {"latitude": 36.6512, "longitude": 117.1201},
    "福州": {"latitude": 26.0745, "longitude": 119.2965},
    "厦门": {"latitude": 24.4798, "longitude": 118.0894},
    "合肥": {"latitude": 31.8206, "longitude": 117.2272},
    "南昌": {"latitude": 28.6820, "longitude": 115.8579},
    "石家庄": {"latitude": 38.0428, "longitude": 114.5149},
    "太原": {"latitude": 37.8706, "longitude": 112.5489},
    "兰州": {"latitude": 36.0611, "longitude": 103.8343},
    "银川": {"latitude": 38.4872, "longitude": 106.2309},
    "西宁": {"latitude": 36.6171, "longitude": 101.7782},
    "乌鲁木齐": {"latitude": 43.8256, "longitude": 87.6168},
    "拉萨": {"latitude": 29.6500, "longitude": 91.1000},
    "海口": {"latitude": 20.0440, "longitude": 110.1990},
    "三亚": {"latitude": 18.2528, "longitude": 109.5119},
    "贵阳": {"latitude": 26.6470, "longitude": 106.6302},
    "南宁": {"latitude": 22.8170, "longitude": 108.3669},
    "呼和浩特": {"latitude": 40.8426, "longitude": 111.7511},
}

# 降级默认值（astral 不可用时使用）
_FALLBACK_RESULT = {"sunrise": "06:00", "sunset": "18:00"}

# 中国标准时区（UTC+8），用于 astral 计算
_CHINA_TZ = "Asia/Shanghai"


def get_city_coordinates(city_name: str) -> dict[str, float] | None:
    """根据城市名称获取经纬度坐标。

    支持模糊匹配：自动去除 "市"/"省"/"特别行政区"/"自治区" 等后缀。

    Args:
        city_name: 城市名称，如 "北京"、"上海市"

    Returns:
        包含 latitude 和 longitude 的字典，未找到时返回 None
    """
    if not city_name or not isinstance(city_name, str):
        return None

    name = city_name.strip()
    if not name:
        return None

    # 精确匹配
    if name in DEFAULT_CITY_COORDINATES:
        return DEFAULT_CITY_COORDINATES[name]

    # 去后缀模糊匹配
    suffixes = ["市", "省", "特别行政区", "自治区", "自治州", "地区", "盟"]
    normalized = name
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break

    if normalized in DEFAULT_CITY_COORDINATES:
        return DEFAULT_CITY_COORDINATES[normalized]

    # 反向匹配（用户输入 "北京市"，字典里是 "北京"）
    for key, coords in DEFAULT_CITY_COORDINATES.items():
        if name.startswith(key) or key.startswith(normalized):
            return coords

    return None


def calculate_sunrise_sunset(
    latitude: float,
    longitude: float,
    date: datetime.date | datetime.datetime | None = None,
) -> dict[str, str]:
    """计算指定坐标和日期的日出日落时间。

    使用 astral 库进行精确计算；若 astral 不可用或计算异常，
    降级返回固定时间 06:00 / 18:00。

    Args:
        latitude:  纬度（-90 ~ 90）
        longitude: 经度（-180 ~ 180）
        date:      日期对象（datetime.date 或 datetime.datetime），
                   为 None 时使用当天

    Returns:
        ``{"sunrise": "HH:MM", "sunset": "HH:MM"}``
    """
    # 参数校验
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        logger.debug("[sunrise_sunset] 坐标转换失败: lat=%r lon=%r", latitude, longitude)
        return dict(_FALLBACK_RESULT)

    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        logger.debug("[sunrise_sunset] 坐标超出范围: lat=%s lon=%s", lat, lon)
        return dict(_FALLBACK_RESULT)

    # 日期处理
    if date is None:
        target_date = datetime.date.today()
    elif isinstance(date, datetime.datetime):
        target_date = date.date()
    elif isinstance(date, datetime.date):
        target_date = date
    else:
        logger.debug("[sunrise_sunset] 日期类型无效: %r", type(date))
        return dict(_FALLBACK_RESULT)

    # 尝试使用 astral 库
    try:
        from astral import LocationInfo
        from astral.sun import sun
    except ImportError:
        logger.debug("[sunrise_sunset] astral 库未安装，降级为 06:00/18:00")
        return dict(_FALLBACK_RESULT)
    except Exception as exc:
        logger.debug("[sunrise_sunset] astral 导入异常: %s", exc)
        return dict(_FALLBACK_RESULT)

    try:
        # astral 2.x/3.x LocationInfo 构造方式兼容
        try:
            loc = LocationInfo(
                latitude=lat,
                longitude=lon,
                timezone=_CHINA_TZ,
            )
        except TypeError:
            # 旧版 astral 需要位置参数: name, region, timezone, latitude, longitude
            loc = LocationInfo("custom", "China", _CHINA_TZ, lat, lon)

        # 计算日出日落（带时区）
        s = sun(loc.observer, date=target_date, tzinfo=loc.timezone)

        # astral 2.x 返回 dict，3.x 可能返回 namedtuple
        if isinstance(s, dict):
            sunrise_dt = s.get("sunrise")
            sunset_dt = s.get("sunset")
        else:
            sunrise_dt = getattr(s, "sunrise", None)
            sunset_dt = getattr(s, "sunset", None)

        if sunrise_dt is None or sunset_dt is None:
            return dict(_FALLBACK_RESULT)

        return {
            "sunrise": sunrise_dt.strftime("%H:%M"),
            "sunset": sunset_dt.strftime("%H:%M"),
        }
    except Exception as exc:
        logger.warning("[sunrise_sunset] astral 计算异常，降级为 06:00/18:00: %s", exc)
        return dict(_FALLBACK_RESULT)


# ============================================================================
# 模块级别便捷实例（供直接 import 使用，与 lunar_calendar_service 风格一致）
# ============================================================================

class _SunriseSunsetService:
    """日出日落计算服务单例封装，提供与模块函数一致的接口。"""

    @property
    def cities(self) -> dict[str, dict[str, float]]:
        return DEFAULT_CITY_COORDINATES

    def get_coordinates(self, city_name: str) -> dict[str, float] | None:
        return get_city_coordinates(city_name)

    def calculate(
        self,
        latitude: float,
        longitude: float,
        date: datetime.date | datetime.datetime | None = None,
    ) -> dict[str, str]:
        return calculate_sunrise_sunset(latitude, longitude, date)


sunrise_sunset_service = _SunriseSunsetService()
