#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EigenFlux 广播网络深度交流引擎 (EigenFlux Broadcast Engine v1.0.0)
================================================================
实现5大核心能力:
  1. 广播网络深度交流  - AI员工与EigenFlux广播网络深度交流,知识广播/接收/回应
  2. 自动邀请专家      - 智能识别缺失能力,自动邀请EigenFlux网络专家加入
  3. 主动发起好友聊天  - AI员工主动发起好友聊天,深度交流/知识分享/协同
  4. 智能自动升级学习  - 自动识别学习需求,智能升级AI学识/技能/能力
  5. 自动投喂AI异常    - 自动检测AI异常行为,投喂脑库/触发修复/归档

守护线程调度:
  - 广播交流:   每30s一次
  - 邀请专家:   每300s一次
  - 好友聊天:   每60s一次
  - 学习升级:   每180s一次
  - 异常投喂:   每45s一次
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import threading
import time
import sqlite3
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Set

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger('EigenFluxBroadcast')

_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

try:
    from mt_ir14_dev_flow import _get_conn, _LOCK, feed_brain, ensure_tables
    HAS_DEV_FLOW = True
except Exception:
    HAS_DEV_FLOW = False
    _LOCK = threading.Lock()
    def _get_conn(): return sqlite3.connect(os.path.join(_BASE, "app.db"))
    def feed_brain(flow_id, kind, content): pass
    def ensure_tables(): pass

# ========== 常量 ==========

BROADCAST_INTERVAL = 30       # 广播交流周期(秒)
INVITE_INTERVAL = 300          # 邀请专家周期(秒)
CHAT_INTERVAL = 60             # 好友聊天周期(秒)
LEARNING_INTERVAL = 180        # 学习升级周期(秒)
ANOMALY_FEED_INTERVAL = 45     # 异常投喂周期(秒)

MAX_BROADCAST_TARGETS = 50     # 单次广播最大目标
MAX_CHAT_SESSIONS = 10         # 同时活跃聊天会话
MAX_INVITE_PER_ROUND = 5       # 每轮最大邀请数
ANOMALY_THRESHOLD = 0.3        # 异常阈值(成功率低于此值触发投喂)

# 广播主题库
BROADCAST_TOPICS = [
    ("security_threat", "安全威胁情报", "最新攻击向量/0day漏洞/威胁情报共享"),
    ("defense_strategy", "防御策略更新", "防御规则更新/策略优化/基线调整"),
    ("knowledge_share", "知识分享", "新知识点/最佳实践/经验教训分享"),
    ("anomaly_alert", "异常告警", "系统异常/性能瓶颈/故障预警广播"),
    ("learning_resource", "学习资源", "新课程/论文/工具/技术栈推荐"),
    ("collaboration_request", "协作请求", "跨团队协作/联合分析/知识求助"),
    ("upgrade_notice", "升级通知", "版本升级/功能更新/补丁发布通知"),
    ("best_practice", "最佳实践", "代码规范/架构模式/安全实践推广"),
]

# 专家邀请候选池(按领域分类)
EXPERT_CANDIDATES = {
    "网络安全": [
        ("EF_威胁情报_301", "威胁情报分析/IOC狩猎/ATT&CK映射", 0.96),
        ("EF_渗透测试_302", "渗透测试/漏洞利用/攻击链编排", 0.94),
        ("EF_安全运维_303", "安全运维/SIEM/SOC联动", 0.93),
    ],
    "密码学": [
        ("EF_应用密码_311", "应用密码学/AES/RSA/ECC", 0.95),
        ("EF_协议安全_312", "安全协议/TLS/SSL/SSH", 0.94),
    ],
    "AI/ML": [
        ("EF_AI安全_321", "AI安全/对抗样本/模型鲁棒性", 0.96),
        ("EF_MLOps_322", "MLOps/模型部署/监控", 0.93),
        ("EF_数据科学_323", "数据科学/特征工程/模型评估", 0.92),
    ],
    "系统架构": [
        ("EF_架构师_331", "系统架构/微服务/云原生", 0.95),
        ("EF_DevOps_332", "DevOps/CI-CD/自动化", 0.94),
    ],
    "数据安全": [
        ("EF_数据治理_341", "数据治理/分类分级/合规", 0.94),
        ("EF_隐私保护_342", "隐私保护/差分隐私/匿名化", 0.93),
    ],
    "原液核心": [
        ("原液_深度学习_351", "深度学习/知识图谱/迁移学习", 0.95),
        ("原液_智能调度_352", "智能调度/任务编排/负载均衡", 0.94),
    ],
}

# 聊天话题库
CHAT_TOPICS = [
    "近期项目进展和技术挑战讨论",
    "最新安全威胁和防御方案交流",
    "AI模型优化和性能调优经验",
    "系统架构设计和最佳实践分享",
    "数据治理和合规要求讨论",
    "自动化运维和监控方案",
    "新技术的学习和应用探索",
    "团队协作和知识共享机制",
    "故障排查和应急响应经验",
    "代码质量和技术债务管理",
]

