#!/usr/bin/env python3
import os
import psutil
import sqlite3
import time
import redis
from datetime import datetime
from flask import Blueprint, jsonify

health_api = Bluelogger.info('health_api', __name__)


def get_system_metrics():
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'cpu': {
            'percent': cpu_percent,
            'count': psutil.cpu_count()
        },
        'memory': {
            'total': round(memory.total / 1024 / 1024 / 1024, 2),
            'used': round(memory.used / 1024 / 1024 / 1024, 2),
            'available': round(memory.available / 1024 / 1024 / 1024, 2),
            'percent': memory.percent
        },
        'disk': {
            'total': round(disk.total / 1024 / 1024 / 1024, 2),
            'used': round(disk.used / 1024 / 1024 / 1024, 2),
            'free': round(disk.free / 1024 / 1024 / 1024, 2),
            'percent': disk.percent
        },
        'uptime': time.time() - psutil.boot_time(),
        'process_count': len(psutil.pids())
    }


def check_database_connection(db_path):
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        return {'status': 'healthy', 'latency_ms': 0}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}


def check_redis_connection():
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, timeout=2)
        start = time.time()
        r.ping()
        latency = (time.time() - start) * 1000
        return {'status': 'healthy', 'latency_ms': round(latency, 2)}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}


def check_scheduler_status():
    pid_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    '.scheduler_pid')
    heartbeat_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    '.scheduler_heartbeat')
    
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            pid = f.read().strip()
        try:
            process = psutil.Process(int(pid))
            running = process.is_running()
            status = 'healthy' if running else 'unhealthy'
        except:
            status = 'unhealthy'
    else:
        status = 'stopped'
    
    last_heartbeat = None
    if os.path.exists(heartbeat_file):
        try:
            with open(heartbeat_file, 'r') as f:
                last_heartbeat = f.read().strip()
        except:
            pass
    
    return {'status': status, 'last_heartbeat': last_heartbeat}


def get_service_status():
    services = {}
    
    services['database'] = check_database_connection(
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    )
    
    services['redis'] = check_redis_connection()
    
    services['scheduler'] = check_scheduler_status()
    
    services['auto_repair'] = {
        'status': 'healthy' if os.path.exists(
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'auto_scheduler.log')
        ) else 'unknown'
    }
    
    return services


@health_api.route('/api/health', methods=['GET'])
def health_check():
    metrics = get_system_metrics()
    services = get_service_status()
    
    overall_status = 'healthy'
    for service_name, service_info in services.items():
        if service_info.get('status') == 'unhealthy':
            overall_status = 'unhealthy'
            break
    
    response = {
        'status': overall_status,
        'timestamp': datetime.now().isoformat(),
        'system': metrics,
        'services': services
    }
    
    http_status = 200 if overall_status == 'healthy' else 503
    return jsonify(response), http_status


@health_api.route('/api/health/system', methods=['GET'])
def system_metrics():
    metrics = get_system_metrics()
    return jsonify({
        'success': True,
        'data': metrics,
        'timestamp': datetime.now().isoformat()
    })


@health_api.route('/api/health/services', methods=['GET'])
def service_status():
    services = get_service_status()
    return jsonify({
        'success': True,
        'data': services,
        'timestamp': datetime.now().isoformat()
    })


@health_api.route('/api/health/database', methods=['GET'])
def database_health():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    result = check_database_connection(db_path)
    return jsonify({
        'success': result['status'] == 'healthy',
        'data': result,
        'timestamp': datetime.now().isoformat()
    })


@health_api.route('/api/health/redis', methods=['GET'])
def redis_health():
    result = check_redis_connection()
    return jsonify({
        'success': result['status'] == 'healthy',
        'data': result,
        'timestamp': datetime.now().isoformat()
    })


@health_api.route('/api/health/scheduler', methods=['GET'])
def scheduler_health():
    result = check_scheduler_status()
    return jsonify({
        'success': result['status'] == 'healthy',
        'data': result,
        'timestamp': datetime.now().isoformat()
    })


@health_api.route('/api/health/quick', methods=['GET'])
def quick_health():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
    db_status = check_database_connection(db_path)
    
    status = 'healthy' if db_status['status'] == 'healthy' else 'unhealthy'
    
    return jsonify({
        'status': status,
        'timestamp': datetime.now().isoformat()
    }), 200 if status == 'healthy' else 503