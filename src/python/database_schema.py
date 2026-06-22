"""
MTSCOS AI 智能管理系统 - 数据库架构
按内容分表分项设计
"""

from database_schema_base import DatabaseSchema

# ============================================================
# 数据库架构定义
# ============================================================

SCHEMA = DatabaseSchema()

# ----------------------------------------------------------
# 1. 用户与认证相关表
# ----------------------------------------------------------

SCHEMA.add_table("users", {
    "description": "用户主表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "user_id": {"type": "TEXT", "unique": True, "not_null": True},
        "username": {"type": "TEXT", "unique": True, "not_null": True},
        "password_hash": {"type": "TEXT", "not_null": True},
        "email": {"type": "TEXT"},
        "phone": {"type": "TEXT"},
        "avatar": {"type": "TEXT"},
        "role": {"type": "TEXT", "default": "user"},
        "status": {"type": "TEXT", "default": "active"},
        "created_at": {"type": "INTEGER", "not_null": True},
        "updated_at": {"type": "INTEGER", "not_null": True},
        "last_login": {"type": "INTEGER"},
        "login_attempts": {"type": "INTEGER", "default": 0},
        "locked_until": {"type": "INTEGER", "default": 0},
        "is_active": {"type": "INTEGER", "default": 1}
    },
    "indexes": ["username", "email", "role", "status"]
})

SCHEMA.add_table("user_profiles", {
    "description": "用户详细信息表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "user_id": {"type": "TEXT", "unique": True, "not_null": True},
        "real_name": {"type": "TEXT"},
        "gender": {"type": "TEXT"},
        "birthday": {"type": "TEXT"},
        "address": {"type": "TEXT"},
        "bio": {"type": "TEXT"},
        "education": {"type": "TEXT"},
        "occupation": {"type": "TEXT"},
        "interests": {"type": "TEXT"},  # JSON数组
        "preferences": {"type": "TEXT"},  # JSON对象
        "created_at": {"type": "INTEGER", "not_null": True},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["user_id"]
})

SCHEMA.add_table("user_sessions", {
    "description": "用户会话表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "session_id": {"type": "TEXT", "unique": True, "not_null": True},
        "user_id": {"type": "TEXT", "not_null": True},
        "token": {"type": "TEXT"},
        "ip_address": {"type": "TEXT"},
        "user_agent": {"type": "TEXT"},
        "device_info": {"type": "TEXT"},
        "created_at": {"type": "INTEGER", "not_null": True},
        "expires_at": {"type": "INTEGER", "not_null": True},
        "last_activity": {"type": "INTEGER"},
        "is_active": {"type": "INTEGER", "default": 1}
    },
    "indexes": ["user_id", "session_id", "expires_at"]
})

SCHEMA.add_table("user_security", {
    "description": "用户安全表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "user_id": {"type": "TEXT", "unique": True, "not_null": True},
        "security_question": {"type": "TEXT"},
        "security_answer_hash": {"type": "TEXT"},
        "password_history": {"type": "TEXT"},  # JSON数组
        "trusted_devices": {"type": "TEXT"},  # JSON数组
        "login_history": {"type": "TEXT"},  # JSON数组
        "security_level": {"type": "INTEGER", "default": 1},
        "mfa_enabled": {"type": "INTEGER", "default": 0},
        "mfa_secret": {"type": "TEXT"},
        "created_at": {"type": "INTEGER", "not_null": True},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["user_id"]
})

# ----------------------------------------------------------
# 2. 权限与角色相关表
# ----------------------------------------------------------

SCHEMA.add_table("roles", {
    "description": "角色表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "role_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "description": {"type": "TEXT"},
        "level": {"type": "INTEGER", "default": 1},
        "permissions": {"type": "TEXT"},  # JSON数组
        "is_system": {"type": "INTEGER", "default": 0},
        "created_at": {"type": "INTEGER", "not_null": True},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["role_id", "name"]
})

SCHEMA.add_table("permissions", {
    "description": "权限表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "permission_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "category": {"type": "TEXT", "not_null": True},
        "description": {"type": "TEXT"},
        "resource": {"type": "TEXT"},
        "action": {"type": "TEXT"},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["permission_id", "category"]
})

