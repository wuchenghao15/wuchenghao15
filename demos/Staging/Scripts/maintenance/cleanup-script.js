/**
 * 测试环境清理脚本
 * 用途: 清理过期文件和临时文件，保持环境整洁
 */

// const fs = require('fs'); /* 代码质量修复：未使用的 常量 */
// const path = require('path'); /* 代码质量修复：未使用的 常量 */
const { execSync } = require('child_process');

// /* 修复：注释掉调试日志 */ // console.log('开始执行测试环境清理...'); /* 代码质量修复：调试语句 */

// 配置信息（应该从配置文件读取，但这里硬编码为示例）
// const config = { /* 代码质量修复：未使用的 常量 */
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
    ];
};

// 计算截止日期
// function getCutoffDate(days) { /* 代码质量修复：未使用的函数 */
// //     const date = new Date(); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//     date.setDate(date.getDate() - days); /* 代码质量修复：未使用的函数 */
//     return date; /* 代码质量修复：未使用的函数 */
// } /* 代码质量修复：未使用的函数 */

// 递归删除目录
// function deleteDirectory(dirPath) { /* 代码质量修复：未使用的函数 */
//     if (!fs.existsSync(dirPath)) return; /* 代码质量修复：未使用的函数 */
//      /* 代码质量修复：未使用的函数 */
// //     const files = fs.readdirSync(dirPath); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//     for (const file of files) { /* 代码质量修复：未使用的函数 */
// //         const filePath = path.join(dirPath, file); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//         if (fs.statSync(filePath).isDirectory()) { /* 代码质量修复：未使用的函数 */
//             deleteDirectory(filePath); /* 代码质量修复：未使用的函数 */
//         } else { /* 代码质量修复：未使用的函数 */
//             fs.unlinkSync(filePath); /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */
//     } /* 代码质量修复：未使用的函数 */
//      /* 代码质量修复：未使用的函数 */
//     fs.rmdirSync(dirPath); /* 代码质量修复：未使用的函数 */
// } /* 代码质量修复：未使用的函数 */

// 清理过期文件
// function cleanupOldFiles(dirPath, days) { /* 代码质量修复：未使用的函数 */
//     if (!fs.existsSync(dirPath)) return; /* 代码质量修复：未使用的函数 */
//      /* 代码质量修复：未使用的函数 */
// //     const cutoffDate = getCutoffDate(days); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //     let deletedCount = 0; /* 代码质量修复：未使用的 变量 */ /* 代码质量修复：未使用的函数 */
//      /* 代码质量修复：未使用的函数 */
//     function processDir(currentPath) { /* 代码质量修复：未使用的函数 */
// //         const files = fs.readdirSync(currentPath); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//         for (const file of files) { /* 代码质量修复：未使用的函数 */
// //             const filePath = path.join(currentPath, file); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //             const stats = fs.statSync(filePath); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//              /* 代码质量修复：未使用的函数 */
//             if (stats.isDirectory()) { /* 代码质量修复：未使用的函数 */
//                 // 检查是否需要排除此目录 /* 代码质量修复：未使用的函数 */
// //                 const shouldExclude = config.excludePatterns.some(pattern =>  /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                     filePath.includes(pattern) /* 代码质量修复：未使用的函数 */
//                 ); /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 if (!shouldExclude) { /* 代码质量修复：未使用的函数 */
//                     processDir(filePath); /* 代码质量修复：未使用的函数 */
//                     // 检查目录是否为空 /* 代码质量修复：未使用的函数 */
// //                     const subFiles = fs.readdirSync(filePath); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                     if (subFiles.length === 0) { /* 代码质量修复：未使用的函数 */
//                         fs.rmdirSync(filePath); /* 代码质量修复：未使用的函数 */
//                         deletedCount++; /* 代码质量修复：未使用的函数 */
//                     } /* 代码质量修复：未使用的函数 */
//                 } /* 代码质量修复：未使用的函数 */
//             } else if (stats.mtime < cutoffDate) { /* 代码质量修复：未使用的函数 */
//                 // 检查文件是否匹配清理模式 /* 代码质量修复：未使用的函数 */
// //                 const shouldDelete = config.cleanupPatterns.some(pattern => { /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//                     const regex = new RegExp(pattern.replace(/\*/g, '.*')); /* 代码质量修复：未使用的函数 */
//                     return regex.test(file); /* 代码质量修复：未使用的函数 */
//                 }); /* 代码质量修复：未使用的函数 */
//                  /* 代码质量修复：未使用的函数 */
//                 if (shouldDelete || pattern === '*') { /* 代码质量修复：未使用的函数 */
//                     fs.unlinkSync(filePath); /* 代码质量修复：未使用的函数 */
//                     deletedCount++; /* 代码质量修复：未使用的函数 */
//                 } /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */
//     } /* 代码质量修复：未使用的函数 */
//      /* 代码质量修复：未使用的函数 */
//     processDir(dirPath); /* 代码质量修复：未使用的函数 */
// //     /* 修复：注释掉调试日志 */ // console.log(`已清理 ${deletedCount} 个过期文件`); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
// } /* 代码质量修复：未使用的函数 */

