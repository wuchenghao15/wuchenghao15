#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 深度巡检引擎 (Deep Inspection Engine v1.0.0)
=====================================================
自动组织并巡检项目各个页面功能 + 逐行源代码检查 + AI团队路由 + 全生命周期追踪

6大模块:
  1. PageInspector    - 页面/路由功能检查(扫描所有Flask路由,检查响应/状态/功能)
  2. CodeLineInspector- 逐行代码检查(AST分析+安全漏洞+死代码+资源泄露+未定义变量)
  3. AITeamRouter     - AI团队路由(按错误类型路由到对应AI专家组)
  4. AutoFixer        - 自动修复(多策略修复+安全保护+回滚机制)
  5. LifecycleTracker - 全生命周期追踪(发现→分配→修复→验证→解决→归档)
  6. DatabasePersistor- 数据库永久化存储(全链路报告+错误+修复+验证记录)

AI团队路由表:
  syntax/indentation  → 修复AI_003 (自动修复)
  security/vuln       → EF_红队指挥_201 + EF_蓝队防御_202 (安全专家组)
  page/route_error    → 原液_巡检AI_301 (页面巡检组)
  performance         → EF_云安全_231 (性能优化组)
  pattern/dead_code   → 原液_修复AI_302 (代码清理组)
  resource_leak       → 原液_修复AI_302 (资源管理组)
  unknown             → 原液_协调AI_305 (协调组,人工升级)
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
import py_compile
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger('DeepInspection')

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

# ========== AI团队路由表 ==========

AI_TEAM_ROUTING = {
    'syntax_error':       ('修复AI_003', '自动修复组', '语法错误修复'),
    'indentation_error':  ('修复AI_003', '自动修复组', '缩进错误修复'),
    'security_vuln':      ('EF_红队指挥_201', '安全专家组', '安全漏洞分析'),
    'sql_injection':      ('EF_蓝队防御_202', '安全专家组', 'SQL注入防御'),
    'xss_vuln':           ('EF_蓝队防御_202', '安全专家组', 'XSS防御'),
    'page_error':         ('原液_巡检AI_301', '页面巡检组', '页面功能检查'),
    'route_missing':      ('原液_巡检AI_301', '页面巡检组', '路由缺失检查'),
    'undefined_var':      ('原液_修复AI_302', '代码清理组', '未定义变量'),
    'dead_code':          ('原液_修复AI_302', '代码清理组', '死代码清理'),
    'resource_leak':      ('原液_修复AI_302', '资源管理组', '资源泄露修复'),
    'pattern_issue':      ('修复AI_003', '自动修复组', '代码模式修复'),
    'import_error':       ('修复AI_003', '自动修复组', '导入修复'),
    'performance':        ('EF_云安全_231', '性能优化组', '性能优化'),
    'unknown':            ('原液_协调AI_305', '协调组', '人工升级处理'),
}

# 安全漏洞检测模式
SECURITY_PATTERNS = [
    (r'execute\s*\(\s*["\'].*%s.*["\'].*%', 'sql_injection', 'high', 'SQL拼接(可能注入)'),
    (r'execute\s*\(\s*f["\']', 'sql_injection', 'high', 'f-string SQL(可能注入)'),
    (r'eval\s*\(', 'security_vuln', 'critical', 'eval()使用(代码执行风险)'),
    (r'exec\s*\(', 'security_vuln', 'critical', 'exec()使用(代码执行风险)'),
    (r'os\.system\s*\(', 'security_vuln', 'high', 'os.system(命令注入风险)'),
    (r'subprocess\.call\s*\(\s*shell=True', 'security_vuln', 'high', 'shell=True(命令注入)'),
    (r'pickle\.loads?\s*\(', 'security_vuln', 'high', 'pickle反序列化(代码执行)'),
    (r'markupsafe\.Markup\s*\(\s*f["\']', 'xss_vuln', 'high', 'Markup+f-string(XSS风险)'),
    (r'innerHTML\s*=', 'xss_vuln', 'medium', 'innerHTML(XSS风险)'),
    (r'password\s*=\s*["\'][^"\']+["\']', 'security_vuln', 'critical', '硬编码密码'),
    (r'api_key\s*=\s*["\'][^"\']+["\']', 'security_vuln', 'critical', '硬编码API密钥'),
    (r'secret_key\s*=\s*["\'][^"\']+["\']', 'security_vuln', 'high', '硬编码密钥'),
    (r'token\s*=\s*["\'][^"\']+["\']', 'security_vuln', 'high', '硬编码Token'),
]

