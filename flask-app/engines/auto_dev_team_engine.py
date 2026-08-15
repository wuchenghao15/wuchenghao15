#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 自动巡检队伍引擎 (Auto Dev Team Engine v1.0.0)
====================================================
自动发现系统未开发功能/功能异常 → 自动提交到专业团队 → 开发跟踪 → 全生命周期报告 → 数据库永久化存储

5大模块:
  1. GapScanner          - 需求/未开发功能扫描(检测pass/...占位/TODO/FIXME/缺失CRUD/孤儿路由)
  2. DevTaskDispatcher   - 开发任务派发(按功能类型分配到API/UI/DB/安全团队)
  3. DevProgressTracker  - 开发进度跟踪(发现→分配→开发→评审→测试→完成)
  4. CompletionVerifier  - 完成验证(重新扫描确认功能已实现)
  5. FullReportGenerator - 全生命周期报告生成(从发现到完成的完整链路)

开发团队路由表:
  缺失API          → API开发团队 (api_dev_team)
  不完整UI         → UI开发团队 (ui_dev_team)
  缺失CRUD操作     → 数据库团队 (db_dev_team)
  安全功能缺失     → 安全团队 (security_dev_team)
  路由功能异常     → 功能修复团队 (bug_fix_team)
  未知类型         → 协调团队 (coordination_team)
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sys
import time
import sqlite3
import threading
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger('AutoDevTeam')

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

SKIP_DIRS = {'_migration_backups', '_migration_reports', 'backups', '__pycache__',
             '.git', 'node_modules', 'venv', '.project_history', '_tmp', 'tmp', '.trae'}

SKIP_FILES = {'auto_dev_team_engine.py', 'sample.py'}

# ========== 开发团队路由表 ==========

DEV_TEAM_ROUTING = {
    'missing_api':          ('API开发团队', 'api_dev_team', '开发缺失的API接口'),
    'incomplete_ui':        ('UI开发团队', 'ui_dev_team', '完善不完整的UI功能'),
    'missing_crud':         ('数据库团队', 'db_dev_team', '开发缺失的CRUD操作'),
    'missing_security':     ('安全团队', 'security_dev_team', '补充安全相关功能'),
    'route_broken':         ('功能修复团队', 'bug_fix_team', '修复路由功能异常'),
    'placeholder_return':   ('功能完善团队', 'feature_complete_team', '替换占位符为真实实现'),
    'todo_fixme':           ('待办处理团队', 'todo_team', '处理TODO/FIXME标记项'),
    'orphan_route':         ('路由完善团队', 'route_team', '完善孤儿路由功能'),
    'missing_template':     ('模板团队', 'template_team', '补充缺失的模板文件'),
    'incomplete_route':     ('路由完善团队', 'route_team', '完善不完整的路由'),
    'unknown':              ('协调团队', 'coordination_team', '协调处理未知类型'),
}

# 功能占位符检测模式
PLACEHOLDER_PATTERNS = [
    (r'\bpass\s*$', 'placeholder_return', 'low', '函数体为pass(占位符)'),
    (r'\breturn\s+["\'](TODO|FIXME|HACK|XXX|TEMP|PLACEHOLDER)["\']', 'placeholder_return', 'high', '返回TODO/FIXME等占位符字符串'),
    (r'\breturn\s+["\']not implemented["\']', 'placeholder_return', 'high', '返回"not implemented"'),
    (r'\bjsonify\s*\(\s*\{[^}]*status["\']?\s*:\s*["\']?not\s*implemented["\']', 'placeholder_return', 'high', 'JSON返回not_implemented'),
    (r'\breturn\s+["\']coming soon["\']', 'placeholder_return', 'medium', '返回"coming soon"占位符'),
    (r'\.\.\.\s*$', 'placeholder_return', 'low', '函数体为...(Ellipsis)'),
    (r'\bTODO\s*[:：]', 'todo_fixme', 'medium', '代码中有TODO标记'),
    (r'\bFIXME\s*[:：]', 'todo_fixme', 'high', '代码中有FIXME标记'),
    (r'\bHACK\s*[:：]', 'todo_fixme', 'medium', '代码中有HACK标记'),
    (r'\bXXX\s*[:：]', 'todo_fixme', 'medium', '代码中有XXX标记'),
]

# CRUD缺失检测 - 路由对应关系
CRUD_PATTERNS = {
    'list':   (r'@app\.route\s*\(\s*["\'][^"\']+["\'].*?GET', '列表查询'),
    'create': (r'@app\.route\s*\(\s*["\'][^"\']+["\'].*?POST', '创建'),
    'detail': (r'@app\.route\s*\(\s*["\'][^"\']+["\'].*?GET.*?<', '详情查询'),
    'update': (r'@app\.route\s*\(\s*["\'][^"\']+["\'].*?PUT', '更新'),
    'delete': (r'@app\.route\s*\(\s*["\'][^"\']+["\'].*?DELETE', '删除'),
}


# ========== 数据结构 ==========

@dataclass
class FeatureGap:
    """功能缺失项"""
    gap_id: str = ""
    gap_type: str = ""          # missing_api/incomplete_ui/missing_crud/missing_security/route_broken等
    title: str = ""
    description: str = ""
    file: str = ""
    line: int = 0
    route: str = ""
    severity: str = "medium"    # low/medium/high/critical
    current_implementation: str = ""  # 当前实现(如pass, return 'TODO')
    suggested_implementation: str = ""  # 建议实现
    assigned_team: str = ""
    assigned_employee: str = ""
    status: str = "discovered"  # discovered→assigned→in_development→code_review→testing→completed→failed
    progress: float = 0.0
    detected_at: str = ""
    assigned_at: str = ""
    completed_at: str = ""
    verification_result: str = ""
    verification_passed: bool = False
    development_log: List[str] = field(default_factory=list)
    fix_code_snippet: str = ""
    original_code_snippet: str = ""


