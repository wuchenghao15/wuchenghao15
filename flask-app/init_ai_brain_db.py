#!/usr/bin/env python3
"""
AI脑库数据库初始化脚本
创建AI脑库相关的数据库表
"""

import sqlite3
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('init_ai_brain_db.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('init_ai_brain_db')

def init_ai_brain_db():
    """初始化AI脑库数据库表"""
    # 获取数据库路径
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    
    logger.info(f"开始初始化AI脑库数据库，路径: {db_path}")
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 创建ai_brain_knowledge表
        create_knowledge_table = """
        CREATE TABLE IF NOT EXISTS ai_brain_knowledge (
            knowledge_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            knowledge_type TEXT NOT NULL,
            source TEXT NOT NULL,
            source_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            tags TEXT,
            priority INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE
        )
        """
        cursor.execute(create_knowledge_table)
        logger.info("已创建ai_brain_knowledge表")
        
        # 创建ai_brain_activity表
        create_activity_table = """
        CREATE TABLE IF NOT EXISTS ai_brain_activity (
            activity_id TEXT PRIMARY KEY,
            activity_type TEXT NOT NULL,
            description TEXT NOT NULL,
            source TEXT NOT NULL,
            source_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
        """
        cursor.execute(create_activity_table)
        logger.info("已创建ai_brain_activity表")
        
        # 创建索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_ai_brain_knowledge_type ON ai_brain_knowledge(knowledge_type)",
            "CREATE INDEX IF NOT EXISTS idx_ai_brain_knowledge_source ON ai_brain_knowledge(source)",
            "CREATE INDEX IF NOT EXISTS idx_ai_brain_knowledge_created ON ai_brain_knowledge(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_ai_brain_activity_type ON ai_brain_activity(activity_type)",
            "CREATE INDEX IF NOT EXISTS idx_ai_brain_activity_created ON ai_brain_activity(created_at)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        logger.info("已创建所有必要的索引")
        
        # 提交更改
        conn.commit()
        logger.info("AI脑库数据库初始化完成")
        
        # 插入示例数据
        insert_sample_data(cursor)
        conn.commit()
        logger.info("已插入示例数据")
        
        return True
    except Exception as e:
        logger.error(f"初始化AI脑库数据库失败: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def insert_sample_data(cursor):
    """插入示例数据"""
    logger.info("开始插入示例数据...")
    
    # 示例知识数据
    sample_knowledge = [
        {
            'knowledge_id': 'knowledge-0001',
            'title': 'AI学习案例适配方法',
            'content': 'AI学习案例适配是指将已有的AI案例适配到不同的应用场景中。主要包括以下步骤：1. 分析原案例的核心技术点；2. 评估目标场景的适配性；3. 调整模型和算法；4. 测试和验证。通过这种方法，可以快速将成熟的AI案例应用到新的场景中，提高开发效率。',
            'knowledge_type': 'method',
            'source': 'AI案例库',
            'source_id': 'https://ai.example.com/cases/1',
            'tags': '["AI", "学习案例", "适配方法"]',
            'priority': 5
        },
        {
            'knowledge_id': 'knowledge-0002',
            'title': 'AI智能升级脑库成功案例',
            'content': '某企业通过AI智能升级脑库，实现了以下成果：1. 知识库容量提升50%；2. 知识检索准确率达到95%；3. 智能推荐系统的点击率提升30%。该案例采用了自动化爬取和智能分类技术，实现了脑库的持续更新和优化。',
            'knowledge_type': 'case_study',
            'source': 'AI案例库',
            'source_id': 'https://ai.example.com/cases/2',
            'tags': '["AI", "脑库升级", "成功案例"]',
            'priority': 5
        },
        {
            'knowledge_id': 'knowledge-0003',
            'title': '机器学习模型适配技术',
            'content': '机器学习模型适配技术包括模型压缩、迁移学习和联邦学习等。模型压缩可以减小模型体积，提高部署效率；迁移学习可以将预训练模型应用到新的任务中；联邦学习可以在保护数据隐私的前提下进行模型训练。这些技术可以帮助企业快速将AI模型部署到不同的设备和场景中。',
            'knowledge_type': 'method',
            'source': 'AI案例库',
            'source_id': 'https://ai.example.com/cases/3',
            'tags': '["机器学习", "模型适配", "迁移学习"]',
            'priority': 4
        }
    ]
    
    # 插入示例知识
    insert_knowledge_sql = """
    INSERT OR IGNORE INTO ai_brain_knowledge (
        knowledge_id, title, content, knowledge_type, source, source_id, tags, priority
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    for knowledge in sample_knowledge:
        cursor.execute(insert_knowledge_sql, (
            knowledge['knowledge_id'],
            knowledge['title'],
            knowledge['content'],
            knowledge['knowledge_type'],
            knowledge['source'],
            knowledge['source_id'],
            knowledge['tags'],
            knowledge['priority']
        ))
    
    # 示例活动日志
    sample_activities = [
        {
            'activity_id': 'activity-0001',
            'activity_type': 'knowledge_added',
            'description': '添加示例知识: AI学习案例适配方法',
            'source': '系统初始化',
            'source_id': 'init_script',
            'metadata': '{"init": true}'
        }
    ]
    
    # 插入示例活动
    insert_activity_sql = """
    INSERT OR IGNORE INTO ai_brain_activity (
        activity_id, activity_type, description, source, source_id, metadata
    ) VALUES (?, ?, ?, ?, ?, ?)
    """
    
    for activity in sample_activities:
        cursor.execute(insert_activity_sql, (
            activity['activity_id'],
            activity['activity_type'],
            activity['description'],
            activity['source'],
            activity['source_id'],
            activity['metadata']
        ))
    
    logger.info(f"已插入 {len(sample_knowledge)} 条示例知识和 {len(sample_activities)} 条示例活动日志")

if __name__ == '__main__':
    init_ai_brain_db()
