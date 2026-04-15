// MTSCOS 统一项目管理器
// 作者: Chenghao Wu
// 版本: 2.0.0
// 功能: 整合所有保护功能、统一管理、智能协调

const fs = require('fs');
const path = require('path');
const { EventEmitter } = require('events');

// 导入各个管理器
let ProjectProtectionManager, EnhancedBackupManager, IntelligentMonitoringSystem;

try {
    ProjectProtectionManager = require('./project-protection-manager');
} catch (error) {
    console.log('警告: 无法加载项目保护管理器:', error.message);
    ProjectProtectionManager = null;
}

try {
    EnhancedBackupManager = require('./enhanced-backup-manager');
} catch (error) {
    console.log('警告: 无法加载增强备份管理器:', error.message);
    EnhancedBackupManager = null;
}

try {
    IntelligentMonitoringSystem = require('./intelligent-monitoring-system');
} catch (error) {
    console.log('警告: 无法加载智能监控系统:', error.message);
    IntelligentMonitoringSystem = null;
}

class UnifiedProjectManager extends EventEmitter {
    constructor() {
        super();
        
        this.rootDir = path.dirname(path.dirname(__filename));
        this.config = {
            // 主配置
            project: {
                name: 'MTSCOS_AI_Project',
                version: '1.3.0',
                author: 'Chenghao Wu',
                description: 'MTSCOS AI项目管理系统'
            },
            
            // 管理器配置
            managers: {
                protection: {
                    enabled: true,
                    autoStart: true
                },
                backup: {
                    enabled: true,
                    autoStart: true
                },
                monitoring: {
                    enabled: true,
                    autoStart: true
                }
            },
            
            // 协调配置
            coordination: {
                enabled: true,
                conflictResolution: 'priority', // priority, consensus, custom
                resourceSharing: true,
                eventBus: true
            },
            
            // 健康检查
            healthCheck: {
                enabled: true,
                interval: 30000, // 30秒
                criticalThreshold: 3, // 连续3次失败认为不健康
                autoRecovery: true
            },
            
            // 报告配置
            reporting: {
                enabled: true,
                interval: 3600000, // 1小时
                formats: ['json', 'html'],
                retention: 7 * 24 * 3600000 // 7天
            }
        };

        this.state = {
            isRunning: false,
            startTime: null,
            managers: {},
            health: {
                status: 'unknown',
                checks: [],
                failures: 0,
                lastCheck: null
            },
            metrics: {
                uptime: 0,
                events: 0,
                actions: 0,
                errors: 0
            },
            reports: []
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
        const logMessage = `[${timestamp}] [UNIFIED-${level.toUpperCase()}] ${message}`;
        console.log(logMessage);
        
        const logFile = path.join(this.logDir, 'unified_manager.log');
        fs.appendFileSync(logFile, logMessage + '\n');
        
        if (data) {
            fs.appendFileSync(logFile, `  Data: ${JSON.stringify(data, null, 2)}\n`);
        }
    }

    // 初始化管理器
    async initializeManagers() {
        this.log('info', '初始化管理器...');

        try {
            // 初始化保护管理器
            if (this.config.managers.protection.enabled && ProjectProtectionManager) {
                this.state.managers.protection = new ProjectProtectionManager();
                this.setupManagerEvents('protection', this.state.managers.protection);
                this.log('info', '保护管理器初始化完成');
            } else if (!ProjectProtectionManager) {
                this.log('warning', '跳过保护管理器初始化 - 模块不可用');
            }

            // 初始化备份管理器
            if (this.config.managers.backup.enabled && EnhancedBackupManager) {
                this.state.managers.backup = new EnhancedBackupManager();
                this.setupManagerEvents('backup', this.state.managers.backup);
                this.log('info', '备份管理器初始化完成');
            } else if (!EnhancedBackupManager) {
                this.log('warning', '跳过备份管理器初始化 - 模块不可用');
            }

            // 初始化监控系统
            if (this.config.managers.monitoring.enabled && IntelligentMonitoringSystem) {
                this.state.managers.monitoring = new IntelligentMonitoringSystem();
                this.setupManagerEvents('monitoring', this.state.managers.monitoring);
                this.log('info', '监控系统初始化完成');
            } else if (!IntelligentMonitoringSystem) {
                this.log('warning', '跳过监控系统初始化 - 模块不可用');
            }

        } catch (error) {
            this.log('error', '管理器初始化失败', error.message);
            throw error;
        }
    }

    // 设置管理器事件
    setupManagerEvents(managerName, manager) {
        // 检查管理器是否有事件功能
        if (typeof manager.on === 'function') {
            // 监听管理器事件
            manager.on('started', () => {
                this.log('info', `${managerName}管理器已启动`);
                this.emit('managerStarted', { manager: managerName });
            });

            manager.on('stopped', () => {
                this.log('info', `${managerName}管理器已停止`);
                this.emit('managerStopped', { manager: managerName });
            });

            manager.on('alert', (alert) => {
                this.handleManagerAlert(managerName, alert);
            });

            manager.on('error', (error) => {
                this.handleManagerError(managerName, error);
            });

            // 如果是监控系统，监听更多事件
            if (managerName === 'monitoring') {
                manager.on('alert', (alert) => {
                    this.handleMonitoringAlert(alert);
                });
            }
        } else {
            this.log('info', `${managerName}管理器不支持事件监听`);
        }
    }

    // 处理管理器报警
    handleManagerAlert(managerName, alert) {
        this.log('warning', `${managerName}管理器报警: ${alert.message}`, alert);
        
        // 协调处理报警
        if (this.config.coordination.enabled) {
            this.coordinateAlertResponse(managerName, alert);
        }

        this.state.metrics.events++;
        this.emit('managerAlert', { manager: managerName, alert });
    }

    // 处理管理器错误
    handleManagerError(managerName, error) {
        this.log('error', `${managerName}管理器错误: ${error.message}`, error);
        
        this.state.metrics.errors++;
        this.emit('managerError', { manager: managerName, error });

        // 尝试恢复
        if (this.config.healthCheck.autoRecovery) {
            this.attemptManagerRecovery(managerName, error);
        }
    }

    // 处理监控报警
    handleMonitoringAlert(alert) {
        // 根据报警类型协调其他管理器
        switch (alert.type) {
            case 'memory':
            case 'cpu':
                this.coordinatePerformanceResponse(alert);
                break;
            case 'disk':
                this.coordinateDiskResponse(alert);
                break;
            case 'service':
                this.coordinateServiceResponse(alert);
                break;
            case 'file':
                this.coordinateFileResponse(alert);
                break;
        }
    }

    // 协调报警响应
    coordinateAlertResponse(managerName, alert) {
        const responses = {
            protection: {
                'file': 'performIntegrityCheck',
                'security': 'performSecurityScan'
            },
            backup: {
                'disk': 'performBackup',
                'file': 'performBackup'
            },
            monitoring: {
                'performance': 'adjustMonitoringFrequency'
            }
        };

        const managerResponses = responses[managerName];
        if (managerResponses && managerResponses[alert.type]) {
            const action = managerResponses[alert.type];
            this.executeManagerAction(managerName, action, alert);
        }
    }

    // 协调性能响应
    coordinatePerformanceResponse(alert) {
        if (alert.level === 'critical') {
            // 通知保护管理器进行安全检查
            if (this.state.managers.protection) {
                this.executeManagerAction('protection', 'performSecurityScan', alert);
            }
            
            // 通知备份管理器进行备份
            if (this.state.managers.backup) {
                this.executeManagerAction('backup', 'performBackup', alert);
            }
        }
    }

    // 协调磁盘响应
    coordinateDiskResponse(alert) {
        if (alert.level === 'critical') {
            // 通知备份管理器清理旧备份
            if (this.state.managers.backup) {
                this.executeManagerAction('backup', 'cleanupOldBackups', alert);
            }
        }
    }

    // 协调服务响应
    coordinateServiceResponse(alert) {
        // 监控系统已经处理了服务恢复
        this.log('info', `服务报警已由监控系统处理: ${alert.service}`);
    }

    // 协调文件响应
    coordinateFileResponse(alert) {
        if (alert.changeType === 'deleted' && alert.level === 'critical') {
            // 通知备份管理器进行备份
            if (this.state.managers.backup) {
                this.executeManagerAction('backup', 'performBackup', alert);
            }
        }
    }

    // 执行管理器动作
    executeManagerAction(managerName, action, data) {
        const manager = this.state.managers[managerName];
        if (!manager) {
            this.log('warning', `管理器不存在: ${managerName}`);
            return;
        }

        try {
            this.log('info', `执行${managerName}管理器动作: ${action}`);
            
            switch (action) {
                case 'performIntegrityCheck':
                    if (manager.checkFileIntegrity) {
                        manager.checkFileIntegrity();
                    }
                    break;
                case 'performSecurityScan':
                    if (manager.performSecurityScan) {
                        manager.performSecurityScan();
                    }
                    break;
                case 'performBackup':
                    if (manager.performBackup) {
                        manager.performBackup();
                    } else if (manager.performIncrementalBackup) {
                        manager.performIncrementalBackup();
                    }
                    break;
                case 'cleanupOldBackups':
                    if (manager.cleanupOldBackups) {
                        manager.cleanupOldBackups();
                    }
                    break;
                case 'adjustMonitoringFrequency':
                    if (manager.adjustFrequency) {
                        manager.adjustFrequency('high');
                    }
                    break;
                default:
                    this.log('warning', `未知动作: ${action}`);
            }

            this.state.metrics.actions++;
            
        } catch (error) {
            this.log('error', `执行管理器动作失败: ${managerName}.${action}`, error.message);
        }
    }

    // 尝试管理器恢复
    async attemptManagerRecovery(managerName, error) {
        this.log('info', `尝试恢复${managerName}管理器`);

        try {
            const manager = this.state.managers[managerName];
            if (manager) {
                // 停止并重新启动管理器
                if (manager.stop) {
                    manager.stop();
                }
                
                // 等待一段时间
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                if (manager.start) {
                    manager.start();
                }
                
                this.log('info', `${managerName}管理器恢复成功`);
            }
        } catch (recoveryError) {
            this.log('error', `${managerName}管理器恢复失败`, recoveryError.message);
        }
    }

    // 启动统一管理器
    async start() {
        if (this.state.isRunning) {
            this.log('warning', '统一管理器已在运行');
            return;
        }

        this.log('info', '启动MTSCOS统一项目管理器...');
        this.state.isRunning = true;
        this.state.startTime = new Date();

        try {
            // 初始化管理器
            await this.initializeManagers();

            // 启动各个管理器
            for (const [managerName, manager] of Object.entries(this.state.managers)) {
                if (this.config.managers[managerName].autoStart && manager.start) {
                    manager.start();
                }
            }

            // 启动健康检查
            if (this.config.healthCheck.enabled) {
                this.startHealthCheck();
            }

            // 启动报告生成
            if (this.config.reporting.enabled) {
                this.startReporting();
            }

            this.log('info', 'MTSCOS统一项目管理器启动完成');
            this.emit('started');

        } catch (error) {
            this.state.isRunning = false;
            this.log('error', '统一管理器启动失败', error.message);
            throw error;
        }
    }

    // 停止统一管理器
    async stop() {
        if (!this.state.isRunning) {
            return;
        }

        this.log('info', '停止MTSCOS统一项目管理器...');
        this.state.isRunning = false;

        try {
            // 停止各个管理器
            for (const [managerName, manager] of Object.entries(this.state.managers)) {
                if (manager.stop) {
                    manager.stop();
                }
            }

            // 停止健康检查
            if (this.healthCheckInterval) {
                clearInterval(this.healthCheckInterval);
            }

            // 停止报告生成
            if (this.reportingInterval) {
                clearInterval(this.reportingInterval);
            }

            this.log('info', 'MTSCOS统一项目管理器已停止');
            this.emit('stopped');

        } catch (error) {
            this.log('error', '统一管理器停止失败', error.message);
        }
    }

    // 启动健康检查
    startHealthCheck() {
        this.healthCheckInterval = setInterval(() => {
            this.performHealthCheck();
        }, this.config.healthCheck.interval);

        // 立即执行一次健康检查
        this.performHealthCheck();
    }

    // 执行健康检查
    async performHealthCheck() {
        const checks = [];
        let allHealthy = true;

        // 检查各个管理器状态
        for (const [managerName, manager] of Object.entries(this.state.managers)) {
            try {
                let isHealthy = true;
                let details = {};

                if (manager.getStatus) {
                    const status = manager.getStatus();
                    isHealthy = status.uptime > 0;
                    details = status;
                } else if (manager.state && manager.state.isRunning !== undefined) {
                    isHealthy = manager.state.isRunning;
                }

                checks.push({
                    manager: managerName,
                    healthy: isHealthy,
                    details
                });

                if (!isHealthy) {
                    allHealthy = false;
                }

            } catch (error) {
                checks.push({
                    manager: managerName,
                    healthy: false,
                    error: error.message
                });
                allHealthy = false;
            }
        }

        // 更新健康状态
        this.state.health.checks = checks;
        this.state.health.lastCheck = new Date();

        if (allHealthy) {
            this.state.health.status = 'healthy';
            this.state.health.failures = 0;
        } else {
            this.state.health.failures++;
            if (this.state.health.failures >= this.config.healthCheck.criticalThreshold) {
                this.state.health.status = 'critical';
                this.log('error', '系统健康状态严重，尝试自动恢复');
                
                if (this.config.healthCheck.autoRecovery) {
                    await this.performSystemRecovery();
                }
            } else {
                this.state.health.status = 'degraded';
            }
        }

        this.emit('healthCheck', this.state.health);
    }

    // 执行系统恢复
    async performSystemRecovery() {
        this.log('info', '执行系统级恢复...');

        for (const [managerName, manager] of Object.entries(this.state.managers)) {
            try {
                if (manager.stop) {
                    manager.stop();
                }
                
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                if (manager.start) {
                    manager.start();
                }
                
                this.log('info', `${managerName}管理器恢复成功`);
            } catch (error) {
                this.log('error', `${managerName}管理器恢复失败`, error.message);
            }
        }

        this.state.health.failures = 0;
        this.state.health.status = 'healthy';
    }

    // 启动报告生成
    startReporting() {
        this.reportingInterval = setInterval(() => {
            this.generateReport();
        }, this.config.reporting.interval);

        // 立即生成一次报告
        this.generateReport();
    }

    // 生成报告
    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            project: this.config.project,
            uptime: Date.now() - this.state.startTime.getTime(),
            health: this.state.health,
            metrics: { ...this.state.metrics },
            managers: {}
        };

