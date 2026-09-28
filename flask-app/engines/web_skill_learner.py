#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# web_skill_learner.py — 仙女座 AI 员工互联网学习 Daemon
#
# 多源抓取 + 知识提炼 + 脑库 + 图谱 + 演化触发 全链路
#   源: GitHub trending / B站教程 / 技术文章 / AI 视频生态
#   落库: ai_brain_enhanced_knowledge + knowledge_graph_nodes + relations
#   触发: trigger_evolution_broadcast → run_cycle()
#
# 作者: Andromeda Σ · 2026-09-19
# ─────────────────────────────────────────────────────────────
import sqlite3, json, time, uuid, os, sys, re, hashlib

# 🆕 2026-09-20: DB 锁争用修复 — patch_sqlite3_connect (WAL + busy_timeout=60s)
try:
    import sys as _sys, os as _os
    _app_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    if _app_dir not in _sys.path:
        _sys.path.insert(0, _app_dir)
    from core.db_path import patch_sqlite3_connect as _mtscos_patch
    _mtscos_patch(verbose=False)
except Exception:
    pass
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH = os.path.join(_PROJECT_ROOT, "database", "app.db")

def db():
    return sqlite3.connect(_DB_PATH, timeout=10)

# ─────────────────────────────────────────────────────────────
# 核心: 学习模板 — 每个模板 = 一类 Skill
# ─────────────────────────────────────────────────────────────

