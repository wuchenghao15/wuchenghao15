# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分布式业务管理API - 提供微服务管理、服务发现、分布式协调接口
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime

distributed_business_api = Blueprint('distributed_business_api', __name__)

# 全局分布式业务管理器实例
distributed_manager_instance = None

def init_distributed_manager():
    """初始化分布式业务管理器"""
    global distributed_manager_instance
    if distributed_manager_instance is None:
        from app.utils.distributed_business_manager import get_distributed_manager
        distributed_manager_instance = get_distributed_manager()
    return distributed_manager_instance

def get_distributed_manager():
    """获取分布式业务管理器实例"""
    if distributed_manager_instance is None:
        return init_distributed_manager()
    return distributed_manager_instance

@distributed_business_api.route('/')
def index():
    return jsonify({'status': 'ok', 'service': 'distributed-business-api'})

@distributed_business_api.route('/services')
def list_services():
    """获取所有服务"""
    manager = get_distributed_manager()
    services = manager.get_all_services()
    return jsonify(services)

@distributed_business_api.route('/services/<service_name>')
def get_service(service_name):
    """获取服务详情"""
    manager = get_distributed_manager()
    service = manager.get_service_status(service_name)
    
    if service:
        return jsonify(service)
    return jsonify({'error': '服务不存在'}), 404

@distributed_business_api.route('/services/<service_name>/status')
def get_service_status(service_name):
    """获取服务状态"""
    manager = get_distributed_manager()
    service = manager.get_service_status(service_name)
    
    if service:
        return jsonify({'status': service['status']})
    return jsonify({'error': '服务不存在'}), 404

@distributed_business_api.route('/services/start', methods=['POST'])
def start_services():
    """启动服务"""
    manager = get_distributed_manager()
    data = request.get_json()
    
    if data and 'services' in data:
        # 启动指定服务
        for service_name in data['services']:
            if service_name in manager.modules:
                manager.modules[service_name].start()
        return jsonify({'success': True, 'message': f"启动服务: {data['services']}"})
    else:
        # 启动所有服务
        manager.start_all()
        return jsonify({'success': True, 'message': '所有服务已启动'})

@distributed_business_api.route('/services/stop', methods=['POST'])
def stop_services():
    """停止服务"""
    manager = get_distributed_manager()
    data = request.get_json()
    
    if data and 'services' in data:
        for service_name in data['services']:
            if service_name in manager.modules:
                manager.modules[service_name].stop()
        return jsonify({'success': True, 'message': f"停止服务: {data['services']}"})
    else:
        manager.stop_all()
        return jsonify({'success': True, 'message': '所有服务已停止'})

@distributed_business_api.route('/services/restart', methods=['POST'])
def restart_services():
    """重启服务"""
    manager = get_distributed_manager()
    data = request.get_json()
    
    if data and 'services' in data:
        for service_name in data['services']:
            if service_name in manager.modules:
                manager.modules[service_name].stop()
                manager.modules[service_name].start()
        return jsonify({'success': True, 'message': f"重启服务: {data['services']}"})
    else:
        manager.stop_all()
        manager.start_all()
        return jsonify({'success': True, 'message': '所有服务已重启'})

@distributed_business_api.route('/discovery/services')
def discover_services():
    """发现所有服务"""
    manager = get_distributed_manager()
    services = {}
    
    for service_name in manager.modules.keys():
        instances = manager.service_discovery.discover_service(service_name)
        if instances:
            services[service_name] = {
                'instance_count': len(instances),
                'instances': instances
            }
    
    return jsonify(services)

@distributed_business_api.route('/discovery/service/<service_name>')
def discover_service(service_name):
    """发现指定服务"""
    manager = get_distributed_manager()
    instances = manager.service_discovery.discover_service(service_name)
    
    if instances:
        return jsonify({
            'service': service_name,
            'instance_count': len(instances),
            'instances': instances
        })
    return jsonify({'error': '服务未找到'}), 404

@distributed_business_api.route('/discovery/health')
def discovery_health():
    """服务健康检查"""
    manager = get_distributed_manager()
    results = {}
    
    for service_name in manager.modules.keys():
        instances = manager.service_discovery.get_healthy_instances(service_name)
        results[service_name] = {
            'healthy_instances': len(instances),
            'status': 'healthy' if instances else 'unhealthy'
        }
    
    return jsonify(results)

