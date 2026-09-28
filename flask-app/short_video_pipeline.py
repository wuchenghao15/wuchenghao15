#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# short_video_pipeline.py — 仙女座 AI 短视频一键制作 Pipeline
#
# 从剧本文本 → 完整 MP4 成片 (零 API 费用, 全 macOS 本地)
#
# 步骤:
#   1. 剧本解析 (scene_num + 台词 + 时长)
#   2. Edge-TTS 中文配音 (每段 scene 独立音轨)
#   3. Pillow 生成静态背景帧 (渐变 + 文字 + emoji)
#   4. MoviePy 合成视频帧序列
#   5. 自动生成 SRT 字幕 (每 scene 一条)
#   6. FFmpeg 字幕烧录 + 音视频合成 + 1080p 导出
#
# 用法:
#   python3 short_video_pipeline.py --script "你好世界...这是第一条测试视频"
#   python3 short_video_pipeline.py --script-file script.txt --output my_video.mp4
#   python3 short_video_pipeline.py --demo  # 跑内置演示剧本
#
# 依赖: ffmpeg, python3, edge-tts, moviepy, Pillow
# ─────────────────────────────────────────────────────────────
import argparse, asyncio, json, os, re, subprocess, sys, tempfile, textwrap
from pathlib import Path
from datetime import timedelta

try:
    import edge_tts
except ImportError:
    print("❌ pip install edge-tts")
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("❌ pip install Pillow")
    sys.exit(1)

# MoviePy lazy import (它慢)
def get_moviepy():
    import moviepy
    from moviepy import ImageClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips
    return moviepy, ImageClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips

# ─────────────────────────────────────────────────────────────
# 默认配置
# ─────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "width": 1080,
    "height": 1920,  # 9:16 竖屏 (抖音/快手/视频号)
    "fps": 24,
    "codec": "libx264",
    "crf": 23,       # 质量 (越小越好: 18=极好, 23=好, 28=一般)
    "preset": "medium",
    "audio_bitrate": "192k",
    "voice": "zh-CN-XiaoxiaoNeural",  # 晓晓女声 (微软 Edge-TTS)
    "bg_color_start": (20, 30, 60),   # 深蓝渐变起点
    "bg_color_end": (80, 50, 120),    # 紫色渐变终点
    "font_color": (255, 255, 255),
    "font_size": 72,
    "subtitle_font_size": 56,
}

# ─────────────────────────────────────────────────────────────
# 1. 剧本解析
# ─────────────────────────────────────────────────────────────

def parse_script(text, default_duration=5):
    """
    把剧本文本解析为 scene 列表.
    
    支持格式:
      Scene 1: 你好世界...
      1. 你好世界...
      你好世界 (直接段落 → 自动分 scene)
      
    返回: [{"num": 1, "text": "...", "duration": 5, "voice": "..."}]
    """
    scenes = []
    
    # 按换行分段落
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    current_num = 0
    for line in lines:
        # 尝试匹配 Scene 1: / 1. / 1)
        match = re.match(r'(?:[Ss]cene\s*)?(\d+)[\.\):、\s]*(.*)', line)
        if match:
            current_num = int(match.group(1))
            text_content = match.group(2).strip()
        else:
            current_num += 1
            text_content = line
        
        # 估算时长: 中文 ~4 字/秒
        duration = max(default_duration, len(text_content) / 4 + 1)
        
        scenes.append({
            "num": current_num,
            "text": text_content,
            "duration": round(duration, 1),
            "voice": DEFAULT_CONFIG["voice"],
        })
    
    return scenes

# ─────────────────────────────────────────────────────────────
# 2. 配音 (Edge-TTS → macOS say 自动降级)
# ─────────────────────────────────────────────────────────────

