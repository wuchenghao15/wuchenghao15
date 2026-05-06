// VERSION: 20251106.66e11044dbf3f1dadb31fda4
/**
 * MTSCOS 版本更新管理脚本使用示例
 * 本示例演示如何在其他脚本中使用 version_update_manager.js 的功能
 */

const path = require('path');
const { logger, updateFileVersion, processDirectory, mountViKeyFiles } = require('./version_update_manager');

/**
 * 示例1: 更新单个文件的版本号
 */
async function exampleUpdateSingleFile() {
    console.log('\n=== 示例1: 更新单个文件 ===');
    
    const testFilePath = path.join(__dirname, 'JavaScript', 'test-manager.js');
    
    try {
        const success = await updateFileVersion(testFilePath);
        if (success) {
            console.log(`✅ 成功更新文件: ${testFilePath}`);
        } else {
            console.log(`❌ 更新文件失败: ${testFilePath}`);
        }
    } catch (error) {
        console.error(`❌ 处理单个文件时出错: ${error.message}`);
    }
}

/**
 * 示例2: 处理整个目录
 */
async function exampleProcessDirectory() {
    console.log('\n=== 示例2: 处理目录 ===');
    
    const targetDir = path.join(__dirname, 'JavaScript');
    
    try {
        const stats = await processDirectory(targetDir);
        console.log(`\n处理结果:`);
        console.log(`- 总文件数: ${stats.total}`);
        console.log(`- 成功更新: ${stats.updated}`);
        console.log(`- 更新失败: ${stats.failed}`);
    } catch (error) {
        console.error(`❌ 处理目录时出错: ${error.message}`);
    }
}

/**
 * 示例3: 挂载ViKey文件
 */
async function exampleMountViKeyFiles() {
    console.log('\n=== 示例3: 挂载ViKey文件 ===');
    
    try {
        const success = await mountViKeyFiles();
        if (success) {
            console.log('✅ ViKey文件挂载成功');
        } else {
            console.log('⚠️ ViKey文件挂载可能不完整');
        }
    } catch (error) {
        console.error(`❌ 挂载ViKey文件时出错: ${error.message}`);
    }
}

/**
 * 自定义使用示例: 只更新特定类型的文件
 */
async function exampleCustomUpdate() {
    console.log('\n=== 示例4: 自定义更新逻辑 ===');
    
    // 导入更多功能
    const { collectFiles } = require('./version_update_manager');
    
    try {
        // 收集特定类型的文件
        console.log('收集.js和.html文件...');
        const allFiles = collectFiles(__dirname);
        
        // 过滤出特定类型的文件
        const jsFiles = allFiles.filter(file => file.endsWith('.js'));
        const htmlFiles = allFiles.filter(file => file.endsWith('.html'));
        
        console.log(`找到 ${jsFiles.length} 个JS文件和 ${htmlFiles.length} 个HTML文件`);
        
        // 只更新JS文件
        console.log('\n开始更新JS文件...');
        let updatedCount = 0;
        
        for (const file of jsFiles.slice(0, 5)) { // 只更新前5个JS文件作为示例
            const success = await updateFileVersion(file);
            if (success) updatedCount++;
        }
        
        console.log(`已更新 ${updatedCount} 个JS文件`);
    } catch (error) {
        console.error(`❌ 自定义更新过程中出错: ${error.message}`);
    }
}

/**
 * 主示例函数
 */
async function runExamples() {
    console.log('====================================');
    console.log('  MTSCOS 版本更新管理脚本使用示例');
    console.log('====================================');
    
    try {
        // 运行所有示例
        await exampleUpdateSingleFile();
        await exampleProcessDirectory();
        await exampleMountViKeyFiles();
        await exampleCustomUpdate();
        
        console.log('\n====================================');
        console.log('所有示例运行完成！');
        console.log('====================================');
    } catch (error) {
        console.error('\n❌ 示例运行过程中发生错误:', error.message);
    }
}

// 运行示例
if (require.main === module) {
    runExamples();
}

module.exports = {
    runExamples,
    exampleUpdateSingleFile,
    exampleProcessDirectory,
    exampleMountViKeyFiles,
    exampleCustomUpdate
};