"""
大规模题库数据生成脚本
包含9年制义务教育、成人教育、竞赛题库、英语考试、日语考试等
"""

import sqlite3
import json
import time
import os
import random
import uuid

QUESTION_BANKS = [
    # 9年制义务教育题库
    {"bank_id": "k9_math", "name": "九年制数学题库", "subject": "math", "grade_level": "1-9", "description": "覆盖小学至初中数学全部知识点"},
    {"bank_id": "k9_chinese", "name": "九年制语文题库", "subject": "chinese", "grade_level": "1-9", "description": "覆盖小学至初中语文全部知识点"},
    {"bank_id": "k9_english", "name": "九年制英语题库", "subject": "english", "grade_level": "1-9", "description": "覆盖小学至初中英语全部知识点"},
    {"bank_id": "k9_physics", "name": "九年制物理题库", "subject": "physics", "grade_level": "7-9", "description": "覆盖初中物理全部知识点"},
    {"bank_id": "k9_chemistry", "name": "九年制化学题库", "subject": "chemistry", "grade_level": "9", "description": "覆盖初中化学全部知识点"},
    {"bank_id": "k9_biology", "name": "九年制生物题库", "subject": "biology", "grade_level": "7-9", "description": "覆盖初中生物全部知识点"},
    {"bank_id": "k9_history", "name": "九年制历史题库", "subject": "history", "grade_level": "7-9", "description": "覆盖初中历史全部知识点"},
    {"bank_id": "k9_geography", "name": "九年制地理题库", "subject": "geography", "grade_level": "7-9", "description": "覆盖初中地理全部知识点"},
    
    # 成人教育题库
    {"bank_id": "adult_math", "name": "成人高考数学题库", "subject": "math", "grade_level": "adult", "description": "成人高考数学真题及模拟题"},
    {"bank_id": "adult_chinese", "name": "成人高考语文题库", "subject": "chinese", "grade_level": "adult", "description": "成人高考语文真题及模拟题"},
    {"bank_id": "adult_english", "name": "成人高考英语题库", "subject": "english", "grade_level": "adult", "description": "成人高考英语真题及模拟题"},
    {"bank_id": "adult_politics", "name": "成人高考政治题库", "subject": "politics", "grade_level": "adult", "description": "成人高考政治真题及模拟题"},
    {"bank_id": "adult_history", "name": "成人高考历史题库", "subject": "history", "grade_level": "adult", "description": "成人高考历史真题及模拟题"},
    {"bank_id": "adult_geography", "name": "成人高考地理题库", "subject": "geography", "grade_level": "adult", "description": "成人高考地理真题及模拟题"},
    
    # 自主招生题库
    {"bank_id": "zizhu_math", "name": "自主招生数学题库", "subject": "math", "grade_level": "high", "description": "高校自主招生数学试题"},
    {"bank_id": "zizhu_physics", "name": "自主招生物理题库", "subject": "physics", "grade_level": "high", "description": "高校自主招生物理试题"},
    {"bank_id": "zizhu_chemistry", "name": "自主招生化学题库", "subject": "chemistry", "grade_level": "high", "description": "高校自主招生化学试题"},
    
    # AMC8数学竞赛
    {"bank_id": "amc8", "name": "AMC8数学竞赛题库", "subject": "math", "grade_level": "middle", "description": "美国AMC8数学竞赛历年真题"},
    
    # 华罗庚数学竞赛
    {"bank_id": "huageng_math", "name": "华罗庚金杯数学竞赛题库", "subject": "math", "grade_level": "1-9", "description": "华罗庚金杯少年数学邀请赛历年真题"},
    
    # 新概念英语
    {"bank_id": "newconcept_eng", "name": "新概念英语题库", "subject": "english", "grade_level": "all", "description": "新概念英语1-4册练习题"},
    
    # 新东方英语
    {"bank_id": "xdf_english", "name": "新东方英语题库", "subject": "english", "grade_level": "all", "description": "新东方英语培训习题"},
    
    # 雅思
    {"bank_id": "ielts", "name": "雅思题库", "subject": "english", "grade_level": "adult", "description": "IELTS雅思考试真题"},
    
    # 托福
    {"bank_id": "toefl", "name": "托福题库", "subject": "english", "grade_level": "adult", "description": "TOEFL托福考试真题"},
    
    # 国际数学竞赛
    {"bank_id": "imo", "name": "IMO国际数学奥林匹克题库", "subject": "math", "grade_level": "high", "description": "国际数学奥林匹克竞赛历年真题"},
    {"bank_id": "usamo", "name": "USAMO美国数学奥林匹克题库", "subject": "math", "grade_level": "high", "description": "美国数学奥林匹克竞赛历年真题"},
    {"bank_id": "cmo", "name": "CMO中国数学奥林匹克题库", "subject": "math", "grade_level": "high", "description": "中国数学奥林匹克竞赛历年真题"},
    {"bank_id": "romanian_math", "name": "罗马尼亚数学大师赛题库", "subject": "math", "grade_level": "high", "description": "罗马尼亚数学大师赛历年真题"},
    {"bank_id": "russian_math", "name": "俄罗斯数学竞赛题库", "subject": "math", "grade_level": "high", "description": "俄罗斯数学竞赛历年真题"},
    
    # 日语考试
    {"bank_id": "jlpt_n1", "name": "JLPT N1题库", "subject": "japanese", "grade_level": "N1", "description": "日语能力考试N1真题"},
    {"bank_id": "jlpt_n2", "name": "JLPT N2题库", "subject": "japanese", "grade_level": "N2", "description": "日语能力考试N2真题"},
    {"bank_id": "jlpt_n3", "name": "JLPT N3题库", "subject": "japanese", "grade_level": "N3", "description": "日语能力考试N3真题"},
    {"bank_id": "jlpt_n4", "name": "JLPT N4题库", "subject": "japanese", "grade_level": "N4", "description": "日语能力考试N4真题"},
    {"bank_id": "jlpt_n5", "name": "JLPT N5题库", "subject": "japanese", "grade_level": "N5", "description": "日语能力考试N5真题"},
    {"bank_id": "japanese_reading", "name": "日语精读练习题库", "subject": "japanese", "grade_level": "all", "description": "日语精读练习题及往年真题"},
]

