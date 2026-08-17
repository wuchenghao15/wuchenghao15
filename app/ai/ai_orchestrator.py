#!/usr/bin/env python3
import json
import datetime
import threading
import time
import sqlite3
import os
import sys

class AIEmployeeOrchestrator:
    def __init__(self):
        self._lock = threading.Lock()
        self.growth_cycles = {}
        self._create_tables()
        self._start_growth_monitor()

    def _create_tables(self):
        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS growth_cycles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    cycle_number INTEGER DEFAULT 1,
                    stage TEXT DEFAULT 'pending',
                    start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    end_time TEXT,
                    status TEXT DEFAULT 'running',
                    thinking_result TEXT,
                    learning_result TEXT,
                    skill_evolution TEXT,
                    insights TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employee_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    period TEXT,
                    thinking_sessions INTEGER DEFAULT 0,
                    learning_hours REAL DEFAULT 0,
                    knowledge_acquired INTEGER DEFAULT 0,
                    skills_improved INTEGER DEFAULT 0,
                    plan_progress REAL DEFAULT 0,
                    overall_score REAL DEFAULT 0,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
            logger.info("[AIEmployeeOrchestrator] 数据库表创建完成")
        except Exception as e:
            logger.info(f"[AIEmployeeOrchestrator] 创建表失败: {e}")

    def _start_growth_monitor(self):
        self.monitor_thread = threading.Thread(target=self._monitor_growth_cycles, daemon=True)
        self.monitor_thread.start()

    def _monitor_growth_cycles(self):
        while True:
            try:
                self._process_pending_cycles()
            except Exception as e:
                logger.info(f"[AIEmployeeOrchestrator] 监控线程异常: {e}")
            time.sleep(300)

    def _process_pending_cycles(self):
        pass

    def trigger_full_growth_cycle(self, employee_id, employee_name, current_skills=None):
        try:
            try:
                from app.ai.ai_professional_role import ai_professional_role_system
            except ImportError:
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                from app.ai.ai_professional_role import ai_professional_role_system
            
            try:
                from app.ai.ai_skill_evolution import skill_evolution_system
            except ImportError:
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                from app.ai.ai_skill_evolution import skill_evolution_system
        except ImportError as e:
            return {
                'success': False,
                'message': f'依赖模块加载失败: {str(e)}'
            }

        cycle_record = {
            'employee_id': employee_id,
            'employee_name': employee_name,
            'cycle_number': self._get_next_cycle_number(employee_id),
            'stage': 'thinking',
            'start_time': datetime.datetime.now().isoformat(),
            'steps': []
        }

        try:
            role_data = ai_professional_role_system.get_role(employee_id)
            if not role_data['success']:
                return {
                    'success': False,
                    'message': '员工未分配职业角色'
                }

            thinking_result = ai_professional_role_system.trigger_independent_thinking(
                employee_id, employee_name, current_skills
            )
            cycle_record['steps'].append({
                'step': 'independent_thinking',
                'success': thinking_result['success'],
                'message': thinking_result.get('message', '')
            })

            skill_analysis = thinking_result.get('thinking_result', {}).get('analysis_content', '{}')
            try:
                skill_analysis = json.loads(skill_analysis)
            except:
                skill_analysis = {}

            cycle_record['stage'] = 'learning'
            learning_topics = []
            skill_gaps = skill_analysis.get('skill_gaps', [])
            for gap in skill_gaps[:3]:
                learning_topics.append(gap.get('skill_name', ''))

            if not learning_topics and role_data.get('role_type'):
                role_type = role_data['role_type']
                if 'japanese' in role_type:
                    learning_topics = ['kansai_dialect',
                    'casual_japanese'] if 'kansai' in role_type else ['standard_japanese', 'business_japanese']
                elif 'english' in role_type:
                    learning_topics = ['american_pronunciation',
                    'slang_us'] if 'american' in role_type else ['british_pronunciation', 'idioms_uk']

            learning_results = []
            for topic in learning_topics[:2]:
                if topic:
                    learning_result = ai_professional_role_system.trigger_web_learning(
                        employee_id, employee_name, topic
                    )
                    learning_results.append({
                        'topic': topic,
                        'success': learning_result['success'],
                        'knowledge_acquired': len(learning_result.get('learning_result', {}).get('knowledge_acquired',
                        []))
                    })
                    cycle_record['steps'].append({
                        'step': 'web_learning',
                        'topic': topic,
                        'success': learning_result['success']
                    })

            cycle_record['stage'] = 'skill_evolution'
            for skill_name, skill_data in (current_skills or {}).items():
                score = skill_data.get('score', 0)
                improvement = skill_data.get('improvement_rate', 0)
                skill_evolution_system.track_task_outcome(
                    employee_id, employee_name, 'learning', skill_name, 
                    success=True, score_change=improvement
                )
            cycle_record['steps'].append({
                'step': 'skill_evolution_update',
                'success': True
            })

            cycle_record['stage'] = 'completed'
            cycle_record['end_time'] = datetime.datetime.now().isoformat()

            self._save_growth_cycle(cycle_record, learning_results)

            insights = []
            total_knowledge = sum(lr.get('knowledge_acquired', 0) for lr in learning_results)
            insights.append(f"完成第{cycle_record['cycle_number']}个成长周期")
            insights.append(f"网络学习获得{total_knowledge}条新知识")
            insights.append(f"识别到{len(skill_gaps)}个技能缺口")

            return {
                'success': True,
                'message': f"{employee_name}完成完整成长周期",
                'cycle_number': cycle_record['cycle_number'],
                'steps': cycle_record['steps'],
                'insights': insights,
                'learning_topics': learning_topics
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"成长周期执行失败: {str(e)}"
            }

    def _get_next_cycle_number(self, employee_id):
        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(cycle_number) FROM growth_cycles WHERE employee_id = ?', (employee_id,))
            row = cursor.fetchone()
            conn.close()
            return (row[0] or 0) + 1
        except:
            return 1

    def _save_growth_cycle(self, cycle_record, learning_results):
        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO growth_cycles
                (employee_id, cycle_number, stage, start_time, end_time, status,
                 thinking_result, learning_result, skill_evolution, insights)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (cycle_record['employee_id'], cycle_record['cycle_number'],
                  cycle_record['stage'], cycle_record['start_time'],
                  cycle_record['end_time'], 'completed',
                  json.dumps(cycle_record.get('steps', [])),
                  json.dumps(learning_results),
                  json.dumps({'updated': True}),
                  json.dumps(cycle_record.get('steps', []))))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AIEmployeeOrchestrator] 保存成长周期失败: {e}")

    def get_growth_history(self, employee_id):
        try:
            conn = sqlite3.connect('professional_role.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM growth_cycles WHERE employee_id = ? ORDER BY cycle_number DESC', (employee_id,
            ))
            rows = cursor.fetchall()
            conn.close()

            history = []
            for row in rows:
                history.append({
                    'cycle_number': row[2],
                    'stage': row[3],
                    'start_time': row[4],
                    'end_time': row[5],
                    'status': row[6],
                    'learning_result': json.loads(row[8]) if row[8] else []
                })
            return history
        except Exception as e:
            logger.info(f"[AIEmployeeOrchestrator] 获取成长历史失败: {e}")
            return []

    def trigger_batch_growth(self, employee_ids):
        results = []
        for emp_id in employee_ids:
            result = self.trigger_full_growth_cycle(emp_id, f"员工{emp_id}")
            results.append({
                'employee_id': emp_id,
                'success': result['success'],
                'message': result.get('message', '')
            })
        return results

    def get_all_employees_overview(self):
        try:
            from app.ai.ai_professional_role import ai_professional_role_system
            summary = ai_professional_role_system.get_professional_summary()
            return summary
        except Exception as e:
            logger.info(f"[AIEmployeeOrchestrator] 获取员工概览失败: {e}")
            return []

ai_orchestrator = AIEmployeeOrchestrator()