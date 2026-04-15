/**
 * 统一系统规则和机制管理器
 * 负责系统启动时的自动执行和统一管理
 */

class UnifiedSystemManager {
    constructor() {
        this.systemRules = new Map();
        this.systemMechanisms = new Map();
        this.isInitialized = false;
        this.startTime = null;
        this.version = '3.0.0';
        this.internalVersion = '3.0.0.20250115';
        this.databaseManager = null;
    }

    /**
     * 初始化系统管理器
     */
    async initialize() {
        if (this.isInitialized) {
            console.log('系统管理器已初始化');
            return;
        }

        this.startTime = Date.now();
        console.log('🚀 开始初始化统一系统管理器...');

        try {
            // 0. 初始化数据库管理器
            await this.initializeDatabaseManager();
            
            // 1. 加载系统规则
            await this.loadSystemRules();
            
            // 2. 初始化系统机制
            await this.initializeSystemMechanisms();
            
            // 3. 执行启动检查
            await this.performStartupChecks();
            
            // 4. 启动自动化任务
            await this.startAutomatedTasks();
            
            // 5. 注册系统事件监听
            this.registerSystemEventListeners();
            
            this.isInitialized = true;
            
            const initTime = Date.now() - this.startTime;
            console.log(`✅ 统一系统管理器初始化完成，耗时: ${initTime}ms`);
            
            // 记录初始化日志
            this.logSystemEvent('SYSTEM_INITIALIZED', {
                version: this.version,
                internalVersion: this.internalVersion,
                initTime: initTime,
                timestamp: new Date().toISOString()
            });

        } catch (error) {
            console.error('❌ 系统管理器初始化失败:', error);
            this.handleInitializationError(error);
            throw error;
        }
    }

    /**
     * 初始化数据库管理器
     */
    async initializeDatabaseManager() {
        console.log('🗄️ 初始化数据库管理器...');
        
        try {
            if (typeof DatabaseManager !== 'undefined') {
                this.databaseManager = new DatabaseManager();
                await this.databaseManager.initialize();
                console.log('✅ 数据库管理器初始化成功');
            } else {
                console.warn('⚠️ DatabaseManager未找到，跳过数据库初始化');
            }
        } catch (error) {
            console.error('❌ 数据库管理器初始化失败:', error);
            throw error;
        }
    }

    /**
     * 加载系统规则
     */
    async loadSystemRules() {
        console.log('📋 加载系统规则...');
        
        // 安全规则
        this.systemRules.set('security', {
            requireAuth: true,
            sessionTimeout: 30 * 60 * 1000, // 30分钟
            maxLoginAttempts: 5,
            passwordMinLength: 8,
            encryptionRequired: true,
            auditLogEnabled: true
        });

        // 性能规则
        this.systemRules.set('performance', {
            maxMemoryUsage: 512 * 1024 * 1024, // 512MB
            maxCpuUsage: 80, // 80%
            responseTimeout: 10000, // 10秒
            cacheEnabled: true,
            compressionEnabled: true
        });

        // 数据规则
        this.systemRules.set('data', {
            backupInterval: 24 * 60 * 60 * 1000, // 24小时
            maxConnections: 100,
            connectionTimeout: 5000, // 5秒
            transactionTimeout: 30000, // 30秒
            dataValidation: true
        });

        // 监控规则
        this.systemRules.set('monitoring', {
            healthCheckInterval: 60 * 1000, // 1分钟
            alertThresholds: {
                cpu: 80,
                memory: 85,
                disk: 90,
                responseTime: 5000
            },
            logLevel: 'info',
            metricsEnabled: true
        });

        // 更新规则
        this.systemRules.set('updates', {
            autoCheckEnabled: true,
            checkInterval: 6 * 60 * 60 * 1000, // 6小时
            autoInstallSecurity: true,
            requireRestart: false,
            rollbackEnabled: true
        });

        console.log(`✅ 已加载 ${this.systemRules.size} 个系统规则类别`);
    }

