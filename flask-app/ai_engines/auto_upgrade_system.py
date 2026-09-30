#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 自动升级系统 (AutoUpgradeSystem)
========================================
功能：
  - 4大升级目标检测：系统自身(Git) / 数据库Schema / AI引擎与规则 / 依赖包
  - 半自动策略：检测 → 生成提案 → 审批 → 执行（含回滚快照）
  - 升级前自动快照 + 失败自动回滚
  - SSOT 持久化（5张表 + 双库双写 + 审计日志）

遵循：
  - SSOT 原则（数据库为权威源）
  - 双库双写
  - §14 强制开发流程
  - 超级管理员 wuchenghao15 无视审批可强制执行

版本: v1.0.0
"""

import os
import sys
import json
import time
import uuid
import sqlite3
import logging
import subprocess
import shutil
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('auto_upgrade_system')


# ============================================================================
# 枚举定义
# ============================================================================

class UpgradeTarget(Enum):
    """升级目标"""
    SYSTEM_SELF = "system_self"            # MTSCOS系统自身（Git代码/版本）
    DB_SCHEMA = "db_schema"                # 数据库Schema迁移
    AI_ENGINE_RULES = "ai_engine_rules"    # AI引擎/规则系统升级
    DEPENDENCIES = "dependencies"          # Python依赖包/环境升级


class UpgradeStatus(Enum):
    """升级状态机"""
    DETECTED = "detected"          # 已检测到可用升级
    PROPOSED = "proposed"          # 已生成提案（待审批）
    APPROVED = "approved"          # 已审批通过
    REJECTED = "rejected"          # 审批拒绝
    EXECUTING = "executing"        # 执行中
    COMPLETED = "completed"        # 升级完成
    FAILED = "failed"              # 升级失败
    ROLLED_BACK = "rolled_back"    # 已回滚
    SKIPPED = "skipped"            # 跳过（无可用升级/不满足条件）


class UpgradeRisk(Enum):
    """升级风险等级"""
    LOW = "low"            # 低风险（PATCH/依赖小版本）
    MEDIUM = "medium"      # 中风险（MINOR/Schema加列）
    HIGH = "high"          # 高风险（MAJOR/Schema改列）
    CRITICAL = "critical"  # 极高风险（破坏性变更）


class UpgradeStrategy(Enum):
    """升级执行策略"""
    HOT_RELOAD = "hot_reload"      # 热更新（不重启）
    GRACEFUL = "graceful"          # 优雅重启
    ROLLING = "rolling"            # 灰度滚动
    FULL_STOP = "full_stop"        # 全停升级


# ============================================================================
# 数据模型
# ============================================================================

class UpgradeItem:
    """单个升级项"""

    def __init__(self, item_id: str, target: UpgradeTarget, title: str,
                 current_version: str, target_version: str,
                 risk: UpgradeRisk = UpgradeRisk.LOW,
                 strategy: UpgradeStrategy = UpgradeStrategy.HOT_RELOAD,
                 details: Dict = None):
        self.item_id = item_id
        # 枚举校验：字符串自动转换，非法值抛 ValueError（防注入/防脏数据）
        self.target = target if isinstance(target, UpgradeTarget) else UpgradeTarget(target)
        self.title = title
        self.current_version = current_version
        self.target_version = target_version
        self.risk = risk if isinstance(risk, UpgradeRisk) else UpgradeRisk(risk)
        self.strategy = strategy if isinstance(strategy, UpgradeStrategy) else UpgradeStrategy(strategy)
        self.details = details or {}
        self.status = UpgradeStatus.DETECTED
        self.detected_at = datetime.now().isoformat()
        self.description = ""

    def to_dict(self) -> Dict:
        return {
            'item_id': self.item_id,
            'target': self.target.value,
            'title': self.title,
            'current_version': self.current_version,
            'target_version': self.target_version,
            'risk': self.risk.value,
            'strategy': self.strategy.value,
            'details': self.details,
            'status': self.status.value,
            'detected_at': self.detected_at,
            'description': self.description,
        }


class UpgradeProposal:
    """升级提案（半自动入口：检测→提案→审批→执行）"""

    def __init__(self, proposal_id: str, items: List[UpgradeItem],
                 summary: str = ""):
        self.proposal_id = proposal_id
        self.items = items
        self.summary = summary or f"升级提案 {proposal_id}: 含 {len(items)} 个升级项"
        self.status = UpgradeStatus.PROPOSED
        self.created_at = datetime.now().isoformat()
        self.approved_at = None
        self.approved_by = None
        self.executed_at = None
        self.execution_id = None
        self.risk_assessment = self._assess_risk()

    def _assess_risk(self) -> str:
        """汇总风险评估"""
        if not self.items:
            return UpgradeRisk.LOW.value
        risk_order = [UpgradeRisk.CRITICAL, UpgradeRisk.HIGH,
                      UpgradeRisk.MEDIUM, UpgradeRisk.LOW]
        max_risk = UpgradeRisk.LOW
        for item in self.items:
            if risk_order.index(item.risk) < risk_order.index(max_risk):
                max_risk = item.risk
        return max_risk.value

    def to_dict(self) -> Dict:
        return {
            'proposal_id': self.proposal_id,
            'items': [item.to_dict() for item in self.items],
            'summary': self.summary,
            'status': self.status.value,
            'created_at': self.created_at,
            'approved_at': self.approved_at,
            'approved_by': self.approved_by,
            'executed_at': self.executed_at,
            'execution_id': self.execution_id,
            'risk_assessment': self.risk_assessment,
            'item_count': len(self.items),
        }


# ============================================================================
# 升级检测器
# ============================================================================

class SystemSelfDetector:
    """系统自身升级检测器（Git远程对比）"""

    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.name = "系统自身检测器"

    def _run_git(self, *args) -> Tuple[bool, str]:
        """安全执行git命令"""
        try:
            result = subprocess.run(
                ['git'] + list(args),
                cwd=self.project_dir,
                capture_output=True, text=True, timeout=30,
            )
            return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
        except Exception as e:
            return False, str(e)

    def detect(self) -> List[UpgradeItem]:
        items = []
        ok, current_commit = self._run_git('rev-parse', '--short', 'HEAD')
        if not ok:
            return items

        # 检查远程是否有新提交
        ok_fetch, _ = self._run_git('fetch', '--dry-run')
        ok_log, remote_log = self._run_git(
            'log', 'HEAD..origin/main', '--oneline')
        if ok_log and remote_log:
            commit_count = len([l for l in remote_log.split('\n') if l.strip()])
            if commit_count > 0:
                risk = UpgradeRisk.HIGH if commit_count > 10 else UpgradeRisk.MEDIUM
                items.append(UpgradeItem(
                    item_id=f"SYS_GIT_{int(time.time())}",
                    target=UpgradeTarget.SYSTEM_SELF,
                    title=f"Git远程有 {commit_count} 个新提交",
                    current_version=current_commit,
                    target_version="origin/main",
                    risk=risk,
                    strategy=UpgradeStrategy.GRACEFUL,
                    details={'commit_count': commit_count, 'commits': remote_log[:500]},
                ))
                items[-1].description = f"远程main分支领先本地 {commit_count} 个提交，建议 git pull 升级"

        return items


class DbSchemaDetector:
    """数据库Schema迁移检测器"""

    def __init__(self, db_path: str = None, dual_db=None):
        self.db_path = db_path
        self.dual_db = dual_db
        self.name = "数据库Schema检测器"

    def _get_connection(self):
        if self.dual_db:
            return self.dual_db.get_connection()
        return sqlite3.connect(self.db_path, timeout=10)

    def _query(self, sql: str, params: tuple = ()) -> List[Dict]:
        if self.dual_db:
            return self.dual_db.execute_query(sql, params)
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def detect(self) -> List[UpgradeItem]:
        items = []
        if not self.db_path and not self.dual_db:
            return items

        try:
            # 检查 schema_version 表是否存在
            rows = self._query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='mt_schema_version'")
            if not rows:
                # 无版本表 → 建议创建（初版迁移）
                items.append(UpgradeItem(
                    item_id=f"DB_SCHEMA_INIT_{int(time.time())}",
                    target=UpgradeTarget.DB_SCHEMA,
                    title="Schema版本表未初始化",
                    current_version="v0",
                    target_version="v1",
                    risk=UpgradeRisk.MEDIUM,
                    strategy=UpgradeStrategy.HOT_RELOAD,
                    details={'action': 'create_schema_version_table'},
                ))
                items[-1].description = "建议创建 mt_schema_version 表以支持版本化迁移"
            else:
                # 查询当前版本
                ver_rows = self._query(
                    "SELECT version, applied_at FROM mt_schema_version ORDER BY id DESC LIMIT 1")
                current = ver_rows[0]['version'] if ver_rows else 'v0'
                # 检查是否有待应用的迁移（这里简化：对比预设目标版本）
                target = self._get_target_schema_version()
                if self._version_lt(current, target):
                    items.append(UpgradeItem(
                        item_id=f"DB_SCHEMA_MIG_{int(time.time())}",
                        target=UpgradeTarget.DB_SCHEMA,
                        title=f"数据库Schema可从 {current} 迁移到 {target}",
                        current_version=current,
                        target_version=target,
                        risk=UpgradeRisk.MEDIUM,
                        strategy=UpgradeStrategy.HOT_RELOAD,
                        details={'current': current, 'target': target},
                    ))
                    items[-1].description = f"检测到Schema版本落后，建议执行幂等迁移 {current}→{target}"
        except Exception as e:
            logger.warning(f"Schema检测失败: {e}")

        return items

    @staticmethod
    def _version_lt(v1: str, v2: str) -> bool:
        """比较版本 v1 < v2"""
        def parse(v):
            nums = []
            for p in v.replace('v', '').split('.'):
                try:
                    nums.append(int(p))
                except ValueError:
                    nums.append(0)
            return nums
        return parse(v1) < parse(v2)

    def _get_target_schema_version(self) -> str:
        """获取目标Schema版本（从迁移脚本目录推断）"""
        migrations_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'db', 'migrations')
        if not os.path.exists(migrations_dir):
            return 'v1'
        versions = sorted([f for f in os.listdir(migrations_dir)
                          if f.endswith('.sql')])
        return f'v{len(versions) + 1}' if versions else 'v1'


class AiEngineDetector:
    """AI引擎/规则系统升级检测器"""

    # 已知AI引擎及其版本（与auto_maintenance_agent对齐）
    KNOWN_ENGINES = {
        'auto_maintenance_agent': 'v2.4.0',
        'anti_decompilation': 'v1.0.0',
        'database_crypto': 'v1.0.0',
        'json_db_sync': 'v1.0.0',
        'ai_brain': 'v1.0.0',
        'ai_employees': 'v1.0.0',
    }

    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.name = "AI引擎检测器"

    def detect(self) -> List[UpgradeItem]:
        items = []
        engines_dir = os.path.join(self.project_dir, 'ai_engines')
        if not os.path.exists(engines_dir):
            return items

        for engine_name, known_ver in self.KNOWN_ENGINES.items():
            engine_path = os.path.join(engines_dir, f'{engine_name}.py')
            if not os.path.exists(engine_path):
                continue
            # 读取文件头部版本声明
            actual_ver = self._read_version(engine_path)
            if actual_ver and self._version_lt(actual_ver, known_ver):
                items.append(UpgradeItem(
                    item_id=f"AI_ENGINE_{engine_name}_{int(time.time())}",
                    target=UpgradeTarget.AI_ENGINE_RULES,
                    title=f"AI引擎 {engine_name} 可升级",
                    current_version=actual_ver,
                    target_version=known_ver,
                    risk=UpgradeRisk.MEDIUM,
                    strategy=UpgradeStrategy.ROLLING,
                    details={'engine': engine_name, 'path': engine_path},
                ))
                items[-1].description = f"{engine_name}: {actual_ver} → {known_ver}（灰度发布）"

        # 规则库检测（检查规则文件mtime）
        rules_dir = os.path.join(self.project_dir, '.trae', 'rules')
        if os.path.exists(rules_dir):
            for f in os.listdir(rules_dir):
                if f.endswith('.md'):
                    path = os.path.join(rules_dir, f)
                    mtime = os.path.getmtime(path)
                    age_days = (time.time() - mtime) / 86400
                    if age_days < 1:
                        # 规则文件1天内更新过 → 建议同步到AI脑库
                        items.append(UpgradeItem(
                            item_id=f"AI_RULE_{f}_{int(time.time())}",
                            target=UpgradeTarget.AI_ENGINE_RULES,
                            title=f"规则文件 {f} 近期更新",
                            current_version=datetime.fromtimestamp(mtime).isoformat(),
                            target_version="sync_to_brain",
                            risk=UpgradeRisk.LOW,
                            strategy=UpgradeStrategy.HOT_RELOAD,
                            details={'file': f, 'age_days': round(age_days, 1)},
                        ))
                        items[-1].description = f"规则文件 {f} 在 {age_days:.1f} 天内更新，建议同步到AI脑库"

        return items

    @staticmethod
    def _read_version(filepath: str) -> Optional[str]:
        """从文件读取版本号"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f.readlines()[:50]:
                    if 'VERSION' in line and '=' in line and 'v' in line:
                        # 提取 v1.0.0 形式
                        import re
                        m = re.search(r'v\d+\.\d+\.\d+', line)
                        if m:
                            return m.group(0)
        except Exception:
            pass
        return None

    @staticmethod
    def _version_lt(v1: str, v2: str) -> bool:
        def parse(v):
            return [int(x) if x.isdigit() else 0
                    for x in v.replace('v', '').split('.')]
        try:
            return parse(v1) < parse(v2)
        except Exception:
            return False


