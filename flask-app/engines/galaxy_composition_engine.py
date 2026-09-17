"""
仙女座星系子系统 — AI 自由组合创作引擎 (v23.2.0)

flow_id: galaxy_composition_engine
version: v23.2.0
核心思想:
  从 25 域 33,525 个 AI 员工中动态组队 → 按公式配方产出 production_spec → 合规 → 多平台发布

Agent Swarm 8 种组合公式 (可扩展):
  1. 历史老师 × 动画 AI × EigenFlux → 历史事件讲解 (动效可爱风)
  2. 科学老师 × 爆点设计 × EigenFlux → 科学原理可视化 (爆炸效果风)
  3. 编程 AI × UI 设计 × 知识图谱 → 编程技巧演示 (代码+动效)
  4. 生活科普 × 创意文案 × 情感配乐 → 生活小知识 (治愈风)
  5. 国学老师 × 水墨动画 × 书法 AI → 国学经典讲解 (国风)
  6. 专家团队 × 热点追踪 × 评论 AI → 热点事件快评 (专业分析)
  7. 数学老师 × 几何动画 × 趣味叙事 → 数学之美 (可视化)
  8. 英语老师 × 角色配音 × 情景动画 → 英语情景剧 (趣味)

Custom 模式: 用户可以手动传自定义角色组合 (e.g. ['narrator','musician','code_explainer'])
"""
import hashlib
import json
import os
import re
import sqlite3
import sys
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, 'database', 'app.db')


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH, timeout=15)
    c.execute('PRAGMA journal_mode=WAL')
    c.row_factory = sqlite3.Row
    return c


# ============================================================
# 8 种组合公式配方
# ============================================================

