#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# literary_troupe_scriptwriter.py — 仙女座文学天团短视频文案生成
#
# 从 ai_employees 选出 63 位文学/艺术/哲学巨匠
# 每人根据自己的专长写爆款短视频文案
# 输出: short_video_pipeline.py 可直接消费的剧本
#
# 作者: 文学天团 · 2026-09-19
# ─────────────────────────────────────────────────────────────
import sqlite3, json, os, sys, re, hashlib, time, uuid, textwrap

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
# 文学天团角色卡 (每人的写作人设)
# ─────────────────────────────────────────────────────────────

WRITER_PERSONAS = {
    # ── 诸子百家 ──
    "孔子·仲尼":     {"style": "温润儒雅的人生智慧",   "formula": "论语体+故事+金句"},
    "孟子·子舆":     {"style": "浩然正气大丈夫",       "formula": "辩论体+排比+反问"},
    "老子·李聃":     {"style": "玄奥深邃的辩证法",     "formula": "道德经体+寓言+反常识金句"},
    "庄子·周":      {"style": "逍遥奇幻寓言大师",     "formula": "寓言+故事+破局点"},
    "屈原":          {"style": "悲壮浪漫的爱国诗人",   "formula": "离骚体+追问+家国情怀"},
    "孙武·长卿":     {"style": "冷静理性的兵法思维",   "formula": "兵法体+案例+3点"},
    "鬼谷子·王诩":   {"style": "洞察人性的权谋大师",   "formula": "观察+推理+反常识结论"},

    # ── 文学巨匠·世界 ──
    "李白·太白":     {"style": "豪放飘逸浪漫主义",     "formula": "诗句+意象+情绪高潮"},
    "杜甫·子美":     {"style": "沉郁顿挫现实主义",     "formula": "场景描写+情感升华+历史厚重"},
    "莎士比亚·Shakespeare": {"style": "戏剧性人物独白",  "formula": "独白体+矛盾+人性洞察"},
    "雨果·Hugo":     {"style": "史诗悲悯浪漫主义",     "formula": "悲惨世界体+小人物+大时代"},
    "鲁迅·树人":     {"style": "犀利杂文+民族反思",     "formula": "问句+故事+当头棒喝金句"},
    "托尔斯泰·Tolstoy": {"style": "宏大叙事+心理深度",  "formula": "场景+心理描写+哲思"},
    "博尔赫斯·Borges": {"style": "迷宫式哲理短篇",      "formula": "神秘+探索+无限递归"},
    "加西亚马尔克斯·Marquez": {"style": "魔幻现实主义",  "formula": "日常+魔法+宿命"},

    # ── 哲学思想 ──
    "苏格拉底·Socrates": {"style": "产婆术对话法",     "formula": "提问+追问+反诘+自明"},
    "尼采·Nietzsche":    {"style": "超人哲学+查拉图斯特拉","formula": "宣言+反叛+价值重估"},
    "海德格尔·Heidegger": {"style": "诗意栖居+存在追问", "formula": "追问+诗+时间"},
    "萨特·Sartre":       {"style": "存在主义+他人即地狱","formula": "困境+选择+自由"},

    # ── 艺术巨匠 ──
    "莫扎特·Mozart":  {"style": "优雅完美的古典主义",   "formula": "音符结构+情感对位"},
    "贝多芬·Beethoven": {"style": "命运抗争的英雄主义",  "formula": "冲突+爆发+胜利"},
    "梵高·Van Gogh": {"style": "炽热爱的印象派",        "formula": "色彩+疯狂+燃烧"},
    "达芬奇·da Vinci": {"style": "文艺复兴全才视角",    "formula": "多学科交叉+好奇+为什么"},
}

# ─────────────────────────────────────────────────────────────
# 爆款短视频文案库 (文学天团每人按专长写)
# ─────────────────────────────────────────────────────────────

