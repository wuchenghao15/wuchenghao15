#!/usr/bin/env python3
"""
MTSCOS AI 数据库增强脚本 v7.2.0
====================================
为16个分库添加增强表结构：
- 移动端配置表
- 通知推送队列表
- 用户设备表
- 系统配置扩展表
"""

import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLIT_DB_DIR = os.path.join(BASE_DIR, 'split_databases')

def execute_sql(db_path, sql, params=None):
    """执行SQL语句"""
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"  ✗ SQL执行失败: {e}")
        return False

def enhance_system_db():
    """增强系统数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'system.db')
    print("\n[系统数据库增强]")
    
    # 移动端配置表
    print("  - 创建移动端配置表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS mobile_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE NOT NULL,
            config_value TEXT,
            description TEXT,
            category TEXT DEFAULT 'mobile',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 通知推送队列表
    print("  - 创建通知推送队列表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS notification_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_id INTEGER,
            recipient_type TEXT DEFAULT 'user',
            title TEXT,
            content TEXT,
            priority INTEGER DEFAULT 10,
            status TEXT DEFAULT 'pending',
            push_type TEXT DEFAULT 'system',
            device_id TEXT,
            sent_at TEXT,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 用户设备表
    print("  - 创建用户设备表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS user_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            device_id TEXT UNIQUE NOT NULL,
            device_type TEXT DEFAULT 'mobile',
            device_name TEXT,
            os_type TEXT,
            os_version TEXT,
            app_version TEXT,
            push_token TEXT,
            last_active_at TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 初始化移动端配置默认数据
    print("  - 初始化移动端配置默认数据...")
    default_configs = [
        ('mobile_enabled', '1', '是否启用移动端支持', 'mobile'),
        ('mobile_viewport', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no', '移动端viewport配置', 'mobile'),
        ('mobile_theme', 'default', '移动端默认主题', 'mobile'),
        ('mobile_push_enabled', '1', '是否启用移动端推送', 'mobile'),
        ('mobile_cache_timeout', '3600', '移动端缓存超时时间(秒)', 'mobile'),
        ('mobile_max_upload_size', '10485760', '移动端最大上传大小(字节)', 'mobile'),
        ('mobile_login_expire_days', '7', '移动端登录过期天数', 'mobile'),
        ('mobile_offline_mode', '1', '是否支持离线模式', 'mobile'),
    ]
    
    for key, value, desc, category in default_configs:
        execute_sql(db_path, '''
            INSERT OR IGNORE INTO mobile_config (config_key, config_value, description, category)
            VALUES (?, ?, ?, ?)
        ''', (key, value, desc, category))
    
    print("  ✓ 系统数据库增强完成")

def enhance_auth_db():
    """增强认证数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'auth.db')
    print("\n[认证数据库增强]")
    
    # 用户登录日志表
    print("  - 创建用户登录日志表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            ip_address TEXT,
            user_agent TEXT,
            device_type TEXT,
            login_status TEXT DEFAULT 'success',
            login_time TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 多因素认证表
    print("  - 创建多因素认证表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS mfa_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            mfa_type TEXT,
            secret TEXT,
            enabled INTEGER DEFAULT 0,
            verified INTEGER DEFAULT 0,
            backup_codes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("  ✓ 认证数据库增强完成")

def enhance_question_db():
    """增强题库数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'question.db')
    print("\n[题库数据库增强]")
    
    # 题库分类扩展表
    print("  - 创建题库分类扩展表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS question_categories_ext (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            category_name TEXT,
            parent_id INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            subject TEXT,
            education_stage TEXT DEFAULT 'k12',
            grade TEXT,
            semester TEXT,
            total_questions INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 题目标签表
    print("  - 创建题目标签表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS question_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_name TEXT UNIQUE NOT NULL,
            tag_color TEXT DEFAULT '#3B82F6',
            usage_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 题目标签关联表
    print("  - 创建题目标签关联表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS question_tag_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            tag_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(question_id, tag_id)
        )
    ''')
    
    # 初始化题库分类数据
    print("  - 初始化题库分类数据...")
    categories = [
        ('成人教育-语文', 0, 1, '语文', 'adult', '', '', 0),
        ('成人教育-数学', 0, 1, '数学', 'adult', '', '', 0),
        ('成人教育-英语', 0, 1, '英语', 'adult', '', '', 0),
        ('成人教育-政治', 0, 1, '政治', 'adult', '', '', 0),
        ('成人教育-历史', 0, 1, '历史', 'adult', '', '', 0),
        ('成人教育-地理', 0, 1, '地理', 'adult', '', '', 0),
        ('成人教育-物理', 0, 1, '物理', 'adult', '', '', 0),
        ('成人教育-化学', 0, 1, '化学', 'adult', '', '', 0),
        ('成人教育-生物', 0, 1, '生物', 'adult', '', '', 0),
        ('K12-语文-小学', 0, 1, '语文', 'k12', '小学', '', 0),
        ('K12-语文-初中', 0, 1, '语文', 'k12', '初中', '', 0),
        ('K12-语文-高中', 0, 1, '语文', 'k12', '高中', '', 0),
        ('K12-数学-小学', 0, 1, '数学', 'k12', '小学', '', 0),
        ('K12-数学-初中', 0, 1, '数学', 'k12', '初中', '', 0),
        ('K12-数学-高中', 0, 1, '数学', 'k12', '高中', '', 0),
        ('K12-英语-小学', 0, 1, '英语', 'k12', '小学', '', 0),
        ('K12-英语-初中', 0, 1, '英语', 'k12', '初中', '', 0),
        ('K12-英语-高中', 0, 1, '英语', 'k12', '高中', '', 0),
        ('K12-物理-初中', 0, 1, '物理', 'k12', '初中', '', 0),
        ('K12-物理-高中', 0, 1, '物理', 'k12', '高中', '', 0),
        ('K12-化学-初中', 0, 1, '化学', 'k12', '初中', '', 0),
        ('K12-化学-高中', 0, 1, '化学', 'k12', '高中', '', 0),
        ('K12-生物-初中', 0, 1, '生物', 'k12', '初中', '', 0),
        ('K12-生物-高中', 0, 1, '生物', 'k12', '高中', '', 0),
        ('K12-历史-初中', 0, 1, '历史', 'k12', '初中', '', 0),
        ('K12-历史-高中', 0, 1, '历史', 'k12', '高中', '', 0),
        ('K12-地理-初中', 0, 1, '地理', 'k12', '初中', '', 0),
        ('K12-地理-高中', 0, 1, '地理', 'k12', '高中', '', 0),
        ('K12-政治-初中', 0, 1, '政治', 'k12', '初中', '', 0),
        ('K12-政治-高中', 0, 1, '政治', 'k12', '高中', '', 0),
    ]
    
    for name, parent_id, level, subject, stage, grade, semester, count in categories:
        execute_sql(db_path, '''
            INSERT OR IGNORE INTO question_categories_ext (category_name, parent_id, level, subject, education_stage, grade, semester, total_questions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, parent_id, level, subject, stage, grade, semester, count))
    
    print("  ✓ 题库数据库增强完成")

def enhance_ai_db():
    """增强AI数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'ai.db')
    print("\n[AI数据库增强]")
    
    # AI模型性能表
    print("  - 创建AI模型性能表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS ai_model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT,
            model_name TEXT,
            provider TEXT,
            model_type TEXT,
            performance_score REAL DEFAULT 0,
            response_time_ms INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0,
            total_requests INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            last_test_at TEXT,
            status TEXT DEFAULT 'registered',
            config TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # AI节点状态表
    print("  - 创建AI节点状态表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS ai_node_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT UNIQUE NOT NULL,
            node_name TEXT,
            node_type TEXT DEFAULT 'worker',
            address TEXT,
            status TEXT DEFAULT 'offline',
            load REAL DEFAULT 0,
            capacity INTEGER DEFAULT 10,
            active_tasks INTEGER DEFAULT 0,
            total_tasks INTEGER DEFAULT 0,
            last_heartbeat TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # AI任务队列扩展表
    print("  - 创建AI任务队列扩展表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS ai_task_queue_ext (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE NOT NULL,
            task_type TEXT,
            priority INTEGER DEFAULT 10,
            status TEXT DEFAULT 'pending',
            node_id TEXT,
            input_data TEXT,
            output_data TEXT,
            error_message TEXT,
            progress INTEGER DEFAULT 0,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            started_at TEXT,
            completed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 初始化AI模型数据
    print("  - 初始化AI模型数据...")
    ai_models = [
        ('model_gpt4', 'GPT-4', 'openai', 'llm', 95.0, 800, 99.5, 0, 0),
        ('model_gpt35', 'GPT-3.5-Turbo', 'openai', 'llm', 88.0, 300, 99.8, 0, 0),
        ('model_gpt35_16k', 'GPT-3.5-Turbo-16K', 'openai', 'llm', 87.0, 400, 99.7, 0, 0),
        ('model_claude_3_opus', 'Claude-3-Opus', 'anthropic', 'llm', 96.0, 1000, 99.2, 0, 0),
        ('model_claude_3_sonnet', 'Claude-3-Sonnet', 'anthropic', 'llm', 92.0, 600, 99.6, 0, 0),
        ('model_claude_3_haiku', 'Claude-3-Haiku', 'anthropic', 'llm', 85.0, 200, 99.9, 0, 0),
        ('model_qwen_7b', 'Qwen-7B', 'alibaba', 'llm', 80.0, 500, 98.0, 0, 0),
        ('model_qwen_14b', 'Qwen-14B', 'alibaba', 'llm', 84.0, 800, 98.5, 0, 0),
        ('model_qwen_72b', 'Qwen-72B', 'alibaba', 'llm', 88.0, 1500, 98.0, 0, 0),
        ('model_llama_3_8b', 'Llama-3-8B', 'meta', 'llm', 82.0, 400, 98.5, 0, 0),
        ('model_llama_3_70b', 'Llama-3-70B', 'meta', 'llm', 90.0, 1200, 98.0, 0, 0),
        ('model_text_embedding_ada', 'text-embedding-ada-002', 'openai', 'embedding', 92.0, 100, 99.9, 0, 0),
        ('model_text_embedding_3_small', 'text-embedding-3-small', 'openai', 'embedding', 88.0, 80, 99.9, 0, 0),
        ('model_text_embedding_3_large', 'text-embedding-3-large', 'openai', 'embedding', 94.0, 150, 99.9, 0, 0),
        ('model_whisper', 'Whisper', 'openai', 'audio', 87.0, 5000, 99.0, 0, 0),
        ('model_whisper_large', 'Whisper-Large', 'openai', 'audio', 90.0, 8000, 99.2, 0, 0),
        ('model_dall_e_3', 'DALL-E-3', 'openai', 'image', 91.0, 5000, 98.0, 0, 0),
        ('model_stable_diffusion', 'Stable Diffusion', 'stability', 'image', 85.0, 10000, 97.0, 0, 0),
        ('model_gemini_pro', 'Gemini-Pro', 'google', 'llm', 89.0, 600, 99.0, 0, 0),
        ('model_gemini_pro_vision', 'Gemini-Pro-Vision', 'google', 'multimodal', 91.0, 800, 98.5, 0, 0),
    ]
    
    for model_id, name, provider, model_type, score, response_time, success_rate, requests, errors in ai_models:
        execute_sql(db_path, '''
            INSERT OR IGNORE INTO ai_model_performance (model_id, model_name, provider, model_type, performance_score, response_time_ms, success_rate, total_requests, error_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (model_id, name, provider, model_type, score, response_time, success_rate, requests, errors))
    
    print("  ✓ AI数据库增强完成")

def enhance_exam_db():
    """增强考试数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'exam.db')
    print("\n[考试数据库增强]")
    
    # 考试统计扩展表
    print("  - 创建考试统计扩展表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS exam_statistics_ext (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            total_students INTEGER DEFAULT 0,
            completed_students INTEGER DEFAULT 0,
            avg_score REAL DEFAULT 0,
            max_score INTEGER DEFAULT 0,
            min_score INTEGER DEFAULT 0,
            pass_rate REAL DEFAULT 0,
            avg_time INTEGER DEFAULT 0,
            difficulty REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 考试错题分析表
    print("  - 创建考试错题分析表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS exam_error_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            question_id INTEGER,
            error_count INTEGER DEFAULT 0,
            total_count INTEGER DEFAULT 0,
            error_rate REAL DEFAULT 0,
            common_wrong_answers TEXT,
            analysis TEXT,
            improvement_suggestion TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("  ✓ 考试数据库增强完成")

def enhance_user_db():
    """增强用户数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'user.db')
    print("\n[用户数据库增强]")
    
    # 用户学习进度扩展表
    print("  - 创建用户学习进度扩展表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS user_learning_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            course_id INTEGER,
            chapter_id INTEGER,
            progress REAL DEFAULT 0,
            completed INTEGER DEFAULT 0,
            last_accessed_at TEXT,
            total_time INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 用户偏好设置表
    print("  - 创建用户偏好设置表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            theme TEXT DEFAULT 'default',
            language TEXT DEFAULT 'zh',
            timezone TEXT DEFAULT 'Asia/Shanghai',
            notification_enabled INTEGER DEFAULT 1,
            email_notification INTEGER DEFAULT 1,
            push_notification INTEGER DEFAULT 1,
            daily_reminder INTEGER DEFAULT 0,
            reminder_time TEXT DEFAULT '09:00',
            difficulty_level TEXT DEFAULT 'medium',
            learning_goal TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("  ✓ 用户数据库增强完成")

def enhance_log_db():
    """增强日志数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'log.db')
    print("\n[日志数据库增强]")
    
    # 操作日志扩展表
    print("  - 创建操作日志扩展表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS operation_logs_ext (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT,
            resource TEXT,
            resource_id INTEGER,
            action_type TEXT,
            detail TEXT,
            ip_address TEXT,
            user_agent TEXT,
            device_type TEXT,
            success INTEGER DEFAULT 1,
            error_message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 性能日志表
    print("  - 创建性能日志表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS performance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_type TEXT,
            metric_name TEXT,
            value REAL,
            unit TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("  ✓ 日志数据库增强完成")

def enhance_admin_db():
    """增强管理数据库"""
    db_path = os.path.join(SPLIT_DB_DIR, 'admin.db')
    print("\n[管理数据库增强]")
    
    # 系统操作日志表
    print("  - 创建系统操作日志表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS admin_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            admin_name TEXT,
            operation TEXT,
            target TEXT,
            target_id INTEGER,
            before_value TEXT,
            after_value TEXT,
            ip_address TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 系统配置变更表
    print("  - 创建系统配置变更表...")
    execute_sql(db_path, '''
        CREATE TABLE IF NOT EXISTS config_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT,
            old_value TEXT,
            new_value TEXT,
            changed_by INTEGER,
            changed_by_name TEXT,
            change_reason TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("  ✓ 管理数据库增强完成")

def run_all_enhancements():
    """运行所有数据库增强"""
    print("=" * 70)
    print("  MTSCOS AI 数据库增强脚本 v7.2.0")
    print("=" * 70)
    print(f"  执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    enhance_system_db()
    enhance_auth_db()
    enhance_question_db()
    enhance_ai_db()
    enhance_exam_db()
    enhance_user_db()
    enhance_log_db()
    enhance_admin_db()
    
    print("\n" + "=" * 70)
    print("  所有数据库增强完成！")
    print("=" * 70)

if __name__ == '__main__':
    run_all_enhancements()