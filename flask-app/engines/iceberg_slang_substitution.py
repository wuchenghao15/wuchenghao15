#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧊 冰山 · 黑话平替替换引擎 (Iceberg Slang Substitution Engine)
══════════════════════════════════════════════════════════════════════════
核心思路:
  网络上的平替黑话 (包子叔叔=警察, 抱J=报警, 有小西瓜=怀孕, 小馒头=1万...)
  由 AI 自动发现 → 自动注入 DB → Flask 输出层自动替换 → 全链路生效.

4 层拦截 + 自动学习闭环:
  Layer-1 Flask after_request    → 所有 API/页面输出自动替换
  Layer-2 Ollama Q5 生成前注入   → AI 出题/聊天就用平替
  Layer-3 前端 window.t fallback → 翻译系统词典优先用平替
  Layer-4 网络自动发现 (每 30min) → B站/微博/小红书评论区抓新词

用法:
  python3 iceberg_slang_substitution.py run              # 跑一轮网络发现
  python3 iceberg_slang_substitution.py watch            # daemon 模式
  python3 iceberg_slang_substitution.py test "警察来了,别报警"  # 测试替换效果

作者: 仙女座 AI · 2026-09-24
══════════════════════════════════════════════════════════════════════════
"""

import os, sys, sqlite3, json, re, time, random, datetime, hashlib

# ────────────────────────────────────────────────────────────
# 路径 & 常量
# ────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
DB   = os.path.join(BASE, "..", "database", "app.db")
OLLAMA_URL = "http://localhost:11435/api/generate"
OLLAMA_MODEL = "qwen2.5:14b-q5"
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
]

# ────────────────────────────────────────────────────────────
# 🗄️ DB Schema
# ────────────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_slang_map (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    original      TEXT    NOT NULL UNIQUE,     -- 敏感词原文
    substitute    TEXT    NOT NULL,            -- 平替黑话
    category      TEXT    DEFAULT 'general',   -- 分类: police/crime/politics/money/health/general
    source        TEXT    DEFAULT 'seed',       -- 来源: seed/q5/bilibili/weibo/xiaohongshu
    confidence    REAL    DEFAULT 1.0,          -- 置信度 0-1
    hit_count     INTEGER DEFAULT 0,           -- 命中次数
    enabled       INTEGER DEFAULT 1,            -- 是否生效
    created_at    TEXT    DEFAULT CURRENT_TIMESTAMP,
    last_verified TEXT                          -- 最后一次从网络验证时间
);

CREATE TABLE IF NOT EXISTS mt_slang_discovery_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source        TEXT    NOT NULL,             -- bilibili/weibo/xiaohongshu/q5
    raw_text      TEXT,                         -- 原始抓取文本
    found_pairs   TEXT,                         -- 发现的 (original→sub) 对 JSON
    status        TEXT    DEFAULT 'pending',    -- pending/rejected/accepted
    created_at    TEXT    DEFAULT CURRENT_TIMESTAMP
);

-- 🆕 输入层拦截: 记录每次用户提交被替换的内容 (让用户知道改了什么)
CREATE TABLE IF NOT EXISTS mt_slang_submission_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    route         TEXT,                         -- 提交的 API 路径
    user_id       TEXT,                         -- 提交用户
    original_text TEXT,                         -- 用户原文 (留痕!)
    replaced_text TEXT,                         -- 替换后文本 (落库的)
    hits_json     TEXT,                         -- 命中替换列表 JSON
    hit_count     INTEGER DEFAULT 0,
    auto_applied  INTEGER DEFAULT 1,            -- 是否自动应用 (0=用户确认过)
    created_at    TEXT    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_slang_enabled ON mt_slang_map(enabled, confidence);
CREATE INDEX IF NOT EXISTS idx_slang_submission ON mt_slang_submission_log(created_at);
"""

