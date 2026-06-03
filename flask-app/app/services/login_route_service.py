#!/usr/bin/env python3
"""
登录路由服务 - 使用加强AI员工统一处理登录用户的路由跳转
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
            self._login_rules = {}
            self._login_ai_employee = None
            self._load_login_rules()
            self._init_login_ai_employee()

    def _load_login_rules(self):
        """从数据库加载登录路由规则"""
        logger.info("从数据库加载登录路由规则...")
        rules = Rule.get_rules_by_type('login_route')

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
        ai_employees = enhanced_ai_service.get_all_enhanced_ai_employees()
        self._login_ai_employee = next(
            (e for e in ai_employees if e.ai_type == 'login_route_manager'),
            None
        )

        if not self._login_ai_employee:
            logger.warning("未找到专门的登录路由AI员工, 将使用默认处理方式")
        else:
            logger.info(f"已找到专门的登录路由AI员工: {self._login_ai_employee.name}, ID: {self._login_ai_employee.employee_id}")

    def refresh_rules(self):
        """刷新登录规则"""
        self._load_login_rules()

    def get_login_route(self, user_role):
        """根据用户角色获取登录后跳转的路由

        Args:
            user_role: 用户角色

        Returns:
            str: 路由端点, 如 'main.dashboard'
        """
        if self._login_ai_employee:
            return self._handle_with_ai_employee(user_role)
        return self._handle_with_rules(user_role)

    def _handle_with_ai_employee(self, user_role):
        """使用AI员工处理登录路由跳转

        Args:
            user_role: 用户角色

        Returns:
            str: 路由端点
        """
        try:
            from app.ai.instances import ai_instance_manager

            request_data = {
                'user_role': user_role,
                'login_rules': self._login_rules,
                'timestamp': self._get_current_timestamp()
            }

            result = ai_instance_manager.process_request(
                request_type='login_route',
                data=request_data
            )

            if result and result.get('success') and result.get('route'):
                logger.info(f"AI员工返回路由: {result['route']}")
                return result['route']
        except Exception as e:
            logger.error(f"AI员工处理登录路由失败: {str(e)}")

        return self._handle_with_rules(user_role)

    def _handle_with_rules(self, user_role):
        """使用规则处理登录路由跳转

        Args:
            user_role: 用户角色

        Returns:
            str: 路由端点
        """
        for rule_name, rule_data in self._login_rules.items():
            if '->' in rule_data['rule_content']:
                parts = rule_data['rule_content'].split('->', 1)
                roles_str = parts[0]
                endpoint = parts[1] if len(parts) > 1 else ''
                roles = [role.strip() for role in roles_str.split(',')]

                if user_role in roles:
                    logger.info(f"匹配到规则 {rule_name}, 跳转到 {endpoint}")
                    return endpoint.strip()
        return 'main.dashboard'

    def _get_current_timestamp(self):
        """获取当前时间戳

        Returns:
            str: 当前时间戳
        """
        from datetime import datetime
        return datetime.now().isoformat()


login_route_service = LoginRouteService()
