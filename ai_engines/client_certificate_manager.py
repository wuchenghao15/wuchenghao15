# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端证书管理和会话记录系统
Client Certificate Management and Session Recording System

特性:
- 统一打包上传数据库和日志
"""

import os
import sys
import json
import time
import hashlib
import uuid
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from collections import deque
import threading
import logging

logger = logging.getLogger('client_certificate')


class CertificateStatus(Enum):
    """证书状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ExitType(Enum):
    """退出类型"""
    NORMAL = "normal"           # 正常退出
    UNEXPECTED = "unexpected"   # 意外退出
    TEMPORARY = "temporary"     # 临时挂单暂退


class OperationType(Enum):
    """操作类型"""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    QUERY = "query"
    EXECUTE = "execute"
    UPLOAD = "upload"
    DOWNLOAD = "download"


class ClientCertificate:
    """客户端数字证书"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.certificate_id = self._generate_certificate_id()
        self.public_key = self._generate_key_pair()['public']
        self.private_key_hash = hashlib.sha256(
            self._generate_key_pair()['private'].encode()
        ).hexdigest()
        
        self.issued_at = datetime.now().isoformat()
        self.expires_at = (datetime.now() + timedelta(days=365)).isoformat()
        self.status = CertificateStatus.ACTIVE
        
        self.issued_by = "MTSCOS_AI_System"
        self.subject = f"Client_{client_id}"
        self.organization = "MTSCOS"
        
        self.metadata = {}
    
    def _generate_certificate_id(self) -> str:
        """生成证书ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"CERT_{timestamp}_{uuid.uuid4().hex[:8]}"
    
    def _generate_key_pair(self) -> Dict:
        """生成密钥对(模拟)"""
        return {
            'public': f"PUBLIC_KEY_{uuid.uuid4().hex}",
            'private': f"PRIVATE_KEY_{uuid.uuid4().hex}"
        }
    
    def to_dict(self) -> Dict:
        return {
            'client_id': self.client_id,
            'certificate_id': self.certificate_id,
            'public_key': self.public_key,
            'issued_at': self.issued_at,
            'expires_at': self.expires_at,
            'status': self.status.value,
            'issued_by': self.issued_by,
            'subject': self.subject,
            'organization': self.organization,
            'metadata': self.metadata
        }
    
    def is_valid(self) -> bool:
        """检查证书是否有效"""
        if self.status != CertificateStatus.ACTIVE:
            return False
        
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.now() < expires
    
    def revoke(self):
        """吊销证书"""
        self.status = CertificateStatus.REVOKED
    
    def renew(self):
        """续期证书"""
        if self.status == CertificateStatus.REVOKED:
            raise ValueError("无法续期已吊销的证书")
        
        self.expires_at = (datetime.now() + timedelta(days=365)).isoformat()
        self.metadata['renew_count'] = self.metadata.get('renew_count', 0) + 1


