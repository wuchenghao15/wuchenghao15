/**
 * MTSCOS AI System - 系统功能整合调度器
 * 版本: 4.3.0
 * 描述: 统一整合所有系统功能及子服务器，由AI调度员智能调度
 */

class SystemOrchestrator {
    constructor(database, dispatcher) {
        this.database = database;
        this.dispatcher = dispatcher;
        this.services = new Map();
        this.serviceInstances = new Map();
        this.isOrchestrating = false;
        this.healthCheckInterval = 30000;
        this.isReady = false;
        this.initPromise = this.init();
    }
    
    async init() {
        // 等待数据库就绪
        await this.database.waitForReady();
        
        // 注册所有系统服务
        this.registerServices();
        
        // 启动服务编排
        this.startOrchestration();
        
        // 启动健康检查
        this.startHealthMonitoring();
        
        this.isReady = true;
        console.log('✅ 系统功能整合调度器初始化成功');
    }
    
    registerServices() {
        // 核心服务
        this.registerService('database', {
            name: '数据库服务',
            type: 'core',
            priority: 0,
            required: true,
            healthCheck: () => this.database.healthCheck()
        });
        
        // 安全服务
        this.registerService('security', {
            name: '安全服务',
            type: 'security',
            priority: 1,
            required: true,
            healthCheck: () => ({ status: 'ok' })
        });
        
        // 中间件服务
        this.registerService('middleware', {
            name: '中间件服务',
            type: 'core',
            priority: 2,
            required: true,
            healthCheck: () => ({ status: 'ok' })
        });
        
        // AI服务
        this.registerService('ai', {
            name: 'AI服务',
            type: 'ai',
            priority: 3,
            required: false,
            healthCheck: () => ({ status: 'ok' })
        });
        
        // 数据同步服务
        this.registerService('sync', {
            name: '数据同步服务',
            type: 'data',
            priority: 4,
            required: false,
            healthCheck: () => ({ status: 'ok' })
        });
        
        // 性能监控服务
        this.registerService('performance', {
            name: '性能监控服务',
            type: 'monitoring',
            priority: 5,
            required: false,
            healthCheck: () => ({ status: 'ok' })
        });
        
        // 日志服务
        this.registerService('logging', {
            name: '日志服务',
            type: 'core',
            priority: 6,
            required: true,
            healthCheck: () => ({ status: 'ok' })
        });
        
        // 配置服务
        this.registerService('config', {
            name: '配置服务',
            type: 'core',
            priority: 7,
            required: true,
            healthCheck: () => ({ status: 'ok' })
        });
        
        // 认证服务
        this.registerService('auth', {
            name: '认证服务',
            type: 'security',
            priority: 8,
            required: true,
            healthCheck: () => ({ status: 'ok' })
        });
        
        // 通知服务
        this.registerService('notification', {
            name: '通知服务',
            type: 'feature',
            priority: 9,
            required: false,
            healthCheck: () => ({ status: 'ok' })
        });
        
        // 缓存服务
        this.registerService('cache', {
            name: '缓存服务',
            type: 'performance',
            priority: 10,
            required: false,
            healthCheck: () => ({ status: 'ok' })
        });
    }
    
    registerService(id, config) {
        this.services.set(id, {
            id,
            ...config,
            status: 'stopped',
            lastHealthCheck: 0,
            error: null,
            restartCount: 0,
            maxRestarts: 5
        });
    }
    
    // ==================== 服务编排 ====================
    
    startOrchestration() {
        this.isOrchestrating = true;
        
        // 按优先级启动服务
        const orderedServices = Array.from(this.services.values())
            .sort((a, b) => a.priority - b.priority);
        
        orderedServices.forEach(service => {
            setTimeout(async () => {
                await this.startService(service.id);
            }, service.priority * 200);
        });
        
        console.log('🔄 系统服务编排已启动');
    }
    
    stopOrchestration() {
        this.isOrchestrating = false;
        
        // 停止所有服务
        this.services.forEach(async (service, id) => {
            await this.stopService(id);
        });
        
        console.log('⏹️ 系统服务编排已停止');
    }
    
    async startService(serviceId) {
        const service = this.services.get(serviceId);
        if (!service) return false;
        
        try {
            service.status = 'starting';
            
            // 检查依赖服务
            await this.checkDependencies(service);
            
            // 创建服务实例
            const instance = await this.createServiceInstance(service);
            this.serviceInstances.set(serviceId, instance);
            
            service.status = 'running';
            service.error = null;
            service.restartCount = 0;
            
            await this.database.addLog(`服务启动: ${service.name}`, 'info', 'orchestrator');
            
            // 触发服务启动事件
            document.dispatchEvent(new CustomEvent('mtscos:service:started', {
                detail: { serviceId, service }
            }));
            
            return true;
        } catch (error) {
            service.status = 'error';
            service.error = error.message;
            service.restartCount++;
            
            await this.database.addLog(`服务启动失败: ${service.name}`, 'error', 'orchestrator', {
                error: error.message,
                restartCount: service.restartCount
            });
            
            // 自动重启
            if (service.restartCount < service.maxRestarts) {
                setTimeout(() => this.startService(serviceId), 5000);
            }
            
            return false;
        }
    }
    
