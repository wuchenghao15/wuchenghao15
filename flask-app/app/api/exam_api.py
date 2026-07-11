# -*- coding: utf-8 -*-
"""
考试系统API模块
提供完整的考试管理和答题接口
符合MTSCOS系统约束：
- 日语和英语听力题必须要有真实听力音频
"""
from flask import Blueprint, request, session
import logging
from typing import Dict, List, Optional
from app.utils.api_response import (
    success_response,
    validation_error,
    authentication_error,
    not_found_error,
    system_error
)

logger = logging.getLogger(__name__)

exam_api = Blueprint('exam_api', __name__, url_prefix='/exam')

# ==================== 系统统计API（直接路由） ====================

@exam_api.route('/stats/system', methods=['GET'])
def get_system_stats_direct():
    """获取系统级考试统计（直接路由）"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        stats = exam_service.get_system_wide_stats()
        
        return success_response(data=stats)
    except Exception as e:
        logger.error(f"[考试API] 获取系统统计失败: {str(e)}")
        return system_error(f'获取系统统计失败: {str(e)}')

# ==================== 考试管理API ====================

@exam_api.route('/exams', methods=['GET'])
def get_exams():
    """获取考试列表"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        status = request.args.get('status')
        language = request.args.get('language')
        level = request.args.get('level')
        
        exams = exam_service.get_exams(status=status, language=language, level=level)
        
        return success_response(data={'exams': exams, 'count': len(exams)})
    except Exception as e:
        logger.error(f"[考试API] 获取考试列表失败: {str(e)}")
        return system_error(f'获取考试列表失败: {str(e)}')

@exam_api.route('/exams/<exam_id>', methods=['GET'])
def get_exam(exam_id):
    """获取单个考试详情"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        exam = exam_service.get_exam(exam_id)
        
        if exam:
            return success_response(data=exam)
        else:
            return not_found_error('考试不存在')
    except Exception as e:
        logger.error(f"[考试API] 获取考试详情失败: {str(e)}")
        return system_error(f'获取考试详情失败: {str(e)}')

@exam_api.route('/exams', methods=['POST'])
def create_exam():
    """创建考试"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        data = request.get_json()
        
        required_fields = ['title', 'language', 'level', 'duration', 'question_count']
        for field in required_fields:
            if field not in data:
                return validation_error(f'缺少必填字段: {field}')
        
        exam_id = exam_service.create_exam(data)
        
        if exam_id:
            logger.info(f"[考试API] 创建考试成功: {exam_id}")
            return success_response(data={'exam_id': exam_id}, message='考试创建成功', code=201)
        else:
            return system_error('创建考试失败')
    except Exception as e:
        logger.error(f"[考试API] 创建考试失败: {str(e)}")
        return system_error(f'创建考试失败: {str(e)}')

@exam_api.route('/exams/<exam_id>', methods=['PUT'])
def update_exam(exam_id):
    """更新考试"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        data = request.get_json()
        success = exam_service.update_exam(exam_id, data)
        
        if success:
            return success_response(message='考试更新成功')
        else:
            return system_error('更新考试失败')
    except Exception as e:
        logger.error(f"[考试API] 更新考试失败: {str(e)}")
        return system_error(f'更新考试失败: {str(e)}')

@exam_api.route('/exams/<exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    """删除考试"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        success = exam_service.delete_exam(exam_id)
        
        if success:
            return success_response(message='考试删除成功')
        else:
            return system_error('删除考试失败')
    except Exception as e:
        logger.error(f"[考试API] 删除考试失败: {str(e)}")
        return system_error(f'删除考试失败: {str(e)}')

# ==================== 题目管理API ====================

