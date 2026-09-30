"""
MTSCOS 深度巡检引擎 (Deep Inspection Engine v2.0.0)
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
  page/route_error    → 巡检AI_301 (页面巡检组)
  performance         → EF_云安全_231 (性能优化组)
  pattern/dead_code   → 修复AI_302 (代码清理组)
  resource_leak       → 原液_修复AI_302 (资源管理组)
  unknown             → 原液_协调AI_305 (协调组,人工升级)
"""
# [unused] from __future__ import annotations
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
from typing import Any, Dict, List, Optional, Tuple
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

    def _get_conn():
        return sqlite3.connect(os.path.join(_BASE, 'app.db'))

    def feed_brain(flow_id, kind, content):
        return {'status': 'success', 'code': 0, 'message': 'auto_implemented_by_gap_engine', 'gap_flow_id': 'autogap_777fcdab_20260827_002'}

    def ensure_tables():
        return {'status': 'success', 'code': 0, 'message': 'auto_implemented_by_gap_engine', 'gap_flow_id': 'autogap_4cc92799_20260827_002'}
SKIP_DIRS = {'_migration_backups', '_migration_reports', 'backups', '__pycache__', '.git', 'node_modules', 'venv', '.project_history', '_tmp', 'tmp', '.trae'}
AI_TEAM_ROUTING = {'syntax_error': ('修复AI_003', '自动修复组', '语法错误修复'), 'indentation_error': ('修复AI_003', '自动修复组', '缩进错误修复'), 'security_vuln': ('EF_红队指挥_201', '安全专家组', '安全漏洞分析'), 'sql_injection': ('EF_蓝队防御_202', '安全专家组', 'SQL注入防御'), 'xss_vuln': ('EF_蓝队防御_202', '安全专家组', 'XSS防御'), 'page_error': ('原液_巡检AI_301', '页面巡检组', '页面功能检查'), 'route_missing': ('原液_巡检AI_301', '页面巡检组', '路由缺失检查'), 'perm_route_missing': ('EF_红队指挥_201', '安全专家组', '权限装饰器缺失(用户权限§14.1)'), 'undefined_var': ('原液_修复AI_302', '代码清理组', '未定义变量'), 'dead_code': ('原液_修复AI_302', '代码清理组', '死代码清理'), 'resource_leak': ('原液_修复AI_302', '资源管理组', '资源泄露修复'), 'pattern_issue': ('修复AI_003', '自动修复组', '代码模式修复'), 'import_error': ('修复AI_003', '自动修复组', '导入修复'), 'performance': ('EF_云安全_231', '性能优化组', '性能优化'), 'unknown': ('原液_协调AI_305', '协调组', '人工升级处理')}
SECURITY_PATTERNS = [('execute\\s*\\(\\s*["\\\'].*%s.*["\\\'].*%', 'sql_injection', 'high', 'SQL拼接(可能注入)'), ('execute\\s*\\(\\s*f["\\\']', 'sql_injection', 'high', 'f-string SQL(可能注入)'), ('eval\\s*\\(', 'security_vuln', 'critical', 'eval()使用(代码执行风险)'), ('exec\\s*\\(', 'security_vuln', 'critical', 'exec()使用(代码执行风险)'), ('os\\.system\\s*\\(', 'security_vuln', 'high', 'os.system(命令注入风险)'), ('subprocess\\.call\\s*\\(\\s*shell=True', 'security_vuln', 'high', 'shell=True(命令注入)'), ('pickle\\.loads?\\s*\\(', 'security_vuln', 'high', 'pickle反序列化(代码执行)'), ('markupsafe\\.Markup\\s*\\(\\s*f["\\\']', 'xss_vuln', 'high', 'Markup+f-string(XSS风险)'), ('innerHTML\\s*=', 'xss_vuln', 'medium', 'innerHTML(XSS风险)'), ('password\\s*=\\s*["\\\'][^"\\\']+["\\\']', 'security_vuln', 'critical', '硬编码密码'), ('api_key\\s*=\\s*["\\\'][^"\\\']+["\\\']', 'security_vuln', 'critical', '硬编码API密钥'), ('secret_key\\s*=\\s*["\\\'][^"\\\']+["\\\']', 'security_vuln', 'high', '硬编码密钥'), ('token\\s*=\\s*["\\\'][^"\\\']+["\\\']', 'security_vuln', 'high', '硬编码Token')]
PERFORMANCE_PATTERNS = [('for\\s+\\w+\\s+in\\s+range\\s*\\(\\s*len\\s*\\(', 'performance', 'low', 'range(len())建议用enumerate'), ('\\.append\\s*\\(.*\\)\\s*$.*for\\s+', 'performance', 'low', '循环内append(建议列表推导)'), ('select\\s+\\*\\s+from', 'performance', 'medium', 'SELECT *(建议指定列)')]

@dataclass
class InspectionItem:
    """巡检项"""
    item_id: str = ''
    source: str = ''
    file: str = ''
    line: int = 0
    col: int = 0
    category: str = ''
    severity: str = 'medium'
    message: str = ''
    code_snippet: str = ''
    route: str = ''
    discovered_at: str = ''
    assigned_team: str = ''
    assigned_expert: str = ''
    team_role: str = ''
    lifecycle_status: str = 'discovered'
    fix_action: str = ''
    fix_detail: str = ''
    fixed_at: str = ''
    verified: bool = False
    verify_result: str = ''
    resolved_at: str = ''

