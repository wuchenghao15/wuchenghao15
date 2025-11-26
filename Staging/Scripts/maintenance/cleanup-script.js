/**
 * 测试环境清理脚本
 * 用途: 清理过期文件和临时文件，保持环境整洁
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('开始执行测试环境清理...');

// 配置信息（应该从配置文件读取，但这里硬编码为示例）
const config = {
    basePath: process.env.BASE_PATH || '../..',
    tempPath: 'Temp',
    logsPath: 'Logs',
    resultsPath: 'Results',
    retentionDays: {
        logs: 14,
        results: 7
    },
    cleanupPatterns: [
        '*.tmp',
        '*.temp',
        '~*',
        '*.bak'
    ],
    excludePatterns: [
        '.git/',
        'Backups/',
        'Logs/'
    ]
};

// 计算截止日期
function getCutoffDate(days) {
    const date = new Date();
    date.setDate(date.getDate() - days);
    return date;
}

// 递归删除目录
function deleteDirectory(dirPath) {
    if (!fs.existsSync(dirPath)) return;
    
    const files = fs.readdirSync(dirPath);
    for (const file of files) {
        const filePath = path.join(dirPath, file);
        if (fs.statSync(filePath).isDirectory()) {
            deleteDirectory(filePath);
        } else {
            fs.unlinkSync(filePath);
        }
    }
    
    fs.rmdirSync(dirPath);
}

// 清理过期文件
function cleanupOldFiles(dirPath, days) {
    if (!fs.existsSync(dirPath)) return;
    
    const cutoffDate = getCutoffDate(days);
    let deletedCount = 0;
    
    function processDir(currentPath) {
        const files = fs.readdirSync(currentPath);
        for (const file of files) {
            const filePath = path.join(currentPath, file);
            const stats = fs.statSync(filePath);
            
            if (stats.isDirectory()) {
                // 检查是否需要排除此目录
                const shouldExclude = config.excludePatterns.some(pattern => 
                    filePath.includes(pattern)
                );
                
                if (!shouldExclude) {
                    processDir(filePath);
                    // 检查目录是否为空
                    const subFiles = fs.readdirSync(filePath);
                    if (subFiles.length === 0) {
                        fs.rmdirSync(filePath);
                        deletedCount++;
                    }
                }
            } else if (stats.mtime < cutoffDate) {
                // 检查文件是否匹配清理模式
                const shouldDelete = config.cleanupPatterns.some(pattern => {
                    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
                    return regex.test(file);
                });
                
                if (shouldDelete || pattern === '*') {
                    fs.unlinkSync(filePath);
                    deletedCount++;
                }
            }
        }
    }
    
    processDir(dirPath);
    console.log(`已清理 ${deletedCount} 个过期文件`);
}

// 清理临时目录
function cleanupTempDirectory() {
    const tempDir = path.join(config.basePath, config.tempPath);
    if (fs.existsSync(tempDir)) {
        console.log(`清理临时目录: ${tempDir}`);
        const files = fs.readdirSync(tempDir);
        for (const file of files) {
            const filePath = path.join(tempDir, file);
            if (fs.statSync(filePath).isDirectory()) {
                deleteDirectory(filePath);
            } else {
                fs.unlinkSync(filePath);
            }
        }
        console.log(`临时目录清理完成，共清理 ${files.length} 个文件`);
    } else {
        console.log('临时目录不存在');
    }
}

// 清理日志文件
function cleanupLogFiles() {
    const logDir = path.join(config.basePath, config.logsPath);
    console.log(`清理过期日志文件: ${logDir}`);
    cleanupOldFiles(logDir, config.retentionDays.logs);
}

// 清理测试结果
function cleanupTestResults() {
    const resultsDir = path.join(config.basePath, config.resultsPath);
    console.log(`清理过期测试结果: ${resultsDir}`);
    cleanupOldFiles(resultsDir, config.retentionDays.results);
}

// 检查磁盘使用情况
function checkDiskUsage() {
    try {
        console.log('检查磁盘使用情况...');
        // 在不同操作系统上可能需要调整命令
        const output = execSync('df -h').toString();
        console.log(output);
    } catch (error) {
        console.error('检查磁盘使用情况失败:', error.message);
    }
}

// 主函数
function main() {
    try {
        const startTime = new Date();
        
        console.log('======================');
        console.log(`开始时间: ${startTime.toISOString()}`);
        console.log('======================');
        
        // 执行清理任务
        cleanupTempDirectory();
        cleanupLogFiles();
        cleanupTestResults();
        checkDiskUsage();
        
        const endTime = new Date();
        const duration = (endTime - startTime) / 1000;
        
        console.log('======================');
        console.log(`结束时间: ${endTime.toISOString()}`);
        console.log(`总耗时: ${duration.toFixed(2)} 秒`);
        console.log('清理完成!');
    } catch (error) {
        console.error('清理过程中发生错误:', error.message);
        process.exit(1);
    }
}

// 执行主函数
main();
