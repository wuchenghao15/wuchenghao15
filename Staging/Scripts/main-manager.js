#!/usr/bin/env node

const path = require('path');
const fs = require('fs');

// 使用Node.js内置的fs.promises替代mkdirp

// 导入系统模块
const { configManager } = require('./config/config-manager');
const { EnhancedLogger, LOG_LEVELS, FileLogTarget, ConsoleLogTarget } = require('./monitoring/enhanced-logger');

/**
 * MTSCOS AI 灰度测试环境主管理器
 */
class MTSCOSManager {
    constructor() {
        this.logger = null;
        this.modules = new Map();
        this.isInitialized = false;
        this.isRunning = false;
        this.basePath = path.join(__dirname, '../');
    }

    /**
     * 初始化主管理器
     */
    async initialize() {
        try {
            console.log('正在初始化 MTSCOS AI 灰度测试环境管理器...');
            
            // 1. 初始化日志系统
            await this.initializeLogging();
            this.logger.info('MAIN', '日志系统初始化成功');
            
            // 2. 初始化配置管理器
            const configPath = path.join(this.basePath, 'config/system-config.json');
            await configManager.initialize(configPath);
            this.logger.info('MAIN', '配置管理器初始化成功');
            
            // 3. 设置配置管理器的日志器
            configManager.setLogger(this.logger);
            
            // 4. 根据配置调整日志级别
            const logLevel = configManager.get('system.logLevel', 'info');
            this.logger.setLevel(logLevel);
            this.logger.info('MAIN', `日志级别设置为: ${logLevel}`);
            
            // 5. 加载配置摘要
            const configSummary = configManager.getConfigSummary();
            this.logger.info('MAIN', '系统配置摘要', configSummary);
            
            // 6. 创建必要的目录
            await this.createRequiredDirectories();
            this.logger.info('MAIN', '必要目录创建完成');
            
            // 7. 加载所有模块
            await this.loadModules();
            this.logger.info('MAIN', `成功加载 ${this.modules.size} 个系统模块`);
            
            this.isInitialized = true;
            console.log('MTSCOS AI 灰度测试环境管理器初始化完成!');
            return true;
        } catch (error) {
            console.error(`初始化失败: ${error.message}`);
            if (this.logger) {
                this.logger.error('MAIN', '初始化失败', error);
            }
            return false;
        }
    }

    /**
     * 初始化日志系统
     */
    async initializeLogging() {
        try {
            // 创建日志目录
            const logsDir = path.join(this.basePath, 'Logs');
            await fs.promises.mkdir(logsDir, { recursive: true });
            
            // 创建日志器
            this.logger = new EnhancedLogger({
                level: LOG_LEVELS.INFO,
                targets: [
                    new ConsoleLogTarget(),
                    new FileLogTarget({
                        filePath: path.join(logsDir, 'system.log'),
                        maxFileSize: 10 * 1024 * 1024, // 10MB
                        maxFiles: 5
                    })
                ]
            });
            
            // 异步初始化日志器
            await this.logger.initialize();
            
        } catch (error) {
            throw new Error(`日志系统初始化失败: ${error.message}`);
        }
    }

    /**
     * 创建必要的目录
     */
    async createRequiredDirectories() {
        try {
            const pathsConfig = configManager.get('paths', {});
            const systemRoot = configManager.get('system.basePath') || this.basePath;
            
            // 创建配置中定义的所有目录
            for (const [key, dirPath] of Object.entries(pathsConfig)) {
                if (dirPath && typeof dirPath === 'string') {
                    // 如果是绝对路径（以/开头），则相对于系统根目录创建
                    const resolvedPath = dirPath.startsWith('/') 
                        ? path.join(systemRoot, dirPath.substring(1)) 
                        : dirPath;
                    
                    await fs.promises.mkdir(resolvedPath, { recursive: true });
                    this.logger.debug('MAIN', `创建目录: ${resolvedPath}`);
                }
            }
            
            // 额外创建一些必要的目录
            const extraDirs = [
                path.join(this.basePath, 'Temp'),
                path.join(this.basePath, 'Results'),
                path.join(this.basePath, 'Uploads'),
                path.join(this.basePath, 'Users')
            ];
            
            for (const dir of extraDirs) {
                await fs.promises.mkdir(dir, { recursive: true });
                this.logger.debug('MAIN', `创建额外目录: ${dir}`);
            }
        } catch (error) {
            throw new Error(`创建目录失败: ${error.message}`);
        }
    }

