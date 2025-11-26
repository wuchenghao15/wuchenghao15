// MTSCOS 增强版备份管理器
// 作者: Chenghao Wu
// 版本: 2.0.0
// 功能: 智能备份、增量备份、压缩存储、恢复管理

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const zlib = require('zlib');
const { promisify } = require('util');
const { exec } = require('child_process');

const gzip = promisify(zlib.gzip);
const gunzip = promisify(zlib.gunzip);

class EnhancedBackupManager {
    constructor() {
        this.rootDir = path.dirname(path.dirname(__filename));
        this.backupDir = path.join(this.rootDir, 'Backups');
        this.config = {
            // 基础配置
            maxBackups: 15,
            compressionEnabled: true,
            incrementalEnabled: true,
            
            // 备份策略
            strategies: {
                full: {
                    interval: 24 * 60 * 60 * 1000, // 24小时
                    keepCount: 7 // 保留7个完整备份
                },
                incremental: {
                    interval: 30 * 60 * 1000, // 30分钟
                    keepCount: 48 // 保留48个增量备份
                },
                differential: {
                    interval: 4 * 60 * 60 * 1000, // 4小时
                    keepCount: 6 // 保留6个差异备份
                }
            },
            
            // 排除配置
            exclude: {
                directories: [
                    'Backups', '.git', 'node_modules', '.snapshots',
                    'dist', 'build', '.next', '.nuxt', 'coverage'
                ],
                files: [
                    '.DS_Store', '*.tmp', '*.log', '*.cache',
                    'Thumbs.db', '*.swp', '*.swo'
                ],
                extensions: [
                    '.lock', '.pid', '.tmp'
                ]
            },
            
            // 压缩配置
            compression: {
                level: 6, // 1-9
                threshold: 1024 // 大于1KB的文件才压缩
            },
            
            // 验证配置
            verification: {
                enabled: true,
                checksumAlgorithm: 'sha256',
                verifyAfterBackup: true
            }
        };

        this.state = {
            lastFullBackup: null,
            lastIncrementalBackup: null,
            lastDifferentialBackup: null,
            backupChain: [],
            currentBase: null,
            metrics: {
                totalBackups: 0,
                fullBackups: 0,
                incrementalBackups: 0,
                differentialBackups: 0,
                totalSize: 0,
                compressedSize: 0,
                errors: 0
            }
        };

        this.ensureDirectories().catch(error => console.error(`[enhanced-backup-manager.js] this.ensureDirectories failed:`, error));
        this.loadBackupChain();
    }

    // 确保目录存在
    ensureDirectories() {
        const dirs = [
            this.backupDir,
            path.join(this.backupDir, 'full'),
            path.join(this.backupDir, 'incremental'),
            path.join(this.backupDir, 'differential'),
            path.join(this.backupDir, 'metadata')
        ];

        dirs.forEach(dir => {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
        });
    }

    // 日志记录
    log(level, message, data = null) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logMessage = `[${timestamp}] [BACKUP-${level.toUpperCase().catch(error => console.error(`[enhanced-backup-manager.js] level.toUpperCase failed:`, error))}] ${message}`;
        console.log(logMessage);
        
        const logFile = path.join(this.rootDir, 'Logs', 'backup_manager.log');
        if (!fs.existsSync(path.dirname(logFile))) {
            fs.mkdirSync(path.dirname(logFile), { recursive: true });
        }
        fs.appendFileSync(logFile, logMessage + '\n');
        