SCHEMA.add_table("role_permissions", {
    "description": "角色权限关联表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "role_id": {"type": "TEXT", "not_null": True},
        "permission_id": {"type": "TEXT", "not_null": True},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["role_id", "permission_id"]
})

# ----------------------------------------------------------
# 3. AI员工相关表
# ----------------------------------------------------------

SCHEMA.add_table("ai_employees", {
    "description": "AI员工主表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "employee_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "title": {"type": "TEXT", "not_null": True},
        "description": {"type": "TEXT"},
        "avatar": {"type": "TEXT"},
        "category": {"type": "TEXT", "not_null": True},
        "subcategory": {"type": "TEXT"},
        "capabilities": {"type": "TEXT"},  # JSON数组
        "skills": {"type": "TEXT"},  # JSON数组
        "status": {"type": "TEXT", "default": "active"},
        "efficiency": {"type": "REAL", "default": 95.0},
        "workload": {"type": "REAL", "default": 30.0},
        "task_count": {"type": "INTEGER", "default": 0},
        "success_count": {"type": "INTEGER", "default": 0},
        "rating": {"type": "REAL", "default": 5.0},
        "created_at": {"type": "INTEGER", "not_null": True},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["employee_id", "name", "category", "status"]
})

SCHEMA.add_table("ai_employee_categories", {
    "description": "AI员工分类表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "category_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "icon": {"type": "TEXT"},
        "description": {"type": "TEXT"},
        "parent_id": {"type": "TEXT"},
        "sort_order": {"type": "INTEGER", "default": 0},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["category_id", "parent_id"]
})

SCHEMA.add_table("ai_tasks", {
    "description": "AI任务表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "task_id": {"type": "TEXT", "unique": True, "not_null": True},
        "employee_id": {"type": "TEXT", "not_null": True},
        "task_type": {"type": "TEXT", "not_null": True},
        "title": {"type": "TEXT"},
        "description": {"type": "TEXT"},
        "input_data": {"type": "TEXT"},  # JSON
        "output_data": {"type": "TEXT"},  # JSON
        "status": {"type": "TEXT", "default": "pending"},
        "priority": {"type": "INTEGER", "default": 5},
        "progress": {"type": "INTEGER", "default": 0},
        "error_message": {"type": "TEXT"},
        "started_at": {"type": "INTEGER"},
        "completed_at": {"type": "INTEGER"},
        "created_at": {"type": "INTEGER", "not_null": True},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["employee_id", "status", "task_type", "created_at"]
})

SCHEMA.add_table("ai_collaborations", {
    "description": "AI协作表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "collab_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "task_ids": {"type": "TEXT"},  # JSON数组
        "participants": {"type": "TEXT"},  # JSON数组
        "mode": {"type": "TEXT"},  # sequential, parallel, adaptive
        "status": {"type": "TEXT", "default": "pending"},
        "result": {"type": "TEXT"},  # JSON
        "created_at": {"type": "INTEGER", "not_null": True},
        "completed_at": {"type": "INTEGER"}
    },
    "indexes": ["collab_id", "status"]
})

SCHEMA.add_table("ai_knowledge", {
    "description": "AI知识库表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "knowledge_id": {"type": "TEXT", "unique": True, "not_null": True},
        "employee_id": {"type": "TEXT"},
        "category": {"type": "TEXT", "not_null": True},
        "title": {"type": "TEXT", "not_null": True},
        "content": {"type": "TEXT", "not_null": True},
        "tags": {"type": "TEXT"},  # JSON数组
        "source": {"type": "TEXT"},
        "author": {"type": "TEXT"},
        "views": {"type": "INTEGER", "default": 0},
        "rating": {"type": "REAL", "default": 0},
        "created_at": {"type": "INTEGER", "not_null": True},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["knowledge_id", "category", "employee_id"]
})

# ----------------------------------------------------------
# 4. 教育相关表
# ----------------------------------------------------------