    /**
     * 加载系统模块
     */
    async loadModules() {
        try {
            // 模块加载配置
            const moduleConfig = {
                'configManager': { path: './config/config-manager', export: 'configManager' },
                'autoRepairEngine': { path: './monitoring/auto-repair-engine', export: 'AutoRepairEngine' },
                'adaptiveEngine': { path: './intelligence/adaptive-engine', export: 'AdaptiveEngine' },
                'serverManagement': { path: './intelligence/server-management', export: 'ServerDynamicManagement' },
                'testUserManagement': { path: './testing/test-user-management', export: 'TestUserManagement' },
                'githubBackupManager': { path: './backup/github-backup-manager', export: 'GitHubBackupManager' },
                'rollingCodeLock': { path: './security/rolling-code-lock', export: 'RollingCodeLock' },
                'colorSchemeRecommender': { path: './design/color-scheme-recommender', export: 'ColorSchemeRecommender' }
            };
            
            // 加载每个模块
            for (const [moduleName, config] of Object.entries(moduleConfig)) {
                try {
                    // 构建模块路径
                    const modulePath = path.join(__dirname, config.path);
                    
                    // 检查模块是否存在
                    if (!fs.existsSync(`${modulePath}.js`)) {
                        this.logger.warn('MAIN', `模块不存在: ${moduleName}`);
                        continue;
                    }
                    
                    // 动态导入模块
                    const module = require(modulePath);
                    
                    // 获取导出的类或对象
                    const exportItem = module[config.export];
                    
                    if (exportItem) {
                        this.modules.set(moduleName, {
                            config,
                            module,
                            exportItem,
                            instance: null,
                            isInitialized: false
                        });
                        
                        this.logger.info('MAIN', `加载模块: ${moduleName}`);
                    } else {
                        this.logger.warn('MAIN', `模块导出项不存在: ${moduleName}.${config.export}`);
                    }
                } catch (error) {
                    this.logger.error('MAIN', `加载模块 ${moduleName} 失败`, error);
                }
            }
        } catch (error) {
            this.logger.error('MAIN', '模块加载失败', error);
        }
    }

    /**
     * 初始化所有模块
     */
    async initializeModules() {
        try {
            this.logger.info('MAIN', '开始初始化所有模块...');
            
            for (const [moduleName, moduleInfo] of this.modules.entries()) {
                try {
                    // 跳过已初始化的模块
                    if (moduleInfo.isInitialized) {
                        continue;
                    }
                    
                    // 获取模块配置
                    const moduleConfig = configManager.get(moduleName, {});
                    
                    // 检查模块是否启用
                    if (moduleConfig.enabled === false) {
                        this.logger.info('MAIN', `模块已禁用: ${moduleName}`);
                        continue;
                    }
                    
                    // 创建模块实例
                    let instance;
                    if (typeof moduleInfo.exportItem === 'function') {
                        // 构造函数
                        instance = new moduleInfo.exportItem();
                    } else {
                        // 已实例化的对象
                        instance = moduleInfo.exportItem;
                    }
                    
                    // 设置实例
                    moduleInfo.instance = instance;
                    
                    // 初始化模块（如果有initialize方法）
                    if (instance.initialize && typeof instance.initialize === 'function') {
                        const success = await instance.initialize();
                        
                        if (success) {
                            moduleInfo.isInitialized = true;
                            this.logger.info('MAIN', `模块初始化成功: ${moduleName}`);
                        } else {
                            this.logger.error('MAIN', `模块初始化失败: ${moduleName}`);
                            continue;
                        }
                    } else {
                        // 没有初始化方法，标记为已初始化
                        moduleInfo.isInitialized = true;
                        this.logger.info('MAIN', `模块无需初始化: ${moduleName}`);
                    }
                    
                    // 设置日志器（如果支持）
                    if (instance.setLogger && typeof instance.setLogger === 'function') {
                        instance.setLogger(this.logger.getLogger(moduleName));
                    }
                    
                    // 设置配置管理器（如果支持）
                    if (instance.setConfigManager && typeof instance.setConfigManager === 'function') {
                        instance.setConfigManager(configManager);
                    }
                } catch (error) {
                    this.logger.error('MAIN', `初始化模块 ${moduleName} 失败`, error);
                }
            }
            
            this.logger.info('MAIN', '所有模块初始化完成');
        } catch (error) {
            this.logger.error('MAIN', '模块初始化过程失败', error);
        }
    }