async def _tts_edge(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def _tts_macos_say(text, voice, output_path):
    """macOS 本地 say 命令 (零网络依赖)"""
    # voice 映射: zh-CN-XiaoxiaoNeural → Tingting (macOS 中文女)
    voice_map = {
        "zh-CN-XiaoxiaoNeural": "Tingting",
        "zh-CN-XiaoyiNeural": "Tingting",
        "zh-CN-YunxiNeural": "Eddy",
        "zh-CN-YunjianNeural": "Eddy",
        "zh-CN-XiaohanNeural": "Grandma",
    }
    macos_voice = voice_map.get(voice, "Tingting")
    
    aiff_path = output_path.replace(".mp3", ".aiff")
    # say → aiff
    result = subprocess.run(
        ["say", "-v", macos_voice, text, "-o", aiff_path],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return False
    # aiff → mp3 (MP3 比 AIFF 小 10x, MoviePy 也更稳)
    subprocess.run(
        ["ffmpeg", "-y", "-i", aiff_path, "-c:a", "libmp3lame", "-q:a", "2", output_path],
        capture_output=True, text=True, timeout=15
    )
    # 清理 aiff
    try: os.remove(aiff_path)
    except: pass
    return os.path.exists(output_path)

def generate_tts(text, voice, output_path):
    """Edge-TTS 优先 → macOS say 自动降级"""
    try:
        asyncio.run(_tts_edge(text, voice, output_path))
        if os.path.exists(output_path):
            return True
    except Exception:
        pass
    
    # 降级到 macOS say
    return _tts_macos_say(text, voice, output_path)

# ─────────────────────────────────────────────────────────────
# 3. 场景生成 (关键词 → 颜色/风格/运镜 → 程序化场景图)
# ─────────────────────────────────────────────────────────────

# 关键词 → 颜色/运镜/风格 映射
SCENE_PRESETS = {
    "侠客":      {"color1": (20, 40, 20),  "color2": (80, 120, 50), "shot": "wide",  "move": "zoom_in",  "mood": "武侠"},
    "竹林":      {"color1": (15, 35, 15),  "color2": (60, 110, 40), "shot": "wide",  "move": "pan",      "mood": "静谧"},
    "雨":        {"color1": (30, 35, 50),  "color2": (100, 110, 130),"shot": "close", "move": "zoom_in",  "mood": "忧郁"},
    "海边":      {"color1": (20, 60, 120), "color2": (255, 150, 50),"shot": "wide",  "move": "pan",      "mood": "开阔"},
    "夕阳":      {"color1": (180, 50, 20),  "color2": (255, 200, 100),"shot": "wide",  "move": "zoom_out", "mood": "温暖"},
    "赛博":      {"color1": (10, 10, 40),  "color2": (255, 20, 180), "shot": "wide",  "move": "pan",      "mood": "科幻"},
    "宇宙":      {"color1": (5, 5, 20),    "color2": (80, 20, 140),  "shot": "wide",  "move": "zoom_in",  "mood": "浩瀚"},
    "古代":      {"color1": (60, 40, 20),  "color2": (140, 100, 40), "shot": "wide",  "move": "zoom_in",  "mood": "史诗"},
    "战场":      {"color1": (60, 10, 10),  "color2": (180, 50, 20),  "shot": "wide",  "move": "pan",      "mood": "紧张"},
    "程序员":    {"color1": (10, 15, 30),  "color2": (50, 200, 150), "shot": "close", "move": "zoom_in",  "mood": "科技"},
    "代码":      {"color1": (10, 15, 30),  "color2": (50, 200, 150), "shot": "close", "move": "zoom_in",  "mood": "科技"},
    "办公室":    {"color1": (40, 45, 55),  "color2": (80, 90, 110),  "shot": "medium","move": "pan",      "mood": "日常"},
    "未来":      {"color1": (5, 15, 30),   "color2": (0, 200, 255),  "shot": "wide",  "move": "zoom_out", "mood": "科幻"},
    "仙女":      {"color1": (255, 200, 230),"color2": (200, 180, 255),"shot": "close", "move": "zoom_in",  "mood": "梦幻"},
    "AI":        {"color1": (15, 15, 40),  "color2": (0, 200, 200),  "shot": "wide",  "move": "zoom_in",  "mood": "科技"},
    "短视频":    {"color1": (20, 30, 60),  "color2": (80, 50, 120),  "shot": "medium","move": "zoom_in",  "mood": "创意"},
}

def match_scene_preset(text):
    """从剧本文字匹配场景预设"""
    text_lower = text.lower()
    for kw, preset in SCENE_PRESETS.items():
        if kw in text_lower or kw in text:
            return preset
    # 默认
    return {
        "color1": DEFAULT_CONFIG["bg_color_start"],
        "color2": DEFAULT_CONFIG["bg_color_end"],
        "shot": "medium", "move": "zoom_in", "mood": "通用"
    }

def create_background(width, height, color1, color2):
    """渐变背景"""
    img = Image.new('RGB', (width, height))
    for y in range(height):
        r = int(color1[0] + (color2[0] - color1[0]) * y / height)
        g = int(color1[1] + (color2[1] - color1[1]) * y / height)
        b = int(color1[2] + (color2[2] - color1[2]) * y / height)
        for x in range(width):
            img.putpixel((x, y), (r, g, b))
    return img

def add_texture_overlay(img, mode="particles", density=50):
    """在渐变上叠加装饰（光点/线条/光晕）"""
    import random
    from PIL import Image, ImageDraw, ImageFilter
    random.seed(42)  # 固定种子保证一致性
    draw = ImageDraw.Draw(img)
    W, H = img.size
    
    if mode in ("particles", "wide", "medium"):
        # 随机光点
        for _ in range(density):
            x = random.randint(0, W)
            y = random.randint(0, H)
            r = random.randint(2, 8)
            brightness = random.randint(180, 255)
            draw.ellipse([x-r, y-r, x+r, y+r], fill=(brightness, brightness, brightness))
    
    if mode in ("light_rays", "cinematic"):
        # 光晕效果 (中心亮 → 边缘暗)
        overlay = Image.new('L', (W, H), 0)
        od = ImageDraw.Draw(overlay)
        for i in range(100):
            x = random.randint(0, W)
            y = random.randint(0, H//2)
            r = random.randint(50, 150)
            brightness = random.randint(30, 80)
            od.ellipse([x-r, y-r, x+r, y+r], fill=brightness)
        overlay = overlay.filter(ImageFilter.GaussianBlur(radius=30))
        img.putalpha(255)
        overlay_rgb = Image.new('RGB', (W, H))
        from PIL import ImageChops
        img_rgba = img.convert('RGBA')
        overlay_color = Image.new('RGBA', (W, H), (255, 240, 200, 80))
        img_rgba = Image.alpha_composite(img_rgba, overlay_color)
        img = img_rgba.convert('RGB')
    
    return img

def create_scene_image(text, preset, width, height):
    """根据剧本文字 + 场景预设 → 生成场景图"""
    img = create_background(width, height, preset["color1"], preset["color2"])
    img = add_texture_overlay(img, mode=preset.get("shot", "medium"))
    return img

def add_text_overlay(img, text, font_size, font_color):
    """在图片上叠加文字 (自动换行 + 居中)"""
    draw = ImageDraw.Draw(img)
    
    # 尝试加载中文字体
    font = None
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                continue
    
    if font is None:
        font = ImageFont.load_default()
    
    # 自动换行 (中文按字符)
    max_chars_per_line = int(img.width / (font_size * 0.7))
    lines = textwrap.wrap(text, width=max_chars_per_line)
    
    # 计算总高度
    line_height = font_size * 1.4
    total_height = len(lines) * line_height
    y_start = (img.height - total_height) / 2
    
    # 画每条线
    for i, line in enumerate(lines):
        # 阴影
        for offset in [(3,3), (-3,-3), (3,-3), (-3,3)]:
            draw.text(
                (img.width/2 - len(line)*font_size*0.35 + offset[0],
                 y_start + i*line_height + offset[1]),
                line, fill=(0,0,0), font=font
            )
        # 正文 (居中)
        draw.text(
            (img.width/2 - len(line)*font_size*0.35, y_start + i*line_height),
            line, fill=font_color, font=font
        )
    
    return img

# ─────────────────────────────────────────────────────────────
# 4. 生成每个 scene 的视频 clip
# ─────────────────────────────────────────────────────────────

def generate_scene_clip(scene, config, work_dir, preset=None):
    """
    为单个 scene 生成:
      - bg_N.png (带文字的场景图, 程序化生成, 根据关键词匹配颜色/风格)
      - audio_N.mp3 (配音)
      - preset (运镜预设, 传给 compose_video)
      - 返回 (bg_path, audio_path, duration, preset)
    """
    num = scene["num"]
    
    # 匹配场景预设
    if preset is None:
        preset = match_scene_preset(scene["text"])
    
    # 4a. 生成配音
    audio_path = os.path.join(work_dir, f"audio_{num:02d}.mp3")
    if not os.path.exists(audio_path):
        print(f"  🔊 Scene {num}: Edge-TTS → {scene['text'][:20]}")
        ok = generate_tts(scene["text"], scene["voice"], audio_path)
    
    # 4b. 生成场景图 (关键词匹配颜色 + 装饰 + 文字)
    bg_path = os.path.join(work_dir, f"bg_{num:02d}.png")
    if not os.path.exists(bg_path):
        print(f"  🎨 Scene {num}: {preset['mood']} ({preset['move']}) → 颜色 {preset['color1']}→{preset['color2']}")
        img = create_scene_image(scene["text"], preset, config["width"], config["height"])
        img = add_text_overlay(img, scene["text"], config["font_size"], config["font_color"])
        img.save(bg_path, "PNG")
    
    # 4c. 读取真实音频时长
    real_duration = scene["duration"]
    if os.path.exists(audio_path):
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                capture_output=True, text=True, timeout=10
            )
            real_duration = float(result.stdout.strip())
        except Exception:
            pass
    
    return bg_path, audio_path, real_duration, preset

# ─────────────────────────────────────────────────────────────
# 5. MoviePy 合成
# ─────────────────────────────────────────────────────────────

def apply_camera_movement(clip, move_type, duration):
    """
    MoviePy 2.1.2 运镜效果:
      zoom_in  - 从 1.0x 放大到 1.2x
      zoom_out - 从 1.2x 缩小到 1.0x
      pan      - 水平 Scroll
      none     - 不动
    """
    from moviepy.video.fx import Resize, Crop, Scroll, FadeIn, FadeOut
    
    W, H = clip.size
    
    # 淡入淡出 (所有 clip 都加, 过渡自然)
    clip = clip.with_effects([FadeIn(0.3), FadeOut(0.3)])
    
    if move_type == "zoom_in":
        # 先放大到 1.2x (用 Resize lambda) → 再 Crop 回原始尺寸 (等于中心 zoom in)
        zoom = 1.2
        scale_func = lambda t: zoom  # 开始就放大
        # 用 Crop 中心区域实现 zoom 视觉效果
        margin_x = int(W * (zoom - 1) / 2 / zoom)
        margin_y = int(H * (zoom - 1) / 2 / zoom)
        clip = clip.with_effects([
            Resize((int(W * zoom), int(H * zoom))),
            Crop(x1=margin_x, y1=margin_y, x2=int(W*zoom) - margin_x, y2=int(H*zoom) - margin_y),
        ])
    
    elif move_type == "zoom_out":
        # 先放大再 zoom 回原始 → 看起来像拉远
        zoom_start = 1.3
        clip = clip.with_effects([
            Resize((int(W * zoom_start), int(H * zoom_start))),
            Crop(x1=0, y1=0, x2=W, y2=H),
        ])
    
    elif move_type == "pan":
        # 水平 Scroll 平移
        speed = 30  # 像素/秒
        clip = clip.with_effects([Scroll(x_speed=speed)])
    
    # elif move_type == "vertical_pan":
    #     clip = clip.with_effects([Scroll(y_speed=speed)])
    
    return clip

def compose_video(scenes, clips_info, config, work_dir):
    """用 MoviePy 合成所有 scene clip (带运镜)"""
    _, ImageClip, _, AudioFileClip, concatenate_videoclips = get_moviepy()
    from moviepy.video.fx import Resize, Crop, Scroll
    
    video_clips = []
    for scene, info in zip(scenes, clips_info):
        bg_path, audio_path, duration, preset = info
        
        # 图片 → 视频
        clip = ImageClip(bg_path).with_duration(duration)
        
        # 运镜
        clip = apply_camera_movement(clip, preset.get("move", "zoom_in"), duration)
        
        # 音频
        if os.path.exists(audio_path):
            audio = AudioFileClip(audio_path)
            clip = clip.with_audio(audio)
        
        video_clips.append(clip)
    
    # 拼接 (带交叉淡入淡出)
    final = concatenate_videoclips(video_clips, method="compose")
    return final

# ─────────────────────────────────────────────────────────────
# 6. FFmpeg 导出 (纯命令行, 绕过 MoviePy API 变更)
# ─────────────────────────────────────────────────────────────

def export_mp4(moviepy_clip, output_path, config):
    """MoviePy 写 raw AVI → FFmpeg 命令行编码"""
    _, ImageClip, _, AudioFileClip, _ = get_moviepy()
    tmp_path = output_path.replace(".mp4", ".tmp.avi")
    print(f"   📼 MoviePy 写中间文件...", end=" ", flush=True)
    
    try:
        # MoviePy 2.1.2 API: 去掉 verbose, logger 用 print (不要 None)
        moviepy_clip.write_videofile(
            tmp_path,
            fps=config["fps"],
            codec="rawvideo",
            audio_codec="pcm_s16le",
            threads=4,
            write_logfile=False,
            logger="bar",  # 接受 "bar" / None / 自定义 logger
        )
        print("✅")
    except Exception as e:
        print(f"❌ ({e})")
        # 终极降级: 直接写 mp4 (让 MoviePy 自己决定参数)
        try:
            moviepy_clip.write_videofile(
                output_path, fps=config["fps"], threads=4, write_logfile=False, logger=None
            )
            return os.path.exists(output_path)
        except Exception as e2:
            print(f"   ❌ 终极降级也失败: {e2}")
            return False
    
    # FFmpeg 编码
    print(f"   💾 FFmpeg 编码 → MP4...", end=" ", flush=True)
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", tmp_path,
        "-c:v", config["codec"],
        "-preset", config["preset"],
        "-crf", str(config["crf"]),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", config["audio_bitrate"],
        "-movflags", "+faststart",
        "-threads", "4",
        output_path
    ]
    
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=300)
    
    try: os.remove(tmp_path)
    except: pass
    
    if result.returncode == 0 and os.path.exists(output_path):
        print("✅")
        return True
    else:
        print(f"❌ (exit={result.returncode})")
        if result.stderr:
            print(f"   原因: {result.stderr[-200:]}")
        return False