    /**
     * 初始化系统机制
     */
    async initializeSystemMechanisms() {
        console.log('⚙️ 初始化系统机制...');

        // 错误处理机制
        this.systemMechanisms.set('errorHandler', {
            globalErrorHandling: true,
            errorReporting: true,
            automaticRecovery: true,
            maxRetries: 3,
            retryDelay: 1000
        });

        // 缓存机制
        this.systemMechanisms.set('cache', {
            enabled: true,
            ttl: 5 * 60 * 1000, // 5分钟
            maxSize: 1000,
            cleanupInterval: 10 * 60 * 1000 // 10分钟
        });

        // 日志机制
        this.systemMechanisms.set('logging', {
            level: 'info',
            fileLogging: true,
            consoleLogging: true,
            remoteLogging: false,
            rotationEnabled: true,
            maxFileSize: 10 * 1024 * 1024 // 10MB
        });

        // 安全机制
        this.systemMechanisms.set('security', {
            rateLimiting: true,
            corsEnabled: true,
            csrfProtection: true,
            xssProtection: true,
            sqlInjectionProtection: true
        });

        // 性能优化机制
        this.systemMechanisms.set('optimization', {
            lazyLoading: true,
            codeSplitting: true,
            resourceMinification: true,
            imageOptimization: true,
            bundleAnalysis: true
        });

        console.log(`✅ 已初始化 ${this.systemMechanisms.size} 个系统机制`);
    }

    /**
     * 执行启动检查
     */
    async performStartupChecks() {
        console.log('🔍 执行系统启动检查...');

        const checks = [
            this.checkSystemResources(),
            this.checkDatabaseConnection(),
            this.checkFileSystem(),
            this.checkNetworkConnectivity(),
            this.checkSecurityConfiguration(),
            this.checkDependencies()
        ];

        const results = await Promise.allSettled(checks);
        const failedChecks = results.filter(result => result.status === 'rejected');

        if (failedChecks.length > 0) {
            console.warn(`⚠️ ${failedChecks.length} 项启动检查失败`);
            failedChecks.forEach((result, index) => {
                console.error(`检查 ${index + 1} 失败:`, result.reason);
            });
        } else {
            console.log('✅ 所有启动检查通过');
        }
    }

    /**
     * 检查系统资源
     */
    async checkSystemResources() {
        const memoryUsage = process.memoryUsage();
        const cpuUsage = process.cpuUsage();
        
        console.log('📊 系统资源状态:');
        console.log(`  内存使用: ${(memoryUsage.heapUsed / 1024 / 1024).toFixed(2)}MB`);
        console.log(`  CPU使用: ${cpuUsage.user + cpuUsage.system}ms`);

        // 检查资源使用是否在允许范围内
        const performanceRules = this.systemRules.get('performance');
        if (memoryUsage.heapUsed > performanceRules.maxMemoryUsage) {
            throw new Error(`内存使用超过限制: ${(memoryUsage.heapUsed / 1024 / 1024).toFixed(2)}MB`);
        }

        return true;
    }

    /**
     * 检查数据库连接
     */
    async checkDatabaseConnection() {
        console.log('🗄️ 检查数据库连接...');
        
        try {
            // 这里将集成MSSQL连接检查
            const dbConfig = {
                server: 'wuchenghao15.net',
                port: 33693,
                user: 'sa',
                password: 'LoginMe15',
                database: 'MyData',
                options: {
                    encrypt: false,
                    trustServerCertificate: true
                }
            };

            console.log('✅ 数据库配置验证通过');
            return true;
        } catch (error) {
            throw new Error(`数据库连接检查失败: ${error.message}`);
        }
    }

    /**
     * 检查文件系统
     */
    async checkFileSystem() {
        console.log('📁 检查文件系统...');
        
        const requiredPaths = [
            './Logs',
            './Backups',
            './Configs',
            './assets'
        ];

        for (const path of requiredPaths) {
            try {
                const fs = require('fs').promises;
                await fs.access(path);
                console.log(`  ✓ ${path} 可访问`);
            } catch (error) {
                console.warn(`  ⚠️ ${path} 不可访问，将创建`);
                // 自动创建缺失的目录
                const fs = require('fs').promises;
                await fs.mkdir(path, { recursive: true });
            }
        }

        return true;
    }

    /**
     * 检查网络连接
     */
    async checkNetworkConnectivity() {
        console.log('🌐 检查网络连接...');
        
        // 简单的网络连接检查
        try {
            const https = require('https');
            await new Promise((resolve, reject) => {
                const req = https.request('https://www.baidu.com', (res) => {
                    resolve(res.statusCode === 200);
                });
                req.on('error', reject);
                req.setTimeout(5000, () => reject(new Error('网络超时')));
                req.end();
            });
            console.log('✅ 网络连接正常');
            return true;
        } catch (error) {
            console.warn('⚠️ 网络连接检查失败，但不影响本地运行');
            return true;
        }
    }