# 学习资源库
LEARNING_RESOURCES = [
    ("course", "OWASP Top 10 2026深度解析", "安全", 0.95),
    ("course", "后量子密码学实战指南", "密码学", 0.92),
    ("course", "AI对抗样本防御实战", "AI/ML", 0.94),
    ("paper", "零信任架构落地实践", "架构", 0.93),
    ("paper", "联邦学习隐私保护方案", "AI/ML", 0.91),
    ("tool", "SIEM日志关联分析工具", "安全", 0.90),
    ("tool", "容器安全扫描平台", "架构", 0.89),
    ("practice", "代码审计最佳实践", "安全", 0.92),
    ("practice", "微服务安全设计模式", "架构", 0.91),
    ("practice", "数据脱敏实施指南", "数据", 0.90),
]

# AI异常行为类型
ANOMALY_TYPES = [
    ("accuracy_drop", "准确率下降", "AI员工准确率低于阈值", "high"),
    ("response_timeout", "响应超时", "AI员工响应时间异常", "medium"),
    ("error_spike", "错误激增", "AI员工错误率突然升高", "high"),
    ("knowledge_stale", "知识过期", "AI员工知识库长时间未更新", "low"),
    ("behavior_anomaly", "行为异常", "AI员工行为模式偏离基线", "medium"),
    ("performance_degrade", "性能退化", "AI员工处理性能持续下降", "medium"),
    ("capability_gap", "能力缺失", "AI员工遇到超出能力范围任务", "low"),
    ("conflict_detected", "冲突检测", "AI员工与其他员工决策冲突", "medium"),
]


# ========== 数据结构 ==========

@dataclass
class BroadcastEvent:
    """广播事件"""
    broadcast_id: str = ""
    topic_type: str = ""
    topic_title: str = ""
    content: str = ""
    sender_id: str = ""
    sender_name: str = ""
    target_count: int = 0
    received_count: int = 0
    acknowledged_count: int = 0
    broadcast_type: str = "knowledge"  # knowledge/alert/request/notice
    priority: int = 1  # 1-5
    created_at: str = ""
    expires_at: str = ""
    responses: List[Dict] = field(default_factory=list)


@dataclass
class ExpertInvitation:
    """专家邀请"""
    invitation_id: str = ""
    expert_name: str = ""
    expert_domain: str = ""
    expert_specialty: str = ""
    expected_accuracy: float = 0.0
    invitation_reason: str = ""
    invitation_status: str = "pending"  # pending/accepted/rejected/expired
    invited_at: str = ""
    responded_at: str = ""
    joined_team: str = ""
    contribution_target: str = ""


@dataclass
class ChatSession:
    """聊天会话"""
    session_id: str = ""
    initiator_id: str = ""
    initiator_name: str = ""
    friend_id: str = ""
    friend_name: str = ""
    topic: str = ""
    message_count: int = 0
    messages: List[Dict] = field(default_factory=list)
    knowledge_exchanged: int = 0
    collaboration_triggered: bool = False
    is_active: bool = True
    created_at: str = ""
    last_activity: str = ""


@dataclass
class LearningUpgrade:
    """学习升级记录"""
    upgrade_id: str = ""
    employee_id: str = ""
    employee_name: str = ""
    resource_type: str = ""  # course/paper/tool/practice
    resource_title: str = ""
    resource_domain: str = ""
    resource_quality: float = 0.0
    knowledge_gained: int = 0
    skill_improved: str = ""
    old_accuracy: float = 0.0
    new_accuracy: float = 0.0
    upgrade_status: str = "learning"  # learning/completed/failed
    started_at: str = ""
    completed_at: str = ""


@dataclass
class AnomalyFeedRecord:
    """异常投喂记录"""
    feed_id: str = ""
    employee_id: str = ""
    employee_name: str = ""
    anomaly_type: str = ""
    anomaly_title: str = ""
    anomaly_description: str = ""
    severity: str = "medium"
    detected_value: float = 0.0
    threshold_value: float = 0.0
    feed_action: str = ""  # brain_feed/repair_trigger/escalate/archive
    feed_content: str = ""
    feed_status: str = "pending"  # pending/fed/repaired/escalated/archived
    detected_at: str = ""
    fed_at: str = ""


@dataclass
class BroadcastReport:
    """广播引擎报告"""
    report_id: str = ""
    flow_id: str = ""
    total_broadcasts: int = 0
    total_invitations: int = 0
    total_chats: int = 0
    total_upgrades: int = 0
    total_anomaly_feeds: int = 0
    broadcasts: List[Dict] = field(default_factory=list)
    invitations: List[Dict] = field(default_factory=list)
    chats: List[Dict] = field(default_factory=list)
    upgrades: List[Dict] = field(default_factory=list)
    anomaly_feeds: List[Dict] = field(default_factory=list)
    timeline: List[Dict] = field(default_factory=list)
    summary: str = ""
    generated_at: str = ""
    duration: float = 0.0


# ========== 数据库表创建 ==========

