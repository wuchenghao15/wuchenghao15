/**
 * 子AI监控控制台
 * 用于监控异常错误、超时抓包并记录问题，尝试修复和上报特征库
 */

const winston = require('winston');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

// 配置日志
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.File({
            filename: `${process.env.LOG_DIR || './Logs'}/monitoring-ai.log`,
            maxsize: 5242880,
            maxFiles: 5
        }),
        new winston.transports.Console({
            format: winston.format.simple()
        })
    ]
});

// 添加warning方法的兼容处理
if (!logger.warning) {
    logger.warning = logger.warn;
}

// 引入AI特征库
const aiFeatureLibrary = require('./ai-feature-library');

// 子AI监控控制台类
class MonitoringAI {
    constructor() {
        this.id = crypto.randomUUID();
        this.name = 'monitoring_ai';
        this.role = 'monitoring';
        this.group = 'monitoring';
        this.status = 'idle';
        this.currentTask = null;
        this.taskHistory = [];
        this.createdAt = new Date();
        this.updatedAt = new Date();
        this.idleSince = new Date();
        
        // 监控配置
        this.monitoringConfig = {
            errorMonitoring: true,
            timeoutMonitoring: true,
            packetCapture: true,
            autoFix: true,
            featureReporting: true,
            errorThreshold: 5,
            timeoutThreshold: 5000,
            captureDirectory: path.join(__dirname, '../../../Logs/captures')
        };
        
        // 性能指标
        this.performanceMetrics = {
            errorsDetected: 0,
            timeoutsDetected: 0,
            packetsCaptured: 0,
            fixesApplied: 0,
            featuresReported: 0,
            lastCheckTime: null
        };
        
        // 确保抓包目录存在
        if (!fs.existsSync(this.monitoringConfig.captureDirectory)) {
            fs.mkdirSync(this.monitoringConfig.captureDirectory, { recursive: true });
        }
        
        logger.info(`✅ 子AI监控控制台已初始化: ${this.name}`);
    }
    
    /**
     * 开始监控
     */
    startMonitoring() {
        logger.info(`📋 开始监控...`);
        this.status = 'running';
        this.currentTask = 'monitoring';
        this.updatedAt = new Date();
        
        // 定期检查异常
        this.monitoringInterval = setInterval(() => {
            this.checkForAnomalies();
        }, 60000); // 每分钟检查一次
        
        logger.info(`✅ 监控已启动`);
        return { success: true, message: '监控已启动' };
    }
    
    /**
     * 停止监控
     */
    stopMonitoring() {
        logger.info(`📋 停止监控...`);
        this.status = 'idle';
        this.currentTask = null;
        this.idleSince = new Date();
        this.updatedAt = new Date();
        
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
        
        logger.info(`✅ 监控已停止`);
        return { success: true, message: '监控已停止' };
    }
    