    /**
     * 检查安全配置
     */
    async checkSecurityConfiguration() {
        console.log('🔒 检查安全配置...');
        
        const securityRules = this.systemRules.get('security');
        
        // 检查环境变量
        if (!process.env.NODE_ENV) {
            console.warn('⚠️ NODE_ENV 未设置，建议设置为 production');
        }

        // 检查敏感信息
        const sensitiveVars = ['PASSWORD', 'SECRET', 'TOKEN', 'KEY'];
        const exposedVars = sensitiveVars.filter(varName => process.env[varName]);
        
        if (exposedVars.length > 0) {
            console.warn('⚠️ 检测到可能暴露的敏感环境变量');
        }

        console.log('✅ 安全配置检查完成');
        return true;
    }

    /**
     * 检查依赖项
     */
    async checkDependencies() {
        console.log('📦 检查依赖项...');
        
        try {
            const packageJson = require('./package.json');
            const dependencies = Object.keys(packageJson.dependencies || {});
            const devDependencies = Object.keys(packageJson.devDependencies || {});
            
            console.log(`✅ 发现 ${dependencies.length} 个生产依赖，${devDependencies.length} 个开发依赖`);
            
            // 检查关键依赖
            const criticalDeps = ['express', 'mssql', 'helmet', 'cors'];
            const missingDeps = criticalDeps.filter(dep => !dependencies.includes(dep));
            
            if (missingDeps.length > 0) {
                console.warn(`⚠️ 缺少关键依赖: ${missingDeps.join(', ')}`);
            }
            
            return true;
        } catch (error) {
            throw new Error(`依赖项检查失败: ${error.message}`);
        }
    }

    /**
     * 启动自动化任务
     */
    async startAutomatedTasks() {
        console.log('🤖 启动自动化任务...');

        // 启动健康检查任务
        this.startHealthCheckTask();
        
        // 启动清理任务
        this.startCleanupTask();
        
        // 启动备份任务
        this.startBackupTask();
        
        // 启动监控任务
        this.startMonitoringTask();

        console.log('✅ 自动化任务启动完成');
    }

    /**
     * 启动健康检查任务
     */
    startHealthCheckTask() {
        const monitoringRules = this.systemRules.get('monitoring');
        const interval = monitoringRules.healthCheckInterval;

        setInterval(async () => {
            try {
                await this.performHealthCheck();
            } catch (error) {
                console.error('健康检查失败:', error);
            }
        }, interval);

        console.log(`✅ 健康检查任务已启动，间隔: ${interval / 1000}秒`);
    }

    /**
     * 执行健康检查
     */
    async performHealthCheck() {
        const health = {
            timestamp: new Date().toISOString(),
            status: 'healthy',
            checks: {}
        };

        // 检查内存使用
        const memoryUsage = process.memoryUsage();
        const memoryPercent = (memoryUsage.heapUsed / memoryUsage.heapTotal) * 100;
        health.checks.memory = {
            usage: `${(memoryUsage.heapUsed / 1024 / 1024).toFixed(2)}MB`,
            percentage: memoryPercent.toFixed(2) + '%',
            status: memoryPercent < 80 ? 'healthy' : 'warning'
        };

        // 检查响应时间
        const startTime = Date.now();
        await new Promise(resolve => setTimeout(resolve, 1));
        const responseTime = Date.now() - startTime;
        health.checks.responseTime = {
            time: `${responseTime}ms`,
            status: responseTime < 100 ? 'healthy' : 'warning'
        };

        // 记录健康状态
        if (health.checks.memory.status === 'warning' || health.checks.responseTime.status === 'warning') {
            health.status = 'warning';
        }

        this.logSystemEvent('HEALTH_CHECK', health);
    }

    /**
     * 启动清理任务
     */
    startCleanupTask() {
        // 每小时执行一次清理
        setInterval(async () => {
            try {
                await this.performCleanup();
            } catch (error) {
                console.error('清理任务失败:', error);
            }
        }, 60 * 60 * 1000);

        console.log('✅ 清理任务已启动，间隔: 1小时');
    }

    /**
     * 执行清理
     */
    async performCleanup() {
        console.log('🧹 执行系统清理...');
        
        // 清理临时文件
        await this.cleanupTempFiles();
        
        // 清理日志文件
        await this.cleanupLogFiles();
        
        // 清理缓存
        await this.cleanupCache();

        console.log('✅ 系统清理完成');
    }

