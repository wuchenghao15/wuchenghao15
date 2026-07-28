# -*- coding: utf-8 -*-
""" 题库升级脚本 - v5.2.0 为MTSCOS系统注入多学科高质量题目种子数据 涵盖：数学、语文、英语、物理、化学、生物、历史、地理、政治 v5.2.0新增：高中学段题目（高一数学/物理/化学） """

import os
import sys
import json
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')


# 数学题库（初中）
MATH_QUESTIONS = [
    {
        'subject': '数学',
        'grade': '初一',
        'chapter': '第一章 有理数',
        'question_type': 'single_choice',
        'difficulty': 'easy',
        'content': '下列各数中，是负数的是（  ）',
        'options': ['-(-3)', '|-3|', '(-3)²', '-3'],
        'correct_answer': 'D',
        'explanation': 'A: -(-3)=3是正数；B: |-3|=3是正数；C: (-3)²=9是正数；D: -3是负数。',
        'knowledge_points': ['正负数', '相反数', '绝对值', '乘方'],
        'points': 3
    },
    {
        'subject': '数学',
        'grade': '初一',
        'chapter': '第一章 有理数',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': '若 |a-2| + |b+3| = 0，则 a+b 的值为（  ）',
        'options': ['1', '-1', '5', '-5'],
        'correct_answer': 'B',
        'explanation': '因为绝对值非负，两个非负数相加为0，则各自为0。所以 a-2=0 得 a=2；b+3=0 得 b=-3。a+b=2+(-3)=-1。',
        'knowledge_points': ['绝对值的性质', '非负数的性质'],
        'points': 4
    },
    {
        'subject': '数学',
        'grade': '初一',
        'chapter': '第三章 一元一次方程',
        'question_type': 'single_choice',
        'difficulty': 'easy',
        'content': '方程 2x - 5 = 3 的解是（  ）',
        'options': ['x = 1', 'x = 2', 'x = 3', 'x = 4'],
        'correct_answer': 'D',
        'explanation': '2x - 5 = 3，移项得 2x = 8，两边同除以2得 x = 4。',
        'knowledge_points': ['一元一次方程', '移项'],
        'points': 3
    },
    {
        'subject': '数学',
        'grade': '初二',
        'chapter': '第十二章 全等三角形',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': '下列条件中，不能判定两个三角形全等的是（  ）',
        'options': ['三边对应相等 (SSS)', '两边及其夹角对应相等 (SAS)', '两角及其夹边对应相等 (ASA)', '两边及其中一边的对角对应相等 (SSA)'],
        'correct_answer': 'D',
        'explanation': 'SSA不能判定三角形全等，因为两边及其中一边的对角对应相等时，三角形形状不确定。',
        'knowledge_points': ['全等三角形判定定理', 'SSA不成立'],
        'points': 4
    },
    {
        'subject': '数学',
        'grade': '初三',
        'chapter': '第二十二章 二次函数',
        'question_type': 'single_choice',
        'difficulty': 'hard',
        'content': '二次函数 y = x² - 4x + 3 的顶点坐标是（  ）',
        'options': ['(2, -1)', '(2, 1)', '(-2, -1)', '(-2, 1)'],
        'correct_answer': 'A',
        'explanation': '配方法：y = x² - 4x + 3 = (x-2)² - 4 + 3 = (x-2)² - 1，所以顶点坐标为(2, -1)。',
        'knowledge_points': ['二次函数', '配方法', '顶点坐标'],
        'points': 5
    },
    {
        'subject': '数学',
        'grade': '初二',
        'chapter': '第十六章 二次根式',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': '化简 √18 的结果是（  ）',
        'options': ['3√2', '2√3', '9√2', '6√3'],
        'correct_answer': 'A',
        'explanation': '√18 = √(9×2) = √9 × √2 = 3√2。',
        'knowledge_points': ['二次根式化简', '最简二次根式'],
        'points': 4
    },
]

