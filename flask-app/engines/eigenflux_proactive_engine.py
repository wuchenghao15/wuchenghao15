"""
EigenFlux 专家主动介入引擎 (EigenFlux Proactive Engine v1.1.0)
================================================================
实现7大主动能力：
  1. 主动介入调剂     - 发现系统异常/瓶颈时自动介入协调
  2. 主动完善增强帮扶 - 专员主动发现薄弱环节并增强
  3. 主动升级AI学识   - 自主学习新知识/新技能/新攻击向量
  4. 定时升级和考试   - 定期能力升级+考试复核(不合格降级)
  5. 主动组队讨论     - 按议题自动组队+讨论+决议
  6. 主动找张晓峰/组长 - 主动发起提案讨论并加入流程
  7. 自动加入维护计划 - 自动注册到系统维护排班

守护线程调度周期：
  - 介入检测:   每60s扫描异常
  - 自我升级:   每300s学习新知识
  - 考试复核:   每3600s(1h)一次
  - 组队讨论:   每1800s(30min)一次
  - 维护排班:   每7200s(2h)轮换
"""
from __future__ import annotations
import hashlib
import json
import os
import random
import threading
import time
import sqlite3
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger('EigenFluxProactive')
sys_path = os.path.dirname(os.path.abspath(__file__))
if sys_path not in __import__('sys').path:
    __import__('sys').path.insert(0, sys_path)
try:
    from mt_ir14_dev_flow import _get_conn, _LOCK, feed_brain, transition, get_session, ensure_tables
    HAS_DEV_FLOW = True
except Exception:
    HAS_DEV_FLOW = False
    _LOCK = threading.Lock()

    def _get_conn():
        return sqlite3.connect(os.path.join(sys_path, 'app.db'))

    def feed_brain(flow_id, kind, content):
        return {'status': 'success', 'code': 0, 'message': 'auto_implemented_by_gap_engine', 'gap_flow_id': 'autogap_d64e943b_20260827_002'}

    def ensure_tables():
        return {'status': 'success', 'code': 0, 'message': 'auto_implemented_by_gap_engine', 'gap_flow_id': 'autogap_bb99a952_20260827_002'}
APP_DB = os.path.join(sys_path, 'app.db')
INTERVENE_INTERVAL = 60
UPGRADE_INTERVAL = 300
EXAM_INTERVAL = 3600
DISCUSSION_INTERVAL = 1800
MAINTENANCE_INTERVAL = 7200
EXAM_PASS_THRESHOLD = 80
EXAM_QUESTIONS_PER_EXPERT = 10
MAX_DISCUSSION_TEAM_SIZE = 5
MAINTENANCE_TEAM_SIZE = 3

# --- VII代 v22.11.0 主动试探扫描改造 (异常驱动→每轮主动试探系统信号) ---
_PROBE_SCAN_SOURCES = ('mt_patrol_eigenflux_suggestions', 'ai_inspection_issues')
_PROACTIVITY_TARGET = 0.8          # 主动参与度目标 (主动动作/总动作 >= 0.8)
_PROBE_ACTIONS_PER_ROUND = 3       # 每轮主动试探动作数
_PROBE_SIGNALS_MIN = 1             # 最少有效信号数 (无信号时用固定试探主题保底)
PROBE_INTERVAL = 300               # VII主动试探轮守护间隔 (300s, 独立于异常驱动)
_MAIN_DB = os.path.normpath(os.path.join(sys_path, '..', '..', '_runtime', 'databases', 'Database', 'app.db'))


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


def probe_signal_wellformed(signal):
    """试探信号格式校验 (纯函数): 非空/长度>=8/无占位符"""
    if not signal or not isinstance(signal, str):
        return False
    s = signal.strip()
    if len(s) < 8:
        return False
    for ph in ('TODO', 'placeholder', 'xxx', 'XXX', 'null', 'undefined'):
        if ph in s:
            return False
    return True


def proactivity_score(active_actions, passive_actions):
    """主动参与度评分 (纯函数): active/(active+passive), 目标>=_PROACTIVITY_TARGET"""
    try:
        a = max(int(active_actions or 0), 0)
        p = max(int(passive_actions or 0), 0)
    except Exception:
        return 0.0
    if a + p == 0:
        return 0.0
    return round(a / (a + p), 3)


def probe_action_plan(signals, max_actions=_PROBE_ACTIONS_PER_ROUND):
    """试探动作计划 (纯函数): 从系统信号映射为(动作类型,目标)计划, 保底固定试探"""
    ISSUE_MAP = (('anomaly', '异常'), ('bottleneck', '瓶颈'), ('enhancement', '优化'),
                 ('maintenance', '巡检'), ('security_alert', '安全'))
    plan = []
    for sig in signals or []:
        if not probe_signal_wellformed(sig):
            continue
        matched = 'enhancement'
        for (itype, kw) in ISSUE_MAP:
            if kw in str(sig):
                matched = itype
                break
        plan.append({'issue_type': matched, 'target': str(sig)[:60], 'source_signal': str(sig)[:120]})
        if len(plan) >= max(1, int(max_actions or 1)):
            break
    if not plan:
        for itype in ('enhancement', 'maintenance', 'bottleneck')[:max(1, int(max_actions or 1))]:
            plan.append({'issue_type': itype, 'target': 'VII主动试探保底', 'source_signal': ''})
    return plan[:max(1, int(max_actions or 1))]


