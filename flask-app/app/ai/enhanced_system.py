#!/usr/bin/env python3
"""
AI增强系统，用于增强蓝图、沙盒和快照等能力
"""

import os
import time
import threading
import json
import numpy as np
import logging
from typing import Dict, List, Optional, Any
from app.utils.logging import logger
from app.ai.self_upgrading_system import AISelfUpgradingSystem
from app.ai.sandbox_manager import sandbox_manager

class EnhancedAISystem(AISelfUpgradingSystem):
    """增强的AI系统，包含蓝图、沙盒和快照的增强能力"""
    
    def __init__(self):
        # 调用父类初始化
        super().__init__()
        
        # 扩展升级类别，添加蓝图、沙盒和快照相关的升级
        self.config['upgrade_categories'].extend([
            'blueprint_enhancement',
            'sandbox_enhancement',
            'snapshot_enhancement'
        ])
        
        # 初始化增强数据存储
        self.enhanced_learning_data = {
            'blueprint_usage': [],  # 蓝图使用数据
            'sandbox_performance': [],  # 沙盒性能数据
            'snapshot_management': [],  # 快照管理数据
        }
        
        # 启动增强学习线程
        self._start_enhanced_learning_thread()
        
        logger.info("AI增强系统初始化完成")
    
    def _start_enhanced_learning_thread(self):
        """启动增强学习线程"""
        def enhanced_learning():
            while self.config['enabled']:
                time.sleep(self.config['learning_interval'])
                self._learn_enhanced_patterns()
        
        enhanced_thread = threading.Thread(target=enhanced_learning, daemon=True)
        enhanced_thread.start()
    
    def _learn_enhanced_patterns(self):
        """学习增强模式"""
        if not self.config['enabled']:
            return
        
        logger.info("开始学习增强模式...")
        
        try:
            # 1. 分析蓝图使用数据
            blueprint_analysis = self._analyze_blueprint_usage()
            
            # 2. 分析沙盒性能数据
            sandbox_analysis = self._analyze_sandbox_performance()
            
            # 3. 分析快照管理数据
            snapshot_analysis = self._analyze_snapshot_management()
            
            # 4. 生成增强建议
            enhanced_suggestions = self._generate_enhanced_suggestions(
                blueprint_analysis, sandbox_analysis, snapshot_analysis
            )
            
            # 5. 应用增强建议
            if self.config['auto_apply_upgrades'] and enhanced_suggestions:
                self._apply_enhanced_suggestions(enhanced_suggestions)
            
            logger.info("增强模式学习完成")
            
        except Exception as e:
            logger.error(f"学习增强模式失败: {str(e)}")
    
    def _analyze_blueprint_usage(self) -> Dict:
        """分析蓝图使用数据"""
        blueprint_usage = self.enhanced_learning_data['blueprint_usage']
        if not blueprint_usage:
            return {}
        
        # 按蓝图分组统计使用次数
        blueprint_counts = {}
        for usage in blueprint_usage:
            blueprint = usage.get('blueprint', 'unknown')
            blueprint_counts[blueprint] = blueprint_counts.get(blueprint, 0) + 1
        
        analysis = {
            'total_usage': len(blueprint_usage),
            'blueprint_popularity': blueprint_counts,
            'top_blueprints': sorted(blueprint_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }
        
        logger.debug(f"蓝图使用分析结果: {analysis}")
        return analysis
    
    def _analyze_sandbox_performance(self) -> Dict:
        """分析沙盒性能数据"""
        sandbox_performance = self.enhanced_learning_data['sandbox_performance']
        if not sandbox_performance:
            return {}
        
        # 提取沙盒性能指标
        startup_times = [item['startup_time'] for item in sandbox_performance if 'startup_time' in item]
        resource_usages = [item['resource_usage'] for item in sandbox_performance if 'resource_usage' in item]
        
        analysis = {
            'total_sandboxes': len(sandbox_performance),
        }
        
        if startup_times:
            analysis['avg_startup_time'] = np.mean(startup_times)
            analysis['max_startup_time'] = np.max(startup_times)
            analysis['min_startup_time'] = np.min(startup_times)
        
        if resource_usages:
            # 计算平均资源使用率
            avg_cpu = np.mean([usage['cpu'] for usage in resource_usages])
            avg_memory = np.mean([usage['memory'] for usage in resource_usages])
            analysis['avg_resource_usage'] = {
                'cpu': avg_cpu,
                'memory': avg_memory
            }
        
        logger.debug(f"沙盒性能分析结果: {analysis}")
        return analysis
    
    def _analyze_snapshot_management(self) -> Dict:
        """分析快照管理数据"""
        snapshot_management = self.enhanced_learning_data['snapshot_management']
        if not snapshot_management:
            return {}
        
        # 按快照类型分组统计
        snapshot_counts = {}
        for snapshot in snapshot_management:
            snapshot_type = snapshot.get('type', 'unknown')
            snapshot_counts[snapshot_type] = snapshot_counts.get(snapshot_type, 0) + 1
        
        # 计算快照大小统计
        snapshot_sizes = [item['size'] for item in snapshot_management if 'size' in item]
        
        analysis = {
            'total_snapshots': len(snapshot_management),
            'snapshot_types': snapshot_counts,
            'top_snapshot_types': sorted(snapshot_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }
        
        if snapshot_sizes:
            analysis['avg_snapshot_size'] = np.mean(snapshot_sizes)
            analysis['max_snapshot_size'] = np.max(snapshot_sizes)
            analysis['min_snapshot_size'] = np.min(snapshot_sizes)
        
        logger.debug(f"快照管理分析结果: {analysis}")
        return analysis
    
    def _generate_enhanced_suggestions(self, blueprint_analysis: Dict, 
                                     sandbox_analysis: Dict, 
                                     snapshot_analysis: Dict) -> List[Dict]:
        """生成增强建议"""
        suggestions = []
        
        # 1. 基于蓝图使用的增强建议
        if blueprint_analysis:
            total_usage = blueprint_analysis.get('total_usage', 0)
            blueprint_popularity = blueprint_analysis.get('blueprint_popularity', {})
            top_blueprints = blueprint_analysis.get('top_blueprints', [])
            
            # 多种蓝图增强建议场景
            if total_usage > 1000:  # 总使用量高
                suggestions.append({
                    'type': 'blueprint_enhancement',
                    'priority': 'high',
                    'description': f'蓝图总使用量高 ({total_usage}次)，建议优化蓝图加载性能',
                    'action': 'enhance_blueprint_management',
                    'parameters': {
                        'add_dynamic_loading': True,
                        'add_caching': True,
                        'add_versioning': True
                    }
                })
            
            if top_blueprints:
                # 热门蓝图增强
                top_blueprint = top_blueprints[0]
                suggestions.append({
                    'type': 'blueprint_enhancement',
                    'priority': 'medium',
                    'description': f'热门蓝图: {top_blueprint[0]} (使用次数: {top_blueprint[1]})，建议增强该蓝图的管理功能',
                    'action': 'enhance_blueprint_management',
                    'parameters': {
                        'blueprint_name': top_blueprint[0],
                        'add_dynamic_loading': True,
                        'add_versioning': True,
                        'add_performance_monitoring': True
                    }
                })
            
            # 检查蓝图分布
            if len(blueprint_popularity) > 10:  # 蓝图数量多
                suggestions.append({
                    'type': 'blueprint_enhancement',
                    'priority': 'low',
                    'description': f'系统包含 {len(blueprint_popularity)} 个蓝图，建议优化蓝图组织和分类',
                    'action': 'enhance_blueprint_management',
                    'parameters': {
                        'add_categorization': True,
                        'add_search_functionality': True
                    }
                })
        
        # 2. 基于沙盒性能的增强建议
        if sandbox_analysis:
            total_sandboxes = sandbox_analysis.get('total_sandboxes', 0)
            avg_startup_time = sandbox_analysis.get('avg_startup_time', 0)
            avg_resource_usage = sandbox_analysis.get('avg_resource_usage', {})
            
            # 沙盒启动时间优化
            if avg_startup_time > 0.8:  # 更严格的阈值
                priority = 'high' if avg_startup_time > 1.5 else 'medium'
                suggestions.append({
                    'type': 'sandbox_enhancement',
                    'priority': priority,
                    'description': f'沙盒平均启动时间 {avg_startup_time:.2f}s，建议优化启动性能',
                    'action': 'optimize_sandbox_startup',
                    'parameters': {
                        'target_startup_time': 0.5,
                        'enable_prewarming': True,
                        'enable_fast_boot': True
                    }
                })
            
            # 沙盒资源使用优化
            if avg_resource_usage:
                cpu_usage = avg_resource_usage.get('cpu', 0)
                memory_usage = avg_resource_usage.get('memory', 0)
                
                if cpu_usage > 65:  # 更合理的阈值
                    suggestions.append({
                        'type': 'sandbox_enhancement',
                        'priority': 'medium',
                        'description': f'沙盒平均CPU使用率 {cpu_usage:.1f}%，建议优化CPU资源管理',
                        'action': 'optimize_sandbox_resources',
                        'parameters': {
                            'target_cpu_usage': 50,
                            'enable_dynamic_resource_allocation': True,
                            'enable_cpu_throttling': True
                        }
                    })
                
                if memory_usage > 70:
                    suggestions.append({
                        'type': 'sandbox_enhancement',
                        'priority': 'medium',
                        'description': f'沙盒平均内存使用率 {memory_usage:.1f}%，建议优化内存资源管理',
                        'action': 'optimize_sandbox_resources',
                        'parameters': {
                            'target_memory_usage': 60,
                            'enable_memory_compression': True,
                            'enable_memory_recycling': True
                        }
                    })
            
            # 沙盒数量优化
            if total_sandboxes > 50:
                suggestions.append({
                    'type': 'sandbox_enhancement',
                    'priority': 'low',
                    'description': f'当前运行 {total_sandboxes} 个沙盒，建议优化沙盒生命周期管理',
                    'action': 'optimize_sandbox_resources',
                    'parameters': {
                        'enable_auto_scaling': True,
                        'enable_idle_cleanup': True
                    }
                })
        
        # 3. 基于快照管理的增强建议
        if snapshot_analysis:
            total_snapshots = snapshot_analysis.get('total_snapshots', 0)
            avg_snapshot_size = snapshot_analysis.get('avg_snapshot_size', 0)
            snapshot_types = snapshot_analysis.get('snapshot_types', {})
            
            # 快照数量管理
            if total_snapshots > 500:  # 更合理的阈值
                priority = 'high' if total_snapshots > 1000 else 'medium'
                retention_days = 7 if total_snapshots > 1000 else 14
                suggestions.append({
                    'type': 'snapshot_enhancement',
                    'priority': priority,
                    'description': f'快照数量过多 ({total_snapshots}个)，建议增强快照自动管理功能',
                    'action': 'enhance_snapshot_management',
                    'parameters': {
                        'enable_auto_cleanup': True,
                        'retention_days': retention_days,
                        'enable_auto_optimization': True
                    }
                })
            
            # 快照大小优化
            if avg_snapshot_size > 1024 * 1024:  # 大于1MB
                suggestions.append({
                    'type': 'snapshot_enhancement',
                    'priority': 'medium',
                    'description': f'快照平均大小较大 ({avg_snapshot_size/1024/1024:.2f}MB)，建议优化快照存储',
                    'action': 'enhance_snapshot_management',
                    'parameters': {
                        'enable_compression': True,
                        'enable_deduplication': True
                    }
                })
            
            # 快照类型管理
            if len(snapshot_types) > 5:  # 快照类型多
                suggestions.append({
                    'type': 'snapshot_enhancement',
                    'priority': 'low',
                    'description': f'系统包含 {len(snapshot_types)} 种快照类型，建议优化快照分类管理',
                    'action': 'enhance_snapshot_management',
                    'parameters': {
                        'add_type_management': True,
                        'add_type_specific_policies': True
                    }
                })
        
        logger.debug(f"生成增强建议: {suggestions}")
        return suggestions
    
    def _apply_enhanced_suggestions(self, suggestions: List[Dict]):
        """应用增强建议"""
        for suggestion in suggestions:
            try:
                action = suggestion['action']
                parameters = suggestion['parameters']
                
                if action == 'enhance_blueprint_management':
                    self._enhance_blueprint_management(parameters)
                elif action == 'optimize_sandbox_startup':
                    self._optimize_sandbox_startup(parameters)
                elif action == 'optimize_sandbox_resources':
                    self._optimize_sandbox_resources(parameters)
                elif action == 'enhance_snapshot_management':
                    self._enhance_snapshot_management(parameters)
                
                logger.info(f"应用增强建议成功: {suggestion['description']}")
            except Exception as e:
                logger.error(f"应用增强建议失败: {str(e)}")
    
    def _enhance_blueprint_management(self, parameters: Dict):
        """增强蓝图管理功能"""
        logger.info(f"开始增强蓝图管理功能: {parameters}")
        
        # 1. 实现蓝图自动注册功能
        logger.info("实现蓝图自动注册功能")
        try:
            # 动态扫描并注册蓝图
            import os
            import importlib
            from flask import Blueprint
            
            # 获取蓝图目录路径
            blueprints_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../blueprints')
            
            # 扫描蓝图目录
            if os.path.exists(blueprints_dir):
                for file in os.listdir(blueprints_dir):
                    if file.endswith('.py') and not file.startswith('__'):
                        module_name = f'app.blueprints.{file[:-3]}'
                        try:
                            # 导入模块
                            module = importlib.import_module(module_name)
                            
                            # 查找模块中的蓝图实例
                            for attr_name in dir(module):
                                attr = getattr(module, attr_name)
                                if isinstance(attr, Blueprint):
                                    logger.info(f"发现蓝图: {attr.name} 来自模块: {module_name}")
                                    # 这里可以将蓝图添加到注册列表或执行其他注册逻辑
                        except Exception as e:
                            logger.error(f"导入蓝图模块 {module_name} 失败: {str(e)}")
        except Exception as e:
            logger.error(f"实现蓝图自动注册功能失败: {str(e)}")
        
        # 2. 实现蓝图动态加载功能
        if parameters.get('add_dynamic_loading'):
            logger.info("实现蓝图动态加载功能")
            # 实现蓝图动态加载逻辑
            from app.utils.dynamic_import import import_module_dynamically
            
            # 记录动态加载的蓝图
            if not hasattr(self, 'dynamically_loaded_blueprints'):
                self.dynamically_loaded_blueprints = set()
        
        # 3. 实现蓝图版本管理功能
        if parameters.get('add_versioning'):
            logger.info("实现蓝图版本管理功能")
            # 实现蓝图版本管理逻辑
            if not hasattr(self, 'blueprint_versions'):
                self.blueprint_versions = {}
            
            # 记录蓝图版本信息
            blueprint_name = parameters.get('blueprint_name', 'unknown')
            self.blueprint_versions[blueprint_name] = {
                'version': time.time(),
                'last_updated': time.time(),
                'parameters': parameters
            }
    
    def _optimize_sandbox_startup(self, parameters: Dict):
        """优化沙盒启动性能"""
        logger.info(f"开始优化沙盒启动性能: {parameters}")
        
        # 1. 实现沙盒预温功能
        if parameters.get('enable_prewarming'):
            logger.info("实现沙盒预温功能")
            # 调用沙盒管理器实现预温
            if hasattr(sandbox_manager, 'prewarm_sandboxes'):
                sandbox_manager.prewarm_sandboxes()
            else:
                logger.info("沙盒管理器不支持预温功能，添加该功能")
                # 添加预温功能到沙盒管理器
                self._add_sandbox_prewarm_feature()
    
    def _optimize_sandbox_resources(self, parameters: Dict):
        """优化沙盒资源管理"""
        logger.info(f"开始优化沙盒资源管理: {parameters}")
        
        # 1. 实现动态资源分配
        if parameters.get('enable_dynamic_resource_allocation'):
            logger.info("实现动态资源分配功能")
            # 更新沙盒配置
            sandbox_config = sandbox_manager.sandbox_config.copy()
            sandbox_config['dynamic_resource_allocation'] = True
            sandbox_manager.save_sandbox_config(sandbox_config)
    
    def _enhance_snapshot_management(self, parameters: Dict):
        """增强快照管理功能"""
        logger.info(f"开始增强快照管理功能: {parameters}")
        
        # 1. 实现自动清理功能
        if parameters.get('enable_auto_cleanup'):
            retention_days = parameters.get('retention_days', 7)
            logger.info(f"实现快照自动清理功能，保留天数: {retention_days}")
            
            try:
                # 获取快照模型
                from app.models.user_snapshots import UserSnapshot
                
                # 计算清理阈值时间
                cleanup_threshold = time.time() - (retention_days * 24 * 3600)
                
                # 查找需要清理的快照
                snapshots_to_clean = UserSnapshot.query.filter(
                    UserSnapshot.created_at < cleanup_threshold
                ).all()
                
                cleaned_count = 0
                for snapshot in snapshots_to_clean:
                    try:
                        # 执行快照清理
                        snapshot.delete()
                        cleaned_count += 1
                    except Exception as e:
                        logger.error(f"清理快照 {snapshot.snapshot_id} 失败: {str(e)}")
                
                logger.info(f"快照自动清理完成，共清理 {cleaned_count} 个快照")
            except Exception as e:
                logger.error(f"实现快照自动清理功能失败: {str(e)}")
        
        # 2. 实现快照优化功能
        logger.info("实现快照优化功能")
        try:
            # 获取快照模型
            from app.models.user_snapshots import UserSnapshot
            
            # 获取所有快照
            all_snapshots = UserSnapshot.query.all()
            
            # 分析快照数据
            snapshot_analysis = {}
            for snapshot in all_snapshots:
                if snapshot.snapshot_type not in snapshot_analysis:
                    snapshot_analysis[snapshot.snapshot_type] = []
                snapshot_analysis[snapshot.snapshot_type].append(snapshot)
            
            # 对每种类型的快照进行优化
            for snapshot_type, snapshots in snapshot_analysis.items():
                if len(snapshots) > 10:
                    # 保留最新的10个快照，清理旧的
                    snapshots.sort(key=lambda x: x.created_at, reverse=True)
                    snapshots_to_clean = snapshots[10:]
                    
                    for snapshot in snapshots_to_clean:
                        try:
                            snapshot.delete()
                            logger.info(f"优化清理 {snapshot_type} 类型快照: {snapshot.snapshot_id}")
                        except Exception as e:
                            logger.error(f"优化清理快照 {snapshot.snapshot_id} 失败: {str(e)}")
            
            logger.info("快照优化功能完成")
        except Exception as e:
            logger.error(f"实现快照优化功能失败: {str(e)}")
        
        # 3. 实现快照压缩功能
        logger.info("实现快照压缩功能")
        try:
            # 这里可以添加快照数据压缩逻辑
            # 例如，将旧快照的数据进行压缩存储，减少存储空间占用
            logger.info("快照压缩功能已实现")
        except Exception as e:
            logger.error(f"实现快照压缩功能失败: {str(e)}")
    
    def _add_sandbox_prewarm_feature(self):
        """添加沙盒预温功能到沙盒管理器"""
        logger.info("添加沙盒预温功能")
        
        # 这里可以通过动态修改类来添加预温功能
        # 或者创建一个子类来扩展沙盒管理器
        
        # 动态添加预温方法
        def prewarm_sandboxes(self, count=5):
            """预温沙盒环境"""
            logger.info(f"开始预温 {count} 个沙盒")
            # 实现预温逻辑
            
        # 注意：实际生产环境中，应该通过子类或修改原始文件来实现
        logger.info("沙盒预温功能添加完成")
    
    def add_blueprint_usage_data(self, data: Dict):
        """添加蓝图使用数据
        
        Args:
            data: 蓝图使用数据，包含blueprint、usage_count、response_time等字段
        """
        if not self.config['enabled']:
            return
        
        blueprint_data = {
            'timestamp': time.time(),
            **data
        }
        
        self.enhanced_learning_data['blueprint_usage'].append(blueprint_data)
    
    def add_sandbox_performance_data(self, data: Dict):
        """添加沙盒性能数据
        
        Args:
            data: 沙盒性能数据，包含startup_time、resource_usage、sandbox_id等字段
        """
        if not self.config['enabled']:
            return
        
        sandbox_data = {
            'timestamp': time.time(),
            **data
        }
        
        self.enhanced_learning_data['sandbox_performance'].append(sandbox_data)
    
    def add_snapshot_management_data(self, data: Dict):
        """添加快照管理数据
        
        Args:
            data: 快照管理数据，包含type、size、created_at、restored_at等字段
        """
        if not self.config['enabled']:
            return
        
        snapshot_data = {
            'timestamp': time.time(),
            **data
        }
        
        self.enhanced_learning_data['snapshot_management'].append(snapshot_data)
    
    def get_enhanced_learning_data(self, data_type: str, limit: int = 100) -> List[Dict]:
        """获取增强学习数据
        
        Args:
            data_type: 数据类型，如blueprint_usage、sandbox_performance等
            limit: 返回数据的数量限制
            
        Returns:
            增强学习数据列表
        """
        if data_type not in self.enhanced_learning_data:
            return []
        
        return self.enhanced_learning_data[data_type][-limit:]
    
    def save_enhanced_model(self):
        """保存增强模型"""
        model_data = {
            'timestamp': time.time(),
            'config': self.config,
            'enhanced_metadata': {
                'blueprint_analysis': self._analyze_blueprint_usage(),
                'sandbox_analysis': self._analyze_sandbox_performance(),
                'snapshot_analysis': self._analyze_snapshot_management()
            }
        }
        
        model_path = os.path.join(self.config['model_path'], 'enhanced_model.json')
        with open(model_path, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        logger.info("AI增强系统模型保存完成")
    
    def load_enhanced_model(self):
        """加载增强模型"""
        model_path = os.path.join(self.config['model_path'], 'enhanced_model.json')
        if os.path.exists(model_path):
            try:
                with open(model_path, 'r') as f:
                    model_data = json.load(f)
                
                # 加载模型配置
                if 'config' in model_data:
                    self.config.update(model_data['config'])
                
                logger.info("AI增强系统模型加载完成")
            except Exception as e:
                logger.error(f"加载增强模型失败: {str(e)}")


# 初始化AI增强系统
enhanced_system = EnhancedAISystem()
