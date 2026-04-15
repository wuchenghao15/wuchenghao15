/**
 * MySQL数据库备份同步脚本
 * 创建备用数据库并定期同步数据，实现故障转移机制
 */

const mysql = require('mysql2/promise');
const fs = require('fs');
const path = require('path');

class MySQLBackupSync {
    constructor() {
        // 加载主数据库配置
        this.mainConfig = require('../config/database.json');
        // 备用数据库配置（基于主配置，仅修改数据库名）
        this.backupConfig = {
            ...this.mainConfig,
            database: 'mtscos_backup'
        };
        
        this.syncInterval = 5 * 60 * 1000; // 5分钟同步一次
        this.running = false;
        this.syncTimer = null;
    }

    /**
     * 初始化备用数据库
     */
    async initializeBackupDatabase() {
        try {
            console.log('[BACKUP] 正在初始化备用数据库...');
            
            // 连接到MySQL服务器（不指定数据库）
            const connection = await mysql.createConnection({
                host: this.mainConfig.host,
                port: this.mainConfig.port,
                user: this.mainConfig.user,
                password: this.mainConfig.password,
                charset: this.mainConfig.charset
            });
            
            // 检查备用数据库是否存在
            const [databases] = await connection.execute(
                'SHOW DATABASES LIKE ?',
                [this.backupConfig.database]
            );
            
            if (databases.length === 0) {
                // 创建备用数据库
                await connection.execute(`CREATE DATABASE ${this.backupConfig.database} CHARACTER SET ${this.mainConfig.charset}`);
                console.log(`[BACKUP] 备用数据库 ${this.backupConfig.database} 创建成功`);
            } else {
                console.log(`[BACKUP] 备用数据库 ${this.backupConfig.database} 已存在`);
            }
            
            await connection.end();
            return true;
        } catch (error) {
            console.error('[BACKUP] 初始化备用数据库失败:', error);
            return false;
        }
    }

    /**
     * 同步数据库结构和数据
     */
    async syncDatabases() {
        try {
            console.log('[BACKUP] 开始同步数据库...');
            
            // 连接到主数据库
            const mainConnection = await mysql.createConnection(this.mainConfig);
            // 连接到备用数据库
            const backupConnection = await mysql.createConnection(this.backupConfig);
            
            try {
                // 获取主数据库的所有表
                const [tables] = await mainConnection.execute(
                    'SHOW TABLES'
                );
                
                console.log(`[BACKUP] 发现 ${tables.length} 个表需要同步`);
                
                for (const table of tables) {
                    const tableName = table[Object.keys(table)[0]];
                    console.log(`[BACKUP] 同步表: ${tableName}`);
                    
                    // 获取表结构
                    const [createTableResult] = await mainConnection.execute(
                        `SHOW CREATE TABLE ${tableName}`
                    );
                    const createTableSql = createTableResult[0]['Create Table'];
                    
                    // 在备用数据库中删除并重新创建表
                    await backupConnection.execute(`DROP TABLE IF EXISTS ${tableName}`);
                    await backupConnection.execute(createTableSql);
                    
                    // 同步数据
                    const [data] = await mainConnection.execute(`SELECT * FROM ${tableName}`);
                    if (data.length > 0) {
                        const columns = Object.keys(data[0]);
                        const placeholders = columns.map(() => '?').join(', ');
                        const values = data.map(row => columns.map(col => row[col]));
                        
                        const insertSql = `INSERT INTO ${tableName} (${columns.join(', ')}) VALUES (${placeholders})`;
                        
                        // 批量插入数据
                        for (const valueSet of values) {
                            await backupConnection.execute(insertSql, valueSet);
                        }
                        
                        console.log(`[BACKUP] 表 ${tableName} 同步完成，插入 ${data.length} 条记录`);
                    } else {
                        console.log(`[BACKUP] 表 ${tableName} 无数据，跳过同步`);
                    }
                }
                
                console.log('[BACKUP] 数据库同步完成');
                return true;
            } finally {
                // 关闭连接
                await mainConnection.end();
                await backupConnection.end();
            }
        } catch (error) {
            console.error('[BACKUP] 数据库同步失败:', error);
            return false;
        }
    }

    /**
     * 启动定期同步
     */
    startSync() {
        if (this.running) {
            console.log('[BACKUP] 同步服务已经在运行');
            return;
        }
        
        this.running = true;
        console.log('[BACKUP] 启动定期同步服务');
        
        // 立即执行一次同步
        this.syncDatabases();
        
        // 设置定期同步
        this.syncTimer = setInterval(() => {
            this.syncDatabases();
        }, this.syncInterval);
    }

