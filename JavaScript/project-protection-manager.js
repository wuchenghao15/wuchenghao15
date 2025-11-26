// MTSCOS 项目自我保护和管理系统
// 作者: Chenghao Wu
// 版本: 2.0.0
// 功能: 文件完整性检查、自动备份、安全监控、性能优化

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { exec } = require('child_process');
const os = require('os');

class ProjectProtectionManager {
    constructor() {
        this.rootDir = path.dirname(path.dirname(__filename));
        this.config = {
            // 备份配置
            backup: {
                enabled: true,
                interval: 30 * 60 * 1000, // 30分钟
                maxBackups: 15,
                excludeDirs: ['Backups', '.git', 'node_modules', '.snapshots'],
                excludeFiles: ['.DS_Store', '*.tmp', '*.log']
            },
            // 文件监控配置
            fileMonitor: {
                enabled: true,
                interval: 60 * 1000, // 1分钟
                criticalExtensions: ['.js', '.html', '.css', '.json', '.sh'],
                hashAlgorithm: 'sha256'
            },
            // 安全配置
            security: {
                enabled: true,
                scanInterval: 5 * 60 * 1000, // 5分钟
                maxFileSize: 10 * 1024 * 1024, // 10MB
                suspiciousPatterns: [
                    /eval\s*\(/gi,
                    /document\.write\s*\(/gi,
                    /innerHTML\s*=/gi,
                    /outerHTML\s*=/gi
                ]
            },
            // 性能配置
            performance: {
                enabled: true,
                memoryThreshold: 0.8, // 80%
                cpuThreshold: 0.7, // 70%
                diskThreshold: 0.9 // 90%
            }
        };

        this.state = {
            lastBackup: null,
            fileHashes: new Map(),
            suspiciousFiles: new Set(),
            protectedFiles: new Set(),
            metrics: {
                backupCount: 0,
                securityScans: 0,
                fileChanges: 0,
                errors: 0
            }
        };

        this.logDir = path.join(this.rootDir, 'Logs');
        this.backupDir = path.join(this.rootDir, 'Backups');
        this.ensureDirectories().catch(error => console.error(`[project-protection-manager.js] this.ensureDirectories failed:`, error));
        this.initializeFileHashes();
    }

    // 确保必要的目录存在
    ensureDirectories() {
        [this.logDir, this.backupDir].forEach(dir => {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
        });
    }

    // 日志记录
    log(level, message, data = null) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logMessage = `[${timestamp}] [${level.toUpperCase().catch(error => console.error(`[project-protection-manager.js] level.toUpperCase failed:`, error))}] ${message}`;
        console.log(logMessage);
        
        const logFile = path.join(this.logDir, 'project_protection.log');
        fs.appendFileSync(logFile, logMessage + '\n');
        
        if (data) {
            fs.appendFileSync(logFile, `  Data: ${JSON.stringify(data, null, 2)}\n`);
        }
    }

    // 初始化文件哈希
    initializeFileHashes() {
        this.log('info', '初始化文件完整性检查...');
        this.scanProjectFiles().catch(error => console.error(`[project-protection-manager.js] this.scanProjectFiles failed:`, error));
    }

    // 扫描项目文件
    scanProjectFiles() {
        const scanDir = (dir, relativePath = '') => {
            const items = fs.readdirSync(dir);
            
            for (const item of items) {
                const fullPath = path.join(dir, item);
                const itemRelativePath = path.join(relativePath, item);
                
                // 跳过排除的目录
                if (this.config.backup.excludeDirs.some(excluded => 
                    itemRelativePath.includes(excluded))) {
                    continue;
                }
                
                const stat = fs.statSync(fullPath);
                
                if (stat.isDirectory().catch(error => console.error(`[project-protection-manager.js] stat.isDirectory failed:`, error))) {
                    scanDir(fullPath, itemRelativePath);
                } else if (stat.isFile().catch(error => console.error(`[project-protection-manager.js] stat.isFile failed:`, error))) {
                    // 计算文件哈希
                    try {
                        const hash = this.calculateFileHash(fullPath);
                        this.state.fileHashes.set(itemRelativePath, {
                            hash,
                            size: stat.size,
                            modified: stat.mtime
                        });
                    } catch (error) {
                        this.log('error', `无法计算文件哈希: ${itemRelativePath}`, error.message);
                    }
                }
            }
        };
        
        scanDir(this.rootDir);
        this.log('info', `文件完整性检查完成，共扫描 ${this.state.fileHashes.size} 个文件`);
    }

    // 计算文件哈希
    calculateFileHash(filePath) {
        const content = fs.readFileSync(filePath);
        return crypto.createHash(this.config.fileMonitor.hashAlgorithm).update(content).digest('hex');
    }

    // 检查文件完整性
    checkFileIntegrity() {
        this.log('info', '开始文件完整性检查...');
        const changes = [];
        
        for (const [relativePath, fileInfo] of this.state.fileHashes) {
            const fullPath = path.join(this.rootDir, relativePath);
            
            if (!fs.existsSync(fullPath)) {
                changes.push({ type: 'deleted', path: relativePath });
                continue;
            }
            
            try {
                const currentHash = this.calculateFileHash(fullPath);
                if (currentHash !== fileInfo.hash) {
                    changes.push({ 
                        type: 'modified', 
                        path: relativePath,
                        oldHash: fileInfo.hash,
                        newHash: currentHash
                    });
                    
                    // 更新哈希记录
                    this.state.fileHashes.set(relativePath, {
                        hash: currentHash,
                        size: fs.statSync(fullPath).size,
                        modified: fs.statSync(fullPath).mtime
                    });
                }
            } catch (error) {
                this.log('error', `检查文件时出错: ${relativePath}`, error.message);
            }
        }
        
        if (changes.length > 0) {
            this.state.metrics.fileChanges += changes.length;
            this.log('warning', `检测到 ${changes.length} 个文件变更`, changes);
            
            // 如果有关键文件变更，触发备份
            const criticalChanges = changes.filter(change => 
                this.config.fileMonitor.criticalExtensions.some(ext => 
                    change.path.endsWith(ext)
                )
            );
            
            if (criticalChanges.length > 0) {
                this.log('warning', `检测到关键文件变更，触发自动备份`);
                this.performBackup().catch(error => console.error(`[project-protection-manager.js] this.performBackup failed:`, error));
            }
        }
        
        return changes;
    }

    // 执行备份
    performBackup() {
        if (!this.config.backup.enabled) {
            return;
        }
        
        this.log('info', '开始执行自动备份...');
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
        const version = this.getProjectVersion().catch(error => console.error(`[project-protection-manager.js] this.getProjectVersion failed:`, error));
        const backupName = `backup_${timestamp}_v${version}`;
        const backupPath = path.join(this.backupDir, backupName);
        
        try {
            // 创建备份目录
            fs.mkdirSync(backupPath, { recursive: true });
            
            // 复制项目文件
            this.copyProject(this.rootDir, backupPath);
            
            // 创建备份信息文件
            const backupInfo = {
                timestamp: new Date().toISOString(),
                version,
                fileCount: this.state.fileHashes.size,
                metrics: { ...this.state.metrics }
            };
            fs.writeFileSync(
                path.join(backupPath, 'backup_info.json'), 
                JSON.stringify(backupInfo, null, 2)
            );
            
            this.state.lastBackup = new Date();
            this.state.metrics.backupCount++;
            this.log('info', `备份完成: ${backupName}`);
            
            // 清理旧备份
            this.cleanupOldBackups().catch(error => console.error(`[project-protection-manager.js] this.cleanupOldBackups failed:`, error));
            
        } catch (error) {
            this.state.metrics.errors++;
            this.log('error', '备份失败', error.message);
        }
    }

    // 复制项目文件
    copyProject(src, dest) {
        const copyDir = (srcDir, destDir) => {
            if (!fs.existsSync(destDir)) {
                fs.mkdirSync(destDir, { recursive: true });
            }
            
            const items = fs.readdirSync(srcDir);
            
            for (const item of items) {
                const srcPath = path.join(srcDir, item);
                const destPath = path.join(destDir, item);
                
                // 跳过排除的目录和文件
                if (this.config.backup.excludeDirs.includes(item) ||
                    this.config.backup.excludeFiles.some(pattern => 
                        item.match(pattern.replace('*', '.*'))
                    )) {
                    continue;
                }
                
                const stat = fs.statSync(srcPath);
                
                if (stat.isDirectory().catch(error => console.error(`[project-protection-manager.js] stat.isDirectory failed:`, error))) {
                    copyDir(srcPath, destPath);
                } else {
                    fs.copyFileSync(srcPath, destPath);
                }
            }
        };
        
        copyDir(src, dest);
    }

    // 清理旧备份
    cleanupOldBackups() {
        try {
            const backups = fs.readdirSync(this.backupDir)
                .filter(item => item.startsWith('backup_'))
                .map(item => ({
                    name: item,
                    path: path.join(this.backupDir, item),
                    stat: fs.statSync(path.join(this.backupDir, item))
                }))
                .sort((a, b) => b.stat.mtime - a.stat.mtime);
            
            if (backups.length > this.config.backup.maxBackups) {
                const toDelete = backups.slice(this.config.backup.maxBackups);
                toDelete.forEach(backup => {
                    this.deleteDirectory(backup.path);
                    this.log('info', `已删除旧备份: ${backup.name}`);
                });
            }
        } catch (error) {
            this.log('error', '清理旧备份失败', error.message);
        }
    }

    // 递归删除目录
    deleteDirectory(dirPath) {
        if (fs.existsSync(dirPath)) {
            fs.rmSync(dirPath, { recursive: true, force: true });
        }
    }

    // 安全扫描
    performSecurityScan() {
        if (!this.config.security.enabled) {
            return;
        }
        
        this.log('info', '开始安全扫描...');
        const suspiciousFiles = [];
        
        for (const [relativePath, fileInfo] of this.state.fileHashes) {
            const fullPath = path.join(this.rootDir, relativePath);
            
            // 检查文件大小
            if (fileInfo.size > this.config.security.maxFileSize) {
                suspiciousFiles.push({
                    path: relativePath,
                    reason: '文件过大',
                    size: fileInfo.size
                });
                continue;
            }
            
            // 检查可疑模式
            if (this.config.fileMonitor.criticalExtensions.some(ext => 
                relativePath.endsWith(ext))) {
                try {
                    const content = fs.readFileSync(fullPath, 'utf8');
                    
                    for (const pattern of this.config.security.suspiciousPatterns) {
                        if (pattern.test(content)) {
                            suspiciousFiles.push({
                                path: relativePath,
                                reason: `检测到可疑模式: ${pattern.source}`,
                                pattern: pattern.source
                            });
                            break;
                        }
                    }
                } catch (error) {
                    // 忽略二进制文件的读取错误
                }
            }
        }
        
        this.state.metrics.securityScans++;
        
        if (suspiciousFiles.length > 0) {
            this.log('warning', `安全扫描发现 ${suspiciousFiles.length} 个可疑文件`, suspiciousFiles);
            suspiciousFiles.forEach(file => {
                this.state.suspiciousFiles.add(file.path);
            });
        } else {
            this.log('info', '安全扫描完成，未发现威胁');
        }
        
        return suspiciousFiles;
    }

    // 性能监控
    checkPerformance() {
        if (!this.config.performance.enabled) {
            return;
        }
        
        const metrics = {
            memory: process.memoryUsage().catch(error => console.error(`[project-protection-manager.js] process.memoryUsage failed:`, error)),
            cpu: process.cpuUsage(),
            disk: this.getDiskUsage().catch(error => console.error(`[project-protection-manager.js] this.getDiskUsage failed:`, error))
        };
        
        // 检查内存使用
        const memoryUsage = metrics.memory.heapUsed / metrics.memory.heapTotal;
        if (memoryUsage > this.config.performance.memoryThreshold) {
            this.log('warning', `内存使用率过高: ${(memoryUsage * 100).toFixed(2)}%`);
        }
        
        // 检查磁盘使用
        if (metrics.disk.used > this.config.performance.diskThreshold) {
            this.log('warning', `磁盘使用率过高: ${(metrics.disk.used * 100).toFixed(2)}%`);
        }
        
        return metrics;
    }

    // 获取磁盘使用情况
    getDiskUsage() {
        try {
            const stats = fs.statSync(this.rootDir);
            const total = 100 * 1024 * 1024 * 1024; // 假设100GB
            const used = stats.size / total;
            return { total, used: Math.min(used, 1) };
        } catch (error) {
            return { total: 0, used: 0 };
        }
    }

    // 获取项目版本
    getProjectVersion() {
        try {
            const versionFile = path.join(this.rootDir, 'VERSION');
            if (fs.existsSync(versionFile)) {
                return fs.readFileSync(versionFile, 'utf8').trim();
            }
        } catch (error) {
            // 忽略错误
        }
        return '2.0.0';
    }

    // 获取系统状态
    getStatus() {
        return {
            uptime: process.uptime().catch(error => console.error(`[project-protection-manager.js] process.uptime failed:`, error)),
            lastBackup: this.state.lastBackup,
            metrics: { ...this.state.metrics },
            fileCount: this.state.fileHashes.size,
            suspiciousFiles: Array.from(this.state.suspiciousFiles),
            protectedFiles: Array.from(this.state.protectedFiles),
            config: this.config
        };
    }

    // 启动保护系统
    start() {
        this.log('info', '启动MTSCOS项目保护系统...');
        
        // 文件完整性检查
        if (this.config.fileMonitor.enabled) {
            setInterval(() => {
                this.checkFileIntegrity().catch(error => console.error(`[project-protection-manager.js] this.checkFileIntegrity failed:`, error));
            }, this.config.fileMonitor.interval);
        }
        
        // 自动备份
        if (this.config.backup.enabled) {
            setInterval(() => {
                this.performBackup().catch(error => console.error(`[project-protection-manager.js] this.performBackup failed:`, error));
            }, this.config.backup.interval);
        }
        
        // 安全扫描
        if (this.config.security.enabled) {
            setInterval(() => {
                this.performSecurityScan().catch(error => console.error(`[project-protection-manager.js] this.performSecurityScan failed:`, error));
            }, this.config.security.scanInterval);
        }
        
        // 性能监控
        if (this.config.performance.enabled) {
            setInterval(() => {
                this.checkPerformance().catch(error => console.error(`[project-protection-manager.js] this.checkPerformance failed:`, error));
            }, 60000); // 每分钟检查一次
        }
        
        // 立即执行一次完整检查
        this.checkFileIntegrity().catch(error => console.error(`[project-protection-manager.js] this.checkFileIntegrity failed:`, error));
        this.performSecurityScan();
        this.checkPerformance().catch(error => console.error(`[project-protection-manager.js] this.checkPerformance failed:`, error));
        
        this.log('info', 'MTSCOS项目保护系统已启动');
    }

    // 停止保护系统
    stop() {
        this.log('info', '停止MTSCOS项目保护系统...');
        // 这里可以添加清理逻辑
    }
}

// 创建并启动保护系统
const protectionManager = new ProjectProtectionManager();

// 导出模块
module.exports = ProjectProtectionManager;

// 如果直接运行此脚本，启动保护系统
if (require.main === module) {
    protectionManager.start().catch(error => console.error(`[project-protection-manager.js] protectionManager.start failed:`, error));
    
    // 优雅关闭
    process.on('SIGINT', () => {
        protectionManager.stop().catch(error => console.error(`[project-protection-manager.js] protectionManager.stop failed:`, error));
        process.exit(0);
    });
    
    process.on('SIGTERM', () => {
        protectionManager.stop().catch(error => console.error(`[project-protection-manager.js] protectionManager.stop failed:`, error));
        process.exit(0);
    });
}

console.log('[MTSCOS] 项目保护系统已加载');