COMPOSITION_FORMULAS = {
    'f_history_cute': {
        'name': '历史讲解 · 可爱动画风',
        'description': '历史老师 + 动画AI + EigenFlux专家 → 重要历史事件',
        'role_kit': {
            'narrator': '历史叙事者 (讲故事风格)',
            'animator': '可爱动画设计师 (Q版/卡通风)',
            'explainer': '知识点讲解者 (简单类比)',
            'effects': '爆炸特效师 (关键帧动效)',
        },
        'explosion_style': 'cute_burst',
        'platforms': ['douyin', 'xiaohongshu'],
        'target_duration_sec': 45,
        'hot_score_base': 75,
    },
    'f_science_burst': {
        'name': '科学原理 · 爆炸效果风',
        'description': '科学老师 + 爆点设计 + EigenFlux专家 → 原理可视化',
        'role_kit': {
            'narrator': '科学叙事者 (悬念开场)',
            'visualizer': '原理可视化师 (几何/粒子)',
            'designer': '爆点设计师 (高光时刻)',
            'effects': '爆炸特效师 (粒子/能量环)',
        },
        'explosion_style': 'energy_burst',
        'platforms': ['douyin', 'bilibili'],
        'target_duration_sec': 60,
        'hot_score_base': 80,
    },
    'f_code_demo': {
        'name': '编程技巧 · 代码动效风',
        'description': '编程AI + UI设计 + 知识图谱 → 代码技巧演示',
        'role_kit': {
            'coder': '代码演示者 (最佳实践)',
            'designer': '界面动效师 (代码高亮/执行)',
            'explainer': '原理解释者 (为什么这样写)',
        },
        'explosion_style': 'code_flash',
        'platforms': ['douyin', 'bilibili', 'xiaohongshu'],
        'target_duration_sec': 90,
        'hot_score_base': 65,
    },
    'f_life_healing': {
        'name': '生活科普 · 治愈风',
        'description': '生活科普 + 创意文案 + 情感配乐 → 生活小知识',
        'role_kit': {
            'narrator': '治愈叙事者 (温暖声音)',
            'designer': '生活动画师 (简约可爱)',
            'musician': 'BGM推荐师 (治愈系配乐)',
        },
        'explosion_style': 'soft_glow',
        'platforms': ['xiaohongshu', 'douyin'],
        'target_duration_sec': 30,
        'hot_score_base': 70,
    },
    'f_guochao': {
        'name': '国学经典 · 水墨国风',
        'description': '国学老师 + 水墨动画 + 书法AI → 经典讲解',
        'role_kit': {
            'scholar': '国学学者 (正典释义)',
            'animator': '水墨动画师 (留白/意境)',
            'calligrapher': '书法设计师 (手写风格)',
        },
        'explosion_style': 'ink_spread',
        'platforms': ['bilibili', 'xiaohongshu'],
        'target_duration_sec': 60,
        'hot_score_base': 72,
    },
    'f_hotspot_review': {
        'name': '热点快评 · 专业分析风',
        'description': '专家团队 + 热点追踪 + 评论AI → 热点事件快评',
        'role_kit': {
            'analyst': '热点分析师 (多角度拆解)',
            'commentator': '评论员 (犀利观点)',
            'designer': '信息图设计师 (数据可视化)',
        },
        'explosion_style': 'data_burst',
        'platforms': ['douyin', 'bilibili'],
        'target_duration_sec': 120,
        'hot_score_base': 85,
    },
    'f_math_beauty': {
        'name': '数学之美 · 几何可视化',
        'description': '数学老师 + 几何动画 + 趣味叙事 → 数学之美',
        'role_kit': {
            'narrator': '数学叙事者 (生活类比)',
            'visualizer': '几何动画师 (分形/对称)',
            'explainer': '原理讲解者 (直觉化)',
        },
        'explosion_style': 'fractal_burst',
        'platforms': ['bilibili', 'douyin'],
        'target_duration_sec': 75,
        'hot_score_base': 70,
    },
    'f_english_drama': {
        'name': '英语情景剧 · 趣味配音',
        'description': '英语老师 + 角色配音 + 情景动画 → 情景剧',
        'role_kit': {
            'teacher': '英语老师 (场景化语法)',
            'voice_actor': '配音演员 (多角色)',
            'animator': '情景动画师 (角色互动)',
        },
        'explosion_style': 'emotion_burst',
        'platforms': ['xiaohongshu', 'bilibili'],
        'target_duration_sec': 60,
        'hot_score_base': 60,
    },
}


# ============================================================
# 话题 → 公式 匹配 (丰富关键词库)
# ============================================================

TOPIC_KEYWORDS = {
    'f_history_cute': [
        # 朝代
        '秦', '汉', '唐', '宋', '元', '明', '清', '夏', '商', '周', '春秋', '战国', '三国',
        # 人物
        '皇帝', '秦始皇', '刘邦', '李世民', '武则天', '康熙', '乾隆', '岳飞', '诸葛亮',
        '孔子', '老子', '屈原', '李白', '杜甫',
        # 事件
        '统一', '起义', '革命', '战役', '变法', '贞观之治', '开元盛世',
        # 通用
        '历史', '古代', '历史事件', '中国史', '世界史', '史话', '古人', '朝代',
        '历史人物', '历史故事', '历史课', '历史学', '历史上', '史记', '资治通鉴',
    ],
    'f_science_burst': [
        '科学', '物理', '化学', '生物', '原理', '实验', '粒子', '量子', '牛顿', '爱因斯坦',
        '相对论', '黑洞', '引力', '电磁', '化学反应', '生物进化', 'DNA', '基因',
        '自然科学', '科学原理', '科学实验', '是什么原理', '物理原理', '元素周期',
    ],
    'f_code_demo': [
        'python', 'Python', '代码', '编程', '函数', '算法', '程序员', '开发', 'debug',
        'bug', 'github', '开源', 'API', '框架', '数据结构', '计算机', 'IT', '技术',
        'list', 'dict', '循环', '递归', '面向对象', 'web开发', '前端', '后端',
    ],
    'f_life_healing': [
        '生活', '小技巧', '治愈', '日常', '健康', '美食', '旅行', '职场', '学习方法',
        '效率', '情绪', '压力', '放松', '小妙招', '生活方式', '日常用品',
    ],
    'f_guochao': [
        '国学', '论语', '诗词', '中国传统', '书法', '水墨画', '国画', '京剧', '武术',
        '道德经', '庄子', '孔子', '孟子', '唐诗', '宋词', '古文', '经典', '国风',
        '传统文化', '东方美学',
    ],
    'f_hotspot_review': [
        '热点', '事件', '新闻', '评论', '最新', '突发', '现状', '趋势', '争议',
        '热议', '热搜', '爆发', '新政策', '改革', '发布',
    ],
    'f_math_beauty': [
        '数学', '几何', '公式', '代数', '函数', '概率', '统计', '微积分', '斐波那契',
        '黄金比例', '圆', '三角形', '分形', '对称', '拓扑', '数学之美', '数学原理',
        'π', '圆周率',
    ],
    'f_english_drama': [
        '英语', '英文', '口语', 'grammar', '语法', '单词', '词汇', '音标', '听力',
        'CET', '四六级', '雅思', '托福', '商务英语', '日常英语', '情景英语',
    ],
}


