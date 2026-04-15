#!/usr/bin/env node

/**
 * MTSCOS AI 防火墙配置检查脚本
 * 功能: 检查防火墙配置是否正确
 */

const fs = require('fs');
const path = require('path');
const firewallConfig = require('./src/config/firewall.config');
const firewallMiddleware = require('./src/infrastructure/middlewares/firewall-middleware');

// 日志函数
function log(message, level = 'INFO') {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] [${level}] ${message}`;
    console.log(logMessage);
    return logMessage;
}

// 检查防火墙配置
function checkFirewallConfig() {
    log('🔍 检查防火墙配置...');
    
    const checks = [
        { name: '防火墙基本配置', exists: !!firewallConfig.firewall },
        { name: '端口配置', exists: !!firewallConfig.ports },
        { name: '网络访问控制', exists: !!firewallConfig.network },
        { name: '安全规则', exists: !!firewallConfig.security },
        { name: '服务访问控制', exists: !!firewallConfig.services },
        { name: '监控和日志', exists: !!firewallConfig.monitoring },
        { name: '部署配置', exists: !!firewallConfig.deployment },
        { name: '自动配置规则', exists: !!firewallConfig.autoConfig }
    ];
    
    checks.forEach(check => {
        if (check.exists) {
            log(`✅ ${check.name} 配置完整`);
        } else {
            log(`❌ ${check.name} 配置缺失`, 'ERROR');
        }
    });
}

// 检查防火墙中间件
function checkFirewallMiddleware() {
    log('🔍 检查防火墙中间件...');
    
    const checks = [
        { name: 'IP访问控制', exists: typeof firewallMiddleware.ipAccessControl === 'function' },
        { name: '输入验证', exists: typeof firewallMiddleware.inputValidation === 'function' },
        { name: '安全头部', exists: typeof firewallMiddleware.securityHeaders === 'function' },
        { name: 'API访问控制', exists: typeof firewallMiddleware.apiAccessControl === 'function' },
        { name: '管理界面访问控制', exists: typeof firewallMiddleware.adminAccessControl === 'function' },
        { name: '文件上传访问控制', exists: typeof firewallMiddleware.uploadAccessControl === 'function' },
        { name: '应用所有中间件', exists: typeof firewallMiddleware.applyAll === 'function' }
    ];
    
    checks.forEach(check => {
        if (check.exists) {
            log(`✅ ${check.name} 中间件存在`);
        } else {
            log(`❌ ${check.name} 中间件缺失`, 'ERROR');
        }
    });
}

// 检查端口配置
function checkPortConfig() {
    log('🔍 检查端口配置...');
    
    const ports = firewallConfig.ports;
    const criticalPorts = ['http', 'https', 'mtscos'];
    
    criticalPorts.forEach(portName => {
        if (ports[portName]) {
            log(`✅ ${portName} 端口配置: ${ports[portName]}`);
        } else {
            log(`❌ ${portName} 端口配置缺失`, 'ERROR');
        }
    });
}

// 检查网络配置
function checkNetworkConfig() {
    log('🔍 检查网络配置...');
    
    const network = firewallConfig.network;
    
    if (network.allowedIPs && network.allowedIPs.length > 0) {
        log(`✅ 允许的IP范围: ${network.allowedIPs.length} 个`);
    } else {
        log(`❌ 允许的IP范围配置缺失`, 'ERROR');
    }
    
    if (network.rateLimit.enabled) {
        log(`✅ 速率限制已启用`);
    } else {
        log(`⚠️  速率限制未启用`, 'WARNING');
    }
}

// 检查安全规则
function checkSecurityRules() {
    log('🔍 检查安全规则...');
    
    const security = firewallConfig.security;
    
    const securityChecks = [
        { name: '输入验证', enabled: security.inputValidation.enabled },
        { name: '输出编码', enabled: security.outputEncoding.enabled },
        { name: 'XSS保护', enabled: security.xssProtection.enabled },
        { name: 'CSRF保护', enabled: security.csrfProtection.enabled },
        { name: 'SQL注入保护', enabled: security.sqlInjectionProtection.enabled }
    ];
    
    securityChecks.forEach(check => {
        if (check.enabled) {
            log(`✅ ${check.name} 已启用`);
        } else {
            log(`⚠️  ${check.name} 未启用`, 'WARNING');
        }
    });
}

// 主函数
function main() {
    log('🚀 开始防火墙配置检查...');
    
    checkFirewallConfig();
    checkFirewallMiddleware();
    checkPortConfig();
    checkNetworkConfig();
    checkSecurityRules();
    
    log('🎉 防火墙配置检查完成！');
}

// 执行检查
if (require.main === module) {
    main();
}