        // 收集各管理器状态
        for (const [managerName, manager] of Object.entries(this.state.managers)) {
            try {
                if (manager.getStatus) {
                    report.managers[managerName] = manager.getStatus();
                } else if (manager.getMonitoringStatus) {
                    report.managers[managerName] = manager.getMonitoringStatus();
                } else if (manager.getBackupStatus) {
                    report.managers[managerName] = manager.getBackupStatus();
                } else {
                    report.managers[managerName] = { status: 'unknown' };
                }
            } catch (error) {
                report.managers[managerName] = { 
                    status: 'error', 
                    error: error.message 
                };
            }
        }

        // 保存报告
        this.saveReport(report);
        
        // 清理旧报告
        this.cleanupOldReports();

        this.state.reports.push(report);
        this.log('info', '系统报告已生成');
        this.emit('report', report);
    }

    // 保存报告
    saveReport(report) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        
        // 保存JSON格式
        const jsonFile = path.join(this.logDir, `report_${timestamp}.json`);
        fs.writeFileSync(jsonFile, JSON.stringify(report, null, 2));

        // 保存HTML格式
        if (this.config.reporting.formats.includes('html')) {
            const htmlFile = path.join(this.logDir, `report_${timestamp}.html`);
            const htmlContent = this.generateHTMLReport(report);
            fs.writeFileSync(htmlFile, htmlContent);
        }
    }

    // 生成HTML报告
    generateHTMLReport(report) {
        return `
<!DOCTYPE html>
<html>
<head>
    <title>MTSCOS 系统报告 - ${report.timestamp}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .healthy { color: green; }
        .degraded { color: orange; }
        .critical { color: red; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>MTSCOS 系统报告</h1>
        <p>项目: ${report.project.name}</p>
        <p>版本: ${report.project.version}</p>
        <p>生成时间: ${report.timestamp}</p>
        <p>运行时间: ${Math.floor(report.uptime / 1000 / 60)} 分钟</p>
    </div>

    <div class="section">
        <h2>系统健康状态</h2>
        <p class="${report.health.status}">状态: ${report.health.status}</p>
        <p>检查次数: ${report.health.checks.length}</p>
        <p>失败次数: ${report.health.failures}</p>
        <p>最后检查: ${report.health.lastCheck}</p>
    </div>

    <div class="section">
        <h2>系统指标</h2>
        <p>事件数: ${report.metrics.events}</p>
        <p>动作数: ${report.metrics.actions}</p>
        <p>错误数: ${report.metrics.errors}</p>
    </div>

    <div class="section">
        <h2>管理器状态</h2>
        <table>
            <tr><th>管理器</th><th>状态</th><th>详情</th></tr>
            ${Object.entries(report.managers).map(([name, status]) => 
                `<tr>
                    <td>${name}</td>
                    <td>${status.status || 'unknown'}</td>
                    <td>${JSON.stringify(status).substring(0, 100)}...</td>
                </tr>`
            ).join('')}
        </table>
    </div>
</body>
</html>`;
    }

    // 清理旧报告
    cleanupOldReports() {
        const cutoff = Date.now() - this.config.reporting.retention;
        
        this.state.reports = this.state.reports.filter(report => {
            const reportTime = new Date(report.timestamp).getTime();
            return reportTime > cutoff;
        });
    }

    // 获取统一状态
    getUnifiedStatus() {
        return {
            isRunning: this.state.isRunning,
            startTime: this.state.startTime,
            uptime: this.state.isRunning ? Date.now() - this.state.startTime.getTime() : 0,
            health: this.state.health,
            metrics: { ...this.state.metrics },
            managers: Object.keys(this.state.managers),
            config: this.config
        };
    }

    // 获取详细状态
    getDetailedStatus() {
        const status = this.getUnifiedStatus();
        
        // 添加各管理器的详细状态
        status.managerDetails = {};
        for (const [managerName, manager] of Object.entries(this.state.managers)) {
            try {
                if (manager.getStatus) {
                    status.managerDetails[managerName] = manager.getStatus();
                } else if (manager.getMonitoringStatus) {
                    status.managerDetails[managerName] = manager.getMonitoringStatus();
                } else if (manager.getBackupStatus) {
                    status.managerDetails[managerName] = manager.getBackupStatus();
                } else {
                    status.managerDetails[managerName] = { status: 'available' };
                }
            } catch (error) {
                status.managerDetails[managerName] = { 
                    status: 'error', 
                    error: error.message 
                };
            }
        }

        return status;
    }
}

// 创建并导出统一管理器
const unifiedManager = new UnifiedProjectManager();

module.exports = UnifiedProjectManager;

// 如果直接运行此脚本，启动统一管理器
if (require.main === module) {
    unifiedManager.start().catch(error => {
        console.error('启动统一管理器失败:', error);
        process.exit(1);
    });
    
    process.on('SIGINT', async () => {
        await unifiedManager.stop();
        process.exit(0);
    });
    
    process.on('SIGTERM', async () => {
        await unifiedManager.stop();
        process.exit(0);
    });
}

console.log('[MTSCOS] 统一项目管理器已加载');