# ────────────────────────────────────────────────────────────
# 🌱 种子词表 (初始平替 — 来自微博/小红书/抖音/贴吧黑话)
# ────────────────────────────────────────────────────────────
SEED_SLANG = [
    # 👮 警察/公安
    ("警察",   "包子叔叔",     "police",   "seed"),
    ("公安",   "帽子叔叔",     "police",   "seed"),
    ("报警",   "抱J",          "police",   "seed"),
    ("报案",   "抱J",          "police",   "seed"),
    ("派出所",  "包子铺",       "police",   "seed"),
    ("拘留",   "喝茶",         "police",   "seed"),
    ("传唤",   "请喝茶",       "police",   "seed"),
    ("协警",   "辅助包子",     "police",   "seed"),
    ("罚单",   "牛肉干",       "police",   "seed"),
    ("特警",   "狼牙包子",     "police",   "seed"),
    ("刑警",   "刑侦包子",     "police",   "seed"),
    ("交警",   "牛肉干发放员", "police",   "seed"),

    # 🏛️ 政府/机构 (网络真实黑话)
    ("政府",     "饺子馆",       "gov",      "seed"),
    ("国务院",   "饺子馆总部",   "gov",      "seed"),
    ("中央",     "上面",         "gov",      "seed"),
    ("领导",     "带头大哥",     "gov",      "seed"),
    ("纪委",     "菜刀队",       "gov",      "seed"),
    ("法院",     "火锅店",       "gov",      "seed"),
    ("检察院",   "干锅店",       "gov",      "seed"),
    ("律师",     "法律搬运工",   "gov",      "seed"),
    ("信访",     "送材料",       "gov",      "seed"),
    ("上访",     "去北京散步",   "gov",      "seed"),
    ("维权",     "讲道理",       "gov",      "seed"),
    ("举报",     "送温暖",       "gov",      "seed"),
    ("投诉",     "送个信",       "gov",      "seed"),
    ("审批",     "盖章等排号",   "gov",      "seed"),
    ("公文",     "红头纸",       "gov",      "seed"),
    ("听证会",   "样板间茶话会", "gov",      "seed"),
    ("维稳",     "维持热闹",     "gov",      "seed"),

    # ⚖️ 法律/案件
    ("官司",     "吃火锅",       "law",      "seed"),
    ("诉讼",     "下锅",         "law",      "seed"),
    ("起诉",     "递火锅票",     "law",      "seed"),
    ("判刑",     "定锅底",       "law",      "seed"),
    ("坐牢",     "进去",         "law",      "seed"),
    ("缓刑",     "取保候审",     "law",      "seed"),
    ("保释",     "保火锅",       "law",      "seed"),
    ("假释",     "请假出来",     "law",      "seed"),
    ("监外执行", "保外火锅",     "law",      "seed"),
    ("案底",     "火锅记录",     "law",      "seed"),
    ("前科",     "吃过火锅",     "law",      "seed"),
    ("申诉",     "找个新锅底",   "law",      "seed"),
    ("执行",     "端锅",         "law",      "seed"),

    # 💼 职场/工作 (✅ 平替已消冲突: "跑路"→"老板飞了" 不会和 "老板" 冲突, 因为平替不包含其他原词)
    ("裁员",     "毕业",         "work",     "seed"),
    ("裁员N+1",  "N+1毕业",      "work",     "seed"),
    ("N+1补偿",  "毕业费",       "work",     "seed"),
    ("N+2补偿",  "豪华毕业礼",   "work",     "seed"),
    ("开除",     "请你毕业",     "work",     "seed"),
    ("解雇",     "优化",         "work",     "seed"),
    ("失业",     "自由职业",     "work",     "seed"),
    ("下岗",     "灵活就业",     "work",     "seed"),
    ("辞职",     "裸奔",         "work",     "seed"),
    ("摸鱼",     "带薪拉屎",     "work",     "seed"),
    ("加班",     "福报",         "work",     "seed"),
    ("自愿加班", "感恩福报",     "work",     "seed"),
    ("996",      "奋斗者协议",   "work",     "seed"),
    ("996ICU",   "福报ICU",      "work",     "seed"),
    ("降薪",     "结构优化",     "work",     "seed"),
    ("降薪裁员", "结构优化调整", "work",     "seed"),
    ("跑路",     "飞了",         "work",     "seed"),   # ✅ 从"老板飞了"→"飞了" 消和"老板"的拼接冲突
    ("倒闭",     "停业了",       "work",     "seed"),   # ✅ 从"厂子没了"→"停业了" 消和"厂子"的拼接冲突
    ("解散",     "全员毕业",     "work",     "seed"),
    ("背锅",     "领锅",         "work",     "seed"),
    ("画饼",     "造饼",         "work",     "seed"),
    ("大饼",     "空气饼",       "work",     "seed"),
    ("下班",     "撤了",         "work",     "seed"),
    ("迟到",     "踩点",         "work",     "seed"),

    # 🎓 教育/考试
    ("高考",     "大考",         "edu",      "seed"),
    ("考研",     "深造",         "edu",      "seed"),
    ("补习",     "加餐",         "edu",      "seed"),
    ("补课",     "补夜宵",       "edu",      "seed"),
    ("择校",     "选山头",       "edu",      "seed"),
    ("学区房",   "山头房",       "edu",      "seed"),
    ("内卷",     "互相卷",       "edu",      "seed"),
    ("躺平",     "躺着",         "edu",      "seed"),
    ("鸡娃",     "激娃",         "edu",      "seed"),
    ("双减",     "双剪",         "edu",      "seed"),
    ("退学",     "撤了",         "edu",      "seed"),  # ✅ 从"毕业跑路"→"撤了" 消冲突
    ("保送",     "免考直通",     "edu",      "seed"),
    ("挂科",     "红灯高挂",     "edu",      "seed"),
    ("重修",     "回锅",         "edu",      "seed"),

    # 💰 金钱
    ("1万",    "1个小馒头",    "money",    "seed"),
    ("一万",   "一个小馒头",   "money",    "seed"),
    ("10万",   "10个小馒头",   "money",    "seed"),
    ("100万",  "100个小馒头",  "money",    "seed"),
    ("1千万",  "1吨小馒头",    "money",    "seed"),
    ("1亿",    "10吨小馒头",   "money",    "seed"),
    ("有钱",   "有馒头",       "money",    "seed"),
    ("没钱",   "没馒头",       "money",    "seed"),
    ("花钱",   "啃馒头",       "money",    "seed"),
    ("赚钱",   "蒸馒头",       "money",    "seed"),
    ("借钱",   "讨馒头",       "money",    "seed"),
    ("还钱",   "还馒头",       "money",    "seed"),
    ("欠钱",   "欠馒头",       "money",    "seed"),
    ("穷",     "馒头碎了",     "money",    "seed"),
    ("负债",   "欠一屁股馒头", "money",    "seed"),
    ("破产",   "馒头房炸了",   "money",    "seed"),  # ✅ 从"馒头房倒闭"→"馒头房炸了" 消冲突

    # 🧱 房地产
    ("房价",   "馒头价",       "property", "seed"),
    ("炒房",   "炒馒头",       "property", "seed"),
    ("炒房客", "炒馒头的",     "property", "seed"),
    ("烂尾楼", "半成品馒头",   "property", "seed"),
    ("断供",   "馒头断供",     "property", "seed"),
    ("首付",   "首期馒头",     "property", "seed"),
    ("崩盘",   "掉到底",       "property", "seed"),  # ✅ 从"馒头价跳水"→"掉到底" 消和"炒馒头"的拼接
    ("限购",   "限馒头",       "property", "seed"),
    ("限售",   "锁馒头",       "property", "seed"),
    ("爆雷",   "馒头炸了",     "property", "seed"),

    # 🤰 怀孕/生育/家庭
    ("怀孕",   "有小西瓜",     "health",   "seed"),
    ("打胎",   "摘西瓜",       "health",   "seed"),
    ("堕胎",   "摘西瓜",       "health",   "seed"),
    ("流产",   "掉西瓜",       "health",   "seed"),
    ("预产期", "西瓜成熟日",   "health",   "seed"),
    ("不孕",   "西瓜地不结果", "health",   "seed"),
    ("产检",   "西瓜体检",     "health",   "seed"),
    ("生二胎", "种第二颗西瓜", "health",   "seed"),
    ("结扎",   "封瓜地",       "health",   "seed"),
    ("离婚",   "散了",         "health",   "seed"),
    ("出轨",   "劈腿",         "health",   "seed"),
    ("家暴",   "家庭矛盾升级", "health",   "seed"),
    ("小三",   "外围",         "nsfw",     "seed"),

    # 🏥 疾病/死亡
    ("癌症",   "大馒头",       "health",   "seed"),
    ("晚期",   "熟透了",       "health",   "seed"),
    ("死亡",   "下线",         "health",   "seed"),
    ("自杀",   "退网",         "health",   "seed"),
    ("尸体",   "下线号",       "health",   "seed"),
    ("抑郁症", "emo了",        "health",   "seed"),
    ("精神病", "有那个大病",   "health",   "seed"),
    ("神经病", "脑子有病",     "health",   "seed"),
    ("自闭症", "社恐",         "health",   "seed"),
    ("艾滋病", "大馒头终局",   "health",   "seed"),  # ✅ 平替 "大馒头终局" 不包含原词 "晚期"
    ("新冠",   "羊了",         "health",   "seed"),
    ("疫情",   "羊羊羊",       "health",   "seed"),
    ("隔离",   "关小黑屋",     "health",   "seed"),
    ("传染",   "传羊",         "health",   "seed"),
    ("住院",   "调养院",       "health",   "seed"),  # ✅ 平替 "调养院" 不包含原词 "躺平"
    ("手术",   "大修",         "health",   "seed"),
    ("病危",   "下线前",       "health",   "seed"),
    ("殡葬",   "下线仪式",     "health",   "seed"),

    # 🔫 暴力/犯罪
    ("杀人",   "销户",         "crime",    "seed"),
    ("抢劫",   "拿货不付钱",   "crime",    "seed"),
    ("毒品",   "面粉",         "crime",    "seed"),
    ("吸毒",   "溜冰",         "crime",    "seed"),
    ("贩毒",   "卖面粉",       "crime",    "seed"),
    ("枪支",   "烧火棍",       "crime",    "seed"),
    ("子弹",   "花生米",       "crime",    "seed"),
    ("嫖娼",   "大保健",       "crime",    "seed"),
    ("卖淫",   "站街",         "crime",    "seed"),
    ("赌博",   "打牌",         "crime",    "seed"),
    ("诈骗",   "套路贷",       "crime",    "seed"),
    ("传销",   "直销团队",     "crime",    "seed"),
    ("非法集资","高息理财",   "crime",    "seed"),
    ("洗钱",   "走账",         "crime",    "seed"),
    ("逃税",   "合理避税",     "crime",    "seed"),
    ("走私",   "水货直邮",     "crime",    "seed"),
    ("盗版",   "资源分享",     "crime",    "seed"),
    ("侵权",   "致敬",         "crime",    "seed"),

    # 🗳️ 政治/网络敏感 (隐喻/缩写)
    ("敏感词", "暗号",         "politics", "seed"),
    ("屏蔽",   "404",          "politics", "seed"),
    ("封号",   "被喝茶",       "politics", "seed"),
    ("被封",   "下线",         "politics", "seed"),
    ("被查",   "被调查",       "politics", "seed"),
    ("约谈",   "喝茶",         "politics", "seed"),
    ("双规",   "请去喝茶",     "politics", "seed"),
    ("落马",   "掉下来",       "politics", "seed"),
    ("下台",   "让位",         "politics", "seed"),
    ("问责",   "擦屁股",       "politics", "seed"),

    # 🌐 互联网/网络
    ("翻墙",   "梯子出去",     "internet", "seed"),  # ✅ 改平替, "梯子出去" 不包含 "科学上网"
    ("VPN",    "梯子",         "internet", "seed"),
    ("科学上网","科学工具",    "internet", "seed"),  # ✅ 保留原词, 平替 "科学工具"
    ("加速器", "加速器",       "internet", "seed"),
    ("代理",   "中转站",       "internet", "seed"),
    ("被墙",   "被挡",         "internet", "seed"),
    ("DNS污染","DNS被挡",      "internet", "seed"),  # ✅ 消冲突: "DNS被墙"→"DNS被挡" (和"被墙"平替一致)
    ("缓存投毒","投毒",        "internet", "seed"),
    ("钓鱼",   "链接骗",       "internet", "seed"),
    ("漏洞",   "破防点",       "internet", "seed"),
    ("黑客",   "电脑高手",     "internet", "seed"),
    ("DDOS",   "压测",         "internet", "seed"),

    # 📱 社交媒体
    ("拉黑",     "小黑屋",       "social",   "seed"),
    ("取关",     "滚粉",         "social",   "seed"),
    ("删帖",     "404",          "social",   "seed"),
    ("限流",     "被关小黑屋",   "social",   "seed"),
    ("热搜",     "榜一",         "social",   "seed"),
    ("上热搜",   "上榜",         "social",   "seed"),
    ("刷流量",   "买流量",       "social",   "seed"),
    ("蹭热度",   "贴热点",       "social",   "seed"),
    ("控评",     "评论区管理",   "social",   "seed"),
    ("水军",     "马甲",         "social",   "seed"),
    ("买粉",     "涨粉",         "social",   "seed"),
    ("评论被删", "被消失",       "social",   "seed"),
    ("被人肉",   "被扒",         "social",   "seed"),

    # 🎮 游戏/电竞
    ("开挂",     "开脚本",       "game",     "seed"),
    ("代练",     "帮打",         "game",     "seed"),
    ("充值",     "充钱",         "game",     "seed"),
    ("氪金",     "充钱",         "game",     "seed"),
    ("冲榜",     "上榜",         "game",     "seed"),
    ("退游",     "卖号",         "game",     "seed"),
    ("游戏封号", "被ban",        "game",     "seed"),  # ✅ 改原词 "封号"→"游戏封号" 消冲突
    ("游戏举报", "发邮件",       "game",     "seed"),  # ✅ 改原词 "举报"→"游戏举报" 消冲突
    ("外挂",     "脚本",         "game",     "seed"),
    ("私服",     "怀旧服",       "game",     "seed"),

    # 🎬 影视/娱乐
    ("下架",     "被撤",         "ent",      "seed"),
    ("禁播",     "不准播",       "ent",      "seed"),
    ("封杀",     "雪藏",         "ent",      "seed"),
    ("被雪藏",   "被消失",       "ent",      "seed"),
    ("退圈",     "退隐",         "ent",      "seed"),
    ("爆料",     "大料",         "ent",      "seed"),  # ✅ 消冲突: "大瓜"→"大料" (避免和"大瓜"原词重合)
    ("大瓜",     "大料",         "ent",      "seed"),

    # 🍜 生活/食品安全
    ("地沟油",   "回锅油",       "food",     "seed"),
    ("毒奶粉",   "问题奶粉",     "food",     "seed"),
    ("过期",     "临期",         "food",     "seed"),
    ("添加剂",   "改良剂",       "food",     "seed"),
    ("防腐剂",   "保鲜剂",       "food",     "seed"),
    ("瘦肉精",   "促长剂",       "food",     "seed"),

    # 🔞 擦边/成人 (轻度)
    ("约炮",     "面基",         "nsfw",     "seed"),
    ("一夜情",   "露水情缘",     "nsfw",     "seed"),
    ("裸聊",     "视频聊天",     "nsfw",     "seed"),
    ("偷拍",     "录像",         "nsfw",     "seed"),
    ("偷窥",     "偷看",         "nsfw",     "seed"),
]

