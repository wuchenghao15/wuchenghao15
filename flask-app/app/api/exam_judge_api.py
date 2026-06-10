# -*- coding: utf-8 -*-
"""
考试判断API接口
提供统一的考试判断服务
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, request, jsonify
from exam_judge_system import ExamJudgeSystem, ExamType

exam_judge_api = Blueprint('exam_judge_api', __name__, url_prefix='/api/exam')
judge_system = ExamJudgeSystem()


@exam_judge_api.route('/judge', methods=['POST'])
def judge_exam_endpoint():
    """统一的考试判断接口"""
    try:
        data = request.get_json()
        
        exam_type = data.get('exam_type')
        user_id = data.get('user_id')
        score = data.get('score', 0)
        total_score = data.get('total_score', 100)
        answers = data.get('answers', [])
        time_spent = data.get('time_spent', 0)
        duration = data.get('duration', 0)
        
        # 调用判断系统（排除已定义的参数）
        extra_kwargs = {k: v for k, v in data.items() 
                       if k not in ['exam_type', 'user_id', 'score', 'total_score', 'answers', 'time_spent', 'duration']}
        
        result = judge_system.judge_exam(
            exam_type=exam_type,
            user_id=user_id,
            score=score,
            total_score=total_score,
            answers=answers,
            time_spent=time_spent,
            duration=duration,
            **extra_kwargs
        )
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@exam_judge_api.route('/record', methods=['POST'])
def save_exam_record():
    """保存考试记录"""
    try:
        data = request.get_json()
        
        record_id = judge_system.save_exam_record(
            exam_type=data.get('exam_type'),
            user_id=data.get('user_id'),
            exam_id=data.get('exam_id'),
            exam_name=data.get('exam_name'),
            score=data.get('score', 0),
            total_score=data.get('total_score', 100),
            correct_count=data.get('correct_count', 0),
            total_questions=data.get('total_questions', 0),
            time_spent=data.get('time_spent', 0),
            duration=data.get('duration', 0),
            answers=data.get('answers'),
            difficulty=data.get('difficulty', 'medium')
        )
        
        if record_id:
            return jsonify({
                "success": True,
                "record_id": record_id
            })
        else:
            return jsonify({
                "success": False,
                "error": "保存失败"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@exam_judge_api.route('/report', methods=['GET'])
def get_exam_report():
    """获取考试报告"""
    try:
        user_id = request.args.get('user_id', type=int)
        exam_type = request.args.get('exam_type')
        
        report = judge_system.generate_exam_report(user_id, exam_type)
        
        return jsonify({
            "success": True,
            "data": report
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@exam_judge_api.route('/types', methods=['GET'])
def get_exam_types():
    """获取支持的考试类型"""
    types = [
        {
            "value": ExamType.PLACEMENT.value,
            "label": "摸底考试",
            "description": "了解学生初始水平"
        },
        {
            "value": ExamType.RANDOM_QUIZ.value,
            "label": "随机小测试",
            "description": "日常快速检测"
        },
        {
            "value": ExamType.POST_LESSON.value,
            "label": "课后测试",
            "description": "巩固课堂学习成果"
        },
        {
            "value": ExamType.MIDTERM.value,
            "label": "期中考试",
            "description": "检验阶段性学习成果"
        },
        {
            "value": ExamType.FINAL.value,
            "label": "期末考试",
            "description": "综合能力终极检验"
        },
        {
            "value": ExamType.PROMOTION.value,
            "label": "升学考试",
            "description": "选拔进入下一级别"
        },
        {
            "value": ExamType.RETEST.value,
            "label": "补考",
            "description": "为未通过者提供机会"
        }
    ]
    
    return jsonify({
        "success": True,
        "data": types
    })


@exam_judge_api.route('/guide', methods=['GET'])
def get_exam_guide():
    """获取考试判断指南"""
    judge_system.show_exam_type_guide()
    
    return jsonify({
        "success": True,
        "message": "指南已在控制台输出"
    })


# 便捷的专用判断接口

@exam_judge_api.route('/placement', methods=['POST'])
def judge_placement():
    """摸底考试判断"""
    return judge_exam()


@exam_judge_api.route('/quiz', methods=['POST'])
def judge_quiz():
    """随机小测试判断"""
    return judge_exam()


@exam_judge_api.route('/post-lesson', methods=['POST'])
def judge_post_lesson():
    """课后测试判断"""
    return judge_exam()


@exam_judge_api.route('/midterm', methods=['POST'])
def judge_midterm():
    """期中考试判断"""
    return judge_exam()


@exam_judge_api.route('/final', methods=['POST'])
def judge_final():
    """期末考试判断"""
    return judge_exam()


@exam_judge_api.route('/promotion', methods=['POST'])
def judge_promotion():
    """升学考试判断"""
    return judge_exam()


@exam_judge_api.route('/retest', methods=['POST'])
def judge_retest():
    """补考判断"""
    return judge_exam()