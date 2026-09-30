#!/usr/bin/env python3
"""
🎬 繁花 (FANHUA) — 仙女座影视短视频子系统
==========================================

仙女座 25 域星中的【影视域】专属子系统.
本地 Ollama 推理生成分镜脚本 Markdown, subprocess 调 ffmpeg 生成 5s 彩色预览片段.
零 token 消耗 · 5 种影视短视频模式.

┌──────────────────────────────────────────────────────────┐
│   🎬 storyboard  分镜脚本   (10-15 个镜头, 景别/角度/时长) │
│   📝 script      短视频脚本 (60秒内, 钩子-内容-结尾)         │
│   📋 shotlist    镜头清单   (编号/景别/时长/备注)           │
│   ✂️ editplan    剪辑方案   (BGM/转场/字幕/调色)             │
│   🖼️ title       标题封面   (3个备选标题 + 封面描述)         │
└──────────────────────────────────────────────────────────┘

AI 员工: 导演(L9 分镜) · 剪辑(L8 剪辑方案) · 镜头(L7 镜头语言)
"""

from __future__ import annotations
import json, os, sys, time, uuid, subprocess
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class FanhuaEngine(BaseAndromedaSubsystem):
    """🎬 繁花 — 仙女座影视短视频子系统"""

    SUBSYSTEM_NAME = "繁花"
    SUBSYSTEM_ICON = "🎬"
    SUBSYSTEM_DESC = "影视短视频 · 分镜脚本 · 剪辑方案 · 镜头语言"
    DB_TABLE = "mt_fanhua_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_fanhua_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT UNIQUE,
    mode            TEXT NOT NULL,
    topic           TEXT NOT NULL,
    duration_sec    INTEGER DEFAULT 60,
    platforms       TEXT DEFAULT '抖音,小红书',
    storyboard_json TEXT,
    final_text      TEXT,
    artifact_path   TEXT,
    status          TEXT DEFAULT 'pending',
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    done_at         TEXT
);
CREATE INDEX IF NOT EXISTS idx_fh_mode   ON mt_fanhua_tasks(mode);
CREATE INDEX IF NOT EXISTS idx_fh_status ON mt_fanhua_tasks(status, created_at);
"""
    ARTIFACT_DIR = "fanhua_artifacts"
    ARTIFACT_EXT = "md"
    PREFERRED_MODELS = ["qwen2.5:14b-q5", "qwen2.5:14b"]
    DAEMON_NAME = "sys_fanhua"
    DAEMON_DUTY = "🎬 繁花影视短视频子系统"

    AI_EMPLOYEES = [
        ("fh_daoyan",   "导演", "storyboard_director", 9, "分镜导演. 10-15 镜头规划. 景别/角度/构图/时长分配."),
        ("fh_jianji",   "剪辑", "video_editor",        8, "剪辑专家. BGM/转场/字幕/调色方案. 节奏控制."),
        ("fh_jingtou",  "镜头", "cinematographer",    7, "镜头语言专家. 运镜/景深/光线/色彩."),
    ]

    # ── 5 种模式 ──────────────────────────────────────────
    MODES = {
        "storyboard": {
            "name": "分镜脚本", "icon": "🎬",
            "desc": "10-15 个镜头, 景别/角度/时长/台词",
            "prompt": lambda t,d,p: f"""# 繁花 · 分镜脚本 (storyboard)

## 需求
- 主题: {t}
- 总时长: {d}秒
- 平台: {p}

## 输出 Markdown
按以下格式写 10-15 个镜头:

```
## 镜头 1 | [景别] [运镜] [角度] | [时长]s
- **画面**: 画面描述
- **台词/旁白**: 台词
- **音效**: 音效
- **BGM**: 音乐情绪

## 镜头 2 | ...
```

景别参考: 特写 / 近景 / 中景 / 全景 / 远景
运镜参考: 固定 / 推 / 拉 / 摇 / 移 / 跟 / 升降
角度参考: 平视 / 俯拍 / 仰拍 / 倾斜
"""
        },
        "script": {
            "name": "短视频脚本", "icon": "📝",
            "desc": "60秒内, 钩子-内容-结尾",
            "prompt": lambda t,d,p: f"""# 繁花 · 短视频脚本 (script)

## 需求
- 主题: {t}
- 总时长: {d}秒
- 平台: {p}

## 三段式结构 (黄金 3 秒钩子)
1. **Hook 钩子 (0-3s)**: 直接冲击, 制造悬念/冲突
2. **Content 内容 (3-{d-5}s)**: 核心信息, 3-5 个要点
3. **Ending 结尾 ({d-5}-{d}s)**: CTA / 金句 / 反转

