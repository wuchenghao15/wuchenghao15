import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import json
import random
from datetime import datetime, timedelta

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

class EducationAlignment:
    """教育体系适配管理器"""
    
    def __init__(self):
        self.education_levels = ['小学', '初中', '高中', '大学', '竞赛']
        self.difficulty_levels = {
            '小学': ['入门', '基础', '提高'],
            '初中': ['基础', '提高', '拓展'],
            '高中': ['基础', '提高', '拓展', '竞赛'],
            '大学': ['基础', '提高', '进阶', '研究'],
            '竞赛': ['省级', '国家级', '国际级']
        }
        
        self.subjects = {
            '数学': ['代数', '几何', '概率统计', '微积分', '线性代数', '数论'],
            '语文': ['阅读理解', '写作', '文言文', '诗词鉴赏', '语法修辞'],
            '英语': ['词汇', '语法', '阅读理解', '写作', '听力', '口语'],
            '物理': ['力学', '电磁学', '光学', '热学', '量子物理'],
            '化学': ['无机化学', '有机化学', '分析化学', '物理化学'],
            '编程': ['Python', 'C++', '数据结构', '算法', '数据库'],
            '计算机': ['计算机基础', '网络技术', '操作系统', '人工智能']
        }
        
        self.exam_types = {
            'standard': '标准考试',
            'quiz': '随堂测验',
            'homework': '作业练习',
            'midterm': '期中考试',
            'final': '期末考试',
            'competition': '竞赛选拔',
            'mock': '模拟考试'
        }
        
        self.competition_rules = {
            '省级': {'time_limit': 120, 'question_count': 20, 'passing_score': 60},
            '国家级': {'time_limit': 150, 'question_count': 25, 'passing_score': 70},
            '国际级': {'time_limit': 180, 'question_count': 30, 'passing_score': 75}
        }

    def create_education_structure(self):
        """创建教育体系结构表"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # 创建学科表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建章节表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    education_level TEXT NOT NULL,
                    chapter_order INTEGER DEFAULT 0,
                    description TEXT,
                    FOREIGN KEY (subject_id) REFERENCES subjects(id)
                )
            ''')
            
            # 创建知识点表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    difficulty TEXT DEFAULT 'medium',
                    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
                )
            ''')
            
            # 创建题目与知识点关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS question_knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    knowledge_point_id INTEGER NOT NULL,
                    FOREIGN KEY (question_id) REFERENCES questions(id),
                    FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_points(id)
                )
            ''')
            
            conn.commit()
            print("✅ 创建教育体系结构表完成")
    
    def init_education_data(self):
        """初始化教育体系数据"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # 检查是否已有数据
            cursor.execute("SELECT COUNT(*) FROM subjects")
            if cursor.fetchone()[0] > 0:
                print("ℹ️ 教育体系数据已存在,跳过初始化")
                return
            
            # 插入学科
            for subject_name in self.subjects.keys():
                cursor.execute('INSERT INTO subjects (name) VALUES (?)', (subject_name,))
            
            conn.commit()
            
            # 获取学科ID
            cursor.execute("SELECT id, name FROM subjects")
            subjects = {name: id for id, name in cursor.fetchall()}
            
            # 插入章节
            for subject_name, chapters in self.subjects.items():
                subject_id = subjects[subject_name]
                for idx, chapter_name in enumerate(chapters, 1):
                    for level in self.education_levels:
                        cursor.execute('''
                            INSERT INTO chapters (subject_id, name, education_level, chapter_order)
                            VALUES (?, ?, ?, ?)
                        ''', (subject_id, chapter_name, level, idx))
            
            conn.commit()
            print("✅ 教育体系数据初始化完成")
    
    def align_questions_to_education(self):
        """将题目与教育体系对齐"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # 获取所有题目
            cursor.execute("SELECT id, category, difficulty FROM questions")
            questions = cursor.fetchall()
            
            # 获取学科和章节映射
            cursor.execute("SELECT id, name FROM subjects")
            subjects = {name.lower(): id for id, name in cursor.fetchall()}
            
            cursor.execute("SELECT id, subject_id, name, education_level FROM chapters")
            chapters = {}
            for ch_id, sub_id, ch_name, level in cursor.fetchall():
                key = (sub_id, ch_name.lower(), level)
                chapters[key] = ch_id
            
            aligned_count = 0
            for q_id, category, difficulty in questions:
                # 映射类别到学科
                category_map = {
                    'programming': '编程',
                    'math': '数学',
                    'language': '英语',
                    'computer_science': '计算机',
                    'ai': '计算机'
                }
                
                subject_name = category_map.get(category, '数学')
                subject_id = subjects.get(subject_name.lower())
                
                if subject_id:
                    # 获取章节ID(简化处理,根据难度分配)
                    level = self._get_education_level(difficulty)
                    cursor.execute('''
                        SELECT id FROM chapters 
                        WHERE subject_id = ? AND education_level = ? 
                        ORDER BY RANDOM() LIMIT 1
                    ''', (subject_id, level))
                    chapter = cursor.fetchone()
                    
                    if chapter:
                        chapter_id = chapter[0]
                        
                        # 获取知识点
                        cursor.execute('''
                            SELECT id FROM knowledge_points 
                            WHERE chapter_id = ? ORDER BY RANDOM() LIMIT 1
                        ''', (chapter_id,))
                        kp = cursor.fetchone()
                        
                        if kp:
                            kp_id = kp[0]
                        else:
                            # 创建新知识点
                            cursor.execute('''
                                INSERT INTO knowledge_points (chapter_id, name, difficulty)
                                VALUES (?, ?, ?)
                            ''', (chapter_id, f'{category}基础', difficulty))
                            kp_id = cursor.lastrowid
                        
                        # 关联题目与知识点
                        cursor.execute('''
                            INSERT OR IGNORE INTO question_knowledge 
                            (question_id, knowledge_point_id) VALUES (?, ?)
                        ''', (q_id, kp_id))
                        aligned_count += 1
            
            conn.commit()
            print(f"✅ 已对齐 {aligned_count} 道题目到教育体系")
    
    def _get_education_level(self, difficulty):
        """根据难度获取教育级别"""
        level_map = {
            'easy': '初中',
            'medium': '高中',
            'hard': '大学',
            'expert': '竞赛'
        }
        return level_map.get(difficulty, '高中')
    
    def generate_aligned_questions(self, count=5):
        """生成符合教育体系的题目"""
        questions = []
        
        for _ in range(count):
            subject = random.choice(list(self.subjects.keys()))
            chapter = random.choice(self.subjects[subject])
            level = random.choice(self.education_levels)
            difficulty = random.choice(self.difficulty_levels.get(level, ['基础', '提高', '拓展']))
            
            question = self._generate_subject_question(subject, chapter, level, difficulty)
            questions.append(question)
        
        return questions
    
    def _generate_subject_question(self, subject, chapter, level, difficulty):
        """生成特定学科的题目"""
        question_templates = {
            '数学': {
                '代数': [
                    {
                        "question_text": f"{level}数学 - 代数: 解方程 2x + 5 = 15,x = ?",
                        "options": ["5", "10", "3", "7"],
                        "correct_answer": "5",
                        "explanation": "2x + 5 = 15 → 2x = 10 → x = 5"
                    },
                    {
                        "question_text": f"{level}数学 - 代数: 化简 (a+b)^2 = ?",
                        "options": ["a²+2ab+b²", "a²+b²", "a²-2ab+b²", "2ab"],
                        "correct_answer": "a²+2ab+b²",
                        "explanation": "(a+b)² = a² + 2ab + b²"
                    }
                ],
                '几何': [
                    {
                        "question_text": f"{level}数学 - 几何: 三角形内角和等于多少度?",
                        "options": ["180°", "90°", "360°", "270°"],
                        "correct_answer": "180°",
                        "explanation": "三角形内角和恒等于180度"
                    },
                    {
                        "question_text": f"{level}数学 - 几何: 圆的面积公式是?",
                        "options": ["πr²", "2πr", "πd", "2πd"],
                        "correct_answer": "πr²",
                        "explanation": "圆的面积 = π × 半径²"
                    }
                ],
                '概率统计': [
                    {
                        "question_text": f"{level}数学 - 概率: 抛一枚硬币正面朝上的概率是?",
                        "options": ["0.5", "0.25", "0.75", "1"],
                        "correct_answer": "0.5",
                        "explanation": "硬币只有正反两面,正面概率为1/2=0.5"
                    }
                ]
            },
            '英语': {
                '词汇': [
                    {
                        "question_text": f"{level}英语 - 词汇: 'Beautiful' 的反义词是?",
                        "options": ["Ugly", "Pretty", "Lovely", "Handsome"],
                        "correct_answer": "Ugly",
                        "explanation": "Beautiful意为美丽的,其反义词是Ugly(丑陋的)"
                    }
                ],
                '语法': [
                    {
                        "question_text": f"{level}英语 - 语法: She ___ to school every day.",
                        "options": ["goes", "go", "going", "went"],
                        "correct_answer": "goes",
                        "explanation": "主语是第三人称单数,动词需加s"
                    }
                ]
            },
            '编程': {
                'Python': [
                    {
                        "question_text": f"{level}编程 - Python: 打印'Hello World'的正确代码是?",
                        "options": ["print('Hello World')", "echo 'Hello World'", "printf('Hello World')", "console.log('Hello World')"],
                        "correct_answer": "print('Hello World')",
                        "explanation": "Python使用print()函数输出内容"
                    },
                    {
                        "question_text": f"{level}编程 - Python: 以下哪个是Python的注释符号?",
                        "options": ["#", "//", "/* */", "--"],
                        "correct_answer": "#",
                        "explanation": "Python使用#进行单行注释"
                    }
                ],
                '数据结构': [
                    {
                        "question_text": f"{level}编程 - 数据结构: 栈的特点是?",
                        "options": ["先进后出", "先进先出", "随机访问", "双向访问"],
                        "correct_answer": "先进后出",
                        "explanation": "栈(Stack)是后进先出(LIFO)的数据结构"
                    }
                ],
                '算法': [
                    {
                        "question_text": f"{level}编程 - 算法: 快速排序的平均时间复杂度是?",
                        "options": ["O(n log n)", "O(n²)", "O(n)", "O(log n)"],
                        "correct_answer": "O(n log n)",
                        "explanation": "快速排序平均时间复杂度为O(n log n)"
                    }
                ]
            },
            '计算机': {
                '计算机基础': [
                    {
                        "question_text": f"{level}计算机 - 基础: CPU的全称是?",
                        "options": ["Central Processing Unit", "Computer Processing Unit", "Central Program Unit", "Computer Program Unit"],
                        "correct_answer": "Central Processing Unit",
                        "explanation": "CPU全称Central Processing Unit,中央处理器"
                    }
                ],
                '人工智能': [
                    {
                        "question_text": f"{level}计算机 - AI: 机器学习中用于分类的算法是?",
                        "options": ["决策树", "K-means", "PCA", "梯度下降"],
                        "correct_answer": "决策树",
                        "explanation": "决策树是常用的分类算法"
                    }
                ]
            },
            '物理': {
                '力学': [
                    {
                        "question_text": f"{level}物理 - 力学: 牛顿第一定律又称为?",
                        "options": ["惯性定律", "加速度定律", "作用力定律", "万有引力定律"],
                        "correct_answer": "惯性定律",
                        "explanation": "牛顿第一定律也称为惯性定律"
                    }
                ],
                '电磁学': [
                    {
                        "question_text": f"{level}物理 - 电磁学: 电流的单位是?",
                        "options": ["安培", "伏特", "欧姆", "瓦特"],
                        "correct_answer": "安培",
                        "explanation": "电流单位是安培(A)"
                    }
                ]
            },
            '化学': {
                '无机化学': [
                    {
                        "question_text": f"{level}化学 - 无机: 水的化学式是?",
                        "options": ["H₂O", "CO₂", "NaCl", "H₂SO₄"],
                        "correct_answer": "H₂O",
                        "explanation": "水的化学式是H₂O"
                    }
                ]
            },
            '语文': {
                '阅读理解': [
                    {
                        "question_text": f"{level}语文 - 阅读: '床前明月光'的作者是?",
                        "options": ["李白", "杜甫", "白居易", "苏轼"],
                        "correct_answer": "李白",
                        "explanation": "\"床前明月光\"出自李白的《静夜思》"
                    }
                ],
                '文言文': [
                    {
                        "question_text": f"{level}语文 - 文言: '之'在文言文中的含义不包括?",
                        "options": ["动词,去", "代词,他", "助词,的", "形容词,美丽"],
                        "correct_answer": "形容词,美丽",
                        "explanation": "\"之\"主要用作动词、代词、助词"
                    }
                ]
            }
        }
        
        templates = question_templates.get(subject, {}).get(chapter, [])
        if templates:
            template = random.choice(templates)
            return {
                "question_text": template["question_text"],
                "question_type": "multiple_choice",
                "options": template["options"],
                "correct_answer": template["correct_answer"],
                "explanation": template["explanation"],
                "difficulty": difficulty,
                "category": subject,
                "points": self._calculate_points(difficulty)
            }
        
        return None
    
    def _calculate_points(self, difficulty):
        """根据难度计算分值"""
        points_map = {
            '入门': 5,
            '基础': 10,
            '提高': 15,
            '拓展': 20,
            '进阶': 25,
            '研究': 30,
            '省级': 20,
            '国家级': 25,
            '国际级': 30
        }
        return points_map.get(difficulty, 10)
    
    def update_question_bank_with_alignment(self):
        """更新题库并对齐教育体系"""
        print("="*70)
        print("📚 开始更新题库并对齐教育体系")
        print("="*70)
        
        # 创建结构
        self.create_education_structure()
        
        # 初始化数据
        self.init_education_data()
        
        # 生成新题目
        new_questions = self.generate_aligned_questions(10)
        
        # 添加到数据库
        added_count = 0
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            for q in new_questions:
                if q:
                    cursor.execute("SELECT id FROM questions WHERE question_text = ?", (q['question_text'],))
                    exists = cursor.fetchone()
                    
                    if not exists:
                        cursor.execute('''
                            INSERT INTO questions 
                            (question_text, question_type, options, correct_answer, 
                             explanation, difficulty, category, points)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            q['question_text'],
                            q['question_type'],
                            json.dumps(q['options']),
                            q['correct_answer'],
                            q['explanation'],
                            q['difficulty'],
                            q['category'],
                            q['points']
                        ))
                        added_count += 1
            
            conn.commit()
        
        # 对齐题目到教育体系
        self.align_questions_to_education()
        
        print(f"✅ 新增 {added_count} 道符合教育体系的题目")
        return {'success': True, 'added': added_count}

# 创建单例
education_alignment = EducationAlignment()

if __name__ == '__main__':
    aligner = EducationAlignment()
    result = aligner.update_question_bank_with_alignment()
    logger.info(f"\n📊 更新完成: {result}")
