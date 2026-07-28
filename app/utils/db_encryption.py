#!/usr/bin/env python3
import os
import hashlib
import json
from datetime import datetime

try:
    from cryptography.fernet import Fernet
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

class DatabaseEncryption:
    def __init__(self):
        self.encryption_enabled = True
        self.key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'encryption_key.key')
        self.key = self._load_or_generate_key()
        if HAS_CRYPTOGRAPHY:
            self.fernet = Fernet(self.key)
    
    def _load_or_generate_key(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            if HAS_CRYPTOGRAPHY:
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                return key
            else:
                return hashlib.sha256(b'mtscos_default_key').digest()[:32] + b'=' * 16
    
    def encrypt_data(self, data):
        if not self.encryption_enabled or not HAS_CRYPTOGRAPHY:
            return data
        
        try:
            if isinstance(data, dict) or isinstance(data, list):
                data_str = json.dumps(data, ensure_ascii=False)
                return self.fernet.encrypt(data_str.encode()).decode()
            elif isinstance(data, str):
                return self.fernet.encrypt(data.encode()).decode()
            else:
                return data
        except Exception as e:
            return data
    
    def decrypt_data(self, data):
        if not self.encryption_enabled or not HAS_CRYPTOGRAPHY:
            return data
        
        try:
            if isinstance(data, str) and data.startswith('gAAAAA'):
                decrypted = self.fernet.decrypt(data.encode()).decode()
                try:
                    return json.loads(decrypted)
                except json.JSONDecodeError:
                    return decrypted
            else:
                return data
        except Exception as e:
            return data
    
    def encrypt_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, hashed_password):
        return hashlib.sha256(password.encode()).hexdigest() == hashed_password
    
    def generate_session_token(self, user_id):
        token_data = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'nonce': os.urandom(16).hex()
        }
        return self.encrypt_data(token_data)
    
    def validate_session_token(self, token):
        try:
            data = self.decrypt_data(token)
            if isinstance(data, dict) and 'user_id' in data and 'timestamp' in data:
                token_time = datetime.fromisoformat(data['timestamp'])
                if (datetime.now() - token_time).total_seconds() < 7200:
                    return data['user_id']
            return None
        except Exception as e:
            return None
    
    def encrypt_file(self, input_path, output_path=None):
        if not HAS_CRYPTOGRAPHY:
            return False
        
        try:
            if output_path is None:
                output_path = input_path + '.encrypted'
            
            with open(input_path, 'rb') as f:
                data = f.read()
            
            encrypted = self.fernet.encrypt(data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted)
            
            return True
        except Exception as e:
            return False
    
    def decrypt_file(self, input_path, output_path=None):
        if not HAS_CRYPTOGRAPHY:
            return False
        
        try:
            if output_path is None:
                output_path = input_path.replace('.encrypted', '')
            
            with open(input_path, 'rb') as f:
                data = f.read()
            
            decrypted = self.fernet.decrypt(data)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted)
            
            return True
        except Exception as e:
            return False

db_encryption = DatabaseEncryption()