## 输出 Markdown
```
# [标题]

## 0:00-0:03 · 钩子
- 画面: ...
- 台词: ...

## 0:03-0:30 · 内容
...

## 0:30-0:{d} · 结尾
...

## 标题备选
1. ...
2. ...
3. ...
```
"""
        },
        "shotlist": {
            "name": "镜头清单", "icon": "📋",
            "desc": "编号/景别/时长/备注",
            "prompt": lambda t,d,p: f"""# 繁花 · 镜头清单 (shotlist)

## 主题
{t}

## 输出表格 (Markdown)
| # | 景别 | 角度 | 运镜 | 时长(s) | 画面描述 | 备注 |
|---|------|------|------|---------|----------|------|
| 1 | ...  | ...  | ...  | ...     | ...      | ...  |

至少 10 个镜头, 覆盖起承转合.
"""
        },
        "editplan": {
            "name": "剪辑方案", "icon": "✂️",
            "desc": "BGM/转场/字幕/调色",
            "prompt": lambda t,d,p: f"""# 繁花 · 剪辑方案 (editplan)

## 主题 / 原始素材
{t}

## 输出 JSON
```json
{{
  "bgm": {{
    "style": "情绪关键词",
    "bpm": 120,
    "suggestions": ["歌名1", "歌名2"],
    "volume_fade_in": true,
    "volume_fade_out": true
  }},
  "transitions": [
    {{"from": 1, "to": 2, "type": "硬切/叠化/黑场", "duration": 0.5}}
  ],
  "subtitles": {{
    "style": "底部白字黑描边",
    "font": "思源黑体 Bold",
    "size": 28
  }},
  "color_grading": {{
    "preset": "电影感/日系/胶片",
    "contrast": 1.1,
    "saturation": 1.05,
    "temperature": 5500
  }},
  "pacing_notes": "节奏控制建议"
}}
```
"""
        },
        "title": {
            "name": "标题封面", "icon": "🖼️",
            "desc": "3个备选标题 + 封面图描述",
            "prompt": lambda t,d,p: f"""# 繁花 · 标题封面 (title)

## 主题
{t}

## 输出 JSON
```json
{{
  "titles": [
    {{"text": "备选标题1", "style": "短/悬念/数字/emoji", "clickbait_level": 3}},
    {{"text": "备选标题2", "style": "...", "clickbait_level": 2}},
    {{"text": "备选标题3", "style": "...", "clickbait_level": 1}}
  ],
  "cover_image": {{
    "composition": "构图描述",
    "colors": ["主色HEX", "辅色HEX"],
    "text_overlay": "封面大标题文字",
    "style_keywords": ["关键词"]
  }},
  "platform_specific": {{
    "douyin": "抖音版标题 (20字内)",
    "xiaohongshu": "小红书版标题 (emoji+分段)"
  }}
}}
```
"""
        },
    }

    # ────────────────────────────────────────────────────────
    # ffmpeg 生成 5s 彩色测试片段
    # ────────────────────────────────────────────────────────
    @staticmethod
    def _make_test_mp4(path: Path, duration: float = 5.0,
                         resolution: str = "640x360",
                         colors: tuple[str, str] = ("red", "blue")) -> bool:
        """用 ffmpeg 生成测试片段, 返回是否成功"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, timeout=5)
            if result.returncode != 0:
                print(f"  ⚠️ ffmpeg 未安装, 跳过视频生成")
                return False
        except FileNotFoundError:
            print(f"  ⚠️ ffmpeg 未找到, 跳过视频生成")
            return False

        try:
            # 生成颜色渐变测试卡
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c={colors[0]}:s={resolution}:d={duration}",
                "-f", "lavfi",
                "-i", f"color=c={colors[1]}:s={resolution}:d={duration}",
                "-filter_complex",
                f"[0:v][1:v]blend=all_mode='overlay':all_opacity=0.5,drawtext=text='FANHUA':fontsize=40:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                str(path)
            ], capture_output=True, timeout=30)
            return path.exists()
        except Exception as e:
            print(f"  ⚠️ ffmpeg 执行失败: {e}")
            return False

    # ═══════════════════════════════════════════════════════
    def write(self, mode: str, topic: str, duration_sec: int = 60,
              platforms: str = "抖音,小红书", **kwargs) -> str:
        """繁花生成入口"""
        m = self.MODES.get(mode)
        if not m:
            print(f"[{self.SUBSYSTEM_ICON}] ❌ 未知模式 {mode}, 可用: {list(self.MODES.keys())}")
            return ""

        task_id = self.new_task_id("fh")
        start = time.time()

        print(f"\n{'═'*56}")
        print(f"{self.SUBSYSTEM_ICON} 繁花 · {m['icon']} {m['name']}")
        print(f"   task_id: {task_id}")
        print(f"   主题: {topic[:50]} · 时长: {duration_sec}s · 平台: {platforms}")
        print(f"{'═'*56}")

        self.db_insert_task(task_id, mode=mode, topic=topic,
            duration_sec=duration_sec, platforms=platforms, status="generating")

        try:
            prompt = m["prompt"](topic, duration_sec, platforms)
            print(f"  ⏳ Ollama 生成分镜内容中...")
            draft = self.ollama_generate(prompt, max_tokens=2000)
            duration = int(time.time() - start)

            # 尝试保存 storyboard JSON
            sb_json = None
            try:
                # 简单正则提取 JSON
                import re
                json_blocks = re.findall(r'```json\s*(.*?)```', draft, re.DOTALL)
                if json_blocks:
                    sb_json = json.dumps(json.loads(json_blocks[0]), ensure_ascii=False)
            except Exception:
                pass

            # 保存 Markdown 分镜
            md_path = self.artifact_path / f"{task_id}.md"
            md_path.write_text(
                f"# 繁花 · {m['icon']} {m['name']}\n\n"
                f"> 主题: {topic}\n> 时长: {duration_sec}s\n> 平台: {platforms}\n"
                f"> 模式: {mode}\n> 耗时: {duration}s\n\n"
                f"---\n\n{draft}\n", encoding="utf-8")

            # 尝试生成预览视频
            mp4_path = self.artifact_path / f"{task_id}_preview.mp4"
            video_ok = self._make_test_mp4(mp4_path, duration=5.0)

            artifact_file = str(md_path)
            if video_ok:
                artifact_file += f" | {mp4_path}"

            self.db_update_task(task_id,
                storyboard_json=sb_json,
                final_text=draft,
                artifact_path=artifact_file,
                status="done",
                done_at=datetime.now().isoformat())

            print(f"  ✅ 完成: {duration}s")
            print(f"  📄 分镜: {md_path}")
            if video_ok:
                print(f"  🎥 预览: {mp4_path}")

        except Exception as e:
            self.db_update_task(task_id, status="failed",
                done_at=datetime.now().isoformat())
            print(f"  💥 失败: {e}")
            raise

        return task_id