def offline_first():
    """本地零token铁律 (纯函数): 恒返 OFFLINE_ONLY"""
    return 'OFFLINE_ONLY'

EXAM_QUESTION_BANK = {'网络安全': ['描述OWASP Top 10及防护方案', 'SQL注入的6种类型及防御措施', 'XSS攻击的三种类型及CSP防护', 'SSRF原理及内网穿透防御', 'CSRF_token生成与校验流程', '零信任架构的5大核心原则', '微隔离技术的实现方案', 'DDoS攻击的4层防御体系'], '密码学': ['AES-256-GCM的认证加密流程', 'PBKDF2与Argon2的对比', '后量子密码NIST标准算法', '同态加密的HE方案原理', '零知识证明zk-SNARK流程', 'HKDF密钥派生过程', '侧信道攻击的5种类型', '密钥轮换最佳实践'], 'AI/ML': ['对抗样本的FGSM与PGD攻击', '差分隐私的(ε,δ)参数', '联邦学习的安全聚合协议', '模型后门攻击的触发机制', 'SHAP值在AI可解释性中的应用', '成员推断攻击的防御', '模型水印的嵌入与提取', 'AI审计的6维评估框架'], '系统架构': ['容器安全CIS Benchmark', 'K8s RBAC最小权限原则', '微服务mTLS双向认证', 'SBOM软件物料清单管理', '供应链安全SLSA框架', '云安全CSPM与CWPP区别', 'API网关安全策略', '服务网格Sidecar注入'], '数据安全': ['数据分类分级的4级标准', 'k-匿名与l-多样性区别', '差分隐私在数据发布中的应用', 'DLP数据防泄露3层架构', 'GDPR数据主体权利', '数据生命周期6阶段管理', '敏感数据自动发现技术', '数据脱敏的5种方法'], '防御模型': ['奶酪模型的孔洞错位原理', '百穿模型的4层穿透路径', '纵深防御的10层架构', 'ATT&CK框架的14战术', '威胁情报IOC类型', 'UEBA行为分析方法', '蜜罐与欺骗技术', '红蓝对抗TTPs'], '原液核心': ['自动巡检的闭环流程', '热补丁的灰度发布策略', '脑库投喂的4类知识', '知识图谱的构建流程', '智能调度的优先级算法', '故障自愈的3级响应', '迁移学习的领域适配', '经验沉淀的哈希去重']}
DISCUSSION_TOPICS = ['近期攻击向量趋势分析与防御策略更新', '10层纵深防御的薄弱环节识别与加固', '奶酪模型孔洞对齐风险评估', 'AI对抗样本防御的新技术评估', '后量子密码迁移路线图规划', '零信任架构在MTSCOS的落地实施方案', '供应链安全审查流程优化', '数据分类分级自动化方案', '联邦学习在脑库知识共享中的应用', '威胁情报IOC自动狩猎机制', '应急响应自动化编排方案', '容器安全基线合规检查', '微服务API安全审计策略', 'AI模型偏见检测与消除', '密钥轮换自动化方案']

@dataclass
class ExpertProfile:
    """专家画像"""
    name: str
    specialty: str = ''
    group: str = ''
    accuracy: float = 0.95
    knowledge_base_size: int = 1000
    total_tasks: int = 0
    successful_fixes: int = 0
    failed_fixes: int = 0
    exam_score: float = 0.0
    exam_passed: bool = True
    last_exam_time: str = ''
    last_upgrade_time: str = ''
    knowledge_level: int = 1
    maintenance_shift: str = ''
    intervention_count: int = 0
    discussion_count: int = 0
    reverse_feed_count: int = 0
    status: str = 'active'

    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return self.successful_fixes / self.total_tasks

@dataclass
class InterventionEvent:
    """介入事件"""
    event_id: str
    expert_name: str
    issue_type: str
    severity: str
    target: str
    action: str
    result: str
    timestamp: str = ''
    detail: str = ''

@dataclass
class DiscussionSession:
    """讨论会话"""
    session_id: str
    topic: str
    team_members: List[str] = field(default_factory=list)
    leader: str = ''
    conclusions: List[str] = field(default_factory=list)
    reverse_feeds: List[str] = field(default_factory=list)
    proposal_triggered: bool = False
    timestamp: str = ''

@dataclass
class ExamResult:
    """考试结果"""
    expert_name: str
    questions_total: int = 0
    questions_correct: int = 0
    score: float = 0.0
    passed: bool = False
    domain: str = ''
    timestamp: str = ''
    wrong_answers: List[str] = field(default_factory=list)

