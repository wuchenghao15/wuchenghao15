# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI Cluster Manager
Manages AI clusters and employees with unified control, monitoring, and upgrading capabilities
Supports database persistence for cluster and employee configurations
"""

import os
import sys
import time
import json
import threading
import logging
import sqlite3
import typing
from contextlib import contextmanager
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('ai_cluster_manager.log'), logging.StreamHandler()])
logger = logging.getLogger('AI_Cluster_Manager')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app.db')

@contextmanager
def get_db_connection():
    """Database connection context manager"""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.close()

DATABASE_VERSION = 2

def init_cluster_database():

    """Initialize database tables for cluster and employee configuration with migration support"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''

                CREATE TABLE IF NOT EXISTS ai_cluster_config (
                    cluster_id TEXT PRIMARY KEY,
                    cluster_type TEXT NOT NULL,
                    config TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')


            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_employee_config (
                    employee_id TEXT PRIMARY KEY,
                    employee_type TEXT NOT NULL,
                    capabilities TEXT DEFAULT '[]',
                    config TEXT DEFAULT '{}',
                    assigned_cluster TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_cluster_employee (
                    cluster_id TEXT,
                    employee_id TEXT,
                    FOREIGN KEY (cluster_id) REFERENCES ai_cluster_config(cluster_id),
                    FOREIGN KEY (employee_id) REFERENCES ai_employee_config(employee_id),
                    PRIMARY KEY (cluster_id, employee_id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_config_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_type TEXT NOT NULL,
                    config_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    operator TEXT DEFAULT 'system',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_config_snapshot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_name TEXT NOT NULL,
                    snapshot_data TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    operator TEXT DEFAULT 'system'
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_database_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_model_config (
                    model_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    api_key TEXT DEFAULT '',
                    endpoint TEXT DEFAULT '',
                    parameters TEXT DEFAULT '{}',
                    performance_metrics TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'active',
                    version TEXT DEFAULT '1.0',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_model_endpoints (
                    endpoint_id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    method TEXT DEFAULT 'POST',
                    headers TEXT DEFAULT '{}',
                    timeout INTEGER DEFAULT 30,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (model_id) REFERENCES ai_model_config(model_id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    latency REAL DEFAULT 0.0,
                    throughput REAL DEFAULT 0.0,
                    accuracy REAL DEFAULT 0.0,
                    error_rate REAL DEFAULT 0.0,
                    requests_count INTEGER DEFAULT 0,
                    FOREIGN KEY (model_id) REFERENCES ai_model_config(model_id)
                )
            ''')

            cursor.execute('SELECT version FROM ai_database_version ORDER BY version DESC LIMIT 1')
            row = cursor.fetchone()
            current_version = row[0] if row else 0

            if current_version < DATABASE_VERSION:
                logger.info(f"数据库版本升级: {current_version} -> {DATABASE_VERSION}")
                _run_database_migrations(conn, cursor, current_version)

            conn.commit()

        logger.info("AI集群配置数据库表初始化完成")
    except Exception as e:
        logger.error(f"初始化集群配置数据库失败: {str(e)}")

def _run_database_migrations(conn, cursor, current_version):
    """Run database migrations from current version to latest"""
    migrations = [
        {
            'version': 1,
            'description': 'Initial schema',
            'operations': []
        },
        {
            'version': 2,
            'description': 'Add snapshot table and version tracking',
            'operations': [
                '''CREATE TABLE IF NOT EXISTS ai_config_snapshot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_name TEXT NOT NULL,
                    snapshot_data TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    operator TEXT DEFAULT 'system'
                )''',
                '''CREATE TABLE IF NOT EXISTS ai_database_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )'''
            ]
        }
    ]

    for migration in migrations:
        if migration['version'] > current_version:
            logger.info(f"应用迁移版本 {migration['version']}: {migration['description']}")
            for operation in migration['operations']:
                cursor.execute(operation)
            
            cursor.execute('''
                INSERT OR REPLACE INTO ai_database_version (version, description)
                VALUES (?, ?)
            ''', (migration['version'], migration['description']))
            conn.commit()
            logger.info(f"迁移版本 {migration['version']} 应用完成")

class AIEmployee:
    """AI Employee class represents an individual AI worker with specific capabilities"""

    def __init__(self, employee_id: str, employee_type: str, capabilities: List[str], config: Optional[Dict] = None):
        self.employee_id = employee_id
        self.employee_type = employee_type
        self.capabilities = capabilities
        self.config = config or {}
        self.status = "active"
        self.last_heartbeat = time.time()
        self.performance_metrics = {
            'tasks_completed': 0,
            'success_rate': 1.0,
            'average_response_time': 0.0,
            'last_task_time': 0.0
        }
        self.current_task = None
        self.assigned_cluster = None

        logger.info(f"Created AI Employee: {employee_id} ({employee_type})")

    def update_status(self, status: str, metrics: Optional[Dict] = None):
        """Update employee status and performance metrics"""
        self.status = status
        self.last_heartbeat = time.time()
        if metrics:
            for key, value in metrics.items():
                if key in self.performance_metrics:
                    self.performance_metrics[key] = value

        logger.debug(f"Updated status for {self.employee_id}: {status}")

    def assign_task(self, task: Dict[str, Any]) -> bool:
        """Assign a task to the employee"""
        if self.status != "active":
            logger.warning(f"Cannot assign task to {self.employee_id}: not active")
            return False

        self.current_task = task
        self.update_status("busy")
        logger.info(f"Assigned task to {self.employee_id}: {task['task_id']}")
        return True

    def complete_task(self, result: Dict[str, Any]) -> bool:
        """Complete the current task"""
        if not self.current_task:
            logger.warning(f"No current task for {self.employee_id}")
            return False

        task_id = self.current_task['task_id']
        self.performance_metrics['tasks_completed'] += 1

        if result.get('success', False):
            total = self.performance_metrics['tasks_completed']
            current_success = self.performance_metrics['success_rate'] * (total - 1)
            self.performance_metrics['success_rate'] = (current_success + 1) / total

        self.current_task = None
        self.update_status("active")
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get employee status"""
        return {
            'employee_id': self.employee_id,
            'employee_type': self.employee_type,
            'capabilities': self.capabilities,
            'status': self.status,
            'last_heartbeat': self.last_heartbeat,
            'performance_metrics': self.performance_metrics,
            'current_task': self.current_task,
            'assigned_cluster': self.assigned_cluster,
            'config': self.config
        }

    def upgrade(self, upgrade_data: Optional[Dict] = None) -> bool:
        """Upgrade the employee's capabilities"""
        try:
            logger.info(f"Upgrading AI Employee: {self.employee_id}")
            self.update_status("upgrading")

            time.sleep(1)

            if upgrade_data:
                if 'capabilities' in upgrade_data:
                    self.capabilities.extend(upgrade_data['capabilities'])
                    self.capabilities = list(set(self.capabilities))

                if 'config' in upgrade_data:
                    self.config.update(upgrade_data['config'])

            self.update_status("active")
            logger.info(f"Successfully upgraded AI Employee: {self.employee_id}")
            return True
        except Exception as e:
            self.update_status("error")
            logger.error(f"Failed to upgrade {self.employee_id}: {str(e)}")
            return False

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to database dict"""
        return {
            'employee_id': self.employee_id,
            'employee_type': self.employee_type,
            'capabilities': json.dumps(self.capabilities),
            'config': json.dumps(self.config),
            'assigned_cluster': self.assigned_cluster,
            'status': self.status
        }


class AICluster:
    """AI Cluster class manages a group of AI employees"""

    def __init__(self, cluster_id: str, cluster_type: str, config: Optional[Dict] = None):
        self.cluster_id = cluster_id
        self.cluster_type = cluster_type
        self.config = config or {}
        self.status = "active"
        self.created_at = time.time()
        self.last_updated = time.time()
        self.employees: Dict[str, AIEmployee] = {}
        self.task_queue: List[Dict] = []
        self.lock = threading.RLock()

        logger.info(f"Created AI Cluster: {cluster_id} ({cluster_type})")

    def add_employee(self, employee: AIEmployee) -> bool:
        """Add an employee to the cluster"""
        with self.lock:
            if employee.employee_id in self.employees:
                logger.warning(f"Employee {employee.employee_id} already in cluster {self.cluster_id}")
                return False

            self.employees[employee.employee_id] = employee
            employee.assigned_cluster = self.cluster_id
            self.last_updated = time.time()
            logger.info(f"Added employee {employee.employee_id} to cluster {self.cluster_id}")
            return True

    def remove_employee(self, employee_id: str) -> bool:
        """Remove an employee from the cluster"""
        with self.lock:
            if employee_id not in self.employees:
                logger.warning(f"Employee {employee_id} not in cluster {self.cluster_id}")
                return False

            employee = self.employees[employee_id]
            employee.assigned_cluster = None
            del self.employees[employee_id]
            logger.info(f"Removed employee {employee_id} from cluster {self.cluster_id}")
            return True

    def assign_task(self, task: Dict[str, Any]) -> bool:
        """Assign a task to the cluster"""
        with self.lock:
            required_capability = task.get('required_capability')

            for employee in self.employees.values():
                if employee.status == "active" and (not required_capability or required_capability in employee.capabilities):
                    return employee.assign_task(task)

            self.task_queue.append(task)
            return True

    def get_status(self) -> Dict[str, Any]:
        """Get cluster status"""
        with self.lock:
            employee_statuses = {}
            for employee_id, employee in self.employees.items():
                employee_statuses[employee_id] = employee.get_status()

            return {
                'cluster_id': self.cluster_id,
                'cluster_type': self.cluster_type,
                'config': self.config,
                'status': self.status,
                'created_at': self.created_at,
                'last_updated': self.last_updated,
                'employees': employee_statuses,
                'task_queue_length': len(self.task_queue),
                'employee_count': len(self.employees)
            }

    def upgrade_employees(self, upgrade_data: Optional[Dict] = None) -> Dict[str, bool]:
        """Upgrade all employees in the cluster"""
        with self.lock:
            results = {}
            for employee_id, employee in self.employees.items():
                results[employee_id] = employee.upgrade(upgrade_data)
            return results

    def update_status(self, status: str) -> bool:
        """Update cluster status"""
        with self.lock:
            self.status = status
            self.last_updated = time.time()

            if status != "active":
                for employee in self.employees.values():
                    employee.update_status(status)
            logger.info(f"Updated cluster {self.cluster_id} status: {status}")
            return True

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to database dict"""
        return {
            'cluster_id': self.cluster_id,
            'cluster_type': self.cluster_type,
            'config': json.dumps(self.config),
            'status': self.status
        }


class AIClusterManager:
    """Main AI Cluster Manager that handles all clusters and employees with database persistence"""
    
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.clusters: Dict[str, AICluster] = {}
        self.employees: Dict[str, AIEmployee] = {}
        self.lock = threading.RLock()
        self.monitoring_enabled = True
        self.auto_upgrade_enabled = True
        self.auto_extend_enabled = True
        self.auto_onboard_enabled = True
        self.monitoring_interval = 60
        self.upgrade_interval = 3600
        self.auto_extend_interval = 3600
        self.last_auto_extend_time = time.time()

        init_cluster_database()
        self._load_from_database()
        self._start_monitoring_thread()
        
        self._initialized = True

    def _load_from_database(self):
        """Load clusters and employees from database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM ai_cluster_config')
                for row in cursor.fetchall():
                    cluster_id, cluster_type, config_str, status, created_at, updated_at = row
                    config = json.loads(config_str) if config_str else {}
                    cluster = AICluster(cluster_id, cluster_type, config)
                    cluster.status = status
                    if created_at:
                        cluster.created_at = float(created_at) if created_at.replace('.', '').isdigit() else time.time()
                    if updated_at:
                        cluster.last_updated = float(updated_at) if updated_at.replace('.', '').isdigit() else time.time()
                    self.clusters[cluster_id] = cluster

                cursor.execute('SELECT * FROM ai_employee_config')
                for row in cursor.fetchall():
                    employee_id, employee_type, capabilities_str, config_str, assigned_cluster, status, created_at, updated_at = row
                    capabilities = json.loads(capabilities_str) if capabilities_str else []
                    config = json.loads(config_str) if config_str else {}
                    employee = AIEmployee(employee_id, employee_type, capabilities, config)
                    employee.status = status
                    employee.assigned_cluster = assigned_cluster
                    self.employees[employee_id] = employee

                    if assigned_cluster and assigned_cluster in self.clusters:
                        self.clusters[assigned_cluster].add_employee(employee)

            logger.info(f"从数据库加载完成: {len(self.clusters)} 个集群, {len(self.employees)} 个员工")
            
            self._ensure_all_employees_assigned()
            
            if len(self.clusters) == 0 and len(self.employees) == 0:
                logger.info("数据库为空，初始化默认集群和员工...")
                self._initialize_defaults()
        except Exception as e:
            logger.error(f"从数据库加载配置失败: {str(e)}")
            self._initialize_defaults()

    def _save_to_database(self):
        """Save all clusters and employees to database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                for cluster in self.clusters.values():
                    data = cluster.to_db_dict()
                    data['updated_at'] = str(time.time())
                    cursor.execute('''
                        INSERT OR REPLACE INTO ai_cluster_config 
                        (cluster_id, cluster_type, config, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (data['cluster_id'], data['cluster_type'], data['config'], data['status'], str(cluster.created_at), data['updated_at']))

                for employee in self.employees.values():
                    data = employee.to_db_dict()
                    cursor.execute('''
                        INSERT OR REPLACE INTO ai_employee_config 
                        (employee_id, employee_type, capabilities, config, assigned_cluster, status, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (data['employee_id'], data['employee_type'], data['capabilities'], data['config'], data['assigned_cluster'], data['status'], str(time.time())))

                cursor.execute('DELETE FROM ai_cluster_employee')
                for cluster in self.clusters.values():
                    for employee_id in cluster.employees.keys():
                        cursor.execute('''
                            INSERT INTO ai_cluster_employee (cluster_id, employee_id)
                            VALUES (?, ?)
                        ''', (cluster.cluster_id, employee_id))

                conn.commit()

            logger.info(f"保存到数据库完成: {len(self.clusters)} 个集群, {len(self.employees)} 个员工")
        except Exception as e:
            logger.error(f"保存到数据库失败: {str(e)}")

    def _initialize_defaults(self):
        """Initialize default clusters and employees if database is empty"""
        logger.info("初始化默认集群和员工...")
        self._create_default_clusters()
        self._create_default_employees()
        self._assign_default_employees()
        self._initialize_default_models()
        self._save_to_database()

    def _create_default_clusters(self):
        """Create default clusters"""
        default_clusters = [
            ('api_cluster', 'api_management'),
            ('frontend_cluster', 'frontend_development'),
            ('backend_cluster', 'backend_development'),
            ('database_cluster', 'database_management'),
            ('security_cluster', 'security_management'),
            ('middleware_cluster', 'middleware_management'),
            ('logging_cluster', 'log_management'),
            ('ai_education_cluster', 'ai_education'),
            ('ai_question_bank_cluster', 'ai_question_bank'),
            ('ai_analysis_cluster', 'ai_analysis'),
            ('ai_tutor_cluster', 'ai_tutor'),
            ('ai_code_cluster', 'ai_code_generation'),
            ('ai_image_cluster', 'ai_image_generation'),
        ]

        for cluster_id, cluster_type in default_clusters:
            self.create_cluster(cluster_id, cluster_type)

    def _create_default_employees(self):
        """Create default employees"""
        employees = [
            ('api_worker_1', 'api_specialist', ['api_port_management', 'api_monitoring', 'api_optimization']),
            ('api_worker_2', 'api_specialist', ['api_port_management', 'api_security', 'api_testing']),
            ('frontend_worker_1', 'frontend_specialist', ['frontend_development', 'ui_ux_design', 'responsive_design']),
            ('backend_worker_1', 'backend_specialist', ['backend_development', 'server_configuration', 'performance_optimization']),
            ('database_worker_1', 'database_specialist', ['database_management', 'query_optimization', 'indexing']),
            ('database_worker_2', 'database_specialist', ['database_management', 'backup_restore', 'security_audit']),
            ('middleware_worker_1', 'middleware_specialist', ['middleware_management', 'containerization', 'microservices']),
            ('logging_worker_1', 'logging_specialist', ['log_management', 'log_analysis', 'monitoring']),
            ('lock_ai_employee', 'lock_manager', ['system_lock_management', 'timeout_management', 'user_activity_tracking', 'security_policies', 'auto_maintenance', 'self_upgrade']),
            ('ai_education_worker_1', 'ai_education_specialist', ['learning_path_recommendation', 'personalized_learning', 'knowledge_graph', 'adaptive_assessment']),
            ('ai_education_worker_2', 'ai_education_specialist', ['learning_analytics', 'student_progress_tracking', 'classroom_optimization', 'curriculum_design']),
            ('ai_question_bank_worker_1', 'ai_question_bank_specialist', ['question_generation', 'exam_composition', 'difficulty_adjustment', 'knowledge_point_mapping']),
            ('ai_question_bank_worker_2', 'ai_question_bank_specialist', ['wrong_book_analysis', 'weak_point_detection', 'practice_recommendation', 'question_bank_expansion']),
            ('ai_analysis_worker_1', 'ai_analysis_specialist', ['data_visualization', 'predictive_analytics', 'trend_analysis', 'performance_metrics']),
            ('ai_analysis_worker_2', 'ai_analysis_specialist', ['cluster_analysis', 'anomaly_detection', 'root_cause_analysis', 'business_intelligence']),
            ('ai_tutor_worker_1', 'ai_tutor_specialist', ['intelligent_qna', 'explaination_generation', 'concept_clarification', 'study_assistance']),
            ('ai_tutor_worker_2', 'ai_tutor_specialist', ['exam_preparation', 'homework_assistance', 'learning_strategy', 'motivation_boost']),
            ('ai_code_worker_1', 'ai_code_specialist', ['code_generation', 'code_explanation', 'debug_assistance', 'code_optimization']),
            ('ai_code_worker_2', 'ai_code_specialist', ['arduino_code_generation', 'circuit_design', 'embedded_programming', 'hardware_integration']),
            ('ai_image_worker_1', 'ai_image_specialist', ['image_generation', 'visual_design', 'diagram_generation', 'educational_visuals']),
        ]

        for employee_id, employee_type, capabilities in employees:
            self.create_employee(employee_id, employee_type, capabilities)

    def _assign_default_employees(self):
        """Assign default employees to clusters"""
        assignments = [
            ('test_emp', 'test_cluster'),
            ('api_worker_1', 'api_cluster'),
            ('api_worker_2', 'api_cluster'),
            ('frontend_worker_1', 'frontend_cluster'),
            ('backend_worker_1', 'backend_cluster'),
            ('database_worker_1', 'database_cluster'),
            ('database_worker_2', 'database_cluster'),
            ('middleware_worker_1', 'middleware_cluster'),
            ('logging_worker_1', 'logging_cluster'),
            ('lock_ai_employee', 'security_cluster'),
            ('ai_education_worker_1', 'ai_education_cluster'),
            ('ai_education_worker_2', 'ai_education_cluster'),
            ('ai_question_bank_worker_1', 'ai_question_bank_cluster'),
            ('ai_question_bank_worker_2', 'ai_question_bank_cluster'),
            ('ai_analysis_worker_1', 'ai_analysis_cluster'),
            ('ai_analysis_worker_2', 'ai_analysis_cluster'),
            ('ai_tutor_worker_1', 'ai_tutor_cluster'),
            ('ai_tutor_worker_2', 'ai_tutor_cluster'),
            ('ai_code_worker_1', 'ai_code_cluster'),
            ('ai_code_worker_2', 'ai_code_cluster'),
            ('ai_image_worker_1', 'ai_image_cluster'),
        ]

        for employee_id, cluster_id in assignments:
            if employee_id in self.employees and cluster_id in self.clusters:
                self.assign_employee_to_cluster(employee_id, cluster_id)

    def _ensure_all_employees_assigned(self):
        """Ensure all employees are assigned to a cluster"""
        unassigned_count = 0
        for employee_id, employee in self.employees.items():
            if not employee.assigned_cluster or employee.assigned_cluster not in self.clusters:
                target_cluster = self._find_appropriate_cluster(employee)
                if target_cluster:
                    self.assign_employee_to_cluster(employee_id, target_cluster)
                    unassigned_count += 1
                else:
                    logger.warning(f"无法为员工 {employee_id} 找到合适的集群")
        
        if unassigned_count > 0:
            logger.info(f"已修复 {unassigned_count} 个未分配员工的集群分配")
            self._save_to_database()

    def _find_appropriate_cluster(self, employee: AIEmployee) -> Optional[str]:
        """Find an appropriate cluster for an employee based on type"""
        employee_type = employee.employee_type
        type_mapping = {
            'test_type': 'test_cluster',
            'api_specialist': 'api_cluster',
            'frontend_specialist': 'frontend_cluster',
            'backend_specialist': 'backend_cluster',
            'database_specialist': 'database_cluster',
            'security_specialist': 'security_cluster',
            'middleware_specialist': 'middleware_cluster',
            'logging_specialist': 'logging_cluster',
            'lock_manager': 'security_cluster',
            'ai_education_specialist': 'ai_education_cluster',
            'ai_question_bank_specialist': 'ai_question_bank_cluster',
            'ai_analysis_specialist': 'ai_analysis_cluster',
            'ai_tutor_specialist': 'ai_tutor_cluster',
            'ai_code_specialist': 'ai_code_cluster',
            'ai_image_specialist': 'ai_image_cluster',
        }
        
        if employee_type in type_mapping:
            cluster_id = type_mapping[employee_type]
            if cluster_id in self.clusters:
                return cluster_id
        
        for cluster_id, cluster in self.clusters.items():
            if cluster.cluster_type == 'test_type' or cluster.cluster_type == employee_type:
                return cluster_id
        
        if 'test_cluster' in self.clusters:
            return 'test_cluster'
        
        if self.clusters:
            return next(iter(self.clusters.keys()))
        
        return None

    def _log_config_change(self, config_type: str, config_id: str, action: str, old_value: str = None, new_value: str = None, operator: str = 'system'):
        """Log configuration changes to database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_config_history 
                    (config_type, config_id, action, old_value, new_value, operator)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (config_type, config_id, action, old_value, new_value, operator))
                conn.commit()
        except Exception as e:
            logger.error(f"记录配置变更日志失败: {str(e)}")

    def _start_monitoring_thread(self):
        """Start the monitoring thread"""
        def monitor():
            while True:
                time.sleep(self.monitoring_interval)
                if self.monitoring_enabled:
                    self._monitor_all()

        monitoring_thread = threading.Thread(target=monitor, daemon=True)
        monitoring_thread.start()

    def _monitor_all(self):
        """Monitor all clusters and employees"""
        with self.lock:
            current_time = time.time()
            for employee_id, employee in self.employees.items():
                if current_time - employee.last_heartbeat > self.monitoring_interval * 2:
                    logger.warning(f"Employee {employee_id} missed heartbeat - marking as offline")
                    employee.update_status("offline")

            for cluster_id, cluster in self.clusters.items():
                active_employees = sum(1 for e in cluster.employees.values() if e.status == "active")
                if active_employees == 0 and len(cluster.employees) > 0:
                    logger.warning(f"Cluster {cluster_id} has no active employees")
                    cluster.update_status("degraded")
                else:
                    cluster.update_status("active")

            if self.auto_extend_enabled and (current_time - self.last_auto_extend_time) > self.auto_extend_interval:
                self._auto_extend_system()
                self.last_auto_extend_time = current_time

            self._save_to_database()

    def _auto_extend_system(self):
        """Auto extend system features and AI employees"""
        logger.info("Starting auto-extend system...")

        try:
            system_analysis = self._analyze_system_needs()
            self._extend_system_features(system_analysis)
            self._auto_onboard_ai_employees(system_analysis)

            self._save_to_database()
            logger.info("Auto-extend system completed")
        except Exception as e:
            logger.error(f"Auto-extend system failed: {str(e)}")

    def _analyze_system_needs(self):
        """Analyze system needs"""
        logger.info("Analyzing system needs...")

        analysis = self._build_analysis_base()
        self._analyze_cluster_needs(analysis)
        self._analyze_employee_needs(analysis)

        logger.info(f"System analysis completed: {analysis}")
        return analysis

    def _build_analysis_base(self):
        """Build base analysis structure"""
        return {
            'timestamp': time.time(),
            'current_clusters': list(self.clusters.keys()),
            'current_employees': list(self.employees.keys()),
            'employee_count': len(self.employees),
            'cluster_count': len(self.clusters),
            'active_employees': sum(1 for e in self.employees.values() if e.status == "active"),
            'needs': {
                'new_clusters': [],
                'new_employees': [],
                'feature_extensions': []
            }
        }

    def _analyze_cluster_needs(self, analysis):
        """Analyze cluster needs"""
        core_clusters = [
            ('api_cluster', 'api_management'),
            ('frontend_cluster', 'frontend_development'),
            ('backend_cluster', 'backend_development'),
            ('database_cluster', 'database_management'),
            ('security_cluster', 'security_management'),
            ('monitoring_cluster', 'monitoring_management')
        ]

        for cluster_id, cluster_type in core_clusters:
            if cluster_id not in analysis['current_clusters']:
                analysis['needs']['new_clusters'].append((cluster_id, cluster_type))

    def _analyze_employee_needs(self, analysis):
        """Analyze employee needs"""
        employee_types = {}
        for employee in self.employees.values():
            employee_types[employee.employee_type] = employee_types.get(employee.employee_type, 0) + 1

        core_employees = [
            {
                'employee_id': 'lock_ai_employee',
                'employee_type': 'lock_manager',
                'capabilities': ['system_lock_management', 'timeout_management', 'user_activity_tracking', 'security_policies', 'auto_maintenance', 'self_upgrade'],
                'cluster_id': 'security_cluster'
            },
            {
                'employee_id': 'monitoring_ai_employee',
                'employee_type': 'monitoring_manager',
                'capabilities': ['system_monitoring', 'performance_analysis', 'alert_management', 'log_analysis', 'auto_scaling'],
                'cluster_id': 'monitoring_cluster'
            },
            {
                'employee_id': 'database_ai_employee',
                'employee_type': 'database_manager',
                'capabilities': ['database_optimization', 'backup_management', 'query_analysis', 'schema_design', 'data_security'],
                'cluster_id': 'database_cluster'
            }
        ]

        for employee_info in core_employees:
            if employee_info['employee_id'] not in analysis['current_employees']:
                analysis['needs']['new_employees'].append(employee_info)

        if employee_types.get('api_specialist', 0) < 2:
            analysis['needs']['new_employees'].append({
                'employee_id': f'api_worker_{employee_types.get("api_specialist", 0) + 1}',
                'employee_type': 'api_specialist',
                'capabilities': ['api_port_management', 'api_monitoring', 'api_optimization', 'api_security', 'api_testing'],
                'cluster_id': 'api_cluster'
            })

    def _extend_system_features(self, analysis):
        """Extend system features"""
        logger.info("Extending system features...")

        for cluster_id, cluster_type in analysis['needs']['new_clusters']:
            self.create_cluster(cluster_id, cluster_type)

        for cluster_id in self.clusters.keys():
            cluster = self.clusters[cluster_id]

            if cluster_id == 'security_cluster':
                if 'advanced_security' not in cluster.config:
                    cluster.config['advanced_security'] = {
                        'enabled': True,
                        'intrusion_detection': True,
                        'anomaly_detection': True,
                        'auto_response': True
                    }
                    logger.info(f"Added advanced security to cluster {cluster_id}")

            if cluster_id == 'monitoring_cluster':
                if 'advanced_monitoring' not in cluster.config:
                    cluster.config['advanced_monitoring'] = {
                        'enabled': True,
                        'real_time_analytics': True,
                        'predictive_maintenance': True,
                        'capacity_planning': True
                    }
                    logger.info(f"Added advanced monitoring to cluster {cluster_id}")

    def _auto_onboard_ai_employees(self, analysis):
        """Auto onboard AI employees"""
        logger.info("Auto-onboarding AI employees...")

        for employee_info in analysis['needs']['new_employees']:
            self._onboard_single_employee(employee_info)

        self._optimize_existing_employees()

    def _onboard_single_employee(self, employee_info):
        """Onboard a single employee"""
        employee_id = employee_info['employee_id']
        employee_type = employee_info['employee_type']
        capabilities = employee_info['capabilities']
        cluster_id = employee_info['cluster_id']

        self.create_employee(employee_id, employee_type, capabilities)

        if cluster_id in self.clusters:
            self.assign_employee_to_cluster(employee_id, cluster_id)

        employee = self.employees.get(employee_id)
        if employee:
            self._configure_employee_advanced_features(employee, employee_id)

        logger.info(f"AI employee {employee_id} onboarded to {cluster_id}")

    def _configure_employee_advanced_features(self, employee, employee_id):
        """Configure advanced features for specific employees"""
        if employee_id == 'lock_ai_employee':
            employee.config['advanced_features'] = {
                'auto_optimize': True,
                'adaptive_learning': True,
                'threat_intelligence': True,
                'self_healing': True
            }
            logger.info(f"Configured advanced features for {employee_id}")

        elif employee_id == 'monitoring_ai_employee':
            employee.config['advanced_features'] = {
                'predictive_analytics': True,
                'performance_tuning': True,
                'root_cause_analysis': True
            }
            logger.info(f"Configured advanced features for {employee_id}")

    def _optimize_existing_employees(self):
        """Optimize configurations for existing employees"""
        logger.info("Optimizing existing employee configurations...")
        for employee_id, employee in self.employees.items():
            if 'auto_upgrade' not in employee.config:
                employee.config['auto_upgrade'] = True
                employee.config['learning_rate'] = 0.1
                employee.config['self_improvement'] = True
                logger.info(f"Optimized configuration for {employee_id}")

    def create_cluster(self, cluster_id: str, cluster_type: str, config: Optional[Dict] = None) -> bool:
        """Create a new AI cluster"""
        with self.lock:
            if cluster_id in self.clusters:
                logger.warning(f"Cluster {cluster_id} already exists")
                return False

            self.clusters[cluster_id] = AICluster(cluster_id, cluster_type, config)
            self._log_config_change('cluster', cluster_id, 'create', new_value=json.dumps({'cluster_type': cluster_type, 'config': config or {}}))
            self._save_to_database()
            logger.info(f"Created cluster: {cluster_id} ({cluster_type})")
            return True

    def delete_cluster(self, cluster_id: str) -> bool:
        """Delete an existing cluster"""
        with self.lock:
            if cluster_id not in self.clusters:
                logger.warning(f"Cluster {cluster_id} does not exist")
                return False

            cluster = self.clusters[cluster_id]
            old_value = json.dumps(cluster.to_db_dict())
            
            for employee_id in list(cluster.employees.keys()):
                cluster.remove_employee(employee_id)

            del self.clusters[cluster_id]
            self._log_config_change('cluster', cluster_id, 'delete', old_value=old_value)
            self._save_to_database()
            logger.info(f"Deleted cluster: {cluster_id}")
            return True

    def create_employee(self, employee_id: str, employee_type: str, capabilities: List[str], config: Optional[Dict] = None) -> bool:
        """Create a new AI employee"""
        with self.lock:
            if employee_id in self.employees:
                logger.warning(f"Employee {employee_id} already exists")
                return False

            employee = AIEmployee(employee_id, employee_type, capabilities, config)
            self.employees[employee_id] = employee
            self._log_config_change('employee', employee_id, 'create', new_value=json.dumps({'employee_type': employee_type, 'capabilities': capabilities, 'config': config or {}}))
            self._save_to_database()
            logger.info(f"Created employee: {employee_id} ({employee_type})")
            return True

    def delete_employee(self, employee_id: str) -> bool:
        """Delete an existing AI employee"""
        with self.lock:
            if employee_id not in self.employees:
                logger.warning(f"Employee {employee_id} does not exist")
                return False

            employee = self.employees[employee_id]
            old_value = json.dumps(employee.to_db_dict())
            
            if employee.assigned_cluster:
                cluster = self.clusters.get(employee.assigned_cluster)
                if cluster:
                    cluster.remove_employee(employee_id)

            del self.employees[employee_id]
            self._log_config_change('employee', employee_id, 'delete', old_value=old_value)
            self._save_to_database()
            logger.info(f"Deleted employee: {employee_id}")
            return True

    def assign_employee_to_cluster(self, employee_id: str, cluster_id: str) -> bool:
        """Assign an employee to a cluster"""
        with self.lock:
            if employee_id not in self.employees:
                logger.warning(f"Employee {employee_id} does not exist")
                return False

            if cluster_id not in self.clusters:
                logger.warning(f"Cluster {cluster_id} does not exist")
                return False

            employee = self.employees[employee_id]
            old_cluster = employee.assigned_cluster
            
            if employee.assigned_cluster:
                current_cluster = self.clusters.get(employee.assigned_cluster)
                if current_cluster:
                    current_cluster.remove_employee(employee_id)

            cluster = self.clusters[cluster_id]
            cluster.add_employee(employee)
            
            self._log_config_change('employee', employee_id, 'assign', 
                                   old_value=json.dumps({'assigned_cluster': old_cluster}),
                                   new_value=json.dumps({'assigned_cluster': cluster_id}))
            self._save_to_database()
            return True

    def update_cluster_config(self, cluster_id: str, config: Dict) -> bool:
        """Update cluster configuration"""
        with self.lock:
            if cluster_id not in self.clusters:
                logger.warning(f"Cluster {cluster_id} does not exist")
                return False

            cluster = self.clusters[cluster_id]
            old_config = cluster.config.copy()
            cluster.config.update(config)
            cluster.last_updated = time.time()
            
            self._log_config_change('cluster', cluster_id, 'update_config',
                                   old_value=json.dumps(old_config),
                                   new_value=json.dumps(cluster.config))
            self._save_to_database()
            logger.info(f"Updated cluster config: {cluster_id}")
            return True

    def update_employee_config(self, employee_id: str, config: Dict) -> bool:
        """Update employee configuration"""
        with self.lock:
            if employee_id not in self.employees:
                logger.warning(f"Employee {employee_id} does not exist")
                return False

            employee = self.employees[employee_id]
            old_config = employee.config.copy()
            employee.config.update(config)
            
            self._log_config_change('employee', employee_id, 'update_config',
                                   old_value=json.dumps(old_config),
                                   new_value=json.dumps(employee.config))
            self._save_to_database()
            logger.info(f"Updated employee config: {employee_id}")
            return True

    def get_cluster_status(self, cluster_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cluster status"""
        with self.lock:
            if cluster_id:
                cluster = self.clusters.get(cluster_id)
                if not cluster:
                    return {
                        'success': False,
                        'error': f"Cluster {cluster_id} not found"
                    }
                return {
                    'success': True,
                    'status': cluster.get_status()
                }
            else:
                all_status = {}
                for cluster_id, cluster in self.clusters.items():
                    all_status[cluster_id] = cluster.get_status()
                return {
                    'success': True,
                    'status': all_status
                }

    def get_employee_status(self, employee_id: Optional[str] = None) -> Dict[str, Any]:
        """Get employee status"""
        with self.lock:
            if employee_id:
                employee = self.employees.get(employee_id)
                if not employee:
                    return {
                        'success': False,
                        'error': f"Employee {employee_id} not found"
                    }
                return {
                    'success': True,
                    'status': employee.get_status()
                }
            else:
                all_status = {}
                for employee_id, employee in self.employees.items():
                    all_status[employee_id] = employee.get_status()
                return {
                    'success': True,
                    'status': all_status
                }

    def get_config_history(self, config_type: Optional[str] = None, config_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get configuration change history"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                query = 'SELECT * FROM ai_config_history WHERE 1=1'
                params = []
                
                if config_type:
                    query += ' AND config_type = ?'
                    params.append(config_type)
                
                if config_id:
                    query += ' AND config_id = ?'
                    params.append(config_id)
                
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                history = []
                for row in rows:
                    history.append({
                        'id': row[0],
                        'config_type': row[1],
                        'config_id': row[2],
                        'action': row[3],
                        'old_value': json.loads(row[4]) if row[4] else None,
                        'new_value': json.loads(row[5]) if row[5] else None,
                        'operator': row[6],
                        'created_at': row[7]
                    })
            
            return {
                'success': True,
                'history': history
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def upgrade_all(self, upgrade_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Upgrade all clusters and employees"""
        with self.lock:
            results = {
                'clusters': {},
                'employees': {}
            }

            for cluster_id, cluster in self.clusters.items():
                cluster_results = cluster.upgrade_employees(upgrade_data)
                results['clusters'][cluster_id] = cluster_results

                for employee_id, success in cluster_results.items():
                    results['employees'][employee_id] = success

            for employee_id, employee in self.employees.items():
                if employee_id not in results['employees']:
                    results['employees'][employee_id] = employee.upgrade(upgrade_data)

            self._save_to_database()
            logger.info("Global upgrade completed")
            return {
                'success': True,
                'results': results
            }

    def assign_task(self, cluster_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Assign a task to a cluster"""
        with self.lock:
            cluster = self.clusters.get(cluster_id)
            if not cluster:
                return {
                    'success': False,
                    'error': f"Cluster {cluster_id} not found"
                }

            success = cluster.assign_task(task)
            return {
                'success': success,
                'cluster_id': cluster_id
            }

    def set_monitoring_enabled(self, enabled: bool) -> bool:
        """Enable or disable monitoring"""
        self.monitoring_enabled = enabled
        logger.info(f"Monitoring {'enabled' if enabled else 'disabled'}")
        return True

    def set_auto_upgrade_enabled(self, enabled: bool) -> bool:
        """Enable or disable auto-upgrade"""
        self.auto_upgrade_enabled = enabled
        logger.info(f"Auto-upgrade {'enabled' if enabled else 'disabled'}")
        return True

    def _initialize_default_models(self):
        """Initialize default AI models"""
        logger.info("初始化默认AI模型...")
        default_models = [
            {
                'model_id': 'gpt-4',
                'model_name': 'GPT-4',
                'model_type': 'llm',
                'provider': 'openai',
                'endpoint': 'https://api.openai.com/v1/chat/completions',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 4096}),
                'performance_metrics': json.dumps({'latency': 0.8, 'throughput': 50, 'accuracy': 0.95}),
                'version': '4.0'
            },
            {
                'model_id': 'gpt-4o',
                'model_name': 'GPT-4o',
                'model_type': 'llm',
                'provider': 'openai',
                'endpoint': 'https://api.openai.com/v1/chat/completions',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 128000}),
                'performance_metrics': json.dumps({'latency': 0.5, 'throughput': 100, 'accuracy': 0.96}),
                'version': '4.o'
            },
            {
                'model_id': 'gpt-4o-mini',
                'model_name': 'GPT-4o mini',
                'model_type': 'llm',
                'provider': 'openai',
                'endpoint': 'https://api.openai.com/v1/chat/completions',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 128000}),
                'performance_metrics': json.dumps({'latency': 0.15, 'throughput': 200, 'accuracy': 0.92}),
                'version': '1.0'
            },
            {
                'model_id': 'gpt-4-turbo',
                'model_name': 'GPT-4 Turbo',
                'model_type': 'llm',
                'provider': 'openai',
                'endpoint': 'https://api.openai.com/v1/chat/completions',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 128000}),
                'performance_metrics': json.dumps({'latency': 0.6, 'throughput': 80, 'accuracy': 0.95}),
                'version': '128k'
            },
            {
                'model_id': 'claude-3-opus',
                'model_name': 'Claude 3 Opus',
                'model_type': 'llm',
                'provider': 'anthropic',
                'endpoint': 'https://api.anthropic.com/v1/messages',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 200000}),
                'performance_metrics': json.dumps({'latency': 1.2, 'throughput': 30, 'accuracy': 0.97}),
                'version': '3.0'
            },
            {
                'model_id': 'claude-3-sonnet',
                'model_name': 'Claude 3 Sonnet',
                'model_type': 'llm',
                'provider': 'anthropic',
                'endpoint': 'https://api.anthropic.com/v1/messages',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 200000}),
                'performance_metrics': json.dumps({'latency': 0.6, 'throughput': 80, 'accuracy': 0.94}),
                'version': '3.0'
            },
            {
                'model_id': 'claude-3.5-sonnet',
                'model_name': 'Claude 3.5 Sonnet',
                'model_type': 'llm',
                'provider': 'anthropic',
                'endpoint': 'https://api.anthropic.com/v1/messages',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 200000}),
                'performance_metrics': json.dumps({'latency': 0.4, 'throughput': 120, 'accuracy': 0.96}),
                'version': '3.5'
            },
            {
                'model_id': 'claude-3.5-haiku',
                'model_name': 'Claude 3.5 Haiku',
                'model_type': 'llm',
                'provider': 'anthropic',
                'endpoint': 'https://api.anthropic.com/v1/messages',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 200000}),
                'performance_metrics': json.dumps({'latency': 0.15, 'throughput': 300, 'accuracy': 0.90}),
                'version': '3.5'
            },
            {
                'model_id': 'qwen-max',
                'model_name': 'Qwen Max',
                'model_type': 'llm',
                'provider': 'alibaba',
                'endpoint': 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 8192}),
                'performance_metrics': json.dumps({'latency': 0.7, 'throughput': 60, 'accuracy': 0.92}),
                'version': '2.0'
            },
            {
                'model_id': 'qwen-plus',
                'model_name': 'Qwen Plus',
                'model_type': 'llm',
                'provider': 'alibaba',
                'endpoint': 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 4096}),
                'performance_metrics': json.dumps({'latency': 0.4, 'throughput': 100, 'accuracy': 0.90}),
                'version': '2.0'
            },
            {
                'model_id': 'qwen-2.5-max',
                'model_name': 'Qwen 2.5 Max',
                'model_type': 'llm',
                'provider': 'alibaba',
                'endpoint': 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 128000}),
                'performance_metrics': json.dumps({'latency': 0.3, 'throughput': 150, 'accuracy': 0.94}),
                'version': '2.5'
            },
            {
                'model_id': 'qwen-2.5-plus',
                'model_name': 'Qwen 2.5 Plus',
                'model_type': 'llm',
                'provider': 'alibaba',
                'endpoint': 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 4096}),
                'performance_metrics': json.dumps({'latency': 0.2, 'throughput': 200, 'accuracy': 0.91}),
                'version': '2.5'
            },
            {
                'model_id': 'llama-3-70b',
                'model_name': 'Llama 3 70B',
                'model_type': 'llm',
                'provider': 'meta',
                'endpoint': '',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 8192}),
                'performance_metrics': json.dumps({'latency': 1.0, 'throughput': 40, 'accuracy': 0.93}),
                'version': '3.0'
            },
            {
                'model_id': 'llama-3.1-70b',
                'model_name': 'Llama 3.1 70B',
                'model_type': 'llm',
                'provider': 'meta',
                'endpoint': '',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 128000}),
                'performance_metrics': json.dumps({'latency': 0.8, 'throughput': 60, 'accuracy': 0.94}),
                'version': '3.1'
            },
            {
                'model_id': 'llama-3.1-8b',
                'model_name': 'Llama 3.1 8B',
                'model_type': 'llm',
                'provider': 'meta',
                'endpoint': '',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 8192}),
                'performance_metrics': json.dumps({'latency': 0.2, 'throughput': 150, 'accuracy': 0.90}),
                'version': '3.1'
            },
            {
                'model_id': 'gemini-pro',
                'model_name': 'Gemini Pro',
                'model_type': 'llm',
                'provider': 'google',
                'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 8192}),
                'performance_metrics': json.dumps({'latency': 0.6, 'throughput': 70, 'accuracy': 0.92}),
                'version': '1.5'
            },
            {
                'model_id': 'gemini-1.5-pro',
                'model_name': 'Gemini 1.5 Pro',
                'model_type': 'llm',
                'provider': 'google',
                'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 1048576}),
                'performance_metrics': json.dumps({'latency': 0.8, 'throughput': 50, 'accuracy': 0.95}),
                'version': '1.5'
            },
            {
                'model_id': 'gemini-1.5-flash',
                'model_name': 'Gemini 1.5 Flash',
                'model_type': 'llm',
                'provider': 'google',
                'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 1048576}),
                'performance_metrics': json.dumps({'latency': 0.2, 'throughput': 200, 'accuracy': 0.92}),
                'version': '1.5'
            },
            {
                'model_id': 'whisper-large',
                'model_name': 'Whisper Large',
                'model_type': 'speech_to_text',
                'provider': 'openai',
                'endpoint': 'https://api.openai.com/v1/audio/transcriptions',
                'parameters': json.dumps({'language': 'zh'}),
                'performance_metrics': json.dumps({'latency': 2.0, 'throughput': 10, 'accuracy': 0.98}),
                'version': '3.0'
            },
            {
                'model_id': 'text-embedding-3-large',
                'model_name': 'Text Embedding 3 Large',
                'model_type': 'embedding',
                'provider': 'openai',
                'endpoint': 'https://api.openai.com/v1/embeddings',
                'parameters': json.dumps({'dimensions': 3072}),
                'performance_metrics': json.dumps({'latency': 0.1, 'throughput': 500, 'accuracy': 0.99}),
                'version': '3.0'
            },
            {
                'model_id': 'text-embedding-3-small',
                'model_name': 'Text Embedding 3 Small',
                'model_type': 'embedding',
                'provider': 'openai',
                'endpoint': 'https://api.openai.com/v1/embeddings',
                'parameters': json.dumps({'dimensions': 1536}),
                'performance_metrics': json.dumps({'latency': 0.05, 'throughput': 1000, 'accuracy': 0.97}),
                'version': '3.0'
            },
            {
                'model_id': 'dall-e-3',
                'model_name': 'DALL-E 3',
                'model_type': 'image_generation',
                'provider': 'openai',
                'endpoint': 'https://api.openai.com/v1/images/generations',
                'parameters': json.dumps({'size': '1024x1024'}),
                'performance_metrics': json.dumps({'latency': 5.0, 'throughput': 5, 'accuracy': 0.90}),
                'version': '3.0'
            },
            {
                'model_id': 'stable-diffusion',
                'model_name': 'Stable Diffusion',
                'model_type': 'image_generation',
                'provider': 'stability-ai',
                'endpoint': '',
                'parameters': json.dumps({'steps': 30}),
                'performance_metrics': json.dumps({'latency': 8.0, 'throughput': 3, 'accuracy': 0.88}),
                'version': '2.1'
            },
            {
                'model_id': 'sdxl',
                'model_name': 'Stable Diffusion XL',
                'model_type': 'image_generation',
                'provider': 'stability-ai',
                'endpoint': '',
                'parameters': json.dumps({'steps': 30, 'width': 1024, 'height': 1024}),
                'performance_metrics': json.dumps({'latency': 10.0, 'throughput': 2, 'accuracy': 0.92}),
                'version': '1.0'
            },
            {
                'model_id': 'code-llama',
                'model_name': 'Code Llama',
                'model_type': 'code',
                'provider': 'meta',
                'endpoint': '',
                'parameters': json.dumps({'temperature': 0.2, 'max_tokens': 8192}),
                'performance_metrics': json.dumps({'latency': 1.5, 'throughput': 20, 'accuracy': 0.91}),
                'version': '3.0'
            },
            {
                'model_id': 'codellama-3.1',
                'model_name': 'Code Llama 3.1',
                'model_type': 'code',
                'provider': 'meta',
                'endpoint': '',
                'parameters': json.dumps({'temperature': 0.2, 'max_tokens': 128000}),
                'performance_metrics': json.dumps({'latency': 1.0, 'throughput': 40, 'accuracy': 0.93}),
                'version': '3.1'
            },
            {
                'model_id': 'deepseek-coder',
                'model_name': 'DeepSeek Coder',
                'model_type': 'code',
                'provider': 'deepseek',
                'endpoint': '',
                'parameters': json.dumps({'temperature': 0.2, 'max_tokens': 8192}),
                'performance_metrics': json.dumps({'latency': 0.8, 'throughput': 50, 'accuracy': 0.92}),
                'version': '2.0'
            },
            {
                'model_id': 'chatglm-4',
                'model_name': 'ChatGLM 4',
                'model_type': 'llm',
                'provider': 'zhipu',
                'endpoint': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 8192}),
                'performance_metrics': json.dumps({'latency': 0.5, 'throughput': 90, 'accuracy': 0.91}),
                'version': '4.0'
            },
            {
                'model_id': 'chatglm-4-plus',
                'model_name': 'ChatGLM 4 Plus',
                'model_type': 'llm',
                'provider': 'zhipu',
                'endpoint': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 128000}),
                'performance_metrics': json.dumps({'latency': 0.3, 'throughput': 120, 'accuracy': 0.93}),
                'version': '4.0'
            },
            {
                'model_id': 'ernie-4.0',
                'model_name': 'ERNIE 4.0',
                'model_type': 'llm',
                'provider': 'baidu',
                'endpoint': 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 4096}),
                'performance_metrics': json.dumps({'latency': 0.6, 'throughput': 70, 'accuracy': 0.90}),
                'version': '4.0'
            },
            {
                'model_id': 'ernie-5.0',
                'model_name': 'ERNIE 5.0',
                'model_type': 'llm',
                'provider': 'baidu',
                'endpoint': 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 8192}),
                'performance_metrics': json.dumps({'latency': 0.4, 'throughput': 100, 'accuracy': 0.92}),
                'version': '5.0'
            },
            {
                'model_id': 'mistral-large',
                'model_name': 'Mistral Large',
                'model_type': 'llm',
                'provider': 'mistral',
                'endpoint': 'https://api.mistral.ai/v1/chat/completions',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 32768}),
                'performance_metrics': json.dumps({'latency': 0.6, 'throughput': 60, 'accuracy': 0.93}),
                'version': '2.0'
            },
            {
                'model_id': 'mixtral-8x7b',
                'model_name': 'Mixtral 8x7B',
                'model_type': 'llm',
                'provider': 'mistral',
                'endpoint': '',
                'parameters': json.dumps({'temperature': 0.7, 'max_tokens': 32768}),
                'performance_metrics': json.dumps({'latency': 0.8, 'throughput': 40, 'accuracy': 0.91}),
                'version': '8x7b'
            },
            {
                'model_id': 'embedding-qwen',
                'model_name': 'Qwen Embedding',
                'model_type': 'embedding',
                'provider': 'alibaba',
                'endpoint': 'https://dashscope.aliyuncs.com/api/v1/services/embedding/text-embedding/text-embedding',
                'parameters': json.dumps({'dimensions': 1024}),
                'performance_metrics': json.dumps({'latency': 0.08, 'throughput': 800, 'accuracy': 0.95}),
                'version': '2.0'
            },
            {
                'model_id': 'speech-qwen',
                'model_name': 'Qwen Speech',
                'model_type': 'speech_to_text',
                'provider': 'alibaba',
                'endpoint': 'https://dashscope.aliyuncs.com/api/v1/services/audio/asr/speech_to_text',
                'parameters': json.dumps({'language': 'zh'}),
                'performance_metrics': json.dumps({'latency': 1.5, 'throughput': 15, 'accuracy': 0.96}),
                'version': '2.0'
            },
        ]

        for model_info in default_models:
            self.create_model(model_info)

    def create_model(self, model_info: Dict) -> bool:
        """Create a new AI model"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                model_id = model_info['model_id']
                cursor.execute('SELECT COUNT(*) FROM ai_model_config WHERE model_id = ?', (model_id,))
                if cursor.fetchone()[0] > 0:
                    logger.warning(f"Model {model_id} already exists")
                    return False

                cursor.execute('''
                    INSERT INTO ai_model_config 
                    (model_id, model_name, model_type, provider, endpoint, parameters, performance_metrics, version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    model_info['model_id'],
                    model_info['model_name'],
                    model_info['model_type'],
                    model_info['provider'],
                    model_info.get('endpoint', ''),
                    model_info.get('parameters', '{}'),
                    model_info.get('performance_metrics', '{}'),
                    model_info.get('version', '1.0')
                ))
                
                conn.commit()
                logger.info(f"Created AI model: {model_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to create model: {str(e)}")
            return False

    def get_models(self, model_type: str = None) -> Dict[str, Any]:
        """Get all AI models"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if model_type:
                    cursor.execute('SELECT * FROM ai_model_config WHERE model_type = ?', (model_type,))
                else:
                    cursor.execute('SELECT * FROM ai_model_config')
                
                models = []
                for row in cursor.fetchall():
                    models.append({
                        'model_id': row[0],
                        'model_name': row[1],
                        'model_type': row[2],
                        'provider': row[3],
                        'endpoint': row[5],
                        'parameters': json.loads(row[6]) if row[6] else {},
                        'performance_metrics': json.loads(row[7]) if row[7] else {},
                        'status': row[8],
                        'version': row[9]
                    })
                
                return {'success': True, 'models': models}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_model_performance(self, model_id: str, metrics: Dict) -> bool:
        """Update model performance metrics"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO ai_model_performance 
                    (model_id, latency, throughput, accuracy, error_rate, requests_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    model_id,
                    metrics.get('latency', 0.0),
                    metrics.get('throughput', 0.0),
                    metrics.get('accuracy', 0.0),
                    metrics.get('error_rate', 0.0),
                    metrics.get('requests_count', 0)
                ))
                
                cursor.execute('''
                    UPDATE ai_model_config 
                    SET performance_metrics = ?, updated_at = ?
                    WHERE model_id = ?
                ''', (json.dumps(metrics), str(time.time()), model_id))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update model performance: {str(e)}")
            return False

    def shutdown(self) -> bool:
        """Shutdown the cluster manager"""
        with self.lock:
            logger.info("Shutting down AI Cluster Manager...")
            for cluster in self.clusters.values():
                cluster.update_status("shutdown")

            for employee in self.employees.values():
                employee.update_status("shutdown")
            
            self._save_to_database()
            logger.info("AI Cluster Manager shut down successfully")
            return True


ai_cluster_manager = AIClusterManager()

if __name__ == "__main__":
    logger.info("AI Cluster Manager initialized")

    cluster_status = ai_cluster_manager.get_cluster_status()
    logger.info(f"Cluster Status: {json.dumps(cluster_status, indent=2)}")

    employee_status = ai_cluster_manager.get_employee_status()
    logger.info(f"Employee Status: {json.dumps(employee_status, indent=2)}")

    upgrade_result = ai_cluster_manager.upgrade_all({"capabilities": ["new_feature"]})
    logger.info(f"Upgrade Result: {json.dumps(upgrade_result, indent=2)}")

    config_history = ai_cluster_manager.get_config_history()
    logger.info(f"Config History: {json.dumps(config_history, indent=2)}")

    logger.info("AI Cluster Manager test completed!")