/**
 * 诊断脚本 - 测试各个组件的启动状态
 */

const fs = require('fs');
const path = require('path');

// 测试配置加载
function testConfig() {
    console.log('🔧 测试配置加载...');
    try {
        const config = require('./src/config/app.config');
        console.log('✅ 配置加载成功:', config.app.version);
        return true;
    } catch (error) {
        console.error('❌ 配置加载失败:', error.message);
        return false;
    }
}

// 测试中间件
function testMiddlewares() {
    console.log('🔧 测试中间件加载...');
    try {
        const errorHandler = require('./src/infrastructure/middlewares/error-handler');
        const requestLogger = require('./src/infrastructure/middlewares/request-logger');
        const securityHeaders = require('./src/infrastructure/middlewares/security-headers');
        console.log('✅ 中间件加载成功');
        return true;
    } catch (error) {
        console.error('❌ 中间件加载失败:', error.message);
        return false;
    }
}

// 测试路由
function testRoutes() {
    console.log('🔧 测试路由加载...');
    try {
        const authRoutes = require('./src/api/routes/auth');
        const jptestRoutes = require('./src/api/routes/jptest');
        const monitorRoutes = require('./src/api/routes/monitor');
        const storageRoutes = require('./src/api/routes/storage');
        console.log('✅ 路由加载成功');
        return true;
    } catch (error) {
        console.error('❌ 路由加载失败:', error.message);
        return false;
    }
}

// 测试监控服务
function testMonitor() {
    console.log('🔧 测试监控服务...');
    try {
        const { getServerMonitor } = require('./src/core/monitor/server-monitor');
        const monitor = getServerMonitor();
        monitor.start();
        console.log('✅ 监控服务加载成功');
        return true;
    } catch (error) {
        console.error('❌ 监控服务加载失败:', error.message);
        return false;
    }
}

// 测试清理服务
function testCleanup() {
    console.log('🔧 测试清理服务...');
    try {
        const CleanupService = require('./src/core/cleanup/cleanup-service');
        const cleanup = new CleanupService();
        cleanup.start();
        console.log('✅ 清理服务加载成功');
        return true;
    } catch (error) {
        console.error('❌ 清理服务加载失败:', error.message);
        return false;
    }
}

// 主诊断函数
function runDiagnostics() {
    console.log('🚀 开始系统诊断...\n');
    
    const results = {
        config: testConfig(),
        middlewares: testMiddlewares(),
        routes: testRoutes(),
        monitor: testMonitor(),
        cleanup: testCleanup()
    };
    
    console.log('\n📋 诊断结果:');
    Object.entries(results).forEach(([component, status]) => {
        console.log(`${status ? '✅' : '❌'} ${component}: ${status ? '正常' : '异常'}`);
    });
    
    const allGood = Object.values(results).every(status => status);
    console.log(`\n� 整体状态: ${allGood ? '✅ 所有组件正常' : '❌ 存在异常组件'}`);
    
    if (!allGood) {
        console.log('🔍 建议: 检查上面标记为异常的组件');
    } else {
        console.log('🚀 系统准备就绪，可以启动主服务器');
    }
}

// 运行诊断
runDiagnostics();