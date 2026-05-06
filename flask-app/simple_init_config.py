#!/usr/bin/env python3
"""
简单的系统配置初始化脚本

import os
import sys
import sqlite3

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_system_config_table():
    """创建系统配置表"""
    # 连接到数据库
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # 创建系统配置表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key VARCHAR(100) UNIQUE NOT NULL,
        value TEXT,
        description VARCHAR(255),
        category VARCHAR(50),
        data_type VARCHAR(20),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 提交更改并关闭连接
    conn.commit()
    conn.close()

    print("[INFO] 系统配置表创建成功")

def init_default_configs():
    """初始化默认系统配置"""
    # 连接到数据库
    cursor = conn.cursor()
    # 默认配置列表
        # AI配置参数
        ("ai_model_type", "gpt-4o-mini", "默认使用的AI模型类型", "ai_config", "string", True),
        ("ai_api_key", "", "AI API密钥", "ai_config", "string", True),
        ("ai_temperature", "0.7", "AI生成文本的温度参数", "ai_config", "number", True),
        ("ai_max_tokens", "2000", "AI生成文本的最大令牌数", "ai_config", "number", True),

        # 应用配置参数
        ("app_name", "MTSCOS AI Project", "应用名称", "app_config", "string", True),
        ("app_version", "1.0.0", "应用版本", "app_config", "string", True),
        ("app_port", "8888", "应用默认端口", "app_config", "number", True),
        ("debug_mode", "true", "调试模式开关", "app_config", "boolean", True),

        # 题目生成配置参数
        ("supported_languages", '["japanese", "english", "chinese"]', "支持的语言列表", "question_config", "array", True),
        ("supported_categories", '["词汇", "语法", "阅读", "听力", "写作", "口语", "翻译"]', "支持的题目类别列表", "question_config", "array", True),
        ("supported_question_types", '["single", "multiple", "fill", "short_answer", "essay", "speaking", "translation"]', "支持的题目类型列表", "question_config", "array", True),
        ("default_question_count", "20", "默认题目数量", "question_config", "number", True),
        ("default_user_level", "3", "默认用户等级", "question_config", "number", True),

        # 试卷生成配置参数
        ("paper_category_ratios", '{"placement": {"词汇": 20, "语法": 20, "阅读": 20, "听力": 20, "写作": 10, "翻译": 10}, "diagnostic": {"词汇": 25, "语法": 25, "阅读": 20, "听力": 20, "写作": 5, "翻译": 5}, "comprehensive": {"词汇": 15, "语法": 15, "阅读": 20, "听力": 20, "写作": 15, "口语": 10, "翻译": 5}, "level": {"1": {"词汇": 50, "语法": 30, "阅读": 20}, "2": {"词汇": 50, "语法": 30, "阅读": 20}, "3": {"词汇": 40, "语法": 35, "阅读": 25}, "4": {"词汇": 30, "语法": 30, "阅读": 40}, "5": {"词汇": 30, "语法": 30, "阅读": 40}}}', "不同测试类型的题目类别比例配置", "paper_config", "object", True),
        ("paper_difficulty_adjustment", '{"max_difficulty_increase": 1, "max_difficulty_decrease": 1}', "试卷难度调整配置", "paper_config", "object", True),

        # 评分配置参数
        ("scoring_criteria", '{"short_answer": {"accuracy": 40, "completeness": 30, "clarity": 20, "vocabulary": 10}, "essay": {"content": 30, "structure": 25, "language": 20, "creativity": 15, "format": 10}, "speaking": {"pronunciation": 25, "grammar": 25, "vocabulary": 20, "fluency": 20, "relevance": 10}, "translation": {"accuracy": 40, "fluency": 30, "naturalness": 20, "format": 10}}', "AI评分标准配置", "scoring_config", "object", True)
    ]

    # 插入或更新默认配置
    for config in default_configs:
        cursor.execute('''
        INSERT OR REPLACE INTO system_config (key, value, description, category, data_type, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', config)
    # 提交更改并关闭连接
    conn.commit()
    conn.close()

    print("[INFO] 默认系统配置初始化成功")
if __name__ == "__main__":

    create_system_config_table()

    # 初始化默认配置

    print("[INFO] 系统配置初始化完成！")
