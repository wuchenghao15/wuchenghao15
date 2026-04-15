import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Callable

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RuleManager:
    """规则管理器，负责管理和应用不同的登录规则"""
    
    def __init__(self, config_file: str = None):
        self.instance_id = f"rule_manager_{id(self)}"
        self.name = "规则管理器"
        self.description = "负责管理和应用不同的登录规则"
        self.logger = logger
        self.logger.info(f"初始化规则管理器: {self.instance_id}")
        
        # 规则存储
        self.rules = {
            "login": {
                "max_attempts": 5,
                "lockout_duration": 300,  # 5分钟
                "min_password_length": 8,
                "require_strong_password": True,
                "enable_2fa": False,
                "enable_ip_restriction": False,
                "allowed_ips": [],
                "blocked_ips": [],
                "enable_rate_limiting": True,
                "rate_limit_window": 60,  # 1分钟
                "rate_limit_max_requests": 10
            },
            "registration": {
                "allow_registration": True,
                "require_email_verification": False,
                "max_registrations_per_ip": 5,
                "registration_cooldown": 3600,  # 1小时
                "enable_captcha": False
            },
            "session": {
                "session_timeout": 3600,  # 1小时
                "max_sessions_per_user": 5,
                "enable_session_management": True,
                "enable_session_revocation": True
            },
            "security": {
                "enable_brute_force_protection": True,
                "enable_account_lockout": True,
                "enable_ip_ban": True,
                "enable_logging": True,
                "enable_audit_trail": True
            }
        }
        
        # 规则执行器
        self.rule_executors = {
            "login": {
                "max_attempts": self._check_login_attempts,
                "ip_restriction": self._check_ip_restriction,
                "rate_limiting": self._check_rate_limiting
            },
            "registration": {
                "max_registrations_per_ip": self._check_registration_limit,
                "captcha": self._check_captcha
            }
        }
        
        # 规则状态
        self.rule_state = {
            "login_attempts": {},
            "registrations": {},
            "rate_limits": {}
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
                if "rules" in config:
                    self.rules.update(config["rules"])
                    self.logger.info(f"加载规则配置文件成功: {config_file}")
        except Exception as e:
            self.logger.error(f"加载规则配置文件失败: {str(e)}")
    
    def save_config(self, config_file: str):
        """保存规则配置到文件
        
        Args:
            config_file: 配置文件路径
        """
        try:
            config = {"rules": self.rules}
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                self.logger.info(f"保存规则配置文件成功: {config_file}")
        except Exception as e:
            self.logger.error(f"保存规则配置文件失败: {str(e)}")
    
    def get_rule(self, rule_type: str, rule_name: str) -> Any:
        """获取规则值
        
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
        """设置规则值
        
        Args:
            rule_type: 规则类型
            rule_name: 规则名称
            value: 规则值
        """
        if rule_type not in self.rules:
            self.rules[rule_type] = {}
        self.rules[rule_type][rule_name] = value
        self.logger.info(f"设置规则: {rule_type}.{rule_name} = {value}")
    
    def check_rule(self, rule_type: str, rule_name: str, **kwargs) -> Dict[str, Any]:
        """检查规则
        
        Args:
            rule_type: 规则类型
            rule_name: 规则名称
            **kwargs: 规则检查需要的参数
            
        Returns:
            检查结果
        """
        if rule_type in self.rule_executors and rule_name in self.rule_executors[rule_type]:
            executor = self.rule_executors[rule_type][rule_name]
            return executor(**kwargs)
        return {"success": True, "message": "规则检查通过"}
    
    def _check_login_attempts(self, username: str, **kwargs) -> Dict[str, Any]:
        """检查登录尝试次数
        
        Args:
            username: 用户名
            
        Returns:
            检查结果
        """
        max_attempts = self.rules["login"]["max_attempts"]
        lockout_duration = self.rules["login"]["lockout_duration"]
        
        if username not in self.rule_state["login_attempts"]:
            self.rule_state["login_attempts"][username] = {
                "attempts": 0,
                "last_attempt": None,
                "locked_until": None
            }
        
        user_attempts = self.rule_state["login_attempts"][username]
        
        # 检查是否被锁定
        if user_attempts["locked_until"]:
            locked_until = datetime.fromisoformat(user_attempts["locked_until"])
            if datetime.now() < locked_until:
                remaining_time = int((locked_until - datetime.now()).total_seconds())
                return {
                    "success": False,
                    "message": f"账户已被锁定，请 {remaining_time} 秒后再试"
                }
            else:
                # 锁定时间已过，重置尝试次数
                user_attempts["attempts"] = 0
                user_attempts["locked_until"] = None
        
        # 增加尝试次数
        user_attempts["attempts"] += 1
        user_attempts["last_attempt"] = datetime.now().isoformat()
        
        # 检查是否达到最大尝试次数
        if user_attempts["attempts"] > max_attempts:
            locked_until = (datetime.now() + timedelta(seconds=lockout_duration)).isoformat()
            user_attempts["locked_until"] = locked_until
            return {
                "success": False,
                "message": f"登录失败次数过多，账户已被锁定 {lockout_duration} 秒"
            }
        
        return {"success": True, "message": "登录尝试次数检查通过"}
    
    def _check_ip_restriction(self, ip_address: str, **kwargs) -> Dict[str, Any]:
        """检查IP地址限制
        
        Args:
            ip_address: IP地址
            
        Returns:
            检查结果
        """
        enable_ip_restriction = self.rules["login"]["enable_ip_restriction"]
        allowed_ips = self.rules["login"]["allowed_ips"]
        blocked_ips = self.rules["login"]["blocked_ips"]
        
        if not enable_ip_restriction:
            return {"success": True, "message": "IP地址限制未启用"}
        
        # 检查是否在黑名单中
        if ip_address in blocked_ips:
            return {
                "success": False,
                "message": "IP地址已被禁止访问"
            }
        
        # 检查是否在白名单中
        if allowed_ips and ip_address not in allowed_ips:
            return {
                "success": False,
                "message": "IP地址不在允许列表中"
            }
        
        return {"success": True, "message": "IP地址检查通过"}
    
    def _check_rate_limiting(self, ip_address: str, **kwargs) -> Dict[str, Any]:
        """检查速率限制
        
        Args:
            ip_address: IP地址
            
        Returns:
            检查结果
        """
        enable_rate_limiting = self.rules["login"]["enable_rate_limiting"]
        rate_limit_window = self.rules["login"]["rate_limit_window"]
        rate_limit_max_requests = self.rules["login"]["rate_limit_max_requests"]
        
        if not enable_rate_limiting:
            return {"success": True, "message": "速率限制未启用"}
        
        if ip_address not in self.rule_state["rate_limits"]:
            self.rule_state["rate_limits"][ip_address] = {
                "requests": [],
                "last_cleanup": datetime.now().isoformat()
            }
        
        rate_limit = self.rule_state["rate_limits"][ip_address]
        
        # 清理过期的请求记录
        current_time = datetime.now()
        rate_limit["requests"] = [
            req for req in rate_limit["requests"]
            if (current_time - datetime.fromisoformat(req)).total_seconds() < rate_limit_window
        ]
        
        # 检查是否达到速率限制
        if len(rate_limit["requests"]) >= rate_limit_max_requests:
            return {
                "success": False,
                "message": f"请求过于频繁，请 {rate_limit_window} 秒后再试"
            }
        
        # 添加当前请求
        rate_limit["requests"].append(current_time.isoformat())
        
        return {"success": True, "message": "速率限制检查通过"}
    
    def _check_registration_limit(self, ip_address: str, **kwargs) -> Dict[str, Any]:
        """检查注册限制
        
        Args:
            ip_address: IP地址
            
        Returns:
            检查结果
        """
        max_registrations = self.rules["registration"]["max_registrations_per_ip"]
        registration_cooldown = self.rules["registration"]["registration_cooldown"]
        
        if ip_address not in self.rule_state["registrations"]:
            self.rule_state["registrations"][ip_address] = {
                "count": 0,
                "last_registration": None
            }
        
        registration = self.rule_state["registrations"][ip_address]
        
        # 检查冷却时间
        if registration["last_registration"]:
            last_reg = datetime.fromisoformat(registration["last_registration"])
            if (datetime.now() - last_reg).total_seconds() < registration_cooldown:
                remaining_time = int((last_reg + timedelta(seconds=registration_cooldown) - datetime.now()).total_seconds())
                return {
                    "success": False,
                    "message": f"注册过于频繁，请 {remaining_time} 秒后再试"
                }
        
        # 检查注册次数
        if registration["count"] >= max_registrations:
            return {
                "success": False,
                "message": "该IP地址注册次数已达上限"
            }
        
        # 增加注册次数
        registration["count"] += 1
        registration["last_registration"] = datetime.now().isoformat()
        
        return {"success": True, "message": "注册限制检查通过"}
    
    def _check_captcha(self, captcha_response: str = None, **kwargs) -> Dict[str, Any]:
        """检查验证码
        
        Args:
            captcha_response: 验证码响应
            
        Returns:
            检查结果
        """
        enable_captcha = self.rules["registration"]["enable_captcha"]
        
        if not enable_captcha:
            return {"success": True, "message": "验证码未启用"}
        
        if not captcha_response:
            return {
                "success": False,
                "message": "请输入验证码"
            }
        
        # 这里可以添加验证码验证逻辑
        # 例如，使用Google reCAPTCHA或其他验证码服务
        
        return {"success": True, "message": "验证码检查通过"}
    
    def reset_login_attempts(self, username: str):
        """重置登录尝试次数
        
        Args:
            username: 用户名
        """
        if username in self.rule_state["login_attempts"]:
            self.rule_state["login_attempts"][username] = {
                "attempts": 0,
                "last_attempt": None,
                "locked_until": None
            }
            self.logger.info(f"重置登录尝试次数: {username}")
    
    def __str__(self):
        return f"RuleManager(instance_id={self.instance_id}, name={self.name})"
    
    def __repr__(self):
        return self.__str__()

# 创建全局规则管理器实例
rule_manager = RuleManager()