class DependencyDetector:
    """Python依赖包升级检测器"""

    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.name = "依赖包检测器"

    def detect(self) -> List[UpgradeItem]:
        items = []
        # 检查 requirements.txt 是否存在
        req_path = os.path.join(self.project_dir, 'requirements.txt')
        if not os.path.exists(req_path):
            return items

        try:
            # 使用 pip list --outdated 检测过期依赖（非阻塞，超时保护）
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--outdated',
                 '--format=json'],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0 and result.stdout.strip():
                outdated = json.loads(result.stdout)
                for pkg in outdated[:20]:  # 限制前20个
                    name = pkg.get('name', '')
                    current = pkg.get('version', '')
                    latest = pkg.get('latest_version', '')
                    if name and latest:
                        risk = UpgradeRisk.HIGH if self._is_major_bump(current, latest) else UpgradeRisk.LOW
                        items.append(UpgradeItem(
                            item_id=f"DEP_{name}_{int(time.time())}",
                            target=UpgradeTarget.DEPENDENCIES,
                            title=f"依赖 {name} 可升级",
                            current_version=current,
                            target_version=latest,
                            risk=risk,
                            strategy=UpgradeStrategy.GRACEFUL,
                            details={'package': name, 'current': current, 'latest': latest},
                        ))
                        items[-1].description = f"pip: {name} {current} → {latest}"
        except subprocess.TimeoutExpired:
            logger.warning("pip list --outdated 超时，跳过依赖检测")
        except Exception as e:
            logger.warning(f"依赖检测失败: {e}")

        return items

    @staticmethod
    def _is_major_bump(current: str, latest: str) -> bool:
        """判断是否为大版本升级"""
        try:
            c = [int(x) for x in current.split('.')]
            l = [int(x) for x in latest.split('.')]
            if len(c) >= 1 and len(l) >= 1:
                return l[0] > c[0]
        except Exception:
            pass
        return False