class RecordUnit:
    """记录单元 - 用户信息记录"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.record_id = f"REC_{uuid.uuid4().hex[:12]}"
        
        self.user_info = {}
        self.device_info = {}
        self.session_info = {}
        self.connection_info = {}
        
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def update_user_info(self, user_info: Dict):
        """更新用户信息"""
        self.user_info.update(user_info)
        self.updated_at = datetime.now().isoformat()
    
    def update_device_info(self, device_info: Dict):
        """更新设备信息"""
        self.device_info.update(device_info)
        self.updated_at = datetime.now().isoformat()
    
    def update_session_info(self, session_info: Dict):
        """更新会话信息"""
        self.session_info.update(session_info)
        self.updated_at = datetime.now().isoformat()
    
    def update_connection_info(self, connection_info: Dict):
        """更新连接信息"""
        self.connection_info.update(connection_info)
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            'record_id': self.record_id,
            'client_id': self.client_id,
            'user_info': self.user_info,
            'device_info': self.device_info,
            'session_info': self.session_info,
            'connection_info': self.connection_info,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class LogUnit:
    """日志单元 - 操作日志记录"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.log_entries = deque(maxlen=10000)
    
    def add_log(self, level: str, message: str, context: Dict = None):
        """添加日志条目"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.upper(),
            'message': message,
            'context': context or {}
        }
        self.log_entries.append(log_entry)
    
    def info(self, message: str, context: Dict = None):
        """添加INFO级别日志"""
        self.add_log('INFO', message, context)
    
    def warning(self, message: str, context: Dict = None):
        """添加WARNING级别日志"""
        self.add_log('WARNING', message, context)
    
    def error(self, message: str, context: Dict = None):
        """添加ERROR级别日志"""
        self.add_log('ERROR', message, context)
    
    def debug(self, message: str, context: Dict = None):
        """添加DEBUG级别日志"""
        self.add_log('DEBUG', message, context)
    
    def critical(self, message: str, context: Dict = None):
        """添加CRITICAL级别日志"""
        self.add_log('CRITICAL', message, context)
    
    def get_logs(self, limit: int = 100) -> List[Dict]:
        """获取日志列表"""
        return list(self.log_entries)[-limit:]
    
    def to_dict(self) -> Dict:
        return {
            'client_id': self.client_id,
            'log_count': len(self.log_entries),
            'logs': list(self.log_entries)
        }


class OperationUnit:
    """操作单元 - 操作记录"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.operations = deque(maxlen=1000)
    
    def record_operation(self, op_type: OperationType, 
                        resource: str = "",
                        details: Dict = None):
        """记录操作"""
        operation = {
            'operation_id': f"OP_{uuid.uuid4().hex[:12]}",
            'timestamp': datetime.now().isoformat(),
            'type': op_type.value,
            'resource': resource,
            'details': details or {}
        }
        self.operations.append(operation)
    
    def get_operations(self, limit: int = 50) -> List[Dict]:
        """获取操作列表"""
        return list(self.operations)[-limit:]
    
    def to_dict(self) -> Dict:
        return {
            'client_id': self.client_id,
            'operation_count': len(self.operations),
            'operations': list(self.operations)
        }


