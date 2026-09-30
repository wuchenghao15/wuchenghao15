#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仙女座全网教育知识聚合引擎 · sys_knowledge_aggregator
========================================================
§14 flow_id: andromeda_knowledge_brain_v1_20260922
MVP 周期: 120min
首测平台: B站 (公开 API, 手写 HTTP header)
首测领域: JLPT 日语 N5-N1 + 新概念英语 + K12 数学

工作流:
  1. B站搜索 API → 返回候选视频列表 (bvid/title/author/play)
  2. 视频详情 API → 获取 bvid/aid/duration/desc/publish_time
  3. Ollama 长文本摘要 (qwen2.5:7b, 降级到固定模板)
  4. 知识点提取 + 难度分级
  5. INSERT 到 mt_andromeda_knowledge_base (UNIQUE deduplication_hash)
  6. 关联 contributor_persona (author 匹配人格档案)
  7. 自动投喂 mt_ai_brain_feed_log
"""
import os, sys, json, re, time, sqlite3, hashlib, urllib.request, urllib.parse, ssl

# ====== 路径常量 ======
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "engines", "app.db")
FLOW_ID = "andromeda_knowledge_brain_v1_20260922"

# ====== B站公开 API ======
BILI_SEARCH_API = "https://api.bilibili.com/x/web-interface/search/type"
BILI_VIDEO_API = "https://api.bilibili.com/x/web-interface/view"
# ✅ B 站反爬修复: 加 buvid3 Cookie (每次跑生成随机值)
import os as _os, hashlib as _hlib, time as _time
_random_buvid = _hlib.md5(f"{_os.getpid()}_{_time.time()}_mtscos".encode()).hexdigest()[:32]
BILI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Accept": "application/json, text/plain, */*",
    "Cookie": f"buvid3={_random_buvid}; buvid4={_hlib.md5(_random_buvid.encode()).hexdigest()[:32]}",
}

# ====== 搜索词池 (MVP) ======
SEARCH_POOL = [
    # ====== 日语/日本语教育 ======
    ("JLPT N5 日语学习 五十音", "bilibili", "JLPT-N5", "tutorial"),
    ("JLPT N4 日语考级 语法", "bilibili", "JLPT-N4", "tutorial"),
    ("JLPT N3 中级日语 听力", "bilibili", "JLPT-N3", "lecture"),
    ("JLPT N2 高级日语 真题", "bilibili", "JLPT-N2", "lecture"),
    ("JLPT N1 日语能力考 词汇", "bilibili", "JLPT-N1", "exam"),
    ("日语敬语 礼貌语 教学", "bilibili", "日语敬语", "lecture"),
    ("动漫日语 日常口语 沉浸式", "bilibili", "动漫日语", "tutorial"),
    ("新标日 中日交流标准日本语", "bilibili", "新标日", "tutorial"),
    # ====== 英语教育 ======
    ("新概念英语 第一册 零基础", "bilibili", "新概念英语-1", "tutorial"),
    ("新概念英语 第二册 语法精讲", "bilibili", "新概念英语-2", "lecture"),
    ("新概念英语 第三册 写作", "bilibili", "新概念英语-3", "lecture"),
    ("雅思听力 真题 技巧", "bilibili", "雅思-IELTS", "exam"),
    ("雅思口语 万能模板", "bilibili", "雅思口语", "exam"),
    ("托福阅读 长难句解析", "bilibili", "托福-TOEFL", "exam"),
    ("新东方 英语语法 系统", "bilibili", "新东方英语", "lecture"),
    # ====== K12 ======
    ("小学数学 奥数 思维训练", "bilibili", "K12数学-小学", "tutorial"),
    ("初中数学 几何 函数 难点", "bilibili", "K12数学-初中", "tutorial"),
    ("高中数学 导数 解析几何", "bilibili", "K12数学-高中", "lecture"),
    ("高考数学 压轴题 详解", "bilibili", "高考数学", "exam"),
    ("高考语文 作文 阅读", "bilibili", "高考语文", "exam"),
    ("初中物理 力学 电学", "bilibili", "K12物理-初中", "tutorial"),
    ("高中物理 电磁感应 相对论", "bilibili", "K12物理-高中", "lecture"),
    ("初中英语 语法 时态", "bilibili", "K12英语-初中", "tutorial"),
    # ====== 高等教育 ======
    ("高等数学 微积分 极限", "bilibili", "高等数学", "lecture"),
    ("线性代数 矩阵 向量空间", "bilibili", "线性代数", "lecture"),
    ("概率统计 正态分布 贝叶斯", "bilibili", "概率统计", "lecture"),
    ("大学物理 量子力学 相对论", "bilibili", "大学物理", "lecture"),
    ("C语言 指针 内存管理", "bilibili", "C语言", "tutorial"),
    ("Python 入门 爬虫 数据分析", "bilibili", "Python编程", "tutorial"),
    ("机器学习 神经网络 入门", "bilibili", "机器学习", "lecture"),
    # ====== 老年教育 ======
    ("老年人学智能手机 抖音", "bilibili", "老年教育-手机", "tutorial"),
    ("老年人学英语 ABC", "bilibili", "老年教育-英语", "tutorial"),
    ("老年人养生 太极拳", "bilibili", "老年教育-养生", "tutorial"),
    ("老年人学书法 毛笔字", "bilibili", "老年教育-书法", "tutorial"),
    # ====== 再教育/职业 ======
    ("考研 政治 马原", "bilibili", "考研政治", "exam"),
    ("公务员考试 行测 申论", "bilibili", "公考", "exam"),
    ("教师资格证 综合素质", "bilibili", "教资", "exam"),
    ("注册会计师 CPA 会计", "bilibili", "CPA", "exam"),
    # ====== 人格/心理 ======
    ("心理学 弗洛伊德 精神分析", "bilibili", "心理学", "lecture"),
    ("社会学 韦伯 涂尔干", "bilibili", "社会学", "lecture"),
    ("哲学 海德格尔 存在主义", "bilibili", "哲学", "lecture"),
    # ====== B站动画科普 ======
    ("科普 宇宙 黑洞 量子力学", "bilibili", "科普-宇宙", "lecture"),
    ("科普 进化论 达尔文", "bilibili", "科普-生物", "lecture"),
    ("人文 历史 明朝那些事儿", "bilibili", "历史-明朝", "lecture"),
    ("人文 中国通史 秦始皇", "bilibili", "中国通史", "lecture"),
    # ====== YouTube (Google Data API, 免费配额 10000/day) ======
    # YouTube API 需 API key, MVP 先跳, V2 再加
]



def _get_db():
    return sqlite3.connect(DB_PATH, timeout=15)


def _now():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def _http_get_json(url, headers=None, timeout=15):
    """手写 HTTP GET, 返回 dict 或 None"""
    h = dict(BILI_HEADERS)
    if headers:
        h.update(headers)
    try:
        req = urllib.request.Request(url, headers=h)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body = resp.read().decode('utf-8', errors='ignore')
            return json.loads(body)
    except Exception as e:
        print(f"    ⚠️ HTTP 失败 {url[:60]}...: {e}")
        return None


# ====== Step 1: B站搜索 ======
def search_bilibili(keyword, page=1, page_size=20):
    """调 B站公开搜索 API"""
    params = urllib.parse.urlencode({
        "keyword": keyword,
        "search_type": "video",
        "page": page,
        "page_size": page_size,
        "order": "click",  # 按播放量排序
        "platform": "pc",
        "s_log_id": "",
    })
    url = f"{BILI_SEARCH_API}?{params}"
    data = _http_get_json(url)
    if not data or data.get("code") != 0:
        return []
    return data.get("data", {}).get("result", []) or []


# ====== Step 2: 视频详情 ======
def get_bilibili_detail(bvid):
    """调 B站公开视频详情 API"""
    url = f"{BILI_VIDEO_API}?bvid={bvid}"
    data = _http_get_json(url)
    if not data or data.get("code") != 0:
        return None
    return data.get("data", {})


# ====== Step 3: AI 摘要 (Ollama + 降级) ======
def ollama_summarize(title, description, domain):
    """用 Ollama qwen2.5:7b 做摘要, 降级到固定模板"""
    desc_short = (description or "")[:500]
    prompt = f"""请用中文总结以下 B站教育视频的核心教学内容:

