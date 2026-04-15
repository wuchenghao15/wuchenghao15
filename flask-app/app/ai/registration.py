import time
from app.utils.logging import logger
from app.models.user import User
from app.ai.validator import validator_ai
from app.utils.security import security_utils
from app.ai.instances import ai_instance_manager

class RegistrationAI:
    """注册AI，负责处理用户注册流程"""
    
    def __init__(self):
        self.instance_id = f"registration_ai_{id(self)}"
        self.name = "注册AI"
        self.description = "负责处理用户注册流程，包括验证、处理和监控"
        self.logger = logger
        self.logger.info(f"初始化注册AI: {self.instance_id}")
        
        # 注册配置
        self.registration_config = {
            "enabled": True,
            "require_email_verification": False,
            "require_phone_verification": False,
            "max_attempts_per_ip": 10,
            "cooldown_period": 3600,  # 1小时
            "block_suspicious_ips": True,
            "auto_approve_known_ips": [],
            "ai_notification_enabled": True,
            "fraud_detection_enabled": True,
            "password_complexity": {
                "require_upper": True,
                "require_lower": True,
                "require_digit": True,
                "require_special": True,
                "min_length": 8,
                "max_length": 64
            }
        }
        
        # 注册统计
        self.registration_stats = {
            "total_registrations": 0,
            "successful_registrations": 0,
            "failed_registrations": 0,
            "suspicious_attempts": 0,
            "auto_approved": 0,
            "manual_review": 0,
            "daily_stats": {},
            "ip_stats": {}
        }
    
    def register_user(self, user_data, ip_address="127.0.0.1"):
        """处理用户注册请求"""
        try:
            self.logger.info(f"{self.instance_id} 收到注册请求，IP: {ip_address}")
            
            # 增加总注册尝试次数
            self.registration_stats["total_registrations"] += 1
            
            # 验证注册数据
            validation_result = self._validate_registration_data(user_data)
            if not validation_result["success"]:
                self.registration_stats["failed_registrations"] += 1
                return {
                    "success": False,
                    "message": "注册数据验证失败",
                    "errors": validation_result["errors"]
                }
            
            # 检查IP是否被限制
            if self._is_ip_restricted(ip_address):
                self.registration_stats["suspicious_attempts"] += 1
                return {
                    "success": False,
                    "message": "该IP地址注册过于频繁，请稍后再试"
                }
            
            # 检查用户名是否已存在
            if User.get_by_username(user_data["username"]):
                self.registration_stats["failed_registrations"] += 1
                return {
                    "success": False,
                    "message": "用户名已存在"
                }
            
            # 检查邮箱是否已存在
            conn = User._connect_db()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email=?', (user_data["email"],))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.registration_stats["failed_registrations"] += 1
                return {
                    "success": False,
                    "message": "邮箱已存在"
                }
            
            # 哈希密码
            hashed_password = security_utils.hash_password(user_data["password"])
            
            # 创建新用户
            new_user = User(
                username=user_data["username"],
                password=hashed_password,
                email=user_data["email"],
                role=user_data.get("role", "user")
            )
            user_id = new_user.save()
            
            # 为新用户创建专用AI实例
            try:
                # 创建用户专用AI实例
                instance_id = f"user_{user_data['username']}_ai"
                ai_instance_manager.create_ai_instance(
                    instance_id=instance_id,
                    ai_type="user_dedicated",
                    name=f"{user_data['username']}的专用AI",
                    description=f"为用户{user_data['username']}创建的专用AI实例，用于个性化学习辅助",
                    functions=["个性化测试生成", "学习进度分析", "知识点推荐"],
                    responsibilities=["处理用户的个性化学习请求", "生成符合用户水平的测试题", "分析用户学习数据"],
                    config={"user_id": user_id, "username": user_data['username']}
                )
                
                # 将AI实例绑定到用户
                ai_instance_manager.bind_ai_instance(user_id, instance_id)
                self.logger.info(f"{self.instance_id} 为用户 {user_data['username']} 创建并绑定专用AI实例: {instance_id}")
            except Exception as e:
                self.logger.error(f"{self.instance_id} 为用户 {user_data['username']} 创建专用AI实例失败: {str(e)}")
            
            # 增加成功注册次数
            self.registration_stats["successful_registrations"] += 1
            
            # 更新每日统计
            self._update_daily_stats()
            
            self.logger.info(f"{self.instance_id} 用户注册成功: {user_data['username']}")
            
            return {
                "success": True,
                "message": "注册成功",
                "user": {
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "role": user_data.get("role", "user")
                }
            }
        except Exception as e:
            self.registration_stats["failed_registrations"] += 1
            self.logger.error(f"{self.instance_id} 注册失败: {str(e)}")
            return {
                "success": False,
                "message": f"注册过程中发生错误: {str(e)}"
            }
    
    def _validate_registration_data(self, user_data):
        """验证注册数据"""
        # 定义注册数据的验证模式
        schema = {
            "username": {
                "required": True,
                "type": "string",
                "min_length": 3,
                "max_length": 20,
                "pattern": r"^[a-zA-Z0-9_]{3,20}$"
            },
            "password": {
                "required": True,
                "type": "string",
                "min_length": 8
            },
            "email": {
                "required": True,
                "type": "string",
                "pattern": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            },
            "role": {
                "required": False,
                "type": "string",
                "enum": ["admin", "teacher", "user", "hardware_vikey_admin", "super_admin"]
            }
        }
        
        return validator_ai.validate_data(user_data, schema)
    
    def _is_ip_restricted(self, ip_address):
        """检查IP是否被限制"""
        # 简单的IP限制逻辑，实际项目中可以使用更复杂的算法
        if not self.registration_config["block_suspicious_ips"]:
            return False
        
        # 这里可以添加IP限制的具体实现
        # 例如：检查该IP在最近一小时内的注册尝试次数
        
        return False
    
    def _update_daily_stats(self):
        """更新每日统计信息"""
        today = time.strftime("%Y-%m-%d")
        if today not in self.registration_stats["daily_stats"]:
            self.registration_stats["daily_stats"][today] = {
                "registrations": 0,
                "successful": 0,
                "failed": 0
            }
        
        self.registration_stats["daily_stats"][today]["registrations"] += 1
    
    def get_registration_stats(self):
        """获取注册统计信息"""
        return self.registration_stats
    
    def monitor_registration_process(self, process_id):
        """监控注册动作脚本进程"""
        try:
            self.logger.info(f"{self.instance_id} 开始监控注册进程: {process_id}")
            
            # 这里可以添加进程监控逻辑
            # 例如：检查进程是否在运行，资源使用情况等
            
            return {
                "success": True,
                "message": f"正在监控注册进程: {process_id}",
                "process_id": process_id
            }
        except Exception as e:
            self.logger.error(f"{self.instance_id} 监控注册进程失败: {str(e)}")
            return {
                "success": False,
                "message": f"监控注册进程失败: {str(e)}"
            }
    
    def execute_registration_rules(self, user_data):
        """执行注册规则"""
        try:
            self.logger.info(f"{self.instance_id} 开始执行注册规则")
            
            # 这里可以添加规则执行逻辑
            # 例如：根据用户数据执行不同的注册规则
            
            return {
                "success": True,
                "message": "注册规则执行成功",
                "applied_rules": []
            }
        except Exception as e:
            self.logger.error(f"{self.instance_id} 执行注册规则失败: {str(e)}")
            return {
                "success": False,
                "message": f"执行注册规则失败: {str(e)}"
            }
    
    def __str__(self):
        return f"RegistrationAI(instance_id={self.instance_id}, name={self.name})"
    
    def __repr__(self):
        return self.__str__()

# 创建全局注册AI实例
registration_ai = RegistrationAI()