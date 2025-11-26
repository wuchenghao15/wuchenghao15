/**
 * 环境监控和预警系统
 * 实时监控多环境状态，提供智能预警和告警功能
 */

const fs = require('fs');
const path = require('path');
const { exec, spawn } = require('child_process');
const EventEmitter = require('events');
const crypto = require('crypto');

class EnvironmentMonitoringSystem extends EventEmitter {
    constructor(config = {}) {
        super();
        
        this.config = {
            // 监控配置
            monitoring: {
                enabled: true,
                interval: 30000,              // 监控间隔 30秒
                timeout: 10000,                // 检查超时 10秒
                retryAttempts: 3,              // 重试次数
                retryDelay: 5000               // 重试延迟
            },
            // 环境配置
            environments: {
                production: {
                    name: '生产环境',
                    url: 'http://localhost:8080',
                    healthEndpoint: '/health',
                    critical: true,
                    alertThreshold: 1          // 连续失败次数触发告警
                },
                staging: {
                    name: '预发布环境',
                    url: 'http://localhost:8081',
                    healthEndpoint: '/health',
                    critical: false,
                    alertThreshold: 3
                },
                gray: {
                    name: '灰色环境',
                    url: 'http://localhost:8082',
                    healthEndpoint: '/health',
                    critical: false,
                    alertThreshold: 2
                },
                development: {
                    name: '开发环境',
                    url: 'http://localhost:3000',
                    healthEndpoint: '/health',
                    critical: false,
                    alertThreshold: 5
                }
            },
            // 指标配置
            metrics: {
                enabled: true,
                collectInterval: 60000,        // 指标收集间隔 1分钟
                retentionDays: 7,              // 数据保留天数
                aggregationInterval: 300000    // 聚合间隔 5分钟
            },
            // 告警配置
            alerts: {
                enabled: true,
                channels: {
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
                    slack: {
                        enabled: false,
                        webhook: '',
                        channel: '#alerts'
                    },
                    webhook: {
                        enabled: false,
                        url: '',
                        headers: {}
                    }
                },
                thresholds: {
                    responseTime: 5000,         // 响应时间阈值 5秒
                    errorRate: 0.05,            // 错误率阈值 5%
                    cpuUsage: 80,               // CPU使用率阈值 80%
                    memoryUsage: 85,            // 内存使用率阈值 85%
                    diskUsage: 90               // 磁盘使用率阈值 90%
                },
                cooldown: 300000               // 告警冷却期 5分钟
            },
            // 仪表板配置
            dashboard: {
                enabled: true,
                port: 8083,
                refreshInterval: 5000,         // 刷新间隔 5秒
                historyPoints: 100             // 历史数据点数
            },
            ...config
        };

        // 监控状态
        this.isMonitoring = false;
        this.monitoringTimer = null;
        this.metricsTimer = null;
        
        // 环境状态
        this.environmentStatus = new Map();
        this.environmentMetrics = new Map();
        this.alertHistory = [];
        this.metricsHistory = [];
        
        // 告警状态
        this.alertCooldowns = new Map();
        this.activeAlerts = new Map();

        // 初始化
        this.initialize().catch(error => console.error(`[environment-monitoring-system.js] this.initialize failed:`, error));
    }

    /**
     * 初始化监控系统
     */
    async initialize() {
        this.log('🔍 初始化环境监控和预警系统...');

        try {
            // 创建监控目录
            await this.createMonitoringDirectories();
            
            // 初始化环境状态
            this.initializeEnvironmentStatus().catch(error => console.error(`[environment-monitoring-system.js] this.initializeEnvironmentStatus failed:`, error));
            
            // 加载历史数据
            await this.loadHistoricalData();
            
            // 启动监控
            if (this.config.monitoring.enabled) {
                await this.startMonitoring();
            }

            // 启动指标收集
            if (this.config.metrics.enabled) {
                await this.startMetricsCollection();
            }

            // 启动仪表板
            if (this.config.dashboard.enabled) {
                await this.startDashboard();
            }

            this.log('✅ 环境监控和预警系统初始化完成');
        } catch (error) {
            this.log(`❌ 初始化失败: ${error.message}`);
            throw error;
        }
    }

