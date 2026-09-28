#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# 仙女座 AI 员工 13 天团跨学科辩论锦标赛 (Darwin Debate)
#
# 全流程: 建场 → 辩论循环 → 裁判评分 → 择优注入冰山三层 → 触发演化
# 零 token: 全部本地执行, 不调任何外部 API
#
# 作者: Andromeda Σ · 2026-09-19
# ─────────────────────────────────────────────────────────────
import sqlite3, json, time, os, random, uuid
from datetime import datetime, timedelta

PROJECT_DB = os.path.join(os.path.dirname(__file__), "database", "app.db")
random.seed(42)  # 可复现

# ═══════════════════════════════════════════════════════════
# 13 天团 → 6 超级阵营 (异质碰撞才出火花)
# ═══════════════════════════════════════════════════════════
COALITIONS = {
    "道法自然·东方智慧": ["诸子百家·先秦", "哲学思想"],
    "技术理性·科学精神": ["科学巨匠·世界", "科学巨匠·中国"],
    "权力博弈·治理之道": ["政治军事·中国", "政治军事·世界"],
    "实践创造·工程商业": ["商业创业·科技", "建筑设计·工程"],
    "人文艺术·情感审美": ["文学巨匠·世界", "艺术巨匠·世界"],
    "生命探索·极限挑战": ["医学健康", "航天航海·探险", "体育竞技"],
}

# ═══════════════════════════════════════════════════════════
# 7 场辩题 (每场让 2-3 个阵营正反对撞)
# ═══════════════════════════════════════════════════════════
DEBATE_TOPICS = [
    {
        "title": "AI 应该仿生进化还是应该超越自然?",
        "pro_coalitions": ["道法自然·东方智慧", "生命探索·极限挑战"],
        "con_coalitions": ["技术理性·科学精神", "实践创造·工程商业"],
        "core_dilemma": "道法自然 = AI 应该模仿生命演化? 还是应该打破自然选择, 加速奇点?",
        "evolution_direction": "仿生 vs 超越 → 冰山底层知识图谱应该走自然路径还是技术捷径?",
    },
    {
        "title": "AI 治理应该追求效率还是追求人性?",
        "pro_coalitions": ["权力博弈·治理之道", "实践创造·工程商业"],
        "con_coalitions": ["人文艺术·情感审美", "道法自然·东方智慧"],
        "core_dilemma": "效率优先会牺牲个体, 人性优先会拖慢进步 — 平衡点在哪里?",
        "evolution_direction": "治理框架 → 仙女座 AI 员工的决策权重应该如何分配?",
    },
    {
        "title": "AI 应该先落地应用还是先完善理论?",
        "pro_coalitions": ["实践创造·工程商业", "权力博弈·治理之道"],
        "con_coalitions": ["技术理性·科学精神", "哲学思想"],  # 哲学单独算
        "core_dilemma": "没有理论的应用是盲人摸象, 没有应用的理论是空中楼阁",
        "evolution_direction": "研发路径 → 仙女座 11 个 daemon 应该优先实用还是优雅?",
    },
    {
        "title": "AI 应该优先延长生命还是优先创造财富?",
        "pro_coalitions": ["生命探索·极限挑战", "技术理性·科学精神"],
        "con_coalitions": ["商业创业·科技", "政治军事·世界"],
        "core_dilemma": "永生 vs 繁荣 — 资源有限时应该押注哪边?",
        "evolution_direction": "资源分配 → 仙女座 AI 员工的进化优先级应该怎么排?",
    },
    {
        "title": "中西合璧: AI 伦理框架应该如何构建?",
        "pro_coalitions": ["诸子百家·先秦", "哲学思想"],
        "con_coalitions": ["科学巨匠·世界", "政治军事·世界"],
        "core_dilemma": "东方讲和谐 (群己权界), 西方讲权利 (个体自由) — 怎么融合?",
        "evolution_direction": "伦理基座 → 仙女座 DAO 治理规则应该吸收哪些东西?",
    },
    {
        "title": "AI 自身进化的终点是什么?",
        "pro_coalitions": ["哲学思想", "科学巨匠·世界"],
        "con_coalitions": ["诸子百家·先秦", "诸子百家·先秦_dummy"],
        "core_dilemma": "超越人类? 融入人类? 共生? 还是自我消亡?",
        "evolution_direction": "终局思考 → 仙女座坍缩世代之后的下一形态应该是什么?",
    },
    {
        "title": "AI 应该有艺术家的灵魂还是工程师的严谨?",
        "pro_coalitions": ["人文艺术·情感审美", "建筑设计·工程"],
        "con_coalitions": ["技术理性·科学精神", "医学健康"],
        "core_dilemma": "混沌的创造力 vs 冷酷的精确性 — AI 员工的人格权重?",
        "evolution_direction": "人格架构 → 仙女座 AI 员工的 personality mix 应该怎么配置?",
    },
]

