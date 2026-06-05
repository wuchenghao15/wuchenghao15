#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学生行为管理系统 - 数据模型"""
from app.utils.logging import logger
from datetime import datetime


class BehaviorCategory:
    """行为分类模型"""
    
    def __init__(self, category_id=None, name=None, description=None, 
                 points_default=None, is_active=1, created_at=None, 
                 created_by=None):
        self.category_id = category_id
        self.name = name
        self.description = description
        self.points_default = points_default
        self.is_active = is_active
        self.created_at = created_at
        self.created_by = created_by

    @staticmethod
    def create_table():
        """创建行为分类表"""
        try:
            from app.utils.db import db_manager
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS behavior_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    points_default INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            ''')
            logger.info("行为分类表创建成功")
            return True
        except Exception as e:
            logger.error(f"创建行为分类表失败: {str(e)}")
            return False

    @staticmethod
    def init_default_categories():
        """初始化默认行为分类"""
        try:
            from app.utils.db import db_manager
            
            default_categories = [
                ('课堂表现', '课堂参与度、注意力集中', 5),
                ('作业完成', '按时完成作业情况', 3),
                ('考试成绩', '考试成绩表现', 10),
                ('纪律表现', '遵守纪律情况', 5),
                ('团队合作', '小组合作表现', 4),
                ('创新实践', '创新思维与实践', 8),
                ('助人为乐', '帮助同学、公益活动', 6),
                ('出勤情况', '按时到校、不迟到早退', 3),
                ('学习态度', '学习积极性、主动性', 4),
                ('其他', '其他行为表现', 2)
            ]
            
            for name, desc, points in default_categories:
                existing = db_manager.fetch_one(
                    'SELECT id FROM behavior_categories WHERE name = ?',
                    (name,)
                )
                if not existing:
                    db_manager.execute(
                        'INSERT INTO behavior_categories (name, description, points_default) VALUES (?, ?, ?)',
                        (name, desc, points)
                    )
            logger.info("默认行为分类初始化完成")
            return True
        except Exception as e:
            logger.error(f"初始化默认行为分类失败: {str(e)}")
            return False

    def save(self):
        """保存行为分类"""
        try:
            from app.utils.db import db_manager
            if self.category_id:
                db_manager.execute('''
                    UPDATE behavior_categories 
                    SET name=?, description=?, points_default=?, is_active=?
                    WHERE id=?
                ''', (self.name, self.description, self.points_default, 
                      self.is_active, self.category_id))
                logger.info(f"更新行为分类: {self.name}")
            else:
                db_manager.execute('''
                    INSERT INTO behavior_categories (name, description, points_default, is_active, created_by)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.name, self.description, self.points_default, 
                      self.is_active, self.created_by))
                self.category_id = db_manager.lastrowid
                logger.info(f"创建行为分类: {self.name}")
            return True
        except Exception as e:
            logger.error(f"保存行为分类失败: {str(e)}")
            return False

    @staticmethod
    def get_all():
        """获取所有行为分类"""
        try:
            from app.utils.db import db_manager
            categories = db_manager.fetch_all('''
                SELECT id, name, description, points_default, is_active, created_at 
                FROM behavior_categories 
                ORDER BY id
            ''')
            return [BehaviorCategory(
                category_id=c['id'] if isinstance(c, dict) else c[0],
                name=c['name'] if isinstance(c, dict) else c[1],
                description=c['description'] if isinstance(c, dict) else c[2],
                points_default=c['points_default'] if isinstance(c, dict) else c[3],
                is_active=c['is_active'] if isinstance(c, dict) else c[4],
                created_at=c['created_at'] if isinstance(c, dict) else c[5]
            ) for c in categories]
        except Exception as e:
            logger.error(f"获取行为分类失败: {str(e)}")
            return []

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.category_id,
            'name': self.name,
            'description': self.description,
            'points_default': self.points_default,
            'is_active': self.is_active,
            'created_at': self.created_at
        }


