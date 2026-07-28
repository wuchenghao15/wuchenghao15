#!/usr/bin/env python3
import sqlite3
import hashlib
import base64
import os

DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/split_databases/auth.db'

def hash_password(password):
    password_hash = hashlib.sha256(password.encode()).digest()
    return base64.b64encode(password_hash).decode()

def update_password(username, new_password):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        cursor = conn.cursor()
        
        hashed_password = hash_password(new_password)
        
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", 
                      (hashed_password, username))
        
        if cursor.rowcount > 0:
            conn.commit()
            logger.info(f"✅ 用户 {username} 的密码已更新")
            logger.info(f"   新密码哈希: {hashed_password}")
        else:
            logger.info(f"❌ 用户 {username} 不存在")
        
        conn.close()
        return cursor.rowcount > 0
    except Exception as e:
        logger.info(f"❌ 错误: {e}")
        return False

def verify_password(stored_password, provided_password):
    try:
        stored_bytes = base64.b64decode(stored_password)
        if len(stored_bytes) == 32:
            provided_hash = hashlib.sha256(provided_password.encode()).digest()
            return stored_bytes == provided_hash
    except Exception:
        pass
    return False

def test_login(username, password):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            stored_password = result[0]
            is_valid = verify_password(stored_password, password)
            if is_valid:
                logger.info(f"✅ 密码验证成功: {username}")
                return True
            else:
                logger.info(f"❌ 密码验证失败: {username}")
                logger.info(f"   存储的哈希: {stored_password}")
                logger.info(f"   输入密码的哈希: {hash_password(password)}")
                return False
        else:
            logger.info(f"❌ 用户 {username} 不存在")
            return False
    except Exception as e:
        logger.info(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        new_password = sys.argv[2]
    else:
        username = os.environ.get('RESET_PASSWORD_USERNAME', '')
        new_password = os.environ.get('RESET_PASSWORD_NEW_PASSWORD', '')
    
    if not username or not new_password:
        logger.info("用法: python reset_password_v2.py <username> <new_password>")
        logger.info("或设置环境变量: RESET_PASSWORD_USERNAME 和 RESET_PASSWORD_NEW_PASSWORD")
        sys.exit(1)
    
    logger.info(f"\n=== 更新用户 {username} 的密码 ===")
    update_password(username, new_password)
    
    logger.info(f"\n=== 测试新密码 ===")
    test_login(username, new_password)