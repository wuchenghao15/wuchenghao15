#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
协议管理器模块
统一管理和协调所有通讯协议
"""

import json
import time
from typing import Dict, Any, Optional, Callable, List
from app.utils.logging import logger


class ProtocolManager:
    """协议管理器类"""
    
    def __init__(self):
        self.protocols: Dict[str, Any] = {}
        self.protocol_configs: Dict[str, Dict[str, Any]] = {}
        self.active_protocols: List[str] = []
        
        # 协议状态
        self.protocol_status: Dict[str, bool] = {}
        
        # 消息路由表
        self.message_routes: Dict[str, List[Callable]] = {}
        
        # 统计信息
        self.global_stats = {
            'total_protocols': 0,
            'active_protocols': 0,
            'total_messages': 0,
            'total_requests': 0,
            'errors': 0
        }
    
    def register_protocol(self, protocol_name: str, protocol_instance, config: Optional[Dict[str, Any]] = None):
        """注册协议"""
        self.protocols[protocol_name] = protocol_instance
        if config:
            self.protocol_configs[protocol_name] = config
        else:
            self.protocol_configs[protocol_name] = {}
        
        self.protocol_status[protocol_name] = False
        self.global_stats['total_protocols'] += 1
        
        logger.info(f"协议已注册: {protocol_name}")
    
    def unregister_protocol(self, protocol_name: str):
        """注销协议"""
        if protocol_name in self.protocols:
            self.stop_protocol(protocol_name)
            del self.protocols[protocol_name]
            del self.protocol_configs[protocol_name]
            del self.protocol_status[protocol_name]
            self.global_stats['total_protocols'] -= 1
            logger.info(f"协议已注销: {protocol_name}")
    
    def start_protocol(self, protocol_name: str, **kwargs) -> bool:
        """启动协议"""
        if protocol_name not in self.protocols:
            logger.error(f"协议未注册: {protocol_name}")
            return False
        
        try:
            protocol = self.protocols[protocol_name]
            
            # 根据协议类型调用不同的启动方法
            if hasattr(protocol, 'start_server'):
                config = self.protocol_configs.get(protocol_name, {})
                config.update(kwargs)
                host = config.get('host', '0.0.0.0')
                port = config.get('port', self._get_default_port(protocol_name))
                result = protocol.start_server(host=host, port=port)
            elif hasattr(protocol, 'connect'):
                config = self.protocol_configs.get(protocol_name, {})
                config.update(kwargs)
                result = protocol.connect(**config)
            else:
                result = True
            
            if result:
                self.protocol_status[protocol_name] = True
                if protocol_name not in self.active_protocols:
                    self.active_protocols.append(protocol_name)
                self.global_stats['active_protocols'] += 1
                logger.info(f"协议已启动: {protocol_name}")
            else:
                logger.error(f"启动协议失败: {protocol_name}")
            
            return result
        except Exception as e:
            logger.error(f"启动协议异常: {protocol_name}, 错误: {str(e)}")
            self.global_stats['errors'] += 1
            return False
    
    def stop_protocol(self, protocol_name: str):
        """停止协议"""
        if protocol_name not in self.protocols:
            return
        
        try:
            protocol = self.protocols[protocol_name]
            
            # 根据协议类型调用不同的停止方法
            if hasattr(protocol, 'stop_server'):
                protocol.stop_server()
            elif hasattr(protocol, 'disconnect'):
                protocol.disconnect()
            elif hasattr(protocol, 'close'):
                protocol.close()
            
            self.protocol_status[protocol_name] = False
            if protocol_name in self.active_protocols:
                self.active_protocols.remove(protocol_name)
            self.global_stats['active_protocols'] -= 1
            logger.info(f"协议已停止: {protocol_name}")
        except Exception as e:
            logger.error(f"停止协议异常: {protocol_name}, 错误: {str(e)}")
            self.global_stats['errors'] += 1
    
    def start_all_protocols(self):
        """启动所有已注册的协议"""
        for protocol_name in self.protocols.keys():
            if not self.protocol_status[protocol_name]:
                self.start_protocol(protocol_name)
    
    def stop_all_protocols(self):
        """停止所有运行中的协议"""
        for protocol_name in list(self.active_protocols):
            self.stop_protocol(protocol_name)
    
    def send_message(self, protocol_name: str, target: str, data: Dict[str, Any], **kwargs) -> bool:
        """发送消息"""
        if protocol_name not in self.protocols:
            logger.error(f"协议未注册: {protocol_name}")
            return False
        
        if not self.protocol_status[protocol_name]:
            logger.error(f"协议未启动: {protocol_name}")
            return False
        
        try:
            protocol = self.protocols[protocol_name]
            
            # 根据协议类型调用不同的发送方法
            if hasattr(protocol, 'send_message'):
                return protocol.send_message(target, data, **kwargs)
            elif hasattr(protocol, 'broadcast'):
                return protocol.broadcast(data, **kwargs)
            elif hasattr(protocol, 'publish'):
                return protocol.publish(target, data, **kwargs)
            elif hasattr(protocol, 'post'):
                return protocol.post(target, data, **kwargs)
            elif hasattr(protocol, 'send'):
                return protocol.send(data, **kwargs)
            
            logger.error(f"协议不支持消息发送: {protocol_name}")
            return False
        except Exception as e:
            logger.error(f"发送消息失败: {protocol_name}, 错误: {str(e)}")
            self.global_stats['errors'] += 1
            return False
    
    def broadcast_message(self, data: Dict[str, Any]):
        """广播消息到所有活动协议"""
        for protocol_name in self.active_protocols:
            try:
                self.send_message(protocol_name, '', data)
            except Exception as e:
                logger.error(f"广播消息失败: {protocol_name}, 错误: {str(e)}")
    
    def register_message_handler(self, topic: str, callback: Callable):
        """注册消息处理器"""
        if topic not in self.message_routes:
            self.message_routes[topic] = []
        self.message_routes[topic].append(callback)
    
    def unregister_message_handler(self, topic: str, callback: Callable):
        """注销消息处理器"""
        if topic in self.message_routes:
            self.message_routes[topic].remove(callback)
    
    def route_message(self, topic: str, data: Dict[str, Any]):
        """路由消息到处理器"""
        if topic in self.message_routes:
            for callback in self.message_routes[topic]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"消息处理器执行失败: {topic}, 错误: {str(e)}")
                    self.global_stats['errors'] += 1
        
        # 触发通配符处理器
        for pattern in self.message_routes:
            if self._match_topic(pattern, topic):
                for callback in self.message_routes[pattern]:
                    try:
                        callback(data)
                    except Exception as e:
                        logger.error(f"通配符处理器执行失败: {pattern}, 错误: {str(e)}")
    
    def _match_topic(self, pattern: str, topic: str) -> bool:
        """匹配主题模式"""
        if pattern == '*':
            return True
        if pattern == topic:
            return True
        
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        for p, t in zip(pattern_parts, topic_parts):
            if p == '#':
                return True
            if p == '+':
                continue
            if p != t:
                return False
        
        return len(pattern_parts) == len(topic_parts)
    
    def _get_default_port(self, protocol_name: str) -> int:
        """获取协议默认端口"""
        port_map = {
            'http': 8080,
            'https': 443,
            'websocket': 8765,
            'mqtt': 1883,
            'grpc': 50051
        }
        return port_map.get(protocol_name.lower(), 8080)
    
    def get_protocol_status(self, protocol_name: str) -> bool:
        """获取协议状态"""
        return self.protocol_status.get(protocol_name, False)
    
    def get_all_protocols(self) -> Dict[str, bool]:
        """获取所有协议状态"""
        return self.protocol_status.copy()
    
    def get_protocol_stats(self, protocol_name: str) -> Optional[Dict[str, Any]]:
        """获取协议统计信息"""
        if protocol_name not in self.protocols:
            return None
        
        protocol = self.protocols[protocol_name]
        if hasattr(protocol, 'get_stats'):
            return protocol.get_stats()
        return None
    
    def get_global_stats(self) -> Dict[str, Any]:
        """获取全局统计信息"""
        return self.global_stats.copy()
    
    def reset_stats(self):
        """重置所有统计信息"""
        for protocol in self.protocols.values():
            if hasattr(protocol, 'reset_stats'):
                protocol.reset_stats()
        
        self.global_stats = {
            'total_protocols': len(self.protocols),
            'active_protocols': len(self.active_protocols),
            'total_messages': 0,
            'total_requests': 0,
            'errors': 0
        }
    
    def get_protocol_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有协议信息"""
        info = {}
        for name, protocol in self.protocols.items():
            info[name] = {
                'status': self.protocol_status.get(name, False),
                'config': self.protocol_configs.get(name, {}),
                'stats': protocol.get_stats() if hasattr(protocol, 'get_stats') else {}
            }
        return info
    
    def save_config(self, filepath: str):
        """保存配置到文件"""
        config = {
            'protocols': self.protocol_configs,
            'message_routes': self.message_routes.keys()
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info(f"协议配置已保存: {filepath}")
    
    def load_config(self, filepath: str):
        """从文件加载配置"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if 'protocols' in config:
                self.protocol_configs = config['protocols']
            
            logger.info(f"协议配置已加载: {filepath}")
            return True
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
            return False


# 创建全局协议管理器实例
protocol_manager = ProtocolManager()