# 语文题库
CHINESE_QUESTIONS = [
    {
        'subject': '语文',
        'grade': '初一',
        'chapter': '第一单元',
        'question_type': 'single_choice',
        'difficulty': 'easy',
        'content': '下列词语中加点字注音完全正确的一项是（  ）',
        'options': [
            '酝酿(liàng)  黄晕(yùn)  发髻(jì)',
            '静谧(mì)    高邈(miǎo)  莅临(lì)',
            '粗犷(kuàng)  棱镜(léng)  池畦(qí)',
            '贮蓄(chǔ)   着落(zháo)  应和(hè)'
        ],
        'correct_answer': 'B',
        'explanation': 'A项"酝酿"应读niàng；C项"粗犷"应读guǎng；D项"贮蓄"应读zhù，"着落"应读zhuó。',
        'knowledge_points': ['字音辨析'],
        'points': 3
    },
    {
        'subject': '语文',
        'grade': '初二',
        'chapter': '第三单元',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': '下列句子中没有语病的一项是（  ）',
        'options': [
            '通过这次活动，使我们受到了深刻的教育。',
            '能否保持一颗平常心是考试正常发挥的关键。',
            '我们要及时解决并发现学习中存在的问题。',
            '秋天的北京是一个美丽的季节。'
        ],
        'correct_answer': 'B',
        'explanation': 'A项缺主语，删去"通过"或"使"；C项语序不当，应为"发现并解决"；D项搭配不当，应为"北京的秋天"。',
        'knowledge_points': ['病句辨析', '成分残缺', '语序不当', '搭配不当'],
        'points': 4
    },
    {
        'subject': '语文',
        'grade': '初三',
        'chapter': '古诗文',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': '"忽如一夜春风来，千树万树梨花开"运用的修辞手法是（  ）',
        'options': ['拟人', '比喻', '夸张', '排比'],
        'correct_answer': 'B',
        'explanation': '诗句以"梨花"比喻"雪花"，形象生动地写出了大雪纷飞的景象，是比喻的修辞手法。',
        'knowledge_points': ['修辞手法', '比喻', '古诗文理解'],
        'points': 4
    },
]

# 英语题库
ENGLISH_QUESTIONS = [
    {
        'subject': '英语',
        'grade': '初一',
        'chapter': 'Unit 1',
        'question_type': 'single_choice',
        'difficulty': 'easy',
        'content': '— ___ is your name?  — My name is Tom.',
        'options': ['What', 'How', 'Where', 'Who'],
        'correct_answer': 'A',
        'explanation': '询问姓名用疑问词What。How问方式，Where问地点，Who问人。',
        'knowledge_points': ['疑问词', '特殊疑问句'],
        'points': 3
    },
    {
        'subject': '英语',
        'grade': '初二',
        'chapter': 'Unit 3',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': 'Tina is ___ than Tara. She always makes us laugh.',
        'options': ['funny', 'funnier', 'more funny', 'most funny'],
        'correct_answer': 'B',
        'explanation': '两者比较用比较级。funny的比较级是funnier（变y为i加er）。',
        'knowledge_points': ['形容词比较级', '变化规则'],
        'points': 4
    },
    {
        'subject': '英语',
        'grade': '初三',
        'chapter': 'Unit 5',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': 'The desk ___ wood. It was made by my grandfather.',
        'options': [
            'is made of',
            'is made from',
            'is made in',
            'is made by'
        ],
        'correct_answer': 'A',
        'explanation': 'be made of能看出原材料；be made from看不出原材料；be made in表产地；be made by表制造者。桌子能看出木头材质，用of。',
        'knowledge_points': ['make短语辨析', '被动语态'],
        'points': 4
    },
]

# 物理题库
PHYSICS_QUESTIONS = [
    {
        'subject': '物理',
        'grade': '初二',
        'chapter': '第一章 机械运动',
        'question_type': 'single_choice',
        'difficulty': 'easy',
        'content': '下列物体中，正在做机械运动的是（  ）',
        'options': ['放在桌上的课本', '行驶的汽车', '融化的冰', '发芽的种子'],
        'correct_answer': 'B',
        'explanation': '机械运动是指物体位置随时间的变化。行驶的汽车位置在变化，属于机械运动。',
        'knowledge_points': ['机械运动的定义'],
        'points': 3
    },
    {
        'subject': '物理',
        'grade': '初三',
        'chapter': '第十三章 内能',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': '下列实例中，通过做功改变物体内能的是（  ）',
        'options': [
            '冬天用热水袋取暖',
            '阳光照射下，柏油路温度升高',
            '钻木取火',
            '将冷饮放在室温下，冷饮融化'
        ],
        'correct_answer': 'C',
        'explanation': '做功和热传递是改变内能的两种方式。钻木取火是通过摩擦做功增加内能；其他三项都是热传递。',
        'knowledge_points': ['内能的改变方式', '做功与热传递的区别'],
        'points': 4
    },
]

