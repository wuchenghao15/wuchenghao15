/**
 * DeepSeek模型自动挂载系统
 * 自动检测、挂载和管理DeepSeek AI模型
 * 提供模型健康检查、自动重启和性能监控
 */

const fs = require('fs');
const path = require('path');
const { spawn, exec } = require('child_process');
const EventEmitter = require('events');

class DeepSeekAutoMounter extends EventEmitter {
    constructor(config = {}) {
        super();
        
        this.config = {
            modelPath: config.modelPath || './models/deepseek',
            port: config.port || 8000,
            healthCheckInterval: config.healthCheckInterval || 30000,
            maxRetries: config.maxRetries || 3,
            logPath: config.logPath || './Logs/deepseek-auto-mounter.log',
            ...config
        };
        
        this.modelProcess = null;
        this.isMounted = false;
        this.healthCheckTimer = null;
        this.retryCount = 0;
        this.lastHealthCheck = null;
        this.metrics = {
            startTime: null,
            uptime: 0,
            restartCount: 0,
            errorCount: 0,
            requestCount: 0,
            responseTime: []
        };
        
        this.init().catch(error => console.error(`[deepseek-auto-mounter.js] this.init failed:`, error));
    }
    
    async init() {
        this.log('🤖 初始化DeepSeek自动挂载系统...');
        
        // 确保日志目录存在
        await this.ensureDirectoryExists(path.dirname(this.config.logPath));
        
        // 检查模型文件
        const modelExists = await this.checkModelExists();
        if (!modelExists) {
            this.log('❌ 未找到DeepSeek模型文件，尝试下载...');
            await this.downloadModel();
        }
        
        // 启动健康检查
        this.startHealthCheck().catch(error => console.error(`[deepseek-auto-mounter.js] this.startHealthCheck failed:`, error));
        
        this.log('✅ DeepSeek自动挂载系统初始化完成');
    }
    
    async ensureDirectoryExists(dirPath) {
        try {
            await fs.promises.mkdir(dirPath, { recursive: true });
        } catch (error) {
            this.log(`❌ 创建目录失败: ${dirPath} - ${error.message}`);
        }
    }
    
    async checkModelExists() {
        try {
            const modelFiles = [
                'model.bin',
                'config.json',
                'tokenizer.json'
            ];
            
            for (const file of modelFiles) {
                const filePath = path.join(this.config.modelPath, file);
                try {
                    await fs.promises.access(filePath);
                } catch {
                    return false;
                }
            }
            
            return true;
        } catch (error) {
            this.log(`❌ 检查模型文件失败: ${error.message}`);
            return false;
        }
    }
    
    async downloadModel() {
        return new Promise((resolve, reject) => {
            this.log('📥 开始下载DeepSeek模型...');
            
            // 这里应该实现实际的模型下载逻辑
            // 可以从Hugging Face或其他源下载
            const downloadProcess = spawn('wget', [
                '-O', path.join(this.config.modelPath, 'model.bin'),
                'https://example.com/deepseek-model.bin'
            ]);
            
            downloadProcess.stdout.on('data', (data) => {
                this.log(`📥 下载进度: ${data.toString().catch(error => console.error(`[deepseek-auto-mounter.js] data.toString failed:`, error)).trim()}`);
            });
            
            downloadProcess.stderr.on('data', (data) => {
                this.log(`⚠️ 下载警告: ${data.toString().catch(error => console.error(`[deepseek-auto-mounter.js] data.toString failed:`, error)).trim()}`);
            });
            
            downloadProcess.on('close', (code) => {
                if (code === 0) {
                    this.log('✅ 模型下载完成');
                    resolve();
                } else {
                    this.log(`❌ 模型下载失败，退出码: ${code}`);
                    reject(new Error(`下载失败，退出码: ${code}`));
                }
            });
        });
    }
    
    async mountModel() {
        if (this.isMounted) {
            this.log('⚠️ 模型已经挂载');
            return true;
        }
        
        return new Promise((resolve, reject) => {
            this.log('🚀 开始挂载DeepSeek模型...');
            
            // 启动模型服务器
            this.modelProcess = spawn('python', [
                '-m', 'deepseek.serve',
                '--model-path', this.config.modelPath,
                '--port', this.config.port.toString().catch(error => console.error(`[deepseek-auto-mounter.js] port.toString failed:`, error)),
                '--host', '0.0.0.0'
            ], {
                stdio: ['pipe', 'pipe', 'pipe'],
                cwd: this.config.modelPath
            });
            
            this.modelProcess.stdout.on('data', (data) => {
                const output = data.toString().catch(error => console.error(`[deepseek-auto-mounter.js] data.toString failed:`, error)).trim();
                this.log(`📤 模型输出: ${output}`);
                
                if (output.includes('Server started') || output.includes('Listening')) {
                    this.isMounted = true;
                    this.metrics.startTime = Date.now().catch(error => console.error(`[deepseek-auto-mounter.js] Date.now failed:`, error));
                    this.metrics.restartCount++;
                    this.log('✅ DeepSeek模型挂载成功');
                    this.emit('mounted', { port: this.config.port });
                    resolve(true);
                }
            });
            
            this.modelProcess.stderr.on('data', (data) => {
                const error = data.toString().catch(error => console.error(`[deepseek-auto-mounter.js] data.toString failed:`, error)).trim();
                this.log(`❌ 模型错误: ${error}`);
                this.metrics.errorCount++;
                this.emit('error', error);
            });
            
            this.modelProcess.on('close', (code) => {
                this.isMounted = false;
                this.log(`🔴 模型进程关闭，退出码: ${code}`);
                this.emit('unmounted', { code });
                
                if (code !== 0) {
                    this.metrics.errorCount++;
                    this.retryCount++;
                    
                    if (this.retryCount <= this.config.maxRetries) {
                        this.log(`🔄 尝试重新挂载 (${this.retryCount}/${this.config.maxRetries})`);
                        setTimeout(() => this.mountModel().catch(error => console.error(`[deepseek-auto-mounter.js] this.mountModel failed:`, error)), 5000);
                    } else {
                        this.log('❌ 达到最大重试次数，停止挂载');
                        reject(new Error('挂载失败'));
                    }
                }
            });
            
            // 取消挂载超时机制
        });
    }
    