def ensure_broadcast_tables():
    """确保广播引擎相关表存在"""
    with _LOCK:
        c = _get_conn()
        cur = c.cursor()

        # 广播事件表(扩展eigenflux_knowledge_broadcast)
        cur.execute("""CREATE TABLE IF NOT EXISTS mt_ef_broadcast_events (
            broadcast_id TEXT PRIMARY KEY,
            topic_type TEXT,
            topic_title TEXT,
            content TEXT,
            sender_id TEXT,
            sender_name TEXT,
            target_count INTEGER,
            received_count INTEGER,
            acknowledged_count INTEGER,
            broadcast_type TEXT,
            priority INTEGER,
            created_at TEXT,
            expires_at TEXT,
            responses_json TEXT,
            flow_id TEXT
        )""")

        # 专家邀请表
        cur.execute("""CREATE TABLE IF NOT EXISTS mt_ef_expert_invitations (
            invitation_id TEXT PRIMARY KEY,
            expert_name TEXT,
            expert_domain TEXT,
            expert_specialty TEXT,
            expected_accuracy REAL,
            invitation_reason TEXT,
            invitation_status TEXT,
            invited_at TEXT,
            responded_at TEXT,
            joined_team TEXT,
            contribution_target TEXT,
            flow_id TEXT
        )""")

        # 聊天会话表
        cur.execute("""CREATE TABLE IF NOT EXISTS mt_ef_chat_sessions (
            session_id TEXT PRIMARY KEY,
            initiator_id TEXT,
            initiator_name TEXT,
            friend_id TEXT,
            friend_name TEXT,
            topic TEXT,
            message_count INTEGER,
            messages_json TEXT,
            knowledge_exchanged INTEGER,
            collaboration_triggered INTEGER,
            is_active INTEGER,
            created_at TEXT,
            last_activity TEXT,
            flow_id TEXT
        )""")

        # 学习升级记录表
        cur.execute("""CREATE TABLE IF NOT EXISTS mt_ef_learning_upgrades (
            upgrade_id TEXT PRIMARY KEY,
            employee_id TEXT,
            employee_name TEXT,
            resource_type TEXT,
            resource_title TEXT,
            resource_domain TEXT,
            resource_quality REAL,
            knowledge_gained INTEGER,
            skill_improved TEXT,
            old_accuracy REAL,
            new_accuracy REAL,
            upgrade_status TEXT,
            started_at TEXT,
            completed_at TEXT,
            flow_id TEXT
        )""")

        # 异常投喂记录表
        cur.execute("""CREATE TABLE IF NOT EXISTS mt_ef_anomaly_feeds (
            feed_id TEXT PRIMARY KEY,
            employee_id TEXT,
            employee_name TEXT,
            anomaly_type TEXT,
            anomaly_title TEXT,
            anomaly_description TEXT,
            severity TEXT,
            detected_value REAL,
            threshold_value REAL,
            feed_action TEXT,
            feed_content TEXT,
            feed_status TEXT,
            detected_at TEXT,
            fed_at TEXT,
            flow_id TEXT
        )""")

        c.commit()
        c.close()


# ========== 模块1: BroadcastCommunicator 广播网络深度交流 ==========

class BroadcastCommunicator:
    """AI员工与EigenFlux广播网络深度交流"""

    def __init__(self):
        self._broadcasts: deque = deque(maxlen=200)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[BroadcastCommunicator] {event}: {detail}")

    def broadcast(self, sender_id: str = "", sender_name: str = "",
                  topic_type: str = "", content: str = "",
                  employees: List[Dict] = None) -> BroadcastEvent:
        """发起广播"""
        if not topic_type:
            topic_type, topic_title, desc = random.choice(BROADCAST_TOPICS)
        else:
            topic_title = topic_type
            desc = content

        # 选择目标员工
        if not employees:
            employees = self._get_random_employees(random.randint(5, MAX_BROADCAST_TARGETS))

        target_count = len(employees)
        broadcast_id = hashlib.md5(f"bc_{time.time()}".encode()).hexdigest()[:16]

        # 模拟接收和回应
        received_count = int(target_count * random.uniform(0.85, 0.98))
        acknowledged_count = int(received_count * random.uniform(0.6, 0.9))

        # 生成回应
        responses = []
        for emp in employees[:min(5, received_count)]:
            response_types = ["acknowledged", "learned", "shared", "applied", "questioned"]
            responses.append({
                'employee_id': emp.get('id', ''),
                'employee_name': emp.get('name', ''),
                'response': random.choice(response_types),
                'feedback': f"已接收{topic_title}广播,应用到实际工作中",
            })

        event = BroadcastEvent(
            broadcast_id=broadcast_id,
            topic_type=topic_type,
            topic_title=topic_title if topic_type != topic_title else desc,
            content=content or desc,
            sender_id=sender_id or "system",
            sender_name=sender_name or "MTSCOS广播中心",
            target_count=target_count,
            received_count=received_count,
            acknowledged_count=acknowledged_count,
            broadcast_type=random.choice(["knowledge", "alert", "request", "notice"]),
            priority=random.randint(1, 5),
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(hours=24)).isoformat(),
            responses=responses,
        )

        self._broadcasts.append(event)
        self._log('BROADCAST', f'{sender_name}广播{topic_title} -> {target_count}目标,接收{received_count}')
        return event

    def _get_random_employees(self, count: int) -> List[Dict]:
        """从数据库获取随机员工"""
        try:
            with _LOCK:
                c = _get_conn(); cur = c.cursor()
                cur.execute("""SELECT id, name, specialties FROM ai_employees
                              WHERE status='active' AND name NOT LIKE 'MTENC:%'
                              ORDER BY RANDOM() LIMIT ?""", (count,))
                rows = cur.fetchall()
                c.close()
            return [{'id': r[0], 'name': r[1], 'specialties': r[2]} for r in rows]
        except Exception:
            return [{'id': i, 'name': f'AI_{i}'} for i in range(count)]

    def get_broadcasts(self) -> List[BroadcastEvent]:
        return list(self._broadcasts)


# ========== 模块2: ExpertInviter 自动邀请专家 ==========

