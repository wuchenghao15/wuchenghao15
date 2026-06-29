# -*- coding: utf-8 -*-
"""题库管理API - 完整的题库CRUD、AI智能出题、统计分析、导入导出、智能组卷"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from typing import Dict, List, Any

from app.services.enhanced_question_bank_service import (
    enhanced_question_bank_service,
    QuestionType,
    DifficultyLevel,
    QuestionCategory
)

question_bank_api = Blueprint('question_bank_api', __name__, url_prefix='/api/question_bank')


@question_bank_api.route('/', methods=['GET'])
def index():
    """题库API状态"""
    stats = enhanced_question_bank_service.get_statistics()
    return jsonify({
        'success': True,
        'status': 'ready',
        'total_questions': stats.total_questions,
        'api_endpoints': [
            '/api/question_bank/questions',
            '/api/question_bank/questions/<id>',
            '/api/question_bank/questions/search',
            '/api/question_bank/questions/batch',
            '/api/question_bank/generate',
            '/api/question_bank/generate/mass',
            '/api/question_bank/stats',
            '/api/question_bank/categories',
            '/api/question_bank/exam_paper',
            '/api/question_bank/import',
            '/api/question_bank/export'
        ]
    })


@question_bank_api.route('/questions', methods=['GET'])
def get_questions():
    """获取题目列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        q_type = request.args.get('type')
        category = request.args.get('category')
        difficulty = request.args.get('difficulty')
        keyword = request.args.get('keyword')
        knowledge_point = request.args.get('knowledge_point')
        year = request.args.get('year')

        filters = {}
        if q_type:
            filters['type'] = q_type
        if category:
            filters['category'] = category
        if difficulty:
            filters['difficulty'] = difficulty
        if keyword:
            filters['keyword'] = keyword
        if knowledge_point:
            filters['knowledge_point'] = knowledge_point
        if year:
            filters['year'] = int(year)

        questions = enhanced_question_bank_service.search_questions(**filters)
        
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


