#!/usr/bin/env python3
"""仙女座 v5.2: 前端设计参数统一 — 动态 CSS 覆盖层生成器

对齐真实变量体系 (183 模板实际消费):
  - --mtscos-*  (47 变量, 最主要: admin_app/base + base_unified + 独立页)
  - --el-*      (Element Plus 基础, design_tokens.css + 部分模板)
  - --biz-*     (index.html 等独立页专用)
  - --andromeda-* (index.html 仙女座星系主题)
  - 打包源变量 (mtscos-design-system.css: --bg-primary, --font-size-base 等)

从 mt_params frontend 分组读参数 → 生成 :root 覆盖层 → 全站热生效
用法:
  python3 ai_frontend_optimizer.py once   # 生成一次
  python3 ai_frontend_optimizer.py watch  # daemon 模式 (每 10min 检查)
"""
import os, sys, time, sqlite3, hashlib

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_flask_app = os.path.dirname(_THIS_DIR)
if os.path.basename(_THIS_DIR) == "engines":
    PROJECT_ROOT = os.path.dirname(_flask_app)
else:
    PROJECT_ROOT = _THIS_DIR
APP_DB = os.path.join(PROJECT_ROOT, "Database", "app.db")
CSS_OUT = os.path.join(PROJECT_ROOT, "flask-app", "static", "css", "mtscos_frontend_overrides.css")
HASH_FILE = os.path.join(PROJECT_ROOT, "_runtime", "frontend_css_hash.txt")


def _get_conn():
    c = sqlite3.connect(APP_DB, timeout=10)
    c.execute("PRAGMA busy_timeout=10000")
    return c


def load_frontend_params() -> dict:
    """读 mt_params frontend 分组 → dict"""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT param_key, param_value, param_type FROM mt_params WHERE param_group='frontend'"
    ).fetchall()
    conn.close()
    result = {}
    for key, val, ptype in rows:
        if ptype in ("int", "integer"):
            try: val = int(val)
            except: pass
        elif ptype in ("float", "number"):
            try: val = float(val)
            except: pass
        result[key] = val
    return result


def _num(v) -> float:
    """安全转 float"""
    try: return float(v)
    except: return 0


