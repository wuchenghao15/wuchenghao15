const EventEmitter = require('events');
const fs = require('fs');
const path = require('path');
const RepairEngine = require('./repair-engine');

/**
 * 自动错误修复系统
 * 提供JavaScript、CSS、HTML文件的错误自动检测和修复功能
 */
class AutoErrorRepairSystem extends EventEmitter {
    /**
     * 构造函数
     * @param {Object} config - 配置信息
     */
    constructor(config = {}) {
        super();
        
        // 配置参数
        this.config = Object.assign({
            // 扫描的文件类型
            fileTypes: ['.js', '.css', '.html'],
            
            // 排除的目录
            excludeDirs: ['node_modules', '.git', 'dist', 'build'],
            
            // 修复策略配置
            repairStrategies: {
                auto: true,
                ai: true,
                security: true,
                performance: true,
                codeQuality: true
            },
            
            // AI模型配置
            aiModels: {
                gpt35: { enabled: true, priority: 1 },
                gpt4: { enabled: true, priority: 2 },
                claude: { enabled: false, priority: 3 },
                gemini: { enabled: false, priority: 4 }
            },
            
            // 日志级别
            logLevel: 'info',
            
            // 修复超时时间
            repairTimeout: 30000,
            
            // 并行修复限制
            maxConcurrentRepairs: 5,
            
            // 是否自动保存修复结果
            autoSave: false,
            
            // 是否创建备份
            createBackup: true,
            
            // 备份目录
            backupDir: './backups'
        }, config);
        
        // 初始化修复引擎
        this.repairEngine = new RepairEngine(this.config);
        
        // 初始化日志
        this.logger = this.repairEngine.logger;
        
        // 初始化修复结果统计
        this.stats = {
            scannedFiles: 0,
            filesWithIssues: 0,
            totalIssues: 0,
            fixedIssues: 0,
            failedIssues: 0,
            repairTime: 0
        };
        
        // 初始化工作队列
        this.workQueue = [];
        this.currentRepairs = 0;
        
        // 监听修复引擎事件
        this.repairEngine.on('repair_started', (filePath) => {
            this.emit('repair_started', filePath);
        });
        
        this.repairEngine.on('repair_completed', (result) => {
            this.emit('repair_completed', result);
            this.currentRepairs--;
            this.processNextInQueue();
        });
        
        this.repairEngine.on('repair_failed', (result) => {
            this.emit('repair_failed', result);
            this.currentRepairs--;
            this.processNextInQueue();
        });
        
        // 创建备份目录
        if (this.config.createBackup && !fs.existsSync(this.config.backupDir)) {
            fs.mkdirSync(this.config.backupDir, { recursive: true });
        }
        
        this.logger.info('AUTO_ERROR_REPAIR_SYSTEM', '系统初始化完成');
    }
    
    /**
     * 扫描目录并修复文件
     * @param {string} dirPath - 目录路径
     * @returns {Promise<Object>} 修复结果
     */
    async scanAndRepair(dirPath) {
        this.logger.info('AUTO_ERROR_REPAIR_SYSTEM', '开始扫描和修复', { dirPath });
        
        const startTime = Date.now();
        this.stats = {
            scannedFiles: 0,
            filesWithIssues: 0,
            totalIssues: 0,
            fixedIssues: 0,
            failedIssues: 0,
            repairTime: 0
        };
        
        try {
            // 获取所有要扫描的文件
            const files = await this.getFilesToScan(dirPath);
            
            // 扫描并修复每个文件
            for (const file of files) {
                await this.scanAndRepairFile(file);
            }
            
            // 等待所有修复完成
            while (this.currentRepairs > 0) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            
            this.stats.repairTime = Date.now() - startTime;
            
            this.logger.info('AUTO_ERROR_REPAIR_SYSTEM', '扫描和修复完成', this.stats);
            this.emit('scan_completed', this.stats);
            
            return this.stats;
        } catch (error) {
            this.logger.error('AUTO_ERROR_REPAIR_SYSTEM', '扫描和修复失败', error);
            this.emit('scan_failed', error);
            throw error;
        }
    }
    