MATH_KNOWLEDGE_POINTS = [
    "数与代数", "方程与不等式", "函数", "几何", "三角", "数列", "概率统计",
    "集合", "逻辑", "向量", "复数", "导数", "积分", "矩阵", "组合数学",
    "数论", "图论", "极值问题", "应用题", "综合题"
]

CHINESE_KNOWLEDGE_POINTS = [
    "现代汉语", "古代汉语", "阅读理解", "文言文", "诗词鉴赏", "写作",
    "文学常识", "修辞手法", "语法", "词汇", "标点符号", "名言名句",
    "文学作品", "文化常识", "语言运用"
]

ENGLISH_KNOWLEDGE_POINTS = [
    "词汇", "语法", "阅读理解", "完形填空", "听力", "写作", "翻译",
    "口语", "语法填空", "短文改错", "同义替换", "固定搭配",
    "时态", "语态", "从句", "词汇辨析"
]

PHYSICS_KNOWLEDGE_POINTS = [
    "力学", "运动学", "能量", "动量", "电学", "磁学", "光学",
    "热学", "波动", "近代物理", "实验题", "计算题", "综合题"
]

CHEMISTRY_KNOWLEDGE_POINTS = [
    "物质结构", "化学反应", "元素化合物", "有机化学", "化学平衡",
    "电化学", "化学反应速率", "溶液", "化学实验", "计算题", "推断题"
]

BIOLOGY_KNOWLEDGE_POINTS = [
    "细胞", "遗传", "进化", "生态", "代谢", "生命调节", "生物实验",
    "分子生物学", "生态学", "生物技术", "生物工程"
]