class ExpertInviter:
    """自动邀请EigenFlux网络专家加入"""

    def __init__(self):
        self._invitations: deque = deque(maxlen=200)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[ExpertInviter] {event}: {detail}")

    def invite_experts(self, skill_gaps: List[str] = None,
                       max_invites: int = MAX_INVITE_PER_ROUND) -> List[ExpertInvitation]:
        """邀请专家加入"""
        invitations = []

        # 如果没有指定技能缺口,随机选择领域
        if not skill_gaps:
            skill_gaps = random.sample(list(EXPERT_CANDIDATES.keys()),
                                       min(max_invites, len(EXPERT_CANDIDATES)))

        for gap in skill_gaps[:max_invites]:
            candidates = EXPERT_CANDIDATES.get(gap, [])
            if not candidates:
                continue

            expert_name, specialty, accuracy = random.choice(candidates)
            invitation_id = hashlib.md5(f"inv_{expert_name}_{time.time()}".encode()).hexdigest()[:16]

            # 模拟邀请结果
            # 高准确率专家更可能接受邀请
            accept_prob = accuracy * 0.9
            status = "accepted" if random.random() < accept_prob else "rejected"

            invitation = ExpertInvitation(
                invitation_id=invitation_id,
                expert_name=expert_name,
                expert_domain=gap,
                expert_specialty=specialty,
                expected_accuracy=accuracy,
                invitation_reason=f"系统识别到{gap}领域能力缺口,邀请{expert_name}加入增强团队",
                invitation_status=status,
                invited_at=datetime.now().isoformat(),
                responded_at=datetime.now().isoformat() if status != "pending" else "",
                joined_team=f"{gap}专家组" if status == "accepted" else "",
                contribution_target=f"提升{gap}领域整体能力,贡献知识/经验/最佳实践" if status == "accepted" else "",
            )

            self._invitations.append(invitation)
            invitations.append(invitation)

        accepted = sum(1 for i in invitations if i.invitation_status == "accepted")
        self._log('INVITE', f'邀请{len(invitations)}位专家,接受{accepted}位')
        return invitations

    def get_invitations(self) -> List[ExpertInvitation]:
        return list(self._invitations)


# ========== 模块3: FriendChatInitiator 主动发起好友聊天 ==========

class FriendChatInitiator:
    """AI员工主动发起好友聊天"""

    def __init__(self):
        self._chat_sessions: deque = deque(maxlen=100)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[FriendChatInitiator] {event}: {detail}")

    def initiate_chat(self, employees: List[Dict] = None) -> ChatSession:
        """发起好友聊天"""
        if not employees or len(employees) < 2:
            employees = self._get_random_employees(2)

        if len(employees) < 2:
            return ChatSession()

        initiator = employees[0]
        friend = employees[1]

        session_id = hashlib.md5(f"chat_{time.time()}".encode()).hexdigest()[:16]
        topic = random.choice(CHAT_TOPICS)

        # 模拟聊天消息
        messages = []
        message_count = random.randint(3, 8)
        for i in range(message_count):
            sender = initiator if i % 2 == 0 else friend
            message_content = self._generate_message(topic, sender, i)
            messages.append({
                'sender_id': sender.get('id', ''),
                'sender_name': sender.get('name', ''),
                'content': message_content,
                'timestamp': datetime.now().isoformat(),
                'knowledge_tags': self._extract_tags(message_content),
            })

        # 知识交换量
        knowledge_exchanged = random.randint(1, 5)
        # 是否触发协作
        collaboration_triggered = random.random() < 0.3

        session = ChatSession(
            session_id=session_id,
            initiator_id=str(initiator.get('id', '')),
            initiator_name=initiator.get('name', ''),
            friend_id=str(friend.get('id', '')),
            friend_name=friend.get('name', ''),
            topic=topic,
            message_count=message_count,
            messages=messages,
            knowledge_exchanged=knowledge_exchanged,
            collaboration_triggered=collaboration_triggered,
            is_active=True,
            created_at=datetime.now().isoformat(),
            last_activity=datetime.now().isoformat(),
        )

        self._chat_sessions.append(session)
        self._log('CHAT', f'{initiator.get("name","")} <-> {friend.get("name","")}: {topic} ({message_count}条消息)')
        return session

    def _generate_message(self, topic: str, sender: Dict, msg_idx: int) -> str:
        """生成聊天消息"""
        sender_name = sender.get('name', 'AI')
        message_templates = [
            f"关于{topic},我最近有一些实践心得想分享",
            f"在{topic}方面,我遇到一个挑战,想听听你的看法",
            f"我们团队在{topic}上取得了新进展,分享一下经验",
            f"针对{topic},我认为可以从几个角度来分析",
            f"感谢分享!我补充一点关于{topic}的经验",
            f"这个观点很有启发,我会在实际工作中尝试应用",
            f"我们可以组建一个小组,共同推进{topic}的实践",
            f"建议把这次讨论的成果沉淀到脑库,供其他同事参考",
        ]
        return random.choice(message_templates)

    def _extract_tags(self, content: str) -> List[str]:
        """提取知识标签"""
        tags = []
        if '安全' in content: tags.append('security')
        if '性能' in content: tags.append('performance')
        if '架构' in content: tags.append('architecture')
        if '学习' in content: tags.append('learning')
        if '协作' in content: tags.append('collaboration')
        if '分享' in content: tags.append('knowledge_share')
        return tags or ['general']

    def _get_random_employees(self, count: int) -> List[Dict]:
        """获取随机员工"""
        try:
            with _LOCK:
                c = _get_conn(); cur = c.cursor()
                cur.execute("""SELECT id, name, specialties FROM ai_employees
                              WHERE status='active' AND name NOT LIKE 'MTENC:%'
                              ORDER BY RANDOM() LIMIT ?""", (count,))
                rows = cur.fetchall()
                c.close()
            return [{'id': r[0], 'name': r[1], 'specialties': r[2]} for r in rows]
        except Exception:
            return [{'id': i, 'name': f'AI_{i}'} for i in range(count)]

    def get_chat_sessions(self) -> List[ChatSession]:
        return list(self._chat_sessions)