SCHEMA.add_table("question_banks", {
    "description": "题库表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "bank_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "subject": {"type": "TEXT", "not_null": True},
        "grade_level": {"type": "TEXT"},  # 如 "1-9" 或 "N1-N5"
        "description": {"type": "TEXT"},
        "tags": {"type": "TEXT"},  # JSON数组
        "question_count": {"type": "INTEGER", "default": 0},
        "creator_id": {"type": "TEXT"},
        "is_public": {"type": "INTEGER", "default": 0},
        "status": {"type": "TEXT", "default": "active"},
        "created_at": {"type": "INTEGER", "not_null": True},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["bank_id", "subject", "grade_level"]
})

SCHEMA.add_table("questions", {
    "description": "题目表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "question_id": {"type": "TEXT", "unique": True, "not_null": True},
        "bank_id": {"type": "TEXT", "not_null": True},
        "type": {"type": "TEXT", "not_null": True},  # choice, fill, essay, etc.
        "content": {"type": "TEXT", "not_null": True},
        "options": {"type": "TEXT"},  # JSON数组 (选择题)
        "answer": {"type": "TEXT"},  # JSON
        "analysis": {"type": "TEXT"},
        "difficulty": {"type": "INTEGER", "default": 3},  # 1-5
        "knowledge_points": {"type": "TEXT"},  # JSON数组
        "tags": {"type": "TEXT"},  # JSON数组
        "score": {"type": "INTEGER", "default": 5},
        "time_limit": {"type": "INTEGER"},  # 秒
        "usage_count": {"type": "INTEGER", "default": 0},
        "correct_rate": {"type": "REAL", "default": 0},
        "created_at": {"type": "INTEGER", "not_null": True},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["question_id", "bank_id", "type", "difficulty"]
})

SCHEMA.add_table("exams", {
    "description": "考试表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "exam_id": {"type": "TEXT", "unique": True, "not_null": True},
        "title": {"type": "TEXT", "not_null": True},
        "description": {"type": "TEXT"},
        "subject": {"type": "TEXT", "not_null": True},
        "grade_level": {"type": "TEXT"},
        "duration": {"type": "INTEGER"},  # 分钟
        "total_score": {"type": "INTEGER"},
        "pass_score": {"type": "INTEGER"},
        "question_ids": {"type": "TEXT"},  # JSON数组
        "settings": {"type": "TEXT"},  # JSON对象
        "status": {"type": "TEXT", "default": "draft"},
        "creator_id": {"type": "TEXT"},
        "created_at": {"type": "INTEGER", "not_null": True},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["exam_id", "subject", "status"]
})

SCHEMA.add_table("exam_records", {
    "description": "考试成绩表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "record_id": {"type": "TEXT", "unique": True, "not_null": True},
        "exam_id": {"type": "TEXT", "not_null": True},
        "user_id": {"type": "TEXT", "not_null": True},
        "answers": {"type": "TEXT"},  # JSON
        "score": {"type": "INTEGER"},
        "rank": {"type": "INTEGER"},
        "duration": {"type": "INTEGER"},  # 秒
        "started_at": {"type": "INTEGER"},
        "submitted_at": {"type": "INTEGER"},
        "graded_at": {"type": "INTEGER"},
        "status": {"type": "TEXT", "default": "pending"}
    },
    "indexes": ["record_id", "exam_id", "user_id", "status"]
})

SCHEMA.add_table("learning_progress", {
    "description": "学习进度表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "user_id": {"type": "TEXT", "not_null": True},
        "subject": {"type": "TEXT", "not_null": True},
        "grade_level": {"type": "TEXT"},
        "chapter": {"type": "TEXT"},
        "completed": {"type": "INTEGER", "default": 0},
        "progress": {"type": "REAL", "default": 0},  # 百分比
        "time_spent": {"type": "INTEGER", "default": 0},  # 秒
        "score": {"type": "REAL"},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["user_id", "subject", "grade_level"]
})

# ----------------------------------------------------------
# 5. 理科公式相关表
# ----------------------------------------------------------