HISTORY_KNOWLEDGE_POINTS = [
    "中国古代史", "中国近代史", "中国现代史", "世界古代史", "世界近代史",
    "世界现代史", "历史人物", "历史事件", "历史文献", "历史评价"
]

GEOGRAPHY_KNOWLEDGE_POINTS = [
    "自然地理", "人文地理", "区域地理", "地理环境", "地图", "气候",
    "地形", "水文", "人口", "城市", "农业", "工业", "交通"
]

POLITICS_KNOWLEDGE_POINTS = [
    "马克思主义原理", "毛泽东思想", "邓小平理论", "政治经济学",
    "哲学", "时事政治", "法律基础", "政治常识"
]

JAPANESE_KNOWLEDGE_POINTS = [
    "词汇", "语法", "阅读理解", "听力", "写作", "翻译", "口语",
    "汉字", "假名", "句型", "敬语", "阅读理解", "完形填空"
]

KNOWLEDGE_POINTS_MAP = {
    "math": MATH_KNOWLEDGE_POINTS,
    "chinese": CHINESE_KNOWLEDGE_POINTS,
    "english": ENGLISH_KNOWLEDGE_POINTS,
    "physics": PHYSICS_KNOWLEDGE_POINTS,
    "chemistry": CHEMISTRY_KNOWLEDGE_POINTS,
    "biology": BIOLOGY_KNOWLEDGE_POINTS,
    "history": HISTORY_KNOWLEDGE_POINTS,
    "geography": GEOGRAPHY_KNOWLEDGE_POINTS,
    "politics": POLITICS_KNOWLEDGE_POINTS,
    "japanese": JAPANESE_KNOWLEDGE_POINTS,
}

SUBJECT_TITLES = {
    "math": ["关于{}的计算问题", "求解{}", "证明{}", "{}的应用", "{}的性质", "{}的求解", "计算{}", "化简{}"],
    "chinese": ["阅读下面的文章，回答问题", "翻译下列文言文", "赏析这首诗词", "根据要求写作", "解释下列词语", "修改病句", "默写填空", "仿写句子"],
    "english": ["Choose the correct answer", "Complete the sentence", "Read the passage and answer", "Translate the sentence", "Fill in the blanks", "Rewrite the sentence", "Choose the best word", "Correct the error"],
    "physics": ["{}的计算", "分析{}现象", "解释{}原理", "证明{}公式", "{}的应用", "计算{}的值", "分析{}过程", "{}的实验"],
    "chemistry": ["写出{}的化学式", "配平下列方程式", "计算{}的量", "分析{}反应", "{}的性质", "推断{}物质", "{}的实验", "{}的应用"],
    "biology": ["解释{}现象", "分析{}过程", "{}的结构", "{}的功能", "{}的原理", "{}的实验", "{}的应用", "{}的进化"],
    "history": ["分析{}事件", "评价{}人物", "简述{}过程", "比较{}异同", "{}的背景", "{}的影响", "{}的意义", "{}的原因"],
    "geography": ["分析{}气候", "描述{}地形", "{}的区位因素", "{}的地理特征", "{}的分布", "{}的成因", "{}的影响", "{}的对策"],
    "politics": ["阐述{}原理", "分析{}现象", "{}的意义", "{}的实践", "{}的理论", "{}的观点", "{}的作用", "{}的方法"],
    "japanese": ["次の文章を読んで答えなさい", "次の単語の意味を答えなさい", "次の文を訳しなさい", "空欄を埋めなさい", "次の選択肢から正しいものを選びなさい", "次の文の文法を分析しなさい"],
}

MATH_CONTENT_TEMPLATES = [
    "已知{}，求{}的值。",
    "设{}，证明{}。",
    "解方程：{}",
    "化简：{}",
    "计算：{}",
    "求函数{}的{}。",
    "在△ABC中，{}，求{}。",
    "已知数列{}，求{}。",
    "设{}，求{}的最小值。",
    "证明不等式：{}。",
]

