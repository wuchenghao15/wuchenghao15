#!/usr/bin/env python3
"""
仙女座 AI 员工 · AI 短视频制作 Skill 学习 (Web + GitHub)
══════════════════════════════════════════════════════
搜索来源: GitHub trending / awesome-video-generation / OpenMontage / Pixelle-Video
覆盖: 开源模型 / 商业 API / 全流程 Pipeline / Agent 系统 / 技术栈

流程:
  1. 批量写入 ai_brain_enhanced_knowledge (category='ai_short_video')
  2. 触发 trigger_evolution_broadcast → 演化引擎吸收
  3. AI 员工 skill_level 自动提升 + knowledge_base_size 增长
"""
import sqlite3, json, time, os, sys, uuid

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "app.db")
c = sqlite3.connect(DB_PATH, timeout=10)

print("=" * 70)
print("🎬 仙女座 AI 员工 · AI 短视频 Skill 学习")
print("=" * 70)

# ─────────────────────────────────────────────────────────────
# AI 短视频制作知识 (从 GitHub + Web 搜索整理)
# ─────────────────────────────────────────────────────────────

VIDEO_KNOWLEDGE = [
    # ═══════════════════════════════════════════════════════
    # Section 1: 全流程 Agent 系统 (最完整的 pipeline)
    # ═══════════════════════════════════════════════════════
    {
        "category": "ai_short_video",
        "subcategory": "full_pipeline",
        "title": "OpenMontage — 世界首个开源 Agent 全流程视频制作系统",
        "content": """OpenMontage (github.com/calesthio/OpenMontage, 34.7k stars, Python)
世界上第一个开源的 agentic video production system。

核心能力:
  - 12 个完整 production pipelines
  - 52 个 video production tools
  - 500+ agent skills
  - 把 AI coding assistant (Claude/GPT/Cursor/Copilot) 变成完整视频制作工作室

技术栈: Python, agent, flux, open-source, text-to-speech, ffmpeg, stable-diffusion, 
        remotion (视频框架), elevenlabs, openai, claude

工作流:
  1. 剧本生成 → 2. 分镜设计 → 3. 角色一致性控制 → 4. 画面生成
  5. 配音 (ElevenLabs/Edge-TTS) → 6. 字幕烧录 → 7. FFmpeg 合成 → 8. Remotion 渲染

适用: 短视频 / 短剧 / AI 影视 / shorts production""",
        "source": "github:calesthio/OpenMontage",
        "quality": 0.98,
    },
    {
        "category": "ai_short_video",
        "subcategory": "full_pipeline",
        "title": "Pixelle-Video — AI 全自动短视频引擎",
        "content": """Pixelle-Video (github.com/ATH-MaaS/Pixelle-Video, 24.3k stars, Python)
AI Fully Automated Short Video Engine — 全自动短视频生成引擎。

核心特性:
  - 一键从剧本到完整视频
  - 自动分镜 + 自动角色设计 + 自动画面生成
  - ComfyUI 后端支持
  - TTS 语音合成
  - 字幕自动烧录
  - 1080p 输出

技术栈: Python, TTS, image-generation, video-generation, AIGC, ComfyUI""",
        "source": "github:ATH-MaaS/Pixelle-Video",
        "quality": 0.95,
    },
    {
        "category": "ai_short_video",
        "subcategory": "full_pipeline",
        "title": "Duix-Avatar — 开源数字人克隆工具包",
        "content": """Duix-Avatar (github.com/duixcom/Duix-Avatar, 13.8k stars)
真正的开源 AI avatar / digital human toolkit — 离线视频生成 + 数字人克隆。

核心能力:
  - 完全开源的数字人克隆 (audio → 视频)
  - Offline video generation (离线生成, 零 API 费用)
  - Lip sync (口型同步)
  - Avatar animation
  - Face cloning

适用: 数字人 / 虚拟主播 / AI 讲师 / talking head""",
        "source": "github:duixcom/Duix-Avatar",
        "quality": 0.92,
    },

    # ═══════════════════════════════════════════════════════
    # Section 2: 开源视频生成模型 (可本地跑)
    # ═══════════════════════════════════════════════════════
    {
        "category": "ai_short_video",
        "subcategory": "opensource_model",
        "title": "Wan2.2 — 阿里开源视频生成大模型 (当前最强)",
        "content": """Wan2.2 (github.com/Wan-Video/Wan2.2, 16.6k stars, Python)
阿里达摩院开源, 目前最强的开源视频生成模型。

核心能力:
  - Text-to-Video (文生视频)
  - Image-to-Video (图生视频)
  - 高质量 1080p 输出
  - 长视频生成
  - 角色一致性较好
  - 透明 alpha 通道 (Wan-Alpha)

本地部署:
  - ComfyUI 节点可用
  - 需要 NVIDIA GPU (≥16GB VRAM)
  - 支持 HuggingFace weights
  - Python 推理脚本可用

适用: 短剧 / 短视频 / 影视分镜 / 动效素材""",
        "source": "github:Wan-Video/Wan2.2",
        "quality": 0.97,
    },
    {
        "category": "ai_short_video",
        "subcategory": "opensource_model",
        "title": "CogVideo — 清华视频生成框架",
        "content": """CogVideo (github.com/THUDM/CogVideo, 12.8k stars, Apache-2.0)
清华大学 CogVideo 系列, 完整视频生成框架。

核心能力:
  - Text-to-Video
  - Image-to-Video  
  - Video Captioning (反向: 视频→描述)
  - 长视频扩展
  - Latent Diffusion + Transformer 架构
  - LLM prompt expansion (短描述→详细描述)

版本: CogVideoX, CogVideoX-2B, CogVideoX-5B

适用: 研究 / 本地部署 / 视频理解 + 生成双功能""",
        "source": "github:THUDM/CogVideo",
        "quality": 0.96,
    },
    {
        "category": "ai_short_video",
        "subcategory": "opensource_model",
        "title": "Open Sora — Sora 级开源模型",
        "content": """Open Sora (github.com/hpcaitech/Open-Sora)
清华 HPC-AI Tech, Sora 级开源视频生成。

核心: Diffusion Transformer (DiT) 架构
特性: 高分辨率 / 长时长 / 高质量视频

适合: 有 GPU 算力的研究/生产环境""",
        "source": "github:hpcaitech/Open-Sora",
        "quality": 0.93,
    },
    {
        "category": "ai_short_video",
        "subcategory": "opensource_model",
        "title": "LivePortrait — Kling AI 人脸动画",
        "content": """LivePortrait (github.com/KlingAIResearch/LivePortrait, 18.7k stars)
快手 Kling AI 开源 — 让静止画像动起来。

核心能力:
  - Face animation (人脸动画)
  - Portrait animation (画像动起来)
  - Driving video (驱动视频)
  - 表情迁移
  - 姿态迁移

适用: AI 短剧演员 / 虚拟主播 / 老照片活化 / 数字人""",
        "source": "github:KlingAIResearch/LivePortrait",
        "quality": 0.94,
    },

    # ═══════════════════════════════════════════════════════
    # Section 3: 商业 API (调接口, 快速上手)
    # ═══════════════════════════════════════════════════════
    {
        "category": "ai_short_video",
        "subcategory": "commercial_api",
        "title": "国产 AI 视频生成 API 对比 (2026)",
        "content": """中国 AI 视频生成 API 生态 (2026):

| API | 公司 | 特点 | 质量 | 价格 |
|-----|------|------|------|------|
| Kling AI | 快手 | 角色一致性好, 真人效果 | ⭐⭐⭐⭐⭐ | 中等 |
| Seedance 2.5 | 字节跳动 | 4K 原生, 真人脸, 角色一致 | ⭐⭐⭐⭐⭐ | 中等 |
| Hailuo AI | MiniMax | 海螺视频, 质量高 | ⭐⭐⭐⭐ | 中等 |
| Vidu | 生数科技 | 稳定输出 | ⭐⭐⭐⭐ | 中等 |
| Qwen-Video | 阿里通义 | 长视频 | ⭐⭐⭐⭐ | 中等 |
| HunyuanVideo API | 腾讯混元 | 多模态 | ⭐⭐⭐⭐ | 中等 |

Python SDK:
  - Seedance-2.5-API (github.com/SamurAIGPT, 466 stars)
  - Seedance-2-API (github.com/Anil-matcha, 344 stars)
  - Kling AI 有官方 Python SDK
  - MiniMax / Hailuo 有 HTTP API

适用: 不想自己训模型, 快速出片""",
        "source": "web+github: awesome-video-generation",
        "quality": 0.92,
    },
    {
        "category": "ai_short_video",
        "subcategory": "commercial_api",
        "title": "海外 AI 视频 API 对比",
        "content": """海外 AI 视频生成 API (2026):

| API | 特点 | 限制 |
|-----|------|------|
| Runway Gen-3/4 | 行业标准, 质量最高 | 贵, 排队 |
| Pika 2.0 | 速度快, 创意性好 | 角色一致性一般 |
| Luma Dream Machine | 运动自然 | 时长限制 |
| Veo 2/3 (Google) | 真实感强 | Waitlist |
| Stability SVD | 开源, image-to-video | 短 (4s) |
| ElevenLabs | TTS + Dubbing | 不是视频生成, 是配音 |
| Fliki | text-to-video + TTS 一体化 | 简单但好用 |

选择策略:
  - 真人短剧 → Kling / Seedance (国产更适合亚洲脸)
  - 创意动画 → Runway / Pika
  - 图片转视频 → LivePortrait / SVD
  - 想零 API 费用 → Wan / CogVideo 本地跑""",
        "source": "web: awesome-video-generation",
        "quality": 0.90,
    },

    # ═══════════════════════════════════════════════════════
    # Section 4: 完整制作 Pipeline (手工 + Agent)
    # ═══════════════════════════════════════════════════════
    {
        "category": "ai_short_video",
        "subcategory": "pipeline",
        "title": "AI 短视频完整制作 Pipeline (手工版)",
        "content": """AI 短视频 8 步完整 Pipeline (手工可控):

Step 1 — 剧本生成
  LLM (GPT/Claude/DeepSeek) → 分镜剧本 (scene + 台词 + 画面描述)
  格式: scene_num | narration | visual_prompt | duration

Step 2 — 分镜 Storyboard
  把剧本转化为逐镜头的 visual prompt
  统一角色描述 (确保一致性)

Step 3 — 角色设计 + 一致性
  ComfyUI + IP-Adapter / InstantID
  或 LivePortrait 驱动
  关键: 同一角色每张图/视频保持外观一致

Step 4 — 画面生成 (每个镜头)
  Image-to-Video: 首帧图 → Wan/CogVideo/LivePortrait 生成 2-5s 视频
  Text-to-Video: prompt → 直接生成
  关键: 镜头运动 (推/拉/摇/跟) 统一

Step 5 — 配音 TTS
  ElevenLabs (英文最好)
  Edge-TTS (免费, 多语言)
  火山引擎 / 讯飞 (中文最好)
  多角色 → 多 voice preset

Step 6 — 字幕 + 后期
  自动生成 SRT → FFmpeg 烧录
  特效: 转场 / 滤镜 / 调色
  Remotion (React 视频框架) 做模板化

Step 7 — FFmpeg 合成
  ffmpeg -i scene1.mp4 -i scene2.mp4 -filter_complex concat
  ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac output.mp4
  ffmpeg -i video.mp4 -vf subtitles=subs.srt -c:a copy output_with_subs.mp4

Step 8 — 输出导出
  1080p / 2K / 4K
  H.264 (通用) / H.265 (压缩)
  MP4 / MOV / WebM""",
        "source": "experience+github",
        "quality": 0.96,
    },
    {
        "category": "ai_short_video",
        "subcategory": "pipeline",
        "title": "AI 短视频完整制作 Pipeline (Agent 自动化版)",
        "content": """AI Agent 全自动化短视频 Pipeline (无需人类干预):

Agent 1 — Scriptwriter (LLM)
  输入: 主题 / 关键词
  输出: 分镜剧本 + 逐镜头 visual prompt + 角色卡
  工具: GPT-4o / Claude 3.5 Sonnet

Agent 2 — Visual Designer (ComfyUI)
  输入: 剧本 + 角色卡
  输出: 每个镜头的首帧图 + 风格一致
  工具: Flux / SDXL + IP-Adapter + ControlNet

Agent 3 — Video Generator (Wan/CogVideo)
  输入: 首帧图 + motion prompt
  输出: 2-5s 视频 clip
  工具: Wan2.2 image-to-video / LivePortrait / Kling API

Agent 4 — Voice Actor (TTS)
  输入: 台词
  输出: 多角色配音 track
  工具: ElevenLabs API / 火山引擎 / 本地 Edge-TTS

Agent 5 — Editor (FFmpeg + Remotion)
  输入: 所有视频 clip + 音轨 + SRT 字幕
  输出: 完整成片
  工具: FFmpeg / Remotion / MoviePy

Agent Orchestrator
  调度上面 5 个 Agent
  处理失败重试
  确保角色一致性 + 风格一致性
  质量检查 (VBench / VCLIP 评分)

开源实现参考: OpenMontage, Pixelle-Video, AIComicBuilder (1.8k⭐)""",
        "source": "github:OpenMontage + 经验",
        "quality": 0.95,
    },

    # ═══════════════════════════════════════════════════════
    # Section 5: 技术栈汇总
    # ═══════════════════════════════════════════════════════
    {
        "category": "ai_short_video",
        "subcategory": "tech_stack",
        "title": "AI 短视频制作技术栈汇总 (2026)",
        "content": """AI 短视频完整技术栈:

【脚本生成】
  - LLM: GPT-4o / Claude 3.5 / DeepSeek V3 / Qwen 2.5
  - Prompt 模板系统: 分镜格式 / 角色卡 / visual prompt 生成器

【画面生成】
  - 文生图: Flux / SDXL / DALL-E 3 / Midjourney
  - 图生视频: Wan2.2 / CogVideo / LivePortrait / Kling API
  - 角色一致性: IP-Adapter / InstantID / ComfyUI
  - 开源框架: ComfyUI / Diffusers (HuggingFace) / diffsynth

【配音 TTS】
  - 云端 API: ElevenLabs / 火山引擎 / 讯飞 / MiniMax
  - 免费: Edge-TTS (Python edge-tts) / Bark
  - 本地: CosyVoice / ChatTTS (Python)
  - 多角色: voice clone / voice preset

【视频合成】
  - FFmpeg (命令行): 合成 + 字幕 + 转场 + 压缩
  - MoviePy (Python): 编程式视频编辑
  - Remotion (React): 模板化视频生成
  - OpenCV: 图像处理

【数字人】
  - Duix-Avatar: 开源数字人克隆
  - LivePortrait: 人脸动画驱动
  - SadTalker: 开源说话人头
  - Wav2Lip: 口型同步
  - MuseTalk: 实时 talking head

【评估】
  - VBench: 视频质量评估基准
  - VCLIP: 视频-文本相似度
  - PySceneDetect: 镜头切换检测
  - VMAF / SSIM: 画质评估

【基础设施】
  - GPU: RTX 4090 / A100 (≥16GB VRAM)
  - 云: RunPod / Lambda Labs / AutoDL
  - 存储: S3 / R2
  - 队列: Redis + Celery / BullMQ (Node.js)""",
        "source": "web+github",
        "quality": 0.97,
    },

    # ═══════════════════════════════════════════════════════
    # Section 6: 实操 Skill — 最小可运行链路
    # ═══════════════════════════════════════════════════════
    {
        "category": "ai_short_video",
        "subcategory": "minimum_pipeline",
        "title": "零 API 费用: AI 短视频最小可运行 Pipeline (本地全开源)",
        "content": """完全开源 + 零 API 费用 + 本地可跑的最小 AI 短视频 Pipeline:

环境: macOS (M1/M2/M3 Pro 或 Intel) / Linux / Windows
GPU: Apple Silicon (Metal) 或 NVIDIA (CUDA, ≥12GB)

Step 1 — 安装依赖
  brew install ffmpeg python3 git-lfs
  pip install diffusers transformers accelerate edge-tts moviepy
  pip install comfyui (可选, GUI 方式)

Step 2 — 文生图 (Flux, 本地 Metal)
  from diffusers import FluxPipeline
  pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell")
  image = pipe("cinematic scene, golden hour").images[0]

Step 3 — 图生视频 (LivePortrait 或 CogVideoX)
  # LivePortrait: 让图动起来
  git clone https://github.com/KlingAIResearch/LivePortrait
  python inference.py -s source.jpg -d driving.mp4

  # CogVideoX: 直接生成视频
  from diffusers import CogVideoXPipeline
  pipe = CogVideoXPipeline.from_pretrained("THUDM/CogVideoX-2B")
  video = pipe("a cat running").frames

Step 4 — 配音 (Edge-TTS, 免费)
  import asyncio, edge_tts
  async def speak():
      await edge_tts.Communicate("你好世界", "zh-CN-XiaoxiaoNeural").save("out.mp3")
  asyncio.run(speak())

Step 5 — 合成 (FFmpeg)
  # 字幕烧录
  ffmpeg -i video.mp4 -vf subtitles=subs.srt -c:a copy output.mp4
  # 音视频合成
  ffmpeg -i video.mp4 -i audio.mp3 -shortest -c:v copy output.mp4

Step 6 — 导出 1080p
  ffmpeg -i output.mp4 -vf scale=1920:1080 -c:v libx264 -crf 23 final.mp4

关键工具:
  FFmpeg / edge-tts / diffusers / LivePortrait / ComfyUI / MoviePy""",
        "source": "github+经验",
        "quality": 0.94,
    },
    {
        "category": "ai_short_video",
        "subcategory": "minimum_pipeline",
        "title": "最快上手: 商业 API 版 5 分钟出片",
        "content": """最快出片方案 (调 API, 不装模型, 5 分钟):

1. 注册 Kling AI / Runway / Seedance
2. 用 Python SDK 或 HTTP API:

# 示例: Kling AI Python SDK (伪代码)
from kling import KlingClient
client = KlingClient(api_key="your_key")

# 文生视频
video = client.text_to_video(
    prompt="一位侠客在雨中的竹林里舞剑, 电影感, 慢动作",
    duration=5,
    mode="standard"
)
video.download("output.mp4")

# 配音 (ElevenLabs)
from elevenlabs import generate, play
audio = generate(text="一位侠客在雨中的竹林里舞剑...", voice="Chinese Male")
# ffmpeg 合成

# 种子 (Seedance 2.5) Python SDK
from seedance import SeedanceClient
client = SeedanceClient(api_key="sk-...")
resp = client.text_to_video(prompt="...", resolution="1080p")
resp.download("output.mp4")

3. FFmpeg 合成字幕 + 音轨 → 完成

成本估算:
  Kling: ~$0.5/5s
  Seedance: ~$0.4/5s
  Runway: ~$1.0/4s
  
适用: 不想折腾 GPU, 快速验证想法""",
        "source": "github:SamurAIGPT/Seedance-2.5-API + 经验",
        "quality": 0.90,
    },

    # ═══════════════════════════════════════════════════════
    # Section 7: 质量控制 + 常见坑
    # ═══════════════════════════════════════════════════════
    {
        "category": "ai_short_video",
        "subcategory": "quality_control",
        "title": "AI 短视频质量控制 — 5 个关键指标 + 常见坑",
        "content": """AI 短视频质量控制 (QC):

【核心指标】
  1. 角色一致性 (Character Consistency) — 同一角色在不同镜头长相不能大变
     方法: IP-Adapter / InstantID / 固定 seed + LoRA fine-tune
  2. 运动自然度 (Motion Naturalness) — 不抽搐 / 不变形 / 不闪烁
     方法: Wan2.2 / LivePortrait / 使用 driving video 引导
  3. 画面连贯性 (Temporal Coherence) — 相邻镜头切换不突兀
     方法: 统一风格 / 色温 / 光照 / 转场特效
  4. 文字可读性 — 字幕清晰不糊
     方法: FFmpeg subtitles filter / Remotion 精调位置
  5. 音频同步 — 口型和配音匹配
     方法: Wav2Lip / MuseTalk / 手动对齐

【常见坑】
  ❌ 角色在不同镜头变了 (最常见!)
     → 用 IP-Adapter / 固定角色卡 / 同一张 reference image
  ❌ 画面闪烁 / 变形
     → 用更强的模型 (Wan2.2 > CogVideoX) / 缩短时长 2-3s
  ❌ 口型不同步
     → 加 Wav2Lip 后处理 / 用 LivePortrait + 音频驱动
  ❌ 人物 6 指 / 肢体异常
     → Flux + ControlNet / 用 reference image 约束
  ❌ 字幕烧录后模糊
     → subtitles 滤镜 fontsize=32+ / 背景加深
  ❌ API 限流
     → 加 retry / 排队 / 用多个 API 分摊

【评估工具】
  VBench — 学术界视频质量评估基准
  VCLIP — 视频和文本描述的相似度
  PySceneDetect — 自动镜头切换检测
  VMAF — 画质客观评分""",
        "source": "经验+github",
        "quality": 0.93,
    },
]