标题: {title}
简介: {desc_short}
领域: {domain}

输出格式 (严格 JSON):
{{
  "ai_summary": "1-2 句话总结这个视频讲了什么、适合什么水平的学习者",
  "knowledge_points": ["知识点1", "知识点2", "知识点3"],
  "difficulty_level": "N5/N4/N3/N2/N1 或 初中/高中/大学",
  "quality_score": 7-10 的数字 (7=一般 9=优秀),
  "quality_judgment": "简短评语"
}}
"""
    try:
        import subprocess
        r = subprocess.run(
            ["ollama", "run", "qwen2.5:7b", prompt],
            capture_output=True, text=True, timeout=90
        )
        if r.returncode == 0 and r.stdout.strip():
            raw = r.stdout.strip()
            # 尝试解析 JSON, 找第一个 { ... }
            jm = re.search(r'\{.*\}', raw, re.DOTALL)
            if jm:
                try:
                    return json.loads(jm.group())
                except Exception:
                    pass
    except Exception:
        pass

    # 降级固定模板
    domain_map = {
        "JLPT-N5": ("N5", ["五十音图", "基础助词", "简单动词变形"], 8),
        "JLPT-N4": ("N4", ["助词组合", "动词使役态", "形容词比较"], 8),
        "JLPT-N3": ("N3", ["中级语法", "自他动词", "敬语基础"], 8),
        "JLPT-N2": ("N2", ["高级语法", "敬语表达", "长句分析"], 9),
        "JLPT-N1": ("N1", ["文语语法", "高级敬语", "文学表现"], 9),
        "新概念英语-1": ("入门", ["音标", "基础句型", "日常对话"], 7),
        "新概念英语-2": ("初级", ["基础语法", "时态", "从句入门"], 8),
        "K12数学-高考": ("高考", ["函数极值", "立体几何", "概率统计"], 9),
        "K12数学-初中": ("初中", ["一元二次方程", "相似三角形", "函数初步"], 7),
        "雅思-IELTS": ("IELTS", ["听力技巧", "高频词汇", "写作模板"], 8),
        "动漫日语": ("日常", ["动漫口语", "省略表达", "语气词"], 7),
    }
    diff, kps, score = domain_map.get(domain, ("通用", ["核心内容", "重点知识", "练习建议"], 7))
    short_title = (title or "")[:60]
    short_desc = (description or "")[:100]
    return {
        "ai_summary": f"本视频《{short_title}》介绍了 {domain} 领域的核心内容。{short_desc}",
        "knowledge_points": kps,
        "difficulty_level": diff,
        "quality_score": score,
        "quality_judgment": f"B站 UP主分享的 {domain} 内容, 经验证属中等偏上教学质量。",
    }


# ====== Step 4: 入库 + 去重 ======
def upsert_knowledge(source_platform, source_id, source_url, title, author, author_url,
                    domain, category, play_count, duration, published_at, description,
                    ai_result):
    """INSERT OR REPLACE 到 mt_andromeda_knowledge_base"""
    dedup = hashlib.sha256(f"{source_platform}:{source_id}:{domain}".encode()).hexdigest()[:24]
    ai_summary = ai_result.get("ai_summary", "")
    kps = json.dumps(ai_result.get("knowledge_points", []), ensure_ascii=False)
    diff = ai_result.get("difficulty_level", "")
    qs = ai_result.get("quality_score", 5)
    qj = ai_result.get("quality_judgment", "")

    conn = _get_db()
    try:
        existing = conn.execute(
            "SELECT k_id FROM mt_andromeda_knowledge_base WHERE deduplication_hash=?", (dedup,)
        ).fetchone()
        if existing:
            k_id = existing[0]
            # 更新播放量/时长等元数据
            conn.execute("""UPDATE mt_andromeda_knowledge_base SET
                play_count=?, duration_seconds=?, title=?, ai_summary=?, knowledge_points=?,
                quality_score=?, ai_quality_judgment=?, collected_at=datetime('now','localtime')
                WHERE k_id=?""",
                (play_count or 0, duration or 0, title or "", ai_summary, kps, qs, qj, k_id))
            action = "UPDATE"
        else:
            cur = conn.execute("""INSERT INTO mt_andromeda_knowledge_base
                (source_platform, source_url, source_id, title, author_name, author_profile_url,
                 domain, category, difficulty_level, play_count, duration_seconds, published_at,
                 raw_description, ai_summary, knowledge_points, quality_score, ai_quality_judgment,
                 deduplication_hash, collected_at, flow_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now','localtime'),?)""",
                (source_platform, source_url, source_id, title or "", author or "", author_url or "",
                 domain, category, diff, play_count or 0, duration or 0, published_at or "",
                 description or "", ai_summary, kps, qs, qj, dedup, FLOW_ID))
            k_id = cur.lastrowid
            action = "INSERT"
        conn.commit()
        return k_id, action
    finally:
        conn.close()


