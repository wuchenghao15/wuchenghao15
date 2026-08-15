#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI 模型部署服务 (v15.0.0)
==================================
AI 模型部署生命周期管理服务，构建模型从开发到生产的完整部署能力。

核心能力：
1. 部署注册表 - 模型部署实例管理
2. 环境管理 - dev/staging/prod 多环境隔离
3. 部署策略 - 蓝绿/金丝雀/滚动三种发布策略
4. 健康检查 - 部署后自动健康探测
5. 流量路由 - 按权重分流和A/B测试
6. 回滚机制 - 版本回滚和快速恢复
7. 自动扩缩容 - 基于指标自动调整实例数
8. 部署审计 - 完整部署历史和变更追踪
"""
import os
import json
import time
import uuid
import random
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_model_deployment.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIModelDeployment')


# ========== 环境管理 ==========

ENVIRONMENTS = {
    'dev': {
        'name': '开发环境',
        'description': '开发和测试环境',
        'min_instances': 1,
        'max_instances': 3,
        'auto_scale': False,
        'health_check_interval': 60,
        'require_approval': False
    },
    'staging': {
        'name': '预发布环境',
        'description': '预发布验证环境',
        'min_instances': 2,
        'max_instances': 5,
        'auto_scale': True,
        'health_check_interval': 30,
        'require_approval': True
    },
    'prod': {
        'name': '生产环境',
        'description': '生产环境',
        'min_instances': 3,
        'max_instances': 20,
        'auto_scale': True,
        'health_check_interval': 15,
        'require_approval': True
    }
}

DEPLOYMENT_STRATEGIES = {
    'blue_green': {
        'name': '蓝绿部署',
        'description': '同时维护两个环境，切换流量实现零停机部署',
        'steps': ['prepare_green', 'deploy_green', 'verify_green', 'switch_traffic', 'cleanup_blue']
    },
    'canary': {
        'name': '金丝雀发布',
        'description': '逐步增加新版本流量比例，按比例灰度发布',
        'steps': ['deploy_canary', 'route_5_percent', 'monitor', 'route_25_percent',
                  'monitor', 'route_50_percent', 'monitor', 'route_100_percent']
    },
    'rolling': {
        'name': '滚动更新',
        'description': '逐个替换实例，分批滚动更新',
        'steps': ['batch_1', 'batch_2', 'batch_3', 'finalize']
    }
}

DEPLOYMENT_STATUS = {
    'pending': '待部署',
    'deploying': '部署中',
    'running': '运行中',
    'verifying': '验证中',
    'failed': '部署失败',
    'rolled_back': '已回滚',
    'stopped': '已停止',
    'deprecated': '已弃用'
}


# ========== 部署实例 ==========

class DeploymentInstance:
    """模型部署实例"""

    def __init__(self, deployment_id: str, model_id: str, model_version: str,
                 environment: str, strategy: str = 'rolling',
                 instances: int = 1, endpoint: str = '',
                 config: Optional[Dict] = None):
        self.deployment_id = deployment_id
        self.model_id = model_id
        self.model_version = model_version
        self.environment = environment
        self.strategy = strategy
        self.instances = instances
        self.endpoint = endpoint
        self.config = config or {}
        self.status = 'pending'
        self.traffic_weight = 0  # 流量权重百分比
        self.health_status = 'unknown'  # unknown/healthy/unhealthy/degraded
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.deployed_at = None
        self.last_health_check = None
        self.error_message = ''
        self.metrics = {
            'requests': 0,
            'errors': 0,
            'avg_latency_ms': 0.0,
            'cpu_usage': 0.0,
            'memory_usage': 0.0
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            'deployment_id': self.deployment_id,
            'model_id': self.model_id,
            'model_version': self.model_version,
            'environment': self.environment,
            'strategy': self.strategy,
            'instances': self.instances,
            'endpoint': self.endpoint,
            'config': self.config,
            'status': self.status,
            'traffic_weight': self.traffic_weight,
            'health_status': self.health_status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'deployed_at': self.deployed_at,
            'last_health_check': self.last_health_check,
            'error_message': self.error_message,
            'metrics': self.metrics
        }


# ========== 健康检查器 ==========

class HealthChecker:
    """部署健康检查器"""

    def __init__(self):
        self.checks: Dict[str, Callable] = {
            'endpoint_reachable': self._check_endpoint,
            'response_time': self._check_response_time,
            'error_rate': self._check_error_rate,
            'resource_usage': self._check_resource_usage
        }

    def _check_endpoint(self, deployment: DeploymentInstance) -> Tuple[bool, str]:
        """检查端点可达性（模拟）"""
        if not deployment.endpoint:
            return False, '端点未配置'
        # 模拟检查
        if deployment.status != 'running':
            return False, f'部署状态异常: {deployment.status}'
        return True, '端点可达'

    def _check_response_time(self, deployment: DeploymentInstance,
                              threshold_ms: float = 2000) -> Tuple[bool, str]:
        """检查响应时间"""
        latency = deployment.metrics.get('avg_latency_ms', 0)
        if latency == 0:
            return True, '无延迟数据'
        if latency > threshold_ms:
            return False, f'响应时间过长: {latency}ms > {threshold_ms}ms'
        return True, f'响应时间正常: {latency}ms'

    def _check_error_rate(self, deployment: DeploymentInstance,
                           threshold: float = 0.05) -> Tuple[bool, str]:
        """检查错误率"""
        requests = deployment.metrics.get('requests', 0)
        errors = deployment.metrics.get('errors', 0)
        if requests == 0:
            return True, '无请求数据'
        rate = errors / requests
        if rate > threshold:
            return False, f'错误率过高: {rate:.2%} > {threshold:.2%}'
        return True, f'错误率正常: {rate:.2%}'

    def _check_resource_usage(self, deployment: DeploymentInstance,
                               threshold: float = 0.9) -> Tuple[bool, str]:
        """检查资源使用率"""
        cpu = deployment.metrics.get('cpu_usage', 0)
        memory = deployment.metrics.get('memory_usage', 0)
        if cpu > threshold:
            return False, f'CPU使用率过高: {cpu:.1%}'
        if memory > threshold:
            return False, f'内存使用率过高: {memory:.1%}'
        return True, f'资源使用正常: CPU={cpu:.1%} MEM={memory:.1%}'

    def run_checks(self, deployment: DeploymentInstance) -> Dict[str, Any]:
        """运行所有健康检查"""
        results = []
        all_pass = True
        for check_name, check_fn in self.checks.items():
            try:
                passed, message = check_fn(deployment)
                results.append({
                    'check': check_name,
                    'passed': passed,
                    'message': message
                })
                if not passed:
                    all_pass = False
            except Exception as e:
                results.append({
                    'check': check_name,
                    'passed': False,
                    'message': f'检查异常: {str(e)}'
                })
                all_pass = False

        return {
            'healthy': all_pass,
            'checks': results,
            'checked_at': datetime.now().isoformat(),
            'deployment_id': deployment.deployment_id
        }


# ========== 自动扩缩容 ==========

class AutoScaler:
    """自动扩缩容管理器"""

    def __init__(self):
        self.policies: Dict[str, Dict] = {}
        self._load_default_policies()

    def _load_default_policies(self):
        """加载默认扩缩容策略"""
        self.policies = {
            'cpu_based': {
                'name': '基于CPU使用率',
                'metric': 'cpu_usage',
                'scale_up_threshold': 0.7,
                'scale_down_threshold': 0.3,
                'scale_up_step': 1,
                'scale_down_step': 1,
                'cooldown_seconds': 300
            },
            'latency_based': {
                'name': '基于响应延迟',
                'metric': 'avg_latency_ms',
                'scale_up_threshold': 1000,
                'scale_down_threshold': 200,
                'scale_up_step': 2,
                'scale_down_step': 1,
                'cooldown_seconds': 180
            },
            'error_rate_based': {
                'name': '基于错误率',
                'metric': 'error_rate',
                'scale_up_threshold': 0.05,
                'scale_down_threshold': 0.01,
                'scale_up_step': 2,
                'scale_down_step': 1,
                'cooldown_seconds': 600
            }
        }

    def evaluate(self, deployment: DeploymentInstance,
                  policy_name: str = 'cpu_based') -> Dict[str, Any]:
        """评估扩缩容决策"""
        policy = self.policies.get(policy_name)
        if not policy:
            return {'action': 'none', 'reason': f'策略不存在: {policy_name}'}

        env_config = ENVIRONMENTS.get(deployment.environment, {})
        min_instances = env_config.get('min_instances', 1)
        max_instances = env_config.get('max_instances', 10)

        metric = policy['metric']
        current_value = self._get_metric_value(deployment, metric)
        current_instances = deployment.instances

        action = 'none'
        reason = '指标正常'
        target_instances = current_instances

        if metric == 'error_rate':
            if current_value > policy['scale_up_threshold']:
                action = 'scale_up'
                target_instances = min(current_instances + policy['scale_up_step'], max_instances)
                reason = f'{metric}={current_value:.2%} > {policy["scale_up_threshold"]:.2%}'
            elif current_value < policy['scale_down_threshold']:
                action = 'scale_down'
                target_instances = max(current_instances - policy['scale_down_step'], min_instances)
                reason = f'{metric}={current_value:.2%} < {policy["scale_down_threshold"]:.2%}'
        else:
            if current_value > policy['scale_up_threshold']:
                action = 'scale_up'
                target_instances = min(current_instances + policy['scale_up_step'], max_instances)
                reason = f'{metric}={current_value:.2f} > {policy["scale_up_threshold"]}'
            elif current_value < policy['scale_down_threshold']:
                action = 'scale_down'
                target_instances = max(current_instances - policy['scale_down_step'], min_instances)
                reason = f'{metric}={current_value:.2f} < {policy["scale_down_threshold"]}'

        if action != 'none' and target_instances == current_instances:
            action = 'none'
            reason += ' (已达实例上限/下限)'

        return {
            'action': action,
            'reason': reason,
            'policy': policy_name,
            'current_instances': current_instances,
            'target_instances': target_instances,
            'metric': metric,
            'current_value': current_value,
            'threshold_up': policy['scale_up_threshold'],
            'threshold_down': policy['scale_down_threshold']
        }

    def _get_metric_value(self, deployment: DeploymentInstance, metric: str) -> float:
        """获取指标值"""
        if metric == 'error_rate':
            requests = deployment.metrics.get('requests', 0)
            errors = deployment.metrics.get('errors', 0)
            return errors / requests if requests > 0 else 0.0
        return deployment.metrics.get(metric, 0.0)


# ========== 部署服务主类 ==========

class AIModelDeploymentService:
    """AI 模型部署服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self.health_checker = HealthChecker()
        self.auto_scaler = AutoScaler()
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """初始化数据库表"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 部署记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_model_deployments (
                        deployment_id TEXT PRIMARY KEY,
                        model_id TEXT NOT NULL,
                        model_version TEXT NOT NULL,
                        environment TEXT NOT NULL,
                        strategy TEXT NOT NULL,
                        instances INTEGER DEFAULT 1,
                        endpoint TEXT,
                        config TEXT,
                        status TEXT DEFAULT 'pending',
                        traffic_weight INTEGER DEFAULT 0,
                        health_status TEXT DEFAULT 'unknown',
                        created_at TEXT,
                        updated_at TEXT,
                        deployed_at TEXT,
                        last_health_check TEXT,
                        error_message TEXT,
                        metrics TEXT
                    )
                ''')
                # 部署历史表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_deployment_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        deployment_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        from_status TEXT,
                        to_status TEXT,
                        details TEXT,
                        operator TEXT,
                        created_at TEXT
                    )
                ''')
                # 健康检查记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_deployment_health_checks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        deployment_id TEXT NOT NULL,
                        healthy INTEGER NOT NULL,
                        checks TEXT,
                        checked_at TEXT
                    )
                ''')
                # 扩缩容记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_deployment_scalings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        deployment_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        policy TEXT,
                        from_instances INTEGER,
                        to_instances INTEGER,
                        reason TEXT,
                        created_at TEXT
                    )
                ''')
                # 流量路由表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_traffic_routes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_id TEXT NOT NULL,
                        environment TEXT NOT NULL,
                        deployment_id TEXT NOT NULL,
                        weight INTEGER DEFAULT 0,
                        route_type TEXT DEFAULT 'weighted',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 回滚记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_deployment_rollbacks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        deployment_id TEXT NOT NULL,
                        target_version TEXT NOT NULL,
                        reason TEXT,
                        rollback_type TEXT DEFAULT 'manual',
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        completed_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('AI模型部署服务数据库初始化完成')
        except Exception as e:
            logger.error(f'初始化数据库失败: {e}')

    # ========== 部署管理 ==========

    def create_deployment(self, model_id: str, model_version: str,
                          environment: str, strategy: str = 'rolling',
                          instances: int = 1, endpoint: str = '',
                          config: Optional[Dict] = None) -> Dict[str, Any]:
        """创建部署"""
        with self._lock:
            if environment not in ENVIRONMENTS:
                return {'success': False, 'error': f'未知环境: {environment}'}
            if strategy not in DEPLOYMENT_STRATEGIES:
                return {'success': False, 'error': f'未知部署策略: {strategy}'}

            env_config = ENVIRONMENTS[environment]
            if instances < env_config['min_instances']:
                instances = env_config['min_instances']
            elif instances > env_config['max_instances']:
                instances = env_config['max_instances']

            deployment_id = f'deploy_{int(time.time())}_{uuid.uuid4().hex[:8]}'
            deployment = DeploymentInstance(
                deployment_id=deployment_id,
                model_id=model_id,
                model_version=model_version,
                environment=environment,
                strategy=strategy,
                instances=instances,
                endpoint=endpoint or f'http://{environment}-serving:8080/predict',
                config=config or {}
            )

            # 持久化
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ai_model_deployments
                        (deployment_id, model_id, model_version, environment, strategy,
                         instances, endpoint, config, status, traffic_weight, health_status,
                         created_at, updated_at, deployed_at, last_health_check,
                         error_message, metrics)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        deployment.deployment_id, deployment.model_id, deployment.model_version,
                        deployment.environment, deployment.strategy, deployment.instances,
                        deployment.endpoint, json.dumps(deployment.config),
                        deployment.status, deployment.traffic_weight, deployment.health_status,
                        deployment.created_at, deployment.updated_at, deployment.deployed_at,
                        deployment.last_health_check, deployment.error_message,
                        json.dumps(deployment.metrics)
                    ))
                    # 记录历史
                    self._record_history(conn, deployment_id, 'created', None, 'pending',
                                          {'model_id': model_id, 'version': model_version,
                                           'environment': environment, 'strategy': strategy})
                    conn.commit()
            except Exception as e:
                logger.error(f'创建部署失败: {e}')
                return {'success': False, 'error': str(e)}

            logger.info(f'创建部署 {deployment_id} (model={model_id} v{model_version} env={environment})')
            return {
                'success': True,
                'deployment_id': deployment_id,
                'deployment': deployment.to_dict()
            }

    def deploy(self, deployment_id: str, operator: str = 'system') -> Dict[str, Any]:
        """执行部署"""
        with self._lock:
            deployment = self._get_deployment(deployment_id)
            if not deployment:
                return {'success': False, 'error': '部署不存在'}

            if deployment['status'] not in ('pending', 'failed'):
                return {'success': False, 'error': f'部署状态不允许部署: {deployment["status"]}'}

            strategy = deployment['strategy']
            strategy_config = DEPLOYMENT_STRATEGIES.get(strategy, {})
            steps = strategy_config.get('steps', [])

            try:
                # 更新状态为部署中
                self._update_deployment_status(deployment_id, 'deploying', operator=operator)

                # 模拟执行部署步骤
                executed_steps = []
                for step in steps:
                    step_result = self._execute_deploy_step(deployment_id, step, deployment)
                    executed_steps.append({
                        'step': step,
                        'status': 'success' if step_result else 'failed',
                        'timestamp': datetime.now().isoformat()
                    })
                    if not step_result:
                        raise Exception(f'步骤执行失败: {step}')

                # 部署完成
                now = datetime.now().isoformat()
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE ai_model_deployments
                        SET status = 'running', deployed_at = ?, updated_at = ?,
                            health_status = 'unknown', error_message = ''
                        WHERE deployment_id = ?
                    ''', (now, now, deployment_id))
                    self._record_history(conn, deployment_id, 'deployed', 'deploying', 'running',
                                          {'steps': executed_steps, 'operator': operator})
                    conn.commit()

                logger.info(f'部署 {deployment_id} 执行成功 (策略: {strategy})')
                return {
                    'success': True,
                    'deployment_id': deployment_id,
                    'status': 'running',
                    'strategy': strategy,
                    'executed_steps': executed_steps
                }
            except Exception as e:
                # 部署失败
                self._update_deployment_status(deployment_id, 'failed',
                                                error=str(e), operator=operator)
                logger.error(f'部署 {deployment_id} 执行失败: {e}')
                return {'success': False, 'error': str(e), 'deployment_id': deployment_id}

    def _execute_deploy_step(self, deployment_id: str, step: str,
                              deployment: Dict) -> bool:
        """执行单个部署步骤（模拟）"""
        # 模拟部署步骤执行
        time.sleep(0.1)
        # 95% 成功率模拟
        return random.random() < 0.95

    def stop_deployment(self, deployment_id: str, operator: str = 'system') -> Dict[str, Any]:
        """停止部署"""
        with self._lock:
            deployment = self._get_deployment(deployment_id)
            if not deployment:
                return {'success': False, 'error': '部署不存在'}

            if deployment['status'] != 'running':
                return {'success': False, 'error': f'部署状态不允许停止: {deployment["status"]}'}

            self._update_deployment_status(deployment_id, 'stopped', operator=operator)
            # 流量权重置零
            self._update_traffic_weight(deployment_id, 0)
            logger.info(f'部署 {deployment_id} 已停止')
            return {'success': True, 'deployment_id': deployment_id, 'status': 'stopped'}

    # ========== 回滚管理 ==========

    def rollback(self, deployment_id: str, target_version: str,
                  reason: str = '', operator: str = 'system') -> Dict[str, Any]:
        """回滚到指定版本"""
        with self._lock:
            deployment = self._get_deployment(deployment_id)
            if not deployment:
                return {'success': False, 'error': '部署不存在'}

            rollback_id = None
            try:
                now = datetime.now().isoformat()
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    # 创建回滚记录
                    cursor.execute('''
                        INSERT INTO ai_deployment_rollbacks
                        (deployment_id, target_version, reason, rollback_type, status, created_at)
                        VALUES (?, ?, ?, 'manual', 'pending', ?)
                    ''', (deployment_id, target_version, reason, now))
                    rollback_id = cursor.lastrowid

                    # 执行回滚：更新版本和状态
                    old_version = deployment['model_version']
                    cursor.execute('''
                        UPDATE ai_model_deployments
                        SET model_version = ?, status = 'running', updated_at = ?,
                            health_status = 'unknown', error_message = ''
                        WHERE deployment_id = ?
                    ''', (target_version, now, deployment_id))

                    self._record_history(conn, deployment_id, 'rollback',
                                          deployment['status'], 'running',
                                          {'from_version': old_version, 'to_version': target_version,
                                           'reason': reason, 'operator': operator})

                    # 更新回滚记录为完成
                    cursor.execute('''
                        UPDATE ai_deployment_rollbacks
                        SET status = 'completed', completed_at = ?
                        WHERE id = ?
                    ''', (now, rollback_id))
                    conn.commit()

                logger.info(f'部署 {deployment_id} 回滚成功: {old_version} -> {target_version}')
                return {
                    'success': True,
                    'deployment_id': deployment_id,
                    'rollback_id': rollback_id,
                    'from_version': old_version,
                    'to_version': target_version
                }
            except Exception as e:
                logger.error(f'回滚失败: {e}')
                if rollback_id:
                    with self._get_connection() as conn:
                        conn.execute('''
                            UPDATE ai_deployment_rollbacks
                            SET status = 'failed', completed_at = ?
                            WHERE id = ?
                        ''', (datetime.now().isoformat(), rollback_id))
                        conn.commit()
                return {'success': False, 'error': str(e)}

    # ========== 流量路由 ==========

    def update_traffic(self, model_id: str, environment: str,
                       routing: Dict[str, int]) -> Dict[str, Any]:
        """更新流量路由（deployment_id -> weight）"""
        with self._lock:
            total = sum(routing.values())
            if total != 100:
                return {'success': False, 'error': f'权重总和必须为100，当前为{total}'}

            try:
                now = datetime.now().isoformat()
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    # 清除旧路由
                    cursor.execute('''
                        DELETE FROM ai_traffic_routes
                        WHERE model_id = ? AND environment = ?
                    ''', (model_id, environment))
                    # 插入新路由
                    for deployment_id, weight in routing.items():
                        cursor.execute('''
                            INSERT INTO ai_traffic_routes
                            (model_id, environment, deployment_id, weight, route_type, created_at, updated_at)
                            VALUES (?, ?, ?, ?, 'weighted', ?, ?)
                        ''', (model_id, environment, deployment_id, weight, now, now))
                        # 更新部署的流量权重
                        cursor.execute('''
                            UPDATE ai_model_deployments
                            SET traffic_weight = ?, updated_at = ?
                            WHERE deployment_id = ?
                        ''', (weight, now, deployment_id))
                    conn.commit()

                logger.info(f'更新流量路由: model={model_id} env={environment} routing={routing}')
                return {'success': True, 'model_id': model_id, 'environment': environment, 'routing': routing}
            except Exception as e:
                logger.error(f'更新流量路由失败: {e}')
                return {'success': False, 'error': str(e)}

    def _update_traffic_weight(self, deployment_id: str, weight: int):
        """更新单个部署流量权重"""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute('''
                UPDATE ai_model_deployments
                SET traffic_weight = ?, updated_at = ?
                WHERE deployment_id = ?
            ''', (weight, now, deployment_id))
            conn.commit()

    # ========== 健康检查 ==========

    def run_health_check(self, deployment_id: str) -> Dict[str, Any]:
        """运行健康检查"""
        with self._lock:
            deployment_data = self._get_deployment(deployment_id)
            if not deployment_data:
                return {'success': False, 'error': '部署不存在'}

            # 转换为实例对象
            deployment = self._dict_to_instance(deployment_data)
            result = self.health_checker.run_checks(deployment)

            # 更新部署健康状态
            now = datetime.now().isoformat()
            health_status = 'healthy' if result['healthy'] else 'unhealthy'
            if result['healthy'] and deployment.metrics.get('avg_latency_ms', 0) > 1500:
                health_status = 'degraded'

            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE ai_model_deployments
                        SET health_status = ?, last_health_check = ?, updated_at = ?
                        WHERE deployment_id = ?
                    ''', (health_status, now, now, deployment_id))

                    # 记录健康检查
                    cursor.execute('''
                        INSERT INTO ai_deployment_health_checks
                        (deployment_id, healthy, checks, checked_at)
                        VALUES (?, ?, ?, ?)
                    ''', (deployment_id, 1 if result['healthy'] else 0,
                          json.dumps(result['checks']), now))
                    conn.commit()
            except Exception as e:
                logger.error(f'保存健康检查结果失败: {e}')

            result['health_status'] = health_status
            return {'success': True, **result}

    # ========== 自动扩缩容 ==========

    def evaluate_scaling(self, deployment_id: str,
                          policy_name: str = 'cpu_based') -> Dict[str, Any]:
        """评估扩缩容"""
        with self._lock:
            deployment_data = self._get_deployment(deployment_id)
            if not deployment_data:
                return {'success': False, 'error': '部署不存在'}

            deployment = self._dict_to_instance(deployment_data)
            decision = self.auto_scaler.evaluate(deployment, policy_name)

            # 如果需要扩缩容，执行
            if decision['action'] in ('scale_up', 'scale_down'):
                target = decision['target_instances']
                current = decision['current_instances']
                if target != current:
                    self._scale_deployment(deployment_id, current, target,
                                            decision['reason'], policy_name)
                    decision['executed'] = True
                else:
                    decision['executed'] = False
                    decision['reason'] += ' (无需变更)'
            else:
                decision['executed'] = False

            return {'success': True, **decision}

    def _scale_deployment(self, deployment_id: str, from_n: int, to_n: int,
                           reason: str, policy: str):
        """执行扩缩容"""
        now = datetime.now().isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE ai_model_deployments
                    SET instances = ?, updated_at = ?
                    WHERE deployment_id = ?
                ''', (to_n, now, deployment_id))
                cursor.execute('''
                    INSERT INTO ai_deployment_scalings
                    (deployment_id, action, policy, from_instances, to_instances, reason, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (deployment_id,
                      'scale_up' if to_n > from_n else 'scale_down',
                      policy, from_n, to_n, reason, now))
                self._record_history(conn, deployment_id, 'scaled', None, None,
                                      {'from': from_n, 'to': to_n, 'reason': reason})
                conn.commit()
            logger.info(f'部署 {deployment_id} 扩缩容: {from_n} -> {to_n} ({reason})')
        except Exception as e:
            logger.error(f'扩缩容失败: {e}')

    # ========== 指标更新 ==========

    def update_metrics(self, deployment_id: str, metrics: Dict[str, float]) -> Dict[str, Any]:
        """更新部署指标"""
        with self._lock:
            try:
                now = datetime.now().isoformat()
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE ai_model_deployments
                        SET metrics = ?, updated_at = ?
                        WHERE deployment_id = ?
                    ''', (json.dumps(metrics), now, deployment_id))
                    conn.commit()
                return {'success': True, 'deployment_id': deployment_id, 'metrics': metrics}
            except Exception as e:
                logger.error(f'更新指标失败: {e}')
                return {'success': False, 'error': str(e)}

    # ========== 查询接口 ==========

    def list_deployments(self, environment: str = None,
                          model_id: str = None,
                          status: str = None) -> Dict[str, Any]:
        """列出部署"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                sql = 'SELECT * FROM ai_model_deployments WHERE 1=1'
                params = []
                if environment:
                    sql += ' AND environment = ?'
                    params.append(environment)
                if model_id:
                    sql += ' AND model_id = ?'
                    params.append(model_id)
                if status:
                    sql += ' AND status = ?'
                    params.append(status)
                sql += ' ORDER BY created_at DESC'
                cursor.execute(sql, params)
                rows = cursor.fetchall()

                columns = ['deployment_id', 'model_id', 'model_version', 'environment',
                           'strategy', 'instances', 'endpoint', 'config', 'status',
                           'traffic_weight', 'health_status', 'created_at', 'updated_at',
                           'deployed_at', 'last_health_check', 'error_message', 'metrics']
                deployments = []
                for row in rows:
                    d = dict(zip(columns, row))
                    try:
                        d['config'] = json.loads(d['config']) if d['config'] else {}
                    except Exception:
                        d['config'] = {}
                    try:
                        d['metrics'] = json.loads(d['metrics']) if d['metrics'] else {}
                    except Exception:
                        d['metrics'] = {}
                    deployments.append(d)
                return {'success': True, 'deployments': deployments, 'count': len(deployments)}
        except Exception as e:
            logger.error(f'列出部署失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """获取部署详情"""
        deployment = self._get_deployment(deployment_id)
        if not deployment:
            return {'success': False, 'error': '部署不存在'}
        return {'success': True, 'deployment': deployment}

    def get_deployment_history(self, deployment_id: str) -> Dict[str, Any]:
        """获取部署历史"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT action, from_status, to_status, details, operator, created_at
                    FROM ai_deployment_history
                    WHERE deployment_id = ?
                    ORDER BY created_at DESC
                ''', (deployment_id,))
                rows = cursor.fetchall()
                history = []
                for row in rows:
                    h = {
                        'action': row[0],
                        'from_status': row[1],
                        'to_status': row[2],
                        'details': json.loads(row[3]) if row[3] else {},
                        'operator': row[4],
                        'created_at': row[5]
                    }
                    history.append(h)
                return {'success': True, 'history': history, 'count': len(history)}
        except Exception as e:
            logger.error(f'获取部署历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 辅助方法 ==========

    def _get_deployment(self, deployment_id: str) -> Optional[Dict]:
        """从数据库获取部署"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT deployment_id, model_id, model_version, environment, strategy,
                           instances, endpoint, config, status, traffic_weight, health_status,
                           created_at, updated_at, deployed_at, last_health_check,
                           error_message, metrics
                    FROM ai_model_deployments
                    WHERE deployment_id = ?
                ''', (deployment_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                d = {
                    'deployment_id': row[0], 'model_id': row[1], 'model_version': row[2],
                    'environment': row[3], 'strategy': row[4], 'instances': row[5],
                    'endpoint': row[6], 'config': json.loads(row[7]) if row[7] else {},
                    'status': row[8], 'traffic_weight': row[9], 'health_status': row[10],
                    'created_at': row[11], 'updated_at': row[12], 'deployed_at': row[13],
                    'last_health_check': row[14], 'error_message': row[15],
                    'metrics': json.loads(row[16]) if row[16] else {}
                }
                return d
        except Exception as e:
            logger.error(f'获取部署失败: {e}')
            return None

    def _dict_to_instance(self, data: Dict) -> DeploymentInstance:
        """字典转实例对象"""
        dep = DeploymentInstance(
            deployment_id=data['deployment_id'],
            model_id=data['model_id'],
            model_version=data['model_version'],
            environment=data['environment'],
            strategy=data['strategy'],
            instances=data['instances'],
            endpoint=data.get('endpoint', ''),
            config=data.get('config', {})
        )
        dep.status = data['status']
        dep.traffic_weight = data['traffic_weight']
        dep.health_status = data['health_status']
        dep.created_at = data['created_at']
        dep.updated_at = data['updated_at']
        dep.deployed_at = data.get('deployed_at')
        dep.last_health_check = data.get('last_health_check')
        dep.error_message = data.get('error_message', '')
        dep.metrics = data.get('metrics', {})
        return dep

    def _update_deployment_status(self, deployment_id: str, status: str,
                                    error: str = '', operator: str = 'system'):
        """更新部署状态"""
        now = datetime.now().isoformat()
        old_status = None
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT status FROM ai_model_deployments WHERE deployment_id = ?',
                                (deployment_id,))
                row = cursor.fetchone()
                if row:
                    old_status = row[0]
                cursor.execute('''
                    UPDATE ai_model_deployments
                    SET status = ?, error_message = ?, updated_at = ?
                    WHERE deployment_id = ?
                ''', (status, error, now, deployment_id))
                self._record_history(conn, deployment_id, 'status_change',
                                      old_status, status, {'operator': operator, 'error': error})
                conn.commit()
        except Exception as e:
            logger.error(f'更新部署状态失败: {e}')

    def _record_history(self, conn, deployment_id: str, action: str,
                          from_status: str, to_status: str, details: Dict):
        """记录历史"""
        now = datetime.now().isoformat()
        operator = details.get('operator', 'system') if details else 'system'
        conn.execute('''
            INSERT INTO ai_deployment_history
            (deployment_id, action, from_status, to_status, details, operator, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (deployment_id, action, from_status, to_status,
              json.dumps(details, ensure_ascii=False), operator, now))

    def get_statistics(self) -> Dict[str, Any]:
        """获取部署统计"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 按状态统计
                cursor.execute('''
                    SELECT status, COUNT(*) FROM ai_model_deployments GROUP BY status
                ''')
                status_stats = {row[0]: row[1] for row in cursor.fetchall()}
                # 按环境统计
                cursor.execute('''
                    SELECT environment, COUNT(*) FROM ai_model_deployments GROUP BY environment
                ''')
                env_stats = {row[0]: row[1] for row in cursor.fetchall()}
                # 按策略统计
                cursor.execute('''
                    SELECT strategy, COUNT(*) FROM ai_model_deployments GROUP BY strategy
                ''')
                strategy_stats = {row[0]: row[1] for row in cursor.fetchall()}
                # 按健康状态统计
                cursor.execute('''
                    SELECT health_status, COUNT(*) FROM ai_model_deployments GROUP BY health_status
                ''')
                health_stats = {row[0]: row[1] for row in cursor.fetchall()}

                # 历史统计
                cursor.execute('SELECT COUNT(*) FROM ai_deployment_history')
                history_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_deployment_scalings')
                scaling_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_deployment_rollbacks')
                rollback_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM ai_deployment_health_checks')
                health_check_count = cursor.fetchone()[0]

                return {
                    'success': True,
                    'total_deployments': sum(status_stats.values()),
                    'by_status': status_stats,
                    'by_environment': env_stats,
                    'by_strategy': strategy_stats,
                    'by_health': health_stats,
                    'history_records': history_count,
                    'scaling_records': scaling_count,
                    'rollback_records': rollback_count,
                    'health_check_records': health_check_count,
                    'available_environments': list(ENVIRONMENTS.keys()),
                    'available_strategies': list(DEPLOYMENT_STRATEGIES.keys())
                }
        except Exception as e:
            logger.error(f'获取统计失败: {e}')
            return {'success': False, 'error': str(e)}


# ========== 模块入口 ==========

if __name__ == '__main__':
    service = AIModelDeploymentService()

    print('=' * 60)
    print('MTSCOS AI 模型部署服务 v15.0.0 测试')
    print('=' * 60)

    # 创建部署
    print('\n1. 创建蓝绿部署...')
    result = service.create_deployment(
        model_id='gpt-4',
        model_version='v1.0.0',
        environment='staging',
        strategy='blue_green',
        instances=2,
        endpoint='http://staging-serving:8080/predict'
    )
    print(f'   结果: {result["success"]}')
    if result['success']:
        deploy_id = result['deployment_id']

        # 执行部署
        print('\n2. 执行部署...')
        result = service.deploy(deploy_id, operator='admin')
        print(f'   结果: {result["success"]} 状态: {result.get("status")}')

        # 更新指标
        print('\n3. 更新指标...')
        result = service.update_metrics(deploy_id, {
            'requests': 1500,
            'errors': 15,
            'avg_latency_ms': 350,
            'cpu_usage': 0.78,
            'memory_usage': 0.62
        })
        print(f'   结果: {result["success"]}')

        # 健康检查
        print('\n4. 健康检查...')
        result = service.run_health_check(deploy_id)
        print(f'   健康: {result.get("healthy")} 状态: {result.get("health_status")}')

        # 扩缩容评估
        print('\n5. 扩缩容评估 (CPU策略)...')
        result = service.evaluate_scaling(deploy_id, 'cpu_based')
        print(f'   动作: {result.get("action")} 目标实例: {result.get("target_instances")}')
        print(f'   原因: {result.get("reason")}')

        # 流量路由
        print('\n6. 更新流量路由...')
        result = service.update_traffic('gpt-4', 'staging', {deploy_id: 100})
        print(f'   结果: {result["success"]}')

        # 回滚
        print('\n7. 回滚到 v0.9.0...')
        result = service.rollback(deploy_id, 'v0.9.0', reason='性能不达标', operator='admin')
        print(f'   结果: {result["success"]}')

        # 历史记录
        print('\n8. 获取历史...')
        result = service.get_deployment_history(deploy_id)
        print(f'   历史记录数: {result.get("count", 0)}')
        for h in result.get('history', [])[:3]:
            print(f'   - {h["action"]} @ {h["created_at"]}')

    # 统计
    print('\n9. 部署统计...')
    stats = service.get_statistics()
    print(f'   总部署数: {stats.get("total_deployments")}')
    print(f'   按状态: {stats.get("by_status")}')
    print(f'   按环境: {stats.get("by_environment")}')
    print(f'   按策略: {stats.get("by_strategy")}')
    print(f'   按健康: {stats.get("by_health")}')

    print('\n' + '=' * 60)
    print('测试完成')
    print('=' * 60)