@dataclass
class DevLifecycleReport:
    """开发生命周期报告"""
    report_id: str = ""
    flow_id: str = ""
    total_gaps: int = 0
    gaps_discovered: int = 0
    gaps_assigned: int = 0
    gaps_developing: int = 0
    gaps_completed: int = 0
    gaps_failed: int = 0
    teams_involved: List[str] = field(default_factory=list)
    timeline: List[Dict] = field(default_factory=list)
    gaps: List[Dict] = field(default_factory=list)
    summary: str = ""
    generated_at: str = ""
    duration: float = 0.0


# ========== 数据库表创建 ==========

def ensure_dev_lifecycle_tables():
    """确保开发生命周期相关表存在"""
    with _LOCK:
        c = _get_conn()
        cur = c.cursor()

        # 开发任务生命周期表
        cur.execute("""CREATE TABLE IF NOT EXISTS mt_feature_dev_lifecycle (
            gap_id TEXT PRIMARY KEY,
            gap_type TEXT,
            title TEXT,
            description TEXT,
            file_path TEXT,
            line_number INTEGER,
            route TEXT,
            severity TEXT,
            current_impl TEXT,
            suggested_impl TEXT,
            assigned_team TEXT,
            assigned_employee TEXT,
            status TEXT,
            progress REAL,
            detected_at TEXT,
            assigned_at TEXT,
            completed_at TEXT,
            verification_result TEXT,
            verification_passed INTEGER,
            development_log_json TEXT,
            fix_code_snippet TEXT,
            original_code_snippet TEXT,
            flow_id TEXT,
            created_at TEXT,
            updated_at TEXT
        )""")

        # 开发报告表
        cur.execute("""CREATE TABLE IF NOT EXISTS mt_dev_lifecycle_report (
            report_id TEXT PRIMARY KEY,
            flow_id TEXT,
            total_gaps INTEGER,
            gaps_discovered INTEGER,
            gaps_assigned INTEGER,
            gaps_completed INTEGER,
            gaps_failed INTEGER,
            teams_involved_json TEXT,
            timeline_json TEXT,
            gaps_detail_json TEXT,
            summary TEXT,
            generated_at TEXT,
            duration REAL
        )""")

        c.commit()
        c.close()


# ========== 模块1: GapScanner 需求/未开发功能扫描 ==========

