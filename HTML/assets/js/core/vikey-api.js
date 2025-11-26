/**
 * Vikey硬件API模块
 * 提供Vikey硬件密钥的完整API接口，包括读取、验证、状态监控等功能
 * 基于官方Vikey.h、Vikey.lib、Vikey.cab、Vikey.dll实现
 */

class VikeyAPI {
    constructor() {
        this.isInitialized = false;
        this.vikeyConnected = false;
        this.currentVikeyInfo = null;
        this.monitoringInterval = null;
        this.eventListeners = new Map();
        
        // Vikey状态枚举
        this.VIKEY_STATES = {
            NOT_CONNECTED: 0,
            CONNECTED: 1,
            AUTHENTICATED: 2,
            ERROR: 3,
            EXPIRED: 4,
            INVALID_PERMISSION: 5
        };

        // Vikey权限级别
        this.PERMISSION_LEVELS = {
            USER: 1,
            ADMIN: 2,
            SUPER_ADMIN: 3,
            VIKEY_ADMIN: 4
        };

        // Vikey错误代码
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

        this.initializeVikeySystem();
    }

    /**
     * 初始化Vikey系统
     */
    async initializeVikeySystem() {
        try {
            // 初始化ActiveX控件（仅在IE/Edge中）
            if (this.isIEBrowser()) {
                await this.initializeActiveXControl();
            }
            
            // 初始化Web API接口
            await this.initializeWebAPI();
            
            // 开始监控Vikey状态
            this.startMonitoring();
            
            this.isInitialized = true;
            this.emitEvent('VIKEY_INITIALIZED', { success: true });
            
        } catch (error) {
            console.error('Vikey系统初始化失败:', error);
            this.emitEvent('VIKEY_INITIALIZATION_ERROR', { error: error.message });
        }
    }

    /**
     * 检查是否为IE浏览器
     */
    isIEBrowser() {
        return /MSIE|Trident|Edge/.test(navigator.userAgent);
    }

    /**
     * 初始化ActiveX控件
     */
    async initializeActiveXControl() {
        return new Promise((resolve, reject) => {
            try {
                // 创建Vikey ActiveX控件实例
                this.vikeyControl = new ActiveXObject('Vikey.VikeyControl');
                
                // 设置控件属性
                this.vikeyControl.TimeOut = this.config.connectionTimeout;
                
                resolve();
            } catch (error) {
                reject(new Error('ActiveX控件初始化失败: ' + error.message));
            }
        });
    }

    /**
     * 初始化Web API接口
     */
    async initializeWebAPI() {
        // 这里实现Web版本的Vikey API
        // 可以通过WebSocket或其他方式与本地Vikey服务通信
        this.webAPI = {
            findDevice: this.findVikeyDeviceWeb.bind(this),
            verify: this.verifyVikeyWeb.bind(this),
            readInfo: this.readVikeyInfoWeb.bind(this),
            checkStatus: this.checkVikeyStatusWeb.bind(this)
        };
    }

    /**
     * 查找Vikey设备
     * @returns {Promise<Object>} 查找结果
     */
    async findVikeyDevice() {
        try {
            let result;
            
            if (this.isIEBrowser() && this.vikeyControl) {
                result = await this.findVikeyDeviceActiveX();
            } else {
                result = await this.findVikeyDeviceWeb();
            }

            this.vikeyConnected = result.success;
            
            if (result.success) {
                this.emitEvent('VIKEY_FOUND', result.data);
            } else {
                this.emitEvent('VIKEY_NOT_FOUND', { error: result.error });
            }

            return result;
            
        } catch (error) {
            this.emitEvent('VIKEY_FIND_ERROR', { error: error.message });
            return { success: false, error: error.message };
        }
    }

    /**
     * ActiveX方式查找Vikey设备
     */
    async findVikeyDeviceActiveX() {
        return new Promise((resolve) => {
            try {
                const result = this.vikeyControl.FindDevice();
                
                if (result === this.ERROR_CODES.SUCCESS) {
                    const deviceInfo = {
                        deviceId: this.vikeyControl.GetDeviceID(),
                        version: this.vikeyControl.GetVersion(),
                        serialNumber: this.vikeyControl.GetSerialNumber()
                    };
                    
                    resolve({ success: true, data: deviceInfo });
                } else {
                    resolve({ success: false, error: this.getErrorMessage(result) });
                }
                
            } catch (error) {
                resolve({ success: false, error: error.message });
            }
        });
    }

