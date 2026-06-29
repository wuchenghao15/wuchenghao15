# -*- coding: utf-8 -*-
"""AI题库管理API - 听力题智能生成、管理、推荐、质量分析"""

from flask import Blueprint, jsonify, request, session
from datetime import datetime
from typing import Dict, List, Any

from app.ai.question_bank_ai import (
    get_question_bank_ai,
    ListeningLanguage,
    ListeningAccent,
    ListeningVoice,
    ListeningDifficulty,
    ListeningTopic,
    ListeningQuestion
)

question_bank_ai_api = Blueprint('question_bank_ai_api', __name__, url_prefix='/api/question_bank_ai')


@question_bank_ai_api.route('/', methods=['GET'])
def index():
    """AI题库API状态"""
    ai = get_question_bank_ai()
    stats = ai.get_statistics()
    return jsonify({
        'success': True,
        'status': 'ready',
        'module': 'AI题库管理智能助手',
        'features': [
            '听力题智能生成',
            '多口音多音色支持',
            '题目质量分析',
            '智能推荐系统',
            '用户偏好管理'
        ],
        'statistics': {
            'total_questions': stats.total_questions,
            'listening_questions': stats.listening_questions,
            'by_language': stats.by_language,
            'by_accent': stats.by_accent,
            'by_difficulty': stats.by_difficulty,
            'avg_correct_rate': stats.avg_correct_rate
        },
        'api_endpoints': [
            '/api/question_bank_ai/listening/generate',
            '/api/question_bank_ai/listening/generate_mass',
            '/api/question_bank_ai/listening/questions',
            '/api/question_bank_ai/listening/search',
            '/api/question_bank_ai/listening/stats',
            '/api/question_bank_ai/listening/accents',
            '/api/question_bank_ai/listening/voices',
            '/api/question_bank_ai/listening/preferences',
            '/api/question_bank_ai/listening/recommend',
            '/api/question_bank_ai/listening/quality/<id>'
        ]
    })


