#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教学内容数据库初始化脚本
初始化教学大纲、备课、教案的数据库，并添加示例数据
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.teaching_content import TeachingContentManager, TeachingSyllabus, TeachingPreparation, TeachingPlan

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_sample_syllabi(manager: TeachingContentManager):
    """初始化示例教学大纲"""
    logger.info("开始初始化示例教学大纲...")
    
    syllabi = [
        # 小学数学
        {
            'grade': '小学1年级',
            'subject': '数学',
            'semester': '第一学期',
            'title': '10以内数的认识',
            'description': '认识10以内的数，掌握数的顺序和大小比较',
            'content': '本单元主要学习10以内数的认识、数的顺序和大小比较，为后续计算打下基础。',
            'objectives': ['认识10以内的数字', '掌握数的顺序', '学会数的大小比较', '培养数感'],
            'knowledge_points': ['数字0-10', '数的顺序', '数的大小比较', '数的组成'],
            'teaching_hours': 8,
            'difficulty_level': 'low',
            'prerequisites': ['具备基本的数数能力'],
            'teaching_methods': ['直观教学法', '游戏教学法', '情境教学法'],
            'assessment_methods': ['课堂提问', '书面作业', '单元测验'],
            'reference_materials': ['人教版小学数学一年级上册', '小学数学课程标准'],
            'status': 'active',
            'created_by': '系统'
        },
        
        # 小学语文
        {
            'grade': '小学1年级',
            'subject': '语文',
            'semester': '第一学期',
            'title': '拼音学习',
            'description': '学习汉语拼音，掌握声母、韵母和整体认读音节',
            'content': '本单元主要学习汉语拼音的基本内容，包括声母、韵母、声调和整体认读音节。',
            'objectives': ['认识声母和韵母', '掌握拼音拼写规则', '学会拼读拼音', '培养语感'],
            'knowledge_points': ['23个声母', '24个韵母', '16个整体认读音节', '拼音拼写规则'],
            'teaching_hours': 16,
            'difficulty_level': 'medium',
            'prerequisites': ['具备基本的听说能力'],
            'teaching_methods': ['跟读练习', '情境教学', '游戏学习'],
            'assessment_methods': ['口头朗读', '书面听写', '拼读测试'],
            'reference_materials': ['人教版小学语文一年级上册', '语文课程标准'],
            'status': 'active',
            'created_by': '系统'
        },
        
        # 初中数学
        {
            'grade': '初中1年级',
            'subject': '数学',
            'semester': '第一学期',
            'title': '有理数',
            'description': '学习有理数的概念、运算和性质',
            'content': '本单元主要学习有理数的概念、数轴、相反数、绝对值以及有理数的加减乘除运算。',
            'objectives': ['理解有理数的概念', '掌握有理数的运算', '学会用数轴表示数', '培养逻辑思维'],
            'knowledge_points': ['有理数概念', '数轴', '相反数', '绝对值', '有理数加减法', '有理数乘除法'],
            'teaching_hours': 12,
            'difficulty_level': 'medium',
            'prerequisites': ['掌握正负数概念'],
            'teaching_methods': ['讲解法', '练习法', '讨论法'],
            'assessment_methods': ['课堂练习', '单元测验', '作业评定'],
            'reference_materials': ['人教版初中数学七年级上册', '初中数学课程标准'],
            'status': 'active',
            'created_by': '系统'
        },
        
        # 初中语文
        {
            'grade': '初中1年级',
            'subject': '语文',
            'semester': '第一学期',
            'title': '现代文阅读',
            'description': '学习现代文阅读方法，理解文章内容和主题',
            'content': '本单元主要学习现代文阅读的基本方法，包括理解词句、把握内容、体会感情。',
            'objectives': ['理解文章主要内容', '体会作者思想感情', '掌握阅读方法', '培养阅读兴趣'],
            'knowledge_points': ['词句理解', '内容概括', '情感体会', '写作手法'],
            'teaching_hours': 10,
            'difficulty_level': 'medium',
            'prerequisites': ['具备基本阅读能力'],
            'teaching_methods': ['朗读法', '讨论法', '提问法'],
            'assessment_methods': ['阅读测试', '读后感', '课堂讨论'],
            'reference_materials': ['人教版初中语文七年级上册', '语文课程标准'],
            'status': 'active',
            'created_by': '系统'
        }
    ]
    
    for syllabus_data in syllabi:
        syllabus_id = manager.create_syllabus(syllabus_data)
        logger.info(f"创建教学大纲: {syllabus_data['title']} (ID: {syllabus_id})")


