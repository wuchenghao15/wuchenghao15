#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git AI模块 - 专门处理Git版本控制和代码管理
负责Git操作、分支管理、代码审查、自动提交等功能
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.ai.base_ai import BaseAI
from app.services.git_manager import git_manager

# 配置日志
logger = logging.getLogger('git_ai')

class GitAI(BaseAI):
    """Git AI类 - 专门处理Git版本控制和代码管理"""
    
    def __init__(self, instance_id: str):
        """初始化Git AI"""
        super().__init__(instance_id, ai_type='git')
        self.name = 'Git AI'
        self.description = '专攻Git版本控制、代码管理、分支策略和自动化工作流'
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
        
        # Git管理器实例
        self.git_manager = git_manager
        
        # Git操作历史记录
        self.git_operations_history = []
        self.max_history_size = 100
        
        # 自动提交配置
        self.auto_commit_enabled = False
        self.auto_commit_interval = 300  # 秒
        
        # 代码变更监控
        self.monitoring_active = False
        self.last_checked_files = set()
        
        # 专业知识库
        self.git_knowledge_base = {
            'branching_strategies': {
                'git_flow': 'Git Flow工作流: master, develop, feature/*, release/*, hotfix/*',
                'trunk_based': '基于主干开发: 短生命周期分支，频繁合并到主干',
                'github_flow': 'GitHub Flow: 简单的分支策略，一个长期分支'
            },
            'best_practices': {
                'commit_messages': '提交信息应该清晰描述变更内容，使用动词开头',
                'atomic_commits': '每次提交应该是一个原子性变更，只做一件事',
                'branch_naming': '使用语义化分支命名，如feature/user-login, bugfix/login-error'
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
                'prevention': '经常拉取远程更新，保持分支同步',
                'detection': '使用git status和git diff检测冲突',
                'resolution': '仔细检查冲突标记(<<<<<<<, =======, >>>>>>>)，选择正确的代码'
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
            logger.info(f"Git状态分析完成: {analysis}")
            return analysis
        except Exception as e:
            logger.error(f"分析Git状态失败: {str(e)}")
            return {'error': str(e)}
    
    def smart_commit(self, message: str = None, auto_message: bool = True) -> Dict[str, Any]:
        """智能提交：自动分析变更并生成合适的提交信息"""
        try:
            # 先添加所有变更
            add_result = self.git_manager.add()
            if not add_result.get('success', False):
                return {'error': '添加文件到暂存区失败', 'details': add_result}
            
            # 生成或使用提交信息
            if auto_message and not message:
                message = self._generate_commit_message()
            
            if not message:
                message = f"自动提交: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 提交变更
            commit_result = self.git_manager.commit(message)
            
            result = {
                'success': commit_result.get('success', False),
                'commit_message': message,
                'details': commit_result,
                'timestamp': datetime.now().isoformat()
            }
            
            self._record_operation('smart_commit', result)
            logger.info(f"智能提交完成: {result}")
            return result
        except Exception as e:
            logger.error(f"智能提交失败: {str(e)}")
            return {'error': str(e)}
    
    def analyze_branch_strategy(self) -> Dict[str, Any]:
        """分析当前分支策略并提供建议"""
        try:
            branch_result = self.git_manager.branch()
            log_result = self.git_manager.log(20)
            
            analysis = {
                'current_branch': self._get_current_branch(),
                'all_branches': self._parse_branches(branch_result.get('stdout', '')),
                'recent_commits': self._parse_commits(log_result.get('stdout', '')),
                'recommendations': self._generate_branch_recommendations(),
                'analysis_time': datetime.now().isoformat()
            }
            
            self._record_operation('analyze_branch_strategy', analysis)
            logger.info(f"分支策略分析完成")
            return analysis
        except Exception as e:
            logger.error(f"分析分支策略失败: {str(e)}")
            return {'error': str(e)}
    
    def detect_and_suggest_conflicts(self, target_branch: str = 'main') -> Dict[str, Any]:
        """检测潜在的合并冲突并提供解决方案建议"""
        try:
            current_branch = self._get_current_branch()
            
            # 获取差异
            diff_result = self.git_manager.diff()
            
            # 分析可能的冲突
            conflict_analysis = {
                'current_branch': current_branch,
                'target_branch': target_branch,
                'has_changes': len(diff_result.get('stdout', '')) > 0,
                'diff_content': diff_result.get('stdout', ''),
                'conflict_risk': self._assess_conflict_risk(diff_result.get('stdout', '')),
                'suggestions': self._generate_conflict_suggestions(),
                'analysis_time': datetime.now().isoformat()
            }
            
            self._record_operation('detect_conflicts', conflict_analysis)
            logger.info(f"冲突检测完成: {conflict_analysis}")
            return conflict_analysis
        except Exception as e:
            logger.error(f"检测冲突失败: {str(e)}")
            return {'error': str(e)}
    
    def generate_version_tag(self, version_type: str = 'patch') -> Dict[str, Any]:
        """生成版本标签"""
        try:
            # 获取当前最新标签
            latest_tag = self._get_latest_tag()
            
            # 生成新版本号
            new_version = self._increment_version(latest_tag, version_type)
            
            # 创建标签
            tag_message = f"版本 {new_version}"
            tag_result = self.git_manager.tag(new_version, tag_message)
            
            result = {
                'success': tag_result.get('success', False),
                'old_version': latest_tag,
                'new_version': new_version,
                'version_type': version_type,
                'details': tag_result,
                'timestamp': datetime.now().isoformat()
            }
            
            self._record_operation('generate_tag', result)
            logger.info(f"版本标签生成完成: {result}")
            return result
        except Exception as e:
            logger.error(f"生成版本标签失败: {str(e)}")
            return {'error': str(e)}
    
    def analyze_code_changes(self, file_path: str = None) -> Dict[str, Any]:
        """分析代码变更，提供改进建议"""
        try:
            diff_result = self.git_manager.diff(file_path)
            
            analysis = {
                'file_path': file_path or 'all files',
                'diff_content': diff_result.get('stdout', ''),
                'change_summary': self._summarize_changes(diff_result.get('stdout', '')),
                'improvement_suggestions': self._generate_improvement_suggestions(),
                'analysis_time': datetime.now().isoformat()
            }
            
            self._record_operation('analyze_code_changes', analysis)
            logger.info(f"代码变更分析完成")
            return analysis
        except Exception as e:
            logger.error(f"分析代码变更失败: {str(e)}")
            return {'error': str(e)}
    
    def auto_backup(self, backup_name: str = None) -> Dict[str, Any]:
        """自动备份当前状态"""
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 创建备份分支
            backup_branch = f"backup/{backup_name}"
            create_branch_result = self.git_manager.create_branch(backup_branch)
            
            # 切换回原分支
            original_branch = self._get_current_branch()
            checkout_result = self.git_manager.checkout(original_branch)
            
            result = {
                'success': create_branch_result.get('success', False),
                'backup_branch': backup_branch,
                'original_branch': original_branch,
                'details': {'create_branch': create_branch_result, 'checkout': checkout_result},
                'timestamp': datetime.now().isoformat()
            }
            
            self._record_operation('auto_backup', result)
            logger.info(f"自动备份完成: {result}")
            return result
        except Exception as e:
            logger.error(f"自动备份失败: {str(e)}")
            return {'error': str(e)}
    
    # 内部辅助方法
    
    def _get_current_branch(self) -> str:
        """获取当前分支名称"""
        try:
            result = self.git_manager._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
            return result.get('stdout', '').strip() if result.get('success', False) else 'unknown'
        except Exception:
            return 'unknown'
    
    def _get_latest_tag(self) -> str:
        """获取最新的标签"""
        try:
            result = self.git_manager._run_git_command(['describe', '--tags', '--abbrev=0'])
            return result.get('stdout', '').strip() if result.get('success', False) else 'v0.0.0'
        except Exception:
            return 'v0.0.0'
    
    def _increment_version(self, current_version: str, version_type: str) -> str:
        """递增版本号"""
        try:
            # 移除前导的'v'
            if current_version.startswith('v'):
                current_version = current_version[1:]
            
            # 解析版本号
            parts = current_version.split('.')
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            
            # 根据类型递增
            if version_type == 'major':
                major += 1
                minor = 0
                patch = 0
            elif version_type == 'minor':
                minor += 1
                patch = 0
            else:  # patch
                patch += 1
            
            return f"v{major}.{minor}.{patch}"
        except Exception:
            return 'v0.0.1'
    
    def _generate_commit_message(self) -> str:
        """生成提交信息"""
        try:
            status = self.git_manager.status()
            stdout = status.get('stdout', '')
            
            if 'modified:' in stdout:
                return '更新文件'
            elif 'new file:' in stdout:
                return '添加新文件'
            elif 'deleted:' in stdout:
                return '删除文件'
            else:
                return f"代码变更: {datetime.now().strftime('%Y-%m-%d')}"
        except Exception:
            return f"自动提交: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    def _parse_branches(self, branch_output: str) -> List[Dict[str, Any]]:
        """解析分支输出"""
        branches = []
        for line in branch_output.split('\n'):
            line = line.strip()
            if line:
                is_current = line.startswith('*')
                branch_name = line[1:].strip() if is_current else line
                branches.append({
                    'name': branch_name,
                    'is_current': is_current
                })
        return branches
    
    def _parse_commits(self, log_output: str) -> List[Dict[str, Any]]:
        """解析提交日志"""
        commits = []
        for line in log_output.split('\n'):
            line = line.strip()
            if line:
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1]
                    })
        return commits
    
    def _generate_branch_recommendations(self) -> List[str]:
        """生成分支建议"""
        return [
            '考虑使用Git Flow工作流来管理分支',
            '定期清理已合并的分支',
            '使用语义化的分支命名规范',
            '保持分支生命周期简短'
        ]
    
    def _assess_conflict_risk(self, diff_content: str) -> str:
        """评估冲突风险"""
        if len(diff_content) > 5000:
            return 'high'
        elif len(diff_content) > 1000:
            return 'medium'
        else:
            return 'low'
    
    def _generate_conflict_suggestions(self) -> List[str]:
        """生成冲突解决建议"""
        return [
            '在合并前先拉取远程更新',
            '使用git diff查看具体变更',
            '考虑使用git stash暂存当前变更',
            '合并后仔细测试代码'
        ]
    
    def _summarize_changes(self, diff_content: str) -> Dict[str, int]:
        """总结变更"""
        lines_added = diff_content.count('\n+')
        lines_removed = diff_content.count('\n-')
        return {
            'lines_added': lines_added,
            'lines_removed': lines_removed,
            'net_change': lines_added - lines_removed
        }
    
    def _generate_improvement_suggestions(self) -> List[str]:
        """生成改进建议"""
        return [
            '考虑添加代码注释',
            '确保遵循代码风格规范',
            '添加必要的单元测试',
            '检查是否有性能优化空间'
        ]
    
    def _record_operation(self, operation_type: str, details: Dict[str, Any]):
        """记录Git操作历史"""
        self.git_operations_history.append({
            'operation_type': operation_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        # 限制历史记录大小
        if len(self.git_operations_history) > self.max_history_size:
            self.git_operations_history = self.git_operations_history[-self.max_history_size:]

# 创建全局Git AI实例
git_ai = GitAI('git_ai_default')

if __name__ == '__main__':
    print("Git AI模块加载成功")
    print(f"Git AI实例: {git_ai.instance_id}")
    print(f"Git AI职责: {git_ai.responsibilities}")
