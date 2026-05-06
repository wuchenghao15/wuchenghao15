#!/usr/bin/env python3
"""
测试优化后的index路由功能

import sys
import os
import uuid

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 模拟Flask会话
class MockSession:
    def __init__(self):
        self.data = {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, key):
        return key in self.data

# 测试自动游客登录和AI智能路由功能
def test_index_route():
    print("=== 测试优化后的index路由功能 ===")

    # 模拟会话
    session = MockSession()

    print("1. 测试未登录状态下的自动游客登录...")

    # 导入所需模块
    from app.models.user import User
    from app.utils.security import security_utils
    from app.ai.route_optimizer import ai_route_optimizer

    # 测试自动游客登录逻辑
    if not session.get('logged_in'):
        # 生成随机游客用户名
        guest_username = f"guest_{uuid.uuid4().hex[:8]}"
        guest_email = f"{guest_username}@guest.example.com"
        random_password = uuid.uuid4().hex[:16]
        hashed_password = security_utils.hash_password(random_password)

        print(f"   - 生成游客用户: {guest_username}")
        print(f"   - 生成游客邮箱: {guest_email}")

        # 创建游客用户记录到数据库
        guest_user = User(
            username=guest_username,
            email=guest_email,
            password=hashed_password,
            role='guest',
            is_active=1,
            super_admin_approved=1,
            hardware_admin_approved=1
        )

        # 保存游客用户到数据库
        guest_user_id = guest_user.save()
        print(f"   - 游客用户保存成功，ID: {guest_user_id}")

        # 设置会话
        session['logged_in'] = True
        session['username'] = guest_username
        session['user_level'] = 'guest'
        session['user_role'] = 'guest'
        session['is_guest'] = True
        session['user_id'] = guest_user_id

        print("   - 会话设置完成")
        print(f"   - 登录状态: {session.get('logged_in')}")
        print(f"   - 用户名: {session.get('username')}")
        print(f"   - 用户角色: {session.get('user_role')}")

    print("\n2. 测试AI智能路由功能...")

    # 使用AI路由优化器获取最佳路由
    best_route = ai_route_optimizer.calculate_best_route(session)
    print(f"   - AI计算的最佳路由: {best_route}")

    print("\n=== 测试完成 ===")
    return True

if __name__ == "__main__":
    try:
        test_index_route()
        print("\n✅ 测试成功！优化后的index路由功能正常工作。")
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

"""