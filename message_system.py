#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS实时消息系统
支持WebSocket实时通信
"""

import os
import json
import time
import threading
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List

try:
    from flask_socketio import SocketIO, emit, join_room, leave_room
    socketio_available = True
except ImportError:
    socketio_available = False

logger = print

class MessageSystem:
    """实时消息系统"""
    
    def __init__(self, app=None):
        self.app = app
        self.socketio = None
        self.connected_users: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[str, str] = {}
        self.message_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        
        if socketio_available and app:
            self._init_socketio()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'message_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'cors_enabled': True,
            'async_mode': 'eventlet',
            'heartbeat_interval': 30,
            'ping_timeout': 60,
            'max_connections': 100,
            'message_types': ['system', 'notification', 'chat', 'alert', 'data']
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'message_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_socketio(self):
        """初始化SocketIO"""
        self.socketio = SocketIO(
            self.app,
            async_mode=self.config['async_mode'],
            cors_allowed_origins="*" if self.config['cors_enabled'] else None,
            heartbeat_interval=self.config['heartbeat_interval'],
            ping_timeout=self.config['ping_timeout']
        )
        
        @self.socketio.on('connect')
        def handle_connect():
            logger(f"[消息系统] 客户端连接")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger(f"[消息系统] 客户端断开")
        
        @self.socketio.on('authenticate')
        def handle_authenticate(data):
            user_id = data.get('user_id')
            session_id = data.get('session_id')
            
            if user_id:
                with self.lock:
                    self.connected_users[user_id] = {
                        'session_id': session_id,
                        'connected_at': datetime.now(),
                        'last_activity': datetime.now()
                    }
                    self.user_sessions[session_id] = user_id
                
                emit('authenticated', {'status': 'success'})
                logger(f"[消息系统] 用户认证: {user_id}")
        
        @self.socketio.on('send_message')
        def handle_send_message(data):
            message = self._create_message(
                sender_id=data.get('sender_id'),
                message_type=data.get('type', 'chat'),
                content=data.get('content'),
                target_user=data.get('target_user')
            )
            self._broadcast_message(message)
        
        @self.socketio.on('join_room')
        def handle_join_room(room):
            join_room(room)
            logger(f"[消息系统] 用户加入房间: {room}")
        
        @self.socketio.on('leave_room')
        def handle_leave_room(room):
            leave_room(room)
            logger(f"[消息系统] 用户离开房间: {room}")
        
        @self.socketio.on('subscribe')
        def handle_subscribe(channels):
            for channel in channels:
                join_room(channel)
            logger(f"[消息系统] 用户订阅频道: {channels}")
        
        logger(f"[消息系统] SocketIO已初始化")
    
    def _create_message(self, sender_id: str, message_type: str, 
                        content: str, target_user: str = None) -> Dict[str, Any]:
        """创建消息"""
        message = {
            'id': hashlib.md5(f"{sender_id}{time.time()}".encode()).hexdigest(),
            'sender_id': sender_id,
            'type': message_type,
            'content': content,
            'target_user': target_user,
            'timestamp': datetime.now().isoformat(),
            'status': 'sent'
        }
        
        with self.lock:
            self.message_history.append(message)
            if len(self.message_history) > self.max_history_size:
                self.message_history = self.message_history[-self.max_history_size:]
        
        return message
    
    def _broadcast_message(self, message: Dict[str, Any]):
        """广播消息"""
        if not self.socketio:
            return
        
        target_user = message.get('target_user')
        
        if target_user:
            emit('new_message', message, room=target_user)
        else:
            emit('new_message', message, broadcast=True)
    
    def send_message(self, sender_id: str, message_type: str, content: str,
                     target_user: str = None, room: str = None):
        """发送消息"""
        message = self._create_message(sender_id, message_type, content, target_user)
        
        if self.socketio:
            if room:
                emit('new_message', message, room=room)
            elif target_user:
                emit('new_message', message, room=target_user)
            else:
                emit('new_message', message, broadcast=True)
        
        return message
    
    def send_system_message(self, content: str, target_user: str = None):
        """发送系统消息"""
        return self.send_message('system', 'system', content, target_user)
    
    def send_notification(self, content: str, target_user: str = None):
        """发送通知"""
        return self.send_message('system', 'notification', content, target_user)
    
    def send_alert(self, content: str, target_user: str = None):
        """发送警报"""
        return self.send_message('system', 'alert', content, target_user)
    
    def send_data(self, data: Dict[str, Any], target_user: str = None):
        """发送数据消息"""
        return self.send_message('system', 'data', json.dumps(data), target_user)
    
    def get_message_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取消息历史"""
        with self.lock:
            return self.message_history[-limit:]
    
    def get_connected_users(self) -> List[Dict[str, Any]]:
        """获取在线用户"""
        with self.lock:
            return list(self.connected_users.values())
    
    def disconnect_user(self, user_id: str):
        """断开用户连接"""
        with self.lock:
            if user_id in self.connected_users:
                session_id = self.connected_users[user_id]['session_id']
                del self.connected_users[user_id]
                if session_id in self.user_sessions:
                    del self.user_sessions[session_id]
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            return {
                'status': 'running' if self.socketio else 'disabled',
                'connected_users': len(self.connected_users),
                'max_connections': self.config['max_connections'],
                'message_history_size': len(self.message_history),
                'heartbeat_interval': self.config['heartbeat_interval'],
                'ping_timeout': self.config['ping_timeout']
            }
    
    def start(self, host: str = '0.0.0.0', port: int = 5001):
        """启动消息服务"""
        if not self.socketio:
            logger(f"[消息系统] SocketIO不可用，请安装 flask-socketio")
            return
        
        self.socketio.run(self.app, host=host, port=port, debug=True)
    
    def init_app(self, app):
        """初始化应用"""
        self.app = app
        if socketio_available:
            self._init_socketio()

message_system = MessageSystem()