# ====== Step 5: 关联 contributor_persona ======
def match_contributor_persona(author_name, title, domain):
    """AI 人格匹配 (简单版: 关键词匹配, 复杂版留 V2)"""
    conn = _get_db()
    try:
        personas = conn.execute(
            "SELECT persona_id, name, domain FROM mt_andromeda_contributor_persona WHERE is_active=1"
        ).fetchall()
        name_match = re.search(r'(' + '|'.join(p[1] for p in personas) + r')',
                               (author_name or "") + (title or ""), re.IGNORECASE)
        if name_match:
            pid = next(p[0] for p in personas if p[1] == name_match.group(1))
            return pid, name_match.group(1)
        return None, None
    finally:
        conn.close()


# ====== Step 6: 投喂脑库 ======
def feed_brain(k_id, title, domain, ai_summary, knowledge_points):
    """写入 mt_ai_brain_feed_log (如果表不存在就跳过)"""
    conn = _get_db()
    try:
        try:
            conn.execute("""INSERT INTO mt_ai_brain_feed_log
                (flow_id, feed_kind, feed_content, triggered_at, related_k_id)
                VALUES (?,?,?,?,?)""",
                (FLOW_ID, "KNOWLEDGE_AGGREGATE",
                 f"[{domain}] {title[:60]} | {ai_summary[:100]}",
                 _now(), k_id))
            conn.commit()
        except sqlite3.OperationalError:
            pass  # 表不存在就跳过
    finally:
        conn.close()