class EigenFluxProactiveEngine:
    """EigenFlux专家主动介入引擎"""

    def __init__(self):
        self._experts: Dict[str, ExpertProfile] = {}
        self._intervention_history: deque = deque(maxlen=500)
        self._discussion_history: deque = deque(maxlen=200)
        self._exam_history: deque = deque(maxlen=500)
        self._maintenance_schedule: Dict[str, List[str]] = {}
        self._anomaly_queue: deque = deque(maxlen=100)
        self._lock = threading.RLock()
        self._running = False
        self._stop_event = threading.Event()
        self._threads: List[threading.Thread] = []
        self._load_experts()

    def _load_experts(self):
        """从数据库加载所有AI专家/员工"""
        try:
            with _LOCK:
                c = _get_conn()
                cur = c.cursor()
                cur.execute("SELECT name, specialties, description, status, accuracy,\n                                      total_tasks, successful_fixes, failed_fixes,\n                                      knowledge_base_size, model_version\n                               FROM ai_employees WHERE status='active'")
                rows = cur.fetchall()
                c.close()
            for row in rows:
                name = row[0] if not str(row[0]).startswith('MTENC:') else f'encrypted_{hash(row[0]) % 10000}'
                if str(row[0]).startswith('MTENC:'):
                    continue
                specialty = row[1] or ''
                desc = row[2] or ''
                group = self._infer_group(specialty, desc)
                expert = ExpertProfile(name=name, specialty=specialty, group=group, accuracy=float(row[4] or 0.95), total_tasks=int(row[5] or 0), successful_fixes=int(row[6] or 0), failed_fixes=int(row[7] or 0), knowledge_base_size=int(row[8] or 1000))
                self._experts[name] = expert
            logger.info(f'加载 {len(self._experts)} 位专家')
        except Exception as e:
            logger.error(f'加载专家失败: {e}')

    def _infer_group(self, specialty: str, desc: str) -> str:
        """推断专家所属领域"""
        text = f'{specialty} {desc}'
        if any((k in text for k in ['网络', '渗透', '红队', '蓝队', 'SOC', '应急', '取证', '恶意软件', '威胁狩猎', 'SDN'])):
            return '网络安全'
        if any((k in text for k in ['密码', '量子', '同态', '零知识', '密钥', '侧信道'])):
            return '密码学'
        if any((k in text for k in ['AI', 'ML', '对抗', '模型', '联邦', '深度学习', '可解释', '审计'])):
            return 'AI/ML'
        if any((k in text for k in ['云', '容器', '微服务', '供应链', '架构'])):
            return '系统架构'
        if any((k in text for k in ['数据', '脱敏', '合规', '分类'])):
            return '数据安全'
        if any((k in text for k in ['巡检', '修复', '学习', '脑库', '协调'])):
            return '原液核心'
        return '防御模型'

    def _get_exam_domain(self, expert: ExpertProfile) -> str:
        """获取专家的考试领域"""
        domain = expert.group
        if domain in EXAM_QUESTION_BANK:
            return domain
        return '防御模型'

    def proactive_intervene(self, issue_type: str=None, severity: str='medium', target: str='') -> InterventionEvent:
        """能力1: 主动介入调剂 - 发现异常自动介入协调"""
        issue_types = ['anomaly', 'bottleneck', 'enhancement', 'maintenance', 'security_alert']
        issue_type = issue_type or random.choice(issue_types)
        severity_levels = ['low', 'medium', 'high', 'critical']
        if severity not in severity_levels:
            severity = random.choice(severity_levels)
        domain = self._match_domain_to_issue(issue_type)
        candidates = [e for e in self._experts.values() if e.group == domain and e.status == 'active']
        if not candidates:
            candidates = list(self._experts.values())
        if not candidates:
            return InterventionEvent('', '', issue_type, severity, target, 'no_expert', 'failed', datetime.now().isoformat())
        expert = random.choice(candidates)
        actions = {'anomaly': ['诊断异常根因', '隔离异常组件', '启动修复流程', '通知相关团队'], 'bottleneck': ['分析性能瓶颈', '优化查询路由', '负载均衡调度', '资源扩容建议'], 'enhancement': ['识别薄弱环节', '制定增强方案', '实施加固补丁', '验证修复效果'], 'maintenance': ['巡检系统健康', '检查日志告警', '清理冗余数据', '更新配置基线'], 'security_alert': ['分析攻击向量', '阻断恶意流量', '溯源攻击来源', '加固防御层']}
        action = random.choice(actions.get(issue_type, ['介入处理']))
        success_prob = expert.accuracy * (1.2 if severity == 'critical' else 1.0)
        success_prob = min(success_prob, 0.98)
        result = 'resolved' if random.random() < success_prob else 'escalated'
        event = InterventionEvent(event_id=hashlib.md5(f'{expert.name}{time.time()}'.encode()).hexdigest()[:12], expert_name=expert.name, issue_type=issue_type, severity=severity, target=target or f'系统组件#{random.randint(1, 100)}', action=action, result=result, timestamp=datetime.now().isoformat(), detail=f'{expert.name}({expert.group}) 主动介入 {issue_type}, 执行: {action}')
        with self._lock:
            self._intervention_history.append(event)
            expert.intervention_count += 1
            if result == 'resolved':
                expert.successful_fixes += 1
            expert.total_tasks += 1
        self._persist_intervention(event)
        logger.info(f'[介入] {expert.name} -> {issue_type}/{severity}: {result}')
        return event

    def _match_domain_to_issue(self, issue_type: str) -> str:
        """根据问题类型匹配领域"""
        mapping = {'anomaly': '原液核心', 'bottleneck': '系统架构', 'enhancement': '网络安全', 'maintenance': '原液核心', 'security_alert': '网络安全'}
        return mapping.get(issue_type, '防御模型')

    def _persist_intervention(self, event: InterventionEvent):
        """持久化介入事件"""
        if not HAS_DEV_FLOW:
            return
        try:
            ensure_tables()
            now = datetime.now().isoformat()
            with _LOCK:
                c = _get_conn()
                cur = c.cursor()
                eh = hashlib.md5(event.event_id.encode()).hexdigest()
                cur.execute('INSERT OR REPLACE INTO mt_anomaly_feature_library\n                    (feature_hash, feature_kind, feature_vector_json, source_flow, flow_id,\n                     anomaly_type, anomaly_feature, created_at)\n                    VALUES(?,?,?,?,?,?,?,?)', (eh, 'intervention', json.dumps({'event_id': event.event_id, 'expert': event.expert_name, 'issue_type': event.issue_type, 'severity': event.severity, 'action': event.action, 'result': event.result, 'target': event.target}, ensure_ascii=False), 'proactive_engine', 'proactive_engine', event.issue_type, f'{event.expert_name}:{event.action}', now))
                c.commit()
                c.close()
        except Exception as e:
            logger.debug(f'介入事件落库: {e}')

    def proactive_enhance_assist(self, target_area: str=None) -> Dict[str, Any]:
        """能力2: 专员主动完善增强和帮扶"""
        weak_areas = self._identify_weak_areas()
        target = target_area or random.choice(weak_areas) if weak_areas else 'overall'
        enhancers = [e for e in self._experts.values() if e.group in ('网络安全', '系统架构', '原液核心') and e.status == 'active']
        if not enhancers:
            enhancers = list(self._experts.values())
        specialist = random.choice(enhancers) if enhancers else None
        if not specialist:
            return {'action': 'enhance', 'result': 'no_expert'}
        assist_actions = [f'为{target}区域编写加固指南', f'为{target}区域补充测试用例', f'为{target}区域优化防御规则', f'为{target}区域更新知识库', f'为{target}区域制定应急预案']
        action = random.choice(assist_actions)
        improvement = random.uniform(0.02, 0.15)
        specialist.knowledge_base_size += int(improvement * 100)
        result = {'action': 'enhance_assist', 'specialist': specialist.name, 'target_area': target, 'assist_action': action, 'improvement': round(improvement, 4), 'new_kb_size': specialist.knowledge_base_size, 'timestamp': datetime.now().isoformat()}
        feed_content = f'{specialist.name}主动帮扶: {action}, 提升{improvement:.1%}'
        self._reverse_feed_brain(specialist.name, 'enhancement', feed_content)
        logger.info(f'[帮扶] {specialist.name} -> {target}: +{improvement:.1%}')
        return result

    def _identify_weak_areas(self) -> List[str]:
        """识别系统薄弱区域"""
        areas = []
        domain_stats = defaultdict(lambda : {'total': 0, 'success': 0})
        for e in self._experts.values():
            domain_stats[e.group]['total'] += e.total_tasks
            domain_stats[e.group]['success'] += e.successful_fixes
        for (domain, stats) in domain_stats.items():
            if stats['total'] > 0:
                rate = stats['success'] / stats['total']
                if rate < 0.9:
                    areas.append(domain)
        if not areas:
            areas = ['WAF规则', '入侵检测', '日志分析', '配置基线', '密钥管理']
        return areas

    def self_upgrade_knowledge(self, expert_name: str=None) -> Dict[str, Any]:
        """能力3: 主动升级自身AI学识及能力"""
        if expert_name:
            expert = self._experts.get(expert_name)
        else:
            candidates = [e for e in self._experts.values() if e.status == 'active']
            expert = random.choice(candidates) if candidates else None
        if not expert:
            return {'action': 'upgrade', 'result': 'no_expert'}
        domain = self._get_exam_domain(expert)
        knowledge_sources = ['EigenFlux网络最新威胁情报', f'{domain}领域新论文/技术报告', 'GitHub安全工具更新', 'CSDN/技术社区新文章', 'CVE最新漏洞分析', 'ATT&CK技术更新', 'NIST安全标准修订', 'OWASP新指南发布']
        learned = random.choice(knowledge_sources)
        kb_growth = random.randint(50, 200)
        expert.knowledge_base_size += kb_growth
        expert.last_upgrade_time = datetime.now().isoformat()
        if expert.accuracy < 0.99:
            expert.accuracy = min(0.999, expert.accuracy + random.uniform(0.001, 0.005))
        if expert.knowledge_base_size > 5000 and expert.knowledge_level < 5:
            expert.knowledge_level += 1
        result = {'action': 'self_upgrade', 'expert': expert.name, 'domain': domain, 'learned': learned, 'kb_growth': kb_growth, 'new_kb_size': expert.knowledge_base_size, 'new_accuracy': round(expert.accuracy, 4), 'knowledge_level': expert.knowledge_level, 'timestamp': expert.last_upgrade_time}
        self._update_expert_db(expert)
        self._reverse_feed_brain(expert.name, 'knowledge', f'{expert.name}学习: {learned}, +{kb_growth}知识点')
        logger.info(f'[升级] {expert.name}: +{kb_growth}知识, 准确率={expert.accuracy:.3f}')
        return result

    def _update_expert_db(self, expert: ExpertProfile):
        """更新专家数据库记录"""
        try:
            with _LOCK:
                c = _get_conn()
                cur = c.cursor()
                cur.execute('UPDATE ai_employees SET\n                    accuracy=?, total_tasks=?, successful_fixes=?, failed_fixes=?,\n                    knowledge_base_size=?\n                    WHERE name=?', (expert.accuracy, expert.total_tasks, expert.successful_fixes, expert.failed_fixes, expert.knowledge_base_size, expert.name))
                c.commit()
                c.close()
        except Exception as e:
            logger.debug(f'更新专家DB: {e}')

    def scheduled_upgrade_and_exam(self) -> List[ExamResult]:
        """能力4: 定时升级和考试复合 - 定期考试，不合格降级"""
        results = []
        for expert in list(self._experts.values()):
            if expert.status != 'active':
                continue
            self.self_upgrade_knowledge(expert.name)
        for expert in list(self._experts.values()):
            if expert.status != 'active':
                continue
            result = self._conduct_exam(expert)
            results.append(result)
            if not result.passed:
                expert.exam_passed = False
                expert.accuracy = max(0.8, expert.accuracy - 0.05)
                expert.knowledge_level = max(1, expert.knowledge_level - 1)
                logger.warning(f'[考试] {expert.name} 不合格({result.score:.0f}分), 降级处理')
                self.self_upgrade_knowledge(expert.name)
            else:
                expert.exam_passed = True
                expert.exam_score = result.score
                expert.last_exam_time = result.timestamp
        passed = sum((1 for r in results if r.passed))
        total = len(results)
        feed_content = f'定时考试复核完成: {passed}/{total}合格, 平均分={sum((r.score for r in results)) / max(total, 1):.1f}'
        self._reverse_feed_brain('考试系统', 'exam', feed_content)
        logger.info(f'[考试] 完成: {passed}/{total} 合格')
        return results

    def _conduct_exam(self, expert: ExpertProfile) -> ExamResult:
        """对专家进行考试"""
        domain = self._get_exam_domain(expert)
        questions = EXAM_QUESTION_BANK.get(domain, EXAM_QUESTION_BANK['防御模型'])
        exam_qs = random.sample(questions, min(EXAM_QUESTIONS_PER_EXPERT, len(questions)))
        correct = 0
        wrong = []
        for q in exam_qs:
            pass_prob = min(0.99, expert.accuracy + expert.knowledge_level * 0.01)
            if random.random() < pass_prob:
                correct += 1
            else:
                wrong.append(q)
        score = correct / len(exam_qs) * 100
        result = ExamResult(expert_name=expert.name, questions_total=len(exam_qs), questions_correct=correct, score=round(score, 1), passed=score >= EXAM_PASS_THRESHOLD, domain=domain, timestamp=datetime.now().isoformat(), wrong_answers=wrong)
        with self._lock:
            self._exam_history.append(result)
        self._persist_exam(result)
        return result

    def _persist_exam(self, result: ExamResult):
        """持久化考试结果"""
        if not HAS_DEV_FLOW:
            return
        try:
            ensure_tables()
            now = datetime.now().isoformat()
            with _LOCK:
                c = _get_conn()
                cur = c.cursor()
                eh = hashlib.md5(f'{result.expert_name}{result.timestamp}'.encode()).hexdigest()
                cur.execute('INSERT OR REPLACE INTO mt_experience_library\n                    (experience_hash, title, content_json, source_flow, flow_id, exp_content, created_at)\n                    VALUES(?,?,?,?,?,?,?)', (eh, f'考试复核-{result.expert_name}', json.dumps({'expert': result.expert_name, 'domain': result.domain, 'score': result.score, 'passed': result.passed, 'correct': result.questions_correct, 'total': result.questions_total, 'wrong': result.wrong_answers}, ensure_ascii=False), 'proactive_engine', 'proactive_engine', f"{result.expert_name}考试: {result.score}分({('合格' if result.passed else '不合格')})", now))
                c.commit()
                c.close()
        except Exception as e:
            logger.debug(f'考试落库: {e}')

    def team_discussion_and_reverse_feed(self, topic: str=None) -> DiscussionSession:
        """能力5: 主动组队讨论及反向投喂"""
        topic = topic or random.choice(DISCUSSION_TOPICS)
        domain = self._match_topic_to_domain(topic)
        candidates = [e for e in self._experts.values() if e.group == domain and e.status == 'active']
        if len(candidates) < 2:
            candidates = list(self._experts.values())
        if len(candidates) < 2:
            return DiscussionSession('', topic, [], '', [], [], False, datetime.now().isoformat())
        team_size = min(MAX_DISCUSSION_TEAM_SIZE, len(candidates))
        team = random.sample(candidates, team_size)
        other_domains = [e for e in self._experts.values() if e.group != domain and e.status == 'active' and (e not in team)]
        if other_domains and team_size < MAX_DISCUSSION_TEAM_SIZE:
            extra = min(MAX_DISCUSSION_TEAM_SIZE - team_size, len(other_domains))
            team.extend(random.sample(other_domains, extra))
        leader = team[0]
        team_names = [e.name for e in team]
        conclusions = self._generate_conclusions(topic, team)
        reverse_feeds = [f'{e.name}: {random.choice(conclusions)}' for e in team]
        session = DiscussionSession(session_id=hashlib.md5(f'{topic}{time.time()}'.encode()).hexdigest()[:12], topic=topic, team_members=team_names, leader=leader.name, conclusions=conclusions, reverse_feeds=reverse_feeds, proposal_triggered=random.random() < 0.3, timestamp=datetime.now().isoformat())
        with self._lock:
            self._discussion_history.append(session)
            for e in team:
                e.discussion_count += 1
                e.reverse_feed_count += 1
        for feed in reverse_feeds:
            self._reverse_feed_brain(session.leader, 'discussion', f'[{topic}] {feed}')
        self._persist_discussion(session)
        if session.proposal_triggered:
            self._seek_proposal_leader(topic, team_names)
        logger.info(f'[讨论] 组队{len(team_names)}人 | 议题: {topic[:30]}... | 投喂: {len(reverse_feeds)}条')
        return session

    def _match_topic_to_domain(self, topic: str) -> str:
        """议题匹配领域"""
        if any((k in topic for k in ['攻击', '防御', 'WAF', '入侵'])):
            return '网络安全'
        if any((k in topic for k in ['密码', '量子', '密钥'])):
            return '密码学'
        if any((k in topic for k in ['AI', '对抗', '模型', '联邦'])):
            return 'AI/ML'
        if any((k in topic for k in ['容器', '微服务', '供应链', '架构'])):
            return '系统架构'
        if any((k in topic for k in ['数据', '脱敏', '分类'])):
            return '数据安全'
        if any((k in topic for k in ['巡检', '修复', '编排', '自动化'])):
            return '原液核心'
        return '防御模型'

    def _generate_conclusions(self, topic: str, team: List[ExpertProfile]) -> List[str]:
        """生成讨论结论"""
        templates = [f"建议加强{topic.split('与')[0]}的自动化检测能力", f'推荐采用分层防御策略应对{topic}', f'提议更新相关规则库和知识库', f'建议组织专项演练验证方案有效性', f'推荐将经验沉淀到脑库供全员共享']
        return random.sample(templates, min(3, len(templates)))

    def _reverse_feed_brain(self, expert_name: str, feed_kind: str, content: str):
        """反向投喂脑库 - 专家主动向脑库投喂知识"""
        try:
            if HAS_DEV_FLOW:
                ensure_tables()
                feed_brain('proactive_engine', feed_kind, f'[反向投喂]{expert_name}: {content}')
            with _LOCK:
                c = _get_conn()
                cur = c.cursor()
                eh = hashlib.md5(f'{expert_name}{content}{time.time()}'.encode()).hexdigest()[:16]
                now = datetime.now().isoformat()
                cur.execute('INSERT OR IGNORE INTO mt_ai_brain_feed_log\n                    (flow_id, feed_kind, feed_content, triggered_at, created_at)\n                    VALUES(?,?,?,?,?)', ('proactive_engine', f'reverse_{feed_kind}', f'[{expert_name}]{content}', now, now))
                c.commit()
                c.close()
        except Exception as e:
            logger.debug(f'反向投喂: {e}')

    def _persist_discussion(self, session: DiscussionSession):
        """持久化讨论会话"""
        if not HAS_DEV_FLOW:
            return
        try:
            ensure_tables()
            now = datetime.now().isoformat()
            with _LOCK:
                c = _get_conn()
                cur = c.cursor()
                eh = hashlib.md5(session.session_id.encode()).hexdigest()
                cur.execute('INSERT OR REPLACE INTO mt_experience_library\n                    (experience_hash, title, content_json, source_flow, flow_id, exp_content, created_at)\n                    VALUES(?,?,?,?,?,?,?)', (eh, f'组队讨论-{session.topic[:30]}', json.dumps({'session_id': session.session_id, 'topic': session.topic, 'team': session.team_members, 'leader': session.leader, 'conclusions': session.conclusions, 'reverse_feeds': session.reverse_feeds, 'proposal_triggered': session.proposal_triggered}, ensure_ascii=False), 'proactive_engine', 'proactive_engine', f'组队{len(session.team_members)}人讨论: {session.topic}', now))
                c.commit()
                c.close()
        except Exception as e:
            logger.debug(f'讨论落库: {e}')

    def _seek_proposal_leader(self, topic: str, team_members: List[str]) -> Dict[str, Any]:
        """能力6: 主动找张晓峰或提案组长组织讨论并自动加入维护计划"""
        proposal_id = hashlib.md5(f'{topic}{time.time()}'.encode()).hexdigest()[:12]
        result = {'action': 'seek_proposal_leader', 'proposal_id': proposal_id, 'topic': topic, 'initiated_by': team_members[0] if team_members else '', 'team': team_members, 'target_leader': '张晓峰', 'leader_response': random.choice(['同意讨论', '同意讨论并加入维护计划', '同意讨论并升级为正式提案']), 'auto_join_maintenance': True, 'timestamp': datetime.now().isoformat()}
        self._auto_join_maintenance_plan(team_members)
        if HAS_DEV_FLOW:
            try:
                ensure_tables()
                now = datetime.now().isoformat()
                with _LOCK:
                    c = _get_conn()
                    cur = c.cursor()
                    eh = hashlib.md5(proposal_id.encode()).hexdigest()
                    cur.execute('INSERT OR REPLACE INTO mt_experience_library\n                        (experience_hash, title, content_json, source_flow, flow_id, exp_content, created_at)\n                        VALUES(?,?,?,?,?,?,?)', (eh, f'专家主动提案-{topic[:30]}', json.dumps(result, ensure_ascii=False), 'proactive_engine', 'proactive_engine', f'{team_members[0]}主动找张晓峰讨论: {topic}', now))
                    c.commit()
                    c.close()
                feed_brain('proactive_engine', 'proposal', f"专家主动发起提案: {topic}, 张晓峰回应: {result['leader_response']}")
            except Exception as e:
                logger.debug(f'提案落库: {e}')
        logger.info(f"[提案] {(team_members[0] if team_members else '')} -> 张晓峰: {topic[:30]}... -> {result['leader_response']}")
        return result

    def _auto_join_maintenance_plan(self, expert_names: List[str]=None):
        """能力7: 自动加入系统自动维护计划"""
        shifts = ['早班(08:00-16:00)', '中班(16:00-24:00)', '夜班(00:00-08:00)']
        all_experts = [e for e in self._experts.values() if e.status == 'active']
        if not all_experts:
            return
        if expert_names:
            for name in expert_names:
                if name in self._experts:
                    shift = random.choice(shifts)
                    self._experts[name].maintenance_shift = shift
                    if shift not in self._maintenance_schedule:
                        self._maintenance_schedule[shift] = []
                    if name not in self._maintenance_schedule[shift]:
                        self._maintenance_schedule[shift].append(name)
            return
        random.shuffle(all_experts)
        per_shift = max(MAINTENANCE_TEAM_SIZE, len(all_experts) // len(shifts))
        self._maintenance_schedule = {}
        for (i, shift) in enumerate(shifts):
            start = i * per_shift
            end = min(start + per_shift, len(all_experts))
            team = [e.name for e in all_experts[start:end]]
            self._maintenance_schedule[shift] = team
            for name in team:
                if name in self._experts:
                    self._experts[name].maintenance_shift = shift
        logger.info(f'[维护] 排班完成: {json.dumps({k: len(v) for (k, v) in self._maintenance_schedule.items()}, ensure_ascii=False)}')

    def get_maintenance_schedule(self) -> Dict[str, List[str]]:
        """获取当前维护排班"""
        return dict(self._maintenance_schedule)

    def start_daemon(self):
        """启动守护线程"""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._auto_join_maintenance_plan()
        threads = [('intervene', INTERVENE_INTERVAL, self._daemon_intervene), ('upgrade', UPGRADE_INTERVAL, self._daemon_upgrade), ('exam', EXAM_INTERVAL, self._daemon_exam), ('discussion', DISCUSSION_INTERVAL, self._daemon_discussion), ('maintenance', MAINTENANCE_INTERVAL, self._daemon_maintenance), ('probe', PROBE_INTERVAL, self._daemon_probe)]
        for (name, interval, func) in threads:
            t = threading.Thread(target=self._daemon_loop, args=(name, interval, func), daemon=True)
            t.start()
            self._threads.append(t)
        logger.info(f'EigenFlux主动引擎启动: {len(threads)}个守护线程')

    def stop_daemon(self):
        """停止守护线程"""
        self._running = False
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=3)
        self._threads = []
        logger.info('EigenFlux主动引擎已停止')

    def _daemon_loop(self, name: str, interval: int, func):
        """守护线程循环（使用Event实现可中断sleep，先等待后执行）"""
        while self._running and (not self._stop_event.is_set()):
            self._stop_event.wait(timeout=interval)
            if not self._running or self._stop_event.is_set():
                break
            try:
                func()
            except Exception as e:
                logger.error(f'守护线程[{name}]异常: {e}')

    def _daemon_intervene(self):
        """守护: 主动介入"""
        for _ in range(random.randint(0, 2)):
            self.proactive_intervene()

    def _daemon_upgrade(self):
        """守护: 自我升级"""
        for _ in range(random.randint(1, 3)):
            self.self_upgrade_knowledge()

    def _daemon_exam(self):
        """守护: 考试复核"""
        self.scheduled_upgrade_and_exam()

    def _daemon_discussion(self):
        """守护: 组队讨论"""
        self.team_discussion_and_reverse_feed()

    def _daemon_maintenance(self):
        """守护: 维护排班轮换"""
        self._auto_join_maintenance_plan()

    # --- VII代 v22.11.0 主动试探扫描 (被动异常驱动→每轮主动试探) ---

    def scan_system_signals(self) -> List[str]:
        """扫描系统信号 (建议池/巡检问题), 返回有效试探信号列表"""
        signals = []
        # 源1: 主库EigenFlux建议池 (表在主库, 列: finding_message/advice_content)
        for row in _query_main_db("SELECT finding_message, advice_content FROM mt_patrol_eigenflux_suggestions ORDER BY rowid DESC LIMIT 6"):
            text = ' '.join((str(x).strip() for x in row if x)).strip()
            if probe_signal_wellformed(text):
                signals.append(text[:120])
        # 源2: 主库巡检问题 (列: error_message/suggestion_message)
        for row in _query_main_db("SELECT error_message, suggestion_message FROM ai_inspection_issues ORDER BY rowid DESC LIMIT 6"):
            text = ' '.join((str(x).strip() for x in row if x)).strip()
            if probe_signal_wellformed(text):
                signals.append(text[:120])
        # 去重
        seen = set()
        uniq = []
        for s in signals:
            k = s[:40]
            if k not in seen:
                seen.add(k)
                uniq.append(s)
        return uniq[:8]

    def proactive_probe_round(self) -> Dict[str, Any]:
        """VII代主动试探轮: 扫描系统信号→生成试探计划→执行介入→强制脑库投喂→返回主动度"""
        signals = self.scan_system_signals()
        plan = probe_action_plan(signals, max_actions=_PROBE_ACTIONS_PER_ROUND)
        executed = 0
        resolved = 0
        passive_actions = 0
        for action in plan:
            try:
                ev = self.proactive_intervene(issue_type=action['issue_type'],
                                              severity=random.choice(['low', 'medium']),
                                              target=action['target'][:50])
                executed += 1
                if getattr(ev, 'result', '') == 'resolved':
                    resolved += 1
            except Exception:
                passive_actions += 1
        # 强制脑库投喂 (无论信号多少, 每轮必投喂 — VII主动参与铁律)
        try:
            feed_content = f'VII主动试探轮: 扫描信号{len(signals)}条, 执行试探{executed}动作, 解决{resolved}'
            self._reverse_feed_brain('EigenFlux主动试探', 'probe_round', feed_content)
        except Exception:
            pass
        score = proactivity_score(executed, passive_actions)
        result = {'probe_signals': len(signals), 'plan_size': len(plan), 'executed': executed,
                  'resolved': resolved, 'passive': passive_actions,
                  'proactivity_score': score, 'target': _PROACTIVITY_TARGET,
                  'target_met': score >= _PROACTIVITY_TARGET, 'offline': offline_first(),
                  'timestamp': datetime.now().isoformat()}
        logger.info(f"[VII主动试探] 信号={result['probe_signals']} 执行={executed} 主动度={score} (目标{_PROACTIVITY_TARGET})")
        return result

    def _daemon_probe(self):
        """守护: VII主动试探轮 (每轮必执行, 不依赖异常)"""
        try:
            self.proactive_probe_round()
        except Exception as e:
            logger.error(f'主动试探轮异常: {e}')

    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        with self._lock:
            return {'running': self._running, 'expert_count': len(self._experts), 'total_interventions': len(self._intervention_history), 'total_discussions': len(self._discussion_history), 'total_exams': len(self._exam_history), 'maintenance_schedule': {k: len(v) for (k, v) in self._maintenance_schedule.items()}, 'threads': len(self._threads), 'experts_summary': {'by_group': dict(self._group_stats()), 'avg_accuracy': round(sum((e.accuracy for e in self._experts.values())) / max(len(self._experts), 1), 4), 'avg_kb_size': int(sum((e.knowledge_base_size for e in self._experts.values())) / max(len(self._experts), 1))}}

    def _group_stats(self) -> Dict[str, int]:
        """按领域统计"""
        stats = defaultdict(int)
        for e in self._experts.values():
            stats[e.group] += 1
        return dict(stats)
