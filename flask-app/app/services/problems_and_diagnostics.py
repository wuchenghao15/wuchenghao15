# -*- coding: utf-8 -*-
"""
问题诊断服务
提供系统健康检查、问题检测、诊断报告等功能
整合到自动迭代更新流程中
"""

import os
import sys
import json
import sqlite3
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.logging import logger


@dataclass
class ProblemDiagnosis:
    """问题诊断结果"""
    problem_id: str
    severity: str
    category: str
    title: str
    description: str
    recommendation: str
    status: str = 'detected'
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: Optional[str] = None
    resolution: Optional[str] = None


class ProblemsAndDiagnosticsService:
    """问题诊断服务"""
    
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
        
        self._db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'app.db'
        )
        self._problems: List[ProblemDiagnosis] = []
        self._health_check_interval = 3600
        self._db_retry_max = 5
        self._db_retry_delay = 2.0
        
        self._init_database()
        self._load_existing_problems()
        self._start_health_check_thread()
        
        logger.info("[问题诊断服务] 初始化完成")
        self._initialized = True
    
    def _execute_with_retry(self, func, *args, **kwargs):
        """带重试机制的数据库操作"""
        for attempt in range(self._db_retry_max):
            try:
                return func(*args, **kwargs)
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e) and attempt < self._db_retry_max - 1:
                    logger.warning(f"[问题诊断服务] 数据库锁定，第 {attempt + 1} 次重试...")
                    time.sleep(self._db_retry_delay * (attempt + 1))
                else:
                    raise
        raise sqlite3.OperationalError("数据库锁定，重试次数已用完")
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_problems (
                    problem_id TEXT PRIMARY KEY,
                    severity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    recommendation TEXT,
                    status TEXT DEFAULT 'detected',
                    detected_at TEXT NOT NULL,
                    resolved_at TEXT,
                    resolution TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_check_results (
                    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_type TEXT NOT NULL,
                    check_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pass',
                    message TEXT DEFAULT '',
                    timestamp TEXT NOT NULL,
                    details TEXT DEFAULT '{}'
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sp_severity ON system_problems(severity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sp_category ON system_problems(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sp_status ON system_problems(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hcr_check_type ON health_check_results(check_type)')
            
            conn.commit()
            conn.close()
            logger.info("[问题诊断服务] 数据库表初始化完成")
        except Exception as e:
            logger.error(f"[问题诊断服务] 初始化数据库失败: {e}")
    
    def _start_health_check_thread(self):
        """启动定时健康检查线程"""
        def health_check_loop():
            while True:
                try:
                    self.run_health_check()
                except Exception as e:
                    logger.error(f"[问题诊断服务] 健康检查失败: {e}")
                time.sleep(self._health_check_interval)
        
        thread = threading.Thread(target=health_check_loop, daemon=True)
        thread.start()
        logger.info(f"[问题诊断服务] 健康检查线程已启动，间隔: {self._health_check_interval}秒")
    
    def _load_existing_problems(self):
        """加载已存在的问题"""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM system_problems WHERE status = 'detected'")
            rows = cursor.fetchall()
            
            for row in rows:
                problem = ProblemDiagnosis(
                    problem_id=row['problem_id'],
                    severity=row['severity'],
                    category=row['category'],
                    title=row['title'],
                    description=row['description'],
                    recommendation=row['recommendation'],
                    status=row['status'],
                    detected_at=row['detected_at'],
                    resolved_at=row['resolved_at'],
                    resolution=row['resolution']
                )
                self._problems.append(problem)
            
            conn.close()
            logger.info(f"[问题诊断服务] 加载了 {len(self._problems)} 个待处理问题")
        except Exception as e:
            logger.error(f"[问题诊断服务] 加载问题失败: {e}")
    
    def detect_problems(self) -> List[ProblemDiagnosis]:
        """检测系统问题"""
        problems = []
        
        problems.extend(self._check_database_health())
        problems.extend(self._check_component_health())
        problems.extend(self._check_configuration_health())
        problems.extend(self._check_performance_health())
        problems.extend(self._check_security_health())
        
        for problem in problems:
            self._add_problem(problem)
        
        return problems
    
    def _check_database_health(self) -> List[ProblemDiagnosis]:
        """检查数据库健康状况"""
        problems = []
        
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            if integrity != 'ok':
                problems.append(ProblemDiagnosis(
                    problem_id=f"db_integrity_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    severity='critical',
                    category='database',
                    title='数据库完整性检查失败',
                    description=f"数据库完整性检查结果: {integrity}",
                    recommendation='立即备份数据库并修复损坏'
                ))
            
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            critical_tables = [
                'users', 'roles', 'permissions', 'exam_results', 'questions',
                'iteration_plans', 'ai_employees', 'approvals'
            ]
            
            try:
                from app.utils.table_encryption import table_encryption
                
                for table in critical_tables:
                    encrypted_name = table_encryption.encrypt_table_name(table)
                    
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                    plain_exists = cursor.fetchone()
                    
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (encrypted_name,))
                    encrypted_exists = cursor.fetchone()
                    
                    if not plain_exists and not encrypted_exists:
                        problems.append(ProblemDiagnosis(
                            problem_id=f"db_missing_table_{table}",
                            severity='high',
                            category='database',
                            title=f'关键表 {table} 缺失',
                            description=f"系统运行必需的表 {table} (加密为 {encrypted_name}) 不存在",
                            recommendation=f'创建缺失的表 {table}'
                        ))
                    elif plain_exists and encrypted_exists:
                        problems.append(ProblemDiagnosis(
                            problem_id=f"db_duplicate_table_{table}",
                            severity='warning',
                            category='database',
                            title=f'表 {table} 同时存在明文和加密版本',
                            description=f"表 {table} 同时存在明文版本和加密版本({encrypted_name})",
                            recommendation='清理重复表，保持一致性'
                        ))
            except Exception as e:
                logger.warning(f"[问题诊断服务] 表名加密检查失败: {e}")
                
                for table in critical_tables:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                    if not cursor.fetchone():
                        problems.append(ProblemDiagnosis(
                            problem_id=f"db_missing_table_{table}",
                            severity='medium',
                            category='database',
                            title=f'关键表 {table} 缺失(未加密检查)',
                            description=f"系统运行必需的表 {table} 不存在",
                            recommendation=f'创建缺失的表 {table}'
                        ))
            
            conn.close()
        except Exception as e:
            problems.append(ProblemDiagnosis(
                problem_id=f"db_connection_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                severity='critical',
                category='database',
                title='数据库连接失败',
                description=f"无法连接到数据库: {str(e)}",
                recommendation='检查数据库连接配置和文件权限'
            ))
        
        return problems
    
    def _check_component_health(self) -> List[ProblemDiagnosis]:
        """检查组件健康状况"""
        problems = []
        
        components = [
            ('迭代规则引擎', 'app.agents.iteration_rules', 'IterationConfig'),
            ('迭代引擎', 'app.agents.iteration_engine', 'IterationEngine'),
            ('AI员工增强系统', 'app.ai.ai_employee_enhanced_system', 'AIEmployeeAutoGenerator'),
            ('审批管理器', 'app.agents.approval_manager', 'ApprovalManager'),
            ('测试运行器', 'app.agents.auto_test_runner', 'AutoTestRunner'),
            ('Git自动操作', 'app.agents.git_auto_ops', 'GitAutoOps'),
            ('依赖扫描器', 'app.agents.dependency_scanner', 'DependencyScanner'),
            ('运维报告生成器', 'app.agents.ops_report_generator', 'OpsReportGenerator'),
            ('版本更新服务', 'app.services.auto_version_updater', 'AutoVersionUpdater')
        ]
        
        for name, module_path, class_name in components:
            try:
                mod = __import__(module_path, fromlist=[class_name])
                getattr(mod, class_name)
            except Exception as e:
                problems.append(ProblemDiagnosis(
                    problem_id=f"component_{module_path.replace('.', '_')}",
                    severity='high',
                    category='component',
                    title=f'{name} 加载失败',
                    description=f"组件 {name} ({module_path}) 无法正常加载: {str(e)}",
                    recommendation=f'检查组件 {name} 的代码和依赖'
                ))
        
        return problems
    
    def _check_configuration_health(self) -> List[ProblemDiagnosis]:
        """检查配置健康状况"""
        problems = []
        
        config_checks = [
            ('TABLE_ENCRYPTION_KEY', os.environ.get('TABLE_ENCRYPTION_KEY'), 'warning'),
            ('SECRET_KEY', os.environ.get('SECRET_KEY'), 'high'),
            ('FLASK_APP', os.environ.get('FLASK_APP'), 'medium'),
            ('FLASK_ENV', os.environ.get('FLASK_ENV'), 'medium')
        ]
        
        for name, value, severity in config_checks:
            if not value:
                problems.append(ProblemDiagnosis(
                    problem_id=f"config_missing_{name}",
                    severity=severity,
                    category='configuration',
                    title=f'环境变量 {name} 缺失',
                    description=f"系统配置必需的环境变量 {name} 未设置",
                    recommendation=f'设置环境变量 {name}'
                ))
        
        try:
            from app.agents.iteration_rules import IterationConfig
            config = IterationConfig()
            
            if len(config.AI_EMPLOYEE_ROLES) == 0:
                problems.append(ProblemDiagnosis(
                    problem_id="config_no_employees",
                    severity='high',
                    category='configuration',
                    title='AI员工配置为空',
                    description='迭代规则中未配置任何AI员工',
                    recommendation='在iteration_rules.py中配置AI员工角色'
                ))
            
            enabled_cycles = [k for k, v in config.ITERATION_CYCLES.items() if v.get('enabled')]
            if len(enabled_cycles) == 0:
                problems.append(ProblemDiagnosis(
                    problem_id="config_no_cycles",
                    severity='medium',
                    category='configuration',
                    title='迭代周期未启用',
                    description='所有迭代周期都已禁用',
                    recommendation='启用至少一个迭代周期'
                ))
            
        except Exception as e:
            problems.append(ProblemDiagnosis(
                problem_id="config_iteration_load",
                severity='high',
                category='configuration',
                title='迭代规则配置加载失败',
                description=f"无法加载迭代规则配置: {str(e)}",
                recommendation='检查iteration_rules.py文件'
            ))
        
        return problems
    
    def _check_performance_health(self) -> List[ProblemDiagnosis]:
        """检查性能健康状况"""
        problems = []
        
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                problems.append(ProblemDiagnosis(
                    problem_id=f"perf_cpu_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    severity='warning',
                    category='performance',
                    title='CPU使用率过高',
                    description=f"当前CPU使用率: {cpu_percent}%",
                    recommendation='检查是否有异常进程占用CPU资源'
                ))
            
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                problems.append(ProblemDiagnosis(
                    problem_id=f"perf_memory_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    severity='warning',
                    category='performance',
                    title='内存使用率过高',
                    description=f"当前内存使用率: {memory.percent}%",
                    recommendation='释放缓存或增加系统内存'
                ))
            
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                problems.append(ProblemDiagnosis(
                    problem_id=f"perf_disk_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    severity='high',
                    category='performance',
                    title='磁盘空间不足',
                    description=f"当前磁盘使用率: {disk.percent}%",
                    recommendation='清理磁盘空间'
                ))
            
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"[问题诊断服务] 性能检查失败: {e}")
        
        return problems
    
    def _check_security_health(self) -> List[ProblemDiagnosis]:
        """检查安全健康状况"""
        problems = []
        
        try:
            from app.agents.iteration_rules import IterationConfig
            config = IterationConfig()
            
            for emp_type, emp_config in config.AI_EMPLOYEE_ROLES.items():
                if not emp_config.get('enabled', True):
                    problems.append(ProblemDiagnosis(
                        problem_id=f"security_disabled_{emp_type}",
                        severity='medium',
                        category='security',
                        title=f'AI员工 {emp_config.get("name", emp_type)} 已禁用',
                        description=f"安全相关的AI员工 {emp_config.get('name', emp_type)} 被禁用",
                        recommendation=f'考虑启用 {emp_config.get("name", emp_type)} AI员工'
                    ))
            
        except Exception as e:
            logger.warning(f"[问题诊断服务] 安全检查失败: {e}")
        
        return problems
    
    def _add_problem(self, problem: ProblemDiagnosis):
        """添加问题到数据库"""
        def _do_add():
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO system_problems
                (problem_id, severity, category, title, description, 
                 recommendation, status, detected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                problem.problem_id,
                problem.severity,
                problem.category,
                problem.title,
                problem.description,
                problem.recommendation,
                problem.status,
                problem.detected_at
            ))
            
            conn.commit()
            conn.close()
            
            if problem.problem_id not in [p.problem_id for p in self._problems]:
                self._problems.append(problem)
            
            logger.info(f"[问题诊断服务] 检测到问题: {problem.title} ({problem.severity})")
        
        try:
            self._execute_with_retry(_do_add)
        except Exception as e:
            logger.error(f"[问题诊断服务] 添加问题失败: {e}")
    
    def resolve_problem(self, problem_id: str, resolution: str) -> bool:
        """标记问题为已解决"""
        def _do_resolve():
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE system_problems 
                SET status = 'resolved', 
                    resolution = ?, 
                    resolved_at = ?
                WHERE problem_id = ?
            ''', (resolution, datetime.now().isoformat(), problem_id))
            
            conn.commit()
            conn.close()
            
            for problem in self._problems:
                if problem.problem_id == problem_id:
                    problem.status = 'resolved'
                    problem.resolution = resolution
                    problem.resolved_at = datetime.now().isoformat()
                    break
            
            logger.info(f"[问题诊断服务] 问题 {problem_id} 已解决")
        
        try:
            self._execute_with_retry(_do_resolve)
            return True
        except Exception as e:
            logger.error(f"[问题诊断服务] 解决问题失败: {e}")
            return False
    
    def get_problems(self, severity: str = '', category: str = '', 
                     status: str = '') -> List[ProblemDiagnosis]:
        """获取问题列表"""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM system_problems WHERE 1=1"
            params = []
            
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            if category:
                query += " AND category = ?"
                params.append(category)
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY detected_at DESC"
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            problems = []
            for row in rows:
                problems.append(ProblemDiagnosis(
                    problem_id=row['problem_id'],
                    severity=row['severity'],
                    category=row['category'],
                    title=row['title'],
                    description=row['description'],
                    recommendation=row['recommendation'],
                    status=row['status'],
                    detected_at=row['detected_at'],
                    resolved_at=row['resolved_at'],
                    resolution=row['resolution']
                ))
            
            conn.close()
            return problems
        except Exception as e:
            logger.error(f"[问题诊断服务] 获取问题列表失败: {e}")
            return []
    
    def run_health_check(self) -> Dict:
        """运行健康检查"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'checks': [],
            'summary': {
                'pass': 0,
                'warning': 0,
                'fail': 0
            }
        }
        
        check_types = [
            ('database', '数据库连接', self._check_db_connection),
            ('database', '数据库完整性', self._check_db_integrity),
            ('component', '迭代引擎', self._check_iteration_engine),
            ('component', 'AI员工系统', self._check_ai_employee_system),
            ('configuration', '环境变量', self._check_env_vars),
            ('performance', '系统资源', self._check_system_resources)
        ]
        
        for check_type, check_name, check_func in check_types:
            try:
                result = check_func()
                results['checks'].append({
                    'type': check_type,
                    'name': check_name,
                    'status': result['status'],
                    'message': result.get('message', '')
                })
                results['summary'][result['status']] += 1
            except Exception as e:
                results['checks'].append({
                    'type': check_type,
                    'name': check_name,
                    'status': 'fail',
                    'message': f'检查失败: {str(e)}'
                })
                results['summary']['fail'] += 1
        
        self._save_health_check_result(results)
        
        if results['summary']['fail'] > 0:
            logger.warning(f"[问题诊断服务] 健康检查发现 {results['summary']['fail']} 个失败项")
        else:
            logger.info(f"[问题诊断服务] 健康检查通过: {results['summary']['pass']} 项通过")
        
        return results
    
    def _check_db_connection(self) -> Dict:
        """检查数据库连接"""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return {'status': 'pass', 'message': '数据库连接正常'}
        except Exception as e:
            return {'status': 'fail', 'message': f'数据库连接失败: {str(e)}'}
    
    def _check_db_integrity(self) -> Dict:
        """检查数据库完整性"""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            conn.close()
            if result == 'ok':
                return {'status': 'pass', 'message': '数据库完整性检查通过'}
            else:
                return {'status': 'fail', 'message': f'数据库完整性检查失败: {result}'}
        except Exception as e:
            return {'status': 'fail', 'message': f'数据库完整性检查失败: {str(e)}'}
    
    def _check_iteration_engine(self) -> Dict:
        """检查迭代引擎"""
        try:
            from app.agents.iteration_engine import get_iteration_engine
            engine = get_iteration_engine()
            plans = engine.get_iteration_plans()
            return {'status': 'pass', 'message': f'迭代引擎正常，已执行 {len(plans)} 个计划'}
        except Exception as e:
            return {'status': 'fail', 'message': f'迭代引擎异常: {str(e)}'}
    
    def _check_ai_employee_system(self) -> Dict:
        """检查AI员工系统"""
        try:
            from app.ai.ai_employee_enhanced_system import AIEmployeeAutoGenerator
            gen = AIEmployeeAutoGenerator()
            return {'status': 'pass', 'message': f'AI员工系统正常，共 {len(gen.EMPLOYEE_TEMPLATES)} 个模板'}
        except Exception as e:
            return {'status': 'fail', 'message': f'AI员工系统异常: {str(e)}'}
    
    def _check_env_vars(self) -> Dict:
        """检查环境变量"""
        critical_vars = ['SECRET_KEY', 'FLASK_APP']
        missing = [v for v in critical_vars if not os.environ.get(v)]
        if missing:
            return {'status': 'warning', 'message': f'缺失关键环境变量: {", ".join(missing)}'}
        else:
            return {'status': 'pass', 'message': '关键环境变量齐全'}
    
    def _check_system_resources(self) -> Dict:
        """检查系统资源"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 80 or memory_percent > 85:
                return {'status': 'warning', 
                        'message': f'资源使用率偏高 - CPU: {cpu_percent}%, 内存: {memory_percent}%'}
            else:
                return {'status': 'pass', 
                        'message': f'资源使用正常 - CPU: {cpu_percent}%, 内存: {memory_percent}%'}
        except ImportError:
            return {'status': 'pass', 'message': 'psutil未安装，跳过资源检查'}
        except Exception as e:
            return {'status': 'warning', 'message': f'资源检查失败: {str(e)}'}
    
    def _save_health_check_result(self, results: Dict):
        """保存健康检查结果"""
        def _do_save():
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            for check in results['checks']:
                cursor.execute('''
                    INSERT INTO health_check_results
                    (check_type, check_name, status, message, timestamp, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    check['type'],
                    check['name'],
                    check['status'],
                    check['message'],
                    results['timestamp'],
                    json.dumps(results['summary'])
                ))
            
            conn.commit()
            conn.close()
        
        try:
            self._execute_with_retry(_do_save)
        except Exception as e:
            logger.error(f"[问题诊断服务] 保存健康检查结果失败: {e}")
    
    def get_health_check_history(self, limit: int = 20) -> List[Dict]:
        """获取健康检查历史"""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM health_check_results
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'check_id': row['check_id'],
                    'check_type': row['check_type'],
                    'check_name': row['check_name'],
                    'status': row['status'],
                    'message': row['message'],
                    'timestamp': row['timestamp'],
                    'details': json.loads(row['details']) if row['details'] else {}
                })
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"[问题诊断服务] 获取健康检查历史失败: {e}")
            return []
    
    def get_diagnostic_report(self) -> Dict:
        """获取诊断报告"""
        problems = self.get_problems()
        health_check = self.run_health_check()
        
        severity_counts = {}
        category_counts = {}
        status_counts = {}
        
        for problem in problems:
            severity_counts[problem.severity] = severity_counts.get(problem.severity, 0) + 1
            category_counts[problem.category] = category_counts.get(problem.category, 0) + 1
            status_counts[problem.status] = status_counts.get(problem.status, 0) + 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'problems': {
                'total': len(problems),
                'by_severity': severity_counts,
                'by_category': category_counts,
                'by_status': status_counts,
                'recent_problems': [p.__dict__ for p in problems[:10]]
            },
            'health_check': health_check,
            'system_status': 'healthy' if health_check['summary']['fail'] == 0 else 'unhealthy'
        }


