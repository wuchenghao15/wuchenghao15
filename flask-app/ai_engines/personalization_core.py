#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 个性化引擎 (PersonalizationCore)
========================================
用户个性化4子模块：
  1. UI主题个性化 (主题色/字体/密度/暗黑/毛玻璃/圆角)
  2. 首页/菜单个性化 (模块顺序/快捷入口/收藏页面/常用排序)
  3. 数据交互偏好 (默认过滤/每页条数/排序规则/时间范围/通知频率)
  4. AI员工形象定制 (每AI员工 名称/头像/性格权重/工作节奏/输出风格)

遵循：
  - SSOT 数据库权威源 + 云端优先同步(CloudSyncLayer联动)
  - 超级管理员wuchenghao15配置全局IRON_RULE级，不可覆盖
  - KV存储：profile_key -> {version, value, updated_at, device}
  - 配置分级：global_default > role_default > user_personal (后优先级高)

版本: v1.1.0  (新增: 12套预设主题方案库 + CSS变量自动生成 + 配色应用)
"""

import os
import sys
import json
import time
import re
import hashlib
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('personalization_core')


# ============================================================================
# 枚举定义
# ============================================================================

class ProfileCategory(Enum):
    """个性化配置分类"""
    UI_THEME = "ui_theme"                  # UI主题
    HOME_MENU = "home_menu"                # 首页/菜单
    DATA_INTERACTION = "data_interaction"  # 数据交互偏好
    AI_EMPLOYEE_STYLE = "ai_employee"      # AI员工形象定制


class ProfileLevel(Enum):
    """配置优先级（数值越大优先级越高）"""
    GLOBAL_DEFAULT = 1   # 系统全局默认
    ROLE_DEFAULT = 2     # 角色默认
    USER_PERSONAL = 3    # 用户个人（最高）


# 超级管理员wuchenghao15的IRON_RULE级配置（不可被角色/用户覆盖）
_IRON_RULE_SUPER_ADMIN_KEYS = {"_iron_rule_level"}

_SUPER_ADMIN_UN = "wuchenghao15"


# ============================================================================
# 默认配置模板
# ============================================================================

DEFAULT_UI_THEME = {
    "theme_color": "#6366f1",
    "font_family": "system",
    "ui_density": "comfortable",   # compact/comfortable/relaxed
    "dark_mode": "auto",            # light/dark/auto
    "blur_level": 0.6,              # 毛玻璃 0~1
    "radius_level": "medium",       # small/medium/large
    "accent_color": "#06b6d4",
    "font_size": "14px",
    "animation_enabled": True,
}

DEFAULT_HOME_MENU = {
    "modules_order": ["dashboard", "ai_employees", "maintenance", "rules", "settings"],
    "shortcuts": ["/dashboard", "/ai-employees", "/maintenance", "/proposals"],
    "favorites": [],
    "recent_items": [],
    "frequent_sort": {"type": "click_count", "asc": False},
    "widget_order": ["system_health", "ai_status", "maintenance", "alerts"],
}

DEFAULT_DATA_INTERACTION = {
    "default_filters": {},
    "page_size": 20,
    "max_page_size": 100,
    "default_sort": {"field": "updated_at", "asc": False},
    "time_range": "7d",             # 1d/7d/30d/90d/all
    "notification_frequency": "realtime",  # realtime/hourly/daily/off
    "table_density": "comfortable",
    "auto_refresh": False,
    "refresh_interval": 30,
    "confirm_before_delete": True,
}

DEFAULT_AI_EMPLOYEE_STYLE = {
    # per-employee customization
    # { employee_id: {name, avatar, personality_weights, work_rhythm, output_style} }
}

DEFAULTS = {
    ProfileCategory.UI_THEME: DEFAULT_UI_THEME,
    ProfileCategory.HOME_MENU: DEFAULT_HOME_MENU,
    ProfileCategory.DATA_INTERACTION: DEFAULT_DATA_INTERACTION,
    ProfileCategory.AI_EMPLOYEE_STYLE: DEFAULT_AI_EMPLOYEE_STYLE,
}


# ============================================================================
# 个性化引擎主类
# ============================================================================

class PersonalizationCore:
    """MTSCOS 用户个性化引擎"""

    CORE_VERSION = "v1.1.0"
    # Super admin global overrides (IRON_RULE level — never overwritten)
    _SA_GLOBAL_OVERRIDE = {
        "ui_theme.dark_mode": "auto",   # 固定auto，管理员也不能改
        "data_interaction.confirm_before_delete": True,
    }

    def __init__(self, db_path: str = None, dual_db=None,
                 cloud_sync_layer=None, project_dir: str = None):
        self.db_path = db_path
        self.dual_db = dual_db
        self.cloud_sync = cloud_sync_layer   # 可选联动云端
        self.project_dir = project_dir or os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))

        # 内存缓存 (username/category -> {value, version, updated_at})
        self._cache: Dict[str, Dict] = {}

        self.stats = {
            'total_gets': 0,
            'total_sets': 0,
            'total_deletes': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'sync_pushes': 0,
            'sync_pulls': 0,
            'last_sync': None,
        }

        self._ensure_tables()
        logger.info(f"PersonalizationCore {self.CORE_VERSION} 已初始化")

    # ======================================================================
    # 核心API：get/set/delete
    # ======================================================================

    def get_profile(self, username: str, category: ProfileCategory,
                    role: str = "user") -> Dict[str, Any]:
        """
        获取用户个性化配置（3级合并：全局默认>角色默认>用户个人）
        超级管理员wuchenghao15 会附加 IRON_RULE 覆盖
        """
        self.stats['total_gets'] += 1
        cat = category if isinstance(category, ProfileCategory) else ProfileCategory(category)
        cache_key = f"{username}::{cat.value}"

        # 1) 用户个人层
        user_val = self._load_user_profile(username, cat)
        if user_val is None:
            self.stats['cache_misses'] += 1
        else:
            self.stats['cache_hits'] += 1

        # 2) 角色层
        role_val = self._load_role_profile(role, cat)

        # 3) 全局默认层
        global_val = self._load_global_profile(cat)

        # 合并（数值越大优先级越高）：user > role > global_default
        merged = {}
        merged.update(DEFAULTS.get(cat, {}))        # 基础默认（代码层）
        merged.update(global_val or {})              # 全局默认（DB层）
        merged.update(role_val or {})                # 角色默认
        merged.update(user_val or {})                # 用户个人

        # 4) 超级管理员 IRON_RULE 覆盖（不可被任何层覆盖）
        if username == _SUPER_ADMIN_UN:
            # wuchenghao15的配置同时作为全局IRON_RULE覆盖下发
            for k, v in self._SA_GLOBAL_OVERRIDE.items():
                parts = k.split('.', 1)
                if parts[0] == cat.value and len(parts) == 2:
                    merged[parts[1]] = v

        # 5) 云端优先：如果有云同步层，以云端为准（LWW合并）
        if self.cloud_sync:
            try:
                cloud_val = self.cloud_sync.pull_user_personalization(username, cat.value)
                if cloud_val is not None:
                    merged = self._lww_merge(merged, cloud_val)
                    self.stats['sync_pulls'] += 1
                    self.stats['last_sync'] = datetime.now().isoformat()
            except Exception as e:
                logger.warning(f"云端个性化拉取失败，用本地: {e}")

        return merged

    def set_profile(self, username: str, category: ProfileCategory,
                    value: Dict[str, Any], role: str = "user",
                    level: ProfileLevel = ProfileLevel.USER_PERSONAL,
                    device: str = "unknown") -> Dict[str, Any]:
        """
        保存个性化配置。云端优先：写入本地同时推送云端（若配置）

        level:
            USER_PERSONAL → 存 per-user
            ROLE_DEFAULT → 存 per-role (需管理员)
            GLOBAL_DEFAULT → 存 global (需超级管理员)
        """
        self.stats['total_sets'] += 1
        cat = category if isinstance(category, ProfileCategory) else ProfileCategory(category)

        # 权限校验：ROLE/GLOBAL不能由普通用户改
        if level != ProfileLevel.USER_PERSONAL and username != _SUPER_ADMIN_UN:
            return {'success': False, 'error': '无权修改角色/全局默认配置'}

        # 超管全局IRON_RULE键 不可被用户层覆盖
        if username != _SUPER_ADMIN_UN or level == ProfileLevel.USER_PERSONAL:
            for k in self._SA_GLOBAL_OVERRIDE:
                parts = k.split('.', 1)
                if parts[0] == cat.value and len(parts) == 2 and parts[1] in value:
                    del value[parts[1]]  # 剥离被覆盖键

        version = int(time.time() * 1000)
        updated_at = datetime.now().isoformat()

        # 存储
        ok = self._save_profile(username=username if level == ProfileLevel.USER_PERSONAL else None,
                                role=role if level == ProfileLevel.ROLE_DEFAULT else None,
                                is_global=level == ProfileLevel.GLOBAL_DEFAULT,
                                category=cat, value=value, version=version,
                                updated_at=updated_at, device=device)
        if not ok:
            return {'success': False, 'error': 'DB写入失败'}

        # 缓存失效
        if level == ProfileLevel.USER_PERSONAL:
            self._cache.pop(f"{username}::{cat.value}", None)
        else:
            self._cache.clear()  # role/global 清全缓存

        # 云端推送
        if self.cloud_sync and level == ProfileLevel.USER_PERSONAL:
            try:
                self.cloud_sync.push_user_personalization(
                    username, cat.value, value, version, updated_at, device)
                self.stats['sync_pushes'] += 1
                self.stats['last_sync'] = updated_at
            except Exception as e:
                logger.warning(f"云端推送失败(本地已保存): {e}")

        return {'success': True, 'category': cat.value,
                'version': version, 'updated_at': updated_at}

    def delete_profile(self, username: str, category: ProfileCategory,
                       level: ProfileLevel = ProfileLevel.USER_PERSONAL,
                       role: str = "user") -> Dict[str, Any]:
        """删除个性化配置（恢复继承上级默认）"""
        self.stats['total_deletes'] += 1
        cat = category if isinstance(category, ProfileCategory) else ProfileCategory(category)
        if level == ProfileLevel.GLOBAL_DEFAULT and username != _SUPER_ADMIN_UN:
            return {'success': False, 'error': '无权删除全局默认'}
        if level == ProfileLevel.ROLE_DEFAULT and username != _SUPER_ADMIN_UN:
            return {'success': False, 'error': '无权删除角色默认'}

        ok = self._delete_profile(username if level == ProfileLevel.USER_PERSONAL else None,
                                  role if level == ProfileLevel.ROLE_DEFAULT else None,
                                  level == ProfileLevel.GLOBAL_DEFAULT, cat)
        self._cache.clear()
        return {'success': ok}

    # ======================================================================
    # AI员工形象定制（第4子模块，专用API）
    # ======================================================================

    def get_ai_employee_style(self, username: str, employee_id: str) -> Dict[str, Any]:
        """获取某用户对某AI员工的个性化定制（merge默认值）"""
        base = self.get_profile(username, ProfileCategory.AI_EMPLOYEE_STYLE)
        per_emp = base.get(employee_id, {}) if isinstance(base, dict) else {}
        # 默认值兜底
        default_style = {
            "display_name": employee_id,
            "avatar_emoji": "🤖",
            "personality_weights": {"理性": 0.5, "感性": 0.5, "严谨": 0.7, "创新": 0.5},
            "work_rhythm": "steady",  # fast/steady/leisure
            "output_style": "professional",  # concise/professional/friendly/casual
            "response_temperature": 0.7,
        }
        default_style.update(per_emp)
        return default_style

    def set_ai_employee_style(self, username: str, employee_id: str,
                              style: Dict[str, Any],
                              device: str = "unknown") -> Dict[str, Any]:
        """保存某AI员工定制"""
        cat = ProfileCategory.AI_EMPLOYEE_STYLE
        current = self.get_profile(username, cat)
        # 只修改对应employee_id键，保留其他员工
        merged = dict(current) if isinstance(current, dict) else {}
        # 过滤掉默认代码层混入的空值：只保留真正存过的员工
        clean = {k: v for k, v in merged.items() if isinstance(v, dict)}
        clean[employee_id] = style
        return self.set_profile(username, cat, clean, device=device)

    # ======================================================================
    # 批量/统计API
    # ======================================================================

    def get_all_for_user(self, username: str, role: str = "user") -> Dict[str, Any]:
        """获取某用户4大类全量配置"""
        result = {}
        for cat in ProfileCategory:
            result[cat.value] = self.get_profile(username, cat, role)
        result['_stats'] = {
            'version': self.CORE_VERSION,
            'generated_at': datetime.now().isoformat(),
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
        }
        return result

    def get_status(self) -> Dict[str, Any]:
        return {
            'version': self.CORE_VERSION,
            'categories': [c.value for c in ProfileCategory],
            'levels': [l.value for l in ProfileLevel],
            'super_admin_override_keys': list(self._SA_GLOBAL_OVERRIDE.keys()),
            'stats': self.stats,
            'cloud_sync_available': self.cloud_sync is not None,
            'timestamp': datetime.now().isoformat(),
        }

    # ======================================================================
    # DB持久化（私有方法）
    # ======================================================================

    def _conn(self):
        if self.dual_db:
            return self.dual_db.get_connection()
        return sqlite3.connect(self.db_path or ':memory:', timeout=10)

    def _write(self, sql, params):
        if self.dual_db:
            return self.dual_db.execute_write(sql, params)
        try:
            conn = self._conn()
            conn.execute(sql, params)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"_write failed: {e}")
            return False

    def _query(self, sql, params):
        if self.dual_db:
            return self.dual_db.execute_query(sql, params)
        try:
            conn = self._conn()
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"_query failed: {e}")
            return []

    def _ensure_tables(self):
        tables = [
            """CREATE TABLE IF NOT EXISTS mt_personalization_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                role TEXT,
                is_global INTEGER DEFAULT 0,
                category TEXT NOT NULL,
                value_json TEXT NOT NULL,
                version INTEGER,
                updated_at TEXT,
                device TEXT,
                UNIQUE(username, category) ON CONFLICT REPLACE,
                UNIQUE(role, category, is_global) ON CONFLICT REPLACE
            )""",
            """CREATE TABLE IF NOT EXISTS mt_personalization_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                category TEXT,
                old_json TEXT,
                new_json TEXT,
                changed_by TEXT,
                changed_at TEXT,
                device TEXT
            )""",
        ]
        for sql in tables:
            self._write(sql, ())

    def _load_user_profile(self, username: str, cat: ProfileCategory) -> Optional[Dict]:
        rows = self._query(
            "SELECT value_json, version, updated_at FROM mt_personalization_profiles "
            "WHERE username = ? AND category = ? LIMIT 1",
            (username, cat.value))
        if rows:
            try:
                return json.loads(rows[0]['value_json'])
            except Exception:
                return None
        return None

    def _load_role_profile(self, role: str, cat: ProfileCategory) -> Optional[Dict]:
        if not role:
            return None
        rows = self._query(
            "SELECT value_json FROM mt_personalization_profiles "
            "WHERE role = ? AND category = ? AND is_global = 0 LIMIT 1",
            (role, cat.value))
        if rows:
            try:
                return json.loads(rows[0]['value_json'])
            except Exception:
                return None
        return None

    def _load_global_profile(self, cat: ProfileCategory) -> Optional[Dict]:
        rows = self._query(
            "SELECT value_json FROM mt_personalization_profiles "
            "WHERE is_global = 1 AND category = ? LIMIT 1",
            (cat.value,))
        if rows:
            try:
                return json.loads(rows[0]['value_json'])
            except Exception:
                return None
        return None

    def _save_profile(self, username: Optional[str], role: Optional[str],
                      is_global: bool, category: ProfileCategory,
                      value: Dict, version: int, updated_at: str,
                      device: str) -> bool:
        # 先做历史记录
        old_rows = self._query(
            "SELECT value_json FROM mt_personalization_profiles WHERE "
            + (f"username = ? " if username else (f"role = ? AND is_global = 0 " if role else "is_global = 1 "))
            + "AND category = ?",
            (username or role or 1, category.value) if not is_global
            else (category.value,))
        old_json = old_rows[0]['value_json'] if old_rows else '{}'

        self._write(
            "INSERT INTO mt_personalization_history "
            "(username, category, old_json, new_json, changed_by, changed_at, device) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username or role or ('GLOBAL' if is_global else None),
             category.value, old_json, json.dumps(value, ensure_ascii=False),
             username or 'system', updated_at, device))

        sql = (
            "INSERT INTO mt_personalization_profiles "
            "(username, role, is_global, category, value_json, version, updated_at, device) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        )
        params = (
            username, role, 1 if is_global else 0,
            category.value, json.dumps(value, ensure_ascii=False),
            version, updated_at, device)
        return self._write(sql, params)

    def _delete_profile(self, username, role, is_global, category) -> bool:
        if username:
            return self._write(
                "DELETE FROM mt_personalization_profiles WHERE username = ? AND category = ?",
                (username, category.value))
        if role:
            return self._write(
                "DELETE FROM mt_personalization_profiles WHERE role = ? AND category = ?",
                (role, category.value))
        if is_global:
            return self._write(
                "DELETE FROM mt_personalization_profiles WHERE is_global = 1 AND category = ?",
                (category.value,))
        return False

    # ======================================================================
    # 工具：LWW合并（Last Writer Wins）
    # ======================================================================

    @staticmethod
    def _lww_merge(local: Dict, cloud: Dict) -> Dict:
        """简单LWW合并：dict值取cloud（云端优先），其余字段保留"""
        merged = dict(local)
        for k, v in (cloud or {}).items():
            merged[k] = v
        return merged


# ============================================================================
# 预设主题方案库 + CSS变量生成 + 配色应用（v1.1.0 扩展）
# ============================================================================

PRESET_THEMES: Dict[str, Dict[str, Any]] = {
    "deep_blue": {
        "name": "深邃蓝", "icon": "🌌",
        "theme_color": "#4f46e5", "accent_color": "#06b6d4",
        "bg_page": "linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)",
        "bg_sidebar": "rgba(15, 23, 42, 0.85)", "bg_card": "rgba(15, 23, 42, 0.7)",
        "dark_mode": "dark", "font_family": "system", "ui_density": "comfortable",
        "blur_level": 0.6, "radius_level": "medium", "font_size": "14px",
        "animation_enabled": True,
    },
    "ocean_cyan": {
        "name": "海洋青", "icon": "🌊",
        "theme_color": "#0ea5e9", "accent_color": "#22d3ee",
        "bg_page": "linear-gradient(135deg, #0c4a6e 0%, #164e63 100%)",
        "bg_sidebar": "rgba(12, 74, 110, 0.85)", "bg_card": "rgba(8, 47, 73, 0.7)",
        "dark_mode": "dark", "font_family": "system", "ui_density": "comfortable",
        "blur_level": 0.7, "radius_level": "medium", "font_size": "14px",
        "animation_enabled": True,
    },
    "emerald_forest": {
        "name": "翡翠林", "icon": "🌲",
        "theme_color": "#10b981", "accent_color": "#84cc16",
        "bg_page": "linear-gradient(135deg, #064e3b 0%, #065f46 100%)",
        "bg_sidebar": "rgba(6, 78, 59, 0.85)", "bg_card": "rgba(4, 47, 46, 0.7)",
        "dark_mode": "dark", "font_family": "system", "ui_density": "comfortable",
        "blur_level": 0.5, "radius_level": "medium", "font_size": "14px",
        "animation_enabled": True,
    },
    "sunset_orange": {
        "name": "日落橙", "icon": "🌅",
        "theme_color": "#f97316", "accent_color": "#fbbf24",
        "bg_page": "linear-gradient(135deg, #431407 0%, #7c2d12 100%)",
        "bg_sidebar": "rgba(67, 20, 7, 0.85)", "bg_card": "rgba(67, 20, 7, 0.7)",
        "dark_mode": "dark", "font_family": "system", "ui_density": "comfortable",
        "blur_level": 0.6, "radius_level": "medium", "font_size": "14px",
        "animation_enabled": True,
    },
    "rose_pink": {
        "name": "玫瑰粉", "icon": "🌸",
        "theme_color": "#e11d48", "accent_color": "#f43f5e",
        "bg_page": "linear-gradient(135deg, #4c0519 0%, #881337 100%)",
        "bg_sidebar": "rgba(76, 5, 25, 0.85)", "bg_card": "rgba(76, 5, 25, 0.7)",
        "dark_mode": "dark", "font_family": "system", "ui_density": "comfortable",
        "blur_level": 0.6, "radius_level": "large", "font_size": "14px",
        "animation_enabled": True,
    },
    "royal_purple": {
        "name": "皇家紫", "icon": "👑",
        "theme_color": "#7c3aed", "accent_color": "#a855f7",
        "bg_page": "linear-gradient(135deg, #2e1065 0%, #4c1d95 100%)",
        "bg_sidebar": "rgba(46, 16, 101, 0.85)", "bg_card": "rgba(46, 16, 101, 0.7)",
        "dark_mode": "dark", "font_family": "system", "ui_density": "comfortable",
        "blur_level": 0.65, "radius_level": "medium", "font_size": "14px",
        "animation_enabled": True,
    },
    "midnight_dark": {
        "name": "午夜黑", "icon": "🌑",
        "theme_color": "#6366f1", "accent_color": "#818cf8",
        "bg_page": "linear-gradient(135deg, #000000 0%, #0a0a0a 100%)",
        "bg_sidebar": "rgba(0, 0, 0, 0.9)", "bg_card": "rgba(10, 10, 10, 0.8)",
        "dark_mode": "dark", "font_family": "system", "ui_density": "compact",
        "blur_level": 0.4, "radius_level": "small", "font_size": "13px",
        "animation_enabled": False,
    },
    "clean_light": {
        "name": "清新白", "icon": "☀️",
        "theme_color": "#3b82f6", "accent_color": "#0ea5e9",
        "bg_page": "linear-gradient(135deg, #f0f4ff 0%, #e0f2fe 100%)",
        "bg_sidebar": "rgba(255, 255, 255, 0.95)", "bg_card": "rgba(255, 255, 255, 0.9)",
        "dark_mode": "light", "font_family": "system", "ui_density": "comfortable",
        "blur_level": 0.3, "radius_level": "medium", "font_size": "14px",
        "animation_enabled": True,
    },
    "warm_paper": {
        "name": "暖纸黄", "icon": "📜",
        "theme_color": "#d97706", "accent_color": "#f59e0b",
        "bg_page": "linear-gradient(135deg, #fefce8 0%, #fef3c7 100%)",
        "bg_sidebar": "rgba(254, 252, 232, 0.95)", "bg_card": "rgba(254, 243, 199, 0.9)",
        "dark_mode": "light", "font_family": "system", "ui_density": "relaxed",
        "blur_level": 0.2, "radius_level": "large", "font_size": "15px",
        "animation_enabled": True,
    },
    "tech_green": {
        "name": "科技绿", "icon": "💚",
        "theme_color": "#22c55e", "accent_color": "#4ade80",
        "bg_page": "linear-gradient(135deg, #052e16 0%, #14532d 100%)",
        "bg_sidebar": "rgba(5, 46, 22, 0.85)", "bg_card": "rgba(5, 46, 22, 0.7)",
        "dark_mode": "dark", "font_family": "mono", "ui_density": "compact",
        "blur_level": 0.5, "radius_level": "small", "font_size": "13px",
        "animation_enabled": True,
    },
    "arctic_ice": {
        "name": "极地冰", "icon": "🧊",
        "theme_color": "#0284c7", "accent_color": "#38bdf8",
        "bg_page": "linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)",
        "bg_sidebar": "rgba(240, 249, 255, 0.95)", "bg_card": "rgba(224, 242, 254, 0.9)",
        "dark_mode": "light", "font_family": "system", "ui_density": "comfortable",
        "blur_level": 0.4, "radius_level": "medium", "font_size": "14px",
        "animation_enabled": True,
    },
    "cyber_neon": {
        "name": "赛博霓虹", "icon": "🌃",
        "theme_color": "#d946ef", "accent_color": "#22d3ee",
        "bg_page": "linear-gradient(135deg, #1a0a2e 0%, #16213e 50%, #0f3460 100%)",
        "bg_sidebar": "rgba(26, 10, 46, 0.9)", "bg_card": "rgba(22, 33, 62, 0.8)",
        "dark_mode": "dark", "font_family": "system", "ui_density": "compact",
        "blur_level": 0.8, "radius_level": "small", "font_size": "14px",
        "animation_enabled": True,
    },
}


def get_preset_themes() -> List[Dict[str, Any]]:
    """返回所有预设主题方案列表"""
    result = []
    for key, cfg in PRESET_THEMES.items():
        result.append({
            'id': key,
            'name': cfg.get('name', key),
            'icon': cfg.get('icon', '🎨'),
            'theme_color': cfg.get('theme_color'),
            'accent_color': cfg.get('accent_color'),
            'dark_mode': cfg.get('dark_mode'),
            'preview': {
                'bg': cfg.get('bg_page', ''),
                'primary': cfg.get('theme_color', ''),
                'accent': cfg.get('accent_color', ''),
            }
        })
    return result


def apply_preset_theme(username: str, theme_id: str,
                       core: 'PersonalizationCore',
                       role: str = "user",
                       device: str = "unknown") -> Dict[str, Any]:
    """应用预设主题方案到用户配置"""
    if theme_id not in PRESET_THEMES:
        return {'success': False, 'error': f'未知主题方案: {theme_id}'}
    cfg = dict(PRESET_THEMES[theme_id])
    # 剥离name/icon（非UI_THEME字段）
    ui_value = {k: v for k, v in cfg.items() if k not in ('name', 'icon')}
    r = core.set_profile(username, ProfileCategory.UI_THEME, ui_value,
                         role=role, device=device)
    if r.get('success'):
        r['theme_id'] = theme_id
        r['theme_name'] = cfg.get('name', theme_id)
    return r


def generate_css_variables(theme_config: Dict[str, Any]) -> str:
    """
    把用户UI_THEME配置转成CSS变量字符串（可直接注入<style>）
    对应前端 theme.css 的变量命名
    """
    tc = theme_config or {}

    # 输入校验（防XSS/注入：仅允许合法HEX颜色和枚举值，非法一律回退默认）
    _HEX_RE = re.compile(r'^#[0-9a-fA-F]{6}$')
    def _safe_hex(val, default):
        if isinstance(val, str) and _HEX_RE.match(val):
            return val
        return default
    def _safe_enum(val, allowed, default):
        if val in allowed:
            return val
        return default
    def _safe_str(val, pattern, default):
        if isinstance(val, str) and re.match(pattern, val):
            return val
        return default

    primary = _safe_hex(tc.get('theme_color'), '#6366f1')
    accent = _safe_hex(tc.get('accent_color'), '#06b6d4')
    dark = _safe_enum(tc.get('dark_mode'), ('light', 'dark', 'auto'), 'auto')
    blur_raw = tc.get('blur_level', 0.6)
    blur = blur_raw if isinstance(blur_raw, (int, float)) and 0 <= blur_raw <= 1 else 0.6
    radius = _safe_enum(tc.get('radius_level'), ('small', 'medium', 'large'), 'medium')
    density = _safe_enum(tc.get('ui_density'), ('compact', 'comfortable', 'relaxed'), 'comfortable')
    font_size = _safe_str(tc.get('font_size'), r'^\d{2,3}px$', '14px')
    font_family = _safe_enum(tc.get('font_family'), ('system', 'mono', 'serif'), 'system')
    animation = bool(tc.get('animation_enabled', True))
    # 背景值校验：白名单机制，仅允许 CSS 渐变/rgba/rgb/#hex 格式
    _BG_SAFE_RE = re.compile(
        r'^(linear-gradient\(|radial-gradient\(|rgba\(|rgb\(|#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})',
        re.I,
    )
    def _safe_css_bg(val, default):
        if (isinstance(val, str) and len(val) < 500
                and _BG_SAFE_RE.match(val)
                and not re.search(r'[<>{}]|;|`|\$|script|expression|javascript:|command|exec|eval', val, re.I)):
            return val
        return default
    bg_page_raw = _safe_css_bg(tc.get('bg_page'), None)
    bg_sidebar_raw = _safe_css_bg(tc.get('bg_sidebar'), None)
    bg_card_raw = _safe_css_bg(tc.get('bg_card'), None)

    # 颜色亮度判断（简单HEX转RGB取亮度）
    def _hex_lighten(hex_color: str, amount: float) -> str:
        try:
            h = hex_color.lstrip('#')
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            r = min(255, int(r + (255 - r) * amount))
            g = min(255, int(g + (255 - g) * amount))
            b = min(255, int(b + (255 - b) * amount))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    def _hex_darken(hex_color: str, amount: float) -> str:
        try:
            h = hex_color.lstrip('#')
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            r = max(0, int(r * (1 - amount)))
            g = max(0, int(g * (1 - amount)))
            b = max(0, int(b * (1 - amount)))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    def _hex_to_rgba(hex_color: str, alpha: float) -> str:
        try:
            h = hex_color.lstrip('#')
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        except Exception:
            return f"rgba(99, 102, 241, {alpha})"

    primary_light = _hex_lighten(primary, 0.15)
    primary_dark = _hex_darken(primary, 0.15)

    # 圆角
    radius_map = {'small': '6px', 'medium': '12px', 'large': '16px'}
    r_sm = radius_map.get(radius, '12px')
    r_md = str(int(r_sm.rstrip('px')) + 4) + 'px' if r_sm.endswith('px') else '12px'
    r_lg = str(int(r_sm.rstrip('px')) + 8) + 'px' if r_sm.endswith('px') else '16px'

    # 密度间距
    density_map = {
        'compact': {'s1': '2px', 's2': '4px', 's3': '8px', 's4': '12px', 's6': '16px', 's8': '24px'},
        'comfortable': {'s1': '4px', 's2': '8px', 's3': '12px', 's4': '16px', 's6': '24px', 's8': '32px'},
        'relaxed': {'s1': '6px', 's2': '12px', 's3': '16px', 's4': '20px', 's6': '28px', 's8': '40px'},
    }
    sp = density_map.get(density, density_map['comfortable'])

    # 暗黑/亮色模式背景
    is_dark = dark in ('dark', 'auto')  # auto默认走暗色（前端JS再根据时间修正）
    if is_dark:
        bg_page = bg_page_raw or f"linear-gradient(135deg, {_hex_darken(primary, 0.85)} 0%, {_hex_darken(primary, 0.75)} 100%)"
        bg_sidebar = bg_sidebar_raw or _hex_to_rgba(_hex_darken(primary, 0.9), 0.85)
        bg_card = bg_card_raw or _hex_to_rgba(_hex_darken(primary, 0.88), 0.7)
        text_primary = '#f8fafc'
        text_secondary = '#cbd5e1'
        text_muted = '#94a3b8'
    else:
        bg_page = bg_page_raw or f"linear-gradient(135deg, {_hex_lighten(primary, 0.92)} 0%, {_hex_lighten(primary, 0.85)} 100%)"
        bg_sidebar = bg_sidebar_raw or 'rgba(255, 255, 255, 0.95)'
        bg_card = bg_card_raw or 'rgba(255, 255, 255, 0.9)'
        text_primary = '#1e293b'
        text_secondary = '#475569'
        text_muted = '#64748b'

    # 字体族
    font_map = {
        'system': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        'mono': '"SF Mono", Monaco, Menlo, Consolas, "Courier New", monospace',
        'serif': 'Georgia, "Times New Roman", "Songti SC", serif',
    }
    font_str = font_map.get(font_family, font_map['system'])

    blur_px = int(blur * 20) if isinstance(blur, (int, float)) else 12

    css = f"""/* MTSCOS Personalized Theme — Auto Generated */
