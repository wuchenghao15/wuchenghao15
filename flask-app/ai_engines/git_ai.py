# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git AI模块 - 专门处理Git版本控制和代码管理
负责Git操作, 分支管理,代码审查,自动提交等功能
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.ai.base_ai import BaseAI
from app.services.git_manager import git_manager

logger = logging.getLogger('git_ai')


class GitAI(BaseAI):
    """Git AI类 - 专门处理Git版本控制和代码管理"""

    def __init__(self, instance_id: str):
        """初始化Git AI"""
        super().__init__(instance_id, ai_type='git')
        self.name = 'Git AI'
        self.description = '专攻Git版本控制, 代码管理,分支策略和自动化工作流'
        self.responsibilities = [
            'Git仓库管理与操作',
            '分支策略与管理',
            '代码审查与分析',
            '自动提交与发布',
            '版本历史分析',
            '代码变更检测与优化',
            '冲突检测与解决方案建议',
            '工作流自动化'
        ]

        self.git_manager = git_manager

        self.git_operations_history = []
        self.max_history_size = 100

        self.auto_commit_enabled = False
        self.auto_commit_interval = 300

        self.monitoring_active = False
        self.last_checked_files = set()

        self.git_knowledge_base = {
            'branching_strategies': {
                'git_flow': 'Git Flow工作流: master, develop, feature/*, release/*, hotfix/*',
                'trunk_based': '基于主干开发: 短生命周期分支,频繁合并到主干',
                'github_flow': 'GitHub Flow: 简单的分支策略,一个长期分支'
            },
            'best_practices': {
                'commit_messages': '提交信息应该清晰描述变更内容,使用动词开头',
                'atomic_commits': '每次提交应该是一个原子性变更,只做一件事',
                'branch_naming': '使用语义化分支命名,如feature/user-login, bugfix/login-error'
            },
            'common_commands': {
                'status': 'git status - 查看仓库状态',
                'add': 'git add . - 添加所有文件到暂存区',
                'commit': 'git commit -m "message" - 提交变更',
                'push': 'git push origin branch - 推送到远程仓库',
                'pull': 'git pull origin branch - 拉取远程更新',
                'branch': 'git branch - 查看分支列表',
                'checkout': 'git checkout branch - 切换分支',
                'merge': 'git merge branch - 合并分支',
                'log': 'git log --oneline - 查看提交历史',
                'diff': 'git diff - 查看文件差异'
            },
            'conflict_resolution': {
                'prevention': '经常拉取远程更新,保持分支同步',
                'detection': '使用git status和git diff检测冲突',
                'resolution': '仔细检查冲突标记(<<<<<<<, =======, >>>>>>>),选择正确的代码'
            }
        }

        logger.info(f"Git AI初始化完成: {self.instance_id}")

    def analyze_git_status(self) -> Dict[str, Any]:
        """分析Git仓库状态"""
        try:
            status_result = self.git_manager.status()

            analysis = {
                'is_git_repo': self.git_manager._is_git_repo(),
                'status_output': status_result.get('stdout', ''),
                'has_changes': 'Changes not staged' in status_result.get('stdout', '') or
                               'Untracked files' in status_result.get('stdout', ''),
                'has_staged': 'Changes to be committed' in status_result.get('stdout', ''),
                'branch': self._get_current_branch(),
                'analysis_time': datetime.now().isoformat()
            }

            self._record_operation('analyze_status', analysis)
            return analysis
        except Exception as e:
            logger.error(f"分析Git状态失败: {str(e)}")
            return {}

    def _get_current_branch(self) -> str:
        """获取当前分支名"""
        try:
            result = self.git_manager.run_command(['branch', '--show-current'])
            return result.get('stdout', '').strip()
        except Exception:
            return 'unknown'

    def _record_operation(self, operation_type: str, details: Dict[str, Any]):
        """记录Git操作历史"""
        self.git_operations_history.append({
            'operation_type': operation_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

        if len(self.git_operations_history) > self.max_history_size:
            self.git_operations_history = self.git_operations_history[-self.max_history_size:]

    def get_status(self) -> Dict[str, Any]:
        """获取Git AI状态"""
        return {
            'instance_id': self.instance_id,
            'name': self.name,
            'is_running': True,
            'auto_commit_enabled': self.auto_commit_enabled,
            'monitoring_active': self.monitoring_active,
            'operations_count': len(self.git_operations_history)
        }


git_ai = GitAI('git_ai_default')

if __name__ == '__main__':
    print("Git AI模块加载成功")
    print(f"Git AI实例: {git_ai.instance_id}")
    print(f"Git AI职责: {git_ai.responsibilities}")
