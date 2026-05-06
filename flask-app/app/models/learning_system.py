#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新学习系统核心模型

import sqlite3
# JSON import removed - using database
from datetime import datetime, timedelta
from app.config import Config
from app.utils.logging import logger

class LearningSystemModel:
    """学习系统核心模型基类"""

    @staticmethod
    def _connect_db():
        """连接数据库"""
        return sqlite3.connect(Config.DATABASE_PATH)

    @staticmethod
        """创建表（子类实现）"""
        raise NotImplementedError("子类必须实现create_table方法")

    def save(self):
        """保存数据（子类实现）"""
        raise NotImplementedError("子类必须实现save方法")

    @staticmethod
        """通过ID获取数据（子类实现）"""
        raise NotImplementedError("子类必须实现get_by_id方法")

class Course(LearningSystemModel):
    """课程模型"""

    def __init__(self, course_id=None, title=None, description=None, language="japanese", level="beginner", category="日常对话",
                 cover_image=None, created_by=None, created_at=None, updated_at=None, is_active=1, is_public=1):
        self.course_id = course_id
        self.title = title
        self.description = description
        self.language = language
        self.level = level
        self.category = category
        self.cover_image = cover_image
        self.created_by = created_by
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = updated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.is_active = is_active
        self.is_public = is_public

    @staticmethod
        """创建课程表"""
        conn = LearningSystemModel._connect_db()
        cursor = conn.cursor()
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                language TEXT NOT NULL DEFAULT 'japanese',
                level TEXT NOT NULL DEFAULT 'beginner',
                category TEXT NOT NULL DEFAULT '日常对话',
                cover_image TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                is_public INTEGER DEFAULT 1,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("课程表创建成功")

    def save(self):
        """保存课程"""
        conn = LearningSystemModel._connect_db()
        cursor = conn.cursor()

            # 更新现有课程
            cursor.execute('''
                UPDATE courses SET title=?, description=?, language=?, level=?, category=?, cover_image=?,
                is_active=?, is_public=?, updated_at=CURRENT_TIMESTAMP WHERE id=?
            ''', (self.title, self.description, self.language, self.level, self.category, self.cover_image,
                 self.is_active, self.is_public, self.course_id))
            logger.info(f"更新课程: {self.title}")
        else:
            # 创建新课程
            cursor.execute('''
                INSERT INTO courses (title, description, language, level, category, cover_image, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.title, self.description, self.language, self.level, self.category, self.cover_image, self.created_by))
            self.course_id = cursor.lastrowid
            logger.info(f"创建课程: {self.title}")

        conn.commit()
        conn.close()
        return self.course_id

    @staticmethod
        """通过ID获取课程"""
        conn = LearningSystemModel._connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM courses WHERE id=?', (course_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return Course(
                course_id=row[0],
                title=row[1],
                description=row[2],
                language=row[3],
                level=row[4],
                category=row[5],
                cover_image=row[6],
                created_by=row[7],
                created_at=row[8],
                updated_at=row[9],
                is_active=row[10],
                is_public=row[11]
            )
        return None

    @staticmethod
        """获取所有课程"""
        conn = LearningSystemModel._connect_db()
        cursor = conn.cursor()
        rows = cursor.fetchall()
        conn.close()

        courses = []
        for row in rows:
            courses.append(Course(
                course_id=row[0],
                title=row[1],
                description=row[2],
                language=row[3],
                level=row[4],
                category=row[5],
                cover_image=row[6],
                created_by=row[7],
                created_at=row[8],
                is_active=row[10],
            ))

    """课程章节模型"""
    def __init__(self, lesson_id=None, course_id=None, title=None, description=None, order_index=0,
        self.lesson_id = lesson_id
        self.title = title
        self.order_index = order_index
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.is_active = is_active
        conn = LearningSystemModel._connect_db()
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                content TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("章节表创建成功")

        """保存章节"""
        conn = LearningSystemModel._connect_db()

            # 更新现有章节
            cursor.execute('''
                UPDATE lessons SET title=?, description=?, order_index=?, content=?,
                 self.is_active, self.lesson_id))
        else:
            cursor.execute('''
                INSERT INTO lessons (course_id, title, description, order_index, content)
            ''', (self.course_id, self.title, self.description, self.order_index, str(self.content)))
            self.lesson_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return self.lesson_id

    @staticmethod
        """通过ID获取章节"""
        conn = LearningSystemModel._connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM lessons WHERE id=?', (lesson_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return Lesson(
                lesson_id=row[0],
                course_id=row[1],
                title=row[2],
                description=row[3],
                order_index=row[4],
                content=eval(row[5]),
                created_at=row[6],
                updated_at=row[7],
                is_active=row[8]
            )
        return None

    @staticmethod
        """通过课程ID获取章节列表"""
        conn = LearningSystemModel._connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM lessons WHERE course_id=? AND is_active=1 ORDER BY order_index', (course_id,))
        rows = cursor.fetchall()
        conn.close()

        lessons = []
        for row in rows:
                lesson_id=row[0],
                course_id=row[1],
                title=row[2],
                order_index=row[4],
                content=eval(row[5]),
                created_at=row[6],
                updated_at=row[7],
                is_active=row[8]
            ))

