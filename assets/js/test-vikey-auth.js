// Vikey认证测试脚本
console.log('开始测试Vikey认证功能...');

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', async () => {
    // 确保所有依赖已加载
    await waitForDependencies();
    
    // 运行测试套件
    runTests();
});

/**
 * 等待所有依赖加载完成
 */
async function waitForDependencies() {
    return new Promise((resolve) => {
        const checkDependencies = () => {
            if (window.VikeyMockAPI && window.authManager) {
                console.log('所有依赖已加载完成');
                resolve();
            } else {
                console.log('等待依赖加载...');
                setTimeout(checkDependencies, 100);
            }
        };
        
        // 最多等待5秒
        const timeout = setTimeout(() => {
            console.warn('依赖加载超时，将继续测试但可能会有错误');
            resolve();
        }, 5000);
        
        checkDependencies();
    });
}

/**
 * 运行测试套件
 */
async function runTests() {
    console.log('====================================');
    console.log('运行Vikey认证测试套件');
    console.log('====================================');
    
    try {
        // 测试1: 测试VikeyMockAPI实例化
        await testVikeyMockAPIInstantiation();
        
        // 测试2: 测试Vikey设备状态检查
        await testVikeyStatusCheck();
        
        // 测试3: 测试Vikey验证功能
        await testVikeyVerification();
        
        // 测试4: 测试Vikey信息读取
        await testVikeyInfoReading();
        
        // 测试5: 测试认证管理器中的Vikey认证集成
        await testAuthManagerVikeyIntegration();
        
        // 测试6: 测试Vikey认证登录流程
        await testVikeyAuthLogin();
        
        console.log('====================================');
        console.log('✅ 所有测试完成！');
        console.log('====================================');
        
    } catch (error) {
        console.error('❌ 测试套件执行失败:', error);
    }
}

/**
 * 测试1: 测试VikeyMockAPI实例化
 */
async function testVikeyMockAPIInstantiation() {
    console.log('\n测试1: 测试VikeyMockAPI实例化');
    
    try {
        const vikeyAPI = new window.VikeyMockAPI();
        console.log('✅ VikeyMockAPI实例化成功');
        console.log('  - 实例类型:', typeof vikeyAPI);
        console.log('  - 可用方法:', Object.getOwnPropertyNames(vikeyAPI.constructor.prototype).filter(m => m !== 'constructor'));
        
        // 检查状态枚举是否可用
        console.log('  - 状态枚举:', vikeyAPI.Status);
        
        return true;
    } catch (error) {
        console.error('❌ VikeyMockAPI实例化失败:', error);
        return false;
    }
}

/**
 * 测试2: 测试Vikey设备状态检查
 */
async function testVikeyStatusCheck() {
    console.log('\n测试2: 测试Vikey设备状态检查');
    
    try {
        const vikeyAPI = new window.VikeyMockAPI();
        
        // 检查设备状态
        const status = await vikeyAPI.checkVikeyStatus();
        console.log('✅ 设备状态检查成功');
        console.log('  - 当前状态码:', status);
        console.log('  - 当前状态:', vikeyAPI.Status[status]);
        
        // 验证状态是否为READY
        if (status === vikeyAPI.Status.READY) {
            console.log('  - ✅ 设备状态为READY');
        } else {
            console.log('  - ⚠️  设备状态不是READY，而是:', vikeyAPI.Status[status]);
        }
        
        return true;
    } catch (error) {
        console.error('❌ 设备状态检查失败:', error);
        return false;
    }
}

/**
 * 测试3: 测试Vikey验证功能
 */
async function testVikeyVerification() {
    console.log('\n测试3: 测试Vikey验证功能');
    
    try {
        const vikeyAPI = new window.VikeyMockAPI();
        
        // 执行验证
        const result = await vikeyAPI.verifyVikey();
        console.log('✅ Vikey验证执行成功');
        console.log('  - 验证结果:', result.success ? '成功' : '失败');
        console.log('  - 验证消息:', result.message);
        
        // 如果有数据，显示数据
        if (result.data) {
            console.log('  - 验证数据:', result.data);
        }
        
        return result.success;
    } catch (error) {
        console.error('❌ Vikey验证失败:', error);
        return false;
    }
}

/**
 * 测试4: 测试Vikey信息读取
 */
