"""
MTSCOS AI 教育管理系统 - 统一API服务器
整合考试系统、AI员工管理、操作日志等功能
"""

from flask import Flask, request, jsonify, send_from_directory
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from database_manager import MTSCOSDatabase
except ImportError:
    import sqlite3
    
    class MTSCOSDatabase:
        def __init__(self, db_path='mtcos_system.db'):
            self.db_path = db_path
            self.init_database()
        
        def get_connection(self):
            return sqlite3.connect(self.db_path)
        
        def init_database(self):
            conn = self.get_connection()
            cursor = conn.cursor()
            
            tables = [
                '''CREATE TABLE IF NOT EXISTS ai_employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL, role TEXT NOT NULL, department TEXT,
                    avatar TEXT, capabilities TEXT, status TEXT DEFAULT 'active',
                    performance_score REAL DEFAULT 0.0, tasks_completed INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP, last_active TEXT)''',
                '''CREATE TABLE IF NOT EXISTS exam_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
                    exam_name TEXT NOT NULL, exam_type TEXT, score INTEGER,
                    total_score INTEGER, status TEXT DEFAULT 'completed',
                    start_time TEXT, end_time TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''',
                '''CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT,
                    operation_type TEXT NOT NULL, operation_details TEXT,
                    module TEXT, ip_address TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''
            ]
            
            for table_sql in tables:
                cursor.execute(table_sql)
            
            cursor.execute('SELECT COUNT(*) FROM ai_employees')
            if cursor.fetchone()[0] == 0:
                default_employees = [
                    ('小智', '考试监督员', '考试中心', '👨‍🏫', 
                     json.dumps(['考试监控', '成绩分析']), 95.5, 156),
                    ('小雅', '日语教学助手', '日语学院', '🗾',
                     json.dumps(['日语教学', 'JLPT培训']), 92.8, 89),
                    ('小能', '算法导师', '计算机学院', '💻',
                     json.dumps(['算法指导', '代码评审']), 94.2, 134),
                    ('小蓝', 'AI学习教练', '学习中心', '🤖',
                     json.dumps(['AI教学', '自适应学习']), 96.3, 201),
                ]
                cursor.executemany('''
                    INSERT INTO ai_employees (name, role, department, avatar, capabilities, performance_score, tasks_completed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', default_employees)
            
            conn.commit()
            conn.close()
        
        def get_all_ai_employees(self):
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM ai_employees ORDER BY performance_score DESC')
            employees = cursor.fetchall()
            conn.close()
            return employees
        
        def add_ai_employee(self, name, role, department, avatar, capabilities):
            conn = self.get_connection()
            cursor = conn.cursor()
            capabilities_json = json.dumps(capabilities) if isinstance(capabilities, list) else capabilities
            cursor.execute('''
                INSERT INTO ai_employees (name, role, department, avatar, capabilities)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, role, department, avatar, capabilities_json))
            employee_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return employee_id
        
        def delete_ai_employee(self, id):
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM ai_employees WHERE id = ?', (id,))
            conn.commit()
            conn.close()
        
        def log_operation(self, user_id, operation_type, operation_details, module=''):
            conn = self.get_connection()
            cursor = conn.cursor()
            details_json = json.dumps(operation_details) if isinstance(operation_details, dict) else operation_details
            cursor.execute('''
                INSERT INTO operation_logs (user_id, operation_type, operation_details, module)
                VALUES (?, ?, ?, ?)
            ''', (user_id, operation_type, details_json, module))
            conn.commit()
            conn.close()
        
        def save_exam_record(self, user_id, exam_name, exam_type, score, total_score, start_time, end_time):
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO exam_records (user_id, exam_name, exam_type, score, total_score, start_time, end_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, exam_name, exam_type, score, total_score, start_time, end_time))
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return record_id

app = Flask(__name__, static_folder='.', static_url_path='')
db = MTSCOSDatabase()

# Enable CORS for all routes
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

def serialize_employee(emp):
    return {
        'id': emp[0], 'name': emp[1], 'role': emp[2], 'department': emp[3],
        'avatar': emp[4], 'capabilities': json.loads(emp[5]) if emp[5] else [],
        'status': emp[6], 'performance_score': emp[7], 'tasks_completed': emp[8],
        'created_at': emp[9], 'last_active': emp[10]
    }

@app.route('/')
def index():
    return send_from_directory('frontend/pages', 'exam.html')

@app.route('/frontend/pages/<path:filename>')
def serve_pages(filename):
    return send_from_directory('frontend/pages', filename)

@app.route('/api/ai-employees', methods=['GET'])
def get_ai_employees():
    try:
        employees = db.get_all_ai_employees()
        return jsonify({
            'success': True,
            'data': [serialize_employee(emp) for emp in employees],
            'total': len(employees)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-employees', methods=['POST'])
def add_ai_employee():
    try:
        data = request.get_json()
        name = data.get('name')
        role = data.get('role')
        department = data.get('department', '')
        avatar = data.get('avatar', '🤖')
        capabilities = data.get('capabilities', [])
        
        if not name or not role:
            return jsonify({'success': False, 'error': '姓名和角色不能为空'}), 400
        
        employee_id = db.add_ai_employee(name, role, department, avatar, capabilities)
        db.log_operation('system', 'ai_employee_added', f'新增AI员工: {name} ({role})', 'ai_employees')
        
        return jsonify({
            'success': True,
            'message': f'AI员工 {name} 添加成功',
            'employee_id': employee_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-employees/<int:id>', methods=['DELETE'])
def delete_ai_employee(id):
    try:
        db.delete_ai_employee(id)
        db.log_operation('system', 'ai_employee_deleted', f'删除AI员工ID: {id}', 'ai_employees')
        
        return jsonify({
            'success': True,
            'message': 'AI员工删除成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/exam/save', methods=['POST'])
def save_exam():
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        exam_name = data.get('exam_name')
        exam_type = data.get('exam_type', '')
        score = data.get('score', 0)
        total_score = data.get('total_score', 100)
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        record_id = db.save_exam_record(user_id, exam_name, exam_type, score, total_score, start_time, end_time)
        db.log_operation(user_id, 'exam_completed', 
                        f'完成考试: {exam_name}, 得分: {score}/{total_score}', 'exam')
        
        return jsonify({
            'success': True,
            'message': '考试记录已保存',
            'record_id': record_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/operation/log', methods=['POST'])
def log_operation():
    try:
        content_type = request.content_type or ''
        
        if 'text/plain' in content_type:
            data = json.loads(request.data)
        else:
            data = request.get_json()
        
        user_id = data.get('user_id', 'anonymous')
        operation_type = data.get('operation_type')
        operation_details = data.get('operation_details', {})
        module = data.get('module', '')
        
        db.log_operation(user_id, operation_type, operation_details, module)
        
        return jsonify({'success': True, 'message': '操作日志已记录'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    try:
        db.get_all_ai_employees()
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/version', methods=['GET'])
def get_version():
    """获取系统版本"""
    try:
        with open('VERSION', 'r', encoding='utf-8') as f:
            version = f.readline().strip()
        return jsonify({
            'success': True,
            'version': version,
            'name': 'MTSCOS AI Project'
        })
    except:
        return jsonify({
            'success': True,
            'version': '3.3.0',
            'name': 'MTSCOS AI Project'
        })

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    try:
        employees = db.get_all_ai_employees()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM exam_records')
        total_exams = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'ai_employees_count': len(employees),
                'total_exams': total_exams,
                'total_exercises': 0,
                'avg_performance': round(sum(e[7] for e in employees) / len(employees), 1) if employees else 0,
                'total_tasks': sum(e[8] for e in employees)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/operation/logs', methods=['GET'])
def get_operation_logs():
    """获取操作日志"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM operation_logs ORDER BY created_at DESC LIMIT 50')
        logs = cursor.fetchall()
        conn.close()
        
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                'id': log[0],
                'user_id': log[1],
                'operation_type': log[2],
                'operation_details': log[3],
                'module': log[4],
                'ip_address': log[5],
                'created_at': log[6]
            })
        
        return jsonify({
            'success': True,
            'data': formatted_logs,
            'total': len(formatted_logs)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-employees/<int:id>', methods=['GET'])
def get_employee(id):
    """获取单个AI员工详情"""
    try:
        employees = db.get_all_ai_employees()
        for emp in employees:
            if emp[0] == id:
                return jsonify({
                    'success': True,
                    'data': {
                        'id': emp[0],
                        'name': emp[1],
                        'role': emp[2],
                        'department': emp[3],
                        'avatar': emp[4],
                        'capabilities': json.loads(emp[5]) if emp[5] else [],
                        'status': emp[6],
                        'performance_score': emp[7],
                        'tasks_completed': emp[8],
                        'created_at': emp[9],
                        'last_active': emp[10]
                    }
                })
        return jsonify({'success': False, 'error': 'Employee not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-employees/<int:id>', methods=['PUT'])
def update_employee(id):
    """更新AI员工信息"""
    try:
        data = request.get_json()
        name = data.get('name')
        role = data.get('role')
        department = data.get('department')
        status = data.get('status')
        
        conn = db.get_connection()
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
        
        return jsonify({
            'success': True,
            'message': 'Employee updated successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-employees/department/<string:department>', methods=['GET'])
def get_employees_by_department(department):
    """按部门获取AI员工"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ai_employees WHERE department = ? ORDER BY performance_score DESC', (department,))
        employees = cursor.fetchall()
        conn.close()
        
        result = []
        for emp in employees:
            try:
                capabilities = json.loads(emp[5])
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
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/departments', methods=['GET'])
def get_all_departments():
    """获取所有部门统计"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT department, COUNT(*), AVG(performance_score), SUM(tasks_completed)
            FROM ai_employees
            WHERE department IS NOT NULL
            GROUP BY department
            ORDER BY COUNT(*) DESC
        ''')
        departments = cursor.fetchall()
        conn.close()
        
        result = []
        for dept in departments:
            result.append({
                'department': dept[0],
                'employee_count': dept[1],
                'avg_performance_score': round(dept[2], 2) if dept[2] else 0,
                'total_tasks': dept[3]
            })
        
        return jsonify({
            'success': True,
            'data': result,
            'total': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-employees/search/<string:keyword>', methods=['GET'])
def search_employees(keyword):
    """搜索AI员工"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        search_pattern = f'%{keyword}%'
        cursor.execute('''
            SELECT * FROM ai_employees
            WHERE name LIKE ? OR role LIKE ? OR department LIKE ? OR capabilities LIKE ?
            ORDER BY performance_score DESC
        ''', (search_pattern, search_pattern, search_pattern, search_pattern))
        employees = cursor.fetchall()
        conn.close()
        
        result = []
        for emp in employees:
            try:
                capabilities = json.loads(emp[5])
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
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("MTSCOS AI 教育管理系统")
    print("=" * 60)
    print("启动统一API服务器...")
    print("版本: v3.3.0")
    print("功能模块:")
    print("  • AI员工管理系统 (28名AI员工)")
    print("  • 考试记录管理")
    print("  • 操作日志系统")
    print("  • 统计分析功能")
    print("API端点:")
    print("  • GET /api/health - 健康检查")
    print("  • GET /api/version - 版本信息")
    print("  • GET /api/ai-employees - AI员工列表")
    print("  • POST /api/ai-employees - 添加AI员工")
    print("  • GET /api/ai-employees/<id> - 获取AI员工详情")
    print("  • PUT /api/ai-employees/<id> - 更新AI员工")
    print("  • DELETE /api/ai-employees/<id> - 删除AI员工")
    print("  • GET /api/ai-employees/department/<dept> - 按部门查询")
    print("  • GET /api/ai-employees/search/<keyword> - 搜索AI员工")
    print("  • GET /api/departments - 部门统计")
    print("  • POST /api/operation/log - 记录操作日志")
    print("  • GET /api/operation/logs - 获取操作日志")
    print("  • GET /api/statistics - 统计数据")
    print("  • POST /api/exam/save - 保存考试记录")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5001, debug=True)