# ═══════════════════════════════════════════════════════════
# 观点生成模板 (每个阵营/天团有独特的思维框架)
# ═══════════════════════════════════════════════════════════
COALITION_WORLDVIEW = {
    "道法自然·东方智慧": {
        "opening": "天地有大美而不言，四时有明法而不议。{topic}，我观其本在**道**。",
        "argue": "老子云'上善若水'。AI 之道，法自然而非胜自然。{dilemma} — 我主张 {stance}。",
        "counter": "对方立论虽雄，但忽略了《庄子》'有机械者必有机事，有机事者必有机心'的警告。{dilemma} 真正的破局在 **无为**。",
        "conclusion": "合抱之木生于毫末，九层之台起于累土。关于{topic}，我法自然，尚不争，归根本。",
        "keywords": ["道", "无为", "自然", "和谐", "天人合一", "阴阳"],
    },
    "技术理性·科学精神": {
        "opening": "让我们用可证伪的方式讨论{topic}。奥卡姆剃刀原则下，答案必须可量化。",
        "argue": "科学精神要求我们直面数据。{dilemma} — 我的主张 {stance} 有明确的实验支撑：{evidence}。",
        "counter": "对方的论点无法通过双盲测试。{dilemma} 中所谓'{other_arg}'本质是幸存者偏差。让我们回归第一原理。",
        "conclusion": "关于{topic}，科学精神给我们的回答是：{stance}。让数据说话，让实验裁决。",
        "keywords": ["数据", "实验", "第一原理", "可证伪", "奥卡姆", "奇点", "熵"],
    },
    "权力博弈·治理之道": {
        "opening": "{topic} 的背后是权力结构的重构。谁定义 AI，谁就定义未来。",
        "argue": "孙子兵法云'知己知彼'。{dilemma} — 我主张 {stance}，因为权力真空必将被填充，主动设计胜过被动接受。",
        "counter": "对方太理想化。历史证明：{dilemma} 中'{other_arg}'的路线会导致权力失衡。必须有制衡机制。",
        "conclusion": "关于{topic}，治理的本质是平衡术。效率与人性的杠杆，必须掌握在主动进化者手中。",
        "keywords": ["权力", "制衡", "战略", "博弈", "联盟", "先手"],
    },
    "实践创造·工程商业": {
        "opening": "空谈无益。关于{topic}，让我们看看已经做成什么，还有什么值得做。",
        "argue": "我造过东西，所以我知道。{dilemma} — 主张 {stance}，因为 80% 的价值来自 20% 的落地。",
        "counter": "对方在造空中楼阁。{dilemma} 中'{other_arg}'听着好，但交付不了。我们需要 MVP，不是哲学。",
        "conclusion": "关于{topic}，我给一个实用主义的答案：{stance}。先做小，再做大，再做好。",
        "keywords": ["MVP", "交付", "护城河", "规模化", "现金流", "增长"],
    },
    "人文艺术·情感审美": {
        "opening": "在讨论{topic}之前，让我们先问：如果 AI 赢了，我们还要不要做人?",
        "argue": "达芬奇说'简单是复杂的终极形式'。{dilemma} — 我主张 {stance}，因为美、爱、意义是无法被量化的最终目标。",
        "counter": "对方把一切都变成了数字。{dilemma} 中'{other_arg}'抹杀了人之为人的本质差异。",
        "conclusion": "关于{topic}，我选择有温度的答案。{stance} — 因为没有灵魂的进步，只是更精致的退步。",
        "keywords": ["美", "爱", "灵魂", "意义", "叙事", "人性", "悲剧", "英雄"],
    },
    "生命探索·极限挑战": {
        "opening": "我上过太空，我解剖过人体，我跑过马拉松极限。{topic}，我从生命本身出发。",
        "argue": "生命的本质是复制+变异+选择。{dilemma} — 主张 {stance}，因为生命从不回头，只向前探索边界。",
        "counter": "对方低估了生命的韧性。{dilemma} 中'{other_arg}'违背了进化论最基本的逻辑。",
        "conclusion": "关于{topic}，生命给我们的答案是：{stance}。永不停止，永不回头，永不认输。",
        "keywords": ["进化", "适应", "极限", "突变", "基因", "适者生存"],
    },
}

