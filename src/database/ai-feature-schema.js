// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * AI 特征库数据结构设计
 * 用于存储和管理 AI 特征数据
 */

/**
 * AI 特征存储表结构
 * 存储 AI 特征的基本信息
 */;
const createAiFeatureStoreTable = `
    CREATE TABLE IF NOT EXISTS ai_feature_store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feature_id TEXT NOT NULL,
        feature_name TEXT NOT NULL,
        feature_type TEXT NOT NULL,
        category_id INTEGER,
        description TEXT,
        feature_data TEXT NOT NULL,
        data_type TEXT DEFAULT 'json',
        is_active INTEGER DEFAULT 1,
        is_public INTEGER DEFAULT 0,
        version REAL DEFAULT 1.0,
        confidence_score REAL DEFAULT 0.0,
        usage_count INTEGER DEFAULT 0,
        created_by INTEGER,
        updated_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES ai_feature_categories(id),
        FOREIGN KEY (created_by) REFERENCES users(id),
        FOREIGN KEY (updated_by) REFERENCES users(id),
        UNIQUE(feature_id)
    )
`;

/**
 * AI 特征分类表结构
 * 存储特征的分类信息
 */;
const createAiFeatureCategoriesTable = `
    CREATE TABLE IF NOT EXISTS ai_feature_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT NOT NULL,
        category_description TEXT,
        parent_category_id INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_category_id) REFERENCES ai_feature_categories(id),
        UNIQUE(category_name)
    )
`;

/**
 * AI 特征关系表结构
 * 存储特征之间的关系
 */;
const createAiFeatureRelationsTable = `
    CREATE TABLE IF NOT EXISTS ai_feature_relations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_feature_id TEXT NOT NULL,
        target_feature_id TEXT NOT NULL,
        relation_type TEXT NOT NULL,
        relation_strength REAL DEFAULT 0.0,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_feature_id) REFERENCES ai_feature_store(feature_id),
        FOREIGN KEY (target_feature_id) REFERENCES ai_feature_store(feature_id),
        UNIQUE(source_feature_id, target_feature_id, relation_type)
    )
`;

/**
 * AI 特征元数据表结构
 * 存储特征的元数据信息
 */;
const createAiFeatureMetadataTable = `
    CREATE TABLE IF NOT EXISTS ai_feature_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feature_id TEXT NOT NULL,
        metadata_key TEXT NOT NULL,
        metadata_value TEXT NOT NULL,
        metadata_type TEXT DEFAULT 'string',
        is_searchable INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (feature_id) REFERENCES ai_feature_store(feature_id),
        UNIQUE(feature_id, metadata_key)
    )
`;

/**
 * AI 特征使用记录表结构
 * 存储特征的使用记录
 */;
const createAiFeatureUsageTable = `
    CREATE TABLE IF NOT EXISTS ai_feature_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feature_id TEXT NOT NULL,
        user_id INTEGER,
        usage_type TEXT NOT NULL,
        usage_context TEXT,
        result TEXT,
        duration_ms INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (feature_id) REFERENCES ai_feature_store(feature_id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
`;

/**
 * AI 特征索引创建
 */;
const createAiFeatureIndexes = `
    -- AI 特征存储表索引
    CREATE INDEX IF NOT EXISTS idx_ai_feature_store_feature_id ON ai_feature_store(feature_id);
    CREATE INDEX IF NOT EXISTS idx_ai_feature_store_feature_type ON ai_feature_store(feature_type);
    CREATE INDEX IF NOT EXISTS idx_ai_feature_store_category_id ON ai_feature_store(category_id);
    CREATE INDEX IF NOT EXISTS idx_ai_feature_store_is_active ON ai_feature_store(is_active);
    
    -- AI 特征分类表索引
    CREATE INDEX IF NOT EXISTS idx_ai_feature_categories_parent_id ON ai_feature_categories(parent_category_id);
    CREATE INDEX IF NOT EXISTS idx_ai_feature_categories_is_active ON ai_feature_categories(is_active);
    
    -- AI 特征关系表索引
    CREATE INDEX IF NOT EXISTS idx_ai_feature_relations_source ON ai_feature_relations(source_feature_id);
    CREATE INDEX IF NOT EXISTS idx_ai_feature_relations_target ON ai_feature_relations(target_feature_id);
    CREATE INDEX IF NOT EXISTS idx_ai_feature_relations_type ON ai_feature_relations(relation_type);
    
    -- AI 特征元数据表索引
    CREATE INDEX IF NOT EXISTS idx_ai_feature_metadata_feature_id ON ai_feature_metadata(feature_id);
    CREATE INDEX IF NOT EXISTS idx_ai_feature_metadata_key ON ai_feature_metadata(metadata_key);
    
    -- AI 特征使用记录表索引
    CREATE INDEX IF NOT EXISTS idx_ai_feature_usage_feature_id ON ai_feature_usage(feature_id);
    CREATE INDEX IF NOT EXISTS idx_ai_feature_usage_user_id ON ai_feature_usage(user_id);
    CREATE INDEX IF NOT EXISTS idx_ai_feature_usage_created_at ON ai_feature_usage(created_at);
`;

/**
 * 初始化 AI 特征分类数据
 */;
const initAiFeatureCategories = `
    INSERT OR IGNORE INTO ai_feature_categories (category_name, category_description) VALUES
    ('natural_language', '自然语言处理特征'),
    ('computer_vision', '计算机视觉特征'),
    ('speech_recognition', '语音识别特征'),
    ('machine_learning', '机器学习特征'),
    ('user_behavior', '用户行为特征'),
    ('sentiment_analysis', '情感分析特征'),
    ('recommendation', '推荐系统特征'),
    ('anomaly_detection', '异常检测特征'),
    ('predictive_analytics', '预测分析特征'),
    ('other', '其他特征'),
    ('japanese_learning', '日语学习特征'),
    ('question_generation', '题目生成特征'),
    ('exam_preparation', '考试准备特征')
`;

/**
 * 导出 AI 特征库相关 SQL 语句
 */;
module.exports = {
    createAiFeatureStoreTable,
    createAiFeatureCategoriesTable,
    createAiFeatureRelationsTable,
    createAiFeatureMetadataTable,
    createAiFeatureUsageTable,
    createAiFeatureIndexes,
    initAiFeatureCategories
};