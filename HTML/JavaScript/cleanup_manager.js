#!/usr/bin/env node
// VERSION: 20251106.ebc720c2dc507fbeaf86
// -*- coding: utf-8 -*-
/**
 * 项目清理管理器
 * 清理项目冗余文件和文件夹，删除过早log和备份文件
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class CleanupManager {
    constructor() {
        // 项目根目录
        this.projectRoot = path.resolve(__dirname, '..');
        
        // 目录路径
        this.logDir = path.join(this.projectRoot, 'Logs');
        this.backupDir = path.join(this.projectRoot, 'Backups');
        
        // 日志文件
        this.logFile = path.join(this.logDir, 'cleanup_manager.log');
        this.errorLogFile = path.join(this.logDir, 'error.log');
        
        // 配置
        this.logMaxAgeDays = 30; // 日志文件最大保存时间（天）
        this.backupMaxCount = 8; // 完整备份数量保持8份
        
        // 确保必要目录存在
        this.ensureDirExists(this.logDir);
    };

    
    /**
     * 确保目录存在
     */
    ensureDirExists(dirPath) {
        if (!fs.existsSync(dirPath)) {
            fs.mkdirSync(dirPath, { recursive: true });
            this.log(`目录创建: ${dirPath}`);
        };

    };

    
    /**
     * 日志函数
     */
    log(message) {
        try {
            const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
            
            // 确保消息不为空
            if (!message || typeof message !== 'string' || message.trim() === '') {
                message = '空日志消息';
            }
            
            const logMessage = `[${timestamp}] ${message}`;
            
            // 控制台输出
            console.log(logMessage);
            
            // 写入日志文件
            try {
                if (fs.existsSync(this.logDir)) {
                    fs.appendFileSync(this.logFile, logMessage + '\n', 'utf8');
                }
            } catch (fileError) {
                console.error(`写入日志文件失败: ${fileError.message}`);
            }
        } catch (logError) {
            console.error(`日志记录失败: ${logError.message}`);
        }

    };

    
    /**
     * 错误日志函数
     */
    errorLog(message) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logMessage = `[${timestamp}] ERROR: ${message}`;
        
        console.error(logMessage);
        
        try {
            fs.appendFileSync(this.errorLogFile, logMessage + '/n');
            fs.appendFileSync(this.logFile, logMessage + '/n');
        } catch (error) {
            console.error(`写入错误日志失败: ${error.message}`);
        };

    };

    
    /**
     * 获取文件的创建或修改时间
     */
    getFileAge(filePath) {
        try {
            const stat = fs.statSync(filePath);
            const now = new Date();
            const fileTime = new Date(stat.mtime);
            const diffTime = Math.abs(now - fileTime);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            return diffDays;
        } catch (error) {
            this.errorLog(`获取文件年龄失败 ${filePath}: ${error.message}`);
            return 0;
        };

    };

    
    /**
     * 清理过期日志文件
     */
    async deleteOldLogs() {
        try {
            this.log(`开始清理过期日志文件（保留${this.logMaxDays}天）...`);
            
            if (!fs.existsSync(this.logDir)) {
                this.log(`日志目录不存在: ${this.logDir}`);
                return { success: true, deleted: 0, message: '日志目录不存在' };
            }

            
            const files = fs.readdirSync(this.logDir);
            let deletedCount = 0;
            const errors = [];
            
            for (const file of files) {
                try {
                    const filePath = path.join(this.logDir, file);
                    const stat = fs.statSync(filePath);
                    
                    // 检查是否是文件且超过保留期限
                    if (stat.isFile() && Date.now() - stat.mtime.getTime() > this.logMaxDays * 24 * 60 * 60 * 1000) {
                        try {
                            fs.unlinkSync(filePath);
                            this.log(`已删除过期日志: ${file}`);
                            deletedCount++;
                        } catch (deleteError) {
                            const errorMsg = `删除日志文件失败 ${file}: ${deleteError.message}`;
                            errors.push(errorMsg);
                            this.errorLog(errorMsg);
                        }
                    }
                } catch (fileError) {
                    const errorMsg = `处理日志文件失败 ${file}: ${fileError.message}`;
                    errors.push(errorMsg);
                    this.errorLog(errorMsg);
                }
            }

            const result = { 
                success: errors.length === 0, 
                deleted: deletedCount,
                errors: errors
            };

            if (errors.length > 0) {
                this.log(`清理旧日志完成，但有 ${errors.length} 个错误`, 'warning');
            } else {
                this.log(`日志清理完成，共删除 ${deletedCount} 个过期日志文件`);
            }

            return result;
        } catch (error) {
            const errorMsg = `清理过期日志失败: ${error.message}`;
            this.errorLog(errorMsg);
            return { success: false, deleted: 0, error: errorMsg };
        }
    }

    
    /**
     * 清理备份文件，保持指定数量
     */
    cleanupBackupFiles() {
        try {
            this.log(`开始清理备份文件，保留最近的${this.backupMaxCount}个...`);
            
            if (!fs.existsSync(this.backupDir)) {
                this.log(`备份目录不存在: ${this.backupDir}`);
                return;
            }

            
            // 获取所有备份目录，按修改时间排序
            const backups = fs.readdirSync(this.backupDir)
                .filter(file => {
                    const filePath = path.join(this.backupDir, file);
                    return fs.statSync(filePath).isDirectory();
                })
                .map(file => {
                    const filePath = path.join(this.backupDir, file);
                    return {
                        name: file,
                        path: filePath,
                        mtime: fs.statSync(filePath).mtime.getTime()
                    };
                })
                .sort((a, b) => b.mtime - a.mtime); // 按修改时间降序排序
            
            // 删除超出数量的备份
            let deletedCount = 0;
            if (backups.length > this.backupMaxCount) {
                for (let i = this.backupMaxCount; i < backups.length; i++) {
                    this.deleteDirectory(backups[i].path);
                    this.log(`已删除旧备份: ${backups[i].name}`);
                    deletedCount++;
                }
            }

            
            this.log(`备份清理完成，共删除 ${deletedCount} 个备份目录`);
        } catch (error) {
            this.errorLog(`清理备份文件失败: ${error.message}`);
        }
    }

    
    /**
     * 删除目录及其内容
     */
    deleteDirectory(dirPath) {
        try {
            if (!fs.existsSync(dirPath)) {
                return;
            }
    
            const files = fs.readdirSync(dirPath);
            for (const file of files) {
                const filePath = path.join(dirPath, file);
                const stat = fs.statSync(filePath);
                
                if (stat.isDirectory()) {
                    this.deleteDirectory(filePath);
                } else {
                    fs.unlinkSync(filePath);
                }
            }
    
            
            fs.rmdirSync(dirPath);
        } catch (error) {
            this.errorLog(`删除目录失败 ${dirPath}: ${error.message}`);
        }
    }

    
    /**
     * 清理项目冗余文件
     */
    cleanupRedundantFiles() {
        try {
            this.log(`开始清理项目冗余文件...`);
            
            // 定义要清理的文件类型
            const redundantPatterns = [
                '*.tmp',
                '*.temp',
                '*~',
                '.DS_Store',
                'Thumbs.db'
            ];
            
            let deletedCount = 0;
            
            // 遍历所有文件
            function traverse(dir) {
                const files = fs.readdirSync(dir);
                
                for (const file of files) {
                    const filePath = path.join(dir, file);
                    const stat = fs.statSync(filePath);
                    
                    if (stat.isDirectory()) {
                        // 跳过某些特殊目录
                        if (file === 'node_modules' || file === '.git' || file === 'Logs' || file === 'Backups') {
                            continue;
                        }

                        traverse(filePath);
                    } else {
                        // 检查是否匹配冗余文件模式
                        for (const pattern of redundantPatterns) {
                            if (this.matchesPattern(file, pattern)) {
                                fs.unlinkSync(filePath);
                                this.log(`已删除冗余文件: ${filePath}`);
                                deletedCount++;
                                break;
                            }
                        }
                    }
                }
            }

            
            traverse.call(this, this.projectRoot);
            
            this.log(`冗余文件清理完成，共删除 ${deletedCount} 个文件`);
        } catch (error) {
            this.errorLog(`清理冗余文件失败: ${error.message}`);
        }
    }

    
    /**
     * 检查文件名是否匹配模式
     */
    matchesPattern(filename, pattern) {
        // 简单的通配符匹配
        const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
        return regex.test(filename);
    }

    
    /**
     * 执行清理任务
     */
    runCleanup() {
        this.log("=====================================");
        this.log("      项目清理管理器启动      ");
        this.log("=====================================");
        
        // 执行各项清理任务
        this.deleteOldLogs();
        this.cleanupBackupFiles();
        this.cleanupRedundantFiles();
        
        this.log("=====================================");
        this.log("      项目清理完成      ");
        this.log("=====================================");
    }

};


// 主函数
function main() {
    const cleanupManager = new CleanupManager();
    cleanupManager.runCleanup();
    
    // 设置定时清理（每周清理一次）
    setInterval(() => {
        cleanupManager.runCleanup();
    }, 7 * 24 * 60 * 60 * 1000);
}

// 执行主函数
if (require.main === module) {
    main();
}

module.exports = CleanupManager;