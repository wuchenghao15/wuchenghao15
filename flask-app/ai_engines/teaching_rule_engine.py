#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教学规则引擎系统
包含教学大纲、备课、教案的智能规则管理
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class TeachingRule:
    """教学规则"""
    
    def __init__(self, rule_id: str, rule_type: str, name: str, description: str, 
                 condition: Callable, action: Callable, priority: int = 5,
                 metadata: Optional[Dict[str, Any]] = None):
        self.id = rule_id
        self.type = rule_type  # 'syllabus', 'preparation', 'plan', 'assessment'
        self.name = name
        self.description = description
        self.condition = condition
        self.action = action
        self.priority = priority
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.enabled = True
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """评估规则条件"""
        if not self.enabled:
            return False
        try:
            return self.condition(context)
        except Exception as e:
            logger.error(f"规则评估失败 {self.id}: {e}")
            return False
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行规则动作"""
        try:
            return self.action(context)
        except Exception as e:
            logger.error(f"规则执行失败 {self.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'description': self.description,
            'priority': self.priority,
            'enabled': self.enabled,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class TeachingRuleEngine:
    """教学规则引擎"""
    
    def __init__(self):
        self.rules: Dict[str, TeachingRule] = {}
        self.rule_history: List[Dict[str, Any]] = []
        self._init_default_rules()
        logger.info("教学规则引擎初始化完成")
    
    def _init_default_rules(self):
        """初始化默认规则"""
        rules = [
            # 大纲规则
            TeachingRule(
                'syllabus_objectives_check', 'syllabus',
                '教学目标完整性检查',
                '检查教学目标是否包含知识、技能、情感态度三个维度',
                lambda ctx: len(ctx.get('objectives', [])) > 0 and len(ctx.get('objectives', [])) < 5,
                lambda ctx: {'suggestion': '建议补充教学目标，覆盖知识、技能、情感态度三个维度'},
                priority=8
            ),
            TeachingRule(
                'syllabus_knowledge_points_check', 'syllabus',
                '知识点密度检查',
                '检查每课时知识点数量是否合理',
                lambda ctx: ctx.get('teaching_hours', 0) > 0 and len(ctx.get('knowledge_points', [])) / ctx.get('teaching_hours', 1) > 5,
                lambda ctx: {'suggestion': '建议减少课时内知识点数量，确保教学质量'},
                priority=7
            ),
            TeachingRule(
                'syllabus_difficulty_check', 'syllabus',
                '难度匹配检查',
                '检查内容难度与年级是否匹配',
                lambda ctx: ctx.get('difficulty_level') == 'high' and ctx.get('grade') in ['小学1年级', '小学2年级'],
                lambda ctx: {'suggestion': '建议调整难度，小学低年级不宜设置过高难度'},
                priority=9
            ),
            
            # 备课规则
            TeachingRule(
                'preparation_time_allocation', 'preparation',
                '时间分配合理性检查',
                '检查教学时间分配是否合理',
                lambda ctx: len(ctx.get('time_allocation', [])) > 0,
                lambda ctx: {'suggestion': '建议细化教学时间分配，确保各环节时间合理'},
                priority=6
            ),
            TeachingRule(
                'preparation_key_points', 'preparation',
                '重点突出检查',
                '检查是否有明确的教学重点',
                lambda ctx: len(ctx.get('key_points', [])) == 0,
                lambda ctx: {'suggestion': '建议明确教学重点，至少列出2-3个核心知识点'},
                priority=8
            ),
            TeachingRule(
                'preparation_difficult_points', 'preparation',
                '难点突破检查',
                '检查是否有明确的教学难点及解决方案',
                lambda ctx: len(ctx.get('difficult_points', [])) > 0 and 'teaching_process' not in ctx,
                lambda ctx: {'suggestion': '建议在教学过程中明确难点突破的方法'},
                priority=7
            ),
            
            # 教案规则
            TeachingRule(
                'plan_objectives_complete', 'plan',
                '教学目标完整性检查',
                '检查教案的三维教学目标',
                lambda ctx: len(ctx.get('teaching_objectives', [])) == 0 or len(ctx.get('knowledge_skills', [])) == 0,
                lambda ctx: {'suggestion': '建议完善教学目标，包含知识技能、过程方法、情感态度三个维度'},
                priority=9
            ),
            TeachingRule(
                'plan_activity_design', 'plan',
                '活动设计检查',
                '检查是否有充足的教学活动设计',
                lambda ctx: len(ctx.get('activity_design', [])) < 2,
                lambda ctx: {'suggestion': '建议增加教学活动设计，提高课堂互动性'},
                priority=6
            ),
            TeachingRule(
                'plan_question_design', 'plan',
                '问题设计检查',
                '检查问题设计是否分层',
                lambda ctx: len(ctx.get('question_design', [])) < 3,
                lambda ctx: {'suggestion': '建议设计不同层次的问题，包括基础、理解、应用、拓展'},
                priority=7
            ),
            TeachingRule(
                'plan_reflection', 'plan',
                '课后反思检查',
                '检查是否有课后反思设计',
                lambda ctx: not ctx.get('after_class_reflection'),
                lambda ctx: {'suggestion': '建议添加课后反思部分，便于教学改进'},
                priority=5
            ),
            
            # 评估规则
            TeachingRule(
                'assessment_aligned', 'assessment',
                '评估一致性检查',
                '检查评估与教学目标是否一致',
                lambda ctx: 'assessment_design' in ctx and len(ctx.get('teaching_objectives', [])) > 0,
                lambda ctx: {'suggestion': '确保评估内容与教学目标一致'},
                priority=8
            ),
            TeachingRule(
                'assessment_diverse', 'assessment',
                '评估方式多样性',
                '检查评估方式是否多样化',
                lambda ctx: len(ctx.get('assessment_methods', [])) < 2,
                lambda ctx: {'suggestion': '建议采用多样化的评估方式，如口头、书面、实践等'},
                priority=6
            )
        ]
        
        for rule in rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: TeachingRule) -> bool:
        """添加规则"""
        if rule.id in self.rules:
            logger.warning(f"规则已存在: {rule.id}")
            return False
        
        self.rules[rule.id] = rule
        logger.info(f"添加规则: {rule.id}")
        return True
    
    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"移除规则: {rule_id}")
            return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[TeachingRule]:
        """获取规则"""
        return self.rules.get(rule_id)
    
    def get_rules_by_type(self, rule_type: str) -> List[TeachingRule]:
        """按类型获取规则"""
        return [r for r in self.rules.values() if r.type == rule_type]
    
    def evaluate_all(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """评估所有规则"""
        results = []
        
        # 按优先级排序
        sorted_rules = sorted(self.rules.values(), key=lambda r: -r.priority)
        
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            
            matched = rule.evaluate(context)
            result = {
                'rule_id': rule.id,
                'rule_name': rule.name,
                'rule_type': rule.type,
                'priority': rule.priority,
                'matched': matched,
                'evaluated_at': datetime.now().isoformat()
            }
            
            if matched:
                action_result = rule.execute(context)
                result['action_result'] = action_result
            
            results.append(result)
            
            # 记录到历史
            self.rule_history.append({
                'rule_id': rule.id,
                'context_summary': {k: v for k, v in list(context.items())[:5]},
                'matched': matched,
                'timestamp': datetime.now().isoformat()
            })
        
        return results
    
    def evaluate_type(self, context: Dict[str, Any], rule_type: str) -> List[Dict[str, Any]]:
        """评估指定类型的规则"""
        type_rules = [r for r in self.rules.values() if r.type == rule_type and r.enabled]
        type_rules.sort(key=lambda r: -r.priority)
        
        results = []
        for rule in type_rules:
            matched = rule.evaluate(context)
            result = {
                'rule_id': rule.id,
                'rule_name': rule.name,
                'matched': matched
            }
            
            if matched:
                action_result = rule.execute(context)
                result['action_result'] = action_result
            
            results.append(result)
        
        return results
    
    def get_suggestions(self, context: Dict[str, Any], rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取智能建议"""
        if rule_type:
            results = self.evaluate_type(context, rule_type)
        else:
            results = self.evaluate_all(context)
        
        suggestions = []
        for r in results:
            if r.get('matched') and 'action_result' in r:
                suggestions.append({
                    'rule_id': r['rule_id'],
                    'rule_name': r['rule_name'],
                    'suggestion': r['action_result'].get('suggestion', '')
                })
        
        return suggestions
    
    def enable_rule(self, rule_id: str) -> bool:
        """启用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            logger.info(f"启用规则: {rule_id}")
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            logger.info(f"禁用规则: {rule_id}")
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取规则统计"""
        type_stats = {}
        for rule in self.rules.values():
            rule_type = rule.type
            if rule_type not in type_stats:
                type_stats[rule_type] = {'total': 0, 'enabled': 0}
            type_stats[rule_type]['total'] += 1
            if rule.enabled:
                type_stats[rule_type]['enabled'] += 1
        
        return {
            'total_rules': len(self.rules),
            'enabled_rules': len([r for r in self.rules.values() if r.enabled]),
            'type_statistics': type_stats,
            'history_count': len(self.rule_history)
        }
    
    def export_rules(self, filepath: str) -> bool:
        """导出规则"""
        try:
            rules_data = {rule_id: rule.to_dict() for rule_id, rule in self.rules.items()}
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, ensure_ascii=False, indent=2)
            logger.info(f"规则已导出到: {filepath}")
            return True
        except Exception as e:
            logger.error(f"规则导出失败: {e}")
            return False