    async stopService(serviceId) {
        const service = this.services.get(serviceId);
        if (!service) return false;
        
        try {
            service.status = 'stopping';
            
            // 销毁服务实例
            const instance = this.serviceInstances.get(serviceId);
            if (instance && typeof instance.destroy === 'function') {
                await instance.destroy();
            }
            
            this.serviceInstances.delete(serviceId);
            
            service.status = 'stopped';
            
            await this.database.addLog(`服务停止: ${service.name}`, 'info', 'orchestrator');
            
            return true;
        } catch (error) {
            await this.database.addLog(`服务停止失败: ${service.name}`, 'error', 'orchestrator', {
                error: error.message
            });
            return false;
        }
    }
    
    async restartService(serviceId) {
        await this.stopService(serviceId);
        await this.startService(serviceId);
    }
    
    async createServiceInstance(service) {
        // 根据服务类型创建实例
        switch (service.id) {
            case 'database':
                return this.database;
            case 'security':
                return { destroy: () => {} };
            case 'middleware':
                return { destroy: () => {} };
            case 'ai':
                return { destroy: () => {} };
            case 'sync':
                return { destroy: () => {} };
            case 'performance':
                return { destroy: () => {} };
            case 'logging':
                return { destroy: () => {} };
            case 'config':
                return { destroy: () => {} };
            case 'auth':
                return { destroy: () => {} };
            case 'notification':
                return { destroy: () => {} };
            case 'cache':
                return { destroy: () => {} };
            default:
                return { destroy: () => {} };
        }
    }
    
    async checkDependencies(service) {
        // 检查前置依赖
        const requiredServices = this.services.values().filter(s => 
            s.required && s.priority < service.priority
        );
        
        for (const dep of requiredServices) {
            if (dep.status !== 'running') {
                throw new Error(`依赖服务 ${dep.name} 未启动`);
            }
        }
        
        return true;
    }
    
    // ==================== 健康监控 ====================
    
    startHealthMonitoring() {
        this.healthInterval = setInterval(async () => {
            await this.performHealthCheck();
        }, this.healthCheckInterval);
    }
    
    stopHealthMonitoring() {
        if (this.healthInterval) {
            clearInterval(this.healthInterval);
        }
    }
    
    async performHealthCheck() {
        const results = {};
        let allHealthy = true;
        
        for (const [serviceId, service] of this.services) {
            try {
                const health = await service.healthCheck();
                
                results[serviceId] = {
                    name: service.name,
                    status: health.status,
                    ...health
                };
                
                if (health.status !== 'ok') {
                    allHealthy = false;
                    
                    await this.database.addLog(`服务异常: ${service.name}`, 'warning', 'orchestrator', health);
                    
                    // 自动重启异常服务
                    if (service.status === 'running') {
                        await this.restartService(serviceId);
                    }
                }
                
                service.lastHealthCheck = Date.now();
            } catch (error) {
                results[serviceId] = {
                    name: service.name,
                    status: 'error',
                    error: error.message
                };
                
                allHealthy = false;
                
                await this.database.addLog(`服务健康检查失败: ${service.name}`, 'error', 'orchestrator', {
                    error: error.message
                });
            }
        }
        
        // 记录整体健康状态
        await this.database.addLog(`系统健康检查: ${allHealthy ? '全部正常' : '存在异常'}`, 'info', 'orchestrator', results);
        
        return {
            status: allHealthy ? 'healthy' : 'degraded',
            services: results,
            timestamp: Date.now()
        };
    }
    
    // ==================== 服务状态管理 ====================
    
    getServiceStatus(serviceId) {
        return this.services.get(serviceId) || null;
    }
    
    getAllServiceStatus() {
        const status = {};
        
        for (const [serviceId, service] of this.services) {
            status[serviceId] = {
                name: service.name,
                type: service.type,
                status: service.status,
                priority: service.priority,
                required: service.required,
                restartCount: service.restartCount,
                lastHealthCheck: service.lastHealthCheck
            };
        }
        
        return status;
    }
    
    getServiceInstance(serviceId) {
        return this.serviceInstances.get(serviceId) || null;
    }
    
    // ==================== 功能调度 ====================
    