    /**
     * 停止定期同步
     */
    stopSync() {
        if (!this.running) {
            console.log('[BACKUP] 同步服务未运行');
            return;
        }
        
        this.running = false;
        if (this.syncTimer) {
            clearInterval(this.syncTimer);
            this.syncTimer = null;
        }
        console.log('[BACKUP] 停止定期同步服务');
    }

    /**
     * 检查数据库状态
     */
    async checkDatabaseStatus() {
        try {
            // 检查主数据库
            const mainConnection = await mysql.createConnection(this.mainConfig);
            await mainConnection.ping();
            await mainConnection.end();
            
            // 检查备用数据库
            const backupConnection = await mysql.createConnection(this.backupConfig);
            await backupConnection.ping();
            await backupConnection.end();
            
            return {
                main: true,
                backup: true
            };
        } catch (error) {
            console.error('[BACKUP] 检查数据库状态失败:', error);
            return {
                main: false,
                backup: false
            };
        }
    }

    /**
     * 切换到备用数据库
     * 更新配置文件，指向备用数据库
     */
    async switchToBackup() {
        try {
            console.log('[BACKUP] 切换到备用数据库...');
            
            // 保存当前主配置备份
            const configBackupPath = path.join(__dirname, '../config/database.json.bak');
            fs.writeFileSync(
                configBackupPath,
                JSON.stringify(this.mainConfig, null, 2)
            );
            
            // 更新配置文件，指向备用数据库
            const backupConfigForUse = {
                ...this.mainConfig,
                database: this.backupConfig.database
            };
            
            fs.writeFileSync(
                path.join(__dirname, '../config/database.json'),
                JSON.stringify(backupConfigForUse, null, 2)
            );
            
            console.log('[BACKUP] 已切换到备用数据库');
            return true;
        } catch (error) {
            console.error('[BACKUP] 切换到备用数据库失败:', error);
            return false;
        }
    }

    /**
     * 恢复到主数据库
     * 更新配置文件，指向主数据库
     */
    async restoreToMain() {
        try {
            console.log('[BACKUP] 恢复到主数据库...');
            
            // 检查备份配置文件是否存在
            const configBackupPath = path.join(__dirname, '../config/database.json.bak');
            if (fs.existsSync(configBackupPath)) {
                const originalConfig = JSON.parse(fs.readFileSync(configBackupPath, 'utf8'));
                
                // 更新配置文件，指向主数据库
                fs.writeFileSync(
                    path.join(__dirname, '../config/database.json'),
                    JSON.stringify(originalConfig, null, 2)
                );
                
                console.log('[BACKUP] 已恢复到主数据库');
                return true;
            } else {
                console.error('[BACKUP] 配置备份文件不存在');
                return false;
            }
        } catch (error) {
            console.error('[BACKUP] 恢复到主数据库失败:', error);
            return false;
        }
    }
}

// 命令行使用
if (require.main === module) {
    const backupSync = new MySQLBackupSync();
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.log('MySQL数据库备份同步工具');
        console.log('用法: node mysql-backup-sync.js [命令]');
        console.log('命令:');
        console.log('  init      - 初始化备用数据库');
        console.log('  sync      - 执行一次数据库同步');
        console.log('  start     - 启动定期同步服务');
        console.log('  stop      - 停止定期同步服务');
        console.log('  status    - 检查数据库状态');
        console.log('  switch    - 切换到备用数据库');
        console.log('  restore   - 恢复到主数据库');
        process.exit(0);
    }
    
    const command = args[0];
    
    (async () => {
        switch (command) {
            case 'init':
                await backupSync.initializeBackupDatabase();
                break;
            case 'sync':
                await backupSync.syncDatabases();
                break;
            case 'start':
                backupSync.startSync();
                break;
            case 'stop':
                backupSync.stopSync();
                break;
            case 'status':
                const status = await backupSync.checkDatabaseStatus();
                console.log('[BACKUP] 数据库状态:', status);
                break;
            case 'switch':
                await backupSync.switchToBackup();
                break;
            case 'restore':
                await backupSync.restoreToMain();
                break;
            default:
                console.log('未知命令:', command);
                break;
        }
    })();
}

module.exports = MySQLBackupSync;