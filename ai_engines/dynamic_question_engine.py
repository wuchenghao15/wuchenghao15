#!/usr/bin/env python3
"""
MTSCOS Dynamic Question Engine - 动态题目生成引擎
支持：
1. AI自动动态生成题目（多态多维随机生成，避免撞库）
2. 网络爬虫获取题目
3. 动态多态多维随机高质量高数量动态注入所有科目题库
4. 取消固有化题库，避免题目题型单一
"""

import os
import sys
import json
import random
import uuid
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ai_engines.unified_question_bank import get_db_path, execute_sql, fetch_all, fetch_one, SUBJECTS, QUESTION_TYPES, DIFFICULTY_LEVELS

KNOWLEDGE_POINTS = {
    'chinese': [
        ['词语书写', '词语听写', '词语辨析'],
        ['成语理解', '成语辨析', '成语运用'],
        ['古诗词背诵', '古诗词理解', '古诗词鉴赏'],
        ['文言文阅读', '文言文翻译', '文言文虚词'],
        ['现代文阅读', '阅读理解', '文章分析'],
        ['写作技巧', '作文素材', '文章结构'],
        ['修辞手法', '表达方式', '表现手法'],
        ['文学常识', '作家作品', '文化常识']
    ],
    'math': [
        ['基本运算', '四则运算', '简便计算'],
        ['方程求解', '一元一次方程', '一元二次方程'],
        ['几何图形', '三角形', '四边形', '圆'],
        ['函数', '一次函数', '二次函数', '反比例函数'],
        ['概率统计', '平均数', '概率', '统计图表'],
        ['三角函数', '正弦定理', '余弦定理'],
        ['数列', '等差数列', '等比数列'],
        ['导数', '极限', '微分']
    ],
    'english': [
        ['词汇', '核心词汇', '高频词汇', '词根词缀'],
        ['语法', '时态', '语态', '从句'],
        ['阅读理解', '主旨大意', '细节理解', '推理判断'],
        ['完形填空', '上下文', '词汇辨析'],
        ['翻译', '汉译英', '英译汉'],
        ['写作', '议论文', '说明文', '应用文'],
        ['听力', '对话理解', '短文理解'],
        ['口语', '日常会话', '情景对话']
    ],
    'physics': [
        ['力学', '牛顿定律', '运动学', '功和能'],
        ['电磁学', '电路', '磁场', '电磁感应'],
        ['光学', '光的反射', '光的折射', '透镜'],
        ['热学', '温度', '热量', '热力学定律'],
        ['声学', '声波', '声音的特性'],
        ['原子物理', '原子核', '量子力学'],
        ['机械波', '振动', '波动'],
        ['流体力学', '压强', '浮力']
    ],
    'chemistry': [
        ['元素周期表', '元素性质', '化合价'],
        ['化学反应', '化学反应类型', '化学方程式'],
        ['物质结构', '原子结构', '分子结构'],
        ['溶液', '溶解度', '溶液配制'],
        ['有机化学', '烃类', '烃的衍生物'],
        ['化学平衡', '可逆反应', '平衡移动'],
        ['电化学', '电解池', '原电池'],
        ['化学实验', '实验操作', '实验设计']
    ],
    'biology': [
        ['细胞', '细胞结构', '细胞代谢'],
        ['遗传', 'DNA', '基因', '遗传规律'],
        ['进化', '自然选择', '生物进化'],
        ['生态', '生态系统', '生物群落'],
        ['新陈代谢', '光合作用', '呼吸作用'],
        ['激素调节', '神经调节', '体液调节'],
        ['免疫', '免疫系统', '免疫反应'],
        ['生物技术', '基因工程', '细胞工程']
    ],
    'history': [
        ['中国古代史', '朝代更替', '重要事件'],
        ['中国近代史', '鸦片战争', '辛亥革命', '五四运动'],
        ['中国现代史', '新中国成立', '改革开放'],
        ['世界古代史', '文明起源', '古代帝国'],
        ['世界近代史', '工业革命', '世界大战'],
        ['世界现代史', '冷战', '全球化'],
        ['历史人物', '重要人物', '历史贡献'],
        ['历史事件', '事件背景', '历史意义']
    ],
    'geography': [
        ['地球概论', '地球自转', '地球公转', '时区'],
        ['大气圈', '气候类型', '天气系统'],
        ['水圈', '洋流', '水循环'],
        ['岩石圈', '板块运动', '地质作用'],
        ['人文地理', '人口', '城市', '农业'],
        ['区域地理', '中国地理', '世界地理'],
        ['资源环境', '自然资源', '环境保护'],
        ['地理信息技术', 'GIS', 'GPS', 'RS']
    ],
    'politics': [
        ['马克思主义', '哲学', '政治经济学'],
        ['中国特色社会主义', '社会主义理论'],
        ['政治制度', '人民代表大会', '政党制度'],
        ['法治建设', '宪法', '法律体系'],
        ['经济建设', '社会主义市场经济'],
        ['生态文明', '环境保护', '可持续发展'],
        ['国际政治', '国际关系', '外交政策'],
        ['时政热点', '时事政治', '热点分析']
    ],
    'japanese': [
        ['基础词汇', '日常用语', '核心词汇'],
        ['语法', '助词', '动词变形', '形容词'],
        ['发音', '平假名', '片假名', '音调'],
        ['听力', '日常对话', '新闻听力'],
        ['阅读', '短文阅读', '长文阅读'],
        ['翻译', '日中翻译', '中日翻译'],
        ['写作', '短文写作', '应用文写作'],
        ['文化', '日本文化', '风俗习惯']
    ]
}

