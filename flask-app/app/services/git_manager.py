import os
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from app.ai.server_ai import server_ai

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitManager:
    """Git 管理器，负责整合 Git 核心功能"""
    
    def __init__(self, repo_path: str = None):
        self.instance_id = f"git_manager_{id(self)}"
        self.name = "Git 管理器"
        self.description = "负责整合 Git 核心功能"
        self.logger = logger
        self.logger.info(f"初始化 Git 管理器: {self.instance_id}")
        
        # 仓库路径
        self.repo_path = repo_path or os.getcwd()
        
        # 检查是否在 Git 仓库中
        if not self._is_git_repo():
            self.logger.warning(f"当前目录 {self.repo_path} 不是 Git 仓库")
        else:
            self.logger.info(f"当前目录 {self.repo_path} 是 Git 仓库")
    
    def _is_git_repo(self) -> bool:
        """检查当前目录是否是 Git 仓库
        
        Returns:
            是否是 Git 仓库
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
            self.logger.error(f"检查 Git 仓库失败: {str(e)}")
            return False
    
    def _run_git_command(self, command: List[str]) -> Dict[str, Any]:
        """运行 Git 命令
        
        Args:
            command: Git 命令列表
            
        Returns:
            命令执行结果
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
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            self.logger.error(f"运行 Git 命令失败: {str(e)}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": 1
            }
    
    def init_repo(self) -> Dict[str, Any]:
        """初始化 Git 仓库
        
        Returns:
            命令执行结果
        """
        self.logger.info(f"初始化 Git 仓库: {self.repo_path}")
        return self._run_git_command(['init'])
    
    def clone_repo(self, url: str, target_dir: str = None) -> Dict[str, Any]:
        """克隆 Git 仓库
        
        Args:
            url: 仓库 URL
            target_dir: 目标目录
            
        Returns:
            命令执行结果
        """
        command = ['clone', url]
        if target_dir:
            command.append(target_dir)
        self.logger.info(f"克隆 Git 仓库: {url} -> {target_dir or os.path.basename(url)}")
        return self._run_git_command(command)
    
    def add(self, paths: List[str] = None) -> Dict[str, Any]:
        """添加文件到暂存区
        
        Args:
            paths: 文件路径列表，None 表示添加所有文件
            
        Returns:
            命令执行结果
        """
        command = ['add']
        if paths:
            command.extend(paths)
        else:
            command.append('.')
        self.logger.info(f"添加文件到暂存区: {paths or 'all files'}")
        return self._run_git_command(command)
    
    def commit(self, message: str) -> Dict[str, Any]:
        """提交更改
        
        Args:
            message: 提交消息
            
        Returns:
            命令执行结果
        """
        self.logger.info(f"提交更改: {message}")
        return self._run_git_command(['commit', '-m', message])
    
    def push(self, remote: str = 'origin', branch: str = 'master') -> Dict[str, Any]:
        """推送更改
        
        Args:
            remote: 远程仓库
            branch: 分支名称
            
        Returns:
            命令执行结果
        """
        self.logger.info(f"推送更改: {remote}/{branch}")
        return self._run_git_command(['push', remote, branch])
    
    def pull(self, remote: str = 'origin', branch: str = 'master') -> Dict[str, Any]:
        """拉取更改
        
        Args:
            remote: 远程仓库
            branch: 分支名称
            
        Returns:
            命令执行结果
        """
        self.logger.info(f"拉取更改: {remote}/{branch}")
        return self._run_git_command(['pull', remote, branch])
    
    def status(self) -> Dict[str, Any]:
        """查看仓库状态
        
        Returns:
            命令执行结果
        """
        self.logger.info("查看仓库状态")
        return self._run_git_command(['status'])
    
    def log(self, limit: int = 10) -> Dict[str, Any]:
        """查看提交日志
        
        Args:
            limit: 日志条数限制
            
        Returns:
            命令执行结果
        """
        self.logger.info(f"查看提交日志，限制 {limit} 条")
        return self._run_git_command(['log', '-n', str(limit), '--oneline'])
    
    def branch(self) -> Dict[str, Any]:
        """查看分支
        
        Returns:
            命令执行结果
        """
        self.logger.info("查看分支")
        return self._run_git_command(['branch'])
    
    def checkout(self, branch: str) -> Dict[str, Any]:
        """切换分支
        
        Args:
            branch: 分支名称
            
        Returns:
            命令执行结果
        """
        self.logger.info(f"切换分支: {branch}")
        return self._run_git_command(['checkout', branch])
    
    def create_branch(self, branch: str) -> Dict[str, Any]:
        """创建分支
        
        Args:
            branch: 分支名称
            
        Returns:
            命令执行结果
        """
        self.logger.info(f"创建分支: {branch}")
        return self._run_git_command(['checkout', '-b', branch])
    
    def merge(self, branch: str) -> Dict[str, Any]:
        """合并分支
        
        Args:
            branch: 要合并的分支名称
            
        Returns:
            命令执行结果
        """
        self.logger.info(f"合并分支: {branch}")
        return self._run_git_command(['merge', branch])
    
    def remote(self) -> Dict[str, Any]:
        """查看远程仓库
        
        Returns:
            命令执行结果
        """
        self.logger.info("查看远程仓库")
        return self._run_git_command(['remote', '-v'])
    
    def add_remote(self, name: str, url: str) -> Dict[str, Any]:
        """添加远程仓库
        
        Args:
            name: 远程仓库名称
            url: 远程仓库 URL
            
        Returns:
            命令执行结果
        """
        self.logger.info(f"添加远程仓库: {name} -> {url}")
        return self._run_git_command(['remote', 'add', name, url])
    
    def remove_remote(self, name: str) -> Dict[str, Any]:
        """移除远程仓库
        
        Args:
            name: 远程仓库名称
            
        Returns:
            命令执行结果
        """
        self.logger.info(f"移除远程仓库: {name}")
        return self._run_git_command(['remote', 'remove', name])
    
    def diff(self, path: str = None) -> Dict[str, Any]:
        """查看文件差异
        
        Args:
            path: 文件路径
            
        Returns:
            命令执行结果
        """
        command = ['diff']
        if path:
            command.append(path)
        self.logger.info(f"查看文件差异: {path or 'all files'}")
        return self._run_git_command(command)
    
    def reset(self, mode: str = 'mixed', commit: str = 'HEAD') -> Dict[str, Any]:
        """重置提交
        
        Args:
            mode: 重置模式 (mixed, soft, hard)
            commit: 提交 hash 或引用
            
        Returns:
            命令执行结果
        """
        self.logger.info(f"重置提交: {mode} {commit}")
        return self._run_git_command(['reset', f'--{mode}', commit])
    
    def tag(self, name: str, message: str = None) -> Dict[str, Any]:
        """创建标签
        
        Args:
            name: 标签名称
            message: 标签消息
            
        Returns:
            命令执行结果
        """
        command = ['tag', name]
        if message:
            command.extend(['-m', message])
        self.logger.info(f"创建标签: {name}")
        return self._run_git_command(command)
    
    def fetch(self, remote: str = 'origin') -> Dict[str, Any]:
        """获取远程更改
        
        Args:
            remote: 远程仓库
            
        Returns:
            命令执行结果
        """
        self.logger.info(f"获取远程更改: {remote}")
        return self._run_git_command(['fetch', remote])
    
    def stash(self, message: str = None) -> Dict[str, Any]:
        """暂存更改
        
        Args:
            message: 暂存消息
            
        Returns:
            命令执行结果
        """
        command = ['stash']
        if message:
            command.extend(['push', '-m', message])
        self.logger.info(f"暂存更改: {message or 'no message'}")
        return self._run_git_command(command)
    
    def stash_pop(self) -> Dict[str, Any]:
        """恢复暂存的更改
        
        Returns:
            命令执行结果
        """
        self.logger.info("恢复暂存的更改")
        return self._run_git_command(['stash', 'pop'])
    
    def get_repo_info(self) -> Dict[str, Any]:
        """获取仓库信息
        
        Returns:
            仓库信息
        """
        try:
            info = {
                "repo_path": self.repo_path,
                "is_git_repo": self._is_git_repo(),
                "status": self.status(),
                "branches": self.branch(),
                "remotes": self.remote(),
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
    
    def __str__(self):
        return f"GitManager(instance_id={self.instance_id}, repo_path={self.repo_path})"
    
    def __repr__(self):
        return self.__str__()
    
    def get_system_version(self) -> Dict[str, Any]:
        """获取系统版本信息
        
        Returns:
            系统版本信息
        """
        try:
            # 获取当前分支
            branch_result = self._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
            branch = branch_result['stdout'].strip() if branch_result['success'] else 'unknown'
            
            # 获取当前提交哈希
            commit_result = self._run_git_command(['rev-parse', 'HEAD'])
            commit_hash = commit_result['stdout'].strip() if commit_result['success'] else 'unknown'
            
            # 获取当前提交时间
            commit_time_result = self._run_git_command(['log', '-1', '--format=%ci', 'HEAD'])
            commit_time = commit_time_result['stdout'].strip() if commit_time_result['success'] else 'unknown'
            
            # 获取当前提交作者
            author_result = self._run_git_command(['log', '-1', '--format=%an', 'HEAD'])
            author = author_result['stdout'].strip() if author_result['success'] else 'unknown'
            
            # 获取当前提交消息
            message_result = self._run_git_command(['log', '-1', '--format=%s', 'HEAD'])
            message = message_result['stdout'].strip() if message_result['success'] else 'unknown'
            
            # 构建版本信息
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
    
    def analyze_version_with_ai(self, version_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """使用 AI 分析版本信息
        
        Args:
            version_info: 版本信息，如果为 None 则自动获取
            
        Returns:
            AI 分析结果
        """
        try:
            # 如果没有提供版本信息，自动获取
            if not version_info:
                version_info = self.get_system_version()
            
            # 构建 AI 分析数据
            ai_data = {
                "version_info": version_info,
                "analysis_type": "version_analysis",
                "timestamp": datetime.now().isoformat()
            }
            
            # 使用 AI 进行分析
            analysis_result = server_ai.analyze_server_performance(
                "system_version",
                ai_data
            )
            
            # 构建分析结果
            result = {
                "version_info": version_info,
                "ai_analysis": analysis_result,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"使用 AI 分析版本信息: {result}")
            return result
        except Exception as e:
            self.logger.error(f"使用 AI 分析版本信息失败: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def track_version_changes(self) -> Dict[str, Any]:
        """跟踪版本变更
        
        Returns:
            版本变更信息
        """
        try:
            # 获取最近的提交记录
            log_result = self._run_git_command(['log', '-n', '10', '--oneline'])
            commits = log_result['stdout'].strip().split('\n') if log_result['success'] else []
            
            # 构建版本变更信息
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
            版本报告
        """
        try:
            # 获取版本信息
            version_info = self.get_system_version()
            
            # 跟踪版本变更
            changes = self.track_version_changes()
            
            # 使用 AI 分析版本信息
            ai_analysis = self.analyze_version_with_ai(version_info)
            
            # 构建版本报告
            report = {
                "version_info": version_info,
                "changes": changes,
                "ai_analysis": ai_analysis,
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

# 创建全局 Git 管理器实例
git_manager = GitManager()