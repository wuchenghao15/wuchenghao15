# -*- coding: utf-8 -*-
"""
AI智能出题系统API
基于学科和知识点自动生成不同类型题目，支持批量生成、审核、统计和导出
"""

from flask import Blueprint, request, session
from app.middlewares.permission_decorators import require_login, require_admin
from app.utils.api_response import APIResponse
import sqlite3
import logging
import os
import json
import random
from datetime import datetime

logger = logging.getLogger(__name__)

ai_question_generation_api = Blueprint('ai_question_generation_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_ai_question_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_generated_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL DEFAULT 'medium',
            question_type TEXT NOT NULL,
            question_content TEXT NOT NULL,
            options TEXT,
            answer TEXT NOT NULL,
            analysis TEXT,
            knowledge_points TEXT,
            created_by INTEGER,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            batch_id INTEGER,
            FOREIGN KEY (batch_id) REFERENCES ai_question_batches(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_question_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            count INTEGER NOT NULL,
            difficulty TEXT NOT NULL DEFAULT 'medium',
            question_types TEXT,
            status TEXT NOT NULL DEFAULT 'generating',
            created_at TEXT NOT NULL,
            completed_count INTEGER DEFAULT 0,
            created_by INTEGER
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("AI智能出题系统数据库表初始化完成")


SUBJECT_KNOWLEDGE = {
    '数学': {
        '代数': {
            '知识点': ['一元一次方程', '二元一次方程组', '一元二次方程', '不等式', '因式分解', '整式运算', '分式', '根式'],
            '模板': {
                'choice': [
                    '若关于x的方程{expr}=0的解为x={val}，则{param}的值为？',
                    '下列不等式中，与{inequality}解集相同的是？',
                    '若{a}+{b}={sum_val}，{a}*{b}={product}，则{a}^2+{b}^2的值为？',
                ],
                'fill': [
                    '方程{expr}=0的解为x=____。',
                    '因式分解：{poly}=____。',
                    '若{x}+{y}={s}，{x}-{y}={d}，则{x}*{y}=____。',
                ],
                'judge': [
                    '方程{expr}=0一定有实数解。（　）',
                    '若{a}>{b}，则{a}^2>{b}^2。（　）',
                    '{poly}可以分解为两个一次因式的乘积。（　）',
                ],
                'short': [
                    '请解方程：{expr}=0',
                    '已知条件{conditions}，求{target}的值。',
                    '证明：{statement}',
                ]
            }
        },
        '几何': {
            '知识点': ['三角形', '四边形', '圆', '相似三角形', '全等三角形', '勾股定理', '面积计算', '立体几何'],
            '模板': {
                'choice': [
                    '一个三角形的三边长分别为{a}、{b}、{c}，则该三角形是？',
                    '圆的半径为{r}，则其面积为？',
                    '在三角形ABC中，若{condition}，则该三角形为？',
                ],
                'fill': [
                    '一个正方形的边长为{a}，则其对角线长为____。',
                    '圆的周长公式是____。',
                    '三角形的内角和为____度。',
                ],
                'judge': [
                    '所有的等边三角形都是等腰三角形。（　）',
                    '直径是圆中最长的弦。（　）',
                    '两个面积相等的三角形一定全等。（　）',
                ],
                'short': [
                    '已知三角形ABC中，{conditions}，求{target}。',
                    '证明：{statement}',
                    '计算图形的面积：{description}',
                ]
            }
        },
        '函数': {
            '知识点': ['一次函数', '二次函数', '反比例函数', '三角函数', '函数图像', '函数性质'],
            '模板': {
                'choice': [
                    '函数{func}的图像经过点({x}, {y})，则{k}的值为？',
                    '二次函数{quad_func}的顶点坐标是？',
                    '下列函数中，是反比例函数的是？',
                ],
                'fill': [
                    '一次函数y={k}x+{b}的斜率为____。',
                    '函数{func}的定义域是____。',
                    '抛物线{quad_func}的对称轴是____。',
                ],
                'judge': [
                    '一次函数的图像一定经过原点。（　）',
                    '反比例函数的图像在每一象限内，y随x的增大而减小。（　）',
                    '二次函数的图像是抛物线。（　）',
                ],
                'short': [
                    '求函数{func}的解析式，已知{conditions}。',
                    '分析函数{func}的性质。',
                    '画出函数{func}的图像并说明其特点。',
                ]
            }
        }
    },
    '物理': {
        '力学': {
            '知识点': ['牛顿运动定律', '匀变速直线运动', '力的合成与分解', '功和能', '动量守恒', '圆周运动', '万有引力'],
            '模板': {
                'choice': [
                    '一个质量为{m}kg的物体，受到{F}N的力作用，其加速度为？',
                    '物体从高度{h}处自由下落，落地时的速度约为？（g取10m/s2）',
                    '下列说法正确的是？',
                ],
                'fill': [
                    '牛顿第一定律又称为____定律。',
                    '动能的计算公式是____。',
                    '重力加速度g的近似值为____m/s2。',
                ],
                'judge': [
                    '物体不受力时一定静止。（　）',
                    '作用力与反作用力大小相等、方向相反。（　）',
                    '做匀速圆周运动的物体，向心力不做功。（　）',
                ],
                'short': [
                    '一个{m}kg的物体在{F}N的力作用下，从静止开始运动，求{t}秒后的速度和位移。',
                    '请简述牛顿三大定律的内容。',
                    '从{h}高处平抛一物体，初速度为{v0}，求物体落地时的水平位移和速度。',
                ]
            }
        },
        '电磁学': {
            '知识点': ['静电场', '恒定电流', '磁场', '电磁感应', '交流电', '电磁波'],
            '模板': {
                'choice': [
                    '电阻{R}两端电压为{U}，则通过电阻的电流为？',
                    '电容器的电容为{C}，带电量为{Q}，则两极板间电压为？',
                    '下列说法正确的是？',
                ],
                'fill': [
                    '欧姆定律的表达式是____。',
                    '电功率的计算公式是____。',
                    '电磁波在真空中的传播速度约为____m/s。',
                ],
                'judge': [
                    '电流的方向与正电荷定向移动的方向相同。（　）',
                    '磁场对运动电荷一定有力的作用。（　）',
                    '只要穿过闭合电路的磁通量发生变化，就会产生感应电流。（　）',
                ],
                'short': [
                    '在如图所示的电路中，{circuit_desc}，求{target}。',
                    '请简述法拉第电磁感应定律。',
                    '计算：{calc_description}',
                ]
            }
        },
        '热学': {
            '知识点': ['分子热运动', '内能', '热力学定律', '气体状态方程', '热传递'],
            '模板': {
                'choice': [
                    '理想气体在等温过程中，体积增大为原来的{n}倍，则压强变为原来的？',
                    '下列说法正确的是？',
                    '物体的内能是指？',
                ],
                'fill': [
                    '热力学第一定律的表达式是____。',
                    '热传递的三种方式是____、____、____。',
                    '分子动理论的基本内容是____。',
                ],
                'judge': [
                    '温度高的物体内能一定大。（　）',
                    '热量可以自发地从低温物体传到高温物体。（　）',
                    '布朗运动是分子的无规则运动。（　）',
                ],
                'short': [
                    '一定质量的理想气体，{conditions}，求{target}。',
                    '请简述热力学第二定律的两种表述。',
                    '解释：{phenomenon}',
                ]
            }
        }
    },
    '化学': {
        '基础化学': {
            '知识点': ['原子结构', '元素周期表', '化学键', '物质的量', '氧化还原反应', '离子反应'],
            '模板': {
                'choice': [
                    '下列元素中，原子半径最大的是？',
                    '下列物质中，含有离子键的是？',
                    '{n}mol水的质量是？',
                ],
                'fill': [
                    '元素周期表共有____个周期，____个族。',
                    '摩尔质量的单位是____。',
                    '氧化还原反应的本质是____。',
                ],
                'judge': [
                    '所有的化学反应都伴随着能量变化。（　）',
                    '离子化合物中一定含有金属元素。（　）',
                    '氧化剂在反应中得到电子，发生还原反应。（　）',
                ],
                'short': [
                    '请写出{reaction}的化学方程式，并配平。',
                    '简述原子结构的组成。',
                    '计算：{calc_description}',
                ]
            }
        },
        '有机化学': {
            '知识点': ['烃类', '醇酚醚', '醛酮酸', '酯类', '糖类', '蛋白质', '高分子化合物'],
            '模板': {
                'choice': [
                    '下列物质中，属于饱和烃的是？',
                    '乙醇的官能团是？',
                    '下列物质中，能发生银镜反应的是？',
                ],
                'fill': [
                    '甲烷的分子式是____，结构式是____。',
                    '酯化反应的机理是____。',
                    '蛋白质的基本组成单位是____。',
                ],
                'judge': [
                    '苯分子中碳碳键是单双键交替的结构。（　）',
                    '乙醇和乙醚互为同分异构体。（　）',
                    '淀粉和纤维素互为同分异构体。（　）',
                ],
                'short': [
                    '写出{compound}的结构简式，并说明其化学性质。',
                    '请简述加成反应和取代反应的区别。',
                    '以{material}为原料，设计合成路线制备{target}。',
                ]
            }
        },
        '实验化学': {
            '知识点': ['化学实验基本操作', '物质的检验', '物质的分离与提纯', '气体制备', '定量实验'],
            '模板': {
                'choice': [
                    '下列实验操作正确的是？',
                    '检验CO3^2-离子常用的试剂是？',
                    '下列气体中，不能用排水法收集的是？',
                ],
                'fill': [
                    '过滤操作中，玻璃棒的作用是____。',
                    '配制一定物质的量浓度的溶液，需要用到的仪器有____。',
                    '蒸馏是利用____不同分离混合物的方法。',
                ],
                'judge': [
                    '用托盘天平称量时，左盘放砝码，右盘放药品。（　）',
                    'pH试纸可以直接浸入待测液中测量。（　）',
                    '分液时，下层液体从下口放出，上层液体从上口倒出。（　）',
                ],
                'short': [
                    '设计实验方案，验证{hypothesis}。',
                    '简述{experiment}的实验步骤和注意事项。',
                    '实验室制取{gas}的反应原理是什么？需要哪些装置？',
                ]
            }
        }
    },
    '英语': {
        '语法': {
            '知识点': ['时态', '语态', '从句', '非谓语动词', '虚拟语气', '主谓一致', '倒装句', '强调句'],
            '模板': {
                'choice': [
                    'He {verb_pattern} to Beijing tomorrow.',
                    'The book {passive_pattern} by many people.',
                    'I don\'t know {clause_pattern}.',
                ],
                'fill': [
                    'She ____(study) English for five years.（用正确时态填空）',
                    'The letter ____(write) by him yesterday.（用被动语态填空）',
                    'If I ____(be) you, I would study harder.（虚拟语气）',
                ],
                'judge': [
                    '现在完成时表示过去发生的动作对现在造成的影响。（　）',
                    '被动语态的构成是be+过去分词。（　）',
                    '宾语从句中，从句要用陈述语序。（　）',
                ],
                'short': [
                    '请将下列句子改为被动语态：{sentence}',
                    '分析句子结构：{sentence}',
                    '用给定的语法点造句：{grammar_point}',
                ]
            }
        },
        '词汇': {
            '知识点': ['常用词汇', '短语搭配', '同义词辨析', '词根词缀', '词性转换'],
            '模板': {
                'choice': [
                    'What is the meaning of "{word}"?',
                    'Choose the correct word: He is very ____ in learning English.',
                    'Which word has a different meaning from the others?',
                ],
                'fill': [
                    'The ____(important) of learning English is obvious.（词性转换）',
                    'Please pay attention ____ your pronunciation.（介词填空）',
                    'He is good ____ playing basketball.（介词填空）',
                ],
                'judge': [
                    '"Look forward to"后面接动词原形。（　）',
                    '"Make progress"中的progress是可数名词。（　）',
                    '"Used to"表示过去常常做某事，现在不做了。（　）',
                ],
                'short': [
                    '请用{word}造一个句子，并解释其含义。',
                    '辨析下列词组的区别：{phrase1} vs {phrase2}',
                    '写出{root}词根的三个派生词并解释。',
                ]
            }
        },
        '阅读理解': {
            '知识点': ['主旨大意', '细节理解', '推理判断', '词义猜测', '观点态度'],
            '模板': {
                'choice': [
                    'What is the main idea of the passage?',
                    'According to the passage, which statement is true?',
                    'What can we infer from the text?',
                ],
                'fill': [
                    'The best title for this passage is ____.',
                    'The word "{word}" in paragraph {n} probably means ____.',
                    'The author\'s attitude towards {topic} is ____.',
                ],
                'judge': [
                    'The passage mainly talks about {topic}.（　）',
                    'According to the author, {statement}.（　）',
                    'The word "{word}" has the same meaning as "{another_word}".（　）',
                ],
                'short': [
                    'Please summarize the main idea of the passage in your own words.',
                    'What do you think is the author\'s purpose in writing this passage?',
                    'Based on the passage, what conclusion can we draw?',
                ]
            }
        }
    },
    '语文': {
        '文言文': {
            '知识点': ['文言实词', '文言虚词', '文言句式', '文言文翻译', '古文理解'],
            '模板': {
                'choice': [
                    '下列句子中"{word}"的解释正确的是？',
                    '下列句子中，句式与其他三项不同的是？',
                    '下列虚词用法相同的一组是？',
                ],
                'fill': [
                    '"{sentence}"中"{word}"的意思是____。',
                    '翻译句子：{sentence} —— ____',
                    '本文的作者是____，选自《____》。',
                ],
                'judge': [
                    '"之"在文言文中只能作代词。（　）',
                    '文言文翻译要做到"信、达、雅"。（　）',
                    '"师者，所以传道受业解惑也"是判断句。（　）',
                ],
                'short': [
                    '请翻译下列文言文句子：{sentence}',
                    '分析{text}的主要内容和写作特点。',
                    '简述{ancient_figure}的人物形象。',
                ]
            }
        },
        '现代文阅读': {
            '知识点': ['记叙文阅读', '议论文阅读', '说明文阅读', '散文阅读', '小说阅读'],
            '模板': {
                'choice': [
                    '本文的文体是？',
                    '作者在文中主要运用了什么写作手法？',
                    '下列对文章内容的理解，正确的是？',
                ],
                'fill': [
                    '本文的线索是____。',
                    '第{n}段在文中的作用是____。',
                    '文章表达了作者____的思想感情。',
                ],
                'judge': [
                    '本文是一篇议论文。（　）',
                    '作者在文中运用了比喻、拟人等修辞手法。（　）',
                    '文章的主旨是{topic}。（　）',
                ],
                'short': [
                    '请概括本文的主要内容。',
                    '分析第{n}段中划线句子的表达效果。',
                    '结合全文，谈谈你对{topic}的理解。',
                ]
            }
        },
        '作文': {
            '知识点': ['命题作文', '材料作文', '话题作文', '议论文写作', '记叙文写作'],
            '模板': {
                'choice': [
                    '下列关于写作的说法，正确的是？',
                    '议论文的三要素是？',
                    '记叙文的六要素不包括？',
                ],
                'fill': [
                    '一篇好的作文应该具备____、____、____等特点。',
                    '议论文的论证方法有____、____、____等。',
                    '记叙文的写作顺序通常有____、____、____。',
                ],
                'judge': [
                    '作文开头要点题，结尾要扣题。（　）',
                    '议论文只能用举例子的论证方法。（　）',
                    '材料作文可以脱离材料任意发挥。（　）',
                ],
                'short': [
                    '请以"{topic}"为题，写一篇作文提纲。',
                    '根据材料"{material}"，自选角度，自拟题目，写一篇议论文提纲。',
                    '请写一段关于{scene}的景物描写。',
                ]
            }
        }
    }
}

QUESTION_TYPES = {
    'choice': '选择题',
    'fill': '填空题',
    'judge': '判断题',
    'short': '简答题'
}

DIFFICULTY_LEVELS = {
    'easy': '简单',
    'medium': '中等',
    'hard': '困难'
}


def generate_options(correct_answer, subject, topic, question_type):
    if question_type != 'choice':
        return None

    all_options = [correct_answer]

    if subject == '数学':
        variations = [
            lambda x: str(int(x) + random.randint(1, 10)),
            lambda x: str(int(x) - random.randint(1, 10)),
            lambda x: str(int(x) * 2),
            lambda x: str(int(x) // 2) if int(x) % 2 == 0 else str(int(x) + 1),
        ]
        try:
            num_val = int(correct_answer)
            for _ in range(3):
                variation = random.choice(variations)
                wrong_answer = variation(correct_answer)
                if wrong_answer not in all_options:
                    all_options.append(wrong_answer)
        except (ValueError, TypeError):
            for i in range(3):
                all_options.append(f'选项{chr(66+i)}')
    elif subject == '物理':
        for i in range(3):
            all_options.append(f'选项{chr(66+i)}')
    elif subject == '化学':
        for i in range(3):
            all_options.append(f'选项{chr(66+i)}')
    elif subject == '英语':
        for i in range(3):
            all_options.append(f'option{chr(66+i)}')
    elif subject == '语文':
        for i in range(3):
            all_options.append(f'选项{chr(66+i)}')
    else:
        for i in range(3):
            all_options.append(f'选项{chr(66+i)}')

    while len(all_options) < 4:
        all_options.append(f'错误选项{len(all_options)}')

    random.shuffle(all_options)
    return json.dumps({
        'A': all_options[0],
        'B': all_options[1],
        'C': all_options[2],
        'D': all_options[3]
    }, ensure_ascii=False)


def generate_analysis(subject, topic, question_type, question_content, answer):
    analyses = {
        '数学': [
            f'本题考查{topic}相关知识。解题思路：根据相关公式和定理，逐步推导可得答案为{answer}。',
            f'这是一道{topic}的{QUESTION_TYPES[question_type]}。解析：利用已知条件，结合相关知识点，可以得出正确答案是{answer}。',
            f'考点分析：本题主要考察学生对{topic}的理解和应用。通过分析题目条件，运用相应的解题方法，最终答案为{answer}。',
        ],
        '物理': [
            f'本题考查{topic}的基本概念和公式应用。根据物理原理，通过计算可得答案为{answer}。',
            f'物理{topic}题解析：首先明确已知量和所求量，选择合适的物理公式，代入数据计算可得答案{answer}。',
            f'解题思路：本题涉及{topic}的知识点。分析物理过程，建立物理模型，运用相应定律，最终答案为{answer}。',
        ],
        '化学': [
            f'本题考查{topic}的相关知识。根据化学原理和反应规律，分析可得答案为{answer}。',
            f'化学{topic}题解析：理解相关概念，掌握化学方程式，通过分析推理可得正确答案是{answer}。',
            f'考点分析：本题考察学生对{topic}的掌握程度。运用化学基本原理，分析题目条件，答案为{answer}。',
        ],
        '英语': [
            f'本题考查{topic}的相关语法/词汇知识。通过分析句子结构和语境，正确答案是{answer}。',
            f'英语{topic}题解析：理解句子意思，掌握相关语法规则/词汇用法，可得出答案为{answer}。',
            f'解题思路：本题涉及{topic}知识点。仔细阅读题目，运用所学知识分析，最终答案为{answer}。',
        ],
        '语文': [
            f'本题考查{topic}的相关知识。通过分析文章内容/句子含义，正确答案是{answer}。',
            f'语文{topic}题解析：理解题意，结合上下文/文言文知识，分析可得答案为{answer}。',
            f'考点分析：本题考察学生对{topic}的理解和运用能力。深入分析题目，运用语文知识，答案为{answer}。',
        ]
    }

    subject_analyses = analyses.get(subject, analyses['数学'])
    return random.choice(subject_analyses)


def generate_single_question(subject, topic, difficulty, question_type):
    if subject not in SUBJECT_KNOWLEDGE:
        subject = random.choice(list(SUBJECT_KNOWLEDGE.keys()))

    if topic not in SUBJECT_KNOWLEDGE[subject]:
        topic = random.choice(list(SUBJECT_KNOWLEDGE[subject].keys()))

    topic_data = SUBJECT_KNOWLEDGE[subject][topic]
    knowledge_points = topic_data['知识点']
    templates = topic_data['模板'].get(question_type, [])

    if not templates:
        question_type = 'choice'
        templates = topic_data['模板'].get('choice', [])

    template = random.choice(templates)

    kp = random.choice(knowledge_points)

    difficulty_factors = {
        'easy': {'variation': 1, 'complexity': '简单'},
        'medium': {'variation': 2, 'complexity': '中等'},
        'hard': {'variation': 3, 'complexity': '较难'}
    }
    factor = difficulty_factors.get(difficulty, difficulty_factors['medium'])

    fill_params = {
        'a': str(random.randint(1, 20) * factor['variation']),
        'b': str(random.randint(1, 15) * factor['variation']),
        'c': str(random.randint(1, 10) * factor['variation']),
        'x': str(random.randint(1, 10)),
        'y': str(random.randint(1, 10)),
        'm': str(random.randint(1, 50) * factor['variation']),
        'r': str(random.randint(1, 20) * factor['variation']),
        'h': str(random.randint(1, 30) * factor['variation']),
        'v0': str(random.randint(5, 30) * factor['variation']),
        't': str(random.randint(1, 20)),
        'k': str(random.randint(1, 5)),
        'param': '参数',
        'val': str(random.randint(1, 10)),
        'sum_val': str(random.randint(10, 50)),
        'product': str(random.randint(10, 100)),
        'expr': f'x^2 + {random.randint(1, 10)}x + {random.randint(1, 20)}',
        'inequality': f'2x + 1 > 5',
        'poly': f'x^2 + {random.randint(2, 8)}x + {random.randint(1, 12)}',
        's': str(random.randint(10, 30)),
        'd': str(random.randint(2, 10)),
        'condition': 'AB=AC且角A=60度',
        'conditions': 'AB=BC=CA',
        'target': '角B的度数',
        'statement': '等腰三角形两底角相等',
        'func': f'y = {random.randint(1, 5)}x + {random.randint(1, 10)}',
        'quad_func': f'y = x^2 + {random.randint(1, 5)}x + {random.randint(1, 10)}',
        'n': str(random.randint(2, 5)),
        'F': str(random.randint(10, 100) * factor['variation']),
        'U': str(random.randint(10, 220)),
        'R': str(random.randint(10, 100) * factor['variation']),
        'Q': str(random.randint(1, 10)),
        'C': str(random.randint(1, 50)),
        'reaction': '氢气燃烧',
        'compound': '乙醇',
        'experiment': '粗盐提纯',
        'gas': '氧气',
        'hypothesis': '催化剂能加快反应速率',
        'calc_description': '计算溶液的质量分数',
        'material': '乙烯',
        'root': 'port',
        'sentence': 'He plays basketball every day.',
        'grammar_point': '现在完成时',
        'word': 'important',
        'phrase1': 'look for',
        'phrase2': 'find',
        'another_word': 'significant',
        'topic': '环保',
        'text': '《岳阳楼记》',
        'ancient_figure': '孔子',
        'scene': '秋天的校园',
        'desc': '一个长方形，长5cm，宽3cm',
        'phenomenon': '热胀冷缩',
        'circuit_desc': '两个电阻串联',
        'verb_pattern': 'goes',
        'passive_pattern': 'is read',
        'clause_pattern': 'where he lives',
        'description': '描述计算过程',
    }

    try:
        question_content = template.format(**fill_params)
    except (KeyError, IndexError):
        question_content = f'[{subject}][{topic}] 这是一道{DIFFICULTY_LEVELS.get(difficulty, "中等")}难度的{QUESTION_TYPES[question_type]}。'

    if question_type == 'choice':
        if subject == '数学':
            correct_answer = str(random.randint(1, 50) * factor['variation'])
        elif subject == '物理':
            correct_answer = str(random.randint(1, 100) * factor['variation'])
        elif subject == '化学':
            correct_answer = random.choice(['A', 'B', 'C', 'D'])
        elif subject == '英语':
            correct_answer = random.choice(['A', 'B', 'C', 'D'])
        elif subject == '语文':
            correct_answer = random.choice(['A', 'B', 'C', 'D'])
        else:
            correct_answer = random.choice(['A', 'B', 'C', 'D'])
        options = generate_options(correct_answer, subject, topic, question_type)
    elif question_type == 'fill':
        if subject == '数学':
            correct_answer = str(random.randint(1, 100))
        elif subject == '物理':
            correct_answer = str(random.randint(1, 100)) + ' m/s'
        elif subject == '化学':
            correct_answer = random.choice(knowledge_points)
        else:
            correct_answer = f'答案内容_{random.randint(1, 100)}'
        options = None
    elif question_type == 'judge':
        correct_answer = random.choice(['正确', '错误'])
        options = None
    elif question_type == 'short':
        correct_answer = f'本题考查{kp}的相关知识。解题要点如下：\n1. 理解题意，明确已知条件\n2. 运用{kp}的相关原理/公式\n3. 逐步推导，得出结论\n4. 检查验证答案的合理性。'
        options = None
    else:
        correct_answer = '答案'
        options = None

    analysis = generate_analysis(subject, topic, question_type, question_content, correct_answer)

    return {
        'subject': subject,
        'topic': topic,
        'difficulty': difficulty,
        'question_type': question_type,
        'question_content': question_content,
        'options': options,
        'answer': correct_answer,
        'analysis': analysis,
        'knowledge_points': json.dumps([kp], ensure_ascii=False),
    }


def generate_questions_batch(subject, topic, count, difficulty, question_types, batch_id, created_by):
    conn = get_db_connection()
    cursor = conn.cursor()

    generated_count = 0

    for i in range(count):
        q_type = random.choice(question_types) if question_types else random.choice(list(QUESTION_TYPES.keys()))

        question = generate_single_question(subject, topic, difficulty, q_type)

        cursor.execute('''
            INSERT INTO ai_generated_questions 
            (subject, topic, difficulty, question_type, question_content, options, answer, analysis, 
             knowledge_points, created_by, created_at, status, batch_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            question['subject'],
            question['topic'],
            question['difficulty'],
            question['question_type'],
            question['question_content'],
            question['options'],
            question['answer'],
            question['analysis'],
            question['knowledge_points'],
            created_by,
            datetime.now().isoformat(),
            'pending',
            batch_id
        ))

        generated_count += 1

        cursor.execute('''
            UPDATE ai_question_batches 
            SET completed_count = ? 
            WHERE id = ?
        ''', (generated_count, batch_id))
        conn.commit()

    cursor.execute('''
        UPDATE ai_question_batches 
        SET status = 'completed' 
        WHERE id = ?
    ''', (batch_id,))
    conn.commit()
    conn.close()

    logger.info(f"批次{batch_id}题目生成完成，共生成{generated_count}道题")
    return generated_count


@ai_question_generation_api.route('/api/ai/qg/generate', methods=['POST'])
@require_login
def generate_questions():
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error('请求参数不能为空')

        subject = data.get('subject', '数学')
        topic = data.get('topic', '代数')
        count = int(data.get('count', 10))
        difficulty = data.get('difficulty', 'medium')
        question_types = data.get('question_types', ['choice', 'fill', 'judge', 'short'])

        if count < 1 or count > 100:
            return APIResponse.error('题目数量必须在1-100之间')

        if difficulty not in DIFFICULTY_LEVELS:
            return APIResponse.error(f'难度参数无效，可选值: {list(DIFFICULTY_LEVELS.keys())}')

        valid_types = set(QUESTION_TYPES.keys())
        if not set(question_types).issubset(valid_types):
            return APIResponse.error(f'题型参数无效，可选值: {list(QUESTION_TYPES.keys())}')

        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO ai_question_batches 
            (subject, topic, count, difficulty, question_types, status, created_at, completed_count, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            subject,
            topic,
            count,
            difficulty,
            json.dumps(question_types, ensure_ascii=False),
            'generating',
            datetime.now().isoformat(),
            0,
            user_id
        ))
        batch_id = cursor.lastrowid
        conn.commit()
        conn.close()

        import threading
        thread = threading.Thread(
            target=generate_questions_batch,
            args=(subject, topic, count, difficulty, question_types, batch_id, user_id)
        )
        thread.daemon = True
        thread.start()

        return APIResponse.success(
            data={'batch_id': batch_id, 'status': 'generating', 'message': '题目正在生成中'},
            message='出题任务已创建',
            code=201
        )

    except Exception as e:
        logger.error(f"生成题目失败: {str(e)}")
        return APIResponse.server_error(f'生成题目失败: {str(e)}')


@ai_question_generation_api.route('/api/ai/qg/batch/<batch_id>', methods=['GET'])
@require_login
def get_batch_status(batch_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM ai_question_batches WHERE id = ?', (batch_id,))
        batch = cursor.fetchone()

        if not batch:
            conn.close()
            return APIResponse.not_found('批次不存在')

        cursor.execute('SELECT COUNT(*) as cnt FROM ai_generated_questions WHERE batch_id = ?', (batch_id,))
        total_generated = cursor.fetchone()['cnt']

        conn.close()

        batch_data = dict(batch)
        batch_data['question_types'] = json.loads(batch_data['question_types']) if batch_data['question_types'] else []
        batch_data['total_generated'] = total_generated

        return APIResponse.success(data=batch_data, message='获取批次状态成功')

    except Exception as e:
        logger.error(f"获取批次状态失败: {str(e)}")
        return APIResponse.server_error(f'获取批次状态失败: {str(e)}')


@ai_question_generation_api.route('/api/ai/qg/batches', methods=['GET'])
@require_login
def get_batches():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        subject = request.args.get('subject')
        status = request.args.get('status')

        conn = get_db_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM ai_question_batches WHERE 1=1'
        params = []

        if subject:
            query += ' AND subject = ?'
            params.append(subject)
        if status:
            query += ' AND status = ?'
            params.append(status)

        query += ' ORDER BY created_at DESC'

        cursor.execute(query, params)
        all_batches = cursor.fetchall()
        total = len(all_batches)

        start = (page - 1) * per_page
        query += ' LIMIT ? OFFSET ?'
        params.extend([per_page, start])

        cursor.execute(query, params)
        batches = cursor.fetchall()
        conn.close()

        batch_list = []
        for batch in batches:
            batch_data = dict(batch)
            batch_data['question_types'] = json.loads(batch_data['question_types']) if batch_data['question_types'] else []
            batch_list.append(batch_data)

        return APIResponse.success(data={
            'batches': batch_list,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }, message='获取批次列表成功')

    except Exception as e:
        logger.error(f"获取批次列表失败: {str(e)}")
        return APIResponse.server_error(f'获取批次列表失败: {str(e)}')


@ai_question_generation_api.route('/api/ai/qg/questions', methods=['GET'])
@require_login
def get_questions():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        subject = request.args.get('subject')
        topic = request.args.get('topic')
        difficulty = request.args.get('difficulty')
        question_type = request.args.get('question_type')
        status = request.args.get('status')
        batch_id = request.args.get('batch_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM ai_generated_questions WHERE 1=1'
        params = []

        if subject:
            query += ' AND subject = ?'
            params.append(subject)
        if topic:
            query += ' AND topic = ?'
            params.append(topic)
        if difficulty:
            query += ' AND difficulty = ?'
            params.append(difficulty)
        if question_type:
            query += ' AND question_type = ?'
            params.append(question_type)
        if status:
            query += ' AND status = ?'
            params.append(status)
        if batch_id:
            query += ' AND batch_id = ?'
            params.append(batch_id)

        query += ' ORDER BY created_at DESC'

        cursor.execute(query, params)
        all_questions = cursor.fetchall()
        total = len(all_questions)

        start = (page - 1) * per_page
        query += ' LIMIT ? OFFSET ?'
        params.extend([per_page, start])

        cursor.execute(query, params)
        questions = cursor.fetchall()
        conn.close()

        question_list = []
        for q in questions:
            q_data = dict(q)
            if q_data['options']:
                q_data['options'] = json.loads(q_data['options'])
            if q_data['knowledge_points']:
                q_data['knowledge_points'] = json.loads(q_data['knowledge_points'])
            question_list.append(q_data)

        return APIResponse.success(data={
            'questions': question_list,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }, message='获取题目列表成功')

    except Exception as e:
        logger.error(f"获取题目列表失败: {str(e)}")
        return APIResponse.server_error(f'获取题目列表失败: {str(e)}')


@ai_question_generation_api.route('/api/ai/qg/question/<question_id>', methods=['GET'])
@require_login
def get_question_detail(question_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM ai_generated_questions WHERE id = ?', (question_id,))
        question = cursor.fetchone()
        conn.close()

        if not question:
            return APIResponse.not_found('题目不存在')

        q_data = dict(question)
        if q_data['options']:
            q_data['options'] = json.loads(q_data['options'])
        if q_data['knowledge_points']:
            q_data['knowledge_points'] = json.loads(q_data['knowledge_points'])

        return APIResponse.success(data=q_data, message='获取题目详情成功')

    except Exception as e:
        logger.error(f"获取题目详情失败: {str(e)}")
        return APIResponse.server_error(f'获取题目详情失败: {str(e)}')


@ai_question_generation_api.route('/api/ai/qg/question/<question_id>/approve', methods=['POST'])
@require_login
def approve_question(question_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM ai_generated_questions WHERE id = ?', (question_id,))
        question = cursor.fetchone()

        if not question:
            conn.close()
            return APIResponse.not_found('题目不存在')

        cursor.execute('''
            UPDATE ai_generated_questions 
            SET status = 'approved' 
            WHERE id = ?
        ''', (question_id,))
        conn.commit()
        conn.close()

        return APIResponse.success(data={'question_id': question_id, 'status': 'approved'}, message='审核通过')

    except Exception as e:
        logger.error(f"审核题目失败: {str(e)}")
        return APIResponse.server_error(f'审核题目失败: {str(e)}')


@ai_question_generation_api.route('/api/ai/qg/question/<question_id>/reject', methods=['POST'])
@require_login
def reject_question(question_id):
    try:
        data = request.get_json() or {}
        reason = data.get('reason', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM ai_generated_questions WHERE id = ?', (question_id,))
        question = cursor.fetchone()

        if not question:
            conn.close()
            return APIResponse.not_found('题目不存在')

        cursor.execute('''
            UPDATE ai_generated_questions 
            SET status = 'rejected', analysis = ? 
            WHERE id = ?
        ''', (f'【拒绝原因】{reason}\n{question["analysis"] if question["analysis"] else ""}', question_id))
        conn.commit()
        conn.close()

        return APIResponse.success(data={'question_id': question_id, 'status': 'rejected'}, message='已拒绝该题目')

    except Exception as e:
        logger.error(f"拒绝题目失败: {str(e)}")
        return APIResponse.server_error(f'拒绝题目失败: {str(e)}')


@ai_question_generation_api.route('/api/ai/qg/stats', methods=['GET'])
@require_login
def get_generation_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as total FROM ai_generated_questions')
        total_questions = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as cnt FROM ai_generated_questions WHERE status = 'approved'")
        approved_count = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM ai_generated_questions WHERE status = 'pending'")
        pending_count = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM ai_generated_questions WHERE status = 'rejected'")
        rejected_count = cursor.fetchone()['cnt']

        cursor.execute('SELECT subject, COUNT(*) as cnt FROM ai_generated_questions GROUP BY subject')
        by_subject = {row['subject']: row['cnt'] for row in cursor.fetchall()}

        cursor.execute('SELECT difficulty, COUNT(*) as cnt FROM ai_generated_questions GROUP BY difficulty')
        by_difficulty = {row['difficulty']: row['cnt'] for row in cursor.fetchall()}

        cursor.execute('SELECT question_type, COUNT(*) as cnt FROM ai_generated_questions GROUP BY question_type')
        by_type = {row['question_type']: row['cnt'] for row in cursor.fetchall()}

        cursor.execute('SELECT COUNT(*) as total FROM ai_question_batches')
        total_batches = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as cnt FROM ai_question_batches WHERE status = 'completed'")
        completed_batches = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM ai_question_batches WHERE status = 'generating'")
        generating_batches = cursor.fetchone()['cnt']

        conn.close()

        stats = {
            'total_questions': total_questions,
            'approved_count': approved_count,
            'pending_count': pending_count,
            'rejected_count': rejected_count,
            'approval_rate': round(approved_count / total_questions * 100, 2) if total_questions > 0 else 0,
            'by_subject': by_subject,
            'by_difficulty': by_difficulty,
            'by_type': by_type,
            'total_batches': total_batches,
            'completed_batches': completed_batches,
            'generating_batches': generating_batches
        }

        return APIResponse.success(data=stats, message='获取统计信息成功')

    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return APIResponse.server_error(f'获取统计信息失败: {str(e)}')


@ai_question_generation_api.route('/api/ai/qg/export', methods=['POST'])
@require_login
def export_questions():
    try:
        data = request.get_json() or {}
        subject = data.get('subject')
        topic = data.get('topic')
        difficulty = data.get('difficulty')
        question_type = data.get('question_type')
        status = data.get('status', 'approved')
        batch_id = data.get('batch_id')
        export_format = data.get('format', 'json')

        conn = get_db_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM ai_generated_questions WHERE 1=1'
        params = []

        if subject:
            query += ' AND subject = ?'
            params.append(subject)
        if topic:
            query += ' AND topic = ?'
            params.append(topic)
        if difficulty:
            query += ' AND difficulty = ?'
            params.append(difficulty)
        if question_type:
            query += ' AND question_type = ?'
            params.append(question_type)
        if status:
            query += ' AND status = ?'
            params.append(status)
        if batch_id:
            query += ' AND batch_id = ?'
            params.append(batch_id)

        query += ' ORDER BY subject, topic, created_at DESC'

        cursor.execute(query, params)
        questions = cursor.fetchall()
        conn.close()

        question_list = []
        for q in questions:
            q_data = dict(q)
            if q_data['options']:
                q_data['options'] = json.loads(q_data['options'])
            if q_data['knowledge_points']:
                q_data['knowledge_points'] = json.loads(q_data['knowledge_points'])
            question_list.append(q_data)

        if export_format == 'json':
            export_data = question_list
        elif export_format == 'markdown':
            md_content = f'# 导出题目\n\n'
            md_content += f'- 导出时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
            md_content += f'- 题目数量: {len(question_list)}\n\n'

            for idx, q in enumerate(question_list, 1):
                md_content += f'## 第{idx}题\n\n'
                md_content += f'- **学科**: {q["subject"]}\n'
                md_content += f'- **主题**: {q["topic"]}\n'
                md_content += f'- **难度**: {DIFFICULTY_LEVELS.get(q["difficulty"], q["difficulty"])}\n'
                md_content += f'- **题型**: {QUESTION_TYPES.get(q["question_type"], q["question_type"])}\n\n'
                md_content += f'### 题目\n\n{q["question_content"]}\n\n'

                if q.get('options'):
                    md_content += '### 选项\n\n'
                    for k, v in q['options'].items():
                        md_content += f'- {k}. {v}\n'
                    md_content += '\n'

                md_content += f'### 答案\n\n{q["answer"]}\n\n'

                if q.get('analysis'):
                    md_content += f'### 解析\n\n{q["analysis"]}\n\n'

                if q.get('knowledge_points'):
                    md_content += f'### 知识点\n\n{", ".join(q["knowledge_points"])}\n\n'

                md_content += '---\n\n'

            export_data = {'content': md_content, 'format': 'markdown'}
        else:
            export_data = question_list

        return APIResponse.success(data={
            'total': len(question_list),
            'format': export_format,
            'data': export_data
        }, message='导出成功')

    except Exception as e:
        logger.error(f"导出题目失败: {str(e)}")
        return APIResponse.server_error(f'导出题目失败: {str(e)}')


@ai_question_generation_api.route('/api/ai/qg/subjects', methods=['GET'])
def get_available_subjects():
    subjects = {}
    for subject, topics in SUBJECT_KNOWLEDGE.items():
        subjects[subject] = list(topics.keys())

    return APIResponse.success(data={
        'subjects': subjects,
        'question_types': QUESTION_TYPES,
        'difficulty_levels': DIFFICULTY_LEVELS
    }, message='获取学科配置成功')


init_ai_question_tables()
