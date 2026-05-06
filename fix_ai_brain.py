#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用现有脑库修复系统
功能：
1. 清理AI脑库中的重复数据
2. 添加有用的AI脑库特征
3. 优化系统服务配置

import os
import sys
import sqlite3
import logging
from datetime import datetime

# 配置日志
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logs')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'fix_ai_brain.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('fix_ai_brain')

def fix_ai_brain():
    """修复AI脑库"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Database', 'ai_brain.db')

    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        logger.info("🧠 开始修复AI脑库...")

        # 1. 清理重复的AI技术数据
        logger.info("🔍 清理重复的AI技术数据...")

        # 创建临时表存储去重后的数据（按名称和描述分组，保留最新的记录）
        cursor.execute('''
            CREATE TEMPORARY TABLE temp_ai_technologies AS
            SELECT
                name,
                description,
                category,
                relevance,
                implementation_path,
                source,
                MAX(crawled_at) as crawled_at,
                status
            FROM ai_technologies
            GROUP BY name, description
        ''')

        # 删除原表数据
        cursor.execute('DELETE FROM ai_technologies')

        # 将去重后的数据插入原表
        cursor.execute('''
            SELECT name, description, category, relevance, implementation_path, source, crawled_at, status
            FROM temp_ai_technologies
        ''')

        cursor.execute('DROP TABLE temp_ai_technologies')

        conn.commit()
        logger.info("✅ AI技术数据去重完成")

        # 2. 清理重复的AI成功案例数据
        logger.info("🔍 清理重复的AI成功案例数据...")

        # 创建临时表存储去重后的数据（按名称和描述分组，保留最新的记录）
            CREATE TEMPORARY TABLE temp_ai_success_cases AS
                name,
                description,
                industry,
                results,
                MAX(crawled_at) as crawled_at,
            FROM ai_success_cases
            GROUP BY name, description
        ''')

        cursor.execute('DELETE FROM ai_success_cases')
        # 将去重后的数据插入原表
        cursor.execute('''
            INSERT INTO ai_success_cases (name, description, industry, implementation_details, results, source, crawled_at, adapted)
        ''')
        # 删除临时表
        cursor.execute('DROP TABLE temp_ai_success_cases')

        logger.info("✅ AI成功案例数据去重完成")

        # 3. 添加有用的AI脑库特征

        ai_features = [
            {
                "feature_name": "自动服务监控",
                "feature_type": "system",
                "description": "自动监控系统服务状态，出现异常时自动重启",
                "implementation_code": "# 服务监控逻辑\ndef monitor_service(service_name, port):\n    # 实现服务监控和自动重启逻辑\n    pass",
            },
            {
                "feature_name": "AI技术推荐",
                "description": "根据项目需求推荐合适的AI技术",
                "implementation_code": "# AI技术推荐逻辑\ndef recommend_ai_technology(project_requirements):\n    # 实现AI技术推荐算法\n    pass",
                "version": "1.0.0"
            },
            {
                "feature_name": "成功案例适配",
                "feature_type": "ai",
                "description": "将AI成功案例适配到当前系统",
                "implementation_code": "# 成功案例适配逻辑\ndef adapt_success_case(case_id, system_config):\n    # 实现成功案例适配算法\n    pass",
                "version": "1.0.0"
            },
            {
                "feature_name": "系统自动升级",
                "feature_type": "system",
                "description": "根据国际规则自动升级系统版本",
                "version": "1.0.0"
            },
            {
                "feature_name": "云端功能集成",
                "feature_type": "cloud",
                "version": "1.0.0"
        ]
        # 插入AI脑库特征（如果不存在）
        added_count = 0
                SELECT COUNT(*) FROM ai_brain_features WHERE feature_name = ?
            ''', (feature["feature_name"],))
                # 插入新特征
                    INSERT INTO ai_brain_features (feature_name, feature_type, description, implementation_code, version, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    feature["feature_type"],
                    feature["description"],
                    feature["implementation_code"],
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                added_count += 1

        conn.commit()
        logger.info(f"✅ AI脑库特征添加完成，新增 {added_count} 个特征")

        # 4. 清理重复的AI脑库特征数据
        logger.info("🔍 清理重复的AI脑库特征数据...")

        # 创建临时表存储去重后的数据（按feature_name分组，保留最新的记录）
        cursor.execute('''
            CREATE TEMPORARY TABLE temp_ai_brain_features AS
            SELECT
                feature_type,
                description,
                implementation_code,
                version,
                MAX(created_at) as created_at,
                MAX(updated_at) as updated_at
            FROM ai_brain_features
        ''')

        # 删除原表数据

        cursor.execute('''
            INSERT INTO ai_brain_features (feature_name, feature_type, description, implementation_code, version, created_at, updated_at)
            SELECT feature_name, feature_type, description, implementation_code, version, created_at, updated_at
        ''')

        # 删除临时表
        cursor.execute('DROP TABLE temp_ai_brain_features')

        conn.commit()
        logger.info("✅ AI脑库特征数据去重完成")

        logger.info("📊 修复后的AI脑库状态:")

        # 统计AI技术数量
        cursor.execute('SELECT COUNT(*) FROM ai_technologies')
        tech_count = cursor.fetchone()[0]

        # 统计AI成功案例数量
        cursor.execute('SELECT COUNT(*) FROM ai_success_cases')
        logger.info(f"  AI成功案例数量: {case_count}")
        # 统计AI脑库特征数量
        cursor.execute('SELECT COUNT(*) FROM ai_brain_features')
        feature_count = cursor.fetchone()[0]
        logger.info(f"  AI脑库特征数量: {feature_count}")

        # 显示AI脑库特征详情
        cursor.execute('SELECT feature_name, feature_type, version FROM ai_brain_features')
        features = cursor.fetchall()
        for feature in features:
            logger.info(f"    - {feature[0]} (类型: {feature[1]}, 版本: {feature[2]})")

        logger.info("✅ AI脑库修复完成")
    except Exception as e:
        logger.error(f"❌ AI脑库修复失败: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def main():
    logger.info("🚀 开始使用现有脑库修复系统...")

    # 修复AI脑库
    fix_ai_brain()

    logger.info("✅ 系统修复完成")

if __name__ == "__main__":
    main()
