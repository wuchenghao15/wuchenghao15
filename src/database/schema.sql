-- 日语测试题库数据库结构
-- 支持10000题的存储和管理

-- 题目主表
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL, -- N1, N2, N3, N4, N5
    type TEXT NOT NULL, -- listening, vocabulary, grammar, reading, writing
    question TEXT NOT NULL, -- 题目内容
    options TEXT, -- 选项（JSON格式）
    answer TEXT, -- 正确答案
    explanation TEXT, -- 解析
    audio_url TEXT, -- 音频URL（听力题专用）
    scenario TEXT, -- 场景描述（听力题专用）
    passage TEXT, -- 阅读文章（阅读题专用）
    difficulty INTEGER DEFAULT 1, -- 难度等级 1-5
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以优化查询性能
CREATE INDEX IF NOT EXISTS idx_questions_level_type ON questions(level, type);
CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(type);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);

-- 题目统计信息表
CREATE TABLE IF NOT EXISTS question_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    type TEXT NOT NULL,
    total_count INTEGER DEFAULT 0,
    used_count INTEGER DEFAULT 0,
    correct_rate REAL DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(level, type)
);

-- 用户答题记录表
CREATE TABLE IF NOT EXISTS user_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    question_id INTEGER NOT NULL,
    answer TEXT,
    is_correct INTEGER DEFAULT 0,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_answers_user ON user_answers(user_id);
CREATE INDEX IF NOT EXISTS idx_user_answers_question ON user_answers(question_id);

-- 学习进度表
CREATE TABLE IF NOT EXISTS learning_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    level TEXT NOT NULL,
    type TEXT NOT NULL,
    progress REAL DEFAULT 0, -- 0-100
    last_practiced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, level, type)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_learning_progress_user ON learning_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_progress_level_type ON learning_progress(level, type);

-- 初始化题目统计信息
INSERT OR IGNORE INTO question_stats (level, type, total_count) VALUES
('N1', 'listening', 0),
('N1', 'vocabulary', 0),
('N1', 'grammar', 0),
('N1', 'reading', 0),
('N1', 'writing', 0),
('N2', 'listening', 0),
('N2', 'vocabulary', 0),
('N2', 'grammar', 0),
('N2', 'reading', 0),
('N2', 'writing', 0),
('N3', 'listening', 0),
('N3', 'vocabulary', 0),
('N3', 'grammar', 0),
('N3', 'reading', 0),
('N3', 'writing', 0),
('N4', 'listening', 0),
('N4', 'vocabulary', 0),
('N4', 'grammar', 0),
('N4', 'reading', 0),
('N4', 'writing', 0),
('N5', 'listening', 0),
('N5', 'vocabulary', 0),
('N5', 'grammar', 0),
('N5', 'reading', 0),
('N5', 'writing', 0);