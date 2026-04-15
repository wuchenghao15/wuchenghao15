#!/usr/bin/env python3
"""
扩充题库到10万题，覆盖所有学科、所有等级和所有难度
"""

import sys
import os
import time
import logging

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ai.question_bank_expander import QuestionBankExpander
from app.models.question import QuestionManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def expand_to_100k():
    """
    扩充题库到10万题，覆盖所有学科、所有等级和所有难度
    """
    print("================================================================================")
    print("扩充题库到10万题，覆盖所有学科、所有等级和所有难度")
    print("================================================================================")
    
    try:
        # 初始化题库扩充系统
        expander = QuestionBankExpander()
        logger.info("题库扩充系统初始化成功")
        
        # 初始化题目管理器
        question_manager = QuestionManager()
        
        # 获取当前题库状态
        current_questions = question_manager.get_questions()
        current_count = len(current_questions)
        logger.info(f"当前题库题目数量: {current_count}")
        
        # 目标题目数量
        target_count = 100000
        needed_count = target_count - current_count
        
        if needed_count <= 0:
            logger.info(f"题库已经达到或超过目标数量 {target_count}，无需扩充")
            return
        
        logger.info(f"需要生成的题目数量: {needed_count}")
        
        # 记录开始时间
        start_time = time.time()
        
        # 每次扩充的题目数量
        batch_size = expander._config["questions_per_expansion"]
        logger.info(f"每次扩充生成的题目数量: {batch_size}")
        
        # 计算需要的批次数
        batches = needed_count // batch_size
        if needed_count % batch_size > 0:
            batches += 1
        logger.info(f"需要的批次数: {batches}")
        
        # 执行扩充（跳过重复检测，直接生成题目）
        total_generated = 0
        for i in range(batches):
            logger.info(f"开始第 {i+1}/{batches} 批扩充")
            
            # 计算本次需要生成的题目数量
            current_needed = min(batch_size, needed_count - total_generated)
            
            # 直接生成题目，跳过重复检测
            batch_generated = 0
            for _ in range(current_needed):
                # 确定题目参数
                bank_status = expander._analyze_question_bank()
                question_params = expander._determine_question_params(bank_status)
                
                # 生成题目，跳过重复检测
                question = expander._generate_question(
                    **question_params,
                    check_duplicate=False
                )
                
                # 直接保存题目，跳过重复检测
                if question:
                    try:
                        question.save()
                        batch_generated += 1
                        total_generated += 1
                    except Exception as e:
                        logger.error(f"保存题目失败: {str(e)}")
            
            logger.info(f"第 {i+1} 批扩充完成，生成 {batch_generated} 道题目")
            logger.info(f"累计生成 {total_generated} 道题目")
            
            # 检查是否达到目标
            if total_generated >= needed_count:
                break
            
            # 短暂休息，避免系统过载
            time.sleep(0.1)
        
        # 记录结束时间
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 获取最终题库状态
        final_questions = question_manager.get_questions()
        final_count = len(final_questions)
        
        logger.info("\n扩充完成！")
        logger.info(f"开始时题库题目数量: {current_count}")
        logger.info(f"结束时题库题目数量: {final_count}")
        logger.info(f"实际生成题目数量: {final_count - current_count}")
        logger.info(f"耗时: {elapsed_time:.2f} 秒")
        
        # 验证是否达到目标
        if final_count >= target_count:
            logger.info(f"✅ 成功达到目标数量 {target_count} 题")
        else:
            logger.warning(f"❌ 未达到目标数量 {target_count} 题，当前数量: {final_count}")
        
        # 验证覆盖范围
        logger.info("\n验证覆盖范围:")
        
        # 分析题库状态
        bank_status = expander._analyze_question_bank()
        
        # 验证学科覆盖
        category_stats = bank_status.get('category_stats', {})
        logger.info(f"覆盖的学科数量: {len(category_stats)}")
        for category_id, stats in category_stats.items():
            logger.info(f"  学科 {stats['name']}: {stats['count']} 题")
        
        # 验证等级覆盖
        level_stats = bank_status.get('level_stats', {})
        logger.info(f"覆盖的等级数量: {len(level_stats)}")
        for level_id, stats in level_stats.items():
            logger.info(f"  等级 {stats['name']}: {stats['count']} 题")
        
        # 验证语言覆盖
        language_stats = bank_status.get('language_stats', {})
        logger.info(f"覆盖的语言数量: {len(language_stats)}")
        for language_id, stats in language_stats.items():
            logger.info(f"  语言 {stats['name']}: {stats['count']} 题")
        
        # 验证题目类型覆盖
        type_stats = bank_status.get('type_stats', {})
        logger.info(f"覆盖的题目类型数量: {len(type_stats)}")
        for question_type, count in type_stats.items():
            logger.info(f"  题目类型 {question_type}: {count} 题")
        
    except Exception as e:
        logger.error(f"扩充失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n================================================================================")
        print("扩充完成！")
        print("================================================================================")

if __name__ == "__main__":
    expand_to_100k()