class InfoContainer:
    """信息容器 - 统一打包客户端数据"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.container_id = f"CNT_{uuid.uuid4().hex[:16]}"
        
        self.record_unit = RecordUnit(client_id)
        self.log_unit = LogUnit(client_id)
        self.operation_unit = OperationUnit(client_id)
        
        self.created_at = datetime.now().isoformat()
        self.last_packed_at = None
        self.pack_count = 0
    
    def pack(self, exit_type: ExitType = ExitType.NORMAL,
             exit_reason: str = "") -> Dict:
        """打包所有数据"""
        self.last_packed_at = datetime.now().isoformat()
        self.pack_count += 1
        
        package = {
            'container_id': self.container_id,
            'client_id': self.client_id,
            'exit_type': exit_type.value,
            'exit_reason': exit_reason,
            'packed_at': self.last_packed_at,
            'pack_count': self.pack_count,
            
            'record_unit': self.record_unit.to_dict(),
            'log_unit': self.log_unit.to_dict(),
            'operation_unit': self.operation_unit.to_dict(),
            
            'package_checksum': self._calculate_checksum()
        }
        
        return package
    
    def _calculate_checksum(self) -> str:
        """计算包的校验和"""
        data = json.dumps({
            'record': self.record_unit.to_dict(),
            'logs': self.log_unit.get_logs(),
            'operations': self.operation_unit.get_operations()
        }, sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()
    
    def clear(self):
        """清空容器数据"""
        self.record_unit = RecordUnit(self.client_id)
        self.log_unit = LogUnit(self.client_id)
        self.operation_unit = OperationUnit(self.client_id)
        self.pack_count = 0


class ClientSession:
    """客户端会话"""
    
    def __init__(self, client_id: str, certificate: ClientCertificate):
        self.client_id = client_id
        self.certificate = certificate
        self.session_id = f"SES_{uuid.uuid4().hex[:12]}"
        
        self.info_container = InfoContainer(client_id)
        
        self.login_time = datetime.now().isoformat()
        self.last_active_time = datetime.now().isoformat()
        self.is_active = True
        
        self.connection_count = 1
    
    def update_activity(self):
        """更新活动时间"""
        self.last_active_time = datetime.now().isoformat()
    
    def logout(self, exit_type: ExitType = ExitType.NORMAL,
               reason: str = "") -> Dict:
        """退出登录并打包数据"""
        self.is_active = False
        
        # 记录退出操作
        self.info_container.operation_unit.record_operation(
            OperationType.LOGOUT,
            details={'exit_type': exit_type.value, 'reason': reason}
        )
        
        # 记录退出日志
        self.info_container.log_unit.info(
            f"Client logged out",
            {'exit_type': exit_type.value, 'reason': reason}
        )
        
        # 打包数据
        package = self.info_container.pack(exit_type, reason)
        
        return package
    
    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'client_id': self.client_id,
            'certificate_id': self.certificate.certificate_id,
            'login_time': self.login_time,
            'last_active_time': self.last_active_time,
            'is_active': self.is_active,
            'connection_count': self.connection_count
        }


class ClientCertificateManager:
    """客户端证书管理器"""
    
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(__file__), '..', '..', 'client_certificates'
        )
        
        self.certificates_dir = os.path.join(self.storage_dir, 'certificates')
        self.sessions_dir = os.path.join(self.storage_dir, 'sessions')
        self.packages_dir = os.path.join(self.storage_dir, 'packages')
        self.metadata_dir = os.path.join(self.storage_dir, '.metadata')
        
        self.certificates_file = os.path.join(self.metadata_dir, 'certificates.json')
        self.sessions_file = os.path.join(self.metadata_dir, 'sessions.json')
        self.packages_file = os.path.join(self.metadata_dir, 'packages.json')
        
        self.certificates = {}
        self.sessions = {}
        self.packages = {}
        
        self.lock = threading.Lock()
        
        self._ensure_directories()
        self._load_data()
    
    def _ensure_directories(self):
        """确保目录结构存在"""
        directories = [
            self.storage_dir,
            self.certificates_dir,
            self.sessions_dir,
            self.packages_dir,
            self.metadata_dir
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
    
    def _load_data(self):
        """加载数据"""
        # 加载证书
        if os.path.exists(self.certificates_file):
            try:
                with open(self.certificates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for client_id, cert_data in data.items():
                        cert = ClientCertificate(client_id)
                        cert.__dict__.update(cert_data)
                        cert.status = CertificateStatus(cert.status)
                        self.certificates[client_id] = cert
            except Exception as e:
                logger.error(f"加载证书失败: {str(e)}")
        
        # 加载会话
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    self.sessions = json.load(f)
            except Exception as e:
                logger.error(f"加载会话失败: {str(e)}")
        
        # 加载包记录
        if os.path.exists(self.packages_file):
            try:
                with open(self.packages_file, 'r', encoding='utf-8') as f:
                    self.packages = json.load(f)
            except Exception as e:
                logger.error(f"加载包记录失败: {str(e)}")
    
    def _save_data(self):
        """保存数据"""
        # 保存证书
        try:
            with open(self.certificates_file, 'w', encoding='utf-8') as f:
                data = {client_id: cert.to_dict() for client_id, cert in self.certificates.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存证书失败: {str(e)}")
        
        # 保存会话
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存会话失败: {str(e)}")
        
        # 保存包记录
        try:
            with open(self.packages_file, 'w', encoding='utf-8') as f:
                json.dump(self.packages, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存包记录失败: {str(e)}")
    
    def issue_certificate(self, client_id: str) -> Optional[ClientCertificate]:
        """发放证书"""
        with self.lock:
            if client_id in self.certificates:
                existing = self.certificates[client_id]
                if existing.is_valid():
                    logger.info(f"客户端已有有效证书: {client_id}")
                    return existing
            
            certificate = ClientCertificate(client_id)
            self.certificates[client_id] = certificate
            
            # 保存证书文件
            cert_file = os.path.join(self.certificates_dir, f"{client_id}.json")
            with open(cert_file, 'w', encoding='utf-8') as f:
                json.dump(certificate.to_dict(), f, indent=2, ensure_ascii=False)
            
            self._save_data()
            logger.info(f"发放新证书: {client_id} -> {certificate.certificate_id}")
            
            return certificate
    
    def get_certificate(self, client_id: str) -> Optional[ClientCertificate]:
        """获取证书"""
        return self.certificates.get(client_id)
    
    def revoke_certificate(self, client_id: str) -> bool:
        """吊销证书"""
        if client_id not in self.certificates:
            return False
        
        self.certificates[client_id].revoke()
        self._save_data()
        logger.info(f"吊销证书: {client_id}")
        return True
    
    def renew_certificate(self, client_id: str) -> bool:
        """续期证书"""
        if client_id not in self.certificates:
            return False
        
        try:
            self.certificates[client_id].renew()
            self._save_data()
            logger.info(f"续期证书: {client_id}")
            return True
        except ValueError:
            return False
    
    def create_session(self, client_id: str) -> Optional[ClientSession]:
        """创建会话"""
        certificate = self.get_certificate(client_id)
        if not certificate or not certificate.is_valid():
            logger.error(f"无效证书: {client_id}")
            return None
        
        session = ClientSession(client_id, certificate)
        self.sessions[session.session_id] = session.to_dict()
        
        session.info_container.log_unit.info(f"Session created")
        session.info_container.operation_unit.record_operation(OperationType.LOGIN)
        
        self._save_data()
        logger.info(f"创建会话: {client_id} -> {session.session_id}")
        
        return session
    
    def get_session(self, session_id: str) -> Optional[ClientSession]:
        """获取会话"""
        session_data = self.sessions.get(session_id)
        if not session_data:
            return None
        
        client_id = session_data.get('client_id')
        certificate = self.get_certificate(client_id)
        if not certificate:
            return None
        
        session = ClientSession(client_id, certificate)
        session.__dict__.update(session_data)
        return session
    
    def close_session(self, session_id: str, 
                     exit_type: ExitType = ExitType.NORMAL,
                     reason: str = "") -> Optional[Dict]:
        """关闭会话"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        # 打包数据
        package = session.logout(exit_type, reason)
        
        # 保存包文件
        package_file = os.path.join(
            self.packages_dir,
            f"{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(package_file, 'w', encoding='utf-8') as f:
            json.dump(package, f, indent=2, ensure_ascii=False)
        
        # 记录包
        self.packages[package['container_id']] = {
            'package_id': package['container_id'],
            'client_id': session.client_id,
            'session_id': session_id,
            'exit_type': exit_type.value,
            'file_path': package_file,
            'packed_at': package['packed_at'],
            'uploaded_to_db': False
        }
        
        # 从活跃会话中移除
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        self._save_data()
        
        # 上报数据库
        self._report_to_database(package)
        
        logger.info(f"会话关闭: {session_id}, 退出类型: {exit_type.value}")
        
        return package
    
    def _report_to_database(self, package: Dict):
        """上报到数据库"""
        try:
            from app.ai.system_integration import enhanced_db_reporter
            
            # 上报会话包
            enhanced_db_reporter.report_data_point(
                'client_session_package',
                package,
                'NORMAL'
            )
            
            # 标记已上报
            self.packages[package['container_id']]['uploaded_to_db'] = True
            self._save_data()
            
            logger.info(f"会话包已上报数据库: {package['container_id']}")
            
        except ImportError:
            logger.warning("数据库上报模块未加载")
        except Exception as e:
            logger.error(f"上报数据库失败: {str(e)}")
    
    def get_client_info(self, client_id: str) -> Dict:
        """获取客户端完整信息"""
        certificate = self.get_certificate(client_id)
        sessions = [
            s for s in self.sessions.values()
            if s.get('client_id') == client_id
        ]
        client_packages = [
            p for p in self.packages.values()
            if p.get('client_id') == client_id
        ]
        
        return {
            'client_id': client_id,
            'certificate': certificate.to_dict() if certificate else None,
            'active_sessions': sessions,
            'total_packages': len(client_packages),
            'last_package': client_packages[-1] if client_packages else None
        }
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        active_certs = sum(1 for c in self.certificates.values() if c.status == CertificateStatus.ACTIVE)
        active_sessions = sum(1 for s in self.sessions.values() if s.get('is_active'))
        
        return {
            'total_certificates': len(self.certificates),
            'active_certificates': active_certs,
            'total_sessions': len(self.sessions),
            'active_sessions': active_sessions,
            'total_packages': len(self.packages),
            'storage_dir': self.storage_dir
        }


# 全局实例
client_certificate_manager = ClientCertificateManager()
