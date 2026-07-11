"""智能学习助手API路由 - MTSCOS AI项目"""

from flask import Blueprint, request, session, jsonify
from app.services.ai_learning_assistant import get_ai_learning_assistant
from app.utils.api_response import APIResponse
from app.utils.permission import require_login
from app.exceptions import (
    ValidationException,
    ResourceNotFoundException,
    BusinessException
)

learning_assistant_api = Blueprint('learning_assistant_api', __name__)


@learning_assistant_api.route('/api/learning_assistant/recommendations', methods=['GET'])
@require_login
def get_recommendations():
    """获取学习推荐"""
    user_id = session.get('user_id')
    
    assistant = get_ai_learning_assistant()
    recommendations = assistant.get_recommendations(user_id)
    
    return APIResponse.success(recommendations)


@learning_assistant_api.route('/api/learning_assistant/generate_recommendations', methods=['POST'])
@require_login
def generate_recommendations():
    """生成新的学习推荐"""
    user_id = session.get('user_id')
    
    assistant = get_ai_learning_assistant()
    recommendations = assistant.generate_recommendations(user_id)
    
    return APIResponse.success(recommendations)


@learning_assistant_api.route('/api/learning_assistant/recommendations/<string:rec_id>/view', methods=['POST'])
@require_login
def mark_recommendation_viewed(rec_id):
    """标记推荐已查看"""
    from app.services.ai_learning_assistant import LearningRecommendation
    
    success = LearningRecommendation.mark_viewed(rec_id)
    
    if success:
        return APIResponse.success(message='已标记为已查看')
    return APIResponse.error(message='操作失败')


@learning_assistant_api.route('/api/learning_assistant/recommendations/<string:rec_id>/complete', methods=['POST'])
@require_login
def mark_recommendation_completed(rec_id):
    """标记推荐已完成"""
    from app.services.ai_learning_assistant import LearningRecommendation
    
    success = LearningRecommendation.mark_completed(rec_id)
    
    if success:
        return APIResponse.success(message='已标记为已完成')
    return APIResponse.error(message='操作失败')


@learning_assistant_api.route('/api/learning_assistant/homework/analyze', methods=['POST'])
@require_login
def analyze_homework():
    """分析作业答案"""
    user_id = session.get('user_id')
    
    data = request.get_json()
    homework_id = data.get('homework_id')
    question_id = data.get('question_id')
    question_text = data.get('question_text')
    user_answer = data.get('user_answer', '')
    
    if not homework_id or not question_id or not question_text:
        return APIResponse.validation_error('缺少必要参数')
    
    assistant = get_ai_learning_assistant()
    
    try:
        result = assistant.analyze_homework(user_id, homework_id, question_id, question_text, user_answer)
        return APIResponse.success(result)
    except BusinessException as e:
        return APIResponse.error(message=e.message)
    except Exception as e:
        return APIResponse.server_error(str(e))


@learning_assistant_api.route('/api/learning_assistant/homework/list', methods=['GET'])
@require_login
def get_homework_assistance():
    """获取作业辅导列表"""
    user_id = session.get('user_id')
    homework_id = request.args.get('homework_id')
    
    from app.services.ai_learning_assistant import HomeworkAssistant
    
    assistance_list = HomeworkAssistant.get_user_homework_assistance(user_id, homework_id)
    
    return APIResponse.success(assistance_list)


@learning_assistant_api.route('/api/learning_assistant/homework/<string:assist_id>', methods=['GET'])
@require_login
def get_assistance_detail(assist_id):
    """获取作业辅导详情"""
    from app.services.ai_learning_assistant import HomeworkAssistant
    
    assistance = HomeworkAssistant.get_assistance(assist_id)
    
    if not assistance:
        return APIResponse.not_found('作业辅导记录不存在')
    
    return APIResponse.success(assistance)


@learning_assistant_api.route('/api/learning_assistant/report', methods=['GET'])
@require_login
def get_learning_report():
    """获取学习报告"""
    user_id = session.get('user_id')
    period = request.args.get('period', 'week')
    
    assistant = get_ai_learning_assistant()
    
    try:
        report = assistant.generate_learning_report(user_id, period)
        return APIResponse.success(report)
    except Exception as e:
        return APIResponse.server_error(str(e))


@learning_assistant_api.route('/api/learning_assistant/analytics', methods=['GET'])
@require_login
def get_learning_analytics():
    """获取学习分析数据"""
    user_id = session.get('user_id')
    
    assistant = get_ai_learning_assistant()
    analytics = assistant.get_learning_analytics(user_id)
    
    return APIResponse.success(analytics)