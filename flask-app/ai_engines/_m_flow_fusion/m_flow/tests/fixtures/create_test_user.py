"""
创建测试用户脚本
================
用于 P0 阶段测试数据准备

使用方法:
    .venv/bin/python m_flow/tests/fixtures/create_test_user.py
"""

import asyncio
import sys

sys.path.insert(0, ".")


async def create_test_user():
    """创建测试用户"""
    from m_flow.auth.methods.create_user import create_user
    from m_flow.auth.methods.get_user_by_email import get_user_by_email

    TEST_EMAIL = "test@example.com"
    TEST_PASSWORD = "TestPassword123!"

    # 检查用户是否已存在
    existing = await get_user_by_email(TEST_EMAIL)
    if existing:
        print(f"✅ 测试用户已存在: {TEST_EMAIL}")
        return existing

    # 创建新用户
    try:
        user = await create_user(email=TEST_EMAIL, password=TEST_PASSWORD, is_superuser=False, is_verified=True)
        print(f"✅ 测试用户创建成功: {TEST_EMAIL}")
        return user
    except Exception as e:
        print(f"❌ 创建测试用户失败: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(create_test_user())
