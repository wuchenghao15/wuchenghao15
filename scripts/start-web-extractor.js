#!/usr/bin/env node

/**
 * 日语网络数据提取器启动脚本
 * 测试自动数据提取功能
 */

const japaneseWebExtractor = require('./src/core/database/japanese-web-extractor');

/**
 * 主函数
 */
async function main() {
    console.log('🚀 日语网络数据提取器启动');
    console.log('=========================');
    
    try {
        // 初始化提取器
        await japaneseWebExtractor.initialize();
        console.log('✅ 提取器初始化成功');
        
        // 执行一次提取任务
        console.log('\n📥 执行数据提取任务...');
        const results = await japaneseWebExtractor.startExtraction();
        
        // 显示提取结果
        console.log('\n📊 提取结果汇总:');
        let totalExtracted = 0;
        results.forEach((result, index) => {
            if (result.success) {
                console.log(`   ✅ ${result.source}: ${result.count} 个题目`);
                totalExtracted += result.count;
            } else {
                console.log(`   ❌ ${index + 1}: 失败 - ${result.error}`);
            }
        });
        console.log(`\n🎯 总计提取: ${totalExtracted} 个题目`);
        
        // 导出提取结果
        const exportPath = await japaneseWebExtractor.exportResults();
        console.log(`📁 提取结果已导出到: ${exportPath}`);
        
        // 启动定时提取
        console.log('\n⏰ 启动定时提取任务...');
        await japaneseWebExtractor.runScheduledExtraction();
        
        console.log('\n✅ 提取器启动成功！');
        console.log('📝 系统将每小时自动提取日语练习题');
        console.log('🔍 提取内容包括: 语法、单词、听力、新闻、动漫');
        
    } catch (error) {
        console.error('❌ 提取器启动失败:', error);
        process.exit(1);
    }
}

// 执行主函数
if (require.main === module) {
    main();
}

module.exports = {
    main
};