#!/usr/bin/env node

// 测试mkdirp 1.0.4的正确使用方式
const mkdirp = require('mkdirp');

console.log('mkdirp版本:', require('./node_modules/mkdirp/package.json').version);

// 测试1: 基本使用
console.log('\n测试1: 基本使用 - mkdirp("./test-dir", callback)');
mkdirp('./test-dir', (err) => {
    if (err) {
        console.error('测试1失败:', err.message);
        console.error('错误堆栈:', err.stack);
    } else {
        console.log('测试1成功: 目录创建成功');
    }
});

// 测试2: 测试promisify
console.log('\n测试2: promisify包装');
const { promisify } = require('util');
const mkdirpAsync = promisify(mkdirp);

async function testPromisify() {
    try {
        await mkdirpAsync('./test-dir-async');
        console.log('测试2成功: promisify创建目录成功');
    } catch (error) {
        console.error('测试2失败:', error.message);
        console.error('错误堆栈:', error.stack);
    }
}

testPromisify();