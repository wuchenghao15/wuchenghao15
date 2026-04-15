# -*- coding: utf-8 -*-
"""
考试测试系统API
提供考试相关的接口，包括获取下一题、提交测试、获取测试结果等
"""


from app.models.exam_system import ExamSystemManager
from app.models.question import question_manager
from app.utils.logging import logger


# 创建考试测试API蓝图
exam_test_api = Blueprint('exam_test_api', __name__)

# 初始化考试系统管理器
exam_manager = ExamSystemManager()


@exam_test_api.route('/japanese-test/next-question', methods=['POST'])
def get_next_japanese_question():
    """获取下一道日语题目"""
    try:
        # 处理空请求体
        try:
            data = request.get_json() or {}
        except Exception:
            data = {}
        
        current_index = data.get('current_index', 0)
        user_id = data.get('user_id', 1)  # 默认使用用户ID 1
        
        # 1. 获取用户最近使用的题目，避免重复出题
        used_question_ids = exam_manager.get_user_used_questions(user_id, limit=100)  # 获取最近使用的100道题
        
        # 2. 分析用户表现，调整题目难度
        user_performance = exam_manager._analyze_user_performance(user_id)
        
        # 3. 根据用户表现确定难度范围
        difficulty_min = 1
        difficulty_max = 10
        
        if user_performance['average_accuracy'] > 0.8:  # 用户表现优秀，增加难题比例
            difficulty_min = 4
        elif user_performance['average_accuracy'] < 0.6:  # 用户表现较弱，增加简单题比例
            difficulty_max = 7
        
        # 4. 获取可用题目，排除已使用的题目
        # 获取足够多的题目进行筛选
        all_questions = question_manager.get_questions(
            language_id=1,  # 日语
            limit=50,  # 获取50道题进行筛选
            difficulty_min=difficulty_min,
            difficulty_max=difficulty_max
        )
        
        # 排除已使用的题目
        available_questions = [q for q in all_questions if q.id not in used_question_ids]
        
        # 如果可用题目不足，放宽限制
        if not available_questions:
            available_questions = all_questions
        
        if not available_questions:
            return jsonify({
                'success': False,
                'message': '已到达最后一题'
            }), 200
        
        # 随机选择一道题目
        import random
        question = random.choice(available_questions)
        
        # 5. 记录题目使用情况
        exam_manager.record_question_usage(user_id, question.id)
        
        # 将选项列表转换为字典格式（A, B, C, D）
        option_dict = {chr(65 + i): opt for i, opt in enumerate(question.options[:4])}
        
        # 构建问题HTML
        question_html = f"""
        <div class="question-section" data-question-id="{question.id}">
            <div class="question-number">問題 {current_index + 1}/20</div>
            <div class="question-text">{question.content}</div>
            <div class="options">
                <label class="option">
                    <input type="radio" name="question{question.id}" value="A">
                    <span class="option-label">A. {option_dict.get('A', '')}</span>
                </label>
                <label class="option">
                    <input type="radio" name="question{question.id}" value="B">
                    <span class="option-label">B. {option_dict.get('B', '')}</span>
                </label>
                <label class="option">
                    <input type="radio" name="question{question.id}" value="C">
                    <span class="option-label">C. {option_dict.get('C', '')}</span>
                </label>
                <label class="option">
                    <input type="radio" name="question{question.id}" value="D">
                    <span class="option-label">D. {option_dict.get('D', '')}</span>
                </label>
            </div>
        </div>
        """
        
        return jsonify({
            'success': True,
            'question_html': question_html,
            'question_id': question.id,
            'current_index': current_index
        }), 200
        
    except Exception as e:
        logger.error(f"获取下一题失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取下一题失败: {str(e)}'
        }), 500


@exam_test_api.route('/japanese-test/submit', methods=['POST'])
def submit_japanese_test():
    """提交日语测试"""
    try:
        data = request.get_json() or {}
        answers = data.get('answers', {})
        
        # 获取当前用户ID（从会话中获取）
        user_id = session.get('user_id', 1)  # 默认使用用户ID 1
        
        # 创建临时考试
        temp_exam = exam_manager.create_exam(
            title="日语能力测试",
            description="日语能力测试（N3级别）",
            language="japanese",
            level="intermediate",
            duration=30,
            question_count=20
        )
        
        # 生成试卷
        exam_paper = exam_manager.generate_exam_paper(temp_exam.id, user_id)
        
        # 开始考试
        exam_manager.start_exam(exam_paper.id)
        
        # 提交答案
        exam_result = exam_manager.submit_exam(exam_paper.id, answers)
        
        return jsonify({
            'success': True,
            'test_id': exam_result.id,
            'total_score': exam_result.total_score,
            'correct_count': exam_result.correct_count,
            'wrong_count': exam_result.wrong_count,
            'accuracy': exam_result.accuracy,
            'analysis': exam_result.analysis
        }), 200
        
    except Exception as e:
        logger.error(f"提交测试失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'提交测试失败: {str(e)}'
        }), 500


@exam_test_api.route('/test-result/<int:result_id>', methods=['GET'])
def get_test_result(result_id: int):
    """获取测试结果"""
    try:
        exam_result = exam_manager.get_exam_result(result_id)
        if not exam_result:
            return jsonify({
                'success': False,
                'message': '测试结果不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': exam_result.to_dict(),
            'message': '获取测试结果成功'
        }), 200
        
    except Exception as e:
        logger.error(f"获取测试结果失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取测试结果失败: {str(e)}'
        }), 500


@exam_test_api.route('/generate-personalized-exam', methods=['POST'])
def generate_personalized_exam():
    """生成个性化考试"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', 1)  # 默认使用用户ID 1
        language = data.get('language', 'japanese')
        level = data.get('level', 'intermediate')
        question_count = data.get('question_count', 20)
        topics = data.get('topics', [])
        
        # 生成个性化试卷
        exam_paper = exam_manager.generate_personalized_exam(
            user_id=user_id,
            language=language,
            level=level,
            question_count=question_count,
            topics=topics
        )
        
        return jsonify({
            'success': True,
            'exam_paper_id': exam_paper.id,
            'question_count': len(exam_paper.questions),
            'message': '生成个性化考试成功'
        }), 201
        
    except Exception as e:
        logger.error(f"生成个性化考试失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'生成个性化考试失败: {str(e)}'
        }), 500


@exam_test_api.route('/exam-statistics/<int:exam_id>', methods=['GET'])
def get_exam_statistics(exam_id: int):
    """获取考试统计信息"""
    try:
        statistics = exam_manager.get_exam_statistics(exam_id)
        if not statistics:
            return jsonify({
                'success': False,
                'message': '考试不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': statistics,
            'message': '获取考试统计信息成功'
        }), 200
        
    except Exception as e:
        logger.error(f"获取考试统计信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取考试统计信息失败: {str(e)}'
        }), 500


@exam_test_api.route('/learning-recommendations/<int:result_id>', methods=['GET'])
def get_learning_recommendations(result_id: int):
    """获取学习建议"""
    try:
        user_id = request.args.get('user_id', 1, type=int)  # 默认使用用户ID 1
        recommendations = exam_manager.generate_learning_recommendations(user_id, result_id)
        
        return jsonify({
            'success': True,
            'data': recommendations,
            'message': '获取学习建议成功'
        }), 200
        
    except Exception as e:
        logger.error(f"获取学习建议失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取学习建议失败: {str(e)}'
        }), 500
