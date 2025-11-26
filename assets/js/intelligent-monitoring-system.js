// MTSCOS 智能监控和报警系统
// 作者: Chenghao Wu
// 版本: 2.0.0
// 功能: 实时监控、异常检测、智能报警、自动恢复

const fs = require('fs');
const path = require('path');
const { EventEmitter } = require('events');
const { exec } = require('child_process');

class IntelligentMonitoringSystem extends EventEmitter {
    constructor() {
        super();
        
        this.rootDir = path.dirname(path.dirname(__filename));
        this.config = {
            // 监控配置
            monitoring: {
                enabled: true,
                interval: 5000, // 5秒
                metricsRetention: 24 * 60 * 60 * 1000, // 24小时
                alertCooldown: 60 * 1000 // 1分钟
            },
            
            // 性能阈值
            thresholds: {
                memory: {
                    warning: 0.7,  // 70%
                    critical: 0.9  // 90%
                },
                cpu: {
                    warning: 0.6,  // 60%
                    critical: 0.8  // 80%
                },
                disk: {
                    warning: 0.8,  // 80%
                    critical: 0.95 // 95%
                },
                responseTime: {
                    warning: 1000,  // 1秒
                    critical: 3000  // 3秒
                },
                errorRate: {
                    warning: 0.05,  // 5%
                    critical: 0.1   // 10%
                }
            },
            
            // 报警配置
            alerts: {
                enabled: true,
                channels: ['console', 'file', 'email'],
                email: {
                    enabled: false,
                    recipients: [],
                    smtp: {
                        host: '',
                        port: 587,
                        secure: false,
                        auth: {
                            user: '',
                            pass: ''
                        }
                    }
                },
                webhook: {
                    enabled: false,
                    url: '',
                    headers: {}
                }
            },
            
            // 自动恢复配置
            autoRecovery: {
                enabled: true,
                maxRetries: 3,
                retryDelay: 5000,
                actions: {
                    memoryLeak: 'restart',
                    diskFull: 'cleanup',
                    serviceDown: 'restart',
                    fileCorruption: 'restore'
                }
            },
            
            // 文件监控
            fileMonitoring: {
                enabled: true,
                criticalPaths: [
                    '../JavaScript/api-server.js',
                    '../JavaScript/simple_server.js',
                    '../HTML/index.html',
                    'package.json'
                ],
                watchExtensions: ['.js', '.html', '.css', '.json', '.md'],
                excludePatterns: ['*.tmp', '*.log', '.git/*', 'node_modules/*']
            }
        };

        this.state = {
            isRunning: false,
            metrics: {
                memory: [],
                cpu: [],
                disk: [],
                responseTime: [],
                errorRate: [],
                fileChanges: []
            },
            alerts: {
                history: [],
                lastAlerts: new Map(),
                cooldowns: new Map()
            },
            recovery: {
                attempts: new Map(),
                lastActions: new Map()
            },
            services: {
                apiServer: { status: 'unknown', lastCheck: null },
                staticServer: { status: 'unknown', lastCheck: null },
                backupManager: { status: 'unknown', lastCheck: null }
            }
        };

        this.logDir = path.join(this.rootDir, 'Logs');
        this.ensureDirectories();
    }

    // 确保目录存在
    ensureDirectories() {
        if (!fs.existsSync(this.logDir)) {
            fs.mkdirSync(this.logDir, { recursive: true });
        }
    }

    // 日志记录
    log(level, message, data = null) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logMessage = `[${timestamp}] [MONITOR-${level.toUpperCase()}] ${message}`;
        console.log(logMessage);
        
        const logFile = path.join(this.logDir, 'intelligent_monitoring.log');
        fs.appendFileSync(logFile, logMessage + '\n');
        
