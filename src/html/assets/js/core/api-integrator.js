/**
 * MTSCOS AI System - API集成师AI员工
 * 版本: 4.4.0
 * 描述: 专注于第三方API集成、接口开发、服务编排和数据交换
 */

class APIIntegrator {
    constructor() {
        this.id = 'api-integrator';
        this.name = 'API集成师';
        this.icon = 'fa-plug';
        this.color = '#6366f1';
        this.gradient = 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)';
        this.role = '接口集成专家';
        this.status = 'active';
        this.workload = 25;
        this.efficiency = 94;
        this.apis = new Map();
        this.rateLimiters = new Map();
    }

    // ==================== API注册管理 ====================

    // 注册API
    registerAPI(config) {
        const api = {
            id: config.id,
            name: config.name,
            baseURL: config.baseURL,
            endpoints: config.endpoints || [],
            headers: config.headers || {},
            auth: config.auth || null,
            rateLimit: config.rateLimit || { requests: 100, window: 60000 },
            timeout: config.timeout || 30000,
            retry: config.retry || 3,
            status: 'active',
            registeredAt: Date.now()
        };

        this.apis.set(api.id, api);
        
        // 设置限流器
        this.rateLimiters.set(api.id, {
            requests: [],
            limit: api.rateLimit.requests,
            window: api.rateLimit.window
        });

        return api;
    }

    // 注销API
    unregisterAPI(apiId) {
        this.apis.delete(apiId);
        this.rateLimiters.delete(apiId);
    }

    // 获取API配置
    getAPI(apiId) {
        return this.apis.get(apiId);
    }

    // ==================== 请求处理 ====================

    // 发起请求
    async request(apiId, endpoint, options = {}) {
        const api = this.apis.get(apiId);
        if (!api) {
            throw new Error(`API未注册: ${apiId}`);
        }

        // 检查限流
        if (!this.checkRateLimit(apiId)) {
            throw new Error('请求频率超限，请稍后重试');
        }

        const url = this.buildURL(api.baseURL, endpoint, options.params);
        const config = {
            method: options.method || 'GET',
            headers: {
                ...api.headers,
                ...options.headers
            },
            body: options.body ? JSON.stringify(options.body) : undefined
        };

        // 添加认证
        if (api.auth) {
            config.headers['Authorization'] = `Bearer ${api.auth.token}`;
        }

        // 添加重试逻辑
        let lastError;
        for (let i = 0; i < api.retry; i++) {
            try {
                const response = await this.fetchWithTimeout(url, config, api.timeout);
                this.recordRequest(apiId);
                return response;
            } catch (error) {
                lastError = error;
                if (error.status >= 400 && error.status < 500) {
                    throw error; // 客户端错误不重试
                }
                await this.delay(1000 * (i + 1)); // 指数退避
            }
        }

        throw lastError;
    }

    // 构建URL
    buildURL(baseURL, endpoint, params) {
        let url = baseURL.replace(/\/$/, '') + '/' + endpoint.replace(/^\//, '');
        
        if (params) {
            const searchParams = new URLSearchParams(params);
            url += '?' + searchParams.toString();
        }
        
        return url;
    }

    // 带超时的fetch
    async fetchWithTimeout(url, config, timeout) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const error = new Error(`HTTP ${response.status}`);
                error.status = response.status;
                error.response = response;
                throw error;
            }

            return response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                const timeoutError = new Error('请求超时');
                timeoutError.status = 408;
                throw timeoutError;
            }
            
            throw error;
        }
    }

    // ==================== 限流管理 ====================

    // 检查限流
    checkRateLimit(apiId) {
        const limiter = this.rateLimiters.get(apiId);
        if (!limiter) return true;

        const now = Date.now();
        const windowStart = now - limiter.window;
        
        // 清理过期记录
        limiter.requests = limiter.requests.filter(t => t > windowStart);
        
        return limiter.requests.length < limiter.limit;
    }

    // 记录请求
    recordRequest(apiId) {
        const limiter = this.rateLimiters.get(apiId);
        if (limiter) {
            limiter.requests.push(Date.now());
        }
    }

    // 获取剩余请求数
    getRemainingRequests(apiId) {
        const limiter = this.rateLimiters.get(apiId);
        if (!limiter) return Infinity;

        const now = Date.now();
        const windowStart = now - limiter.window;
        const validRequests = limiter.requests.filter(t => t > windowStart);
        
        return Math.max(0, limiter.limit - validRequests.length);
    }

    // ==================== 常用API模板 ====================

    // RESTful CRUD
    async create(apiId, resource, data) {
        return this.request(apiId, `/${resource}`, {
            method: 'POST',
            body: data
        });
    }

    async read(apiId, resource, id = null) {
        const endpoint = id ? `/${resource}/${id}` : `/${resource}`;
        return this.request(apiId, endpoint);
    }

    async update(apiId, resource, id, data) {
        return this.request(apiId, `/${resource}/${id}`, {
            method: 'PUT',
            body: data
        });
    }

    async delete(apiId, resource, id) {
        return this.request(apiId, `/${resource}/${id}`, {
            method: 'DELETE'
        });
    }

    async patch(apiId, resource, id, data) {
        return this.request(apiId, `/${resource}/${id}`, {
            method: 'PATCH',
            body: data
        });
    }

    // ==================== Webhook处理 ====================

    // 注册Webhook
    registerWebhook(config) {
        return {
            id: `webhook_${Date.now()}`,
            url: config.url,
            events: config.events || ['*'],
            secret: config.secret,
            active: true,
            createdAt: Date.now()
        };
    }

    // 验证Webhook签名
    verifyWebhook(payload, signature, secret) {
        // 实现签名验证逻辑
        const crypto = window.crypto || window.msCrypto;
        if (!crypto) return true; // 降级处理
        
        // HMAC-SHA256验证
        const encoder = new TextEncoder();
        const key = encoder.encode(secret);
        const data = encoder.encode(JSON.stringify(payload));
        
        return crypto.subtle.verifyHMAC('SHA-256', key, signature, data);
    }

    // ==================== 服务编排 ====================

    // 编排多个API调用
    async orchestrate(workflow) {
        const results = [];
        
        for (const step of workflow.steps) {
            try {
                const result = await this.request(
                    step.api,
                    step.endpoint,
                    {
                        method: step.method || 'GET',
                        params: step.params,
                        body: step.body
                    }
                );
                
                results.push({
                    step: step.name,
                    success: true,
                    data: result
                });

                // 如果步骤失败且要求停止
                if (step.stopOnError && !result.success) {
                    break;
                }
            } catch (error) {
                results.push({
                    step: step.name,
                    success: false,
                    error: error.message
                });

                if (workflow.stopOnError) {
                    break;
                }
            }
        }

        return {
            workflow: workflow.name,
            completed: results.length,
            total: workflow.steps.length,
            results
        };
    }

    // ==================== 辅助方法 ====================

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // 获取状态
    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            registeredAPIs: this.apis.size,
            workload: this.workload,
            efficiency: this.efficiency
        };
    }

    // 列出所有API
    listAPIs() {
        return Array.from(this.apis.values()).map(api => ({
            id: api.id,
            name: api.name,
            status: api.status,
            endpoints: api.endpoints.length,
            rateLimit: api.rateLimit
        }));
    }
}

// 创建全局实例
window.apiIntegrator = new APIIntegrator();

// 导出
window.MTSCOS_APIIntegrator = APIIntegrator;
