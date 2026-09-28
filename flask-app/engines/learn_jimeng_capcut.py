#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# learn_jimeng_capcut.py — 向即梦 Seedance 2.5 + 剪映学习 Skill
#
# 把即梦和剪映的核心能力提炼成仙女座可以复用的 Skill, 写入脑库
# 同时演示如何用 Python API 调用 Seedance 2.5
#
# 学习目标:
#   即梦 Seedance 2.5 — 30秒原生长镜头 / 4K / 50个多模态参考 / R2V 参考生视频 / 原生音画同步
#   剪映 6.0 — 20+ AI 工具 / 智能文案 / 数字人 / 智能剪口播 / AI补帧 / 人声分离
# ─────────────────────────────────────────────────────────────
import sqlite3, json, os, sys, time, uuid, hashlib

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

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH = os.path.join(_PROJECT_ROOT, "database", "app.db")

def db():
    return sqlite3.connect(_DB_PATH, timeout=10)

# ─────────────────────────────────────────────────────────────
# Skill 库: 即梦 Seedance 2.5
# ─────────────────────────────────────────────────────────────

SEEDANCE_25_SKILLS = [
    {
        "category": "opensource_model",
        "title": "即梦 Seedance 2.5 核心能力全景",
        "content": """Seedance 2.5 是字节跳动2026年7月31日发布的下一代视频生成模型.
核心能力:
  ① 30秒原生长镜头 (连续无拼接, 人物/服装/光线/动作全程一致)
  ② 4K原生输出 + 10-bit 色深 (比720p/1080p时代画质飞跃)
  ③ 原生音画同步 (声音和画面一次生成, 不是后配音)
  ④ 最多50个多模态参考素材 (图片+视频+风格+角色+产品 全部喂进去锁一致性)
  ⑤ R2V 参考视频控制 (上传参考视频传达运镜速度/人物轨迹/动作调度)
  ⑥ 精准局部编辑 (只改局部, 保留原有构图/光影/音频/时间线)
  ⑦ 强 Prompt 遵循 (详细描述会被精准执行, 模糊描述会产生模糊结果)

对比 Seedance 2 Mini: 全功能版 vs 迭代快/成本低 (3 credits/s, 4-15s, 480p/720p)

Python SDK: pip install seedance25-api
API 入口: CyberBara (cyberbara.com/api) 或 BytePlus ModelArk 或 fal.ai
定价: fal.ai $0.4730/s (720p) / $0.2205/s (480p), 音频包含在内""",
        "source": "jimeng.jianying.com / seedance-25.ai / fal.ai",
    },
    {
        "category": "prompt_engineering",
        "title": "Seedance 2.5 Prompt 结构模板 (6要素)",
        "content": """Seedance 2.5 Prompt 最佳实践 = 6要素结构:

[1. 主体描述] + [2. 动作/运镜] + [3. 场景/环境] + [4. 光线/氛围] + [5. 风格/参考] + [6. 音频描述]

完整模板:
"[主体] 在 [场景] [运镜描述], [动作细节], [光线条件], [风格参考], 电影质感. 
音频: [环境音] + [音效] + [人声描述]"

示例1 (AI产品广告):
"A high-end perfume commercial, slow motion liquid splash, 
glossy lighting, premium cinematic style. 
Camera: 360-degree orbiting close-up. 
Audio: glass clink, liquid pouring, ambient music. 
参考素材: 3张产品图 + 1支参考广告片"

示例2 (社交媒体竖屏):
"9:16 竖屏 UGC, 手持手机镜头, 中景. 
一位穿着浴袍的女生在阳光卧室里举着皱巴巴的亚麻衬衫, 
对着镜头说 Meeting in twenty minutes. 
然后用挂烫机熨烫, 最后挑眉看镜头. 
Audio: 房间混响 + 挂烫机 gurgling + 衬衫摩擦声"

Prompt 长度: 不要太冗长, 200-500字最佳. 
参考素材: 可混合图片+视频, 最多50个.""",
        "source": "seedance-25.ai/blog",
    },
    {
        "category": "api_integration",
        "title": "Seedance 2.5 Python SDK 实战 (CyberBara / BytePlus / fal.ai)",
        "content": """三选一 API 接入方式:

方式A: CyberBara (全球通用, pip 包已发布)
  pip install seedance25-api
  from seedance25_api import Seedance25Client
  client = Seedance25Client("YOUR_API_KEY")
  # 文生视频
  created = client.text_to_video("cinematic mountain village drone shot", duration="10", aspect_ratio="16:9")
  task = client.wait_for_task(created["task_id"])
  print(task["output"]["videos"])  # 下载URL
  # 图生视频 + 参考图
  upload = client.upload_images(["./character_ref.png"])
  created = client.image_to_video("character turns to camera, subtle smile",
                                  image_urls=upload["urls"], duration="10", aspect_ratio="9:16")

方式B: BytePlus ModelArk (官方接入)
  model_id = "dreamina-seedance-2-5-260628"
  from volcengine.boto3 import client as byte_client
  resp = byte_client.content_generation.tasks.create(
      model=model_id,
      content=[{"type":"text","text":"prompt"}, {"type":"image_url","image_url":{"url":"..."}}]
  )

方式C: fal.ai (最灵活, 支持 MCP server)
  npm install @fal-ai/client
  export FAL_KEY="YOUR_FAL_KEY"
  import { fal } from "@fal-ai/client"
  const result = await fal.subscribe("bytedance/seedance-2.5/text-to-video", {
    input: { prompt: "...", duration: 10, aspect_ratio: "9:16" }
  })

定价参考: fal.ai $0.4730/s (720p 16:9) / $0.2205/s (480p)
任务是异步的 — 创建后 poll task_id 直到完成""",
        "source": "pypi.org/project/seedance25-api / docs.byteplus.com / fal.ai",
    },
    {
        "category": "character_consistency",
        "title": "Seedance 2.5 角色一致性工程方案",
        "content": """30秒长镜头 + 角色一致性是 Seedance 2.5 最核心卖点. 实操方案:

方案1: 多参考素材锚定 (推荐)
  ① 准备 3-5 张角色正/侧/角度参考图
  ② 1 张风格参考图 (色彩/光线/质感)
  ③ 1 支动作参考视频 (如果有特定动作要求)
  → Seedance 2.5 自动融合 50 个参考素材锁定角色

方案2: R2V 参考视频控制
  上传一段真人表演视频 (即使是手机拍的) → Seedance 2.5 提取运镜/动作/调度
  → 用户只需描述 "用 Seedance 生成, 按照参考视频的运镜和节奏"

方案3: Prompt 里反复锚定
  开头描述 + 中间描述 + 结尾描述各加一次角色特征:
  "一个穿红色风衣的长发女生 [开头锚定] 走进咖啡馆 [中间锚定红色风衣长发], 
   坐下喝拿铁 [结尾锚定红色风衣长发特写]"

方案4: 后处理一致性修复
  用 Seedance 2.5 局部编辑功能 (Reference-to-Video endpoint):
  先出粗剪 → 锁定不一致的片段 → 局部重新生成 (不影响整段时间线)

常见坑:
  ❌ 只用文字描述 → 角色会飘 (换脸/换衣服/换发型)
  ❌ 参考图风格差异太大 → Seedance 平均化处理
  ✅ 参考图数量适中 3-5 张 + 1 风格图 → 最佳""",
        "source": "seedance-25.ai/blog",
    },
    {
        "category": "workflow_sop",
        "title": "Seedance 2.5 端到端工作流 (4步)",
        "content": """完整生产工作流, 从创意到成片:

Step 1 - 前期准备
  ✅ 写 Prompt (6要素: 主体+运镜+场景+光线+风格+音频)
  ✅ 准备参考素材 (角色图 3-5张 + 风格图 1张 + 动作视频 可选)
  ✅ 确定时长 (10s/15s/30s) 和比例 (16:9/9:16/1:1)

Step 2 - 生成 (建议同时跑2-3个变体)
  ✅ 文生视频 + 参考图 → Seedance 2.5 返回 30秒 4K 原生音画
  ✅ 如果有参考视频 → 用 R2V endpoint (bytedance/seedance-2.5/reference-to-video)
  ✅ fal.ai playground 可快速试验 → 满意后 lift as Python/cURL code

Step 3 - 后处理 (CapCut/剪映)
  ✅ 导入 Seedance 2.5 的 MP4 成片
  ✅ 智能剪口播 (剪掉 Seedance 生成的口播中不自然的片段)
  ✅ AI音效 (自动匹配电影级音效)
  ✅ 智能调色 (色轮/HSL/曲线)
  ✅ 关键帧 (补充额外运镜)
  ✅ 数字人 (如果要加讲解/旁白, 用剪映数字人)

Step 4 - 输出发布
  ✅ 清晰度: 4K (Seedance 输出) 或 1080p (发布优化)
  ✅ 比例: 抖音/快手 9:16, B站 16:9, 小红书 3:4
  ✅ 剪映自动字幕 → 导出 SRT → FFmpeg 烧录 → 发布Ready""",
        "source": "jimeng.jianying.com / capcut.cn",
    },
]

