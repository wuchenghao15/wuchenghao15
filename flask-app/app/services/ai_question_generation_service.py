# -*- coding: utf-8 -*-
"""
AI智能题目生成服务
从文本内容自动生成考试题目，支持多种题型和难度级别
"""

import re
import random
import json
import logging
import sqlite3
import os
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AIQuestionGenerationService:
    """AI智能题目生成服务"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                   'split_databases/question.db')
        self.subject_keywords = {
            '语文': ['文章', '段落', '诗词', '文言文', '阅读理解', '写作', '成语', '词语', '修辞'],
            '数学': ['计算', '证明', '方程', '几何', '函数', '概率', '统计', '矩阵', '导数'],
            '英语': ['阅读理解', '完形填空', '语法', '词汇', '翻译', '听力', '写作'],
            '物理': ['力学', '电学', '光学', '热学', '声学', '能量', '运动', '力'],
            '化学': ['反应', '元素', '化合物', '方程式', '离子', '溶液', '酸碱'],
            '生物': ['细胞', '遗传', '进化', '生态', '代谢', '器官', '组织'],
            '历史': ['朝代', '事件', '人物', '战争', '改革', '条约', '文化'],
            '地理': ['气候', '地形', '河流', '城市', '资源', '人口', '环境'],
            '政治': ['哲学', '经济', '政治', '法律', '道德', '社会', '国家'],
            '科学': ['实验', '观察', '推理', '自然', '技术', '发现'],
            '日语': ['词汇', '语法', '听力', '阅读', '会话', '汉字']
        }
        
        self.question_types = ['单选题', '多选题', '判断题', '填空题', '简答题', '论述题']
        
        self.poetry_database = [
            {'title': '静夜思', 'author': '李白', 'content': '床前明月光，疑是地上霜。举头望明月，低头思故乡。'},
            {'title': '春晓', 'author': '孟浩然', 'content': '春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。'},
            {'title': '登鹳雀楼', 'author': '王之涣', 'content': '白日依山尽，黄河入海流。欲穷千里目，更上一层楼。'},
            {'title': '相思', 'author': '王维', 'content': '红豆生南国，春来发几枝。愿君多采撷，此物最相思。'},
            {'title': '悯农', 'author': '李绅', 'content': '锄禾日当午，汗滴禾下土。谁知盘中餐，粒粒皆辛苦。'},
            {'title': '江雪', 'author': '柳宗元', 'content': '千山鸟飞绝，万径人踪灭。孤舟蓑笠翁，独钓寒江雪。'},
            {'title': '望庐山瀑布', 'author': '李白', 'content': '日照香炉生紫烟，遥看瀑布挂前川。飞流直下三千尺，疑是银河落九天。'},
            {'title': '绝句', 'author': '杜甫', 'content': '两个黄鹂鸣翠柳，一行白鹭上青天。窗含西岭千秋雪，门泊东吴万里船。'},
            {'title': '游子吟', 'author': '孟郊', 'content': '慈母手中线，游子身上衣。临行密密缝，意恐迟迟归。谁言寸草心，报得三春晖。'},
            {'title': '送元二使安西', 'author': '王维', 'content': '渭城朝雨浥轻尘，客舍青青柳色新。劝君更尽一杯酒，西出阳关无故人。'},
            {'title': '出塞', 'author': '王昌龄', 'content': '秦时明月汉时关，万里长征人未还。但使龙城飞将在，不教胡马度阴山。'},
            {'title': '枫桥夜泊', 'author': '张继', 'content': '月落乌啼霜满天，江枫渔火对愁眠。姑苏城外寒山寺，夜半钟声到客船。'},
            {'title': '九月九日忆山东兄弟', 'author': '王维', 'content': '独在异乡为异客，每逢佳节倍思亲。遥知兄弟登高处，遍插茱萸少一人。'},
            {'title': '凉州词', 'author': '王翰', 'content': '葡萄美酒夜光杯，欲饮琵琶马上催。醉卧沙场君莫笑，古来征战几人回。'},
            {'title': '早发白帝城', 'author': '李白', 'content': '朝辞白帝彩云间，千里江陵一日还。两岸猿声啼不住，轻舟已过万重山。'},
            {'title': '望天门山', 'author': '李白', 'content': '天门中断楚江开，碧水东流至此回。两岸青山相对出，孤帆一片日边来。'},
            {'title': '赠汪伦', 'author': '李白', 'content': '李白乘舟将欲行，忽闻岸上踏歌声。桃花潭水深千尺，不及汪伦送我情。'},
            {'title': '黄鹤楼送孟浩然之广陵', 'author': '李白', 'content': '故人西辞黄鹤楼，烟花三月下扬州。孤帆远影碧空尽，唯见长江天际流。'},
            {'title': '绝句二首', 'author': '杜甫', 'content': '迟日江山丽，春风花草香。泥融飞燕子，沙暖睡鸳鸯。'},
            {'title': '春望', 'author': '杜甫', 'content': '国破山河在，城春草木深。感时花溅泪，恨别鸟惊心。烽火连三月，家书抵万金。白头搔更短，浑欲不胜簪。'}
        ]
        
        self.classic_literature = [
            {'title': '论语·学而', 'content': '子曰：\"学而时习之，不亦说乎？有朋自远方来，不亦乐乎？人不知而不愠，不亦君子乎？\"'},
            {'title': '论语·为政', 'content': '子曰：\"温故而知新，可以为师矣。\"'},
            {'title': '论语·述而', 'content': '子曰：\"三人行，必有我师焉。择其善者而从之，其不善者而改之。\"'},
            {'title': '道德经·第一章', 'content': '道可道，非常道；名可名，非常名。无名天地之始，有名万物之母。'},
            {'title': '道德经·第八章', 'content': '上善若水。水善利万物而不争，处众人之所恶，故几于道。'},
            {'title': '大学·开篇', 'content': '大学之道，在明明德，在亲民，在止于至善。'},
            {'title': '中庸·开篇', 'content': '天命之谓性，率性之谓道，修道之谓教。'},
            {'title': '孟子·告子上', 'content': '鱼，我所欲也；熊掌，亦我所欲也。二者不可得兼，舍鱼而取熊掌者也。'},
            {'title': '庄子·秋水', 'content': '秋水时至，百川灌河。泾流之大，两涘渚崖之间，不辩牛马。'}
        ]
        
        self.math_formulas = [
            {'name': '勾股定理', 'formula': 'a² + b² = c²', 'description': '直角三角形两直角边的平方和等于斜边的平方'},
            {'name': '二次方程求根公式', 'formula': 'x = (-b ± √(b²-4ac)) / 2a', 'description': '一元二次方程ax²+bx+c=0的求根公式'},
            {'name': '等差数列求和公式', 'formula': 'Sₙ = n(a₁ + aₙ) / 2', 'description': '等差数列前n项和公式'},
            {'name': '等比数列求和公式', 'formula': 'Sₙ = a₁(1-qⁿ) / (1-q)', 'description': '等比数列前n项和公式'},
            {'name': '三角函数基本关系', 'formula': 'sin²θ + cos²θ = 1', 'description': '正弦和余弦的平方和等于1'},
            {'name': '正弦定理', 'formula': 'a/sinA = b/sinB = c/sinC = 2R', 'description': '三角形各边与对角正弦的比值相等'},
            {'name': '余弦定理', 'formula': 'c² = a² + b² - 2ab·cosC', 'description': '三角形一边的平方等于另两边平方和减去它们乘积的两倍乘以夹角余弦'},
            {'name': '导数定义', 'formula': "f'(x) = lim(Δx→0) [f(x+Δx)-f(x)]/Δx", 'description': '函数在某点的导数定义'},
            {'name': '牛顿-莱布尼茨公式', 'formula': '∫ₐᵇ f(x)dx = F(b) - F(a)', 'description': '定积分与原函数的关系'},
            {'name': '圆的面积公式', 'formula': 'S = πr²', 'description': '圆的面积等于圆周率乘以半径的平方'},
            {'name': '球的体积公式', 'formula': 'V = (4/3)πr³', 'description': '球的体积公式'},
            {'name': '向量点积公式', 'formula': 'a·b = |a||b|cosθ', 'description': '两个向量的点积公式'},
            {'name': '排列组合公式', 'formula': 'P(n,k) = n!/(n-k)!', 'description': '从n个元素中选k个的排列数'},
            {'name': '二项式定理', 'formula': '(a+b)ⁿ = ΣC(n,k)a^(n-k)b^k', 'description': '二项式展开公式'},
            {'name': '概率公式', 'formula': 'P(A) = n(A)/n(S)', 'description': '事件A发生的概率公式'}
        ]
        
        self.essay_topics = [
            {'topic': '成长的足迹', 'type': '记叙文', 'hint': '回忆自己成长过程中的重要经历，表达对成长的感悟'},
            {'topic': '温暖', 'type': '记叙文', 'hint': '写一件让你感受到温暖的事，表达真挚的情感'},
            {'topic': '那一刻，我明白了', 'type': '记叙文', 'hint': '讲述一个让你有所领悟的瞬间，写出心灵的触动'},
            {'topic': '家乡的变化', 'type': '说明文', 'hint': '介绍家乡近年来的发展变化，展现时代进步'},
            {'topic': '我的理想', 'type': '议论文', 'hint': '阐述自己的理想，说明为什么有这样的理想以及如何实现'},
            {'topic': '诚信', 'type': '议论文', 'hint': '论述诚信的重要性，结合实例说明'},
            {'topic': '学会感恩', 'type': '议论文', 'hint': '谈谈对感恩的理解，说说你想感恩的人和事'},
            {'topic': '网络时代', 'type': '议论文', 'hint': '谈谈网络对我们生活的影响，辩证看待网络的利弊'},
            {'topic': '坚持', 'type': '议论文', 'hint': '论述坚持的力量，结合名人名言或实例'},
            {'topic': '责任', 'type': '议论文', 'hint': '谈谈你对责任的理解，作为学生或公民应承担的责任'},
            {'topic': '挫折', 'type': '议论文', 'hint': '论述如何面对挫折，挫折对人生的意义'},
            {'topic': '时间', 'type': '议论文', 'hint': '谈谈对时间的看法，如何珍惜时间'},
            {'topic': '合作', 'type': '议论文', 'hint': '论述合作的重要性，结合实例说明'},
            {'topic': '创新', 'type': '议论文', 'hint': '谈谈创新的意义，如何培养创新精神'},
            {'topic': '读书', 'type': '议论文', 'hint': '论述读书的益处，分享你的读书心得'}
        ]
        
        self.reading_passages = [
            {
                'title': '春',
                'content': '盼望着，盼望着，东风来了，春天的脚步近了。一切都像刚睡醒的样子，欣欣然张开了眼。山朗润起来了，水涨起来了，太阳的脸红起来了。小草偷偷地从土里钻出来，嫩嫩的，绿绿的。园子里，田野里，瞧去，一大片一大片满是的。坐着，躺着，打两个滚，踢几脚球，赛几趟跑，捉几回迷藏。风轻悄悄的，草软绵绵的。',
                'author': '朱自清',
                'genre': '散文'
            },
            {
                'title': '荷塘月色',
                'content': '曲曲折折的荷塘上面，弥望的是田田的叶子。叶子出水很高，像亭亭的舞女的裙。层层的叶子中间，零星地点缀着些白花，有袅娜地开着的，有羞涩地打着朵儿的；正如一粒粒的明珠，又如碧天里的星星，又如刚出浴的美人。微风过处，送来缕缕清香，仿佛远处高楼上渺茫的歌声似的。',
                'author': '朱自清',
                'genre': '散文'
            },
            {
                'title': '背影',
                'content': '我看见他戴着黑布小帽，穿着黑布大马褂，深青布棉袍，蹒跚地走到铁道边，慢慢探身下去，尚不大难。可是他穿过铁道，要爬上那边月台，就不容易了。他用两手攀着上面，两脚再向上缩；他肥胖的身子向左微倾，显出努力的样子。这时我看见他的背影，我的泪很快地流下来了。',
                'author': '朱自清',
                'genre': '散文'
            },
            {
                'title': '济南的冬天',
                'content': '对于一个在北平住惯的人，像我，冬天要是不刮风，便觉得是奇迹；济南的冬天是没有风声的。对于一个刚由伦敦回来的人，像我，冬天要能看得见日光，便觉得是怪事；济南的冬天是响晴的。自然，在热带的地方，日光是永远那么毒，响亮的天气，反有点叫人害怕。可是，在北中国的冬天，而能有温晴的天气，济南真得算个宝地。',
                'author': '老舍',
                'genre': '散文'
            },
            {
                'title': '白杨礼赞',
                'content': '白杨树实在是不平凡的，我赞美白杨树！当汽车在望不到边际的高原上奔驰，扑入你的视野的，是黄绿错综的一条大毯子；黄的是土，未开垦的荒地，几十万年前由伟大的自然力堆积成功的黄土高原的外壳；绿的呢，是人类劳力战胜自然的成果，是麦田。和风吹送，翻起了一轮一轮的绿波——这时你会真心佩服昔人所造的两个字“麦浪”，若不是妙手偶得，便确是经过锤炼的语言的精华。',
                'author': '茅盾',
                'genre': '散文'
            }
        ]
        
        logger.info("[AI题目生成服务] 初始化完成")
    
    def detect_subject(self, text: str) -> str:
        """根据文本内容自动检测科目"""
        text_lower = text.lower()
        
        for subject, keywords in self.subject_keywords.items():
            for keyword in keywords:
                if keyword in text or keyword.lower() in text_lower:
                    return subject
        
        return '其他'
    
    def extract_key_points(self, text: str) -> List[str]:
        """从文本中提取关键点"""
        sentences = re.split(r'[。！？；\n\r]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        key_points = []
        for sentence in sentences:
            if len(sentence) > 10:
                key_points.append(sentence[:100])
        
        return key_points[:20]
    
    def generate_single_choice(self, text: str, key_point: str) -> Dict:
        """生成单选题"""
        options = ['A', 'B', 'C', 'D']
        
        question = f"关于以下内容，哪个说法是正确的？\n\"{key_point[:80]}...\""
        
        correct_idx = random.randint(0, 3)
        correct_answer = options[correct_idx]
        
        wrong_answers = []
        for i in range(3):
            wrong_answers.append(f"错误选项{chr(65 + i)}")
        
        options_list = []
        idx = 0
        for i in range(4):
            if i == correct_idx:
                options_list.append({"option": options[i], "content": "正确答案选项"})
            else:
                options_list.append({"option": options[i], "content": wrong_answers[idx]})
                idx += 1
        
        return {
            'type': '单选题',
            'question': question,
            'options': options_list,
            'answer': correct_answer,
            'analysis': f"本题考查对文本内容的理解。正确答案为{correct_answer}，因为..."
        }
    
    def generate_multiple_choice(self, text: str, key_point: str) -> Dict:
        """生成多选题"""
        options = ['A', 'B', 'C', 'D', 'E']
        
        question = f"根据以下内容，哪些说法是正确的？（多选）\n\"{key_point[:80]}...\""
        
        correct_count = random.randint(2, 3)
        correct_indices = random.sample(range(5), correct_count)
        correct_answer = ''.join(sorted([options[i] for i in correct_indices]))
        
        options_list = []
        for i in range(5):
            is_correct = i in correct_indices
            options_list.append({
                "option": options[i],
                "content": "正确选项" if is_correct else f"错误选项{options[i]}",
                "is_correct": is_correct
            })
        
        return {
            'type': '多选题',
            'question': question,
            'options': options_list,
            'answer': correct_answer,
            'analysis': f"本题考查对文本内容的综合理解。正确答案为{correct_answer}。"
        }
    
    def generate_judgment(self, text: str, key_point: str) -> Dict:
        """生成判断题"""
        question = f"判断正误：\n\"{key_point[:80]}...\""
        
        is_true = random.choice([True, False])
        answer = '正确' if is_true else '错误'
        
        return {
            'type': '判断题',
            'question': question,
            'answer': answer,
            'analysis': f"本题考查对文本内容的判断能力。{answer}，因为..."
        }
    
    def generate_fill_blank(self, text: str, key_point: str) -> Dict:
        """生成填空题"""
        words = key_point.split()
        if len(words) < 3:
            return None
        
        blank_idx = random.randint(1, min(len(words) - 2, 3))
        blank_word = words[blank_idx]
        
        words[blank_idx] = '______'
        question = ' '.join(words)[:100]
        
        return {
            'type': '填空题',
            'question': question,
            'answer': blank_word,
            'analysis': f"本题考查对关键概念的记忆。正确答案是：{blank_word}"
        }
    
    def generate_short_answer(self, text: str, key_point: str) -> Dict:
        """生成简答题"""
        question = f"请简述以下内容的主要观点：\n\"{key_point[:80]}...\""
        
        return {
            'type': '简答题',
            'question': question,
            'answer': "参考答案：根据文本内容，主要观点包括...",
            'analysis': "本题考查对文本内容的归纳和总结能力。"
        }
    
    def generate_discussion(self, text: str, key_point: str) -> Dict:
        """生成论述题"""
        question = f"请结合以下内容，论述相关问题：\n\"{key_point[:80]}...\"\n\n要求：观点明确，论据充分，逻辑清晰，不少于200字。"
        
        return {
            'type': '论述题',
            'question': question,
            'answer': "参考答案：本题要求考生结合文本内容进行论述。答题要点包括：1. 观点阐述...",
            'analysis': "本题考查综合分析和论述能力，需要考生结合文本内容进行深入分析。"
        }
    
    def generate_poetry_fill_blank(self) -> Dict:
        """生成古诗文默写题"""
        poetry = random.choice(self.poetry_database)
        lines = poetry['content'].split('，')
        
        if len(lines) >= 2:
            blank_line_idx = random.randint(0, len(lines) - 1)
            lines_copy = lines.copy()
            answer = lines_copy[blank_line_idx].replace('。', '').replace('？', '').replace('！', '')
            lines_copy[blank_line_idx] = '________'
            question_text = '，'.join(lines_copy)
            
            return {
                'type': '默写题',
                'question': f"请补全下列诗句：\n《{poetry['title']}》- {poetry['author']}\n{question_text}",
                'answer': answer,
                'analysis': f"本题考查对古诗《{poetry['title']}》的背诵和默写能力。正确答案出自{poetry['author']}的这首诗。"
            }
        return None
    
    def generate_poetry_translation(self) -> Dict:
        """生成古诗文翻译题"""
        poetry = random.choice(self.poetry_database)
        lines = poetry['content'].split('，')
        selected_line = random.choice(lines).replace('。', '').replace('？', '').replace('！', '')
        
        return {
            'type': '翻译题',
            'question': f"请翻译下列诗句：\n《{poetry['title']}》- {poetry['author']}\n\"{selected_line}\"",
            'answer': f"参考答案：{selected_line}（请结合诗句意境进行翻译）",
            'analysis': f"本题考查对古诗《{poetry['title']}》中诗句的理解和翻译能力。"
        }
    
    def generate_poetry_analysis(self) -> Dict:
        """生成古诗文赏析题"""
        poetry = random.choice(self.poetry_database)
        
        analysis_types = [
            "请分析这首诗的主题思想",
            "请赏析诗中的修辞手法",
            "请分析诗人表达的情感",
            "请谈谈这首诗的艺术特色"
        ]
        
        return {
            'type': '赏析题',
            'question': f"阅读下列古诗，完成题目：\n\n《{poetry['title']}》\n{poetry['author']}\n{poetry['content']}\n\n{random.choice(analysis_types)}",
            'answer': f"参考答案：本题考查对《{poetry['title']}》的深入理解和赏析能力。答题要点包括...",
            'analysis': f"本题考查古诗词鉴赏能力，要求考生结合诗句内容进行分析。"
        }
    
    def generate_classic_text_question(self) -> Dict:
        """生成古文经典解析题"""
        classic = random.choice(self.classic_literature)
        
        question_types = [
            ('单选题', f"下列对《{classic['title']}》中句子的理解，正确的是："),
            ('翻译题', f"请翻译《{classic['title']}》中的这句话：\"{classic['content'][:50]}...\""),
            ('简答题', f"请简述《{classic['title']}》中这段话的含义")
        ]
        
        q_type, q_text = random.choice(question_types)
        
        return {
            'type': q_type,
            'question': q_text,
            'answer': f"参考答案：本题考查对经典文献《{classic['title']}》的理解。",
            'analysis': f"本题考查对中国古代经典文献的阅读理解能力。"
        }
    
    def generate_essay_topic(self) -> Dict:
        """生成作文题目"""
        essay = random.choice(self.essay_topics)
        
        return {
            'type': '作文题',
            'question': f"请以\"{essay['topic']}\"为题，写一篇{essay['type']}。\n\n要求：\n1. 立意自定，文体自选（诗歌除外）\n2. 不少于{random.choice(['600', '800', '1000'])}字\n3. {essay['hint']}",
            'answer': f"写作思路参考：\n1. 审题立意：理解\"{essay['topic']}\"的内涵\n2. 选材构思：选择恰当的素材\n3. 结构安排：合理组织文章结构\n4. 语言表达：运用恰当的表达方式",
            'analysis': f"本题考查{essay['type']}写作能力，要求围绕\"{essay['topic']}\"展开，表达真情实感。"
        }
    
    def generate_reading_comprehension(self) -> Dict:
        """生成阅读理解题"""
        passage = random.choice(self.reading_passages)
        
        question_types = [
            f"本文的中心思想是什么？",
            f"文中\"{passage['content'][20:40]}...\"这句话表达了作者怎样的情感？",
            f"分析文中使用的修辞手法及其效果",
            f"结合全文，谈谈你对\"{passage['content'][40:60]}...\"这句话的理解",
            f"本文的写作特点是什么？"
        ]
        
        return {
            'type': '阅读理解',
            'question': f"阅读下面的文章，完成题目：\n\n【{passage['genre']}】《{passage['title']}》\n作者：{passage['author']}\n\n{passage['content']}\n\n{random.choice(question_types)}",
            'answer': f"参考答案：本题考查对散文《{passage['title']}》的阅读理解能力。答题要点包括...",
            'analysis': f"本题考查现代文阅读理解能力，要求考生准确理解文章内容和作者的写作意图。"
        }
    
    def generate_formula_application(self) -> Dict:
        """生成公式运用题"""
        formula = random.choice(self.math_formulas)
        
        problem_scenarios = [
            f"已知直角三角形的两条直角边分别为3和4，利用{formula['name']}计算斜边长度。",
            f"请举例说明{formula['name']}在实际生活中的应用，并写出具体计算过程。",
            f"推导{formula['name']}的公式，并说明其适用条件。",
            f"利用{formula['name']}解决以下问题：（请结合公式特点设计具体问题）",
            f"比较{formula['name']}与相关公式的联系与区别。"
        ]
        
        return {
            'type': '公式运用',
            'question': f"公式：{formula['formula']}\n名称：{formula['name']}\n{formula['description']}\n\n{random.choice(problem_scenarios)}",
            'answer': f"参考答案：本题考查{formula['name']}的理解和运用能力。解题步骤包括...",
            'analysis': f"本题考查数学公式的理解和实际运用能力，要求考生掌握{formula['name']}的推导和应用场景。"
        }
    
    def generate_case_analysis(self, subject: str = None) -> Dict:
        """生成经典案例分析题"""
        subjects = ['数学', '物理', '化学', '语文']
        if not subject:
            subject = random.choice(subjects)
        
        case_templates = {
            '数学': {
                'question': "请分析以下数学经典案例：\n\n案例：在平面直角坐标系中，已知点A(0,0)、B(3,0)、C(0,4)，求三角形ABC的面积和外接圆方程。\n\n要求：1. 写出解题步骤；2. 说明用到的数学原理；3. 总结解题思路。",
                'answer': "参考答案：本题考查三角形面积计算和圆的方程知识。解题步骤包括...",
                'analysis': "本题通过经典几何案例考查数学知识的综合运用能力。"
            },
            '物理': {
                'question': "请分析以下物理经典案例：\n\n案例：一辆汽车以20m/s的速度行驶，司机发现前方障碍物后紧急刹车，加速度为-5m/s²。求：1. 汽车刹车后3秒时的速度；2. 汽车刹车后5秒内的位移。\n\n要求：1. 写出物理公式；2. 代入数值计算；3. 分析结果的物理意义。",
                'answer': "参考答案：本题考查匀变速直线运动知识。解题步骤包括...",
                'analysis': "本题通过经典运动学案例考查物理知识的实际应用能力。"
            },
            '化学': {
                'question': "请分析以下化学经典案例：\n\n案例：将10g氢氧化钠固体溶解在90g水中，配制氢氧化钠溶液。求：1. 溶液的质量分数；2. 若要配制100mL 0.5mol/L的氢氧化钠溶液，需要多少克氢氧化钠？\n\n要求：1. 写出计算公式；2. 代入数值计算；3. 说明实验操作步骤。",
                'answer': "参考答案：本题考查溶液浓度计算知识。解题步骤包括...",
                'analysis': "本题通过经典溶液配制案例考查化学计算和实验操作能力。"
            },
            '语文': {
                'question': "请分析以下文学经典案例：\n\n案例：鲁迅在《呐喊》中通过阿Q这一形象，揭示了怎样的社会现象？\n\n要求：1. 分析阿Q的人物形象；2. 结合具体情节说明；3. 探讨作品的社会意义。",
                'answer': "参考答案：本题考查文学作品分析能力。答题要点包括...",
                'analysis': "本题通过经典文学作品考查文学鉴赏和分析能力。"
            }
        }
        
        template = case_templates.get(subject, case_templates['数学'])
        return {
            'type': '案例分析',
            'question': template['question'],
            'answer': template['answer'],
            'analysis': template['analysis']
        }
    
    def generate_adult_education_question(self) -> Dict:
        """生成成人教育技能题目"""
        skill_categories = [
            {
                'category': '职场沟通',
                'question': "在工作中，你需要向领导汇报一个复杂的项目进展。请简述汇报的要点和注意事项。",
                'answer': "参考答案：汇报要点包括：1. 项目进展概述；2. 已完成工作；3. 遇到的问题；4. 下一步计划。注意事项包括：突出重点、数据支撑、逻辑清晰。",
                'analysis': "本题考查职场沟通能力，要求考生掌握工作汇报的技巧和方法。"
            },
            {
                'category': '时间管理',
                'question': "请介绍至少三种时间管理方法，并说明如何应用在日常工作中。",
                'answer': "参考答案：常见的时间管理方法包括：1. 四象限法；2. Pomodoro技术；3. GTD工作流程。应用要点包括...",
                'analysis': "本题考查时间管理技能，要求考生掌握有效的时间管理方法。"
            },
            {
                'category': '团队协作',
                'question': "在团队合作中，当遇到意见分歧时，你会如何处理？请举例说明。",
                'answer': "参考答案：处理方法包括：1. 倾听各方意见；2. 分析利弊；3. 寻求共识；4. 必要时请上级协调。",
                'analysis': "本题考查团队协作能力，要求考生掌握处理团队冲突的技巧。"
            },
            {
                'category': '计算机应用',
                'question': "请简述Excel中VLOOKUP函数的用法，并举例说明其在数据处理中的应用。",
                'answer': "参考答案：VLOOKUP函数用于在表格中查找数据。语法：VLOOKUP(查找值, 查找区域, 返回列数, 匹配类型)。应用场景包括数据匹配、报表生成等。",
                'analysis': "本题考查办公软件应用技能，要求考生掌握常用Excel函数的使用。"
            }
        ]
        
        skill = random.choice(skill_categories)
        return {
            'type': '技能题',
            'question': f"【{skill['category']}】{skill['question']}",
            'answer': skill['answer'],
            'analysis': skill['analysis']
        }
    
    def generate_college_admission_question(self) -> Dict:
        """生成自主招生题目"""
        admission_topics = [
            {
                'topic': '数学竞赛',
                'question': "已知函数f(x) = x³ - 3x + a，若f(x)在区间[-2, 2]上有两个零点，求实数a的取值范围。",
                'answer': "参考答案：a ∈ (-2, 2)",
                'analysis': "本题考查三次函数的零点问题，需要利用导数分析函数单调性和极值。"
            },
            {
                'topic': '物理竞赛',
                'question': "如图所示，质量为m的小球从光滑斜面顶端由静止滑下，斜面倾角为θ，斜面长度为L。求小球到达斜面底端时的速度大小。",
                'answer': "参考答案：v = √(2gLsinθ)",
                'analysis': "本题考查机械能守恒定律的应用，重力势能转化为动能。"
            },
            {
                'topic': '化学竞赛',
                'question': "在标准状况下，将22.4L的HCl气体溶于水配制成1L溶液。求该溶液的物质的量浓度。",
                'answer': "参考答案：1mol/L",
                'analysis': "本题考查气体摩尔体积和物质的量浓度的计算。"
            },
            {
                'topic': '生物竞赛',
                'question': "请简述DNA复制的过程，并说明其生物学意义。",
                'answer': "参考答案：DNA复制包括解旋、引物合成、延伸和终止四个阶段，保证了遗传信息的准确传递。",
                'analysis': "本题考查DNA复制的分子机制。"
            },
            {
                'topic': '综合能力',
                'question': "请结合实际，谈谈科技创新对社会发展的影响。",
                'answer': "参考答案：科技创新推动生产力发展、改变生活方式、促进社会进步。",
                'analysis': "本题考查综合分析和表达能力。"
            }
        ]
        
        topic = random.choice(admission_topics)
        return {
            'type': '自主招生',
            'question': f"【{topic['topic']}】{topic['question']}",
            'answer': topic['answer'],
            'analysis': topic['analysis']
        }
    
    def generate_competition_question(self) -> Dict:
        """生成专项竞赛试题"""
        competition_topics = [
            {
                'topic': '奥数',
                'question': "求满足x² + y² = z²的正整数解（勾股数），并证明有无穷多组解。",
                'answer': "参考答案：取x = m² - n², y = 2mn, z = m² + n²，其中m > n > 0，可得无穷多组解。",
                'analysis': "本题考查数论中的勾股数问题。"
            },
            {
                'topic': '物理奥赛',
                'question': "一个质点在光滑水平面上做匀速圆周运动，向心力由绳子提供。若绳子突然断裂，质点将如何运动？",
                'answer': "参考答案：质点将沿切线方向做匀速直线运动。",
                'analysis': "本题考查牛顿第一定律和圆周运动。"
            },
            {
                'topic': '化学奥赛',
                'question': "配平下列化学方程式：Fe + O₂ → Fe₂O₃",
                'answer': "参考答案：4Fe + 3O₂ = 2Fe₂O₃",
                'analysis': "本题考查化学方程式配平。"
            },
            {
                'topic': '信息学',
                'question': "使用二分查找算法在有序数组中查找某个元素，最坏情况下的时间复杂度是多少？",
                'answer': "参考答案：O(log n)",
                'analysis': "本题考查算法复杂度分析。"
            },
            {
                'topic': '英语竞赛',
                'question': "Translate the following sentence into English: 科技改变生活。",
                'answer': "参考答案：Technology changes life.",
                'analysis': "本题考查翻译能力。"
            }
        ]
        
        topic = random.choice(competition_topics)
        return {
            'type': '竞赛题',
            'question': f"【{topic['topic']}】{topic['question']}",
            'answer': topic['answer'],
            'analysis': topic['analysis']
        }
    
    def generate_exam_real_question(self) -> Dict:
        """生成历年高考中考真题"""
        exam_topics = [
            {
                'year': '2023',
                'subject': '数学',
                'type': '高考',
                'question': "已知等差数列{an}的前n项和为Sn，若a₁ = 2，公差d = 3，求S₁₀。",
                'answer': "参考答案：S₁₀ = 10×2 + 10×9×3/2 = 155",
                'analysis': "本题考查等差数列求和公式。"
            },
            {
                'year': '2022',
                'subject': '物理',
                'type': '中考',
                'question': "一辆汽车以20m/s的速度行驶，司机看到前方红灯后立即刹车，加速度为-5m/s²。求汽车刹车后4秒内的位移。",
                'answer': "参考答案：s = vt + ½at² = 20×4 - ½×5×16 = 40m",
                'analysis': "本题考查匀变速直线运动。"
            },
            {
                'year': '2023',
                'subject': '语文',
                'type': '高考',
                'question': "阅读下面的诗歌，完成题目。《登高》杜甫\n风急天高猿啸哀，渚清沙白鸟飞回。无边落木萧萧下，不尽长江滚滚来。",
                'answer': "参考答案：本题考查诗歌鉴赏，分析意境、手法等。",
                'analysis': "本题考查古诗词鉴赏能力。"
            },
            {
                'year': '2022',
                'subject': '英语',
                'type': '中考',
                'question': "Choose the correct answer: He _____ to school every day. A) go B) goes C) going D) went",
                'answer': "参考答案：B",
                'analysis': "本题考查一般现在时态。"
            },
            {
                'year': '2023',
                'subject': '化学',
                'type': '高考',
                'question': "写出下列反应的化学方程式：氢氧化钠与盐酸反应。",
                'answer': "参考答案：NaOH + HCl = NaCl + H₂O",
                'analysis': "本题考查酸碱中和反应。"
            }
        ]
        
        topic = random.choice(exam_topics)
        return {
            'type': '真题',
            'question': f"【{topic['year']}{topic['type']}-{topic['subject']}】{topic['question']}",
            'answer': topic['answer'],
            'analysis': topic['analysis']
        }
    
    def generate_key_review_question(self) -> Dict:
        """生成重点复习题"""
        review_topics = [
            {
                'subject': '数学',
                'key_point': '函数单调性',
                'question': "设函数f(x) = x³ - 3x，求f(x)的单调递增区间和单调递减区间。",
                'answer': "参考答案：增区间(-∞, -1)和(1, +∞)，减区间(-1, 1)",
                'analysis': "本题考查利用导数求函数单调性。"
            },
            {
                'subject': '物理',
                'key_point': '牛顿运动定律',
                'question': "质量为2kg的物体受到10N的水平推力作用，在光滑水平面上运动。求物体的加速度。",
                'answer': "参考答案：a = F/m = 10/2 = 5m/s²",
                'analysis': "本题考查牛顿第二定律。"
            },
            {
                'subject': '语文',
                'key_point': '文言文虚词',
                'question': "下列句子中'之'的用法与其他三项不同的是：A)吾欲之南海 B)送孟浩然之广陵 C)辍耕之垄上 D)予独爱莲之出淤泥而不染",
                'answer': "参考答案：D（D项为取消句子独立性，其他三项为动词'到'）",
                'analysis': "本题考查文言虚词'之'的用法。"
            },
            {
                'subject': '英语',
                'key_point': '非谓语动词',
                'question': "_____ the book, he found it very interesting. A) Read B) Reading C) To read D) Readed",
                'answer': "参考答案：B",
                'analysis': "本题考查现在分词作状语。"
            },
            {
                'subject': '化学',
                'key_point': '化学反应速率',
                'question': "影响化学反应速率的因素有哪些？请举例说明。",
                'answer': "参考答案：温度、浓度、压强、催化剂等。",
                'analysis': "本题考查化学反应速率的影响因素。"
            }
        ]
        
        topic = random.choice(review_topics)
        return {
            'type': '重点复习',
            'question': f"【{topic['subject']}-{topic['key_point']}】{topic['question']}",
            'answer': topic['answer'],
            'analysis': topic['analysis']
        }
    
    def generate_international_competition_question(self) -> Dict:
        """生成国际竞赛真题"""
        international_topics = [
            {
                'competition': 'IMO',
                'year': '2023',
                'question': "Let n be a positive integer. Prove that there exists a positive integer k such that n divides 2ᵏ - 1.",
                'answer': "参考答案：利用鸽巢原理证明。",
                'analysis': "本题考查数论中的阶的概念。"
            },
            {
                'competition': 'IPhO',
                'year': '2022',
                'question': "A particle moves in a circular path of radius R with constant speed v. What is the magnitude of its centripetal acceleration?",
                'answer': "参考答案：a = v²/R",
                'analysis': "本题考查圆周运动的向心加速度。"
            },
            {
                'competition': 'IChO',
                'year': '2023',
                'question': "Calculate the pH of a 0.1mol/L solution of acetic acid (Ka = 1.8×10⁻⁵).",
                'answer': "参考答案：pH ≈ 2.87",
                'analysis': "本题考查弱酸的电离平衡。"
            },
            {
                'competition': 'IBO',
                'year': '2022',
                'question': "Describe the process of photosynthesis and explain its significance.",
                'answer': "参考答案：光合作用包括光反应和暗反应两个阶段，将光能转化为化学能。",
                'analysis': "本题考查光合作用的过程。"
            },
            {
                'competition': 'IOI',
                'year': '2023',
                'question': "Design an algorithm to find the shortest path in a weighted graph.",
                'answer': "参考答案：使用Dijkstra算法。",
                'analysis': "本题考查图论中的最短路径算法。"
            }
        ]
        
        topic = random.choice(international_topics)
        return {
            'type': '国际竞赛',
            'question': f"【{topic['competition']} {topic['year']}】{topic['question']}",
            'answer': topic['answer'],
            'analysis': topic['analysis']
        }
    
    def generate_literature_analysis_question(self) -> Dict:
        """生成文科经典案例文章解析与阅读理解"""
        literature_topics = [
            {
                'work': '红楼梦',
                'author': '曹雪芹',
                'question': "分析林黛玉的人物形象及其悲剧命运的原因。",
                'answer': "参考答案：林黛玉是一个才情出众、敏感多疑的女性形象，她的悲剧源于封建礼教的束缚和个人性格的弱点。",
                'analysis': "本题考查古典文学名著的人物分析能力。"
            },
            {
                'work': '呐喊',
                'author': '鲁迅',
                'question': "分析阿Q精神胜利法的内涵及其社会意义。",
                'answer': "参考答案：阿Q精神胜利法是一种自我安慰的心理机制，反映了当时国民的劣根性。",
                'analysis': "本题考查现代文学作品的主题分析。"
            },
            {
                'work': '围城',
                'author': '钱钟书',
                'question': "谈谈你对'围城'这一象征意义的理解。",
                'answer': "参考答案：围城象征着人生的困境，城外的人想进去，城里的人想出来。",
                'analysis': "本题考查文学作品的象征手法。"
            },
            {
                'work': '平凡的世界',
                'author': '路遥',
                'question': "分析孙少平的成长历程及其体现的时代精神。",
                'answer': "参考答案：孙少平从农村青年成长为有理想、有追求的青年，体现了改革开放初期的时代精神。",
                'analysis': "本题考查当代文学作品的人物分析。"
            },
            {
                'work': '古文观止',
                'author': '吴楚材',
                'question': "分析《岳阳楼记》中'先天下之忧而忧，后天下之乐而乐'的思想内涵。",
                'answer': "参考答案：这句话表达了作者忧国忧民的情怀和以天下为己任的担当精神。",
                'analysis': "本题考查古代散文的思想内涵分析。"
            }
        ]
        
        topic = random.choice(literature_topics)
        return {
            'type': '文学分析',
            'question': f"【{topic['work']}-{topic['author']}】{topic['question']}",
            'answer': topic['answer'],
            'analysis': topic['analysis']
        }
    
    def generate_formula_skill_question(self) -> Dict:
        """生成基础公式巧用与运用试题"""
        formula_skill_topics = [
            {
                'formula': '完全平方公式',
                'question': "利用完全平方公式计算：(a + b)² - (a - b)²",
                'answer': "参考答案：(a² + 2ab + b²) - (a² - 2ab + b²) = 4ab",
                'analysis': "本题考查完全平方公式的灵活运用。"
            },
            {
                'formula': '均值不等式',
                'question': "已知x > 0，求x + 1/x的最小值。",
                'answer': "参考答案：由均值不等式，x + 1/x ≥ 2√(x·1/x) = 2，当x = 1时取等号。",
                'analysis': "本题考查均值不等式的应用。"
            },
            {
                'formula': '勾股定理',
                'question': "已知直角三角形的斜边为10，一条直角边为6，求另一条直角边的长度。",
                'answer': "参考答案：由勾股定理，另一条直角边 = √(10² - 6²) = √64 = 8",
                'analysis': "本题考查勾股定理的直接应用。"
            },
            {
                'formula': '欧姆定律',
                'question': "一个电阻为10Ω的导体，两端电压为20V，通过的电流是多少？",
                'answer': "参考答案：由欧姆定律，I = U/R = 20/10 = 2A",
                'analysis': "本题考查欧姆定律的应用。"
            },
            {
                'formula': '牛顿第二定律',
                'question': "质量为5kg的物体受到25N的合力作用，求物体的加速度。",
                'answer': "参考答案：由牛顿第二定律，a = F/m = 25/5 = 5m/s²",
                'analysis': "本题考查牛顿第二定律的应用。"
            }
        ]
        
        topic = random.choice(formula_skill_topics)
        return {
            'type': '公式巧用',
            'question': f"【{topic['formula']}】{topic['question']}",
            'answer': topic['answer'],
            'analysis': topic['analysis']
        }
    
    def generate_ai_foundation_question(self) -> Dict:
        """生成AI基础模型专项练习题"""
        ai_topics = [
            {
                'topic': '神经网络基础',
                'question': "请解释神经网络中前向传播和反向传播的基本原理，并说明它们在模型训练中的作用。",
                'answer': "参考答案：前向传播是指输入数据通过网络层计算得到输出的过程；反向传播是指根据损失函数计算梯度并更新参数的过程。两者共同构成神经网络的训练过程。",
                'analysis': "本题考查神经网络基础知识，要求考生理解深度学习的核心概念。"
            },
            {
                'topic': '卷积神经网络',
                'question': "请说明卷积神经网络（CNN）中卷积层、池化层和全连接层的作用，并举例说明CNN在图像处理中的应用。",
                'answer': "参考答案：卷积层用于提取特征；池化层用于降维和特征选择；全连接层用于分类。CNN在图像识别、目标检测等领域有广泛应用。",
                'analysis': "本题考查CNN的基本原理和应用，要求考生掌握深度学习在计算机视觉中的应用。"
            },
            {
                'topic': 'Transformer架构',
                'question': "请解释Transformer架构中的自注意力机制，并说明它相比传统RNN的优势。",
                'answer': "参考答案：自注意力机制通过计算序列中每个位置与其他位置的关联程度来捕捉长距离依赖关系。相比RNN，Transformer可以并行计算，处理长序列能力更强。",
                'analysis': "本题考查Transformer架构的核心概念，要求考生理解现代NLP模型的基础。"
            },
            {
                'topic': '模型评估',
                'question': "请说明分类任务中常用的评估指标（准确率、精确率、召回率、F1分数）的定义和适用场景。",
                'answer': "参考答案：准确率是正确分类的比例；精确率是预测为正例中真正正例的比例；召回率是真正正例中被正确预测的比例；F1是精确率和召回率的调和平均。",
                'analysis': "本题考查机器学习模型评估知识，要求考生掌握分类任务的评价方法。"
            }
        ]
        
        topic = random.choice(ai_topics)
        return {
            'type': 'AI专项',
            'question': f"【{topic['topic']}】{topic['question']}",
            'answer': topic['answer'],
            'analysis': topic['analysis']
        }
    
    def generate_specialized_question(self, question_type: str) -> Dict:
        """根据专项类型生成题目"""
        type_map = {
            '默写题': self.generate_poetry_fill_blank,
            '翻译题': self.generate_poetry_translation,
            '赏析题': self.generate_poetry_analysis,
            '古文解析': self.generate_classic_text_question,
            '作文题': self.generate_essay_topic,
            '阅读理解': self.generate_reading_comprehension,
            '公式运用': self.generate_formula_application,
            '案例分析': self.generate_case_analysis,
            '技能题': self.generate_adult_education_question,
            'AI专项': self.generate_ai_foundation_question,
            '自主招生': self.generate_college_admission_question,
            '竞赛题': self.generate_competition_question,
            '真题': self.generate_exam_real_question,
            '重点复习': self.generate_key_review_question,
            '国际竞赛': self.generate_international_competition_question,
            '文学分析': self.generate_literature_analysis_question,
            '公式巧用': self.generate_formula_skill_question
        }
        
        generator = type_map.get(question_type)
        if generator:
            return generator()
        return None
    
    def generate_questions(self, text: str, count: int = 10, types: Optional[List[str]] = None, 
                          difficulty: str = 'medium', subject: str = None) -> Dict:
        """
        从文本生成题目
        :param text: 输入文本
        :param count: 生成题目数量
        :param types: 题型列表
        :param difficulty: 难度等级
        :param subject: 科目（自动检测或指定）
        """
        if not types:
            types = self.question_types
        
        if not subject:
            subject = self.detect_subject(text)
        
        key_points = self.extract_key_points(text)
        
        questions = []
        type_weights = {
            '单选题': 30,
            '多选题': 20,
            '判断题': 15,
            '填空题': 15,
            '简答题': 12,
            '论述题': 8
        }
        
        specialized_types = ['默写题', '翻译题', '赏析题', '古文解析', '作文题', 
                            '阅读理解', '公式运用', '案例分析', '技能题', 'AI专项',
                            '自主招生', '竞赛题', '真题', '重点复习', '国际竞赛',
                            '文学分析', '公式巧用']
        
        available_types = []
        for t in types:
            if t in type_weights or t in specialized_types:
                available_types.append(t)
        
        if not available_types:
            available_types = ['单选题', '多选题', '判断题']
        
        for _ in range(count):
            question = None
            
            has_text = key_points and len(key_points) > 0
            
            type_choice = random.choice(available_types)
            
            if type_choice in specialized_types:
                question = self.generate_specialized_question(type_choice)
            elif has_text:
                key_point = random.choice(key_points)
                if type_choice == '单选题':
                    question = self.generate_single_choice(text, key_point)
                elif type_choice == '多选题':
                    question = self.generate_multiple_choice(text, key_point)
                elif type_choice == '判断题':
                    question = self.generate_judgment(text, key_point)
                elif type_choice == '填空题':
                    question = self.generate_fill_blank(text, key_point)
                elif type_choice == '简答题':
                    question = self.generate_short_answer(text, key_point)
                elif type_choice == '论述题':
                    question = self.generate_discussion(text, key_point)
            else:
                question = self.generate_specialized_question('单选题')
            
            if question:
                question['difficulty'] = difficulty
                question['subject'] = subject
                question['generated_at'] = datetime.now().isoformat()
                questions.append(question)
        
        return {
            'success': True,
            'data': {
                'subject': subject,
                'total_questions': len(questions),
                'types': types,
                'difficulty': difficulty,
                'questions': questions
            }
        }
    
    def save_questions(self, questions: List[Dict], user_id: int = 0) -> Dict:
        """保存生成的题目到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            for q in questions:
                options_str = json.dumps(q.get('options', []), ensure_ascii=False)
                
                cursor.execute('''
                    INSERT INTO questions (subject, type, question, options, answer, 
                                          analysis, difficulty, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    q.get('subject', '其他'),
                    q.get('type', '单选题'),
                    q.get('question', ''),
                    options_str,
                    q.get('answer', ''),
                    q.get('analysis', ''),
                    q.get('difficulty', 'medium'),
                    datetime.now().isoformat()
                ))
                
                saved_count += 1
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'成功保存 {saved_count} 道题目',
                'saved_count': saved_count
            }
        
        except Exception as e:
            logger.error(f"[保存题目失败] {e}")
            return {
                'success': False,
                'message': f'保存失败: {e}'
            }
    
    def get_generation_stats(self) -> Dict:
        """获取生成统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM questions")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT type, COUNT(*) FROM questions GROUP BY type")
            by_type = {row[0]: row[1] for row in cursor.fetchall()}
            
            cursor.execute("SELECT subject, COUNT(*) FROM questions GROUP BY subject ORDER BY COUNT(*) DESC LIMIT 10")
            by_subject = [{'subject': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'success': True,
                'data': {
                    'total_questions': total,
                    'by_type': by_type,
                    'top_subjects': by_subject
                }
            }
        except Exception as e:
            logger.error(f"[获取统计失败] {e}")
            return {
                'success': False,
                'message': str(e)
            }


ai_question_generation_service = AIQuestionGenerationService()