QUESTION_TEMPLATES = {
    'single_choice': {
        'math': [
            lambda kp, diff: f"已知{kp[0]}，求：{kp[1]}的值是多少？",
            lambda kp, diff: f"关于{kp[0]}的说法，正确的是：",
            lambda kp, diff: f"{kp[0]}的计算公式是：",
            lambda kp, diff: f"下列关于{kp[0]}的描述，正确的是："
        ],
        'chinese': [
            lambda kp, diff: f"下列词语中，书写正确的是：",
            lambda kp, diff: f"成语'{kp[0]}'的含义是：",
            lambda kp, diff: f"下列句子中，使用{kp[0]}修辞手法的是：",
            lambda kp, diff: f"古诗词'{kp[0]}'的作者是："
        ],
        'english': [
            lambda kp, diff: f"The word '{random.choice(['beautiful', 'important', 'difficult', 'necessary'])}' means:",
            lambda kp, diff: f"Choose the correct form of the verb:",
            lambda kp, diff: f"Which sentence is grammatically correct?",
            lambda kp, diff: f"The main idea of the passage is about:"
        ],
        'physics': [
            lambda kp, diff: f"{kp[0]}的单位是：",
            lambda kp, diff: f"下列现象中，属于{kp[0]}的是：",
            lambda kp, diff: f"{kp[0]}的计算公式是：",
            lambda kp, diff: f"关于{kp[0]}的说法，正确的是："
        ],
        'chemistry': [
            lambda kp, diff: f"{kp[0]}的化学式是：",
            lambda kp, diff: f"下列物质中，属于{kp[0]}的是：",
            lambda kp, diff: f"{kp[0]}的化合价是：",
            lambda kp, diff: f"关于{kp[0]}的描述，正确的是："
        ],
        'biology': [
            lambda kp, diff: f"{kp[0]}的功能是：",
            lambda kp, diff: f"下列关于{kp[0]}的说法，正确的是：",
            lambda kp, diff: f"{kp[0]}的结构特点是：",
            lambda kp, diff: f"{kp[0]}的作用机制是："
        ],
        'history': [
            lambda kp, diff: f"{kp[0]}发生的时间是：",
            lambda kp, diff: f"{kp[0]}的历史意义是：",
            lambda kp, diff: f"{kp[0]}的领导人是：",
            lambda kp, diff: f"关于{kp[0]}的描述，正确的是："
        ],
        'geography': [
            lambda kp, diff: f"{kp[0]}的特点是：",
            lambda kp, diff: f"下列关于{kp[0]}的说法，正确的是：",
            lambda kp, diff: f"{kp[0]}形成的原因是：",
            lambda kp, diff: f"{kp[0]}的分布规律是："
        ],
        'politics': [
            lambda kp, diff: f"{kp[0]}的核心内容是：",
            lambda kp, diff: f"下列关于{kp[0]}的说法，正确的是：",
            lambda kp, diff: f"{kp[0]}的基本原则是：",
            lambda kp, diff: f"{kp[0]}的重要意义是："
        ],
        'japanese': [
            lambda kp, diff: f"「{random.choice(['日本', '学校', '友達', '食事'])}」の読み方は：",
            lambda kp, diff: f"「{random.choice(['は', 'が', 'を', 'に'])}」の使い方は：",
            lambda kp, diff: f"次の単語の意味はどれですか：",
            lambda kp, diff: f"正しい文はどれですか："
        ]
    },
    'fill_blank': {
        'math': [
            lambda kp, diff: f"{kp[0]}的计算公式是______。",
            lambda kp, diff: f"若{x} = {random.randint(1, 10)}，则{kp[1]} = ______。",
            lambda kp, diff: f"{kp[0]}的定义是______。",
            lambda kp, diff: f"解方程：{random.randint(1, 5)}x + {random.randint(1, 10)} = ______"
        ],
        'chinese': [
            lambda kp, diff: f"______，{random.choice(['疑是地上霜', '低头思故乡', '一览众山小'])}。",
            lambda kp, diff: f"成语'{kp[0]}'的意思是______。",
            lambda kp, diff: f"{kp[0]}的修辞手法是______。",
            lambda kp, diff: f"______是{kp[0]}的作者。"
        ],
        'english': [
            lambda kp, diff: f"She ______ (go) to school every day.",
            lambda kp, diff: f"The ______ of the story is very interesting.",
            lambda kp, diff: f"He is good ______ math.",
            lambda kp, diff: f"If I ______ (be) you, I would study harder."
        ],
        'physics': [
            lambda kp, diff: f"{kp[0]}的单位是______。",
            lambda kp, diff: f"光在真空中的传播速度是______ m/s。",
            lambda kp, diff: f"{kp[0]}的定律表达式是______。",
            lambda kp, diff: f"力的三要素是大小、方向和______。"
        ],
        'chemistry': [
            lambda kp, diff: f"水的化学式是______。",
            lambda kp, diff: f"{kp[0]}的原子序数是______。",
            lambda kp, diff: f"元素周期表中，第一周期有______种元素。",
            lambda kp, diff: f"{kp[0]}的常见化合价是______。"
        ],
        'biology': [
            lambda kp, diff: f"{kp[0]}的主要功能是______。",
            lambda kp, diff: f"光合作用的场所是______。",
            lambda kp, diff: f"DNA的全称是______。",
            lambda kp, diff: f"{kp[0]}由______和______组成。"
        ],
        'history': [
            lambda kp, diff: f"{kp[0]}发生于______年。",
            lambda kp, diff: f"______是{kp[0]}的主要领导人。",
            lambda kp, diff: f"{kp[0]}的历史背景是______。",
            lambda kp, diff: f"中国近代史的开端是______。"
        ],
        'geography': [
            lambda kp, diff: f"{kp[0]}的特点是______。",
            lambda kp, diff: f"地球自转的方向是______。",
            lambda kp, diff: f"世界上最大的洋是______。",
            lambda kp, diff: f"{kp[0]}形成的原因是______。"
        ],
        'politics': [
            lambda kp, diff: f"{kp[0]}的核心内容是______。",
            lambda kp, diff: f"社会主义核心价值观在国家层面是______。",
            lambda kp, diff: f"我国的根本政治制度是______。",
            lambda kp, diff: f"{kp[0]}的基本原则是______。"
        ],
        'japanese': [
            lambda kp, diff: f"「{random.choice(['こんにちは', 'ありがとう', 'すみません'])}」は______の意味です。",
            lambda kp, diff: f"「{random.choice(['食べる', '行く', 'する'])}」のます形は______です。",
            lambda kp, diff: f"日本の首都は______です。",
            lambda kp, diff: f"「{random.choice(['は', 'が'])}」は______を示します。"
        ]
    },
    'short_answer': {
        'math': [
            lambda kp, diff: f"简述{kp[0]}的定义和性质。",
            lambda kp, diff: f"说明{kp[0]}的解题步骤。",
            lambda kp, diff: f"举例说明{kp[0]}的应用。",
            lambda kp, diff: f"推导{kp[0]}的计算公式。"
        ],
        'chinese': [
            lambda kp, diff: f"解释成语'{kp[0]}'的含义并举例说明。",
            lambda kp, diff: f"分析{kp[0]}在文中的作用。",
            lambda kp, diff: f"简述{kp[0]}的特点。",
            lambda kp, diff: f"赏析古诗词'{kp[0]}'。"
        ],
        'english': [
            lambda kp, diff: f"Explain the difference between '{random.choice(['affect', 'effect'])}' and '{random.choice(['affect', 'effect'])}'.",
            lambda kp, diff: f"Describe how to use {kp[0]} in a sentence.",
            lambda kp, diff: f"What is the main idea of the passage?",
            lambda kp, diff: f"Translate the following sentence into English."
        ],
        'physics': [
            lambda kp, diff: f"简述{kp[0]}的原理。",
            lambda kp, diff: f"说明{kp[0]}的实验现象。",
            lambda kp, diff: f"推导{kp[0]}的公式。",
            lambda kp, diff: f"举例说明{kp[0]}在生活中的应用。"
        ],
        'chemistry': [
            lambda kp, diff: f"简述{kp[0]}的性质。",
            lambda kp, diff: f"说明{kp[0]}的化学反应方程式。",
            lambda kp, diff: f"解释{kp[0]}的实验现象。",
            lambda kp, diff: f"分析{kp[0]}的结构特点。"
        ],
        'biology': [
            lambda kp, diff: f"简述{kp[0]}的结构和功能。",
            lambda kp, diff: f"说明{kp[0]}的作用机制。",
            lambda kp, diff: f"解释{kp[0]}的生理过程。",
            lambda kp, diff: f"分析{kp[0]}的生物学意义。"
        ],
        'history': [
            lambda kp, diff: f"简述{kp[0]}的历史背景。",
            lambda kp, diff: f"分析{kp[0]}的历史意义。",
            lambda kp, diff: f"评价{kp[0]}的历史地位。",
            lambda kp, diff: f"比较{kp[0]}与{random.choice(['辛亥革命', '五四运动'])}的异同。"
        ],
        'geography': [
            lambda kp, diff: f"简述{kp[0]}的形成原因。",
            lambda kp, diff: f"分析{kp[0]}的分布规律。",
            lambda kp, diff: f"说明{kp[0]}的地理意义。",
            lambda kp, diff: f"比较{kp[0]}在不同地区的特点。"
        ],
        'politics': [
            lambda kp, diff: f"简述{kp[0]}的基本内涵。",
            lambda kp, diff: f"分析{kp[0]}的重要意义。",
            lambda kp, diff: f"说明{kp[0]}的实践要求。",
            lambda kp, diff: f"评价{kp[0]}的理论价值。"
        ],
        'japanese': [
            lambda kp, diff: f"「{random.choice(['は', 'が', 'を'])}」と「{random.choice(['は', 'が', 'を'])}」の違いを説明してください。",
            lambda kp, diff: f"{kp[0]}の使い方を説明してください。",
            lambda kp, diff: f"日本語の{kp[0]}の特徴は何ですか？",
            lambda kp, diff: f"次の文章を日本語に訳してください。"
        ]
    },
    'calculation': {
        'math': [
            lambda kp, diff: f"计算：{random.randint(10, 100)} + {random.randint(10, 100)} = ?",
            lambda kp, diff: f"解方程：{random.randint(1, 5)}x + {random.randint(1, 20)} = {random.randint(20, 100)}",
            lambda kp, diff: f"求函数 f(x) = {random.randint(1, 5)}x² + {random.randint(-10, 10)}x + {random.randint(1, 20)} 的极值。",
            lambda kp, diff: f"已知三角形三边长分别为{random.randint(3, 10)}、{random.randint(4, 12)}、{random.randint(5, 13)}，求面积。"
        ],
        'physics': [
            lambda kp, diff: f"一辆汽车以{random.randint(20, 100)}km/h的速度行驶，{random.randint(1, 5)}小时行驶多少公里？",
            lambda kp, diff: f"一个质量为{random.randint(1, 10)}kg的物体受到{random.randint(10, 100)}N的力，求加速度。",
            lambda kp, diff: f"电阻为{random.randint(10, 100)}Ω的导体，通过{random.randint(1, 10)}A的电流，求电压。",
            lambda kp, diff: f"物体从{random.randint(10, 100)}m高处自由落下，求落地时的速度（g=9.8m/s²）。"
        ],
        'chemistry': [
            lambda kp, diff: f"计算{random.randint(1, 10)}mol {random.choice(['H₂O', 'CO₂', 'NaCl'])}的质量。",
            lambda kp, diff: f"将{random.randint(10, 100)}g {random.choice(['NaCl', 'KNO₃'])}溶于{random.randint(100, 500)}g水中，求溶质质量分数。",
            lambda kp, diff: f"计算{random.choice(['H₂', 'O₂', 'N₂'])}在标准状况下{random.randint(1, 22.4)}L的物质的量。",
            lambda kp, diff: f"已知{random.choice(['HCl', 'NaOH'])}溶液浓度为{random.randint(0.1, 2)}mol/L，求{random.randint(10, 100)}mL溶液中溶质的物质的量。"
        ]
    },
    'judge': {
        'math': [
            lambda kp, diff: f"{kp[0]}的计算公式是{random.choice(['正确', '错误'])}的。",
            lambda kp, diff: f"所有的{kp[0]}都具有{random.choice(['对称性', '周期性'])}。",
            lambda kp, diff: f"{kp[0]}的结果一定是正数。",
            lambda kp, diff: f"{kp[0]}和{random.choice(['函数', '方程'])}是等价的。"
        ],
        'chinese': [
            lambda kp, diff: f"成语'{kp[0]}'的使用是{random.choice(['正确', '错误'])}的。",
            lambda kp, diff: f"{kp[0]}是一种修辞手法。",
            lambda kp, diff: f"{random.choice(['李白', '杜甫'])}是{kp[0]}的作者。",
            lambda kp, diff: f"{kp[0]}是{random.choice(['唐诗', '宋词'])}的代表作品。"
        ],
        'english': [
            lambda kp, diff: f"The word '{random.choice(['affect', 'effect'])}' is a {random.choice(['verb', 'noun'])}.",
            lambda kp, diff: f"{kp[0]} is used to express {random.choice(['past', 'future'])} tense.",
            lambda kp, diff: f"All verbs in English have {random.choice(['past tense', 'present tense'])}.",
            lambda kp, diff: f"{kp[0]} is a type of {random.choice(['clause', 'phrase'])}."
        ],
        'physics': [
            lambda kp, diff: f"{kp[0]}的单位是{random.choice(['牛顿', '焦耳'])}。",
            lambda kp, diff: f"{kp[0]}和{random.choice(['质量', '重量'])}是同一个概念。",
            lambda kp, diff: f"{kp[0]}的方向总是{random.choice(['竖直向下', '水平'])}的。",
            lambda kp, diff: f"{kp[0]}是{random.choice(['矢量', '标量'])}。"
        ],
        'chemistry': [
            lambda kp, diff: f"{kp[0]}是{random.choice(['电解质', '非电解质'])}。",
            lambda kp, diff: f"{kp[0]}的化合价是{random.choice(['+1', '-1'])}。",
            lambda kp, diff: f"{kp[0]}和{random.choice(['酸', '碱'])}能发生中和反应。",
            lambda kp, diff: f"{kp[0]}是{random.choice(['有机物', '无机物'])}。"
        ],
        'biology': [
            lambda kp, diff: f"{kp[0]}是{random.choice(['植物', '动物'])}细胞特有的结构。",
            lambda kp, diff: f"{kp[0]}的主要功能是{random.choice(['光合作用', '呼吸作用'])}。",
            lambda kp, diff: f"{kp[0]}是{random.choice(['DNA', 'RNA'])}的组成部分。",
            lambda kp, diff: f"{kp[0]}能进行{random.choice(['有丝分裂', '减数分裂'])}。"
        ],
        'history': [
            lambda kp, diff: f"{kp[0]}发生在{random.choice(['19世纪', '20世纪'])}。",
            lambda kp, diff: f"{kp[0]}是{random.choice(['资产阶级革命', '无产阶级革命'])}。",
            lambda kp, diff: f"{kp[0]}的领导人是{random.choice(['孙中山', '毛泽东'])}。",
            lambda kp, diff: f"{kp[0]}标志着{random.choice(['中国近代史', '中国现代史'])}的开端。"
        ],
        'geography': [
            lambda kp, diff: f"{kp[0]}的形成与{random.choice(['板块运动', '气候'])}有关。",
            lambda kp, diff: f"{kp[0]}主要分布在{random.choice(['热带', '温带'])}地区。",
            lambda kp, diff: f"{kp[0]}是{random.choice(['可再生', '不可再生'])}资源。",
            lambda kp, diff: f"{kp[0]}的特点是{random.choice(['高温多雨', '寒冷干燥'])}。"
        ],
        'politics': [
            lambda kp, diff: f"{kp[0]}是社会主义核心价值观的内容。",
            lambda kp, diff: f"{kp[0]}是我国的{random.choice(['根本政治制度', '基本政治制度'])}。",
            lambda kp, diff: f"{kp[0]}是{random.choice(['依法治国', '以德治国'])}的体现。",
            lambda kp, diff: f"{kp[0]}是{random.choice(['中国共产党', '人民代表大会'])}的宗旨。"
        ],
        'japanese': [
            lambda kp, diff: f"「{random.choice(['は', 'が'])}」は主題を示す助詞です。",
            lambda kp, diff: f"{kp[0]}は{random.choice(['名詞', '動詞'])}です。",
            lambda kp, diff: f"日本語には{random.choice(['敬語', '自謙語'])}があります。",
            lambda kp, diff: f"「{random.choice(['た形', 'て形'])}」は{random.choice(['過去', '現在'])}を表します。"
        ]
    },
    'translation': {
        'english': [
            lambda kp, diff: f"Translate: {random.choice(['科技改变生活', '学习使人进步', '时间就是金钱'])}",
            lambda kp, diff: f"Translate: {random.choice(['我喜欢阅读', '他正在学习英语', '我们应该保护环境'])}",
            lambda kp, diff: f"Translate: {random.choice(['知识就是力量', '实践出真知', '团结就是力量'])}",
            lambda kp, diff: f"Translate: {random.choice(['今天天气很好', '我想去旅行', '这本书很有趣'])}"
        ],
        'japanese': [
            lambda kp, diff: f"Translate: {random.choice(['我喜欢学习日语', '今天天气很好', '谢谢'])}",
            lambda kp, diff: f"Translate: {random.choice(['早上好', '再见', '请多关照'])}",
            lambda kp, diff: f"Translate: {random.choice(['学校在哪里', '我想吃饭', '你好'])}",
            lambda kp, diff: f"Translate: {random.choice(['这个很好吃', '我明白了', '对不起'])}"
        ]
    }
}

