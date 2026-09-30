#!/usr/bin/env python3
"""
🎵 梵音 (FANYIN) — 仙女座音乐乐理子系统
==========================================

仙女座 25 域星中的【音乐域】专属子系统.
本地 Ollama 推理生成简谱/和弦/乐理分析, 用 wave+struct 程序化产出 WAV.
零 token 消耗 · 5 种音乐模式.

┌──────────────────────────────────────────────────────────┐
│   🎼 melody    旋律创作   (C大调和弦进行, 数字简谱 1234567) │
│   🎹 harmony   和弦配器   (I-V-vi-IV 等进行, 标功能)         │
│   🥁 rhythm    节奏型     (4/4拍, BPM, 鼓点模式)           │
│   📚 theory    乐理分析   (调性/音程/调式/转调)             │
│   🎧 arrange   编曲方案   (乐器分配, 声部层次)              │
└──────────────────────────────────────────────────────────┘

AI 员工: 伯牙(L9 旋律大师) · 嵇康(L8 和弦配器) · 律吕(L7 乐理)
"""

from __future__ import annotations
import json, os, sys, time, uuid, wave, struct, math
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class FanyinEngine(BaseAndromedaSubsystem):
    """🎵 梵音 — 仙女座音乐乐理子系统"""

    SUBSYSTEM_NAME = "梵音"
    SUBSYSTEM_ICON = "🎵"
    SUBSYSTEM_DESC = "音乐乐理 · 旋律创作 · 和弦配器 · 节奏型 · 编曲方案"
    DB_TABLE = "mt_fanyin_tasks"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_fanyin_tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT UNIQUE,
    mode            TEXT NOT NULL,
    topic           TEXT NOT NULL,
    key_signature   TEXT DEFAULT 'C',
    tempo           INTEGER DEFAULT 120,
    chord_progression TEXT,
    melody_score    TEXT,
    final_text      TEXT,
    artifact_path   TEXT,
    status          TEXT DEFAULT 'pending',
    duration_sec    INTEGER,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    done_at         TEXT
);
CREATE INDEX IF NOT EXISTS idx_fy_mode   ON mt_fanyin_tasks(mode);
CREATE INDEX IF NOT EXISTS idx_fy_status ON mt_fanyin_tasks(status, created_at);
"""
    ARTIFACT_DIR = "fanyin_artifacts"
    ARTIFACT_EXT = "wav"
    PREFERRED_MODELS = ["qwen2.5:14b-q5", "qwen2.5:14b"]
    DAEMON_NAME = "sys_fanyin"
    DAEMON_DUTY = "🎵 梵音音乐乐理子系统"

    AI_EMPLOYEES = [
        ("fy_boya",   "伯牙", "melody_master", 9, "旋律创作大师. 精通数字简谱/五线谱/调性调式. 擅长写动人旋律."),
        ("fy_jikang", "嵇康", "harmonist",     8, "和弦配器专家. I-V-vi-IV/ii-V-I 等进行. 功能和声分析."),
        ("fy_lvlv",   "律吕", "theorist",       7, "乐理专家. 调性/音程/调式/转调/对位法."),
    ]

    # ── 5 种模式 ──────────────────────────────────────────
    MODES = {
        "melody": {
            "name": "旋律创作", "icon": "🎼",
            "desc": "C大调和弦进行, 数字简谱 1234567",
            "prompt": lambda t,ks,tp: f"""# 梵音 · 旋律创作 (melody)

## 需求
- 主题: {t}
- 调性: {ks}大调
- BPM: {tp}

## 输出 JSON
```json
{{
  "key": "{ks}",
  "tempo": {tp},
  "time_signature": "4/4",
  "chord_progression": "C-G-Am-F (I-V-vi-IV)",
  "melody": [
    {{"note": "1", "duration": "4", "lyric": ""}},
    {{"note": "2", "duration": "2", "lyric": ""}}
  ],
  "full_score": "完整简谱文本 (含音符+时值+和弦标)",
  "emotion": "情绪关键词"
}}
```
数字简谱: 1=C, 1234567 对应 Do Re Mi Fa Sol La Si, 高音加点如 1̇
"""
        },
        "harmony": {
            "name": "和弦配器", "icon": "🎹",
            "desc": "I-V-vi-IV 等进行, 标功能",
            "prompt": lambda t,ks,tp: f"""# 梵音 · 和弦配器 (harmony)

## 主题
{t}

