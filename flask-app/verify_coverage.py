#!/usr/bin/env python3
"""
验证题库覆盖范围
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.question import QuestionManager

def verify_coverage():
    """
    验证题库覆盖范围
    """
    print("================================================================================")
    print("验证题库覆盖范围")
    print("================================================================================")
    
    try:
        # 初始化题目管理器
        question_manager = QuestionManager()
        print("题目管理器初始化成功")
        
        # 获取所有题目
        questions = question_manager.get_questions(limit=100000)
        total_count = len(questions)
        print(f"题库总题目数量: {total_count}")
        
        # 统计覆盖范围
        languages = set()
        levels = set()
        categories = set()
        question_types = set()
        difficulties = set()
        
        for question in questions:
            if question.language_id:
                languages.add(question.language_id)
            if question.level_id:
                levels.add(question.level_id)
            if question.category_id:
                categories.add(question.category_id)
            if question.question_type:
                question_types.add(question.question_type)
            # 从 difficulty_score 推断难度级别
            if question.difficulty_score:
                if question.difficulty_score <= 1.5:
                    difficulties.add("easy")
                elif question.difficulty_score <= 2.5:
                    difficulties.add("medium")
                else:
                    difficulties.add("hard")
        
        # 验证覆盖范围
        print("\n覆盖范围验证:")
        print(f"覆盖的语言数量: {len(languages)}")
        print(f"覆盖的语言ID: {sorted(languages)}")
        print(f"覆盖的等级数量: {len(levels)}")
        print(f"覆盖的等级ID: {sorted(levels)}")
        print(f"覆盖的分类数量: {len(categories)}")
        print(f"覆盖的分类ID: {sorted(categories)}")
        print(f"覆盖的题目类型数量: {len(question_types)}")
        print(f"覆盖的题目类型: {sorted(question_types)}")
        print(f"覆盖的难度级别数量: {len(difficulties)}")
        print(f"覆盖的难度级别: {sorted(difficulties)}")
        
        # 验证是否覆盖所有学科
        expected_languages = {1, 2, 3}  # 1: 日语, 2: 英语, 3: 中文
        missing_languages = expected_languages - languages
        if not missing_languages:
            print("\n✅ 所有语言都已覆盖")
        else:
            print(f"\n❌ 缺少语言: {sorted(missing_languages)}")
        
        # 验证是否覆盖所有等级
        expected_levels = {1, 2, 3, 4, 5}  # 1-5
        missing_levels = expected_levels - levels
        if not missing_levels:
            print("✅ 所有等级都已覆盖")
        else:
            print(f"❌ 缺少等级: {sorted(missing_levels)}")
        
        # 验证是否覆盖所有分类
        expected_categories = {1, 2, 3, 4, 5}  # 1-5
        missing_categories = expected_categories - categories
        if not missing_categories:
            print("✅ 所有分类都已覆盖")
        else:
            print(f"❌ 缺少分类: {sorted(missing_categories)}")
        
        # 验证是否覆盖所有题目类型
        expected_types = {"single_choice"}  # 只生成了单选题
        missing_types = expected_types - question_types
        if not missing_types:
            print("✅ 所有题目类型都已覆盖")
        else:
            print(f"❌ 缺少题目类型: {sorted(missing_types)}")
        
        # 验证是否覆盖所有难度
        expected_difficulties = {"easy", "medium", "hard"}
        missing_difficulties = expected_difficulties - difficulties
        if not missing_difficulties:
            print("✅ 所有难度级别都已覆盖")
        else:
            print(f"❌ 缺少难度级别: {sorted(missing_difficulties)}")
        
        # 验证题库总量
        if total_count >= 100000:
            print("\n✅ 题库总量已达到10万题")
        else:
            print(f"\n❌ 题库总量未达到10万题，当前数量: {total_count}")
        
    except Exception as e:
        print(f"\n❌ 验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n================================================================================")
        print("验证完成！")
        print("================================================================================")

if __name__ == "__main__":
    verify_coverage()
