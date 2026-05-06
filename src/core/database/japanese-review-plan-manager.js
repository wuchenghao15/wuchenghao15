// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 日语复习计划数据库管理器
 * 负责管理复习计划、练习记录、用户进度等数据
 */

const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

class JapaneseReviewPlanManager {
    constructor() {
        this.dbPath = path.join(__dirname, '../../../data/japanese_review_plans.db');
        this.db = null;
    }

    /**
     * 初始化数据库
     */
    async initialize() {
        console.log('📚 初始化日语复习计划数据库...');
        
        // 确保数据目录存在
        const dataDir = path.join(__dirname, '../../../data');
        if (!fs.existsSync(dataDir)) {
            fs.mkdirSync(dataDir, { recursive: true });
            console.log('✅ 数据目录创建成功');
        }

        // 连接数据库
        this.db = new sqlite3.Database(this.dbPath, (err) => {
            if (err) {
                console.error('❌ 数据库连接失败:', err);
                throw err;
            }
            console.log('✅ 日语复习计划数据库连接成功');
        });

        // 创建表结构
        await this.createTables();
        console.log('✅ 日语复习计划数据库初始化完成');
    }

    /**
     * 创建数据库表结构
     */
    async createTables() {
        return new Promise((resolve, reject) => {
            // 创建复习计划表
            const createPlansTable = `
                CREATE TABLE IF NOT EXISTS review_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    plan_name TEXT NOT NULL,
                    level TEXT NOT NULL,
                    target_score INTEGER,
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    total_days INTEGER,
                    daily_target INTEGER,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            `;

            // 创建学习进度表
            const createProgressTable = `
                CREATE TABLE IF NOT EXISTS learning_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    progress_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    plan_id TEXT,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT,
                    current_score INTEGER,
                    target_score INTEGER,
                    completed_items INTEGER,
                    total_items INTEGER,
                    last_studied TIMESTAMP,
                    streak_days INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES review_plans(plan_id)
                )
            `;

            // 创建练习记录表
            const createPracticeRecordsTable = `
                CREATE TABLE IF NOT EXISTS practice_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    plan_id TEXT,
                    paper_id TEXT,
                    paper_type TEXT NOT NULL,
                    level TEXT NOT NULL,
                    score INTEGER,
                    total_questions INTEGER,
                    correct_answers INTEGER,
                time_spent INTEGER,
                questions TEXT,
                answers TEXT,
                correct_answers_text TEXT,
                difficulty INTEGER,
                    feedback TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES review_plans(plan_id)
                )
            `;

            // 创建用户学习统计
            const createUserStatsTable = `
                CREATE TABLE IF NOT EXISTS user_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    total_practices INTEGER DEFAULT 0,
                    total_score INTEGER DEFAULT 0,
                    average_score REAL DEFAULT 0,
                    streak_days INTEGER DEFAULT 0,
                    last_practice TIMESTAMP,
                    best_score INTEGER DEFAULT 0,
                    weak_categories TEXT,
                    strong_categories TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            `;

            // 创建AI生成的试卷表
            const createAIPapersTable = `
                CREATE TABLE IF NOT EXISTS ai_papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER,
                    plan_id TEXT,
                    level TEXT NOT NULL,
                    paper_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    questions TEXT NOT NULL,
                    difficulty INTEGER,
                    estimated_time INTEGER,
                    ai_model TEXT,
                    generation_time INTEGER,
                    status TEXT DEFAULT 'generated',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES review_plans(plan_id)
                )
            `;

            // 创建自动提取的题目表
            const createExtractedQuestionsTable = `
                CREATE TABLE IF NOT EXISTS extracted_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id TEXT UNIQUE NOT NULL,
                    source TEXT NOT NULL,
                    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    question_type TEXT NOT NULL,
                    level TEXT,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    status TEXT DEFAULT 'pending',
                    processing_time INTEGER,
                    error_message TEXT,
                    FOREIGN KEY (question_id) REFERENCES questions(question_id)
                )
            `;

            // 执行创建表操作
            this.db.serialize(() => {
                this.db.run(createPlansTable, (err) => {
                    if (err) {
                        console.error('❌ 创建复习计划表失败:', err);
                        reject(err);
                        return;
                    }
                    console.log('✅ 复习计划表创建成功');
                });

                this.db.run(createProgressTable, (err) => {
                    if (err) {
                        console.error('❌ 创建学习进度表失败:', err);
                        reject(err);
                        return;
                    }
                    console.log('✅ 学习进度表创建成功');
                });

                this.db.run(createPracticeRecordsTable, (err) => {
                    if (err) {
                        console.error('❌ 创建练习记录表失败:', err);
                        reject(err);
                        return;
                    }
                    console.log('✅ 练习记录表创建成功');
                });

                this.db.run(createUserStatsTable, (err) => {
                    if (err) {
                        console.error('❌ 创建用户统计表失败:', err);
                        reject(err);
                        return;
                    }
                    console.log('✅ 用户统计表创建成功');
                });

                this.db.run(createAIPapersTable, (err) => {
                    if (err) {
                        console.error('❌ 创建AI试卷表失败:', err);
                        reject(err);
                        return;
                    }
                    console.log('✅ AI试卷表创建成功');
                });

                this.db.run(createExtractedQuestionsTable, (err) => {
                    if (err) {
                        console.error('❌ 创建自动提取题目表失败:', err);
                        reject(err);
                        return;
                    }
                    console.log('✅ 自动提取题目表创建成功');
                    resolve();
                });
            });
        });
    }

