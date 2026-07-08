import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
端口监控服务 - AI员工模块
监控系统端口异常，匹配参数数据信息库，自动修复并上传数据库
"""

import os
import re
import json
import time
import socket
import sqlite3
import subprocess
from datetime import datetime
from contextlib import contextmanager
from flask import request

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'mtscos.db')


@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_port_monitor_tables():
    """初始化端口监控表"""
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS port_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                port INTEGER UNIQUE NOT NULL,
                service_name TEXT,
                expected_status TEXT DEFAULT 'running',
                protocol TEXT DEFAULT 'tcp',
                bind_address TEXT DEFAULT '0.0.0.0',
                config_file TEXT,
                config_params TEXT,
                actual_status TEXT DEFAULT 'unknown',
                last_check INTEGER,
                last_error TEXT,
                error_count INTEGER DEFAULT 0,
                last_fixed INTEGER,
                fix_count INTEGER DEFAULT 0,
                status_changed INTEGER
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_port_status_port ON port_status(port)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_port_status_status ON port_status(actual_status)')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS port_fix_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fix_id TEXT UNIQUE NOT NULL,
                port INTEGER NOT NULL,
                service_name TEXT,
                problem_type TEXT NOT NULL,
                problem_details TEXT,
                fix_action TEXT,
                fix_result TEXT DEFAULT 'pending',
                fix_time INTEGER,
                applied_by TEXT DEFAULT 'system',
                before_config TEXT,
                after_config TEXT,
                verified INTEGER DEFAULT 0,
                verify_time INTEGER
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_port_fix_port ON port_fix_logs(port)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_port_fix_result ON port_fix_logs(fix_result)')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS port_config_params (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                param_id TEXT UNIQUE NOT NULL,
                port INTEGER NOT NULL,
                param_name TEXT NOT NULL,
                expected_value TEXT,
                actual_value TEXT,
                param_type TEXT DEFAULT 'string',
                required INTEGER DEFAULT 1,
                validation_regex TEXT,
                match_status TEXT DEFAULT 'unknown',
                last_checked INTEGER,
                notes TEXT
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_port_params_port ON port_config_params(port)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_port_params_match ON port_config_params(match_status)')
        
        conn.commit()
    print("[INFO] 端口监控表初始化完成")


def generate_fix_id():
    """生成修复ID"""
    return f"fix_{int(time.time())}_{hash(str(time.time())) % 10000}"


def generate_param_id(port, param_name):
    """生成参数ID"""
    return f"param_{port}_{hash(param_name) % 10000}"


def is_port_open(port, host='127.0.0.1', timeout=2):
    """检查端口是否开放"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((host, port))
            return result == 0
    except Exception:
        return False


