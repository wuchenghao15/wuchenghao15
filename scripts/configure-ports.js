#!/usr/bin/env node

/**
 * MTSCOS AI 服务器端口配置脚本
 * 功能: 检查和配置上传项目到172.16.0.196所需要的所有端口
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 目标服务器配置
const REMOTE_SERVER = {
    host: '172.16.0.196',
    ports: {
        http: 80,           // HTTP服务端口
        https: 443,         // HTTPS服务端口
        ssh: 22,            // SSH远程管理端口
        mtscos: 8081,       // MTSCOS AI服务端口
        ftp: 21,            // FTP文件传输端口
        ftpPassive: [20, 1024, 65535], // FTP被动模式端口范围
        smb: 445,           // SMB文件共享端口
        rdp: 3389           // 远程桌面端口
    }
};

// 日志目录
const LOG_DIR = path.join(__dirname, 'Logs');
if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
}

// 日志文件
const LOG_FILE = path.join(LOG_DIR, `port-configuration-${Date.now()}.log`);

// 日志函数
function log(message, level = 'INFO') {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] [${level}] ${message}`;
    console.log(logMessage);
    fs.appendFileSync(LOG_FILE, logMessage + '\n');
}

// 错误处理函数
function handleError(error, context) {
    const errorMessage = `Error in ${context}: ${error.message || error}`;
    log(errorMessage, 'ERROR');
    return false;
}

// 检测端口状态
function checkPortStatus(host, port) {
    try {
        log(`🔍 检测端口 ${port} 状态...`);
        const result = execSync(`nc -zv ${host} ${port} 2>&1`, { encoding: 'utf8', timeout: 10000 });
        const isOpen = result.includes('succeeded');
        log(`   ${port}: ${isOpen ? '✅ 开放' : '❌ 关闭'}`);
        return isOpen;
    } catch (error) {
        log(`   ${port}: ❌ 关闭`, 'WARNING');
        return false;
    }
}

// 批量检测端口
function checkAllPorts() {
    log('📋 开始批量检测服务器端口状态...');
    
    const portStatus = {};
    
    Object.entries(REMOTE_SERVER.ports).forEach(([name, portConfig]) => {
        if (Array.isArray(portConfig)) {
            // 端口范围
            log(`📡 检测 ${name} 端口范围: ${portConfig[0]}-${portConfig[2]}`);
            portStatus[name] = {
                type: 'range',
                ports: portConfig,
                status: '需要手动配置'
            };
        } else {
            // 单个端口
            const isOpen = checkPortStatus(REMOTE_SERVER.host, portConfig);
            portStatus[name] = {
                type: 'single',
                port: portConfig,
                isOpen
            };
        }
    });
    
    return portStatus;
}

// 生成端口配置指南
function generatePortConfigurationGuide(portStatus) {
    log('📄 生成端口配置指南...');
    
    const guideContent = `
# MTSCOS AI 服务器端口配置指南

## 目标服务器
- IP地址: ${REMOTE_SERVER.host}
- 服务器类型: Microsoft-IIS/10.0

## 当前端口状态
${Object.entries(portStatus).map(([name, status]) => {
    if (status.type === 'single') {
        return `- ${name.toUpperCase()} (${status.port}): ${status.isOpen ? '✅ 开放' : '❌ 关闭'}`;
    } else {
        return `- ${name.toUpperCase()} (${status.ports[0]}-${status.ports[2]}): ${status.status}`;
    }
}).join('\\n')}

## 需要开放的端口

### 1. 文件上传和管理端口
- **HTTP (80)**: 用于Web上传和访问
- **HTTPS (443)**: 用于安全Web访问（推荐）
- **FTP (21)**: 用于文件传输
- **SMB (445)**: 用于Windows文件共享
- **RDP (3389)**: 用于远程桌面管理
- **SSH (22)**: 用于远程命令行管理（推荐）

### 2. 应用服务端口
- **MTSCOS AI (8081)**: 用于运行MTSCOS AI项目服务
- **Node.js 调试 (9229)**: 用于开发调试（可选）

### 3. 数据库和服务端口
- **SQL Server (1433)**: 如果使用SQL Server数据库
- **MySQL (3306)**: 如果使用MySQL数据库
- **Redis (6379)**: 如果使用Redis缓存
- **MongoDB (27017)**: 如果使用MongoDB数据库

## 防火墙配置方法

### Windows 服务器防火墙配置
1. **打开防火墙高级设置**: 控制面板 → 系统和安全 → Windows Defender 防火墙 → 高级设置
2. **入站规则**: 右键点击 → 新建规则
3. **端口规则**: 选择"端口" → 下一步
4. **指定端口**: 输入需要开放的端口（如8081）
5. **允许连接**: 选择"允许连接" → 下一步
6. **应用配置文件**: 选择适用的网络类型 → 下一步
7. **命名规则**: 输入规则名称（如"MTSCOS AI Port"）→ 完成

### IIS 服务器配置
1. **打开IIS管理器**: 控制面板 → 管理工具 → Internet Information Services (IIS) 管理器
2. **添加网站**: 右键点击"网站" → 添加网站
3. **配置网站**:
   - 网站名称: MTSCOS AI Project
   - 物理路径: 指向项目目录
   - 绑定: 类型=http, IP地址=全部未分配, 端口=8081
4. **启动网站**: 右键点击新网站 → 管理网站 → 启动

### 路由器端口转发（如果服务器在局域网内）
1. **登录路由器管理界面**: 通常为 http://192.168.1.1 或 http://192.168.0.1
2. **找到端口转发设置**: 高级设置 → 端口转发
3. **添加转发规则**:
   - 服务名称: MTSCOS AI
   - 外部端口: 8081
   - 内部IP: 172.16.0.196
   - 内部端口: 8081
   - 协议: TCP
4. **保存设置**

## 端口测试方法

### 使用命令行测试
使用以下命令测试端口状态:
- 测试HTTP服务: curl -I http://${REMOTE_SERVER.host}
- 测试MTSCOS AI服务: curl -I http://${REMOTE_SERVER.host}:8081
- 测试SSH端口: nc -zv ${REMOTE_SERVER.host} 22
- 测试远程桌面端口: nc -zv ${REMOTE_SERVER.host} 3389

### 使用在线端口测试工具
1. **访问在线端口测试网站**: 如 https://www.canyouseeme.org/
2. **输入服务器IP**: ${REMOTE_SERVER.host}
3. **输入端口号**: 如8081
4. **点击测试**: 查看端口是否可访问

## 安全建议

1. **只开放必要端口**: 不要开放不需要的端口
2. **使用HTTPS**: 为生产环境配置SSL证书
3. **防火墙规则**: 限制访问IP范围，只允许信任的IP访问
4. **定期检查**: 定期检查端口状态和防火墙规则
5. **密码保护**: 为所有服务设置强密码
6. **更新系统**: 定期更新服务器操作系统和软件

## 故障排除

### 端口无法开放的常见原因
1. **防火墙阻止**: 检查Windows防火墙和第三方防火墙设置
2. **端口被占用**: 检查是否有其他服务占用了相同端口
3. **服务未启动**: 确保相关服务已启动
4. **网络配置**: 检查网络适配器设置和路由配置
5. **权限问题**: 确保有足够的权限修改防火墙设置

### 解决方案
1. **重启服务**: 重启相关服务和服务器
2. **更改端口**: 如果端口被占用，更改服务端口
3. **检查日志**: 查看Windows事件查看器和服务日志
4. **网络诊断**: 使用Windows网络诊断工具
5. **专业支持**: 如果问题复杂，联系网络管理员或IT支持

## 部署后验证

部署完成后，使用以下命令验证所有服务是否正常运行:
- 测试HTTP服务: curl -I http://${REMOTE_SERVER.host}
- 测试MTSCOS AI服务: curl -I http://${REMOTE_SERVER.host}:8081
- 测试健康检查端点: curl http://${REMOTE_SERVER.host}:8081/api/health
- 测试AI模型端点: curl http://${REMOTE_SERVER.host}:8081/api/ai/models

## 联系支持

如果遇到端口配置问题，请联系:
- MTSCOS AI 技术支持团队
- 网络管理员
- IT基础设施团队
`;
    
    const guideFile = path.join(__dirname, 'port-configuration-guide.md');
    fs.writeFileSync(guideFile, guideContent);
    
    log(`✅ 端口配置指南已生成: ${guideFile}`);
    return guideFile;
}

// 生成Windows防火墙配置脚本
function generateWindowsFirewallScript() {
    log('📄 生成Windows防火墙配置脚本...');
    
    const firewallScript = `
@echo off
rem MTSCOS AI 服务器防火墙配置脚本
rem 功能: 开放上传项目到172.16.0.196所需要的所有端口

echo 开始配置Windows防火墙...

rem 开放HTTP端口
netsh advfirewall firewall add rule name="MTSCOS HTTP" dir=in action=allow protocol=TCP localport=80
echo ✅ 开放HTTP端口(80)

rem 开放HTTPS端口
netsh advfirewall firewall add rule name="MTSCOS HTTPS" dir=in action=allow protocol=TCP localport=443
echo ✅ 开放HTTPS端口(443)

rem 开放SSH端口
netsh advfirewall firewall add rule name="MTSCOS SSH" dir=in action=allow protocol=TCP localport=22
echo ✅ 开放SSH端口(22)

rem 开放MTSCOS AI服务端口
netsh advfirewall firewall add rule name="MTSCOS AI Service" dir=in action=allow protocol=TCP localport=8081
echo ✅ 开放MTSCOS AI服务端口(8081)

rem 开放FTP端口
netsh advfirewall firewall add rule name="MTSCOS FTP" dir=in action=allow protocol=TCP localport=21
echo ✅ 开放FTP端口(21)

rem 开放SMB文件共享端口
netsh advfirewall firewall add rule name="MTSCOS SMB" dir=in action=allow protocol=TCP localport=445
echo ✅ 开放SMB端口(445)

rem 开放远程桌面端口
netsh advfirewall firewall add rule name="MTSCOS RDP" dir=in action=allow protocol=TCP localport=3389
echo ✅ 开放远程桌面端口(3389)

rem 显示当前防火墙规则
echo.
echo 当前MTSCOS相关防火墙规则:
netsh advfirewall firewall show rule name=all | findstr "MTSCOS"

echo.
echo 配置完成
echo 配置完成端口配置脚本执行完成!

echo 防火墙配置完成!
pause
`;
    
    const scriptFile = path.join(__dirname, 'configure-firewall.bat');
    fs.writeFileSync(scriptFile, firewallScript);
    
    log(`✅ Windows防火墙配置脚本已生成: ${scriptFile}`);
    return scriptFile;
}

// 主函数
function main() {
    log('🚀 开始MTSCOS AI服务器端口配置...');
    log(`🎯 目标服务器: ${REMOTE_SERVER.host}`);
    
    try {
        // 检查所有端口状态
        const portStatus = checkAllPorts();
        
        // 生成端口配置指南
        const guideFile = generatePortConfigurationGuide(portStatus);
        
        // 生成Windows防火墙配置脚本
        const firewallScript = generateWindowsFirewallScript();
        
        // 输出总结
        log('====================================');
        log('📊 端口配置总结');
        log('====================================');
        log(`🎯 目标服务器: ${REMOTE_SERVER.host}`);
        log(`📋 端口检测完成，请查看详细报告`);
        log(`📄 配置指南: ${guideFile}`);
        log(`🔧 Windows防火墙脚本: ${firewallScript}`);
        log('====================================');
        log('💡 请在目标服务器上运行防火墙配置脚本');
        log('🚀 或按照配置指南手动配置端口');
        log('====================================');
        
        log('🎉 端口配置任务完成!');
        
    } catch (error) {
        console.error('Error:', error);
        log('❌ 端口配置失败', 'ERROR');
        process.exit(1);
    }
}

// 执行主函数
if (require.main === module) {
    main();
}

module.exports = {
    main,
    checkAllPorts,
    generatePortConfigurationGuide,
    generateWindowsFirewallScript
};