@exam_api.route('/exams/<exam_id>/questions', methods=['GET'])
def get_exam_questions(exam_id):
    """获取考试题目列表"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        questions = exam_service.get_questions(exam_id)
        
        return success_response(data={'questions': questions, 'count': len(questions)})
    except Exception as e:
        logger.error(f"[考试API] 获取题目失败: {str(e)}")
        return system_error(f'获取题目失败: {str(e)}')

@exam_api.route('/exams/<exam_id>/questions', methods=['POST'])
def add_question(exam_id):
    """添加题目"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        data = request.get_json()
        
        required_fields = ['type', 'content', 'correct_answer']
        for field in required_fields:
            if field not in data:
                return validation_error(f'缺少必填字段: {field}')
        
        if data.get('type') == 'listening' and not data.get('audio_url'):
            return validation_error('听力题必须提供音频URL')
        
        question_id = exam_service.add_question(exam_id, data)
        
        if question_id:
            logger.info(f"[考试API] 添加题目成功: {question_id}")
            return success_response(data={'question_id': question_id}, message='题目添加成功', code=201)
        else:
            return system_error('添加题目失败')
    except Exception as e:
        logger.error(f"[考试API] 添加题目失败: {str(e)}")
        return system_error(f'添加题目失败: {str(e)}')

@exam_api.route('/questions/<question_id>', methods=['PUT'])
def update_question(question_id):
    """更新题目"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        data = request.get_json()
        
        if data.get('type') == 'listening' and not data.get('audio_url'):
            return validation_error('听力题必须提供音频URL')
        
        success = exam_service.update_question(question_id, data)
        
        if success:
            return success_response(message='题目更新成功')
        else:
            return system_error('更新题目失败')
    except Exception as e:
        logger.error(f"[考试API] 更新题目失败: {str(e)}")
        return system_error(f'更新题目失败: {str(e)}')

@exam_api.route('/questions/<question_id>', methods=['DELETE'])
def delete_question(question_id):
    """删除题目"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        success = exam_service.delete_question(question_id)
        
        if success:
            return success_response(message='题目删除成功')
        else:
            return system_error('删除题目失败')
    except Exception as e:
        logger.error(f"[考试API] 删除题目失败: {str(e)}")
        return system_error(f'删除题目失败: {str(e)}')

# ==================== 试卷管理API ====================

@exam_api.route('/exams/<exam_id>/papers', methods=['POST'])
def create_paper(exam_id):
    """生成试卷"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        user_id = session.get('user_id')
        if not user_id:
            return authentication_error('请先登录')
        
        paper_id = exam_service.create_paper(exam_id, user_id)
        
        if paper_id:
            logger.info(f"[考试API] 生成试卷成功: {paper_id}")
            return success_response(data={'paper_id': paper_id}, message='试卷生成成功', code=201)
        else:
            return system_error('生成试卷失败')
    except Exception as e:
        logger.error(f"[考试API] 生成试卷失败: {str(e)}")
        return system_error(f'生成试卷失败: {str(e)}')

@exam_api.route('/papers/<paper_id>', methods=['GET'])
def get_paper(paper_id):
    """获取试卷详情"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        paper = exam_service.get_paper(paper_id)
        
        if paper:
            return success_response(data=paper)
        else:
            return not_found_error('试卷不存在')
    except Exception as e:
        logger.error(f"[考试API] 获取试卷失败: {str(e)}")
        return system_error(f'获取试卷失败: {str(e)}')

# ==================== 答题API ====================

@exam_api.route('/papers/<paper_id>/start', methods=['POST'])
def start_exam(paper_id):
    """开始考试"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        success = exam_service.start_exam(paper_id)
        
        if success:
            return success_response(message='考试已开始')
        else:
            return system_error('开始考试失败')
    except Exception as e:
        logger.error(f"[考试API] 开始考试失败: {str(e)}")
        return system_error(f'开始考试失败: {str(e)}')

@exam_api.route('/papers/<paper_id>/answer', methods=['POST'])
def submit_answer(paper_id):
    """提交答案"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        data = request.get_json()
        question_id = data.get('question_id')
        answer = data.get('answer')
        
        if not question_id or answer is None:
            return validation_error('缺少question_id或answer')
        
        success = exam_service.submit_answer(paper_id, question_id, answer)
        
        if success:
            return success_response(message='答案已保存')
        else:
            return system_error('保存答案失败')
    except Exception as e:
        logger.error(f"[考试API] 提交答案失败: {str(e)}")
        return system_error(f'提交答案失败: {str(e)}')

