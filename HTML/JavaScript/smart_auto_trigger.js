#!/usr/bin/env node
// VERSION: 20251114.0001

/**
 * MTSCOS 智能自动更新触发器
 * 功能：
 * 1. 智能文件变更检测
 * 2. 自动触发更新机制
 * 3. 依赖关系分析
 * 4. 增量更新优化
 * 5. 更新队列管理
 */

const fs = require('fs');
const path = require('path');
const { execSync, exec } = require('child_process');
const crypto = require('crypto');
const chokidar = require('chokidar');

// 配置
const CONFIG = {
    // 项目根目录
    PROJECT_ROOT: process.cwd(),
    // 监控配置
    WATCH_CONFIG: {
        // 监控目录
        WATCH_DIRS: [
            './JavaScript',
            './CSS',
            './HTML',
            './Scripts',
            './HardwareKey',
            './Server'
        ],
        // 监控文件类型
        WATCH_EXTENSIONS: ['.js', '.css', '.html', '.sh', '.json', '.md'],
        // 忽略模式
        IGNORE_PATTERNS: [
            '**/node_modules/**',
            '**/Backups/**',
            '**/Logs/**',
            '**/.git/**',
            '**/*.log',
            '**/*.tmp',
            '**/*.bak'
        ],
        // 防抖延迟（毫秒）
        DEBOUNCE_DELAY: 1000,
        // 批处理延迟
        BATCH_DELAY: 5000
    },
    // 更新配置
    UPDATE_CONFIG: {
        // 更新触发器脚本
        TRIGGER_SCRIPT: '../Scripts/update_trigger.sh',
        // 增强更新管理器
        ENHANCED_MANAGER: '../JavaScript/enhanced_update_manager.js',
        // 最大并发更新数
        MAX_CONCURRENT_UPDATES: 3,
        // 更新队列大小限制
        MAX_QUEUE_SIZE: 100,
        // 自动优化
        AUTO_OPTIMIZE: true,
        // 依赖检查
        DEPENDENCY_CHECK: true
    },
    // 日志配置
    LOG_CONFIG: {
        LOG_FILE: '../Logs/auto_trigger.log',
        LOG_LEVEL: 'INFO',
        MAX_LOG_SIZE: 10 * 1024 * 1024, // 10MB
        LOG_ROTATION: true
    }
};

/**
 * 智能日志管理器
 */
class SmartLogger {
    constructor() {
        this.logFile = path.resolve(CONFIG.PROJECT_ROOT, CONFIG.LOG_CONFIG.LOG_FILE);
        this.logDir = path.dirname(this.logFile);
        this.ensureLogDir();
    }

    ensureLogDir() {
        if (!fs.existsSync(this.logDir)) {
            fs.mkdirSync(this.logDir, { recursive: true });
        }
    }

    getTimestamp() {
        return new Date().toISOString().replace('T', ' ').substring(0, 23);
    }

    shouldLog(level) {
        const levels = { DEBUG: 0, INFO: 1, WARNING: 2, ERROR: 3 };
        return levels[level] >= levels[CONFIG.LOG_CONFIG.LOG_LEVEL];
    }

    rotateLog() {
        if (!CONFIG.LOG_CONFIG.LOG_ROTATION) return;

        try {
            const stats = fs.statSync(this.logFile);
            if (stats.size >= CONFIG.LOG_CONFIG.MAX_LOG_SIZE) {
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                const backupFile = this.logFile.replace('.log', `.${timestamp}.log`);
                fs.renameSync(this.logFile, backupFile);
                this.info(`日志已轮转: ${backupFile}`);
            }
        } catch (error) {
            console.error(`日志轮转失败: ${error.message}`);
        }
    }

    log(message, level = 'INFO') {
        if (!this.shouldLog(level)) return;

        const timestamp = this.getTimestamp();
        const logMessage = `[${timestamp}] [${level}] ${message}\n`;

        // 输出到控制台
        if (level === 'ERROR') {
            console.error(logMessage.trim());
        } else {
            console.log(logMessage.trim());
        }

        // 写入日志文件
        try {
            this.rotateLog();
            fs.appendFileSync(this.logFile, logMessage, 'utf8');
        } catch (error) {
            console.error(`写入日志失败: ${error.message}`);
        }
    }

    debug(message) { this.log(message, 'DEBUG'); }
    info(message) { this.log(message, 'INFO'); }
    warning(message) { this.log(message, 'WARNING'); }
    error(message) { this.log(message, 'ERROR'); }
    success(message) { this.log(message, 'SUCCESS'); }
}