CHINESE_CONTENT_TEMPLATES = [
    "阅读下面的文字，完成{}题。\n\n{}",
    "翻译下列文言文句子：{}",
    "赏析{}这首诗，分析其{}。",
    "根据以下材料，写一篇{}字的{}文。\n\n材料：{}",
    "解释下列词语在文中的含义：{}",
    "修改下列病句：{}",
    "默写填空：{}",
    "仿照例句，写一个{}句：{}",
]

ENGLISH_CONTENT_TEMPLATES = [
    "Choose the correct word to complete the sentence: {} ______ {}",
    "Read the passage and answer the questions.\n\nPassage: {}\n\nQuestion: {}",
    "Translate the following sentence into English: {}",
    "Fill in the blanks with the correct form of the verb: {}",
    "Complete the sentence with the appropriate preposition: {}",
    "Choose the best answer: {}",
    "Correct the error in the sentence: {}",
    "Rewrite the sentence without changing its meaning: {}",
]

PHYSICS_CONTENT_TEMPLATES = [
    "一个{}质量为{}kg的物体，在{}作用下，{}，求{}。",
    "如图所示，{}，已知{}，求{}。",
    "在{}过程中，{}，求{}。",
    "证明{}定律在{}情况下成立。",
    "分析{}现象的{}原因。",
    "计算{}的{}值。",
    "设计一个实验验证{}。",
    "解释{}原理。",
]

CHEMISTRY_CONTENT_TEMPLATES = [
    "写出{}的化学方程式并配平。",
    "计算{}mol {}完全反应需要{}mol {}。",
    "分析{}的{}性质。",
    "推断{}物质的化学式。",
    "解释{}反应的{}原理。",
    "计算{}溶液的{}浓度。",
    "设计实验验证{}。",
    "比较{}和{}的{}差异。",
]

JAPANESE_CONTENT_TEMPLATES = [
    "次の文章を読んで、下の問いに答えなさい。\n\n{}",
    "次の単語の読み方を書きなさい：{}",
    "次の文を中国語に訳しなさい：{}",
    "次の空欄に適切な言葉を入れなさい：{}",
    "次の選択肢から正しいものを一つ選びなさい：{}",
    "次の文の文法的誤りを指摘しなさい：{}",
]

CONTENT_TEMPLATES_MAP = {
    "math": MATH_CONTENT_TEMPLATES,
    "chinese": CHINESE_CONTENT_TEMPLATES,
    "english": ENGLISH_CONTENT_TEMPLATES,
    "physics": PHYSICS_CONTENT_TEMPLATES,
    "chemistry": CHEMISTRY_CONTENT_TEMPLATES,
    "biology": ["解释{}现象。", "分析{}过程。", "{}的结构特点是什么？", "{}的功能是什么？", "{}的原理是什么？", "设计实验验证{}。"],
    "history": ["分析{}事件的背景和影响。", "评价{}历史人物。", "简述{}历史过程。", "比较{}和{}的异同。", "{}的原因是什么？", "{}的意义是什么？"],
    "geography": ["分析{}气候的成因。", "描述{}地形特征。", "{}的区位因素有哪些？", "{}的地理特征是什么？", "{}的分布规律是什么？", "{}的影响有哪些？"],
    "politics": ["阐述{}原理。", "分析{}现象。", "{}的意义是什么？", "{}的实践应用。", "{}的理论基础。", "{}的作用是什么？"],
    "japanese": JAPANESE_CONTENT_TEMPLATES,
}

def generate_math_expression():
    """生成数学表达式"""
    expressions = [
        "x^2 + 2x + 1", "2x + 3 = 7", "3x - 5 = 10", "(x + 2)(x - 3)",
        "sqrt(x^2 + y^2)", "sin(x) + cos(x)", "x^3 - 3x^2 + 2x",
        "log(x) + log(y)", "e^x + e^(-x)", "x/(x+1) + (x+1)/x",
        "a^2 + b^2", "a^3 + b^3", "(a+b)^2", "(a-b)^3",
        "x^2 - 4x + 3", "2x^2 + 5x - 3", "x^3 - 8", "4x^2 - 9",
        "sin^2(x) + cos^2(x)", "tan(x) = sin(x)/cos(x)",
        "S_n = n(a1 + an)/2", "an = a1 + (n-1)d",
        "C(n,k) = n!/(k!(n-k)!)", "P(n,k) = n!/(n-k)!",
    ]
    return random.choice(expressions)

