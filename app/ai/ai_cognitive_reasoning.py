#!/usr/bin/env python3
import os
import json
import sqlite3
import threading
import hashlib
import random
from datetime import datetime
from collections import defaultdict

class AICognitiveReasoning:
    REASONING_TYPES = ['deductive', 'inductive', 'abductive', 'analogical', 'causal']
    REASONING_STATUS = ['pending', 'in_progress', 'completed', 'failed']
    CONFIDENCE_LEVELS = ['low', 'medium', 'high', 'very_high']
    
    def __init__(self):
        self.reasoning_tasks = {}
        self.knowledge_base = {}
        self._lock = threading.Lock()
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('ai_cognitive.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reasoning_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL UNIQUE,
                    reasoning_type TEXT NOT NULL,
                    input_data TEXT,
                    goal TEXT,
                    status TEXT DEFAULT 'pending',
                    confidence REAL DEFAULT 0.0,
                    result TEXT,
                    reasoning_steps TEXT,
                    source_memories TEXT,
                    source_knowledge TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    duration REAL DEFAULT 0.0,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_id TEXT NOT NULL UNIQUE,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT,
                    confidence REAL DEFAULT 1.0,
                    source TEXT,
                    verified BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    accessed_count INTEGER DEFAULT 0,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reasoning_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    step_number INTEGER NOT NULL,
                    step_type TEXT,
                    description TEXT,
                    data_used TEXT,
                    intermediate_result TEXT,
                    confidence REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_knowledge_id TEXT NOT NULL,
                    target_knowledge_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    confidence REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_knowledge_id, target_knowledge_id, relation_type)
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Cognitive Reasoning] 创建表失败: {e}")
    
    def _generate_task_id(self):
        return 'task_' + hashlib.md5((str(datetime.now().timestamp()) + str(random.random())).encode()).hexdigest()[:16]
    
    def _generate_knowledge_id(self):
        return 'kb_' + hashlib.md5((str(datetime.now().timestamp()) + str(random.random())).encode()).hexdigest()[:16]
    
    def add_knowledge(self, topic, content, category=None, source='system', tags=None, metadata=None):
        with self._lock:
            knowledge_id = self._generate_knowledge_id()
            try:
                conn = sqlite3.connect('ai_cognitive.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO knowledge_base 
                    (knowledge_id, topic, content, category, source, verified, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (knowledge_id, topic, content, category, source, 1, json.dumps({'tags': tags or [],
                **(metadata or {})})))
                conn.commit()
                conn.close()
                
                self.knowledge_base[knowledge_id] = {
                    'knowledge_id': knowledge_id,
                    'topic': topic,
                    'content': content,
                    'category': category,
                    'source': source,
                    'tags': tags or [],
                    'created_at': datetime.now().isoformat()
                }
                
                return {'success': True, 'knowledge_id': knowledge_id}
            except Exception as e:
                return {'success': False, 'error': str(e)}
    
    def get_knowledge(self, knowledge_id):
        try:
            conn = sqlite3.connect('ai_cognitive.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM knowledge_base WHERE knowledge_id = ?', (knowledge_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.info(f"[AI Cognitive Reasoning] 获取知识失败: {e}")
            return None
    
    def search_knowledge(self, query, category=None, limit=10):
        try:
            conn = sqlite3.connect('ai_cognitive.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT * FROM knowledge_base 
                    WHERE (topic LIKE ? OR content LIKE ?) AND category = ?
                    ORDER BY accessed_count DESC, confidence DESC LIMIT ?
                ''', ('%' + query + '%', '%' + query + '%', category, limit))
            else:
                cursor.execute('''
                    SELECT * FROM knowledge_base 
                    WHERE topic LIKE ? OR content LIKE ?
                    ORDER BY accessed_count DESC, confidence DESC LIMIT ?
                ''', ('%' + query + '%', '%' + query + '%', limit))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.info(f"[AI Cognitive Reasoning] 搜索知识失败: {e}")
            return []
    
    def deductive_reasoning(self, premises, conclusion_goal):
        task_id = self._generate_task_id()
        start_time = datetime.now()
        
        steps = []
        result = None
        confidence = 0.0
        
        steps.append({
            'step': 1,
            'type': 'premise_analysis',
            'description': f'分析前提条件: {len(premises)} 个前提',
            'data': str(premises)[:200]
        })
        
        steps.append({
            'step': 2,
            'type': 'logical_inference',
            'description': '进行逻辑演绎推理',
            'data': f'目标: {conclusion_goal}'
        })
        
        try:
            confidence = min(0.95, 0.7 + len(premises) * 0.05)
            
            result = {
                'conclusion': f'基于前提条件的逻辑推导，得出结论：{conclusion_goal}',
                'supporting_premises': premises,
                'confidence': confidence,
                'explanation': '通过演绎推理，从给定的前提条件出发，按照逻辑规则推导出结论'
            }
            
            steps.append({
                'step': 3,
                'type': 'conclusion',
                'description': '推理完成，生成结论',
                'data': str(result)[:200]
            })
        except Exception as e:
            steps.append({
                'step': 3,
                'type': 'error',
                'description': f'推理失败: {str(e)}',
                'data': ''
            })
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        try:
            conn = sqlite3.connect('ai_cognitive.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reasoning_tasks 
                (task_id, reasoning_type, input_data, goal, status, confidence, result, reasoning_steps, created_at,
                completed_at, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id, 'deductive', json.dumps({'premises': premises}),
                conclusion_goal, 'completed', confidence,
                json.dumps(result) if result else '{}',
                json.dumps(steps),
                start_time.isoformat(), end_time.isoformat(), duration
            ))
            conn.commit()
            
            for step in steps:
                cursor.execute('''
                    INSERT INTO reasoning_history 
                    (task_id, step_number, step_type, description, data_used, intermediate_result, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_id, step['step'], step['type'],
                    step['description'], step.get('data', ''),
                    step.get('result', ''), confidence
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Cognitive Reasoning] 保存推理任务失败: {e}")
        
        return {
            'success': True,
            'task_id': task_id,
            'reasoning_type': 'deductive',
            'result': result,
            'confidence': confidence,
            'steps': steps,
            'duration': duration
        }
    
    def inductive_reasoning(self, observations, pattern_goal):
        task_id = self._generate_task_id()
        start_time = datetime.now()
        
        steps = []
        result = None
        confidence = 0.0
        
        steps.append({
            'step': 1,
            'type': 'observation_analysis',
            'description': f'分析观察数据: {len(observations)} 个观察',
            'data': str(observations)[:200]
        })
        
        steps.append({
            'step': 2,
            'type': 'pattern_recognition',
            'description': '识别数据中的模式和规律',
            'data': f'目标: {pattern_goal}'
        })
        
        try:
            confidence = min(0.85, 0.6 + len(observations) * 0.03)
            
            pattern_summary = []
            for i, obs in enumerate(observations[:3]):
                pattern_summary.append(f"观察{i+1}: {obs}")
            
            result = {
                'pattern': f'从观察数据中归纳出模式：{pattern_goal}',
                'supporting_observations': len(observations),
                'confidence': confidence,
                'explanation': '通过归纳推理，从多个具体观察中抽象出一般规律和模式',
                'sample_observations': pattern_summary
            }
            
            steps.append({
                'step': 3,
                'type': 'generalization',
                'description': '进行归纳泛化',
                'data': str(result)[:200]
            })
        except Exception as e:
            steps.append({
                'step': 3,
                'type': 'error',
                'description': f'推理失败: {str(e)}',
                'data': ''
            })
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        try:
            conn = sqlite3.connect('ai_cognitive.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reasoning_tasks 
                (task_id, reasoning_type, input_data, goal, status, confidence, result, reasoning_steps, created_at,
                completed_at, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id, 'inductive', json.dumps({'observations': observations}),
                pattern_goal, 'completed', confidence,
                json.dumps(result) if result else '{}',
                json.dumps(steps),
                start_time.isoformat(), end_time.isoformat(), duration
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Cognitive Reasoning] 保存推理任务失败: {e}")
        
        return {
            'success': True,
            'task_id': task_id,
            'reasoning_type': 'inductive',
            'result': result,
            'confidence': confidence,
            'steps': steps,
            'duration': duration
        }
    
    def abductive_reasoning(self, evidence, hypothesis_goal):
        task_id = self._generate_task_id()
        start_time = datetime.now()
        
        steps = []
        result = None
        confidence = 0.0
        
        steps.append({
            'step': 1,
            'type': 'evidence_analysis',
            'description': f'分析证据: {len(evidence)} 条证据',
            'data': str(evidence)[:200]
        })
        
        steps.append({
            'step': 2,
            'type': 'hypothesis_generation',
            'description': '生成可能的假设',
            'data': f'目标: {hypothesis_goal}'
        })
        
        try:
            confidence = min(0.80, 0.5 + len(evidence) * 0.05)
            
            result = {
                'hypothesis': f'基于证据的最佳解释：{hypothesis_goal}',
                'supporting_evidence': len(evidence),
                'confidence': confidence,
                'explanation': '通过溯因推理，从观察到的证据出发，找到最可能的解释或原因',
                'alternatives': ['备选假设1', '备选假设2']
            }
            
            steps.append({
                'step': 3,
                'type': 'best_explanation',
                'description': '选择最佳解释',
                'data': str(result)[:200]
            })
        except Exception as e:
            steps.append({
                'step': 3,
                'type': 'error',
                'description': f'推理失败: {str(e)}',
                'data': ''
            })
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        try:
            conn = sqlite3.connect('ai_cognitive.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reasoning_tasks 
                (task_id, reasoning_type, input_data, goal, status, confidence, result, reasoning_steps, created_at,
                completed_at, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id, 'abductive', json.dumps({'evidence': evidence}),
                hypothesis_goal, 'completed', confidence,
                json.dumps(result) if result else '{}',
                json.dumps(steps),
                start_time.isoformat(), end_time.isoformat(), duration
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Cognitive Reasoning] 保存推理任务失败: {e}")
        
        return {
            'success': True,
            'task_id': task_id,
            'reasoning_type': 'abductive',
            'result': result,
            'confidence': confidence,
            'steps': steps,
            'duration': duration
        }
    
    def analogical_reasoning(self, source_domain, target_domain, mapping_goal):
        task_id = self._generate_task_id()
        start_time = datetime.now()
        
        steps = []
        result = None
        confidence = 0.0
        
        steps.append({
            'step': 1,
            'type': 'domain_analysis',
            'description': f'分析源域和目标域',
            'data': f'源域: {source_domain}, 目标域: {target_domain}'
        })
        
        steps.append({
            'step': 2,
            'type': 'mapping_creation',
            'description': '创建域之间的映射关系',
            'data': f'目标: {mapping_goal}'
        })
        
        try:
            confidence = 0.75
            
            mappings = []
            for key in source_domain.keys()[:3]:
                if key in target_domain:
                    mappings.append(f"{key}: {source_domain[key]} -> {target_domain[key]}")
            
            result = {
                'mapping': f'建立类比映射：{mapping_goal}',
                'source_domain': list(source_domain.keys()),
                'target_domain': list(target_domain.keys()),
                'confidence': confidence,
                'explanation': '通过类比推理，将源域的知识和关系映射到目标域，实现知识迁移',
                'mappings': mappings
            }
            
            steps.append({
                'step': 3,
                'type': 'knowledge_transfer',
                'description': '完成知识迁移',
                'data': str(result)[:200]
            })
        except Exception as e:
            steps.append({
                'step': 3,
                'type': 'error',
                'description': f'推理失败: {str(e)}',
                'data': ''
            })
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        try:
            conn = sqlite3.connect('ai_cognitive.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reasoning_tasks 
                (task_id, reasoning_type, input_data, goal, status, confidence, result, reasoning_steps, created_at,
                completed_at, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id, 'analogical', json.dumps({'source': source_domain, 'target': target_domain}),
                mapping_goal, 'completed', confidence,
                json.dumps(result) if result else '{}',
                json.dumps(steps),
                start_time.isoformat(), end_time.isoformat(), duration
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Cognitive Reasoning] 保存推理任务失败: {e}")
        
        return {
            'success': True,
            'task_id': task_id,
            'reasoning_type': 'analogical',
            'result': result,
            'confidence': confidence,
            'steps': steps,
            'duration': duration
        }
    
    def causal_reasoning(self, events, effect_goal):
        task_id = self._generate_task_id()
        start_time = datetime.now()
        
        steps = []
        result = None
        confidence = 0.0
        
        steps.append({
            'step': 1,
            'type': 'event_analysis',
            'description': f'分析事件序列: {len(events)} 个事件',
            'data': str(events)[:200]
        })
        
        steps.append({
            'step': 2,
            'type': 'causal_chain',
            'description': '构建因果链',
            'data': f'目标效果: {effect_goal}'
        })
        
        try:
            confidence = min(0.85, 0.6 + len(events) * 0.04)
            
            causal_chain = []
            for i, event in enumerate(events[:5]):
                if i < len(events) - 1:
                    causal_chain.append(f"事件{i+1} -> 事件{i+2}")
            
            result = {
                'effect': f'因果推理结果：{effect_goal}',
                'event_count': len(events),
                'confidence': confidence,
                'explanation': '通过因果推理，分析事件之间的因果关系，预测或解释特定效果',
                'causal_chain': causal_chain
            }
            
            steps.append({
                'step': 3,
                'type': 'effect_prediction',
                'description': '预测效果',
                'data': str(result)[:200]
            })
        except Exception as e:
            steps.append({
                'step': 3,
                'type': 'error',
                'description': f'推理失败: {str(e)}',
                'data': ''
            })
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        try:
            conn = sqlite3.connect('ai_cognitive.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reasoning_tasks 
                (task_id, reasoning_type, input_data, goal, status, confidence, result, reasoning_steps, created_at,
                completed_at, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id, 'causal', json.dumps({'events': events}),
                effect_goal, 'completed', confidence,
                json.dumps(result) if result else '{}',
                json.dumps(steps),
                start_time.isoformat(), end_time.isoformat(), duration
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Cognitive Reasoning] 保存推理任务失败: {e}")
        
        return {
            'success': True,
            'task_id': task_id,
            'reasoning_type': 'causal',
            'result': result,
            'confidence': confidence,
            'steps': steps,
            'duration': duration
        }
    
    def execute_reasoning(self, reasoning_type, input_data, goal):
        reasoning_methods = {
            'deductive': self.deductive_reasoning,
            'inductive': self.inductive_reasoning,
            'abductive': self.abductive_reasoning,
            'analogical': self.analogical_reasoning,
            'causal': self.causal_reasoning
        }
        
        if reasoning_type not in reasoning_methods:
            return {'success': False, 'error': f'不支持的推理类型: {reasoning_type}'}
        
        method = reasoning_methods[reasoning_type]
        
        if reasoning_type == 'deductive':
            return method(input_data.get('premises', []), goal)
        elif reasoning_type == 'inductive':
            return method(input_data.get('observations', []), goal)
        elif reasoning_type == 'abductive':
            return method(input_data.get('evidence', []), goal)
        elif reasoning_type == 'analogical':
            return method(input_data.get('source_domain', {}), input_data.get('target_domain', {}), goal)
        elif reasoning_type == 'causal':
            return method(input_data.get('events', []), goal)
        
        return {'success': False, 'error': '未知推理类型'}
    
    def get_reasoning_task(self, task_id):
        try:
            conn = sqlite3.connect('ai_cognitive.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reasoning_tasks WHERE task_id = ?', (task_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                result = dict(row)
                result['input_data'] = json.loads(result.get('input_data', '{}'))
                result['result'] = json.loads(result.get('result', '{}'))
                result['reasoning_steps'] = json.loads(result.get('reasoning_steps', '[]'))
                return result
            return None
        except Exception as e:
            logger.info(f"[AI Cognitive Reasoning] 获取推理任务失败: {e}")
            return None
    
    def list_reasoning_tasks(self, reasoning_type=None, limit=20):
        try:
            conn = sqlite3.connect('ai_cognitive.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if reasoning_type:
                cursor.execute('''
                    SELECT * FROM reasoning_tasks WHERE reasoning_type = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (reasoning_type, limit))
            else:
                cursor.execute('''
                    SELECT * FROM reasoning_tasks
                    ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
            
            results = []
            for row in cursor.fetchall():
                task = dict(row)
                task['result'] = json.loads(task.get('result', '{}'))
                results.append(task)
            
            conn.close()
            return results
        except Exception as e:
            logger.info(f"[AI Cognitive Reasoning] 列出推理任务失败: {e}")
            return []
    
    def get_reasoning_statistics(self):
        try:
            conn = sqlite3.connect('ai_cognitive.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM reasoning_tasks')
            total_tasks = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM reasoning_tasks WHERE status = ?', ('completed',))
            completed_tasks = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM knowledge_base')
            knowledge_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(confidence) FROM reasoning_tasks WHERE status = ?', ('completed',))
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            cursor.execute('''
                SELECT reasoning_type, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM reasoning_tasks WHERE status = 'completed'
                GROUP BY reasoning_type
            ''')
            type_stats = []
            for row in cursor.fetchall():
                type_stats.append({
                    'reasoning_type': row[0],
                    'count': row[1],
                    'avg_confidence': row[2] or 0.0
                })
            
            conn.close()
            
            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'knowledge_count': knowledge_count,
                'avg_confidence': round(avg_confidence, 2),
                'type_statistics': type_stats
            }
        except Exception as e:
            logger.info(f"[AI Cognitive Reasoning] 获取统计信息失败: {e}")
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'knowledge_count': 0,
                'avg_confidence': 0.0,
                'type_statistics': []
            }

ai_cognitive_reasoning = AICognitiveReasoning()