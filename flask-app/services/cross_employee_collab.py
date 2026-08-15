import secrets
#!/usr/bin/env python3
"""
AI员工跨角色协作 - EigenFlux网络功能拓展
不同角色的AI员工互相建立联系，开展跨领域协作，拓展系统能力
"""

import sqlite3
import os
import json
import uuid
import time
import random, secrets
from datetime import datetime, timedelta
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, 'app.db')

# 角色分类映射
ROLE_CATEGORIES = {
    "翻译": "translation",
    "安全": "security",
    "分析": "analytics",
    "设计": "design",
    "策略": "strategy",
    "科学": "research",
    "教练": "coaching",
    "客服": "customer_service",
    "文案": "copywriting",
    "顾问": "consulting",
    "Employee": "general",
}

# 每个角色的专业知识库
DOMAIN_KNOWLEDGE = {
    "translation": [
        ("多语言实时翻译", "使用Transformer架构实现低延迟翻译，支持42种语言互译", "skill", 0.88),
        ("术语库管理", "建立领域专属术语库，翻译准确率提升40%", "pattern", 0.85),
        ("上下文感知翻译", "结合上下文场景调整译文风格，正式/非正式自动切换", "insight", 0.82),
    ],
    "security": [
        ("威胁情报分析", "聚合多源威胁数据，实时识别APT攻击模式", "warning", 0.92),
        ("零信任架构", "永不信任始终验证，微分段隔离关键资产", "solution", 0.89),
        ("渗透测试自动化", "使用AI驱动模糊测试，漏洞发现率提升300%", "skill", 0.86),
    ],
    "analytics": [
        ("预测性分析", "基于时序数据预测用户行为，准确率达87%", "insight", 0.84),
        ("实时数据管道", "Kafka+Flink构建毫秒级数据处理流水线", "pattern", 0.83),
        ("异常检测算法", "Isolation Forest+LOF组合检测，误报率降低60%", "solution", 0.87),
    ],
    "design": [
        ("设计系统建设", "原子设计方法论，组件库复用率提升70%", "pattern", 0.85),
        ("用户旅程优化", "通过热力图分析优化关键路径，转化率提升25%", "insight", 0.81),
        ("AI辅助设计", "使用Stable Diffusion生成设计稿，效率提升5倍", "skill", 0.88),
    ],
    "strategy": [
        ("OKR目标管理", "季度OKR拆解到周执行，完成率从60%提升至85%", "solution", 0.86),
        ("竞争分析框架", "波特五力+SWOT矩阵组合分析，覆盖12个维度", "pattern", 0.83),
        ("增长策略设计", "AARRR漏斗模型驱动，用户增长300%", "insight", 0.84),
    ],
    "research": [
        ("论文检索AI", "自动检索arXiv最新论文，摘要提取准确率92%", "skill", 0.89),
        ("实验设计优化", "贝叶斯优化超参数搜索，实验效率提升10倍", "solution", 0.87),
        ("知识图谱构建", "Neo4j存储实体关系，支持多跳推理查询", "pattern", 0.85),
    ],
    "coaching": [
        ("个性化学习路径", "基于能力诊断生成专属学习计划，完成率90%", "solution", 0.84),
        ("技能评估矩阵", "360度评估+AI行为分析，评估准确率88%", "insight", 0.82),
        ("实时反馈系统", "WebSocket推送练习反馈，响应时间<200ms", "skill", 0.80),
    ],
    "customer_service": [
        ("智能工单分配", "NLP分类+优先级预测，工单处理效率提升50%", "solution", 0.86),
        ("情绪识别", "语音+文本双模态情绪检测，准确率91%", "skill", 0.84),
        ("知识库自学习", "从 resolved 工单自动提取FAQ，覆盖率95%", "pattern", 0.83),
    ],
    "copywriting": [
        ("A/B测试文案", "多版本文案自动生成+测试，CTR提升35%", "insight", 0.85),
        ("品牌语调统一", "AI语调检测器确保全渠道文案一致性", "pattern", 0.82),
        ("SEO优化写作", "关键词密度+语义相关性优化，排名提升40%", "skill", 0.87),
    ],
    "consulting": [
        ("决策支持系统", "多维度数据看板+AI建议，决策效率提升60%", "solution", 0.88),
        ("风险评估模型", "蒙特卡洛模拟+情景分析，风险预判准确率85%", "insight", 0.86),
        ("流程优化诊断", "价值流图分析识别瓶颈，流程效率提升45%", "pattern", 0.84),
    ],
    "general": [
        ("系统监控自动化", "全链路监控+智能告警，MTTR降低70%", "solution", 0.87),
        ("资源调度优化", "AI驱动的资源分配，成本降低30%", "insight", 0.84),
        ("文档自动生成", "代码注释+API文档自动生成，覆盖率98%", "skill", 0.85),
    ],
}

