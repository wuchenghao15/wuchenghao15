#!/usr/bin/env node

const path = require('path');
const { EnhancedLogger, LOG_LEVELS, ConsoleLogTarget, FileLogTarget } = require('./Staging/Scripts/monitoring/enhanced-logger');

async function testLogger() {
    console.log('开始测试日志系统...');
    
    try {
        // 测试1: 仅使用控制台日志目标
        console.log('\n测试1: 仅使用控制台日志目标');
        const logger1 = new EnhancedLogger({
            level: LOG_LEVELS.INFO,
            targets: [new ConsoleLogTarget()]
        });
        await logger1.initialize();
        logger1.info('TEST', '控制台日志测试成功');
        
        // 测试2: 使用文件日志目标（简单配置）
        console.log('\n测试2: 使用文件日志目标（简单配置）');
        const logger2 = new EnhancedLogger({
            level: LOG_LEVELS.INFO,
            targets: [
                new ConsoleLogTarget(),
                new FileLogTarget({
                    filePath: './test.log'
                })
            ]
        });
        await logger2.initialize();
        logger2.info('TEST', '文件日志测试成功');
        
        console.log('\n所有测试通过！');
        
    } catch (error) {
        console.error('测试失败:', error);
        console.error('错误堆栈:', error.stack);
    }
}

testLogger();