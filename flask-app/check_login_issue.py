import sqlite3
import hashlib
from werkzeug.security import check_password_hash

# 连接到数据库
db_path = 'app.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查询所有用户信息
print("=== 数据库用户信息 ===")
cursor.execute("SELECT id, username, password, role FROM users")
users = cursor.fetchall()

for user in users:
    user_id, username, password, role = user
    print(f"ID: {user_id}, 用户名: {username}, 密码长度: {len(password)}, 密码开头: {password[:20]}..., 角色: {role}")

# 测试密码验证函数
def verify_password(stored_password, provided_password):
    print(f"\n=== 验证密码 ===")
    print(f"存储密码: {stored_password[:50]}... (长度: {len(stored_password)})")
    print(f"提供密码: {provided_password}")
    
    # 1. 尝试使用werkzeug.security.check_password_hash（支持scrypt哈希）
    print("\n1. 尝试使用werkzeug.security.check_password_hash验证...")
    try:
        result = check_password_hash(stored_password, provided_password)
        print(f"   结果: {'成功' if result else '失败'}")
        if result:
            return True
    except Exception as e:
        print(f"   错误: {e}")
    
    # 2. 尝试使用hex格式验证（update_users.py使用的格式）
    print("\n2. 尝试使用hex格式验证...")
    if len(stored_password) in [64, 96]:
        try:
            salt_hex = stored_password[:32]  # 前32个字符是salt的十六进制表示（16字节）
            hash_hex = stored_password[32:96]  # 后面是hash的十六进制表示（32字节）
            salt = bytes.fromhex(salt_hex)
            stored_hash = bytes.fromhex(hash_hex)
            
            print(f"   提取的salt: {salt_hex} (长度: {len(salt_hex)})")
            print(f"   提取的hash: {hash_hex} (长度: {len(hash_hex)})")
            print(f"   salt字节: {salt} (长度: {len(salt)})")
            
            # 计算提供密码的哈希值
            hashed = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
            print(f"   计算的hash: {hashed.hex()} (长度: {len(hashed)})")
            
            result = hashed == stored_hash
            print(f"   结果: {'成功' if result else '失败'}")
            return result
        except Exception as e:
            print(f"   错误: {e}")
    
    # 3. 尝试使用base64格式验证
    print("\n3. 尝试使用base64格式验证...")
    if '$pbkdf2-sha256$' in stored_password:
        try:
            # 解析pbkdf2格式
            parts = stored_password.split('$')
            if len(parts) == 5:
                iterations = int(parts[2])
                salt = parts[3].encode('utf-8')
                stored_hash = parts[4]
                
                print(f"   迭代次数: {iterations}")
                print(f"   salt: {salt} (长度: {len(salt)})")
                print(f"   存储的hash: {stored_hash}")
                
                # 计算哈希值
                hashed = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, iterations)
                hashed_base64 = hashed.hex()  # 转换为十六进制
                
                print(f"   计算的hash: {hashed_base64}")
                
                result = hashed_base64 == stored_hash
                print(f"   结果: {'成功' if result else '失败'}")
                return result
        except Exception as e:
            print(f"   错误: {e}")
    
    print("\n所有验证方法均失败!")
    return False

# 测试特定用户的密码验证
if users:
    print(f"\n\n=== 测试用户登录 ===")
    username_to_test = input("请输入要测试的用户名 (直接回车测试第一个用户): ")
    
    if not username_to_test:
        # 默认测试第一个用户
        test_user = users[0]
        username_to_test = test_user[1]
    else:
        # 查找指定用户
        test_user = next((user for user in users if user[1] == username_to_test), None)
        if not test_user:
            print(f"未找到用户: {username_to_test}")
            conn.close()
            exit()
    
    user_id, username, stored_password, role = test_user
    password_to_test = input(f"请输入 '{username}' 的密码: ")
    
    if not password_to_test:
        password_to_test = "123456"  # 默认密码
        print(f"使用默认密码: {password_to_test}")
    
    # 进行验证
    result = verify_password(stored_password, password_to_test)
    
    print(f"\n=== 最终验证结果 ===")
    print(f"用户名: {username}")
    print(f"密码: {password_to_test}")
    print(f"验证结果: {'登录成功!' if result else '登录失败!'}")

# 关闭数据库连接
conn.close()