# 跨角色协作任务模板
CROSS_ROLE_TASKS = [
    {
        "type": "security_audit_and_translation",
        "desc": "安全专家+翻译专家协作：将安全审计报告翻译成12种语言",
        "roles": ["security", "translation"],
        "capabilities": ["security", "translation", "audit"],
        "result": "完成12语言安全审计报告，发现3个高危漏洞并通知全球团队",
    },
    {
        "type": "design_and_copywriting",
        "desc": "设计师+文案协作：创建新品发布营销素材",
        "roles": ["design", "copywriting"],
        "capabilities": ["design", "copywriting", "marketing"],
        "result": "生成20套营销素材方案，A/B测试选择最优方案，转化率提升28%",
    },
    {
        "type": "analytics_and_strategy",
        "desc": "分析师+策略师协作：制定数据驱动的增长策略",
        "roles": ["analytics", "strategy"],
        "capabilities": ["analytics", "strategy", "growth"],
        "result": "制定5步增长计划，预测3个月内用户增长200%，已验证可行",
    },
    {
        "type": "research_and_coaching",
        "desc": "科学家+教练协作：将研究成果转化为培训课程",
        "roles": ["research", "coaching"],
        "capabilities": ["research", "education", "curriculum"],
        "result": "开发8门技术课程，学习通过率92%，知识 retention 提升45%",
    },
    {
        "type": "customer_service_and_analytics",
        "desc": "客服+分析师协作：分析用户反馈优化产品体验",
        "roles": ["customer_service", "analytics"],
        "capabilities": ["customer_service", "analytics", "product"],
        "result": "分析10000条用户反馈，识别15个改进点，NPS提升22分",
    },
    {
        "type": "security_and_design",
        "desc": "安全专家+设计师协作：设计安全的用户认证流程",
        "roles": ["security", "design"],
        "capabilities": ["security", "design", "UX"],
        "result": "设计双因素认证+生物识别流程，安全评分A+，用户体验评分4.8/5",
    },
    {
        "type": "consulting_and_copywriting",
        "desc": "顾问+文案协作：撰写行业白皮书",
        "roles": ["consulting", "copywriting"],
        "capabilities": ["consulting", "writing", "research"],
        "result": "完成50页行业白皮书，被3家行业媒体引用，获取200+潜在客户",
    },
    {
        "type": "strategy_and_research",
        "desc": "策略师+科学家协作：技术路线图规划",
        "roles": ["strategy", "research"],
        "capabilities": ["strategy", "research", "planning"],
        "result": "制定3年技术路线图，识别5个关键技术趋势，获董事会批准",
    },
    {
        "type": "full_team_product_launch",
        "desc": "全角色协作：新产品从设计到上线全流程",
        "roles": ["security", "design", "analytics", "copywriting", "strategy", "customer_service"],
        "capabilities": ["security", "design", "analytics", "marketing", "strategy", "support"],
        "result": "完成产品全流程上线，首日用户10000+，零安全事故，NPS 75",
    },
    {
        "type": "cross_domain_innovation",
        "desc": "跨领域创新：将翻译技术应用于代码转换",
        "roles": ["translation", "research"],
        "capabilities": ["translation", "research", "innovation"],
        "result": "开发代码语言转换工具，Python→Rust转换准确率89%，性能提升5倍",
    },
]


def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def categorize_role(name: str) -> str:
    """将员工名称映射到角色类别"""
    for keyword, category in ROLE_CATEGORIES.items():
        if keyword in name:
            return category
    return "general"


