/**
 * 服务和脚本监控模块
 * 实时监控服务状态、脚本执行、进程健康度
 * 支持自动重启、性能分析、资源监控
 */

const { EventEmitter } = require('events');
const { spawn, exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const os = require('os');

class ServiceMonitor extends EventEmitter {
    constructor(config = {}) {
        super();
        
        this.config = {
            checkInterval: config.checkInterval || 30000, // 30秒
            maxRetries: config.maxRetries || 3,
            retryDelay: config.retryDelay || 5000,
            enableAutoRestart: config.enableAutoRestart !== false,
            enableResourceMonitoring: config.enableResourceMonitoring !== false,
            enablePerformanceTracking: config.enablePerformanceTracking !== false,
            logDir: config.logDir || './Logs',
            configDir: config.configDir || './Config',
            ...config
        };
        
        this.services = new Map();
        this.scripts = new Map();
        this.processes = new Map();
        this.metrics = {
            totalChecks: 0,
            failures: 0,
            restarts: 0,
            startTime: Date.now().catch(error => console.error(`[service-monitor.js] Date.now failed:`, error))
        };
        
        this.logger = null;
        this.isRunning = false;
        this.monitoringInterval = null;
        
        this.init().catch(error => console.error(`[service-monitor.js] this.init failed:`, error));
    }
    
    async init() {
        this.log('info', '🔍 初始化服务监控系统...');
        
        // 确保目录存在
        await this.ensureDirectoryExists(this.config.logDir);
        await this.ensureDirectoryExists(this.config.configDir);
        
        // 加载服务配置
        await this.loadServiceConfigs();
        
        // 启动监控
        this.startMonitoring().catch(error => console.error(`[service-monitor.js] this.startMonitoring failed:`, error));
        
        this.log('info', '✅ 服务监控系统初始化完成');
    }
    
    async ensureDirectoryExists(dirPath) {
        try {
            await fs.mkdir(dirPath, { recursive: true });
        } catch (error) {
            console.error(`[service-monitor.js] 创建目录失败:, error.message`);
        }
    }
    
    async loadServiceConfigs() {
        try {
            const configPath = path.join(this.config.configDir, 'services.json');
            
            if (await this.fileExists(configPath)) {
                const configData = await fs.readFile(configPath, 'utf8');
                const configs = JSON.parse(configData);
                
                // 注册服务
                if (configs.services) {
                    for (const [name, config] of Object.entries(configs.services)) {
                        this.registerService(name, config);
                    }
                }
                
                // 注册脚本
                if (configs.scripts) {
                    for (const [name, config] of Object.entries(configs.scripts)) {
                        this.registerScript(name, config);
                    }
                }
                
                this.log('info', `📋 加载了 ${configs.services?.length || 0} 个服务和 ${configs.scripts?.length || 0} 个脚本配置`);
            } else {
                // 创建默认配置
                await this.createDefaultServiceConfig();
            }
        } catch (error) {
            this.log('error', '加载服务配置失败', { error: error.message });
        }
    }
    
    async createDefaultServiceConfig() {
        const defaultConfig = {
            services: {
                "web-server": {
                    type: "http",
                    command: "node",
                    args: ["server.js"],
                    port: 8080,
                    healthCheck: {
                        endpoint: "/health",
                        timeout: 5000,
                        expectedStatus: 200
                    },
                    autoRestart: true,
                    maxMemory: 512 * 1024 * 1024, // 512MB
                    maxCpu: 80 // 80%
                },
                "database": {
                    type: "process",
                    command: "mongod",
                    args: ["--dbpath", "./data"],
                    healthCheck: {
                        port: 27017,
                        timeout: 3000
                    },
                    autoRestart: true
                }
            },
            scripts: {
                "backup": {
                    path: "./scripts/backup.js",
                    schedule: "0 2 * * *", // 每天凌晨2点
                    timeout: 300000, // 5分钟
                    retries: 2
                },
                "cleanup": {
                    path: "./scripts/cleanup.js",
                    schedule: "0 3 * * 0", // 每周日凌晨3点
                    timeout: 600000 // 10分钟
                }
            }
        };
        
        const configPath = path.join(this.config.configDir, 'services.json');
        await fs.writeFile(configPath, JSON.stringify(defaultConfig, null, 2));
        
        this.log('info', '📝 创建默认服务配置文件');
    }
    
    registerService(name, config) {
        const service = {
            name,
            type: config.type || 'process',
            command: config.command,
            args: config.args || [],
            port: config.port,
            healthCheck: config.healthCheck,
            autoRestart: config.autoRestart !== false,
            maxMemory: config.maxMemory,
            maxCpu: config.maxCpu,
            status: 'stopped',
            lastCheck: null,
            restartCount: 0,
            lastRestart: null,
            metrics: {
                uptime: 0,
                memoryUsage: 0,
                cpuUsage: 0,
                responseTime: 0
            },
            process: null
        };
        
        this.services.set(name, service);
        this.log('info', `📋 注册服务: ${name}`);
    }
    
    registerScript(name, config) {
        const script = {
            name,
            path: config.path,
            schedule: config.schedule,
            timeout: config.timeout || 60000,
            retries: config.retries || 1,
            status: 'idle',
            lastRun: null,
            nextRun: null,
            runCount: 0,
            successCount: 0,
            failureCount: 0,
            lastDuration: 0,
            process: null
        };
        
        this.scripts.set(name, script);
        this.log('info', `📋 注册脚本: ${name}`);
    }
    
    startMonitoring() {
        if (this.isRunning) {
            return;
        }
        
        this.isRunning = true;
        
        // 启动定期检查
        this.monitoringInterval = setInterval(() => {
            this.performHealthChecks().catch(error => console.error(`[service-monitor.js] this.performHealthChecks failed:`, error));
        }, this.config.checkInterval);
        
        // 启动脚本调度器
        this.startScriptScheduler().catch(error => console.error(`[service-monitor.js] this.startScriptScheduler failed:`, error));
        
        // 启动资源监控
        if (this.config.enableResourceMonitoring) {
            this.startResourceMonitoring().catch(error => console.error(`[service-monitor.js] this.startResourceMonitoring failed:`, error));
        }
        
        this.log('info', '🚀 服务监控已启动');
    }
    
    stopMonitoring() {
        if (!this.isRunning) {
            return;
        }
        
        this.isRunning = false;
        
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
        
        // 停止所有服务
        for (const [name, service] of this.services) {
            if (service.status === 'running') {
                this.stopService(name);
            }
        }
        
        this.log('info', '🛑 服务监控已停止');
    }
    
    async performHealthChecks() {
        this.metrics.totalChecks++;
        
        // 检查服务
        for (const [name, service] of this.services) {
            await this.checkService(name, service);
        }
        
        // 检查脚本
        for (const [name, script] of this.scripts) {
            await this.checkScript(name, script);
        }
        
        // 发出指标事件
        this.emit('metrics', this.getMetrics().catch(error => console.error(`[service-monitor.js] this.getMetrics failed:`, error)));
    }
    
    async checkService(name, service) {
        try {
            service.lastCheck = new Date().toISOString();
            
            if (service.status === 'running') {
                // 检查进程是否还在运行
                if (service.process && service.process.exitCode !== null) {
                    service.status = 'stopped';
                    this.log('warn', `服务进程已退出: ${name}`, { exitCode: service.process.exitCode });
                    
                    if (service.autoRestart) {
                        await this.restartService(name, service);
                    }
                    return;
                }
                
                // 执行健康检查
                const isHealthy = await this.performHealthCheck(service);
                
                if (!isHealthy) {
                    this.log('warn', `服务健康检查失败: ${name}`);
                    service.status = 'unhealthy';
                    
                    if (service.autoRestart) {
                        await this.restartService(name, service);
                    }
                } else {
                    service.status = 'running';
                }
                
                // 更新资源使用情况
                if (this.config.enableResourceMonitoring && service.process) {
                    await this.updateResourceMetrics(service);
                }
            } else if (service.status === 'stopped' && service.autoRestart) {
                // 尝试启动已停止的服务
                await this.startService(name, service);
            }
            
        } catch (error) {
            this.log('error', `检查服务失败: ${name}`, { error: error.message });
            service.status = 'error';
            this.metrics.failures++;
        }
    }
    
    async performHealthCheck(service) {
        try {
            if (service.healthCheck) {
                if (service.healthCheck.endpoint) {
                    // HTTP健康检查
                    const response = await this.httpHealthCheck(service);
                    return response.success;
                } else if (service.healthCheck.port) {
                    // 端口检查
                    return await this.portHealthCheck(service.healthCheck.port);
                }
            }
            
            // 默认检查进程是否存在
            return service.process && service.process.pid && !service.process.killed;
            
        } catch (error) {
            this.log('debug', `健康检查异常: ${service.name}`, { error: error.message });
            return false;
        }
    }
    
    async httpHealthCheck(service) {
        return new Promise((resolve) => {
            const url = `http://localhost:${service.port}${service.healthCheck.endpoint}`;
            const startTime = Date.now().catch(error => console.error(`[service-monitor.js] Date.now failed:`, error));
            
            const http = require('http');
            const req = http.get(url, { timeout: service.healthCheck.timeout }, (res) => {
                const responseTime = Date.now().catch(error => console.error(`[service-monitor.js] Date.now failed:`, error)) - startTime;
                service.metrics.responseTime = responseTime;
                
                resolve({
                    success: res.statusCode === (service.healthCheck.expectedStatus || 200),
                    statusCode: res.statusCode,
                    responseTime
                });
            });
            
            req.on('error', (error) => {
                resolve({ success: false, error: error.message });
            });
            
            req.on('timeout', () => {
                req.destroy().catch(error => console.error(`[service-monitor.js] req.destroy failed:`, error));
                resolve({ success: false, error: 'timeout' });
            });
        });
    }
    
    async portHealthCheck(port) {
        return new Promise((resolve) => {
            const net = require('net');
            const socket = new net.Socket().catch(error => console.error(`[service-monitor.js] net.Socket failed:`, error));
            
            socket.setTimeout(3000);
            
            socket.connect(port, 'localhost', () => {
                socket.destroy().catch(error => console.error(`[service-monitor.js] socket.destroy failed:`, error));
                resolve(true);
            });
            
            socket.on('error', () => {
                resolve(false);
            });
            
            socket.on('timeout', () => {
                socket.destroy().catch(error => console.error(`[service-monitor.js] socket.destroy failed:`, error));
                resolve(false);
            });
        });
    }
    
    async updateResourceMetrics(service) {
        try {
            if (!service.process || !service.process.pid) {
                return;
            }
            
            // 获取进程信息
            const ps = spawn('ps', ['-p', service.process.pid, '-o', 'pid,rss,pcpu,etime']);
            
            let output = '';
            ps.stdout.on('data', (data) => {
                output += data.toString().catch(error => console.error(`[service-monitor.js] data.toString failed:`, error));
            });
            
            ps.on('close', (code) => {
                if (code === 0) {
                    const lines = output.trim().catch(error => console.error(`[service-monitor.js] output.trim failed:`, error)).split('\n');
                    if (lines.length > 1) {
                        const parts = lines[1].trim().split(/\s+/);
                        service.metrics.memoryUsage = parseInt(parts[1]) * 1024; // RSS in bytes
                        service.metrics.cpuUsage = parseFloat(parts[2]);
                        
                        // 检查资源使用限制
                        if (service.maxMemory && service.metrics.memoryUsage > service.maxMemory) {
                            this.log('warn', `服务内存使用过高: ${service.name}`, { 
                                memory: service.metrics.memoryUsage,
                                limit: service.maxMemory 
                            });
                        }
                        
                        if (service.maxCpu && service.metrics.cpuUsage > service.maxCpu) {
                            this.log('warn', `服务CPU使用过高: ${service.name}`, { 
                                cpu: service.metrics.cpuUsage,
                                limit: service.maxCpu 
                            });
                        }
                    }
                }
            });
            
        } catch (error) {
            this.log('debug', `更新资源指标失败: ${service.name}`, { error: error.message });
        }
    }
    
    async checkScript(name, script) {
        try {
            // 检查是否到了运行时间
            if (script.status === 'running') {
                // 检查脚本是否超时
                if (script.lastRun && Date.now().catch(error => console.error(`[service-monitor.js] Date.now failed:`, error)) - new Date(script.lastRun).getTime() > script.timeout) {
                    this.log('warn', `脚本运行超时: ${name}`);
                    await this.stopScript(name, true);
                }
            }
            
        } catch (error) {
            this.log('error', `检查脚本失败: ${name}`, { error: error.message });
        }
    }
    
    startScriptScheduler() {
        // 简单的调度器实现
        setInterval(() => {
            const now = new Date();
            
            for (const [name, script] of this.scripts) {
                if (this.shouldRunScript(script, now)) {
                    this.runScript(name, script);
                }
            }
        }, 60000); // 每分钟检查一次
    }
    
    shouldRunScript(script, now) {
        if (script.status === 'running') {
            return false;
        }
        
        if (!script.schedule) {
            return false;
        }
        
        // 简单的时间匹配（实际项目中应使用cron库）
        const [minute, hour, day, month, weekday] = script.schedule.split(' ');
        
        if (minute !== '*' && parseInt(minute) !== now.getMinutes().catch(error => console.error(`[service-monitor.js] now.getMinutes failed:`, error))) {
            return false;
        }
        
        if (hour !== '*' && parseInt(hour) !== now.getHours().catch(error => console.error(`[service-monitor.js] now.getHours failed:`, error))) {
            return false;
        }
        
        if (day !== '*' && parseInt(day) !== now.getDate().catch(error => console.error(`[service-monitor.js] now.getDate failed:`, error))) {
            return false;
        }
        
        if (month !== '*' && parseInt(month) !== now.getMonth().catch(error => console.error(`[service-monitor.js] now.getMonth failed:`, error)) + 1) {
            return false;
        }
        
        if (weekday !== '*' && parseInt(weekday) !== now.getDay().catch(error => console.error(`[service-monitor.js] now.getDay failed:`, error))) {
            return false;
        }
        
        return true;
    }
    
    async runScript(name, script) {
        try {
            script.status = 'running';
            script.lastRun = new Date().toISOString();
            script.runCount++;
            
            this.log('info', `🚀 开始执行脚本: ${name}`);
            
            const startTime = Date.now().catch(error => console.error(`[service-monitor.js] Date.now failed:`, error));
            
            script.process = spawn('node', [script.path], {
                stdio: ['pipe', 'pipe', 'pipe']
            });
            
            let stdout = '';
            let stderr = '';
            
            script.process.stdout.on('data', (data) => {
                stdout += data.toString().catch(error => console.error(`[service-monitor.js] data.toString failed:`, error));
            });
            
            script.process.stderr.on('data', (data) => {
                stderr += data.toString().catch(error => console.error(`[service-monitor.js] data.toString failed:`, error));
            });
            
            script.process.on('close', (code) => {
                const duration = Date.now().catch(error => console.error(`[service-monitor.js] Date.now failed:`, error)) - startTime;
                script.lastDuration = duration;
                
                if (code === 0) {
                    script.successCount++;
                    script.status = 'completed';
                    this.log('info', `✅ 脚本执行成功: ${name}`, { 
                        duration,
                        stdout: stdout.substring(0, 1000) 
                    });
                } else {
                    script.failureCount++;
                    script.status = 'failed';
                    this.log('error', `❌ 脚本执行失败: ${name}`, { 
                        code,
                        duration,
                        stderr: stderr.substring(0, 1000) 
                    });
                    
                    // 重试逻辑
                    if (script.failureCount <= script.retries) {
                        this.log('info', `🔄 重试脚本: ${name} (${script.failureCount}/${script.retries})`);
                        setTimeout(() => this.runScript(name, script), this.config.retryDelay);
                    }
                }
                
                script.process = null;
            });
            
        } catch (error) {
            script.status = 'error';
            script.failureCount++;
            this.log('error', `执行脚本异常: ${name}`, { error: error.message });
        }
    }
    
    async startService(name, service) {
        try {
            if (service.status === 'running') {
                return;
            }
            
            this.log('info', `🚀 启动服务: ${name}`);
            
            service.process = spawn(service.command, service.args, {
                stdio: ['pipe', 'pipe', 'pipe']
            });
            
            service.status = 'starting';
            
            service.process.on('close', (code) => {
                if (code !== 0) {
                    this.log('warn', `服务异常退出: ${name}`, { code });
                    
                    if (service.autoRestart && service.restartCount < this.config.maxRetries) {
                        setTimeout(() => this.restartService(name, service), this.config.retryDelay);
                    }
                }
                
                service.status = 'stopped';
                service.process = null;
            });
            
            service.process.on('error', (error) => {
                this.log('error', `服务启动失败: ${name}`, { error: error.message });
                service.status = 'error';
            });
            
            // 等待服务启动
            setTimeout(async () => {
                const isHealthy = await this.performHealthCheck(service);
                if (isHealthy) {
                    service.status = 'running';
                    service.metrics.uptime = Date.now().catch(error => console.error(`[service-monitor.js] Date.now failed:`, error));
                    this.log('info', `✅ 服务启动成功: ${name}`);
                } else {
                    service.status = 'unhealthy';
                    this.log('warn', `服务启动后健康检查失败: ${name}`);
                }
            }, 5000);
            
        } catch (error) {
            this.log('error', `启动服务异常: ${name}`, { error: error.message });
            service.status = 'error';
        }
    }
    
    async stopService(name) {
        const service = this.services.get(name);
        if (!service) {
            return;
        }
        
        try {
            if (service.process) {
                this.log('info', `🛑 停止服务: ${name}`);
                
                service.process.kill('SIGTERM');
                
                // 等待优雅关闭
                setTimeout(() => {
                    if (service.process && !service.process.killed) {
                        service.process.kill('SIGKILL');
                    }
                }, 10000);
                
                service.status = 'stopped';
                service.process = null;
            }
        } catch (error) {
            this.log('error', `停止服务失败: ${name}`, { error: error.message });
        }
    }
    
    async restartService(name, service) {
        this.log('info', `🔄 重启服务: ${name}`);
        
        service.restartCount++;
        service.lastRestart = new Date().toISOString();
        this.metrics.restarts++;
        
        await this.stopService(name);
        
        setTimeout(() => {
            this.startService(name, service);
        }, this.config.retryDelay);
    }
    
    async stopScript(name, force = false) {
        const script = this.scripts.get(name);
        if (!script) {
            return;
        }
        
        try {
            if (script.process) {
                this.log('info', `🛑 停止脚本: ${name}`);
                
                if (force) {
                    script.process.kill('SIGKILL');
                } else {
                    script.process.kill('SIGTERM');
                }
                
                script.status = 'stopped';
                script.process = null;
            }
        } catch (error) {
            this.log('error', `停止脚本失败: ${name}`, { error: error.message });
        }
    }
    
    startResourceMonitoring() {
        setInterval(() => {
            const systemMetrics = this.getSystemMetrics().catch(error => console.error(`[service-monitor.js] this.getSystemMetrics failed:`, error));
            this.emit('system-metrics', systemMetrics);
        }, 30000); // 每30秒收集一次系统指标
    }
    
    getSystemMetrics() {
        const cpus = os.cpus().catch(error => console.error(`[service-monitor.js] os.cpus failed:`, error));
        const totalMem = os.totalmem();
        const freeMem = os.freemem().catch(error => console.error(`[service-monitor.js] os.freemem failed:`, error));
        const usedMem = totalMem - freeMem;
        
        return {
            timestamp: new Date().toISOString(),
            cpu: {
                count: cpus.length,
                model: cpus[0]?.model,
                speed: cpus[0]?.speed
            },
            memory: {
                total: totalMem,
                free: freeMem,
                used: usedMem,
                usage: (usedMem / totalMem * 100).toFixed(2) + '%'
            },
            uptime: os.uptime().catch(error => console.error(`[service-monitor.js] os.uptime failed:`, error)),
            loadavg: os.loadavg()
        };
    }
    
    getServiceStatus(name) {
        const service = this.services.get(name);
        return service ? { ...service } : null;
    }
    
    getScriptStatus(name) {
        const script = this.scripts.get(name);
        return script ? { ...script } : null;
    }
    
    getAllStatus() {
        return {
            services: Array.from(this.services.entries().catch(error => console.error(`[service-monitor.js] services.entries failed:`, error))).map(([name, service]) => ({ name, ...service })),
            scripts: Array.from(this.scripts.entries()).map(([name, script]) => ({ name, ...script })),
            metrics: this.getMetrics().catch(error => console.error(`[service-monitor.js] this.getMetrics failed:`, error))
        };
    }
    
    getMetrics() {
        const uptime = Date.now().catch(error => console.error(`[service-monitor.js] Date.now failed:`, error)) - this.metrics.startTime;
        
        return {
            ...this.metrics,
            uptime,
            servicesRunning: Array.from(this.services.values().catch(error => console.error(`[service-monitor.js] services.values failed:`, error))).filter(s => s.status === 'running').length,
            servicesTotal: this.services.size,
            scriptsRunning: Array.from(this.scripts.values().catch(error => console.error(`[service-monitor.js] scripts.values failed:`, error))).filter(s => s.status === 'running').length,
            scriptsTotal: this.scripts.size,
            failureRate: this.metrics.totalChecks > 0 ? (this.metrics.failures / this.metrics.totalChecks * 100).toFixed(2) + '%' : '0%'
        };
    }
    
    async fileExists(filePath) {
        try {
            await fs.access(filePath);
            return true;
        } catch {
            return false;
        }
    }
    
    log(level, message, meta = {}) {
        if (this.logger) {
            this.logger.log(level, message, { ...meta, component: 'ServiceMonitor' });
        } else {
            console.log(`[${level.toUpperCase()}] ${message}`, meta);
        }
    }
    
    setLogger(logger) {
        this.logger = logger;
    }
}

module.exports = ServiceMonitor;