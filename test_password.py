#!/usr/bin/env python3
import sqlite3
import hashlib
import base64
import sys

db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

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
        
        if stored_password == provided_password:
            return True
            
    except Exception as e:
        print(f"Verify error: {e}")
    
    return stored_password == provided_password

print("Step 1: Connecting to database...")
try:
    conn = sqlite3.connect(db_path, timeout=5)
    cursor = conn.cursor()
    print("Connected successfully!")
    
    print("\nStep 2: Querying user...")
    cursor.execute("SELECT username, password, role FROM users WHERE username = 'wuchenghao15'")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        username, stored_password, role = row
        print(f"User found: {username}")
        print(f"Role: {role}")
        print(f"Password length: {len(stored_password)}")
        print(f"Password prefix: {stored_password[:30]}")
        
        print("\nStep 3: Testing password verification...")
        test_password = 'test123'
        
        try:
            decoded = base64.b64decode(stored_password)
            print(f"Base64 decoded length: {len(decoded)} bytes")
            
            test_hash = hashlib.sha256(test_password.encode()).digest()
            print(f"Test SHA256 hash: {test_hash.hex()}")
            print(f"Stored hash: {decoded.hex()}")
            print(f"Direct match: {decoded == test_hash}")
        except Exception as e:
            print(f"Base64 decode failed: {e}")
        
        result = verify_password(stored_password, test_password)
        print(f"\nPassword verification result: {result}")
        
        if not result:
            print("\nTrying other formats...")
            print(f"Starts with pbkdf2: {stored_password.startswith('pbkdf2:')}")
            print(f"Starts with $2b$: {stored_password.startswith('$2b$')}")
            print(f"Starts with $2a$: {stored_password.startswith('$2a$')}")
            
    else:
        print("User not found!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()