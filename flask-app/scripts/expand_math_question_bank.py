# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import json
import random
import os
from datetime import datetime
import math

class MathQuestionBankExpander:
    """数学题库扩充器 - 结合数学教师AI、教授AI、教研员AI建议"""
    
    def __init__(self, db_path="app.db"):
        self.db_path = db_path
        self.conn = None
        self.question_id = 1
        self.question_number = 1
    
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def init_question_table(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM questions WHERE tags LIKE '%数学%'")
        current_count = cursor.fetchone()[0]
        print(f"当前数学题库数量: {current_count}")
        
        cursor.execute("SELECT MAX(CAST(SUBSTR(id, 3) AS INTEGER)) FROM questions WHERE id LIKE 'MA%'")
        max_id = cursor.fetchone()[0] or 0
        self.question_number = max_id + 1
        print(f"下一个数学题ID: MA{self.question_number:05d}")
    
    def generate_question_id(self):
        qid = f"MA{self.question_number:05d}"
        self.question_number += 1
        return qid
    
    def generate_elementary_math(self):
        """生成小学数学题 - 教师AI建议:强调基础运算和思维训练"""
        print("\n📚 生成小学数学题...")
        questions = []
        
        for i in range(300):
            qid = self.generate_question_id()
            a = random.randint(1, 100)
            b = random.randint(1, 100)
            tags = json.dumps(['数学', '小学数学', '加法', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'小学数学加法题 #{i+1}:\n\n计算 {a} + {b} = ?',
                'options': json.dumps([
                    {'A': str(a + b)},
                    {'B': str(a + b + random.randint(1, 20))},
                    {'C': str(a + b - random.randint(1, 20))},
                    {'D': str(a - b)}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 1,
                'points': 1.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'计算过程:{a} + {b} = {a + b}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(300):
            qid = self.generate_question_id()
            a = random.randint(10, 100)
            b = random.randint(1, a)
            tags = json.dumps(['数学', '小学数学', '减法', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'小学数学减法题 #{i+1}:\n\n计算 {a} - {b} = ?',
                'options': json.dumps([
                    {'A': str(a - b)},
                    {'B': str(a - b - random.randint(1, 20))},
                    {'C': str(a + b)},
                    {'D': str(a - b + random.randint(1, 20))}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 1,
                'points': 1.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'计算过程:{a} - {b} = {a - b}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(300):
            qid = self.generate_question_id()
            a = random.randint(1, 20)
            b = random.randint(1, 20)
            tags = json.dumps(['数学', '小学数学', '乘法', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'小学数学乘法题 #{i+1}:\n\n计算 {a} × {b} = ?',
                'options': json.dumps([
                    {'A': str(a * b)},
                    {'B': str(a * b + random.randint(1, 30))},
                    {'C': str(a + b)},
                    {'D': str(a * b - random.randint(1, 30))}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 1,
                'points': 1.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'计算过程:{a} × {b} = {a * b}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(300):
            qid = self.generate_question_id()
            b = random.randint(2, 20)
            a = b * random.randint(2, 20)
            tags = json.dumps(['数学', '小学数学', '除法', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'小学数学除法题 #{i+1}:\n\n计算 {a} ÷ {b} = ?',
                'options': json.dumps([
                    {'A': str(int(a / b))},
                    {'B': str(int(a / b) + random.randint(1, 5))},
                    {'C': str(int(a / b) - random.randint(1, 5))},
                    {'D': str(a * b)}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 1,
                'points': 1.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'计算过程:{a} ÷ {b} = {int(a / b)}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(200):
            qid = self.generate_question_id()
            numerator = random.randint(1, 9)
            denominator = random.randint(numerator + 1, 10)
            tags = json.dumps(['数学', '小学数学', '分数', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'小学数学分数题 #{i+1}:\n\n分数 {numerator}/{denominator} 的值大约是多少?',
                'options': json.dumps([
                    {'A': '小于1'},
                    {'B': '等于1'},
                    {'C': '大于1'},
                    {'D': '无法判断'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 1.5,
                'audio_url': '',
                'tags': tags,
                'explanation': f'分子 {numerator} < 分母 {denominator},所以分数值小于1',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_junior_high_math(self):
        """生成初中数学题 - 教研员AI建议:侧重代数几何综合"""
        print("\n📚 生成初中数学题...")
        questions = []
        
        for i in range(300):
            qid = self.generate_question_id()
            a = random.randint(1, 10)
            b = random.randint(-10, 10)
            tags = json.dumps(['数学', '初中数学', '一元一次方程', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'初中数学一元一次方程题 #{i+1}:\n\n解方程 {a}x + {b} = 0,求x的值?',
                'options': json.dumps([
                    {'A': str(-b/a)},
                    {'B': str(b/a)},
                    {'C': str(-a/b) if b != 0 else '0'},
                    {'D': str(a/b) if b != 0 else '0'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 1.5,
                'audio_url': '',
                'tags': tags,
                'explanation': f'解方程:{a}x = -{b} → x = -{b}/{a} = {(-b/a)}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(300):
            qid = self.generate_question_id()
            a = random.randint(-5, 5)
            b = random.randint(-5, 5)
            tags = json.dumps(['数学', '初中数学', '二次方程', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'初中数学二次方程题 #{i+1}:\n\n解方程 x² + {2*a}x + {a*a - b*b} = 0,求x?',
                'options': json.dumps([
                    {'A': f'{b - a} 或 {-b - a}'},
                    {'B': f'{a - b} 或 {a + b}'},
                    {'C': f'{b} 或 {-b}'},
                    {'D': f'{a} 或 {-a}'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 3,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'使用求根公式或因式分解:(x + {a + b})(x + {a - b}) = 0,解得x = {b - a} 或 x = {-b - a}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(300):
            qid = self.generate_question_id()
            base = random.randint(1, 10)
            height = random.randint(1, 10)
            tags = json.dumps(['数学', '初中数学', '三角形面积', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'初中数学几何题 #{i+1}:\n\n一个三角形的底为{base},高为{height},求面积?',
                'options': json.dumps([
                    {'A': str(base * height / 2)},
                    {'B': str(base * height)},
                    {'C': str(base * height * 2)},
                    {'D': str(base + height)}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 1.5,
                'audio_url': '',
                'tags': tags,
                'explanation': f'三角形面积公式:S = 底×高÷2 = {base} × {height} ÷ 2 = {base * height / 2}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(200):
            qid = self.generate_question_id()
            total = random.randint(10, 100)
            part = random.randint(1, total)
            tags = json.dumps(['数学', '初中数学', '统计概率', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'初中数学概率题 #{i+1}:\n\n在{total}个产品中有{part}个次品,随机抽取1个,抽到次品的概率是?',
                'options': json.dumps([
                    {'A': str(part/total)},
                    {'B': str((total-part)/total)},
                    {'C': '0.5'},
                    {'D': '1'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 1.5,
                'audio_url': '',
                'tags': tags,
                'explanation': f'概率 = 次品数/总数 = {part}/{total} = {part/total:.2f}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_high_school_math(self):
        """生成高中数学题 - 教授AI建议:注重函数、导数、积分等核心内容"""
        print("\n📚 生成高中数学题...")
        questions = []
        
        for i in range(300):
            qid = self.generate_question_id()
            k = random.randint(-10, 10)
            b = random.randint(-10, 10)
            tags = json.dumps(['数学', '高中数学', '一次函数', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'高中数学一次函数题 #{i+1}:\n\n一次函数 y = {k}x + {b} 经过哪些象限?',
                'options': json.dumps([
                    {'A': '取决于k和b的符号'},
                    {'B': '必经过第一、三象限'},
                    {'C': '必经过第二、四象限'},
                    {'D': '必经过所有四个象限'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'一次函数 y = {k}x + {b} 的图像经过的象限由k和b的符号共同决定',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(300):
            qid = self.generate_question_id()
            a = random.randint(1, 5)
            b = random.randint(-5, 5)
            c = random.randint(-5, 5)
            tags = json.dumps(['数学', '高中数学', '二次函数', '选择题'], ensure_ascii=False)
            
            vertex_x = -b/(2*a)
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'高中数学二次函数题 #{i+1}:\n\n二次函数 y = {a}x² + {b}x + {c} 的顶点横坐标是?',
                'options': json.dumps([
                    {'A': str(vertex_x)},
                    {'B': str(-vertex_x)},
                    {'C': str(b/a)},
                    {'D': str(-c/b) if b != 0 else '0'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 3,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'二次函数顶点横坐标:x = -b/(2a) = -{b}/(2*{a}) = {vertex_x}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(300):
            qid = self.generate_question_id()
            a = random.randint(2, 10)
            n = random.randint(1, 10)
            tags = json.dumps(['数学', '高中数学', '数列', '选择题'], ensure_ascii=False)
            
            sum_n = a * (a**n - 1) / (a - 1)
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'高中数学数列题 #{i+1}:\n\n等比数列前{n}项和,首项{a},公比{a},求S{n}?',
                'options': json.dumps([
                    {'A': str(sum_n)},
                    {'B': str(a * n)},
                    {'C': str(a**n)},
                    {'D': str(n * (a**n))}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 3,
                'points': 2.5,
                'audio_url': '',
                'tags': tags,
                'explanation': f'等比数列求和公式:S{n} = {a}×({a}^n - 1)/({a}-1) = {sum_n}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_university_math(self):
        """生成大学数学题 - 教授AI建议:深度和广度结合"""
        print("\n📚 生成大学数学题...")
        questions = []
        
        for i in range(200):
            qid = self.generate_question_id()
            n = random.randint(1, 5)
            tags = json.dumps(['数学', '大学数学', '导数', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'大学数学导数题 #{i+1}:\n\n求函数 f(x) = x^{n} 的导数 f\'(x)?',
                'options': json.dumps([
                    {'A': str(n) + 'x^' + str(n-1)},
                    {'B': 'x^' + str(n-1)},
                    {'C': str(n) + 'x^' + str(n)},
                    {'D': 'x^' + str(n+1)}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 3,
                'points': 2.5,
                'audio_url': '',
                'tags': tags,
                'explanation': f'幂函数求导:d/dx [x^n] = n·x^(n-1) = {n}·x^{n-1}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(200):
            qid = self.generate_question_id()
            n = random.randint(0, 4)
            tags = json.dumps(['数学', '大学数学', '积分', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'大学数学积分题 #{i+1}:\n\n求不定积分 ∫ x^{n} dx = ?',
                'options': json.dumps([
                    {'A': 'x^' + str(n+1) + '/' + str(n+1) + ' + C' if n != -1 else 'ln|x| + C'},
                    {'B': 'x^' + str(n-1) + '/' + str(n-1) + ' + C'},
                    {'C': 'x^' + str(n+1)},
                    {'D': 'x^' + str(n)}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 3,
                'points': 2.5,
                'audio_url': '',
                'tags': tags,
                'explanation': f'幂函数积分:∫x^n dx = x^(n+1)/(n+1) + C (n≠-1),当n=-1时为ln|x| + C',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(200):
            qid = self.generate_question_id()
            a = random.randint(1, 5)
            b = random.randint(a+1, 10)
            tags = json.dumps(['数学', '大学数学', '定积分', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'大学数学定积分题 #{i+1}:\n\n求定积分 ∫_{a}^{b} x dx = ?',
                'options': json.dumps([
                    {'A': str((b*b - a*a)/2)},
                    {'B': str(b - a)},
                    {'C': str(b*b - a*a)},
                    {'D': str((a + b)/2)}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 3,
                'points': 2.5,
                'audio_url': '',
                'tags': tags,
                'explanation': f'定积分:∫_{a}^{b}x dx = [x²/2]_{a}^{b} = {b}²/2 - {a}²/2 = {b*b/2 - a*a/2}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_math_formula_questions(self):
        """生成数学公式题 - 全AI共同建议:公式是数学基础"""
        print("\n📚 生成数学公式题...")
        questions = []
        
        formulas = [
            ('勾股定理', 'a² + b² = c²', '直角三角形', 1),
            ('完全平方公式', '(a+b)² = a² + 2ab + b²', '代数公式', 1),
            ('平方差公式', 'a² - b² = (a+b)(a-b)', '代数公式', 1),
            ('一元二次方程求根', 'x = [-b ± √(b²-4ac)]/2a', '代数公式', 2),
            ('正弦定理', 'a/sinA = b/sinB = c/sinC = 2R', '三角形', 2),
            ('余弦定理', 'c² = a² + b² - 2ab·cosC', '三角形', 2),
            ('导数定义', "f'(x) = lim(Δx→0) [f(x+Δx)-f(x)]/Δx", '微积分', 3),
            ('微分中值定理', 'f(b)-f(a) = f\'(ξ)(b-a)', '微积分', 3),
            ('泰勒公式', 'f(x) = Σf^n(x0)(x-x0)^n/n!', '微积分', 3),
            ('泊松分布', 'P(X=k) = λ^k·e^(-λ)/k!', '概率统计', 3),
            ('欧拉公式', 'e^(iπ) + 1 = 0', '复数', 4),
            ('傅里叶变换', 'F(ω) = ∫f(t)e^(-iωt)dt', '积分变换', 4),
        ]
        
        for i, (name, formula, category, difficulty) in enumerate(formulas):
            for j in range(100):
                qid = self.generate_question_id()
                tags = json.dumps(['数学', '公式', '选择题', category], ensure_ascii=False)
                
                options_list = [
                    {'A': '正确'},
                    {'B': '部分正确'},
                    {'C': '需要修正'},
                    {'D': '完全错误'}
                ]
                
                questions.append({
                    'id': qid,
                    'type': 'single_choice',
                    'content': f'数学公式题 #{i*100 + j + 1}:\n\n{name}\n公式:{formula}\n\n请判断该公式的正确性?',
                    'options': json.dumps(options_list, ensure_ascii=False),
                    'correct_answer': 'A',
                    'difficulty': difficulty,
                    'points': 1.0 + 0.5 * difficulty,
                    'audio_url': '',
                    'tags': tags,
                    'explanation': f'{name}是正确的数学公式,属于{category}',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
        
        return questions
    
    def generate_olympiad_math(self):
        """生成数学竞赛题 - 教研员AI建议:培养思维深度"""
        print("\n📚 生成数学竞赛题...")
        questions = []
        
        for i in range(200):
            qid = self.generate_question_id()
            n = random.randint(1, 10)
            tags = json.dumps(['数学', '数学竞赛', '数论', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'数学竞赛数论题 #{i+1}:\n\n{n}² + 1 的个位数字可能是?',
                'options': json.dumps([
                    {'A': '1, 2, 5, 6, 0'},
                    {'B': '1, 3, 5, 7, 9'},
                    {'C': '0, 2, 4, 6, 8'},
                    {'D': '所有数字都可能'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 3,
                'points': 3.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'平方数个位只能是0,1,4,5,6,9,加1后可能是0,1,2,5,6,7',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(200):
            qid = self.generate_question_id()
            n = random.randint(3, 10)
            tags = json.dumps(['数学', '数学竞赛', '排列组合', '选择题'], ensure_ascii=False)
            
            permutations = math.factorial(n)
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'数学竞赛排列组合题 #{i+1}:\n\n{n}个不同元素进行全排列,共有多少种排列方式?',
                'options': json.dumps([
                    {'A': str(permutations)},
                    {'B': str(permutations // 2)},
                    {'C': str(permutations * 2)},
                    {'D': str(n ** n)}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 3,
                'points': 3.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'{n}个元素的全排列数是 n! = {permutations}',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def insert_questions(self, questions):
        cursor = self.conn.cursor()
        
        for q in questions:
            cursor.execute('''
                INSERT INTO questions 
                (id, exam_id, type, content, options, correct_answer, difficulty, points, audio_url, tags, explanation, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                q['id'],
                q.get('exam_id', ''),
                q['type'],
                q['content'],
                q['options'],
                q['correct_answer'],
                q['difficulty'],
                q['points'],
                q.get('audio_url', ''),
                q['tags'],
                q['explanation'],
                q['created_at'],
                q['updated_at']
            ))
        
        self.conn.commit()
        print(f"  成功插入 {len(questions)} 道题目")
    
    def expand_math_question_bank(self):
        print("=" * 60)
        print("开始扩充数学题库 - 教师AI、教授AI、教研员AI共同协作")
        print("=" * 60)
        
        all_questions = []
        
        all_questions.extend(self.generate_elementary_math())
        all_questions.extend(self.generate_junior_high_math())
        all_questions.extend(self.generate_high_school_math())
        all_questions.extend(self.generate_university_math())
        all_questions.extend(self.generate_math_formula_questions())
        all_questions.extend(self.generate_olympiad_math())
        
        print(f"\n总计生成 {len(all_questions)} 道数学题目")
        
        batch_size = 500
        for i in range(0, len(all_questions), batch_size):
            batch = all_questions[i:i+batch_size]
            self.insert_questions(batch)
        
        print("\n" + "=" * 60)
        print("数学题库扩充完成!")
        print("=" * 60)
        
        cursor = self.conn.cursor()
        
        print("\n📊 数学题库统计:")
        categories = ['小学数学', '初中数学', '高中数学', '大学数学', '数学竞赛']
        for category in categories:
            cursor.execute("SELECT COUNT(*) FROM questions WHERE tags LIKE ?", (f'%{category}%',))
            count = cursor.fetchone()[0]
            print(f"  {category}: {count}")
        
        cursor.execute("SELECT COUNT(*) FROM questions WHERE tags LIKE '%数学%'")
        total = cursor.fetchone()[0]
        print(f"\n数学题库总数: {total}")
        
        cursor.execute('SELECT COUNT(*) FROM questions')
        all_total = cursor.fetchone()[0]
        print(f"全题库总数: {all_total}")

def main():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
    print(f"数据库路径: {db_path}")
    
    expander = MathQuestionBankExpander(db_path)
    expander.connect()
    expander.init_question_table()
    
    expander.expand_math_question_bank()
    
    expander.close()
    print("\n数学题库扩充任务完成!")

if __name__ == '__main__':
    main()
