#!/usr/bin/env node

/**
 * MTSCOS AI Project - DeepSeek 引擎集成模块
 * 负责与DeepSeek API的交互和本地项目引擎的集成
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');
const { createLogger, transports, format } = require('winston');

// 获取项目根目录
const PROJECT_DIR = path.resolve(__dirname, '../../');

// 配置日志
const logger = createLogger({
    level: 'info',
    format: format.combine(
        format.timestamp({
            format: 'YYYY-MM-DD HH:mm:ss'
        }),
        format.printf(info => `${info.timestamp} [${info.level.toUpperCase()}] ${info.message}`)
    ),
    transports: [
        new transports.Console(),
        new transports.File({ filename: path.join(PROJECT_DIR, 'Logs', 'deepseek.log') })
    ]
});

// 加载配置
const loadConfig = () => {
    try {
        const configPath = path.join(PROJECT_DIR, 'JavaScript', 'config.js');
        return require(configPath);
    } catch (error) {
        logger.error(`Failed to load config: ${error.message}`);
        // 返回默认配置
        return {
            server: {
                port: 3001,
                host: 'localhost'
            },
            monitoring: {
                enabled: true
            },
            api: {
                timeout: 30000
            }
        };
    }
};

// DeepSeek 引擎类
class DeepSeekEngine {
    constructor() {
        this.config = loadConfig();
        this.apiKey = process.env.DEEPSEEK_API_KEY || '';
        this.apiUrl = process.env.DEEPSEEK_API_URL || 'https://api.deepseek.com/v1/chat/completions';
        this.isRunning = false;
        this.cache = new Map();
        this.cacheTTL = 3600000; // 1小时缓存
    }

    // 初始化DeepSeek引擎
    async initialize() {
        logger.info('Initializing DeepSeek Engine...');
        
        try {
            // 检查API密钥
            if (!this.apiKey) {
                logger.warn('DeepSeek API key not found, using default integration mode');
            }

            // 测试API连接
            if (this.apiKey) {
                await this.testApiConnection();
            }

            this.isRunning = true;
            logger.info('DeepSeek Engine initialized successfully');
            return true;
        } catch (error) {
            logger.error(`Failed to initialize DeepSeek Engine: ${error.message}`);
            this.isRunning = false;
            return false;
        }
    }

    // 测试API连接
    async testApiConnection() {
        try {
            const response = await axios.post(this.apiUrl, {
                model: 'deepseek-chat',
                messages: [
                    { role: 'system', content: 'You are a helpful assistant.' },
                    { role: 'user', content: 'Hello, DeepSeek!' }
                ],
                max_tokens: 10
            }, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                },
                timeout: this.config.api.timeout || 30000
            });

            if (response.status === 200) {
                logger.info('DeepSeek API connection test successful');
                return true;
            } else {
                logger.error(`DeepSeek API connection test failed with status: ${response.status}`);
                return false;
            }
        } catch (error) {
            logger.error(`DeepSeek API connection test failed: ${error.message}`);
            return false;
        }
    }

    // 调用DeepSeek API
    async callApi(prompt, options = {}) {
        try {
            // 检查引擎是否运行
            if (!this.isRunning) {
                throw new Error('DeepSeek Engine is not running');
            }

            // 检查API密钥
            if (!this.apiKey) {
                logger.warn('DeepSeek API key not found, using local fallback');
                return this.localFallback(prompt);
            }

            // 构建请求参数
            const requestData = {
                model: options.model || 'deepseek-chat',
                messages: [
                    { role: 'system', content: options.systemPrompt || 'You are a helpful assistant.' },
                    { role: 'user', content: prompt }
                ],
                max_tokens: options.maxTokens || 1000,
                temperature: options.temperature || 0.7,
                top_p: options.topP || 0.95
            };

            // 发送请求
            const response = await axios.post(this.apiUrl, requestData, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                },
                timeout: this.config.api.timeout || 30000
            });

            if (response.status === 200) {
                const result = response.data.choices[0].message.content;
                logger.info('DeepSeek API call successful');
                return result;
            } else {
                logger.error(`DeepSeek API call failed with status: ${response.status}`);
                return this.localFallback(prompt);
            }
        } catch (error) {
            logger.error(`DeepSeek API call error: ${error.message}`);
            return this.localFallback(prompt);
        }
    }

    // 本地回退机制
    localFallback(prompt) {
        logger.info('Using local fallback for DeepSeek request');
        
        // 简单的本地回退逻辑，可以根据项目需求扩展
        const responses = {
            'hello': 'Hello! This is the local fallback response from MTSCOS AI Project.',
            'help': 'How can I assist you today? For more advanced features, please configure your DeepSeek API key.',
            'status': 'DeepSeek Engine is running in local mode. API key not configured.'
        };

        // 查找最匹配的响应
        for (const [key, value] of Object.entries(responses)) {
            if (prompt.toLowerCase().includes(key)) {
                return value;
            }
        }

        // 默认响应
        return `This is a local fallback response. Your query: "${prompt}". \n\nTo get more accurate responses, please configure your DeepSeek API key in the environment variables.`;
    }

    // 缓存管理
    getCache(key) {
        const cached = this.cache.get(key);
        if (cached && (Date.now() - cached.timestamp) < this.cacheTTL) {
            logger.debug(`Cache hit for key: ${key}`);
            return cached.value;
        }
        logger.debug(`Cache miss for key: ${key}`);
        return null;
    }

    setCache(key, value) {
        this.cache.set(key, {
            value: value,
            timestamp: Date.now()
        });
        logger.debug(`Cache set for key: ${key}`);
    }

    // 清理缓存
    cleanupCache() {
        const now = Date.now();
        let cleaned = 0;
        
        for (const [key, cached] of this.cache.entries()) {
            if ((now - cached.timestamp) > this.cacheTTL) {
                this.cache.delete(key);
                cleaned++;
            }
        }
        
        if (cleaned > 0) {
            logger.info(`Cleaned ${cleaned} expired cache entries`);
        }
    }

    // 停止引擎
    stop() {
        logger.info('Stopping DeepSeek Engine...');
        this.isRunning = false;
        this.cache.clear();
        logger.info('DeepSeek Engine stopped');
    }

    // 获取状态
    getStatus() {
        return {
            isRunning: this.isRunning,
            apiKeyConfigured: !!this.apiKey,
            cacheSize: this.cache.size,
            timestamp: new Date().toISOString()
        };
    }

    // 系统监控
    async runSystemHealthCheck() {
        try {
            logger.info('Running system health check...');
            
            const healthStatus = {
                timestamp: Date.now(),
                deepseek: this.getStatus(),
                diskSpace: await this.getDiskSpace(),
                memoryUsage: process.memoryUsage()
            };

            // 保存健康检查结果
            const healthCheckPath = path.join(PROJECT_DIR, 'Staging', 'Logs', 'health-checks.json');
            fs.writeFileSync(healthCheckPath, JSON.stringify(healthStatus, null, 2));
            
            logger.info('System health check completed');
            return healthStatus;
        } catch (error) {
            logger.error(`System health check failed: ${error.message}`);
            return null;
        }
    }

    // 获取磁盘空间信息
    async getDiskSpace() {
        try {
            const stats = fs.statfsSync(PROJECT_DIR);
            const total = stats.blockSize * stats.blocks;
            const free = stats.blockSize * stats.bfree;
            const used = total - free;

            return {
                total: this.formatBytes(total),
                used: this.formatBytes(used),
                free: this.formatBytes(free),
                usage: Math.round((used / total) * 100)
            };
        } catch (error) {
            logger.error(`Failed to get disk space: ${error.message}`);
            return null;
        }
    }

    // 格式化字节数
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// 主函数
const main = async () => {
    logger.info('Starting DeepSeek Engine Integration...');

    // 创建DeepSeek引擎实例
    const deepseekEngine = new DeepSeekEngine();

    // 初始化引擎
    const initialized = await deepseekEngine.initialize();
    if (!initialized) {
        logger.error('Failed to initialize DeepSeek Engine, exiting...');
        process.exit(1);
    }

    // 定期运行健康检查
    const healthCheckInterval = setInterval(() => {
        deepseekEngine.runSystemHealthCheck();
    }, 3600000); // 每小时运行一次

    // 定期清理缓存
    const cacheCleanupInterval = setInterval(() => {
        deepseekEngine.cleanupCache();
    }, 1800000); // 每30分钟清理一次

    // 处理终止信号
    process.on('SIGINT', () => {
        logger.info('Received SIGINT, stopping DeepSeek Engine...');
        clearInterval(healthCheckInterval);
        clearInterval(cacheCleanupInterval);
        deepseekEngine.stop();
        process.exit(0);
    });

    process.on('SIGTERM', () => {
        logger.info('Received SIGTERM, stopping DeepSeek Engine...');
        clearInterval(healthCheckInterval);
        clearInterval(cacheCleanupInterval);
        deepseekEngine.stop();
        process.exit(0);
    });

    // 处理未捕获的异常
    process.on('uncaughtException', (error) => {
        logger.error(`Uncaught Exception: ${error.message}`);
        logger.error(error.stack);
    });

    process.on('unhandledRejection', (reason, promise) => {
        logger.error(`Unhandled Rejection: ${reason.message || reason}`);
        logger.error(`Promise: ${promise}`);
    });

    logger.info('DeepSeek Engine Integration started successfully');

    // 保持进程运行
    setInterval(() => {}, 1000);
};

// 启动应用
if (require.main === module) {
    main();
}

// 导出模块
module.exports = DeepSeekEngine;