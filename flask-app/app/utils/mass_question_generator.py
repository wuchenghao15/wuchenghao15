import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import json
import random
import time
from datetime import datetime
import threading
import queue
import os

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

class MassQuestionGenerator:
    """大规模题目生成器"""
    
    def __init__(self):
        self.subjects = {
            '数学': ['代数', '几何', '概率统计', '微积分', '线性代数', '数论'],
            '语文': ['阅读理解', '写作', '文言文', '诗词鉴赏', '语法修辞'],
            '英语': ['词汇', '语法', '阅读理解', '写作', '听力', '口语'],
            '物理': ['力学', '电磁学', '光学', '热学', '量子物理'],
            '化学': ['无机化学', '有机化学', '分析化学', '物理化学'],
            '编程': ['Python', 'C++', '数据结构', '算法', '数据库'],
            '计算机': ['计算机基础', '网络技术', '操作系统', '人工智能']
        }
        
        self.education_levels = ['小学', '初中', '高中', '大学', '竞赛']
        
        self.difficulty_map = {
            '小学': ['入门', '基础', '提高'],
            '初中': ['基础', '提高', '拓展'],
            '高中': ['基础', '提高', '拓展', '竞赛'],
            '大学': ['基础', '提高', '进阶', '研究'],
            '竞赛': ['省级', '国家级', '国际级']
        }
        
        # 数学题目模板
        self.math_templates = {
            '代数': [
                {"template": "{level}数学 - 代数: 解方程 {a}x {op} {b} = {c},x = ?", "func": self._generate_linear_eq},
                {"template": "{level}数学 - 代数: 化简 ({a}+{b})^2 = ?", "func": self._generate_square},
                {"template": "{level}数学 - 代数: 计算 {a}² + {b}² = ?", "func": self._generate_sum_squares},
                {"template": "{level}数学 - 代数: 如果 x = {x}, 则 2x + {a} = ?", "func": self._generate_simple_expr},
                {"template": "{level}数学 - 代数: 因式分解 x² + {a}x + {b} = ?", "func": self._generate_factor},
                {"template": "{level}数学 - 代数: 解不等式 {a}x + {b} > {c}", "func": self._generate_inequality},
                {"template": "{level}数学 - 代数: 求 {a} 和 {b} 的最大公约数", "func": self._generate_gcd},
                {"template": "{level}数学 - 代数: 求 {a} 和 {b} 的最小公倍数", "func": self._generate_lcm},
            ],
            '几何': [
                {"template": "{level}数学 - 几何: 边长为{a}的正方形面积是?", "func": self._generate_square_area},
                {"template": "{level}数学 - 几何: 半径为{r}的圆面积是?", "func": self._generate_circle_area},
                {"template": "{level}数学 - 几何: 长{a}宽{b}的长方形周长是?", "func": self._generate_rect_perimeter},
                {"template": "{level}数学 - 几何: 底{a}高{b}的三角形面积是?", "func": self._generate_triangle_area},
                {"template": "{level}数学 - 几何: 直径{d}的圆周长是?", "func": self._generate_circle_circumference},
                {"template": "{level}数学 - 几何: 正方体棱长{a},体积是?", "func": self._generate_cube_volume},
                {"template": "{level}数学 - 几何: 长方体长宽高{a},{b},{c},表面积是?", "func": self._generate_box_surface},
                {"template": "{level}数学 - 几何: 直角三角形两直角边{a},{b},斜边是?", "func": self._generate_pythagoras},
            ],
            '概率统计': [
                {"template": "{level}数学 - 概率: 掷骰子得到{target}的概率是?", "func": self._generate_dice_prob},
                {"template": "{level}数学 - 概率: 从{a}个红球{b}个白球中取红球的概率", "func": self._generate_ball_prob},
                {"template": "{level}数学 - 统计: 数据{a},{b},{c},{d},{e}的平均数是?", "func": self._generate_average},
                {"template": "{level}数学 - 统计: 数据{a},{b},{c}的中位数是?", "func": self._generate_median},
                {"template": "{level}数学 - 概率: 抛硬币{a}次都正面的概率", "func": self._generate_coin_prob},
            ],
            '微积分': [
                {"template": "{level}数学 - 微积分: f(x)={expr} 的导数是?", "func": self._generate_derivative},
                {"template": "{level}数学 - 微积分: f(x)={expr} 在x={x}处的导数值", "func": self._generate_derivative_value},
                {"template": "{level}数学 - 微积分: ∫{expr}dx = ?", "func": self._generate_integral},
            ],
            '线性代数': [
                {"template": "{level}数学 - 线代: 矩阵A=[{m11},{m12};{m21},{m22}]的行列式是?", "func": self._generate_matrix_det},
                {"template": "{level}数学 - 线代: 向量{a},{b}的点积是?", "func": self._generate_dot_product},
            ],
            '数论': [
                {"template": "{level}数学 - 数论: 判断{a}是否为质数", "func": self._generate_prime_check},
                {"template": "{level}数学 - 数论: {a}的质因数分解是?", "func": self._generate_factorization},
            ]
        }
        
        # 英语题目模板
        self.english_templates = {
            '词汇': [
                {"template": "{level}英语 - 词汇: '{word}' 的中文意思是?", "func": self._generate_vocab},
                {"template": "{level}英语 - 词汇: '{word}' 的反义词是?", "func": self._generate_antonym},
                {"template": "{level}英语 - 词汇: '{word}' 的同义词是?", "func": self._generate_synonym},
                {"template": "{level}英语 - 词汇: 选择正确的词性: {word} (n./v./adj.)", "func": self._generate_part_of_speech},
            ],
            '语法': [
                {"template": "{level}英语 - 语法: She ___ to school every day. (go/goes/went)", "func": self._generate_verb_form},
                {"template": "{level}英语 - 语法: I have ___ finished my homework. (already/yet/ever)", "func": self._generate_adverb},
                {"template": "{level}英语 - 语法: This is the book ___ I bought. (who/which/what)", "func": self._generate_relative_pronoun},
                {"template": "{level}英语 - 语法: If I ___ rich, I would travel. (am/was/were)", "func": self._generate_subjunctive},
            ],
            '阅读理解': [
                {"template": "{level}英语 - 阅读: The word 'it' in line {n} refers to ?", "func": self._generate_reading_ref},
                {"template": "{level}英语 - 阅读: What is the main idea of the passage?", "func": self._generate_main_idea},
            ]
        }
        
        # 编程题目模板
        self.programming_templates = {
            'Python': [
                {"template": "{level}编程 - Python: 输出{text}的代码是?", "func": self._generate_print_code},
                {"template": "{level}编程 - Python: 计算{a}+{b}的代码是?", "func": self._generate_add_code},
                {"template": "{level}编程 - Python: 列表{lst}的长度是?", "func": self._generate_list_len},
                {"template": "{level}编程 - Python: for循环遍历列表的写法", "func": self._generate_for_loop},
                {"template": "{level}编程 - Python: 判断{a}是否在列表{lst}中", "func": self._generate_in_list},
            ],
            '数据结构': [
                {"template": "{level}编程 - 数据结构: {ds}的时间复杂度是?", "func": self._generate_ds_complexity},
                {"template": "{level}编程 - 数据结构: {op}操作在{ds}上的复杂度", "func": self._generate_op_complexity},
                {"template": "{level}编程 - 数据结构: {ds}适合{scenario}场景吗?", "func": self._generate_ds_scenario},
            ],
            '算法': [
                {"template": "{level}编程 - 算法: {algo}的时间复杂度是?", "func": self._generate_algo_complexity},
                {"template": "{level}编程 - 算法: 排序{n}个元素的最好情况", "func": self._generate_sort_case},
                {"template": "{level}编程 - 算法: {algo}是稳定排序吗?", "func": self._generate_stability},
            ]
        }
        
        # 物理题目模板
        self.physics_templates = {
            '力学': [
                {"template": "{level}物理 - 力学: 质量{m}kg物体受{F}N力,加速度是?", "func": self._generate_newton},
                {"template": "{level}物理 - 力学: 物体从{h}m高处自由落下,落地速度是?", "func": self._generate_free_fall},
                {"template": "{level}物理 - 力学: {m1}kg和{m2}kg物体碰撞后的速度", "func": self._generate_collision},
            ],
            '电磁学': [
                {"template": "{level}物理 - 电磁: {I}A电流通过{R}Ω电阻,电压是?", "func": self._generate_ohm},
                {"template": "{level}物理 - 电磁: {Q}C电荷在{V}V电压下的能量", "func": self._generate_energy},
            ]
        }
        
        # 化学题目模板
        self.chemistry_templates = {
            '无机化学': [
                {"template": "{level}化学 - 无机: {element}的原子序数是?", "func": self._generate_atomic_number},
                {"template": "{level}化学 - 无机: {compound}的化学式是?", "func": self._generate_formula},
                {"template": "{level}化学 - 无机: {acid}和{base}反应生成?", "func": self._generate_neutralization},
            ],
            '有机化学': [
                {"template": "{level}化学 - 有机: {compound}属于{type}类化合物", "func": self._generate_organic_type},
            ]
        }
        
        # 语文题目模板
        self.chinese_templates = {
            '阅读理解': [
                {"template": "{level}语文 - 阅读: '{poem}'的作者是?", "func": self._generate_poem_author},
                {"template": "{level}语文 - 阅读: 这段文字的修辞手法是?", "func": self._generate_rhetoric},
            ],
            '文言文': [
                {"template": "{level}语文 - 文言: '{word}'在文中的意思是?", "func": self._generate_classical_word},
                {"template": "{level}语文 - 文言: '{sentence}'的翻译是?", "func": self._generate_classical_translate},
            ],
            '诗词鉴赏': [
                {"template": "{level}语文 - 诗词: '{poem}'表达了作者什么情感?", "func": self._generate_poem_emotion},
            ]
        }
        
        # 计算机题目模板
        self.computer_templates = {
            '计算机基础': [
                {"template": "{level}计算机 - 基础: {component}的功能是?", "func": self._generate_component_func},
                {"template": "{level}计算机 - 基础: {term}的全称是?", "func": self._generate_full_name},
            ],
            '网络技术': [
                {"template": "{level}计算机 - 网络: {protocol}使用{port}端口", "func": self._generate_port},
                {"template": "{level}计算机 - 网络: OSI模型第{n}层是?", "func": self._generate_osi_layer},
            ],
            '人工智能': [
                {"template": "{level}计算机 - AI: {algo}属于{type}学习", "func": self._generate_ml_type},
                {"template": "{level}计算机 - AI: {concept}的定义是?", "func": self._generate_ai_concept},
            ]
        }
        
        self.template_map = {
            '数学': self.math_templates,
            '语文': self.chinese_templates,
            '英语': self.english_templates,
            '物理': self.physics_templates,
            '化学': self.chemistry_templates,
            '编程': self.programming_templates,
            '计算机': self.computer_templates,
        }
        
        self.generated_count = 0
        self.duplicate_count = 0
        self.lock = threading.Lock()
        self.question_queue = queue.Queue(maxsize=1000)
    
    # 数学题目生成函数
    def _generate_linear_eq(self):
        a = random.randint(1, 10)
        b = random.randint(1, 20)
        op = random.choice(['+', '-'])
        if op == '+':
            c = a * random.randint(1, 10) + b
            x = (c - b) // a
        else:
            c = a * random.randint(1, 10) - b
            x = (c + b) // a
        return {'a': a, 'op': op, 'b': b, 'c': c, 'answer': str(x)}
    
    def _generate_square(self):
        a, b = random.randint(1, 10), random.randint(1, 10)
        answer = f"{a}²+2{a}{b}+{b}²"
        return {'a': a, 'b': b, 'answer': answer}
    
    def _generate_sum_squares(self):
        a, b = random.randint(1, 20), random.randint(1, 20)
        answer = str(a*a + b*b)
        return {'a': a, 'b': b, 'answer': answer}
    
    def _generate_simple_expr(self):
        x = random.randint(1, 10)
        a = random.randint(1, 20)
        answer = str(2*x + a)
        return {'x': x, 'a': a, 'answer': answer}
    
    def _generate_factor(self):
        a = random.randint(2, 10)
        b = random.randint(1, a*a)
        answer = f"(x+{random.randint(1, a)})(x+{random.randint(1, b//a)})"
        return {'a': a, 'b': b, 'answer': answer}
    
    def _generate_inequality(self):
        a = random.randint(1, 5)
        b = random.randint(1, 10)
        c = random.randint(b+1, 30)
        answer = f"x > {(c-b)//a}"
        return {'a': a, 'b': b, 'c': c, 'answer': answer}
    
    def _generate_gcd(self):
        a, b = random.randint(10, 100), random.randint(10, 100)
        answer = str(self._gcd(a, b))
        return {'a': a, 'b': b, 'answer': answer}
    
    def _generate_lcm(self):
        a, b = random.randint(10, 50), random.randint(10, 50)
        answer = str(a * b // self._gcd(a, b))
        return {'a': a, 'b': b, 'answer': answer}
    
    def _gcd(self, a, b):
        while b:
            a, b = b, a % b
        return a
    
    def _generate_square_area(self):
        a = random.randint(1, 20)
        answer = str(a * a)
        return {'a': a, 'answer': answer}
    
    def _generate_circle_area(self):
        r = random.randint(1, 10)
        answer = f"{r*r}π"
        return {'r': r, 'answer': answer}
    
    def _generate_rect_perimeter(self):
        a, b = random.randint(1, 20), random.randint(1, 20)
        answer = str(2 * (a + b))
        return {'a': a, 'b': b, 'answer': answer}
    
    def _generate_triangle_area(self):
        a, b = random.randint(1, 20), random.randint(1, 20)
        answer = str(a * b // 2)
        return {'a': a, 'b': b, 'answer': answer}
    
    def _generate_circle_circumference(self):
        d = random.randint(2, 20)
        answer = f"{d}π"
        return {'d': d, 'answer': answer}
    
    def _generate_cube_volume(self):
        a = random.randint(1, 10)
        answer = str(a * a * a)
        return {'a': a, 'answer': answer}
    
    def _generate_box_surface(self):
        a, b, c = random.randint(1, 10), random.randint(1, 10), random.randint(1, 10)
        answer = str(2 * (a*b + b*c + a*c))
        return {'a': a, 'b': b, 'c': c, 'answer': answer}
    
    def _generate_pythagoras(self):
        a, b = random.randint(3, 10), random.randint(4, 10)
        c = int((a*a + b*b)**0.5)
        answer = str(c) if c*c == a*a + b*b else f"√({a*a + b*b})"
        return {'a': a, 'b': b, 'answer': answer}
    
    def _generate_dice_prob(self):
        target = random.randint(1, 6)
        answer = "1/6"
        return {'target': target, 'answer': answer}
    
    def _generate_ball_prob(self):
        a, b = random.randint(1, 10), random.randint(1, 10)
        answer = f"{a}/{a+b}"
        return {'a': a, 'b': b, 'answer': answer}
    
    def _generate_average(self):
        nums = [random.randint(1, 100) for _ in range(5)]
        avg = sum(nums) // 5
        answer = str(avg)
        return {'a': nums[0], 'b': nums[1], 'c': nums[2], 'd': nums[3], 'e': nums[4], 'answer': answer}
    
    def _generate_median(self):
        nums = sorted([random.randint(1, 100) for _ in range(3)])
        answer = str(nums[1])
        return {'a': nums[0], 'b': nums[1], 'c': nums[2], 'answer': answer}
    
    def _generate_coin_prob(self):
        a = random.randint(1, 5)
        answer = f"1/{2**a}"
        return {'a': a, 'answer': answer}
    
    def _generate_derivative(self):
        exprs = ["x²", "2x", "x³", "sin(x)", "cos(x)", "e^x", "ln(x)"]
        derivs = ["2x", "2", "3x²", "cos(x)", "-sin(x)", "e^x", "1/x"]
        idx = random.randint(0, len(exprs)-1)
        return {'expr': exprs[idx], 'answer': derivs[idx]}
    
    def _generate_derivative_value(self):
        x = random.randint(1, 5)
        answer = str(2 * x)
        return {'expr': "x²", 'x': x, 'answer': answer}
    
    def _generate_integral(self):
        exprs = ["2x", "x²", "cos(x)", "e^x"]
        integrals = ["x²+C", "x³/3+C", "sin(x)+C", "e^x+C"]
        idx = random.randint(0, len(exprs)-1)
        return {'expr': exprs[idx], 'answer': integrals[idx]}
    
    def _generate_matrix_det(self):
        m11, m12, m21, m22 = [random.randint(1, 9) for _ in range(4)]
        det = m11 * m22 - m12 * m21
        return {'m11': m11, 'm12': m12, 'm21': m21, 'm22': m22, 'answer': str(det)}
    
    def _generate_dot_product(self):
        a, b = random.randint(1, 10), random.randint(1, 10)
        answer = str(a * b)
        return {'a': a, 'b': b, 'answer': answer}
    
    def _generate_prime_check(self):
        n = random.randint(2, 100)
        is_prime = self._is_prime(n)
        answer = "是" if is_prime else "否"
        return {'a': n, 'answer': answer}
    
    def _is_prime(self, n):
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True
    
    def _generate_factorization(self):
        n = random.randint(4, 100)
        factors = []
        temp = n
        for i in range(2, int(n**0.5) + 1):
            while temp % i == 0:
                factors.append(str(i))
                temp //= i
        if temp > 1:
            factors.append(str(temp))
        answer = "*".join(factors)
        return {'a': n, 'answer': answer}
    
    # 英语题目生成函数
    def _generate_vocab(self):
        words = [('beautiful', '美丽的'), ('important', '重要的'), ('knowledge', '知识'), 
                 ('computer', '计算机'), ('science', '科学'), ('education', '教育'),
                 ('mathematics', '数学'), ('programming', '编程'), ('algorithm', '算法')]
        word, meaning = random.choice(words)
        return {'word': word, 'answer': meaning}
    
    def _generate_antonym(self):
        words = [('happy', 'sad'), ('big', 'small'), ('fast', 'slow'), 
                 ('up', 'down'), ('hot', 'cold'), ('easy', 'difficult')]
        word, antonym = random.choice(words)
        return {'word': word, 'answer': antonym}
    
    def _generate_synonym(self):
        words = [('happy', 'glad'), ('big', 'large'), ('fast', 'quick'),
                 ('smart', 'clever'), ('beautiful', 'pretty'), ('important', 'essential')]
        word, synonym = random.choice(words)
        return {'word': word, 'answer': synonym}
    
    def _generate_part_of_speech(self):
        words = [('run', 'v.'), ('book', 'n.'), ('happy', 'adj.'),
                 ('quickly', 'adv.'), ('love', 'v.'), ('knowledge', 'n.')]
        word, pos = random.choice(words)
        return {'word': word, 'answer': pos}
    
    def _generate_verb_form(self):
        return {'answer': 'goes'}
    
    def _generate_adverb(self):
        return {'answer': 'already'}
    
    def _generate_relative_pronoun(self):
        return {'answer': 'which'}
    
    def _generate_subjunctive(self):
        return {'answer': 'were'}
    
    def _generate_reading_ref(self):
        return {'n': random.randint(1, 5), 'answer': '前文提到的事物'}
    
    def _generate_main_idea(self):
        return {'answer': '文章的主旨'}
    
    # 编程题目生成函数
    def _generate_print_code(self):
        texts = ['Hello World', 'Python', 'Code', 'Test', 'Hello']
        text = random.choice(texts)
        return {'text': text, 'answer': f"print('{text}')"}
    
    def _generate_add_code(self):
        a, b = random.randint(1, 100), random.randint(1, 100)
        return {'a': a, 'b': b, 'answer': f"{a} + {b}"}
    
    def _generate_list_len(self):
        lst = [random.randint(1, 10) for _ in range(random.randint(3, 8))]
        return {'lst': str(lst), 'answer': str(len(lst))}
    
    def _generate_for_loop(self):
        return {'answer': 'for item in list:'}
    
    def _generate_in_list(self):
        lst = [random.randint(1, 10) for _ in range(random.randint(3, 6))]
        a = random.choice(lst) if random.random() > 0.3 else random.randint(100, 200)
        answer = 'True' if a in lst else 'False'
        return {'a': a, 'lst': str(lst), 'answer': answer}
    
    def _generate_ds_complexity(self):
        ds_map = [('数组', 'O(1)访问/O(n)插入'), ('链表', 'O(n)访问/O(1)插入'),
                  ('栈', 'O(1)'), ('队列', 'O(1)'), ('哈希表', 'O(1)平均')]
        ds, complexity = random.choice(ds_map)
        return {'ds': ds, 'answer': complexity}
    
    def _generate_op_complexity(self):
        ops = ['插入', '删除', '查找', '遍历']
        ds_map = [('数组', 'O(n)'), ('链表', 'O(1)'), ('栈', 'O(1)'), ('队列', 'O(1)')]
        op = random.choice(ops)
        ds, complexity = random.choice(ds_map)
        return {'op': op, 'ds': ds, 'answer': complexity}
    
    def _generate_ds_scenario(self):
        scenarios = ['频繁插入删除', '随机访问', '先进先出', '后进先出']
        ds_map = [('链表', '适合'), ('数组', '适合'), ('队列', '适合'), ('栈', '适合')]
        scenario = random.choice(scenarios)
        ds, answer = random.choice(ds_map)
        return {'ds': ds, 'scenario': scenario, 'answer': answer}
    
    def _generate_algo_complexity(self):
        algos = [('冒泡排序', 'O(n²)'), ('快速排序', 'O(n log n)'),
                 ('二分查找', 'O(log n)'), ('线性查找', 'O(n)')]
        algo, complexity = random.choice(algos)
        return {'algo': algo, 'answer': complexity}
    
    def _generate_sort_case(self):
        n = random.randint(10, 100)
        answer = 'O(n log n)'
        return {'n': n, 'answer': answer}
    
    def _generate_stability(self):
        algos = [('冒泡排序', '是'), ('快速排序', '否'), ('归并排序', '是'), ('选择排序', '否')]
        algo, answer = random.choice(algos)
        return {'algo': algo, 'answer': answer}
    
    # 物理题目生成函数
    def _generate_newton(self):
        m = random.randint(1, 10)
        F = random.randint(10, 100)
        a = F // m
        return {'m': m, 'F': F, 'answer': f"{a} m/s²"}
    
    def _generate_free_fall(self):
        h = random.randint(10, 100)
        v = int((2 * 9.8 * h)**0.5)
        return {'h': h, 'answer': f"{v} m/s"}
    
    def _generate_collision(self):
        m1, m2 = random.randint(1, 10), random.randint(1, 10)
        return {'m1': m1, 'm2': m2, 'answer': '根据动量守恒计算'}
    
    def _generate_ohm(self):
        I = random.randint(1, 10)
        R = random.randint(1, 20)
        V = I * R
        return {'I': I, 'R': R, 'answer': f"{V}V"}
    
    def _generate_energy(self):
        Q = random.randint(1, 10)
        V = random.randint(1, 100)
        E = Q * V
        return {'Q': Q, 'V': V, 'answer': f"{E}J"}
    
    # 化学题目生成函数
    def _generate_atomic_number(self):
        elements = [('氢', '1'), ('碳', '6'), ('氧', '8'), ('铁', '26'), ('铜', '29')]
        element, num = random.choice(elements)
        return {'element': element, 'answer': num}
    
    def _generate_formula(self):
        compounds = [('水', 'H₂O'), ('二氧化碳', 'CO₂'), ('氯化钠', 'NaCl'), ('硫酸', 'H₂SO₄')]
        compound, formula = random.choice(compounds)
        return {'compound': compound, 'answer': formula}
    
    def _generate_neutralization(self):
        acids = ['盐酸', '硫酸', '硝酸']
        bases = ['氢氧化钠', '氢氧化钙']
        return {'acid': random.choice(acids), 'base': random.choice(bases), 'answer': '盐和水'}
    
    def _generate_organic_type(self):
        compounds = [('甲烷', '烷烃'), ('乙醇', '醇'), ('乙酸', '羧酸'), ('葡萄糖', '糖类')]
        compound, type_ = random.choice(compounds)
        return {'compound': compound, 'type': type_, 'answer': type_}
    
    # 语文题目生成函数
    def _generate_poem_author(self):
        poems = [('床前明月光', '李白'), ('春眠不觉晓', '孟浩然'), ('白日依山尽', '王之涣')]
        poem, author = random.choice(poems)
        return {'poem': poem, 'answer': author}
    
    def _generate_rhetoric(self):
        rhetorics = ['比喻', '拟人', '夸张', '排比']
        return {'answer': random.choice(rhetorics)}
    
    def _generate_classical_word(self):
        words = [('之', '的'), ('其', '他的'), ('而', '但是'), ('于', '在')]
        word, meaning = random.choice(words)
        return {'word': word, 'answer': meaning}
    
    def _generate_classical_translate(self):
        sentences = [('学而时习之', '学习并且时常复习'), ('三人行必有我师', '三个人同行一定有我的老师')]
        sentence, translation = random.choice(sentences)
        return {'sentence': sentence, 'answer': translation}
    
    def _generate_poem_emotion(self):
        emotions = ['思乡', '爱国', '惜春', '壮志豪情']
        poems = ['静夜思', '满江红', '春晓', '将进酒']
        return {'poem': random.choice(poems), 'answer': random.choice(emotions)}
    
    # 计算机题目生成函数
    def _generate_component_func(self):
        components = [('CPU', '中央处理器,执行指令'), ('内存', '临时存储数据'), 
                      ('硬盘', '永久存储数据'), ('显卡', '处理图形')]
        component, func = random.choice(components)
        return {'component': component, 'answer': func}
    
    def _generate_full_name(self):
        terms = [('CPU', 'Central Processing Unit'), ('RAM', 'Random Access Memory'),
                 ('ROM', 'Read Only Memory'), ('HTTP', 'HyperText Transfer Protocol')]
        term, full = random.choice(terms)
        return {'term': term, 'answer': full}
    
    def _generate_port(self):
        protocols = [('HTTP', '80'), ('HTTPS', '443'), ('FTP', '21'), ('SSH', '22')]
        protocol, port = random.choice(protocols)
        return {'protocol': protocol, 'port': port, 'answer': port}
    
    def _generate_osi_layer(self):
        layers = {1: '物理层', 2: '数据链路层', 3: '网络层', 4: '传输层', 
                  5: '会话层', 6: '表示层', 7: '应用层'}
        n = random.randint(1, 7)
        return {'n': n, 'answer': layers[n]}
    
    def _generate_ml_type(self):
        algos = [('决策树', '监督学习'), ('K-means', '无监督学习'), 
                 ('强化学习', '强化学习'), ('神经网络', '深度学习')]
        algo, type_ = random.choice(algos)
        return {'algo': algo, 'type': type_, 'answer': type_}
    
    def _generate_ai_concept(self):
        concepts = [('机器学习', '让计算机从数据中学习'), ('深度学习', '使用神经网络学习'),
                    ('自然语言处理', '处理和理解人类语言'), ('计算机视觉', '让计算机看懂图像')]
        concept, definition = random.choice(concepts)
        return {'concept': concept, 'answer': definition}
    
    def generate_single_question(self):
        """生成单个题目"""
        subject = random.choice(list(self.subjects.keys()))
        chapter = random.choice(self.subjects[subject])
        level = random.choice(self.education_levels)
        difficulty = random.choice(self.difficulty_map.get(level, ['基础', '提高', '拓展']))
        
        subject_templates = self.template_map.get(subject, {})
        chapter_templates = subject_templates.get(chapter, [])
        
        if not chapter_templates:
            return None
        
        template_info = random.choice(chapter_templates)
        template = template_info['template']
        func = template_info['func']
        
        try:
            params = func()
            params['level'] = level
            
            question_text = template.format(**params)
            correct_answer = params.get('answer', '未知')
            
            # 生成选项
            options = self._generate_options(correct_answer)
            
            return {
                'question_text': question_text,
                'question_type': 'multiple_choice',
                'options': options,
                'correct_answer': correct_answer,
                'explanation': self._generate_explanation(subject, chapter, correct_answer),
                'difficulty': difficulty,
                'category': subject,
                'points': self._calculate_points(difficulty)
            }
        except Exception as e:
            return None
    
    def _generate_options(self, correct_answer):
        """生成选项"""
        wrong_answers = {
            '5': ['3', '7', '10'],
            '11': ['14', '7', '24'],
            '13': ['10', '15', '8'],
            '8': ['4', '16', '2'],
            '1024': ['512', '2048', '256'],
            'len()': ['count()', 'length()', 'size()'],
            'went': ['goed', 'gone', 'going'],
            '队列': ['栈', '树', '图'],
            '标签数据': ['无标签数据', 'GPU', '大数据'],
            'def': ['function', 'func', 'define'],
            'print()': ['echo', 'printf', 'console.log'],
            '先进后出': ['先进先出', '随机访问', '双向访问'],
            'O(n log n)': ['O(n²)', 'O(n)', 'O(log n)'],
            '安培': ['伏特', '欧姆', '瓦特'],
            'H₂O': ['CO₂', 'NaCl', 'H₂SO₄'],
            '李白': ['杜甫', '白居易', '苏轼'],
            '80': ['21', '22', '443'],
            'inertia': ['momentum', 'force', 'energy'],
        }
        
        wrong = wrong_answers.get(correct_answer, [str(random.randint(1, 100)) for _ in range(3)])
        options = [correct_answer] + wrong[:3]
        random.shuffle(options)
        return options
    
    def _generate_explanation(self, subject, chapter, answer):
        """生成解析"""
        explanations = {
            '数学': f'{chapter}知识点:{answer}是正确答案',
            '英语': f'{chapter}知识点:{answer}是正确答案',
            '编程': f'{chapter}知识点:{answer}是正确答案',
            '物理': f'{chapter}知识点:{answer}是正确答案',
            '化学': f'{chapter}知识点:{answer}是正确答案',
            '语文': f'{chapter}知识点:{answer}是正确答案',
            '计算机': f'{chapter}知识点:{answer}是正确答案',
        }
        return explanations.get(subject, f'{chapter}知识点解析')
    
    def _calculate_points(self, difficulty):
        """计算分值"""
        points_map = {
            '入门': 5, '基础': 10, '提高': 15, '拓展': 20,
            '进阶': 25, '研究': 30, '省级': 20, '国家级': 25, '国际级': 30
        }
        return points_map.get(difficulty, 10)
    
    def generate_batch(self, count=1000):
        """批量生成题目"""
        questions = []
        for _ in range(count):
            q = self.generate_single_question()
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
                added += 1
            
            conn.commit()
        
        with self.lock:
            self.generated_count += added
        
        return added
    
    def generate_mass_questions(self, target_count=100000, batch_size=1000):
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
            
            if added == 0:
                print("⚠️  连续多次未添加新题目,可能已达到生成极限")
                break
        
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
    generator = MassQuestionGenerator()
    result = generator.generate_mass_questions(target_count=10000)
    logger.info("\n📊 结果:", result)
