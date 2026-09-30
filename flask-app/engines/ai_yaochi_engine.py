#!/usr/bin/env python3
"""
🎨 瑶池 (YAOCHI) — 仙女座绘画美术子系统
==========================================

仙女座 25 域星中的【艺术域】专属子系统.
本地 Ollama 推理生成画面描述 + 颜色方案, 用 PIL/numpy 程序化产出 PNG.
零 token 消耗 · 5 种美术风格模式.

┌──────────────────────────────────────────────────────────┐
│   🎨 concept  概念设计图  (文字描述画面细节, 颜色/光影/构图) │
│   ✒️ sketch    草图线稿    (简洁线条, 结构准确)            │
│   🖌️ ink       水墨写意    (中国风, 留白, 意境)            │
│   🎮 pixel     像素艺术    (复古风格, 8bit/16bit)          │
│   🌈 color     色彩方案    (主色/辅色/点缀色 + HEX)         │
└──────────────────────────────────────────────────────────┘

AI 员工: 青衫(L9 概念设计) · 留白(L8 水墨写意) · 像素(L7 像素艺术)
"""

from __future__ import annotations
import json, os, sys, time, uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


# ═══════════════════════════════════════════════════════════
# 瑶池子系统定义
# ═══════════════════════════════════════════════════════════
class YaochiEngine(BaseAndromedaSubsystem):
    """🎨 瑶池 — 仙女座绘画美术子系统"""

    SUBSYSTEM_NAME = "瑶池"
    SUBSYSTEM_ICON = "🎨"
    SUBSYSTEM_DESC = "绘画美术 · 概念设计 · 水墨写意 · 像素艺术 · 色彩方案"
    DB_TABLE = "mt_yaochi_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_yaochi_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT UNIQUE,
    mode            TEXT NOT NULL,
    topic           TEXT NOT NULL,
    style           TEXT DEFAULT 'default',
    color_scheme    TEXT,
    final_text      TEXT,
    artifact_path   TEXT,
    status          TEXT DEFAULT 'pending',
    duration_sec    INTEGER,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    done_at         TEXT
);
CREATE INDEX IF NOT EXISTS idx_yc_mode ON mt_yaochi_tasks(mode);
CREATE INDEX IF NOT EXISTS idx_yc_status ON mt_yaochi_tasks(status, created_at);
"""
    ARTIFACT_DIR = "yaochi_artifacts"
    ARTIFACT_EXT = "png"
    PREFERRED_MODELS = ["qwen2.5:14b-q5", "qwen2.5:7b"]  # flux2-klein 暂不支持 /api/generate
    DAEMON_NAME = "sys_yaochi"
    DAEMON_DUTY = "🎨 瑶池绘画美术子系统"

    AI_EMPLOYEES = [
        ("yc_qingshan",   "青衫",   "concept_designer",  9,  "概念设计专家. 精通画面构图/光影/色彩搭配. 擅长用文字精确描述视觉画面."),
        ("yc_liubai",     "留白",   "ink_painter",       8,  "水墨写意画家. 中国传统绘画风格. 重意境/留白/笔墨韵味."),
        ("yc_pixel",      "像素",   "pixel_artist",      7,  "像素艺术家. 8bit/16bit 复古风格. 游戏美术/图标/场景设计."),
    ]

    # ═══════════════════════════════════════════════════════
    # 5 种美术模式 + Prompt 模板
    # ═══════════════════════════════════════════════════════
    MODES = {
        "concept": {
            "name": "概念设计图", "icon": "🎨",
            "desc": "文字描述画面细节, 颜色/光影/构图",
            "prompt": lambda t,s: (
                "# 瑶池 · 概念设计图 (concept)\n\n"
                f"## 主题\n{t}\n\n"
                "## 任务\n"
                "请以视觉设计师的视角, 为这个主题写出**概念设计图的详细描述**.\n\n"
                "### 输出格式 (严格按此 JSON):\n"
                "```json\n"
                "{\n"
                '  "subject": "画面主体描述 (1-2句)",\n'
                '  "composition": "构图分析 (三分法/对称/引导线等)",\n'
                '  "lighting": "光影描述 (光源方向/色温/明暗对比)",\n'
                '  "color_scheme": {\n'
                '    "primary":  { "name": "主色名", "hex": "#RRGGBB", "role": "主色调" },\n'
                '    "secondary":{ "name": "辅色名", "hex": "#RRGGBB", "role": "辅助色" },\n'
                '    "accent":   { "name": "点缀色", "hex": "#RRGGBB", "role": "点睛" },\n'
                '    "background":{ "name": "背景色", "hex": "#RRGGBB", "role": "环境" }\n'
                "  },\n"
                '  "style_keywords": ["关键词1", "关键词2", "关键词3"],\n'
                '  "full_description": "完整画面描述 (300字以上, 像给画师的需求文档)"\n'
                "}\n"
                "```\n"
            )
        },
        "sketch": {
            "name": "草图线稿", "icon": "✒️",
            "desc": "简洁线条, 结构准确",
            "prompt": lambda t,s: f"""# 瑶池 · 草图线稿 (sketch)