# ============================================================================
# 回滚管理器
# ============================================================================

class RollbackManager:
    """升级回滚管理器：升级前快照 + 失败回滚"""

    def __init__(self, db_path: str = None, dual_db=None,
                 backup_dir: str = None):
        self.db_path = db_path
        self.dual_db = dual_db
        self.backup_dir = backup_dir or os.path.join(
            os.path.dirname(db_path) if db_path else '/tmp',
            'upgrade_snapshots')
        os.makedirs(self.backup_dir, exist_ok=True)
        self.name = "回滚管理器"

    def create_snapshot(self, execution_id: str, items: List[UpgradeItem]) -> Dict[str, Any]:
        """创建升级前快照"""
        snapshot = {
            'snapshot_id': f"SNA_{execution_id}_{uuid.uuid4().hex[:8]}",
            'execution_id': execution_id,
            'created_at': datetime.now().isoformat(),
            'db_backup_path': None,
            'code_commit': None,
            'files_hash': {},
            'items': [item.to_dict() for item in items],
        }

        # 1. 数据库快照（复制db文件）
        if self.db_path and os.path.exists(self.db_path):
            db_backup = os.path.join(
                self.backup_dir, f"{execution_id}_db_snapshot.db")
            try:
                shutil.copy2(self.db_path, db_backup)
                snapshot['db_backup_path'] = db_backup
                # 计算hash用于校验
                with open(db_backup, 'rb') as f:
                    snapshot['files_hash']['db'] = hashlib.sha256(f.read()).hexdigest()
            except Exception as e:
                logger.error(f"数据库快照失败: {e}")

        # 2. 代码快照（记录当前git commit）
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                snapshot['code_commit'] = result.stdout.strip()
        except Exception:
            pass

        # 3. 持久化快照记录到数据库
        self._persist_snapshot(snapshot)

        logger.info(f"升级快照已创建: {snapshot['snapshot_id']}")
        return snapshot

    def rollback(self, execution_id: str) -> Dict[str, Any]:
        """执行回滚"""
        result = {
            'execution_id': execution_id,
            'success': False,
            'actions': [],
            'error': None,
        }

        try:
            snapshot = self._load_snapshot(execution_id)
            if not snapshot:
                result['error'] = f"未找到执行 {execution_id} 的快照"
                return result

            # 回滚数据库
            db_backup = snapshot.get('db_backup_path')
            if db_backup and os.path.exists(db_backup) and self.db_path:
                shutil.copy2(db_backup, self.db_path)
                result['actions'].append(f"数据库已从快照恢复: {db_backup}")

            # 回滚代码（git reset 到快照commit）
            code_commit = snapshot.get('code_commit')
            if code_commit:
                try:
                    r = subprocess.run(
                        ['git', 'reset', '--hard', code_commit],
                        capture_output=True, text=True, timeout=30,
                    )
                    if r.returncode == 0:
                        result['actions'].append(f"代码已回滚到 commit: {code_commit}")
                    else:
                        result['actions'].append(f"代码回滚失败(非致命): {r.stderr.strip()}")
                except Exception as e:
                    result['actions'].append(f"代码回滚异常(非致命): {e}")

            result['success'] = True
            self._update_rollback_status(execution_id, 'rolled_back')
            logger.warning(f"⚠️ 升级 {execution_id} 已回滚")

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"回滚失败: {e}")

        return result

    def _persist_snapshot(self, snapshot: Dict):
        """持久化快照记录"""
        sql = """INSERT INTO mt_upgrade_snapshots
                 (snapshot_id, execution_id, created_at, db_backup_path,
                  code_commit, files_hash_json, items_json)
                 VALUES (?, ?, ?, ?, ?, ?, ?)"""
        params = (
            snapshot['snapshot_id'],
            snapshot['execution_id'],
            snapshot['created_at'],
            snapshot.get('db_backup_path'),
            snapshot.get('code_commit'),
            json.dumps(snapshot.get('files_hash', {}), ensure_ascii=False),
            json.dumps(snapshot.get('items', []), ensure_ascii=False),
        )
        try:
            if self.dual_db:
                self.dual_db.execute_write(sql, params)
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.execute(sql, params)
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"持久化快照失败: {e}")

    def _load_snapshot(self, execution_id: str) -> Optional[Dict]:
        """加载快照"""
        sql = "SELECT * FROM mt_upgrade_snapshots WHERE execution_id = ? ORDER BY created_at DESC LIMIT 1"
        try:
            if self.dual_db:
                rows = self.dual_db.execute_query(sql, (execution_id,))
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.row_factory = sqlite3.Row
                rows = [dict(r) for r in conn.execute(sql, (execution_id,)).fetchall()]
                conn.close()
            if rows:
                r = rows[0]
                return {
                    'snapshot_id': r['snapshot_id'],
                    'execution_id': r['execution_id'],
                    'created_at': r['created_at'],
                    'db_backup_path': r['db_backup_path'],
                    'code_commit': r['code_commit'],
                    'files_hash': json.loads(r['files_hash_json'] or '{}'),
                    'items': json.loads(r['items_json'] or '[]'),
                }
        except Exception as e:
            logger.error(f"加载快照失败: {e}")
        return None

    def _update_rollback_status(self, execution_id: str, status: str):
        """更新回滚状态（DB恢复后执行记录可能已丢失，用 INSERT OR REPLACE 重建）"""
        now = datetime.now().isoformat()
        sql = """INSERT OR REPLACE INTO mt_upgrade_executions
                 (execution_id, proposal_id, approved_by, started_at, completed_at,
                  status, items_total, items_succeeded, items_failed, snapshot_id,
                  actions_json, rolled_back, error)
                 VALUES (
                    ?, NULL, NULL, ?, ?,
                    ?, 0, 0, 0, NULL,
                    '[]', 1, 'rolled back after db snapshot restore'
                 )"""
        params = (execution_id, now, now, status)
        try:
            if self.dual_db:
                self.dual_db.execute_write(sql, params)
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.execute(sql, params)
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"更新回滚状态失败: {e}")