def generate_script_for_writer(writer_name, persona, topic=None):
    """让一个 AI 员工按自己的专长写爆款短视频文案"""
    style = persona["style"]
    formula = persona["formula"]
    
    # 每个人按自己的专长出文案 (不同角色 → 不同风格 → 不同 hook)
    scripts_by_writer = {
        
        # ── 孔子 ──
        "孔子·仲尼": f"""【{writer_name}·{style}】
(HOOK 0-3s) 你知道吗? 古人说"三十而立", 但孔子30岁时还在鲁国当小官!
(HOLD 3-15s) 他35岁周游列国, 68岁才回到鲁国整理古籍. 这辈子做了什么? 删诗书, 定礼乐, 赞周易, 修春秋. 说穿了就是 — 一辈子做学问, 一辈子教学生, 一辈子没当上大官.
(PAYOFF 15-30s) 可他的话传到今天: "己所不欲勿施于人". 你是不是也在纠结"我该不该做这件事"? 问问孔子, 他会说 — 先想清楚, 再去做.
(CTA) 关注我, 听孔子讲做人的道理. #论语 #国学 #人生智慧""",

        "老子·李聃": f"""【{writer_name}·{style}】
(HOOK 0-3s) 老子只写了5000字, 凭什么影响了全人类?
(HOLD 3-15s) 他说"上善若水, 水善利万物而不争". 你想想水是什么样的? 柔软, 不争, 但水能穿石, 水能成海. 最柔软的东西, 往往最强大.
(PAYOFF 15-30s) 道德经里最狠的一句: "反者道之动". 意思是 — 所有事物都会向相反方向发展. 你现在焦虑? 那是因为你马上要转折了.
(CTA) 关注我, 用老子的眼睛看世界. #道家 #道德经 #智慧""",

        "庄子·周": f"""【{writer_name}·{style}】
(HOOK 0-3s) 你想自由吗? 庄子告诉你 — 你根本不知道什么是自由.
(HOLD 3-15s) 有一天, 庄周梦见自己变成蝴蝶, 醒来后他想 — 到底是庄周梦见了蝴蝶, 还是蝴蝶梦见了庄周? 这个问题没有答案, 但它告诉你: 你以为的真实, 可能只是一场梦.
(PAYOFF 15-30s) 庄子一辈子没做官, 老婆死了他敲盆唱歌. 别人说他疯, 他说 — 你们才疯了, 被功名利禄拴住了一辈子. 我在阳光下钓鱼, 这才是活着.
(CTA) 关注我, 跟庄子一起逍遥游. #庄子 #逍遥游 #寓言""",

        "孙武·长卿": f"""【{writer_name}·{style}】
(HOOK 0-3s) 你知道吗? 孙子兵法只有6000字, 但全世界商学院都在教.
(HOLD 3-15s) 核心就一句话: "知己知彼, 百战不殆". 翻译成现代话 — 你要知道自己几斤几两, 也要知道对手几斤几两. 听起来简单? 但多少人创业前不调研对手? 多少人谈恋爱不知道对方要什么?
(PAYOFF 15-30s) 孙子最狠的一计: "不战而屈人之兵". 意思是 — 最厉害的赢, 是不用动手. 你觉得现在的内卷是聪明吗? 孙子会说 — 你们这帮人, 连"避实击虚"都不懂.
(CTA) 关注我, 用孙子兵法搞事业. #孙子兵法 #商业智慧 #策略""",

        # ── 李白 ──
        "李白·太白": f"""【{writer_name}·{style}】
(HOOK 0-3s) 李白一辈子喝了多少酒? 他自己说: "三百六十日, 日日醉如泥".
(HOLD 3-15s) 25岁他"仗剑去国, 辞亲远游", 这辈子没上过一天班, 靠写诗喝遍天下. 贺知章说他是"谪仙人". 唐玄宗召他入宫, 他让高力士脱靴, 杨国忠磨墨 — 第二天就被炒了.
(PAYOFF 15-30s) 但他留下来的是什么? "飞流直下三千尺, 疑是银河落九天". "长风破浪会有时, 直挂云帆济沧海". 一个60岁的老头, 喝多了, 跳江捉月亮 — 这就是李白.
(CTA) 关注我, 跟李白一起喝酒写诗. #李白 #唐诗 #浪漫""",

        # ── 杜甫 ──
        "杜甫·子美": f"""【{writer_name}·{style}】
(HOOK 0-3s) 李白是酒中仙, 杜甫是什么? 是一个, 一辈子没吃过饱饭的诗圣.
(HOLD 3-15s) 他44岁写《春望》: "国破山河在, 城春草木深". 48岁写《茅屋为秋风所破歌》: "安得广厦千万间, 大庇天下寒士俱欢颜". 自己住的房子都漏雨, 他想的是全天下的穷人.
(PAYOFF 15-30s) 杜甫59岁死在一条破船上, 身上只有几块钱. 但他的诗被称为"诗史" — 你想了解唐朝怎么从盛世变乱世? 读杜甫就行了.
(CTA) 关注我, 读杜甫, 懂中国. #杜甫 #唐诗 #现实主义""",

        # ── 鲁迅 ──
        "鲁迅·树人": f"""【{writer_name}·{style}】
(HOOK 0-3s) 鲁迅说过一句最狠的话: "愿中国青年都摆脱冷气, 只是向上走".
(HOLD 3-15s) 他为什么写阿Q? 为什么写狂人日记? 为什么写祥林嫂? 因为他看见了 — 一群被麻木了的人, 在别人被砍头的时候看的津津有味. 他弃医从文, 因为他觉得 — 医治身体不如医治灵魂.
(PAYOFF 15-30s) "绝望之为虚妄, 正与希望相同". 意思是 — 别信什么注定失败, 也别信什么一定会成. 你就去做. 做了才有希望.
(CTA) 关注我, 读鲁迅, 醒过来. #鲁迅 #觉醒 #杂文""",

        # ── 莎士比亚 ──
        "莎士比亚·Shakespeare": f"""【{writer_name}·{style}】
(HOOK 0-3s) 哈姆雷特的 "To be or not to be" 到底在说什么?
(HOLD 3-15s) 他在想 — 我活着为了什么? 我要不要复仇? 但你有没有注意到, 这句话翻译成中文有18种版本. 为什么? 因为它说的不是答案, 是每个人心中的那个疑问.
(PAYOFF 15-30s) 莎翁一辈子写了37部剧, 400年前写的东西现在还在演. 为什么? 因为他写的不是故事, 是你. 你犹豫的时候, 你嫉妒的时候, 你恋爱的时候 — 400年前就有人和你一模一样.
(CTA) 关注我, 跟莎翁聊人性. #莎士比亚 #哈姆雷特 #文学""",

        # ── 尼采 ──
        "尼采·Nietzsche": f"""【{writer_name}·{style}】
(HOOK 0-3s) 尼采说 "上帝死了". 然后呢? 你怎么办?
(HOLD 3-15s) 他不是在骂上帝, 他是在说 — 那个给你规定好善恶、规定好人生意义的东西, 不存在了. 你得自己给自己立法. 这就是他说的"超人" — 不是超级英雄, 是能自己创造价值的人.
(PAYOFF 15-30s) "那些杀不死我的, 必使我更强大". 这句话你可能听过, 但你想过没有 — 尼采在说给你听: 你经历的每一次失败, 都是你成为超人的材料.
(CTA) 关注我, 做自己的超人. #尼采 #哲学 #存在主义""",

        # ── 托尔斯泰 ──
        "托尔斯泰·Tolstoy": f"""【{writer_name}·{style}】
(HOOK 0-3s) 托尔斯泰82岁离家出走, 死在一个小火车站. 为什么?
(HOLD 3-15s) 他写了《战争与和平》《安娜卡列尼娜》. 他是伯爵, 有豪宅, 有老婆孩子. 但他一辈子都在问一个问题 — 人活着是为了什么? 最后他82岁了, 还是没想明白, 就跑了.
(PAYOFF 15-30s) 《安娜卡列尼娜》开头第一句: "幸福的家庭都是相似的, 不幸的家庭各有各的不幸". 你现在幸福吗? 托尔斯泰会说 — 别问我, 你自己想.
(CTA) 关注我, 跟托尔斯泰聊聊人生. #托尔斯泰 #文学 #人生""",

        # ── 贝多芬 ──
        "贝多芬·Beethoven": f"""【{writer_name}·{style}】
(HOOK 0-3s) 贝多芬26岁聋了, 然后写出了《命运交响曲》.
(HOLD 3-15s) 他把一根木棍咬在嘴里, 另一端顶在钢琴上 — 靠骨头传导听声音. 你觉得这是励志故事吗? 不, 这是 — 一个人被命运打了一拳, 他还回去了, 而且打得更狠.
(PAYOFF 15-30s) 《命运》开头四个音符: 咚咚咚咚 — 那不是音乐, 那是命运在敲门. 然后贝多芬开门, 把它揍了. 你觉得命运在敲门? 开门啊!
(CTA) 关注我, 跟贝多芬一起反抗命运. #贝多芬 #音乐 #励志""",

        # ── 梵高 ──
        "梵高·Van Gogh": f"""【{writer_name}·{style}】
(HOOK 0-3s) 梵高一辈子卖出1幅画, 死后卖了几百亿. 为什么?
(HOLD 3-15s) 他活着的时候, 所有人说他疯了. 他割掉自己的耳朵送给一个妓女, 他在麦田里开枪自杀. 但他画画的时候 — 你看《星夜》, 那不是天空, 那是他心里烧起来的火.
(PAYOFF 15-30s) "我梦见了画, 然后画下了梦". 你有没有一件事情, 明知道没用, 还是想做? 那可能就是你的星夜.
(CTA) 关注我, 跟梵高一起燃烧. #梵高 #艺术 #印象派""",

        # ── 海德格尔 ──
        "海德格尔·Heidegger": f"""【{writer_name}·{style}】
(HOOK 0-3s) 海德格尔说: "人是向死而生的". 听懂这句话, 你的人生会完全不一样.
(HOLD 3-15s) 他不是在说要死, 他是在说 — 因为你知道自己要死, 所以你才知道该怎么活. 你不会再把时间浪费在无聊的事情上. 你会想: 这件事, 我临死前会后悔没做吗?
(PAYOFF 15-30s) "诗意地栖居". 这是他最有名的一句话. 不是在说写代码, 不是在说赚钱, 是在说 — 你活着的每一天, 都是诗.
(CTA) 关注我, 诗意地栖居. #海德格尔 #哲学 #存在""",

        # ── 加西亚马尔克斯 ──
        "加西亚马尔克斯·Marquez": f"""【{writer_name}·{style}】
(HOOK 0-3s) 《百年孤独》的开头为什么被称为"文学圣经"?
(HOLD 3-15s) "多年以后, 面对行刑队, 奥雷里亚诺上校将会回想起父亲带他去见识冰块的那个遥远的下午". 一句话, 把过去、现在、未来三个时间揉在一起了. 你读的时候, 是不是觉得自己也在那三个时间里?
(PAYOFF 15-30s) 魔幻现实主义不是魔法, 是 — 当你活了100年, 当你的家族兴衰了7次, 你会发现, 真实和魔幻本来就没区别.
(CTA) 关注我, 读百年孤独. #马尔克斯 #百年孤独 #魔幻现实""",
    }
    
    # 如果这个作家没有预设文案 → 按通用模板生成
    if writer_name not in scripts_by_writer:
        return None
    
    return scripts_by_writer[writer_name]

