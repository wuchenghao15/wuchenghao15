#!/usr/bin/env node

/**
 * MTSCOS AI 项目FTP上传脚本
 * 功能: 使用提供的FTP凭据上传项目到 wuchenghao15.xicp.net
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
    user: 'wuchenghao15',
    password: 'LoginMe.1988',
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
        log(`⚠️ FTP服务检查超时，尝试直接上传`, 'WARNING');
        return true; // 即使检查失败也尝试上传
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

// 尝试使用curl上传
function tryCurlUpload() {
    log('尝试使用curl上传...');
    
    try {
        const curlCommand = `curl -v -T ${DEPLOY_PACKAGE_DIR} ftp://${FTP_SERVER.user}:${FTP_SERVER.password}@${FTP_SERVER.host}:${FTP_SERVER.port}${FTP_SERVER.remotePath} -m 300`;
        const output = executeCommand(curlCommand);
        
        if (output) {
            log(`✅ curl上传尝试完成`);
            return true;
        } else {
            log(`❌ curl上传失败`, 'ERROR');
            return false;
        }
        
    } catch (error) {
        handleError(error, 'curl upload');
        return false;
    }
}

// 创建上传指南
function createUploadGuide() {
    log('📄 创建上传指南...');
    
    const guideContent = `
# MTSCOS AI 项目FTP上传指南

## FTP服务器配置
- **主机**: ${FTP_SERVER.host}
- **端口**: ${FTP_SERVER.port}
- **用户名**: ${FTP_SERVER.user}
- **密码**: ${FTP_SERVER.password}
- **远程路径**: ${FTP_SERVER.remotePath}

## 上传方法

### 方法1: 使用FileZilla
1. **下载FileZilla**: https://filezilla-project.org/
2. **打开FileZilla**
3. **输入连接信息**:
   - 主机: ${FTP_SERVER.host}
   - 端口: ${FTP_SERVER.port}
   - 用户名: ${FTP_SERVER.user}
   - 密码: ${FTP_SERVER.password}
4. **点击连接**
5. **上传文件**:
   - 左侧: 找到 ${DEPLOY_PACKAGE_DIR}
   - 右侧: 导航到 ${FTP_SERVER.remotePath}
   - 选择所有文件，拖拽到右侧

### 方法2: 使用命令行
\`\`\`bash
# 使用ftp命令
ftp -n -v -s:ftp-upload.txt

# 或使用curl
curl -T ${DEPLOY_PACKAGE_DIR} ftp://${FTP_SERVER.user}:${FTP_SERVER.password}@${FTP_SERVER.host}:${FTP_SERVER.port}${FTP_SERVER.remotePath}
\`\`\`

### 方法3: 使用其他FTP客户端
1. **打开FTP客户端**
2. **输入连接信息**
3. **连接服务器**
4. **上传 ${DEPLOY_PACKAGE_DIR} 中的所有文件**

## 部署后操作
1. **连接服务器**: 使用SSH或远程桌面
2. **导航到项目目录**: cd ${FTP_SERVER.remotePath}
3. **安装依赖**: npm install
4. **启动服务**: npm start
5. **验证服务**: http://${FTP_SERVER.host}/api/health

## 故障排除
- **连接失败**: 检查网络连接和FTP凭据
- **上传失败**: 检查文件权限和磁盘空间
- **启动失败**: 检查端口占用和依赖安装
- **访问失败**: 检查防火墙设置
`;
    
    const guidePath = path.join(PROJECT_ROOT, 'FTP_UPLOAD_GUIDE.md');
    fs.writeFileSync(guidePath, guideContent);
    log(`✅ 创建上传指南: ${guidePath}`);
    return guidePath;
}

// 主函数
function main() {
    log('🚀 开始使用FTP上传项目到 wuchenghao15.xicp.net...');
    log(`📋 FTP凭据: ${FTP_SERVER.user}/${'*'.repeat(FTP_SERVER.password.length)}`);
    
    try {
        // 检查部署包
        if (!checkDeployPackage()) {
            return false;
        }
        
        // 检查FTP服务
        checkFtpService();
        
        // 创建FTP上传脚本
        const ftpScriptPath = createFtpUploadScript();
        
        // 执行FTP上传
        const ftpSuccess = executeFtpUpload(ftpScriptPath);
        
        // 如果FTP上传失败，尝试curl上传
        let uploadSuccess = ftpSuccess;
        if (!ftpSuccess) {
            log('尝试使用curl上传...');
            uploadSuccess = tryCurlUpload();
        }
        
        // 创建上传指南
        createUploadGuide();
        
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
        log(`部署包: ${DEPLOY_PACKAGE_DIR}`);
        log(`FTP上传: ${ftpSuccess}`);
        log(`Curl上传: ${!ftpSuccess && uploadSuccess}`);
        log(`上传指南: FTP_UPLOAD_GUIDE.md`);
        log('====================================');
        
        if (uploadSuccess) {
            log('🎉 FTP上传项目成功！', 'SUCCESS');
            log('🚀 项目已上传到: http://wuchenghao15.xicp.net');
            log('💡 请在服务器上运行: npm start 启动服务');
        } else {
            log('⚠️  自动上传失败，请按照上传指南手动上传', 'WARNING');
            log('📄 详细指南: FTP_UPLOAD_GUIDE.md');
        }
        
        return uploadSuccess;
        
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
    tryCurlUpload,
    createUploadGuide
};