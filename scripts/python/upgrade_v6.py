#!/usr/bin/env python3
import sqlite3
import os
import time
from datetime import datetime

DB_DIR = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/split_databases'

def upgrade_system_version():
    logger.info("=== 开始系统版本升级 ===")
    
    system_db = os.path.join(DB_DIR, 'system.db')
    conn = sqlite3.connect(system_db)
    cursor = conn.cursor()
    
    cursor.execute(""" CREATE TABLE IF NOT EXISTS system_version_history ( id INTEGER PRIMARY KEY AUTOINCREMENT, version TEXT NOT NULL, previous_version TEXT, upgrade_date TEXT NOT NULL, description TEXT, status TEXT DEFAULT 'completed' ) """)
    
    cursor.execute("PRAGMA table_info(system_version_history)")
    cols = [c[1] for c in cursor.fetchall()]
    if 'previous_version' not in cols:
        cursor.execute("ALTER TABLE system_version_history ADD COLUMN previous_version TEXT")
    if 'upgrade_date' not in cols:
        cursor.execute("ALTER TABLE system_version_history ADD COLUMN upgrade_date TEXT")
    if 'description' not in cols:
        cursor.execute("ALTER TABLE system_version_history ADD COLUMN description TEXT")
    if 'status' not in cols:
        cursor.execute("ALTER TABLE system_version_history ADD COLUMN status TEXT DEFAULT 'completed'")
    
    current_version = "6.0.0"
    previous_version = "5.3.0"
    
    cursor.execute(""" INSERT INTO system_version_history (version, previous_version, upgrade_date, description) VALUES (?, ?, ?, ?) """, (current_version, previous_version, datetime.now().isoformat(),
          "系统全面升级：数据库拆分、权限规则增强、题库升级、前端页面优化"))
    
    cursor.execute(""" CREATE TABLE IF NOT EXISTS system_version ( id INTEGER PRIMARY KEY AUTOINCREMENT, version TEXT NOT NULL, major_version INTEGER, minor_version INTEGER, patch_version INTEGER, build_number TEXT, build_date TEXT, codename TEXT, status TEXT DEFAULT 'stable', updated_at TEXT ) """)
    
    cursor.execute("SELECT COUNT(*) FROM system_version")
    count = cursor.fetchone()[0]
    
    if count == 0:
        cursor.execute(""" INSERT INTO system_version (version, major_version, minor_version, patch_version, build_number, build_date, codename, status, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) """, (current_version, 6, 0, 0, "", datetime.now().strftime('%Y-%m-%d'),
              "Distributed Database Edition", "stable", datetime.now().isoformat()))
    else:
        cursor.execute(""" UPDATE system_version SET version = ?, major_version = ?, minor_version = ?, patch_version = ?, build_date = ?, codename = ?, status = ?, updated_at = ? WHERE id = 1 """, (current_version, 6, 0, 0, datetime.now().strftime('%Y-%m-%d'),
              "Distributed Database Edition", "stable", datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    logger.info(f"版本已升级到 {current_version}")
    logger.info("版本历史记录已创建")

def upgrade_permissions():
    logger.info("\n=== 升级权限规则 ===")
    
    auth_db = os.path.join(DB_DIR, 'auth.db')
    conn = sqlite3.connect(auth_db)
    cursor = conn.cursor()
    
    cursor.execute(""" CREATE TABLE IF NOT EXISTS permission_groups ( id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, description TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP ) """)
    
    permission_groups = [
        ('系统管理', '系统配置、用户管理、权限管理'),
        ('考试管理', '创建考试、管理试卷、查看成绩'),
        ('题库管理', '添加题目、编辑题目、题目分类'),
        ('学习管理', '学习记录、学习进度、学习报告'),
        ('AI功能', 'AI助手、智能推荐、自动批改'),
        ('硬件管理', '硬件设备、设备授权、设备监控'),
        ('监考管理', '监考配置、作弊检测、监考记录'),
        ('数据分析', '数据统计、报表分析、可视化'),
    ]
    
    for name, desc in permission_groups:
        cursor.execute("INSERT OR IGNORE INTO permission_groups (name, description) VALUES (?, ?)", (name, desc))
    
    cursor.execute(""" CREATE TABLE IF NOT EXISTS role_permission_groups ( role_id INTEGER, group_id INTEGER, can_read INTEGER DEFAULT 1, can_write INTEGER DEFAULT 0, can_delete INTEGER DEFAULT 0, PRIMARY KEY (role_id, group_id) ) """)
    
    cursor.execute("PRAGMA table_info(permissions)")
    perm_cols = [c[1] for c in cursor.fetchall()]
    if 'group_id' not in perm_cols:
        cursor.execute("ALTER TABLE permissions ADD COLUMN group_id INTEGER DEFAULT 1")
    if 'description' not in perm_cols:
        cursor.execute("ALTER TABLE permissions ADD COLUMN description TEXT")
    
    new_permissions = [
        ('admin_app_access', '访问管理后台', 1),
        ('system_config_edit', '编辑系统配置', 1),
        ('user_management', '用户管理', 1),
        ('permission_management', '权限管理', 1),
        ('exam_create', '创建考试', 2),
        ('exam_edit', '编辑考试', 2),
        ('exam_delete', '删除考试', 2),
        ('exam_view_results', '查看考试成绩', 2),
        ('question_add', '添加题目', 3),
        ('question_edit', '编辑题目', 3),
        ('question_delete', '删除题目', 3),
        ('question_export', '导出题目', 3),
        ('learning_view', '查看学习记录', 4),
        ('learning_report', '生成学习报告', 4),
        ('ai_chat', 'AI聊天', 5),
        ('ai_generate', 'AI生成', 5),
        ('hardware_manage', '硬件管理', 6),
        ('hardware_activate', '硬件激活', 6),
        ('proctor_monitor', '监考监控', 7),
        ('proctor_alert', '监考告警', 7),
        ('data_analytics', '数据分析', 8),
        ('data_export', '数据导出', 8),
    ]
    
    for code, name, group_id in new_permissions:
        cursor.execute("INSERT OR IGNORE INTO permissions (permission_code, permission_name, description, group_id) VALUES (?, ?, ?, ?)",
                      (code, name, name, group_id))
    
    role_permissions = {
        'super_admin': ['admin_app_access', 'system_config_edit', 'user_management', 'permission_management',
                        'exam_create', 'exam_edit', 'exam_delete', 'exam_view_results',
                        'question_add', 'question_edit', 'question_delete', 'question_export',
                        'learning_view', 'learning_report', 'ai_chat', 'ai_generate',
                        'hardware_manage', 'hardware_activate', 'proctor_monitor', 'proctor_alert',
                        'data_analytics', 'data_export'],
        'admin': ['admin_app_access', 'user_management', 'exam_create', 'exam_edit', 'exam_view_results',
                  'question_add', 'question_edit', 'learning_view', 'learning_report', 'ai_chat',
                  'data_analytics'],
        'teacher': ['exam_create', 'exam_edit', 'exam_view_results', 'question_add', 'question_edit',
                    'learning_view', 'learning_report', 'ai_chat'],
        'hardware_admin': ['hardware_manage', 'hardware_activate', 'admin_app_access'],
        'researcher': ['learning_view', 'learning_report', 'ai_chat', 'ai_generate', 'data_analytics', 'data_export'],
        'designer': ['question_add', 'question_edit', 'ai_generate'],
        'student': ['exam_view_results', 'learning_view', 'ai_chat'],
    }
    
    for role_name, perms in role_permissions.items():
        for perm_code in perms:
            cursor.execute("INSERT OR IGNORE INTO role_permissions (role_name, permission_code) VALUES (?, ?)", 
                          (role_name, perm_code))
    
    conn.commit()
    conn.close()
    
    logger.info("权限规则升级完成")

def upgrade_question_bank():
    logger.info("\n=== 升级题库结构 ===")
    
    question_db = os.path.join(DB_DIR, 'question.db')
    conn = sqlite3.connect(question_db)
    cursor = conn.cursor()
    
    cursor.execute(""" CREATE TABLE IF NOT EXISTS question_difficulty ( id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT NOT NULL UNIQUE, name TEXT NOT NULL, weight REAL DEFAULT 1.0, description TEXT ) """)
    
    difficulties = [
        ('easy', '简单', 0.5, '基础知识点'),
        ('medium', '中等', 1.0, '综合知识点'),
        ('hard', '困难', 1.5, '复杂综合题'),
        ('expert', '专家', 2.0, '挑战性题目'),
    ]
    
    for level, name, weight, desc in difficulties:
        cursor.execute("INSERT OR IGNORE INTO question_difficulty (level, name, weight, description) VALUES (?, ?, ?, ?)",
                      (level, name, weight, desc))
    
    cursor.execute(""" CREATE TABLE IF NOT EXISTS question_source ( id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, description TEXT, url TEXT ) """)
    
    sources = [
        ('gaokao', '高考真题', '高考历年真题'),
        ('zhongkao', '中考真题', '中考历年真题'),
        ('school', '学校题库', '学校自建题库'),
        ('textbook', '教材习题', '教材配套习题'),
        ('ai_generated', 'AI生成', 'AI自动生成题目'),
        ('teacher', '教师上传', '教师手动上传'),
    ]
    
    for name, desc, url in sources:
        cursor.execute("INSERT OR IGNORE INTO question_source (name, description, url) VALUES (?, ?, ?)", 
                      (name, desc, url))
    
    cursor.execute(""" CREATE TABLE IF NOT EXISTS question_format ( id INTEGER PRIMARY KEY AUTOINCREMENT, format TEXT NOT NULL UNIQUE, name TEXT NOT NULL, description TEXT ) """)
    
    formats = [
        ('single', '单选题', '只有一个正确答案'),
        ('multiple', '多选题', '有多个正确答案'),
        ('judge', '判断题', '对或错'),
        ('fill', '填空题', '填写答案'),
        ('short', '简答题', '简短回答'),
        ('essay', '论述题', '详细论述'),
        ('calculation', '计算题', '需要计算'),
        ('programming', '编程题', '编写代码'),
    ]
    
    for fmt, name, desc in formats:
        cursor.execute("INSERT OR IGNORE INTO question_format (format, name, description) VALUES (?, ?, ?)", 
                      (fmt, name, desc))
    
    try:
        cursor.execute("ALTER TABLE questions ADD COLUMN difficulty_id INTEGER")
    except Exception as e:
        pass
    
    try:
        cursor.execute("ALTER TABLE questions ADD COLUMN source_id INTEGER")
    except Exception as e:
        pass
    
    try:
        cursor.execute("ALTER TABLE questions ADD COLUMN format_id INTEGER")
    except Exception as e:
        pass
    
    try:
        cursor.execute("ALTER TABLE questions ADD COLUMN quality_score REAL DEFAULT 0.0")
    except Exception as e:
        pass
    
    try:
        cursor.execute("ALTER TABLE questions ADD COLUMN usage_count INTEGER DEFAULT 0")
    except Exception as e:
        pass
    
    try:
        cursor.execute("ALTER TABLE questions ADD COLUMN last_used_date TEXT")
    except Exception as e:
        pass
    
    conn.commit()
    conn.close()
    
    logger.info("题库结构升级完成")

def main():
    upgrade_system_version()
    upgrade_permissions()
    upgrade_question_bank()
    
    logger.info("\n=== 系统升级完成 ===")
    logger.info("版本: v6.0.0")
    logger.info("代号: Distributed Database Edition")
    logger.info("日期:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

if __name__ == '__main__':
    main()



