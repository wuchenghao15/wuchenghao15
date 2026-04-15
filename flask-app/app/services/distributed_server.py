#!/usr/bin/env python3
"""
分布式服务器管理模块，用于管理客户端的子服务器，减轻主服务器负载
"""

import time
import threading
import json
import socket
from app.utils.logging import logger
from app.config import Config
# 导入子服务器系统AI
from app.ai.server_ai import server_ai
# 导入子服务器规则管理器
from app.utils.server_rule_manager import server_rule_manager
# 导入子服务器权限管理器
from app.utils.server_permission_manager import server_permission_manager
# 导入子服务器路由管理器
from app.utils.server_route_manager import server_route_manager
# 导入 Git 管理器
from app.services.git_manager import git_manager

class DistributedServerManager:
    """分布式服务器管理器类"""
    
    def __init__(self):
        self.is_running = False
        self.thread = None
        self.child_servers = {}  # 子服务器字典
        self.child_servers_lock = threading.Lock()
        self.heartbeat_interval = 30  # 心跳检测间隔，单位：秒
        self.server_timeout = 60  # 服务器超时时间，单位：秒
        self.max_child_servers = 100  # 最大子服务器数量
    
    def start(self):
        """启动分布式服务器管理器"""
        if self.is_running:
            logger.info("分布式服务器管理器已在运行")
            return
        
        logger.info("启动分布式服务器管理器...")
        self.is_running = True
        
        # 启动心跳检测线程
        self.thread = threading.Thread(target=self._run_heartbeat_loop, daemon=True)
        self.thread.start()
        
        logger.info("分布式服务器管理器启动成功")
    
    def stop(self):
        """停止分布式服务器管理器"""
        if not self.is_running:
            logger.info("分布式服务器管理器未在运行")
            return
        
        logger.info("停止分布式服务器管理器...")
        self.is_running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("分布式服务器管理器已停止")
    
    def _run_heartbeat_loop(self):
        """心跳检测循环"""
        while self.is_running:
            try:
                self._check_heartbeats()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"心跳检测循环发生错误: {str(e)}")
                time.sleep(5)  # 发生错误时，等待5秒后重试
    
    def _check_heartbeats(self):
        """检查子服务器心跳"""
        logger.debug("开始检查子服务器心跳...")
        current_time = time.time()
        servers_to_remove = []
        
        with self.child_servers_lock:
            for server_id, server_info in self.child_servers.items():
                # 检查服务器是否超时
                if current_time - server_info['last_heartbeat'] > self.server_timeout:
                    servers_to_remove.append(server_id)
                    logger.warning(f"子服务器 {server_id} 心跳超时，将被移除")
        
        # 移除超时的子服务器
        for server_id in servers_to_remove:
            self.remove_child_server(server_id)
    
    def register_child_server(self, server_info):
        """注册子服务器"""
        server_id = server_info.get('server_id')
        if not server_id:
            logger.error("子服务器注册失败：缺少server_id")
            return False
        
        with self.child_servers_lock:
            # 检查子服务器数量是否已达上限
            if len(self.child_servers) >= self.max_child_servers:
                logger.error(f"子服务器注册失败：已达最大子服务器数量 {self.max_child_servers}")
                return False
            
            # 注册子服务器
            self.child_servers[server_id] = {
                'server_id': server_id,
                'ip': server_info.get('ip', 'unknown'),
                'port': server_info.get('port', 0),
                'status': 'online',
                'last_heartbeat': time.time(),
                'registered_at': time.time(),
                'client_info': server_info.get('client_info', {}),
                'load': server_info.get('load', 0),
                'resources': server_info.get('resources', {}),
                'tasks': []  # 分配给该服务器的任务
            }
        
        logger.info(f"子服务器 {server_id} 注册成功，IP: {server_info.get('ip')}, 端口: {server_info.get('port')}")
        return True
    
    def update_child_server_heartbeat(self, server_id):
        """更新子服务器心跳"""
        with self.child_servers_lock:
            if server_id in self.child_servers:
                self.child_servers[server_id]['last_heartbeat'] = time.time()
                self.child_servers[server_id]['status'] = 'online'
                logger.debug(f"更新子服务器 {server_id} 心跳")
                return True
            else:
                logger.warning(f"更新子服务器 {server_id} 心跳失败：服务器未注册")
                return False
    
    def remove_child_server(self, server_id):
        """移除子服务器"""
        with self.child_servers_lock:
            if server_id in self.child_servers:
                del self.child_servers[server_id]
                logger.info(f"子服务器 {server_id} 已移除")
                return True
            else:
                logger.warning(f"移除子服务器 {server_id} 失败：服务器未注册")
                return False
    
    def get_child_server_info(self, server_id):
        """获取子服务器信息"""
        with self.child_servers_lock:
            return self.child_servers.get(server_id, None)
    
    def get_all_child_servers(self):
        """获取所有子服务器信息"""
        with self.child_servers_lock:
            return list(self.child_servers.values())
    
    def get_online_child_servers(self):
        """获取在线子服务器信息"""
        with self.child_servers_lock:
            return [server for server in self.child_servers.values() if server['status'] == 'online']
    
    def assign_task(self, task_info):
        """分配任务给子服务器
        
        根据子服务器的负载情况，将任务分配给负载最低的子服务器
        """
        with self.child_servers_lock:
            online_servers = [server for server in self.child_servers.values() if server['status'] == 'online']
            if not online_servers:
                logger.error("分配任务失败：没有在线的子服务器")
                return None
            
            # 选择负载最低的子服务器
            selected_server = min(online_servers, key=lambda s: s['load'])
            
            # 创建任务ID
            import uuid
            task_id = f"task_{uuid.uuid4().hex[:8]}"
            
            # 分配任务
            task = {
                'task_id': task_id,
                'status': 'pending',
                'assigned_at': time.time(),
                'task_info': task_info
            }
            selected_server['tasks'].append(task)
            
            # 更新服务器负载
            selected_server['load'] += 1
            
            logger.info(f"任务 {task_id} 已分配给子服务器 {selected_server['server_id']}")
            return {
                'server_id': selected_server['server_id'],
                'task_id': task_id
            }
    
    def update_task_status(self, server_id, task_id, status, result=None):
        """更新任务状态"""
        with self.child_servers_lock:
            if server_id in self.child_servers:
                server = self.child_servers[server_id]
                for task in server['tasks']:
                    if task['task_id'] == task_id:
                        task['status'] = status
                        task['completed_at'] = time.time()
                        if result:
                            task['result'] = result
                        
                        # 任务完成，降低服务器负载
                        if status in ['completed', 'failed']:
                            server['load'] = max(0, server['load'] - 1)
                        
                        logger.info(f"子服务器 {server_id} 上的任务 {task_id} 状态已更新为 {status}")
                        return True
                logger.warning(f"更新任务状态失败：任务 {task_id} 未在子服务器 {server_id} 上找到")
                return False
            else:
                logger.warning(f"更新任务状态失败：子服务器 {server_id} 未注册")
                return False
    
    def balance_load(self):
        """负载均衡
        
        根据子服务器的负载情况，调整任务分配
        """
        logger.info("开始负载均衡...")
        
        with self.child_servers_lock:
            online_servers = [server for server in self.child_servers.values() if server['status'] == 'online']
            if len(online_servers) < 2:
                logger.info("负载均衡跳过：在线子服务器数量不足")
                return
            
            # 计算平均负载
            total_load = sum(server['load'] for server in online_servers)
            avg_load = total_load / len(online_servers)
            
            # 找出负载过高和过低的服务器
            overloaded_servers = [server for server in online_servers if server['load'] > avg_load + 2]
            underloaded_servers = [server for server in online_servers if server['load'] < avg_load - 2]
            
            if not overloaded_servers or not underloaded_servers:
                logger.info("负载均衡跳过：负载分布较为均衡")
                return
            
            # 调整任务分配
            for overloaded_server in overloaded_servers:
                # 计算需要转移的任务数量
                tasks_to_transfer = overloaded_server['load'] - int(avg_load)
                if tasks_to_transfer <= 0:
                    continue
                
                # 选择负载最低的服务器接收任务
                selected_server = min(underloaded_servers, key=lambda s: s['load'])
                
                # 转移任务
                tasks = overloaded_server['tasks'][:tasks_to_transfer]
                overloaded_server['tasks'] = overloaded_server['tasks'][tasks_to_transfer:]
                selected_server['tasks'].extend(tasks)
                
                # 更新服务器负载
                overloaded_server['load'] -= len(tasks)
                selected_server['load'] += len(tasks)
                
                logger.info(f"已从子服务器 {overloaded_server['server_id']} 向子服务器 {selected_server['server_id']} 转移 {len(tasks)} 个任务")
                
                # 更新underloaded_servers列表
                underloaded_servers = [server for server in online_servers if server['load'] < avg_load - 2]
                if not underloaded_servers:
                    break
    
    def get_distributed_stats(self):
        """获取分布式系统统计信息"""
        with self.child_servers_lock:
            total_servers = len(self.child_servers)
            online_servers = len([server for server in self.child_servers.values() if server['status'] == 'online'])
            total_load = sum(server['load'] for server in self.child_servers.values())
            avg_load = total_load / total_servers if total_servers > 0 else 0
            total_tasks = sum(len(server['tasks']) for server in self.child_servers.values())
            
            return {
                'total_servers': total_servers,
                'online_servers': online_servers,
                'total_load': total_load,
                'average_load': avg_load,
                'total_tasks': total_tasks,
                'max_servers': self.max_child_servers
            }
    
    def shutdown_all_child_servers(self):
        """关闭所有子服务器"""
        logger.info("开始关闭所有子服务器...")
        
        with self.child_servers_lock:
            for server_id in list(self.child_servers.keys()):
                self.remove_child_server(server_id)
        
        logger.info("所有子服务器已关闭")
    
    def analyze_server_performance(self, server_id):
        """分析服务器性能
        
        Args:
            server_id: 服务器ID
            
        Returns:
            分析结果
        """
        try:
            server_info = self.get_child_server_info(server_id)
            if not server_info:
                logger.error(f"分析服务器性能失败：服务器 {server_id} 不存在")
                return None
            
            # 构建性能数据
            performance_data = {
                "cpu_usage": server_info.get("resources", {}).get("cpu_usage", 0),
                "memory_usage": server_info.get("resources", {}).get("memory_usage", 0),
                "disk_usage": server_info.get("resources", {}).get("disk_usage", 0),
                "network_traffic": server_info.get("resources", {}).get("network_traffic", 0),
                "response_time": server_info.get("resources", {}).get("response_time", 0)
            }
            
            # 使用AI分析服务器性能
            analysis = server_ai.analyze_server_performance(server_id, performance_data)
            return analysis
        except Exception as e:
            logger.error(f"分析服务器性能失败: {str(e)}")
            return None
    
    def predict_server_load(self, server_id, time_window=30):
        """预测服务器负载
        
        Args:
            server_id: 服务器ID
            time_window: 预测时间窗口（分钟）
            
        Returns:
            预测结果
        """
        try:
            # 使用AI预测服务器负载
            prediction = server_ai.predict_server_load(server_id, time_window)
            return prediction
        except Exception as e:
            logger.error(f"预测服务器负载失败: {str(e)}")
            return None
    
    def detect_server_anomalies(self, server_id):
        """检测服务器异常
        
        Args:
            server_id: 服务器ID
            
        Returns:
            异常检测结果
        """
        try:
            server_info = self.get_child_server_info(server_id)
            if not server_info:
                logger.error(f"检测服务器异常失败：服务器 {server_id} 不存在")
                return None
            
            # 构建性能数据
            performance_data = {
                "cpu_usage": server_info.get("resources", {}).get("cpu_usage", 0),
                "memory_usage": server_info.get("resources", {}).get("memory_usage", 0),
                "disk_usage": server_info.get("resources", {}).get("disk_usage", 0),
                "network_traffic": server_info.get("resources", {}).get("network_traffic", 0),
                "response_time": server_info.get("resources", {}).get("response_time", 0)
            }
            
            # 使用AI检测服务器异常
            detection = server_ai.detect_server_anomalies(server_id, performance_data)
            return detection
        except Exception as e:
            logger.error(f"检测服务器异常失败: {str(e)}")
            return None
    
    def predict_server_failure(self, server_id, time_window=60):
        """预测服务器故障
        
        Args:
            server_id: 服务器ID
            time_window: 预测时间窗口（分钟）
            
        Returns:
            故障预测结果
        """
        try:
            # 使用AI预测服务器故障
            prediction = server_ai.predict_server_failure(server_id, time_window)
            return prediction
        except Exception as e:
            logger.error(f"预测服务器故障失败: {str(e)}")
            return None
    
    def optimize_resource_allocation(self):
        """优化资源分配
        
        Returns:
            资源分配优化结果
        """
        try:
            # 获取所有子服务器信息
            servers = self.get_all_child_servers()
            
            # 构建服务器列表
            server_list = []
            for server in servers:
                server_list.append({
                    "server_id": server["server_id"],
                    "performance": {
                        "cpu_usage": server.get("resources", {}).get("cpu_usage", 0),
                        "memory_usage": server.get("resources", {}).get("memory_usage", 0),
                        "disk_usage": server.get("resources", {}).get("disk_usage", 0),
                        "network_traffic": server.get("resources", {}).get("network_traffic", 0),
                        "response_time": server.get("resources", {}).get("response_time", 0)
                    }
                })
            
            # 使用AI优化资源分配
            allocation = server_ai.optimize_resource_allocation(server_list)
            return allocation
        except Exception as e:
            logger.error(f"优化资源分配失败: {str(e)}")
            return None
    
    def optimize_server_config(self, server_id, current_config):
        """优化服务器配置
        
        Args:
            server_id: 服务器ID
            current_config: 当前配置
            
        Returns:
            优化后的配置
        """
        try:
            # 使用AI优化服务器配置
            optimization = server_ai.optimize_server_config(server_id, current_config)
            return optimization
        except Exception as e:
            logger.error(f"优化服务器配置失败: {str(e)}")
            return current_config
    
    def check_server_registration_rules(self, server_info):
        """检查服务器注册规则
        
        Args:
            server_info: 服务器信息
            
        Returns:
            检查结果
        """
        try:
            # 使用规则管理器检查服务器注册规则
            result = server_rule_manager.check_server_registration(server_info)
            return result
        except Exception as e:
            logger.error(f"检查服务器注册规则失败: {str(e)}")
            return None
    
    def check_server_health_rules(self, server_info):
        """检查服务器健康规则
        
        Args:
            server_info: 服务器信息
            
        Returns:
            检查结果
        """
        try:
            # 使用规则管理器检查服务器健康规则
            result = server_rule_manager.check_server_health(server_info)
            return result
        except Exception as e:
            logger.error(f"检查服务器健康规则失败: {str(e)}")
            return None
    
    def check_resource_usage_rules(self, server_info):
        """检查资源使用规则
        
        Args:
            server_info: 服务器信息
            
        Returns:
            检查结果
        """
        try:
            # 使用规则管理器检查资源使用规则
            result = server_rule_manager.check_resource_usage(server_info)
            return result
        except Exception as e:
            logger.error(f"检查资源使用规则失败: {str(e)}")
            return None
    
    def check_security_rules(self, server_info):
        """检查安全规则
        
        Args:
            server_info: 服务器信息
            
        Returns:
            检查结果
        """
        try:
            # 使用规则管理器检查安全规则
            result = server_rule_manager.check_security(server_info)
            return result
        except Exception as e:
            logger.error(f"检查安全规则失败: {str(e)}")
            return None
    
    def check_performance_rules(self, server_info):
        """检查性能规则
        
        Args:
            server_info: 服务器信息
            
        Returns:
            检查结果
        """
        try:
            # 使用规则管理器检查性能规则
            result = server_rule_manager.check_performance(server_info)
            return result
        except Exception as e:
            logger.error(f"检查性能规则失败: {str(e)}")
            return None
    
    def get_server_rules(self, rule_type=None):
        """获取服务器规则
        
        Args:
            rule_type: 规则类型
            
        Returns:
            规则字典
        """
        try:
            if rule_type:
                return server_rule_manager.get_rules(rule_type)
            else:
                return server_rule_manager.get_all_rules()
        except Exception as e:
            logger.error(f"获取服务器规则失败: {str(e)}")
            return {}
    
    def update_server_rules(self, rule_type, rules):
        """更新服务器规则
        
        Args:
            rule_type: 规则类型
            rules: 规则字典
            
        Returns:
            是否成功
        """
        try:
            server_rule_manager.update_rules(rule_type, rules)
            return True
        except Exception as e:
            logger.error(f"更新服务器规则失败: {str(e)}")
            return False
    
    def check_server_access(self, role, server_id, action):
        """检查用户对服务器的访问权限
        
        Args:
            role: 角色名称
            server_id: 服务器ID
            action: 操作类型 (view, start, stop, restart, deploy, undeploy, config, resources)
            
        Returns:
            是否有权限
        """
        try:
            # 使用权限管理器检查服务器访问权限
            result = server_permission_manager.check_server_access(role, server_id, action)
            return result
        except Exception as e:
            logger.error(f"检查服务器访问权限失败: {str(e)}")
            return False
    
    def check_rule_access(self, role, action):
        """检查用户对规则的访问权限
        
        Args:
            role: 角色名称
            action: 操作类型 (view, manage)
            
        Returns:
            是否有权限
        """
        try:
            # 使用权限管理器检查规则访问权限
            result = server_permission_manager.check_rule_access(role, action)
            return result
        except Exception as e:
            logger.error(f"检查规则访问权限失败: {str(e)}")
            return False
    
    def check_permission_access(self, role, action):
        """检查用户对权限的访问权限
        
        Args:
            role: 角色名称
            action: 操作类型 (view, manage)
            
        Returns:
            是否有权限
        """
        try:
            # 使用权限管理器检查权限访问权限
            result = server_permission_manager.check_permission_access(role, action)
            return result
        except Exception as e:
            logger.error(f"检查权限访问权限失败: {str(e)}")
            return False
    
    def check_ai_access(self, role, action):
        """检查用户对AI功能的访问权限
        
        Args:
            role: 角色名称
            action: 操作类型 (view, manage)
            
        Returns:
            是否有权限
        """
        try:
            # 使用权限管理器检查AI访问权限
            result = server_permission_manager.check_ai_access(role, action)
            return result
        except Exception as e:
            logger.error(f"检查AI访问权限失败: {str(e)}")
            return False
    
    def get_user_permissions(self, role):
        """获取用户权限
        
        Args:
            role: 角色名称
            
        Returns:
            权限列表
        """
        try:
            permissions = server_permission_manager.get_permissions(role)
            return permissions
        except Exception as e:
            logger.error(f"获取用户权限失败: {str(e)}")
            return []
    
    def has_permission(self, role, permission):
        """检查角色是否有指定权限
        
        Args:
            role: 角色名称
            permission: 权限名称
            
        Returns:
            是否有权限
        """
        try:
            result = server_permission_manager.has_permission(role, permission)
            return result
        except Exception as e:
            logger.error(f"检查权限失败: {str(e)}")
            return False
    
    def update_user_permissions(self, role, permissions):
        """更新用户权限
        
        Args:
            role: 角色名称
            permissions: 权限列表
            
        Returns:
            是否成功
        """
        try:
            server_permission_manager.update_permissions(role, permissions)
            return True
        except Exception as e:
            logger.error(f"更新用户权限失败: {str(e)}")
            return False
    
    def get_all_roles(self):
        """获取所有角色
        
        Returns:
            角色列表
        """
        try:
            roles = server_permission_manager.get_roles()
            return roles
        except Exception as e:
            logger.error(f"获取角色列表失败: {str(e)}")
            return []
    
    def get_route(self, blueprint, route_name):
        """获取路由
        
        Args:
            blueprint: 蓝图名称
            route_name: 路由名称
            
        Returns:
            路由路径
        """
        try:
            route = server_route_manager.get_route(blueprint, route_name)
            return route
        except Exception as e:
            logger.error(f"获取路由失败: {str(e)}")
            return None
    
    def set_route(self, blueprint, route_name, path):
        """设置路由
        
        Args:
            blueprint: 蓝图名称
            route_name: 路由名称
            path: 路由路径
            
        Returns:
            是否成功
        """
        try:
            server_route_manager.set_route(blueprint, route_name, path)
            return True
        except Exception as e:
            logger.error(f"设置路由失败: {str(e)}")
            return False
    
    def get_route_permissions(self, route):
        """获取路由的权限要求
        
        Args:
            route: 路由名称，格式为 "blueprint.route"
            
        Returns:
            权限列表
        """
        try:
            permissions = server_route_manager.get_route_permissions(route)
            return permissions
        except Exception as e:
            logger.error(f"获取路由权限失败: {str(e)}")
            return []
    
    def set_route_permission(self, route, permissions):
        """设置路由的权限要求
        
        Args:
            route: 路由名称，格式为 "blueprint.route"
            permissions: 权限列表
            
        Returns:
            是否成功
        """
        try:
            server_route_manager.set_route_permission(route, permissions)
            return True
        except Exception as e:
            logger.error(f"设置路由权限失败: {str(e)}")
            return False
    
    def check_route_permission(self, route, user_role):
        """检查路由权限
        
        Args:
            route: 路由名称，格式为 "blueprint.route"
            user_role: 用户角色
            
        Returns:
            是否有权限
        """
        try:
            result = server_route_manager.check_route_permission(route, user_role)
            return result
        except Exception as e:
            logger.error(f"检查路由权限失败: {str(e)}")
            return False
    
    def get_all_routes(self):
        """获取所有路由
        
        Returns:
            路由字典
        """
        try:
            routes = server_route_manager.get_all_routes()
            return routes
        except Exception as e:
            logger.error(f"获取所有路由失败: {str(e)}")
            return {}
    
    def register_blueprint(self, blueprint):
        """注册蓝图
        
        Args:
            blueprint: 蓝图实例
            
        Returns:
            是否成功
        """
        try:
            server_route_manager.register_blueprint(blueprint)
            return True
        except Exception as e:
            logger.error(f"注册蓝图失败: {str(e)}")
            return False
    
    def register_all_routes(self, app):
        """注册所有路由
        
        Args:
            app: Flask应用实例
            
        Returns:
            是否成功
        """
        try:
            server_route_manager.register_all_routes(app)
            return True
        except Exception as e:
            logger.error(f"注册所有路由失败: {str(e)}")
            return False
    
    def git_init(self, repo_path=None):
        """初始化 Git 仓库
        
        Args:
            repo_path: 仓库路径
            
        Returns:
            命令执行结果
        """
        try:
            if repo_path:
                # 创建临时 Git 管理器实例
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.init_repo()
            else:
                result = git_manager.init_repo()
            return result
        except Exception as e:
            logger.error(f"初始化 Git 仓库失败: {str(e)}")
            return {"success": False, "stderr": str(e)}
    
    def git_status(self, repo_path=None):
        """查看 Git 仓库状态
        
        Args:
            repo_path: 仓库路径
            
        Returns:
            命令执行结果
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.status()
            else:
                result = git_manager.status()
            return result
        except Exception as e:
            logger.error(f"查看 Git 仓库状态失败: {str(e)}")
            return {"success": False, "stderr": str(e)}
    
    def git_add(self, paths=None, repo_path=None):
        """添加文件到 Git 暂存区
        
        Args:
            paths: 文件路径列表
            repo_path: 仓库路径
            
        Returns:
            命令执行结果
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.add(paths)
            else:
                result = git_manager.add(paths)
            return result
        except Exception as e:
            logger.error(f"添加文件到 Git 暂存区失败: {str(e)}")
            return {"success": False, "stderr": str(e)}
    
    def git_commit(self, message, repo_path=None):
        """提交 Git 更改
        
        Args:
            message: 提交消息
            repo_path: 仓库路径
            
        Returns:
            命令执行结果
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.commit(message)
            else:
                result = git_manager.commit(message)
            return result
        except Exception as e:
            logger.error(f"提交 Git 更改失败: {str(e)}")
            return {"success": False, "stderr": str(e)}
    
    def git_push(self, remote='origin', branch='master', repo_path=None):
        """推送 Git 更改
        
        Args:
            remote: 远程仓库
            branch: 分支名称
            repo_path: 仓库路径
            
        Returns:
            命令执行结果
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.push(remote, branch)
            else:
                result = git_manager.push(remote, branch)
            return result
        except Exception as e:
            logger.error(f"推送 Git 更改失败: {str(e)}")
            return {"success": False, "stderr": str(e)}
    
    def git_pull(self, remote='origin', branch='master', repo_path=None):
        """拉取 Git 更改
        
        Args:
            remote: 远程仓库
            branch: 分支名称
            repo_path: 仓库路径
            
        Returns:
            命令执行结果
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.pull(remote, branch)
            else:
                result = git_manager.pull(remote, branch)
            return result
        except Exception as e:
            logger.error(f"拉取 Git 更改失败: {str(e)}")
            return {"success": False, "stderr": str(e)}
    
    def git_log(self, limit=10, repo_path=None):
        """查看 Git 提交日志
        
        Args:
            limit: 日志条数限制
            repo_path: 仓库路径
            
        Returns:
            命令执行结果
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.log(limit)
            else:
                result = git_manager.log(limit)
            return result
        except Exception as e:
            logger.error(f"查看 Git 提交日志失败: {str(e)}")
            return {"success": False, "stderr": str(e)}
    
    def git_branch(self, repo_path=None):
        """查看 Git 分支
        
        Args:
            repo_path: 仓库路径
            
        Returns:
            命令执行结果
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.branch()
            else:
                result = git_manager.branch()
            return result
        except Exception as e:
            logger.error(f"查看 Git 分支失败: {str(e)}")
            return {"success": False, "stderr": str(e)}
    
    def git_checkout(self, branch, repo_path=None):
        """切换 Git 分支
        
        Args:
            branch: 分支名称
            repo_path: 仓库路径
            
        Returns:
            命令执行结果
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.checkout(branch)
            else:
                result = git_manager.checkout(branch)
            return result
        except Exception as e:
            logger.error(f"切换 Git 分支失败: {str(e)}")
            return {"success": False, "stderr": str(e)}
    
    def git_create_branch(self, branch, repo_path=None):
        """创建 Git 分支
        
        Args:
            branch: 分支名称
            repo_path: 仓库路径
            
        Returns:
            命令执行结果
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.create_branch(branch)
            else:
                result = git_manager.create_branch(branch)
            return result
        except Exception as e:
            logger.error(f"创建 Git 分支失败: {str(e)}")
            return {"success": False, "stderr": str(e)}
    
    def git_merge(self, branch, repo_path=None):
        """合并 Git 分支
        
        Args:
            branch: 要合并的分支名称
            repo_path: 仓库路径
            
        Returns:
            命令执行结果
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.merge(branch)
            else:
                result = git_manager.merge(branch)
            return result
        except Exception as e:
            logger.error(f"合并 Git 分支失败: {str(e)}")
            return {"success": False, "stderr": str(e)}
    
    def git_get_repo_info(self, repo_path=None):
        """获取 Git 仓库信息
        
        Args:
            repo_path: 仓库路径
            
        Returns:
            仓库信息
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.get_repo_info()
            else:
                result = git_manager.get_repo_info()
            return result
        except Exception as e:
            logger.error(f"获取 Git 仓库信息失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_system_version(self, repo_path=None):
        """获取系统版本信息
        
        Args:
            repo_path: 仓库路径
            
        Returns:
            系统版本信息
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.get_system_version()
            else:
                result = git_manager.get_system_version()
            return result
        except Exception as e:
            logger.error(f"获取系统版本信息失败: {str(e)}")
            return {"error": str(e)}
    
    def analyze_version_with_ai(self, version_info=None, repo_path=None):
        """使用 AI 分析版本信息
        
        Args:
            version_info: 版本信息，如果为 None 则自动获取
            repo_path: 仓库路径
            
        Returns:
            AI 分析结果
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.analyze_version_with_ai(version_info)
            else:
                result = git_manager.analyze_version_with_ai(version_info)
            return result
        except Exception as e:
            logger.error(f"使用 AI 分析版本信息失败: {str(e)}")
            return {"error": str(e)}
    
    def track_version_changes(self, repo_path=None):
        """跟踪版本变更
        
        Args:
            repo_path: 仓库路径
            
        Returns:
            版本变更信息
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.track_version_changes()
            else:
                result = git_manager.track_version_changes()
            return result
        except Exception as e:
            logger.error(f"跟踪版本变更失败: {str(e)}")
            return {"error": str(e)}
    
    def generate_version_report(self, repo_path=None):
        """生成版本报告
        
        Args:
            repo_path: 仓库路径
            
        Returns:
            版本报告
        """
        try:
            if repo_path:
                from app.services.git_manager import GitManager
                temp_git_manager = GitManager(repo_path)
                result = temp_git_manager.generate_version_report()
            else:
                result = git_manager.generate_version_report()
            return result
        except Exception as e:
            logger.error(f"生成版本报告失败: {str(e)}")
            return {"error": str(e)}

# 创建全局分布式服务器管理器实例
distributed_server_manager = DistributedServerManager()