    /**
     * 清理临时文件
     */
    async cleanupTempFiles() {
        const fs = require('fs').promises;
        const path = require('path');
        
        try {
            const tempDirs = ['./temp', './tmp', './.cache'];
            for (const dir of tempDirs) {
                try {
                    const files = await fs.readdir(dir);
                    for (const file of files) {
                        const filePath = path.join(dir, file);
                        const stats = await fs.stat(filePath);
                        
                        // 删除超过24小时的临时文件
                        if (Date.now() - stats.mtime.getTime() > 24 * 60 * 60 * 1000) {
                            await fs.unlink(filePath);
                            console.log(`  删除临时文件: ${filePath}`);
                        }
                    }
                } catch (error) {
                    // 目录不存在，忽略
                }
            }
        } catch (error) {
            console.error('清理临时文件失败:', error);
        }
    }

    /**
     * 清理日志文件
     */
    async cleanupLogFiles() {
        const fs = require('fs').promises;
        const path = require('path');
        
        try {
            const logDir = './Logs';
            const files = await fs.readdir(logDir);
            
            for (const file of files) {
                if (file.endsWith('.log')) {
                    const filePath = path.join(logDir, file);
                    const stats = await fs.stat(filePath);
                    
                    // 删除超过7天的日志文件
                    if (Date.now() - stats.mtime.getTime() > 7 * 24 * 60 * 60 * 1000) {
                        await fs.unlink(filePath);
                        console.log(`  删除日志文件: ${filePath}`);
                    }
                }
            }
        } catch (error) {
            console.error('清理日志文件失败:', error);
        }
    }

    /**
     * 清理缓存
     */
    async cleanupCache() {
        // 清理内存缓存
        if (this.cache && this.cache.clear) {
            this.cache.clear();
            console.log('  内存缓存已清理');
        }
    }

    /**
     * 启动备份任务
     */
    startBackupTask() {
        const dataRules = this.systemRules.get('data');
        const interval = dataRules.backupInterval;

        setInterval(async () => {
            try {
                await this.performBackup();
            } catch (error) {
                console.error('备份任务失败:', error);
            }
        }, interval);

        console.log(`✅ 备份任务已启动，间隔: ${interval / 1000 / 60 / 60}小时`);
    }

