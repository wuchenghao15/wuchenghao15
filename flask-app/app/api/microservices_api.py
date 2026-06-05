#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微服务架构管理API - 提供服务注册发现、RPC调用、配置中心、监控接口
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime

microservices_api = Blueprint('microservices_api', __name__)

# 全局微服务管理器实例
microservices_manager_instance = None

def init_microservices():
    """初始化微服务管理器"""
    global microservices_manager_instance
    if microservices_manager_instance is None:
        from app.utils.microservices_manager import get_microservices_manager
        microservices_manager_instance = get_microservices_manager()
    return microservices_manager_instance

def get_microservices_manager():
    """获取微服务管理器实例"""
    if microservices_manager_instance is None:
        return init_microservices()
    return microservices_manager_instance

@microservices_api.route('/')
def index():
    return jsonify({'status': 'ok', 'service': 'microservices-api'})

# ==================== 服务管理 ====================

@microservices_api.route('/services')
def list_services():
    """获取所有服务"""
    manager = get_microservices_manager()
    services = manager.get_all_services()
    return jsonify(services)

@microservices_api.route('/services/<service_name>')
def get_service(service_name):
    """获取服务详情"""
    manager = get_microservices_manager()
    service = manager.get_service_status(service_name)
    
    if service:
        return jsonify(service)
    return jsonify({'error': '服务不存在'}), 404

@microservices_api.route('/services/<service_name>/status')
def get_service_status(service_name):
    """获取服务状态"""
    manager = get_microservices_manager()
    service = manager.get_service_status(service_name)
    
    if service:
        return jsonify({'status': service['status']})
    return jsonify({'error': '服务不存在'}), 404

@microservices_api.route('/services/start', methods=['POST'])
def start_services():
    """启动服务"""
    manager = get_microservices_manager()
    data = request.get_json()
    
    if data and 'services' in data:
        for service_name in data['services']:
            manager.start_service(service_name)
        return jsonify({'success': True, 'message': f"启动服务: {data['services']}"})
    else:
        manager.start_all()
        return jsonify({'success': True, 'message': '所有服务已启动'})

@microservices_api.route('/services/stop', methods=['POST'])
def stop_services():
    """停止服务"""
    manager = get_microservices_manager()
    data = request.get_json()
    
    if data and 'services' in data:
        for service_name in data['services']:
            manager.stop_service(service_name)
        return jsonify({'success': True, 'message': f"停止服务: {data['services']}"})
    else:
        manager.stop_all()
        return jsonify({'success': True, 'message': '所有服务已停止'})

@microservices_api.route('/services/restart', methods=['POST'])
def restart_services():
    """重启服务"""
    manager = get_microservices_manager()
    data = request.get_json()
    
    if data and 'services' in data:
        for service_name in data['services']:
            manager.stop_service(service_name)
            manager.start_service(service_name)
        return jsonify({'success': True, 'message': f"重启服务: {data['services']}"})
    else:
        manager.stop_all()
        manager.start_all()
        return jsonify({'success': True, 'message': '所有服务已重启'})

# ==================== 服务注册发现 ====================

@microservices_api.route('/registry/services')
def registry_services():
    """获取注册的服务"""
    manager = get_microservices_manager()
    services = manager.registry.get_all_services()
    return jsonify({'services': services})

@microservices_api.route('/registry/service/<service_name>')
def registry_service(service_name):
    """获取服务实例"""
    manager = get_microservices_manager()
    instances = manager.registry.discover(service_name)
    return jsonify({
        'service': service_name,
        'instances': instances
    })

@microservices_api.route('/registry/register', methods=['POST'])
def registry_register():
    """注册服务实例"""
    manager = get_microservices_manager()
    data = request.get_json()
    
    if not data or 'service_name' not in data or 'host' not in data or 'port' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    manager.rpc.register_service(
        data['service_name'],
        data['host'],
        data.get('port', 80),
        data.get('version', '1.0.0')
    )
    
    return jsonify({'success': True, 'message': '服务注册成功'})

@microservices_api.route('/registry/deregister', methods=['POST'])
def registry_deregister():
    """注销服务实例"""
    manager = get_microservices_manager()
    data = request.get_json()
    
    if not data or 'service_name' not in data or 'instance_id' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    manager.registry.deregister(data['service_name'], data['instance_id'])
    return jsonify({'success': True, 'message': '服务注销成功'})

# ==================== RPC调用 ====================

@microservices_api.route('/rpc/call', methods=['POST'])
def rpc_call():
    """调用远程服务"""
    manager = get_microservices_manager()
    data = request.get_json()
    
    if not data or 'service' not in data or 'method' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    try:
        result = manager.call_service(data['service'], data['method'], data.get('params'))
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 配置中心 ====================

