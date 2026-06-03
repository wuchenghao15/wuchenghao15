# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主题配色系统 V2.0 (Theme System)
增强版主题配色系统，支持多主题管理、颜色系统、用户偏好和实时预览
"""

import os
import time
import uuid
import json
import hashlib
import logging
import threading
import sqlite3
import base64
from enum import Enum
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('theme_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ThemeSystem')

class ThemeType(Enum):
    """主题类型枚举"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    CUSTOM = "custom"

class ColorPalette(Enum):
    """调色板枚举"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    ACCENT = "accent"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    BACKGROUND = "background"
    TEXT = "text"
    BORDER = "border"

@dataclass
class ColorValue:
    """颜色值"""
    hex: str
    rgb: Tuple[int, int, int]
    hsl: Tuple[int, int, int]
    alpha: float = 1.0
    
    def __post_init__(self):
        if self.alpha < 0:
            self.alpha = 0.0
        elif self.alpha > 1:
            self.alpha = 1.0
    
    def to_css(self) -> str:
        if self.alpha < 1:
            return f"rgba({self.rgb[0]}, {self.rgb[1]}, {self.rgb[2]}, {self.alpha})"
        return self.hex
    
    def to_rgba(self) -> str:
        return f"rgba({self.rgb[0]}, {self.rgb[1]}, {self.rgb[2]}, {self.alpha})"
    
    def to_hsla(self) -> str:
        return f"hsla({self.hsl[0]}, {self.hsl[1]}%, {self.hsl[2]}%, {self.alpha})"

@dataclass
class ColorPalette:
    """调色板"""
    name: str
    colors: Dict[str, str]

@dataclass
class ThemeColors:
    """主题颜色"""
    primary: ColorValue
    secondary: ColorValue
    accent: ColorValue
    success: ColorValue
    warning: ColorValue
    error: ColorValue
    info: ColorValue
    background: ColorValue
    surface: ColorValue
    text: ColorValue
    text_secondary: ColorValue
    border: ColorValue
    shadow: ColorValue
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "primary": self.primary.to_css(),
            "secondary": self.secondary.to_css(),
            "accent": self.accent.to_css(),
            "success": self.success.to_css(),
            "warning": self.warning.to_css(),
            "error": self.error.to_css(),
            "info": self.info.to_css(),
            "background": self.background.to_css(),
            "surface": self.surface.to_css(),
            "text": self.text.to_css(),
            "text_secondary": self.text_secondary.to_css(),
            "border": self.border.to_css(),
            "shadow": self.shadow.to_css()
        }

@dataclass
class Theme:
    """主题"""
    theme_id: str
    name: str
    theme_type: ThemeType
    description: str = ""
    colors: Dict[str, str] = None
    typography: Dict = None
    spacing: Dict = None
    border_radius: Dict = None
    shadows: Dict = None
    is_system: bool = False
    is_active: bool = False
    created_at: float = 0.0
    updated_at: float = 0.0
    
    def __post_init__(self):
        if self.colors is None:
            self.colors = {}
        if self.typography is None:
            self.typography = {}
        if self.spacing is None:
            self.spacing = {}
        if self.border_radius is None:
            self.border_radius = {}
        if self.shadows is None:
            self.shadows = {}
        if self.created_at == 0.0:
            self.created_at = time.time()

@dataclass
class UserThemePreference:
    """用户主题偏好"""
    preference_id: str
    user_id: str
    theme_id: str
    custom_colors: Dict = None
    font_size: str = "medium"
    font_family: str = "system"
    reduced_motion: bool = False
    high_contrast: bool = False
    created_at: float = 0.0
    updated_at: float = 0.0
    
    def __post_init__(self):
        if self.custom_colors is None:
            self.custom_colors = {}
        if self.created_at == 0.0:
            self.created_at = time.time()

@dataclass
class ColorScheme:
    """色彩方案"""
    scheme_id: str
    name: str
    base_colors: Dict[str, str]
    variations: Dict[str, Dict[str, str]] = None
    description: str = ""
    
    def __post_init__(self):
        if self.variations is None:
            self.variations = {}

class ThemeSystem:
    """增强版主题配色系统"""
    
    def __init__(self):
        """初始化主题系统"""
        self.themes: Dict[str, Theme] = {}
        self.user_preferences: Dict[str, UserThemePreference] = {}
        self.color_schemes: Dict[str, ColorScheme] = {}
        
        self.lock = threading.Lock()
        
        self._init_database()
        self._init_default_themes()
        self._init_color_schemes()
        
        logger.info("主题配色系统初始化完成")
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.db_conn = sqlite3.connect('theme_system.db', check_same_thread=False)
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS themes (
                    theme_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    theme_type TEXT NOT NULL,
                    description TEXT,
                    colors TEXT,
                    typography TEXT,
                    spacing TEXT,
                    border_radius TEXT,
                    shadows TEXT,
                    is_system BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT FALSE,
                    created_at REAL,
                    updated_at REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    preference_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    theme_id TEXT NOT NULL,
                    custom_colors TEXT,
                    font_size TEXT DEFAULT 'medium',
                    font_family TEXT DEFAULT 'system',
                    reduced_motion BOOLEAN DEFAULT FALSE,
                    high_contrast BOOLEAN DEFAULT FALSE,
                    created_at REAL,
                    updated_at REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS color_schemes (
                    scheme_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_colors TEXT NOT NULL,
                    variations TEXT,
                    description TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS theme_usage_stats (
                    stat_id TEXT PRIMARY KEY,
                    theme_id TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    last_used REAL,
                    FOREIGN KEY (theme_id) REFERENCES themes(theme_id)
                )
            ''')
            
            self.db_conn.commit()
            logger.info("主题系统数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """HEX转RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hsl(self, r: int, g: int, b: int) -> Tuple[int, int, int]:
        """RGB转HSL"""
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        l = (max_c + min_c) / 2
        
        if max_c == min_c:
            h = s = 0
        else:
            d = max_c - min_c
            s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
            
            if max_c == r:
                h = ((g - b) / d + (g < b and 6 or 0)) / 6
            elif max_c == g:
                h = ((b - r) / d + 2) / 6
            else:
                h = ((r - g) / d + 4) / 6
        
        return (int(h * 360), int(s * 100), int(l * 100))
    
    def _create_color_value(self, hex_color: str, alpha: float = 1.0) -> ColorValue:
        """创建颜色值"""
        rgb = self._hex_to_rgb(hex_color)
        hsl = self._rgb_to_hsl(*rgb)
        return ColorValue(hex=hex_color, rgb=rgb, hsl=hsl, alpha=alpha)
    
    def _init_default_themes(self):
        """初始化默认主题"""
        default_themes = [
            Theme(
                theme_id="theme_default",
                name="默认主题",
                theme_type=ThemeType.LIGHT,
                description="系统默认浅色主题",
                colors={
                    "primary": "#3B82F6",
                    "secondary": "#64748B",
                    "accent": "#8B5CF6",
                    "success": "#10B981",
                    "warning": "#F59E0B",
                    "error": "#EF4444",
                    "info": "#06B6D4",
                    "background": "#FFFFFF",
                    "surface": "#F8FAFC",
                    "text": "#1E293B",
                    "text_secondary": "#64748B",
                    "border": "#E2E8F0",
                    "shadow": "rgba(0, 0, 0, 0.1)"
                },
                typography={
                    "font_family": "system-ui, -apple-system, sans-serif",
                    "font_size_base": "16px",
                    "line_height": "1.5"
                },
                is_system=True,
                is_active=True
            ),
            Theme(
                theme_id="theme_dark",
                name="深色主题",
                theme_type=ThemeType.DARK,
                description="护眼深色主题",
                colors={
                    "primary": "#60A5FA",
                    "secondary": "#94A3B8",
                    "accent": "#A78BFA",
                    "success": "#34D399",
                    "warning": "#FBBF24",
                    "error": "#F87171",
                    "info": "#22D3EE",
                    "background": "#0F172A",
                    "surface": "#1E293B",
                    "text": "#F1F5F9",
                    "text_secondary": "#94A3B8",
                    "border": "#334155",
                    "shadow": "rgba(0, 0, 0, 0.3)"
                },
                typography={
                    "font_family": "system-ui, -apple-system, sans-serif",
                    "font_size_base": "16px",
                    "line_height": "1.5"
                },
                is_system=True
            ),
            Theme(
                theme_id="theme_ocean",
                name="海洋主题",
                theme_type=ThemeType.LIGHT,
                description="清新海洋风格",
                colors={
                    "primary": "#0891B2",
                    "secondary": "#64748B",
                    "accent": "#06B6D4",
                    "success": "#10B981",
                    "warning": "#F59E0B",
                    "error": "#EF4444",
                    "info": "#0EA5E9",
                    "background": "#F0F9FF",
                    "surface": "#E0F2FE",
                    "text": "#0C4A6E",
                    "text_secondary": "#0369A1",
                    "border": "#BAE6FD",
                    "shadow": "rgba(8, 145, 178, 0.1)"
                },
                is_system=True
            ),
            Theme(
                theme_id="theme_forest",
                name="森林主题",
                theme_type=ThemeType.LIGHT,
                description="自然森林风格",
                colors={
                    "primary": "#059669",
                    "secondary": "#64748B",
                    "accent": "#10B981",
                    "success": "#34D399",
                    "warning": "#FBBF24",
                    "error": "#EF4444",
                    "info": "#06B6D4",
                    "background": "#F0FDF4",
                    "surface": "#DCFCE7",
                    "text": "#14532D",
                    "text_secondary": "#166534",
                    "border": "#86EFAC",
                    "shadow": "rgba(5, 150, 105, 0.1)"
                },
                is_system=True
            ),
            Theme(
                theme_id="theme_sunset",
                name="日落主题",
                theme_type=ThemeType.LIGHT,
                description="温暖日落风格",
                colors={
                    "primary": "#EA580C",
                    "secondary": "#64748B",
                    "accent": "#F97316",
                    "success": "#10B981",
                    "warning": "#FBBF24",
                    "error": "#EF4444",
                    "info": "#06B6D4",
                    "background": "#FFFBEB",
                    "surface": "#FEF3C7",
                    "text": "#7C2D12",
                    "text_secondary": "#9A3412",
                    "border": "#FED7AA",
                    "shadow": "rgba(234, 88, 12, 0.1)"
                },
                is_system=True
            ),
            Theme(
                theme_id="theme_midnight",
                name="午夜主题",
                theme_type=ThemeType.DARK,
                description="深邃午夜风格",
                colors={
                    "primary": "#818CF8",
                    "secondary": "#94A3B8",
                    "accent": "#A78BFA",
                    "success": "#34D399",
                    "warning": "#FBBF24",
                    "error": "#F87171",
                    "info": "#22D3EE",
                    "background": "#030712",
                    "surface": "#111827",
                    "text": "#F9FAFB",
                    "text_secondary": "#9CA3AF",
                    "border": "#1F2937",
                    "shadow": "rgba(0, 0, 0, 0.5)"
                },
                is_system=True
            ),
            Theme(
                theme_id="theme_pastel",
                name="马卡龙主题",
                theme_type=ThemeType.LIGHT,
                description="甜美马卡龙风格",
                colors={
                    "primary": "#F472B6",
                    "secondary": "#A78BFA",
                    "accent": "#C084FC",
                    "success": "#34D399",
                    "warning": "#FBBF24",
                    "error": "#F87171",
                    "info": "#22D3EE",
                    "background": "#FDF2F8",
                    "surface": "#FCE7F3",
                    "text": "#831843",
                    "text_secondary": "#BE185D",
                    "border": "#FBCFE8",
                    "shadow": "rgba(244, 114, 182, 0.15)"
                },
                is_system=True
            )
        ]
        
        with self.lock:
            for theme in default_themes:
                if theme.theme_id not in self.themes:
                    self.themes[theme.theme_id] = theme
                    self._save_theme(theme)
    
    def _init_color_schemes(self):
        """初始化色彩方案"""
        schemes = [
            ColorScheme(
                scheme_id="scheme_blue",
                name="蓝色系",
                base_colors={
                    "primary": "#3B82F6",
                    "secondary": "#60A5FA",
                    "tertiary": "#93C5FD"
                },
                description="经典蓝色调"
            ),
            ColorScheme(
                scheme_id="scheme_green",
                name="绿色系",
                base_colors={
                    "primary": "#10B981",
                    "secondary": "#34D399",
                    "tertiary": "#6EE7B7"
                },
                description="清新绿色调"
            ),
            ColorScheme(
                scheme_id="scheme_purple",
                name="紫色系",
                base_colors={
                    "primary": "#8B5CF6",
                    "secondary": "#A78BFA",
                    "tertiary": "#C4B5FD"
                },
                description="优雅紫色调"
            ),
            ColorScheme(
                scheme_id="scheme_orange",
                name="橙色系",
                base_colors={
                    "primary": "#F97316",
                    "secondary": "#FB923C",
                    "tertiary": "#FDBA74"
                },
                description="活力橙色调"
            ),
            ColorScheme(
                scheme_id="scheme_pink",
                name="粉色系",
                base_colors={
                    "primary": "#EC4899",
                    "secondary": "#F472B6",
                    "tertiary": "#F9A8D4"
                },
                description="甜美粉色调"
            )
        ]
        
        with self.lock:
            for scheme in schemes:
                if scheme.scheme_id not in self.color_schemes:
                    self.color_schemes[scheme.scheme_id] = scheme
    
    def _save_theme(self, theme: Theme):
        """保存主题到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO themes
                (theme_id, name, theme_type, description, colors, typography, spacing, 
                 border_radius, shadows, is_system, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                theme.theme_id, theme.name, theme.theme_type.value, theme.description,
                json.dumps(theme.colors), json.dumps(theme.typography),
                json.dumps(theme.spacing), json.dumps(theme.border_radius),
                json.dumps(theme.shadows), theme.is_system, theme.is_active,
                theme.created_at, theme.updated_at
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存主题失败: {str(e)}")
    
    def create_theme(self, name: str, theme_type: ThemeType, description: str = "",
                   colors: Dict = None) -> str:
        """创建主题"""
        theme_id = f"theme_{uuid.uuid4().hex[:8]}"
        
        if colors is None:
            default_theme = self.themes.get("theme_default")
            colors = default_theme.colors if default_theme else {}
        
        theme = Theme(
            theme_id=theme_id,
            name=name,
            theme_type=theme_type,
            description=description,
            colors=colors
        )
        
        with self.lock:
            self.themes[theme_id] = theme
            self._save_theme(theme)
        
        logger.info(f"创建主题: {name} ({theme_id})")
        return theme_id
    
    def get_theme(self, theme_id: str) -> Optional[Theme]:
        """获取主题"""
        with self.lock:
            return self.themes.get(theme_id)
    
    def update_theme(self, theme_id: str, **kwargs) -> bool:
        """更新主题"""
        with self.lock:
            theme = self.themes.get(theme_id)
            if not theme:
                return False
            
            if 'name' in kwargs:
                theme.name = kwargs['name']
            if 'description' in kwargs:
                theme.description = kwargs['description']
            if 'colors' in kwargs:
                theme.colors.update(kwargs['colors'])
            if 'typography' in kwargs:
                theme.typography.update(kwargs['typography'])
            
            theme.updated_at = time.time()
            self._save_theme(theme)
        
        logger.info(f"更新主题: {theme_id}")
        return True
    
    def delete_theme(self, theme_id: str) -> bool:
        """删除主题"""
        with self.lock:
            theme = self.themes.get(theme_id)
            if not theme:
                return False
            
            if theme.is_system:
                logger.error("不能删除系统主题")
                return False
            
            del self.themes[theme_id]
            
            cursor = self.db_conn.cursor()
            cursor.execute('DELETE FROM themes WHERE theme_id = ?', (theme_id,))
            self.db_conn.commit()
        
        logger.info(f"删除主题: {theme_id}")
        return True
    
    def list_themes(self) -> List[Dict]:
        """列出所有主题"""
        with self.lock:
            return [{
                "theme_id": theme.theme_id,
                "name": theme.name,
                "theme_type": theme.theme_type.value,
                "description": theme.description,
                "is_system": theme.is_system,
                "is_active": theme.is_active,
                "created_at": theme.created_at
            } for theme in self.themes.values()]
    
    def activate_theme(self, theme_id: str) -> bool:
        """激活主题"""
        with self.lock:
            theme = self.themes.get(theme_id)
            if not theme:
                return False
            
            for other_theme in self.themes.values():
                other_theme.is_active = False
                self._save_theme(other_theme)
            
            theme.is_active = True
            self._save_theme(theme)
        
        logger.info(f"激活主题: {theme_id}")
        return True
    
    def generate_css(self, theme_id: str) -> str:
        """生成主题CSS"""
        theme = self.themes.get(theme_id)
        if not theme:
            return ""
        
        colors = theme.colors
        
        css = f"""/* Theme: {theme.name} */
