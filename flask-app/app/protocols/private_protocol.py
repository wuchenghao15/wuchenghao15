#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
私有数据交互协议模块
提供安全、加密的私有数据传输支持
"""

import json
import time
import zlib
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from app.utils.logging import logger


class PrivateDataProtocol:
    """私有数据交互协议实现类"""
    
    PROTOCOL_VERSION = "1.0.0"
    PROTOCOL_NAME = "MTSCOS-Private"
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        # 加密配置
        if encryption_key:
            self.fernet = Fernet(encryption_key)
        else:
            self.fernet = Fernet(Fernet.generate_key())
        
        # 生成RSA密钥对
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        
        # 统计信息
        self.stats = {
            'total_messages': 0,
            'encrypted_messages': 0,
            'decrypted_messages': 0,
            'compressed_messages': 0,
            'verified_messages': 0,
            'errors': 0
        }
        
        # 消息ID计数器
        self.message_id_counter = 0
        
        logger.info(f"私有数据协议初始化完成，版本: {self.PROTOCOL_VERSION}")
    
    def _generate_message_id(self) -> str:
        """生成唯一消息ID"""
        self.message_id_counter += 1
        timestamp = int(time.time() * 1000)
        return f"msg_{timestamp}_{self.message_id_counter:06d}"
    
    def _compress_data(self, data: bytes) -> bytes:
        """压缩数据"""
        return zlib.compress(data, level=zlib.Z_BEST_COMPRESSION)
    
    def _decompress_data(self, compressed_data: bytes) -> bytes:
        """解压数据"""
        return zlib.decompress(compressed_data)
    
    def _sign_message(self, data: bytes) -> bytes:
        """使用私钥签名数据"""
        signature = self.private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    
    def _verify_signature(self, data: bytes, signature: bytes, public_key) -> bool:
        """验证签名"""
        try:
            public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def encrypt_data(self, data: Dict[str, Any]) -> bytes:
        """加密数据"""
        try:
            json_str = json.dumps(data, ensure_ascii=False)
            data_bytes = json_str.encode('utf-8')
            encrypted = self.fernet.encrypt(data_bytes)
            self.stats['encrypted_messages'] += 1
            return encrypted
        except Exception as e:
            logger.error(f"数据加密失败: {str(e)}")
            self.stats['errors'] += 1
            raise
    
    def decrypt_data(self, encrypted_data: bytes) -> Dict[str, Any]:
        """解密数据"""
        try:
            decrypted = self.fernet.decrypt(encrypted_data)
            data = json.loads(decrypted.decode('utf-8'))
            self.stats['decrypted_messages'] += 1
            return data
        except Exception as e:
            logger.error(f"数据解密失败: {str(e)}")
            self.stats['errors'] += 1
            raise
    
    def create_message(self, payload: Dict[str, Any], 
                       compression: bool = True, 
                       sign: bool = True) -> Dict[str, Any]:
        """创建标准化消息"""
        message_id = self._generate_message_id()
        timestamp = datetime.utcnow().isoformat()
        
        message = {
            'protocol': self.PROTOCOL_NAME,
            'version': self.PROTOCOL_VERSION,
            'message_id': message_id,
            'timestamp': timestamp,
            'compression': compression,
            'signed': sign,
            'payload': payload
        }
        
        if compression:
            payload_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            compressed_payload = self._compress_data(payload_bytes)
            message['payload'] = compressed_payload.hex()
            self.stats['compressed_messages'] += 1
        
        if sign:
            message_str = json.dumps(message, ensure_ascii=False, sort_keys=True)
            signature = self._sign_message(message_str.encode('utf-8'))
            message['signature'] = signature.hex()
        
        self.stats['total_messages'] += 1
        return message
    
    def parse_message(self, message: Dict[str, Any], 
                     public_key = None) -> Optional[Dict[str, Any]]:
        """解析并验证消息"""
        try:
            # 验证协议版本
            if message.get('protocol') != self.PROTOCOL_NAME:
                logger.error(f"协议不匹配: {message.get('protocol')}")
                return None
            
            # 验证签名
            if message.get('signed') and public_key:
                message_copy = message.copy()
                signature_hex = message_copy.pop('signature', '')
                
                if not signature_hex:
                    logger.error("消息缺少签名")
                    return None
                
                message_str = json.dumps(message_copy, ensure_ascii=False, sort_keys=True)
                signature = bytes.fromhex(signature_hex)
                
                if not self._verify_signature(message_str.encode('utf-8'), signature, public_key):
                    logger.error("签名验证失败")
                    return None
                
                self.stats['verified_messages'] += 1
            
            # 解压数据
            payload = message.get('payload')
            if message.get('compression') and isinstance(payload, str):
                compressed_data = bytes.fromhex(payload)
                decompressed = self._decompress_data(compressed_data)
                payload = json.loads(decompressed.decode('utf-8'))
            
            return {
                'message_id': message.get('message_id'),
                'timestamp': message.get('timestamp'),
                'payload': payload,
                'version': message.get('version')
            }
        except Exception as e:
            logger.error(f"消息解析失败: {str(e)}")
            self.stats['errors'] += 1
            return None
    
    def export_public_key(self) -> bytes:
        """导出公钥"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    def import_public_key(self, public_key_bytes: bytes):
        """导入公钥"""
        return serialization.load_pem_public_key(public_key_bytes)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_messages': 0,
            'encrypted_messages': 0,
            'decrypted_messages': 0,
            'compressed_messages': 0,
            'verified_messages': 0,
            'errors': 0
        }
    
    def validate_version(self, version: str) -> bool:
        """验证协议版本兼容性"""
        current_parts = self.PROTOCOL_VERSION.split('.')
        target_parts = version.split('.')
        
        # 主版本号必须相同
        if current_parts[0] != target_parts[0]:
            return False
        return True


class SecureChannel:
    """安全通道封装类"""
    
    def __init__(self, protocol: Optional[PrivateDataProtocol] = None):
        self.protocol = protocol or PrivateDataProtocol()
        self.peer_public_key = None
        self.connected = False
    
    def connect(self, peer_public_key: Optional[bytes] = None):
        """建立安全连接"""
        if peer_public_key:
            self.peer_public_key = self.protocol.import_public_key(peer_public_key)
        self.connected = True
        logger.info("安全通道已建立")
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        self.peer_public_key = None
        logger.info("安全通道已断开")
    
    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送安全消息"""
        if not self.connected:
            logger.error("安全通道未建立")
            return None
        
        return self.protocol.create_message(
            data, 
            compression=True, 
            sign=True
        )
    
    def receive(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """接收并解析安全消息"""
        return self.protocol.parse_message(message, self.peer_public_key)
    
    def get_protocol_version(self) -> str:
        """获取协议版本"""
        return self.protocol.PROTOCOL_VERSION
    
    def get_public_key(self) -> bytes:
        """获取公钥"""
        return self.protocol.export_public_key()