#!/usr/bin/env python3
"""
验证9年制义务教育题库扩充结果
"""

import sys
import os
import logging

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.question import QuestionManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_9year_education():
    """
    验证9年制义务教育题库扩充结果
    """
    print("================================================================================")
    print("验证9年制义务教育题库扩充结果")
    print("================================================================================")
    
    try:
        # 初始化题目管理器
        question_manager = QuestionManager()
        logger.info("题目管理器初始化成功")
        
        # 获取数据库中题目总数
        conn = question_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM questions')
        total_questions = cursor.fetchone()[0]
        conn.close()
        
        # 计算偏移量，获取最新的10000道题目
        offset = max(0, total_questions - 10000)
        questions = question_manager.get_questions(limit=10000, offset=offset)
        logger.info(f"共获取到 {len(questions)} 道题目")
        
        # 按ID降序排序，确保顺序正确
        questions.sort(key=lambda q: q.id, reverse=True)
        
        # 分析题目覆盖情况
        versions = set()
        grades = set()
        exam_types = set()
        subjects = set()
        levels = set()
        categories = set()
        difficulties = set()
        question_types = set()
        
        # 统计各类题目数量
        version_count = {}
        grade_count = {}
        exam_type_count = {}
        subject_count = {}
        level_count = {}
        category_count = {}
        difficulty_count = {}
        question_type_count = {}
        
        # 分析每道题目
        for question in questions:
            # 解析题目内容，提取版本、年级、考试类型等信息
            content = question.content
            
            # 提取版本、年级、考试类型和学科信息
            # 检查版本
            for version in ["人教版", "北师大版", "苏教版", "沪教版", "鲁教版", "粤教版", "湘教版", "川教版"]:
                if version in content:
                    versions.add(version)
                    version_count[version] = version_count.get(version, 0) + 1
                    break
            
            # 检查年级
            for grade in ["小学一年级", "小学二年级", "小学三年级", "小学四年级", "小学五年级", "小学六年级", "初中一年级", "初中二年级", "初中三年级"]:
                if grade in content:
                    grades.add(grade)
                    grade_count[grade] = grade_count.get(grade, 0) + 1
                    break
            
            # 检查考试类型
            for exam_type in ["中考题", "高考题", "压轴题"]:
                if exam_type in content:
                    exam_types.add(exam_type)
                    exam_type_count[exam_type] = exam_type_count.get(exam_type, 0) + 1
                    break
            
            # 检查学科
            for subject in ["数学", "英语", "语文"]:
                if subject in content:
                    subjects.add(subject)
                    subject_count[subject] = subject_count.get(subject, 0) + 1
                    break
            
            # 统计等级
            levels.add(question.level_id)
            level_count[question.level_id] = level_count.get(question.level_id, 0) + 1
            
            # 统计分类
            if question.category_id is not None:
                categories.add(question.category_id)
                category_count[question.category_id] = category_count.get(question.category_id, 0) + 1
            
            # 统计题目类型
            if question.question_type is not None:
                question_types.add(question.question_type)
                question_type_count[question.question_type] = question_type_count.get(question.question_type, 0) + 1
            
            # 统计难度
            if question.difficulty_score:
                if question.difficulty_score < 1.5:
                    difficulty = "easy"
                elif question.difficulty_score < 2.5:
                    difficulty = "medium"
                else:
                    difficulty = "hard"
                difficulties.add(difficulty)
                difficulty_count[difficulty] = difficulty_count.get(difficulty, 0) + 1
        
        # 过滤并排序结果
        sorted_versions = sorted(versions)
        sorted_grades = sorted(grades)
        sorted_exam_types = sorted(exam_types)
        sorted_subjects = sorted(subjects)
        sorted_levels = sorted([level for level in levels if level is not None])
        sorted_categories = sorted([category for category in categories if category is not None])
        sorted_question_types = sorted([q_type for q_type in question_types if q_type is not None])
        sorted_difficulties = sorted(difficulties)
        
        # 打印验证结果
        print("\n验证结果：")
        print(f"总题目数：{len(questions)}")
        print(f"覆盖版本数：{len(versions)}，具体版本：{sorted_versions}")
        print(f"覆盖年级数：{len(grades)}，具体年级：{sorted_grades}")
        print(f"覆盖考试类型数：{len(exam_types)}，具体类型：{sorted_exam_types}")
        print(f"覆盖学科数：{len(subjects)}，具体学科：{sorted_subjects}")
        print(f"覆盖等级数：{len(levels)}，具体等级：{sorted_levels}")
        print(f"覆盖分类数：{len(categories)}，具体分类：{sorted_categories}")
        print(f"覆盖题目类型数：{len(question_types)}，具体类型：{sorted_question_types}")
        print(f"覆盖难度级别数：{len(difficulties)}，具体级别：{sorted_difficulties}")
        
        # 打印各类题目数量
        print("\n各类题目数量统计：")
        print("版本分布：")
        for version, count in sorted(version_count.items()):
            print(f"  {version}: {count}")
        
        print("\n年级分布：")
        for grade, count in sorted(grade_count.items()):
            print(f"  {grade}: {count}")
        
        print("\n考试类型分布：")
        for exam_type, count in sorted(exam_type_count.items()):
            print(f"  {exam_type}: {count}")
        
        print("\n学科分布：")
        for subject, count in sorted(subject_count.items()):
            print(f"  {subject}: {count}")
        
        print("\n等级分布：")
        for level, count in sorted(level_count.items()):
            print(f"  等级{level}: {count}")
        
        print("\n分类分布：")
        for category, count in sorted(category_count.items()):
            print(f"  分类{category}: {count}")
        
        print("\n题目类型分布：")
        for q_type, count in sorted(question_type_count.items()):
            print(f"  {q_type}: {count}")
        
        print("\n难度分布：")
        for difficulty, count in sorted(difficulty_count.items()):
            print(f"  {difficulty}: {count}")
        
        # 验证是否达到目标
        target_count = 10000
        if len(questions) >= target_count:
            print(f"\n✓ 题目数量达到目标：{len(questions)}/{target_count}")
        else:
            print(f"\n✗ 题目数量未达到目标：{len(questions)}/{target_count}")
        
        # 验证版本覆盖
        expected_versions = ["人教版", "北师大版", "苏教版", "沪教版", "鲁教版", "粤教版", "湘教版", "川教版"]
        if set(expected_versions).issubset(versions):
            print("✓ 所有版本覆盖完成")
        else:
            missing_versions = set(expected_versions) - versions
            print(f"✗ 缺少版本：{missing_versions}")
        
        # 验证年级覆盖
        expected_grades = ["小学一年级", "小学二年级", "小学三年级", "小学四年级", "小学五年级", "小学六年级", "初中一年级", "初中二年级", "初中三年级"]
        if set(expected_grades).issubset(grades):
            print("✓ 所有年级覆盖完成")
        else:
            missing_grades = set(expected_grades) - grades
            print(f"✗ 缺少年级：{missing_grades}")
        
        # 验证考试类型覆盖
        expected_exam_types = ["中考题", "高考题", "压轴题"]
        if set(expected_exam_types).issubset(exam_types):
            print("✓ 所有考试类型覆盖完成")
        else:
            missing_exam_types = set(expected_exam_types) - exam_types
            print(f"✗ 缺少考试类型：{missing_exam_types}")
        
        # 验证学科覆盖
        expected_subjects = ["数学", "英语", "语文"]
        if set(expected_subjects).issubset(subjects):
            print("✓ 所有学科覆盖完成")
        else:
            missing_subjects = set(expected_subjects) - subjects
            print(f"✗ 缺少学科：{missing_subjects}")
        
        # 验证等级覆盖
        expected_levels = {1, 2, 3, 4, 5}
        if expected_levels.issubset(levels):
            print("✓ 所有等级覆盖完成")
        else:
            missing_levels = expected_levels - levels
            print(f"✗ 缺少等级：{missing_levels}")
        
        # 验证分类覆盖
        expected_categories = {1, 2, 3, 4, 5}
        if expected_categories.issubset(categories):
            print("✓ 所有分类覆盖完成")
        else:
            missing_categories = expected_categories - categories
            print(f"✗ 缺少分类：{missing_categories}")
        
        # 验证题目类型覆盖
        expected_question_types = {"single_choice"}
        if expected_question_types.issubset(question_types):
            print("✓ 所有题目类型覆盖完成")
        else:
            missing_question_types = expected_question_types - question_types
            print(f"✗ 缺少题目类型：{missing_question_types}")
        
        # 验证难度覆盖
        expected_difficulties = {"easy", "medium", "hard"}
        if expected_difficulties.issubset(difficulties):
            print("✓ 所有难度覆盖完成")
        else:
            missing_difficulties = expected_difficulties - difficulties
            print(f"✗ 缺少难度：{missing_difficulties}")
        
    except Exception as e:
        logger.error(f"验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n================================================================================")
        print("验证完成！")
        print("================================================================================")

if __name__ == "__main__":
    verify_9year_education()