    /**
     * 创建监控目录
     */
    async createMonitoringDirectories() {
        const directories = [
            './monitoring',
            './monitoring/logs',
            './monitoring/metrics',
            './monitoring/alerts',
            './monitoring/reports'
        ];

        for (const dir of directories) {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
        }
    }

    /**
     * 初始化环境状态
     */
    initializeEnvironmentStatus() {
        for (const [envKey, envConfig] of Object.entries(this.config.environments)) {
            this.environmentStatus.set(envKey, {
                name: envConfig.name,
                url: envConfig.url,
                status: 'unknown',
                lastCheck: null,
                responseTime: null,
                errorRate: 0,
                uptime: 0,
                consecutiveFailures: 0,
                lastError: null,
                metrics: {
                    cpu: null,
                    memory: null,
                    disk: null,
                    network: null
                }
            });

            this.environmentMetrics.set(envKey, {
                responseTime: [],
                errorRate: [],
                cpu: [],
                memory: [],
                disk: [],
                network: []
            });
        }
    }

    /**
     * 启动监控
     */
    async startMonitoring() {
        if (this.isMonitoring) {
            return;
        }

        this.isMonitoring = true;
        this.log('🚀 启动环境监控...');

        // 立即执行一次检查
        await this.performEnvironmentChecks();

        // 设置定时监控
        this.monitoringTimer = setInterval(async () => {
            try {
                await this.performEnvironmentChecks();
            } catch (error) {
                this.log(`监控检查异常: ${error.message}`);
            }
        }, this.config.monitoring.interval);
    }

    /**
     * 停止监控
     */
    stopMonitoring() {
        if (this.monitoringTimer) {
            clearInterval(this.monitoringTimer);
            this.monitoringTimer = null;
        }

        if (this.metricsTimer) {
            clearInterval(this.metricsTimer);
            this.metricsTimer = null;
        }

        this.isMonitoring = false;
        this.log('⏹️ 环境监控已停止');
    }

    /**
     * 执行环境检查
     */
    async performEnvironmentChecks() {
        const checkPromises = [];

        for (const [envKey, envConfig] of Object.entries(this.config.environments)) {
            checkPromises.push(this.checkEnvironment(envKey, envConfig));
        }

        await Promise.allSettled(checkPromises);
        
        // 更新全局状态
        this.updateGlobalStatus().catch(error => console.error(`[environment-monitoring-system.js] this.updateGlobalStatus failed:`, error));
        
        // 触发状态更新事件
        this.emit('statusUpdate', this.getEnvironmentStatus().catch(error => console.error(`[environment-monitoring-system.js] this.getEnvironmentStatus failed:`, error)));
    }

