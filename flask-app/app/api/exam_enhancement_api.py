# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
考试系统增强API模块
提供智能组卷、防作弊检测、数据分析等高级功能的API接口
"""

from flask import Blueprint, jsonify, request, session
import logging
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)

exam_enhancement_api = Blueprint('exam_enhancement_api', __name__, url_prefix='/api/exam/enhanced')


# ==================== 智能组卷API ====================

@exam_enhancement_api.route('/paper/generate', methods=['POST'])
def generate_intelligent_paper():
    """
    智能组卷接口
    
    根据难度分布、知识点覆盖率、题型比例自动生成试卷
    
    请求参数:
    - total_questions: 题目总数 (可选, 默认20)
    - total_points: 总分 (可选, 默认100)
    - type_ratio: 题型比例配置 (可选)
    - difficulty_distribution: 难度分布配置 (可选)
    - required_knowledge_points: 必须覆盖的知识点列表 (可选)
    - min_knowledge_coverage: 最小知识点覆盖率 (可选, 默认80)
    - shuffle_questions: 是否打乱题目顺序 (可选, 默认True)
    - shuffle_options: 是否打乱选项顺序 (可选, 默认True)
    - exam_id: 考试ID (可选, 用于指定题目池)
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        
        from app.services.intelligent_paper_generator import get_intelligent_paper_generator
        from app.utils.db import db_manager
        
        generator = get_intelligent_paper_generator(db_manager)
        
        # 构建配置
        from app.services.intelligent_paper_generator import PaperGenerationConfig
        config = PaperGenerationConfig(
            total_questions=data.get('total_questions', 20),
            total_points=data.get('total_points', 100.0),
            type_ratio=data.get('type_ratio', {
                'single_choice': 0.5,
                'multiple_choice': 0.2,
                'true_false': 0.1,
                'fill_blank': 0.1,
                'short_answer': 0.1
            }),
            difficulty_distribution=data.get('difficulty_distribution', {
                1: 0.15, 2: 0.25, 3: 0.35, 4: 0.20, 5: 0.05
            }),
            required_knowledge_points=data.get('required_knowledge_points', []),
            min_knowledge_coverage=data.get('min_knowledge_coverage', 80.0),
            shuffle_questions=data.get('shuffle_questions', True),
            shuffle_options=data.get('shuffle_options', True)
        )
        
        exam_id = data.get('exam_id')
        
        # 生成试卷
        paper = generator.generate_paper(config, exam_id)
        
        if paper.get('paper_id'):
            logger.info(f"智能组卷成功: {paper['paper_id']}")
            return jsonify({
                'success': True,
                'data': paper,
                'message': '试卷生成成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': paper.get('error', '试卷生成失败')
            }), 500
            
    except Exception as e:
        logger.error(f"智能组卷失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/paper/generate_from_template', methods=['POST'])
def generate_paper_from_template():
    """
    从模板生成试卷接口
    
    请求参数:
    - template_id: 模板ID
    - exam_id: 考试ID (可选)
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        template_id = data.get('template_id')
        
        if not template_id:
            return jsonify({'success': False, 'error': '缺少模板ID'}), 400
        
        from app.utils.db import db_manager
        
        # 获取模板
        template = db_manager.fetch_one(
            "SELECT * FROM exam_templates WHERE id = ?", (template_id,)
        )
        
        if not template:
            return jsonify({'success': False, 'error': '模板不存在'}), 404
        
        template_data = template if isinstance(template, dict) else {
            'question_count': template[5],
            'total_points': 100.0,
            'type_ratio': json.loads(template[6]) if template[6] else {},
            'difficulty_distribution': json.loads(template[7]) if template[7] else {},
            'shuffle_questions': True,
            'shuffle_options': True
        }
        
        from app.services.intelligent_paper_generator import get_intelligent_paper_generator
        generator = get_intelligent_paper_generator(db_manager)
        
        exam_id = data.get('exam_id')
        paper = generator.generate_paper_from_template(template_data, exam_id)
        
        return jsonify({
            'success': True,
            'data': paper,
            'message': '从模板生成试卷成功'
        })
        
    except Exception as e:
        logger.error(f"从模板生成试卷失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/paper/validate', methods=['POST'])
def validate_paper_quality():
    """
    验证试卷质量接口
    
    请求参数:
    - paper: 试卷数据
    """
    try:
        data = request.get_json()
        paper = data.get('paper')
        
        if not paper:
            return jsonify({'success': False, 'error': '缺少试卷数据'}), 400
        
        from app.services.intelligent_paper_generator import get_intelligent_paper_generator
        generator = get_intelligent_paper_generator()
        
        validation = generator.validate_paper_quality(paper)
        
        return jsonify({
            'success': True,
            'data': validation,
            'message': '试卷质量验证完成'
        })
        
    except Exception as e:
        logger.error(f"试卷质量验证失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/paper/optimize', methods=['POST'])
def optimize_paper():
    """
    优化试卷难度接口
    
    请求参数:
    - paper: 试卷数据
    - target_difficulty: 目标平均难度 (可选, 默认3.0)
    """
    try:
        data = request.get_json()
        paper = data.get('paper')
        target_difficulty = data.get('target_difficulty', 3.0)
        
        if not paper:
            return jsonify({'success': False, 'error': '缺少试卷数据'}), 400
        
        from app.services.intelligent_paper_generator import get_intelligent_paper_generator
        generator = get_intelligent_paper_generator()
        
        optimized_paper = generator.optimize_paper_difficulty(paper, target_difficulty)
        
        return jsonify({
            'success': True,
            'data': optimized_paper,
            'message': '试卷难度优化完成'
        })
        
    except Exception as e:
        logger.error(f"试卷难度优化失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 防作弊检测API ====================

@exam_enhancement_api.route('/anti-cheating/behavior/record', methods=['POST'])
def record_behavior_event():
    """
    记录答题行为事件接口
    
    请求参数:
    - session_id: 考试会话ID
    - exam_id: 考试ID
    - event_type: 事件类型
    - question_id: 相关题目ID (可选)
    - details: 事件详情 (可选)
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        
        session_id = data.get('session_id')
        exam_id = data.get('exam_id')
        event_type = data.get('event_type')
        question_id = data.get('question_id')
        details = data.get('details')
        
        if not session_id or not exam_id or not event_type:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        from app.services.anti_cheating_service import get_anti_cheating_service
        service = get_anti_cheating_service()
        
        result = service.record_behavior_event(
            session_id, user_id, exam_id, event_type, question_id, details
        )
        
        return jsonify({
            'success': result.get('success', False),
            'data': result,
            'message': '行为事件记录成功' if result.get('success') else result.get('error', '记录失败')
        })
        
    except Exception as e:
        logger.error(f"记录行为事件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/anti-cheating/screen-switch/detect', methods=['POST'])
def detect_screen_switch():
    """
    切屏检测接口
    
    请求参数:
    - session_id: 会话ID
    - switch_type: 切屏类型 (可选, 默认tab_switch)
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        session_id = data.get('session_id')
        switch_type = data.get('switch_type', 'tab_switch')
        
        if not session_id:
            return jsonify({'success': False, 'error': '缺少会话ID'}), 400
        
        from app.services.anti_cheating_service import get_anti_cheating_service
        service = get_anti_cheating_service()
        
        result = service.detect_screen_switch(session_id, user_id, switch_type)
        
        return jsonify({
            'success': result.get('success', False),
            'data': result,
            'message': '切屏检测完成'
        })
        
    except Exception as e:
        logger.error(f"切屏检测失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/anti-cheating/time-anomaly/detect', methods=['POST'])
def detect_time_anomaly():
    """
    时间异常检测接口
    
    请求参数:
    - session_id: 会话ID
    - anomaly_type: 异常类型
    - expected_value: 期望值
    - actual_value: 实际值
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        
        session_id = data.get('session_id')
        anomaly_type = data.get('anomaly_type')
        expected_value = data.get('expected_value')
        actual_value = data.get('actual_value')
        
        if not session_id or not anomaly_type:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        from app.services.anti_cheating_service import get_anti_cheating_service
        service = get_anti_cheating_service()
        
        result = service.detect_time_anomaly(
            session_id, user_id, anomaly_type, expected_value, actual_value
        )
        
        return jsonify({
            'success': result.get('success', False),
            'data': result,
            'message': '时间异常检测完成'
        })
        
    except Exception as e:
        logger.error(f"时间异常检测失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/anti-cheating/pattern/analyze', methods=['POST'])
def analyze_answer_pattern():
    """
    答题模式分析接口
    
    请求参数:
    - session_id: 会话ID
    - answers: 答题数据
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        session_id = data.get('session_id')
        answers = data.get('answers')
        
        if not session_id or not answers:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        from app.services.anti_cheating_service import get_anti_cheating_service
        service = get_anti_cheating_service()
        
        result = service.analyze_answer_pattern(session_id, user_id, answers)
        
        return jsonify({
            'success': result.get('success', False),
            'data': result,
            'message': '答题模式分析完成'
        })
        
    except Exception as e:
        logger.error(f"答题模式分析失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/anti-cheating/comprehensive/detect', methods=['POST'])
def perform_comprehensive_detection():
    """
    综合作弊检测接口
    
    请求参数:
    - session_id: 会话ID
    - exam_id: 考试ID
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        session_id = data.get('session_id')
        exam_id = data.get('exam_id')
        
        if not session_id or not exam_id:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        from app.services.anti_cheating_service import get_anti_cheating_service
        service = get_anti_cheating_service()
        
        result = service.perform_comprehensive_detection(session_id, user_id, exam_id)
        
        return jsonify({
            'success': True,
            'data': {
                'is_cheating': result.is_cheating,
                'cheating_type': result.cheating_type,
                'confidence': result.confidence,
                'risk_level': result.risk_level,
                'evidence': result.evidence,
                'recommendation': result.recommendation
            },
            'message': '综合作弊检测完成'
        })
        
    except Exception as e:
        logger.error(f"综合作弊检测失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/anti-cheating/report/<session_id>', methods=['GET'])
def get_cheating_report(session_id):
    """
    获取作弊报告接口
    
    Args:
        session_id: 会话ID
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        from app.services.anti_cheating_service import get_anti_cheating_service
        service = get_anti_cheating_service()
        
        report = service.get_session_cheating_report(session_id)
        
        return jsonify({
            'success': True,
            'data': report,
            'message': '作弊报告获取成功'
        })
        
    except Exception as e:
        logger.error(f"获取作弊报告失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/anti-cheating/history/<user_id>', methods=['GET'])
def get_user_cheating_history(user_id):
    """
    获取用户作弊历史接口
    
    Args:
        user_id: 用户ID
    """
    try:
        current_user_id = session.get('user_id')
        if not current_user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        # 只能查看自己的历史，或者管理员可以查看所有
        role = session.get('role', '')
        if current_user_id != user_id and role not in ['admin', 'teacher']:
            return jsonify({'success': False, 'error': '无权限查看'}), 403
        
        from app.services.anti_cheating_service import get_anti_cheating_service
        service = get_anti_cheating_service()
        
        limit = request.args.get('limit', 20, type=int)
        history = service.get_user_cheating_history(user_id, limit)
        
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history),
            'message': '作弊历史获取成功'
        })
        
    except Exception as e:
        logger.error(f"获取作弊历史失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 数据分析API ====================

@exam_enhancement_api.route('/analysis/score-distribution/<exam_id>', methods=['GET'])
def analyze_score_distribution(exam_id):
    """
    成绩分布分析接口
    
    Args:
        exam_id: 考试ID
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        # 检查是否有缓存
        from app.services.exam_data_analysis_service import get_exam_data_analysis_service
        service = get_exam_data_analysis_service()
        
        cached = service.get_cached_analysis(exam_id, 'score_distribution')
        if cached:
            return jsonify({
                'success': True,
                'data': cached['data'],
                'cached': True,
                'generated_at': cached['generated_at']
            })
        
        distribution = service.analyze_score_distribution(exam_id)
        
        return jsonify({
            'success': True,
            'data': {
                'score_ranges': distribution.score_ranges,
                'mean': distribution.mean,
                'median': distribution.median,
                'std_dev': distribution.std_dev,
                'min_score': distribution.min_score,
                'max_score': distribution.max_score,
                'mode': distribution.mode,
                'percentile_25': distribution.percentile_25,
                'percentile_75': distribution.percentile_75
            },
            'cached': False,
            'message': '成绩分布分析完成'
        })
        
    except Exception as e:
        logger.error(f"成绩分布分析失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/analysis/question-difficulty/<exam_id>', methods=['GET'])
def analyze_question_difficulty(exam_id):
    """
    题目难度分析接口
    
    Args:
        exam_id: 考试ID
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        from app.services.exam_data_analysis_service import get_exam_data_analysis_service
        service = get_exam_data_analysis_service()
        
        cached = service.get_cached_analysis(exam_id, 'question_difficulty')
        if cached:
            return jsonify({
                'success': True,
                'data': cached['data'],
                'cached': True,
                'generated_at': cached['generated_at']
            })
        
        analyses = service.analyze_question_difficulty(exam_id)
        
        data = [{
            'question_id': qa.question_id,
            'difficulty_level': qa.difficulty_level,
            'correct_rate': qa.correct_rate,
            'avg_time_spent': qa.avg_time_spent,
            'discrimination_index': qa.discrimination_index,
            'difficulty_index': qa.difficulty_index,
            'analysis_result': qa.analysis_result
        } for qa in analyses]
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'cached': False,
            'message': '题目难度分析完成'
        })
        
    except Exception as e:
        logger.error(f"题目难度分析失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/analysis/knowledge-mastery/<exam_id>', methods=['GET'])
def analyze_knowledge_mastery(exam_id):
    """
    知识点掌握度分析接口
    
    Args:
        exam_id: 考试ID
    
    查询参数:
    - user_id: 用户ID (可选, 如果不提供则分析整体)
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        target_user_id = request.args.get('user_id')
        
        from app.services.exam_data_analysis_service import get_exam_data_analysis_service
        service = get_exam_data_analysis_service()
        
        mastery_list = service.analyze_knowledge_mastery(exam_id, target_user_id)
        
        data = [{
            'knowledge_point': km.knowledge_point,
            'total_questions': km.total_questions,
            'correct_count': km.correct_count,
            'mastery_rate': km.mastery_rate,
            'avg_time': km.avg_time,
            'difficulty_avg': km.difficulty_avg,
            'mastery_level': km.mastery_level
        } for km in mastery_list]
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'message': '知识点掌握度分析完成'
        })
        
    except Exception as e:
        logger.error(f"知识点掌握度分析失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/analysis/report/<exam_id>', methods=['GET'])
def generate_analysis_report(exam_id):
    """
    生成考试分析报告接口
    
    Args:
        exam_id: 考试ID
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        # 验证权限（教师或管理员才能查看完整报告）
        role = session.get('role', '')
        if role not in ['admin', 'teacher']:
            return jsonify({'success': False, 'error': '无权限查看完整报告'}), 403
        
        from app.services.exam_data_analysis_service import get_exam_data_analysis_service
        service = get_exam_data_analysis_service()
        
        # 检查缓存
        cached = service.get_cached_analysis(exam_id, 'full_report')
        if cached:
            return jsonify({
                'success': True,
                'data': cached['data'],
                'cached': True,
                'generated_at': cached['generated_at']
            })
        
        report = service.generate_exam_analysis_report(exam_id)
        
        return jsonify({
            'success': True,
            'data': {
                'exam_id': report.exam_id,
                'total_participants': report.total_participants,
                'score_distribution': {
                    'score_ranges': report.score_distribution.score_ranges,
                    'mean': report.score_distribution.mean,
                    'median': report.score_distribution.median,
                    'std_dev': report.score_distribution.std_dev
                },
                'question_analyses': [{
                    'question_id': qa.question_id,
                    'correct_rate': qa.correct_rate,
                    'analysis_result': qa.analysis_result
                } for qa in report.question_analyses],
                'knowledge_mastery': [{
                    'knowledge_point': km.knowledge_point,
                    'mastery_rate': km.mastery_rate,
                    'mastery_level': km.mastery_level
                } for km in report.knowledge_mastery],
                'overall_statistics': report.overall_statistics,
                'recommendations': report.recommendations,
                'generated_at': report.generated_at.isoformat()
            },
            'cached': False,
            'message': '考试分析报告生成完成'
        })
        
    except Exception as e:
        logger.error(f"生成考试分析报告失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/analysis/user-history/<user_id>', methods=['GET'])
def analyze_user_exam_history(user_id):
    """
    分析用户考试历史接口
    
    Args:
        user_id: 用户ID
    
    查询参数:
    - limit: 返回记录数量限制 (可选, 默认20)
    """
    try:
        current_user_id = session.get('user_id')
        if not current_user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        # 只能查看自己的历史，或者管理员可以查看所有
        role = session.get('role', '')
        if current_user_id != user_id and role not in ['admin', 'teacher']:
            return jsonify({'success': False, 'error': '无权限查看'}), 403
        
        from app.services.exam_data_analysis_service import get_exam_data_analysis_service
        service = get_exam_data_analysis_service()
        
        limit = request.args.get('limit', 20, type=int)
        history = service.analyze_user_exam_history(user_id, limit)
        
        return jsonify({
            'success': True,
            'data': history,
            'message': '用户考试历史分析完成'
        })
        
    except Exception as e:
        logger.error(f"分析用户考试历史失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/analysis/comparison', methods=['POST'])
def generate_comparison_report():
    """
    生成用户对比报告接口
    
    请求参数:
    - exam_id: 考试ID
    - user_ids: 用户ID列表
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        # 验证权限（教师或管理员才能查看对比报告）
        role = session.get('role', '')
        if role not in ['admin', 'teacher']:
            return jsonify({'success': False, 'error': '无权限查看对比报告'}), 403
        
        data = request.get_json()
        exam_id = data.get('exam_id')
        user_ids = data.get('user_ids', [])
        
        if not exam_id or not user_ids:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        from app.services.exam_data_analysis_service import get_exam_data_analysis_service
        service = get_exam_data_analysis_service()
        
        comparison = service.generate_comparison_report(exam_id, user_ids)
        
        return jsonify({
            'success': True,
            'data': comparison,
            'message': '用户对比报告生成完成'
        })
        
    except Exception as e:
        logger.error(f"生成对比报告失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 综合增强功能API ====================

@exam_enhancement_api.route('/template/create', methods=['POST'])
def create_exam_template():
    """
    创建考试模板接口
    
    请求参数:
    - name: 模板名称
    - description: 模板描述 (可选)
    - language: 语言 (可选)
    - level: 等级 (可选)
    - duration: 考试时长 (可选)
    - question_count: 题目数量
    - type_ratio: 题型比例
    - difficulty_distribution: 难度分布
    - knowledge_points: 知识点列表 (可选)
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name') or not data.get('question_count'):
            return jsonify({'success': False, 'error': '缺少必填字段'}), 400
        
        from app.utils.db import db_manager
        from uuid import uuid4
        from datetime import datetime, timezone
        
        template_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        db_manager.execute('''
            INSERT INTO exam_templates 
            (id, name, description, language, level, duration, question_count, 
             question_types, difficulty_distribution, tags, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            template_id,
            data['name'],
            data.get('description', ''),
            data.get('language', 'zh'),
            data.get('level', 'intermediate'),
            data.get('duration', 60),
            data['question_count'],
            json.dumps(data.get('type_ratio', {})),
            json.dumps(data.get('difficulty_distribution', {})),
            json.dumps(data.get('knowledge_points', [])),
            user_id,
            now,
            now
        ))
        
        return jsonify({
            'success': True,
            'template_id': template_id,
            'message': '考试模板创建成功'
        }), 201
        
    except Exception as e:
        logger.error(f"创建考试模板失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/template/list', methods=['GET'])
def list_exam_templates():
    """
    获取考试模板列表接口
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        from app.utils.db import db_manager
        
        templates = db_manager.fetch_all(
            "SELECT id, name, description, language, level, duration, question_count, created_at FROM exam_templates ORDER BY created_at DESC"
        )
        
        template_list = []
        for t in templates:
            if isinstance(t, dict):
                template_list.append({
                    'id': t['id'],
                    'name': t['name'],
                    'description': t.get('description', ''),
                    'language': t.get('language', 'zh'),
                    'level': t.get('level', 'intermediate'),
                    'duration': t.get('duration', 60),
                    'question_count': t.get('question_count', 20),
                    'created_at': t.get('created_at')
                })
            else:
                template_list.append({
                    'id': t[0],
                    'name': t[1],
                    'description': t[2] if t[2] else '',
                    'language': t[3] if t[3] else 'zh',
                    'level': t[4] if t[4] else 'intermediate',
                    'duration': t[5] if t[5] else 60,
                    'question_count': t[6] if t[6] else 20,
                    'created_at': t[7]
                })
        
        return jsonify({
            'success': True,
            'data': template_list,
            'count': len(template_list)
        })
        
    except Exception as e:
        logger.error(f"获取考试模板列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/enhanced/start', methods=['POST'])
def start_enhanced_exam():
    """
    启动增强考试会话接口
    
    集成防作弊检测和智能组卷功能
    
    请求参数:
    - exam_id: 考试ID
    - use_intelligent_paper: 是否使用智能组卷 (可选, 默认False)
    - paper_config: 试卷配置 (可选, 当use_intelligent_paper为True时使用)
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        exam_id = data.get('exam_id')
        
        if not exam_id:
            return jsonify({'success': False, 'error': '缺少考试ID'}), 400
        
        # 创建考试会话
        from app.services.exam_proctor_service import get_exam_proctor_service
        proctor_service = get_exam_proctor_service()
        
        session_id = proctor_service.create_exam_session(user_id, exam_id)
        
        # 初始化防作弊检测
        from app.services.anti_cheating_service import get_anti_cheating_service
        anti_cheating = get_anti_cheating_service()
        anti_cheating.record_behavior_event(
            session_id, user_id, exam_id, 'exam_start',
            details={'session_created': True}
        )
        
        # 如果使用智能组卷，生成试卷
        paper = None
        if data.get('use_intelligent_paper', False):
            from app.services.intelligent_paper_generator import get_intelligent_paper_generator, PaperGenerationConfig
            from app.utils.db import db_manager
            
            generator = get_intelligent_paper_generator(db_manager)
            
            config_data = data.get('paper_config', {})
            config = PaperGenerationConfig(
                total_questions=config_data.get('total_questions', 20),
                total_points=config_data.get('total_points', 100.0),
                shuffle_questions=config_data.get('shuffle_questions', True),
                shuffle_options=config_data.get('shuffle_options', True)
            )
            
            paper = generator.generate_paper(config, exam_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'exam_id': exam_id,
            'paper': paper,
            'message': '增强考试会话启动成功'
        })
        
    except Exception as e:
        logger.error(f"启动增强考试会话失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@exam_enhancement_api.route('/enhanced/end', methods=['POST'])
def end_enhanced_exam():
    """
    结束增强考试会话接口
    
    集成作弊检测分析和数据分析
    
    请求参数:
    - session_id: 会话ID
    - exam_id: 考试ID
    - answers: 答题数据 (可选)
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        
        data = request.get_json()
        session_id = data.get('session_id')
        exam_id = data.get('exam_id')
        answers = data.get('answers')
        
        if not session_id or not exam_id:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        # 执行综合作弊检测
        from app.services.anti_cheating_service import get_anti_cheating_service
        anti_cheating = get_anti_cheating_service()
        
        # 如果有答题数据，先分析答题模式
        if answers:
            anti_cheating.analyze_answer_pattern(session_id, user_id, answers)
        
        # 执行作弊检测
        detection_result = anti_cheating.perform_comprehensive_detection(session_id, user_id, exam_id)
        
        # 结束会话
        from app.services.exam_proctor_service import get_exam_proctor_service
        proctor_service = get_exam_proctor_service()
        proctor_service.end_session(session_id)
        
        return jsonify({
            'success': True,
            'detection_result': {
                'is_cheating': detection_result.is_cheating,
                'risk_level': detection_result.risk_level,
                'confidence': detection_result.confidence,
                'recommendation': detection_result.recommendation
            },
            'message': '增强考试会话结束成功'
        })
        
    except Exception as e:
        logger.error(f"结束增强考试会话失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# API文档
@exam_enhancement_api.route('/docs', methods=['GET'])
def get_api_docs():
    """获取API文档"""
    docs = {
        'api_name': '考试系统增强API',
        'version': 'v1.0',
        'modules': {
            'intelligent_paper': {
                'description': '智能组卷模块',
                'endpoints': [
                    {
                        'path': '/paper/generate',
                        'method': 'POST',
                        'description': '智能组卷'
                    },
                    {
                        'path': '/paper/generate_from_template',
                        'method': 'POST',
                        'description': '从模板生成试卷'
                    },
                    {
                        'path': '/paper/validate',
                        'method': 'POST',
                        'description': '验证试卷质量'
                    },
                    {
                        'path': '/paper/optimize',
                        'method': 'POST',
                        'description': '优化试卷难度'
                    }
                ]
            },
            'anti_cheating': {
                'description': '防作弊检测模块',
                'endpoints': [
                    {
                        'path': '/anti-cheating/behavior/record',
                        'method': 'POST',
                        'description': '记录答题行为事件'
                    },
                    {
                        'path': '/anti-cheating/screen-switch/detect',
                        'method': 'POST',
                        'description': '切屏检测'
                    },
                    {
                        'path': '/anti-cheating/time-anomaly/detect',
                        'method': 'POST',
                        'description': '时间异常检测'
                    },
                    {
                        'path': '/anti-cheating/pattern/analyze',
                        'method': 'POST',
                        'description': '答题模式分析'
                    },
                    {
                        'path': '/anti-cheating/comprehensive/detect',
                        'method': 'POST',
                        'description': '综合作弊检测'
                    },
                    {
                        'path': '/anti-cheating/report/<session_id>',
                        'method': 'GET',
                        'description': '获取作弊报告'
                    },
                    {
                        'path': '/anti-cheating/history/<user_id>',
                        'method': 'GET',
                        'description': '获取用户作弊历史'
                    }
                ]
            },
            'data_analysis': {
                'description': '数据分析模块',
                'endpoints': [
                    {
                        'path': '/analysis/score-distribution/<exam_id>',
                        'method': 'GET',
                        'description': '成绩分布分析'
                    },
                    {
                        'path': '/analysis/question-difficulty/<exam_id>',
                        'method': 'GET',
                        'description': '题目难度分析'
                    },
                    {
                        'path': '/analysis/knowledge-mastery/<exam_id>',
                        'method': 'GET',
                        'description': '知识点掌握度分析'
                    },
                    {
                        'path': '/analysis/report/<exam_id>',
                        'method': 'GET',
                        'description': '生成考试分析报告'
                    },
                    {
                        'path': '/analysis/user-history/<user_id>',
                        'method': 'GET',
                        'description': '分析用户考试历史'
                    },
                    {
                        'path': '/analysis/comparison',
                        'method': 'POST',
                        'description': '生成用户对比报告'
                    }
                ]
            }
        }
    }
    
    return jsonify({
        'success': True,
        'data': docs
    })