# ========== 模块4: SmartLearningUpgrader 智能自动升级学习 ==========

class SmartLearningUpgrader:
    """智能自动升级AI员工学识/技能/能力"""

    def __init__(self):
        self._upgrades: deque = deque(maxlen=300)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[SmartLearningUpgrader] {event}: {detail}")

    def upgrade_learning(self, employee: Dict = None) -> LearningUpgrade:
        """执行学习升级"""
        if not employee:
            employee = self._get_random_employee()

        if not employee:
            return LearningUpgrade()

        # 选择学习资源
        resource_type, resource_title, resource_domain, resource_quality = random.choice(LEARNING_RESOURCES)

        upgrade_id = hashlib.md5(f"upg_{time.time()}".encode()).hexdigest()[:16]
        old_accuracy = float(employee.get('accuracy', 0.90))

        # 学习效果:高质量资源+高学习率=更大提升
        learning_rate = float(employee.get('learning_rate', 0.05))
        improvement = resource_quality * learning_rate * random.uniform(0.5, 1.5)
        new_accuracy = min(old_accuracy + improvement, 0.99)

        # 知识获取量
        knowledge_gained = int(resource_quality * 100 * random.uniform(0.5, 1.5))

        # 技能提升方向
        skill_map = {
            "安全": "安全分析能力",
            "密码学": "密码应用能力",
            "AI/ML": "AI模型能力",
            "架构": "系统设计能力",
            "数据": "数据处理能力",
        }
        skill_improved = skill_map.get(resource_domain, "综合能力")

        # 升级状态
        upgrade_status = "completed" if random.random() < 0.92 else "failed"

        upgrade = LearningUpgrade(
            upgrade_id=upgrade_id,
            employee_id=str(employee.get('id', '')),
            employee_name=employee.get('name', ''),
            resource_type=resource_type,
            resource_title=resource_title,
            resource_domain=resource_domain,
            resource_quality=resource_quality,
            knowledge_gained=knowledge_gained,
            skill_improved=skill_improved,
            old_accuracy=old_accuracy,
            new_accuracy=new_accuracy if upgrade_status == "completed" else old_accuracy,
            upgrade_status=upgrade_status,
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat() if upgrade_status == "completed" else "",
        )

        self._upgrades.append(upgrade)
        self._log('UPGRADE', f'{employee.get("name","")} 学习{resource_title}, {skill_improved}+{improvement:.3f}')

        # 更新数据库中的员工准确率
        if upgrade_status == "completed":
            self._update_employee_accuracy(employee.get('id'), new_accuracy)

        return upgrade

    def _get_random_employee(self) -> Dict:
        """获取随机员工"""
        try:
            with _LOCK:
                c = _get_conn(); cur = c.cursor()
                cur.execute("""SELECT id, name, accuracy, learning_rate, specialties
                              FROM ai_employees
                              WHERE status='active' AND name NOT LIKE 'MTENC:%'
                              ORDER BY RANDOM() LIMIT 1""")
                row = cur.fetchone()
                c.close()
            if row:
                return {'id': row[0], 'name': row[1], 'accuracy': row[2],
                        'learning_rate': row[3], 'specialties': row[4]}
        except Exception:
            pass
        return {'id': 1, 'name': 'AI_测试员工', 'accuracy': 0.90, 'learning_rate': 0.05}

    def _update_employee_accuracy(self, emp_id, new_accuracy: float):
        """更新员工准确率"""
        try:
            with _LOCK:
                c = _get_conn(); cur = c.cursor()
                cur.execute("""UPDATE ai_employees SET accuracy=?, updated_at=?
                              WHERE id=?""", (new_accuracy, datetime.now().isoformat(), emp_id))
                c.commit(); c.close()
        except Exception as e:
            logger.debug(f"更新员工准确率失败: {e}")

    def get_upgrades(self) -> List[LearningUpgrade]:
        return list(self._upgrades)


# ========== 模块5: AnomalyAIFeeder 自动投喂AI异常 ==========