def _hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """#RRGGBB → rgba(R,G,B,A)"""
    h = hex_color.lstrip("#")
    if len(h) == 3: h = "".join(c + c for c in h)
    if len(h) != 6: return hex_color
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def generate_overrides_css(params: dict) -> str:
    """根据 mt_params frontend 参数生成 :root 覆盖 CSS

    变量映射表 (key=mt_params, value=真实 CSS 变量):
      primary_color          → --mtscos-primary-base + --el-color-primary + --bg-primary (打包源)
      primary_gradient_start → --andromeda-gradient-start (index.html 用)
      primary_gradient_end   → --andromeda-gradient-end
      brand_color            → --mtscos-brand-color
      bg_page                → --mtscos-bg-page + --el-bg-color-page + --bg-primary (打包源)
      bg_card                → --mtscos-bg-card + --el-bg-color + --bg-card (打包源)
      text_primary           → --mtscos-text-primary + --el-text-color-primary
      text_secondary         → --mtscos-text-secondary + --el-text-color-regular
      font_size_base         → --el-font-size-base + --font-size-base (打包源)
      font_size_hero         → --mtscos-font-hero (新增)
      line_height            → --el-line-height-primary
      spacing_unit           → --mtscos-spacing-sm / md / lg / xl / 3xl (自动推导)
      container_max_width    → --mtscos-container-xl / 2xl (自动推导)
      radius_base            → --mtscos-radius-sm / md / lg (自动推导) + --el-border-radius-base
      radius_card            → --mtscos-radius-lg / xl + --biz-radius (index.html)
      radius_button          → --mtscos-btn-default-radius + --el-button-border-radius
      shadow_level           → --mtscos-shadow-md / card / card-hover (自动推导)
      transition_duration    → --mtscos-transition-base + --el-transition-duration
      default_theme          → data-theme attribute 注入 (JS 处理)
    """
    def p(k, default):
        v = params.get(k, default)
        return v

    lines = [
        "/* ==========================================================================",
        " * 仙女座 v5.2 · 前端设计参数动态覆盖层",
        " * 来源: mt_params frontend 分组 (对齐 --mtscos- / --el- / --biz- / --andromeda- 变量体系)",
        " * 生成时间: " + time.strftime("%Y-%m-%d %H:%M:%S"),
        " * 生效范围: 183 模板 (admin_app/base + base_unified + base_layout + 独立页)",
        " * ========================================================================== */",
        "",
        # 高权重选择器: 覆盖 _theme_tokens_source.css 里的 :root[data-theme="xxx"] 主题感知变量
        # _theme_tokens_source 定义 :root[data-theme="dark"] { --mtscos-primary-base: ... }
        # :root (0,1,0) < :root[data-theme="dark"] (0,2,0) — 所以我们也要带属性选择器
        # 用多重选择器覆盖所有可能的主题值
        ":root, :root[data-theme], :root[data-theme='light'], :root[data-theme='dark'],",
        ":root[data-theme='andromeda'], :root[data-theme='aurora'], :root[data-theme='auto'],",
        ":root[data-art-theme], :root[data-art-theme='aurora'], :root[data-art-theme='nebula'], :root[data-art-theme='void'] {",
        "",
        "  /* ═══════════════════════════════════════════════",
        "   * 一、主色系统 (三套变量同步覆盖)",
        "   * ═══════════════════════════════════════════════ */",
    ]

    # ── 主色 ──
    pc = p("primary_color", "#5B8FB9")
    pg_s = p("primary_gradient_start", "#0B1F3A")   # 仙女座 deep 蓝
    pg_e = p("primary_gradient_end", "#9B59B6")      # 仙女座 purple
    brand = p("brand_color", "#00979d")
    secondary = p("secondary_color", "#6FA88B")       # admin_app 里看到的 secondary

    # 自动推导: primary-dark / primary-light / primary-soft
    lines += [
        f"  /* mt_params.primary_color = {pc} */",
        f"  --mtscos-primary-base: {pc};",
        f"  --mtscos-primary-dark-1: #3d6b99;",
        f"  --mtscos-primary-dark-2: #2e5276;",
        f"  --mtscos-primary-light: #8fb0cc;",
        f"  --mtscos-primary-soft: {_hex_to_rgba(pc, 0.12)};",
        f"  --el-color-primary: {pc};",
        f"  --bg-primary: {pc};",
        f"  /* 次色 */",
        f"  --mtscos-secondary-base: {secondary};",
        f"  --mtscos-secondary-soft: {_hex_to_rgba(secondary, 0.12)};",
        f"  /* 品牌 */",
        f"  --mtscos-brand-color: {brand};",
        f"  /* 仙女座星系渐变 (index.html 等独立页消费) */",
        f"  --andromeda-gradient-start: {pg_s};",
        f"  --andromeda-gradient-end: {pg_e};",
        f"  --andromeda-purple: {pg_e};",
        f"  --andromeda-deep: {pg_s};",
        f"  --andromeda-blue: #2E86DE;",
        f"  --andromeda-grad: linear-gradient(135deg, {pg_s} 0%, #2E86DE 40%, {pg_e} 75%, #FF6B9D 100%);",
        f"  --andromeda-grad-soft: linear-gradient(135deg, {_hex_to_rgba('#2E86DE', 0.08)}, {_hex_to_rgba(pg_e, 0.10)});",
        "",
        "  /* ═══════════════════════════════════════════════",
        "   * 二、背景系统",
        "   * ═══════════════════════════════════════════════ */",
    ]

    bg_page = p("bg_page", "#F7F3EC")
    bg_card = p("bg_card", "#FFFFFF")
    bg_soft = _hex_to_rgba(bg_page, 0.55)

    lines += [
        f"  --mtscos-bg-page: {bg_page};",
        f"  --mtscos-bg-card: {bg_card};",
        f"  --mtscos-bg-soft: {bg_soft};",
        f"  --el-bg-color-page: {bg_page};",
        f"  --el-bg-color: {bg_card};",
        f"  /* 打包源变量 (mtscos-design-system.css) */",
        f"  --bg-primary: {bg_page};",
        f"  --bg-secondary: #EBEEF5;",
        f"  --bg-card: {bg_card};",
        f"  --bg-soft: {bg_soft};",
        "",
        "  /* ═══════════════════════════════════════════════",
        "   * 三、文本系统",
        "   * ═══════════════════════════════════════════════ */",
    ]

    tp = p("text_primary", "#1f2d3d")
    ts = p("text_secondary", "#7a8aa0")
    ti = "#FFFFFF"

    lines += [
        f"  --mtscos-text-primary: {tp};",
        f"  --mtscos-text-secondary: {ts};",
        f"  --mtscos-text-tertiary: #a0b0c0;",
        f"  --mtscos-text-inverse: {ti};",
        f"  --el-text-color-primary: {tp};",
        f"  --el-text-color-regular: {tp};",
        f"  --el-text-color-secondary: {ts};",
        "",
        "  /* ═══════════════════════════════════════════════",
        "   * 四、圆角系统 (对齐 mtscos + biz + el 三套)",
        "   * ═══════════════════════════════════════════════ */",
    ]

    rb = _num(p("radius_base", 8))
    rc = _num(p("radius_card", 12))
    rbtn = _num(p("radius_button", 8))

    lines += [
        f"  --mtscos-radius-xs: {max(rb - 4, 2)}px;",
        f"  --mtscos-radius-sm: {max(rb - 2, 4)}px;",
        f"  --mtscos-radius-md: {rb}px;",
        f"  --mtscos-radius-lg: {rc}px;",
        f"  --mtscos-radius-xl: {rc + 4}px;",
        f"  --mtscos-radius-full: 999px;",
        f"  --el-border-radius-base: {rb}px;",
        f"  --el-border-radius-round: {rbtn}px;",
        f"  /* index.html 独立页专用 */",
        f"  --biz-radius: {rc}px;",
        f"  /* 按钮 */",
        f"  --mtscos-btn-default-radius: {rbtn}px;",
        f"  --el-button-border-radius: {rbtn}px;",
        "",
        "  /* ═══════════════════════════════════════════════",
        "   * 五、间距系统 (基于 spacing_unit 自动推导 5 级)",
        "   * ═══════════════════════════════════════════════ */",
    ]

    su = _num(p("spacing_unit", 8))

    lines += [
        f"  --mtscos-spacing-xs: {su}px;",
        f"  --mtscos-spacing-sm: {su * 2}px;",
        f"  --mtscos-spacing-md: {su * 3}px;",
        f"  --mtscos-spacing-lg: {su * 4}px;",
        f"  --mtscos-spacing-xl: {su * 6}px;",
        f"  --mtscos-spacing-3xl: {su * 8}px;",
        f"  --mtscos-container-xl: {int(p('container_max_width', 1280))}px;",
        f"  --mtscos-container-2xl: {int(p('container_max_width', 1280)) + 256}px;",
        "",
        "  /* ═══════════════════════════════════════════════",
        "   * 六、字体系统",
        "   * ═══════════════════════════════════════════════ */",
    ]

    fb = _num(p("font_size_base", 14))
    lh = p("line_height", 1.5)

    lines += [
        f"  --mtscos-font-sans: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;",
        f"  --mtscos-font-mono: 'SFMono-Regular', Menlo, monospace;",
        f"  --el-font-family: var(--mtscos-font-sans);",
        f"  --el-font-size-base: {fb}px;",
        f"  --font-size-base: {fb}px;",
        f"  --el-line-height-primary: {lh};",
        f"  --mtscos-font-hero: {_num(p('font_size_hero', 20))}px;",
        "",
        "  /* ═══════════════════════════════════════════════",
        "   * 七、动效系统",
        "   * ═══════════════════════════════════════════════ */",
    ]

    td = _num(p("transition_duration", 200))

    lines += [
        f"  --mtscos-transition-base: {td}ms;",
        f"  --el-transition-duration: {td}ms;",
        f"  --mtscos-animation-duration-base: {td}ms;",
        f"  --mtscos-animation-delay-fast: {td // 2}ms;",
        "",
        "  /* ═══════════════════════════════════════════════",
        "   * 八、阴影系统 (shadow_level 1-3 自动推导)",
        "   * ═══════════════════════════════════════════════ */",
    ]

    sl = int(p("shadow_level", 2))
    shadows = [
        ("0 1px 3px rgba(0,0,0,0.08)", "0 4px 12px -4px rgba(0,0,0,0.10)", "0 16px 48px -12px rgba(0,0,0,0.16)"),
        ("0 2px 6px rgba(0,0,0,0.10)", "0 8px 20px -6px rgba(0,0,0,0.14)", "0 24px 64px -16px rgba(0,0,0,0.22)"),
        ("0 4px 10px rgba(0,0,0,0.12)", "0 12px 32px -8px rgba(0,0,0,0.18)", "0 32px 80px -20px rgba(0,0,0,0.28)"),
    ]
    sm, sc, sch = shadows[max(0, min(sl - 1, 2))]

    lines += [
        f"  --mtscos-shadow-sm: {sm};",
        f"  --mtscos-shadow-md: {sc};",
        f"  --mtscos-shadow-card: {sc};",
        f"  --mtscos-shadow-card-hover: {sch};",
        f"  --mtscos-shadow-glow: 0 0 28px {_hex_to_rgba(pg_e, 0.30)}, 0 0 60px {_hex_to_rgba('#2E86DE', 0.18)};",
        f"  /* index.html 专用 */",
        f"  --biz-shadow: {sch};",
        f"  --biz-shadow-soft: {sc};",
        f"  --biz-shadow-card-hover: {sch};",
        "",
        "  /* ═══════════════════════════════════════════════",
        "   * 九、边框 + 状态色",
        "   * ═══════════════════════════════════════════════ */",
    ]

    danger = "#d15b5b"
    success = "#6FA88B"
    warning = "#E6A23C"
    info = "#5B8FB9"

    lines += [
        f"  --mtscos-border-light: {_hex_to_rgba(pc, 0.15)};",
        f"  --mtscos-border-base: {_hex_to_rgba(pc, 0.25)};",
        f"  --mtscos-border-lighter: {_hex_to_rgba(pc, 0.08)};",
        f"  --biz-line: {_hex_to_rgba(pg_e, 0.12)};",
        f"  --mtscos-success-base: {success};",
        f"  --mtscos-success-soft: {_hex_to_rgba(success, 0.12)};",
        f"  --mtscos-danger: {danger};",
        f"  --mtscos-danger-base: {danger};",
        f"  --mtscos-danger-soft: {_hex_to_rgba(danger, 0.12)};",
        f"  --mtscos-warning: {warning};",
        f"  --mtscos-warning-soft: {_hex_to_rgba(warning, 0.12)};",
        f"  --mtscos-info: {info};",
        f"  --mtscos-info-soft: {_hex_to_rgba(info, 0.12)};",
        "",
        "  /* ═══════════════════════════════════════════════",
        "   * 十、导航结构变量 (供消费方 var() 调用)",
        "   * 注意: class 硬编码高度不直接覆盖, 通过 padding/transform 适配",
        "   * ═══════════════════════════════════════════════ */",
    ]

    nav_h = int(p("nav_bar_height", 56))
    sb_w = int(p("nav_sidebar_width", 240))
    sb_c = int(p("nav_sidebar_collapsed", 64))

    lines += [
        f"  --nav-header-height: {nav_h}px;",
        f"  --nav-sidebar-width: {sb_w}px;",
        f"  --nav-sidebar-collapsed: {sb_c}px;",
        "",
        "}",  # :root 结束
        "",
        "/* ==========================================================================",
        " * END · mt_params frontend overrides (v5.2)",
        " * ========================================================================== */",
    ]

    return "\n".join(lines) + "\n"


