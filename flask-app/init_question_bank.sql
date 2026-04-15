-- 初始化题库相关表结构

-- 1. 题目语言表
CREATE TABLE IF NOT EXISTS question_languages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_code TEXT UNIQUE NOT NULL,
    language_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 题目章节表
CREATE TABLE IF NOT EXISTS question_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 题目难度表
CREATE TABLE IF NOT EXISTS question_difficulties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    difficulty_level TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 题目等级表
CREATE TABLE IF NOT EXISTS question_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_id INTEGER NOT NULL,
    level_code TEXT NOT NULL,
    level_name TEXT NOT NULL,
    level_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (language_id) REFERENCES question_languages(id),
    UNIQUE (language_id, level_code)
);

-- 5. 题库表
CREATE TABLE IF NOT EXISTS question_banks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    language_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (language_id) REFERENCES question_languages(id)
);

-- 6. 题目表
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_bank_id INTEGER NOT NULL,
    level_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    difficulty_id INTEGER NOT NULL,
    question_content TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_bank_id) REFERENCES question_banks(id),
    FOREIGN KEY (level_id) REFERENCES question_levels(id),
    FOREIGN KEY (section_id) REFERENCES question_sections(id),
    FOREIGN KEY (difficulty_id) REFERENCES question_difficulties(id)
);

-- 7. 题目选项表
CREATE TABLE IF NOT EXISTS question_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    option_label TEXT NOT NULL,
    option_content TEXT NOT NULL,
    option_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

-- 8. 题目素材来源表
CREATE TABLE IF NOT EXISTS question_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. 修改题目表，添加素材来源字段
ALTER TABLE questions ADD COLUMN source_id INTEGER REFERENCES question_sources(id);

-- 10. 插入初始素材来源数据
INSERT INTO question_sources (source_type, description) VALUES
('standard', '标准日语教材'),
('past_exam', '历年真题'),
('anime_movie', '动漫电影电视剧'),
('news', '历年新闻');

-- 11. 题目