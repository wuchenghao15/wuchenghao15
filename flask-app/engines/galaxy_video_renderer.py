"""
galaxy_video_renderer.py — Agent Swarm 视频合成引擎 (v1 MVP)

输入:  production_spec JSON (from galaxy_composition_engine)
输出:  本地 mp4 文件 + publishing_manifest.json

v1 实现: 静态文字卡片 + edge-tts 旁白 + moviepy 合成
v2 实现: 爆炸动画效果 + BGM + 封面自动生成

CLI:
    python3 galaxy_video_renderer.py render --topic "秦统一六国" [--formula f_history_cute]
    python3 galaxy_video_renderer.py batch --topics "秦统一六国,量子纠缠,Python列表推导式" [--count 3]
    python3 galaxy_video_renderer.py manifest --video-dir /tmp/video_out/xxx

依赖: ffmpeg, moviepy, edge-tts, pillow, numpy
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 允许 engines 内部脚本直接运行时找到同级模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

VIDEO_W, VIDEO_H = 1080, 1920          # 竖屏短视频 (抖音/xhs/B站 标准)
FPS = 24
FONT_SIZE_TITLE = 72
FONT_SIZE_BODY = 48
FONT_SIZE_CTA = 40

# 颜色 (Element Plus 风格)
COLOR_BG_TOP = (64, 158, 255)          # 主蓝
COLOR_BG_BOTTOM = (103, 194, 58)       # 主绿
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_TEXT_DARK = (30, 30, 30)
COLOR_CARD_BG = (255, 255, 255, 230)   # 半透明白卡片

# 输出目录
OUTPUT_DIR = Path("/tmp/galaxy_video_out")


# ---------------------------------------------------------------------------
# Step 1: Pillow 渲染文字卡片 → PNG
# ---------------------------------------------------------------------------

def _find_cjk_font() -> str:
    """在 macOS 上找一个能渲染中文的字体"""
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    # fallback
    from PIL import ImageFont
    return ImageFont.load_default().getbbox.__class__.__name__  # type: ignore


def render_text_card(
    title: str,
    body: str,
    accent: str = "",
    duration_sec: float = 5.0,
    shot_idx: int = 1,
    shot_total: int = 6,
    explosion_emoji: str = "",
    bg_top: Tuple[int, int, int] = COLOR_BG_TOP,
    bg_bottom: Tuple[int, int, int] = COLOR_BG_BOTTOM,
) -> Tuple[str, float]:
    """渲染一张 1080x1920 文字卡片 → PNG 路径 + duration"""
    from PIL import Image, ImageDraw, ImageFont

    font_path = _find_cjk_font()
    font_title = ImageFont.truetype(font_path, FONT_SIZE_TITLE)
    font_body = ImageFont.truetype(font_path, FONT_SIZE_BODY)
    font_cta = ImageFont.truetype(font_path, FONT_SIZE_CTA)

    # 渐变背景
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), bg_top)
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_H):
        ratio = y / VIDEO_H
        r = int(bg_top[0] * (1 - ratio) + bg_bottom[0] * ratio)
        g = int(bg_top[1] * (1 - ratio) + bg_bottom[1] * ratio)
        b = int(bg_top[2] * (1 - ratio) + bg_bottom[2] * ratio)
        draw.line([(0, y), (VIDEO_W, y)], fill=(r, g, b))

    # 主卡片 (居中, 白色半透明圆角)
    card_w, card_h = VIDEO_W - 120, VIDEO_H - 400
    card_x, card_y = 60, 220
    card = Image.new("RGBA", (card_w, card_h), COLOR_CARD_BG)
    img.paste(card, (card_x, card_y), card)

    # 爆炸 emoji (顶部)
    if explosion_emoji:
        emoji_font = ImageFont.truetype(font_path, 140)
        emoji_bbox = draw.textbbox((0, 0), explosion_emoji, font=emoji_font)
        emoji_w = emoji_bbox[2] - emoji_bbox[0]
        draw.text(((VIDEO_W - emoji_w) // 2, card_y + 30),
                  explosion_emoji, fill=(255, 140, 0), font=emoji_font)

    # Shot 计数 (右上角)
    draw.text((VIDEO_W - 160, 30),
              f"{shot_idx}/{shot_total}",
              fill=COLOR_TEXT_WHITE, font=font_cta)

    # Title
    title_clean = title.strip()[:20]  # 截断防溢出
    title_bbox = draw.textbbox((0, 0), title_clean, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((VIDEO_W - title_w) // 2, card_y + 180),
              title_clean, fill=COLOR_TEXT_DARK, font=font_title)

    # Body (多行, 每行≤15字)
    body_lines = []
    for chunk in body.strip().split("。"):
        chunk = chunk.strip()
        if not chunk:
            continue
        while len(chunk) > 15:
            body_lines.append(chunk[:15])
            chunk = chunk[15:]
        if chunk:
            body_lines.append(chunk)
    body_lines = body_lines[:6]  # 最多 6 行
    for i, line in enumerate(body_lines):
        draw.text((card_x + 40, card_y + 340 + i * 60),
                  line, fill=COLOR_TEXT_DARK, font=font_body)

    # Accent 标签 (底部)
    if accent:
        draw.text((card_x + 40, card_y + card_h - 80),
                  f"# {accent}", fill=bg_top, font=font_cta)

    # 保存
    fd, path = tempfile.mkstemp(suffix=".png", prefix=f"card_{shot_idx}_")
    os.close(fd)
    img.save(path, "PNG")
    return path, duration_sec


# ---------------------------------------------------------------------------
# Step 2: edge-tts 生成旁白 WAV (async)
# ---------------------------------------------------------------------------

async def _tts_generate(text: str, voice: str = "zh-CN-XiaoxiaoNeural",
                        rate: str = "+0%", volume: str = "+0%") -> str:
    """edge-tts 生成 mp3 → 转 wav (moviepy 更喜欢 wav)"""
    import edge_tts
    fd_mp3, mp3_path = tempfile.mkstemp(suffix=".mp3", prefix="tts_")
    fd_wav, wav_path = tempfile.mkstemp(suffix=".wav", prefix="tts_")
    os.close(fd_mp3); os.close(fd_wav)

    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    await communicate.save(mp3_path)

    # mp3 → wav (moviepy 兼容)
    import subprocess
    subprocess.run(
        ["ffmpeg", "-y", "-i", mp3_path, "-ar", "22050", "-ac", "1", wav_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    os.remove(mp3_path)
    return wav_path


def generate_voiceover(text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> str:
    """同步包装: edge-tts mp3→wav"""
    return asyncio.run(_tts_generate(text, voice))


def get_audio_duration(wav_path: str) -> float:
    """读音频时长 (秒)"""
    from moviepy import AudioFileClip
    clip = AudioFileClip(wav_path)
    d = clip.duration
    clip.close()
    return d


# ---------------------------------------------------------------------------
# Step 3: 组装 production_spec → 视频
# ---------------------------------------------------------------------------

def _extract_voice_texts(spec: Dict) -> List[str]:
    """从 production_spec 抽出 6 段旁白 (对应 6 个 storyboard shot)"""
    script = spec.get("script", {})
    hook = script.get("hook", "")
    body = script.get("body", "")
    cta = script.get("cta", "")
    sb = spec.get("storyboard", [])

    # 6 段旁白: hook → body 分段 → CTA
    lines = []
    lines.append(hook)
    # body 按句号切成最多 4 段
    body_sents = [s.strip() for s in body.split("。") if s.strip()]
    body_chunks = []
    cur = ""
    for s in body_sents:
        if len(cur) + len(s) + 1 > 30:
            body_chunks.append(cur)
            cur = s
        else:
            cur = cur + ("。" if cur else "") + s
    if cur:
        body_chunks.append(cur)
    body_chunks = body_chunks[:4] + [""] * max(0, 4 - len(body_chunks))
    lines.extend(body_chunks)
    lines.append(cta)
    return [l for l in lines if l.strip()]


def _shot_meta(spec: Dict, idx: int) -> Dict:
    """抽第 idx 个 storyboard shot 的标题/描述/爆炸效果"""
    sb = spec.get("storyboard", [])
    if idx < len(sb):
        return sb[idx]
    return {"description": f"Shot {idx+1}", "explosion_effect": ""}


def _explosion_emoji(effect_type: str) -> str:
    """爆炸效果类型 → emoji 视觉占位"""
    mapping = {
        "cute_burst": "💥✨",
        "energy_burst": "⚡🔥",
        "code_flash": "💻✨",
        "soft_glow": "🌟💫",
        "ink_spread": "🎨🖌️",
        "data_burst": "📊⚡",
        "fractal_burst": "🔮✨",
        "emotion_burst": "❤️💫",
    }
    return mapping.get(effect_type, "✨")


def render_video(spec: Dict, out_dir: Path = OUTPUT_DIR) -> Dict:
    """production_spec → mp4 + metadata (端到端)

    Returns:
        dict with: video_path, duration_sec, size_mb, frame_count,
                   card_paths, audio_paths, publishing_manifest
    """
    from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips

    out_dir.mkdir(parents=True, exist_ok=True)
    topic = spec.get("meta", {}).get("topic", "unknown")
    swarm_id = spec.get("meta", {}).get("swarm_id",
                 f"swarm_{spec.get('meta',{}).get('content_hash','unknown')[:8]}")
    video_path = out_dir / f"{swarm_id}.mp4"

    # voiceover 建议 voice 可能不是 edge-tts 合法名 → 过滤
    VALID_EDGE_TTS_VOICES = [
        "zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural",
        "zh-CN-YunjianNeural", "zh-CN-XiaoyiNeural",
        "zh-CN-XiaohanNeural", "zh-CN-XiaomengNeural",
    ]
    raw_voice = spec.get("voiceover", {}).get("suggested_voice", "zh-CN-XiaoxiaoNeural")
    voice = raw_voice if raw_voice in VALID_EDGE_TTS_VOICES else "zh-CN-XiaoxiaoNeural"
    voice_texts = _extract_voice_texts(spec)
    sb = spec.get("storyboard", [])
    formula_id = spec.get("meta", {}).get("formula_id", "")
    explosion_style = spec.get("meta", {}).get("explosion_style", "")
    accent_tag = spec.get("tags", {}).get("activity_tags", {}).get(
        spec.get("meta", {}).get("target_platforms", ["douyin"])[0], "知识分享")

    # 颜色: 不同公式不同配色
    PALETTES = {
        "f_history_cute":   ((255, 138, 76),  (255, 198, 120)),   # 暖橙
        "f_science_burst":  ((64, 158, 255),  (159, 122, 234)),   # 蓝紫
        "f_code_demo":      ((30, 41, 59),    (100, 116, 139)),   # 深蓝灰
        "f_life_healing":   ((103, 194, 58),  (252, 194, 0)),     # 绿黄
        "f_guochao":        ((189, 22, 30),   (255, 215, 0)),     # 国潮红金
        "f_hotspot_review": ((245, 108, 108), (144, 147, 153)),   # 红灰
        "f_math_beauty":    ((220, 20, 60),   (75, 0, 130)),      # 红紫
        "f_english_drama":  ((0, 150, 136),   (121, 85, 72)),     # 青棕
    }
    palette = PALETTES.get(formula_id, (COLOR_BG_TOP, COLOR_BG_BOTTOM))
    bg_top, bg_bottom = palette

    print(f"🎬 渲染视频: topic='{topic}' swarm={swarm_id} formula={formula_id}")
    print(f"   voice={voice} explosion={explosion_style} palette={palette}")

    clips = []
    card_paths = []
    audio_paths = []
    audio_durations = []

    total_shots = min(len(voice_texts), 6)
    explosion_emoji = _explosion_emoji(explosion_style)

    # 6 段旁白 + 6 张卡片
    for i in range(total_shots):
        text = voice_texts[i]
        shot = _shot_meta(spec, i)
        shot_title = shot.get("description", f"片段 {i+1}")
        shot_desc = text[:40] if text else shot_title
        effect_type = shot.get("explosion_effect", explosion_style)
        shot_emoji = _explosion_emoji(effect_type) if effect_type != explosion_style else explosion_emoji

        # 渲染卡片 (先用 6 秒占位, 后面按音频时长改)
        png_path, _ = render_text_card(
            title=shot_title, body=shot_desc,
            accent=accent_tag[:10], duration_sec=6.0,
            shot_idx=i + 1, shot_total=total_shots,
            explosion_emoji=shot_emoji,
            bg_top=bg_top, bg_bottom=bg_bottom,
        )
        card_paths.append(png_path)

        # 生成旁白
        print(f"   🎙️  TTS shot {i+1}: '{text[:30]}...'")
        try:
            wav_path = generate_voiceover(text, voice=voice)
            dur = get_audio_duration(wav_path)
        except Exception as e:
            print(f"      ⚠️  TTS 失败: {e}, 用占位时长 5s")
            wav_path = None
            dur = 5.0

        audio_paths.append(wav_path)
        audio_durations.append(dur)

        # ImageClip + AudioFileClip
        img_clip = ImageClip(png_path).with_duration(dur)
        if wav_path:
            audio = AudioFileClip(wav_path).with_duration(dur)
            img_clip = img_clip.with_audio(audio)
        clips.append(img_clip)

    # 拼接
    print(f"   🎞️  拼接 {len(clips)} 段 clip...")
    final = concatenate_videoclips(clips, method="compose")
    print(f"   💾  写入 {video_path} ({VIDEO_W}x{VIDEO_H} @ {FPS}fps, {final.duration:.1f}s)")
    final.write_videofile(
        str(video_path), fps=FPS,
        codec="libx264", audio_codec="aac",
        preset="ultrafast",
    )

    # 清理 clip 对象
    final.close()
    for c in clips:
        try:
            c.close()
        except Exception:
            pass

    size_mb = video_path.stat().st_size / 1024 / 1024
    result = {
        "video_path": str(video_path),
        "duration_sec": final.duration,
        "size_mb": round(size_mb, 2),
        "frame_count": int(final.duration * FPS),
        "card_count": len(card_paths),
        "explosion_style": explosion_style,
        "swarm_id": swarm_id,
        "topic": topic,
    }
    print(f"   ✅ 完成: {video_path} ({size_mb:.1f}MB, {final.duration:.1f}s)")
    return result


# ---------------------------------------------------------------------------
# Step 4: Publishing Manifest (给人手动上传用)
# ---------------------------------------------------------------------------

def build_publishing_manifest(
    spec: Dict, video_info: Dict, out_dir: Path
) -> str:
    """生成 publishing_manifest.json (mp4 路径 + 平台标题 + tags + 描述)"""
    meta = spec.get("meta", {})
    script = spec.get("script", {})
    tags = spec.get("tags", {})
    platforms = meta.get("target_platforms", ["douyin", "xiaohongshu", "bilibili"])

    hook = script.get("hook", "")
    cta = script.get("cta", "")
    body_first_line = script.get("body", "").split("。")[0] if script.get("body") else ""

    platform_captions = {}
    for plat in platforms:
        plat_tags = tags.get("platform_tags", {}).get(plat, tags.get("platform_tags", {}).get("all", []))
        act_tags = tags.get("activity_tags", {}).get(plat, [])
        platform_captions[plat] = {
            "title": hook[:30],
            "description": f"{body_first_line}\n\n{cta}\n\n# " + " # ".join(plat_tags[:5]) if plat_tags else body_first_line,
            "hashtags": plat_tags + act_tags,
            "cover_suggestion": f"第 1 帧截图 ({video_info['card_count']} 张卡片中选信息最多的一张)",
            "upload_tips": [
                "横屏→竖屏 1080x1920 (已适配)",
                "封面图选第 2 张或第 3 张卡片 (信息密度最高)",
                "标题 ≤ 30 字 (已截断)",
                "标签 ≤ 5 个 (已精选)",
            ],
        }

    manifest = {
        "swarm_id": video_info["swarm_id"],
        "topic": video_info["topic"],
        "formula_id": meta.get("formula_id"),
        "video_path": video_info["video_path"],
        "video_size_mb": video_info["size_mb"],
        "video_duration_sec": video_info["duration_sec"],
        "explosion_style": video_info["explosion_style"],
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "platforms": platform_captions,
        "manual_upload_steps": [
            "1. 打开对应创作者后台",
            "2. 上传 mp4 文件",
            "3. 复制标题 + 描述 + hashtags",
            "4. 截图封面 (从 manifest 的 cover_suggestion 选帧)",
            "5. 设置发布时间 (推荐每 3 小时发 1 条, 避免限流)",
            "6. 发布后回写 publish_log.status → 'published'",
        ],
    }

    manifest_path = out_dir / f"{video_info['swarm_id']}_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"   📄 Publishing Manifest: {manifest_path}")
    return str(manifest_path)


# ---------------------------------------------------------------------------
# Step 5: 端到端流水线 (composition → 合规 → renderer → manifest)
# ---------------------------------------------------------------------------

def run_pipeline(
    topic: str,
    formula_id: Optional[str] = None,
    use_ollama: bool = False,
    out_dir: Path = OUTPUT_DIR,
) -> Dict:
    """完整流水线: topic → production_spec → 合规 → mp4 → manifest"""
    from engines.galaxy_composition_engine import (
        generate_production_spec, submit_for_compliance,
    )

    print(f"\n{'='*60}")
    print(f"🌌 MTSCOS Agent Swarm Video Pipeline")
    print(f"   topic='{topic}' formula={formula_id or 'auto'}")
    print(f"{'='*60}")

    # 1. 生成 production_spec
    spec = generate_production_spec(
        topic, formula_id=formula_id, use_ollama=use_ollama,
    )
    swarm_id = f"swarm_{spec['meta']['content_hash'][:12]}"
    spec.setdefault("meta", {})["swarm_id"] = swarm_id
    print(f"✅ production_spec: formula={spec['meta']['formula_id']} "
          f"explosion={spec['meta']['explosion_style']} "
          f"team={len(spec['meta']['team_members_detail'])}人")

    # 2. 合规
    compliance = submit_for_compliance(spec)
    print(f"✅ 合规: {compliance['overall']} "
          f"(平台: {spec['meta']['target_platforms']})")
    if compliance['overall'] == 'BLOCK':
        print(f"❌ 合规 BLOCK, 跳过渲染")
        return {"error": "compliance_block", "compliance": compliance}

    # 3. 渲染 mp4
    video_info = render_video(spec, out_dir=out_dir)

    # 4. publishing manifest
    manifest_path = build_publishing_manifest(spec, video_info, out_dir)
    video_info["manifest_path"] = manifest_path

    return video_info


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="MTSCOS Agent Swarm 视频渲染引擎 v1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 galaxy_video_renderer.py render -t "秦统一六国"
  python3 galaxy_video_renderer.py render -t "Python列表推导式" -f f_code_demo
  python3 galaxy_video_renderer.py batch --topics "秦统一六国,量子纠缠,Python列表推导式" --count 2
  python3 galaxy_video_renderer.py verify -v /tmp/galaxy_video_out/swarm_xxx.mp4
        """,
    )
    sub = parser.add_subparsers(dest="mode")

    # render
    p_render = sub.add_parser("render", help="渲染单条视频")
    p_render.add_argument("-t", "--topic", required=True, help="视频主题")
    p_render.add_argument("-f", "--formula", default=None, help="组合公式 (默认 auto)")
    p_render.add_argument("--ollama", action="store_true", help="用 Ollama 生成脚本")

    # batch
    p_batch = sub.add_parser("batch", help="批量渲染")
    p_batch.add_argument("--topics", required=True, help="逗号分隔主题列表")
    p_batch.add_argument("-c", "--count", type=int, default=1, help="每 topic 渲染几条")
    p_batch.add_argument("--ollama", action="store_true", help="用 Ollama")
    p_batch.add_argument("--interval", type=int, default=5, help="每条之间间隔秒数 (防限流)")

    # verify
    p_verify = sub.add_parser("verify", help="验证视频文件")
    p_verify.add_argument("-v", "--video", required=True, help="mp4 路径")

    args = parser.parse_args()

    if args.mode == "render":
        result = run_pipeline(args.topic, args.formula, args.ollama)
        print(f"\n🎉 完成: {result.get('video_path', 'N/A')}")
        if "error" in result:
            sys.exit(1)

    elif args.mode == "batch":
        topics = [t.strip() for t in args.topics.split(",") if t.strip()]
        print(f"📦 Batch: {len(topics)} topics × {args.count} each = {len(topics)*args.count} videos")
        all_results = []
        for topic in topics:
            for i in range(args.count):
                result = run_pipeline(topic, use_ollama=args.ollama)
                all_results.append(result)
                if args.interval > 0 and i < args.count - 1:
                    print(f"   ⏳ wait {args.interval}s...")
                    time.sleep(args.interval)
        print(f"\n🎉 Batch 完成: {len([r for r in all_results if 'video_path' in r])} videos")
        for r in all_results:
            if "video_path" in r:
                print(f"   📹 {r['video_path']} ({r['size_mb']}MB, {r['duration_sec']:.1f}s)")

    elif args.mode == "verify":
        from moviepy import VideoFileClip
        clip = VideoFileClip(args.video)
        print(f"📹 视频验证:")
        print(f"   分辨率: {clip.size}")
        print(f"   时长: {clip.duration:.2f}s")
        print(f"   FPS: {clip.fps}")
        print(f"   有音频: {clip.audio is not None}")
        print(f"   有字幕轨道: {len(getattr(clip, 'subclips', [])) > 0}")
        clip.close()
        import subprocess
        subprocess.run(["open", args.video], check=False)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
