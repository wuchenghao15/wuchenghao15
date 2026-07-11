"""课程模型 - MTSCOS AI项目"""

from datetime import datetime
from app.utils.db import db_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CourseStatus:
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'


class CourseType:
    VIDEO = 'video'
    LIVE = 'live'
    INTERACTIVE = 'interactive'
    ASSESSMENT = 'assessment'
    PRACTICE = 'practice'


class Course:
    """课程数据模型"""
    TABLE_NAME = 'courses'

    def __init__(self, id=None, title=None, description=None, course_type=None, 
                 subject=None, grade=None, duration=None, cover_image=None,
                 status=None, created_by=None, created_at=None, updated_at=None,
                 view_count=0, enrollment_count=0, price=0.0, is_free=False):
        self.id = id
        self.title = title
        self.description = description
        self.course_type = course_type
        self.subject = subject
        self.grade = grade
        self.duration = duration
        self.cover_image = cover_image
        self.status = status or CourseStatus.DRAFT
        self.created_by = created_by
        self.created_at = created_at
        self.updated_at = updated_at
        self.view_count = view_count
        self.enrollment_count = enrollment_count
        self.price = price
        self.is_free = is_free

    @classmethod
    def _create_table(cls):
        """创建课程表"""
        try:
            db_manager.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    course_type TEXT DEFAULT 'video',
                    subject TEXT,
                    grade TEXT,
                    duration INTEGER DEFAULT 0,
                    cover_image TEXT,
                    status TEXT DEFAULT 'draft',
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    view_count INTEGER DEFAULT 0,
                    enrollment_count INTEGER DEFAULT 0,
                    price REAL DEFAULT 0.0,
                    is_free INTEGER DEFAULT 1
                )
            """)
        except Exception as e:
            logger.error(f"创建课程表失败: {str(e)}")

    @classmethod
    def create(cls, title: str, description: str = None, course_type: str = 'video',
               subject: str = None, grade: str = None, duration: int = 0,
               cover_image: str = None, created_by: int = None) -> 'Course':
        """创建课程"""
        try:
            cls._create_table()
            db_manager.execute(f"""
                INSERT INTO {cls.TABLE_NAME} 
                (title, description, course_type, subject, grade, duration, 
                 cover_image, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, description, course_type, subject, grade, duration, 
                  cover_image, created_by))
            course_id = db_manager.fetch_one(f"SELECT last_insert_rowid() FROM {cls.TABLE_NAME}")
            course_id = course_id[0] if course_id else None
            logger.info(f"创建课程成功: id={course_id}, title={title}")
            return cls.get_by_id(course_id)
        except Exception as e:
            logger.error(f"创建课程失败: {str(e)}")
            return None

    @classmethod
    def get_by_id(cls, course_id: int) -> 'Course':
        """通过ID获取课程"""
        try:
            data = db_manager.fetch_one(f"""
                SELECT * FROM {cls.TABLE_NAME} WHERE id = ?
            """, (course_id,))
            if data:
                return cls._from_row(data)
            return None
        except Exception as e:
            logger.error(f"获取课程失败: {str(e)}")
            return None

    @classmethod
    def get_all(cls, status: str = None, subject: str = None, 
                grade: str = None, page: int = 1, limit: int = 20) -> list:
        """获取课程列表"""
        try:
            query = f"SELECT * FROM {cls.TABLE_NAME}"
            params = []
            
            conditions = []
            if status:
                conditions.append("status = ?")
                params.append(status)
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
            logger.error(f"获取课程列表失败: {str(e)}")
            return []

    @classmethod
    def get_by_user(cls, user_id: int) -> list:
        """获取用户创建的课程"""
        try:
            rows = db_manager.fetch_all(f"""
                SELECT * FROM {cls.TABLE_NAME} WHERE created_by = ? ORDER BY created_at DESC
            """, (user_id,))
            return [cls._from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"获取用户课程失败: {str(e)}")
            return []

    def update(self, **kwargs) -> bool:
        """更新课程"""
        try:
            kwargs['updated_at'] = datetime.now().isoformat()
            fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
            params = list(kwargs.values()) + [self.id]
            db_manager.execute(f"""
                UPDATE {self.TABLE_NAME} SET {fields} WHERE id = ?
            """, tuple(params))
            logger.info(f"更新课程成功: id={self.id}")
            updated = self.get_by_id(self.id)
            if updated:
                self.__dict__.update(updated.__dict__)
            return True
        except Exception as e:
            logger.error(f"更新课程失败: {str(e)}")
            return False

    def delete(self) -> bool:
        """删除课程"""
        try:
            db_manager.execute(f"DELETE FROM {self.TABLE_NAME} WHERE id = ?", (self.id,))
            logger.info(f"删除课程成功: id={self.id}, title={self.title}")
            return True
        except Exception as e:
            logger.error(f"删除课程失败: {str(e)}")
            return False

    def publish(self) -> bool:
        """发布课程"""
        return self.update(status=CourseStatus.PUBLISHED)

    def archive(self) -> bool:
        """归档课程"""
        return self.update(status=CourseStatus.ARCHIVED)

    def increment_view_count(self) -> bool:
        """增加浏览量"""
        try:
            db_manager.execute(f"""
                UPDATE {self.TABLE_NAME} SET view_count = view_count + 1 WHERE id = ?
            """, (self.id,))
            self.view_count += 1
            return True
        except Exception as e:
            logger.error(f"增加浏览量失败: {str(e)}")
            return False

    def increment_enrollment_count(self) -> bool:
        """增加报名人数"""
        try:
            db_manager.execute(f"""
                UPDATE {self.TABLE_NAME} SET enrollment_count = enrollment_count + 1 WHERE id = ?
            """, (self.id,))
            self.enrollment_count += 1
            return True
        except Exception as e:
            logger.error(f"增加报名人数失败: {str(e)}")
            return False

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'course_type': self.course_type,
            'subject': self.subject,
            'grade': self.grade,
            'duration': self.duration,
            'cover_image': self.cover_image,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'view_count': self.view_count,
            'enrollment_count': self.enrollment_count,
            'price': self.price,
            'is_free': bool(self.is_free)
        }

    @classmethod
    def _from_row(cls, row) -> 'Course':
        """从数据库行创建课程对象"""
        if isinstance(row, dict):
            return cls(
                id=row.get('id'),
                title=row.get('title'),
                description=row.get('description'),
                course_type=row.get('course_type'),
                subject=row.get('subject'),
                grade=row.get('grade'),
                duration=row.get('duration'),
                cover_image=row.get('cover_image'),
                status=row.get('status'),
                created_by=row.get('created_by'),
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at'),
                view_count=row.get('view_count', 0),
                enrollment_count=row.get('enrollment_count', 0),
                price=row.get('price', 0.0),
                is_free=bool(row.get('is_free', 1))
            )
        else:
            return cls(
                id=row[0],
                title=row[1],
                description=row[2],
                course_type=row[3],
                subject=row[4],
                grade=row[5],
                duration=row[6],
                cover_image=row[7],
                status=row[8],
                created_by=row[9],
                created_at=row[10],
                updated_at=row[11],
                view_count=row[12] if len(row) > 12 else 0,
                enrollment_count=row[13] if len(row) > 13 else 0,
                price=row[14] if len(row) > 14 else 0.0,
                is_free=bool(row[15] if len(row) > 15 else 1)
            )

    @staticmethod
    def get_statistics() -> dict:
        """获取课程统计信息"""
        try:
            total = db_manager.fetch_one("SELECT COUNT(*) FROM courses")
            published = db_manager.fetch_one("SELECT COUNT(*) FROM courses WHERE status = 'published'")
            total_views = db_manager.fetch_one("SELECT COALESCE(SUM(view_count), 0) FROM courses")
            total_enrollments = db_manager.fetch_one("SELECT COALESCE(SUM(enrollment_count), 0) FROM courses")
            
            return {
                'total_courses': total[0] if total else 0,
                'published_courses': published[0] if published else 0,
                'total_views': total_views[0] if total_views else 0,
                'total_enrollments': total_enrollments[0] if total_enrollments else 0
            }
        except Exception as e:
            logger.error(f"获取课程统计失败: {str(e)}")
            return {
                'total_courses': 0,
                'published_courses': 0,
                'total_views': 0,
                'total_enrollments': 0
            }