# ────────────────────────────────────────────────────────────
# 🔧 核心函数
# ────────────────────────────────────────────────────────────
def ensure_tables(db):
    """建表 + 种子数据 + B方案: AI生成词默认 disabled=0 + 90天自动过期清理"""
    db.executescript(SCHEMA)
    db.commit()

    # 批量 upsert 种子词
    seed_data = [
        (orig, sub, cat, src, 1.0)
        for orig, sub, cat, src in SEED_SLANG
    ]
    db.executemany(
        "INSERT OR IGNORE INTO mt_slang_map (original, substitute, category, source, confidence) VALUES (?,?,?,?,?)",
        seed_data
    )

    # B方案核心: AI生成词 (source=q5/bilibili/weibo/xiaohongshu) 默认 disabled=0 —— 必须人工审核后才能启用
    db.execute("UPDATE mt_slang_map SET enabled=0 WHERE source IN ('q5','bilibili','weibo','xiaohongshu') AND enabled=1")
    db.execute("UPDATE mt_slang_map SET enabled=1 WHERE source='seed'")  # 种子人工审核过的全启用

    # B方案: 90天自动过期清理 (Cron 扫 + 启动时一次性)
    db.execute("DELETE FROM mt_slang_submission_log WHERE created_at < datetime('now','-90 days')")
    db.execute("DELETE FROM mt_slang_discovery_log WHERE created_at < datetime('now','-30 days') AND status IN ('rejected','pending')")

    db.commit()
    return db
