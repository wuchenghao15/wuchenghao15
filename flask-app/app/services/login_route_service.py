#!/usr/bin/env python3
"""
登录路由服务，使用加强AI员工统一处理登录用户的路由跳转
"""

from app.models.rule import Rule
from app.services.enhanced_ai_service import enhanced_ai_service
from app.utils.logging import logger

class LoginRouteService:
    """登录路由服务类"""
    
    _instance = None
    _login_rules = None
    _login_ai_employee = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(LoginRouteService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化登录路由服务"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._login_rules = {}  # 缓存登录规则
            self._login_ai_employee = None  # 专门的AI员工
            self._load_login_rules()
            self._init_login_ai_employee()
    
    def _load_login_rules(self):
        """从数据库加载登录路由规则"""
        logger.info("从数据库加载登录路由规则...")
        rules = Rule.get_rules_by_type('login_route')
        
        # 构建规则字典
        for rule in rules:
            self._login_rules[rule.rule_name] = {
                'rule_id': rule.id,
                'rule_type': rule.rule_type,
                'rule_name': rule.rule_name,
                'rule_content': rule.rule_content,
                'description': rule.description,
                'priority': rule.priority,
                'enabled': rule.enabled
            }
        
        logger.info(f"成功加载 {len(self._login_rules)} 条登录路由规则")
    
    def _init_login_ai_employee(self):
        """初始化专门的登录路由AI员工"""
        logger.info("初始化专门的登录路由AI员工...")
        # 获取所有加强AI员工
        ai_employees = enhanced_ai_service.get_all_enhanced_ai_employees()
        # 查找专门处理登录路由的AI员工
        self._login_ai_employee = next((e for e in ai_employees if e.ai_type == 'login_route_manager'), None)
        
        if not self._login_ai_employee:
            logger.warning("未找到专门的登录路由AI员工，将使用默认处理方式")
        else:
            logger.info(f"已找到专门的登录路由AI员工: {self._login_ai_employee.name}，ID: {self._login_ai_employee.employee_id}")
    
    def refresh_rules(self):
        """刷新登录规则"""
        self._load_login_rules()
    
    def get_login_route(self, user_role):
        """根据用户角色获取登录后跳转的路由
        
        Args:
            user_role: 用户角色
            
        Returns:
            str: 路由端点，如 'main.dashboard'
        """
        # 如果有专门的AI员工，使用AI员工处理
        if self._login_ai_employee:
            return self._handle_with_ai_employee(user_role)
        
        # 否则使用规则字典处理
        return self._handle_with_rules(user_role)
    
    def _handle_with_ai_employee(self, user_role):
        """使用AI员工处理登录路由跳转
        
        Args:
            user_role: 用户角色
            
        Returns:
            str: 路由端点
        """
        logger.info(f"使用AI员工 {self._login_ai_employee.name} 处理 {user_role} 角色的登录路由")
        
        try:
            # 调用AI员工处理登录路由
            # 这里可以根据实际情况扩展AI员工的处理逻辑
            from app.ai.instances import ai_instance_manager
            
            # 构建处理请求
            request_data = {
                'user_role': user_role,
                'login_rules': self._login_rules,
                'timestamp': self._get_current_timestamp()
            }
            
            # 调用AI员工处理
            result = ai_instance_manager.process_request(
                ai_type='login_route_manager',
                request_type='login_route',
                data=request_data
            )
            
            if result and result.get('success') and result.get('route'):
                logger.info(f"AI员工返回路由: {result['route']}")
                return result['route']
            
            logger.warning(f"AI员工处理失败，使用默认规则")
        except Exception as e:
            logger.error(f"AI员工处理登录路由失败: {str(e)}")
        
        # 降级使用规则处理
        return self._handle_with_rules(user_role)
    
    def _handle_with_rules(self, user_role):
        """使用规则处理登录路由跳转
        
        Args:
            user_role: 用户角色
            
        Returns:
            str: 路由端点
        """
        logger.info(f"使用规则处理 {user_role} 角色的登录路由")
        
        # 遍历规则，找到匹配的角色
        for rule_name, rule_data in sorted(self._login_rules.items(), key=lambda x: x[1]['priority'], reverse=True):
            # 解析规则内容，格式：roles->endpoint
            if '->' in rule_data['rule_content']:
                roles_str, endpoint = rule_data['rule_content'].split('->', 1)
                roles = [role.strip() for role in roles_str.split(',')]
                
                # 检查用户角色是否在规则中
                if user_role in roles:
                    logger.info(f"匹配到规则 {rule_name}，跳转到 {endpoint}")
                    return endpoint.strip()
        
        # 默认跳转
        logger.info(f"未匹配到规则，使用默认路由 main.index")
        return 'main.index'
    
    def _get_current_timestamp(self):
        """获取当前时间戳
        
        Returns:
            str: 当前时间戳
        """
        from datetime import datetime
        return datetime.now().isoformat()


# 初始化登录路由服务
login_route_service = LoginRouteService()