def generate_chinese_text():
    """生成中文文本"""
    texts = [
        "春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。",
        "明月几时有，把酒问青天。不知天上宫阙，今夕是何年。",
        "人生自古谁无死，留取丹心照汗青。",
        "学而不思则罔，思而不学则殆。",
        "海内存知己，天涯若比邻。",
        "落红不是无情物，化作春泥更护花。",
        "先天下之忧而忧，后天下之乐而乐。",
        "路漫漫其修远兮，吾将上下而求索。",
        "长风破浪会有时，直挂云帆济沧海。",
        "会当凌绝顶，一览众山小。",
        "大漠孤烟直，长河落日圆。",
        "采菊东篱下，悠然见南山。",
        "枯藤老树昏鸦，小桥流水人家，古道西风瘦马。",
        "山重水复疑无路，柳暗花明又一村。",
        "沉舟侧畔千帆过，病树前头万木春。",
    ]
    return random.choice(texts)

def generate_english_text():
    """生成英文文本"""
    texts = [
        "The quick brown fox jumps over the lazy dog.",
        "A journey of a thousand miles begins with a single step.",
        "Knowledge is power.",
        "To be or not to be, that is the question.",
        "All that glitters is not gold.",
        "Where there is a will, there is a way.",
        "Practice makes perfect.",
        "Time flies when you're having fun.",
        "The early bird catches the worm.",
        "Actions speak louder than words.",
        "Every cloud has a silver lining.",
        "Don't put all your eggs in one basket.",
        "A picture is worth a thousand words.",
        "When in Rome, do as the Romans do.",
        "The best things in life are free.",
    ]
    return random.choice(texts)

def generate_japanese_text():
    """生成日文文本"""
    texts = [
        "日本語の勉強は楽しいです。",
        "毎日日本語を勉強しています。",
        "東京はとても美しい都市です。",
        "朝早く起きて散歩します。",
        "友達と一緒に食事をしました。",
        "本を読むのが好きです。",
        "天気がいいので公園へ行きます。",
        "勉強が終わったら遊びます。",
        "家族と一緒に旅行に行きました。",
        "日本の文化を学びたいです。",
    ]
    return random.choice(texts)

def generate_content(subject):
    """生成题目内容"""
    templates = CONTENT_TEMPLATES_MAP.get(subject, ["{}"])
    template = random.choice(templates)
    placeholder_count = template.count("{}")
    
    if subject == "math":
        args = [generate_math_expression()] * placeholder_count
    elif subject == "chinese":
        args = [generate_chinese_text()] * placeholder_count
    elif subject == "english":
        args = [generate_english_text()[:20]] * placeholder_count
    elif subject == "japanese":
        args = [generate_japanese_text()] * placeholder_count
    elif subject == "physics":
        objects = ["小球", "木块", "小车", "电荷", "导体", "透镜", "弹簧"]
        actions = ["从高处落下", "在水平面上运动", "受到力的作用", "匀速运动", "加速运动"]
        forces = ["重力", "弹力", "摩擦力", "电场力"]
        args = []
        for _ in range(placeholder_count):
            args.append(random.choice(objects + actions + forces))
    elif subject == "chemistry":
        substances = ["H2O", "NaCl", "HCl", "NaOH", "CO2", "Fe", "Cu", "Ag"]
        reactions = ["分解", "化合", "置换", "复分解", "氧化还原"]
        args = []
        for _ in range(placeholder_count):
            args.append(random.choice(substances + reactions))
    else:
        kps = KNOWLEDGE_POINTS_MAP.get(subject, ["知识点"])
        args = [random.choice(kps)] * placeholder_count
    
    return template.format(*args)

