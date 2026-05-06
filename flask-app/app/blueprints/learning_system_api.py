#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习系统API蓝图

from flask import Blueprint, request, jsonify
from app.models.learning_system import Course, Lesson, UserProgress, LearningSystem, LearningAnalytics
from app.utils.logging import logger

# 创建学习系统API蓝图
learning_system_api = Blueprint('learning_system_api', __name__, url_prefix='/api/learning')

@learning_system_api.route('/initialize', methods=['POST'])
def initialize_learning_system():
    """初始化学习系统"""
    try:
        LearningSystem.initialize_tables()
        return jsonify({"success": True, "message": "学习系统初始化成功"}), 200
    except Exception as e:
        logger.error(f"学习系统初始化失败: {str(e)}")
        return jsonify({"success": False, "message": f"学习系统初始化失败: {str(e)}"}), 500

@learning_system_api.route('/courses', methods=['GET'])
def get_courses():
    """获取所有课程"""
    try:
        result = []
        for course in courses:
            result.append({
                "course_id": course.course_id,
                "title": course.title,
                "description": course.description,
                "language": course.language,
                "level": course.level,
                "category": course.category,
                "cover_image": course.cover_image,
                "created_by": course.created_by,
                "created_at": course.created_at,
                "updated_at": course.updated_at,
                "is_active": course.is_active,
                "is_public": course.is_public
            })
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        logger.error(f"获取课程列表失败: {str(e)}")
        return jsonify({"success": False, "message": f"获取课程列表失败: {str(e)}"}), 500