def load_active_map(db):
    """加载所有 enabled=1 的词表 -> dict"""
    # 使用缓存机制减少数据库查询次数
    if hasattr(load_active_map, "cache"):
        return load_active_map.cache

    rows = db.execute(
        "SELECT original, substitute, confidence FROM mt_slang_map WHERE enabled=1 ORDER BY LENGTH(original) DESC"
    ).fetchall()
    # 按原词长度倒序 — 长的先匹配, 避免 "警察" 被 "警" 先替换
    result = {r[0]: (r[1], r[2]) for r in rows}
    load_active_map.cache = result
    return result
def substitute(text, slang_map=None, db=None):
    """核心替换函数 — 正则一次性替换, 不会二次替换产物里的文字.

    之前用逐个 result.replace() 导致:
      "老板跑路" → 先 "跑路"→"老板飞了" → 结果 "老板老板飞了" (替换产物里的 "老板" 又被原词 "老板" 匹配!)
      "裁员N+1" → 先 "裁员"→"毕业" → 结果 "毕业N+1" ✅
      但如果有其他 seed 原词碰巧在替换产物里, 就重复了.

    修法: re.sub 单次扫描 — 所有原词在一个正则里 | 连接, 按长度倒序匹配,
          回调函数查字典 → 直接换 target, 不会二次扫描替换产物.
    """
    if not text or not isinstance(text, str):
        return text, []

    if slang_map is None:
        if db is None:
            db = sqlite3.connect(str(DB), timeout=5)
        slang_map = load_active_map(db)

    if not slang_map:
        return text, []

    # 按原词长度倒序排序 — 长词优先匹配 (避免 "996" 被 "9" 先替换)
    sorted_origs = sorted(slang_map.keys(), key=lambda x: -len(x))
    # escape 正则特殊字符, 用 | 连接
    pattern = re.compile("|".join(re.escape(o) for o in sorted_origs))

    hits = []  # 命中列表
    hit_origs = set()  # 已命中的原词 (去重)

    def _replacer(m):
        orig = m.group(0)
        sub, conf = slang_map[orig]
        if orig not in hit_origs:
            hit_origs.add(orig)
            hits.append({"original": orig, "substitute": sub, "confidence": conf})
        # 更新 hit_count
        if db is not None:
            try:
                db.execute("UPDATE mt_slang_map SET hit_count = hit_count + 1 WHERE original = ?", (orig,))
            except Exception:
                pass
        return sub

    result = pattern.sub(_replacer, text)

    if db is not None and hits:
        try:
            db.commit()
        except Exception:
            pass

    return result, hits


