/**
 * Vikey硬件API模拟模块
 * 替代无法加载的官方Vikey.h、Vikey.lib、Vikey.cab、Vikey.dll实现
 * 提供完全兼容的接口，用于开发和测试环境
 */

class VikeyMockAPI {
    constructor() {
        this.isInitialized = false;
        this.vikeyConnected = true; // 模拟环境默认连接状态为true
        this.currentVikeyInfo = null;
        this.monitoringInterval = null;
        this.eventListeners = new Map();
        
        // 模拟的Vikey数据
        this.mockVikeyData = {
            deviceId: 'MOCK-VIKEY-DEV-001',
            vikeyId: 'MOCK-VIKEY-123456',
            vikeyName: '开发测试Vikey',
            version: '1.0.0',
            serialNumber: 'MOCK-SN-12345678',
            permissionLevel: 2, // ADMIN级别
            validFrom: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(), // 30天前
            validTo: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(), // 1年后
            state: 2, // AUTHENTICATED
            signature: 'MOCK-SIGNATURE-' + Date.now(),
            lastUsed: new Date().toISOString()
        };
        
        // Vikey状态枚举 - 与原始API保持一致
        this.VIKEY_STATES = {
            NOT_CONNECTED: 0,
            CONNECTED: 1,
            AUTHENTICATED: 2,
            ERROR: 3,
            EXPIRED: 4,
            INVALID_PERMISSION: 5
        };

        // Vikey权限级别 - 与原始API保持一致
        this.PERMISSION_LEVELS = {
            USER: 1,
            ADMIN: 2,
            SUPER_ADMIN: 3,
            VIKEY_ADMIN: 4
        };

        // Vikey错误代码 - 与原始API保持一致
        this.ERROR_CODES = {
            SUCCESS: 0,
            NOT_FOUND: -1,
            ACCESS_DENIED: -2,
            INVALID_KEY: -3,
            EXPIRED: -4,
            DEVICE_ERROR: -5,
            COMMUNICATION_ERROR: -6
        };

        // 配置参数
        this.config = {
            monitoringInterval: 1000, // 监控间隔1秒
            connectionTimeout: 5000,   // 连接超时5秒
            maxRetryAttempts: 3,       // 最大重试次数
            autoReconnect: true        // 自动重连
        };

        // 初始化模拟系统
        this.initializeVikeySystem();
    }

    /**
     * 初始化Vikey系统 - 模拟实现
     */
    async initializeVikeySystem() {
        try {
            // 模拟初始化延迟
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // 设置模拟的当前Vikey信息
            this.currentVikeyInfo = { ...this.mockVikeyData };
            
            // 开始监控Vikey状态
            this.startMonitoring();
            
            this.isInitialized = true;
            this.emitEvent('VIKEY_INITIALIZED', { success: true });
            console.log('[Vikey Mock] 模拟Vikey系统初始化成功');
            
        } catch (error) {
            console.error('[Vikey Mock] 模拟Vikey系统初始化失败:', error);
            this.emitEvent('VIKEY_INITIALIZATION_ERROR', { error: error.message });
        }
    }

    /**
     * 检查是否为IE浏览器 - 模拟实现
     */
    isIEBrowser() {
        return false; // 模拟环境始终返回非IE
    }

    /**
     * 查找Vikey设备 - 模拟实现
     */
    async findVikeyDevice() {
        try {
            // 模拟延迟
            await new Promise(resolve => setTimeout(resolve, 300));
            
            // 模拟总是能找到设备
            this.vikeyConnected = true;
            
            const deviceInfo = {
                deviceId: this.mockVikeyData.deviceId,
                version: this.mockVikeyData.version,
                serialNumber: this.mockVikeyData.serialNumber
            };
            
            this.emitEvent('VIKEY_FOUND', deviceInfo);
            console.log('[Vikey Mock] 模拟找到Vikey设备:', deviceInfo);
            
            return { success: true, data: deviceInfo };
            
        } catch (error) {
            this.emitEvent('VIKEY_FIND_ERROR', { error: error.message });
            return { success: false, error: error.message };
        }
    }

    /**
     * 验证Vikey - 模拟实现
     */
    async verifyVikey(challenge = null) {
        try {
            if (!this.vikeyConnected) {
                const findResult = await this.findVikeyDevice();
                if (!findResult.success) {
                    return { success: false, error: 'Vikey设备未连接' };
                }
            }

            // 模拟验证延迟
            await new Promise(resolve => setTimeout(resolve, 400));
            
            // 模拟验证成功
            this.currentVikeyInfo = {
                ...this.mockVikeyData,
                signature: 'MOCK-SIGNATURE-' + Date.now() + '-' + (challenge || 'NO-CHALLENGE'),
                lastUsed: new Date().toISOString()
            };
            
            this.emitEvent('VIKEY_VERIFIED', this.currentVikeyInfo);
            console.log('[Vikey Mock] 模拟Vikey验证成功:', this.currentVikeyInfo);
            
            return { success: true, data: this.currentVikeyInfo };
            
        } catch (error) {
            this.emitEvent('VIKEY_VERIFICATION_ERROR', { error: error.message });
            return { success: false, error: error.message };
        }
    }