@learning_system_api.route('/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """获取单个课程"""
    try:
        if not course:
            return jsonify({"success": False, "message": "课程不存在"}), 404

        result = {
            "course_id": course.course_id,
            "title": course.title,
            "description": course.description,
            "level": course.level,
            "cover_image": course.cover_image,
            "created_at": course.created_at,
            "is_active": course.is_active,
        }
    except Exception as e:
        return jsonify({"success": False, "message": f"获取课程详情失败: {str(e)}"}), 500
@learning_system_api.route('/courses', methods=['POST'])
    """创建课程"""
        if not data:

        if not data.get('title'):
            return jsonify({"success": False, "message": "课程标题不能为空"}), 400

        # 创建课程
        course = Course(
            title=data.get('title'),
            description=data.get('description'),
            language=data.get('language', 'japanese'),
            level=data.get('level', 'beginner'),
            category=data.get('category', '日常对话'),
            cover_image=data.get('cover_image'),
            created_by=data.get('created_by')
        )

        course_id = course.save()
        return jsonify({"success": True, "message": "课程创建成功", "course_id": course_id}), 201
    except Exception as e:
        logger.error(f"创建课程失败: {str(e)}")
        return jsonify({"success": False, "message": f"创建课程失败: {str(e)}"}), 500

@learning_system_api.route('/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    """更新课程"""
    try:
        if not data:
            return jsonify({"success": False, "message": "请求数据为空"}), 400

        # 获取课程
        course = Course.get_by_id(course_id)
        if not course:
            return jsonify({"success": False, "message": "课程不存在"}), 404

        # 更新课程信息
        if 'title' in data:
            course.title = data['title']
        if 'description' in data:
            course.description = data['description']
        if 'language' in data:
            course.language = data['language']
        if 'level' in data:
        if 'category' in data:
        if 'cover_image' in data:
            course.is_active = data['is_active']
            course.is_public = data['is_public']
        course.save()
        return jsonify({"success": True, "message": "课程更新成功"}), 200
    except Exception as e:
        logger.error(f"更新课程失败: {str(e)}")
        return jsonify({"success": False, "message": f"更新课程失败: {str(e)}"}), 500

@learning_system_api.route('/courses/<int:course_id>/lessons', methods=['GET'])
def get_course_lessons(course_id):
    """获取课程的所有章节"""
    try:
        result = []
        for lesson in lessons:
            result.append({
                "lesson_id": lesson.lesson_id,
                "course_id": lesson.course_id,
                "title": lesson.title,
                "description": lesson.description,
                "order_index": lesson.order_index,
                "content": lesson.content,
                "created_at": lesson.created_at,
                "updated_at": lesson.updated_at,
                "is_active": lesson.is_active
            })
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        logger.error(f"获取课程章节失败: {str(e)}")
        return jsonify({"success": False, "message": f"获取课程章节失败: {str(e)}"}), 500

@learning_system_api.route('/lessons/<int:lesson_id>', methods=['GET'])
def get_lesson(lesson_id):
    """获取单个章节"""
    try:
        if not lesson:
            return jsonify({"success": False, "message": "章节不存在"}), 404

        result = {
            "lesson_id": lesson.lesson_id,
            "course_id": lesson.course_id,
            "title": lesson.title,
            "description": lesson.description,
            "order_index": lesson.order_index,
            "content": lesson.content,
            "created_at": lesson.created_at,
            "updated_at": lesson.updated_at,
            "is_active": lesson.is_active
        }
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        logger.error(f"获取章节详情失败: {str(e)}")
        return jsonify({"success": False, "message": f"获取章节详情失败: {str(e)}"}), 500

@learning_system_api.route('/lessons', methods=['POST'])
def create_lesson():
    """创建章节"""
    try:
        if not data:
            return jsonify({"success": False, "message": "请求数据为空"}), 400
        # 验证必填字段
        if not data.get('course_id') or not data.get('title'):
            return jsonify({"success": False, "message": "课程ID和章节标题不能为空"}), 400

        lesson = Lesson(
            title=data['title'],
            order_index=data.get('order_index', 0),

        return jsonify({"success": True, "message": "章节创建成功", "lesson_id": lesson_id}), 201
        logger.error(f"创建章节失败: {str(e)}")

def update_lesson(lesson_id):
        if not data:

        # 获取章节
        if not lesson:
            return jsonify({"success": False, "message": "章节不存在"}), 404

        # 更新章节信息
        if 'title' in data:
            lesson.title = data['title']
        if 'description' in data:
            lesson.description = data['description']
        if 'order_index' in data:
            lesson.order_index = data['order_index']
        if 'content' in data:
        if 'is_active' in data:
            lesson.is_active = data['is_active']

        lesson.save()
        return jsonify({"success": True, "message": "章节更新成功"}), 200
    except Exception as e:
        logger.error(f"更新章节失败: {str(e)}")
        return jsonify({"success": False, "message": f"更新章节失败: {str(e)}"}), 500
@learning_system_api.route('/user/<int:user_id>/progress', methods=['GET'])
def get_user_progress(user_id):
    """获取用户学习进度"""
        lesson_id = request.args.get('lesson_id', type=int)

        progress = UserProgress.get_user_progress(user_id, course_id, lesson_id)
        for p in progress:
            result.append({
                "progress_id": p.progress_id,
                "user_id": p.user_id,
                "course_id": p.course_id,
                "lesson_id": p.lesson_id,
                "progress_type": p.progress_type,
                "completed": p.completed,
                "score": p.score,
                "last_accessed": p.last_accessed,
                "created_at": p.created_at,
            })
        return jsonify({"success": True, "data": result}), 200
        logger.error(f"获取用户学习进度失败: {str(e)}")
        return jsonify({"success": False, "message": f"获取用户学习进度失败: {str(e)}"}), 500
@learning_system_api.route('/user/progress', methods=['POST'])
    """更新用户学习进度"""
            return jsonify({"success": False, "message": "请求数据为空"}), 400

        # 验证必填字段
        if not data.get('user_id'):
            return jsonify({"success": False, "message": "用户ID不能为空"}), 400

        # 创建或更新进度
        progress = UserProgress(
            user_id=data['user_id'],
            course_id=data.get('course_id'),
            lesson_id=data.get('lesson_id'),
            progress_type=data.get('progress_type', 'course'),
            completed=data.get('completed', 0),
            score=data.get('score')
        )

        progress_id = progress.save()
        return jsonify({"success": True, "message": "学习进度更新成功", "progress_id": progress_id}), 200
    except Exception as e:
        logger.error(f"更新用户学习进度失败: {str(e)}")
        return jsonify({"success": False, "message": f"更新用户学习进度失败: {str(e)}"}), 500

@learning_system_api.route('/user/<int:user_id>/summary', methods=['GET'])
def get_user_learning_summary(user_id):
    """获取用户学习摘要"""
    try:
    except Exception as e:
        logger.error(f"获取用户学习摘要失败: {str(e)}")
        return jsonify({"success": False, "message": f"获取用户学习摘要失败: {str(e)}"}), 500

def get_course_recommendations(user_id):
    """获取课程推荐"""
    try:
        recommendations = LearningSystem.recommend_courses(user_id, limit)
    except Exception as e:
        logger.error(f"获取课程推荐失败: {str(e)}")
        return jsonify({"success": False, "message": f"获取课程推荐失败: {str(e)}"}), 500

@learning_system_api.route('/analytics', methods=['POST'])
def add_analytics():
    """添加学习分析数据"""
    try:
        if not data:
            return jsonify({"success": False, "message": "请求数据为空"}), 400

        # 验证必填字段
        if not data.get('user_id') or not data.get('metric_name') or 'metric_value' not in data:
            return jsonify({"success": False, "message": "用户ID、指标名称和指标值不能为空"}), 400

        # 创建分析数据
        analytics = LearningAnalytics(
            user_id=data['user_id'],
            metric_name=data['metric_name'],
            metric_value=data['metric_value'],
            metric_type=data.get('metric_type', 'gauge'),
            category=data.get('category', 'learning')
        )

        analytics_id = analytics.save()
        return jsonify({"success": True, "message": "学习分析数据添加成功", "analytics_id": analytics_id}), 201
    except Exception as e:
        logger.error(f"添加学习分析数据失败: {str(e)}")
        return jsonify({"success": False, "message": f"添加学习分析数据失败: {str(e)}"}), 500

@learning_system_api.route('/user/<int:user_id>/analytics', methods=['GET'])
def get_user_analytics(user_id):
    """获取用户学习分析数据"""
    try:
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

        analytics = LearningAnalytics.get_user_analytics(user_id, metric_name, start_time, end_time)
        for a in analytics:
            result.append({
                "analytics_id": a.analytics_id,
                "user_id": a.user_id,
                "metric_name": a.metric_name,
                "metric_type": a.metric_type,
                "category": a.category,
                "timestamp": a.timestamp
            })
        return jsonify({"success": True, "data": result}), 200
        logger.error(f"获取用户学习分析数据失败: {str(e)}")
        return jsonify({"success": False, "message": f"获取用户学习分析数据失败: {str(e)}"}), 500