    async executeFunction(functionId, params = {}) {
        // 根据功能ID路由到相应的服务
        const routing = {
            'system:health': async () => await this.performHealthCheck(),
            'system:backup': async () => await this.dispatcher.addTask({
                id: 'manual-backup',
                name: '手动数据备份',
                type: 'data',
                priority: 'high'
            }),
            'system:cleanup': async () => await this.dispatcher.addTask({
                id: 'manual-cleanup',
                name: '手动系统清理',
                type: 'system',
                priority: 'normal'
            }),
            'system:sync': async () => await this.dispatcher.addTask({
                id: 'manual-sync',
                name: '手动数据同步',
                type: 'data',
                priority: 'high'
            }),
            'security:audit': async () => await this.dispatcher.addTask({
                id: 'security-audit',
                name: '安全审计',
                type: 'security',
                priority: 'high',
                ability: 'audit'
            }),
            'performance:report': async () => {
                const metrics = await this.database.getPerformanceMetrics();
                return metrics;
            },
            'config:get': async (key) => {
                const value = await this.database.getSystemSetting(key);
                return { key, value };
            },
            'config:set': async ({ key, value }) => {
                await this.database.setSystemSetting(key, value);
                return { success: true, key, value };
            },
            'user:profile:get': async (userId) => {
                const profile = await this.database.getUserProfile(userId);
                return profile;
            },
            'user:profile:save': async ({ userId, profile }) => {
                await this.database.saveUserProfile(userId, profile);
                return { success: true };
            },
            'user:prefs:get': async (userId) => {
                const prefs = await this.database.getUserPreferences(userId);
                return prefs;
            },
            'user:prefs:save': async ({ userId, preferences }) => {
                await this.database.saveUserPreferences(userId, preferences);
                return { success: true };
            },
            'ai:employee:get': async (employeeId) => {
                const employee = await this.database.getAIEmployee(employeeId);
                return employee;
            },
            'ai:employee:list': async () => {
                const employees = await this.database.getAllAIEmployees();
                return employees;
            },
            'ai:task:add': async (task) => {
                const result = await this.dispatcher.addTask(task);
                return result;
            },
            'ai:status': async () => {
                const status = await this.dispatcher.getStatus();
                return status;
            }
        };
        
        const handler = routing[functionId];
        
        if (!handler) {
            return { success: false, error: `功能 ${functionId} 未找到` };
        }
        
        try {
            const result = await handler(params);
            
            await this.database.addLog(`功能执行: ${functionId}`, 'info', 'orchestrator', {
                params,
                result: result ? 'success' : 'failed'
            });
            
            return { success: true, result };
        } catch (error) {
            await this.database.addLog(`功能执行失败: ${functionId}`, 'error', 'orchestrator', {
                params,
                error: error.message
            });
            
            return { success: false, error: error.message };
        }
    }
    
    // ==================== 动态服务注册 ====================
    
    async registerDynamicService(serviceConfig) {
        if (this.services.has(serviceConfig.id)) {
            return { success: false, error: '服务已存在' };
        }
        
        this.registerService(serviceConfig.id, serviceConfig);
        await this.startService(serviceConfig.id);
        
        return { success: true, service: serviceConfig };
    }
    
    async unregisterDynamicService(serviceId) {
        if (!this.services.has(serviceId)) {
            return { success: false, error: '服务不存在' };
        }
        
        await this.stopService(serviceId);
        this.services.delete(serviceId);
        this.serviceInstances.delete(serviceId);
        
        return { success: true };
    }
    
    // ==================== 子服务器管理 ====================
    
    async registerSubServer(serverConfig) {
        // 注册子服务器
        const serviceId = `subserver:${serverConfig.id}`;
        
        return await this.registerDynamicService({
            id: serviceId,
            name: serverConfig.name,
            type: 'subserver',
            priority: 100,
            required: false,
            healthCheck: async () => {
                // 检查子服务器状态
                try {
                    const response = await fetch(`${serverConfig.url}/health`);
                    const data = await response.json();
                    return { status: response.ok ? 'ok' : 'error', ...data };
                } catch {
                    return { status: 'error', error: '无法连接' };
                }
            }
        });
    }
    
    async getSubServerStatus(serverId) {
        const serviceId = `subserver:${serverId}`;
        return this.getServiceStatus(serviceId);
    }
    
    // ==================== 健康检查 ====================
    
    async healthCheck() {
        return {
            status: this.isOrchestrating ? 'ok' : 'stopped',
            services: this.services.size,
            runningServices: Array.from(this.services.values()).filter(s => s.status === 'running').length,
            orchestrating: this.isOrchestrating
        };
    }
    
    // ==================== 销毁 ====================
    
    destroy() {
        this.stopOrchestration();
        this.stopHealthMonitoring();
        this.services.clear();
        this.serviceInstances.clear();
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SystemOrchestrator;
}