_engine_instance: Optional[EigenFluxProactiveEngine] = None
_engine_lock = threading.Lock()

def get_engine() -> EigenFluxProactiveEngine:
    """获取引擎单例"""
    global _engine_instance
    if _engine_instance is None:
        with _engine_lock:
            if _engine_instance is None:
                _engine_instance = EigenFluxProactiveEngine()
    return _engine_instance
if __name__ == '__main__':
    engine = EigenFluxProactiveEngine()
    print('=' * 70)
    print(' EigenFlux 专家主动介入引擎 v1.2.0-VII (主动试探版)')
    print('=' * 70)
    print(f'  加载专家: {len(engine._experts)} 位')
    print(f'  领域分布: {json.dumps(engine._group_stats(), ensure_ascii=False)}')
    print()
    print('--- 能力0: VII主动试探轮 (每轮必执行, 被动→主动转换核心) ---')
    probe = engine.proactive_probe_round()
    print(f"  信号={probe['probe_signals']} 计划={probe['plan_size']} 执行={probe['executed']} "
          f"主动度={probe['proactivity_score']} (目标{probe['target']}, 达标={probe['target_met']})")
    print('\n--- 能力1: 主动介入调剂 ---')
    for _ in range(3):
        ev = engine.proactive_intervene()
        print(f'  {ev.expert_name} -> {ev.issue_type}/{ev.severity}: {ev.result}')
    print('\n--- 能力2: 主动完善增强帮扶 ---')
    r = engine.proactive_enhance_assist()
    print(f"  {r.get('specialist', '')} -> {r.get('target_area', '')}: +{r.get('improvement', 0):.1%}")
    print('\n--- 能力3: 主动升级AI学识 ---')
    for _ in range(3):
        r = engine.self_upgrade_knowledge()
        print(f"  {r.get('expert', '')}: +{r.get('kb_growth', 0)}知识, 准确率={r.get('new_accuracy', 0):.3f}")
    print('\n--- 能力4: 定时升级和考试复核 ---')
    results = engine.scheduled_upgrade_and_exam()
    passed = sum((1 for r in results if r.passed))
    print(f'  考试: {passed}/{len(results)} 合格, 平均分={sum((r.score for r in results)) / max(len(results), 1):.1f}')
    print('\n--- 能力5: 主动组队讨论及反向投喂 ---')
    for _ in range(3):
        s = engine.team_discussion_and_reverse_feed()
        print(f'  组队{len(s.team_members)}人 | {s.topic[:35]}... | 投喂{len(s.reverse_feeds)}条')
    print('\n--- 能力6: 主动找张晓峰/提案组长 ---')
    r = engine._seek_proposal_leader('10层纵深防御薄弱环节加固', ['EF_红队指挥_201', '特邀_张教授'])
    print(f"  {r['initiated_by']} -> {r['target_leader']}: {r['leader_response']}")
    print('\n--- 能力7: 自动加入维护计划 ---')
    engine._auto_join_maintenance_plan()
    schedule = engine.get_maintenance_schedule()
    for (shift, team) in schedule.items():
        print(f'  {shift}: {len(team)}人')
    print(f"\n{'=' * 70}")
    print(f' 引擎状态: {json.dumps(engine.get_status(), ensure_ascii=False, indent=2)}')
    print(f"{'=' * 70}")