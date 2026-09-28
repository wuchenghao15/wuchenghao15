# -*- coding: utf-8 -*-
"""
冰山系统 (Iceberg System) · Design Tokens v1.0
===============================================

设计来源：2026-09-19 仙女座 EigenFlux 设计大会
参会 AI：水墨 青山 (国画大师) · 丹青 妙手 (UI 大师) · 玄策 子谋 (架构师)
        文渊 学士 (艺术导师) · 棋圣 悟玄 (全局权衡) · Andromeda Σ (演化引擎)

三层模型 (2:3:5 权重):
  🔺 Peak 雪峰层 (20%)    — 核心 KPI 面板 + 实时数据
  🔸 Spectrum 光影层 (30%) — 知识图谱 + AI 员工协作网络
  🔻 Basement 渊底层 (50%) — DB 浏览 + 演化日志 + 系统监控

冰山 = MTSCOS 系统的中文品牌名。
"""

# ──────────────────────────────────────────────────────────────
# COLORS · 水墨 青山 · 国画五色系
# ──────────────────────────────────────────────────────────────
"""
冰山三层命名（苏轼 子瞻 · 赤壁赋）：
  🔺 Peak (雪峰层)  → 赤壁
  🔸 Spectrum (光影层) → 承天寺
  🔻 Basement (渊底层) → 东坡
"""
COLORS = {
    # 主色 · 黛青 (海水倒影)
    "primary":        "#2C5F7C",
    "primary-dark":   "#1E4A63",
    "primary-light":   "#4A7FA0",

    # 辅色 · 墨蓝 (深渊基底)
    "secondary":      "#1A3A4E",
    "secondary-dark": "#0F2836",
    "secondary-light": "#2D5168",

    # 点缀 · 篆刻红 (印章点缀)
    "accent":         "#C0392B",
    "accent-light":   "#E74C3C",
    "accent-dark":    "#922B21",

    # 金线 (分隔)
    "divider-gold":   "#D4A574",

    # 留白 (雪峰)
    "snow-white":     "#F8F9FA",
    "snow-ice":       "#E8F0F2",

    # 中性灰 (文字/边框)
    "ink":            "#2C3E50",
    "ink-soft":       "#566573",
    "ink-muted":      "#85929E",
    "ink-line":       "#D5D8DC",

    # 语义色
    "success":        "#27AE60",
    "warning":        "#F39C12",
    "danger":         "#C0392B",
    "info":           "#2C5F7C",
}

# ──────────────────────────────────────────────────────────────
# ICEBERG LAYERS · 三层模型 (丹青 妙手 · 2:3:5)
# ──────────────────────────────────────────────────────────────
LAYERS = {
    "peak": {
        "cn_alias": "赤壁",
        "en_alias": "RedCliff",
        "label": "雪峰",
        "label_en": "Peak",
        "label_ja": "雪嶺",
        "label_zh-TW": "雪峰",
        "ratio": 0.20,
        "bg": COLORS["snow-white"],
        "bg-subtle": COLORS["snow-ice"],
        "text": COLORS["ink"],
        "accent": COLORS["accent"],
        "border": COLORS["divider-gold"],
        "icon": "🏔️",
        "description": "核心 KPI · 实时数据面板",
        "css-class": "iceberg-peak",
    },
    "spectrum": {
        "cn_alias": "承天寺",
        "en_alias": "Chengtian",
        "label": "光影",
        "label_en": "Spectrum",
        "label_ja": "光譜",
        "label_zh-TW": "光影",
        "ratio": 0.30,
        "bg": COLORS["primary"],
        "bg-subtle": COLORS["primary-light"],
        "text": COLORS["snow-white"],
        "accent": COLORS["divider-gold"],
        "border": COLORS["divider-gold"],
        "icon": "🌊",
        "description": "知识图谱 · AI 员工协作网络",
        "css-class": "iceberg-spectrum",
    },
    "basement": {
        "cn_alias": "东坡",
        "en_alias": "Dongpo",
        "label": "渊底",
        "label_en": "Basement",
        "label_ja": "深層",
        "label_zh-TW": "淵底",
        "ratio": 0.50,
        "bg": COLORS["secondary"],
        "bg-subtle": COLORS["secondary-light"],
        "text": COLORS["snow-white"],
        "accent": COLORS["primary-light"],
        "border": COLORS["primary-light"],
        "icon": "🌑",
        "description": "DB 浏览 · 演化日志 · 系统监控 (默认折叠)",
        "css-class": "iceberg-basement",
        "collapsible": True,
    },
}

