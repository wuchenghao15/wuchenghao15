/**
 * Vikey ActiveX控件集成和监控模块
 * 负责Vikey ActiveX控件的加载、初始化、状态监控和插拔检测
 */

class VikeyActiveXMonitor {
    constructor() {
        this.isActiveXAvailable = false;
        this.vikeyControl = null;
        this.isMonitoring = false;
        this.monitoringInterval = null;
        this.currentVikeyState = null;
        this.eventListeners = new Map();
        
        // Vikey状态定义
        this.VIKEY_STATES = {
            REMOVED: 0,        // Vikey已拔出
            INSERTED: 1,       // Vikey已插入
            AUTHENTICATED: 2,  // Vikey已验证
            ERROR: 3,          // Vikey错误
            EXPIRED: 4         // Vikey已过期
        };

        // 监控配置
        this.config = {
            monitoringInterval: 500,      // 监控间隔500ms
            connectionTimeout: 3000,      // 连接超时3秒
            retryAttempts: 3,             // 重试次数
            autoReconnect: true,          // 自动重连
            enableEventLogging: true      // 启用事件日志
        };

        // 初始化ActiveX控件
        this.initializeActiveX();
    }

    /**
     * 初始化ActiveX控件
     */
    async initializeActiveX() {
        try {
            // 检查浏览器是否支持ActiveX
            if (!this.checkActiveXSupport()) {
                console.warn('当前浏览器不支持ActiveX控件');
                this.emitEvent('ACTIVEX_NOT_SUPPORTED', { message: '浏览器不支持ActiveX控件' });
                return false;
            }

            // 尝试创建Vikey ActiveX控件
            this.vikeyControl = await this.createVikeyControl();
            
            if (this.vikeyControl) {
                this.isActiveXAvailable = true;
                this.setupControlProperties();
                this.emitEvent('ACTIVEX_INITIALIZED', { success: true });
                return true;
            } else {
                this.emitEvent('ACTIVEX_INITIALIZATION_FAILED', { error: '无法创建Vikey控件' });
                return false;
            }

        } catch (error) {
            console.error('ActiveX初始化失败:', error);
            this.emitEvent('ACTIVEX_INITIALIZATION_ERROR', { error: error.message });
            return false;
        }
    }

    /**
     * 检查ActiveX支持
     */
    checkActiveXSupport() {
        // 检查是否为IE或支持ActiveX的浏览器
        try {
            // 检查ActiveXObject是否存在
            if (typeof ActiveXObject !== 'undefined') {
                return true;
            }

            // 检查是否为Microsoft Edge（Legacy）
            if (window.navigator && window.navigator.userAgent && 
                (window.navigator.userAgent.indexOf('MSIE') !== -1 || 
                 window.navigator.userAgent.indexOf('Trident') !== -1)) {
                return true;
            }

            // 检查是否支持document.createElement创建ActiveX对象
            if (document.createElement && 
                typeof document.createElement('object').setAttribute === 'function') {
                return true;
            }

            return false;
        } catch (error) {
            return false;
        }
    }