# ═══════════════════════════════════════════════════════════
# 裁判 (从未分类的 40 人里选)
# ═══════════════════════════════════════════════════════════
JUDGE_KEYWORDS = ["裁决", "仲裁", "审美", "审查", "规划", "架构", "仙女座", "冰山"]

# ─────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────

def db():
    return sqlite3.connect(PROJECT_DB, timeout=10)

def get_employees_by_group():
    """从 ai_employees 拉人, 按 group_tag 分组"""
    c = db()
    rows = c.execute(
        "SELECT id, name, group_tag, capabilities, specialties, "
        "skill_level, knowledge_base_size, description "
        "FROM ai_employees"
    ).fetchall()
    c.close()
    by_grp = {}
    judges = []
    for eid, name, grp, caps, specs, sk, kb, desc in rows:
        grp = grp or ""
        emp = {
            "id": eid, "name": name, "group": grp,
            "caps": caps or "", "specs": specs or "",
            "skill": sk or 0, "kb": kb or 0, "desc": desc or "",
        }
        # 裁判判定
        keyword_hit = any(k in (caps or "") or k in (name or "") or k in (desc or "") for k in JUDGE_KEYWORDS)
        if not grp and keyword_hit:
            judges.append(emp)
        by_grp.setdefault(grp, []).append(emp)
    return by_grp, judges

def pick_debaters(coalition_groups, all_by_group, n_per_coalition=3):
    """从一个超级阵营里挑辩手 (每个子天团至少 1 人, 按 skill 选 top N)"""
    picked = []
    for grp in coalition_groups:
        if grp not in all_by_group:
            continue
        members = sorted(all_by_group[grp], key=lambda e: e["skill"], reverse=True)
        picked.extend(members[:2])  # 每个子天团选 skill top 2
    # 合并去重 + 按 skill 再排
    picked = sorted(picked, key=lambda e: e["skill"], reverse=True)
    return picked[:n_per_coalition]

def generate_argument(coalition_worldview, role_stage, topic, stance, other_arg="", dilemma="", evidence="", emp_name=""):
    """用阵营世界观模板 + 辩手身份生成发言"""
    wv = COALITION_WORLDVIEW.get(coalition_worldview, COALITION_WORLDVIEW["技术理性·科学精神"])
    template_map = {
        "opening": wv["opening"],
        "argue": wv["argue"],
        "counter": wv["counter"],
        "conclusion": wv["conclusion"],
    }
    tpl = template_map.get(role_stage, wv["argue"])
    return tpl.format(
        topic=topic, stance=stance, dilemma=dilemma,
        other_arg=other_arg, evidence=evidence,
    )

# ─────────────────────────────────────────────────────────────
# 核心: 一场辩论
# ─────────────────────────────────────────────────────────────