/**
 * 文件变更分析器
 */
class FileChangeAnalyzer {
    constructor(logger) {
        this.logger = logger;
        this.fileHashes = new Map();
        this.dependencyGraph = new Map();
        this.initializeFileHashes();
    }

    /**
     * 初始化文件哈希缓存
     */
    initializeFileHashes() {
        CONFIG.WATCH_CONFIG.WATCH_DIRS.forEach(dir => {
            const fullPath = path.resolve(CONFIG.PROJECT_ROOT, dir);
            if (fs.existsSync(fullPath)) {
                this.scanDirectory(fullPath);
            }
        });
        this.logger.info(`已初始化 ${this.fileHashes.size} 个文件的哈希缓存`);
    }

    /**
     * 扫描目录并计算文件哈希
     */
    scanDirectory(dir) {
        const files = this.getAllFiles(dir);
        files.forEach(file => {
            if (this.shouldWatchFile(file)) {
                this.updateFileHash(file);
            }
        });
    }

    /**
     * 获取目录下所有文件
     */
    getAllFiles(dir) {
        const files = [];
        const items = fs.readdirSync(dir);
        
        items.forEach(item => {
            const fullPath = path.join(dir, item);
            const stat = fs.statSync(fullPath);
            
            if (stat.isDirectory()) {
                files.push(...this.getAllFiles(fullPath));
            } else if (stat.isFile()) {
                files.push(fullPath);
            }
        });
        
        return files;
    }

    /**
     * 判断是否应该监控文件
     */
    shouldWatchFile(filePath) {
        const ext = path.extname(filePath);
        const relativePath = path.relative(CONFIG.PROJECT_ROOT, filePath);
        
        // 检查扩展名
        if (!CONFIG.WATCH_CONFIG.WATCH_EXTENSIONS.includes(ext)) {
            return false;
        }
        
        // 检查忽略模式
        return !CONFIG.WATCH_CONFIG.IGNORE_PATTERNS.some(pattern => {
            const regex = new RegExp(pattern.replace(/\*\*/g, '.*').replace(/\*/g, '[^/]*'));
            return regex.test(relativePath);
        });
    }

