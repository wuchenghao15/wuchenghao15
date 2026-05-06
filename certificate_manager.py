#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用户证书管理系统 - 数字证书和指纹证书"""

import os
import sqlite3
import logging
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# 添加flask-app到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask-app/app'))
from data_storage_manager import storage_manager

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('certificate_manager')

class CertificateManager:
    def __init__(self):
        self.db_path = 'app.db'
        self.init_certificate_database()
    
    def init_certificate_database(self):
        """初始化证书数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tables = [
            '''CREATE TABLE IF NOT EXISTS user_certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                certificate_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                certificate_type TEXT,
                certificate_data TEXT NOT NULL,
                fingerprint TEXT UNIQUE,
                issuer TEXT,
                valid_from TEXT,
                valid_to TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS device_fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                device_id TEXT,
                device_name TEXT,
                os TEXT,
                browser TEXT,
                ip_address TEXT,
                fingerprint_hash TEXT UNIQUE NOT NULL,
                last_used TEXT,
                trusted INTEGER DEFAULT 1,
                created_at TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS certificate_revocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                certificate_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                revocation_reason TEXT,
                revoked_at TEXT,
                revoked_by TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS certificate_usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                certificate_id TEXT,
                user_id TEXT,
                action TEXT,
                timestamp TEXT,
                ip_address TEXT,
                success INTEGER
            )'''
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        conn.commit()
        conn.close()
        logger.info("证书数据库初始化完成")
    
    def generate_certificate_id(self) -> str:
        """生成证书ID"""
        timestamp = int(time.time() * 1000)
        random_part = secrets.randbits(96)
        return f"CERT{timestamp:x}{random_part:x}"
    
    def generate_fingerprint(self, device_info: Dict) -> str:
        """生成设备指纹 - 使用字符串格式化替代JSON"""
        # 使用排序后的键值对生成稳定的指纹字符串
        fingerprint_str = str(sorted(device_info.items()))
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    def generate_certificate(self, user_id: str, certificate_type: str = 'digital') -> Dict:
        """生成数字证书"""
        certificate_id = self.generate_certificate_id()
        
        certificate_data = {
            'version': '1.0',
            'certificate_id': certificate_id,
            'user_id': user_id,
            'type': certificate_type,
            'issued_by': 'MTSCOS Certificate Authority',
            'issued_at': datetime.now().isoformat(),
            'valid_from': datetime.now().isoformat(),
            'valid_to': (datetime.now() + timedelta(days=365)).isoformat(),
            'serial_number': secrets.token_hex(16),
            'public_key': self.generate_public_key(),
            'signature': self.generate_signature(certificate_id)
        }
        
        fingerprint = self.generate_certificate_fingerprint(certificate_data)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 使用统一存储管理器存储证书数据
        storage_manager.store_certificate(
            certificate_id, int(user_id), certificate_type,
            str(certificate_data), fingerprint,
            'MTSCOS Certificate Authority',
            certificate_data['valid_from'],
            certificate_data['valid_to'],
            'active'
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_certificates
            (certificate_id, user_id, certificate_type, certificate_data, 
             fingerprint, issuer, valid_from, valid_to, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            certificate_id,
            user_id,
            certificate_type,
            str(certificate_data),
            fingerprint,
            'MTSCOS Certificate Authority',
            certificate_data['valid_from'],
            certificate_data['valid_to'],
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return certificate_data
    
    def generate_public_key(self) -> str:
        """生成公钥"""
        return secrets.token_hex(64)
    
    def generate_signature(self, certificate_id: str) -> str:
        """生成数字签名"""
        signature_data = f"{certificate_id}{int(time.time())}"
        return hashlib.sha512(signature_data.encode()).hexdigest()
    
    def generate_certificate_fingerprint(self, certificate_data: Dict) -> str:
        """生成证书指纹"""
        data_str = f"{certificate_data['certificate_id']}{certificate_data['user_id']}{certificate_data['serial_number']}"
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def register_device_fingerprint(self, user_id: str, device_info: Dict) -> Dict:
        """注册设备指纹"""
        fingerprint_hash = self.generate_fingerprint(device_info)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            fingerprint_id = f"FP{int(time.time() * 1000)}{secrets.randbits(32):x}"
            
            cursor.execute('''
                INSERT INTO device_fingerprints
                (fingerprint_id, user_id, device_id, device_name, os, browser, 
                 ip_address, fingerprint_hash, last_used, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fingerprint_id,
                user_id,
                device_info.get('device_id', ''),
                device_info.get('device_name', 'Unknown'),
                device_info.get('os', ''),
                device_info.get('browser', ''),
                device_info.get('ip_address', ''),
                fingerprint_hash,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            result = {'success': True, 'fingerprint_id': fingerprint_id, 'fingerprint_hash': fingerprint_hash}
        
        except sqlite3.IntegrityError:
            cursor.execute('''
                UPDATE device_fingerprints 
                SET last_used = ?, trusted = 1 
                WHERE fingerprint_hash = ?
            ''', (datetime.now().isoformat(), fingerprint_hash))
            conn.commit()
            
            cursor.execute('SELECT fingerprint_id FROM device_fingerprints WHERE fingerprint_hash = ?', (fingerprint_hash,))
            fingerprint_id = cursor.fetchone()[0]
            result = {'success': True, 'fingerprint_id': fingerprint_id, 'fingerprint_hash': fingerprint_hash, 'message': '设备已存在，已更新'}
        
        finally:
            conn.close()
        
        return result
    
    def validate_certificate(self, certificate_id: str, user_id: str = None) -> Dict:
        """验证数字证书"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT certificate_data, status, valid_to FROM user_certificates WHERE certificate_id = ?'
        params = [certificate_id]
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        conn.close()
        
        if not result:
            return {'valid': False, 'reason': 'certificate_not_found'}
        
        certificate_data, status, valid_to = result
        
        if status != 'active':
            return {'valid': False, 'reason': 'certificate_inactive'}
        
        if datetime.now() > datetime.fromisoformat(valid_to):
            return {'valid': False, 'reason': 'certificate_expired'}
        
        cert_data = eval(certificate_data)
        
        # 验证签名
        expected_signature = self.generate_signature(certificate_id)
        if cert_data.get('signature') != expected_signature:
            return {'valid': False, 'reason': 'invalid_signature'}
        
        return {'valid': True, 'certificate': cert_data}
    
    def validate_fingerprint(self, user_id: str, fingerprint_hash: str) -> Dict:
        """验证设备指纹"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fingerprint_id, device_name, trusted, last_used 
            FROM device_fingerprints 
            WHERE user_id = ? AND fingerprint_hash = ?
        ''', (user_id, fingerprint_hash))
        
        result = cursor.fetchone()
        
        conn.close()
        
        if not result:
            return {'valid': False, 'reason': 'fingerprint_not_found', 'trusted': False}
        
        fingerprint_id, device_name, trusted, last_used = result
        
        if trusted != 1:
            return {'valid': False, 'reason': 'fingerprint_not_trusted', 'trusted': False, 'device_name': device_name}
        
        return {'valid': True, 'trusted': True, 'device_name': device_name, 'fingerprint_id': fingerprint_id}
    
    def revoke_certificate(self, certificate_id: str, user_id: str, reason: str = 'user_request'):
        """吊销证书"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_certificates SET status = 'revoked' WHERE certificate_id = ? AND user_id = ?
        ''', (certificate_id, user_id))
        
        cursor.execute('''
            INSERT INTO certificate_revocations
            (certificate_id, user_id, revocation_reason, revoked_at, revoked_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (certificate_id, user_id, reason, datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        return True
    
    def log_certificate_usage(self, certificate_id: str, user_id: str, action: str, ip_address: str, success: bool):
        """记录证书使用日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO certificate_usage_logs
            (certificate_id, user_id, action, timestamp, ip_address, success)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (certificate_id, user_id, action, datetime.now().isoformat(), ip_address, 1 if success else 0))
        
        conn.commit()
        conn.close()
    
    def get_user_certificates(self, user_id: str) -> List:
        """获取用户证书列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT certificate_id, certificate_type, valid_to, status 
            FROM user_certificates WHERE user_id = ?
        ''', (user_id,))
        
        certificates = []
        for row in cursor.fetchall():
            certificates.append({
                'certificate_id': row[0],
                'type': row[1],
                'valid_to': row[2],
                'status': row[3]
            })
        
        conn.close()
        return certificates
    
    def get_user_fingerprints(self, user_id: str) -> List:
        """获取用户设备指纹列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fingerprint_id, device_name, os, browser, trusted, last_used 
            FROM device_fingerprints WHERE user_id = ?
        ''', (user_id,))
        
        fingerprints = []
        for row in cursor.fetchall():
            fingerprints.append({
                'fingerprint_id': row[0],
                'device_name': row[1],
                'os': row[2],
                'browser': row[3],
                'trusted': bool(row[4]),
                'last_used': row[5]
            })
        
        conn.close()
        return fingerprints
    
    def generate_certificate_report(self):
        """生成证书报告"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM user_certificates')
        total_certs = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM user_certificates WHERE status = "active"')
        active_certs = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM user_certificates WHERE status = "revoked"')
        revoked_certs = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM device_fingerprints')
        total_fingerprints = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM device_fingerprints WHERE trusted = 1')
        trusted_fingerprints = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM certificate_revocations')
        revocation_count = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n" + "="*80)
        print("          用户证书管理系统报告")
        print("="*80)
        
        print(f"\n数字证书统计:")
        print(f"  证书总数: {total_certs}")
        print(f"  活跃证书: {active_certs}")
        print(f"  已吊销证书: {revoked_certs}")
        
        print(f"\n设备指纹统计:")
        print(f"  指纹总数: {total_fingerprints}")
        print(f"  可信指纹: {trusted_fingerprints}")
        
        print(f"\n吊销记录:")
        print(f"  吊销次数: {revocation_count}")
        
        print("\n安全特性:")
        print(f"  ✅ 数字证书签名验证")
        print(f"  ✅ 证书有效期检查")
        print(f"  ✅ 设备指纹识别")
        print(f"  ✅ 指纹可信度验证")
        print(f"  ✅ 证书吊销列表")
        print(f"  ✅ 使用日志记录")
        
        print("\n" + "="*80)
        print("  用户证书管理系统完成！")
        print("="*80)
    
    def run_certificate_demo(self):
        """运行证书演示"""
        print("="*80)
        print("          用户证书管理系统")
        print("="*80)
        
        user_id = 'test_user_123'
        
        print("\n[1/3] 生成数字证书...")
        cert = self.generate_certificate(user_id, 'digital')
        print(f"  ✓ 证书生成成功")
        print(f"    证书ID: {cert['certificate_id'][:20]}...")
        print(f"    序列号: {cert['serial_number']}")
        print(f"    有效期至: {cert['valid_to']}")
        
        print("\n[2/3] 注册设备指纹...")
        device_info = {
            'device_id': 'device_001',
            'device_name': 'iPhone 15 Pro',
            'os': 'iOS 17',
            'browser': 'Safari',
            'ip_address': '192.168.1.100'
        }
        fp_result = self.register_device_fingerprint(user_id, device_info)
        print(f"  ✓ 设备指纹注册成功")
        print(f"    指纹ID: {fp_result['fingerprint_id']}")
        print(f"    指纹哈希: {fp_result['fingerprint_hash'][:20]}...")
        
        print("\n[3/3] 验证证书和指纹...")
        cert_valid = self.validate_certificate(cert['certificate_id'], user_id)
        print(f"  证书验证: {'✅ 有效' if cert_valid['valid'] else '❌ 无效'}")
        
        fp_valid = self.validate_fingerprint(user_id, fp_result['fingerprint_hash'])
        print(f"  指纹验证: {'✅ 有效' if fp_valid['valid'] else '❌ 无效'}")
        if fp_valid.get('trusted'):
            print(f"  指纹信任: ✅ 可信")
        
        self.generate_certificate_report()

def main():
    manager = CertificateManager()
    manager.run_certificate_demo()

if __name__ == "__main__":
    main()