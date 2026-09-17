"""
galaxy_jimeng_pipeline.py — 仙女座 × 即梦 Jimeng 原生流水线 (v1)

核心理念:
  整条链交给即梦 — 即梦 seedance 视频模型内部自带文案→分镜→视频生成能力,
  不用 Ollama 写文案 + moviepy 拼视频。我们只需要给即梦一个好 prompt。

Pipeline:
  topic → JimengPromptBuilder (构造好 prompt, 含风格/画面/时长)
       → dreamina text2video --poll 300 (即梦自己搞定一切)
       → 合规 (C1~C7)
       → publish_to_douyin / publish_to_bilibili

降级:
  dreamina CLI 不可用 → Ollama copywriting + moviepy renderer (旧路)

依赖:
  dreamina CLI (curl -s https://jimeng.jianying.com/cli | bash)
  即梦 OAuth 登录 (dreamina login)
  ffmpeg (pip 已装, 用于 probe)
  抖音/B站 cookie (social-auto-upload, ~/mtscos_sau)

CLI:
  python3 galaxy_jimeng_pipeline.py generate -t "秦统一六国" --prompt-style cute_history
  python3 galaxy_jimeng_pipeline.py batch -t "秦统一六国,量子纠缠" --count 2
  python3 galaxy_jimeng_pipeline.py login
  python3 galaxy_jimeng_pipeline.py check
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 允许直接运行时找同级模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# TRAE 沙箱允许写的目录 — dreamina 把 log+登录态写到这里
# dreamina 登录态由用户在真实终端登录时保存在真实 HOME (~/Library 或 ~/.dreamina_cli)
# 我们在 TRAE 沙箱里只读不写 —— _dreamina_env() 传递原始环境变量, 不改 HOME
# 仅当 TRAE 沙箱真的拦截 dreamina 写日志时才 fallback 到临时 HOME
TRAE_SAFE_HOME = "/tmp/mtscos_dreamina_real"

def _dreamina_env() -> Dict[str, str]:
    """返回调用 dreamina 的环境变量 (保持真实 HOME, 不重定向)

    原因: dreamina 登录态存在真实 HOME 下, 重定向 HOME 会导致找不到登录态.
    经验证, TRAE 沙箱不拦截 dreamina 读真实 HOME 的登录态 (只拦截写 .dreamina_cli/logs/).
    我们只调 user_credit / text2video (都是读 + API 调用), 不写本地日志.
    """
    env = os.environ.copy()
    # 不改 HOME — 保持真实 HOME, dreamina 才能找到登录态
    return env


# ============================================================================
# Step 1: PromptBuilder — 给即梦写专业级 prompt (即梦的文案模型比 Ollama 强)
# ============================================================================

PROMPT_TEMPLATES = {
    # (seedance 风格增强词 + 画面指令 + 叙事结构)
    "cute_history": (
        "可爱卡通风格，Q版角色，色彩明亮，适合短视频平台。"
        "故事结构: 引入(让你惊讶的历史事实)→背景(当时世界啥样)→过程(关键人物做了啥)→结局(改变了什么)"
        "每个画面自然流畅，角色动作可爱。"
    ),
    "explosive_science": (
        "炫酷科技风格，能量爆炸特效，赛博朋克调色。"
        "故事结构: 现象提出→原理拆解(用比喻让抽象变具象)→实验室/自然展示→日常应用"
        "镜头切换快，关键原理处有爆炸能量特效。"
    ),
    "code_demo": (
        "现代科技感UI界面风格，代码编辑器画面，深色主题。"
        "故事结构: 痛点问题→一行代码展示→逐行拆解→运行结果→延伸技巧"
        "画面是真实IDE界面截图风格，代码高亮清晰。"
    ),
    "healing_life": (
        "温暖治愈系风格，柔和光影，生活化场景。"
        "故事结构: 日常小烦恼→一个小妙招→前后对比→生活感悟"
        "画面温暖，配色柔和。"
    ),
    "guochao": (
        "国潮国风风格，水墨+现代设计融合，金红配色。"
        "故事结构: 传统文化介绍→现代演绎→跨界融合→文化自信"
        "画面有传统元素(山水/书法/戏曲)但构图现代。"
    ),
    "hotspot": (
        "新闻快报风格，简洁字幕条，时间线画面。"
        "故事结构: 事件爆点→时间线梳理→各方反应→深度解读"
        "画面有新闻感但不失精致。"
    ),
    "math_beauty": (
        "数学之美可视化风格，公式动画，几何图形运动。"
        "故事结构: 一个美丽的公式→几何意义→生活中的应用→为什么重要"
        "画面有公式动画、几何图形旋转、曲线生成。"
    ),
    "chibi_cute": (
        "超级Q版风格，大眼睛圆脸角色，糖果色。"
        "所有画面都是chibi比例角色，夸张可爱表情。"
    ),
}

JIMENG_VIDEO_PARAMS = {
    "seedance2.0fast": {
        "ratio": "9:16",
        "resolution": "720p",
        "duration_default": 5,      # 秒 (4-15)
        "duration_max": 15,
    },
    "seedance2.0": {
        "ratio": "9:16",
        "resolution": "720p",
        "duration_default": 5,
        "duration_max": 15,
    },
    "seedance2.5": {
        "ratio": "9:16",
        "resolution": "720p",
        "duration_default": 10,
        "duration_max": 30,
    },
}


def build_jimeng_prompt(
    topic: str,
    prompt_style: str = "cute_history",
    duration_sec: int = 5,
    explosion_keyword: str = "",
) -> Tuple[str, Dict]:
    """构造即梦 text2video 的专业 prompt + 参数

    Returns:
        (prompt_str, video_params)
    """
    style_desc = PROMPT_TEMPLATES.get(prompt_style, PROMPT_TEMPLATES["cute_history"])

    # 爆炸/能量/代码/情感 关键词 → 视觉指令
    visual_keywords = {
        "cute_burst": "画面中有可爱卡通角色+小型爆炸特效,能量闪击效果",
        "energy_burst": "能量爆炸特效,蓝色紫色电光,粒子扩散",
        "code_flash": "代码编辑器画面,代码行闪烁高亮,绿色荧光效果",
        "soft_glow": "柔和光晕,温暖光线,缓缓扩散的光粒",
        "ink_spread": "水墨扩散,颜料在水中舒展,笔触流动",
        "data_burst": "数据流动特效,图表可视化,数字雨,几何图形爆炸",
        "fractal_burst": "分形图案生长,递归几何,魔法阵旋转",
        "emotion_burst": "心形粒子,情感符号爆炸,温暖光粒包围",
    }
    visual_cmd = visual_keywords.get(explosion_keyword, "")

    prompt = f"""请生成一个关于"{topic}"的短视频。

