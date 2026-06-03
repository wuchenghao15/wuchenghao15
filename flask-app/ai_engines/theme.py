# -*- coding: utf-8 -*-
import json
import logging
from app.utils.logging import logger
from app.config import Config
import os

class ThemeAI:
    """主题配色AI: 负责统一系统主题和配色方案"""

    def __init__(self):
        self.instance_id = f"theme_ai_{id(self)}"
        self.name = "主题配色AI"
        self.description = "负责统一系统主题和配色方案"
        self.logger = logger
        self.logger.info(f"初始化主题配色AI: {self.instance_id}")

        self.unified_theme = {
            "name": "MTSCOS_Unified_Theme",
            "description": "统一的MTSCOS系统主题",
            "languages": ["japanese", "english"],
            "colors": {
                "primary": "#2c3e50",
                "secondary": "#3498db",
                "success": "#27ae60",
                "warning": "#f39c12",
                "danger": "#e74c3c",
                "info": "#17a2b8",
                "light": "#f8f9fa",
                "dark": "#343a40",
                "background": "#ffffff",
                "text": "#2c3e50",
                "text_light": "#ffffff",
                "border": "#dee2e6",
                "hover": "#3498db",
                "active": "#2980b9"
            },
            "typography": {
                "font_family": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                "font_size": {
                    "base": "16px",
                    "h1": "2.5rem",
                    "h2": "2rem",
                    "h3": "1.75rem",
                    "h4": "1.5rem",
                    "h5": "1.25rem",
                    "h6": "1rem",
                    "p": "1rem",
                    "small": "0.875rem"
                },
                "line_height": {
                    "base": "1.5",
                    "headings": "1.2"
                }
            },
            "spacing": {
                "base": "1rem",
                "small": "0.5rem",
                "large": "2rem"
            },
            "border_radius": {
                "base": "0.25rem",
                "large": "0.5rem",
                "circle": "50%"
            },
            "box_shadow": {
                "base": "0 2px 4px rgba(0, 0, 0, 0.1)",
                "hover": "0 4px 8px rgba(0, 0, 0, 0.15)",
                "active": "0 2px 4px rgba(0, 0, 0, 0.2)"
            }
        }

    def unify_theme(self, ui_elements, language="english"):
        try:
            self.logger.info(f"{self.instance_id} 正在统一主题,语言: {language}")
            themed_elements = self._apply_theme(ui_elements, language)
            self.logger.info(f"{self.instance_id} 主题统一完成")
            return themed_elements
        except Exception as e:
            self.logger.error(f"统一主题失败: {str(e)}")
            return []

    def optimize_ui(self, ui_elements):
        """优化UI元素"""
        try:
            self.logger.info(f"{self.instance_id} 正在优化UI元素")
            optimized_elements = []
            for element in ui_elements:
                optimized_element = self._optimize_element(element)
                optimized_elements.append(optimized_element)
            self.logger.info(f"{self.instance_id} UI优化完成")
            return optimized_elements
        except Exception as e:
            self.logger.error(f"优化UI失败: {str(e)}")
            return []

    def adapt_styles(self, styles, target_platform="web"):
        """适配样式到目标平台"""
        try:
            self.logger.info(f"{self.instance_id} 正在适配样式到目标平台: {target_platform}")
            adapted_styles = self._adapt_to_platform(styles, target_platform)
            self.logger.info(f"{self.instance_id} 样式适配完成")
            return adapted_styles
        except Exception as e:
            self.logger.error(f"适配样式失败: {str(e)}")
            return {}

    def get_theme_config(self, language="english"):
        """获取主题配置"""
        self.logger.info(f"{self.instance_id} 获取主题配置,语言: {language}")
        return self._get_language_adapted_theme(language)

    def _apply_theme(self, ui_elements, language):
        """应用主题到UI元素"""
        themed_elements = []
        for element in ui_elements:
            themed_element = element.copy()

            if "color" in themed_element:
                if themed_element["color"] in self.unified_theme["colors"]:
                    themed_element["color"] = self.unified_theme["colors"][themed_element["color"]]

            if "font_family" in themed_element:
                themed_element["font_family"] = self.unified_theme["typography"]["font_family"]

            if "font_size" in themed_element:
                font_size_key = themed_element["font_size"]
                if font_size_key in self.unified_theme["typography"]["font_size"]:
                    themed_element["font_size"] = self.unified_theme["typography"]["font_size"][font_size_key]

            if "border_radius" in themed_element:
                radius_key = themed_element["border_radius"]
                if radius_key in self.unified_theme["border_radius"]:
                    themed_element["border_radius"] = self.unified_theme["border_radius"][radius_key]

            themed_elements.append(themed_element)

        return themed_elements

    def _optimize_element(self, element):
        """优化单个UI元素"""
        optimized = element.copy()

        if "class" in optimized:
            if not optimized["class"].startswith("mtscos-"):
                optimized["class"] = f"mtscos-{optimized['class']}"

        if "margin" not in optimized:
            optimized["margin"] = self.unified_theme["spacing"]["base"]

        if "padding" not in optimized:
            optimized["padding"] = self.unified_theme["spacing"]["small"]

        if "border" in optimized and optimized["border"]:
            if "border_color" not in optimized:
                optimized["border_color"] = self.unified_theme["colors"]["border"]

        return optimized

    def _adapt_to_platform(self, styles, platform):
        """适配样式到目标平台"""
        adapted = styles.copy() if isinstance(styles, dict) else {}

        if platform == "mobile":
            if "typography" in adapted:
                adapted["typography"]["font_size"]["base"] = "14px"
            if "spacing" in adapted:
                adapted["spacing"]["base"] = "0.75rem"
        elif platform == "tablet":
            if "typography" in adapted:
                adapted["typography"]["font_size"]["base"] = "15px"
            if "spacing" in adapted:
                adapted["spacing"]["base"] = "0.875rem"

        return adapted

    def _get_language_adapted_theme(self, language):
        """获取适配语言的主题"""
        theme = self.unified_theme.copy()
        if language == "japanese":
            theme["typography"]["font_family"] = "'Noto Sans JP', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
        elif language == "english":
            theme["typography"]["font_family"] = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
        return theme

    def generate_css(self, theme=None):
        """生成统一的CSS样式"""
        try:
            self.logger.info(f"{self.instance_id} 生成统一CSS样式")
            target_theme = theme or self.unified_theme

            css = f"""/* MTSCOS 统一主题 CSS */
:root {{
    /* 颜色变量 */
    --primary-color: {target_theme['colors']['primary']};
    --secondary-color: {target_theme['colors']['secondary']};
    --success-color: {target_theme['colors']['success']};
    --warning-color: {target_theme['colors']['warning']};
    --danger-color: {target_theme['colors']['danger']};
    --info-color: {target_theme['colors']['info']};
    --dark-color: {target_theme['colors']['dark']};
    --background-color: {target_theme['colors']['background']};
    --text-color: {target_theme['colors']['text']};
    --text-light-color: {target_theme['colors']['text_light']};
    --border-color: {target_theme['colors']['border']};
    --hover-color: {target_theme['colors']['hover']};
    --active-color: {target_theme['colors']['active']};

    /* 排版变量 */
    --font-family: {target_theme['typography']['font_family']};
    --font-size-base: {target_theme['typography']['font_size']['base']};
    --font-size-h1: {target_theme['typography']['font_size']['h1']};
    --font-size-h2: {target_theme['typography']['font_size']['h2']};
    --font-size-h3: {target_theme['typography']['font_size']['h3']};
    --font-size-h4: {target_theme['typography']['font_size']['h4']};
    --font-size-h5: {target_theme['typography']['font_size']['h5']};
    --font-size-h6: {target_theme['typography']['font_size']['h6']};
    --font-size-p: {target_theme['typography']['font_size']['p']};
    --font-size-small: {target_theme['typography']['font_size']['small']};
    --line-height-base: {target_theme['typography']['line_height']['base']};
    --line-height-headings: {target_theme['typography']['line_height']['headings']};

    /* 间距变量 */
    --spacing-base: {target_theme['spacing']['base']};
    --spacing-small: {target_theme['spacing']['small']};
    --spacing-large: {target_theme['spacing']['large']};

    /* 边框圆角变量 */
    --border-radius-base: {target_theme['border_radius']['base']};
    --border-radius-large: {target_theme['border_radius']['large']};
    --border-radius-circle: {target_theme['border_radius']['circle']};

    /* 阴影变量 */
    --box-shadow-base: {target_theme['box_shadow']['base']};
    --box-shadow-hover: {target_theme['box_shadow']['hover']};
    --box-shadow-active: {target_theme['box_shadow']['active']};
}}

/* 全局样式重置 */
* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

body {{
    font-family: var(--font-family);
    font-size: var(--font-size-base);
    line-height: var(--line-height-base);
    color: var(--text-color);
    background-color: var(--background-color);
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: var(--font-family);
    line-height: var(--line-height-headings);
    margin-bottom: var(--spacing-base);
    color: var(--primary-color);
}}

h1 {{ font-size: var(--font-size-h1); }}
h2 {{ font-size: var(--font-size-h2); }}
h3 {{ font-size: var(--font-size-h3); }}
h4 {{ font-size: var(--font-size-h4); }}
h5 {{ font-size: var(--font-size-h5); }}
h6 {{ font-size: var(--font-size-h6); }}

p {{ margin-bottom: var(--spacing-base); }}

a {{ color: var(--primary-color); text-decoration: none; }}
a:hover {{ color: var(--hover-color); text-decoration: underline; }}

button {{
    font-family: var(--font-family);
    border-radius: var(--border-radius-base);
    cursor: pointer;
    transition: all 0.3s ease;
}}

button:hover {{ opacity: 0.9; }}
button:active {{ opacity: 0.8; }}

/* 统一的容器样式 */
.mtscos-container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: var(--spacing-base);
}}

/* 统一的卡片样式 */
.mtscos-card {{
    background-color: var(--background-color);
    border-radius: var(--border-radius-base);
    box-shadow: var(--box-shadow-base);
    padding: var(--spacing-base);
    margin-bottom: var(--spacing-base);
}}

/* 统一的按钮样式 */
.mtscos-btn {{
    display: inline-block;
    padding: var(--spacing-small) var(--spacing-base);
    font-size: var(--font-size-p);
    font-weight: 400;
    text-align: center;
    white-space: nowrap;
    vertical-align: middle;
    cursor: pointer;
    border: 1px solid transparent;
    border-radius: var(--border-radius-base);
    transition: all 0.3s ease;
}}

.mtscos-btn-primary {{
    color: var(--text-light-color);
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}}
.mtscos-btn-primary:hover {{
    background-color: var(--active-color);
    border-color: var(--active-color);
}}

.mtscos-btn-secondary {{
    color: var(--text-color);
    background-color: var(--light-color);
    border-color: var(--border-color);
}}

.mtscos-btn-secondary:hover {{
    border-color: var(--border-color);
}}

.mtscos-form-group {{
    margin-bottom: var(--spacing-base);
}}

.mtscos-form-label {{
    display: block;
    margin-bottom: var(--spacing-small);
    font-weight: 600;
}}

.mtscos-form-control {{
    width: 100%;
    padding: var(--spacing-small);
    font-size: var(--font-size-p);
    line-height: var(--line-height-base);
    color: var(--text-color);
    background-color: var(--background-color);
    background-clip: padding-box;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-base);
    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}}

.mtscos-form-control:focus {{
    outline: 0;
    box-shadow: 0 0 0 0.2rem rgba(52, 152, 219, 0.25);
}}
"""
            return css
        except Exception as e:
            self.logger.error(f"生成CSS失败: {str(e)}")
            return ""

    def __str__(self):
        return f"ThemeAI(instance_id={self.instance_id}, name={self.name})"

    def __repr__(self):
        return self.__str__()

theme_ai = ThemeAI()