    /**
     * 启动所有模块
     */
    async start() {
        try {
            if (!this.isInitialized) {
                await this.initialize();
                
                // 检查初始化是否成功
                if (!this.isInitialized) {
                    console.error('初始化失败，无法启动系统');
                    return false;
                }
            }
            
            this.logger.info('MAIN', '正在启动 MTSCOS AI 灰度测试环境...');
            
            // 初始化所有模块
            await this.initializeModules();
            
            // 启动所有已初始化的模块
            for (const [moduleName, moduleInfo] of this.modules.entries()) {
                if (moduleInfo.isInitialized && moduleInfo.instance) {
                    try {
                        if (moduleInfo.instance.start && typeof moduleInfo.instance.start === 'function') {
                            await moduleInfo.instance.start();
                            this.logger.info('MAIN', `模块启动成功: ${moduleName}`);
                        }
                    } catch (error) {
                        this.logger.error('MAIN', `启动模块 ${moduleName} 失败`, error);
                    }
                }
            }
            
            this.isRunning = true;
            this.logger.info('MAIN', 'MTSCOS AI 灰度测试环境启动完成!');
            
            // 显示启动信息
            this.showStartInfo();
            
            return true;
        } catch (error) {
            console.error('系统启动失败:', error);
            if (this.logger) {
                this.logger.error('MAIN', '系统启动失败', error);
            }
            return false;
        }
    }

    /**
     * 停止所有模块
     */
    async stop() {
        try {
            this.logger.info('MAIN', '正在停止 MTSCOS AI 灰度测试环境...');
            
            // 停止所有已初始化的模块
            for (const [moduleName, moduleInfo] of this.modules.entries()) {
                if (moduleInfo.isInitialized && moduleInfo.instance) {
                    try {
                        if (moduleInfo.instance.stop && typeof moduleInfo.instance.stop === 'function') {
                            await moduleInfo.instance.stop();
                            this.logger.info('MAIN', `模块停止成功: ${moduleName}`);
                        } else if (moduleInfo.instance.shutdown && typeof moduleInfo.instance.shutdown === 'function') {
                            await moduleInfo.instance.shutdown();
                            this.logger.info('MAIN', `模块关闭成功: ${moduleName}`);
                        }
                    } catch (error) {
                        this.logger.error('MAIN', `停止模块 ${moduleName} 失败`, error);
                    }
                }
            }
            
            this.isRunning = false;
            this.logger.info('MAIN', 'MTSCOS AI 灰度测试环境停止完成!');
            
            return true;
        } catch (error) {
            this.logger.error('MAIN', '系统停止失败', error);
            return false;
        }
    }

    /**
     * 重启系统
     */
    async restart() {
        try {
            this.logger.info('MAIN', '正在重启 MTSCOS AI 灰度测试环境...');
            
            // 先停止
            await this.stop();
            
            // 再启动
            await this.start();
            
            this.logger.info('MAIN', '系统重启完成!');
            return true;
        } catch (error) {
            this.logger.error('MAIN', '系统重启失败', error);
            return false;
        }
    }

