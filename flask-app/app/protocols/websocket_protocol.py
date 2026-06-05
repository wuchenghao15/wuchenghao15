#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket协议实现模块
提供WebSocket双向通信支持
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, Callable, List
from app.utils.logging import logger

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("websockets库未安装，WebSocket功能不可用")


class WebSocketProtocol:
    """WebSocket协议实现类"""
    
    def __init__(self):
        self.connections: Dict[str, 'websockets.WebSocketServerProtocol'] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.is_running = False
        self.server = None
        
        # 统计信息
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'total_messages_sent': 0,
            'total_messages_received': 0,
            'errors': 0
        }
    
    def register_callback(self, event_type: str, callback: Callable):
        """注册事件回调"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
    
    def unregister_callback(self, event_type: str, callback: Callable):
        """取消注册事件回调"""
        if event_type in self.callbacks:
            self.callbacks[event_type].remove(callback)
    
    async def _handle_client(self, websocket, path):
        """处理客户端连接"""
        client_id = f"client_{id(websocket)}_{int(time.time())}"
        self.connections[client_id] = websocket
        self.stats['total_connections'] += 1
        self.stats['active_connections'] += 1
        
        logger.info(f"WebSocket客户端连接: {client_id}")
        
        # 触发连接事件
        await self._trigger_event('connect', {'client_id': client_id})
        
        try:
            async for message in websocket:
                self.stats['total_messages_received'] += 1
                await self._handle_message(client_id, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket客户端断开连接: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket客户端错误: {client_id}, 错误: {str(e)}")
            self.stats['errors'] += 1
        finally:
            if client_id in self.connections:
                del self.connections[client_id]
                self.stats['active_connections'] -= 1
                await self._trigger_event('disconnect', {'client_id': client_id})
                logger.info(f"WebSocket客户端已断开: {client_id}")
    
    async def _handle_message(self, client_id: str, message: str):
        """处理收到的消息"""
        try:
            data = json.loads(message)
            await self._trigger_event('message', {
                'client_id': client_id,
                'data': data
            })
            
            # 回复消息
            response = {
                'status': 'success',
                'received_at': time.time()
            }
            await self.send_message(client_id, response)
        except json.JSONDecodeError:
            logger.error(f"WebSocket消息解析失败: {message}")
            self.stats['errors'] += 1
    
    async def _trigger_event(self, event_type: str, data: Dict[str, Any]):
        """触发事件回调"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"事件回调执行失败: {event_type}, 错误: {str(e)}")
    
    async def send_message(self, client_id: str, data: Dict[str, Any]):
        """发送消息给指定客户端"""
        if client_id in self.connections:
            try:
                message = json.dumps(data, ensure_ascii=False)
                await self.connections[client_id].send(message)
                self.stats['total_messages_sent'] += 1
                return True
            except Exception as e:
                logger.error(f"发送消息失败: {client_id}, 错误: {str(e)}")
                self.stats['errors'] += 1
                return False
        return False
    
    async def broadcast(self, data: Dict[str, Any]):
        """广播消息给所有客户端"""
        message = json.dumps(data, ensure_ascii=False)
        successful = 0
        
        for client_id, websocket in list(self.connections.items()):
            try:
                await websocket.send(message)
                successful += 1
                self.stats['total_messages_sent'] += 1
            except Exception as e:
                logger.error(f"广播消息失败: {client_id}, 错误: {str(e)}")
                self.stats['errors'] += 1
        
        return successful
    
    async def start_server(self, host: str = '0.0.0.0', port: int = 8765):
        """启动WebSocket服务器"""
        if not WEBSOCKETS_AVAILABLE:
            logger.error("websockets库未安装，无法启动WebSocket服务器")
            return False
        
        try:
            self.server = await websockets.serve(
                self._handle_client,
                host,
                port
            )
            self.is_running = True
            logger.info(f"WebSocket服务器已启动: ws://{host}:{port}")
            return True
        except Exception as e:
            logger.error(f"启动WebSocket服务器失败: {str(e)}")
            return False
    
    async def stop_server(self):
        """停止WebSocket服务器"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.is_running = False
            logger.info("WebSocket服务器已停止")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'total_messages_sent': 0,
            'total_messages_received': 0,
            'errors': 0
        }


class WebSocketClient:
    """WebSocket客户端封装类"""
    
    def __init__(self, url: str):
        self.url = url
        self.websocket = None
        self.is_connected = False
        self.callbacks: Dict[str, List[Callable]] = {}
        
    def on_message(self, callback: Callable):
        """注册消息回调"""
        if 'message' not in self.callbacks:
            self.callbacks['message'] = []
        self.callbacks['message'].append(callback)
    
    def on_error(self, callback: Callable):
        """注册错误回调"""
        if 'error' not in self.callbacks:
            self.callbacks['error'] = []
        self.callbacks['error'].append(callback)
    
    async def connect(self):
        """连接到WebSocket服务器"""
        if not WEBSOCKETS_AVAILABLE:
            logger.error("websockets库未安装，无法连接WebSocket服务器")
            return False
        
        try:
            self.websocket = await websockets.connect(self.url)
            self.is_connected = True
            logger.info(f"WebSocket客户端已连接: {self.url}")
            
            # 启动消息监听
            asyncio.create_task(self._listen())
            return True
        except Exception as e:
            logger.error(f"WebSocket连接失败: {str(e)}")
            return False
    
    async def _listen(self):
        """监听消息"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                if 'message' in self.callbacks:
                    for callback in self.callbacks['message']:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(data)
                            else:
                                callback(data)
                        except Exception as e:
                            logger.error(f"消息回调执行失败: {str(e)}")
        except websockets.exceptions.ConnectionClosed:
            self.is_connected = False
            logger.info("WebSocket连接已关闭")
        except Exception as e:
            logger.error(f"WebSocket监听错误: {str(e)}")
            if 'error' in self.callbacks:
                for callback in self.callbacks['error']:
                    try:
                        callback(e)
                    except Exception:
                        pass
    
    async def send(self, data: Dict[str, Any]):
        """发送消息"""
        if self.websocket and self.is_connected:
            try:
                message = json.dumps(data, ensure_ascii=False)
                await self.websocket.send(message)
                return True
            except Exception as e:
                logger.error(f"发送消息失败: {str(e)}")
                return False
        return False
    
    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("WebSocket客户端已关闭")
