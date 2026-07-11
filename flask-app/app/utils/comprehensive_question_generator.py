import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import json
import random
import time
import math
import sys
import os

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

class ComprehensiveQuestionGenerator:
    """综合大规模题目生成器"""
    
    def __init__(self):
        self.generated_count = 0
        self.duplicate_count = 0
        self.subject_generators = {
            '数学': self.generate_math_question,
            '物理': self.generate_physics_question,
            '化学': self.generate_chemistry_question,
            '生物': self.generate_biology_question,
            '英语': self.generate_english_question,
            '语文': self.generate_chinese_question,
            '历史': self.generate_history_question,
            '地理': self.generate_geography_question,
            '政治': self.generate_politics_question,
            '编程': self.generate_programming_question,
            '计算机': self.generate_computer_question,
            '日语': self.generate_japanese_question,
        }
    
    def generate_math_question(self):
        """生成数学题目"""
        math_topics = [
            self._generate_arithmetic,
            self._generate_algebra,
            self._generate_geometry,
            self._generate_probability,
            self._generate_function,
            self._generate_sequence,
            self._generate_trigonometry,
            self._generate_matrix,
        ]
        return random.choice(math_topics)()
    
    def _generate_arithmetic(self):
        a, b = random.randint(1, 100), random.randint(1, 100)
        op = random.choice(['+', '-', '*', '/'])
        if op == '+':
            ans = a + b
        elif op == '-':
            a, b = max(a, b), min(a, b)
            ans = a - b
        elif op == '*':
            ans = a * b
        else:
            while b == 0 or a % b != 0:
                b = random.randint(1, 50)
            ans = a // b
        
        options = [str(ans), str(ans + random.randint(-10, 10)), str(ans + random.randint(-10, 10)), str(ans + random.randint(-10, 10))]
        options = list(set(options))
        while len(options) < 4:
            options.append(str(random.randint(1, 200)))
        random.shuffle(options)
        
        return {
            'question_text': f"数学 - 算术: 计算 {a} {op} {b} = ?",
            'options': options,
            'correct_answer': str(ans),
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_algebra(self):
        a, b, c = random.randint(1, 10), random.randint(1, 20), random.randint(21, 100)
        ans = (c - b) // a
        
        options = [str(ans), str(ans + random.randint(-5, 5)), str(ans + random.randint(-5, 5)), str(ans + random.randint(-5, 5))]
        random.shuffle(options)
        
        return {
            'question_text': f"数学 - 代数: 解方程 {a}x + {b} = {c},x = ?",
            'options': options,
            'correct_answer': str(ans),
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_geometry(self):
        shape = random.choice(['正方形', '长方形', '圆形', '三角形'])
        if shape == '正方形':
            a = random.randint(1, 20)
            ans = a * a
            q = f"数学 - 几何: 边长为{a}cm的{shape}面积是多少平方厘米?"
        elif shape == '长方形':
            a, b = random.randint(1, 20), random.randint(1, 20)
            ans = a * b
            q = f"数学 - 几何: 长{a}cm宽{b}cm的{shape}面积是多少平方厘米?"
        elif shape == '圆形':
            r = random.randint(1, 10)
            ans = int(math.pi * r * r)
            q = f"数学 - 几何: 半径为{r}cm的{shape}面积约是多少平方厘米?"
        else:
            a, h = random.randint(1, 20), random.randint(1, 20)
            ans = (a * h) // 2
            q = f"数学 - 几何: 底{a}cm高{h}cm的{shape}面积是多少平方厘米?"
        
        options = [str(ans), str(ans + random.randint(-10, 10)), str(ans + random.randint(-10, 10)), str(ans + random.randint(-10, 10))]
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': str(ans),
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_probability(self):
        total, target = random.randint(2, 20), random.randint(1, 19)
        ans = f"{target}/{total}"
        
        options = [ans, f"{total-target}/{total}", f"1/{total}", f"{target+1}/{total}"]
        random.shuffle(options)
        
        return {
            'question_text': f"数学 - 概率: 从{total}个球中随机取一个,恰好取到目标球的概率是?",
            'options': options,
            'correct_answer': ans,
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_function(self):
        a, b, x = random.randint(1, 10), random.randint(1, 10), random.randint(1, 10)
        ans = a * x + b
        
        options = [str(ans), str(ans + random.randint(-10, 10)), str(ans + random.randint(-10, 10)), str(ans + random.randint(-10, 10))]
        random.shuffle(options)
        
        return {
            'question_text': f"数学 - 函数: 若 f(x) = {a}x + {b},则 f({x}) = ?",
            'options': options,
            'correct_answer': str(ans),
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_sequence(self):
        a1, d, n = random.randint(1, 10), random.randint(1, 5), random.randint(5, 15)
        ans = a1 + (n - 1) * d
        
        options = [str(ans), str(ans + random.randint(-10, 10)), str(ans + random.randint(-10, 10)), str(ans + random.randint(-10, 10))]
        random.shuffle(options)
        
        return {
            'question_text': f"数学 - 数列: 等差数列首项{a1},公差{d},第{n}项是?",
            'options': options,
            'correct_answer': str(ans),
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_trigonometry(self):
        angle = random.choice([0, 30, 45, 60, 90])
        func = random.choice(['sin', 'cos', 'tan'])
        values = {
            (0, 'sin'): '0', (30, 'sin'): '1/2', (45, 'sin'): '√2/2', (60, 'sin'): '√3/2', (90, 'sin'): '1',
            (0, 'cos'): '1', (30, 'cos'): '√3/2', (45, 'cos'): '√2/2', (60, 'cos'): '1/2', (90, 'cos'): '0',
            (0, 'tan'): '0', (30, 'tan'): '√3/3', (45, 'tan'): '1', (60, 'tan'): '√3', (90, 'tan'): '不存在'
        }
        ans = values[(angle, func)]
        
        options = [ans, random.choice(['0', '1', '1/2', '√2/2', '√3/2', '√3', '√3/3', '不存在']),
                   random.choice(['0', '1', '1/2', '√2/2', '√3/2', '√3', '√3/3', '不存在']),
                   random.choice(['0', '1', '1/2', '√2/2', '√3/2', '√3', '√3/3', '不存在'])]
        random.shuffle(options)
        
        return {
            'question_text': f"数学 - 三角: {func}({angle}°) = ?",
            'options': options,
            'correct_answer': ans,
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_matrix(self):
        a, b, c, d = [random.randint(1, 9) for _ in range(4)]
        ans = a * d - b * c
        
        options = [str(ans), str(ans + random.randint(-20, 20)), str(ans + random.randint(-20, 20)), str(ans + random.randint(-20, 20))]
        random.shuffle(options)
        
        return {
            'question_text': f"数学 - 矩阵: 矩阵[[{a},{b}],[{c},{d}]]的行列式是?",
            'options': options,
            'correct_answer': str(ans),
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 20
        }
    
    def generate_physics_question(self):
        """生成物理题目"""
        physics_topics = [
            self._generate_mechanics,
            self._generate_electricity,
            self._generate_thermodynamics,
            self._generate_optics,
        ]
        return random.choice(physics_topics)()
    
    def _generate_mechanics(self):
        m, F = random.randint(1, 10), random.randint(10, 100)
        ans = F // m
        
        options = [str(ans), str(ans + random.randint(-5, 5)), str(ans + random.randint(-5, 5)), str(ans + random.randint(-5, 5))]
        random.shuffle(options)
        
        return {
            'question_text': f"物理 - 力学: 质量{m}kg的物体受到{F}N的力,加速度是多少m/s²?",
            'options': options,
            'correct_answer': str(ans),
            'category': '物理',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_electricity(self):
        I, R = random.randint(1, 10), random.randint(1, 20)
        ans = I * R
        
        options = [str(ans), str(ans + random.randint(-10, 10)), str(ans + random.randint(-10, 10)), str(ans + random.randint(-10, 10))]
        random.shuffle(options)
        
        return {
            'question_text': f"物理 - 电磁: {I}A电流通过{R}Ω电阻,电压是多少伏特?",
            'options': options,
            'correct_answer': str(ans),
            'category': '物理',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_thermodynamics(self):
        options = ['做功', '热传递', '辐射', '传导']
        ans = random.choice(options)
        wrong = [o for o in options if o != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "物理 - 热学: 改变物体内能的方式不包括以下哪一项?",
            'options': options,
            'correct_answer': ans,
            'category': '物理',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_optics(self):
        options = ['反射', '折射', '衍射', '干涉']
        ans = random.choice(options)
        wrong = [o for o in options if o != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "物理 - 光学: 彩虹的形成主要是由于光的什么现象?",
            'options': options,
            'correct_answer': ans,
            'category': '物理',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_chemistry_question(self):
        """生成化学题目"""
        chemistry_topics = [
            self._generate_inorganic,
            self._generate_organic,
            self._generate_reactions,
            self._generate_periodic,
        ]
        return random.choice(chemistry_topics)()
    
    def _generate_inorganic(self):
        elements = [('H', '氢'), ('O', '氧'), ('C', '碳'), ('N', '氮'), ('Na', '钠'), ('Cl', '氯')]
        symbol, name = random.choice(elements)
        wrong = [n for _, n in elements if n != name]
        
        options = [name] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': f"化学 - 无机: 元素符号'{symbol}'对应的元素名称是?",
            'options': options,
            'correct_answer': name,
            'category': '化学',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_organic(self):
        compounds = [('CH4', '甲烷'), ('C2H6', '乙烷'), ('C2H4', '乙烯'), ('C2H2', '乙炔')]
        formula, name = random.choice(compounds)
        wrong = [n for _, n in compounds if n != name]
        
        options = [name] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': f"化学 - 有机: 分子式'{formula}'对应的化合物名称是?",
            'options': options,
            'correct_answer': name,
            'category': '化学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_reactions(self):
        reactions = [
            ('酸+碱', '盐+水'),
            ('金属+酸', '盐+氢气'),
            ('燃烧', '氧化物'),
            ('置换反应', '新盐+新金属'),
        ]
        reactants, products = random.choice(reactions)
        wrong = [p for _, p in reactions if p != products]
        
        options = [products] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': f"化学 - 反应: '{reactants}'反应的主要产物是?",
            'options': options,
            'correct_answer': products,
            'category': '化学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_periodic(self):
        periods = ['第一周期', '第二周期', '第三周期', '第四周期']
        ans = random.choice(periods)
        wrong = [p for p in periods if p != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "化学 - 周期表: 钠元素位于元素周期表的第几周期?",
            'options': options,
            'correct_answer': '第三周期',
            'category': '化学',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_biology_question(self):
        """生成生物题目"""
        biology_topics = [
            self._generate_cell,
            self._generate_genetics,
            self._generate_ecology,
            self._generate_physiology,
        ]
        return random.choice(biology_topics)()
    
    def _generate_cell(self):
        organelles = ['细胞膜', '细胞核', '线粒体', '叶绿体', '核糖体']
        ans = random.choice(organelles)
        wrong = [o for o in organelles if o != ans]
        
        options = [ans] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': "生物 - 细胞: 细胞中控制遗传信息的结构是?",
            'options': options,
            'correct_answer': '细胞核',
            'category': '生物',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_genetics(self):
        options = ['DNA', 'RNA', '蛋白质', '糖类']
        ans = random.choice(options)
        wrong = [o for o in options if o != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "生物 - 遗传: 携带遗传信息的主要物质是?",
            'options': options,
            'correct_answer': 'DNA',
            'category': '生物',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_ecology(self):
        levels = ['个体', '种群', '群落', '生态系统']
        ans = random.choice(levels)
        wrong = [l for l in levels if l != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "生物 - 生态: 一定区域内所有生物的总和称为?",
            'options': options,
            'correct_answer': '群落',
            'category': '生物',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_physiology(self):
        systems = ['消化系统', '呼吸系统', '循环系统', '神经系统']
        ans = random.choice(systems)
        wrong = [s for s in systems if s != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "生物 - 生理: 负责运输氧气和营养物质的系统是?",
            'options': options,
            'correct_answer': '循环系统',
            'category': '生物',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_english_question(self):
        """生成英语题目"""
        english_topics = [
            self._generate_vocab,
            self._generate_grammar,
            self._generate_phrases,
            self._generate_idioms,
        ]
        return random.choice(english_topics)()
    
    def _generate_vocab(self):
        words = [('beautiful', '美丽的'), ('important', '重要的'), ('knowledge', '知识'), ('computer', '计算机')]
        word, meaning = random.choice(words)
        wrong = [m for _, m in words if m != meaning]
        
        options = [meaning] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': f"英语 - 词汇: '{word}' 的中文意思是?",
            'options': options,
            'correct_answer': meaning,
            'category': '英语',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_grammar(self):
        tenses = ['一般现在时', '一般过去时', '现在进行时', '现在完成时']
        ans = random.choice(tenses)
        wrong = [t for t in tenses if t != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "英语 - 语法: 'He has finished his homework.' 使用的是什么时态?",
            'options': options,
            'correct_answer': '现在完成时',
            'category': '英语',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_phrases(self):
        phrases = [
            ('look forward to', '期待'),
            ('take care of', '照顾'),
            ('make sense', '有意义'),
            ('give up', '放弃'),
        ]
        phrase, meaning = random.choice(phrases)
        wrong = [m for _, m in phrases if m != meaning]
        
        options = [meaning] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': f"英语 - 短语: '{phrase}' 的意思是?",
            'options': options,
            'correct_answer': meaning,
            'category': '英语',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_idioms(self):
        idioms = [
            ('break a leg', '祝你好运'),
            ('piece of cake', '小菜一碟'),
            ('under the weather', '身体不适'),
            ('hit the books', '用功学习'),
        ]
        idiom, meaning = random.choice(idioms)
        wrong = [m for _, m in idioms if m != meaning]
        
        options = [meaning] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': f"英语 - 习语: '{idiom}' 的意思是?",
            'options': options,
            'correct_answer': meaning,
            'category': '英语',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_chinese_question(self):
        """生成语文题目"""
        chinese_topics = [
            self._generate_poetry,
            self._generate_classical,
            self._generate_rhetoric,
            self._generate_idioms_chinese,
        ]
        return random.choice(chinese_topics)()
    
    def _generate_poetry(self):
        poems = [
            ('床前明月光', '李白'),
            ('春眠不觉晓', '孟浩然'),
            ('白日依山尽', '王之涣'),
            ('举头望明月', '李白'),
        ]
        line, author = random.choice(poems)
        wrong = [a for _, a in poems if a != author]
        
        options = [author] + wrong[:3]
        while len(options) < 4:
            options.append(random.choice(['杜甫', '白居易', '苏轼', '王维', '李商隐']))
        random.shuffle(options)
        
        return {
            'question_text': f"语文 - 诗词: '{line}' 的作者是?",
            'options': options,
            'correct_answer': author,
            'category': '语文',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_classical(self):
        words = [('之', '的'), ('其', '他的'), ('而', '但是'), ('于', '在')]
        word, meaning = random.choice(words)
        wrong = [m for _, m in words if m != meaning]
        
        options = [meaning] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': f"语文 - 文言: '之' 在文言文中通常表示?",
            'options': options,
            'correct_answer': '的',
            'category': '语文',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_rhetoric(self):
        devices = ['比喻', '拟人', '夸张', '排比']
        ans = random.choice(devices)
        wrong = [d for d in devices if d != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "语文 - 修辞: '飞流直下三千尺' 使用了什么修辞手法?",
            'options': options,
            'correct_answer': '夸张',
            'category': '语文',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_idioms_chinese(self):
        idioms = [
            ('画蛇添足', '多此一举'),
            ('画龙点睛', '锦上添花'),
            ('对牛弹琴', '白费力气'),
            ('亡羊补牢', '为时未晚'),
        ]
        idiom, meaning = random.choice(idioms)
        wrong = [m for _, m in idioms if m != meaning]
        
        options = [meaning] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': f"语文 - 成语: '{idiom}' 的寓意是?",
            'options': options,
            'correct_answer': meaning,
            'category': '语文',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_history_question(self):
        """生成历史题目"""
        history_topics = [
            self._generate_chinese_history,
            self._generate_world_history,
            self._generate_ancient_history,
            self._generate_modern_history,
        ]
        return random.choice(history_topics)()
    
    def _generate_chinese_history(self):
        dynasties = ['夏朝', '商朝', '周朝', '秦朝']
        ans = random.choice(dynasties)
        wrong = [d for d in dynasties if d != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "历史 - 中国史: 中国历史上第一个统一的封建王朝是?",
            'options': options,
            'correct_answer': '秦朝',
            'category': '历史',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_world_history(self):
        events = ['工业革命', '法国大革命', '美国独立战争', '第一次世界大战']
        ans = random.choice(events)
        wrong = [e for e in events if e != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "历史 - 世界史: 标志着现代世界开端的事件是?",
            'options': options,
            'correct_answer': '工业革命',
            'category': '历史',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_ancient_history(self):
        civilizations = ['古埃及', '古希腊', '古罗马', '古印度']
        ans = random.choice(civilizations)
        wrong = [c for c in civilizations if c != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "历史 - 古代史: 金字塔是哪个文明的建筑?",
            'options': options,
            'correct_answer': '古埃及',
            'category': '历史',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_modern_history(self):
        figures = ['孙中山', '毛泽东', '邓小平', '周恩来']
        ans = random.choice(figures)
        wrong = [f for f in figures if f != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "历史 - 现代史: 领导中国改革开放的领导人是?",
            'options': options,
            'correct_answer': '邓小平',
            'category': '历史',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_geography_question(self):
        """生成地理题目"""
        geography_topics = [
            self._generate_physical_geo,
            self._generate_human_geo,
            self._generate_climate,
            self._generate_continents,
        ]
        return random.choice(geography_topics)()
    
    def _generate_physical_geo(self):
        landforms = ['山脉', '平原', '高原', '盆地']
        ans = random.choice(landforms)
        wrong = [l for l in landforms if l != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "地理 - 地形: 青藏高原属于什么地形类型?",
            'options': options,
            'correct_answer': '高原',
            'category': '地理',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_human_geo(self):
        industries = ['农业', '工业', '服务业', '高新技术产业']
        ans = random.choice(industries)
        wrong = [i for i in industries if i != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "地理 - 人文: 第三产业通常指的是?",
            'options': options,
            'correct_answer': '服务业',
            'category': '地理',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_climate(self):
        climates = ['热带季风气候', '亚热带季风气候', '温带季风气候', '温带大陆性气候']
        ans = random.choice(climates)
        wrong = [c for c in climates if c != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "地理 - 气候: 中国东部主要是什么气候类型?",
            'options': options,
            'correct_answer': '亚热带季风气候',
            'category': '地理',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_continents(self):
        continents = ['亚洲', '欧洲', '非洲', '美洲']
        ans = random.choice(continents)
        wrong = [c for c in continents if c != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "地理 - 大洲: 世界上面积最大的大洲是?",
            'options': options,
            'correct_answer': '亚洲',
            'category': '地理',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_politics_question(self):
        """生成政治题目"""
        politics_topics = [
            self._generate_philosophy,
            self._generate_economics,
            self._generate_politics,
            self._generate_law,
        ]
        return random.choice(politics_topics)()
    
    def _generate_philosophy(self):
        concepts = ['实践', '真理', '矛盾', '发展']
        ans = random.choice(concepts)
        wrong = [c for c in concepts if c != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "政治 - 哲学: 检验真理的唯一标准是?",
            'options': options,
            'correct_answer': '实践',
            'category': '政治',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_economics(self):
        concepts = ['供给', '需求', '价格', '市场']
        ans = random.choice(concepts)
        wrong = [c for c in concepts if c != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "政治 - 经济: 决定商品价格的主要因素是?",
            'options': options,
            'correct_answer': '需求',
            'category': '政治',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_politics(self):
        systems = ['社会主义', '资本主义', '共产主义', '封建主义']
        ans = random.choice(systems)
        wrong = [s for s in systems if s != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "政治 - 制度: 中国实行的社会制度是?",
            'options': options,
            'correct_answer': '社会主义',
            'category': '政治',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_law(self):
        rights = ['生命权', '财产权', '选举权', '受教育权']
        ans = random.choice(rights)
        wrong = [r for r in rights if r != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "政治 - 法律: 公民的基本权利不包括以下哪一项?",
            'options': options,
            'correct_answer': ans,
            'category': '政治',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_programming_question(self):
        """生成编程题目"""
        programming_topics = [
            self._generate_python,
            self._generate_data_structures,
            self._generate_algorithms,
            self._generate_web,
        ]
        return random.choice(programming_topics)()
    
    def _generate_python(self):
        concepts = ['变量', '函数', '循环', '条件']
        ans = random.choice(concepts)
        wrong = [c for c in concepts if c != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "编程 - Python: 用于重复执行代码的结构是?",
            'options': options,
            'correct_answer': '循环',
            'category': '编程',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_data_structures(self):
        structures = ['数组', '链表', '栈', '队列']
        ans = random.choice(structures)
        wrong = [s for s in structures if s != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "编程 - 数据结构: 先进后出的数据结构是?",
            'options': options,
            'correct_answer': '栈',
            'category': '编程',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_algorithms(self):
        algorithms = ['排序', '查找', '递归', '动态规划']
        ans = random.choice(algorithms)
        wrong = [a for a in algorithms if a != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "编程 - 算法: 二分查找的时间复杂度是?",
            'options': options,
            'correct_answer': '查找',
            'category': '编程',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_web(self):
        technologies = ['HTML', 'CSS', 'JavaScript', 'Python']
        ans = random.choice(technologies)
        wrong = [t for t in technologies if t != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "编程 - Web: 用于网页样式设计的技术是?",
            'options': options,
            'correct_answer': 'CSS',
            'category': '编程',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_computer_question(self):
        """生成计算机题目"""
        computer_topics = [
            self._generate_hardware,
            self._generate_software,
            self._generate_network,
            self._generate_ai,
        ]
        return random.choice(computer_topics)()
    
    def _generate_hardware(self):
        components = ['CPU', '内存', '硬盘', '显卡']
        ans = random.choice(components)
        wrong = [c for c in components if c != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "计算机 - 硬件: 负责执行程序指令的部件是?",
            'options': options,
            'correct_answer': 'CPU',
            'category': '计算机',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_software(self):
        types = ['操作系统', '应用软件', '编程语言', '数据库']
        ans = random.choice(types)
        wrong = [t for t in types if t != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "计算机 - 软件: Windows 属于什么类型的软件?",
            'options': options,
            'correct_answer': '操作系统',
            'category': '计算机',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_network(self):
        protocols = ['HTTP', 'HTTPS', 'FTP', 'TCP']
        ans = random.choice(protocols)
        wrong = [p for p in protocols if p != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "计算机 - 网络: 用于安全传输数据的协议是?",
            'options': options,
            'correct_answer': 'HTTPS',
            'category': '计算机',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_ai(self):
        concepts = ['机器学习', '深度学习', '神经网络', '人工智能']
        ans = random.choice(concepts)
        wrong = [c for c in concepts if c != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "计算机 - AI: 使用神经网络进行学习的方法是?",
            'options': options,
            'correct_answer': '深度学习',
            'category': '计算机',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_japanese_question(self):
        """生成日语题目"""
        japanese_topics = [
            self._generate_japanese_vocab,
            self._generate_japanese_grammar,
            self._generate_japanese_culture,
        ]
        return random.choice(japanese_topics)()
    
    def _generate_japanese_vocab(self):
        words = [('猫', 'ねこ', '猫'), ('犬', 'いぬ', '狗'), ('本', 'ほん', '书'), ('水', 'みず', '水')]
        kanji, hiragana, meaning = random.choice(words)
        wrong = [m for _, _, m in words if m != meaning]
        
        options = [meaning] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': f"日语 - 词汇: '{kanji} ({hiragana})' 的意思是?",
            'options': options,
            'correct_answer': meaning,
            'category': '日语',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _generate_japanese_grammar(self):
        forms = ['ます形', 'て形', 'た形', 'ない形']
        ans = random.choice(forms)
        wrong = [f for f in forms if f != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "日语 - 文法: '食べる' 的否定形式是?",
            'options': options,
            'correct_answer': 'ない形',
            'category': '日语',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def _generate_japanese_culture(self):
        cultures = ['茶道', '和服', '寿司', '能剧']
        ans = random.choice(cultures)
        wrong = [c for c in cultures if c != ans]
        
        options = [ans] + wrong
        random.shuffle(options)
        
        return {
            'question_text': "日语 - 文化: 日本的传统服饰是?",
            'options': options,
            'correct_answer': '和服',
            'category': '日语',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _get_difficulty(self):
        """获取难度"""
        return random.choice(['入门', '基础', '提高', '拓展'])
    
    def generate_question(self):
        """生成单个题目"""
        subject = random.choice(list(self.subject_generators.keys()))
        return self.subject_generators[subject]()
    
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
                def handle_request(**kwargs):
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
    
    def generate_mass_questions(self, target_count=100000, batch_size=10000):
        """大规模生成题目"""
        print(f"🚀 开始生成 {target_count} 道题目...")
        start_time = time.time()
        
        while self.generated_count < target_count:
            remaining = target_count - self.generated_count
            current_batch = min(batch_size, remaining)
            
            questions = self.generate_batch(current_batch)
            added = self.save_to_database(questions)
            
            elapsed = time.time() - start_time
            rate = self.generated_count / elapsed if elapsed > 0 else 0
            remaining_time = (target_count - self.generated_count) / rate if rate > 0 else 0
            
            print(f"\r📊 生成进度: {self.generated_count}/{target_count} | 新增: {added} | 重复: {self.duplicate_count} | 速度: {rate:.2f}题/秒", end='')
            
            if added == 0:
                break
        
        elapsed_total = time.time() - start_time
        print(f"\n\n🎉 生成完成!")
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
    generator = ComprehensiveQuestionGenerator()
    result = generator.generate_mass_questions(target_count=100000)
    logger.info("\n📊 结果:", result)