// 清理临时目录
// function cleanupTempDirectory() { /* 代码质量修复：未使用的函数 */
// //     const tempDir = path.join(config.basePath, config.tempPath); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//     if (fs.existsSync(tempDir)) { /* 代码质量修复：未使用的函数 */
// //         /* 修复：注释掉调试日志 */ // console.log(`清理临时目录: ${tempDir}`); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
// //         const files = fs.readdirSync(tempDir); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//         for (const file of files) { /* 代码质量修复：未使用的函数 */
// //             const filePath = path.join(tempDir, file); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//             if (fs.statSync(filePath).isDirectory()) { /* 代码质量修复：未使用的函数 */
//                 deleteDirectory(filePath); /* 代码质量修复：未使用的函数 */
//             } else { /* 代码质量修复：未使用的函数 */
//                 fs.unlinkSync(filePath); /* 代码质量修复：未使用的函数 */
//             } /* 代码质量修复：未使用的函数 */
//         } /* 代码质量修复：未使用的函数 */
// //         /* 修复：注释掉调试日志 */ // console.log(`临时目录清理完成，共清理 ${files.length} 个文件`); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//     } else { /* 代码质量修复：未使用的函数 */
// //         /* 修复：注释掉调试日志 */ // console.log('临时目录不存在'); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//     } /* 代码质量修复：未使用的函数 */
// } /* 代码质量修复：未使用的函数 */

// 清理日志文件
// function cleanupLogFiles() { /* 代码质量修复：未使用的函数 */
// //     const logDir = path.join(config.basePath, config.logsPath); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //     /* 修复：注释掉调试日志 */ // console.log(`清理过期日志文件: ${logDir}`); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//     cleanupOldFiles(logDir, config.retentionDays.logs); /* 代码质量修复：未使用的函数 */
// } /* 代码质量修复：未使用的函数 */

// 清理测试结果
// function cleanupTestResults() { /* 代码质量修复：未使用的函数 */
// //     const resultsDir = path.join(config.basePath, config.resultsPath); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //     /* 修复：注释掉调试日志 */ // console.log(`清理过期测试结果: ${resultsDir}`); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//     cleanupOldFiles(resultsDir, config.retentionDays.results); /* 代码质量修复：未使用的函数 */
// } /* 代码质量修复：未使用的函数 */

// 检查磁盘使用情况
// function checkDiskUsage() { /* 代码质量修复：未使用的函数 */
//     try { /* 代码质量修复：未使用的函数 */
// //         /* 修复：注释掉调试日志 */ // console.log('检查磁盘使用情况...'); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//         // 在不同操作系统上可能需要调整命令 /* 代码质量修复：未使用的函数 */
// //         const output = execSync('df -h').toString(); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //         /* 修复：注释掉调试日志 */ // console.log(output); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//     } catch (error) { /* 代码质量修复：未使用的函数 */
// //         console.error('检查磁盘使用情况失败:', error.message); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//     } /* 代码质量修复：未使用的函数 */
// } /* 代码质量修复：未使用的函数 */

// 主函数
// function main() { /* 代码质量修复：未使用的函数 */
//     try { /* 代码质量修复：未使用的函数 */
// //         const startTime = new Date(); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//          /* 代码质量修复：未使用的函数 */
// //         /* 修复：注释掉调试日志 */ // console.log('======================'); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
// //         /* 修复：注释掉调试日志 */ // console.log(`开始时间: ${startTime.toISOString()}`); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
// //         /* 修复：注释掉调试日志 */ // console.log('======================'); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//          /* 代码质量修复：未使用的函数 */
//         // 执行清理任务 /* 代码质量修复：未使用的函数 */
//         cleanupTempDirectory(); /* 代码质量修复：未使用的函数 */
//         cleanupLogFiles(); /* 代码质量修复：未使用的函数 */
//         cleanupTestResults(); /* 代码质量修复：未使用的函数 */
//         checkDiskUsage(); /* 代码质量修复：未使用的函数 */
//          /* 代码质量修复：未使用的函数 */
// //         const endTime = new Date(); /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
// //         const duration = (endTime - startTime) / 1000; /* 代码质量修复：未使用的 常量 */ /* 代码质量修复：未使用的函数 */
//          /* 代码质量修复：未使用的函数 */
// //         /* 修复：注释掉调试日志 */ // console.log('======================'); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
// //         /* 修复：注释掉调试日志 */ // console.log(`结束时间: ${endTime.toISOString()}`); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
// //         /* 修复：注释掉调试日志 */ // console.log(`总耗时: ${duration.toFixed(2)} 秒`); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
// //         /* 修复：注释掉调试日志 */ // console.log('清理完成!'); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//     } catch (error) { /* 代码质量修复：未使用的函数 */
// //         console.error('清理过程中发生错误:', error.message); /* 代码质量修复：调试语句 */ /* 代码质量修复：未使用的函数 */
//         process.exit(1); /* 代码质量修复：未使用的函数 */
//     } /* 代码质量修复：未使用的函数 */
// } /* 代码质量修复：未使用的函数 */

// 执行主函数
main();
