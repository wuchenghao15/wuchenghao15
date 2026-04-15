#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量生成题目脚本，用于丰富题库题量和题型
"""

import sys
import os
import time
from app.ai.question_generator import ai_question_generator
from app.models.question import Question

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def batch_generate_questions():
    """批量生成题目"""
    print("=" * 60)
    print("批量生成题目脚本")
    print("=" * 60)
    
    try:
        # 配置生成参数
        configs = [
            # 日语题目配置
            {
                'language': 'japanese',
                'levels': ['beginner', 'intermediate', 'advanced', 'expert'],
                'categories': ['日常对话', '商务日语', '学术日语', '日本文化', '往年真题', '词汇题', '语法题', '听力理解'],
                'question_types': ['multiple_choice', 'fill_in_blank', 'true_false', 'short_answer', 'essay'],
                'count_per_config': 2  # 每种配置生成的题目数量
            },
            # 英语题目配置
            {
                'language': 'english',
                'levels': ['beginner', 'intermediate', 'advanced', 'expert'],
                'categories': ['日常对话', '商务英语', '学术写作', '英语听力', '雅思托福', '词汇题', '语法题', '阅读理解'],
                'question_types': ['multiple_choice', 'fill_in_blank', 'true_false', 'short_answer', 'essay'],
                'count_per_config': 2  # 每种配置生成的题目数量
            }
        ]
        
        total_generated = 0
        start_time = time.time()
        
        # 遍历配置，生成题目
        for config in configs:
            language = config['language']
            print(f"\n开始生成 {language} 题目...")
            
            for level in config['levels']:
                for category in config['categories']:
                    for question_type in config['question_types']:
                        print(f"  生成: {language} - {level} - {category} - {question_type}")
                        
                        # 生成题目
                        try:
                            generated = 0
                            for _ in range(config['count_per_config']):
                                # 生成单道题目
                                result = ai_question_generator.generate_question(
                                    language=language,
                                    level=level,
                                    category=category,
                                    question_type=question_type
                                )
                                
                                if result:
                                    generated += 1
                                    total_generated += 1
                                    
                                    # 保存到数据库
                                    if not Question.is_duplicate_question(result.content, language, category):
                                        question_obj = Question(
                                            language=result.language,
                                            level=result.level,
                                            category=result.category,
                                            content=result.content,
                                            options=result.options,
                                            correct_answer=result.correct_answer,
                                            explanation=result.explanation,
                                            source='ai_generated',
                                            question_type=result.question_type
                                        )
                                        question_obj.save()
                                        print(f"    ✅ 生成题目: {result.content[:30]}...")
                                    else:
                                        print(f"    ⚠️  题目重复，已跳过")
                            
                            print(f"    共生成 {generated} 道题目")
                        except Exception as e:
                            print(f"    ❌ 生成失败: {str(e)}")
                            continue
        
        end_time = time.time()
        print(f"\n" + "=" * 60)
        print(f"✅ 批量生成完成！")
        print(f"总共生成: {total_generated} 道题目")
        print(f"耗时: {end_time - start_time:.2f} 秒")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 批量生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    batch_generate_questions()