:root {{
  --theme-primary: {primary};
  --theme-primary-light: {primary_light};
  --theme-primary-dark: {primary_dark};
  --theme-primary-accent: {accent};
  --theme-primary-soft: {_hex_to_rgba(primary, 0.12)};
  --theme-primary-hover: {_hex_to_rgba(primary, 0.22)};
  --theme-primary-text: {primary_light};
  --theme-primary-text-bright: {_hex_lighten(primary, 0.3)};

  --theme-secondary: {accent};
  --theme-secondary-soft: {_hex_to_rgba(accent, 0.12)};
  --theme-secondary-text: {_hex_darken(accent, 0.15)};

  --theme-success: #22c55e;
  --theme-warning: #f59e0b;
  --theme-danger: #ef4444;

  --theme-text-primary: {text_primary};
  --theme-text-secondary: {text_secondary};
  --theme-text-muted: {text_muted};

  --theme-bg-page: {bg_page};
  --theme-bg-sidebar: {bg_sidebar};
  --theme-bg-card: {bg_card};
  --theme-bg-glass: {_hex_to_rgba(_hex_darken(primary, 0.88), 0.8)};

  --theme-border-subtle: {_hex_to_rgba(primary, 0.1)};
  --theme-border-strong: {_hex_to_rgba(primary, 0.18)};

  --theme-radius-sm: {r_sm};
  --theme-radius-md: {r_md};
  --theme-radius-lg: {r_lg};

  --theme-space-1: {sp['s1']};
  --theme-space-2: {sp['s2']};
  --theme-space-3: {sp['s3']};
  --theme-space-4: {sp['s4']};
  --theme-space-6: {sp['s6']};
  --theme-space-8: {sp['s8']};

  --theme-glass-blur: {blur_px}px;

  --theme-font-sans: {font_str};
  --theme-font-size-base: {font_size};

  --theme-animation-enabled: {'1' if animation else '0'};
  --theme-logo-gradient: linear-gradient(135deg, {primary}, {accent});
}}
body {{
  font-family: var(--theme-font-sans);
  font-size: var(--theme-font-size-base);
  background: var(--theme-bg-page);
  color: var(--theme-text-primary);
}}
"""
    if not animation:
        css += "\n* { animation: none !important; transition: none !important; }\n"
    return css
