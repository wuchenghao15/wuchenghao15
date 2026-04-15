/**
 * 启动浏览器兼容性子AI脚本
 */

const path = require('path');
const browserCompatibilitySubAI = require('../src/core/ai/browser-compatibility-subai');

/**
 * 主函数
 */
async function main() {
    console.log('=== 启动浏览器兼容性子AI ===');
    console.log('开始运行浏览器兼容性适配流程...');
    
    try {
        // 运行浏览器兼容性适配
        const result = await browserCompatibilitySubAI.runBrowserCompatibilityAdaptation();
        
        if (result.success) {
            console.log('\n✅ 浏览器兼容性适配流程完成');
            console.log('\n=== 兼容性报告摘要 ===');
            console.log(`发现问题数: ${result.report.totalIssues}`);
            console.log(`修复问题数: ${result.report.totalFixes}`);
            console.log(`功能拓展数: ${result.report.totalEnhancements}`);
            console.log(`支持的浏览器: ${result.report.browsersSupported} 种`);
            console.log('\n具体报告请查看日志文件: Logs/browser-compatibility-ai.log');
        } else {
            console.error('\n❌ 浏览器兼容性适配流程失败:', result.message);
        }
    } catch (error) {
        console.error('\n❌ 运行浏览器兼容性子AI时发生错误:', error.message);
        console.error(error.stack);
    }
}

// 执行主函数
main();