## 输出 JSON
```json
{{
  "key": "{ks}",
  "progressions": [
    {{
      "name": "流行经典进行",
      "roman": "I-V-vi-IV",
      "chords": ["C", "G", "Am", "F"],
      "function": "主-属-下中-下属",
      "usage": "流行/民谣/抒情"
    }}
  ],
  "analysis": "功能和声分析 (300字)"
}}
```
"""
        },
        "rhythm": {
            "name": "节奏型", "icon": "🥁",
            "desc": "4/4拍, BPM, 鼓点模式",
            "prompt": lambda t,ks,tp: f"""# 梵音 · 节奏型 (rhythm)

## 主题
{t}

## 输出 JSON
```json
{{
  "bpm": {tp},
  "time_signature": "4/4",
  "patterns": [
    {{
      "name": "基础摇滚",
      "kick": "X . . . X . . .",
      "snare": ". . X . . . X .",
      "hihat": "x x x x x x x x"
    }}
  ],
  "groove_desc": "律动描述"
}}
```
"""
        },
        "theory": {
            "name": "乐理分析", "icon": "📚",
            "desc": "调性/音程/调式/转调",
            "prompt": lambda t,ks,tp: f"""# 梵音 · 乐理分析 (theory)

## 主题 / 乐谱
{t}

## 输出
1. 调性判断 (大调/小调/调式)
2. 音程分析
3. 和弦功能标注
4. 调式音阶说明
5. 转调可能性
6. 对位法建议 (如有)
"""
        },
        "arrange": {
            "name": "编曲方案", "icon": "🎧",
            "desc": "乐器分配, 声部层次",
            "prompt": lambda t,ks,tp: f"""# 梵音 · 编曲方案 (arrange)

## 需求
- 主题: {t}
- 调性: {ks}
- BPM: {tp}

