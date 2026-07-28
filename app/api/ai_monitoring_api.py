#!/usr/bin/env python3
""" 系统监控API 提供系统状态监控、性能指标、AI员工状态、神经网络状态、集群状态等功能 """

import os
import json
import psutil
import sqlite3
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin

ai_monitoring_api = Bluelogger.info('ai_monitoring_api', __name__)

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


@ai_monitoring_api.route('/api/ai/monitoring/system/health', methods=['GET'])
@require_login
def system_health_check():
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        health = {
            'status': 'healthy' if cpu_percent < 90 and memory.percent < 90 else 'warning',
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': cpu_percent,
                'cores': psutil.cpu_count(),
                'threads': psutil.cpu_count(logical=True)
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
            'network': {
                'bytes_sent': round(network.bytes_sent / 1024 / 1024, 2),
                'bytes_recv': round(network.bytes_recv / 1024 / 1024, 2),
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            },
            'process': {
                'pid': os.getpid(),
                'name': 'MTSCOS AI Server',
                'uptime': datetime.now().isoformat()
            }
        }
        
        return jsonify({'success': True, 'data': health})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_monitoring_api.route('/api/ai/monitoring/system/stats', methods=['GET'])
@require_admin
def system_stats():
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM ai_employees")
            employee_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_employees WHERE status = 'active'")
            active_employees = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_brain_knowledge")
            knowledge_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM neural_network_nodes WHERE status = 'active'")
            active_nodes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM neural_network_connections WHERE status = 'active'")
            active_connections = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_cluster_config WHERE status = 'active'")
            cluster_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM system_rules WHERE is_active = 1")
            active_rules = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM brain_learning_records")
            learning_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_upgrade_records WHERE status = 'completed'")
            completed_upgrades = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(accuracy) FROM ai_employees")
            avg_accuracy = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT AVG(proficiency_after) FROM brain_learning_records")
            avg_proficiency = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM system_maintenance_logs WHERE result = 'success'")
            successful_maintenance = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM system_maintenance_logs WHERE result = 'failed'")
            failed_maintenance = cursor.fetchone()[0]
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'ai_employees': {
                'total': employee_count,
                'active': active_employees,
                'avg_accuracy': round(avg_accuracy, 4)
            },
            'brain_knowledge': {
                'total': knowledge_count
            },
            'neural_network': {
                'active_nodes': active_nodes,
                'active_connections': active_connections,
                'density': round(active_connections / max(active_nodes, 1), 2)
            },
            'clusters': {
                'active': cluster_count
            },
            'rules': {
                'active': active_rules
            },
            'learning': {
                'total_records': learning_records,
                'avg_proficiency': round(avg_proficiency, 4)
            },
            'upgrades': {
                'completed': completed_upgrades
            },
            'maintenance': {
                'successful': successful_maintenance,
                'failed': failed_maintenance,
                'success_rate': round(successful_maintenance / max(successful_maintenance + failed_maintenance,
                1) * 100, 2)
            }
        }
        
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_monitoring_api.route('/api/ai/monitoring/employees', methods=['GET'])
@require_admin
def get_employees_status():
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            status_filter = request.args.get('status')
            if status_filter:
                cursor.execute("SELECT id, name, employee_code, role, status, accuracy, created_at, updated_at FROM ai_employees WHERE status = ?", (status_filter,))
            else:
                cursor.execute("SELECT id, name, employee_code, role, status, accuracy, created_at, updated_at FROM ai_employees")
            
            rows = cursor.fetchall()
        
        employees = []
        for row in rows:
            employees.append({
                'id': row[0],
                'name': row[1],
                'employee_code': row[2],
                'role': row[3],
                'status': row[4],
                'accuracy': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            })
        
        return jsonify({'success': True, 'data': employees, 'count': len(employees),
        'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_monitoring_api.route('/api/ai/monitoring/employee/<employee_id>', methods=['GET'])
@require_admin
def get_employee_detail(employee_id):
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM ai_employees WHERE id = ?", (employee_id,))
            emp = cursor.fetchone()
            
            if not emp:
                return jsonify({'success': False, 'error': '员工不存在'}), 404
            
            cursor.execute(
            "SELECT * FROM brain_learning_records WHERE employee_id = ? ORDER BY created_at DESC LIMIT 5",
            (str(employee_id),))
            learning_history = cursor.fetchall()
            
            cursor.execute("SELECT * FROM ai_upgrade_records WHERE employee_id = ? ORDER BY created_at DESC LIMIT 5",
            (employee_id,))
            upgrade_history = cursor.fetchall()
        
        employee = {
            'id': emp[0],
            'name': emp[1],
            'employee_code': emp[2],
            'role': emp[3],
            'department': emp[4],
            'skill_level': emp[5],
            'status': emp[6],
            'accuracy': emp[7],
            'speed': emp[8],
            'reliability': emp[9],
            'efficiency': emp[10],
            'creativity': emp[11],
            'knowledge_base': emp[12],
            'capabilities': json.loads(emp[13]) if emp[13] else {},
            'personality': json.loads(emp[14]) if emp[14] else {},
            'training_progress': emp[15],
            'last_training_time': emp[16],
            'created_at': emp[17],
            'updated_at': emp[18],
            'learning_history': [],
            'upgrade_history': []
        }
        
        for record in learning_history:
            employee['learning_history'].append({
                'record_id': record[0],
                'learning_type': record[3],
                'proficiency_gain': record[9],
                'created_at': record[15]
            })
        
        for record in upgrade_history:
            employee['upgrade_history'].append({
                'upgrade_id': record[0],
                'upgrade_type': record[3],
                'before_level': record[5],
                'after_level': record[6],
                'upgrade_score': record[10],
                'status': record[12],
                'created_at': record[14]
            })
        
        return jsonify({'success': True, 'data': employee, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_monitoring_api.route('/api/ai/monitoring/neural-network', methods=['GET'])
@require_admin
def get_neural_network_status():
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM neural_network_nodes")
            total_nodes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM neural_network_nodes WHERE status = 'active'")
            active_nodes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM neural_network_nodes WHERE status = 'pruned'")
            pruned_nodes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM neural_network_connections")
            total_connections = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM neural_network_connections WHERE status = 'active'")
            active_connections = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(accuracy) FROM neural_network_nodes WHERE status = 'active'")
            avg_accuracy = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT AVG(weight) FROM neural_network_connections WHERE status = 'active'")
            avg_weight = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT SUM(training_count) FROM neural_network_nodes")
            total_training_count = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT node_layer, COUNT(*) FROM neural_network_nodes WHERE status = 'active' GROUP BY node_layer")
            layer_distribution = cursor.fetchall()
        
        layer_info = {}
        for layer, count in layer_distribution:
            layer_info[str(layer)] = count
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'nodes': {
                'total': total_nodes,
                'active': active_nodes,
                'pruned': pruned_nodes,
                'avg_accuracy': round(avg_accuracy, 4),
                'total_training_count': total_training_count
            },
            'connections': {
                'total': total_connections,
                'active': active_connections,
                'avg_weight': round(avg_weight, 4)
            },
            'density': round(active_connections / max(active_nodes, 1), 2),
            'layer_distribution': layer_info
        }
        
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_monitoring_api.route('/api/ai/monitoring/clusters', methods=['GET'])
@require_admin
def get_cluster_status():
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM ai_cluster_config")
            clusters = cursor.fetchall()
            
            cluster_list = []
            for cluster in clusters:
                cluster_id = cluster[0]
                cursor.execute("SELECT COUNT(*) FROM ai_cluster_employee WHERE cluster_id = ?", (cluster_id,))
                member_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT( *) FROM cluster_coordination_records WHERE cluster_id = ? AND status = 'completed'", (cluster_id,))
                completed_coordinations = cursor.fetchone()[0]
                
                cluster_list.append({
                    'cluster_id': cluster[0],
                    'cluster_type': cluster[1],
                    'config': json.loads(cluster[2]) if cluster[2] else {},
                    'status': cluster[3],
                    'member_count': member_count,
                    'completed_coordinations': completed_coordinations,
                    'created_at': cluster[4],
                    'updated_at': cluster[5]
                })
        
        return jsonify({'success': True, 'data': cluster_list, 'count': len(cluster_list),
        'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_monitoring_api.route('/api/ai/monitoring/maintenance/logs', methods=['GET'])
@require_admin
def get_maintenance_logs():
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            limit = int(request.args.get('limit', 50))
            operation_type = request.args.get('operation_type')
            result = request.args.get('result')
            
            query = "SELECT * FROM system_maintenance_logs ORDER BY timestamp DESC"
            params = []
            
            if operation_type:
                query = "SELECT * FROM system_maintenance_logs WHERE operation_type = ? ORDER BY timestamp DESC"
                params.append(operation_type)
            elif result:
                query = "SELECT * FROM system_maintenance_logs WHERE result = ? ORDER BY timestamp DESC"
                params.append(result)
            
            query += " LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
        
        logs = []
        for row in rows:
            logs.append({
                'id': row[0],
                'operation_type': row[1],
                'target': row[2],
                'result': row[3],
                'details': row[4],
                'timestamp': row[5]
            })
        
        return jsonify({'success': True, 'data': logs, 'count': len(logs), 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_monitoring_api.route('/api/ai/monitoring/learning/trends', methods=['GET'])
@require_admin
def get_learning_trends():
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute(''' SELECT DATE(recorded_at) as date, AVG(metric_value) as avg_value FROM performance_metrics WHERE metric_name = 'learning_progress' GROUP BY DATE(recorded_at) ORDER BY date DESC LIMIT 30 ''')
            learning_progress = cursor.fetchall()
            
            cursor.execute(''' SELECT DATE(learned_at) as date, COUNT(*) as count FROM learning_history GROUP BY DATE(learned_at) ORDER BY date DESC LIMIT 30 ''')
            learning_count = cursor.fetchall()
            
            cursor.execute(''' SELECT DATE(created_at) as date, COUNT(*) as count FROM ai_brain_knowledge GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 30 ''')
            knowledge_count = cursor.fetchall()
        
        trends = {
            'timestamp': datetime.now().isoformat(),
            'learning_progress': [{'date': row[0], 'avg_value': round(row[1], 4)} for row in learning_progress],
            'learning_count': [{'date': row[0], 'count': row[1]} for row in learning_count],
            'knowledge_count': [{'date': row[0], 'count': row[1]} for row in knowledge_count]
        }
        
        return jsonify({'success': True, 'data': trends})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_monitoring_api.route('/api/ai/monitoring/alert', methods=['GET'])
@require_admin
def get_alerts():
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        alerts = []
        
        if cpu_percent > 90:
            alerts.append({
                'level': 'critical',
                'type': 'cpu',
                'message': f'CPU使用率过高: {cpu_percent}%',
                'timestamp': datetime.now().isoformat()
            })
        elif cpu_percent > 70:
            alerts.append({
                'level': 'warning',
                'type': 'cpu',
                'message': f'CPU使用率偏高: {cpu_percent}%',
                'timestamp': datetime.now().isoformat()
            })
        
        if memory.percent > 90:
            alerts.append({
                'level': 'critical',
                'type': 'memory',
                'message': f'内存使用率过高: {memory.percent}%',
                'timestamp': datetime.now().isoformat()
            })
        elif memory.percent > 70:
            alerts.append({
                'level': 'warning',
                'type': 'memory',
                'message': f'内存使用率偏高: {memory.percent}%',
                'timestamp': datetime.now().isoformat()
            })
        
        if disk.percent > 90:
            alerts.append({
                'level': 'critical',
                'type': 'disk',
                'message': f'磁盘使用率过高: {disk.percent}%',
                'timestamp': datetime.now().isoformat()
            })
        elif disk.percent > 80:
            alerts.append({
                'level': 'warning',
                'type': 'disk',
                'message': f'磁盘使用率偏高: {disk.percent}%',
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({'success': True, 'data': alerts, 'count': len(alerts), 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_monitoring_api.route('/api/ai/monitoring/summary', methods=['GET'])
@require_admin
def monitoring_summary():
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM ai_employees WHERE status = 'active'")
            active_employees = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_brain_knowledge")
            knowledge_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM neural_network_nodes WHERE status = 'active'")
            active_nodes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM brain_learning_records WHERE DATE(learned_at) = DATE('now')")
            today_learning = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_upgrade_records WHERE DATE(created_at) = DATE('now')")
            today_upgrades = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM system_maintenance_logs WHERE result = 'failed' AND DATE( timestamp) = DATE('now')")
            today_failures = cursor.fetchone()[0]
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'status': 'healthy' if cpu_percent < 70 and memory.percent < 70 else 'warning' if cpu_percent < 90 and 
                memory.percent < 90 else 'critical'
            },
            'ai_employees': {
                'active': active_employees
            },
            'brain_knowledge': {
                'total': knowledge_count
            },
            'neural_network': {
                'active_nodes': active_nodes
            },
            'today_activity': {
                'learning_records': today_learning,
                'upgrades': today_upgrades,
                'failures': today_failures
            }
        }
        
        return jsonify({'success': True, 'data': summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500