def generate_title(subject):
    """生成题目标题"""
    kps = KNOWLEDGE_POINTS_MAP.get(subject, ["知识点"])
    templates = SUBJECT_TITLES.get(subject, ["{}"])
    return random.choice(templates).format(random.choice(kps))

def generate_question(bank_id, subject, index):
    """生成单条题目"""
    types = ["choice", "fill", "essay", "judge", "computation"]
    q_type = random.choice(types)
    
    if q_type == "choice":
        options = [
            {"label": "A", "content": "选项A内容"},
            {"label": "B", "content": "选项B内容"},
            {"label": "C", "content": "选项C内容"},
            {"label": "D", "content": "选项D内容"},
        ]
        answer = {"type": "choice", "answer": random.choice(["A", "B", "C", "D"])}
    elif q_type == "fill":
        options = None
        answer = {"type": "fill", "answer": "____"}
    elif q_type == "judge":
        options = [
            {"label": "A", "content": "正确"},
            {"label": "B", "content": "错误"},
        ]
        answer = {"type": "judge", "answer": random.choice(["A", "B"])}
    else:
        options = None
        answer = {"type": q_type, "answer": "参考答案"}
    
    kps = KNOWLEDGE_POINTS_MAP.get(subject, [])
    knowledge_points = random.sample(kps, min(random.randint(1, 3), len(kps))) if kps else []
    
    return {
        "question_id": f"q_{bank_id}_{index:06d}",
        "bank_id": bank_id,
        "type": q_type,
        "content": generate_content(subject),
        "options": json.dumps(options) if options else None,
        "answer": json.dumps(answer),
        "analysis": "本题考查{}知识点。解题思路：{}。",
        "difficulty": random.randint(1, 5),
        "knowledge_points": json.dumps(knowledge_points),
        "tags": json.dumps([subject, random.choice(knowledge_points) if knowledge_points else subject]),
        "score": random.randint(2, 15),
        "time_limit": random.randint(30, 300),
        "usage_count": 0,
        "correct_rate": round(random.uniform(0.3, 0.95), 2),
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
    }

def create_banks(db, conn):
    """创建题库"""
    current_time = int(time.time())
    for bank in QUESTION_BANKS:
        bank_data = bank.copy()
        bank_data['tags'] = json.dumps([bank['subject'], bank['grade_level']])
        bank_data['question_count'] = 0
        bank_data['creator_id'] = "admin"
        bank_data['is_public'] = 1
        bank_data['status'] = "active"
        bank_data['created_at'] = current_time
        bank_data['updated_at'] = current_time
        try:
            db.add('question_banks', bank_data)
            print(f"  ✅ 创建题库: {bank['name']}")
        except Exception as e:
            print(f"  ⏭️ 题库已存在: {bank['name']}")

def generate_questions_for_bank(conn, bank_id, subject, count):
    """为指定题库生成题目"""
    print(f"    正在生成 {count} 条题目...")
    
    questions = []
    for i in range(count):
        q = generate_question(bank_id, subject, i + 1)
        questions.append(q)
        
        if len(questions) >= 1000:
            batch_insert(conn, questions)
            questions = []
            print(f"      已生成 {i + 1} 条...")
    
    if questions:
        batch_insert(conn, questions)
    
    return count

def batch_insert(conn, questions):
    """批量插入题目"""
    placeholders = ", ".join(["(" + ", ".join(["?"] * 16) + ")"] * len(questions))
    
    values = []
    for q in questions:
        values.extend([
            q['question_id'], q['bank_id'], q['type'], q['content'],
            q['options'], q['answer'], q['analysis'], q['difficulty'],
            q['knowledge_points'], q['tags'], q['score'], q['time_limit'],
            q['usage_count'], q['correct_rate'], q['created_at'], q['updated_at']
        ])
    
    conn.execute(f"""
        INSERT OR IGNORE INTO questions 
        (question_id, bank_id, type, content, options, answer, analysis, difficulty,
         knowledge_points, tags, score, time_limit, usage_count, correct_rate, created_at, updated_at)
        VALUES {placeholders}
    """, values)
    conn.commit()