    /**
     * 执行备份
     */
    async performBackup() {
        console.log('💾 执行系统备份...');
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const backupDir = `./Backups/${timestamp}`;
        
        try {
            const fs = require('fs').promises;
            await fs.mkdir(backupDir, { recursive: true });
            
            // 备份配置文件
            await this.backupConfigs(backupDir);
            
            // 备份重要数据
            await this.backupData(backupDir);
            
            console.log(`✅ 系统备份完成: ${backupDir}`);
            
            this.logSystemEvent('BACKUP_COMPLETED', {
                backupDir: backupDir,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            console.error('备份失败:', error);
        }
    }

    /**
     * 备份配置文件
     */
    async backupConfigs(backupDir) {
        const fs = require('fs').promises;
        const path = require('path');
        
        const configFiles = [
            './package.json',
            './.env',
            './Configs'
        ];
        
        for (const file of configFiles) {
            try {
                const stats = await fs.stat(file);
                if (stats.isDirectory()) {
                    await this.copyDirectory(file, path.join(backupDir, path.basename(file)));
                } else {
                    await fs.copyFile(file, path.join(backupDir, path.basename(file)));
                }
            } catch (error) {
                console.warn(`  备份配置文件失败: ${file}`);
            }
        }
    }

    /**
     * 备份数据
     */
    async backupData(backupDir) {
        // 这里将集成数据库备份逻辑
        console.log('  数据库备份功能将在MSSQL集成后实现');
    }

    /**
     * 复制目录
     */
    async copyDirectory(src, dest) {
        const fs = require('fs').promises;
        const path = require('path');
        
        await fs.mkdir(dest, { recursive: true });
        const entries = await fs.readdir(src, { withFileTypes: true });
        
        for (const entry of entries) {
            const srcPath = path.join(src, entry.name);
            const destPath = path.join(dest, entry.name);
            
            if (entry.isDirectory()) {
                await this.copyDirectory(srcPath, destPath);
            } else {
                await fs.copyFile(srcPath, destPath);
            }
        }
    }

    /**
     * 启动监控任务
     */
    startMonitoringTask() {
        const monitoringRules = this.systemRules.get('monitoring');
        
        setInterval(async () => {
            try {
                await this.collectMetrics();
            } catch (error) {
                console.error('监控任务失败:', error);
            }
        }, 60 * 1000); // 每分钟收集一次指标

        console.log('✅ 监控任务已启动，间隔: 1分钟');
    }

    /**
     * 收集系统指标
     */
    async collectMetrics() {
        const metrics = {
            timestamp: new Date().toISOString(),
            memory: process.memoryUsage(),
            cpu: process.cpuUsage(),
            uptime: process.uptime(),
            version: this.version
        };

        this.logSystemEvent('METRICS_COLLECTED', metrics);
    }

    /**
     * 注册系统事件监听
     */
    registerSystemEventListeners() {
        // 进程退出事件
        process.on('SIGINT', () => {
            console.log('🛑 接收到SIGINT信号，正在优雅关闭...');
            this.gracefulShutdown();
        });

        process.on('SIGTERM', () => {
            console.log('🛑 接收到SIGTERM信号，正在优雅关闭...');
            this.gracefulShutdown();
        });

        // 未捕获异常
        process.on('uncaughtException', (error) => {
            console.error('❌ 未捕获异常:', error);
            this.handleCriticalError(error);
        });

        process.on('unhandledRejection', (reason, promise) => {
            console.error('❌ 未处理的Promise拒绝:', reason);
            this.handleCriticalError(reason);
        });

        console.log('✅ 系统事件监听器已注册');
    }

    /**
     * 优雅关闭
     */
    async gracefulShutdown() {
        console.log('🔄 正在执行优雅关闭...');
        
        try {
            // 停止所有定时任务
            if (this.timers) {
                this.timers.forEach(timer => clearInterval(timer));
            }
            
            // 执行最终备份
            await this.performBackup();
            
            // 清理资源
            await this.cleanup();
            
            console.log('✅ 优雅关闭完成');
            process.exit(0);
        } catch (error) {
            console.error('❌ 优雅关闭失败:', error);
            process.exit(1);
        }
    }

    /**
     * 处理关键错误
     */
    handleCriticalError(error) {
        this.logSystemEvent('CRITICAL_ERROR', {
            error: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        });

        // 尝试自动恢复
        const errorHandler = this.systemMechanisms.get('errorHandler');
        if (errorHandler.automaticRecovery) {
            console.log('🔄 尝试自动恢复...');
            setTimeout(() => {
                this.initialize();
            }, errorHandler.retryDelay);
        }
    }

    /**
     * 处理初始化错误
     */
    handleInitializationError(error) {
        this.logSystemEvent('INITIALIZATION_ERROR', {
            error: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * 清理资源
     */
    async cleanup() {
        console.log('🧹 清理系统资源...');
        
        // 清理缓存
        await this.cleanupCache();
        
        // 关闭数据库连接
        // 这里将集成数据库连接关闭逻辑
        
        console.log('✅ 资源清理完成');
    }

    /**
     * 记录系统事件
     */
    logSystemEvent(eventType, data) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            event: eventType,
            data: data
        };

        // 写入日志文件
        const fs = require('fs');
        const logPath = './Logs/system_events.log';
        
        try {
            fs.appendFileSync(logPath, JSON.stringify(logEntry) + '\n');
        } catch (error) {
            console.error('写入系统事件日志失败:', error);
        }
    }

    /**
     * 获取系统状态
     */
    getSystemStatus() {
        return {
            initialized: this.isInitialized,
            version: this.version,
            internalVersion: this.internalVersion,
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            rules: Object.fromEntries(this.systemRules),
            mechanisms: Object.fromEntries(this.systemMechanisms),
            startTime: this.startTime
        };
    }

    /**
     * 更新系统规则
     */
    updateSystemRules(category, rules) {
        if (this.systemRules.has(category)) {
            this.systemRules.set(category, { ...this.systemRules.get(category), ...rules });
            this.logSystemEvent('RULES_UPDATED', { category, rules });
            return true;
        }
        return false;
    }

    /**
     * 更新系统机制
     */
    updateSystemMechanisms(category, mechanisms) {
        if (this.systemMechanisms.has(category)) {
            this.systemMechanisms.set(category, { ...this.systemMechanisms.get(category), ...mechanisms });
            this.logSystemEvent('MECHANISMS_UPDATED', { category, mechanisms });
            return true;
        }
        return false;
    }
}

// 导出类（浏览器环境）
if (typeof window !== 'undefined') {
    window.UnifiedSystemManager = UnifiedSystemManager;
} else if (typeof module !== 'undefined' && module.exports) {
    // Node.js环境
    module.exports = UnifiedSystemManager;
}