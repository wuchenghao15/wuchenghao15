# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
集群管理模块
负责管理服务器集群中的节点通信,健康检查,数据同步和领导者选举
"""

import logging
import threading
import time
import requests
from app.config import load_config
import json
import sys
import os

logger = logging.getLogger(__name__)

class ClusterManager:
    """集群管理器,负责管理服务器集群"""
    
    def __init__(self):
        self.config = load_config()
        self.cluster_enabled = self.config.get('CLUSTER_ENABLED', False)
        self.cluster_nodes = self.config.get('CLUSTER_NODES', [])
        self.node_id = self.config.get('CLUSTER_NODE_ID', 'node-1')
        self.node_role = self.config.get('CLUSTER_NODE_ROLE', 'worker')
        self.communication_port = self.config.get('CLUSTER_COMMUNICATION_PORT', 9999)
        self.health_check_interval = self.config.get('CLUSTER_HEALTH_CHECK_INTERVAL', 30)
        self.data_sync_interval = self.config.get('CLUSTER_DATA_SYNC_INTERVAL', 60)
        self.leader_election_enabled = self.config.get('CLUSTER_LEADER_ELECTION_ENABLED', True)
        self.leader_election_timeout = self.config.get('CLUSTER_LEADER_ELECTION_TIMEOUT', 10)
        self.leader_heartbeat_interval = self.config.get('CLUSTER_LEADER_HEARTBEAT_INTERVAL', 5)
        self.monitoring_enabled = self.config.get('CLUSTER_MONITORING_ENABLED', True)

        self.node_statuses = {}
        self.leader_node = None
        self.leader_last_seen = 0
        self.is_leader = False
        self.heartbeat_thread = None
        self.health_check_thread = None
        self.data_sync_thread = None
        self.leader_election_thread = None

        self.status_lock = threading.Lock()
        self.leader_lock = threading.Lock()

        logger.info(f"[集群管理] 初始化集群管理器,节点ID: {self.node_id}, 角色: {self.node_role}")

    def start(self):
        """启动集群管理器"""
        if not self.cluster_enabled:
            logger.info("[集群管理] 集群模式未启用,跳过集群管理器启动")
            return

        logger.info("[集群管理] 启动集群管理器...")

        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_check_thread.start()
        logger.info("[集群管理] 健康检查线程已启动")

        self.data_sync_thread = threading.Thread(target=self._data_sync_loop, daemon=True)
        self.data_sync_thread.start()
        logger.info("[集群管理] 数据同步线程已启动")

        if self.leader_election_enabled:
            self.leader_election_thread = threading.Thread(target=self._leader_election_loop, daemon=True)
            self.leader_election_thread.start()
            logger.info("[集群管理] 领导者选举线程已启动")

        if self.node_role in ['master', 'source']:
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()
            logger.info("[集群管理] 领导者心跳线程已启动")

        logger.info("[集群管理] 集群管理器启动完成")

    def stop(self):
        """停止集群管理器"""
        logger.info("[集群管理] 停止集群管理器...")

        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
        if self.data_sync_thread:
            self.data_sync_thread.join(timeout=5)
        if self.leader_election_thread:
            self.leader_election_thread.join(timeout=5)
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)

        logger.info("[集群管理] 集群管理器已停止")

    def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                self._check_nodes_health()
            except Exception as e:
                logger.error(f"[集群管理] 健康检查失败: {str(e)}")
            time.sleep(self.health_check_interval)

    def _check_nodes_health(self):
        """检查所有节点的健康状态"""
        logger.info("[集群管理] 开始健康检查...")

        for node in self.cluster_nodes:
            try:
                response = requests.get(f"http://{node}/health", timeout=5)
                status = "healthy" if response.status_code == 200 else "unhealthy"
                with self.status_lock:
                    self.node_statuses[node] = {
                        "status": status,
                        "last_check": time.time(),
                        "response_code": response.status_code
                    }
                logger.info(f"[集群管理] 节点 {node} 健康状态: {status}")
            except Exception as e:
                logger.error(f"[集群管理] 节点 {node} 健康检查失败: {str(e)}")
                with self.status_lock:
                    self.node_statuses[node] = {
                        "status": "unhealthy",
                        "last_check": time.time(),
                        "error": str(e)
                    }

        logger.info("[集群管理] 健康检查完成")

    def _data_sync_loop(self):
        """数据同步循环"""
        while True:
            try:
                self._sync_data()
            except Exception as e:
                logger.error(f"[集群管理] 数据同步失败: {str(e)}")
            time.sleep(self.data_sync_interval)

    def _sync_data(self):
        """同步数据 - 从领导者节点同步数据到当前节点"""
        logger.info("[集群管理] 开始数据同步...")

        try:
            if not self.leader_node:
                return

            if self.is_leader:
                logger.info("[集群管理] 当前节点是领导者,不需要同步数据")
                return

            leader_url = f"http://{self.leader_node}"

            logger.info(f"[集群管理] 从领导者 {self.leader_node} 同步系统配置...")
            try:
                config_response = requests.get(f"{leader_url}/api/cluster/config", timeout=10)
                if config_response.status_code == 200:
                    config_data = config_response.json()
                    if config_data.get('success'):
                        logger.info("[集群管理] 系统配置同步成功")
            except Exception as e:
                logger.error(f"[集群管理] 同步系统配置失败: {str(e)}")

            logger.info(f"[集群管理] 从领导者 {self.leader_node} 同步AI模型状态...")
            try:
                ai_response = requests.get(f"{leader_url}/api/ai-brain/status", timeout=10)
                if ai_response.status_code == 200:
                    ai_data = ai_response.json()
                    if ai_data.get('success'):
                        logger.info("[集群管理] AI模型状态同步成功")
                    else:
                        logger.error(f"[集群管理] AI模型状态同步失败: {ai_data.get('message')}")
            except Exception as e:
                logger.error(f"[集群管理] 同步AI模型状态失败: {str(e)}")

            logger.info(f"[集群管理] 从领导者 {self.leader_node} 同步数据库数据...")
            try:
                db_response = requests.get(f"{leader_url}/api/server-system/db/status", timeout=15)
                if db_response.status_code == 200:
                    db_data = db_response.json()
                    if db_data.get('success'):
                        logger.info("[集群管理] 数据库状态同步成功")
                    else:
                        logger.error(f"[集群管理] 数据库状态同步失败: {db_data.get('message')}")
            except Exception as e:
                logger.error(f"[集群管理] 同步数据库数据失败: {str(e)}")

        except Exception as e:
            logger.error(f"[集群管理] 数据同步过程中发生错误: {str(e)}")

        logger.info("[集群管理] 数据同步完成")

    def _leader_election_loop(self):
        """领导者选举循环"""
        while True:
            try:
                self._check_leader_status()
            except Exception as e:
                logger.error(f"[集群管理] 领导者选举失败: {str(e)}")
            time.sleep(self.leader_election_timeout)

    def _check_leader_status(self):
        """检查领导者状态"""
        with self.leader_lock:
            if self.leader_node and (time.time() - self.leader_last_seen) > 2 * self.leader_heartbeat_interval:
                logger.warning(f"[集群管理] 领导者 {self.leader_node} 心跳超时,开始重新选举领导者")
                self._elect_leader()

    def _elect_leader(self):
        """选举领导者"""
        with self.status_lock:
            healthy_nodes = [node for node, status in self.node_statuses.items() if status.get('status') == 'healthy']
        
        if healthy_nodes:
            new_leader = healthy_nodes[0]
            with self.leader_lock:
                self.leader_node = new_leader
                self.leader_last_seen = time.time()
                self.is_leader = (new_leader == self._get_current_node_address())
            logger.info(f"[集群管理] 新领导者选举完成: {new_leader}, 当前节点是否为领导者: {self.is_leader}")
        else:
            logger.warning("[集群管理] 没有健康的节点可选举为领导者")

    def _heartbeat_loop(self):
        """领导者心跳循环"""
        while True:
            try:
                self._send_heartbeat()
            except Exception as e:
                logger.error(f"[集群管理] 发送心跳失败: {str(e)}")
            time.sleep(self.leader_heartbeat_interval)

    def _send_heartbeat(self):
        """发送领导者心跳"""
        logger.debug(f"[集群管理] 领导者 {self.node_id} 发送心跳")

    def _get_current_node_address(self):
        """获取当前节点的地址"""
        host = self.config.get('SERVER_HOST', '0.0.0.0')
        if host == '0.0.0.0':
            host = '127.0.0.1'
        port = self.config.get('SERVER_PORT', 8888)
        return f"{host}:{port}"

    def get_cluster_status(self):
        """获取集群状态"""
        with self.status_lock:
            node_statuses = self.node_statuses.copy()
        with self.leader_lock:
            return {
                "enabled": self.cluster_enabled,
                "leader_node": self.leader_node,
                "is_leader": self.is_leader,
                "current_node_id": self.node_id,
                "current_node_role": self.node_role,
                "nodes": node_statuses,
                "cluster_nodes": self.cluster_nodes,
                "last_leader_seen": self.leader_last_seen
            }

    def get_healthy_nodes(self):
        """获取健康的节点列表"""
        with self.status_lock:
            return [node for node, status in self.node_statuses.items() if status.get('status') == 'healthy']

    def get_unhealthy_nodes(self):
        """获取不健康的节点列表"""
        with self.status_lock:
            return [node for node, status in self.node_statuses.items() if status.get('status') != 'healthy']

    def join_cluster(self, node_address: str):
        """加入集群"""
        logger.info(f"[集群管理] 尝试加入节点 {node_address} 到集群")
        with self.status_lock:
            if node_address not in self.cluster_nodes:
                self.cluster_nodes.append(node_address)
                logger.info(f"[集群管理] 节点 {node_address} 已成功加入集群")
            else:
                logger.info(f"[集群管理] 节点 {node_address} 已经在集群中")

    def leave_cluster(self, node_address: str):
        """离开集群"""
        logger.info(f"[集群管理] 尝试移除节点 {node_address} 从集群")
        with self.status_lock:
            if node_address in self.cluster_nodes:
                self.cluster_nodes.remove(node_address)
                logger.info(f"[集群管理] 节点 {node_address} 已成功从集群移除")
            else:
                logger.info(f"[集群管理] 节点 {node_address} 不在集群中")

cluster_manager = ClusterManager()