def update_bank_counts(conn):
    """更新题库题目数量"""
    conn.execute("""
        UPDATE question_banks 
        SET question_count = (SELECT COUNT(*) FROM questions WHERE questions.bank_id = question_banks.bank_id),
            updated_at = ?
    """, (int(time.time()),))
    conn.commit()

def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║           大规模题库数据生成工具                           ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    start_time = time.time()
    
    db_path = "data/mtscos_new.db"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, '..', db_path)
    
    print(f"📦 数据库路径: {db_path}")
    
    from database_schema import SCHEMA
    from database_schema_base import EnhancedDatabaseManager
    
    db = EnhancedDatabaseManager(full_path, SCHEMA)
    conn = db.conn
    
    print("\n📁 创建题库...")
    create_banks(db, conn)
    
    print("\n📝 生成题目数据...")
    
    total_questions = 0
    
    # 为每个题库生成题目
    bank_question_counts = {
        # 九年制题库 - 每个8000题
        "k9_math": 8000,
        "k9_chinese": 8000,
        "k9_english": 8000,
        "k9_physics": 5000,
        "k9_chemistry": 4000,
        "k9_biology": 4000,
        "k9_history": 5000,
        "k9_geography": 5000,
        
        # 成人教育题库 - 每个5000题
        "adult_math": 5000,
        "adult_chinese": 5000,
        "adult_english": 5000,
        "adult_politics": 4000,
        "adult_history": 4000,
        "adult_geography": 4000,
        
        # 自主招生题库 - 每个3000题
        "zizhu_math": 3000,
        "zizhu_physics": 3000,
        "zizhu_chemistry": 3000,
        
        # AMC8 - 1000题
        "amc8": 1000,
        
        # 华罗庚数学竞赛 - 2000题
        "huageng_math": 2000,
        
        # 新概念英语 - 5000题
        "newconcept_eng": 5000,
        
        # 新东方英语 - 5000题
        "xdf_english": 5000,
        
        # 雅思 - 3000题
        "ielts": 3000,
        
        # 托福 - 3000题
        "toefl": 3000,
        
        # 国际数学竞赛
        "imo": 1000,
        "usamo": 1000,
        "cmo": 1000,
        "romanian_math": 500,
        "russian_math": 500,
        
        # 日语考试
        "jlpt_n1": 3000,
        "jlpt_n2": 3000,
        "jlpt_n3": 2500,
        "jlpt_n4": 2500,
        "jlpt_n5": 2500,
        "japanese_reading": 3000,
    }
    
    subject_map = {bank['bank_id']: bank['subject'] for bank in QUESTION_BANKS}
    
    for bank_id, count in bank_question_counts.items():
        subject = subject_map.get(bank_id, "math")
        print(f"\n  📚 题库: {bank_id} ({count}题)")
        count_generated = generate_questions_for_bank(conn, bank_id, subject, count)
        total_questions += count_generated
        print(f"    ✅ 完成: {count_generated} 条题目")
    
    print("\n🔄 更新题库统计...")
    update_bank_counts(conn)
    
    db.close()
    
    elapsed = time.time() - start_time
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                   生成完成！                              ║
╠══════════════════════════════════════════════════════════╣
║  题库数量: {len(QUESTION_BANKS):<50}  ║
║  题目总数: {total_questions:<50}  ║
║  耗时: {elapsed:.2f} 秒                    ║
╚══════════════════════════════════════════════════════════╝

📊 题库分类统计:
  - 九年制义务教育: 8个题库，约32000题
  - 成人教育: 6个题库，约16500题
  - 自主招生: 3个题库，约6000题
  - 数学竞赛: 6个题库，约3300题
  - 英语考试: 4个题库，约10000题
  - 日语考试: 6个题库，约10500题
    """)


if __name__ == '__main__':
    main()
