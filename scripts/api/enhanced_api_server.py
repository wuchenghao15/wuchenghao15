#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 增强版API服务器
集成AI员工管理、JSON自动同步、系统管理等功能
强制HTTPS登录支持
"""

from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
import sys
import os
import json
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入各模块
try:
    from integrated_system_manager import IntegratedSystemManager
    from ai_employee_manager import AIEmployeeManager
    from json_auto_sync_system import EnhancedJSONSyncManager
except ImportError as e:
    print(f"警告: 部分模块导入失败: {e}")
    # 提供基础实现
    AIEmployeeManager = None
    EnhancedJSONSyncManager = None

app = Flask(__name__, static_folder='.', static_url_path='')

# HTTPS配置
FORCE_HTTPS = True
SSL_CERT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ssl', 'cert.pem')
SSL_KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ssl', 'key.pem')

# 安全相关的路由（需要HTTPS）
SECURE_ROUTES = [
    '/api/login',
    '/api/logout',
    '/api/register',
    '/api/user/profile',
    '/api/user/settings',
    '/api/change-password',
    '/api/security/',
    '/api/auth/',
    '/api/token/',
]

def is_secure_route(path):
    """检查是否为安全路由"""
    for route in SECURE_ROUTES:
        if path.startswith(route):
            return True
    return False

# 全局管理器实例
system_manager = None
emp_manager = None
json_sync_manager = None

# 操作日志数据库
LOGS_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'operation_logs.db')


def initialize_logs_db():
    """初始化操作日志数据库"""
    conn = sqlite3.connect(LOGS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL,
            category TEXT,
            data TEXT,
            timestamp TEXT NOT NULL,
            user_agent TEXT,
            status TEXT DEFAULT 'success'
        )
    ''')
    conn.commit()
    conn.close()


def log_operation_to_db(operation, data=None, category=None, status='success'):
    """记录操作到数据库"""
    try:
        conn = sqlite3.connect(LOGS_DB)
        cursor = conn.cursor()
        data_json = json.dumps(data, ensure_ascii=False) if data else None
        cursor.execute('''
            INSERT INTO operation_logs (operation, category, data, timestamp, user_agent, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            operation,
            category,
            data_json,
            datetime.now().isoformat(),
            request.user_agent.string if request else None,
            status
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️  记录操作日志失败: {e}")


def initialize_managers():
    """初始化管理器"""
    global system_manager, emp_manager, json_sync_manager

    project_root = os.path.dirname(os.path.abspath(__file__))

    try:
        # 尝试初始化综合管理器
        if 'IntegratedSystemManager' in globals():
            system_manager = IntegratedSystemManager(project_root=project_root)
            emp_manager = system_manager.emp_manager
            json_sync_manager = system_manager.json_sync_manager
            print("✅ 综合系统管理器已初始化")
    except Exception as e:
        print(f"⚠️  综合系统管理器初始化失败: {e}")

    # 备用初始化
    if not emp_manager and AIEmployeeManager:
        try:
            emp_manager = AIEmployeeManager()
            print("✅ AI员工管理器已初始化(备用)")
        except Exception as e:
            print(f"⚠️  AI员工管理器初始化失败: {e}")

    if not json_sync_manager and EnhancedJSONSyncManager:
        try:
            json_sync_manager = EnhancedJSONSyncManager(
                db_path=os.path.join(project_root, 'mtcos_json_sync.db'),
                project_root=project_root
            )
            print("✅ JSON同步管理器已初始化(备用)")
        except Exception as e:
            print(f"⚠️  JSON同步管理器初始化失败: {e}")

    # 初始化日志数据库
    initialize_logs_db()
    print("✅ 操作日志数据库已初始化")


# HTTPS强制重定向中间件
@app.before_request
def enforce_https():
    """强制安全路由使用HTTPS"""
    if FORCE_HTTPS:
        # 检查是否为安全路由
        if is_secure_route(request.path):
            # 检查是否已经是HTTPS
            if request.scheme == 'http':
                # 构建HTTPS URL
                https_url = request.url.replace('http://', 'https://', 1)
                return redirect(https_url, code=301)

# 安全HTTP头中间件
@app.after_request
def add_security_headers(response):
    # 安全相关的HTTP头
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # CORS配置
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    return response


# ========== 静态文件服务 ==========
@app.route('/')
def index():
    """主页"""
    return send_from_directory('frontend/pages', 'index.html')


@app.route('/<filename>.html')
def serve_html_file(filename):
    """直接提供 .html 文件"""
    # 先尝试在 frontend/pages/ 中查找
    pages_path = os.path.join('frontend', 'pages', f'{filename}.html')
    if os.path.exists(pages_path) and os.path.isfile(pages_path):
        return send_from_directory('frontend/pages', f'{filename}.html')
    
    # 然后尝试在 frontend/ 中查找
    frontend_path = os.path.join('frontend', f'{filename}.html')
    if os.path.exists(frontend_path) and os.path.isfile(frontend_path):
        return send_from_directory('frontend', f'{filename}.html')
    
    # 最后尝试在根目录查找
    if os.path.exists(f'{filename}.html') and os.path.isfile(f'{filename}.html'):
        return send_from_directory('.', f'{filename}.html')
    
    return jsonify({'error': 'File not found'}), 404


# 处理直接访问 assets 的情况
@app.route('/assets/<path:filename>')
def serve_assets_direct(filename):
    """直接提供 assets 文件"""
    return send_from_directory('frontend/assets', filename)


@app.route('/css/<path:filename>')
def serve_css_direct(filename):
    """直接提供 css 文件"""
    return send_from_directory('frontend/assets/css', filename)


@app.route('/js/<path:filename>')
def serve_js_direct(filename):
    """直接提供 js 文件"""
    return send_from_directory('frontend/assets/js', filename)


@app.route('/frontend/pages/<path:filename>')
def serve_pages(filename):
    """提供前端页面"""
    return send_from_directory('frontend/pages', filename)


@app.route('/frontend/assets/<path:filename>')
def serve_assets(filename):
    """提供前端静态资源"""
    return send_from_directory('frontend/assets', filename)


# ========== 健康检查与系统信息 ==========
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    try:
        # 简单的数据库检查
        if emp_manager:
            emp_manager.get_all_employees()

        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '3.3.0'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/version', methods=['GET'])
def get_version():
    """获取系统版本"""
    try:
        with open('VERSION', 'r', encoding='utf-8') as f:
            version = f.readline().strip()
    except:
        version = '3.3.0'

    return jsonify({
        'success': True,
        'version': version,
        'name': 'MTSCOS AI Project (Enhanced)'
    })


@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        if system_manager:
            status = system_manager.get_system_status()
            return jsonify({
                'success': True,
                'data': status
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'is_running': True,
                    'timestamp': datetime.now().isoformat(),
                    'components': {}
                }
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========== 操作日志API ==========
@app.route('/api/logs', methods=['POST'])
def record_operation_logs():
    """记录操作日志（兼容旧接口）"""
    try:
        data = request.get_json() or {}
        operation = data.get('operation', 'unknown')
        category = data.get('category')
        log_data = data.get('data')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        user_agent = data.get('user_agent')

        log_operation_to_db(operation, log_data, category, 'success')

        print(f"📝 记录操作日志: {operation}")

        return jsonify({
            'success': True,
            'message': 'Log recorded successfully'
        })
    except Exception as e:
        print(f"⚠️  记录操作日志失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/operation/log', methods=['POST'])
def record_operation():
    """记录操作日志"""
    try:
        data = request.get_json() or {}
        operation = data.get('operation', 'unknown')
        category = data.get('category')
        log_data = data.get('data')

        log_operation_to_db(operation, log_data, category, 'success')

        print(f"📝 记录操作日志: {operation}")

        return jsonify({
            'success': True,
            'message': 'Log recorded successfully'
        })
    except Exception as e:
        print(f"⚠️  记录操作日志失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/logs', methods=['GET'])
def get_operation_logs():
    """获取操作日志（兼容旧接口）"""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        conn = sqlite3.connect(LOGS_DB)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, operation, category, data, timestamp, user_agent, status
            FROM operation_logs
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))

        logs = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row[3]) if row[3] else None
            except:
                data = row[3]

            logs.append({
                'id': row[0],
                'operation': row[1],
                'category': row[2],
                'data': data,
                'timestamp': row[4],
                'user_agent': row[5],
                'status': row[6]
            })

        conn.close()

        return jsonify({
            'success': True,
            'data': logs,
            'total': len(logs)
        })
    except Exception as e:
        print(f"⚠️  获取操作日志失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/operation/logs', methods=['GET'])
def get_logs():
    """获取操作日志"""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        conn = sqlite3.connect(LOGS_DB)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, operation, category, data, timestamp, user_agent, status
            FROM operation_logs
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))

        logs = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row[3]) if row[3] else None
            except:
                data = row[3]

            logs.append({
                'id': row[0],
                'operation': row[1],
                'category': row[2],
                'data': data,
                'timestamp': row[4],
                'user_agent': row[5],
                'status': row[6]
            })

        conn.close()

        return jsonify({
            'success': True,
            'data': logs,
            'total': len(logs)
        })
    except Exception as e:
        print(f"⚠️  获取操作日志失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========== AI员工管理API ==========
@app.route('/api/ai-employees', methods=['GET'])
def get_ai_employees():
    """获取所有AI员工"""
    try:
        if emp_manager:
            employees = emp_manager.get_all_employees()

            result = []
            for emp in employees:
                try:
                    capabilities = json.loads(emp[5]) if emp[5] else []
                except:
                    capabilities = []

                result.append({
                    'id': emp[0],
                    'name': emp[1],
                    'role': emp[2],
                    'department': emp[3],
                    'avatar': emp[4],
                    'capabilities': capabilities,
                    'status': emp[6],
                    'performance_score': emp[7],
                    'tasks_completed': emp[8],
                    'created_at': emp[9],
                    'last_active': emp[10]
                })

            return jsonify({
                'success': True,
                'data': result,
                'total': len(result)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Employee manager not available'
            }), 503
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai-employees', methods=['POST'])
def add_ai_employee():
    """添加AI员工"""
    try:
        if not emp_manager:
            return jsonify({
                'success': False,
                'error': 'Employee manager not available'
            }), 503

        data = request.get_json()
        name = data.get('name')
        role = data.get('role')
        department = data.get('department')
        avatar = data.get('avatar', '🤖')
        capabilities = data.get('capabilities', [])
        performance_score = data.get('performance_score', 85.0)

        if not name or not role:
            return jsonify({
                'success': False,
                'error': 'Name and role are required'
            }), 400

        # 使用综合管理器的同步方法
        if system_manager:
            emp_id = system_manager.add_ai_employee_with_sync(
                name, role, department, avatar, capabilities, performance_score
            )
        else:
            emp_id = emp_manager.add_employee(
                name, role, department, avatar, capabilities, performance_score
            )

        log_operation_to_db('add_ai_employee', {
            'name': name,
            'role': role,
            'id': emp_id
        }, 'ai_employees', 'success')

        return jsonify({
            'success': True,
            'message': f'AI employee {name} added successfully',
            'employee_id': emp_id
        })
    except Exception as e:
        log_operation_to_db('add_ai_employee_failed', str(e), 'ai_employees', 'error')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai-employees/<int:id>', methods=['GET'])
def get_employee(id):
    """获取单个AI员工详情"""
    try:
        if not emp_manager:
            return jsonify({
                'success': False,
                'error': 'Employee manager not available'
            }), 503

        employees = emp_manager.get_all_employees()
        for emp in employees:
            if emp[0] == id:
                try:
                    capabilities = json.loads(emp[5]) if emp[5] else []
                except:
                    capabilities = []

                return jsonify({
                    'success': True,
                    'data': {
                        'id': emp[0],
                        'name': emp[1],
                        'role': emp[2],
                        'department': emp[3],
                        'avatar': emp[4],
                        'capabilities': capabilities,
                        'status': emp[6],
                        'performance_score': emp[7],
                        'tasks_completed': emp[8],
                        'created_at': emp[9],
                        'last_active': emp[10]
                    }
                })

        return jsonify({
            'success': False,
            'error': 'Employee not found'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai-employees/<int:id>', methods=['PUT'])
def update_employee(id):
    """更新AI员工信息"""
    try:
        if not emp_manager:
            return jsonify({
                'success': False,
                'error': 'Employee manager not available'
            }), 503

        data = request.get_json()
        name = data.get('name')
        role = data.get('role')
        department = data.get('department')
        status = data.get('status')

        conn = emp_manager._connect() if hasattr(emp_manager, '_connect') else None
        if not conn:
            conn = sqlite3.connect(emp_manager.db_path)

        cursor = conn.cursor()

        updates = []
        params = []
        if name:
            updates.append('name = ?')
            params.append(name)
        if role:
            updates.append('role = ?')
            params.append(role)
        if department is not None:
            updates.append('department = ?')
            params.append(department)
        if status:
            updates.append('status = ?')
            params.append(status)

        if updates:
            params.append(id)
            cursor.execute(f'UPDATE ai_employees SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()

        conn.close()

        if system_manager:
            system_manager._sync_employee_to_json(id)

        log_operation_to_db('update_ai_employee', {
            'id': id,
            'name': name,
            'role': role
        }, 'ai_employees', 'success')

        return jsonify({
            'success': True,
            'message': 'Employee updated successfully'
        })
    except Exception as e:
        log_operation_to_db('update_ai_employee_failed', str(e), 'ai_employees', 'error')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai-employees/<int:id>', methods=['DELETE'])
def delete_ai_employee(id):
    """删除AI员工"""
    try:
        if not emp_manager:
            return jsonify({
                'success': False,
                'error': 'Employee manager not available'
            }), 503

        emp_manager.delete_employee(id)

        log_operation_to_db('delete_ai_employee', {'id': id}, 'ai_employees', 'success')

        return jsonify({
            'success': True,
            'message': 'Employee deleted successfully'
        })
    except Exception as e:
        log_operation_to_db('delete_ai_employee_failed', str(e), 'ai_employees', 'error')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai-employees/department/<string:department>', methods=['GET'])
def get_employees_by_department(department):
    """按部门获取AI员工"""
    try:
        if not emp_manager:
            return jsonify({
                'success': False,
                'error': 'Employee manager not available'
            }), 503

        employees = emp_manager.get_all_employees()

        result = []
        for emp in employees:
            if emp[3] == department:
                try:
                    capabilities = json.loads(emp[5]) if emp[5] else []
                except:
                    capabilities = []

                result.append({
                    'id': emp[0],
                    'name': emp[1],
                    'role': emp[2],
                    'department': emp[3],
                    'avatar': emp[4],
                    'capabilities': capabilities,
                    'status': emp[6],
                    'performance_score': emp[7],
                    'tasks_completed': emp[8],
                    'created_at': emp[9],
                    'last_active': emp[10]
                })

        return jsonify({
            'success': True,
            'data': result,
            'total': len(result)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ai-employees/search/<string:keyword>', methods=['GET'])
def search_employees(keyword):
    """搜索AI员工"""
    try:
        if not emp_manager:
            return jsonify({
                'success': False,
                'error': 'Employee manager not available'
            }), 503

        employees = emp_manager.get_all_employees()

        search_lower = keyword.lower()
        result = []
        for emp in employees:
            name = str(emp[1]).lower()
            role = str(emp[2]).lower()
            dept = str(emp[3]).lower() if emp[3] else ''
            caps = str(emp[5]).lower() if emp[5] else ''

            if (search_lower in name or search_lower in role or
                search_lower in dept or search_lower in caps):
                try:
                    capabilities = json.loads(emp[5]) if emp[5] else []
                except:
                    capabilities = []

                result.append({
                    'id': emp[0],
                    'name': emp[1],
                    'role': emp[2],
                    'department': emp[3],
                    'avatar': emp[4],
                    'capabilities': capabilities,
                    'status': emp[6],
                    'performance_score': emp[7],
                    'tasks_completed': emp[8],
                    'created_at': emp[9],
                    'last_active': emp[10]
                })

        return jsonify({
            'success': True,
            'data': result,
            'total': len(result),
            'keyword': keyword
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/departments', methods=['GET'])
def get_all_departments():
    """获取所有部门统计"""
    try:
        if not emp_manager:
            return jsonify({
                'success': False,
                'error': 'Employee manager not available'
            }), 503

        employees = emp_manager.get_all_employees()

        dept_stats = {}
        for emp in employees:
            dept = emp[3] if emp[3] else '未分配'
            if dept not in dept_stats:
                dept_stats[dept] = {
                    'department': dept,
                    'employee_count': 0,
                    'total_performance': 0.0,
                    'total_tasks': 0
                }

            dept_stats[dept]['employee_count'] += 1
            dept_stats[dept]['total_performance'] += emp[7] if emp[7] else 0
            dept_stats[dept]['total_tasks'] += emp[8] if emp[8] else 0

        result = []
        for dept, stats in dept_stats.items():
            avg_perf = stats['total_performance'] / stats['employee_count'] if stats['employee_count'] > 0 else 0
            result.append({
                'department': dept,
                'employee_count': stats['employee_count'],
                'avg_performance_score': round(avg_perf, 2),
                'total_tasks': stats['total_tasks']
            })

        result.sort(key=lambda x: x['employee_count'], reverse=True)

        return jsonify({
            'success': True,
            'data': result,
            'total': len(result)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========== JSON同步API ==========
@app.route('/api/json-sync/status', methods=['GET'])
def get_sync_status():
    """获取同步状态"""
    try:
        if json_sync_manager:
            stats = json_sync_manager.get_statistics()
            return jsonify({
                'success': True,
                'data': stats
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'total_files': 0,
                    'synced_files': 0,
                    'total_versions': 0,
                    'success_count': 0
                }
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/json-sync/files', methods=['GET'])
def get_sync_files():
    """获取已同步的文件列表"""
    try:
        if json_sync_manager:
            files = json_sync_manager.get_registered_files()
            return jsonify({
                'success': True,
                'data': files
            })
        else:
            return jsonify({
                'success': True,
                'data': []
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/json-sync/logs', methods=['GET'])
def get_sync_logs():
    """获取同步日志"""
    try:
        limit = request.args.get('limit', 50, type=int)
        if json_sync_manager:
            logs = json_sync_manager.get_sync_logs(limit=limit)
            return jsonify({
                'success': True,
                'data': logs
            })
        else:
            return jsonify({
                'success': True,
                'data': []
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/json-sync/sync', methods=['POST'])
def trigger_sync():
    """手动触发同步"""
    try:
        if json_sync_manager:
            count = json_sync_manager.sync_all_files()
            log_operation_to_db('trigger_json_sync', {'count': count}, 'json_sync', 'success')
            return jsonify({
                'success': True,
                'synced_files': count
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Sync manager not available'
            }), 503
    except Exception as e:
        log_operation_to_db('trigger_json_sync_failed', str(e), 'json_sync', 'error')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/json-sync/scan', methods=['POST'])
def scan_files():
    """扫描JSON文件"""
    try:
        if json_sync_manager:
            count = json_sync_manager.scan_directory()
            log_operation_to_db('scan_json_files', {'count': count}, 'json_sync', 'success')
            return jsonify({
                'success': True,
                'found_files': count
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Sync manager not available'
            }), 503
    except Exception as e:
        log_operation_to_db('scan_json_files_failed', str(e), 'json_sync', 'error')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/json-sync/file/<path:file_path>', methods=['GET'])
def get_file_content(file_path):
    """获取JSON文件内容"""
    try:
        if json_sync_manager:
            version = request.args.get('version', type=int)
            content = json_sync_manager.get_json_content(file_path, version=version)
            if content:
                return jsonify({
                    'success': True,
                    'data': content
                })
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        else:
            return jsonify({
                'success': False,
                'error': 'Sync manager not available'
            }), 503
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========== 统计API ==========
@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取系统统计信息"""
    try:
        stats = {
            'ai_employees': {},
            'json_sync': {},
            'operation_logs': {},
            'system': {
                'timestamp': datetime.now().isoformat(),
                'version': '3.3.0'
            }
        }

        if emp_manager:
            employees = emp_manager.get_all_employees()
            stats['ai_employees'] = {
                'count': len(employees),
                'avg_performance': round(sum(e[7] for e in employees if e[7]) / len(employees) if employees else 0, 1),
                'total_tasks': sum(e[8] for e in employees if e[8])
            }

        if json_sync_manager:
            sync_stats = json_sync_manager.get_statistics()
            stats['json_sync'] = sync_stats

        try:
            conn = sqlite3.connect(LOGS_DB)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM operation_logs')
            log_count = cursor.fetchone()[0]
            stats['operation_logs'] = {
                'total_count': log_count
            }
            conn.close()
        except:
            stats['operation_logs'] = {'total_count': 0}

        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========== 通用静态文件路由（放在所有API路由之后） ==========