    /**
     * 读取Vikey信息 - 模拟实现
     */
    async readVikeyInfo() {
        try {
            if (!this.vikeyConnected) {
                return { success: false, error: 'Vikey设备未连接' };
            }

            // 模拟读取延迟
            await new Promise(resolve => setTimeout(resolve, 200));
            
            return { success: true, data: { ...this.mockVikeyData } };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * 检查Vikey状态 - 模拟实现
     */
    async checkVikeyStatus() {
        try {
            // 模拟状态检查延迟
            await new Promise(resolve => setTimeout(resolve, 100));
            
            const status = {
                state: this.VIKEY_STATES.AUTHENTICATED,
                isValid: true,
                lastCheck: new Date().toISOString()
            };
            
            return { success: true, data: status };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * 开始监控Vikey状态 - 模拟实现
     */
    startMonitoring() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
        }

        this.monitoringInterval = setInterval(async () => {
            try {
                const statusResult = await this.checkVikeyStatus();
                
                if (statusResult.success) {
                    const previousState = this.currentVikeyInfo?.state;
                    const currentState = statusResult.data.state;
                    
                    // 状态变化检测
                    if (previousState !== currentState) {
                        this.emitEvent('VIKEY_STATE_CHANGED', {
                            from: previousState,
                            to: currentState,
                            data: statusResult.data
                        });
                    }
                }
                
            } catch (error) {
                console.error('[Vikey Mock] 模拟Vikey监控错误:', error);
            }
        }, this.config.monitoringInterval);
    }

    /**
     * 停止监控 - 模拟实现
     */
    stopMonitoring() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
    }

    /**
     * 添加事件监听器 - 与原始API保持一致
     */
    addEventListener(eventType, callback) {
        if (!this.eventListeners.has(eventType)) {
            this.eventListeners.set(eventType, []);
        }
        this.eventListeners.get(eventType).push(callback);
    }

    /**
     * 移除事件监听器 - 与原始API保持一致
     */
    removeEventListener(eventType, callback) {
        const listeners = this.eventListeners.get(eventType);
        if (listeners) {
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    /**
     * 触发事件 - 与原始API保持一致
     */
    emitEvent(eventType, data) {
        const listeners = this.eventListeners.get(eventType);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`[Vikey Mock] 事件监听器错误 (${eventType}):`, error);
                }
            });
        }
    }

    /**
     * 获取错误信息 - 与原始API保持一致
     */
    getErrorMessage(errorCode) {
        const errorMessages = {
            [this.ERROR_CODES.NOT_FOUND]: '未找到Vikey设备',
            [this.ERROR_CODES.ACCESS_DENIED]: '访问被拒绝',
            [this.ERROR_CODES.INVALID_KEY]: '无效的Vikey密钥',
            [this.ERROR_CODES.EXPIRED]: 'Vikey已过期',
            [this.ERROR_CODES.DEVICE_ERROR]: 'Vikey设备错误',
            [this.ERROR_CODES.COMMUNICATION_ERROR]: '通信错误'
        };

        return errorMessages[errorCode] || '未知错误';
    }

    /**
     * 检查Vikey权限 - 与原始API保持一致
     */
    hasPermission(requiredLevel) {
        if (!this.currentVikeyInfo) {
            return false;
        }

        return this.currentVikeyInfo.permissionLevel >= requiredLevel;
    }

    /**
     * 检查Vikey时效性 - 与原始API保持一致
     */
    isValid() {
        if (!this.currentVikeyInfo) {
            return false;
        }

        const now = new Date();
        const validFrom = new Date(this.currentVikeyInfo.validFrom);
        const validTo = new Date(this.currentVikeyInfo.validTo);

        return now >= validFrom && now <= validTo;
    }

    /**
     * 获取当前Vikey信息 - 与原始API保持一致
     */
    getCurrentVikeyInfo() {
        return this.currentVikeyInfo;
    }

    /**
     * 获取Vikey连接状态 - 与原始API保持一致
     */
    isConnected() {
        return this.vikeyConnected;
    }

    /**
     * 销毁Vikey API实例 - 与原始API保持一致
     */
    destroy() {
        this.stopMonitoring();
        this.eventListeners.clear();
        this.currentVikeyInfo = null;
        this.vikeyConnected = false;
        this.isInitialized = false;
    }
}

// 创建全局实例
const vikeyMockAPI = new VikeyMockAPI();

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VikeyMockAPI;
} else {
    // 优先使用模拟API，覆盖原始API
    window.VikeyAPI = VikeyMockAPI;
    window.vikeyAPI = vikeyMockAPI;
    console.log('[Vikey Mock] 模拟Vikey API已加载并替换原始API');
}
