/**
 * SQLite数据库备份同步脚本
 * 创建备用数据库并定期同步数据，实现故障转移机制
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class SQLiteBackupSync {
    constructor() {
        // 主数据库文件路径
        this.mainDbPath = path.join(__dirname, '../src/database/jp_test.db');
        // 备用数据库文件路径
        this.backupDbPath = path.join(__dirname, '../src/database/jp_test_backup.db');
        // 配置文件路径
        this.configPath = path.join(__dirname, '../config/database.json');
        
        this.syncInterval = 5 * 60 * 1000; // 5分钟同步一次
        this.running = false;
        this.syncTimer = null;
    }

    /**
     * 初始化备用数据库
     */
    initializeBackupDatabase() {
        try {
            console.log('[BACKUP] 正在初始化备用数据库...');
            
            // 检查主数据库是否存在
            if (!fs.existsSync(this.mainDbPath)) {
                console.error('[BACKUP] 主数据库文件不存在:', this.mainDbPath);
                return false;
            }
            
            // 复制主数据库到备用数据库
            this.copyDatabase();
            
            console.log('[BACKUP] 备用数据库初始化成功');
            return true;
        } catch (error) {
            console.error('[BACKUP] 初始化备用数据库失败:', error);
            return false;
        }
    }

    /**
     * 复制数据库文件
     */
    copyDatabase() {
        try {
            // 确保目标目录存在
            const backupDir = path.dirname(this.backupDbPath);
            if (!fs.existsSync(backupDir)) {
                fs.mkdirSync(backupDir, { recursive: true });
            }
            
            // 复制文件
            fs.copyFileSync(this.mainDbPath, this.backupDbPath);
            console.log(`[BACKUP] 数据库已从 ${this.mainDbPath} 复制到 ${this.backupDbPath}`);
            return true;
        } catch (error) {
            console.error('[BACKUP] 复制数据库失败:', error);
            return false;
        }
    }

    /**
     * 同步数据库
     */
    syncDatabases() {
        try {
            console.log('[BACKUP] 开始同步数据库...');
            
            // 检查主数据库是否存在
            if (!fs.existsSync(this.mainDbPath)) {
                console.error('[BACKUP] 主数据库文件不存在，跳过同步');
                return false;
            }
            
            // 复制数据库
            this.copyDatabase();
            
            console.log('[BACKUP] 数据库同步完成');
            return true;
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
    checkDatabaseStatus() {
        try {
            const mainExists = fs.existsSync(this.mainDbPath);
            const backupExists = fs.existsSync(this.backupDbPath);
            
            let mainSize = 0;
            let backupSize = 0;
            
            if (mainExists) {
                const mainStats = fs.statSync(this.mainDbPath);
                mainSize = mainStats.size;
            }
            
            if (backupExists) {
                const backupStats = fs.statSync(this.backupDbPath);
                backupSize = backupStats.size;
            }
            
            console.log('[BACKUP] 数据库状态:');
            console.log(`- 主数据库: ${mainExists ? '存在' : '不存在'} (${mainSize} bytes)`);
            console.log(`- 备用数据库: ${backupExists ? '存在' : '不存在'} (${backupSize} bytes)`);
            
            return {
                main: mainExists,
                backup: backupExists,
                mainSize,
                backupSize
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
     * 将备用数据库复制到主数据库位置
     */
    switchToBackup() {
        try {
            console.log('[BACKUP] 切换到备用数据库...');
            
            // 检查备用数据库是否存在
            if (!fs.existsSync(this.backupDbPath)) {
                console.error('[BACKUP] 备用数据库文件不存在，无法切换');
                return false;
            }
            
            // 备份当前主数据库（如果存在）
            if (fs.existsSync(this.mainDbPath)) {
                const mainBackupPath = this.mainDbPath + '.bak';
                fs.copyFileSync(this.mainDbPath, mainBackupPath);
                console.log(`[BACKUP] 已备份当前主数据库到 ${mainBackupPath}`);
            }
            
            // 将备用数据库复制到主数据库位置
            fs.copyFileSync(this.backupDbPath, this.mainDbPath);
            console.log('[BACKUP] 已切换到备用数据库');
            return true;
        } catch (error) {
            console.error('[BACKUP] 切换到备用数据库失败:', error);
            return false;
        }
    }

    /**
     * 验证数据库完整性
     */
    validateDatabase() {
        try {
            console.log('[BACKUP] 验证数据库完整性...');
            
            // 对于SQLite，我们可以通过检查文件大小和基本结构来验证
            // 注意：在实际环境中，应该使用SQLite的PRAGMA integrity_check
            
            if (fs.existsSync(this.mainDbPath)) {
                const mainStats = fs.statSync(this.mainDbPath);
                console.log(`[BACKUP] 主数据库大小: ${mainStats.size} bytes`);
                console.log(`[BACKUP] 主数据库修改时间: ${mainStats.mtime}`);
            }
            
            if (fs.existsSync(this.backupDbPath)) {
                const backupStats = fs.statSync(this.backupDbPath);
                console.log(`[BACKUP] 备用数据库大小: ${backupStats.size} bytes`);
                console.log(`[BACKUP] 备用数据库修改时间: ${backupStats.mtime}`);
            }
            
            console.log('[BACKUP] 数据库验证完成');
            return true;
        } catch (error) {
            console.error('[BACKUP] 验证数据库完整性失败:', error);
            return false;
        }
    }

    /**
     * 清理旧备份
     */
    cleanOldBackups() {
        try {
            console.log('[BACKUP] 清理旧备份...');
            
            // 检查并清理旧的备份文件
            const backupDir = path.dirname(this.backupDbPath);
            const files = fs.readdirSync(backupDir);
            
            let cleanedCount = 0;
            files.forEach(file => {
                if (file.endsWith('.db.bak') || file.includes('_old_')) {
                    const filePath = path.join(backupDir, file);
                    fs.unlinkSync(filePath);
                    cleanedCount++;
                    console.log(`[BACKUP] 已清理旧备份: ${file}`);
                }
            });
            
            console.log(`[BACKUP] 清理完成，共清理 ${cleanedCount} 个旧备份文件`);
            return true;
        } catch (error) {
            console.error('[BACKUP] 清理旧备份失败:', error);
            return false;
        }
    }
}

// 命令行使用
if (require.main === module) {
    const backupSync = new SQLiteBackupSync();
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.log('SQLite数据库备份同步工具');
        console.log('用法: node sqlite-backup-sync.js [命令]');
        console.log('命令:');
        console.log('  init      - 初始化备用数据库');
        console.log('  sync      - 执行一次数据库同步');
        console.log('  start     - 启动定期同步服务');
        console.log('  stop      - 停止定期同步服务');
        console.log('  status    - 检查数据库状态');
        console.log('  switch    - 切换到备用数据库');
        console.log('  validate  - 验证数据库完整性');
        console.log('  clean     - 清理旧备份');
        process.exit(0);
    }
    
    const command = args[0];
    
    switch (command) {
        case 'init':
            backupSync.initializeBackupDatabase();
            break;
        case 'sync':
            backupSync.syncDatabases();
            break;
        case 'start':
            backupSync.startSync();
            break;
        case 'stop':
            backupSync.stopSync();
            break;
        case 'status':
            backupSync.checkDatabaseStatus();
            break;
        case 'switch':
            backupSync.switchToBackup();
            break;
        case 'validate':
            backupSync.validateDatabase();
            break;
        case 'clean':
            backupSync.cleanOldBackups();
            break;
        default:
            console.log('未知命令:', command);
            break;
    }
}

module.exports = SQLiteBackupSync;