# ─────────────────────────────────────────────────────────────
# Skill 库: 剪映 6.0 AI 能力
# ─────────────────────────────────────────────────────────────

CAPCUT_60_SKILLS = [
    {
        "category": "video_editing_sop",
        "title": "剪映 6.0 AI 工具全景 (20+ 个工具分类)",
        "content": """剪映 6.0 AI 工具按功能分 5 大类:

【脚本生成类】
  ✅ AI Story Generator (剧本→对话→分镜全链路)
  ✅ 智能解说粗剪 (生成解说词 + 自动剪切成粗剪版)
  ✅ 智能剪口播 (对着文本剪口播, 识别无效词)
  ✅ AI Writer (自动写文案/脚本)

【视频生成类】
  ✅ AI Video Generator (Seedance 2.5 后端, 30秒 4K 原生长镜头)
  ✅ AI Avatar (100+ 数字人形象, 支持定制形象)
  ✅ AI Portrait Generator (AI 肖像, 任意风格)
  ✅ AI Sticker Generator (定制贴纸)
  ✅ AI Background Changer (AI 换背景)
  ✅ AI Background Expand (AI 拓展背景)
  ✅ AI Design (AI 海报/广告设计)

【语音音频类】
  ✅ 文本朗读 (热门音色 + 音色克隆)
  ✅ AI Voice Generator (最拟人的 AI 配音)
  ✅ 音色克隆 (上传一段你的声音, 克隆出你的 AI 声音)
  ✅ 人声分离 (一键提取人声, 去掉背景音乐)
  ✅ 音频降噪 (过滤环境噪声)
  ✅ 人声美化 (变磁性/变圆润)
  ✅ AI音效 (智能匹配电影级音效)
  ✅ 响度统一 (统一到行业标准)

【画面增强类】
  ✅ 超清画质修复 (一键画质增强)
  ✅ AI补帧 (提升帧率, 增强流畅度)
  ✅ 智能抠像 (识别人像, 抠除背景)
  ✅ 智能调色 (一键色彩调整)
  ✅ 美颜美体 (单/多人, 美颜+身形)

【剪辑效率类】
  ✅ 智能搜索素材 (精准识别+定位素材)
  ✅ 多机位自动对齐 (4/9 机位模式)
  ✅ 关键帧自动生成 (起点+终点→流畅过渡)
  ✅ 多时间线 (一个草稿最多 50 条时间线)

免费功能: 大部分 AI 工具免费. 
付费版 (剪映 Pro): 高级调色/多机位/50条时间线/无损云空间""",
        "source": "capcut.cn / capcut.com/tools/ai-tools",
    },
    {
        "category": "workflow_sop",
        "title": "剪映 AI 一键成片流程 (文字想法 → 发布视频)",
        "content": """最简工作流: 1个想法 → 10分钟 → 发布Ready

Step 1 - 描述想法
  剪映首页 → "AI视频生成" → 输入: 
  "我想做一条关于xxx的15秒抖音视频, 风格是xxx, 节奏要快"
  → AI 自动生成: 剧本 + 分镜表 + 配音脚本 + 建议素材

Step 2 - AI 生成视频
  选择 Seedance 2.5 模型 (30秒 4K 原生长镜头)
  → 直接出完整视频 (有画面+有声音)
  
Step 3 - AI 后期增强
  ✅ 智能剪口播 (自动剪掉 AI 生成口播中不自然的段落)
  ✅ AI音效 (匹配电影级音效)
  ✅ 智能调色 (一键色彩风格)
  ✅ 自动字幕 (识别口播生成 SRT)
  ✅ 关键帧 (自动生成运镜补充)
  
Step 4 - 数字人 (可选)
  如果要讲解/旁白但没时间录:
  数字人 → 选 100+ 形象 → 克隆你自己的声音 → 输入文字 → 自动出说话头部视频
  
Step 5 - 发布
  剪映自动适配: 抖音 9:16 / B站 16:9 / 小红书 3:4 / 视频号
  一键上传 (剪映内置平台对接)

时间估算:
  简单创意 (直接用 AI): 10-15 分钟
  中等创意 (有参考素材): 30-45 分钟
  复杂创意 (定制形象/声音): 1-2 小时""",
        "source": "capcut.cn",
    },
    {
        "category": "comparative_analysis",
        "title": "2026 年 AI 视频工具 Top 6 对比 (剪映 vs 即梦 vs HeyGen)",
        "content": """| 工具 | 定位 | 最强点 | 定价 |
|------|------|--------|------|
| 剪映 CapCut | 全能一站式 | 对话式 AI 创作助手, 脚本→成片全链路 | 免费+Pro |
| 即梦 Seedance 2.5 | 视频生成模型 | 30秒原生长镜头 + 4K + 音画同步 | 按量计费 |
| HeyGen | 数字人专家 | 40+ 语言 + 企业级数字人 | $24/月起 |
| Runway Gen-3 | 好莱坞级 | 电影画质 + 多模态精确控制 | $12/月起 |
| Pika 3 | 动画/漫画 | 动画效果最好 + 风格转移 | $10/月起 |
| Kling 2.6 | 国产最强 | 角色一致性最好 + 真人脸效果 | 按量计费 |

选型建议:
  个人自媒体 → 剪映 (免费够用) + 即梦 Seedance 2.5 (生成视频)
  企业/品牌 → HeyGen (数字人) + Runway (广告片) + 剪映 (后期)
  创作者/设计师 → Runway (电影感) + Kling (真人) + 剪映 (剪辑)
  电商/带货 → 即梦 Seedance 2.5 (商品视频) + 剪映 (字幕/调色)

仙女座 pipeline 定位:
  已有: FFmpeg + MoviePy + Edge-TTS (零 API 本地 pipeline)
  升级目标: 接入 Seedance 2.5 API (当需要高质量成片时)
           用剪映导出的草稿 JSON → 程序化控制剪映 (如果需要)""",
        "source": "capcut.com/resource/top-6-ai-video-generators",
    },
]

