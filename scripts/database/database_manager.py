"""
MTSCOS AI 教育管理系统 - 数据库管理模块
支持考试系统、AI员工、操作日志等数据存储
"""

import sqlite3
import json
from datetime import datetime
import os

class MTSCOSDatabase:
    def __init__(self, db_path='mtcos_system.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 考试记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                exam_name TEXT NOT NULL,
                exam_type TEXT,
                score INTEGER,
                total_score INTEGER,
                status TEXT DEFAULT 'completed',
                start_time TEXT,
                end_time TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 练习记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercise_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                exercise_name TEXT NOT NULL,
                course_type TEXT,
                questions_count INTEGER,
                correct_count INTEGER,
                duration INTEGER,
                completed_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # AI员工表
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
        
        # 操作日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                operation_type TEXT NOT NULL,
                operation_details TEXT,
                module TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 错题记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wrong_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                question_title TEXT NOT NULL,
                course_type TEXT,
                knowledge_point TEXT,
                wrong_count INTEGER DEFAULT 1,
                last_wrong_time TEXT,
                status TEXT DEFAULT 'unreviewed',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 学习计划表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                plan_name TEXT NOT NULL,
                plan_type TEXT,
                tasks TEXT,
                progress REAL DEFAULT 0.0,
                status TEXT DEFAULT 'active',
                start_date TEXT,
                end_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                user_group TEXT,
                student_type TEXT,
                total_exams INTEGER DEFAULT 0,
                total_exercises INTEGER DEFAULT 0,
                avg_score REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.init_default_ai_employees()
    
    def init_default_ai_employees(self):
        """初始化默认AI员工"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
    
    # ==================== 考试记录操作 ====================
    def save_exam_record(self, user_id, exam_name, exam_type, score, total_score, start_time, end_time):
        """保存考试记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO exam_records 
            (user_id, exam_name, exam_type, score, total_score, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, exam_name, exam_type, score, total_score, start_time, end_time))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.log_operation(user_id, 'exam_completed', 
                          f'完成考试: {exam_name}, 得分: {score}/{total_score}', 'exam')
        
        return record_id
    
    def get_user_exam_records(self, user_id, limit=10):
        """获取用户的考试记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM exam_records 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        records = cursor.fetchall()
        conn.close()
        return records
    
    # ==================== 练习记录操作 ====================
    def save_exercise_record(self, user_id, exercise_name, course_type, 
                            questions_count, correct_count, duration):
        """保存练习记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO exercise_records 
            (user_id, exercise_name, course_type, questions_count, correct_count, duration)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, exercise_name, course_type, questions_count, correct_count, duration))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.log_operation(user_id, 'exercise_completed',
                          f'完成练习: {exercise_name}, 正确率: {correct_count}/{questions_count}', 'exercise')
        
        return record_id
    
    def get_user_exercise_records(self, user_id, limit=20):
        """获取用户的练习记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM exercise_records 
            WHERE user_id = ? 
            ORDER BY completed_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        records = cursor.fetchall()
        conn.close()
        return records
    
    # ==================== AI员工操作 ====================
    def get_all_ai_employees(self):
        """获取所有AI员工"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ai_employees ORDER BY performance_score DESC')
        employees = cursor.fetchall()
        conn.close()
        
        return employees
    
    def get_ai_employee_by_role(self, role):
        """根据角色获取AI员工"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ai_employees WHERE role LIKE ?', (f'%{role}%',))
        employee = cursor.fetchone()
        conn.close()
        
        return employee
    
    def update_ai_employee_performance(self, employee_id, task_completed=True, score_delta=0.0):
        """更新AI员工绩效"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if task_completed:
            cursor.execute('''
                UPDATE ai_employees 
                SET tasks_completed = tasks_completed + 1,
                    performance_score = (performance_score * tasks_completed + ?) / (tasks_completed + 1),
                    last_active = ?
                WHERE id = ?
            ''', (score_delta, datetime.now().isoformat(), employee_id))
        else:
            cursor.execute('''
                UPDATE ai_employees 
                SET last_active = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), employee_id))
        
        conn.commit()
        conn.close()
    
    def add_ai_employee(self, name, role, department, avatar, capabilities):
        """添加新的AI员工"""
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
        
        self.log_operation('system', 'ai_employee_added',
                          f'新增AI员工: {name} ({role})', 'ai_employees')
        
        return employee_id
    
    # ==================== 错题记录操作 ====================
    def add_wrong_question(self, user_id, question_title, course_type, knowledge_point):
        """添加错题记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, wrong_count FROM wrong_questions 
            WHERE user_id = ? AND question_title = ?
        ''', (user_id, question_title))
        
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE wrong_questions 
                SET wrong_count = wrong_count + 1,
                    last_wrong_time = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), existing[0]))
        else:
            cursor.execute('''
                INSERT INTO wrong_questions 
                (user_id, question_title, course_type, knowledge_point, last_wrong_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, question_title, course_type, knowledge_point, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_user_wrong_questions(self, user_id, limit=50):
        """获取用户的错题列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM wrong_questions 
            WHERE user_id = ? 
            ORDER BY wrong_count DESC, last_wrong_time DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        questions = cursor.fetchall()
        conn.close()
        return questions
    
    # ==================== 学习计划操作 ====================
    def save_study_plan(self, user_id, plan_name, plan_type, tasks, start_date, end_date):
        """保存学习计划"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        tasks_json = json.dumps(tasks) if isinstance(tasks, list) else tasks
        
        cursor.execute('''
            INSERT INTO study_plans 
            (user_id, plan_name, plan_type, tasks, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, plan_name, plan_type, tasks_json, start_date, end_date))
        
        plan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.log_operation(user_id, 'study_plan_created',
                          f'创建学习计划: {plan_name}', 'study_plan')
        
        return plan_id
    
    def update_study_plan_progress(self, plan_id, progress):
        """更新学习计划进度"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE study_plans SET progress = ? WHERE id = ?
        ''', (progress, plan_id))
        
        conn.commit()
        conn.close()
    
    # ==================== 操作日志 ====================
    def log_operation(self, user_id, operation_type, operation_details, module=''):
        """记录操作日志"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        details_json = json.dumps(operation_details) if isinstance(operation_details, dict) else operation_details
        
        cursor.execute('''
            INSERT INTO operation_logs 
            (user_id, operation_type, operation_details, module)
            VALUES (?, ?, ?, ?)
        ''', (user_id, operation_type, details_json, module))
        
        conn.commit()
        conn.close()
    
    def get_operation_logs(self, user_id=None, limit=100):
        """获取操作日志"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT * FROM operation_logs 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM operation_logs 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
        
        logs = cursor.fetchall()
        conn.close()
        return logs
    
    # ==================== 用户统计 ====================
    def get_user_statistics(self, user_id):
        """获取用户学习统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*), AVG(score * 1.0 / total_score * 100) 
            FROM exam_records WHERE user_id = ?
        ''', (user_id,))
        exam_stats = cursor.fetchone()
        
        cursor.execute('SELECT COUNT(*) FROM exercise_records WHERE user_id = ?', (user_id,))
        exercise_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM wrong_questions WHERE user_id = ? AND status = ?', 
                      (user_id, 'unreviewed'))
        wrong_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_exams': exam_stats[0] or 0,
            'avg_score': round(exam_stats[1] or 0, 1),
            'total_exercises': exercise_count,
            'wrong_questions': wrong_count
        }

if __name__ == '__main__':
    db = MTSCOSDatabase()
    print("数据库初始化完成！")
    
    employees = db.get_all_ai_employees()
    print(f"\n当前AI员工数量: {len(employees)}")
    for emp in employees:
        print(f"  - {emp[4]}: {emp[2]} ({emp[3]})")
