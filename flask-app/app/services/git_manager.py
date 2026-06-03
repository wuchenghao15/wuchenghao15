# -*- coding: utf-8 -*-
"""Git管理器模块,负责整合Git核心功能"""

import os
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitManager:
    """Git管理器,负责整合Git核心功能"""

    def __init__(self, repo_path: str = None):
        """初始化Git管理器
        
        Args:
            repo_path: Git仓库路径,默认为当前工作目录
        """
        self.instance_id = f"git_manager_{id(self)}"
        self.name = "Git管理器"
        self.description = "负责整合Git核心功能"
        self.logger = logger
        self.logger.info(f"初始化Git管理器: {self.instance_id}")

        self.repo_path = repo_path or os.getcwd()

        if not self._is_git_repo():
            self.logger.warning(f"当前目录 {self.repo_path} 不是Git仓库")
        else:
            self.logger.info(f"当前目录 {self.repo_path} 是Git仓库")
    
    def initialize(self):
        """初始化Git管理器(空方法,保持接口一致性)"""
        self.logger.info(f"Git管理器已初始化: {self.instance_id}")

    def _is_git_repo(self) -> bool:
        """检查当前目录是否是Git仓库
        
        Returns:
            bool: 是否是Git仓库
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--is-inside-work-tree'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"检查Git仓库失败: {str(e)}")
            return False

    def _run_git_command(self, command: List[str]) -> Dict[str, Any]:
        """运行Git命令
        
        Args:
            command: Git命令列表(不包含'git'前缀)
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        try:
            result = subprocess.run(
                ['git'] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
        except Exception as e:
            self.logger.error(f"运行Git命令失败: {str(e)}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": 1
            }

    def init_repo(self, bare: bool = False) -> Dict[str, Any]:
        """初始化Git仓库
        
        Args:
            bare: 是否创建裸仓库
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        self.logger.info(f"初始化Git仓库: {self.repo_path}")
        command = ['init']
        if bare:
            command.append('--bare')
        return self._run_git_command(command)

    def clone_repo(self, url: str, target_dir: str = None, branch: str = None) -> Dict[str, Any]:
        """克隆Git仓库
        
        Args:
            url: 仓库URL
            target_dir: 目标目录
            branch: 指定分支
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        command = ['clone']
        if branch:
            command.extend(['-b', branch])
        command.append(url)
        if target_dir:
            command.append(target_dir)
        
        self.logger.info(f"克隆Git仓库: {url} -> {target_dir or os.path.basename(url)}")
        return self._run_git_command(command)

    def add(self, paths: List[str] = None) -> Dict[str, Any]:
        """添加文件到暂存区
        
        Args:
            paths: 文件路径列表,None表示添加所有文件
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        command = ['add']
        if paths:
            command.extend(paths)
        else:
            command.append('.')
        
        self.logger.info(f"添加文件到暂存区: {paths or 'all files'}")
        return self._run_git_command(command)

    def commit(self, message: str, amend: bool = False, author: str = None) -> Dict[str, Any]:
        """提交更改
        
        Args:
            message: 提交消息
            amend: 是否修改上一次提交
            author: 指定作者(格式: "name <email>")
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        command = ['commit', '-m', message]
        if amend:
            command.append('--amend')
        if author:
            command.extend(['--author', author])
        
        self.logger.info(f"提交更改: {message}")
        return self._run_git_command(command)

    def push(self, remote: str = 'origin', branch: str = 'main', force: bool = False) -> Dict[str, Any]:
        """推送更改
        
        Args:
            remote: 远程仓库名称
            branch: 分支名称
            force: 是否强制推送
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        command = ['push', remote, branch]
        if force:
            command.append('--force')
        
        self.logger.info(f"推送更改: {remote}/{branch}")
        return self._run_git_command(command)

    def pull(self, remote: str = 'origin', branch: str = 'main', rebase: bool = False) -> Dict[str, Any]:
        """拉取更改
        
        Args:
            remote: 远程仓库名称
            branch: 分支名称
            rebase: 是否使用rebase模式
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        command = ['pull', remote, branch]
        if rebase:
            command.append('--rebase')
        
        self.logger.info(f"拉取更改: {remote}/{branch}")
        return self._run_git_command(command)

    def status(self) -> Dict[str, Any]:
        """查看仓库状态
        
        Returns:
            Dict[str, Any]: 仓库状态信息
        """
        self.logger.info("查看仓库状态")
        result = self._run_git_command(['status', '--porcelain'])
        
        if result['success']:
            lines = result['stdout'].split('\n') if result['stdout'] else []
            status_info = {
                'staged': [],
                'modified': [],
                'untracked': [],
                'deleted': []
            }
            
            for line in lines:
                if line:
                    status = line[:2]
                    filename = line[3:]
                    if status.startswith('A'):
                        status_info['staged'].append(filename)
                    elif status.startswith('M'):
                        status_info['modified'].append(filename)
                    elif status == '??':
                        status_info['untracked'].append(filename)
                    elif status.startswith('D'):
                        status_info['deleted'].append(filename)
            
            return {**result, 'parsed_status': status_info}
        
        return result

    def log(self, limit: int = 10, full: bool = False) -> Dict[str, Any]:
        """查看提交日志
        
        Args:
            limit: 日志条数限制
            full: 是否显示完整格式
            
        Returns:
            Dict[str, Any]: 提交日志信息
        """
        self.logger.info(f"查看提交日志,限制 {limit} 条")
        
        if full:
            result = self._run_git_command(['log', '-n', str(limit)])
        else:
            result = self._run_git_command(['log', '-n', str(limit), '--oneline'])
            
            if result['success']:
                commits = []
                for line in result['stdout'].split('\n'):
                    if line:
                        parts = line.split(' ', 1)
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1] if len(parts) > 1 else ''
                        })
                return {**result, 'commits': commits}
        
        return result

    def branch(self, all: bool = False) -> Dict[str, Any]:
        """查看分支
        
        Args:
            all: 是否显示所有分支(包括远程)
            
        Returns:
            Dict[str, Any]: 分支列表
        """
        self.logger.info("查看分支")
        command = ['branch']
        if all:
            command.append('-a')
        
        result = self._run_git_command(command)
        
        if result['success']:
            branches = []
            current_branch = None
            for line in result['stdout'].split('\n'):
                if line:
                    if line.startswith('*'):
                        current_branch = line[2:].strip()
                        branches.append({'name': current_branch, 'current': True})
                    else:
                        branches.append({'name': line.strip(), 'current': False})
            
            return {**result, 'branches': branches, 'current_branch': current_branch}
        
        return result

    def checkout(self, branch: str, create: bool = False) -> Dict[str, Any]:
        """切换分支
        
        Args:
            branch: 分支名称
            create: 是否创建新分支
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        self.logger.info(f"切换分支: {branch}")
        
        if create:
            return self._run_git_command(['checkout', '-b', branch])
        return self._run_git_command(['checkout', branch])

    def create_branch(self, branch: str, base: str = 'HEAD') -> Dict[str, Any]:
        """创建分支
        
        Args:
            branch: 新分支名称
            base: 基于哪个提交创建
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        self.logger.info(f"创建分支: {branch}")
        return self._run_git_command(['checkout', '-b', branch, base])

    def delete_branch(self, branch: str, force: bool = False) -> Dict[str, Any]:
        """删除分支
        
        Args:
            branch: 要删除的分支名称
            force: 是否强制删除
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        self.logger.info(f"删除分支: {branch}")
        command = ['branch']
        if force:
            command.append('-D')
        else:
            command.append('-d')
        command.append(branch)
        return self._run_git_command(command)

    def merge(self, branch: str, no_ff: bool = False) -> Dict[str, Any]:
        """合并分支
        
        Args:
            branch: 要合并的分支名称
            no_ff: 是否禁用快进合并
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        self.logger.info(f"合并分支: {branch}")
        command = ['merge']
        if no_ff:
            command.append('--no-ff')
        command.append(branch)
        return self._run_git_command(command)

    def remote(self, verbose: bool = False) -> Dict[str, Any]:
        """查看远程仓库
        
        Args:
            verbose: 是否显示详细信息
            
        Returns:
            Dict[str, Any]: 远程仓库列表
        """
        self.logger.info("查看远程仓库")
        command = ['remote']
        if verbose:
            command.append('-v')
        
        result = self._run_git_command(command)
        
        if result['success'] and verbose:
            remotes = {}
            for line in result['stdout'].split('\n'):
                if line:
                    parts = line.split('\t')
                    name = parts[0]
                    url_info = parts[1].split(' ')
                    url = url_info[0]
                    direction = url_info[1].strip('()') if len(url_info) > 1 else 'push'
                    
                    if name not in remotes:
                        remotes[name] = {'url': url, 'fetch': None, 'push': None}
                    remotes[name][direction] = url
            
            return {**result, 'remotes': remotes}
        
        return result

    def add_remote(self, name: str, url: str) -> Dict[str, Any]:
        """添加远程仓库
        
        Args:
            name: 远程仓库名称
            url: 远程仓库URL
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        self.logger.info(f"添加远程仓库: {name} -> {url}")
        return self._run_git_command(['remote', 'add', name, url])

    def remove_remote(self, name: str) -> Dict[str, Any]:
        """移除远程仓库
        
        Args:
            name: 远程仓库名称
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        self.logger.info(f"移除远程仓库: {name}")
        return self._run_git_command(['remote', 'remove', name])

    def set_remote_url(self, name: str, url: str) -> Dict[str, Any]:
        """设置远程仓库URL
        
        Args:
            name: 远程仓库名称
            url: 新的URL
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        self.logger.info(f"设置远程仓库URL: {name} -> {url}")
        return self._run_git_command(['remote', 'set-url', name, url])

    def diff(self, path: str = None, cached: bool = False) -> Dict[str, Any]:
        """查看文件差异
        
        Args:
            path: 文件路径,None表示所有文件
            cached: 是否查看暂存区差异
            
        Returns:
            Dict[str, Any]: 差异信息
        """
        command = ['diff']
        if cached:
            command.append('--cached')
        if path:
            command.append(path)
        
        self.logger.info(f"查看文件差异: {path or 'all files'}")
        return self._run_git_command(command)

    def reset(self, mode: str = 'mixed', commit: str = 'HEAD') -> Dict[str, Any]:
        """重置提交
        
        Args:
            mode: 重置模式 (soft, mixed, hard)
            commit: 提交hash或引用
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        self.logger.info(f"重置提交: {mode} {commit}")
        return self._run_git_command(['reset', f'--{mode}', commit])

    def tag(self, name: str, message: str = None, commit: str = 'HEAD') -> Dict[str, Any]:
        """创建标签
        
        Args:
            name: 标签名称
            message: 标签消息(用于附注标签)
            commit: 关联的提交
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        command = ['tag', name, commit]
        if message:
            command.extend(['-m', message])
        
        self.logger.info(f"创建标签: {name}")
        return self._run_git_command(command)

    def list_tags(self) -> Dict[str, Any]:
        """列出所有标签
        
        Returns:
            Dict[str, Any]: 标签列表
        """
        self.logger.info("列出所有标签")
        result = self._run_git_command(['tag', '-l'])
        
        if result['success']:
            tags = result['stdout'].split('\n') if result['stdout'] else []
            return {**result, 'tags': tags}
        
        return result

    def delete_tag(self, name: str) -> Dict[str, Any]:
        """删除标签
        
        Args:
            name: 标签名称
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        self.logger.info(f"删除标签: {name}")
        return self._run_git_command(['tag', '-d', name])

    def fetch(self, remote: str = 'origin', prune: bool = False) -> Dict[str, Any]:
        """获取远程更改
        
        Args:
            remote: 远程仓库名称
            prune: 是否删除已不存在的远程分支引用
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        command = ['fetch', remote]
        if prune:
            command.append('--prune')
        
        self.logger.info(f"获取远程更改: {remote}")
        return self._run_git_command(command)

    def stash(self, message: str = None) -> Dict[str, Any]:
        """暂存更改
        
        Args:
            message: 暂存消息
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        command = ['stash']
        if message:
            command.extend(['push', '-m', message])
        else:
            command.append('push')
        
        self.logger.info(f"暂存更改: {message or 'no message'}")
        return self._run_git_command(command)

    def stash_pop(self, stash_id: str = None) -> Dict[str, Any]:
        """恢复暂存的更改
        
        Args:
            stash_id: 暂存记录ID(如stash@{0})
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        command = ['stash', 'pop']
        if stash_id:
            command.append(stash_id)
        
        self.logger.info("恢复暂存的更改")
        return self._run_git_command(command)

    def stash_list(self) -> Dict[str, Any]:
        """列出所有暂存记录
        
        Returns:
            Dict[str, Any]: 暂存记录列表
        """
        self.logger.info("列出所有暂存记录")
        result = self._run_git_command(['stash', 'list'])
        
        if result['success']:
            stashes = []
            for line in result['stdout'].split('\n'):
                if line:
                    parts = line.split(':')
                    stashes.append({
                        'id': parts[0].strip(),
                        'branch': parts[1].strip() if len(parts) > 1 else '',
                        'message': parts[2].strip() if len(parts) > 2 else ''
                    })
            return {**result, 'stashes': stashes}
        
        return result

    def stash_drop(self, stash_id: str = None) -> Dict[str, Any]:
        """删除暂存记录
        
        Args:
            stash_id: 暂存记录ID
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        command = ['stash', 'drop']
        if stash_id:
            command.append(stash_id)
        
        self.logger.info(f"删除暂存记录: {stash_id or 'latest'}")
        return self._run_git_command(command)

    def get_repo_info(self) -> Dict[str, Any]:
        """获取仓库信息
        
        Returns:
            Dict[str, Any]: 仓库综合信息
        """
        try:
            info = {
                "is_git_repo": self._is_git_repo(),
                "repo_path": self.repo_path,
                "status": self.status(),
                "branches": self.branch(all=True),
                "remotes": self.remote(verbose=True),
                "last_commits": self.log(5)
            }
            return info
        except Exception as e:
            self.logger.error(f"获取仓库信息失败: {str(e)}")
            return {
                "repo_path": self.repo_path,
                "is_git_repo": False,
                "error": str(e)
            }

    def get_system_version(self) -> Dict[str, Any]:
        """获取系统版本信息
        
        Returns:
            Dict[str, Any]: 版本信息
        """
        try:
            branch_result = self._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
            branch = branch_result['stdout'].strip() if branch_result['success'] else 'unknown'

            commit_result = self._run_git_command(['rev-parse', 'HEAD'])
            commit_hash = commit_result['stdout'].strip() if commit_result['success'] else 'unknown'

            commit_time_result = self._run_git_command(['log', '-1', '--format=%ci', 'HEAD'])
            commit_time = commit_time_result['stdout'].strip() if commit_time_result['success'] else 'unknown'

            author_result = self._run_git_command(['log', '-1', '--format=%an <%ae>', 'HEAD'])
            author = author_result['stdout'].strip() if author_result['success'] else 'unknown'

            message_result = self._run_git_command(['log', '-1', '--format=%s', 'HEAD'])
            message = message_result['stdout'].strip() if message_result['success'] else 'unknown'

            version_info = {
                "branch": branch,
                "commit_hash": commit_hash,
                "commit_time": commit_time,
                "author": author,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "repo_path": self.repo_path
            }

            self.logger.info(f"获取系统版本信息: {version_info}")
            return version_info
        except Exception as e:
            self.logger.error(f"获取系统版本信息失败: {str(e)}")
            return {
                "branch": "unknown",
                "commit_hash": "unknown",
                "commit_time": "unknown",
                "author": "unknown",
                "message": "unknown",
                "timestamp": datetime.now().isoformat(),
                "repo_path": self.repo_path,
                "error": str(e)
            }

    def track_version_changes(self, limit: int = 10) -> Dict[str, Any]:
        """跟踪版本变更
        
        Args:
            limit: 提交记录数量限制
            
        Returns:
            Dict[str, Any]: 版本变更信息
        """
        try:
            log_result = self._run_git_command(['log', '-n', str(limit), '--oneline', '--format=%H|%an|%ae|%ci|%s'])
            
            commits = []
            if log_result['success'] and log_result['stdout']:
                for line in log_result['stdout'].split('\n'):
                    if line:
                        parts = line.split('|')
                        commits.append({
                            'hash': parts[0],
                            'author_name': parts[1],
                            'author_email': parts[2],
                            'commit_time': parts[3],
                            'message': parts[4] if len(parts) > 4 else ''
                        })

            changes = {
                "recent_commits": commits,
                "total_commits": len(commits),
                "timestamp": datetime.now().isoformat(),
                "repo_path": self.repo_path
            }

            self.logger.info(f"跟踪版本变更: {changes}")
            return changes
        except Exception as e:
            self.logger.error(f"跟踪版本变更失败: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def generate_version_report(self) -> Dict[str, Any]:
        """生成版本报告
        
        Returns:
            Dict[str, Any]: 版本报告
        """
        try:
            version_info = self.get_system_version()
            changes = self.track_version_changes()
            branches = self.branch(all=True)
            remotes = self.remote(verbose=True)

            report = {
                "version_info": version_info,
                "changes": changes,
                "branches": branches,
                "remotes": remotes,
                "timestamp": datetime.now().isoformat(),
                "repo_path": self.repo_path
            }

            self.logger.info(f"生成版本报告: {report}")
            return report
        except Exception as e:
            self.logger.error(f"生成版本报告失败: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_file_history(self, file_path: str, limit: int = 10) -> Dict[str, Any]:
        """获取文件修改历史
        
        Args:
            file_path: 文件路径
            limit: 记录数量限制
            
        Returns:
            Dict[str, Any]: 文件修改历史
        """
        self.logger.info(f"获取文件修改历史: {file_path}")
        command = ['log', '-n', str(limit), '--oneline', '--follow', '--', file_path]
        result = self._run_git_command(command)
        
        if result['success']:
            history = []
            for line in result['stdout'].split('\n'):
                if line:
                    parts = line.split(' ', 1)
                    history.append({
                        'hash': parts[0],
                        'message': parts[1] if len(parts) > 1 else ''
                    })
            return {**result, 'history': history}
        
        return result

    def show_commit(self, commit_hash: str = 'HEAD') -> Dict[str, Any]:
        """查看提交详情
        
        Args:
            commit_hash: 提交hash
            
        Returns:
            Dict[str, Any]: 提交详情
        """
        self.logger.info(f"查看提交详情: {commit_hash}")
        result = self._run_git_command(['show', commit_hash, '--stat'])
        return result

    def cherry_pick(self, commit_hash: str, no_commit: bool = False) -> Dict[str, Any]:
        """樱桃采摘(将指定提交应用到当前分支)
        
        Args:
            commit_hash: 要应用的提交hash
            no_commit: 是否不自动提交
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        command = ['cherry-pick', commit_hash]
        if no_commit:
            command.append('--no-commit')
        
        self.logger.info(f"樱桃采摘: {commit_hash}")
        return self._run_git_command(command)

    def rebase(self, branch: str, interactive: bool = False) -> Dict[str, Any]:
        """变基
        
        Args:
            branch: 要变基到的分支
            interactive: 是否交互式变基
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        command = ['rebase', branch]
        if interactive:
            command.append('-i')
        
        self.logger.info(f"变基到: {branch}")
        return self._run_git_command(command)

    def clean(self, dry_run: bool = False) -> Dict[str, Any]:
        """清理未跟踪的文件
        
        Args:
            dry_run: 是否仅预览不实际执行
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        command = ['clean', '-f']
        if dry_run:
            command.append('-n')
        
        self.logger.info(f"清理未跟踪文件{'(预览)' if dry_run else ''}")
        return self._run_git_command(command)

    def __str__(self):
        return f"GitManager(instance_id={self.instance_id}, repo_path={self.repo_path})"

    def __repr__(self):
        return self.__str__()

git_manager = GitManager()

def get_git_manager(repo_path: str = None) -> GitManager:
    """获取Git管理器实例
    
    Args:
        repo_path: Git仓库路径
        
    Returns:
        GitManager: Git管理器实例
    """
    if repo_path:
        return GitManager(repo_path)
    return git_manager

def initialize():
    """初始化Git管理器"""
    global git_manager
    git_manager = GitManager()
    logger.info("Git管理器初始化完成")