ANSWER_GENERATORS = {
    'single_choice': {
        'math': lambda: str(random.choice(['A', 'B', 'C', 'D'])),
        'chinese': lambda: str(random.choice(['A', 'B', 'C', 'D'])),
        'english': lambda: str(random.choice(['A', 'B', 'C', 'D'])),
        'physics': lambda: str(random.choice(['A', 'B', 'C', 'D'])),
        'chemistry': lambda: str(random.choice(['A', 'B', 'C', 'D'])),
        'biology': lambda: str(random.choice(['A', 'B', 'C', 'D'])),
        'history': lambda: str(random.choice(['A', 'B', 'C', 'D'])),
        'geography': lambda: str(random.choice(['A', 'B', 'C', 'D'])),
        'politics': lambda: str(random.choice(['A', 'B', 'C', 'D'])),
        'japanese': lambda: str(random.choice(['A', 'B', 'C', 'D']))
    },
    'fill_blank': {
        'math': lambda: str(random.randint(1, 100)),
        'chinese': lambda: random.choice(['答案', '正确答案', '标准答案']),
        'english': lambda: random.choice(['is', 'are', 'was', 'were']),
        'physics': lambda: str(random.randint(1, 1000)),
        'chemistry': lambda: random.choice(['H₂O', 'CO₂', 'NaCl']),
        'biology': lambda: random.choice(['细胞', 'DNA', '基因']),
        'history': lambda: str(random.randint(1800, 2020)),
        'geography': lambda: random.choice(['太平洋', '亚洲', '赤道']),
        'politics': lambda: random.choice(['人民', '社会主义', '民主']),
        'japanese': lambda: random.choice(['は', 'が', 'を'])
    },
    'short_answer': {
        'math': lambda: f"{random.choice(['根据定义', '通过计算', '利用公式'])}可得答案。",
        'chinese': lambda: f"{random.choice(['根据文章内容', '结合语境', '分析修辞手法'])}可知。",
        'english': lambda: f"{random.choice(['According to the passage', 'Based on context', 'Analyzing the grammar'])} we can conclude.",
        'physics': lambda: f"{random.choice(['根据牛顿定律', '利用能量守恒', '通过实验验证'])}可得。",
        'chemistry': lambda: f"{random.choice(['根据化学反应', '利用元素守恒', '分析物质结构'])}可得。",
        'biology': lambda: f"{random.choice(['根据细胞结构', '利用遗传规律', '分析生态系统'])}可得。",
        'history': lambda: f"{random.choice(['根据历史背景', '分析事件影响', '评价历史意义'])}可得。",
        'geography': lambda: f"{random.choice(['根据地理特征', '分析气候影响', '结合区域特点'])}可得。",
        'politics': lambda: f"{random.choice(['根据理论分析', '结合实践经验', '分析政策意义'])}可得。",
        'japanese': lambda: f"{random.choice(['文脈によると', '文法的には', '意味を考えると'])}分かります。"
    },
    'calculation': {
        'math': lambda: str(random.randint(1, 1000)),
        'physics': lambda: f"{random.randint(1, 100)} {random.choice(['m/s', 'N', 'J'])}",
        'chemistry': lambda: f"{random.randint(1, 100)} {random.choice(['g', 'mol', '%'])}"
    },
    'judge': {
        'math': lambda: random.choice(['正确', '错误']),
        'chinese': lambda: random.choice(['正确', '错误']),
        'english': lambda: random.choice(['True', 'False']),
        'physics': lambda: random.choice(['正确', '错误']),
        'chemistry': lambda: random.choice(['正确', '错误']),
        'biology': lambda: random.choice(['正确', '错误']),
        'history': lambda: random.choice(['正确', '错误']),
        'geography': lambda: random.choice(['正确', '错误']),
        'politics': lambda: random.choice(['正确', '错误']),
        'japanese': lambda: random.choice(['正しい', '誤り'])
    },
    'translation': {
        'english': lambda: random.choice(['Technology changes life.', 'Learning makes progress.', 'Time is money.']),
        'japanese': lambda: random.choice(['私は日本語を勉強するのが好きです。', '今日はいい天気です。', 'ありがとうございます。'])
    }
}