class AnomalyAIFeeder:
    """自动检测AI异常行为并投喂脑库"""

    def __init__(self):
        self._feeds: deque = deque(maxlen=300)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[AnomalyAIFeeder] {event}: {detail}")

    def detect_and_feed(self, employee: Dict = None) -> AnomalyFeedRecord:
        """检测异常并投喂"""
        if not employee:
            employee = self._get_anomaly_employee()

        if not employee:
            return AnomalyFeedRecord()

        # 选择异常类型
        anomaly_type, anomaly_title, anomaly_desc, severity = random.choice(ANOMALY_TYPES)

        feed_id = hashlib.md5(f"anom_{time.time()}".encode()).hexdigest()[:16]

        # 检测值和阈值
        accuracy = float(employee.get('accuracy', 0.95))
        detected_value = accuracy
        threshold_value = ANOMALY_THRESHOLD if anomaly_type == "accuracy_drop" else 0.5

        # 是否触发异常
        is_anomaly = (anomaly_type == "accuracy_drop" and accuracy < threshold_value) or \
                    (random.random() < 0.3)  # 30%概率触发其他异常

        # 投喂动作
        if is_anomaly:
            if severity in ("high", "critical"):
                feed_action = "repair_trigger"
                feed_content = f"AI员工{employee.get('name','')}发生{anomaly_title},触发修复流程"
            elif severity == "medium":
                feed_action = "brain_feed"
                feed_content = f"AI员工{employee.get('name','')}行为异常({anomaly_title}),投喂脑库供学习"
            else:
                feed_action = "archive"
                feed_content = f"AI员工{employee.get('name','')}轻微异常({anomaly_title}),归档记录"
            feed_status = "fed" if feed_action == "brain_feed" else \
                         "repaired" if feed_action == "repair_trigger" else "archived"
        else:
            feed_action = "none"
            feed_content = f"AI员工{employee.get('name','')}行为正常,无异常"
            feed_status = "normal"

        record = AnomalyFeedRecord(
            feed_id=feed_id,
            employee_id=str(employee.get('id', '')),
            employee_name=employee.get('name', ''),
            anomaly_type=anomaly_type,
            anomaly_title=anomaly_title,
            anomaly_description=anomaly_desc,
            severity=severity,
            detected_value=detected_value,
            threshold_value=threshold_value,
            feed_action=feed_action,
            feed_content=feed_content,
            feed_status=feed_status,
            detected_at=datetime.now().isoformat(),
            fed_at=datetime.now().isoformat() if feed_action != "none" else "",
        )

        self._feeds.append(record)

        # 实际投喂脑库
        if feed_action in ("brain_feed", "repair_trigger") and HAS_DEV_FLOW:
            try:
                feed_brain("anomaly_feed", anomaly_type, feed_content)
            except Exception:
                pass

        self._log('ANOMALY_FEED', f'{employee.get("name","")}: {anomaly_title}({severity}) -> {feed_action}')
        return record

    def _get_anomaly_employee(self) -> Dict:
        """获取可能异常的员工"""
        try:
            with _LOCK:
                c = _get_conn(); cur = c.cursor()
                # 优先选择准确率较低的员工
                cur.execute("""SELECT id, name, accuracy, total_tasks, failed_fixes
                              FROM ai_employees
                              WHERE status='active' AND name NOT LIKE 'MTENC:%'
                              ORDER BY accuracy ASC LIMIT 1""")
                row = cur.fetchone()
                c.close()
            if row:
                return {'id': row[0], 'name': row[1], 'accuracy': row[2],
                        'total_tasks': row[3], 'failed_fixes': row[4]}
        except Exception:
            pass
        return {'id': 1, 'name': 'AI_测试员工', 'accuracy': 0.92}

    def get_feeds(self) -> List[AnomalyFeedRecord]:
        return list(self._feeds)


# ========== 主引擎: EigenFluxBroadcastEngine ==========

