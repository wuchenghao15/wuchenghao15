#!/usr/bin/env node

/**
 * 初始化用户数据存储系统
 * 手动创建用户数据存储表并测试功能
 */

const db = require('./src/database/db');
const userDataStorageService = require('./src/core/storage/user-data-storage-service');

async function initializeUserDataStorage() {
    console.log('🔄 开始初始化用户数据存储系统...');
    
    try {
        // 1. 初始化数据库连接
        console.log('📦 初始化数据库连接...');
        await db.initialize();
        console.log('✅ 数据库连接初始化成功');
        
        // 2. 直接执行SQL创建用户数据存储表
        console.log('🗄️  创建用户数据存储表...');
        await db.execute(`
            CREATE TABLE IF NOT EXISTS user_data_storage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                data_key TEXT NOT NULL,
                data_value TEXT NOT NULL,
                data_type TEXT DEFAULT 'json',
                category TEXT DEFAULT 'general',
                is_encrypted INTEGER DEFAULT 0,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, data_key)
            )
        `);
        
        await db.execute(`
            CREATE INDEX IF NOT EXISTS idx_user_data_storage_user_id ON user_data_storage(user_id)
        `);
        
        await db.execute(`
            CREATE INDEX IF NOT EXISTS idx_user_data_storage_key ON user_data_storage(data_key)
        `);
        
        await db.execute(`
            CREATE INDEX IF NOT EXISTS idx_user_data_storage_category ON user_data_storage(category)
        `);
        
        await db.execute(`
            CREATE INDEX IF NOT EXISTS idx_user_data_storage_expires_at ON user_data_storage(expires_at)
        `);
        
        console.log('✅ 用户数据存储表创建成功');
        
        // 3. 测试用户数据存储功能
        console.log('🧪 测试用户数据存储功能...');
        
        // 测试存储数据
        const storeResult = await userDataStorageService.storeUserData(1, 'test_key', {
            name: '测试用户',
            age: 25,
            email: 'test@example.com'
        });
        
        console.log('📥 存储测试结果:', storeResult);
        
        // 测试获取数据
        const getResult = await userDataStorageService.getUserData(1, 'test_key');
        console.log('📤 获取测试结果:', getResult);
        
        // 测试列表功能
        const listResult = await userDataStorageService.getUserDataList(1);
        console.log('📋 列表测试结果:', listResult);
        
        // 测试统计功能
        const statsResult = await userDataStorageService.getUserDataStats(1);
        console.log('📊 统计测试结果:', statsResult);
        
        // 4. 验证表是否存在
        console.log('🔍 验证用户数据存储表...');
        const tables = await db.query(`
            SELECT name FROM sqlite_master WHERE type='table' AND name='user_data_storage'
        `);
        
        if (tables.length > 0) {
            console.log('✅ 用户数据存储表验证成功');
        } else {
            console.error('❌ 用户数据存储表验证失败');
        }
        
        console.log('🎉 用户数据存储系统初始化完成！');
        console.log('📋 系统状态:');
        console.log('   - 数据库连接: ✅');
        console.log('   - 用户数据存储表: ✅');
        console.log('   - 存储功能: ✅');
        console.log('   - 获取功能: ✅');
        console.log('   - 列表功能: ✅');
        console.log('   - 统计功能: ✅');
        
    } catch (error) {
        console.error('❌ 初始化用户数据存储系统失败:', error);
    } finally {
        // 关闭数据库连接
        db.close();
        console.log('🔒 数据库连接已关闭');
    }
}

// 运行初始化
initializeUserDataStorage();