def refresh_css(force: bool = False) -> dict:
    """读 mt_params → 写 CSS 文件 → 返回变更信息"""
    os.makedirs(os.path.dirname(CSS_OUT), exist_ok=True)

    params = load_frontend_params()
    content = generate_overrides_css(params)

    new_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    old_hash = ""
    if os.path.exists(HASH_FILE):
        try: old_hash = open(HASH_FILE).read().strip()
        except: pass

    if old_hash == new_hash and not force:
        return {"status": "unchanged", "hash": new_hash, "params_count": len(params)}

    tmp = CSS_OUT + ".tmp"
    with open(tmp, "w") as f:
        f.write(content)
    os.replace(tmp, CSS_OUT)

    os.makedirs(os.path.dirname(HASH_FILE), exist_ok=True)
    with open(HASH_FILE, "w") as f:
        f.write(new_hash)

    size = os.path.getsize(CSS_OUT)
    return {"status": "written", "hash": new_hash, "params_count": len(params), "size": size}


def watch_loop():
    """daemon 模式: 每 10min 检查一次 mt_params 变更"""
    print(f"[FRONTEND-OPT] v5.2 watch 模式启动 (cycle=600s)")
    last = ""
    while True:
        try:
            result = refresh_css()
            if result["status"] == "written":
                print(f"[FRONTEND-OPT] CSS 已刷新 hash={result['hash']} size={result['size']}")
            else:
                print(f"[FRONTEND-OPT] 无变更 hash={result['hash']}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[FRONTEND-OPT] err: {e}")
        time.sleep(600)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        watch_loop()
    else:
        result = refresh_css(force=True)
        print(f"[FRONTEND-OPT] v5.2 {result}")
