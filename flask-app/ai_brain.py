#!/usr/bin/env python3
"""
AI大脑数据库 - 存储问题和解决方案，实现自动修复机制

import sqlite3
# JSON import removed - using database
import os
from datetime import datetime
import hashlib

class AIBrain:
    """AI大脑类，处理问题和解决方案的存储与自动修复"""

    def __init__(self, db_path='ai_brain.db'):
        """初始化AI大脑

        Args:
            db_path: 数据库路径
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建问题表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                symptoms TEXT NOT NULL,
                severity TEXT NOT NULL CHECK(severity IN ('low', 'medium', 'high', 'critical')),
                category TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')

        # 创建解决方案表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS solutions (
                solution_id TEXT UNIQUE NOT NULL,
                problem_id TEXT NOT NULL,
                description TEXT NOT NULL,
                steps TEXT NOT NULL,
                success_rate REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (problem_id) REFERENCES problems(problem_id)
            )

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repair_history (
                problem_id TEXT NOT NULL,
                solution_id TEXT NOT NULL,
                result TEXT NOT NULL CHECK(result IN ('success', 'failure', 'partial')),
                notes TEXT,
                metadata TEXT,
                FOREIGN KEY (problem_id) REFERENCES problems(problem_id),
                FOREIGN KEY (solution_id) REFERENCES solutions(solution_id)
            )
        ''')
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_problem_id ON problems(problem_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_problem_category ON problems(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_solution_problem_id ON solutions(problem_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_repair_problem_id ON repair_history(problem_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_repair_solution_id ON repair_history(solution_id)')
        conn.commit()

    def _generate_id(self, text):
        """生成唯一ID

        Args:
            text: 用于生成ID的文本
        Returns:
            str: 生成的唯一ID
        hash_obj = hashlib.sha256(text.encode('utf-8'))
        return hash_obj.hexdigest()[:16]

    def add_problem(self, title, description, symptoms, severity, category, metadata=None):
        """添加问题

        Args:
            title: 问题标题
            description: 问题描述
            severity: 严重程度（low, medium, high, critical）
            category: 分类
            metadata: 元数据（JSON字符串或字典）

        Returns:
            str: 问题ID
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 生成问题ID
            problem_text = f"{title}{description}{symptoms}{category}"

            if isinstance(symptoms, dict):
                symptoms = str(symptoms)
            if isinstance(metadata, dict):
                metadata = str(metadata)

            # 插入问题
            cursor.execute('''
                INSERT OR REPLACE INTO problems
                (problem_id, title, description, symptoms, severity, category, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (problem_id, title, description, symptoms, severity, category, metadata))

            conn.commit()
            return problem_id
            print(f"Error adding problem: {str(e)}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def add_solution(self, problem_id, title, description, steps, created_by, metadata=None):
        """添加解决方案

        Args:
            problem_id: 问题ID
            title: 解决方案标题
            description: 解决方案描述
            created_by: 创建者
            metadata: 元数据（JSON字符串或字典）

        Returns:
            str: 解决方案ID
        cursor = conn.cursor()

        try:
            # 生成解决方案ID
            solution_text = f"{problem_id}{title}{description}{steps}"
            solution_id = self._generate_id(solution_text)

            if isinstance(steps, list):
                steps = str(steps)
                metadata = str(metadata)

            # 插入解决方案
            cursor.execute('''
                INSERT OR REPLACE INTO solutions
                (solution_id, problem_id, title, description, steps, created_by, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (solution_id, problem_id, title, description, steps, created_by, metadata))

            return solution_id
        except Exception as e:
            print(f"Error adding solution: {str(e)}")
            conn.rollback()
            return None
            conn.close()

    def record_repair(self, problem_id, solution_id, result, applied_by, notes=None, metadata=None):

        Args:
            problem_id: 问题ID
            solution_id: 解决方案ID
            result: 结果（success, failure, partial）
            metadata: 元数据（JSON字符串或字典）

        Returns:
        conn = sqlite3.connect(self.db_path)

        try:
            # 处理JSON数据
                metadata = str(metadata)

            # 插入修复历史
                (problem_id, solution_id, result, applied_by, notes, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (problem_id, solution_id, result, applied_by, notes, metadata))
            # 更新解决方案的使用次数和成功率
            cursor.execute('''
                UPDATE solutions
                SET used_count = used_count + 1
            ''', (solution_id,))
            # 计算新的成功率
            cursor.execute('''
                SELECT COUNT(*) as total,
                FROM repair_history
                WHERE solution_id = ?
            row = cursor.fetchone()
            if row and row[0] > 0:
                success_rate = row[1] / row[0]
                    SET success_rate = ?
                    WHERE solution_id = ?
                ''', (success_rate, solution_id))

            conn.commit()
            print(f"Error recording repair: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
    def find_problems_by_symptoms(self, symptoms, category=None):

            symptoms: 症状文本或字典
            category: 分类（可选）

        Returns:
            list: 匹配的问题列表
        cursor = conn.cursor()

        try:
            # 将症状转换为字符串进行匹配
            if isinstance(symptoms, dict):
                symptoms_str = str(symptoms)
            else:
                symptoms_str = str(symptoms)

            query = '''
                SELECT * FROM problems
            '''
            params = [f"%{symptoms_str}%"]

            if category:
                params.append(category)
            query += " ORDER BY severity DESC, last_updated DESC"

            cursor.execute(query, params)

            problems = []
                problem = {
                    'problem_id': row[1],
                    'title': row[2],
                    'description': row[3],
                    'severity': row[5],
                    'category': row[6],
                    'last_updated': row[8],
                    'metadata': eval(row[9]) if row[9] else {}
                problems.append(problem)

            return problems
        except Exception as e:
            print(f"Error finding problems: {str(e)}")
            return []
        finally:
            conn.close()
    def get_solutions_for_problem(self, problem_id):
        """获取问题的所有解决方案

        Args:
            problem_id: 问题ID

            list: 解决方案列表
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT * FROM solutions
                WHERE problem_id = ?
                ORDER BY success_rate DESC, used_count DESC
            ''', (problem_id,))

            solutions = []
            for row in cursor.fetchall():
                solution = {
                    'id': row[0],
                    'problem_id': row[2],
                    'title': row[3],
                    'description': row[4],
                    'steps': eval(row[5]) if row[5] else [],
                    'success_rate': row[6],
                    'created_at': row[8],
                    'last_updated': row[9],
                    'created_by': row[10],
                    'metadata': eval(row[11]) if row[11] else {}
                }
                solutions.append(solution)

        except Exception as e:
            print(f"Error getting solutions: {str(e)}")
            return []
        finally:
            conn.close()

    def get_best_solution(self, problem_id):
        """获取最佳解决方案

        Args:
            problem_id: 问题ID

        Returns:
            dict: 最佳解决方案或None
        solutions = self.get_solutions_for_problem(problem_id)
        return solutions[0] if solutions else None

        """自动修复问题

        Args:
            symptoms: 症状
            category: 分类（可选）

        Returns:
            dict: 修复结果
        # 1. 根据症状查找问题
        problems = self.find_problems_by_symptoms(symptoms, category)
            return {
                'message': '未找到匹配的问题',
                'details': {
                    'symptoms': symptoms,
                    'category': category
                }
            }

        # 2. 获取最佳解决方案
        best_problem = problems[0]
        best_solution = self.get_best_solution(best_problem['problem_id'])
        if not best_solution:
            return {
                'success': False,
                'message': '未找到解决方案',
                'details': {
                    'problem_id': best_problem['problem_id'],
                    'problem_title': best_problem['title']
                }
            }

        # 3. 应用解决方案（这里是模拟，实际应用需要根据steps执行）
        print(f"[自动修复] 应用解决方案: {best_solution['title']} 到问题: {best_problem['title']}")
        print(f"[自动修复] 步骤: {best_solution['steps']}")
        # 模拟修复结果
        result = 'success' if best_solution['success_rate'] > 0.7 else 'failure'

        # 4. 记录修复历史
        self.record_repair(
            problem_id=best_problem['problem_id'],
            solution_id=best_solution['solution_id'],
            result=result,
            applied_by=applied_by,
            notes=f"自动修复 - 成功率: {best_solution['success_rate']:.2f}",
            metadata={
                'symptoms': symptoms,
                'category': category,
                'auto_repaired': True
            }
        )

        return {
            'details': {
                'problem': best_problem,
                'solution': best_solution,
                'result': result,
                'applied_by': applied_by,
                'applied_at': datetime.now().isoformat()
            }
        }

    def get_problem(self, problem_id):
        """根据ID获取问题

        Args:
            problem_id: 问题ID

        Returns:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

            cursor.execute('SELECT * FROM problems WHERE problem_id = ?', (problem_id,))
            if not row:
                return None

            return {
                'id': row[0],
                'problem_id': row[1],
                'title': row[2],
                'description': row[3],
                'symptoms': eval(row[4]) if row[4] else {},
                'severity': row[5],
                'category': row[6],
                'created_at': row[7],
                'last_updated': row[8],
                'metadata': eval(row[9]) if row[9] else {}
        except Exception as e:
            print(f"Error getting problem: {str(e)}")
            return None
        finally:
            conn.close()

        """根据ID获取解决方案

        Args:
            solution_id: 解决方案ID
        Returns:
            dict: 解决方案信息或None
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM solutions WHERE solution_id = ?', (solution_id,))
            row = cursor.fetchone()
                return None

            return {
                'id': row[0],
                'solution_id': row[1],
                'problem_id': row[2],
                'title': row[3],
                'description': row[4],
                'steps': eval(row[5]) if row[5] else [],
                'success_rate': row[6],
                'used_count': row[7],
                'created_at': row[8],
                'last_updated': row[9],
                'created_by': row[10],
                'metadata': eval(row[11]) if row[11] else {}
        except Exception as e:
            return None
            conn.close()

    def get_repair_history(self, problem_id=None, solution_id=None, limit=50):

        Args:
            problem_id: 问题ID（可选）

        Returns:
            list: 修复历史列表
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM repair_history WHERE 1=1"

            if problem_id:
                params.append(problem_id)

            if solution_id:
                query += " AND solution_id = ?"
                params.append(solution_id)

            query += " ORDER BY applied_at DESC LIMIT ?"
            params.append(limit)
            cursor.execute(query, params)

            history = []
            for row in cursor.fetchall():
                history.append({
                    'id': row[0],
                    'applied_by': row[5],
                    'notes': row[6],
                    'metadata': eval(row[7]) if row[7] else {}
                })

        except Exception as e:
            print(f"Error getting repair history: {str(e)}")
            return []
        finally:
            conn.close()

    def export_knowledge_base(self):
        """导出知识库
        Returns:
            dict: 知识库数据
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # 获取所有问题
            cursor.execute('SELECT * FROM problems')
            problems = []
            for row in cursor.fetchall():
                problems.append({
                    'problem_id': row[1],
                    'title': row[2],
                    'description': row[3],
                    'symptoms': eval(row[4]) if row[4] else {},
                    'severity': row[5],
                    'created_at': row[7],
                    'last_updated': row[8],
                    'metadata': eval(row[9]) if row[9] else {}
                })

            cursor.execute('SELECT * FROM solutions')
            for row in cursor.fetchall():
                    'problem_id': row[2],
                    'title': row[3],
                    'description': row[4],
                    'success_rate': row[6],
                    'used_count': row[7],
                    'created_at': row[8],
                    'last_updated': row[9],
                    'created_by': row[10],
                })

            return {
                'export_time': datetime.now().isoformat(),
                'problems': problems,
                'solutions': solutions,
                'version': '1.0.0'
            }
        except Exception as e:
            print(f"Error exporting knowledge base: {str(e)}")
            return {
                'export_time': datetime.now().isoformat(),
                'problems': [],
                'solutions': [],
                'version': '1.0.0'
            }
        finally:
            conn.close()

# 单例模式 - 全局AI大脑实例
global_ai_brain = None

def get_ai_brain():
    """获取全局AI大脑实例

    Returns:
        AIBrain: AI大脑实例
    global global_ai_brain
    if global_ai_brain is None:
        global_ai_brain = AIBrain()
    return global_ai_brain

# 测试代码
if __name__ == '__main__':
    ai_brain = AIBrain()

    # 添加测试问题
    problem_id = ai_brain.add_problem(
        description='当访问/login路由时，返回的是文本而不是HTML模板',
        symptoms='返回内容为纯文本，不是HTML页面',
        severity='high',
        category='web',
        metadata={'endpoint': '/auth/login'}

    # 添加测试解决方案
    solution_id = ai_brain.add_solution(
        problem_id=problem_id,
        title='修复登录路由返回模板',
        description='将登录路由的返回值从文本改为render_template调用',
        steps=[
            '找到login路由函数',
            '将return "Login Page"改为return render_template(\'login.html\')',
            '保存并测试'
        ],
        created_by='ai_brain',
        metadata={'file': 'simple_flask_start.py'}
    )

    print(f"添加的问题ID: {problem_id}")

    # 测试自动修复
    repair_result = ai_brain.auto_repair(
        symptoms='返回内容为纯文本，不是HTML页面',
        category='web',
        applied_by='test'
    )

    print(f"\n自动修复结果:")
    print(str(repair_result, indent=2))

    problems = ai_brain.find_problems_by_symptoms('登录页面')
    print(f"\n查询到的问题:")
    for problem in problems:
        print(f"  - {problem['title']} (ID: {problem['problem_id']})")
        solutions = ai_brain.get_solutions_for_problem(problem['problem_id'])
        for solution in solutions:
            print(f"    * 解决方案: {solution['title']} (成功率: {solution['success_rate']:.2f})")