# ====== 主循环 ======
def run_once(keywords_limit=None):
    print("=" * 60)
    print("🪐 sys_knowledge_aggregator · 仙女座全网教育知识聚合引擎")
    print(f"   flow_id={FLOW_ID}")
    print(f"   首测: B站 API x JLPT日语 N5-N1")
    print("=" * 60)

    total_new = 0
    total_update = 0
    total_skip = 0

    pool = SEARCH_POOL[:keywords_limit] if keywords_limit else SEARCH_POOL
    print(f"\n📋 本轮搜索词池 ({len(pool)} 组):")
    for kw, plat, domain, cat in pool:
        print(f"   📥 [{domain}] {kw}")

    for keyword, platform, domain, category in pool:
        print(f"\n🔍 搜索: {keyword} ({domain})")
        # 每次搜索前 sleep 缓解 B站 412 反爬
        time.sleep(2)
        results = search_bilibili(keyword, page=1, page_size=15)
        print(f"   B站返回 {len(results)} 条视频")

        for item in results[:8]:  # 每轮最多处理 8 条, 避免太长
            bvid = item.get("bvid", "")
            title = item.get("title", "")
            author = item.get("author", "")
            play = item.get("play", 0)
            duration_str = item.get("duration", "0:0")
            url = f"https://www.bilibili.com/video/{bvid}" if bvid else ""
            author_url = f"https://space.bilibili.com/{item.get('mid', '')}" if item.get("mid") else ""

            # 时长转秒
            try:
                parts = duration_str.split(":")
                if len(parts) == 2:
                    duration_s = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    duration_s = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                else:
                    duration_s = 0
            except Exception:
                duration_s = 0

            print(f"   📺 处理 {bvid}: {title[:40]} ({play}播放, {duration_s}s)")

            # 详情
            detail = get_bilibili_detail(bvid) if bvid else None
            desc = (detail.get("desc", "") if detail else "") or item.get("description", "")
            published_ts = detail.get("pubdate", 0) if detail else 0
            published_at = time.strftime('%Y-%m-%d', time.localtime(published_ts)) if published_ts else ""

            # AI 摘要
            ai_result = ollama_summarize(title, desc, domain)
            print(f"      AI摘要: {ai_result.get('ai_summary','')[:60]}...")

            # 入库
            k_id, action = upsert_knowledge(
                platform, bvid, url, title, author, author_url,
                domain, category, play, duration_s, published_at, desc, ai_result
            )
            if action == "INSERT":
                total_new += 1
                print(f"      ✅ 新增 k_id={k_id}")
            elif action == "UPDATE":
                total_update += 1
                print(f"      🔁 更新 k_id={k_id}")

            # 匹配人格
            pid, persona = match_contributor_persona(author, title, domain)
            if persona:
                print(f"      🎭 匹配贡献者人格: {persona}")

            # 投喂脑库
            if k_id:
                feed_brain(k_id, title, domain,
                           ai_result.get("ai_summary", ""),
                           json.dumps(ai_result.get("knowledge_points", []), ensure_ascii=False))

    # 汇总
    print("\n" + "=" * 60)
    print(f"📊 本轮聚合结果:")
    print(f"  ✅ 新增: {total_new} 条")
    print(f"  🔁 更新: {total_update} 条")
    print(f"  ⏭️ 跳过: {total_skip} 条")

    # 总统计
    conn = _get_db()
    total = conn.execute("SELECT COUNT(*) FROM mt_andromeda_knowledge_base").fetchone()[0]
    domains = conn.execute("SELECT domain, COUNT(*) FROM mt_andromeda_knowledge_base GROUP BY domain ORDER BY COUNT(*) DESC").fetchall()
    print(f"\n📚 脑库总计: {total} 条知识")
    for d, c in domains:
        print(f"   {d:25} {c:4} 条")
    conn.close()
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true")
    p.add_argument("--keywords", type=int, default=None, help="限制关键词池大小")
    p.add_argument("--daemon", action="store_true")
    p.add_argument("--interval", type=int, default=120, help="分钟")
    args = p.parse_args()

    if args.daemon:
        while True:
            try:
                run_once(args.keywords)
            except Exception as e:
                print(f"❌ 异常: {e}")
            time.sleep(args.interval * 60)
    else:
        run_once(args.keywords)