    /**
     * 添加复习计划
     */
    async addReviewPlan(plan) {
        return new Promise((resolve, reject) => {
            const sql = `
                INSERT OR REPLACE INTO review_plans 
                (plan_id, user_id, plan_name, level, target_score, start_date, end_date, status, total_days, daily_target, description, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            `;

            this.db.run(sql, [
                plan.plan_id,
                plan.user_id,
                plan.plan_name,
                plan.level,
                plan.target_score,
                plan.start_date,
                plan.end_date,
                plan.status,
                plan.total_days,
                plan.daily_target,
                plan.description
            ], function(err) {
                if (err) {
                    console.error('❌ 添加复习计划失败:', err);
                    reject(err);
                    return;
                }
                resolve({
                    success: true,
                    plan_id: plan.plan_id,
                    id: this.lastID
                });
            });
        });
    }

    /**
     * 获取用户的复习计划
     */
    async getUserPlans(userId) {
        return new Promise((resolve, reject) => {
            const sql = `SELECT * FROM review_plans WHERE user_id = ? ORDER BY created_at DESC`;
            this.db.all(sql, [userId], (err, rows) => {
                if (err) {
                    reject(err);
                    return;
                }
                resolve(rows);
            });
        });
    }

    /**
     * 记录练习结果
     */
    async addPracticeRecord(record) {
        return new Promise((resolve, reject) => {
            const sql = `
                INSERT INTO practice_records 
                (record_id, user_id, plan_id, paper_id, paper_type, level, score, total_questions, correct_answers, time_spent, questions, answers, correct_answers_text, difficulty, feedback, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            `;

            this.db.run(sql, [
                record.record_id,
                record.user_id,
                record.plan_id,
                record.paper_id,
                record.paper_type,
                record.level,
                record.score,
                record.total_questions,
                record.correct_answers,
                record.time_spent,
                JSON.stringify(record.questions),
                JSON.stringify(record.answers),
                JSON.stringify(record.correct_answers),
                record.difficulty,
                record.feedback,
                record.status
            ], function(err) {
                if (err) {
                    console.error('❌ 添加练习记录失败:', err);
                    reject(err);
                    return;
                }
                resolve({
                    success: true,
                    record_id: record.record_id,
                    id: this.lastID
                });
            });
        });
    }

    /**
     * 更新学习进度
     */
    async updateProgress(progress) {
        return new Promise((resolve, reject) => {
            const sql = `
                INSERT OR REPLACE INTO learning_progress 
                (progress_id, user_id, plan_id, level, category, subcategory, current_score, target_score, completed_items, total_items, last_studied, streak_days, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            `;

            this.db.run(sql, [
                progress.progress_id,
                progress.user_id,
                progress.plan_id,
                progress.level,
                progress.category,
                progress.subcategory,
                progress.current_score,
                progress.target_score,
                progress.completed_items,
                progress.total_items,
                new Date().toISOString(),
                progress.streak_days
            ], function(err) {
                if (err) {
                    console.error('❌ 更新学习进度失败:', err);
                    reject(err);
                    return;
                }
                resolve({
                    success: true,
                    progress_id: progress.progress_id,
                    id: this.lastID
                });
            });
        });
    }