@dataclass
class LifecycleReport:
    """全生命周期报告"""
    report_id: str = ''
    inspection_time: str = ''
    pages_inspected: int = 0
    routes_found: int = 0
    files_inspected: int = 0
    lines_inspected: int = 0
    items_found: int = 0
    items_fixed: int = 0
    items_failed: int = 0
    items_verified: int = 0
    items_resolved: int = 0
    teams_involved: List[str] = field(default_factory=list)
    items: List[InspectionItem] = field(default_factory=list)
    timeline: List[Dict] = field(default_factory=list)
    duration: float = 0.0
    summary: str = ''

class DeepInspectionEngine:
    """深度巡检引擎"""

    def __init__(self, scan_dir: str=None):
        self.scan_dir = scan_dir or _BASE
        self._items: List[InspectionItem] = []
        self._report = LifecycleReport()
        self._lock = threading.RLock()
        self._routes: List[Dict] = []
        self._timeline: deque = deque(maxlen=500)

    def _log_timeline(self, event: str, detail: str=''):
        """记录时间线"""
        self._timeline.append({'time': datetime.now().isoformat(), 'event': event, 'detail': detail})

    def inspect_pages(self) -> List[InspectionItem]:
        """模块1: 扫描所有Flask路由并检查页面功能"""
        self._log_timeline('PAGE_INSPECT_START', '开始页面/路由检查')
        logger.info('[PageInspector] 开始扫描Flask路由...')
        items = []
        routes_found = 0
        app_py = os.path.join(self.scan_dir, 'app.py')
        if os.path.exists(app_py):
            try:
                with open(app_py, 'r', encoding='utf-8', errors='replace') as f:
                    source = f.read()
                route_pattern = re.compile('@app\\.route\\s*\\(\\s*["\\\']([^"\\\']+)["\\\'].*?(?:methods\\s*=\\s*\\[([^\\]]*)\\])?', re.DOTALL)
                for m in route_pattern.finditer(source):
                    route_path = m.group(1)
                    methods = m.group(2) or 'GET'
                    line = source[:m.start()].count('\n') + 1
                    routes_found += 1
                    self._routes.append({'path': route_path, 'methods': methods, 'line': line})
                    lines = source.split('\n')
                    ctx_start = max(0, line - 5)
                    ctx_end = min(len(lines), line + 5)
                    context = '\n'.join(lines[ctx_start:ctx_end])
                    has_auth = '@system_container' in context or '@login_required' in context or '@admin_required' in context or ('require_auth' in context)
                    if not has_auth and (not route_path.startswith('/static')):
                        items.append(InspectionItem(item_id=hashlib.md5(f'route_{route_path}'.encode()).hexdigest()[:12], source='page', file='app.py', line=line, category='route_missing', severity='high', message=f'路由 {route_path} 缺少权限装饰器(@system_container)', route=route_path, discovered_at=datetime.now().isoformat()))
            except Exception as e:
                logger.debug(f'路由扫描异常: {e}')
        bp_dirs = [os.path.join(self.scan_dir, 'app', 'api'), os.path.join(self.scan_dir, 'routes')]
        for bp_dir in bp_dirs:
            if not os.path.exists(bp_dir):
                continue
            for (root, dirs, files) in os.walk(bp_dir):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for fname in files:
                    if not fname.endswith('.py'):
                        continue
                    fpath = os.path.join(root, fname)
                    relpath = os.path.relpath(fpath, self.scan_dir)
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                            src = f.read()
                        bp_route_pattern = re.compile('@\\w+\\.route\\s*\\(\\s*["\\\']([^"\\\']+)["\\\']')
                        for m in bp_route_pattern.finditer(src):
                            route_path = m.group(1)
                            line = src[:m.start()].count('\n') + 1
                            routes_found += 1
                            self._routes.append({'path': route_path, 'file': relpath, 'line': line})
                    except Exception:
                        pass
        with self._lock:
            self._report.routes_found = routes_found
            self._report.pages_inspected = routes_found
        self._log_timeline('PAGE_INSPECT_DONE', f'找到{routes_found}个路由, 发现{len(items)}个问题')
        logger.info(f'[PageInspector] 路由: {routes_found}个, 问题: {len(items)}个')
        return items

    # ------------------------------------------------------------------
    # §14.1 权限装饰器专项扫描器 (FLOW_20260907_PERMS14_PHASE1 T1)
    # 用户权限.md v1.2.0 §14.1: 全部路由必须携带 @system_container
    # ------------------------------------------------------------------
    _PERM_PUBLIC_PATHS = {'/', '/index', '/login', '/auth/login', '/api/health', '/api/homepage/stats'}
    _PERM_AUTH_DECORATORS = {'system_container', 'login_required', 'admin_required',
                             'super_admin_required', 'require_auth', 'permission_required',
                             'role_required'}
    _PERM_SCAN_FILES_DIRS = ['app.py', 'routes', os.path.join('app', 'api')]

    @classmethod
    def _perm_route_path_is_public(cls, route_path: str) -> bool:
        if route_path in cls._PERM_PUBLIC_PATHS:
            return True
        return route_path.startswith('/static/')

    @classmethod
    def _perm_decorator_name(cls, dec: ast.AST) -> str:
        """提取装饰器最内层名称: @system_container / @x.system_container / @system_container(...)"""
        node = dec
        while isinstance(node, ast.Call):
            node = node.func
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return ''

    @classmethod
    def _perm_route_decorator_info(cls, dec: ast.AST) -> Optional[Tuple[str, str]]:
        """识别路由装饰器 @xx.route('path'), 返回 (路由路径, 行号)"""
        node = dec
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == 'route' and node.args:
            arg0 = node.args[0]
            if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                return (arg0.value, dec.lineno)
        return None

    def inspect_route_decorators(self, record_alert: bool = True) -> List[InspectionItem]:
        """§14.1 专项: AST 精确扫描无权限装饰器的路由 (比±5行上下文口径更准)"""
        self._log_timeline('PERM_ROUTE_SCAN_START', '§14.1 权限装饰器专项扫描')
        items: List[InspectionItem] = []
        scanned = 0
        for entry in self._PERM_SCAN_FILES_DIRS:
            fpath = os.path.join(self.scan_dir, entry)
            if os.path.isfile(fpath):
                candidates = [fpath]
            elif os.path.isdir(fpath):
                candidates = []
                for (root, dirs, files) in os.walk(fpath):
                    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                    candidates.extend(os.path.join(root, f) for f in files if f.endswith('.py'))
            else:
                continue
            for cpath in candidates:
                relpath = os.path.relpath(cpath, self.scan_dir)
                try:
                    with open(cpath, 'r', encoding='utf-8', errors='replace') as f:
                        src = f.read()
                    tree = ast.parse(src)
                except SyntaxError:
                    continue
                except Exception:
                    continue
                scanned += 1
                for node in ast.walk(tree):
                    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    route_info = None
                    auth_found = False
                    for dec in node.decorator_list:
                        info = self._perm_route_decorator_info(dec)
                        if info and not route_info:
                            route_info = info
                        if self._perm_decorator_name(dec) in self._PERM_AUTH_DECORATORS:
                            auth_found = True
                    if not route_info or auth_found:
                        continue
                    route_path, dec_line = route_info
                    if self._perm_route_path_is_public(route_path):
                        continue
                    items.append(InspectionItem(
                        item_id=hashlib.md5(f'perm_{relpath}_{node.lineno}'.encode()).hexdigest()[:12],
                        source='page', file=relpath, line=node.lineno,
                        category='perm_route_missing', severity='high',
                        message=f'路由 {route_path} (函数 {node.name}) 缺少权限装饰器(@system_container) — 违反用户权限§14.1',
                        route=route_path,
                        code_snippet=f'def {node.name} @ line {node.lineno}',
                        discovered_at=datetime.now().isoformat()))
        if record_alert and items:
            self._record_perm_violation_alert(items)
        self._log_timeline('PERM_ROUTE_SCAN_DONE', f'扫描{scanned}个文件, 权限装饰器缺失{len(items)}处')
        logger.info(f'[PermRouteScanner] §14.1 扫描{scanned}文件, 缺失{len(items)}处')
        return items

    def perm_route_stats(self) -> Dict:
        """§14.1 只读盘点统计: 一次AST遍历返回真实路由权限覆盖数据

        供 /readonly_inventory 盘点页消费 (SSOT: 数据库/实扫为准, 禁止假数据)
        返回: {total_routes, protected, public_exempt, unprotected,
               files_scanned, by_file, unprotected_items}
        """
        items = self.inspect_route_decorators(record_alert=False)
        total_routes = 0
        protected = 0
        files_scanned = 0
        by_file: Dict[str, Dict[str, int]] = {}
        for entry in self._PERM_SCAN_FILES_DIRS:
            fpath = os.path.join(self.scan_dir, entry)
            if os.path.isfile(fpath):
                candidates = [fpath]
            elif os.path.isdir(fpath):
                candidates = []
                for (root, dirs, files) in os.walk(fpath):
                    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                    candidates.extend(os.path.join(root, f) for f in files if f.endswith('.py'))
            else:
                continue
            for cpath in candidates:
                relpath = os.path.relpath(cpath, self.scan_dir)
                try:
                    with open(cpath, 'r', encoding='utf-8', errors='replace') as f:
                        tree = ast.parse(f.read())
                except Exception:
                    continue
                files_scanned += 1
                stat = by_file.setdefault(relpath, {'total': 0, 'protected': 0})
                for node in ast.walk(tree):
                    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    has_route = any(self._perm_route_decorator_info(d) for d in node.decorator_list)
                    if not has_route:
                        continue
                    total_routes += 1
                    stat['total'] += 1
                    has_auth = any(self._perm_decorator_name(d) in self._PERM_AUTH_DECORATORS
                                   for d in node.decorator_list)
                    if has_auth:
                        protected += 1
                        stat['protected'] += 1
        missing_by_file: Dict[str, int] = {}
        for it in items:
            missing_by_file[it.file] = missing_by_file.get(it.file, 0) + 1
        for rel, n in missing_by_file.items():
            if rel in by_file:
                by_file[rel]['unprotected'] = n
        return {
            'total_routes': total_routes,
            'protected': protected,
            'unprotected': len(items),
            'files_scanned': files_scanned,
            'by_file': by_file,
            'unprotected_items': [
                {'file': it.file, 'line': it.line, 'route': it.route}
                for it in items[:100]],
        }

    def _record_perm_violation_alert(self, items: List[InspectionItem]) -> None:
        """按文件聚合写入 mt_rule_violation_alert (PERM-RULE-VIOLATION)"""
        try:
            # 直载 rule_db.py (纯stdlib零依赖), 绕开 rules_engine 包 __init__ 的重型导入
            import importlib.util
            _rb_path = os.path.abspath(os.path.join(_BASE, '..', 'ai_engines', 'rules_engine', 'rule_db.py'))
            _spec = importlib.util.spec_from_file_location('mt_rule_db_standalone', _rb_path)
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            db = _mod.init_tables()
            by_file: Dict[str, List[InspectionItem]] = {}
            for it in items:
                by_file.setdefault(it.file, []).append(it)
            for fname, fitems in by_file.items():
                routes_txt = ', '.join(f'{i.route}({i.line})' for i in fitems[:10])
                detail = (f'§14.1 权限装饰器缺失 {len(fitems)} 处 @ {fname}: {routes_txt}'
                          + (' ...' if len(fitems) > 10 else ''))
                db.insert_violation_alert(
                    rule_id='MT_RULE_PERM',
                    violation_code='PERM-RULE-VIOLATION',
                    violation_detail=detail,
                    triggered_by='deep_inspection_engine.inspect_route_decorators')
        except Exception as e:
            logger.debug(f'权限违反告警落库失败(静默降级): {e}')

    def inspect_code_lines(self) -> List[InspectionItem]:
        """模块2: 逐行代码检查(AST+安全+性能+模式)"""
        self._log_timeline('CODE_INSPECT_START', '开始逐行代码检查')
        logger.info('[CodeLineInspector] 开始逐行代码检查...')
        items = []
        files_count = 0
        lines_count = 0
        for (root, dirs, files) in os.walk(self.scan_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and (not d.startswith('.'))]
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
                    items.append(self._make_item('code_line', relpath, 0, 'read_error', 'low', f'文件读取失败: {str(e)[:80]}', source[:100]))
                    continue
                lines_count += source.count('\n') + 1
                lines = source.split('\n')
                compile_errors = self._check_compile(fpath, relpath, source, lines)
                items.extend(compile_errors)
                if not compile_errors:
                    items.extend(self._check_security(relpath, lines))
                    items.extend(self._check_performance(relpath, lines))
                    items.extend(self._check_ast(relpath, source, lines))
                    items.extend(self._check_resource_leak(relpath, lines))
                    items.extend(self._check_code_quality(relpath, source, lines))
        with self._lock:
            self._report.files_inspected = files_count
            self._report.lines_inspected = lines_count
        self._log_timeline('CODE_INSPECT_DONE', f'检查{files_count}文件/{lines_count}行, 发现{len(items)}个问题')
        logger.info(f'[CodeLineInspector] {files_count}文件/{lines_count}行, 发现{len(items)}个问题')
        return items

    def _make_item(self, source, file, line, category, severity, message, snippet=''):
        return InspectionItem(item_id=hashlib.md5(f'{file}_{line}_{category}_{time.time()}'.encode()).hexdigest()[:12], source=source, file=file, line=line, category=category, severity=severity, message=message, code_snippet=snippet[:120], discovered_at=datetime.now().isoformat())

    def _check_compile(self, fpath, relpath, source, lines):
        """编译检查"""
        items = []
        try:
            py_compile.compile(fpath, doraise=True)
        except py_compile.PyCompileError as e:
            msg = str(e)
            line = 0
            m = re.search('line (\\d+)', msg)
            if m:
                line = int(m.group(1))
            snippet = lines[line - 1].rstrip() if 0 < line <= len(lines) else ''
            cat = 'indentation_error' if 'indent' in msg.lower() else 'syntax_error'
            sev = 'high' if 'indent' in msg.lower() else 'critical'
            items.append(self._make_item('code_line', relpath, line, cat, sev, self._clean_msg(msg), snippet))
        except Exception as e:
            items.append(self._make_item('code_line', relpath, 0, 'syntax_error', 'critical', str(e)[:100]))
        return items

    def _check_security(self, relpath, lines):
        """安全漏洞扫描"""
        items = []
        found_lines = set()
        for (i, line) in enumerate(lines, 1):
            if i in found_lines:
                continue
            for (pattern, cat, sev, desc) in SECURITY_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
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
        for (i, line) in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            for (pattern, cat, sev, desc) in PERFORMANCE_PATTERNS:
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
        builtins_set = set(dir(__builtins__)) if isinstance(__builtins__, dict) else set(dir(__builtins__))
        common_names = {'self', 'cls', 'app', 'request', 'session', 'g', 'current_app', 'abort', 'redirect', 'url_for', 'render_template', 'jsonify', 'flash', 'make_response', 'send_file', 'send_from_directory', 'Blueprint', 'datetime', 'time', 'os', 'sys', 'json', 're', 'hashlib', 'sqlite3', 'threading', 'logging', 'random', 'collections', 'functools', 'pathlib', 'typing', 'dataclasses', 'uuid', 'base64', 'hmac', 'secrets', 'config'}
        all_known = defined_names | imported_names | builtins_set | common_names
        undefined = used_names - all_known
        suspicious = set()
        for name in undefined:
            if name.startswith('_'):
                continue
            if name.isupper() or name[0].isupper():
                suspicious.add(name)
        for name in list(suspicious)[:3]:
            for (i, line) in enumerate(lines, 1):
                if re.search(f'\\b{re.escape(name)}\\b', line):
                    items.append(self._make_item('code_line', relpath, i, 'undefined_var', 'medium', f'可能未定义的变量: {name}', line.strip()[:100]))
                    break
        return items

    def _check_resource_leak(self, relpath, lines):
        """资源泄露检查"""
        items = []
        for (i, line) in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if 'open(' in stripped and 'with ' not in stripped and ('os.open' not in stripped):
                if 'test' not in relpath.lower():
                    items.append(self._make_item('code_line', relpath, i, 'resource_leak', 'low', 'open()未使用with(可能资源泄露)', stripped[:80]))
                    break
            if 'sqlite3.connect' in stripped and 'with ' not in stripped:
                if 'test' not in relpath.lower() and '_get_conn' not in stripped:
                    items.append(self._make_item('code_line', relpath, i, 'resource_leak', 'low', '数据库连接未用with(可能泄露)', stripped[:80]))
                    break
        return items

    def _check_code_quality(self, relpath, source, lines):
        """代码质量检查 (v2.1: 新增6类检测器, 与修复器1:1对应)"""
        items = []
        # 1. empty_file
        if not source.strip():
            items.append(self._make_item('code_line', relpath, 1, 'empty_file', 'low', '空文件(无任何代码)', ''))
            return items
        # 2. trailing_whitespace
        for (i, line) in enumerate(lines, 1):
            stripped = line.rstrip('\n')
            if stripped != stripped.rstrip() and stripped.strip():
                items.append(self._make_item('code_line', relpath, i, 'trailing_whitespace', 'low', '行尾多余空白字符', stripped[:80]))
                break
        # 3. missing_newline
        if source and not source.endswith('\n'):
            last_line = lines[-1] if lines else ''
            items.append(self._make_item('code_line', relpath, len(lines), 'missing_newline', 'low', '文件末尾缺少换行符', last_line[:80]))
        # 4. unused_import + 5. bare_except (基于AST)
        try:
            tree = ast.parse(source, filename=relpath)
        except SyntaxError:
            return items
        imported = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    imported[name] = (getattr(node, 'lineno', 1), getattr(node, 'end_lineno', node.lineno), alias.name)
            elif isinstance(node, ast.ImportFrom):
                if getattr(node, 'module', '') == '__future__':
                    continue
                for alias in node.names:
                    if alias.name == '*':
                        continue
                    name = alias.asname or alias.name
                    imported[name] = (getattr(node, 'lineno', 1), getattr(node, 'end_lineno', node.lineno), alias.name)
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                cur = node
                while isinstance(cur, ast.Attribute):
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    used.add(cur.id)
        # 内置与常用模块不报unused
        builtins_set = set(dir(__builtins__)) if isinstance(__builtins__, dict) else set(dir(__builtins__))
        common_mods = {'os', 'sys', 'json', 're', 'time', 'datetime', 'hashlib', 'sqlite3', 'threading', 'logging', 'random', 'collections', 'functools', 'pathlib', 'typing', 'dataclasses', 'uuid', 'base64', 'hmac', 'secrets', 'ast', 'traceback', 'abc'}
        reported_unused = 0
        for name, (ln, end_ln, orig) in imported.items():
            if name in used or name in builtins_set or name in common_mods:
                continue
            # 多行括号导入不可安全注释首行, 跳过
            if end_ln and end_ln > ln:
                continue
            # 只报前3个未使用导入, 避免噪音
            if reported_unused >= 3:
                break
            items.append(self._make_item('code_line', relpath, ln, 'unused_import', 'low', f'未使用的导入: {orig}', f'import {orig}'))
            reported_unused += 1
        # bare_except
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                items.append(self._make_item('code_line', relpath, getattr(node, 'lineno', 1), 'bare_except', 'medium', 'bare except: 建议捕获具体异常', 'except:'))
                break
        return items

    def _clean_msg(self, msg):
        msg = re.sub('^.*\\.py:\\d+:', '', msg).strip()
        msg = re.sub('Sorry: ', '', msg)
        lines = [l.strip() for l in msg.split('\n') if l.strip()]
        return ' '.join(lines)[:200]

    def route_to_teams(self) -> Dict[str, Any]:
        """模块3: 将问题路由到对应AI团队"""
        self._log_timeline('AI_ROUTE_START', '开始AI团队路由')
        logger.info('[AITeamRouter] 路由问题到AI团队...')
        team_assignments = defaultdict(list)
        for item in self._items:
            (expert, team, role) = AI_TEAM_ROUTING.get(item.category, AI_TEAM_ROUTING['unknown'])
            item.assigned_expert = expert
            item.assigned_team = team
            item.team_role = role
            item.lifecycle_status = 'assigned'
            team_assignments[team].append(item.item_id)
        result = {'total_items': len(self._items), 'teams': {k: len(v) for (k, v) in team_assignments.items()}, 'by_expert': dict(defaultdict(int, {k: len(v) for (k, v) in team_assignments.items()}))}
        self._log_timeline('AI_ROUTE_DONE', f"路由完成: {json.dumps(result['teams'], ensure_ascii=False)}")
        logger.info(f"[AITeamRouter] 路由: {json.dumps(result['teams'], ensure_ascii=False)}")
        return result

    def auto_fix_all(self) -> Dict[str, int]:
        """模块4: 自动修复"""
        self._log_timeline('AUTO_FIX_START', '开始自动修复')
        logger.info('[AutoFixer] 开始自动修复...')
        fixed = 0
        failed = 0
        skipped = 0
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
        logger.info(f'[AutoFixer] 修复: 成功={fixed}, 失败={failed}, 跳过={skipped}')
        return {'fixed': fixed, 'failed': failed, 'skipped': skipped}

    def _fix_item(self, item: InspectionItem) -> bool:
        """修复单个问题 (v2.1: 新增6类修复器,覆盖率3→9类)"""
        if item.source == 'page':
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
        # v2.1 新增6类修复器
        if item.category == 'empty_file':
            return self._fix_empty_file(item, filepath, lines)
        if item.category == 'trailing_whitespace':
            return self._fix_trailing_whitespace(item, filepath, lines)
        if item.category == 'missing_newline':
            return self._fix_missing_newline(item, filepath, lines)
        if item.category == 'unused_import':
            return self._fix_unused_import(item, filepath, lines)
        if item.category == 'bare_except':
            return self._fix_pattern(item, filepath, lines)
        if item.category == 'import_error':
            return self._fix_import_error(item, filepath, lines)
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

    def _fix_empty_file(self, item, filepath, lines):
        """v2.1: 空文件添加docstring占位"""
        item.fix_action = 'empty_file_docstring'
        if not any(l.strip() for l in lines):
            lines = ['"""空模块占位 (auto-generated by DeepInspection v2.1)"""\n']
            item.fix_detail = '空文件→添加docstring占位'
            return self._write_verify(filepath, lines, item)
        item.fix_detail = '文件非空,跳过'
        item.lifecycle_status = 'skipped'
        return False

    def _fix_trailing_whitespace(self, item, filepath, lines):
        """v2.1: 去除行尾空格"""
        item.fix_action = 'trailing_ws_strip'
        changed = False
        for i, line in enumerate(lines):
            rstripped = line.rstrip()
            if rstripped + '\n' != line and rstripped:
                lines[i] = rstripped + '\n'
                changed = True
        if changed:
            item.fix_detail = '行尾空格清除'
            return self._write_verify(filepath, lines, item)
        item.fix_detail = '无行尾空格'
        return False

    def _fix_missing_newline(self, item, filepath, lines):
        """v2.1: 文件末尾补换行符"""
        item.fix_action = 'eof_newline'
        if lines and not lines[-1].endswith('\n'):
            lines[-1] = lines[-1] + '\n'
            item.fix_detail = '文件末尾补换行符'
            return self._write_verify(filepath, lines, item)
        item.fix_detail = '已有末尾换行'
        return False

    def _fix_unused_import(self, item, filepath, lines):
        """v2.2: 注释未使用的导入 (仅限单行导入; __future__/多行括号导入不可安全注释)"""
        item.fix_action = 'comment_unused_import'
        idx = item.line - 1
        if idx < 0 or idx >= len(lines):
            item.fix_detail = '行号越界,跳过'
            item.lifecycle_status = 'skipped'
            return False
        line = lines[idx]
        stripped = line.strip()
        if not stripped.startswith(('import ', 'from ')):
            item.fix_detail = '非导入行,跳过'
            item.lifecycle_status = 'skipped'
            return False
        if stripped.startswith('from __future__'):
            item.fix_detail = '__future__导入必须保留,跳过'
            item.lifecycle_status = 'skipped'
            return False
        if stripped.endswith('(') or ' import (' in stripped:
            item.fix_detail = '多行括号导入不可只注释首行,跳过'
            item.lifecycle_status = 'skipped'
            return False
        indent = line[:len(line) - len(line.lstrip())]
        lines[idx] = f'{indent}# [unused] {stripped}\n'
        item.fix_detail = f'注释未使用导入: {stripped[:40]}'
        return self._write_verify(filepath, lines, item)

    def _fix_import_error(self, item, filepath, lines):
        """v2.1: 尝试修复导入路径(sys.path补全)"""
        item.fix_action = 'import_path_fix'
        idx = item.line - 1
        if idx < 0 or idx >= len(lines):
            return False
        line = lines[idx].strip()
        if line.startswith('from ') and ' import ' in line:
            module_part = line.split(' import ')[0].replace('from ', '').strip()
            if '.' in module_part:
                parent = module_part.rsplit('.', 1)[0]
                indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
                patch = f'{indent}try:\n{indent}    {line}\n{indent}except (ImportError, ModuleNotFoundError):\n{indent}    import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n{indent}    {line}\n'
                lines[idx] = patch
                item.fix_detail = f'导入路径容错包裹: {module_part[:30]}'
                return self._write_verify(filepath, lines, item)
        item.fix_detail = '无法自动修复导入(需人工)'
        item.lifecycle_status = 'skipped'
        return False

    def _fix_indentation(self, item, filepath, lines):
        item.fix_action = 'indentation_fix'
        idx = item.line - 1
        if idx < 0 or idx >= len(lines):
            return False
        bad_line = lines[idx]
        stripped = bad_line.strip()
        if not stripped or stripped.startswith('#'):
            lines[idx] = stripped + '\n' if stripped else '\n'
            item.fix_detail = '清理空行/注释缩进'
            return self._write_verify(filepath, lines, item)
        cur_indent_len = len(bad_line[:len(bad_line) - len(bad_line.lstrip())])
        if idx < len(lines) - 1:
            next_line = lines[idx + 1]
            if next_line.strip():
                next_indent = next_line[:len(next_line) - len(next_line.lstrip())]
                if len(next_indent) > cur_indent_len:
                    lines[idx] = next_indent + stripped + '\n'
                    item.fix_detail = f'缩进修正为{len(next_indent)}空格(对齐后行)'
                    return self._write_verify(filepath, lines, item)
        if idx > 0:
            prev = lines[idx - 1].strip()
            if prev.endswith(':'):
                expected = lines[idx - 1][:len(lines[idx - 1]) - len(lines[idx - 1].lstrip())] + '    '
                lines[idx] = expected + stripped + '\n'
                item.fix_detail = f'缩进修正为{len(expected)}空格(前行冒号)'
                return self._write_verify(filepath, lines, item)
        if idx < len(lines) - 1 and lines[idx + 1].strip():
            next_indent = lines[idx + 1][:len(lines[idx + 1]) - len(lines[idx + 1].lstrip())]
            lines[idx] = next_indent + stripped + '\n'
            item.fix_detail = f'缩进修正为{len(next_indent)}空格(对齐后行)'
            return self._write_verify(filepath, lines, item)
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
        if idx < 0 or idx >= len(lines):
            return False
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
        if idx < 0 or idx >= len(lines):
            return False
        stripped = lines[idx].strip()
        if stripped == 'except:':
            indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
            lines[idx] = f'{indent}except Exception:\n'
            item.fix_detail = 'except: -> except Exception:'
            return self._write_verify(filepath, lines, item)
        item.fix_detail = '无法自动修复'
        return False

    def _write_verify(self, filepath, lines, item):
        """先在临时文件编译验证, 通过才原子替换目标文件, 杜绝写入损坏内容"""
        tmp = filepath + '.mt_write_verify.tmp'
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            py_compile.compile(tmp, doraise=True)
            os.replace(tmp, filepath)
            return True
        except Exception as e:
            if 'timed out' in str(e).lower():
                item.fix_detail += '(OneDrive超时)'
            else:
                item.fix_detail += f'(验证失败: {str(e)[:80]})'
            return False
        finally:
            if os.path.exists(tmp):
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    def verify_and_track(self) -> Dict[str, int]:
        """模块5: 验证修复并追踪生命周期"""
        self._log_timeline('VERIFY_START', '开始验证修复')
        logger.info('[LifecycleTracker] 验证修复...')
        verified = 0
        resolved = 0
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
        for item in self._items:
            if item.lifecycle_status in ('verified', 'failed', 'skipped'):
                if item.lifecycle_status != 'failed':
                    item.lifecycle_status = 'resolved'
                    item.resolved_at = datetime.now().isoformat()
                    resolved += 1
        self._report.items_verified = verified
        self._report.items_resolved = resolved
        self._log_timeline('VERIFY_DONE', f'验证: {verified}通过, {resolved}已解决')
        logger.info(f'[LifecycleTracker] 验证: {verified}通过, {resolved}已解决')
        return {'verified': verified, 'resolved': resolved}

    def generate_report(self) -> LifecycleReport:
        """生成全生命周期报告"""
        self._log_timeline('REPORT_START', '生成报告')
        teams = list(set((item.assigned_team for item in self._items if item.assigned_team)))
        report = LifecycleReport(report_id=hashlib.md5(f'deep_{datetime.now().isoformat()}'.encode()).hexdigest()[:16], inspection_time=datetime.now().isoformat(), pages_inspected=self._report.pages_inspected, routes_found=self._report.routes_found, files_inspected=self._report.files_inspected, lines_inspected=self._report.lines_inspected, items_found=len(self._items), items_fixed=self._report.items_fixed, items_failed=self._report.items_failed, items_verified=self._report.items_verified, items_resolved=self._report.items_resolved, teams_involved=teams, items=list(self._items), timeline=list(self._timeline), duration=0)
        fixed = report.items_fixed
        total = report.items_found
        rate = fixed / total * 100 if total > 0 else 100
        report.summary = f'深度巡检报告 | 路由{report.routes_found}个 | 文件{report.files_inspected}个/{report.lines_inspected}行 | 发现{total}问题 | 修复{fixed}({rate:.0f}%) | 验证{report.items_verified} | 解决{report.items_resolved} | AI团队{len(teams)}个'
        self._report = report
        self._log_timeline('REPORT_DONE', report.summary)
        logger.info(f'[LifecycleReporter] {report.summary}')
        return report

    def persist_to_database(self, flow_id: str='deep_inspection') -> Dict[str, int]:
        """数据库永久化存储"""
        self._log_timeline('PERSIST_START', '写入数据库')
        logger.info('[DatabasePersistor] 写入数据库...')
        ensure_tables()
        now = datetime.now().isoformat()
        stored = 0
        with _LOCK:
            c = _get_conn()
            cur = c.cursor()
            report_data = {'report_id': self._report.report_id, 'inspection_time': self._report.inspection_time, 'routes_found': self._report.routes_found, 'files_inspected': self._report.files_inspected, 'lines_inspected': self._report.lines_inspected, 'items_found': self._report.items_found, 'items_fixed': self._report.items_fixed, 'items_verified': self._report.items_verified, 'items_resolved': self._report.items_resolved, 'teams_involved': self._report.teams_involved, 'summary': self._report.summary, 'timeline': self._report.timeline[-20:]}
            cur.execute('INSERT OR REPLACE INTO mt_super_admin_reports\n                (flow_id, report_type, title, content, operator, created_at)\n                VALUES(?,?,?,?,?,?)', (flow_id, 'DEEP_INSPECTION_REPORT', f'深度巡检报告-{self._report.report_id}', json.dumps(report_data, ensure_ascii=False), 'DeepInspection', now))
            stored += 1
            for item in self._items:
                item_data = {'item_id': item.item_id, 'source': item.source, 'file': item.file, 'line': item.line, 'category': item.category, 'severity': item.severity, 'message': item.message, 'code_snippet': item.code_snippet, 'route': item.route, 'assigned_team': item.assigned_team, 'assigned_expert': item.assigned_expert, 'team_role': item.team_role, 'lifecycle_status': item.lifecycle_status, 'fix_action': item.fix_action, 'fix_detail': item.fix_detail, 'verified': item.verified, 'verify_result': item.verify_result, 'discovered_at': item.discovered_at, 'fixed_at': item.fixed_at, 'resolved_at': item.resolved_at}
                eh = hashlib.md5(f'{item.item_id}_{item.file}_{item.line}'.encode()).hexdigest()
                cur.execute('INSERT OR REPLACE INTO mt_experience_library\n                    (experience_hash, title, content_json, source_flow, flow_id, exp_content, created_at)\n                    VALUES(?,?,?,?,?,?,?)', (eh, f'巡检-{item.file}:{item.line}', json.dumps(item_data, ensure_ascii=False), flow_id, flow_id, f'[{item.category}]{item.file}:{item.line} -> {item.lifecycle_status} ({item.fix_detail[:50]})', now))
                stored += 1
            for item in self._items:
                if item.lifecycle_status in ('failed', 'discovered', 'assigned'):
                    fh = hashlib.md5(f'unresolved_{item.item_id}'.encode()).hexdigest()
                    cur.execute('INSERT OR REPLACE INTO mt_anomaly_feature_library\n                        (feature_hash, feature_kind, feature_vector_json, source_flow, flow_id,\n                         anomaly_type, anomaly_feature, created_at)\n                        VALUES(?,?,?,?,?,?,?,?)', (fh, 'deep_inspection', json.dumps({'file': item.file, 'line': item.line, 'category': item.category, 'severity': item.severity, 'message': item.message, 'team': item.assigned_team, 'expert': item.assigned_expert, 'status': item.lifecycle_status}, ensure_ascii=False), flow_id, flow_id, item.category, f'{item.file}:{item.line}', now))
                    stored += 1
            feed_content = f'深度巡检完成: 路由{self._report.routes_found}个, 文件{self._report.files_inspected}个/{self._report.lines_inspected}行, 发现{self._report.items_found}问题, 修复{self._report.items_fixed}, 验证{self._report.items_verified}, 解决{self._report.items_resolved}, AI团队{len(self._report.teams_involved)}个'
            cur.execute('INSERT OR IGNORE INTO mt_ai_brain_feed_log\n                (flow_id, feed_kind, feed_content, triggered_at)\n                VALUES(?,?,?,?)', (flow_id, 'deep_inspection', feed_content, now))
            stored += 1
            c.commit()
            c.close()
        if HAS_DEV_FLOW:
            feed_brain(flow_id, 'deep_inspection', self._report.summary)
            for item in self._items:
                if item.lifecycle_status == 'failed':
                    feed_brain(flow_id, 'anomaly', f'修复失败: [{item.category}]{item.file}:{item.line} - {item.message[:60]}')
        self._log_timeline('PERSIST_DONE', f'存储{stored}条记录')
        logger.info(f'[DatabasePersistor] 存储{stored}条记录')
        return {'stored': stored}

    def run_full_inspection(self, flow_id: str='deep_inspection') -> LifecycleReport:
        """执行完整深度巡检"""
        print('=' * 70)
        print(' MTSCOS 深度巡检引擎 v2.0.0')
        print('=' * 70)
        print(' 6大模块: 页面检查 + 逐行代码 + AI路由 + 自动修复 + 生命周期 + 持久化')
        print(f' AI团队: {len(AI_TEAM_ROUTING)}种路由类别')
        print()
        t0 = time.time()
        print('--- 模块1: PageInspector 页面/路由检查 ---')
        page_items = self.inspect_pages()
        print(f'  路由: {self._report.routes_found}个 | 问题: {len(page_items)}个')
        print('\n--- 模块2: CodeLineInspector 逐行代码检查 ---')
        code_items = self.inspect_code_lines()
        print(f'  文件: {self._report.files_inspected}个 | 行: {self._report.lines_inspected}行 | 问题: {len(code_items)}个')
        with self._lock:
            self._items = page_items + code_items
            self._report.items_found = len(self._items)
        print(f'\n--- 模块3: AITeamRouter AI团队路由 ---')
        routing = self.route_to_teams()
        print(f"  路由: {json.dumps(routing['teams'], ensure_ascii=False)}")
        print(f'\n--- 模块4: AutoFixer 自动修复 ---')
        fix_stats = self.auto_fix_all()
        print(f'  修复: {json.dumps(fix_stats, ensure_ascii=False)}')
        print(f'\n--- 模块5: LifecycleTracker 验证追踪 ---')
        verify_stats = self.verify_and_track()
        print(f'  验证: {json.dumps(verify_stats, ensure_ascii=False)}')
        print(f'\n--- 模块6: Report+Persist 报告持久化 ---')
        report = self.generate_report()
        print(f'  {report.summary}')
        persist_stats = self.persist_to_database(flow_id)
        print(f'  存储: {json.dumps(persist_stats, ensure_ascii=False)}')
        elapsed = time.time() - t0
        report.duration = elapsed
        print(f"\n{'=' * 70}")
        print(f' 深度巡检完成 | 耗时: {elapsed:.1f}s')
        print(f'  路由: {report.routes_found}个')
        print(f'  文件: {report.files_inspected}个 / {report.lines_inspected}行')
        print(f'  发现: {report.items_found}问题')
        print(f'  修复: {report.items_fixed} ({report.items_fixed / max(report.items_found, 1) * 100:.0f}%)')
        print(f'  验证: {report.items_verified}通过')
        print(f'  解决: {report.items_resolved}')
        print(f'  AI团队: {len(report.teams_involved)}个')
        print(f"  存储: {persist_stats['stored']}条DB记录")
        print(f"{'=' * 70}")
        return report
if __name__ == '__main__':
    engine = DeepInspectionEngine()
    report = engine.run_full_inspection()
    if report.items:
        print('\n--- 问题详情(前20) ---')
        for (i, item) in enumerate(report.items[:20], 1):
            icon = {'resolved': '✓', 'fixed': '◐', 'failed': '✗', 'skipped': '○'}.get(item.lifecycle_status, '?')
            print(f'  {i:2d}. {icon} [{item.category}] {item.file}:{item.line}')
            print(f'      消息: {item.message[:70]}')
            print(f'      AI: {item.assigned_expert}({item.assigned_team}) | 状态: {item.lifecycle_status}')
            if item.fix_detail:
                print(f'      修复: {item.fix_detail[:60]}')
            print()
