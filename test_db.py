#!/usr/bin/env python3
import sqlite3
import hashlib
import base64
import os

test_db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/test_login.db'

if os.path.exists(test_db_path):
    os.remove(test_db_path)

conn = sqlite3.connect(test_db_path)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT
    )
''')

def hash_password(password):
    password_hash = hashlib.sha256(password.encode()).digest()
    return base64.b64encode(password_hash).decode()

cursor.execute('''
    INSERT INTO users (username, password, role, email)
    VALUES (?, ?, ?, ?)
''', ('testuser', hash_password('test123'), 'admin', 'test@test.com'))

conn.commit()
conn.close()

print(f"Test database created at: {test_db_path}")

conn2 = sqlite3.connect(test_db_path)
cursor2 = conn2.cursor()
cursor2.execute('SELECT * FROM users')
row = cursor2.fetchone()
conn2.close()

if row:
    print(f"User created: {row[1]}")
    print(f"Password hash: {row[2]}")
    
    decoded = base64.b64decode(row[2])
    test_hash = hashlib.sha256('test123'.encode()).digest()
    print(f"Password verification: {decoded == test_hash}")