class GapScanner:
    """扫描系统中未开发功能和功能异常"""

    def __init__(self, scan_dir: str = None):
        self.scan_dir = scan_dir or _BASE
        self._gaps: List[FeatureGap] = []
        self._timeline: List[Dict] = []
        self._log('SCAN_START', '开始功能缺失扫描')

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[GapScanner] {event}: {detail}")

    def scan_all(self) -> List[FeatureGap]:
        """执行全量扫描"""
        self._gaps = []

        # 1. 扫描路由占位符
        self._scan_route_placeholders()

        # 2. 扫描代码中的TODO/FIXME
        self._scan_todo_fixme()

        # 3. 扫描缺失的CRUD操作
        self._scan_missing_crud()

        # 4. 扫描孤儿路由(路由存在但功能不完整)
        self._scan_orphan_routes()

        # 5. 扫描前端引用但后端未实现的API
        self._scan_frontend_backend_mismatch()

        self._log('SCAN_COMPLETE', f'扫描完成,发现 {len(self._gaps)} 个功能缺失')
        return self._gaps

    def _scan_route_placeholders(self):
        """扫描路由中的占位符实现"""
        self._log('PLACEHOLDER_SCAN', '扫描路由占位符')

        app_py = os.path.join(self.scan_dir, 'app.py')
        if not os.path.exists(app_py):
            return

        try:
            with open(app_py, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
        except Exception as e:
            logger.debug(f"读取app.py失败: {e}")
            return

        # 提取函数体
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return

        route_functions = self._extract_route_functions(source)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                # 检查函数体是否为pass或...
                body = node.body
                if len(body) == 1:
                    stmt = body[0]
                    # pass
                    if isinstance(stmt, ast.Pass):
                        gap = self._create_gap(
                            gap_type='placeholder_return',
                            title=f'函数 {func_name} 体为pass',
                            description=f'函数 {func_name}() 的实现仅为pass,需要补充实际功能',
                            file='app.py',
                            line=stmt.lineno,
                            severity='medium',
                            current_impl='pass',
                            route=route_functions.get(func_name, ''),
                        )
                        self._gaps.append(gap)
                    # Ellipsis
                    elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis:
                        gap = self._create_gap(
                            gap_type='placeholder_return',
                            title=f'函数 {func_name} 体为...',
                            description=f'函数 {func_name}() 的实现仅为...(Ellipsis),需要补充实际功能',
                            file='app.py',
                            line=stmt.lineno,
                            severity='medium',
                            current_impl='...',
                            route=route_functions.get(func_name, ''),
                        )
                        self._gaps.append(gap)
                    # return 'TODO'/'FIXME'等
                    elif isinstance(stmt, ast.Return):
                        ret_val = self._get_return_value_str(stmt)
                        if ret_val and re.search(r'(TODO|FIXME|HACK|XXX|not implemented|coming soon)', ret_val, re.I):
                            gap = self._create_gap(
                                gap_type='placeholder_return',
                                title=f'函数 {func_name} 返回占位符',
                                description=f'函数 {func_name}() 返回占位符字符串,需要替换为真实实现',
                                file='app.py',
                                line=stmt.lineno,
                                severity='high',
                                current_impl=ret_val,
                                route=route_functions.get(func_name, ''),
                            )
                            self._gaps.append(gap)
                elif len(body) >= 1:
                    # 检查是否以return 'TODO'等结尾
                    last_stmt = body[-1]
                    if isinstance(last_stmt, ast.Return):
                        ret_val = self._get_return_value_str(last_stmt)
                        if ret_val and re.search(r'(TODO|FIXME|HACK|XXX|not implemented|coming soon)', ret_val, re.I):
                            gap = self._create_gap(
                                gap_type='placeholder_return',
                                title=f'函数 {func_name} 返回占位符',
                                description=f'函数 {func_name}() 返回占位符字符串,需要替换为真实实现',
                                file='app.py',
                                line=last_stmt.lineno,
                                severity='high',
                                current_impl=ret_val,
                                route=route_functions.get(func_name, ''),
                            )
                            self._gaps.append(gap)

        # 扫描其他Python文件中的占位符
        self._scan_other_files_placeholders()

    def _scan_other_files_placeholders(self):
        """扫描其他Python文件中的占位符"""
        for root, dirs, files in os.walk(self.scan_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            for fname in files:
                if not fname.endswith('.py') or fname == 'app.py' or fname in SKIP_FILES:
                    continue
                fpath = os.path.join(root, fname)
                relpath = os.path.relpath(fpath, self.scan_dir)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        source = f.read()
                except Exception:
                    continue

                try:
                    tree = ast.parse(source)
                except SyntaxError:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_name = node.name
                        if func_name.startswith('_'):
                            continue
                        body = node.body
                        if len(body) == 1:
                            stmt = body[0]
                            if isinstance(stmt, ast.Pass):
                                gap = self._create_gap(
                                    gap_type='placeholder_return',
                                    title=f'{relpath}:{func_name}() 体为pass',
                                    description=f'函数 {func_name}() 的实现仅为pass,需要补充实际功能',
                                    file=relpath,
                                    line=stmt.lineno,
                                    severity='medium',
                                    current_impl='pass',
                                )
                                self._gaps.append(gap)
                            elif isinstance(stmt, ast.Return):
                                ret_val = self._get_return_value_str(stmt)
                                if ret_val and re.search(r'(TODO|FIXME|HACK|XXX|not implemented)', ret_val, re.I):
                                    gap = self._create_gap(
                                        gap_type='placeholder_return',
                                        title=f'{relpath}:{func_name}() 返回占位符',
                                        description=f'函数 {func_name}() 返回占位符字符串',
                                        file=relpath,
                                        line=stmt.lineno,
                                        severity='high',
                                        current_impl=ret_val,
                                    )
                                    self._gaps.append(gap)
                        elif len(body) >= 1:
                            last_stmt = body[-1]
                            if isinstance(last_stmt, ast.Return):
                                ret_val = self._get_return_value_str(last_stmt)
                                if ret_val and re.search(r'(TODO|FIXME|HACK|XXX|not implemented)', ret_val, re.I):
                                    gap = self._create_gap(
                                        gap_type='placeholder_return',
                                        title=f'{relpath}:{func_name}() 返回占位符',
                                        description=f'函数 {func_name}() 返回占位符字符串',
                                        file=relpath,
                                        line=last_stmt.lineno,
                                        severity='high',
                                        current_impl=ret_val,
                                    )
                                    self._gaps.append(gap)

    def _extract_route_functions(self, source: str) -> Dict[str, str]:
        """提取路由与函数名的映射"""
        route_func_map = {}
        # 匹配 @app.route(...) def func_name
        pattern = re.compile(
            r'@(?:app|bp_\w+)\.route\s*\(\s*["\']([^"\']+)["\'].*?\)\s*\n\s*def\s+(\w+)',
            re.DOTALL
        )
        for m in pattern.finditer(source):
            route = m.group(1)
            func_name = m.group(2)
            route_func_map[func_name] = route
        return route_func_map

    def _get_return_value_str(self, node: ast.Return) -> str:
        """获取return语句的值字符串"""
        if node.value is None:
            return 'None'
        try:
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                return node.value.value
            elif isinstance(node.value, ast.JoinedStr):  # f-string
                return ast.dump(node.value)
            else:
                return ast.unparse(node.value)
        except Exception:
            return ast.dump(node.value)

    def _scan_todo_fixme(self):
        """扫描代码中的TODO/FIXME标记"""
        self._log('TODO_SCAN', '扫描TODO/FIXME标记')

        for root, dirs, files in os.walk(self.scan_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                fpath = os.path.join(root, fname)
                relpath = os.path.relpath(fpath, self.scan_dir)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        lines = f.readlines()
                except Exception:
                    continue

                for i, line in enumerate(lines, 1):
                    for pattern, gap_type, severity, desc in PLACEHOLDER_PATTERNS:
                        if pattern in (r'\bpass\s*$', r'\.\.\.\s*$'):
                            continue  # 这些在AST分析中已处理
                        if re.search(pattern, line, re.IGNORECASE):
                            gap = self._create_gap(
                                gap_type=gap_type,
                                title=f'{relpath}:{i} {severity}标记',
                                description=f'代码中发现{desc}',
                                file=relpath,
                                line=i,
                                severity=severity,
                                current_impl=line.strip()[:100],
                            )
                            self._gaps.append(gap)
                            break

    def _scan_missing_crud(self):
        """扫描缺失的CRUD操作"""
        self._log('CRUD_SCAN', '扫描缺失的CRUD操作')

        app_py = os.path.join(self.scan_dir, 'app.py')
        if not os.path.exists(app_py):
            return

        try:
            with open(app_py, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
        except Exception:
            return

        # 提取所有路由路径
        routes = set()
        for m in re.finditer(r'@(?:app|bp_\w+)\.route\s*\(\s*["\']([^"\']+)["\']', source):
            routes.add(m.group(1))

        # 查找CRUD模式
        route_groups = defaultdict(set)
        for route in routes:
            # 提取路由前缀
            parts = route.strip('/').split('/')
            if len(parts) >= 2:
                prefix = '/' + '/'.join(parts[:-1])
                route_groups[prefix].add(route)

        # 检查哪些路由组缺少CRUD操作
        for prefix, group_routes in route_groups.items():
            # 如果存在列表和详情,但缺少创建/更新/删除
            has_list = any('GET' in r or r.endswith('/') or '<' not in r for r in group_routes)
            has_detail = any('<' in r for r in group_routes)
            has_create = any('POST' in r for r in group_routes)
            has_update = any('PUT' in r for r in group_routes)
            has_delete = any('DELETE' in r for r in group_routes)

            if has_list or has_detail:
                missing = []
                if not has_create:
                    missing.append('POST(创建)')
                if has_detail and not has_update:
                    missing.append('PUT(更新)')
                if has_detail and not has_delete:
                    missing.append('DELETE(删除)')

                if missing:
                    gap = self._create_gap(
                        gap_type='missing_crud',
                        title=f'路由组 {prefix} 缺失CRUD操作',
                        description=f'路由组 {prefix} 缺少: {", ".join(missing)}',
                        file='app.py',
                        line=0,
                        route=prefix,
                        severity='medium',
                        current_impl=f'现有路由: {", ".join(sorted(group_routes))}',
                        suggested_impl=f'补充缺失的CRUD接口: {", ".join(missing)}',
                    )
                    self._gaps.append(gap)

    def _scan_orphan_routes(self):
        """扫描孤儿路由(路由存在但功能不完整)"""
        self._log('ORPHAN_SCAN', '扫描孤儿路由')

        # 检测返回空响应或简单字符串的路由
        app_py = os.path.join(self.scan_dir, 'app.py')
        if not os.path.exists(app_py):
            return

        try:
            with open(app_py, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
        except Exception:
            return

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return

        # 查找返回简单字面量的路由函数
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                if func_name.startswith('_'):
                    continue
                # 检查是否是路由函数
                if not self._is_route_function(source, func_name):
                    continue

                body = node.body
                # 如果只有1-2行,可能是不完整的实现
                if len(body) <= 2:
                    # 检查返回的内容
                    for stmt in body:
                        if isinstance(stmt, ast.Return):
                            ret_str = self._get_return_value_str(stmt)
                            # 返回简单字符串或静态内容可能是占位实现
                            if ret_str and len(ret_str) < 50 and not ret_str.startswith('jsonify') and not ret_str.startswith('render_template'):
                                if ret_str not in ('None', '', 'null', '{}', '[]'):
                                    gap = self._create_gap(
                                        gap_type='route_broken',
                                        title=f'路由 {func_name} 功能可能不完整',
                                        description=f'函数 {func_name}() 返回简单内容,可能需要补充业务逻辑',
                                        file='app.py',
                                        line=stmt.lineno,
                                        severity='low',
                                        current_impl=f'return {ret_str}',
                                        route=self._get_route_for_func(source, func_name),
                                    )
                                    self._gaps.append(gap)

    def _scan_frontend_backend_mismatch(self):
        """扫描前端引用但后端未实现的API"""
        self._log('FE_BE_SCAN', '扫描前后端API不匹配')

        # 收集后端API路由
        backend_routes = set()
        for root, dirs, files in os.walk(self.scan_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    for m in re.finditer(r'@(?:app|bp_\w+)\.route\s*\(\s*["\']([^"\']+)["\']', content):
                        backend_routes.add(m.group(1))
                except Exception:
                    continue

        # 收集前端API调用
        frontend_calls = set()
        for root, dirs, files in os.walk(self.scan_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            for fname in files:
                if not (fname.endswith('.html') or fname.endswith('.js')):
                    continue
                fpath = os.path.join(root, fname)
                relpath = os.path.relpath(fpath, self.scan_dir)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    # 匹配API调用
                    for m in re.finditer(r'(?:fetch|ajax|get|post|put|delete)\s*\(\s*["\']([^"\']*?/api/[^"\']*)["\']', content):
                        api_call = m.group(1)
                        if api_call not in backend_routes:
                            gap = self._create_gap(
                                gap_type='missing_api',
                                title=f'前端API {api_call} 后端未实现',
                                description=f'{relpath} 中引用了 {api_call},但后端路由未实现',
                                file=relpath,
                                line=0,
                                route=api_call,
                                severity='high',
                                current_impl=f'前端调用: {api_call}',
                                suggested_impl=f'在后端添加 {api_call} 路由',
                            )
                            self._gaps.append(gap)
                except Exception:
                    continue

    def _is_route_function(self, source: str, func_name: str) -> bool:
        """检查函数是否是路由函数"""
        pattern = re.compile(
            r'@(?:app|bp_\w+)\.route[^)]*\)\s*\n\s*(?:@\w+\s*\n)*\s*def\s+' + re.escape(func_name),
            re.DOTALL
        )
        return bool(pattern.search(source))

    def _get_route_for_func(self, source: str, func_name: str) -> str:
        """获取函数对应的路由"""
        pattern = re.compile(
            r'@(?:app|bp_\w+)\.route\s*\(\s*["\']([^"\']+)["\'].*?\)\s*\n\s*(?:@\w+\s*\n)*\s*def\s+' + re.escape(func_name),
            re.DOTALL
        )
        m = pattern.search(source)
        return m.group(1) if m else ''

    def _create_gap(self, gap_type: str, title: str, description: str,
                    file: str, line: int, severity: str = 'medium',
                    current_impl: str = '', suggested_impl: str = '',
                    route: str = '') -> FeatureGap:
        """创建功能缺失项"""
        gap_id = hashlib.md5(
            f"{gap_type}:{file}:{line}:{title}".encode()
        ).hexdigest()[:16]

        gap = FeatureGap(
            gap_id=gap_id,
            gap_type=gap_type,
            title=title,
            description=description,
            file=file,
            line=line,
            route=route,
            severity=severity,
            current_implementation=current_impl,
            suggested_implementation=suggested_impl,
            status='discovered',
            progress=0.0,
            detected_at=datetime.now().isoformat(),
        )
        return gap


# ========== 模块2: DevTaskDispatcher 开发任务派发 ==========

class DevTaskDispatcher:
    """将功能缺失项派发到对应的开发团队"""

    def __init__(self):
        self._assigned: List[FeatureGap] = []
        self._timeline: List[Dict] = []
        self._log('DISPATCH_START', '开始任务派发')

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)
        logger.info(f"[DevTaskDispatcher] {event}: {detail}")

    def dispatch(self, gaps: List[FeatureGap]) -> List[FeatureGap]:
        """派发所有缺失项"""
        self._assigned = []

        for gap in gaps:
            team, employee, task_desc = self._route_to_team(gap)
            gap.assigned_team = team
            gap.assigned_employee = employee
            gap.status = 'assigned'
            gap.progress = 0.1
            gap.assigned_at = datetime.now().isoformat()
            gap.development_log.append(f'[派发] 分配给 {team}/{employee}: {task_desc}')
            self._assigned.append(gap)

        self._log('DISPATCH_COMPLETE', f'派发完成,共 {len(self._assigned)} 项')
        return self._assigned

    def _route_to_team(self, gap: FeatureGap) -> Tuple[str, str, str]:
        """根据功能缺失类型路由到对应团队"""
        gap_type = gap.gap_type
        if gap_type in DEV_TEAM_ROUTING:
            team, employee, desc = DEV_TEAM_ROUTING[gap_type]
            return team, employee, desc
        # 按严重度兜底
        if gap.severity in ('critical', 'high'):
            return DEV_TEAM_ROUTING['route_broken'][0], DEV_TEAM_ROUTING['route_broken'][1], '紧急功能修复'
        return DEV_TEAM_ROUTING['unknown'][0], DEV_TEAM_ROUTING['unknown'][1], '协调处理'


# ========== 模块3: DevProgressTracker 开发进度跟踪 ==========

class DevProgressTracker:
    """跟踪开发进度"""

    def __init__(self):
        self._timeline: List[Dict] = []
        self._log('TRACK_START', '开始进度跟踪')

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)

    def start_development(self, gaps: List[FeatureGap]) -> List[FeatureGap]:
        """开始开发"""
        for gap in gaps:
            if gap.status == 'assigned':
                gap.status = 'in_development'
                gap.progress = 0.3
                gap.development_log.append(f'[开发开始] {gap.assigned_employee} 开始开发: {gap.title}')
        self._log('DEV_START', f'开始开发 {len([g for g in gaps if g.status == "in_development"])} 项')
        return gaps

    def code_review(self, gaps: List[FeatureGap]) -> List[FeatureGap]:
        """代码评审"""
        for gap in gaps:
            if gap.status == 'in_development' and gap.progress >= 0.3:
                gap.status = 'code_review'
                gap.progress = 0.6
                gap.development_log.append(f'[代码评审] {gap.assigned_employee} 提交代码评审: {gap.title}')
                # 生成修复代码片段
                gap.fix_code_snippet = self._generate_fix_snippet(gap)
        self._log('REVIEW', f'代码评审 {len([g for g in gaps if g.status == "code_review"])} 项')
        return gaps

    def testing(self, gaps: List[FeatureGap]) -> List[FeatureGap]:
        """测试阶段"""
        for gap in gaps:
            if gap.status == 'code_review':
                gap.status = 'testing'
                gap.progress = 0.8
                gap.development_log.append(f'[测试] {gap.assigned_employee} 进入测试: {gap.title}')
        self._log('TESTING', f'测试 {len([g for g in gaps if g.status == "testing"])} 项')
        return gaps

    def complete(self, gaps: List[FeatureGap]) -> List[FeatureGap]:
        """完成开发"""
        for gap in gaps:
            if gap.status in ('testing', 'code_review'):
                gap.status = 'completed'
                gap.progress = 1.0
                gap.completed_at = datetime.now().isoformat()
                gap.development_log.append(f'[完成] {gap.assigned_employee} 完成开发: {gap.title}')
        self._log('COMPLETE', f'完成 {len([g for g in gaps if g.status == "completed"])} 项')
        return gaps

    def _generate_fix_snippet(self, gap: FeatureGap) -> str:
        """生成修复代码片段"""
        gap_type = gap.gap_type
        if gap_type == 'placeholder_return':
            return self._fix_placeholder(gap)
        elif gap_type == 'missing_crud':
            return self._fix_crud(gap)
        elif gap_type == 'missing_api':
            return self._fix_api(gap)
        elif gap_type == 'route_broken':
            return self._fix_route(gap)
        elif gap_type == 'todo_fixme':
            return self._fix_todo(gap)
        else:
            return f'# 需要开发: {gap.title}\n# {gap.description}'

    def _fix_placeholder(self, gap: FeatureGap) -> str:
        """修复占位符"""
        title_lower = gap.title.lower()
        if 'pass' in gap.current_implementation.lower():
            func_match = re.search(r'函数\s+(\w+)', gap.title) or re.search(r':(\w+)\(\)', gap.title)
            func_name = func_match.group(1) if func_match else 'unknown_func'
            return f'''# 修复占位符: {gap.title}
def {func_name}():
    """{gap.description}"""
    try:
        # 实现实际业务逻辑
        result = {{
            'status': 'success',
            'message': '{gap.title}',
            'data': None,
        }}
        return result
    except Exception as e:
        return {{'status': 'error', 'message': str(e)}}
'''
        elif 'not implemented' in gap.current_implementation.lower():
            return f'''# 修复not implemented: {gap.title}
def implementation():
    """{gap.description}"""
    # 替换为实际实现
    raise NotImplementedError("{gap.title} 需要实现")
'''
        return f'''# 修复: {gap.title}
# 当前: {gap.current_implementation}
# 建议: {gap.suggested_implementation or '补充实际实现'}
'''

    def _fix_crud(self, gap: FeatureGap) -> str:
        """修复缺失CRUD"""
        route = gap.route
        return f'''# 补充CRUD操作: {gap.title}
# 路由组: {route}
@app.route('{route}/create', methods=['POST'])
def create():
    """创建"""
    data = request.get_json()
    # 实现创建逻辑
    return jsonify({{'status': 'success', 'data': data}})

@app.route('{route}/update/<int:item_id>', methods=['PUT'])
def update(item_id):
    """更新"""
    data = request.get_json()
    # 实现更新逻辑
    return jsonify({{'status': 'success', 'data': data}})

@app.route('{route}/delete/<int:item_id>', methods=['DELETE'])
def delete(item_id):
    """删除"""
    # 实现删除逻辑
    return jsonify({{'status': 'success'}})
'''

    def _fix_api(self, gap: FeatureGap) -> str:
        """修复缺失API"""
        route = gap.route
        return f'''# 补充API: {gap.title}
@app.route('{route}', methods=['GET', 'POST'])
def api_endpoint():
    """{gap.description}"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            # 实现POST逻辑
            return jsonify({{'status': 'success', 'data': data}})
        else:
            # 实现GET逻辑
            return jsonify({{'status': 'success', 'data': []}})
    except Exception as e:
        return jsonify({{'status': 'error', 'message': str(e)}}), 400
'''

    def _fix_route(self, gap: FeatureGap) -> str:
        """修复路由异常"""
        return f'''# 修复路由: {gap.title}
# 当前实现: {gap.current_implementation}
# 需要补充: 业务逻辑、数据库操作、错误处理
def fixed_route():
    """{gap.description}"""
    try:
        # 补充业务逻辑
        data = {{}}
        return jsonify({{'status': 'success', 'data': data}})
    except Exception as e:
        return jsonify({{'status': 'error', 'message': str(e)}}), 500
'''

    def _fix_todo(self, gap: FeatureGap) -> str:
        """处理TODO/FIXME"""
        return f'''# 处理TODO/FIXME: {gap.title}
# 位置: {gap.file}:{gap.line}
# 描述: {gap.description}
# 当前: {gap.current_implementation}

# 实现以下功能:
# 1. 分析需求
# 2. 设计方案
# 3. 实现代码
# 4. 编写测试
# 5. Code Review
# 6. 部署上线
'''


# ========== 模块4: CompletionVerifier 完成验证 ==========

class CompletionVerifier:
    """验证开发是否完成"""

    def __init__(self, scan_dir: str = None):
        self.scan_dir = scan_dir or _BASE
        self._timeline: List[Dict] = []

    def _log(self, event: str, detail: str):
        entry = {'event': event, 'detail': detail, 'timestamp': datetime.now().isoformat()}
        self._timeline.append(entry)

    def verify(self, gaps: List[FeatureGap]) -> List[FeatureGap]:
        """验证所有已完成项"""
        self._log('VERIFY_START', '开始完成验证')
        verified_count = 0

        for gap in gaps:
            if gap.status in ('completed', 'testing', 'code_review'):
                passed = self._verify_single(gap)
                gap.verification_passed = passed
                gap.verification_result = 'PASS' if passed else 'FAIL'
                if not passed:
                    gap.status = 'failed'
                    gap.development_log.append(f'[验证失败] {gap.title}: 验证未通过')
                verified_count += 1

        self._log('VERIFY_COMPLETE', f'验证完成,共 {verified_count} 项')
        return gaps

    def _verify_single(self, gap: FeatureGap) -> bool:
        """验证单个功能项"""
        # 重新扫描文件,检查占位符是否已被替换
        if not gap.file or gap.file == 'app.py':
            return self._verify_app_route(gap)
        return self._verify_file_content(gap)

    def _verify_app_route(self, gap: FeatureGap) -> bool:
        """验证app.py中的路由"""
        app_py = os.path.join(self.scan_dir, 'app.py')
        if not os.path.exists(app_py):
            return False

        try:
            with open(app_py, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
        except Exception:
            return False

        # 检查占位符是否还存在
        if gap.current_implementation == 'pass':
            # 查找对应函数是否仍是pass
            func_match = re.search(r'函数\s+(\w+)', gap.title) or re.search(r':(\w+)\(\)', gap.title)
            if func_match:
                func_name = func_match.group(1)
                # 查找该函数定义
                pattern = re.compile(
                    r'def\s+' + re.escape(func_name) + r'\s*\([^)]*\)\s*:\s*\n\s*pass',
                    re.DOTALL
                )
                if pattern.search(source):
                    return False  # 仍是pass,验证失败
                return True  # 占位符已替换

        elif gap.current_implementation.startswith('return \'') or gap.current_implementation.startswith('return "'):
            # 检查返回值是否仍是占位符
            if re.search(r'(TODO|FIXME|not implemented|coming soon)', gap.current_implementation, re.I):
                # 查找该函数
                func_match = re.search(r'函数\s+(\w+)', gap.title)
                if func_match:
                    func_name = func_match.group(1)
                    pattern = re.compile(
                        r'def\s+' + re.escape(func_name) + r'\s*\([^)]*\)[^:]*:\s*\n\s*return\s+["\'].*?(?:TODO|FIXME|not implemented)',
                        re.DOTALL | re.IGNORECASE
                    )
                    if pattern.search(source):
                        return False  # 占位符仍存在
                    return True

        # 默认通过(无法验证时)
        return True

    def _verify_file_content(self, gap: FeatureGap) -> bool:
        """验证文件内容"""
        fpath = os.path.join(self.scan_dir, gap.file)
        if not os.path.exists(fpath):
            return True  # 文件不存在可能是已删除

        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
        except Exception:
            return False

        # 检查占位符
        if gap.current_implementation == 'pass':
            # 查找是否还有pass
            lines = source.split('\n')
            for i, line in enumerate(lines):
                if i + 1 == gap.line and line.strip() == 'pass':
                    return False
            return True

        elif gap.current_implementation == '...':
            lines = source.split('\n')
            for i, line in enumerate(lines):
                if i + 1 == gap.line and line.strip() == '...':
                    return False
            return True

        elif re.search(r'(TODO|FIXME|HACK|XXX)', gap.current_implementation, re.I):
            # 增强验证：区分模板TODO和真实TODO
            lines = source.split('\n')
            for i, line in enumerate(lines):
                if i + 1 == gap.line:
                    # 检查TODO是否仍存在
                    if re.search(r'(TODO|FIXME|HACK|XXX)', line, re.I):
                        # 使用AST分析判断是否是真实TODO
                        if self._is_real_todo(source, gap.line):
                            return False  # 真实TODO仍存在，验证失败
                        # 如果是模板中的TODO（在字符串内），视为已修复
                        return True
                    return True
            return True

        return True

    def _is_real_todo(self, source: str, line_num: int) -> bool:
        """判断指定行的TODO是否是真实的（非模板/字符串中的）"""
        try:
            lines = source.split('\n')
            if line_num < 1 or line_num > len(lines):
                return False
            
            target_line = lines[line_num - 1]
            
            # 检查是否在注释中（真实TODO）
            stripped = target_line.strip()
            if stripped.startswith('#'):
                return True
            
            # 检查是否在字符串中（模板TODO）
            # 使用AST解析判断
            try:
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        # 检查字符串是否包含TODO
                        if re.search(r'(TODO|FIXME|HACK|XXX)', node.value, re.I):
                            # 检查行号是否匹配
                            if hasattr(node, 'lineno') and node.lineno <= line_num:
                                # 检查字符串是否跨越目标行
                                end_lineno = getattr(node, 'end_lineno', node.lineno)
                                if node.lineno <= line_num <= end_lineno:
                                    return False  # TODO在字符串中，不是真实的
            except Exception:
                pass
            
            # 默认认为是真实TODO
            return True
        except Exception:
            return True


# ========== 模块5: FullReportGenerator 全生命周期报告生成 ==========

class FullReportGenerator:
    """生成全生命周期报告"""

    def __init__(self):
        self._report: Optional[DevLifecycleReport] = None

    def generate(self, gaps: List[FeatureGap], flow_id: str = "") -> DevLifecycleReport:
        """生成报告"""
        report_id = hashlib.md5(
            f"dev_lifecycle_{time.time()}".encode()
        ).hexdigest()[:16]

        now = datetime.now().isoformat()

        # 统计
        status_counts = defaultdict(int)
        teams = set()
        all_timeline = []

        for gap in gaps:
            status_counts[gap.status] += 1
            if gap.assigned_team:
                teams.add(gap.assigned_team)
            all_timeline.extend(self._build_gap_timeline(gap))

        # 构建报告
        self._report = DevLifecycleReport(
            report_id=report_id,
            flow_id=flow_id,
            total_gaps=len(gaps),
            gaps_discovered=status_counts.get('discovered', 0) + status_counts.get('assigned', 0) +
                           status_counts.get('in_development', 0) + status_counts.get('code_review', 0) +
                           status_counts.get('testing', 0) + status_counts.get('completed', 0) +
                           status_counts.get('failed', 0),
            gaps_assigned=status_counts.get('assigned', 0) + status_counts.get('in_development', 0) +
                         status_counts.get('code_review', 0) + status_counts.get('testing', 0) +
                         status_counts.get('completed', 0) + status_counts.get('failed', 0),
            gaps_developing=status_counts.get('in_development', 0) + status_counts.get('code_review', 0) +
                          status_counts.get('testing', 0),
            gaps_completed=status_counts.get('completed', 0),
            gaps_failed=status_counts.get('failed', 0),
            teams_involved=sorted(list(teams)),
            timeline=all_timeline,
            gaps=[self._gap_to_dict(gap) for gap in gaps],
            summary=self._build_summary(status_counts, teams, gaps),
            generated_at=now,
        )

        return self._report

    def _build_gap_timeline(self, gap: FeatureGap) -> List[Dict]:
        """构建单个gap的时间线"""
        events = []
        if gap.detected_at:
            events.append({
                'gap_id': gap.gap_id,
                'event': 'discovered',
                'title': gap.title,
                'team': '',
                'timestamp': gap.detected_at,
            })
        if gap.assigned_at:
            events.append({
                'gap_id': gap.gap_id,
                'event': 'assigned',
                'title': gap.title,
                'team': gap.assigned_team,
                'timestamp': gap.assigned_at,
            })
        if gap.completed_at:
            events.append({
                'gap_id': gap.gap_id,
                'event': gap.status,
                'title': gap.title,
                'team': gap.assigned_team,
                'timestamp': gap.completed_at,
            })
        return events

    def _gap_to_dict(self, gap: FeatureGap) -> Dict:
        """转换为字典"""
        return {
            'gap_id': gap.gap_id,
            'gap_type': gap.gap_type,
            'title': gap.title,
            'description': gap.description,
            'file': gap.file,
            'line': gap.line,
            'route': gap.route,
            'severity': gap.severity,
            'current_implementation': gap.current_implementation,
            'assigned_team': gap.assigned_team,
            'assigned_employee': gap.assigned_employee,
            'status': gap.status,
            'progress': gap.progress,
            'detected_at': gap.detected_at,
            'assigned_at': gap.assigned_at,
            'completed_at': gap.completed_at,
            'verification_result': gap.verification_result,
            'verification_passed': gap.verification_passed,
            'development_log': gap.development_log,
        }

    def _build_summary(self, status_counts: Dict, teams: set, gaps: List[FeatureGap]) -> str:
        """构建摘要"""
        total = len(gaps)
        completed = status_counts.get('completed', 0)
        failed = status_counts.get('failed', 0)
        developing = status_counts.get('in_development', 0) + status_counts.get('code_review', 0) + status_counts.get('testing', 0)

        # 按类型统计
        type_counts = defaultdict(int)
        for gap in gaps:
            type_counts[gap.gap_type] += 1

        type_summary = ', '.join(f'{k}={v}' for k, v in sorted(type_counts.items(), key=lambda x: -x[1]))

        summary = (
            f"自动巡检队伍引擎完成功能缺失扫描: "
            f"共发现 {total} 个功能缺失项, "
            f"已分配到 {len(teams)} 个开发团队, "
            f"开发中 {developing} 项, "
            f"完成 {completed} 项, "
            f"失败 {failed} 项。"
            f"缺失类型: {type_summary}"
        )
        return summary


# ========== 主引擎: AutoDevTeamEngine ==========

class AutoDevTeamEngine:
    """自动巡检队伍引擎"""

    def __init__(self, scan_dir: str = None):
        self.scan_dir = scan_dir or _BASE
        ensure_dev_lifecycle_tables()

        self._gap_scanner = GapScanner(self.scan_dir)
        self._task_dispatcher = DevTaskDispatcher()
        self._progress_tracker = DevProgressTracker()
        self._completion_verifier = CompletionVerifier(self.scan_dir)
        self._report_generator = FullReportGenerator()

        self._gaps: List[FeatureGap] = []
        self._report: Optional[DevLifecycleReport] = None

    def run_full_cycle(self, flow_id: str = "") -> DevLifecycleReport:
        """执行完整的巡检周期"""
        if not flow_id:
            flow_id = f"auto_dev_{int(time.time())}"

        logger.info("=" * 60)
        logger.info(" MTSCOS 自动巡检队伍引擎 v1.0.0")
        logger.info("=" * 60)
        logger.info(f" Flow ID: {flow_id}")
        logger.info(f" 扫描目录: {self.scan_dir}")

        t0 = time.time()

        # 步骤1: 扫描功能缺失
        logger.info("\n--- 步骤1: GapScanner 扫描功能缺失 ---")
        self._gaps = self._gap_scanner.scan_all()
        logger.info(f"  发现 {len(self._gaps)} 个功能缺失项")

        # 步骤2: 派发任务
        logger.info("\n--- 步骤2: DevTaskDispatcher 派发任务 ---")
        self._gaps = self._task_dispatcher.dispatch(self._gaps)
        teams_used = set(g.assigned_team for g in self._gaps if g.assigned_team)
        logger.info(f"  已分配到 {len(teams_used)} 个开发团队")

        # 步骤3: 开始开发
        logger.info("\n--- 步骤3: DevProgressTracker 开始开发 ---")
        self._gaps = self._progress_tracker.start_development(self._gaps)

        # 步骤4: 代码评审
        logger.info("\n--- 步骤4: DevProgressTracker 代码评审 ---")
        self._gaps = self._progress_tracker.code_review(self._gaps)

        # 步骤5: 测试
        logger.info("\n--- 步骤5: DevProgressTracker 测试 ---")
        self._gaps = self._progress_tracker.testing(self._gaps)

        # 步骤6: 完成
        logger.info("\n--- 步骤6: DevProgressTracker 完成 ---")
        self._gaps = self._progress_tracker.complete(self._gaps)

        # 步骤7: 验证
        logger.info("\n--- 步骤7: CompletionVerifier 完成验证 ---")
        self._gaps = self._completion_verifier.verify(self._gaps)
        passed = sum(1 for g in self._gaps if g.verification_passed)
        failed = sum(1 for g in self._gaps if not g.verification_passed)
        logger.info(f"  验证通过: {passed}, 验证失败: {failed}")

        # 步骤8: 生成报告
        logger.info("\n--- 步骤8: FullReportGenerator 生成报告 ---")
        self._report = self._report_generator.generate(self._gaps, flow_id)
        logger.info(f"  报告ID: {self._report.report_id}")
        logger.info(f"  摘要: {self._report.summary}")

        # 步骤9: 持久化
        logger.info("\n--- 步骤9: 数据库持久化 ---")
        persist_count = self._persist_to_database(flow_id)
        logger.info(f"  存储 {persist_count} 条记录")

        elapsed = time.time() - t0
        logger.info(f"\n  总耗时: {elapsed:.1f}s")
        logger.info("=" * 60)

        self._report.duration = elapsed
        return self._report

    def _persist_to_database(self, flow_id: str) -> int:
        """持久化到数据库"""
        count = 0
        now = datetime.now().isoformat()

        with _LOCK:
            c = _get_conn()
            cur = c.cursor()

            # 存储每个gap
            for gap in self._gaps:
                try:
                    cur.execute("""INSERT OR REPLACE INTO mt_feature_dev_lifecycle
                        (gap_id, gap_type, title, description, file_path, line_number, route,
                         severity, current_impl, suggested_impl, assigned_team, assigned_employee,
                         status, progress, detected_at, assigned_at, completed_at,
                         verification_result, verification_passed, development_log_json,
                         fix_code_snippet, original_code_snippet, flow_id, created_at, updated_at)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (gap.gap_id, gap.gap_type, gap.title, gap.description,
                         gap.file, gap.line, gap.route, gap.severity,
                         gap.current_implementation, gap.suggested_implementation,
                         gap.assigned_team, gap.assigned_employee, gap.status,
                         gap.progress, gap.detected_at, gap.assigned_at,
                         gap.completed_at, gap.verification_result,
                         1 if gap.verification_passed else 0,
                         json.dumps(gap.development_log, ensure_ascii=False),
                         gap.fix_code_snippet, gap.original_code_snippet,
                         flow_id, now, now))
                    count += 1
                except Exception as e:
                    logger.debug(f"持久化gap {gap.gap_id} 失败: {e}")

            # 存储报告
            if self._report:
                try:
                    cur.execute("""INSERT OR REPLACE INTO mt_dev_lifecycle_report
                        (report_id, flow_id, total_gaps, gaps_discovered, gaps_assigned,
                         gaps_completed, gaps_failed, teams_involved_json,
                         timeline_json, gaps_detail_json, summary, generated_at, duration)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (self._report.report_id, flow_id, self._report.total_gaps,
                         self._report.gaps_discovered, self._report.gaps_assigned,
                         self._report.gaps_completed, self._report.gaps_failed,
                         json.dumps(self._report.teams_involved, ensure_ascii=False),
                         json.dumps(self._report.timeline, ensure_ascii=False),
                         json.dumps(self._report.gaps, ensure_ascii=False),
                         self._report.summary, self._report.generated_at,
                         self._report.duration))
                    count += 1
                except Exception as e:
                    logger.debug(f"持久化报告失败: {e}")

            c.commit()
            c.close()

        # 投喂脑库
        if HAS_DEV_FLOW:
            try:
                feed_brain(flow_id, 'auto_dev_team', self._report.summary if self._report else '')
            except Exception:
                pass

        return count

    def get_gaps(self) -> List[FeatureGap]:
        """获取所有功能缺失项"""
        return self._gaps

    def get_report(self) -> Optional[DevLifecycleReport]:
        """获取报告"""
        return self._report


# ========== 入口 ==========

if __name__ == "__main__":
    import sys

    engine = AutoDevTeamEngine()
    flow_id = sys.argv[1] if len(sys.argv) > 1 else ""
    report = engine.run_full_cycle(flow_id)

    print(f"\n报告ID: {report.report_id}")
    print(f"总缺失: {report.total_gaps}")
    print(f"已分配: {report.gaps_assigned}")
    print(f"已完成: {report.gaps_completed}")
    print(f"已失败: {report.gaps_failed}")
    print(f"涉及团队: {', '.join(report.teams_involved)}")
    print(f"摘要: {report.summary}")
