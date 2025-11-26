#!/usr/bin/env node

/**
 * MTSCOS AI 灰度测试环境监控脚本
 * 用途: 实时监控灰度测试环境，检测恶意篡改和异常情况
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync, spawn } = require('child_process');

class EnvironmentMonitor {
    constructor() {
        // 基础配置
        this.basePath = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Staging';
        this.configPath = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/config/staging-environment.json';
        this.monitorConfig = {
            checkInterval: 60000, // 检查间隔，默认60秒
            alertThreshold: 3,    // 警报阈值
            maxAlertFrequency: 300000, // 最大警报频率，5分钟
            logFile: path.join(this.basePath, 'Logs/environment-monitor.log'),
            integrityFile: path.join(this.basePath, 'Logs/file-integrity.json'),
            excludePatterns: [
                'node_modules',
                '.git',
                'Logs',
                'Temp',
                'Uploads',
                '.DS_Store',
                '.env'
            ],
            criticalFiles: [
                'staging-manager.js',
                'Scripts/maintenance/deploy.sh',
                'Scripts/upgrades/update-dependencies.sh'
            ]
        };
        
        // 状态变量
        this.lastAlertTime = 0;
        this.alertCount = 0;
        this.monitoringActive = false;
        this.monitoringInterval = null;
        this.integrityHashes = {};
    }

    /**
     * 初始化监控器
     */
    async initialize() {
        try {
            this.log('==========================================');
            this.log('MTSCOS AI 灰度测试环境监控系统启动');
            this.log('==========================================');
            
            // 加载配置
            await this.loadConfiguration();
            
            // 初始化日志目录
            this.ensureLogDirectory();
            
            // 加载或初始化文件完整性数据库
            await this.initializeIntegrityDatabase();
            
            // 执行初始检查
            await this.performInitialChecks();
            
            this.log('监控系统初始化完成');
            return true;
        } catch (error) {
            this.logError('初始化失败', error);
            return false;
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
                if (config.stagingEnvironment && config.stagingEnvironment.monitoring) {
                    this.monitorConfig = {
                        ...this.monitorConfig,
                        ...config.stagingEnvironment.monitoring
                    };
                }
                
                this.log(`已加载配置: ${this.configPath}`);
            }
        } catch (error) {
            this.logError('加载配置失败', error);
            throw new Error('配置加载失败');
        }
    }

    /**
     * 确保日志目录存在
     */
    ensureLogDirectory() {
        const logDir = path.dirname(this.monitorConfig.logFile);
        if (!fs.existsSync(logDir)) {
            fs.mkdirSync(logDir, { recursive: true });
            this.log(`创建日志目录: ${logDir}`);
        }
    }

    /**
     * 初始化文件完整性数据库
     */
    async initializeIntegrityDatabase() {
        try {
            if (fs.existsSync(this.monitorConfig.integrityFile)) {
                const integrityData = fs.readFileSync(this.monitorConfig.integrityFile, 'utf8');
                this.integrityHashes = JSON.parse(integrityData);
                this.log(`已加载文件完整性数据库，包含 ${Object.keys(this.integrityHashes).length} 个文件`);
            } else {
                // 首次运行，创建文件哈希
                this.log('首次运行，创建文件完整性数据库...');
                await this.buildIntegrityDatabase();
                this.saveIntegrityDatabase();
                this.log('文件完整性数据库创建完成');
            }
        } catch (error) {
            this.logError('初始化文件完整性数据库失败', error);
            // 尝试重新构建数据库
            await this.buildIntegrityDatabase();
            this.saveIntegrityDatabase();
        }
    }

    /**
     * 构建文件完整性数据库
     */
    async buildIntegrityDatabase() {
        const startTime = Date.now();
        const newHashes = {};
        
        function shouldExclude(filePath, excludePatterns) {
            return excludePatterns.some(pattern => 
                filePath.includes(pattern) || filePath.endsWith(pattern)
            );
        }
        
        function processDirectory(dir, callback) {
            try {
                const entries = fs.readdirSync(dir, { withFileTypes: true });
                
                for (const entry of entries) {
                    const fullPath = path.join(dir, entry.name);
                    
                    // 检查是否应该排除
                    if (shouldExclude(fullPath, this.monitorConfig.excludePatterns)) {
                        continue;
                    }
                    
                    if (entry.isDirectory()) {
                        processDirectory.call(this, fullPath, callback);
                    } else if (entry.isFile()) {
                        try {
                            const hash = this.calculateFileHash(fullPath);
                            callback(fullPath, hash);
                        } catch (error) {
                            this.logError(`计算文件哈希失败: ${fullPath}`, error);
                        }
                    }
                }
            } catch (error) {
                this.logError(`处理目录失败: ${dir}`, error);
            }
        }
        
        processDirectory.call(this, this.basePath, (filePath, hash) => {
            // 计算相对路径作为键
            const relativePath = path.relative(this.basePath, filePath);
            newHashes[relativePath] = {
                hash,
                timestamp: Date.now(),
                size: fs.statSync(filePath).size
            };
        });
        
        this.integrityHashes = newHashes;
        const duration = (Date.now() - startTime) / 1000;
        this.log(`构建完整性数据库完成，处理了 ${Object.keys(newHashes).length} 个文件，耗时 ${duration.toFixed(2)} 秒`);
    }

    /**
     * 保存文件完整性数据库
     */
    saveIntegrityDatabase() {
        try {
            fs.writeFileSync(
                this.monitorConfig.integrityFile,
                JSON.stringify(this.integrityHashes, null, 2)
            );
            this.log(`文件完整性数据库已保存: ${this.monitorConfig.integrityFile}`);
        } catch (error) {
            this.logError('保存文件完整性数据库失败', error);
        }
    }

    /**
     * 计算文件哈希值
     */
    calculateFileHash(filePath) {
        const data = fs.readFileSync(filePath);
        return crypto.createHash('sha256').update(data).digest('hex');
    }

    /**
     * 执行初始检查
     */
    async performInitialChecks() {
        this.log('执行初始环境检查...');
        
        // 检查目录结构
        await this.checkDirectoryStructure();
        
        // 检查关键文件
        await this.checkCriticalFiles();
        
        // 检查系统资源
        await this.checkSystemResources();
        
        this.log('初始检查完成');
    }

    /**
     * 检查目录结构
     */
    async checkDirectoryStructure() {
        try {
            const requiredDirs = [
                path.join(this.basePath, 'Backups'),
                path.join(this.basePath, 'Logs'),
                path.join(this.basePath, 'Results'),
                path.join(this.basePath, 'Scripts'),
                path.join(this.basePath, 'Temp'),
                path.join(this.basePath, 'Uploads'),
                path.join(this.basePath, 'Users')
            ];
            
            let missingDirs = [];
            for (const dir of requiredDirs) {
                if (!fs.existsSync(dir)) {
                    missingDirs.push(dir);
                }
            }
            
            if (missingDirs.length > 0) {
                this.logError('目录结构检查失败：缺少必要目录', {
                    missingDirectories: missingDirs
                });
                
                // 尝试创建缺失的目录
                for (const dir of missingDirs) {
                    try {
                        fs.mkdirSync(dir, { recursive: true });
                        this.log(`已创建缺失的目录: ${dir}`);
                    } catch (error) {
                        this.logError(`创建目录失败: ${dir}`, error);
                    }
                }
            } else {
                this.log('目录结构检查通过');
            }
        } catch (error) {
            this.logError('目录结构检查失败', error);
        }
    }

    /**
     * 检查关键文件
     */
    async checkCriticalFiles() {
        try {
            let missingFiles = [];
            let modifiedFiles = [];
            
            for (const relPath of this.monitorConfig.criticalFiles) {
                const fullPath = path.join(this.basePath, relPath);
                
                if (!fs.existsSync(fullPath)) {
                    missingFiles.push(fullPath);
                } else if (this.integrityHashes[relPath]) {
                    const currentHash = this.calculateFileHash(fullPath);
                    if (currentHash !== this.integrityHashes[relPath].hash) {
                        modifiedFiles.push(relPath);
                    }
                }
            }
            
            if (missingFiles.length > 0) {
                this.logError('关键文件检查失败：文件缺失', {
                    missingFiles
                });
                this.triggerAlert('CRITICAL_FILE_MISSING', { missingFiles });
            }
            
            if (modifiedFiles.length > 0) {
                this.logError('关键文件检查失败：文件被修改', {
                    modifiedFiles
                });
                this.triggerAlert('CRITICAL_FILE_MODIFIED', { modifiedFiles });
            }
            
            if (missingFiles.length === 0 && modifiedFiles.length === 0) {
                this.log('关键文件检查通过');
            }
        } catch (error) {
            this.logError('关键文件检查失败', error);
        }
    }

    /**
     * 检查系统资源
     */
    async checkSystemResources() {
        try {
            // 检查磁盘空间
            const diskInfo = this.getDiskInfo(this.basePath);
            if (diskInfo.percentUsed > 90) {
                this.logError('磁盘空间警告', {
                    percentUsed: diskInfo.percentUsed,
                    freeSpace: diskInfo.freeSpace
                });
                this.triggerAlert('DISK_SPACE_WARNING', diskInfo);
            }
            
            // 检查内存使用情况（仅在支持的系统上）
            try {
                const memoryInfo = this.getMemoryInfo();
                if (memoryInfo.percentUsed > 85) {
                    this.logError('内存使用警告', memoryInfo);
                    this.triggerAlert('MEMORY_USAGE_WARNING', memoryInfo);
                }
            } catch (error) {
                this.logError('获取内存信息失败', error);
            }
            
            this.log('系统资源检查完成');
        } catch (error) {
            this.logError('系统资源检查失败', error);
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
     * 获取内存信息
     */
    getMemoryInfo() {
        try {
            // 在不同操作系统上可能需要调整命令
            if (process.platform === 'darwin') {
                const output = execSync('vm_stat').toString();
                const lines = output.trim().split('\n');
                
                // 提取内存信息
                let freeMemory = 0;
                let activeMemory = 0;
                let inactiveMemory = 0;
                let wiredMemory = 0;
                
                for (const line of lines) {
                    if (line.includes('Pages free')) {
                        freeMemory = parseInt(line.match(/\d+/)[0]) * 4096;
                    } else if (line.includes('Pages active')) {
                        activeMemory = parseInt(line.match(/\d+/)[0]) * 4096;
                    } else if (line.includes('Pages inactive')) {
                        inactiveMemory = parseInt(line.match(/\d+/)[0]) * 4096;
                    } else if (line.includes('Pages wired down')) {
                        wiredMemory = parseInt(line.match(/\d+/)[0]) * 4096;
                    }
                }
                
                const usedMemory = activeMemory + inactiveMemory + wiredMemory;
                // 这只是估算，实际总内存需要其他命令获取
                const totalMemory = usedMemory + freeMemory;
                const percentUsed = totalMemory > 0 ? (usedMemory / totalMemory) * 100 : 0;
                
                return {
                    totalMemory,
                    usedMemory,
                    freeMemory,
                    percentUsed,
                    formatted: {
                        total: this.formatBytes(totalMemory),
                        used: this.formatBytes(usedMemory),
                        free: this.formatBytes(freeMemory)
                    }
                };
            } else {
                // 对于Linux系统
                const output = execSync('free -b').toString();
                const lines = output.trim().split('\n');
                const memoryLine = lines[1];
                const parts = memoryLine.split(/\s+/);
                
                const totalMemory = parseInt(parts[1]);
                const usedMemory = parseInt(parts[2]);
                const freeMemory = parseInt(parts[3]);
                const percentUsed = (usedMemory / totalMemory) * 100;
                
                return {
                    totalMemory,
                    usedMemory,
                    freeMemory,
                    percentUsed,
                    formatted: {
                        total: this.formatBytes(totalMemory),
                        used: this.formatBytes(usedMemory),
                        free: this.formatBytes(freeMemory)
                    }
                };
            }
        } catch (error) {
            throw new Error(`获取内存信息失败: ${error.message}`);
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
     * 开始监控
     */
    startMonitoring() {
        if (this.monitoringActive) {
            this.log('监控已经在运行中');
            return;
        }
        
        this.log(`启动环境监控，检查间隔: ${this.monitorConfig.checkInterval / 1000}秒`);
        this.monitoringActive = true;
        
        // 执行首次监控
        this.performMonitoringCheck();
        
        // 设置定时器
        this.monitoringInterval = setInterval(() => {
            this.performMonitoringCheck();
        }, this.monitorConfig.checkInterval);
    }

    /**
     * 停止监控
     */
    stopMonitoring() {
        if (!this.monitoringActive) {
            this.log('监控已经停止');
            return;
        }
        
        this.log('停止环境监控');
        this.monitoringActive = false;
        
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
    }

    /**
     * 执行监控检查
     */
    async performMonitoringCheck() {
        try {
            const startTime = Date.now();
            this.log('开始执行监控检查...');
            
            // 检查文件完整性
            await this.checkFileIntegrity();
            
            // 检查目录结构
            await this.checkDirectoryStructure();
            
            // 检查系统资源
            await this.checkSystemResources();
            
            // 检查异常进程
            await this.checkSuspiciousProcesses();
            
            // 生成状态报告
            await this.generateStatusReport();
            
            const duration = (Date.now() - startTime) / 1000;
            this.log(`监控检查完成，耗时 ${duration.toFixed(2)} 秒`);
        } catch (error) {
            this.logError('监控检查失败', error);
        }
    }

    /**
     * 检查文件完整性
     */
    async checkFileIntegrity() {
        try {
            const modifiedFiles = [];
            const addedFiles = [];
            const missingFiles = [];
            
            // 检查现有文件是否被修改或删除
            for (const [relPath, info] of Object.entries(this.integrityHashes)) {
                const fullPath = path.join(this.basePath, relPath);
                
                if (!fs.existsSync(fullPath)) {
                    missingFiles.push(relPath);
                } else {
                    try {
                        const currentHash = this.calculateFileHash(fullPath);
                        if (currentHash !== info.hash) {
                            modifiedFiles.push(relPath);
                        }
                    } catch (error) {
                        this.logError(`检查文件完整性失败: ${fullPath}`, error);
                    }
                }
            }
            
            // 检查是否有新文件添加
            function scanDirectory(dir, baseDir, callback) {
                try {
                    const entries = fs.readdirSync(dir, { withFileTypes: true });
                    
                    for (const entry of entries) {
                        const fullPath = path.join(dir, entry.name);
                        const relPath = path.relative(baseDir, fullPath);
                        
                        // 跳过排除的模式
                        if (this.monitorConfig.excludePatterns.some(pattern => 
                            relPath.includes(pattern) || relPath.endsWith(pattern)
                        )) {
                            continue;
                        }
                        
                        if (entry.isDirectory()) {
                            scanDirectory.call(this, fullPath, baseDir, callback);
                        } else if (entry.isFile() && !this.integrityHashes[relPath]) {
                            callback(relPath);
                        }
                    }
                } catch (error) {
                    this.logError(`扫描目录失败: ${dir}`, error);
                }
            }
            
            scanDirectory.call(this, this.basePath, this.basePath, (relPath) => {
                addedFiles.push(relPath);
            });
            
            // 报告发现的问题
            if (modifiedFiles.length > 0) {
                this.logError('文件完整性检查失败：检测到修改的文件', {
                    count: modifiedFiles.length,
                    files: modifiedFiles.slice(0, 10) // 只显示前10个
                });
                this.triggerAlert('FILE_MODIFICATION_DETECTED', { modifiedFiles });
            }
            
            if (missingFiles.length > 0) {
                this.logError('文件完整性检查失败：检测到缺失的文件', {
                    count: missingFiles.length,
                    files: missingFiles.slice(0, 10)
                });
                this.triggerAlert('FILE_MISSING_DETECTED', { missingFiles });
            }
            
            if (addedFiles.length > 0) {
                this.log('文件完整性检查：检测到新添加的文件', {
                    count: addedFiles.length,
                    files: addedFiles.slice(0, 10)
                });
                // 自动更新完整性数据库
                for (const relPath of addedFiles) {
                    const fullPath = path.join(this.basePath, relPath);
                    try {
                        this.integrityHashes[relPath] = {
                            hash: this.calculateFileHash(fullPath),
                            timestamp: Date.now(),
                            size: fs.statSync(fullPath).size
                        };
                    } catch (error) {
                        this.logError(`更新文件哈希失败: ${fullPath}`, error);
                    }
                }
                this.saveIntegrityDatabase();
            }
            
            if (modifiedFiles.length === 0 && missingFiles.length === 0 && addedFiles.length === 0) {
                this.log('文件完整性检查通过');
            }
        } catch (error) {
            this.logError('文件完整性检查失败', error);
        }
    }

    /**
     * 检查可疑进程
     */
    async checkSuspiciousProcesses() {
        try {
            // 定义可疑进程模式
            const suspiciousPatterns = [
                'nc ', 'netcat', 'telnet', 'bash -i', 
                'python -c', 'perl -e', 'ruby -e',
                'sh -c', 'curl | bash', 'wget | bash'
            ];
            
            // 获取进程列表
            const processes = this.getRunningProcesses();
            const suspiciousProcesses = [];
            
            for (const process of processes) {
                if (suspiciousPatterns.some(pattern => 
                    process.cmdLine && process.cmdLine.includes(pattern)
                )) {
                    suspiciousProcesses.push(process);
                }
            }
            
            if (suspiciousProcesses.length > 0) {
                this.logError('检测到可疑进程', {
                    count: suspiciousProcesses.length,
                    processes: suspiciousProcesses.slice(0, 5)
                });
                this.triggerAlert('SUSPICIOUS_PROCESSES_DETECTED', { 
                    processes: suspiciousProcesses 
                });
            } else {
                this.log('进程检查通过，未发现可疑进程');
            }
        } catch (error) {
            this.logError('进程检查失败', error);
        }
    }

    /**
     * 获取运行中的进程
     */
    getRunningProcesses() {
        try {
            if (process.platform === 'darwin' || process.platform === 'linux') {
                const output = execSync('ps aux').toString();
                const lines = output.trim().split('\n');
                const processes = [];
                
                // 跳过标题行
                for (let i = 1; i < lines.length; i++) {
                    const parts = lines[i].split(/\s+/);
                    if (parts.length >= 11) {
                        processes.push({
                            user: parts[0],
                            pid: parseInt(parts[1]),
                            cpu: parseFloat(parts[2]),
                            mem: parseFloat(parts[3]),
                            vsz: parseInt(parts[4]),
                            rss: parseInt(parts[5]),
                            tty: parts[6],
                            stat: parts[7],
                            start: parts[8],
                            time: parts[9],
                            cmdLine: parts.slice(10).join(' ')
                        });
                    }
                }
                
                return processes;
            } else {
                this.log('警告: 进程监控功能仅在 macOS 和 Linux 上支持');
                return [];
            }
        } catch (error) {
            throw new Error(`获取进程列表失败: ${error.message}`);
        }
    }

    /**
     * 生成状态报告
     */
    async generateStatusReport() {
        try {
            const report = {
                timestamp: new Date().toISOString(),
                environment: 'staging',
                checks: {
                    fileIntegrity: 'pending',
                    directoryStructure: 'pending',
                    systemResources: 'pending',
                    processCheck: 'pending'
                },
                alerts: this.alertCount,
                metrics: {
                    monitoredFiles: Object.keys(this.integrityHashes).length
                },
                resources: {
                    disk: this.getDiskInfo(this.basePath)
                }
            };
            
            // 尝试获取内存信息
            try {
                report.resources.memory = this.getMemoryInfo();
            } catch (error) {
                this.logError('获取内存信息失败', error);
            }
            
            // 保存报告
            const reportPath = path.join(
                this.basePath,
                'Logs',
                `monitoring-report-${new Date().toISOString().split('T')[0]}.json`
            );
            
            fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
            this.log(`监控状态报告已生成: ${reportPath}`);
        } catch (error) {
            this.logError('生成状态报告失败', error);
        }
    }

    /**
     * 触发警报
     */
    triggerAlert(alertType, alertData) {
        const now = Date.now();
        
        // 检查警报频率限制
        if (now - this.lastAlertTime < this.monitorConfig.maxAlertFrequency) {
            this.log(`警报频率限制: ${alertType}`);
            return;
        }
        
        this.alertCount++;
        this.lastAlertTime = now;
        
        const alert = {
            id: `${alertType}-${Date.now()}`,
            type: alertType,
            timestamp: new Date().toISOString(),
            severity: this.getAlertSeverity(alertType),
            data: alertData
        };
        
        this.logError(`警报触发: ${alertType}`, alert);
        
        // 保存警报到日志
        const alertLogPath = path.join(
            this.basePath,
            'Logs',
            `alerts-${new Date().toISOString().split('T')[0]}.log`
        );
        
        try {
            fs.appendFileSync(alertLogPath, JSON.stringify(alert) + '\n');
        } catch (error) {
            this.logError('保存警报日志失败', error);
        }
        
        // 根据严重程度执行不同操作
        if (alert.severity === 'critical') {
            this.handleCriticalAlert(alert);
        } else if (alert.severity === 'high') {
            this.handleHighAlert(alert);
        }
    }

    /**
     * 获取警报严重程度
     */
    getAlertSeverity(alertType) {
        const criticalAlerts = [
            'CRITICAL_FILE_MODIFIED',
            'CRITICAL_FILE_MISSING',
            'SUSPICIOUS_PROCESSES_DETECTED',
            'SYSTEM_CRASH_DETECTED'
        ];
        
        const highAlerts = [
            'FILE_MODIFICATION_DETECTED',
            'FILE_MISSING_DETECTED',
            'DISK_SPACE_WARNING',
            'MEMORY_USAGE_WARNING'
        ];
        
        if (criticalAlerts.includes(alertType)) return 'critical';
        if (highAlerts.includes(alertType)) return 'high';
        return 'medium';
    }

    /**
     * 处理严重警报
     */
    handleCriticalAlert(alert) {
        this.log(`处理严重警报: ${alert.type}`);
        
        // 执行紧急操作
        switch (alert.type) {
            case 'CRITICAL_FILE_MODIFIED':
            case 'CRITICAL_FILE_MISSING':
                this.log('警告: 关键文件被修改或缺失，建议立即检查');
                // 这里可以添加更多的紧急响应措施
                break;
            case 'SUSPICIOUS_PROCESSES_DETECTED':
                this.log('警告: 检测到可疑进程，可能存在安全威胁');
                // 记录可疑进程详情
                for (const proc of alert.data.processes || []) {
                    this.log(`可疑进程: PID=${proc.pid}, CMD=${proc.cmdLine}`);
                }
                break;
        }
    }

    /**
     * 处理高优先级警报
     */
    handleHighAlert(alert) {
        this.log(`处理高优先级警报: ${alert.type}`);
        // 根据警报类型执行相应操作
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
            fs.appendFileSync(this.monitorConfig.logFile, logEntry + '\n');
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
            fs.appendFileSync(this.monitorConfig.logFile, logEntry + '\n');
        } catch (err) {
            console.error('写入错误日志失败:', err);
        }
    }

    /**
     * 重启监控服务
     */
    async restart() {
        this.log('重启监控服务...');
        this.stopMonitoring();
        
        // 重新初始化
        await this.initialize();
        this.startMonitoring();
        
        this.log('监控服务重启完成');
    }

    /**
     * 生成文件完整性报告
     */
    async generateIntegrityReport() {
        try {
            const report = {
                timestamp: new Date().toISOString(),
                totalFiles: Object.keys(this.integrityHashes).length,
                lastUpdated: new Date(Math.max(
                    ...Object.values(this.integrityHashes).map(h => h.timestamp)
                )).toISOString(),
                summary: {
                    javascriptFiles: Object.keys(this.integrityHashes)
                        .filter(f => f.endsWith('.js')).length,
                    htmlFiles: Object.keys(this.integrityHashes)
                        .filter(f => f.endsWith('.html')).length,
                    cssFiles: Object.keys(this.integrityHashes)
                        .filter(f => f.endsWith('.css')).length,
                    scriptFiles: Object.keys(this.integrityHashes)
                        .filter(f => f.includes('Scripts')).length
                }
            };
            
            const reportPath = path.join(
                this.basePath,
                'Logs',
                `integrity-report-${new Date().toISOString().split('T')[0]}.json`
            );
            
            fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
            this.log(`文件完整性报告已生成: ${reportPath}`);
            
            return report;
        } catch (error) {
            this.logError('生成完整性报告失败', error);
            throw error;
        }
    }
}

// 主函数
async function main() {
    const monitor = new EnvironmentMonitor();
    
    // 初始化监控器
    const initialized = await monitor.initialize();
    if (!initialized) {
        console.error('监控系统初始化失败，无法启动');
        process.exit(1);
    }
    
    // 启动监控
    monitor.startMonitoring();
    
    // 生成初始报告
    await monitor.generateIntegrityReport();
    
    // 监听进程信号
    process.on('SIGINT', () => {
        console.log('\n接收到终止信号，正在停止监控...');
        monitor.stopMonitoring();
        console.log('监控已停止');
        process.exit(0);
    });
    
    process.on('SIGTERM', () => {
        console.log('\n接收到终止信号，正在停止监控...');
        monitor.stopMonitoring();
        console.log('监控已停止');
        process.exit(0);
    });
    
    // 定期保存完整性数据库
    setInterval(() => {
        monitor.saveIntegrityDatabase();
    }, 300000); // 每5分钟保存一次
}

// 如果直接运行此脚本
if (require.main === module) {
    main().catch(error => {
        console.error('监控系统启动失败:', error);
        process.exit(1);
    });
}

module.exports = EnvironmentMonitor;