    /**
     * 显示启动信息
     */
    showStartInfo() {
        console.log('\n' + '='.repeat(60));
        console.log('MTSCOS AI 灰度测试环境');
        console.log('='.repeat(60));
        
        const configSummary = configManager.getConfigSummary();
        console.log(`\n系统名称: ${configSummary.system.name}`);
        console.log(`版本: ${configSummary.system.version}`);
        console.log(`环境: ${configSummary.system.environment}`);
        
        console.log('\n已加载的模块:');
        for (const [moduleName, moduleInfo] of this.modules.entries()) {
            const status = moduleInfo.isInitialized ? '✓ 已初始化' : '✗ 未初始化';
            console.log(`  - ${moduleName}: ${status}`);
        }
        
        console.log('\n访问地址:');
        console.log(`  - 主页面: http://localhost:8000/Staging/HTML/index.html`);
        console.log(`  - 设置页面: http://localhost:8000/Staging/HTML/settings/color-scheme-settings.html`);
        
        console.log('\n' + '='.repeat(60));
        console.log('系统已准备就绪!');
        console.log('='.repeat(60) + '\n');
    }

    /**
     * 获取系统状态
     */
    getStatus() {
        const moduleStatus = {};
        
        for (const [moduleName, moduleInfo] of this.modules.entries()) {
            moduleStatus[moduleName] = {
                isInitialized: moduleInfo.isInitialized,
                isRunning: this.isRunning && moduleInfo.isInitialized
            };
        }
        
        return {
            isInitialized: this.isInitialized,
            isRunning: this.isRunning,
            modules: moduleStatus,
            configSummary: configManager.getConfigSummary()
        };
    }

    /**
     * 获取模块实例
     */
    getModule(moduleName) {
        const moduleInfo = this.modules.get(moduleName);
        return moduleInfo ? moduleInfo.instance : null;
    }
}

// 创建全局管理器实例
const mtscosManager = new MTSCOSManager();

// 命令行接口
async function main() {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        // 默认启动系统
        await mtscosManager.start();
        return;
    }
    
    const command = args[0].toLowerCase();
    
    switch (command) {
        case 'start':
            await mtscosManager.start();
            break;
            
        case 'stop':
            await mtscosManager.stop();
            break;
            
        case 'restart':
            await mtscosManager.restart();
            break;
            
        case 'status':
            const status = mtscosManager.getStatus();
            console.log(JSON.stringify(status, null, 2));
            break;
            
        case 'init':
            await mtscosManager.initialize();
            break;
            
        case 'help':
        case '--help':
        case '-h':
            showHelp();
            break;
            
        default:
            console.error(`未知命令: ${command}`);
            showHelp();
            process.exit(1);
    }
}

// 显示帮助信息
function showHelp() {
    console.log('MTSCOS AI 灰度测试环境管理器');
    console.log('用法: node main-manager.js [命令]');
    console.log('\n命令:');
    console.log('  start     启动系统');
    console.log('  stop      停止系统');
    console.log('  restart   重启系统');
    console.log('  status    显示系统状态');
    console.log('  init      初始化系统');
    console.log('  help      显示帮助信息');
}

// 处理退出信号
process.on('SIGINT', async () => {
    console.log('\n接收到停止信号，正在优雅关闭系统...');
    await mtscosManager.stop();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('\n接收到终止信号，正在优雅关闭系统...');
    await mtscosManager.stop();
    process.exit(0);
});

// 处理未捕获的异常
process.on('uncaughtException', (error) => {
    console.error('未捕获的异常:', error);
    mtscosManager.logger?.fatal('MAIN', '未捕获的异常', error);
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('未处理的 Promise 拒绝:', reason);
    mtscosManager.logger?.fatal('MAIN', '未处理的 Promise 拒绝', reason);
    process.exit(1);
});

// 导出模块
module.exports = {
    MTSCOSManager,
    mtscosManager
};

// 如果直接运行此脚本
if (require.main === module) {
    main();
}

/**
 * 使用示例:
 * 
 * # 启动系统
 * node main-manager.js start
 * 
 * # 停止系统
 * node main-manager.js stop
 * 
 * # 查看系统状态
 * node main-manager.js status
 * 
 * # 重启系统
 * node main-manager.js restart
 */