    /**
     * 检查单个环境
     */
    async checkEnvironment(envKey, envConfig) {
        const status = this.environmentStatus.get(envKey);
        const startTime = Date.now().catch(error => console.error(`[environment-monitoring-system.js] Date.now failed:`, error));

        try {
            // 健康检查
            const healthResult = await this.performHealthCheck(envConfig);
            const responseTime = Date.now().catch(error => console.error(`[environment-monitoring-system.js] Date.now failed:`, error)) - startTime;

            // 更新状态
            status.status = 'healthy';
            status.lastCheck = new Date().toISOString();
            status.responseTime = responseTime;
            status.consecutiveFailures = 0;
            status.lastError = null;

            // 收集系统指标
            if (healthResult.metrics) {
                status.metrics = { ...status.metrics, ...healthResult.metrics };
            }

            // 记录指标
            this.recordMetrics(envKey, {
                responseTime,
                status: 'healthy',
                ...healthResult.metrics
            });

            // 检查告警条件
            await this.checkAlertConditions(envKey, status, envConfig);

        } catch (error) {
            const responseTime = Date.now().catch(error => console.error(`[environment-monitoring-system.js] Date.now failed:`, error)) - startTime;

            // 更新错误状态
            status.status = 'unhealthy';
            status.lastCheck = new Date().toISOString();
            status.responseTime = responseTime;
            status.consecutiveFailures++;
            status.lastError = error.message;

            // 记录指标
            this.recordMetrics(envKey, {
                responseTime,
                status: 'unhealthy',
                error: error.message
            });

            // 检查是否需要告警
            if (status.consecutiveFailures >= envConfig.alertThreshold) {
                await this.triggerAlert(envKey, 'environment_down', {
                    environment: envConfig.name,
                    consecutiveFailures: status.consecutiveFailures,
                    error: error.message
                }, envConfig.critical);
            }

            this.log(`⚠️ 环境检查失败 ${envConfig.name}: ${error.message}`);
        }
    }

