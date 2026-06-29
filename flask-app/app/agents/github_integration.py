# -*- coding: utf-8 -*-
"""
GitHubIntegration - GitHub集成模块
提供代码仓库对接功能，支持读写权限、分支创建、提交合并等操作
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List
from github import Github
from github.GithubException import GithubException
from github.Repository import Repository
from github.Branch import Branch
from github.PullRequest import PullRequest

logger = logging.getLogger(__name__)


class GitHubIntegration:
    """GitHub集成模块"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.github = None
        self.token = os.environ.get('GITHUB_TOKEN')
        self.repositories = {}
        self._connect()
    
    def _connect(self):
        """连接GitHub"""
        if self.token:
            try:
                self.github = Github(self.token)
                self.user = self.github.get_user()
                logger.info(f"[GitHub集成] 已连接GitHub: {self.user.login}")
            except Exception as e:
                logger.error(f"[GitHub集成] 连接GitHub失败: {e}")
        else:
            logger.warning("[GitHub集成] 未设置GITHUB_TOKEN环境变量")
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.github is not None
    
    def get_repositories(self) -> List[Dict]:
        """获取仓库列表"""
        repos = []
        
        if not self.github:
            return repos
        
        try:
            for repo in self.github.get_user().get_repos():
                repos.append({
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description,
                    'private': repo.private,
                    'stars': repo.stargazers_count,
                    'forks': repo.forks_count,
                    'url': repo.html_url,
                    'default_branch': repo.default_branch
                })
        except Exception as e:
            logger.error(f"[GitHub集成] 获取仓库列表失败: {e}")
        
        return repos
    
    def get_repository(self, repo_name: str) -> Repository:
        """获取单个仓库"""
        if not self.github:
            return None
        
        try:
            return self.github.get_repo(repo_name)
        except Exception as e:
            logger.error(f"[GitHub集成] 获取仓库失败 {repo_name}: {e}")
            return None
    
    def read_file(self, repo_name: str, file_path: str, branch: str = None) -> Dict:
        """读取仓库文件"""
        repo = self.get_repository(repo_name)
        if not repo:
            return {'success': False, 'error': '仓库不存在'}
        
        try:
            if branch:
                contents = repo.get_contents(file_path, ref=branch)
            else:
                contents = repo.get_contents(file_path)
            
            return {
                'success': True,
                'content': contents.decoded_content.decode('utf-8'),
                'sha': contents.sha,
                'branch': branch or repo.default_branch
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def write_file(self, repo_name: str, file_path: str, content: str, 
                   message: str, branch: str = None) -> Dict:
        """写入仓库文件"""
        repo = self.get_repository(repo_name)
        if not repo:
            return {'success': False, 'error': '仓库不存在'}
        
        try:
            if branch:
                contents = repo.get_contents(file_path, ref=branch)
                result = repo.update_file(
                    file_path, message, content, contents.sha, branch=branch
                )
            else:
                contents = repo.get_contents(file_path)
                result = repo.update_file(
                    file_path, message, content, contents.sha
                )
            
            return {
                'success': True,
                'commit': result.get('commit').sha,
                'url': result.get('commit').html_url
            }
        
        except GithubException as e:
            if e.status == 404:
                try:
                    result = repo.create_file(file_path, message, content)
                    return {
                        'success': True,
                        'commit': result.get('commit').sha,
                        'url': result.get('commit').html_url
                    }
                except Exception as e2:
                    return {'success': False, 'error': str(e2)}
            
            return {'success': False, 'error': str(e)}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_branch(self, repo_name: str, base_branch: str, new_branch: str) -> Dict:
        """创建分支"""
        repo = self.get_repository(repo_name)
        if not repo:
            return {'success': False, 'error': '仓库不存在'}
        
        try:
            base_ref = repo.get_git_ref(f"heads/{base_branch}")
            repo.create_git_ref(f"refs/heads/{new_branch}", base_ref.object.sha)
            
            return {
                'success': True,
                'branch': new_branch,
                'base_branch': base_branch,
                'url': f"{repo.html_url}/tree/{new_branch}"
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_branch(self, repo_name: str, branch_name: str) -> Dict:
        """删除分支"""
        repo = self.get_repository(repo_name)
        if not repo:
            return {'success': False, 'error': '仓库不存在'}
        
        try:
            ref = repo.get_git_ref(f"heads/{branch_name}")
            ref.delete()
            
            return {'success': True, 'branch': branch_name}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_branches(self, repo_name: str) -> List[Dict]:
        """获取分支列表"""
        repo = self.get_repository(repo_name)
        if not repo:
            return []
        
        branches = []
        try:
            for branch in repo.get_branches():
                branches.append({
                    'name': branch.name,
                    'protected': branch.protected,
                    'commit_sha': branch.commit.sha,
                    'commit_url': branch.commit.html_url
                })
        except Exception as e:
            logger.error(f"[GitHub集成] 获取分支列表失败: {e}")
        
        return branches
    
    def create_pull_request(self, repo_name: str, head_branch: str, 
                           base_branch: str, title: str, body: str = "") -> Dict:
        """创建Pull Request"""
        repo = self.get_repository(repo_name)
        if not repo:
            return {'success': False, 'error': '仓库不存在'}
        
        try:
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch
            )
            
            return {
                'success': True,
                'pr_number': pr.number,
                'title': pr.title,
                'url': pr.html_url,
                'state': pr.state
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def merge_pull_request(self, repo_name: str, pr_number: int, 
                          commit_message: str = "") -> Dict:
        """合并Pull Request"""
        repo = self.get_repository(repo_name)
        if not repo:
            return {'success': False, 'error': '仓库不存在'}
        
        try:
            pr = repo.get_pull(pr_number)
            
            if pr.state != 'open':
                return {'success': False, 'error': 'PR未打开'}
            
            commit_message = commit_message or f"Merge PR #{pr_number}: {pr.title}"
            
            pr.merge(commit_message=commit_message)
            
            return {
                'success': True,
                'pr_number': pr_number,
                'title': pr.title,
                'url': pr.html_url,
                'state': pr.state
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_pull_requests(self, repo_name: str, state: str = 'open') -> List[Dict]:
        """获取Pull Request列表"""
        repo = self.get_repository(repo_name)
        if not repo:
            return []
        
        prs = []
        try:
            for pr in repo.get_pulls(state=state):
                prs.append({
                    'number': pr.number,
                    'title': pr.title,
                    'head': pr.head.ref,
                    'base': pr.base.ref,
                    'state': pr.state,
                    'url': pr.html_url,
                    'created_at': pr.created_at.isoformat(),
                    'updated_at': pr.updated_at.isoformat()
                })
        except Exception as e:
            logger.error(f"[GitHub集成] 获取PR列表失败: {e}")
        
        return prs
    
    def commit_and_push(self, repo_name: str, file_path: str, content: str, 
                       commit_message: str, branch: str = None) -> Dict:
        """提交并推送代码"""
        result = self.write_file(repo_name, file_path, content, commit_message, branch)
        
        if result.get('success'):
            logger.info(f"[GitHub集成] 代码已提交: {repo_name}/{file_path}")
        
        return result
    
    def auto_fix_and_push(self, repo_name: str, file_path: str, 
                         original_content: str, fixed_content: str, 
                         fix_description: str) -> Dict:
        """自动修复并推送"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fix_branch = f"auto-fix/{timestamp}"
        
        try:
            repo = self.get_repository(repo_name)
            if not repo:
                return {'success': False, 'error': '仓库不存在'}
            
            base_branch = repo.default_branch
            
            create_result = self.create_branch(repo_name, base_branch, fix_branch)
            if not create_result.get('success'):
                return create_result
            
            commit_message = f"Auto-fix: {fix_description}\n\nTimestamp: {timestamp}"
            
            write_result = self.write_file(repo_name, file_path, fixed_content, 
                                         commit_message, fix_branch)
            if not write_result.get('success'):
                self.delete_branch(repo_name, fix_branch)
                return write_result
            
            pr_title = f"Auto-fix: {fix_description}"
            pr_body = f"自动修复内容:\n\n- 文件: {file_path}\n- 描述: {fix_description}\n- 时间: {timestamp}"
            
            pr_result = self.create_pull_request(repo_name, fix_branch, 
                                                base_branch, pr_title, pr_body)
            
            return {
                'success': True,
                'branch': fix_branch,
                'commit': write_result.get('commit'),
                'pr': pr_result
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def execute(self, action: str, **kwargs) -> Dict:
        """执行GitHub操作"""
        actions = {
            'list_repos': self.get_repositories,
            'list_branches': lambda: self.get_branches(kwargs.get('repo_name')),
            'read_file': lambda: self.read_file(kwargs.get('repo_name'), kwargs.get('file_path'), kwargs.get('branch')),
            'write_file': lambda: self.write_file(kwargs.get('repo_name'), kwargs.get('file_path'), kwargs.get('content'), kwargs.get('message'), kwargs.get('branch')),
            'create_branch': lambda: self.create_branch(kwargs.get('repo_name'), kwargs.get('base_branch'), kwargs.get('new_branch')),
            'delete_branch': lambda: self.delete_branch(kwargs.get('repo_name'), kwargs.get('branch_name')),
            'create_pr': lambda: self.create_pull_request(kwargs.get('repo_name'), kwargs.get('head_branch'), kwargs.get('base_branch'), kwargs.get('title'), kwargs.get('body')),
            'merge_pr': lambda: self.merge_pull_request(kwargs.get('repo_name'), kwargs.get('pr_number'), kwargs.get('commit_message')),
            'list_prs': lambda: self.get_pull_requests(kwargs.get('repo_name'), kwargs.get('state')),
            'commit_and_push': lambda: self.commit_and_push(kwargs.get('repo_name'), kwargs.get('file_path'), kwargs.get('content'), kwargs.get('commit_message'), kwargs.get('branch')),
            'auto_fix_and_push': lambda: self.auto_fix_and_push(kwargs.get('repo_name'), kwargs.get('file_path'), kwargs.get('original_content'), kwargs.get('fixed_content'), kwargs.get('fix_description'))
        }
        
        if action not in actions:
            return {'success': False, 'error': f'未知动作: {action}'}
        
        return actions[action]()


def get_github_integration() -> GitHubIntegration:
    """获取GitHub集成实例"""
    return GitHubIntegration()


def init_github():
    """初始化GitHub集成"""
    return get_github_integration()
