#!/usr/bin/env node

/**
 * MTSCOS AI 项目FTP上传脚本
 * 功能: 使用FTP上传项目到 wuchenghao15.xicp.net
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 项目根目录
const PROJECT_ROOT = __dirname;

// FTP服务器配置
const FTP_SERVER = {
    host: 'wuchenghao15.xicp.net',
    port: 21,
    user: 'anonymous',
    password: 'user@example.com',
    remotePath: '/'
};

// 部署包目录
const DEPLOY_PACKAGE_DIR = path.join(PROJECT_ROOT, 'deploy-package');

// 日志函数
function log(message, level = 'INFO') {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] [${level}] ${message}`;
    console.log(logMessage);
    return logMessage;
}

// 错误处理函数
function handleError(error, context) {
    const errorMessage = log(`Error in ${context}: ${error.message || error}`, 'ERROR');
    return false;
}

// 执行命令
function executeCommand(command, silent = false) {
    try {
        if (!silent) {
            log(`执行命令: ${command}`);
        }
        const output = execSync(command, { encoding: 'utf8', timeout: 300000 }); // 5分钟超时
        if (!silent) {
            log(`命令执行成功`);
        }
        return output;
    } catch (error) {
        log(`命令执行失败: ${error.message}`, 'ERROR');
        return null;
    }
}

// 检查部署包是否存在
function checkDeployPackage() {
    log('🔍 检查部署包...');
    
    if (fs.existsSync(DEPLOY_PACKAGE_DIR)) {
        const files = fs.readdirSync(DEPLOY_PACKAGE_DIR);
        log(`✅ 部署包存在，包含 ${files.length} 个文件/目录`);
        return true;
    } else {
        log('❌ 部署包不存在，请先运行部署准备脚本', 'ERROR');
        return false;
    }
}

// 检查FTP服务是否可用
function checkFtpService() {
    log('🔍 检查FTP服务是否可用...');
    
    // 使用nc命令检查FTP端口
    const output = executeCommand(`nc -zv ${FTP_SERVER.host} ${FTP_SERVER.port}`, true);
    
    if (output && output.includes('succeeded')) {
        log(`✅ FTP服务可用: ${FTP_SERVER.host}:${FTP_SERVER.port}`);
        return true;
    } else {
        log(`❌ FTP服务不可用，请检查网络连接`, 'ERROR');
        return false;
    }
}

// 创建FTP上传脚本
function createFtpUploadScript() {
    log('📝 创建FTP上传脚本...');
    
    const ftpScriptContent = `
# FTP上传脚本
open ${FTP_SERVER.host} ${FTP_SERVER.port}
user ${FTP_SERVER.user} ${FTP_SERVER.password}
binary
cd ${FTP_SERVER.remotePath}
lcd ${DEPLOY_PACKAGE_DIR}
mput *
quit
`;
    
    const ftpScriptPath = path.join(PROJECT_ROOT, 'ftp-upload.txt');
    fs.writeFileSync(ftpScriptPath, ftpScriptContent);
    log(`✅ 创建FTP上传脚本: ${ftpScriptPath}`);
    return ftpScriptPath;
}

// 执行FTP上传
function executeFtpUpload(ftpScriptPath) {
    log('🌐 执行FTP上传...');
    
    try {
        // 使用ftp命令执行上传
        const command = `ftp -n -v -s:${ftpScriptPath}`;
        const output = executeCommand(command);
        
        if (output) {
            log(`✅ FTP上传完成`);
            log(`上传输出: ${output.substring(0, 500)}...`); // 只显示前500个字符
            return true;
        } else {
            log(`❌ FTP上传失败`, 'ERROR');
            return false;
        }
        
    } catch (error) {
        handleError(error, 'FTP upload');
        return false;
    }
}

// 验证上传结果
function verifyUpload() {
    log('🔍 验证上传结果...');
    
    // 检查目标服务器是否可以访问
    const output = executeCommand(`curl -s -I http://${FTP_SERVER.host}`, true);
    
    if (output) {
        log(`✅ 服务器可访问`);
        log(`HTTP响应: ${output.substring(0, 200)}...`); // 只显示前200个字符
        return true;
    } else {
        log(`⚠️  无法验证服务器状态，HTTP请求被阻止`, 'WARNING');
        return false;
    }
}

// 主函数
function main() {
    log('🚀 开始使用FTP上传项目到 wuchenghao15.xicp.net...');
    
    try {
        // 检查部署包
        if (!checkDeployPackage()) {
            return false;
        }
        
        // 检查FTP服务
        if (!checkFtpService()) {
            return false;
        }
        
        // 创建FTP上传脚本
        const ftpScriptPath = createFtpUploadScript();
        
        // 执行FTP上传
        const uploadSuccess = executeFtpUpload(ftpScriptPath);
        
        if (!uploadSuccess) {
            log('❌ FTP上传失败', 'ERROR');
            return false;
        }
        
        // 验证上传
        const verificationSuccess = verifyUpload();
        
        // 清理临时文件
        if (fs.existsSync(ftpScriptPath)) {
            fs.unlinkSync(ftpScriptPath);
            log(`✅ 清理临时文件: ${ftpScriptPath}`);
        }
        
        // 输出总结
        log('====================================');
        log('📋 FTP上传总结');
        log('====================================');
        log(`FTP服务器: ${FTP_SERVER.host}:${FTP_SERVER.port}`);
        log(`用户名: ${FTP_SERVER.user}`);
        log(`远程路径: ${FTP_SERVER.remotePath}`);
        log(`部署包: ${DEPLOY_PACKAGE_DIR}`);
        log(`上传成功: ${uploadSuccess}`);
        log(`验证成功: ${verificationSuccess}`);
        log('====================================');
        
        if (uploadSuccess) {
            log('🎉 FTP上传项目到 wuchenghao15.xicp.net 成功！', 'SUCCESS');
            log('🚀 项目已上传到: http://wuchenghao15.xicp.net');
            log('💡 请在服务器上运行: npm start 启动服务');
            return true;
        } else {
            log('❌ FTP上传项目失败', 'ERROR');
            return false;
        }
        
    } catch (error) {
        handleError(error, 'main');
        log('❌ FTP上传过程中发生错误', 'ERROR');
        return false;
    }
}

// 执行上传
if (require.main === module) {
    main();
}

module.exports = {
    main,
    checkDeployPackage,
    checkFtpService,
    createFtpUploadScript,
    executeFtpUpload,
    verifyUpload
};