def _match_formula(topic: str) -> str:
    """按关键词命中密度选公式 (命中数最多者胜出)"""
    scores = {}
    for fid, keywords in TOPIC_KEYWORDS.items():
        scores[fid] = sum(1 for k in keywords if k in topic)
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return random.choice(list(COMPOSITION_FORMULAS.keys()))


# ============================================================
# 虚拟角色 → employee_type 候选池
# ============================================================

ROLE_CANDIDATES = {
    'narrator':      ['copy_write', 'listening_generate', 'eigenflux_expert'],
    'animator':      ['design_ingest', 'beautify_plan', 'ui_designer', 'eigenflux_expert'],
    'explainer':     ['knowledge_curator', 'knowledge_ingest', 'eigenflux_expert'],
    'effects':       ['design_ingest', 'beautify_plan', 'eigenflux_expert'],
    'visualizer':    ['design_ingest', 'beautify_plan', 'eigenflux_expert'],
    'designer':      ['design_ingest', 'beautify_plan', 'ui_designer', 'eigenflux_expert'],
    'coder':         ['code_review', 'eigenflux_expert'],
    'musician':      ['beautify_plan', 'listening_generate', 'eigenflux_expert'],
    'scholar':       ['knowledge_curator', 'knowledge_ingest', 'eigenflux_expert'],
    'calligrapher':  ['design_ingest', 'ui_designer', 'eigenflux_expert'],
    'analyst':       ['incident_analyze', 'knowledge_curator', 'eigenflux_expert'],
    'commentator':   ['copy_write', 'eigenflux_expert'],
    'teacher':       ['curriculum_designer', 'knowledge_ingest', 'eigenflux_expert'],
    'voice_actor':   ['listening_generate', 'eigenflux_expert'],
}


def sample_team(formula_id: str, topic: str = '', seed: int = None,
                custom_roles: List[str] = None) -> List[Dict]:
    """
    从 employee_registry 抽样组队 + 虚拟角色分配

    custom_roles: 自定义角色 (e.g. ['narrator','musician','coder'])
    """
    formula = COMPOSITION_FORMULAS[formula_id]
    random.seed(seed or hash(f"{formula_id}_{topic}_{datetime.now().timestamp()}") % (2**31))

    roles_needed = custom_roles or list(formula['role_kit'].keys())
    role_label_map = formula['role_kit']
    conn = _conn()
    team = []
    used_etypes = set()

    for role in roles_needed:
        candidates = ROLE_CANDIDATES.get(role, ['eigenflux_expert'])
        picked = None
        for etype in candidates:
            if etype in used_etypes and etype != 'eigenflux_expert':
                continue
            row = conn.execute("""
                SELECT employee_id, name, employee_type, level, neuralhub_task
                FROM mt_andromeda_employee_registry
                WHERE employee_type=? AND enabled=1
                ORDER BY call_count ASC, RANDOM()
                LIMIT 1
            """, (etype,)).fetchone()
            if row:
                picked = dict(row)
                used_etypes.add(etype)
                break
        if not picked:
            row = conn.execute("""
                SELECT employee_id, name, employee_type, level, neuralhub_task
                FROM mt_andromeda_employee_registry
                WHERE employee_type='eigenflux_expert' AND enabled=1
                ORDER BY RANDOM() LIMIT 1
            """).fetchone()
            picked = dict(row) if row else None

        if picked:
            picked['virtual_role'] = role
            picked['role_label'] = role_label_map.get(role, role)
            team.append(picked)

    conn.close()
    return team