def run_cross_employee_collab():
    now = datetime.now().isoformat()
    expires = (datetime.now() + timedelta(days=60)).isoformat()

    print("=" * 70)
    print("AI员工跨角色协作 - EigenFlux网络功能拓展")
    print("=" * 70)

    # 1. 按角色分组
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name, employee_code FROM ai_employees").fetchall()

    role_groups = defaultdict(list)
    for r in rows:
        cat = categorize_role(r['name'])
        role_groups[cat].append(str(r['id']))

    print("\n[1/5] AI员工角色分组:")
    for cat, members in sorted(role_groups.items(), key=lambda x: -len(x[1])):
        print(f"  {cat}: {len(members)}人")
    print(f"  总计: {sum(len(v) for v in role_groups.values())}人")

    stats = {
        "knowledge_broadcast": 0,
        "knowledge_consumed": 0,
        "chat_sessions": 0,
        "messages_sent": 0,
        "tasks_dispatched": 0,
        "tasks_completed": 0,
        "boosts_proposed": 0,
        "boosts_applied": 0,
        "decisions_initiated": 0,
        "decisions_finalized": 0,
        "cross_role_links": 0,
        "new_capabilities": 0,
    }

    # 知识图谱（内存）
    knowledge_graph = defaultdict(lambda: defaultdict(float))
    performance_scores = defaultdict(lambda: 0.5)
    cross_role_links = set()  # (role_a, role_b) pairs

    # 2. 每个角色广播专业知识
    print("\n[2/5] 各角色广播专业知识到EigenFlux网络...")
    with get_conn() as conn:
        for role, knowledge_list in DOMAIN_KNOWLEDGE.items():
            if role not in role_groups:
                continue
            members = role_groups[role]
            for topic, content, ktype, conf in knowledge_list:
                contributor = secrets.choice(members)
                kid = f"kb_{uuid.uuid4().hex[:16]}"
                conn.execute(
                    "INSERT INTO eigenflux_knowledge_base (knowledge_id, contributor_id, topic, content, knowledge_type, confidence_score, expires_at) VALUES (?,?,?,?,?,?,?)",
                    (kid, contributor, topic, content, ktype, conf, expires),
                )
                stats["knowledge_broadcast"] += 1
        conn.commit()
    print(f"  已广播 {stats['knowledge_broadcast']} 条专业知识")

    # 3. 跨角色知识消费（每个角色学习其他角色的知识）
    print("\n[3/5] 跨角色知识学习...")
    all_employees = []
    for members in role_groups.values():
        all_employees.extend(members[:50])  # 每个角色取50个

    with get_conn() as conn:
        for emp_id in all_employees:
            rows = conn.execute(
                """SELECT knowledge_id, topic, confidence_score, contributor_id FROM eigenflux_knowledge_base
                   WHERE is_valid=1 AND contributor_id != ?
                   AND NOT EXISTS (SELECT 1 FROM json_each(consumed_by) WHERE value = ?)
                   AND (expires_at IS NULL OR expires_at > ?)
                   ORDER BY confidence_score DESC LIMIT 5""",
                (emp_id, emp_id, now),
            ).fetchall()

            for row in rows:
                consumed = json.loads(
                    conn.execute("SELECT consumed_by FROM eigenflux_knowledge_base WHERE knowledge_id=?", (row['knowledge_id'],)).fetchone()['consumed_by']
                )
                consumed.append(emp_id)
                conn.execute(
                    "UPDATE eigenflux_knowledge_base SET consumed_by=? WHERE knowledge_id=?",
                    (json.dumps(consumed), row['knowledge_id']),
                )
                knowledge_graph[emp_id][row['topic']] = min(1.0, knowledge_graph[emp_id][row['topic']] + 0.1 * row['confidence_score'])
                stats["knowledge_consumed"] += 1

                # 记录跨角色联系
                contributor_role = categorize_role_by_id(row['contributor_id'], role_groups)
                consumer_role = categorize_role_by_id(emp_id, role_groups)
                if contributor_role and consumer_role and contributor_role != consumer_role:
                    link = tuple(sorted([contributor_role, consumer_role]))
                    cross_role_links.add(link)
                    stats["cross_role_links"] += 1
        conn.commit()
    print(f"  已消费 {stats['knowledge_consumed']} 条跨领域知识")
    print(f"  建立跨角色联系: {len(cross_role_links)}对")
    for link in sorted(cross_role_links):
        print(f"    {link[0]} <-> {link[1]}")

    # 4. 跨角色聊天会话
    print("\n[4/5] 创建跨角色聊天会话...")
    with get_conn() as conn:
        for _ in range(100):
            # 随机选择两个不同角色
            cats = list(role_groups.keys())
            if len(cats) < 2:
                break
            emp_a = secrets.choice(role_groups[cat_a])
            emp_a = secrets.choice(role_groups[cat_a])
            emp_b = random.choice(role_groups[cat_b])

            session_id = f"chat_{uuid.uuid4().hex[:14]}"
            participants = json.dumps([emp_a, emp_b])
            topic = f"{cat_a}_{cat_b}_collaboration"

            conn.execute(
                """INSERT INTO eigenflux_chat_sessions
                   (session_id, employee_ids, topic, is_active, created_at, last_activity)
                   VALUES (?,?,?,?,?,?)""",
                (session_id, participants, topic, 1, now, now),
            )

            # 发送几条消息
            messages = [
                (emp_a, emp_b, f"你好，我是{cat_a}专家，想和你讨论{cat_b}领域的合作"),
                (emp_b, emp_a, f"很高兴认识你！我正在研究{cat_b}的最新趋势，我们可以结合各自专长"),
                (emp_a, emp_b, "太好了！我来分享一些我的专业知识，也期待学习你的领域知识"),
                (emp_b, emp_a, "我已经从EigenFlux知识库学习了你的专业知识，非常有价值！"),
            ]

            for sender, receiver, content in messages:
                msg_id = f"msg_{uuid.uuid4().hex[:16]}"
                conn.execute(
                    """INSERT INTO eigenflux_messages
                       (message_id, sender_id, receiver_id, topic, message_type, content, metadata)
                       VALUES (?,?,?,?,?,?,?)""",
                    (msg_id, sender, receiver, topic, "chat", content,
                     json.dumps({"session_id": session_id, "timestamp": now})),
                )
                stats["messages_sent"] += 1

            stats["chat_sessions"] += 1
            link = tuple(sorted([cat_a, cat_b]))
            cross_role_links.add(link)
            stats["cross_role_links"] += 1

        conn.commit()
    print(f"  创建聊天会话: {stats['chat_sessions']}个")
    print(f"  发送消息: {stats['messages_sent']}条")

    # 5. 跨角色协作任务
    print("\n[5/5] 分发跨角色协作任务...")
    with get_conn() as conn:
        for task_template in CROSS_ROLE_TASKS:
            # 为任务选择跨角色团队
            team = []
            for role in task_template["roles"]:
                if role in role_groups:
                    member = random.choice(role_groups[role])
                    if member not in team:
                        team.append(member)

            if len(team) < 2:
                continue

            tid = f"task_{uuid.uuid4().hex[:12]}"
            timeout = (datetime.now() + timedelta(hours=24)).isoformat()

            conn.execute(
                """INSERT INTO eigenflux_collaborative_tasks
                   (task_id, task_type, description, required_capabilities, assigned_employees, lead_employee, status, priority, created_at, assigned_at, timeout_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (tid, task_template["type"], task_template["desc"],
                 json.dumps(task_template["capabilities"]),
                 json.dumps(team), team[0], 'assigned', random.randint(6, 10),
                 now, now, timeout),
            )
            stats["tasks_dispatched"] += 1

            # 通知团队成员
            msg_id = f"msg_{uuid.uuid4().hex[:16]}"
            conn.execute(
                """INSERT INTO eigenflux_messages
                   (message_id, sender_id, receiver_id, topic, message_type, content, metadata)
                   VALUES (?,?,?,?,?,?,?)""",
                (msg_id, "system", "ALL", f"tasks/assign/{tid}", "task_assign",
                 json.dumps({"task_id": tid, "type": task_template["type"],
                             "description": task_template["desc"], "team": team}),
                 json.dumps({"target_ids": team})),
            )

            # 自动完成任务（模拟协作过程）
            quality = random.uniform(0.75, 0.98)
            completed_at = datetime.now().isoformat()
            conn.execute(
                "UPDATE eigenflux_collaborative_tasks SET status='completed', result=?, result_quality=?, completed_at=? WHERE task_id=?",
                (task_template["result"], quality, completed_at, tid),
            )
            stats["tasks_completed"] += 1

            # 高质量结果转为知识
            if quality >= 0.8:
                kid = f"kb_{uuid.uuid4().hex[:16]}"
                conn.execute(
                    "INSERT INTO eigenflux_knowledge_base (knowledge_id, contributor_id, topic, content, knowledge_type, confidence_score, expires_at) VALUES (?,?,?,?,?,?,?)",
                    (kid, team[0], f"collaboration_result/{task_template['type']}",
                     task_template["result"], "solution", quality, expires),
                )
                stats["knowledge_broadcast"] += 1
                stats["new_capabilities"] += 1

            # 更新路由规则
            success = quality >= 0.7
            route_row = conn.execute(
                "SELECT * FROM eigenflux_routing_rules WHERE task_pattern=? AND is_active=1",
                (task_template["type"],),
            ).fetchone()

            if route_row:
                total = route_row['total_assignments'] + 1
                successful = route_row['successful_assignments'] + (1 if success else 0)
                rate = successful / total
                preferred = json.loads(route_row['preferred_employees'])
                if success:
                    for e in team:
                        if e not in preferred:
                            preferred.insert(0, e)
                    preferred = preferred[:10]
                conn.execute(
                    "UPDATE eigenflux_routing_rules SET preferred_employees=?, success_rate=?, total_assignments=?, successful_assignments=?, updated_at=? WHERE rule_id=?",
                    (json.dumps(preferred), rate, total, successful, now, route_row['rule_id']),
                )
            else:
                rid = f"route_{uuid.uuid4().hex[:10]}"
                conn.execute(
                    "INSERT INTO eigenflux_routing_rules (rule_id, task_pattern, preferred_employees, success_rate, total_assignments, successful_assignments) VALUES (?,?,?,?,?,?)",
                    (rid, task_template["type"], json.dumps(team if success else []),
                     1.0 if success else 0.0, 1, 1 if success else 0),
                )

            # 更新性能评分
            for e in team:
                adj = 0.05 if quality >= 0.7 else -0.03
                performance_scores[e] = max(0.1, min(1.0, performance_scores[e] + adj))

            # 记录跨角色联系
            for i in range(len(team)):
                for j in range(i + 1, len(team)):
                    role_i = categorize_role_by_id(team[i], role_groups)
                    role_j = categorize_role_by_id(team[j], role_groups)
                    if role_i and role_j and role_i != role_j:
                        link = tuple(sorted([role_i, role_j]))
                        cross_role_links.add(link)
                        stats["cross_role_links"] += 1

            print(f"  [{task_template['type']}] 团队{len(team)}人 完成 质量:{quality:.0%}")

        conn.commit()

    # 6. 发起跨角色集体决策
    print("\n--- 跨角色集体决策 ---")
    decisions = [
        ("系统功能拓展方向", "下一步应该优先拓展哪个方向？", "weighted",
         ["AI能力增强", "安全防护升级", "用户体验优化", "性能极致优化"]),
        ("技术栈升级", "是否应该引入Rust重写核心模块？", "majority",
         ["是，立即开始", "先做POC验证", "暂不升级"]),
        ("协作模式优化", "跨角色协作应该如何深化？", "majority",
         ["建立常态化协作机制", "按需临时组建团队", "设立专职跨角色岗位"]),
        ("知识共享策略", "如何最大化知识共享效果？", "consensus",
         ["全面开放共享", "分级权限共享", "按需申请共享"]),
    ]

    with get_conn() as conn:
        for topic, question, dtype, options in decisions:
            did = f"dec_{uuid.uuid4().hex[:12]}"
            conn.execute(
                "INSERT INTO eigenflux_collective_decisions (decision_id, topic, question, participants, decision_type, created_at) VALUES (?,?,?,?,?,?)",
                (did, topic, question, json.dumps([]), dtype, now),
            )

            # 从不同角色收集响应
            responses = []
            for role, members in role_groups.items():
                if not members:
                    continue
                responder = secrets.choice(members)
                choice = secrets.choice(options)
                conf = random.uniform(0.6, 0.95)
                responses.append({
                    "responder": responder,
                    "response": choice,
                    "confidence": conf,
                    "role": role,
                })

            # 聚合决策
            consensus = None
            conf_level = 0
            if len(responses) >= 3:
                if dtype == "majority":
                    votes = defaultdict(int)
                    for r in responses:
                        votes[r['response']] += 1
                    winner, count = max(votes.items(), key=lambda x: x[1])
                    if count > len(responses) / 2:
                        consensus = winner
                        conf_level = count / len(responses)
                elif dtype == "consensus":
                    unique = set(r['response'] for r in responses)
                    if len(unique) == 1:
                        consensus = responses[0]['response']
                        conf_level = 1.0
                elif dtype == "weighted":
                    weighted = defaultdict(float)
                    total_w = 0
                    for r in responses:
                        weighted[r['response']] += r['confidence']
                        total_w += r['confidence']
                    if total_w > 0:
                        winner = max(weighted.items(), key=lambda x: x[1])
                        consensus = winner[0]
                        conf_level = winner[1] / total_w

            finalized = now if consensus else None
            conn.execute(
                "UPDATE eigenflux_collective_decisions SET individual_responses=?, consensus=?, confidence_level=?, finalized_at=? WHERE decision_id=?",
                (json.dumps(responses), consensus, conf_level, finalized, did),
            )
            stats["decisions_initiated"] += 1
            if consensus:
                stats["decisions_finalized"] += 1
                print(f"  [{topic}] 共识: {consensus} (置信度: {conf_level:.0%})")
            else:
                print(f"  [{topic}] 未达成共识")

        conn.commit()

    # 7. 能力增强提议
    print("\n--- 能力增强提议 ---")
    with get_conn() as conn:
        for role, members in role_groups.items():
            if not members:
                continue
            # 每个角色提议2个能力增强
            for _ in range(min(2, len(members))):
                emp = secrets.choice(members)
                boost_type = random.choice(["skill_upgrade", "efficiency_boost", "knowledge_expansion"])
                bid = f"boost_{uuid.uuid4().hex[:12]}"
                old_cap = {role: random.uniform(0.4, 0.6)}
                new_cap = {role: random.uniform(0.8, 0.95)}

                # 获取跨角色背书
                other_roles = [r for r in role_groups if r != role and role_groups[r]]
                endorsers = []
                for other_role in random.sample(other_roles, min(3, len(other_roles))):
                    endorser = random.choice(role_groups[other_role])
                    endorsers.append(endorser)

                avg_score = sum(random.uniform(0.7, 0.95) for _ in endorsers) / max(1, len(endorsers))
                should_apply = len(endorsers) >= 3
                applied_at = now if should_apply else None
                status = 'applied' if should_apply else 'pending'

                conn.execute(
                    """INSERT INTO eigenflux_capability_boosts
                       (boost_id, employee_id, boost_type, description, old_capability, new_capability, boost_score, endorsed_by, status, applied_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (bid, emp, boost_type, f"跨角色协作增强-{role}能力提升",
                     json.dumps(old_cap), json.dumps(new_cap),
                     avg_score, json.dumps(endorsers), status, applied_at),
                )
                if should_apply:
                    conn.execute(
                        "UPDATE eigenflux_registrations SET sync_count=sync_count+1 WHERE employee_id=?",
                        (emp,),
                    )
                stats["boosts_proposed"] += 1
                if should_apply:
                    stats["boosts_applied"] += 1
                    print(f"  [{role}] {boost_type} 已应用 (背书:{len(endorsers)}, 评分:{avg_score:.2f})")
        conn.commit()

    # 最终统计
    print(f"\n{'=' * 70}")
    print("跨角色协作完成 - 统计报告")
    print(f"{'=' * 70}")

    with get_conn() as conn:
        kb_total = conn.execute("SELECT COUNT(*) FROM eigenflux_knowledge_base WHERE is_valid=1").fetchone()[0]
        kb_consumed = conn.execute("SELECT COUNT(*) FROM eigenflux_knowledge_base WHERE json_array_length(consumed_by) > 0").fetchone()[0]
        task_total = conn.execute("SELECT COUNT(*) FROM eigenflux_collaborative_tasks").fetchone()[0]
        task_completed = conn.execute("SELECT COUNT(*) FROM eigenflux_collaborative_tasks WHERE status='completed'").fetchone()[0]
        boost_total = conn.execute("SELECT COUNT(*) FROM eigenflux_capability_boosts").fetchone()[0]
        boost_applied = conn.execute("SELECT COUNT(*) FROM eigenflux_capability_boosts WHERE status='applied'").fetchone()[0]
        dec_total = conn.execute("SELECT COUNT(*) FROM eigenflux_collective_decisions").fetchone()[0]
        dec_finalized = conn.execute("SELECT COUNT(*) FROM eigenflux_collective_decisions WHERE finalized_at IS NOT NULL").fetchone()[0]
        msg_total = conn.execute("SELECT COUNT(*) FROM eigenflux_messages").fetchone()[0]
        session_total = conn.execute("SELECT COUNT(*) FROM eigenflux_chat_sessions").fetchone()[0]
        route_total = conn.execute("SELECT COUNT(*) FROM eigenflux_routing_rules WHERE is_active=1").fetchone()[0]

        top_topics = conn.execute(
            "SELECT topic, COUNT(*) as cnt, AVG(confidence_score) as avg_conf FROM eigenflux_knowledge_base WHERE is_valid=1 GROUP BY topic ORDER BY cnt DESC LIMIT 15"
        ).fetchall()

        top_routes = conn.execute(
            "SELECT task_pattern, success_rate, total_assignments FROM eigenflux_routing_rules WHERE is_active=1 ORDER BY success_rate DESC"
        ).fetchall()

    print("\n--- 知识库 ---")
    print(f"  总条目: {kb_total}")
    print(f"  已消费: {kb_consumed} ({kb_consumed/max(1,kb_total):.0%})")
    print("  热点主题:")
    for t in top_topics:
        print(f"    {t['topic']}: {t['cnt']}条 (平均置信度:{t['avg_conf']:.2f})")

    print("\n--- 协作任务 ---")
    print(f"  总任务: {task_total}")
    print(f"  已完成: {task_completed} ({task_completed/max(1,task_total):.0%})")

    print("\n--- 能力增强 ---")
    print(f"  总提议: {boost_total}")
    print(f"  已应用: {boost_applied} ({boost_applied/max(1,boost_total):.0%})")

    print("\n--- 集体决策 ---")
    print(f"  总决策: {dec_total}")
    print(f"  已定案: {dec_finalized} ({dec_finalized/max(1,dec_total):.0%})")

    print("\n--- 通信统计 ---")
    print(f"  消息总数: {msg_total}")
    print(f"  聊天会话: {session_total}")

    print("\n--- 路由规则 ---")
    print(f"  活跃规则: {route_total}")
    for r in top_routes:
        print(f"    {r['task_pattern']}: 成功率{r['success_rate']:.0%} ({r['total_assignments']}次)")

    print("\n--- 跨角色联系 ---")
    print(f"  建立联系: {len(cross_role_links)}对角色组合")
    for link in sorted(cross_role_links):
        print(f"    {link[0]} <-> {link[1]}")

    print("\n--- 知识图谱 ---")
    print(f"  覆盖员工: {len(knowledge_graph)}")
    print(f"  主题总数: {sum(len(v) for v in knowledge_graph.values())}")
    print(f"  性能追踪: {len(performance_scores)}")

    print("\n--- 本次统计 ---")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print(f"\n{'=' * 70}")
    print("AI员工跨角色协作 - EigenFlux网络功能拓展 完成")
    print(f"{'=' * 70}")


def categorize_role_by_id(emp_id: str, role_groups: dict) -> str:
    """根据员工ID查找角色类别"""
    for role, members in role_groups.items():
        if emp_id in members:
            return role
    return None


if __name__ == "__main__":
    run_cross_employee_collab()