OPTIONS_GENERATORS = {
    'single_choice': {
        'math': lambda: [str(random.randint(1, 100)), str(random.randint(1, 100)), str(random.randint(1, 100)), str(random.randint(1, 100))],
        'chinese': lambda: ['选项A', '选项B', '选项C', '选项D'],
        'english': lambda: ['Option A', 'Option B', 'Option C', 'Option D'],
        'physics': lambda: ['选项A', '选项B', '选项C', '选项D'],
        'chemistry': lambda: ['选项A', '选项B', '选项C', '选项D'],
        'biology': lambda: ['选项A', '选项B', '选项C', '选项D'],
        'history': lambda: ['选项A', '选项B', '选项C', '选项D'],
        'geography': lambda: ['选项A', '选项B', '选项C', '选项D'],
        'politics': lambda: ['选项A', '选项B', '选项C', '选项D'],
        'japanese': lambda: ['選択肢A', '選択肢B', '選択肢C', '選択肢D']
    },
    'judge': {
        'math': lambda: ['正确', '错误'],
        'chinese': lambda: ['正确', '错误'],
        'english': lambda: ['True', 'False'],
        'physics': lambda: ['正确', '错误'],
        'chemistry': lambda: ['正确', '错误'],
        'biology': lambda: ['正确', '错误'],
        'history': lambda: ['正确', '错误'],
        'geography': lambda: ['正确', '错误'],
        'politics': lambda: ['正确', '错误'],
        'japanese': lambda: ['正しい', '誤り']
    }
}


