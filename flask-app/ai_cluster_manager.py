#!/usr/bin/env python3
"""
AI Cluster Manager
Manages AI clusters and employees with unified control, monitoring, and upgrading capabilities
"""

import os
import sys
import time
import json
import threading
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('ai_cluster_manager.log'),
                              logging.StreamHandler()])
logger = logging.getLogger('AI_Cluster_Manager')

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
        
        # Update performance metrics
        task_id = self.current_task['task_id']
        self.performance_metrics['tasks_completed'] += 1
        
        if result.get('success', False):
            # Calculate new success rate
            total = self.performance_metrics['tasks_completed']
            current_success = self.performance_metrics['success_rate'] * (total - 1)
            self.performance_metrics['success_rate'] = (current_success + 1) / total
        
        self.current_task = None
        self.update_status("active")
        logger.info(f"Task completed by {self.employee_id}: {task_id}")
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
            
            # Simulate upgrade process
            time.sleep(1)
            
            if upgrade_data:
                # Update capabilities if provided
                if 'capabilities' in upgrade_data:
                    self.capabilities.extend(upgrade_data['capabilities'])
                    # Remove duplicates
                    self.capabilities = list(set(self.capabilities))
                
                # Update config if provided
                if 'config' in upgrade_data:
                    self.config.update(upgrade_data['config'])
            
            self.update_status("active")
            logger.info(f"Successfully upgraded AI Employee: {self.employee_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to upgrade AI Employee {self.employee_id}: {str(e)}")
            self.update_status("error")
            return False

class AICluster:
    """AI Cluster class manages a group of AI employees"""
    
    def __init__(self, cluster_id: str, cluster_type: str, config: Optional[Dict] = None):
        self.cluster_id = cluster_id
        self.cluster_type = cluster_type
        self.config = config or {}
        self.employees: Dict[str, AIEmployee] = {}
        self.status = "active"
        self.created_at = time.time()
        self.last_updated = time.time()
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
            self.last_updated = time.time()
            logger.info(f"Removed employee {employee_id} from cluster {self.cluster_id}")
            return True
    
    def assign_task(self, task: Dict[str, Any]) -> bool:
        """Assign a task to the cluster"""
        with self.lock:
            # Find an available employee with matching capabilities
            required_capability = task.get('required_capability')
            
            for employee in self.employees.values():
                if employee.status == "active" and (not required_capability or required_capability in employee.capabilities):
                    return employee.assign_task(task)
            
            # No available employee, add to queue
            self.task_queue.append(task)
            logger.info(f"Added task to queue for cluster {self.cluster_id}")
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
                'status': self.status,
                'created_at': self.created_at,
                'last_updated': self.last_updated,
                'employee_count': len(self.employees),
                'employees': employee_statuses,
                'task_queue_length': len(self.task_queue),
                'config': self.config
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
            
            # Update all employees' status if cluster is not active
            if status != "active":
                for employee in self.employees.values():
                    employee.update_status(status)
            
            logger.info(f"Updated cluster {self.cluster_id} status: {status}")
            return True

