"""
用户界面个性化布局设置服务
用于 MTSCOS AI 项目，提供用户布局偏好的存储与管理功能。
"""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LayoutPersonalizationService:
    """用户界面个性化布局设置服务类。"""

    # 允许更新的字段白名单（防止 SQL 注入和非法字段写入）
    _UPDATABLE_FIELDS = {
        'theme', 'sidebar_collapsed', 'sidebar_position', 'content_density',
        'font_size', 'color_scheme', 'language', 'dashboard_layout',
        'notification_position', 'enable_animations', 'enable_sound',
        'auto_save_interval', 'custom_css', 'pinned_modules',
        'hidden_modules', 'widget_order'
    }

    def __init__(self, db_path: str = 'app.db'):
        """初始化服务。

        Args:
            db_path: SQLite 数据库文件路径，默认为 'app.db'。
        """
        self.db_path = db_path
        self._lock = threading.RLock()
        self._init_db()

    # ------------------------------------------------------------------
    # 内部工具方法
    # ------------------------------------------------------------------
    def _get_connection(self) -> sqlite3.Connection:
        """获取 SQLite 数据库连接。"""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """初始化数据库表。"""
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_layout_preferences (
                        user_id               TEXT PRIMARY KEY,
                        theme                 TEXT DEFAULT 'auto',
                        sidebar_collapsed     INTEGER DEFAULT 0,
                        sidebar_position      TEXT DEFAULT 'left',
                        content_density       TEXT DEFAULT 'comfortable',
                        font_size             TEXT DEFAULT 'medium',
                        color_scheme          TEXT DEFAULT 'default',
                        language              TEXT DEFAULT 'zh-CN',
                        dashboard_layout      TEXT DEFAULT 'grid',
                        notification_position TEXT DEFAULT 'top-right',
                        enable_animations     INTEGER DEFAULT 1,
                        enable_sound          INTEGER DEFAULT 1,
                        auto_save_interval    INTEGER DEFAULT 30,
                        custom_css            TEXT DEFAULT '',
                        pinned_modules        TEXT DEFAULT '[]',
                        hidden_modules        TEXT DEFAULT '[]',
                        widget_order          TEXT DEFAULT '[]',
                        created_at            TEXT,
                        updated_at            TEXT
                    )
                ''')
                conn.commit()
                logger.info("数据库表 user_layout_preferences 初始化完成")
            except sqlite3.Error as e:
                logger.error("初始化数据库表失败: %s", e)
                raise
            finally:
                if 'conn' in locals():
                    conn.close()

    @staticmethod
    def _now() -> str:
        """获取当前时间字符串。"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def _json_dumps(value: Any) -> str:
        """安全序列化 JSON。"""
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            logger.warning("JSON 序列化失败: %s", e)
            return '[]'

    @staticmethod
    def _json_loads(value: Any, default: Any = None) -> Any:
        """安全反序列化 JSON。"""
        if default is None:
            default = []
        if value is None or value == '':
            return default
        if isinstance(value, (list, dict)):
            return value
        try:
            return json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError) as e:
            logger.warning("JSON 反序列化失败: %s", e)
            return default

    # ------------------------------------------------------------------
    # 偏好查询与更新
    # ------------------------------------------------------------------
    def get_default_preferences(self) -> Dict[str, Any]:
        """返回默认偏好设置。"""
        return {
            'user_id': None,
            'theme': 'auto',
            'sidebar_collapsed': 0,
            'sidebar_position': 'left',
            'content_density': 'comfortable',
            'font_size': 'medium',
            'color_scheme': 'default',
            'language': 'zh-CN',
            'dashboard_layout': 'grid',
            'notification_position': 'top-right',
            'enable_animations': 1,
            'enable_sound': 1,
            'auto_save_interval': 30,
            'custom_css': '',
            'pinned_modules': [],
            'hidden_modules': [],
            'widget_order': [],
            'created_at': None,
            'updated_at': None,
        }

    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """获取用户布局偏好，如果不存在则返回默认值。"""
        if not user_id:
            logger.warning("get_preferences: user_id 为空")
            return self.get_default_preferences()

        with self._lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM user_layout_preferences WHERE user_id = ?',
                    (user_id,)
                )
                row = cursor.fetchone()
                if row is None:
                    logger.info("用户 %s 无布局偏好记录，返回默认值", user_id)
                    defaults = self.get_default_preferences()
                    defaults['user_id'] = user_id
                    return defaults

                pref = dict(row)
                pref['pinned_modules'] = self._json_loads(pref.get('pinned_modules'), [])
                pref['hidden_modules'] = self._json_loads(pref.get('hidden_modules'), [])
                pref['widget_order'] = self._json_loads(pref.get('widget_order'), [])
                return pref
            except sqlite3.Error as e:
                logger.error("获取用户 %s 布局偏好失败: %s", user_id, e)
                defaults = self.get_default_preferences()
                defaults['user_id'] = user_id
                return defaults
            finally:
                if conn is not None:
                    conn.close()

    def update_preferences(self, user_id: str, **kwargs) -> bool:
        """更新用户布局偏好。"""
        if not user_id:
            logger.warning("update_preferences: user_id 为空")
            return False

        # 过滤出允许更新的字段
        updates: Dict[str, Any] = {}
        for key, value in kwargs.items():
            if key in self._UPDATABLE_FIELDS:
                # JSON 字段需要序列化
                if key in ('pinned_modules', 'hidden_modules', 'widget_order'):
                    updates[key] = self._json_dumps(value if value is not None else [])
                else:
                    updates[key] = value

        if not updates:
            logger.warning("update_preferences: 没有可更新的字段")
            return False

        updates['updated_at'] = self._now()

        with self._lock:
            conn = None
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                # 检查记录是否存在
                cursor.execute(
                    'SELECT user_id FROM user_layout_preferences WHERE user_id = ?',
                    (user_id,)
                )
                exists = cursor.fetchone() is not None

                if exists:
                    set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
                    values = list(updates.values()) + [user_id]
                    cursor.execute(
                        f'UPDATE user_layout_preferences SET {set_clause} WHERE user_id = ?',
                        values
                    )
                    logger.info("用户 %s 布局偏好已更新", user_id)
                else:
                    # 插入新记录
                    fields = ['user_id', 'created_at'] + list(updates.keys())
                    placeholders = ', '.join(['?'] * len(fields))
                    values = [user_id, self._now()] + list(updates.values())
                    cursor.execute(
                        f'INSERT INTO user_layout_preferences ({", ".join(fields)}) VALUES ({placeholders})',
                        values
                    )
                    logger.info("用户 %s 布局偏好已创建", user_id)

                conn.commit()
                return True
            except sqlite3.Error as e:
                logger.error("更新用户 %s 布局偏好失败: %s", user_id, e)
                if conn is not None:
                    conn.rollback()
                return False
            finally:
                if conn is not None:
                    conn.close()

    def reset_preferences(self, user_id: str) -> bool:
        """重置用户布局偏好为默认值。"""
        if not user_id:
            logger.warning("reset_preferences: user_id 为空")
            return False

        defaults = self.get_default_preferences()
        reset_fields = {
            'theme': defaults['theme'],
            'sidebar_collapsed': defaults['sidebar_collapsed'],
            'sidebar_position': defaults['sidebar_position'],
            'content_density': defaults['content_density'],
            'font_size': defaults['font_size'],
            'color_scheme': defaults['color_scheme'],
            'language': defaults['language'],
            'dashboard_layout': defaults['dashboard_layout'],
            'notification_position': defaults['notification_position'],
            'enable_animations': defaults['enable_animations'],
            'enable_sound': defaults['enable_sound'],
            'auto_save_interval': defaults['auto_save_interval'],
            'custom_css': defaults['custom_css'],
            'pinned_modules': '[]',
            'hidden_modules': '[]',
            'widget_order': '[]',
            'updated_at': self._now(),
        }
        return self.update_preferences(user_id, **reset_fields)

    # ------------------------------------------------------------------
    # 静态枚举信息
    # ------------------------------------------------------------------
    def get_available_themes(self) -> List[Dict[str, str]]:
        """返回可用主题列表。"""
        return [
            {'value': 'dark', 'label': '深色主题'},
            {'value': 'light', 'label': '浅色主题'},
            {'value': 'auto', 'label': '跟随系统'},
        ]

    def get_available_color_schemes(self) -> List[Dict[str, str]]:
        """返回可用配色方案。"""
        return [
            {'value': 'default', 'label': '默认配色'},
            {'value': 'blue', 'label': '蓝色系'},
            {'value': 'green', 'label': '绿色系'},
            {'value': 'purple', 'label': '紫色系'},
            {'value': 'orange', 'label': '橙色系'},
        ]

    # ------------------------------------------------------------------
    # 模块管理
    # ------------------------------------------------------------------
    def _get_json_field(self, user_id: str, field_name: str) -> List[Any]:
        """获取用户指定 JSON 字段（内部使用）。"""
        pref = self.get_preferences(user_id)
        return self._json_loads(pref.get(field_name), [])

    def _set_json_field(self, user_id: str, field_name: str, value: List[Any]) -> bool:
        """设置用户指定 JSON 字段（内部使用）。"""
        return self.update_preferences(user_id, **{field_name: value})

    def get_pinned_modules(self, user_id: str) -> List[Any]:
        """获取用户置顶模块。"""
        return self._get_json_field(user_id, 'pinned_modules')

    def pin_module(self, user_id: str, module_id: str) -> bool:
        """置顶模块。"""
        if not module_id:
            return False
        with self._lock:
            pinned = self.get_pinned_modules(user_id)
            if module_id in pinned:
                logger.info("模块 %s 已置顶，无需重复操作", module_id)
                return True
            pinned.append(module_id)
            return self._set_json_field(user_id, 'pinned_modules', pinned)

    def unpin_module(self, user_id: str, module_id: str) -> bool:
        """取消置顶模块。"""
        if not module_id:
            return False
        with self._lock:
            pinned = self.get_pinned_modules(user_id)
            if module_id not in pinned:
                logger.info("模块 %s 未置顶，无需操作", module_id)
                return True
            pinned = [m for m in pinned if m != module_id]
            return self._set_json_field(user_id, 'pinned_modules', pinned)

    def hide_module(self, user_id: str, module_id: str) -> bool:
        """隐藏模块。"""
        if not module_id:
            return False
        with self._lock:
            hidden = self._get_json_field(user_id, 'hidden_modules')
            if module_id in hidden:
                logger.info("模块 %s 已隐藏，无需重复操作", module_id)
                return True
            hidden.append(module_id)
            return self._set_json_field(user_id, 'hidden_modules', hidden)

    def show_module(self, user_id: str, module_id: str) -> bool:
        """显示模块（从隐藏列表中移除）。"""
        if not module_id:
            return False
        with self._lock:
            hidden = self._get_json_field(user_id, 'hidden_modules')
            if module_id not in hidden:
                logger.info("模块 %s 未被隐藏，无需操作", module_id)
                return True
            hidden = [m for m in hidden if m != module_id]
            return self._set_json_field(user_id, 'hidden_modules', hidden)

    # ------------------------------------------------------------------
    # 组件排序与自定义 CSS
    # ------------------------------------------------------------------
    def update_widget_order(self, user_id: str, widget_ids: List[str]) -> bool:
        """更新组件排序。"""
        if not isinstance(widget_ids, list):
            logger.warning("update_widget_order: widget_ids 必须为列表")
            return False
        return self._set_json_field(user_id, 'widget_order', widget_ids)

    def apply_custom_css(self, user_id: str, css: str) -> bool:
        """应用自定义 CSS。"""
        if css is None:
            css = ''
        if not isinstance(css, str):
            logger.warning("apply_custom_css: css 必须为字符串")
            return False
        return self.update_preferences(user_id, custom_css=css)

    # ------------------------------------------------------------------
    # 导入 / 导出
    # ------------------------------------------------------------------
    def export_preferences(self, user_id: str) -> Optional[str]:
        """导出用户偏好为 JSON 字符串。"""
        pref = self.get_preferences(user_id)
        if not pref or not pref.get('user_id'):
            logger.warning("export_preferences: 用户 %s 无偏好记录", user_id)
            return None
        try:
            return json.dumps(pref, ensure_ascii=False, indent=2)
        except (TypeError, ValueError) as e:
            logger.error("导出用户 %s 偏好失败: %s", user_id, e)
            return None

    def import_preferences(self, user_id: str, preferences_json: str) -> bool:
        """从 JSON 字符串导入用户偏好。"""
        if not preferences_json:
            logger.warning("import_preferences: preferences_json 为空")
            return False
        try:
            data = json.loads(preferences_json)
        except (TypeError, ValueError, json.JSONDecodeError) as e:
            logger.error("导入用户 %s 偏好失败，JSON 解析错误: %s", user_id, e)
            return False

        if not isinstance(data, dict):
            logger.error("导入用户 %s 偏好失败，JSON 顶层不是对象", user_id)
            return False

        # 剔除不允许直接写入的字段（如 user_id、created_at、updated_at）
        filtered = {
            k: v for k, v in data.items()
            if k in self._UPDATABLE_FIELDS
        }
        if not filtered:
            logger.warning("import_preferences: 解析后无可导入字段")
            return False

        return self.update_preferences(user_id, **filtered)


# 全局服务实例
layout_service = LayoutPersonalizationService()


if __name__ == '__main__':
    # 简单自测
    test_user = 'test_user_001'
    print("默认偏好:", layout_service.get_default_preferences())
    print("可用主题:", layout_service.get_available_themes())
    print("可用配色:", layout_service.get_available_color_schemes())

    layout_service.update_preferences(
        test_user,
        theme='dark',
        font_size='large',
        color_scheme='blue'
    )
    print("当前偏好:", layout_service.get_preferences(test_user))

    layout_service.pin_module(test_user, 'dashboard')
    layout_service.pin_module(test_user, 'analytics')
    print("置顶模块:", layout_service.get_pinned_modules(test_user))
    layout_service.unpin_module(test_user, 'dashboard')
    print("取消置顶后:", layout_service.get_pinned_modules(test_user))

    exported = layout_service.export_preferences(test_user)
    print("导出:", exported)

    layout_service.reset_preferences(test_user)
    print("重置后:", layout_service.get_preferences(test_user))