SCHEMA.add_table("science_formulas", {
    "description": "理科公式表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "formula_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "subject": {"type": "TEXT", "not_null": True},  # math, physics, chemistry, biology
        "category": {"type": "TEXT"},  # 如: algebra, geometry, mechanics, thermodynamics
        "subcategory": {"type": "TEXT"},  # 如: quadratic_equations, trigonometry
        "formula_latex": {"type": "TEXT", "not_null": True},
        "formula_plain": {"type": "TEXT"},  # 纯文本表示
        "description": {"type": "TEXT"},  # 公式描述
        "variables": {"type": "TEXT"},  # JSON对象，变量说明
        "units": {"type": "TEXT"},  # JSON对象，单位说明
        "derivation": {"type": "TEXT"},  # 推导过程
        "applications": {"type": "TEXT"},  # 应用场景
        "grade_level": {"type": "TEXT"},  # 适用年级
        "difficulty": {"type": "INTEGER", "default": 3},  # 1-5
        "is_important": {"type": "INTEGER", "default": 0},  # 是否重点公式
        "tags": {"type": "TEXT"},  # JSON数组
        "created_at": {"type": "INTEGER", "not_null": True},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["formula_id", "subject", "category", "grade_level", "is_important"]
})

SCHEMA.add_table("formula_categories", {
    "description": "公式分类表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "category_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "subject": {"type": "TEXT", "not_null": True},
        "parent_id": {"type": "TEXT"},
        "description": {"type": "TEXT"},
        "icon": {"type": "TEXT"},
        "sort_order": {"type": "INTEGER", "default": 0},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["category_id", "subject", "parent_id"]
})

# ----------------------------------------------------------
# 6. 文件与存储相关表
# ----------------------------------------------------------

SCHEMA.add_table("files", {
    "description": "文件表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "file_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "original_name": {"type": "TEXT"},
        "type": {"type": "TEXT", "not_null": True},
        "mime_type": {"type": "TEXT"},
        "size": {"type": "INTEGER", "not_null": True},
        "path": {"type": "TEXT"},
        "url": {"type": "TEXT"},
        "thumbnail_url": {"type": "TEXT"},
        "hash": {"type": "TEXT"},
        "owner_id": {"type": "TEXT"},
        "folder_id": {"type": "TEXT"},
        "is_public": {"type": "INTEGER", "default": 0},
        "download_count": {"type": "INTEGER", "default": 0},
        "created_at": {"type": "INTEGER", "not_null": True},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["file_id", "owner_id", "type", "folder_id"]
})

SCHEMA.add_table("folders", {
    "description": "文件夹表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "folder_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "parent_id": {"type": "TEXT"},
        "owner_id": {"type": "TEXT", "not_null": True},
        "type": {"type": "TEXT", "default": "private"},  # private, shared, public
        "created_at": {"type": "INTEGER", "not_null": True},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["folder_id", "owner_id", "parent_id"]
})

SCHEMA.add_table("cloud_drives", {
    "description": "云盘表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "drive_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "owner_id": {"type": "TEXT", "not_null": True},
        "capacity": {"type": "INTEGER", "not_null": True},  # 字节
        "used_space": {"type": "INTEGER", "default": 0},
        "file_count": {"type": "INTEGER", "default": 0},
        "status": {"type": "TEXT", "default": "active"},
        "created_at": {"type": "INTEGER", "not_null": True},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["drive_id", "owner_id"]
})

# ----------------------------------------------------------
# 7. 系统配置相关表
# ----------------------------------------------------------

SCHEMA.add_table("system_config", {
    "description": "系统配置表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "key": {"type": "TEXT", "unique": True, "not_null": True},
        "value": {"type": "TEXT", "not_null": True},
        "type": {"type": "TEXT", "default": "string"},
        "category": {"type": "TEXT"},
        "description": {"type": "TEXT"},
        "is_encrypted": {"type": "INTEGER", "default": 0},
        "updated_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["key", "category"]
})

SCHEMA.add_table("themes", {
    "description": "主题配置表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "theme_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "type": {"type": "TEXT"},  # light, dark, custom
        "colors": {"type": "TEXT"},  # JSON对象
        "fonts": {"type": "TEXT"},  # JSON对象
        "is_active": {"type": "INTEGER", "default": 0},
        "is_default": {"type": "INTEGER", "default": 0},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["theme_id", "is_active"]
})

# ----------------------------------------------------------
# 8. 日志与审计相关表
# ----------------------------------------------------------