def _SELF_TEST():
    print("\n" + "=" * 56)
    print("🎬 繁花 (FANHUA) — 自检测")
    print("=" * 56)
    try:
        e = FanhuaEngine()
        print(f"  ✅ 引擎实例化成功")
        print(f"  ✅ DB_TABLE: {e.DB_TABLE}")
        print(f"  ✅ MODES: {list(e.MODES.keys())}")
        print(f"  ✅ AI_EMPLOYEES: {len(e.AI_EMPLOYEES)} 位")
        e.register_daemon()
        e.register_ai_employees()
        print(f"  ✅ _SELF_TEST PASSED\n")
        return True
    except Exception as ex:
        print(f"  ❌ _SELF_TEST FAILED: {ex}\n")
        return False


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="🎬 繁花 · 仙女座影视短视频子系统")
    ap.add_argument("mode", nargs="?", default="storyboard",
                    help="模式: storyboard/script/shotlist/editplan/title")
    ap.add_argument("topic", nargs="?", help="主题")
    ap.add_argument("--duration", "-d", type=int, default=60, help="目标时长(秒)")
    ap.add_argument("--platforms", "-p", default="抖音,小红书", help="目标平台")
    ap.add_argument("--modes", action="store_true", help="列出模式")
    ap.add_argument("--list", "-l", type=int, const=10, nargs="?", help="最近 N 个 task")
    ap.add_argument("--self-test", action="store_true", help="自检测")
    args = ap.parse_args()

    if args.self_test:
        _SELF_TEST()
    else:
        eng = FanhuaEngine()
        if args.modes:
            print("🎬 繁花 · 5 种影视模式:")
            for k, v in eng.MODES.items():
                print(f"  {v['icon']} {k:12s} → {v['name']:12s} · {v['desc']}")
        elif args.list:
            tasks = eng.db_list_tasks(args.list)
            for t in tasks:
                print(f"  {t['task_id']}  [{t['mode']:12s}] {t['status']:8s} {str(t.get('topic',''))[:35]:35s}")
        elif args.topic:
            task_id = eng.write(args.mode, args.topic, args.duration, args.platforms)
            print(f"\n🎯 task_id={task_id}")
        else:
            ap.print_help()