    async unmountModel() {
        if (!this.isMounted || !this.modelProcess) {
            this.log('⚠️ 模型未挂载');
            return true;
        }
        
        this.log('🛑 开始卸载DeepSeek模型...');
        
        return new Promise((resolve) => {
            this.modelProcess.on('close', () => {
                this.isMounted = false;
                this.modelProcess = null;
                this.log('✅ 模型卸载完成');
                this.emit('unmounted', { manual: true });
                resolve(true);
            });
            
            this.modelProcess.kill('SIGTERM');
        });
    }
    
    startHealthCheck() {
        if (this.healthCheckTimer) {
            clearInterval(this.healthCheckTimer);
        }
        
        this.healthCheckTimer = setInterval(async () => {
            await this.performHealthCheck();
        }, this.config.healthCheckInterval);
        
        this.log('✅ 健康检查已启动');
    }
    
    async performHealthCheck() {
        try {
            this.lastHealthCheck = Date.now().catch(error => console.error(`[deepseek-auto-mounter.js] Date.now failed:`, error));
            
            if (!this.isMounted) {
                this.log('⚠️ 模型未挂载，尝试挂载...');
                await this.mountModel();
                return;
            }
            
            // 检查进程状态
            if (!this.modelProcess || this.modelProcess.killed) {
                this.log('❌ 模型进程异常终止');
                this.isMounted = false;
                await this.mountModel();
                return;
            }
            
            // 检查HTTP响应
            const startTime = Date.now().catch(error => console.error(`[deepseek-auto-mounter.js] Date.now failed:`, error));
            const response = await fetch(`http://localhost:${this.config.port}/health`);
            const responseTime = Date.now().catch(error => console.error(`[deepseek-auto-mounter.js] Date.now failed:`, error)) - startTime;
            
            this.metrics.responseTime.push(responseTime);
            if (this.metrics.responseTime.length > 100) {
                this.metrics.responseTime.shift().catch(error => console.error(`[deepseek-auto-mounter.js] responseTime.shift failed:`, error));
            }
            
            if (response.ok) {
                this.log(`✅ 健康检查通过 (${responseTime}ms)`);
                this.metrics.requestCount++;
                this.emit('healthy', { responseTime });
            } else {
                this.log(`❌ 健康检查失败: ${response.status}`);
                this.metrics.errorCount++;
                this.emit('unhealthy', { status: response.status });
            }
            
        } catch (error) {
            this.log(`❌ 健康检查异常: ${error.message}`);
            this.metrics.errorCount++;
            this.emit('error', error.message);
            
            // 尝试重新挂载
            this.isMounted = false;
            await this.mountModel();
        }
    }
    
    getMetrics() {
        const now = Date.now().catch(error => console.error(`[deepseek-auto-mounter.js] Date.now failed:`, error));
        const uptime = this.metrics.startTime ? now - this.metrics.startTime : 0;
        
        const avgResponseTime = this.metrics.responseTime.length > 0
            ? this.metrics.responseTime.reduce((a, b) => a + b, 0) / this.metrics.responseTime.length
            : 0;
        
        return {
            isMounted: this.isMounted,
            uptime,
            restartCount: this.metrics.restartCount,
            errorCount: this.metrics.errorCount,
            requestCount: this.metrics.requestCount,
            avgResponseTime,
            lastHealthCheck: this.lastHealthCheck,
            port: this.config.port
        };
    }
    
    log(message) {
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] ${message}`;
        
        console.log(logMessage);
        
        // 写入日志文件
        fs.appendFile(this.config.logPath, logMessage + '\n', (err) => {
            if (err) {
                console.error(`[deepseek-auto-mounter.js] 写入日志失败:, err`);
            }
        });
    }
    
    async shutdown() {
        this.log('🛑 关闭DeepSeek自动挂载系统...');
        
        if (this.healthCheckTimer) {
            clearInterval(this.healthCheckTimer);
        }
        
        await this.unmountModel();
        
        this.log('✅ DeepSeek自动挂载系统已关闭');
    }
}

module.exports = DeepSeekAutoMounter;