        if (data) {
            fs.appendFileSync(logFile, `  Data: ${JSON.stringify(data, null, 2)}\n`);
        }
    }

    // 加载备份链
    loadBackupChain() {
        const chainFile = path.join(this.backupDir, 'metadata', 'backup_chain.json');
        
        if (fs.existsSync(chainFile)) {
            try {
                const chainData = fs.readFileSync(chainFile, 'utf8');
                this.state.backupChain = JSON.parse(chainData);
                this.updateCurrentBase().catch(error => console.error(`[enhanced-backup-manager.js] this.updateCurrentBase failed:`, error));
                this.log('info', `已加载备份链，包含 ${this.state.backupChain.length} 个备份`);
            } catch (error) {
                this.log('error', '加载备份链失败', error.message);
            }
        }
    }

    // 保存备份链
    saveBackupChain() {
        const chainFile = path.join(this.backupDir, 'metadata', 'backup_chain.json');
        
        try {
            fs.writeFileSync(chainFile, JSON.stringify(this.state.backupChain, null, 2));
        } catch (error) {
            this.log('error', '保存备份链失败', error.message);
        }
    }

    // 更新当前基础备份
    updateCurrentBase() {
        const fullBackups = this.state.backupChain
            .filter(backup => backup.type === 'full')
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        this.state.currentBase = fullBackups[0] || null;
        
        if (this.state.currentBase) {
            this.state.lastFullBackup = new Date(this.state.currentBase.timestamp);
        }
    }

    // 获取文件哈希
    async calculateFileHash(filePath) {
        try {
            const content = fs.readFileSync(filePath);
            return crypto.createHash(this.config.verification.checksumAlgorithm)
                .update(content).digest('hex');
        } catch (error) {
            return null;
        }
    }

    // 扫描项目文件
    async scanProjectFiles() {
        const fileMap = new Map();
        
        const scanDir = (dir, relativePath = '') => {
            try {
                const items = fs.readdirSync(dir);
                
                for (const item of items) {
                    const fullPath = path.join(dir, item);
                    const itemRelativePath = path.join(relativePath, item);
                    
                    // 检查排除规则
                    if (this.shouldExclude(itemRelativePath, fullPath)) {
                        continue;
                    }
                    
                    const stat = fs.statSync(fullPath);
                    
                    if (stat.isDirectory().catch(error => console.error(`[enhanced-backup-manager.js] stat.isDirectory failed:`, error))) {
                        scanDir(fullPath, itemRelativePath);
                    } else if (stat.isFile().catch(error => console.error(`[enhanced-backup-manager.js] stat.isFile failed:`, error))) {
                        fileMap.set(itemRelativePath, {
                            path: fullPath,
                            size: stat.size,
                            modified: stat.mtime,
                            hash: null
                        });
                    }
                }
            } catch (error) {
                this.log('error', `扫描目录失败: ${dir}`, error.message);
            }
        };
        
        scanDir(this.rootDir);
        
        // 计算文件哈希
        for (const [relativePath, fileInfo] of fileMap) {
            fileInfo.hash = await this.calculateFileHash(fileInfo.path);
        }
        
        return fileMap;
    }

    // 检查是否应该排除
    shouldExclude(relativePath, fullPath) {
        // 检查目录排除
        for (const excludeDir of this.config.exclude.directories) {
            if (relativePath.includes(excludeDir)) {
                return true;
            }
        }
        
        // 检查文件排除
        const fileName = path.basename(relativePath);
        for (const excludeFile of this.config.exclude.files) {
            const pattern = excludeFile.replace('*', '.*');
            if (fileName.match(new RegExp(pattern, 'i'))) {
                return true;
            }
        }
        
        // 检查扩展名排除
        const ext = path.extname(relativePath);
        if (this.config.exclude.extensions.includes(ext)) {
            return true;
        }
        
        return false;
    }

    // 执行完整备份
    async performFullBackup() {
        this.log('info', '开始完整备份...');
        
        const timestamp = new Date().toISOString();
        const backupId = `full_${timestamp.replace(/[:.]/g, '-')}`;
        const backupPath = path.join(this.backupDir, 'full', backupId);
        
        try {
            // 创建备份目录
            fs.mkdirSync(backupPath, { recursive: true });
            
            // 扫描文件
            const fileMap = await this.scanProjectFiles();
            
            // 复制文件
            let totalSize = 0;
            let compressedSize = 0;
            const backedUpFiles = [];
            
            for (const [relativePath, fileInfo] of fileMap) {
                const destPath = path.join(backupPath, relativePath);
                const destDir = path.dirname(destPath);
                
                if (!fs.existsSync(destDir)) {
                    fs.mkdirSync(destDir, { recursive: true });
                }
                
                let finalContent = fs.readFileSync(fileInfo.path);
                totalSize += finalContent.length;
                
                // 压缩文件
                if (this.config.compressionEnabled && 
                    finalContent.length > this.config.compression.threshold) {
                    try {
                        finalContent = await gzip(finalContent, { 
                            level: this.config.compression.level 
                        });
                        compressedSize += finalContent.length;
                        
                        // 保存为压缩文件
                        fs.writeFileSync(destPath + '.gz', finalContent);
                        
                        backedUpFiles.push({
                            path: relativePath,
                            hash: fileInfo.hash,
                            compressed: true,
                            originalSize: fileInfo.size,
                            compressedSize: finalContent.length
                        });
                    } catch (error) {
                        // 压缩失败，保存原文件
                        fs.writeFileSync(destPath, finalContent);
                        compressedSize += finalContent.length;
                        
                        backedUpFiles.push({
                            path: relativePath,
                            hash: fileInfo.hash,
                            compressed: false,
                            originalSize: fileInfo.size,
                            compressedSize: finalContent.length
                        });
                    }
                } else {
                    // 不压缩，直接保存
                    fs.writeFileSync(destPath, finalContent);
                    compressedSize += finalContent.length;
                    
                    backedUpFiles.push({
                        path: relativePath,
                        hash: fileInfo.hash,
                        compressed: false,
                        originalSize: fileInfo.size,
                        compressedSize: finalContent.length
                    });
                }
            }
            
            // 创建备份元数据
            const metadata = {
                id: backupId,
                type: 'full',
                timestamp,
                baseBackup: null,
                files: backedUpFiles,
                stats: {
                    fileCount: backedUpFiles.length,
                    originalSize: totalSize,
                    compressedSize,
                    compressionRatio: totalSize > 0 ? (compressedSize / totalSize) : 1
                }
            };
            
            fs.writeFileSync(
                path.join(backupPath, 'metadata.json'),
                JSON.stringify(metadata, null, 2)
            );
            
            // 更新备份链
            this.state.backupChain.push(metadata);
            this.state.lastFullBackup = new Date(timestamp);
            this.state.metrics.fullBackups++;
            this.state.metrics.totalBackups++;
            this.state.metrics.totalSize += totalSize;
            this.state.metrics.compressedSize += compressedSize;
            
            this.saveBackupChain().catch(error => console.error(`[enhanced-backup-manager.js] this.saveBackupChain failed:`, error));
            this.cleanupOldBackups();
            
            this.log('info', `完整备份完成: ${backupId}`, {
                fileCount: backedUpFiles.length,
                originalSize: this.formatBytes(totalSize),
                compressedSize: this.formatBytes(compressedSize),
                compressionRatio: `${((1 - compressedSize / totalSize) * 100).toFixed(2)}%`
            });
            
            return metadata;
            
        } catch (error) {
            this.state.metrics.errors++;
            this.log('error', '完整备份失败', error.message);
            throw error;
        }
    }

    // 执行增量备份
    async performIncrementalBackup() {
        if (!this.state.currentBase) {
            this.log('warning', '没有基础备份，执行完整备份');
            return await this.performFullBackup();
        }
        
        this.log('info', '开始增量备份...');
        
        const timestamp = new Date().toISOString();
        const backupId = `incremental_${timestamp.replace(/[:.]/g, '-')}`;
        const backupPath = path.join(this.backupDir, 'incremental', backupId);
        
        try {
            fs.mkdirSync(backupPath, { recursive: true });
            
            // 扫描当前文件
            const currentFileMap = await this.scanProjectFiles();
            
            // 获取基础备份的文件信息
            const baseBackup = this.state.currentBase;
            const baseFiles = new Map(
                baseBackup.files.map(file => [file.path, file])
            );
            
            // 找出变更的文件
            const changedFiles = [];
            let totalSize = 0;
            let compressedSize = 0;
            
            for (const [relativePath, fileInfo] of currentFileMap) {
                const baseFile = baseFiles.get(relativePath);
                
                // 新文件或哈希不同的文件
                if (!baseFile || baseFile.hash !== fileInfo.hash) {
                    const destPath = path.join(backupPath, relativePath);
                    const destDir = path.dirname(destPath);
                    
                    if (!fs.existsSync(destDir)) {
                        fs.mkdirSync(destDir, { recursive: true });
                    }
                    
                    let finalContent = fs.readFileSync(fileInfo.path);
                    totalSize += finalContent.length;
                    
                    // 压缩文件
                    if (this.config.compressionEnabled && 
                        finalContent.length > this.config.compression.threshold) {
                        try {
                            finalContent = await gzip(finalContent, { 
                                level: this.config.compression.level 
                            });
                            compressedSize += finalContent.length;
                            fs.writeFileSync(destPath + '.gz', finalContent);
                            
                            changedFiles.push({
                                path: relativePath,
                                hash: fileInfo.hash,
                                compressed: true,
                                originalSize: fileInfo.size,
                                compressedSize: finalContent.length,
                                changeType: baseFile ? 'modified' : 'added'
                            });
                        } catch (error) {
                            fs.writeFileSync(destPath, finalContent);
                            compressedSize += finalContent.length;
                            
                            changedFiles.push({
                                path: relativePath,
                                hash: fileInfo.hash,
                                compressed: false,
                                originalSize: fileInfo.size,
                                compressedSize: finalContent.length,
                                changeType: baseFile ? 'modified' : 'added'
                            });
                        }
                    } else {
                        fs.writeFileSync(destPath, finalContent);
                        compressedSize += finalContent.length;
                        
                        changedFiles.push({
                            path: relativePath,
                            hash: fileInfo.hash,
                            compressed: false,
                            originalSize: fileInfo.size,
                            compressedSize: finalContent.length,
                            changeType: baseFile ? 'modified' : 'added'
                        });
                    }
                }
            }
            
            // 检查删除的文件
            const deletedFiles = [];
            for (const [relativePath] of baseFiles) {
                if (!currentFileMap.has(relativePath)) {
                    deletedFiles.push({
                        path: relativePath,
                        changeType: 'deleted'
                    });
                }
            }
            
            // 创建备份元数据
            const metadata = {
                id: backupId,
                type: 'incremental',
                timestamp,
                baseBackup: baseBackup.id,
                files: changedFiles,
                deletedFiles,
                stats: {
                    fileCount: changedFiles.length,
                    deletedCount: deletedFiles.length,
                    originalSize: totalSize,
                    compressedSize,
                    compressionRatio: totalSize > 0 ? (compressedSize / totalSize) : 1
                }
            };
            
            fs.writeFileSync(
                path.join(backupPath, 'metadata.json'),
                JSON.stringify(metadata, null, 2)
            );
            
            // 更新备份链
            this.state.backupChain.push(metadata);
            this.state.lastIncrementalBackup = new Date(timestamp);
            this.state.metrics.incrementalBackups++;
            this.state.metrics.totalBackups++;
            this.state.metrics.totalSize += totalSize;
            this.state.metrics.compressedSize += compressedSize;
            
            this.saveBackupChain().catch(error => console.error(`[enhanced-backup-manager.js] this.saveBackupChain failed:`, error));
            this.cleanupOldBackups();
            
            this.log('info', `增量备份完成: ${backupId}`, {
                changedFiles: changedFiles.length,
                deletedFiles: deletedFiles.length,
                originalSize: this.formatBytes(totalSize),
                compressedSize: this.formatBytes(compressedSize)
            });
            
            return metadata;
            
        } catch (error) {
            this.state.metrics.errors++;
            this.log('error', '增量备份失败', error.message);
            throw error;
        }
    }

    // 清理旧备份
    cleanupOldBackups() {
        const backupTypes = ['full', 'incremental', 'differential'];
        
        backupTypes.forEach(type => {
            const backups = this.state.backupChain
                .filter(backup => backup.type === type)
                .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            
            const keepCount = this.config.strategies[type].keepCount;
            
            if (backups.length > keepCount) {
                const toDelete = backups.slice(keepCount);
                
                toDelete.forEach(backup => {
                    try {
                        const backupPath = path.join(this.backupDir, type, backup.id);
                        this.deleteDirectory(backupPath);
                        
                        // 从备份链中移除
                        const index = this.state.backupChain.findIndex(b => b.id === backup.id);
                        if (index !== -1) {
                            this.state.backupChain.splice(index, 1);
                        }
                        
                        this.log('info', `已删除旧${type}备份: ${backup.id}`);
                    } catch (error) {
                        this.log('error', `删除备份失败: ${backup.id}`, error.message);
                    }
                });
            }
        });
        
        this.saveBackupChain().catch(error => console.error(`[enhanced-backup-manager.js] this.saveBackupChain failed:`, error));
    }

    // 递归删除目录
    deleteDirectory(dirPath) {
        if (fs.existsSync(dirPath)) {
            fs.rmSync(dirPath, { recursive: true, force: true });
        }
    }

    // 格式化字节数
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 获取备份状态
    getBackupStatus() {
        return {
            ...this.state,
            config: this.config,
            nextFullBackup: this.getNextBackupTime('full'),
            nextIncrementalBackup: this.getNextBackupTime('incremental'),
            nextDifferentialBackup: this.getNextBackupTime('differential')
        };
    }

    // 获取下次备份时间
    getNextBackupTime(type) {
        const strategy = this.config.strategies[type];
        const lastBackup = this.state[`last${type.charAt(0).toUpperCase() + type.slice(1)}Backup`];
        
        if (!lastBackup) {
            return new Date();
        }
        
        return new Date(lastBackup.getTime() + strategy.interval);
    }

    // 启动备份管理器
    start() {
        this.log('info', '启动增强版备份管理器...');
        
        // 定期完整备份
        setInterval(async () => {
            try {
                await this.performFullBackup();
            } catch (error) {
                this.log('error', '定期完整备份失败', error.message);
            }
        }, this.config.strategies.full.interval);
        
        // 定期增量备份
        setInterval(async () => {
            try {
                await this.performIncrementalBackup();
            } catch (error) {
                this.log('error', '定期增量备份失败', error.message);
            }
        }, this.config.strategies.incremental.interval);
        
        // 立即执行一次备份
        if (!this.state.currentBase) {
            this.performFullBackup().catch(error => console.error(`[enhanced-backup-manager.js] this.performFullBackup failed:`, error));
        } else {
            this.performIncrementalBackup().catch(error => console.error(`[enhanced-backup-manager.js] this.performIncrementalBackup failed:`, error));
        }
        
        this.log('info', '增强版备份管理器已启动');
    }

    // 停止备份管理器
    stop() {
        this.log('info', '停止增强版备份管理器...');
    }
}

// 创建并导出备份管理器
const backupManager = new EnhancedBackupManager();

module.exports = EnhancedBackupManager;

// 如果直接运行此脚本，启动备份管理器
if (require.main === module) {
    backupManager.start().catch(error => console.error(`[enhanced-backup-manager.js] backupManager.start failed:`, error));
    
    process.on('SIGINT', () => {
        backupManager.stop().catch(error => console.error(`[enhanced-backup-manager.js] backupManager.stop failed:`, error));
        process.exit(0);
    });
}

console.log('[MTSCOS] 增强版备份管理器已加载');