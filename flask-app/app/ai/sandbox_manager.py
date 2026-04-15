import os
import sys
import json
import time
import logging
import threading
import subprocess
import random
from typing import Dict, List, Optional
from app.config import Config
from app.utils.logging import logger


class SandboxManager:
    """沙盒管理器，用于管理AI实例的沙盒环境"""
    
    def __init__(self):
        self.sandboxes = {}
        self.sandbox_lock = threading.RLock()  # 使用可重入锁解决锁重入问题
        self.sandbox_config = self._load_sandbox_config()
        self.running_sandboxes = 0
        # 初始化动态沙盒配置
        self._init_dynamic_config()
        # 初始沙盒上限
        self.max_sandboxes = self.sandbox_config.get('initial_max_sandboxes', 10)
        
    def _init_dynamic_config(self):
        """初始化动态沙盒配置"""
        self.dynamic_config = {
            'enabled': True,
            'min_sandboxes': 5,      # 最小沙盒数量
            'max_sandboxes': 50,      # 绝对最大沙盒数量
            'resource_threshold': {
                'cpu': 80.0,           # CPU使用率阈值（%）
                'memory': 80.0,         # 内存使用率阈值（%）
                'disk': 80.0            # 磁盘使用率阈值（%）
            },
            'adjustment_step': 5,     # 每次调整的沙盒数量
            'check_interval': 60,      # 检查和调整的时间间隔（秒）
            'last_adjustment': time.time()
        }
        
        # 从配置文件加载动态配置
        if 'dynamic_sandbox' in self.sandbox_config:
            self.dynamic_config.update(self.sandbox_config['dynamic_sandbox'])
    
    def _load_sandbox_config(self):
        """加载沙盒配置"""
        default_config = {
            'enabled': True,
            'isolation_level': 'medium',
            'initial_max_sandboxes': 50,  # 初始沙盒上限
            'resource_limits': {
                'cpu': 50,          # CPU使用率限制（%）
                'memory': 1024,     # 内存限制（MB）
                'disk': 10240,      # 磁盘空间限制（MB）
                'processes': 10     # 进程数限制
            },
            'network_access': True,
            'file_system_access': True,
            'clipboard_access': False,
            'gpu_access': False,
            'dynamic_sandbox': {
                'enabled': True,
                'min_sandboxes': 5,
                'max_sandboxes': 50,
                'adjustment_step': 5
            }
        }
        
        try:
            # 尝试从配置文件加载沙盒配置
            config_path = os.path.join('config', 'sandbox.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            return default_config
        except Exception as e:
            logger.error(f"加载沙盒配置失败: {str(e)}")
            return default_config
    
    def save_sandbox_config(self, config):
        """保存沙盒配置"""
        try:
            config_path = os.path.join('config', 'sandbox.json')
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.sandbox_config = config
            logger.info("沙盒配置已保存")
            return True
        except Exception as e:
            logger.error(f"保存沙盒配置失败: {str(e)}")
            return False
    
    def _adjust_sandbox_limit(self):
        """根据资源使用情况动态调整沙盒上限"""
        if not self.dynamic_config['enabled']:
            return
        
        current_time = time.time()
        # 检查是否需要调整
        if current_time - self.dynamic_config['last_adjustment'] < self.dynamic_config['check_interval']:
            return
        
        # 获取系统资源使用情况（模拟）
        system_resources = self._get_system_resource_usage()
        
        # 计算新的沙盒上限
        new_max = self.max_sandboxes
        
        # 如果系统资源使用率低于阈值，可以增加沙盒上限
        if all(usage < threshold for usage, threshold in zip(
                system_resources.values(), 
                self.dynamic_config['resource_threshold'].values())):
            new_max = min(
                self.max_sandboxes + self.dynamic_config['adjustment_step'],
                self.dynamic_config['max_sandboxes']
            )
        # 如果系统资源使用率高于阈值，需要减少沙盒上限
        elif any(usage > threshold for usage, threshold in zip(
                system_resources.values(), 
                self.dynamic_config['resource_threshold'].values())):
            new_max = max(
                self.max_sandboxes - self.dynamic_config['adjustment_step'],
                self.dynamic_config['min_sandboxes']
            )
        
        # 更新沙盒上限
        if new_max != self.max_sandboxes:
            old_max = self.max_sandboxes
            self.max_sandboxes = new_max
            self.dynamic_config['last_adjustment'] = current_time
            logger.info(f"动态调整沙盒上限: {old_max} -> {new_max}，系统资源使用: {system_resources}")
    
    def _get_system_resource_usage(self):
        """获取系统资源使用情况"""
        try:
            # 尝试使用psutil获取真实系统资源使用情况
            import psutil
            
            return {
                'cpu': psutil.cpu_percent(),
                'memory': psutil.virtual_memory().percent,
                'disk': psutil.disk_usage('/').percent
            }
        except ImportError:
            # 如果psutil不可用，返回模拟数据
            logger.warning("psutil库未安装，使用模拟系统资源数据")
            return {
                'cpu': random.uniform(20.0, 90.0),
                'memory': random.uniform(30.0, 85.0),
                'disk': random.uniform(10.0, 75.0)
            }
    
    def create_sandbox(self, instance_id: str, ai_type: str = "general") -> Dict:
        """为AI实例创建沙盒环境"""
        with self.sandbox_lock:
            if instance_id in self.sandboxes:
                logger.warning(f"AI实例 {instance_id} 的沙盒环境已存在")
                return self.sandboxes[instance_id]
            
            # 动态调整沙盒上限
            self._adjust_sandbox_limit()
            
            if self.running_sandboxes >= self.max_sandboxes:
                logger.warning(f"沙盒数量已达当前上限: {self.max_sandboxes}，正在尝试清理不活跃沙盒")
                # 清理不活跃沙盒
                self.cleanup_inactive_sandboxes(inactive_time=1800)  # 清理30分钟未使用的沙盒
                
                # 再次检查
                if self.running_sandboxes >= self.max_sandboxes:
                    logger.warning(f"清理后沙盒数量仍达上限: {self.max_sandboxes}")
                    return None
            
            # 创建沙盒环境配置
            sandbox = {
                'sandbox_id': f"sandbox_{instance_id}_{int(time.time())}",
                'instance_id': instance_id,
                'ai_type': ai_type,
                'status': 'created',
                'created_at': time.time(),
                'last_used': time.time(),
                'config': {
                    'isolation_level': self.sandbox_config.get('isolation_level'),
                    'resource_limits': self.sandbox_config.get('resource_limits'),
                    'network_access': self.sandbox_config.get('network_access'),
                    'file_system_access': self.sandbox_config.get('file_system_access'),
                    'clipboard_access': self.sandbox_config.get('clipboard_access'),
                    'gpu_access': self.sandbox_config.get('gpu_access')
                },
                'resources_used': {
                    'cpu': 0.0,
                    'memory': 0.0,
                    'disk': 0.0,
                    'processes': 0
                },
                'activity_log': []
            }
            
            try:
                # 这里可以添加实际的沙盒创建逻辑
                # 例如，使用Docker、LXC或其他沙盒技术创建隔离环境
                
                # 模拟沙盒创建成功
                sandbox['status'] = 'running'
                self.sandboxes[instance_id] = sandbox
                self.running_sandboxes += 1
                
                logger.info(f"成功为AI实例 {instance_id} 创建沙盒环境: {sandbox['sandbox_id']}")
                return sandbox
            except Exception as e:
                logger.error(f"为AI实例 {instance_id} 创建沙盒环境失败: {str(e)}")
                sandbox['status'] = 'failed'
                sandbox['error'] = str(e)
                self.sandboxes[instance_id] = sandbox
                return sandbox
    
    def get_sandbox(self, instance_id: str) -> Optional[Dict]:
        """获取AI实例的沙盒环境"""
        with self.sandbox_lock:
            sandbox = self.sandboxes.get(instance_id)
            if sandbox:
                sandbox['last_used'] = time.time()
            return sandbox
    
    def update_sandbox(self, instance_id: str, updates: Dict) -> bool:
        """更新沙盒配置"""
        with self.sandbox_lock:
            if instance_id not in self.sandboxes:
                logger.error(f"AI实例 {instance_id} 的沙盒环境不存在")
                return False
            
            try:
                sandbox = self.sandboxes[instance_id]
                sandbox.update(updates)
                sandbox['last_used'] = time.time()
                logger.info(f"已更新AI实例 {instance_id} 的沙盒环境配置")
                return True
            except Exception as e:
                logger.error(f"更新AI实例 {instance_id} 的沙盒环境配置失败: {str(e)}")
                return False
    
    def destroy_sandbox(self, instance_id: str) -> bool:
        """销毁AI实例的沙盒环境"""
        with self.sandbox_lock:
            if instance_id not in self.sandboxes:
                logger.warning(f"AI实例 {instance_id} 的沙盒环境不存在")
                return True
            
            try:
                sandbox = self.sandboxes[instance_id]
                # 这里可以添加实际的沙盒销毁逻辑
                # 例如，停止并删除Docker容器或LXC实例
                
                # 模拟沙盒销毁成功
                sandbox['status'] = 'destroyed'
                sandbox['destroyed_at'] = time.time()
                del self.sandboxes[instance_id]
                self.running_sandboxes -= 1
                
                logger.info(f"成功销毁AI实例 {instance_id} 的沙盒环境: {sandbox['sandbox_id']}")
                return True
            except Exception as e:
                logger.error(f"销毁AI实例 {instance_id} 的沙盒环境失败: {str(e)}")
                return False
    
    def monitor_sandbox(self, instance_id: str) -> Optional[Dict]:
        """监控沙盒资源使用情况"""
        with self.sandbox_lock:
            sandbox = self.sandboxes.get(instance_id)
            if not sandbox or sandbox['status'] != 'running':
                return None
            
            try:
                # 这里可以添加实际的沙盒监控逻辑
                # 例如，获取Docker容器的资源使用情况
                
                # 模拟资源使用监控数据
                sandbox['resources_used'] = {
                    'cpu': round(random.uniform(0.0, sandbox['config']['resource_limits']['cpu']), 2),
                    'memory': round(random.uniform(0.0, sandbox['config']['resource_limits']['memory']), 2),
                    'disk': round(random.uniform(0.0, sandbox['config']['resource_limits']['disk']), 2),
                    'processes': random.randint(1, sandbox['config']['resource_limits']['processes'])
                }
                
                sandbox['last_used'] = time.time()
                return sandbox
            except Exception as e:
                logger.error(f"监控AI实例 {instance_id} 的沙盒环境失败: {str(e)}")
                return None
    
    def get_all_sandboxes(self) -> List[Dict]:
        """获取所有沙盒环境"""
        with self.sandbox_lock:
            return list(self.sandboxes.values())
    
    def get_sandbox_stats(self) -> Dict:
        """获取沙盒统计信息"""
        with self.sandbox_lock:
            stats = {
                'total_sandboxes': len(self.sandboxes),
                'running_sandboxes': self.running_sandboxes,
                'max_sandboxes': self.max_sandboxes,
                'sandbox_types': {},
                'resource_usage': {
                    'cpu': 0.0,
                    'memory': 0.0,
                    'disk': 0.0,
                    'processes': 0
                }
            }
            
            # 统计沙盒类型
            for sandbox in self.sandboxes.values():
                ai_type = sandbox['ai_type']
                stats['sandbox_types'][ai_type] = stats['sandbox_types'].get(ai_type, 0) + 1
                
                # 累加资源使用
                stats['resource_usage']['cpu'] += sandbox['resources_used']['cpu']
                stats['resource_usage']['memory'] += sandbox['resources_used']['memory']
                stats['resource_usage']['disk'] += sandbox['resources_used']['disk']
                stats['resource_usage']['processes'] += sandbox['resources_used']['processes']
            
            return stats
    
    def cleanup_inactive_sandboxes(self, inactive_time: int = 3600) -> List[str]:
        """清理长时间未使用的沙盒环境"""
        with self.sandbox_lock:
            current_time = time.time()
            inactive_sandboxes = []
            
            for instance_id, sandbox in list(self.sandboxes.items()):
                if current_time - sandbox['last_used'] > inactive_time:
                    inactive_sandboxes.append(instance_id)
                    self.destroy_sandbox(instance_id)
            
            if inactive_sandboxes:
                logger.info(f"已清理 {len(inactive_sandboxes)} 个长时间未使用的沙盒环境")
            
            return inactive_sandboxes
    
    def is_sandbox_enabled(self) -> bool:
        """检查沙盒功能是否启用"""
        return self.sandbox_config.get('enabled', False)
    
    def set_sandbox_enabled(self, enabled: bool) -> bool:
        """设置沙盒功能是否启用"""
        try:
            self.sandbox_config['enabled'] = enabled
            self.save_sandbox_config(self.sandbox_config)
            
            if not enabled:
                # 如果禁用沙盒，销毁所有运行中的沙盒
                for instance_id in list(self.sandboxes.keys()):
                    self.destroy_sandbox(instance_id)
            
            logger.info(f"沙盒功能已{'启用' if enabled else '禁用'}")
            return True
        except Exception as e:
            logger.error(f"设置沙盒功能状态失败: {str(e)}")
            return False
    
    def prewarm_sandboxes(self, count: int = 5):
        """预温沙盒环境，提前创建指定数量的沙盒以提高后续使用性能
        
        Args:
            count: 要预温的沙盒数量
        """
        if not self.is_sandbox_enabled():
            logger.info("沙盒功能未启用，跳过预温")
            return
        
        # 智能计算需要预温的沙盒数量
        smart_count = self._calculate_optimal_prewarm_count(count)
        logger.info(f"开始智能预温 {smart_count} 个沙盒环境...")
        
        # 检查当前运行的沙盒数量
        current_sandboxes = len(self.sandboxes)
        
        # 计算需要预温的沙盒数量
        need_prewarm = max(0, smart_count - current_sandboxes)
        if need_prewarm <= 0:
            logger.info(f"当前已有 {current_sandboxes} 个沙盒在运行，无需预温")
            return
        
        # 预温沙盒
        prewarmed_count = 0
        for i in range(need_prewarm):
            # 生成临时实例ID
            temp_instance_id = f"prewarm_{i}_{int(time.time())}"
            try:
                sandbox = self.create_sandbox(temp_instance_id, ai_type="prewarm")
                if sandbox and sandbox['status'] == 'running':
                    prewarmed_count += 1
                    # 标记为预温沙盒，便于后续管理
                    sandbox['prewarmed'] = True
                    sandbox['prewarm_time'] = time.time()
                    # 根据历史使用模式设置预温沙盒的资源配置
                    sandbox['config'] = self._get_optimal_sandbox_config()
                    logger.info(f"已预温沙盒: {sandbox['sandbox_id']}，配置: {sandbox['config']['resource_limits']}")
            except Exception as e:
                logger.error(f"预温沙盒失败: {str(e)}")
                continue
        
        logger.info(f"沙盒预温完成，共预温 {prewarmed_count} 个沙盒")
    
    def _calculate_optimal_prewarm_count(self, base_count: int = 5) -> int:
        """智能计算最佳预温沙盒数量
        
        Args:
            base_count: 基础预温数量
            
        Returns:
            最佳预温沙盒数量
        """
        # 获取系统资源使用情况
        system_resources = self._get_system_resource_usage()
        
        # 基于资源使用率调整预温数量
        resource_factor = 1.0
        
        # 如果系统资源使用率低，可以增加预温数量
        if all(usage < 40 for usage in system_resources.values()):
            resource_factor = 1.5
        # 如果系统资源使用率高，减少预温数量
        elif any(usage > 70 for usage in system_resources.values()):
            resource_factor = 0.5
        
        # 获取历史使用模式（模拟）
        historical_pattern = self._get_historical_usage_pattern()
        
        # 结合历史使用模式调整预温数量
        pattern_factor = historical_pattern.get('peak_factor', 1.0)
        
        # 计算最终预温数量
        optimal_count = int(base_count * resource_factor * pattern_factor)
        
        # 确保预温数量在合理范围内
        optimal_count = max(1, min(optimal_count, self.dynamic_config['max_sandboxes'] // 2))
        
        logger.info(f"智能计算预温数量: 基础={base_count}, 资源因子={resource_factor}, 模式因子={pattern_factor}, 最终={optimal_count}")
        
        return optimal_count
    
    def _get_historical_usage_pattern(self) -> dict:
        """获取历史使用模式
        
        Returns:
            历史使用模式字典
        """
        # 这里可以实现真实的历史使用模式分析
        # 目前返回模拟数据
        current_hour = time.localtime().tm_hour
        
        # 模拟不同时间段的使用模式
        if 9 <= current_hour < 18:  # 工作时间
            return {
                'peak_factor': 1.5,
                'usage_type': 'high',
                'expected_increase': True
            }
        else:  # 非工作时间
            return {
                'peak_factor': 0.5,
                'usage_type': 'low',
                'expected_increase': False
            }
    
    def _get_optimal_sandbox_config(self) -> dict:
        """获取最佳沙盒配置
        
        Returns:
            最佳沙盒配置
        """
        # 获取当前系统资源使用情况
        system_resources = self._get_system_resource_usage()
        
        # 基于系统资源情况调整沙盒配置
        base_config = self.sandbox_config.copy()
        
        # 如果系统CPU使用率高，降低沙盒CPU限制
        if system_resources['cpu'] > 70:
            base_config['resource_limits']['cpu'] = max(25, base_config['resource_limits']['cpu'] - 10)
        # 如果系统内存使用率高，降低沙盒内存限制
        if system_resources['memory'] > 70:
            base_config['resource_limits']['memory'] = max(512, base_config['resource_limits']['memory'] - 256)
        
        return base_config
    
    def get_prewarmed_sandbox(self):
        """获取一个预温的沙盒
        
        Returns:
            Optional[Dict]: 预温的沙盒配置，或None如果没有可用的预温沙盒
        """
        with self.sandbox_lock:
            # 查找预温沙盒
            for instance_id, sandbox in self.sandboxes.items():
                if sandbox.get('prewarmed') and sandbox['status'] == 'running':
                    # 标记为已使用，移除预温标记
                    sandbox['prewarmed'] = False
                    logger.info(f"使用预温沙盒: {sandbox['sandbox_id']}")
                    return sandbox
        
        # 没有可用的预温沙盒
        logger.info("没有可用的预温沙盒")
        return None


# 创建全局沙盒管理器实例
sandbox_manager = SandboxManager()
