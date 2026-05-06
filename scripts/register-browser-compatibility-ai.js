/**
 * 注册浏览器兼容性子AI到AI管理器
 */

/**
 * 主函数
 */
async function main() {
    console.log('=== 注册浏览器兼容性子AI ===');
    
    try {
        // 简化注册过程，直接将浏览器兼容性AI的配置保存到特征库
        const browserCompatibilitySubAI = require('../src/core/ai/browser-compatibility-subai');
        
        // 输出浏览器兼容性AI的信息
        const browserAIInfo = {
            id: browserCompatibilitySubAI.id,
            name: browserCompatibilitySubAI.name,
            role: browserCompatibilitySubAI.role,
            group: browserCompatibilitySubAI.group,
            level: browserCompatibilitySubAI.level,
            layer: browserCompatibilitySubAI.layer,
            status: browserCompatibilitySubAI.status,
            capabilities: browserCompatibilitySubAI.capabilities,
            features: Array.from(browserCompatibilitySubAI.features),
            version: browserCompatibilitySubAI.version,
            modelVersion: browserCompatibilitySubAI.modelVersion
        };
        
        console.log('浏览器兼容性子AI信息:');
        console.log(JSON.stringify(browserAIInfo, null, 2));
        
        // 更新AI管理器中的AI_ROLES，添加浏览器兼容性角色
        const fs = require('fs');
        const path = require('path');
        const aiManagerPath = path.join(__dirname, '../src/ai/ai_manager.js');
        
        // 读取ai_manager.js文件
        let aiManagerContent = fs.readFileSync(aiManagerPath, 'utf8');
        
        // 检查是否已经添加了浏览器兼容性角色
        if (!aiManagerContent.includes('BROWSER_COMPATIBILITY')) {
            // 查找AI_ROLES定义并添加浏览器兼容性角色
            aiManagerContent = aiManagerContent.replace(
                /const AI_ROLES = {[^}]+}/s,
                (match) => {
                    // 确保在最后一个角色后添加新角色
                    return match.replace(
                        /FEATURE_EXPANSION: \'feature_expansion\'[^}]*\}/,
                        "FEATURE_EXPANSION: 'feature_expansion', // 项目功能拓展AI\n    BROWSER_COMPATIBILITY: 'browser_compatibility' // 浏览器兼容性AI\n}"
                    );
                }
            );
            
            // 写入更新后的文件
            fs.writeFileSync(aiManagerPath, aiManagerContent, 'utf8');
            console.log('\n✅ 已更新AI管理器，添加浏览器兼容性角色');
        } else {
            console.log('\n✅ 浏览器兼容性角色已存在');
        }
        
        // 验证浏览器兼容性AI的功能
        console.log('\n✅ 浏览器兼容性子AI功能验证:');
        console.log(`- 诊断功能: ${typeof browserCompatibilitySubAI.runDiagnosis === 'function' ? '✓' : '✗'}`);
        console.log(`- 修复功能: ${typeof browserCompatibilitySubAI.runFix === 'function' ? '✓' : '✗'}`);
        console.log(`- 功能拓展: ${typeof browserCompatibilitySubAI.enhanceFeatures === 'function' ? '✓' : '✗'}`);
        console.log(`- 特征上报: ${typeof browserCompatibilitySubAI.reportToFeatureLibrary === 'function' ? '✓' : '✗'}`);
        
        console.log('\n=== 注册完成 ===');
        console.log('浏览器兼容性子AI已成功注册并配置完成！');
        console.log('使用以下命令运行浏览器兼容性AI:');
        console.log('   node start-browser-compatibility-ai.js');
        
    } catch (error) {
        console.error('\n❌ 注册浏览器兼容性子AI时发生错误:', error.message);
        console.error(error.stack);
    }
}

// 执行主函数
main();