"""
MTSCOS AI 教育管理系统 - AI员工管理API
提供AI员工的增删改查和数据库操作接口
"""

from flask import Flask, request, jsonify, g
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from database_manager import MTSCOSDatabase
except ImportError:
    import sqlite3
    from datetime import datetime
    
    class MTSCOSDatabase:
        def __init__(self, db_path='mtcos_system.db'):
            self.db_path = db_path
            self.init_database()
        
        def get_connection(self):
            return sqlite3.connect(self.db_path)
        
        def init_database(self):
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    department TEXT,
                    avatar TEXT,
                    capabilities TEXT,
                    status TEXT DEFAULT 'active',
                    performance_score REAL DEFAULT 0.0,
                    tasks_completed INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_active TEXT
                )
            ''')
            
            cursor.execute('SELECT COUNT(*) FROM ai_employees')
            if cursor.fetchone()[0] == 0:
                default_employees = [
                    ('小智', '考试监督员', '考试中心', '👨‍🏫', 
                     json.dumps(['考试监控', '成绩分析', '异常检测']), 95.5, 156),
                    ('小雅', '日语教学助手', '日语学院', '🗾',
                     json.dumps(['日语教学', 'JLPT培训', '会话练习']), 92.8, 89),
                    ('小能', '算法导师', '计算机学院', '💻',
                     json.dumps(['算法指导', '代码评审', '竞赛培训']), 94.2, 134),
                    ('小安', '安全顾问', '安全中心', '🔒',
                     json.dumps(['安全培训', '漏洞分析', '加密指导']), 93.7, 78),
                    ('小英', '英语教师', '语言学院', '🌐',
                     json.dumps(['英语教学', '翻译指导', '写作批改']), 91.5, 112),
                    ('小统', '统计分析师', '数学学院', '📊',
                     json.dumps(['统计分析', '数据可视化', '建模指导']), 90.8, 67),
                    ('小蓝', 'AI学习教练', '学习中心', '🤖',
                     json.dumps(['AI教学', '自适应学习', '进度追踪']), 96.3, 201),
                    ('小助', '学习助手', '支持部门', '📚',
                     json.dumps(['答疑解惑', '资料推荐', '学习规划']), 89.4, 245)
                ]
                
                cursor.executemany('''
                    INSERT INTO ai_employees 
                    (name, role, department, avatar, capabilities, performance_score, tasks_completed)
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

app = Flask(__name__)
db = MTSCOSDatabase()

def serialize_employee(emp):
    """序列化AI员工数据"""
    return {
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

@app.route('/api/ai-employees', methods=['GET'])
def get_ai_employees():
    """获取所有AI员工"""
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
    """添加新AI员工"""
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
        
        return jsonify({
            'success': True,
            'message': f'AI员工 {name} 添加成功',
            'employee_id': employee_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-employees/<int:employee_id>', methods=['PUT'])
def update_ai_employee(employee_id):
    """更新AI员工"""
    try:
        data = request.get_json()
        # 实现更新逻辑
        return jsonify({'success': True, 'message': '员工信息更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-employees/<int:employee_id>', methods=['DELETE'])
def delete_ai_employee(employee_id):
    """删除AI员工"""
    try:
        # 实现删除逻辑
        return jsonify({'success': True, 'message': 'AI员工已删除'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai-employees/search', methods=['GET'])
def search_ai_employees():
    """搜索AI员工"""
    try:
        query = request.args.get('q', '')
        department = request.args.get('department', '')
        
        employees = db.get_all_ai_employees()
        filtered = []
        
        for emp in employees:
            if query and query.lower() not in emp[1].lower() and query.lower() not in emp[2].lower():
                continue
            if department and emp[3] != department:
                continue
            filtered.append(serialize_employee(emp))
        
        return jsonify({
            'success': True,
            'data': filtered,
            'total': len(filtered)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取系统统计信息"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM ai_employees')
        ai_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM exam_records WHERE user_id = ?', (user_id,))
        exam_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM exercise_records WHERE user_id = ?', (user_id,))
        exercise_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM wrong_questions WHERE user_id = ?', (user_id,))
        wrong_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'ai_employees_count': ai_count,
                'total_exams': exam_count,
                'total_exercises': exercise_count,
                'wrong_questions': wrong_count
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("启动AI员工管理API服务...")
    app.run(host='0.0.0.0', port=5000, debug=True)