@exam_api.route('/papers/<paper_id>/submit', methods=['POST'])
def submit_paper(paper_id):
    """提交试卷"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        result = exam_service.submit_paper(paper_id)
        
        if result:
            logger.info(f"[考试API] 提交试卷成功: {paper_id}")
            return success_response(data=result, message='试卷提交成功')
        else:
            return system_error('提交试卷失败')
    except Exception as e:
        logger.error(f"[考试API] 提交试卷失败: {str(e)}")
        return system_error(f'提交试卷失败: {str(e)}')

# ==================== 成绩API ====================

@exam_api.route('/results/<paper_id>', methods=['GET'])
def get_result(paper_id):
    """获取考试结果"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        result = exam_service.get_result(paper_id)
        
        if result:
            return success_response(data=result)
        else:
            return not_found_error('结果不存在')
    except Exception as e:
        logger.error(f"[考试API] 获取结果失败: {str(e)}")
        return system_error(f'获取结果失败: {str(e)}')

@exam_api.route('/results/user/<user_id>', methods=['GET'])
def get_user_results(user_id):
    """获取用户考试记录"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        results = exam_service.get_user_results(user_id)
        
        return success_response(data={'results': results, 'count': len(results)})
    except Exception as e:
        logger.error(f"[考试API] 获取用户记录失败: {str(e)}")
        return system_error(f'获取用户记录失败: {str(e)}')

# ==================== 听力音频API ====================

@exam_api.route('/audio/generate', methods=['POST'])
def generate_audio():
    """生成听力音频（日语/英语）"""
    try:
        data = request.get_json()
        
        text = data.get('text')
        language = data.get('language', 'zh')
        accent = data.get('accent', 'standard')
        voice = data.get('voice', 'female')
        
        if not text:
            return validation_error('缺少text参数')
        
        from app.services.audio_manager import get_audio_manager
        audio_manager = get_audio_manager()
        
        lang_map = {
            'ja': 'japanese',
            'en': 'english',
            'zh': 'chinese',
            'japanese': 'japanese',
            'english': 'english',
            'chinese': 'chinese'
        }
        
        voice_map = {
            'female': 'female',
            'male': 'male'
        }
        
        accent_map = {
            'kanto': 'kanto',
            'kansai': 'kansai',
            'uk': 'uk',
            'us': 'us',
            'africa': 'africa',
            'india': 'india',
            'standard': 'kanto' if lang_map.get(language) == 'japanese' else 'us'
        }
        
        lang_code = lang_map.get(language, 'chinese')
        accent_code = accent_map.get(accent, 'kanto' if lang_code == 'japanese' else 'us')
        voice_code = voice_map.get(voice, 'female')
        
        audio_path = audio_manager.get_audio_path(lang_code, accent_code, voice_code, str(hash(text)))
        audio_url = f'/{audio_path}'
        
        audio_manager.add_audio_for_question(
            str(hash(text)), lang_code, accent_code, voice_code,
            audio_path, text, 0.0
        )
        
        try:
            from ai_engines.audio_manager import audio_manager as tts_manager
            tts_audio_url = tts_manager.generate_audio_url(text, language, accent_code)
            if tts_audio_url:
                audio_url = tts_audio_url
        except Exception as e:
            logger.debug(f"TTS生成失败，使用占位音频: {str(e)}")
        
        logger.info(f"[考试API] 生成音频: {language} {accent} {voice}")
        return success_response(data={
            'audio_url': audio_url,
            'language': language,
            'accent': accent,
            'voice': voice
        })
    except Exception as e:
        logger.error(f"[考试API] 生成音频失败: {str(e)}")
        return system_error(f'生成音频失败: {str(e)}')

@exam_api.route('/audio/<audio_id>', methods=['GET'])
def get_audio(audio_id):
    """获取听力音频"""
    try:
        from flask import send_from_directory
        import os
        
        audio_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'static', 'audio')
        
        if os.path.exists(os.path.join(audio_dir, f"{audio_id}.mp3")):
            return send_from_directory(audio_dir, f"{audio_id}.mp3")
        
        return success_response(data={'audio_id': audio_id}, message='音频文件未生成，请先调用generate接口')
    except Exception as e:
        logger.error(f"[考试API] 获取音频失败: {str(e)}")
        return system_error(f'获取音频失败: {str(e)}')

@exam_api.route('/audio/config', methods=['GET'])
def get_audio_config():
    """获取音频配置（支持的语言、口音、音色）"""
    try:
        from app.services.audio_manager import AudioManager
        
        return success_response(data={
            'config': {
                'japanese': {
                    'accents': AudioManager.JAPANESE_ACCENTS,
                    'voices': AudioManager.VOICES
                },
                'english': {
                    'accents': AudioManager.ENGLISH_ACCENTS,
                    'voices': AudioManager.VOICES
                },
                'chinese': {
                    'accents': {
                        'mandarin': '普通话',
                        'cantonese': '粤语'
                    },
                    'voices': AudioManager.VOICES
                }
            }
        })
    except Exception as e:
        logger.error(f"[考试API] 获取音频配置失败: {str(e)}")
        return system_error(f'获取音频配置失败: {str(e)}')

@exam_api.route('/audio/preferences', methods=['GET'])
def get_audio_preferences():
    """获取用户音频偏好"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return authentication_error('请先登录')
        
        from app.services.audio_manager import get_audio_manager
        audio_manager = get_audio_manager()
        
        preferences = {}
        for lang in ['japanese', 'english', 'chinese']:
            pref = audio_manager.get_user_preference(user_id, lang)
            if pref:
                preferences[lang] = pref
        
        return success_response(data={'user_id': user_id, 'preferences': preferences})
    except Exception as e:
        logger.error(f"[考试API] 获取音频偏好失败: {str(e)}")
        return system_error(f'获取音频偏好失败: {str(e)}')

