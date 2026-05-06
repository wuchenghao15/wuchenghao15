// 日语题库自动同步脚本
// 监控题库文件变更并自动同步到数据库

const fs = require('fs');
const path = require('path');
const japaneseDatabaseManager = require('../src/core/database/japanese-database-manager');



class JapaneseDatabaseAutoSync {
    constructor() {
        this.watcher = null;
        this.syncing = false;
        this.lastSyncTime = null;
        this.logFile = path.join(__dirname, '../logs/japanese-database-sync.log');
        
        // 确保日志目录存在
        this.ensureLogDirectory();
        
        // 初始化数据库管理器
        this.initDatabaseManager();
    }
    
    // 确保日志目录存在
    ensureLogDirectory() {
        const logDir = path.join(__dirname, '../logs');
        if (!fs.existsSync(logDir)) {
            fs.mkdirSync(logDir, { recursive: true });
        }
    }
    
    // 初始化数据库管理器
    async initDatabaseManager() {
        try {
            await japaneseDatabaseManager.initialize();
            this.log('✅ 日语题库数据库管理器初始化成功');
        } catch (error) {
            this.log(`❌ 初始化失败: ${error.message}`);
            throw error;
        }
    }
    
    // 开始监控
    startMonitoring() {
        const watchPaths = [
            path.join(__dirname, 'initialize-japanese-database.js'),
            path.join(__dirname, '../src/core/database/japanese-database-manager.js'),
            path.join(__dirname, '../src/core/database/japanese-review-plan-manager.js')
        ];
        
        this.log(`🚀 开始监控题库文件变更: ${watchPaths.join(', ')}`);
        
        // 使用fs.watch来监控文件变化
        watchPaths.forEach((watchPath) => {
            try {
                fs.watch(watchPath, {
                    persistent: true,
                    recursive: false
                }, (eventType, filename) => {
                    if (eventType === 'change') {
                        this.log(`📁 文件变更: ${watchPath}`);
                        this.syncDatabase();
                    }
                });
                this.log(`✅ 成功监控文件: ${watchPath}`);
            } catch (error) {
                this.log(`❌ 监控文件失败: ${watchPath}, 错误: ${error.message}`);
            }
        });
        
        this.log('✅ 自动同步监控已启动');
    }
    
    // 同步数据库
    async syncDatabase() {
        if (this.syncing) {
            this.log('⏳ 同步已在进行中，跳过本次同步');
            return;
        }
        
        this.syncing = true;
        this.log('🔄 开始同步日语题库到数据库...');
        
        try {
            // 确保数据库管理器已初始化
            await japaneseDatabaseManager.initialize();
            
            // 加载题目数据
            const { sampleQuestions } = require('./initialize-japanese-database');
            
            // 添加题目到数据库
            const result = await japaneseDatabaseManager.addQuestions(sampleQuestions);
            
            this.lastSyncTime = new Date();
            
            this.log(`✅ 日语题库同步完成:`);
            this.log(`   总计: ${result.total} 题`);
            this.log(`   成功: ${result.successful} 题`);
            this.log(`   失败: ${result.failed} 题`);
            
            // 尝试获取最新的统计信息
            try {
                const stats = await japaneseDatabaseManager.getStatistics();
                this.log('📊 最新题库统计信息:');
                stats.forEach(stat => {
                    this.log(`   ${stat.level} ${stat.type}: ${stat.count}题 (难度: ${stat.avg_difficulty.toFixed(1)})`);
                });
            } catch (statsError) {
                this.log(`⚠️  获取统计信息失败: ${statsError.message}`);
                this.log('   统计信息获取失败，但同步过程已完成');
            }
            
        } catch (error) {
            this.log(`❌ 同步失败: ${error.message}`);
            this.log(`   错误堆栈: ${error.stack}`);
        } finally {
            this.syncing = false;
        }
    }
    
    // 手动触发同步
    async triggerSync() {
        this.log('🔄 手动触发日语题库同步...');
        await this.syncDatabase();
    }
    
    // 停止监控
    stopMonitoring() {
        if (this.watcher) {
            this.watcher.close();
            this.log('✅ 自动同步监控已停止');
        }
        
        // 关闭数据库连接
        japaneseDatabaseManager.close();
        this.log('✅ 数据库连接已关闭');
    }
    
    // 记录日志
    log(message) {
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] ${message}`;
        
        console.log(logMessage);
        
        // 写入日志文件
        try {
            fs.appendFileSync(this.logFile, logMessage + '\n');
        } catch (error) {
            console.error(`❌ 写入日志文件失败: ${error.message}`);
        }
    }
}

// 主函数
async function main() {
    console.log('🚀 日语题库自动同步工具');
    console.log('=======================');
    
    try {
        const syncTool = new JapaneseDatabaseAutoSync();
        
        // 立即执行一次同步
        await syncTool.triggerSync();
        
        // 开始监控
        syncTool.startMonitoring();
        
        // 处理进程终止
        process.on('SIGINT', () => {
            console.log('\n🛑 正在停止自动同步工具...');
            syncTool.stopMonitoring();
            process.exit(0);
        });
        
        process.on('SIGTERM', () => {
            console.log('\n🛑 正在停止自动同步工具...');
            syncTool.stopMonitoring();
            process.exit(0);
        });
        
        console.log('\n✅ 自动同步工具已启动');
        console.log('📝 日志输出到: scripts/../logs/japanese-database-sync.log');
        console.log('⌨️  按 Ctrl+C 停止工具');
        
    } catch (error) {
        console.error(`❌ 启动失败: ${error.message}`);
        process.exit(1);
    }
}

// 执行主函数
if (require.main === module) {
    main();
}

module.exports = JapaneseDatabaseAutoSync;
