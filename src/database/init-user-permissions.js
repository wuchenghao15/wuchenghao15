// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

// 数据库文件路径
const DB_PATH = path.join(__dirname, 'jp_test.db');

// 初始化user_permissions表
function initUserPermissionsTable() {
    const db = new sqlite3.Database(DB_PATH, (err) => {
        if (err) {
            console.error('数据库连接失败:', err);
            return;
        }
        console.log('数据库连接成功');
        
        // 创建user_permissions表
        db.run(`
            CREATE TABLE IF NOT EXISTS user_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                permission_type TEXT NOT NULL,
                permission_level INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, permission_type)
            )
        `, (err) => {
            if (err) {
                console.error('创建user_permissions表失败:', err);
            } else {
                console.log('user_permissions表创建成功');
                
                // 创建索引
                db.run(`
                    CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id)
                `, (err) => {
                    if (err) {
                        console.error('创建索引失败:', err);
                    } else {
                        console.log('索引创建成功');
                    }
                });
            }
        });
        
        db.close();
    });
}

// 执行初始化
if (require.main === module) {
    initUserPermissionsTable();
}

module.exports = initUserPermissionsTable;