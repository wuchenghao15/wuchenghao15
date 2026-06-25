import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import json
import random
import time
from datetime import datetime
import math

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

class EnhancedQuestionGenerator:
    """增强版大规模题目生成器"""
    
    def __init__(self):
        self.generated_count = 0
        self.duplicate_count = 0
        
        self.math_constants = ['π', 'e', '√2', '√3']
        self.units = ['m', 'kg', 's', 'm/s', 'm/s²', 'N', 'J', 'W', 'V', 'A', 'Ω']
        
        self.number_ranges = {
            '小学': (1, 100),
            '初中': (1, 1000),
            '高中': (1, 10000),
            '大学': (1, 100000),
            '竞赛': (1, 1000000)
        }
    
    def generate_arithmetic_question(self, level):
        """生成算术题目"""
        r = self.number_ranges[level]
        a = random.randint(*r)
        b = random.randint(max(1, r[0]), min(100, r[1]))
        
        ops = ['+', '-', '*', '/']
        op = random.choice(ops)
        
        if op == '+':
            answer = a + b
        elif op == '-':
            a, b = max(a, b), min(a, b)
            answer = a - b
        elif op == '*':
            answer = a * b
        else:
            while b == 0 or a % b != 0:
                b = random.randint(max(1, r[0]), min(50, r[1]))
            answer = a // b
        
        return {
            'question_text': f"{level}数学 - 算术: 计算 {a} {op} {b} = ?",
            'options': self._generate_numeric_options(answer),
            'correct_answer': str(answer),
            'category': '数学',
            'difficulty': self._get_difficulty(level),
            'points': self._get_points(level)
        }
    
    def generate_algebra_question(self, level):
        """生成代数题目"""
        r = self.number_ranges[level]
        a = random.randint(1, 10)
        b = random.randint(1, 20)
        c = random.randint(b+1, 50)
        
        question_text = f"{level}数学 - 代数: 解方程 {a}x + {b} = {c},x = ?"
        answer = (c - b) // a
        
        return {
            'question_text': question_text,
            'options': self._generate_numeric_options(answer),
            'correct_answer': str(answer),
            'category': '数学',
            'difficulty': self._get_difficulty(level),
            'points': self._get_points(level)
        }
    
    def generate_geometry_question(self, level):
        """生成几何题目"""
        r = self.number_ranges[level]
        shapes = ['正方形', '长方形', '圆形', '三角形', '正方体', '球体']
        shape = random.choice(shapes)
        
        if shape == '正方形':
            a = random.randint(1, 20)
            area = a * a
            question_text = f"{level}数学 - 几何: 边长为{a}cm的{shape}面积是多少平方厘米?"
            answer = str(area)
        
        elif shape == '长方形':
            a, b = random.randint(1, 20), random.randint(1, 20)
            area = a * b
            question_text = f"{level}数学 - 几何: 长{a}cm宽{b}cm的{shape}面积是多少平方厘米?"
            answer = str(area)
        
        elif shape == '圆形':
            r = random.randint(1, 10)
            area = int(math.pi * r * r)
            question_text = f"{level}数学 - 几何: 半径为{r}cm的{shape}面积约是多少平方厘米?"
            answer = str(area)
        
        elif shape == '三角形':
            a, h = random.randint(1, 20), random.randint(1, 20)
            area = (a * h) // 2
            question_text = f"{level}数学 - 几何: 底{a}cm高{h}cm的{shape}面积是多少平方厘米?"
            answer = str(area)
        
        elif shape == '正方体':
            a = random.randint(1, 10)
            vol = a * a * a
            question_text = f"{level}数学 - 几何: 棱长为{a}cm的{shape}体积是多少立方厘米?"
            answer = str(vol)
        
        else:
            r = random.randint(1, 10)
            vol = int((4/3) * math.pi * r * r * r)
            question_text = f"{level}数学 - 几何: 半径为{r}cm的{shape}体积约是多少立方厘米?"
            answer = str(vol)
        
        return {
            'question_text': question_text,
            'options': self._generate_numeric_options(int(answer)),
            'correct_answer': answer,
            'category': '数学',
            'difficulty': self._get_difficulty(level),
            'points': self._get_points(level)
        }
    
    def generate_probability_question(self, level):
        """生成概率统计题目"""
        total = random.randint(2, 20)
        target = random.randint(1, total-1)
        
        question_text = f"{level}数学 - 概率: 从{total}个球中随机取一个,恰好取到目标球的概率是?"
        answer = f"{target}/{total}"
        
        return {
            'question_text': question_text,
            'options': [answer, f"{total-target}/{total}", f"1/{total}", f"{target-1}/{total}"],
            'correct_answer': answer,
            'category': '数学',
            'difficulty': self._get_difficulty(level),
            'points': self._get_points(level)
        }
    
    def generate_english_vocab_question(self, level):
        """生成英语词汇题目"""
        vocab_list = [
            ('apple', '苹果'), ('book', '书'), ('cat', '猫'), ('dog', '狗'), ('egg', '鸡蛋'),
            ('flower', '花'), ('garden', '花园'), ('house', '房子'), ('island', '岛屿'), ('jungle', '丛林'),
            ('kitchen', '厨房'), ('library', '图书馆'), ('mountain', '山'), ('notebook', '笔记本'), ('orange', '橙子'),
            ('picture', '图片'), ('question', '问题'), ('rainbow', '彩虹'), ('sunshine', '阳光'), ('teacher', '老师'),
            ('university', '大学'), ('vegetable', '蔬菜'), ('water', '水'), ('yellow', '黄色'), ('zebra', '斑马')
        ]
        
        word, meaning = random.choice(vocab_list)
        
        wrong_choices = [v[1] for v in random.sample(vocab_list, 3) if v[1] != meaning]
        options = [meaning] + wrong_choices
        random.shuffle(options)
        
        return {
            'question_text': f"{level}英语 - 词汇: '{word}' 的中文意思是?",
            'options': options,
            'correct_answer': meaning,
            'category': '英语',
            'difficulty': self._get_difficulty(level),
            'points': self._get_points(level)
        }
    
    def generate_english_grammar_question(self, level):
        """生成英语语法题目"""
        grammar_templates = [
            {
                'question': f"{level}英语 - 语法: She ___ to school every day.",
                'options': ['go', 'goes', 'going', 'went'],
                'answer': 'goes'
            },
            {
                'question': f"{level}英语 - 语法: I have ___ finished my homework.",
                'options': ['already', 'yet', 'ever', 'never'],
                'answer': 'already'
            },
            {
                'question': f"{level}英语 - 语法: This is the book ___ I bought.",
                'options': ['who', 'which', 'what', 'whom'],
                'answer': 'which'
            },
            {
                'question': f"{level}英语 - 语法: He is good ___ math.",
                'options': ['at', 'in', 'on', 'with'],
                'answer': 'at'
            },
            {
                'question': f"{level}英语 - 语法: The meeting ___ at 3 PM.",
                'options': ['start', 'starts', 'started', 'starting'],
                'answer': 'starts'
            }
        ]
        
        template = random.choice(grammar_templates)
        
        return {
            'question_text': template['question'],
            'options': template['options'],
            'correct_answer': template['answer'],
            'category': '英语',
            'difficulty': self._get_difficulty(level),
            'points': self._get_points(level)
        }
    
    def generate_physics_question(self, level):
        """生成物理题目"""
        physics_templates = [
            {
                'func': lambda: {'m': random.randint(1, 10), 'F': random.randint(10, 100)},
                'template': "{level}物理 - 力学: 质量{m}kg的物体受到{F}N的力,加速度是多少m/s²?",
                'answer_func': lambda m, F: str(F // m)
            },
            {
                'func': lambda: {'v': random.randint(10, 100), 't': random.randint(1, 10)},
                'template': "{level}物理 - 力学: 物体以{v}m/s的速度运动{t}秒,位移是多少米?",
                'answer_func': lambda v, t: str(v * t)
            },
            {
                'func': lambda: {'I': random.randint(1, 10), 'R': random.randint(1, 20)},
                'template': "{level}物理 - 电磁: {I}A电流通过{R}Ω电阻,电压是多少伏特?",
                'answer_func': lambda I, R: str(I * R)
            },
            {
                'func': lambda: {'P': random.randint(10, 100), 't': random.randint(1, 10)},
                'template': "{level}物理 - 能量: {P}W的功率工作{t}秒,消耗多少焦耳能量?",
                'answer_func': lambda P, t: str(P * t)
            }
        ]
        
        template = random.choice(physics_templates)
        params = template['func']()
        answer = template['answer_func'](**params)
        
        params['level'] = level
        return {
            'question_text': template['template'].format(**params),
            'options': self._generate_numeric_options(int(answer)),
            'correct_answer': answer,
            'category': '物理',
            'difficulty': self._get_difficulty(level),
            'points': self._get_points(level)
        }
    
    def generate_chemistry_question(self, level):
        """生成化学题目"""
        chemistry_templates = [
            {
                'question': f"{level}化学 - 基础: 水的化学式是?",
                'options': ['H₂O', 'CO₂', 'NaCl', 'H₂SO₄'],
                'answer': 'H₂O'
            },
            {
                'question': f"{level}化学 - 基础: 二氧化碳的化学式是?",
                'options': ['CO₂', 'H₂O', 'O₂', 'N₂'],
                'answer': 'CO₂'
            },
            {
                'question': f"{level}化学 - 基础: 氧元素的原子序数是?",
                'options': ['8', '6', '1', '26'],
                'answer': '8'
            },
            {
                'question': f"{level}化学 - 基础: 酸和碱反应生成什么?",
                'options': ['盐和水', '氧气', '氢气', '二氧化碳'],
                'answer': '盐和水'
            },
            {
                'question': f"{level}化学 - 基础: 氯化钠的化学式是?",
                'options': ['NaCl', 'HCl', 'NaOH', 'H₂O'],
                'answer': 'NaCl'
            }
        ]
        
        template = random.choice(chemistry_templates)
        
        return {
            'question_text': template['question'],
            'options': template['options'],
            'correct_answer': template['answer'],
            'category': '化学',
            'difficulty': self._get_difficulty(level),
            'points': self._get_points(level)
        }
    
    def generate_chinese_question(self, level):
        """生成语文题目"""
        chinese_templates = [
            {
                'question': f"{level}语文 - 诗词: '床前明月光'的作者是?",
                'options': ['李白', '杜甫', '白居易', '王维'],
                'answer': '李白'
            },
            {
                'question': f"{level}语文 - 诗词: '春眠不觉晓'出自哪首诗?",
                'options': ['春晓', '静夜思', '登鹳雀楼', '望庐山瀑布'],
                'answer': '春晓'
            },
            {
                'question': f"{level}语文 - 文言: '之'在文言文中常用作什么词?",
                'options': ['代词', '动词', '形容词', '副词'],
                'answer': '代词'
            },
            {
                'question': f"{level}语文 - 修辞: '飞流直下三千尺'使用了什么修辞手法?",
                'options': ['夸张', '比喻', '拟人', '排比'],
                'answer': '夸张'
            },
            {
                'question': f"{level}语文 - 成语: '画蛇添足'的寓意是?",
                'options': ['多此一举', '画龙点睛', '锦上添花', '雪中送炭'],
                'answer': '多此一举'
            }
        ]
        
        template = random.choice(chinese_templates)
        
        return {
            'question_text': template['question'],
            'options': template['options'],
            'correct_answer': template['answer'],
            'category': '语文',
            'difficulty': self._get_difficulty(level),
            'points': self._get_points(level)
        }
    
    def generate_programming_question(self, level):
        """生成编程题目"""
        programming_templates = [
            {
                'question': f"{level}编程 - Python: 输出'Hello World'的代码是?",
                'options': ["print('Hello World')", "echo 'Hello World'", "printf('Hello World')", "console.log('Hello World')"],
                'answer': "print('Hello World')"
            },
            {
                'question': f"{level}编程 - 概念: 变量的作用是什么?",
                'options': ['存储数据', '执行命令', '定义函数', '输出结果'],
                'answer': '存储数据'
            },
            {
                'question': f"{level}编程 - 数据结构: 列表的索引从几开始?",
                'options': ['0', '1', '-1', '任意'],
                'answer': '0'
            },
            {
                'question': f"{level}编程 - 控制流: if语句用于什么?",
                'options': ['条件判断', '循环', '函数定义', '变量声明'],
                'answer': '条件判断'
            },
            {
                'question': f"{level}编程 - 概念: 什么是循环?",
                'options': ['重复执行代码', '定义变量', '输出结果', '导入模块'],
                'answer': '重复执行代码'
            }
        ]
        
        template = random.choice(programming_templates)
        
        return {
            'question_text': template['question'],
            'options': template['options'],
            'correct_answer': template['answer'],
            'category': '编程',
            'difficulty': self._get_difficulty(level),
            'points': self._get_points(level)
        }
    
    def generate_computer_question(self, level):
        """生成计算机题目"""
        computer_templates = [
            {
                'question': f"{level}计算机 - 基础: CPU的全称是?",
                'options': ['Central Processing Unit', 'Computer Processing Unit', 'Control Processing Unit', 'Core Processing Unit'],
                'answer': 'Central Processing Unit'
            },
            {
                'question': f"{level}计算机 - 网络: HTTP协议默认端口是?",
                'options': ['80', '443', '21', '22'],
                'answer': '80'
            },
            {
                'question': f"{level}计算机 - 基础: RAM是什么?",
                'options': ['随机存取存储器', '只读存储器', '硬盘', '显卡'],
                'answer': '随机存取存储器'
            },
            {
                'question': f"{level}计算机 - 网络: HTTPS使用什么端口?",
                'options': ['443', '80', '8080', '3000'],
                'answer': '443'
            },
            {
                'question': f"{level}计算机 - 基础: 二进制中1+1等于?",
                'options': ['10', '2', '11', '0'],
                'answer': '10'
            }
        ]
        
        template = random.choice(computer_templates)
        
        return {
            'question_text': template['question'],
            'options': template['options'],
            'correct_answer': template['answer'],
            'category': '计算机',
            'difficulty': self._get_difficulty(level),
            'points': self._get_points(level)
        }
    
    def _generate_numeric_options(self, answer):
        """生成数字选项"""
        options = [str(answer)]
        while len(options) < 4:
            wrong = answer + random.randint(-10, 10)
            if wrong != answer and str(wrong) not in options:
                options.append(str(wrong))
        random.shuffle(options)
        return options
    
    def _get_difficulty(self, level):
        """获取难度等级"""
        difficulty_map = {
            '小学': ['入门', '基础', '提高'],
            '初中': ['基础', '提高', '拓展'],
            '高中': ['提高', '拓展', '竞赛'],
            '大学': ['拓展', '进阶', '研究'],
            '竞赛': ['省级', '国家级', '国际级']
        }
        return random.choice(difficulty_map[level])
    
    def _get_points(self, level):
        """获取分值"""
        points_map = {
            '小学': 5,
            '初中': 10,
            '高中': 15,
            '大学': 20,
            '竞赛': 25
        }
        return points_map[level]
    
    def generate_question(self):
        """生成单个题目"""
        level = random.choice(['小学', '初中', '高中', '大学', '竞赛'])
        
        generators = [
            self.generate_arithmetic_question,
            self.generate_algebra_question,
            self.generate_geometry_question,
            self.generate_probability_question,
            self.generate_english_vocab_question,
            self.generate_english_grammar_question,
            self.generate_physics_question,
            self.generate_chemistry_question,
            self.generate_chinese_question,
            self.generate_programming_question,
            self.generate_computer_question
        ]
        
        generator = random.choice(generators)
        return generator(level)
    
    def generate_batch(self, count=1000):
        """批量生成题目"""
        questions = []
        for _ in range(count):
            q = self.generate_question()
            if q:
                questions.append(q)
        return questions
    
    def save_to_database(self, questions):
        """保存题目到数据库"""
        if not questions:
            return 0
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            added = 0
            
            for q in questions:
                cursor.execute("SELECT id FROM questions WHERE question_text = ?", (q['question_text'],))
                if cursor.fetchone():
                    self.duplicate_count += 1
                    continue
                
                cursor.execute('''
                    INSERT INTO questions 
                    (question_text, question_type, options, correct_answer, 
                     explanation, difficulty, category, points)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                def run_operation(**kwargs):
                ''', (
                    q['question_text'],
                    'multiple_choice',
                    json.dumps(q['options']),
                    q['correct_answer'],
                    f"{q['category']}知识点解析",
                    q['difficulty'],
                    q['category'],
                    q['points']
                ))
                added += 1
            
            conn.commit()
        
        self.generated_count += added
        return added
    
    def generate_mass_questions(self, target_count=100000, batch_size=5000):
        """大规模生成题目"""
        print(f"🚀 开始生成 {target_count} 道题目...")
        start_time = time.time()
        
        while self.generated_count < target_count:
            remaining = target_count - self.generated_count
            current_batch = min(batch_size, remaining)
            
            print(f"\n📝 正在生成第 {self.generated_count+1}-{min(self.generated_count+current_batch, target_count)} 道题目...")
            
            questions = self.generate_batch(current_batch)
            added = self.save_to_database(questions)
            
            elapsed = time.time() - start_time
            rate = self.generated_count / elapsed if elapsed > 0 else 0
            remaining_time = (target_count - self.generated_count) / rate if rate > 0 else 0
            
            print(f"✅ 新增: {added} 道 | 总数: {self.generated_count} | 重复: {self.duplicate_count}")
            print(f"⏱️  耗时: {elapsed:.2f}秒 | 速度: {rate:.2f}题/秒 | 预计剩余: {remaining_time:.2f}秒")
            
            # 每生成50000题保存一次进度
            if self.generated_count % 50000 == 0 and self.generated_count > 0:
                print(f"\n📌 已生成 {self.generated_count} 道题目,继续中...")
        
        elapsed_total = time.time() - start_time
        print(f"\n🎉 生成完成!")
        print(f"📊 最终统计:")
        print(f"   生成题目: {self.generated_count} 道")
        print(f"   重复跳过: {self.duplicate_count} 道")
        print(f"   总耗时: {elapsed_total:.2f} 秒")
        print(f"   平均速度: {self.generated_count/elapsed_total:.2f} 题/秒")
        
        return {
            'success': True,
            'generated': self.generated_count,
            'duplicates': self.duplicate_count,
            'time_elapsed': elapsed_total
        }

if __name__ == '__main__':
    generator = EnhancedQuestionGenerator()
    result = generator.generate_mass_questions(target_count=50000)
    logger.info("\n📊 结果:", result)
