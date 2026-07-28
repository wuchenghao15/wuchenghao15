#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS VPN Server - 基于Python的VPN代理服务器
实现安全的网络流量代理功能，支持多用户认证、流量监控、API管理
增强功能：连接状态管理、流量限制、连接保持、心跳检测、自动重连
"""

import socket
import threading
import ssl
import os
import sys
import json
import hashlib
import time
import signal
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = print

class VPNServer:
    """VPN代理服务器"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 51820):
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.clients: Dict[int, Dict[str, Any]] = {}
        self.client_id_counter = 0
        self.lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        self.traffic_stats = {
            'total_bytes_sent': 0,
            'total_bytes_received': 0,
            'total_connections': 0,
            'current_connections': 0,
            'peak_connections': 0,
            'start_time': datetime.now(),
            'connections_history': [],
            'traffic_history': []
        }
        
        self.login_attempts: Dict[str, Dict[str, int]] = {}
        self.connection_states: Dict[int, str] = {}
        self.heartbeat_thread = None
        
        self.config = self._load_config()
        self._setup_ssl()
        
        self._start_heartbeat_check()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'vpn_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'server': {
                'host': '0.0.0.0',
                'port': 51820,
                'max_clients': 10,
                'connection_timeout': 300,
                'max_login_attempts': 5,
                'login_lockout_time': 60
            },
            'ssl': {
                'enabled': True,
                'cert_file': 'vpn_server.crt',
                'key_file': 'vpn_server.key'
            },
            'auth': {
                'enabled': True,
                'users': {
                    'mtscos_admin': 'MTSCOS_VPN_2026',
                    'admin': 'mtscos_vpn_2026'
                }
            },
            'firewall': {
                'enabled': True,
                'whitelist': [],
                'blacklist': [],
                'allowed_ports': [80, 443, 22, 3389, 5432, 3306],
                'blocked_ports': []
            },
            'logging': {
                'enabled': True,
                'log_file': 'vpn_server.log',
                'log_level': 'INFO'
            },
            'api': {
                'enabled': True,
                'host': '127.0.0.1',
                'port': 51821,
                'api_key': 'MTSCOS_VPN_API_KEY_2026'
            },
            'traffic': {
                'enabled': True,
                'limit_per_user': 1073741824
            }
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'vpn_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _generate_ssl_cert(self):
        """生成SSL证书"""
        cert_file = self.config['ssl']['cert_file']
        key_file = self.config['ssl']['key_file']
        
        if os.path.exists(cert_file) and os.path.exists(key_file):
            logger(f"[VPN] SSL证书已存在")
            return True
        
        logger(f"[VPN] 生成SSL证书...")
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import serialization, hashes
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.backends import default_backend
            import datetime
            
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            public_key = private_key.public_key()
            
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MTSCOS AI"),
                x509.NameAttribute(NameOID.COMMON_NAME, "mtscos-vpn"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                public_key
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).sign(private_key, hashes.SHA256(), default_backend())
            
            with open(key_file, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                ))
            
            with open(cert_file, 'wb') as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            logger(f"[VPN] SSL证书生成成功")
            return True
        except ImportError:
            logger(f"[VPN] 未安装cryptography库，跳过SSL证书生成")
            return False
        except Exception as e:
            logger(f"[VPN] SSL证书生成失败: {e}")
            return False
    
    def _setup_ssl(self):
        """设置SSL"""
        if self.config['ssl']['enabled']:
            self._generate_ssl_cert()
    
    def _log(self, message: str, level: str = 'INFO'):
        """日志记录"""
        if not self.config['logging']['enabled']:
            return
        
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        current_level = levels.index(self.config['logging']['log_level'])
        message_level = levels.index(level)
        
        if message_level >= current_level:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"[{timestamp}] [{level}] {message}"
            print(log_entry)
            
            log_file = self.config['logging']['log_file']
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
    
    def _check_firewall(self, client_ip: str, target_port: int) -> bool:
        """防火墙检查"""
        firewall = self.config['firewall']
        if not firewall['enabled']:
            return True
        
        if client_ip in firewall['blacklist']:
            self._log(f"[VPN] IP {client_ip} 在黑名单中", 'WARNING')
            return False
        
        if firewall['whitelist'] and client_ip not in firewall['whitelist']:
            self._log(f"[VPN] IP {client_ip} 不在白名单中", 'WARNING')
            return False
        
        if target_port in firewall['blocked_ports']:
            self._log(f"[VPN] 端口 {target_port} 被阻止", 'WARNING')
            return False
        
        if firewall['allowed_ports'] and target_port not in firewall['allowed_ports']:
            self._log(f"[VPN] 端口 {target_port} 不在允许列表中", 'WARNING')
            return False
        
        return True
    
    def _check_traffic_limit(self, client_id: int) -> bool:
        """检查流量限制"""
        traffic_config = self.config.get('traffic', {})
        if not traffic_config.get('enabled', True):
            return True
        
        limit_per_user = traffic_config.get('limit_per_user', 1073741824)
        
        with self.lock:
            if client_id in self.clients:
                total_traffic = self.clients[client_id].get('bytes_sent', 0) + \
                               self.clients[client_id].get('bytes_received', 0)
                if total_traffic >= limit_per_user:
                    self._log(f"[VPN] 客户端 {client_id} 流量超限", 'WARNING')
                    return False
        
        return True
    
    def _start_heartbeat_check(self):
        """启动心跳检测线程"""
        def heartbeat_check():
            while self.is_running:
                try:
                    now = time.time()
                    timeout = self.config['server'].get('connection_timeout', 300)
                    
                    with self.lock:
                        clients_to_remove = []
                        for client_id, info in self.clients.items():
                            last_activity = info.get('last_activity', now)
                            if now - last_activity > timeout:
                                clients_to_remove.append(client_id)
                                self.connection_states[client_id] = 'timeout'
                        
                        for client_id in clients_to_remove:
                            if client_id in self.clients:
                                self._log(f"[VPN] 客户端 {client_id} 超时断开", 'WARNING')
                                del self.clients[client_id]
                                if client_id in self.connection_states:
                                    del self.connection_states[client_id]
                except Exception as e:
                    self._log(f"[VPN] 心跳检测错误: {e}", 'ERROR')
                
                time.sleep(60)
        
        self.heartbeat_thread = threading.Thread(target=heartbeat_check)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
    
    def _update_client_activity(self, client_id: int):
        """更新客户端活动时间"""
        with self.lock:
            if client_id in self.clients:
                self.clients[client_id]['last_activity'] = time.time()
    
    def _check_login_attempts(self, client_ip: str) -> bool:
        """检查登录尝试次数"""
        now = time.time()
        max_attempts = self.config['server']['max_login_attempts']
        lockout_time = self.config['server']['login_lockout_time']
        
        if client_ip not in self.login_attempts:
            self.login_attempts[client_ip] = {'count': 0, 'first_attempt': now}
        
        attempts = self.login_attempts[client_ip]
        
        if attempts['count'] >= max_attempts:
            if now - attempts['first_attempt'] < lockout_time:
                remaining = int(lockout_time - (now - attempts['first_attempt']))
                self._log(f"[VPN] IP {client_ip} 登录被锁定，剩余 {remaining} 秒", 'WARNING')
                return False
            else:
                attempts['count'] = 0
                attempts['first_attempt'] = now
        
        return True
    
    def _record_login_attempt(self, client_ip: str, success: bool):
        """记录登录尝试"""
        if client_ip not in self.login_attempts:
            self.login_attempts[client_ip] = {'count': 0, 'first_attempt': time.time()}
        
        if not success:
            self.login_attempts[client_ip]['count'] += 1
        else:
            self.login_attempts[client_ip]['count'] = 0
    
    def _authenticate(self, username: str, password: str) -> bool:
        """用户认证"""
        if not self.config['auth']['enabled']:
            return True
        
        users = self.config['auth']['users']
        if username in users and users[username] == password:
            return True
        return False
    
    def _update_stats(self, sent_bytes: int = 0, received_bytes: int = 0, connected: bool = False,
    disconnected: bool = False):
        """更新统计信息"""
        with self.stats_lock:
            if sent_bytes > 0:
                self.traffic_stats['total_bytes_sent'] += sent_bytes
            if received_bytes > 0:
                self.traffic_stats['total_bytes_received'] += received_bytes
            
            if sent_bytes > 0 or received_bytes > 0:
                traffic_record = {
                    'time': datetime.now().isoformat(),
                    'bytes_sent': sent_bytes,
                    'bytes_received': received_bytes
                }
                self.traffic_stats['traffic_history'].append(traffic_record)
                if len(self.traffic_stats['traffic_history']) > 200:
                    self.traffic_stats['traffic_history'] = self.traffic_stats['traffic_history'][-200:]
            
            if connected:
                self.traffic_stats['total_connections'] += 1
                self.traffic_stats['current_connections'] += 1
                if self.traffic_stats['current_connections'] > self.traffic_stats['peak_connections']:
                    self.traffic_stats['peak_connections'] = self.traffic_stats['current_connections']
                
                record = {
                    'time': datetime.now().isoformat(),
                    'event': 'connected'
                }
                self.traffic_stats['connections_history'].append(record)
                if len(self.traffic_stats['connections_history']) > 100:
                    self.traffic_stats['connections_history'] = self.traffic_stats['connections_history'][-100:]
            
            if disconnected:
                self.traffic_stats['current_connections'] -= 1
                
                record = {
                    'time': datetime.now().isoformat(),
                    'event': 'disconnected'
                }
                self.traffic_stats['connections_history'].append(record)
                if len(self.traffic_stats['connections_history']) > 100:
                    self.traffic_stats['connections_history'] = self.traffic_stats['connections_history'][-100:]
    
    def _handle_client(self, client_socket: socket.socket, addr: tuple):
        """处理客户端连接"""
        client_ip = addr[0]
        
        if not self._check_login_attempts(client_ip):
            client_socket.close()
            return
        
        with self.lock:
            self.client_id_counter += 1
            client_id = self.client_id_counter
            self.connection_states[client_id] = 'connecting'
        
        self._log(f"[VPN] 客户端连接: {addr} (ID: {client_id})")
        
        try:
            if self.config['ssl']['enabled']:
                cert_file = self.config['ssl']['cert_file']
                key_file = self.config['ssl']['key_file']
                if os.path.exists(cert_file) and os.path.exists(key_file):
                    try:
                        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                        context.load_cert_chain(certfile=cert_file, keyfile=key_file)
                        client_socket = context.wrap_socket(client_socket, server_side=True)
                        self._log(f"[VPN] SSL连接已建立")
                    except Exception as e:
                        self._log(f"[VPN] SSL握手失败: {e}", 'ERROR')
                        client_socket.close()
                        return
            
            buffer = b''
            authenticated = not self.config['auth']['enabled']
            username = None
            
            while True:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    buffer += data
                    
                    if b'\r\n\r\n' in buffer:
                        header, rest = buffer.split(b'\r\n\r\n', 1)
                        header_str = header.decode('utf-8', errors='ignore')
                        
                        if header_str.startswith('AUTH') and not authenticated:
                            parts = header_str.split()
                            if len(parts) >= 3:
                                username = parts[1]
                                password = parts[2]
                                if self._authenticate(username, password):
                                    client_socket.sendall(b'OK\r\n\r\n')
                                    authenticated = True
                                    self._record_login_attempt(client_ip, True)
                                    self._log(f"[VPN] 用户认证成功: {username}")
                                    self._update_stats(connected=True)
                                    
                                    with self.lock:
                                        self.clients[client_id] = {
                                            'ip': client_ip,
                                            'username': username,
                                            'connected_at': datetime.now(),
                                            'bytes_sent': 0,
                                            'bytes_received': 0,
                                            'last_activity': time.time()
                                        }
                                        self.connection_states[client_id] = 'authenticated'
                                else:
                                    client_socket.sendall(b'ERROR\r\n\r\n')
                                    self._record_login_attempt(client_ip, False)
                                    self._log(f"[VPN] 用户认证失败: {username}", 'WARNING')
                                    client_socket.close()
                                    return
                        elif header_str.startswith('CONNECT'):
                            if authenticated:
                                if not self._check_traffic_limit(client_id):
                                    client_socket.sendall(b'HTTP/1.1 429 Too Many Requests\r\n\r\n')
                                    self._log(f"[VPN] 客户端 {client_id} 流量超限，拒绝连接", 'WARNING')
                                    continue
                                self.connection_states[client_id] = 'connected'
                                self._handle_connect(client_socket, header_str, client_id)
                            else:
                                client_socket.sendall(b'HTTP/1.1 401 Unauthorized\r\n\r\n')
                                self._log(f"[VPN] 未认证的CONNECT请求", 'WARNING')
                        buffer = rest
                        
                        self._update_client_activity(client_id)
                except Exception as e:
                    self._log(f"[VPN] 客户端错误: {e}", 'ERROR')
                    break
        
        except Exception as e:
            self._log(f"[VPN] 客户端处理异常: {e}", 'ERROR')
        
        finally:
            client_socket.close()
            self._update_stats(disconnected=True)
            
            with self.lock:
                if client_id in self.clients:
                    del self.clients[client_id]
                if client_id in self.connection_states:
                    del self.connection_states[client_id]
            
            self._log(f"[VPN] 客户端断开: {addr} (ID: {client_id})")
    
    def _handle_connect(self, client_socket: socket.socket, header: str, client_id: int):
        """处理CONNECT请求"""
        try:
            lines = header.split('\r\n')
            connect_line = lines[0]
            target = connect_line.split()[1]
            
            if ':' in target:
                target_host, target_port = target.rsplit(':', 1)
                target_port = int(target_port)
            else:
                target_host = target
                target_port = 443
            
            client_ip = ''
            with self.lock:
                if client_id in self.clients:
                    client_ip = self.clients[client_id]['ip']
            
            if not self._check_firewall(client_ip, target_port):
                client_socket.sendall(b'HTTP/1.1 403 Forbidden\r\n\r\n')
                return
            
            self._log(f"[VPN] 转发到: {target_host}:{target_port}")
            
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.settimeout(10)
            
            try:
                target_socket.connect((target_host, target_port))
                client_socket.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                
                self._relay_traffic(client_socket, target_socket, client_id)
            except Exception as e:
                self._log(f"[VPN] 连接目标失败: {e}", 'ERROR')
                client_socket.sendall(b'HTTP/1.1 503 Service Unavailable\r\n\r\n')
                target_socket.close()
        
        except Exception as e:
            self._log(f"[VPN] CONNECT处理失败: {e}", 'ERROR')
    
    def _relay_traffic(self, client_socket: socket.socket, target_socket: socket.socket, client_id: int):
        """转发流量"""
        def forward(source, destination, direction: str):
            while True:
                try:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.sendall(data)
                    
                    byte_count = len(data)
                    self._update_stats(
                        sent_bytes=byte_count if direction == 'out' else 0,
                        received_bytes=byte_count if direction == 'in' else 0
                    )
                    
                    with self.lock:
                        if client_id in self.clients:
                            if direction == 'out':
                                self.clients[client_id]['bytes_sent'] += byte_count
                            else:
                                self.clients[client_id]['bytes_received'] += byte_count
                except:
                    break
        
        thread1 = threading.Thread(target=forward, args=(client_socket, target_socket, 'out'))
        thread2 = threading.Thread(target=forward, args=(target_socket, client_socket, 'in'))
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        target_socket.close()
    
    def start(self):
        """启动VPN服务器"""
        self._log(f"启动MTSCOS VPN服务器...")
        self._log(f"监听地址: {self.host}:{self.port}")
        self._log(f"SSL加密: {'启用' if self.config['ssl']['enabled'] else '禁用'}")
        self._log(f"用户认证: {'启用' if self.config['auth']['enabled'] else '禁用'}")
        self._log(f"防火墙: {'启用' if self.config['firewall']['enabled'] else '禁用'}")
        self._log(f"API服务: {'启用' if self.config['api']['enabled'] else '禁用'}")
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.is_running = True
            
            if self.config['api']['enabled']:
                self._start_api_server()
            
            self._log(f"VPN服务器已启动，等待客户端连接...")
            
            while self.is_running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    client_socket.settimeout(self.config['server']['connection_timeout'])
                    
                    with self.lock:
                        if len(self.clients) >= self.config['server']['max_clients']:
                            self._log(f"[VPN] 达到最大连接数限制", 'WARNING')
                            client_socket.sendall(b'HTTP/1.1 503 Service Unavailable\r\n\r\n')
                            client_socket.close()
                            continue
                    
                    thread = threading.Thread(target=self._handle_client, args=(client_socket, addr))
                    thread.daemon = True
                    thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.is_running:
                        self._log(f"[VPN] 接受连接失败: {e}", 'ERROR')
        
        except Exception as e:
            self._log(f"[VPN] 启动失败: {e}", 'ERROR')
        finally:
            self.stop()
    
    def _start_api_server(self):
        """启动API服务器"""
        api_host = self.config['api']['host']
        api_port = self.config['api']['port']
        
        class APIHandler(BaseHTTPRequestHandler):
            def __init__(self, *args, server_instance=None, **kwargs):
                self.server_instance = server_instance
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                self._handle_request()
            
            def do_POST(self):
                self._handle_request()
            
            def _handle_request(self):
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
                
                api_key = self.headers.get('X-API-Key', '')
                if api_key != self.server_instance.config['api']['api_key']:
                    self._send_response(401, {'error': 'Unauthorized'})
                    return
                
                path = self.path
                if path == '/api/status':
                    self._handle_status()
                elif path == '/api/clients':
                    self._handle_clients()
                elif path == '/api/users':
                    self._handle_users()
                elif path == '/api/stats':
                    self._handle_stats()
                elif path.startswith('/api/client/'):
                    self._handle_client_action(path)
                else:
                    self._send_response(404, {'error': 'Not Found'})
            
            def _handle_status(self):
                status = {
                    'status': 'running' if self.server_instance.is_running else 'stopped',
                    'port': self.server_instance.port,
                    'ssl_enabled': self.server_instance.config['ssl']['enabled'],
                    'auth_enabled': self.server_instance.config['auth']['enabled'],
                    'max_clients': self.server_instance.config['server']['max_clients'],
                    'current_clients': len(self.server_instance.clients)
                }
                self._send_response(200, status)
            
            def _handle_clients(self):
                with self.server_instance.lock:
                    clients = []
                    for client_id, info in self.server_instance.clients.items():
                        clients.append({
                            'id': client_id,
                            'ip': info['ip'],
                            'username': info['username'],
                            'connected_at': info['connected_at'].isoformat(),
                            'bytes_sent': info['bytes_sent'],
                            'bytes_received': info['bytes_received']
                        })
                self._send_response(200, {'clients': clients})
            
            def _handle_users(self):
                users = list(self.server_instance.config['auth']['users'].keys())
                self._send_response(200, {'users': users})
            
            def _handle_stats(self):
                with self.server_instance.stats_lock:
                    stats = self.server_instance.traffic_stats.copy()
                self._send_response(200, stats)
            
            def _handle_client_action(self, path):
                parts = path.split('/')
                if len(parts) >= 4:
                    action = parts[3]
                    client_id = int(parts[2])
                    
                    if action == 'disconnect':
                        with self.server_instance.lock:
                            if client_id in self.server_instance.clients:
                                del self.server_instance.clients[client_id]
                                self._send_response(200, {'success': True, 'message': 'Client disconnected'})
                            else:
                                self._send_response(404, {'error': 'Client not found'})
                            return
                
                self._send_response(400, {'error': 'Invalid action'})
            
            def _send_response(self, status_code: int, data: dict):
                self.send_response(status_code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            
            def log_message(self, format, *args):
                pass
        
        def create_handler(*args, **kwargs):
            return APIHandler(*args, server_instance=self, **kwargs)
        
        self.api_server = HTTPServer((api_host, api_port), create_handler)
        api_thread = threading.Thread(target=self.api_server.serve_forever)
        api_thread.daemon = True
        api_thread.start()
        
        self._log(f"API服务器已启动: {api_host}:{api_port}")
    
    def stop(self):
        """停止VPN服务器"""
        self._log(f"停止MTSCOS VPN服务器...")
        self.is_running = False
        
        if hasattr(self, 'api_server'):
            self.api_server.shutdown()
        
        if self.server_socket:
            self.server_socket.close()
        
        self._log(f"VPN服务器已停止")
    
    def add_user(self, username: str, password: str):
        """添加用户"""
        self.config['auth']['users'][username] = password
        self._save_config()
        self._log(f"用户添加成功: {username}")
    
    def remove_user(self, username: str):
        """删除用户"""
        if username in self.config['auth']['users']:
            del self.config['auth']['users'][username]
            self._save_config()
            self._log(f"用户删除成功: {username}")
        else:
            self._log(f"用户不存在: {username}", 'WARNING')
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务器状态"""
        with self.lock:
            connection_states_copy = self.connection_states.copy()
        
        return {
            'status': 'running' if self.is_running else 'stopped',
            'port': self.port,
            'ssl_enabled': self.config['ssl']['enabled'],
            'auth_enabled': self.config['auth']['enabled'],
            'max_clients': self.config['server']['max_clients'],
            'current_clients': len(self.clients),
            'connection_states': connection_states_copy,
            'stats': self.traffic_stats
        }
    
    def get_clients(self) -> List[Dict[str, Any]]:
        """获取在线客户端列表"""
        with self.lock:
            clients = []
            for client_id, info in self.clients.items():
                clients.append({
                    'id': client_id,
                    'ip': info['ip'],
                    'username': info['username'],
                    'connected_at': info['connected_at'].isoformat(),
                    'bytes_sent': info['bytes_sent'],
                    'bytes_received': info['bytes_received']
                })
        return clients

def main():
    """主函数"""
    print("=" * 60)
    print("     MTSCOS AI VPN Server v2.0.0")
    print("=" * 60)
    
    server = VPNServer()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'adduser':
            if len(sys.argv) >= 4:
                server.add_user(sys.argv[2], sys.argv[3])
            else:
                print("用法: python vpn_server.py adduser <username> <password>")
            return
        elif sys.argv[1] == 'removeuser':
            if len(sys.argv) >= 3:
                server.remove_user(sys.argv[2])
            else:
                print("用法: python vpn_server.py removeuser <username>")
            return
        elif sys.argv[1] == 'status':
            status = server.get_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
            return
    
    def signal_handler(sig, frame):
        server.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

if __name__ == '__main__':
    main()