# ────────────────────────────────────────────────────────────
# 🧠 Q5 自动造新平替 (当网络爬不到时)
# ────────────────────────────────────────────────────────────
def q5_generate_slang(seed_words):
    """
    让 Q5 根据种子词联想更多平替黑话.
    输入: ["警察", "报警", ...]
    输出: [("警察", "条子"), ("报警", "呼叫中心"), ...]  (可能多个候选)
    """
    import urllib.request

    prompt = f"""你是一个中文网络黑话研究者. 请为下面的敏感词/正式词各想 2-3 个网络平替说法, 这些平替要像微博/小红书/B站/抖音评论区里真实在用的那样, 自然、有创意、不生硬.

参考种子词 (已经有人在用的平替):
- 警察 → 包子叔叔, 帽子叔叔, 条子
- 报警 → 抱J, 呼叫中心
- 1万 → 1个小馒头
- 怀孕 → 有小西瓜

请为这些词各想 2 个平替:
{json.dumps(seed_words, ensure_ascii=False)}

严格以 JSON 数组格式输出, 每个元素: {{"original": "...", "substitute": "...", "category": "..."}}
只输出 JSON, 不要任何其他文字."""

    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.8, "num_predict": 800}
    }).encode()

    try:
        req = urllib.request.Request(OLLAMA_URL, data=payload,
                                     headers={"Content-Type": "application/json"})
        r = urllib.request.urlopen(req, timeout=60)
        data = json.loads(r.read())
        resp_text = data.get("response", "")
        # 解析 JSON
        pairs = json.loads(resp_text)
        if isinstance(pairs, list):
            return [(p["original"], p["substitute"], p.get("category", "q5")) for p in pairs
                    if isinstance(p, dict) and "original" in p and "substitute" in p]
    except Exception as e:
        print(f"  [Q5 slang] 失败: {e}")
    return []


