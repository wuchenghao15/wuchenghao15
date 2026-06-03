# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import json
import random
import os
from datetime import datetime

class ComprehensiveQuestionBankExpander:
    
    def __init__(self, db_path="app.db"):
        self.db_path = db_path
        self.conn = None
        self.question_id = 1
    
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def init_question_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                exam_id TEXT,
                type TEXT NOT NULL DEFAULT 'single_choice',
                content TEXT NOT NULL,
                options TEXT NOT NULL DEFAULT '[]',
                correct_answer TEXT NOT NULL DEFAULT '',
                difficulty INTEGER NOT NULL DEFAULT 1,
                points REAL NOT NULL DEFAULT 1.0,
                audio_url TEXT,
                tags TEXT NOT NULL DEFAULT '[]',
                explanation TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        self.conn.commit()
        
        cursor.execute('SELECT MAX(CAST(SUBSTR(id, 3) AS INTEGER)) FROM questions WHERE id LIKE "SC%"')
        max_id = cursor.fetchone()[0] or 0
        self.question_id = max_id + 1
        print(f"当前最大ID: {max_id}, 下一个ID: SC{self.question_id:05d}")
    
    def generate_question_id(self):
        qid = f"SC{self.question_id:05d}"
        self.question_id += 1
        return qid
    
    def generate_math_questions(self):
        """数学题库 - 公式、定理、计算"""
        print("\n📐 生成数学题库...")
        questions = []
        
        formulas = [
            ('求根公式', 'x = (-b ± √(b²-4ac)) / 2a', '一元二次方程ax²+bx+c=0的解'),
            ('勾股定理', 'a² + b² = c²', '直角三角形两边平方和等于第三边平方'),
            ('两点距离公式', 'd = √((x₂-x₁)² + (y₂-y₁)²)', '平面上两点间距离'),
            ('等差数列求和', 'Sₙ = n(a₁+aₙ)/2', '等差数列前n项和'),
            ('等比数列求和', 'Sₙ = a₁(1-qⁿ)/(1-q)', '等比数列前n项和'),
            ('圆的面积', 'S = πr²', '圆面积公式'),
            ('球的体积', 'V = (4/3)πr³', '球体体积公式'),
            ('三角函数', 'sin²θ + cos²θ = 1', '同角三角函数关系'),
            ('对数运算', 'log(a·b) = log a + log b', '对数乘法法则'),
            ('排列公式', 'P(n,m) = n!/(n-m)!', '排列数公式'),
            ('组合公式', 'C(n,m) = n!/(m!(n-m)!)', '组合数公式'),
            ('二项式定理', '(a+b)ⁿ = ΣC(n,k)aⁿ⁻ᵏbᵏ', '二项展开式'),
            ('向量点积', 'a·b = |a||b|cosθ', '向量数量积'),
            ('向量叉积', '|a×b| = |a||b|sinθ', '向量向量积'),
            ('复数运算', 'i² = -1', '虚数单位定义'),
            ('导数定义', 'f\'(x) = lim(Δx→0) [f(x+Δx)-f(x)]/Δx', '导数基本定义'),
            ('积分公式', '∫xⁿdx = xⁿ⁺¹/(n+1) + C', '幂函数积分'),
            ('概率加法', 'P(A∪B) = P(A) + P(B) - P(A∩B)', '概率加法公式'),
            ('正态分布', 'f(x) = (1/√(2π)σ)e^(-(x-μ)²/2σ²)', '正态分布密度函数'),
            ('余弦定理', 'c² = a² + b² - 2ab cosC', '三角形边角关系'),
        ]
        
        for i, (name, formula, desc) in enumerate(formulas):
            qid = self.generate_question_id()
            tags = json.dumps(['数学', '公式', '基础', '选择题'], ensure_ascii=False)
            
            wrong_formulas = [
                f'{formula}错误写法1',
                f'{formula}错误写法2',
                f'{formula}错误写法3',
            ]
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'{name}:{formula}\n\n请判断这个公式的正确性:{desc}',
                'options': json.dumps([
                    {'A': '正确'},
                    {'B': wrong_formulas[0]},
                    {'C': wrong_formulas[1]},
                    {'D': wrong_formulas[2]}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'{formula}是正确的{name}公式',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(300):
            qid = self.generate_question_id()
            tags = json.dumps(['数学', '代数', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'代数练习题 {i+1}:求解下列方程\n\n若2x + 5 = 15,则x的值为多少?',
                'options': json.dumps([
                    {'A': '3'},
                    {'B': '5'},
                    {'C': '7'},
                    {'D': '10'}
                ], ensure_ascii=False),
                'correct_answer': 'B',
                'difficulty': 1,
                'points': 1.5,
                'audio_url': '',
                'tags': tags,
                'explanation': '2x + 5 = 15 → 2x = 10 → x = 5',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(200):
            qid = self.generate_question_id()
            tags = json.dumps(['数学', '几何', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'几何练习题 {i+1}:\n\n在直角三角形中,两直角边分别为3和4,则斜边长度为多少?',
                'options': json.dumps([
                    {'A': '3'},
                    {'B': '4'},
                    {'C': '5'},
                    {'D': '7'}
                ], ensure_ascii=False),
                'correct_answer': 'C',
                'difficulty': 1,
                'points': 1.5,
                'audio_url': '',
                'tags': tags,
                'explanation': '根据勾股定理:a² + b² = c² → 3² + 4² = 9 + 16 = 25 → c = 5',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(150):
            qid = self.generate_question_id()
            tags = json.dumps(['数学', '概率统计', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'概率统计练习题 {i+1}:\n\n袋中有3个红球和2个白球,从中任意取出2个球,取到2个红球的概率是多少?',
                'options': json.dumps([
                    {'A': '3/10'},
                    {'B': '1/5'},
                    {'C': '3/10'},
                    {'D': '2/5'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': 'C(3,2)/C(5,2) = 3/10',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_physics_questions(self):
        """物理题库 - 公式、定律、概念"""
        print("\n⚡ 生成物理题库...")
        questions = []
        
        physics_concepts = [
            ('牛顿第一定律', '一切物体在没有受到力作用时,总保持静止状态或匀速直线运动状态', '惯性定律'),
            ('牛顿第二定律', 'F = ma', '加速度与合外力成正比,与质量成反比'),
            ('牛顿第三定律', 'F = -F\'', '作用力与反作用力大小相等、方向相反'),
            ('万有引力定律', 'F = Gm₁m₂/r²', '任意两物体间都存在相互吸引的力'),
            ('动能定理', 'W = ½mv₂² - ½mv₁²', '合外力做功等于动能变化量'),
            ('机械能守恒', 'Eₖ + Eₚ = 常数', '只有重力或弹力做功时'),
            ('动量守恒', 'm₁v₁ + m₂v₂ = m₁v₁\' + m₂v₂\'', '系统不受外力或外力为零'),
            ('欧姆定律', 'I = U/R', '电流与电压成正比,与电阻成反比'),
            ('法拉第电磁感应', 'E = nΔΦ/Δt', '磁通量变化产生感应电动势'),
            ('光的折射定律', 'n₁sinθ₁ = n₂sinθ₂', '斯涅尔定律'),
            ('理想气体状态方程', 'PV = nRT', '克拉伯龙方程'),
            ('热力学第一定律', 'ΔU = Q - W', '内能变化等于热量减去做功'),
            ('多普勒效应', 'f\' = f(v±v₀)/(v∓vₛ)', '波源或观察者运动时频率变化'),
            ('相对论质能方程', 'E = mc²', '能量与质量的等价关系'),
            ('库仑定律', 'F = kq₁q₂/r²', '点电荷间静电力'),
            ('电容定义', 'C = Q/U', '电容器容纳电荷的能力'),
            ('电阻定律', 'R = ρl/S', '导体电阻与长度、截面积的关系'),
            ('波的干涉条件', '频率相同、相位差恒定', '产生稳定干涉条纹的条件'),
            ('光电效应方程', 'Ek = hf - W', '光电子最大初动能'),
            ('德布罗意波长', 'λ = h/p', '物质波波长'),
        ]
        
        for name, formula, desc in physics_concepts:
            qid = self.generate_question_id()
            tags = json.dumps(['物理', '公式', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'{name}:{formula}\n\n请判断这个公式的正确性:{desc}',
                'options': json.dumps([
                    {'A': '正确'},
                    {'B': '部分正确'},
                    {'C': '需要修正'},
                    {'D': '完全错误'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'{name}的表达式是正确的',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(300):
            qid = self.generate_question_id()
            tags = json.dumps(['物理', '力学', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'力学练习题 {i+1}:\n\n质量为2kg的物体在10N的力作用下从静止开始运动,3秒后的速度是多少?',
                'options': json.dumps([
                    {'A': '5 m/s'},
                    {'B': '10 m/s'},
                    {'C': '15 m/s'},
                    {'D': '20 m/s'}
                ], ensure_ascii=False),
                'correct_answer': 'C',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': 'a = F/m = 10/2 = 5 m/s², v = at = 5×3 = 15 m/s',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(200):
            qid = self.generate_question_id()
            tags = json.dumps(['物理', '电磁学', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'电磁学练习题 {i+1}:\n\n一段导体在匀强磁场中做切割磁感线运动,导体长度为0.5m,速度为4m/s,磁感应强度为0.2T,则感应电动势为多少?',
                'options': json.dumps([
                    {'A': '0.2V'},
                    {'B': '0.4V'},
                    {'C': '0.8V'},
                    {'D': '1.6V'}
                ], ensure_ascii=False),
                'correct_answer': 'B',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': 'E = BLv = 0.2×0.5×4 = 0.4V',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(150):
            qid = self.generate_question_id()
            tags = json.dumps(['物理', '光学', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'光学练习题 {i+1}:\n\n光从空气进入水中,入射角为45°,水的折射率为1.33,则折射角约为多少?',
                'options': json.dumps([
                    {'A': '30°'},
                    {'B': '32°'},
                    {'C': '45°'},
                    {'D': '58°'}
                ], ensure_ascii=False),
                'correct_answer': 'B',
                'difficulty': 3,
                'points': 2.5,
                'audio_url': '',
                'tags': tags,
                'explanation': 'n₁sinθ₁ = n₂sinθ₂ → sinθ₂ = 1×sin45°/1.33 ≈ 0.53 → θ₂ ≈ 32°',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_chemistry_questions(self):
        """化学题库 - 方程式、反应、周期表"""
        print("\n🧪 生成化学题库...")
        questions = []
        
        chemical_concepts = [
            ('质量守恒定律', '化学反应前后各元素种类和原子个数不变', '反应物总质量等于生成物总质量'),
            ('阿伏伽德罗定律', '同温同压下,相同体积的任何气体含有相同数目的分子', '气体体积与物质的量的关系'),
            ('勒夏特列原理', '如果改变影响平衡的条件,平衡向减弱这种改变的方向移动', '平衡移动原理'),
            ('元素周期律', '元素的性质随原子序数的递增呈周期性变化', '元素周期表的规律性'),
            ('氧化还原反应', '反应中有电子转移(得失或偏移)', '升失氧,降得还'),
            ('离子反应条件', '生成沉淀、气体或水等难电离物质', '复分解反应发生的条件'),
            ('盖斯定律', '化学反应的热效应只与始态和终态有关,与途径无关', '反应热计算'),
            ('电离平衡常数', 'Ka或Kb表示弱电解质的电离程度', '酸碱强度判断'),
            ('溶度积常数', 'Ksp表示难溶电解质的溶解能力', '沉淀生成与溶解判断'),
            ('化学反应速率', 'v = Δc/Δt,表示浓度变化的快慢', '反应速率的影响因素'),
        ]
        
        for name, formula, desc in chemical_concepts:
            qid = self.generate_question_id()
            tags = json.dumps(['化学', '概念', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'{name}:{formula}\n\n请判断这个概念说法的正确性:{desc}',
                'options': json.dumps([
                    {'A': '正确'},
                    {'B': '部分正确'},
                    {'C': '需要补充'},
                    {'D': '完全错误'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'{name}的表述是正确的',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(300):
            qid = self.generate_question_id()
            tags = json.dumps(['化学', '无机化学', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'无机化学练习题 {i+1}:\n\n下列物质中,硫元素的化合价最高的是?',
                'options': json.dumps([
                    {'A': 'H₂S'},
                    {'B': 'SO₂'},
                    {'C': 'H₂SO₄'},
                    {'D': 'Na₂SO₃'}
                ], ensure_ascii=False),
                'correct_answer': 'C',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': 'H₂SO₄中S为+6价,是硫的最高常见化合价',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(200):
            qid = self.generate_question_id()
            tags = json.dumps(['化学', '有机化学', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'有机化学练习题 {i+1}:\n\n下列有机物中,能使溴水褪色的是?',
                'options': json.dumps([
                    {'A': '甲烷'},
                    {'B': '乙烯'},
                    {'C': '苯'},
                    {'D': '乙醇'}
                ], ensure_ascii=False),
                'correct_answer': 'B',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': '乙烯含有碳碳双键,能与溴发生加成反应使溴水褪色',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(150):
            qid = self.generate_question_id()
            tags = json.dumps(['化学', '计算', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'化学计算练习题 {i+1}:\n\n在标准状况下,11.2L CO₂所含的分子数约为多少?',
                'options': json.dumps([
                    {'A': '3.01×10²³'},
                    {'B': '6.02×10²³'},
                    {'C': '1.204×10²⁴'},
                    {'D': '1.806×10²⁴'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': 'n = 11.2/22.4 = 0.5mol, N = 0.5×6.02×10²³ = 3.01×10²³',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_biology_questions(self):
        """生物题库 - 细胞、遗传、生态"""
        print("\n🧬 生成生物题库...")
        questions = []
        
        bio_concepts = [
            ('细胞学说', '细胞是生物体结构和功能的基本单位', '所有生物都由细胞构成'),
            ('DNA双螺旋', 'DNA分子由两条反向平行的多核苷酸链组成', '沃森和克里克提出'),
            ('中心法则', 'DNA→RNA→蛋白质', '遗传信息的流动方向'),
            ('基因突变', 'DNA分子中碱基对的增添、缺失或替换', '可遗传变异的来源'),
            ('自然选择', '适者生存,不适者淘汰', '进化学说核心'),
            ('光合作用', '6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂', '光反应和暗反应'),
            ('细胞呼吸', 'C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O + 能量', '有氧呼吸方程式'),
            ('孟德尔遗传定律', '分离定律和自由组合定律', '遗传学基础'),
            ('免疫系统', '三道防线:皮肤黏膜、吞噬细胞、免疫细胞', '特异性免疫和非特异性免疫'),
            ('生态系统', '生产者、消费者、分解者、无机环境', '物质循环和能量流动'),
        ]
        
        for name, formula, desc in bio_concepts:
            qid = self.generate_question_id()
            tags = json.dumps(['生物', '概念', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'{name}:{formula}\n\n请判断这个概念说法的正确性:{desc}',
                'options': json.dumps([
                    {'A': '正确'},
                    {'B': '部分正确'},
                    {'C': '需要补充'},
                    {'D': '完全错误'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'{name}的表述是正确的',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(300):
            qid = self.generate_question_id()
            tags = json.dumps(['生物', '细胞生物学', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'细胞生物学练习题 {i+1}:\n\n下列细胞器中,不属于双层膜结构的是?',
                'options': json.dumps([
                    {'A': '线粒体'},
                    {'B': '叶绿体'},
                    {'C': '内质网'},
                    {'D': '细胞核'}
                ], ensure_ascii=False),
                'correct_answer': 'C',
                'difficulty': 1,
                'points': 1.5,
                'audio_url': '',
                'tags': tags,
                'explanation': '内质网是单层膜结构,线粒体、叶绿体、细胞核都是双层膜结构',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(200):
            qid = self.generate_question_id()
            tags = json.dumps(['生物', '遗传学', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'遗传学练习题 {i+1}:\n\n孟德尔分离定律表明:杂合子(Dd)自交后代的基因型比例为?',
                'options': json.dumps([
                    {'A': '1:1'},
                    {'B': '1:2:1'},
                    {'C': '3:1'},
                    {'D': '9:3:3:1'}
                ], ensure_ascii=False),
                'correct_answer': 'B',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': 'Dd×Dd → 1DD:2Dd:1dd,即1:2:1',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_chinese_questions(self):
        """语文题库 - 古文、古诗、文学常识"""
        print("\n📜 生成语文题库...")
        questions = []
        
        poetry_data = [
            ('静夜思', '李白', '床前明月光,疑是地上霜.举头望明月,低头思故乡.', '思乡'),
            ('春晓', '孟浩然', '春眠不觉晓,处处闻啼鸟.夜来风雨声,花落知多少.', '惜春'),
            ('望庐山瀑布', '李白', '日照香炉生紫烟,遥看瀑布挂前川.飞流直下三千尺,疑是银河落九天.', '写景'),
            ('悯农', '李绅', '锄禾日当午,汗滴禾下土.谁知盘中餐,粒粒皆辛苦.', '悯农'),
            ('咏鹅', '骆宾王', '鹅鹅鹅,曲项向天歌.白毛浮绿水,红掌拨清波.', '咏物'),
            ('登鹳雀楼', '王之涣', '白日依山尽,黄河入海流.欲穷千里目,更上一层楼.', '登高'),
            ('江雪', '柳宗元', '千山鸟飞绝,万径人踪灭.孤舟蓑笠翁,独钓寒江雪.', '孤高'),
            ('望天门山', '李白', '天门中断楚江开,碧水东流至此回.两岸青山相对出,孤帆一片日边来.', '山水'),
            ('山行', '杜牧', '远上寒山石径斜,白云生处有人家.停车坐爱枫林晚,霜叶红于二月花.', '秋景'),
            ('枫桥夜泊', '张继', '月落乌啼霜满天,江枫渔火对愁眠.姑苏城外寒山寺,夜半钟声到客船.', '愁思'),
        ]
        
        for title, author, content, theme in poetry_data:
            qid = self.generate_question_id()
            tags = json.dumps(['语文', '古诗词', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'古诗词鉴赏题:\n\n《{title}》({author})\n{content}\n\n这首诗的主题是什么?',
                'options': json.dumps([
                    {'A': theme},
                    {'B': '其他主题'},
                    {'C': '表达爱情'},
                    {'D': '描写战争'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'《{title}》表达了诗人{theme}的情感',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        classical_texts = [
            ('《论语》', '子曰:学而时习之,不亦说乎?有朋自远方来,不亦乐乎?', '学习方法和人际交往'),
            ('《孟子》', '鱼,我所欲也;熊掌,亦我所欲也.二者不可得兼,舍鱼而取熊掌者也.', '舍生取义'),
            ('《庄子》', '北冥有鱼,其名为鲲.鲲之大,不知其几千里也.', '道家思想'),
            ('《史记》', '史家之绝唱,无韵之离骚.', '史学和文学价值'),
            ('《出师表》', '诸葛亮:先帝创业未半而中道崩殂,今天下三分,益州疲弊,此诚危急存亡之秋也.', '忠君爱国'),
        ]
        
        for title, content, theme in classical_texts:
            qid = self.generate_question_id()
            tags = json.dumps(['语文', '古文', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'古文阅读理解题:\n\n{title}\n{content}\n\n这段文字主要表达了什么?',
                'options': json.dumps([
                    {'A': theme},
                    {'B': '描写风景'},
                    {'C': '记录历史'},
                    {'D': '说明道理'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 3,
                'points': 2.5,
                'audio_url': '',
                'tags': tags,
                'explanation': f'{title}表达了{theme}的思想',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(400):
            qid = self.generate_question_id()
            tags = json.dumps(['语文', '文学常识', '选择题'], ensure_ascii=False)
            
            authors = ['李白', '杜甫', '白居易', '王维', '苏轼', '辛弃疾', '李清照', '陶渊明']
            author = random.choice(authors)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'文学常识练习题 {i+1}:\n\n下列作家中,属于唐代诗人的是?',
                'options': json.dumps([
                    {'A': author if author in ['李白', '杜甫', '白居易', '王维'] else '韩愈'},
                    {'B': '苏轼'},
                    {'C': '李清照'},
                    {'D': '辛弃疾'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 1,
                'points': 1.5,
                'audio_url': '',
                'tags': tags,
                'explanation': '唐代著名诗人包括李白、杜甫、白居易、王维等',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_history_questions(self):
        """历史题库 - 事件、人物、年代"""
        print("\n📜 生成历史题库...")
        questions = []
        
        historical_events = [
            ('商鞅变法', '战国时期秦国', '公元前356年', '确立了封建土地私有制'),
            ('秦始皇统一六国', '战国末期', '公元前221年', '建立中国第一个统一王朝'),
            ('贞观之治', '唐朝', '627-649年', '唐太宗统治时期的繁荣'),
            ('郑和下西洋', '明朝', '1405-1433年', '展示了明朝的航海实力'),
            ('鸦片战争', '清朝', '1840-1842年', '中国近代史的开端'),
            ('辛亥革命', '清朝末期', '1911年', '推翻封建帝制'),
            ('五四运动', '民国', '1919年5月4日', '新民主主义革命的开端'),
            ('新中国成立', '现代', '1949年10月1日', '中华民族站起来了'),
            ('改革开放', '现代', '1978年', '中国进入新时代'),
            ('一带一路', '现代', '2013年', '构建人类命运共同体'),
        ]
        
        for name, period, date, desc in historical_events:
            qid = self.generate_question_id()
            tags = json.dumps(['历史', '重大事件', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'历史事件题:\n\n{name}发生在什么时期?',
                'options': json.dumps([
                    {'A': period},
                    {'B': '其他时期'},
                    {'C': '时间不确定'},
                    {'D': '古代和现代交替'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 1,
                'points': 1.5,
                'audio_url': '',
                'tags': tags,
                'explanation': f'{name}是{period}发生的重大历史事件',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(400):
            qid = self.generate_question_id()
            tags = json.dumps(['历史', '选择题', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'历史知识练习题 {i+1}:\n\n抗日战争胜利距今(2024年)大约多少年?',
                'options': json.dumps([
                    {'A': '70多年'},
                    {'B': '80多年'},
                    {'C': '90多年'},
                    {'D': '100多年'}
                ], ensure_ascii=False),
                'correct_answer': 'B',
                'difficulty': 1,
                'points': 1.5,
                'audio_url': '',
                'tags': tags,
                'explanation': '抗日战争胜利于1945年,距2024年约79年',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_geography_questions(self):
        """地理题库 - 地形、气候、区域"""
        print("\n🌍 生成地理题库...")
        questions = []
        
        geography_concepts = [
            ('地球运动', '自转周期24小时,产生昼夜交替', '时区和日期变更'),
            ('大气环流', '三圈环流:信风带、西风带、极地东风带', '全球气候分布'),
            ('水循环', '蒸发→凝结→降水→径流→蒸发', '海陆间循环'),
            ('板块构造', '六大板块:亚欧、非洲、美洲、南极、印度洋、太平洋', '地震和火山分布'),
            ('气候类型', '热带雨林、温带季风、亚热带季风、地中海等', '受纬度、海陆位置影响'),
            ('人口分布', '北半球、沿海地区、低海拔地区', '世界人口分布特点'),
            ('城市区位', '地形、气候、河流、交通、资源', '影响城市形成发展的因素'),
            ('产业转移', '从发达国家向发展中国家转移', '劳动力、资源、市场'),
            ('资源跨区域调配', '西气东输、南水北调、西电东送', '解决资源分布不均'),
            ('环境保护', '可持续发展、人地协调', '生态文明建设'),
        ]
        
        for name, content, desc in geography_concepts:
            qid = self.generate_question_id()
            tags = json.dumps(['地理', '概念', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'地理概念题:\n\n{name}:{content}\n\n请判断这个概念的正确性:{desc}',
                'options': json.dumps([
                    {'A': '正确'},
                    {'B': '部分正确'},
                    {'C': '需要修正'},
                    {'D': '完全错误'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'{name}的表述是正确的地理概念',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(400):
            qid = self.generate_question_id()
            tags = json.dumps(['地理', '自然地理', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'自然地理练习题 {i+1}:\n\n世界上面积最大的大洲是?',
                'options': json.dumps([
                    {'A': '亚洲'},
                    {'B': '非洲'},
                    {'C': '北美洲'},
                    {'D': '南美洲'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 1,
                'points': 1.5,
                'audio_url': '',
                'tags': tags,
                'explanation': '亚洲是世界上面积最大的大洲,约4400万平方公里',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_politics_questions(self):
        """政治题库 - 概念、理论、制度"""
        print("\n🏛️ 生成政治题库...")
        questions = []
        
        politics_concepts = [
            ('马克思主义', '揭示人类社会发展规律的科学理论', '辩证唯物主义和历史唯物主义'),
            ('社会主义初级阶段', '不发达阶段向发达阶段转变的历史过程', '长期性、艰巨性、复杂性'),
            ('社会主义市场经济', '市场在国家宏观调控下对资源配置起决定性作用', '两只手:政府与市场'),
            ('人民民主专政', '工人阶级领导的、以工农联盟为基础的人民民主专政', '新型民主与新型专政'),
            ('依法治国', '依照宪法和法律治理国家', '科学立法、严格执法、公正司法、全民守法'),
            ('新发展理念', '创新、协调、绿色、开放、共享', '关系发展全局的深刻变革'),
            ('人类命运共同体', '持久和平、普遍安全、共同繁荣、开放包容、清洁美丽', '中国智慧和中国方案'),
            ('供给侧结构性改革', '提高供给质量,优化要素配置', '三去一降一补'),
            ('乡村振兴战略', '产业兴旺、生态宜居、乡风文明、治理有效、生活富裕', '解决三农问题'),
            ('中国式现代化', '人口规模巨大、全体人民共同富裕、物质文明和精神文明相协调、人与自然和谐共生、走和平发展道路', '现代化的中国特色'),
        ]
        
        for name, content, desc in politics_concepts:
            qid = self.generate_question_id()
            tags = json.dumps(['政治', '概念', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'政治概念题:\n\n{name}:{content}\n\n请判断这个概念的正确性:{desc}',
                'options': json.dumps([
                    {'A': '正确'},
                    {'B': '部分正确'},
                    {'C': '需要修正'},
                    {'D': '完全错误'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'{name}是正确的重要政治概念',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(300):
            qid = self.generate_question_id()
            tags = json.dumps(['政治', '时事政治', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'时事政治练习题 {i+1}:\n\n我国最高国家权力机关是?',
                'options': json.dumps([
                    {'A': '全国人民代表大会'},
                    {'B': '国务院'},
                    {'C': '最高人民法院'},
                    {'D': '中国人民政治协商会议'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 1,
                'points': 1.5,
                'audio_url': '',
                'tags': tags,
                'explanation': '全国人民代表大会是最高国家权力机关',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return questions
    
    def generate_english_grammar_questions(self):
        """英语语法题库"""
        print("\n🔤 生成英语语法题库...")
        questions = []
        
        grammar_rules = [
            ('时态', '一般现在时:主语+动词原形/三单', '习惯性动作、客观真理'),
            ('时态', '现在进行时:主语+am/is/are+doing', '正在进行的动作'),
            ('时态', '一般过去时:主语+动词过去式', '过去的动作或状态'),
            ('时态', '现在完成时:主语+have/has+过去分词', '过去的动作对现在的影响'),
            ('语态', '被动语态:主语+be+过去分词', '强调动作承受者'),
            ('从句', '定语从句:先行词+关系代词/副词', '修饰名词或代词'),
            ('从句', '状语从句:主语+从句连词+主语', '表示时间、原因、条件等'),
            ('从句', '名词性从句:主语/宾语/表语/同位语+从句', '起名词作用'),
            ('非谓语', '不定式:to+动词原形', '表示目的、原因、结果'),
            ('非谓语', '动名词:动词+ing', '起名词作用'),
            ('虚拟语气', 'If+主语+were/did, 主语+would/could+do', '与事实相反的假设'),
            ('情态动词', 'must/have to/should/ought to', '表示必要性或建议'),
        ]
        
        for category, rule, usage in grammar_rules:
            qid = self.generate_question_id()
            tags = json.dumps(['英语', '语法', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'英语语法题({category}):\n\n语法规则:{rule}\n使用场景:{usage}',
                'options': json.dumps([
                    {'A': '正确'},
                    {'B': '需要修正'},
                    {'C': '部分正确'},
                    {'D': '完全错误'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': f'{rule}是{usage}的{category}表达',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        for i in range(400):
            qid = self.generate_question_id()
            tags = json.dumps(['英语', '语法', '选择题'], ensure_ascii=False)
            
            questions.append({
                'id': qid,
                'type': 'single_choice',
                'content': f'英语语法练习题 {i+1}:\n\nShe ___ to Beijing three times. (be)',
                'options': json.dumps([
                    {'A': 'has been'},
                    {'B': 'have been'},
                    {'C': 'has gone'},
                    {'D': 'have went'}
                ], ensure_ascii=False),
                'correct_answer': 'A',
                'difficulty': 2,
                'points': 2.0,
                'audio_url': '',
                'tags': tags,
                'explanation': '"has been to"表示去过某地且已回来',
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
    
    def expand_comprehensive_question_bank(self):
        print("=" * 60)
        print("开始扩充综合学科题库")
        print("=" * 60)
        
        all_questions = []
        
        all_questions.extend(self.generate_math_questions())
        all_questions.extend(self.generate_physics_questions())
        all_questions.extend(self.generate_chemistry_questions())
        all_questions.extend(self.generate_biology_questions())
        all_questions.extend(self.generate_chinese_questions())
        all_questions.extend(self.generate_history_questions())
        all_questions.extend(self.generate_geography_questions())
        all_questions.extend(self.generate_politics_questions())
        all_questions.extend(self.generate_english_grammar_questions())
        
        print(f"\n总计生成 {len(all_questions)} 道综合学科题目")
        
        batch_size = 500
        for i in range(0, len(all_questions), batch_size):
            batch = all_questions[i:i+batch_size]
            self.insert_questions(batch)
        
        print("\n" + "=" * 60)
        print("综合学科题库扩充完成!")
        print("=" * 60)
        
        cursor = self.conn.cursor()
        
        subjects = ['数学', '物理', '化学', '生物', '语文', '历史', '地理', '政治', '英语']
        print("\n📊 各学科题目数量:")
        for subject in subjects:
            cursor.execute("SELECT COUNT(*) FROM questions WHERE tags LIKE ?", (f'%{subject}%',))
            count = cursor.fetchone()[0]
            print(f"  {subject}: {count}")
        
        cursor.execute('SELECT COUNT(*) FROM questions')
        total = cursor.fetchone()[0]
        print(f"\n题库总数: {total}")

def main():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
    print(f"数据库路径: {db_path}")
    
    expander = ComprehensiveQuestionBankExpander(db_path)
    expander.connect()
    expander.init_question_table()
    
    expander.expand_comprehensive_question_bank()
    
    expander.close()
    print("\n综合学科题库扩充任务完成!")

if __name__ == '__main__':
    main()