@distributed_business_api.route('/gateway/routes')
def get_routes():
    """获取网关路由"""
    manager = get_distributed_manager()
    routes = []
    
    for route_key, service_name in manager.api_gateway.routes.items():
        method, path = route_key.split(':', 1)
        routes.append({
            'method': method,
            'path': path,
            'service': service_name
        })
    
    return jsonify({'routes': routes})

@distributed_business_api.route('/gateway/routes', methods=['POST'])
def add_route():
    """添加网关路由"""
    manager = get_distributed_manager()
    data = request.get_json()
    
    if not data or 'method' not in data or 'path' not in data or 'service' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    manager.api_gateway.add_route(data['path'], data['service'], data['method'])
    return jsonify({'success': True, 'message': '路由添加成功'})

@distributed_business_api.route('/gateway/forward', methods=['POST'])
def forward_request():
    """转发请求"""
    manager = get_distributed_manager()
    data = request.get_json()
    
    if not data or 'method' not in data or 'path' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    status, headers, body = manager.process_request(
        data['method'],
        data['path'],
        data.get('headers'),
        data.get('body', '').encode()
    )
    
    return jsonify({
        'status': status,
        'headers': headers,
        'body': body.decode('utf-8') if body else None
    })

@distributed_business_api.route('/coordination/lock', methods=['POST'])
def acquire_lock():
    """获取分布式锁"""
    manager = get_distributed_manager()
    data = request.get_json()
    
    if not data or 'resource' not in data or 'owner' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    success = manager.coordination.acquire_lock(
        data['resource'],
        data['owner'],
        data.get('timeout', 30)
    )
    
    return jsonify({'success': success, 'message': '锁获取成功' if success else '锁获取失败'})

@distributed_business_api.route('/coordination/lock', methods=['DELETE'])
def release_lock():
    """释放分布式锁"""
    manager = get_distributed_manager()
    data = request.get_json()
    
    if not data or 'resource' not in data or 'owner' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    success = manager.coordination.release_lock(data['resource'], data['owner'])
    return jsonify({'success': success, 'message': '锁释放成功' if success else '锁释放失败'})

@distributed_business_api.route('/coordination/leader', methods=['POST'])
def elect_leader():
    """选举领导者"""
    manager = get_distributed_manager()
    data = request.get_json()
    
    if not data or 'candidates' not in data:
        return jsonify({'error': '缺少候选者列表'}), 400
    
    leader = manager.coordination.elect_leader(data['candidates'])
    return jsonify({'success': True, 'leader': leader})

@distributed_business_api.route('/coordination/leader')
def get_leader():
    """获取当前领导者"""
    manager = get_distributed_manager()
    return jsonify({'leader': manager.coordination.leader})

@distributed_business_api.route('/stats')
def get_stats():
    """获取统计信息"""
    manager = get_distributed_manager()
    return jsonify(manager.get_stats())

@distributed_business_api.route('/config')
def get_config():
    """获取配置"""
    manager = get_distributed_manager()
    return jsonify({
        'environment': manager.config.get('environment'),
        'api_gateway': manager.config.get('api_gateway'),
        'service_discovery': manager.config.get('service_discovery'),
        'modules': manager.config.get('modules')
    })

@distributed_business_api.route('/test')
def test():
    """测试功能"""
    manager = get_distributed_manager()
    
    results = {
        'services_test': False,
        'discovery_test': False,
        'gateway_test': False,
        'coordination_test': False
    }
    
    # 测试服务管理
    try:
        services = manager.get_all_services()
        results['services_test'] = len(services) > 0
    except Exception:
        pass
    
    # 测试服务发现
    try:
        instances = manager.service_discovery.discover_service('user_service')
        results['discovery_test'] = instances is not None
    except Exception:
        pass
    
    # 测试网关
    try:
        routes = manager.api_gateway.routes
        results['gateway_test'] = len(routes) > 0
    except Exception:
        pass
    
    # 测试协调
    try:
        success = manager.coordination.acquire_lock('test_resource', 'test_owner')
        manager.coordination.release_lock('test_resource', 'test_owner')
        results['coordination_test'] = success
    except Exception:
        pass
    
    return jsonify(results)

@distributed_business_api.route('/health')
def health():
    """健康检查"""
    manager = get_distributed_manager()
    services = manager.get_all_services()
    
    healthy_count = sum(1 for s in services.values() if s['status'] == 'running')
    total_count = len(services)
    
    return jsonify({
        'status': 'healthy' if healthy_count == total_count else 'degraded',
        'healthy_services': healthy_count,
        'total_services': total_count,
        'timestamp': datetime.now().isoformat()
    })
