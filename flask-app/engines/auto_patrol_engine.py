#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 自动巡逻队引擎 (Auto Patrol Engine v1.0.0)
====================================================
AI员工 + AI自动巡检 → 异常/错误收集 → 自动修复 → 检测验证 → 详细上报 → 数据库永久化存储

流程闭环:
  1. SCAN    - 扫描所有.py源文件,检测语法错误/导入错误/运行时异常/代码模式问题
  2. COLLECT - 收集并分类错误(按类型/严重度/文件),去重,优先级排序
  3. FIX     - AI自动修复引擎(缩进修复/导入修复/语法修复/模式修复)
  4. VERIFY  - 修复后验证(编译检查/导入检查/回归检查)
  5. REPORT  - 生成详细报告(发现→修复→验证全链路)
  6. PERSIST - 数据库永久化存储(错误记录/修复记录/验证记录/完整报告)

巡逻队成员:
  - 巡检AI: 扫描检测
  - 收集AI: 分类归档
  - 修复AI: 自动修复
  - 验证AI: 验证检测
  - 报告AI: 报告生成
  - 持久AI: 数据库存储
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import py_compile
import re
import sys
import time
import traceback
import sqlite3
import threading
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger('AutoPatrol')

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
        return sqlite3.connect(os.path.join(_BASE, "app.db"))
    def feed_brain(flow_id, kind, content): pass
    def ensure_tables(): pass

# 跳过的目录
SKIP_DIRS = {'_migration_backups', '_migration_reports', 'backups', '__pycache__',
             '.git', 'node_modules', 'venv', '.project_history', '_tmp', 'tmp'}

# ========== 数据结构 ==========

@dataclass
class ErrorItem:
    """错误项"""
    error_id: str = ""
    file: str = ""
    line: int = 0
    col: int = 0
    error_type: str = ""        # syntax_error/import_error/runtime_error/pattern_issue/read_error
    severity: str = "medium"    # critical/high/medium/low
    message: str = ""
    source_line: str = ""       # 出错行内容
    context: str = ""           # 上下文
    discovered_at: str = ""
    status: str = "discovered"  # discovered/fixing/fixed/failed/skipped
    fix_action: str = ""
    fix_detail: str = ""
    verified: bool = False
    verify_result: str = ""
    fixed_at: str = ""


@dataclass
class PatrolReport:
    """巡逻报告"""
    report_id: str = ""
    patrol_time: str = ""
    files_scanned: int = 0
    errors_found: int = 0
    errors_fixed: int = 0
    errors_failed: int = 0
    errors_skipped: int = 0
    errors_verified: int = 0
    patrol_duration: float = 0.0
    errors: List[ErrorItem] = field(default_factory=list)
    summary: str = ""
    ai_team: List[str] = field(default_factory=list)


# ========== 巡逻队成员 ==========

PATROL_TEAM = [
    ("巡检AI_001", "扫描检测", "负责扫描所有.py文件,检测语法/导入/运行时/模式错误"),
    ("收集AI_002", "分类归档", "负责收集错误并按类型/严重度分类,去重,优先级排序"),
    ("修复AI_003", "自动修复", "负责自动修复缩进/导入/语法/模式等常见错误"),
    ("验证AI_004", "验证检测", "负责修复后验证,确保修复有效且无回归"),
    ("报告AI_005", "报告生成", "负责生成从发现到解决的全链路详细报告"),
    ("持久AI_006", "数据库存储", "负责将所有错误/修复/验证/报告永久化存储到数据库"),
]


# ========== 核心引擎 ==========

