// VERSION: 20251106.a5d79325b34703ec0944791
// HardwareKey API JavaScript 实现 - 增强版

// 设备类型枚举 - 扩展支持更多现代设备类型
const HardwareKeyType = {
    HardwareKeyAPP: 0,                          // 应用型加密狗
    HardwareKeySTD: 1,                          // 标准型加密狗
    HardwareKeyNET: 2,                          // 网络型加密狗
    HardwareKeyPRO: 3,                          // 专业型加密狗
    HardwareKeyWEB: 4,                          // 网页验证型加密狗
    HardwareKeyTIME: 5,                         // 时间型加密狗
    HardwareKeyMultiFunctional: 0x0A,           // 多功能加密狗
    HardwareKeyMultiFunctionalTime: 0x0B,       // 多功能时间加密狗
    HardwareKeyCloud: 0x0C,                     // 云验证型加密狗
    HardwareKeyMobile: 0x0D,                    // 移动设备验证器
    HardwareKeySecure: 0x0E,                    // 高安全性加密狗
    HardwareKeyInvalid: 0xFF                    // 无效类型
};

// 权限级别
const HardwareKeyNoLevel = 0;    // 无权限
const HardwareKeyUserLevel = 1;  // 用户权限
const HardwareKeyAdminLevel = 2; // 管理员权限

// 错误码定义
const HardwareKeyError = {
    HARDWAREKEY_SUCCESS: 0x00000000,                  // 成功
    HARDWAREKEY_ERROR_NO_HARDWAREKEY: 0x80000001,           // 未找到HardwareKey设备
    HARDWAREKEY_ERROR_INVALID_PASSWORD: 0x80000002,    // 密码错误
    HARDWAREKEY_ERROR_NEED_FIND: 0x80000003,          // 首先需要查找设备
    HARDWAREKEY_ERROR_INVALID_INDEX: 0x80000004,       // 无效索引
    HARDWAREKEY_ERROR_INVALID_VALUE: 0x80000005,       // 数值无效
    HARDWAREKEY_ERROR_INVALID_KEY: 0x80000006,         // 密钥无效
    HARDWAREKEY_ERROR_GET_VALUE: 0x80000007,           // 获取信息失败
    HARDWAREKEY_ERROR_SET_VALUE: 0x80000008,           // 设置信息失败
    HARDWAREKEY_ERROR_NO_CHANCE: 0x80000009,           // 没有机会
    HARDWAREKEY_ERROR_NO_TAUTHORITY: 0x8000000A,       // 权限不足
    HARDWAREKEY_ERROR_INVALID_ADDR_OR_SIZE: 0x8000000B, // 地址或大小无效
    HARDWAREKEY_ERROR_RANDOM: 0x8000000C,              // 获取随机数失败
    HARDWAREKEY_ERROR_SEED: 0x8000000D,                // 获取种子失败
    HARDWAREKEY_ERROR_CONNECTION: 0x8000000E,          // 连接错误
    HARDWAREKEY_ERROR_CALCULATE: 0x8000000F,           // 算法计算错误
    HARDWAREKEY_ERROR_MODULE: 0x80000010,              // 模块错误
    HARDWAREKEY_ERROR_GENERATE_NEW_PASSWORD: 0x80000011, // 生成新密码失败
    HARDWAREKEY_ERROR_ENCRYPT_FAILED: 0x80000012,       // 加密数据失败
    HARDWAREKEY_ERROR_DECRYPT_FAILED: 0x80000013,       // 解密数据失败
    HARDWAREKEY_ERROR_ALREADY_LOCKED: 0x80000014,       // HardwareKey设备已经被锁定
    HARDWAREKEY_ERROR_UNKNOWN_COMMAND: 0x80000015,      // 无效命令
    HARDWAREKEY_ERROR_NO_SUPPORT: 0x80000016,           // 当前HardwareKey设备不支持此功能
    HARDWAREKEY_ERROR_CATCH: 0x80000017,                // 捕获异常
    HARDWAREKEY_ERROR_GET_USBDATA: 0x80000018,          // 获取USB数据失败
    HARDWAREKEY_ERROR_SET_USBDATA: 0x80000019,          // 设置USB数据失败
    HARDWAREKEY_ERROR_TIME_MODULE: 0x8000001A,          // 硬件时间模块错误
    HARDWAREKEY_ERROR_TIME_OUTAGE: 0x8000001B,          // 硬件时间电池电量不足
    HARDWAREKEY_ERROR_MAX_CONNECTION: 0x8000001C,       // 加密狗达到最大连接数
    HARDWAREKEY_ERROR_COMMUNICATION: 0x8000001D,        // 加密狗通信数据错误
    HARDWAREKEY_ERROR_TIME: 0x8000001E,                 // 加密狗时间错误
    HARDWAREKEY_ERROR_UNKNOWN_ERROR: 0xFFFFFFFF         // 未知错误
};