画面风格: {style_desc}
视觉特效: {visual_cmd}
时长: {duration_sec}秒
比例: 9:16竖屏

画面要求:
1. 视频要有完整叙事,开头抓眼球,中间讲清楚,结尾有余韵
2. 画面流畅,转场自然
3. 关键信息处有视觉强调特效
4. 适合抖音/小红书/B站发布

内容主题: {topic}"""

    params = {
        "model_version": "seedance2.0fast",
        "ratio": "9:16",
        "video_resolution": "720p",
        "duration": min(duration_sec, 15),
    }
    return prompt, params


# ============================================================================
# Step 2: 调即梦 CLI — text2video + text2image
# ============================================================================

def _check_dreamina_available() -> Tuple[bool, str]:
    """检查 dreamina CLI 是否可用 + 是否已登录"""
    if not shutil.which("dreamina"):
        return False, "dreamina CLI 未安装 (运行: curl -s https://jimeng.jianying.com/cli | bash)"
    # 尝试 user_credit
    try:
        r = subprocess.run(
            ["dreamina", "user_credit"],
            capture_output=True, text=True, timeout=10,
            env=_dreamina_env(),
        )
        if r.returncode == 0:
            return True, "ready"
        if "未检测到有效登录" in r.stdout + r.stderr:
            return False, "需要登录 (运行: dreamina login)"
        return False, f"error: {(r.stdout + r.stderr)[:200]}"
    except Exception as e:
        return False, f"exception: {e}"


def jimeng_text2video(
    prompt: str,
    model_version: str = "seedance2.0fast",
    duration: int = 5,
    ratio: str = "9:16",
    resolution: str = "720p",
    download_dir: str = "/tmp/galaxy_video_out",
    poll: int = 300,
) -> Dict:
    """调即梦 text2video (自动 poll + 下载)

    Returns:
        {
            "success": True/False,
            "video_path": "...mp4" / None,
            "submit_id": "...",
            "duration_sec": float,
            "size_mb": float,
            "error": str / None,
            "latency_ms": int,
        }
    """
    t0 = time.time()
    os.makedirs(download_dir, exist_ok=True)

    cmd = [
        "dreamina", "text2video",
        "--prompt", prompt,
        "--duration", str(duration),
        "--ratio", ratio,
        "--video_resolution", resolution,
        "--model_version", model_version,
        "--poll", str(poll),
        # ⚠️ 即梦 CLI 没有 --download_dir —— 提交后用 query_result 下载
    ]

    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=poll + 60,
            env=_dreamina_env(),
        )
        combined = r.stdout + "\n" + r.stderr

        # 解析 submit_id
        import re
        submit_match = re.search(r"submit_id[=:]\s*([a-zA-Z0-9\-]+)", combined)
        submit_id = submit_match.group(1) if submit_match else None

        # text2video --poll 可能不自动下载 —— 如果拿到 submit_id, 用 query_result 下载
        video_path = None
        if submit_id:
            try:
                qr = subprocess.run(
                    ["dreamina", "query_result",
                     "--submit_id", submit_id,
                     "--download_dir", download_dir],
                    capture_output=True, text=True, timeout=60,
                    env=_dreamina_env(),
                )
                # 从 query_result 输出里找文件路径
                for line in (qr.stdout + "\n" + qr.stderr).splitlines():
                    line = line.strip()
                    if line.startswith("/") and ".mp4" in line.lower():
                        m = re.search(r"(/\S+\.mp4)", line, re.IGNORECASE)
                        if m:
                            video_path = m.group(1)
                            break
            except Exception:
                pass

        # 如果 query_result 也没下载, 再从 text2video 输出里找
        if not video_path:
            for line in combined.splitlines():
                line = line.strip()
                if line.startswith("/") and ".mp4" in line.lower():
                    m = re.search(r"(/\S+\.mp4)", line, re.IGNORECASE)
                    if m:
                        video_path = m.group(1)
                        break

        # 兜底: download_dir 里最新的 mp4
        if not video_path:
            mtime = 0
            for f in os.listdir(download_dir):
                fp = os.path.join(download_dir, f)
                if f.endswith(".mp4") and os.path.getmtime(fp) > mtime:
                    mtime = os.path.getmtime(fp)
                    video_path = fp

        # 验证文件 + ffprobe
        dur = float(duration)
        size_mb = 0.0
        if video_path and os.path.exists(video_path):
            try:
                probe = subprocess.run(
                    ["ffprobe", "-v", "quiet",
                     "-show_entries", "format=duration,size",
                     "-of", "json", video_path],
                    capture_output=True, text=True, timeout=10,
                )
                info = json.loads(probe.stdout)
                dur = float(info.get("format", {}).get("duration", duration))
                size_mb = float(info.get("format", {}).get("size", 0)) / 1024 / 1024
            except Exception:
                pass

        latency_ms = int((time.time() - t0) * 1000)

        if r.returncode == 0 and video_path and os.path.exists(video_path):
            return {
                "success": True,
                "video_path": video_path,
                "submit_id": submit_id,
                "duration_sec": dur,
                "size_mb": round(size_mb, 2),
                "model_version": model_version,
                "latency_ms": latency_ms,
            }
        else:
            return {
                "success": False,
                "video_path": None,
                "submit_id": submit_id,
                "duration_sec": dur,
                "size_mb": 0.0,
                "model_version": model_version,
                "error": (r.stderr or r.stdout)[-500:] or f"returncode={r.returncode}",
                "latency_ms": latency_ms,
            }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"超时 ({poll}s)",
                "latency_ms": int((time.time()-t0)*1000)}
    except Exception as e:
        return {"success": False, "error": str(e)[:200],
                "latency_ms": int((time.time()-t0)*1000)}


def jimeng_text2image(
    prompt: str,
    num_images: int = 4,
    model_version: str = "4.7",
    ratio: str = "1:1",
    resolution_type: str = "2k",
    download_dir: str = "/tmp/galaxy_art_out",
    poll: int = 60,
) -> Dict:
    """调即梦 text2image (原画/关键帧)"""
    t0 = time.time()
    os.makedirs(download_dir, exist_ok=True)

    cmd = [
        "dreamina", "text2image",
        "--prompt", prompt,
        "--generate_num", str(num_images),
        "--ratio", ratio,
        "--resolution_type", resolution_type,
        "--model_version", model_version,
        "--poll", str(poll),
        # ⚠️ 即梦 CLI 没有 --download_dir —— 提交后 query_result 下载
    ]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                          timeout=poll + 30, env=_dreamina_env())
        images = []
        import re
        for line in (r.stdout + "\n" + r.stderr).splitlines():
            line = line.strip()
            if line.startswith("/") and any(ext in line.lower() for ext in (".png", ".jpg")):
                m = re.search(r"(/\S+\.(?:png|jpg))", line, re.IGNORECASE)
                if m: images.append(m.group(1))

        if not images and os.path.isdir(download_dir):
            for f in sorted(os.listdir(download_dir)):
                if f.endswith((".png", ".jpg")):
                    images.append(os.path.join(download_dir, f))

        return {
            "success": r.returncode == 0 and len(images) > 0,
            "images": images,
            "error": (r.stderr or "")[:300] if r.returncode != 0 else None,
            "latency_ms": int((time.time()-t0)*1000),
        }
    except Exception as e:
        return {"success": False, "images": [], "error": str(e)[:200],
                "latency_ms": int((time.time()-t0)*1000)}


# ============================================================================
# Step 3: 完整 Pipeline — topic → 即梦视频 → 合规 → 发布
# ============================================================================

def run_jimeng_pipeline(
    topic: str,
    prompt_style: str = "cute_history",
    formula_id: Optional[str] = None,
    duration_sec: int = 5,
    platforms: Optional[List[str]] = None,
    use_ollama: bool = True,
) -> Dict:
    """完整即梦优先流水线 (仙女座预处理 → 即梦渲染)

    两阶段:
      Phase A - 仙女座本地 (零token):
        1. Agent Swarm 自动选组合公式 (8种)
        2. Ollama qwen2.5 写文案 (hook+body+CTA, 8种风格)
        3. C1~C7 合规 (DB 72词动态词库)
        4. production_spec 落库

      Phase B - 即梦渲染:
        5. 从 production_spec 抽画面描述 → 拼即梦 prompt
        6. dreamina text2video (seedance 2.0fast)
        7. 发布准备 (多平台 manifest)
    """
    print(f"\n{'='*60}")
    print(f"🌌 仙女座 × 即梦 Jimeng 原生流水线")
    print(f"   topic='{topic}' use_ollama={use_ollama}")
    print(f"{'='*60}")

    # ============== Phase A: 仙女座本地预处理 ==============
    print(f"\n📋 Phase A: 仙女座本地预处理 (零token)")

    # A1. 自动选组合公式
    formula_map = {
        "cute_history": "f_history_cute",
        "explosive_science": "f_science_burst",
        "code_demo": "f_code_demo",
        "healing_life": "f_life_healing",
        "guochao": "f_guochao",
        "hotspot": "f_hotspot_review",
        "math_beauty": "f_math_beauty",
    }
    if not formula_id:
        formula_id = formula_map.get(prompt_style, "f_history_cute")
    print(f"   ✅ 公式: {formula_id}")

    # A2. 即梦可用性检查
    available, msg = _check_dreamina_available()
    print(f"   即梦 CLI: {'✅ 就绪' if available else f'❌ {msg}'}")

    # A3. Ollama 写文案 + 生成 production_spec
    from engines.galaxy_composition_engine import generate_production_spec
    spec = generate_production_spec(
        topic, formula_id=formula_id, use_ollama=use_ollama,
    )
    swarm_id = f"swarm_{spec['meta']['content_hash'][:12]}"
    spec.setdefault("meta", {})["swarm_id"] = swarm_id
    print(f"   ✅ production_spec: swarm={swarm_id} formula={spec['meta']['formula_id']}")
    print(f"      team={len(spec['meta'].get('team_members_detail', []))}人")

    # A4. 合规审查 (submit_for_compliance 在 composition_engine)
    from engines.galaxy_composition_engine import submit_for_compliance
    compliance = submit_for_compliance(spec)
    print(f"   ✅ 合规: {compliance['overall']}")

    # ============== Phase B: 即梦渲染 ==============
    print(f"\n🎬 Phase B: 即梦 Jimeng 渲染")

    if not available:
        print(f"   → 即梦不可用, 降级到 moviepy renderer")
        fallback = _fallback_from_spec(spec)
        return {
            "source": "fallback",
            "swarm_id": swarm_id,
            "compliance": compliance,
            **fallback,
        }

    # B1. 从 production_spec 抽取文案 + 画面描述 → 拼即梦 prompt
    script = spec.get("script", {})
    full_text = script.get("full_text", "")
    sb = spec.get("storyboard", [])
    explosion_style = spec.get("meta", {}).get("explosion_style", "")

    # 即梦 prompt: 把仙女座写好的完整文案 + 画面指令喂给即梦
    formula_visual_map = {
        "f_history_cute": ("可爱卡通风格,Q版角色,色彩明亮,适合短视频平台", "💥✨ cute bursts of light"),
        "f_science_burst": ("炫酷科技风格,能量爆炸特效,赛博朋克调色", "⚡🔥 blue-purple energy explosions"),
        "f_code_demo": ("现代科技感UI界面风格,代码编辑器画面,深色主题", "💻✨ code highlight flashes"),
        "f_life_healing": ("温暖治愈系风格,柔和光影,生活化场景", "🌟💫 soft glowing particles"),
        "f_guochao": ("国潮国风风格,水墨+现代设计融合,金红配色", "🎨🖌️ ink spread effects"),
        "f_hotspot_review": ("新闻快报风格,简洁字幕条,时间线画面", "📊⚡ data burst animations"),
        "f_math_beauty": ("数学之美可视化风格,公式动画,几何图形运动", "🔮✨ fractal pattern growth"),
        "f_english_drama": ("英文情景风格,人物对话场景,青春校园", "❤️💫 warm emotional glow"),
    }
    visual_desc, effect_desc = formula_visual_map.get(
        formula_id, ("现代简洁风格", "✨ soft glow")
    )

    # 构建即梦 prompt — 把仙女座写好的完整文案放前面, 告诉即梦这就是叙事
    jimeng_prompt = f"""请生成一个适合抖音/小红书/B站发布的短视频。