    /**
     * 获取要扫描的文件列表
     * @param {string} dirPath - 目录路径
     * @returns {Promise<Array<string>>} 文件列表
     */
    async getFilesToScan(dirPath) {
        let files = [];
        
        try {
            const entries = await fs.promises.readdir(dirPath, { withFileTypes: true });
            
            for (const entry of entries) {
                const fullPath = path.join(dirPath, entry.name);
                
                // 检查是否为排除的目录
                if (entry.isDirectory() && !this.config.excludeDirs.includes(entry.name)) {
                    // 递归扫描子目录
                    const subFiles = await this.getFilesToScan(fullPath);
                    files = files.concat(subFiles);
                } else if (entry.isFile()) {
                    // 检查文件类型
                    const ext = path.extname(entry.name);
                    if (this.config.fileTypes.includes(ext)) {
                        files.push(fullPath);
                    }
                }
            }
        } catch (error) {
            this.logger.error('AUTO_ERROR_REPAIR_SYSTEM', '获取文件列表失败', { dirPath, error });
        }
        
        return files;
    }
    
    /**
     * 扫描并修复单个文件
     * @param {string} filePath - 文件路径
     * @returns {Promise<Object>} 修复结果
     */
    async scanAndRepairFile(filePath) {
        this.stats.scannedFiles++;
        
        try {
            // 读取文件内容
            const fileContent = await fs.promises.readFile(filePath, 'utf8');
            
            // 检查是否超过修复限制
            if (this.currentRepairs >= this.config.maxConcurrentRepairs) {
                // 添加到工作队列
                return new Promise((resolve) => {
                    this.workQueue.push({ filePath, fileContent, resolve });
                });
            } else {
                return this.processFile(filePath, fileContent);
            }
        } catch (error) {
            this.logger.error('AUTO_ERROR_REPAIR_SYSTEM', '扫描文件失败', { filePath, error });
            return { filePath, success: false, error: error.message };
        }
    }
    
    /**
     * 处理文件修复
     * @param {string} filePath - 文件路径
     * @param {string} fileContent - 文件内容
     * @returns {Promise<Object>} 修复结果
     */
    async processFile(filePath, fileContent) {
        this.currentRepairs++;
        
        try {
            // 检测问题
            const issues = await this.detectIssues(filePath, fileContent);
            
            if (issues.length === 0) {
                this.logger.info('AUTO_ERROR_REPAIR_SYSTEM', '文件无问题', { filePath });
                return { filePath, success: true, issues: [], fixedIssues: 0 };
            }
            
            this.stats.filesWithIssues++;
            this.stats.totalIssues += issues.length;
            
            // 按优先级排序问题
            const prioritizedIssues = this.prioritizeIssues(issues);
            
            // 创建备份
            if (this.config.createBackup) {
                await this.createBackup(filePath, fileContent);
            }
            
            // 修复问题
            let currentContent = fileContent;
            let fixedCount = 0;
            
            for (const issue of prioritizedIssues) {
                const repairResult = await this.repairEngine.repair(issue, currentContent);
                
                if (repairResult.success) {
                    currentContent = repairResult.fixedContent;
                    fixedCount++;
                    this.stats.fixedIssues++;
                    
                    this.logger.info('AUTO_ERROR_REPAIR_SYSTEM', '问题修复成功', {
                        filePath,
                        issueType: issue.type,
                        line: issue.line,
                        message: issue.message,
                        strategy: repairResult.strategy,
                        model: repairResult.model
                    });
                } else {
                    this.stats.failedIssues++;
                    
                    this.logger.warn('AUTO_ERROR_REPAIR_SYSTEM', '问题修复失败', {
                        filePath,
                        issueType: issue.type,
                        line: issue.line,
                        message: issue.message,
                        error: repairResult.error
                    });
                }
            }
            
            // 自动保存修复结果
            if (this.config.autoSave && fixedCount > 0) {
                await fs.promises.writeFile(filePath, currentContent, 'utf8');
                
                this.logger.info('AUTO_ERROR_REPAIR_SYSTEM', '修复结果已保存', { filePath, fixedCount });
            }
            
            return { 
                filePath, 
                success: true, 
                issues: prioritizedIssues, 
                fixedIssues: fixedCount 
            };
        } catch (error) {
            this.logger.error('AUTO_ERROR_REPAIR_SYSTEM', '文件修复失败', { filePath, error });
            return { filePath, success: false, error: error.message };
        } finally {
            this.currentRepairs--;
            this.processNextInQueue();
        }
    }
    
