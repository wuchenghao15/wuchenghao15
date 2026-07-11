#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成人教育与K12题库拓展服务
支持成人高考、自考、职业资格考试、中小学教育等全学段题库
"""

import os
import json
import time
import threading
import random
import uuid
from typing import Dict, List, Optional, Tuple
from enum import Enum

from app.utils.logging import logger


class EducationStage(Enum):
    PRIMARY = "primary"
    JUNIOR_HIGH = "junior_high"
    SENIOR_HIGH = "senior_high"
    VOCATIONAL = "vocational"
    COLLEGE = "college"
    UNDERGRADUATE = "undergraduate"
    ADULT_EXAM = "adult_exam"
    SELF_EXAM = "self_exam"
    PROFESSIONAL_CERT = "professional_cert"


class Subject(Enum):
    CHINESE = "chinese"
    MATH = "math"
    ENGLISH = "english"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    POLITICS = "politics"
    COMPUTER = "computer"
    ECONOMICS = "economics"
    LAW = "law"
    MANAGEMENT = "management"
    ACCOUNTING = "accounting"


class QuestionType(Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    CALCULATION = "calculation"
    CASE_STUDY = "case_study"


class AdultK12QuestionBankService:
    """成人教育与K12题库拓展服务"""

    def __init__(self):
        self._questions: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self._db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'adult_k12_question_bank.json')
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._load_questions()
        self._init_default_questions()
        logger.info(f"成人教育与K12题库服务初始化完成,当前题目数: {len(self._questions)}")

    def _load_questions(self):
        if os.path.exists(self._db_path):
            try:
                with open(self._db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._questions = data.get('questions', {})
                logger.info(f"已加载 {len(self._questions)} 道成人教育/K12题目")
            except Exception as e:
                logger.error(f"加载成人教育/K12题库失败: {str(e)}")

    def _save_questions(self):
        try:
            data = {
                'last_updated': time.time(),
                'total_count': len(self._questions),
                'questions': self._questions
            }
            with open(self._db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存成人教育/K12题库失败: {str(e)}")

    def _generate_id(self) -> str:
        return f"AK-{int(time.time())}-{uuid.uuid4().hex[:6]}"

    def _init_default_questions(self):
        if len(self._questions) == 0:
            questions = []
            
            questions.extend(self._generate_k12_math_questions())
            questions.extend(self._generate_k12_chinese_questions())
            questions.extend(self._generate_k12_english_questions())
            questions.extend(self._generate_k12_science_questions())
            questions.extend(self._generate_adult_exam_questions())
            questions.extend(self._generate_professional_cert_questions())
            
            for q in questions:
                q_id = self._generate_id()
                q['question_id'] = q_id
                q['created_at'] = time.time()
                q['updated_at'] = time.time()
                self._questions[q_id] = q
            
            self._save_questions()
            logger.info(f"已初始化 {len(questions)} 道成人教育/K12题目")

    def _generate_k12_math_questions(self) -> List[Dict]:
        return [
            {
                'stage': 'primary',
                'subject': 'math',
                'type': 'single_choice',
                'difficulty': 'easy',
                'content': '小明有5个苹果，小红有3个苹果，他们一共有几个苹果？',
                'options': [{'A': '7'}, {'B': '8'}, {'C': '9'}, {'D': '10'}],
                'correct_answer': 'B',
                'explanation': '5 + 3 = 8，所以他们一共有8个苹果。',
                'knowledge_points': ['加法'],
                'tags': ['小学数学', '基础运算'],
                'score': 2
            },
            {
                'stage': 'primary',
                'subject': 'math',
                'type': 'fill_blank',
                'difficulty': 'medium',
                'content': '一个长方形的长是8厘米，宽是5厘米，它的周长是______厘米。',
                'correct_answer': '26',
                'explanation': '长方形周长 = (长 + 宽) × 2 = (8 + 5) × 2 = 26厘米',
                'knowledge_points': ['长方形周长'],
                'tags': ['小学数学', '几何'],
                'score': 3
            },
            {
                'stage': 'junior_high',
                'subject': 'math',
                'type': 'single_choice',
                'difficulty': 'medium',
                'content': '若 x² - 5x + 6 = 0，则 x 的值为：',
                'options': [{'A': 'x=2或x=3'}, {'B': 'x=2或x=-3'}, {'C': 'x=-2或x=3'}, {'D': 'x=-2或x=-3'}],
                'correct_answer': 'A',
                'explanation': 'x² - 5x + 6 = (x-2)(x-3) = 0，所以 x=2 或 x=3',
                'knowledge_points': ['一元二次方程', '因式分解'],
                'tags': ['初中数学', '方程'],
                'score': 3
            },
            {
                'stage': 'junior_high',
                'subject': 'math',
                'type': 'calculation',
                'difficulty': 'hard',
                'content': '已知一次函数 y = 2x + 3，求该函数与x轴、y轴的交点坐标，并计算所围成三角形的面积。',
                'correct_answer': '与x轴交点(-1.5, 0)，与y轴交点(0, 3)，面积=2.25',
                'explanation': '与x轴交点：y=0时，2x+3=0，x=-1.5；与y轴交点：x=0时，y=3。面积=1/2×1.5×3=2.25',
                'knowledge_points': ['一次函数', '坐标', '三角形面积'],
                'tags': ['初中数学', '函数'],
                'score': 10
            },
            {
                'stage': 'senior_high',
                'subject': 'math',
                'type': 'single_choice',
                'difficulty': 'hard',
                'content': '设等差数列{aₙ}的前n项和为Sₙ，若a₃=7，S₄=24，则公差d等于：',
                'options': [{'A': '2'}, {'B': '3'}, {'C': '4'}, {'D': '5'}],
                'correct_answer': 'A',
                'explanation': 'a₃ = a₁ + 2d = 7，S₄ = 4a₁ + 6d = 24，解得 d=2',
                'knowledge_points': ['等差数列', '前n项和'],
                'tags': ['高中数学', '数列'],
                'score': 5
            },
            {
                'stage': 'senior_high',
                'subject': 'math',
                'type': 'calculation',
                'difficulty': 'expert',
                'content': '求函数 f(x) = x³ - 3x² + 1 在区间 [-2, 3] 上的最大值和最小值。',
                'correct_answer': '最大值f(-2)=-19，最小值f(2)=-3',
                'explanation': 'f\'(x)=3x²-6x=3x(x-2)，令f\'(x)=0得x=0或x=2。计算f(-2)=-19, f(0)=1, f(2)=-3, f(3)=1。最大值为1，最小值为-19',
                'knowledge_points': ['导数', '极值', '最值'],
                'tags': ['高中数学', '导数'],
                'score': 12
            }
        ]

    def _generate_k12_chinese_questions(self) -> List[Dict]:
        return [
            {
                'stage': 'primary',
                'subject': 'chinese',
                'type': 'fill_blank',
                'difficulty': 'easy',
                'content': '春天来了，______绿了，______红了。',
                'correct_answer': '小草；花儿',
                'explanation': '这是常见的描写春天的句子，小草变绿，花儿变红。',
                'knowledge_points': ['词语填空'],
                'tags': ['小学语文', '词语'],
                'score': 2
            },
            {
                'stage': 'junior_high',
                'subject': 'chinese',
                'type': 'short_answer',
                'difficulty': 'medium',
                'content': '请解释《岳阳楼记》中"先天下之忧而忧，后天下之乐而乐"的含义。',
                'correct_answer': '在天下人忧愁之前先忧愁，在天下人快乐之后才快乐。表达了作者忧国忧民、以天下为己任的情怀。',
                'explanation': '这句话体现了范仲淹的政治抱负和高尚情操，是千古名句。',
                'knowledge_points': ['文言文理解', '名句赏析'],
                'tags': ['初中语文', '文言文'],
                'score': 6
            },
            {
                'stage': 'senior_high',
                'subject': 'chinese',
                'type': 'essay',
                'difficulty': 'hard',
                'content': '阅读下面这首唐诗，然后回答问题。\n\n登高\n杜甫\n风急天高猿啸哀，渚清沙白鸟飞回。\n无边落木萧萧下，不尽长江滚滚来。\n万里悲秋常作客，百年多病独登台。\n艰难苦恨繁霜鬓，潦倒新停浊酒杯。\n\n请分析这首诗的艺术特色。',
                'correct_answer': '1.对仗工整：颔联"无边落木萧萧下，不尽长江滚滚来"对仗极为工整；2.情景交融：景中有情，情中有景；3.用词精准：如"萧萧""滚滚"等叠词的运用；4.意境深远：营造出雄浑苍凉的意境。',
                'explanation': '这首诗是杜甫的代表作之一，被誉为"古今七言律诗第一"。',
                'knowledge_points': ['诗歌鉴赏', '艺术手法'],
                'tags': ['高中语文', '诗歌鉴赏'],
                'score': 15
            }
        ]

    def _generate_k12_english_questions(self) -> List[Dict]:
        return [
            {
                'stage': 'primary',
                'subject': 'english',
                'type': 'single_choice',
                'difficulty': 'easy',
                'content': 'I ______ a student.',
                'options': [{'A': 'am'}, {'B': 'is'}, {'C': 'are'}, {'D': 'be'}],
                'correct_answer': 'A',
                'explanation': '主语是I，be动词用am。',
                'knowledge_points': ['be动词'],
                'tags': ['小学英语', '语法'],
                'score': 2
            },
            {
                'stage': 'junior_high',
                'subject': 'english',
                'type': 'fill_blank',
                'difficulty': 'medium',
                'content': 'She ______ (study) English every day.',
                'correct_answer': 'studies',
                'explanation': '主语是第三人称单数she，谓语动词要用第三人称单数形式。',
                'knowledge_points': ['一般现在时', '动词变位'],
                'tags': ['初中英语', '语法'],
                'score': 2
            },
            {
                'stage': 'senior_high',
                'subject': 'english',
                'type': 'short_answer',
                'difficulty': 'hard',
                'content': 'Translate the following sentence into English: 他建议我们应该立即采取行动。',
                'correct_answer': 'He suggested that we should take action immediately.',
                'explanation': 'suggest后接宾语从句，要用虚拟语气(should+动词原形)。',
                'knowledge_points': ['虚拟语气', '翻译'],
                'tags': ['高中英语', '语法'],
                'score': 5
            }
        ]

    def _generate_k12_science_questions(self) -> List[Dict]:
        return [
            {
                'stage': 'junior_high',
                'subject': 'physics',
                'type': 'single_choice',
                'difficulty': 'medium',
                'content': '下列现象中，属于光的折射现象的是：',
                'options': [{'A': '镜子中的像'}, {'B': '水中的筷子看起来弯折'}, {'C': '影子的形成'}, {'D': '小孔成像'}],
                'correct_answer': 'B',
                'explanation': '光从水中进入空气中时发生折射，导致筷子看起来弯折。',
                'knowledge_points': ['光的折射'],
                'tags': ['初中物理', '光学'],
                'score': 3
            },
            {
                'stage': 'junior_high',
                'subject': 'chemistry',
                'type': 'true_false',
                'difficulty': 'easy',
                'content': '水是由氢元素和氧元素组成的。',
                'correct_answer': 'true',
                'explanation': '水的化学式是H₂O，由氢元素和氧元素组成。',
                'knowledge_points': ['水的组成'],
                'tags': ['初中化学', '基础'],
                'score': 2
            },
            {
                'stage': 'senior_high',
                'subject': 'biology',
                'type': 'short_answer',
                'difficulty': 'medium',
                'content': '简述光合作用的过程和意义。',
                'correct_answer': '过程：光能转化为化学能，二氧化碳和水转化为有机物和氧气。意义：为生物提供能量和氧气，维持生态平衡。',
                'explanation': '光合作用是地球上最重要的化学反应之一。',
                'knowledge_points': ['光合作用'],
                'tags': ['高中生物', '代谢'],
                'score': 8
            },
            {
                'stage': 'senior_high',
                'subject': 'physics',
                'type': 'calculation',
                'difficulty': 'hard',
                'content': '一个质量为2kg的物体，在水平面上受到10N的水平推力作用，物体与地面的动摩擦因数为0.3，求物体的加速度。(g=10m/s²)',
                'correct_answer': 'a=2m/s²',
                'explanation': '摩擦力f=μmg=0.3×2×10=6N，合力F=10-6=4N，加速度a=F/m=4/2=2m/s²',
                'knowledge_points': ['牛顿第二定律', '摩擦力'],
                'tags': ['高中物理', '力学'],
                'score': 10
            }
        ]

    def _generate_adult_exam_questions(self) -> List[Dict]:
        return [
            {
                'stage': 'adult_exam',
                'subject': 'chinese',
                'type': 'single_choice',
                'difficulty': 'medium',
                'content': '下列词语中，加点字的读音完全正确的一项是：',
                'options': [{'A': '联袂(mèi)、踽踽独行(yǔ)'}, {'B': '罹难(lí)、殚精竭虑(dān)'}, {'C': '掮客(qián)、怙恶不悛(quān)'}, {'D': '翘首(qiào)、锲而不舍(qì)'}],
                'correct_answer': 'B',
                'explanation': 'A项踽应读jǔ；C项悛应读quān但掮客正确；D项翘应读qiáo，锲应读qiè。',
                'knowledge_points': ['字音'],
                'tags': ['成人高考', '语文'],
                'score': 3
            },
            {
                'stage': 'adult_exam',
                'subject': 'math',
                'type': 'calculation',
                'difficulty': 'medium',
                'content': '求函数 y = ln(x² - 2x - 3) 的定义域。',
                'correct_answer': '(-∞, -1) ∪ (3, +∞)',
                'explanation': '需要x² - 2x - 3 > 0，即(x-3)(x+1) > 0，解得x < -1或x > 3',
                'knowledge_points': ['对数函数', '定义域'],
                'tags': ['成人高考', '数学'],
                'score': 10
            },
            {
                'stage': 'self_exam',
                'subject': 'english',
                'type': 'fill_blank',
                'difficulty': 'hard',
                'content': 'The manager demanded that all employees ______ (attend) the meeting on time.',
                'correct_answer': '(should) attend',
                'explanation': 'demand后接宾语从句，要用虚拟语气(should+动词原形，should可省略)。',
                'knowledge_points': ['虚拟语气'],
                'tags': ['自学考试', '英语'],
                'score': 3
            },
            {
                'stage': 'adult_exam',
                'subject': 'politics',
                'type': 'essay',
                'difficulty': 'hard',
                'content': '论述我国社会主义初级阶段的基本特征。',
                'correct_answer': '1.生产力水平低且发展不平衡；2.社会主义制度还不完善；3.社会主义市场经济体制还不成熟；4.社会主义民主法制还不健全；5.封建主义、资本主义思想影响还存在。',
                'explanation': '社会主义初级阶段是我国的基本国情，需要长期坚持。',
                'knowledge_points': ['社会主义初级阶段'],
                'tags': ['成人高考', '政治'],
                'score': 15
            }
        ]

    def _generate_professional_cert_questions(self) -> List[Dict]:
        return [
            {
                'stage': 'professional_cert',
                'subject': 'accounting',
                'type': 'single_choice',
                'difficulty': 'medium',
                'content': '下列各项中，属于资产类科目的是：',
                'options': [{'A': '应付账款'}, {'B': '实收资本'}, {'C': '应收账款'}, {'D': '主营业务收入'}],
                'correct_answer': 'C',
                'explanation': '应收账款是企业的资产，应付账款是负债，实收资本是所有者权益，主营业务收入是收入。',
                'knowledge_points': ['会计科目分类'],
                'tags': ['会计从业', '基础'],
                'score': 2
            },
            {
                'stage': 'professional_cert',
                'subject': 'law',
                'type': 'short_answer',
                'difficulty': 'hard',
                'content': '简述我国民法的基本原则。',
                'correct_answer': '1.平等原则；2.自愿原则；3.公平原则；4.诚实信用原则；5.公序良俗原则；6.绿色原则。',
                'explanation': '民法基本原则是民事立法、民事行为和民事司法的基本准则。',
                'knowledge_points': ['民法原则'],
                'tags': ['法律职业', '民法'],
                'score': 10
            },
            {
                'stage': 'professional_cert',
                'subject': 'computer',
                'type': 'single_choice',
                'difficulty': 'easy',
                'content': '在Excel中，单元格引用$A$1表示：',
                'options': [{'A': '相对引用'}, {'B': '绝对引用'}, {'C': '混合引用'}, {'D': '外部引用'}],
                'correct_answer': 'B',
                'explanation': '$A$1是绝对引用，行和列都不会随着复制而变化。',
                'knowledge_points': ['Excel引用'],
                'tags': ['计算机等级', 'Excel'],
                'score': 2
            },
            {
                'stage': 'professional_cert',
                'subject': 'economics',
                'type': 'calculation',
                'difficulty': 'hard',
                'content': '某商品的需求函数为Qd=100-2P，供给函数为Qs=50+3P，求市场均衡价格和均衡数量。',
                'correct_answer': '均衡价格P=10，均衡数量Q=80',
                'explanation': '均衡时Qd=Qs，即100-2P=50+3P，解得P=10，Q=80',
                'knowledge_points': ['市场均衡'],
                'tags': ['经济师', '微观经济学'],
                'score': 10
            }
        ]

    def add_question(self, question_data: Dict) -> str:
        q_id = self._generate_id()
        question_data['question_id'] = q_id
        question_data['created_at'] = time.time()
        question_data['updated_at'] = time.time()
        
        with self._lock:
            self._questions[q_id] = question_data
        
        self._save_questions()
        return q_id

    def add_questions_batch(self, questions_data: List[Dict]) -> Tuple[int, int]:
        success = 0
        failed = 0
        for q_data in questions_data:
            try:
                self.add_question(q_data)
                success += 1
            except Exception:
                failed += 1
        return success, failed

    def get_questions(self, filters: Dict = None) -> List[Dict]:
        results = []
        for q in self._questions.values():
            match = True
            if filters:
                if 'stage' in filters and q.get('stage') != filters['stage']:
                    match = False
                if 'subject' in filters and q.get('subject') != filters['subject']:
                    match = False
                if 'type' in filters and q.get('type') != filters['type']:
                    match = False
                if 'difficulty' in filters and q.get('difficulty') != filters['difficulty']:
                    match = False
            if match:
                results.append(q)
        return results

    def get_stats(self) -> Dict:
        stats = {
            'total': len(self._questions),
            'by_stage': {},
            'by_subject': {},
            'by_type': {},
            'by_difficulty': {}
        }
        
        for q in self._questions.values():
            stats['by_stage'][q.get('stage', 'unknown')] = stats['by_stage'].get(q.get('stage', 'unknown'), 0) + 1
            stats['by_subject'][q.get('subject', 'unknown')] = stats['by_subject'].get(q.get('subject', 'unknown'), 0) + 1
            stats['by_type'][q.get('type', 'unknown')] = stats['by_type'].get(q.get('type', 'unknown'), 0) + 1
            stats['by_difficulty'][q.get('difficulty', 'unknown')] = stats['by_difficulty'].get(q.get('difficulty', 'unknown'), 0) + 1
        
        return stats

    def delete_question(self, question_id: str) -> bool:
        with self._lock:
            if question_id in self._questions:
                del self._questions[question_id]
                self._save_questions()
                return True
        return False


adult_k12_question_bank = AdultK12QuestionBankService()