class UserProgress(LearningSystemModel):
    """用户学习进度模型"""

    def __init__(self, progress_id=None, user_id=None, course_id=None, lesson_id=None,
                 progress_type="course", completed=0, score=None, last_accessed=None,
                 created_at=None, updated_at=None):
        self.progress_id = progress_id
        self.user_id = user_id
        self.course_id = course_id
        self.lesson_id = lesson_id
        self.progress_type = progress_type  # course, lesson, exercise
        self.completed = completed  # 0: 未开始, 1: 进行中, 2: 已完成
        self.score = score
        self.last_accessed = last_accessed or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = updated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        """创建用户进度表"""
        conn = LearningSystemModel._connect_db()
        cursor = conn.cursor()
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id INTEGER,
                lesson_id INTEGER,
                score REAL,
                last_accessed TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
            )
        ''')
        conn.close()

        """保存用户进度"""
        cursor = conn.cursor()
            cursor.execute('''
                updated_at=CURRENT_TIMESTAMP WHERE id=?
            logger.info(f"更新用户进度: 用户{self.user_id} - 课程{self.course_id}")
            cursor.execute('''
                VALUES (?, ?, ?, ?, ?)
            ''', (self.user_id, self.course_id, self.lesson_id, self.progress_type, self.completed))
            logger.info(f"创建用户进度: 用户{self.user_id} - 课程{self.course_id}")

        return self.progress_id

    @staticmethod
        """通过ID获取用户进度"""
        conn = LearningSystemModel._connect_db()
        cursor.execute('SELECT * FROM user_progress WHERE id=?', (progress_id,))
        row = cursor.fetchone()
        conn.close()

            return UserProgress(
                progress_id=row[0],
                user_id=row[1],
                course_id=row[2],
                lesson_id=row[3],
                progress_type=row[4],
                completed=row[5],
                score=row[6],
                last_accessed=row[7],
                created_at=row[8],
                updated_at=row[9]
            )
        return None

    @staticmethod
        """获取用户进度"""
        conn = LearningSystemModel._connect_db()
        cursor = conn.cursor()

        if course_id and lesson_id:
            cursor.execute('SELECT * FROM user_progress WHERE user_id=? AND course_id=? AND lesson_id=?',
                          (user_id, course_id, lesson_id))
        elif course_id:
            cursor.execute('SELECT * FROM user_progress WHERE user_id=? AND course_id=?', (user_id, course_id))
        else:
            cursor.execute('SELECT * FROM user_progress WHERE user_id=?', (user_id,))

        rows = cursor.fetchall()
        conn.close()

        progress_list = []
        for row in rows:
            progress_list.append(UserProgress(
                progress_id=row[0],
                user_id=row[1],
                course_id=row[2],
                lesson_id=row[3],
                completed=row[5],
                score=row[6],
                last_accessed=row[7],
                created_at=row[8],
        return progress_list

    """学习分析模型"""

    def __init__(self, analytics_id=None, user_id=None, metric_name=None, metric_value=None,
                 metric_type="gauge", category="learning", timestamp=None):
        self.analytics_id = analytics_id
        self.user_id = user_id
        self.metric_name = metric_name
        self.metric_value = metric_value
        self.metric_type = metric_type  # gauge, counter, histogram
        self.category = category  # learning, performance, engagement
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
        """创建学习分析表"""
        conn = LearningSystemModel._connect_db()
        cursor = conn.cursor()
            CREATE TABLE IF NOT EXISTS learning_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_type TEXT NOT NULL DEFAULT 'gauge',
                category TEXT NOT NULL DEFAULT 'learning',
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("学习分析表创建成功")

    def save(self):
        """保存学习分析数据"""
        conn = LearningSystemModel._connect_db()
        cursor = conn.cursor()

        # 插入新的分析数据
        cursor.execute('''
            INSERT INTO learning_analytics (user_id, metric_name, metric_value, metric_type, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.user_id, self.metric_name, self.metric_value, self.metric_type, self.category))
        self.analytics_id = cursor.lastrowid

        conn.commit()
        conn.close()

        """通过ID获取学习分析数据"""
        cursor.execute('SELECT * FROM learning_analytics WHERE id=?', (analytics_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return LearningAnalytics(
                analytics_id=row[0],
                user_id=row[1],
                metric_name=row[2],
                metric_value=row[3],
                metric_type=row[4],
                category=row[5],
                timestamp=row[6]

    @staticmethod
        conn = LearningSystemModel._connect_db()
        query = 'SELECT * FROM learning_analytics WHERE user_id=?'

            query += ' AND metric_name=?'

            query += ' AND timestamp >= ?'

            query += ' AND timestamp <= ?'
            params.append(end_time)
        cursor.execute(query, params)
        conn.close()

        analytics_list = []
        for row in rows:
            analytics_list.append(LearningAnalytics(
                analytics_id=row[0],
                user_id=row[1],
                metric_name=row[2],
                metric_value=row[3],
                metric_type=row[4],
                category=row[5],
                timestamp=row[6]
            ))

class LearningSystem:
    @staticmethod
        """初始化所有学习系统表"""
        Course.create_table()
        Lesson.create_table()
        UserProgress.create_table()
        LearningAnalytics.create_table()
        # 初始化考试结果表
        from app.models.learning_system import ExamSystemManager
        conn = LearningSystemModel._connect_db()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id TEXT UNIQUE NOT NULL,
                exam_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                correct_answers INTEGER NOT NULL,
                wrong_answers INTEGER NOT NULL,
                skipped_questions INTEGER NOT NULL,
                completion_time INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                submitted_at TEXT NOT NULL,
                answers TEXT NOT NULL,
                wrong_question_ids TEXT NOT NULL,
                performance_analysis TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        # 初始化错题归档表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS archived_wrong_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                archived_at TEXT DEFAULT CURRENT_TIMESTAMP,
                reason TEXT DEFAULT '已掌握',
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, question_id)
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("学习系统表初始化完成")
    @staticmethod
        conn = LearningSystemModel._connect_db()
        cursor = conn.cursor()

        # 统计已完成课程
        cursor.execute('''
            SELECT COUNT(*) FROM user_progress
            WHERE user_id=? AND progress_type='course' AND completed=2
        completed_courses = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM user_progress
            WHERE user_id=? AND progress_type='lesson' AND completed=2
        ''', (user_id,))
        completed_lessons = cursor.fetchone()[0]


        # 统计平均分数（包括考试分数）
        cursor.execute('''
            SELECT AVG(score) FROM (
                SELECT score FROM user_progress WHERE user_id=? AND score IS NOT NULL
                UNION ALL
            )
        ''', (user_id, user_id))
        avg_score = cursor.fetchone()[0] or 0

        # 统计考试次数
            SELECT COUNT(*) FROM exam_results WHERE user_id=?
        ''', (user_id,))

        conn.close()
        return {
            "completed_courses": completed_courses,
            "completed_lessons": completed_lessons,
            "total_learning_time": total_learning_time,
            "average_score": round(avg_score, 2),
            "total_exams": total_exams
        }
    @staticmethod
        # 这里可以实现基于用户历史和兴趣的推荐算法
        # 目前简单实现：推荐未学习的热门课程
        conn = LearningSystemModel._connect_db()
        cursor = conn.cursor()

        # 获取用户已学习的课程ID
        cursor.execute('''
        ''', (user_id,))
        learned_course_ids = [row[0] for row in cursor.fetchall()]
        # 构建查询条件
            query = f'''SELECT * FROM courses
                      AND is_active=1 AND is_public=1
                      ORDER BY RANDOM() LIMIT ?'''
        else:
            query = '''SELECT * FROM courses
                      WHERE is_active=1 AND is_public=1
                      ORDER BY RANDOM() LIMIT ?'''
            params = [limit]

        rows = cursor.fetchall()

        courses = []
        for row in rows:
            courses.append({
                "course_id": row[0],
                "title": row[1],
                "description": row[2],
                "language": row[3],
                "level": row[4],
                "category": row[5],
                "cover_image": row[6]
            })

        return courses

    @staticmethod
        """根据考试结果更新用户进度"""
        根据考试结果更新用户学习进度
        Args:
            user_id: 用户ID
            exam_result: 考试结果数据

        Returns:
            是否更新成功
        try:
            # 获取考试科目和分数
            subject = exam_result.get("subject", "general")
            score = exam_result.get("score", 0)

            # 保存考试结果到学习分析
            analytics = LearningAnalytics(
                user_id=user_id,
                metric_name="exam_score",
                metric_value=score,
                metric_type="gauge",
                category="exam"
            )
            analytics.save()

            # 更新用户的总体学习进度
            # 这里可以根据考试结果更新用户的学习水平、薄弱点等
            conn = LearningSystemModel._connect_db()
            cursor = conn.cursor()

            # 检查是否有用户学习水平记录
            cursor.execute('''
                SELECT * FROM user_learning_levels WHERE user_id=? AND subject=?
            ''', (user_id, subject))
            level_record = cursor.fetchone()

            # 确定新的学习水平
            new_level = "beginner"
            if score >= 85:
                new_level = "advanced"
            elif score >= 70:
                new_level = "intermediate"

            if level_record:
                # 更新现有记录
                cursor.execute('''
                    UPDATE user_learning_levels SET level=?, updated_at=CURRENT_TIMESTAMP
                    WHERE user_id=? AND subject=?
                ''', (new_level, user_id, subject))
                # 创建新记录
                cursor.execute('''
                    INSERT INTO user_learning_levels (user_id, subject, level, created_at, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (user_id, subject, new_level))

            conn.commit()
            conn.close()

            logger.info(f"成功更新用户 {user_id} 的学习进度")
            return True
        except Exception as e:
            logger.error(f"更新用户学习进度失败: {str(e)}")
            return False

    @staticmethod
    def get_user_exam_based_recommendations(user_id, limit=5):
        基于考试结果的学习推荐
            user_id: 用户ID
            limit: 推荐数量

            推荐的学习资源列表
        logger.info(f"获取用户 {user_id} 基于考试结果的学习推荐")

            conn = LearningSystemModel._connect_db()

            # 1. 获取用户薄弱知识点（从最近的考试结果中）
            cursor.execute('''
                SELECT wrong_question_ids, performance_analysis FROM exam_results
                WHERE user_id=? ORDER BY submitted_at DESC LIMIT 3
            ''', (user_id,))

            exam_results = cursor.fetchall()

            # 收集薄弱知识点
            weak_knowledge_points = []
            for result in exam_results:
                # 解析错题ID和性能分析
                wrong_question_ids = eval(result[0])
                performance_analysis = eval(result[1])

                # 从性能分析中获取薄弱知识点
                    weak_knowledge_points.extend(performance_analysis["weak_knowledge_points"])

            # 统计知识点出现频率
            from collections import Counter
            kp_counter = Counter(weak_knowledge_points)
            top_weak_kp = [kp for kp, count in kp_counter.most_common(3)]

            # 2. 基于薄弱知识点推荐课程
            recommendations = []

            if top_weak_kp:
                # 根据薄弱知识点推荐相关课程
                for kp in top_weak_kp:
                    cursor.execute('''
                        SELECT * FROM courses
                        WHERE category LIKE ? AND is_active=1 AND is_public=1
                    ''', (f"%{kp}%", limit // len(top_weak_kp) + 1))

                    course_rows = cursor.fetchall()
                    for row in course_rows:
                        recommendations.append({
                            "type": "course",
                            "id": row[0],
                            "title": row[1],
                            "description": row[2],
                            "language": row[3],
                            "level": row[4],
                            "category": row[5],
                            "cover_image": row[6],
                            "reason": f"针对薄弱知识点: {kp}"
                        })
            else:
                # 如果没有薄弱知识点，推荐一般课程
                recommendations = LearningSystem.recommend_courses(user_id, limit)

            conn.close()

            # 去重并限制数量
            seen_ids = set()
            unique_recommendations = []
            for rec in recommendations:
                rec_id = rec.get("id")
                if rec_id not in seen_ids:
                    seen_ids.add(rec_id)
                    unique_recommendations.append(rec)
                if len(unique_recommendations) >= limit:
                    break

            logger.info(f"成功获取用户 {user_id} 基于考试结果的学习推荐")
            return unique_recommendations
        except Exception as e:
            logger.error(f"获取基于考试结果的推荐失败: {str(e)}")
            # 返回默认推荐
            return LearningSystem.recommend_courses(user_id, limit)

    @staticmethod
    def get_user_weakness_from_exams(user_id, subject=None, limit=5):
        从考试中获取用户的薄弱点

        Args:
            subject: 科目（可选）
            limit: 限制数量

        Returns:
            用户薄弱点列表
        logger.info(f"获取用户 {user_id} 从考试中的薄弱点")

        try:
            conn = LearningSystemModel._connect_db()
            cursor = conn.cursor()

            # 构建查询
            query = '''
                SELECT wrong_question_ids, performance_analysis FROM exam_results
                WHERE user_id=?
            '''
            params = [user_id]

            if subject:
                query += ' AND subject=?'
                params.append(subject)

            query += ' ORDER BY submitted_at DESC LIMIT 5'

            cursor.execute(query, params)
            exam_results = cursor.fetchall()

            # 收集薄弱知识点
            weak_knowledge_points = []
            wrong_question_details = []

            for result in exam_results:
                wrong_question_ids = eval(result[0])
                performance_analysis = eval(result[1])

                # 从性能分析中获取薄弱知识点
                if "weak_knowledge_points" in performance_analysis:
                    weak_knowledge_points.extend(performance_analysis["weak_knowledge_points"])

                # 获取错题详情
                for q_id in wrong_question_ids[:limit]:
                    cursor.execute('''
                        SELECT content, question_type, options, answer, explanation FROM questions WHERE id=?
                    ''', (q_id,))
                    question = cursor.fetchone()
                    if question:
                        wrong_question_details.append({
                            "question_id": q_id,
                            "content": question[0],
                            "question_type": question[1],
                            "options": eval(question[2]) if question[2] else [],
                            "correct_answer": question[3],
                            "explanation": question[4]
                        })

            conn.close()

            # 统计知识点出现频率
            from collections import Counter
            kp_counter = Counter(weak_knowledge_points)
            top_weakness = [{
                "knowledge_point": kp,
                "frequency": count
            } for kp, count in kp_counter.most_common(limit)]

            return {
                "weak_knowledge_points": top_weakness,
                "wrong_questions": wrong_question_details
            }
        except Exception as e:
            logger.error(f"获取用户薄弱点失败: {str(e)}")
            return {
                "weak_knowledge_points": [],
                "wrong_questions": []
            }

    @staticmethod
    def generate_personalized_learning_plan(user_id, days=7):
        生成个性化学习计划

        Args:
            user_id: 用户ID
            days: 计划天数
        Returns:
            个性化学习计划
        logger.info(f"为用户 {user_id} 生成个性化学习计划")

        try:
            # 1. 获取用户学习数据和薄弱点
            learning_summary = LearningSystem.get_user_learning_summary(user_id)
            weaknesses = LearningSystem.get_user_weakness_from_exams(user_id, limit=3)
            recommended_courses = LearningSystem.recommend_courses(user_id, limit=2)

            # 2. 生成学习计划
            plan = {
                "user_id": user_id,
                "days": days,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "goals": [],
                "daily_plans": [],
                "recommended_resources": recommended_courses
            }

            # 3. 设置学习目标
            if learning_summary["average_score"] < 70:
                plan["goals"].append({
                    "description": "提高平均分数到75分以上",
                    "current": learning_summary["average_score"]

                plan["goals"].append({
                    "description": f"改善薄弱知识点: {', '.join([w['knowledge_point'] for w in weaknesses['weak_knowledge_points']])}",
                    "target": "掌握所有薄弱知识点",
                    "current": f"存在 {len(weaknesses['weak_knowledge_points'])} 个薄弱知识点"
                })

            # 4. 生成每日计划
            daily_plan_templates = [
                {
                    "day": 1,
                    "focus": "薄弱知识点复习",
                    "activities": [
                        "复习薄弱知识点的相关课程",
                        "完成5道相关练习题",
                        "总结学习笔记"
                    ]
                },
                {
                    "day": 2,
                    "focus": "综合练习",
                    "activities": [
                        "完成10道综合练习题",
                        "查看错题解析",
                        "巩固薄弱知识点"
                    ]
                },
                {
                    "day": 3,
                    "focus": "新知识学习",
                    "activities": [
                        "学习推荐课程的新章节",
                        "完成相关练习",
                        "总结新知识点"
                    ]
                }
            ]

            # 循环生成每日计划
            for i in range(days):
                template = daily_plan_templates[i % len(daily_plan_templates)]
                daily_plan = {
                    "day": i + 1,
                    "focus": template["focus"],
                    "activities": template["activities"],
                    "recommended_courses": [course for j, course in enumerate(recommended_courses) if j == i % len(recommended_courses)]
                }
                plan["daily_plans"].append(daily_plan)

            logger.info(f"成功为用户 {user_id} 生成个性化学习计划")
            return plan
            logger.error(f"生成个性化学习计划失败: {str(e)}")
            return {
                "user_id": user_id,
                "days": days,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "goals": [],
                "daily_plans": [],
                "recommended_resources": []
            }

    @staticmethod
    def recommend_practice_questions(user_id, subject=None, difficulty=None, limit=10):
        推荐练习题给用户

            user_id: 用户ID
            difficulty: 难度（可选）
            limit: 推荐数量
        Returns:
            推荐的练习题列表
        logger.info(f"为用户 {user_id} 推荐练习题")
        try:
            conn = LearningSystemModel._connect_db()

            weaknesses = LearningSystem.get_user_weakness_from_exams(user_id, subject=subject, limit=3)

            # 2. 构建查询
            if weak_knowledge_points:
                # 基于薄弱知识点推荐相关题目
                query = '''
                    SELECT id, content, question_type, options, answer, explanation, difficulty
                    FROM questions
                    WHERE category IN ({})
                '''.format(','.join(['?'] * len(weak_knowledge_points)))
                params = weak_knowledge_points

                if difficulty:
                    query += ' AND difficulty=?'
                    params.append(difficulty)

                params.append(limit)
            else:
                # 随机推荐题目
                    SELECT id, content, question_type, options, answer, explanation, difficulty
                '''

                    params.append(difficulty)
                query += ' ORDER BY RANDOM() LIMIT ?'
                params.append(limit)

            cursor.execute(query, params)
            questions = cursor.fetchall()
            conn.close()

            # 3. 格式化结果
            recommended_questions = []
            for q in questions:
                recommended_questions.append({
                    "question_id": q[0],
                    "content": q[1],
                    "question_type": q[2],
                    "options": eval(q[3]) if q[3] else [],
                    "answer": q[4],
                    "explanation": q[5],
                    "difficulty": q[6]
                })

            logger.info(f"成功为用户 {user_id} 推荐 {len(recommended_questions)} 道练习题")
            return recommended_questions
        except Exception as e:
            logger.error(f"推荐练习题失败: {str(e)}")
            return []

    @staticmethod
        获取用户的语言等级

        Args:
            user_id: 用户ID
            language: 语言类型 (japanese, english)

        Returns:
            用户的语言等级，如果不存在返回None
        logger.info(f"获取用户 {user_id} 的 {language} 语言等级")
        try:
            conn = LearningSystemModel._connect_db()
            cursor = conn.cursor()

            # 构建科目名称
            subject = f"{language}_level"

            # 查询用户语言等级
            cursor.execute('''
                SELECT level FROM user_learning_levels WHERE user_id=? AND subject=?
            ''', (user_id, subject))

            result = cursor.fetchone()
            conn.close()

            if result:
                logger.info(f"用户 {user_id} 的 {language} 语言等级为: {result[0]}")
                return result[0]
            else:
                logger.info(f"用户 {user_id} 暂无 {language} 语言等级记录")
                return None
            logger.error(f"获取用户语言等级失败: {str(e)}")
            return None

    @staticmethod
    def analyze_learning_patterns(user_id, days=30):
        分析用户学习模式

        Args:
            user_id: 用户ID
            days: 分析天数

        Returns:
            学习模式分析结果
        logger.info(f"分析用户 {user_id} 的学习模式")

            cursor = conn.cursor()

            # 1. 计算时间范围
            start_date = end_date - timedelta(days=days)
            start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute('''
                SELECT progress_type, completed, score, last_accessed
                WHERE user_id=? AND last_accessed >= ?
                ORDER BY last_accessed
            # 3. 分析学习模式
                "user_id": user_id,
                "total_activities": len(progress_records),
                "completed_activities": 0,
                "average_score": 0,
                "learning_frequency": {
                    "daily": {},
                "time_of_day_preference": {
                    "afternoon": 0,
                    "evening": 0
                },
                "activity_types": {}
            }

            # 4. 统计数据
            scores = []
            for record in progress_records:
                progress_type, completed, score, last_accessed = record

                # 统计已完成活动
                    pattern_analysis["completed_activities"] += 1
                # 统计分数
                    scores.append(score)
                if progress_type not in pattern_analysis["activity_types"]:
                pattern_analysis["activity_types"][progress_type] += 1

                # 统计学习时间偏好
                access_time = datetime.strptime(last_accessed, "%Y-%m-%d %H:%M:%S")
                hour = access_time.hour
                if 6 <= hour < 12:
                    pattern_analysis["time_of_day_preference"]["morning"] += 1
                elif 12 <= hour < 18:
                    pattern_analysis["time_of_day_preference"]["afternoon"] += 1
                else:
                    pattern_analysis["time_of_day_preference"]["evening"] += 1

                # 统计每日和每周学习频率
                date_str = access_time.strftime("%Y-%m-%d")
                if date_str not in pattern_analysis["learning_frequency"]["daily"]:
                    pattern_analysis["learning_frequency"]["daily"][date_str] = 0
                pattern_analysis["learning_frequency"]["daily"][date_str] += 1

                week_str = f"Week {access_time.isocalendar()[1]}"
                if week_str not in pattern_analysis["learning_frequency"]["weekly"]:
                    pattern_analysis["learning_frequency"]["weekly"][week_str] = 0
                pattern_analysis["learning_frequency"]["weekly"][week_str] += 1

            # 5. 计算平均分数
            if scores:
                pattern_analysis["average_score"] = round(sum(scores) / len(scores), 2)

            conn.close()

            logger.info(f"成功分析用户 {user_id} 的学习模式")
            return pattern_analysis
        except Exception as e:
            logger.error(f"分析学习模式失败: {str(e)}")
            return {
                "analysis_period": days,
                "total_activities": 0,
                "average_score": 0,
                "learning_frequency": {
                    "daily": {},
                    "weekly": {}
                },
                "time_of_day_preference": {
                    "morning": 0,
                    "afternoon": 0,
                    "evening": 0
                },
                "activity_types": {}
            }

    @staticmethod
    def archive_wrong_question(user_id, question_id, reason="已掌握"):
        归档错题

        Args:
            user_id: 用户ID
            question_id: 题目ID

            是否归档成功
        logger.info(f"归档用户 {user_id} 的错题: {question_id}")

        try:

            # 检查是否已经归档
                SELECT * FROM archived_wrong_questions WHERE user_id=? AND question_id=?
            ''', (user_id, question_id))
            if cursor.fetchone():
                conn.close()
                return True

            # 归档错题
            cursor.execute('''
                INSERT INTO archived_wrong_questions (user_id, question_id, reason)
                VALUES (?, ?, ?)
            ''', (user_id, question_id, reason))

            conn.commit()
            conn.close()

            logger.info(f"成功归档用户 {user_id} 的错题: {question_id}")
            return True
        except Exception as e:
            logger.error(f"归档错题失败: {str(e)}")
            return False

    def is_question_archived(user_id, question_id):
        检查题目是否已归档

        Args:
            user_id: 用户ID
            question_id: 题目ID

        Returns:
            是否已归档
        try:
            conn = LearningSystemModel._connect_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM archived_wrong_questions WHERE user_id=? AND question_id=?
            ''', (user_id, question_id))
            result = cursor.fetchone()
            conn.close()

            return result is not None
        except Exception as e:
            logger.error(f"检查题目归档状态失败: {str(e)}")
            return False

    @staticmethod
    def get_archived_wrong_questions(user_id, limit=100):
        获取已归档的错题

        Args:
            user_id: 用户ID
            limit: 限制数量

        Returns:
            已归档的错题列表
        logger.info(f"获取用户 {user_id} 的已归档错题")

        try:
            conn = LearningSystemModel._connect_db()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT question_id, archived_at, reason FROM archived_wrong_questions
                WHERE user_id=? ORDER BY archived_at DESC LIMIT ?

            archived_questions = cursor.fetchall()
            conn.close()

            result = []
            for row in archived_questions:
                result.append({
                    "question_id": row[0],
                    "reason": row[2]
                })

            logger.info(f"成功获取用户 {user_id} 的已归档错题，数量: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取已归档错题失败: {str(e)}")
            return []

    def unarchive_wrong_question(user_id, question_id):
        从归档中恢复错题

        Args:
            user_id: 用户ID
            question_id: 题目ID

        Returns:
            是否恢复成功
        logger.info(f"从归档中恢复用户 {user_id} 的错题: {question_id}")

        try:
            conn = LearningSystemModel._connect_db()
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM archived_wrong_questions WHERE user_id=? AND question_id=?
            ''', (user_id, question_id))

            affected_rows = cursor.rowcount
            conn.close()
            if affected_rows > 0:
                logger.info(f"成功从归档中恢复用户 {user_id} 的错题: {question_id}")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"从归档中恢复错题失败: {str(e)}")
            return False

    @staticmethod
    def get_unarchived_wrong_questions(user_id, subject=None, limit=10):
        获取未归档的错题

        Args:
            subject: 科目（可选）
            limit: 限制数量

        Returns:
            未归档的错题列表
        logger.info(f"获取用户 {user_id} 的未归档错题")

        try:
            conn = LearningSystemModel._connect_db()
            cursor = conn.cursor()

            # 构建查询
            query = '''
                SELECT DISTINCT wrong_question_ids FROM exam_results
                WHERE user_id=?
            '''
            params = [user_id]
            if subject:
                query += ' AND subject=?'

            query += ' ORDER BY submitted_at DESC LIMIT 5'

            cursor.execute(query, params)
            exam_results = cursor.fetchall()

            # 收集所有错题ID
            all_wrong_question_ids = set()
            for result in exam_results:
                wrong_question_ids = eval(result[0])

            # 获取已归档的错题ID
            cursor.execute('''
                SELECT question_id FROM archived_wrong_questions WHERE user_id=?
            ''', (user_id,))
            archived_question_ids = set([row[0] for row in cursor.fetchall()])

            # 计算未归档的错题ID
            unarchived_question_ids = list(all_wrong_question_ids - archived_question_ids)

            # 限制数量
            if len(unarchived_question_ids) > limit:
                unarchived_question_ids = unarchived_question_ids[:limit]

            # 获取错题详情
            unarchived_questions = []
            for q_id in unarchived_question_ids:
                cursor.execute('''
                    SELECT id, content, question_type, options, answer, explanation FROM questions WHERE id=?
                ''', (q_id,))
                question = cursor.fetchone()
                if question:
                        "question_id": q_id,
                        "content": question[1],
                        "options": eval(question[3]) if question[3] else [],
                        "explanation": question[5]


            return unarchived_questions
            logger.error(f"获取未归档错题失败: {str(e)}")
