#!/usr/bin/env python3
"""
简化版题库自动扩充系统
直接操作数据库，不依赖Flask应用初始化
"""

import sqlite3
import json
import random
from datetime import datetime

# 知识库
knowledge_base = {
    "日语": {
        "N5": {"concepts": ["平假名", "片假名", "基础汉字", "数字", "时间", "问候语"], "difficulty": 1},
        "N4": {"concepts": ["动词变形", "形容词", "助词", "日常会话"], "difficulty": 2},
        "N3": {"concepts": ["中级语法", "敬语", "中篇文章", "听力"], "difficulty": 4},
        "N2": {"concepts": ["高级语法", "商务日语", "新闻阅读", "学术听力"], "difficulty": 6},
        "N1": {"concepts": ["专业语法", "古典日语", "学术论文", "文学作品"], "difficulty": 8},
    },
    "英语": {
        "九年制基础": {"concepts": ["字母", "基础词汇", "简单句", "一般时态"], "difficulty": 1},
        "九年制进阶": {"concepts": ["时态综合", "从句", "被动语态", "阅读理解"], "difficulty": 3},
        "四级": {"concepts": ["词汇4500", "快速阅读", "听力", "翻译", "写作"], "difficulty": 4},
        "六级": {"concepts": ["词汇5500", "深度阅读", "学术听力", "汉译英", "议论文"], "difficulty": 5},
        "专四": {"concepts": ["词汇8000", "文学阅读", "专业听力", "翻译技巧", "学术写作"], "difficulty": 6},
        "专八": {"concepts": ["词汇13000", "同声传译", "翻译理论", "研究论文", "英美文学"], "difficulty": 8},
    },
    "数学": {
        "九年制基础": {"concepts": ["整数运算", "分数", "小数", "百分数", "基础几何"], "difficulty": 2},
        "九年制进阶": {"concepts": ["代数", "函数", "平面几何", "概率统计"], "difficulty": 4},
        "高中数学": {"concepts": ["集合", "三角函数", "向量", "解析几何", "导数"], "difficulty": 5},
        "高等数学": {"concepts": ["微积分", "线性代数", "微分方程", "复变函数"], "difficulty": 7},
    },
    "物理": {
        "九年制基础": {"concepts": ["声现象", "光现象", "热现象", "简单机械", "力与运动"], "difficulty": 2},
        "九年制进阶": {"concepts": ["电学", "欧姆定律", "电功率", "磁现象"], "difficulty": 4},
        "高中物理": {"concepts": ["力学", "运动学", "牛顿定律", "电磁学", "光学"], "difficulty": 5},
        "大学物理": {"concepts": ["理论力学", "热力学", "电磁学", "量子力学"], "difficulty": 7},
    },
    "化学": {
        "九年制基础": {"concepts": ["物质构成", "元素", "化学式", "化学反应"], "difficulty": 2},
        "九年制进阶": {"concepts": ["金属", "非金属", "有机物", "化学实验"], "difficulty": 4},
        "高中化学": {"concepts": ["物质的量", "氧化还原", "化学平衡", "电化学", "有机化学"], "difficulty": 5},
        "大学化学": {"concepts": ["无机化学", "有机化学", "分析化学", "物理化学"], "difficulty": 7},
    },
}

def generate_question(subject, level, concept, difficulty):
    """生成题目"""
    question_types = ["multiple_choice", "fill_blank", "short_answer"]
    q_type = random.choice(question_types)
    
    if q_type == "multiple_choice":
        question = f"关于{subject}{level}的{concept}，以下说法正确的是："
        options = [f"{concept}的正确描述", "错误描述1", "错误描述2", "错误描述3"]
        answer = "A"
    elif q_type == "fill_blank":
        question = f"{concept}是_________。"
        answer = concept
        options = []
    else:
        question = f"请简述{concept}的主要特点。"
        answer = f"{concept}的主要特点包括..."
        options = []
    
    return {
        "content": question,
        "answer": answer,
        "explanation": f"本题考查{subject}{level}的{concept}知识点，难度等级{difficulty}。",
        "question_type": q_type,
        "options": json.dumps(options) if options else "[]",
        "exam_type": get_exam_type(subject, level),
        "exam_level": level,
        "difficulty_description": f"难度{difficulty}"
    }