@question_bank_api.route('/questions/<question_id>', methods=['GET'])
def get_question(question_id):
    """获取单个题目"""
    try:
        question = enhanced_question_bank_service.get_question(question_id)
        if question:
            return jsonify({'success': True, 'question': question.to_dict()})
        else:
            return jsonify({'success': False, 'error': '题目不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/questions', methods=['POST'])
def add_question():
    """添加题目"""
    try:
        data = request.get_json()
        
        required_fields = ['type', 'category', 'difficulty', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'缺少必要字段: {field}'}), 400

        question_id = enhanced_question_bank_service.add_question(data)
        
        return jsonify({
            'success': True,
            'question_id': question_id,
            'message': '题目添加成功'
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/questions/<question_id>', methods=['PUT'])
def update_question(question_id):
    """更新题目"""
    try:
        data = request.get_json()
        question = enhanced_question_bank_service.get_question(question_id)
        
        if not question:
            return jsonify({'success': False, 'error': '题目不存在'}), 404

        if 'content' in data:
            question.content = data['content']
        if 'options' in data:
            question.options = data['options']
        if 'correct_answer' in data:
            question.correct_answer = data['correct_answer']
        if 'explanation' in data:
            question.explanation = data['explanation']
        if 'analysis' in data:
            question.analysis = data['analysis']
        if 'tags' in data:
            question.tags = data['tags']
        if 'knowledge_points' in data:
            question.knowledge_points = data['knowledge_points']
        if 'formula_used' in data:
            question.formula_used = data['formula_used']
        if 'score' in data:
            question.score = data['score']
        if 'type' in data:
            question.type = QuestionType(data['type'])
        if 'category' in data:
            question.category = QuestionCategory(data['category'])
        if 'difficulty' in data:
            question.difficulty = DifficultyLevel(data['difficulty'])
        
        question.updated_at = datetime.now().timestamp()
        enhanced_question_bank_service._save_question_bank()

        return jsonify({
            'success': True,
            'message': '题目更新成功',
            'question': question.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/questions/<question_id>', methods=['DELETE'])
def delete_question(question_id):
    """删除题目"""
    try:
        question = enhanced_question_bank_service.get_question(question_id)
        
        if not question:
            return jsonify({'success': False, 'error': '题目不存在'}), 404

        del enhanced_question_bank_service._questions[question_id]
        enhanced_question_bank_service._save_question_bank()

        return jsonify({
            'success': True,
            'message': '题目删除成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/questions/batch', methods=['POST'])
def add_questions_batch():
    """批量添加题目"""
    try:
        data = request.get_json()
        questions_data = data.get('questions', [])
        
        if not questions_data:
            return jsonify({'success': False, 'error': '题目数据为空'}), 400

        success, failed = enhanced_question_bank_service.add_questions_batch(questions_data)

        return jsonify({
            'success': True,
            'message': f'批量添加完成',
            'success_count': success,
            'failed_count': failed
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/questions/search', methods=['GET', 'POST'])
def search_questions():
    """搜索题目"""
    try:
        if request.method == 'POST':
            data = request.get_json()
        else:
            data = request.args.to_dict()

        filters = {}
        if 'type' in data:
            filters['type'] = data['type']
        if 'category' in data:
            filters['category'] = data['category']
        if 'difficulty' in data:
            filters['difficulty'] = data['difficulty']
        if 'keyword' in data:
            filters['keyword'] = data['keyword']
        if 'knowledge_point' in data:
            filters['knowledge_point'] = data['knowledge_point']
        if 'year' in data:
            filters['year'] = int(data['year'])

        questions = enhanced_question_bank_service.search_questions(**filters)

        return jsonify({
            'success': True,
            'questions': [q.to_dict() for q in questions],
            'total': len(questions)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/generate', methods=['POST'])
def generate_question():
    """AI智能生成单道题目"""
    try:
        data = request.get_json()
        
        category = data.get('category', 'special_topic')
        q_type = data.get('type', 'single_choice')
        difficulty = data.get('difficulty', 'medium')

        question_data = enhanced_question_bank_service._expert_generate_question(
            category=category,
            q_type=q_type,
            difficulty=difficulty
        )

        question_id = enhanced_question_bank_service.add_question(question_data)

        return jsonify({
            'success': True,
            'question_id': question_id,
            'question': enhanced_question_bank_service.get_question(question_id).to_dict(),
            'message': 'AI智能生成题目成功'
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/generate/mass', methods=['POST'])
def generate_mass_questions():
    """批量生成海量题目"""
    try:
        data = request.get_json()
        
        count = int(data.get('count', 100))
        categories = data.get('categories', ['special_topic', 'must_know', 'calculation', 'logic', 'error_prone'])
        types = data.get('types', ['single_choice', 'multiple_choice', 'true_false', 'fill_blank', 'calculation'])
        difficulties = data.get('difficulties', ['easy', 'medium', 'hard'])

        generated = enhanced_question_bank_service.generate_mass_questions(
            count=count,
            categories=categories,
            types=types,
            difficulties=difficulties
        )

        return jsonify({
            'success': True,
            'generated_count': generated,
            'message': f'成功生成 {generated} 道题目',
            'categories': categories,
            'types': types,
            'difficulties': difficulties
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/generate/real_exam', methods=['POST'])
def generate_real_exam_questions():
    """添加历年真题"""
    try:
        data = request.get_json()
        
        year = int(data.get('year', 2024))
        questions_data = data.get('questions', [])

        enhanced_question_bank_service.add_real_exam_questions(year, questions_data)

        return jsonify({
            'success': True,
            'year': year,
            'count': len(questions_data),
            'message': f'{year}年真题添加成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/generate/must_know', methods=['POST'])
def generate_must_know_questions():
    """添加必考题"""
    try:
        data = request.get_json()
        questions_data = data.get('questions', [])

        enhanced_question_bank_service.add_must_know_questions(questions_data)

        return jsonify({
            'success': True,
            'count': len(questions_data),
            'message': '必考题添加成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/generate/final_challenge', methods=['POST'])
def generate_final_challenge_questions():
    """添加压轴题"""
    try:
        data = request.get_json()
        questions_data = data.get('questions', [])

        enhanced_question_bank_service.add_final_challenge_questions(questions_data)

        return jsonify({
            'success': True,
            'count': len(questions_data),
            'message': '压轴题添加成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/generate/bonus', methods=['POST'])
def generate_bonus_questions():
    """添加加分题"""
    try:
        data = request.get_json()
        questions_data = data.get('questions', [])

        enhanced_question_bank_service.add_bonus_questions(questions_data)

        return jsonify({
            'success': True,
            'count': len(questions_data),
            'message': '加分题添加成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/generate/special_topic', methods=['POST'])
def generate_special_topic_questions():
    """添加专项专题题目"""
    try:
        data = request.get_json()
        
        topic = data.get('topic', '专项训练')
        questions_data = data.get('questions', [])

        enhanced_question_bank_service.add_special_topic_questions(topic, questions_data)

        return jsonify({
            'success': True,
            'topic': topic,
            'count': len(questions_data),
            'message': f'{topic}专题题目添加成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/stats', methods=['GET'])
def get_statistics():
    """获取题库统计分析"""
    try:
        stats = enhanced_question_bank_service.get_statistics()

        return jsonify({
            'success': True,
            'statistics': {
                'total_questions': stats.total_questions,
                'by_type': stats.by_type,
                'by_category': stats.by_category,
                'by_difficulty': stats.by_difficulty,
                'by_year': stats.by_year,
                'avg_correct_rate': round(stats.avg_correct_rate, 2),
                'total_usage': stats.total_usage
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    try:
        categories = enhanced_question_bank_service.get_categories()

        return jsonify({
            'success': True,
            'categories': categories,
            'category_enum': [cat.value for cat in QuestionCategory],
            'type_enum': [t.value for t in QuestionType],
            'difficulty_enum': [d.value for d in DifficultyLevel]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/exam_paper', methods=['POST'])
def generate_exam_paper():
    """智能生成试卷"""
    try:
        data = request.get_json()
        
        title = data.get('title', f'智能组卷 - {datetime.now().strftime("%Y-%m-%d")}')
        total_score = float(data.get('total_score', 100.0))
        question_counts = data.get('question_counts')
        difficulty_distribution = data.get('difficulty_distribution')
        categories = data.get('categories')

        paper = enhanced_question_bank_service.generate_exam_paper(
            title=title,
            total_score=total_score,
            question_counts=question_counts,
            difficulty_distribution=difficulty_distribution,
            categories=categories
        )

        return jsonify({
            'success': True,
            'paper': paper,
            'message': '智能组卷成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/import', methods=['POST'])
def import_questions():
    """导入题目"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '未上传文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400

        import os
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            content = file.read().decode('utf-8')
            f.write(content)
            temp_path = f.name

        try:
            success, failed = enhanced_question_bank_service.import_from_json(temp_path)
        finally:
            os.unlink(temp_path)

        return jsonify({
            'success': True,
            'success_count': success,
            'failed_count': failed,
            'message': f'导入完成: {success}成功, {failed}失败'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@question_bank_api.route('/export', methods=['GET'])
def export_questions():
    """导出题目"""
    try:
        import os
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        success = enhanced_question_bank_service.export_to_json(temp_path)

        if success:
            from flask import send_file
            return send_file(
                temp_path,
                as_attachment=True,
                download_name=f'question_bank_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                mimetype='application/json'
            )
        else:
            return jsonify({'success': False, 'error': '导出失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500