def init_sample_preparations(manager: TeachingContentManager):
    """初始化示例教学备课"""
    logger.info("开始初始化示例教学备课...")
    
    preparations = [
        {
            'grade': '小学1年级',
            'subject': '数学',
            'lesson_title': '1-5的认识',
            'lesson_number': 1,
            'teaching_hours': 1,
            'teaching_date': datetime.now().strftime('%Y-%m-%d'),
            'objectives': ['认识数字1-5', '会读会写1-5', '能用数表示物体个数'],
            'key_points': ['数字1-5的形状和书写', '数的概念建立'],
            'difficult_points': ['数的概念理解'],
            'teaching_aids': ['数字卡片', '小棒', '多媒体课件'],
            'teaching_process': '''
1. 导入：展示生活中的数字
2. 新授：认识1-5，逐个讲解
3. 练习：数数、写数练习
4. 巩固：小游戏巩固
5. 小结：总结本节课内容
''',
            'time_allocation': [
                {'环节': '导入', '时间': 5},
                {'环节': '新授', '时间': 15},
                {'环节': '练习', '时间': 15},
                {'环节': '小结', '时间': 5}
            ],
            'homework': '完成课本第8页练习题',
            'reflection': '注意引导学生理解数的概念，不要只停留在记忆上。',
            'teaching_resources': ['课本', '练习册', '数字卡片'],
            'status': 'published',
            'created_by': '系统'
        },
        
        {
            'grade': '小学1年级',
            'subject': '语文',
            'lesson_title': '单韵母a o e',
            'lesson_number': 1,
            'teaching_hours': 1,
            'teaching_date': datetime.now().strftime('%Y-%m-%d'),
            'objectives': ['认识单韵母a o e', '学会正确发音', '会书写a o e'],
            'key_points': ['单韵母a o e的发音和书写'],
            'difficult_points': ['正确区分三个单韵母'],
            'teaching_aids': ['拼音卡片', '发音挂图', '多媒体课件'],
            'teaching_process': '''
1. 导入：看图说话，引出a o e
2. 新授：逐个学习a o e的发音和书写
3. 练习：跟读、认读练习
4. 巩固：拼音卡片游戏
5. 小结：回顾本节课内容
''',
            'time_allocation': [
                {'环节': '导入', '时间': 5},
                {'环节': '新授', '时间': 20},
                {'环节': '练习', '时间': 15},
                {'环节': '小结', '时间': 5}
            ],
            'homework': '书写a o e各两行',
            'reflection': '注意强调口型和发音部位，多让学生练习。',
            'teaching_resources': ['课本', '拼音卡片', '挂图'],
            'status': 'published',
            'created_by': '系统'
        }
    ]
    
    for prep_data in preparations:
        prep_id = manager.create_preparation(prep_data)
        logger.info(f"创建教学备课: {prep_data['lesson_title']} (ID: {prep_id})")


