// 客户端JavaScript - 集成API客户端
// 作者: Chenghao Wu
// 版本: 2.0.0

// 等待API客户端加载
function initializeClient() {
    if (window.mtscosApi) {
        // 设置API客户端事件监听器
        window.mtscosApi.on('connected', (data) => {
            console.log('[客户端] 已连接到服务器:', data);
            updateConnectionStatus('已连接', 'success');
        });

        window.mtscosApi.on('disconnected', () => {
            console.log('[客户端] 与服务器断开连接');
            updateConnectionStatus('已断开', 'error');
        });

        window.mtscosApi.on('error', (error) => {
            console.error('[客户端] 连接错误:', error);
            updateConnectionStatus('连接错误', 'error');
        });

        window.mtscosApi.on('heartbeat', () => {
            console.log('[客户端] 心跳正常');
        });

        // 初始化测试按钮
        initializeTestButton();
        
        console.log('[客户端] API客户端集成完成');
    } else {
        console.error('[客户端] API客户端未找到');
    }
}

// 更新连接状态显示
function updateConnectionStatus(status, className) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
        statusElement.textContent = status;
        statusElement.className = className;
    }
}

// 初始化测试按钮
function initializeTestButton() {
    const testButton = document.getElementById('testButton');
    const resultDiv = document.getElementById('result');

    if (testButton && resultDiv) {
        testButton.addEventListener('click', async () => {
            try {
                resultDiv.textContent = '正在测试连接...';
                resultDiv.className = '';

                // 使用API客户端获取状态
                const response = await window.mtscosApi.getStatus();
                
                if (response.success) {
                    const data = response.data;
                    resultDiv.textContent = `服务器状态: ${data.status} - 版本: ${data.version} - 运行时间: ${Math.floor(data.uptime / 1000)}秒`;
                    resultDiv.className = 'success';
                } else {
                    throw new Error(response.error || '获取状态失败');
                }
            } catch (error) {
                resultDiv.textContent = `连接错误: ${error.message}`;
                resultDiv.className = 'error';
                console.error('[客户端] 测试连接失败:', error);
            }
        });
    }
}

// 覆盖原生fetch以添加错误处理和API集成
const originalFetch = window.fetch;
window.fetch = function() {
    return originalFetch.apply(this, arguments)
        .then(response => {
            // 检查响应状态
            if (!response.ok) {
                if (response.status === 404) {
                    console.error(`[client.js] 资源未找到 (404`)');
                    // 可以在这里添加重定向到404页面的逻辑
                    // window.location.href = '/HTML/404.html';
                } else if (response.status === 403) {
                    console.error(`[client.js] 访问被拒绝 (403`)');
                    // 可以在这里添加重定向到403页面的逻辑
                    // window.location.href = '/HTML/403.html';
                } else {
                    console.error(`[client.js] HTTP错误:  + response.status`);
                }
                
                // 使用统一错误处理器而不是直接抛出错误
                if (window.unifiedErrorHandler) {
                    return window.unifiedErrorHandler.safeThrow(
                        new Error('HTTP错误: ' + response.status),
                        window.unifiedErrorHandler.errorTypes.HTTP_ERROR
                    );
                } else {
                    throw new Error('HTTP错误: ' + response.status);
                }
            }
            return response;
        })
        .catch(error => {
            // 确保网络错误也被正确处理
            console.error(`[client.js] Fetch请求失败:, error.message`);
            
            // 如果是网络错误，尝试通过API客户端重试
            if (error.message.includes('Failed to fetch') && window.mtscosApi) {
                console.log('[客户端] 尝试通过API客户端重试请求');
                // 这里可以添加重试逻辑
            }
            
            throw error;
        });
};

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeClient);
} else {
    initializeClient();
}

console.log('[客户端] 客户端脚本已加载');