# ─────────────────────────────────────────────────────────────
# 批量写入脑库
# ─────────────────────────────────────────────────────────────

print(f"\n📚 开始写入 {len(VIDEO_KNOWLEDGE)} 条 AI 短视频知识到脑库...")

inserted = 0
for i, k in enumerate(VIDEO_KNOWLEDGE):
    try:
        kid = f"VIDEO-SKILL-{uuid.uuid4().hex[:8]}"
        c.execute("""
            INSERT INTO ai_brain_enhanced_knowledge
            (knowledge_id, category, subcategory, title, content, source, 
             quality_score, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
        """, (
            kid,
            k["category"],
            k.get("subcategory", ""),
            k["title"],
            k["content"],
            k.get("source", "web"),
            k.get("quality", 0.8),
            json.dumps(["ai_short_video", "skill", "github", "andromeda_learned"], ensure_ascii=False),
        ))
        inserted += 1
        print(f"  ✅ [{i+1:2d}/16] {k['title'][:50]:<50} ({k.get('quality',0):.2f})")
    except Exception as e:
        print(f"  ❌ [{i+1:2d}/16] {k['title'][:50]:<50} ERROR: {e}")

c.commit()

print(f"\n✅ 脑库写入完成: {inserted}/{len(VIDEO_KNOWLEDGE)} 条")