def roll_team_for_topic(topic: str, domain_hint: str = None,
                        custom_roles: List[str] = None,
                        custom_formula_id: str = None) -> Tuple[str, Dict]:
    """
    topic → 选公式 + 组队

    custom_formula_id: 强制公式 (不自动匹配)
    custom_roles: 自定义角色组合 (不限公式 role_kit)
    """
    fid = custom_formula_id or _match_formula(topic)
    team = sample_team(fid, topic, custom_roles=custom_roles)
    formula = COMPOSITION_FORMULAS[fid]

    return fid, {
        'formula_id': fid,
        'formula_name': formula['name'],
        'team_size': len(team),
        'members': [
            {
                'employee_id': m['employee_id'],
                'name': m['name'],
                'employee_type': m['employee_type'],
                'virtual_role': m.get('virtual_role', 'support'),
                'role_label': m.get('role_label', '支持'),
            }
            for m in team
        ],
        'explosion_style': formula['explosion_style'],
        'target_platforms': formula['platforms'],
        'target_duration_sec': formula['target_duration_sec'],
        'hot_score_target': formula['hot_score_base'] + random.randint(-5, 10),
    }


# ============================================================
# 爆点素材库 (production_spec 生成时抽样)
# ============================================================

HOOK_TEMPLATES = {
    'f_history_cute':    ["停！{subject}居然是这样！", "{subject}里的你可能没注意到的细节", "看完你会重新认识{subject}", "{subject}被遗忘了很久"],
    'f_science_burst':   ["{subject}为什么这么神奇？", "关于{subject} 不少朋友可能没搞懂", "用{subject}做实验 很有意思", "科学家研究{subject}后发现了什么"],
    'f_code_demo':       ["一行代码搞定{subject}！", "{subject}还能这么写？", "Python 中很实用的{subject}", "这个{subject}技巧 效率更高"],
    'f_life_healing':    ["{subject}居然是这个原因", "生活中的{subject} 你注意到了吗", "治愈你的{subject}小妙招", "每天 3 分钟 {subject} 变轻松"],
    'f_guochao':         ["古人的{subject} 今人不太记得了", "《{subject}》里藏着的智慧", "中国千年{subject} 很美", "为什么{subject}能流传千年"],
    'f_hotspot_review':  ["{subject}事件 快速看懂", "{subject}背后 不只是表面", "专家视角 {subject}怎么看", "{subject} 我们需要想的更深"],
    'f_math_beauty':     ["{subject}居然这么美！", "用{subject}画出整个宇宙", "数学里的{subject} 值得看看", "一条{subject}公式 诠释自然"],
    'f_english_drama':   ["{subject}这个场景 英文怎么说", "3 分钟学会{subject}常用语", "老外常用的{subject}表达", "看情景学{subject} 记忆更深"],
}