# ============================================================================
# 升级执行器
# ============================================================================

class UpgradeExecutor:
    """升级执行器：执行已审批的升级（含回滚）"""

    def __init__(self, project_dir: str, db_path: str = None,
                 dual_db=None, rollback_manager: RollbackManager = None):
        self.project_dir = project_dir
        self.db_path = db_path
        self.dual_db = dual_db
        self.rollback_manager = rollback_manager or RollbackManager(
            db_path=db_path, dual_db=dual_db)
        self.name = "升级执行器"

    def execute_proposal(self, proposal: UpgradeProposal,
                         approved_by: str = None) -> Dict[str, Any]:
        """执行升级提案"""
        execution_id = f"EXEC_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        result = {
            'execution_id': execution_id,
            'proposal_id': proposal.proposal_id,
            'approved_by': approved_by,
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'status': UpgradeStatus.EXECUTING.value,
            'items_total': len(proposal.items),
            'items_succeeded': 0,
            'items_failed': 0,
            'actions': [],
            'rolled_back': False,
            'error': None,
        }

        # 创建升级前快照
        snapshot = self.rollback_manager.create_snapshot(execution_id, proposal.items)
        result['snapshot_id'] = snapshot['snapshot_id']

        # 持久化执行记录
        self._persist_execution(result, proposal)

        try:
            for item in proposal.items:
                item.status = UpgradeStatus.EXECUTING
                action_result = self._execute_item(item)
                result['actions'].append({
                    'item_id': item.item_id,
                    'title': item.title,
                    'target': item.target.value,
                    'result': action_result,
                })
                if action_result.get('success'):
                    item.status = UpgradeStatus.COMPLETED
                    result['items_succeeded'] += 1
                else:
                    item.status = UpgradeStatus.FAILED
                    result['items_failed'] += 1
                    # 高风险失败 → 自动回滚
                    if item.risk in (UpgradeRisk.HIGH, UpgradeRisk.CRITICAL):
                        result['error'] = f"高风险项失败: {item.title}"
                        break

            # 判断整体结果
            if result['items_failed'] > 0 and result['error']:
                # 自动回滚
                rollback_result = self.rollback_manager.rollback(execution_id)
                result['rolled_back'] = rollback_result['success']
                result['status'] = UpgradeStatus.ROLLED_BACK.value
                result['actions'].append({'rollback': rollback_result})
            elif result['items_failed'] > 0:
                result['status'] = UpgradeStatus.FAILED.value
            else:
                result['status'] = UpgradeStatus.COMPLETED.value

        except Exception as e:
            result['error'] = str(e)
            result['status'] = UpgradeStatus.FAILED.value
            # 异常时尝试回滚
            try:
                rollback_result = self.rollback_manager.rollback(execution_id)
                result['rolled_back'] = rollback_result['success']
                result['status'] = UpgradeStatus.ROLLED_BACK.value
            except Exception:
                pass

        result['completed_at'] = datetime.now().isoformat()

        # 更新执行记录
        self._update_execution(result)

        # 写审计日志
        self._write_audit_log(execution_id, 'execute', result)

        return result

    def _execute_item(self, item: UpgradeItem) -> Dict[str, Any]:
        """执行单个升级项"""
        res = {'success': False, 'action': '', 'output': '', 'error': None}
        try:
            if item.target == UpgradeTarget.SYSTEM_SELF:
                res = self._upgrade_system_self(item)
            elif item.target == UpgradeTarget.DB_SCHEMA:
                res = self._upgrade_db_schema(item)
            elif item.target == UpgradeTarget.AI_ENGINE_RULES:
                res = self._upgrade_ai_engine(item)
            elif item.target == UpgradeTarget.DEPENDENCIES:
                res = self._upgrade_dependency(item)
            else:
                res['error'] = f"未知升级目标: {item.target}"
        except Exception as e:
            res['error'] = str(e)
            logger.error(f"执行升级项失败 {item.title}: {e}")
        return res

    def _upgrade_system_self(self, item: UpgradeItem) -> Dict[str, Any]:
        """系统自身升级：git pull"""
        res = {'success': False, 'action': 'git_pull', 'output': '', 'error': None}
        try:
            result = subprocess.run(
                ['git', 'pull', 'origin', 'main'],
                cwd=self.project_dir,
                capture_output=True, text=True, timeout=120,
            )
            res['output'] = result.stdout + result.stderr
            res['success'] = (result.returncode == 0)
            if not res['success']:
                res['error'] = result.stderr.strip() or 'git pull 失败'
        except Exception as e:
            res['error'] = str(e)
        return res

    def _upgrade_db_schema(self, item: UpgradeItem) -> Dict[str, Any]:
        """数据库Schema迁移：幂等执行"""
        res = {'success': False, 'action': 'schema_migrate', 'output': '', 'error': None}
        try:
            action = item.details.get('action', 'migrate')
            if action == 'create_schema_version_table':
                sql = """CREATE TABLE IF NOT EXISTS mt_schema_version (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL,
                    applied_at TEXT NOT NULL,
                    description TEXT
                )"""
                if self.dual_db:
                    self.dual_db.execute_write(sql, ())
                else:
                    conn = sqlite3.connect(self.db_path, timeout=10)
                    conn.execute(sql)
                    conn.commit()
                    conn.close()
                # 记录版本
                self._record_schema_version('v1', '初始化Schema版本表')
                res['output'] = '已创建 mt_schema_version 表并记录 v1'
                res['success'] = True
            else:
                # 执行迁移脚本目录中的SQL
                migrations_dir = os.path.join(self.project_dir, 'db', 'migrations')
                if os.path.exists(migrations_dir):
                    scripts = sorted([f for f in os.listdir(migrations_dir)
                                     if f.endswith('.sql')])
                    executed = 0
                    for script in scripts:
                        path = os.path.join(migrations_dir, script)
                        with open(path, 'r', encoding='utf-8') as f:
                            sql_script = f.read()
                        # 幂等执行（忽略已存在的表/列错误）
                        try:
                            if self.dual_db:
                                self.dual_db.execute_write(sql_script, ())
                            else:
                                conn = sqlite3.connect(self.db_path, timeout=10)
                                conn.executescript(sql_script)
                                conn.commit()
                                conn.close()
                            executed += 1
                        except sqlite3.OperationalError as e:
                            if 'already exists' in str(e):
                                executed += 1  # 幂等：已存在视为成功
                    self._record_schema_version(item.target_version, f'迁移到 {item.target_version}')
                    res['output'] = f'执行 {executed} 个迁移脚本'
                    res['success'] = True
                else:
                    res['output'] = '无迁移脚本目录，仅记录版本'
                    self._record_schema_version(item.target_version, '无脚本版本记录')
                    res['success'] = True
        except Exception as e:
            res['error'] = str(e)
        return res

    def _upgrade_ai_engine(self, item: UpgradeItem) -> Dict[str, Any]:
        """AI引擎升级：记录+同步到脑库（灰度）"""
        res = {'success': False, 'action': 'ai_engine_upgrade', 'output': '', 'error': None}
        try:
            # AI引擎升级主要通过git pull获取新代码，这里记录升级动作
            engine = item.details.get('engine', 'unknown')
            res['output'] = f"AI引擎 {engine} 升级记录: {item.current_version} → {item.target_version}"
            # 写入脑库投喂记录（通过dual_db）
            if self.dual_db:
                self.dual_db.execute_write(
                    "INSERT INTO mt_upgrade_audit_log (action, target, details_json, created_at) VALUES (?, ?, ?, ?)",
                    ('ai_engine_upgrade', engine,
                     json.dumps({'from': item.current_version, 'to': item.target_version}, ensure_ascii=False),
                     datetime.now().isoformat()))
            res['success'] = True
        except Exception as e:
            res['error'] = str(e)
        return res

    def _upgrade_dependency(self, item: UpgradeItem) -> Dict[str, Any]:
        """依赖包升级：pip install --upgrade"""
        res = {'success': False, 'action': 'pip_upgrade', 'output': '', 'error': None}
        try:
            pkg = item.details.get('package', '')
            if not pkg:
                res['error'] = '未指定包名'
                return res
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade', pkg],
                capture_output=True, text=True, timeout=180,
            )
            res['output'] = result.stdout[-500:] + result.stderr[-500:]
            res['success'] = (result.returncode == 0)
            if not res['success']:
                res['error'] = result.stderr.strip() or 'pip install 失败'
        except subprocess.TimeoutExpired:
            res['error'] = f'pip install {pkg} 超时'
        except Exception as e:
            res['error'] = str(e)
        return res

    def _record_schema_version(self, version: str, description: str):
        """记录Schema版本（幂等）"""
        sql = "INSERT INTO mt_schema_version (version, applied_at, description) VALUES (?, ?, ?)"
        params = (version, datetime.now().isoformat(), description)
        try:
            if self.dual_db:
                self.dual_db.execute_write(sql, params)
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.execute(sql, params)
                conn.commit()
                conn.close()
        except Exception as e:
            logger.warning(f"记录Schema版本失败(非致命): {e}")

    def _persist_execution(self, result: Dict, proposal: UpgradeProposal):
        """持久化执行记录"""
        sql = """INSERT INTO mt_upgrade_executions
                 (execution_id, proposal_id, approved_by, started_at, completed_at,
                  status, items_total, items_succeeded, items_failed, snapshot_id,
                  actions_json, rolled_back, error)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        params = (
            result['execution_id'], result['proposal_id'], result.get('approved_by'),
            result['started_at'], result.get('completed_at'),
            result['status'], result['items_total'],
            result['items_succeeded'], result['items_failed'],
            result.get('snapshot_id'),
            json.dumps(result.get('actions', []), ensure_ascii=False),
            1 if result.get('rolled_back') else 0,
            result.get('error'),
        )
        try:
            if self.dual_db:
                self.dual_db.execute_write(sql, params)
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.execute(sql, params)
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"持久化执行记录失败: {e}")

    def _update_execution(self, result: Dict):
        """更新执行记录"""
        sql = """UPDATE mt_upgrade_executions
                 SET completed_at = ?, status = ?, items_succeeded = ?,
                     items_failed = ?, actions_json = ?, rolled_back = ?, error = ?
                 WHERE execution_id = ?"""
        params = (
            result.get('completed_at'), result['status'],
            result['items_succeeded'], result['items_failed'],
            json.dumps(result.get('actions', []), ensure_ascii=False),
            1 if result.get('rolled_back') else 0,
            result.get('error'), result['execution_id'],
        )
        try:
            if self.dual_db:
                self.dual_db.execute_write(sql, params)
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.execute(sql, params)
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"更新执行记录失败: {e}")

    def _write_audit_log(self, execution_id: str, action: str, details: Dict):
        """写审计日志"""
        sql = "INSERT INTO mt_upgrade_audit_log (execution_id, action, details_json, created_at) VALUES (?, ?, ?, ?)"
        params = (execution_id, action,
                  json.dumps(details, ensure_ascii=False, default=str),
                  datetime.now().isoformat())
        try:
            if self.dual_db:
                self.dual_db.execute_write(sql, params)
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.execute(sql, params)
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"写审计日志失败: {e}")


# ============================================================================
# 升级提案器
# ============================================================================

class UpgradeProposer:
    """升级提案器：从检测结果生成提案（半自动入口）"""

    def __init__(self, dual_db=None, db_path: str = None):
        self.dual_db = dual_db
        self.db_path = db_path
        self.name = "升级提案器"

    def create_proposal(self, items: List[UpgradeItem],
                        summary: str = "") -> UpgradeProposal:
        """从检测到的升级项生成提案"""
        proposal_id = f"PROP_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        proposal = UpgradeProposal(proposal_id, items, summary)

        # 持久化提案
        self._persist_proposal(proposal)

        logger.info(f"升级提案已生成: {proposal_id} (含 {len(items)} 项, 风险={proposal.risk_assessment})")
        return proposal

    def approve_proposal(self, proposal_id: str, approved_by: str) -> Dict[str, Any]:
        """审批提案（半自动：需人工审批后才能执行）"""
        result = {'proposal_id': proposal_id, 'approved': False, 'error': None}
        try:
            sql = """UPDATE mt_upgrade_proposals
                     SET status = ?, approved_at = ?, approved_by = ?
                     WHERE proposal_id = ? AND status = ?"""
            params = (UpgradeStatus.APPROVED.value,
                      datetime.now().isoformat(), approved_by,
                      proposal_id, UpgradeStatus.PROPOSED.value)
            if self.dual_db:
                self.dual_db.execute_write(sql, params)
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.execute(sql, params)
                conn.commit()
                conn.close()
            result['approved'] = True
        except Exception as e:
            result['error'] = str(e)
        return result

    def reject_proposal(self, proposal_id: str, reason: str = "") -> Dict[str, Any]:
        """拒绝提案"""
        result = {'proposal_id': proposal_id, 'rejected': False, 'error': None}
        try:
            sql = "UPDATE mt_upgrade_proposals SET status = ? WHERE proposal_id = ? AND status = ?"
            params = (UpgradeStatus.REJECTED.value, proposal_id, UpgradeStatus.PROPOSED.value)
            if self.dual_db:
                self.dual_db.execute_write(sql, params)
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.execute(sql, params)
                conn.commit()
                conn.close()
            result['rejected'] = True
        except Exception as e:
            result['error'] = str(e)
        return result

    def _persist_proposal(self, proposal: UpgradeProposal):
        """持久化提案"""
        sql = """INSERT INTO mt_upgrade_proposals
                 (proposal_id, summary, status, risk_assessment, item_count,
                  items_json, created_at, approved_at, approved_by, executed_at, execution_id)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        params = (
            proposal.proposal_id, proposal.summary, proposal.status.value,
            proposal.risk_assessment, len(proposal.items),
            json.dumps([item.to_dict() for item in proposal.items], ensure_ascii=False),
            proposal.created_at, proposal.approved_at, proposal.approved_by,
            proposal.executed_at, proposal.execution_id,
        )
        try:
            if self.dual_db:
                self.dual_db.execute_write(sql, params)
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.execute(sql, params)
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"持久化提案失败: {e}")