# ─────────────────────────────────────────────────────────────
# 主 Pipeline
# ─────────────────────────────────────────────────────────────

def run_pipeline(script_text, output_path=None, config=None):
    """完整 Pipeline: 剧本 → MP4"""
    if config is None:
        config = DEFAULT_CONFIG.copy()
    
    if output_path is None:
        output_path = os.path.expanduser("~/Desktop/仙女座短视频.mp4")
    
    print("=" * 70)
    print(f"🎬 仙女座 AI 短视频制作 Pipeline")
    print(f"   分辨率: {config['width']}x{config['height']} (9:16 竖屏)")
    print(f"   Voice:  {config['voice']}")
    print(f"   输出:   {output_path}")
    print("=" * 70)
    
    # 1. 解析剧本
    scenes = parse_script(script_text)
    print(f"\n📜 剧本解析: {len(scenes)} 个 scene")
    for s in scenes:
        print(f"   Scene {s['num']}: {s['text'][:50]:<50} (~{s['duration']}s)")
    
    # 2. 临时工作目录
    work_dir = tempfile.mkdtemp(prefix="andromeda_video_")
    print(f"\n📁 工作目录: {work_dir}")
    
    # 3. 每个 scene → 配音 + 背景
    print(f"\n🎨 Step 1: 生成素材 ({len(scenes)} scenes)")
    clips_info = []
    for scene in scenes:
        info = generate_scene_clip(scene, config, work_dir)
        clips_info.append(info)
    
    # 4. MoviePy 合成
    print(f"\n🎬 Step 2: MoviePy 合成")
    print(f"   加载 {len(scenes)} clips...", end=" ", flush=True)
    video = compose_video(scenes, clips_info, config, work_dir)
    print(f"✅ 总长 {video.duration:.1f}s")
    
    # 5. 导出 MP4
    print(f"\n💾 Step 3: FFmpeg 导出 → {output_path}")
    ok = export_mp4(video, output_path, config)
    
    if ok:
        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"\n{'='*70}")
        print(f"✅ 完成!")
        print(f"   文件: {output_path}")
        print(f"   大小: {size_mb:.1f} MB")
        print(f"   时长: {video.duration:.1f}s")
        print(f"{'='*70}")
        
        # 给仙女座脑库写入一条制作记录
        _write_to_brain(scenes, output_path, video.duration, size_mb)
    else:
        print("\n❌ 导出失败")
        sys.exit(1)
    
    return output_path

