#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gRPC协议实现模块
提供gRPC远程过程调用支持
"""

import json
import time
from typing import Dict, Any, Optional, Callable
from concurrent import futures
from app.utils.logging import logger

try:
    import grpc
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    logger.warning("grpcio库未安装，gRPC功能不可用")


class gRPCProtocol:
    """gRPC协议实现类"""
    
    def __init__(self):
        self.server = None
        self.channel = None
        self.is_server_running = False
        self.is_client_connected = False
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'avg_response_time': 0.0
        }
    
    def start_server(self, host: str = '0.0.0.0', port: int = 50051, 
                     max_workers: int = 10):
        """启动gRPC服务器"""
        if not GRPC_AVAILABLE:
            logger.error("grpcio库未安装，无法启动gRPC服务器")
            return False
        
        try:
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
            self.server.add_insecure_port(f'{host}:{port}')
            self.server.start()
            self.is_server_running = True
            logger.info(f"gRPC服务器已启动: grpc://{host}:{port}")
            return True
        except Exception as e:
            logger.error(f"启动gRPC服务器失败: {str(e)}")
            return False
    
    def stop_server(self, grace: int = 5):
        """停止gRPC服务器"""
        if self.server:
            self.server.stop(grace)
            self.is_server_running = False
            logger.info("gRPC服务器已停止")
    
    def connect_to_server(self, server_address: str):
        """连接到gRPC服务器"""
        if not GRPC_AVAILABLE:
            logger.error("grpcio库未安装，无法连接gRPC服务器")
            return False
        
        try:
            self.channel = grpc.insecure_channel(server_address)
            self.is_client_connected = True
            logger.info(f"gRPC客户端已连接: {server_address}")
            return True
        except Exception as e:
            logger.error(f"gRPC连接失败: {str(e)}")
            return False
    
    def disconnect_from_server(self):
        """断开与gRPC服务器的连接"""
        if self.channel:
            self.channel.close()
            self.is_client_connected = False
            logger.info("gRPC客户端已断开")
    
    def add_service(self, service, implementation):
        """添加gRPC服务"""
        if self.server:
            try:
                service.add_implementation_to_server(implementation, self.server)
                logger.info(f"gRPC服务已注册: {service.__name__}")
                return True
            except Exception as e:
                logger.error(f"注册gRPC服务失败: {str(e)}")
                return False
        return False
    
    def make_call(self, stub_class, method_name: str, request, **kwargs):
        """调用gRPC方法"""
        if not self.channel:
            logger.error("gRPC通道未建立")
            return None
        
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            stub = stub_class(self.channel)
            method = getattr(stub, method_name)
            response = method(request, **kwargs)
            
            response_time = time.time() - start_time
            self.stats['total_response_time'] += response_time
            self.stats['successful_requests'] += 1
            self.stats['avg_response_time'] = (
                self.stats['total_response_time'] / self.stats['successful_requests']
            )
            
            return response
        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"gRPC调用失败: {method_name}, 错误: {str(e)}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'avg_response_time': 0.0
        }


class gRPCClient:
    """gRPC客户端封装类"""
    
    def __init__(self, server_address: str = None):
        self.protocol = gRPCProtocol()
        self.server_address = server_address
        
    def connect(self, server_address: str = None):
        """连接到gRPC服务器"""
        address = server_address or self.server_address
        return self.protocol.connect_to_server(address)
    
    def disconnect(self):
        """断开连接"""
        self.protocol.disconnect_from_server()
    
    def call(self, stub_class, method_name: str, request, **kwargs):
        """调用gRPC方法"""
        return self.protocol.make_call(stub_class, method_name, request, **kwargs)
    
    def get_stats(self):
        """获取统计信息"""
        return self.protocol.get_stats()


class gRPCServiceBase:
    """gRPC服务基类"""
    
    def __init__(self):
        self.logger = logger
    
    def log_request(self, method_name: str, request):
        """记录请求日志"""
        self.logger.info(f"gRPC请求: {method_name}")
    
    def log_response(self, method_name: str, response):
        """记录响应日志"""
        self.logger.info(f"gRPC响应: {method_name}")
