# -*- coding: utf-8 -*-
"""
AI员工技能进化子系统
功能：
1. 技能跟踪 - 跟踪每个AI员工的任务完成情况和技能表现
2. 能力评分 - 动态评估AI员工的各项能力
3. 思维进化 - 根据任务结果调整思维焦点和决策模式
4. 技能升级 - 自动提升AI员工的技能等级
5. 进化建议 - 生成针对性的技能提升建议
"""

import os
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'app.db')

SKILL_LEVELS = {
    0: '新手',
    1: '初级',
    2: '中级',
    3: '高级',
    4: '专家',
    5: '大师'
}

THINKING_FOCUS_TYPES = {
    'analytical': '分析型',
    'creative': '创造型',
    'systemic': '系统型',
    'practical': '实践型',
    'critical': '批判型',
    'strategic': '战略型',
    'detail_oriented': '细节型',
    'visionary': '远见型'
}

class SkillMetric:
    """技能指标类"""
    
    def __init__(self, skill_name: str, score: float = 0.0, level: int = 0, 
                 experience: int = 0, improvement_rate: float = 0.0):
        self.skill_name = skill_name
        self.score = score
        self.level = level
        self.experience = experience
        self.improvement_rate = improvement_rate
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'skill_name': self.skill_name,
            'score': round(self.score, 2),
            'level': self.level,
            'level_name': SKILL_LEVELS.get(self.level, '未知'),
            'experience': self.experience,
            'improvement_rate': round(self.improvement_rate, 2),
            'last_updated': self.last_updated.isoformat()
        }

class ThinkingProfile:
    """思维模式档案"""
    
    def __init__(self):
        self.focus_distribution = {
            'analytical': 0.2,
            'creative': 0.2,
            'systemic': 0.2,
            'practical': 0.2,
            'critical': 0.2
        }
        self.primary_focus = 'analytical'
        self.adaptive_history = []
    
    def update_focus(self, task_result: Dict[str, Any]):
        """根据任务结果更新思维焦点"""
        task_type = task_result.get('task_type', '')
        success = task_result.get('success', False)
        feedback = task_result.get('feedback', {})
        
        if success:
            self._reinforce_successful_focus(task_type)
        else:
            self._adapt_from_failure(task_type, feedback)
        
        self._normalize_distribution()
        self._determine_primary_focus()
        
        self.adaptive_history.append({
            'timestamp': datetime.now().isoformat(),
            'task_type': task_type,
            'success': success,
            'previous_focus': self.primary_focus,
            'focus_distribution': self.focus_distribution.copy()
        })
        
        if len(self.adaptive_history) > 50:
            self.adaptive_history = self.adaptive_history[-50:]
    
    def _reinforce_successful_focus(self, task_type: str):
        """强化成功的思维焦点"""
        focus_map = {
            'analysis': 'analytical',
            'design': 'creative',
            'planning': 'systemic',
            'execution': 'practical',
            'review': 'critical',
            'strategy': 'strategic',
            'detail': 'detail_oriented',
            'innovation': 'visionary'
        }
        
        target_focus = focus_map.get(task_type, 'analytical')
        if target_focus in self.focus_distribution:
            self.focus_distribution[target_focus] = min(1.0, self.focus_distribution[target_focus] + 0.05)
    
    def _adapt_from_failure(self, task_type: str, feedback: Dict[str, Any]):
        """从失败中调整思维焦点"""
        weak_areas = feedback.get('weak_areas', [])
        
        for area in weak_areas:
            if area in self.focus_distribution:
                self.focus_distribution[area] = min(1.0, self.focus_distribution[area] + 0.03)
        
        for key in self.focus_distribution:
            if key not in weak_areas:
                self.focus_distribution[key] = max(0.05, self.focus_distribution[key] - 0.01)
    
    def _normalize_distribution(self):
        """归一化分布"""
        total = sum(self.focus_distribution.values())
        if total > 0:
            for key in self.focus_distribution:
                self.focus_distribution[key] /= total
    
    def _determine_primary_focus(self):
        """确定主要思维焦点"""
        self.primary_focus = max(self.focus_distribution, key=self.focus_distribution.get)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'primary_focus': self.primary_focus,
            'primary_focus_name': THINKING_FOCUS_TYPES.get(self.primary_focus, self.primary_focus),
            'focus_distribution': {k: round(v, 3) for k, v in self.focus_distribution.items()},
            'focus_distribution_labels': {
                k: f"{THINKING_FOCUS_TYPES.get(k, k)} ({round(v * 100)}%)" 
                for k, v in self.focus_distribution.items()
            },
            'adaptive_history_length': len(self.adaptive_history)
        }

