import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import json
import random
import time
import math
import hashlib
import os

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

class InfiniteQuestionGenerator:
    """无限题目生成器 - 使用参数化方法生成海量题目"""
    
    def __init__(self):
        self.generated_count = 0
        self.duplicate_count = 0
        self.hash_set = set()
        self.rng_seed = random.randint(0, 1000000)
        
    def generate_unique_hash(self, question_text):
        """生成唯一哈希值"""
        return hashlib.md5(question_text.encode()).hexdigest()
    
    def is_unique(self, question_text):
        """检查题目是否唯一"""
        h = self.generate_unique_hash(question_text)
        if h in self.hash_set:
            return False
        self.hash_set.add(h)
        return True
    
    def generate_math_arithmetic(self):
        """生成数学算术题 - 参数化生成"""
        a = random.randint(1, 9999)
        b = random.randint(1, 9999)
        op = random.choice(['+', '-', '*', '/'])
        
        if op == '+':
            ans = a + b
        elif op == '-':
            if a < b:
                a, b = b, a
            ans = a - b
        elif op == '*':
            a = random.randint(1, 99)
            b = random.randint(1, 99)
            ans = a * b
        else:
            b = random.randint(1, 99)
            ans = random.randint(1, 99)
            a = ans * b
        
        q = f"数学 - 算术: 计算 {a} {op} {b} = ?"
        
        if not self.is_unique(q):
            return None
        
        options = [str(ans)]
        while len(options) < 4:
            wrong = ans + random.randint(-100, 100)
            if wrong != ans and str(wrong) not in options:
                options.append(str(wrong))
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': str(ans),
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_math_algebra(self):
        """生成数学代数题"""
        a = random.randint(1, 99)
        b = random.randint(1, 999)
        c = random.randint(b+1, b+999)
        ans = (c - b) // a
        
        q = f"数学 - 代数: 解方程 {a}x + {b} = {c},x = ?"
        
        if not self.is_unique(q):
            return None
        
        options = [str(ans), str(ans+1), str(ans-1), str(ans+2)]
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': str(ans),
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_math_geometry(self):
        """生成数学几何题"""
        shapes = ['正方形', '长方形', '圆形', '三角形', '正方体', '球体', '圆柱体']
        shape = random.choice(shapes)
        
        if shape == '正方形':
            a = random.randint(1, 999)
            ans = a * a
            q = f"数学 - 几何: 边长为{a}cm的{shape}面积是多少平方厘米?"
        elif shape == '长方形':
            a, b = random.randint(1, 999), random.randint(1, 999)
            ans = a * b
            q = f"数学 - 几何: 长{a}cm宽{b}cm的{shape}面积是多少平方厘米?"
        elif shape == '圆形':
            r = random.randint(1, 99)
            ans = int(math.pi * r * r)
            q = f"数学 - 几何: 半径为{r}cm的{shape}面积约是多少平方厘米?"
        elif shape == '三角形':
            a, h = random.randint(1, 999), random.randint(1, 999)
            ans = (a * h) // 2
            q = f"数学 - 几何: 底{a}cm高{h}cm的{shape}面积是多少平方厘米?"
        elif shape == '正方体':
            a = random.randint(1, 99)
            ans = a * a * a
            q = f"数学 - 几何: 棱长为{a}cm的{shape}体积是多少立方厘米?"
        elif shape == '球体':
            r = random.randint(1, 99)
            ans = int((4/3) * math.pi * r * r * r)
            q = f"数学 - 几何: 半径为{r}cm的{shape}体积约是多少立方厘米?"
        else:
            r, h = random.randint(1, 99), random.randint(1, 999)
            ans = int(math.pi * r * r * h)
            q = f"数学 - 几何: 半径{r}cm高{h}cm的{shape}体积约是多少立方厘米?"
        
        if not self.is_unique(q):
            return None
        
        options = [str(ans), str(ans + random.randint(-100, 100)), 
                   str(ans + random.randint(-100, 100)), str(ans + random.randint(-100, 100))]
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': str(ans),
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_math_probability(self):
        """生成数学概率题"""
        total = random.randint(2, 999)
        target = random.randint(1, total-1)
        ans = f"{target}/{total}"
        
        q = f"数学 - 概率: 从{total}个球中随机取一个,恰好取到目标球的概率是?"
        
        if not self.is_unique(q):
            return None
        
        options = [ans, f"{total-target}/{total}", f"1/{total}", f"{target+1}/{total}"]
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': ans,
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_math_function(self):
        """生成数学函数题"""
        a = random.randint(1, 99)
        b = random.randint(1, 999)
        x = random.randint(1, 99)
        ans = a * x + b
        
        q = f"数学 - 函数: 若 f(x) = {a}x + {b},则 f({x}) = ?"
        
        if not self.is_unique(q):
            return None
        
        options = [str(ans), str(ans+10), str(ans-10), str(ans+20)]
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': str(ans),
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_math_sequence(self):
        """生成数学数列题"""
        a1 = random.randint(1, 99)
        d = random.randint(1, 99)
        n = random.randint(2, 99)
        ans = a1 + (n - 1) * d
        
        q = f"数学 - 数列: 等差数列首项{a1},公差{d},第{n}项是?"
        
        if not self.is_unique(q):
            return None
        
        options = [str(ans), str(ans+d), str(ans-d), str(ans+2*d)]
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': str(ans),
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_math_trigonometry(self):
        """生成数学三角函数题"""
        angle = random.choice([0, 30, 45, 60, 90, 120, 135, 150, 180])
        func = random.choice(['sin', 'cos', 'tan'])
        
        values = {
            (0, 'sin'): '0', (30, 'sin'): '1/2', (45, 'sin'): '√2/2', 
            (60, 'sin'): '√3/2', (90, 'sin'): '1', (120, 'sin'): '√3/2',
            (135, 'sin'): '√2/2', (150, 'sin'): '1/2', (180, 'sin'): '0',
            (0, 'cos'): '1', (30, 'cos'): '√3/2', (45, 'cos'): '√2/2',
            (60, 'cos'): '1/2', (90, 'cos'): '0', (120, 'cos'): '-1/2',
            (135, 'cos'): '-√2/2', (150, 'cos'): '-√3/2', (180, 'cos'): '-1',
            (0, 'tan'): '0', (30, 'tan'): '√3/3', (45, 'tan'): '1',
            (60, 'tan'): '√3', (90, 'tan'): '不存在', (120, 'tan'): '-√3',
            (135, 'tan'): '-1', (150, 'tan'): '-√3/3', (180, 'tan'): '0',
        }
        
        ans = values.get((angle, func), '未知')
        q = f"数学 - 三角: {func}({angle}°) = ?"
        
        if not self.is_unique(q):
            return None
        
        options = [ans, random.choice(['0', '1', '1/2', '√2/2', '√3/2', '√3', '√3/3', '不存在', '-1', '-1/2']),
                   random.choice(['0', '1', '1/2', '√2/2', '√3/2', '√3', '√3/3', '不存在', '-1', '-1/2']),
                   random.choice(['0', '1', '1/2', '√2/2', '√3/2', '√3', '√3/3', '不存在', '-1', '-1/2'])]
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': ans,
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_math_matrix(self):
        """生成数学矩阵题"""
        a, b, c, d = [random.randint(1, 99) for _ in range(4)]
        ans = a * d - b * c
        
        q = f"数学 - 矩阵: 矩阵[[{a},{b}],[{c},{d}]]的行列式是?"
        
        if not self.is_unique(q):
            return None
        
        options = [str(ans), str(ans + random.randint(-1000, 1000)), 
                   str(ans + random.randint(-1000, 1000)), str(ans + random.randint(-1000, 1000))]
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': str(ans),
            'category': '数学',
            'difficulty': self._get_difficulty(),
            'points': 20
        }
    
    def generate_physics_mechanics(self):
        """生成物理力学题"""
        m = random.randint(1, 99)
        F = random.randint(10, 999)
        ans = F // m
        
        q = f"物理 - 力学: 质量{m}kg的物体受到{F}N的力,加速度是多少m/s²?"
        
        if not self.is_unique(q):
            return None
        
        options = [str(ans), str(ans+1), str(ans-1), str(ans+2)]
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': str(ans),
            'category': '物理',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_physics_electricity(self):
        """生成物理电磁题"""
        I = random.randint(1, 99)
        R = random.randint(1, 99)
        ans = I * R
        
        q = f"物理 - 电磁: {I}A电流通过{R}Ω电阻,电压是多少伏特?"
        
        if not self.is_unique(q):
            return None
        
        options = [str(ans), str(ans+10), str(ans-10), str(ans+20)]
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': str(ans),
            'category': '物理',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_physics_optics(self):
        """生成物理光学题"""
        phenomena = ['反射', '折射', '衍射', '干涉', '色散', '偏振']
        ans = random.choice(phenomena)
        wrong = [p for p in phenomena if p != ans]
        
        q = "物理 - 光学: 彩虹的形成主要是由于光的什么现象?"
        
        if not self.is_unique(q):
            return None
        
        options = [ans] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': '折射',
            'category': '物理',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_chemistry_elements(self):
        """生成化学元素题"""
        elements = [
            ('H', '氢', 1), ('He', '氦', 2), ('Li', '锂', 3), ('Be', '铍', 4), ('B', '硼', 5),
            ('C', '碳', 6), ('N', '氮', 7), ('O', '氧', 8), ('F', '氟', 9), ('Ne', '氖', 10),
            ('Na', '钠', 11), ('Mg', '镁', 12), ('Al', '铝', 13), ('Si', '硅', 14), ('P', '磷', 15),
            ('S', '硫', 16), ('Cl', '氯', 17), ('Ar', '氩', 18), ('K', '钾', 19), ('Ca', '钙', 20),
            ('Fe', '铁', 26), ('Cu', '铜', 29), ('Zn', '锌', 30), ('Ag', '银', 47), ('Au', '金', 79),
        ]
        
        symbol, name, num = random.choice(elements)
        q = f"化学 - 元素: 元素符号'{symbol}'对应的元素名称是?"
        
        if not self.is_unique(q):
            return None
        
        wrong = [e[1] for e in elements if e[1] != name]
        options = [name] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': name,
            'category': '化学',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_chemistry_reactions(self):
        """生成化学反应题"""
        reactions = [
            ('酸 + 碱', '盐 + 水'),
            ('金属 + 酸', '盐 + 氢气'),
            ('碳酸钙加热', '氧化钙 + 二氧化碳'),
            ('水电解', '氢气 + 氧气'),
            ('铁 + 氧气', '氧化铁'),
            ('碳 + 氧气', '二氧化碳'),
            ('甲烷燃烧', '二氧化碳 + 水'),
            ('氢氧化钠 + 盐酸', '氯化钠 + 水'),
        ]
        
        reactants, products = random.choice(reactions)
        q = f"化学 - 反应: '{reactants}'反应的主要产物是?"
        
        if not self.is_unique(q):
            return None
        
        wrong = [r[1] for r in reactions if r[1] != products]
        options = [products] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': products,
            'category': '化学',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_biology_cells(self):
        """生成生物细胞题"""
        organelles = [
            ('细胞膜', '控制物质进出'),
            ('细胞核', '储存遗传信息'),
            ('线粒体', '产生能量'),
            ('叶绿体', '光合作用'),
            ('核糖体', '合成蛋白质'),
            ('内质网', '蛋白质加工'),
            ('高尔基体', '物质运输'),
            ('溶酶体', '分解废物'),
        ]
        
        organelle, function = random.choice(organelles)
        q = f"生物 - 细胞: {organelle}的主要功能是?"
        
        if not self.is_unique(q):
            return None
        
        wrong = [o[1] for o in organelles if o[1] != function]
        options = [function] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': function,
            'category': '生物',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_biology_genetics(self):
        """生成生物遗传题"""
        traits = [
            ('AA', '显性纯合'),
            ('Aa', '杂合'),
            ('aa', '隐性纯合'),
            ('XY', '雄性'),
            ('XX', '雌性'),
        ]
        
        genotype, phenotype = random.choice(traits)
        q = f"生物 - 遗传: 基因型'{genotype}'表现为什么性状?"
        
        if not self.is_unique(q):
            return None
        
        wrong = [t[1] for t in traits if t[1] != phenotype]
        options = [phenotype] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': phenotype,
            'category': '生物',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_english_vocab(self):
        """生成英语词汇题"""
        words = [
            ('accomplish', '完成'), ('benefit', '利益'), ('challenge', '挑战'),
            ('demonstrate', '展示'), ('evaluate', '评估'), ('fundamental', '基本的'),
            ('guarantee', '保证'), ('hypothesis', '假设'), ('implement', '实施'),
            ('justify', '证明'), ('knowledge', '知识'), ('maintain', '维持'),
            ('negotiate', '谈判'), ('opportunity', '机会'), ('perspective', '观点'),
            ('questionnaire', '问卷'), ('recognize', '识别'), ('significant', '重要的'),
            ('technology', '技术'), ('understand', '理解'), ('visualize', '可视化'),
            ('worthwhile', '值得的'), ('yesterday', '昨天'), ('adventure', '冒险'),
        ]
        
        word, meaning = random.choice(words)
        q = f"英语 - 词汇: '{word}' 的中文意思是?"
        
        if not self.is_unique(q):
            return None
        
        wrong = [w[1] for w in words if w[1] != meaning]
        options = [meaning] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': meaning,
            'category': '英语',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_english_grammar(self):
        """生成英语语法题"""
        tenses = [
            ('一般现在时', 'He plays basketball every day.'),
            ('一般过去时', 'He played basketball yesterday.'),
            ('现在进行时', 'He is playing basketball now.'),
            ('现在完成时', 'He has played basketball for 5 years.'),
            ('一般将来时', 'He will play basketball tomorrow.'),
            ('过去进行时', 'He was playing basketball at 3 PM.'),
            ('过去完成时', 'He had played basketball before dinner.'),
            ('将来进行时', 'He will be playing basketball at this time tomorrow.'),
        ]
        
        tense, example = random.choice(tenses)
        q = f"英语 - 语法: '{example}' 使用的是什么时态?"
        
        if not self.is_unique(q):
            return None
        
        wrong = [t[0] for t in tenses if t[0] != tense]
        options = [tense] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': tense,
            'category': '英语',
            'difficulty': self._get_difficulty(),
            'points': 15
        }
    
    def generate_chinese_poetry(self):
        """生成语文诗词题"""
        poems = [
            ('床前明月光,疑是地上霜', '李白', '静夜思'),
            ('春眠不觉晓,处处闻啼鸟', '孟浩然', '春晓'),
            ('白日依山尽,黄河入海流', '王之涣', '登鹳雀楼'),
            ('两个黄鹂鸣翠柳,一行白鹭上青天', '杜甫', '绝句'),
            ('千山鸟飞绝,万径人踪灭', '柳宗元', '江雪'),
            ('锄禾日当午,汗滴禾下土', '李绅', '悯农'),
            ('飞流直下三千尺,疑是银河落九天', '李白', '望庐山瀑布'),
            ('举头望明月,低头思故乡', '李白', '静夜思'),
        ]
        
        line, author, title = random.choice(poems)
        q = f"语文 - 诗词: '{line}' 的作者是?"
        
        if not self.is_unique(q):
            return None
        
        wrong = ['杜甫', '白居易', '苏轼', '王维', '李商隐', '杜牧']
        options = [author] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': author,
            'category': '语文',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_chinese_idioms(self):
        """生成语文成语题"""
        idioms = [
            ('画蛇添足', '多此一举'), ('画龙点睛', '锦上添花'),
            ('对牛弹琴', '白费力气'), ('亡羊补牢', '为时未晚'),
            ('守株待兔', '墨守成规'), ('掩耳盗铃', '自欺欺人'),
            ('刻舟求剑', '拘泥固执'), ('拔苗助长', '急于求成'),
            ('杯弓蛇影', '疑神疑鬼'), ('滥竽充数', '混水摸鱼'),
            ('井底之蛙', '见识短浅'), ('狐假虎威', '仗势欺人'),
        ]
        
        idiom, meaning = random.choice(idioms)
        q = f"语文 - 成语: '{idiom}' 的寓意是?"
        
        if not self.is_unique(q):
            return None
        
        wrong = [i[1] for i in idioms if i[1] != meaning]
        options = [meaning] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': meaning,
            'category': '语文',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_history_chinese(self):
        """生成历史中国史题"""
        events = [
            ('夏朝', '中国历史上第一个朝代'),
            ('商朝', '青铜器发达'),
            ('周朝', '分封制'),
            ('秦朝', '第一个统一的封建王朝'),
            ('汉朝', '丝绸之路'),
            ('唐朝', '贞观之治'),
            ('宋朝', '四大发明'),
            ('元朝', '疆域最大'),
            ('明朝', '郑和下西洋'),
            ('清朝', '康乾盛世'),
        ]
        
        dynasty, description = random.choice(events)
        q = f"历史 - 中国史: {description}的朝代是?"
        
        if not self.is_unique(q):
            return None
        
        wrong = [e[0] for e in events if e[0] != dynasty]
        options = [dynasty] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': dynasty,
            'category': '历史',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_geography_climate(self):
        """生成地理气候题"""
        climates = [
            ('热带季风气候', '全年高温,分旱雨两季'),
            ('亚热带季风气候', '夏季高温多雨,冬季温和少雨'),
            ('温带季风气候', '夏季高温多雨,冬季寒冷干燥'),
            ('温带大陆性气候', '冬冷夏热,降水稀少'),
            ('高原山地气候', '气温低,气候垂直变化'),
            ('温带海洋性气候', '全年温和湿润'),
            ('地中海气候', '夏季炎热干燥,冬季温和多雨'),
            ('热带雨林气候', '全年高温多雨'),
        ]
        
        climate, description = random.choice(climates)
        q = f"地理 - 气候: {description}描述的是什么气候?"
        
        if not self.is_unique(q):
            return None
        
        wrong = [c[0] for c in climates if c[0] != climate]
        options = [climate] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': climate,
            'category': '地理',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_programming_python(self):
        """生成编程Python题"""
        concepts = [
            ('print()', '输出内容'),
            ('input()', '获取输入'),
            ('if', '条件判断'),
            ('for', '循环'),
            ('while', '循环'),
            ('def', '定义函数'),
            ('return', '返回值'),
            ('import', '导入模块'),
            ('class', '定义类'),
            ('self', '实例引用'),
        ]
        
        keyword, description = random.choice(concepts)
        q = f"编程 - Python: '{keyword}' 的作用是?"
        
        if not self.is_unique(q):
            return None
        
        wrong = [c[1] for c in concepts if c[1] != description]
        options = [description] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': description,
            'category': '编程',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_computer_network(self):
        """生成计算机网络题"""
        protocols = [
            ('HTTP', '超文本传输协议,默认端口80'),
            ('HTTPS', '安全超文本传输协议,默认端口443'),
            ('FTP', '文件传输协议,默认端口21'),
            ('SSH', '安全外壳协议,默认端口22'),
            ('TCP', '传输控制协议,面向连接'),
            ('UDP', '用户数据报协议,无连接'),
            ('DNS', '域名系统,解析域名'),
            ('IP', '互联网协议,寻址'),
        ]
        
        protocol, description = random.choice(protocols)
        q = f"计算机 - 网络: {description}描述的是什么协议?"
        
        if not self.is_unique(q):
            return None
        
        wrong = [p[0] for p in protocols if p[0] != protocol]
        options = [protocol] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': protocol,
            'category': '计算机',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def generate_japanese_vocab(self):
        """生成日语词汇题"""
        words = [
            ('猫', 'ねこ', '猫'), ('犬', 'いぬ', '狗'), ('本', 'ほん', '书'),
            ('水', 'みず', '水'), ('火', 'ひ', '火'), ('风', 'かぜ', '风'),
            ('山', 'やま', '山'), ('海', 'うみ', '海'), ('空', 'そら', '天空'),
            ('日', 'ひ', '太阳'), ('月', 'つき', '月亮'), ('星', 'ほし', '星星'),
            ('花', 'はな', '花'), ('木', 'き', '树'), ('草', 'くさ', '草'),
        ]
        
        kanji, hiragana, meaning = random.choice(words)
        q = f"日语 - 词汇: '{kanji} ({hiragana})' 的意思是?"
        
        if not self.is_unique(q):
            return None
        
        wrong = [w[2] for w in words if w[2] != meaning]
        options = [meaning] + random.sample(wrong, 3)
        random.shuffle(options)
        
        return {
            'question_text': q,
            'options': options,
            'correct_answer': meaning,
            'category': '日语',
            'difficulty': self._get_difficulty(),
            'points': 10
        }
    
    def _get_difficulty(self):
        """获取难度"""
        return random.choice(['入门', '基础', '提高', '拓展'])
    
    def generate_question(self):
        """生成单个题目"""
        generators = [
            self.generate_math_arithmetic,
            self.generate_math_algebra,
            self.generate_math_geometry,
            self.generate_math_probability,
            self.generate_math_function,
            self.generate_math_sequence,
            self.generate_math_trigonometry,
            self.generate_math_matrix,
            self.generate_physics_mechanics,
            self.generate_physics_electricity,
            self.generate_physics_optics,
            self.generate_chemistry_elements,
            self.generate_chemistry_reactions,
            self.generate_biology_cells,
            self.generate_biology_genetics,
            self.generate_english_vocab,
            self.generate_english_grammar,
            self.generate_chinese_poetry,
            self.generate_chinese_idioms,
            self.generate_history_chinese,
            self.generate_geography_climate,
            self.generate_programming_python,
            self.generate_computer_network,
            self.generate_japanese_vocab,
        ]
        
        attempts = 0
        while attempts < 10:
            generator = random.choice(generators)
            q = generator()
            if q:
                return q
            attempts += 1
        
        return None
    
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
                def execute_capability(**kwargs):
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
    
    def generate_mass_questions(self, target_count=100000, batch_size=1000):
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
            
            print(f"\r📊 生成进度: {self.generated_count}/{target_count} | 新增: {added} | 重复: {self.duplicate_count} | 速度: {rate:.2f}题/秒", end='')
        
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
    generator = InfiniteQuestionGenerator()
    result = generator.generate_mass_questions(target_count=50000)
    logger.info("\n📊 结果:", result)
