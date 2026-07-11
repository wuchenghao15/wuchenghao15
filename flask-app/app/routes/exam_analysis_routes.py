"""考试分析API路由 - MTSCOS AI项目"""

from flask import Blueprint, request, session
from app.services.exam_data_analysis_service import get_exam_data_analysis_service
from app.utils.permission import require_login, require_admin
from app.utils.response import (
    success_response, bad_request, server_error
)
from app.exceptions import (
    ValidationException,
    BusinessException
)

exam_analysis_api = Blueprint('exam_analysis_api', __name__)
analysis_service = get_exam_data_analysis_service()


@exam_analysis_api.route('/api/exam_analysis/score_distribution', methods=['GET'])
@require_login
def get_score_distribution():
    """获取成绩分布分析"""
    try:
        exam_id = request.args.get('exam_id')
        
        if not exam_id:
            raise ValidationException(
                message='考试ID不能为空',
                field_errors={'exam_id': '考试ID不能为空'}
            )
        
        distribution = analysis_service.analyze_score_distribution(exam_id)
        result = {
            'score_ranges': distribution.score_ranges,
            'mean': distribution.mean,
            'median': distribution.median,
            'std_dev': distribution.std_dev,
            'min_score': distribution.min_score,
            'max_score': distribution.max_score,
            'mode': distribution.mode,
            'percentile_25': distribution.percentile_25,
            'percentile_75': distribution.percentile_75
        }
        
        return success_response(result, message='成绩分布分析成功')
    
    except ValidationException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@exam_analysis_api.route('/api/exam_analysis/question_difficulty', methods=['GET'])
@require_login
def get_question_difficulty():
    """获取题目难度分析"""
    try:
        exam_id = request.args.get('exam_id')
        
        if not exam_id:
            raise ValidationException(
                message='考试ID不能为空',
                field_errors={'exam_id': '考试ID不能为空'}
            )
        
        analyses = analysis_service.analyze_question_difficulty(exam_id)
        result = []
        for analysis in analyses:
            result.append({
                'question_id': analysis.question_id,
                'difficulty_level': analysis.difficulty_level,
                'correct_rate': analysis.correct_rate,
                'avg_time_spent': analysis.avg_time_spent,
                'discrimination_index': analysis.discrimination_index,
                'difficulty_index': analysis.difficulty_index,
                'analysis_result': analysis.analysis_result
            })
        
        return success_response(result, message='题目难度分析成功')
    
    except ValidationException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@exam_analysis_api.route('/api/exam_analysis/knowledge_mastery', methods=['GET'])
@require_login
def get_knowledge_mastery():
    """获取知识点掌握度分析"""
    try:
        exam_id = request.args.get('exam_id')
        user_id = request.args.get('user_id')
        
        if not exam_id:
            raise ValidationException(
                message='考试ID不能为空',
                field_errors={'exam_id': '考试ID不能为空'}
            )
        
        mastery_list = analysis_service.analyze_knowledge_mastery(exam_id, user_id)
        result = []
        for mastery in mastery_list:
            result.append({
                'knowledge_point': mastery.knowledge_point,
                'total_questions': mastery.total_questions,
                'correct_count': mastery.correct_count,
                'mastery_rate': mastery.mastery_rate,
                'avg_time': mastery.avg_time,
                'difficulty_avg': mastery.difficulty_avg,
                'mastery_level': mastery.mastery_level
            })
        
        return success_response(result, message='知识点掌握度分析成功')
    
    except ValidationException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@exam_analysis_api.route('/api/exam_analysis/report', methods=['GET'])
@require_login
def get_exam_report():
    """获取考试分析报告"""
    try:
        exam_id = request.args.get('exam_id')
        
        if not exam_id:
            raise ValidationException(
                message='考试ID不能为空',
                field_errors={'exam_id': '考试ID不能为空'}
            )
        
        report = analysis_service.generate_exam_analysis_report(exam_id)
        
        result = {
            'exam_id': report.exam_id,
            'total_participants': report.total_participants,
            'score_distribution': {
                'score_ranges': report.score_distribution.score_ranges,
                'mean': report.score_distribution.mean,
                'median': report.score_distribution.median,
                'std_dev': report.score_distribution.std_dev,
                'min_score': report.score_distribution.min_score,
                'max_score': report.score_distribution.max_score,
                'mode': report.score_distribution.mode,
                'percentile_25': report.score_distribution.percentile_25,
                'percentile_75': report.score_distribution.percentile_75
            },
            'question_analyses': [
                {
                    'question_id': qa.question_id,
                    'difficulty_level': qa.difficulty_level,
                    'correct_rate': qa.correct_rate,
                    'avg_time_spent': qa.avg_time_spent,
                    'discrimination_index': qa.discrimination_index,
                    'difficulty_index': qa.difficulty_index,
                    'analysis_result': qa.analysis_result
                } for qa in report.question_analyses
            ],
            'knowledge_mastery': [
                {
                    'knowledge_point': km.knowledge_point,
                    'total_questions': km.total_questions,
                    'correct_count': km.correct_count,
                    'mastery_rate': km.mastery_rate,
                    'avg_time': km.avg_time,
                    'difficulty_avg': km.difficulty_avg,
                    'mastery_level': km.mastery_level
                } for km in report.knowledge_mastery
            ],
            'overall_statistics': report.overall_statistics,
            'recommendations': report.recommendations,
            'generated_at': report.generated_at.isoformat()
        }
        
        return success_response(result, message='考试分析报告生成成功')
    
    except ValidationException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@exam_analysis_api.route('/api/exam_analysis/user_history', methods=['GET'])
@require_login
def get_user_exam_history():
    """获取用户考试历史分析"""
    try:
        user_id = request.args.get('user_id') or session.get('user_id')
        limit = int(request.args.get('limit', 20))
        
        if not user_id:
            raise ValidationException(
                message='用户ID不能为空',
                field_errors={'user_id': '用户ID不能为空'}
            )
        
        history = analysis_service.analyze_user_exam_history(user_id, limit)
        return success_response(history, message='用户考试历史分析成功')
    
    except ValidationException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@exam_analysis_api.route('/api/exam_analysis/comparison', methods=['POST'])
@require_login
def get_comparison_report():
    """获取用户对比报告"""
    try:
        data = request.json
        exam_id = data.get('exam_id')
        user_ids = data.get('user_ids')
        
        if not exam_id:
            raise ValidationException(
                message='考试ID不能为空',
                field_errors={'exam_id': '考试ID不能为空'}
            )
        
        if not user_ids or not isinstance(user_ids, list):
            raise ValidationException(
                message='用户ID列表不能为空',
                field_errors={'user_ids': '用户ID列表不能为空'}
            )
        
        comparison = analysis_service.generate_comparison_report(exam_id, user_ids)
        return success_response(comparison, message='用户对比报告生成成功')
    
    except ValidationException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))


@exam_analysis_api.route('/api/exam_analysis/cached', methods=['GET'])
@require_login
def get_cached_analysis():
    """获取缓存的分析结果"""
    try:
        exam_id = request.args.get('exam_id')
        analysis_type = request.args.get('type', 'full_report')
        
        if not exam_id:
            raise ValidationException(
                message='考试ID不能为空',
                field_errors={'exam_id': '考试ID不能为空'}
            )
        
        cached = analysis_service.get_cached_analysis(exam_id, analysis_type)
        
        if cached:
            return success_response(cached, message='获取缓存分析成功')
        else:
            return success_response(None, message='暂无缓存数据')
    
    except ValidationException as e:
        return bad_request(e.message, e.error_type, e.suggestion, e.details)
    except Exception as e:
        return server_error(str(e))