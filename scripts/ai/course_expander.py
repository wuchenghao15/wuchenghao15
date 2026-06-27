#!/usr/bin/env python3
"""
MTSCOS AI 教育管理系统 - 自动拓展系统
自动生成和拓展考试课程和练习题库
"""

import json
import random
from datetime import datetime
import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class CourseExpander:
    """课程和练习自动拓展器"""
    
    def __init__(self, db_path='final_courses.db'):
        self.db_path = db_path
        self.course_data = self._load_course_templates()
        self.exercise_data = self._load_exercise_templates()
        self._init_database()
    
    def _load_course_templates(self):
        """加载课程模板数据"""
        return {
            "ai": {
                "name": "AI与机器学习",
                "icon": "🤖",
                "exams": [
                    {"name": "深度学习工程师认证", "duration": 120, "questions": 35, "score": 100, 
                     "desc": "深度学习、神经网络架构、优化算法和应用开发综合测试。"},
                    {"name": "自然语言处理工程师", "duration": 90, "questions": 30, "score": 100,
                     "desc": "NLP技术、文本处理、语言模型和对话系统应用测试。"},
                    {"name": "计算机视觉专家认证", "duration": 100, "questions": 32, "score": 100,
                     "desc": "图像处理、计算机视觉算法和深度学习应用测试。"},
                    {"name": "强化学习工程师", "duration": 85, "questions": 28, "score": 100,
                     "desc": "强化学习算法、环境建模和智能体设计能力测试。"},
                    {"name": "机器学习模型部署", "duration": 75, "questions": 25, "score": 100,
                     "desc": "ML模型部署、MLOps和生产环境应用测试。"}
                ]
            },
            "security": {
                "name": "数据安全",
                "icon": "🔒",
                "exams": [
                    {"name": "网络安全专家认证", "duration": 95, "questions": 30, "score": 100,
                     "desc": "网络攻防、漏洞分析和安全防护综合测试。"},
                    {"name": "云安全架构师", "duration": 80, "questions": 28, "score": 100,
                     "desc": "云平台安全、身份认证和数据保护测试。"},
                    {"name": "移动应用安全", "duration": 70, "questions": 25, "score": 100,
                     "desc": "移动应用安全、渗透测试和安全编码测试。"},
                    {"name": "区块链安全专家", "duration": 85, "questions": 28, "score": 100,
                     "desc": "区块链技术、智能合约安全和加密货币应用测试。"}
                ]
            },
            "math": {
                "name": "数学与统计",
                "icon": "📊",
                "exams": [
                    {"name": "高等数学综合测试", "duration": 90, "questions": 30, "score": 100,
                     "desc": "微积分、线性代数和空间几何综合能力测试。"},
                    {"name": "概率统计高级应用", "duration": 80, "questions": 26, "score": 100,
                     "desc": "概率论、统计学和数据分析应用测试。"},
                    {"name": "离散数学与逻辑", "duration": 75, "questions": 25, "score": 100,
                     "desc": "图论、集合论、数理逻辑和组合数学测试。"},
                    {"name": "数值计算与优化", "duration": 70, "questions": 22, "score": 100,
                     "desc": "数值方法、优化算法和科学计算应用测试。"}
                ]
            },
            "programming": {
                "name": "编程与算法",
                "icon": "💻",
                "exams": [
                    {"name": "Python高级开发", "duration": 100, "questions": 35, "score": 100,
                     "desc": "Python语法、框架、数据结构和工程实践测试。"},
                    {"name": "Java企业级开发", "duration": 110, "questions": 38, "score": 100,
                     "desc": "Java语言、Spring框架和企业应用开发测试。"},
                    {"name": "前端全栈开发", "duration": 95, "questions": 32, "score": 100,
                     "desc": "HTML/CSS/JavaScript、React/Vue和全栈开发测试。"},
                    {"name": "系统设计与架构", "duration": 120, "questions": 25, "score": 100,
                     "desc": "系统架构设计、高可用和可扩展性设计测试。"},
                    {"name": "微服务架构师", "duration": 90, "questions": 28, "score": 100,
                     "desc": "微服务设计、容器化、服务网格和DevOps测试。"}
                ]
            },
            "english": {
                "name": "专业英语",
                "icon": "🌐",
                "exams": [
                    {"name": "IT技术英语高级", "duration": 65, "questions": 40, "score": 100,
                     "desc": "IT专业术语、技术文档阅读和英文沟通能力测试。"},
                    {"name": "商务英语BEC高级", "duration": 75, "questions": 45, "score": 100,
                     "desc": "商务沟通、邮件写作和会议英语能力测试。"},
                    {"name": "学术英语写作", "duration": 80, "questions": 35, "score": 100,
                     "desc": "论文写作、文献引用和学术表达能力测试。"},
                    {"name": "技术文档翻译", "duration": 70, "questions": 30, "score": 100,
                     "desc": "中英双语技术翻译和专业术语准确使用测试。"}
                ]
            },
            "japanese": {
                "name": "日语学习",
                "icon": "🗾",
                "exams": [
                    {"name": "日语能力等级考试（JLPT N2）", "duration": 90, "questions": 35, "score": 100,
                     "desc": "日本语能力测试N2级别，包括词汇、语法、阅读和听力。"},
                    {"name": "日语能力等级考试（JLPT N1）", "duration": 110, "questions": 40, "score": 100,
                     "desc": "日本语能力测试最高级别，高级日语综合能力测试。"},
                    {"name": "日语能力等级考试（JLPT N3）", "duration": 75, "questions": 30, "score": 100,
                     "desc": "日本语能力测试N3级别，中级日语能力认证。"},
                    {"name": "日语能力等级考试（JLPT N4）", "duration": 65, "questions": 25, "score": 100,
                     "desc": "日本语能力测试N4级别，初级日语能力认证，适合日语初学者。"},
                    {"name": "日语能力等级考试（JLPT N5）", "duration": 55, "questions": 20, "score": 100,
                     "desc": "日本语能力测试N5级别，入门级日语能力认证，零基础友好。"},
                    {"name": "日语会话能力测试", "duration": 60, "questions": 15, "score": 100,
                     "desc": "日常日语会话能力评估，包括听力理解和口语表达。"},
                    {"name": "日本商务日语JTEST", "duration": 90, "questions": 30, "score": 100,
                     "desc": "商务日语应用、职场沟通和日企文化测试。"},
                    {"name": "日本留学考试EJU日语", "duration": 100, "questions": 38, "score": 100,
                     "desc": "日本留学考试日语科目，包括记述、读解和听解。"}
                ]
            },
            "business": {
                "name": "商业与管理",
                "icon": "🏢",
                "exams": [
                    {"name": "项目管理PMP认证", "duration": 120, "questions": 40, "score": 100,
                     "desc": "项目管理知识体系、流程和最佳实践测试。"},
                    {"name": "产品经理综合能力", "duration": 100, "questions": 35, "score": 100,
                     "desc": "产品设计、用户研究、数据分析和项目管理测试。"},
                    {"name": "数据分析师认证", "duration": 90, "questions": 32, "score": 100,
                     "desc": "数据分析、可视化、统计建模和业务洞察测试。"},
                    {"name": "数字营销策略师", "duration": 85, "questions": 30, "score": 100,
                     "desc": "数字营销、社交媒体、SEO/SEM和数据分析测试。"}
                ]
            },
            "design": {
                "name": "设计与创意",
                "icon": "🎨",
                "exams": [
                    {"name": "UI/UX设计师认证", "duration": 95, "questions": 32, "score": 100,
                     "desc": "用户界面设计、用户体验研究和设计系统测试。"},
                    {"name": "平面设计师综合能力", "duration": 85, "questions": 28, "score": 100,
                     "desc": "设计原理、排版、色彩和品牌视觉设计测试。"},
                    {"name": "交互设计高级应用", "duration": 80, "questions": 26, "score": 100,
                     "desc": "交互设计、原型制作和用户测试方法测试。"}
                ]
            }
        }
    
    def _load_exercise_templates(self):
        """加载练习题模板数据"""
        return {
            "ai": {
                "exercises": [
                    {"name": "机器学习算法实践", "duration": 60, "questions": 20,
                     "desc": "回归、分类、聚类等经典机器学习算法练习。"},
                    {"name": "深度学习模型搭建", "duration": 90, "questions": 15,
                     "desc": "神经网络、CNN、RNN等深度学习模型构建练习。"},
                    {"name": "Python数据科学练习", "duration": 50, "questions": 25,
                     "desc": "NumPy、Pandas、Matplotlib数据处理和可视化练习。"},
                    {"name": "AI历年真题解析", "duration": 90, "questions": 20,
                     "desc": "AI领域历年考试真题详细解析与练习。"},
                    {"name": "AI压轴难题精选", "duration": 120, "questions": 10,
                     "desc": "AI领域高难度题目精选与深度练习。"},
                    {"name": "深度学习专项练习", "duration": 80, "questions": 12,
                     "desc": "深度学习专项技能提升和实战演练。"}
                ]
            },
            "security": {
                "exercises": [
                    {"name": "密码学基础练习", "duration": 45, "questions": 15,
                     "desc": "对称加密、非对称加密、哈希算法基础练习。"},
                    {"name": "Web安全实战", "duration": 70, "questions": 18,
                     "desc": "XSS、CSRF、SQL注入等Web安全攻击与防护练习。"},
                    {"name": "数据安全历年真题", "duration": 80, "questions": 25,
                     "desc": "数据安全领域历年考试真题解析。"},
                    {"name": "数据安全压轴难题", "duration": 100, "questions": 8,
                     "desc": "数据安全高难度综合挑战题目。"}
                ]
            },
            "math": {
                "exercises": [
                    {"name": "统计分析历年真题", "duration": 70, "questions": 22,
                     "desc": "统计分析领域历年真题详细解析。"}
                ]
            },
            "programming": {
                "exercises": [
                    {"name": "高级算法设计", "duration": 40, "questions": 6,
                     "desc": "动态规划、贪心算法、图算法高级练习。"},
                    {"name": "算法历年真题", "duration": 120, "questions": 15,
                     "desc": "算法竞赛和面试历年真题解析。"},
                    {"name": "算法压轴难题精选", "duration": 150, "questions": 6,
                     "desc": "算法领域顶级难题挑战与详解。"}
                ]
            },
            "english": {
                "exercises": [
                    {"name": "专业英语历年真题", "duration": 60, "questions": 30,
                     "desc": "专业英语领域历年考试真题解析。"}
                ]
            },
            "japanese": {
                "exercises": [
                    {"name": "日语词汇练习", "duration": 30, "questions": 20,
                     "desc": "日语基础到高级词汇系统化练习。"},
                    {"name": "日语语法练习", "duration": 25, "questions": 15,
                     "desc": "日语语法点专项训练和应用练习。"},
                    {"name": "日语阅读练习", "duration": 40, "questions": 8,
                     "desc": "日语阅读理解能力提升专项训练。"},
                    {"name": "日语听力练习", "duration": 35, "questions": 10,
                     "desc": "日语听力理解和反应能力训练。"},
                    {"name": "日语汉字练习", "duration": 20, "questions": 25,
                     "desc": "日语汉字读音、写法和用法练习。"},
                    {"name": "日语会话练习", "duration": 45, "questions": 12,
                     "desc": "日语日常会话和场景对话练习。"},
                    {"name": "JLPT历年真题(N1-N5)", "duration": 120, "questions": 50,
                     "desc": "JLPT各级别历年真题完整练习。"},
                    {"name": "日语能力压轴题", "duration": 90, "questions": 15,
                     "desc": "日语能力考试高难度综合题目。"}
                ]
            },
            "business": {
                "exercises": [
                    {"name": "商业分析案例练习", "duration": 75, "questions": 12,
                     "desc": "真实商业场景分析和决策练习。"},
                    {"name": "财务报表解读", "duration": 60, "questions": 18,
                     "desc": "资产负债表、利润表、现金流量表解读练习。"}
                ]
            },
            "design": {
                "exercises": [
                    {"name": "设计系统构建", "duration": 90, "questions": 10,
                     "desc": "设计Token、组件库和设计规范构建练习。"},
                    {"name": "用户研究方法", "duration": 60, "questions": 15,
                     "desc": "用户访谈、可用性测试和数据分析练习。"}
                ]
            }
        }
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        # 创建课程表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT UNIQUE NOT NULL,
                course_name TEXT NOT NULL,
                course_icon TEXT,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建考试表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id TEXT UNIQUE NOT NULL,
                course_id TEXT NOT NULL,
                exam_name TEXT NOT NULL,
                description TEXT,
                duration INTEGER DEFAULT 60,
                question_count INTEGER DEFAULT 20,
                total_score INTEGER DEFAULT 100,
                difficulty TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'available',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建练习题表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_id TEXT UNIQUE NOT NULL,
                course_id TEXT NOT NULL,
                exercise_name TEXT NOT NULL,
                description TEXT,
                duration INTEGER DEFAULT 30,
                question_count INTEGER DEFAULT 15,
                exercise_type TEXT DEFAULT 'practice',
                difficulty TEXT DEFAULT 'medium',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建题目表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT UNIQUE NOT NULL,
                parent_id TEXT,
                parent_type TEXT,
                question_text TEXT NOT NULL,
                question_type TEXT DEFAULT 'multiple_choice',
                options TEXT,
                correct_answer TEXT,
                explanation TEXT,
                difficulty TEXT DEFAULT 'medium',
                knowledge_point TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def expand_all_courses(self):
        """拓展所有课程"""
        print("=" * 80)
        print("开始拓展所有课程和练习...")
        print("=" * 80)
        
        total_exams = 0
        total_exercises = 0
        
        for course_id, course_info in self.course_data.items():
            print(f"\n📚 处理课程: {course_info['name']}")
            self._create_course(course_id, course_info)
            
            exams_added = self._expand_course_exams(course_id, course_info)
            exercises_added = self._expand_course_exercises(course_id, course_info)
            
            total_exams += exams_added
            total_exercises += exercises_added
            
            print(f"   ✅ 新增 {exams_added} 个考试, {exercises_added} 个练习")
        
        print("\n" + "=" * 80)
        print(f"拓展完成! 总计: {total_exams} 个考试, {total_exercises} 个练习")
        print("=" * 80)
        
        return {
            "total_exams": total_exams,
            "total_exercises": total_exercises
        }
    
    def _create_course(self, course_id, course_info):
        """创建课程记录"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        try:
            # 检查是否存在
            cursor.execute('SELECT id FROM courses WHERE course_id = ?', (course_id,))
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute('''
                    UPDATE courses 
                    SET course_name = ?, course_icon = ?, description = ?
                    WHERE course_id = ?
                ''', (
                    course_info['name'],
                    course_info['icon'],
                    f"{course_info['name']}综合学习课程",
                    course_id
                ))
            else:
                cursor.execute('''
                    INSERT INTO courses 
                    (course_id, course_name, course_icon, description)
                    VALUES (?, ?, ?, ?)
                ''', (
                    course_id,
                    course_info['name'],
                    course_info['icon'],
                    f"{course_info['name']}综合学习课程"
                ))
            conn.commit()
        except Exception as e:
            print(f"   ⚠️ 创建课程失败: {e}")
        
        cursor.close()
        conn.close()
    
    def _expand_course_exams(self, course_id, course_info):
        """拓展课程考试"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        added_count = 0
        
        for exam_info in course_info['exams']:
            exam_id = f"{course_id}_{exam_info['name'].replace(' ', '_').replace('（', '').replace('）', '').replace('/', '_')}"
            
            try:
                cursor.execute('SELECT id FROM exams WHERE exam_id = ?', (exam_id,))
                exists = cursor.fetchone()
                
                if exists:
                    cursor.execute('''
                        UPDATE exams 
                        SET course_id = ?, exam_name = ?, description = ?, 
                            duration = ?, question_count = ?, total_score = ?, status = ?
                        WHERE exam_id = ?
                    ''', (
                        course_id,
                        exam_info['name'],
                        exam_info['desc'],
                        exam_info['duration'],
                        exam_info['questions'],
                        exam_info['score'],
                        'available',
                        exam_id
                    ))
                else:
                    cursor.execute('''
                        INSERT INTO exams 
                        (exam_id, course_id, exam_name, description, duration, 
                         question_count, total_score, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        exam_id,
                        course_id,
                        exam_info['name'],
                        exam_info['desc'],
                        exam_info['duration'],
                        exam_info['questions'],
                        exam_info['score'],
                        'available'
                    ))
                added_count += 1
                
                # 自动生成一些题目
                self._generate_questions(exam_id, 'exam', exam_info['questions'], course_id)
                
            except Exception as e:
                print(f"   ⚠️ 添加考试失败 {exam_info['name']}: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        return added_count
    
    def _expand_course_exercises(self, course_id, course_info):
        """拓展课程练习"""
        if course_id not in self.exercise_data:
            return 0
        
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        added_count = 0
        exercise_info_list = self.exercise_data[course_id]['exercises']
        
        for exercise_info in exercise_info_list:
            exercise_id = f"exercise_{course_id}_{exercise_info['name'].replace(' ', '_').replace('（', '').replace('）', '').replace('/', '_')}"
            
            try:
                cursor.execute('SELECT id FROM exercises WHERE exercise_id = ?', (exercise_id,))
                exists = cursor.fetchone()
                
                if exists:
                    cursor.execute('''
                        UPDATE exercises 
                        SET course_id = ?, exercise_name = ?, description = ?, 
                            duration = ?, question_count = ?, exercise_type = ?
                        WHERE exercise_id = ?
                    ''', (
                        course_id,
                        exercise_info['name'],
                        exercise_info['desc'],
                        exercise_info['duration'],
                        exercise_info['questions'],
                        'practice',
                        exercise_id
                    ))
                else:
                    cursor.execute('''
                        INSERT INTO exercises 
                        (exercise_id, course_id, exercise_name, description, 
                         duration, question_count, exercise_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        exercise_id,
                        course_id,
                        exercise_info['name'],
                        exercise_info['desc'],
                        exercise_info['duration'],
                        exercise_info['questions'],
                        'practice'
                    ))
                added_count += 1
                
                # 自动生成一些题目
                self._generate_questions(exercise_id, 'exercise', exercise_info['questions'], course_id)
                
            except Exception as e:
                print(f"   ⚠️ 添加练习失败 {exercise_info['name']}: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        return added_count
    
    def _generate_questions(self, parent_id, parent_type, count, course_id):
        """自动生成题目"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        # 检查是否已有题目
        cursor.execute('SELECT COUNT(*) FROM questions WHERE parent_id = ?', (parent_id,))
        if cursor.fetchone()[0] > 0:
            cursor.close()
            conn.close()
            return
        
        # 题目模板
        question_templates = {
            "ai": [
                "什么是机器学习中的{}？",
                "请解释{}算法的工作原理？",
                "{}模型的主要应用场景是什么？",
                "如何解决{}问题？"
            ],
            "security": [
                "什么是{}攻击？如何防护？",
                "{}加密算法的工作原理？",
                "安全最佳实践中{}的重要性？",
                "如何检测和响应{}事件？"
            ],
            "math": [
                "请计算{}？",
                "证明{}定理？",
                "{}在实际中的应用？",
                "求解{}方程？"
            ],
            "programming": [
                "如何用代码实现{}？",
                "{}算法的时间复杂度？",
                "解释{}设计模式？",
                "调试{}问题的方法？"
            ],
            "english": [
                "{}的正确英文表达是？",
                "选择最合适的词填入{}？",
                "{}在商务场景中的用法？",
                "翻译{}？"
            ],
            "japanese": [
                "{}的正确日语读法是？",
                "选择正确的{}汉字？",
                "{}的语法用法是？",
                "{}的同义词是？"
            ],
            "business": [
                "{}在项目管理中的作用？",
                "如何制定{}策略？",
                "{}的商业价值是？",
                "分析{}案例？"
            ],
            "design": [
                "{}的设计原则是什么？",
                "如何实现{}用户体验？",
                "{}设计的最佳实践？",
                "评价{}设计作品？"
            ]
        }
        
        templates = question_templates.get(course_id, question_templates["programming"])
        knowledge_points = ["基础概念", "高级应用", "实战技巧", "原理理解"]
        
        for i in range(count):
            question_id = f"{parent_id}_q{i+1}"
            template = random.choice(templates)
            kp = random.choice(knowledge_points)
            
            question_text = template.format(f"概念{i+1}")
            
            options = json.dumps([
                "选项A",
                "选项B", 
                "选项C",
                "选项D"
            ])
            
            cursor.execute('SELECT id FROM questions WHERE question_id = ?', (question_id,))
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute('''
                    INSERT INTO questions 
                    (question_id, parent_id, parent_type, question_text, 
                     question_type, options, correct_answer, knowledge_point)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    question_id,
                    parent_id,
                    parent_type,
                    question_text,
                    'multiple_choice',
                    options,
                    "选项A",
                    kp
                ))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_course_list(self):
        """获取课程列表"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM courses ORDER BY created_at DESC')
        courses = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return courses
    
    def get_exam_list(self, course_id=None):
        """获取考试列表"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        if course_id:
            cursor.execute('SELECT * FROM exams WHERE course_id = ? ORDER BY created_at DESC', (course_id,))
        else:
            cursor.execute('SELECT * FROM exams ORDER BY created_at DESC')
        
        exams = cursor.fetchall()
        cursor.close()
        conn.close()
        return exams
    
    def get_exercise_list(self, course_id=None):
        """获取练习列表"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        if course_id:
            cursor.execute('SELECT * FROM exercises WHERE course_id = ? ORDER BY created_at DESC', (course_id,))
        else:
            cursor.execute('SELECT * FROM exercises ORDER BY created_at DESC')
        
        exercises = cursor.fetchall()
        cursor.close()
        conn.close()
        return exercises


if __name__ == '__main__':
    expander = CourseExpander()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'expand':
            expander.expand_all_courses()
        elif command == 'list':
            print("\n📚 课程列表:")
            courses = expander.get_course_list()
            for course in courses:
                print(f"  {course[2]} ({course[1]})")
            
            print("\n📝 考试列表:")
            exams = expander.get_exam_list()
            for exam in exams:
                print(f"  {exam[3]} - {exam[5]}分钟")
            
            print("\n✏️ 练习列表:")
            exercises = expander.get_exercise_list()
            for ex in exercises:
                print(f"  {ex[3]} - {ex[5]}分钟")
        else:
            print("用法: python course_expander.py [expand|list]")
    else:
        print("开始自动拓展课程和练习...")
        result = expander.expand_all_courses()
        print(f"\n完成! 新增 {result['total_exams']} 个考试, {result['total_exercises']} 个练习")