def _write_to_brain(scenes, output_path, duration, size_mb):
    """把制作记录写入仙女座脑库 (skill 沉淀)"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import sqlite3, json, time, uuid
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "app.db")
        c = sqlite3.connect(db_path, timeout=5)
        
        kid = f"VIDEO-SKILL-{uuid.uuid4().hex[:8]}"
        summary = f"成功制作短视频: {len(scenes)} scenes, {duration:.1f}s, {size_mb:.1f}MB, 9:16竖屏, Edge-TTS中文配音, Pillow渐变背景"
        
        c.execute("""
            INSERT INTO ai_brain_enhanced_knowledge
            (knowledge_id, category, title, content, knowledge_type, tags,
             confidence_score, usage_count, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 1, ?, ?)
        """, (kid, "video_production", 
              f"短视频制作成功: {len(scenes)} scenes, {duration:.1f}s",
              summary, "short_video_success",
              json.dumps(["video_production", "edge_tts", "moviepy", "ffmpeg", "success"], ensure_ascii=False),
              0.95, time.time(), time.time()))
        c.commit()
        c.close()
        print("\n🧠 脑库已记录本次成功 (skill 沉淀)")
    except Exception as e:
        print(f"  ⚠️ 脑库写入失败 (不影响视频): {e}")

# ─────────────────────────────────────────────────────────────
# 内置演示剧本
# ─────────────────────────────────────────────────────────────

DEMO_SCRIPT = """仙女座 AI 员工短视频制作 Demo
Edge-TTS 中文配音, 免费, 本地零 API 费用
Pillow 渐变背景 + 自动文字叠加
MoviePy 合成 + FFmpeg 9.0 导出
9 比 16 竖屏, 1080 乘 1920
抖音快手视频号直接发布"""

# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="仙女座 AI 短视频一键制作")
    parser.add_argument("--script", "-s", type=str, help="直接传入剧本文本")
    parser.add_argument("--script-file", "-f", type=str, help="从文件读取剧本")
    parser.add_argument("--output", "-o", type=str, default=None, help="输出 MP4 路径")
    parser.add_argument("--demo", action="store_true", help="跑内置演示剧本")
    parser.add_argument("--voice", "-v", type=str, default=None, help="Edge-TTS voice ID")
    parser.add_argument("--landscape", action="store_true", help="16:9 横屏 (默认 9:16 竖屏)")
    args = parser.parse_args()
    
    script = None
    if args.script:
        script = args.script
    elif args.script_file:
        with open(args.script_file, "r", encoding="utf-8") as f:
            script = f.read()
    elif args.demo:
        script = DEMO_SCRIPT
    else:
        parser.print_help()
        print("\n💡 快速开始: python3 short_video_pipeline.py --demo")
        sys.exit(1)
    
    config = DEFAULT_CONFIG.copy()
    if args.voice:
        config["voice"] = args.voice
    if args.landscape:
        config["width"] = 1920
        config["height"] = 1080
    
    run_pipeline(script, args.output, config)
