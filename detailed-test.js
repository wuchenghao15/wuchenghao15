#!/usr/bin/env node

const path = require('path');
const fs = require('fs');
const { promisify } = require('util');

async function runTests() {
    // 测试基础依赖
    console.log('测试基础依赖...');
    console.log('fs模块:', fs ? '可用' : '不可用');
    console.log('path模块:', path ? '可用' : '不可用');
    console.log('promisify:', promisify ? '可用' : '不可用');
    
    try {
        const mkdirp = require('mkdirp');
        console.log('mkdirp模块:', mkdirp ? '可用' : '不可用');
        const mkdirpAsync = promisify(mkdirp);
        console.log('mkdirpAsync:', mkdirpAsync ? '可用' : '不可用');
    } catch (error) {
        console.error('mkdirp模块测试失败:', error.message);
    }
    
    // 测试文件路径处理
    console.log('\n测试文件路径处理...');
    const testPath = './test/test.log';
    console.log('测试路径:', testPath);
    console.log('dirname:', path.dirname(testPath));
    
    // 测试文件流创建
    console.log('\n测试文件流创建...');
    try {
        const stream = fs.createWriteStream('./test-direct.log', { flags: 'a', encoding: 'utf8' });
        stream.write('测试写入\n');
        stream.end();
        console.log('文件流创建成功');
    } catch (error) {
        console.error('文件流创建失败:', error.message);
        console.error('错误代码:', error.code);
    }
    
    // 测试日志目标直接初始化
    console.log('\n测试日志目标直接初始化...');
    try {
        const { ConsoleLogTarget } = require('./Staging/Scripts/monitoring/enhanced-logger');
        const consoleTarget = new ConsoleLogTarget();
        console.log('ConsoleLogTarget创建成功');
        
        // 测试ConsoleLogTarget的write方法
        consoleTarget.write({ level: 1, module: 'TEST', timestamp: new Date() }, '测试控制台输出');
    } catch (error) {
        console.error('ConsoleLogTarget测试失败:', error);
    }
    
    try {
        const { FileLogTarget } = require('./Staging/Scripts/monitoring/enhanced-logger');
        const fileTarget = new FileLogTarget({ filePath: './test-file.log' });
        console.log('FileLogTarget创建成功');
        console.log('FileLogTarget选项:', fileTarget.options);
        
        // 测试mkdirp单独使用
        const mkdirpModule = require('mkdirp');
        const mkdirpAsync = promisify(mkdirpModule);
        const dir = path.dirname('./test-file.log');
        console.log('准备创建目录:', dir);
        await mkdirpAsync(dir);
        console.log('目录创建成功');
        
        // 测试openFileStream直接调用
        await fileTarget.openFileStream();
        console.log('openFileStream调用成功');
        
    } catch (error) {
        console.error('FileLogTarget测试失败:', error);
        console.error('错误堆栈:', error.stack);
    }
}

// 执行测试
runTests().catch(error => {
    console.error('测试执行失败:', error);
    process.exit(1);
});