/**
 * MTSCOS AI 系统 - 数据库迁移工具
 * 用于管理数据库结构更新
 */

const fs = require('fs');
const path = require('path');

class DatabaseMigration {
    constructor(dbPath) {
        this.dbPath = dbPath;
        this.migrationsDir = path.join(projectRoot, 'src', 'database', 'migrations');
        this.migrationTable = 'migrations';
        
        // 确保迁移目录存在
        fs.mkdirSync(this.migrationsDir, { recursive: true });
    }
    
    // 创建迁移文件
    createMigration(name) {
        const timestamp = Date.now();
        const migrationName = timestamp + '_' + name.replace(/\s+/g, '_') + '.js';
        const migrationPath = path.join(this.migrationsDir, migrationName);
        
        const migrationTemplate = '/**\n * Migration: ' + name + \n * Timestamp: ' + timestamp + \n */\n\nmodule.exports = {\n    up: async (db) => {\n        // 迁移向上操作\n        // 例如: await db.run('CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT)');\n    },\n    \n    down: async (db) => {\n        // 迁移向下操作\n        // 例如: await db.run('DROP TABLE users');\n    }\n};\n';
        
        fs.writeFileSync(migrationPath, migrationTemplate);
        console.log('[Migration] 创建迁移文件: ' + migrationPath);
        return migrationPath;
    }
    
    // 执行所有未执行的迁移
    async runMigrations(db) {
        // 确保迁移表存在
        await this.ensureMigrationTable(db);
        
        // 获取已执行的迁移
        const executedMigrations = await this.getExecutedMigrations(db);
        
        // 获取所有迁移文件
        const migrationFiles = fs.readdirSync(this.migrationsDir)
            .filter(file => file.endsWith('.js'))
            .sort();
        
        // 执行未执行的迁移
        for (const file of migrationFiles) {
            const migrationName = file.replace('.js', '');
            if (!executedMigrations.includes(migrationName)) {
                const migration = require(path.join(this.migrationsDir, file));
                
                console.log('[Migration] 执行迁移: ' + migrationName);
                await migration.up(db);
                await this.markMigrationExecuted(db, migrationName);
            }
        }
        
        console.log('[Migration] 所有迁移已执行完成');
    }
    
    // 回滚最近的迁移
    async rollbackMigration(db) {
        // 确保迁移表存在
        await this.ensureMigrationTable(db);
        
        // 获取已执行的迁移
        const executedMigrations = await this.getExecutedMigrations(db);
        
        if (executedMigrations.length === 0) {
            console.log('[Migration] 没有可回滚的迁移');
            return;
        }
        
        // 获取最后执行的迁移
        const lastMigration = executedMigrations[executedMigrations.length - 1];
        const migrationFile = lastMigration + '.js';
        const migrationPath = path.join(this.migrationsDir, migrationFile);
        
        if (fs.existsSync(migrationPath)) {
            const migration = require(migrationPath);
            
            console.log('[Migration] 回滚迁移: ' + lastMigration);
            await migration.down(db);
            await this.markMigrationRolledBack(db, lastMigration);
        }
        
        console.log('[Migration] 迁移回滚完成');
    }
    
    // 确保迁移表存在
    async ensureMigrationTable(db) {
        await db.run('\n            CREATE TABLE IF NOT EXISTS ' + this.migrationTable + ' (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                name TEXT UNIQUE NOT NULL,\n                executed_at DATETIME DEFAULT CURRENT_TIMESTAMP\n            )\n        ');
    }
    
    // 获取已执行的迁移
    async getExecutedMigrations(db) {
        const migrations = [];
        const rows = await db.all('SELECT name FROM ' + this.migrationTable + ' ORDER BY executed_at');
        
        for (const row of rows) {
            migrations.push(row.name);
        }
        
        return migrations;
    }
    
    // 标记迁移为已执行
    async markMigrationExecuted(db, migrationName) {
        await db.run(
            'INSERT INTO ' + this.migrationTable + ' (name) VALUES (?)',
            [migrationName]
        );
    }
    
    // 标记迁移为已回滚
    async markMigrationRolledBack(db, migrationName) {
        await db.run(
            'DELETE FROM ' + this.migrationTable + ' WHERE name = ?',
            [migrationName]
        );
    }
}

module.exports = DatabaseMigration;