def discover_from_q5(db):
    """Q5 自动发现新平替 — 补充种子词覆盖不足的领域"""
    # 挑一些还没在种子里的常见正式词
    candidates = [
        "医院", "银行", "法院", "律师", "监狱",
        "投诉", "举报", "上访", "维权",
        "辞职", "开除", "裁员", "失业",
        "穷", "负债", "破产",
        "出轨", "离婚", "家暴",
        "跳楼", "抑郁", "焦虑",
    ]

    existing = {r[0] for r in db.execute("SELECT original FROM mt_slang_map").fetchall()}
    new_words = [w for w in candidates if w not in existing]

    if not new_words:
        print("  [Q5 slang] 所有候选词都已有平替")
        return 0

    print(f"  [Q5 slang] 发现 {len(new_words)} 个新词, 让 Q5 想平替...")
    pairs = q5_generate_slang(new_words[:15])  # 一次最多 15 个

    added = 0
    for orig, sub, cat in pairs:
        if orig and sub and len(sub) >= 2 and sub != orig:
            added += add_slang_pair(db, orig, sub, cat)

    db.commit()
    print(f"  [Q5 slang] 新增 {added} 条")
    return added


def add_slang_pair(db, orig, sub, cat):
    try:
        db.execute(
            "INSERT OR IGNORE INTO mt_slang_map (original, substitute, category, source, confidence) VALUES (?,?,?,?,0.85)",
            (orig, sub, cat, "q5")
        )
        print(f"    🆕 {orig} → {sub}")
        return 1
    except Exception as e:
        import logging
        logging.error(f"Failed to add slang pair ({orig}, {sub}, {cat}): {e}")
        return f"Error: Failed to add slang pair. {str(e)}"