class BehaviorRecord:
    """行为记录模型"""
    
    def __init__(self, record_id=None, student_id=None, category_id=None, 
                 behavior_type=None, points=None, description=None, 
                 recorded_by=None, recorded_at=None, notes=None):
        self.record_id = record_id
        self.student_id = student_id
        self.category_id = category_id
        self.behavior_type = behavior_type  # 'positive' | 'negative'
        self.points = points
        self.description = description
        self.recorded_by = recorded_by
        self.recorded_at = recorded_at
        self.notes = notes

    @staticmethod
    def create_table():
        """创建行为记录表"""
        try:
            from app.utils.db import db_manager
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS behavior_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    behavior_type TEXT NOT NULL CHECK (behavior_type IN ('positive', 'negative')),
                    points INTEGER DEFAULT 0,
                    description TEXT,
                    recorded_by INTEGER,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (student_id) REFERENCES users(id),
                    FOREIGN KEY (category_id) REFERENCES behavior_categories(id),
                    FOREIGN KEY (recorded_by) REFERENCES users(id)
                )
            ''')
            logger.info("行为记录表创建成功")
            return True
        except Exception as e:
            logger.error(f"创建行为记录表失败: {str(e)}")
            return False

    def save(self):
        """保存行为记录"""
        try:
            from app.utils.db import db_manager
            if self.record_id:
                db_manager.execute('''
                    UPDATE behavior_records 
                    SET student_id=?, category_id=?, behavior_type=?, 
                        points=?, description=?, recorded_by=?, notes=?
                    WHERE id=?
                ''', (self.student_id, self.category_id, self.behavior_type, 
                      self.points, self.description, self.recorded_by, 
                      self.notes, self.record_id))
                logger.info(f"更新行为记录: {self.record_id}")
            else:
                db_manager.execute('''
                    INSERT INTO behavior_records 
                    (student_id, category_id, behavior_type, points, description, recorded_by, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (self.student_id, self.category_id, self.behavior_type, 
                      self.points, self.description, self.recorded_by, self.notes))
                self.record_id = db_manager.lastrowid
                logger.info(f"创建行为记录: {self.record_id}")
            return True
        except Exception as e:
            logger.error(f"保存行为记录失败: {str(e)}")
            return False

    @staticmethod
    def get_by_student(student_id, limit=50):
        """获取学生的行为记录"""
        try:
            from app.utils.db import db_manager
            records = db_manager.fetch_all('''
                SELECT br.id, br.student_id, br.category_id, br.behavior_type,
                       br.points, br.description, br.recorded_by, 
                       br.recorded_at, br.notes,
                       bc.name as category_name, u.username as recorder_name
                FROM behavior_records br
                LEFT JOIN behavior_categories bc ON br.category_id = bc.id
                LEFT JOIN users u ON br.recorded_by = u.id
                WHERE br.student_id = ?
                ORDER BY br.recorded_at DESC
                LIMIT ?
            ''', (student_id, limit))
            return records
        except Exception as e:
            logger.error(f"获取学生行为记录失败: {str(e)}")
            return []

    @staticmethod
    def get_student_points(student_id):
        """获取学生的总积分"""
        try:
            from app.utils.db import db_manager
            result = db_manager.fetch_one('''
                SELECT COALESCE(SUM(points), 0) as total_points
                FROM behavior_records
                WHERE student_id = ?
            ''', (student_id,))
            if result:
                return result['total_points'] if isinstance(result, dict) else result[0]
            return 0
        except Exception as e:
            logger.error(f"获取学生积分失败: {str(e)}")
            return 0

    @staticmethod
    def get_all_students_ranking(limit=20):
        """获取学生积分排名"""
        try:
            from app.utils.db import db_manager
            ranking = db_manager.fetch_all('''
                SELECT u.id, u.username, u.email,
                       COALESCE(SUM(br.points), 0) as total_points,
                       COUNT(br.id) as record_count
                FROM users u
                LEFT JOIN behavior_records br ON u.id = br.student_id
                WHERE u.role = 'student' OR u.role = 'user'
                GROUP BY u.id
                ORDER BY total_points DESC
                LIMIT ?
            ''', (limit,))
            return ranking
        except Exception as e:
            logger.error(f"获取学生排名失败: {str(e)}")
            return []

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.record_id,
            'student_id': self.student_id,
            'category_id': self.category_id,
            'behavior_type': self.behavior_type,
            'points': self.points,
            'description': self.description,
            'recorded_by': self.recorded_by,
            'recorded_at': self.recorded_at,
            'notes': self.notes
        }