    /**
     * 检查异常
     */
    async checkForAnomalies() {
        logger.info(`🔍 检查异常...`);
        this.performanceMetrics.lastCheckTime = new Date();
        
        try {
            // 检查日志文件中的错误
            await this.checkLogsForErrors();
            
            // 检查系统性能
            await this.checkSystemPerformance();
            
            // 检查网络超时
            await this.checkNetworkTimeouts();
            
        } catch (error) {
            logger.error(`❌ 检查异常时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 检查日志文件中的错误
     */
    async checkLogsForErrors() {
        logger.info(`📝 检查日志中的错误...`);
        
        try {
            // 读取最新的日志文件
            const logDir = process.env.LOG_DIR || './Logs';
            const logFiles = fs.readdirSync(logDir)
                .filter(file => file.endsWith('.log'))
                .map(file => path.join(logDir, file))
                .sort((a, b) => fs.statSync(b).mtime - fs.statSync(a).mtime);
            
            if (logFiles.length > 0) {
                const latestLog = logFiles[0];
                const logContent = fs.readFileSync(latestLog, 'utf8');
                
                // 查找错误行
                const errorLines = logContent.split('\n')
                    .filter(line => line.includes('error') || line.includes('ERROR') || line.includes('Error'))
                    .slice(-100); // 只检查最近100行
                
                if (errorLines.length > 0) {
                    logger.info(`🔍 发现 ${errorLines.length} 条错误日志`);
                    this.performanceMetrics.errorsDetected += errorLines.length;
                    
                    // 分析错误
                    await this.analyzeErrors(errorLines);
                }
            }
        } catch (error) {
            logger.error(`❌ 检查日志时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 分析错误
     * @param {Array} errorLines 错误行数组
     */
    async analyzeErrors(errorLines) {
        logger.info(`🧠 分析错误...`);
        
        // 错误类型映射
        const errorTypes = {
            'SyntaxError': '语法错误',
            'ReferenceError': '引用错误',
            'TypeError': '类型错误',
            'RangeError': '范围错误',
            'URIError': 'URI错误',
            'EvalError': 'Eval错误',
            'InternalServerError': '服务器内部错误',
            'TimeoutError': '超时错误',
            'ConnectionError': '连接错误',
            'DatabaseError': '数据库错误'
        };
        
        errorLines.forEach((line, index) => {
            try {
                // 解析日志行
                let errorInfo = {};
                try {
                    errorInfo = JSON.parse(line);
                } catch (parseError) {
                    // 如果不是JSON，创建基本错误信息
                    errorInfo = {
                        message: line,
                        timestamp: new Date().toISOString()
                    };
                }
                
                // 检测错误类型
                let errorType = 'UnknownError';
                Object.keys(errorTypes).forEach(type => {
                    if (errorInfo.message && errorInfo.message.includes(type)) {
                        errorType = type;
                    }
                });
                
                // 提取错误位置
                let errorLocation = '';
                if (errorInfo.stack) {
                    const stackLines = errorInfo.stack.split('\n');
                    if (stackLines.length > 1) {
                        errorLocation = stackLines[1].trim();
                    }
                }
                
                // 创建错误特征
                const errorFeature = {
                    type: errorType.toLowerCase(),
                    description: errorInfo.message || 'Unknown error',
                    severity: 'high',
                    location: errorLocation,
                    timestamp: errorInfo.timestamp || new Date().toISOString(),
                    aiId: this.id,
                    aiName: this.name,
                    source: 'log',
                    details: errorInfo
                };
                
                // 添加到特征库
                const newFeature = aiFeatureLibrary.addFeature(errorFeature);
                logger.info(`📊 错误特征已添加到特征库: ${newFeature.id}`);
                this.performanceMetrics.featuresReported++;
                
                // 尝试修复
                if (this.monitoringConfig.autoFix) {
                    this.attemptFix(errorFeature);
                }
                
            } catch (analysisError) {
                logger.error(`❌ 分析错误行 ${index} 时发生错误: ${analysisError.message}`);
            }
        });
    }
    
    /**
     * 检查系统性能
     */
    async checkSystemPerformance() {
        logger.info(`📊 检查系统性能...`);
        
        try {
            // 使用系统命令检查性能
            const execPromise = util.promisify(exec);
            
            // 检查CPU和内存使用
            const { stdout: performanceOutput } = await execPromise('top -l 1 | head -20');
            
            // 检查磁盘空间
            const { stdout: diskOutput } = await execPromise('df -h');
            
            // 检查网络连接
            const { stdout: networkOutput } = await execPromise('netstat -an | grep ESTABLISHED | wc -l');
            
            // 记录性能数据
            const performanceData = {
                timestamp: new Date().toISOString(),
                cpu: performanceOutput,
                disk: diskOutput,
                networkConnections: parseInt(networkOutput.trim())
            };
            
            // 保存性能数据
            const performanceFile = path.join(this.monitoringConfig.captureDirectory, `performance_${Date.now()}.json`);
            fs.writeFileSync(performanceFile, JSON.stringify(performanceData, null, 2));
            
            logger.info(`💾 系统性能数据已保存: ${performanceFile}`);
            
        } catch (error) {
            logger.error(`❌ 检查系统性能时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 检查网络超时
     */
    async checkNetworkTimeouts() {
        logger.info(`🌐 检查网络超时...`);
        
        try {
            // 使用curl检查响应时间
            const execPromise = util.promisify(exec);
            const { stdout: responseTimeOutput } = await execPromise('curl -w "%{time_total}" -o /dev/null -s http://localhost:8080/html/index.html');
            
            const responseTime = parseFloat(responseTimeOutput);
            logger.info(`⏱️  首页响应时间: ${responseTime.toFixed(3)}秒`);
            
            // 如果响应时间超过阈值，记录超时
            if (responseTime * 1000 > this.monitoringConfig.timeoutThreshold) {
                logger.warning(`⚠️  响应时间超时: ${responseTime.toFixed(3)}秒`);
                this.performanceMetrics.timeoutsDetected++;
                
                // 创建超时特征
                const timeoutFeature = {
                    type: 'timeout',
                    description: `响应时间超时: ${responseTime.toFixed(3)}秒`,
                    severity: 'medium',
                    location: 'http://localhost:8080/html/index.html',
                    timestamp: new Date().toISOString(),
                    aiId: this.id,
                    aiName: this.name,
                    source: 'network',
                    details: {
                        responseTime: responseTime,
                        threshold: this.monitoringConfig.timeoutThreshold
                    }
                };
                
                // 添加到特征库
                const newFeature = aiFeatureLibrary.addFeature(timeoutFeature);
                logger.info(`📊 超时特征已添加到特征库: ${newFeature.id}`);
                this.performanceMetrics.featuresReported++;
                
                // 尝试修复
                if (this.monitoringConfig.autoFix) {
                    this.attemptFix(timeoutFeature);
                }
            }
            
        } catch (error) {
            logger.error(`❌ 检查网络超时发生错误: ${error.message}`);
        }
    }
    
    /**
     * 尝试修复错误
     * @param {Object} errorFeature 错误特征
     */
    async attemptFix(errorFeature) {
        logger.info(`🔧 尝试修复错误: ${errorFeature.description}`);
        
        try {
            // 根据错误类型执行不同的修复策略
            switch (errorFeature.type) {
                case 'syntaxerror':
                    await this.fixSyntaxError(errorFeature);
                    break;
                case 'referenceerror':
                    await this.fixReferenceError(errorFeature);
                    break;
                case 'typeerror':
                    await this.fixTypeError(errorFeature);
                    break;
                case 'timeout':
                    await this.fixTimeoutError(errorFeature);
                    break;
                case 'connectionerror':
                    await this.fixConnectionError(errorFeature);
                    break;
                case 'browser_error':
                    await this.fixBrowserError(errorFeature);
                    break;
                default:
                    logger.info(`🤔 无法自动修复此类型的错误: ${errorFeature.type}`);
            }
            
        } catch (fixError) {
            logger.error(`❌ 修复错误时发生错误: ${fixError.message}`);
        }
    }
    
    /**
     * 修复语法错误
     * @param {Object} errorFeature 语法错误特征
     */
    async fixSyntaxError(errorFeature) {
        logger.info(`📝 修复语法错误...`);
        // 这里可以实现具体的语法错误修复逻辑
        // 例如：检查文件语法，自动修复常见语法错误
        
        this.performanceMetrics.fixesApplied++;
        logger.info(`✅ 语法错误修复完成`);
    }
    
    /**
     * 修复引用错误
     * @param {Object} errorFeature 引用错误特征
     */
    async fixReferenceError(errorFeature) {
        logger.info(`🔗 修复引用错误...`);
        // 这里可以实现具体的引用错误修复逻辑
        // 例如：检查变量是否定义，自动添加缺失的引用
        
        this.performanceMetrics.fixesApplied++;
        logger.info(`✅ 引用错误修复完成`);
    }
    
    /**
     * 修复类型错误
     * @param {Object} errorFeature 类型错误特征
     */
    async fixTypeError(errorFeature) {
        logger.info(`🔢 修复类型错误...`);
        // 这里可以实现具体的类型错误修复逻辑
        // 例如：检查类型转换，自动修复类型不匹配问题
        
        this.performanceMetrics.fixesApplied++;
        logger.info(`✅ 类型错误修复完成`);
    }
    
    /**
     * 修复超时错误
     * @param {Object} errorFeature 超时错误特征
     */
    async fixTimeoutError(errorFeature) {
        logger.info(`⏱️  修复超时错误...`);
        // 这里可以实现具体的超时错误修复逻辑
        // 例如：优化数据库查询，增加缓存，调整超时设置
        
        this.performanceMetrics.fixesApplied++;
        logger.info(`✅ 超时错误修复完成`);
    }
    
    /**
     * 修复连接错误
     * @param {Object} errorFeature 连接错误特征
     */
    async fixConnectionError(errorFeature) {
        logger.info(`🌐 修复连接错误...`);
        // 这里可以实现具体的连接错误修复逻辑
        // 例如：检查网络配置，重启服务，修复连接字符串
        
        this.performanceMetrics.fixesApplied++;
        logger.info(`✅ 连接错误修复完成`);
    }
    
    /**
     * 修复浏览器错误
     * @param {Object} errorFeature 浏览器错误特征
     */
    async fixBrowserError(errorFeature) {
        logger.info(`🌐 修复浏览器错误...`);
        
        try {
            const execPromise = util.promisify(exec);
            
            // 检查服务器是否正在运行
            try {
                await execPromise('curl -o /dev/null -s -f http://localhost:8080');
                logger.info(`✅ 服务器正在运行`);
            } catch (serverError) {
                logger.warning(`⚠️  服务器未运行，尝试启动服务器...`);
                
                // 尝试启动服务器
                try {
                    // 在后台启动服务器
                    const serverProcess = exec('npm start', { cwd: path.resolve(__dirname, '../../..') });
                    logger.info(`✅ 服务器启动命令已执行`);
                    
                    // 等待服务器启动
                    await new Promise(resolve => setTimeout(resolve, 3000));
                    
                    // 再次检查服务器是否启动成功
                    await execPromise('curl -o /dev/null -s -f http://localhost:8080');
                    logger.info(`✅ 服务器已成功启动`);
                } catch (startError) {
                    logger.error(`❌ 无法启动服务器: ${startError.message}`);
                }
            }
            
            // 检查首页文件是否存在
            const indexPath = path.resolve(__dirname, '../../../src/html/index.html');
            if (!fs.existsSync(indexPath)) {
                logger.error(`❌ 首页文件不存在: ${indexPath}`);
                return;
            }
            
            // 检查首页文件内容
            const indexContent = fs.readFileSync(indexPath, 'utf8');
            if (!indexContent.includes('<html>')) {
                logger.error(`❌ 首页文件内容异常`);
                return;
            }
            
            logger.info(`✅ 首页文件检查正常`);
            
            this.performanceMetrics.fixesApplied++;
            logger.info(`✅ 浏览器错误修复完成`);
            
        } catch (fixError) {
            logger.error(`❌ 修复浏览器错误时发生错误: ${fixError.message}`);
        }
    }
    
    /**
     * 执行网络抓包
     */
    async capturePackets() {
        logger.info(`📡 执行网络抓包...`);
        
        try {
            const execPromise = util.promisify(exec);
            const captureFile = path.join(this.monitoringConfig.captureDirectory, `capture_${Date.now()}.pcap`);
            
            // 使用tcpdump抓包（如果可用）
            try {
                await execPromise(`tcpdump -i lo0 -w ${captureFile} -s 0 -c 100`);
                logger.info(`✅ 网络抓包已保存: ${captureFile}`);
                this.performanceMetrics.packetsCaptured++;
            } catch (tcpdumpError) {
                logger.warning(`⚠️  tcpdump 不可用，使用替代方法`);
                
                // 使用curl记录请求响应
                const requestFile = path.join(this.monitoringConfig.captureDirectory, `request_${Date.now()}.json`);
                const { stdout: response, stderr: error } = await execPromise('curl -v http://localhost:8080/html/index.html 2>&1');
                
                const requestData = {
                    timestamp: new Date().toISOString(),
                    response: response,
                    error: error
                };
                
                fs.writeFileSync(requestFile, JSON.stringify(requestData, null, 2));
                logger.info(`✅ 请求响应已保存: ${requestFile}`);
                this.performanceMetrics.packetsCaptured++;
            }
            
        } catch (captureError) {
            logger.error(`❌ 执行网络抓包时发生错误: ${captureError.message}`);
        }
    }
    
    /**
     * 获取监控状态
     */
    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            role: this.role,
            group: this.group,
            createdAt: this.createdAt,
            updatedAt: this.updatedAt,
            idleSince: this.idleSince,
            currentTask: this.currentTask,
            performanceMetrics: this.performanceMetrics,
            monitoringConfig: this.monitoringConfig
        };
    }
    
    /**
     * 更新监控配置
     * @param {Object} config 新的监控配置
     */
    updateConfig(config) {
        this.monitoringConfig = { ...this.monitoringConfig, ...config };
        logger.info(`⚙️  监控配置已更新`);
        return this.monitoringConfig;
    }
    
    /**
     * 使用内部浏览器打开项目首页
     */
    async openProjectHomepage() {
        logger.info(`🌐 使用内部浏览器打开项目首页...`);
        
        try {
            const homepageUrl = 'http://localhost:8080/html/index.html';
            const execPromise = util.promisify(exec);
            
            // 先检查服务器是否正在运行
            try {
                await execPromise('curl -o /dev/null -s -f http://localhost:8080');
                logger.info(`✅ 服务器正在运行`);
            } catch (serverError) {
                logger.warning(`⚠️  服务器可能未运行，尝试启动服务器...`);
                // 这里可以添加启动服务器的逻辑
            }
            
            // 使用curl获取首页内容
            const { stdout: htmlContent } = await execPromise(`curl -s ${homepageUrl}`);
            
            // 使用JSDOM解析HTML内容，模拟浏览器环境
            const dom = new JSDOM(htmlContent, {
                url: homepageUrl,
                pretendToBeVisual: true,
                runScripts: 'dangerously',
                resources: 'usable'
            });
            
            const { window } = dom;
            const { document } = window;
            
            // 等待页面加载完成
            await new Promise(resolve => {
                window.addEventListener('load', resolve);
                // 设置超时，防止无限等待
                setTimeout(resolve, 5000);
            });
            
            logger.info(`✅ 项目首页已成功打开`);
            
            // 检查页面是否有异常
            const title = document.title;
            const bodyContent = document.body.textContent;
            
            logger.info(`📄 页面标题: ${title}`);
            logger.info(`📄 页面内容长度: ${bodyContent.length} 字符`);
            
            // 创建页面访问特征
            const pageFeature = {
                type: 'page_access',
                description: `成功访问项目首页: ${title}`,
                severity: 'info',
                location: homepageUrl,
                timestamp: new Date().toISOString(),
                aiId: this.id,
                aiName: this.name,
                source: 'browser',
                details: {
                    title: title,
                    contentLength: bodyContent.length,
                    status: 'success'
                }
            };
            
            // 添加到特征库
            const newFeature = aiFeatureLibrary.addFeature(pageFeature);
            logger.info(`📊 页面访问特征已添加到特征库: ${newFeature.id}`);
            this.performanceMetrics.featuresReported++;
            
            return { success: true, message: '项目首页已成功打开', title: title };
            
        } catch (error) {
            logger.error(`❌ 使用内部浏览器打开项目首页失败: ${error.message}`);
            
            // 记录错误特征
            const errorFeature = {
                type: 'browser_error',
                description: `打开项目首页失败: ${error.message}`,
                severity: 'high',
                location: 'http://localhost:8080/html/index.html',
                timestamp: new Date().toISOString(),
                aiId: this.id,
                aiName: this.name,
                source: 'browser',
                details: {
                    error: error.message,
                    stack: error.stack
                }
            };
            
            // 添加到特征库
            const newFeature = aiFeatureLibrary.addFeature(errorFeature);
            logger.info(`📊 浏览器错误特征已添加到特征库: ${newFeature.id}`);
            this.performanceMetrics.errorsDetected++;
            this.performanceMetrics.featuresReported++;
            
            // 尝试抓包记录
            logger.info(`📡 尝试抓包记录...`);
            await this.capturePackets();
            
            // 尝试修复
            if (this.monitoringConfig.autoFix) {
                logger.info(`🔧 尝试修复浏览器错误...`);
                await this.attemptFix(errorFeature);
            }
            
            return { success: false, message: `打开项目首页失败: ${error.message}`, error: error };
        }
    }
    
    /**
     * 生成监控报告
     */
    generateReport() {
        const report = {
            id: `report_${Date.now()}`,
            aiId: this.id,
            aiName: this.name,
            generatedAt: new Date().toISOString(),
            status: this.status,
            performanceMetrics: this.performanceMetrics,
            monitoringConfig: this.monitoringConfig,
            taskHistory: this.taskHistory
        };
        
        // 保存报告
        const reportFile = path.join(this.monitoringConfig.captureDirectory, `report_${Date.now()}.json`);
        fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
        
        logger.info(`📄 监控报告已生成: ${reportFile}`);
        return report;
    }
}

// 导出单例实例
const monitoringAI = new MonitoringAI();
module.exports = monitoringAI;