STORYBOARD_TEMPLATE = [
    {'shot': 1, 'duration_pct': 0.10, 'role': 'hook',    'desc': '悬念开场',   'visual': 'close_up', 'anim': 'zoom_in'},
    {'shot': 2, 'duration_pct': 0.20, 'role': 'setup',   'desc': '问题展开',   'visual': 'wide',     'anim': 'pan'},
    {'shot': 3, 'duration_pct': 0.25, 'role': 'explain',  'desc': '核心讲解',   'visual': 'medium',   'anim': 'fade'},
    {'shot': 4, 'duration_pct': 0.20, 'role': 'burst',    'desc': '爆炸效果',   'visual': 'close_up', 'anim': 'explode'},
    {'shot': 5, 'duration_pct': 0.15, 'role': 'review',   'desc': '总结回顾',   'visual': 'wide',     'anim': 'tilt'},
    {'shot': 6, 'duration_pct': 0.10, 'role': 'cta',      'desc': '互动引导',   'visual': 'close_up', 'anim': 'pop_in'},
]

HOT_TAGS = {
    'douyin':    ['知识分享', '科普', '历史', '数学之美', '程序员日常', 'AI生成', '原创动画'],
    'xiaohongshu': ['学习笔记', '治愈', '国风', '知识干货', 'AI工具', '自我提升'],
    'bilibili':  ['知识区', '原创动画', '技术分享', '历史区', '硬核科普', 'AI创作'],
}
ACTIVITY_TAGS = {
    'douyin':    ['#抖音知识节', '#douyin_edu_2026', '#创作者激励计划'],
    'xiaohongshu': ['#小红书教育', '#xhs_creator_support', '#知识创作者'],
    'bilibili':  ['#知识区创作者', '#bili_college', '#up主激励计划'],
}


# ============================================================
# 本地 Ollama 调用 (失败返回空)
# ============================================================

def _ollama_chat(prompt: str, system: str = '', timeout: int = 30) -> str:
    try:
        import urllib.request
        payload = json.dumps({
            "model": "qwen2.5:14b",
            "prompt": (system + "\n" + prompt).strip(),
            "stream": False,
            "options": {"temperature": 0.7}
        }).encode()
        req = urllib.request.Request(
            "http://localhost:11435/api/generate",
            data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())['response']
    except Exception:
        return ""


# ============================================================
# 核心: production_spec 生成
# ============================================================

