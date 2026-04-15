# -*- coding: utf-8 -*-
"""
题库管理API
提供题库的题目、分类、语种和等级的管理接口
"""


from app.models.question import question_manager
from app.utils.logging import logger


# 创建题库API蓝图
question_bank_api = Blueprint('question_bank_api', __name__)


@question_bank_api.route('/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    try:
        categories = question_manager.get_all_categories()
        return jsonify({
            'success': True,
            'data': [category.to_dict() for category in categories],
            'message': '获取分类成功'
        }), 200
    except Exception as e:
        logger.error(f"获取分类失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取分类失败: {str(e)}'
        }), 500


@question_bank_api.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id: int):
    """获取单个分类"""
    try:
        category = question_manager.get_category(category_id)
        if not category:
            return jsonify({
                'success': False,
                'message': '分类不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': category.to_dict(),
            'message': '获取分类成功'
        }), 200
    except Exception as e:
        logger.error(f"获取分类失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取分类失败: {str(e)}'
        }), 500


@question_bank_api.route('/categories', methods=['POST'])
def create_category():
    """创建分类"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({
                'success': False,
                'message': '缺少分类名称'
            }), 400
        
        category = question_manager.create_category(
            name=data['name'],
            description=data.get('description')
        )
        
        return jsonify({
            'success': True,
            'data': category.to_dict(),
            'message': '创建分类成功'
        }), 201
    except Exception as e:
        logger.error(f"创建分类失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'创建分类失败: {str(e)}'
        }), 500


@question_bank_api.route('/languages', methods=['GET'])
def get_languages():
    """获取所有语种"""
    try:
        languages = question_manager.get_all_languages()
        return jsonify({
            'success': True,
            'data': [language.to_dict() for language in languages],
            'message': '获取语种成功'
        }), 200
    except Exception as e:
        logger.error(f"获取语种失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取语种失败: {str(e)}'
        }), 500


@question_bank_api.route('/languages/<int:language_id>', methods=['GET'])
def get_language(language_id: int):
    """获取单个语种"""
    try:
        language = question_manager.get_language(language_id)
        if not language:
            return jsonify({
                'success': False,
                'message': '语种不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': language.to_dict(),
            'message': '获取语种成功'
        }), 200
    except Exception as e:
        logger.error(f"获取语种失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取语种失败: {str(e)}'
        }), 500


@question_bank_api.route('/languages', methods=['POST'])
def create_language():
    """创建语种"""
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'code' not in data:
            return jsonify({
                'success': False,
                'message': '缺少语种名称或代码'
            }), 400
        
        language = question_manager.create_language(
            name=data['name'],
            code=data['code']
        )
        
        return jsonify({
            'success': True,
            'data': language.to_dict(),
            'message': '创建语种成功'
        }), 201
    except Exception as e:
        logger.error(f"创建语种失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'创建语种失败: {str(e)}'
        }), 500


@question_bank_api.route('/levels', methods=['GET'])
def get_levels():
    """获取所有等级"""
    try:
        levels = question_manager.get_all_levels()
        return jsonify({
            'success': True,
            'data': [level.to_dict() for level in levels],
            'message': '获取等级成功'
        }), 200
    except Exception as e:
        logger.error(f"获取等级失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取等级失败: {str(e)}'
        }), 500


@question_bank_api.route('/levels/<int:level_id>', methods=['GET'])
def get_level(level_id: int):
    """获取单个等级"""
    try:
        level = question_manager.get_level(level_id)
        if not level:
            return jsonify({
                'success': False,
                'message': '等级不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': level.to_dict(),
            'message': '获取等级成功'
        }), 200
    except Exception as e:
        logger.error(f"获取等级失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取等级失败: {str(e)}'
        }), 500


@question_bank_api.route('/levels', methods=['POST'])
def create_level():
    """创建等级"""
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'level' not in data:
            return jsonify({
                'success': False,
                'message': '缺少等级名称或级别'
            }), 400
        
        level = question_manager.create_level(
            name=data['name'],
            level=data['level'],
            description=data.get('description')
        )
        
        return jsonify({
            'success': True,
            'data': level.to_dict(),
            'message': '创建等级成功'
        }), 201
    except Exception as e:
        logger.error(f"创建等级失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'创建等级失败: {str(e)}'
        }), 500


@question_bank_api.route('/questions', methods=['GET'])
def get_questions():
    """获取题目列表，支持按分类、语种、等级过滤"""
    try:
        # 获取查询参数
        category_id = request.args.get('category_id', type=int)
        language_id = request.args.get('language_id', type=int)
        level_id = request.args.get('level_id', type=int)
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        # 获取题目
        questions = question_manager.get_questions(
            category_id=category_id,
            language_id=language_id,
            level_id=level_id,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'success': True,
            'data': [question.to_dict() for question in questions],
            'message': '获取题目成功',
            'total': len(questions)
        }), 200
    except Exception as e:
        logger.error(f"获取题目失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取题目失败: {str(e)}'
        }), 500


@question_bank_api.route('/questions/<int:question_id>', methods=['GET'])
def get_question(question_id: int):
    """获取单个题目"""
    try:
        question = question_manager.get_question(question_id)
        if not question:
            return jsonify({
                'success': False,
                'message': '题目不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': question.to_dict(),
            'message': '获取题目成功'
        }), 200
    except Exception as e:
        logger.error(f"获取题目失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取题目失败: {str(e)}'
        }), 500


@question_bank_api.route('/questions', methods=['POST'])
def create_question():
    """创建题目"""
    try:
        data = request.get_json()
        if not data or 'content' not in data or 'answer' not in data:
            return jsonify({
                'success': False,
                'message': '缺少题目内容或答案'
            }), 400
        
        question = question_manager.create_question(
            content=data['content'],
            answer=data['answer'],
            explanation=data.get('explanation'),
            category_id=data.get('category_id'),
            language_id=data.get('language_id'),
            level_id=data.get('level_id')
        )
        
        return jsonify({
            'success': True,
            'data': question.to_dict(),
            'message': '创建题目成功'
        }), 201
    except Exception as e:
        logger.error(f"创建题目失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'创建题目失败: {str(e)}'
        }), 500


@question_bank_api.route('/questions/<int:question_id>', methods=['PUT'])
def update_question(question_id: int):
    """更新题目"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少更新数据'
            }), 400
        
        question = question_manager.update_question(question_id, **data)
        if not question:
            return jsonify({
                'success': False,
                'message': '题目不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': question.to_dict(),
            'message': '更新题目成功'
        }), 200
    except Exception as e:
        logger.error(f"更新题目失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新题目失败: {str(e)}'
        }), 500