:root {{
    --theme-primary: {colors.get('primary', '#3B82F6')};
    --theme-secondary: {colors.get('secondary', '#64748B')};
    --theme-accent: {colors.get('accent', '#8B5CF6')};
    --theme-success: {colors.get('success', '#10B981')};
    --theme-warning: {colors.get('warning', '#F59E0B')};
    --theme-error: {colors.get('error', '#EF4444')};
    --theme-info: {colors.get('info', '#06B6D4')};
    --theme-background: {colors.get('background', '#FFFFFF')};
    --theme-surface: {colors.get('surface', '#F8FAFC')};
    --theme-text: {colors.get('text', '#1E293B')};
    --theme-text-secondary: {colors.get('text_secondary', '#64748B')};
    --theme-border: {colors.get('border', '#E2E8F0')};
    --theme-shadow: {colors.get('shadow', 'rgba(0, 0, 0, 0.1)')};
    
    /* Typography */
    --theme-font-family: {theme.typography.get('font_family', 'system-ui, sans-serif')};
    --theme-font-size-base: {theme.typography.get('font_size_base', '16px')};
    --theme-line-height: {theme.typography.get('line_height', '1.5')};
}}
"""
        
        if theme.theme_type == ThemeType.DARK:
            css += """
[data-theme="dark"] {
    color-scheme: dark;
}
"""
        
        return css
    
    def save_user_preference(self, user_id: str, theme_id: str, 
                           custom_colors: Dict = None, **kwargs) -> str:
        """保存用户偏好"""
        preference_id = f"pref_{uuid.uuid4().hex[:8]}"
        
        with self.lock:
            for pref_id, pref in self.user_preferences.items():
                if pref.user_id == user_id:
                    preference_id = pref_id
                    if custom_colors:
                        pref.custom_colors.update(custom_colors)
                    if 'font_size' in kwargs:
                        pref.font_size = kwargs['font_size']
                    if 'font_family' in kwargs:
                        pref.font_family = kwargs['font_family']
                    if 'reduced_motion' in kwargs:
                        pref.reduced_motion = kwargs['reduced_motion']
                    if 'high_contrast' in kwargs:
                        pref.high_contrast = kwargs['high_contrast']
                    pref.updated_at = time.time()
                    self._save_user_preference(pref)
                    return preference_id
            
            pref = UserThemePreference(
                preference_id=preference_id,
                user_id=user_id,
                theme_id=theme_id,
                custom_colors=custom_colors or {},
                **kwargs
            )
            
            self.user_preferences[preference_id] = pref
            self._save_user_preference(pref)
        
        logger.info(f"保存用户偏好: {user_id} -> {theme_id}")
        return preference_id
    
    def _save_user_preference(self, pref: UserThemePreference):
        """保存用户偏好到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences
                (preference_id, user_id, theme_id, custom_colors, font_size, 
                 font_family, reduced_motion, high_contrast, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pref.preference_id, pref.user_id, pref.theme_id,
                json.dumps(pref.custom_colors), pref.font_size, pref.font_family,
                pref.reduced_motion, pref.high_contrast, pref.created_at, pref.updated_at
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存用户偏好失败: {str(e)}")
    
    def get_user_preference(self, user_id: str) -> Optional[UserThemePreference]:
        """获取用户偏好"""
        with self.lock:
            for pref in self.user_preferences.values():
                if pref.user_id == user_id:
                    return pref
        return None
    
    def generate_user_css(self, user_id: str) -> str:
        """生成用户个性化CSS"""
        pref = self.get_user_preference(user_id)
        if not pref:
            return self.generate_css("theme_default")
        
        theme = self.themes.get(pref.theme_id)
        if not theme:
            return self.generate_css("theme_default")
        
        css = self.generate_css(pref.theme_id)
        
        if pref.custom_colors:
            custom_css = ":root {\n"
            for key, value in pref.custom_colors.items():
                custom_css += f"    --custom-{key}: {value};\n"
            custom_css += "}\n"
            css += custom_css
        
        if pref.font_size != "medium":
            size_map = {
                "small": "14px",
                "large": "18px",
                "extra_large": "20px"
            }
            css += f"""
html {{
    font-size: {size_map.get(pref.font_size, '16px')};
}}
"""
        
        return css
    
    def create_color_variation(self, base_color: str, variation_type: str) -> str:
        """创建颜色变体"""
        rgb = self._hex_to_rgb(base_color)
        r, g, b = rgb
        h, s, l = self._rgb_to_hsl(r, g, b)
        
        if variation_type == "lighter":
            l = min(l + 20, 100)
        elif variation_type == "darker":
            l = max(l - 20, 0)
        elif variation_type == "saturated":
            s = min(s + 20, 100)
        elif variation_type == "desaturated":
            s = max(s - 20, 0)
        
        r_hex = int((h / 360) * 255)
        g_hex = int((s / 100) * 255)
        b_hex = int((l / 100) * 255)
        
        return f"#{r_hex:02X}{g_hex:02X}{b_hex:02X}"
    
    def blend_colors(self, color1: str, color2: str, ratio: float = 0.5) -> str:
        """混合两种颜色"""
        rgb1 = self._hex_to_rgb(color1)
        rgb2 = self._hex_to_rgb(color2)
        
        r = int(rgb1[0] * (1 - ratio) + rgb2[0] * ratio)
        g = int(rgb1[1] * (1 - ratio) + rgb2[1] * ratio)
        b = int(rgb1[2] * (1 - ratio) + rgb2[2] * ratio)
        
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def get_complementary_color(self, color: str) -> str:
        """获取互补色"""
        rgb = self._hex_to_rgb(color)
        r, g, b = rgb
        
        r = 255 - r
        g = 255 - g
        b = 255 - b
        
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def generate_gradient(self, color1: str, color2: str, direction: str = "to right") -> str:
        """生成渐变"""
        return f"linear-gradient({direction}, {color1}, {color2})"
    
    def export_theme(self, theme_id: str) -> Dict:
        """导出版式"""
        theme = self.themes.get(theme_id)
        if not theme:
            return {}
        
        return {
            "version": "2.0",
            "exported_at": time.time(),
            "theme": {
                "theme_id": theme.theme_id,
                "name": theme.name,
                "theme_type": theme.theme_type.value,
                "description": theme.description,
                "colors": theme.colors,
                "typography": theme.typography
            }
        }
    
    def import_theme(self, theme_data: Dict) -> str:
        """导入主题"""
        try:
            theme_info = theme_data['theme']
            
            theme = Theme(
                theme_id=f"theme_{uuid.uuid4().hex[:8]}",
                name=theme_info['name'],
                theme_type=ThemeType(theme_info['theme_type']),
                description=theme_info.get('description', ''),
                colors=theme_info['colors'],
                typography=theme_info.get('typography', {})
            )
            
            with self.lock:
                self.themes[theme.theme_id] = theme
                self._save_theme(theme)
            
            logger.info(f"导入主题: {theme.theme_id}")
            return theme.theme_id
        
        except Exception as e:
            logger.error(f"导入主题失败: {str(e)}")
            raise
    
    def get_color_schemes(self) -> List[Dict]:
        """获取色彩方案"""
        with self.lock:
            return [{
                "scheme_id": scheme.scheme_id,
                "name": scheme.name,
                "base_colors": scheme.base_colors,
                "description": scheme.description
            } for scheme in self.color_schemes.values()]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.lock:
            total_themes = len(self.themes)
            system_themes = sum(1 for t in self.themes.values() if t.is_system)
            custom_themes = total_themes - system_themes
            active_theme = next((t.theme_id for t in self.themes.values() if t.is_active), None)
            total_users = len(self.user_preferences)
        
        return {
            "total_themes": total_themes,
            "system_themes": system_themes,
            "custom_themes": custom_themes,
            "active_theme": active_theme,
            "total_users_with_preferences": total_users,
            "total_color_schemes": len(self.color_schemes)
        }


def test_theme_system():
    """测试主题系统"""
    print("主题配色系统 V2.0 测试")
    print("=" * 60)
    
    ts = ThemeSystem()
    
    print("列出主题:")
    themes = ts.list_themes()
    for theme in themes:
        print(f"  {theme['name']}: {theme['theme_type']} {'(系统)' if theme['is_system'] else ''}")
    
    print("\n创建自定义主题:")
    custom_theme_id = ts.create_theme(
        name="我的主题",
        theme_type=ThemeType.CUSTOM,
        description="自定义主题",
        colors={
            "primary": "#FF6B6B",
            "secondary": "#4ECDC4",
            "accent": "#FFE66D",
            "background": "#FFFFFF",
            "surface": "#F7F7F7"
        }
    )
    print(f"  创建主题: {custom_theme_id}")
    
    print("\n激活主题:")
    ts.activate_theme(custom_theme_id)
    print(f"  已激活: {custom_theme_id}")
    
    print("\n生成CSS:")
    css = ts.generate_css(custom_theme_id)
    print(f"  CSS长度: {len(css)} 字符")
    
    print("\n颜色工具测试:")
    lighter = ts.create_color_variation("#3B82F6", "lighter")
    darker = ts.create_color_variation("#3B82F6", "darker")
    complementary = ts.get_complementary_color("#3B82F6")
    gradient = ts.generate_gradient("#3B82F6", "#8B5CF6")
    print(f"  原色: #3B82F6")
    print(f"  亮色: {lighter}")
    print(f"  暗色: {darker}")
    print(f"  互补色: {complementary}")
    print(f"  渐变: {gradient[:50]}...")
    
    print("\n导出主题:")
    export_data = ts.export_theme("theme_default")
    print(f"  导出成功: {len(json.dumps(export_data))} 字符")
    
    print("\n保存用户偏好:")
    pref_id = ts.save_user_preference(
        user_id="user123",
        theme_id="theme_ocean",
        font_size="large",
        reduced_motion=True
    )
    print(f"  保存偏好: {pref_id}")
    
    print("\n生成用户CSS:")
    user_css = ts.generate_user_css("user123")
    print(f"  CSS长度: {len(user_css)} 字符")
    
    print("\n获取色彩方案:")
    schemes = ts.get_color_schemes()
    for scheme in schemes:
        print(f"  {scheme['name']}: {list(scheme['base_colors'].keys())}")
    
    print("\n获取统计:")
    stats = ts.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n主题配色系统 V2.0 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_theme_system()