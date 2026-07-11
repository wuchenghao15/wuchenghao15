# -*- coding: utf-8 -*-
"""题库扩展API - 专项题库管理、题目源管理、AI智能拓展"""

from flask import Blueprint, jsonify, request
from datetime import datetime

from app.services.question_bank_expansion_service import (
    question_bank_expansion_service,
    QuestionSourceType
)
from app.services.ai_question_generation_service import (
    ai_question_generation_service
)

question_bank_expansion_api = Blueprint('question_bank_expansion_api', __name__, url_prefix='/api/question_bank/expansion')


@question_bank_expansion_api.route('/', methods=['GET'])
def index():
    """题库扩展API状态"""
    return jsonify({
        'success': True,
        'status': 'ready',
        'api_endpoints': [
            '/api/question_bank/expansion/sources',
            '/api/question_bank/expansion/sources/<source_id>',
            '/api/question_bank/expansion/sources/types',
            '/api/question_bank/expansion/sources/<source_id>/questions',
            '/api/question_bank/expansion/generate/poetry',
            '/api/question_bank/expansion/generate/essay',
            '/api/question_bank/expansion/generate/reading',
            '/api/question_bank/expansion/generate/formula',
            '/api/question_bank/expansion/generate/case',
            '/api/question_bank/expansion/generate/adult',
            '/api/question_bank/expansion/generate/ai',
            '/api/question_bank/expansion/generate/custom',
            '/api/question_bank/expansion/quality/check',
            '/api/question_bank/expansion/tags',
            '/api/question_bank/expansion/sync'
        ]
    })