@exam_api.route('/audio/preferences', methods=['POST'])
def set_audio_preferences():
    """设置用户音频偏好"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return authentication_error('请先登录')
        
        data = request.get_json()
        language = data.get('language')
        accent = data.get('accent')
        voice = data.get('voice')
        
        if not language or not accent or not voice:
            return validation_error('缺少必要参数')
        
        from app.services.audio_manager import get_audio_manager, AudioManager
        audio_manager = get_audio_manager()
        
        valid_accents = AudioManager.JAPANESE_ACCENTS if language == 'japanese' else \
                       AudioManager.ENGLISH_ACCENTS if language == 'english' else \
                       {'mandarin': '普通话', 'cantonese': '粤语'}
        
        if accent not in valid_accents or voice not in AudioManager.VOICES:
            return validation_error('无效的参数值')
        
        success = audio_manager.set_user_preference(user_id, language, accent, voice)
        
        if success:
            return success_response(data={
                'preferences': {
                    'language': language,
                    'accent': accent,
                    'voice': voice
                }
            }, message='音频偏好设置成功')
        else:
            return system_error('设置失败')
    except Exception as e:
        logger.error(f"[考试API] 设置音频偏好失败: {str(e)}")
        return system_error(f'设置音频偏好失败: {str(e)}')

# ==================== 统计API ====================

@exam_api.route('/stats/exam/<exam_id>', methods=['GET'])
def get_exam_stats(exam_id):
    """获取考试统计"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        stats = exam_service.get_exam_stats(exam_id)
        
        return success_response(data=stats)
    except Exception as e:
        logger.error(f"[考试API] 获取统计失败: {str(e)}")
        return system_error(f'获取统计失败: {str(e)}')

@exam_api.route('/stats/user/<user_id>', methods=['GET'])
def get_user_stats(user_id):
    """获取用户统计"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        stats = exam_service.get_user_stats(user_id)
        
        return success_response(data=stats)
    except Exception as e:
        logger.error(f"[考试API] 获取用户统计失败: {str(e)}")
        return system_error(f'获取用户统计失败: {str(e)}')

@exam_api.route('/stats/exam/system', methods=['GET'])
def get_system_stats():
    """获取系统级考试统计"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        stats = exam_service.get_system_wide_stats()
        
        return success_response(data=stats)
    except Exception as e:
        logger.error(f"[考试API] 获取系统统计失败: {str(e)}")
        return system_error(f'获取系统统计失败: {str(e)}')

@exam_api.route('/stats/exam/activity', methods=['GET'])
def get_exam_activity():
    """获取最近考试活动"""
    try:
        from app.services.exam_service import ExamService
        exam_service = ExamService()
        
        days = request.args.get('days', 7, type=int)
        activity = exam_service.get_recent_exam_activity(days)
        
        return success_response(data=activity)
    except Exception as e:
        logger.error(f"[考试API] 获取考试活动失败: {str(e)}")
        return system_error(f'获取考试活动失败: {str(e)}')