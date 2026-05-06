#!/usr/bin/env python3
"""
直接测试User.verify_credentials方法

from app.models.user import User

def test_user_verify():
    """直接测试User.verify_credentials方法"""
    # 测试用户名和密码
    username = "testuser"
    password = "Test123!@#"

    print(f"\n🔍 测试User.verify_credentials方法")
    print(f"   用户名: {username}")
    print(f"   密码: {password}")

    try:
        # 直接调用User.verify_credentials方法
        user = User.verify_credentials(username, password)

        if user:
            print(f"\n✅ 登录成功！")
            print(f"   用户ID: {user.user_id}")
            print(f"   用户名: {user.username}")
            print(f"   角色: {user.role}")
            return True
        else:
            print(f"\n❌ 登录失败！")
            return False
    except Exception as e:
        print(f"\n💥 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
def main():
    """主函数"""
    print("🚀 直接测试User.verify_credentials方法")
    print("=" * 50)

    # 测试登录
    test_user_verify()

    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()
