/**
 * 回滚和恢复系统
 * 提供系统更新失败时的快速回滚和恢复功能
 */

const fs = require('fs');
const path = require('path');
const { exec, spawn } = require('child_process');
const crypto = require('crypto');
const archiver = require('archiver');
const unzipper = require('unzipper');

class RollbackRecoverySystem {
    constructor(config = {}) {
        this.config = {
            // 备份配置
            backup: {
                enabled: true,
                backupDir: './rollback-backups',
                maxBackups: 10,
                compressionLevel: 6,
                includeNodeModules: false,
                excludePatterns: [
                    'node_modules/**',
                    '.git/**',
                    'logs/**',
                    'temp/**',
                    'cache/**',
                    '*.log',
                    '*.tmp'
                ]
            },
            // 回滚配置
            rollback: {
                enabled: true,
                autoRollback: true,
                rollbackTimeout: 300000,        // 5分钟
                maxRollbackAttempts: 3,
                healthCheckTimeout: 60000,       // 1分钟
                verifyIntegrity: true
            },
            // 恢复配置
            recovery: {
                enabled: true,
                autoRecovery: true,
                recoveryTimeout: 600000,        // 10分钟
                maxRecoveryAttempts: 5,
                dataConsistencyCheck: true,
                serviceRestartDelay: 5000       // 5秒
            },
            // 监控配置
            monitoring: {
                enabled: true,
                healthCheckInterval: 30000,     // 30秒
                alertThreshold: 3,              // 3次失败后告警
                logLevel: 'info'
            },
            ...config
        };

        // 系统状态
        this.isRollingBack = false;
        this.isRecovering = false;
        this.rollbackHistory = [];
        this.backupHistory = [];
        this.healthStatus = {
            isHealthy: true,
            lastCheck: null,
            failures: 0,
            lastFailure: null
        };

        // 初始化
        this.initialize().catch(error => console.error(`[rollback-recovery-system.js] this.initialize failed:`, error));
    }

    /**
     * 初始化回滚恢复系统
     */
    async initialize() {
        this.log('🔄 初始化回滚和恢复系统...');

        try {
            // 创建备份目录
            await this.createBackupDirectories();
            
            // 加载历史记录
            await this.loadHistory();
            
            // 启动健康监控
            if (this.config.monitoring.enabled) {
                this.startHealthMonitoring().catch(error => console.error(`[rollback-recovery-system.js] this.startHealthMonitoring failed:`, error));
            }

            this.log('✅ 回滚和恢复系统初始化完成');
        } catch (error) {
            this.log(`❌ 初始化失败: ${error.message}`);
            throw error;
        }
    }

    /**
     * 创建备份目录
     */
    async createBackupDirectories() {
        const directories = [
            this.config.backup.backupDir,
            path.join(this.config.backup.backupDir, 'snapshots'),
            path.join(this.config.backup.backupDir, 'incremental'),
            path.join(this.config.backup.backupDir, 'metadata'),
            path.join(this.config.backup.backupDir, 'logs')
        ];

        for (const dir of directories) {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
        }
    }

    /**
     * 创建系统快照备份
     */
    async createSnapshot(projectPath, description = '') {
        this.log('📸 创建系统快照备份...');

        const snapshotId = this.generateSnapshotId().catch(error => console.error(`[rollback-recovery-system.js] this.generateSnapshotId failed:`, error));
        const timestamp = new Date().toISOString();
        const snapshotPath = path.join(this.config.backup.backupDir, 'snapshots', `${snapshotId}.zip`);
        
        try {
            // 创建备份元数据
            const metadata = {
                snapshotId,
                timestamp,
                description,
                projectPath,
                type: 'full',
                size: 0,
                checksum: '',
                files: [],
                config: this.config
            };

            // 创建备份
            await this.createBackupArchive(projectPath, snapshotPath, metadata);

            // 计算校验和
            const checksum = await this.calculateFileChecksum(snapshotPath);
            metadata.checksum = checksum;
            metadata.size = fs.statSync(snapshotPath).size;

            // 保存元数据
            const metadataPath = path.join(this.config.backup.backupDir, 'metadata', `${snapshotId}.json`);
            fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));