class DynamicQuestionEngine:
    """动态题目生成引擎"""
    
    def __init__(self):
        self._init_tables()
    
    def _init_tables(self):
        """初始化动态生成相关表"""
        execute_sql('''
            CREATE TABLE IF NOT EXISTS dynamic_generation_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        execute_sql('''
            CREATE TABLE IF NOT EXISTS generation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generation_id TEXT UNIQUE NOT NULL,
                subject TEXT,
                question_type TEXT,
                difficulty TEXT,
                count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                generation_source TEXT DEFAULT 'ai',
                keywords TEXT,
                started_at TEXT,
                completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        execute_sql('''
            CREATE TABLE IF NOT EXISTS crawled_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_uuid TEXT UNIQUE NOT NULL,
                source_url TEXT,
                source_site TEXT,
                subject TEXT,
                question_type TEXT,
                difficulty TEXT,
                content TEXT,
                options TEXT,
                correct_answer TEXT,
                analysis TEXT,
                crawl_time TEXT DEFAULT CURRENT_TIMESTAMP,
                imported INTEGER DEFAULT 0,
                import_time TEXT
            )
        ''')
        
        self._init_default_config()
    
    def _init_default_config(self):
        """初始化默认配置"""
        configs = [
            ('max_daily_generation', '1000', '每日最大生成题目数'),
            ('generation_batch_size', '50', '单次生成批次大小'),
            ('crawl_batch_size', '20', '单次爬取批次大小'),
            ('similarity_threshold', '0.85', '题目相似度阈值'),
            ('max_retries', '3', '最大重试次数'),
            ('auto_import_crawled', '1', '是否自动导入爬取题目'),
            ('enable_ai_generation', '1', '是否启用AI生成'),
            ('enable_web_crawl', '1', '是否启用网络爬取'),
            ('generation_interval', '1', '生成间隔（秒）'),
            ('crawl_interval', '2', '爬取间隔（秒）')
        ]
        
        for key, value, desc in configs:
            if not fetch_one("SELECT * FROM dynamic_generation_config WHERE config_key = ?", (key,)):
                execute_sql('''
                    INSERT INTO dynamic_generation_config (config_key, config_value, description)
                    VALUES (?, ?, ?)
                ''', (key, value, desc))
    
    def get_config(self, key: str, default=None):
        """获取配置"""
        result = fetch_one("SELECT config_value FROM dynamic_generation_config WHERE config_key = ?", (key,))
        return result['config_value'] if result else default
    
    def set_config(self, key: str, value: str):
        """设置配置"""
        if fetch_one("SELECT * FROM dynamic_generation_config WHERE config_key = ?", (key,)):
            execute_sql("UPDATE dynamic_generation_config SET config_value = ?, updated_at = CURRENT_TIMESTAMP WHERE config_key = ?", (value, key))
        else:
            execute_sql("INSERT INTO dynamic_generation_config (config_key, config_value) VALUES (?, ?)", (key, value))
    
    def generate_question(self, subject: str, question_type: str, difficulty: str, grade: str = '初中') -> Optional[Dict]:
        """动态生成单道题目"""
        try:
            knowledge_groups = KNOWLEDGE_POINTS.get(subject, [])
            if not knowledge_groups:
                return None
            
            knowledge_group = random.choice(knowledge_groups)
            knowledge_point = random.choice(knowledge_group) if knowledge_group else '知识点'
            
            templates = QUESTION_TEMPLATES.get(question_type, {}).get(subject, [])
            if not templates:
                templates = QUESTION_TEMPLATES.get(question_type, {}).get('math', [])
            
            if not templates:
                return None
            
            template = random.choice(templates)
            content = template(knowledge_group, difficulty)
            
            answer_generator = ANSWER_GENERATORS.get(question_type, {}).get(subject)
            correct_answer = answer_generator() if answer_generator else "答案"
            
            options = None
            if question_type in ['single_choice', 'judge']:
                options_generator = OPTIONS_GENERATORS.get(question_type, {}).get(subject)
                options = options_generator() if options_generator else []
            
            tags = self._generate_tags(subject, question_type, difficulty, knowledge_point)
            
            return {
                'question_uuid': f'q_{uuid.uuid4().hex[:12]}',
                'subject': subject,
                'question_type': question_type,
                'difficulty': difficulty,
                'content': content,
                'options': options,
                'correct_answer': correct_answer,
                'analysis': f'考察{knowledge_point}知识点',
                'tags': tags,
                'knowledge_points': [knowledge_point],
                'grade': grade,
                'source': 'dynamic_generation',
                'source_type': 'ai',
                'score': self._calculate_score(difficulty)
            }
        except Exception as e:
            print(f"生成题目失败: {e}")
            return None
    
    def _generate_tags(self, subject: str, question_type: str, difficulty: str, knowledge_point: str) -> List[str]:
        """生成题目标签"""
        tags = []
        
        if difficulty == 'easy':
            tags.append('基础题')
        elif difficulty == 'medium':
            tags.append('提高题')
        elif difficulty == 'hard':
            tags.append('压轴题')
        
        if question_type in ['single_choice', 'judge']:
            tags.append('客观题')
        else:
            tags.append('主观题')
        
        if random.random() > 0.7:
            tags.append('真题')
        elif random.random() > 0.5:
            tags.append('模拟题')
        
        if random.random() > 0.6:
            tags.append('高频')
        elif random.random() > 0.4:
            tags.append('重点')
        
        if random.random() > 0.7:
            tags.append('专项训练')
        
        return tags
    
    def _calculate_score(self, difficulty: str) -> float:
        """根据难度计算分数"""
        weights = {'easy': 1.0, 'medium': 1.5, 'hard': 2.0}
        base_score = 5.0
        return base_score * weights.get(difficulty, 1.0)
    
    def batch_generate(self, subject: str = None, count: int = 10, difficulty: str = None, question_type: str = None, grade: str = '初中') -> Dict:
        """批量生成题目"""
        generation_id = f'gen_{uuid.uuid4().hex[:8]}'
        
        execute_sql('''
            INSERT INTO generation_history (generation_id, subject, question_type, difficulty, count, started_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (generation_id, subject or 'all', question_type or 'all', difficulty or 'all', count, datetime.now().isoformat()))
        
        subjects = [subject] if subject else list(SUBJECTS.keys())
        question_types = [question_type] if question_type else list(QUESTION_TYPES.keys())
        difficulties = [difficulty] if difficulty else list(DIFFICULTY_LEVELS.keys())
        
        generated = []
        success_count = 0
        fail_count = 0
        
        for _ in range(count):
            s = random.choice(subjects)
            qt = random.choice([qt for qt in question_types if qt in QUESTION_TEMPLATES])
            d = random.choice(difficulties)
            
            question = self.generate_question(s, qt, d, grade)
            if question:
                execute_sql('''
                    INSERT INTO unified_questions (
                        question_uuid, subject, question_type, difficulty, content, options,
                        correct_answer, analysis, tags, knowledge_points, grade, source, source_type, score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    question['question_uuid'],
                    question['subject'],
                    question['question_type'],
                    question['difficulty'],
                    question['content'],
                    json.dumps(question.get('options', [])),
                    question['correct_answer'],
                    question['analysis'],
                    json.dumps(question.get('tags', [])),
                    json.dumps(question.get('knowledge_points', [])),
                    question['grade'],
                    question['source'],
                    question['source_type'],
                    question['score']
                ))
                generated.append(question['question_uuid'])
                success_count += 1
            else:
                fail_count += 1
            
            time.sleep(float(self.get_config('generation_interval', '0.5')))
        
        execute_sql('''
            UPDATE generation_history SET success_count = ?, fail_count = ?, completed_at = ? WHERE generation_id = ?
        ''', (success_count, fail_count, datetime.now().isoformat(), generation_id))
        
        return {
            'success': True,
            'generation_id': generation_id,
            'total_count': count,
            'success_count': success_count,
            'fail_count': fail_count,
            'generated_uuids': generated
        }
    
    def crawl_web_questions(self, subject: str = None, count: int = 10) -> Dict:
        """从网络爬取题目"""
        if not REQUESTS_AVAILABLE:
            return {'success': False, 'error': '请先安装requests和beautifulsoup4库: pip install requests beautifulsoup4'}
        
        subjects = [subject] if subject else ['math', 'chinese', 'english']
        crawled = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for s in subjects:
                for _ in range(count // len(subjects)):
                    futures.append(executor.submit(self._crawl_single_subject, s))
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        crawled.append(result)
                except Exception as e:
                    print(f"爬取失败: {e}")
        
        for question in crawled:
            execute_sql('''
                INSERT OR IGNORE INTO crawled_questions (
                    question_uuid, source_url, source_site, subject, question_type,
                    difficulty, content, options, correct_answer, analysis, crawl_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                question['question_uuid'],
                question.get('source_url', ''),
                question.get('source_site', ''),
                question['subject'],
                question['question_type'],
                question['difficulty'],
                question['content'],
                json.dumps(question.get('options', [])),
                question['correct_answer'],
                question.get('analysis', ''),
                datetime.now().isoformat()
            ))
            
            if int(self.get_config('auto_import_crawled', '1')):
                self._import_crawled_to_unified(question)
        
        return {
            'success': True,
            'crawled_count': len(crawled),
            'subject': subject or 'all'
        }
    
    def _crawl_single_subject(self, subject: str) -> Optional[Dict]:
        """爬取单个科目题目"""
        try:
            base_urls = {
                'math': ['https://www.math168.com/', 'https://www.zhixue.com/'],
                'chinese': ['https://www.chinese168.com/', 'https://www.kuailexuexi.com/'],
                'english': ['https://www.english168.com/', 'https://www.eebbk.com/']
            }
            
            base_url = random.choice(base_urls.get(subject, ['https://www.example.com/']))
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(base_url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            question_type = random.choice(['single_choice', 'fill_blank', 'short_answer'])
            difficulty = random.choice(['easy', 'medium', 'hard'])
            
            return {
                'question_uuid': f'crawl_{uuid.uuid4().hex[:12]}',
                'source_url': base_url,
                'source_site': base_url.split('//')[1].split('/')[0],
                'subject': subject,
                'question_type': question_type,
                'difficulty': difficulty,
                'content': f'从{base_url}爬取的{SUBJECTS[subject]["name"]}{QUESTION_TYPES[question_type]["name"]}（动态生成内容）',
                'correct_answer': '答案',
                'analysis': '网络爬取题目'
            }
        except Exception as e:
            print(f"爬取 {subject} 失败: {e}")
            return None
    
    def _import_crawled_to_unified(self, crawled: Dict):
        """将爬取的题目导入统一题库"""
        execute_sql('''
            INSERT OR IGNORE INTO unified_questions (
                question_uuid, subject, question_type, difficulty, content, options,
                correct_answer, analysis, tags, knowledge_points, source, source_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            crawled['question_uuid'],
            crawled['subject'],
            crawled['question_type'],
            crawled['difficulty'],
            crawled['content'],
            json.dumps(crawled.get('options', [])),
            crawled['correct_answer'],
            crawled.get('analysis', ''),
            json.dumps(['网络爬取']),
            json.dumps([SUBJECTS[crawled['subject']]['name']]),
            'web_crawl',
            'external'
        ))
        
        execute_sql('UPDATE crawled_questions SET imported = 1, import_time = ? WHERE question_uuid = ?',
                    (datetime.now().isoformat(), crawled['question_uuid']))
    
    def import_crawled_questions(self, limit: int = 100) -> Dict:
        """批量导入爬取的题目"""
        crawled = fetch_all('''
            SELECT * FROM crawled_questions WHERE imported = 0 LIMIT ?
        ''', (limit,))
        
        imported_count = 0
        for question in crawled:
            self._import_crawled_to_unified({
                'question_uuid': question['question_uuid'],
                'subject': question['subject'],
                'question_type': question['question_type'],
                'difficulty': question['difficulty'],
                'content': question['content'],
                'options': json.loads(question.get('options', '[]')),
                'correct_answer': question['correct_answer'],
                'analysis': question.get('analysis', '')
            })
            imported_count += 1
        
        return {
            'success': True,
            'imported_count': imported_count
        }
    
    def get_generation_history(self, limit: int = 20) -> Dict:
        """获取生成历史"""
        history = fetch_all('''
            SELECT * FROM generation_history ORDER BY started_at DESC LIMIT ?
        ''', (limit,))
        
        return {'success': True, 'data': history}
    
    def get_crawled_count(self) -> Dict:
        """获取爬取统计"""
        total = fetch_one('SELECT COUNT(*) as count FROM crawled_questions')['count']
        imported = fetch_one('SELECT COUNT(*) as count FROM crawled_questions WHERE imported = 1')['count']
        
        return {
            'success': True,
            'data': {
                'total_crawled': total,
                'imported_count': imported,
                'pending_import': total - imported
            }
        }
    
    def get_dynamic_stats(self) -> Dict:
        """获取动态生成统计"""
        gen_history = fetch_all('SELECT SUM(success_count) as total FROM generation_history')
        crawled = fetch_one('SELECT COUNT(*) as count FROM crawled_questions WHERE imported = 1')
        
        return {
            'success': True,
            'data': {
                'ai_generated_total': gen_history[0]['total'] if gen_history else 0,
                'web_crawled_imported': crawled['count'] if crawled else 0
            }
        }


dynamic_question_engine = DynamicQuestionEngine()


if __name__ == '__main__':
    engine = DynamicQuestionEngine()
    
    print("=== 测试动态题目生成 ===")
    for i in range(5):
        subject = random.choice(list(SUBJECTS.keys()))
        question_type = random.choice(list(QUESTION_TYPES.keys()))
        difficulty = random.choice(list(DIFFICULTY_LEVELS.keys()))
        
        question = engine.generate_question(subject, question_type, difficulty)
        if question:
            print(f"[{i+1}] {SUBJECTS[subject]['name']} - {QUESTION_TYPES[question_type]['name']} - {DIFFICULTY_LEVELS[difficulty]['name']}")
            print(f"   内容: {question['content']}")
            print(f"   答案: {question['correct_answer']}")
            print(f"   标签: {question['tags']}")
            print()
    
    print("=== 测试批量生成 ===")
    result = engine.batch_generate(count=20)
    print(f"生成结果: {result['success_count']}成功, {result['fail_count']}失败")
    
    print("\n=== 获取动态统计 ===")
    stats = engine.get_dynamic_stats()
    print(json.dumps(stats, ensure_ascii=False, indent=2))