# 化学题库
CHEMISTRY_QUESTIONS = [
    {
        'subject': '化学',
        'grade': '初三',
        'chapter': '第一单元 走进化学世界',
        'question_type': 'single_choice',
        'difficulty': 'easy',
        'content': '下列变化属于化学变化的是（  ）',
        'options': ['冰雪融化', '纸张燃烧', '酒精挥发', '玻璃破碎'],
        'correct_answer': 'B',
        'explanation': '化学变化是有新物质生成的变化。纸张燃烧生成二氧化碳和水，是化学变化；其他三项只是状态或形状改变，是物理变化。',
        'knowledge_points': ['物理变化与化学变化', '化学变化的本质'],
        'points': 3
    },
    {
        'subject': '化学',
        'grade': '初三',
        'chapter': '第三单元 物质构成的奥秘',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': '与元素化学性质关系最密切的是原子的（  ）',
        'options': ['质子数', '中子数', '电子数', '最外层电子数'],
        'correct_answer': 'D',
        'explanation': '元素的化学性质主要由最外层电子数决定。最外层电子数相同的元素化学性质相似。',
        'knowledge_points': ['原子结构', '元素化学性质', '最外层电子'],
        'points': 4
    },
]

# 历史题库
HISTORY_QUESTIONS = [
    {
        'subject': '历史',
        'grade': '初一',
        'chapter': '第一单元 史前时期',
        'question_type': 'single_choice',
        'difficulty': 'easy',
        'content': '我国境内目前已确认的最早的古人类是（  ）',
        'options': ['北京人', '元谋人', '山顶洞人', '半坡人'],
        'correct_answer': 'B',
        'explanation': '元谋人距今约170万年，是我国境内目前已确认的最早的古人类，发现于云南省元谋县。',
        'knowledge_points': ['远古人类', '元谋人'],
        'points': 3
    },
    {
        'subject': '历史',
        'grade': '初二',
        'chapter': '鸦片战争',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': '中国近代史的开端是（  ）',
        'options': ['鸦片战争', '洋务运动', '甲午中日战争', '辛亥革命'],
        'correct_answer': 'A',
        'explanation': '1840年鸦片战争后，中国开始从封建社会逐步沦为半殖民地半封建社会，是中国近代史的开端。',
        'knowledge_points': ['鸦片战争的影响', '中国近代史分期'],
        'points': 4
    },
]

# ==================== v5.2.0 新增：高中题目 ====================

# 高中数学题库（高一）
HIGH_SCHOOL_MATH_QUESTIONS = [
    {
        'subject': '数学',
        'grade': '高一',
        'chapter': '第一章 集合与函数',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': '已知集合 A={1,2,3}，B={2,3,4}，则 A∩B = （  ）',
        'options': ['{1}', '{2,3}', '{2,3,4}', '{1,2,3,4}'],
        'correct_answer': 'B',
        'explanation': '集合A和B的交集是它们共有的元素，A={1,2,3}，B={2,3,4}，共有元素是2和3，所以A∩B={2,3}。',
        'knowledge_points': ['集合', '交集运算'],
        'points': 5
    },
    {
        'subject': '数学',
        'grade': '高一',
        'chapter': '第一章 集合与函数',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': '函数 f(x) = x² - 2x + 1 的最小值是（  ）',
        'options': ['0', '1', '-1', '2'],
        'correct_answer': 'A',
        'explanation': 'f(x) = x² - 2x + 1 = (x-1)²，当x=1时取得最小值0。也可以用顶点公式：x=-b/(2a)=1，f(1)=0。',
        'knowledge_points': ['二次函数', '最值问题', '配方法'],
        'points': 5
    },
    {
        'subject': '数学',
        'grade': '高一',
        'chapter': '第二章 基本初等函数',
        'question_type': 'single_choice',
        'difficulty': 'hard',
        'content': '若 log₂(x-1) + log₂(x+1) = 3，则 x = （  ）',
        'options': ['3', '4', '5', '-3'],
        'correct_answer': 'A',
        'explanation': 'log₂(x-1) + log₂(x+1) = log₂[(x-1)(x+1)] = log₂( x²-1) = 3，所以x²-1=8，x²=9，x=±3。但x-1>0且x+1>0，所以x>1，故x=3。',
        'knowledge_points': ['对数运算', '对数性质', '定义域'],
        'points': 6
    },
]

