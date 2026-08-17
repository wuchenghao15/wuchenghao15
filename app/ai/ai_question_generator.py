#!/usr/bin/env python3
""" AI智能出题系统 v2.0 增强功能：AI模型调用、动态选项生成、自适应难度、错题分析、题目去重 支持多科目、多题型、智能学习分析 """

import sqlite3
import random
import json
import hashlib
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger('ai_question_generator')

class AIQuestionGenerator:
    SUBJECTS = ['数学', '英语', '语文', '物理', '化学', '生物', '历史', '地理', '政治', '日语']
    
    QUESTION_TEMPLATES = {
        '数学': {
            '函数基础': [
                ('求函数f(x) = {a}x^2 + {b}x + {c}的顶点坐标', '顶点坐标为(-b/(2a), f(-b/(2a)))'),
                ('已知函数f(x) = {a}x + {b}，求f({x_val})的值', '代入计算'),
                ('判断函数f(x) = {expr}的奇偶性', 'f(-x) = f(x)为偶函数，f(-x) = -f(x)为奇函数'),
                ('求函数y = {expr}的定义域', '分析表达式中各部分的限制条件'),
                ('求函数y = {expr}的值域', '分析函数在定义域内的取值范围'),
                ('求函数f(x) = {expr}的零点', '令f(x) = 0，解方程'),
                ('判断函数f(x) = {expr}在区间[{a}, {b}]上的单调性', '求导分析导数符号'),
            ],
            '导数': [
                ('求函数f(x) = {expr}的导数f\'(x)', '应用求导公式'),
                ('已知f(x) = {expr}，求f\'({x_val})', '先求导再代入'),
                ('求函数f(x) = {expr}的单调区间', '求导并分析导数的正负'),
                ('求函数f(x) = {expr}的极值', '令导数为0，分析临界点'),
                ('求函数f(x) = {expr}在区间[{a}, {b}]上的最值', '比较端点和极值'),
                ('求曲线y = {expr}在点({x_val}, f({x_val}))处的切线方程', '利用导数求切线斜率'),
            ],
            '概率统计': [
                ('从{n}个球中随机取出{k}个，求其中{m}个红球的概率', '组合计算'),
                ('掷骰子{k}次，求出现{m}次点数为{n}的概率', '二项分布'),
                ('计算数据{data}的平均数', '求和除以个数'),
                ('计算数据{data}的方差', '先求均值，再计算偏差平方和'),
                ('分析两组数据的相关性', '计算相关系数'),
                ('从数据{data}中找出中位数', '排序后取中间值'),
            ],
            '三角函数': [
                ('化简表达式{expr}', '利用三角恒等式'),
                ('求sin({angle})的值', '使用三角函数公式'),
                ('解三角方程{expr} = 0', '利用三角恒等式转化'),
                ('求函数y = {expr}的周期', '分析三角函数的周期性质'),
                ('证明三角恒等式{expr}', '利用已知恒等式推导'),
                ('求函数y = {expr}的振幅和初相', '分析三角函数的参数'),
            ],
            '立体几何': [
                ('求正方体的对角线长度', '空间对角线公式'),
                ('求圆柱的体积', '底面积乘以高'),
                ('求圆锥的表面积', '侧面积加底面积'),
                ('证明线面平行', '利用判定定理'),
                ('求异面直线的夹角', '利用向量方法'),
                ('求棱锥的体积', '底面积乘以高再除以3'),
            ],
            '解析几何': [
                ('求过点({a}, {b})和({c}, {d})的直线方程', '两点式求直线方程'),
                ('求圆{x}^2 + {y}^2 + {a}x + {b}y + {c} = 0的圆心和半径', '配方法'),
                ('求直线{a}x + {b}y + {c} = 0与圆的位置关系', '计算圆心到直线的距离'),
                ('求椭圆{x}^2/{a}^2 + {y}^2/{b}^2 = 1的焦点坐标', 'c^2 = a^2 - b^2'),
            ],
        },
        '英语': {
            '词汇': [
                ('选择与{word}意思最接近的词', '词汇辨析'),
                ('用{word}的正确形式填空', '词性和时态'),
                ('翻译句子{sentence}', '英译中'),
                ('写出{word}的反义词', '词汇记忆'),
                ('用{word}造句', '词汇应用'),
                ('选择{word}的正确词性', '词汇分类'),
                ('解释{word}在句子中的含义', '语境理解'),
            ],
            '语法': [
                ('选择正确的时态填空', '时态辨析'),
                ('分析句子的语法结构', '句子成分分析'),
                ('改写句子为被动语态', '语态转换'),
                ('选择正确的介词', '介词搭配'),
                ('判断句子的正误', '语法规则'),
                ('选择正确的连词', '连词用法'),
                ('分析定语从句的关系词', '从句语法'),
            ],
            '阅读': [
                ('根据文章内容推断作者意图', '推理判断'),
                ('找出文章的主旨句', '主旨大意'),
                ('解释文中划线部分的含义', '词义猜测'),
                ('根据文章内容选择最佳标题', '标题归纳'),
                ('分析文章的结构', '篇章结构'),
                ('判断文章的写作手法', '写作技巧'),
            ],
            '写作': [
                ('根据提示写一篇{num}词的短文', '书面表达'),
                ('修改作文中的语法错误', '纠错能力'),
                ('完善句子使其更加流畅', '句式优化'),
                ('根据提纲组织文章', '写作结构'),
                ('使用连接词使文章连贯', '逻辑衔接'),
            ],
            '听力': [
                ('根据听力内容选择正确答案', '听力理解'),
                ('听对话选择说话人的态度', '语气判断'),
                ('听短文回答问题', '信息提取'),
            ],
        },
        '语文': {
            '文言文': [
                ('解释实词{word}的含义', '实词释义'),
                ('翻译句子{sentence}', '句子翻译'),
                ('分析虚词{word}的用法', '虚词用法'),
                ('理解文章的主旨', '主旨理解'),
                ('分析人物形象', '人物分析'),
                ('断句并翻译', '古文断句'),
                ('分析文章的论证方法', '论证分析'),
            ],
            '现代文': [
                ('分析文章的写作手法', '写作技巧'),
                ('理解作者的情感', '情感把握'),
                ('概括段落大意', '段落概括'),
                ('分析文章的语言特色', '语言风格'),
                ('评价文章的观点', '观点评价'),
                ('分析文章的结构', '篇章结构'),
            ],
            '诗词鉴赏': [
                ('分析诗词的意象', '意象分析'),
                ('理解诗词的意境', '意境赏析'),
                ('分析诗人的情感', '情感把握'),
                ('鉴赏诗词的语言', '语言特色'),
                ('分析诗词的表现手法', '手法分析'),
            ],
            '写作': [
                ('根据材料写一篇议论文', '议论文写作'),
                ('根据提示写一篇记叙文', '记叙文写作'),
                ('写一篇说明文介绍{topic}', '说明文写作'),
                ('修改作文提升文采', '作文修改'),
            ],
        },
        '物理': {
            '力学': [
                ('计算物体在{F}牛作用下的加速度', '牛顿第二定律'),
                ('求物体从高度{h}自由落下的时间', '自由落体运动'),
                ('计算两个物体碰撞后的速度', '动量守恒'),
                ('分析物体在斜面上的受力', '受力分析'),
                ('求弹簧的弹性势能', '胡克定律'),
                ('计算匀速圆周运动的向心力', '圆周运动'),
                ('分析平抛运动的轨迹', '抛体运动'),
            ],
            '电磁学': [
                ('计算电路中的电流', '欧姆定律'),
                ('求电阻的功率', 'P=UI'),
                ('分析磁场对电流的作用', '安培力'),
                ('计算电容器的电容', 'C=Q/U'),
                ('分析电磁感应现象', '法拉第定律'),
                ('计算带电粒子在磁场中的运动', '洛伦兹力'),
                ('分析交流电的有效值', '交流电'),
            ],
            '热学': [
                ('计算理想气体的压强变化', '理想气体定律'),
                ('分析热传递过程', '热力学'),
                ('计算物体的内能变化', '内能'),
            ],
        },
        '化学': {
            '无机化学': [
                ('配平方程式{eq}', '原子守恒'),
                ('计算物质的量', 'n=m/M'),
                ('判断化学反应类型', '反应分类'),
                ('分析元素周期律', '周期表知识'),
                ('计算溶液的浓度', '物质的量浓度'),
                ('分析氧化还原反应', '氧化还原'),
                ('判断离子共存', '离子反应'),
            ],
            '有机化学': [
                ('命名有机物{name}', '系统命名法'),
                ('判断有机物的官能团', '官能团识别'),
                ('分析有机物的结构', '结构分析'),
                ('写出有机物的同分异构体', '同分异构'),
                ('判断有机反应类型', '反应类型'),
                ('分析有机物的性质', '有机物性质'),
            ],
        },
        '生物': {
            '细胞生物学': [
                ('分析细胞膜的结构', '细胞膜'),
                ('解释细胞呼吸过程', '细胞呼吸'),
                ('分析光合作用的机制', '光合作用'),
                ('描述细胞分裂过程', '细胞分裂'),
                ('解释DNA复制过程', 'DNA复制'),
            ],
            '遗传学': [
                ('分析孟德尔遗传定律', '遗传定律'),
                ('计算基因频率', '种群遗传学'),
                ('解释基因突变', '基因突变'),
                ('分析染色体变异', '染色体变异'),
            ],
        },
        '历史': {
            '中国古代史': [
                ('分析朝代更替的原因', '朝代变迁'),
                ('评价历史人物', '人物评价'),
                ('分析历史事件的影响', '事件分析'),
                ('描述制度变革', '制度史'),
            ],
            '中国近现代史': [
                ('分析近代化进程', '近代化'),
                ('评价重大历史事件', '事件评价'),
                ('分析社会变革', '社会史'),
            ],
        },
        '地理': {
            '自然地理': [
                ('分析气候类型', '气候'),
                ('解释地形形成', '地貌'),
                ('分析洋流影响', '洋流'),
                ('描述板块运动', '板块构造'),
            ],
            '人文地理': [
                ('分析城市发展', '城市地理'),
                ('评价农业区位', '农业地理'),
                ('分析工业布局', '工业地理'),
            ],
        },
        '政治': {
            '哲学': [
                ('分析唯物辩证法', '辩证法'),
                ('解释认识论', '认识论'),
                ('分析历史唯物主义', '唯物史观'),
            ],
            '经济学': [
                ('分析市场经济', '市场经济'),
                ('解释宏观调控', '宏观经济'),
                ('分析国际贸易', '国际经济'),
            ],
        },
        '日语': {
            '词汇': [
                ('选择{word}({kana})的正确中文意思', '词汇释义'),
                ('写出{word}的平假名', '假名'),
                ('写出{word}的片假名', '片假名'),
                ('用{word}造句', '词汇应用'),
            ],
            '语法': [
                ('选择正确的助词', '助词'),
                ('分析动词的活用', '动词变形'),
                ('选择正确的敬语', '敬语'),
                ('分析句子结构', '句型'),
            ],
        },
    }

    VOCABULARY_DATA = {
        '英语': {
            '初级': [
                {'word': 'apple', 'meaning': '苹果', 'confusions': ['orange', 'banana', 'grape']},
                {'word': 'book', 'meaning': '书', 'confusions': ['notebook', 'magazine', 'dictionary']},
                {'word': 'happy', 'meaning': '快乐的', 'confusions': ['sad', 'angry', 'tired']},
                {'word': 'run', 'meaning': '跑', 'confusions': ['walk', 'jump', 'swim']},
                {'word': 'beautiful', 'meaning': '美丽的', 'confusions': ['pretty', 'handsome', 'ugly']},
                {'word': 'important', 'meaning': '重要的', 'confusions': ['necessary', 'essential', 'unimportant']},
                {'word': 'difficult', 'meaning': '困难的', 'confusions': ['hard', 'easy', 'simple']},
                {'word': 'knowledge', 'meaning': '知识', 'confusions': ['information', 'intelligence', 'wisdom']},
            ],
            '中级': [
                {'word': 'development', 'meaning': '发展', 'confusions': ['progress', 'growth', 'improvement']},
                {'word': 'opportunity', 'meaning': '机会', 'confusions': ['chance', 'possibility', 'risk']},
                {'word': 'challenge', 'meaning': '挑战', 'confusions': ['difficulty', 'problem', 'opportunity']},
                {'word': 'success', 'meaning': '成功', 'confusions': ['achievement', 'victory', 'failure']},
                {'word': 'education', 'meaning': '教育', 'confusions': ['learning', 'training', 'teaching']},
            ],
            '高级': [
                {'word': 'comprehensive', 'meaning': '综合的', 'confusions': ['comprehensible', 'complicative',
                'complementary']},
                {'word': 'sophisticated', 'meaning': '复杂精密的', 'confusions': ['simplistic', 'sophomoric', 'soporific']},
                {'word': 'contemporary', 'meaning': '当代的', 'confusions': ['temporary', 'contentious', 'conservative']},
                {'word': 'fundamental', 'meaning': '基本的', 'confusions': ['fundamentally', 'functional',
                'foundational']},
            ],
        },
        '日语': {
            '初级': [
                {'word': '猫', 'kana': 'ねこ', 'meaning': '猫', 'confusions': ['犬', '鳥', '魚']},
                {'word': '犬', 'kana': 'いぬ', 'meaning': '狗', 'confusions': ['猫', '馬', '牛']},
                {'word': '本', 'kana': 'ほん', 'meaning': '书', 'confusions': ['雑誌', '新聞', '辞書']},
                {'word': '水', 'kana': 'みず', 'meaning': '水', 'confusions': ['お茶', 'コーヒー', 'ジュース']},
                {'word': '食べる', 'kana': 'たべる', 'meaning': '吃', 'confusions': ['飲む', '話す', '見る']},
                {'word': '行く', 'kana': 'いく', 'meaning': '去', 'confusions': ['来る', '帰る', '出る']},
                {'word': '見る', 'kana': 'みる', 'meaning': '看', 'confusions': ['聞く', '話す', '食べる']},
                {'word': '聞く', 'kana': 'きく', 'meaning': '听', 'confusions': ['見る', '話す', '読む']},
            ],
            '中级': [
                {'word': '勉強', 'kana': 'べんきょう', 'meaning': '学习', 'confusions': ['仕事', '働く', '研究']},
                {'word': '研究', 'kana': 'けんきゅう', 'meaning': '研究', 'confusions': ['勉強', '調査', '開発']},
                {'word': '開発', 'kana': 'かいはつ', 'meaning': '开发', 'confusions': ['研究', '設計', '製造']},
                {'word': '設計', 'kana': 'せっけい', 'meaning': '设计', 'confusions': ['開発', '製造', '企画']},
            ],
            '高级': [
                {'word': '認識', 'kana': 'にんしき', 'meaning': '认识', 'confusions': ['認知', '意識', '理解']},
                {'word': '意識', 'kana': 'いしき', 'meaning': '意识', 'confusions': ['認識', '認知', '知識']},
                {'word': '理解', 'kana': 'りかい', 'meaning': '理解', 'confusions': ['認識', '知識', '認知']},
            ],
        },
        '语文': {
            '初级': [
                {'word': '之', 'meaning': '的/到', 'confusions': ['其', '于', '而']},
                {'word': '其', 'meaning': '他的/其中', 'confusions': ['之', '于', '以']},
                {'word': '于', 'meaning': '在/从', 'confusions': ['之', '其', '而']},
                {'word': '而', 'meaning': '但是/并且', 'confusions': ['之', '于', '则']},
            ],
            '中级': [
                {'word': '乃', 'meaning': '于是/才', 'confusions': ['遂', '即', '因']},
                {'word': '遂', 'meaning': '于是/终于', 'confusions': ['乃', '即', '遂']},
                {'word': '即', 'meaning': '就/立即', 'confusions': ['乃', '遂', '因']},
            ],
        },
    }

    SENTENCES_DATA = {
        '英语': [
            'The quick brown fox jumps over the lazy dog.',
            'Education is the key to success.',
            'Knowledge is power.',
            'Practice makes perfect.',
            'Time flies when you are having fun.',
            'Actions speak louder than words.',
            'The early bird catches the worm.',
            'Where there is a will, there is a way.',
        ],
        '语文': [
            '学而不思则罔，思而不学则殆。',
            '三人行，必有我师焉。',
            '温故而知新，可以为师矣。',
            '知之者不如好之者，好之者不如乐之者。',
            '君子坦荡荡，小人长戚戚。',
            '己所不欲，勿施于人。',
        ],
        '日语': [
            'こんにちは。元気ですか？',
            'ありがとうございます。',
            'すみません、道を教えてください。',
            '今日はいい天気ですね。',
            '日本語を勉強しています。',
        ],
    }

    EQUATIONS_DATA = {
        '化学': [
            {'equation': 'Fe + O2 -> Fe2O3', 'balanced': '4Fe + 3O2 = 2Fe2O3'},
            {'equation': 'H2 + O2 -> H2O', 'balanced': '2H2 + O2 = 2H2O'},
            {'equation': 'NaOH + HCl -> NaCl + H2O', 'balanced': 'NaOH + HCl = NaCl + H2O'},
            {'equation': 'CaCO3 -> CaO + CO2', 'balanced': 'CaCO3 = CaO + CO2'},
            {'equation': 'N2 + H2 -> NH3', 'balanced': 'N2 + 3H2 = 2NH3'},
        ],
    }

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'app.db')
        self._init_database()
        self._ai_engine = None

    def _get_ai_engine(self):
        if self._ai_engine is None:
            try:
                from ai_engines.ai_engine import AIEngine
                self._ai_engine = AIEngine()
            except Exception as e:
                logger.warning(f"AI引擎初始化失败，使用模板生成模式: {e}")
        return self._ai_engine

    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(''' CREATE TABLE IF NOT EXISTS generated_question_sets ( id INTEGER PRIMARY KEY AUTOINCREMENT, set_id TEXT NOT NULL UNIQUE, user_id TEXT NOT NULL, subject TEXT NOT NULL, difficulty TEXT, topic TEXT, question_count INTEGER DEFAULT 10, questions TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')

        cursor.execute(''' CREATE TABLE IF NOT EXISTS question_statistics ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, subject TEXT, topic TEXT, question_type TEXT, correct_count INTEGER DEFAULT 0, wrong_count INTEGER DEFAULT 0, accuracy REAL DEFAULT 0.0, last_practice_date TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')

        conn.commit()
        conn.close()

    def _generate_number(self, min_val=1, max_val=100):
        return random.randint(min_val, max_val)

    def _generate_expression(self, topic):
        if topic in ['函数基础', '导数']:
            a, b, c = self._generate_number(1, 10), self._generate_number(-10, 10), self._generate_number(-100, 100)
            return f'{a}x^2 + {b}x + {c}'
        elif topic == '三角函数':
            func = random.choice(['sin', 'cos', 'tan'])
            coeff = self._generate_number(1, 5)
            angle = random.choice(['x', '2x', 'x/2', 'x + π/2'])
            return f'{coeff}{func}({angle})'
        elif topic == '概率统计':
            data = ', '.join(str(self._generate_number(1, 100)) for _ in range(5))
            return data
        elif topic == '解析几何':
            a, b, c = self._generate_number(1, 10), self._generate_number(-10, 10), self._generate_number(-50, 50)
            return f'{a}x + {b}y + {c}'
        return 'x^2 + 2x + 1'

    def _generate_word(self, subject, difficulty='medium'):
        vocab = self.VOCABULARY_DATA.get(subject, {})
        level = '初级'
        if difficulty == 'high':
            level = '高级'
        elif difficulty == 'medium':
            level = '中级'

        vocab_list = vocab.get(level, vocab.get('初级', []))
        if vocab_list:
            return random.choice(vocab_list)
        return {'word': 'test', 'meaning': '测试', 'confusions': ['exam', 'quiz', 'assessment']}

    def _generate_sentence(self, subject):
        sentences = self.SENTENCES_DATA.get(subject, [])
        if sentences:
            return random.choice(sentences)
        return 'Test sentence'

    def _generate_equation(self, subject):
        equations = self.EQUATIONS_DATA.get(subject, [])
        if equations:
            return random.choice(equations)
        return {'equation': 'A + B -> C', 'balanced': 'A + B = C'}

    def _generate_options(self, question_text, subject, topic, difficulty):
        options = []
        answer_text = ""

        if subject in ['英语', '日语'] and topic == '词汇':
            vocab_item = self._generate_word(subject, difficulty)
            answer_text = vocab_item['meaning']
            options = [{'key': chr(ord('A') + i), 'text': opt} 
                       for i, opt in enumerate(vocab_item.get('confusions', [])[:3] + [answer_text])]
            random.shuffle(options)
            return options, answer_text

        elif subject == '数学' and topic in ['函数基础', '导数']:
            a = self._generate_number(1, 10)
            b = self._generate_number(-10, 10)
            c = self._generate_number(-100, 100)
            answer = a + b + c
            options = [
                {'key': 'A', 'text': str(answer)},
                {'key': 'B', 'text': str(answer + random.randint(1, 20))},
                {'key': 'C', 'text': str(answer - random.randint(1, 20))},
                {'key': 'D', 'text': str(abs(answer) * random.randint(2, 3))},
            ]
            random.shuffle(options)
            return options, str(answer)

        elif subject == '数学' and topic == '概率统计':
            data = [self._generate_number(10, 90) for _ in range(5)]
            answer = sum(data) // len(data)
            options = [
                {'key': 'A', 'text': str(answer)},
                {'key': 'B', 'text': str(answer + random.randint(5, 15))},
                {'key': 'C', 'text': str(answer - random.randint(5, 15))},
                {'key': 'D', 'text': str(int(answer * 1.5))},
            ]
            random.shuffle(options)
            return options, str(answer)

        elif subject == '物理' and topic == '力学':
            F = self._generate_number(10, 100)
            m = self._generate_number(1, 10)
            answer = F // m
            options = [
                {'key': 'A', 'text': str(answer)},
                {'key': 'B', 'text': str(answer + random.randint(1, 10))},
                {'key': 'C', 'text': str(answer - random.randint(1, 10))},
                {'key': 'D', 'text': str(answer * random.randint(2, 3))},
            ]
            random.shuffle(options)
            return options, str(answer)

        elif subject == '化学' and topic == '无机化学':
            eq = self._generate_equation(subject)
            answer = eq['balanced']
            options = [
                {'key': 'A', 'text': answer},
                {'key': 'B', 'text': eq['equation']},
                {'key': 'C', 'text': eq['equation'].replace('->', '=')},
                {'key': 'D', 'text': '无法配平'},
            ]
            random.shuffle(options)
            return options, answer

        default_options = [
            {'key': 'A', 'text': '正确答案'},
            {'key': 'B', 'text': '干扰项A'},
            {'key': 'C', 'text': '干扰项B'},
            {'key': 'D', 'text': '干扰项C'},
        ]
        random.shuffle(default_options)
        return default_options, '正确答案'

    def _generate_question(self, subject, topic, difficulty='medium', use_ai=False):
        if use_ai:
            return self._generate_ai_question(subject, topic, difficulty)

        templates = self.QUESTION_TEMPLATES.get(subject, {}).get(topic, [])
        if not templates:
            templates = [('请解答以下问题', '请根据所学知识回答')]

        template, explanation = random.choice(templates)

        replacements = {
            'a': str(self._generate_number(1, 10)),
            'b': str(self._generate_number(-10, 10)),
            'c': str(self._generate_number(-100, 100)),
            'x_val': str(self._generate_number(-10, 10)),
            'n': str(self._generate_number(5, 20)),
            'k': str(self._generate_number(1, 5)),
            'm': str(self._generate_number(1, 4)),
            'h': str(self._generate_number(1, 100)),
            'F': str(self._generate_number(10, 100)),
            'expr': self._generate_expression(topic),
            'angle': random.choice(['30°', '45°', '60°', '90°', '120°']),
            'data': ', '.join(str(self._generate_number(10, 90)) for _ in range(5)),
            'word': '',
            'kana': '',
            'sentence': self._generate_sentence(subject),
            'eq': self._generate_equation(subject).get('equation', 'A + B -> C'),
            'name': random.choice(['甲烷', '乙烷', '丙烷', '乙醇', '乙酸', '苯', '甲苯', '苯酚']),
            'num': str(self._generate_number(80, 150)),
            'topic': topic,
        }

        if subject in ['英语', '日语'] and topic == '词汇':
            vocab_item = self._generate_word(subject, difficulty)
            replacements['word'] = vocab_item['word']
            if 'kana' in vocab_item:
                replacements['kana'] = vocab_item['kana']

        question_text = template.format(**replacements)
        options, answer_text = self._generate_options(question_text, subject, topic, difficulty)

        correct_key = None
        for opt in options:
            if opt['text'] == answer_text:
                correct_key = opt['key']
                break
        if correct_key is None and options:
            correct_key = options[0]['key']

        return {
            'question_id': hashlib.md5(f"{question_text}{datetime.now()}{random.random()}".encode()).hexdigest()[:16],
            'question_text': question_text,
            'subject': subject,
            'topic': topic,
            'difficulty': difficulty,
            'options': options,
            'answer': answer_text,
            'correct_key': correct_key,
            'explanation': explanation,
            'generated_by': 'template',
        }

    def _generate_ai_question(self, subject, topic, difficulty):
        ai_engine = self._get_ai_engine()
        if ai_engine is None:
            return self._generate_question(subject, topic, difficulty, use_ai=False)

        try:
            prompt = f"""请生成一道{subject}{topic}的{difficulty}难度题目。 要求： 1. 题目类型为单选题 2. 提供4个选项（A、B、C、D），其中只有一个正确答案 3. 提供详细的解析 4. 返回格式为JSON，包含以下字段： - question_text: 题目内容 - options: 选项数组，每个元素包含key和text - answer: 正确答案内容 - correct_key: 正确选项的字母(A/B/C/D) - explanation: 解析内容  示例格式： {{ "question_text": "题目内容", "options": [ {{"key": "A", "text": "选项A"}}, {{"key": "B", "text": "选项B"}}, {{"key": "C", "text": "选项C"}}, {{"key": "D", "text": "选项D"}} ], "answer": "正确答案内容", "correct_key": "A", "explanation": "解析内容" }}"""

            response = ai_engine.generate(prompt)
            content = response.content

            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group(0)
                try:
                    result = json.loads(json_str)
                    return {
                        'question_id': hashlib.md5(f"{result.get('question_text', '')}{datetime.now()}".encode()).hexdigest()[:16],
                        'question_text': result.get('question_text', ''),
                        'subject': subject,
                        'topic': topic,
                        'difficulty': difficulty,
                        'options': result.get('options', []),
                        'answer': result.get('answer', ''),
                        'correct_key': result.get('correct_key', 'A'),
                        'explanation': result.get('explanation', ''),
                        'generated_by': 'ai',
                    }
                except json.JSONDecodeError:
                    logger.warning("AI生成的JSON解析失败，回退到模板生成")

        except Exception as e:
            logger.warning(f"AI题目生成失败，回退到模板生成: {e}")

        return self._generate_question(subject, topic, difficulty, use_ai=False)

    def _analyze_user_weaknesses(self, user_id, subject):
        weaknesses = []
        topic_weights = {}

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(''' SELECT question_content, wrong_count FROM wrong_questions WHERE user_id = ? AND subject = ? ORDER BY wrong_count DESC ''', (str(user_id), subject))
            wrong_questions = cursor.fetchall()

            for q_content, count in wrong_questions:
                for topic in self.QUESTION_TEMPLATES.get(subject, {}).keys():
                    if topic in q_content or q_content in topic:
                        topic_weights[topic] = topic_weights.get(topic, 0) + count

            cursor.execute(''' SELECT score FROM exam_results WHERE user_id = ? ''', (user_id,))
            scores = cursor.fetchall()
            if scores:
                avg_score = sum(s[0] for s in scores) / len(scores)
                if avg_score < 70:
                    for topic in self.QUESTION_TEMPLATES.get(subject, {}).keys():
                        if random.random() > 0.5:
                            topic_weights[topic] = topic_weights.get(topic, 0) + 3

            cursor.execute(''' SELECT topic, wrong_count FROM question_statistics WHERE user_id = ? AND subject = ? AND wrong_count > correct_count ''', (str(user_id), subject))
            stats = cursor.fetchall()
            for topic, wrong_count in stats:
                topic_weights[topic] = topic_weights.get(topic, 0) + wrong_count

            conn.close()

        except Exception as e:
            logger.error(f"分析用户薄弱点失败: {e}")

        sorted_topics = sorted(topic_weights.items(), key=lambda x: -x[1])
        return [t[0] for t in sorted_topics[:5]]

    def _calculate_adaptive_difficulty(self, user_id, subject):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(''' SELECT correct_count, wrong_count FROM question_statistics WHERE user_id = ? AND subject = ? ''', (str(user_id), subject))
            stats = cursor.fetchall()

            total_correct = sum(s[0] for s in stats)
            total_wrong = sum(s[1] for s in stats)
            total = total_correct + total_wrong

            conn.close()

            if total == 0:
                return 'medium'

            accuracy = total_correct / total
            if accuracy >= 0.85:
                return 'high'
            elif accuracy >= 0.6:
                return 'medium'
            else:
                return 'low'

        except Exception as e:
            logger.error(f"计算自适应难度失败: {e}")
            return 'medium'

    def generate_question_set(self, user_id, subject, count=10, difficulty=None, topic=None, use_ai=False):
        if subject not in self.SUBJECTS:
            return {'success': False, 'error': f'不支持的科目: {subject}'}

        if difficulty is None:
            difficulty = self._calculate_adaptive_difficulty(user_id, subject)

        weaknesses = self._analyze_user_weaknesses(user_id, subject)

        topics = []
        if topic:
            topics = [topic]
        elif weaknesses:
            topics = weaknesses[:3]
        else:
            topics = list(self.QUESTION_TEMPLATES.get(subject, {}).keys())

        if not topics:
            topics = ['综合']

        questions = []
        generated_topics = []
        for i in range(count):
            if topics:
                if len(generated_topics) >= len(topics) * 2:
                    generated_topics = []
                available_topics = [t for t in topics if generated_topics.count(t) < 2]
                if available_topics:
                    selected_topic = random.choice(available_topics)
                else:
                    selected_topic = random.choice(topics)
                generated_topics.append(selected_topic)
            else:
                selected_topic = '综合'

            q = self._generate_question(subject, selected_topic, difficulty, use_ai)
            questions.append(q)

        set_id = hashlib.md5(f"{user_id}{subject}{datetime.now()}{random.random()}".encode()).hexdigest()[:16]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(''' INSERT INTO generated_question_sets (set_id, user_id, subject, difficulty, topic, question_count, questions) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (set_id, str(user_id), subject, difficulty, topic or ','.join(topics), count, json.dumps(questions,
        ensure_ascii=False)))
        conn.commit()
        conn.close()

        return {
            'success': True,
            'set_id': set_id,
            'user_id': user_id,
            'subject': subject,
            'difficulty': difficulty,
            'topic': topic or ','.join(topics),
            'question_count': count,
            'questions': questions,
            'created_at': datetime.now().isoformat(),
        }

    def get_question_set(self, set_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM generated_question_sets WHERE set_id = ?', (set_id,))
        record = cursor.fetchone()

        if record:
            questions = json.loads(record[7]) if record[7] else []
            conn.close()
            return {
                'success': True,
                'set_id': record[1],
                'user_id': record[2],
                'subject': record[3],
                'difficulty': record[4],
                'topic': record[5],
                'question_count': record[6],
                'questions': questions,
                'created_at': record[8]
            }

        conn.close()
        return {'success': False, 'error': '题目集不存在'}

    def get_user_statistics(self, user_id, subject=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = 'SELECT * FROM question_statistics WHERE user_id = ?'
        params = [str(user_id)]

        if subject:
            query += ' AND subject = ?'
            params.append(subject)

        cursor.execute(query, params)
        records = cursor.fetchall()

        stats = []
        for r in records:
            stats.append({
                'subject': r[2],
                'topic': r[3],
                'question_type': r[4],
                'correct_count': r[5],
                'wrong_count': r[6],
                'accuracy': r[7],
                'last_practice_date': r[8]
            })

        conn.close()
        return {'success': True, 'statistics': stats}

    def update_statistics(self, user_id, subject, topic, question_type, is_correct):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(''' SELECT * FROM question_statistics WHERE user_id = ? AND subject = ? AND topic = ? AND question_type = ? ''', (str(user_id), subject, topic, question_type))

        record = cursor.fetchone()

        if record:
            correct_count = record[5] + (1 if is_correct else 0)
            wrong_count = record[6] + (0 if is_correct else 1)
            total = correct_count + wrong_count
            accuracy = correct_count / total if total > 0 else 0.0

            cursor.execute(''' UPDATE question_statistics SET correct_count = ?, wrong_count = ?, accuracy = ?, last_practice_date = ?, updated_at = ? WHERE id = ? ''', (correct_count, wrong_count, accuracy, datetime.now().isoformat(),
                  datetime.now().isoformat(), record[0]))
        else:
            correct_count = 1 if is_correct else 0
            wrong_count = 0 if is_correct else 1
            accuracy = correct_count / (correct_count + wrong_count) if (correct_count + wrong_count) > 0 else 0.0

            cursor.execute(''' INSERT INTO question_statistics (user_id, subject, topic, question_type, correct_count, wrong_count, accuracy, last_practice_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (str(user_id), subject, topic, question_type, correct_count, wrong_count,
                  accuracy, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return {'success': True}

    def get_subject_topics(self, subject):
        topics = list(self.QUESTION_TEMPLATES.get(subject, {}).keys())
        return {'success': True, 'topics': topics}

    def generate_review_set(self, user_id, subject, count=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(''' SELECT question_content, topic, wrong_count FROM wrong_questions WHERE user_id = ? AND subject = ? ORDER BY wrong_count DESC, last_wrong_date DESC LIMIT ? ''', (str(user_id), subject, count))
        wrong_questions = cursor.fetchall()

        questions = []
        for q_content, topic, wrong_count in wrong_questions:
            if topic and topic in self.QUESTION_TEMPLATES.get(subject, {}):
                q = self._generate_question(subject, topic, difficulty='medium')
                q['from_wrong'] = True
                q['original_wrong_count'] = wrong_count
                questions.append(q)

        conn.close()

        if len(questions) < count:
            remaining = count - len(questions)
            result = self.generate_question_set(user_id, subject, remaining, difficulty='medium')
            if result.get('success'):
                for q in result['questions']:
                    q['from_wrong'] = False
                questions.extend(result['questions'])

        set_id = hashlib.md5(f"review_{user_id}{subject}{datetime.now()}".encode()).hexdigest()[:16]

        return {
            'success': True,
            'set_id': set_id,
            'user_id': user_id,
            'subject': subject,
            'question_count': len(questions),
            'questions': questions,
            'created_at': datetime.now().isoformat(),
        }

    def get_overall_stats(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM generated_question_sets')
        total_sets = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM question_statistics')
        total_stats = cursor.fetchone()[0]

        cursor.execute('SELECT subject, COUNT(*) FROM generated_question_sets GROUP BY subject')
        by_subject = dict(cursor.fetchall())

        conn.close()

        return {
            'success': True,
            'total_sets': total_sets,
            'total_stats': total_stats,
            'by_subject': by_subject,
        }

    def delete_question_set(self, set_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM generated_question_sets WHERE set_id = ?', (set_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()

        return {'success': True, 'deleted': affected > 0}

    def generate_batch_questions(self, user_id, subjects, counts, difficulty='medium', use_ai=False):
        results = []
        
        for subject, count in zip(subjects, counts):
            if subject in self.SUBJECTS:
                result = self.generate_question_set(user_id, subject, count, difficulty, use_ai=use_ai)
                results.append({
                    'subject': subject,
                    'success': result.get('success'),
                    'question_count': result.get('question_count', 0),
                    'set_id': result.get('set_id'),
                    'error': result.get('error')
                })
            else:
                results.append({
                    'subject': subject,
                    'success': False,
                    'question_count': 0,
                    'error': f'不支持的科目: {subject}'
                })

        return {
            'success': True,
            'results': results,
            'total_generated': sum(r['question_count'] for r in results),
            'created_at': datetime.now().isoformat(),
        }

    def get_knowledge_point_stats(self, subject=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = ''' SELECT topic, SUM(correct_count) as total_correct, SUM(wrong_count) as total_wrong, COUNT(*) as question_count FROM question_statistics '''
        params = []
        
        if subject:
            query += ' WHERE subject = ?'
            params.append(subject)
        
        query += ' GROUP BY topic ORDER BY total_wrong DESC'
        
        cursor.execute(query, params)
        stats = cursor.fetchall()

        knowledge_stats = []
        for row in stats:
            topic = row[0]
            total_correct = row[1]
            total_wrong = row[2]
            question_count = row[3]
            total = total_correct + total_wrong
            accuracy = round(total_correct / total * 100, 2) if total > 0 else 0
            
            knowledge_stats.append({
                'topic': topic,
                'total_correct': total_correct,
                'total_wrong': total_wrong,
                'total_attempts': total,
                'question_count': question_count,
                'accuracy': accuracy,
                'weakness_level': self._calculate_weakness_level(total_wrong, accuracy)
            })

        conn.close()

        return {
            'success': True,
            'subject': subject or '全部科目',
            'knowledge_points': knowledge_stats,
            'total_topics': len(knowledge_stats),
            'weak_topics': [k for k in knowledge_stats if k['weakness_level'] >= 2],
            'strong_topics': [k for k in knowledge_stats if k['weakness_level'] == 0]
        }

    def _calculate_weakness_level(self, wrong_count, accuracy):
        if wrong_count >= 5 or accuracy < 50:
            return 3
        elif wrong_count >= 3 or accuracy < 70:
            return 2
        elif wrong_count >= 1 or accuracy < 85:
            return 1
        else:
            return 0

    def get_daily_generation_stats(self, days=30):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(''' SELECT DATE(created_at) as date, COUNT(*) as count, subject FROM generated_question_sets WHERE created_at >= DATE('now', ?) GROUP BY DATE(created_at), subject ORDER BY date DESC ''', (f'-{days} days',))
        
        stats = cursor.fetchall()
        
        daily_stats = {}
        for row in stats:
            date = row[0]
            count = row[1]
            subject = row[2]
            
            if date not in daily_stats:
                daily_stats[date] = {'total': 0, 'by_subject': {}}
            daily_stats[date]['total'] += count
            daily_stats[date]['by_subject'][subject] = daily_stats[date]['by_subject'].get(subject, 0) + count

        conn.close()

        sorted_dates = sorted(daily_stats.keys(), reverse=True)
        
        return {
            'success': True,
            'days': days,
            'daily_stats': [{
                'date': date,
                'total': daily_stats[date]['total'],
                'by_subject': daily_stats[date]['by_subject']
            } for date in sorted_dates],
            'total_generated': sum(daily_stats[d]['total'] for d in daily_stats)
        }


ai_question_generator = AIQuestionGenerator()