@question_bank_api.route('/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id: int):
    """删除题目"""
    try:
        success = question_manager.delete_question(question_id)
        if not success:
            return jsonify({
                'success': False,
                'message': '题目不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '删除题目成功'
        }), 200
    except Exception as e:
        logger.error(f"删除题目失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除题目失败: {str(e)}'
        }), 500


@question_bank_api.route('/questions/generate', methods=['POST'])
def generate_questions():
    """自动生成题目"""
    try:
        data = request.get_json() or {}
        count = data.get('count', 5)
        category_id = data.get('category_id')
        language_id = data.get('language_id')
        level_id = data.get('level_id')
        
        generated_questions = question_manager.generate_questions(
            count=count,
            category_id=category_id,
            language_id=language_id,
            level_id=level_id
        )
        
        return jsonify({
            'success': True,
            'data': [question.to_dict() for question in generated_questions],
            'message': f'成功生成 {len(generated_questions)} 道题目',
            'total': len(generated_questions)
        }), 201
    except Exception as e:
        logger.error(f"生成题目失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'生成题目失败: {str(e)}'
        }), 500


@question_bank_api.route('/questions/generate/ai', methods=['POST'])
def generate_question_by_ai():
    """使用AI生成单个题目"""
    try:
        data = request.get_json() or {}
        prompt = data.get('prompt')
        
        question = question_manager.generate_question_by_ai(prompt=prompt)
        if not question:
            return jsonify({
                'success': False,
                'message': 'AI生成题目失败'
            }), 500
        
        return jsonify({
            'success': True,
            'data': question.to_dict(),
            'message': 'AI生成题目成功'
        }), 201
    except Exception as e:
        logger.error(f"AI生成题目失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'AI生成题目失败: {str(e)}'
        }), 500