    /**
     * 获取用户统计信息
     */
    async getUserStats(userId) {
        return new Promise((resolve, reject) => {
            const sql = `SELECT * FROM user_stats WHERE user_id = ?`;
            this.db.get(sql, [userId], (err, row) => {
                if (err) {
                    reject(err);
                    return;
                }
                resolve(row);
            });
        });
    }

    /**
     * 更新用户统计信息
     */
    async updateUserStats(userId, stats) {
        return new Promise((resolve, reject) => {
            const sql = `
                INSERT OR REPLACE INTO user_stats 
                (user_id, total_practices, total_score, average_score, streak_days, last_practice, best_score, weak_categories, strong_categories, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            `;

            this.db.run(sql, [
                userId,
                stats.total_practices,
                stats.total_score,
                stats.average_score,
                stats.streak_days,
                new Date().toISOString(),
                stats.best_score,
                JSON.stringify(stats.weak_categories),
                JSON.stringify(stats.strong_categories)
            ], function(err) {
                if (err) {
                    console.error('❌ 更新用户统计失败:', err);
                    reject(err);
                    return;
                }
                resolve({
                    success: true,
                    user_id: userId
                });
            });
        });
    }

    /**
     * 添加AI生成的试卷
     */
    async addAIPaper(paper) {
        return new Promise((resolve, reject) => {
            const sql = `
                INSERT INTO ai_papers 
                (paper_id, user_id, plan_id, level, paper_type, title, description, questions, difficulty, estimated_time, ai_model, generation_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            `;

            this.db.run(sql, [
                paper.paper_id,
                paper.user_id,
                paper.plan_id,
                paper.level,
                paper.paper_type,
                paper.title,
                paper.description,
                JSON.stringify(paper.questions),
                paper.difficulty,
                paper.estimated_time,
                paper.ai_model,
                paper.generation_time,
                paper.status
            ], function(err) {
                if (err) {
                    console.error('❌ 添加AI试卷失败:', err);
                    reject(err);
                    return;
                }
                resolve({
                    success: true,
                    paper_id: paper.paper_id,
                    id: this.lastID
                });
            });
        });
    }

    /**
     * 添加自动提取的题目
     */
    async addExtractedQuestion(question) {
        return new Promise((resolve, reject) => {
            const sql = `
                INSERT INTO extracted_questions 
                (question_id, source, extraction_date, question_type, level, content, metadata, status, processing_time, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            `;

            this.db.run(sql, [
                question.question_id,
                question.source,
                new Date().toISOString(),
                question.question_type,
                question.level,
                question.content,
                JSON.stringify(question.metadata),
                question.status || 'pending',
                question.processing_time,
                question.error_message
            ], function(err) {
                if (err) {
                    console.error('❌ 添加提取题目失败:', err);
                    reject(err);
                    return;
                }
                resolve({
                    success: true,
                    question_id: question.question_id,
                    id: this.lastID
                });
            });
        });
    }

    /**
     * 获取数据库统计信息
     */
    async getStatistics() {
        return new Promise((resolve, reject) => {
            const sql = `
                SELECT 
                    (SELECT COUNT(*) FROM review_plans) as total_plans,
                    (SELECT COUNT(*) FROM learning_progress) as total_progress,
                    (SELECT COUNT(*) FROM practice_records) as total_records,
                    (SELECT COUNT(*) FROM ai_papers) as total_ai_papers,
                    (SELECT COUNT(*) FROM extracted_questions) as total_extracted_questions
            `;

            this.db.get(sql, (err, row) => {
                if (err) {
                    reject(err);
                    return;
                }
                resolve(row);
            });
        });
    }

    /**
     * 关闭数据库连接
     */
    close() {
        if (this.db) {
            this.db.close((err) => {
                if (err) {
                    console.error('❌ 数据库关闭失败:', err);
                } else {
                    console.log('✅ 日语复习计划数据库连接已关闭');
                }
            });
        }
    }
}

// 导出单例
const japaneseReviewPlanManager = new JapaneseReviewPlanManager();
module.exports = japaneseReviewPlanManager;
module.exports.JapaneseReviewPlanManager = JapaneseReviewPlanManager;