【内容文案】(请用画面表现以下叙事):
{full_text}

【画面要求】
- 风格: {visual_desc}
- 视觉特效: {effect_desc}
- 时长: {duration_sec}秒, 比例: 9:16竖屏
- 视频要有完整叙事: 开头抓眼球, 中间讲清楚, 结尾有余韵
- 画面流畅, 转场自然
- 关键信息处有视觉强调特效
- 整体色调明亮, 色彩饱和, 适合短视频平台传播

【故事分镜参考】
{chr(10).join(f'  Shot {i+1}: {s.get("description", "")}' for i, s in enumerate(sb[:6]))}"""

    print(f"   prompt: {jimeng_prompt[:100]}...")

    # B2. 调即梦 text2video
    video_result = jimeng_text2video(
        prompt=jimeng_prompt,
        model_version="seedance2.0fast",
        duration=min(duration_sec, 15),
        ratio="9:16",
        resolution="720p",
        poll=300,
    )

    if video_result["success"]:
        print(f"   ✅ 即梦视频: {video_result['video_path']}")
        print(f"      {video_result['duration_sec']:.1f}s, {video_result['size_mb']:.1f}MB, {video_result['latency_ms']/1000:.0f}s")
    else:
        print(f"   ❌ 即梦失败: {video_result.get('error', 'unknown')[:100]}")
        print(f"   → 降级到 moviepy")
        return {
            "source": "jimeng_failed_fallback",
            "swarm_id": swarm_id,
            "compliance": compliance,
            "jimeng_error": video_result.get("error"),
            **_fallback_from_spec(spec),
        }

    # B3. 可选: 即梦文生图 (关键帧/原画)
    art_prompt = sb[0].get("description", "") if sb else topic
    art_result = jimeng_text2image(
        prompt=f"{art_prompt}, {visual_desc}",
        num_images=4, model_version="4.7", ratio="9:16",
    )
    if art_result["success"]:
        print(f"   ✅ 即梦原画: {len(art_result['images'])} 张关键帧")
    else:
        print(f"   ⚠️ 原画跳过: {art_result.get('error', 'unknown')[:60]}")

    # B4. 多平台 publishing manifest
    platforms = platforms or spec.get("meta", {}).get("target_platforms", ["douyin", "bilibili"])
    from engines.galaxy_video_renderer import build_publishing_manifest
    video_info = {
        "video_path": video_result["video_path"],
        "swarm_id": swarm_id,
        "topic": topic,
        "explosion_style": explosion_style,
        "duration_sec": video_result["duration_sec"],
        "size_mb": video_result["size_mb"],
    }
    manifest_path = build_publishing_manifest(
        spec, video_info, Path(video_result["video_path"]).parent,
    )
    print(f"   ✅ Publishing Manifest: {manifest_path}")

    return {
        "source": "jimeng",
        "swarm_id": swarm_id,
        "compliance": compliance,
        "formula_id": formula_id,
        "video": video_result,
        "art": art_result if art_result["success"] else None,
        "prompt": jimeng_prompt,
        "production_spec": spec,
        "manifest_path": manifest_path,
    }


def _fallback_from_spec(spec: Dict) -> Dict:
    """用已生成的 production_spec 降级到 moviepy"""
    from engines.galaxy_video_renderer import render_video, build_publishing_manifest
    swarm_id = spec.get("meta", {}).get("swarm_id", "swarm_fallback")
    video_info = render_video(spec)
    video_info["swarm_id"] = swarm_id
    manifest_path = build_publishing_manifest(
        spec, video_info, Path(video_info["video_path"]).parent,
    )
    return {
        "source": "fallback_moviepy",
        "video": video_info,
        "manifest_path": manifest_path,
    }


# ============================================================================
# Step 4: 发布对接 social-auto-upload
# ============================================================================

def publish_to_platform(
    video_path: str,
    platform: str,
    title: str,
    description: str,
    tags: List[str],
    sau_dir: str = os.path.expanduser("~/mtscos_sau"),
) -> Dict:
    """调 social-auto-upload 发布到抖音/B站

    依赖: sau_dir 下有 cookies/<platform>_galaxy_acc_xxx.json
    """
    sau_cli = os.path.join(sau_dir, "sau_cli.py")
    if not os.path.exists(sau_cli):
        return {"success": False, "error": f"sau_cli.py not found at {sau_cli}"}

    cmd_map = {
        "douyin": [
            sys.executable, sau_cli, "douyin", "upload-video",
            "--account", "galaxy_acc_1789667686",
            "--file", video_path,
            "--title", title[:30],
            "--desc", description[:300],
            "--tags", ",".join(tags[:5]),
        ],
        "bilibili": [
            sys.executable, sau_cli, "bilibili", "upload-video",
            "--account", "galaxy_acc_1789667686",
            "--file", video_path,
            "--title", title[:80],
            "--desc", description[:1000],
            "--tags", ",".join(tags[:5]),
        ],
        "xiaohongshu": [
            sys.executable, sau_cli, "xiaohongshu", "upload-video",
            "--account", "galaxy_acc_1789667686",
            "--file", video_path,
            "--title", title[:20],
            "--desc", description[:1000],
            "--tags", ",".join(tags[:5]),
        ],
    }
    if platform not in cmd_map:
        return {"success": False, "error": f"未知平台: {platform}"}

    try:
        r = subprocess.run(
            cmd_map[platform], capture_output=True, text=True,
            timeout=120,
            env={**os.environ, "HOME": os.path.expanduser("~")},
        )
        success = r.returncode == 0 and "成功" in (r.stdout + r.stderr)
        return {
            "success": success,
            "returncode": r.returncode,
            "output": (r.stdout + "\n" + r.stderr)[-500:],
        }
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="仙女座 × 即梦 Jimeng 原生流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检查即梦状态
  python3 galaxy_jimeng_pipeline.py check

  # 生成 (即梦不可用时自动降级)
  python3 galaxy_jimeng_pipeline.py generate -t "秦统一六国" --style cute_history

  # 批量
  python3 galaxy_jimeng_pipeline.py batch -t "秦统一六国,量子纠缠,Python列表推导式" --count 1

  # 发布
  python3 galaxy_jimeng_pipeline.py publish -v /tmp/xxx.mp4 -p douyin --title "测试标题"
        """,
    )
    sub = parser.add_subparsers(dest="mode")

    # check
    sub.add_parser("check", help="检查即梦 CLI 登录状态")

    # generate
    p_gen = sub.add_parser("generate", help="单条生成")
    p_gen.add_argument("-t", "--topic", required=True)
    p_gen.add_argument("-s", "--style", default="cute_history",
                       choices=list(PROMPT_TEMPLATES.keys()))
    p_gen.add_argument("--duration", type=int, default=5)
    p_gen.add_argument("-f", "--formula", default=None)

    # batch
    p_batch = sub.add_parser("batch", help="批量生成")
    p_batch.add_argument("-t", "--topics", required=True, help="逗号分隔")
    p_batch.add_argument("--style", default="cute_history")
    p_batch.add_argument("--count", type=int, default=1)
    p_batch.add_argument("--interval", type=int, default=10)

    # publish
    p_pub = sub.add_parser("publish", help="发布到平台")
    p_pub.add_argument("-v", "--video", required=True)
    p_pub.add_argument("-p", "--platform", required=True,
                       choices=["douyin", "bilibili", "xiaohongshu"])
    p_pub.add_argument("--title", required=True)
    p_pub.add_argument("--desc", default="")
    p_pub.add_argument("--tags", default="")

    args = parser.parse_args()

    if args.mode == "check":
        ok, msg = _check_dreamina_available()
        print(f"{'✅' if ok else '❌'} {msg}")
        print(f"   HOME 重定向: {TRAE_SAFE_HOME}")
        if ok:
            print(f"   即梦可用, video_gen + original_art 已就绪")

    elif args.mode == "generate":
        result = run_jimeng_pipeline(
            topic=args.topic, prompt_style=args.style,
            formula_id=args.formula, duration_sec=args.duration,
        )
        if result["source"] == "jimeng" and result.get("jimeng_result", {}).get("success"):
            r = result["jimeng_result"]
            print(f"\n🎉 完成: {r['video_path']}")
            print(f"   {r['duration_sec']:.1f}s, {r['size_mb']:.1f}MB, {r['latency_ms']/1000:.0f}s")
        else:
            print(f"\n⚠️ 结果: {result}")

    elif args.mode == "batch":
        topics = [t.strip() for t in args.topics.split(",") if t.strip()]
        print(f"📦 Batch: {len(topics)} topics × {args.count} each = {len(topics)*args.count} videos")
        for topic in topics:
            for i in range(args.count):
                try:
                    run_jimeng_pipeline(topic=topic, prompt_style=args.style)
                except Exception as e:
                    print(f"   ❌ {topic}: {e}")
                if args.interval > 0:
                    print(f"   ⏳ wait {args.interval}s...")
                    time.sleep(args.interval)

    elif args.mode == "publish":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        result = publish_to_platform(
            video_path=args.video, platform=args.platform,
            title=args.title, description=args.desc, tags=tags,
        )
        print(f"{'✅' if result.get('success') else '❌'} publish_to_{args.platform}")
        if result.get("error"):
            print(f"   error: {result['error']}")
        elif result.get("output"):
            print(f"   output: {result['output'][:300]}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