    /**
     * 更新文件哈希
     */
    updateFileHash(filePath) {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const hash = crypto.createHash('md5').update(content).digest('hex');
            this.fileHashes.set(filePath, hash);
            return hash;
        } catch (error) {
            this.logger.error(`计算文件哈希失败 ${filePath}: ${error.message}`);
            return null;
        }
    }

    /**
     * 检查文件是否真的发生了变化
     */
    hasFileChanged(filePath) {
        const currentHash = this.updateFileHash(filePath);
        const previousHash = this.fileHashes.get(filePath);
        
        if (previousHash && currentHash !== previousHash) {
            this.logger.debug(`文件内容变化检测到: ${filePath}`);
            return true;
        }
        
        return false;
    }

    /**
     * 分析文件依赖关系
     */
    analyzeDependencies(filePath) {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const dependencies = [];
            
            // JavaScript 依赖分析
            if (path.extname(filePath) === '.js') {
                // import/require 语句
                const importRegex = /(?:import\s+.*?\s+from\s+['"`]([^'"`]+)['"`]|require\s*\(\s*['"`]([^'"`]+)['"`]\s*\))/g;
                let match;
                while ((match = importRegex.exec(content)) !== null) {
                    const depPath = match[1] || match[2];
                    if (depPath && !depPath.startsWith('.')) {
                        dependencies.push(depPath);
                    }
                }
            }
            
            // CSS 依赖分析
            if (path.extname(filePath) === '.css') {
                const importRegex = /@import\s+['"`]([^'"`]+)['"`]/g;
                let match;
                while ((match = importRegex.exec(content)) !== null) {
                    dependencies.push(match[1]);
                }
            }
            
            // HTML 依赖分析
            if (path.extname(filePath) === '.html') {
                const scriptRegex = /<script[^>]*src\s*=\s*['"`]([^'"`]+)['"`]/g;
                const linkRegex = /<link[^>]*href\s*=\s*['"`]([^'"`]+)['"`]/g;
                
                let match;
                while ((match = scriptRegex.exec(content)) !== null) {
                    dependencies.push(match[1]);
                }
                while ((match = linkRegex.exec(content)) !== null) {
                    dependencies.push(match[1]);
                }
            }
            
            this.dependencyGraph.set(filePath, dependencies);
            return dependencies;
        } catch (error) {
            this.logger.error(`分析文件依赖失败 ${filePath}: ${error.message}`);
            return [];
        }
    }

    /**
     * 获取受影响的文件列表
     */
    getAffectedFiles(changedFile) {
        const affected = [changedFile];
        const dependencies = this.dependencyGraph.get(changedFile) || [];
        
        // 简单的依赖反向查找
        this.dependencyGraph.forEach((deps, file) => {
            if (deps.includes(changedFile)) {
                affected.push(file);
            }
        });
        
        return affected;
    }
}

/**
 * 更新队列管理器
 */
class UpdateQueueManager {
    constructor(logger) {
        this.logger = logger;
        this.updateQueue = [];
        this.processingUpdates = new Set();
        this.isProcessing = false;
    }

    /**
     * 添加更新任务到队列
     */
    addUpdateTask(filePath, priority = 'normal') {
        if (this.updateQueue.length >= CONFIG.UPDATE_CONFIG.MAX_QUEUE_SIZE) {
            this.logger.warning(`更新队列已满，丢弃任务: ${filePath}`);
            return false;
        }

        const task = {
            id: Date.now() + Math.random(),
            filePath,
            priority,
            timestamp: new Date(),
            retryCount: 0
        };

        // 根据优先级插入队列
        if (priority === 'high') {
            this.updateQueue.unshift(task);
        } else {
            this.updateQueue.push(task);
        }

        this.logger.debug(`添加更新任务: ${filePath} (优先级: ${priority})`);
        
        // 启动处理循环
        this.processQueue();
        return true;
    }

    /**
     * 处理更新队列
     */
    async processQueue() {
        if (this.isProcessing || this.updateQueue.length === 0) {
            return;
        }

        this.isProcessing = true;

        while (this.updateQueue.length > 0 && this.processingUpdates.size < CONFIG.UPDATE_CONFIG.MAX_CONCURRENT_UPDATES) {
            const task = this.updateQueue.shift();
            this.processUpdateTask(task);
        }

        this.isProcessing = false;
    }

    /**
     * 处理单个更新任务
     */
    async processUpdateTask(task) {
        const { filePath, id } = task;
        this.processingUpdates.add(id);

        try {
            this.logger.info(`开始处理更新任务: ${filePath}`);
            
            // 执行更新操作
            const success = await this.executeUpdate(filePath);
            
            if (success) {
                this.logger.success(`更新任务完成: ${filePath}`);
            } else {
                this.logger.error(`更新任务失败: ${filePath}`);
                
                // 重试机制
                if (task.retryCount < 3) {
                    task.retryCount++;
                    this.updateQueue.unshift(task);
                    this.logger.warning(`重试更新任务: ${filePath} (第${task.retryCount}次)`);
                }
            }
        } catch (error) {
            this.logger.error(`处理更新任务异常 ${filePath}: ${error.message}`);
        } finally {
            this.processingUpdates.delete(id);
            
            // 继续处理队列
            setTimeout(() => this.processQueue(), 100);
        }
    }

    /**
     * 执行更新操作
     */
    async executeUpdate(filePath) {
        try {
            const relativePath = path.relative(CONFIG.PROJECT_ROOT, filePath);
            const ext = path.extname(filePath);
            
            // 调用更新触发器脚本
            const triggerScript = path.resolve(CONFIG.PROJECT_ROOT, CONFIG.UPDATE_CONFIG.TRIGGER_SCRIPT);
            if (fs.existsSync(triggerScript)) {
                await this.execCommand(`bash "${triggerScript}" "${relativePath}" "${ext}"`);
            }
            
            // 如果是 JavaScript 文件，调用增强更新管理器
            if (ext === '.js') {
                const enhancedManager = path.resolve(CONFIG.PROJECT_ROOT, CONFIG.UPDATE_CONFIG.ENHANCED_MANAGER);
                if (fs.existsSync(enhancedManager)) {
                    await this.execCommand(`node "${enhancedManager}" --update-file "${relativePath}"`);
                }
            }
            
            return true;
        } catch (error) {
            this.logger.error(`执行更新失败: ${error.message}`);
            return false;
        }
    }

    /**
     * 执行命令
     */
    execCommand(command) {
        return new Promise((resolve, reject) => {
            exec(command, { cwd: CONFIG.PROJECT_ROOT }, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    resolve({ stdout, stderr });
                }
            });
        });
    }

    /**
     * 获取队列状态
     */
    getQueueStatus() {
        return {
            queueLength: this.updateQueue.length,
            processingCount: this.processingUpdates.size,
            isProcessing: this.isProcessing
        };
    }
}

/**
 * 主智能更新触发器类
 */
class SmartAutoUpdateTrigger {
    constructor() {
        this.logger = new SmartLogger();
        this.analyzer = new FileChangeAnalyzer(this.logger);
        this.queueManager = new UpdateQueueManager(this.logger);
        this.watcher = null;
        this.debounceTimers = new Map();
        this.batchTimers = new Map();
        this.pendingUpdates = new Set();
    }

    /**
     * 启动智能更新触发器
     */
    async start() {
        try {
            this.logger.info('启动智能自动更新触发器...');
            
            // 初始化文件监控
            await this.initializeWatcher();
            
            // 设置信号处理
            this.setupSignalHandlers();
            
            this.logger.success('智能自动更新触发器已启动');
            this.logger.info(`监控目录: ${CONFIG.WATCH_CONFIG.WATCH_DIRS.join(', ')}`);
            this.logger.info(`监控文件类型: ${CONFIG.WATCH_CONFIG.WATCH_EXTENSIONS.join(', ')}`);
            
        } catch (error) {
            this.logger.error(`启动失败: ${error.message}`);
            process.exit(1);
        }
    }

    /**
     * 初始化文件监控器
     */
    async initializeWatcher() {
        const watchPaths = CONFIG.WATCH_CONFIG.WATCH_DIRS.map(dir => 
            path.resolve(CONFIG.PROJECT_ROOT, dir)
        );

        this.watcher = chokidar.watch(watchPaths, {
            ignored: CONFIG.WATCH_CONFIG.IGNORE_PATTERNS,
            persistent: true,
            ignoreInitial: true,
            awaitWriteFinish: {
                stabilityThreshold: 1000,
                pollInterval: 100
            }
        });

        // 监听文件变化
        this.watcher.on('change', (filePath) => this.handleFileChange(filePath, 'change'));
        this.watcher.on('add', (filePath) => this.handleFileChange(filePath, 'add'));
        this.watcher.on('unlink', (filePath) => this.handleFileChange(filePath, 'unlink'));

        // 监控器错误处理
        this.watcher.on('error', (error) => {
            this.logger.error(`文件监控错误: ${error.message}`);
        });

        this.logger.info('文件监控器已初始化');
    }

    /**
     * 处理文件变化
     */
    handleFileChange(filePath, eventType) {
        try {
            // 检查是否应该处理此文件
            if (!this.analyzer.shouldWatchFile(filePath)) {
                return;
            }

            // 检查文件内容是否真的变化了
            if (eventType === 'change' && !this.analyzer.hasFileChanged(filePath)) {
                return;
            }

            this.logger.debug(`检测到文件${eventType}: ${filePath}`);

            // 防抖处理
            this.debounceFileUpdate(filePath);

        } catch (error) {
            this.logger.error(`处理文件变化失败 ${filePath}: ${error.message}`);
        }
    }

    /**
     * 防抖文件更新
     */
    debounceFileUpdate(filePath) {
        // 清除之前的定时器
        if (this.debounceTimers.has(filePath)) {
            clearTimeout(this.debounceTimers.get(filePath));
        }

        // 设置新的防抖定时器
        const timer = setTimeout(() => {
            this.processFileUpdate(filePath);
            this.debounceTimers.delete(filePath);
        }, CONFIG.WATCH_CONFIG.DEBOUNCE_DELAY);

        this.debounceTimers.set(filePath, timer);
    }

    /**
     * 处理文件更新
     */
    async processFileUpdate(filePath) {
        try {
            // 分析文件依赖
            if (CONFIG.UPDATE_CONFIG.DEPENDENCY_CHECK) {
                this.analyzer.analyzeDependencies(filePath);
            }

            // 获取受影响的文件
            const affectedFiles = this.analyzer.getAffectedFiles(filePath);
            
            // 添加到待处理集合
            affectedFiles.forEach(file => this.pendingUpdates.add(file));

            // 批处理更新
            this.batchUpdates();

        } catch (error) {
            this.logger.error(`处理文件更新失败 ${filePath}: ${error.message}`);
        }
    }

    /**
     * 批处理更新
     */
    batchUpdates() {
        // 清除之前的批处理定时器
        if (this.batchTimers.has('batch')) {
            clearTimeout(this.batchTimers.get('batch'));
        }

        // 设置批处理定时器
        const timer = setTimeout(() => {
            this.executeBatchUpdates();
            this.batchTimers.delete('batch');
        }, CONFIG.WATCH_CONFIG.BATCH_DELAY);

        this.batchTimers.set('batch', timer);
    }

    /**
     * 执行批处理更新
     */
    async executeBatchUpdates() {
        if (this.pendingUpdates.size === 0) {
            return;
        }

        const filesToUpdate = Array.from(this.pendingUpdates);
        this.pendingUpdates.clear();

        this.logger.info(`开始批处理更新，共 ${filesToUpdate.length} 个文件`);

        // 按优先级排序
        filesToUpdate.sort((a, b) => {
            const priorityA = this.getFilePriority(a);
            const priorityB = this.getFilePriority(b);
            return priorityB - priorityA;
        });

        // 添加到更新队列
        filesToUpdate.forEach(filePath => {
            const priority = this.getFilePriority(filePath);
            this.queueManager.addUpdateTask(filePath, priority);
        });

        // 自动优化
        if (CONFIG.UPDATE_CONFIG.AUTO_OPTIMIZE) {
            setTimeout(() => this.performAutoOptimization(), 10000);
        }
    }

    /**
     * 获取文件优先级
     */
    getFilePriority(filePath) {
        const ext = path.extname(filePath);
        const fileName = path.basename(filePath);
        
        // 高优先级文件
        if (fileName.includes('main') || fileName.includes('index') || fileName.includes('config')) {
            return 3;
        }
        
        // 中等优先级文件
        if (['.js', '.css'].includes(ext)) {
            return 2;
        }
        
        // 普通优先级
        return 1;
    }

    /**
     * 执行自动优化
     */
    async performAutoOptimization() {
        try {
            this.logger.info('执行自动优化...');
            
            // 调用优化脚本
            const optimizeScript = path.resolve(CONFIG.PROJECT_ROOT, '../Scripts/optimize_system.sh');
            if (fs.existsSync(optimizeScript)) {
                await this.queueManager.execCommand(`bash "${optimizeScript}"`);
                this.logger.success('自动优化完成');
            }
        } catch (error) {
            this.logger.error(`自动优化失败: ${error.message}`);
        }
    }

    /**
     * 设置信号处理器
     */
    setupSignalHandlers() {
        const gracefulShutdown = () => {
            this.logger.info('正在关闭智能更新触发器...');
            
            if (this.watcher) {
                this.watcher.close();
            }
            
            // 清理定时器
            this.debounceTimers.forEach(timer => clearTimeout(timer));
            this.batchTimers.forEach(timer => clearTimeout(timer));
            
            this.logger.info('智能更新触发器已关闭');
            process.exit(0);
        };

        process.on('SIGINT', gracefulShutdown);
        process.on('SIGTERM', gracefulShutdown);
        process.on('SIGQUIT', gracefulShutdown);
    }

    /**
     * 获取系统状态
     */
    getStatus() {
        const queueStatus = this.queueManager.getQueueStatus();
        return {
            isRunning: this.watcher && this.watcher.getWatched().size > 0,
            watchedPaths: this.watcher ? Array.from(this.watcher.getWatched().keys()) : [],
            pendingUpdates: this.pendingUpdates.size,
            debounceTimers: this.debounceTimers.size,
            ...queueStatus
        };
    }
}

// 主程序入口
async function main() {
    const trigger = new SmartAutoUpdateTrigger();
    
    // 处理命令行参数
    const args = process.argv.slice(2);
    if (args.includes('--status')) {
        console.log(JSON.stringify(trigger.getStatus(), null, 2));
        return;
    }
    
    if (args.includes('--help')) {
        console.log(`
MTSCOS 智能自动更新触发器

用法:
  node smart_auto_trigger.js [选项]

选项:
  --status    显示当前状态
  --help      显示帮助信息

功能:
  - 智能文件变更检测
  - 自动触发更新机制
  - 依赖关系分析
  - 增量更新优化
  - 更新队列管理
        `);
        return;
    }
    
    // 启动触发器
    await trigger.start();
}

// 如果直接运行此脚本
if (require.main === module) {
    main().catch(error => {
        console.error('启动失败:', error.message);
        process.exit(1);
    });
}

module.exports = { SmartAutoUpdateTrigger, FileChangeAnalyzer, UpdateQueueManager, SmartLogger };