#!/usr/bin/env python3
import os
import json
import sqlite3
import threading
import hashlib
import random
from datetime import datetime
from collections import defaultdict

class AIIntelligentDecision:
    DECISION_TYPES = ['learning_path', 'resource_recommendation', 'intervention', 'goal_setting', 'skill_development']
    DECISION_PRIORITY = ['low', 'medium', 'high', 'critical']
    DECISION_STATUS = ['pending', 'analyzing', 'completed', 'executed', 'rejected']
    
    def __init__(self):
        self.decision_cache = {}
        self._lock = threading.Lock()
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('ai_decision.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decision_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL UNIQUE,
                    decision_type TEXT NOT NULL,
                    user_id TEXT,
                    input_data TEXT,
                    status TEXT DEFAULT 'pending',
                    priority TEXT DEFAULT 'medium',
                    confidence REAL DEFAULT 0.0,
                    decision_result TEXT,
                    reasoning_chain TEXT,
                    execution_plan TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    executed_at TEXT,
                    duration REAL DEFAULT 0.0,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decision_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    step_number INTEGER NOT NULL,
                    step_name TEXT NOT NULL,
                    module_used TEXT,
                    input_data TEXT,
                    output_data TEXT,
                    confidence REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decision_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL UNIQUE,
                    rule_name TEXT NOT NULL,
                    decision_type TEXT,
                    conditions TEXT,
                    actions TEXT,
                    priority INTEGER DEFAULT 1,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decision_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL UNIQUE,
                    task_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target_system TEXT,
                    parameters TEXT,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Intelligent Decision] 创建表失败: {e}")
    
    def _generate_id(self, prefix):
        return prefix + '_' + hashlib.md5((str(datetime.now().timestamp()) + str(random.random())).encode()).hexdigest(
        )[:16]
    
    def add_decision_rule(self, rule_name, decision_type, conditions, actions, priority=1):
        rule_id = self._generate_id('rule')
        
        try:
            conn = sqlite3.connect('ai_decision.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO decision_rules 
                (rule_id, rule_name, decision_type, conditions, actions, priority, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (rule_id, rule_name, decision_type, json.dumps(conditions), json.dumps(actions), priority, 1))
            conn.commit()
            conn.close()
            
            return {'success': True, 'rule_id': rule_id}
        except Exception as e:
            logger.info(f"[AI Intelligent Decision] 添加决策规则失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_decision_rules(self, decision_type=None):
        try:
            conn = sqlite3.connect('ai_decision.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if decision_type:
                cursor.execute(
                'SELECT * FROM decision_rules WHERE decision_type = ? AND enabled = 1 ORDER BY priority DESC',
                (decision_type,))
            else:
                cursor.execute('SELECT * FROM decision_rules WHERE enabled = 1 ORDER BY priority DESC')
            
            rules = []
            for row in cursor.fetchall():
                rule = dict(row)
                rule['conditions'] = json.loads(rule.get('conditions', '[]'))
                rule['actions'] = json.loads(rule.get('actions', '[]'))
                rules.append(rule)
            
            conn.close()
            return rules
        except Exception as e:
            logger.info(f"[AI Intelligent Decision] 获取决策规则失败: {e}")
            return []
    
    def analyze_user_context(self, user_id):
        context = {
            'user_id': user_id,
            'learning_profile': None,
            'knowledge_gaps': [],
            'recent_interactions': [],
            'current_paths': [],
            'recommendations': []
        }
        
        try:
            from app.ai.ai_adaptive_learning import ai_adaptive_learning
            profile = ai_adaptive_learning.get_or_create_profile(user_id)
            if profile:
                context['learning_profile'] = profile
            
            gaps_result = ai_adaptive_learning.detect_knowledge_gaps(user_id)
            if gaps_result.get('success'):
                context['knowledge_gaps'] = gaps_result.get('gaps', [])
            
            paths = ai_adaptive_learning.get_user_paths(user_id)
            context['current_paths'] = paths
            
            recs = ai_adaptive_learning.generate_recommendations(user_id)
            if recs.get('success'):
                context['recommendations'] = recs.get('recommendations', [])
        except Exception as e:
            logger.info(f"[AI Intelligent Decision] 分析用户上下文失败: {e}")
        
        return context
    
    def generate_decision(self, decision_type, user_id=None, input_data=None):
        task_id = self._generate_id('decision')
        start_time = datetime.now()
        
        steps = []
        result = None
        confidence = 0.0
        
        try:
            conn = sqlite3.connect('ai_decision.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO decision_tasks 
                (task_id, decision_type, user_id, input_data, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (task_id, decision_type, user_id, json.dumps(input_data or {}), 'analyzing'))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Intelligent Decision] 创建决策任务失败: {e}")
        
        steps.append({
            'step': 1,
            'name': 'context_analysis',
            'module': 'adaptive_learning',
            'description': '分析用户上下文信息'
        })
        
        context = self.analyze_user_context(user_id) if user_id else {}
        
        steps.append({
            'step': 2,
            'name': 'rule_matching',
            'module': 'decision_rules',
            'description': '匹配决策规则',
            'data': f"发现 {len(context.get('knowledge_gaps', []))} 个知识漏洞"
        })
        
        rules = self.get_decision_rules(decision_type)
        
        steps.append({
            'step': 3,
            'name': 'reasoning_integration',
            'module': 'cognitive_reasoning',
            'description': '整合认知推理'
        })
        
        reasoning_result = None
        try:
            from app.ai.ai_cognitive_reasoning import ai_cognitive_reasoning
            
            if decision_type == 'learning_path':
                observations = []
                if context.get('learning_profile'):
                    observations.append(f"学习风格: {context['learning_profile'].get('learning_style', 'unknown')}")
                for gap in context.get('knowledge_gaps', []):
                    observations.append(f"知识漏洞: {gap.get('topic', '')}")
                
                if observations:
                    reasoning_result = ai_cognitive_reasoning.inductive_reasoning(
                        observations, 
                        f"为用户{user_id}生成最佳学习路径"
                    )
            elif decision_type == 'intervention':
                evidence = []
                for gap in context.get('knowledge_gaps', []):
                    if gap.get('gap_level', 0) >= 3:
                        evidence.append(f"高优先级漏洞: {gap.get('topic', '')}")
                
                if evidence:
                    reasoning_result = ai_cognitive_reasoning.abductive_reasoning(
                        evidence,
                        f"为用户{user_id}制定干预策略"
                    )
        except Exception as e:
            logger.info(f"[AI Intelligent Decision] 认知推理调用失败: {e}")
        
        steps.append({
            'step': 4,
            'name': 'decision_synthesis',
            'module': 'decision_engine',
            'description': '综合生成决策'
        })
        
        confidence = 0.6 + len(rules) * 0.1
        confidence = min(0.95, confidence)
        
        decision_content = self._synthesize_decision(decision_type, context, reasoning_result, rules)
        execution_plan = self._generate_execution_plan(decision_type, decision_content)
        
        result = {
            'decision_type': decision_type,
            'user_id': user_id,
            'confidence': round(confidence, 2),
            'content': decision_content,
            'execution_plan': execution_plan,
            'context_summary': {
                'gaps_count': len(context.get('knowledge_gaps', [])),
                'paths_count': len(context.get('current_paths', [])),
                'learning_style': context.get('learning_profile', {}).get('learning_style')
            },
            'reasoning_used': reasoning_result is not None,
            'rules_applied': len(rules)
        }
        
        try:
            conn = sqlite3.connect('ai_decision.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE decision_tasks 
                SET status = ?, confidence = ?, decision_result = ?, 
                    reasoning_chain = ?, execution_plan = ?, completed_at = ?, duration = ?
                WHERE task_id = ?
            ''', (
                'completed', confidence, json.dumps(result['content']),
                json.dumps(reasoning_result) if reasoning_result else '{}',
                json.dumps(execution_plan),
                datetime.now().isoformat(),
                (datetime.now() - start_time).total_seconds(),
                task_id
            ))
            conn.commit()
            
            for step in steps:
                cursor.execute('''
                    INSERT INTO decision_history 
                    (task_id, step_number, step_name, module_used, input_data, output_data, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_id, step['step'], step['name'],
                    step['module'],
                    json.dumps(step.get('data', '')),
                    json.dumps(step.get('result', '')),
                    confidence
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Intelligent Decision] 保存决策结果失败: {e}")
        
        self.decision_cache[task_id] = result
        
        return {
            'success': True,
            'task_id': task_id,
            'decision_type': decision_type,
            'result': result,
            'confidence': round(confidence, 2),
            'steps': steps,
            'duration': round((datetime.now() - start_time).total_seconds(), 2)
        }
    
    def _synthesize_decision(self, decision_type, context, reasoning_result, rules):
        decisions = {
            'learning_path': {
                'recommendation': '基于您的学习情况，建议调整学习路径',
                'path_adjustments': [],
                'priority_topics': [],
                'estimated_time': 0
            },
            'resource_recommendation': {
                'resources': [],
                'resource_types': [],
                'personalization_score': 0.0
            },
            'intervention': {
                'intervention_type': 'normal',
                'actions': [],
                'urgency': 'low',
                'expected_outcome': ''
            },
            'goal_setting': {
                'short_term_goals': [],
                'long_term_goals': [],
                'milestones': [],
                'success_criteria': []
            },
            'skill_development': {
                'skill_gaps': [],
                'development_plan': [],
                'practice_recommendations': [],
                'progress_metrics': []
            }
        }
        
        base_decision = decisions.get(decision_type, {})
        
        if decision_type == 'learning_path':
            gaps = context.get('knowledge_gaps', [])[:3]
            for gap in gaps:
                base_decision['priority_topics'].append(gap.get('topic', ''))
                base_decision['path_adjustments'].append({
                    'topic': gap.get('topic', ''),
                    'gap_level': gap.get('gap_level', 1),
                    'suggested_action': gap.get('suggested_actions', [])[0] if gap.get('suggested_actions') else ''
                })
            base_decision['estimated_time'] = len(gaps) * 2
        
        elif decision_type == 'intervention':
            high_priority_gaps = [g for g in context.get('knowledge_gaps', []) if g.get('gap_level', 0) >= 3]
            if high_priority_gaps:
                base_decision['intervention_type'] = 'targeted'
                base_decision['urgency'] = 'high'
                base_decision['actions'] = [
                    f"针对漏洞 '{g.get('topic', '')}' 进行专项练习"
                    for g in high_priority_gaps
                ]
                base_decision['expected_outcome'] = f"预计修复 {len(high_priority_gaps)} 个高优先级知识漏洞"
        
        elif decision_type == 'goal_setting':
            base_decision['short_term_goals'] = ['完成当前学习路径', '修复1-2个知识漏洞']
            base_decision['long_term_goals'] = ['掌握所有核心知识点', '提升整体知识水平']
            base_decision['milestones'] = ['完成50%学习进度', '完成80%学习进度', '全部完成']
        
        elif decision_type == 'skill_development':
            base_decision['skill_gaps'] = ['推理能力', '问题解决能力']
            base_decision['development_plan'] = ['每天练习推理题', '每周进行综合评估']
        
        return base_decision
    
    def _generate_execution_plan(self, decision_type, decision_content):
        plan = {
            'steps': [],
            'estimated_duration': 0,
            'dependencies': [],
            'success_criteria': ''
        }
        
        if decision_type == 'learning_path':
            plan['steps'] = [
                {'step': 1, 'action': '评估当前学习状态', 'duration': 5},
                {'step': 2, 'action': '调整学习路径优先级', 'duration': 10},
                {'step': 3, 'action': '生成个性化学习计划', 'duration': 15},
                {'step': 4, 'action': '推送学习建议', 'duration': 5}
            ]
            plan['estimated_duration'] = 35
            plan['success_criteria'] = '学习路径更新完成并通知用户'
        
        elif decision_type == 'intervention':
            plan['steps'] = [
                {'step': 1, 'action': '识别高危知识漏洞', 'duration': 5},
                {'step': 2, 'action': '生成干预方案', 'duration': 10},
                {'step': 3, 'action': '执行干预措施', 'duration': 20},
                {'step': 4, 'action': '跟踪干预效果', 'duration': 10}
            ]
            plan['estimated_duration'] = 45
            plan['success_criteria'] = '知识漏洞修复率达到80%以上'
        
        elif decision_type == 'goal_setting':
            plan['steps'] = [
                {'step': 1, 'action': '分析学习数据', 'duration': 10},
                {'step': 2, 'action': '制定短期和长期目标', 'duration': 15},
                {'step': 3, 'action': '设置里程碑', 'duration': 10},
                {'step': 4, 'action': '生成目标跟踪计划', 'duration': 10}
            ]
            plan['estimated_duration'] = 45
            plan['success_criteria'] = '目标设定完成并开始跟踪'
        
        elif decision_type == 'skill_development':
            plan['steps'] = [
                {'step': 1, 'action': '评估技能水平', 'duration': 10},
                {'step': 2, 'action': '制定技能提升计划', 'duration': 15},
                {'step': 3, 'action': '推荐练习资源', 'duration': 10},
                {'step': 4, 'action': '建立评估机制', 'duration': 10}
            ]
            plan['estimated_duration'] = 45
            plan['success_criteria'] = '技能提升计划开始执行'
        
        elif decision_type == 'resource_recommendation':
            plan['steps'] = [
                {'step': 1, 'action': '分析用户学习偏好', 'duration': 5},
                {'step': 2, 'action': '匹配资源库', 'duration': 10},
                {'step': 3, 'action': '生成推荐列表', 'duration': 10},
                {'step': 4, 'action': '推送推荐结果', 'duration': 5}
            ]
            plan['estimated_duration'] = 30
            plan['success_criteria'] = '推荐资源推送完成'
        
        return plan
    
    def execute_decision(self, task_id):
        try:
            conn = sqlite3.connect('ai_decision.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM decision_tasks WHERE task_id = ?', (task_id,))
            task = cursor.fetchone()
            
            if not task:
                conn.close()
                return {'success': False, 'error': '决策任务不存在'}
            
            if task['status'] == 'executed':
                conn.close()
                return {'success': False, 'error': '决策已执行'}
            
            decision_type = task['decision_type']
            execution_plan = json.loads(task.get('execution_plan', '{}'))
            
            executions = []
            for step in execution_plan.get('steps', []):
                exec_id = self._generate_id('exec')
                cursor.execute('''
                    INSERT INTO decision_executions 
                    (execution_id, task_id, action, target_system, parameters, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (exec_id, task_id, step['action'], 'learning_system', json.dumps(step), 'completed'))
                
                executions.append({
                    'execution_id': exec_id,
                    'action': step['action'],
                    'status': 'completed'
                })
            
            cursor.execute('''
                UPDATE decision_tasks 
                SET status = ?, executed_at = ?
                WHERE task_id = ?
            ''', ('executed', datetime.now().isoformat(), task_id))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'task_id': task_id,
                'decision_type': decision_type,
                'executions': executions,
                'message': '决策执行完成'
            }
        except Exception as e:
            logger.info(f"[AI Intelligent Decision] 执行决策失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_decision_task(self, task_id):
        try:
            conn = sqlite3.connect('ai_decision.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM decision_tasks WHERE task_id = ?', (task_id,))
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                result['input_data'] = json.loads(result.get('input_data', '{}'))
                result['decision_result'] = json.loads(result.get('decision_result', '{}'))
                result['reasoning_chain'] = json.loads(result.get('reasoning_chain', '{}'))
                result['execution_plan'] = json.loads(result.get('execution_plan', '{}'))
                return result
            
            conn.close()
            return None
        except Exception as e:
            logger.info(f"[AI Intelligent Decision] 获取决策任务失败: {e}")
            return None
    
    def list_decision_tasks(self, decision_type=None, user_id=None, limit=20):
        try:
            conn = sqlite3.connect('ai_decision.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            if decision_type:
                conditions.append('decision_type = ?')
                params.append(decision_type)
            
            if user_id:
                conditions.append('user_id = ?')
                params.append(user_id)
            
            params.append(limit)
            
            query = 'SELECT * FROM decision_tasks'
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            query += ' ORDER BY created_at DESC LIMIT ?'
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                task = dict(row)
                task['decision_result'] = json.loads(task.get('decision_result', '{}'))
                results.append(task)
            
            conn.close()
            return results
        except Exception as e:
            logger.info(f"[AI Intelligent Decision] 列出决策任务失败: {e}")
            return []
    
    def get_decision_statistics(self):
        try:
            conn = sqlite3.connect('ai_decision.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM decision_tasks')
            total_tasks = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM decision_tasks WHERE status = ?', ('completed',))
            completed_tasks = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM decision_tasks WHERE status = ?', ('executed',))
            executed_tasks = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM decision_rules')
            rule_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(confidence) FROM decision_tasks WHERE status = ?', ('completed',))
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            cursor.execute('''
                SELECT decision_type, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM decision_tasks WHERE status = 'completed'
                GROUP BY decision_type
            ''')
            type_stats = []
            for row in cursor.fetchall():
                type_stats.append({
                    'decision_type': row[0],
                    'count': row[1],
                    'avg_confidence': row[2] or 0.0
                })
            
            conn.close()
            
            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'executed_tasks': executed_tasks,
                'execution_rate': round(executed_tasks / completed_tasks * 100, 2) if completed_tasks > 0 else 0.0,
                'rule_count': rule_count,
                'avg_confidence': round(avg_confidence, 2),
                'type_statistics': type_stats
            }
        except Exception as e:
            logger.info(f"[AI Intelligent Decision] 获取统计信息失败: {e}")
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'executed_tasks': 0,
                'execution_rate': 0.0,
                'rule_count': 0,
                'avg_confidence': 0.0,
                'type_statistics': []
            }

ai_intelligent_decision = AIIntelligentDecision()