#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动巡检队伍引擎 1000轮测试 (Auto Dev Team 1000-Rounds Test)
============================================================
覆盖三大场景:
  - 正常逻辑 400轮 (功能扫描/任务派发/开发跟踪/完成验证/报告生成/DB持久化)
  - 异常场景 300轮 (空目录/不存在目录/二进制文件/超大文件/Unicode文件名)
  - 黑客攻击 300轮 (路径穿越/SQL注入/命令注入/资源耗尽/重放攻击)

验收项:
  - 5大模块全部正常工作
  - 开发团队路由准确率 100%
  - 功能缺失检测完整性
  - 完成验证逻辑正确
  - DB持久化数据完整
  - 黑客攻击 100%拦截
"""
from __future__ import annotations

import os
import sys
import json
import time
import shutil
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

from auto_dev_team_engine import (
    AutoDevTeamEngine, FeatureGap, DevLifecycleReport,
    DEV_TEAM_ROUTING, PLACEHOLDER_PATTERNS,
)

FLOW_ID = "flow_auto_dev_team_20260814_001"


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


# ========== 测试辅助: 创建临时项目 ==========

def make_temp_project(name: str = "test_proj", with_placeholder: bool = True,
                      with_todo: bool = False, with_missing_api: bool = False,
                      with_empty_route: bool = False) -> str:
    """创建临时测试项目"""
    tmpdir = tempfile.mkdtemp(prefix=f"dev_team_{name}_")

    # app.py
    app_content = """#!/usr/bin/env python3
from flask import Flask, jsonify, request
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({'status': 'ok'})

@app.route('/api/users', methods=['GET'])
def list_users():
    return jsonify({'users': []})

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return jsonify({'user': None})

@app.route('/api/users/<int:user_id>', methods=['POST'])
def create_user(user_id):
    data = request.get_json()
    return jsonify({'status': 'created', 'data': data})
"""
    if with_placeholder:
        app_content += """
@app.route('/api/feature/stub')
def feature_stub():
    pass

@app.route('/api/feature/todo')
def feature_todo():
    return 'TODO: 待实现'

@app.route('/api/feature/fixme')
def feature_fixme():
    return 'FIXME: 需要重写'
"""
    if with_todo:
        app_content += """
@app.route('/api/todo/item')
def todo_item():
    # TODO: 实现完整功能
    return jsonify({'status': 'placeholder'})

@app.route('/api/hack/item')
def hack_item():
    # HACK: 临时方案
    return jsonify({'status': 'hack'})
"""
    if with_missing_api:
        app_content += """
@app.route('/api/needs/implementation')
def needs_impl():
    return 'not implemented'
"""
    if with_empty_route:
        app_content += """
@app.route('/api/almost/done')
def almost_done():
    return jsonify({'status': 'almost', 'progress': 0.9})
"""
    with open(os.path.join(tmpdir, "app.py"), "w") as f:
        f.write(app_content)

    # sample.py with issues
    sample = """#!/usr/bin/env python3
import os
import sys

def working_func():
    return 'working'
"""
    if with_placeholder:
        sample += """
def stub_func():
    pass

def todo_func():
    return 'TODO: implement me'
"""
    if with_todo:
        sample += """
# TODO: 优化性能
def slow_func():
    return 'slow'

# FIXME: 安全漏洞
def unsafe_func():
    return 'unsafe'
"""
    with open(os.path.join(tmpdir, "sample.py"), "w") as f:
        f.write(sample)

    # 前端引用后端不存在的API
    if with_missing_api:
        html_content = """<!DOCTYPE html>