SCHEMA.add_table("logs", {
    "description": "系统日志表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "level": {"type": "TEXT", "not_null": True},  # debug, info, warn, error
        "category": {"type": "TEXT"},
        "message": {"type": "TEXT", "not_null": True},
        "context": {"type": "TEXT"},  # JSON
        "user_id": {"type": "TEXT"},
        "ip_address": {"type": "TEXT"},
        "user_agent": {"type": "TEXT"},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["level", "category", "user_id", "created_at"]
})

SCHEMA.add_table("audit_logs", {
    "description": "审计日志表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "action": {"type": "TEXT", "not_null": True},
        "resource_type": {"type": "TEXT", "not_null": True},
        "resource_id": {"type": "TEXT"},
        "user_id": {"type": "TEXT", "not_null": True},
        "old_value": {"type": "TEXT"},
        "new_value": {"type": "TEXT"},
        "ip_address": {"type": "TEXT"},
        "result": {"type": "TEXT", "default": "success"},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["action", "resource_type", "user_id", "created_at"]
})

SCHEMA.add_table("security_events", {
    "description": "安全事件表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "event_id": {"type": "TEXT", "unique": True, "not_null": True},
        "type": {"type": "TEXT", "not_null": True},
        "severity": {"type": "TEXT", "not_null": True},  # low, medium, high, critical
        "description": {"type": "TEXT"},
        "user_id": {"type": "TEXT"},
        "ip_address": {"type": "TEXT"},
        "details": {"type": "TEXT"},  # JSON
        "status": {"type": "TEXT", "default": "pending"},
        "handled_by": {"type": "TEXT"},
        "handled_at": {"type": "INTEGER"},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["event_id", "type", "severity", "status"]
})

# ----------------------------------------------------------
# 9. 同步与备份相关表
# ----------------------------------------------------------

SCHEMA.add_table("sync_records", {
    "description": "同步记录表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "sync_id": {"type": "TEXT", "unique": True, "not_null": True},
        "sync_type": {"type": "TEXT", "not_null": True},  # push, pull, full
        "direction": {"type": "TEXT", "not_null": True},  # upload, download
        "status": {"type": "TEXT", "not_null": True},  # pending, running, success, failed
        "items_total": {"type": "INTEGER", "default": 0},
        "items_synced": {"type": "INTEGER", "default": 0},
        "items_failed": {"type": "INTEGER", "default": 0},
        "error_message": {"type": "TEXT"},
        "started_at": {"type": "INTEGER"},
        "completed_at": {"type": "INTEGER"},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["sync_id", "sync_type", "status", "created_at"]
})

SCHEMA.add_table("backups", {
    "description": "备份记录表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "backup_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "type": {"type": "TEXT", "not_null": True},  # full, incremental, differential
        "size": {"type": "INTEGER"},
        "path": {"type": "TEXT"},
        "status": {"type": "TEXT", "default": "pending"},
        "tables": {"type": "TEXT"},  # JSON数组
        "created_by": {"type": "TEXT"},
        "created_at": {"type": "INTEGER", "not_null": True},
        "expires_at": {"type": "INTEGER"}
    },
    "indexes": ["backup_id", "type", "status"]
})

SCHEMA.add_table("snapshots", {
    "description": "系统快照表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "snapshot_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "description": {"type": "TEXT"},
        "type": {"type": "TEXT", "not_null": True},  # full, partial
        "data": {"type": "TEXT"},  # JSON
        "size": {"type": "INTEGER"},
        "tags": {"type": "TEXT"},  # JSON数组
        "created_by": {"type": "TEXT"},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["snapshot_id", "type", "created_at"]
})

# ----------------------------------------------------------
# 10. 消息与通知相关表
# ----------------------------------------------------------

SCHEMA.add_table("notifications", {
    "description": "通知表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "notification_id": {"type": "TEXT", "unique": True, "not_null": True},
        "user_id": {"type": "TEXT", "not_null": True},
        "type": {"type": "TEXT", "not_null": True},  # system, alert, message
        "title": {"type": "TEXT", "not_null": True},
        "content": {"type": "TEXT"},
        "data": {"type": "TEXT"},  # JSON
        "is_read": {"type": "INTEGER", "default": 0},
        "read_at": {"type": "INTEGER"},
        "priority": {"type": "TEXT", "default": "normal"},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["notification_id", "user_id", "is_read", "created_at"]
})

