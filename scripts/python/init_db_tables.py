#!/usr/bin/env python3
"""初始化AI自我学习相关数据库表"""

import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

tables = [
    '''
    CREATE TABLE IF NOT EXISTS self_learning_insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        insight_type TEXT,
        domain TEXT,
        topic TEXT,
        insight TEXT,
        priority TEXT,
        confidence REAL DEFAULT 0.0,
        score REAL DEFAULT 0.0,
        source TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS error_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        error_type TEXT,
        error_message TEXT,
        error_trace TEXT,
        source_file TEXT,
        source_line INTEGER,
        status TEXT DEFAULT "open",
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS brain_learning_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id TEXT UNIQUE NOT NULL,
        employee_id TEXT,
        employee_name TEXT,
        learning_type TEXT,
        domain TEXT,
        topic TEXT,
        content_summary TEXT,
        proficiency_before REAL DEFAULT 0.0,
        proficiency_after REAL DEFAULT 0.0,
        proficiency_gain REAL DEFAULT 0.0,
        learning_duration REAL DEFAULT 0.0,
        knowledge_id TEXT,
        learning_method TEXT,
        mastery_level TEXT,
        practice_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS ai_upgrade_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        upgrade_id TEXT UNIQUE NOT NULL,
        employee_id TEXT,
        employee_name TEXT,
        upgrade_type TEXT,
        upgrade_category TEXT,
        before_level INTEGER DEFAULT 0,
        after_level INTEGER DEFAULT 0,
        before_capabilities TEXT,
        after_capabilities TEXT,
        upgrade_score REAL DEFAULT 0.0,
        upgrade_data TEXT,
        upgrade_reason TEXT,
        status TEXT DEFAULT "pending",
        performed_by TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS system_maintenance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation_type TEXT,
        target TEXT,
        result TEXT,
        details TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS ai_brain_knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        knowledge_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        knowledge_type TEXT,
        source TEXT,
        tags TEXT,
        priority INTEGER DEFAULT 5,
        status TEXT DEFAULT "active",
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS ai_brain_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        knowledge_id TEXT,
        activity_type TEXT,
        details TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS brain_feeding_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feed_id TEXT UNIQUE NOT NULL,
        feed_type TEXT,
        feed_source TEXT,
        feed_data TEXT,
        knowledge_type TEXT,
        priority INTEGER DEFAULT 5,
        status TEXT DEFAULT "pending",
        scheduled_at TEXT,
        data_size INTEGER DEFAULT 0,
        tags TEXT,
        description TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS brain_feeding_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stat_date TEXT,
        total_feeds INTEGER DEFAULT 0,
        total_learnings INTEGER DEFAULT 0,
        total_upgrades INTEGER DEFAULT 0,
        total_coordinations INTEGER DEFAULT 0,
        knowledge_count INTEGER DEFAULT 0,
        active_nodes INTEGER DEFAULT 0,
        active_connections INTEGER DEFAULT 0,
        avg_proficiency REAL DEFAULT 0.0,
        avg_accuracy REAL DEFAULT 0.0,
        neural_network_density REAL DEFAULT 0.0,
        cluster_efficiency REAL DEFAULT 0.0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS learning_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_code TEXT UNIQUE NOT NULL,
        rule_name TEXT NOT NULL,
        rule_value TEXT,
        rule_type TEXT DEFAULT "learning",
        learning_domain TEXT,
        learning_priority TEXT DEFAULT "normal",
        discovery_source TEXT,
        confidence REAL DEFAULT 0.0,
        execution_count INTEGER DEFAULT 0,
        last_executed TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        description TEXT
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS learning_policy_executions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_id TEXT NOT NULL,
        policy_name TEXT NOT NULL,
        execution_type TEXT,
        target_domain TEXT,
        target_employees TEXT,
        execution_params TEXT,
        execution_result TEXT,
        success INTEGER DEFAULT 0,
        executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS network_learning_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_name TEXT NOT NULL,
        source_url TEXT NOT NULL,
        category TEXT,
        domain TEXT,
        keywords TEXT,
        last_collected TEXT,
        success_count INTEGER DEFAULT 0,
        fail_count INTEGER DEFAULT 0,
        status TEXT DEFAULT "active",
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS network_learning_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        knowledge_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT,
        domain TEXT,
        source_url TEXT,
        source_name TEXT,
        confidence REAL DEFAULT 0.0,
        extracted_keywords TEXT,
        status TEXT DEFAULT "collected",
        fed_to_brain INTEGER DEFAULT 0,
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        fed_at TEXT
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS system_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_code TEXT UNIQUE NOT NULL,
        rule_name TEXT NOT NULL,
        rule_value TEXT,
        rule_type TEXT DEFAULT "system",
        description TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS neural_network_nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id TEXT UNIQUE NOT NULL,
        node_type TEXT,
        node_name TEXT,
        node_layer INTEGER DEFAULT 0,
        node_layer_name TEXT,
        activation_function TEXT DEFAULT "relu",
        weight REAL DEFAULT 0.5,
        bias REAL DEFAULT 0.0,
        threshold REAL DEFAULT 0.5,
        status TEXT DEFAULT "active",
        processing_capacity REAL DEFAULT 100.0,
        current_load REAL DEFAULT 0.0,
        accuracy REAL DEFAULT 0.5,
        training_count INTEGER DEFAULT 0,
        last_trained TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS neural_network_connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        connection_id TEXT UNIQUE NOT NULL,
        source_node_id TEXT,
        target_node_id TEXT,
        connection_type TEXT DEFAULT "synapse",
        weight REAL DEFAULT 0.5,
        signal_strength REAL DEFAULT 0.0,
        status TEXT DEFAULT "active",
        learning_rate REAL DEFAULT 0.01,
        activation_count INTEGER DEFAULT 0,
        last_activated TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS ai_employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        employee_code TEXT,
        status TEXT DEFAULT "active",
        accuracy REAL DEFAULT 0.5,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS ai_employee_learning (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT UNIQUE NOT NULL,
        domain TEXT,
        total_topics INTEGER DEFAULT 0,
        mastered_topics INTEGER DEFAULT 0,
        avg_proficiency REAL DEFAULT 0.0,
        total_learning_hours REAL DEFAULT 0.0,
        learning_streak INTEGER DEFAULT 0,
        last_learning_time TEXT,
        knowledge_base TEXT,
        learning_history TEXT,
        upgrade_status TEXT DEFAULT "learning",
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS cluster_coordination_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coordination_id TEXT UNIQUE NOT NULL,
        cluster_id TEXT,
        coordination_type TEXT,
        task_description TEXT,
        participating_employees TEXT,
        task_assignment TEXT,
        coordination_strategy TEXT,
        result TEXT,
        efficiency_score REAL DEFAULT 0.0,
        duration_seconds REAL DEFAULT 0.0,
        status TEXT DEFAULT "completed",
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS ai_cluster_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cluster_id TEXT UNIQUE NOT NULL,
        cluster_type TEXT,
        config TEXT,
        status TEXT DEFAULT "active",
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''',
    '''
    CREATE TABLE IF NOT EXISTS ai_cluster_employee (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cluster_id TEXT,
        employee_id TEXT,
        role TEXT,
        status TEXT DEFAULT "active",
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    '''
]

created_count = 0
for table_sql in tables:
    try:
        cursor.execute(table_sql)
        created_count += 1
    except Exception as e:
        logger.info(f"创建表失败: {e}")

conn.commit()
conn.close()

logger.info(f"✅ 成功创建 {created_count} 个数据库表")