def get_port_process(port):
    """获取端口占用进程"""
    try:
        result = subprocess.run(
            ['lsof', '-i', f':{port}'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                return lines[1].split()[0]
    except Exception:
        pass
    return None


def get_port_status(port):
    """获取端口状态"""
    open_status = is_port_open(port)
    process = get_port_process(port)
    
    status = 'running' if open_status else 'stopped'
    if process and not open_status:
        status = 'blocked'
    
    return {
        'port': port,
        'is_open': open_status,
        'process': process,
        'status': status
    }


def check_port_config_params(port):
    """检查端口配置参数匹配"""
    params = []
    
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM port_config_params WHERE port = ?', (port,)
        ).fetchall()
        
        for row in rows:
            param = dict(row)
            param['match_status'] = 'matched' if param['expected_value'] == param['actual_value'] else 'mismatched'
            
            if param['validation_regex']:
                try:
                    if re.match(param['validation_regex'], str(param['actual_value'])):
                        param['match_status'] = 'validated'
                    else:
                        param['match_status'] = 'invalid'
                except Exception:
                    pass
            
            params.append(param)
            
            conn.execute('''
                UPDATE port_config_params 
                SET match_status = ?, last_checked = ? 
                WHERE param_id = ?
            ''', (param['match_status'], int(time.time()), param['param_id']))
        conn.commit()
    
    return params


def get_expected_port_config():
    """获取预期端口配置"""
    configs = [
        {'port': 8888, 'service_name': 'MTSCOS HTTP服务', 'expected_status': 'running', 'protocol': 'tcp', 'description': '主应用HTTP端口'},
        {'port': 8443, 'service_name': 'MTSCOS HTTPS服务', 'expected_status': 'running', 'protocol': 'tcp', 'description': '主应用HTTPS端口'},
        {'port': 5000, 'service_name': 'Flask开发服务', 'expected_status': 'running', 'protocol': 'tcp', 'description': '开发环境端口'},
        {'port': 5001, 'service_name': 'API服务', 'expected_status': 'running', 'protocol': 'tcp', 'description': 'API服务端口'},
        {'port': 5002, 'service_name': 'WebSocket服务', 'expected_status': 'running', 'protocol': 'tcp', 'description': '实时通信端口'},
        {'port': 3306, 'service_name': 'MySQL数据库', 'expected_status': 'optional', 'protocol': 'tcp', 'description': 'MySQL数据库端口'},
        {'port': 27017, 'service_name': 'MongoDB', 'expected_status': 'optional', 'protocol': 'tcp', 'description': 'MongoDB数据库端口'},
        {'port': 6379, 'service_name': 'Redis缓存', 'expected_status': 'running', 'protocol': 'tcp', 'description': 'Redis缓存端口'},
        {'port': 6380, 'service_name': 'Redis哨兵', 'expected_status': 'optional', 'protocol': 'tcp', 'description': 'Redis哨兵端口'},
        {'port': 80, 'service_name': '标准HTTP', 'expected_status': 'optional', 'protocol': 'tcp', 'description': '标准HTTP端口'},
        {'port': 443, 'service_name': '标准HTTPS', 'expected_status': 'optional', 'protocol': 'tcp', 'description': '标准HTTPS端口'},
        {'port': 22, 'service_name': 'SSH服务', 'expected_status': 'running', 'protocol': 'tcp', 'description': 'SSH远程连接端口'},
        {'port': 25, 'service_name': 'SMTP服务', 'expected_status': 'optional', 'protocol': 'tcp', 'description': '邮件服务端口'},
        {'port': 587, 'service_name': 'SMTP TLS', 'expected_status': 'optional', 'protocol': 'tcp', 'description': '邮件加密端口'},
        {'port': 9200, 'service_name': 'Elasticsearch', 'expected_status': 'optional', 'protocol': 'tcp', 'description': '搜索服务端口'},
        {'port': 9092, 'service_name': 'Kafka', 'expected_status': 'optional', 'protocol': 'tcp', 'description': '消息队列端口'},
        {'port': 8080, 'service_name': '管理控制台', 'expected_status': 'running', 'protocol': 'tcp', 'description': '管理控制台端口'},
        {'port': 8081, 'service_name': '监控服务', 'expected_status': 'running', 'protocol': 'tcp', 'description': '监控服务端口'},
        {'port': 8082, 'service_name': '日志服务', 'expected_status': 'running', 'protocol': 'tcp', 'description': '日志服务端口'},
        {'port': 8083, 'service_name': '定时任务', 'expected_status': 'running', 'protocol': 'tcp', 'description': '定时任务服务端口'},
    ]
    return configs


def scan_port_range(start_port, end_port, host='127.0.0.1'):
    """扫描端口范围"""
    results = []
    for port in range(start_port, end_port + 1):
        try:
            status = get_port_status(port)
            results.append(status)
        except Exception:
            pass
    return results


def allocate_port(start_range=8000, end_range=9000):
    """分配可用端口"""
    for port in range(start_range, end_range + 1):
        if not is_port_open(port):
            return port
    return None


def reserve_port(port, service_name):
    """预留端口"""
    with get_db() as conn:
        conn.execute('''
            INSERT OR REPLACE INTO port_status (
                port, service_name, expected_status, protocol, bind_address,
                actual_status, last_check
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (port, service_name, 'reserved', 'tcp', '0.0.0.0', 'reserved', int(time.time())))
        conn.commit()
    return True


def release_port(port):
    """释放端口"""
    with get_db() as conn:
        conn.execute('DELETE FROM port_status WHERE port = ?', (port,))
        conn.execute('DELETE FROM port_config_params WHERE port = ?', (port,))
        conn.commit()
    return True


def get_port_usage_stats():
    """获取端口使用统计"""
    with get_db() as conn:
        total = conn.execute('SELECT COUNT(*) FROM port_status').fetchone()[0]
        running = conn.execute('SELECT COUNT(*) FROM port_status WHERE actual_status = "running"').fetchone()[0]
        stopped = conn.execute('SELECT COUNT(*) FROM port_status WHERE actual_status = "stopped"').fetchone()[0]
        reserved = conn.execute('SELECT COUNT(*) FROM port_status WHERE actual_status = "reserved"').fetchone()[0]
        
        protocol_stats = conn.execute('SELECT protocol, COUNT(*) FROM port_status GROUP BY protocol').fetchall()
        status_stats = conn.execute('SELECT actual_status, COUNT(*) FROM port_status GROUP BY actual_status').fetchall()
        
        return {
            'total': total,
            'running': running,
            'stopped': stopped,
            'reserved': reserved,
            'protocol_distribution': dict(protocol_stats),
            'status_distribution': dict(status_stats)
        }


def sync_port_configs():
    """同步端口配置到数据库"""
    configs = get_expected_port_config()
    
    with get_db() as conn:
        for config in configs:
            conn.execute('''
                INSERT OR REPLACE INTO port_status (
                    port, service_name, expected_status, protocol, bind_address,
                    actual_status, last_check
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                config['port'], config['service_name'], config['expected_status'],
                config['protocol'], '0.0.0.0', 'unknown', int(time.time())
            ))
        conn.commit()


def sync_port_params():
    """同步端口参数配置"""
    params = [
        {'port': 8888, 'param_name': 'FLASK_PORT', 'expected_value': '8888', 'param_type': 'integer'},
        {'port': 8443, 'param_name': 'SSL_PORT', 'expected_value': '8443', 'param_type': 'integer'},
        {'port': 8888, 'param_name': 'DEBUG_MODE', 'expected_value': 'False', 'param_type': 'boolean'},
        {'port': 8443, 'param_name': 'SSL_ENABLED', 'expected_value': 'True', 'param_type': 'boolean'},
        {'port': 8888, 'param_name': 'HOST_BIND', 'expected_value': '0.0.0.0', 'param_type': 'string'},
        {'port': 8443, 'param_name': 'HOST_BIND', 'expected_value': '0.0.0.0', 'param_type': 'string'},
        {'port': 3306, 'param_name': 'DB_PORT', 'expected_value': '3306', 'param_type': 'integer'},
        {'port': 27017, 'param_name': 'MONGO_PORT', 'expected_value': '27017', 'param_type': 'integer'},
        {'port': 6379, 'param_name': 'REDIS_PORT', 'expected_value': '6379', 'param_type': 'integer'},
    ]
    
    with get_db() as conn:
        for param in params:
            param_id = generate_param_id(param['port'], param['param_name'])
            actual_value = os.environ.get(param['param_name'], '')
            
            conn.execute('''
                INSERT OR REPLACE INTO port_config_params (
                    param_id, port, param_name, expected_value, actual_value,
                    param_type, required, last_checked
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                param_id, param['port'], param['param_name'], 
                param['expected_value'], actual_value,
                param['param_type'], 1, int(time.time())
            ))
        conn.commit()


def scan_all_ports():
    """扫描所有端口状态"""
    results = []
    
    with get_db() as conn:
        rows = conn.execute('SELECT port, service_name, expected_status FROM port_status').fetchall()
        
        for row in rows:
            port_info = dict(row)
            status = get_port_status(port_info['port'])
            
            port_info.update(status)
            
            actual_status = status['status']
            error_count = row['error_count'] if 'error_count' in row else 0
            
            if actual_status != port_info['expected_status'] and port_info['expected_status'] == 'running':
                error_count += 1
            
            conn.execute('''
                UPDATE port_status 
                SET actual_status = ?, last_check = ?, error_count = ?, last_error = ?
                WHERE port = ?
            ''', (actual_status, int(time.time()), error_count, 
                  f"端口状态异常: {actual_status}" if error_count > 0 else '', port_info['port']))
            
            results.append(port_info)
        
        conn.commit()
    
    return results


def fix_port_mismatch(port):
    """修复端口参数不匹配"""
    fix_id = generate_fix_id()
    fixes = []
    
    params = check_port_config_params(port)
    
    for param in params:
        if param['match_status'] == 'mismatched':
            os.environ[param['param_name']] = param['expected_value']
            fixes.append({
                'param_name': param['param_name'],
                'old_value': param['actual_value'],
                'new_value': param['expected_value'],
                'action': '环境变量更新'
            })
            
            with get_db() as conn:
                conn.execute('''
                    UPDATE port_config_params 
                    SET actual_value = ?, match_status = ?, last_checked = ?
                    WHERE param_id = ?
                ''', (param['expected_value'], 'matched', int(time.time()), param['param_id']))
                conn.commit()
    
    if fixes:
        with get_db() as conn:
            conn.execute('''
                INSERT INTO port_fix_logs (
                    fix_id, port, service_name, problem_type, problem_details,
                    fix_action, fix_result, fix_time, applied_by,
                    before_config, after_config
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fix_id, port, '', '参数不匹配',
                json.dumps([p['param_name'] for p in params if p['match_status'] == 'mismatched']),
                json.dumps(fixes), 'success', int(time.time()), 'port_monitor_ai',
                json.dumps([{'name': p['param_name'], 'value': p['actual_value']} for p in params]),
                json.dumps([{'name': p['param_name'], 'value': p['expected_value']} for p in params])
            ))
            conn.commit()
        
        conn.execute('''
            UPDATE port_status 
            SET last_fixed = ?, fix_count = fix_count + 1, error_count = 0
            WHERE port = ?
        ''', (int(time.time()), port))
        conn.commit()
    
    return fix_id, 'success' if fixes else 'no_mismatch', fixes


def fix_port_not_running(port):
    """修复端口未运行"""
    fix_id = generate_fix_id()
    
    with get_db() as conn:
        row = conn.execute('SELECT service_name FROM port_status WHERE port = ?', (port,)).fetchone()
        service_name = row['service_name'] if row else ''
    
    try:
        process = get_port_process(port)
        if process:
            subprocess.run(['kill', '-9', f'$(lsof -ti:{port})'], shell=True, capture_output=True)
            time.sleep(2)
        
        if port == 8888 or port == 8443:
            subprocess.Popen([
                'python3', '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.py',
                '--port' if port == 8888 else '--ssl', '--ssl-port' if port == 8443 else '', str(port)
            ], cwd='/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app')
        
        time.sleep(5)
        
        if is_port_open(port):
            fix_result = 'success'
            fix_action = f'重启服务 {service_name} 到端口 {port}'
        else:
            fix_result = 'failed'
            fix_action = f'尝试重启服务 {service_name} 失败'
        
        with get_db() as conn:
            conn.execute('''
                INSERT INTO port_fix_logs (
                    fix_id, port, service_name, problem_type, problem_details,
                    fix_action, fix_result, fix_time, applied_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fix_id, port, service_name, '端口未运行',
                f'端口 {port} 状态为 stopped',
                fix_action, fix_result, int(time.time()), 'port_monitor_ai'
            ))
            conn.commit()
            
            if fix_result == 'success':
                conn.execute('''
                    UPDATE port_status 
                    SET actual_status = 'running', last_fixed = ?, fix_count = fix_count + 1, error_count = 0
                    WHERE port = ?
                ''', (int(time.time()), port))
                conn.commit()
        
        return fix_id, fix_result, fix_action
    
    except Exception as e:
        with get_db() as conn:
            conn.execute('''
                INSERT INTO port_fix_logs (
                    fix_id, port, service_name, problem_type, problem_details,
                    fix_action, fix_result, fix_time, applied_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fix_id, port, service_name, '修复失败', str(e),
                '自动修复尝试', 'failed', int(time.time()), 'port_monitor_ai'
            ))
            conn.commit()
        
        return fix_id, 'failed', str(e)


def auto_fix_port_issues():
    """自动修复所有端口问题"""
    results = []
    
    with get_db() as conn:
        rows = conn.execute('''
            SELECT port, service_name, actual_status, expected_status 
            FROM port_status 
            WHERE expected_status = 'running'
        ''').fetchall()
        
        for row in rows:
            port = row['port']
            actual_status = row['actual_status']
            expected_status = row['expected_status']
            
            if actual_status != expected_status:
                fix_id, result, action = fix_port_not_running(port)
                results.append({
                    'port': port,
                    'service_name': row['service_name'],
                    'problem': f'{actual_status} != {expected_status}',
                    'fix_id': fix_id,
                    'result': result,
                    'action': action
                })
            
            params = check_port_config_params(port)
            mismatched = [p for p in params if p['match_status'] == 'mismatched']
            
            if mismatched:
                fix_id, result, fixes = fix_port_mismatch(port)
                results.append({
                    'port': port,
                    'service_name': row['service_name'],
                    'problem': f'{len(mismatched)}个参数不匹配',
                    'fix_id': fix_id,
                    'result': result,
                    'action': fixes
                })
    
    return results


def get_port_stats():
    """获取端口监控统计"""
    try:
        with get_db() as conn:
            total_ports = conn.execute('SELECT COUNT(*) FROM port_status').fetchone()[0]
            running_ports = conn.execute('SELECT COUNT(*) FROM port_status WHERE actual_status = "running"').fetchone()[0]
            stopped_ports = conn.execute('SELECT COUNT(*) FROM port_status WHERE actual_status = "stopped"').fetchone()[0]
            error_ports = conn.execute('SELECT COUNT(*) FROM port_status WHERE error_count > 0').fetchone()[0]
            
            total_fixes = conn.execute('SELECT COUNT(*) FROM port_fix_logs').fetchone()[0]
            successful_fixes = conn.execute('SELECT COUNT(*) FROM port_fix_logs WHERE fix_result = "success"').fetchone()[0]
            
            mismatched_params = conn.execute('SELECT COUNT(*) FROM port_config_params WHERE match_status = "mismatched"').fetchone()[0]
            
            return {
                'total_ports': total_ports,
                'running_ports': running_ports,
                'stopped_ports': stopped_ports,
                'error_ports': error_ports,
                'total_fixes': total_fixes,
                'successful_fixes': successful_fixes,
                'mismatched_params': mismatched_params,
                'updated_at': int(time.time())
            }
    except Exception as e:
        print(f"[ERROR] 获取端口统计失败: {e}")
        return {}


def get_port_status_list():
    """获取所有端口状态"""
    try:
        with get_db() as conn:
            rows = conn.execute('SELECT * FROM port_status ORDER BY port').fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"[ERROR] 获取端口状态失败: {e}")
        return []


