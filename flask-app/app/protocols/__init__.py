#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通讯协议模块
提供多种通讯协议支持：HTTP、WebSocket、MQTT、gRPC、私有数据协议等
"""

from .http_protocol import HTTPProtocol
from .websocket_protocol import WebSocketProtocol
from .mqtt_protocol import MQTTProtocol
from .grpc_protocol import gRPCProtocol
from .private_protocol import PrivateDataProtocol, SecureChannel
from .version_history import VersionHistory, VersionTracker, version_history, version_tracker
from .protocol_manager import ProtocolManager

__all__ = [
    'HTTPProtocol',
    'WebSocketProtocol',
    'MQTTProtocol',
    'gRPCProtocol',
    'PrivateDataProtocol',
    'SecureChannel',
    'ProtocolManager',
    'VersionHistory',
    'VersionTracker',
    'protocol_manager',
    'version_history',
    'version_tracker'
]

# 创建全局协议管理器实例
protocol_manager = ProtocolManager()