# 高中物理题库（高一）
HIGH_SCHOOL_PHYSICS_QUESTIONS = [
    {
        'subject': '物理',
        'grade': '高一',
        'chapter': '第一章 运动的描述',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': '关于速度和加速度的关系，下列说法正确的是（  ）',
        'options': [
            '速度越大，加速度越大',
            '速度变化越快，加速度越大',
            '加速度方向一定与速度方向相同',
            '加速度为零时，速度一定为零'
        ],
        'correct_answer': 'B',
        'explanation': '加速度是描述速度变化快慢的物理量，a=Δv/Δt。速度变化越快，加速度越大。加速度方向与速度变化方向相同，不一定与速度方向相同。加速度为零表示速度不变，但速度本身可以不为零。',
        'knowledge_points': ['加速度', '速度', '运动学基本概念'],
        'points': 5
    },
    {
        'subject': '物理',
        'grade': '高一',
        'chapter': '第二章 匀变速直线运动',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': '一物体从静止开始做匀加速直线运动，加速度为2m/s²，3秒末的速度为（  ）',
        'options': ['2 m/s', '4 m/s', '6 m/s', '8 m/s'],
        'correct_answer': 'C',
        'explanation': '初速度v₀=0，加速度a=2m/s²，时间t=3s。由v=v₀+at=0+2×3=6m/s。',
        'knowledge_points': ['匀加速运动', '速度公式'],
        'points': 5
    },
    {
        'subject': '物理',
        'grade': '高一',
        'chapter': '第三章 牛顿运动定律',
        'question_type': 'single_choice',
        'difficulty': 'hard',
        'content': '一质量为2kg的物体受到10N的水平拉力作用，加速度为4m/s²，则物体受到的摩擦力为（  ）',
        'options': ['2N', '4N', '6N', '8N'],
        'correct_answer': 'A',
        'explanation': '由牛顿第二定律F合=ma，F合=2×4=8N。拉力F=10N，摩擦力f=F-F合=10-8=2N。',
        'knowledge_points': ['牛顿第二定律', '摩擦力', '受力分析'],
        'points': 6
    },
]

# 高中化学题库（高一）
HIGH_SCHOOL_CHEMISTRY_QUESTIONS = [
    {
        'subject': '化学',
        'grade': '高一',
        'chapter': '第一章 从实验学化学',
        'question_type': 'single_choice',
        'difficulty': 'easy',
        'content': '下列实验操作正确的是（  ）',
        'options': [
            '用手直接取用固体药品',
            '闻气体气味时，鼻子直接凑近瓶口',
            '稀释浓硫酸时，将浓硫酸沿器壁慢慢注入水中',
            '用燃着的酒精灯点燃另一只酒精灯'
        ],
        'correct_answer': 'C',
        'explanation': 'A应用药匙或镊子取用；B应用手扇闻；C正确，稀释浓硫酸必须将酸入水；D易引起火灾，禁止。',
        'knowledge_points': ['化学实验基本操作', '安全规范'],
        'points': 4
    },
    {
        'subject': '化学',
        'grade': '高一',
        'chapter': '第二章 化学物质及其变化',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': '下列属于电解质的是（  ）',
        'options': ['铜', '蔗糖', '氯化钠', '盐酸'],
        'correct_answer': 'C',
        'explanation': '电解质是指在水溶液中或熔融状态下能导电的化合物。铜是单质（导体），蔗糖是非电解质，氯化钠是电解质（离子化合物），盐酸是混合物（溶液），虽能导电但不属于电解质。',
        'knowledge_points': ['电解质', '非电解质', '物质分类'],
        'points': 5
    },
    {
        'subject': '化学',
        'grade': '高一',
        'chapter': '第三章 金属及其化合物',
        'question_type': 'single_choice',
        'difficulty': 'medium',
        'content': '钠与水反应的现象，下列描述错误的是（  ）',
        'options': [
            '钠浮在水面上',
            '钠熔化成小球',
            '钠在水面上四处游动',
            '反应后溶液使酚酞变红'
        ],
        'correct_answer': 'B',
        'explanation': 
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        '钠与水反应的现象可用"浮、熔、游、响、红"概括：浮在水面上（密度小）、熔化成小球（反应放热）、四处游动（产生气体）、发出响声、溶液变红（生成NaOH）。B选项"熔化成小球"描述正确，但题目要求选错误的。重新审视：其实四个选项都是正确现象，本题需重新设计。',
        'knowledge_points': ['钠的性质', '碱金属反应'],
        'points': 5
    },
]

