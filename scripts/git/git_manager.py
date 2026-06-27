#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git管理工具
提供完整的Git工作流管理功能
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

class GitManager:
    """Git管理工具"""
    
    def __init__(self, repo_path=None):
        self.repo_path = repo_path or os.getcwd()
        self.git_dir = os.path.join(self.repo_path, '.git')
        
    def run_git_command(self, command):
        """执行Git命令"""
        try:
            result = subprocess.run(
                f'git {command}',
                shell=True,
                cwd=self.repo_path,
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
            
    def status(self):
        """获取Git状态"""
        result = self.run_git_command('status --porcelain')
        if result['success']:
            files = []
            for line in result['output'].strip().split('\n'):
                if line:
                    status = line[:2].strip()
                    file = line[3:].strip()
                    files.append({'status': status, 'file': file})
            return {
                'success': True,
                'files': files,
                'count': len(files)
            }
        return result
        
    def branch(self):
        """获取当前分支"""
        result = self.run_git_command('branch --show-current')
        if result['success']:
            return {
                'success': True,
                'branch': result['output'].strip()
            }
        return result
        
    def branches(self):
        """获取所有分支"""
        result = self.run_git_command('branch -a')
        if result['success']:
            branches = []
            for line in result['output'].strip().split('\n'):
                if line:
                    current = line.startswith('*')
                    name = line.replace('*', '').strip()
                    branches.append({'name': name, 'current': current})
            return {
                'success': True,
                'branches': branches
            }
        return result
        
    def log(self, count=10):
        """获取提交历史"""
        result = self.run_git_command(f'log -{count} --pretty=format:"%H|%an|%ai|%s"')
        if result['success']:
            commits = []
            for line in result['output'].strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        commits.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'date': parts[2],
                            'message': '|'.join(parts[3:])
                        })
            return {
                'success': True,
                'commits': commits
            }
        return result
        
    def add(self, files='.'):
        """添加文件到暂存区"""
        if isinstance(files, list):
            files = ' '.join(files)
        return self.run_git_command(f'add {files}')
        
    def commit(self, message):
        """提交更改"""
        return self.run_git_command(f'commit -m "{message}"')
        
    def push(self, remote='origin', branch=None):
        """推送到远程仓库"""
        if branch is None:
            branch_result = self.branch()
            if branch_result['success']:
                branch = branch_result['branch']
            else:
                branch = 'main'
        return self.run_git_command(f'push {remote} {branch}')
        
    def pull(self, remote='origin', branch=None):
        """从远程仓库拉取"""
        if branch is None:
            branch_result = self.branch()
            if branch_result['success']:
                branch = branch_result['branch']
            else:
                branch = 'main'
        return self.run_git_command(f'pull {remote} {branch}')
        
    def create_branch(self, branch_name):
        """创建新分支"""
        return self.run_git_command(f'branch {branch_name}')
        
    def switch_branch(self, branch_name):
        """切换分支"""
        return self.run_git_command(f'checkout {branch_name}')
        
    def merge_branch(self, branch_name):
        """合并分支"""
        return self.run_git_command(f'merge {branch_name}')
        
    def diff(self, file=None):
        """查看差异"""
        if file:
            return self.run_git_command(f'diff {file}')
        return self.run_git_command('diff')
        
    def stash(self, message=''):
        """暂存更改"""
        if message:
            return self.run_git_command(f'sash push -m "{message}"')
        return self.run_git_command('stash push')
        
    def stash_pop(self):
        """恢复暂存"""
        return self.run_git_command('stash pop')
        
    def remote(self):
        """获取远程仓库信息"""
        result = self.run_git_command('remote -v')
        if result['success']:
            remotes = {}
            for line in result['output'].strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        url = parts[1]
                        if name not in remotes:
                            remotes[name] = {}
                        if 'fetch' in line or '(fetch)' in line:
                            remotes[name]['fetch'] = url
                        elif 'push' in line or '(push)' in line:
                            remotes[name]['push'] = url
            return {
                'success': True,
                'remotes': remotes
            }
        return result
        
    def tag(self, tag_name, message=''):
        """创建标签"""
        if message:
            return self.run_git_command(f'tag -a {tag_name} -m "{message}"')
        return self.run_git_command(f'tag {tag_name}')
        
    def tags(self):
        """获取所有标签"""
        result = self.run_git_command('tag -l')
        if result['success']:
            tags = result['output'].strip().split('\n')
            return {
                'success': True,
                'tags': [t for t in tags if t]
            }
        return result
        
    def reset(self, commit='HEAD', mode='soft'):
        """重置到指定提交"""
        return self.run_git_command(f'reset --{mode} {commit}')
        
    def clean(self, dry_run=False):
        """清理未跟踪的文件"""
        if dry_run:
            return self.run_git_command('clean -n')
        return self.run_git_command('clean -fd')
        
    def summary(self):
        """获取Git仓库摘要"""
        status = self.status()
        branch = self.branch()
        remote = self.remote()
        log = self.log(5)
        
        return {
            'repo_path': self.repo_path,
            'branch': branch.get('branch', 'unknown'),
            'status': {
                'modified': len([f for f in status.get('files', []) if 'M' in f['status']]),
                'added': len([f for f in status.get('files', []) if 'A' in f['status']]),
                'deleted': len([f for f in status.get('files', []) if 'D' in f['status']]),
                'untracked': len([f for f in status.get('files', []) if '?' in f['status']])
            },
            'remotes': list(remote.get('remotes', {}).keys()),
            'recent_commits': log.get('commits', [])
        }

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Git管理工具")
        print("\n用法: python git_manager.py <命令> [参数]")
        print("\n命令:")
        print("  status    - 查看状态")
        print("  branch    - 查看当前分支")
        print("  branches  - 查看所有分支")
        print("  log       - 查看提交历史")
        print("  remote    - 查看远程仓库")
        print("  summary   - 查看摘要")
        print("  add       - 添加文件")
        print("  commit    - 提交更改")
        print("  push      - 推送")
        print("  pull      - 拉取")
        return
        
    manager = GitManager()
    command = sys.argv[1]
    
    if command == 'status':
        result = manager.status()
        if result['success']:
            print(f"状态: {result['count']} 个文件")
            for file in result['files']:
                print(f"  {file['status']} {file['file']}")
        else:
            print(f"错误: {result['error']}")
            
    elif command == 'branch':
        result = manager.branch()
        if result['success']:
            print(f"当前分支: {result['branch']}")
        else:
            print(f"错误: {result['error']}")
            
    elif command == 'branches':
        result = manager.branches()
        if result['success']:
            print("所有分支:")
            for branch in result['branches']:
                current = '* ' if branch['current'] else '  '
                print(f"{current}{branch['name']}")
        else:
            print(f"错误: {result['error']}")
            
    elif command == 'log':
        result = manager.log()
        if result['success']:
            print("提交历史:")
            for commit in result['commits']:
                print(f"  {commit['hash'][:8]} - {commit['message']} ({commit['author']}, {commit['date']})")
        else:
            print(f"错误: {result['error']}")
            
    elif command == 'remote':
        result = manager.remote()
        if result['success']:
            print("远程仓库:")
            for name, urls in result['remotes'].items():
                print(f"  {name}:")
                if 'fetch' in urls:
                    print(f"    fetch: {urls['fetch']}")
                if 'push' in urls:
                    print(f"    push: {urls['push']}")
        else:
            print(f"错误: {result['error']}")
            
    elif command == 'summary':
        result = manager.summary()
        print("Git仓库摘要:")
        print(f"  路径: {result['repo_path']}")
        print(f"  分支: {result['branch']}")
        print(f"  状态:")
        print(f"    修改: {result['status']['modified']}")
        print(f"    添加: {result['status']['added']}")
        print(f"    删除: {result['status']['deleted']}")
        print(f"    未跟踪: {result['status']['untracked']}")
        print(f"  远程仓库: {', '.join(result['remotes'])}")
        print(f"  最近提交:")
        for commit in result['recent_commits']:
            print(f"    {commit['hash'][:8]} - {commit['message']}")
            
    elif command == 'add':
        files = sys.argv[2:] if len(sys.argv) > 2 else '.'
        result = manager.add(files)
        if result['success']:
            print("✅ 文件已添加")
        else:
            print(f"错误: {result['error']}")
            
    elif command == 'commit':
        if len(sys.argv) < 3:
            print("错误: 请提供提交信息")
            return
        message = sys.argv[2]
        result = manager.commit(message)
        if result['success']:
            print("✅ 提交成功")
        else:
            print(f"错误: {result['error']}")
            
    elif command == 'push':
        result = manager.push()
        if result['success']:
            print("✅ 推送成功")
        else:
            print(f"错误: {result['error']}")
            
    elif command == 'pull':
        result = manager.pull()
        if result['success']:
            print("✅ 拉取成功")
        else:
            print(f"错误: {result['error']}")
            
    else:
        print(f"未知命令: {command}")

if __name__ == '__main__':
    main()