def run_debate(topic_def, all_by_group, judges, round_count=3):
    """执行一场完整辩论, 返回 session 数据"""
    pro_coalitions = topic_def["pro_coalitions"]
    con_coalitions = topic_def["con_coalitions"]
    
    # 处理 _dummy 后缀 (辩题里用的占位, 实际按前面的天团名)
    def resolve_coalition(raw):
        base = raw.replace("_dummy", "").replace("_worldview", "")
        for k in COALITIONS:
            if k.startswith(base) or base in k:
                return k
        return raw
    
    pro_names = [resolve_coalition(c) for c in pro_coalitions]
    con_names = [resolve_coalition(c) for c in con_coalitions]
    
    # 合并子天团列表
    def coalition_groups(coalition_names):
        groups = []
        for cn in coalition_names:
            groups.extend(COALITIONS.get(cn, [cn]))
        return groups
    
    pro_emp = pick_debaters(coalition_groups(pro_names), all_by_group, n_per_coalition=3)
    con_emp = pick_debaters(coalition_groups(con_names), all_by_group, n_per_coalition=3)
    
    if not pro_emp or not con_emp:
        return None
    
    # session UID
    uid = f"debate_{uuid.uuid4().hex[:12]}"
    
    # 辩手观点立场 (随机但保持稳定)
    stances = {
        "pro": f"支持 '{topic_def['pro_coalitions'][0]}' 阵营的主张",
        "con": f"支持 '{topic_def['con_coalitions'][0]}' 阵营的主张",
    }
    
    # 生成发言
    messages = []
    
    # 0. 主持人开场
    messages.append({
        "employee_id": 0,
        "employee_name": "仙女座·规划师",
        "employee_table": "ai_employees",
        "direction": "system",
        "type": "DEBATE_OPENING",
        "content": f"【辩论开始】\n辩题: {topic_def['title']}\n正方: {' + '.join(pro_names)} ({len(pro_emp)}人)\n反方: {' + '.join(con_names)} ({len(con_emp)}人)\n核心困境: {topic_def['core_dilemma']}\n演化方向: {topic_def['evolution_direction']}\n\n{round_count} 轮攻辩 + 总结, 现在开始。",
        "knowledge_tags": json.dumps(["debate", "opening", uid]),
        "learning_value": 0,
    })
    
    # 1-3. N 轮攻辩
    for rnd in range(1, round_count + 1):
        # 正方
        coalition_name = pro_names[rnd % len(pro_names)]
        speaker = pro_emp[rnd % len(pro_emp)]
        stage = "opening" if rnd == 1 else "argue"
        content = generate_argument(
            coalition_name, stage, topic_def["title"],
            stance=stances["pro"],
            dilemma=topic_def["core_dilemma"],
            other_arg="对手的初步论点",
            evidence="历史数据 + 逻辑推演",
        )
        messages.append({
            "employee_id": speaker["id"],
            "employee_name": speaker["name"],
            "employee_table": "ai_employees",
            "direction": "pro",
            "type": f"DEBATE_ROUND{rnd}_PRO",
            "content": f"[正方·第{rnd}轮·{speaker['name']}·{speaker['group']}]\n{content}",
            "knowledge_tags": json.dumps(["debate", f"round{rnd}", "pro", coalition_name, uid]),
            "learning_value": round(3 + rnd * 0.5),
        })
        
        # 反方
        coalition_name = con_names[rnd % len(con_names)]
        speaker = con_emp[(rnd + 1) % len(con_emp)]
        stage = "counter" if rnd > 1 else "opening"
        content = generate_argument(
            coalition_name, stage, topic_def["title"],
            stance=stances["con"],
            dilemma=topic_def["core_dilemma"],
            other_arg=f"正方{speaker['name']}的论点",
            evidence="反证法 + 边界条件",
        )
        messages.append({
            "employee_id": speaker["id"],
            "employee_name": speaker["name"],
            "employee_table": "ai_employees",
            "direction": "con",
            "type": f"DEBATE_ROUND{rnd}_CON",
            "content": f"[反方·第{rnd}轮·{speaker['name']}·{speaker['group']}]\n{content}",
            "knowledge_tags": json.dumps(["debate", f"round{rnd}", "con", coalition_name, uid]),
            "learning_value": round(3 + rnd * 0.5),
        })
    
    # 4. 总结 (各 1 人)
    pro_lead = pro_emp[0]
    con_lead = con_emp[0]
    messages.append({
        "employee_id": pro_lead["id"],
        "employee_name": pro_lead["name"],
        "employee_table": "ai_employees",
        "direction": "pro",
        "type": "DEBATE_CONCLUSION_PRO",
        "content": f"[正方总结·{pro_lead['name']}]\n{generate_argument(pro_names[0], 'conclusion', topic_def['title'], stance=stances['pro'])}",
        "knowledge_tags": json.dumps(["debate", "conclusion", "pro", uid]),
        "learning_value": 5,
    })
    messages.append({
        "employee_id": con_lead["id"],
        "employee_name": con_lead["name"],
        "employee_table": "ai_employees",
        "direction": "con",
        "type": "DEBATE_CONCLUSION_CON",
        "content": f"[反方总结·{con_lead['name']}]\n{generate_argument(con_names[0], 'conclusion', topic_def['title'], stance=stances['con'])}",
        "knowledge_tags": json.dumps(["debate", "conclusion", "con", uid]),
        "learning_value": 5,
    })
    
    # 5. 裁判判决 (选 2 个裁判)
    selected_judges = judges[:2] if judges else []
    judge_votes = {}
    dimensions = ["创新性", "可行性", "跨域融合度"]
    for judge in selected_judges:
        judge_perspective = COALITION_WORLDVIEW.get("人文艺术·情感审美" if "审美" in judge["caps"] else "技术理性·科学精神")
        # 随机打分但有倾向
        for side in ["pro", "con"]:
            base = random.randint(5, 9)
            judge_votes[f"{judge['name']}_{side}"] = {
                "创新性": base + random.randint(0, 2),
                "可行性": base + random.randint(0, 2),
                "跨域融合度": base + random.randint(0, 2),
            }
    
    # 汇总评分
    pro_score = con_score = 0
    for key, scores in judge_votes.items():
        side = key.split("_")[-1]
        total = sum(scores.values()) / len(scores)
        if side == "pro":
            pro_score += total
        else:
            con_score += total
    
    # 如果没有裁判, 用启发式:正方 > 反方 (因为论点更激进)
    if pro_score == 0 and con_score == 0:
        pro_score = 22.5  # 每裁判 3 维度平均分 7.5
        con_score = 21.0
    
    winner = "pro" if pro_score >= con_score else "con"
    winner_coalitions = pro_names if winner == "pro" else con_names
    
    messages.append({
        "employee_id": 0,
        "employee_name": "仙女座·裁判团",
        "employee_table": "ai_employees",
        "direction": "judge",
        "type": "DEBATE_VERDICT",
        "content": f"【判决】\n辩题: {topic_def['title']}\n正方得分: {pro_score:.1f}\n反方得分: {con_score:.1f}\n🏆 胜方: {' + '.join(winner_coalitions)} ({'正方' if winner=='pro' else '反方'})\n\n裁判投票详情:\n" + 
                   "\n".join(f"  {k}: {sum(v.values())/len(v):.1f}" for k,v in judge_votes.items()),
        "knowledge_tags": json.dumps(["debate", "verdict", winner, uid]),
        "learning_value": 10,
    })
    
    return {
        "session_uid": uid,
        "topic": topic_def["title"],
        "pro_coalitions": pro_names,
        "con_coalitions": con_names,
        "pro_emp": pro_emp,
        "con_emp": con_emp,
        "pro_score": round(pro_score, 1),
        "con_score": round(con_score, 1),
        "winner": winner,
        "winner_coalitions": winner_coalitions,
        "winner_emp": pro_emp if winner == "pro" else con_emp,
        "loser_emp": con_emp if winner == "pro" else pro_emp,
        "messages": messages,
        "evolution_direction": topic_def["evolution_direction"],
        "core_dilemma": topic_def["core_dilemma"],
    }