@question_bank_ai_api.route('/listening/generate', methods=['POST'])
def generate_listening_question():
    """AI智能生成听力题"""
    try:
        data = request.get_json()
        
        language = data.get('language', 'english')
        accent = data.get('accent', 'us')
        voice = data.get('voice', 'female')
        difficulty = int(data.get('difficulty', 2))
        topic = data.get('topic', 'daily')
        count = int(data.get('count', 1))

        ai = get_question_bank_ai()
        
        # 验证参数
        try:
            lang_enum = ListeningLanguage(language)
        except ValueError:
            return jsonify({'success': False, 'error': f'不支持的语言: {language}'}), 400
        
        try:
            # 根据语言验证口音
            if lang_enum == ListeningLanguage.JAPANESE:
                if accent not in ['kanto', 'kansai']:
                    return jsonify({'success': False, 'error': f'日语不支持口音: {accent}'}), 400
            elif lang_enum == ListeningLanguage.ENGLISH:
                if accent not in ['uk', 'us', 'africa', 'india']:
                    return jsonify({'success': False, 'error': f'英语不支持口音: {accent}'}), 400
            
            accent_enum = ListeningAccent(accent)
            voice_enum = ListeningVoice(voice)
            difficulty_enum = ListeningDifficulty(difficulty)
            topic_enum = ListeningTopic(topic)
        except ValueError as e:
            return jsonify({'success': False, 'error': f'参数错误: {str(e)}'}), 400

        questions = ai.generate_listening_question(
            language=lang_enum,
            accent=accent_enum,
            voice=voice_enum,
            difficulty=difficulty_enum,
            topic=topic_enum,
            count=count
        )

        return jsonify({
            'success': True,
            'generated_count': len(questions),
            'questions': [q.to_dict() for q in questions],
            'message': f'成功生成 {len(questions)} 道{language}听力题',
            'config': {
                'language': language,
                'accent': accent,
                'voice': voice,
                'difficulty': difficulty,
                'topic': topic
            }
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_ai_api.route('/listening/generate_mass', methods=['POST'])
def generate_mass_listening_questions():
    """批量生成海量听力题"""
    try:
        data = request.get_json()
        
        count = int(data.get('count', 50))
        languages = data.get('languages', ['japanese', 'english'])
        accents = data.get('accents', ['kanto', 'us'])
        voices = data.get('voices', ['female', 'male'])
        difficulties = data.get('difficulties', [1, 2, 3])
        topics = data.get('topics', ['daily', 'business', 'campus'])

        ai = get_question_bank_ai()
        generated = ai.generate_mass_listening_questions(
            count=count,
            languages=languages,
            accents=accents,
            voices=voices,
            difficulties=difficulties,
            topics=topics
        )

        return jsonify({
            'success': True,
            'generated_count': generated,
            'message': f'成功生成 {generated} 道听力题',
            'config': {
                'languages': languages,
                'accents': accents,
                'voices': voices,
                'difficulties': difficulties,
                'topics': topics
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_ai_api.route('/listening/questions', methods=['GET'])
def get_listening_questions():
    """获取听力题列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        language = request.args.get('language')
        accent = request.args.get('accent')
        voice = request.args.get('voice')
        difficulty = request.args.get('difficulty')
        topic = request.args.get('topic')
        keyword = request.args.get('keyword')

        ai = get_question_bank_ai()
        
        filters = {}
        if language:
            filters['language'] = language
        if accent:
            filters['accent'] = accent
        if voice:
            filters['voice'] = voice
        if difficulty:
            filters['difficulty'] = int(difficulty)
        if topic:
            filters['topic'] = topic
        if keyword:
            filters['keyword'] = keyword

        questions = ai.search_questions(**filters, limit=1000)
        
        total = len(questions)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = questions[start:end]

        return jsonify({
            'success': True,
            'questions': [q.to_dict() for q in paginated],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_ai_api.route('/listening/questions/<question_id>', methods=['GET'])
def get_listening_question(question_id):
    """获取单个听力题"""
    try:
        ai = get_question_bank_ai()
        question = ai.get_question(question_id)
        
        if question:
            return jsonify({'success': True, 'question': question.to_dict()})
        else:
            return jsonify({'success': False, 'error': '听力题不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_ai_api.route('/listening/search', methods=['GET', 'POST'])
def search_listening_questions():
    """搜索听力题"""
    try:
        if request.method == 'POST':
            data = request.get_json()
        else:
            data = request.args.to_dict()

        ai = get_question_bank_ai()
        
        filters = {}
        if 'language' in data:
            filters['language'] = data['language']
        if 'accent' in data:
            filters['accent'] = data['accent']
        if 'voice' in data:
            filters['voice'] = data['voice']
        if 'difficulty' in data:
            filters['difficulty'] = int(data['difficulty'])
        if 'topic' in data:
            filters['topic'] = data['topic']
        if 'keyword' in data:
            filters['keyword'] = data['keyword']
        if 'limit' in data:
            filters['limit'] = int(data['limit'])
        else:
            filters['limit'] = 50

        questions = ai.search_questions(**filters)

        return jsonify({
            'success': True,
            'questions': [q.to_dict() for q in questions],
            'total': len(questions)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_ai_api.route('/listening/stats', methods=['GET'])
def get_listening_statistics():
    """获取听力题库统计"""
    try:
        ai = get_question_bank_ai()
        stats = ai.get_statistics()

        return jsonify({
            'success': True,
            'statistics': {
                'total_questions': stats.total_questions,
                'listening_questions': stats.listening_questions,
                'by_language': stats.by_language,
                'by_accent': stats.by_accent,
                'by_difficulty': stats.by_difficulty,
                'avg_correct_rate': round(stats.avg_correct_rate, 4),
                'ai_generated_count': stats.ai_generated_count
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_ai_api.route('/listening/accents', methods=['GET'])
def get_available_accents():
    """获取可用口音列表"""
    try:
        language = request.args.get('language', 'japanese')
        ai = get_question_bank_ai()
        accents = ai.get_available_accents(language)

        return jsonify({
            'success': True,
            'language': language,
            'accents': accents,
            'description': {
                'japanese': {
                    'kanto': '关东腔（标准东京口音）',
                    'kansai': '关西腔（大阪/京都口音）'
                },
                'english': {
                    'uk': '英式发音（英国标准口音）',
                    'us': '美式发音（美国标准口音）',
                    'africa': '非洲英语（非洲口音）',
                    'india': '印度英语（印度口音）'
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_ai_api.route('/listening/voices', methods=['GET'])
def get_available_voices():
    """获取可用音色列表"""
    try:
        ai = get_question_bank_ai()
        voices = ai.get_available_voices()

        return jsonify({
            'success': True,
            'voices': voices,
            'description': {
                'female': '标准女声（清晰柔和）',
                'male': '标准男声（沉稳有力）'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_ai_api.route('/listening/preferences', methods=['GET', 'POST'])
def user_listening_preferences():
    """用户听力偏好管理"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '未登录'}), 401

        ai = get_question_bank_ai()

        if request.method == 'POST':
            data = request.get_json()
            language = data.get('language')
            accent = data.get('accent')
            voice = data.get('voice')

            if not all([language, accent, voice]):
                return jsonify({'success': False, 'error': '缺少必要参数'}), 400

            ai.set_user_preference(user_id, language, accent, voice)

            return jsonify({
                'success': True,
                'message': '听力偏好设置成功',
                'preference': {
                    'language': language,
                    'accent': accent,
                    'voice': voice
                }
            })
        else:
            language = request.args.get('language', 'japanese')
            preference = ai.get_user_preference(user_id, language)

            return jsonify({
                'success': True,
                'user_id': user_id,
                'language': language,
                'preference': preference
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_ai_api.route('/listening/recommend', methods=['GET', 'POST'])
def recommend_listening_questions():
    """为用户智能推荐听力题"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            # 未登录用户使用默认配置
            user_id = 0

        if request.method == 'POST':
            data = request.get_json()
            language = data.get('language', 'english')
            difficulty = int(data.get('difficulty', 2))
            count = int(data.get('count', 10))
        else:
            language = request.args.get('language', 'english')
            difficulty = int(request.args.get('difficulty', 2))
            count = int(request.args.get('count', 10))

        ai = get_question_bank_ai()
        questions = ai.recommend_questions_for_user(
            user_id=user_id,
            language=language,
            difficulty=difficulty,
            count=count
        )

        return jsonify({
            'success': True,
            'user_id': user_id,
            'language': language,
            'recommended_count': len(questions),
            'questions': [q.to_dict() for q in questions],
            'message': f'为您推荐 {len(questions)} 道听力题'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_ai_api.route('/listening/quality/<question_id>', methods=['GET'])
def analyze_question_quality(question_id):
    """分析听力题质量"""
    try:
        ai = get_question_bank_ai()
        result = ai.analyze_question_quality(question_id)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_ai_api.route('/listening/statistics/update', methods=['POST'])
def update_question_statistics():
    """更新题目统计数据"""
    try:
        data = request.get_json()
        question_id = data.get('question_id')
        correct = data.get('correct', True)

        if not question_id:
            return jsonify({'success': False, 'error': '缺少题目ID'}), 400

        ai = get_question_bank_ai()
        ai.update_question_statistics(question_id, correct)

        return jsonify({
            'success': True,
            'message': '题目统计更新成功',
            'question_id': question_id,
            'correct': correct
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_ai_api.route('/listening/topics', methods=['GET'])
def get_available_topics():
    """获取可用主题列表"""
    topics = {
        'daily': '日常生活',
        'business': '商务场景',
        'campus': '校园场景',
        'news': '新闻报道',
        'culture': '文化交流',
        'science': '科学技术'
    }

    return jsonify({
        'success': True,
        'topics': topics,
        'description': {
            'daily': '日常生活对话场景，包括购物、交通、天气等',
            'business': '商务工作场景，包括会议、项目管理等',
            'campus': '校园学习场景，包括考试、图书馆等',
            'news': '新闻报道场景，包括经济、科技新闻等',
            'culture': '文化交流场景，包括旅行、文化介绍等',
            'science': '科学技术场景，包括科学发现、技术发展等'
        }
    })


@question_bank_ai_api.route('/listening/difficulties', methods=['GET'])
def get_available_difficulties():
    """获取可用难度列表"""
    difficulties = {
        1: '初级（适合入门学习者）',
        2: '中级（适合有一定基础的学习者）',
        3: '高级（适合熟练学习者）',
        4: '专家级（适合专业学习者）'
    }

    return jsonify({
        'success': True,
        'difficulties': difficulties,
        'description': {
            1: '初级难度：简单的日常对话，词汇量约500-1000',
            2: '中级难度：中等复杂对话，词汇量约1000-3000',
            3: '高级难度：复杂对话和专业内容，词汇量约3000-5000',
            4: '专家级难度：专业领域对话，词汇量5000+'
        }
    })


@question_bank_ai_api.route('/audio/config', methods=['GET'])
def get_audio_config():
    """获取音频配置信息"""
    config = {
        'japanese': {
            'accents': ['kanto', 'kansai'],
            'voices': ['female', 'male'],
            'accent_description': {
                'kanto': '关东腔（标准东京口音）',
                'kansai': '关西腔（大阪/京都口音）'
            },
            'voice_description': {
                'female': '标准女声',
                'male': '标准男声'
            },
            'audio_format': 'mp3',
            'default_accent': 'kanto',
            'default_voice': 'female'
        },
        'english': {
            'accents': ['uk', 'us', 'africa', 'india'],
            'voices': ['female', 'male'],
            'accent_description': {
                'uk': '英式发音',
                'us': '美式发音',
                'africa': '非洲英语',
                'india': '印度英语'
            },
            'voice_description': {
                'female': '标准女声',
                'male': '标准男声'
            },
            'audio_format': 'mp3',
            'default_accent': 'us',
            'default_voice': 'female'
        },
        'audio_generation': {
            'methods': ['browser_tts', 'server_tts', 'pre_recorded'],
            'browser_tts_supported': True,
            'server_tts_available': True,
            'pre_recorded_library': True
        }
    }

    return jsonify({
        'success': True,
        'config': config,
        'message': '听力音频配置信息'
    })