class BehaviorGoal:
    """行为目标模型"""
    
    def __init__(self, goal_id=None, student_id=None, category_id=None, 
                 target_points=None, current_points=None, start_date=None, 
                 end_date=None, status=None, created_at=None):
        self.goal_id = goal_id
        self.student_id = student_id
        self.category_id = category_id
        self.category_id = category_id
        self.target_points = target_points
        self.current_points = current_points
        self.start_date = start_date
        self.end_date = end_date
        self.status = status  # 'active', 'completed', 'expired'
        self.created_at = created_at

    @staticmethod
    def create_table():
        """创建行为目标表"""
        try:
            from app.utils.db import db_manager
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS behavior_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    category_id INTEGER,
                    target_points INTEGER NOT NULL,
                    current_points INTEGER DEFAULT 0,
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP,
                    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'expired')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES users(id),
                    FOREIGN KEY (category_id) REFERENCES behavior_categories(id)
                )
            ''')
            logger.info("行为目标表创建成功")
            return True
        except Exception as e:
            logger.error(f"创建行为目标表失败: {str(e)}")
            return False

    def save(self):
        """保存行为目标"""
        try:
            from app.utils.db import db_manager
            if self.goal_id:
                db_manager.execute('''
                    UPDATE behavior_goals 
                    SET student_id=?, category_id=?, target_points=?, 
                        current_points=?, start_date=?, end_date=?, status=?
                    WHERE id=?
                ''', (self.student_id, self.category_id, self.target_points, 
                      self.current_points, self.start_date, self.end_date, 
                      self.status, self.goal_id))
                logger.info(f"更新行为目标: {self.goal_id}")
            else:
                db_manager.execute('''
                    INSERT INTO behavior_goals 
                    (student_id, category_id, target_points, current_points, 
                     start_date, end_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (self.student_id, self.category_id, self.target_points, 
                      self.current_points, self.start_date, self.end_date, self.status))
                self.goal_id = db_manager.lastrowid
                logger.info(f"创建行为目标: {self.goal_id}")
            return True
        except Exception as e:
            logger.error(f"保存行为目标失败: {str(e)}")
            return False

    @staticmethod
    def get_by_student(student_id):
        """获取学生的行为目标"""
        try:
            from app.utils.db import db_manager
            goals = db_manager.fetch_all('''
                SELECT bg.id, bg.student_id, bg.category_id, bg.target_points,
                       bg.current_points, bg.start_date, bg.end_date, bg.status,
                       bc.name as category_name
                FROM behavior_goals bg
                LEFT JOIN behavior_categories bc ON bg.category_id = bc.id
                WHERE bg.student_id = ?
                ORDER BY bg.created_at DESC
            ''', (student_id,))
            return goals
        except Exception as e:
            logger.error(f"获取学生行为目标失败: {str(e)}")
            return []


def init_behavior_system():
    """初始化学生行为管理系统"""
    BehaviorCategory.create_table()
    BehaviorRecord.create_table()
    BehaviorGoal.create_table()
    BehaviorCategory.init_default_categories()
    logger.info("学生行为管理系统初始化完成")
    return True