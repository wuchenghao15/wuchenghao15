// 简化的API客户端 - 修复版本
console.log('API客户端已加载');

// 避免重复声明
if (typeof window.apiClient === 'undefined') {
    window.apiClient = {
        // 基础配置
        config: {
            baseURL: window.location.origin,
            timeout: 10000,
            retries: 3
        },

        // 模拟API响应
        mockResponses: {
            '/api/health': {
                success: true,
                status: 'healthy',
                timestamp: new Date().toISOString()
            },
            '/api/user/profile': {
                success: true,
                user: {
                    id: 1,
                    username: 'demo_user',
                    email: 'demo@example.com'
                }
            }
        },

        // 通用请求方法
        async request(endpoint, options = {}) {
            console.log(`API请求: ${endpoint}`);
            
            // 模拟网络延迟
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // 返回模拟响应
            const mockResponse = this.mockResponses[endpoint];
            if (mockResponse) {
                return {
                    success: true,
                    data: mockResponse
                };
            }
            
            // 默认响应
            return {
                success: true,
                data: { message: '请求成功', endpoint }
            };
        },

        // 健康检查
        async healthCheck() {
            try {
                const response = await this.request('/api/health');
                console.log('健康检查成功:', response);
                return response;
            } catch (error) {
                console.error('健康检查失败:', error);
                return { success: false, error: error.message };
            }
        },

        // 获取用户信息
        async getUserProfile() {
            try {
                const response = await this.request('/api/user/profile');
                console.log('获取用户信息成功:', response);
                return response;
            } catch (error) {
                console.error('获取用户信息失败:', error);
                return { success: false, error: error.message };
            }
        },

        // 初始化
        init() {
            console.log('API客户端初始化完成');
            
            // 自动健康检查
            this.healthCheck();
            
            // 暴露到全局
            window.api = this;
        }
    };

    // 自动初始化
    window.apiClient.init();
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.apiClient;
}