# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
矩阵题库管理系统 - 数据库初始化
"""

import sqlite3
import os
from datetime import datetime
import json

DB_PATH = 'app.db'


def init_matrix_tables():
    """初始化矩阵题库管理表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. 矩阵类型表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matrix_types (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            dimensions TEXT,  -- JSON数组定义维度
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    
    # 2. 矩阵数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matrix_data (
            id TEXT PRIMARY KEY,
            matrix_type_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            data TEXT,  -- JSON格式存储矩阵数据
            metadata TEXT,  -- 附加元数据
            version INTEGER DEFAULT 1,
            created_by TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (matrix_type_id) REFERENCES matrix_types(id)
        )
    ''')
    
    # 3. 题库知识点表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_points (
            id TEXT PRIMARY KEY,
            subject TEXT NOT NULL,
            grade TEXT NOT NULL,
            chapter TEXT,
            name TEXT NOT NULL,
            description TEXT,
            difficulty INTEGER DEFAULT 1,  -- 1-5
            importance INTEGER DEFAULT 3,  -- 1-5
            tags TEXT,  -- JSON数组
            parent_id TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    
    # 4. 能力维度表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ability_dimensions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,  -- 认知、技能、情感等
            weight REAL DEFAULT 1.0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    
    # 5. 题库-矩阵映射表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS question_matrix_mapping (
            id TEXT PRIMARY KEY,
            question_id TEXT NOT NULL,
            matrix_data_id TEXT NOT NULL,
            dimension_values TEXT,  -- JSON对象,各维度的值
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (matrix_data_id) REFERENCES matrix_data(id)
        )
    ''')
    
    # 6. 知识点-能力映射表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_ability_mapping (
            id TEXT PRIMARY KEY,
            knowledge_point_id TEXT NOT NULL,
            ability_dimension_id TEXT NOT NULL,
            strength REAL DEFAULT 0.5,  -- 关联强度 0-1
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_points(id),
            FOREIGN KEY (ability_dimension_id) REFERENCES ability_dimensions(id)
        )
    ''')
    
    # 7. 学生能力画像表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_ability_profile (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            knowledge_point_id TEXT,
            ability_dimension_id TEXT,
            score REAL,
            level TEXT,
            trend TEXT,  -- improving, stable, declining
            last_updated TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_points(id),
            FOREIGN KEY (ability_dimension_id) REFERENCES ability_dimensions(id)
        )
    ''')
    
    # 8. 组卷策略表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_generation_strategy (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            subject TEXT,
            grade TEXT,
            matrix_config TEXT,  -- JSON配置矩阵要求
            constraints TEXT,  -- JSON约束条件
            is_default INTEGER DEFAULT 0,
            created_by TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    
    # 9. 矩阵分析报告表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matrix_analysis_report (
            id TEXT PRIMARY KEY,
            report_type TEXT NOT NULL,
            matrix_type_id TEXT,
            data TEXT,  -- JSON格式的分析结果
            generated_at TEXT DEFAULT (datetime('now')),
            generated_by TEXT,
            FOREIGN KEY (matrix_type_id) REFERENCES matrix_types(id)
        )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_kp_subject ON knowledge_points(subject)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_kp_grade ON knowledge_points(grade)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_qmm_question ON question_matrix_mapping(question_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_qmm_matrix ON question_matrix_mapping(matrix_data_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sap_user ON student_ability_profile(user_id)')
    
    conn.commit()
    conn.close()
    
    print("✅ 矩阵题库管理表创建成功!")


def init_default_matrix_types():
    """初始化默认的矩阵类型"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    default_types = [
        {
            'id': 'knowledge_ability',
            'name': '知识点-能力矩阵',
            'description': '知识点与能力维度的关联矩阵',
            'dimensions': json.dumps(['知识点', '能力维度', '难度', '重要性'])
        },
        {
            'id': 'difficulty_distribution',
            'name': '难度分布矩阵',
            'description': '题库在不同难度下的分布',
            'dimensions': json.dumps(['学科', '年级', '难度'])
        },
        {
            'id': 'coverage_matrix',
            'name': '知识点覆盖率矩阵',
            'description': '各知识点的题目覆盖情况',
            'dimensions': json.dumps(['学科', '年级', '知识点', '题目数量'])
        },
        {
            'id': 'student_mastery',
            'name': '学生掌握度矩阵',
            'description': '学生对各知识点的掌握情况',
            'dimensions': json.dumps(['学生', '知识点', '能力维度', '掌握度'])
        }
    ]
    
    for mt in default_types:
        cursor.execute('''
            INSERT OR REPLACE INTO matrix_types 
            (id, name, description, dimensions)
            VALUES (?, ?, ?, ?)
        ''', (mt['id'], mt['name'], mt['description'], mt['dimensions']))
    
    conn.commit()
    conn.close()
    
    print("✅ 默认矩阵类型初始化成功!")


def init_default_ability_dimensions():
    """初始化默认的能力维度"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    abilities = [
        ('memory', '记忆能力', '认知', 1.0),
        ('understanding', '理解能力', '认知', 1.2),
        ('application', '应用能力', '技能', 1.5),
        ('analysis', '分析能力', '技能', 1.3),
        ('synthesis', '综合能力', '技能', 1.4),
        ('evaluation', '评价能力', '认知', 1.1),
        ('computation', '计算能力', '技能', 1.0),
        ('reading_comprehension', '阅读理解能力', '技能', 1.2),
        ('logical_thinking', '逻辑思维能力', '认知', 1.3),
        ('creativity', '创新能力', '情感', 0.8)
    ]
    
    for aid, name, category, weight in abilities:
        cursor.execute('''
            INSERT OR REPLACE INTO ability_dimensions 
            (id, name, description, category, weight)
            VALUES (?, ?, ?, ?, ?)
        ''', (aid, name, f'{category}能力', category, weight))
    
    conn.commit()
    conn.close()
    
    print("✅ 默认能力维度初始化成功!")


def main():
    print("=" * 60)
    print("矩阵题库管理系统 - 数据库初始化")
    print("=" * 60)
    
    init_matrix_tables()
    init_default_matrix_types()
    init_default_ability_dimensions()
    
    print("\n" + "=" * 60)
    print("初始化完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
