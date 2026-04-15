#!/usr/bin/env python3
"""
测试优化后的题库系统和AI托管功能
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入模块
from app.models.question import question_manager
from app.ai.ai_hosting import ai_hosting_manager

def test_question_model():
    """测试题目模型"""
    print("开始测试题目模型...")
    print("=" * 80)
    
    # 测试创建题目
    print("测试创建题目...")
    question = question_manager.create_question(
        content="测试题目内容",
        answer="测试答案",
        explanation="测试解析",
        category_id=1,
        language_id=1,
        level_id=1,
        question_type="single_choice",
        options=["选项1", "选项2", "选项3", "选项4"],
        tags=["测试", "单选"],
        difficulty_score=5.0,
        discrimination_index=0.5,
        audio_url="http://example.com/audio.mp3",
        image_url="http://example.com/image.jpg",
        video_url="http://example.com/video.mp4",
        time_limit=60,
        score=10
    )
    print(f"创建题目成功，ID: {question.id}")
    
    # 测试获取题目
    print("测试获取题目...")
    retrieved_question = question_manager.get_question(question.id)
    print(f"获取题目成功，ID: {retrieved_question.id}")
    print(f"题目内容: {retrieved_question.content}")
    print(f"题目类型: {retrieved_question.question_type}")
    print(f"题目选项: {retrieved_question.options}")
    print(f"题目标签: {retrieved_question.tags}")
    print(f"难度分数: {retrieved_question.difficulty_score}")
    print(f"区分度: {retrieved_question.discrimination_index}")
    print(f"音频URL: {retrieved_question.audio_url}")
    print(f"图片URL: {retrieved_question.image_url}")
    print(f"视频URL: {retrieved_question.video_url}")
    print(f"时间限制: {retrieved_question.time_limit}")
    print(f"题目分值: {retrieved_question.score}")
    
    # 测试更新题目
    print("测试更新题目...")
    updated_question = question_manager.update_question(
        question.id,
        content="更新后的题目内容",
        difficulty_score=6.0,
        time_limit=90,
        score=15
    )
    print(f"更新题目成功，ID: {updated_question.id}")
    print(f"更新后的题目内容: {updated_question.content}")
    print(f"更新后的难度分数: {updated_question.difficulty_score}")
    print(f"更新后的时间限制: {updated_question.time_limit}")
    print(f"更新后的题目分值: {updated_question.score}")
    
    # 测试获取题目列表
    print("测试获取题目列表...")
    questions = question_manager.get_questions(limit=5)
    print(f"获取到 {len(questions)} 道题目")
    for q in questions[:3]:
        print(f"题目ID: {q.id}, 内容: {q.content[:50]}...")
    
    # 测试评估题目质量
    print("测试评估题目质量...")
    evaluation = question_manager.evaluate_question_quality(question.id)
    print(f"题目质量评估: {evaluation}")
    
    # 测试删除题目
    print("测试删除题目...")
    success = question_manager.delete_question(question.id)
    print(f"删除题目成功: {success}")
    
    print("=" * 80)
    print("题目模型测试完成！")

def test_ai_hosting():
    """测试AI托管功能"""
    print("开始测试AI托管功能...")
    print("=" * 80)
    
    # 初始化AI托管管理器
    print("初始化AI托管管理器...")
    ai_hosting_manager.initialize()
    
    # 测试生成题目
    print("测试生成题目...")
    generated_question = ai_hosting_manager.generate_question(
        language='chinese',
        level='beginner',
        category='数学',
        question_type='single_choice'
    )
    if generated_question:
        print(f"生成题目成功: {generated_question['content'][:50]}...")
    else:
        print("生成题目失败")
    
    # 测试AI托管系统状态
    print("测试AI托管系统状态...")
    status = ai_hosting_manager.get_status()
    print(f"AI托管系统状态: {status['hosting_name']} (ID: {status['hosting_id']})")
    print(f"活跃实例数: {status['status']['active_instances']}")
    print(f"系统健康状态: {status['status']['system_health']}")
    
    # 测试关闭AI托管系统
    print("测试关闭AI托管系统...")
    ai_hosting_manager.shutdown()
    
    print("=" * 80)
    print("AI托管功能测试完成！")

def test_question_generator():
    """测试题目生成功能"""
    print("开始测试题目生成功能...")
    print("=" * 80)
    
    # 测试生成不同类型的题目
    print("测试生成不同类型的题目...")
    question_types = ["single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer"]
    
    for q_type in question_types:
        print(f"生成{q_type}类型题目...")
        questions = question_manager.generate_questions(
            count=2,
            category_id=1,
            language_id=1,
            level_id=1,
            question_type=q_type
        )
        print(f"生成了 {len(questions)} 道{q_type}类型题目")
        for q in questions:
            print(f"  - {q.content[:50]}...")
    
    print("=" * 80)
    print("题目生成功能测试完成！")

def test_question_analysis():
    """测试题目分析功能"""
    print("开始测试题目分析功能...")
    print("=" * 80)
    
    # 创建一个测试题目
    question = question_manager.create_question(
        content="测试题目内容",
        answer="测试答案",
        explanation="测试解析",
        category_id=1,
        language_id=1,
        level_id=1,
        question_type="single_choice",
        options=["选项1", "选项2", "选项3", "选项4"],
        tags=["测试", "单选"],
        difficulty_score=5.0,
        discrimination_index=0.5,
        usage_count=10,
        correct_rate=0.6
    )
    
    # 测试评估题目质量
    print("测试评估题目质量...")
    evaluation = question_manager.evaluate_question_quality(question.id)
    print(f"题目质量评估: {evaluation}")
    
    # 测试优化题目质量
    print("测试优化题目质量...")
    success = question_manager.optimize_question_quality(question.id)
    print(f"优化题目质量成功: {success}")
    
    # 测试批量优化题目质量
    print("测试批量优化题目质量...")
    result = question_manager.batch_optimize_questions(limit=5)
    print(f"批量优化结果: {result}")
    
    # 删除测试题目
    question_manager.delete_question(question.id)
    
    print("=" * 80)
    print("题目分析功能测试完成！")

def test_database_operations():
    """测试数据库操作功能"""
    print("开始测试数据库操作功能...")
    print("=" * 80)
    
    # 测试导入导出功能
    print("测试导入导出功能...")
    
    # 创建一些测试题目
    test_questions = []
    for i in range(3):
        question = question_manager.create_question(
            content=f"测试题目{i+1}",
            answer=f"答案{i+1}",
            explanation=f"解析{i+1}",
            category_id=1,
            language_id=1,
            level_id=1,
            question_type="single_choice",
            options=["选项1", "选项2", "选项3", "选项4"]
        )
        test_questions.append(question)
    
    # 导出题目到JSON
    import json
    export_file = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    success = question_manager.export_questions_to_json(export_file)
    print(f"导出题目到JSON成功: {success}")
    
    # 导入题目从JSON
    with open(export_file, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    
    import_result = question_manager.batch_import_questions(questions_data)
    print(f"导入题目从JSON成功: {import_result}")
    
    # 清理测试文件
    if os.path.exists(export_file):
        os.remove(export_file)
    
    # 清理测试题目
    for question in test_questions:
        question_manager.delete_question(question.id)
    
    print("=" * 80)
    print("数据库操作功能测试完成！")

def main():
    """主测试函数"""
    print("开始测试优化后的题库系统...")
    print("=" * 80)
    
    try:
        # 测试题目模型
        test_question_model()
        
        # 测试题目生成功能
        test_question_generator()
        
        # 测试题目分析功能
        test_question_analysis()
        
        # 测试数据库操作功能
        test_database_operations()
        
        # 测试AI托管功能
        test_ai_hosting()
        
        print("=" * 80)
        print("所有测试完成！")
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