    /**
     * 处理队列中的下一个文件
     */
    processNextInQueue() {
        if (this.workQueue.length > 0 && this.currentRepairs < this.config.maxConcurrentRepairs) {
            const { filePath, fileContent, resolve } = this.workQueue.shift();
            this.processFile(filePath, fileContent).then(resolve);
        }
    }
    
    /**
     * 检测文件中的问题
     * @param {string} filePath - 文件路径
     * @param {string} fileContent - 文件内容
     * @returns {Promise<Array<Object>>} 问题列表
     */
    async detectIssues(filePath, fileContent) {
        try {
            // 使用修复引擎检测问题
            const issues = await this.repairEngine.detect(filePath, fileContent);
            
            return issues;
        } catch (error) {
            this.logger.error('AUTO_ERROR_REPAIR_SYSTEM', '检测问题失败', { filePath, error });
            return [];
        }
    }
    
    /**
     * 按优先级排序问题
     * @param {Array<Object>} issues - 问题列表
     * @returns {Array<Object>} 排序后的问题列表
     */
    prioritizeIssues(issues) {
        // 定义问题类型优先级
        const typePriority = {
            'SecurityVulnerability': 1,
            'SyntaxError': 2,
            'LogicError': 3,
            'PerformanceIssue': 4,
            'CodeQuality': 5
        };
        
        // 定义严重程度优先级
        const severityPriority = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4
        };
        
        // 按优先级排序
        return [...issues].sort((a, b) => {
            // 先按问题类型排序
            const typeDiff = typePriority[a.type] - typePriority[b.type];
            if (typeDiff !== 0) return typeDiff;
            
            // 再按严重程度排序
            const severityDiff = severityPriority[a.severity] - severityPriority[b.severity];
            if (severityDiff !== 0) return severityDiff;
            
            // 最后按行号排序
            return a.line - b.line;
        });
    }
    
    /**
     * 创建文件备份
     * @param {string} filePath - 文件路径
     * @param {string} fileContent - 文件内容
     * @returns {Promise<void>}
     */
    async createBackup(filePath, fileContent) {
        try {
            const relativePath = path.relative(process.cwd(), filePath);
            const backupPath = path.join(this.config.backupDir, relativePath);
            
            // 创建备份目录结构
            await fs.promises.mkdir(path.dirname(backupPath), { recursive: true });
            
            // 保存备份
            await fs.promises.writeFile(backupPath, fileContent, 'utf8');
            
            this.logger.debug('AUTO_ERROR_REPAIR_SYSTEM', '备份创建成功', { filePath, backupPath });
        } catch (error) {
            this.logger.error('AUTO_ERROR_REPAIR_SYSTEM', '创建备份失败', { filePath, error });
        }
    }
    
    /**
     * 获取修复系统状态
     * @returns {Object} 系统状态
     */
    getStatus() {
        return {
            config: this.config,
            stats: this.stats,
            queueLength: this.workQueue.length,
            currentRepairs: this.currentRepairs,
            repairEngineStatus: this.repairEngine.getStatus()
        };
    }
    
    /**
     * 设置配置
     * @param {Object} newConfig - 新配置
     */
    setConfig(newConfig) {
        this.config = Object.assign(this.config, newConfig);
        this.repairEngine.setConfig(this.config);
        
        this.logger.info('AUTO_ERROR_REPAIR_SYSTEM', '配置已更新', newConfig);
    }
    
    /**
     * 清理资源
     * @returns {Promise<void>}
     */
    async cleanup() {
        await this.repairEngine.cleanup();
        
        this.logger.info('AUTO_ERROR_REPAIR_SYSTEM', '资源已清理');
    }
}

module.exports = AutoErrorRepairSystem;