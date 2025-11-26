const fs = require('fs');
const path = require('path');
const { EnhancedLogger, LOG_LEVELS } = require('../Staging/Scripts/monitoring/enhanced-logger');
const DeepSeekAI = require('../JavaScript/deepseek-ai');
const LocalDeepSeekModel = require('../JavaScript/local-deepseek-model');
const configManager = require('../JavaScript/config-manager');
const EventEmitter = require('events');

// 临时注释掉不存在的模块导入
// const ModelAdapter = require('./model-adapter');
// const RepairReporter = require('./repair-reporter');
// const CodeQualityEvaluator = require('./code-quality-evaluator');
// const { AsyncQueue } = require('./utils/async-queue');

// 临时注释掉不存在的检测器导入
// const SecurityVulnerabilityDetector = require('./detectors/security-detector');
// const PerformanceIssueDetector = require('./detectors/performance-detector');
// const CodeQualityDetector = require('./detectors/code-quality-detector');
// const TypeScriptErrorDetector = require('./detectors/typescript-detector');
// const CSSIssueDetector = require('./detectors/css-detector');
// const HTMLIssueDetector = require('./detectors/html-detector');

// 临时定义空检测器类
const SecurityVulnerabilityDetector = class {};
const PerformanceIssueDetector = class {};
const CodeQualityDetector = class {};
const TypeScriptErrorDetector = class {};
const CSSIssueDetector = class {};

// 临时注释掉不存在的HTML问题检测器
// const HTMLIssueDetector = require('./detectors/html-detector');
const HTMLIssueDetector = class {};

// 临时注释掉不存在的策略模块导入
// const ContextAwareRepairStrategy = require('./strategies/context-aware-repair-strategy');
// const ProgressiveRepairStrategy = require('./strategies/progressive-repair-strategy');
// const SecurityRepairStrategy = require('./strategies/security-repair-strategy');
// const PerformanceOptimizationStrategy = require('./strategies/performance-optimization-strategy');
// const CodeRefactoringStrategy = require('./strategies/code-refactoring-strategy');
// const DependencyManagementStrategy = require('./strategies/dependency-management-strategy');

// 临时定义空策略类
const ContextAwareRepairStrategy = class { constructor() {} execute() {} };
const ProgressiveRepairStrategy = class { constructor() {} execute() {} };
const SecurityRepairStrategy = class { constructor() {} execute() {} };
const PerformanceOptimizationStrategy = class { constructor() {} execute() {} };
const CodeRefactoringStrategy = class { constructor() {} execute() {} };
const DependencyManagementStrategy = class { constructor() {} execute() {} };

/**
 * 修复引擎 V2 - 增强型多模型协作修复系统
 * 能够检测和修复JavaScript、TypeScript、CSS、HTML代码中的各种问题
 * 支持AI驱动修复、批量修复、并行处理和详细报告生成
 */
class RepairEngine extends EventEmitter {
    constructor(config = {}) {
        super();
        
        // 版本信息
        this.version = '2.0.0';
        
        // 默认配置 - 新增更多选项和支持更多文件类型
        this.defaultConfig = {
            deepseek: {
                apiKey: '',
                baseUrl: 'https://api.deepseek.com',
                model: 'deepseek-coder',
                maxTokens: 2048,  // 增加token限制
                temperature: 0.2,  // 降低温度以获得更精确的修复
                timeout: 60000     // 增加超时时间
            },
            // 新增：支持更多AI模型
            aiModels: {
                deepseek: { enabled: true, priority: 1 },
                gpt35: { enabled: false, priority: 2 },
                gpt4: { enabled: false, priority: 3 },
                claude: { enabled: false, priority: 4 },
                gemini: { enabled: false, priority: 5 }
            },
            // 新增：支持更多文件类型
            fileTypes: ['.js', '.jsx', '.ts', '.tsx', '.css', '.html'],
            cache: {
                enabled: true,
                maxSize: 500,   // 增加缓存大小
                ttl: 86400,     // 增加缓存有效期
                useRedis: false // 支持Redis缓存
            },
            logger: {
                level: 'info',
                format: 'json',
                enableFileLogging: true,
                logFilePath: './logs/repair-engine.log'
            },
            retry: {
                attempts: 5,    // 增加重试次数
                delay: 2000,    // 增加重试延迟
                maxDelay: 16000 // 增加最大重试延迟
            },
            // 新增：并行处理配置
            parallel: {
                enabled: true,
                maxConcurrent: 10,  // 增加并发处理数
                queueSize: 1000     // 增加队列大小
            },
            // 新增：修复策略配置
            repairStrategies: {
                auto: true,
                ai: true,
                security: true,
                performance: true,
                codeQuality: true,
                contextAware: true,
                progressive: true
            },
            // 新增：修复验证配置
            validation: {
                enabled: true,
                runTests: false,     // 支持运行测试验证修复
                checkSyntax: true,   // 检查语法正确性
                checkTypeScript: true, // 检查TypeScript类型
                checkSecurity: true,  // 检查安全性
                checkPerformance: true // 检查性能
            },
            // 新增：备份配置
            backup: {
                enabled: true,
                directory: './backups',
                format: 'timestamp', // 备份文件名格式
                keepDays: 7          // 保留备份天数
            },
            // 新增：报告配置
            reporting: {
                enabled: true,
                format: 'html', // 支持html、json、markdown格式
                directory: './reports'
            }
        };

        // 使用配置管理器加载配置
        this.config = {...this.defaultConfig, ...config};
        configManager.registerConfig('repairEngine', this.config);
        
        // 初始化日志器 - 支持文件日志
        const logTargets = [
            { write: (entry, message) => console.log(message) }
        ];
        
        if (this.config.logger.enableFileLogging) {
            logTargets.push({
                write: (entry, message) => {
                    const logDir = path.dirname(this.config.logger.logFilePath);
                    if (!fs.existsSync(logDir)) {
                        fs.mkdirSync(logDir, { recursive: true });
                    }
                    fs.appendFileSync(this.config.logger.logFilePath, message + '\n', 'utf8');
                }
            });
        }
        
        this.logger = new EnhancedLogger({
            level: LOG_LEVELS[this.config.logger.level.toUpperCase()] || LOG_LEVELS.INFO,
            targets: logTargets
        });
        
        // 初始化组件
        this.aiModels = {};
        this.components = {
            detectors: [],
            strategies: []
        };
        
        // 初始化修复统计信息
        this.repairStats = {
            filesScanned: 0,
            detectedIssues: 0,
            fixedIssues: 0,
            filesRepaired: 0,
            totalRepairs: 0,
            criticalIssues: 0,
            highIssues: 0,
            mediumIssues: 0,
            lowIssues: 0
        };
        
        // 保持向后兼容
        this.issueDetectors = this.components.detectors;
        this.repairStrategies = this.components.strategies;
        
        // 临时注释掉不存在模块的初始化
        // this.modelAdapter = new ModelAdapter(this.config);
        // this.codeQualityEvaluator = new CodeQualityEvaluator();
        // this.repairReporter = new RepairReporter(this.config);
        // this.taskQueue = new AsyncQueue({
        this.modelAdapter = null;
        this.codeQualityEvaluator = null;
        this.repairReporter = null;
        this.taskQueue = null;
            // concurrency: this.config.parallel.maxConcurrent,
            // queueSize: this.config.parallel.queueSize
        // });
        
        // 新增：修复统计信息
        this.stats = {
            totalFiles: 0,
            filesWithIssues: 0,
            totalIssues: 0,
            fixedIssues: 0,
            failedIssues: 0,
            repairTime: 0,
            successfulRepairs: 0,
            failedRepairs: 0
        };
        
        // 初始化状态
        this.isInitialized = false;
        this.cache = new Map();
        this.backupMap = new Map();
        
        // 记录初始化日志
        this.logger.info('REPAIR_ENGINE', `修复引擎 V${this.version} 初始化`, {
            config: this.config,
            time: new Date().toISOString()
        });
        
        // 触发初始化事件
        this.emit('initialized', { version: this.version });
    }

    /**
     * 初始化修复引擎
     */
    async initialize() {
        try {
            this.emit('init_start', { time: new Date().toISOString() });
            this.logger.info('REPAIR_ENGINE', '开始初始化修复引擎 V2');
            
            // 初始化文件系统相关目录
            await this.initDirectories();
            
            // 初始化AI模型
            await this.initializeModels();

            // 注册默认的问题检测器和修复策略
            this.registerDefaultDetectors();
            this.registerDefaultStrategies();

            // 加载缓存
            await this.loadCache();
            
            this.isInitialized = true;
            
            this.logger.info('REPAIR_ENGINE', '修复引擎 V2 初始化完成', {
                stats: {
                    detectors: this.components.detectors.length,
                    strategies: this.components.strategies.length,
                    aiModels: Object.keys(this.aiModels).length
                }
            });
            
            this.emit('init_complete', {
                time: new Date().toISOString(),
                version: this.version,
                stats: {
                    detectors: this.components.detectors.length,
                    strategies: this.components.strategies.length
                }
            });
            
            return { success: true };
        } catch (error) {
            this.logger.error('REPAIR_ENGINE', '修复引擎初始化失败', {
                error: error.message,
                stack: error.stack
            });
            
            this.emit('init_error', {
                time: new Date().toISOString(),
                error: error.message
            });
            
            return { 
                success: false, 
                error: '修复引擎初始化失败',
                errorType: 'InitializationError',
                details: error.message
            };
        }
    }

    /**
     * 初始化文件系统相关目录
     */
    async initDirectories() {
        try {
            // 确保日志目录存在
            if (this.config.logger.enableFileLogging) {
                const logDir = path.dirname(this.config.logger.logFilePath);
                if (!fs.existsSync(logDir)) {
                    fs.mkdirSync(logDir, { recursive: true });
                }
            }
            
            // 确保备份目录存在
            if (this.config.backup.enabled) {
                if (!fs.existsSync(this.config.backup.directory)) {
                    fs.mkdirSync(this.config.backup.directory, { recursive: true });
                }
            }
            
            // 确保报告目录存在
            if (this.config.reporting.enabled) {
                if (!fs.existsSync(this.config.reporting.directory)) {
                    fs.mkdirSync(this.config.reporting.directory, { recursive: true });
                }
            }
            
            this.logger.debug('REPAIR_ENGINE', '文件系统目录初始化完成');
        } catch (error) {
            this.logger.error('REPAIR_ENGINE', '文件系统目录初始化失败', { error: error.message });
            throw error;
        }
    }
    
    /**
     * 初始化AI模型
     */
    async initializeModels() {
        try {
            // 临时修复：如果没有模型适配器，使用传统方式初始化模型
            if (!this.modelAdapter) {
                this.aiModels = {};
                // 这里可以添加传统方式的模型初始化代码
            } else {
                await this.modelAdapter.initModels();
                this.aiModels = this.modelAdapter.models;
            }
            
            this.logger.info('REPAIR_ENGINE', 'AI模型初始化完成', {
                models: Object.keys(this.aiModels).map(key => ({
                    name: key,
                    enabled: this.aiModels[key].enabled,
                    type: this.aiModels[key].type
                }))
            });
        } catch (error) {
            // 模型适配器初始化失败，回退到传统方式
            this.logger.warn('REPAIR_ENGINE', '模型适配器初始化失败，使用传统方式初始化模型', {
                error: error.message
            });
            
            // 初始化云端DeepSeek模型
            this.aiModels.cloud = new DeepSeekAI(this.config.deepseek);
            await this.aiModels.cloud.init();

            // 尝试初始化本地模型
            try {
                this.aiModels.local = new LocalDeepSeekModel(this.config);
                await this.aiModels.local.initialize();
            } catch (localError) {
                // 本地模型加载失败，使用云端模型即可
                this.logger.warn('REPAIR_ENGINE', '本地模型加载失败，仅使用云端模型', {
                    error: localError.message
                });
            }
        }
    }
    
