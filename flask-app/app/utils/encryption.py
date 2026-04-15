# 简化的加密工具类
import secrets
import hashlib
from cryptography.fernet import Fernet

class EncryptionUtils:
    """简化的加密工具类"""
    
    def __init__(self):
        """初始化加密工具"""
        # 使用内存中的密钥，不再依赖文件系统
        self.key = self._generate_key()
        self.cipher_suite = Fernet(self.key)
    
    def _generate_key(self):
        """生成加密密钥"""
        return Fernet.generate_key()
    
    def encrypt(self, data):
        """加密数据"""
        if not isinstance(data, bytes):
            data = str(data).encode()
        return self.cipher_suite.encrypt(data).decode()
    
    def decrypt(self, encrypted_data):
        """解密数据"""
        if not isinstance(encrypted_data, bytes):
            encrypted_data = encrypted_data.encode()
        return self.cipher_suite.decrypt(encrypted_data).decode()
    
    def hash_data(self, data):
        """哈希数据"""
        if not isinstance(data, bytes):
            data = str(data).encode()
        return hashlib.sha256(data).hexdigest()
    
    def generate_secure_token(self, length=32):
        """生成安全令牌"""
        return secrets.token_urlsafe(length)

# 创建单例实例
encryption_utils = EncryptionUtils()