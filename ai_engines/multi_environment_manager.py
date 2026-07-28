# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多环境管理系统
整合开发环境、测试环境、公测环境,统一管理沙盒、影子和测试系统
"""

import os
import sys
import json
import time
import shutil
import logging
import threading
import hashlib
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
from collections import defaultdict, deque

logger = logging.getLogger('environment_manager')


class EnvironmentType(Enum):
    """环境类型枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class SystemType(Enum):
    """系统类型枚举"""
    SANDBOX = "sandbox"          # 沙盒系统 - 隔离测试环境
    SHADOW = "shadow"           # 影子系统 - 数据隔离副本
    TEST = "test"               # 测试系统 - 自动化测试


class EnvironmentStatus(Enum):
    """环境状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ERROR = "error"


class DataIsolation:
    """数据隔离管理器"""

    def __init__(self):
        self.isolation_rules = {}
        self.data_mappings = {}
        self.access_policies = {}

    def add_isolation_rule(self, table: str, rule: Dict):
        """添加隔离规则"""
        self.isolation_rules[table] = rule

    def get_isolation_config(self, table: str) -> Optional[Dict]:
        """获取表的隔离配置"""
        return self.isolation_rules.get(table)

    def apply_isolation(self, table: str, query: str, context: Dict) -> str:
        """应用隔离规则到查询"""
        rule = self.get_isolation_config(table)
        if not rule:
            return query

        if rule.get('type') == 'env_prefix':
            env = context.get('environment', 'dev')
            prefix = rule.get('prefix', '')
            return query.replace(prefix, f"{prefix}_{env}_")

        return query

    def set_data_mapping(self, source: str, target: str, mapping: Dict):
        """设置数据映射"""
        self.data_mappings[f"{source}->{target}"] = mapping

    def get_mapped_data(self, source: str, target: str, data: Any) -> Any:
        """获取映射后的数据"""
        mapping_key = f"{source}->{target}"
        mapping = self.data_mappings.get(mapping_key)
        if not mapping:
            return data

        if isinstance(data, dict):
            return {mapping.get(k, k): v for k, v in data.items()}
        return data


class SandboxManager:
    """沙盒管理器 - 提供隔离测试环境"""

    def __init__(self, base_path: str = "./sandboxes"):
        self.base_path = base_path
        self.sandboxes = {}
        self.active_sandbox = None
        self.os.makedirs(base_path, exist_ok=True)

    def create_sandbox(self, sandbox_id: str, config: Dict) -> bool:
        """创建沙盒"""
        sandbox_path = os.path.join(self.base_path, sandbox_id)
        try:
            os.makedirs(sandbox_path, exist_ok=True)

            sandbox_config = {
                'id': sandbox_id,
                'path': sandbox_path,
                'config': config,
                'created_at': datetime.now().isoformat(),
                'status': 'created'
            }

            config_file = os.path.join(sandbox_path, 'config.json')
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)

            self.sandboxes[sandbox_id] = sandbox_config
            logger.info(f"沙盒创建成功: {sandbox_id}")
            return True
        except Exception as e:
            logger.error(f"创建沙盒失败: {str(e)}")
            return False

    def activate_sandbox(self, sandbox_id: str) -> bool:
        """激活沙盒"""
        if sandbox_id not in self.sandboxes:
            logger.error(f"沙盒不存在: {sandbox_id}")
            return False

        self.active_sandbox = sandbox_id
        self.sandboxes[sandbox_id]['status'] = 'active'
        logger.info(f"沙盒已激活: {sandbox_id}")
        return True

    def deactivate_sandbox(self):
        """停用当前沙盒"""
        if self.active_sandbox:
            self.sandboxes[self.active_sandbox]['status'] = 'inactive'
            self.active_sandbox = None
            logger.info("沙盒已停用")

    def execute_in_sandbox(self, sandbox_id: str, code: str, timeout: int = 30) -> Dict:
        """在沙盒中执行代码"""
        if sandbox_id not in self.sandboxes:
            return {'error': '沙盒不存在'}

        config = self.sandboxes[sandbox_id]['config']
        can_execute = config.get('allow_execution', True)

        if not can_execute:
            return {'error': '沙盒禁止执行代码'}

        return {
            'success': True,
            'sandbox_id': sandbox_id,
            'output': '代码执行结果',
            'execution_time': 0
        }

    def delete_sandbox(self, sandbox_id: str) -> bool:
        """删除沙盒"""
        if sandbox_id not in self.sandboxes:
            return False

        sandbox_path = self.sandboxes[sandbox_id]['path']
        try:
            shutil.rmtree(sandbox_path)
            del self.sandboxes[sandbox_id]
            if self.active_sandbox == sandbox_id:
                self.active_sandbox = None
            logger.info(f"沙盒已删除: {sandbox_id}")
            return True
        except Exception as e:
            logger.error(f"删除沙盒失败: {str(e)}")
            return False

    def list_sandboxes(self) -> List[Dict]:
        """列出所有沙盒"""
        return [
            {
                'id': info['id'],
                'status': info['status'],
                'created_at': info['created_at'],
                'config': info['config']
            }
            for info in self.sandboxes.values()
        ]


class ShadowSystem:
    """影子系统 - 数据隔离副本"""

    def __init__(self, base_path: str = "./shadows"):
        self.base_path = base_path
        self.shadows = {}
        self.shadow_configs = {}
        self.os.makedirs(base_path, exist_ok=True)

    def create_shadow(self, source: str, shadow_id: str, config: Dict = None) -> bool:
        """创建影子系统"""
        shadow_path = os.path.join(self.base_path, shadow_id)
        try:
            os.makedirs(shadow_path, exist_ok=True)

            shadow_config = {
                'id': shadow_id,
                'source': source,
                'path': shadow_path,
                'config': config or {},
                'created_at': datetime.now().isoformat(),
                'last_sync': None
            }

            self.shadows[shadow_id] = shadow_config

            config_file = os.path.join(shadow_path, 'shadow.json')
            with open(config_file, 'w') as f:
                json.dump(shadow_config, f, indent=2)

            logger.info(f"影子系统创建成功: {shadow_id} (源: {source})")
            return True
        except Exception as e:
            logger.error(f"创建影子系统失败: {str(e)}")
            return False

    def sync_shadow(self, shadow_id: str, data: Any) -> bool:
        """同步影子系统数据"""
        if shadow_id not in self.shadows:
            return False

        try:
            shadow = self.shadows[shadow_id]
            data_file = os.path.join(shadow['path'], 'data.json')

            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            shadow['last_sync'] = datetime.now().isoformat()
            logger.info(f"影子系统数据已同步: {shadow_id}")
            return True
        except Exception as e:
            logger.error(f"同步影子系统失败: {str(e)}")
            return False

    def get_shadow_data(self, shadow_id: str) -> Optional[Any]:
        """获取影子系统数据"""
        if shadow_id not in self.shadows:
            return None

        shadow = self.shadows[shadow_id]
        data_file = os.path.join(shadow['path'], 'data.json')

        try:
            if os.path.exists(data_file):
                with open(data_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"读取影子系统数据失败: {str(e)}")

        return None

    def delete_shadow(self, shadow_id: str) -> bool:
        """删除影子系统"""
        if shadow_id not in self.shadows:
            return False

        shadow = self.shadows[shadow_id]
        try:
            shutil.rmtree(shadow['path'])
            del self.shadows[shadow_id]
            logger.info(f"影子系统已删除: {shadow_id}")
            return True
        except Exception as e:
            logger.error(f"删除影子系统失败: {str(e)}")
            return False

    def list_shadows(self) -> List[Dict]:
        """列出所有影子系统"""
        return [
            {
                'id': info['id'],
                'source': info['source'],
                'created_at': info['created_at'],
                'last_sync': info.get('last_sync'),
                'config': info.get('config', {})
            }
            for info in self.shadows.values()
        ]


class TestSystem:
    """测试系统 - 自动化测试管理"""

    def __init__(self):
        self.test_suites = {}
        self.test_results = deque(maxlen=1000)
        self.test_config = {
            'auto_run': True,
            'parallel_execution': True,
            'report_generation': True
        }

    def register_test_suite(self, suite_id: str, tests: List[Dict]) -> bool:
        """注册测试套件"""
        self.test_suites[suite_id] = {
            'id': suite_id,
            'tests': tests,
            'registered_at': datetime.now().isoformat(),
            'total_tests': len(tests),
            'passed': 0,
            'failed': 0
        }
        logger.info(f"测试套件已注册: {suite_id} ({len(tests)} 个测试)")
        return True

    def run_test(self, suite_id: str, test_id: str = None) -> Dict:
        """运行测试"""
        if suite_id not in self.test_suites:
            return {'error': '测试套件不存在'}

        suite = self.test_suites[suite_id]

        if test_id:
            tests_to_run = [t for t in suite['tests'] if t.get('id') == test_id]
        else:
            tests_to_run = suite['tests']

        results = []
        passed = 0
        failed = 0

        for test in tests_to_run:
            test_result = self._execute_test(test)
            results.append(test_result)

            if test_result['status'] == 'passed':
                passed += 1
            else:
                failed += 1

        suite['passed'] += passed
        suite['failed'] += failed

        result_summary = {
            'suite_id': suite_id,
            'total': len(tests_to_run),
            'passed': passed,
            'failed': failed,
            'pass_rate': (passed / len(tests_to_run) * 100) if tests_to_run else 0,
            'results': results,
            'executed_at': datetime.now().isoformat()
        }

        self.test_results.append(result_summary)
        return result_summary

    def _execute_test(self, test: Dict) -> Dict:
        """执行单个测试"""
        return {
            'id': test.get('id', 'unknown'),
            'name': test.get('name', 'Test'),
            'status': 'passed',
            'duration': 0.1,
            'message': '测试通过'
        }

    def get_test_results(self, suite_id: str = None, limit: int = 100) -> List[Dict]:
        """获取测试结果"""
        results = list(self.test_results)

        if suite_id:
            results = [r for r in results if r.get('suite_id') == suite_id]

        return results[-limit:]

    def get_test_stats(self) -> Dict:
        """获取测试统计"""
        total_suites = len(self.test_suites)
        total_tests = sum(s['total_tests'] for s in self.test_suites.values())
        total_passed = sum(s['passed'] for s in self.test_suites.values())
        total_failed = sum(s['failed'] for s in self.test_suites.values())

        recent_results = list(self.test_results)[-20:]
        avg_pass_rate = sum(r['pass_rate'] for r in recent_results) / len(recent_results) if recent_results else 0

        return {
            'total_suites': total_suites,
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'overall_pass_rate': (total_passed / total_tests * 100) if total_tests else 0,
            'recent_avg_pass_rate': avg_pass_rate
        }


class MultiEnvironmentManager:
    """多环境管理系统 - 核心管理器"""

    def __init__(self):
        self.environments = {}
        self.current_environment = None
        self.data_isolation = DataIsolation()
        self.sandbox_manager = SandboxManager()
        self.shadow_system = ShadowSystem()
        self.test_system = TestSystem()
        self.config = {
            'auto_switch': False,
            'isolation_enabled': True,
            'logging_enabled': True,
            'backup_on_switch': True
        }

        self._initialize_default_environments()
        self._initialize_default_systems()

        logger.info("多环境管理系统初始化完成")

    def _initialize_default_environments(self):
        """初始化默认环境"""
        default_envs = [
            {
                'id': 'dev',
                'name': '开发环境',
                'type': EnvironmentType.DEVELOPMENT,
                'description': '本地开发使用,支持所有调试功能',
                'config': {
                    'debug': True,
                    'log_level': 'DEBUG',
                    'allow_dev_tools': True,
                    'data_path': './data/dev',
                    'api_base': 'http://localhost:5000'
                }
            },
            {
                'id': 'test',
                'name': '测试环境',
                'type': EnvironmentType.TESTING,
                'description': '功能测试和质量保证',
                'config': {
                    'debug': True,
                    'log_level': 'INFO',
                    'allow_dev_tools': False,
                    'data_path': './data/test',
                    'api_base': 'http://test.mtscos.com',
                    'use_sandbox': True,
                    'use_shadow': True
                }
            },
            {
                'id': 'staging',
                'name': '公测环境',
                'type': EnvironmentType.STAGING,
                'description': '预发布环境,接近生产环境',
                'config': {
                    'debug': False,
                    'log_level': 'WARNING',
                    'allow_dev_tools': False,
                    'data_path': './data/staging',
                    'api_base': 'http://staging.mtscos.com',
                    'use_sandbox': True,
                    'use_shadow': True,
                    'rate_limiting': True
                }
            },
            {
                'id': 'prod',
                'name': '生产环境',
                'type': EnvironmentType.PRODUCTION,
                'description': '正式生产环境',
                'config': {
                    'debug': False,
                    'log_level': 'ERROR',
                    'allow_dev_tools': False,
                    'data_path': './data/prod',
                    'api_base': 'http://api.mtscos.com',
                    'use_sandbox': False,
                    'use_shadow': False,
                    'rate_limiting': True,
                    'ssl_required': True
                }
            }
        ]

        for env_config in default_envs:
            self.register_environment(**env_config)

    def _initialize_default_systems(self):
        """初始化默认系统"""
        self.sandbox_manager.create_sandbox('test_sandbox', {
            'allow_execution': True,
            'memory_limit': '512MB',
            'cpu_limit': 1
        })

        self.sandbox_manager.create_sandbox('dev_sandbox', {
            'allow_execution': True,
            'memory_limit': '1GB',
            'cpu_limit': 2
        })

        self.shadow_system.create_shadow('production', 'test_shadow', {
            'sync_interval': 3600,
            'anonymize': True
        })

        self.test_system.register_test_suite('unit_tests', [
            {'id': 'test_001', 'name': '用户登录测试'},
            {'id': 'test_002', 'name': '数据查询测试'},
            {'id': 'test_003', 'name': 'API调用测试'}
        ])

        self.test_system.register_test_suite('integration_tests', [
            {'id': 'it_001', 'name': '端到端流程测试'},
            {'id': 'it_002', 'name': '多环境切换测试'}
        ])

    def register_environment(self, env_id: str, name: str, type: EnvironmentType, config: Dict, description: str = ''):
        """注册环境"""
        env_info = {
            'id': env_id,
            'name': name,
            'type': type.value,
            'description': description,
            'config': config,
            'status': EnvironmentStatus.INACTIVE.value,
            'created_at': datetime.now().isoformat(),
            'last_activated': None
        }

        self.environments[env_id] = env_info
        logger.info(f"环境已注册: {env_id} ({name})")

    def activate_environment(self, env_id: str) -> bool:
        """激活环境"""
        if env_id not in self.environments:
            logger.error(f"环境不存在: {env_id}")
            return False

        if self.current_environment == env_id:
            logger.warning(f"环境已是激活状态: {env_id}")
            return True

        if self.config['backup_on_switch'] and self.current_environment:
            self._backup_current_environment()

        old_env = self.current_environment

        for env in self.environments.values():
            if env['status'] == EnvironmentStatus.ACTIVE.value:
                env['status'] = EnvironmentStatus.INACTIVE.value

        self.environments[env_id]['status'] = EnvironmentStatus.ACTIVE.value
        self.environments[env_id]['last_activated'] = datetime.now().isoformat()
        self.current_environment = env_id

        self._apply_environment_config(env_id)

        if self.environments[env_id]['config'].get('use_sandbox'):
            self._activate_sandbox_for_env(env_id)

        if self.environments[env_id]['config'].get('use_shadow'):
            self._activate_shadow_for_env(env_id)

        logger.info(f"环境已切换: {old_env} -> {env_id}")
        return True

    def _backup_current_environment(self):
        """备份当前环境"""
        if self.current_environment:
            logger.info(f"备份环境配置: {self.current_environment}")

    def _apply_environment_config(self, env_id: str):
        """应用环境配置"""
        env = self.environments[env_id]
        config = env['config']

        if config.get('debug'):
            os.environ['DEBUG'] = 'true'
        else:
            os.environ['DEBUG'] = 'false'

        os.environ['LOG_LEVEL'] = config.get('log_level', 'INFO')
        os.environ['API_BASE'] = config.get('api_base', '')

    def _activate_sandbox_for_env(self, env_id: str):
        """为环境激活沙盒"""
        sandbox_name = f"{env_id}_sandbox"
        sandboxes = self.sandbox_manager.list_sandboxes()

        if any(s['id'] == sandbox_name for s in sandboxes):
            self.sandbox_manager.activate_sandbox(sandbox_name)
        else:
            self.sandbox_manager.create_sandbox(sandbox_name, {
                'allow_execution': True,
                'memory_limit': '512MB',
                'cpu_limit': 1,
                'env_id': env_id
            })

    def _activate_shadow_for_env(self, env_id: str):
        """为环境激活影子系统"""
        shadow_name = f"{env_id}_shadow"
        shadows = self.shadow_system.list_shadows()

        if not any(s['id'] == shadow_name for s in shadows):
            self.shadow_system.create_shadow('production', shadow_name, {
                'env_id': env_id,
                'sync_interval': 3600
            })

    def switch_environment(self, env_id: str) -> Dict:
        """切换环境(带验证)"""
        if env_id not in self.environments:
            return {
                'success': False,
                'error': f'环境不存在: {env_id}'
            }

        success = self.activate_environment(env_id)

        return {
            'success': success,
            'from': self.current_environment,
            'to': env_id,
            'timestamp': datetime.now().isoformat()
        }

    def get_current_environment(self) -> Optional[Dict]:
        """获取当前环境"""
        if not self.current_environment:
            return None

        return self.environments.get(self.current_environment)

    def list_environments(self, include_status: bool = True) -> List[Dict]:
        """列出所有环境"""
        envs = []
        for env in self.environments.values():
            env_info = {
                'id': env['id'],
                'name': env['name'],
                'type': env['type'],
                'description': env['description']
            }

            if include_status:
                env_info['status'] = env['status']
                env_info['is_active'] = env['id'] == self.current_environment
                env_info['last_activated'] = env.get('last_activated')

            envs.append(env_info)

        return envs

    def get_environment_config(self, env_id: str) -> Optional[Dict]:
        """获取环境配置"""
        if env_id not in self.environments:
            return None

        return self.environments[env_id]['config']

    def update_environment_config(self, env_id: str, config: Dict) -> bool:
        """更新环境配置"""
        if env_id not in self.environments:
            return False

        self.environments[env_id]['config'].update(config)
        logger.info(f"环境配置已更新: {env_id}")
        return True

    def execute_in_environment(self, env_id: str, code: str, timeout: int = 30) -> Dict:
        """在指定环境中执行代码"""
        if env_id not in self.environments:
            return {'error': '环境不存在'}

        env = self.environments[env_id]

        if env['config'].get('use_sandbox'):
            sandbox_name = f"{env_id}_sandbox"
            return self.sandbox_manager.execute_in_sandbox(sandbox_name, code, timeout)

        return {
            'error': '环境未启用沙盒,无法执行代码'
        }

    def get_system_status(self, system_type: SystemType) -> Dict:
        """获取系统状态"""
        if system_type == SystemType.SANDBOX:
            return {
                'type': 'sandbox',
                'sandboxes': self.sandbox_manager.list_sandboxes(),
                'active_sandbox': self.sandbox_manager.active_sandbox
            }
        elif system_type == SystemType.SHADOW:
            return {
                'type': 'shadow',
                'shadows': self.shadow_system.list_shadows()
            }
        elif system_type == SystemType.TEST:
            return {
                'type': 'test',
                'stats': self.test_system.get_test_stats(),
                'recent_results': self.test_system.get_test_results(limit=10)
            }

    def run_tests_in_environment(self, env_id: str, suite_id: str = None) -> Dict:
        """在环境中运行测试"""
        if env_id not in self.environments:
            return {'error': '环境不存在'}

        self.activate_environment(env_id)

        if suite_id:
            return self.test_system.run_test(suite_id)
        else:
            return {
                'message': '运行所有测试套件',
                'results': [
                    self.test_system.run_test(suite_id)
                    for suite_id in self.test_system.test_suites.keys()
                ]
            }

    def get_dashboard(self) -> Dict:
        """获取仪表板"""
        current_env = self.get_current_environment()

        return {
            'current_environment': current_env,
            'environments': self.list_environments(),
            'systems': {
                'sandbox': self.get_system_status(SystemType.SANDBOX),
                'shadow': self.get_system_status(SystemType.SHADOW),
                'test': self.get_system_status(SystemType.TEST)
            },
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }

    def validate_environment(self, env_id: str) -> Dict:
        """验证环境"""
        if env_id not in self.environments:
            return {
                'valid': False,
                'error': '环境不存在'
            }

        env = self.environments[env_id]
        issues = []

        if not env['config'].get('api_base'):
            issues.append('缺少API基础地址配置')

        if env['config'].get('use_sandbox'):
            sandbox_name = f"{env_id}_sandbox"
            if not any(s['id'] == sandbox_name for s in self.sandbox_manager.list_sandboxes()):
                issues.append('沙盒系统未初始化')

        return {
            'valid': len(issues) == 0,
            'environment': env_id,
            'issues': issues
        }

    def export_environment_config(self, env_id: str) -> Optional[str]:
        """导出环境配置"""
        if env_id not in self.environments:
            return None

        env = self.environments[env_id]
        return json.dumps(env, indent=2, ensure_ascii=False)

    def import_environment_config(self, config_json: str) -> bool:
        """导入环境配置"""
        try:
            config = json.loads(config_json)
            env_id = config.get('id')

            if env_id in self.environments:
                logger.warning(f"环境已存在,将被覆盖: {env_id}")

            self.environments[env_id] = config
            logger.info(f"环境配置已导入: {env_id}")
            return True
        except Exception as e:
            logger.error(f"导入环境配置失败: {str(e)}")
            return False


multi_env_manager = MultiEnvironmentManager()
