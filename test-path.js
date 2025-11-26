const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.join(__dirname, '.');

// 测试路径映射
const testPaths = [
    '/Staging/assets/css/common_styles/modern-color-scheme.css',
    '/Staging/assets/css/common_styles/modern-layout.css',
    '/Staging/assets/css/common_styles/modern-forms.css'
];

async function testPathMapping() {
    console.log('测试静态文件路径映射...');
    console.log(`PROJECT_ROOT: ${PROJECT_ROOT}`);
    console.log('=' .repeat(50));
    
    for (const requestPath of testPaths) {
        console.log(`\n测试请求路径: ${requestPath}`);
        
        if (requestPath.startsWith('/Staging/assets/')) {
            let mappedPath = requestPath.replace('/Staging/assets/', '/assets/');
            console.log(`映射后的路径: ${mappedPath}`);
            
            const filePath = path.join(PROJECT_ROOT, mappedPath);
            console.log(`完整文件路径: ${filePath}`);
            
            try {
                const stats = await fs.promises.stat(filePath);
                if (stats.isFile()) {
                    console.log(`✅ 文件存在: ${filePath}`);
                    console.log(`文件大小: ${stats.size} 字节`);
                } else {
                    console.log(`❌ 不是文件: ${filePath}`);
                }
            } catch (error) {
                console.log(`❌ 文件不存在: ${filePath}`);
                console.log(`错误: ${error.message}`);
            }
        }
    }
}

testPathMapping();