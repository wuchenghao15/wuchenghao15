#!/usr/bin/env python3
"""
更新系统配置脚本

import sqlite3
# JSON import removed - using database
def update_system_config():
    """更新系统配置"""
    # 连接到数据库
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # 需要更新或添加的配置列表
    configs_to_update = [
        # AI配置参数
        ("ai_model_type", "gpt-4o-mini", "string", "默认使用的AI模型类型"),
        ("ai_temperature", "0.7", "number", "AI生成文本的温度参数"),
        ("ai_max_tokens", "2000", "number", "AI生成文本的最大令牌数"),

        # 题目生成配置参数
        ("supported_languages", str(["japanese", "english", "chinese"]), "array", "支持的语言列表"),
        ("supported_categories", str(["词汇", "语法", "阅读", "听力", "写作", "口语", "翻译"]), "array", "支持的题目类别列表"),
        ("supported_question_types", str(["single", "multiple", "fill", "short_answer", "essay", "speaking", "translation"]), "array", "支持的题目类型列表"),
        ("default_question_count", "20", "number", "默认题目数量"),
        ("default_user_level", "3", "number", "默认用户等级"),

        # 试卷生成配置参数
        ("paper_category_ratios", str({
            "placement": {"词汇": 20, "语法": 20, "阅读": 20, "听力": 20, "写作": 10, "翻译": 10},
            "diagnostic": {"词汇": 25, "语法": 25, "阅读": 20, "听力": 20, "写作": 5, "翻译": 5},
            "comprehensive": {"词汇": 15, "语法": 15, "阅读": 20, "听力": 20, "写作": 15, "口语": 10, "翻译": 5},
            "level": {
                "1": {"词汇": 50, "语法": 30, "阅读": 20},
                "2": {"词汇": 50, "语法": 30, "阅读": 20},
                "3": {"词汇": 40, "语法": 35, "阅读": 25},
                "4": {"词汇": 30, "语法": 30, "阅读": 40},
                "5": {"词汇": 30, "语法": 30, "阅读": 40}
            }
        }), "object", "不同测试类型的题目类别比例配置"),

        # 评分配置参数
        ("scoring_criteria", str({
            "short_answer": {"accuracy": 40, "completeness": 30, "clarity": 20, "vocabulary": 10},
            "essay": {"content": 30, "structure": 25, "language": 20, "creativity": 15, "format": 10},
            "speaking": {"pronunciation": 25, "grammar": 25, "vocabulary": 20, "fluency": 20, "relevance": 10},
            "translation": {"accuracy": 40, "fluency": 30, "naturalness": 20, "format": 10}
        }), "object", "AI评分标准配置")
    ]

    # 更新或添加配置
    for config_key, config_value, config_type, description in configs_to_update:
        # 检查配置是否已存在
        cursor.execute("SELECT id FROM system_config WHERE config_key = ?", (config_key,))
        existing_config = cursor.fetchone()

        if existing_config:
            # 更新现有配置
            cursor.execute('''
            UPDATE system_config
            SET config_value = ?, config_type = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE config_key = ?
            ''', (config_value, config_type, description, config_key))
            print(f"[INFO] 更新配置: {config_key}")
        else:
            # 添加新配置
            cursor.execute('''
            VALUES (?, ?, ?, ?)
            ''', (config_key, config_value, config_type, description))
            print(f"[INFO] 添加配置: {config_key}")

    # 提交更改并关闭连接
    conn.commit()
    conn.close()

    print("[INFO] 系统配置更新完成")

def check_updated_configs():
    """检查更新后的配置"""
    # 连接到数据库
    cursor = conn.cursor()
    # 查询所有配置
    configs = cursor.fetchall()

    print(f"[INFO] 系统配置总数: {len(configs)}")
    print("[INFO] 配置列表:")
    for config in configs:
        print(f"  {config[0]}: {config[1]} (类型: {config[2]}, 描述: {config[3]})")

    # 关闭连接
    conn.close()

if __name__ == "__main__":
    print("[INFO] 开始更新系统配置...")

    update_system_config()

    # 检查更新后的配置
    check_updated_configs()

    print("[INFO] 系统配置更新完成！")