    /**
     * 创建Vikey ActiveX控件
     */
    async createVikeyControl() {
        return new Promise((resolve, reject) => {
            try {
                // 方法1: 使用ActiveXObject
                if (typeof ActiveXObject !== 'undefined') {
                    try {
                        const control = new ActiveXObject('Vikey.VikeyControl');
                        resolve(control);
                        return;
                    } catch (e) {
                        console.warn('使用ActiveXObject创建Vikey控件失败:', e);
                    }
                }

                // 方法2: 使用object标签创建
                const objectElement = document.createElement('object');
                objectElement.setAttribute('classid', 'CLSID:12345678-1234-1234-1234-123456789ABC'); // 替换为实际的CLSID
                objectElement.setAttribute('codebase', 'Vikey.cab#version=1,0,0,0');
                objectElement.style.display = 'none';
                objectElement.id = 'vikeyControlObject';

                document.body.appendChild(objectElement);

                // 等待控件加载
                objectElement.onreadystatechange = () => {
                    if (objectElement.readyState === 'complete') {
                        try {
                            const control = objectElement.object || objectElement;
                            resolve(control);
                        } catch (error) {
                            reject(error);
                        }
                    }
                };

                // 设置超时
                setTimeout(() => {
                    reject(new Error('Vikey ActiveX控件加载超时'));
                }, this.config.connectionTimeout);

            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * 设置控件属性
     */
    setupControlProperties() {
        if (!this.vikeyControl) return;

        try {
            // 设置基本属性
            if (typeof this.vikeyControl.TimeOut !== 'undefined') {
                this.vikeyControl.TimeOut = this.config.connectionTimeout;
            }

            if (typeof this.vikeyControl.EnableEvents !== 'undefined') {
                this.vikeyControl.EnableEvents = true;
            }

            // 绑定事件处理器
            this.bindControlEvents();

        } catch (error) {
            console.error('设置Vikey控件属性失败:', error);
        }
    }

    /**
     * 绑定控件事件
     */
    bindControlEvents() {
        if (!this.vikeyControl) return;

        try {
            // Vikey插入事件
            if (typeof this.vikeyControl.OnVikeyInserted !== 'undefined') {
                this.vikeyControl.OnVikeyInserted = (vikeyInfo) => {
                    this.handleVikeyInserted(vikeyInfo);
                };
            }

            // Vikey拔出事件
            if (typeof this.vikeyControl.OnVikeyRemoved !== 'undefined') {
                this.vikeyControl.OnVikeyRemoved = () => {
                    this.handleVikeyRemoved();
                };
            }

            // Vikey错误事件
            if (typeof this.vikeyControl.OnVikeyError !== 'undefined') {
                this.vikeyControl.OnVikeyError = (errorCode, errorMessage) => {
                    this.handleVikeyError(errorCode, errorMessage);
                };
            }

            // Vikey验证事件
            if (typeof this.vikeyControl.OnVikeyVerified !== 'undefined') {
                this.vikeyControl.OnVikeyVerified = (verificationResult) => {
                    this.handleVikeyVerified(verificationResult);
                };
            }

        } catch (error) {
            console.error('绑定Vikey控件事件失败:', error);
        }
    }

    /**
     * 开始监控Vikey状态
     */
    startMonitoring() {
        if (this.isMonitoring) {
            console.warn('Vikey监控已在运行中');
            return;
        }

        if (!this.isActiveXAvailable) {
            console.error('ActiveX控件不可用，无法开始监控');
            return;
        }

        this.isMonitoring = true;
        this.emitEvent('MONITORING_STARTED', {});

        // 启动定时监控
        this.monitoringInterval = setInterval(() => {
            this.checkVikeyStatus();
        }, this.config.monitoringInterval);

        // 立即执行一次状态检查
        this.checkVikeyStatus();
    }

    /**
     * 停止监控Vikey状态
     */
    stopMonitoring() {
        if (!this.isMonitoring) {
            return;
        }

        this.isMonitoring = false;

        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }

        this.emitEvent('MONITORING_STOPPED', {});
    }

    /**
     * 检查Vikey状态
     */
    async checkVikeyStatus() {
        try {
            if (!this.vikeyControl) {
                this.handleVikeyRemoved();
                return;
            }

            // 检查Vikey是否插入
            const isInserted = await this.checkVikeyInserted();
            const previousState = this.currentVikeyState;

            if (isInserted) {
                // Vikey已插入，获取详细信息
                const vikeyInfo = await this.getVikeyInfo();
                
                if (vikeyInfo) {
                    this.currentVikeyState = {
                        state: this.VIKEY_STATES.INSERTED,
                        info: vikeyInfo,
                        timestamp: new Date().toISOString()
                    };

                    // 状态变化检测
                    if (!previousState || previousState.state !== this.VIKEY_STATES.INSERTED) {
                        this.handleVikeyInserted(vikeyInfo);
                    }
                } else {
                    this.currentVikeyState = {
                        state: this.VIKEY_STATES.ERROR,
                        error: '无法获取Vikey信息',
                        timestamp: new Date().toISOString()
                    };
                    this.handleVikeyError(-1, '无法获取Vikey信息');
                }
            } else {
                // Vikey未插入
                this.currentVikeyState = {
                    state: this.VIKEY_STATES.REMOVED,
                    timestamp: new Date().toISOString()
                };

                if (previousState && previousState.state !== this.VIKEY_STATES.REMOVED) {
                    this.handleVikeyRemoved();
                }
            }

        } catch (error) {
            console.error('检查Vikey状态失败:', error);
            this.handleVikeyError(-2, error.message);
        }
    }

    /**
     * 检查Vikey是否插入
     */
    async checkVikeyInserted() {
        return new Promise((resolve) => {
            try {
                if (this.vikeyControl && typeof this.vikeyControl.IsInserted !== 'undefined') {
                    const result = this.vikeyControl.IsInserted();
                    resolve(!!result);
                } else {
                    // 备用方法：尝试获取设备ID
                    const deviceId = this.vikeyControl.GetDeviceID();
                    resolve(!!deviceId);
                }
            } catch (error) {
                resolve(false);
            }
        });
    }

    /**
     * 获取Vikey信息
     */
    async getVikeyInfo() {
        try {
            if (!this.vikeyControl) {
                return null;
            }

            const vikeyInfo = {
                deviceId: '',
                vikeyId: '',
                vikeyName: '',
                version: '',
                serialNumber: '',
                permissionLevel: 1,
                validFrom: null,
                validTo: null,
                state: this.VIKEY_STATES.INSERTED
            };

            // 获取基本信息
            if (typeof this.vikeyControl.GetDeviceID !== 'undefined') {
                vikeyInfo.deviceId = this.vikeyControl.GetDeviceID();
            }

            if (typeof this.vikeyControl.GetVikeyID !== 'undefined') {
                vikeyInfo.vikeyId = this.vikeyControl.GetVikeyID();
            }

            if (typeof this.vikeyControl.GetVikeyName !== 'undefined') {
                vikeyInfo.vikeyName = this.vikeyControl.GetVikeyName();
            }

            if (typeof this.vikeyControl.GetVersion !== 'undefined') {
                vikeyInfo.version = this.vikeyControl.GetVersion();
            }

            if (typeof this.vikeyControl.GetSerialNumber !== 'undefined') {
                vikeyInfo.serialNumber = this.vikeyControl.GetSerialNumber();
            }

            // 获取权限和时效信息
            if (typeof this.vikeyControl.GetPermissionLevel !== 'undefined') {
                vikeyInfo.permissionLevel = this.vikeyControl.GetPermissionLevel();
            }

            if (typeof this.vikeyControl.GetValidFrom !== 'undefined') {
                vikeyInfo.validFrom = this.vikeyControl.GetValidFrom();
            }

            if (typeof this.vikeyControl.GetValidTo !== 'undefined') {
                vikeyInfo.validTo = this.vikeyControl.GetValidTo();
            }

            // 检查时效性
            if (vikeyInfo.validTo) {
                const now = new Date();
                const validTo = new Date(vikeyInfo.validTo);
                
                if (now > validTo) {
                    vikeyInfo.state = this.VIKEY_STATES.EXPIRED;
                }
            }

            return vikeyInfo;

        } catch (error) {
            console.error('获取Vikey信息失败:', error);
            return null;
        }
    }

    /**
     * 验证Vikey
     * @param {string} challenge - 挑战码
     * @returns {Promise<Object>} 验证结果
     */
    async verifyVikey(challenge = null) {
        try {
            if (!this.vikeyControl) {
                return { success: false, error: 'Vikey控件不可用' };
            }

            // 设置挑战码
            if (challenge && typeof this.vikeyControl.SetChallenge !== 'undefined') {
                this.vikeyControl.SetChallenge(challenge);
            }

            // 执行验证
            let result;
            if (typeof this.vikeyControl.Verify !== 'undefined') {
                result = this.vikeyControl.Verify();
            } else {
                return { success: false, error: '验证方法不可用' };
            }

            if (result === 0) { // 0表示成功
                const vikeyInfo = await this.getVikeyInfo();
                this.currentVikeyState = {
                    state: this.VIKEY_STATES.AUTHENTICATED,
                    info: vikeyInfo,
                    timestamp: new Date().toISOString()
                };

                this.handleVikeyVerified({ success: true, info: vikeyInfo });
                return { success: true, info: vikeyInfo };
            } else {
                this.handleVikeyVerified({ success: false, error: this.getErrorMessage(result) });
                return { success: false, error: this.getErrorMessage(result) };
            }

        } catch (error) {
            console.error('验证Vikey失败:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * 处理Vikey插入事件
     * @param {Object} vikeyInfo - Vikey信息
     */
    handleVikeyInserted(vikeyInfo) {
        console.log('Vikey已插入:', vikeyInfo);
        
        this.emitEvent('VIKEY_INSERTED', {
            info: vikeyInfo,
            timestamp: new Date().toISOString()
        });

        // 记录日志
        this.logVikeyEvent('INSERTED', 'Vikey设备插入', vikeyInfo);

        // 更新UI状态
        this.updateUIStatus('inserted', vikeyInfo);
    }

    /**
     * 处理Vikey拔出事件
     */
    handleVikeyRemoved() {
        console.log('Vikey已拔出');
        
        this.emitEvent('VIKEY_REMOVED', {
            timestamp: new Date().toISOString()
        });

        // 记录日志
        this.logVikeyEvent('REMOVED', 'Vikey设备拔出', null);

        // 更新UI状态
        this.updateUIStatus('removed', null);

        // 清除当前Vikey信息
        this.currentVikeyState = null;
    }

    /**
     * 处理Vikey错误事件
     * @param {number} errorCode - 错误代码
     * @param {string} errorMessage - 错误信息
     */
    handleVikeyError(errorCode, errorMessage) {
        console.error('Vikey错误:', errorCode, errorMessage);
        
        this.emitEvent('VIKEY_ERROR', {
            errorCode: errorCode,
            errorMessage: errorMessage,
            timestamp: new Date().toISOString()
        });

        // 记录日志
        this.logVikeyEvent('ERROR', `Vikey错误: ${errorMessage}`, { errorCode, errorMessage });

        // 更新UI状态
        this.updateUIStatus('error', { errorCode, errorMessage });
    }

    /**
     * 处理Vikey验证事件
     * @param {Object} verificationResult - 验证结果
     */
    handleVikeyVerified(verificationResult) {
        console.log('Vikey验证结果:', verificationResult);
        
        this.emitEvent('VIKEY_VERIFIED', {
            result: verificationResult,
            timestamp: new Date().toISOString()
        });

        // 记录日志
        this.logVikeyEvent('VERIFIED', 
            verificationResult.success ? 'Vikey验证成功' : 'Vikey验证失败', 
            verificationResult);

        // 更新UI状态
        this.updateUIStatus('verified', verificationResult);
    }

    /**
     * 记录Vikey事件日志
     * @param {string} action - 动作类型
     * @param {string} description - 描述
     * @param {Object} data - 附加数据
     */
    logVikeyEvent(action, description, data) {
        if (!this.config.enableEventLogging) {
            return;
        }

        try {
            const logEntry = {
                action: action,
                description: description,
                data: data,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent
            };

            // 发送到日志系统
            if (window.vikeyDatabase && window.vikeyDatabase.logVikeyAction) {
                window.vikeyDatabase.logVikeyAction({
                    action: action,
                    details: description,
                    level: action === 'ERROR' ? 'error' : 'info',
                    data: data
                });
            }

            // 本地存储日志
            this.saveLocalLog(logEntry);

        } catch (error) {
            console.error('记录Vikey事件日志失败:', error);
        }
    }

    /**
     * 保存本地日志
     * @param {Object} logEntry - 日志条目
     */
    saveLocalLog(logEntry) {
        try {
            const logs = JSON.parse(localStorage.getItem('vikey_event_logs') || '[]');
            logs.push(logEntry);
            
            // 保留最近1000条日志
            if (logs.length > 1000) {
                logs.splice(0, logs.length - 1000);
            }
            
            localStorage.setItem('vikey_event_logs', JSON.stringify(logs));
        } catch (error) {
            console.error('保存本地日志失败:', error);
        }
    }

    /**
     * 更新UI状态
     * @param {string} status - 状态
     * @param {Object} data - 数据
     */
    updateUIStatus(status, data) {
        try {
            // 更新状态指示器
            const statusIndicator = document.getElementById('vikey-status-indicator');
            if (statusIndicator) {
                statusIndicator.className = `vikey-status vikey-status-${status}`;
                statusIndicator.title = this.getStatusText(status, data);
            }

            // 更新状态文本
            const statusText = document.getElementById('vikey-status-text');
            if (statusText) {
                statusText.textContent = this.getStatusText(status, data);
            }

            // 更新详细信息
            const statusDetails = document.getElementById('vikey-status-details');
            if (statusDetails && data) {
                statusDetails.innerHTML = this.formatStatusDetails(data);
            }

        } catch (error) {
            console.error('更新UI状态失败:', error);
        }
    }

    /**
     * 获取状态文本
     * @param {string} status - 状态
     * @param {Object} data - 数据
     * @returns {string} 状态文本
     */
    getStatusText(status, data) {
        const statusTexts = {
            'inserted': 'Vikey已插入',
            'removed': 'Vikey已拔出',
            'verified': 'Vikey验证成功',
            'error': 'Vikey错误'
        };

        let text = statusTexts[status] || '未知状态';

        if (status === 'inserted' && data && data.vikeyName) {
            text += ` - ${data.vikeyName}`;
        }

        if (status === 'error' && data && data.errorMessage) {
            text += ` - ${data.errorMessage}`;
        }

        return text;
    }

    /**
     * 格式化状态详情
     * @param {Object} data - 数据
     * @returns {string} 格式化的HTML
     */
    formatStatusDetails(data) {
        if (!data) return '';

        let html = '<div class="vikey-details">';
        
        if (data.vikeyId) {
            html += `<div><strong>Vikey ID:</strong> ${data.vikeyId}</div>`;
        }
        
        if (data.vikeyName) {
            html += `<div><strong>名称:</strong> ${data.vikeyName}</div>`;
        }
        
        if (data.serialNumber) {
            html += `<div><strong>序列号:</strong> ${data.serialNumber}</div>`;
        }
        
        if (data.permissionLevel) {
            html += `<div><strong>权限级别:</strong> ${data.permissionLevel}</div>`;
        }
        
        if (data.validTo) {
            html += `<div><strong>有效期至:</strong> ${new Date(data.validTo).toLocaleString()}</div>`;
        }

        html += '</div>';
        return html;
    }

    /**
     * 获取错误信息
     * @param {number} errorCode - 错误代码
     * @returns {string} 错误信息
     */
    getErrorMessage(errorCode) {
        const errorMessages = {
            0: '成功',
            '-1': 'Vikey未找到',
            '-2': '访问被拒绝',
            '-3': '验证失败',
            '-4': 'Vikey已过期',
            '-5': '设备错误',
            '-6': '通信错误'
        };

        return errorMessages[errorCode] || `未知错误 (${errorCode})`;
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
     * 获取当前Vikey状态
     * @returns {Object|null} 当前状态
     */
    getCurrentState() {
        return this.currentVikeyState;
    }

    /**
     * 检查Vikey是否可用
     * @returns {boolean} 是否可用
     */
    isVikeyAvailable() {
        return this.currentVikeyState && 
               (this.currentVikeyState.state === this.VIKEY_STATES.INSERTED || 
                this.currentVikeyState.state === this.VIKEY_STATES.AUTHENTICATED);
    }

    /**
     * 销毁监控器
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
        this.currentVikeyState = null;
        this.isActiveXAvailable = false;
    }
}

// 创建全局实例
const vikeyActiveXMonitor = new VikeyActiveXMonitor();

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VikeyActiveXMonitor;
} else {
    window.VikeyActiveXMonitor = VikeyActiveXMonitor;
    window.vikeyActiveXMonitor = vikeyActiveXMonitor;
}