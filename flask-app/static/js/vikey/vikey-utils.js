// ViKey工具函数库
// 提供ViKey相关的辅助功能和工具函数

// 全局Vikey对象
if (typeof window.MTSCOS === 'undefined') {
    window.MTSCOS = {};
}
if (typeof MTSCOS.Vikey === 'undefined') {
    MTSCOS.Vikey = {};
}

/**
 * ViKey工具函数
 */
MTSCOS.Vikey.Utils = {
    /**
     * 格式化ViKey硬件ID
     * @param {string} hardwareId - ViKey硬件ID
     * @returns {string} 格式化后的硬件ID
     */
    formatHardwareId: function(hardwareId) {
        if (!hardwareId) return '';
        // 将硬件ID格式化为每4位一组，用连字符分隔
        return hardwareId.replace(/(.{4})(?=.{4})/g, '$1-$');
    },
    
    /**
     * 检查浏览器兼容性
     * @returns {object} 浏览器兼容性信息
     */
    checkBrowserCompatibility: function() {
        const isIE = /Trident|MSIE/.test(window.navigator.userAgent);
        const isEdge = /Edge\//.test(window.navigator.userAgent);
        const isChrome = /Chrome\//.test(window.navigator.userAgent);
        const isFirefox = /Firefox\//.test(window.navigator.userAgent);
        const isSafari = /Safari\//.test(window.navigator.userAgent) && !isChrome;
        
        return {
            isCompatible: isIE || isEdge,
            browserName: isIE ? 'IE' : isEdge ? 'Edge' : isChrome ? 'Chrome' : isFirefox ? 'Firefox' : isSafari ? 'Safari' : 'Unknown',
            supportsActiveX: isIE || isEdge
        };
    },
    
    /**
     * 生成随机挑战码
     * @param {number} length - 挑战码长度
     * @returns {string} 随机挑战码
     */
    generateChallenge: function(length = 32) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    },
    
    /**
     * 验证ViKey签名
     * @param {string} signature - 签名数据
     * @param {string} challenge - 挑战码
     * @param {string} hardwareId - 硬件ID
     * @returns {boolean} 签名是否有效
     */
    verifySignature: function(signature, challenge, hardwareId) {
        // 这里实现签名验证逻辑
        // 实际项目中应该调用服务器端API进行验证
        return signature && signature.length > 0;
    },
    
    /**
     * 获取ViKey状态文本
     * @param {boolean} connected - 是否连接
     * @param {boolean} isAdmin - 是否为管理员
     * @returns {string} 状态文本
     */
    getStatusText: function(connected, isAdmin) {
        if (!connected) {
            return '未检测到Vikey';
        }
        return isAdmin ? 'Vikey管理员已连接' : 'Vikey用户已连接';
    },
    
    /**
     * 显示Vikey状态通知
     * @param {string} message - 通知消息
     * @param {string} type - 通知类型：success, error, info, warning
     */
    showNotification: function(message, type = 'info') {
        // 这里实现通知显示逻辑
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // 如果页面上有通知组件，可以调用它来显示
        if (typeof MTSCOS.UI !== 'undefined' && MTSCOS.UI.Notification) {
            MTSCOS.UI.Notification.show(message, type);
        }
    },
    
    /**
     * 保存Vikey配置
     * @param {object} config - 配置对象
     */
    saveConfig: function(config) {
        try {
            localStorage.setItem('vikey_config', JSON.stringify(config));
            return true;
        } catch (error) {
            console.error('保存Vikey配置失败:', error);
            return false;
        }
    },
    
    /**
     * 加载Vikey配置
     * @returns {object} 配置对象
     */
    loadConfig: function() {
        try {
            const config = localStorage.getItem('vikey_config');
            return config ? JSON.parse(config) : {
                detectionInterval: 1000,
                autoLogin: false,
                showNotifications: true
            };
        } catch (error) {
            console.error('加载Vikey配置失败:', error);
            return {
                detectionInterval: 1000,
                autoLogin: false,
                showNotifications: true
            };
        }
    },
    
    /**
     * 清理Vikey相关数据
     */
    clearVikeyData: function() {
        try {
            localStorage.removeItem('vikey_config');
            localStorage.removeItem('vikey_hardware_id');
            localStorage.removeItem('vikey_last_connected');
            return true;
        } catch (error) {
            console.error('清理Vikey数据失败:', error);
            return false;
        }
    },
    
    /**
     * 检查是否为Vikey管理员
     * @param {string} hardwareId - ViKey硬件ID
     * @returns {Promise<boolean>} 是否为管理员
     */
    checkAdminPrivilege: async function(hardwareId) {
        // 这里实现管理员权限检查逻辑
        // 实际项目中应该调用服务器端API进行验证
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve(hardwareId && hardwareId.length > 0);
            }, 100);
        });
    },
    
    /**
     * 获取ViKey版本信息
     * @returns {object} 版本信息
     */
    getVersionInfo: function() {
        return {
            vikeyUtilsVersion: '1.0.0',
            vikeyDetectionVersion: '1.0.0',
            vikeyConfigVersion: '1.0.0'
        };
    }
};

// 导出工具函数（如果支持模块化）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MTSCOS.Vikey.Utils;
}
