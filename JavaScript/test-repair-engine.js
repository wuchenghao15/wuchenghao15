#!/usr/bin/env node

const RepairEngine = require('./repair-engine');
const path = require('path');
const fs = require('fs');

// 测试配置
const testConfig = {
    deepseek: {
        apiKey: 'sk-demo-key-for-local-testing',
        baseUrl: 'https://api.deepseek.com',
        model: 'deepseek-coder',
        maxTokens: 1024,
        temperature: 0.3,
        timeout: 30000
    },
    cache: {
        enabled: true,
        maxSize: 100,
        ttl: 3600000
    },
    logger: {
        level: 'info',
        format: 'json'
    }
};

// 创建测试文件
const testDir = path.join(__dirname, 'test-repair');
if (!fs.existsSync(testDir)) {
    fs.mkdirSync(testDir);
}

// 创建测试用的有问题的JavaScript文件
const testFile = path.join(testDir, 'problematic.js');
fs.writeFileSync(testFile, `// 测试文件 - 包含各种问题
function problematicFunction() {
    // 空的if语句
    if (true) {
    }
    
    // 调试日志
    console.log('调试信息');
    
    // 安全漏洞 - eval
    const userInput = 'alert("恶意代码")';
    eval(userInput);
    
    // 逻辑错误 - 空循环
    for (let i = 0; i < 10; i++) {
    }
    
    return true;
}

// 语法错误示例
function syntaxErrorFunction() {
    let x = 10
    let y = 20
    return x + y
}
`, 'utf8');

console.log('测试文件已创建:', testFile);

// 测试修复引擎
async function testRepairEngine() {
    console.log('\n=== 开始测试修复引擎 ===');
    
    try {
        // 创建修复引擎实例
        const repairEngine = new RepairEngine(testConfig);
        
        // 初始化修复引擎
        console.log('1. 初始化修复引擎...');
        await repairEngine.initialize();
        console.log('✅ 修复引擎初始化成功');
        
        // 测试文件修复
        console.log('\n2. 测试单个文件修复...');
        const fileRepairResult = await repairEngine.repairFile(testFile);
        console.log('文件修复结果:', JSON.stringify(fileRepairResult, null, 2));
        
        // 测试目录修复
        console.log('\n3. 测试目录修复...');
        const dirRepairResult = await repairEngine.repairDirectory(testDir, ['.js']);
        console.log('目录修复结果:', JSON.stringify(dirRepairResult, null, 2));
        
        // 获取修复引擎状态
        console.log('\n4. 获取修复引擎状态...');
        const status = repairEngine.getStatus();
        console.log('修复引擎状态:', JSON.stringify(status, null, 2));
        
        // 清理测试文件
        console.log('\n5. 清理测试文件...');
        fs.unlinkSync(testFile);
        fs.rmdirSync(testDir);
        console.log('✅ 测试文件清理完成');
        
        console.log('\n=== 修复引擎测试完成 ===');
        return true;
    } catch (error) {
        console.error('❌ 测试失败:', error);
        return false;
    }
}

// 运行测试
testRepairEngine().then(success => {
    process.exit(success ? 0 : 1);
}).catch(error => {
    console.error('❌ 测试过程中发生未捕获的错误:', error);
    process.exit(1);
});