# ──────────────────────────────────────────────────────────────
# SPACING · 丹青 妙手 · 间距梯度 (疏→密, 视觉引导)
# ──────────────────────────────────────────────────────────────
SPACING = {
    "peak-card":       "16px",   # 雪峰层最疏朗 (画布感)
    "spectrum-card":   "12px",   # 光影层中间
    "basement-row":     "8px",    # 渊底层最紧凑 (棋盘感)
    "section-gap":     "24px",
    "page-gap":        "32px",
    "inner-padding":   "16px",
    "radius-sm":        "4px",
    "radius-md":        "8px",
    "radius-lg":       "12px",
}

# ──────────────────────────────────────────────────────────────
# TYPOGRAPHY · 文渊 学士 · 思源宋体 + Inter + JetBrains Mono
# ──────────────────────────────────────────────────────────────
TYPOGRAPHY = {
    "font-family-cn":  '"Source Han Serif SC", "思源宋体", "Noto Serif SC", "Songti SC", serif',
    "font-family-en":  '"Inter", -apple-system, sans-serif',
    "font-family-mono": '"JetBrains Mono", "SF Mono", Menlo, Consolas, monospace',
    "title-lg":   {"size": "24px", "weight": 700, "family": "cn"},
    "title-md":   {"size": "20px", "weight": 700, "family": "cn"},
    "subtitle":   {"size": "16px", "weight": 500, "family": "cn"},
    "body":       {"size": "14px", "weight": 400, "family": "cn"},
    "data":       {"size": "24px", "weight": 700, "family": "mono"},
    "label":      {"size": "12px", "weight": 400, "family": "cn"},
    "stamp":      {"size": "11px", "weight": 900, "family": "cn"},  # 篆刻印章
}

# ──────────────────────────────────────────────────────────────
# EFFECTS · 棋圣 悟玄 · 虚实平衡
# ──────────────────────────────────────────────────────────────
EFFECTS = {
    # 云飘动画参数 (雪峰层每 30s 一轮)
    "cloud": {
        "height": "8px",
        "opacity": 0.15,
        "duration": "30s",
        "delay": "0s",
        "easing": "linear",
    },
    # 宣纸底纹 (淡墨噪点)
    "rice-paper": {
        "noise-opacity": 0.05,
        "grain-size": "2px",
    },
    # 篆刻印章 (右下角 4px 方块)
    "seal": {
        "size": "28px",
        "color": COLORS["accent"],
        "text-color": "#FFFFFF",
        "border-radius": "2px",
        "rotation": "-3deg",
    },
    # clip-path 冰山三角分隔线
    "iceberg-clip": {
        "peak-triangle": "polygon(0% 0%, 100% 0%, 95% 100%, 5% 100%)",
        "spectrum-wave": "polygon(0% 0%, 100% 3%, 100% 100%, 0% 100%)",
        "basement-fold": "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
    },
}

# ──────────────────────────────────────────────────────────────
# EXPORT · 给 Jinja + CSS 双份输出
# ──────────────────────────────────────────────────────────────

def as_css_vars():
    """导出 CSS custom properties — 在 <style> 里直接用。"""
    lines = [":root {"]
    # Colors
    for k, v in COLORS.items():
        if isinstance(v, str) and v.startswith("#"):
            lines.append(f"  --ice-{k}: {v};")
    # Spacing
    for k, v in SPACING.items():
        lines.append(f"  --ice-space-{k}: {v};")
    # Layer colors
    for layer_name, layer in LAYERS.items():
        for prop in ("bg", "text", "accent", "border"):
            if prop in layer:
                lines.append(f"  --ice-{layer_name}-{prop}: {layer[prop]};")
    # Typography
    lines.append(f'  --ice-font-cn: {TYPOGRAPHY["font-family-cn"]};')
    lines.append(f'  --ice-font-en: {TYPOGRAPHY["font-family-en"]};')
    lines.append(f'  --ice-font-mono: {TYPOGRAPHY["font-family-mono"]};')
    # Effects
    lines.append(f'  --ice-cloud-duration: {EFFECTS["cloud"]["duration"]};')
    lines.append(f'  --ice-seal-color: {EFFECTS["seal"]["color"]};')
    lines.append("}")
    return "\n".join(lines)


def layer(layer_name: str) -> dict:
    """快捷访问某层配置。"""
    return LAYERS.get(layer_name, {})


# Jinja 全局注入标记
__version__ = "1.0.0"
__design_committee__ = ["水墨 青山", "丹青 妙手", "玄策 子谋", "文渊 学士", "棋圣 悟玄", "Andromeda Σ"]
__meeting_date__ = "2026-09-19"