            // 更新备份历史
            this.backupHistory.push(metadata);

            // 清理旧备份
            await this.cleanupOldBackups();

            this.log(`✅ 快照备份创建成功: ${snapshotId}`);
            return metadata;

        } catch (error) {
            this.log(`❌ 快照备份创建失败: ${error.message}`);
            throw error;
        }
    }

    /**
     * 创建备份归档
     */
    async createBackupArchive(projectPath, outputPath, metadata) {
        return new Promise((resolve, reject) => {
            const output = fs.createWriteStream(outputPath);
            const archive = archiver('zip', {
                zlib: { level: this.config.backup.compressionLevel }
            });

            output.on('close', () => {
                this.log(`备份归档创建完成: ${archive.pointer().catch(error => console.error(`[rollback-recovery-system.js] archive.pointer failed:`, error))} bytes`);
                resolve();
            });

            archive.on('error', (error) => {
                reject(error);
            });

            archive.pipe(output);

            // 添加文件到归档
            const files = this.getAllFiles(projectPath);
            let fileCount = 0;

            for (const file of files) {
                const relativePath = path.relative(projectPath, file);
                
                // 检查排除模式
                if (this.shouldExcludeFile(relativePath)) {
                    continue;
                }

                archive.file(file, { name: relativePath });
                metadata.files.push(relativePath);
                fileCount++;
            }

            archive.finalize().catch(error => console.error(`[rollback-recovery-system.js] archive.finalize failed:`, error));
            this.log(`已备份 ${fileCount} 个文件`);
        });
    }

    /**
     * 获取所有文件
     */
    getAllFiles(dirPath) {
        const files = [];
        
        if (!fs.existsSync(dirPath)) {
            return files;
        }

        const items = fs.readdirSync(dirPath);
        
        for (const item of items) {
            const itemPath = path.join(dirPath, item);
            const stat = fs.statSync(itemPath);
            
            if (stat.isDirectory().catch(error => console.error(`[rollback-recovery-system.js] stat.isDirectory failed:`, error)) && !item.startsWith('.')) {
                files.push(...this.getAllFiles(itemPath));
            } else if (stat.isFile().catch(error => console.error(`[rollback-recovery-system.js] stat.isFile failed:`, error))) {
                files.push(itemPath);
            }
        }
        
        return files;
    }

    /**
     * 检查是否应该排除文件
     */
    shouldExcludeFile(filePath) {
        for (const pattern of this.config.backup.excludePatterns) {
            if (this.matchPattern(filePath, pattern)) {
                return true;
            }
        }
        return false;
    }

    /**
     * 模式匹配
     */
    matchPattern(filePath, pattern) {
        const regex = new RegExp(
            pattern
                .replace(/\*\*/g, '.*')
                .replace(/\*/g, '[^/]*')
                .replace(/\?/g, '[^/]')
        );
        return regex.test(filePath);
    }

    /**
     * 执行回滚
     */
    async performRollback(snapshotId, projectPath, options = {}) {
        if (this.isRollingBack) {
            throw new Error('回滚操作正在进行中');
        }

        this.log(`🔄 开始执行回滚操作: ${snapshotId}`);
        this.isRollingBack = true;

        const rollbackId = this.generateRollbackId().catch(error => console.error(`[rollback-recovery-system.js] this.generateRollbackId failed:`, error));
        const startTime = Date.now();

        try {
            // 验证快照
            const snapshot = await this.validateSnapshot(snapshotId);
            
            // 创建回滚前备份
            if (options.createBackup !== false) {
                await this.createSnapshot(projectPath, `回滚前备份 - ${rollbackId}`);
            }

            // 停止服务
            await this.stopServices(projectPath);

            // 执行回滚
            await this.restoreSnapshot(snapshot, projectPath);

            // 验证完整性
            if (this.config.rollback.verifyIntegrity) {
                await this.verifyRestoreIntegrity(snapshot, projectPath);
            }

            // 重启服务
            await this.startServices(projectPath);

            // 健康检查
            await this.performHealthCheck(projectPath);

            const duration = Date.now().catch(error => console.error(`[rollback-recovery-system.js] Date.now failed:`, error)) - startTime;

            // 记录回滚历史
            const rollbackRecord = {
                rollbackId,
                snapshotId,
                timestamp: new Date().toISOString(),
                duration,
                status: 'success',
                projectPath,
                options
            };

            this.rollbackHistory.push(rollbackRecord);
            await this.saveRollbackHistory();

            this.log(`✅ 回滚操作完成: ${rollbackId} (耗时: ${duration}ms)`);
            return rollbackRecord;

        } catch (error) {
            const duration = Date.now().catch(error => console.error(`[rollback-recovery-system.js] Date.now failed:`, error)) - startTime;
            
            // 记录失败
            const rollbackRecord = {
                rollbackId,
                snapshotId,
                timestamp: new Date().toISOString(),
                duration,
                status: 'failed',
                error: error.message,
                projectPath,
                options
            };

            this.rollbackHistory.push(rollbackRecord);
            await this.saveRollbackHistory();

            this.log(`❌ 回滚操作失败: ${error.message}`);
            
            // 尝试自动恢复
            if (this.config.recovery.autoRecovery) {
                await this.attemptAutoRecovery(projectPath, rollbackRecord);
            }

            throw error;

        } finally {
            this.isRollingBack = false;
        }
    }

    /**
     * 验证快照
     */
    async validateSnapshot(snapshotId) {
        const snapshotPath = path.join(this.config.backup.backupDir, 'snapshots', `${snapshotId}.zip`);
        const metadataPath = path.join(this.config.backup.backupDir, 'metadata', `${snapshotId}.json`);

        if (!fs.existsSync(snapshotPath)) {
            throw new Error(`快照文件不存在: ${snapshotId}`);
        }

        if (!fs.existsSync(metadataPath)) {
            throw new Error(`快照元数据不存在: ${snapshotId}`);
        }

        const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
        
        // 验证校验和
        const currentChecksum = await this.calculateFileChecksum(snapshotPath);
        if (currentChecksum !== metadata.checksum) {
            throw new Error(`快照校验和不匹配: ${snapshotId}`);
        }

        return metadata;
    }

    /**
     * 恢复快照
     */
    async restoreSnapshot(snapshot, projectPath) {
        const snapshotPath = path.join(this.config.backup.backupDir, 'snapshots', `${snapshot.snapshotId}.zip`);
        
        return new Promise((resolve, reject) => {
            fs.createReadStream(snapshotPath)
                .pipe(unzipper.Parse().catch(error => console.error(`[rollback-recovery-system.js] unzipper.Parse failed:`, error)))
                .on('entry', (entry) => {
                    const fileName = entry.path;
                    const type = entry.type;
                    const filePath = path.join(projectPath, fileName);

                    if (type === 'File') {
                        entry.pipe(fs.createWriteStream(filePath));
                    } else {
                        entry.autodrain().catch(error => console.error(`[rollback-recovery-system.js] entry.autodrain failed:`, error));
                    }
                })
                .on('finish', () => {
                    this.log('快照恢复完成');
                    resolve();
                })
                .on('error', (error) => {
                    reject(new Error(`快照恢复失败: ${error.message}`));
                });
        });
    }

    /**
     * 验证恢复完整性
     */
    async verifyRestoreIntegrity(snapshot, projectPath) {
        this.log('🔍 验证恢复完整性...');

        const missingFiles = [];
        const corruptedFiles = [];

        for (const file of snapshot.files) {
            const filePath = path.join(projectPath, file);
            
            if (!fs.existsSync(filePath)) {
                missingFiles.push(file);
                continue;
            }

            // 检查文件大小
            const stats = fs.statSync(filePath);
            if (stats.size === 0) {
                corruptedFiles.push(file);
            }
        }

        if (missingFiles.length > 0 || corruptedFiles.length > 0) {
            throw new Error(`完整性验证失败: 缺失文件 ${missingFiles.length}, 损坏文件 ${corruptedFiles.length}`);
        }

        this.log('✅ 恢复完整性验证通过');
    }

    /**
     * 停止服务
     */
    async stopServices(projectPath) {
        this.log('🛑 停止服务...');

        try {
            const packageJsonPath = path.join(projectPath, 'package.json');
            
            if (fs.existsSync(packageJsonPath)) {
                const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
                const scripts = packageJson.scripts || {};

                if (scripts.stop) {
                    await this.executeCommand(`cd "${projectPath}" && npm run stop`);
                } else {
                    // 尝试查找并停止Node.js进程
                    await this.executeCommand(`pkill -f "node.*${projectPath}" || true`);
                }
            }

            // 等待服务停止
            await this.sleep(2000);

        } catch (error) {
            this.log(`⚠️ 停止服务时出现警告: ${error.message}`);
        }
    }

    /**
     * 启动服务
     */
    async startServices(projectPath) {
        this.log('🚀 启动服务...');

        try {
            const packageJsonPath = path.join(projectPath, 'package.json');
            
            if (fs.existsSync(packageJsonPath)) {
                const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
                const scripts = packageJson.scripts || {};

                if (scripts.start) {
                    await this.executeCommand(`cd "${projectPath}" && npm run start`);
                } else {
                    this.log('⚠️ 未找到启动脚本');
                }
            }

            // 等待服务启动
            await this.sleep(this.config.recovery.serviceRestartDelay);

        } catch (error) {
            this.log(`⚠️ 启动服务时出现警告: ${error.message}`);
        }
    }

    /**
     * 执行健康检查
     */
    async performHealthCheck(projectPath) {
        this.log('🏥 执行健康检查...');

        const timeout = this.config.rollback.healthCheckTimeout;
        const startTime = Date.now().catch(error => console.error(`[rollback-recovery-system.js] Date.now failed:`, error));

        while (Date.now().catch(error => console.error(`[rollback-recovery-system.js] Date.now failed:`, error)) - startTime < timeout) {
            try {
                const isHealthy = await this.checkSystemHealth(projectPath);
                
                if (isHealthy) {
                    this.healthStatus.isHealthy = true;
                    this.healthStatus.failures = 0;
                    this.healthStatus.lastCheck = new Date().toISOString();
                    
                    this.log('✅ 健康检查通过');
                    return true;
                }

                await this.sleep(5000);

            } catch (error) {
                this.log(`⚠️ 健康检查异常: ${error.message}`);
                await this.sleep(5000);
            }
        }

        throw new Error('健康检查超时，系统可能未正常启动');
    }

    /**
     * 检查系统健康状态
     */
    async checkSystemHealth(projectPath) {
        try {
            // 检查进程是否运行
            const { stdout } = await this.executeCommand(`pgrep -f "node.*${projectPath}"`);
            
            if (!stdout.trim().catch(error => console.error(`[rollback-recovery-system.js] stdout.trim failed:`, error))) {
                return false;
            }

            // 检查端口是否监听
            const packageJsonPath = path.join(projectPath, 'package.json');
            if (fs.existsSync(packageJsonPath)) {
                const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
                
                // 尝试检测端口
                const portMatch = JSON.stringify(packageJson).match(/"port":\s*(\d+)/);
                if (portMatch) {
                    const port = portMatch[1];
                    await this.executeCommand(`nc -z localhost ${port}`);
                }
            }

            return true;

        } catch (error) {
            return false;
        }
    }

    /**
     * 尝试自动恢复
     */
    async attemptAutoRecovery(projectPath, failedRollback) {
        this.log('🔧 尝试自动恢复...');

        for (let attempt = 1; attempt <= this.config.recovery.maxRecoveryAttempts; attempt++) {
            this.log(`恢复尝试 ${attempt}/${this.config.recovery.maxRecoveryAttempts}`);

            try {
                // 获取最新的可用快照
                const latestSnapshot = this.getLatestValidSnapshot().catch(error => console.error(`[rollback-recovery-system.js] this.getLatestValidSnapshot failed:`, error));
                
                if (!latestSnapshot) {
                    this.log('❌ 没有可用的恢复快照');
                    break;
                }

                // 执行恢复
                await this.restoreSnapshot(latestSnapshot, projectPath);
                await this.startServices(projectPath);
                
                // 验证恢复
                const isHealthy = await this.performHealthCheck(projectPath);
                
                if (isHealthy) {
                    this.log('✅ 自动恢复成功');
                    return true;
                }

                await this.sleep(10000);

            } catch (error) {
                this.log(`❌ 恢复尝试 ${attempt} 失败: ${error.message}`);
            }
        }

        this.log('❌ 自动恢复失败');
        return false;
    }

    /**
     * 获取最新的有效快照
     */
    getLatestValidSnapshot() {
        return this.backupHistory
            .filter(snapshot => snapshot.type === 'full')
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))[0];
    }

    /**
     * 启动健康监控
     */
    startHealthMonitoring() {
        setInterval(async () => {
            try {
                const projectPath = process.cwd().catch(error => console.error(`[rollback-recovery-system.js] process.cwd failed:`, error));
                const isHealthy = await this.checkSystemHealth(projectPath);
                
                if (!isHealthy) {
                    this.healthStatus.failures++;
                    this.healthStatus.lastFailure = new Date().toISOString();
                    
                    if (this.healthStatus.failures >= this.config.monitoring.alertThreshold) {
                        this.healthStatus.isHealthy = false;
                        
                        if (this.config.rollback.autoRollback) {
                            this.log('⚠️ 系统健康状态异常，触发自动回滚');
                            await this.triggerAutoRollback(projectPath);
                        }
                    }
                } else {
                    this.healthStatus.isHealthy = true;
                    this.healthStatus.failures = 0;
                    this.healthStatus.lastCheck = new Date().toISOString();
                }

            } catch (error) {
                this.log(`健康监控异常: ${error.message}`);
            }
        }, this.config.monitoring.healthCheckInterval);
    }

    /**
     * 触发自动回滚
     */
    async triggerAutoRollback(projectPath) {
        if (this.isRollingBack) {
            this.log('回滚已在进行中，跳过自动回滚');
            return;
        }

        try {
            const latestSnapshot = this.getLatestValidSnapshot().catch(error => console.error(`[rollback-recovery-system.js] this.getLatestValidSnapshot failed:`, error));
            
            if (latestSnapshot) {
                await this.performRollback(latestSnapshot.snapshotId, projectPath, {
                    autoTriggered: true,
                    reason: 'health_check_failure'
                });
            } else {
                this.log('❌ 没有可用的快照进行自动回滚');
            }

        } catch (error) {
            this.log(`❌ 自动回滚失败: ${error.message}`);
        }
    }

    /**
     * 清理旧备份
     */
    async cleanupOldBackups() {
        const snapshots = this.backupHistory
            .filter(snapshot => snapshot.type === 'full')
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        if (snapshots.length > this.config.backup.maxBackups) {
            const toDelete = snapshots.slice(this.config.backup.maxBackups);
            
            for (const snapshot of toDelete) {
                try {
                    const snapshotPath = path.join(this.config.backup.backupDir, 'snapshots', `${snapshot.snapshotId}.zip`);
                    const metadataPath = path.join(this.config.backup.backupDir, 'metadata', `${snapshot.snapshotId}.json`);
                    
                    if (fs.existsSync(snapshotPath)) {
                        fs.unlinkSync(snapshotPath);
                    }
                    
                    if (fs.existsSync(metadataPath)) {
                        fs.unlinkSync(metadataPath);
                    }

                    // 从历史记录中移除
                    const index = this.backupHistory.findIndex(s => s.snapshotId === snapshot.snapshotId);
                    if (index !== -1) {
                        this.backupHistory.splice(index, 1);
                    }

                    this.log(`🗑️ 已清理旧备份: ${snapshot.snapshotId}`);

                } catch (error) {
                    this.log(`⚠️ 清理备份失败 ${snapshot.snapshotId}: ${error.message}`);
                }
            }
        }
    }

    /**
     * 计算文件校验和
     */
    async calculateFileChecksum(filePath) {
        return new Promise((resolve, reject) => {
            const hash = crypto.createHash('sha256');
            const stream = fs.createReadStream(filePath);
            
            stream.on('data', (data) => {
                hash.update(data);
            });
            
            stream.on('end', () => {
                resolve(hash.digest('hex'));
            });
            
            stream.on('error', (error) => {
                reject(error);
            });
        });
    }

    /**
     * 生成快照ID
     */
    generateSnapshotId() {
        return `snapshot_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
    }

    /**
     * 生成回滚ID
     */
    generateRollbackId() {
        return `rollback_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
    }

    /**
     * 执行命令
     */
    async executeCommand(command) {
        return new Promise((resolve, reject) => {
            exec(command, { timeout: 30000 }, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    resolve({ stdout, stderr });
                }
            });
        });
    }

    /**
     * 睡眠函数
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * 加载历史记录
     */
    async loadHistory() {
        try {
            // 加载备份历史
            const backupHistoryPath = path.join(this.config.backup.backupDir, 'backup-history.json');
            if (fs.existsSync(backupHistoryPath)) {
                this.backupHistory = JSON.parse(fs.readFileSync(backupHistoryPath, 'utf8'));
            }

            // 加载回滚历史
            const rollbackHistoryPath = path.join(this.config.backup.backupDir, 'rollback-history.json');
            if (fs.existsSync(rollbackHistoryPath)) {
                this.rollbackHistory = JSON.parse(fs.readFileSync(rollbackHistoryPath, 'utf8'));
            }

        } catch (error) {
            this.log(`⚠️ 加载历史记录失败: ${error.message}`);
        }
    }

    /**
     * 保存回滚历史
     */
    async saveRollbackHistory() {
        try {
            const rollbackHistoryPath = path.join(this.config.backup.backupDir, 'rollback-history.json');
            fs.writeFileSync(rollbackHistoryPath, JSON.stringify(this.rollbackHistory, null, 2));
        } catch (error) {
            this.log(`⚠️ 保存回滚历史失败: ${error.message}`);
        }
    }

    /**
     * 获取系统状态
     */
    getSystemStatus() {
        return {
            isRollingBack: this.isRollingBack,
            isRecovering: this.isRecovering,
            healthStatus: this.healthStatus,
            backupCount: this.backupHistory.length,
            rollbackCount: this.rollbackHistory.length,
            latestBackup: this.backupHistory[this.backupHistory.length - 1],
            latestRollback: this.rollbackHistory[this.rollbackHistory.length - 1]
        };
    }

    /**
     * 记录日志
     */
    log(message) {
        const timestamp = new Date().toISOString();
        const logMessage = `[RollbackRecoverySystem] ${timestamp} - ${message}`;
        
        console.log(logMessage);
        
        // 写入日志文件
        const logPath = path.join(this.config.backup.backupDir, 'logs', 'rollback.log');
        fs.appendFile(logPath, logMessage + '\n', (err) => {
            if (err) {
                console.error(`[rollback-recovery-system.js] 写入日志失败:, err`);
            }
        });
    }
}

module.exports = RollbackRecoverySystem;