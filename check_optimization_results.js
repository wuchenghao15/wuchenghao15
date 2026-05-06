/**
 * 检查优化结果脚本
 */

const { DataAPI } = require('./src/database/db');

async function checkOptimizationResults() {
    console.log('检查优化结果...');
    
    try {
        // 获取最新的几个优化举措
        const timestamp = Date.now();
        const recentOptimizations = [];
        
        // 尝试获取最近的优化举措
        for (let i = 0; i < 10; i++) {
            const key = `optimization.${timestamp - i * 1000}_${Math.floor(Math.random() * 1000)}`;
            try {
                const optimization = await DataAPI.getConfig(key);
                if (optimization) {
                    recentOptimizations.push(optimization);
                }
            } catch (error) {
                // 忽略错误，继续尝试
            }
        }
        
        console.log('\n最近的优化举措:');
        if (recentOptimizations.length > 0) {
            recentOptimizations.forEach((opt, index) => {
                console.log(`${index + 1}. ${opt.type}: ${opt.action} (${opt.timestamp})`);
            });
        } else {
            console.log('没有找到最近的优化举措');
        }
        
        // 检查错误特征
        console.log('\n检查异常特征...');
        const recentErrors = [];
        
        // 尝试获取最近的错误特征
        for (let i = 0; i < 10; i++) {
            const key = `error.feature.${timestamp - i * 1000}_${Math.floor(Math.random() * 1000)}`;
            try {
                const errorFeature = await DataAPI.getConfig(key);
                if (errorFeature) {
                    recentErrors.push(errorFeature);
                }
            } catch (error) {
                // 忽略错误，继续尝试
            }
        }
        
        console.log('\n最近的异常特征:');
        if (recentErrors.length > 0) {
            recentErrors.forEach((error, index) => {
                console.log(`${index + 1}. ${error.type}: ${error.error} (${error.timestamp})`);
            });
        } else {
            console.log('没有找到最近的异常特征');
        }
        
        // 检查AI实例数量
        const { AIManager } = require('./src/ai/ai_manager');
        console.log(`\n当前AI实例数量: ${AIManager.aiInstances.size}`);
        
        // 检查任务队列
        console.log(`当前任务队列长度: ${AIManager.taskQueue.length}`);
        
    } catch (error) {
        console.error('检查优化结果失败:', error);
    }
}

// 执行检查
checkOptimizationResults();
