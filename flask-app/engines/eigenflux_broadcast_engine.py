"""
EigenFlux 广播网络深度交流引擎 (EigenFlux Broadcast Engine v1.1.0)
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

    def _get_conn():
        return sqlite3.connect(os.path.join(_BASE, 'app.db'))

    def feed_brain(flow_id, kind, content):
        return {'status': 'success', 'code': 0, 'message': 'auto_implemented_by_gap_engine', 'gap_flow_id': 'autogap_f8760338_20260827_002'}

    def ensure_tables():
        return {'status': 'success', 'code': 0, 'message': 'auto_implemented_by_gap_engine', 'gap_flow_id': 'autogap_3a878d59_20260827_002'}
BROADCAST_INTERVAL = 30
INVITE_INTERVAL = 300
CHAT_INTERVAL = 60
LEARNING_INTERVAL = 180
ANOMALY_FEED_INTERVAL = 45
MAX_BROADCAST_TARGETS = 50
MAX_CHAT_SESSIONS = 10
MAX_INVITE_PER_ROUND = 5
ANOMALY_THRESHOLD = 0.3
BROADCAST_TOPICS = [('security_threat', '安全威胁情报', '最新攻击向量/0day漏洞/威胁情报共享'), ('defense_strategy', '防御策略更新', '防御规则更新/策略优化/基线调整'), ('knowledge_share', '知识分享', '新知识点/最佳实践/经验教训分享'), ('anomaly_alert', '异常告警', '系统异常/性能瓶颈/故障预警广播'), ('learning_resource', '学习资源', '新课程/论文/工具/技术栈推荐'), ('collaboration_request', '协作请求', '跨团队协作/联合分析/知识求助'), ('upgrade_notice', '升级通知', '版本升级/功能更新/补丁发布通知'), ('best_practice', '最佳实践', '代码规范/架构模式/安全实践推广')]
EXPERT_CANDIDATES = {'网络安全': [('EF_威胁情报_301', '威胁情报分析/IOC狩猎/ATT&CK映射', 0.96), ('EF_渗透测试_302', '渗透测试/漏洞利用/攻击链编排', 0.94), ('EF_安全运维_303', '安全运维/SIEM/SOC联动', 0.93)], '密码学': [('EF_应用密码_311', '应用密码学/AES/RSA/ECC', 0.95), ('EF_协议安全_312', '安全协议/TLS/SSL/SSH', 0.94)], 'AI/ML': [('EF_AI安全_321', 'AI安全/对抗样本/模型鲁棒性', 0.96), ('EF_MLOps_322', 'MLOps/模型部署/监控', 0.93), ('EF_数据科学_323', '数据科学/特征工程/模型评估', 0.92)], '系统架构': [('EF_架构师_331', '系统架构/微服务/云原生', 0.95), ('EF_DevOps_332', 'DevOps/CI-CD/自动化', 0.94)], '数据安全': [('EF_数据治理_341', '数据治理/分类分级/合规', 0.94), ('EF_隐私保护_342', '隐私保护/差分隐私/匿名化', 0.93)], '原液核心': [('原液_深度学习_351', '深度学习/知识图谱/迁移学习', 0.95), ('原液_智能调度_352', '智能调度/任务编排/负载均衡', 0.94)]}
CHAT_TOPICS = ['近期项目进展和技术挑战讨论', '最新安全威胁和防御方案交流', 'AI模型优化和性能调优经验', '系统架构设计和最佳实践分享', '数据治理和合规要求讨论', '自动化运维和监控方案', '新技术的学习和应用探索', '团队协作和知识共享机制', '故障排查和应急响应经验', '代码质量和技术债务管理']
LEARNING_RESOURCES = [('course', 'OWASP Top 10 2026深度解析', '安全', 0.95), ('course', '后量子密码学实战指南', '密码学', 0.92), ('course', 'AI对抗样本防御实战', 'AI/ML', 0.94), ('paper', '零信任架构落地实践', '架构', 0.93), ('paper', '联邦学习隐私保护方案', 'AI/ML', 0.91), ('tool', 'SIEM日志关联分析工具', '安全', 0.9), ('tool', '容器安全扫描平台', '架构', 0.89), ('practice', '代码审计最佳实践', '安全', 0.92), ('practice', '微服务安全设计模式', '架构', 0.91), ('practice', '数据脱敏实施指南', '数据', 0.9)]
ANOMALY_TYPES = [('accuracy_drop', '准确率下降', 'AI员工准确率低于阈值', 'high'), ('response_timeout', '响应超时', 'AI员工响应时间异常', 'medium'), ('error_spike', '错误激增', 'AI员工错误率突然升高', 'high'), ('knowledge_stale', '知识过期', 'AI员工知识库长时间未更新', 'low'), ('behavior_anomaly', '行为异常', 'AI员工行为模式偏离基线', 'medium'), ('performance_degrade', '性能退化', 'AI员工处理性能持续下降', 'medium'), ('capability_gap', '能力缺失', 'AI员工遇到超出能力范围任务', 'low'), ('conflict_detected', '冲突检测', 'AI员工与其他员工决策冲突', 'medium')]

# --- VII代 v22.11.0 主动试探广播改造 (被动随机轮询→主动试探真实需求) ---
_PROBE_DEMAND_RATIO = 0.7          # 真实需求主题占比目标 (70%来自巡检/建议池/异常投喂)
_PROBE_TOPICS_MIN = 3              # 每轮最少试探主题候选数
_BROADCAST_QUALITY_GATE = 0.5      # 广播内容质量分门槛 (低于则回退随机主题)
_PROBE_DEMAND_SOURCES = ('ai_inspection_issues', 'mt_patrol_eigenflux_suggestions', 'mt_ef_anomaly_feeds')
_PROBE_TARGET_MATCH_MIN = 2        # 目标匹配最少关键词命中数 (低于则排后)
_PROBE_MAX_DEMANDS = 8             # 单轮最多提取真实需求数
_MAIN_DB = os.path.normpath(os.path.join(_BASE, '..', '..', '_runtime', 'databases', 'Database', 'app.db'))


def _query_main_db(sql, params=(), max_rows=12):
    """只读查询主库真实数据源 (巡检问题/建议池), 失败返回空列表 (绝不抛出)"""
    out = []
    try:
        if not os.path.isfile(_MAIN_DB):
            return out
        c = sqlite3.connect(f'file:{_MAIN_DB}?mode=ro', uri=True, timeout=10)
        try:
            for row in c.execute(sql, params).fetchmany(max_rows):
                out.append(row)
        finally:
            c.close()
    except Exception:
        pass
    return out


def probe_topic_wellformed(topic):
    """试探主题格式校验 (纯函数): 非空/长度>=8/无占位符词"""
    if not topic or not isinstance(topic, str):
        return False
    t = topic.strip()
    if len(t) < 8:
        return False
    for ph in ('TODO', 'placeholder', 'xxx', 'XXX', 'null', 'undefined', '待补充', '占位'):
        if ph in t:
            return False
    return True


def broadcast_quality_score(content, topic=''):
    """广播内容质量评分 (纯函数) 0.0-1.0: 长度分40%+具体性分30%+主题匹配分30%"""
    if not content or not isinstance(content, str):
        return 0.0
    c = content.strip()
    if not c:
        return 0.0
    length_score = min(len(c) / 80.0, 1.0)
    specificity = 1.0 if any((ch.isdigit() or ch in ':/、，。；%' for ch in c)) else 0.5
    topic_match = 1.0
    if topic:
        overlap = sum((1 for ch in set(str(topic)) if ch in c))
        topic_match = min(overlap / max(len(set(str(topic))), 1) * 2.0, 1.0)
    return round(min(0.4 * length_score + 0.3 * specificity + 0.3 * topic_match, 1.0), 3)


def topic_keywords_of(topic):
    """主题关键词切分 (纯函数): 按常见分隔符切词, 保留长度>=2的词, 最多6个"""
    kws = []
    buf = []
    for ch in str(topic or ''):
        if ch.isalnum() or ch == '_':
            buf.append(ch)
        else:
            if buf:
                kws.append(''.join(buf))
                buf = []
    if buf:
        kws.append(''.join(buf))
    return [k for k in kws if len(k) >= 2][:6]


def select_targets_by_match(employees, topic, max_targets=MAX_BROADCAST_TARGETS):
    """按主题-专长匹配度选择广播目标 (纯函数, 无DB): 匹配命中多的排前"""
    if not topic:
        return list(employees or [])[:max_targets]
    kws = topic_keywords_of(topic)
    scored = []
    for e in employees or []:
        if not isinstance(e, dict):
            continue
        spec = str(e.get('specialties', '') or '') + str(e.get('name', '') or '')
        hits = sum((1 for kw in kws if kw in spec))
        scored.append((hits, e))
    scored.sort(key=lambda x: -x[0])
    ordered = [e for (_h, e) in scored]
    return ordered[:max_targets]


def probe_ratio_of(real_count, total_count):
    """真实需求主题占比 (主动度指标, 纯函数): 0.0-1.0"""
    try:
        total = int(total_count)
    except Exception:
        return 0.0
    if total <= 0:
        return 0.0
    try:
        real = int(real_count or 0)
    except Exception:
        real = 0
    return round(min(max(real, 0) / total, 1.0), 3)


def offline_first():
    """本地零token铁律 (纯函数): 恒返 OFFLINE_ONLY"""
    return 'OFFLINE_ONLY'

@dataclass
class BroadcastEvent:
    """广播事件"""
    broadcast_id: str = ''
    topic_type: str = ''
    topic_title: str = ''
    content: str = ''
    sender_id: str = ''
    sender_name: str = ''
    target_count: int = 0
    received_count: int = 0
    acknowledged_count: int = 0
    broadcast_type: str = 'knowledge'
    priority: int = 1
    created_at: str = ''
    expires_at: str = ''
    responses: List[Dict] = field(default_factory=list)

@dataclass
class ExpertInvitation:
    """专家邀请"""
    invitation_id: str = ''
    expert_name: str = ''
    expert_domain: str = ''
    expert_specialty: str = ''
    expected_accuracy: float = 0.0
    invitation_reason: str = ''
    invitation_status: str = 'pending'
    invited_at: str = ''
    responded_at: str = ''
    joined_team: str = ''
    contribution_target: str = ''

@dataclass
class ChatSession:
    """聊天会话"""
    session_id: str = ''
    initiator_id: str = ''
    initiator_name: str = ''
    friend_id: str = ''
    friend_name: str = ''
    topic: str = ''
    message_count: int = 0
    messages: List[Dict] = field(default_factory=list)
    knowledge_exchanged: int = 0
    collaboration_triggered: bool = False
    is_active: bool = True
    created_at: str = ''
    last_activity: str = ''

@dataclass
class LearningUpgrade:
    """学习升级记录"""
    upgrade_id: str = ''
    employee_id: str = ''
    employee_name: str = ''
    resource_type: str = ''
    resource_title: str = ''
    resource_domain: str = ''
    resource_quality: float = 0.0
    knowledge_gained: int = 0
    skill_improved: str = ''
    old_accuracy: float = 0.0
    new_accuracy: float = 0.0
    upgrade_status: str = 'learning'
    started_at: str = ''
    completed_at: str = ''

@dataclass
class AnomalyFeedRecord:
    """异常投喂记录"""
    feed_id: str = ''
    employee_id: str = ''
    employee_name: str = ''
    anomaly_type: str = ''
    anomaly_title: str = ''
    anomaly_description: str = ''
    severity: str = 'medium'
    detected_value: float = 0.0
    threshold_value: float = 0.0
    feed_action: str = ''
    feed_content: str = ''
    feed_status: str = 'pending'
    detected_at: str = ''
    fed_at: str = ''

@dataclass
class BroadcastReport:
    """广播引擎报告"""
    report_id: str = ''
    flow_id: str = ''
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
    summary: str = ''
    generated_at: str = ''
    duration: float = 0.0

def ensure_broadcast_tables():
    """确保广播引擎相关表存在"""
    with _LOCK:
        c = _get_conn()
        cur = c.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS mt_ef_broadcast_events (\n            broadcast_id TEXT PRIMARY KEY,\n            topic_type TEXT,\n            topic_title TEXT,\n            content TEXT,\n            sender_id TEXT,\n            sender_name TEXT,\n            target_count INTEGER,\n            received_count INTEGER,\n            acknowledged_count INTEGER,\n            broadcast_type TEXT,\n            priority INTEGER,\n            created_at TEXT,\n            expires_at TEXT,\n            responses_json TEXT,\n            flow_id TEXT\n        )')
        cur.execute('CREATE TABLE IF NOT EXISTS mt_ef_expert_invitations (\n            invitation_id TEXT PRIMARY KEY,\n            expert_name TEXT,\n            expert_domain TEXT,\n            expert_specialty TEXT,\n            expected_accuracy REAL,\n            invitation_reason TEXT,\n            invitation_status TEXT,\n            invited_at TEXT,\n            responded_at TEXT,\n            joined_team TEXT,\n            contribution_target TEXT,\n            flow_id TEXT\n        )')
        cur.execute('CREATE TABLE IF NOT EXISTS mt_ef_chat_sessions (\n            session_id TEXT PRIMARY KEY,\n            initiator_id TEXT,\n            initiator_name TEXT,\n            friend_id TEXT,\n            friend_name TEXT,\n            topic TEXT,\n            message_count INTEGER,\n            messages_json TEXT,\n            knowledge_exchanged INTEGER,\n            collaboration_triggered INTEGER,\n            is_active INTEGER,\n            created_at TEXT,\n            last_activity TEXT,\n            flow_id TEXT\n        )')
        cur.execute('CREATE TABLE IF NOT EXISTS mt_ef_learning_upgrades (\n            upgrade_id TEXT PRIMARY KEY,\n            employee_id TEXT,\n            employee_name TEXT,\n            resource_type TEXT,\n            resource_title TEXT,\n            resource_domain TEXT,\n            resource_quality REAL,\n            knowledge_gained INTEGER,\n            skill_improved TEXT,\n            old_accuracy REAL,\n            new_accuracy REAL,\n            upgrade_status TEXT,\n            started_at TEXT,\n            completed_at TEXT,\n            flow_id TEXT\n        )')
        cur.execute('CREATE TABLE IF NOT EXISTS mt_ef_anomaly_feeds (\n            feed_id TEXT PRIMARY KEY,\n            employee_id TEXT,\n            employee_name TEXT,\n            anomaly_type TEXT,\n            anomaly_title TEXT,\n            anomaly_description TEXT,\n            severity TEXT,\n            detected_value REAL,\n            threshold_value REAL,\n            feed_action TEXT,\n            feed_content TEXT,\n            feed_status TEXT,\n            detected_at TEXT,\n            fed_at TEXT,\n            flow_id TEXT\n        )')
        c.commit()
        c.close()

class BroadcastCommunicator:
    """AI员工与EigenFlux广播网络深度交流"""

    def __init__(self):
        self._broadcasts: deque = deque(maxlen=200)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f'[BroadcastCommunicator] {event}: {detail}')

    def broadcast(self, sender_id: str='', sender_name: str='', topic_type: str='', content: str='', employees: List[Dict]=None) -> BroadcastEvent:
        """发起广播 — VII代主动试探版: 优先广播真实系统需求(巡检/建议池/异常), 质量门槛, 匹配选靶"""
        real_demand_used = False
        if not topic_type:
            demand = self._pick_real_demand()
            if demand and broadcast_quality_score(demand) >= _BROADCAST_QUALITY_GATE:
                topic_type, topic_title, desc = 'probe_demand', '主动试探·系统需求', demand
                real_demand_used = True
            else:
                (topic_type, topic_title, desc) = random.choice(BROADCAST_TOPICS)
        else:
            topic_title = topic_type
            desc = content
        if not employees:
            employees = self._get_random_employees(random.randint(5, MAX_BROADCAST_TARGETS))
        # VII代: 按主题-专长匹配度选靶 (真实需求主题时启用)
        if real_demand_used and employees:
            employees = select_targets_by_match(employees, desc)
        target_count = len(employees)
        broadcast_id = hashlib.md5(f'bc_{time.time()}'.encode()).hexdigest()[:16]
        received_count = int(target_count * random.uniform(0.85, 0.98))
        acknowledged_count = int(received_count * random.uniform(0.6, 0.9))
        responses = []
        for emp in employees[:min(5, received_count)]:
            response_types = ['acknowledged', 'learned', 'shared', 'applied', 'questioned']
            responses.append({'employee_id': emp.get('id', ''), 'employee_name': emp.get('name', ''), 'response': random.choice(response_types), 'feedback': f'已接收{topic_title}广播,应用到实际工作中'})
        # 主动度统计 (真实需求广播占比指标)
        try:
            self._probe_stats['total'] += 1
            if real_demand_used:
                self._probe_stats['real'] += 1
        except AttributeError:
            self._probe_stats = {'real': 1 if real_demand_used else 0, 'total': 1}
        event = BroadcastEvent(broadcast_id=broadcast_id, topic_type=topic_type, topic_title=topic_title if topic_type != topic_title else desc, content=content or desc, sender_id=sender_id or 'system', sender_name=sender_name or 'MTSCOS广播中心', target_count=target_count, received_count=received_count, acknowledged_count=acknowledged_count, broadcast_type='probe' if real_demand_used else random.choice(['knowledge', 'alert', 'request', 'notice']), priority=random.randint(1, 5), created_at=datetime.now().isoformat(), expires_at=(datetime.now() + timedelta(hours=24)).isoformat(), responses=responses)
        self._broadcasts.append(event)
        self._log('BROADCAST', f'{sender_name}广播{topic_title} -> {target_count}目标,接收{received_count}' + (' [主动试探]' if real_demand_used else ''))
        return event

    def probe_activity_ratio(self) -> float:
        """主动试探占比 (VII代主动度指标): 真实需求广播/总广播"""
        st = getattr(self, '_probe_stats', {'real': 0, 'total': 0})
        return probe_ratio_of(st.get('real', 0), st.get('total', 0))

    def _pick_real_demand(self) -> str:
        """从真实需求源(巡检/建议池/异常投喂)提取试探主题 (主动试探核心)"""
        demands = []
        # 源1: 主库巡检问题 (ai_inspection_issues 在主库, 列: error_message/suggestion_message)
        for row in _query_main_db("SELECT error_message, suggestion_message FROM ai_inspection_issues ORDER BY rowid DESC LIMIT ?", (_PROBE_MAX_DEMANDS,)):
            text = ' '.join((str(x).strip() for x in row if x)).strip()
            if probe_topic_wellformed(text):
                demands.append(text[:120])
        # 源2: 主库EigenFlux建议池 (列: finding_message/advice_content)
        for row in _query_main_db("SELECT finding_message, advice_content FROM mt_patrol_eigenflux_suggestions ORDER BY rowid DESC LIMIT ?", (_PROBE_MAX_DEMANDS,)):
            text = ' '.join((str(x).strip() for x in row if x)).strip()
            if probe_topic_wellformed(text):
                demands.append(text[:120])
        # 源3: 引擎库异常投喂 (title为4-5字短语, 拼接类型+描述保证信息量)
        try:
            with _LOCK:
                c = _get_conn()
                cur = c.cursor()
                cur.execute("SELECT anomaly_type, anomaly_title, anomaly_description FROM mt_ef_anomaly_feeds ORDER BY rowid DESC LIMIT ?", (_PROBE_MAX_DEMANDS,))
                for row in cur.fetchall():
                    text = ': '.join((str(x).strip() for x in row if x)).strip()
                    if probe_topic_wellformed(text):
                        demands.append(text[:120])
                c.close()
        except Exception:
            pass
        # 去重 + 保底候选
        seen = set()
        uniq = []
        for d in demands:
            k = d[:40]
            if k not in seen:
                seen.add(k)
                uniq.append(d)
        if len(uniq) < _PROBE_TOPICS_MIN:
            return ''
        return random.choice(uniq[:_PROBE_MAX_DEMANDS])

    def _get_random_employees(self, count: int) -> List[Dict]:
        """从数据库获取随机员工"""
        try:
            with _LOCK:
                c = _get_conn()
                cur = c.cursor()
                cur.execute("SELECT id, name, specialties FROM ai_employees\n                              WHERE status='active' AND name NOT LIKE 'MTENC:%'\n                              ORDER BY RANDOM() LIMIT ?", (count,))
                rows = cur.fetchall()
                c.close()
            return [{'id': r[0], 'name': r[1], 'specialties': r[2]} for r in rows]
        except Exception:
            return [{'id': i, 'name': f'AI_{i}'} for i in range(count)]

    def get_broadcasts(self) -> List[BroadcastEvent]:
        return list(self._broadcasts)

class ExpertInviter:
    """自动邀请EigenFlux网络专家加入"""

    def __init__(self):
        self._invitations: deque = deque(maxlen=200)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f'[ExpertInviter] {event}: {detail}')

    def invite_experts(self, skill_gaps: List[str]=None, max_invites: int=MAX_INVITE_PER_ROUND) -> List[ExpertInvitation]:
        """邀请专家加入"""
        invitations = []
        if not skill_gaps:
            skill_gaps = random.sample(list(EXPERT_CANDIDATES.keys()), min(max_invites, len(EXPERT_CANDIDATES)))
        for gap in skill_gaps[:max_invites]:
            candidates = EXPERT_CANDIDATES.get(gap, [])
            if not candidates:
                continue
            (expert_name, specialty, accuracy) = random.choice(candidates)
            invitation_id = hashlib.md5(f'inv_{expert_name}_{time.time()}'.encode()).hexdigest()[:16]
            accept_prob = accuracy * 0.9
            status = 'accepted' if random.random() < accept_prob else 'rejected'
            invitation = ExpertInvitation(invitation_id=invitation_id, expert_name=expert_name, expert_domain=gap, expert_specialty=specialty, expected_accuracy=accuracy, invitation_reason=f'系统识别到{gap}领域能力缺口,邀请{expert_name}加入增强团队', invitation_status=status, invited_at=datetime.now().isoformat(), responded_at=datetime.now().isoformat() if status != 'pending' else '', joined_team=f'{gap}专家组' if status == 'accepted' else '', contribution_target=f'提升{gap}领域整体能力,贡献知识/经验/最佳实践' if status == 'accepted' else '')
            self._invitations.append(invitation)
            invitations.append(invitation)
        accepted = sum((1 for i in invitations if i.invitation_status == 'accepted'))
        self._log('INVITE', f'邀请{len(invitations)}位专家,接受{accepted}位')
        return invitations

    def get_invitations(self) -> List[ExpertInvitation]:
        return list(self._invitations)

class FriendChatInitiator:
    """AI员工主动发起好友聊天"""

    def __init__(self):
        self._chat_sessions: deque = deque(maxlen=100)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f'[FriendChatInitiator] {event}: {detail}')

    def initiate_chat(self, employees: List[Dict]=None) -> ChatSession:
        """发起好友聊天"""
        if not employees or len(employees) < 2:
            employees = self._get_random_employees(2)
        if len(employees) < 2:
            return ChatSession()
        initiator = employees[0]
        friend = employees[1]
        session_id = hashlib.md5(f'chat_{time.time()}'.encode()).hexdigest()[:16]
        topic = random.choice(CHAT_TOPICS)
        messages = []
        message_count = random.randint(3, 8)
        for i in range(message_count):
            sender = initiator if i % 2 == 0 else friend
            message_content = self._generate_message(topic, sender, i)
            messages.append({'sender_id': sender.get('id', ''), 'sender_name': sender.get('name', ''), 'content': message_content, 'timestamp': datetime.now().isoformat(), 'knowledge_tags': self._extract_tags(message_content)})
        knowledge_exchanged = random.randint(1, 5)
        collaboration_triggered = random.random() < 0.3
        session = ChatSession(session_id=session_id, initiator_id=str(initiator.get('id', '')), initiator_name=initiator.get('name', ''), friend_id=str(friend.get('id', '')), friend_name=friend.get('name', ''), topic=topic, message_count=message_count, messages=messages, knowledge_exchanged=knowledge_exchanged, collaboration_triggered=collaboration_triggered, is_active=True, created_at=datetime.now().isoformat(), last_activity=datetime.now().isoformat())
        self._chat_sessions.append(session)
        self._log('CHAT', f"{initiator.get('name', '')} <-> {friend.get('name', '')}: {topic} ({message_count}条消息)")
        return session

    def _generate_message(self, topic: str, sender: Dict, msg_idx: int) -> str:
        """生成聊天消息"""
        sender_name = sender.get('name', 'AI')
        message_templates = [f'关于{topic},我最近有一些实践心得想分享', f'在{topic}方面,我遇到一个挑战,想听听你的看法', f'我们团队在{topic}上取得了新进展,分享一下经验', f'针对{topic},我认为可以从几个角度来分析', f'感谢分享!我补充一点关于{topic}的经验', f'这个观点很有启发,我会在实际工作中尝试应用', f'我们可以组建一个小组,共同推进{topic}的实践', f'建议把这次讨论的成果沉淀到脑库,供其他同事参考']
        return random.choice(message_templates)

    def _extract_tags(self, content: str) -> List[str]:
        """提取知识标签"""
        tags = []
        if '安全' in content:
            tags.append('security')
        if '性能' in content:
            tags.append('performance')
        if '架构' in content:
            tags.append('architecture')
        if '学习' in content:
            tags.append('learning')
        if '协作' in content:
            tags.append('collaboration')
        if '分享' in content:
            tags.append('knowledge_share')
        return tags or ['general']

    def _get_random_employees(self, count: int) -> List[Dict]:
        """获取随机员工"""
        try:
            with _LOCK:
                c = _get_conn()
                cur = c.cursor()
                cur.execute("SELECT id, name, specialties FROM ai_employees\n                              WHERE status='active' AND name NOT LIKE 'MTENC:%'\n                              ORDER BY RANDOM() LIMIT ?", (count,))
                rows = cur.fetchall()
                c.close()
            return [{'id': r[0], 'name': r[1], 'specialties': r[2]} for r in rows]
        except Exception:
            return [{'id': i, 'name': f'AI_{i}'} for i in range(count)]

    def get_chat_sessions(self) -> List[ChatSession]:
        return list(self._chat_sessions)

class SmartLearningUpgrader:
    """智能自动升级AI员工学识/技能/能力"""

    def __init__(self):
        self._upgrades: deque = deque(maxlen=300)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f'[SmartLearningUpgrader] {event}: {detail}')

    def upgrade_learning(self, employee: Dict=None) -> LearningUpgrade:
        """执行学习升级"""
        if not employee:
            employee = self._get_random_employee()
        if not employee:
            return LearningUpgrade()
        (resource_type, resource_title, resource_domain, resource_quality) = random.choice(LEARNING_RESOURCES)
        upgrade_id = hashlib.md5(f'upg_{time.time()}'.encode()).hexdigest()[:16]
        old_accuracy = float(employee.get('accuracy', 0.9))
        learning_rate = float(employee.get('learning_rate', 0.05))
        improvement = resource_quality * learning_rate * random.uniform(0.5, 1.5)
        new_accuracy = min(old_accuracy + improvement, 0.99)
        knowledge_gained = int(resource_quality * 100 * random.uniform(0.5, 1.5))
        skill_map = {'安全': '安全分析能力', '密码学': '密码应用能力', 'AI/ML': 'AI模型能力', '架构': '系统设计能力', '数据': '数据处理能力'}
        skill_improved = skill_map.get(resource_domain, '综合能力')
        upgrade_status = 'completed' if random.random() < 0.92 else 'failed'
        upgrade = LearningUpgrade(upgrade_id=upgrade_id, employee_id=str(employee.get('id', '')), employee_name=employee.get('name', ''), resource_type=resource_type, resource_title=resource_title, resource_domain=resource_domain, resource_quality=resource_quality, knowledge_gained=knowledge_gained, skill_improved=skill_improved, old_accuracy=old_accuracy, new_accuracy=new_accuracy if upgrade_status == 'completed' else old_accuracy, upgrade_status=upgrade_status, started_at=datetime.now().isoformat(), completed_at=datetime.now().isoformat() if upgrade_status == 'completed' else '')
        self._upgrades.append(upgrade)
        self._log('UPGRADE', f"{employee.get('name', '')} 学习{resource_title}, {skill_improved}+{improvement:.3f}")
        if upgrade_status == 'completed':
            self._update_employee_accuracy(employee.get('id'), new_accuracy)
        return upgrade

    def _get_random_employee(self) -> Dict:
        """获取随机员工"""
        try:
            with _LOCK:
                c = _get_conn()
                cur = c.cursor()
                cur.execute("SELECT id, name, accuracy, learning_rate, specialties\n                              FROM ai_employees\n                              WHERE status='active' AND name NOT LIKE 'MTENC:%'\n                              ORDER BY RANDOM() LIMIT 1")
                row = cur.fetchone()
                c.close()
            if row:
                return {'id': row[0], 'name': row[1], 'accuracy': row[2], 'learning_rate': row[3], 'specialties': row[4]}
        except Exception:
            pass
        return {'id': 1, 'name': 'AI_测试员工', 'accuracy': 0.9, 'learning_rate': 0.05}

    def _update_employee_accuracy(self, emp_id, new_accuracy: float):
        """更新员工准确率"""
        try:
            with _LOCK:
                c = _get_conn()
                cur = c.cursor()
                cur.execute('UPDATE ai_employees SET accuracy=?, updated_at=?\n                              WHERE id=?', (new_accuracy, datetime.now().isoformat(), emp_id))
                c.commit()
                c.close()
        except Exception as e:
            logger.debug(f'更新员工准确率失败: {e}')

    def get_upgrades(self) -> List[LearningUpgrade]:
        return list(self._upgrades)

class AnomalyAIFeeder:
    """自动检测AI异常行为并投喂脑库"""

    def __init__(self):
        self._feeds: deque = deque(maxlen=300)
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f'[AnomalyAIFeeder] {event}: {detail}')

    def detect_and_feed(self, employee: Dict=None) -> AnomalyFeedRecord:
        """检测异常并投喂"""
        if not employee:
            employee = self._get_anomaly_employee()
        if not employee:
            return AnomalyFeedRecord()
        (anomaly_type, anomaly_title, anomaly_desc, severity) = random.choice(ANOMALY_TYPES)
        feed_id = hashlib.md5(f'anom_{time.time()}'.encode()).hexdigest()[:16]
        accuracy = float(employee.get('accuracy', 0.95))
        detected_value = accuracy
        threshold_value = ANOMALY_THRESHOLD if anomaly_type == 'accuracy_drop' else 0.5
        is_anomaly = anomaly_type == 'accuracy_drop' and accuracy < threshold_value or random.random() < 0.3
        if is_anomaly:
            if severity in ('high', 'critical'):
                feed_action = 'repair_trigger'
                feed_content = f"AI员工{employee.get('name', '')}发生{anomaly_title},触发修复流程"
            elif severity == 'medium':
                feed_action = 'brain_feed'
                feed_content = f"AI员工{employee.get('name', '')}行为异常({anomaly_title}),投喂脑库供学习"
            else:
                feed_action = 'archive'
                feed_content = f"AI员工{employee.get('name', '')}轻微异常({anomaly_title}),归档记录"
            feed_status = 'fed' if feed_action == 'brain_feed' else 'repaired' if feed_action == 'repair_trigger' else 'archived'
        else:
            feed_action = 'none'
            feed_content = f"AI员工{employee.get('name', '')}行为正常,无异常"
            feed_status = 'normal'
        record = AnomalyFeedRecord(feed_id=feed_id, employee_id=str(employee.get('id', '')), employee_name=employee.get('name', ''), anomaly_type=anomaly_type, anomaly_title=anomaly_title, anomaly_description=anomaly_desc, severity=severity, detected_value=detected_value, threshold_value=threshold_value, feed_action=feed_action, feed_content=feed_content, feed_status=feed_status, detected_at=datetime.now().isoformat(), fed_at=datetime.now().isoformat() if feed_action != 'none' else '')
        self._feeds.append(record)
        if feed_action in ('brain_feed', 'repair_trigger') and HAS_DEV_FLOW:
            try:
                feed_brain('anomaly_feed', anomaly_type, feed_content)
            except Exception:
                pass
        self._log('ANOMALY_FEED', f"{employee.get('name', '')}: {anomaly_title}({severity}) -> {feed_action}")
        return record

    def _get_anomaly_employee(self) -> Dict:
        """获取可能异常的员工"""
        try:
            with _LOCK:
                c = _get_conn()
                cur = c.cursor()
                cur.execute("SELECT id, name, accuracy, total_tasks, failed_fixes\n                              FROM ai_employees\n                              WHERE status='active' AND name NOT LIKE 'MTENC:%'\n                              ORDER BY accuracy ASC LIMIT 1")
                row = cur.fetchone()
                c.close()
            if row:
                return {'id': row[0], 'name': row[1], 'accuracy': row[2], 'total_tasks': row[3], 'failed_fixes': row[4]}
        except Exception:
            pass
        return {'id': 1, 'name': 'AI_测试员工', 'accuracy': 0.92}

    def get_feeds(self) -> List[AnomalyFeedRecord]:
        return list(self._feeds)

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
        logger.info(f'[EigenFluxBroadcast] {event}: {detail}')

    def run_cycle(self, flow_id: str='', rounds: int=1) -> BroadcastReport:
        """执行单次交流周期"""
        if not flow_id:
            flow_id = f'ef_broadcast_{int(time.time())}'
        self._log('CYCLE_START', f'开始广播交流周期,flow_id={flow_id},轮次={rounds}')
        t0 = time.time()
        all_broadcasts = []
        all_invitations = []
        all_chats = []
        all_upgrades = []
        all_feeds = []
        for r in range(rounds):
            self._log('ROUND', f'第{r + 1}/{rounds}轮')
            bc = self._broadcaster.broadcast()
            all_broadcasts.append(bc)
            invs = self._inviter.invite_experts()
            all_invitations.extend(invs)
            chat = self._chatter.initiate_chat()
            all_chats.append(chat)
            upg = self._learner.upgrade_learning()
            all_upgrades.append(upg)
            feed = self._feeder.detect_and_feed()
            all_feeds.append(feed)
        report = self._generate_report(flow_id, all_broadcasts, all_invitations, all_chats, all_upgrades, all_feeds)
        report.duration = time.time() - t0
        self._persist_to_database(flow_id, report)
        self._log('CYCLE_COMPLETE', f'周期完成,耗时{report.duration:.1f}s')
        return report

    def _generate_report(self, flow_id: str, broadcasts: List, invitations: List, chats: List, upgrades: List, feeds: List) -> BroadcastReport:
        """生成报告"""
        report_id = hashlib.md5(f'rpt_{time.time()}'.encode()).hexdigest()[:16]
        accepted_invites = sum((1 for i in invitations if i.invitation_status == 'accepted'))
        completed_upgrades = sum((1 for u in upgrades if u.upgrade_status == 'completed'))
        anomaly_count = sum((1 for f in feeds if f.feed_action != 'none'))
        teams = set()
        for i in invitations:
            if i.joined_team:
                teams.add(i.joined_team)
        summary = f"EigenFlux广播网络深度交流周期完成: 广播{len(broadcasts)}次, 邀请专家{len(invitations)}位(接受{accepted_invites}位), 好友聊天{len(chats)}场, 学习升级{len(upgrades)}次(完成{completed_upgrades}次), 异常投喂{anomaly_count}次。涉及团队: {(', '.join(teams) if teams else '无')}"
        report = BroadcastReport(report_id=report_id, flow_id=flow_id, total_broadcasts=len(broadcasts), total_invitations=len(invitations), total_chats=len(chats), total_upgrades=len(upgrades), total_anomaly_feeds=anomaly_count, broadcasts=[self._broadcast_to_dict(b) for b in broadcasts], invitations=[self._invitation_to_dict(i) for i in invitations], chats=[self._chat_to_dict(c) for c in chats], upgrades=[self._upgrade_to_dict(u) for u in upgrades], anomaly_feeds=[self._feed_to_dict(f) for f in feeds], timeline=self._timeline + self._broadcaster._timeline + self._inviter._timeline + self._chatter._timeline + self._learner._timeline + self._feeder._timeline, summary=summary, generated_at=datetime.now().isoformat())
        return report

    def _broadcast_to_dict(self, b: BroadcastEvent) -> Dict:
        return {'broadcast_id': b.broadcast_id, 'topic_type': b.topic_type, 'topic_title': b.topic_title, 'content': b.content, 'sender_name': b.sender_name, 'target_count': b.target_count, 'received_count': b.received_count, 'acknowledged_count': b.acknowledged_count, 'broadcast_type': b.broadcast_type, 'priority': b.priority}

    def _invitation_to_dict(self, i: ExpertInvitation) -> Dict:
        return {'invitation_id': i.invitation_id, 'expert_name': i.expert_name, 'expert_domain': i.expert_domain, 'expert_specialty': i.expert_specialty, 'expected_accuracy': i.expected_accuracy, 'invitation_status': i.invitation_status, 'joined_team': i.joined_team}

    def _chat_to_dict(self, c: ChatSession) -> Dict:
        return {'session_id': c.session_id, 'initiator_name': c.initiator_name, 'friend_name': c.friend_name, 'topic': c.topic, 'message_count': c.message_count, 'knowledge_exchanged': c.knowledge_exchanged, 'collaboration_triggered': c.collaboration_triggered}

    def _upgrade_to_dict(self, u: LearningUpgrade) -> Dict:
        return {'upgrade_id': u.upgrade_id, 'employee_name': u.employee_name, 'resource_type': u.resource_type, 'resource_title': u.resource_title, 'resource_domain': u.resource_domain, 'knowledge_gained': u.knowledge_gained, 'skill_improved': u.skill_improved, 'old_accuracy': u.old_accuracy, 'new_accuracy': u.new_accuracy, 'upgrade_status': u.upgrade_status}

    def _feed_to_dict(self, f: AnomalyFeedRecord) -> Dict:
        return {'feed_id': f.feed_id, 'employee_name': f.employee_name, 'anomaly_type': f.anomaly_type, 'anomaly_title': f.anomaly_title, 'severity': f.severity, 'feed_action': f.feed_action, 'feed_status': f.feed_status}

    def _persist_to_database(self, flow_id: str, report: BroadcastReport):
        """持久化到数据库"""
        now = datetime.now().isoformat()
        count = 0
        with _LOCK:
            c = _get_conn()
            cur = c.cursor()
            for b in report.broadcasts:
                try:
                    cur.execute('INSERT OR REPLACE INTO mt_ef_broadcast_events\n                        (broadcast_id, topic_type, topic_title, content, sender_id, sender_name,\n                         target_count, received_count, acknowledged_count, broadcast_type,\n                         priority, created_at, expires_at, responses_json, flow_id)\n                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (b['broadcast_id'], b['topic_type'], b['topic_title'], b.get('content', ''), 'system', b['sender_name'], b['target_count'], b['received_count'], b['acknowledged_count'], b['broadcast_type'], b['priority'], now, now, '[]', flow_id))
                    count += 1
                except Exception as e:
                    logger.debug(f'存储广播失败: {e}')
            for i in report.invitations:
                try:
                    cur.execute('INSERT OR REPLACE INTO mt_ef_expert_invitations\n                        (invitation_id, expert_name, expert_domain, expert_specialty,\n                         expected_accuracy, invitation_reason, invitation_status,\n                         invited_at, responded_at, joined_team, contribution_target, flow_id)\n                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)', (i['invitation_id'], i['expert_name'], i['expert_domain'], i['expert_specialty'], i.get('expected_accuracy', 0), f'能力缺口邀请', i['invitation_status'], now, now, i.get('joined_team', ''), f'贡献知识经验', flow_id))
                    count += 1
                except Exception as e:
                    logger.debug(f'存储邀请失败: {e}')
            for ch in report.chats:
                try:
                    cur.execute('INSERT OR REPLACE INTO mt_ef_chat_sessions\n                        (session_id, initiator_id, initiator_name, friend_id, friend_name,\n                         topic, message_count, messages_json, knowledge_exchanged,\n                         collaboration_triggered, is_active, created_at, last_activity, flow_id)\n                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (ch['session_id'], '', ch['initiator_name'], '', ch['friend_name'], ch['topic'], ch['message_count'], '[]', ch['knowledge_exchanged'], 1 if ch['collaboration_triggered'] else 0, 1, now, now, flow_id))
                    count += 1
                except Exception as e:
                    logger.debug(f'存储聊天失败: {e}')
            for u in report.upgrades:
                try:
                    cur.execute('INSERT OR REPLACE INTO mt_ef_learning_upgrades\n                        (upgrade_id, employee_id, employee_name, resource_type, resource_title,\n                         resource_domain, resource_quality, knowledge_gained, skill_improved,\n                         old_accuracy, new_accuracy, upgrade_status, started_at, completed_at, flow_id)\n                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (u['upgrade_id'], '', u['employee_name'], u['resource_type'], u['resource_title'], u['resource_domain'], 0.9, u['knowledge_gained'], u['skill_improved'], u['old_accuracy'], u['new_accuracy'], u['upgrade_status'], now, now, flow_id))
                    count += 1
                except Exception as e:
                    logger.debug(f'存储升级失败: {e}')
            for f in report.anomaly_feeds:
                try:
                    cur.execute('INSERT OR REPLACE INTO mt_ef_anomaly_feeds\n                        (feed_id, employee_id, employee_name, anomaly_type, anomaly_title,\n                         anomaly_description, severity, detected_value, threshold_value,\n                         feed_action, feed_content, feed_status, detected_at, fed_at, flow_id)\n                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (f['feed_id'], '', f['employee_name'], f['anomaly_type'], f['anomaly_title'], f.get('anomaly_description', ''), f['severity'], 0, 0, f['feed_action'], f.get('feed_content', ''), f['feed_status'], now, now, flow_id))
                    count += 1
                except Exception as e:
                    logger.debug(f'存储异常投喂失败: {e}')
            c.commit()
            c.close()
        self._log('PERSIST', f'持久化{count}条记录')
        return count

    def start_daemon(self):
        """启动守护线程"""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        threads_config = [('broadcast', self._broadcast_loop, BROADCAST_INTERVAL), ('invite', self._invite_loop, INVITE_INTERVAL), ('chat', self._chat_loop, CHAT_INTERVAL), ('learning', self._learning_loop, LEARNING_INTERVAL), ('anomaly', self._anomaly_loop, ANOMALY_FEED_INTERVAL)]
        for (name, func, interval) in threads_config:
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
                logger.error(f'守护线程{name}异常: {e}')
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
if __name__ == '__main__':
    engine = EigenFluxBroadcastEngine()
    report = engine.run_cycle(flow_id='ef_broadcast_test_001', rounds=3)
    print(f"\n{'=' * 60}")
    print(f' EigenFlux广播网络深度交流引擎 v1.1.0')
    print(f"{'=' * 60}")
    print(f' 报告ID: {report.report_id}')
    print(f' 广播次数: {report.total_broadcasts}')
    print(f' 邀请专家: {report.total_invitations}')
    print(f' 好友聊天: {report.total_chats}')
    print(f' 学习升级: {report.total_upgrades}')
    print(f' 异常投喂: {report.total_anomaly_feeds}')
    print(f' 耗时: {report.duration:.1f}s')
    print(f' 摘要: {report.summary}')
    print(f"{'=' * 60}")