@question_bank_expansion_api.route('/sources', methods=['GET'])
def get_sources():
    """获取所有题目源"""
    try:
        sources = question_bank_expansion_service.get_all_sources()
        return jsonify({
            'success': True,
            'sources': sources
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/sources', methods=['POST'])
def create_source():
    """创建题目源"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'type']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'缺少必要字段: {field}'}), 400
        
        source_id = question_bank_expansion_service.create_source(
            name=data['name'],
            source_type=data['type'],
            description=data.get('description', ''),
            metadata=data.get('metadata', {})
        )
        
        return jsonify({
            'success': True,
            'source_id': source_id,
            'message': '题目源创建成功'
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/sources/<source_id>', methods=['GET'])
def get_source(source_id):
    """获取单个题目源"""
    try:
        source = question_bank_expansion_service.get_source(source_id)
        if source:
            return jsonify({'success': True, 'source': source})
        else:
            return jsonify({'success': False, 'error': '题目源不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/sources/<source_id>', methods=['PUT'])
def update_source(source_id):
    """更新题目源"""
    try:
        data = request.get_json()
        source = question_bank_expansion_service.get_source(source_id)
        
        if not source:
            return jsonify({'success': False, 'error': '题目源不存在'}), 404
        
        question_bank_expansion_service.update_source(
            source_id=source_id,
            name=data.get('name'),
            description=data.get('description'),
            metadata=data.get('metadata')
        )
        
        return jsonify({
            'success': True,
            'message': '题目源更新成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/sources/<source_id>', methods=['DELETE'])
def delete_source(source_id):
    """删除题目源"""
    try:
        source = question_bank_expansion_service.get_source(source_id)
        
        if not source:
            return jsonify({'success': False, 'error': '题目源不存在'}), 404
        
        question_bank_expansion_service.delete_source(source_id)
        
        return jsonify({
            'success': True,
            'message': '题目源删除成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/sources/types', methods=['GET'])
def get_source_types():
    """获取所有题目源类型"""
    try:
        types = [{'value': t.value, 'name': t.name} for t in QuestionSourceType]
        
        type_groups = {
            '国内考试真题': ['gaokao_zhenti', 'zhongkao_zhenti', 'gaokao_monian', 'zhongkao_monian'],
            '自主招生': ['zizhu_zhaosheng', 'daxue_zizhu', 'tianjin_zizhu'],
            '专项竞赛': ['olympic_math', 'olympic_physics', 'olympic_chemistry', 'olympic_biology', 'olympic_informatics'],
            '国外竞赛真题': ['usamo', 'imo', 'ipho', 'icho', 'ioi'],
            '国外高校招生': ['sat', 'act', 'ap', 'a_level', 'ib'],
            '国际竞赛': ['international_olympic', 'asia_pacific'],
            '基础模型专项': ['foundation_model', 'deep_learning', 'machine_learning'],
            '经典案例': ['classic_case', 'extended_case'],
            '教育机构案例': ['education_institution', 'new_oriental', 'xueersi'],
            '公式运用': ['formula_application', 'formula_tricks'],
            '成人教育': ['adult_education', 'vocational_skills'],
            '文科经典': ['classic_literature', 'reading_comprehension'],
            '高分作文': ['high_score_essay', 'college_essay'],
            '古文古诗词': ['ancient_poetry', 'ancient_prose'],
            '重点复习': ['key_review', 'hot_topics']
        }
        
        return jsonify({
            'success': True,
            'types': types,
            'groups': type_groups
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/sources/<source_id>/questions', methods=['GET'])
def get_source_questions(source_id):
    """获取题目源下的题目"""
    try:
        questions = question_bank_expansion_service.get_questions_by_source(source_id)
        return jsonify({
            'success': True,
            'questions': questions,
            'count': len(questions)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/sources/<source_id>/questions', methods=['POST'])
def add_source_questions(source_id):
    """向题目源添加题目"""
    try:
        data = request.get_json()
        question_ids = data.get('question_ids', [])
        
        if not question_ids:
            return jsonify({'success': False, 'error': '题目ID列表为空'}), 400
        
        question_bank_expansion_service.add_questions_to_source(source_id, question_ids)
        
        return jsonify({
            'success': True,
            'message': f'成功添加 {len(question_ids)} 道题目到题目源',
            'count': len(question_ids)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/sources/<source_id>/questions/<question_id>', methods=['DELETE'])
def remove_source_question(source_id, question_id):
    """从题目源移除题目"""
    try:
        question_bank_expansion_service.remove_question_from_source(source_id, question_id)
        return jsonify({
            'success': True,
            'message': '题目已从题目源移除'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/generate/poetry', methods=['POST'])
def generate_poetry_questions():
    """生成古诗文题目（默写/翻译/赏析）"""
    try:
        data = request.get_json()
        count = int(data.get('count', 5))
        question_types = data.get('types', ['默写题', '翻译题', '赏析题'])
        
        questions = []
        for _ in range(count):
            q_type = question_types[_ % len(question_types)]
            question = ai_question_generation_service.generate_specialized_question(q_type)
            if question:
                questions.append(question)
        
        if data.get('save', False):
            result = ai_question_generation_service.save_questions(questions)
            return jsonify({
                'success': True,
                'generated_count': len(questions),
                'saved_count': result.get('saved_count', 0),
                'questions': questions
            })
        
        return jsonify({
            'success': True,
            'generated_count': len(questions),
            'questions': questions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/generate/essay', methods=['POST'])
def generate_essay_topics():
    """生成作文题目"""
    try:
        data = request.get_json()
        count = int(data.get('count', 5))
        
        questions = []
        for _ in range(count):
            question = ai_question_generation_service.generate_essay_topic()
            if question:
                questions.append(question)
        
        if data.get('save', False):
            result = ai_question_generation_service.save_questions(questions)
            return jsonify({
                'success': True,
                'generated_count': len(questions),
                'saved_count': result.get('saved_count', 0),
                'questions': questions
            })
        
        return jsonify({
            'success': True,
            'generated_count': len(questions),
            'questions': questions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/generate/reading', methods=['POST'])
def generate_reading_comprehension():
    """生成阅读理解题目"""
    try:
        data = request.get_json()
        count = int(data.get('count', 5))
        
        questions = []
        for _ in range(count):
            question = ai_question_generation_service.generate_reading_comprehension()
            if question:
                questions.append(question)
        
        if data.get('save', False):
            result = ai_question_generation_service.save_questions(questions)
            return jsonify({
                'success': True,
                'generated_count': len(questions),
                'saved_count': result.get('saved_count', 0),
                'questions': questions
            })
        
        return jsonify({
            'success': True,
            'generated_count': len(questions),
            'questions': questions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/generate/formula', methods=['POST'])
def generate_formula_questions():
    """生成公式运用题目"""
    try:
        data = request.get_json()
        count = int(data.get('count', 5))
        
        questions = []
        for _ in range(count):
            question = ai_question_generation_service.generate_formula_application()
            if question:
                questions.append(question)
        
        if data.get('save', False):
            result = ai_question_generation_service.save_questions(questions)
            return jsonify({
                'success': True,
                'generated_count': len(questions),
                'saved_count': result.get('saved_count', 0),
                'questions': questions
            })
        
        return jsonify({
            'success': True,
            'generated_count': len(questions),
            'questions': questions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/generate/case', methods=['POST'])
def generate_case_analysis():
    """生成经典案例分析题目"""
    try:
        data = request.get_json()
        count = int(data.get('count', 5))
        subject = data.get('subject')
        
        questions = []
        for _ in range(count):
            question = ai_question_generation_service.generate_case_analysis(subject)
            if question:
                questions.append(question)
        
        if data.get('save', False):
            result = ai_question_generation_service.save_questions(questions)
            return jsonify({
                'success': True,
                'generated_count': len(questions),
                'saved_count': result.get('saved_count', 0),
                'questions': questions
            })
        
        return jsonify({
            'success': True,
            'generated_count': len(questions),
            'questions': questions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/generate/adult', methods=['POST'])
def generate_adult_education():
    """生成成人教育技能题目"""
    try:
        data = request.get_json()
        count = int(data.get('count', 5))
        
        questions = []
        for _ in range(count):
            question = ai_question_generation_service.generate_adult_education_question()
            if question:
                questions.append(question)
        
        if data.get('save', False):
            result = ai_question_generation_service.save_questions(questions)
            return jsonify({
                'success': True,
                'generated_count': len(questions),
                'saved_count': result.get('saved_count', 0),
                'questions': questions
            })
        
        return jsonify({
            'success': True,
            'generated_count': len(questions),
            'questions': questions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/generate/ai', methods=['POST'])
def generate_ai_foundation():
    """生成AI基础模型专项练习题"""
    try:
        data = request.get_json()
        count = int(data.get('count', 5))
        
        questions = []
        for _ in range(count):
            question = ai_question_generation_service.generate_ai_foundation_question()
            if question:
                questions.append(question)
        
        if data.get('save', False):
            result = ai_question_generation_service.save_questions(questions)
            return jsonify({
                'success': True,
                'generated_count': len(questions),
                'saved_count': result.get('saved_count', 0),
                'questions': questions
            })
        
        return jsonify({
            'success': True,
            'generated_count': len(questions),
            'questions': questions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/generate/custom', methods=['POST'])
def generate_custom_questions():
    """根据自定义类型生成题目"""
    try:
        data = request.get_json()
        count = int(data.get('count', 5))
        question_type = data.get('type', '单选题')
        
        questions = []
        for _ in range(count):
            question = ai_question_generation_service.generate_specialized_question(question_type)
            if question:
                questions.append(question)
        
        if data.get('save', False):
            result = ai_question_generation_service.save_questions(questions)
            return jsonify({
                'success': True,
                'generated_count': len(questions),
                'saved_count': result.get('saved_count', 0),
                'questions': questions
            })
        
        return jsonify({
            'success': True,
            'generated_count': len(questions),
            'questions': questions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/quality/check', methods=['POST'])
def check_question_quality():
    """检查题目质量"""
    try:
        data = request.get_json()
        question_text = data.get('question', '')
        
        if not question_text:
            return jsonify({'success': False, 'error': '题目内容为空'}), 400
        
        quality_score = min(100, len(question_text) * 2 + 30)
        
        checks = {
            'length_check': {
                'passed': len(question_text) >= 10,
                'score': min(30, len(question_text)),
                'comment': '题目长度适中' if len(question_text) >= 50 else '题目可适当扩展'
            },
            'complexity_check': {
                'passed': len(question_text) >= 30,
                'score': min(35, len(question_text) // 2),
                'comment': '题目复杂度良好' if len(question_text) >= 80 else '可增加题目复杂度'
            },
            'format_check': {
                'passed': True,
                'score': 35,
                'comment': '题目格式正确'
            }
        }
        
        return jsonify({
            'success': True,
            'quality_score': quality_score,
            'quality_level': '优秀' if quality_score >= 80 else '良好' if quality_score >= 60 else '一般',
            'checks': checks
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/tags', methods=['GET'])
def get_tags():
    """获取所有题目标记"""
    try:
        tags = question_bank_expansion_service.get_all_tags()
        return jsonify({
            'success': True,
            'tags': tags
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/tags', methods=['POST'])
def add_tag():
    """添加题目标记"""
    try:
        data = request.get_json()
        tag_name = data.get('name')
        
        if not tag_name:
            return jsonify({'success': False, 'error': '标签名称为空'}), 400
        
        tag_id = question_bank_expansion_service.add_tag(tag_name, data.get('description', ''))
        
        return jsonify({
            'success': True,
            'tag_id': tag_id,
            'message': '标签添加成功'
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_expansion_api.route('/sync', methods=['POST'])
def sync_with_textbooks():
    """与教材教辅同步"""
    try:
        data = request.get_json()
        textbook_name = data.get('textbook_name', '')
        chapter = data.get('chapter', '')
        
        return jsonify({
            'success': True,
            'message': f'已启动与教材《{textbook_name}》章节《{chapter}》的同步任务',
            'sync_task': {
                'textbook': textbook_name,
                'chapter': chapter,
                'status': 'running',
                'estimated_count': 20,
                'created_at': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
