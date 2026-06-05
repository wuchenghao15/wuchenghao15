#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT协议实现模块
提供MQTT消息队列协议支持
"""

import json
import time
from typing import Dict, Any, Optional, Callable, List
from app.utils.logging import logger

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logger.warning("paho-mqtt库未安装，MQTT功能不可用")


class MQTTProtocol:
    """MQTT协议实现类"""
    
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.callbacks: Dict[str, List[Callable]] = {}
        self.topics_subscribed = []
        
        # 统计信息
        self.stats = {
            'total_messages_published': 0,
            'total_messages_received': 0,
            'total_connections': 0,
            'errors': 0
        }
    
    def register_callback(self, topic: str, callback: Callable):
        """注册主题消息回调"""
        if topic not in self.callbacks:
            self.callbacks[topic] = []
        self.callbacks[topic].append(callback)
    
    def unregister_callback(self, topic: str, callback: Callable):
        """取消注册主题消息回调"""
        if topic in self.callbacks:
            self.callbacks[topic].remove(callback)
    
    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            self.is_connected = True
            self.stats['total_connections'] += 1
            logger.info("MQTT连接成功")
            
            # 重新订阅所有主题
            for topic in self.topics_subscribed:
                self.client.subscribe(topic)
                logger.info(f"MQTT订阅主题: {topic}")
        else:
            logger.error(f"MQTT连接失败，错误码: {rc}")
            self.stats['errors'] += 1
    
    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        self.is_connected = False
        logger.info(f"MQTT断开连接，原因: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """消息回调"""
        try:
            payload = msg.payload.decode('utf-8')
            data = json.loads(payload)
            self.stats['total_messages_received'] += 1
            
            # 触发主题回调
            if msg.topic in self.callbacks:
                for callback in self.callbacks[msg.topic]:
                    try:
                        callback(msg.topic, data)
                    except Exception as e:
                        logger.error(f"MQTT回调执行失败: {str(e)}")
            
            # 触发通配符回调
            for topic_pattern in self.callbacks:
                if self._match_topic(topic_pattern, msg.topic):
                    for callback in self.callbacks[topic_pattern]:
                        try:
                            callback(msg.topic, data)
                        except Exception as e:
                            logger.error(f"MQTT通配符回调执行失败: {str(e)}")
        except json.JSONDecodeError:
            logger.error(f"MQTT消息解析失败: {payload}")
            self.stats['errors'] += 1
        except Exception as e:
            logger.error(f"MQTT消息处理失败: {str(e)}")
            self.stats['errors'] += 1
    
    def _match_topic(self, pattern: str, topic: str) -> bool:
        """匹配主题模式"""
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
    
    def connect(self, broker_host: str = 'localhost', broker_port: int = 1883, 
                client_id: str = None, username: str = None, password: str = None,
                keepalive: int = 60):
        """连接到MQTT代理"""
        if not MQTT_AVAILABLE:
            logger.error("paho-mqtt库未安装，无法连接MQTT")
            return False
        
        try:
            if client_id is None:
                client_id = f"mtscos_{int(time.time())}"
            
            self.client = mqtt.Client(client_id=client_id)
            
            if username and password:
                self.client.username_pw_set(username, password)
            
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            self.client.connect(broker_host, broker_port, keepalive)
            self.client.loop_start()
            
            return True
        except Exception as e:
            logger.error(f"MQTT连接失败: {str(e)}")
            self.stats['errors'] += 1
            return False
    
    def disconnect(self):
        """断开MQTT连接"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
            logger.info("MQTT已断开连接")
    
    def subscribe(self, topic: str, qos: int = 0):
        """订阅主题"""
        if self.client and self.is_connected:
            try:
                self.client.subscribe(topic, qos)
                if topic not in self.topics_subscribed:
                    self.topics_subscribed.append(topic)
                logger.info(f"MQTT订阅主题: {topic}")
                return True
            except Exception as e:
                logger.error(f"MQTT订阅失败: {str(e)}")
                self.stats['errors'] += 1
                return False
        return False
    
    def unsubscribe(self, topic: str):
        """取消订阅主题"""
        if self.client and self.is_connected:
            try:
                self.client.unsubscribe(topic)
                if topic in self.topics_subscribed:
                    self.topics_subscribed.remove(topic)
                logger.info(f"MQTT取消订阅主题: {topic}")
                return True
            except Exception as e:
                logger.error(f"MQTT取消订阅失败: {str(e)}")
                return False
        return False
    
    def publish(self, topic: str, data: Dict[str, Any], qos: int = 0, retain: bool = False):
        """发布消息"""
        if self.client and self.is_connected:
            try:
                payload = json.dumps(data, ensure_ascii=False)
                result = self.client.publish(topic, payload, qos=qos, retain=retain)
                result.wait_for_publish()
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    self.stats['total_messages_published'] += 1
                    return True
                else:
                    logger.error(f"MQTT发布失败，错误码: {result.rc}")
                    self.stats['errors'] += 1
                    return False
            except Exception as e:
                logger.error(f"MQTT发布失败: {str(e)}")
                self.stats['errors'] += 1
                return False
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_messages_published': 0,
            'total_messages_received': 0,
            'total_connections': 0,
            'errors': 0
        }


class MQTTClient:
    """MQTT客户端封装类"""
    
    def __init__(self):
        self.protocol = MQTTProtocol()
    
    def connect(self, **kwargs):
        """连接到MQTT代理"""
        return self.protocol.connect(**kwargs)
    
    def disconnect(self):
        """断开连接"""
        self.protocol.disconnect()
    
    def subscribe(self, topic: str, callback: Callable = None, qos: int = 0):
        """订阅主题"""
        if callback:
            self.protocol.register_callback(topic, callback)
        return self.protocol.subscribe(topic, qos)
    
    def unsubscribe(self, topic: str):
        """取消订阅主题"""
        return self.protocol.unsubscribe(topic)
    
    def publish(self, topic: str, data: Dict[str, Any], **kwargs):
        """发布消息"""
        return self.protocol.publish(topic, data, **kwargs)
    
    def get_stats(self):
        """获取统计信息"""
        return self.protocol.get_stats()