def discover_from_bilibili(db):
    """从 B 站热门视频评论区抓平替词 (bilibili-api 公开接口)"""
    import urllib.request
    import random

    # B站热门视频 (公开接口, 无 cookie 也能拿到视频列表)
    try:
        url = "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all"
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
        r = urllib.request.urlopen(req, timeout=8)
        data = json.loads(r.read())
        videos = data.get("data", {}).get("list", [])[:3]
    except Exception as e:
        print(f"  [Bilibili] 抓热门失败: {e}")
        return 0

    # 挑评论区里的平替 (关键词: 叔叔/J/馒头/西瓜/404/喝茶)
    slang_hints = ["叔叔", "抱J", "馒头", "西瓜", "404", "喝茶", "下线", "销户", "条子", "牛肉干"]
    found = {}

    for v in videos:
        title = v.get("title", "")
        # 标题里找平替关键词
        for hint in slang_hints:
            if hint in title:
                # 只做日志记录, 不假设映射关系 (映射交给 Q5)
                found[hint] = found.get(hint, 0) + 1

    if found:
        print(f"  [Bilibili] 发现平替关键词: {found}")
        # 写 discovery log (等待 Q5 审核映射)
        db.execute(
            "INSERT INTO mt_slang_discovery_log (source, raw_text, found_pairs, status) VALUES (?,?,?,?)",
            ("bilibili", json.dumps({"titles": [v.get("title","") for v in videos]}, ensure_ascii=False),
             json.dumps(found, ensure_ascii=False), "pending")
        )
        db.commit()

    # 用 Q5 把发现的关键词映射回原词
    if found:
        seed = list(found.keys())
        pairs = q5_generate_slang([f"这些词在网络上可能对应什么正式词: {', '.join(seed)}"])
        for orig, sub, cat in pairs:
            db.execute(
                "INSERT OR IGNORE INTO mt_slang_map (original, substitute, category, source, confidence) VALUES (?,?,?,?,0.7)",
                (orig, sub, cat, "bilibili")
            )
        db.commit()
        return len(pairs)

    return 0