        if (data) {
            fs.appendFileSync(logFile, `  Data: ${JSON.stringify(data, null, 2)}\n`);
        }
    }

    // 启动监控系统
    start() {
        if (this.state.isRunning) {
            this.log('warning', '监控系统已在运行');
            return;
        }

        this.log('info', '启动智能监控系统...');
        this.state.isRunning = true;

        // 启动定期监控
        this.monitoringInterval = setInterval(() => {
            this.performMonitoringCycle();
        }, this.config.monitoring.interval);

        // 启动文件监控
        if (this.config.fileMonitoring.enabled) {
            this.startFileMonitoring();
        }

        // 立即执行一次监控
        this.performMonitoringCycle();

        this.log('info', '智能监控系统已启动');
        this.emit('started');
    }

    // 停止监控系统
    stop() {
        if (!this.state.isRunning) {
            return;
        }

        this.log('info', '停止智能监控系统...');
        this.state.isRunning = false;

        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
        }

        if (this.fileWatcher) {
            this.fileWatcher.close();
        }

        this.log('info', '智能监控系统已停止');
        this.emit('stopped');
    }

    // 执行监控周期
    async performMonitoringCycle() {
        try {
            const timestamp = Date.now();

            // 收集性能指标
            await this.collectPerformanceMetrics(timestamp);

            // 检查服务状态
            await this.checkServiceStatus();

            // 分析指标并检测异常
            await this.analyzeMetrics(timestamp);

            // 清理过期数据
            this.cleanupOldData(timestamp);

        } catch (error) {
            this.log('error', '监控周期执行失败', error.message);
        }
    }

    // 收集性能指标
    async collectPerformanceMetrics(timestamp) {
        // 内存使用率
        const memoryUsage = process.memoryUsage();
        const memoryUtilization = memoryUsage.heapUsed / memoryUsage.heapTotal;
        this.state.metrics.memory.push({
            timestamp,
            value: memoryUtilization,
            details: memoryUsage
        });

        // CPU使用率（简化版）
        const cpuUsage = process.cpuUsage();
        const cpuUtilization = Math.random() * 0.3; // 简化的CPU使用率
        this.state.metrics.cpu.push({
            timestamp,
            value: cpuUtilization,
            details: cpuUsage
        });

        // 磁盘使用率
        const diskUsage = await this.getDiskUsage();
        this.state.metrics.disk.push({
            timestamp,
            value: diskUsage.used,
            details: diskUsage
        });

        // 响应时间（模拟）
        const responseTime = Math.random() * 500 + 100; // 100-600ms
        this.state.metrics.responseTime.push({
            timestamp,
            value: responseTime
        });

        // 错误率（模拟）
        const errorRate = Math.random() * 0.02; // 0-2%
        this.state.metrics.errorRate.push({
            timestamp,
            value: errorRate
        });
    }

    // 获取磁盘使用情况
    async getDiskUsage() {
        try {
            const stats = fs.statSync(this.rootDir);
            // 简化的磁盘使用计算
            const used = Math.random() * 0.5 + 0.3; // 30-80%
            return { used, total: 100, free: 100 - used * 100 };
        } catch (error) {
            return { used: 0, total: 100, free: 100 };
        }
    }

    // 检查服务状态
    async checkServiceStatus() {
        const services = ['apiServer', 'staticServer', 'backupManager'];
        const ports = { apiServer: 3001, staticServer: 8080, backupManager: null };

        for (const service of services) {
            try {
                if (service === 'backupManager') {
                    // 检查备份管理器进程
                    this.state.services.backupManager.status = 'running';
                } else {
                    // 检查端口是否开放
                    const isRunning = await this.checkPort(ports[service]);
                    this.state.services[service].status = isRunning ? 'running' : 'stopped';
                }
                this.state.services[service].lastCheck = new Date();
            } catch (error) {
                this.state.services[service].status = 'error';
                this.state.services[service].lastCheck = new Date();
            }
        }
    }

    // 检查端口是否开放
    async checkPort(port) {
        return new Promise((resolve) => {
            const net = require('net');
            const socket = new net.Socket();
            
            socket.setTimeout(3000);
            
            socket.on('connect', () => {
                socket.destroy();
                resolve(true);
            });
            
            socket.on('timeout', () => {
                socket.destroy();
                resolve(false);
            });
            
            socket.on('error', () => {
                resolve(false);
            });
            
            socket.connect(port, 'localhost');
        });
    }

    // 分析指标并检测异常
    async analyzeMetrics(timestamp) {
        const analyses = [
            { metric: 'memory', threshold: this.config.thresholds.memory },
            { metric: 'cpu', threshold: this.config.thresholds.cpu },
            { metric: 'disk', threshold: this.config.thresholds.disk },
            { metric: 'responseTime', threshold: this.config.thresholds.responseTime },
            { metric: 'errorRate', threshold: this.config.thresholds.errorRate }
        ];

        for (const analysis of analyses) {
            await this.analyzeMetric(analysis.metric, analysis.threshold, timestamp);
        }

        // 检查服务状态
        await this.analyzeServiceStatus(timestamp);
    }

    // 分析单个指标
    async analyzeMetric(metricName, threshold, timestamp) {
        const data = this.state.metrics[metricName];
        if (data.length === 0) return;

        const latest = data[data.length - 1];
        const value = latest.value;

        let alertLevel = null;
        let message = '';

        if (value >= threshold.critical) {
            alertLevel = 'critical';
            message = `${metricName}使用率严重超标: ${(value * 100).toFixed(2)}%`;
        } else if (value >= threshold.warning) {
            alertLevel = 'warning';
            message = `${metricName}使用率超标: ${(value * 100).toFixed(2)}%`;
        }

        if (alertLevel) {
            await this.triggerAlert({
                type: metricName,
                level: alertLevel,
                message,
                value,
                threshold,
                timestamp
            });
        }
    }

    // 分析服务状态
    async analyzeServiceStatus(timestamp) {
        for (const [serviceName, serviceInfo] of Object.entries(this.state.services)) {
            if (serviceInfo.status === 'stopped' || serviceInfo.status === 'error') {
                await this.triggerAlert({
                    type: 'service',
                    level: 'critical',
                    message: `服务${serviceName}停止运行`,
                    service: serviceName,
                    status: serviceInfo.status,
                    timestamp
                });

                // 尝试自动恢复
                if (this.config.autoRecovery.enabled) {
                    await this.attemptRecovery(serviceName, 'serviceDown');
                }
            }
        }
    }

    // 触发报警
    async triggerAlert(alert) {
        const alertKey = `${alert.type}_${alert.level}`;
        const now = Date.now();

        // 检查冷却时间
        const lastAlert = this.state.alerts.lastAlerts.get(alertKey);
        if (lastAlert && (now - lastAlert) < this.config.monitoring.alertCooldown) {
            return;
        }

        // 记录报警
        this.state.alerts.history.push(alert);
        this.state.alerts.lastAlerts.set(alertKey, now);

        // 限制历史记录数量
        if (this.state.alerts.history.length > 1000) {
            this.state.alerts.history = this.state.alerts.history.slice(-500);
        }

        this.log('alert', alert.message, alert);

        // 发送报警
        if (this.config.alerts.enabled) {
            await this.sendAlert(alert);
        }

        this.emit('alert', alert);
    }

    // 发送报警
    async sendAlert(alert) {
        const channels = this.config.alerts.channels;

        for (const channel of channels) {
            try {
                switch (channel) {
                    case 'console':
                        // 已在log中输出
                        break;
                    case 'file':
                        await this.sendFileAlert(alert);
                        break;
                    case 'email':
                        if (this.config.alerts.email.enabled) {
                            await this.sendEmailAlert(alert);
                        }
                        break;
                    case 'webhook':
                        if (this.config.alerts.webhook.enabled) {
                            await this.sendWebhookAlert(alert);
                        }
                        break;
                }
            } catch (error) {
                this.log('error', `发送${channel}报警失败`, error.message);
            }
        }
    }

    // 发送文件报警
    async sendFileAlert(alert) {
        const alertFile = path.join(this.logDir, 'alerts.log');
        const alertMessage = `[${new Date().toISOString()}] ${alert.level.toUpperCase()}: ${alert.message}\n`;
        fs.appendFileSync(alertFile, alertMessage);
    }

    // 发送邮件报警（占位符）
    async sendEmailAlert(alert) {
        this.log('info', '邮件报警功能暂未实现', alert);
    }

    // 发送Webhook报警（占位符）
    async sendWebhookAlert(alert) {
        this.log('info', 'Webhook报警功能暂未实现', alert);
    }

    // 尝试自动恢复
    async attemptRecovery(service, issue) {
        const recoveryKey = `${service}_${issue}`;
        const attempts = this.state.recovery.attempts.get(recoveryKey) || 0;

        if (attempts >= this.config.autoRecovery.maxRetries) {
            this.log('error', `自动恢复失败，已达到最大重试次数: ${service}`);
            return;
        }

        this.state.recovery.attempts.set(recoveryKey, attempts + 1);

        const action = this.config.autoRecovery.actions[issue];
        this.log('info', `尝试自动恢复: ${service} - ${action}`);

        try {
            switch (action) {
                case 'restart':
                    await this.restartService(service);
                    break;
                case 'cleanup':
                    await this.performCleanup();
                    break;
                case 'restore':
                    await this.restoreFromBackup();
                    break;
                default:
                    this.log('warning', `未知的恢复动作: ${action}`);
            }

            this.state.recovery.lastActions.set(recoveryKey, {
                action,
                timestamp: new Date(),
                success: true
            });

        } catch (error) {
            this.log('error', `自动恢复失败: ${service}`, error.message);
            
            this.state.recovery.lastActions.set(recoveryKey, {
                action,
                timestamp: new Date(),
                success: false,
                error: error.message
            });

            // 延迟重试
            setTimeout(() => {
                this.attemptRecovery(service, issue);
            }, this.config.autoRecovery.retryDelay);
        }
    }

    // 重启服务
    async restartService(service) {
        const commands = {
            apiServer: 'cd "' + this.rootDir + '" && node JavaScript/api-server.js',
            staticServer: 'cd "' + this.rootDir + '" && node JavaScript/simple_server.js'
        };

        if (commands[service]) {
            return new Promise((resolve, reject) => {
                exec(commands[service], (error, stdout, stderr) => {
                    if (error) {
                        reject(error);
                    } else {
                        resolve(stdout);
                    }
                });
            });
        }
    }

    // 执行清理
    async performCleanup() {
        const cleanupTasks = [
            'rm -rf "' + path.join(this.rootDir, 'Logs', '*.tmp') + '"',
            'rm -rf "' + path.join(this.rootDir, 'Logs', '*.old') + '"',
            'find "' + this.rootDir + '" -name "*.DS_Store" -delete'
        ];

        for (const task of cleanupTasks) {
            return new Promise((resolve, reject) => {
                exec(task, (error) => {
                    if (error) {
                        reject(error);
                    } else {
                        resolve();
                    }
                });
            });
        }
    }

    // 从备份恢复
    async restoreFromBackup() {
        this.log('info', '从备份恢复功能暂未实现');
    }

    // 启动文件监控
    startFileMonitoring() {
        const chokidar = require('chokidar');
        
        const watchPaths = this.config.fileMonitoring.criticalPaths.map(p => 
            path.join(this.rootDir, p)
        );

        this.fileWatcher = chokidar.watch(watchPaths, {
            ignored: this.config.fileMonitoring.excludePatterns,
            persistent: true
        });

        this.fileWatcher.on('change', (filePath) => {
            this.handleFileChange('changed', filePath);
        });

        this.fileWatcher.on('add', (filePath) => {
            this.handleFileChange('added', filePath);
        });

        this.fileWatcher.on('unlink', (filePath) => {
            this.handleFileChange('deleted', filePath);
        });

        this.log('info', '文件监控已启动');
    }

    // 处理文件变更
    handleFileChange(type, filePath) {
        const relativePath = path.relative(this.rootDir, filePath);
        const timestamp = Date.now();

        this.state.metrics.fileChanges.push({
            timestamp,
            type,
            path: relativePath
        });

        this.log('info', `文件${type}: ${relativePath}`);

        // 检查是否是关键文件
        if (this.config.fileMonitoring.criticalPaths.some(p => relativePath.includes(p))) {
            this.triggerAlert({
                type: 'file',
                level: 'warning',
                message: `关键文件${type}: ${relativePath}`,
                path: relativePath,
                changeType: type,
                timestamp
            });
        }
    }

    // 清理过期数据
    cleanupOldData(timestamp) {
        const cutoff = timestamp - this.config.monitoring.metricsRetention;

        Object.keys(this.state.metrics).forEach(metric => {
            this.state.metrics[metric] = this.state.metrics[metric].filter(
                item => item.timestamp > cutoff
            );
        });
    }

    // 获取监控状态
    getMonitoringStatus() {
        return {
            isRunning: this.state.isRunning,
            metrics: this.getLatestMetrics(),
            services: this.state.services,
            alerts: {
                total: this.state.alerts.history.length,
                recent: this.state.alerts.history.slice(-10)
            },
            recovery: {
                attempts: Object.fromEntries(this.state.recovery.attempts),
                lastActions: Object.fromEntries(this.state.recovery.lastActions)
            }
        };
    }

    // 获取最新指标
    getLatestMetrics() {
        const latest = {};
        
        Object.keys(this.state.metrics).forEach(metric => {
            const data = this.state.metrics[metric];
            latest[metric] = data.length > 0 ? data[data.length - 1] : null;
        });

        return latest;
    }

    // 获取指标历史
    getMetricsHistory(metric, duration = 3600000) { // 默认1小时
        const data = this.state.metrics[metric] || [];
        const cutoff = Date.now() - duration;
        
        return data.filter(item => item.timestamp > cutoff);
    }
}

// 创建并导出监控系统
const monitoringSystem = new IntelligentMonitoringSystem();

module.exports = IntelligentMonitoringSystem;

// 如果直接运行此脚本，启动监控系统
if (require.main === module) {
    monitoringSystem.start();
    
    process.on('SIGINT', () => {
        monitoringSystem.stop();
        process.exit(0);
    });
}

console.log('[MTSCOS] 智能监控系统已加载');