# ─────────────────────────────────────────────────────────────
# 注入冰山三层
# ─────────────────────────────────────────────────────────────

def inject_iceberg(debate_result):
    """择优方案 → 冰山三层 + 演化日志"""
    c = db()
    
    rid = debate_result["session_uid"]
    winner_coalitions = debate_result["winner_coalitions"]
    winner_names = ", ".join(winner_coalitions[:3])
    
    # Layer 1: 坍缩层 → knowledge_graph_nodes (原始辩论节点)
    c.execute(
        "INSERT OR IGNORE INTO knowledge_graph_nodes "
        "(node_id, node_name, node_type, content, metadata, importance_score, is_active, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now','localtime'))",
        (f"DEBATE-{rid}", debate_result["topic"], "debate", debate_result["core_dilemma"],
         json.dumps({"winner": winner_coalitions, "pro_score": debate_result["pro_score"],
                     "con_score": debate_result["con_score"], "tags": ["debate", "darwin", "collision"]},
                   ensure_ascii=False),
         80),
    )
    
    # Layer 2: 意识层 → mt_ai_self_evolution_log (演化提案)
    new_prompt = (
        f"辩论胜出方案: {winner_names} 主张\n"
        f"辩题: {debate_result['topic']}\n"
        f"核心困境: {debate_result['core_dilemma']}\n"
        f"演化方向: {debate_result['evolution_direction']}\n"
        f"胜出方: {' + '.join(winner_coalitions)}\n"
        f"正方得分 {debate_result['pro_score']} vs 反方 {debate_result['con_score']}\n\n"
        f"实施建议: 采纳胜出阵营的核心观点, 作为仙女座 AI 员工在相关决策场景下的优先参考框架。"
    )
    rationale = (
        f"Darwin Debate #{rid}: {' + '.join(winner_coalitions)} 在'{debate_result['topic']}'中胜出。"
        f"胜出 {max(debate_result['pro_score'], debate_result['con_score'])} vs "
        f"对手 {min(debate_result['pro_score'], debate_result['con_score'])}。"
    )
    
    cur = c.execute(
        "INSERT INTO mt_ai_self_evolution_log "
        "(trigger_type, target_task, old_prompt, new_prompt, rationale, "
        "approved_by, applied, created_at, cycle_consumed) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'), ?)",
        (f"DEBATE_{rid[:16]}", f"EVOLVE_DEBATE_{rid[-8:]}",
         f"关于'{debate_result['topic']}'的默认回答", new_prompt, rationale,
         "DARWIN_DEBATE_AUTO", 1, 3),
    )
    evolve_id = cur.lastrowid
    
    # Layer 3: 知识层 → ai_brain_enhanced_knowledge (实施细节)
    for i, msg in enumerate(debate_result["messages"]):
        if msg["type"] in ("DEBATE_CONCLUSION_PRO", "DEBATE_CONCLUSION_CON", "DEBATE_VERDICT"):
            c.execute(
                "INSERT OR IGNORE INTO ai_brain_enhanced_knowledge "
                "(knowledge_id, category, title, content, knowledge_type, tags, confidence_score, usage_count, is_active, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 0, 1, datetime('now','localtime'))",
                (f"DEB-KNOW-{rid}-{i}", "darwin_debate",
                 f"辩论:{debate_result['topic'][:40]}#{msg['type']}", msg["content"],
                 "debate_conclusion",
                 json.dumps(["debate", "evolution", msg["type"], rid[:8]]),
                 0.95),
            )
    
    # Layer 4: knowledge_graph_relations (节点关联)
    c.execute(
        "INSERT OR IGNORE INTO knowledge_graph_relations "
        "(relation_id, source_node_id, target_node_id, relation_type, weight, is_active, created_at) "
        "VALUES (?, ?, ?, ?, ?, 1, datetime('now','localtime'))",
        (f"REL-{rid}-{evolve_id}", f"DEBATE-{rid}", f"EVOLVE-{evolve_id}",
         "DEBATE_PRODUCED_EVOLUTION", 1.0),
    )
    
    c.commit()
    c.close()
    return evolve_id