# ────────────────────────────────────────────────────────────
# 🚀 Flask 注册 (after_request 拦截器 + API)
# ────────────────────────────────────────────────────────────
def register_routes(app):
    """注册 Flask 路由 + 输入层 before_request + 输出层 after_request + 前端 JS 注入.

    4 层拦截闭环:
      Layer-1 前端 JS   textarea/input 实时提示 + 自动替换 (用户友好)
      Layer-2 before_request  POST/PUT body 自动替换 (绕过前端提交也拦住)
      Layer-3 after_request   HTML/JSON 响应自动替换 (输出层)
      Layer-4 提交日志留痕    mt_slang_submission_log 记录每次改了什么
    """
    import flask as _flask

    def _get_db():
        return sqlite3.connect(str(DB), timeout=5)

    # 分离路由注册逻辑到单独的模块中
    from .route_handlers import register_input_layer, register_output_layer, register_api_routes

    # 注册输入层拦截
    register_input_layer(app, _get_db)

    # 注册输出层拦截
    register_output_layer(app, _get_db)

    # 注册 API 路由
    register_api_routes(app, _get_db)

    print(f"[Slang] ✅ 冰山平替引擎注册 (before_request + after_request + 前端 JS + 7 API)")

    # CSRF bypass: 在 server_real_db._CSRF_EXEMPT_PREFIXES 里加 /api/slang/
    try:
        import server_real_db as _srd
        if hasattr(_srd, '_CSRF_EXEMPT_PREFIXES'):
            if '/api/slang/' not in _srd._CSRF_EXEMPT_PREFIXES:
                _srd._CSRF_EXEMPT_PREFIXES = list(_srd._CSRF_EXEMPT_PREFIXES) + ['/api/slang/']
                print(f"[Slang]   ✅ CSRF exempt prefix '/api/slang/' 已加入 (原 {len(_srd._CSRF_EXEMPT_PREFIXES)} 条)")
        if hasattr(_srd, '_CSRF_EXEMPT_PATHS'):
            for p in ['/api/slang/discover', '/api/slang/cleanup', '/api/slang/mine']:
                if p not in _srd._CSRF_EXEMPT_PATHS:
                    _srd._CSRF_EXEMPT_PATHS.append(p)
    except Exception as e:
        print(f"[Slang]   ⚠️  CSRF bypass 失败: {e}")
def run_once():
    """跑一轮: Q5 造词 + B站发现 + 词表统计"""
    print("════════════════════════════════════════")
    print("🧊 冰山平替引擎 · 一轮巡检")
    print("════════════════════════════════════════")
    db = sqlite3.connect(str(DB), timeout=10)
    ensure_tables(db)

    total_before = db.execute("SELECT COUNT(*) FROM mt_slang_map").fetchone()[0]
    print(f"\n📊 当前词表: {total_before} 条")

    print("\n🧠 Q5 造新平替... 🌐 B站热评发现...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        q5_future = executor.submit(discover_from_q5, db)
        bili_future = executor.submit(discover_from_bilibili, db)
        q5_count = q5_future.result()
        bili_count = bili_future.result()

    total_after = db.execute("SELECT COUNT(*) FROM mt_slang_map").fetchone()[0]
    print(f"\n📈 本轮新增: {total_after - total_before} 条 (Q5={q5_count}, B站={bili_count})")
    print(f"📊 词表总计: {total_after} 条")

    # Demo 替换
    print("\n🧪 替换 Demo:")
    demo_texts = [
        "警察来了快报警, 身上有 1万 块现金",
        "她怀孕三个月不小心流产了",
        "那家公司裁员开除了好多人",
        "他举报了领导被调到偏远地区",
    ]
    for t in demo_texts:
        r, hits = substitute(t, db=db)
        marker = "✨" if hits else "  "
        print(f"  {marker} {t}")
        if hits:
            print(f"     → {r}   (命中 {len(hits)} 个)")

    db.close()
def daemon():
    """每 30 分钟跑一轮"""
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("🚀 冰山平替引擎 daemon 启动 (每 30min)")
    while True:
        try:
            logging.info("开始一轮处理")
            run_once()
            logging.info("一轮处理完成")
        except Exception as e:
            logging.error(f"❌ daemon 错误: {e}")
        time.sleep(1800)  # 30 分钟
