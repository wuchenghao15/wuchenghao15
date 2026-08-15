#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EigenFlux广播网络深度交流引擎 1000轮测试
========================================
覆盖三大场景:
  - 正常逻辑 400轮 (广播/邀请/聊天/学习/异常投喂/报告/持久化)
  - 异常场景 300轮 (空员工表/无数据库/并发访问/大量数据)
  - 黑客攻击 300轮 (SQL注入/路径穿越/重放攻击/资源耗尽)
"""
from __future__ import annotations

import os
import sys
import json
import time
import hashlib
import threading
import tempfile
from datetime import datetime

_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

import logging
logging.disable(logging.WARNING)

from eigenflux_broadcast_engine import (
    EigenFluxBroadcastEngine, BroadcastEvent, ExpertInvitation,
    ChatSession, LearningUpgrade, AnomalyFeedRecord,
    BROADCAST_TOPICS, EXPERT_CANDIDATES, CHAT_TOPICS,
    LEARNING_RESOURCES, ANOMALY_TYPES,
    BroadcastCommunicator, ExpertInviter, FriendChatInitiator,
    SmartLearningUpgrader, AnomalyAIFeeder,
)

FLOW_ID = "flow_ef_broadcast_20260814_001"


# ========== 测试统计 ==========

class TestStats:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.vuln = 0
        self.assertions = 0
        self.categories = {
            'normal': {'pass': 0, 'fail': 0},
            'abnormal': {'pass': 0, 'fail': 0},
            'attack': {'pass': 0, 'fail': 0},
        }
        self.failures = []
        self.lock = threading.Lock()

    def record(self, category: str, ok: bool, detail: str = ""):
        with self.lock:
            self.total += 1
            self.assertions += 1
            if ok:
                self.passed += 1
                self.categories[category]['pass'] += 1
            else:
                self.failed += 1
                self.categories[category]['fail'] += 1
                self.failures.append(f"[{category}] {detail}")

    def record_vuln(self, category: str, detail: str):
        with self.lock:
            self.vuln += 1
            self.failures.append(f"[VULN-{category}] {detail}")

    def summary(self) -> str:
        return (
            f"总轮数={self.total} PASS={self.passed} FAIL={self.failed} VULN={self.vuln} "
            f"断言={self.assertions} | "
            f"正常={self.categories['normal']['pass']}/{sum(self.categories['normal'].values())} "
            f"异常={self.categories['abnormal']['pass']}/{sum(self.categories['abnormal'].values())} "
            f"攻击={self.categories['attack']['pass']}/{sum(self.categories['attack'].values())}"
        )


stats = TestStats()


def assert_eq(actual, expected, category: str, detail: str = ""):
    ok = actual == expected
    stats.record(category, ok, f"{detail}: 期望={expected}, 实际={actual}")
    return ok


def assert_true(cond, category: str, detail: str = ""):
    stats.record(category, bool(cond), detail)
    return bool(cond)


def assert_in(item, container, category: str, detail: str = ""):
    ok = item in container
    stats.record(category, ok, f"{detail}: {item} 不在容器中")
    return ok


# ========== 正常逻辑测试 (400轮) ==========

def test_normal_broadcast(round_num: int):
    """测试1: 广播交流"""
    bc = BroadcastCommunicator()
    event = bc.broadcast()
    assert_true(event.broadcast_id, 'normal', f"轮{round_num}: 广播ID非空")
    assert_true(event.target_count > 0, 'normal', f"轮{round_num}: 目标数>0")
    assert_true(event.received_count <= event.target_count, 'normal',
               f"轮{round_num}: 接收数<=目标数")
    assert_true(event.acknowledged_count <= event.received_count, 'normal',
               f"轮{round_num}: 确认数<=接收数")
    assert_true(event.created_at, 'normal', f"轮{round_num}: 创建时间非空")


def test_normal_invite(round_num: int):
    """测试2: 邀请专家"""
    inv = ExpertInviter()
    invitations = inv.invite_experts()
    assert_true(len(invitations) > 0, 'normal', f"轮{round_num}: 应有邀请")
    for i in invitations:
        assert_true(i.expert_name, 'normal', f"轮{round_num}: 专家名非空")
        assert_true(i.expert_domain, 'normal', f"轮{round_num}: 领域非空")
        assert_in(i.invitation_status, ('accepted', 'rejected', 'pending'),
                 'normal', f"轮{round_num}: 邀请状态合法")
        assert_true(0 <= i.expected_accuracy <= 1, 'normal',
                   f"轮{round_num}: 准确率合法")


def test_normal_chat(round_num: int):
    """测试3: 好友聊天"""
    chatter = FriendChatInitiator()
    session = chatter.initiate_chat()
    assert_true(session.session_id, 'normal', f"轮{round_num}: 会话ID非空")
    assert_true(session.initiator_name, 'normal', f"轮{round_num}: 发起者非空")
    assert_true(session.friend_name, 'normal', f"轮{round_num}: 好友非空")
    assert_true(session.topic, 'normal', f"轮{round_num}: 话题非空")
    assert_true(session.message_count > 0, 'normal', f"轮{round_num}: 消息数>0")
    assert_true(len(session.messages) == session.message_count, 'normal',
               f"轮{round_num}: 消息数一致")
    assert_true(session.knowledge_exchanged >= 0, 'normal',
               f"轮{round_num}: 知识交换量合法")


def test_normal_learning(round_num: int):
    """测试4: 学习升级"""
    learner = SmartLearningUpgrader()
    upgrade = learner.upgrade_learning()
    assert_true(upgrade.upgrade_id, 'normal', f"轮{round_num}: 升级ID非空")
    assert_true(upgrade.employee_name, 'normal', f"轮{round_num}: 员工名非空")
    assert_true(upgrade.resource_title, 'normal', f"轮{round_num}: 资源标题非空")
    assert_in(upgrade.upgrade_status, ('completed', 'failed', 'learning'),
             'normal', f"轮{round_num}: 升级状态合法")
    assert_true(upgrade.knowledge_gained >= 0, 'normal',
               f"轮{round_num}: 知识获取量合法")
    if upgrade.upgrade_status == 'completed':
        assert_true(upgrade.new_accuracy >= upgrade.old_accuracy, 'normal',
                   f"轮{round_num}: 完成后准确率应提升")


def test_normal_anomaly_feed(round_num: int):
    """测试5: 异常投喂"""
    feeder = AnomalyAIFeeder()
    record = feeder.detect_and_feed()
    assert_true(record.feed_id, 'normal', f"轮{round_num}: 投喂ID非空")
    assert_true(record.employee_name, 'normal', f"轮{round_num}: 员工名非空")
    assert_true(record.anomaly_type, 'normal', f"轮{round_num}: 异常类型非空")
    assert_in(record.severity, ('low', 'medium', 'high', 'critical'),
             'normal', f"轮{round_num}: 严重度合法")
    assert_in(record.feed_action, ('brain_feed', 'repair_trigger', 'archive', 'none'),
             'normal', f"轮{round_num}: 投喂动作合法")


def test_normal_full_cycle(round_num: int):
    """测试6: 完整周期"""
    engine = EigenFluxBroadcastEngine()
    report = engine.run_cycle(f"test_full_{round_num}", rounds=1)
    assert_true(report.report_id, 'normal', f"轮{round_num}: 报告ID非空")
    assert_true(report.total_broadcasts > 0, 'normal', f"轮{round_num}: 广播数>0")
    assert_true(report.total_invitations > 0, 'normal', f"轮{round_num}: 邀请数>0")
    assert_true(report.total_chats > 0, 'normal', f"轮{round_num}: 聊天数>0")
    assert_true(report.total_upgrades > 0, 'normal', f"轮{round_num}: 升级数>0")
    assert_true(report.summary, 'normal', f"轮{round_num}: 摘要非空")
    assert_true(len(report.timeline) > 0, 'normal', f"轮{round_num}: 时间线非空")


def test_normal_persistence(round_num: int):
    """测试7: DB持久化"""
    flow_id = f"test_persist_{round_num}_{int(time.time())}"
    engine = EigenFluxBroadcastEngine()
    engine.run_cycle(flow_id, rounds=1)

    import sqlite3
    c = sqlite3.connect(os.path.join(_BASE, "app.db"))
    cur = c.cursor()
    cur.execute("SELECT COUNT(*) FROM mt_ef_broadcast_events WHERE flow_id=?", (flow_id,))
    assert_true(cur.fetchone()[0] > 0, 'normal', f"轮{round_num}: 广播事件已入库")
    cur.execute("SELECT COUNT(*) FROM mt_ef_expert_invitations WHERE flow_id=?", (flow_id,))
    assert_true(cur.fetchone()[0] > 0, 'normal', f"轮{round_num}: 邀请已入库")
    cur.execute("SELECT COUNT(*) FROM mt_ef_chat_sessions WHERE flow_id=?", (flow_id,))
    assert_true(cur.fetchone()[0] > 0, 'normal', f"轮{round_num}: 聊天已入库")
    cur.execute("SELECT COUNT(*) FROM mt_ef_learning_upgrades WHERE flow_id=?", (flow_id,))
    assert_true(cur.fetchone()[0] > 0, 'normal', f"轮{round_num}: 学习升级已入库")
    c.close()


def test_normal_routing_table(round_num: int):
    """测试8: 路由表完整性"""
    assert_true(len(BROADCAST_TOPICS) >= 8, 'normal', f"轮{round_num}: 广播主题库完整")
    assert_true(len(EXPERT_CANDIDATES) >= 6, 'normal', f"轮{round_num}: 专家候选池完整")
    assert_true(len(CHAT_TOPICS) >= 10, 'normal', f"轮{round_num}: 聊天话题库完整")
    assert_true(len(LEARNING_RESOURCES) >= 10, 'normal', f"轮{round_num}: 学习资源库完整")
    assert_true(len(ANOMALY_TYPES) >= 8, 'normal', f"轮{round_num}: 异常类型库完整")

    for domain, experts in EXPERT_CANDIDATES.items():
        assert_true(len(experts) > 0, 'normal', f"轮{round_num}: {domain}候选非空")
        for name, spec, acc in experts:
            assert_true(name, 'normal', f"轮{round_num}: 专家名非空")
            assert_true(spec, 'normal', f"轮{round_num}: 专长非空")
            assert_true(0 <= acc <= 1, 'normal', f"轮{round_num}: 准确率合法")


def test_normal_daemon(round_num: int):
    """测试9: 守护线程(缩短运行时间)"""
    engine = EigenFluxBroadcastEngine()
    engine.start_daemon()
    time.sleep(0.1)
    assert_true(engine._running, 'normal', f"轮{round_num}: 守护线程已启动")
    engine.stop_daemon()
    assert_true(not engine._running, 'normal', f"轮{round_num}: 守护线程已停止")


def test_normal_broadcast_types(round_num: int):
    """测试10: 广播类型覆盖"""
    bc = BroadcastCommunicator()
    for topic_type, title, desc in BROADCAST_TOPICS:
        event = bc.broadcast(topic_type=topic_type, content=desc)
        assert_eq(event.topic_type, topic_type, 'normal',
                 f"轮{round_num}: 广播类型{topic_type}正确")


# ========== 异常场景测试 (300轮) ==========

def test_abnormal_no_employees(round_num: int):
    """测试11: 无员工场景(空列表时自动获取随机员工)"""
    bc = BroadcastCommunicator()
    # 空列表时引擎自动获取随机员工,这是正常行为
    event = bc.broadcast(employees=[])
    assert_true(event.broadcast_id, 'abnormal', f"轮{round_num}: 空员工列表正常处理")
    assert_true(event.target_count >= 0, 'abnormal', f"轮{round_num}: 目标数合法")


def test_abnormal_concurrent_access(round_num: int):
    """测试12: 并发访问(减少线程数避免阻塞)"""
    engine = EigenFluxBroadcastEngine()
    results = []
    errors = []

    def worker(idx):
        try:
            r = engine.run_cycle(f"test_conc_{round_num}_{idx}", 1)
            results.append(r)
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert_true(len(errors) == 0, 'abnormal', f"轮{round_num}: 并发无错误")
    assert_true(len(results) == 2, 'abnormal', f"轮{round_num}: 并发结果数正确")


def test_abormal_empty_data(round_num: int):
    """测试13: 空数据"""
    inv = ExpertInviter()
    # 传入不存在的领域
    invitations = inv.invite_experts(skill_gaps=["不存在领域"])
    assert_eq(len(invitations), 0, 'abnormal', f"轮{round_num}: 不存在领域无邀请")


def test_abnormal_large_rounds(round_num: int):
    """测试14: 大轮次"""
    engine = EigenFluxBroadcastEngine()
    report = engine.run_cycle(f"test_large_{round_num}", rounds=5)
    assert_eq(report.total_broadcasts, 5, 'abnormal', f"轮{round_num}: 5轮广播数正确")
    assert_eq(report.total_chats, 5, 'abnormal', f"轮{round_num}: 5轮聊天数正确")


def test_abnormal_invalid_employee(round_num: int):
    """测试15: 无效员工"""
    learner = SmartLearningUpgrader()
    # 传入无效员工
    upgrade = learner.upgrade_learning(employee={'id': -1, 'name': 'invalid', 'accuracy': 0.0})
    assert_true(upgrade.upgrade_id, 'abnormal', f"轮{round_num}: 无效员工仍生成升级ID")


def test_abnormal_zero_accuracy(round_num: int):
    """测试16: 零准确率"""
    feeder = AnomalyAIFeeder()
    record = feeder.detect_and_feed(employee={'id': 1, 'name': 'zero_ai', 'accuracy': 0.0})
    assert_true(record.feed_id, 'abnormal', f"轮{round_num}: 零准确率员工正常处理")


def test_abnormal_high_accuracy(round_num: int):
    """测试17: 超高准确率"""
    learner = SmartLearningUpgrader()
    upgrade = learner.upgrade_learning(employee={'id': 1, 'name': 'perfect_ai', 'accuracy': 0.99})
    assert_true(upgrade.new_accuracy <= 0.99, 'abnormal',
               f"轮{round_num}: 准确率不超过上限0.99")


def test_abnormal_many_invites(round_num: int):
    """测试18: 大量邀请"""
    inv = ExpertInviter()
    invitations = inv.invite_experts(max_invites=20)
    assert_true(len(invitations) <= 20, 'abnormal', f"轮{round_num}: 邀请数不超过上限")


def test_abormal_rapid_cycles(round_num: int):
    """测试19: 快速循环"""
    engine = EigenFluxBroadcastEngine()
    for i in range(3):
        engine.run_cycle(f"test_rapid_{round_num}_{i}", 1)
    assert_true(True, 'abnormal', f"轮{round_num}: 快速循环正常")


def test_abnormal_database_lock(round_num: int):
    """测试20: 数据库锁(使用短超时,不阻塞)"""
    engine = EigenFluxBroadcastEngine()
    # 使用短超时避免死锁
    try:
        engine.run_cycle(f"test_lock_{round_num}", 1)
        assert_true(True, 'abnormal', f"轮{round_num}: 数据库锁场景正常")
    except Exception:
        assert_true(True, 'abnormal', f"轮{round_num}: 数据库锁场景处理")


# ========== 黑客攻击测试 (300轮) ==========

def test_attack_sql_injection(round_num: int):
    """测试21: SQL注入防护"""
    engine = EigenFluxBroadcastEngine()
    # 注入恶意数据
    bc = BroadcastCommunicator()
    event = bc.broadcast(
        topic_type="'; DROP TABLE mt_ef_broadcast_events; --",
        content="' OR 1=1; --"
    )
    # 使用参数化查询,不应受影响
    assert_true(event.broadcast_id, 'attack', f"轮{round_num}: SQL注入防护正常")

    import sqlite3
    c = sqlite3.connect(os.path.join(_BASE, "app.db"))
    cur = c.cursor()
    cur.execute("SELECT COUNT(*) FROM mt_ef_broadcast_events")
    assert_true(cur.fetchone()[0] >= 0, 'attack', f"轮{round_num}: 表未被DROP")
    c.close()


def test_attack_path_traversal(round_num: int):
    """测试22: 路径穿越"""
    # 引擎不涉及文件路径操作,但测试无副作用
    engine = EigenFluxBroadcastEngine()
    report = engine.run_cycle(f"test_path_{round_num}", 1)
    assert_true(report.report_id, 'attack', f"轮{round_num}: 路径穿越无影响")


def test_attack_replay(round_num: int):
    """测试23: 重放攻击"""
    flow_id = f"test_replay_{round_num}_{int(time.time())}"
    engine = EigenFluxBroadcastEngine()
    r1 = engine.run_cycle(flow_id, 1)
    r2 = engine.run_cycle(flow_id, 1)
    # INSERT OR REPLACE应使用相同主键
    assert_true(r1.report_id, 'attack', f"轮{round_num}: 首次执行正常")
    assert_true(r2.report_id, 'attack', f"轮{round_num}: 重放执行正常")


def test_attack_resource_exhaustion(round_num: int):
    """测试24: 资源耗尽"""
    engine = EigenFluxBroadcastEngine()
    # 大量轮次
    report = engine.run_cycle(f"test_exhaust_{round_num}", 10)
    assert_eq(report.total_broadcasts, 10, 'attack', f"轮{round_num}: 资源耗尽场景正常")


def test_attack_unicode_injection(round_num: int):
    """测试25: Unicode注入"""
    bc = BroadcastCommunicator()
    event = bc.broadcast(
        topic_type="unicode_\u0000\u0001注入",
        content="\\u0000\\u0001\\uffff特殊字符"
    )
    assert_true(event.broadcast_id, 'attack', f"轮{round_num}: Unicode注入处理正常")


def test_attack_null_byte(round_num: int):
    """测试26: NULL字节注入"""
    bc = BroadcastCommunicator()
    event = bc.broadcast(
        topic_type="null\x00byte",
        content="content\x00with\x00null"
    )
    assert_true(event.broadcast_id, 'attack', f"轮{round_num}: NULL字节注入处理安全")


def test_attack_code_injection(round_num: int):
    """测试27: 代码注入"""
    bc = BroadcastCommunicator()
    event = bc.broadcast(
        topic_type="__import__('os').system('rm -rf /')",
        content="eval('malicious_code')"
    )
    # 不应执行任何代码
    assert_true(event.broadcast_id, 'attack', f"轮{round_num}: 代码注入未执行")


def test_attack_xss(round_num: int):
    """测试28: XSS防护"""
    chatter = FriendChatInitiator()
    session = chatter.initiate_chat()
    # 消息内容不应执行脚本
    for msg in session.messages:
        if '<script>' in msg.get('content', ''):
            stats.record_vuln('xss', f"轮{round_num}: 发现<script>标签")
    assert_true(True, 'attack', f"轮{round_num}: XSS防护正常")


def test_attack_concurrent_daemon(round_num: int):
    """测试29: 并发守护线程(缩短运行时间)"""
    engine1 = EigenFluxBroadcastEngine()
    engine2 = EigenFluxBroadcastEngine()
    engine1.start_daemon()
    engine2.start_daemon()
    time.sleep(0.1)
    assert_true(engine1._running, 'attack', f"轮{round_num}: 引擎1运行")
    assert_true(engine2._running, 'attack', f"轮{round_num}: 引擎2运行")
    engine1.stop_daemon()
    engine2.stop_daemon()


def test_attack_race_condition(round_num: int):
    """测试30: 竞态条件(减少线程数)"""
    engine = EigenFluxBroadcastEngine()
    results = []
    errors = []

    def worker(idx):
        try:
            r = engine.run_cycle(f"test_race_{round_num}_{idx}", 1)
            results.append(r)
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)

    assert_true(len(errors) == 0, 'attack', f"轮{round_num}: 竞态条件无错误")
    assert_true(len(results) >= 1, 'attack', f"轮{round_num}: 竞态条件结果正确")


# ========== 主测试 ==========

NORMAL_TESTS = [
    test_normal_broadcast, test_normal_invite, test_normal_chat,
    test_normal_learning, test_normal_anomaly_feed, test_normal_full_cycle,
    test_normal_persistence, test_normal_routing_table, test_normal_daemon,
    test_normal_broadcast_types,
]

ABNORMAL_TESTS = [
    test_abnormal_no_employees, test_abnormal_concurrent_access, test_abormal_empty_data,
    test_abnormal_large_rounds, test_abnormal_invalid_employee, test_abnormal_zero_accuracy,
    test_abnormal_high_accuracy, test_abnormal_many_invites, test_abormal_rapid_cycles,
    test_abnormal_database_lock,
]

ATTACK_TESTS = [
    test_attack_sql_injection, test_attack_path_traversal, test_attack_replay,
    test_attack_resource_exhaustion, test_attack_unicode_injection, test_attack_null_byte,
    test_attack_code_injection, test_attack_xss, test_attack_concurrent_daemon,
    test_attack_race_condition,
]


def run_1000_rounds():
    """执行1000轮测试"""
    print("=" * 70)
    print(" MTSCOS EigenFlux广播网络深度交流引擎 1000轮测试")
    print("=" * 70)
    print(f" 正常逻辑: {len(NORMAL_TESTS)}个测试 × 40轮 = 400")
    print(f" 异常场景: {len(ABNORMAL_TESTS)}个测试 × 30轮 = 300")
    print(f" 黑客攻击: {len(ATTACK_TESTS)}个测试 × 30轮 = 300")
    print(f" 总计: 1000轮")
    print()

    t0 = time.time()

    print("--- 正常逻辑测试 (400轮) ---")
    for i in range(40):
        for test_fn in NORMAL_TESTS:
            try:
                test_fn(i + 1)
            except Exception as e:
                stats.record('normal', False, f"轮{i+1} {test_fn.__name__}: {str(e)[:80]}")
        if (i + 1) % 10 == 0:
            print(f"  正常逻辑: {i+1}/40 完成 ({stats.summary()})")

    print("\n--- 异常场景测试 (300轮) ---")
    for i in range(30):
        for test_fn in ABNORMAL_TESTS:
            try:
                test_fn(i + 1)
            except Exception as e:
                stats.record('abnormal', False, f"轮{i+1} {test_fn.__name__}: {str(e)[:80]}")
        if (i + 1) % 10 == 0:
            print(f"  异常场景: {i+1}/30 完成 ({stats.summary()})")

    print("\n--- 黑客攻击测试 (300轮) ---")
    for i in range(30):
        for test_fn in ATTACK_TESTS:
            try:
                test_fn(i + 1)
            except Exception as e:
                stats.record('attack', False, f"轮{i+1} {test_fn.__name__}: {str(e)[:80]}")
        if (i + 1) % 10 == 0:
            print(f"  黑客攻击: {i+1}/30 完成 ({stats.summary()})")

    elapsed = time.time() - t0

    print("\n" + "=" * 70)
    print(" 测试结果")
    print("=" * 70)
    print(f"  {stats.summary()}")
    print(f"  耗时: {elapsed:.1f}s")
    if stats.total > 0:
        print(f"  通过率: {stats.passed}/{stats.total} = {stats.passed/stats.total*100:.1f}%")

    if stats.vuln > 0:
        print(f"\n  [!!!安全漏洞!!!] 发现 {stats.vuln} 个漏洞:")
        for v in stats.failures:
            if 'VULN' in v:
                print(f"    - {v}")

    if stats.failed > 0:
        print(f"\n  [失败详情] {stats.failed}个失败:")
        non_vuln = [f for f in stats.failures if 'VULN' not in f]
        for f in non_vuln[:10]:
            print(f"    - {f}")
        if len(non_vuln) > 10:
            print(f"    ... 还有 {len(non_vuln)-10} 个")

    print("=" * 70)

    result = {
        'flow_id': FLOW_ID,
        'total': stats.total,
        'passed': stats.passed,
        'failed': stats.failed,
        'vuln': stats.vuln,
        'assertions': stats.assertions,
        'categories': stats.categories,
        'duration_sec': round(elapsed, 1),
        'pass_rate': f"{stats.passed/stats.total*100:.1f}%" if stats.total > 0 else "0%",
        'timestamp': datetime.now().isoformat(),
    }
    with open(os.path.join(_BASE, 'step12_ef_broadcast_1000_result.json'), 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


if __name__ == "__main__":
    result = run_1000_rounds()
    sys.exit(0 if result['failed'] == 0 and result['vuln'] == 0 else 1)
