# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集群管理API - 提供集群状态查询和管理接口
"""

from flask import Blueprint, jsonify, request
import json
import time
from datetime import datetime
import os

cluster_api_bp = Blueprint('cluster_api', __name__)

# 模拟集群管理器
class MockClusterManager:
    def __init__(self):
        self.nodes = {
            'node-master': {'name': '主节点', 'role': 'master', 'status': 'healthy', 'host': '127.0.0.1', 'port': 8443},
            'node-worker-1': {'name': '工作节点1', 'role': 'worker', 'status': 'healthy', 'host': '127.0.0.1', 'port': 8444},
            'node-worker-2': {'name': '工作节点2', 'role': 'worker', 'status': 'healthy', 'host': '127.0.0.1', 'port': 8445}
        }
        self.current_master = 'node-master'
        self.start_time = datetime.now().isoformat()
    
    def get_status(self):
        return {
            'cluster_name': 'mtscos-cluster',
            'status': 'healthy',
            'nodes': self.nodes,
            'master': self.current_master,
            'node_count': len(self.nodes),
            'start_time': self.start_time,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_nodes(self):
        return list(self.nodes.values())
    
    def get_node(self, node_id):
        return self.nodes.get(node_id)
    
    def add_node(self, node_config):
        node_id = node_config['id']
        self.nodes[node_id] = node_config
        return True
    
    def remove_node(self, node_id):
        if node_id in self.nodes:
            del self.nodes[node_id]
            return True
        return False

cluster_manager = MockClusterManager()

@cluster_api_bp.route('/')
def index():
    return jsonify({'status': 'ok', 'service': 'cluster-api'})

@cluster_api_bp.route('/status')
def status():
    return jsonify(cluster_manager.get_status())

@cluster_api_bp.route('/nodes')
def nodes():
    return jsonify({'nodes': cluster_manager.get_nodes()})

@cluster_api_bp.route('/nodes/<node_id>')
def node_detail(node_id):
    node = cluster_manager.get_node(node_id)
    if node:
        return jsonify(node)
    return jsonify({'error': '节点不存在'}), 404

@cluster_api_bp.route('/nodes', methods=['POST'])
def add_node():
    data = request.get_json()
    if cluster_manager.add_node(data):
        return jsonify({'success': True, 'message': '节点添加成功'})
    return jsonify({'success': False, 'message': '节点添加失败'}), 500

@cluster_api_bp.route('/nodes/<node_id>', methods=['DELETE'])
def remove_node(node_id):
    if cluster_manager.remove_node(node_id):
        return jsonify({'success': True, 'message': '节点移除成功'})
    return jsonify({'success': False, 'message': '节点不存在'}), 404

@cluster_api_bp.route('/master')
def master():
    master_node = cluster_manager.get_node(cluster_manager.current_master)
    return jsonify(master_node)

@cluster_api_bp.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@cluster_api_bp.route('/metrics')
def metrics():
    return jsonify({
        'cpu_usage': {'master': 35, 'worker-1': 28, 'worker-2': 42},
        'memory_usage': {'master': 45, 'worker-1': 38, 'worker-2': 41},
        'connections': {'master': 120, 'worker-1': 85, 'worker-2': 95},
        'requests_per_second': 45.6,
        'response_time_ms': 12.3
    })
