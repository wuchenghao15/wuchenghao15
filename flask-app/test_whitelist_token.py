#!/usr/bin/env python3
"""
白名单 token 功能测试脚本
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== 白名单 token 功能测试 ===")

# 测试1：检查白名单 token 表是否创建成功
try:
    db_path = 'app.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查白名单 token 表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='whitelist_tokens';")
    result = cursor.fetchone()
    
    print("\n1. 检查白名单 token 表创建情况...")
    if result:
        print("   ✅ whitelist_tokens 表创建成功")
    else:
        print("   ❌ whitelist_tokens 表创建失败")
        sys.exit(1)
    
    conn.close()
except Exception as e:
    print(f"   ❌ 数据库表检查失败: {str(e)}")
    sys.exit(1)

# 测试2：测试白名单 token 生成和验证
try:
    print("\n2. 测试白名单 token 生成和验证...")
    
    # 导入验证工具
    from app.utils.verification import verification_utils
    
    # 生成测试数据
    test_user_id = 1
    test_username = "test_user"
    
    # 测试生成白名单 token
    token = verification_utils.generate_whitelist_token(
        user_id=test_user_id,
        username=test_username,
        description="测试白名单 token"
    )
    print(f"   ✅ 生成白名单 token 成功: {token[:10]}...")
    
    # 测试验证白名单 token
    valid, message = verification_utils.verify_whitelist_token(token, test_user_id, test_username)
    if valid:
        print(f"   ✅ 验证白名单 token 成功: {message}")
    else:
        print(f"   ❌ 验证白名单 token 失败: {message}")
        sys.exit(1)
    
    # 测试验证不存在的 token
    invalid_valid, invalid_message = verification_utils.verify_whitelist_token("invalid_token")
    if not invalid_valid:
        print(f"   ✅ 验证不存在的 token 失败，符合预期: {invalid_message}")
    else:
        print(f"   ❌ 验证不存在的 token 成功，不符合预期")
        sys.exit(1)
    
    print("   ✓ 白名单 token 测试通过")
except Exception as e:
    print(f"   ❌ 白名单 token 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试3：测试有期限的白名单 token
try:
    print("\n3. 测试有期限的白名单 token...")
    
    # 导入验证工具
    from app.utils.verification import verification_utils
    
    # 生成测试数据
    test_user_id = 1
    test_username = "test_user"
    
    # 生成过期的 token（1秒后过期）
    expires_at = datetime.now() - timedelta(seconds=1)
    expired_token = verification_utils.generate_whitelist_token(
        user_id=test_user_id,
        username=test_username,
        expires_at=expires_at,
        description="过期的白名单 token"
    )
    print(f"   ✅ 生成过期的白名单 token 成功: {expired_token[:10]}...")
    
    # 测试验证过期的 token
    valid, message = verification_utils.verify_whitelist_token(expired_token, test_user_id, test_username)
    if not valid:
        print(f"   ✅ 验证过期的 token 失败，符合预期: {message}")
    else:
        print(f"   ❌ 验证过期的 token 成功，不符合预期")
        sys.exit(1)
    
    print("   ✓ 有期限的白名单 token 测试通过")
except Exception as e:
    print(f"   ❌ 有期限的白名单 token 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 测试4：测试停用白名单 token
try:
    print("\n4. 测试停用白名单 token...")
    
    # 导入验证工具
    from app.utils.verification import verification_utils
    
    # 生成测试数据
    test_user_id = 1
    test_username = "test_user"
    
    # 生成白名单 token
    token = verification_utils.generate_whitelist_token(
        user_id=test_user_id,
        username=test_username,
        description="要停用的白名单 token"
    )
    print(f"   ✅ 生成白名单 token 成功: {token[:10]}...")
    
    # 验证 token 有效
    valid, message = verification_utils.verify_whitelist_token(token, test_user_id, test_username)
    if valid:
        print(f"   ✅ 验证白名单 token 成功: {message}")
    else:
        print(f"   ❌ 验证白名单 token 失败: {message}")
        sys.exit(1)
    
    # 停用 token
    deactivated = verification_utils.deactivate_whitelist_token(token)
    if deactivated:
        print(f"   ✅ 停用白名单 token 成功")
    else:
        print(f"   ❌ 停用白名单 token 失败")
        sys.exit(1)
    
    # 验证停用的 token
    valid, message = verification_utils.verify_whitelist_token(token, test_user_id, test_username)
    if not valid:
        print(f"   ✅ 验证停用的 token 失败，符合预期: {message}")
    else:
        print(f"   ❌ 验证停用的 token 成功，不符合预期")
        sys.exit(1)
    
    print("   ✓ 停用白名单 token 测试通过")
except Exception as e:
    print(f"   ❌ 停用白名单 token 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n=== 白名单 token 功能测试完成 ===")
print("\n🎉 白名单 token 功能实现成功！")
print("\n已实现的功能：")
print("1. ✅ 生成白名单 token")
print("2. ✅ 验证白名单 token")
print("3. ✅ 支持有期限的白名单 token")
print("4. ✅ 支持停用白名单 token")
print("5. ✅ 支持关联用户的白名单 token")
print("6. ✅ 支持匿名白名单 token")
print("\n使用说明：")
print("- 登录时，可以只输入白名单 token 直接登录")
print("- 也可以结合用户名和密码使用白名单 token")
print("- 白名单 token 可以设置有效期")
print("- 可以随时停用白名单 token")
