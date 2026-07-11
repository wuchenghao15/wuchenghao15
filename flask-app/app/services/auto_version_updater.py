# -*- coding: utf-8 -*-
"""
版本自动更新服务 - 自动版本升级、Git提交、GitHub同步
支持：版本号自动升级、Changelog自动更新、Git自动提交、GitHub同步推送
"""
import os
import json
import logging
import threading
import subprocess
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class AutoVersionUpdater:
    """版本自动更新服务"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._lock = threading.Lock()
        self._repo_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._version_file = os.path.join(self._repo_path, 'app', 'version.py')
        self._default_branch = 'main'
        
        self._initialized = True
        logger.info("[版本更新服务] 版本自动更新服务初始化完成")
    
    def update_version(self, level: str = 'patch', changes: List[str] = None, title: str = '') -> Dict:
        """
        执行完整的版本更新流程
        
        Args:
            level: 升级级别 'major', 'minor', 'patch'
            changes: 更新内容列表
            title: 版本标题
            
        Returns:
            更新结果字典
        """
        with self._lock:
            start_time = datetime.now()
            
            result = {
                'success': False,
                'current_version': '',
                'new_version': '',
                'steps': [],
                'git_commit': '',
                'git_push': '',
                'error': ''
            }
            
            try:
                from app.version import VERSION, CHANGELOG, VERSION_INFO
                from app.services.version_manager import version_manager
                
                result['current_version'] = VERSION
                
                new_version = version_manager.upgrade_version(level=level, description=title)
                result['new_version'] = new_version
                result['steps'].append(f"版本号升级: {VERSION} -> {new_version}")
                
                version_parts = version_manager.parse_version(new_version)
                
                self._update_version_file(
                    new_version,
                    version_parts['major'],
                    version_parts['minor'],
                    version_parts['patch']
                )
                result['steps'].append("版本文件更新完成")
                
                if changes:
                    self._update_changelog(new_version, title or f'自动更新版本 {new_version}', changes)
                    result['steps'].append("Changelog更新完成")
                
                git_result = self._git_commit_and_push(new_version, title, changes)
                result['git_commit'] = git_result.get('commit_hash', '')
                result['git_push'] = git_result.get('push_result', '')
                
                if git_result.get('success'):
                    result['steps'].append("Git提交和推送完成")
                else:
                    result['steps'].append(f"Git推送失败: {git_result.get('error', '')}")
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                result['success'] = True
                result['duration'] = duration
                logger.info(f"[版本更新服务] 版本更新完成: {VERSION} -> {new_version}, 耗时: {duration:.2f}s")
                
            except Exception as e:
                result['error'] = str(e)
                result['steps'].append(f"更新失败: {str(e)}")
                logger.error(f"[版本更新服务] 版本更新失败: {e}")
            
            return result
    
    def _update_version_file(self, version: str, major: int, minor: int, patch: int):
        """更新version.py文件"""
        if not os.path.exists(self._version_file):
            raise FileNotFoundError(f"版本文件不存在: {self._version_file}")
        
        with open(self._version_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        build_number = datetime.now().strftime('%Y%m%d')
        
        content = re.sub(
            r'VERSION = "[^"]+"',
            f'VERSION = "{version}"',
            content
        )
        
        content = re.sub(
            r'BUILD_NUMBER = "[^"]+"',
            f'BUILD_NUMBER = "{build_number}"',
            content
        )
        
        content = re.sub(
            r'RELEASE_DATE = "[^"]+"',
            f'RELEASE_DATE = "{today}"',
            content
        )
        
        content = re.sub(
            r"'version': '[^']+'",
            f"'version': '{version}'",
            content
        )
        
        with open(self._version_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"[版本更新服务] 版本文件已更新: {version}")
    
    def _update_changelog(self, version: str, title: str, changes: List[str]):
        """更新CHANGELOG"""
        if not os.path.exists(self._version_file):
            raise FileNotFoundError(f"版本文件不存在: {self._version_file}")
        
        with open(self._version_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        new_entry = {
            'version': version,
            'date': today,
            'title': title,
            'changes': changes,
            'security_fixes': [],
            'breaking_changes': [],
            'contributors': ['Auto Version Updater'],
            'highlights': changes[:3] if len(changes) > 0 else []
        }
        
        new_entry_str = json.dumps(new_entry, ensure_ascii=False, indent=4)
        new_entry_str = new_entry_str.replace('"', "'")
        
        changelog_pattern = r'(CHANGELOG = \[)'
        insert_after_match = re.search(changelog_pattern, content)
        
        if insert_after_match:
            insert_pos = insert_after_match.end()
            new_content = content[:insert_pos] + '\n    ' + new_entry_str + ',\n' + content[insert_pos:]
            
            with open(self._version_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"[版本更新服务] Changelog已更新: {version}")
    
    def _git_commit_and_push(self, version: str, title: str, changes: List[str]) -> Dict:
        """执行Git提交和推送"""
        result = {
            'success': False,
            'commit_hash': '',
            'push_result': '',
            'error': ''
        }
        
        try:
            commit_msg = f"chore: version {version} - {title}"
            if changes:
                commit_msg += f"\n\nChanges:\n" + '\n'.join(f"- {c}" for c in changes[:10])
            
            self._run_git_command(['add', '.'])
            result['push_result'] += "文件已暂存\n"
            
            self._run_git_command(['commit', '-m', commit_msg])
            result['push_result'] += f"已提交: {commit_msg[:50]}...\n"
            
            try:
                self._run_git_command(['push', 'origin', self._default_branch])
                result['push_result'] += "已推送到远程仓库\n"
            except Exception as push_error:
                result['push_result'] += f"推送失败(可能需要手动处理): {str(push_error)}\n"
            
            commit_hash = self._run_git_command(['rev-parse', 'HEAD'])
            result['commit_hash'] = commit_hash.strip()
            
            result['success'] = True
            logger.info(f"[版本更新服务] Git提交完成: {result['commit_hash']}")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"[版本更新服务] Git操作失败: {e}")
        
        return result
    
    def _run_git_command(self, args: List[str]) -> str:
        """执行Git命令"""
        result = subprocess.run(
            ['git'] + args,
            cwd=self._repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            error_msg = f"Git命令失败: {' '.join(args)}\nstderr: {result.stderr}"
            raise Exception(error_msg)
        
        return result.stdout
    
    def check_git_status(self) -> Dict:
        """检查Git状态"""
        try:
            status = self._run_git_command(['status', '--short'])
            branch = self._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
            remote = self._run_git_command(['remote', '-v'])
            
            return {
                'success': True,
                'branch': branch.strip(),
                'status': status.strip(),
                'remote': remote.strip()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def pull_latest(self) -> Dict:
        """拉取最新代码"""
        try:
            result = self._run_git_command(['pull', 'origin', self._default_branch])
            return {
                'success': True,
                'result': result.strip()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_version_info(self) -> Dict:
        """获取当前版本信息"""
        try:
            from app.version import VERSION, VERSION_INFO, CHANGELOG
            
            return {
                'success': True,
                'version': VERSION,
                'version_info': VERSION_INFO,
                'latest_changelog': CHANGELOG[0] if CHANGELOG else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def auto_update(self, trigger: str = 'auto') -> Dict:
        """
        自动检测并更新版本
        
        Args:
            trigger: 触发原因 'auto', 'manual', 'cron', 'webhook'
            
        Returns:
            更新结果
        """
        logger.info(f"[版本更新服务] 自动更新触发: {trigger}")
        
        git_status = self.check_git_status()
        if not git_status['success']:
            return {
                'success': False,
                'error': f"Git状态检查失败: {git_status['error']}"
            }
        
        if git_status['status']:
            changes = [line.strip() for line in git_status['status'].split('\n') if line.strip()]
            if len(changes) > 0:
                level = 'minor' if len(changes) > 5 else 'patch'
                title = f'自动更新 {trigger}'
                
                return self.update_version(level=level, changes=changes, title=title)
        
        return {
            'success': False,
            'message': '没有需要提交的变更'
        }


def get_auto_version_updater() -> AutoVersionUpdater:
    """获取版本自动更新服务单例"""
    return AutoVersionUpdater()


def init_auto_version_updater():
    """初始化版本自动更新服务"""
    updater = get_auto_version_updater()
    logger.info("[版本更新服务] 版本自动更新服务初始化完成")
    return updater