async function testVikeyInfoReading() {
    console.log('\n测试4: 测试Vikey信息读取');
    
    try {
        const vikeyAPI = new window.VikeyMockAPI();
        
        // 读取设备信息
        const result = await vikeyAPI.readVikeyInfo();
        console.log('✅ Vikey信息读取成功');
        console.log('  - 读取结果:', result.success ? '成功' : '失败');
        
        // 显示设备信息
        if (result.data) {
            console.log('  - 设备信息:');
            console.log('    * 设备ID:', result.data.deviceId);
            console.log('    * 设备名称:', result.data.deviceName);
            console.log('    * 固件版本:', result.data.firmwareVersion);
            console.log('    * 序列号:', result.data.serialNumber);
            console.log('    * 有效期:', result.data.validityPeriod);
        } else {
            console.log('  - ⚠️  未返回设备信息');
        }
        
        return result.success;
    } catch (error) {
        console.error('❌ Vikey信息读取失败:', error);
        return false;
    }
}

/**
 * 测试5: 测试认证管理器中的Vikey认证集成
 */
async function testAuthManagerVikeyIntegration() {
    console.log('\n测试5: 测试认证管理器中的Vikey认证集成');
    
    try {
        if (!window.authManager) {
            throw new Error('authManager未加载');
        }
        
        // 检查认证管理器的Vikey功能
        console.log('✅ 检查认证管理器Vikey功能');
        console.log('  - Vikey认证是否可用:', window.authManager.config.useVikeyAuth);
        console.log('  - VikeyAPI实例是否存在:', window.authManager.vikeyAPI ? '是' : '否');
        
        // 检查Vikey可用性
        const availability = await window.authManager.checkVikeyAvailability();
        console.log('✅ 检查Vikey设备可用性');
        console.log('  - 设备是否可用:', availability.available ? '是' : '否');
        if (availability.status !== undefined) {
            console.log('  - 设备状态:', availability.statusText);
        }
        
        return true;
    } catch (error) {
        console.error('❌ 认证管理器Vikey集成测试失败:', error);
        return false;
    }
}

/**
 * 测试6: 测试Vikey认证登录流程
 */
async function testVikeyAuthLogin() {
    console.log('\n测试6: 测试Vikey认证登录流程');
    
    try {
        if (!window.authManager) {
            throw new Error('authManager未加载');
        }
        
        // 测试使用Vikey认证的登录
        console.log('✅ 测试使用Vikey认证的登录');
        const loginResult = await window.authManager.login({
            username: 'admin',
            useVikey: true // 使用Vikey认证，不需要密码
        });
        
        console.log('  - 登录结果:', loginResult.success ? '成功' : '失败');
        console.log('  - 登录消息:', loginResult.message);
        
        // 检查认证状态
        const authStatus = window.authManager.getAuthStatus();
        console.log('✅ 检查认证状态');
        console.log('  - 是否已认证:', authStatus.isAuthenticated);
        if (authStatus.currentUser) {
            console.log('  - 当前用户:', authStatus.currentUser.username);
        }
        
        return loginResult.success;
    } catch (error) {
        console.error('❌ Vikey认证登录测试失败:', error);
        return false;
    }
}

/**
 * 创建测试结果显示区域
 */
function createTestResultsUI() {
    const resultsDiv = document.createElement('div');
    resultsDiv.id = 'vikey-test-results';
    resultsDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        width: 400px;
        max-height: 600px;
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-family: monospace;
        font-size: 14px;
        overflow-y: auto;
        z-index: 9999;
    `;
    
    const title = document.createElement('h3');
    title.textContent = 'Vikey认证测试结果';
    title.style.marginTop = 0;
    resultsDiv.appendChild(title);
    
    const consoleOutput = document.createElement('pre');
    consoleOutput.id = 'vikey-test-output';
    consoleOutput.style.margin = '10px 0';
    consoleOutput.style.whiteSpace = 'pre-wrap';
    resultsDiv.appendChild(consoleOutput);
    
    // 添加到页面
    document.body.appendChild(resultsDiv);
    
    // 重定向console.log到测试结果区域
    const originalConsoleLog = console.log;
    console.log = function(...args) {
        originalConsoleLog(...args);
        const output = document.getElementById('vikey-test-output');
        if (output) {
            const message = args.map(arg => {
                if (typeof arg === 'object') {
                    return JSON.stringify(arg, null, 2);
                }
                return String(arg);
            }).join(' ');
            output.textContent += message + '\n';
            output.scrollTop = output.scrollHeight;
        }
    };
    
    // 重定向console.error
    const originalConsoleError = console.error;
    console.error = function(...args) {
        originalConsoleError(...args);
        const output = document.getElementById('vikey-test-output');
        if (output) {
            const message = args.map(arg => {
                if (typeof arg === 'object') {
                    return JSON.stringify(arg, null, 2);
                }
                return String(arg);
            }).join(' ');
            output.textContent += '❌ ERROR: ' + message + '\n';
            output.scrollTop = output.scrollHeight;
        }
    };
}

// 创建测试结果UI
createTestResultsUI();

console.log('Vikey认证测试脚本已加载，等待DOM完成...');