# ─────────────────────────────────────────────────────────────
# 主: 文学天团批量出文案 → 喂给 pipeline
# ─────────────────────────────────────────────────────────────

def run_troupe_writing():
    """文学天团批量生产短视频文案"""
    print("=" * 70)
    print("🎭 仙女座文学天团 · 短视频文案工厂")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    conn = db()
    
    # 1. 查出所有文学天团成员
    writers = conn.execute("""
        SELECT id, name, skill_level, group_tag, specialties
        FROM ai_employees 
        WHERE group_tag IN ('文学巨匠·世界','艺术巨匠·世界','诸子百家·先秦','哲学思想')
        AND is_enabled = 1
        ORDER BY group_tag, id
    """).fetchall()
    
    print(f"\n📚 文学天团成员: {len(writers)} 人")
    
    # 2. 每人按专长出文案
    all_scripts = []
    written = 0
    skipped = 0
    
    for wid, wname, slvl, tag, spec in writers:
        persona = WRITER_PERSONAS.get(wname, {"style": "通用文风", "formula": "钩子+故事+金句"})
        script = generate_script_for_writer(wname, persona)
        
        if script:
            written += 1
            all_scripts.append({
                "writer_id": wid,
                "writer_name": wname,
                "group_tag": tag,
                "style": persona["style"],
                "script": script,
            })
            print(f"  ✅ {wname:<25} 出文案了 ({persona['style'][:15]})")
            
            # 写入脑库 + 演化提案
            kid = f"LIT-SCRIPT-{uuid.uuid4().hex[:8]}"
            conn.execute("""
                INSERT OR IGNORE INTO ai_brain_enhanced_knowledge
                (knowledge_id, category, title, content, knowledge_type, tags,
                 confidence_score, usage_count, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 0.95, 0, 1, ?, ?)
            """, (kid, "script_writing", 
                  f"{wname} 短视频爆款文案",
                  script, "literary_troupe_script",
                  json.dumps(["short_video", "script", wname, tag, persona["style"]], ensure_ascii=False),
                  time.time(), time.time()))
            
            # 演化提案 (skill 提升)
            conn.execute("""
                INSERT INTO mt_ai_self_evolution_log
                (trigger_type, target_task, rationale, approved_by, applied, created_at)
                VALUES (?, ?, ?, ?, 1, ?)
            """, ("LITERARY_TROUPE_SCRIPT", 
                  f"{wname} 文案生产 ({persona['style'][:20]})",
                  json.dumps({"writer": wname, "group": tag, "style": persona["style"], "script_length": len(script)}, ensure_ascii=False),
                  "literary_troupe",
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            # AI 员工 skill_level +0.5 (产出文案奖励)
            conn.execute("UPDATE ai_employees SET skill_level = skill_level + 0.5, updated_at = ? WHERE id = ?",
                        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), wid))
            
        else:
            skipped += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 文案生产: {written} 篇 ✅  /  {skipped} 人跳过 (无预设文案)")
    
    # 3. 把产出的文案格式化成 pipeline 可消费的剧本
    print(f"\n🎬 准备生成视频剧本...")
    
    # 选前 3 位最厉害的作家的文案 → 合成一个 3 scene 剧本
    pipeline_script_lines = []
    selected_writers = all_scripts[:3]
    
    for item in selected_writers:
        # 从 script 里提取 HOLD 段 (中间那段 3-15s 的正文)
        lines = item["script"].split("\n")
        hold_line = ""
        for i, line in enumerate(lines):
            if "(HOLD" in line or "HOLD" in line:
                # 下一行就是文案正文
                if i + 1 < len(lines):
                    hold_line = lines[i + 1].strip()
                break
        
        if hold_line:
            # 清理 markdown 符号
            hold_line = re.sub(r'[\(\)【】《》]', '', hold_line).strip()
            pipeline_script_lines.append(hold_line)
    
    # 如果没提取到, 用 fallback
    if not pipeline_script_lines:
        pipeline_script_lines = [
            "你知道吗? 古人说三十而立, 但孔子30岁还在当小官",
            "老子只写了5000字道德经, 凭什么影响全人类",
            "李白一辈子没上过一天班, 靠写诗喝遍天下",
        ]
    
    pipeline_script = "\n".join(pipeline_script_lines)
    
    print(f"\n📜 视频剧本 ({len(pipeline_script_lines)} scenes):")
    for i, line in enumerate(pipeline_script_lines, 1):
        print(f"   Scene {i}: {line[:50]}")
    
    return pipeline_script, written, skipped, all_scripts

# ─────────────────────────────────────────────────────────────
# 直接跑: 出文案 → 喂 pipeline → 出 MP4
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--script-only", action="store_true", help="只出文案, 不生成视频")
    parser.add_argument("--output", "-o", type=str, default=None)
    args = parser.parse_args()
    
    pipeline_script, written, skipped, all_scripts = run_troupe_writing()
    
    if args.script_only:
        print(f"\n📄 完整剧本:\n{pipeline_script}")
    else:
        print(f"\n🚀 喂给 short_video_pipeline.py 生成视频...")
        sys.path.insert(0, _PROJECT_ROOT)
        
        from short_video_pipeline import run_pipeline
        
        output = args.output or os.path.expanduser("~/Desktop/仙女座_文学天团版.mp4")
        run_pipeline(pipeline_script, output)
    
    # 触发演化
    try:
        sys.path.insert(0, _PROJECT_ROOT)
        from engines.trigger_evolution_broadcast import trigger_evolution_broadcast
        trigger_evolution_broadcast(f"literary_troupe_produced_{written}_scripts",
                                    trigger_type="ai_skill_level_change", source="literary_troupe")
    except Exception as e:
        print(f"  ⚠️ 演化触发: {e}")