    /**
     * 执行健康检查
     */
    async performHealthCheck(envConfig) {
        const healthUrl = `${envConfig.url}${envConfig.healthEndpoint}`;
        
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('健康检查超时'));
            }, this.config.monitoring.timeout);

            const startTime = Date.now().catch(error => console.error(`[environment-monitoring-system.js] Date.now failed:`, error));
            
            // 使用curl进行健康检查
            exec(`curl -f -s -w "%{http_code}" "${healthUrl}"`, (error, stdout, stderr) => {
                clearTimeout(timeout);
                const responseTime = Date.now().catch(error => console.error(`[environment-monitoring-system.js] Date.now failed:`, error)) - startTime;

                if (error) {
                    reject(new Error(`健康检查失败: ${error.message}`));
                    return;
                }

                const httpCode = stdout.trim().catch(error => console.error(`[environment-monitoring-system.js] stdout.trim failed:`, error));
                if (httpCode === '200') {
                    // 收集系统指标
                    this.collectSystemMetrics().then(metrics => {
                        resolve({
                            status: 'healthy',
                            responseTime,
                            metrics
                        });
                    }).catch(() => {
                        resolve({
                            status: 'healthy',
                            responseTime
                        });
                    });
                } else {
                    reject(new Error(`HTTP状态码: ${httpCode}`));
                }
            });
        });
    }

    /**
     * 收集系统指标
     */
    async collectSystemMetrics() {
        const metrics = {};

        try {
            // CPU使用率
            const cpuResult = await this.executeCommand('top -bn1 | grep "Cpu(s)" | awk \'{print $2}\' | cut -d\'%\' -f1');
            metrics.cpu = parseFloat(cpuResult.stdout.trim().catch(error => console.error(`[environment-monitoring-system.js] stdout.trim failed:`, error))) || 0;

            // 内存使用率
            const memResult = await this.executeCommand('free | grep Mem | awk \'{printf "%.1f", $3/$2 * 100.0}\'');
            metrics.memory = parseFloat(memResult.stdout.trim().catch(error => console.error(`[environment-monitoring-system.js] stdout.trim failed:`, error))) || 0;

            // 磁盘使用率
            const diskResult = await this.executeCommand('df -h / | tail -1 | awk \'{print $5}\' | cut -d\'%\' -f1');
            metrics.disk = parseFloat(diskResult.stdout.trim().catch(error => console.error(`[environment-monitoring-system.js] stdout.trim failed:`, error))) || 0;

        } catch (error) {
            this.log(`收集系统指标失败: ${error.message}`);
        }

        return metrics;
    }

    /**
     * 记录指标
     */
    recordMetrics(envKey, metrics) {
        const envMetrics = this.environmentMetrics.get(envKey);
        const timestamp = Date.now().catch(error => console.error(`[environment-monitoring-system.js] Date.now failed:`, error));

        // 记录响应时间
        if (metrics.responseTime) {
            envMetrics.responseTime.push({
                timestamp,
                value: metrics.responseTime
            });
        }

        // 记录错误率
        envMetrics.errorRate.push({
            timestamp,
            value: metrics.status === 'healthy' ? 0 : 1
        });

        // 记录系统指标
        if (metrics.cpu !== undefined) {
            envMetrics.cpu.push({
                timestamp,
                value: metrics.cpu
            });
        }

        if (metrics.memory !== undefined) {
            envMetrics.memory.push({
                timestamp,
                value: metrics.memory
            });
        }

        if (metrics.disk !== undefined) {
            envMetrics.disk.push({
                timestamp,
                value: metrics.disk
            });
        }

        // 限制历史数据长度
        const maxLength = this.config.dashboard.historyPoints;
        Object.values(envMetrics).forEach(metricArray => {
            if (metricArray.length > maxLength) {
                metricArray.splice(0, metricArray.length - maxLength);
            }
        });
    }

    /**
     * 检查告警条件
     */
    async checkAlertConditions(envKey, status, envConfig) {
        const thresholds = this.config.alerts.thresholds;
        const alerts = [];

        // 检查响应时间
        if (status.responseTime > thresholds.responseTime) {
            alerts.push({
                type: 'response_time_high',
                message: `响应时间过高: ${status.responseTime}ms`,
                value: status.responseTime,
                threshold: thresholds.responseTime
            });
        }

        // 检查CPU使用率
        if (status.metrics.cpu > thresholds.cpuUsage) {
            alerts.push({
                type: 'cpu_usage_high',
                message: `CPU使用率过高: ${status.metrics.cpu}%`,
                value: status.metrics.cpu,
                threshold: thresholds.cpuUsage
            });
        }

        // 检查内存使用率
        if (status.metrics.memory > thresholds.memoryUsage) {
            alerts.push({
                type: 'memory_usage_high',
                message: `内存使用率过高: ${status.metrics.memory}%`,
                value: status.metrics.memory,
                threshold: thresholds.memoryUsage
            });
        }

        // 检查磁盘使用率
        if (status.metrics.disk > thresholds.diskUsage) {
            alerts.push({
                type: 'disk_usage_high',
                message: `磁盘使用率过高: ${status.metrics.disk}%`,
                value: status.metrics.disk,
                threshold: thresholds.diskUsage
            });
        }

        // 触发告警
        for (const alert of alerts) {
            await this.triggerAlert(envKey, alert.type, {
                environment: envConfig.name,
                ...alert
            }, false);
        }
    }

    /**
     * 触发告警
     */
    async triggerAlert(envKey, alertType, data, isCritical = false) {
        const alertId = this.generateAlertId().catch(error => console.error(`[environment-monitoring-system.js] this.generateAlertId failed:`, error));
        const cooldownKey = `${envKey}_${alertType}`;

        // 检查冷却期
        if (this.isInCooldown(cooldownKey)) {
            return;
        }

        const alert = {
            alertId,
            envKey,
            alertType,
            data,
            isCritical,
            timestamp: new Date().toISOString(),
            status: 'active'
        };

        // 记录告警
        this.alertHistory.push(alert);
        this.activeAlerts.set(alertId, alert);

        // 设置冷却期
        this.setCooldown(cooldownKey);

        // 发送告警通知
        await this.sendAlertNotifications(alert);

        // 触发告警事件
        this.emit('alert', alert);

        this.log(`🚨 告警触发: ${alertType} - ${data.message}`);
    }

    /**
     * 发送告警通知
     */
    async sendAlertNotifications(alert) {
        const channels = this.config.alerts.channels;

        // 邮件通知
        if (channels.email.enabled) {
            await this.sendEmailAlert(alert);
        }

        // Slack通知
        if (channels.slack.enabled) {
            await this.sendSlackAlert(alert);
        }

        // Webhook通知
        if (channels.webhook.enabled) {
            await this.sendWebhookAlert(alert);
        }
    }

    /**
     * 发送邮件告警
     */
    async sendEmailAlert(alert) {
        try {
            const nodemailer = require('nodemailer');
            const transporter = nodemailer.createTransporter(this.config.alerts.channels.email.smtp);

            const mailOptions = {
                from: this.config.alerts.channels.email.smtp.auth.user,
                to: this.config.alerts.channels.email.recipients.join(','),
                subject: `环境监控告警: ${alert.alertType}`,
                html: this.generateEmailAlertContent(alert)
            };

            await transporter.sendMail(mailOptions);
            this.log(`📧 邮件告警已发送: ${alert.alertId}`);

        } catch (error) {
            this.log(`邮件告警发送失败: ${error.message}`);
        }
    }

    /**
     * 发送Slack告警
     */
    async sendSlackAlert(alert) {
        try {
            const slackMessage = {
                channel: this.config.alerts.channels.slack.channel,
                text: `环境监控告警: ${alert.alertType}`,
                attachments: [{
                    color: alert.isCritical ? 'danger' : 'warning',
                    fields: [
                        { title: '环境', value: alert.data.environment, short: true },
                        { title: '类型', value: alert.alertType, short: true },
                        { title: '消息', value: alert.data.message, short: false },
                        { title: '时间', value: alert.timestamp, short: true }
                    ]
                }]
            };

            await this.executeCommand(`curl -X POST -H 'Content-type: application/json' --data '${JSON.stringify(slackMessage)}' ${this.config.alerts.channels.slack.webhook}`);
            this.log(`💬 Slack告警已发送: ${alert.alertId}`);

        } catch (error) {
            this.log(`Slack告警发送失败: ${error.message}`);
        }
    }

    /**
     * 发送Webhook告警
     */
    async sendWebhookAlert(alert) {
        try {
            const webhookData = {
                alertId: alert.alertId,
                envKey: alert.envKey,
                alertType: alert.alertType,
                data: alert.data,
                isCritical: alert.isCritical,
                timestamp: alert.timestamp
            };

            const headers = this.config.alerts.channels.webhook.headers;
            const headerString = Object.entries(headers)
                .map(([key, value]) => `-H "${key}: ${value}"`)
                .join(' ');

            await this.executeCommand(`curl -X POST ${headerString} -H 'Content-type: application/json' --data '${JSON.stringify(webhookData)}' ${this.config.alerts.channels.webhook.url}`);
            this.log(`🔗 Webhook告警已发送: ${alert.alertId}`);

        } catch (error) {
            this.log(`Webhook告警发送失败: ${error.message}`);
        }
    }

    /**
     * 生成邮件告警内容
     */
    generateEmailAlertContent(alert) {
        return `
            <html>
                <body>
                    <h2>环境监控告警</h2>
                    <table border="1" cellpadding="5" cellspacing="0">
                        <tr><td><strong>告警ID</strong></td><td>${alert.alertId}</td></tr>
                        <tr><td><strong>环境</strong></td><td>${alert.data.environment}</td></tr>
                        <tr><td><strong>类型</strong></td><td>${alert.alertType}</td></tr>
                        <tr><td><strong>消息</strong></td><td>${alert.data.message}</td></tr>
                        <tr><td><strong>严重程度</strong></td><td>${alert.isCritical ? '严重' : '警告'}</td></tr>
                        <tr><td><strong>时间</strong></td><td>${alert.timestamp}</td></tr>
                    </table>
                    <p>请及时处理相关问题。</p>
                </body>
            </html>
        `;
    }

    /**
     * 检查是否在冷却期
     */
    isInCooldown(cooldownKey) {
        const cooldown = this.alertCooldowns.get(cooldownKey);
        if (!cooldown) {
            return false;
        }

        return Date.now() - cooldown < this.config.alerts.cooldown;
    }

    /**
     * 设置冷却期
     */
    setCooldown(cooldownKey) {
        this.alertCooldowns.set(cooldownKey, Date.now().catch(error => console.error(`[environment-monitoring-system.js] Date.now failed:`, error)));
    }

    /**
     * 启动指标收集
     */
    async startMetricsCollection() {
        this.log('📊 启动指标收集...');

        this.metricsTimer = setInterval(async () => {
            try {
                await this.collectAndAggregateMetrics();
            } catch (error) {
                this.log(`指标收集异常: ${error.message}`);
            }
        }, this.config.metrics.collectInterval);
    }

    /**
     * 收集和聚合指标
     */
    async collectAndAggregateMetrics() {
        const timestamp = Date.now().catch(error => console.error(`[environment-monitoring-system.js] Date.now failed:`, error));
        const aggregatedMetrics = {};

        for (const [envKey, envMetrics] of this.environmentMetrics.entries().catch(error => console.error(`[environment-monitoring-system.js] environmentMetrics.entries failed:`, error))) {
            aggregatedMetrics[envKey] = {
                timestamp,
                responseTime: this.calculateAverage(envMetrics.responseTime),
                errorRate: this.calculateAverage(envMetrics.errorRate),
                cpu: this.calculateAverage(envMetrics.cpu),
                memory: this.calculateAverage(envMetrics.memory),
                disk: this.calculateAverage(envMetrics.disk)
            };
        }

        this.metricsHistory.push(aggregatedMetrics);

        // 限制历史数据
        if (this.metricsHistory.length > 1000) {
            this.metricsHistory.splice(0, this.metricsHistory.length - 1000);
        }

        // 保存指标数据
        await this.saveMetricsData(aggregatedMetrics);
    }

    /**
     * 计算平均值
     */
    calculateAverage(metricArray) {
        if (metricArray.length === 0) {
            return 0;
        }

        const recentMetrics = metricArray.slice(-10); // 取最近10个数据点
        const sum = recentMetrics.reduce((acc, item) => acc + item.value, 0);
        return Math.round((sum / recentMetrics.length) * 100) / 100;
    }

    /**
     * 保存指标数据
     */
    async saveMetricsData(metrics) {
        try {
            const timestamp = new Date().toISOString().split('T')[0];
            const filePath = path.join('./monitoring/metrics', `metrics-${timestamp}.json`);
            
            let existingData = [];
            if (fs.existsSync(filePath)) {
                existingData = JSON.parse(fs.readFileSync(filePath, 'utf8'));
            }

            existingData.push(metrics);
            fs.writeFileSync(filePath, JSON.stringify(existingData, null, 2));

        } catch (error) {
            this.log(`保存指标数据失败: ${error.message}`);
        }
    }

    /**
     * 启动仪表板
     */
    async startDashboard() {
        const express = require('express');
        const app = express();
        const http = require('http').createServer(app);
        const io = require('socket.io')(http);

        // 静态文件服务
        app.use(express.static(path.join(__dirname, '../monitoring')));
        
        // API路由
        app.get('/api/status', (req, res) => {
            res.json(this.getEnvironmentStatus().catch(error => console.error(`[environment-monitoring-system.js] this.getEnvironmentStatus failed:`, error)));
        });

        app.get('/api/metrics', (req, res) => {
            res.json(this.getMetricsData().catch(error => console.error(`[environment-monitoring-system.js] this.getMetricsData failed:`, error)));
        });

        app.get('/api/alerts', (req, res) => {
            res.json(this.getAlertHistory().catch(error => console.error(`[environment-monitoring-system.js] this.getAlertHistory failed:`, error)));
        });

        // WebSocket连接
        io.on('connection', (socket) => {
            this.log('🔌 仪表板客户端已连接');

            // 发送实时数据
            socket.emit('status', this.getEnvironmentStatus().catch(error => console.error(`[environment-monitoring-system.js] this.getEnvironmentStatus failed:`, error)));
            socket.emit('metrics', this.getMetricsData());

            // 监听状态更新
            this.on('statusUpdate', (status) => {
                socket.emit('status', status);
            });

            this.on('alert', (alert) => {
                socket.emit('alert', alert);
            });

            socket.on('disconnect', () => {
                this.log('🔌 仪表板客户端已断开');
            });
        });

        // 启动服务器
        http.listen(this.config.dashboard.port, () => {
            this.log(`🌐 监控仪表板已启动: http://localhost:${this.config.dashboard.port}`);
        });
    }

    /**
     * 更新全局状态
     */
    updateGlobalStatus() {
        let allHealthy = true;
        let hasCriticalIssues = false;

        for (const [envKey, status] of this.environmentStatus.entries().catch(error => console.error(`[environment-monitoring-system.js] environmentStatus.entries failed:`, error))) {
            const envConfig = this.config.environments[envKey];
            
            if (status.status !== 'healthy') {
                allHealthy = false;
                
                if (envConfig.critical) {
                    hasCriticalIssues = true;
                }
            }
        }

        // 更新全局状态
        this.globalStatus = {
            overall: allHealthy ? 'healthy' : (hasCriticalIssues ? 'critical' : 'degraded'),
            timestamp: new Date().toISOString(),
            environmentCount: this.environmentStatus.size,
            healthyCount: Array.from(this.environmentStatus.values().catch(error => console.error(`[environment-monitoring-system.js] environmentStatus.values failed:`, error))).filter(s => s.status === 'healthy').length,
            activeAlerts: this.activeAlerts.size
        };
    }

    /**
     * 获取环境状态
     */
    getEnvironmentStatus() {
        const status = {};
        
        for (const [envKey, envStatus] of this.environmentStatus.entries().catch(error => console.error(`[environment-monitoring-system.js] environmentStatus.entries failed:`, error))) {
            status[envKey] = { ...envStatus };
        }

        return {
            global: this.globalStatus,
            environments: status,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 获取指标数据
     */
    getMetricsData() {
        const metrics = {};
        
        for (const [envKey, envMetrics] of this.environmentMetrics.entries().catch(error => console.error(`[environment-monitoring-system.js] environmentMetrics.entries failed:`, error))) {
            metrics[envKey] = { ...envMetrics };
        }

        return {
            current: metrics,
            history: this.metricsHistory.slice(-100),
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 获取告警历史
     */
    getAlertHistory() {
        return {
            active: Array.from(this.activeAlerts.values().catch(error => console.error(`[environment-monitoring-system.js] activeAlerts.values failed:`, error))),
            history: this.alertHistory.slice(-100),
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 加载历史数据
     */
    async loadHistoricalData() {
        try {
            // 加载告警历史
            const alertsPath = './monitoring/alerts/alert-history.json';
            if (fs.existsSync(alertsPath)) {
                this.alertHistory = JSON.parse(fs.readFileSync(alertsPath, 'utf8'));
            }

        } catch (error) {
            this.log(`加载历史数据失败: ${error.message}`);
        }
    }

    /**
     * 生成告警ID
     */
    generateAlertId() {
        return `alert_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
    }

    /**
     * 执行命令
     */
    async executeCommand(command) {
        return new Promise((resolve, reject) => {
            exec(command, { timeout: 5000 }, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    resolve({ stdout, stderr });
                }
            });
        });
    }

    /**
     * 记录日志
     */
    log(message) {
        const timestamp = new Date().toISOString();
        const logMessage = `[EnvironmentMonitoringSystem] ${timestamp} - ${message}`;
        
        console.log(logMessage);
        
        // 写入日志文件
        const logPath = path.join('./monitoring/logs', 'monitoring.log');
        fs.appendFile(logPath, logMessage + '\n', (err) => {
            if (err) {
                console.error(`[environment-monitoring-system.js] 写入日志失败:, err`);
            }
        });
    }
}

module.exports = EnvironmentMonitoringSystem;