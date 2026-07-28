#!/usr/bin/env python3
import sqlite3
import hashlib
import base64

db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

def hash_password(password):
    password_hash = hashlib.sha256(password.encode()).digest()
    return base64.b64encode(password_hash).decode()

try:
    conn = sqlite3.connect(db_path, timeout=10)
    cursor = conn.cursor()
    
    new_password = 'test123'
    hashed_password = hash_password(new_password)
    
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, 'wuchenghao15'))
    conn.commit()
    conn.close()
    
    logger.info("Password reset successful!")
    logger.info(f"New hash: {hashed_password}")
    
    conn2 = sqlite3.connect(db_path, timeout=5)
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT password FROM users WHERE username = 'wuchenghao15'")
    row = cursor2.fetchone()
    conn2.close()
    
    if row:
        stored = row[0]
        logger.info(f"Stored hash: {stored}")
        logger.info(f"Match: {stored == hashed_password}")
        
        decoded = base64.b64decode(stored)
        test_hash = hashlib.sha256(new_password.encode()).digest()
        logger.info(f"Decoded matches SHA256: {decoded == test_hash}")
        
except Exception as e:
    logger.info(f"Error: {e}")
    import traceback
    traceback.print_exc()