class AIEmployeeEvolution:
    """单个AI员工的进化记录"""
    
    def __init__(self, employee_id: str, employee_type: str, name: str):
        self.employee_id = employee_id
        self.employee_type = employee_type
        self.name = name
        self.skills = {}
        self.thinking_profile = ThinkingProfile()
        self.task_history = []
        self.performance_trend = []
        self.evolution_stage = 1
        self.total_experience = 0
        
        self._init_skills()
    
    def _init_skills(self):
        """初始化技能"""
        skill_templates = {
            'system_maintenance': ['系统诊断', '问题修复', '性能优化', '安全监控'],
            'code_fixer': ['代码分析', 'Bug修复', '代码重构', '代码审查'],
            'data_analyzer': ['数据处理', '统计分析', '可视化', '预测建模'],
            'exam_system_expert': ['试卷生成', '题库管理', '成绩分析', '难度评估'],
            'learning_analyst': ['学习分析', '路径规划', '知识图谱', '个性化推荐'],
            'devops_engineer': ['部署管理', '配置管理', '监控告警', '自动化运维'],
            'security_guard': ['安全扫描', '漏洞检测', '权限管理', '威胁分析'],
            'frontend_engineer': ['UI设计', '交互开发', '响应式布局', '性能优化']
        }
        
        skills = skill_templates.get(self.employee_type, ['通用技能', '问题解决'])
        
        for skill_name in skills:
            self.skills[skill_name] = SkillMetric(skill_name, score=50.0, level=1, experience=0)
    
    def record_task(self, task_result: Dict[str, Any]):
        """记录任务结果"""
        task_record = {
            'task_id': task_result.get('task_id', ''),
            'task_type': task_result.get('task_type', ''),
            'success': task_result.get('success', False),
            'execution_time': task_result.get('execution_time', 0),
            'quality_score': task_result.get('quality_score', 0),
            'feedback': task_result.get('feedback', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        self.task_history.append(task_record)
        
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-100:]
        
        self._update_skills(task_record)
        self._update_performance_trend(task_record)
        self.thinking_profile.update_focus(task_record)
        self._check_evolution_stage()
    
    def _update_skills(self, task_record: Dict[str, Any]):
        """更新技能评分"""
        task_type = task_record.get('task_type', '')
        success = task_record.get('success', False)
        quality_score = task_record.get('quality_score', 80)
        
        skill_mapping = {
            'analysis': ['系统诊断', '代码分析', '数据处理', '学习分析'],
            'design': ['UI设计', '交互开发', '路径规划'],
            'execution': ['问题修复', 'Bug修复', '部署管理', '配置管理'],
            'review': ['代码审查', '安全扫描', '漏洞检测'],
            'optimization': ['性能优化', '代码重构', '知识图谱'],
            'creation': ['试卷生成', '题库管理', '个性化推荐']
        }
        
        relevant_skills = skill_mapping.get(task_type, [])
        
        for skill_name in self.skills:
            is_relevant = skill_name in relevant_skills
            
            if success:
                exp_gain = int(quality_score / 10)
                score_increase = 1.5 if is_relevant else 0.5
            else:
                exp_gain = 5
                score_increase = 0.3 if is_relevant else 0.1
            
            self.skills[skill_name].experience += exp_gain
            self.skills[skill_name].score = min(100, self.skills[skill_name].score + score_increase)
            self.skills[skill_name].last_updated = datetime.now()
            
            self._check_skill_level_up(self.skills[skill_name])
    
    def _check_skill_level_up(self, skill: SkillMetric):
        """检查技能是否升级"""
        exp_thresholds = [0, 50, 150, 350, 700, 1200]
        
        for level, threshold in enumerate(exp_thresholds):
            if skill.experience >= threshold and skill.level < level:
                skill.level = level
                logger.info(f"[技能进化] AI员工 {self.name} 的技能 {skill.skill_name} 升级到 {SKILL_LEVELS[level]}")
    
    def _update_performance_trend(self, task_record: Dict[str, Any]):
        """更新性能趋势"""
        trend_point = {
            'timestamp': datetime.now().isoformat(),
            'success': 1 if task_record.get('success', False) else 0,
            'quality': task_record.get('quality_score', 0),
            'execution_time': task_record.get('execution_time', 0)
        }
        
        self.performance_trend.append(trend_point)
        
        if len(self.performance_trend) > 50:
            self.performance_trend = self.performance_trend[-50:]
        
        self.total_experience += 10 if task_record.get('success', False) else 5
    
    def _check_evolution_stage(self):
        """检查进化阶段"""
        stage_thresholds = [0, 10, 50, 200, 500, 1000]
        
        for stage, threshold in enumerate(stage_thresholds):
            if self.total_experience >= threshold and self.evolution_stage < stage:
                self.evolution_stage = stage
                logger.info(f"[进化阶段] AI员工 {self.name} 进化到阶段 {stage}")
    
    def get_evolution_summary(self) -> Dict[str, Any]:
        """获取进化摘要"""
        recent_tasks = self.task_history[-10:]
        success_rate = sum(1 for t in recent_tasks if t['success']) / len(recent_tasks) if recent_tasks else 0
        
        return {
            'employee_id': self.employee_id,
            'employee_type': self.employee_type,
            'name': self.name,
            'evolution_stage': self.evolution_stage,
            'evolution_stage_name': SKILL_LEVELS.get(self.evolution_stage, '未知'),
            'total_experience': self.total_experience,
            'recent_success_rate': round(success_rate * 100, 1),
            'skills': {name: skill.to_dict() for name, skill in self.skills.items()},
            'thinking_profile': self.thinking_profile.to_dict(),
            'task_count': len(self.task_history),
            'performance_trend_length': len(self.performance_trend)
        }
    
    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """获取改进建议"""
        suggestions = []
        
        weak_skills = sorted(
            self.skills.items(), 
            key=lambda x: x[1].score
        )[:3]
        
        for skill_name, skill in weak_skills:
            if skill.score < 70:
                suggestions.append({
                    'skill_name': skill_name,
                    'current_score': round(skill.score, 1),
                    'current_level': SKILL_LEVELS.get(skill.level, '未知'),
                    'suggestion': f"建议增加 {skill_name} 相关任务的练习",
                    'priority': 'high' if skill.score < 50 else 'medium'
                })
        
        if self.thinking_profile.adaptive_history:
            recent_adaptations = self.thinking_profile.adaptive_history[-5:]
            failure_count = sum(1 for a in recent_adaptations if not a['success'])
            
            if failure_count >= 3:
                suggestions.append({
                    'skill_name': '思维模式',
                    'current_score': round(self.thinking_profile.focus_distribution[self.thinking_profile.primary_focus] * 100, 1),
                    'suggestion': '建议调整思维焦点，当前主要依赖' + THINKING_FOCUS_TYPES.get(self.thinking_profile.primary_focus, '') + '模式',
                    'priority': 'medium'
                })
        
        if not suggestions:
            suggestions.append({
                'skill_name': '综合能力',
                'current_score': round(sum(s.score for s in self.skills.values()) / len(self.skills), 1),
                'suggestion': '当前技能状态良好，建议继续保持并尝试更复杂的任务',
                'priority': 'low'
            })
        
        return suggestions

class AISkillEvolutionSystem:
    """AI技能进化系统"""
    
    def __init__(self):
        self.employees = {}
        self._lock = threading.RLock()
        self._evolution_thread = None
        self._is_evolving = False
        
        self._create_tables()
        self._load_employee_data()
    
    def _create_tables(self):
        """创建技能进化相关数据表"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_skill_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id TEXT NOT NULL,
                        employee_type TEXT NOT NULL,
                        employee_name TEXT NOT NULL,
                        skill_name TEXT NOT NULL,
                        skill_score REAL DEFAULT 0.0,
                        skill_level INTEGER DEFAULT 0,
                        experience INTEGER DEFAULT 0,
                        improvement_rate REAL DEFAULT 0.0,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_thinking_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id TEXT NOT NULL,
                        primary_focus TEXT DEFAULT 'analytical',
                        focus_distribution TEXT DEFAULT '{}',
                        adaptive_history TEXT DEFAULT '[]',
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_evolution_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id TEXT NOT NULL,
                        evolution_stage INTEGER DEFAULT 1,
                        total_experience INTEGER DEFAULT 0,
                        event_type TEXT DEFAULT 'task_completion',
                        event_data TEXT DEFAULT '{}',
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_task_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id TEXT NOT NULL,
                        task_id TEXT,
                        task_type TEXT,
                        success INTEGER DEFAULT 0,
                        execution_time REAL DEFAULT 0,
                        quality_score REAL DEFAULT 0,
                        feedback TEXT DEFAULT '{}',
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("[技能进化系统] 数据表创建完成")
        except Exception as e:
            logger.error(f"[技能进化系统] 创建数据表失败: {str(e)}")
    
    def _load_employee_data(self):
        """加载员工数据"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT id, ai_type, name FROM ai_employees')
                employees = cursor.fetchall()
                
                for emp in employees:
                    self.employees[emp['id']] = AIEmployeeEvolution(
                        employee_id=emp['id'],
                        employee_type=emp['ai_type'],
                        name=emp['name']
                    )
                
                cursor.execute('''
                    SELECT employee_id, skill_name, skill_score, skill_level, experience
                    FROM ai_skill_records
                ''')
                for record in cursor.fetchall():
                    emp_id = record['employee_id']
                    if emp_id in self.employees:
                        self.employees[emp_id].skills[record['skill_name']] = SkillMetric(
                            skill_name=record['skill_name'],
                            score=record['skill_score'],
                            level=record['skill_level'],
                            experience=record['experience']
                        )
                
                logger.info(f"[技能进化系统] 已加载 {len(self.employees)} 个AI员工")
        except Exception as e:
            logger.error(f"[技能进化系统] 加载员工数据失败: {str(e)}")
    
    def start_evolution(self):
        """启动进化线程"""
        if self._is_evolving:
            return
        
        self._is_evolving = True
        self._evolution_thread = threading.Thread(
            target=self._evolution_loop,
            daemon=True,
            name='SkillEvolutionThread'
        )
        self._evolution_thread.start()
        logger.info("[技能进化系统] 进化线程已启动")
    
    def stop_evolution(self):
        """停止进化线程"""
        self._is_evolving = False
        if self._evolution_thread:
            self._evolution_thread.join(timeout=5)
        logger.info("[技能进化系统] 进化线程已停止")
    
    def _evolution_loop(self):
        """进化主循环"""
        while self._is_evolving:
            try:
                self._process_pending_tasks()
                self._update_skill_records()
                self._persist_evolution_data()
            except Exception as e:
                logger.error(f"[技能进化系统] 进化循环错误: {str(e)}")
            
            time.sleep(120)
    
    def _process_pending_tasks(self):
        """处理待处理的任务"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM ai_task_logs 
                    WHERE processed = 0 
                    ORDER BY created_at DESC LIMIT 50
                ''')
                
                pending_tasks = cursor.fetchall()
                
                for task in pending_tasks:
                    emp_id = task['ai_id']
                    
                    if emp_id in self.employees:
                        task_result = {
                            'task_id': task['task_id'],
                            'task_type': task['task_type'],
                            'success': bool(task['success']),
                            'execution_time': task['execution_time'] or 0,
                            'quality_score': task.get('quality_score', 80),
                            'feedback': json.loads(task.get('feedback', '{}'))
                        }
                        
                        self.employees[emp_id].record_task(task_result)
                    
                    cursor.execute('''
                        UPDATE ai_task_logs SET processed = 1 WHERE id = ?
                    ''', (task['id'],))
                
                conn.commit()
        except Exception as e:
            logger.error(f"[技能进化系统] 处理待处理任务失败: {str(e)}")
    
    def _update_skill_records(self):
        """更新技能记录"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                for emp_id, evolution in self.employees.items():
                    for skill_name, skill in evolution.skills.items():
                        cursor.execute('''
                            INSERT OR REPLACE INTO ai_skill_records 
                            (employee_id, employee_type, employee_name, skill_name, 
                             skill_score, skill_level, experience, improvement_rate, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            emp_id,
                            evolution.employee_type,
                            evolution.name,
                            skill_name,
                            skill.score,
                            skill.level,
                            skill.experience,
                            skill.improvement_rate,
                            datetime.now().isoformat()
                        ))
                
                conn.commit()
        except Exception as e:
            logger.error(f"[技能进化系统] 更新技能记录失败: {str(e)}")
    
    def _persist_evolution_data(self):
        """持久化进化数据"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                for emp_id, evolution in self.employees.items():
                    thinking = evolution.thinking_profile
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO ai_thinking_profiles 
                        (employee_id, primary_focus, focus_distribution, adaptive_history, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        emp_id,
                        thinking.primary_focus,
                        json.dumps(thinking.focus_distribution),
                        json.dumps(thinking.adaptive_history),
                        datetime.now().isoformat()
                    ))
                
                conn.commit()
        except Exception as e:
            logger.error(f"[技能进化系统] 持久化进化数据失败: {str(e)}")
    
    def record_employee_task(self, employee_id: str, task_result: Dict[str, Any]):
        """记录员工任务结果"""
        with self._lock:
            if employee_id not in self.employees:
                try:
                    with sqlite3.connect(DATABASE_PATH) as conn:
                        conn.row_factory = sqlite3.Row
                        cursor = conn.cursor()
                        cursor.execute('SELECT id, ai_type, name FROM ai_employees WHERE id = ?', (employee_id,))
                        emp = cursor.fetchone()
                        
                        if emp:
                            self.employees[employee_id] = AIEmployeeEvolution(
                                employee_id=emp['id'],
                                employee_type=emp['ai_type'],
                                name=emp['name']
                            )
                        else:
                            self.employees[employee_id] = AIEmployeeEvolution(
                                employee_id=employee_id,
                                employee_type='general',
                                name=f'员工{employee_id[:8]}'
                            )
                except Exception as e:
                    logger.error(f"[技能进化系统] 创建员工进化记录失败: {str(e)}")
                    return
            
            self.employees[employee_id].record_task(task_result)
    
    def get_employee_evolution(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """获取员工进化信息"""
        with self._lock:
            if employee_id in self.employees:
                return self.employees[employee_id].get_evolution_summary()
            return None
    
    def get_all_employees_evolution(self) -> List[Dict[str, Any]]:
        """获取所有员工进化信息"""
        with self._lock:
            return [emp.get_evolution_summary() for emp in self.employees.values()]
    
    def get_improvement_suggestions(self, employee_id: str) -> List[Dict[str, Any]]:
        """获取员工改进建议"""
        with self._lock:
            if employee_id in self.employees:
                return self.employees[employee_id].get_improvement_suggestions()
            return []
    
    def get_top_employees(self, limit: int = 5, by: str = 'experience') -> List[Dict[str, Any]]:
        """获取顶尖员工"""
        with self._lock:
            employees = list(self.employees.values())
            
            if by == 'experience':
                key_func = lambda e: e.total_experience
            elif by == 'success_rate':
                key_func = lambda e: e.get_evolution_summary()['recent_success_rate']
            elif by == 'stage':
                key_func = lambda e: e.evolution_stage
            else:
                key_func = lambda e: e.total_experience
            
            sorted_employees = sorted(employees, key=key_func, reverse=True)
            
            return [emp.get_evolution_summary() for emp in sorted_employees[:limit]]
    
    def get_evolution_stats(self) -> Dict[str, Any]:
        """获取进化统计"""
        with self._lock:
            if not self.employees:
                return {
                    'total_employees': 0,
                    'avg_experience': 0,
                    'avg_success_rate': 0,
                    'top_stage': 0,
                    'stage_distribution': {}
                }
            
            summaries = [emp.get_evolution_summary() for emp in self.employees.values()]
            
            stage_distribution = defaultdict(int)
            for s in summaries:
                stage_distribution[s['evolution_stage']] += 1
            
            return {
                'total_employees': len(self.employees),
                'avg_experience': round(sum(s['total_experience'] for s in summaries) / len(summaries)),
                'avg_success_rate': round(sum(s['recent_success_rate'] for s in summaries) / len(summaries), 1),
                'top_stage': max(s['evolution_stage'] for s in summaries),
                'stage_distribution': {SKILL_LEVELS.get(k, str(k)): v for k, v in stage_distribution.items()},
                'active_employees': len([s for s in summaries if s['task_count'] > 0])
            }
    
    def reset_employee_skills(self, employee_id: str) -> bool:
        """重置员工技能"""
        with self._lock:
            if employee_id in self.employees:
                self.employees[employee_id]._init_skills()
                self.employees[employee_id].total_experience = 0
                self.employees[employee_id].evolution_stage = 1
                self.employees[employee_id].thinking_profile = ThinkingProfile()
                logger.info(f"[技能进化系统] 已重置员工 {employee_id} 的技能")
                return True
            return False
    
    def simulate_training(self, employee_id: str, skill_name: str, intensity: float = 1.0) -> Dict[str, Any]:
        """模拟技能训练"""
        with self._lock:
            if employee_id not in self.employees:
                return {'success': False, 'message': '员工不存在'}
            
            employee = self.employees[employee_id]
            
            if skill_name not in employee.skills:
                employee.skills[skill_name] = SkillMetric(skill_name, score=50.0, level=1, experience=0)
            
            skill = employee.skills[skill_name]
            
            exp_gain = int(50 * intensity)
            score_increase = 5.0 * intensity
            
            skill.experience += exp_gain
            skill.score = min(100, skill.score + score_increase)
            skill.last_updated = datetime.now()
            
            employee._check_skill_level_up(skill)
            
            return {
                'success': True,
                'employee_id': employee_id,
                'skill_name': skill_name,
                'experience_gained': exp_gain,
                'score_increase': score_increase,
                'new_score': round(skill.score, 1),
                'new_level': skill.level,
                'level_name': SKILL_LEVELS.get(skill.level, '未知')
            }

ai_skill_evolution_system = AISkillEvolutionSystem()