#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub CLI集成工具
提供GitHub操作集成功能
"""

import os
import sys
import json
import subprocess
from datetime import datetime

class GitHubCLI:
    """GitHub CLI集成工具"""
    
    def __init__(self):
        self.check_gh_installed()
        
    def check_gh_installed(self):
        """检查gh是否已安装"""
        try:
            result = subprocess.run(
                ['gh', '--version'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print("❌ GitHub CLI未安装")
                print("请安装: brew install gh (macOS)")
                print("或访问: https://cli.github.com/")
                return False
            return True
        except FileNotFoundError:
            print("❌ GitHub CLI未安装")
            return False
            
    def run_gh_command(self, command):
        """执行gh命令"""
        try:
            result = subprocess.run(
                f'gh {command}',
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }
            
    def auth_status(self):
        """检查认证状态"""
        return self.run_gh_command('auth status')
        
    def auth_login(self):
        """登录GitHub"""
        print("🔐 登录GitHub...")
        return self.run_gh_command('auth login')
        
    def repo_create(self, name, private=False, description=''):
        """创建仓库"""
        visibility = 'private' if private else 'public'
        cmd = f'repo create {name} --{visibility}'
        if description:
            cmd += f' --description "{description}"'
        return self.run_gh_command(cmd)
        
    def repo_view(self, repo=''):
        """查看仓库"""
        return self.run_gh_command(f'repo view {repo}')
        
    def repo_list(self, limit=30):
        """列出仓库"""
        return self.run_gh_command(f'repo list --limit {limit}')
        
    def issue_create(self, title, body='', labels='', repo=''):
        """创建Issue"""
        cmd = f'issue create --title "{title}"'
        if body:
            cmd += f' --body "{body}"'
        if labels:
            cmd += f' --labels {labels}'
        if repo:
            cmd += f' --repo {repo}'
        return self.run_gh_command(cmd)
        
    def issue_list(self, state='open', limit=30, repo=''):
        """列出Issues"""
        cmd = f'issue list --state {state} --limit {limit}'
        if repo:
            cmd += f' --repo {repo}'
        return self.run_gh_command(cmd)
        
    def pr_create(self, title, body='', base='main', draft=False):
        """创建Pull Request"""
        cmd = f'pr create --title "{title}" --base {base}'
        if body:
            cmd += f' --body "{body}"'
        if draft:
            cmd += ' --draft'
        return self.run_gh_command(cmd)
        
    def pr_list(self, state='open', limit=30):
        """列出Pull Requests"""
        return self.run_gh_command(f'pr list --state {state} --limit {limit}')
        
    def pr_checkout(self, pr_number):
        """检出Pull Request"""
        return self.run_gh_command(f'pr checkout {pr_number}')
        
    def release_create(self, tag, title='', notes=''):
        """创建Release"""
        cmd = f'release create {tag}'
        if title:
            cmd += f' --title "{title}"'
        if notes:
            cmd += f' --notes "{notes}"'
        return self.run_gh_command(cmd)
        
    def release_list(self, limit=30):
        """列出Releases"""
        return self.run_gh_command(f'release list --limit {limit}')
        
    def workflow_list(self):
        """列出Workflows"""
        return self.run_gh_command('workflow list')
        
    def workflow_run(self, workflow, ref='main'):
        """运行Workflow"""
        return self.run_gh_command(f'workflow run {workflow} --ref {ref}')
        
    def run_list(self, limit=10):
        """列出Workflow Runs"""
        return self.run_gh_command(f'run list --limit {limit}')
        
    def gist_create(self, file, public=False, description=''):
        """创建Gist"""
        cmd = f'gist create {file}'
        if public:
            cmd += ' --public'
        if description:
            cmd += f' --desc "{description}"'
        return self.run_gh_command(cmd)
        
    def gist_list(self, limit=30):
        """列出Gists"""
        return self.run_gh_command(f'gist list --limit {limit}')
        
    def search_repos(self, query, limit=30):
        """搜索仓库"""
        return self.run_gh_command(f'search repos "{query}" --limit {limit}')
        
    def search_code(self, query, limit=30):
        """搜索代码"""
        return self.run_gh_command(f'search code "{query}" --limit {limit}')

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("GitHub CLI集成工具")
        print("\n用法: python github_cli.py <命令> [参数]")
        print("\n命令:")
        print("  auth       - 检查认证状态")
        print("  login      - 登录GitHub")
        print("  repos      - 列出仓库")
        print("  issues     - 列出Issues")
        print("  prs        - 列出Pull Requests")
        print("  releases   - 列出Releases")
        print("  workflows  - 列出Workflows")
        print("  runs       - 列出Workflow Runs")
        print("  gists      - 列出Gists")
        return
        
    cli = GitHubCLI()
    command = sys.argv[1]
    
    if command == 'auth':
        result = cli.auth_status()
        print(result['output'])
        if not result['success']:
            print(result['error'])
            
    elif command == 'login':
        result = cli.auth_login()
        print(result['output'])
        
    elif command == 'repos':
        result = cli.repo_list()
        if result['success']:
            print(result['output'])
        else:
            print(f"错误: {result['error']}")
            
    elif command == 'issues':
        result = cli.issue_list()
        if result['success']:
            print(result['output'])
        else:
            print(f"错误: {result['error']}")
            
    elif command == 'prs':
        result = cli.pr_list()
        if result['success']:
            print(result['output'])
        else:
            print(f"错误: {result['error']}")
            
    elif command == 'releases':
        result = cli.release_list()
        if result['success']:
            print(result['output'])
        else:
            print(f"错误: {result['error']}")
            
    elif command == 'workflows':
        result = cli.workflow_list()
        if result['success']:
            print(result['output'])
        else:
            print(f"错误: {result['error']}")
            
    elif command == 'runs':
        result = cli.run_list()
        if result['success']:
            print(result['output'])
        else:
            print(f"错误: {result['error']}")
            
    elif command == 'gists':
        result = cli.gist_list()
        if result['success']:
            print(result['output'])
        else:
            print(f"错误: {result['error']}")
            
    else:
        print(f"未知命令: {command}")

if __name__ == '__main__':
    main()
