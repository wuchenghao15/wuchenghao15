import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServerRuleManager:
    """子服务器规则管理器，负责管理和应用子服务器系统的规则"""
    
    def __init__(self, config_file: str = None):
        self.instance_id = f"server_rule_manager_{id(self)}"
        self.name = "子服务器规则管理器"
        self.description = "负责管理和应用子服务器系统的规则"
        self.logger = logger
        self.logger.info(f"初始化子服务器规则管理器: {self.instance_id}")
        
        # 规则存储
        self.rules = {
            "server_registration": {
                "max_servers": 100,
                "min_resources": {
                    "cpu": 1,
                    "memory": 2,
                    "disk": 20,
                    "network": 10
                },
                "allowed_ips": [],  # 空列表表示允许所有IP
                "denied_ips": [],
                "required_metadata": ["server_name", "host", "port"]
            },
            "server_health": {
                "health_check_interval": 30,  # 健康检查间隔（秒）
                "max_failed_checks": 3,  # 最大失败检查次数
                "timeout": 5,  # 健康检查超时时间（秒）
                "min_response_time": 0,  # 最小响应时间（毫秒）
                "max_response_time": 5000,  # 最大响应时间（毫秒）
                "min_uptime": 60  # 最小运行时间（秒）
            },
            "resource_usage": {
                "max_cpu_usage": 90,  # 最大CPU使用率（%）
                "max_memory_usage": 90,  # 最大内存使用率（%）
                "max_disk_usage": 95,  # 最大磁盘使用率（%）
                "max_network_traffic": 90,  # 最大网络流量使用率（%）
                "min_free_memory": 512,  # 最小可用内存（MB）
                "min_free_disk": 5120  # 最小可用磁盘空间（MB）
            },
            "load_balancing": {
                "strategy": "round_robin",  # 负载均衡策略：round_robin, random, least_connections, least_load
                "max_connections_per_server": 1000,  # 每服务器最大连接数
                "min_servers": 1,  # 最小服务器数量
                "max_servers": 100,  # 最大服务器数量
                "auto_scaling": True,  # 是否启用自动伸缩
                "scale_up_threshold": 70,  # 触发扩容的负载阈值（%）
                "scale_down_threshold": 30  # 触发缩容的负载阈值（%）
            },
            "security": {
                "enable_auth": False,  # 是否启用认证
                "require_ssl": False,  # 是否要求SSL
                "allowed_ports": [80, 443, 8000, 8080, 8888],  # 允许的端口
                "denied_ports": [22, 3389],  # 拒绝的端口
                "max_login_attempts": 5,  # 最大登录尝试次数
                "lockout_duration": 300  # 锁定 duration（秒）
            },
            "performance": {
                "min_performance_score": 50,  # 最小性能分数
                "performance_check_interval": 60,  # 性能检查间隔（秒）
                "anomaly_detection": True,  # 是否启用异常检测
                "failure_prediction": True  # 是否启用故障预测
            }
        }
        
        # 规则历史记录
        self.rule_history = {
            "server_registration": [],
            "server_health": [],
            "resource_usage": [],
            "load_balancing": [],
            "security": [],
            "performance": []
        }
        
        # 加载配置文件
        if config_file:
            self.load_config(config_file)
    
    def load_config(self, config_file: str):
        """加载规则配置文件
        
        Args:
            config_file: 配置文件路径
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "server_rules" in config:
                    self.rules.update(config["server_rules"])
                self.logger.info(f"加载子服务器规则配置文件成功: {config_file}")
        except Exception as e:
            self.logger.error(f"加载子服务器规则配置文件失败: {str(e)}")
    
    def save_config(self, config_file: str):
        """保存规则配置到文件
        
        Args:
            config_file: 配置文件路径
        """
        try:
            config = {
                "server_rules": self.rules
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                self.logger.info(f"保存子服务器规则配置文件成功: {config_file}")
        except Exception as e:
            self.logger.error(f"保存子服务器规则配置文件失败: {str(e)}")
    
    def get_rule(self, rule_type: str, rule_name: str) -> Any:
        """获取规则
        
        Args:
            rule_type: 规则类型
            rule_name: 规则名称
            
        Returns:
            规则值
        """
        if rule_type in self.rules and rule_name in self.rules[rule_type]:
            return self.rules[rule_type][rule_name]
        return None
    
    def set_rule(self, rule_type: str, rule_name: str, value: Any):
        """设置规则
        
        Args:
            rule_type: 规则类型
            rule_name: 规则名称
            value: 规则值
        """
        if rule_type not in self.rules:
            self.rules[rule_type] = {}
        
        # 记录规则历史
        if rule_type not in self.rule_history:
            self.rule_history[rule_type] = []
        
        self.rule_history[rule_type].append({
            "rule_name": rule_name,
            "old_value": self.rules[rule_type].get(rule_name),
            "new_value": value,
            "timestamp": datetime.now().isoformat()
        })
        
        # 设置新规则
        self.rules[rule_type][rule_name] = value
        self.logger.info(f"设置子服务器规则: {rule_type}.{rule_name} = {value}")
    
    def get_rules(self, rule_type: str) -> Dict[str, Any]:
        """获取指定类型的所有规则
        
        Args:
            rule_type: 规则类型
            
        Returns:
            规则字典
        """
        if rule_type in self.rules:
            return self.rules[rule_type]
        return {}
    
    def update_rules(self, rule_type: str, rules: Dict[str, Any]):
        """更新指定类型的规则
        
        Args:
            rule_type: 规则类型
            rules: 规则字典
        """
        if rule_type not in self.rules:
            self.rules[rule_type] = {}
        
        for rule_name, value in rules.items():
            self.set_rule(rule_type, rule_name, value)
        
        self.logger.info(f"更新子服务器规则类型: {rule_type}, 更新了 {len(rules)} 条规则")
    
    def check_server_registration(self, server_info: Dict[str, Any]) -> Dict[str, Any]:
        """检查服务器注册规则
        
        Args:
            server_info: 服务器信息
            
        Returns:
            检查结果
        """
        try:
            rules = self.rules.get("server_registration", {})
            errors = []
            
            # 检查服务器名称
            server_name = server_info.get("server_name")
            if not server_name:
                errors.append("服务器名称不能为空")
            
            # 检查主机和端口
            host = server_info.get("host")
            port = server_info.get("port")
            if not host:
                errors.append("服务器主机不能为空")
            if not port:
                errors.append("服务器端口不能为空")
            
            # 检查IP地址
            ip = server_info.get("ip", host)
            allowed_ips = rules.get("allowed_ips", [])
            denied_ips = rules.get("denied_ips", [])
            
            if allowed_ips and ip not in allowed_ips:
                errors.append(f"IP地址 {ip} 不在允许列表中")
            if ip in denied_ips:
                errors.append(f"IP地址 {ip} 在拒绝列表中")
            
            # 检查资源要求
            resources = server_info.get("resources", {})
            min_resources = rules.get("min_resources", {})
            
            if "cpu" in min_resources:
                cpu = resources.get("cpu", 0)
                if cpu < min_resources["cpu"]:
                    errors.append(f"CPU资源不足，至少需要 {min_resources['cpu']} 核心")
            
            if "memory" in min_resources:
                memory = resources.get("memory", 0)
                if memory < min_resources["memory"]:
                    errors.append(f"内存资源不足，至少需要 {min_resources['memory']} GB")
            
            if "disk" in min_resources:
                disk = resources.get("disk", 0)
                if disk < min_resources["disk"]:
                    errors.append(f"磁盘资源不足，至少需要 {min_resources['disk']} GB")
            
            if "network" in min_resources:
                network = resources.get("network", 0)
                if network < min_resources["network"]:
                    errors.append(f"网络带宽不足，至少需要 {min_resources['network']} Mbps")
            
            # 检查必需的元数据
            required_metadata = rules.get("required_metadata", [])
            metadata = server_info.get("metadata", {})
            
            for key in required_metadata:
                if key not in metadata:
                    errors.append(f"缺少必需的元数据: {key}")
            
            result = {
                "success": len(errors) == 0,
                "errors": errors,
                "warnings": [],
                "rule_type": "server_registration"
            }
            
            self.logger.info(f"检查服务器注册规则: {result['success']}, 错误数: {len(errors)}")
            return result
        except Exception as e:
            self.logger.error(f"检查服务器注册规则失败: {str(e)}")
            return {
                "success": False,
                "errors": [f"检查服务器注册规则失败: {str(e)}"],
                "warnings": [],
                "rule_type": "server_registration"
            }
    
    def check_server_health(self, server_info: Dict[str, Any]) -> Dict[str, Any]:
        """检查服务器健康规则
        
        Args:
            server_info: 服务器信息
            
        Returns:
            检查结果
        """
        try:
            rules = self.rules.get("server_health", {})
            errors = []
            warnings = []
            
            # 检查响应时间
            response_time = server_info.get("response_time", 0)
            min_response_time = rules.get("min_response_time", 0)
            max_response_time = rules.get("max_response_time", 5000)
            
            if response_time < min_response_time:
                warnings.append(f"响应时间过低，可能存在问题: {response_time}ms")
            if response_time > max_response_time:
                errors.append(f"响应时间过高，超过阈值: {response_time}ms > {max_response_time}ms")
            
            # 检查运行时间
            uptime = server_info.get("uptime", 0)
            min_uptime = rules.get("min_uptime", 60)
            
            if uptime < min_uptime:
                warnings.append(f"运行时间过短，可能不稳定: {uptime}s < {min_uptime}s")
            
            # 检查失败检查次数
            failed_checks = server_info.get("failed_checks", 0)
            max_failed_checks = rules.get("max_failed_checks", 3)
            
            if failed_checks >= max_failed_checks:
                errors.append(f"健康检查失败次数过多: {failed_checks} >= {max_failed_checks}")
            
            result = {
                "success": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "rule_type": "server_health"
            }
            
            self.logger.info(f"检查服务器健康规则: {result['success']}, 错误数: {len(errors)}, 警告数: {len(warnings)}")
            return result
        except Exception as e:
            self.logger.error(f"检查服务器健康规则失败: {str(e)}")
            return {
                "success": False,
                "errors": [f"检查服务器健康规则失败: {str(e)}"],
                "warnings": [],
                "rule_type": "server_health"
            }
    
    def check_resource_usage(self, server_info: Dict[str, Any]) -> Dict[str, Any]:
        """检查资源使用规则
        
        Args:
            server_info: 服务器信息
            
        Returns:
            检查结果
        """
        try:
            rules = self.rules.get("resource_usage", {})
            errors = []
            warnings = []
            
            # 检查CPU使用率
            cpu_usage = server_info.get("cpu_usage", 0)
            max_cpu_usage = rules.get("max_cpu_usage", 90)
            
            if cpu_usage > max_cpu_usage:
                errors.append(f"CPU使用率过高: {cpu_usage}% > {max_cpu_usage}%")
            elif cpu_usage > max_cpu_usage * 0.8:
                warnings.append(f"CPU使用率较高: {cpu_usage}% > {max_cpu_usage * 0.8}%")
            
            # 检查内存使用率
            memory_usage = server_info.get("memory_usage", 0)
            max_memory_usage = rules.get("max_memory_usage", 90)
            
            if memory_usage > max_memory_usage:
                errors.append(f"内存使用率过高: {memory_usage}% > {max_memory_usage}%")
            elif memory_usage > max_memory_usage * 0.8:
                warnings.append(f"内存使用率较高: {memory_usage}% > {max_memory_usage * 0.8}%")
            
            # 检查磁盘使用率
            disk_usage = server_info.get("disk_usage", 0)
            max_disk_usage = rules.get("max_disk_usage", 95)
            
            if disk_usage > max_disk_usage:
                errors.append(f"磁盘使用率过高: {disk_usage}% > {max_disk_usage}%")
            elif disk_usage > max_disk_usage * 0.8:
                warnings.append(f"磁盘使用率较高: {disk_usage}% > {max_disk_usage * 0.8}%")
            
            # 检查网络流量
            network_traffic = server_info.get("network_traffic", 0)
            max_network_traffic = rules.get("max_network_traffic", 90)
            
            if network_traffic > max_network_traffic:
                errors.append(f"网络流量过高: {network_traffic}% > {max_network_traffic}%")
            elif network_traffic > max_network_traffic * 0.8:
                warnings.append(f"网络流量较高: {network_traffic}% > {max_network_traffic * 0.8}%")
            
            # 检查可用内存
            free_memory = server_info.get("free_memory", 0)
            min_free_memory = rules.get("min_free_memory", 512)
            
            if free_memory < min_free_memory:
                errors.append(f"可用内存不足: {free_memory}MB < {min_free_memory}MB")
            
            # 检查可用磁盘空间
            free_disk = server_info.get("free_disk", 0)
            min_free_disk = rules.get("min_free_disk", 5120)
            
            if free_disk < min_free_disk:
                errors.append(f"可用磁盘空间不足: {free_disk}MB < {min_free_disk}MB")
            
            result = {
                "success": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "rule_type": "resource_usage"
            }
            
            self.logger.info(f"检查资源使用规则: {result['success']}, 错误数: {len(errors)}, 警告数: {len(warnings)}")
            return result
        except Exception as e:
            self.logger.error(f"检查资源使用规则失败: {str(e)}")
            return {
                "success": False,
                "errors": [f"检查资源使用规则失败: {str(e)}"],
                "warnings": [],
                "rule_type": "resource_usage"
            }
    
    def check_security(self, server_info: Dict[str, Any]) -> Dict[str, Any]:
        """检查安全规则
        
        Args:
            server_info: 服务器信息
            
        Returns:
            检查结果
        """
        try:
            rules = self.rules.get("security", {})
            errors = []
            warnings = []
            
            # 检查端口
            port = server_info.get("port")
            allowed_ports = rules.get("allowed_ports", [80, 443, 8000, 8080, 8888])
            denied_ports = rules.get("denied_ports", [22, 3389])
            
            if allowed_ports and port not in allowed_ports:
                warnings.append(f"端口 {port} 不在允许列表中")
            if port in denied_ports:
                errors.append(f"端口 {port} 在拒绝列表中")
            
            # 检查SSL
            require_ssl = rules.get("require_ssl", False)
            ssl_enabled = server_info.get("ssl_enabled", False)
            
            if require_ssl and not ssl_enabled:
                errors.append("SSL已启用，但服务器未配置SSL")
            
            # 检查认证
            enable_auth = rules.get("enable_auth", False)
            auth_enabled = server_info.get("auth_enabled", False)
            
            if enable_auth and not auth_enabled:
                errors.append("认证已启用，但服务器未配置认证")
            
            result = {
                "success": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "rule_type": "security"
            }
            
            self.logger.info(f"检查安全规则: {result['success']}, 错误数: {len(errors)}, 警告数: {len(warnings)}")
            return result
        except Exception as e:
            self.logger.error(f"检查安全规则失败: {str(e)}")
            return {
                "success": False,
                "errors": [f"检查安全规则失败: {str(e)}"],
                "warnings": [],
                "rule_type": "security"
            }
    
    def check_performance(self, server_info: Dict[str, Any]) -> Dict[str, Any]:
        """检查性能规则
        
        Args:
            server_info: 服务器信息
            
        Returns:
            检查结果
        """
        try:
            rules = self.rules.get("performance", {})
            errors = []
            warnings = []
            
            # 检查性能分数
            performance_score = server_info.get("performance_score", 0)
            min_performance_score = rules.get("min_performance_score", 50)
            
            if performance_score < min_performance_score:
                errors.append(f"性能分数过低: {performance_score} < {min_performance_score}")
            elif performance_score < min_performance_score * 1.2:
                warnings.append(f"性能分数较低: {performance_score} < {min_performance_score * 1.2}")
            
            result = {
                "success": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "rule_type": "performance"
            }
            
            self.logger.info(f"检查性能规则: {result['success']}, 错误数: {len(errors)}, 警告数: {len(warnings)}")
            return result
        except Exception as e:
            self.logger.error(f"检查性能规则失败: {str(e)}")
            return {
                "success": False,
                "errors": [f"检查性能规则失败: {str(e)}"],
                "warnings": [],
                "rule_type": "performance"
            }
    
    def get_rule_history(self, rule_type: str) -> List[Dict[str, Any]]:
        """获取规则历史记录
        
        Args:
            rule_type: 规则类型
            
        Returns:
            规则历史记录
        """
        if rule_type in self.rule_history:
            return self.rule_history[rule_type]
        return []
    
    def get_all_rules(self) -> Dict[str, Dict[str, Any]]:
        """获取所有规则
        
        Returns:
            规则字典
        """
        return self.rules
    
    def __str__(self):
        return f"ServerRuleManager(instance_id={self.instance_id}, name={self.name})"
    
    def __repr__(self):
        return self.__str__()

# 创建全局子服务器规则管理器实例
server_rule_manager = ServerRuleManager()