class AIClusterManager:
    """Main AI Cluster Manager that handles all clusters and employees"""
    
    def __init__(self):
        self.clusters: Dict[str, AICluster] = {}
        self.employees: Dict[str, AIEmployee] = {}
        self.lock = threading.RLock()
        self.monitoring_enabled = True
        self.auto_upgrade_enabled = True
        self.auto_extend_enabled = True  # 自动扩展系统功能
        self.auto_onboard_enabled = True  # 自动AI员工入驻
        self.monitoring_interval = 60  # seconds
        self.upgrade_interval = 3600  # seconds
        self.auto_extend_interval = 3600  # 自动扩展检查间隔
        self.last_auto_extend_time = time.time()  # 上次自动扩展时间
        
        # Start monitoring thread
        self._start_monitoring_thread()
        
        logger.info("AI Cluster Manager initialized successfully")
    
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
            # Check employee heartbeats
            current_time = time.time()
            for employee_id, employee in self.employees.items():
                if current_time - employee.last_heartbeat > self.monitoring_interval * 2:
                    logger.warning(f"Employee {employee_id} missed heartbeat - marking as offline")
                    employee.update_status("offline")
            
            # Check cluster health
            for cluster_id, cluster in self.clusters.items():
                active_employees = sum(1 for e in cluster.employees.values() if e.status == "active")
                if active_employees == 0 and len(cluster.employees) > 0:
                    logger.warning(f"Cluster {cluster_id} has no active employees")
                    cluster.update_status("degraded")
                else:
                    cluster.update_status("active")
            
            # Check if auto-extend is needed
            if self.auto_extend_enabled and (current_time - self.last_auto_extend_time) > self.auto_extend_interval:
                self._auto_extend_system()
                self.last_auto_extend_time = current_time
    
    def _auto_extend_system(self):
        """自动扩展系统功能和AI员工入驻"""
        logger.info("开始自动扩展系统功能和AI员工入驻...")
        
        try:
            # 1. 分析当前系统状态和需求
            system_analysis = self._analyze_system_needs()
            
            # 2. 扩展系统功能
            self._extend_system_features(system_analysis)
            
            # 3. 自动入驻AI员工
            self._auto_onboard_ai_employees(system_analysis)
            
            logger.info("自动扩展系统功能和AI员工入驻完成")
        except Exception as e:
            logger.error(f"自动扩展系统失败: {str(e)}")
    
    def _analyze_system_needs(self):
        """分析系统需求"""
        logger.info("分析系统需求...")
        
        # 分析当前系统状态
        analysis = {
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
        
        # 分析员工类型分布
        employee_types = {}
        for employee in self.employees.values():
            employee_types[employee.employee_type] = employee_types.get(employee.employee_type, 0) + 1
        
        # 基于当前状态确定需求
        
        # 1. 检查核心集群是否存在
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
        
        # 2. 检查核心员工是否存在
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
        
        # 3. 根据员工类型分布智能添加新员工
        # 示例：如果API管理员工数量不足，则添加API管理员工
        if employee_types.get('api_specialist', 0) < 2:
            analysis['needs']['new_employees'].append({
                'employee_id': f'api_worker_{employee_types.get("api_specialist", 0) + 1}',
                'employee_type': 'api_specialist',
                'capabilities': ['api_port_management', 'api_monitoring', 'api_optimization', 'api_security', 'api_testing'],
                'cluster_id': 'api_cluster'
            })
        
        # 4. 分析系统功能扩展需求
        # 示例：如果没有日志管理功能，则添加日志管理员工
        if 'logging_cluster' not in analysis['current_clusters']:
            analysis['needs']['new_clusters'].append(('logging_cluster', 'log_management'))
            analysis['needs']['new_employees'].append({
                'employee_id': 'logging_ai_employee',
                'employee_type': 'logging_manager',
                'capabilities': ['log_collection', 'log_analysis', 'log_storage', 'log_search', 'log_visualization'],
                'cluster_id': 'logging_cluster'
            })
        
        # 5. 基于员工状态分析需求
        # 示例：如果活跃员工比例低于70%，则添加新员工
        if analysis['employee_count'] > 0 and analysis['active_employees'] / analysis['employee_count'] < 0.7:
            # 添加更多活跃员工
            for cluster_id in analysis['current_clusters']:
                cluster = self.clusters[cluster_id]
                active_in_cluster = sum(1 for e in cluster.employees.values() if e.status == "active")
                total_in_cluster = len(cluster.employees)
                if total_in_cluster > 0 and active_in_cluster / total_in_cluster < 0.7:
                    # 为该集群添加新员工
                    employee_type = cluster.cluster_type.split('_')[0] + '_specialist'
                    analysis['needs']['new_employees'].append({
                        'employee_id': f'{cluster_id}_worker_{total_in_cluster + 1}',
                        'employee_type': employee_type,
                        'capabilities': [f'{cluster_id}_management', f'{cluster_id}_optimization', f'{cluster_id}_monitoring'],
                        'cluster_id': cluster_id
                    })
        
        logger.info(f"系统需求分析完成: {analysis}")
        return analysis
    
    def _extend_system_features(self, analysis):
        """扩展系统功能"""
        logger.info("扩展系统功能...")
        
        # 1. 创建新集群
        for cluster_id, cluster_type in analysis['needs']['new_clusters']:
            self.create_cluster(cluster_id, cluster_type)
        
        # 2. 为现有集群添加新功能
        for cluster_id in self.clusters.keys():
            cluster = self.clusters[cluster_id]
            
            # 示例：为安全集群添加高级安全功能
            if cluster_id == 'security_cluster':
                # 确保集群配置包含高级安全功能
                if 'advanced_security' not in cluster.config:
                    cluster.config['advanced_security'] = {
                        'enabled': True,
                        'intrusion_detection': True,
                        'anomaly_detection': True,
                        'auto_response': True
                    }
                    logger.info(f"为集群 {cluster_id} 添加高级安全功能")
            
            # 示例：为监控集群添加高级监控功能
            elif cluster_id == 'monitoring_cluster':
                if 'advanced_monitoring' not in cluster.config:
                    cluster.config['advanced_monitoring'] = {
                        'enabled': True,
                        'real_time_analytics': True,
                        'predictive_maintenance': True,
                        'capacity_planning': True
                    }
                    logger.info(f"为集群 {cluster_id} 添加高级监控功能")
        
        # 3. 执行系统功能扩展
        logger.info(f"系统功能扩展完成，当前集群数量: {len(self.clusters)}")
    
    def _auto_onboard_ai_employees(self, analysis):
        """自动入驻AI员工"""
        logger.info("自动入驻AI员工...")
        
        # 创建新员工并分配到集群
        for employee_info in analysis['needs']['new_employees']:
            employee_id = employee_info['employee_id']
            employee_type = employee_info['employee_type']
            capabilities = employee_info['capabilities']
            cluster_id = employee_info['cluster_id']
            
            # 创建员工
            self.create_employee(employee_id, employee_type, capabilities)
            
            # 分配到集群
            self.assign_employee_to_cluster(employee_id, cluster_id)
            
            # 4. 为新员工配置高级功能
            employee = self.employees.get(employee_id)
            if employee:
                # 示例：为锁定AI员工配置高级功能
                if employee_id == 'lock_ai_employee':
                    employee.config['advanced_features'] = {
                        'auto_optimize': True,
                        'adaptive_learning': True,
                        'threat_intelligence': True,
                        'self_healing': True
                    }
                    logger.info(f"为AI员工 {employee_id} 配置高级功能")
                
                # 示例：为监控AI员工配置高级功能
                elif employee_id == 'monitoring_ai_employee':
                    employee.config['advanced_features'] = {
                        'predictive_analytics': True,
                        'auto_scaling': True,
                        'performance_tuning': True,
                        'root_cause_analysis': True
                    }
                    logger.info(f"为AI员工 {employee_id} 配置高级功能")
            
            logger.info(f"AI员工 {employee_id} 已成功入驻 {cluster_id} 集群")
        
        # 5. 优化现有员工配置
        logger.info("优化现有员工配置...")
        for employee_id, employee in self.employees.items():
            # 确保所有员工都有基础配置
            if 'auto_upgrade' not in employee.config:
                employee.config['auto_upgrade'] = True
                employee.config['learning_rate'] = 0.1
                employee.config['self_improvement'] = True
                logger.info(f"优化员工 {employee_id} 配置")
    
    def create_cluster(self, cluster_id: str, cluster_type: str, config: Optional[Dict] = None) -> bool:
        """Create a new AI cluster"""
        with self.lock:
            if cluster_id in self.clusters:
                logger.warning(f"Cluster {cluster_id} already exists")
                return False
            
            self.clusters[cluster_id] = AICluster(cluster_id, cluster_type, config)
            logger.info(f"Created cluster: {cluster_id} ({cluster_type})")
            return True
    
    def delete_cluster(self, cluster_id: str) -> bool:
        """Delete an existing cluster"""
        with self.lock:
            if cluster_id not in self.clusters:
                logger.warning(f"Cluster {cluster_id} does not exist")
                return False
            
            # Remove all employees from cluster first
            cluster = self.clusters[cluster_id]
            for employee_id in list(cluster.employees.keys()):
                cluster.remove_employee(employee_id)
            
            del self.clusters[cluster_id]
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
            logger.info(f"Created employee: {employee_id} ({employee_type})")
            return True
    
    def delete_employee(self, employee_id: str) -> bool:
        """Delete an existing AI employee"""
        with self.lock:
            if employee_id not in self.employees:
                logger.warning(f"Employee {employee_id} does not exist")
                return False
            
            # Remove from any cluster
            employee = self.employees[employee_id]
            if employee.assigned_cluster:
                cluster = self.clusters.get(employee.assigned_cluster)
                if cluster:
                    cluster.remove_employee(employee_id)
            
            del self.employees[employee_id]
            logger.info(f"Deleted employee: {employee_id}")
            return True
    
    def assign_employee_to_cluster(self, employee_id: str, cluster_id: str) -> bool:
        """Assign an employee to a cluster"""
        with self.lock:
            # Check if employee and cluster exist
            if employee_id not in self.employees:
                logger.warning(f"Employee {employee_id} does not exist")
                return False
            
            if cluster_id not in self.clusters:
                logger.warning(f"Cluster {cluster_id} does not exist")
                return False
            
            # Remove from current cluster if any
            employee = self.employees[employee_id]
            if employee.assigned_cluster:
                current_cluster = self.clusters.get(employee.assigned_cluster)
                if current_cluster:
                    current_cluster.remove_employee(employee_id)
            
            # Add to new cluster
            cluster = self.clusters[cluster_id]
            return cluster.add_employee(employee)
    
    def get_cluster_status(self, cluster_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cluster status, or all clusters if none specified"""
        with self.lock:
            if cluster_id:
                # Get specific cluster
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
                # Get all clusters
                all_status = {}
                for cluster_id, cluster in self.clusters.items():
                    all_status[cluster_id] = cluster.get_status()
                return {
                    'success': True,
                    'status': all_status
                }
    
    def get_employee_status(self, employee_id: Optional[str] = None) -> Dict[str, Any]:
        """Get employee status, or all employees if none specified"""
        with self.lock:
            if employee_id:
                # Get specific employee
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
                # Get all employees
                all_status = {}
                for employee_id, employee in self.employees.items():
                    all_status[employee_id] = employee.get_status()
                return {
                    'success': True,
                    'status': all_status
                }
    
    def upgrade_all(self, upgrade_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Upgrade all clusters and employees"""
        with self.lock:
            logger.info("Starting global upgrade")
            results = {
                'clusters': {},
                'employees': {}
            }
            
            # Upgrade all clusters
            for cluster_id, cluster in self.clusters.items():
                cluster_results = cluster.upgrade_employees(upgrade_data)
                results['clusters'][cluster_id] = cluster_results
                
                # Update employee results
                for employee_id, success in cluster_results.items():
                    results['employees'][employee_id] = success
            
            # Upgrade unassigned employees
            for employee_id, employee in self.employees.items():
                if not employee.assigned_cluster:
                    results['employees'][employee_id] = employee.upgrade(upgrade_data)
            
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
                'success': success
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
    
    def shutdown(self) -> bool:
        """Shutdown the cluster manager"""
        with self.lock:
            logger.info("Shutting down AI Cluster Manager...")
            self.monitoring_enabled = False
            
            # Update all clusters and employees
            for cluster in self.clusters.values():
                cluster.update_status("shutdown")
            
            for employee in self.employees.values():
                employee.update_status("shutdown")
            
            logger.info("AI Cluster Manager shut down successfully")
            return True

# Initialize cluster manager instance
ai_cluster_manager = AIClusterManager()

# Pre-create some default clusters and employees
def initialize_default_clusters():
    """Initialize default clusters and employees"""
    # Create clusters
    default_clusters = [
        ('api_cluster', 'api_management'),
        ('frontend_cluster', 'frontend_development'),
        ('backend_cluster', 'backend_development'),
        ('database_cluster', 'database_management'),
        ('middleware_cluster', 'middleware_management'),
        ('logging_cluster', 'log_management'),
        ('security_cluster', 'security_management')
    ]
    
    for cluster_id, cluster_type in default_clusters:
        ai_cluster_manager.create_cluster(cluster_id, cluster_type)
    
    # Create employees with various capabilities
    employees = [
        ('api_worker_1', 'api_specialist', ['api_port_management', 'api_monitoring', 'api_optimization']),
        ('api_worker_2', 'api_specialist', ['api_port_management', 'api_security', 'api_testing']),
        ('frontend_worker_1', 'frontend_specialist', ['frontend_development', 'ui_ux_design', 'responsive_design']),
        ('backend_worker_1', 'backend_specialist', ['backend_development', 'server_configuration', 'performance_optimization']),
        ('database_worker_1', 'database_specialist', ['database_management', 'sql_optimization', 'data_migration']),
        ('database_worker_2', 'database_specialist', ['database_management', 'backup_restore', 'security_audit']),
        ('middleware_worker_1', 'middleware_specialist', ['middleware_management', 'containerization', 'microservices']),
        ('logging_worker_1', 'logging_specialist', ['log_management', 'log_analysis', 'monitoring']),
        ('lock_ai_employee', 'lock_manager', ['system_lock_management', 'timeout_management', 'user_activity_tracking', 'security_policies', 'auto_maintenance', 'self_upgrade'])
    ]
    
    for employee_id, employee_type, capabilities in employees:
        ai_cluster_manager.create_employee(employee_id, employee_type, capabilities)
    
    # Assign employees to clusters
    assignments = [
        ('api_worker_1', 'api_cluster'),
        ('api_worker_2', 'api_cluster'),
        ('frontend_worker_1', 'frontend_cluster'),
        ('backend_worker_1', 'backend_cluster'),
        ('database_worker_1', 'database_cluster'),
        ('database_worker_2', 'database_cluster'),
        ('middleware_worker_1', 'middleware_cluster'),
        ('logging_worker_1', 'logging_cluster'),
        ('lock_ai_employee', 'security_cluster')
    ]
    
    for employee_id, cluster_id in assignments:
        ai_cluster_manager.assign_employee_to_cluster(employee_id, cluster_id)

# Initialize default clusters and employees
initialize_default_clusters()

if __name__ == "__main__":
    # Test the cluster manager
    logger.info("Testing AI Cluster Manager...")
    
    # Get all cluster status
    cluster_status = ai_cluster_manager.get_cluster_status()
    logger.info(f"Cluster Status: {json.dumps(cluster_status, indent=2, ensure_ascii=False)}")
    
    # Get all employee status
    employee_status = ai_cluster_manager.get_employee_status()
    logger.info(f"Employee Status: {json.dumps(employee_status, indent=2, ensure_ascii=False)}")
    
    # Test upgrading
    upgrade_result = ai_cluster_manager.upgrade_all({"capabilities": ["new_feature"]})
    logger.info(f"Upgrade Result: {json.dumps(upgrade_result, indent=2, ensure_ascii=False)}")
    
    logger.info("AI Cluster Manager test completed!")

    def cluster_health_check(self):
        """AI集群健康检查"""
        health_status = {}
        for instance_id, instance in self.ai_instances.items():
            try:
                # 检查实例是否在线
                instance.health_check()
                health_status[instance_id] = {
                    'status': 'healthy',
                    'last_check': datetime.datetime.now().isoformat(),
                    'load': instance.get_load()
                }
            except Exception as e:
                health_status[instance_id] = {
                    'status': 'unhealthy',
                    'last_check': datetime.datetime.now().isoformat(),
                    'error': str(e)
                }
        return health_status
    
    def auto_scale_cluster(self, target_load=0.7):
        """自动扩展AI集群"""
        current_health = self.cluster_health_check()
        healthy_instances = [i for i in current_health.values() if i['status'] == 'healthy']
        
        if not healthy_instances:
            # 如果没有健康实例，添加一个新实例
            self.add_ai_instance()
            logger.info("集群自动扩展: 添加了一个新的AI实例")
            return True
        
        # 计算平均负载
        avg_load = sum([i['load'] for i in healthy_instances]) / len(healthy_instances)
        
        if avg_load > target_load:
            # 负载过高，添加新实例
            self.add_ai_instance()
            logger.info(f"集群自动扩展: 平均负载 {avg_load:.2f} 超过阈值 {target_load}, 添加了一个新实例")
            return True
        
        return False