# ─────────────────────────────────────────────────────────────
# 写入脑库 + 图谱 + 演化
# ─────────────────────────────────────────────────────────────

def ingest_to_brain(all_skills):
    """把所有 skill 写入脑库 + 图谱 + 触发演化"""
    conn = db()
    ts = time.time()
    
    brain_count = 0
    node_count = 0
    rel_count = 0
    
    # Skill Group 节点
    for group_name in ["jimeng_seedance_25", "jianying_capcut_60"]:
        gid = f"SKILLGROUP-{hashlib.md5(group_name.encode()).hexdigest()[:8]}"
        conn.execute("""
            INSERT OR IGNORE INTO knowledge_graph_nodes
            (node_id, node_name, node_type, content, metadata, 
             importance_score, is_active, created_at, updated_at)
            VALUES (?, ?, 'BRAINCATEGORY', ?, ?, 0.90, 1, ?, ?)
        """, (gid, group_name, f"Skill Group: {group_name}",
              json.dumps({"source": "jimeng/capcut", "category": group_name}, ensure_ascii=False),
              ts, ts))
        node_count += 1
    
    # 每个 skill → 脑库 + 节点 + 关系
    for skill in all_skills:
        kid = f"SEEDCAP-{uuid.uuid4().hex[:8]}"
        nid = f"KNOWLEDGE-{hashlib.md5(skill['title'].encode()).hexdigest()[:10]}"
        group = "jimeng_seedance_25" if "Seedance" in skill["title"] else "jianying_capcut_60"
        gid = f"SKILLGROUP-{hashlib.md5(group.encode()).hexdigest()[:8]}"
        
        # 脑库
        conn.execute("""
            INSERT OR IGNORE INTO ai_brain_enhanced_knowledge
            (knowledge_id, category, title, content, knowledge_type, tags,
             confidence_score, usage_count, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 0.95, 0, 1, ?, ?)
        """, (kid, skill["category"], skill["title"], skill["content"],
              "seedance_capcut_skill",
              json.dumps([group, skill["category"], "jimeng", "capcut", "andromeda_learned"], ensure_ascii=False),
              ts, ts))
        brain_count += 1
        
        # 知识图谱节点
        conn.execute("""
            INSERT OR IGNORE INTO knowledge_graph_nodes
            (node_id, node_name, node_type, content, metadata, 
             importance_score, is_active, created_at, updated_at)
            VALUES (?, ?, 'knowledge', ?, ?, 0.88, 1, ?, ?)
        """, (nid, skill["title"][:40], skill["content"][:200],
              json.dumps({"skill_group": group, "source": skill.get("source", "web")}, ensure_ascii=False),
              ts, ts))
        node_count += 1
        
        # BELONGS_TO 关系
        rid = f"REL-{hashlib.md5((nid+gid).encode()).hexdigest()[:10]}"
        conn.execute("""
            INSERT OR IGNORE INTO knowledge_graph_relations
            (relation_id, source_node_id, target_node_id, relation_type, 
             weight, description, is_active, created_at)
            VALUES (?, ?, ?, 'BELONGS_TO', 0.92, ?, 1, ?)
        """, (rid, nid, gid, f"{skill['title'][:20]} ∈ {group}", ts))
        rel_count += 1
    
    conn.commit()
    conn.close()
    return brain_count, node_count, rel_count