// LED状态定义
const LEDStatus = {
    LED_OFF: 0,         // 关闭
    LED_ON: 1,          // 开启
    LED_BLINK: 2,       // 闪烁
    LED_OFF_BLINK: 3,   // 平时关闭-通讯时闪烁
    LED_ON_BLINK: 4     // 平时开启-通讯时闪烁
};

class HardwareKeyAPI {
    constructor() {
        this.devices = [];
        this.initialized = false;
        this.authTokens = new Map(); // 用于存储HardwareKey认证令牌
        this.lastActivity = new Date().getTime();
        
        // 启用自动检查以维护会话状态
        this.startSessionMonitoring();
    }
    
    /**
     * 启动会话监控，定期检查设备连接状态
     */
    startSessionMonitoring() {
        setInterval(() => {
            const now = new Date().getTime();
            // 如果超过5分钟没有活动，重新检查设备连接
            if (now - this.lastActivity > 300000 && this.initialized) {
                console.log('会话超时，重新检查设备连接...');
                this.checkDeviceConnection().catch(err => {
                    console.error('设备连接检查失败:', err);
                });
            }
        }, 60000); // 每分钟检查一次
    }
    
    /**
     * 检查设备连接状态
     * @returns {Promise<Object>} {code: 错误码, connected: 是否已连接}
     */
    async checkDeviceConnection() {
        try {
            // 重新验证设备是否仍连接
            const result = await this.HardwareKeyFind();
            const connected = result.code === HardwareKeyError.HARDWAREKEY_SUCCESS && result.count > 0;
            
            if (!connected) {
                // 如果设备已断开连接，重置状态
                this.initialized = false;
                this.devices = [];
                this.authTokens.clear();
            }
            
            return { code: result.code, connected };
        } catch (error) {
            console.error('检查设备连接失败:', error);
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_UNKNOWN_ERROR, connected: false };
        }
    }
    
    /**
     * 更新活动时间，防止会话超时
     */
    updateActivity() {
        this.lastActivity = new Date().getTime();
    }

    /**
     * 查找设备 - 增强版，添加更详细的设备信息
     * @returns {Object} {code: 错误码, count: 找到的设备数量, devices: 设备列表}
     */
    async HardwareKeyFind() {
        try {
            this.updateActivity();
            
            // 模拟查找设备，实际项目中应该调用原生接口
            // 增强版返回更详细的设备信息
            this.devices = [{
                id: '0001',
                type: HardwareKeyType.HardwareKeySecure,
                version: '3.0',
                status: 'active',
                lastAccessTime: new Date().toISOString()
            }];
            
            this.initialized = true;
            console.log(`找到 ${this.devices.length} 个HardwareKey设备`);
            
            return {
                code: HardwareKeyError.HARDWAREKEY_SUCCESS,
                count: this.devices.length,
                devices: this.devices
            };
        } catch (error) {
            console.error('查找设备失败:', error);
            return {
                code: HardwareKeyError.HARDWAREKEY_ERROR_NO_HARDWAREKEY,
                count: 0,
                devices: []
            };
        }
    }

    /**
     * 查找设备Ex
     * @returns {Object} {code: 错误码, count: 找到的设备数量}
     */
    async HardwareKeyFindEx() {
        return this.HardwareKeyFind();
    }

    /**
     * 卸载设备
     * @returns {Object} {code: 错误码}
     */
    async HardwareKeyUninitialization() {
        try {
            this.devices = [];
            this.initialized = false;
            return { code: HardwareKeyError.HARDWAREKEY_SUCCESS };
        } catch (error) {
            console.error('卸载设备失败:', error);
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_UNKNOWN_ERROR };
        }
    }

    /**
     * 获取设备硬件ID
     * @param {number} index 设备索引
     * @returns {Object} {code: 错误码, hid: 硬件ID}
     */
    async HardwareKeyGetHID(index) {
        if (!this.initialized) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_NEED_FIND, hid: 0 };
        }

        if (index < 0 || index >= this.devices.length) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_INVALID_INDEX, hid: 0 };
        }

        try {
            // 模拟返回硬件ID
            if (this.devices && this.devices[index] && this.devices[index].id) {
                const hid = parseInt(this.devices[index].id, 16);
                return { code: HardwareKeyError.HARDWAREKEY_SUCCESS, hid };
            } else {
                return { code: HardwareKeyError.HARDWAREKEY_ERROR_GET_VALUE, hid: 0 };
            }
        } catch (error) {
            console.error('获取硬件ID失败:', error);
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_GET_VALUE, hid: 0 };
        }
    }

    /**
     * 获取设备类型
     * @param {number} index 设备索引
     * @returns {Object} {code: 错误码, type: 设备类型}
     */
    async HardwareKeyGetType(index) {
        if (!this.initialized) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_NEED_FIND, type: HardwareKeyType.HardwareKeyInvalid };
        }

        if (index < 0 || index >= this.devices.length) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_INVALID_INDEX, type: HardwareKeyType.HardwareKeyInvalid };
        }

        try {
            if (this.devices && this.devices[index] && this.devices[index].type !== undefined) {
                return { code: HardwareKeyError.HARDWAREKEY_SUCCESS, type: this.devices[index].type };
            } else {
                return { code: HardwareKeyError.HARDWAREKEY_ERROR_GET_VALUE, type: HardwareKeyType.HardwareKeyInvalid };
            }
        } catch (error) {
            console.error('获取设备类型失败:', error);
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_GET_VALUE, type: HardwareKeyType.HardwareKeyInvalid };
        }
    }

    /**
     * 获取设备当前权限
     * @param {number} index 设备索引
     * @returns {Object} {code: 错误码, level: 权限级别}
     */
    async HardwareKeyGetLevel(index) {
        if (!this.initialized) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_NEED_FIND, level: HardwareKeyNoLevel };
        }

        if (index < 0 || index >= this.devices.length) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_INVALID_INDEX, level: HardwareKeyNoLevel };
        }

        try {
            // 模拟返回权限级别，实际应从设备读取
            return { code: HardwareKeyError.HARDWAREKEY_SUCCESS, level: HardwareKeyNoLevel };
        } catch (error) {
            console.error('获取权限级别失败:', error);
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_GET_VALUE, level: HardwareKeyNoLevel };
        }
    }

    /**
     * 设置产品名称
     * @param {number} index 设备索引
     * @param {string} name 产品名称（最大16字节）
     * @returns {Object} {code: 错误码}
     */
    async HardwareKeySetPtroductName(index, name) {
        if (!this.initialized) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_NEED_FIND };
        }

        if (index < 0 || index >= this.devices.length) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_INVALID_INDEX };
        }

        try {
            // 模拟设置产品名称
            console.log(`设置产品名称: ${name}`);
            return { code: HardwareKeyError.HARDWAREKEY_SUCCESS };
        } catch (error) {
            console.error('设置产品名称失败:', error);
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_SET_VALUE };
        }
    }

    /**
     * 获取产品名称
     * @param {number} index 设备索引
     * @returns {Object} {code: 错误码, name: 产品名称}
     */
    async HardwareKeyGetPtroductName(index) {
        if (!this.initialized) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_NEED_FIND, name: '' };
        }

        if (index < 0 || index >= this.devices.length) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_INVALID_INDEX, name: '' };
        }

        try {
            // 模拟返回产品名称
            return { code: HardwareKeyError.HARDWAREKEY_SUCCESS, name: 'MTSC HardwareKey' };
        } catch (error) {
            console.error('获取产品名称失败:', error);
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_GET_VALUE, name: '' };
        }
    }

    /**
     * 用户登录
     * @param {number} index 设备索引
     * @param {string} password 用户密码
     * @returns {Object} {code: 错误码}
     */
    async HardwareKeyUserLogin(index, password) {
        if (!this.initialized) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_NEED_FIND };
        }

        if (index < 0 || index >= this.devices.length) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_INVALID_INDEX };
        }

        try {
            // 模拟用户登录验证
            // 在实际应用中，这里应该调用原生接口进行验证
            console.log(`用户登录，索引: ${index}, 密码: ${password}`);
            
            // 这里可以根据实际情况返回不同的错误码
            return { code: HardwareKeyError.HARDWAREKEY_SUCCESS };
        } catch (error) {
            console.error('用户登录失败:', error);
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_INVALID_PASSWORD };
        }
    }

    /**
     * 管理员登录
     * @param {number} index 设备索引
     * @param {string} password 管理员密码
     * @returns {Object} {code: 错误码}
     */
    async HardwareKeyAdminLogin(index, password) {
        if (!this.initialized) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_NEED_FIND };
        }

        if (index < 0 || index >= this.devices.length) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_INVALID_INDEX };
        }

        try {
            this.updateActivity();
            // 模拟管理员登录验证
            console.log(`管理员登录，索引: ${index}`);
            return { code: HardwareKeyError.HARDWAREKEY_SUCCESS };
        } catch (error) {
            console.error('管理员登录失败:', error);
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_INVALID_PASSWORD };
        }
    }
    
    /**
     * 验证HardwareKey认证码 - 新增功能
     * @param {string} HardwareKey HardwareKey认证码
     * @param {number} index 设备索引（可选）
     * @returns {Object} {code: 错误码, valid: 是否有效, token: 认证令牌}
     */
    async HardwareKeyVerifyAuthCode(HardwareKey, index = 0) {
        try {
            this.updateActivity();
            
            if (!this.initialized) {
                console.log('需要先查找设备');
                // 尝试自动查找设备
                const findResult = await this.HardwareKeyFind();
                if (findResult.code !== HardwareKeyError.HARDWAREKEY_SUCCESS) {
                    return { 
                        code: HardwareKeyError.HARDWAREKEY_ERROR_NO_HARDWAREKEY, 
                        valid: false, 
                        token: null 
                    };
                }
            }
            
            if (index < 0 || index >= this.devices.length) {
                return { 
                    code: HardwareKeyError.HARDWAREKEY_ERROR_INVALID_INDEX, 
                    valid: false, 
                    token: null 
                };
            }
            
            // 验证HardwareKey格式 - 基本格式检查：至少8位，包含字母和数字
            const isValidFormat = HardwareKey && HardwareKey.length >= 8 && /[A-Za-z]/.test(HardwareKey) && /[0-9]/.test(HardwareKey);
            
            if (!isValidFormat) {
                return { 
                    code: HardwareKeyError.HARDWAREKEY_ERROR_INVALID_VALUE, 
                    valid: false, 
                    token: null 
                };
            }
            
            // 在实际应用中，这里应该调用原生接口进行验证
            // 模拟验证逻辑
            console.log(`验证HardwareKey认证码: ${HardwareKey.substring(0, 3)}****${HardwareKey.substring(HardwareKey.length-3)}`);
            
            // 生成认证令牌
            if (this.devices && this.devices[index] && this.devices[index].id) {
                const token = this.generateAuthToken(HardwareKey, this.devices[index].id);
                this.authTokens.set(HardwareKey, { token, timestamp: new Date().getTime() });
                
                return { 
                    code: HardwareKeyError.HARDWAREKEY_SUCCESS, 
                    valid: true, 
                    token 
                };
            } else {
                return { 
                    code: HardwareKeyError.HARDWAREKEY_ERROR_GET_VALUE, 
                    valid: false, 
                    token: null 
                };
            }
        } catch (error) {
            console.error('HardwareKey验证失败:', error);
            return { 
                code: HardwareKeyError.HARDWAREKEY_ERROR_UNKNOWN_ERROR, 
                valid: false, 
                token: null 
            };
        }
    }
    
    /**
     * 生成认证令牌
     * @private
     * @param {string} HardwareKey HardwareKey认证码
     * @param {string} deviceId 设备ID
     * @returns {string} 认证令牌
     */
    generateAuthToken(HardwareKey, deviceId) {
        const timestamp = new Date().getTime();
        // 简单的令牌生成，实际应用中应该使用更安全的方法
        const baseToken = `${HardwareKey}-${deviceId}-${timestamp}`;
        // 生成一个简单的哈希作为令牌（实际应用应使用更安全的哈希算法）
        let hash = 0;
        for (let i = 0; i < baseToken.length; i++) {
            const char = baseToken.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // 转换为32位整数
        }
        return `HARDWAREKEY-${Math.abs(hash).toString(16).toUpperCase()}-${timestamp}`;
    }
    
    /**
     * 验证认证令牌是否有效
     * @param {string} token 认证令牌
     * @returns {Object} {valid: 是否有效, expires: 过期时间}
     */
    async HardwareKeyValidateToken(token) {
        try {
            this.updateActivity();
            
            // 检查令牌格式
            if (!token || !token.startsWith('HARDWAREKEY-')) {
                return { valid: false, expires: null };
            }
            
            // 从令牌中提取时间戳
            const parts = token.split('-');
            if (parts.length < 3) {
                return { valid: false, expires: null };
            }
            
            const timestamp = parseInt(parts[2], 10);
            const now = new Date().getTime();
            const tokenAge = now - timestamp;
            
            // 令牌有效期为30分钟
            const valid = tokenAge <= 1800000;
            const expires = new Date(timestamp + 1800000).toISOString();
            
            return { valid, expires };
        } catch (error) {
            console.error('令牌验证失败:', error);
            return { valid: false, expires: null };
        }
    }

    /**
     * 注销登录 - 增强版，同时清除认证令牌
     * @param {number} index 设备索引
     * @returns {Object} {code: 错误码}
     */
    async HardwareKeyLogoff(index) {
        if (!this.initialized) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_NEED_FIND };
        }

        if (index < 0 || index >= this.devices.length) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_INVALID_INDEX };
        }

        try {
            this.updateActivity();
            // 清除所有认证令牌
            this.authTokens.clear();
            console.log(`注销登录，索引: ${index}，已清除所有认证令牌`);
            return { code: HardwareKeyError.HARDWAREKEY_SUCCESS };
        } catch (error) {
            console.error('注销登录失败:', error);
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_UNKNOWN_ERROR };
        }
    }

    /**
     * 设置用户密码尝试次数
     * @param {number} index 设备索引
     * @param {number} attempt 尝试次数
     * @returns {Object} {code: 错误码}
     */
    async HardwareKeySetUserPassWordAttempt(index, attempt) {
        if (!this.initialized) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_NEED_FIND };
        }

        if (index < 0 || index >= this.devices.length) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_INVALID_INDEX };
        }

        try {
            console.log(`设置用户密码尝试次数: ${attempt}`);
            return { code: HardwareKeyError.HARDWAREKEY_SUCCESS };
        } catch (error) {
            console.error('设置用户密码尝试次数失败:', error);
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_SET_VALUE };
        }
    }

    /**
     * 获取用户密码尝试次数
     * @param {number} index 设备索引
     * @returns {Object} {code: 错误码, currentAttempt: 当前尝试次数, maxAttempt: 最大尝试次数}
     */
    async HardwareKeyGetUserPassWordAttempt(index) {
        if (!this.initialized) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_NEED_FIND, currentAttempt: 0, maxAttempt: 0 };
        }

        if (index < 0 || index >= this.devices.length) {
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_INVALID_INDEX, currentAttempt: 0, maxAttempt: 0 };
        }

        try {
            // 模拟返回尝试次数
            return { code: HardwareKeyError.HARDWAREKEY_SUCCESS, currentAttempt: 3, maxAttempt: 5 };
        } catch (error) {
            console.error('获取用户密码尝试次数失败:', error);
            return { code: HardwareKeyError.HARDWAREKEY_ERROR_GET_VALUE, currentAttempt: 0, maxAttempt: 0 };
        }
    }
}

// 导出API
// 创建全局实例
window.HardwareKeyAPI = new HardwareKeyAPI();
// 暴露常量到全局
window.HardwareKeyType = HardwareKeyType;
window.HardwareKeyNoLevel = HardwareKeyNoLevel;
window.HardwareKeyUserLevel = HardwareKeyUserLevel;
window.HardwareKeyAdminLevel = HardwareKeyAdminLevel;
window.HardwareKeyError = HardwareKeyError;
window.LEDStatus = LEDStatus;