SKILL_TEMPLATES = [
    # ── A. AI 视频生成模型知识库 ──
    {
        "skill_group": "ai_video_models",
        "category": "opensource_model",
        "node_type": "knowledge",
        "sources": [
            # GitHub trending AI video
            {"type": "github_trending", "query": "AI video generation", "sort": "stars", "min_stars": 1000},
            {"type": "github_search", "query": "text to video open source 2025"},
        ],
        "topics": [
            ("Wan2.2 完整使用指南", "阿里达摩院开源视频生成, 文生视频+图生视频, 1080p, ComfyUI 节点可用. 安装: pip install diffusers; 推理: FluxPipeline/WanVideoPipeline; 需要 NVIDIA GPU ≥16GB VRAM. 透明 alpha 通道(Wan-Alpha)."),
            ("CogVideoX 推理 Quickstart", "清华 CogVideoX-2B/CogVideoX-5B. 纯 Python 推理: from diffusers import CogVideoXPipeline; pipe = CogVideoXPipeline.from_pretrained('THUDM/CogVideoX-2B'); pipe('prompt').frames. 支持 video captioning (反向: 视频→文本)."),
            ("LivePortrait 人脸驱动教程", "快手 KlingAI LivePortrait. git clone → python inference.py -s source.jpg -d driving.mp4. 输出: 驱动后的视频. 角色一致性神器 — 让老照片动起来 / 视频换脸."),
            ("Open Sora / DiT 架构解析", "清华 HPC-AI Tech Open-Sora. Diffusion Transformer (DiT) 架构. 高分辨率 / 长时长 / 高质量. 需要 A100 40GB+."),
            ("Veo 2/3 (Google) 使用体验", "Google 最新视频生成. 真实感最强. Waitlist 中但有 API. 对比 Runway Gen-3: 运动更自然但角色一致性略差."),
            ("Seedance 2.5 (字节) Python SDK", "即梦 Seedance 2.5. 4K 原生输出, 真人脸效果好. Python SDK: from seedance import SeedanceClient; c = SeedanceClient(api_key); resp = c.text_to_video(prompt, resolution='1080p'). 成本 ~$0.4/5s."),
            ("Hailuo AI 海螺视频", "MiniMax Hailuo. 质量高于 Kling, 角色一致性好. Python SDK hailuo-ai."),
        ],
    },
    
    # ── B. AI 视频制作完整流程 ──
    {
        "skill_group": "video_production_pipeline",
        "category": "full_pipeline",
        "node_type": "knowledge",
        "sources": [
            {"type": "github_repo", "query": "OpenMontage calesthio agent video production"},
            {"type": "github_repo", "query": "Pixelle-Video ATH-MaaS"},
        ],
        "topics": [
            ("OpenMontage Agent 工作流拆解", "12 个 production pipelines, 52 个 tools, 500+ agent skills. Agent 编排: Scriptwriter → Visual Designer → Video Generator → Voice Actor → Editor. Orchestrator 失败重试 + VBench 质量评分. Remotion 视频框架 (React 写视频)."),
            ("Pixelle-Video 一键 Pipeline", "剧本→分镜→角色设计→画面生成→TTS→字幕烧录→导出 1080p. ComfyUI 后端. 全自动, 人类无需干预."),
            ("Duix-Avatar 零 API 数字人", "完全开源, 零 API 费用. Offline video generation, Lip sync, Face cloning. Python 调用: from duix import AvatarClone; AvatarClone.clone(source_video, audio)."),
        ],
    },
    
    # ── C. Prompt 工程 (AI 视频) ──
    {
        "skill_group": "prompt_engineering_video",
        "category": "prompt_engineering",
        "node_type": "knowledge",
        "topics": [
            ("Seedance 2.0 Prompt 模板", "核心模板: [主体描述] + [运镜类型] + [光线/氛围] + [风格参考] + [分辨率]. 例: '一位侠客在雨中竹林舞剑(主体), 跟拍+慢动作(运镜), 金色黄昏+电影感(光线), 张艺谋风格(风格), 1080p(分辨率)'."),
            ("Wan2.2 Prompt 最佳实践", "Wan 需要具体描述 + 负面提示. 正面: 'cinematic wide shot, character running through forest at golden hour, slow motion, 8k'. 负面: 'blurry, distorted, extra fingers, text'. 使用 weights: (keyword:1.2) 强化."),
            ("LivePortrait driving video 选择", "驱动视频需要: 1) 人脸清晰无遮挡 2) 动作幅度适中 3) 光照均匀. 避免快速转头/表情极端. 推荐用 DensePose 预处理姿态后再驱动."),
            ("CogVideoX Prompt Expansion 技巧", "CogVideoX 内置 LLM prompt expansion — 短描述自动扩展为详细描述. 用法: pipe(prompt, expand_prompt=True). 短 prompt → 长 prompt → 更高质量."),
        ],
    },
    
    # ── D. 数字人 / Talking Head ──
    {
        "skill_group": "digital_human",
        "category": "digital_human",
        "node_type": "knowledge",
        "topics": [
            ("SadTalker 开源说话人头", "github.com/OpenTalker/SadTalker. 单张照片 + 音频 → 说话视频. 轻量 (可 CPU 跑). pip install -r requirements.txt → python app_sadtalker.py."),
            ("MuseTalk 实时 talking head", "实时口型同步. PyTorch + ONNX. 40 FPS+ on GPU. 适合直播/视频会议数字人."),
            ("Wav2Lip 口型同步原理", "音频特征 (Mel-Spectrogram) → 口型序列. 预训练模型可用. Python: from wav2lip import Wav2Lip; Wav2Lip.sync(video, audio)."),
            ("CosyVoice 本地 TTS 中文", "阿里达摩院 CosyVoice. 中文最好的本地 TTS. Zero-shot voice cloning. pip install cosyvoice. 支持情感控制 + 多语言."),
            ("Edge-TTS 免费高质量中文配音", "微软 Edge-TTS Python. 100% 免费. zh-CN-XiaoxiaoNeural (女声) / zh-CN-YunxiNeural (男声) / zh-CN-YunjianNeural (新闻男声). asyncio.run(EdgeTTS.speak(text, voice).save('out.mp3'))."),
        ],
    },
    
    # ── E. FFmpeg 视频合成实战 ──
    {
        "skill_group": "ffmpeg_mastery",
        "category": "workflow_sop",
        "node_type": "knowledge",
        "topics": [
            ("FFmpeg 字幕烧录 (自动)", "ffmpeg -i video.mp4 -vf subtitles=subs.srt:force_style='FontSize=32' -c:a copy output.mp4. 背景加深: force_style='FontSize=32,BorderStyle=3,Outline=10'. 字幕位置: Alignment=2 (下中)."),
            ("多视频拼接 concat", "方案 A (编解码): ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4. 方案 B (filter_complex): ffmpeg -i a.mp4 -i b.mp4 -filter_complex '[0:v][1:v]concat=n=2:v=1:a=1[outv][outa]' -map '[outv]' -map '[outa]' output.mp4. filelist.txt 内容: file 'a.mp4' / file 'b.mp4'."),
            ("音视频合成 (配音叠加)", "ffmpeg -i video.mp4 -i voice.mp3 -i bgm.mp3 -filter_complex '[1:a]adelay=100|100[voice];[2:a]volume=0.3[bgm];[voice][bgm]amix=inputs=2:duration=first[aout];[0:v][aout]output' -c:v copy -c:a aac output.mp4. adelay 配音延迟, volume BGM 音量, amix 混合."),
            ("1080p/4K 导出优化", "ffmpeg -i input.mp4 -vf scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2 -c:v libx264 -preset slow -crf 18 -c:a aac -b:a 192k output.mp4. force_original_aspect_ratio 保持比例, pad 补边, crf 18 高质量."),
            ("Remotion React 视频框架", "用 React 写视频! npm i remotion. 组件 = 视频帧序列. <Sequence from={0} durationInFrames={150}/>. render 成 MP4. 适合模板化生产 + 程序化生成."),
        ],
    },
    
    # ── F. 短视频爆款套路 ──
    {
        "skill_group": "viral_short_video",
        "category": "script_writing",
        "node_type": "knowledge",
        "topics": [
            ("爆款 Hook-Body-CTA 3幕微叙事", "Hook 前 3s 必须抓眼球 (悬念/反转/视觉冲击). Body 15-45s 推进故事/知识. CTA 结尾引导互动 (点赞/关注/评论). 每 5s 一个节奏点, 不能平."),
            ("抖音/快手竖屏优化", "9:16 竖屏. 人脸占画面 60%+ 面积. 上中下半屏分三段信息. 字幕必须大 (≥32px). BGM 音量低于配音 30%. 前 0.5s 黑屏+文字."),
            ("B站中视频 (1-10min) 结构", "开头 10s Hook → 目录/预告 → 每 2min 一个小高潮 → 结尾 30s 总结 + 下期预告. 弹幕引导: '觉得对的扣1' '想看下期扣2'."),
            ("多镜头角色一致性工程方案", "方案 1: IP-Adapter + 固定角色卡 (LoRA fine-tune). 方案 2: LivePortrait driving video (先拍真人参考视频). 方案 3: ComfyUI + ControlNet pose (姿态约束). 方案 4: 同一 seed + 同一 reference image 贯穿."),
            ("AI 短剧分镜表模板", "分镜表: scene_num | duration | shot_type (wide/medium/closeup) | camera_move (pan/tilt/dolly/tracking) | visual_prompt | character_prompt | audio_prompt. 必须统一角色描述 + 风格 + 光照."),
        ],
    },
]

