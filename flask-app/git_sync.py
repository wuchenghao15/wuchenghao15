#!/usr/bin/env python3
import os
import subprocess
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class GitSyncManager:
    def __init__(self, repo_path=None):
        self.repo_path = repo_path or os.path.dirname(os.path.abspath(__file__))
        self.git_executable = self._find_git()
    
    def _find_git(self):
        for path in ['git', '/usr/bin/git', '/usr/local/bin/git']:
            try:
                subprocess.run([path, '--version'], capture_output=True, check=True)
                return path
            except:
                continue
        return 'git'
    
    def _run_command(self, cmd, capture_output=True):
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=capture_output,
                text=True,
                timeout=30
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.strip() if result.stdout else '',
                'stderr': result.stderr.strip() if result.stderr else '',
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'stdout': '', 'stderr': '命令执行超时', 'returncode': -1}
        except Exception as e:
            return {'success': False, 'stdout': '', 'stderr': str(e), 'returncode': -2}
    
    def get_status(self):
        result = self._run_command([self.git_executable, 'status'])
        if not result['success']:
            return {'success': False, 'message': '获取状态失败', 'error': result['stderr']}
        
        branch_result = self._run_command([self.git_executable, 'branch', '--show-current'])
        branch = branch_result['stdout'] if branch_result['success'] else 'unknown'
        
        remote_result = self._run_command([self.git_executable, 'remote', '-v'])
        remotes = []
        if remote_result['success']:
            for line in remote_result['stdout'].split('\n'):
                parts = line.split()
                if len(parts) >= 2:
                    remotes.append({'name': parts[0], 'url': parts[1]})
        
        status_output = result['stdout']
        has_changes = 'modified:' in status_output or 'Untracked:' in status_output
        
        return {
            'success': True,
            'branch': branch,
            'remotes': remotes,
            'has_changes': has_changes,
            'status_output': status_output
        }
    
    def get_log(self, limit=10):
        result = self._run_command([self.git_executable, 'log', '--oneline', f'-{limit}'])
        if not result['success']:
            return {'success': False, 'message': '获取日志失败', 'error': result['stderr']}
        
        commits = []
        for line in result['stdout'].split('\n'):
            if line.strip():
                parts = line.split(' ', 1)
                if len(parts) >= 2:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1]
                    })
        
        return {'success': True, 'commits': commits}
    
    def add_all(self):
        return self._run_command([self.git_executable, 'add', '.'])
    
    def commit(self, message=None):
        if not message:
            message = f"Auto commit: {datetime.now().isoformat()}"
        return self._run_command([self.git_executable, 'commit', '-m', message])
    
    def pull(self, remote='origin', branch='main'):
        result = self._run_command([self.git_executable, 'pull', remote, branch])
        if not result['success'] and 'Already up to date' in result['stderr']:
            return {'success': True, 'stdout': 'Already up to date', 'stderr': '', 'returncode': 0}
        return result
    
    def push(self, remote='origin', branch='main'):
        return self._run_command([self.git_executable, 'push', remote, branch])
    
    def sync(self, commit_message=None):
        status = self.get_status()
        if not status['success']:
            return status
        
        if not status['has_changes']:
            return {'success': True, 'message': '没有需要同步的更改'}
        
        add_result = self.add_all()
        if not add_result['success']:
            return {'success': False, 'message': '添加文件失败', 'error': add_result['stderr']}
        
        commit_result = self.commit(commit_message)
        if not commit_result['success']:
            return {'success': False, 'message': '提交失败', 'error': commit_result['stderr']}
        
        push_result = self.push()
        if not push_result['success']:
            return {'success': False, 'message': '推送失败', 'error': push_result['stderr']}
        
        return {
            'success': True,
            'message': '同步成功',
            'commit_message': commit_message or 'Auto commit',
            'branch': status['branch']
        }
    
    def auto_sync(self):
        try:
            status = self.get_status()
            if not status['success']:
                logger.error(f"Git同步失败: {status.get('error', '')}")
                return status
            
            if not status['has_changes']:
                logger.info("Git: 没有需要同步的更改")
                return {'success': True, 'message': '没有需要同步的更改'}
            
            commit_message = f"Auto sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - MTSCOS AI System"
            
            add_result = self.add_all()
            if not add_result['success']:
                logger.error(f"Git添加文件失败: {add_result['stderr']}")
                return add_result
            
            commit_result = self.commit(commit_message)
            if not commit_result['success']:
                logger.error(f"Git提交失败: {commit_result['stderr']}")
                return commit_result
            
            push_result = self.push()
            if not push_result['success']:
                logger.error(f"Git推送失败: {push_result['stderr']}")
                return push_result
            
            logger.info(f"Git同步成功: {commit_message}")
            return {
                'success': True,
                'message': '自动同步成功',
                'commit_message': commit_message,
                'branch': status['branch']
            }
        except Exception as e:
            logger.error(f"Git自动同步异常: {str(e)}")
            return {'success': False, 'message': f'同步异常: {str(e)}'}

git_sync_manager = GitSyncManager()