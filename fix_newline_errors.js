#!/usr/bin/env node
/**
 * 修复JavaScript文件中的换行符错误
 * 将 '/n' 替换为 '\n'
 */

const fs = require('fs');
const path = require('path');

// 需要修复的文件列表
const filesToFix = [
    'JavaScript/captcha_manager.js',
    'JavaScript/cleanup_manager.js', 
    'JavaScript/startup-manager.js',
    'JavaScript/js_encrypt_monitor.js'
];

// 项目根目录
const projectRoot = __dirname;

/**
 * 修复单个文件中的换行符错误
 */
function fixFileNewlines(filePath) {
    try {
        const fullPath = path.join(projectRoot, filePath);
        
        if (!fs.existsSync(fullPath)) {
            console.log(`文件不存在: ${filePath}`);
            return false;
        }
        
        // 读取文件内容
        let content = fs.readFileSync(fullPath, 'utf8');
        
        // 统计替换次数
        const originalContent = content;
        
        // 替换所有 '/n' 为 '\n'
        content = content.replace(/'\/n'/g, "'\\n'");
        
        // 检查是否有变化
        if (content !== originalContent) {
            // 写回文件
            fs.writeFileSync(fullPath, content, 'utf8');
            console.log(`✓ 已修复文件: ${filePath}`);
            return true;
        } else {
            console.log(`- 文件无需修复: ${filePath}`);
            return false;
        }
    } catch (error) {
        console.error(`✗ 修复文件失败 ${filePath}: ${error.message}`);
        return false;
    }
}

/**
 * 主函数
 */
function main() {
    console.log('开始修复JavaScript文件中的换行符错误...\n');
    
    let fixedCount = 0;
    
    filesToFix.forEach(filePath => {
        if (fixFileNewlines(filePath)) {
            fixedCount++;
        }
    });
    
    console.log(`\n修复完成！共修复了 ${fixedCount} 个文件。`);
}

// 执行主函数
main();