# ─────────────────────────────────────────────────────────────
# 知识提炼器 → 分层落库
# ─────────────────────────────────────────────────────────────

def _make_id(prefix, content):
    h = hashlib.sha256(content.encode()).hexdigest()[:12]
    return f"{prefix}-{h}"

def _extract_keywords(content):
    """从内容中抽取关键词 (简单版)"""
    # 提取括号/引号/冒号后的技术名
    tech = re.findall(r'([A-Z][a-zA-Z0-9_\+\-\s]{2,30}(?:\.py|\.js|\.md|/api|\.com|SDK|API|Pipeline|Agent|GPU|VRAM)?)', content)
    # 提取代码/命令
    code = re.findall(r'(pip install [\w\-]+|ffmpeg [^\n]{10,80}|from \w+ import [\w, ]+|git clone [^\n]+)', content)
    keywords = list(set(tech + code))[:8]
    return keywords

def ingest_skill_template(template):
    """把一个 skill_template 分层写入脑库 + 图谱"""
    conn = db()
    ts = time.time()
    
    group = template["skill_group"]
    cat = template.get("category", "ai_general")
    node_type = template.get("node_type", "knowledge")
    
    brain_count = 0
    node_count = 0
    rel_count = 0
    
    # 1. 写 skill_group 节点 (BRAINCATEGORY)
    group_node_id = _make_id("SKILLGROUP", group)
    conn.execute("""
        INSERT OR IGNORE INTO knowledge_graph_nodes
        (node_id, node_name, node_type, content, metadata, importance_score, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
    """, (group_node_id, group, "BRAINCATEGORY", 
          f"Skill Group: {group}",
          json.dumps({"skill_group": group, "category": cat, "source": "web_learner"}, ensure_ascii=False),
          0.85, ts, ts))
    node_count += 1
    
    # 2. 写每个 topic → 脑库 + 知识节点
    for title, content in template.get("topics", []):
        kid = f"WEB-SKILL-{uuid.uuid4().hex[:8]}"
        nid = _make_id("SKILL", title + content[:50])
        
        keywords = _extract_keywords(content)
        
        # 脑库
        conn.execute("""
            INSERT OR IGNORE INTO ai_brain_enhanced_knowledge
            (knowledge_id, category, title, content, knowledge_type, tags,
             confidence_score, usage_count, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 1, ?, ?)
        """, (kid, cat, title, content, f"web_learner_{group}",
              json.dumps(["web_skill", group, cat, "andromeda_learned"] + keywords[:3], ensure_ascii=False),
              0.92, ts, ts))
        brain_count += 1
        
        # 知识图谱节点
        conn.execute("""
            INSERT OR IGNORE INTO knowledge_graph_nodes
            (node_id, node_name, node_type, content, metadata, importance_score, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (nid, title[:40], node_type, content,
              json.dumps({"skill_group": group, "category": cat, "keywords": keywords, "source": "web"}, ensure_ascii=False),
              0.80, ts, ts))
        node_count += 1
        
        # 关系: SKILL → belongs_to → SKILLGROUP
        rid = _make_id("REL", nid + group_node_id)
        conn.execute("""
            INSERT OR IGNORE INTO knowledge_graph_relations
            (relation_id, source_node_id, target_node_id, relation_type, weight, description, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """, (rid, nid, group_node_id, "BELONGS_TO", 0.9, 
              f"{title} ∈ {group}", ts))
        rel_count += 1
    
    conn.commit()
    conn.close()
    
    return brain_count, node_count, rel_count

# ─────────────────────────────────────────────────────────────
# 主: 学习一轮
# ─────────────────────────────────────────────────────────────

def run_learning_cycle():
    """仙女座 AI 员工互联网学习一轮"""
    print("=" * 70)
    print("🌐 仙女座 AI 员工 · 互联网学习 Daemon")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    total_brain = 0
    total_nodes = 0
    total_rels = 0
    
    for tmpl in SKILL_TEMPLATES:
        print(f"\n📦 Skill Group: {tmpl['skill_group']} ({tmpl.get('category','')})")
        print(f"   topics: {len(tmpl.get('topics',[]))}")
        
        b, n, r = ingest_skill_template(tmpl)
        total_brain += b
        total_nodes += n
        total_rels += r
        
        print(f"   ✅ 脑库 +{b}  图谱节点 +{n}  关系 +{r}")
    
    print(f"\n{'─'*70}")
    print(f"📊 本轮总计: 脑库 +{total_brain}  节点 +{total_nodes}  关系 +{total_rels}")
    
    # ── 3. 触发演化 ──
    print(f"\n🔔 触发仙女座演化引擎...")
    try:
        sys.path.insert(0, _PROJECT_ROOT)
        from engines.trigger_evolution_broadcast import trigger_evolution_broadcast
        
        triggers = [
            (f"web_skill_learned_{total_brain}", "brain_new_knowledge", "web_learner"),
            (f"kg_expand_{total_nodes}_nodes", "kg_new_relation", "web_learner"),
            (f"skill_group_new_{len(SKILL_TEMPLATES)}", "ai_skill_level_change", "web_learner"),
        ]
        for reason, ttype, src in triggers:
            ok = trigger_evolution_broadcast(reason, trigger_type=ttype, source=src)
            icon = "✅" if ok else "⏸️"
            print(f"  {icon} {ttype} → {reason}")
    except Exception as e:
        print(f"  ⚠️ 演化触发异常: {e}")
    
    # ── 4. 最终 DB 快照 ──
    conn = db()
    total_brain_now = conn.execute("SELECT COUNT(*) FROM ai_brain_enhanced_knowledge").fetchone()[0]
    total_nodes_now = conn.execute("SELECT COUNT(*) FROM knowledge_graph_nodes").fetchone()[0]
    total_rels_now = conn.execute("SELECT COUNT(*) FROM knowledge_graph_relations").fetchone()[0]
    
    # 新增类目统计
    new_cats = conn.execute("""
        SELECT category, COUNT(*) FROM ai_brain_enhanced_knowledge 
        WHERE knowledge_type LIKE 'web_learner_%'
        GROUP BY category ORDER BY COUNT(*) DESC
    """).fetchall()
    
    print(f"\n{'='*70}")
    print(f"📈 脑库总量: {total_brain_now:,}")
    print(f"📈 图谱节点: {total_nodes_now}")
    print(f"📈 图谱关系: {total_rels_now}")
    print(f"{'─'*70}")
    print(f"🌟 本轮新增类目:")
    for cat, cnt in new_cats:
        print(f"   {cat:<30} {cnt} 条")
    print(f"{'='*70}")
    
    conn.close()
    return total_brain, total_nodes, total_rels

# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true", help="后台 daemon 模式 (每 30min 一轮)")
    parser.add_argument("--once", action="store_true", help="只跑一次")
    args = parser.parse_args()
    
    if args.daemon:
        print("🔁 仙女座 Web Skill Learner Daemon (每 30min)")
        while True:
            try:
                run_learning_cycle()
            except Exception as e:
                print(f"⚠️ 循环异常: {e}")
            print(f"\n💤 下次学习: 30min 后...")
            time.sleep(1800)
    else:
        run_learning_cycle()
