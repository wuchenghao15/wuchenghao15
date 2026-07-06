#!/usr/bin/env python3
import sqlite3
import hashlib
import base64
import os

db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

def hash_password(password):
    password_hash = hashlib.sha256(password.encode()).digest()
    return base64.b64encode(password_hash).decode()

def main():
    try:
        conn = sqlite3.connect(db_path, timeout=15)
        cursor = conn.cursor()
        
        new_password = 'test123'
        hashed_password = hash_password(new_password)
        
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, 'wuchenghao15'))
        conn.commit()
        
        cursor.execute("SELECT password FROM users WHERE username = ?", ('wuchenghao15',))
        row = cursor.fetchone()
        
        if row:
            stored = row[0]
            print(f"Password updated successfully!")
            print(f"New hash: {stored}")
            
            decoded = base64.b64decode(stored)
            test_hash = hashlib.sha256(new_password.encode()).digest()
            print(f"Verification: {decoded == test_hash}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()