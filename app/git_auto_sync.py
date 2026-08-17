#!/usr/bin/env python3
"""
Git自动同步服务 - 基于核心文件变更触发
不再按固定时间间隔同步，而是检测核心文件/版本信息变化后自动同步
"""

import os
import subprocess
import logging
import time
import json
import hashlib
import sqlite3
from datetime import datetime
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

# 核心文件列表：这些文件的变更触发同步
CORE_FILES = [
    'app.py',
    'version_manager.py',
    'auto_scheduler.py',
    'auth_manager.py',
    'app/middlewares/security_middleware.py',
    'app/middlewares/auth_middleware.py',
    'app/utils/db.py',
    'app/system_rules_extension.py',
    'ai_engines/ai_engine.py',
    'ai_engines/ai_self_learning_engine.py',
    'ai_engines/auto_scheduler.py',
    'templates/student_base.html',
]

# 核心目录：检测目录下任何.py文件变更
CORE_DIRS = [
    'app/',
    'ai_engines/',
    'templates/',
]

# 数据库中的版本规则码
VERSION_RULE_CODES = ['SYS_VERSION', 'SYSTEM_VERSION', 'APP_VERSION']

# 同步状态文件
SYNC_STATE_FILE = '.git_sync_state.json'


class GitAutoSync:
    """基于文件变更的Git自动同步服务"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.repo_path = self.config.get('repo_path', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.sync_branch = self.config.get('sync_branch', 'main')
        self.sync_remote = self.config.get('sync_remote', 'mtscos_origin')
        self.auto_commit = self.config.get('auto_commit', True)
        self.commit_message = self.config.get('commit_message', 'Auto sync: {timestamp}')
        self.auto_push = self.config.get('auto_push', True)
        self.retry_count = self.config.get('retry_count', 3)
        self.retry_delay = self.config.get('retry_delay', 30)
        self._running = False
        self._last_file_hashes = {}
        self._last_db_version = None
        self._load_sync_state()

    # ==================== 状态持久化 ====================

    def _load_sync_state(self):
        """加载上次同步状态"""
        state_path = os.path.join(self.repo_path, SYNC_STATE_FILE)
        try:
            if os.path.exists(state_path):
                with open(state_path, 'r') as f:
                    state = json.load(f)
                    self._last_file_hashes = state.get('file_hashes', {})
                    self._last_db_version = state.get('db_version')
                    logger.info(f"[Git同步] 加载同步状态: {len(self._last_file_hashes)}个文件, DB版本={self._last_db_version}")
        except Exception as e:
            logger.warning(f"[Git同步] 加载同步状态失败: {e}")

    def _save_sync_state(self):
        """保存同步状态"""
        state_path = os.path.join(self.repo_path, SYNC_STATE_FILE)
        try:
            state = {
                'file_hashes': self._last_file_hashes,
                'db_version': self._last_db_version,
                'last_sync': datetime.now().isoformat()
            }
            with open(state_path, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"[Git同步] 保存同步状态失败: {e}")

    # ==================== 变更检测 ====================

    def _compute_file_hash(self, filepath: str) -> Optional[str]:
        """计算文件内容的MD5哈希"""
        try:
            full_path = os.path.join(self.repo_path, filepath)
            if not os.path.exists(full_path):
                return None
            with open(full_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None

    def _get_core_files(self) -> List[str]:
        """获取需要监控的核心文件列表"""
        files = list(CORE_FILES)

        # 扫描核心目录下的.py文件
        for core_dir in CORE_DIRS:
            dir_path = os.path.join(self.repo_path, core_dir)
            if os.path.isdir(dir_path):
                for root, dirs, filenames in os.walk(dir_path):
                    # 排除__pycache__
                    dirs[:] = [d for d in dirs if d != '__pycache__']
                    for filename in filenames:
                        if filename.endswith('.py'):
                            rel_path = os.path.relpath(os.path.join(root, filename), self.repo_path)
                            files.append(rel_path.replace('\\', '/'))

        return list(set(files))

    def _get_db_version(self) -> Optional[str]:
        """从数据库获取当前系统版本"""
        db_path = os.path.join(self.repo_path, 'app.db')
        if not os.path.exists(db_path):
            return None

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            for rule_code in VERSION_RULE_CODES:
                try:
                    cursor.execute(
                        "SELECT rule_value FROM system_rules WHERE rule_code = ? AND is_active = 1",
                        (rule_code,)
                    )
                    result = cursor.fetchone()
                    if result:
                        conn.close()
                        return result[0]
                except Exception:
                    continue
            conn.close()
        except Exception as e:
            logger.warning(f"[Git同步] 读取数据库版本失败: {e}")

        return None

    def _get_git_status(self) -> str:
        """获取Git状态"""
        return self._run_git_command('git status --porcelain')

    def detect_changes(self) -> Dict:
        """
        检测是否有核心文件或版本信息变更
        返回: {'has_changes': bool, 'changed_files': [], 'version_changed': bool, 'reason': str}
        """
        result = {
            'has_changes': False,
            'changed_files': [],
            'version_changed': False,
            'reason': ''
        }

        # 1. 检测核心文件哈希变化
        core_files = self._get_core_files()
        changed_files = []

        for filepath in core_files:
            current_hash = self._compute_file_hash(filepath)
            if current_hash is None:
                continue

            last_hash = self._last_file_hashes.get(filepath)
            if last_hash is not None and current_hash != last_hash:
                changed_files.append(filepath)
            # 更新哈希
            if current_hash:
                self._last_file_hashes[filepath] = current_hash

        if changed_files:
            result['changed_files'] = changed_files
            result['has_changes'] = True
            result['reason'] = f'核心文件变更: {", ".join(changed_files[:5])}'
            logger.info(f"[Git同步] 检测到核心文件变更: {changed_files}")

        # 2. 检测数据库版本变化
        current_db_version = self._get_db_version()
        if current_db_version and self._last_db_version and current_db_version != self._last_db_version:
            result['version_changed'] = True
            result['has_changes'] = True
            result['reason'] += f' | 版本变更: {self._last_db_version} -> {current_db_version}'
            logger.info(f"[Git同步] 检测到版本变更: {self._last_db_version} -> {current_db_version}")

        # 更新版本记录
        if current_db_version:
            self._last_db_version = current_db_version

        # 3. 检测git工作区是否有未提交的变更
        git_status = self._get_git_status()
        if git_status.strip():
            # 有未提交的变更，也触发同步
            uncommitted = [l.strip() for l in git_status.strip().split('\n') if l.strip()]
            # 过滤掉同步状态文件本身
            uncommitted = [f for f in uncommitted if SYNC_STATE_FILE not in f]
            if uncommitted:
                result['has_changes'] = True
                result['reason'] += f' | Git工作区有{len(uncommitted)}个变更'
                if not changed_files:
                    result['changed_files'] = uncommitted[:10]

        return result

    # ==================== Git操作 ====================

    def _run_git_command(self, command: str, cwd: Optional[str] = None) -> str:
        """执行Git命令"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                logger.error(f"Git命令执行失败: {command}")
                logger.error(f"错误信息: {result.stderr}")
                return ""
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"Git命令超时: {command}")
            return ""
        except Exception as e:
            logger.error(f"Git命令执行异常: {command}, 错误: {e}")
            return ""

    def _get_current_branch(self) -> str:
        return self._run_git_command('git branch --show-current')

    def _checkout_branch(self, branch: str) -> bool:
        result = self._run_git_command(f'git checkout {branch}')
        return result != ""

    def _add_all(self) -> bool:
        self._run_git_command('git add .')
        return True

    def _commit(self, message: str) -> bool:
        result = self._run_git_command(f'git commit -m "{message}"')
        return result != "" or "nothing to commit" in result

    def _push(self) -> bool:
        result = self._run_git_command(f'git push {self.sync_remote} {self.sync_branch}')
        return result != "" or "Everything up-to-date" in result

    # ==================== 同步执行 ====================

    def _sync(self, reason: str = '') -> bool:
        """执行同步操作"""
        logger.info(f"[Git同步] 开始同步, 原因: {reason}")

        current_branch = self._get_current_branch()
        if current_branch != self.sync_branch:
            logger.info(f"[Git同步] 切换到分支: {self.sync_branch}")
            if not self._checkout_branch(self.sync_branch):
                logger.error(f"[Git同步] 切换分支失败: {self.sync_branch}")
                return False

        status = self._get_git_status()
        if status:
            # 过滤掉同步状态文件
            lines = [l for l in status.split('\n') if l.strip() and SYNC_STATE_FILE not in l]
            if lines:
                logger.info(f"[Git同步] 检测到变更:\n{chr(10).join(lines)}")

                if self.auto_commit:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    message = self.commit_message.format(timestamp=timestamp)
                    if reason:
                        message += f' | {reason}'

                    self._add_all()
                    if not self._commit(message):
                        logger.warning("[Git同步] 提交可能无变更")

        if self.auto_push:
            logger.info("[Git同步] 推送到远程...")
            if not self._push():
                logger.error("[Git同步] 推送失败")
                return False

        # 保存同步状态
        self._save_sync_state()
        logger.info("[Git同步] 同步完成")
        return True

    def sync_if_changed(self) -> Dict:
        """
        检测变更并同步（主入口）
        返回同步结果信息
        """
        change_info = self.detect_changes()

        if not change_info['has_changes']:
            logger.debug("[Git同步] 无核心文件或版本变更，跳过同步")
            return {
                'synced': False,
                'reason': 'no_changes',
                'changed_files': [],
                'version_changed': False
            }

        # 有变更，执行同步
        success = False
        for attempt in range(self.retry_count):
            try:
                if self._sync(change_info['reason']):
                    success = True
                    break
            except Exception as e:
                logger.error(f"[Git同步] 尝试 {attempt + 1}/{self.retry_count} 失败: {e}")

            if attempt < self.retry_count - 1:
                logger.info(f"[Git同步] 等待 {self.retry_delay} 秒后重试...")
                time.sleep(self.retry_delay)

        return {
            'synced': success,
            'reason': change_info['reason'],
            'changed_files': change_info['changed_files'],
            'version_changed': change_info['version_changed'],
            'attempts': self.retry_count
        }

    # ==================== 兼容旧接口 ====================

    def sync(self) -> bool:
        """执行同步（兼容旧接口）"""
        result = self.sync_if_changed()
        return result['synced']

    def sync_on_startup(self):
        """启动时同步"""
        logger.info("[Git同步] 启动时检查同步")
        self.sync_if_changed()

    def sync_on_shutdown(self):
        """关闭时同步"""
        logger.info("[Git同步] 关闭时执行同步")
        # 关闭时强制同步，无论是否有变更
        self._sync('shutdown_sync')

    def start(self):
        """启动自动同步服务（轮询模式）"""
        logger.info(f"[Git同步] 启动基于文件变更的自动同步服务")
        self._running = True
        poll_interval = 60  # 每60秒检测一次变更

        while self._running:
            try:
                self.sync_if_changed()
            except Exception as e:
                logger.error(f"[Git同步] 自动同步异常: {e}")

            for _ in range(poll_interval):
                if not self._running:
                    break
                time.sleep(1)

    def stop(self):
        """停止自动同步服务"""
        logger.info("[Git同步] 停止自动同步服务")
        self._running = False


class GitHubSync:
    """GitHub同步服务（兼容接口）"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.git_sync = GitAutoSync(config)

    def sync(self) -> bool:
        """执行GitHub同步"""
        result = self.git_sync.sync_if_changed()
        return result['synced']


git_auto_sync = GitAutoSync()
github_sync = GitHubSync()
