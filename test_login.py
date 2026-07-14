#!/usr/bin/env python3
import sqlite3
import hashlib
import base64

db_path = 'app.db'

def verify_password(stored_password, provided_password):
    try:
        if stored_password.startswith('pbkdf2:'):
            parts = stored_password.split('$')
            if len(parts) == 3:
                algo_parts = parts[0].split(':')
                if len(algo_parts) >= 3:
                    algo = algo_parts[1]
                    iterations = int(algo_parts[2])
                    salt = parts[1].encode()
                    stored_hash = parts[2].encode()
                    provided_hash = hashlib.pbkdf2_hmac(algo, provided_password.encode(), salt, iterations)
                    return stored_hash == base64.b64encode(provided_hash).decode()
            return False
        
        if stored_password.startswith('$2b$') or stored_password.startswith('$2a$') or stored_password.startswith('$2y$'):
            try:
                import bcrypt
                return bcrypt.checkpw(provided_password.encode(), stored_password.encode())
            except ImportError:
                return False
        
        try:
            stored_bytes = base64.b64decode(stored_password)
            if len(stored_bytes) == 32:
                provided_hash = hashlib.sha256(provided_password.encode()).digest()
                return stored_bytes == provided_hash
            if len(stored_bytes) > 32:
                salt = stored_bytes[:16]
                stored_hash = stored_bytes[16:]
                provided_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
                return stored_hash == provided_hash
        except Exception:
            pass
        
        return stored_password == provided_password
    except Exception as e:
        print(f"验证错误: {e}")
        return False

print("=== 测试密码验证 ===")
try:
    conn = sqlite3.connect(db_path, timeout=5)
    cursor = conn.cursor()
    
    cursor.execute("SELECT username, password, role FROM users WHERE username = 'wuchenghao15'")
    result = cursor.fetchone()
    
    if result:
        username, stored_password, role = result
        print(f"用户名: {username}")
        print(f"角色: {role}")
        print(f"存储的密码: {stored_password[:50]}...")
        
        try:
            decoded = base64.b64decode(stored_password)
            print(f"解码后长度: {len(decoded)} bytes")
        except:
            print("不是base64编码")
        
        test_password = 'test123'
        result = verify_password(stored_password, test_password)
        print(f"密码验证结果: {result}")
        
        if not result:
            test_hash = hashlib.sha256(test_password.encode()).digest()
            print(f"测试密码的SHA256: {test_hash.hex()}")
            try:
                decoded = base64.b64decode(stored_password)
                print(f"存储的哈希: {decoded.hex()}")
            except:
                pass
    
    conn.close()
    print("\n数据库连接正常")
except Exception as e:
    print(f"数据库错误: {e}")