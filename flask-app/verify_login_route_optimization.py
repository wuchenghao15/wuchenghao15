#!/usr/bin/env python3
"""
验证登录路由优化是否成功
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.rule import Rule
from app.services.enhanced_ai_service import enhanced_ai_service
from app.services.login_route_service import login_route_service
from app.utils.logging import logger

def verify_login_route_optimization():
    """验证登录路由优化是否成功"""
    print("开始验证登录路由优化...")
    
    # 检查1: 登录路由规则是否存在
    print("\n1. 检查登录路由规则...")
    rules = Rule.get_rules_by_type('login_route')
    if rules:
        print(f"✅ 成功找到 {len(rules)} 条登录路由规则")
        for rule in rules:
            print(f"   - {rule.rule_name}: {rule.rule_content} (优先级: {rule.priority})")
    else:
        print("❌ 未找到登录路由规则")
    
    # 检查2: 专门的AI员工是否存在
    print("\n2. 检查专门的AI员工...")
    ai_employees = enhanced_ai_service.get_all_enhanced_ai_employees()
    login_ai = next((e for e in ai_employees if e.ai_type == 'login_route_manager'), None)
    if login_ai:
        print(f"✅ 成功找到专门的登录路由AI员工: {login_ai.name} (ID: {login_ai.employee_id})")
        print(f"   状态: {'已激活' if login_ai.status == 'active' else '未激活'}")
        print(f"   脑库集成: {'已集成' if login_ai.brain_integration else '未集成'}")
        print(f"   适配级别: {login_ai.adaptation_level}")
    else:
        print("❌ 未找到专门的登录路由AI员工")
    
    # 检查3: 登录路由服务是否正常工作
    print("\n3. 测试登录路由服务...")
    test_roles = ['super_admin', 'admin', 'user', 'guest']
    for role in test_roles:
        route = login_route_service.get_login_route(role)
        print(f"   - 角色 {role}: 跳转到 {route}")
    
    print("\n验证完成!")

if __name__ == "__main__":
    verify_login_route_optimization()