@app.route('/<path:filename>')
def serve_static(filename):
    """提供其他静态文件"""
    # 尝试多个可能的位置
    possible_paths = [
        os.path.join('frontend', 'pages', filename),
        os.path.join('frontend', filename),
        os.path.join('frontend', 'assets', filename),
        filename
    ]

    for path in possible_paths:
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path))

    # 如果找不到文件，返回404
    return jsonify({'error': 'File not found'}), 404


def generate_self_signed_cert():
    """生成自签名SSL证书"""
    ssl_dir = os.path.dirname(SSL_CERT_PATH)
    os.makedirs(ssl_dir, exist_ok=True)
    
    if os.path.exists(SSL_CERT_PATH) and os.path.exists(SSL_KEY_PATH):
        print("✅ SSL证书已存在")
        return True
    
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
        
        print("🔐 生成自签名SSL证书...")
        
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # 生成公钥
        public_key = private_key.public_key()
        
        # 创建证书签名请求
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MTSCOS AI"),
            x509.NameAttribute(NameOID.COMMON_NAME, "mtscos.local"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            public_key
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())
        
        # 保存证书和密钥
        with open(SSL_CERT_PATH, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        with open(SSL_KEY_PATH, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))
        
        print("✅ SSL证书生成成功")
        return True
    except ImportError:
        print("⚠️  cryptography库未安装，无法生成SSL证书")
        return False
    except Exception as e:
        print(f"⚠️  SSL证书生成失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 80)
    print("🚀 MTSCOS 增强版API服务器")
    print("=" * 80)

    print("\n🔧 初始化系统管理器...")
    initialize_managers()

    print("\n🔐 配置HTTPS安全连接...")
    if FORCE_HTTPS:
        generate_self_signed_cert()
        print("✅ HTTPS强制登录已启用")
        print("   安全路由将自动重定向到HTTPS")
        print("   安全路由列表:", SECURE_ROUTES)

    print("\n📡 API端点:")
    print("   • 健康检查: GET /api/health")
    print("   • 系统版本: GET /api/version")
    print("   • 系统状态: GET /api/system/status")
    print("")
    print("   • AI员工列表: GET /api/ai-employees")
    print("   • 添加AI员工: POST /api/ai-employees")
    print("   • 获取员工详情: GET /api/ai-employees/<id>")
    print("   • 更新员工: PUT /api/ai-employees/<id>")
    print("   • 删除员工: DELETE /api/ai-employees/<id>")
    print("   • 按部门查询: GET /api/ai-employees/department/<dept>")
    print("   • 搜索员工: GET /api/ai-employees/search/<keyword>")
    print("   • 部门统计: GET /api/departments")
    print("")
    print("   • 同步状态: GET /api/json-sync/status")
    print("   • 同步文件: GET /api/json-sync/files")
    print("   • 同步日志: GET /api/json-sync/logs")
    print("   • 触发同步: POST /api/json-sync/sync")
    print("   • 扫描文件: POST /api/json-sync/scan")
    print("   • 获取文件内容: GET /api/json-sync/file/<path>")
    print("")
    print("   • 记录操作日志: POST /api/logs, POST /api/operation/log")
    print("   • 获取操作日志: GET /api/logs, GET /api/operation/logs")
    print("   • 系统统计: GET /api/statistics")

    print("\n🔒 安全特性:")
    print("   • HTTPS强制登录: ✅")
    print("   • HSTS头: ✅")
    print("   • X-Content-Type-Options: ✅")
    print("   • X-Frame-Options: ✅")
    print("   • XSS保护: ✅")
    print("   • 内容安全策略: ✅")

    print("\n" + "=" * 80)
    if FORCE_HTTPS:
        print("💡 服务器启动在 https://0.0.0.0:8888")
        print("   HTTP端口: 8888")
        print("   HTTPS端口: 8443")
        print("=" * 80)

        # 检查SSL证书是否存在
        if os.path.exists(SSL_CERT_PATH) and os.path.exists(SSL_KEY_PATH):
            # 尝试启动HTTPS服务器
            try:
                from flask_sslify import SSLify
                sslify = SSLify(app)
                app.run(host='0.0.0.0', port=8888, debug=False, threaded=True,
                        ssl_context=(SSL_CERT_PATH, SSL_KEY_PATH))
            except ImportError:
                print("⚠️  flask-sslify未安装，使用内置SSL支持")
                app.run(host='0.0.0.0', port=8888, debug=False, threaded=True,
                        ssl_context=(SSL_CERT_PATH, SSL_KEY_PATH))
            except Exception as e:
                print(f"⚠️  HTTPS启动失败，降级到HTTP: {e}")
                app.run(host='0.0.0.0', port=8888, debug=False, threaded=True)
        else:
            print("⚠️  SSL证书不存在，使用HTTP启动")
            app.run(host='0.0.0.0', port=8888, debug=False, threaded=True)
    else:
        print("💡 服务器启动在 http://0.0.0.0:8888")
        print("=" * 80)
        app.run(host='0.0.0.0', port=8888, debug=False, threaded=True)


if __name__ == '__main__':
    main()
