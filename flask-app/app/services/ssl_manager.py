import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
SSL证书管理服务
负责SSL证书的生成、管理和配置
"""

import os
import ssl
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from typing import Dict, Optional

class SSLManager:
    """SSL证书管理器"""
    
    def __init__(self, ssl_dir: str = "ssl"):
        self.ssl_dir = ssl_dir
        self.cert_path = os.path.join(ssl_dir, "cert.pem")
        self.key_path = os.path.join(ssl_dir, "key.pem")
        self.ca_cert_path = os.path.join(ssl_dir, "ca_cert.pem")
        self.ca_key_path = os.path.join(ssl_dir, "ca_key.pem")
    
    def generate_self_signed_certificate(self, 
                                        common_name: str = "localhost",
                                        days: int = 365,
                                        key_size: int = 2048) -> bool:
        """生成自签名SSL证书"""
        try:
            # 确保目录存在
            os.makedirs(self.ssl_dir, exist_ok=True)
            
            # 生成私钥
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
            
            # 设置证书有效期
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MTSCOS AI Project"),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=days)
            ).add_extension(
                x509.SubjectAlternativeName([x509.DNSName(common_name), x509.DNSName("127.0.0.1")]),
                critical=False,
            ).sign(private_key, hashes.SHA256(), default_backend())
            
            # 保存证书和密钥
            with open(self.key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                ))
            
            with open(self.cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # 设置文件权限
            os.chmod(self.key_path, 0o600)
            os.chmod(self.cert_path, 0o644)
            
            return True
        except Exception as e:
            print(f"生成SSL证书失败: {str(e)}")
            return False
    
    def generate_ca_signed_certificate(self, 
                                       common_name: str = "localhost",
                                       days: int = 365) -> bool:
        """生成CA签名证书"""
        try:
            # 确保目录存在
            os.makedirs(self.ssl_dir, exist_ok=True)
            
            # 如果CA证书不存在,先创建CA
            if not os.path.exists(self.ca_key_path) or not os.path.exists(self.ca_cert_path):
                self._generate_ca_certificate()
            
            # 加载CA证书和密钥
            with open(self.ca_key_path, "rb") as f:
                ca_private_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
            
            with open(self.ca_cert_path, "rb") as f:
                ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            # 生成服务器私钥
            server_private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # 创建证书签名请求
            csr = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MTSCOS AI Project"),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ])).add_extension(
                x509.SubjectAlternativeName([x509.DNSName(common_name)]),
                critical=False,
            ).sign(server_private_key, hashes.SHA256(), default_backend())
            
            # 用CA签署证书
            cert = x509.CertificateBuilder().subject_name(
                csr.subject
            ).issuer_name(
                ca_cert.subject
            ).public_key(
                csr.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=days)
            ).add_extension(
                x509.SubjectAlternativeName([x509.DNSName(common_name), x509.DNSName("127.0.0.1")]),
                critical=False,
            ).sign(ca_private_key, hashes.SHA256(), default_backend())
            
            # 保存证书和密钥
            with open(self.key_path, "wb") as f:
                f.write(server_private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                ))
            
            with open(self.cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            os.chmod(self.key_path, 0o600)
            os.chmod(self.cert_path, 0o644)
            
            return True
        except Exception as e:
            print(f"生成CA签名证书失败: {str(e)}")
            return False
    
    def _generate_ca_certificate(self):
        """生成CA根证书"""
        ca_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MTSCOS AI CA"),
            x509.NameAttribute(NameOID.COMMON_NAME, "MTSCOS AI Root CA"),
        ])
        
        ca_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            ca_private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=3650)
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True,
        ).sign(ca_private_key, hashes.SHA256(), default_backend())
        
        with open(self.ca_key_path, "wb") as f:
            f.write(ca_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))
        
        with open(self.ca_cert_path, "wb") as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
        
        os.chmod(self.ca_key_path, 0o600)
        os.chmod(self.ca_cert_path, 0o644)
    
    def check_certificate_validity(self) -> Dict:
        """检查证书有效性"""
        try:
            if not os.path.exists(self.cert_path) or not os.path.exists(self.key_path):
                return {
                    'valid': False,
                    'message': '证书文件不存在',
                    'expired': False,
                    'days_remaining': 0
                }
            
            with open(self.cert_path, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())
            
            now = datetime.utcnow()
            not_before = cert.not_valid_before.replace(tzinfo=None)
            not_after = cert.not_valid_after.replace(tzinfo=None)
            
            is_valid = not_before <= now <= not_after
            days_remaining = (not_after - now).days
            
            return {
                'valid': is_valid,
                'message': '证书有效' if is_valid else ('证书尚未生效' if now < not_before else '证书已过期'),
                'expired': now > not_after,
                'days_remaining': days_remaining,
                'not_before': not_before.strftime('%Y-%m-%d %H:%M:%S'),
                'not_after': not_after.strftime('%Y-%m-%d %H:%M:%S'),
                'issuer': cert.issuer.rfc4514_string(),
                'subject': cert.subject.rfc4514_string()
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f'检查证书失败: {str(e)}',
                'expired': True,
                'days_remaining': 0
            }
    
    def get_ssl_context(self) -> Optional[ssl.SSLContext]:
        """获取SSL上下文"""
        try:
            if not os.path.exists(self.cert_path) or not os.path.exists(self.key_path):
                return None
            
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile=self.cert_path, keyfile=self.key_path)
            
            # 安全配置
            context.set_ciphers('ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256')
            context.options |= ssl.OP_NO_SSLv3
            context.options |= ssl.OP_NO_TLSv1
            context.options |= ssl.OP_NO_TLSv1_1
            context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE
            
            return context
        except Exception as e:
            print(f"创建SSL上下文失败: {str(e)}")
            return None
    
    def renew_certificate(self, days: int = 365) -> bool:
        """续期证书"""
        return self.generate_self_signed_certificate(days=days)
    
    def ensure_certificate(self):
        """确保证书存在,如果不存在则生成"""
        validity = self.check_certificate_validity()
        if not validity['valid'] or validity['days_remaining'] < 30:
            print(f"证书无效或即将过期,生成新证书...")
            return self.generate_self_signed_certificate()
        return True

# 全局实例
ssl_manager = None

def get_ssl_manager():
    """获取SSL管理器实例"""
    global ssl_manager
    if ssl_manager is None:
        ssl_manager = SSLManager()
    return ssl_manager

if __name__ == "__main__":
    manager = SSLManager()
    
    # 检查证书有效性
    validity = manager.check_certificate_validity()
    print("证书状态:", validity)
    
    # 如果证书无效,生成新证书
    if not validity['valid']:
        print("生成新的自签名证书...")
        manager.generate_self_signed_certificate()
        validity = manager.check_certificate_validity()
        logger.info("新证书状态:", validity)