def get_exam_type(subject, level):
    """获取考试类型"""
    if subject == "日语":
        return "JLPT"
    elif subject == "英语":
        if "九年制" in level:
            return "九年义务教育"
        elif "四" in level or "六" in level:
            return "CET"
        else:
            return "TEM"
    else:
        if "九年制" in level:
            return "九年义务教育"
        elif "高中" in level:
            return "高考"
        else:
            return "大学"

def expand_database():
    """扩充数据库"""
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    
    print("=" * 80)
    print("开始自动扩充题库")
    print("=" * 80)
    
    total_generated = 0
    
    for subject, levels in knowledge_base.items():
        print(f"\n生成 {subject} 题目...")
        
        for level, data in levels.items():
            concepts = data["concepts"]
            difficulty = data["difficulty"]
            
            # 为每个概念生成5道题目
            for concept in concepts:
                for i in range(5):
                    question_data = generate_question(subject, level, concept, difficulty)
                    
                    # 获取或创建分类
                    cursor.execute("SELECT id FROM question_categories WHERE name = ?", (concept,))
                    row = cursor.fetchone()
                    if row:
                        category_id = row[0]
                    else:
                        cursor.execute("INSERT INTO question_categories (name, description) VALUES (?, ?)",
                                     (concept, f"{subject}-{concept}"))
                        category_id = cursor.lastrowid
                    
                    # 获取或创建语言
                    cursor.execute("SELECT id FROM question_languages WHERE name = ?", (subject,))
                    row = cursor.fetchone()
                    if row:
                        lang_id = row[0]
                    else:
                        cursor.execute("INSERT INTO question_languages (name, code) VALUES (?, ?)",
                                     (subject, subject.lower()))
                        lang_id = cursor.lastrowid
                    
                    # 获取或创建难度
                    cursor.execute("SELECT id FROM question_difficulties WHERE difficulty_level = ?", (f"Level {difficulty}",))
                    row = cursor.fetchone()
                    if row:
                        diff_id = row[0]
                    else:
                        cursor.execute("INSERT INTO question_difficulties (difficulty_level, description) VALUES (?, ?)",
                                     (f"Level {difficulty}", f"难度等级 {difficulty}"))
                        diff_id = cursor.lastrowid
                    
                    # 插入题目
                    cursor.execute("""
                        INSERT INTO questions 
                        (content, answer, explanation, category_id, language_id, level_id,
                         question_type, options, exam_type, exam_level, difficulty_description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        question_data["content"],
                        question_data["answer"],
                        question_data["explanation"],
                        category_id, lang_id, diff_id,
                        question_data["question_type"],
                        question_data["options"],
                        question_data["exam_type"],
                        question_data["exam_level"],
                        question_data["difficulty_description"]
                    ))
                    
                    total_generated += 1
        
        print(f"  {subject} 完成，已生成 {total_generated} 题")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 80)
    print(f"扩充完成！共生成 {total_generated} 道新题目")
    print("=" * 80)
    
    # 显示统计
    show_statistics()

def show_statistics():
    """显示统计"""
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    
    print("\n题库统计：")
    print("-" * 80)
    
    # 总题目数
    cursor.execute("SELECT COUNT(*) FROM questions")
    print(f"总题目数: {cursor.fetchone()[0]}")
    
    # 按考试类型
    print("\n按考试类型：")
    cursor.execute("SELECT exam_type, COUNT(*) FROM questions WHERE exam_type IS NOT NULL GROUP BY exam_type")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} 题")
    
    # 按学科
    print("\n按学科：")
    cursor.execute("""
        SELECT ql.name, COUNT(*) FROM questions q
        JOIN question_languages ql ON q.language_id = ql.id
        GROUP BY ql.name
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} 题")
    
    conn.close()

if __name__ == "__main__":
    expand_database()
