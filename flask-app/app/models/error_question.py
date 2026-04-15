#!/usr/bin/env python3
"""
错题管理模型
"""

import time
from typing import Dict, List, Any, Optional

from app.utils.db import db_manager
from app.utils.logging import logger
from app.utils.table_encryption import table_encryption

class ErrorQuestionManager:
    """错题管理器"""
    
    def __init__(self):
        """初始化错题管理器"""
        self._create_tables()
    
    def _create_tables(self):
        """创建必要的表"""
        try:
            # 获取加密后的表名
            error_questions_table = table_encryption.encrypt_table_name('error_questions')
            error_tags_table = table_encryption.encrypt_table_name('error_tags')
            error_question_tags_table = table_encryption.encrypt_table_name('error_question_tags')
            review_plans_table = table_encryption.encrypt_table_name('review_plans')
            teacher_ai_transfer_table = table_encryption.encrypt_table_name('teacher_ai_transfer')
            error_statistics_table = table_encryption.encrypt_table_name('error_statistics')
            user_table = table_encryption.encrypt_table_name('user')
            questions_table = table_encryption.encrypt_table_name('questions')
            exam_records_table = table_encryption.encrypt_table_name('exam_records')
            
            # 创建错题表
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {error_questions_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    exam_record_id INTEGER NOT NULL,
                    user_answer TEXT,
                    correct_answer TEXT,
                    error_reason TEXT,
                    error_type TEXT,
                    knowledge_point TEXT,
                    difficulty_level INTEGER,
                    mastery_level INTEGER DEFAULT 0,
                    review_count INTEGER DEFAULT 0,
                    last_review_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id),
                    FOREIGN KEY (question_id) REFERENCES {questions_table}(id),
                    FOREIGN KEY (exam_record_id) REFERENCES {exam_records_table}(id)
                )
            ''')
            
            # 创建错题标签表
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {error_tags_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建错题-标签关联表
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {error_question_tags_table} (
                    error_question_id INTEGER,
                    tag_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (error_question_id, tag_id),
                    FOREIGN KEY (error_question_id) REFERENCES {error_questions_table}(id),
                    FOREIGN KEY (tag_id) REFERENCES {error_tags_table}(id)
                )
            ''')
            
            # 创建错题复习计划表
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {review_plans_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    error_question_id INTEGER NOT NULL,
                    review_time TIMESTAMP,
                    review_interval INTEGER,
                    priority INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'pending',
                    review_result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id),
                    FOREIGN KEY (error_question_id) REFERENCES {error_questions_table}(id)
                )
            ''')
            
            # 创建老师AI交接表
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {teacher_ai_transfer_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    error_question_id INTEGER NOT NULL,
                    teacher_ai_id TEXT NOT NULL,
                    transfer_reason TEXT,
                    analysis_result TEXT,
                    teacher_feedback TEXT,
                    follow_up_actions TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id),
                    FOREIGN KEY (error_question_id) REFERENCES {error_questions_table}(id)
                )
            ''')
            
            # 创建错题统计数据表
            db_manager.execute(f'''
                CREATE TABLE IF NOT EXISTS {error_statistics_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date DATE,
                    total_errors INTEGER DEFAULT 0,
                    resolved_errors INTEGER DEFAULT 0,
                    error_types TEXT,
                    knowledge_points TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES {user_table}(id)
                )
            ''')
            
            logger.info("错题管理表结构创建完成")
            
        except Exception as e:
            logger.error(f"创建错题管理表结构失败: {str(e)}")
    
    def add_error_question(self, user_id: int, question_id: int, exam_record_id: int, 
                         user_answer: str, correct_answer: str, error_reason: str = None, 
                         error_type: str = None, tags: List[str] = None, knowledge_point: str = None, 
                         difficulty_level: int = None) -> int:
        """
        添加错题
        
        Args:
            user_id: 用户ID
            question_id: 题目ID
            exam_record_id: 考试记录ID
            user_answer: 用户答案
            correct_answer: 正确答案
            error_reason: 错误原因
            error_type: 错误类型
            tags: 错题标签
            knowledge_point: 知识点
            difficulty_level: 难度等级
        
        Returns:
            错题ID
        """
        try:
            # 获取加密后的表名
            error_questions_table = table_encryption.encrypt_table_name('error_questions')
            error_tags_table = table_encryption.encrypt_table_name('error_tags')
            error_question_tags_table = table_encryption.encrypt_table_name('error_question_tags')
            
            # 检查是否已经存在
            existing = db_manager.fetch_one(
                f'SELECT id FROM {error_questions_table} WHERE user_id = ? AND question_id = ?',
                (user_id, question_id)
            )
            
            if existing:
                # 更新现有错题
                error_id = existing['id'] if isinstance(existing, dict) else existing[0]
                db_manager.execute(
                    f'''
                    UPDATE {error_questions_table}
                    SET user_answer = ?, correct_answer = ?, error_reason = ?, 
                        error_type = ?, knowledge_point = ?, difficulty_level = ?, 
                        review_count = review_count + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    ''',
                    (user_answer, correct_answer, error_reason, error_type, knowledge_point, 
                     difficulty_level, error_id)
                )
            else:
                # 创建新错题
                db_manager.execute(
                    f'''
                    INSERT INTO {error_questions_table} (user_id, question_id, exam_record_id, 
                                              user_answer, correct_answer, error_reason, 
                                              error_type, knowledge_point, difficulty_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (user_id, question_id, exam_record_id, user_answer, correct_answer, 
                     error_reason, error_type, knowledge_point, difficulty_level)
                )
                # 获取最后插入的ID
                result = db_manager.fetch_one('SELECT last_insert_rowid()')
                if result:
                    error_id = result['last_insert_rowid()'] if isinstance(result, dict) else result[0]
                else:
                    return -1
            
            # 添加标签
            if tags:
                for tag_name in tags:
                    # 查找或创建标签
                    tag = db_manager.fetch_one(
                        f'SELECT id FROM {error_tags_table} WHERE name = ?',
                        (tag_name,)
                    )
                    if not tag:
                        # 自动分类标签
                        category = self._categorize_tag(tag_name)
                        db_manager.execute(
                            f'INSERT INTO {error_tags_table} (name, category) VALUES (?, ?)',
                            (tag_name, category)
                        )
                        tag_result = db_manager.fetch_one('SELECT last_insert_rowid()')
                        tag_id = tag_result['last_insert_rowid()'] if isinstance(tag_result, dict) else tag_result[0]
                    else:
                        tag_id = tag['id'] if isinstance(tag, dict) else tag[0]
                    
                    # 关联标签
                    db_manager.execute(
                        f'''
                        INSERT OR IGNORE INTO {error_question_tags_table} (error_question_id, tag_id)
                        VALUES (?, ?)
                        ''',
                        (error_id, tag_id)
                    )
            
            # 更新错题统计
            self._update_error_statistics(user_id, error_type, knowledge_point)
            
            # 自动生成复习计划
            self._generate_review_plan(user_id, error_id, difficulty_level)
            
            logger.info(f"添加错题成功: {error_id}")
            return error_id
        except Exception as e:
            logger.error(f"添加错题失败: {str(e)}")
            return -1
    
    def get_user_error_questions(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取用户的错题列表
        
        Args:
            user_id: 用户ID
            limit: 限制数量
        
        Returns:
            错题列表
        """
        try:
            # 获取加密后的表名
            error_questions_table = table_encryption.encrypt_table_name('error_questions')
            questions_table = table_encryption.encrypt_table_name('questions')
            error_question_tags_table = table_encryption.encrypt_table_name('error_question_tags')
            error_tags_table = table_encryption.encrypt_table_name('error_tags')
            question_options_table = table_encryption.encrypt_table_name('question_options')
            question_tag_relations_table = table_encryption.encrypt_table_name('question_tag_relations')
            question_tags_table = table_encryption.encrypt_table_name('question_tags')
            
            questions = db_manager.fetch_all(
                f'''
                SELECT eq.*, q.content, q.type as question_type
                FROM {error_questions_table} eq
                LEFT JOIN {questions_table} q ON eq.question_id = q.id
                WHERE eq.user_id = ?
                ORDER BY eq.created_at DESC
                LIMIT ?
                ''',
                (user_id, limit)
            )
            
            result = []
            for q in questions:
                content = None
                question_type = None
                
                if isinstance(q, dict):
                    content = q.get('content')
                    question_type = q.get('question_type')
                else:
                    if len(q) > 13:
                        content = q[13]
                    if len(q) > 14:
                        question_type = q[14]
                
                item = {
                    'id': q['id'] if isinstance(q, dict) else q[0],
                    'user_id': q['user_id'] if isinstance(q, dict) else q[1],
                    'question_id': q['question_id'] if isinstance(q, dict) else q[2],
                    'exam_record_id': q['exam_record_id'] if isinstance(q, dict) else q[3],
                    'user_answer': q['user_answer'] if isinstance(q, dict) else q[4],
                    'correct_answer': q['correct_answer'] if isinstance(q, dict) else q[5],
                    'error_reason': q['error_reason'] if isinstance(q, dict) else q[6],
                    'error_type': q['error_type'] if isinstance(q, dict) else q[7],
                    'mastery_level': q['mastery_level'] if isinstance(q, dict) else q[8],
                    'review_count': q['review_count'] if isinstance(q, dict) else q[9],
                    'last_review_time': q['last_review_time'] if isinstance(q, dict) else q[10],
                    'created_at': q['created_at'] if isinstance(q, dict) else q[11],
                    'updated_at': q['updated_at'] if isinstance(q, dict) else q[12],
                    'content': content,
                    'question_type': question_type,
                    'options': [],
                    'question_tags': []
                }
                
                # 获取题目选项
                options = db_manager.fetch_all(
                    f'''
                    SELECT option_text FROM {question_options_table} 
                    WHERE question_id = ? 
                    ORDER BY option_index
                    ''',
                    (item['question_id'],)
                )
                item['options'] = [opt['option_text'] if isinstance(opt, dict) else opt[0] for opt in options]
                
                # 获取题目标签
                question_tags = db_manager.fetch_all(
                    f'''
                    SELECT qt.tag_name
                    FROM {question_tag_relations_table} qtr
                    JOIN {question_tags_table} qt ON qtr.tag_id = qt.id
                    WHERE qtr.question_id = ?
                    ''',
                    (item['question_id'],)
                )
                item['question_tags'] = [tag['tag_name'] if isinstance(tag, dict) else tag[0] for tag in question_tags]
                
                # 获取错题标签
                tags = db_manager.fetch_all(
                    f'''
                    SELECT et.name
                    FROM {error_question_tags_table} eqt
                    JOIN {error_tags_table} et ON eqt.tag_id = et.id
                    WHERE eqt.error_question_id = ?
                    ''',
                    (item['id'],)
                )
                item['tags'] = [t['name'] if isinstance(t, dict) else t[0] for t in tags]
                
                result.append(item)
            
            return result
        except Exception as e:
            logger.error(f"获取用户错题列表失败: {str(e)}")
            return []
    
    def update_mastery_level(self, error_question_id: int, mastery_level: int) -> bool:
        """
        更新错题掌握程度
        
        Args:
            error_question_id: 错题ID
            mastery_level: 掌握程度 (0-5)
        
        Returns:
            是否成功
        """
        try:
            # 获取加密后的表名
            error_questions_table = table_encryption.encrypt_table_name('error_questions')
            
            db_manager.execute(
                f'''
                UPDATE {error_questions_table}
                SET mastery_level = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''',
                (mastery_level, error_question_id)
            )
            logger.info(f"更新错题掌握程度成功: {error_question_id}, 掌握程度: {mastery_level}")
            return True
        except Exception as e:
            logger.error(f"更新错题掌握程度失败: {str(e)}")
            return False
    
    def review_error_question(self, error_question_id: int, review_result: str) -> bool:
        """
        复习错题
        
        Args:
            error_question_id: 错题ID
            review_result: 复习结果
        
        Returns:
            是否成功
        """
        try:
            current_time = time.time()
            
            # 获取加密后的表名
            error_questions_table = table_encryption.encrypt_table_name('error_questions')
            review_plans_table = table_encryption.encrypt_table_name('review_plans')
            
            # 更新错题
            db_manager.execute(
                f'''
                UPDATE {error_questions_table}
                SET review_count = review_count + 1, last_review_time = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''',
                (current_time, error_question_id)
            )
            
            # 更新复习计划
            db_manager.execute(
                f'''
                UPDATE {review_plans_table}
                SET status = 'completed', review_result = ?, updated_at = CURRENT_TIMESTAMP
                WHERE error_question_id = ? AND status = 'pending'
                ''',
                (review_result, error_question_id)
            )
            
            logger.info(f"复习错题成功: {error_question_id}")
            return True
        except Exception as e:
            logger.error(f"复习错题失败: {str(e)}")
            return False
    
    def create_review_plan(self, user_id: int, error_question_id: int, review_time: float) -> int:
        """
        创建复习计划
        
        Args:
            user_id: 用户ID
            error_question_id: 错题ID
            review_time: 复习时间
        
        Returns:
            计划ID
        """
        try:
            # 获取加密后的表名
            review_plans_table = table_encryption.encrypt_table_name('review_plans')
            
            db_manager.execute(
                f'''
                INSERT INTO {review_plans_table} (user_id, error_question_id, review_time)
                VALUES (?, ?, ?)
                ''',
                (user_id, error_question_id, review_time)
            )
            
            result = db_manager.fetch_one('SELECT last_insert_rowid()')
            if result:
                plan_id = result['last_insert_rowid()'] if isinstance(result, dict) else result[0]
                logger.info(f"创建复习计划成功: {plan_id}")
                return plan_id
            return -1
        except Exception as e:
            logger.error(f"创建复习计划失败: {str(e)}")
            return -1
    
    def transfer_to_teacher_ai(self, user_id: int, error_question_id: int, teacher_ai_id: str, 
                              transfer_reason: str) -> int:
        """
        交接给老师AI
        
        Args:
            user_id: 用户ID
            error_question_id: 错题ID
            teacher_ai_id: 老师AI ID
            transfer_reason: 交接原因
        
        Returns:
            交接记录ID
        """
        try:
            # 获取加密后的表名
            teacher_ai_transfer_table = table_encryption.encrypt_table_name('teacher_ai_transfer')
            
            db_manager.execute(
                f'''
                INSERT INTO {teacher_ai_transfer_table} (user_id, error_question_id, teacher_ai_id, transfer_reason)
                VALUES (?, ?, ?, ?)
                ''',
                (user_id, error_question_id, teacher_ai_id, transfer_reason)
            )
            
            result = db_manager.fetch_one('SELECT last_insert_rowid()')
            if result:
                transfer_id = result['last_insert_rowid()'] if isinstance(result, dict) else result[0]
                logger.info(f"交接给老师AI成功: {transfer_id}")
                return transfer_id
            return -1
        except Exception as e:
            logger.error(f"交接给老师AI失败: {str(e)}")
            return -1
    
    def update_teacher_ai_transfer(self, transfer_id: int, analysis_result: str, 
                                 teacher_feedback: str, status: str) -> bool:
        """
        更新老师AI交接状态
        
        Args:
            transfer_id: 交接记录ID
            analysis_result: AI分析结果
            teacher_feedback: 老师反馈
            status: 状态
        
        Returns:
            是否成功
        """
        try:
            # 获取加密后的表名
            teacher_ai_transfer_table = table_encryption.encrypt_table_name('teacher_ai_transfer')
            
            db_manager.execute(
                f'''
                UPDATE {teacher_ai_transfer_table}
                SET analysis_result = ?, teacher_feedback = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''',
                (analysis_result, teacher_feedback, status, transfer_id)
            )
            logger.info(f"更新老师AI交接状态成功: {transfer_id}")
            return True
        except Exception as e:
            logger.error(f"更新老师AI交接状态失败: {str(e)}")
            return False
    
    def get_teacher_ai_transfers(self, teacher_ai_id: str, status: str = None) -> List[Dict[str, Any]]:
        """
        获取老师AI的交接记录
        
        Args:
            teacher_ai_id: 老师AI ID
            status: 状态
        
        Returns:
            交接记录列表
        """
        try:
            # 获取加密后的表名
            teacher_ai_transfer_table = table_encryption.encrypt_table_name('teacher_ai_transfer')
            error_questions_table = table_encryption.encrypt_table_name('error_questions')
            questions_table = table_encryption.encrypt_table_name('questions')
            
            query = f'''
                SELECT tat.*, eq.user_id, eq.question_id, eq.user_answer, eq.correct_answer, 
                       eq.error_reason, eq.error_type, q.content, q.type as question_type
                FROM {teacher_ai_transfer_table} tat
                JOIN {error_questions_table} eq ON tat.error_question_id = eq.id
                JOIN {questions_table} q ON eq.question_id = q.id
                WHERE tat.teacher_ai_id = ?
            '''
            params = [teacher_ai_id]
            
            if status:
                query += ' AND tat.status = ?'
                params.append(status)
            
            query += ' ORDER BY tat.created_at DESC'
            
            transfers = db_manager.fetch_all(query, params)
            
            result = []
            for t in transfers:
                item = {
                    'id': t['id'] if isinstance(t, dict) else t[0],
                    'user_id': t['user_id'] if isinstance(t, dict) else t[1],
                    'error_question_id': t['error_question_id'] if isinstance(t, dict) else t[2],
                    'teacher_ai_id': t['teacher_ai_id'] if isinstance(t, dict) else t[3],
                    'transfer_reason': t['transfer_reason'] if isinstance(t, dict) else t[4],
                    'analysis_result': t['analysis_result'] if isinstance(t, dict) else t[5],
                    'teacher_feedback': t['teacher_feedback'] if isinstance(t, dict) else t[6],
                    'status': t['status'] if isinstance(t, dict) else t[7],
                    'created_at': t['created_at'] if isinstance(t, dict) else t[8],
                    'updated_at': t['updated_at'] if isinstance(t, dict) else t[9],
                    'question_id': t['question_id'] if isinstance(t, dict) else t[11],
                    'user_answer': t['user_answer'] if isinstance(t, dict) else t[12],
                    'correct_answer': t['correct_answer'] if isinstance(t, dict) else t[13],
                    'error_reason': t['error_reason'] if isinstance(t, dict) else t[14],
                    'error_type': t['error_type'] if isinstance(t, dict) else t[15],
                    'content': t['content'] if isinstance(t, dict) else t[16],
                    'question_type': t['question_type'] if isinstance(t, dict) else t[17]
                }
                result.append(item)
            
            return result
        except Exception as e:
            logger.error(f"获取老师AI交接记录失败: {str(e)}")
            return []
    
    def get_error_question_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户错题统计信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            统计信息
        """
        try:
            # 获取加密后的表名
            error_questions_table = table_encryption.encrypt_table_name('error_questions')
            questions_table = table_encryption.encrypt_table_name('questions')
            review_plans_table = table_encryption.encrypt_table_name('review_plans')
            
            # 总错题数
            total_count = db_manager.fetch_scalar(
                f'SELECT COUNT(*) FROM {error_questions_table} WHERE user_id = ?',
                (user_id,)
            )
            
            # 按错误类型统计
            error_types = db_manager.fetch_all(
                f'''
                SELECT error_type, COUNT(*) as count
                FROM {error_questions_table}
                WHERE user_id = ?
                GROUP BY error_type
                ''',
                (user_id,)
            )
            
            # 按掌握程度统计
            mastery_levels = db_manager.fetch_all(
                f'''
                SELECT mastery_level, COUNT(*) as count
                FROM {error_questions_table}
                WHERE user_id = ?
                GROUP BY mastery_level
                ''',
                (user_id,)
            )
            
            # 按知识点统计
            knowledge_points = db_manager.fetch_all(
                f'''
                SELECT knowledge_point, COUNT(*) as count
                FROM {error_questions_table}
                WHERE user_id = ? AND knowledge_point IS NOT NULL
                GROUP BY knowledge_point
                ''',
                (user_id,)
            )
            
            # 按难度等级统计
            difficulty_levels = db_manager.fetch_all(
                f'''
                SELECT difficulty_level, COUNT(*) as count
                FROM {error_questions_table}
                WHERE user_id = ? AND difficulty_level IS NOT NULL
                GROUP BY difficulty_level
                ''',
                (user_id,)
            )
            
            # 最近添加的错题
            recent_errors = db_manager.fetch_all(
                f'''
                SELECT eq.*, q.content
                FROM {error_questions_table} eq
                JOIN {questions_table} q ON eq.question_id = q.id
                WHERE eq.user_id = ?
                ORDER BY eq.created_at DESC
                LIMIT 5
                ''',
                (user_id,)
            )
            
            # 待复习的错题
            pending_reviews = db_manager.fetch_all(
                f'''
                SELECT eq.*, q.content
                FROM {error_questions_table} eq
                JOIN {questions_table} q ON eq.question_id = q.id
                JOIN {review_plans_table} rp ON eq.id = rp.error_question_id
                WHERE eq.user_id = ? AND rp.status = 'pending'
                ORDER BY rp.priority DESC, rp.review_time ASC
                LIMIT 5
                ''',
                (user_id,)
            )
            
            return {
                'total_count': total_count,
                'error_types': {t['error_type'] if isinstance(t, dict) else t[0]: t['count'] if isinstance(t, dict) else t[1] for t in error_types},
                'mastery_levels': {t['mastery_level'] if isinstance(t, dict) else t[0]: t['count'] if isinstance(t, dict) else t[1] for t in mastery_levels},
                'knowledge_points': {t['knowledge_point'] if isinstance(t, dict) else t[0]: t['count'] if isinstance(t, dict) else t[1] for t in knowledge_points},
                'difficulty_levels': {t['difficulty_level'] if isinstance(t, dict) else t[0]: t['count'] if isinstance(t, dict) else t[1] for t in difficulty_levels},
                'recent_errors': [{
                    'id': e['id'] if isinstance(e, dict) else e[0],
                    'question_id': e['question_id'] if isinstance(e, dict) else e[2],
                    'content': e['content'] if isinstance(e, dict) else e[15],
                    'error_type': e['error_type'] if isinstance(e, dict) else e[7],
                    'knowledge_point': e['knowledge_point'] if isinstance(e, dict) else e[8],
                    'difficulty_level': e['difficulty_level'] if isinstance(e, dict) else e[9],
                    'created_at': e['created_at'] if isinstance(e, dict) else e[13]
                } for e in recent_errors],
                'pending_reviews': [{
                    'id': e['id'] if isinstance(e, dict) else e[0],
                    'question_id': e['question_id'] if isinstance(e, dict) else e[2],
                    'content': e['content'] if isinstance(e, dict) else e[15],
                    'knowledge_point': e['knowledge_point'] if isinstance(e, dict) else e[8],
                    'difficulty_level': e['difficulty_level'] if isinstance(e, dict) else e[9],
                    'mastery_level': e['mastery_level'] if isinstance(e, dict) else e[10]
                } for e in pending_reviews]
            }
        except Exception as e:
            logger.error(f"获取错题统计信息失败: {str(e)}")
            return {}
    
    def _categorize_tag(self, tag_name: str) -> str:
        """
        自动分类标签
        
        Args:
            tag_name: 标签名称
        
        Returns:
            标签分类
        """
        categories = {
            'conceptual': ['概念', '定义', '原理', '理论'],
            'calculation': ['计算', '运算', '公式', '数学'],
            'application': ['应用', '实践', '实例', '案例'],
            'memory': ['记忆', '背诵', '默写', '记忆点'],
            'comprehension': ['理解', '分析', '推理', '逻辑'],
            'strategy': ['策略', '技巧', '方法', '思路']
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in tag_name:
                    return category
        
        return 'other'
    
    def _update_error_statistics(self, user_id: int, error_type: str, knowledge_point: str):
        """
        更新错题统计
        
        Args:
            user_id: 用户ID
            error_type: 错误类型
            knowledge_point: 知识点
        """
        try:
            import datetime
            today = datetime.date.today().isoformat()
            
            # 获取加密后的表名
            error_statistics_table = table_encryption.encrypt_table_name('error_statistics')
            
            # 检查今天的统计记录是否存在
            existing = db_manager.fetch_one(
                f'SELECT id FROM {error_statistics_table} WHERE user_id = ? AND date = ?',
                (user_id, today)
            )
            
            if existing:
                # 更新现有记录
                stat_id = existing['id'] if isinstance(existing, dict) else existing[0]
                db_manager.execute(
                    f'''
                    UPDATE {error_statistics_table}
                    SET total_errors = total_errors + 1
                    WHERE id = ?
                    ''',
                    (stat_id,)
                )
            else:
                # 创建新记录
                db_manager.execute(
                    f'''
                    INSERT INTO {error_statistics_table} (user_id, date, total_errors)
                    VALUES (?, ?, 1)
                    ''',
                    (user_id, today)
                )
        except Exception as e:
            logger.error(f"更新错题统计失败: {str(e)}")
    
    def _generate_review_plan(self, user_id: int, error_question_id: int, difficulty_level: int):
        """
        自动生成复习计划
        
        Args:
            user_id: 用户ID
            error_question_id: 错题ID
            difficulty_level: 难度等级
        """
        try:
            import datetime
            
            # 获取加密后的表名
            review_plans_table = table_encryption.encrypt_table_name('review_plans')
            
            # 根据难度等级确定复习间隔和优先级
            if difficulty_level == 5:
                intervals = [1, 3, 7, 14, 30]  # 最难的题目，复习间隔更密集
                priority = 5
            elif difficulty_level == 4:
                intervals = [1, 3, 7, 14]
                priority = 4
            elif difficulty_level == 3:
                intervals = [1, 3, 7]
                priority = 3
            elif difficulty_level == 2:
                intervals = [1, 3]
                priority = 2
            else:
                intervals = [1]
                priority = 1
            
            # 生成复习计划
            for i, interval in enumerate(intervals):
                review_time = datetime.datetime.now() + datetime.timedelta(days=interval)
                
                db_manager.execute(
                    f'''
                    INSERT INTO {review_plans_table} (user_id, error_question_id, review_time, review_interval, priority)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (user_id, error_question_id, review_time.timestamp(), interval, priority)
                )
        except Exception as e:
            logger.error(f"生成复习计划失败: {str(e)}")

# 创建全局错题管理器实例
error_question_manager = ErrorQuestionManager()