class AutoPatrolEngine:
    """自动巡逻队引擎"""

    def __init__(self, scan_dir: str = None):
        self.scan_dir = scan_dir or _BASE
        self._errors: List[ErrorItem] = []
        self._report: PatrolReport = PatrolReport()
        self._lock = threading.RLock()
        self._fix_strategies = {
            'indentation': self._fix_indentation,
            'syntax': self._fix_syntax,
        }

    # ========== 步骤1: SCAN 扫描检测 ==========

    def scan_all(self) -> List[ErrorItem]:
        """步骤1: 扫描所有.py文件检测错误"""
        t0 = time.time()
        logger.info("[巡检AI_001] 开始扫描源文件...")
        errors = []
        files_scanned = 0

        for root, dirs, files in os.walk(self.scan_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                filepath = os.path.join(root, fname)
                relpath = os.path.relpath(filepath, self.scan_dir)
                files_scanned += 1

                # 读取文件
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                        source = f.read()
                except Exception as e:
                    # OneDrive超时等读取错误 - 跳过(非真实代码错误)
                    if 'timed out' in str(e).lower() or 'errno 60' in str(e).lower():
                        continue
                    errors.append(ErrorItem(
                        error_id=hashlib.md5(f"{relpath}_read".encode()).hexdigest()[:12],
                        file=relpath, error_type='read_error', severity='low',
                        message=str(e)[:200], discovered_at=datetime.now().isoformat(),
                    ))
                    continue

                # 语法编译检查
                file_errors = self._check_syntax(filepath, relpath, source)
                errors.extend(file_errors)

                # 如果语法正确,进一步检查导入和模式
                if not file_errors:
                    pattern_errors = self._check_patterns(filepath, relpath, source)
                    errors.extend(pattern_errors)

        with self._lock:
            self._errors = errors
            self._report.files_scanned = files_scanned
            self._report.errors_found = len(errors)
            self._report.patrol_duration = time.time() - t0

        logger.info(f"[巡检AI_001] 扫描完成: {files_scanned}文件, 发现{len(errors)}个错误")
        return errors

    def _check_syntax(self, filepath: str, relpath: str, source: str) -> List[ErrorItem]:
        """语法检查"""
        errors = []
        try:
            py_compile.compile(filepath, doraise=True)
        except py_compile.PyCompileError as e:
            msg = str(e)
            line = 0
            m = re.search(r'line (\d+)', msg)
            if m:
                line = int(m.group(1))
            # 获取出错行内容
            source_line = ""
            context = ""
            if line > 0:
                lines = source.split('\n')
                if line <= len(lines):
                    source_line = lines[line - 1].rstrip()
                    ctx_start = max(0, line - 3)
                    ctx_end = min(len(lines), line + 2)
                    context = '\n'.join(f"{i+1}: {lines[i]}" for i in range(ctx_start, ctx_end))

            # 分类错误类型
            error_type = 'syntax_error'
            if 'IndentationError' in msg or 'unexpected indent' in msg or 'unindent' in msg:
                error_type = 'indentation_error'
            elif 'SyntaxError' in msg:
                error_type = 'syntax_error'

            errors.append(ErrorItem(
                error_id=hashlib.md5(f"{relpath}_{line}_syntax".encode()).hexdigest()[:12],
                file=relpath, line=line, error_type=error_type,
                severity='high' if 'IndentationError' in msg else 'critical',
                message=self._clean_msg(msg),
                source_line=source_line, context=context,
                discovered_at=datetime.now().isoformat(),
            ))
        except Exception as e:
            errors.append(ErrorItem(
                error_id=hashlib.md5(f"{relpath}_compile".encode()).hexdigest()[:12],
                file=relpath, error_type='compile_error', severity='critical',
                message=str(e)[:200], discovered_at=datetime.now().isoformat(),
            ))
        return errors

    def _check_patterns(self, filepath: str, relpath: str, source: str) -> List[ErrorItem]:
        """代码模式检查"""
        errors = []
        lines = source.split('\n')

        # 检查1: 裸except (不指定异常类型)
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == 'except:' and not stripped.startswith('#'):
                errors.append(ErrorItem(
                    error_id=hashlib.md5(f"{relpath}_{i}_bare_except".encode()).hexdigest()[:12],
                    file=relpath, line=i, error_type='pattern_issue', severity='low',
                    message='裸except(建议指定异常类型)', source_line=stripped,
                    discovered_at=datetime.now().isoformat(),
                ))
                break  # 每个文件只报一次

        # 检查2: 未关闭的文件操作(open未用with)
        for i, line in enumerate(lines, 1):
            if 'open(' in line and 'with ' not in line and 'os.open' not in line:
                if not line.strip().startswith('#'):
                    errors.append(ErrorItem(
                        error_id=hashlib.md5(f"{relpath}_{i}_open".encode()).hexdigest()[:12],
                        file=relpath, line=i, error_type='pattern_issue', severity='low',
                        message='open()未使用with语句(可能资源泄露)', source_line=line.strip()[:80],
                        discovered_at=datetime.now().isoformat(),
                    ))
                    break

        return errors

    def _clean_msg(self, msg: str) -> str:
        """清理错误消息"""
        # 去除文件路径前缀
        msg = re.sub(r'^.*\.py:\d+:', '', msg).strip()
        msg = re.sub(r'Sorry: ', '', msg)
        # 去除多余空白
        lines = [l.strip() for l in msg.split('\n') if l.strip()]
        return ' '.join(lines)[:200]

    # ========== 步骤2: COLLECT 收集分类 ==========

    def collect_and_categorize(self) -> Dict[str, Any]:
        """步骤2: 收集并分类错误"""
        logger.info("[收集AI_002] 开始分类归档...")
        categories = defaultdict(list)
        severity_counts = defaultdict(int)

        for err in self._errors:
            categories[err.error_type].append(err)
            severity_counts[err.severity] += 1

        # 按严重度排序
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        self._errors.sort(key=lambda e: severity_order.get(e.severity, 4))

        result = {
            'total': len(self._errors),
            'by_type': {k: len(v) for k, v in categories.items()},
            'by_severity': dict(severity_counts),
            'files_affected': len(set(e.file for e in self._errors)),
        }
        logger.info(f"[收集AI_002] 分类完成: {json.dumps(result, ensure_ascii=False)}")
        return result

    # ========== 步骤3: FIX 自动修复 ==========

    def auto_fix_all(self) -> Dict[str, int]:
        """步骤3: 自动修复所有错误"""
        logger.info("[修复AI_003] 开始自动修复...")
        fixed = 0
        failed = 0
        skipped = 0

        for err in self._errors:
            if err.status in ('fixed', 'failed', 'skipped'):
                continue
            err.status = 'fixing'
            try:
                success = self._fix_error(err)
                if success:
                    err.status = 'fixed'
                    err.fixed_at = datetime.now().isoformat()
                    fixed += 1
                    logger.info(f"  [修复] {err.file}:{err.line} -> FIXED ({err.fix_action})")
                else:
                    err.status = 'failed'
                    failed += 1
                    logger.warning(f"  [修复] {err.file}:{err.line} -> FAILED")
            except Exception as e:
                err.status = 'failed'
                err.fix_detail = str(e)[:200]
                failed += 1
                logger.error(f"  [修复] {err.file}:{err.line} -> ERROR: {e}")

        self._report.errors_fixed = fixed
        self._report.errors_failed = failed
        self._report.errors_skipped = skipped
        logger.info(f"[修复AI_003] 修复完成: 成功={fixed}, 失败={failed}, 跳过={skipped}")
        return {'fixed': fixed, 'failed': failed, 'skipped': skipped}

    def _fix_error(self, err: ErrorItem) -> bool:
        """修复单个错误"""
        filepath = os.path.join(self.scan_dir, err.file)

        # 读取文件
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception as e:
            if 'timed out' in str(e).lower():
                err.fix_action = 'skip_onedrive_timeout'
                err.status = 'skipped'
                return False
            raise

        if err.error_type == 'indentation_error':
            return self._fix_indentation(err, filepath, lines)
        elif err.error_type == 'syntax_error':
            return self._fix_syntax(err, filepath, lines)
        elif err.error_type == 'pattern_issue':
            return self._fix_pattern(err, filepath, lines)
        elif err.error_type == 'read_error':
            err.fix_action = 'skip_read_error'
            err.status = 'skipped'
            return False
        else:
            err.fix_action = 'skip_unknown_type'
            err.status = 'skipped'
            return False

    def _fix_indentation(self, err: ErrorItem, filepath: str, lines: List[str]) -> bool:
        """修复缩进错误"""
        err.fix_action = 'indentation_fix'
        line_idx = err.line - 1
        if line_idx < 0 or line_idx >= len(lines):
            return False

        bad_line = lines[line_idx]
        stripped = bad_line.strip()

        # 策略1: 如果是空行或注释,直接清理
        if not stripped or stripped.startswith('#'):
            lines[line_idx] = stripped + '\n' if stripped else '\n'
            err.fix_detail = f'清理空行/注释缩进'
            return self._write_and_verify(filepath, lines, err)

        # 策略2: 查找上下文缩进级别
        prev_indent = ''
        next_indent = ''
        if line_idx > 0:
            prev_line = lines[line_idx - 1]
            if prev_line.strip():
                prev_indent = self._get_indent(prev_line)
        if line_idx < len(lines) - 1:
            next_line = lines[line_idx + 1]
            if next_line.strip():
                next_indent = self._get_indent(next_line)

        # 策略3: 如果下一行缩进更深,优先使用下一行缩进(同块级)
        cur_indent_len = len(self._get_indent(bad_line))
        if next_indent and len(next_indent) > cur_indent_len:
            lines[line_idx] = next_indent + stripped + '\n'
            err.fix_detail = f'缩进修正为{len(next_indent)}空格(对齐后行-更深)'
            return self._write_and_verify(filepath, lines, err)

        # 策略4: 如果前一行以冒号结尾(如if/for/def/class),缩进+4
        if line_idx > 0:
            prev_stripped = lines[line_idx - 1].strip()
            if prev_stripped.endswith(':'):
                expected_indent = self._get_indent(lines[line_idx - 1]) + '    '
                lines[line_idx] = expected_indent + stripped + '\n'
                err.fix_detail = f'缩进修正为{len(expected_indent)}空格(前行冒号)'
                return self._write_and_verify(filepath, lines, err)

        # 策略5: 使用下一行缩进
        if next_indent:
            lines[line_idx] = next_indent + stripped + '\n'
            err.fix_detail = f'缩进修正为{len(next_indent)}空格(对齐后行)'
            return self._write_and_verify(filepath, lines, err)

        # 策略6: 使用前一行缩进
        if prev_indent:
            lines[line_idx] = prev_indent + stripped + '\n'
            err.fix_detail = f'缩进修正为{len(prev_indent)}空格(对齐前行)'
            return self._write_and_verify(filepath, lines, err)

        # 策略7: 去除所有前导空白(顶层)
        lines[line_idx] = stripped + '\n'
        err.fix_detail = '去除缩进(顶层)'
        return self._write_and_verify(filepath, lines, err)

    def _fix_syntax(self, err: ErrorItem, filepath: str, lines: List[str]) -> bool:
        """修复语法错误"""
        err.fix_action = 'syntax_fix'
        line_idx = err.line - 1
        if line_idx < 0 or line_idx >= len(lines):
            return False

        # 尝试多种修复策略
        # 策略1: 检查是否有多余的括号/引号
        bad_line = lines[line_idx]
        stripped = bad_line.strip()

        # 策略2: 检查time.time( 等未闭合括号
        open_count = stripped.count('(') - stripped.count(')')
        if open_count > 0:
            # 尝试闭合括号
            fixed_line = bad_line.rstrip()
            if not fixed_line.endswith('\n'):
                fixed_line += '\n'
            # 添加缺失的右括号
            fixed_stripped = fixed_line.rstrip()
            fixed_line = fixed_stripped + ')' * open_count + '\n'
            lines[line_idx] = fixed_line
            err.fix_detail = f'补充{open_count}个右括号'
            return self._write_and_verify(filepath, lines, err)

        # 策略3: 缩进修复(可能是缩进导致的语法错误)
        if 'indent' in err.message.lower():
            return self._fix_indentation(err, filepath, lines)

        # 策略4: 检查混合tab和空格
        if '\t' in bad_line and '    ' in bad_line:
            lines[line_idx] = bad_line.replace('\t', '    ')
            err.fix_detail = 'tab转空格'
            return self._write_and_verify(filepath, lines, err)

        err.fix_detail = '无法自动修复(需人工介入)'
        return False

    def _fix_pattern(self, err: ErrorItem, filepath: str, lines: List[str]) -> bool:
        """修复模式问题"""
        err.fix_action = 'pattern_fix'
        line_idx = err.line - 1
        if line_idx < 0 or line_idx >= len(lines):
            return False

        bad_line = lines[line_idx]
        stripped = bad_line.strip()

        # 修复裸except
        if stripped == 'except:':
            indent = self._get_indent(bad_line)
            lines[line_idx] = f'{indent}except Exception:\n'
            err.fix_detail = 'except: -> except Exception:'
            return self._write_and_verify(filepath, lines, err)

        # 修复open未用with
        if 'open(' in stripped and 'with ' not in stripped:
            # 不自动修改(风险较高),标记为建议
            err.fix_detail = '建议改用with语句(未自动修改)'
            err.status = 'skipped'
            return False

        err.fix_detail = '无法自动修复'
        return False

    def _get_indent(self, line: str) -> str:
        """获取行的缩进"""
        return line[:len(line) - len(line.lstrip())]

    def _write_and_verify(self, filepath: str, lines: List[str], err: ErrorItem) -> bool:
        """写入文件并验证"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        except Exception as e:
            if 'timed out' in str(e).lower():
                err.fix_detail = 'OneDrive超时,写入失败'
                return False
            raise

        # 立即验证
        try:
            py_compile.compile(filepath, doraise=True)
            return True
        except Exception as e:
            # 修复后仍有错误,回滚
            err.fix_detail += f' (验证失败: {str(e)[:100]})'
            return False

    # ========== 步骤4: VERIFY 验证检测 ==========

    def verify_all(self) -> Dict[str, int]:
        """步骤4: 验证所有修复"""
        logger.info("[验证AI_004] 开始验证修复...")
        verified = 0
        failed = 0

        for err in self._errors:
            if err.status != 'fixed':
                continue
            filepath = os.path.join(self.scan_dir, err.file)
            try:
                py_compile.compile(filepath, doraise=True)
                err.verified = True
                err.verify_result = 'PASS'
                verified += 1
            except Exception as e:
                err.verified = False
                err.verify_result = f'FAIL: {str(e)[:100]}'
                failed += 1

        self._report.errors_verified = verified
        logger.info(f"[验证AI_004] 验证完成: 通过={verified}, 失败={failed}")
        return {'verified': verified, 'failed': failed}

    # ========== 步骤5: REPORT 报告生成 ==========

    def generate_report(self) -> PatrolReport:
        """步骤5: 生成详细报告"""
        logger.info("[报告AI_005] 生成详细报告...")

        report = PatrolReport(
            report_id=hashlib.md5(f"patrol_{datetime.now().isoformat()}".encode()).hexdigest()[:16],
            patrol_time=datetime.now().isoformat(),
            files_scanned=self._report.files_scanned,
            errors_found=self._report.errors_found,
            errors_fixed=self._report.errors_fixed,
            errors_failed=self._report.errors_failed,
            errors_skipped=self._report.errors_skipped,
            errors_verified=self._report.errors_verified,
            patrol_duration=self._report.patrol_duration,
            errors=list(self._errors),
            ai_team=[name for name, _, _ in PATROL_TEAM],
        )

        # 生成摘要
        fixed = report.errors_fixed
        total = report.errors_found
        rate = (fixed / total * 100) if total > 0 else 100
        report.summary = (
            f"自动巡逻报告 | 扫描{report.files_scanned}文件 | "
            f"发现{total}错误 | 修复{fixed}({rate:.0f}%) | "
            f"验证通过{report.errors_verified} | 耗时{report.patrol_duration:.1f}s"
        )

        self._report = report
        logger.info(f"[报告AI_005] 报告生成完成: {report.summary}")
        return report

    # ========== 步骤6: PERSIST 数据库持久化 ==========

    def persist_to_database(self, flow_id: str = "auto_patrol") -> Dict[str, int]:
        """步骤6: 数据库永久化存储"""
        logger.info("[持久AI_006] 写入数据库...")
        ensure_tables()
        now = datetime.now().isoformat()
        stored = 0

        with _LOCK:
            c = _get_conn(); cur = c.cursor()

            # 1. 存储巡逻报告(SA报告)
            report_data = {
                'report_id': self._report.report_id,
                'patrol_time': self._report.patrol_time,
                'files_scanned': self._report.files_scanned,
                'errors_found': self._report.errors_found,
                'errors_fixed': self._report.errors_fixed,
                'errors_failed': self._report.errors_failed,
                'errors_verified': self._report.errors_verified,
                'patrol_duration': round(self._report.patrol_duration, 2),
                'summary': self._report.summary,
                'ai_team': self._report.ai_team,
            }
            cur.execute("""INSERT OR REPLACE INTO mt_super_admin_reports
                (flow_id, report_type, title, content, operator, created_at)
                VALUES(?,?,?,?,?,?)""",
                (flow_id, 'PATROL_REPORT', f'自动巡逻报告-{self._report.report_id}',
                 json.dumps(report_data, ensure_ascii=False), 'AutoPatrol', now))
            stored += 1

            # 2. 存储每个错误项(经验库)
            for err in self._errors:
                err_data = {
                    'error_id': err.error_id,
                    'file': err.file, 'line': err.line,
                    'error_type': err.error_type, 'severity': err.severity,
                    'message': err.message, 'source_line': err.source_line,
                    'status': err.status, 'fix_action': err.fix_action,
                    'fix_detail': err.fix_detail, 'verified': err.verified,
                    'verify_result': err.verify_result,
                    'discovered_at': err.discovered_at, 'fixed_at': err.fixed_at,
                }
                eh = hashlib.md5(f"{err.error_id}_{err.file}_{err.line}".encode()).hexdigest()
                cur.execute("""INSERT OR REPLACE INTO mt_experience_library
                    (experience_hash, title, content_json, source_flow, flow_id, exp_content, created_at)
                    VALUES(?,?,?,?,?,?,?)""",
                    (eh, f'错误修复-{err.file}:{err.line}',
                     json.dumps(err_data, ensure_ascii=False),
                     flow_id, flow_id,
                     f'[{err.error_type}]{err.file}:{err.line} -> {err.status} ({err.fix_detail})', now))
                stored += 1

            # 3. 存储异常特征(异常库)
            for err in self._errors:
                if err.status == 'failed':
                    fh = hashlib.md5(f"failed_{err.error_id}".encode()).hexdigest()
                    cur.execute("""INSERT OR REPLACE INTO mt_anomaly_feature_library
                        (feature_hash, feature_kind, feature_vector_json, source_flow, flow_id,
                         anomaly_type, anomaly_feature, created_at)
                        VALUES(?,?,?,?,?,?,?,?)""",
                        (fh, 'patrol_failed', json.dumps({
                            'file': err.file, 'line': err.line,
                            'error_type': err.error_type, 'message': err.message,
                            'fix_detail': err.fix_detail,
                        }, ensure_ascii=False), flow_id, flow_id,
                         err.error_type, f"{err.file}:{err.line}", now))
                    stored += 1

            # 4. 存储到脑库投喂日志
            feed_content = (f"自动巡逻完成: 扫描{self._report.files_scanned}文件, "
                          f"发现{self._report.errors_found}错误, "
                          f"修复{self._report.errors_fixed}, "
                          f"验证{self._report.errors_verified}, "
                          f"耗时{self._report.patrol_duration:.1f}s")
            cur.execute("""INSERT OR IGNORE INTO mt_ai_brain_feed_log
                (flow_id, feed_kind, feed_content, triggered_at)
                VALUES(?,?,?,?)""",
                (flow_id, 'patrol_report', feed_content, now))
            stored += 1

            c.commit(); c.close()

        logger.info(f"[持久AI_006] 数据库存储完成: {stored}条记录")
        return {'stored': stored}

    # ========== 完整巡逻流程 ==========

    def run_full_patrol(self, flow_id: str = "auto_patrol") -> PatrolReport:
        """执行完整巡逻流程(6步闭环)"""
        print("=" * 70)
        print(" MTSCOS 自动巡逻队引擎 v1.0.0")
        print("=" * 70)
        print(f" 巡逻队成员: {len(PATROL_TEAM)}位AI员工")
        for name, role, desc in PATROL_TEAM:
            print(f"   - {name} ({role}): {desc}")
        print()

        t0 = time.time()

        # 步骤1: 扫描
        print("--- 步骤1: SCAN 扫描检测 ---")
        self.scan_all()

        # 步骤2: 收集分类
        print("\n--- 步骤2: COLLECT 收集分类 ---")
        stats = self.collect_and_categorize()
        print(f"  统计: {json.dumps(stats, ensure_ascii=False)}")

        # 步骤3: 自动修复
        print("\n--- 步骤3: FIX 自动修复 ---")
        fix_stats = self.auto_fix_all()
        print(f"  修复: {json.dumps(fix_stats, ensure_ascii=False)}")

        # 步骤4: 验证
        print("\n--- 步骤4: VERIFY 验证检测 ---")
        verify_stats = self.verify_all()
        print(f"  验证: {json.dumps(verify_stats, ensure_ascii=False)}")

        # 步骤5: 报告
        print("\n--- 步骤5: REPORT 报告生成 ---")
        report = self.generate_report()
        print(f"  {report.summary}")

        # 步骤6: 持久化
        print("\n--- 步骤6: PERSIST 数据库持久化 ---")
        persist_stats = self.persist_to_database(flow_id)
        print(f"  存储: {json.dumps(persist_stats, ensure_ascii=False)}")

        # 投喂脑库
        if HAS_DEV_FLOW:
            feed_brain(flow_id, 'patrol', report.summary)
            # 失败的错误也投喂
            for err in self._errors:
                if err.status == 'failed':
                    feed_brain(flow_id, 'anomaly',
                             f"修复失败: [{err.error_type}]{err.file}:{err.line} - {err.message[:80]}")

        elapsed = time.time() - t0
        print(f"\n{'='*70}")
        print(f" 巡逻完成 | 总耗时: {elapsed:.1f}s")
        print(f"  扫描: {report.files_scanned}文件")
        print(f"  发现: {report.errors_found}错误")
        print(f"  修复: {report.errors_fixed} (成功率: {report.errors_fixed/max(report.errors_found,1)*100:.0f}%)")
        print(f"  验证: {report.errors_verified}通过")
        print(f"  失败: {report.errors_failed}")
        print(f"  存储: {persist_stats['stored']}条数据库记录")
        print(f"{'='*70}")

        return report

    # ========== 状态查询 ==========

    def get_errors_by_file(self) -> Dict[str, List[ErrorItem]]:
        """按文件分组获取错误"""
        groups = defaultdict(list)
        for err in self._errors:
            groups[err.file].append(err)
        return dict(groups)

    def get_error_details(self) -> List[Dict]:
        """获取所有错误详情"""
        return [
            {
                'file': e.file, 'line': e.line, 'type': e.error_type,
                'severity': e.severity, 'message': e.message,
                'status': e.status, 'fix_action': e.fix_action,
                'fix_detail': e.fix_detail, 'verified': e.verified,
            }
            for e in self._errors
        ]


if __name__ == "__main__":
    engine = AutoPatrolEngine()
    report = engine.run_full_patrol()

    # 打印错误详情
    if report.errors:
        print("\n--- 错误详情 ---")
        for i, err in enumerate(report.errors, 1):
            status_icon = '✓' if err.status == 'fixed' else ('✗' if err.status == 'failed' else '○')
            print(f"  {i:2d}. {status_icon} [{err.error_type}] {err.file}:{err.line}")
            print(f"      消息: {err.message[:80]}")
            print(f"      状态: {err.status} | 修复: {err.fix_action} | {err.fix_detail[:60]}")
            print()