SCHEMA.add_table("messages", {
    "description": "消息表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "message_id": {"type": "TEXT", "unique": True, "not_null": True},
        "from_user_id": {"type": "TEXT", "not_null": True},
        "to_user_id": {"type": "TEXT", "not_null": True},
        "content": {"type": "TEXT", "not_null": True},
        "type": {"type": "TEXT", "default": "text"},  # text, image, file
        "is_read": {"type": "INTEGER", "default": 0},
        "read_at": {"type": "INTEGER"},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["message_id", "from_user_id", "to_user_id", "created_at"]
})

# ----------------------------------------------------------
# 11. API与第三方集成相关表
# ----------------------------------------------------------

SCHEMA.add_table("api_keys", {
    "description": "API密钥表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "key_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "api_key": {"type": "TEXT", "not_null": True},
        "secret_key": {"type": "TEXT"},
        "user_id": {"type": "TEXT", "not_null": True},
        "permissions": {"type": "TEXT"},  # JSON数组
        "rate_limit": {"type": "INTEGER"},
        "is_active": {"type": "INTEGER", "default": 1},
        "last_used_at": {"type": "INTEGER"},
        "expires_at": {"type": "INTEGER"},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["key_id", "user_id", "is_active"]
})

SCHEMA.add_table("api_logs", {
    "description": "API调用日志表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "request_id": {"type": "TEXT", "unique": True, "not_null": True},
        "api_key_id": {"type": "TEXT"},
        "method": {"type": "TEXT", "not_null": True},
        "endpoint": {"type": "TEXT", "not_null": True},
        "params": {"type": "TEXT"},  # JSON
        "response_status": {"type": "INTEGER"},
        "response_time": {"type": "INTEGER"},  # 毫秒
        "ip_address": {"type": "TEXT"},
        "user_agent": {"type": "TEXT"},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["request_id", "api_key_id", "created_at"]
})

SCHEMA.add_table("webhooks", {
    "description": "Webhook配置表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "webhook_id": {"type": "TEXT", "unique": True, "not_null": True},
        "name": {"type": "TEXT", "not_null": True},
        "url": {"type": "TEXT", "not_null": True},
        "secret": {"type": "TEXT"},
        "events": {"type": "TEXT"},  # JSON数组
        "headers": {"type": "TEXT"},  # JSON对象
        "is_active": {"type": "INTEGER", "default": 1},
        "user_id": {"type": "TEXT", "not_null": True},
        "success_count": {"type": "INTEGER", "default": 0},
        "failure_count": {"type": "INTEGER", "default": 0},
        "last_triggered_at": {"type": "INTEGER"},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["webhook_id", "is_active"]
})

# ----------------------------------------------------------
# 12. 缓存相关表
# ----------------------------------------------------------

SCHEMA.add_table("cache", {
    "description": "缓存表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "cache_key": {"type": "TEXT", "unique": True, "not_null": True},
        "value": {"type": "TEXT", "not_null": True},
        "category": {"type": "TEXT"},
        "ttl": {"type": "INTEGER", "not_null": True},
        "hits": {"type": "INTEGER", "default": 0},
        "created_at": {"type": "INTEGER", "not_null": True},
        "expires_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["cache_key", "category", "expires_at"]
})

# ----------------------------------------------------------
# 13. 密码重置相关表
# ----------------------------------------------------------

SCHEMA.add_table("password_resets", {
    "description": "密码重置表",
    "fields": {
        "id": {"type": "INTEGER", "primary": True, "autoincrement": True},
        "reset_id": {"type": "TEXT", "unique": True, "not_null": True},
        "user_id": {"type": "TEXT", "not_null": True},
        "token": {"type": "TEXT", "not_null": True},
        "email": {"type": "TEXT", "not_null": True},
        "status": {"type": "TEXT", "default": "pending"},  # pending, verified, completed, expired
        "expires_at": {"type": "INTEGER", "not_null": True},
        "completed_at": {"type": "INTEGER"},
        "created_at": {"type": "INTEGER", "not_null": True}
    },
    "indexes": ["reset_id", "user_id", "token", "status"]
})

# 输出完整架构
if __name__ == "__main__":
    print(SCHEMA.generate_sql())