@microservices_api.route('/config')
def get_all_configs():
    """获取所有配置"""
    manager = get_microservices_manager()
    return jsonify(manager.config_center.configs)

@microservices_api.route('/config/<key>')
def get_config(key):
    """获取配置"""
    manager = get_microservices_manager()
    value = manager.get_config(key)
    
    if value is not None:
        return jsonify({key: value})
    return jsonify({'error': '配置不存在'}), 404

@microservices_api.route('/config/<key>', methods=['POST'])
def set_config(key):
    """设置配置"""
    manager = get_microservices_manager()
    data = request.get_json()
    
    if not data or 'value' not in data:
        return jsonify({'error': '缺少配置值'}), 400
    
    namespace = data.get('namespace', 'default')
    manager.set_config(key, data['value'], namespace)
    return jsonify({'success': True, 'message': '配置更新成功'})

@microservices_api.route('/config/namespace/<namespace>')
def get_namespace_configs(namespace):
    """获取命名空间配置"""
    manager = get_microservices_manager()
    configs = manager.config_center.get_namespace_configs(namespace)
    return jsonify(configs)

# ==================== 服务监控 ====================

@microservices_api.route('/monitor/metrics')
def get_all_metrics():
    """获取所有指标"""
    manager = get_microservices_manager()
    return jsonify(manager.monitor.metrics)

@microservices_api.route('/monitor/metrics/<service_name>')
def get_service_metrics(service_name):
    """获取服务指标"""
    manager = get_microservices_manager()
    metrics = manager.get_metrics(service_name)
    return jsonify({service_name: metrics})

@microservices_api.route('/monitor/metrics/record', methods=['POST'])
def record_metric():
    """记录指标"""
    manager = get_microservices_manager()
    data = request.get_json()
    
    if not data or 'service' not in data or 'metric' not in data or 'value' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    manager.record_metric(data['service'], data['metric'], float(data['value']))
    return jsonify({'success': True, 'message': '指标记录成功'})

@microservices_api.route('/monitor/alerts')
def get_alerts():
    """获取告警"""
    manager = get_microservices_manager()
    return jsonify({'alerts': manager.get_alerts()})

@microservices_api.route('/monitor/alerts/clear', methods=['POST'])
def clear_alerts():
    """清除告警"""
    manager = get_microservices_manager()
    manager.monitor.clear_alerts()
    return jsonify({'success': True, 'message': '告警已清除'})

@microservices_api.route('/monitor/alerts/check', methods=['POST'])
def check_alerts():
    """检查告警条件"""
    manager = get_microservices_manager()
    data = request.get_json()
    
    if not data or 'service' not in data or 'metric' not in data or 'threshold' not in data:
        return jsonify({'error': '缺少必要参数'}), 400
    
    operator = data.get('operator', '>')
    triggered = manager.monitor.check_alert(
        data['service'],
        data['metric'],
        float(data['threshold']),
        operator
    )
    
    return jsonify({'triggered': triggered})

# ==================== 健康检查 ====================

@microservices_api.route('/health')
def health():
    """健康检查"""
    manager = get_microservices_manager()
    services = manager.get_all_services()
    
    healthy_count = sum(1 for s in services.values() if s['status'] == 'running')
    total_count = len(services)
    
    return jsonify({
        'status': 'healthy' if healthy_count == total_count else 'degraded',
        'healthy_services': healthy_count,
        'total_services': total_count,
        'registered_services': len(manager.registry.get_all_services()),
        'timestamp': datetime.now().isoformat()
    })

@microservices_api.route('/test')
def test():
    """测试功能"""
    manager = get_microservices_manager()
    
    results = {
        'services_test': False,
        'registry_test': False,
        'rpc_test': False,
        'config_test': False,
        'monitor_test': False
    }
    
    # 测试服务管理
    try:
        services = manager.get_all_services()
        results['services_test'] = len(services) > 0
    except Exception:
        pass
    
    # 测试服务注册
    try:
        manager.rpc.register_service('test-service', 'localhost', 9999)
        instances = manager.registry.discover('test-service')
        results['registry_test'] = len(instances) > 0
    except Exception:
        pass
    
    # 测试配置中心
    try:
        manager.set_config('test.key', 'test.value')
        value = manager.get_config('test.key')
        results['config_test'] = value == 'test.value'
    except Exception:
        pass
    
    # 测试监控
    try:
        manager.record_metric('test-service', 'test_metric', 10.0)
        metrics = manager.get_metrics('test-service')
        results['monitor_test'] = 'test_metric' in metrics
    except Exception:
        pass
    
    return jsonify(results)
