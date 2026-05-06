#!/usr/bin/env python3
"""
简单扩充题库到10万题

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

def expand_to_100k_simple():
    简单扩充题库到10万题
    print("================================================================================")
    print("================================================================================")

    try:
        # 初始化题库扩充系统
        expander = QuestionBankExpander()
        logger.info("题库扩充系统初始化成功")

        # 初始化题目管理器
        question_manager = QuestionManager()
        logger.info("题目管理器初始化成功")

        # 目标题目数量
        target_count = 100000

        # 记录开始时间
        start_time = time.time()

        # 生成题目
        generated_count = 0
        batch_size = 1000  # 每批生成1000道题目

        while generated_count < target_count:
            batch_start = time.time()
            batch_generated = 0

            for _ in range(batch_size):
                # 生成随机题目参数
                language_id = 1 + (generated_count % 3)  # 1: 日语, 2: 英语, 3: 中文
                level_id = 1 + (generated_count % 5)  # 1-5
                category_id = 1 + (generated_count % 5)  # 1-5
                question_type = "single_choice"  # 只生成单选题，确保成功
                difficulty = ["easy", "medium", "hard"][generated_count % 3]

                # 生成题目，跳过重复检测
                question = expander._generate_question(
                    language_id=language_id,
                    level_id=level_id,
                    category_id=category_id,
                    question_type=question_type,
                    difficulty=difficulty,
                    check_duplicate=False
                )

                # 保存题目
                if question:
                    try:
                        # 使用 QuestionManager 创建题目
                        question_manager.create_question(
                            content=question.content,
                            explanation=question.explanation,
                            category_id=question.category_id,
                            language_id=question.language_id,
                            level_id=question.level_id,
                            question_type=question.question_type,
                            options=question.options,
                            tags=question.tags,
                            difficulty_score=question.difficulty_score,
                            discrimination_index=question.discrimination_index,
                            usage_count=question.usage_count,
                            correct_rate=question.correct_rate,
                            audio_url=question.audio_url
                        )
                        batch_generated += 1
                        generated_count += 1

                        # 每生成1000道题目，打印一次进度
                            logger.info(f"已生成 {generated_count}/{target_count} 道题目")
                    except Exception as e:
                        logger.error(f"保存题目失败: {str(e)}")

            batch_end = time.time()
            batch_time = batch_end - batch_start
            logger.info(f"第 {generated_count // batch_size} 批生成完成，耗时 {batch_time:.2f} 秒，生成 {batch_generated} 道题目")

            # 短暂休息，避免系统过载
            time.sleep(0.1)

        # 记录结束时间
        end_time = time.time()
        elapsed_time = end_time - start_time

        logger.info("\n扩充完成！")
        logger.info(f"成功生成 {generated_count} 道题目")
        logger.info(f"耗时: {elapsed_time:.2f} 秒")
        logger.info(f"平均生成速度: {generated_count / elapsed_time:.2f} 题/秒")

    except Exception as e:
        logger.error(f"扩充失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n================================================================================")
        print("================================================================================")

if __name__ == "__main__":
    expand_to_100k_simple()

"""