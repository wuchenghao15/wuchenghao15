"""作业模型 - MTSCOS AI项目"""

from datetime import datetime
from app.utils.db import db_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AssignmentStatus:
    DRAFT = 'draft'
    PUBLISHED = 'published'
    CLOSED = 'closed'


class AssignmentType:
    HOMEWORK = 'homework'
    QUIZ = 'quiz'
    EXAM = 'exam'
    PROJECT = 'project'
    ESSAY = 'essay'


class Assignment:
    """作业数据模型"""
    TABLE_NAME = 'assignments'

    def __init__(self, id=None, title=None, description=None, assignment_type=None,
                 course_id=None, subject=None, grade=None, total_score=100,
                 status=None, created_by=None, created_at=None, updated_at=None,
                 due_date=None, published_at=None, completed_count=0,
                 submission_count=0, max_attempts=1, allow_late_submission=False):
        self.id = id
        self.title = title
        self.description = description
        self.assignment_type = assignment_type
        self.course_id = course_id
        self.subject = subject
        self.grade = grade
        self.total_score = total_score
        self.status = status or AssignmentStatus.DRAFT
        self.created_by = created_by
        self.created_at = created_at
        self.updated_at = updated_at
        self.due_date = due_date
        self.published_at = published_at
        self.completed_count = completed_count
        self.submission_count = submission_count
        self.max_attempts = max_attempts
        self.allow_late_submission = allow_late_submission

    @classmethod
    def _create_table(cls):
        """创建作业表"""
        try:
            db_manager.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    assignment_type TEXT DEFAULT 'homework',
                    course_id INTEGER,
                    subject TEXT,
                    grade TEXT,
                    total_score INTEGER DEFAULT 100,
                    status TEXT DEFAULT 'draft',
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    due_date TIMESTAMP,
                    published_at TIMESTAMP,
                    completed_count INTEGER DEFAULT 0,
                    submission_count INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 1,
                    allow_late_submission INTEGER DEFAULT 0
                )
            """)
        except Exception as e:
            logger.error(f"创建作业表失败: {str(e)}")

    @classmethod
    def create(cls, title: str, description: str = None, assignment_type: str = 'homework',
               course_id: int = None, subject: str = None, grade: str = None,
               total_score: int = 100, due_date: str = None, max_attempts: int = 1,
               allow_late_submission: bool = False, created_by: int = None) -> 'Assignment':
        """创建作业"""
        try:
            cls._create_table()
            db_manager.execute(f"""
                INSERT INTO {cls.TABLE_NAME} 
                (title, description, assignment_type, course_id, subject, grade, 
                 total_score, due_date, max_attempts, allow_late_submission, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, description, assignment_type, course_id, subject, grade,
                  total_score, due_date, max_attempts, 1 if allow_late_submission else 0, created_by))
            assignment_id = db_manager.fetch_one(f"SELECT last_insert_rowid() FROM {cls.TABLE_NAME}")
            assignment_id = assignment_id[0] if assignment_id else None
            logger.info(f"创建作业成功: id={assignment_id}, title={title}")
            return cls.get_by_id(assignment_id)
        except Exception as e:
            logger.error(f"创建作业失败: {str(e)}")
            return None

    @classmethod
    def get_by_id(cls, assignment_id: int) -> 'Assignment':
        """通过ID获取作业"""
        try:
            data = db_manager.fetch_one(f"""
                SELECT * FROM {cls.TABLE_NAME} WHERE id = ?
            """, (assignment_id,))
            if data:
                return cls._from_row(data)
            return None
        except Exception as e:
            logger.error(f"获取作业失败: {str(e)}")
            return None

    @classmethod
    def get_all(cls, status: str = None, course_id: int = None, subject: str = None,
                grade: str = None, page: int = 1, limit: int = 20) -> list:
        """获取作业列表"""
        try:
            query = f"SELECT * FROM {cls.TABLE_NAME}"
            params = []
            
            conditions = []
            if status:
                conditions.append("status = ?")
                params.append(status)
            if course_id:
                conditions.append("course_id = ?")
                params.append(course_id)
            if subject:
                conditions.append("subject = ?")
                params.append(subject)
            if grade:
                conditions.append("grade = ?")
                params.append(grade)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, (page - 1) * limit])
            
            rows = db_manager.fetch_all(query, tuple(params))
            return [cls._from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"获取作业列表失败: {str(e)}")
            return []

    @classmethod
    def get_by_user(cls, user_id: int) -> list:
        """获取用户创建的作业"""
        try:
            rows = db_manager.fetch_all(f"""
                SELECT * FROM {cls.TABLE_NAME} WHERE created_by = ? ORDER BY created_at DESC
            """, (user_id,))
            return [cls._from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"获取用户作业失败: {str(e)}")
            return []

    def update(self, **kwargs) -> bool:
        """更新作业"""
        try:
            kwargs['updated_at'] = datetime.now().isoformat()
            fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
            params = list(kwargs.values()) + [self.id]
            db_manager.execute(f"""
                UPDATE {self.TABLE_NAME} SET {fields} WHERE id = ?
            """, tuple(params))
            logger.info(f"更新作业成功: id={self.id}")
            updated = self.get_by_id(self.id)
            if updated:
                self.__dict__.update(updated.__dict__)
            return True
        except Exception as e:
            logger.error(f"更新作业失败: {str(e)}")
            return False

    def delete(self) -> bool:
        """删除作业"""
        try:
            db_manager.execute(f"DELETE FROM {self.TABLE_NAME} WHERE id = ?", (self.id,))
            logger.info(f"删除作业成功: id={self.id}, title={self.title}")
            return True
        except Exception as e:
            logger.error(f"删除作业失败: {str(e)}")
            return False

    def publish(self) -> bool:
        """发布作业"""
        return self.update(status=AssignmentStatus.PUBLISHED, 
                          published_at=datetime.now().isoformat())

    def close(self) -> bool:
        """关闭作业"""
        return self.update(status=AssignmentStatus.CLOSED)

    def increment_submission_count(self) -> bool:
        """增加提交次数"""
        try:
            db_manager.execute(f"""
                UPDATE {self.TABLE_NAME} SET submission_count = submission_count + 1 WHERE id = ?
            """, (self.id,))
            self.submission_count += 1
            return True
        except Exception as e:
            logger.error(f"增加提交次数失败: {str(e)}")
            return False

    def increment_completed_count(self) -> bool:
        """增加完成次数"""
        try:
            db_manager.execute(f"""
                UPDATE {self.TABLE_NAME} SET completed_count = completed_count + 1 WHERE id = ?
            """, (self.id,))
            self.completed_count += 1
            return True
        except Exception as e:
            logger.error(f"增加完成次数失败: {str(e)}")
            return False

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'assignment_type': self.assignment_type,
            'course_id': self.course_id,
            'subject': self.subject,
            'grade': self.grade,
            'total_score': self.total_score,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'due_date': self.due_date,
            'published_at': self.published_at,
            'completed_count': self.completed_count,
            'submission_count': self.submission_count,
            'max_attempts': self.max_attempts,
            'allow_late_submission': bool(self.allow_late_submission)
        }

    @classmethod
    def _from_row(cls, row) -> 'Assignment':
        """从数据库行创建作业对象"""
        if isinstance(row, dict):
            return cls(
                id=row.get('id'),
                title=row.get('title'),
                description=row.get('description'),
                assignment_type=row.get('assignment_type'),
                course_id=row.get('course_id'),
                subject=row.get('subject'),
                grade=row.get('grade'),
                total_score=row.get('total_score', 100),
                status=row.get('status'),
                created_by=row.get('created_by'),
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at'),
                due_date=row.get('due_date'),
                published_at=row.get('published_at'),
                completed_count=row.get('completed_count', 0),
                submission_count=row.get('submission_count', 0),
                max_attempts=row.get('max_attempts', 1),
                allow_late_submission=bool(row.get('allow_late_submission', 0))
            )
        else:
            return cls(
                id=row[0],
                title=row[1],
                description=row[2],
                assignment_type=row[3],
                course_id=row[4],
                subject=row[5],
                grade=row[6],
                total_score=row[7] if len(row) > 7 else 100,
                status=row[8],
                created_by=row[9],
                created_at=row[10],
                updated_at=row[11],
                due_date=row[12] if len(row) > 12 else None,
                published_at=row[13] if len(row) > 13 else None,
                completed_count=row[14] if len(row) > 14 else 0,
                submission_count=row[15] if len(row) > 15 else 0,
                max_attempts=row[16] if len(row) > 16 else 1,
                allow_late_submission=bool(row[17] if len(row) > 17 else 0)
            )

    @staticmethod
    def get_statistics() -> dict:
        """获取作业统计信息"""
        try:
            total = db_manager.fetch_one("SELECT COUNT(*) FROM assignments")
            published = db_manager.fetch_one("SELECT COUNT(*) FROM assignments WHERE status = 'published'")
            total_submissions = db_manager.fetch_one("SELECT COALESCE(SUM(submission_count), 0) FROM assignments")
            total_completed = db_manager.fetch_one("SELECT COALESCE(SUM(completed_count), 0) FROM assignments")
            
            return {
                'total_assignments': total[0] if total else 0,
                'published_assignments': published[0] if published else 0,
                'total_submissions': total_submissions[0] if total_submissions else 0,
                'total_completed': total_completed[0] if total_completed else 0
            }
        except Exception as e:
            logger.error(f"获取作业统计失败: {str(e)}")
            return {
                'total_assignments': 0,
                'published_assignments': 0,
                'total_submissions': 0,
                'total_completed': 0
            }