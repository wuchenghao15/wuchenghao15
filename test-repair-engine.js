#!/usr/bin/env node

const path = require('path');
const fs = require('fs').promises;
const { promisify } = require('util');
const exec = promisify(require('child_process').exec);

// 导入修复引擎和本地脚本
const RepairEngine = require('./JavaScript/repair-engine');
const ErrorFixer = require('./Scripts/error-fixer');

// 创建测试目录和测试文件
async function setupTestEnvironment() {
    console.log('设置测试环境...');
    
    // 创建测试目录
    const testDir = path.join(__dirname, 'test-repair-engine');
    const jsDir = path.join(testDir, 'js');
    const cssDir = path.join(testDir, 'css');
    const htmlDir = path.join(testDir, 'html');
    
    // 确保目录存在
    await fs.mkdir(jsDir, { recursive: true });
    await fs.mkdir(cssDir, { recursive: true });
    await fs.mkdir(htmlDir, { recursive: true });
    
    // 创建有问题的JS文件
    const problematicJs = `
var x = 10;
var y = 20;
if (x = y) {
    console.log('x等于y');
}
function oldStyle() {
    return "old";
}
console.log("调试信息", x, y);
    `;
    await fs.writeFile(path.join(jsDir, 'problematic.js'), problematicJs);
    
    // 创建有问题的CSS文件
    const problematicCss = `
body {
    font-size: 16px;
    color: red;
}

.container {
    width: 100%;
    margin: 0 auto;
    padding: 20px
}

.button {
    background-color: blue;
    color: white;
    padding: 10px 20px;
    border: none;
    cursor: pointer;
}
    `;
    await fs.writeFile(path.join(cssDir, 'problematic.css'), problematicCss);
    
    // 创建有问题的HTML文件
    const problematicHtml = `
<html>
<head>
    <title>测试页面</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <h1>测试页面</h1>
        <p>这是一个测试段落。</p>
        <img src="image.jpg" alt="测试图片">
        <button onclick="alert('测试')">点击我</button>
    </div>
</body>
</html>
    `;
    await fs.writeFile(path.join(htmlDir, 'problematic.html'), problematicHtml);
    
    console.log('测试环境设置完成');
    return { testDir, jsDir, cssDir, htmlDir };
}

// 清理测试环境
async function cleanupTestEnvironment(testDir) {
    console.log('清理测试环境...');
    await fs.rm(testDir, { recursive: true, force: true });
    console.log('测试环境清理完成');
}

// 测试修复引擎的初始化
async function testRepairEngineInit() {
    console.log('\n测试修复引擎初始化...');
    try {
        const engine = new RepairEngine({ 
            fileTypes: ['.js', '.jsx', '.ts', '.tsx', '.css', '.html'],
            logEnabled: true
        });
        console.log('✅ 修复引擎初始化成功');
        return engine;
    } catch (error) {
        console.error('❌ 修复引擎初始化失败:', error.message);
        throw error;
    }
}

// 测试修复引擎的源码分析能力
async function testRepairEngineAnalysis(engine, jsDir) {
    console.log('\n测试修复引擎源码分析能力...');
    try {
        const jsFilePath = path.join(jsDir, 'problematic.js');
        const detectionResult = await engine.detectIssuesInFile(jsFilePath);
        const issues = detectionResult.issues || [];
        console.log(`✅ 源码分析完成，发现 ${issues.length} 个问题`);
        issues.forEach((issue, index) => {
            console.log(`  ${index + 1}. ${issue.type}: ${issue.description || issue.message} (行 ${issue.line})`);
        });
        return issues;
    } catch (error) {
        console.error('❌ 源码分析失败:', error.message);
        throw error;
    }
}

// 测试修复引擎的修复能力
async function testRepairEngineFix(engine, jsDir) {
    console.log('\n测试修复引擎修复能力...');
    try {
        const jsFilePath = path.join(jsDir, 'problematic.js');
        const result = await engine.repairFile(jsFilePath);
        console.log(`✅ 文件修复完成: ${result.success ? '成功' : '失败'}`);
        if (result.success) {
            console.log('  修复的问题:', result.fixedIssues.length);
            if (result.fixedContent) {
                console.log('  修复后的代码预览:', result.fixedContent.substring(0, 100) + '...');
            } else {
                console.log('  文件无需修复，保持原样');
            }
        }
        return result;
    } catch (error) {
        console.error('❌ 文件修复失败:', error.message);
        throw error;
    }
}

// 测试本地脚本的文件扫描和修复功能
async function testErrorFixer(testDir) {
    console.log('\n测试本地脚本的文件扫描和修复功能...');
    try {
        const fixer = new ErrorFixer();
        const result = await fixer.run();
        console.log(`✅ 本地脚本运行完成`);
        console.log(`  扫描的文件数: ${result.totalFiles}`);
        console.log(`  修复的文件数: ${result.fixedFiles}`);
        console.log(`  发现的问题数: ${result.totalIssues}`);
        console.log(`  修复的问题数: ${result.fixedIssues}`);
        return result;
    } catch (error) {
        console.error('❌ 本地脚本运行失败:', error.message);
        throw error;
    }
}

// 测试不同文件类型的修复能力
async function testFileTypeFixing(engine, cssDir, htmlDir) {
    console.log('\n测试不同文件类型的修复能力...');
    
    // 测试CSS文件修复
    try {
        const cssFilePath = path.join(cssDir, 'problematic.css');
        const cssResult = await engine.repairFile(cssFilePath);
        console.log(`✅ CSS文件修复: ${cssResult.success ? '成功' : '失败'}`);
        if (cssResult.success) {
            console.log(`  修复的CSS问题: ${cssResult.fixedIssues.length}`);
        }
    } catch (error) {
        console.error('❌ CSS文件修复失败:', error.message);
    }
    
    // 测试HTML文件修复
    try {
        const htmlFilePath = path.join(htmlDir, 'problematic.html');
        const htmlResult = await engine.repairFile(htmlFilePath);
        console.log(`✅ HTML文件修复: ${htmlResult.success ? '成功' : '失败'}`);
        if (htmlResult.success) {
            console.log(`  修复的HTML问题: ${htmlResult.fixedIssues.length}`);
        }
    } catch (error) {
        console.error('❌ HTML文件修复失败:', error.message);
    }
}

// 执行所有测试
async function runAllTests() {
    console.log('开始测试修复引擎功能...');
    console.log('=' . repeat(60));
    
    let testEnvironment = null;
    
    try {
        // 设置测试环境
        testEnvironment = await setupTestEnvironment();
        
        // 测试修复引擎初始化
        const engine = await testRepairEngineInit();
        
        // 测试源码分析能力
        await testRepairEngineAnalysis(engine, testEnvironment.jsDir);
        
        // 测试修复能力
        await testRepairEngineFix(engine, testEnvironment.jsDir);
        
        // 测试本地脚本
        await testErrorFixer(testEnvironment.testDir);
        
        // 测试不同文件类型修复
        await testFileTypeFixing(engine, testEnvironment.cssDir, testEnvironment.htmlDir);
        
        console.log('\n' + '=' . repeat(60));
        console.log('🎉 所有测试完成！');
        
    } catch (error) {
        console.error('\n' + '=' . repeat(60));
        console.error('❌ 测试失败:', error.message);
        process.exit(1);
    } finally {
        // 清理测试环境
        if (testEnvironment) {
            await cleanupTestEnvironment(testEnvironment.testDir);
        }
    }
}

// 执行测试
runAllTests();
