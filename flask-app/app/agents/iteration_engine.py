# -*- coding: utf-8 -*-
"""
主动迭代引擎 - 运行数据复盘、自动生成需求、代码编写
智能设置周期，Agent复盘全站运行数据，自动生成优化需求
"""
import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class IterationEngine:
    """主动迭代引擎"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._lock = threading.Lock()
        self._iterations: Dict[str, Dict] = {}
        self._db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app.db'
        )
        self._iteration_interval = 3600 * 24
        
        self._init_database()
        self._start_iteration_thread()
        
        self._initialized = True
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            from app.utils.db import db_manager
            
            db_manager.create_table('iteration_plans', {
                'plan_id': 'TEXT PRIMARY KEY',
                'status': 'TEXT NOT NULL DEFAULT "draft"',
                'iteration_type': 'TEXT NOT NULL',
                'priority': 'TEXT DEFAULT "medium"',
                'description': 'TEXT DEFAULT ""',
                'requirements': 'TEXT DEFAULT "{}"',
                'code_changes': 'TEXT DEFAULT "{}"',
                'test_results': 'TEXT DEFAULT ""',
                'created_at': 'TEXT',
                'executed_at': 'TEXT',
                'merged_at': 'TEXT',
                'approval_id': 'TEXT DEFAULT ""'
            })
            
            db_manager.create_table('runtime_analysis', {
                'analysis_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                'plan_id': 'TEXT',
                'metric_type': 'TEXT NOT NULL',
                'metric_name': 'TEXT NOT NULL',
                'value': 'REAL DEFAULT 0',
                'threshold': 'REAL DEFAULT 0',
                'status': 'TEXT NOT NULL DEFAULT "normal"',
                'recommendation': 'TEXT DEFAULT ""',
                'timestamp': 'TEXT NOT NULL'
            })
            
            db_manager.create_table('code_analysis', {
                'analysis_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                'plan_id': 'TEXT',
                'file_path': 'TEXT NOT NULL',
                'complexity': 'INTEGER DEFAULT 0',
                'lines_of_code': 'INTEGER DEFAULT 0',
                'duplicate_score': 'REAL DEFAULT 0',
                'outdated_score': 'REAL DEFAULT 0',
                'recommendation': 'TEXT DEFAULT ""'
            })
            
            logger.info("[迭代引擎] 数据库表初始化完成")
        except Exception as e:
            logger.error(f"[迭代引擎] 初始化数据库失败: {e}")
    
    def _start_iteration_thread(self):
        """启动定时迭代线程"""
        def iteration_loop():
            while True:
                try:
                    self.run_iteration()
                except Exception as e:
                    logger.error(f"[迭代引擎] 定时迭代失败: {e}")
                time.sleep(self._iteration_interval)
        
        thread = threading.Thread(target=iteration_loop, daemon=True)
        thread.start()
        logger.info(f"[迭代引擎] 定时迭代线程已启动，间隔: {self._iteration_interval}秒")
    
    def run_iteration(self) -> Dict:
        """运行一次迭代"""
        plan_id = f"iter_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        plan = {
            'plan_id': plan_id,
            'status': 'running',
            'iteration_type': 'scheduled',
            'priority': 'medium',
            'description': '定期自动迭代',
            'requirements': {},
            'code_changes': {},
            'created_at': datetime.now().isoformat()
        }
        
        self._save_plan(plan)
        
        try:
            runtime_issues = self._analyze_runtime_data(plan_id)
            code_issues = self._analyze_codebase(plan_id)
            
            requirements = self._generate_requirements(runtime_issues + code_issues)
            
            if requirements:
                plan['requirements'] = requirements
                plan['status'] = 'requirement_generated'
                
                from app.agents.approval_manager import get_approval_manager, OperationLevel
                
                approval_manager = get_approval_manager()
                approval_id = approval_manager.create_approval(
                    'iteration_plan',
                    OperationLevel.IMPORTANT.value,
                    f"自动生成迭代计划: {len(requirements)} 个需求",
                    {'requirements': requirements}
                )
                
                plan['approval_id'] = approval_id
                
                code_changes = self._implement_requirements(requirements)
                plan['code_changes'] = code_changes
                
                if code_changes:
                    plan['status'] = 'code_generated'
                    
                    from app.agents.auto_test_runner import get_test_runner
                    
                    test_runner = get_test_runner()
                    test_result = test_runner.run_api_tests()
                    plan['test_results'] = json.dumps(test_result)
                    
                    if test_result['status'] == 'completed':
                        plan['status'] = 'testing_passed'
                        logger.info(f"[迭代引擎] 迭代计划 {plan_id} 测试通过")
                    else:
                        plan['status'] = 'testing_failed'
                        logger.warning(f"[迭代引擎] 迭代计划 {plan_id} 测试失败")
            
            else:
                plan['status'] = 'completed'
                logger.info(f"[迭代引擎] 迭代计划 {plan_id} 无需优化")
            
            plan['executed_at'] = datetime.now().isoformat()
            self._save_plan(plan)
            
        except Exception as e:
            plan['status'] = 'failed'
            plan['code_changes'] = {'error': str(e)}
            self._save_plan(plan)
            logger.error(f"[迭代引擎] 迭代失败: {e}")
        
        return plan
    
    def _analyze_runtime_data(self, plan_id: str) -> List[Dict]:
        """分析运行时数据"""
        issues = []
        
        try:
            import requests
            
            try:
                response = requests.get('http://localhost:8888/api/monitoring/system', timeout=5)
                if response.status_code == 200:
                    system_data = response.json()['metrics']
                    
                    if system_data['cpu']['usage_percent'] > 80:
                        issues.append({
                            'type': 'performance',
                            'severity': 'high',
                            'title': 'CPU使用率过高',
                            'description': f"当前CPU使用率: {system_data['cpu']['usage_percent']}%",
                            'recommendation': '优化CPU密集型任务，考虑异步处理或缓存'
                        })
                    
                    if system_data['memory']['used_percent'] > 85:
                        issues.append({
                            'type': 'performance',
                            'severity': 'medium',
                            'title': '内存使用率过高',
                            'description': f"当前内存使用率: {system_data['memory']['used_percent']}%",
                            'recommendation': '优化内存使用，清理缓存，考虑增加内存'
                        })
            except Exception as e:
                logger.debug(f"[迭代引擎] 获取系统指标失败: {e}")
            
            try:
                response = requests.get('http://localhost:8888/api/core-agents/agents', timeout=5)
                if response.status_code == 200:
                    agents = response.json()['agents']
                    for agent_id, agent in agents.items():
                        if agent['status'] != 'idle':
                            issues.append({
                                'type': 'agent',
                                'severity': 'medium',
                                'title': f"Agent {agent['agent_name']} 状态异常",
                                'description': f"状态: {agent['status']}",
                                'recommendation': '检查Agent运行状态，必要时重启'
                            })
            except Exception as e:
                logger.debug(f"[迭代引擎] 获取Agent状态失败: {e}")
            
            self._save_runtime_analysis(plan_id, issues)
            
        except Exception as e:
            logger.error(f"[迭代引擎] 分析运行时数据失败: {e}")
        
        return issues
    
    def _analyze_codebase(self, plan_id: str) -> List[Dict]:
        """分析代码库"""
        issues = []
        
        try:
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            for root, dirs, files in os.walk(project_dir):
                if '.git' in dirs:
                    dirs.remove('.git')
                if '__pycache__' in dirs:
                    dirs.remove('__pycache__')
                if 'node_modules' in dirs:
                    dirs.remove('node_modules')
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                            
                            lines = content.split('\n')
                            loc = len(lines)
                            
                            complexity = 0
                            for line in lines:
                                if 'def ' in line or 'class ' in line:
                                    complexity += 1
                                if 'if ' in line or 'for ' in line or 'while ' in line:
                                    complexity += 0.5
                            
                            duplicate_score = 0
                            if loc > 500:
                                duplicate_score = min(loc / 1000, 1.0)
                            
                            if loc > 1000 or complexity > 50:
                                issues.append({
                                    'type': 'code_quality',
                                    'severity': 'medium',
                                    'title': f"文件过大或复杂度过高: {file}",
                                    'description': f"行数: {loc}, 复杂度: {complexity:.1f}",
                                    'recommendation': '考虑拆分文件，提取公共模块'
                                })
                            
                            self._save_code_analysis(plan_id, file_path, int(complexity), loc, duplicate_score)
                            
                        except Exception as e:
                            logger.debug(f"[迭代引擎] 分析文件 {file} 失败: {e}")
            
        except Exception as e:
            logger.error(f"[迭代引擎] 分析代码库失败: {e}")
        
        return issues
    
    def _generate_requirements(self, issues: List[Dict]) -> List[Dict]:
        """生成优化需求"""
        requirements = []
        
        for issue in issues:
            if issue['severity'] in ['high', 'critical']:
                requirements.append({
                    'id': f"req_{len(requirements) + 1}",
                    'title': issue['title'],
                    'description': issue['description'],
                    'severity': issue['severity'],
                    'recommendation': issue['recommendation'],
                    'type': issue['type']
                })
        
        return requirements[:5]
    
    def _implement_requirements(self, requirements: List[Dict]) -> Dict:
        """实现需求"""
        changes = {}
        
        for req in requirements:
            if req['type'] == 'performance':
                changes[req['id']] = {
                    'status': 'planned',
                    'description': f"优化: {req['title']}",
                    'files': [],
                    'actions': ['分析瓶颈', '优化代码', '添加缓存']
                }
            elif req['type'] == 'code_quality':
                changes[req['id']] = {
                    'status': 'planned',
                    'description': f"重构: {req['title']}",
                    'files': [],
                    'actions': ['拆分文件', '提取模块', '优化结构']
                }
            else:
                changes[req['id']] = {
                    'status': 'pending',
                    'description': f"待处理: {req['title']}",
                    'files': [],
                    'actions': ['人工审查']
                }
        
        return changes
    
    def _save_plan(self, plan: Dict):
        """保存迭代计划"""
        try:
            from app.utils.db import db_manager
            
            plan_data = {
                'plan_id': plan['plan_id'],
                'status': plan['status'],
                'iteration_type': plan.get('iteration_type', 'scheduled'),
                'priority': plan.get('priority', 'medium'),
                'description': plan.get('description', ''),
                'requirements': json.dumps(plan.get('requirements', {})),
                'code_changes': json.dumps(plan.get('code_changes', {})),
                'test_results': plan.get('test_results', ''),
                'created_at': plan.get('created_at'),
                'executed_at': plan.get('executed_at'),
                'merged_at': plan.get('merged_at'),
                'approval_id': plan.get('approval_id', '')
            }
            
            existing = db_manager.fetch_one(
                'SELECT plan_id FROM iteration_plans WHERE plan_id = ?',
                (plan['plan_id'],)
            )
            
            if existing:
                db_manager.update(
                    'iteration_plans',
                    {k: v for k, v in plan_data.items() if k != 'plan_id'},
                    'plan_id = ?',
                    (plan['plan_id'],)
                )
            else:
                db_manager.insert('iteration_plans', plan_data)
                
            logger.info(f"[迭代引擎] 保存迭代计划成功: {plan['plan_id']}")
        except Exception as e:
            logger.error(f"[迭代引擎] 保存迭代计划失败: {e}")
    
    def _save_runtime_analysis(self, plan_id: str, issues: List[Dict]):
        """保存运行时分析"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            for issue in issues:
                cursor.execute('''
                    INSERT INTO runtime_analysis (plan_id, metric_type, metric_name, 
                        value, threshold, status, recommendation, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    plan_id,
                    issue.get('type', ''),
                    issue.get('title', ''),
                    1.0 if issue['severity'] in ['high', 'critical'] else 0.5,
                    0.8,
                    'warning' if issue['severity'] in ['high', 'critical'] else 'normal',
                    issue.get('recommendation', ''),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[迭代引擎] 保存运行时分析失败: {e}")
    
    def _save_code_analysis(self, plan_id: str, file_path: str, 
                           complexity: int, loc: int, duplicate_score: float):
        """保存代码分析"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO code_analysis (plan_id, file_path, complexity, 
                    lines_of_code, duplicate_score, outdated_score, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                plan_id,
                file_path,
                complexity,
                loc,
                duplicate_score,
                duplicate_score * 0.5,
                '考虑优化' if complexity > 30 or loc > 500 else ''
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[迭代引擎] 保存代码分析失败: {e}")
    
    def get_iteration_plans(self) -> List[Dict]:
        """获取迭代计划"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM iteration_plans ORDER BY created_at DESC')
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'plan_id': row[0],
                    'status': row[1],
                    'iteration_type': row[2],
                    'priority': row[3],
                    'description': row[4],
                    'requirements': json.loads(row[5]) if row[5] else {},
                    'code_changes': json.loads(row[6]) if row[6] else {},
                    'test_results': json.loads(row[7]) if row[7] else {},
                    'created_at': row[8],
                    'executed_at': row[9],
                    'merged_at': row[10],
                    'approval_id': row[11]
                })
            
            conn.close()
            return results
        
        except Exception as e:
            logger.error(f"[迭代引擎] 获取迭代计划失败: {e}")
            return []


def get_iteration_engine() -> IterationEngine:
    """获取迭代引擎单例"""
    return IterationEngine()


def init_iteration_engine():
    """初始化迭代引擎"""
    engine = get_iteration_engine()
    logger.info("[迭代引擎] 主动迭代引擎初始化完成")
    return engine