# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""主题管理服务 - 增强版"""
import os
import json
import uuid
import time
import sqlite3
import threading
from enum import Enum
from typing import Dict, Any, List, Optional

DEFAULT_COLORS = {
    'primary': '#4F46E5',
    'secondary': '#6B7280',
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'info': '#3B82F6',
    'background': '#FFFFFF',
    'surface': '#F9FAFB',
    'text': '#111827',
    'text-muted': '#6B7280',
    'border': '#E5E7EB'
}


class ThemeType(Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ColorMode(Enum):
    AUTO = "auto"
    LIGHT = "light"
    DARK = "dark"


class ThemeManager:
    def __init__(self):
        self.themes = {}
        self.user_preferences: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        
        self._init_database()
        self._load_default_themes()
        
        self.active_theme = 'default'

    def _init_database(self):
        """初始化数据库"""
        try:
            db_path = 'theme_manager.db'
            self.db_conn = sqlite3.connect(db_path, check_same_thread=False)
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS themes (
                    theme_id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    theme_type TEXT NOT NULL,
                    colors TEXT NOT NULL,
                    is_default BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at REAL,
                    updated_at REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    theme_id TEXT NOT NULL,
                    color_mode TEXT DEFAULT "auto",
                    accent_color TEXT,
                    font_size TEXT DEFAULT "normal",
                    updated_at REAL,
                    FOREIGN KEY (theme_id) REFERENCES themes(theme_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS color_palettes (
                    palette_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    colors TEXT NOT NULL,
                    category TEXT,
                    created_at REAL
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_themes_type ON themes(theme_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_preferences_theme ON user_preferences(theme_id)')
            
            self.db_conn.commit()
        except Exception as e:
            print(f"主题管理数据库初始化失败: {str(e)}")

    def _load_default_themes(self):
        """加载默认主题"""
        default_themes = [
            {
                'theme_id': 'default',
                'name': '默认',
                'description': '系统默认主题',
                'theme_type': ThemeType.LIGHT.value,
                'colors': json.dumps(DEFAULT_COLORS),
                'is_default': True
            },
            {
                'theme_id': 'dark',
                'name': '深色',
                'description': '深色主题',
                'theme_type': ThemeType.DARK.value,
                'colors': json.dumps({
                    'primary': '#6366F1',
                    'secondary': '#9CA3AF',
                    'success': '#34D399',
                    'warning': '#FBBF24',
                    'danger': '#F87171',
                    'info': '#60A5FA',
                    'background': '#111827',
                    'surface': '#1F2937',
                    'text': '#F9FAFB',
                    'text-muted': '#9CA3AF',
                    'border': '#374151'
                }),
                'is_default': False
            },
            {
                'theme_id': 'blue',
                'name': '蓝色',
                'description': '蓝色主题',
                'theme_type': ThemeType.LIGHT.value,
                'colors': json.dumps({
                    'primary': '#0EA5E9',
                    'secondary': '#0284C7',
                    'success': '#059669',
                    'warning': '#D97706',
                    'danger': '#DC2626',
                    'info': '#0891B2',
                    'background': '#F0F9FF',
                    'surface': '#E0F2FE',
                    'text': '#0C4A6E',
                    'text-muted': '#075985',
                    'border': '#BAE6FD'
                }),
                'is_default': False
            },
            {
                'theme_id': 'green',
                'name': '绿色',
                'description': '绿色主题',
                'theme_type': ThemeType.LIGHT.value,
                'colors': json.dumps({
                    'primary': '#10B981',
                    'secondary': '#059669',
                    'success': '#047857',
                    'warning': '#D97706',
                    'danger': '#DC2626',
                    'info': '#0891B2',
                    'background': '#ECFDF5',
                    'surface': '#D1FAE5',
                    'text': '#064E3B',
                    'text-muted': '#047857',
                    'border': '#A7F3D0'
                }),
                'is_default': False
            },
            {
                'theme_id': 'purple',
                'name': '紫色',
                'description': '紫色主题',
                'theme_type': ThemeType.LIGHT.value,
                'colors': json.dumps({
                    'primary': '#8B5CF6',
                    'secondary': '#7C3AED',
                    'success': '#10B981',
                    'warning': '#F59E0B',
                    'danger': '#EF4444',
                    'info': '#3B82F6',
                    'background': '#FAF5FF',
                    'surface': '#F3E8FF',
                    'text': '#4C1D95',
                    'text-muted': '#6D28D9',
                    'border': '#E9D5FF'
                }),
                'is_default': False
            }
        ]
        
        with self.lock:
            for theme in default_themes:
                if theme['theme_id'] not in self.themes:
                    self.themes[theme['theme_id']] = theme
                    self._save_theme(theme)

    def _save_theme(self, theme: Dict):
        """保存主题到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO themes 
                (theme_id, name, description, theme_type, colors, is_default, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                theme['theme_id'],
                theme['name'],
                theme['description'],
                theme['theme_type'],
                theme['colors'],
                theme.get('is_default', False),
                theme.get('is_active', True),
                theme.get('created_at', time.time()),
                theme.get('updated_at', time.time())
            ))
            self.db_conn.commit()
        except Exception as e:
            print(f"保存主题失败: {str(e)}")

    def create_theme(self, name: str, description: str = "", 
                     theme_type: ThemeType = ThemeType.LIGHT,
                     colors: Dict = None) -> str:
        """创建主题"""
        if colors is None:
            colors = DEFAULT_COLORS.copy()
        
        theme_id = f"theme_{uuid.uuid4().hex[:8]}"
        
        theme = {
            'theme_id': theme_id,
            'name': name,
            'description': description,
            'theme_type': theme_type.value,
            'colors': json.dumps(colors),
            'is_default': False,
            'is_active': True,
            'created_at': time.time(),
            'updated_at': time.time()
        }
        
        with self.lock:
            self.themes[theme_id] = theme
            self._save_theme(theme)
        
        return theme_id

    def get_theme(self, theme_id: str) -> Optional[Dict]:
        """获取主题"""
        with self.lock:
            return self.themes.get(theme_id)

    def get_theme_colors(self, theme_id: str) -> Dict:
        """获取主题颜色"""
        theme = self.get_theme(theme_id)
        if theme:
            return json.loads(theme['colors'])
        return DEFAULT_COLORS

    def update_theme(self, theme_id: str, **kwargs) -> bool:
        """更新主题"""
        with self.lock:
            theme = self.themes.get(theme_id)
            if not theme:
                return False
            
            if 'name' in kwargs:
                theme['name'] = kwargs['name']
            if 'description' in kwargs:
                theme['description'] = kwargs['description']
            if 'colors' in kwargs:
                theme['colors'] = json.dumps(kwargs['colors'])
            if 'is_active' in kwargs:
                theme['is_active'] = kwargs['is_active']
            
            theme['updated_at'] = time.time()
            self._save_theme(theme)
        
        return True

    def delete_theme(self, theme_id: str) -> bool:
        """删除主题"""
        with self.lock:
            theme = self.themes.get(theme_id)
            if not theme:
                return False
            
            if theme.get('is_default', False):
                return False
            
            del self.themes[theme_id]
            
            cursor = self.db_conn.cursor()
            cursor.execute('DELETE FROM themes WHERE theme_id = ?', (theme_id,))
            cursor.execute('UPDATE user_preferences SET theme_id = "default" WHERE theme_id = ?', (theme_id,))
            self.db_conn.commit()
        
        return True

    def list_themes(self) -> List[Dict]:
        """列出所有主题"""
        with self.lock:
            return [{
                'theme_id': theme['theme_id'],
                'name': theme['name'],
                'description': theme['description'],
                'theme_type': theme['theme_type'],
                'is_default': theme.get('is_default', False),
                'is_active': theme.get('is_active', True)
            } for theme in self.themes.values()]

    def set_user_preference(self, user_id: str, theme_id: str, 
                           color_mode: ColorMode = ColorMode.AUTO,
                           accent_color: str = None,
                           font_size: str = "normal") -> bool:
        """设置用户主题偏好"""
        with self.lock:
            if theme_id not in self.themes:
                return False
            
            preference = {
                'user_id': user_id,
                'theme_id': theme_id,
                'color_mode': color_mode.value,
                'accent_color': accent_color,
                'font_size': font_size,
                'updated_at': time.time()
            }
            
            self.user_preferences[user_id] = preference
            
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences 
                (user_id, theme_id, color_mode, accent_color, font_size, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                theme_id,
                color_mode.value,
                accent_color,
                font_size,
                time.time()
            ))
            self.db_conn.commit()
        
        return True

    def get_user_preference(self, user_id: str) -> Optional[Dict]:
        """获取用户主题偏好"""
        with self.lock:
            return self.user_preferences.get(user_id)

    def generate_css(self, theme_id: str) -> str:
        """生成主题CSS"""
        colors = self.get_theme_colors(theme_id)
        
        css_vars = []
        for key, value in colors.items():
            css_vars.append(f"--color-{key}: {value};")
        
        css = f"""
:root {{
    {chr(10).join(css_vars)}
}}
"""
        return css

    def get_active_theme(self) -> Dict:
        """获取当前激活的主题"""
        return self.get_theme(self.active_theme)

    def set_active_theme(self, theme_id: str) -> bool:
        """设置激活的主题"""
        with self.lock:
            if theme_id in self.themes:
                self.active_theme = theme_id
                return True
            return False

    def get_system_theme(self) -> str:
        """获取系统主题"""
        try:
            if os.name == 'nt':
                import winreg
                reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(reg_key, "AppsUseLightTheme")
                return 'dark' if value == 0 else 'light'
            elif os.name == 'posix':
                result = os.popen('defaults read -g AppleInterfaceStyle 2>/dev/null').read().strip()
                return 'dark' if result == 'Dark' else 'light'
        except:
            pass
        
        return 'light'

    def get_theme_stats(self) -> Dict:
        """获取主题统计信息"""
        with self.lock:
            light_themes = sum(1 for t in self.themes.values() if t['theme_type'] == ThemeType.LIGHT.value)
            dark_themes = sum(1 for t in self.themes.values() if t['theme_type'] == ThemeType.DARK.value)
            
            default_count = sum(1 for t in self.themes.values() if t.get('is_default', False))
            
            user_count = len(self.user_preferences)
            
            theme_usage = {}
            for pref in self.user_preferences.values():
                theme_id = pref['theme_id']
                theme_usage[theme_id] = theme_usage.get(theme_id, 0) + 1
        
        return {
            'total_themes': len(self.themes),
            'light_themes': light_themes,
            'dark_themes': dark_themes,
            'default_count': default_count,
            'total_users_with_preferences': user_count,
            'theme_usage': theme_usage
        }


theme_manager = ThemeManager()