# ============================================================================
# 自动升级系统主协调器
# ============================================================================

class AutoUpgradeSystem:
    """
    MTSCOS 自动升级系统

    半自动策略：检测 → 生成提案 → 审批 → 执行（含回滚）
    遵循 SSOT：所有升级数据实时写入数据库
    """

    SYSTEM_VERSION = "v1.0.0"

    def __init__(self, project_dir: str = None, db_path: str = None,
                 dual_db=None):
        self.project_dir = project_dir or os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        self.db_path = db_path
        self.dual_db = dual_db

        # 检测器
        self.detectors = {
            UpgradeTarget.SYSTEM_SELF: SystemSelfDetector(self.project_dir),
            UpgradeTarget.DB_SCHEMA: DbSchemaDetector(db_path=db_path, dual_db=dual_db),
            UpgradeTarget.AI_ENGINE_RULES: AiEngineDetector(self.project_dir),
            UpgradeTarget.DEPENDENCIES: DependencyDetector(self.project_dir),
        }

        # 回滚管理器
        backup_dir = os.path.join(
            os.path.dirname(db_path) if db_path else os.path.join(self.project_dir, 'db'),
            'upgrade_snapshots')
        self.rollback_manager = RollbackManager(
            db_path=db_path, dual_db=dual_db, backup_dir=backup_dir)

        # 执行器
        self.executor = UpgradeExecutor(
            project_dir=self.project_dir, db_path=db_path,
            dual_db=dual_db, rollback_manager=self.rollback_manager)

        # 提案器
        self.proposer = UpgradeProposer(dual_db=dual_db, db_path=db_path)

        # 统计
        self.stats = {
            'total_detections': 0,
            'total_items_detected': 0,
            'total_proposals': 0,
            'total_executions': 0,
            'total_completed': 0,
            'total_failed': 0,
            'total_rolled_back': 0,
            'last_detection_time': None,
            'last_execution_time': None,
        }

        # 确保表存在
        self._ensure_tables()

        logger.info(f"AutoUpgradeSystem {self.SYSTEM_VERSION} 已初始化 (半自动模式)")

    # ========================================================================
    # 核心流程：检测 → 提案 → 审批 → 执行
    # ========================================================================

    def detect_all(self) -> List[UpgradeItem]:
        """检测所有升级目标"""
        all_items = []
        for target, detector in self.detectors.items():
            try:
                items = detector.detect()
                all_items.extend(items)
                logger.info(f"检测 {target.value}: 发现 {len(items)} 个升级项")
            except Exception as e:
                logger.error(f"检测 {target.value} 失败: {e}")

        # 持久化检测到的升级项
        for item in all_items:
            self._persist_item(item)

        self.stats['total_detections'] += 1
        self.stats['total_items_detected'] += len(all_items)
        self.stats['last_detection_time'] = datetime.now().isoformat()

        return all_items

    def detect_target(self, target: UpgradeTarget) -> List[UpgradeItem]:
        """检测单个升级目标"""
        detector = self.detectors.get(target)
        if not detector:
            return []
        items = detector.detect()
        for item in items:
            self._persist_item(item)
        self.stats['last_detection_time'] = datetime.now().isoformat()
        return items

    def create_proposal(self, items: List[UpgradeItem] = None,
                        summary: str = "") -> UpgradeProposal:
        """从检测项生成升级提案（半自动入口）"""
        if items is None:
            items = self.detect_all()
        if not items:
            # 无可用升级
            empty = UpgradeProposal(f"PROP_EMPTY_{int(time.time())}", [], "无可用升级")
            empty.status = UpgradeStatus.SKIPPED
            return empty
        # 确保升级项已落库（检测来的已落库，直接传入的也补落库，幂等）
        for item in items:
            self._persist_item(item)
        proposal = self.proposer.create_proposal(items, summary)
        self.stats['total_proposals'] += 1
        return proposal

    def approve_proposal(self, proposal_id: str, approved_by: str) -> Dict[str, Any]:
        """审批提案"""
        return self.proposer.approve_proposal(proposal_id, approved_by)

    def reject_proposal(self, proposal_id: str, reason: str = "") -> Dict[str, Any]:
        """拒绝提案"""
        return self.proposer.reject_proposal(proposal_id, reason)

    def execute_proposal(self, proposal_id: str,
                         approved_by: str = None,
                         force: bool = False) -> Dict[str, Any]:
        """
        执行已审批的升级提案

        Args:
            proposal_id: 提案ID
            approved_by: 审批人
            force: 超级管理员强制执行（跳过审批校验）
        """
        proposal = self._load_proposal(proposal_id)
        if not proposal:
            return {'success': False, 'error': f'提案 {proposal_id} 不存在'}

        # 审批校验（超级管理员 force=True 可跳过）
        if not force and proposal.status != UpgradeStatus.APPROVED.value:
            return {'success': False, 'error': f'提案未审批通过(当前状态: {proposal.status})，请先审批'}

        # 重建UpgradeItem对象
        items = []
        for item_dict in proposal.items_json_parsed if hasattr(proposal, 'items_json_parsed') else []:
            item = UpgradeItem(
                item_id=item_dict['item_id'],
                target=UpgradeTarget(item_dict['target']),
                title=item_dict['title'],
                current_version=item_dict['current_version'],
                target_version=item_dict['target_version'],
                risk=UpgradeRisk(item_dict['risk']),
                strategy=UpgradeStrategy(item_dict['strategy']),
                details=item_dict.get('details', {}),
            )
            item.description = item_dict.get('description', '')
            items.append(item)

        if not items:
            return {'success': False, 'error': '提案无升级项'}

        result = self.executor.execute_proposal(
            UpgradeProposal(proposal_id, items), approved_by=approved_by)

        self.stats['total_executions'] += 1
        self.stats['last_execution_time'] = datetime.now().isoformat()
        if result['status'] == UpgradeStatus.COMPLETED.value:
            self.stats['total_completed'] += 1
        elif result['status'] == UpgradeStatus.ROLLED_BACK.value:
            self.stats['total_rolled_back'] += 1
        else:
            self.stats['total_failed'] += 1

        return result

    def rollback(self, execution_id: str) -> Dict[str, Any]:
        """回滚指定执行"""
        result = self.rollback_manager.rollback(execution_id)
        if result['success']:
            self.stats['total_rolled_back'] += 1
        return result

    # ========================================================================
    # 状态与查询
    # ========================================================================

    def get_status(self) -> Dict[str, Any]:
        """获取升级系统状态"""
        return {
            'system_version': self.SYSTEM_VERSION,
            'mode': 'semi_automatic',
            'targets': [t.value for t in UpgradeTarget],
            'detectors': {t.value: d.name for t, d in self.detectors.items()},
            'stats': self.stats,
            'last_detection_time': self.stats['last_detection_time'],
            'last_execution_time': self.stats['last_execution_time'],
            'timestamp': datetime.now().isoformat(),
        }

    def get_items(self, limit: int = 100, status: str = None) -> List[Dict]:
        """获取升级项列表"""
        sql = "SELECT * FROM mt_upgrade_items"
        params = ()
        if status:
            sql += " WHERE status = ?"
            params = (status,)
        sql += " ORDER BY detected_at DESC LIMIT ?"
        params = params + (limit,)
        try:
            if self.dual_db:
                return self.dual_db.execute_query(sql, params)
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"查询升级项失败: {e}")
            return []

    def get_proposals(self, limit: int = 50) -> List[Dict]:
        """获取提案列表"""
        sql = "SELECT * FROM mt_upgrade_proposals ORDER BY created_at DESC LIMIT ?"
        try:
            if self.dual_db:
                return self.dual_db.execute_query(sql, (limit,))
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute(sql, (limit,)).fetchall()]
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"查询提案失败: {e}")
            return []

    def get_executions(self, limit: int = 50) -> List[Dict]:
        """获取执行历史"""
        sql = "SELECT * FROM mt_upgrade_executions ORDER BY started_at DESC LIMIT ?"
        try:
            if self.dual_db:
                return self.dual_db.execute_query(sql, (limit,))
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute(sql, (limit,)).fetchall()]
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"查询执行历史失败: {e}")
            return []

    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """获取审计日志"""
        sql = "SELECT * FROM mt_upgrade_audit_log ORDER BY created_at DESC LIMIT ?"
        try:
            if self.dual_db:
                return self.dual_db.execute_query(sql, (limit,))
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute(sql, (limit,)).fetchall()]
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"查询审计日志失败: {e}")
            return []

    # ========================================================================
    # SSOT 持久化
    # ========================================================================

    def _ensure_tables(self):
        """创建升级系统数据库表（5张）"""
        tables = [
            """CREATE TABLE IF NOT EXISTS mt_upgrade_items (
                item_id TEXT PRIMARY KEY,
                target TEXT NOT NULL,
                title TEXT NOT NULL,
                current_version TEXT,
                target_version TEXT,
                risk TEXT,
                strategy TEXT,
                details_json TEXT,
                status TEXT,
                detected_at TEXT,
                description TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS mt_upgrade_proposals (
                proposal_id TEXT PRIMARY KEY,
                summary TEXT,
                status TEXT,
                risk_assessment TEXT,
                item_count INTEGER,
                items_json TEXT,
                created_at TEXT,
                approved_at TEXT,
                approved_by TEXT,
                executed_at TEXT,
                execution_id TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS mt_upgrade_executions (
                execution_id TEXT PRIMARY KEY,
                proposal_id TEXT,
                approved_by TEXT,
                started_at TEXT,
                completed_at TEXT,
                status TEXT,
                items_total INTEGER,
                items_succeeded INTEGER,
                items_failed INTEGER,
                snapshot_id TEXT,
                actions_json TEXT,
                rolled_back INTEGER DEFAULT 0,
                error TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS mt_upgrade_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                execution_id TEXT,
                created_at TEXT,
                db_backup_path TEXT,
                code_commit TEXT,
                files_hash_json TEXT,
                items_json TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS mt_upgrade_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT,
                action TEXT,
                target TEXT,
                details_json TEXT,
                created_at TEXT
            )""",
        ]
        for sql in tables:
            try:
                if self.dual_db:
                    self.dual_db.execute_write(sql, ())
                elif self.db_path:
                    conn = sqlite3.connect(self.db_path, timeout=10)
                    conn.execute(sql)
                    conn.commit()
                    conn.close()
            except Exception as e:
                logger.error(f"创建表失败: {e}")

    def _persist_item(self, item: UpgradeItem):
        """持久化升级项"""
        sql = """INSERT OR REPLACE INTO mt_upgrade_items
                 (item_id, target, title, current_version, target_version,
                  risk, strategy, details_json, status, detected_at, description)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        params = (
            item.item_id, item.target.value, item.title,
            item.current_version, item.target_version,
            item.risk.value, item.strategy.value,
            json.dumps(item.details, ensure_ascii=False),
            item.status.value, item.detected_at, item.description,
        )
        try:
            if self.dual_db:
                self.dual_db.execute_write(sql, params)
            elif self.db_path:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.execute(sql, params)
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"持久化升级项失败: {e}")

    def _load_proposal(self, proposal_id: str) -> Optional[Any]:
        """从数据库加载提案"""
        sql = "SELECT * FROM mt_upgrade_proposals WHERE proposal_id = ?"
        try:
            if self.dual_db:
                rows = self.dual_db.execute_query(sql, (proposal_id,))
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.row_factory = sqlite3.Row
                rows = [dict(r) for r in conn.execute(sql, (proposal_id,)).fetchall()]
                conn.close()
            if rows:
                r = rows[0]
                # 创建一个简单的命名对象
                class _P:
                    pass
                p = _P()
                p.proposal_id = r['proposal_id']
                p.status = r['status']
                p.items_json_parsed = json.loads(r.get('items_json') or '[]')
                return p
        except Exception as e:
            logger.error(f"加载提案失败: {e}")
        return None