    /**
     * 加载缓存
     */
    async loadCache() {
        try {
            if (this.config.cache.enabled) {
                // 这里可以实现从文件或Redis加载缓存的逻辑
                this.logger.debug('REPAIR_ENGINE', '缓存加载完成');
            }
        } catch (error) {
            this.logger.warning('REPAIR_ENGINE', '缓存加载失败，将使用新缓存', { error: error.message });
            this.cache = new Map();
        }
    }
    
    /**
     * 检查模型健康状态
     */
    async checkModelHealth(modelInfo) {
        try {
            const { model, modelType } = modelInfo;
            
            // 检查本地模型是否就绪
            if (modelType === 'local' && model.isReady) {
                return await model.isReady();
            }
            
            // 检查云端模型是否配置正确
            if (modelType === 'cloud' && model.isConfigured) {
                return await model.isConfigured();
            }
            
            // 默认健康状态为true
            return true;
        } catch (error) {
            this.logger.warn('REPAIR_ENGINE', `模型 ${modelInfo.modelType} 健康检查失败`, error);
            return false;
        }
    }

    /**
     * 注册默认的问题检测器
     */
    registerDefaultDetectors() {
        try {
            this.logger.info('REPAIR_ENGINE', '开始注册默认检测器');
            
            // 语法错误检测器（增强版）
            this.registerDetector({
            name: 'SyntaxErrorDetector',
            priority: 10,
            detect: async (filePath, content) => {
                const issues = [];
                try {
                    // 简单的语法检查
                    new Function(content);
                } catch (error) {
                    if (error instanceof SyntaxError) {
                        issues.push({
                            type: 'SyntaxError',
                            file: filePath,
                            line: error.lineNumber || 0,
                            column: error.columnNumber || 0,
                            message: error.message,
                            severity: 'high',
                            context: this.extractCodeContext(content, error.lineNumber || 0)
                        });
                    }
                }
                return issues;
            }
        });

        // 代码质量检测器（新增）
        this.registerDetector({
            name: 'CodeQualityDetector',
            priority: 8,
            detect: async (filePath, content) => {
                const issues = [];
                // 代码质量检测规则
                const patterns = [
                    { regex: /const\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*=\s*[^;]+;\s*(?!.*\1\s*=|.*\1\s*\(|.*\1\[)/g, message: '未使用的常量' },
                    { regex: /let\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*=\s*[^;]+;\s*(?!.*\1\s*=|.*\1\s*\(|.*\1\[|.*\1\.|.*\1\s*\+)/g, message: '未使用的变量' },
                    { regex: /function\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*\([^)]*\)\s*\{[^}]*\}\s*(?!.*\1\s*\()/g, message: '未使用的函数' },
                    { regex: /\bconsole\.(log|warn|info|debug|error)\s*\([^)]*\)/g, message: '控制台日志语句' },
                    { regex: /\bdebugger\b/g, message: '调试断点语句' }
                ];

                let match;
                for (const pattern of patterns) {
                    pattern.regex.lastIndex = 0;
                    while ((match = pattern.regex.exec(content)) !== null) {
                        const line = content.substring(0, match.index).split('\n').length;
                        issues.push({
                            type: 'CodeQuality',
                            file: filePath,
                            line: line,
                            column: 0,
                            message: pattern.message,
                            severity: 'low'
                        });
                    }
                }
                return issues;
            }
        });

        // 安全漏洞检测器（增强版）
        this.registerDetector({
            name: 'SecurityVulnerabilityDetector',
            priority: 15,
            detect: async (filePath, content) => {
                const issues = [];
                // 安全漏洞检测规则
                const securityPatterns = [
                    { regex: /eval\s*\(/g, message: '使用eval函数存在安全风险' },
                    { regex: /new\s+Function\s*\(/g, message: '使用Function构造函数存在安全风险' },
                    { regex: /process\.env\.[A-Za-z0-9_]+/g, message: '直接使用环境变量可能导致信息泄露' },
                    { regex: /['"`]([a-zA-Z0-9]{16,})['"`]/g, message: '可能存在硬编码密钥或密码' },
                    { regex: /\b(?:password|secret|key|token|api[_-]key)\s*[:=]\s*['"`]([^'"]+)['"`]/gi, message: '可能存在硬编码敏感信息' },
                    { regex: /\b(?:http:|ftp:)\/\//g, message: '使用不安全的HTTP协议' },
                    { regex: /\bexec\s*\(|\bspawn\s*\(|\bfork\s*\(/g, message: '使用系统命令执行可能存在安全风险' },
                    { regex: /\b(?:eval|Function)\s*\(/g, message: '动态代码执行可能存在安全风险' }
                ];

                let match;
                for (const pattern of securityPatterns) {
                    pattern.regex.lastIndex = 0;
                    while ((match = pattern.regex.exec(content)) !== null) {
                        const line = content.substring(0, match.index).split('\n').length;
                        issues.push({
                            type: 'SecurityVulnerability',
                            file: filePath,
                            line: line,
                            column: match.index - content.lastIndexOf('\n', match.index),
                            message: pattern.message,
                            severity: 'high',
                            context: this.extractCodeContext(content, line)
                        });
                    }
                }
                return issues;
            }
        });

        // 性能问题检测器（新增）
        this.registerDetector({
            name: 'PerformanceIssueDetector',
            priority: 7,
            detect: async (filePath, content) => {
                const issues = [];
                // 性能问题检测规则
                const performancePatterns = [
                    { regex: /for\s*\([^)]*\)\s*\{[^}]*\s*\.push\s*\(/g, message: '在循环中使用push可能导致性能问题' },
                    { regex: /for\s*\([^)]*\)\s*\{[^}]*\s*\.splice\s*\(/g, message: '在循环中使用splice可能导致性能问题' },
                    { regex: /\bJSON\.parse\s*\([^)]*\)\s*\+\s*\bJSON\.stringify\s*\(/g, message: '不必要的JSON序列化和反序列化' },
                    { regex: /\b(?:setTimeout|setInterval)\s*\([^)]*\s*0\s*\)/g, message: '使用0ms延迟可能导致不必要的事件循环' },
                    { regex: /\b(?:document\.querySelector|document\.getElementById)\s*\(/g, message: '在循环中频繁DOM操作可能导致性能问题' },
                    { regex: /\b(?:Array\.prototype\.slice\s*\(\)\s*\.forEach|Array\.prototype\.filter\s*\(\)\s*\.map)/g, message: '链式数组操作可能导致性能问题' },
                    { regex: /\b(?:new\s+Array\s*\(\d+\)|\[\s*\])\s*\.concat\s*\(/g, message: '使用concat可能导致不必要的数组复制' }
                ];

                let match;
                for (const pattern of performancePatterns) {
                    pattern.regex.lastIndex = 0;
                    while ((match = pattern.regex.exec(content)) !== null) {
                        const line = content.substring(0, match.index).split('\n').length;
                        issues.push({
                            type: 'PerformanceIssue',
                            file: filePath,
                            line: line,
                            column: match.index - content.lastIndexOf('\n', match.index),
                            message: pattern.message,
                            severity: 'medium',
                            context: this.extractCodeContext(content, line)
                        });
                    }
                }
                return issues;
            }
        });

        // 依赖问题检测器（新增）
        this.registerDetector({
            name: 'DependencyIssueDetector',
            priority: 6,
            detect: async (filePath, content) => {
                const issues = [];
                // 依赖问题检测规则
                const dependencyPatterns = [
                    { regex: /require\s*\(["']\.\.\//g, message: '使用相对路径依赖可能导致模块解析问题' },
                    { regex: /import\s+[^\s]+\s+from\s+["']\.\.\//g, message: '使用相对路径依赖可能导致模块解析问题' },
                    { regex: /require\s*\(["'][^"']+["']\)\s*\.\s*[a-zA-Z_$][a-zA-Z0-9_$]*/g, message: '直接访问模块导出可能导致未定义错误' },
                    { regex: /\b(?:module\.exports|exports\.)\s*=\s*[^;]+\s*;/g, message: 'CommonJS和ES模块混合使用可能导致问题' }
                ];

                let match;
                for (const pattern of dependencyPatterns) {
                    pattern.regex.lastIndex = 0;
                    while ((match = pattern.regex.exec(content)) !== null) {
                        const line = content.substring(0, match.index).split('\n').length;
                        issues.push({
                            type: 'DependencyIssue',
                            file: filePath,
                            line: line,
                            column: match.index - content.lastIndexOf('\n', match.index),
                            message: pattern.message,
                            severity: 'medium',
                            context: this.extractCodeContext(content, line)
                        });
                    }
                }
                return issues;
            }
        });

        // 最佳实践检测器（新增）
        this.registerDetector({
            name: 'BestPracticeDetector',
            priority: 5,
            detect: async (filePath, content) => {
                const issues = [];
                // 最佳实践检测规则
                const bestPracticePatterns = [
                    { regex: /var\s+/g, message: '使用var声明变量可能导致作用域问题，建议使用let或const' },
                    { regex: /function\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*\([^)]*\)\s*\{[^}]*\s*return\s*[^;]+;/g, message: '函数缺少return语句可能导致未定义返回值' },
                    { regex: /\bif\s*\([^)]*\)\s*[^\n\r{]/g, message: 'if语句缺少花括号可能导致逻辑错误' },
                    { regex: /\belse\s*[^\n\r{]/g, message: 'else语句缺少花括号可能导致逻辑错误' },
                    { regex: /\bfor\s*\([^)]*\)\s*[^\n\r{]/g, message: 'for循环缺少花括号可能导致逻辑错误' },
                    { regex: /\bwhile\s*\([^)]*\)\s*[^\n\r{]/g, message: 'while循环缺少花括号可能导致逻辑错误' },
                    { regex: /\b(?:let|const)\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*=[^;]+\s*==\s*[^;]+/g, message: '赋值和比较运算符混用可能导致逻辑错误' }
                ];

                let match;
                for (const pattern of bestPracticePatterns) {
                    pattern.regex.lastIndex = 0;
                    while ((match = pattern.regex.exec(content)) !== null) {
                        const line = content.substring(0, match.index).split('\n').length;
                        issues.push({
                            type: 'BestPractice',
                            file: filePath,
                            line: line,
                            column: match.index - content.lastIndexOf('\n', match.index),
                            message: pattern.message,
                            severity: 'low',
                            context: this.extractCodeContext(content, line)
                        });
                    }
                }
                return issues;
            }
        });

        // 反模式检测器（新增）
        this.registerDetector({
            name: 'AntiPatternDetector',
            priority: 4,
            detect: async (filePath, content) => {
                const issues = [];
                // 反模式检测规则
                const antiPatterns = [
                    { regex: /if\s*\(([^)]+)\)\s*\{[^}]*\}\s*else\s*\{\s*if\s*\(([^)]+)\)\s*\{/g, message: '嵌套if-else语句建议使用switch语句或重构' },
                    { regex: /for\s*\(\s*let\s+i\s*=\s*0\s*;\s*i\s*<\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\.length\s*;\s*i\+\+\)\s*\{/g, message: '在循环条件中重复获取数组长度可能影响性能' },
                    { regex: /try\s*\{[^}]*\}\s*catch\s*\([^)]*\)\s*\{\s*\}/g, message: '空的catch块会隐藏错误信息' },
                    { regex: /\bconsole\.(log|warn|info|debug|error)\s*\(/g, message: '生产环境中应移除或禁用控制台日志' },
                    { regex: /\bdebugger\b/g, message: '生产环境中应移除调试断点' },
                    { regex: /\b(?:Math\.random\s*\(\)\s*<\s*0\.5|Math\.floor\s*\(Math\.random\s*\(\)\s*\*\s*2\))/g, message: '随机数生成可能不够安全或不够均匀' }
                ];

                let match;
                for (const pattern of antiPatterns) {
                    pattern.regex.lastIndex = 0;
                    while ((match = pattern.regex.exec(content)) !== null) {
                        const line = content.substring(0, match.index).split('\n').length;
                        issues.push({
                            type: 'AntiPattern',
                            file: filePath,
                            line: line,
                            column: match.index - content.lastIndexOf('\n', match.index),
                            message: pattern.message,
                            severity: 'medium',
                            context: this.extractCodeContext(content, line)
                        });
                    }
                }
                return issues;
            }
        });

        // 错误模式检测器（新增）
        this.registerDetector({
            name: 'ErrorPatternDetector',
            priority: 12,
            detect: async (filePath, content) => {
                const issues = [];
                // 错误模式检测规则
                const errorPatterns = [
                    { regex: /throw\s*[^;]+;/g, message: '抛出错误应使用Error对象' },
                    { regex: /catch\s*\(([^)]+)\)\s*\{/g, message: 'catch块应捕获具体的错误类型' },
                    { regex: /\b(?:try\s*\{[^}]*\}\s*catch\s*\([^)]*\)\s*\{\s*return\s*[^;]+;\s*\})/g, message: '在catch块中直接返回可能隐藏错误信息' },
                    { regex: /\b(?:Promise\s*\.resolve\s*\(|Promise\s*\.reject\s*\()/g, message: 'Promise应使用new Promise构造函数或async/await' },
                    { regex: /\b(?:setTimeout|setInterval)\s*\([^)]*\s*function\s*\([^)]*\)\s*\{/g, message: '使用箭头函数可以避免this指向问题' }
                ];

                let match;
                for (const pattern of errorPatterns) {
                    pattern.regex.lastIndex = 0;
                    while ((match = pattern.regex.exec(content)) !== null) {
                        const line = content.substring(0, match.index).split('\n').length;
                        issues.push({
                            type: 'ErrorPattern',
                            file: filePath,
                            line: line,
                            column: match.index - content.lastIndexOf('\n', match.index),
                            message: pattern.message,
                            severity: 'medium',
                            context: this.extractCodeContext(content, line)
                        });
                    }
                }
                return issues;
            }
        });

        // 逻辑错误检测器（增强版）
        this.registerDetector({
            name: 'LogicErrorDetector',
            priority: 9,
            detect: async (filePath, content) => {
                const issues = [];
                // 逻辑错误检测规则
                const patterns = [
                    { regex: /if\s*\([^)]*\)\s*\{\s*\}\s*(else\s*\{\s*\})?/g, message: '空的条件语句块' },
                    { regex: /for\s*\([^)]*\)\s*\{\s*\}/g, message: '空的for循环' },
                    { regex: /while\s*\([^)]*\)\s*\{\s*\}/g, message: '空的while循环' },
                    { regex: /do\s*\{\s*\}\s*while\s*\([^)]*\)/g, message: '空的do-while循环' },
                    { regex: /\bif\s*\(\s*(true|false)\s*\)/g, message: '条件始终为真/假的if语句' },
                    { regex: /\bfor\s*\([^)]*\)\s*\{[^}]*break\s*;[^}]*\}/g, message: '无条件中断的循环' },
                    { regex: /\breturn\s*([^;]+);\s*[^}]*\}/g, message: 'return语句后的无效代码' }
                ];

                let match;
                for (const pattern of patterns) {
                    pattern.regex.lastIndex = 0;
                    while ((match = pattern.regex.exec(content)) !== null) {
                        const line = content.substring(0, match.index).split('\n').length;
                        issues.push({
                            type: 'LogicError',
                            file: filePath,
                            line: line,
                            column: 0,
                            message: pattern.message,
                            severity: 'medium',
                            context: this.extractCodeContext(content, line)
                        });
                    }
                }
                return issues;
            }
        });

        // 安全漏洞检测器（增强版）
        this.registerDetector({
            name: 'SecurityVulnerabilityDetector',
            priority: 10,
            detect: async (filePath, content) => {
                const issues = [];
                // 安全漏洞检测规则
                const patterns = [
                    { regex: /(?<!\/\/\s*)eval\s*\([^)]*\)/g, message: '使用eval函数可能导致安全漏洞', severity: 'high' },
                    { regex: /(?<!\/\/\s*)new\s+Function\s*\([^)]*\)/g, message: '使用Function构造函数可能导致安全漏洞', severity: 'high' },
                    { regex: /process\.env\.[A-Za-z0-9_]+/g, message: '直接使用环境变量可能导致安全问题', severity: 'medium' },
                    { regex: /(?<!\/\/\s*)require\s*\(\s*[^'"`][^)]*\)/g, message: '动态require可能导致安全问题', severity: 'high' },
                    { regex: /(?<!\/\/\s*)\bpassword\s*=\s*['"`][^'"]*['"`]/g, message: '硬编码密码可能导致安全漏洞', severity: 'critical' },
                    { regex: /(?<!\/\/\s*)\bapi[_-]?key\s*=\s*['"`][^'"]*['"`]/i, message: '硬编码API密钥可能导致安全漏洞', severity: 'critical' },
                    { regex: /(?<!\/\/\s*)\bsecret\s*=\s*['"`][^'"]*['"`]/i, message: '硬编码密钥可能导致安全漏洞', severity: 'critical' },
                    { regex: /\bXMLHttpRequest\s*\(\)\s*\.open\s*\(['"]\w+['"],\s*[^'"]+/g, message: '不安全的XMLHttpRequest调用', severity: 'medium' }
                ];

                let match;
                for (const pattern of patterns) {
                    pattern.regex.lastIndex = 0;
                    while ((match = pattern.regex.exec(content)) !== null) {
                        const line = content.substring(0, match.index).split('\n').length;
                        issues.push({
                            type: 'SecurityVulnerability',
                            file: filePath,
                            line: line,
                            column: 0,
                            message: pattern.message,
                            severity: pattern.severity || 'high',
                            context: this.extractCodeContext(content, line)
                        });
                    }
                }
                return issues;
            }
        });

        // 性能问题检测器（新增）
        this.registerDetector({
            name: 'PerformanceDetector',
            priority: 7,
            detect: async (filePath, content) => {
                const issues = [];
                // 性能问题检测规则
                const patterns = [
                    { regex: /\bArray\.prototype\.slice\s*\.call\s*\([^)]*\)/g, message: '频繁使用slice.call可能影响性能', severity: 'medium' },
                    { regex: /\bfor\s*\(\s*let\s+i\s*=\s*0;\s*i\s*<\s*(\w+)\.length;\s*i\+\+/g, message: '在循环条件中计算长度可能影响性能', severity: 'low' },
                    { regex: /\bJSON\.parse\s*\(\s*JSON\.stringify\s*\([^)]*\)\s*\)/g, message: '使用JSON.parse(JSON.stringify())进行深拷贝可能影响性能', severity: 'medium' },
                    { regex: /\b\w+\.innerHTML\s*=\s*[^;]+;/g, message: '直接操作innerHTML可能影响性能和安全', severity: 'medium' }
                ];

                let match;
                for (const pattern of patterns) {
                    pattern.regex.lastIndex = 0;
                    while ((match = pattern.regex.exec(content)) !== null) {
                        const line = content.substring(0, match.index).split('\n').length;
                        issues.push({
                            type: 'PerformanceIssue',
                            file: filePath,
                            line: line,
                            column: 0,
                            message: pattern.message,
                            severity: pattern.severity || 'medium'
                        });
                    }
                }
                return issues;
            }
        });
            
            this.logger.info('REPAIR_ENGINE', '默认检测器注册完成', {
                count: this.components.detectors.length,
                detectors: this.components.detectors.map(d => d.name)
            });
        } catch (error) {
            this.logger.error('REPAIR_ENGINE', '检测器注册失败', {
                error: error.message,
                stack: error.stack
            });
            throw error;
        }
    }

    /**
     * 注册默认的修复策略
     */
    registerDefaultStrategies() {
        // 安全漏洞修复策略（增强版）
        this.registerStrategy({
            name: 'SecurityRepairStrategy',
            priority: 20, // 提高优先级
            canHandle: (issue) => issue.type === 'SecurityVulnerability',
            repair: async (issue, fileContent) => {
                try {
                    const lines = fileContent.split('\n');
                    let fixedContent = fileContent;

                    // 根据不同的安全漏洞类型应用特定修复
                    if (issue.message.includes('使用eval函数')) {
                        // 替换eval为更安全的替代方案
                        fixedContent = fixedContent.replace(/eval\s*\(([^)]*)\)/g, (match, expr) => {
                            // 如果是JSON字符串，使用JSON.parse
                            if (expr.match(/^\s*['"`](.*)['"`]\s*$/)) {
                                return `JSON.parse($1)`;
                            }
                            // 否则返回表达式本身
                            return expr;
                        });
                    } else if (issue.message.includes('使用Function构造函数')) {
                        // 提示用户Function构造函数的风险，建议使用标准函数
                        fixedContent = fixedContent.replace(/new\s+Function\s*\(([^)]*)\)/g, (match, params) => {
                            return `/* 安全警告：避免使用Function构造函数 */ (${params.replace(/,\s*$/, '')}) => { /* TODO: 重写为标准函数 */ }`;
                        });
                    } else if (issue.message.includes('直接使用环境变量')) {
                        // 建议使用配置管理系统
                        fixedContent = fixedContent.replace(/process\.env\.([A-Za-z0-9_]+)/g, 'config.$1 /* 建议：使用配置管理系统 */');
                    } else if (issue.message.includes('硬编码密码') || issue.message.includes('硬编码API密钥') || issue.message.includes('硬编码密钥')) {
                        // 替换硬编码凭据为环境变量引用
                        fixedContent = fixedContent.replace(/([a-zA-Z_]+)\s*=\s*['"`]([^'"]*)['"`]/g, '$1 = process.env.$1 /* 安全建议：使用环境变量 */');
                    } else if (issue.message.includes('SQL注入风险')) {
                        // 简单的SQL注入防护提示
                        fixedContent = fixedContent.replace(/(query|execute|sql)\s*=\s*['"`].*['"`]/g, (match) => {
                            return `/* 安全警告：存在SQL注入风险，请使用参数化查询 */ ${match}`;
                        });
                    } else if (issue.message.includes('XSS风险')) {
                        // XSS防护提示
                        fixedContent = fixedContent.replace(/innerHTML\s*=\s*([^;]+);/g, '$1 = escapeHtml($1); /* 安全建议：防止XSS攻击 */');
                    }

                    return {
                        success: true,
                        fixedContent: fixedContent,
                        strategy: 'SecurityRepairStrategy'
                    };
                } catch (error) {
                    return { success: false, error: error.message };
                }
            }
        });

        // 代码质量修复策略（增强版）
        this.registerStrategy({
            name: 'CodeQualityRepairStrategy',
            priority: 12,
            canHandle: (issue) => issue.type === 'CodeQuality' || issue.type === 'BestPractice',
            repair: async (issue, fileContent) => {
                try {
                    const lines = fileContent.split('\n');
                    let fixedContent = fileContent;

                    // 根据不同的代码质量问题应用修复
                    if (issue.message.includes('未使用的常量') || issue.message.includes('未使用的变量')) {
                        // 注释掉未使用的变量/常量
                        const lineToComment = lines[issue.line - 1];
                        lines[issue.line - 1] = `// ${lineToComment} /* 未使用的 ${issue.message.includes('常量') ? '常量' : '变量'} */`;
                        fixedContent = lines.join('\n');
                    } else if (issue.message.includes('未使用的函数')) {
                        // 注释掉未使用的函数
                        let functionStartLine = issue.line - 1;
                        let functionEndLine = issue.line - 1;
                        let braceCount = 0;
                        let inFunction = false;

                        // 查找函数结束位置
                        for (let i = functionStartLine; i < lines.length; i++) {
                            const line = lines[i];
                            braceCount += (line.match(/\{/g) || []).length;
                            braceCount -= (line.match(/\}/g) || []).length;
                            
                            if (inFunction && braceCount === 0) {
                                functionEndLine = i;
                                break;
                            }
                            
                            if (line.includes('function') || line.includes('=>') || line.includes('class')) {
                                inFunction = true;
                            }
                        }

                        // 注释掉整个函数
                        for (let i = functionStartLine; i <= functionEndLine; i++) {
                            lines[i] = `// ${lines[i]}`;
                        }
                        
                        fixedContent = lines.join('\n');
                    } else if (issue.message.includes('控制台日志语句') || issue.message.includes('调试断点语句')) {
                        // 注释掉调试语句
                        const lineToComment = lines[issue.line - 1];
                        lines[issue.line - 1] = `// ${lineToComment} /* 调试语句 */`;
                        fixedContent = lines.join('\n');
                    } else if (issue.message.includes('未使用的导入')) {
                        // 注释掉未使用的导入
                        const lineToComment = lines[issue.line - 1];
                        lines[issue.line - 1] = `// ${lineToComment} /* 未使用的导入 */`;
                        fixedContent = lines.join('\n');
                    } else if (issue.message.includes('使用var声明变量')) {
                        // 将var替换为let或const（简单情况）
                        fixedContent = fixedContent.replace(/var\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*([^;]+);/g, 'const $1 = $2; /* 最佳实践：使用const替代var */');
                        fixedContent = fixedContent.replace(/var\s+([a-zA-Z_$][a-zA-Z0-9_$]*);/g, 'let $1; /* 最佳实践：使用let替代var */');
                    } else if (issue.message.includes('使用==而非===')) {
                        // 将==替换为===
                        fixedContent = fixedContent.replace(/([^=!])==([^=])/g, '$1===$2');
                    }

                    return {
                        success: true,
                        fixedContent: fixedContent,
                        strategy: 'CodeQualityRepairStrategy'
                    };
                } catch (error) {
                    return { success: false, error: error.message };
                }
            }
        });

        // 性能优化修复策略（增强版）
        this.registerStrategy({
            name: 'PerformanceRepairStrategy',
            priority: 10,
            canHandle: (issue) => issue.type === 'PerformanceIssue',
            repair: async (issue, fileContent) => {
                try {
                    const lines = fileContent.split('\n');
                    let fixedContent = fileContent;

                    // 根据不同的性能问题应用修复
                    if (issue.message.includes('频繁使用slice.call')) {
                        // 替换slice.call为Array.from或spread语法
                        fixedContent = fixedContent.replace(/Array\.prototype\.slice\.call\(([^)]+)\)/g, 'Array.from($1)');
                    } else if (issue.message.includes('在循环条件中计算长度')) {
                        // 提取循环条件中的长度计算
                        const lineToFix = lines[issue.line - 1];
                        const fixedLine = lineToFix.replace(/for\s*\(\s*(let|var|const)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*0;\s*\2\s*<\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\.length;\s*\2\+\+/g, (match, declType, indexVar, arrayVar) => {
                            return `// 性能优化：将长度计算移到循环外部\nconst ${arrayVar}_length = ${arrayVar}.length;\nfor (${declType} ${indexVar} = 0; ${indexVar} < ${arrayVar}_length; ${indexVar}++)`;
                        });
                        lines[issue.line - 1] = fixedLine;
                        fixedContent = lines.join('\n');
                    } else if (issue.message.includes('使用JSON.parse(JSON.stringify())进行深拷贝')) {
                        // 建议使用更高效的深拷贝方法
                        fixedContent = fixedContent.replace(/JSON\.parse\s*\(\s*JSON\.stringify\s*\(([^)]*)\)\s*\)/g, 'deepClone($1) /* 建议：使用更高效的深拷贝方法 */');
                    } else if (issue.message.includes('直接操作innerHTML')) {
                        // 建议使用更安全、更高效的DOM操作方法
                        fixedContent = fixedContent.replace(/([a-zA-Z_$][a-zA-Z0-9_$]*)\.innerHTML\s*=\s*([^;]+);/g, '$1.textContent = $2; /* 建议：使用textContent替代innerHTML */');
                    } else if (issue.message.includes('重复计算相同表达式')) {
                        // 提取重复计算的表达式到变量
                        fixedContent = fixedContent.replace(/([a-zA-Z_$][a-zA-Z0-9_$]*)\.([a-zA-Z_$][a-zA-Z0-9_$]*)\(\)\s*\+\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\.([a-zA-Z_$][a-zA-Z0-9_$]*)\(\)/g, (match, obj1, method1, obj2, method2) => {
                            if (obj1 === obj2 && method1 === method2) {
                                return `const result = ${obj1}.${method1}(); result + result /* 性能优化：避免重复计算 */`;
                            }
                            return match;
                        });
                    } else if (issue.message.includes('使用for-in循环遍历数组')) {
                        // 替换for-in循环为for-of循环
                        fixedContent = fixedContent.replace(/for\s*\(\s*(var|let)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s+in\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\)/g, 'for (const $2 of $3)');
                    }

                    return {
                        success: true,
                        fixedContent: fixedContent,
                        strategy: 'PerformanceRepairStrategy'
                    };
                } catch (error) {
                    return { success: false, error: error.message };
                }
            }
        });

        // 多模型协作修复策略（增强版）
        this.registerStrategy({
            name: 'MultiModelRepairStrategy',
            priority: 20,
            canHandle: (issue) => true, // 可以处理所有类型的问题
            repair: async (issue, fileContent) => {
                try {
                    // 模型选择逻辑
                    const models = await this.selectModelsForIssue(issue);
                    
                    if (models.length === 0) {
                        return this.handleError('没有可用的AI模型', 'ModelSelectionError');
                    }

                    // 尝试使用每个模型进行修复，直到成功
                    let lastError;
                    for (const modelInfo of models) {
                        try {
                            const prompt = this.buildRepairPrompt(issue, fileContent);
                            
                            // 使用统一的模型调用方法
                            const modelResult = await this.callModel(modelInfo, prompt, 'javascript');
                            
                            if (modelResult.success) {
                                // 验证修复结果
                                const isValid = await this.validateFix(issue, fileContent, modelResult.content);
                                
                                if (isValid) {
                                    return {
                                        success: true,
                                        fixedContent: modelResult.content,
                                        model: modelInfo.modelType,
                                        strategy: 'MultiModelRepairStrategy'
                                    };
                                } else {
                                    this.logger.warn('REPAIR_ENGINE', '修复结果验证失败，尝试下一个模型', { model: modelInfo.modelType });
                                }
                            } else {
                                this.logger.warn('REPAIR_ENGINE', `模型 ${modelInfo.modelType} 修复失败，尝试下一个模型`, { error: modelResult.error });
                                lastError = new Error(modelResult.error);
                            }
                        } catch (error) {
                            this.logger.warn('REPAIR_ENGINE', `模型 ${modelInfo.modelType} 修复失败，尝试下一个模型`, error);
                            lastError = error;
                        }
                    }

                    return this.handleError(lastError ? lastError.message : '所有模型修复均失败', 'RepairFailureError');
                } catch (error) {
                    return this.handleError('AI修复失败', 'RepairEngineError', error);
                }
            }
        });

        // 简单自动修复策略（增强版）
        this.registerStrategy({
            name: 'SimpleAutoRepairStrategy',
            priority: 14,
            canHandle: (issue) => issue.type === 'LogicError' || issue.type === 'SyntaxError',
            repair: async (issue, fileContent) => {
                try {
                    const lines = fileContent.split('\n');
                    const issueLine = lines[issue.line - 1];
                    let fixedLine = issueLine;

                    // 简单的自动修复
                    if (issue.message.includes('空的if-else语句块') || issue.message.includes('空的条件语句块')) {
                        fixedLine = fixedLine.replace(/\{\s*\}/g, '{ /* TODO: Add implementation */ }');
                    } else if (issue.message.includes('空的for循环') || issue.message.includes('空的while循环') || issue.message.includes('空的do-while循环')) {
                        fixedLine = fixedLine.replace(/\{\s*\}/g, '{ /* TODO: Add loop body */ }');
                    } else if (issue.message.includes('条件始终为真/假')) {
                        // 提示用户条件永远为真/假的问题
                        fixedLine = `// 逻辑警告：条件始终为${issue.message.includes('真') ? '真' : '假'} ${issueLine}`;
                    } else if (issue.message.includes('无条件中断的循环')) {
                        // 移除无条件中断的循环或添加注释
                        fixedLine = `// 逻辑警告：循环会被无条件中断 ${issueLine}`;
                    } else if (issue.message.includes('return语句后的无效代码')) {
                        // 注释掉return语句后的代码
                        const returnIndex = fixedLine.indexOf('return');
                        if (returnIndex !== -1) {
                            const afterReturn = fixedLine.substring(returnIndex + 6).trim();
                            fixedLine = fixedLine.substring(0, returnIndex + 6) + ` ${afterReturn.replace(/;.*$/, '; /* 注意：return后的代码永远不会执行 */')}`;
                        }
                    } else if (issue.message.includes('缺少分号')) {
                        // 添加缺失的分号
                        if (!fixedLine.trim().endsWith(';') && !fixedLine.includes('}') && !fixedLine.includes('{') && !fixedLine.includes(')')) {
                            fixedLine = `${fixedLine};`;
                        }
                    } else if (issue.message.includes('多余的逗号')) {
                        // 移除多余的逗号
                        fixedLine = fixedLine.replace(/,\s*([}\]])/g, ' $1');
                    }

                    lines[issue.line - 1] = fixedLine;
                    return {
                        success: true,
                        fixedContent: lines.join('\n'),
                        strategy: 'SimpleAutoRepairStrategy'
                    };
                } catch (error) {
                    return { success: false, error: error.message };
                }
            }
        });

        // 上下文感知修复策略（新增）
        this.registerStrategy({
            name: 'ContextAwareRepairStrategy',
            priority: 18,
            canHandle: (issue) => true,
            repair: async (issue, fileContent) => {
                try {
                    const lines = fileContent.split('\n');
                    const issueLine = issue.line - 1;
                    const contextWindow = 5;
                    
                    // 提取上下文
                    const startLine = Math.max(0, issueLine - contextWindow);
                    const endLine = Math.min(lines.length - 1, issueLine + contextWindow);
                    const contextLines = lines.slice(startLine, endLine + 1);
                    
                    // 构建上下文感知修复提示
                    const prompt = `修复以下JavaScript代码中的问题，考虑上下文环境：\n\n文件行号：${issue.line}\n问题类型：${issue.type}\n问题描述：${issue.message}\n\n上下文（行 ${startLine + 1}-${endLine + 1}）：\n${contextLines.map((line, i) => `${startLine + i + 1}: ${line}`).join('\n')}\n\n请返回修复后的完整上下文代码块，保持原有格式和风格。`;
                    
                    // 使用AI模型进行修复
                    const modelResult = await this.callModel(this.aiModels.primaryModel, prompt, 'javascript');
                    
                    if (modelResult.success) {
                        // 提取修复后的代码
                        const fixedContext = modelResult.content;
                        const fixedLines = fixedContext.match(/\d+: (.+)/g)?.map(line => line.replace(/\d+: /, '')) || contextLines;
                        
                        // 替换原文件中的对应部分
                        for (let i = 0; i < fixedLines.length; i++) {
                            const targetLine = startLine + i;
                            if (targetLine >= 0 && targetLine < lines.length) {
                                lines[targetLine] = fixedLines[i];
                            }
                        }
                        
                        const fixedContent = lines.join('\n');
                        
                        // 验证修复结果
                        const isValid = await this.validateFix(issue, fileContent, fixedContent);
                        
                        if (isValid) {
                            return {
                                success: true,
                                fixedContent: fixedContent,
                                strategy: 'ContextAwareRepairStrategy'
                            };
                        } else {
                            this.logger.warn('REPAIR_ENGINE', '上下文感知修复验证失败');
                            return this.handleError('修复结果验证失败', 'ValidationError');
                        }
                    } else {
                        return this.handleError(modelResult.error, 'ModelCallError');
                    }
                } catch (error) {
                    return this.handleError('上下文感知修复失败', 'RepairEngineError', error);
                }
            }
        });

        // 渐进式修复策略（增强版）
        this.registerStrategy({
            name: 'ProgressiveRepairStrategy',
            priority: 16,
            canHandle: (issue) => true,
            repair: async (issue, fileContent) => {
                try {
                    // 1. 尝试简单修复
                    let fixedContent = fileContent;
                    let simpleFixApplied = false;
                    
                    const lines = fileContent.split('\n');
                    
                    // 根据问题类型进行简单修复
                    if (issue.type === 'BestPractice' && issue.message.includes('使用var声明变量')) {
                        fixedContent = fixedContent.replace(/var\s+([a-zA-Z_$][a-zA-Z0-9_$]*)/g, 'let $1');
                        simpleFixApplied = true;
                    } else if (issue.type === 'AntiPattern' && issue.message.includes('空的catch块')) {
                        fixedContent = fixedContent.replace(/catch\s*\([^)]*\)\s*\{\s*\}/g, 'catch (error) { console.error(error); }');
                        simpleFixApplied = true;
                    } else if (issue.type === 'ErrorPattern' && issue.message.includes('直接返回可能隐藏错误信息')) {
                        fixedContent = fixedContent.replace(/catch\s*\([^)]*\)\s*\{\s*return\s*([^;]+);\s*\}/g, 'catch (error) { console.error(error); return $1; }');
                        simpleFixApplied = true;
                    } else if (issue.type === 'SyntaxError' && issue.message.includes('缺少括号')) {
                        // 简单的括号修复
                        fixedContent = fixedContent.replace(/\(\s*(.*?)\s*\]/g, '($1)');
                        fixedContent = fixedContent.replace(/\[\s*(.*?)\s*\)/g, '[$1]');
                        simpleFixApplied = true;
                    } else if (issue.type === 'CodeQuality' && issue.message.includes('使用console.log')) {
                        // 注释掉console.log语句
                        fixedContent = fixedContent.replace(/console\.log\s*\(([^)]*)\)\s*;/g, '// console.log($1); /* 调试语句 */');
                        simpleFixApplied = true;
                    }
                    
                    // 如果简单修复有效，返回结果
                    if (simpleFixApplied) {
                        const isValid = await this.validateFix(issue, fileContent, fixedContent);
                        if (isValid) {
                            return {
                                success: true,
                                fixedContent: fixedContent,
                                strategy: 'ProgressiveRepairStrategy',
                                fixLevel: 'simple'
                            };
                        }
                    }
                    
                    // 2. 如果简单修复无效，使用AI模型进行复杂修复
                    this.logger.info('REPAIR_ENGINE', '简单修复无效，使用AI模型进行复杂修复', { issueType: issue.type });
                    
                    const prompt = this.buildRepairPrompt(issue, fileContent);
                    const modelResult = await this.callModel(this.aiModels.primaryModel, prompt, 'javascript');
                    
                    if (modelResult.success) {
                        const isValid = await this.validateFix(issue, fileContent, modelResult.content);
                        
                        if (isValid) {
                            return {
                                success: true,
                                fixedContent: modelResult.content,
                                strategy: 'ProgressiveRepairStrategy',
                                fixLevel: 'advanced'
                            };
                        } else {
                            return this.handleError('复杂修复验证失败', 'ValidationError');
                        }
                    } else {
                        return this.handleError(modelResult.error, 'ModelCallError');
                    }
                } catch (error) {
                    return this.handleError('渐进式修复失败', 'RepairEngineError', error);
                }
            }
        });

        // 代码重构修复策略（新增）
        this.registerStrategy({
            name: 'CodeRefactoringStrategy',
            priority: 8,
            canHandle: (issue) => issue.type === 'CodeQuality' && issue.message.includes('重复代码') || issue.message.includes('过长函数'),
            repair: async (issue, fileContent) => {
                try {
                    const lines = fileContent.split('\n');
                    
                    // 提取函数上下文
                    const contextWindow = 10;
                    const startLine = Math.max(0, issue.line - contextWindow);
                    const endLine = Math.min(lines.length - 1, issue.line + contextWindow);
                    const contextLines = lines.slice(startLine, endLine + 1);
                    
                    // 构建重构提示
                    const prompt = `重构以下JavaScript代码，解决${issue.message}问题：\n\n文件行号：${issue.line}\n\n上下文（行 ${startLine + 1}-${endLine + 1}）：\n${contextLines.map((line, i) => `${startLine + i + 1}: ${line}`).join('\n')}\n\n请返回重构后的完整代码，保持原有功能但提高代码质量和可读性。`;
                    
                    // 使用AI模型进行重构
                    const modelResult = await this.callModel(this.aiModels.primaryModel, prompt, 'javascript');
                    
                    if (modelResult.success) {
                        // 验证重构结果
                        const isValid = await this.validateFix(issue, fileContent, modelResult.content);
                        
                        if (isValid) {
                            return {
                                success: true,
                                fixedContent: modelResult.content,
                                strategy: 'CodeRefactoringStrategy'
                            };
                        } else {
                            return this.handleError('重构结果验证失败', 'ValidationError');
                        }
                    } else {
                        return this.handleError(modelResult.error, 'ModelCallError');
                    }
                } catch (error) {
                    return this.handleError('代码重构失败', 'RepairEngineError', error);
                }
            }
        });

        // 依赖管理修复策略（新增）
        this.registerStrategy({
            name: 'DependencyManagementStrategy',
            priority: 18,
            canHandle: (issue) => issue.type === 'DependencyIssue',
            repair: async (issue, fileContent) => {
                try {
                    let fixedContent = fileContent;
                    
                    // 根据不同的依赖问题应用修复
                    if (issue.message.includes('过时的依赖')) {
                        // 提示更新依赖
                        fixedContent = fixedContent.replace(/("|')(.*?)("|'):\s*("|')(.*?)("|')/g, '$1$2$3: /* 提示：考虑更新此依赖 */ $4$5$6');
                    } else if (issue.message.includes('缺少依赖')) {
                        // 提示安装依赖
                        fixedContent += `\n/* 提示：缺少依赖，请运行 npm install ${issue.message.match(/缺少依赖\s+(.*?)$/)[1]} */`;
                    }
                    
                    return {
                        success: true,
                        fixedContent: fixedContent,
                        strategy: 'DependencyManagementStrategy'
                    };
                } catch (error) {
                    return { success: false, error: error.message };
                }
            }
        });

        // 并行修复策略（新增）
        this.registerStrategy({
            name: 'ParallelRepairStrategy',
            priority: 20,
            canHandle: (issue) => issue.severity === 'high',
            repair: async (issue, fileContent) => {
                try {
                    // 并行使用多个模型进行修复
                    const modelsToUse = [
                        this.aiModels.primaryModel,
                        this.aiModels.secondaryModel
                    ].filter(Boolean);
                    
                    if (modelsToUse.length === 0) {
                        return this.handleError('没有可用的AI模型', 'ModelSelectionError');
                    }
                    
                    // 构建修复提示
                    const prompt = this.buildRepairPrompt(issue, fileContent);
                    
                    // 并行调用所有模型
                    const repairPromises = modelsToUse.map(async (model) => {
                        try {
                            return await this.callModel(model, prompt, 'javascript');
                        } catch (error) {
                            this.logger.warn('REPAIR_ENGINE', `模型并行修复失败`, { model: model.name, error: error.message });
                            return { success: false, error: error.message };
                        }
                    });
                    
                    // 等待所有模型完成
                    const repairResults = await Promise.all(repairPromises);
                    
                    // 过滤成功的结果
                    const successfulResults = repairResults.filter(result => result.success);
                    
                    if (successfulResults.length === 0) {
                        return this.handleError('所有并行模型修复均失败', 'RepairFailureError');
                    }
                    
                    // 选择最佳修复结果
                    const bestResult = successfulResults[0];
                    
                    // 验证最佳结果
                    const isValid = await this.validateFix(issue, fileContent, bestResult.content);
                    
                    if (isValid) {
                        return {
                            success: true,
                            fixedContent: bestResult.content,
                            strategy: 'ParallelRepairStrategy',
                            modelsUsed: modelsToUse.length
                        };
                    } else {
                        return this.handleError('并行修复验证失败', 'ValidationError');
                    }
                } catch (error) {
                    return this.handleError('并行修复失败', 'RepairEngineError', error);
                }
            }
        });
    }

    /**
     * 通用组件注册方法
     */
    registerComponent(type, component) {
        if (!['detectors', 'strategies'].includes(type)) {
            throw new Error(`无效的组件类型: ${type}`);
        }
        
        // 确保组件具有必要的属性
        if (!component.name) {
            throw new Error('组件必须包含name属性');
        }
        
        // 设置默认优先级
        if (component.priority === undefined) {
            component.priority = 0;
        }
        
        this.components[type].push(component);
        // 按优先级排序（高优先级在前）
        this.components[type].sort((a, b) => b.priority - a.priority);
        
        this.logger.info('REPAIR_ENGINE', `已注册${type === 'detectors' ? '问题检测器' : '修复策略'}: ${component.name}`);
    }

    /**
     * 注册问题检测器
     */
    registerDetector(detector) {
        this.registerComponent('detectors', detector);
    }

    /**
     * 注册修复策略
     */
    registerStrategy(strategy) {
        this.registerComponent('strategies', strategy);
    }

    /**
     * 构建修复提示
     * @param {Object} issue - 问题信息
     * @param {string} fileContent - 文件内容
     * @returns {string} 修复提示
     */
    buildRepairPrompt(issue, fileContent) {
        try {
            // 提取上下文代码
            const context = this.extractCodeContext(fileContent, issue.line, 10);
            
            // 根据问题类型生成更精确的修复提示
            let typeSpecificInstructions = '';
            
            switch (issue.type) {
                case 'SyntaxError':
                    typeSpecificInstructions = `
请修复JavaScript语法错误。确保代码符合ECMAScript标准，语法正确无误。`;
                    break;
                    
                case 'LogicError':
                    typeSpecificInstructions = `
请修复逻辑错误。确保代码的逻辑流程正确，条件判断符合预期，循环和控制结构正常工作。`;
                    break;
                    
                case 'SecurityVulnerability':
                    typeSpecificInstructions = `
请修复安全漏洞。遵循安全最佳实践：
1. 避免使用eval()、Function构造函数等动态代码执行
2. 不要硬编码敏感信息（密码、API密钥等）
3. 使用安全的API和方法
4. 验证和过滤用户输入
5. 防止XSS、CSRF等常见攻击`;
                    break;
                    
                case 'CodeQuality':
                    typeSpecificInstructions = `
请修复代码质量问题，遵循最佳实践：
1. 移除未使用的变量、常量和函数
2. 保持代码简洁和可读性
3. 使用适当的命名约定
4. 避免重复代码
5. 添加必要的注释
6. 移除调试语句（console.log, debugger等）`;
                    break;
                    
                case 'PerformanceIssue':
                    typeSpecificInstructions = `
请修复性能问题，优化代码执行效率：
1. 减少不必要的计算和DOM操作
2. 优化循环和迭代
3. 使用更高效的数据结构和算法
4. 避免内存泄漏
5. 考虑异步处理大型操作`;
                    break;
                    
                default:
                    typeSpecificInstructions = `
请修复代码中的问题，确保代码正常工作并遵循最佳实践。`;
            }
            
            // 生成详细的修复提示
            const prompt = `你是一位专业的JavaScript代码修复专家。请修复以下代码中的问题。

文件路径: ${issue.filePath}
问题类型: ${issue.type}
问题严重程度: ${issue.severity}
问题行号: ${issue.line}
问题描述: ${issue.message}

上下文代码（带行号）:
${context}

修复要求:
1. 保持代码功能不变，但修复问题
2. 遵循JavaScript最佳实践和编码规范
3. 保持代码的可读性和可维护性
4. 不要添加不必要的注释或代码
5. 修复后返回完整的代码内容，而不仅仅是修复的部分${typeSpecificInstructions}

请返回修复后的完整代码内容:`;
            
            return prompt;
        } catch (error) {
            this.logger.error('REPAIR_ENGINE', '构建修复提示失败', error);
            
            // 生成基本修复提示作为备选
            return `修复以下JavaScript代码中的问题: ${issue.message}\n\n代码:\n${fileContent}`;
        }
    }

    /**
     * 根据问题选择合适的AI模型
     */
    async selectModelsForIssue(issue) {
        const models = [];
        
        // 先检查所有模型的健康状态
        const modelHealth = {
            cloud: this.aiModels.cloud ? await this.checkModelHealth({ model: this.aiModels.cloud, modelType: 'cloud' }) : false,
            local: this.aiModels.local ? await this.checkModelHealth({ model: this.aiModels.local, modelType: 'local' }) : false
        };
        
        // 根据问题类型和复杂度选择模型
        if (issue.severity === 'high' || issue.type === 'SecurityVulnerability' || issue.type === 'SyntaxError') {
            // 复杂问题优先使用云端模型（如果健康）
            if (modelHealth.cloud) {
                models.push({ model: this.aiModels.cloud, modelType: 'cloud', priority: 'high' });
            }
            // 如果本地模型健康，也可以尝试
            if (modelHealth.local) {
                models.push({ model: this.aiModels.local, modelType: 'local', priority: 'medium' });
            }
        } else {
            // 简单问题优先使用本地模型（如果健康）
            if (modelHealth.local) {
                models.push({ model: this.aiModels.local, modelType: 'local', priority: 'high' });
            }
            // 如果本地模型不健康或修复失败，回退到云端模型
            if (modelHealth.cloud) {
                models.push({ model: this.aiModels.cloud, modelType: 'cloud', priority: 'medium' });
            }
        }
        
        // 按优先级排序模型
        return models.sort((a, b) => {
            const priorityOrder = { high: 1, medium: 2, low: 3 };
            return priorityOrder[a.priority] - priorityOrder[b.priority];
        });
    }
    
    /**
     * 统一的模型调用方法，处理不同模型的调用差异和重试逻辑
     */
    async callModel(modelInfo, prompt, language = 'javascript', retryCount = 2) {
        const { model, modelType } = modelInfo;
        let lastError;
        
        // 实现重试逻辑
        for (let attempt = 0; attempt <= retryCount; attempt++) {
            try {
                // 再次检查模型健康状态
                if (!await this.checkModelHealth(modelInfo)) {
                    throw new Error(`模型 ${modelType} 健康状态异常`);
                }
                
                let response;
                
                if (modelType === 'local') {
                    response = await model.generateResponse(prompt, {
                        temperature: 0.3,
                        maxTokens: 1024
                    });
                    return {
                        success: true,
                        content: response.response,
                        attempt: attempt + 1
                    };
                } else {
                    // 云端模型调用
                    response = await model.generateCode(prompt, language);
                    return {
                        success: true,
                        content: response.code,
                        attempt: attempt + 1
                    };
                }
            } catch (error) {
                    lastError = error;
                    
                    // 如果不是最后一次尝试，等待一段时间后重试
                    if (attempt < retryCount) {
                        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempt))); // 指数退避
                    }
                }
        }
        
        return {
            success: false,
            error: lastError.message,
            attempt: retryCount + 1
        };
    }

    /**
     * 验证修复结果
     */
    async validateFix(issue, originalContent, fixedContent) {
        try {
            // 基本验证：修复内容不能为空
            if (!fixedContent || fixedContent.trim() === '') {
                return false;
            }

            // 验证修复后的代码是否有语法错误
            new Function(fixedContent);

            // 对于不同类型的问题进行特定验证
            switch (issue.type) {
                case 'SyntaxError':
                    // 语法错误应该已经被修复
                    return true;
                
                case 'LogicError':
                    // 检查是否修复了特定的逻辑问题
                    if (issue.message.includes('空的if-else语句块')) {
                        return !fixedContent.includes('{\s*}');
                    }
                    if (issue.message.includes('空的for循环')) {
                        return !fixedContent.includes('for\s*\([^)]*\)\s*{\s*}');
                    }
                    if (issue.message.includes('空的while循环')) {
                        return !fixedContent.includes('while\s*\([^)]*\)\s*{\s*}');
                    }
                    return true;
                
                case 'SecurityVulnerability':
                    // 检查安全漏洞是否被修复
                    if (issue.message.includes('使用eval函数')) {
                        return !fixedContent.includes('eval(');
                    }
                    return true;
                
                default:
                    return true;
            }
        } catch (error) {
            this.logger.error('REPAIR_ENGINE', '修复结果验证失败', error);
            return false;
        }
    }

    /**
     * 检测单个文件的问题
     */
    async detectIssuesInFile(filePath) {
        try {
            if (!fs.existsSync(filePath)) {
                const error = this.handleError(`文件不存在: ${filePath}`, 'FileNotFoundError');
                this.emit('file_detect_error', { filePath, error });
                return error;
            }

            this.emit('file_detect_start', { filePath, timestamp: Date.now() });
            this.logger.info('REPAIR_ENGINE', `开始检测文件: ${filePath}`);
            
            const startTime = Date.now();
            const fileContent = fs.readFileSync(filePath, 'utf8');
            const fileExt = path.extname(filePath).toLowerCase();
            const allIssues = [];
            const detectionResults = [];

            // 执行基本的文件类型验证
            const fileTypeInfo = this.analyzeFileType(filePath, fileContent);
            
            // 使用并行检测提高效率
            const detectionPromises = this.components.detectors.map(async (detector) => {
                try {
                    const detectorStart = Date.now();
                    // 检查检测器是否支持当前文件类型
                    if (detector.supportedFileTypes && !detector.supportedFileTypes.includes(fileExt)) {
                        detectionResults.push({
                            detector: detector.name,
                            success: true,
                            skipped: true,
                            reason: `不支持的文件类型: ${fileExt}`,
                            issuesFound: 0,
                            time: Date.now() - detectorStart
                        });
                        return;
                    }
                    
                    const issues = await detector.detect(filePath, fileContent, fileTypeInfo);
                    const detectorEnd = Date.now();
                    
                    if (issues && issues.length > 0) {
                        // 为每个问题添加上下文和严重程度评分
                        const enrichedIssues = issues.map(issue => {
                            return {
                                ...issue,
                                severityScore: this.calculateSeverityScore(issue),
                                context: this.extractEnhancedContext(fileContent, issue.line, fileTypeInfo),
                                fileExt,
                                detectedBy: detector.name
                            };
                        });
                        
                        allIssues.push(...enrichedIssues);
                        detectionResults.push({
                            detector: detector.name,
                            success: true,
                            issuesFound: issues.length,
                            time: detectorEnd - detectorStart
                        });
                        this.logger.info('REPAIR_ENGINE', `检测器 ${detector.name} 检测到 ${issues.length} 个问题`, {
                            detector: detector.name,
                            issuesFound: issues.length,
                            time: detectorEnd - detectorStart
                        });
                    } else {
                        detectionResults.push({
                            detector: detector.name,
                            success: true,
                            issuesFound: 0,
                            time: detectorEnd - detectorStart
                        });
                    }
                } catch (error) {
                    detectionResults.push({
                        detector: detector.name,
                        success: false,
                        error: error.message,
                        time: Date.now() - (detectorStart || Date.now())
                    });
                    this.logger.error('REPAIR_ENGINE', `检测器 ${detector.name} 执行失败`, {
                        detector: detector.name,
                        error: error.message
                    });
                }
            });

            // 等待所有检测器完成
            await Promise.all(detectionPromises);

            // 按严重程度排序问题
            allIssues.sort((a, b) => b.severityScore - a.severityScore);
            
            // 按严重程度和类型分类问题
            const categorizedIssues = {
                // 按类型分类
                byType: {
                    security: allIssues.filter(i => i.type === 'SecurityVulnerability'),
                    syntax: allIssues.filter(i => i.type === 'SyntaxError'),
                    logic: allIssues.filter(i => i.type === 'LogicError'),
                    performance: allIssues.filter(i => i.type === 'PerformanceIssue'),
                    codeQuality: allIssues.filter(i => i.type === 'CodeQualityIssue'),
                    bestPractice: allIssues.filter(i => i.type === 'BestPracticeViolation'),
                    antiPattern: allIssues.filter(i => i.type === 'AntiPattern'),
                    errorPattern: allIssues.filter(i => i.type === 'ErrorPattern')
                },
                // 按严重程度分类
                bySeverity: {
                    critical: allIssues.filter(i => i.severityScore >= 90),
                    high: allIssues.filter(i => i.severityScore >= 70 && i.severityScore < 90),
                    medium: allIssues.filter(i => i.severityScore >= 40 && i.severityScore < 70),
                    low: allIssues.filter(i => i.severityScore < 40)
                }
            };
            
            // 计算代码质量评分
            const codeQualityScore = this.calculateCodeQualityScore(allIssues, fileContent.length);
            
            // 分析代码复杂度
            const complexityAnalysis = this.analyzeCodeComplexity(fileContent, fileTypeInfo);

            const totalTime = Date.now() - startTime;
            const result = {
                success: true,
                filePath,
                fileExt,
                fileTypeInfo,
                issues: allIssues,
                categorizedIssues,
                detectionResults,
                totalIssues: allIssues.length,
                criticalIssues: categorizedIssues.bySeverity.critical.length,
                highIssues: categorizedIssues.bySeverity.high.length,
                mediumIssues: categorizedIssues.bySeverity.medium.length,
                lowIssues: categorizedIssues.bySeverity.low.length,
                codeQualityScore,
                complexityAnalysis,
                totalTime,
                timestamp: Date.now()
            };

            // 更新统计信息
            this.repairStats.detectedIssues += allIssues.length;
            this.repairStats.filesScanned += 1;
            this.repairStats.criticalIssues += categorizedIssues.bySeverity.critical.length;
            this.repairStats.highIssues += categorizedIssues.bySeverity.high.length;
            this.repairStats.mediumIssues += categorizedIssues.bySeverity.medium.length;
            this.repairStats.lowIssues += categorizedIssues.bySeverity.low.length;

            this.emit('file_detect_complete', result);
            this.logger.info('REPAIR_ENGINE', `文件检测完成: ${filePath}`, {
                totalIssues: allIssues.length,
                criticalIssues: categorizedIssues.bySeverity.critical.length,
                highIssues: categorizedIssues.bySeverity.high.length,
                mediumIssues: categorizedIssues.bySeverity.medium.length,
                lowIssues: categorizedIssues.bySeverity.low.length,
                codeQualityScore,
                totalTime,
                detectionResults: detectionResults.map(r => ({ 
                    detector: r.detector, 
                    issuesFound: r.issuesFound,
                    skipped: r.skipped
                }))
            });

            return result;
        } catch (error) {
            const errorResult = this.handleError('文件检测失败', 'FileDetectError', error);
            this.emit('file_detect_error', { filePath, error: errorResult });
            this.logger.error('REPAIR_ENGINE', `检测文件问题失败: ${filePath}`, error);
            return errorResult;
        }
    }

    /**
     * 标准化错误处理方法
     */
    handleError(message, errorType = 'GeneralError', originalError = null) {
        if (originalError) {
            this.logger.error('REPAIR_ENGINE', message, { 
                errorType, 
                originalError: originalError.message,
                stack: originalError.stack
            });
        } else {
            this.logger.warn('REPAIR_ENGINE', message, { errorType });
        }
        
        return {
            success: false,
            error: message,
            errorType,
            originalError: originalError ? originalError.message : null
        };
    }

    /**
     * 分析文件类型和基本信息
     */
    analyzeFileType(filePath, content) {
        const ext = path.extname(filePath).toLowerCase();
        const lines = content.split('\n');
        
        let language = 'unknown';
        let framework = 'unknown';
        
        // 根据文件扩展名和内容判断语言
        if (['.js', '.jsx'].includes(ext)) {
            language = 'javascript';
            // 检查是否使用React
            if (content.includes('React') || content.includes('import React')) {
                framework = 'react';
            }
            // 检查是否使用Vue
            if (content.includes('Vue') || content.includes('export default {')) {
                framework = 'vue';
            }
        } else if (['.ts', '.tsx'].includes(ext)) {
            language = 'typescript';
            if (content.includes('React') || content.includes('import React')) {
                framework = 'react';
            }
        } else if (['.css'].includes(ext)) {
            language = 'css';
            if (content.includes('@tailwind') || content.includes('tailwindcss')) {
                framework = 'tailwind';
            } else if (content.includes('@import') && content.includes('node_modules')) {
                framework = 'webpack';
            }
        } else if (['.html'].includes(ext)) {
            language = 'html';
            if (content.includes('<!DOCTYPE html>')) {
                framework = 'html5';
            }
        }
        
        return {
            extension: ext,
            language,
            framework,
            lineCount: lines.length,
            characterCount: content.length,
            byteCount: Buffer.byteLength(content, 'utf8')
        };
    }
    
    /**
     * 计算问题的严重程度评分（0-100）
     */
    calculateSeverityScore(issue) {
        // 基础严重程度映射
        const severityMap = {
            'critical': 95,
            'high': 75,
            'medium': 55,
            'low': 35
        };
        
        // 类型严重程度加成
        const typeBonusMap = {
            'SecurityVulnerability': 30,
            'SyntaxError': 20,
            'LogicError': 15,
            'PerformanceIssue': 10,
            'CodeQualityIssue': 5,
            'BestPracticeViolation': 3,
            'AntiPattern': 8,
            'ErrorPattern': 12
        };
        
        let score = severityMap[issue.severity || 'medium'] || 50;
        
        // 添加类型加成
        score += typeBonusMap[issue.type] || 0;
        
        // 确保评分在0-100范围内
        return Math.min(100, Math.max(0, score));
    }
    
    /**
     * 提取增强的代码上下文
     */
    extractEnhancedContext(content, lineNumber, fileTypeInfo, contextLines = 8) {
        const lines = content.split('\n');
        const start = Math.max(0, lineNumber - 1 - contextLines);
        const end = Math.min(lines.length - 1, lineNumber - 1 + contextLines);
        
        let context = '';
        let codeBlockContext = this.extractCodeBlockContext(lines, lineNumber - 1, fileTypeInfo.language);
        
        for (let i = start; i <= end; i++) {
            const line = lines[i];
            const lineNum = i + 1;
            const marker = lineNum === lineNumber ? '>>> ' : '    ';
            context += `${marker}${lineNum}: ${line}\n`;
        }
        
        return {
            lineContext: context.trim(),
            codeBlockContext: codeBlockContext.trim(),
            totalLines: lines.length,
            currentLine: lineNumber
        };
    }
    
    /**
     * 提取代码块上下文
     */
    extractCodeBlockContext(lines, targetLineIndex, language) {
        let start = targetLineIndex;
        let end = targetLineIndex;
        let braceCount = 0;
        let inBlock = false;
        
        // 简单的代码块检测，根据语言调整
        if (['javascript', 'typescript', 'css'].includes(language)) {
            // 向前查找代码块开始
            for (let i = targetLineIndex; i >= 0; i--) {
                const line = lines[i].trim();
                if (line.endsWith('{')) {
                    start = i;
                    braceCount++;
                    inBlock = true;
                    break;
                }
            }
            
            // 向后查找代码块结束
            if (inBlock) {
                for (let i = targetLineIndex; i < lines.length; i++) {
                    const line = lines[i].trim();
                    if (line.startsWith('}')) {
                        braceCount--;
                        if (braceCount === 0) {
                            end = i;
                            break;
                        }
                    } else if (line.endsWith('{')) {
                        braceCount++;
                    }
                }
            }
        }
        
        // 提取代码块
        return lines.slice(start, end + 1).join('\n');
    }
    
    /**
     * 计算代码质量评分
     */
    calculateCodeQualityScore(issues, totalCharacters) {
        // 基于问题数量和严重程度计算评分
        const totalSeverityPoints = issues.reduce((sum, issue) => sum + issue.severityScore, 0);
        const avgSeverity = issues.length > 0 ? totalSeverityPoints / issues.length : 0;
        
        // 基础分100，减去问题带来的扣分
        let score = 100;
        
        // 根据平均严重程度扣分
        score -= avgSeverity * 0.5;
        
        // 根据问题数量扣分（与文件大小相关）
        const issuesPerKb = (issues.length / (totalCharacters / 1024)) * 10;
        score -= issuesPerKb * 2;
        
        // 确保评分在0-100范围内
        return Math.max(0, Math.min(100, Math.round(score)));
    }
    
    /**
     * 分析代码复杂度
     */
    analyzeCodeComplexity(content, fileTypeInfo) {
        const lines = content.split('\n');
        let complexity = {
            cyclomaticComplexity: 1, // 基础复杂度
            functionCount: 0,
            classCount: 0,
            commentDensity: 0,
            lineOfCode: lines.length,
            blankLineCount: 0,
            commentLineCount: 0
        };
        
        // 简单的复杂度分析（实际项目中可能需要更复杂的解析）
        lines.forEach(line => {
            const trimmedLine = line.trim();
            
            if (trimmedLine === '') {
                complexity.blankLineCount++;
            } else if (trimmedLine.startsWith('//') || trimmedLine.startsWith('/*') || trimmedLine.startsWith('*')) {
                complexity.commentLineCount++;
            } else {
                // 计算圈复杂度
                const decisionPoints = (trimmedLine.match(/(if|else|for|while|do|switch|case|break|continue|return|throw|catch|finally)/g) || []).length;
                complexity.cyclomaticComplexity += decisionPoints;
                
                // 计算函数和类数量
                if (/function\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*\(/.test(trimmedLine) ||
                    /const\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*=\s*function/.test(trimmedLine) ||
                    /[a-zA-Z_$][a-zA-Z0-9_$]*\s*=\s*\(.*\)\s*=>/.test(trimmedLine)) {
                    complexity.functionCount++;
                }
                
                if (/class\s+[a-zA-Z_$][a-zA-Z0-9_$]*/.test(trimmedLine)) {
                    complexity.classCount++;
                }
            }
        });
        
        // 计算注释密度
        const codeLines = lines.length - complexity.blankLineCount;
        complexity.commentDensity = codeLines > 0 ? Math.round((complexity.commentLineCount / codeLines) * 100) : 0;
        
        return complexity;
    }

    /**
     * 修复单个文件
     */
    async repairFile(filePath, issues = null) {
        try {
            if (!fs.existsSync(filePath)) {
                const error = this.handleError(`文件不存在: ${filePath}`, 'FileNotFoundError');
                this.emit('file_repair_error', { filePath, error });
                return error;
            }

            this.emit('file_repair_start', { filePath, timestamp: Date.now() });
            this.logger.info('REPAIR_ENGINE', `开始修复文件: ${filePath}`);

            // 如果没有提供问题列表，先检测问题
            if (!issues) {
                issues = await this.detectIssuesInFile(filePath);
            }

            // 如果问题是错误对象，直接返回
            if (issues.success === false) {
                const error = this.handleError('文件检测失败', 'FileDetectError', new Error(issues.error));
                this.emit('file_repair_error', { filePath, error });
                return error;
            }

            // 提取实际问题列表
            const actualIssues = Array.isArray(issues) ? issues : issues.issues;

            if (actualIssues.length === 0) {
                const result = { 
                    success: true, 
                    filePath,
                    issues: actualIssues, 
                    fixedIssues: [],
                    fixedContent: null,
                    totalIssues: 0,
                    totalFixed: 0,
                    repairTime: 0,
                    timestamp: Date.now()
                };
                this.emit('file_repair_complete', result);
                this.logger.info('REPAIR_ENGINE', `文件无需修复: ${filePath}`);
                return result;
            }

            let content = fs.readFileSync(filePath, 'utf8');
            const fixedIssues = [];
            const repairResults = [];

            // 创建备份
            const backupPath = `${filePath}.bak`;
            fs.writeFileSync(backupPath, content, 'utf8');
            this.logger.info('REPAIR_ENGINE', `创建文件备份: ${backupPath}`);

            // 按严重程度和行号排序修复
            const sortedIssues = [...actualIssues].sort((a, b) => {
                // 首先按严重程度排序
                const severityOrder = { critical: 1, high: 2, medium: 3, low: 4 };
                const severityDiff = severityOrder[a.severity] - severityOrder[b.severity];
                if (severityDiff !== 0) return severityDiff;
                // 然后按行号倒序排序，避免行号偏移
                return b.line - a.line;
            });

            for (const issue of sortedIssues) {
                // 找到适合的修复策略
                const strategies = this.components.strategies.filter(s => s.canHandle(issue));
                
                if (strategies.length > 0) {
                    // 使用优先级最高的策略
                    const strategy = strategies.sort((a, b) => a.priority - b.priority)[0];
                    
                    try {
                        const repairStart = Date.now();
                        const result = await strategy.repair(issue, content);
                        const repairEnd = Date.now();
                        
                        if (result.success) {
                            content = result.fixedContent;
                            fixedIssues.push(issue);
                            repairResults.push({
                                issue: issue,
                                strategy: strategy.name,
                                success: true,
                                time: repairEnd - repairStart,
                                message: '修复成功'
                            });
                            this.logger.info('REPAIR_ENGINE', `问题修复成功: ${issue.type}`, {
                                strategy: strategy.name,
                                issueType: issue.type,
                                issueLine: issue.line,
                                time: repairEnd - repairStart
                            });
                        } else {
                            repairResults.push({
                                issue: issue,
                                strategy: strategy.name,
                                success: false,
                                time: repairEnd - repairStart,
                                error: result.error
                            });
                            this.logger.error('REPAIR_ENGINE', `问题修复失败: ${issue.type}`, {
                                strategy: strategy.name,
                                issueType: issue.type,
                                issueLine: issue.line,
                                error: result.error
                            });
                        }
                    } catch (error) {
                        repairResults.push({
                            issue: issue,
                            strategy: strategy.name,
                            success: false,
                            time: Date.now() - repairStart,
                            error: error.message
                        });
                        this.logger.error('REPAIR_ENGINE', `策略执行失败: ${strategy.name}`, {
                            strategy: strategy.name,
                            issueType: issue.type,
                            issueLine: issue.line,
                            error: error.message
                        });
                    }
                } else {
                    repairResults.push({
                        issue: issue,
                        strategy: null,
                        success: false,
                        time: 0,
                        error: '没有找到适合的修复策略'
                    });
                    this.logger.warn('REPAIR_ENGINE', `没有找到适合的修复策略: ${issue.type}`, {
                        issueType: issue.type,
                        issueLine: issue.line
                    });
                }
            }

            // 保存修复后的文件
            fs.writeFileSync(filePath, content, 'utf8');

            // 计算修复统计信息
            const totalTime = repairResults[0] ? Date.now() - repairResults[0].repairStart : Date.now();
            const fixedByType = {};
            fixedIssues.forEach(issue => {
                fixedByType[issue.type] = (fixedByType[issue.type] || 0) + 1;
            });

            const result = { 
                success: true, 
                filePath,
                originalIssues: actualIssues,
                fixedIssues: fixedIssues,
                fixedContent: content,
                repairResults: repairResults,
                backupPath: backupPath,
                totalIssues: actualIssues.length,
                totalFixed: fixedIssues.length,
                fixRate: actualIssues.length > 0 ? (fixedIssues.length / actualIssues.length * 100).toFixed(2) + '%' : '100%',
                fixedByType: fixedByType,
                repairTime: totalTime,
                timestamp: Date.now()
            };

            // 更新统计信息
            this.repairStats.fixedIssues += fixedIssues.length;
            this.repairStats.filesRepaired += 1;

            this.emit('file_repair_complete', result);
            this.logger.info('REPAIR_ENGINE', `文件修复完成: ${filePath}`, {
                totalIssues: actualIssues.length,
                totalFixed: fixedIssues.length,
                fixRate: result.fixRate,
                repairTime: totalTime
            });

            return result;
        } catch (error) {
            const errorResult = this.handleError('文件修复失败', 'FileRepairError', error);
            this.emit('file_repair_error', { filePath, error: errorResult });
            return errorResult;
        }
    }

    /**
     * 批量修复目录中的文件
     */
    async repairDirectory(directoryPath, fileExtensions = ['.js'], parallelLimit = 5) {
        try {
            if (!fs.existsSync(directoryPath)) {
                const error = this.handleError(`目录不存在: ${directoryPath}`, 'DirectoryNotFoundError');
                this.emit('directory_repair_error', { directoryPath, error });
                return error;
            }

            this.emit('directory_repair_start', { directoryPath, fileExtensions, timestamp: Date.now() });
            this.logger.info('REPAIR_ENGINE', `开始修复目录: ${directoryPath}`, {
                fileExtensions,
                parallelLimit
            });

            const files = this.getAllFiles(directoryPath);
            const targetFiles = files.filter(file => fileExtensions.includes(path.extname(file)));
            const totalFiles = targetFiles.length;
            
            this.logger.info('REPAIR_ENGINE', `找到 ${totalFiles} 个目标文件`, {
                directoryPath,
                totalFiles
            });

            const results = [];
            const errors = [];
            const repairStats = {
                totalFiles: totalFiles,
                processedFiles: 0,
                succeededFiles: 0,
                failedFiles: 0,
                totalIssues: 0,
                totalFixed: 0,
                fixRate: 0,
                startTime: Date.now()
            };

            // 使用并行处理提高效率
            const fileChunks = [];
            for (let i = 0; i < targetFiles.length; i += parallelLimit) {
                fileChunks.push(targetFiles.slice(i, i + parallelLimit));
            }

            // 处理每个文件块
            for (const chunk of fileChunks) {
                const chunkPromises = chunk.map(async (file) => {
                    try {
                        this.emit('file_repair_queue', { filePath: file, timestamp: Date.now() });
                        const result = await this.repairFile(file);
                        
                        results.push({ file, result });
                        repairStats.processedFiles++;
                        
                        if (result.success) {
                            repairStats.succeededFiles++;
                            repairStats.totalIssues += result.totalIssues || 0;
                            repairStats.totalFixed += result.totalFixed || 0;
                        } else {
                            repairStats.failedFiles++;
                            errors.push({ filePath: file, error: result.error });
                        }
                        
                        // 更新修复率
                        if (repairStats.totalIssues > 0) {
                            repairStats.fixRate = (repairStats.totalFixed / repairStats.totalIssues * 100).toFixed(2) + '%';
                        }
                        
                        // 触发进度更新事件
                        this.emit('directory_repair_progress', {
                            directoryPath,
                            processed: repairStats.processedFiles,
                            total: totalFiles,
                            progress: Math.round((repairStats.processedFiles / totalFiles) * 100),
                            stats: repairStats,
                            timestamp: Date.now()
                        });
                        
                    } catch (error) {
                        const errorResult = this.handleError(`文件修复失败: ${file}`, 'FileRepairError', error);
                        results.push({ file, result: errorResult });
                        errors.push({ filePath: file, error: error.message });
                        repairStats.processedFiles++;
                        repairStats.failedFiles++;
                        
                        this.emit('directory_repair_progress', {
                            directoryPath,
                            processed: repairStats.processedFiles,
                            total: totalFiles,
                            progress: Math.round((repairStats.processedFiles / totalFiles) * 100),
                            stats: repairStats,
                            timestamp: Date.now()
                        });
                    }
                });

                // 等待当前块的所有文件修复完成
                await Promise.all(chunkPromises);
            }

            // 计算统计信息
            const totalTime = Date.now() - repairStats.startTime;
            const finalResult = {
                success: true,
                directoryPath,
                fileExtensions,
                totalFiles,
                processedFiles: repairStats.processedFiles,
                succeededFiles: repairStats.succeededFiles,
                failedFiles: repairStats.failedFiles,
                totalIssues: repairStats.totalIssues,
                totalFixed: repairStats.totalFixed,
                fixRate: repairStats.fixRate,
                repairTime: totalTime,
                results: results,
                errors: errors,
                timestamp: Date.now()
            };

            this.emit('directory_repair_complete', finalResult);
            this.logger.info('REPAIR_ENGINE', `目录修复完成: ${directoryPath}`, {
                totalFiles,
                succeededFiles: repairStats.succeededFiles,
                failedFiles: repairStats.failedFiles,
                totalIssues: repairStats.totalIssues,
                totalFixed: repairStats.totalFixed,
                fixRate: repairStats.fixRate,
                repairTime: totalTime
            });

            return finalResult;
        } catch (error) {
            const errorResult = this.handleError('目录修复失败', 'DirectoryRepairError', error);
            this.emit('directory_repair_error', { directoryPath, error: errorResult });
            return errorResult;
        }
    }

    /**
     * 获取目录中的所有文件
     * 使用迭代方式替代递归，提高性能和内存效率
     */
    getAllFiles(directoryPath) {
        const files = [];
        const stack = [directoryPath];
        
        while (stack.length > 0) {
            const currentDir = stack.pop();
            const entries = fs.readdirSync(currentDir, { withFileTypes: true });
            
            for (const entry of entries) {
                const fullPath = path.join(currentDir, entry.name);
                
                if (entry.isDirectory()) {
                    stack.push(fullPath);
                } else {
                    files.push(fullPath);
                }
            }
        }
        
        return files;
    }

    /**
     * 获取修复引擎状态
     */
    getStatus() {
        return {
            version: '2.0.0',
            initialized: this.isInitialized,
            startTime: this.startTime,
            uptime: this.startTime ? Date.now() - this.startTime : 0,
            models: {
                cloud: {
                    initialized: !!this.aiModels.cloud,
                    type: this.aiModels.cloud ? 'DeepSeek Cloud Model' : 'Not Initialized'
                },
                local: {
                    initialized: !!this.aiModels.local,
                    type: this.aiModels.local ? 'DeepSeek Local Model' : 'Not Initialized'
                },
                adapters: this.components.modelAdapters ? this.components.modelAdapters.length : 0
            },
            detectors: {
                total: this.components.detectors.length,
                list: this.components.detectors.map(detector => ({
                    name: detector.name,
                    type: detector.type || 'custom'
                }))
            },
            strategies: {
                total: this.components.strategies.length,
                list: this.components.strategies.map(strategy => ({
                    name: strategy.name,
                    priority: strategy.priority,
                    type: strategy.type || 'custom'
                }))
            },
            components: {
                qualityEvaluator: this.components.codeQualityEvaluator ? true : false,
                reportGenerator: this.components.reportGenerator ? true : false,
                modelAdapters: this.components.modelAdapters ? true : false,
                parallelQueue: this.components.parallelQueue ? true : false
            },
            directories: {
                logs: this.config.directories?.logs || 'Default',
                backups: this.config.directories?.backups || 'Default',
                reports: this.config.directories?.reports || 'Default'
            },
            stats: {
                filesScanned: this.repairStats.filesScanned,
                detectedIssues: this.repairStats.detectedIssues,
                fixedIssues: this.repairStats.fixedIssues,
                filesRepaired: this.repairStats.filesRepaired,
                totalRepairs: this.repairStats.totalRepairs,
                successRate: this.repairStats.totalRepairs > 0 
                    ? (this.repairStats.filesRepaired / this.repairStats.totalRepairs * 100).toFixed(2) + '%' 
                    : '0%'
            },
            config: {
                parallelLimit: this.config.parallelLimit,
                useCloudModel: this.config.useCloudModel,
                useLocalModel: this.config.useLocalModel,
                autoBackup: this.config.autoBackup,
                generateReport: this.config.generateReport,
                validation: this.config.validation
            }
        };
    }
}

module.exports = RepairEngine;