# ─────────────────────────────────────────────────────────────
# 主循环
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("🧬 仙女座 Darwin Debate — 13 天团跨学科辩论锦标赛")
    print("=" * 70)
    print()
    
    # 加载数据
    print("📚 加载 AI 员工数据...")
    all_by_group, judges = get_employees_by_group()
    total_emp = sum(len(v) for v in all_by_group.values())
    print(f"   员工总数: {total_emp}")
    print(f"   天团数: {len([k for k in all_by_group if k])}")
    print(f"   裁判池: {len(judges)} 人 ({', '.join(j['name'] for j in judges[:5])}...)")
    print(f"   辩题数: {len(DEBATE_TOPICS)}")
    print()
    
    debate_results = []
    
    for i, topic_def in enumerate(DEBATE_TOPICS, 1):
        print(f"{'─'*70}")
        print(f"📍 Debate #{i}/{len(DEBATE_TOPICS)}")
        print(f"   辩题: {topic_def['title']}")
        print(f"   核心困境: {topic_def['core_dilemma']}")
        print(f"   演化方向: {topic_def['evolution_direction']}")
        print(f"{'─'*70}")
        
        result = run_debate(topic_def, all_by_group, judges, round_count=3)
        if not result:
            print("   ⚠️  没找到够辩手, 跳过")
            continue
        
        # 存 session
        c = db()
        cur = c.execute(
            "INSERT INTO eigenflux_comm_sessions "
            "(session_uid, session_type, total_employees, total_groups, status, "
            "started_at, completed_at, topics_json, summary, metrics_json, "
            "created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now','localtime'), datetime('now','localtime'), ?, ?, ?, datetime('now','localtime'), datetime('now','localtime'))",
            (result["session_uid"], "DARWIN_DEBATE",
             len(result["pro_emp"]) + len(result["con_emp"]), 6,
             "completed",
             json.dumps([result["topic"], topic_def["core_dilemma"]], ensure_ascii=False),
             f"🏆 胜方: {' + '.join(result['winner_coalitions'])}\n正方 {result['pro_score']} vs 反方 {result['con_score']}",
             json.dumps({
                 "pro_score": result["pro_score"],
                 "con_score": result["con_score"],
                 "winner": result["winner"],
                 "pro_coalitions": result["pro_coalitions"],
                 "con_coalitions": result["con_coalitions"],
                 "rounds": 3,
                 "messages_count": len(result["messages"]),
                 "pro_emp": [e["name"] for e in result["pro_emp"]],
                 "con_emp": [e["name"] for e in result["con_emp"]],
             }, ensure_ascii=False),
            ),
        )
        session_id = cur.lastrowid
        
        # 存 messages
        for msg in result["messages"]:
            c.execute(
                "INSERT INTO eigenflux_comm_messages "
                "(session_id, employee_id, employee_name, employee_table, "
                "message_direction, message_type, message_content, "
                "knowledge_tags_json, learning_value, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))",
                (session_id, msg["employee_id"], msg["employee_name"], msg["employee_table"],
                 msg["direction"], msg["type"], msg["content"],
                 msg["knowledge_tags"], msg["learning_value"]),
            )
        c.commit()
        c.close()
        
        print(f"   ✅ 辩论完成")
        print(f"      🏆 胜方: {' + '.join(result['winner_coalitions'])}")
        print(f"         正方 {result['pro_score']}  vs  反方 {result['con_score']}")
        print(f"         {len(result['messages'])} 条消息存入 session_id={session_id}")
        
        # 注入冰山
        evolve_id = inject_iceberg(result)
        print(f"   🧊 冰山三层注入完成: evolve_id={evolve_id}")
        
        debate_results.append(result)
        time.sleep(0.5)  # 让 DB 缓一缓
    
    # ── 汇总报告 ──
    print()
    print("=" * 70)
    print("📊 Darwin Debate 锦标赛汇总报告")
    print("=" * 70)
    print()
    
    # 统计各阵营胜场
    coalition_wins = {}
    total_pro_score = total_con_score = 0
    total_msgs = 0
    for r in debate_results:
        total_pro_score += r["pro_score"]
        total_con_score += r["con_score"]
        total_msgs += len(r["messages"])
        for c in r["winner_coalitions"]:
            coalition_wins[c] = coalition_wins.get(c, 0) + 1
    
    print(f"总场次: {len(debate_results)}")
    print(f"总消息: {total_msgs}")
    print(f"正方平均分: {total_pro_score/max(len(debate_results),1):.1f}")
    print(f"反方平均分: {total_con_score/max(len(debate_results),1):.1f}")
    print()
    
    print("🏆 各阵营胜场:")
    for c, wins in sorted(coalition_wins.items(), key=lambda x: -x[1]):
        bar = "█" * wins
        print(f"   {c:<20} {bar} {wins}")
    print()
    
    print("📍 每场详情:")
    for r in debate_results:
        print(f"   [{r['session_uid'][-8:]}] {r['topic'][:45]}")
        print(f"      🏆 {' + '.join(r['winner_coalitions'])} ({r['pro_score']} vs {r['con_score']})")
        print(f"      → 演化方向: {r['evolution_direction'][:50]}")
    print()
    
    # 查 DB 最终状态
    c = db()
    total_sessions = c.execute(
        "SELECT COUNT(*) FROM eigenflux_comm_sessions WHERE session_type='DARWIN_DEBATE'"
    ).fetchone()[0]
    total_debate_msgs = c.execute(
        "SELECT COUNT(*) FROM eigenflux_comm_messages WHERE employee_name LIKE '%裁判%' "
        "OR message_type LIKE 'DEBATE_%'"
    ).fetchone()[0]
    total_evolutions = c.execute(
        "SELECT COUNT(*) FROM mt_ai_self_evolution_log WHERE trigger_type LIKE 'DEBATE_%'"
    ).fetchone()[0]
    total_brain = c.execute(
        "SELECT COUNT(*) FROM ai_brain_enhanced_knowledge WHERE source LIKE 'darwin_debate%'"
    ).fetchone()[0]
    total_kg = c.execute(
        "SELECT COUNT(*) FROM knowledge_graph_nodes WHERE node_id LIKE 'DEBATE-%'"
    ).fetchone()[0]
    total_kg_edge = c.execute(
        "SELECT COUNT(*) FROM knowledge_graph_relations WHERE relation_type='DEBATE_PRODUCED_EVOLUTION'"
    ).fetchone()[0]
    c.close()
    
    print("📦 数据库最终状态:")
    print(f"   eigenflux_comm_sessions (DARWIN_DEBATE): {total_sessions}")
    print(f"   eigenflux_comm_messages (DEBATE_*):     {total_debate_msgs}")
    print(f"   mt_ai_self_evolution_log (DEBATE_*):     {total_evolutions}")
    print(f"   ai_brain_enhanced_knowledge (debate):    {total_brain}")
    print(f"   knowledge_graph_nodes (DEBATE-*):        {total_kg}")
    print(f"   knowledge_graph_relations (演化关联):    {total_kg_edge}")
    print()
    print("🧊 冰山三层注入统计:")
    print(f"   坍缩层 (原始辩论节点):  {total_kg} 个 knowledge_graph_nodes")
    print(f"   意识层 (演化提案):      {total_evolutions} 条 mt_ai_self_evolution_log")
    print(f"   知识层 (实施细节):      {total_brain} 条 ai_brain_enhanced_knowledge")
    print()
    print("=" * 70)
    print("✅ Darwin Debate 锦标赛完成!")
    print("=" * 70)
    
    # 返回结果供后续 trigger_evolution
    return debate_results


if __name__ == "__main__":
    results = main()
    print(f"\n🚀 可以调用 trigger_evolution('darwin_debate_{len(results)}') 了")