# 全局规则引擎实例
teaching_rule_engine = TeachingRuleEngine()


class TeachingContentValidator:
    """教学内容验证器"""
    
    def __init__(self):
        self.engine = teaching_rule_engine
        logger.info("教学内容验证器初始化完成")
    
    def validate_syllabus(self, syllabus_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证教学大纲"""
        context = {
            'type': 'syllabus',
            'data': syllabus_data,
            'objectives': syllabus_data.get('objectives', []),
            'knowledge_points': syllabus_data.get('knowledge_points', []),
            'teaching_hours': syllabus_data.get('teaching_hours', 0),
            'difficulty_level': syllabus_data.get('difficulty_level', 'medium'),
            'grade': syllabus_data.get('grade', ''),
            'teaching_methods': syllabus_data.get('teaching_methods', [])
        }
        
        suggestions = self.engine.get_suggestions(context, 'syllabus')
        results = self.engine.evaluate_type(context, 'syllabus')
        
        return {
            'valid': len([r for r in results if r['matched']]) == 0,
            'suggestions': suggestions,
            'results': results
        }
    
    def validate_preparation(self, preparation_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证教学备课"""
        context = {
            'type': 'preparation',
            'data': preparation_data,
            'key_points': preparation_data.get('key_points', []),
            'difficult_points': preparation_data.get('difficult_points', []),
            'time_allocation': preparation_data.get('time_allocation', []),
            'teaching_process': preparation_data.get('teaching_process', '')
        }
        
        suggestions = self.engine.get_suggestions(context, 'preparation')
        results = self.engine.evaluate_type(context, 'preparation')
        
        return {
            'valid': len([r for r in results if r['matched']]) == 0,
            'suggestions': suggestions,
            'results': results
        }
    
    def validate_plan(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证教案"""
        context = {
            'type': 'plan',
            'data': plan_data,
            'teaching_objectives': plan_data.get('teaching_objectives', []),
            'knowledge_skills': plan_data.get('knowledge_skills', []),
            'activity_design': plan_data.get('activity_design', []),
            'question_design': plan_data.get('question_design', []),
            'after_class_reflection': plan_data.get('after_class_reflection', '')
        }
        
        suggestions = self.engine.get_suggestions(context, 'plan')
        results = self.engine.evaluate_type(context, 'plan')
        
        return {
            'valid': len([r for r in results if r['matched']]) == 0,
            'suggestions': suggestions,
            'results': results
        }


# 全局验证器实例
teaching_content_validator = TeachingContentValidator()


if __name__ == "__main__":
    print("教学规则引擎系统")
    print(f"规则统计: {json.dumps(teaching_rule_engine.get_statistics(), indent=2, ensure_ascii=False)}")
    
    # 测试验证
    test_syllabus = {
        'objectives': ['了解概念'],
        'knowledge_points': ['点1', '点2', '点3', '点4', '点5', '点6'],
        'teaching_hours': 1,
        'difficulty_level': 'high',
        'grade': '小学1年级'
    }
    
    print("\n测试大纲验证:")
    validation = teaching_content_validator.validate_syllabus(test_syllabus)
    print(json.dumps(validation, indent=2, ensure_ascii=False))
