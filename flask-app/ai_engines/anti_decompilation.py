#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 反编译检测与防护系统 (AntiDecompilationGuard)
=====================================================
功能：
  - 代码完整性校验（SHA256 指纹基线 + 篡改检测）
  - 反编译行为检测（进程扫描 + 调试器检测）
  - 代码水印注入（注释水印 + 不可见字符）
  - 防护动作执行（.pyc 清理 + 告警上报 + 阻断）
  - SSOT 持久化（基线/告警/水印落库）

遵循：
  - SSOT 原则（所有检测数据落库）
  - 超级管理员权限控制
  - 审计日志记录

版本: v1.0.0
"""

import os
import sys
import json
import time
import hashlib
import sqlite3
import logging
import subprocess
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('anti_decompilation')


# ============================================================================
# 枚举定义
# ============================================================================

class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"           # 信息性（.pyc清理等）
    WARNING = "warning"     # 警告（源码修改）
    HIGH = "high"           # 高危（调试器attach）
    CRITICAL = "critical"   # 严重（反编译工具检测）


class AlertType(Enum):
    """告警类型"""
    CODE_MODIFIED = "code_modified"             # 源码被修改
    CODE_ADDED = "code_added"                   # 新增文件
    CODE_DELETED = "code_deleted"               # 文件被删除
    PYC_TAMPERED = "pyc_tampered"               # .pyc被篡改
    DECOMPILER_DETECTED = "decompiler_detected"  # 检测到反编译工具
    DEBUGGER_DETECTED = "debugger_detected"      # 检测到调试器
    PYC_CLEANED = "pyc_cleaned"                 # .pyc已清理
    WATERMARK_INJECTED = "watermark_injected"    # 水印已注入
    WATERMARK_VERIFIED = "watermark_verified"    # 水印验证
    INTEGRITY_CHECK = "integrity_check"          # 完整性检查


class AlertStatus(Enum):
    """告警状态"""
    DETECTED = "detected"
    REPORTED = "reported"
    RESOLVED = "resolved"
    IGNORED = "ignored"


# ============================================================================
# 代码完整性校验器
# ============================================================================

class CodeIntegrityChecker:
    """代码完整性校验器 — SHA256 指纹基线 + 篡改检测"""

    # 需要校验的文件扩展名
    CHECKED_EXTENSIONS = {'.py', '.html', '.js', '.css', '.json', '.md', '.txt', '.cfg', '.ini', '.yaml', '.yml'}

    # 忽略的目录
    IGNORED_DIRS = {'__pycache__', '.git', 'node_modules', '_archive', 'logs', 'db/backups', '.trae'}

    def __init__(self, project_dir: str, db_path: str = None, dual_db=None):
        self.project_dir = project_dir
        self.db_path = db_path
        self.dual_db = dual_db
        self.baseline: Dict[str, Dict[str, Any]] = {}  # {filepath: {sha256, size, mtime}}
        self._ensure_tables()
        self._load_baseline()

    def _ensure_tables(self):
        """创建完整性基线表"""
        if not self.db_path:
            return
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mt_code_integrity_baseline (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filepath TEXT UNIQUE NOT NULL,
                    sha256 TEXT NOT NULL,
                    file_size INTEGER,
                    mtime TEXT,
                    baseline_created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    last_checked_at TEXT,
                    last_status TEXT DEFAULT 'ok',
                    modified_count INTEGER DEFAULT 0
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"创建完整性基线表失败: {e}")

    def _load_baseline(self):
        """从数据库加载基线"""
        if not self.db_path:
            return
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mt_code_integrity_baseline")
            for row in cursor.fetchall():
                self.baseline[row['filepath']] = {
                    'sha256': row['sha256'],
                    'size': row['file_size'],
                    'mtime': row['mtime'],
                }
            conn.close()
            logger.info(f"加载代码完整性基线: {len(self.baseline)} 个文件")
        except Exception as e:
            logger.error(f"加载基线失败: {e}")

    def _compute_sha256(self, filepath: str) -> str:
        """计算文件 SHA256（分块处理大文件）"""
        h = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(65536)  # 64KB 块
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        except Exception as e:
            logger.error(f"计算SHA256失败 {filepath}: {e}")
            return ""

    def _scan_files(self) -> List[str]:
        """扫描项目目录中的所有需要校验的文件"""
        files = []
        for root, dirs, filenames in os.walk(self.project_dir):
            # 忽略目录
            rel_root = os.path.relpath(root, self.project_dir)
            if any(ign in rel_root for ign in self.IGNORED_DIRS):
                continue
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in self.CHECKED_EXTENSIONS:
                    files.append(os.path.join(root, filename))
        return files

    def generate_baseline(self) -> Dict[str, Any]:
        """生成完整性基线（首次运行或重置）"""
        files = self._scan_files()
        self.baseline.clear()
        count = 0
        for filepath in files:
            rel_path = os.path.relpath(filepath, self.project_dir)
            sha256 = self._compute_sha256(filepath)
            if sha256:
                stat = os.stat(filepath)
                self.baseline[rel_path] = {
                    'sha256': sha256,
                    'size': stat.st_size,
                    'mtime': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
                count += 1

        # 落库
        self._save_baseline()
        logger.info(f"完整性基线已生成: {count} 个文件")
        return {
            'total_files': count,
            'baseline_created_at': datetime.now().isoformat(),
        }

    def _save_baseline(self):
        """保存基线到数据库"""
        if not self.db_path:
            return
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM mt_code_integrity_baseline")
            for filepath, info in self.baseline.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO mt_code_integrity_baseline
                    (filepath, sha256, file_size, mtime, last_checked_at, last_status)
                    VALUES (?, ?, ?, ?, ?, 'ok')
                """, (filepath, info['sha256'], info['size'], info['mtime'],
                      datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"保存基线失败: {e}")

    def check_integrity(self) -> List[Dict[str, Any]]:
        """
        检查代码完整性

        Returns:
            发现的问题列表
        """
        issues = []
        current_files = set()
        files = self._scan_files()

        for filepath in files:
            rel_path = os.path.relpath(filepath, self.project_dir)
            current_files.add(rel_path)
            sha256 = self._compute_sha256(filepath)
            if not sha256:
                continue

            stat = os.stat(filepath)
            if rel_path in self.baseline:
                baseline_info = self.baseline[rel_path]
                if sha256 != baseline_info['sha256']:
                    # 文件被修改
                    issues.append({
                        'type': AlertType.CODE_MODIFIED.value,
                        'level': AlertLevel.WARNING.value,
                        'filepath': rel_path,
                        'old_sha256': baseline_info['sha256'][:16] + '...',
                        'new_sha256': sha256[:16] + '...',
                        'old_size': baseline_info['size'],
                        'new_size': stat.st_size,
                        'message': f'文件被修改: {rel_path}',
                    })
                    # 更新基线
                    self.baseline[rel_path] = {
                        'sha256': sha256,
                        'size': stat.st_size,
                        'mtime': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
            else:
                # 新增文件
                issues.append({
                    'type': AlertType.CODE_ADDED.value,
                    'level': AlertLevel.INFO.value,
                    'filepath': rel_path,
                    'sha256': sha256[:16] + '...',
                    'size': stat.st_size,
                    'message': f'新增文件: {rel_path}',
                })
                self.baseline[rel_path] = {
                    'sha256': sha256,
                    'size': stat.st_size,
                    'mtime': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }

        # 检查被删除的文件
        for baseline_file in list(self.baseline.keys()):
            if baseline_file not in current_files:
                issues.append({
                    'type': AlertType.CODE_DELETED.value,
                    'level': AlertLevel.WARNING.value,
                    'filepath': baseline_file,
                    'message': f'文件被删除: {baseline_file}',
                })
                del self.baseline[baseline_file]

        # 保存更新后的基线
        if issues:
            self._save_baseline()

        return issues

    def get_status(self) -> Dict[str, Any]:
        """获取完整性校验器状态"""
        return {
            'total_files': len(self.baseline),
            'project_dir': self.project_dir,
            'checked_extensions': list(self.CHECKED_EXTENSIONS),
        }


# ============================================================================
# 反编译行为检测器
# ============================================================================

class DecompilerDetector:
    """反编译行为检测器 — 进程扫描 + 调试器检测"""

    # 已知反编译工具进程名
    DECOMPILER_PROCESSES = {
        'uncompyle', 'uncompyle2', 'uncompyle6', 'decompyle3',
        'pycdc', 'pycdas', 'decompyle++', 'pydisasm',
        'jd-gui', 'jd-cli',  # Java反编译
        'ghidra', 'ida', 'ida64', 'idaq',  # 通用反编译
        'radare2', 'r2', 'rabin2',
        'dnspy', 'dotpeek',  # .NET反编译
    }

    # 已知调试器进程名
    DEBUGGER_PROCESSES = {
        'gdb', 'lldb', 'lldb-mi', 'strace', 'ltrace', 'ptrace',
        'pdb', 'ipdb', 'pudb', 'pydb', 'debugpy',
        'frida', 'frida-server', 'frida-trace',
        'x64dbg', 'x32dbg', 'ollydbg', 'windbg',
    }

    def __init__(self):
        self.last_scan_time = None
        self.detected_processes: deque = deque(maxlen=100)
        self.stats = {
            'total_scans': 0,
            'decompilers_detected': 0,
            'debuggers_detected': 0,
            'suspicious_access': 0,
        }

    def _get_process_list(self) -> List[Dict[str, Any]]:
        """获取进程列表"""
        try:
            import psutil
            procs = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'username']):
                try:
                    info = proc.info
                    procs.append({
                        'pid': info['pid'],
                        'name': info['name'] or '',
                        'cmdline': ' '.join(info['cmdline'] or []),
                        'username': info['username'] or '',
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return procs
        except ImportError:
            # psutil 不可用，使用 ps 命令
            return self._get_process_list_ps()

    def _get_process_list_ps(self) -> List[Dict[str, Any]]:
        """使用 ps 命令获取进程列表（fallback）"""
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True, text=True, timeout=10
            )
            procs = []
            for line in result.stdout.strip().split('\n')[1:]:  # 跳过header
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    procs.append({
                        'pid': int(parts[1]),
                        'name': parts[10].split()[0] if parts[10].split() else '',
                        'cmdline': parts[10],
                        'username': parts[0],
                    })
            return procs
        except Exception as e:
            logger.error(f"获取进程列表失败: {e}")
            return []

    def scan_processes(self) -> List[Dict[str, Any]]:
        """
        扫描进程列表，检测反编译工具和调试器

        Returns:
            检测到的可疑进程列表
        """
        alerts = []
        procs = self._get_process_list()
        self.stats['total_scans'] += 1
        self.last_scan_time = datetime.now().isoformat()

        for proc in procs:
            name_lower = proc['name'].lower()
            cmdline_lower = proc['cmdline'].lower()

            # 检测反编译工具
            for decompiler in self.DECOMPILER_PROCESSES:
                if decompiler in name_lower or decompiler in cmdline_lower:
                    alert = {
                        'type': AlertType.DECOMPILER_DETECTED.value,
                        'level': AlertLevel.CRITICAL.value,
                        'pid': proc['pid'],
                        'process_name': proc['name'],
                        'cmdline': proc['cmdline'][:200],
                        'username': proc['username'],
                        'message': f'检测到反编译工具: {proc["name"]} (PID:{proc["pid"]})',
                    }
                    alerts.append(alert)
                    self.detected_processes.append(alert)
                    self.stats['decompilers_detected'] += 1
                    break

            # 检测调试器
            for debugger in self.DEBUGGER_PROCESSES:
                if debugger in name_lower or debugger in cmdline_lower:
                    # 排除自身进程
                    if proc['pid'] == os.getpid():
                        continue
                    alert = {
                        'type': AlertType.DEBUGGER_DETECTED.value,
                        'level': AlertLevel.HIGH.value,
                        'pid': proc['pid'],
                        'process_name': proc['name'],
                        'cmdline': proc['cmdline'][:200],
                        'username': proc['username'],
                        'message': f'检测到调试器: {proc["name"]} (PID:{proc["pid"]})',
                    }
                    alerts.append(alert)
                    self.detected_processes.append(alert)
                    self.stats['debuggers_detected'] += 1
                    break

        return alerts

    def check_pyc_access(self, project_dir: str) -> List[Dict[str, Any]]:
        """检查 .pyc 文件异常访问（检查 __pycache__ 目录）"""
        alerts = []
        pyc_dir = os.path.join(project_dir, '__pycache__')
        if os.path.exists(pyc_dir):
            try:
                files = os.listdir(pyc_dir)
                if files:
                    alerts.append({
                        'type': AlertType.PYC_TAMPERED.value,
                        'level': AlertLevel.INFO.value,
                        'filepath': '__pycache__',
                        'file_count': len(files),
                        'message': f'发现 {len(files)} 个 .pyc 文件',
                    })
            except Exception:
                pass
        return alerts

    def get_status(self) -> Dict[str, Any]:
        """获取检测器状态"""
        return {
            'last_scan_time': self.last_scan_time,
            'stats': self.stats.copy(),
            'monitored_decompilers': len(self.DECOMPILER_PROCESSES),
            'monitored_debuggers': len(self.DEBUGGER_PROCESSES),
        }


# ============================================================================
# 代码水印注入器
# ============================================================================

class CodeWatermarker:
    """代码水印注入器 — 注释水印 + 不可见字符"""

    # 水印标识前缀（不可见 Unicode 字符 + 注释）
    WATERMARK_PREFIX = '# \u200b\u200c\u200dMTSCOS_WMARK_'  # 零宽字符 + 标识

    def __init__(self, db_path: str = None, dual_db=None):
        self.db_path = db_path
        self.dual_db = dual_db
        self.watermarks: Dict[str, Dict[str, Any]] = {}
        self._ensure_tables()

    def _ensure_tables(self):
        """创建水印注册表"""
        if not self.db_path:
            return
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mt_code_watermarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    watermark_id TEXT UNIQUE NOT NULL,
                    filepath TEXT NOT NULL,
                    line_number INTEGER,
                    watermark_content TEXT,
                    injected_at TEXT DEFAULT (datetime('now', 'localtime')),
                    verified INTEGER DEFAULT 0,
                    last_verified_at TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"创建水印表失败: {e}")

    def inject_watermark(self, filepath: str, watermark_id: str = None) -> Dict[str, Any]:
        """
        向文件注入水印

        Args:
            filepath: 目标文件路径
            watermark_id: 水印ID（默认自动生成）

        Returns:
            注入结果
        """
        if not os.path.exists(filepath):
            return {'success': False, 'error': '文件不存在'}

        watermark_id = watermark_id or f"WM_{int(time.time())}_{os.path.basename(filepath)[:20]}"
        watermark_content = f"{self.WATERMARK_PREFIX}{watermark_id}"

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 检查是否已有水印
            for i, line in enumerate(lines):
                if 'MTSCOS_WMARK_' in line:
                    return {
                        'success': True,
                        'already_exists': True,
                        'watermark_id': watermark_id,
                        'line_number': i + 1,
                        'message': '文件已有水印',
                    }

            # 在文件末尾注入水印
            lines.append(f'\n{watermark_content}\n')

            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            line_number = len(lines)

            # 落库
            self._save_watermark(watermark_id, filepath, line_number, watermark_content)

            logger.info(f"水印已注入: {filepath} (行 {line_number})")
            return {
                'success': True,
                'watermark_id': watermark_id,
                'filepath': filepath,
                'line_number': line_number,
                'content': watermark_content,
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _save_watermark(self, watermark_id: str, filepath: str, line_number: int, content: str):
        """保存水印到数据库"""
        if not self.db_path:
            return
        try:
            if self.dual_db:
                self.dual_db.execute_write(
                    "INSERT OR REPLACE INTO mt_code_watermarks (watermark_id, filepath, line_number, watermark_content) VALUES (?, ?, ?, ?)",
                    (watermark_id, filepath, line_number, content)
                )
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO mt_code_watermarks (watermark_id, filepath, line_number, watermark_content) VALUES (?, ?, ?, ?)",
                    (watermark_id, filepath, line_number, content)
                )
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"保存水印失败: {e}")

    def verify_watermark(self, filepath: str) -> Dict[str, Any]:
        """
        验证文件中的水印

        Returns:
            验证结果
        """
        if not os.path.exists(filepath):
            return {'success': False, 'error': '文件不存在'}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'MTSCOS_WMARK_' in content:
                # 提取水印ID
                for line in content.split('\n'):
                    if 'MTSCOS_WMARK_' in line:
                        idx = line.find('MTSCOS_WMARK_')
                        watermark_id = line[idx:].strip()
                        return {
                            'success': True,
                            'verified': True,
                            'watermark_id': watermark_id,
                            'filepath': filepath,
                            'message': '水印验证通过',
                        }

            return {
                'success': True,
                'verified': False,
                'filepath': filepath,
                'message': '未找到水印',
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def inject_to_project(self, project_dir: str, key_files: List[str] = None) -> List[Dict[str, Any]]:
        """向项目关键文件批量注入水印"""
        results = []
        if key_files is None:
            # 默认关键文件
            key_files = [
                'app.py', 'server_real_db.py',
                'ai_engines/auto_maintenance_agent.py',
                'ai_engines/database_crypto.py',
                'ai_engines/anti_decompilation.py',
            ]

        for rel_path in key_files:
            filepath = os.path.join(project_dir, rel_path)
            if os.path.exists(filepath):
                result = self.inject_watermark(filepath)
                results.append(result)

        return results

    def get_status(self) -> Dict[str, Any]:
        """获取水印器状态"""
        return {
            'total_watermarks': len(self.watermarks),
            'watermark_prefix': 'MTSCOS_WMARK_',
        }


# ============================================================================
# 防护动作执行器
# ============================================================================

class ProtectionExecutor:
    """防护动作执行器 — .pyc 清理 + 告警上报"""

    def __init__(self, project_dir: str, db_path: str = None, dual_db=None):
        self.project_dir = project_dir
        self.db_path = db_path
        self.dual_db = dual_db
        self.stats = {
            'pyc_cleaned': 0,
            'alerts_generated': 0,
            'alerts_reported': 0,
        }
        self._ensure_tables()

    def _ensure_tables(self):
        """创建告警表"""
        if not self.db_path:
            return
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mt_anti_decompile_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    alert_type TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT,
                    details TEXT,
                    status TEXT DEFAULT 'detected',
                    detected_at TEXT DEFAULT (datetime('now', 'localtime')),
                    reported_at TEXT,
                    resolved_at TEXT,
                    resolved_by TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"创建告警表失败: {e}")

    def clean_pyc_files(self) -> Dict[str, Any]:
        """清理项目中的 .pyc 文件"""
        cleaned = []
        total_size = 0

        for root, dirs, files in os.walk(self.project_dir):
            # 忽略目录
            if '__pycache__' in root or '.git' in root:
                continue
            for filename in files:
                if filename.endswith('.pyc') or filename.endswith('.pyo'):
                    filepath = os.path.join(root, filename)
                    try:
                        size = os.path.getsize(filepath)
                        os.remove(filepath)
                        cleaned.append(filepath)
                        total_size += size
                    except Exception as e:
                        logger.error(f"清理 .pyc 失败 {filepath}: {e}")

        self.stats['pyc_cleaned'] += len(cleaned)

        # 生成告警
        if cleaned:
            self.generate_alert(
                alert_type=AlertType.PYC_CLEANED.value,
                level=AlertLevel.INFO.value,
                message=f'清理 {len(cleaned)} 个 .pyc 文件 (释放 {total_size / 1024:.1f} KB)',
                details={'files': cleaned[:50], 'total_size': total_size}
            )

        return {
            'cleaned_count': len(cleaned),
            'total_size': total_size,
            'files': cleaned,
        }

    def generate_alert(self, alert_type: str, level: str,
                       message: str, details: Dict = None) -> Dict[str, Any]:
        """生成告警并落库"""
        alert_id = f"ALERT_{int(time.time()*1000)}_{level}"
        alert = {
            'alert_id': alert_id,
            'alert_type': alert_type,
            'level': level,
            'message': message,
            'details': json.dumps(details or {}, ensure_ascii=False),
            'status': AlertStatus.DETECTED.value,
            'detected_at': datetime.now().isoformat(),
        }

        # 落库
        if self.db_path:
            try:
                if self.dual_db:
                    self.dual_db.execute_write(
                        """INSERT OR REPLACE INTO mt_anti_decompile_alerts
                        (alert_id, alert_type, level, message, details, status, detected_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (alert['alert_id'], alert['alert_type'], alert['level'],
                         alert['message'], alert['details'], alert['status'], alert['detected_at'])
                    )
                else:
                    conn = sqlite3.connect(self.db_path, timeout=10)
                    cursor = conn.cursor()
                    cursor.execute(
                        """INSERT OR REPLACE INTO mt_anti_decompile_alerts
                        (alert_id, alert_type, level, message, details, status, detected_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (alert['alert_id'], alert['alert_type'], alert['level'],
                         alert['message'], alert['details'], alert['status'], alert['detected_at'])
                    )
                    conn.commit()
                    conn.close()
            except Exception as e:
                logger.error(f"告警落库失败: {e}")

        self.stats['alerts_generated'] += 1
        logger.info(f"告警已生成: [{level}] {message}")
        return alert

    def get_alerts(self, limit: int = 50, level: str = None) -> List[Dict[str, Any]]:
        """获取告警列表"""
        if not self.db_path:
            return []
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if level:
                cursor.execute(
                    "SELECT * FROM mt_anti_decompile_alerts WHERE level = ? ORDER BY detected_at DESC LIMIT ?",
                    (level, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM mt_anti_decompile_alerts ORDER BY detected_at DESC LIMIT ?",
                    (limit,)
                )
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"获取告警失败: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return self.stats.copy()


# ============================================================================
# 反编译检测与防护系统（主类）
# ============================================================================

class AntiDecompilationGuard:
    """
    MTSCOS 反编译检测与防护系统

    使用方式：
        guard = AntiDecompilationGuard(project_dir='.', db_path='app.db')
        guard.run_check()  # 执行完整检测
    """

    VERSION = 'v1.0.0'
    GUARD_ID = 'anti_decompilation_guard_001'
    GUARD_NAME = 'MTSCOS反编译防护系统'

    def __init__(self, project_dir: str = None, db_path: str = None, dual_db=None):
        self.project_dir = project_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = db_path
        self.dual_db = dual_db

        # 子组件
        self.integrity_checker = CodeIntegrityChecker(self.project_dir, db_path, dual_db)
        self.decompiler_detector = DecompilerDetector()
        self.watermarker = CodeWatermarker(db_path, dual_db)
        self.protection_executor = ProtectionExecutor(self.project_dir, db_path, dual_db)

        # 运行状态
        self.last_check_time = None
        self.last_check_results = None
        self.stats = {
            'total_checks': 0,
            'total_alerts': 0,
            'critical_alerts': 0,
            'high_alerts': 0,
            'warning_alerts': 0,
            'info_alerts': 0,
        }

        logger.info(f"{self.GUARD_NAME} 已初始化 (v{self.VERSION})")

    def run_check(self) -> Dict[str, Any]:
        """
        执行完整检测

        Returns:
            检测结果汇总
        """
        start_time = time.time()
        all_alerts = []

        # 1. 代码完整性校验
        integrity_issues = self.integrity_checker.check_integrity()
        for issue in integrity_issues:
            alert = self.protection_executor.generate_alert(
                alert_type=issue['type'],
                level=issue['level'],
                message=issue['message'],
                details=issue
            )
            all_alerts.append(alert)

        # 2. 反编译行为检测
        decompiler_alerts = self.decompiler_detector.scan_processes()
        all_alerts.extend(decompiler_alerts)
        for alert in decompiler_alerts:
            self.protection_executor.generate_alert(
                alert_type=alert['type'],
                level=alert['level'],
                message=alert['message'],
                details=alert
            )

        # 3. .pyc 文件访问检查
        pyc_alerts = self.decompiler_detector.check_pyc_access(self.project_dir)
        for alert in pyc_alerts:
            self.protection_executor.generate_alert(
                alert_type=alert['type'],
                level=alert['level'],
                message=alert['message'],
                details=alert
            )

        # 更新统计
        self.stats['total_checks'] += 1
        self.stats['total_alerts'] += len(all_alerts)
        for alert in all_alerts:
            level = alert.get('level', 'info')
            if level == 'critical':
                self.stats['critical_alerts'] += 1
            elif level == 'high':
                self.stats['high_alerts'] += 1
            elif level == 'warning':
                self.stats['warning_alerts'] += 1
            else:
                self.stats['info_alerts'] += 1

        elapsed = time.time() - start_time
        self.last_check_time = datetime.now().isoformat()
        self.last_check_results = {
            'total_alerts': len(all_alerts),
            'elapsed_seconds': round(elapsed, 2),
            'integrity_issues': len(integrity_issues),
            'decompiler_alerts': len(decompiler_alerts),
            'pyc_alerts': len(pyc_alerts),
        }

        return {
            'guard_id': self.GUARD_ID,
            'version': self.VERSION,
            'check_time': self.last_check_time,
            'elapsed_seconds': round(elapsed, 2),
            'total_alerts': len(all_alerts),
            'alerts_by_level': {
                'critical': sum(1 for a in all_alerts if a.get('level') == 'critical'),
                'high': sum(1 for a in all_alerts if a.get('level') == 'high'),
                'warning': sum(1 for a in all_alerts if a.get('level') == 'warning'),
                'info': sum(1 for a in all_alerts if a.get('level') == 'info'),
            },
            'integrity_issues': len(integrity_issues),
            'decompiler_alerts': len(decompiler_alerts),
            'pyc_alerts': len(pyc_alerts),
        }

    def clean_pyc(self) -> Dict[str, Any]:
        """清理 .pyc 文件"""
        return self.protection_executor.clean_pyc_files()

    def inject_watermarks(self, key_files: List[str] = None) -> List[Dict[str, Any]]:
        """向关键文件注入水印"""
        return self.watermarker.inject_to_project(self.project_dir, key_files)

    def verify_watermark(self, filepath: str) -> Dict[str, Any]:
        """验证水印"""
        return self.watermarker.verify_watermark(filepath)

    def generate_baseline(self) -> Dict[str, Any]:
        """生成完整性基线"""
        return self.integrity_checker.generate_baseline()

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'guard_id': self.GUARD_ID,
            'guard_name': self.GUARD_NAME,
            'version': self.VERSION,
            'last_check_time': self.last_check_time,
            'last_check_results': self.last_check_results,
            'stats': self.stats,
            'integrity_checker': self.integrity_checker.get_status(),
            'decompiler_detector': self.decompiler_detector.get_status(),
            'watermarker': self.watermarker.get_status(),
            'protection_executor': self.protection_executor.get_stats(),
        }

    def get_alerts(self, limit: int = 50, level: str = None) -> List[Dict[str, Any]]:
        """获取告警列表"""
        return self.protection_executor.get_alerts(limit, level)


# ============================================================================
# 单例管理
# ============================================================================

_guard_instance: Optional[AntiDecompilationGuard] = None
_guard_lock = threading.Lock()


def get_anti_decompilation_guard(project_dir: str = None, db_path: str = None,
                                  dual_db=None) -> AntiDecompilationGuard:
    """获取反编译防护系统单例"""
    global _guard_instance
    if _guard_instance is None:
        with _guard_lock:
            if _guard_instance is None:
                _guard_instance = AntiDecompilationGuard(
                    project_dir=project_dir,
                    db_path=db_path,
                    dual_db=dual_db,
                )
    return _guard_instance