# 脑库总量变化
total = c.execute("SELECT COUNT(*) FROM ai_brain_enhanced_knowledge").fetchone()[0]
print(f"   脑库总量: {total} 条")

# 短视频知识分类
cnt = c.execute("SELECT COUNT(*) FROM ai_brain_enhanced_knowledge WHERE category='ai_short_video'").fetchone()[0]
print(f"   AI 短视频知识: {cnt} 条")

c.close()

# ─────────────────────────────────────────────────────────────
# 触发演化 — 让仙女座 AI 员工吸收新知识
# ─────────────────────────────────────────────────────────────
print(f"\n🔔 触发演化 — 让仙女座吸收 AI 短视频 Skill...")

# 直接调用演化触发
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engines"))
from trigger_evolution_broadcast import trigger_evolution_broadcast

triggers = [
    ("brain_ai_short_video_ingest", "brain_new_knowledge", "knowledge"),
    ("ai_short_video_skill_learned", "darwin_debate_conclusion", "evolution"),
    ("github_video_model_update", "rule_modified", "rules"),
]

for reason, ttype, source in triggers:
    ok = trigger_evolution_broadcast(reason, trigger_type=ttype, source=source)
    print(f"  {'✅' if ok else '⏸️'} {ttype} → {reason}")

print(f"\n{'='*70}")
print(f"🎬 仙女座 AI 员工 · AI 短视频 Skill 学习完成!")
print(f"{'='*70}")
print(f"""
  脑库新增: {inserted} 条 AI 短视频知识
  类别覆盖:
    • 全流程 Agent 系统 (OpenMontage/Pixelle/Duix-Avatar)
    • 开源视频生成模型 (Wan/CogVideo/Open Sora/LivePortrait)
    • 商业 API 对比 (Kling/Seedance/Hailuo/Runway)
    • 完整制作 Pipeline (手工 8 步 + Agent 自动化 5 Agent)
    • 技术栈汇总 (脚本/画面/配音/合成/评估/基础设施)
    • 最小可运行链路 (本地零 API 版 + 商业 API 版)
    • 质量控制指标 + 常见坑

  下一步 (自动):
    sys_andromeda_auto_evolution 30s 周期运行
    → 扫到 brain_new_knowledge 事件
    → run_cycle() 摄入新知识
    → AI 员工 skill_level 自动提升
    → knowledge_graph 自动关联 AI 短视频节点
""")