# ─────────────────────────────────────────────────────────────
# 主
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("🎓 仙女座 AI 员工 · 向即梦 Seedance 2.5 + 剪映学习 Skill")
    print(f"   时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    all_skills = SEEDANCE_25_SKILLS + CAPCUT_60_SKILLS
    print(f"\n📚 学习目标: {len(SEEDANCE_25_SKILLS)} Seedance 2.5 + {len(CAPCUT_60_SKILLS)} 剪映 6.0 = {len(all_skills)} 条 Skill")
    
    # 写入脑库
    brain_count, node_count, rel_count = ingest_to_brain(all_skills)
    print(f"\n✅ 写入完成: 脑库 +{brain_count}, 图谱节点 +{node_count}, 关系 +{rel_count}")
    
    # 触发演化
    print(f"\n🔔 触发仙女座演化引擎...")
    try:
        sys.path.insert(0, _PROJECT_ROOT)
        from engines.trigger_evolution_broadcast import trigger_evolution_broadcast
        trigger_evolution_broadcast(f"learned_{brain_count}_jimeng_capcut_skills",
                                    trigger_type="brain_new_knowledge", source="jimeng_capcut_learner")
        trigger_evolution_broadcast("seedance_capcut_skill_group_expand",
                                    trigger_type="ai_skill_level_change", source="jimeng_capcut_learner")
        print("  ✅ 演化广播已发送 (L1-direct)")
    except Exception as e:
        print(f"  ⚠️ 演化触发异常: {e}")
    
    # 最终快照
    conn = db()
    total_brain = conn.execute("SELECT COUNT(*) FROM ai_brain_enhanced_knowledge").fetchone()[0]
    print(f"\n📈 脑库总量: {total_brain:,}")
    conn.close()
    
    print("\n🎉 学习完成! 仙女座现在能回答:")
    print("   'Seedance 2.5 怎么用 Python API?'")
    print("   '剪映数字人怎么接入?'")
    print("   '30秒原生长镜头怎么做角色一致性?'")
    print("   '即梦 vs 剪映 vs Runway 选哪个?'")
    print("   'AI 视频 2026 Top 6 对比'")

if __name__ == "__main__":
    main()