def get_port_params(port):
    """获取端口参数"""
    try:
        with get_db() as conn:
            rows = conn.execute('SELECT * FROM port_config_params WHERE port = ?', (port,)).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"[ERROR] 获取端口参数失败: {e}")
        return []


def get_fix_logs(limit=50):
    """获取修复日志"""
    try:
        with get_db() as conn:
            rows = conn.execute('''
                SELECT * FROM port_fix_logs 
                ORDER BY fix_time DESC LIMIT ?
            ''', (limit,)).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"[ERROR] 获取修复日志失败: {e}")
        return []


def create_port_monitor_employee():
    """创建端口监控AI员工"""
    employee_id = 'emp_port_monitor_ai'
    
    try:
        with get_db() as conn:
            conn.execute('''
                INSERT OR IGNORE INTO ai_employees (
                    employee_id, name, title, description, category,
                    capabilities, efficiency, workload, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                employee_id,
                '端口监控员',
                '系统端口异常监控与修复专家',
                '负责监控系统端口状态，检测端口异常，匹配参数数据信息库，自动修复端口问题并上传数据库',
                'system',
                json.dumps([
                    '端口状态实时监控',
                    '端口参数数据匹配',
                    '端口异常自动检测',
                    '端口参数不匹配修复',
                    '端口未运行自动重启',
                    '修复记录自动上传数据库',
                    '端口统计分析',
                    '参数验证正则匹配',
                    '端口进程管理',
                    '端口配置同步',
                    '实时告警通知',
                    '批量端口扫描'
                ]),
                98,
                0,
                int(time.time()),
                int(time.time())
            ))
            conn.commit()
        print("[INFO] 端口监控AI员工创建完成")
        return True
    except Exception as e:
        print(f"[ERROR] 创建端口监控AI员工失败: {e}")
        return False


def get_port_monitor_employee():
    """获取端口监控AI员工信息"""
    try:
        with get_db() as conn:
            row = conn.execute(
                'SELECT * FROM ai_employees WHERE employee_id = ?', ('emp_port_monitor_ai',)
            ).fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"[ERROR] 获取端口监控AI员工失败: {e}")
        return None


def init_port_monitor():
    """初始化端口监控"""
    init_port_monitor_tables()
    sync_port_configs()
    sync_port_params()
    create_port_monitor_employee()


if __name__ == '__main__':
    init_port_monitor()
    logger.info("端口监控服务初始化完成")
