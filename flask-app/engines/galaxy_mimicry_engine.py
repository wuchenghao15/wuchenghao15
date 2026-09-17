"""
galaxy_mimicry_engine.py — 即梦模仿学习引擎 ("抄作业"引擎)

核心理念: 把即梦 Seedance 2.0 生成的视频的视觉+叙事+Prompt模式
提取成可复用的"作业模板库", 下次生成同类视频时自动套用.

输入: 即梦下载的视频 + 我们同期生成的 Pillow 卡片版视频
输出: mimic_profile.json (模仿配置) → 喂给 galaxy_jimeng_pipeline 使用

提取维度:
  [1] 节奏模仿      → 即梦分镜时长/转场节奏/信息密度分配
  [2] 视觉模仿      → 帧大小波动曲线/画面信息量/转场类型
  [3] Prompt 模仿   → 即梦导演口吻模板 + 运镜指令库
  [4] 叙事模仿      → 旁白节奏/钩子位置/CTA 位置

CLI:
  python3 galaxy_mimicry_engine.py learn --jimeng <path> --ours <path> --topic "斐波那契"
  python3 galaxy_mimicry_engine.py list
  python3 galaxy_mimicry_engine.py apply -t "Python装饰器" --profile fibonacci --render
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = "database/app.db"


# =====================================================================
# 1. 模仿学习配置 (从即梦视频提取后存入 DB)
# =====================================================================

MIMIC_VIDEOS_TABLE = """
CREATE TABLE IF NOT EXISTS mt_galaxy_mimic_profiles (
    profile_id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    source_platform TEXT DEFAULT 'jimeng_seedance_2',
    source_video_path TEXT,
    profile_json TEXT NOT NULL,       -- 完整模仿配置
    quality_score REAL DEFAULT 0,     -- 模仿质量分
    usage_count INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    learned_at REAL,
    updated_at REAL
)
"""


@dataclass
class MimicProfile:
    """一个即梦视频提取出来的可复用模仿配置"""
    profile_id: str
    topic: str

    # [1] 节奏模仿
    pacing: Dict  # {avg_shot_duration, transition_points_per_min, info_density_curve}

    # [2] 视觉模仿
    visual: Dict  # {frame_size_range, transition_types, motion_intensity}

    # [3] Prompt 模仿
    prompt_pattern: Dict  # {effective_pattern, anti_patterns, shot_format}

    # [4] 叙事模仿
    narrative: Dict  # {hook_position, cta_position, narration_rhythm}

    # 源信息
    source_video: str
    source_spec: Dict

    def to_json(self) -> Dict:
        return {
            "profile_id": self.profile_id,
            "topic": self.topic,
            "pacing": self.pacing,
            "visual": self.visual,
            "prompt_pattern": self.prompt_pattern,
            "narrative": self.narrative,
            "source_video": self.source_video,
            "source_spec": self.source_spec,
        }


# =====================================================================
# 2. 从即梦视频提取特征
# =====================================================================

def extract_frame_sizes(video_path: str, interval_sec: int = 2) -> List[int]:
    """抽帧并计算每帧 JPEG 大小 (间接反映画面信息量)"""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-vf", f"fps=1/{interval_sec}",
            "-frames:v", "30",
            f"{td}/frame_%03d.jpg"
        ], capture_output=True).returncode
        if out != 0:
            return []
        sizes = []
        for f in sorted(Path(td).glob("frame_*.jpg")):
            sizes.append(f.stat().st_size)
        return sizes


def extract_video_info(video_path: str) -> Dict:
    """ffprobe 视频基础信息"""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", video_path],
            capture_output=True, text=True
        ).stdout
        d = json.loads(out)
        f = d.get("format", {})
        video_stream = next((s for s in d.get("streams", []) if s["codec_type"] == "video"), {})
        return {
            "duration_s": float(f.get("duration", 0)),
            "size_mb": int(f.get("size", 0)) / 1024 / 1024,
            "resolution": f"{video_stream.get('width',0)}x{video_stream.get('height',0)}",
            "fps": float(eval(video_stream.get("r_frame_rate", "0/1"))),
            "codec": video_stream.get("codec_name", ""),
        }
    except Exception:
        return {"duration_s": 0, "size_mb": 0, "resolution": "?", "fps": 0, "codec": ""}


def compute_motion_score(frame_sizes: List[int]) -> float:
    """帧大小波动 → 画面动态程度 (0-100)"""
    if len(frame_sizes) < 3:
        return 50.0
    import statistics
    mean = statistics.mean(frame_sizes)
    if mean == 0:
        return 50.0
    cv = statistics.stdev(frame_sizes) / mean  # 变异系数
    # 归一化到 0-100, cv=0.5 → score=100
    score = min(100, cv * 200)
    return round(score, 1)


def extract_pacing_profile(info: Dict, frame_sizes: List[int]) -> Dict:
    """从视频信息推断节奏特征"""
    duration = info.get("duration_s", 40)
    # 即梦通常 6 镜头, 假设等分
    est_shots = 6
    avg_shot = duration / est_shots if est_shots else duration

    # 帧波动分段 → 节奏曲线
    segments = []
    seg_size = max(1, len(frame_sizes) // 6)
    for i in range(6):
        seg = frame_sizes[i*seg_size:(i+1)*seg_size]
        if seg:
            import statistics
            seg_mean = statistics.mean(seg)
            # 大波动 = 高信息密度, 低波动 = 稳定/过渡
            seg_cv = statistics.stdev(seg) / seg_mean if seg_mean > 0 else 0
            density = "high" if seg_cv > 0.4 else "medium" if seg_cv > 0.2 else "low"
            segments.append({"segment": i+1, "density": density, "avg_kb": round(seg_mean/1024,1)})

    return {
        "total_duration_s": round(duration, 1),
        "estimated_shots": est_shots,
        "avg_shot_duration_s": round(avg_shot, 1),
        "transition_interval_s": round(avg_shot * 0.9, 1),  # 假设过渡在 90% 位置
        "info_density_curve": segments,
    }


def extract_visual_profile(frame_sizes: List[int]) -> Dict:
    """视觉特征"""
    score = compute_motion_score(frame_sizes)
    import statistics
    if frame_sizes:
        min_kb = min(frame_sizes) / 1024
        max_kb = max(frame_sizes) / 1024
        mean_kb = statistics.mean(frame_sizes) / 1024
    else:
        min_kb = max_kb = mean_kb = 0

    return {
        "motion_intensity_score": score,  # 0=静止, 100=疯狂跳动
        "frame_size_range_kb": f"{round(min_kb)}-{round(max_kb)}",
        "avg_frame_kb": round(mean_kb, 1),
        "dynamicity_level": "HIGH" if score > 65 else "MEDIUM" if score > 35 else "LOW",
        "transition_hint": "crossfade_0.3s" if score > 50 else "straight_cut",
    }


def extract_narrative_profile(topic: str, duration_s: float) -> Dict:
    """叙事特征 (通用知识短视频模板)"""
    return {
        "hook_position_pct": 0,        # 第 1 秒就是 hook
        "hook_type": "title_big_text",
        "peak_position_pct": 20,      # 第 8 秒左右放最震撼数据
        "cta_position_pct": 88,       # 最后倒数第 5 秒 CTA
        "narration_rhythm": "fast_first_slow_middle_fast_end",
        "optimal_shot_count": 6 if duration_s > 30 else 4,
        "per_shot_duration_range": "6-10s" if duration_s > 30 else "4-6s",
    }


PROMPT_PATTERNS = {
    "effective": [
        "导演的口语化分镜指令, 包含运镜方式",
        "从[画面A][运镜方式][画面B],[运镜方式]贯穿全程",
        "完整旁白 + 6镜头数字列表 + 每镜头运镜说明",
        "请直接开始生成, 不要问我确认",
    ],
    "anti_patterns": [
        "写 JSON 结构, AI 会忽略",
        "产品需求文档格式",
        "只有画面描述没运镜指令",
    ],
    "shot_format": {
        "type": "numbered_list",
        "example": "6个镜头依次生成, 每个8-10秒:\n1. 开场大字标题...相机向前推进\n2. 水平时间线...相机平滑过渡",
    },
}


def do_mimic_learn(jimeng_video: str, ours_video: str, topic: str) -> MimicProfile:
    """完整模仿学习流程"""
    print(f"\n🧠 模仿学习: 从即梦视频提取作业模式")
    print(f"   即梦: {Path(jimeng_video).name}")
    print(f"   我们: {Path(ours_video).name if ours_video else '(无对比)'}")
    print(f"   主题: {topic}")

    # 提取即梦特征
    jimeng_info = extract_video_info(jimeng_video)
    jimeng_frames = extract_frame_sizes(jimeng_video, interval_sec=2)
    print(f"\n   即梦视频: {jimeng_info['duration_s']:.1f}s, {jimeng_info['size_mb']:.1f}MB, "
          f"{jimeng_info['resolution']}, {jimeng_info['fps']}fps")
    print(f"   帧大小: {len(jimeng_frames)} 帧, 波动 {min(jimeng_frames)//1024}-{max(jimeng_frames)//1024}KB")

    # 对比我们的 (如果有)
    if ours_video and Path(ours_video).exists():
        ours_info = extract_video_info(ours_video)
        ours_frames = extract_frame_sizes(ours_video, interval_sec=2)
        jimeng_motion = compute_motion_score(jimeng_frames)
        ours_motion = compute_motion_score(ours_frames)
        print(f"\n   📊 对比: 即梦动态分={jimeng_motion} vs 我们={ours_motion} (差 {jimeng_motion - ours_motion:.1f} 分)")

    # 组装模仿配置
    pid = f"mimic_{abs(hash(topic)) % 10000:05d}_{int(time.time()) % 1000}"
    profile = MimicProfile(
        profile_id=pid,
        topic=topic,
        pacing=extract_pacing_profile(jimeng_info, jimeng_frames),
        visual=extract_visual_profile(jimeng_frames),
        prompt_pattern=PROMPT_PATTERNS,
        narrative=extract_narrative_profile(topic, jimeng_info.get("duration_s", 40)),
        source_video=jimeng_video,
        source_spec=jimeng_info,
    )

    # 存入 DB
    c = sqlite3.connect(DB_PATH)
    c.execute(MIMIC_VIDEOS_TABLE)
    c.execute('''INSERT OR REPLACE INTO mt_galaxy_mimic_profiles
                 (profile_id, topic, source_platform, source_video_path, profile_json,
                  quality_score, usage_count, is_active, learned_at, updated_at)
                 VALUES (?, ?, ?, ?, ?, ?, 0, 1, ?, ?)''',
              (pid, topic, "jimeng_seedance_2", jimeng_video,
               json.dumps(profile.to_json(), ensure_ascii=False),
               profile.visual.get("motion_intensity_score", 0),
               time.time(), time.time()))
    c.commit()
    c.close()

    print(f"\n✅ 模仿配置落库: {pid}")
    print(f"   📈 动态强度: {profile.visual['dynamicity_level']} "
          f"(motion_score={profile.visual['motion_intensity_score']})")
    print(f"   🎬 推荐镜头数: {profile.narrative['optimal_shot_count']}")
    print(f"   🎨 推荐转场: {profile.visual['transition_hint']}")
    print(f"   📝 Prompt 模式: 导演口吻 ({profile.prompt_pattern['effective'][1][:30]}...)")
    return profile


# =====================================================================
# 3. 应用模仿配置到视频生成
# =====================================================================

def load_mimic_profile(topic: Optional[str] = None,
                        profile_id: Optional[str] = None) -> Optional[MimicProfile]:
    """从 DB 加载模仿配置"""
    c = sqlite3.connect(DB_PATH)
    c.execute(MIMIC_VIDEOS_TABLE)
    if profile_id:
        row = c.execute('SELECT profile_json FROM mt_galaxy_mimic_profiles WHERE profile_id=?',
                         (profile_id,)).fetchone()
    elif topic:
        # 先 topic 模糊匹配, 没找到就 fallback 选质量分最高的
        row = c.execute('SELECT profile_json FROM mt_galaxy_mimic_profiles WHERE topic LIKE ? ORDER BY learned_at DESC LIMIT 1',
                         (f"%{topic}%",)).fetchone()
        if not row:
            row = c.execute('SELECT profile_json FROM mt_galaxy_mimic_profiles WHERE is_active=1 ORDER BY quality_score DESC LIMIT 1').fetchone()
    else:
        row = c.execute('SELECT profile_json FROM mt_galaxy_mimic_profiles WHERE is_active=1 ORDER BY quality_score DESC LIMIT 1').fetchone()
    c.close()
    if not row:
        return None
    d = json.loads(row[0])
    return MimicProfile(
        profile_id=d["profile_id"], topic=d["topic"],
        pacing=d["pacing"], visual=d["visual"], prompt_pattern=d["prompt_pattern"],
        narrative=d["narrative"], source_video=d["source_video"], source_spec=d["source_spec"],
    )


def apply_mimic_to_spec(spec: Dict, profile: MimicProfile) -> Dict:
    """把模仿配置应用到 production_spec → 改造成"即梦风格"

    关键改动:
      1. 把分镜 duration 改成即梦推荐范围
      2. 在 script 里加入导演口吻 Prompt 模板
      3. 把 explosion_style 改成更动态的
      4. 在 meta 里标记 mimic_applied=True
    """
    spec.setdefault("meta", {})
    spec["meta"]["mimic_applied"] = True
    spec["meta"]["mimic_profile_id"] = profile.profile_id
    spec["meta"]["mimic_source"] = f"jimeng_seedance_2 ({profile.topic})"

    # 改分镜时长
    sb = spec.get("storyboard", [])
    opt_shots = profile.narrative.get("optimal_shot_count", 6)
    if sb and len(sb) != opt_shots:
        # 截断或补全到推荐镜头数
        if len(sb) > opt_shots:
            sb = sb[:opt_shots]
        else:
            while len(sb) < opt_shots:
                sb.append({"content_type": "fact_card", "title": f"补充镜头 {len(sb)+1}",
                           "points": ["知识点补充"]})

    # 每镜头时长改成推荐范围
    duration_range = profile.narrative.get("per_shot_duration_range", "6-10s")
    min_d, max_d = 6, 10
    if "-" in duration_range:
        try:
            min_d = int(duration_range.split("-")[0])
            max_d = int(duration_range.split("-")[1].replace("s", ""))
        except Exception:
            pass
    target_total = profile.pacing.get("total_duration_s", 45)
    per_shot = target_total / len(sb) if sb else 8
    per_shot = max(min_d, min(max_d, per_shot))

    for shot in sb:
        shot["duration_sec"] = round(per_shot, 1)
        # 加运镜描述 (即梦风格)
        content_type = shot.get("content_type", "")
        shot["camera_motion"] = {
            "title": "向前推进 / zoom in",
            "timeline": "平滑横向滑过",
            "comparison": "左右同时出现, 焦点在右半侧",
            "fact_card": "从上往下依次出现要点",
            "formula": "从模糊到清晰 放大呈现",
            "cta": "静止不动, 文字呼吸动画",
        }.get(content_type, "平滑淡入淡出")

    spec["storyboard"] = sb

    # 把 Prompt 改成导演口吻
    script = spec.setdefault("script", {})
    script["jimeng_style_prompt"] = build_jimeng_prompt(spec, profile)

    # 爆炸特效升级
    spec.setdefault("explosion_effects", [])
    if profile.visual.get("dynamicity_level") == "HIGH":
        spec["explosion_effects"] = [
            {"effect_type": "particle_burst", "trigger_shot": 1, "intensity": "high",
             "desc": "开场粒子爆炸, 主标题从光中显现"},
            {"effect_type": "motion_blur", "trigger_shot": 3, "intensity": "medium",
             "desc": "对比卡片切换时的动态模糊过渡"},
            {"effect_type": "glow_pulse", "trigger_shot": 6, "intensity": "low",
             "desc": "CTA 文字轻微呼吸光效"},
        ]

    # 标记视觉要求
    meta = spec["meta"]
    meta["visual_target"] = {
        "transition": profile.visual.get("transition_hint", "crossfade_0.3s"),
        "motion_level": profile.visual.get("dynamicity_level", "MEDIUM"),
        "frame_target_kb": profile.visual.get("frame_size_range_kb", "40-80"),
    }
    meta["pacing_target"] = profile.pacing
    meta["narrative_target"] = profile.narrative

    return spec


def build_jimeng_prompt(spec: Dict, profile: MimicProfile) -> str:
    """按即梦导演口吻模板, 为任意 topic 生成高质量 Prompt"""
    meta = spec.get("meta", {})
    topic = meta.get("topic", "未知主题")
    voiceover = spec.get("script", {}).get("full_text", "")
    sb = spec.get("storyboard", [])
    pal = meta.get("palette", ("255,138,76", "255,198,120"))

    shots_text = []
    for i, s in enumerate(sb, 1):
        ctype = s.get("content_type", "fact_card")
        title = s.get("title", "")
        camera = s.get("camera_motion", "平滑过渡")
        dur = s.get("duration_sec", 8)
        shots_text.append(f"{i}. {title} ({ctype}, {dur}s, {camera})")

    prompt = f"""请为抖音生成一个关于「{topic}」的竖屏短视频 (9:16, 1080p, {profile.pacing['total_duration_s']:.0f}秒)。

