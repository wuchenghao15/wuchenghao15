// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 数据库初始化脚本
 * 用于初始化数据库并生成10000题
 */
;
console.log('Starting database initialization script...');
;
const db = require('./db');
const questionGenerator = require('./question-generator');
;
async function initDatabase() {
    try {
        console.log('1. Initializing database connection...');
        
        // 初始化数据库连接
        await db.initialize();
        console.log('✅ Database connection initialized successfully');
        
        // 生成10000题
        console.log('2. Generating 10000 questions...');
        const generatedCount = await questionGenerator.generateQuestions(10000);
        console.log(`✅ Question generation completed! Generated ${generatedCount} questions`);
        
        // 更新统计信息
        console.log('3. Updating question statistics...');
        await db.updateQuestionStats();
        console.log('✅ Question statistics updated successfully');
        
        // 验证题目数量
        console.log('4. Verifying question count...');
        const totalCount = await db.getQuestionCount();
        console.log(`✅ Total questions in database: ${totalCount}`);
        
        // 验证各个级别的题目数量
        console.log('5. Verifying questions by level...');
        const levels = ['N1', 'N2', 'N3', 'N4', 'N5'];
        for (const level of levels) {
            const count = await db.getQuestionCount(level);
            console.log(`${level} level: ${count} questions`);
        }
        
        console.log('🎉 Database initialization completed successfully!');
        
    } catch (error) {
        console.error('❌ Database initialization failed:', error);
        console.error('Error stack:', error.stack);
        process.exit(1);
    } finally {
        // 关闭数据库连接
        console.log('6. Closing database connection...');
        db.close();
        console.log('✅ Database connection closed');
    }
}

// 执行初始化;
initDatabase();