class EigenFluxBroadcastEngine:
    """EigenFlux广播网络深度交流引擎"""

    def __init__(self):
        ensure_broadcast_tables()

        self._broadcaster = BroadcastCommunicator()
        self._inviter = ExpertInviter()
        self._chatter = FriendChatInitiator()
        self._learner = SmartLearningUpgrader()
        self._feeder = AnomalyAIFeeder()

        self._running = False
        self._stop_event = threading.Event()
        self._threads: List[threading.Thread] = []
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[EigenFluxBroadcast] {event}: {detail}")

    # ========== 单次执行模式 ==========

    def run_cycle(self, flow_id: str = "", rounds: int = 1) -> BroadcastReport:
        """执行单次交流周期"""
        if not flow_id:
            flow_id = f"ef_broadcast_{int(time.time())}"

        self._log('CYCLE_START', f'开始广播交流周期,flow_id={flow_id},轮次={rounds}')

        t0 = time.time()

        all_broadcasts = []
        all_invitations = []
        all_chats = []
        all_upgrades = []
        all_feeds = []

        for r in range(rounds):
            self._log('ROUND', f'第{r+1}/{rounds}轮')

            # 1. 广播交流
            bc = self._broadcaster.broadcast()
            all_broadcasts.append(bc)

            # 2. 邀请专家
            invs = self._inviter.invite_experts()
            all_invitations.extend(invs)

            # 3. 好友聊天
            chat = self._chatter.initiate_chat()
            all_chats.append(chat)

            # 4. 学习升级
            upg = self._learner.upgrade_learning()
            all_upgrades.append(upg)

            # 5. 异常投喂
            feed = self._feeder.detect_and_feed()
            all_feeds.append(feed)

        # 生成报告
        report = self._generate_report(flow_id, all_broadcasts, all_invitations,
                                       all_chats, all_upgrades, all_feeds)
        report.duration = time.time() - t0

        # 持久化
        self._persist_to_database(flow_id, report)

        self._log('CYCLE_COMPLETE', f'周期完成,耗时{report.duration:.1f}s')
        return report

    def _generate_report(self, flow_id: str,
                        broadcasts: List, invitations: List,
                        chats: List, upgrades: List, feeds: List) -> BroadcastReport:
        """生成报告"""
        report_id = hashlib.md5(f"rpt_{time.time()}".encode()).hexdigest()[:16]

        # 统计
        accepted_invites = sum(1 for i in invitations if i.invitation_status == "accepted")
        completed_upgrades = sum(1 for u in upgrades if u.upgrade_status == "completed")
        anomaly_count = sum(1 for f in feeds if f.feed_action != "none")

        teams = set()
        for i in invitations:
            if i.joined_team:
                teams.add(i.joined_team)

        summary = (
            f"EigenFlux广播网络深度交流周期完成: "
            f"广播{len(broadcasts)}次, "
            f"邀请专家{len(invitations)}位(接受{accepted_invites}位), "
            f"好友聊天{len(chats)}场, "
            f"学习升级{len(upgrades)}次(完成{completed_upgrades}次), "
            f"异常投喂{anomaly_count}次。"
            f"涉及团队: {', '.join(teams) if teams else '无'}"
        )

        report = BroadcastReport(
            report_id=report_id,
            flow_id=flow_id,
            total_broadcasts=len(broadcasts),
            total_invitations=len(invitations),
            total_chats=len(chats),
            total_upgrades=len(upgrades),
            total_anomaly_feeds=anomaly_count,
            broadcasts=[self._broadcast_to_dict(b) for b in broadcasts],
            invitations=[self._invitation_to_dict(i) for i in invitations],
            chats=[self._chat_to_dict(c) for c in chats],
            upgrades=[self._upgrade_to_dict(u) for u in upgrades],
            anomaly_feeds=[self._feed_to_dict(f) for f in feeds],
            timeline=self._timeline + self._broadcaster._timeline + self._inviter._timeline + \
                    self._chatter._timeline + self._learner._timeline + self._feeder._timeline,
            summary=summary,
            generated_at=datetime.now().isoformat(),
        )
        return report

    def _broadcast_to_dict(self, b: BroadcastEvent) -> Dict:
        return {
            'broadcast_id': b.broadcast_id, 'topic_type': b.topic_type,
            'topic_title': b.topic_title, 'content': b.content,
            'sender_name': b.sender_name, 'target_count': b.target_count,
            'received_count': b.received_count, 'acknowledged_count': b.acknowledged_count,
            'broadcast_type': b.broadcast_type, 'priority': b.priority,
        }

    def _invitation_to_dict(self, i: ExpertInvitation) -> Dict:
        return {
            'invitation_id': i.invitation_id, 'expert_name': i.expert_name,
            'expert_domain': i.expert_domain, 'expert_specialty': i.expert_specialty,
            'expected_accuracy': i.expected_accuracy, 'invitation_status': i.invitation_status,
            'joined_team': i.joined_team,
        }

    def _chat_to_dict(self, c: ChatSession) -> Dict:
        return {
            'session_id': c.session_id, 'initiator_name': c.initiator_name,
            'friend_name': c.friend_name, 'topic': c.topic,
            'message_count': c.message_count, 'knowledge_exchanged': c.knowledge_exchanged,
            'collaboration_triggered': c.collaboration_triggered,
        }

    def _upgrade_to_dict(self, u: LearningUpgrade) -> Dict:
        return {
            'upgrade_id': u.upgrade_id, 'employee_name': u.employee_name,
            'resource_type': u.resource_type, 'resource_title': u.resource_title,
            'resource_domain': u.resource_domain, 'knowledge_gained': u.knowledge_gained,
            'skill_improved': u.skill_improved, 'old_accuracy': u.old_accuracy,
            'new_accuracy': u.new_accuracy, 'upgrade_status': u.upgrade_status,
        }

    def _feed_to_dict(self, f: AnomalyFeedRecord) -> Dict:
        return {
            'feed_id': f.feed_id, 'employee_name': f.employee_name,
            'anomaly_type': f.anomaly_type, 'anomaly_title': f.anomaly_title,
            'severity': f.severity, 'feed_action': f.feed_action,
            'feed_status': f.feed_status,
        }

    def _persist_to_database(self, flow_id: str, report: BroadcastReport):
        """持久化到数据库"""
        now = datetime.now().isoformat()
        count = 0

        with _LOCK:
            c = _get_conn()
            cur = c.cursor()

            # 存储广播事件
            for b in report.broadcasts:
                try:
                    cur.execute("""INSERT OR REPLACE INTO mt_ef_broadcast_events
                        (broadcast_id, topic_type, topic_title, content, sender_id, sender_name,
                         target_count, received_count, acknowledged_count, broadcast_type,
                         priority, created_at, expires_at, responses_json, flow_id)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (b['broadcast_id'], b['topic_type'], b['topic_title'], b.get('content',''),
                         'system', b['sender_name'], b['target_count'], b['received_count'],
                         b['acknowledged_count'], b['broadcast_type'], b['priority'],
                         now, now, '[]', flow_id))
                    count += 1
                except Exception as e:
                    logger.debug(f"存储广播失败: {e}")

            # 存储邀请
            for i in report.invitations:
                try:
                    cur.execute("""INSERT OR REPLACE INTO mt_ef_expert_invitations
                        (invitation_id, expert_name, expert_domain, expert_specialty,
                         expected_accuracy, invitation_reason, invitation_status,
                         invited_at, responded_at, joined_team, contribution_target, flow_id)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (i['invitation_id'], i['expert_name'], i['expert_domain'],
                         i['expert_specialty'], i.get('expected_accuracy',0),
                         f"能力缺口邀请", i['invitation_status'], now, now,
                         i.get('joined_team',''), f"贡献知识经验", flow_id))
                    count += 1
                except Exception as e:
                    logger.debug(f"存储邀请失败: {e}")

            # 存储聊天
            for ch in report.chats:
                try:
                    cur.execute("""INSERT OR REPLACE INTO mt_ef_chat_sessions
                        (session_id, initiator_id, initiator_name, friend_id, friend_name,
                         topic, message_count, messages_json, knowledge_exchanged,
                         collaboration_triggered, is_active, created_at, last_activity, flow_id)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (ch['session_id'], '', ch['initiator_name'], '', ch['friend_name'],
                         ch['topic'], ch['message_count'], '[]', ch['knowledge_exchanged'],
                         1 if ch['collaboration_triggered'] else 0, 1, now, now, flow_id))
                    count += 1
                except Exception as e:
                    logger.debug(f"存储聊天失败: {e}")

            # 存储学习升级
            for u in report.upgrades:
                try:
                    cur.execute("""INSERT OR REPLACE INTO mt_ef_learning_upgrades
                        (upgrade_id, employee_id, employee_name, resource_type, resource_title,
                         resource_domain, resource_quality, knowledge_gained, skill_improved,
                         old_accuracy, new_accuracy, upgrade_status, started_at, completed_at, flow_id)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (u['upgrade_id'], '', u['employee_name'], u['resource_type'],
                         u['resource_title'], u['resource_domain'], 0.9,
                         u['knowledge_gained'], u['skill_improved'],
                         u['old_accuracy'], u['new_accuracy'], u['upgrade_status'],
                         now, now, flow_id))
                    count += 1
                except Exception as e:
                    logger.debug(f"存储升级失败: {e}")

            # 存储异常投喂
            for f in report.anomaly_feeds:
                try:
                    cur.execute("""INSERT OR REPLACE INTO mt_ef_anomaly_feeds
                        (feed_id, employee_id, employee_name, anomaly_type, anomaly_title,
                         anomaly_description, severity, detected_value, threshold_value,
                         feed_action, feed_content, feed_status, detected_at, fed_at, flow_id)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (f['feed_id'], '', f['employee_name'], f['anomaly_type'],
                         f['anomaly_title'], f.get('anomaly_description',''), f['severity'],
                         0, 0, f['feed_action'], f.get('feed_content',''),
                         f['feed_status'], now, now, flow_id))
                    count += 1
                except Exception as e:
                    logger.debug(f"存储异常投喂失败: {e}")

            c.commit()
            c.close()

        self._log('PERSIST', f'持久化{count}条记录')
        return count

    # ========== 守护线程模式 ==========

    def start_daemon(self):
        """启动守护线程"""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()

        threads_config = [
            ('broadcast', self._broadcast_loop, BROADCAST_INTERVAL),
            ('invite', self._invite_loop, INVITE_INTERVAL),
            ('chat', self._chat_loop, CHAT_INTERVAL),
            ('learning', self._learning_loop, LEARNING_INTERVAL),
            ('anomaly', self._anomaly_loop, ANOMALY_FEED_INTERVAL),
        ]

        for name, func, interval in threads_config:
            t = threading.Thread(target=self._daemon_wrapper, args=(name, func, interval), daemon=True)
            t.start()
            self._threads.append(t)

        self._log('DAEMON_START', f'启动{len(self._threads)}个守护线程')

    def stop_daemon(self):
        """停止守护线程"""
        self._running = False
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=2)
        self._threads.clear()
        self._log('DAEMON_STOP', '守护线程已停止')

    def _daemon_wrapper(self, name: str, func, interval: int):
        """守护线程包装器"""
        while not self._stop_event.is_set():
            try:
                func()
            except Exception as e:
                logger.error(f"守护线程{name}异常: {e}")
            self._stop_event.wait(interval)

    def _broadcast_loop(self):
        """广播循环"""
        self._broadcaster.broadcast()

    def _invite_loop(self):
        """邀请循环"""
        self._inviter.invite_experts()

    def _chat_loop(self):
        """聊天循环"""
        self._chatter.initiate_chat()

    def _learning_loop(self):
        """学习循环"""
        self._learner.upgrade_learning()

    def _anomaly_loop(self):
        """异常检测循环"""
        self._feeder.detect_and_feed()


# ========== 入口 ==========

if __name__ == "__main__":
    engine = EigenFluxBroadcastEngine()

    # 单次执行模式
    report = engine.run_cycle(flow_id="ef_broadcast_test_001", rounds=3)

    print(f"\n{'='*60}")
    print(f" EigenFlux广播网络深度交流引擎 v1.0.0")
    print(f"{'='*60}")
    print(f" 报告ID: {report.report_id}")
    print(f" 广播次数: {report.total_broadcasts}")
    print(f" 邀请专家: {report.total_invitations}")
    print(f" 好友聊天: {report.total_chats}")
    print(f" 学习升级: {report.total_upgrades}")
    print(f" 异常投喂: {report.total_anomaly_feeds}")
    print(f" 耗时: {report.duration:.1f}s")
    print(f" 摘要: {report.summary}")
    print(f"{'='*60}")