【完整旁白台词】(普通话男声讲述):
{voiceover}

【{len(sb)}个分镜画面】(每个镜头有明确运镜方式):
{chr(10).join(shots_text)}

【风格要求】:
- 配色: 主色 RGB({pal[0]}), 辅色 RGB({pal[1]})
- 整体风格: 现代简约知识科普风, 画面动态, 每帧都有变化
- 前 3 秒必须是 hook (大字标题 + 抓眼球画面)
- 关键旁白配白色中文字幕
- 镜头转场平滑, 有连续相机运动感

请直接开始生成, 不要问我确认。"""

    return prompt


# =====================================================================
# 4. 应用模仿配置 → 渲染视频
# =====================================================================

def mimic_render(topic: str, profile: Optional[MimicProfile] = None,
                 team_size: int = 12) -> Dict:
    """用仙女座动态团队 + 即梦模仿风格 渲染视频"""
    from engines.galaxy_dyn_team_engine import assemble_dynamic_crew, crew_to_production_spec
    from engines.galaxy_composition_engine import generate_production_spec

    print(f"\n🚀 仙女座动态团队 + 即梦模仿")
    print(f"   主题: {topic}")
    if profile:
        print(f"   模仿配置: {profile.profile_id} (动态={profile.visual['dynamicity_level']}, motion={profile.visual['motion_intensity_score']})")
    else:
        print(f"   (无模仿配置, 用默认模式)")

    # 1. 动态组装团队
    crew = assemble_dynamic_crew(topic, team_size=team_size)
    print(f"   团队: {len(crew)} 人 ({len({m.neuralhub_task for m in crew})} 职能)")

    # 2. 生成 production_spec
    spec = generate_production_spec(topic, use_ollama=True)

    # 3. 应用模仿配置 (如果有)
    if profile:
        spec = apply_mimic_to_spec(spec, profile)
        print(f"   ✅ 已应用即梦模仿 (转场={spec['meta']['visual_target']['transition']}, "
              f"镜头={spec['meta']['narrative_target']['optimal_shot_count']})")

    # 4. 渲染
    from engines.galaxy_video_renderer import render_video, build_publishing_manifest
    out_dir = Path("/tmp/galaxy_video_out")
    video = render_video(spec, out_dir=out_dir)
    manifest = build_publishing_manifest(spec, video, out_dir)

    # 5. 记录 profile 被使用了
    if profile:
        c = sqlite3.connect(DB_PATH)
        c.execute('UPDATE mt_galaxy_mimic_profiles SET usage_count=usage_count+1, updated_at=? WHERE profile_id=?',
                  (time.time(), profile.profile_id))
        c.commit()
        c.close()

    return {
        "video": video, "manifest": manifest,
        "crew_size": len(crew), "mimic_applied": profile is not None,
        "profile_id": profile.profile_id if profile else None,
    }


# =====================================================================
# 5. CLI
# =====================================================================

def main():
    parser = argparse.ArgumentParser(description="即梦模仿学习引擎")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_learn = sub.add_parser("learn", help="从即梦视频学习")
    p_learn.add_argument("--jimeng", required=True, help="即梦视频路径")
    p_learn.add_argument("--ours", default="", help="我们同期视频路径 (可选)")
    p_learn.add_argument("-t", "--topic", required=True, help="视频主题")

    p_list = sub.add_parser("list", help="列出所有模仿配置")

    p_apply = sub.add_parser("apply", help="应用模仿配置 → 渲染视频")
    p_apply.add_argument("-t", "--topic", required=True)
    p_apply.add_argument("--profile", help="指定 profile_id, 否则自动选")
    p_apply.add_argument("--team-size", type=int, default=12)

    args = parser.parse_args()

    if args.cmd == "learn":
        profile = do_mimic_learn(args.jimeng, args.ours, args.topic)
        print(f"\n📄 配置详情:\n{json.dumps(profile.to_json(), indent=2, ensure_ascii=False)}")

    elif args.cmd == "list":
        c = sqlite3.connect(DB_PATH)
        c.execute(MIMIC_VIDEOS_TABLE)
        rows = c.execute('''
            SELECT profile_id, topic, quality_score, usage_count, learned_at
            FROM mt_galaxy_mimic_profiles WHERE is_active=1
            ORDER BY quality_score DESC
        ''').fetchall()
        c.close()
        if not rows:
            print("(还没有模仿配置, 先用 learn 命令学习即梦视频)")
            return
        print(f"{'PROFILE_ID':<28} {'TOPIC':<20} {'QUALITY':>8} {'USES':>6} {'LEARNED_AT':>22}")
        print("-" * 90)
        for pid, topic, qs, uses, lat in rows:
            print(f"{pid:<28} {topic:<20} {qs:>7.1f}  {uses:>5}  {time.strftime('%m-%d %H:%M', time.localtime(lat))}")

    elif args.cmd == "apply":
        profile = load_mimic_profile(topic=args.topic if not args.profile else None,
                                      profile_id=args.profile)
        if not profile:
            print("⚠️  没找到模仿配置, 用默认模式 (先跑 learn 命令学习即梦视频)")
        result = mimic_render(args.topic, profile, team_size=args.team_size)
        v = result["video"]
        print(f"\n✅ 完成!")
        print(f"   📁 视频: {v['video_path']}")
        print(f"   ⏱️ 时长: {v['duration_sec']:.1f}s")
        print(f"   💾 大小: {v['size_mb']}MB")
        print(f"   🎨 即梦模仿: {'✅ ' + result['profile_id'] if result['mimic_applied'] else '❌ 无'}")
        # 打开
        subprocess.run(["open", v["video_path"]], capture_output=True)


if __name__ == "__main__":
    main()
