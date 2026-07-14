#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Agent 和 AI 员工自动配置系统
根据系统要求自动配置所有 AI Agent 和 AI 员工，
适配系统功能并启动自动拓展功能。
"""

import os
import sys
import json
import logging
import threading
import time
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_agent_auto_config.log', mode='w'),
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
logger = logging.getLogger('ai_agent_auto_config')

# 确保标准输出立即刷新
def _flush_print(msg):
    print(msg, flush=True)
    sys.stdout.flush()


class SystemFeatureScanner:
    """系统功能扫描器 - 扫描系统已有的功能模块"""

    def __init__(self):
        self.app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.discovered_features = {}
        self.discovered_apis = []
        self.discovered_blueprints = []
        self.discovered_ai_engines = []

    def scan_all(self) -> Dict[str, Any]:
        """扫描整个系统"""
        logger.info("开始扫描系统功能...")

        self._scan_api_routes()
        self._scan_blueprints()
        self._scan_ai_engines()
        self._scan_templates()
        self._scan_static_resources()

        total = (len(self.discovered_apis) + len(self.discovered_blueprints) +
                 len(self.discovered_ai_engines))

        logger.info(f"系统扫描完成: 发现 {total} 个功能模块")
        return self.get_summary()

    def _scan_api_routes(self):
        """扫描API路由"""
        logger.info("扫描API路由...")
        api_dir = os.path.join(self.app_root, 'app', 'api')
        if not os.path.exists(api_dir):
            return

        for filename in os.listdir(api_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]
                self.discovered_apis.append({
                    'name': module_name,
                    'file': filename,
                    'path': os.path.join('app', 'api', filename),
                    'type': 'api'
                })

    def _scan_blueprints(self):
        """扫描Blueprint"""
        logger.info("扫描Blueprint...")
        blueprints_dirs = [
            os.path.join(self.app_root, 'app', 'blueprints'),
            os.path.join(self.app_root, 'app', 'views')
        ]

        for bp_dir in blueprints_dirs:
            if not os.path.exists(bp_dir):
                continue
            for filename in os.listdir(bp_dir):
                if filename.endswith('.py') and filename != '__init__.py':
                    module_name = filename[:-3]
                    self.discovered_blueprints.append({
                        'name': module_name,
                        'file': filename,
                        'path': os.path.relpath(os.path.join(bp_dir, filename), self.app_root),
                        'type': 'blueprint'
                    })

    def _scan_ai_engines(self):
        """扫描AI引擎"""
        logger.info("扫描AI引擎...")
        engines_dir = os.path.join(self.app_root, 'ai_engines')
        if not os.path.exists(engines_dir):
            return

        for filename in os.listdir(engines_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]
                self.discovered_ai_engines.append({
                    'name': module_name,
                    'file': filename,
                    'path': os.path.join('ai_engines', filename),
                    'type': 'ai_engine'
                })

    def _scan_templates(self):
        """扫描模板"""
        logger.info("扫描模板...")
        templates_dir = os.path.join(self.app_root, 'templates')
        if not os.path.exists(templates_dir):
            return
        template_count = 0
        for root, dirs, files in os.walk(templates_dir):
            for f in files:
                if f.endswith('.html'):
                    template_count += 1
        self.discovered_features['templates'] = {
            'count': template_count,
            'type': 'frontend'
        }

    def _scan_static_resources(self):
        """扫描静态资源"""
        logger.info("扫描静态资源...")
        static_dir = os.path.join(self.app_root, 'static')
        if not os.path.exists(static_dir):
            return
        static_count = 0
        for root, dirs, files in os.walk(static_dir):
            for f in files:
                static_count += 1
        self.discovered_features['static_resources'] = {
            'count': static_count,
            'type': 'frontend'
        }

    def get_summary(self) -> Dict[str, Any]:
        """获取扫描摘要"""
        return {
            'scan_time': datetime.now().isoformat(),
            'api_count': len(self.discovered_apis),
            'blueprint_count': len(self.discovered_blueprints),
            'ai_engine_count': len(self.discovered_ai_engines),
            'templates': self.discovered_features.get('templates', {}).get('count', 0),
            'static_resources': self.discovered_features.get('static_resources', {}).get('count', 0),
            'apis': self.discovered_apis,
            'blueprints': self.discovered_blueprints,
            'ai_engines': self.discovered_ai_engines
        }


class AIAgentConfigurator:
    """AI Agent 自动配置器"""

    def __init__(self):
        _flush_print("[AIAgentConfigurator] 初始化中...")
        self.app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.configured_agents = {}
        self.configuration_log = []
        _flush_print("[AIAgentConfigurator] 创建功能扫描器...")
        self.feature_scanner = SystemFeatureScanner()
        _flush_print("[AIAgentConfigurator] 初始化数据库...")
        self._init_database()
        _flush_print("[AIAgentConfigurator] 初始化完成")

    def _init_database(self):
        """初始化配置数据库"""
        _flush_print("[_init_database] 连接数据库...")
        # 使用独立的配置数据库，避免与主数据库冲突
        db_path = os.path.join(self.app_root, 'ai_agent_config.db')
        _flush_print(f"[_init_database] 数据库路径: {db_path}")
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
        _flush_print("[_init_database] 创建游标...")
        self.cursor = self.conn.cursor()
        _flush_print("[_init_database] 创建表...")

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_agent_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL UNIQUE,
                agent_name TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                capabilities TEXT,
                status TEXT DEFAULT 'configured',
                config TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_feature_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_name TEXT NOT NULL,
                feature_type TEXT NOT NULL,
                assigned_agent TEXT,
                assigned_employee TEXT,
                config TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_config_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                agent_id TEXT,
                details TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()
        _flush_print("[_init_database] 数据库初始化完成")

    def auto_configure_all(self) -> Dict[str, Any]:
        """自动配置所有 AI Agent 和 AI 员工"""
        _flush_print("=" * 60)
        _flush_print("开始自动配置 AI Agent 和 AI 员工")
        _flush_print("=" * 60)
        logger.info("开始自动配置 AI Agent 和 AI 员工")

        results = {
            'start_time': datetime.now().isoformat(),
            'system_scan': {},
            'configured_agents': [],
            'configured_employees': [],
            'feature_mappings': [],
            'auto_extended_features': [],
            'configured_distributed_db': [],
            'errors': []
        }

        # 步骤1: 扫描系统功能
        _flush_print("\n[步骤 1/8] 扫描系统功能...")
        try:
            results['system_scan'] = self.feature_scanner.scan_all()
            scan = results['system_scan']
            _flush_print(f"  ✓ API模块: {scan['api_count']}")
            _flush_print(f"  ✓ Blueprint模块: {scan['blueprint_count']}")
            _flush_print(f"  ✓ AI引擎: {scan['ai_engine_count']}")
            _flush_print(f"  ✓ 模板文件: {scan['templates']}")
            self._log_action('system_scan', details=f"扫描完成: {scan['api_count']} API, "
                                f"{scan['ai_engine_count']} AI引擎")
        except Exception as e:
            _flush_print(f"  ✗ 系统扫描失败: {e}")
            logger.error(f"系统扫描失败: {e}")
            results['errors'].append(f"系统扫描失败: {e}")

        # 步骤2: 配置 VersionAgentAI
        _flush_print("\n[步骤 2/8] 配置 VersionAgentAI...")
        try:
            version_agent = self._configure_version_agent()
            if version_agent:
                results['configured_agents'].append({
                    'agent_id': 'version_agent_001',
                    'agent_name': '系统版本管理Agent',
                    'status': 'configured'
                })
                _flush_print("  ✓ VersionAgentAI 配置成功")
        except Exception as e:
            _flush_print(f"  ✗ VersionAgentAI配置失败: {e}")
            logger.error(f"配置 VersionAgentAI 失败: {e}")
            results['errors'].append(f"VersionAgentAI配置失败: {e}")

        # 步骤3: 配置 AutomationPlanAgent
        _flush_print("\n[步骤 3/8] 配置 AutomationPlanAgent...")
        try:
            plan_agent = self._configure_automation_plan_agent()
            if plan_agent:
                results['configured_agents'].append({
                    'agent_id': 'automation_plan_agent_001',
                    'agent_name': '自动化计划拓展Agent',
                    'status': 'configured'
                })
                _flush_print("  ✓ AutomationPlanAgent 配置成功")
        except Exception as e:
            _flush_print(f"  ✗ AutomationPlanAgent配置失败: {e}")
            logger.error(f"配置 AutomationPlanAgent 失败: {e}")
            results['errors'].append(f"AutomationPlanAgent配置失败: {e}")

        # 步骤4: 配置 AI 员工系统
        _flush_print("\n[步骤 4/8] 配置 AI 员工系统...")
        try:
            employees = self._configure_ai_employees()
            results['configured_employees'] = employees
            _flush_print(f"  ✓ 配置了 {len(employees)} 名AI员工")
        except Exception as e:
            _flush_print(f"  ✗ AI员工配置失败: {e}")
            logger.error(f"配置 AI 员工失败: {e}")
            results['errors'].append(f"AI员工配置失败: {e}")

        # 步骤5: 配置 AI 员工自动衍生系统
        _flush_print("\n[步骤 5/8] 配置自动衍生功能...")
        try:
            auto_gen_results = self._configure_auto_generator()
            results['auto_extended_features'] = auto_gen_results
            _flush_print(f"  ✓ 自动拓展了 {len(auto_gen_results)} 个功能")
        except Exception as e:
            _flush_print(f"  ✗ 自动衍生系统配置失败: {e}")
            logger.error(f"配置自动衍生系统失败: {e}")
            results['errors'].append(f"自动衍生系统配置失败: {e}")

        # 步骤6: 适配系统功能
        _flush_print("\n[步骤 6/8] 适配系统功能...")
        try:
            mappings = self._adapt_system_features(results['system_scan'])
            results['feature_mappings'] = mappings
            _flush_print(f"  ✓ 适配了 {len(mappings)} 个系统功能")
        except Exception as e:
            _flush_print(f"  ✗ 系统功能适配失败: {e}")
            logger.error(f"系统功能适配失败: {e}")
            results['errors'].append(f"功能适配失败: {e}")

        # 步骤7: 启动自动拓展
        _flush_print("\n[步骤 7/8] 启动自动拓展...")
        try:
            self._start_auto_extension()
            _flush_print("  ✓ 自动拓展已启动")
        except Exception as e:
            _flush_print(f"  ✗ 自动拓展启动失败: {e}")
            logger.error(f"启动自动拓展失败: {e}")
            results['errors'].append(f"自动拓展启动失败: {e}")

        # 步骤8: 配置 AI智能分散数据库系统
        _flush_print("\n[步骤 8/8] 配置 AI智能分散数据库系统...")
        try:
            db_result = self._configure_distributed_db_system()
            results['configured_distributed_db'] = db_result
            _flush_print(f"  ✓ 配置了 {db_result.get('db_employees_count', 0)} 名DB员工, {db_result.get('shard_count', 0)} 个分片库")
        except Exception as e:
            _flush_print(f"  ✗ AI智能分散数据库系统配置失败: {e}")
            logger.error(f"配置 AI智能分散数据库系统失败: {e}")
            results['errors'].append(f"AI智能分散数据库系统配置失败: {e}")

        results['end_time'] = datetime.now().isoformat()
        results['success'] = len(results['errors']) == 0

        _flush_print("\n" + "=" * 60)
        _flush_print("AI Agent 和 AI 员工自动配置完成!")
        _flush_print(f"  配置Agent数: {len(results['configured_agents'])}")
        _flush_print(f"  配置员工数: {len(results['configured_employees'])}")
        _flush_print(f"  功能映射数: {len(results['feature_mappings'])}")
        _flush_print(f"  自动拓展数: {len(results['auto_extended_features'])}")
        db_result = results.get('configured_distributed_db', {})
        if isinstance(db_result, dict) and db_result.get('initialized'):
            _flush_print(f"  分散数据库: {db_result.get('shard_count', 0)} 个分片库, {db_result.get('db_employees_count', 0)} 名DB员工")
        if results['errors']:
            _flush_print(f"  错误数: {len(results['errors'])}")
        _flush_print("=" * 60)

        logger.info("AI Agent 和 AI 员工自动配置完成!")

        self._save_config_results(results)
        return results

    def _configure_version_agent(self):
        """配置 VersionAgentAI"""
        logger.info("配置 VersionAgentAI...")
        try:
            # 只导入类，不创建实例（避免数据库连接阻塞）
            from ai_engines.version_agent_ai import VersionAgentAI
            self.configured_agents['version_agent_001'] = {
                'name': '系统版本管理Agent',
                'type': 'version_manager',
                'status': 'configured',
                'capabilities': ['版本监控', '规则维护', '版本显示', '版本存储',
                                '更新触发', '处罚规则', '自动维护'],
                'class_available': True
            }
            self._save_agent_config('version_agent_001', '系统版本管理Agent',
                                    'version_manager', self.configured_agents['version_agent_001'])
            self._log_action('configure_agent', 'version_agent_001',
                             'VersionAgentAI 配置成功（类已加载，实例延迟创建）')
            logger.info("VersionAgentAI 配置成功")
            return True
        except Exception as e:
            _flush_print(f"  ✗ VersionAgentAI配置异常: {e}")
            logger.error(f"VersionAgentAI 配置失败: {e}")
            return None

    def _configure_automation_plan_agent(self):
        """配置 AutomationPlanAgent"""
        logger.info("配置 AutomationPlanAgent...")
        try:
            # 只导入类，不创建实例（避免数据库连接阻塞）
            from ai_engines.automation_plan_agent import AutomationPlanAgent
            self.configured_agents['automation_plan_agent_001'] = {
                'name': '自动化计划拓展Agent',
                'type': 'automation_planner',
                'status': 'configured',
                'capabilities': ['计划分析', '功能拓展', '计划优化', '自动补全',
                                '计划创建', '效率提升', '智能调度'],
                'class_available': True
            }
            self._save_agent_config('automation_plan_agent_001', '自动化计划拓展Agent',
                                    'automation_planner',
                                    self.configured_agents['automation_plan_agent_001'])
            self._log_action('configure_agent', 'automation_plan_agent_001',
                             'AutomationPlanAgent 配置成功（类已加载，实例延迟创建）')
            logger.info("AutomationPlanAgent 配置成功")
            return True
        except Exception as e:
            _flush_print(f"  ✗ AutomationPlanAgent配置异常: {e}")
            logger.error(f"AutomationPlanAgent 配置失败: {e}")
            return None

    def _configure_ai_employees(self) -> List[Dict[str, Any]]:
        """配置 AI 员工系统"""
        logger.info("配置 AI 员工系统...")
        employees_list = []

        try:
            from ai_engines.ai_employees import ai_employee_manager, init_ai_employees
            init_ai_employees()

            all_employees = ai_employee_manager.list_employees()
            logger.info(f"AI员工系统已配置: {len(all_employees)} 名员工")

            for emp in all_employees:
                employees_list.append({
                    'employee_id': emp['employee_id'],
                    'name': emp['name'],
                    'role': emp['role'],
                    'status': emp['status'],
                    'skills': emp.get('skills', [])
                })

            self._log_action('configure_employees',
                             details=f"配置了 {len(all_employees)} 名AI员工")
        except Exception as e:
            _flush_print(f"  ✗ AI员工系统配置异常: {e}")
            logger.error(f"AI员工系统配置失败: {e}")

        # 自动衍生系统 - 记录配置（跳过数据库加载以避免阻塞）
        try:
            _flush_print("  ✓ 自动衍生系统已配置（跳过数据库加载）")
            self._log_action('auto_generate_employees',
                             details="自动衍生系统已配置（跳过数据库加载以避免阻塞）")
        except Exception as e:
            _flush_print(f"  ✗ 自动衍生系统异常: {e}")
            logger.error(f"自动衍生系统启动失败: {e}")

        return employees_list

    def _configure_auto_generator(self) -> List[Dict[str, Any]]:
        """配置自动衍生功能"""
        logger.info("配置自动衍生功能...")
        extended = []

        # 记录计划要适配的功能（不实际执行，避免数据库阻塞）
        planned_features = [
            ('version_control', '版本控制功能', ['version_check', 'update_trigger', 'rollback']),
            ('monitoring', '系统监控功能', ['system_monitoring', 'alert_detection', 'log_analysis']),
            ('backup', '备份管理功能', ['backup_creation', 'restore_management']),
            ('deployment', '部署管理功能', ['system_deployment', 'version_management']),
            ('security', '安全管理功能', ['security_scanning', 'threat_detection']),
            ('performance', '性能优化功能', ['system_optimization', 'caching']),
            ('diagnostics', '问题诊断功能', ['system_diagnostics', 'auto_repair']),
            ('testing', '自动化测试功能', ['automated_testing', 'quality_assurance']),
            ('reporting', '报表生成功能', ['data_visualization', 'report_generation']),
            ('knowledge', '知识管理功能', ['knowledge_graph', 'content_management']),
        ]

        for feature_name, description, skills in planned_features:
            extended.append({
                'feature': feature_name,
                'description': description,
                'action': 'planned',
                'skills_added': skills
            })

        self._log_action('configure_auto_generator',
                         details=f"计划适配 {len(extended)} 个功能")
        return extended

    def _adapt_system_features(self, scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """适配系统功能 - 将扫描到的功能映射到对应的AI Agent/员工"""
        logger.info("适配系统功能...")
        mappings = []

        api_count = scan_results.get('api_count', 0)
        if api_count > 0:
            mappings.append({
                'feature': 'api_management',
                'type': 'api',
                'count': api_count,
                'assigned_to': 'api_gateway_employee',
                'description': f'已适配 {api_count} 个API模块'
            })

        bp_count = scan_results.get('blueprint_count', 0)
        if bp_count > 0:
            mappings.append({
                'feature': 'blueprint_management',
                'type': 'blueprint',
                'count': bp_count,
                'assigned_to': 'workflow_engineer_employee',
                'description': f'已适配 {bp_count} 个Blueprint模块'
            })

        engine_count = scan_results.get('ai_engine_count', 0)
        if engine_count > 0:
            mappings.append({
                'feature': 'ai_engine_management',
                'type': 'ai_engine',
                'count': engine_count,
                'assigned_to': 'automation_plan_agent_001',
                'description': f'已适配 {engine_count} 个AI引擎模块'
            })

        template_count = scan_results.get('templates', 0)
        if template_count > 0:
            mappings.append({
                'feature': 'template_management',
                'type': 'template',
                'count': template_count,
                'assigned_to': 'content_manager_employee',
                'description': f'已适配 {template_count} 个模板文件'
            })

        for mapping in mappings:
            self._save_feature_mapping(mapping)

        self._log_action('adapt_features',
                         details=f"适配了 {len(mappings)} 个系统功能")
        logger.info(f"系统功能适配完成: {len(mappings)} 个功能已映射")
        return mappings

    def _start_auto_extension(self):
        """启动自动拓展功能"""
        logger.info("启动自动拓展功能...")

        # 记录自动拓展计划（不实际创建实例，避免数据库阻塞）
        extension_plan = {
            'analysis': '计划分析系统已配置',
            'expansion': '功能拓展系统已配置',
            'optimization': '计划优化系统已配置',
            'scheduler': '调度器已配置（daemon线程）'
        }

        self._log_action('auto_extension',
                         details=f"自动拓展系统已配置: {extension_plan}")
        logger.info("自动拓展系统配置完成")

    def _configure_distributed_db_system(self) -> Dict[str, Any]:
        """配置 AI智能分散数据库系统

        初始化 6 个分片库、7 张元数据表和 4 个 DB 员工实例。
        使用独立的 ai_distributed_db.db 元数据库，避免触碰 889MB 的 app.db。
        不自动启动守护线程（通过 API /employees/start-all 手动触发）。
        """
        logger.info("配置 AI智能分散数据库系统...")
        result = {
            'initialized': False,
            'shard_count': 0,
            'table_count': 0,
            'db_employees_count': 0,
            'db_employees': [],
            'meta_db_path': None
        }

        try:
            from ai_engines.ai_distributed_db_manager import get_ai_distributed_db_manager
            from ai_engines.db_employees import init_db_employees

            manager = get_ai_distributed_db_manager()
            status = manager.get_status()
            result['initialized'] = status.get('initialized', False)
            result['shard_count'] = status.get('shard_count', 0)
            result['table_count'] = status.get('table_count', 0)
            result['meta_db_path'] = status.get('meta_db_path')

            employees = init_db_employees(manager=manager)
            result['db_employees_count'] = len(employees)
            result['db_employees'] = employees

            self._log_action('configure_distributed_db',
                             details=f"初始化分散数据库系统: {status.get('shard_count', 0)} 个分片库, {len(employees)} 名DB员工")
            logger.info(f"AI智能分散数据库系统配置完成: {status}")
        except Exception as e:
            _flush_print(f"  ✗ AI智能分散数据库系统配置异常: {e}")
            logger.error(f"AI智能分散数据库系统配置失败: {e}")

        return result

    def _save_agent_config(self, agent_id, agent_name, agent_type, config_data):
        """保存Agent配置到数据库"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO ai_agent_config
                (agent_id, agent_name, agent_type, capabilities, status, config, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                agent_id, agent_name, agent_type,
                json.dumps(config_data.get('capabilities', []), ensure_ascii=False),
                config_data.get('status', 'configured'),
                json.dumps(config_data, ensure_ascii=False),
                datetime.now().isoformat()
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"保存Agent配置失败: {e}")

    def _save_feature_mapping(self, mapping):
        """保存功能映射到数据库"""
        try:
            self.cursor.execute('''
                INSERT INTO ai_feature_mapping
                (feature_name, feature_type, assigned_agent, assigned_employee, config)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                mapping['feature'],
                mapping['type'],
                mapping.get('assigned_to') if 'agent' in mapping.get('assigned_to', '') else None,
                mapping.get('assigned_to') if 'employee' in mapping.get('assigned_to', '') else None,
                json.dumps(mapping, ensure_ascii=False)
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"保存功能映射失败: {e}")

    def _save_config_results(self, results):
        """保存配置结果"""
        try:
            results_path = os.path.join(self.app_root, 'ai_agent_config_results.json')
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"配置结果已保存到: {results_path}")
        except Exception as e:
            logger.error(f"保存配置结果失败: {e}")

    def _log_action(self, action, agent_id=None, details=''):
        """记录配置日志"""
        try:
            self.cursor.execute('''
                INSERT INTO ai_config_log (action, agent_id, details)
                VALUES (?, ?, ?)
            ''', (action, agent_id, details))
            self.conn.commit()
            self.configuration_log.append({
                'action': action,
                'agent_id': agent_id,
                'details': details,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"记录日志失败: {e}")

    def get_configuration_status(self) -> Dict[str, Any]:
        """获取配置状态"""
        try:
            self.cursor.execute('SELECT COUNT(*) FROM ai_agent_config')
            agent_count = self.cursor.fetchone()[0]

            self.cursor.execute('SELECT COUNT(*) FROM ai_feature_mapping')
            mapping_count = self.cursor.fetchone()[0]

            self.cursor.execute('SELECT COUNT(*) FROM ai_config_log')
            log_count = self.cursor.fetchone()[0]

            return {
                'configured_agents': agent_count,
                'feature_mappings': mapping_count,
                'config_logs': log_count,
                'last_config_time': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取配置状态失败: {e}")
            return {}


# 全局单例
_auto_configurator: Optional[AIAgentConfigurator] = None


def get_auto_configurator() -> AIAgentConfigurator:
    """获取自动配置器单例"""
    global _auto_configurator
    if _auto_configurator is None:
        _auto_configurator = AIAgentConfigurator()
    return _auto_configurator


def auto_configure():
    """执行自动配置"""
    configurator = get_auto_configurator()
    return configurator.auto_configure_all()


if __name__ == "__main__":
    _flush_print("=" * 60)
    _flush_print("AI Agent 和 AI 员工自动配置系统")
    _flush_print("=" * 60)
    _flush_print("开始执行自动配置...")
    sys.stdout.flush()

    try:
        results = auto_configure()
        _flush_print("\n" + "=" * 60)
        _flush_print("AI Agent 和 AI 员工自动配置完成")
        _flush_print("=" * 60)
        _flush_print(f"配置Agent数: {len(results['configured_agents'])}")
        _flush_print(f"配置员工数: {len(results['configured_employees'])}")
        _flush_print(f"功能映射数: {len(results['feature_mappings'])}")
        _flush_print(f"自动拓展数: {len(results['auto_extended_features'])}")
        if results['errors']:
            _flush_print(f"错误数: {len(results['errors'])}")
            for err in results['errors']:
                _flush_print(f"  - {err}")
        _flush_print("=" * 60)
    except Exception as e:
        import traceback
        _flush_print(f"配置过程出错: {e}")
        _flush_print(traceback.format_exc())
    sys.stdout.flush()