## 输出 JSON
```json
{{
  "instruments": [
    {{"name": "原声吉他", "role": "节奏", "range": "中低", "layer": 1}},
    {{"name": "人声",     "role": "主旋律", "range": "中",   "layer": 2}},
    {{"name": "贝斯",     "role": "低音",   "range": "低",   "layer": 1}},
    {{"name": "电子鼓",   "role": "节奏",   "range": "全",   "layer": 1}},
    {{"name": "合成器",   "role": "Pad",    "range": "中高", "layer": 3}}
  ],
  "structure": "Intro-Verse-Chorus-Verse-Chorus-Bridge-Chorus-Outro",
  "dynamics": "力度变化标注"
}}
```
"""
        },
    }

    # ────────────────────────────────────────────────────────
    # 生成简单正弦波 WAV (A4=440Hz, 5秒)
    # ────────────────────────────────────────────────────────
    @staticmethod
    def _make_sine_wav(path: Path, duration_sec: float = 5.0,
                        freq: float = 440.0, sample_rate: int = 44100):
        """程序化生成正弦波 WAV"""
        n_frames = int(sample_rate * duration_sec)
        samples = []
        for i in range(n_frames):
            t = i / sample_rate
            # A4=440Hz + 轻微颤音
            f = freq + 2 * math.sin(2 * math.pi * 5 * t)
            sample = int(12000 * math.sin(2 * math.pi * f * t))
            samples.append(struct.pack("<h", sample))

        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(b"".join(samples))

    @staticmethod
    def _make_multi_tone_wav(path: Path, notes: list[float],
                              note_duration: float = 0.5,
                              sample_rate: int = 44100):
        """多音符拼接"""
        all_samples = []
        for freq in notes:
            n = int(sample_rate * note_duration)
            for i in range(n):
                t = i / sample_rate
                s = int(10000 * math.sin(2 * math.pi * freq * t))
                all_samples.append(struct.pack("<h", s))

        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(b"".join(all_samples))

    # ── 提取音符频率 ────────────────────────────────────────
    @staticmethod
    def _extract_notes(text: str) -> list[float]:
        """从简谱数字提取频率 (C4=261.63Hz)"""
        NOTE_FREQ = {"1": 261.63, "2": 293.66, "3": 329.63,
                     "4": 349.23, "5": 392.00, "6": 440.00, "7": 493.88}
        import re
        digits = re.findall(r'[1-7]', text)
        if digits:
            return [NOTE_FREQ.get(d, 440.0) for d in digits[:16]]
        return [440.0, 523.25, 587.33, 659.25]  # 默认 A C E G#

    # ═══════════════════════════════════════════════════════
    def write(self, mode: str, topic: str, key_signature: str = "C",
              tempo: int = 120, **kwargs) -> str:
        """梵音生成入口"""
        m = self.MODES.get(mode)
        if not m:
            print(f"[{self.SUBSYSTEM_ICON}] ❌ 未知模式 {mode}, 可用: {list(self.MODES.keys())}")
            return ""

        task_id = self.new_task_id("fy")
        start = time.time()

        print(f"\n{'═'*56}")
        print(f"{self.SUBSYSTEM_ICON} 梵音 · {m['icon']} {m['name']}")
        print(f"   task_id: {task_id}")
        print(f"   主题: {topic[:50]} · 调性: {key_signature} · BPM: {tempo}")
        print(f"{'═'*56}")

        self.db_insert_task(task_id, mode=mode, topic=topic,
            key_signature=key_signature, tempo=tempo, status="generating")

        try:
            prompt = m["prompt"](topic, key_signature, tempo)
            print(f"  ⏳ Ollama 生成乐理内容中...")
            draft = self.ollama_generate(prompt, max_tokens=1500)
            duration = int(time.time() - start)

            # 和弦 / 简谱提取
            import re
            chords = re.findall(r'([A-G][mjd]?7?(?:sus|add)?[0-9]?)', draft)
            notes = self._extract_notes(draft)

            # 生成 WAV
            wav_path = self.artifact_path / f"{task_id}.wav"
            if notes and len(notes) > 1:
                self._make_multi_tone_wav(wav_path, notes, note_duration=60.0 / tempo)
            else:
                self._make_sine_wav(wav_path, duration_sec=5.0)

            # 保存 Markdown
            md_path = self.artifact_path / f"{task_id}_score.md"
            md_path.write_text(
                f"# 梵音 · {m['icon']} {m['name']}\n\n"
                f"> 主题: {topic}\n> 调性: {key_signature}\n> BPM: {tempo}\n"
                f"> 和弦: {', '.join(chords[:8])}\n> 耗时: {duration}s\n\n"
                f"## AI 生成内容\n\n{draft}\n", encoding="utf-8")

            self.db_update_task(task_id,
                chord_progression=", ".join(chords[:8]) if chords else None,
                melody_score=",".join([str(n) for n in notes]),
                final_text=draft,
                artifact_path=str(wav_path),
                status="done", duration_sec=duration,
                done_at=datetime.now().isoformat())

            print(f"  ✅ 完成: {duration}s")
            print(f"  🎵 WAV: {wav_path}")
            print(f"  📝 乐谱: {md_path}")

        except Exception as e:
            self.db_update_task(task_id, status="failed", done_at=datetime.now().isoformat())
            print(f"  💥 失败: {e}")
            raise

        return task_id


def _SELF_TEST():
    print("\n" + "=" * 56)
    print("🎵 梵音 (FANYIN) — 自检测")
    print("=" * 56)
    try:
        e = FanyinEngine()
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
    ap = argparse.ArgumentParser(description="🎵 梵音 · 仙女座音乐乐理子系统")
    ap.add_argument("mode", nargs="?", default="melody",
                    help="模式: melody/harmony/rhythm/theory/arrange")
    ap.add_argument("topic", nargs="?", help="主题")
    ap.add_argument("--key", "-k", default="C", help="调性")
    ap.add_argument("--tempo", "-t", type=int, default=120, help="BPM")
    ap.add_argument("--modes", action="store_true", help="列出所有模式")
    ap.add_argument("--list", "-l", type=int, const=10, nargs="?", help="最近 N 个 task")
    ap.add_argument("--self-test", action="store_true", help="自检测")
    args = ap.parse_args()

    if args.self_test:
        _SELF_TEST()
    else:
        eng = FanyinEngine()
        if args.modes:
            print("🎵 梵音 · 5 种音乐模式:")
            for k, v in eng.MODES.items():
                print(f"  {v['icon']} {k:10s} → {v['name']:10s} · {v['desc']}")
        elif args.list:
            tasks = eng.db_list_tasks(args.list)
            for t in tasks:
                print(f"  {t['task_id']}  [{t['mode']:10s}] {t['status']:8s} {str(t.get('topic',''))[:35]:35s} {t.get('duration_sec','?')}s")
        elif args.topic:
            task_id = eng.write(args.mode, args.topic, args.key, args.tempo)
            print(f"\n🎯 task_id={task_id}")
        else:
            ap.print_help()
