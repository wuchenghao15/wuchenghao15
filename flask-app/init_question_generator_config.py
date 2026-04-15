#!/usr/bin/env python3
"""
初始化题目生成器的配置项到数据库
"""

import sqlite3
import json

def init_question_generator_config():
    """初始化题目生成器配置"""
    try:
        # 连接到数据库
        conn = sqlite3.connect('primary.db')
        cursor = conn.cursor()
        
        # 题目生成相关配置项
        configs = [
            # 基础配置
            ("ai_model_type", "gpt-4o-mini", "string", "AI模型类型", 1),
            ("supported_languages", json.dumps(["japanese", "english", "chinese"]), "json", "支持的语言列表", 1),
            ("supported_categories", json.dumps(["词汇", "语法", "阅读", "听力", "写作", "口语", "翻译"]), "json", "支持的题目类别", 1),
            ("supported_difficulties", json.dumps([1, 2, 3, 4, 5]), "json", "支持的难度等级", 1),
            ("supported_question_types", json.dumps(["single", "multiple", "fill", "short_answer", "essay", "speaking", "translation"]), "json", "支持的题目类型", 1),
            ("default_question_count", "20", "number", "默认题目数量", 1),
            ("default_user_level", "3", "number", "默认用户等级", 1),
            
            # 题目类别比例配置
            ("paper_category_ratios", json.dumps({
                "placement": {"词汇": 20, "语法": 20, "阅读": 20, "听力": 20, "写作": 10, "翻译": 10},
                "diagnostic": {"词汇": 25, "语法": 25, "阅读": 20, "听力": 20, "写作": 5, "翻译": 5},
                "comprehensive": {"词汇": 15, "语法": 15, "阅读": 20, "听力": 20, "写作": 15, "口语": 10, "翻译": 5},
                "level": {
                    "1": {"词汇": 30, "语法": 30, "阅读": 20, "听力": 15, "写作": 5},
                    "2": {"词汇": 25, "语法": 25, "阅读": 20, "听力": 20, "写作": 5, "翻译": 5},
                    "3": {"词汇": 20, "语法": 20, "阅读": 20, "听力": 20, "写作": 10, "翻译": 10},
                    "4": {"词汇": 15, "语法": 15, "阅读": 25, "听力": 25, "写作": 10, "翻译": 10},
                    "5": {"词汇": 10, "语法": 10, "阅读": 30, "听力": 30, "写作": 10, "翻译": 10}
                }
            }), "json", "试卷类别比例配置", 1),
            
            # 评分标准配置
            ("scoring_criteria", json.dumps({
                "short_answer": {
                    "答案的准确性": 40,
                    "答案的完整性": 30,
                    "表达的清晰度": 20,
                    "用词的准确性": 10
                },
                "essay": {
                    "内容的完整性和深度": 30,
                    "结构的合理性和逻辑性": 25,
                    "语言表达的准确性和流畅性": 20,
                    "创意和原创性": 15,
                    "格式的正确性": 10
                },
                "speaking": {
                    "发音的准确性和清晰度": 25,
                    "语法的正确性": 25,
                    "词汇的丰富性和准确性": 20,
                    "表达的流畅性和连贯性": 20,
                    "内容的完整性和相关性": 10
                },
                "translation": {
                    "意思的准确性": 40,
                    "语言表达的流畅性": 30,
                    "用词的准确性和地道性": 20,
                    "格式的正确性": 10
                }
            }), "json", "评分标准配置", 1),
            
            # AI评分相关配置
            ("ai_scoring_enabled", "true", "boolean", "是否启用AI评分", 1),
            ("ai_scoring_threshold", "0.8", "number", "AI评分可信度阈值", 1),
            ("ai_scoring_max_time", "30", "number", "AI评分最大超时时间(秒)", 1),
            
            # 题目生成质量控制
            ("question_generation_quality", "high", "string", "题目生成质量级别", 1),
            ("question_generation_timeout", "60", "number", "题目生成最大超时时间(秒)", 1),
            
            # 题库扩展配置
            ("question_bank_expansion_enabled", "true", "boolean", "是否启用题库自动扩展", 1),
            ("question_bank_expansion_rate", "0.1", "number", "题库自动扩展比例", 1)
        ]
        
        # 插入或更新配置项
        for config_key, config_value, config_type, description, is_active in configs:
            # 先检查是否已存在
            cursor.execute("SELECT id FROM system_config WHERE config_key = ?", (config_key,))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有配置
                cursor.execute("""
                    UPDATE system_config 
                    SET config_value = ?, config_type = ?, description = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE config_key = ?
                """, (config_value, config_type, description, is_active, config_key))
                print(f"更新配置项: {config_key}")
            else:
                # 插入新配置
                cursor.execute("""
                    INSERT INTO system_config (config_key, config_value, config_type, description, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (config_key, config_value, config_type, description, is_active))
                print(f"插入配置项: {config_key}")
        
        # 提交事务
        conn.commit()
        conn.close()
        
        print("\n配置项初始化完成！")
    except Exception as e:
        print(f"初始化配置项失败: {e}")

if __name__ == "__main__":
    init_question_generator_config()