def generate_production_spec(topic: str, formula_id: str = None,
                             custom_roles: List[str] = None,
                             use_ollama: bool = True) -> Dict:
    """
    topic → formula + team + production_spec

    production_spec 下游对接: MoviePy/Manim/剪映 的结构化输入
    """
    fid, team_info = roll_team_for_topic(topic, custom_roles=custom_roles,
                                         custom_formula_id=formula_id)
    formula = COMPOSITION_FORMULAS[fid]
    team = sample_team(fid, topic, custom_roles=custom_roles)

    # 2. Ollama 生成脚本 (或模板 fallback)
    hook = ''; narration = ''; cta = ''

    if use_ollama:
        prompt = (
            f"你是一个短视频创作团队 (历史叙事者+可爱动画设计师+知识点讲解者+爆炸特效师)。"
            f"围绕「{topic}」写一段口语化的短视频脚本, 风格: {formula['name']}。"
            f"严格按 JSON 格式输出: "
            f'{{"hook": "3-8字吸睛开场", "narration": "150-300字核心讲解 口语化 生活化类比", "cta": "一句话引导互动"}}'
            f"注意: 禁止使用 '第一' '最' '顶级' '唯一' '极致' '100%' 等广告法极限词。"
        )
        resp = _ollama_chat(prompt)
        if resp:
            try:
                obj = json.loads(resp[resp.find('{'):resp.rfind('}')+1])
                hook = obj.get('hook', '')
                narration = obj.get('narration', '')
                cta = obj.get('cta', '')
            except Exception:
                pass

    # fallback 模板
    hook_tpl = random.choice(HOOK_TEMPLATES.get(fid, HOOK_TEMPLATES['f_history_cute']))
    hook = hook or hook_tpl.format(subject=topic)
    narration = narration or (
        f"咱们今天聊聊{topic}。这个话题看似平常, 其实背后的故事非常有意思。"
        f"{topic}之所以让人着迷, 是因为它连接着我们熟悉的生活场景。"
        f"让我们一起来看看它究竟是怎么回事吧。"
    )
    cta = cta or f"你对{topic}有什么看法? 欢迎留言分享~"

    # ============ 平台社区规范违禁话术兜底替换 ============
    # 真实平台 (抖音/xhs/B站) 都会拦的诱导/夸张话术 → 合规平替
    PLATFORM_FORBIDDEN_MAP = {
        # 极限词 (广告法)
        '第一': '很早的', '最': '挺', '顶级': '不错的', '唯一': '独特',
        '极致': '精彩', '100%': '大部分', '绝对': '通常',
        '首次': '较早的一次', '空前': '很有特点', '终极': '核心',
        '全网最': '大家常用的', '翻 N 倍': '更高效',
        # 夸张诱导 (抖音巨量安全词典)
        '99%的人': '不少朋友', '99% 的人': '不少朋友',
        '所有人都': '很多朋友', '所有人不知道': '不少朋友没注意',
        '秘密': '细节', '揭秘': '讲讲',
        '结果炸了': '很有意思', '震惊了': '值得留意',
        # 诱导互动 (三平台通用违禁)
        '评论区说说': '留言分享', '评论区聊聊': '留言交流',
        '评论区见': '欢迎留言', '评论区谈谈': '留言交流',
        '记得收藏': '可以先存着', '赶紧收藏': '可以存一下',
        '点赞关注评论': '欢迎关注支持', '双击': '点赞鼓励',
        '三连': '欢迎支持',
        # 夸张描述
        '美哭': '很美', '看到哭': '值得一看',
        '不看后悔': '值得看看', '看完不后悔': '可以一看',
    }
    def _sanitize(text: str) -> str:
        for bad, good in PLATFORM_FORBIDDEN_MAP.items():
            text = text.replace(bad, good)
        return text
    hook = _sanitize(hook)
    narration = _sanitize(narration)
    cta = _sanitize(cta)

    # 3. 分镜 + 爆炸效果
    duration = formula['target_duration_sec']
    storyboard = []
    explosions = []
    for sb in STORYBOARD_TEMPLATE:
        shot_dur = int(duration * sb['duration_pct'])
        is_burst = sb['role'] == 'burst'
        storyboard.append({
            'shot': sb['shot'],
            'role': sb['role'],
            'duration_sec': shot_dur,
            'description': f"镜头 {sb['shot']}: {sb['desc']} — {topic}",
            'visual_prompt': (
                f"{sb['visual']} close-up, {sb['desc']}, "
                f"{formula['explosion_style']} explosion effect, "
                f"cute cartoon style, 1080p, 30fps"
            ),
            'animation_style': sb['anim'],
            'explosion_effect': is_burst,
        })
        if is_burst or sb['role'] == 'hook':
            explosions.append({
                'effect_type': formula['explosion_style'],
                'trigger_shot': sb['shot'],
                'intensity': random.choice(['low', 'medium', 'high']),
                'description': f"在 {sb['desc']} 处触发 {formula['explosion_style']} 爆炸效果",
            })

    # 4. 标签
    platform_tags = {}; activity_tags = {}
    for plat in formula['platforms']:
        platform_tags[plat] = random.sample(HOT_TAGS.get(plat, []), min(4, len(HOT_TAGS.get(plat, []))))
        activity_tags[plat] = random.sample(ACTIVITY_TAGS.get(plat, []), min(2, len(ACTIVITY_TAGS.get(plat, []))))

    hash_input = f"{topic}_{fid}_{datetime.now().timestamp()}"
    spec = {
        'spec_version': 'v23.2.0',
        'meta': {
            'topic': topic,
            'formula_id': fid,
            'formula_name': formula['name'],
            'team': team_info,
            'team_members_detail': [
                {
                    'employee_id': m['employee_id'], 'name': m['name'],
                    'employee_type': m['employee_type'],
                    'virtual_role': m.get('virtual_role'),
                    'role_label': m.get('role_label'),
                }
                for m in team
            ],
            'explosion_style': formula['explosion_style'],
            'target_platforms': formula['platforms'],
            'target_duration_sec': duration,
            'hot_score_target': formula['hot_score_base'] + random.randint(-5, 10),
            'generated_at': datetime.now().isoformat(),
            'content_hash': hashlib.md5(hash_input.encode()).hexdigest(),
        },
        'script': {
            'hook': hook,
            'body': narration,
            'cta': cta,
            'full_text': f"{hook}\n\n{narration}\n\n{cta}",
        },
        'storyboard': storyboard,
        'voiceover': {
            'total_duration_sec': duration,
            'suggested_voice': (
                'warm_female' if formula['explosion_style'] in ('soft_glow', 'ink_spread')
                else 'energetic_male'
            ),
            'suggested_speed': 1.0 if duration <= 45 else 1.1,
            'bgm_suggestion': (
                'light_inspiring' if formula['explosion_style'] in ('soft_glow', 'ink_spread')
                else 'energetic_trailer'
            ),
        },
        'tags': {
            'platform_tags': platform_tags,
            'activity_tags': activity_tags,
        },
        'explosion_effects': explosions,
    }
    return spec


