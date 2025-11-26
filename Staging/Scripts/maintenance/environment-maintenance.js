#!/usr/bin/env node

/**
 * MTSCOS AI 灰度测试环境维护脚本
 * 用途: 执行环境清理、过期文件删除、备份等维护任务
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const crypto = require('crypto');

class EnvironmentMaintenance {
    constructor() {
        // 基础配置
        this.basePath = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Staging';
        this.configPath = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/config/staging-environment.json';
        this.logFile = path.join(this.basePath, 'Logs/maintenance.log');
        
        // 维护配置
        this.maintenanceConfig = {
            cleaning: {
                enabled: true,
                tempFileAgeDays: 7,       // 临时文件保留天数
                logFileAgeDays: 30,       // 日志文件保留天数
                backupFileAgeDays: 90,    // 备份文件保留天数
                uploadFileAgeDays: 14,    // 上传文件保留天数
                excludePatterns: [        // 排除的文件模式
                    '.gitignore',
                    'README.md',
                    'config.json'
                ]
            },
            backup: {
                enabled: true,
                schedule: {
                    frequency: 'daily',    // daily, weekly, monthly
                    time: '02:00',         // 执行时间 (HH:MM)
                    dayOfWeek: 0,          // 周日是0，仅在weekly模式下使用
                    dayOfMonth: 1          // 仅在monthly模式下使用
                },
                retention: {
                    dailyBackups: 7,       // 保留7天的每日备份
                    weeklyBackups: 4,      // 保留4周的每周备份
                    monthlyBackups: 12     // 保留12个月的每月备份
                },
                compression: true,       // 是否压缩备份
                encryption: false,       // 是否加密备份
                includeDirectories: [    // 需要备份的目录
                    '../HTML',
                    '../assets',
                    '../config',
                    '../Scripts'
                ],
                excludeDirectories: [    // 排除的目录
                    'node_modules',
                    'Logs',
                    'Temp',
                    '.git'
                ],
                backupLocation: path.join(this.basePath, 'Backups')
            },
            systemChecks: {
                enabled: true,
                checkDiskSpace: true,
                checkPermissions: true,
                checkIntegrity: true,
                autoRepair: true         // 是否自动修复轻微问题
            }
        };
        
        // 状态变量
        this.isRunning = false;
        this.currentTask = null;
        this.lastRunResult = {
            timestamp: null,
            duration: 0,
            success: false,
            tasks: []
        };
    }

    /**
     * 初始化维护工具
     */
    async initialize() {
        try {
            this.log('==========================================');
            this.log('MTSCOS AI 灰度测试环境维护系统初始化');
            this.log('==========================================');
            
            // 确保日志目录存在
            this.ensureLogDirectory();
            
            // 加载配置
            await this.loadConfiguration();
            
            // 确保备份目录存在
            if (this.maintenanceConfig.backup.enabled) {
                this.ensureBackupDirectory();
            }
            
            this.log('维护系统初始化完成');
            return true;
        } catch (error) {
            this.logError('初始化失败', error);
            return false;
        }
    }

    /**
     * 确保日志目录存在
     */
    ensureLogDirectory() {
        const logDir = path.dirname(this.logFile);
        if (!fs.existsSync(logDir)) {
            fs.mkdirSync(logDir, { recursive: true });
            this.log(`创建日志目录: ${logDir}`);
        }
    }

    /**
     * 确保备份目录存在
     */
    ensureBackupDirectory() {
        if (!fs.existsSync(this.maintenanceConfig.backup.backupLocation)) {
            fs.mkdirSync(this.maintenanceConfig.backup.backupLocation, { recursive: true });
            this.log(`创建备份目录: ${this.maintenanceConfig.backup.backupLocation}`);
        }
    }

    /**
     * 加载配置
     */
    async loadConfiguration() {
        try {
            if (fs.existsSync(this.configPath)) {
                const configData = fs.readFileSync(this.configPath, 'utf8');
                const config = JSON.parse(configData);
                
                // 合并配置
                if (config.stagingEnvironment && config.stagingEnvironment.maintenance) {
                    this.maintenanceConfig = this.deepMerge(
                        this.maintenanceConfig,
                        config.stagingEnvironment.maintenance
                    );
                }
                
                this.log(`已加载配置: ${this.configPath}`);
            }
        } catch (error) {
            this.logError('加载配置失败', error);
            throw new Error('配置加载失败');
        }
    }

    /**
     * 深度合并对象
     */
    deepMerge(target, source) {
        const output = { ...target };
        
        if (this.isObject(target) && this.isObject(source)) {
            Object.keys(source).forEach(key => {
                if (this.isObject(source[key])) {
                    if (!(key in target)) {
                        Object.assign(output, { [key]: source[key] });
                    } else {
                        output[key] = this.deepMerge(target[key], source[key]);
                    }
                } else {
                    Object.assign(output, { [key]: source[key] });
                }
            });
        }
        
        return output;
    }

    /**
     * 检查是否为对象
     */
    isObject(item) {
        return item && typeof item === 'object' && !Array.isArray(item);
    }

    /**
     * 执行完整的维护流程
     */
    async runMaintenance() {
        if (this.isRunning) {
            this.log('维护任务已经在运行中');
            return this.lastRunResult;
        }
        
        const startTime = Date.now();
        this.isRunning = true;
        this.currentTask = 'maintenance';
        this.lastRunResult = {
            timestamp: new Date().toISOString(),
            duration: 0,
            success: false,
            tasks: []
        };
        
        try {
            this.log('开始执行完整维护流程...');
            
            // 执行系统检查
            if (this.maintenanceConfig.systemChecks.enabled) {
                const systemCheckResult = await this.runSystemChecks();
                this.lastRunResult.tasks.push(systemCheckResult);
            }
            
            // 执行清理任务
            if (this.maintenanceConfig.cleaning.enabled) {
                const cleaningResult = await this.runCleanup();
                this.lastRunResult.tasks.push(cleaningResult);
            }
            
            // 执行备份任务
            if (this.maintenanceConfig.backup.enabled) {
                const backupResult = await this.runBackup();
                this.lastRunResult.tasks.push(backupResult);
            }
            
            // 生成维护报告
            await this.generateMaintenanceReport();
            
            // 更新状态
            this.lastRunResult.duration = Date.now() - startTime;
            this.lastRunResult.success = true;
            
            this.log(`维护流程执行完成，耗时: ${(this.lastRunResult.duration / 1000).toFixed(2)}秒`);
            
            return this.lastRunResult;
        } catch (error) {
            this.logError('维护流程执行失败', error);
            
            this.lastRunResult.duration = Date.now() - startTime;
            this.lastRunResult.success = false;
            
            return this.lastRunResult;
        } finally {
            this.isRunning = false;
            this.currentTask = null;
        }
    }

    /**
     * 执行系统检查
     */
    async runSystemChecks() {
        this.log('开始执行系统检查...');
        this.currentTask = 'system-checks';
        
        const result = {
            type: 'system-checks',
            timestamp: new Date().toISOString(),
            duration: 0,
            success: false,
            checks: [],
            issues: [],
            repairs: []
        };
        
        const startTime = Date.now();
        
        try {
            // 检查磁盘空间
            if (this.maintenanceConfig.systemChecks.checkDiskSpace) {
                const diskResult = await this.checkDiskSpace();
                result.checks.push(diskResult);
                if (!diskResult.success) {
                    result.issues.push({ type: 'disk-space', details: diskResult });
                }
            }
            
            // 检查文件权限
            if (this.maintenanceConfig.systemChecks.checkPermissions) {
                const permResult = await this.checkPermissions();
                result.checks.push(permResult);
                if (!permResult.success) {
                    result.issues.push({ type: 'permissions', details: permResult });
                }
            }
            
            // 检查目录完整性
            if (this.maintenanceConfig.systemChecks.checkIntegrity) {
                const integrityResult = await this.checkDirectoryIntegrity();
                result.checks.push(integrityResult);
                if (!integrityResult.success) {
                    result.issues.push({ type: 'integrity', details: integrityResult });
                }
            }
            
            // 自动修复问题
            if (this.maintenanceConfig.systemChecks.autoRepair && result.issues.length > 0) {
                for (const issue of result.issues) {
                    const repairResult = await this.repairIssue(issue);
                    if (repairResult.success) {
                        result.repairs.push({
                            issueType: issue.type,
                            result: repairResult
                        });
                    }
                }
            }
            
            result.duration = Date.now() - startTime;
            result.success = result.issues.length === 0 || 
                           (this.maintenanceConfig.systemChecks.autoRepair && 
                            result.repairs.length === result.issues.length);
            
            this.log(`系统检查完成，耗时: ${(result.duration / 1000).toFixed(2)}秒`);
            if (result.issues.length > 0) {
                this.log(`发现 ${result.issues.length} 个问题，已修复 ${result.repairs.length} 个`);
            } else {
                this.log('系统检查通过，未发现问题');
            }
            
            return result;
        } catch (error) {
            this.logError('系统检查执行失败', error);
            
            result.duration = Date.now() - startTime;
            result.success = false;
            result.error = error.message;
            
            return result;
        }
    }

    /**
     * 检查磁盘空间
     */
    async checkDiskSpace() {
        const result = {
            name: 'disk-space',
            timestamp: new Date().toISOString(),
            success: true,
            details: null,
            warning: null
        };
        
        try {
            const diskInfo = this.getDiskInfo(this.basePath);
            result.details = diskInfo;
            
            // 检查磁盘空间阈值
            if (diskInfo.percentUsed > 90) {
                result.success = false;
                result.warning = `磁盘空间严重不足: ${diskInfo.percentUsed}% 已使用`;
                this.logError('磁盘空间检查失败', { 
                    percentUsed: diskInfo.percentUsed,
                    freeSpace: diskInfo.freeSpace
                });
            } else if (diskInfo.percentUsed > 80) {
                result.warning = `磁盘空间警告: ${diskInfo.percentUsed}% 已使用`;
                this.log(`磁盘空间警告: ${diskInfo.percentUsed}% 已使用`);
            }
            
            return result;
        } catch (error) {
            this.logError('获取磁盘空间信息失败', error);
            result.success = false;
            result.error = error.message;
            return result;
        }
    }

    /**
     * 获取磁盘信息
     */
    getDiskInfo(path) {
        try {
            // 在不同操作系统上可能需要调整命令
            const output = execSync('df -k ' + path).toString();
            const lines = output.trim().split('\n');
            const lastLine = lines[lines.length - 1];
            const parts = lastLine.split(/\s+/);
            
            const totalSize = parseInt(parts[1]) * 1024; // KB to bytes
            const usedSize = parseInt(parts[2]) * 1024;
            const freeSize = parseInt(parts[3]) * 1024;
            const percentUsed = parseInt(parts[4].replace('%', ''));
            
            return {
                totalSize,
                usedSize,
                freeSize,
                percentUsed,
                formatted: {
                    total: this.formatBytes(totalSize),
                    used: this.formatBytes(usedSize),
                    free: this.formatBytes(freeSize)
                }
            };
        } catch (error) {
            throw new Error(`获取磁盘信息失败: ${error.message}`);
        }
    }

    /**
     * 格式化字节数
     */
    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    /**
     * 检查文件权限
     */
    async checkPermissions() {
        const result = {
            name: 'permissions',
            timestamp: new Date().toISOString(),
            success: true,
            details: {
                checked: 0,
                issues: []
            }
        };
        
        try {
            const criticalDirs = [
                path.join(this.basePath, 'Scripts'),
                path.join(this.basePath, 'Backups'),
                path.join(this.basePath, 'Logs')
            ];
            
            for (const dirPath of criticalDirs) {
                if (fs.existsSync(dirPath)) {
                    result.details.checked++;
                    
                    try {
                        const stats = fs.statSync(dirPath);
                        const isWritable = stats.mode & fs.constants.W_OK;
                        const isReadable = stats.mode & fs.constants.R_OK;
                        
                        if (!isWritable || !isReadable) {
                            result.details.issues.push({
                                path: dirPath,
                                readable: isReadable,
                                writable: isWritable,
                                mode: stats.mode.toString(8)
                            });
                            result.success = false;
                        }
                    } catch (error) {
                        this.logError(`检查目录权限失败: ${dirPath}`, error);
                        result.details.issues.push({
                            path: dirPath,
                            error: error.message
                        });
                        result.success = false;
                    }
                }
            }
            
            // 检查脚本文件可执行权限
            const scriptDir = path.join(this.basePath, 'Scripts');
            if (fs.existsSync(scriptDir)) {
                const scriptFiles = fs.readdirSync(scriptDir, { recursive: true })
                    .filter(f => f.endsWith('.js') || f.endsWith('.sh'))
                    .map(f => path.join(scriptDir, f));
                
                for (const scriptPath of scriptFiles) {
                    if (fs.existsSync(scriptPath)) {
                        result.details.checked++;
                        
                        try {
                            const stats = fs.statSync(scriptPath);
                            const isExecutable = stats.mode & fs.constants.X_OK;
                            
                            if (!isExecutable && scriptPath.endsWith('.sh')) {
                                result.details.issues.push({
                                    path: scriptPath,
                                    executable: isExecutable,
                                    mode: stats.mode.toString(8)
                                });
                                result.success = false;
                            }
                        } catch (error) {
                            this.logError(`检查脚本权限失败: ${scriptPath}`, error);
                        }
                    }
                }
            }
            
            if (result.details.issues.length > 0) {
                this.logError('权限检查失败，发现以下问题', result.details.issues);
            } else {
                this.log('权限检查通过');
            }
            
            return result;
        } catch (error) {
            this.logError('权限检查执行失败', error);
            result.success = false;
            result.error = error.message;
            return result;
        }
    }

    /**
     * 检查目录完整性
     */
    async checkDirectoryIntegrity() {
        const result = {
            name: 'directory-integrity',
            timestamp: new Date().toISOString(),
            success: true,
            details: {
                requiredDirs: [],
                missingDirs: [],
                recoveredDirs: []
            }
        };
        
        try {
            const requiredDirs = [
                path.join(this.basePath, 'Backups'),
                path.join(this.basePath, 'Logs'),
                path.join(this.basePath, 'Results'),
                path.join(this.basePath, 'Scripts'),
                path.join(this.basePath, 'Temp'),
                path.join(this.basePath, 'Uploads'),
                path.join(this.basePath, 'Users'),
                path.join(this.basePath, 'Scripts/monitoring'),
                path.join(this.basePath, 'Scripts/maintenance'),
                path.join(this.basePath, 'Scripts/upgrades')
            ];
            
            result.details.requiredDirs = requiredDirs;
            
            for (const dirPath of requiredDirs) {
                if (!fs.existsSync(dirPath)) {
                    result.details.missingDirs.push(dirPath);
                    result.success = false;
                    
                    // 尝试恢复目录
                    if (this.maintenanceConfig.systemChecks.autoRepair) {
                        try {
                            fs.mkdirSync(dirPath, { recursive: true });
                            result.details.recoveredDirs.push(dirPath);
                            this.log(`已恢复缺失的目录: ${dirPath}`);
                        } catch (error) {
                            this.logError(`恢复目录失败: ${dirPath}`, error);
                        }
                    }
                }
            }
            
            if (result.details.missingDirs.length > 0) {
                this.logError('目录完整性检查失败', {
                    missingDirs: result.details.missingDirs,
                    recoveredDirs: result.details.recoveredDirs
                });
            } else {
                this.log('目录完整性检查通过');
            }
            
            return result;
        } catch (error) {
            this.logError('目录完整性检查执行失败', error);
            result.success = false;
            result.error = error.message;
            return result;
        }
    }

    /**
     * 修复问题
     */
    async repairIssue(issue) {
        const result = {
            success: false,
            message: '',
            details: null
        };
        
        try {
            this.log(`尝试修复问题类型: ${issue.type}`);
            
            switch (issue.type) {
                case 'permissions':
                    // 修复权限问题
                    for (const permissionIssue of issue.details.details.issues) {
                        try {
                            if (permissionIssue.path) {
                                // 设置适当的权限
                                fs.chmodSync(permissionIssue.path, '755');
                                this.log(`已修复权限: ${permissionIssue.path}`);
                            }
                        } catch (error) {
                            this.logError(`修复权限失败: ${permissionIssue.path}`, error);
                        }
                    }
                    result.success = true;
                    result.message = '权限问题修复完成';
                    break;
                    
                case 'disk-space':
                    // 尝试清理临时文件来释放空间
                    const cleanupResult = await this.cleanTempFiles();
                    if (cleanupResult.bytesDeleted > 0) {
                        result.success = true;
                        result.message = `已清理临时文件，释放 ${this.formatBytes(cleanupResult.bytesDeleted)} 空间`;
                    } else {
                        result.success = false;
                        result.message = '无法自动清理足够的磁盘空间，请手动清理';
                    }
                    break;
                    
                case 'integrity':
                    // 目录完整性问题已在检查过程中尝试修复
                    result.success = issue.details.details.recoveredDirs.length > 0;
                    result.message = `已恢复 ${issue.details.details.recoveredDirs.length} 个缺失的目录`;
                    break;
                    
                default:
                    this.log(`未知的问题类型: ${issue.type}`);
                    result.message = `未知的问题类型: ${issue.type}`;
            }
            
            return result;
        } catch (error) {
            this.logError(`修复问题失败: ${issue.type}`, error);
            result.message = error.message;
            return result;
        }
    }

    /**
     * 执行清理任务
     */
    async runCleanup() {
        this.log('开始执行清理任务...');
        this.currentTask = 'cleanup';
        
        const result = {
            type: 'cleanup',
            timestamp: new Date().toISOString(),
            duration: 0,
            success: false,
            tasks: [],
            summary: {
                filesDeleted: 0,
                directoriesDeleted: 0,
                bytesDeleted: 0
            }
        };
        
        const startTime = Date.now();
        
        try {
            // 清理临时文件
            const tempCleanupResult = await this.cleanTempFiles();
            result.tasks.push(tempCleanupResult);
            
            // 清理日志文件
            const logCleanupResult = await this.cleanLogFiles();
            result.tasks.push(logCleanupResult);
            
            // 清理备份文件
            const backupCleanupResult = await this.cleanBackupFiles();
            result.tasks.push(backupCleanupResult);
            
            // 清理上传文件
            const uploadCleanupResult = await this.cleanUploadFiles();
            result.tasks.push(uploadCleanupResult);
            
            // 汇总结果
            result.summary.filesDeleted = result.tasks.reduce(
                (sum, task) => sum + (task.filesDeleted || 0), 0
            );
            result.summary.directoriesDeleted = result.tasks.reduce(
                (sum, task) => sum + (task.directoriesDeleted || 0), 0
            );
            result.summary.bytesDeleted = result.tasks.reduce(
                (sum, task) => sum + (task.bytesDeleted || 0), 0
            );
            
            result.duration = Date.now() - startTime;
            result.success = true;
            
            this.log(`清理任务完成，耗时: ${(result.duration / 1000).toFixed(2)}秒`);
            this.log(`已删除 ${result.summary.filesDeleted} 个文件，释放 ${this.formatBytes(result.summary.bytesDeleted)} 空间`);
            
            return result;
        } catch (error) {
            this.logError('清理任务执行失败', error);
            
            result.duration = Date.now() - startTime;
            result.success = false;
            result.error = error.message;
            
            return result;
        }
    }

    /**
     * 清理临时文件
     */
    async cleanTempFiles() {
        const result = {
            name: 'clean-temp-files',
            timestamp: new Date().toISOString(),
            success: true,
            filesDeleted: 0,
            bytesDeleted: 0,
            details: []
        };
        
        try {
            const tempDir = path.join(this.basePath, 'Temp');
            if (fs.existsSync(tempDir)) {
                const maxAgeMs = this.maintenanceConfig.cleaning.tempFileAgeDays * 24 * 60 * 60 * 1000;
                const now = Date.now();
                
                function cleanDirectory(dir) {
                    const entries = fs.readdirSync(dir, { withFileTypes: true });
                    
                    for (const entry of entries) {
                        const fullPath = path.join(dir, entry.name);
                        const stats = fs.statSync(fullPath);
                        
                        // 检查是否应该排除
                        if (this.maintenanceConfig.cleaning.excludePatterns.some(pattern => 
                            entry.name.includes(pattern)
                        )) {
                            continue;
                        }
                        
                        if (entry.isDirectory()) {
                            cleanDirectory.call(this, fullPath);
                            
                            // 检查目录是否为空且过期
                            const subEntries = fs.readdirSync(fullPath);
                            if (subEntries.length === 0 && (now - stats.mtimeMs) > maxAgeMs) {
                                fs.rmdirSync(fullPath);
                                result.details.push({ 
                                    path: fullPath, 
                                    type: 'directory', 
                                    reason: '过期且为空'
                                });
                            }
                        } else if ((now - stats.mtimeMs) > maxAgeMs) {
                            // 删除过期文件
                            fs.unlinkSync(fullPath);
                            result.filesDeleted++;
                            result.bytesDeleted += stats.size;
                            result.details.push({ 
                                path: fullPath, 
                                type: 'file', 
                                size: stats.size,
                                age: Math.floor((now - stats.mtimeMs) / (24 * 60 * 60 * 1000)) + ' 天'
                            });
                        }
                    }
                }
                
                cleanDirectory.call(this, tempDir);
                
                this.log(`临时文件清理完成: 删除 ${result.filesDeleted} 个文件，释放 ${this.formatBytes(result.bytesDeleted)}`);
            } else {
                this.log('临时目录不存在，跳过清理');
            }
            
            return result;
        } catch (error) {
            this.logError('清理临时文件失败', error);
            result.success = false;
            result.error = error.message;
            return result;
        }
    }

    /**
     * 清理日志文件
     */
    async cleanLogFiles() {
        const result = {
            name: 'clean-log-files',
            timestamp: new Date().toISOString(),
            success: true,
            filesDeleted: 0,
            bytesDeleted: 0,
            details: []
        };
        
        try {
            const logDir = path.join(this.basePath, 'Logs');
            if (fs.existsSync(logDir)) {
                const maxAgeMs = this.maintenanceConfig.cleaning.logFileAgeDays * 24 * 60 * 60 * 1000;
                const now = Date.now();
                
                const logFiles = fs.readdirSync(logDir)
                    .filter(f => f.endsWith('.log') || f.endsWith('.json'))
                    .map(f => path.join(logDir, f));
                
                for (const logFilePath of logFiles) {
                    try {
                        const stats = fs.statSync(logFilePath);
                        
                        // 保留当前日期的日志文件
                        const fileName = path.basename(logFilePath);
                        const today = new Date().toISOString().split('T')[0];
                        if (fileName.includes(today)) {
                            continue;
                        }
                        
                        if ((now - stats.mtimeMs) > maxAgeMs) {
                            // 删除过期日志文件
                            fs.unlinkSync(logFilePath);
                            result.filesDeleted++;
                            result.bytesDeleted += stats.size;
                            result.details.push({ 
                                path: logFilePath, 
                                size: stats.size,
                                age: Math.floor((now - stats.mtimeMs) / (24 * 60 * 60 * 1000)) + ' 天'
                            });
                        }
                    } catch (error) {
                        this.logError(`清理日志文件失败: ${logFilePath}`, error);
                    }
                }
                
                this.log(`日志文件清理完成: 删除 ${result.filesDeleted} 个文件，释放 ${this.formatBytes(result.bytesDeleted)}`);
            } else {
                this.log('日志目录不存在，跳过清理');
            }
            
            return result;
        } catch (error) {
            this.logError('清理日志文件失败', error);
            result.success = false;
            result.error = error.message;
            return result;
        }
    }

    /**
     * 清理备份文件
     */
    async cleanBackupFiles() {
        const result = {
            name: 'clean-backup-files',
            timestamp: new Date().toISOString(),
            success: true,
            filesDeleted: 0,
            bytesDeleted: 0,
            details: []
        };
        
        try {
            const backupDir = this.maintenanceConfig.backup.backupLocation;
            if (fs.existsSync(backupDir)) {
                const maxAgeMs = this.maintenanceConfig.cleaning.backupFileAgeDays * 24 * 60 * 60 * 1000;
                const now = Date.now();
                
                const backupFiles = fs.readdirSync(backupDir)
                    .filter(f => f.includes('backup') && (f.endsWith('.zip') || f.endsWith('.tar.gz')))
                    .map(f => path.join(backupDir, f));
                
                // 按日期分组备份文件
                const dailyBackups = [];
                const weeklyBackups = [];
                const monthlyBackups = [];
                const otherBackups = [];
                
                for (const backupFile of backupFiles) {
                    try {
                        const stats = fs.statSync(backupFile);
                        const fileName = path.basename(backupFile);
                        
                        if (fileName.includes('daily')) {
                            dailyBackups.push({ path: backupFile, mtime: stats.mtimeMs, size: stats.size });
                        } else if (fileName.includes('weekly')) {
                            weeklyBackups.push({ path: backupFile, mtime: stats.mtimeMs, size: stats.size });
                        } else if (fileName.includes('monthly')) {
                            monthlyBackups.push({ path: backupFile, mtime: stats.mtimeMs, size: stats.size });
                        } else {
                            otherBackups.push({ path: backupFile, mtime: stats.mtimeMs, size: stats.size });
                        }
                    } catch (error) {
                        this.logError(`处理备份文件失败: ${backupFile}`, error);
                    }
                }
                
                // 保留最近的备份文件，删除旧的
                const deleteOldBackups = (backups, keepCount) => {
                    // 按时间排序，最新的在前
                    backups.sort((a, b) => b.mtime - a.mtime);
                    
                    // 删除超出保留数量的备份
                    for (let i = keepCount; i < backups.length; i++) {
                        try {
                            fs.unlinkSync(backups[i].path);
                            result.filesDeleted++;
                            result.bytesDeleted += backups[i].size;
                            result.details.push({ 
                                path: backups[i].path, 
                                size: backups[i].size,
                                reason: `超过保留数量(${keepCount})`
                            });
                        } catch (error) {
                            this.logError(`删除备份文件失败: ${backups[i].path}`, error);
                        }
                    }
                };
                
                deleteOldBackups(dailyBackups, this.maintenanceConfig.backup.retention.dailyBackups);
                deleteOldBackups(weeklyBackups, this.maintenanceConfig.backup.retention.weeklyBackups);
                deleteOldBackups(monthlyBackups, this.maintenanceConfig.backup.retention.monthlyBackups);
                
                // 对于其他备份文件，使用通用过期策略
                for (const backup of otherBackups) {
                    if ((now - backup.mtime) > maxAgeMs) {
                        try {
                            fs.unlinkSync(backup.path);
                            result.filesDeleted++;
                            result.bytesDeleted += backup.size;
                            result.details.push({ 
                                path: backup.path, 
                                size: backup.size,
                                age: Math.floor((now - backup.mtime) / (24 * 60 * 60 * 1000)) + ' 天'
                            });
                        } catch (error) {
                            this.logError(`删除备份文件失败: ${backup.path}`, error);
                        }
                    }
                }
                
                this.log(`备份文件清理完成: 删除 ${result.filesDeleted} 个文件，释放 ${this.formatBytes(result.bytesDeleted)}`);
            } else {
                this.log('备份目录不存在，跳过清理');
            }
            
            return result;
        } catch (error) {
            this.logError('清理备份文件失败', error);
            result.success = false;
            result.error = error.message;
            return result;
        }
    }

    /**
     * 清理上传文件
     */
    async cleanUploadFiles() {
        const result = {
            name: 'clean-upload-files',
            timestamp: new Date().toISOString(),
            success: true,
            filesDeleted: 0,
            bytesDeleted: 0,
            details: []
        };
        
        try {
            const uploadDir = path.join(this.basePath, 'Uploads');
            if (fs.existsSync(uploadDir)) {
                const maxAgeMs = this.maintenanceConfig.cleaning.uploadFileAgeDays * 24 * 60 * 60 * 1000;
                const now = Date.now();
                
                function cleanDirectory(dir) {
                    const entries = fs.readdirSync(dir, { withFileTypes: true });
                    
                    for (const entry of entries) {
                        const fullPath = path.join(dir, entry.name);
                        
                        if (entry.isDirectory()) {
                            cleanDirectory.call(this, fullPath);
                            
                            // 检查目录是否为空
                            const subEntries = fs.readdirSync(fullPath);
                            if (subEntries.length === 0) {
                                try {
                                    fs.rmdirSync(fullPath);
                                    result.details.push({ 
                                        path: fullPath, 
                                        type: 'directory', 
                                        reason: '空目录'
                                    });
                                } catch (error) {
                                    this.logError(`删除空目录失败: ${fullPath}`, error);
                                }
                            }
                        } else {
                            try {
                                const stats = fs.statSync(fullPath);
                                if ((now - stats.mtimeMs) > maxAgeMs) {
                                    // 删除过期文件
                                    fs.unlinkSync(fullPath);
                                    result.filesDeleted++;
                                    result.bytesDeleted += stats.size;
                                    result.details.push({ 
                                        path: fullPath, 
                                        size: stats.size,
                                        age: Math.floor((now - stats.mtimeMs) / (24 * 60 * 60 * 1000)) + ' 天'
                                    });
                                }
                            } catch (error) {
                                this.logError(`处理上传文件失败: ${fullPath}`, error);
                            }
                        }
                    }
                }
                
                cleanDirectory.call(this, uploadDir);
                
                this.log(`上传文件清理完成: 删除 ${result.filesDeleted} 个文件，释放 ${this.formatBytes(result.bytesDeleted)}`);
            } else {
                this.log('上传目录不存在，跳过清理');
            }
            
            return result;
        } catch (error) {
            this.logError('清理上传文件失败', error);
            result.success = false;
            result.error = error.message;
            return result;
        }
    }

    /**
     * 执行备份任务
     */
    async runBackup() {
        this.log('开始执行备份任务...');
        this.currentTask = 'backup';
        
        const result = {
            type: 'backup',
            timestamp: new Date().toISOString(),
            duration: 0,
            success: false,
            backupType: this.determineBackupType(),
            backupPath: null,
            size: 0,
            details: null
        };
        
        const startTime = Date.now();
        
        try {
            // 确保备份目录存在
            this.ensureBackupDirectory();
            
            // 生成备份文件名
            const backupFileName = this.generateBackupFileName(result.backupType);
            const backupFilePath = path.join(this.maintenanceConfig.backup.backupLocation, backupFileName);
            
            // 执行备份
            const backupResult = await this.performBackup(backupFilePath);
            
            result.backupPath = backupFilePath;
            result.size = backupResult.size;
            result.details = backupResult;
            result.duration = Date.now() - startTime;
            result.success = true;
            
            this.log(`备份任务完成，耗时: ${(result.duration / 1000).toFixed(2)}秒`);
            this.log(`备份文件: ${backupFileName}, 大小: ${this.formatBytes(result.size)}`);
            
            return result;
        } catch (error) {
            this.logError('备份任务执行失败', error);
            
            result.duration = Date.now() - startTime;
            result.success = false;
            result.error = error.message;
            
            return result;
        }
    }

    /**
     * 确定备份类型
     */
    determineBackupType() {
        const now = new Date();
        const dayOfWeek = now.getDay();
        const dayOfMonth = now.getDate();
        
        // 根据配置和当前日期确定备份类型
        switch (this.maintenanceConfig.backup.schedule.frequency) {
            case 'daily':
                return 'daily';
            case 'weekly':
                return dayOfWeek === this.maintenanceConfig.backup.schedule.dayOfWeek ? 'weekly' : null;
            case 'monthly':
                return dayOfMonth === this.maintenanceConfig.backup.schedule.dayOfMonth ? 'monthly' : null;
            default:
                return 'manual';
        }
    }

    /**
     * 生成备份文件名
     */
    generateBackupFileName(backupType) {
        const now = new Date();
        const dateStr = now.toISOString().split('T')[0].replace(/-/g, '');
        const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '');
        
        let prefix = 'backup';
        if (backupType) {
            prefix += `_${backupType}`;
        }
        
        const extension = this.maintenanceConfig.backup.compression ? '.tar.gz' : '.tar';
        
        return `${prefix}_${dateStr}_${timeStr}${extension}`;
    }

    /**
     * 执行备份操作
     */
    async performBackup(backupFilePath) {
        const result = {
            filesBackedUp: 0,
            directoriesBackedUp: 0,
            size: 0,
            errors: []
        };
        
        try {
            // 构建tar命令
            let tarCommand = 'tar';
            const args = ['-cf'];
            
            if (this.maintenanceConfig.backup.compression) {
                args.push('-z');
            }
            
            args.push(backupFilePath);
            
            // 添加要备份的目录
            const baseDir = path.dirname(this.basePath); // 项目根目录
            
            for (const includePath of this.maintenanceConfig.backup.includeDirectories) {
                const fullPath = path.resolve(baseDir, includePath);
                if (fs.existsSync(fullPath)) {
                    const relativePath = path.relative(baseDir, fullPath);
                    args.push('-C', baseDir, relativePath);
                }
            }
            
            // 执行备份命令
            this.log(`执行备份命令: ${tarCommand} ${args.join(' ')}`);
            
            const tarProcess = spawn(tarCommand, args, {
                cwd: baseDir,
                stdio: 'inherit'
            });
            
            await new Promise((resolve, reject) => {
                tarProcess.on('close', (code) => {
                    if (code === 0) {
                        resolve();
                    } else {
                        reject(new Error(`tar命令执行失败，退出码: ${code}`));
                    }
                });
                
                tarProcess.on('error', (error) => {
                    reject(new Error(`备份过程失败: ${error.message}`));
                });
            });
            
            // 获取备份文件大小
            const stats = fs.statSync(backupFilePath);
            result.size = stats.size;
            
            // 统计备份的文件数量（近似值）
            let totalFiles = 0;
            let totalDirs = 0;
            
            function countFiles(dir, excludePatterns) {
                try {
                    const entries = fs.readdirSync(dir, { withFileTypes: true });
                    
                    for (const entry of entries) {
                        const fullPath = path.join(dir, entry.name);
                        
                        // 检查是否应该排除
                        if (excludePatterns.some(pattern => 
                            fullPath.includes(pattern)
                        )) {
                            continue;
                        }
                        
                        if (entry.isDirectory()) {
                            totalDirs++;
                            countFiles(fullPath, excludePatterns);
                        } else {
                            totalFiles++;
                        }
                    }
                } catch (error) {
                    this.logError(`统计文件数量失败: ${dir}`, error);
                    result.errors.push(`统计文件数量失败: ${dir}`);
                }
            }
            
            for (const includePath of this.maintenanceConfig.backup.includeDirectories) {
                const fullPath = path.resolve(baseDir, includePath);
                if (fs.existsSync(fullPath)) {
                    countFiles(fullPath, this.maintenanceConfig.backup.excludeDirectories);
                }
            }
            
            result.filesBackedUp = totalFiles;
            result.directoriesBackedUp = totalDirs;
            
            return result;
        } catch (error) {
            this.logError('执行备份失败', error);
            result.errors.push(error.message);
            throw error;
        }
    }

    /**
     * 生成维护报告
     */
    async generateMaintenanceReport() {
        try {
            const report = {
                timestamp: new Date().toISOString(),
                environment: 'staging',
                maintenanceResult: this.lastRunResult,
                systemInfo: {
                    nodeVersion: process.version,
                    platform: process.platform,
                    arch: process.arch
                },
                resourceUsage: {
                    disk: this.getDiskInfo(this.basePath)
                }
            };
            
            const reportPath = path.join(
                this.basePath,
                'Logs',
                `maintenance-report-${new Date().toISOString().split('T')[0]}.json`
            );
            
            fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
            this.log(`维护报告已生成: ${reportPath}`);
            
            return report;
        } catch (error) {
            this.logError('生成维护报告失败', error);
            throw error;
        }
    }

    /**
     * 记录日志
     */
    log(message, data = null) {
        const timestamp = new Date().toISOString();
        let logEntry = `[${timestamp}] INFO: ${message}`;
        
        if (data) {
            logEntry += ' ' + JSON.stringify(data);
        }
        
        console.log(logEntry);
        
        try {
            fs.appendFileSync(this.logFile, logEntry + '\n');
        } catch (error) {
            console.error('写入日志失败:', error);
        }
    }

    /**
     * 记录错误日志
     */
    logError(message, error) {
        const timestamp = new Date().toISOString();
        let logEntry = `[${timestamp}] ERROR: ${message}`;
        
        if (error && typeof error === 'object') {
            if (error.stack) {
                logEntry += '\n' + error.stack;
            } else {
                logEntry += ' ' + JSON.stringify(error);
            }
        } else if (error) {
            logEntry += ' ' + String(error);
        }
        
        console.error(logEntry);
        
        try {
            fs.appendFileSync(this.logFile, logEntry + '\n');
        } catch (err) {
            console.error('写入错误日志失败:', err);
        }
    }
}

// 主函数
async function main() {
    const maintenance = new EnvironmentMaintenance();
    
    // 解析命令行参数
    const args = process.argv.slice(2);
    const command = args[0] || 'run';
    
    // 初始化维护工具
    const initialized = await maintenance.initialize();
    if (!initialized) {
        console.error('维护系统初始化失败，无法执行');
        process.exit(1);
    }
    
    // 根据命令执行不同操作
    switch (command) {
        case 'run':
            // 执行完整维护流程
            await maintenance.runMaintenance();
            break;
            
        case 'cleanup':
            // 仅执行清理任务
            await maintenance.runCleanup();
            break;
            
        case 'backup':
            // 仅执行备份任务
            await maintenance.runBackup();
            break;
            
        case 'check':
            // 仅执行系统检查
            await maintenance.runSystemChecks();
            break;
            
        default:
            console.log('未知命令。可用命令: run, cleanup, backup, check');
            process.exit(1);
    }
}

// 如果直接运行此脚本
if (require.main === module) {
    main().catch(error => {
        console.error('维护任务执行失败:', error);
        process.exit(1);
    });
}

module.exports = EnvironmentMaintenance;