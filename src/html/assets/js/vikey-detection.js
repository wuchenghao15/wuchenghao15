// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}
/**
 * Vikey 硬件检测模块
 * 用于检测 Vikey 硬件设备的连接状态和功能
 */
class VikeyDetection {
    constructor() {
        this.isVikeyConnected = false;
        this.detectionInterval = null;
        this.init();
    }
    /**
     * 初始化 Vikey 检测
     */
    init() {
        this.startDetection();
    }
    /**
     * 开始检测 Vikey 硬件
     */
    startDetection() {
        // 模拟 Vikey 硬件检测
        this.detectionInterval = setInterval(() => {
            this.checkVikeyConnection();
        }, 5000);
    }
    /**
     * 检查 Vikey 连接状态
     */
    checkVikeyConnection() {
        const randomDetection = Math.random() > 0.7;
        if (randomDetection !== this.isVikeyConnected) {
            this.isVikeyConnected = randomDetection;
            if (this.isVikeyConnected) {
                this.onVikeyConnected();
            } else {
                this.onVikeyDisconnected();
            }
        }
    }
    /**
     * Vikey 连接时的回调
     */
    onVikeyConnected() {
        const event = new CustomEvent('vikey-connected', {
            detail: {
                timestamp: new Date().toISOString(),
                deviceId: 'Vikey-' + Math.random().toString(36).substr(2, 9)
            }
        });
        document.dispatchEvent(event);
    }
    /**
     * Vikey 断开连接时的回调
     */
    onVikeyDisconnected() {
        const event = new CustomEvent('vikey-disconnected', {
            detail: {
                timestamp: new Date().toISOString()
            }
        });
        document.dispatchEvent(event);
    }
    /**
     * 获取 Vikey 连接状态
     * @return s {boolean} Vikey 连接状态
     */
    getVikeyStatus() {
        return this.isVikeyConnected;
    }
    /**
     * 停止检测
     */
    stopDetection() {
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
        }
    }
}
// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VikeyDetection;
} else {
    window.VikeyDetection = VikeyDetection;
    // 自动初始化
    window.vikeyDetector = new VikeyDetection();
}