# ============================================================
# 合规审查 + 落库
# ============================================================

def submit_for_compliance(spec: Dict, content_id: str = None,
                          platforms: List[str] = None) -> Dict:
    """多平台分别合规 → 取最严格 overall"""
    from engines import galaxy_compliance
    content_id = content_id or f"swarm_{spec['meta']['content_hash'][:10]}"
    platforms = platforms or spec['meta']['target_platforms']
    full_text = spec['script']['full_text']

    results = {}
    overall = 'PASS'
    for p in platforms:
        r = galaxy_compliance.run_compliance_pipeline(
            content_id=content_id, content_type='script',
            text=full_text, platform=p
        )
        results[p] = r
        if r['overall'] == 'BLOCK':
            overall = 'BLOCK'
        elif r['overall'] == 'REVIEW' and overall != 'BLOCK':
            overall = 'REVIEW'

    return {
        'content_id': content_id,
        'overall': overall,
        'platform_results': results,
        'spec': spec,
    }


# ============================================================
# 表创建 (幂等) + 落库
# ============================================================

SWARM_TABLES = """
CREATE TABLE IF NOT EXISTS mt_galaxy_swarm_teams (
    swarm_id        TEXT PRIMARY KEY,
    topic           TEXT NOT NULL,
    formula_id      TEXT NOT NULL,
    team_json       TEXT,
    production_spec TEXT,
    compliance_overview TEXT,
    publish_status  TEXT DEFAULT 'pending',
    platforms       TEXT,
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);
"""


def ensure_swarm_tables() -> Dict:
    conn = _conn()
    try:
        conn.executescript(SWARM_TABLES)
        conn.commit()
        cnt = conn.execute("SELECT COUNT(*) FROM mt_galaxy_swarm_teams").fetchone()[0]
        return {'swarm_teams': cnt}
    finally:
        conn.close()


def save_swarm(swarm_id: str, topic: str, formula_id: str,
               team_json: str, spec_json: str,
               compliance_overview: str, platforms: List[str]) -> bool:
    conn = _conn()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO mt_galaxy_swarm_teams
            (swarm_id, topic, formula_id, team_json, production_spec,
             compliance_overview, publish_status, platforms)
            VALUES (?,?,?,?,?,?,?,?)
        """, (swarm_id, topic, formula_id, team_json, spec_json,
              compliance_overview, 'pending', json.dumps(platforms, ensure_ascii=False)))
        conn.commit()
        return True
    finally:
        conn.close()


def list_swarms(limit: int = 50) -> List[Dict]:
    conn = _conn()
    rows = conn.execute("""
        SELECT swarm_id, topic, formula_id, publish_status, platforms, created_at
        FROM mt_galaxy_swarm_teams ORDER BY created_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# CLI 入口
