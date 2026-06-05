# -*- coding: utf-8 -*-
"""
学生学习优化API
提供个性化的学习路径优化和考试策略指导
"""

from flask import Blueprint, jsonify, request
from app.ai.student_learning_optimizer import student_learning_optimizer
from app.utils.logging import logger

student_learning_api = Blueprint('student_learning_api', __name__)


@student_learning_api.route('/student/analyze', methods=['POST'])
def analyze_student():
    """全面分析学生"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({
                'success': False,
                'error': '缺少用户ID'
            }), 400
        
        user_id = data['user_id']
        exam_history = data.get('exam_history', [])
        
        # 全面分析
        analysis = student_learning_optimizer.analyze_student(user_id, exam_history)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    
    except Exception as e:
        logger.error(f"学生分析失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@student_learning_api.route('/student/performance', methods=['POST'])
def get_performance():
    """获取学习表现分析"""
    try:
        data = request.get_json()
        
        if not data or 'exam_history' not in data:
            return jsonify({
                'success': False,
                'error': '缺少考试历史'
            }), 400
        
        exam_history = data['exam_history']
        
        # 分析表现
        analyzer = student_learning_optimizer.performance_analyzer
        performance = analyzer.analyze_performance(exam_history)
        
        return jsonify({
            'success': True,
            'performance': performance
        })
    
    except Exception as e:
        logger.error(f"获取学习表现失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@student_learning_api.route('/student/gaps', methods=['POST'])
def identify_gaps():
    """识别知识漏洞"""
    try:
        data = request.get_json()
        
        if not data or 'question_analysis' not in data:
            return jsonify({
                'success': False,
                'error': '缺少题目分析数据'
            }), 400
        
        question_analysis = data['question_analysis']
        
        # 识别漏洞
        identifier = student_learning_optimizer.gap_identifier
        gaps = identifier.identify_gaps(question_analysis)
        
        return jsonify({
            'success': True,
            'gaps': gaps
        })
    
    except Exception as e:
        logger.error(f"识别知识漏洞失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@student_learning_api.route('/student/learning-path', methods=['POST'])
def generate_learning_path():
    """生成学习路径"""
    try:
        data = request.get_json()
        
        if not data or 'gaps' not in data or 'performance' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必要数据'
            }), 400
        
        gaps = data['gaps']
        performance = data['performance']
        
        # 生成学习路径
        optimizer = student_learning_optimizer.path_optimizer
        learning_path = optimizer.generate_learning_path(gaps, performance)
        
        return jsonify({
            'success': True,
            'learning_path': learning_path
        })
    
    except Exception as e:
        logger.error(f"生成学习路径失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@student_learning_api.route('/student/exam-strategy', methods=['POST'])
def generate_exam_strategy():
    """生成考试策略"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data or 'exam_config' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必要数据'
            }), 400
        
        user_id = data['user_id']
        exam_config = data['exam_config']
        
        # 生成考试策略
        strategy = student_learning_optimizer.generate_exam_strategy(user_id, exam_config)
        
        return jsonify({
            'success': True,
            'strategy': strategy
        })
    
    except Exception as e:
        logger.error(f"生成考试策略失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@student_learning_api.route('/student/progress', methods=['GET'])
def get_progress():
    """获取进步追踪"""
    try:
        user_id = request.args.get('user_id', type=int)
        days = request.args.get('days', default=30, type=int)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': '缺少用户ID'
            }), 400
        
        # 获取追踪数据
        progress = student_learning_optimizer.get_progress_tracking(user_id, days)
        
        return jsonify({
            'success': True,
            'progress': progress
        })
    
    except Exception as e:
        logger.error(f"获取进步追踪失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@student_learning_api.route('/student/recommendations')
def get_recommendations():
    """获取个性化建议"""
    recommendations = {
        'study_tips': [
            {
                'title': '番茄工作法',
                'description': '学习25分钟，休息5分钟，保持高效专注',
                'applicable': '所有学生'
            },
            {
                'title': '主动回忆',
                'description': '学习后合上书本，尝试回忆关键内容',
                'applicable': '记忆类科目'
            },
            {
                'title': '间隔复习',
                'description': '按照艾宾浩斯遗忘曲线安排复习',
                'applicable': '所有科目'
            }
        ],
        'exam_tips': [
            {
                'title': '先易后难',
                'description': '先完成有把握的题目，建立信心',
                'applicable': '所有考试'
            },
            {
                'title': '时间管理',
                'description': '每题设置最大时间限制，避免在某题停留过久',
                'applicable': '限时考试'
            },
            {
                'title': '仔细审题',
                'description': '特别是选择题，注意否定词和程度词',
                'applicable': '选择题'
            }
        ],
        'mental_health': [
            {
                'title': '保持睡眠',
                'description': '考试前保证7-8小时睡眠',
                'priority': 'high'
            },
            {
                'title': '适度运动',
                'description': '每天30分钟有氧运动，缓解压力',
                'priority': 'medium'
            },
            {
                'title': '积极暗示',
                'description': '给自己正面的心理暗示，增强信心',
                'priority': 'medium'
            }
        ]
    }
    
    return jsonify({
        'success': True,
        'recommendations': recommendations
    })


@student_learning_api.route('/student/capabilities')
def get_capabilities():
    """获取AI学生优化能力"""
    capabilities = {
        'name': 'AI学生学习优化员工',
        'version': '1.0.0',
        'modules': [
            {
                'name': '表现分析器',
                'description': '分析学生的学习表现和趋势',
                'capabilities': [
                    '计算平均分、最高分、最低分',
                    '分析成绩趋势（提升/下降/稳定）',
                    '识别优势和劣势题型',
                    '分析时间效率'
                ]
            },
            {
                'name': '漏洞识别器',
                'description': '识别学生的知识漏洞',
                'capabilities': [
                    '按知识点分析正确率',
                    '计算漏洞严重程度',
                    '按优先级排序漏洞',
                    '分类统计漏洞分布'
                ]
            },
            {
                'name': '路径优化器',
                'description': '生成个性化学习路径',
                'capabilities': [
                    '优先级排序学习任务',
                    '生成每日学习计划',
                    '制定每周学习目标',
                    '推荐学习资源'
                ]
            },
            {
                'name': '考试策略顾问',
                'description': '提供考试策略指导',
                'capabilities': [
                    '优化答题顺序',
                    '合理分配时间',
                    '提供考试技巧',
                    '压力管理建议'
                ]
            }
        ],
        'features': [
            '个性化学习路径规划',
            '知识漏洞精准识别',
            '学习进度实时追踪',
            '考试策略智能优化',
            '压力管理与心理调适',
            '资源推荐与学习指导'
        ]
    }
    
    return jsonify({
        'success': True,
        'capabilities': capabilities
    })