## 主题
{t}

## 任务
为这个主题设计一张**草图线稿**的文字描述.

### 输出:
1. 画面结构 (主体/背景/前景 关系)
2. 关键线条走向 (用 ASCII 示意 + 文字说明)
3. 比例关系
4. HEX 配色 (2-3 色即可, 线稿 + 轻微阴影)
5. 完整描述
"""
        },
        "ink": {
            "name": "水墨写意", "icon": "🖌️",
            "desc": "中国风, 留白, 意境",
            "prompt": lambda t,s: f"""# 瑶池 · 水墨写意 (ink)

## 主题
{t}

## 任务
以**中国传统水墨写意画**风格描述这幅画面.
重视意境、留白、笔墨浓淡.

### 输出:
1. 意境说明 (画外之意)
2. 构图 (疏密/虚实/开合)
3. 笔墨技法 (浓淡/干湿/焦墨)
4. 留白位置与作用
5. HEX 配色 (墨色渐变 #1a1a1a ~ #e8e8e8 + 1色点缀如朱砂 #c0392b)
6. 题款建议
"""
        },
        "pixel": {
            "name": "像素艺术", "icon": "🎮",
            "desc": "复古风格, 8bit/16bit",
            "prompt": lambda t,s: f"""# 瑶池 · 像素艺术 (pixel)

## 主题
{t}

## 任务
设计一个**像素艺术**方案 (16x16 / 32x32 / 64x64).

### 输出:
1. 画布尺寸
2. 调色板 (4-16 色, 含 HEX)
3. 像素布局说明 (分块描述)
4. 动画帧建议 (如需)
5. 游戏/UI 使用场景
"""
        },
        "color": {
            "name": "色彩方案", "icon": "🌈",
            "desc": "主色/辅色/点缀色 + HEX",
            "prompt": lambda t,s: (
                "# 瑶池 · 色彩方案 (color)\n\n"
                f"## 主题\n{t}\n\n"
                "## 任务\n"
                "为这个主题设计一套**完整的色彩方案**.\n\n"
                "### 输出 JSON:\n"
                "```json\n"
                "{\n"
                '  "theme": "主题描述",\n'
                '  "palette_name": "配色名称",\n'
                '  "colors": [\n'
                '    {"name": "主色",   "hex": "#xxxxxx", "rgb": [0,0,0], "role": "primary",   "usage": "60% 面积"},\n'
                '    {"name": "辅色",   "hex": "#xxxxxx", "rgb": [0,0,0], "role": "secondary", "usage": "30% 面积"},\n'
                '    {"name": "点缀色", "hex": "#xxxxxx", "rgb": [0,0,0], "role": "accent",    "usage": "10% 面积"},\n'
                '    {"name": "背景色", "hex": "#xxxxxx", "rgb": [0,0,0], "role": "bg",        "usage": "背景"},\n'
                '    {"name": "文字色", "hex": "#xxxxxx", "rgb": [0,0,0], "role": "text",      "usage": "正文"}\n'
                "  ],\n"
                '  "mood": "情绪关键词",\n'
                '  "complementary": "互补色建议"\n'
                "}\n"
                "```\n"
            )
        },
    }

    # ────────────────────────────────────────────────────────
    # 生成纯色渐变 PNG (程序化产出)
    # ────────────────────────────────────────────────────────
    @staticmethod
    def _make_gradient_png(path: Path, colors: list[str], title: str, subtitle: str = ""):
        """用 PIL/numpy 生成渐变背景 + 文字说明的 PNG"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np
            W, H = 800, 600
            img = Image.new("RGB", (W, H), (250, 248, 245))

            # 渐变背景
            if len(colors) >= 2:
                c1 = YaochiEngine._hex2rgb(colors[0])
                c2 = YaochiEngine._hex2rgb(colors[1])
                arr = np.zeros((H, W, 3), dtype=np.uint8)
                for y in range(H):
                    t = y / H
                    arr[y, :, 0] = int(c1[0] + (c2[0] - c1[0]) * t)
                    arr[y, :, 1] = int(c1[1] + (c2[1] - c1[1]) * t)
                    arr[y, :, 2] = int(c1[2] + (c2[2] - c1[2]) * t)
                img = Image.fromarray(arr)

            draw = ImageDraw.Draw(img)
            # 颜色条
            bar_y = H - 80
            bar_h = 40
            for i, c in enumerate(colors[:6]):
                x0 = 40 + i * 120
                draw.rectangle([x0, bar_y, x0 + 100, bar_y + bar_h],
                               fill=YaochiEngine._hex2rgb(c), outline="white", width=2)
                draw.text((x0, bar_y + bar_h + 4), c, fill="#333333")

            # 标题
            try:
                font_lg = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 36)
                font_sm = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 20)
            except Exception:
                font_lg = ImageFont.load_default()
                font_sm = ImageFont.load_default()

            draw.text((40, 30), title[:40], fill="white", font=font_lg,
                      stroke_width=2, stroke_fill="#333333")
            if subtitle:
                draw.text((40, 90), subtitle[:60], fill="white", font=font_sm,
                          stroke_width=1, stroke_fill="#333333")

            img.save(path)
        except ImportError:
            # PIL 不可用时写一个极简 PPM (可转 PNG)
            path.write_text(f"# Yaochi Placeholder\n# {title}\n# colors: {colors}\n")

    @staticmethod
    def _hex2rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except Exception:
            return (100, 100, 100)

    # ────────────────────────────────────────────────────────
    # 提取颜色方案 (从 Ollama 输出)
    # ────────────────────────────────────────────────────────
    @staticmethod
    def _extract_colors(text: str) -> list[str]:
        import re
        hexes = re.findall(r'#[0-9a-fA-F]{6}', text)
        return hexes[:6] if hexes else ["#ff6b6b", "#4ecdc4", "#ffe66d", "#95e1d3"]

    # ═══════════════════════════════════════════════════════
    # write() 主入口
    # ═══════════════════════════════════════════════════════
    def write(self, mode: str, topic: str, style: str = "default", **kwargs) -> str:
        """瑶池生成入口: mode=concept/sketch/ink/pixel/color"""
        m = self.MODES.get(mode)
        if not m:
            print(f"[{self.SUBSYSTEM_ICON}] ❌ 未知模式 {mode}, 可用: {list(self.MODES.keys())}")
            return ""

        task_id = self.new_task_id("yc")
        start = time.time()

        print(f"\n{'═'*56}")
        print(f"{self.SUBSYSTEM_ICON} 瑶池 · {m['icon']} {m['name']}")
        print(f"   task_id: {task_id}")
        print(f"   主题: {topic[:50]}")
        print(f"{'═'*56}")

        # 落库初始
        self.db_insert_task(task_id, mode=mode, topic=topic, style=style, status="generating")

        try:
            # Ollama 生成画面描述
            prompt = m["prompt"](topic, style)
            print(f"  ⏳ Ollama 生成画面描述中...")
            draft = self.ollama_generate(prompt, max_tokens=1500)
            duration = int(time.time() - start)

            # 提取颜色
            colors = self._extract_colors(draft)
            print(f"  🎨 提取颜色: {colors}")

            # 生成渐变 PNG
            png_path = self.artifact_path / f"{task_id}.png"
            self._make_gradient_png(png_path, colors,
                                    title=f"{m['icon']} {m['name']}",
                                    subtitle=topic[:50])

            # 保存文字描述
            txt_path = self.artifact_path / f"{task_id}_desc.md"
            txt_path.write_text(
                f"# 瑶池 · {m['icon']} {m['name']}\n\n"
                f"> 主题: {topic}\n> 模式: {mode}\n> 耗时: {duration}s\n\n"
                f"## 颜色方案\n{', '.join(colors)}\n\n"
                f"## AI 描述\n\n{draft}\n", encoding="utf-8")

            artifact_file = str(png_path) if png_path.exists() else str(txt_path)

            # 更新 DB
            self.db_update_task(task_id,
                color_scheme=json.dumps(colors, ensure_ascii=False),
                final_text=draft, artifact_path=artifact_file,
                status="done", duration_sec=duration, done_at=datetime.now().isoformat())

            print(f"  ✅ 完成: {duration}s")
            print(f"  🖼️ PNG: {png_path}")
            print(f"  📝 描述: {txt_path}")

        except Exception as e:
            self.db_update_task(task_id, status="failed", done_at=datetime.now().isoformat())
            print(f"  💥 失败: {e}")
            raise

        return task_id

    def list_modes(self) -> list[str]:
        return list(self.MODES.keys())