# ============================================================

if __name__ == '__main__':
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='仙女座 AI 自由组合创作引擎 v23.2.0')
    parser.add_argument('cmd', choices=['roll', 'generate', 'list', 'formulas'],
                        help='roll=只组队, generate=完整生成spec+合规+落库, list=历史记录, formulas=8种公式')
    parser.add_argument('--topic', '-t', default='中国历史上最精彩的一战', help='话题')
    parser.add_argument('--formula', '-f', default=None, help='强制公式 ID (不自动匹配)')
    parser.add_argument('--roles', '-r', default=None, help='自定义角色 e.g. narrator,coder,musician')
    parser.add_argument('--ollama', '-o', action='store_true', help='调用本地 Ollama 生成脚本 (默认 False 用模板)')
    args = parser.parse_args()

    ensure_swarm_tables()
    topic = args.topic
    fid = args.formula
    roles = args.roles.split(',') if args.roles else None
    use_ollama = args.ollama

    if args.cmd == 'formulas':
        for f_id, f in COMPOSITION_FORMULAS.items():
            print(f"  {f_id:20s} | {f['name']:30s} | 💥 {f['explosion_style']:15s} | 📱 {f['platforms']}")

    elif args.cmd == 'roll':
        fid2, team = roll_team_for_topic(topic, custom_roles=roles, custom_formula_id=fid)
        print(f"\n🎲 公式: {fid2} — {COMPOSITION_FORMULAS[fid2]['name']}")
        print(f"👥 组队 ({team['team_size']} 人):")
        for m in team['members']:
            print(f"  🔹 {m['name']} ({m['employee_type']}) → 🎭 {m['role_label']}")
        print(f"💥 爆炸风格: {team['explosion_style']}")
        print(f"🎯 目标平台: {team['target_platforms']}")

    elif args.cmd == 'generate':
        print(f"\n⚡ 生成中... topic={topic}, formula={fid or 'auto'}, roles={roles or 'default'}")
        spec = generate_production_spec(topic, formula_id=fid, custom_roles=roles, use_ollama=use_ollama)

        compliance = submit_for_compliance(spec)
        print(f"\n✅ 合规: {compliance['overall']}")
        for p, r in compliance['platform_results'].items():
            print(f"  📱 {p}: {r['overall']}")

        swarm_id = f"swarm_{spec['meta']['content_hash'][:12]}"
        save_swarm(
            swarm_id=swarm_id, topic=topic,
            formula_id=spec['meta']['formula_id'],
            team_json=json.dumps(spec['meta']['team_members_detail'], ensure_ascii=False),
            spec_json=json.dumps(spec, ensure_ascii=False),
            compliance_overview=compliance['overall'],
            platforms=spec['meta']['target_platforms']
        )
        print(f"\n💾 已落库: {swarm_id}")
        print(f"📂 分镜: {len(spec['storyboard'])} 镜头")
        print(f"💥 爆炸效果: {len(spec['explosion_effects'])} 处")
        print(f"🎯 目标时长: {spec['meta']['target_duration_sec']}s")
        print(f"🏷️  平台标签: {spec['tags']['platform_tags']}")
        print(f"🔥 活动标签: {spec['tags']['activity_tags']}")

    elif args.cmd == 'list':
        items = list_swarms()
        print(f"\n📋 历史 swarm ({len(items)} 条):")
        for s in items:
            print(f"  {s['created_at']} | {s['swarm_id'][:20]:20s} | {s['topic'][:25]:25s} | {s['formula_id']:18s} | {s['publish_status']}")
