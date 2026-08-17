# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
问题解决流水线编排器
整合所有模块，执行完整的问题解决流程
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class IssueResolutionPipeline:
    """问题解决流水线编排器"""

    def __init__(self):
        self.pipeline_id = f"pipeline_{uuid.uuid4().hex[:8]}"
        self.stages = [
            'triage',
            'solution_search',
            'repair',
            'rollback_test',
            'reflection',
            'brain_feeding',
            'version_update',
            'git_commit'
        ]
        self.results = {}
        self._init_modules()

    def _init_modules(self):
        """初始化所有模块"""
        try:
            from .issue_manager import IssueManager
            from .solution_finder import SolutionFinder
            from .repair_coordinator import RepairCoordinator
            from .rollback_tester import RollbackTester
            from .reflection_engine import ReflectionEngine
            from .version_doc_manager import VersionDocManager
            
            self.issue_manager = IssueManager()
            self.solution_finder = SolutionFinder()
            self.repair_coordinator = RepairCoordinator()
            self.rollback_tester = RollbackTester()
            self.reflection_engine = ReflectionEngine()
            self.version_manager = VersionDocManager()
            
            logger.info("[IssueResolutionPipeline] 所有模块初始化完成")
        except Exception as e:
            logger.error(f"[IssueResolutionPipeline] 模块初始化失败: {e}")
            raise

    def run_full_pipeline(self, findings: List[Dict], severity_filter: str = None) -> Dict[str, Any]:
        """执行完整的问题解决流水线"""
        logger.info(f"[IssueResolutionPipeline] 开始执行完整流水线: {self.pipeline_id}")
        
        pipeline_result = {
            'pipeline_id': self.pipeline_id,
            'started_at': datetime.now().isoformat(),
            'stages': [],
            'summary': {}
        }
        
        try:
            if severity_filter:
                filtered_findings = [f for f in findings if f.get('severity') == severity_filter]
            else:
                filtered_findings = findings
            
            self.results['triage'] = self._stage_triage(filtered_findings)
            pipeline_result['stages'].append({'stage': 'triage', 'status': 'completed'})
            
            self.results['solution_search'] = self._stage_solution_search(self.results['triage']['issues'])
            pipeline_result['stages'].append({'stage': 'solution_search', 'status': 'completed'})
            
            self.results['repair'] = self._stage_repair(
                self.results['triage']['issues'], 
                self.results['solution_search']['solutions']
            )
            pipeline_result['stages'].append({'stage': 'repair', 'status': 'completed'})
            
            self.results['rollback_test'] = self._stage_rollback_test(self.results['repair']['repairs'])
            pipeline_result['stages'].append({'stage': 'rollback_test', 'status': 'completed'})
            
            self.results['reflection'] = self._stage_reflection(
                self.results['repair']['repairs'],
                self.results['triage']['issues'],
                self.results['solution_search']['solutions']
            )
            pipeline_result['stages'].append({'stage': 'reflection', 'status': 'completed'})
            
            self.results['brain_feeding'] = self._stage_brain_feeding()
            pipeline_result['stages'].append({'stage': 'brain_feeding', 'status': 'completed'})
            
            self.results['version_update'] = self._stage_version_update()
            pipeline_result['stages'].append({'stage': 'version_update', 'status': 'completed'})
            
            self.results['git_commit'] = self._stage_git_commit()
            pipeline_result['stages'].append({'stage': 'git_commit', 'status': 'completed'})
            
            pipeline_result['summary'] = self._generate_summary()
            pipeline_result['completed_at'] = datetime.now().isoformat()
            pipeline_result['success'] = True
            
            logger.info(f"[IssueResolutionPipeline] 流水线执行完成")
        except Exception as e:
            pipeline_result['success'] = False
            pipeline_result['error'] = str(e)
            pipeline_result['completed_at'] = datetime.now().isoformat()
            logger.error(f"[IssueResolutionPipeline] 流水线执行失败: {e}")
        
        return pipeline_result

    def _stage_triage(self, findings: List[Dict]) -> Dict[str, Any]:
        """问题分类阶段"""
        logger.info("[IssueResolutionPipeline] 阶段1: 问题分类")
        summary = self.issue_manager.load_findings(findings)
        return {
            'summary': summary,
            'issues': self.issue_manager.get_all_issues()
        }

    def _stage_solution_search(self, issues: List[Dict]) -> Dict[str, Any]:
        """解决方案搜索阶段"""
        logger.info(f"[IssueResolutionPipeline] 阶段2: 解决方案搜索 ({len(issues)}个问题)")
        solutions = self.solution_finder.find_solutions_batch(issues)
        return {
            'solutions': solutions,
            'count': len(solutions)
        }

    def _stage_repair(self, issues: List[Dict], solutions: List[Dict]) -> Dict[str, Any]:
        """修复执行阶段"""
        logger.info(f"[IssueResolutionPipeline] 阶段3: 修复执行")
        
        repairs = []
        repair_ids = []
        
        for issue, solution in zip(issues, solutions):
            if issue.get('severity') in ['critical', 'high']:
                repair = self.repair_coordinator.assign_repair(issue, solution)
                repairs.append(repair)
                repair_ids.append(repair['repair_id'])
        
        if repair_ids:
            results = self.repair_coordinator.execute_batch_repair(repair_ids)
        else:
            results = []
        
        return {
            'repairs': repairs,
            'results': results,
            'completed_count': len([r for r in results if r.get('success')])
        }

    def _stage_rollback_test(self, repairs: List[Dict]) -> Dict[str, Any]:
        """回滚测试阶段"""
        logger.info(f"[IssueResolutionPipeline] 阶段4: 回滚测试")
        
        test_results = []
        for repair in repairs:
            if repair.get('status') == 'completed':
                test = self.rollback_tester.run_rollback_test(repair['repair_id'])
                test_results.append(test)
        
        return {
            'test_results': test_results,
            'rolled_back_count': len([t for t in test_results if t.get('rollback_executed')])
        }

    def _stage_reflection(self, repairs: List[Dict], issues: List[Dict], solutions: List[Dict]) -> Dict[str, Any]:
        """反思复盘阶段"""
        logger.info(f"[IssueResolutionPipeline] 阶段5: 反思复盘")
        
        reflections = []
        for repair, issue, solution in zip(repairs, issues, solutions):
            if repair.get('status') == 'completed':
                reflection = self.reflection_engine.reflect_on_repair(repair, issue, solution)
                reflections.append(reflection)
        
        return {
            'reflections': reflections,
            'prevention_rules': self.reflection_engine.get_prevention_rules(),
            'recurring_issues': self.reflection_engine.get_recurring_issues()
        }

    def _stage_brain_feeding(self) -> Dict[str, Any]:
        """脑库投喂阶段"""
        logger.info("[IssueResolutionPipeline] 阶段6: 脑库投喂")
        return self.reflection_engine.feed_to_brain()

    def _stage_version_update(self) -> Dict[str, Any]:
        """版本更新阶段"""
        logger.info("[IssueResolutionPipeline] 阶段7: 版本更新")
        
        changes = []
        if 'repair' in self.results:
            completed = len(self.results['repair'].get('results', []))
            changes.append(f"修复了 {completed} 个安全问题")
        
        if 'reflection' in self.results:
            rules = len(self.results['reflection'].get('prevention_rules', []))
            changes.append(f"新增 {rules} 条预防规则")
        
        return self.version_manager.bump_version('patch', changes)

    def _stage_git_commit(self) -> Dict[str, Any]:
        """Git提交阶段"""
        logger.info("[IssueResolutionPipeline] 阶段8: Git提交")
        
        version = self.results.get('version_update', {})
        version_number = version.get('version_number', self.version_manager.get_current_version())
        
        return self.version_manager.auto_git_commit(f"chore: 自动提交 - 版本 {version_number}")

    def _generate_summary(self) -> Dict[str, Any]:
        """生成流水线摘要"""
        summary = {}
        
        if 'triage' in self.results:
            triage = self.results['triage']['summary']
            summary['total_issues'] = triage.get('total', 0)
            summary['issues_by_severity'] = triage.get('by_severity', {})
        
        if 'solution_search' in self.results:
            summary['solutions_found'] = self.results['solution_search'].get('count', 0)
        
        if 'repair' in self.results:
            summary['repairs_completed'] = self.results['repair'].get('completed_count', 0)
        
        if 'rollback_test' in self.results:
            summary['rollback_tests_run'] = len(self.results['rollback_test'].get('test_results', []))
            summary['rollbacks_executed'] = self.results['rollback_test'].get('rolled_back_count', 0)
        
        if 'reflection' in self.results:
            summary['reflections_count'] = len(self.results['reflection'].get('reflections', []))
            summary['prevention_rules'] = len(self.results['reflection'].get('prevention_rules', []))
        
        if 'brain_feeding' in self.results:
            summary['brain_feeding'] = self.results['brain_feeding']
        
        if 'version_update' in self.results:
            summary['new_version'] = self.results['version_update'].get('version_number')
        
        if 'git_commit' in self.results:
            summary['git_commit'] = self.results['git_commit'].get('commit')
        
        return summary

    def run_stage(self, stage_name: str, **kwargs) -> Dict[str, Any]:
        """单独运行某个阶段"""
        stage_methods = {
            'triage': self._stage_triage,
            'solution_search': self._stage_solution_search,
            'repair': self._stage_repair,
            'rollback_test': self._stage_rollback_test,
            'reflection': self._stage_reflection,
            'brain_feeding': self._stage_brain_feeding,
            'version_update': self._stage_version_update,
            'git_commit': self._stage_git_commit
        }
        
        if stage_name not in stage_methods:
            return {'success': False, 'error': f'未知阶段: {stage_name}'}
        
        try:
            result = stage_methods[stage_name](**kwargs)
            self.results[stage_name] = result
            return {'success': True, 'stage': stage_name, 'result': result}
        except Exception as e:
            return {'success': False, 'stage': stage_name, 'error': str(e)}

    def get_results(self) -> Dict[str, Any]:
        """获取所有阶段结果"""
        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """获取流水线摘要"""
        return self._generate_summary()