# ═══════════════════════════════════════════════════════════
# 自检测
# ═══════════════════════════════════════════════════════════
def _SELF_TEST():
    print("\n" + "=" * 56)
    print("🎨 瑶池 (YAOCHI) — 自检测")
    print("=" * 56)
    try:
        e = YaochiEngine()
        print(f"  ✅ 引擎实例化成功")
        print(f"  ✅ DB_TABLE: {e.DB_TABLE}")
        print(f"  ✅ ARTIFACT_DIR: {e.ARTIFACT_DIR}")
        print(f"  ✅ MODES: {e.list_modes()}")
        print(f"  ✅ AI_EMPLOYEES: {len(e.AI_EMPLOYEES)} 位")
        e.register_daemon()
        e.register_ai_employees()
        print(f"  ✅ daemon + AI员工 注册完成")
        print(f"  ✅ _SELF_TEST PASSED\n")
        return True
    except Exception as ex:
        print(f"  ❌ _SELF_TEST FAILED: {ex}\n")
        return False


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="🎨 瑶池 · 仙女座绘画美术子系统")
    ap.add_argument("mode", nargs="?", default="color",
                    help="模式: concept/sketch/ink/pixel/color")
    ap.add_argument("topic", nargs="?", help="主题描述")
    ap.add_argument("--style", "-s", default="default", help="风格")
    ap.add_argument("--modes", action="store_true", help="列出所有模式")
    ap.add_argument("--list", "-l", type=int, const=10, nargs="?", help="最近 N 个 task")
    ap.add_argument("--self-test", action="store_true", help="运行自检测")
    args = ap.parse_args()

    if args.self_test:
        _SELF_TEST()
    else:
        eng = YaochiEngine()
        if args.modes:
            print("🎨 瑶池 · 5 种美术模式:")
            for k, v in eng.MODES.items():
                print(f"  {v['icon']} {k:10s} → {v['name']:10s} · {v['desc']}")
        elif args.list:
            tasks = eng.db_list_tasks(args.list)
            for t in tasks:
                print(f"  {t['task_id']}  [{t['mode']:8s}] {t['status']:8s} {str(t.get('topic',''))[:35]:35s} {t.get('duration_sec','?')}s")
        elif args.topic:
            task_id = eng.write(args.mode, args.topic, args.style)
            print(f"\n🎯 task_id={task_id}")
        else:
            ap.print_help()