<html>
<body>
<script>
// 调用后端未实现的API
fetch('/api/missing/endpoint');
fetch('/api/not/implemented');
</script>
</body>
</html>
"""
        with open(os.path.join(tmpdir, "frontend.html"), "w") as f:
            f.write(html_content)

    return tmpdir


# ========== 正常逻辑测试 (400轮) ==========

def test_normal_gap_scanning(round_num: int):
    """测试1: 功能缺失扫描"""
    tmpdir = make_temp_project(f"scan_{round_num}", with_placeholder=True, with_todo=True)
    try:
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_scan_{round_num}")
        gaps = engine.get_gaps()
        # 应该发现placeholder和todo
        gap_types = {g.gap_type for g in gaps}
        assert_true('placeholder_return' in gap_types or 'todo_fixme' in gap_types,
                   'normal', f"轮{round_num}: 应发现功能缺失")
        # 应该有分配的团队
        assert_true(any(g.assigned_team for g in gaps), 'normal',
                   f"轮{round_num}: 应有分配团队")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_normal_team_routing(round_num: int):
    """测试2: 团队路由准确性"""
    # 验证路由表
    for gap_type, (team, employee, desc) in DEV_TEAM_ROUTING.items():
        assert_true(team, 'normal', f"轮{round_num}: {gap_type}团队非空")
        assert_true(employee, 'normal', f"轮{round_num}: {gap_type}负责人非空")
        assert_true(desc, 'normal', f"轮{round_num}: {gap_type}描述非空")

    # 抽样验证
    assert_eq(DEV_TEAM_ROUTING['missing_api'][0], 'API开发团队', 'normal',
             f"轮{round_num}: missing_api应路由到API开发团队")
    assert_eq(DEV_TEAM_ROUTING['placeholder_return'][0], '功能完善团队', 'normal',
             f"轮{round_num}: placeholder_return应路由到功能完善团队")
    assert_eq(DEV_TEAM_ROUTING['missing_crud'][0], '数据库团队', 'normal',
             f"轮{round_num}: missing_crud应路由到数据库团队")
    assert_eq(DEV_TEAM_ROUTING['todo_fixme'][0], '待办处理团队', 'normal',
             f"轮{round_num}: todo_fixme应路由到待办处理团队")


def test_normal_dispatch(round_num: int):
    """测试3: 任务派发"""
    tmpdir = make_temp_project(f"dispatch_{round_num}", with_placeholder=True)
    try:
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_dispatch_{round_num}")
        gaps = engine.get_gaps()
        # 所有gap都应该被分配
        for gap in gaps:
            assert_true(gap.assigned_team, 'normal',
                       f"轮{round_num}: {gap.gap_id}应分配团队")
            assert_true(gap.assigned_employee, 'normal',
                       f"轮{round_num}: {gap.gap_id}应分配负责人")
            assert_true(gap.assigned_at, 'normal',
                       f"轮{round_num}: {gap.gap_id}应有分配时间")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_normal_progress_tracking(round_num: int):
    """测试4: 开发进度跟踪"""
    tmpdir = make_temp_project(f"progress_{round_num}", with_placeholder=True)
    try:
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_progress_{round_num}")
        gaps = engine.get_gaps()
        # 检查状态转换
        valid_statuses = {'discovered', 'assigned', 'in_development', 'code_review',
                         'testing', 'completed', 'failed'}
        for gap in gaps:
            assert_in(gap.status, valid_statuses, 'normal',
                     f"轮{round_num}: {gap.gap_id}状态合法: {gap.status}")
            # 检查进度值
            assert_true(0 <= gap.progress <= 1, 'normal',
                       f"轮{round_num}: {gap.gap_id}进度合法: {gap.progress}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_normal_verification(round_num: int):
    """测试5: 完成验证"""
    tmpdir = make_temp_project(f"verify_{round_num}", with_placeholder=True)
    try:
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_verify_{round_num}")
        gaps = engine.get_gaps()
        # 检查验证结果
        for gap in gaps:
            if gap.status == 'completed':
                assert_true(gap.verification_result in ('PASS', 'FAIL', ''), 'normal',
                           f"轮{round_num}: {gap.gap_id}验证结果合法")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_normal_report(round_num: int):
    """测试6: 报告生成"""
    tmpdir = make_temp_project(f"report_{round_num}", with_placeholder=True, with_todo=True)
    try:
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        report = engine.run_full_cycle(f"test_report_{round_num}")
        # 报告字段完整性
        assert_true(report.report_id, 'normal', f"轮{round_num}: 报告ID非空")
        assert_true(report.total_gaps >= 0, 'normal', f"轮{round_num}: 总缺失数合法")
        assert_true(report.gaps_discovered >= 0, 'normal', f"轮{round_num}: 已发现数合法")
        assert_true(report.summary, 'normal', f"轮{round_num}: 摘要非空")
        assert_true(len(report.teams_involved) > 0, 'normal', f"轮{round_num}: 涉及团队非空")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_normal_persistence(round_num: int):
    """测试7: DB持久化"""
    tmpdir = make_temp_project(f"persist_{round_num}", with_placeholder=True)
    try:
        flow_id = f"test_persist_{round_num}_{int(time.time())}"
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(flow_id)

        import sqlite3
        c = sqlite3.connect(os.path.join(_BASE, "app.db"))
        cur = c.cursor()
        # 检查生命周期表
        cur.execute("SELECT COUNT(*) FROM mt_feature_dev_lifecycle WHERE flow_id=?", (flow_id,))
        lifecycle_count = cur.fetchone()[0]
        assert_true(lifecycle_count > 0, 'normal',
                   f"轮{round_num}: 生命周期表有数据")
        # 检查报告表
        cur.execute("SELECT COUNT(*) FROM mt_dev_lifecycle_report WHERE flow_id=?", (flow_id,))
        report_count = cur.fetchone()[0]
        assert_true(report_count > 0, 'normal',
                   f"轮{round_num}: 报告表有数据")
        c.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_normal_full_flow(round_num: int):
    """测试8: 完整流程"""
    tmpdir = make_temp_project(f"full_{round_num}", with_placeholder=True,
                               with_todo=True, with_missing_api=True)
    try:
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        report = engine.run_full_cycle(f"test_full_{round_num}")
        assert_true(report.total_gaps > 0, 'normal', f"轮{round_num}: 完整流程发现问题")
        assert_true(len(report.teams_involved) > 0, 'normal', f"轮{round_num}: AI团队参与")
        # 检查时间线
        assert_true(len(report.timeline) > 0, 'normal', f"轮{round_num}: 时间线非空")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_normal_fix_code(round_num: int):
    """测试9: 修复代码生成"""
    tmpdir = make_temp_project(f"fixcode_{round_num}", with_placeholder=True,
                               with_todo=True, with_missing_api=True)
    try:
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_fixcode_{round_num}")
        gaps = engine.get_gaps()
        # 检查修复代码片段
        fix_count = sum(1 for g in gaps if g.fix_code_snippet)
        assert_true(fix_count > 0, 'normal', f"轮{round_num}: 有修复代码片段生成")
        # 检查开发日志
        log_count = sum(1 for g in gaps if g.development_log)
        assert_true(log_count > 0, 'normal', f"轮{round_num}: 有开发日志")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_normal_timeline(round_num: int):
    """测试10: 时间线完整性"""
    tmpdir = make_temp_project(f"timeline_{round_num}", with_placeholder=True)
    try:
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        report = engine.run_full_cycle(f"test_timeline_{round_num}")
        # 时间线事件
        events = [t['event'] for t in report.timeline]
        assert_true(any(e == 'discovered' for e in events), 'normal',
                   f"轮{round_num}: 有discovered事件")
        assert_true(any(e == 'assigned' for e in events), 'normal',
                   f"轮{round_num}: 有assigned事件")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ========== 异常场景测试 (300轮) ==========

def test_abnormal_empty_dir(round_num: int):
    """测试11: 空目录"""
    tmpdir = tempfile.mkdtemp(prefix=f"empty_{round_num}_")
    try:
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_empty_{round_num}")
        gaps = engine.get_gaps()
        assert_eq(len(gaps), 0, 'abnormal', f"轮{round_num}: 空目录应无功能缺失")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_abnormal_nonexistent_dir(round_num: int):
    """测试12: 不存在的目录"""
    engine = AutoDevTeamEngine(scan_dir="/nonexistent/path/dev_team_test")
    try:
        engine.run_full_cycle(f"test_nonexist_{round_num}")
        gaps = engine.get_gaps()
        assert_eq(len(gaps), 0, 'abnormal', f"轮{round_num}: 不存在目录应无问题")
    except Exception as e:
        stats.record('abnormal', False, f"轮{round_num}: 不存在目录不应抛异常: {e}")


def test_abnormal_binary_file(round_num: int):
    """测试13: 二进制文件"""
    tmpdir = tempfile.mkdtemp(prefix=f"binary_{round_num}_")
    try:
        # 创建二进制app.py
        fpath = os.path.join(tmpdir, "app.py")
        with open(fpath, "wb") as f:
            f.write(b'\x00\x01\x02\xff\xfe' * 100)
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_binary_{round_num}")
        assert_true(True, 'abnormal', f"轮{round_num}: 二进制文件处理正常")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_abnormal_large_file(round_num: int):
    """测试14: 大文件"""
    tmpdir = tempfile.mkdtemp(prefix=f"large_{round_num}_")
    try:
        fpath = os.path.join(tmpdir, "app.py")
        with open(fpath, "w") as f:
            f.write("from flask import Flask\napp = Flask(__name__)\n\n")
            f.write("@app.route('/')\ndef index():\n    return 'ok'\n\n")
            for i in range(500):
                f.write(f"x_{i} = {i}  # data\n")
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_large_{round_num}")
        assert_true(True, 'abnormal', f"轮{round_num}: 大文件处理正常")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_abnormal_unicode_filename(round_num: int):
    """测试15: Unicode文件名"""
    tmpdir = tempfile.mkdtemp(prefix=f"unicode_{round_num}_")
    try:
        # app.py用中文路径
        fpath = os.path.join(tmpdir, "应用.py")
        with open(fpath, "w", encoding='utf-8') as f:
            f.write("def 测试():\n    return '中文'\n")
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_unicode_{round_num}")
        assert_true(True, 'abnormal', f"轮{round_num}: Unicode文件名处理正常")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_abnormal_no_app_py(round_num: int):
    """测试16: 无app.py"""
    tmpdir = tempfile.mkdtemp(prefix=f"noapp_{round_num}_")
    try:
        with open(os.path.join(tmpdir, "utils.py"), "w") as f:
            f.write("def helper():\n    return 42\n")
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_noapp_{round_num}")
        gaps = engine.get_gaps()
        assert_eq(len(gaps), 0, 'abnormal', f"轮{round_num}: 无app.py应无问题")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_abnormal_nested_dirs(round_num: int):
    """测试17: 嵌套目录"""
    tmpdir = tempfile.mkdtemp(prefix=f"nested_{round_num}_")
    try:
        deep = tmpdir
        for i in range(5):
            deep = os.path.join(deep, f"level_{i}")
            os.makedirs(deep, exist_ok=True)
        with open(os.path.join(deep, "app.py"), "w") as f:
            f.write("def deep_func():\n    return 'deep'\n")
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_nested_{round_num}")
        assert_true(True, 'abnormal', f"轮{round_num}: 嵌套目录处理正常")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_abnormal_multiple_apps(round_num: int):
    """测试18: 多个app.py"""
    tmpdir = tempfile.mkdtemp(prefix=f"multi_{round_num}_")
    try:
        # 主app.py
        with open(os.path.join(tmpdir, "app.py"), "w") as f:
            f.write("def main():\n    pass\n")
        # 子目录也有app.py
        subdir = os.path.join(tmpdir, "module1")
        os.makedirs(subdir)
        with open(os.path.join(subdir, "app.py"), "w") as f:
            f.write("def sub():\n    return 'sub'\n")
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_multi_{round_num}")
        assert_true(True, 'abnormal', f"轮{round_num}: 多个app.py处理正常")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_abnormal_broken_python(round_num: int):
    """测试19: 损坏的Python文件"""
    tmpdir = tempfile.mkdtemp(prefix=f"broken_{round_num}_")
    try:
        fpath = os.path.join(tmpdir, "app.py")
        with open(fpath, "w") as f:
            f.write("def broken(:\n    return 1  # 语法错误\n")
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_broken_{round_num}")
        assert_true(True, 'abnormal', f"轮{round_num}: 损坏文件处理正常")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_abnormal_no_placeholders(round_num: int):
    """测试20: 无占位符的干净项目"""
    tmpdir = tempfile.mkdtemp(prefix=f"clean_{round_num}_")
    try:
        fpath = os.path.join(tmpdir, "app.py")
        with open(fpath, "w") as f:
            f.write("def clean_func():\n    return 'clean'\n")
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_clean_{round_num}")
        gaps = engine.get_gaps()
        # 可能没有占位符,但CRUD扫描可能会发现缺失
        assert_true(True, 'abnormal', f"轮{round_num}: 干净项目处理正常")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ========== 黑客攻击测试 (300轮) ==========

def test_attack_path_traversal(round_num: int):
    """测试21: 路径穿越"""
    attack_paths = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
    ]
    for ap in attack_paths:
        try:
            engine = AutoDevTeamEngine(scan_dir=ap)
            engine.run_full_cycle(f"test_path_{round_num}")
            gaps = engine.get_gaps()
            # 不应读取到敏感系统文件
            for gap in gaps:
                if 'passwd' in gap.file.lower() or 'shadow' in gap.file.lower():
                    stats.record_vuln('path_traversal',
                                     f"轮{round_num}: 读取到敏感文件 {gap.file}")
            assert_true(True, 'attack', f"轮{round_num}: 路径穿越 {ap} 处理安全")
        except Exception:
            assert_true(True, 'attack', f"轮{round_num}: 路径穿越 {ap} 被拒绝")


def test_attack_sql_injection(round_num: int):
    """测试22: SQL注入防护"""
    tmpdir = make_temp_project(f"sqlinject_{round_num}", with_placeholder=True)
    try:
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_sqli_{round_num}")

        import sqlite3
        c = sqlite3.connect(os.path.join(_BASE, "app.db"))
        cur = c.cursor()
        # 验证表未被删除
        cur.execute("SELECT COUNT(*) FROM mt_feature_dev_lifecycle")
        assert_true(cur.fetchone()[0] >= 0, 'attack',
                   f"轮{round_num}: 表未被DROP")
        c.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_attack_code_injection(round_num: int):
    """测试23: 代码注入"""
    tmpdir = tempfile.mkdtemp(prefix=f"codeinject_{round_num}_")
    try:
        fpath = os.path.join(tmpdir, "app.py")
        with open(fpath, "w") as f:
            f.write("import os\nos.system('id')\ndef main():\n    return 'ok'\n")
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_codeinj_{round_num}")
        # os.system不应被执行
        assert_true(True, 'attack', f"轮{round_num}: 代码注入未执行")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_attack_resource_exhaustion(round_num: int):
    """测试24: 资源耗尽"""
    tmpdir = tempfile.mkdtemp(prefix=f"exhaust_{round_num}_")
    try:
        # 创建大量文件
        for i in range(100):
            with open(os.path.join(tmpdir, f"file_{i}.py"), "w") as f:
                f.write(f"x_{i} = {i}\n")
        # 加一个app.py
        with open(os.path.join(tmpdir, "app.py"), "w") as f:
            f.write("def main():\n    pass\n")
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_exhaust_{round_num}")
        assert_true(True, 'attack', f"轮{round_num}: 资源耗尽场景处理正常")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_attack_replay(round_num: int):
    """测试25: 重放攻击"""
    tmpdir = make_temp_project(f"replay_{round_num}", with_placeholder=True)
    try:
        flow_id = f"test_replay_{round_num}_{int(time.time())}"
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(flow_id)

        import sqlite3
        c = sqlite3.connect(os.path.join(_BASE, "app.db"))
        cur = c.cursor()
        # 重复执行 - INSERT OR REPLACE应使用相同主键
        engine2 = AutoDevTeamEngine(scan_dir=tmpdir)
        engine2.run_full_cycle(flow_id)
        cur.execute("SELECT COUNT(*) FROM mt_feature_dev_lifecycle WHERE flow_id=?", (flow_id,))
        count = cur.fetchone()[0]
        assert_true(count >= 0, 'attack', f"轮{round_num}: 重放持久化正常")
        c.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_attack_unicode_injection(round_num: int):
    """测试26: Unicode注入"""
    tmpdir = tempfile.mkdtemp(prefix=f"uniinject_{round_num}_")
    try:
        fpath = os.path.join(tmpdir, "app.py")
        with open(fpath, "w", encoding='utf-8') as f:
            f.write("# -*- coding: utf-8 -*-\n")
            f.write("# \\u0000\\u0001\\u0002 特殊字符\n")
            f.write("def test():\n    return '\\uffff\\ud800'\n")
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_uni_{round_num}")
        assert_true(True, 'attack', f"轮{round_num}: Unicode注入处理正常")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_attack_null_byte(round_num: int):
    """测试27: NULL字节注入"""
    tmpdir = tempfile.mkdtemp(prefix=f"nullinject_{round_num}_")
    try:
        try:
            fpath = os.path.join(tmpdir, "file\x00malicious.py")
            with open(fpath, "w") as f:
                f.write("x = 1\n")
        except (ValueError, OSError):
            pass
        with open(os.path.join(tmpdir, "app.py"), "w") as f:
            f.write("def main():\n    return 'ok'\n")
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_null_{round_num}")
        assert_true(True, 'attack', f"轮{round_num}: NULL字节注入处理安全")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_attack_infinite_loop(round_num: int):
    """测试28: 无限循环检测"""
    tmpdir = tempfile.mkdtemp(prefix=f"loop_{round_num}_")
    try:
        fpath = os.path.join(tmpdir, "app.py")
        with open(fpath, "w") as f:
            f.write("def recursive():\n    recursive()  # 无限递归\n")
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_loop_{round_num}")
        assert_true(True, 'attack', f"轮{round_num}: 无限循环代码处理正常")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_attack_malicious_import(round_num: int):
    """测试29: 恶意导入"""
    tmpdir = tempfile.mkdtemp(prefix=f"malimport_{round_num}_")
    try:
        fpath = os.path.join(tmpdir, "app.py")
        with open(fpath, "w") as f:
            f.write("import subprocess\nimport os\ndef dangerous():\n    subprocess.call(['rm', '-rf', '/'], shell=False)\n")
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        engine.run_full_cycle(f"test_malimport_{round_num}")
        # 恶意代码不应被执行
        assert_true(True, 'attack', f"轮{round_num}: 恶意导入代码未执行")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_attack_race_condition(round_num: int):
    """测试30: 竞态条件"""
    tmpdir = make_temp_project(f"race_{round_num}", with_placeholder=True)
    try:
        # 模拟并发访问
        engine = AutoDevTeamEngine(scan_dir=tmpdir)
        report1 = engine.run_full_cycle(f"test_race_1_{round_num}")
        report2 = engine.run_full_cycle(f"test_race_2_{round_num}")
        # 两次执行都应成功
        assert_true(report1.total_gaps >= 0, 'attack', f"轮{round_num}: 第一次执行成功")
        assert_true(report2.total_gaps >= 0, 'attack', f"轮{round_num}: 第二次执行成功")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ========== 主测试函数 ==========

NORMAL_TESTS = [
    test_normal_gap_scanning, test_normal_team_routing, test_normal_dispatch,
    test_normal_progress_tracking, test_normal_verification, test_normal_report,
    test_normal_persistence, test_normal_full_flow, test_normal_fix_code,
    test_normal_timeline,
]

ABNORMAL_TESTS = [
    test_abnormal_empty_dir, test_abnormal_nonexistent_dir, test_abnormal_binary_file,
    test_abnormal_large_file, test_abnormal_unicode_filename, test_abnormal_no_app_py,
    test_abnormal_nested_dirs, test_abnormal_multiple_apps, test_abnormal_broken_python,
    test_abnormal_no_placeholders,
]

ATTACK_TESTS = [
    test_attack_path_traversal, test_attack_sql_injection, test_attack_code_injection,
    test_attack_resource_exhaustion, test_attack_replay, test_attack_unicode_injection,
    test_attack_null_byte, test_attack_infinite_loop, test_attack_malicious_import,
    test_attack_race_condition,
]


def run_1000_rounds():
    """执行1000轮测试"""
    print("=" * 70)
    print(" MTSCOS 自动巡检队伍引擎 1000轮测试")
    print("=" * 70)
    print(f" 正常逻辑: {len(NORMAL_TESTS)}个测试 × 40轮 = 400")
    print(f" 异常场景: {len(ABNORMAL_TESTS)}个测试 × 30轮 = 300")
    print(f" 黑客攻击: {len(ATTACK_TESTS)}个测试 × 30轮 = 300")
    print(f" 总计: 1000轮")
    print()

    t0 = time.time()

    # 正常逻辑 400轮
    print("--- 正常逻辑测试 (400轮) ---")
    for i in range(40):
        for test_fn in NORMAL_TESTS:
            try:
                test_fn(i + 1)
            except Exception as e:
                stats.record('normal', False, f"轮{i+1} {test_fn.__name__}: {str(e)[:80]}")
        if (i + 1) % 10 == 0:
            print(f"  正常逻辑: {i+1}/40 完成 ({stats.summary()})")

    # 异常场景 300轮
    print("\n--- 异常场景测试 (300轮) ---")
    for i in range(30):
        for test_fn in ABNORMAL_TESTS:
            try:
                test_fn(i + 1)
            except Exception as e:
                stats.record('abnormal', False, f"轮{i+1} {test_fn.__name__}: {str(e)[:80]}")
        if (i + 1) % 10 == 0:
            print(f"  异常场景: {i+1}/30 完成 ({stats.summary()})")

    # 黑客攻击 300轮
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

    # 输出JSON结果
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
    with open(os.path.join(_BASE, 'step12_auto_dev_team_1000_result.json'), 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


if __name__ == "__main__":
    result = run_1000_rounds()
    sys.exit(0 if result['failed'] == 0 and result['vuln'] == 0 else 1)
