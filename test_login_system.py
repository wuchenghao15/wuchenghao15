# -*- coding: utf-8 -*-
import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'flask-app')))

from app.ai.login_analyzer import ai_login_analyzer
from app.utils.rule_manager import rule_manager
from app.utils.permission_manager import permission_manager
from app.utils.route_manager import route_manager

class TestLoginSystem(unittest.TestCase):
    """测试登录系统的各项功能"""

    def test_ai_login_analyzer(self):
        """测试AI登录分析器"""
        print("测试AI登录分析器...")

        # 测试分析登录尝试
        analysis = ai_login_analyzer.analyze_login_attempt(
            username="admin",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
        )

        self.assertIsInstance(analysis, dict)
        self.assertIn("risk_level", analysis)
        self.assertIn("suggestions", analysis)
        self.assertIn("is_anomaly", analysis)

        print(f"AI登录分析结果: {analysis}")
        print("AI登录分析器测试通过!")

    def test_rule_manager(self):
        """测试规则管理器"""
        print("\n测试规则管理器...")

        # 测试IP限制规则
        ip_check = rule_manager.check_rule("login", "ip_restriction", ip_address="127.0.0.1")
        self.assertIsInstance(ip_check, dict)
        self.assertIn("success", ip_check)

        # 测试速率限制规则
        rate_limit_check = rule_manager.check_rule("login", "rate_limiting", ip_address="127.0.0.1")
        self.assertIsInstance(rate_limit_check, dict)
        self.assertIn("success", rate_limit_check)

        # 测试最大尝试次数规则
        login_attempts_check = rule_manager.check_rule("login", "max_attempts", username="admin")
        self.assertIsInstance(login_attempts_check, dict)
        self.assertIn("success", login_attempts_check)

        print(f"IP限制规则检查结果: {ip_check}")
        print(f"速率限制规则检查结果: {rate_limit_check}")
        print(f"最大尝试次数规则检查结果: {login_attempts_check}")
        print("规则管理器测试通过!")

    def test_permission_manager(self):
        """测试权限管理器"""
        print("\n测试权限管理器...")

        # 测试获取角色权限
        admin_permissions = permission_manager.get_role_permissions("admin")
        self.assertIsInstance(admin_permissions, list)
        self.assertGreater(len(admin_permissions), 0)

        user_permissions = permission_manager.get_role_permissions("user")
        self.assertIsInstance(user_permissions, list)
        self.assertGreater(len(user_permissions), 0)

        # 测试检查权限
        has_manage_users_permission = permission_manager.has_permission("admin", "manage_users")
        self.assertTrue(has_manage_users_permission)

        has_manage_system_permission = permission_manager.has_permission("admin", "manage_system")
        self.assertTrue(has_manage_system_permission)

        has_manage_users_permission_for_user = permission_manager.has_permission("user", "manage_users")
        self.assertFalse(has_manage_users_permission_for_user)

        print(f"管理员权限: {admin_permissions}")
        print(f"用户权限: {user_permissions}")
        print(f"管理员是否有manage_users权限: {has_manage_users_permission}")
        print(f"管理员是否有manage_system权限: {has_manage_system_permission}")
        print(f"用户是否有manage_users权限: {has_manage_users_permission_for_user}")
        print("权限管理器测试通过!")

    def test_route_manager(self):
        """测试路由管理器"""
        print("\n测试路由管理器...")

        # 测试获取路由
        login_route = route_manager.get_route("auth", "login")
        self.assertEqual(login_route, "/login")

        register_route = route_manager.get_route("auth", "register")
        self.assertEqual(register_route, "/register")

        # 测试获取路由权限
        login_permissions = route_manager.get_route_permissions("auth.login")
        self.assertIsInstance(login_permissions, list)

        admin_center_permissions = route_manager.get_route_permissions("main.admin_center")
        self.assertIsInstance(admin_center_permissions, list)
        self.assertIn("admin", admin_center_permissions)

        # 测试检查路由权限
        admin_has_access = route_manager.check_route_permission("main.admin_center", "admin", ["admin"])
        self.assertTrue(admin_has_access)

        user_has_access = route_manager.check_route_permission("main.admin_center", "user", ["user"])
        self.assertFalse(user_has_access)

        print(f"登录路由: {login_route}")
        print(f"注册路由: {register_route}")
        print(f"登录路由权限: {login_permissions}")
        print(f"管理员中心路由权限: {admin_center_permissions}")
        print(f"管理员是否有访问管理员中心的权限: {admin_has_access}")
        print(f"用户是否有访问管理员中心的权限: {user_has_access}")
        print("路由管理器测试通过!")

if __name__ == "__main__":
    print("开始测试登录系统...")
    unittest.main()
