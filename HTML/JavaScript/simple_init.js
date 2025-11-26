#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('开始MTSCOS系统初始化...');

// 检查并创建关键目录
const dirs = ['Logs', 'Backups', 'Temp'];
dirs.forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        console.log('✓ 创建目录:', dir);
    } else {
        console.log('✓ 目录已存在:', dir);
    }
});

// 检查版本文件
const versionFile = 'VERSION';
if (!fs.existsSync(versionFile)) {
    fs.writeFileSync(versionFile, '1.0.0');
    console.log('✓ 创建版本文件');
} else {
    const version = fs.readFileSync(versionFile, 'utf8').trim();
    console.log('✓ 当前版本:', version);
}

// 检查package.json
if (!fs.existsSync('package.json')) {
    const packageJson = {
        name: 'mtscos-ai-project',
        version: '1.0.0',
        description: 'MTSCOS AI Project',
        main: 'server.js',
        scripts: {
            start: 'node server.js',
            dev: 'nodemon server.js'
        },
        dependencies: {
            express: '^4.18.2',
            'body-parser': '^1.20.2',
            cors: '^2.8.5'
        }
    };
    fs.writeFileSync('package.json', JSON.stringify(packageJson, null, 2));
    console.log('✓ 创建package.json');
} else {
    console.log('✓ package.json已存在');
}

console.log('\n🎉 系统初始化完成!');
console.log('可以运行以下命令启动项目:');
console.log('  npm install  # 安装依赖');
console.log('  npm start     # 启动服务器');