#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
负载均衡管理API - 提供负载均衡器状态查询和管理接口
"""

from flask import Blueprint, jsonify, request
import json
import threading
from datetime import datetime

load_balancer_api = Blueprint('load_balancer_api', __name__)

# 全局负载均衡器实例
lb_instance = None
lb_lock = threading.Lock()

def init_load_balancer():
    """初始化负载均衡器"""
    global lb_instance
    with lb_lock:
        if lb_instance is None:
            from cluster.load_balancer import get_load_balancer
            lb_instance = get_load_balancer()
            lb_instance.start()
    return lb_instance

def get_lb():
    """获取负载均衡器实例"""
    if lb_instance is None:
        return init_load_balancer()
    return lb_instance

@load_balancer_api.route('/')
def index():
    return jsonify({'status': 'ok', 'service': 'load-balancer-api'})

@load_balancer_api.route('/status')
def status():
    """获取负载均衡器状态"""
    lb = get_lb()
    return jsonify(lb.get_status())

@load_balancer_api.route('/nodes')
def nodes():
    """获取节点列表"""
    lb = get_lb()
    return jsonify({'nodes': lb.nodes})

@load_balancer_api.route('/nodes/<node_id>')
def node_detail(node_id):
    """获取单个节点详情"""
    lb = get_lb()
    node = next((n for n in lb.nodes if n['id'] == node_id), None)
    if node:
        return jsonify(node)
    return jsonify({'error': '节点不存在'}), 404

@load_balancer_api.route('/nodes', methods=['POST'])
def add_node():
    """添加节点"""
    lb = get_lb()
    data = request.get_json()
    
    if not data or 'host' not in data or 'port' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    lb.add_node(data)
    return jsonify({'success': True, 'message': '节点添加成功'})

@load_balancer_api.route('/nodes/<node_id>', methods=['DELETE'])
def remove_node(node_id):
    """移除节点"""
    lb = get_lb()
    lb.remove_node(node_id)
    return jsonify({'success': True, 'message': '节点移除成功'})

@load_balancer_api.route('/algorithm')
def get_algorithm():
    """获取当前算法"""
    lb = get_lb()
    return jsonify({'algorithm': lb.algorithm.value})

@load_balancer_api.route('/algorithm', methods=['POST'])
def set_algorithm():
    """设置负载均衡算法"""
    lb = get_lb()
    data = request.get_json()
    
    if not data or 'algorithm' not in data:
        return jsonify({'error': '缺少算法参数'}), 400
    
    algorithm = data['algorithm']
    if lb.set_algorithm(algorithm):
        return jsonify({'success': True, 'message': f'算法已切换为 {algorithm}'})
    return jsonify({'success': False, 'message': '无效的算法'}), 400

@load_balancer_api.route('/algorithms')
def list_algorithms():
    """列出支持的算法"""
    from cluster.load_balancer import LoadBalancingAlgorithm
    algorithms = [{'name': algo.value, 'description': get_algorithm_description(algo.value)} 
                  for algo in LoadBalancingAlgorithm]
    return jsonify({'algorithms': algorithms})

def get_algorithm_description(algorithm: str) -> str:
    """获取算法描述"""
    descriptions = {
        'round_robin': '轮询算法 - 依次将请求分配到各个节点',
        'least_connections': '最小连接数 - 将请求分配到连接数最少的节点',
        'weighted_round_robin': '加权轮询 - 根据权重分配请求',
        'ip_hash': 'IP哈希 - 根据客户端IP分配到固定节点',
        'random': '随机算法 - 随机选择节点'
    }
    return descriptions.get(algorithm, '未知算法')

@load_balancer_api.route('/metrics')
def metrics():
    """获取性能指标"""
    lb = get_lb()
    status = lb.get_status()
    return jsonify(status['metrics'])

@load_balancer_api.route('/health')
def health():
    """健康检查"""
    lb = get_lb()
    healthy_count = sum(1 for node in lb.nodes if node['status'] == 'healthy')
    return jsonify({
        'status': 'healthy' if healthy_count > 0 else 'unhealthy',
        'healthy_nodes': healthy_count,
        'total_nodes': len(lb.nodes),
        'timestamp': datetime.now().isoformat()
    })

@load_balancer_api.route('/test/select')
def test_select():
    """测试节点选择"""
    lb = get_lb()
    client_ip = request.remote_addr
    node = lb.select_node(client_ip)
    
    if node:
        return jsonify({
            'selected_node': node,
            'client_ip': client_ip
        })
    return jsonify({'error': '没有可用节点'}), 503

@load_balancer_api.route('/stats')
def stats():
    """获取统计信息"""
    lb = get_lb()
    status = lb.get_status()
    
    stats = {
        'algorithm': status['algorithm'],
        'status': status['status'],
        'total_requests': status['metrics']['total_requests'],
        'success_rate': f"{status['metrics']['success_rate']:.2f}%",
        'avg_response_time_ms': f"{status['metrics']['avg_response_time_ms']:.2f}",
        'uptime': status['metrics']['uptime'],
        'nodes': [{
            'id': node['id'],
            'status': node['status'],
            'connections': node['connections'],
            'health_score': node['health_score']
        } for node in status['nodes']]
    }
    return jsonify(stats)