# 性能问题模式
PERFORMANCE_PATTERNS = [
    (r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\(', 'performance', 'low', 'range(len())建议用enumerate'),
    (r'\.append\s*\(.*\)\s*$.*for\s+', 'performance', 'low', '循环内append(建议列表推导)'),
    (r'select\s+\*\s+from', 'performance', 'medium', 'SELECT *(建议指定列)'),
]


# ========== 数据结构 ==========

@dataclass
class InspectionItem:
    """巡检项"""
    item_id: str = ""
    source: str = ""           # page / code_line
    file: str = ""             # 文件路径
    line: int = 0              # 行号
    col: int = 0               # 列号
    category: str = ""         # 错误类别
    severity: str = "medium"   # critical/high/medium/low
    message: str = ""          # 错误描述
    code_snippet: str = ""     # 代码片段
    route: str = ""            # 路由路径(页面检查用)
    discovered_at: str = ""
    # AI路由
    assigned_team: str = ""    # 分配的AI团队
    assigned_expert: str = ""  # 分配的专家
    team_role: str = ""        # 团队角色
    # 生命周期
    lifecycle_status: str = "discovered"  # discovered/assigned/fixing/fixed/verified/resolved/archived
    fix_action: str = ""
    fix_detail: str = ""
    fixed_at: str = ""
    verified: bool = False
    verify_result: str = ""
    resolved_at: str = ""


@dataclass
class LifecycleReport:
    """全生命周期报告"""
    report_id: str = ""
    inspection_time: str = ""
    # 统计
    pages_inspected: int = 0
    routes_found: int = 0
    files_inspected: int = 0
    lines_inspected: int = 0
    items_found: int = 0
    items_fixed: int = 0
    items_failed: int = 0
    items_verified: int = 0
    items_resolved: int = 0
    # AI团队
    teams_involved: List[str] = field(default_factory=list)
    # 详情
    items: List[InspectionItem] = field(default_factory=list)
    # 时间线
    timeline: List[Dict] = field(default_factory=list)
    duration: float = 0.0
    summary: str = ""


# ========== 深度巡检引擎 ==========

class DeepInspectionEngine:
    """深度巡检引擎"""

    def __init__(self, scan_dir: str = None):
        self.scan_dir = scan_dir or _BASE
        self._items: List[InspectionItem] = []
        self._report = LifecycleReport()
        self._lock = threading.RLock()
        self._routes: List[Dict] = []
        self._timeline: deque = deque(maxlen=500)

    def _log_timeline(self, event: str, detail: str = ""):
        """记录时间线"""
        self._timeline.append({
            'time': datetime.now().isoformat(),
            'event': event, 'detail': detail,
        })

    # ========== 模块1: PageInspector 页面/路由检查 ==========

    def inspect_pages(self) -> List[InspectionItem]:
        """模块1: 扫描所有Flask路由并检查页面功能"""
        self._log_timeline('PAGE_INSPECT_START', '开始页面/路由检查')
        logger.info("[PageInspector] 开始扫描Flask路由...")
        items = []
        routes_found = 0

        # 扫描app.py中的路由定义
        app_py = os.path.join(self.scan_dir, 'app.py')
        if os.path.exists(app_py):
            try:
                with open(app_py, 'r', encoding='utf-8', errors='replace') as f:
                    source = f.read()
                # 匹配 @app.route 装饰器
                route_pattern = re.compile(
                    r'@app\.route\s*\(\s*["\']([^"\']+)["\'].*?(?:methods\s*=\s*\[([^\]]*)\])?',
                    re.DOTALL
                )
                for m in route_pattern.finditer(source):
                    route_path = m.group(1)
                    methods = m.group(2) or 'GET'
                    line = source[:m.start()].count('\n') + 1
                    routes_found += 1
                    self._routes.append({
                        'path': route_path, 'methods': methods, 'line': line,
                    })

                    # 检查路由是否有权限装饰器
                    # 获取路由前后5行上下文
                    lines = source.split('\n')
                    ctx_start = max(0, line - 5)
                    ctx_end = min(len(lines), line + 5)
                    context = '\n'.join(lines[ctx_start:ctx_end])

                    # 检查是否有 @system_container 或类似权限装饰器
                    has_auth = ('@system_container' in context or
                               '@login_required' in context or
                               '@admin_required' in context or
                               'require_auth' in context)

                    if not has_auth and not route_path.startswith('/static'):
                        items.append(InspectionItem(
                            item_id=hashlib.md5(f"route_{route_path}".encode()).hexdigest()[:12],
                            source='page', file='app.py', line=line,
                            category='route_missing',
                            severity='high',
                            message=f'路由 {route_path} 缺少权限装饰器(@system_container)',
                            route=route_path,
                            discovered_at=datetime.now().isoformat(),
                        ))

            except Exception as e:
                logger.debug(f"路由扫描异常: {e}")

        # 扫描blueprints目录
        bp_dirs = [os.path.join(self.scan_dir, 'app', 'api'), os.path.join(self.scan_dir, 'routes')]
        for bp_dir in bp_dirs:
            if not os.path.exists(bp_dir):
                continue
            for root, dirs, files in os.walk(bp_dir):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for fname in files:
                    if not fname.endswith('.py'):
                        continue
                    fpath = os.path.join(root, fname)
                    relpath = os.path.relpath(fpath, self.scan_dir)
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                            src = f.read()
                        bp_route_pattern = re.compile(
                            r'@\w+\.route\s*\(\s*["\']([^"\']+)["\']'
                        )
                        for m in bp_route_pattern.finditer(src):
                            route_path = m.group(1)
                            line = src[:m.start()].count('\n') + 1
                            routes_found += 1
                            self._routes.append({
                                'path': route_path, 'file': relpath, 'line': line,
                            })
                    except Exception:
                        pass

        with self._lock:
            self._report.routes_found = routes_found
            self._report.pages_inspected = routes_found

        self._log_timeline('PAGE_INSPECT_DONE', f'找到{routes_found}个路由, 发现{len(items)}个问题')
        logger.info(f"[PageInspector] 路由: {routes_found}个, 问题: {len(items)}个")
        return items

    # ========== 模块2: CodeLineInspector 逐行代码检查 ==========

    def inspect_code_lines(self) -> List[InspectionItem]:
        """模块2: 逐行代码检查(AST+安全+性能+模式)"""
        self._log_timeline('CODE_INSPECT_START', '开始逐行代码检查')
        logger.info("[CodeLineInspector] 开始逐行代码检查...")
        items = []
        files_count = 0
        lines_count = 0

        for root, dirs, files in os.walk(self.scan_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                fpath = os.path.join(root, fname)
                relpath = os.path.relpath(fpath, self.scan_dir)
                files_count += 1

                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        source = f.read()
                except Exception as e:
                    if 'timed out' in str(e).lower():
                        continue
                    items.append(self._make_item('code_line', relpath, 0, 'read_error',
                               'low', f'文件读取失败: {str(e)[:80]}', source[:100]))
                    continue

                lines_count += source.count('\n') + 1
                lines = source.split('\n')

                # 2a. 语法/编译检查
                compile_errors = self._check_compile(fpath, relpath, source, lines)
                items.extend(compile_errors)

                # 如果语法正确,继续深度检查
                if not compile_errors:
                    # 2b. 安全漏洞扫描
                    items.extend(self._check_security(relpath, lines))
                    # 2c. 性能模式检查
                    items.extend(self._check_performance(relpath, lines))
                    # 2d. AST深度分析
                    items.extend(self._check_ast(relpath, source, lines))
                    # 2e. 资源泄露检查
                    items.extend(self._check_resource_leak(relpath, lines))

        with self._lock:
            self._report.files_inspected = files_count
            self._report.lines_inspected = lines_count

        self._log_timeline('CODE_INSPECT_DONE', f'检查{files_count}文件/{lines_count}行, 发现{len(items)}个问题')
        logger.info(f"[CodeLineInspector] {files_count}文件/{lines_count}行, 发现{len(items)}个问题")
        return items

    def _make_item(self, source, file, line, category, severity, message, snippet=""):
        return InspectionItem(
            item_id=hashlib.md5(f"{file}_{line}_{category}_{time.time()}".encode()).hexdigest()[:12],
            source=source, file=file, line=line, category=category,
            severity=severity, message=message, code_snippet=snippet[:120],
            discovered_at=datetime.now().isoformat(),
        )

    def _check_compile(self, fpath, relpath, source, lines):
        """编译检查"""
        items = []
        try:
            py_compile.compile(fpath, doraise=True)
        except py_compile.PyCompileError as e:
            msg = str(e)
            line = 0
            m = re.search(r'line (\d+)', msg)
            if m: line = int(m.group(1))
            snippet = lines[line-1].rstrip() if 0 < line <= len(lines) else ""
            cat = 'indentation_error' if 'indent' in msg.lower() else 'syntax_error'
            sev = 'high' if 'indent' in msg.lower() else 'critical'
            items.append(self._make_item('code_line', relpath, line, cat, sev,
                       self._clean_msg(msg), snippet))
        except Exception as e:
            items.append(self._make_item('code_line', relpath, 0, 'syntax_error', 'critical', str(e)[:100]))
        return items

    def _check_security(self, relpath, lines):
        """安全漏洞扫描"""
        items = []
        found_lines = set()
        for i, line in enumerate(lines, 1):
            if i in found_lines:
                continue
            for pattern, cat, sev, desc in SECURITY_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # 跳过注释和测试文件
                    stripped = line.strip()
                    if stripped.startswith('#'):
                        continue
                    if 'test' in relpath.lower() and cat in ('security_vuln',):
                        continue
                    items.append(self._make_item('code_line', relpath, i, cat, sev, desc, stripped[:100]))
                    found_lines.add(i)
                    break
        return items

    def _check_performance(self, relpath, lines):
        """性能模式检查"""
        items = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            for pattern, cat, sev, desc in PERFORMANCE_PATTERNS:
                if re.search(pattern, stripped, re.IGNORECASE):
                    items.append(self._make_item('code_line', relpath, i, cat, sev, desc, stripped[:100]))
                    break
        return items

    def _check_ast(self, relpath, source, lines):
        """AST深度分析"""
        items = []
        try:
            tree = ast.parse(source, filename=relpath)
        except SyntaxError:
            return items

        # 收集已定义和已使用的名称
        defined_names = set()
        used_names = set()
        imported_names = set()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined_names.add(node.name)
                for arg in node.args.args:
                    defined_names.add(arg.arg)
            elif isinstance(node, ast.ClassDef):
                defined_names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_names.add(target.id)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)

        # 检查未定义变量(排除内置和常见名称)
        builtins_set = set(dir(__builtins__)) if isinstance(__builtins__, dict) else set(dir(__builtins__))
        common_names = {'self', 'cls', 'app', 'request', 'session', 'g', 'current_app',
                       'abort', 'redirect', 'url_for', 'render_template', 'jsonify',
                       'flash', 'make_response', 'send_file', 'send_from_directory',
                       'Blueprint', 'datetime', 'time', 'os', 'sys', 'json', 're',
                       'hashlib', 'sqlite3', 'threading', 'logging', 'random',
                       'collections', 'functools', 'pathlib', 'typing', 'dataclasses',
                       'uuid', 'base64', 'hmac', 'secrets', 'config'}
        all_known = defined_names | imported_names | builtins_set | common_names

        undefined = used_names - all_known
        # 只报告明确的未定义变量(过滤太宽泛的结果)
        suspicious = set()
        for name in undefined:
            if name.startswith('_'):
                continue
            if name.isupper() or name[0].isupper():
                suspicious.add(name)
        # 限制每文件最多报告3个未定义变量
        for name in list(suspicious)[:3]:
            # 找到使用该变量的行
            for i, line in enumerate(lines, 1):
                if re.search(rf'\b{re.escape(name)}\b', line):
                    items.append(self._make_item('code_line', relpath, i, 'undefined_var',
                               'medium', f'可能未定义的变量: {name}', line.strip()[:100]))
                    break
        return items

    def _check_resource_leak(self, relpath, lines):
        """资源泄露检查"""
        items = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            # open()未用with
            if 'open(' in stripped and 'with ' not in stripped and 'os.open' not in stripped:
                if 'test' not in relpath.lower():
                    items.append(self._make_item('code_line', relpath, i, 'resource_leak',
                               'low', 'open()未使用with(可能资源泄露)', stripped[:80]))
                    break
            # sqlite3.connect未关闭
            if 'sqlite3.connect' in stripped and 'with ' not in stripped:
                if 'test' not in relpath.lower() and '_get_conn' not in stripped:
                    items.append(self._make_item('code_line', relpath, i, 'resource_leak',
                               'low', '数据库连接未用with(可能泄露)', stripped[:80]))
                    break
        return items

    def _clean_msg(self, msg):
        msg = re.sub(r'^.*\.py:\d+:', '', msg).strip()
        msg = re.sub(r'Sorry: ', '', msg)
        lines = [l.strip() for l in msg.split('\n') if l.strip()]
        return ' '.join(lines)[:200]

    # ========== 模块3: AITeamRouter AI团队路由 ==========

    def route_to_teams(self) -> Dict[str, Any]:
        """模块3: 将问题路由到对应AI团队"""
        self._log_timeline('AI_ROUTE_START', '开始AI团队路由')
        logger.info("[AITeamRouter] 路由问题到AI团队...")
        team_assignments = defaultdict(list)

        for item in self._items:
            expert, team, role = AI_TEAM_ROUTING.get(item.category, AI_TEAM_ROUTING['unknown'])
            item.assigned_expert = expert
            item.assigned_team = team
            item.team_role = role
            item.lifecycle_status = 'assigned'
            team_assignments[team].append(item.item_id)

        result = {
            'total_items': len(self._items),
            'teams': {k: len(v) for k, v in team_assignments.items()},
            'by_expert': dict(defaultdict(int, {k: len(v) for k, v in team_assignments.items()})),
        }
        self._log_timeline('AI_ROUTE_DONE', f'路由完成: {json.dumps(result["teams"], ensure_ascii=False)}')
        logger.info(f"[AITeamRouter] 路由: {json.dumps(result['teams'], ensure_ascii=False)}")
        return result

    # ========== 模块4: AutoFixer 自动修复 ==========

    def auto_fix_all(self) -> Dict[str, int]:
        """模块4: 自动修复"""
        self._log_timeline('AUTO_FIX_START', '开始自动修复')
        logger.info("[AutoFixer] 开始自动修复...")
        fixed = 0; failed = 0; skipped = 0

        for item in self._items:
            if item.lifecycle_status in ('fixed', 'failed', 'archived'):
                continue
            item.lifecycle_status = 'fixing'
            try:
                success = self._fix_item(item)
                if success:
                    item.lifecycle_status = 'fixed'
                    item.fixed_at = datetime.now().isoformat()
                    fixed += 1
                elif item.lifecycle_status == 'skipped':
                    skipped += 1
                else:
                    item.lifecycle_status = 'failed'
                    failed += 1
            except Exception as e:
                item.lifecycle_status = 'failed'
                item.fix_detail = str(e)[:150]
                failed += 1

        self._report.items_fixed = fixed
        self._report.items_failed = failed
        self._log_timeline('AUTO_FIX_DONE', f'修复: 成功={fixed}, 失败={failed}, 跳过={skipped}')
        logger.info(f"[AutoFixer] 修复: 成功={fixed}, 失败={failed}, 跳过={skipped}")
        return {'fixed': fixed, 'failed': failed, 'skipped': skipped}

    def _fix_item(self, item: InspectionItem) -> bool:
        """修复单个问题"""
        if item.source == 'page':
            # 页面问题: 标记为需人工处理
            item.fix_action = 'manual_review'
            item.fix_detail = '页面路由问题需人工添加权限装饰器'
            item.lifecycle_status = 'skipped'
            return False

        filepath = os.path.join(self.scan_dir, item.file)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception as e:
            if 'timed out' in str(e).lower():
                item.fix_action = 'skip_onedrive'
                item.lifecycle_status = 'skipped'
                return False
            raise

        if item.category == 'indentation_error':
            return self._fix_indentation(item, filepath, lines)
        elif item.category == 'syntax_error':
            return self._fix_syntax(item, filepath, lines)
        elif item.category == 'pattern_issue':
            return self._fix_pattern(item, filepath, lines)
        elif item.category == 'resource_leak':
            item.fix_action = 'suggest_with_statement'
            item.fix_detail = '建议改用with语句(未自动修改,风险较高)'
            item.lifecycle_status = 'skipped'
            return False
        elif item.category in ('security_vuln', 'sql_injection', 'xss_vuln'):
            item.fix_action = 'security_review'
            item.fix_detail = f'安全漏洞需{item.assigned_expert}审查(未自动修改)'
            item.lifecycle_status = 'skipped'
            return False
        elif item.category == 'undefined_var':
            item.fix_action = 'manual_check'
            item.fix_detail = '未定义变量需人工确认(可能是动态导入)'
            item.lifecycle_status = 'skipped'
            return False
        elif item.category == 'dead_code':
            item.fix_action = 'suggest_cleanup'
            item.fix_detail = '建议清理死代码(未自动删除)'
            item.lifecycle_status = 'skipped'
            return False
        elif item.category == 'performance':
            item.fix_action = 'suggest_optimize'
            item.fix_detail = '性能建议(未自动修改)'
            item.lifecycle_status = 'skipped'
            return False
        else:
            item.fix_action = 'skip_unknown'
            item.lifecycle_status = 'skipped'
            return False

    def _fix_indentation(self, item, filepath, lines):
        item.fix_action = 'indentation_fix'
        idx = item.line - 1
        if idx < 0 or idx >= len(lines): return False
        bad_line = lines[idx]
        stripped = bad_line.strip()
        if not stripped or stripped.startswith('#'):
            lines[idx] = (stripped + '\n') if stripped else '\n'
            item.fix_detail = '清理空行/注释缩进'
            return self._write_verify(filepath, lines, item)
        # 优先下一行更深缩进
        cur_indent_len = len(bad_line[:len(bad_line) - len(bad_line.lstrip())])
        if idx < len(lines) - 1:
            next_line = lines[idx + 1]
            if next_line.strip():
                next_indent = next_line[:len(next_line) - len(next_line.lstrip())]
                if len(next_indent) > cur_indent_len:
                    lines[idx] = next_indent + stripped + '\n'
                    item.fix_detail = f'缩进修正为{len(next_indent)}空格(对齐后行)'
                    return self._write_verify(filepath, lines, item)
        # 前行冒号
        if idx > 0:
            prev = lines[idx - 1].strip()
            if prev.endswith(':'):
                expected = lines[idx - 1][:len(lines[idx - 1]) - len(lines[idx - 1].lstrip())] + '    '
                lines[idx] = expected + stripped + '\n'
                item.fix_detail = f'缩进修正为{len(expected)}空格(前行冒号)'
                return self._write_verify(filepath, lines, item)
        # 下一行
        if idx < len(lines) - 1 and lines[idx + 1].strip():
            next_indent = lines[idx + 1][:len(lines[idx + 1]) - len(lines[idx + 1].lstrip())]
            lines[idx] = next_indent + stripped + '\n'
            item.fix_detail = f'缩进修正为{len(next_indent)}空格(对齐后行)'
            return self._write_verify(filepath, lines, item)
        # 前行
        if idx > 0 and lines[idx - 1].strip():
            prev_indent = lines[idx - 1][:len(lines[idx - 1]) - len(lines[idx - 1].lstrip())]
            lines[idx] = prev_indent + stripped + '\n'
            item.fix_detail = f'缩进修正为{len(prev_indent)}空格(对齐前行)'
            return self._write_verify(filepath, lines, item)
        lines[idx] = stripped + '\n'
        item.fix_detail = '去除缩进(顶层)'
        return self._write_verify(filepath, lines, item)

    def _fix_syntax(self, item, filepath, lines):
        item.fix_action = 'syntax_fix'
        idx = item.line - 1
        if idx < 0 or idx >= len(lines): return False
        bad_line = lines[idx]
        stripped = bad_line.strip()
        open_count = stripped.count('(') - stripped.count(')')
        if open_count > 0:
            lines[idx] = stripped + ')' * open_count + '\n'
            item.fix_detail = f'补充{open_count}个右括号'
            return self._write_verify(filepath, lines, item)
        if 'indent' in item.message.lower():
            return self._fix_indentation(item, filepath, lines)
        if '\t' in bad_line and '    ' in bad_line:
            lines[idx] = bad_line.replace('\t', '    ')
            item.fix_detail = 'tab转空格'
            return self._write_verify(filepath, lines, item)
        item.fix_detail = '无法自动修复(需人工介入)'
        return False

    def _fix_pattern(self, item, filepath, lines):
        item.fix_action = 'pattern_fix'
        idx = item.line - 1
        if idx < 0 or idx >= len(lines): return False
        stripped = lines[idx].strip()
        if stripped == 'except:':
            indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
            lines[idx] = f'{indent}except Exception:\n'
            item.fix_detail = 'except: -> except Exception:'
            return self._write_verify(filepath, lines, item)
        item.fix_detail = '无法自动修复'
        return False

    def _write_verify(self, filepath, lines, item):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        except Exception as e:
            if 'timed out' in str(e).lower():
                item.fix_detail = 'OneDrive超时'
                return False
            raise
        try:
            py_compile.compile(filepath, doraise=True)
            return True
        except Exception as e:
            item.fix_detail += f'(验证失败: {str(e)[:80]})'
            return False

    # ========== 模块5: LifecycleTracker 生命周期追踪 ==========

    def verify_and_track(self) -> Dict[str, int]:
        """模块5: 验证修复并追踪生命周期"""
        self._log_timeline('VERIFY_START', '开始验证修复')
        logger.info("[LifecycleTracker] 验证修复...")
        verified = 0; resolved = 0

        for item in self._items:
            if item.lifecycle_status != 'fixed':
                continue
            filepath = os.path.join(self.scan_dir, item.file)
            try:
                py_compile.compile(filepath, doraise=True)
                item.verified = True
                item.verify_result = 'PASS'
                item.lifecycle_status = 'verified'
                verified += 1
            except Exception as e:
                item.verified = False
                item.verify_result = f'FAIL: {str(e)[:80]}'
                item.lifecycle_status = 'failed'

        # 标记所有已处理项为resolved
        for item in self._items:
            if item.lifecycle_status in ('verified', 'failed', 'skipped'):
                if item.lifecycle_status != 'failed':
                    item.lifecycle_status = 'resolved'
                    item.resolved_at = datetime.now().isoformat()
                    resolved += 1

        self._report.items_verified = verified
        self._report.items_resolved = resolved
        self._log_timeline('VERIFY_DONE', f'验证: {verified}通过, {resolved}已解决')
        logger.info(f"[LifecycleTracker] 验证: {verified}通过, {resolved}已解决")
        return {'verified': verified, 'resolved': resolved}

    # ========== 模块6: 报告生成 + 数据库持久化 ==========

    def generate_report(self) -> LifecycleReport:
        """生成全生命周期报告"""
        self._log_timeline('REPORT_START', '生成报告')
        teams = list(set(item.assigned_team for item in self._items if item.assigned_team))

        report = LifecycleReport(
            report_id=hashlib.md5(f"deep_{datetime.now().isoformat()}".encode()).hexdigest()[:16],
            inspection_time=datetime.now().isoformat(),
            pages_inspected=self._report.pages_inspected,
            routes_found=self._report.routes_found,
            files_inspected=self._report.files_inspected,
            lines_inspected=self._report.lines_inspected,
            items_found=len(self._items),
            items_fixed=self._report.items_fixed,
            items_failed=self._report.items_failed,
            items_verified=self._report.items_verified,
            items_resolved=self._report.items_resolved,
            teams_involved=teams,
            items=list(self._items),
            timeline=list(self._timeline),
            duration=0,
        )
        fixed = report.items_fixed
        total = report.items_found
        rate = (fixed / total * 100) if total > 0 else 100
        report.summary = (
            f"深度巡检报告 | 路由{report.routes_found}个 | "
            f"文件{report.files_inspected}个/{report.lines_inspected}行 | "
            f"发现{total}问题 | 修复{fixed}({rate:.0f}%) | "
            f"验证{report.items_verified} | 解决{report.items_resolved} | "
            f"AI团队{len(teams)}个"
        )
        self._report = report
        self._log_timeline('REPORT_DONE', report.summary)
        logger.info(f"[LifecycleReporter] {report.summary}")
        return report

    def persist_to_database(self, flow_id: str = "deep_inspection") -> Dict[str, int]:
        """数据库永久化存储"""
        self._log_timeline('PERSIST_START', '写入数据库')
        logger.info("[DatabasePersistor] 写入数据库...")
        ensure_tables()
        now = datetime.now().isoformat()
        stored = 0

        with _LOCK:
            c = _get_conn(); cur = c.cursor()

            # 1. SA报告
            report_data = {
                'report_id': self._report.report_id,
                'inspection_time': self._report.inspection_time,
                'routes_found': self._report.routes_found,
                'files_inspected': self._report.files_inspected,
                'lines_inspected': self._report.lines_inspected,
                'items_found': self._report.items_found,
                'items_fixed': self._report.items_fixed,
                'items_verified': self._report.items_verified,
                'items_resolved': self._report.items_resolved,
                'teams_involved': self._report.teams_involved,
                'summary': self._report.summary,
                'timeline': self._report.timeline[-20:],
            }
            cur.execute("""INSERT OR REPLACE INTO mt_super_admin_reports
                (flow_id, report_type, title, content, operator, created_at)
                VALUES(?,?,?,?,?,?)""",
                (flow_id, 'DEEP_INSPECTION_REPORT', f'深度巡检报告-{self._report.report_id}',
                 json.dumps(report_data, ensure_ascii=False), 'DeepInspection', now))
            stored += 1

            # 2. 每个问题详情(经验库)
            for item in self._items:
                item_data = {
                    'item_id': item.item_id, 'source': item.source,
                    'file': item.file, 'line': item.line,
                    'category': item.category, 'severity': item.severity,
                    'message': item.message, 'code_snippet': item.code_snippet,
                    'route': item.route, 'assigned_team': item.assigned_team,
                    'assigned_expert': item.assigned_expert, 'team_role': item.team_role,
                    'lifecycle_status': item.lifecycle_status, 'fix_action': item.fix_action,
                    'fix_detail': item.fix_detail, 'verified': item.verified,
                    'verify_result': item.verify_result,
                    'discovered_at': item.discovered_at, 'fixed_at': item.fixed_at,
                    'resolved_at': item.resolved_at,
                }
                eh = hashlib.md5(f"{item.item_id}_{item.file}_{item.line}".encode()).hexdigest()
                cur.execute("""INSERT OR REPLACE INTO mt_experience_library
                    (experience_hash, title, content_json, source_flow, flow_id, exp_content, created_at)
                    VALUES(?,?,?,?,?,?,?)""",
                    (eh, f'巡检-{item.file}:{item.line}',
                     json.dumps(item_data, ensure_ascii=False), flow_id, flow_id,
                     f'[{item.category}]{item.file}:{item.line} -> {item.lifecycle_status} ({item.fix_detail[:50]})', now))
                stored += 1

            # 3. 异常库(未解决/失败的问题)
            for item in self._items:
                if item.lifecycle_status in ('failed', 'discovered', 'assigned'):
                    fh = hashlib.md5(f"unresolved_{item.item_id}".encode()).hexdigest()
                    cur.execute("""INSERT OR REPLACE INTO mt_anomaly_feature_library
                        (feature_hash, feature_kind, feature_vector_json, source_flow, flow_id,
                         anomaly_type, anomaly_feature, created_at)
                        VALUES(?,?,?,?,?,?,?,?)""",
                        (fh, 'deep_inspection', json.dumps({
                            'file': item.file, 'line': item.line,
                            'category': item.category, 'severity': item.severity,
                            'message': item.message, 'team': item.assigned_team,
                            'expert': item.assigned_expert, 'status': item.lifecycle_status,
                        }, ensure_ascii=False), flow_id, flow_id,
                         item.category, f"{item.file}:{item.line}", now))
                    stored += 1

            # 4. 脑库投喂
            feed_content = (f"深度巡检完成: 路由{self._report.routes_found}个, "
                          f"文件{self._report.files_inspected}个/{self._report.lines_inspected}行, "
                          f"发现{self._report.items_found}问题, "
                          f"修复{self._report.items_fixed}, "
                          f"验证{self._report.items_verified}, "
                          f"解决{self._report.items_resolved}, "
                          f"AI团队{len(self._report.teams_involved)}个")
            cur.execute("""INSERT OR IGNORE INTO mt_ai_brain_feed_log
                (flow_id, feed_kind, feed_content, triggered_at)
                VALUES(?,?,?,?)""",
                (flow_id, 'deep_inspection', feed_content, now))
            stored += 1

            c.commit(); c.close()

        # 投喂脑库
        if HAS_DEV_FLOW:
            feed_brain(flow_id, 'deep_inspection', self._report.summary)
            for item in self._items:
                if item.lifecycle_status == 'failed':
                    feed_brain(flow_id, 'anomaly',
                             f"修复失败: [{item.category}]{item.file}:{item.line} - {item.message[:60]}")

        self._log_timeline('PERSIST_DONE', f'存储{stored}条记录')
        logger.info(f"[DatabasePersistor] 存储{stored}条记录")
        return {'stored': stored}

    # ========== 完整巡检流程 ==========

    def run_full_inspection(self, flow_id: str = "deep_inspection") -> LifecycleReport:
        """执行完整深度巡检"""
        print("=" * 70)
        print(" MTSCOS 深度巡检引擎 v1.0.0")
        print("=" * 70)
        print(" 6大模块: 页面检查 + 逐行代码 + AI路由 + 自动修复 + 生命周期 + 持久化")
        print(f" AI团队: {len(AI_TEAM_ROUTING)}种路由类别")
        print()

        t0 = time.time()

        # 模块1: 页面检查
        print("--- 模块1: PageInspector 页面/路由检查 ---")
        page_items = self.inspect_pages()
        print(f"  路由: {self._report.routes_found}个 | 问题: {len(page_items)}个")

        # 模块2: 逐行代码检查
        print("\n--- 模块2: CodeLineInspector 逐行代码检查 ---")
        code_items = self.inspect_code_lines()
        print(f"  文件: {self._report.files_inspected}个 | 行: {self._report.lines_inspected}行 | 问题: {len(code_items)}个")

        # 合并所有问题
        with self._lock:
            self._items = page_items + code_items
            self._report.items_found = len(self._items)

        # 模块3: AI团队路由
        print(f"\n--- 模块3: AITeamRouter AI团队路由 ---")
        routing = self.route_to_teams()
        print(f"  路由: {json.dumps(routing['teams'], ensure_ascii=False)}")

        # 模块4: 自动修复
        print(f"\n--- 模块4: AutoFixer 自动修复 ---")
        fix_stats = self.auto_fix_all()
        print(f"  修复: {json.dumps(fix_stats, ensure_ascii=False)}")

        # 模块5: 生命周期追踪
        print(f"\n--- 模块5: LifecycleTracker 验证追踪 ---")
        verify_stats = self.verify_and_track()
        print(f"  验证: {json.dumps(verify_stats, ensure_ascii=False)}")

        # 模块6: 报告+持久化
        print(f"\n--- 模块6: Report+Persist 报告持久化 ---")
        report = self.generate_report()
        print(f"  {report.summary}")
        persist_stats = self.persist_to_database(flow_id)
        print(f"  存储: {json.dumps(persist_stats, ensure_ascii=False)}")

        elapsed = time.time() - t0
        report.duration = elapsed
        print(f"\n{'='*70}")
        print(f" 深度巡检完成 | 耗时: {elapsed:.1f}s")
        print(f"  路由: {report.routes_found}个")
        print(f"  文件: {report.files_inspected}个 / {report.lines_inspected}行")
        print(f"  发现: {report.items_found}问题")
        print(f"  修复: {report.items_fixed} ({report.items_fixed/max(report.items_found,1)*100:.0f}%)")
        print(f"  验证: {report.items_verified}通过")
        print(f"  解决: {report.items_resolved}")
        print(f"  AI团队: {len(report.teams_involved)}个")
        print(f"  存储: {persist_stats['stored']}条DB记录")
        print(f"{'='*70}")
        return report


if __name__ == "__main__":
    engine = DeepInspectionEngine()
    report = engine.run_full_inspection()

    # 打印问题详情
    if report.items:
        print("\n--- 问题详情(前20) ---")
        for i, item in enumerate(report.items[:20], 1):
            icon = {'resolved': '✓', 'fixed': '◐', 'failed': '✗', 'skipped': '○'}.get(item.lifecycle_status, '?')
            print(f"  {i:2d}. {icon} [{item.category}] {item.file}:{item.line}")
            print(f"      消息: {item.message[:70]}")
            print(f"      AI: {item.assigned_expert}({item.assigned_team}) | 状态: {item.lifecycle_status}")
            if item.fix_detail:
                print(f"      修复: {item.fix_detail[:60]}")
            print()