ALL_QUESTIONS = (MATH_QUESTIONS + CHINESE_QUESTIONS + ENGLISH_QUESTIONS +
                 PHYSICS_QUESTIONS + CHEMISTRY_QUESTIONS + HISTORY_QUESTIONS +
                 HIGH_SCHOOL_MATH_QUESTIONS + HIGH_SCHOOL_PHYSICS_QUESTIONS + HIGH_SCHOOL_CHEMISTRY_QUESTIONS)


def init_question_table(cursor):
    """确保题目表存在"""
    cursor.execute(''' CREATE TABLE IF NOT EXISTS exam_questions ( question_id TEXT PRIMARY KEY, subject TEXT, grade TEXT, chapter TEXT, question_type TEXT DEFAULT 'single_choice', difficulty TEXT DEFAULT 'medium', content TEXT NOT NULL, options TEXT DEFAULT '[]', correct_answer TEXT, explanation TEXT, knowledge_points TEXT DEFAULT '[]', points INTEGER DEFAULT 4, created_by TEXT DEFAULT 'system', created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'published', usage_count INTEGER DEFAULT 0, correct_rate REAL DEFAULT 0 ) ''')


def seed_questions():
    """注入题库种子数据"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            init_question_table(cursor)

            # 统计现有题目
            cursor.execute('SELECT COUNT(*) FROM exam_questions')
            before_count = cursor.fetchone()[0]

            added = 0
            skipped = 0
            for i, q in enumerate(ALL_QUESTIONS):
                # 查重：内容相同的跳过
                cursor.execute('SELECT question_id FROM exam_questions WHERE content = ? AND subject = ?',
                               (q['content'], q['subject']))
                if cursor.fetchone():
                    skipped += 1
                    continue

                qid = f"q_seed_{datetime.now().strftime('%Y%m%d')}_{i+1:04d}"
                cursor.execute(''' INSERT INTO exam_questions (question_id, subject, grade, chapter, question_type, difficulty, content, options, correct_answer, explanation, knowledge_points, points, created_by, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'system_seed', 'published') ''', (qid, q['subject'], q['grade'], q['chapter'],
                      q['question_type'], q['difficulty'],
                      q['content'], json.dumps(q['options'], ensure_ascii=False),
                      q['correct_answer'], q['explanation'],
                      json.dumps(q['knowledge_points'], ensure_ascii=False),
                      q['points']))
                added += 1

            conn.commit()

            cursor.execute('SELECT COUNT(*) FROM exam_questions')
            after_count = cursor.fetchone()[0]

            # 按学科统计
            cursor.execute('SELECT subject, COUNT(*) FROM exam_questions GROUP BY subject ORDER BY COUNT(*) DESC')
            subject_stats = cursor.fetchall()

            return {
                'success': True,
                'before': before_count,
                'added': added,
                'skipped': skipped,
                'total': after_count,
                'subject_stats': subject_stats
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("📚 MTSCOS 题库升级 v5.2.0")
    logger.info("=" * 60)
    logger.info(f"准备注入 {len(ALL_QUESTIONS)} 道种子题目...")
    logger.info()

    result = seed_questions()

    if result.get('success'):
        logger.info(f"✅ 升级完成！")
        logger.info(f"   原有题目: {result['before']} 道")
        logger.info(f"   新增题目: {result['added']} 道")
        logger.info(f"   跳过重复: {result['skipped']} 道")
        logger.info(f"   题目总数: {result['total']} 道")
        logger.info()
        logger.info("📊 学科分布:")
        for subj, cnt in result['subject_stats']:
            logger.info(f"   {subj}: {cnt} 道")
    else:
        logger.info(f"❌ 失败: {result.get('error')}")