def get_problems_and_diagnostics_service() -> ProblemsAndDiagnosticsService:
    """获取问题诊断服务单例"""
    return ProblemsAndDiagnosticsService()


def init_problems_and_diagnostics():
    """初始化问题诊断服务"""
    service = get_problems_and_diagnostics_service()
    logger.info("[问题诊断服务] 问题诊断服务初始化完成")
    return service


def run_powerful_diagnostic_fix() -> Dict:
    """运行强力诊断修复 - 检测问题并自动修复"""
    logger.info("[问题诊断服务] 开始强力诊断修复流程...")
    
    diagnostics = get_problems_and_diagnostics_service()
    
    logger.info("[问题诊断服务] 步骤1: 检测系统问题")
    detected_problems = diagnostics.detect_problems()
    
    if not detected_problems:
        logger.info("[问题诊断服务] 未检测到任何问题")
        return {
            'success': True,
            'message': '系统健康，未检测到需要修复的问题',
            'problems_detected': 0,
            'problems_fixed': 0,
            'system_status': 'healthy'
        }
    
    logger.info(f"[问题诊断服务] 检测到 {len(detected_problems)} 个问题")
    
    for problem in detected_problems:
        logger.info(f"  - [{problem.severity.upper()}] {problem.category}: {problem.title}")
    
    logger.info("[问题诊断服务] 步骤2: 启动AI任务调度器进行修复")
    from app.ai.ai_task_scheduler import get_ai_task_scheduler
    
    scheduler = get_ai_task_scheduler()
    
    problems_data = [p.__dict__ for p in detected_problems]
    fix_result = scheduler.submit_problems_for_fix(problems_data)
    
    logger.info(f"[问题诊断服务] 步骤3: 提交修复任务，任务ID: {fix_result.get('task_ids', [])}")
    
    logger.info("[问题诊断服务] 步骤4: 启动调度器执行修复...")
    scheduler.start_scheduler()
    
    import time
    time.sleep(8)
    
    logger.info("[问题诊断服务] 步骤5: 获取修复结果")
    tasks = scheduler.get_all_tasks()
    
    completed_tasks = [t for t in tasks if t['status'] == 'completed']
    successful_tasks = [t for t in completed_tasks if t['success']]
    failed_tasks = [t for t in completed_tasks if not t['success']]
    
    logger.info(f"[问题诊断服务] 修复完成:")
    logger.info(f"  - 总任务数: {len(tasks)}")
    logger.info(f"  - 成功修复: {len(successful_tasks)}")
    logger.info(f"  - 修复失败: {len(failed_tasks)}")
    
    logger.info("[问题诊断服务] 步骤6: 更新问题状态")
    for task in completed_tasks:
        diagnostics.resolve_problem(
            task['problem_id'],
            task['fix_result'] if task['success'] else f"修复失败: {task['fix_result']}"
        )
    
    logger.info("[问题诊断服务] 步骤7: 生成修复报告")
    repair_reports = scheduler.get_repair_reports()
    
    logger.info("[问题诊断服务] 步骤8: 验证修复结果")
    health_check = diagnostics.run_health_check()
    
    system_status = 'healthy' if health_check['summary']['fail'] == 0 else 'unhealthy'
    
    logger.info(f"[问题诊断服务] 强力诊断修复完成，系统状态: {system_status}")
    
    return {
        'success': True,
        'message': f"强力诊断修复完成，共检测 {len(detected_problems)} 个问题，成功修复 {len(successful_tasks)} 个",
        'problems_detected': len(detected_problems),
        'problems_fixed': len(successful_tasks),
        'problems_failed': len(failed_tasks),
        'system_status': system_status,
        'health_check': health_check,
        'repair_reports_count': len(repair_reports),
        'task_ids': fix_result.get('task_ids', []),
        'scheduler_status': scheduler.get_scheduler_status()
    }