    /**
     * Web方式查找Vikey设备
     */
    async findVikeyDeviceWeb() {
        try {
            // 模拟Web API调用
            const response = await fetch('/api/vikey/find', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            return result;
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * 验证Vikey
     * @param {string} challenge - 挑战码
     * @returns {Promise<Object>} 验证结果
     */
    async verifyVikey(challenge = null) {
        try {
            if (!this.vikeyConnected) {
                const findResult = await this.findVikeyDevice();
                if (!findResult.success) {
                    return { success: false, error: 'Vikey设备未连接' };
                }
            }

            let result;
            
            if (this.isIEBrowser() && this.vikeyControl) {
                result = await this.verifyVikeyActiveX(challenge);
            } else {
                result = await this.verifyVikeyWeb(challenge);
            }

            if (result.success) {
                this.currentVikeyInfo = result.data;
                this.emitEvent('VIKEY_VERIFIED', result.data);
            } else {
                this.emitEvent('VIKEY_VERIFICATION_FAILED', { error: result.error });
            }

            return result;
            
        } catch (error) {
            this.emitEvent('VIKEY_VERIFICATION_ERROR', { error: error.message });
            return { success: false, error: error.message };
        }
    }

    /**
     * ActiveX方式验证Vikey
     */
    async verifyVikeyActiveX(challenge) {
        return new Promise((resolve) => {
            try {
                // 设置挑战码
                if (challenge) {
                    this.vikeyControl.SetChallenge(challenge);
                }

                // 执行验证
                const result = this.vikeyControl.Verify();
                
                if (result === this.ERROR_CODES.SUCCESS) {
                    const vikeyInfo = {
                        vikeyId: this.vikeyControl.GetVikeyID(),
                        vikeyName: this.vikeyControl.GetVikeyName(),
                        permissionLevel: this.vikeyControl.GetPermissionLevel(),
                        validFrom: this.vikeyControl.GetValidFrom(),
                        validTo: this.vikeyControl.GetValidTo(),
                        state: this.vikeyControl.GetState(),
                        signature: this.vikeyControl.GetSignature()
                    };
                    
                    resolve({ success: true, data: vikeyInfo });
                } else {
                    resolve({ success: false, error: this.getErrorMessage(result) });
                }
                
            } catch (error) {
                resolve({ success: false, error: error.message });
            }
        });
    }

    /**
     * Web方式验证Vikey
     */
    async verifyVikeyWeb(challenge) {
        try {
            const response = await fetch('/api/vikey/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ challenge })
            });

            const result = await response.json();
            return result;
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * 读取Vikey信息
     * @returns {Promise<Object>} Vikey信息
     */
    async readVikeyInfo() {
        try {
            if (!this.vikeyConnected) {
                return { success: false, error: 'Vikey设备未连接' };
            }

            let result;
            
            if (this.isIEBrowser() && this.vikeyControl) {
                result = await this.readVikeyInfoActiveX();
            } else {
                result = await this.readVikeyInfoWeb();
            }

            return result;
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * ActiveX方式读取Vikey信息
     */
    async readVikeyInfoActiveX() {
        return new Promise((resolve) => {
            try {
                const info = {
                    deviceId: this.vikeyControl.GetDeviceID(),
                    vikeyId: this.vikeyControl.GetVikeyID(),
                    vikeyName: this.vikeyControl.GetVikeyName(),
                    version: this.vikeyControl.GetVersion(),
                    serialNumber: this.vikeyControl.GetSerialNumber(),
                    permissionLevel: this.vikeyControl.GetPermissionLevel(),
                    validFrom: this.vikeyControl.GetValidFrom(),
                    validTo: this.vikeyControl.GetValidTo(),
                    state: this.vikeyControl.GetState(),
                    lastUsed: this.vikeyControl.GetLastUsed(),
                    signature: this.vikeyControl.GetSignature(),
                    customData: this.vikeyControl.GetCustomData()
                };
                
                resolve({ success: true, data: info });
                
            } catch (error) {
                resolve({ success: false, error: error.message });
            }
        });
    }

    /**
     * Web方式读取Vikey信息
     */
    async readVikeyInfoWeb() {
        try {
            const response = await fetch('/api/vikey/info', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            return result;
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * 检查Vikey状态
     * @returns {Promise<Object>} 状态信息
     */
    async checkVikeyStatus() {
        try {
            let result;
            
            if (this.isIEBrowser() && this.vikeyControl) {
                result = await this.checkVikeyStatusActiveX();
            } else {
                result = await this.checkVikeyStatusWeb();
            }

            // 更新连接状态
            this.vikeyConnected = result.success && result.data.state !== this.VIKEY_STATES.NOT_CONNECTED;
            
            // 检查时效性
            if (result.success && result.data.validTo) {
                const now = new Date();
                const validTo = new Date(result.data.validTo);
                
                if (now > validTo) {
                    result.data.state = this.VIKEY_STATES.EXPIRED;
                    this.emitEvent('VIKEY_EXPIRED', result.data);
                }
            }

            return result;
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * ActiveX方式检查Vikey状态
     */
    async checkVikeyStatusActiveX() {
        return new Promise((resolve) => {
            try {
                const state = this.vikeyControl.GetState();
                const isValid = this.vikeyControl.IsValid();
                
                const status = {
                    state: state,
                    isValid: isValid,
                    lastCheck: new Date().toISOString()
                };
                
                resolve({ success: true, data: status });
                
            } catch (error) {
                resolve({ success: false, error: error.message });
            }
        });
    }

    /**
     * Web方式检查Vikey状态
     */
    async checkVikeyStatusWeb() {
        try {
            const response = await fetch('/api/vikey/status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            return result;
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * 开始监控Vikey状态
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
                    
                    // 连接状态变化检测
                    const wasConnected = this.vikeyConnected;
                    const isConnected = currentState !== this.VIKEY_STATES.NOT_CONNECTED;
                    
                    if (wasConnected !== isConnected) {
                        if (isConnected) {
                            this.emitEvent('VIKEY_CONNECTED', statusResult.data);
                        } else {
                            this.emitEvent('VIKEY_DISCONNECTED', {});
                        }
                    }
                }
                
            } catch (error) {
                console.error('Vikey监控错误:', error);
            }
        }, this.config.monitoringInterval);
    }

    /**
     * 停止监控
     */
    stopMonitoring() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
    }

    /**
     * 添加事件监听器
     * @param {string} eventType - 事件类型
     * @param {Function} callback - 回调函数
     */
    addEventListener(eventType, callback) {
        if (!this.eventListeners.has(eventType)) {
            this.eventListeners.set(eventType, []);
        }
        this.eventListeners.get(eventType).push(callback);
    }

    /**
     * 移除事件监听器
     * @param {string} eventType - 事件类型
     * @param {Function} callback - 回调函数
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
     * 触发事件
     * @param {string} eventType - 事件类型
     * @param {Object} data - 事件数据
     */
    emitEvent(eventType, data) {
        const listeners = this.eventListeners.get(eventType);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`事件监听器错误 (${eventType}):`, error);
                }
            });
        }
    }

    /**
     * 获取错误信息
     * @param {number} errorCode - 错误代码
     * @returns {string} 错误信息
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
     * 检查Vikey权限
     * @param {number} requiredLevel - 需要的权限级别
     * @returns {boolean} 是否有权限
     */
    hasPermission(requiredLevel) {
        if (!this.currentVikeyInfo) {
            return false;
        }

        return this.currentVikeyInfo.permissionLevel >= requiredLevel;
    }

    /**
     * 检查Vikey时效性
     * @returns {boolean} 是否在有效期内
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
     * 获取当前Vikey信息
     * @returns {Object|null} Vikey信息
     */
    getCurrentVikeyInfo() {
        return this.currentVikeyInfo;
    }

    /**
     * 获取Vikey连接状态
     * @returns {boolean} 是否已连接
     */
    isConnected() {
        return this.vikeyConnected;
    }

    /**
     * 销毁Vikey API实例
     */
    destroy() {
        this.stopMonitoring();
        
        if (this.vikeyControl) {
            try {
                this.vikeyControl = null;
            } catch (error) {
                console.error('销毁Vikey控件失败:', error);
            }
        }

        this.eventListeners.clear();
        this.currentVikeyInfo = null;
        this.vikeyConnected = false;
        this.isInitialized = false;
    }
}

// 创建全局实例
const vikeyAPI = new VikeyAPI();

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VikeyAPI;
} else {
    window.VikeyAPI = VikeyAPI;
    window.vikeyAPI = vikeyAPI;
}