def init_sample_plans(manager: TeachingContentManager):
    """初始化示例教案"""
    logger.info("开始初始化示例教案...")
    
    plans = [
        {
            'grade': '小学1年级',
            'subject': '数学',
            'lesson_title': '1-5的认识',
            'lesson_type': '新授课',
            'class_duration': 40,
            'students_count': 45,
            'teaching_objectives': ['正确认读1-5', '规范书写1-5', '用数表示物体个数'],
            'knowledge_skills': ['数字识别', '数字书写', '数量对应'],
            'emotional_attitudes': ['培养学习数学的兴趣', '培养观察能力'],
            'key_points': ['1-5的认读和书写'],
            'difficult_points': ['理解数的概念'],
            'teaching_methods': ['直观教学法', '游戏教学法', '操作法'],
            'teaching_aids': ['数字卡片', '小棒', '多媒体课件'],
            'teaching_process': '''
【导入】（5分钟）
展示生活中的数字场景，如门牌、钟表等，引导学生观察。

【新授】（15分钟）
1. 认识数字1：展示1个苹果，说“1”
2. 依次认识2、3、4、5，用小棒演示
3. 教授书写方法，边讲解边示范
4. 学生练习书写

【练习】（15分钟）
1. 数数练习：数教室里的物品
2. 写数练习：在练习本上写
3. 数字卡片游戏：听数举牌

【小结】（5分钟）
回顾本节课学习了什么，鼓励学生。
''',
            'board_design': '''
1-5的认识
数字：1 2 3 4 5
书写：一一演示写法
练习：学生板演
''',
            'activity_design': [
                {'名称': '听数举卡片', '目的': '巩固数字识别', '时间': 5},
                {'名称': '数数比赛', '目的': '练习数数', '时间': 5}
            ],
            'question_design': [
                {'问题': '这是几？', '类型': '基础', '对象': '全体'},
                {'问题': '教室里有几个窗户？', '类型': '应用', '对象': '小组'},
                {'问题': '5可以表示什么？', '类型': '拓展', '对象': '个别'}
            ],
            'assessment_design': '课堂提问和练习完成情况',
            'homework_design': '1. 书写1-5各两行  2. 数一数家里的物品',
            'after_class_reflection': '大部分学生能够正确认读和书写，个别学生还需要加强练习。下次课可以增加更多互动环节。',
            'teaching_notes': '注意个别辅导，多鼓励学生。',
            'attachments': ['教学课件.ppt', '数字卡片.pdf'],
            'status': 'published',
            'created_by': '系统'
        },
        
        {
            'grade': '小学1年级',
            'subject': '语文',
            'lesson_title': '单韵母a o e',
            'lesson_type': '新授课',
            'class_duration': 40,
            'students_count': 45,
            'teaching_objectives': ['认识a o e', '正确发音', '规范书写'],
            'knowledge_skills': ['拼音识别', '拼音书写', '发音方法'],
            'emotional_attitudes': ['培养学习拼音的兴趣', '养成良好书写习惯'],
            'key_points': ['a o e的发音和书写'],
            'difficult_points': ['准确掌握发音部位'],
            'teaching_methods': ['示范法', '模仿法', '游戏法'],
            'teaching_aids': ['拼音卡片', '发音挂图', '多媒体课件'],
            'teaching_process': '''
【导入】（5分钟）
出示插图，引导学生观察，引出a o e。

【新授】（20分钟）
1. 学习a：讲解口型，示范发音，学生模仿
2. 学习o：讲解口型，示范发音，学生模仿
3. 学习e：讲解口型，示范发音，学生模仿
4. 教授书写：逐个讲解笔顺
5. 学生练习书写

【练习】（10分钟）
1. 开火车读拼音
2. 拼音卡片认读
3. 书写练习

【小结】（5分钟）
回顾本节课内容，鼓励学生。
''',
            'board_design': '''
单韵母a o e
a：嘴巴张大 a a a
o：嘴巴圆圆 o o o
e：嘴巴扁扁 e e e
书写：一一演示
''',
            'activity_design': [
                {'名称': '开火车读拼音', '目的': '练习发音', '时间': 5},
                {'名称': '拼音接龙', '目的': '巩固认读', '时间': 5}
            ],
            'question_design': [
                {'问题': '这是什么？', '类型': '基础', '对象': '全体'},
                {'问题': '怎么读？', '类型': '应用', '对象': '个别'},
                {'问题': '你发现口型有什么不同？', '类型': '拓展', '对象': '小组'}
            ],
            'assessment_design': '课堂提问和书写检查',
            'homework_design': '1. 书写a o e各两行  2. 读给家长听',
            'after_class_reflection': '学生发音基本正确，但个别学生还需要纠正。书写需要加强练习。',
            'teaching_notes': '多让学生听标准发音，多练习，及时纠正错误发音。',
            'attachments': ['教学课件.ppt', '拼音卡片.pdf'],
            'status': 'published',
            'created_by': '系统'
        }
    ]
    
    for plan_data in plans:
        plan_id = manager.create_plan(plan_data)
        logger.info(f"创建教案: {plan_data['lesson_title']} (ID: {plan_id})")


def main():
    """主函数"""
    print("=" * 60)
    print("MTSCOS 教学内容数据库初始化")
    print("=" * 60)
    
    try:
        # 创建管理器
        manager = TeachingContentManager()
        
        # 初始化示例数据
        init_sample_syllabi(manager)
        init_sample_preparations(manager)
        init_sample_plans(manager)
        
        # 显示统计
        stats = manager.get_statistics()
        print("\n" + "=" * 60)
        print("初始化完成！")
        print("=" * 60)
        print(f"教学大纲数量: {stats['syllabus_count']}")
        print(f"教学备课数量: {stats['preparation_count']}")
        print(f"教案数量: {stats['plan_count']}")
        print(f"已发布备课: {stats['published_preparation_count']}")
        print(f"已发布教案: {stats['published_plan_count']}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

