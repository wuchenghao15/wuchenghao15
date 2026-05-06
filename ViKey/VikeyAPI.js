// VikeyAPI.js - ViKey加密狗API接口

// 设备类型枚举
const VikeyType = {
    ViKeyAPP: 0,                          // 应用型加密狗
    ViKeySTD: 1,                          // 标准型加密狗
    ViKeyNET: 2,                          // 网络型加密狗
    ViKeyPRO: 3,                          // 专业型加密狗
    ViKeyWEB: 4,                          // 网页验证型加密狗
    ViKeyTIME: 5,                         // 时间型加密狗
    ViKeyMultiFunctional: 0x0A,           // 多功能加密狗
    ViKeyMultiFunctionalTime: 0x0B,       // 多功能时间加密狗
    ViKeyCloud: 0x0C,                     // 云验证型加密狗
    ViKeyMobile: 0x0D,                    // 移动设备验证器
    ViKeySecure: 0x0E,                    // 高安全性加密狗
    ViKeyInvalid: 0xFF                    // 无效类型
};

// 权限级别
const ViKeyNoLevel = 0;    // 无权限
const ViKeyUserLevel = 1;  // 用户权限
const ViKeyAdminLevel = 2; // 管理员权限

// 错误码定义
const VikeyError = {
    VIKEY_SUCCESS: 0x00000000,                  // 成功
    VIKEY_ERROR_NO_VIKEY: 0x80000001,           // 未找到ViKey设备
    VIKEY_ERROR_INVALID_PASSWORD: 0x80000002,    // 密码错误
    VIKEY_ERROR_NEED_FIND: 0x80000003,          // 首先需要查找设备
    VIKEY_ERROR_INVALID_INDEX: 0x80000004,       // 无效索引
    VIKEY_ERROR_INVALID_VALUE: 0x80000005,       // 数值无效
    VIKEY_ERROR_INVALID_KEY: 0x80000006,         // 密钥无效
    VIKEY_ERROR_GET_VALUE: 0x80000007,           // 获取信息失败
    VIKEY_ERROR_SET_VALUE: 0x80000008,           // 设置信息失败
    VIKEY_ERROR_NO_CHANCE: 0x80000009,           // 没有机会
    VIKEY_ERROR_NO_TAUTHORITY: 0x8000000A,       // 权限不足
    VIKEY_ERROR_INVALID_ADDR_OR_SIZE: 0x8000000B, // 地址或大小无效
    VIKEY_ERROR_RANDOM: 0x8000000C,              // 获取随机数失败
    VIKEY_ERROR_SEED: 0x8000000D,                // 获取种子失败
    VIKEY_ERROR_CONNECTION: 0x8000000E,          // 连接错误
    VIKEY_ERROR_CALCULATE: 0x8000000F,           // 算法计算错误
    VIKEY_ERROR_MODULE: 0x80000010,              // 模块错误
    VIKEY_ERROR_GENERATE_NEW_PASSWORD: 0x80000011, // 生成新密码失败
    VIKEY_ERROR_ENCRYPT_FAILED: 0x80000012,       // 加密数据失败
    VIKEY_ERROR_DECRYPT_FAILED: 0x80000013,       // 解密数据失败
    VIKEY_ERROR_ALREADY_LOCKED: 0x80000014,       // ViKey设备已经被锁定
    VIKEY_ERROR_UNKNOWN_COMMAND: 0x80000015,      // 无效命令
    VIKEY_ERROR_NO_SUPPORT: 0x80000016,           // 当前ViKey设备不支持此功能
    VIKEY_ERROR_CATCH: 0x80000017,                // 捕获异常
    VIKEY_ERROR_GET_USBDATA: 0x80000018,          // 获取USB数据失败
    VIKEY_ERROR_SET_USBDATA: 0x80000019,          // 设置USB数据失败
    VIKEY_ERROR_TIME_MODULE: 0x8000001A,          // 硬件时间模块错误
    VIKEY_ERROR_TIME_OUTAGE: 0x8000001B,          // 硬件时间电池电量不足
    VIKEY_ERROR_MAX_CONNECTION: 0x8000001C,       // 加密狗达到最大连接数
    VIKEY_ERROR_COMMUNICATION: 0x8000001D,        // 加密狗通信数据错误
    VIKEY_ERROR_TIME: 0x8000001E,                 // 加密狗时间错误
    VIKEY_ERROR_UNKNOWN_ERROR: 0xFFFFFFFF         // 未知错误
};

// LED状态枚举
const LEDStatus = {
    LED_OFF: 0,         // 关闭
    LED_ON: 1,          // 开启
    LED_BLINK: 2,       // 闪烁
    LED_OFF_BLINK: 3,   // 平时关闭-通讯时闪烁
    LED_ON_BLINK: 4     // 平时开启-通讯时闪烁
};

// ViKey API主类
class VikeyAPI {
    constructor() {
        this.sessionTimeout = 30 * 60 * 1000; // 30分钟会话超时
        this.lastActivityTime = Date.now();
        this.startSessionMonitoring();
    }
    
    // 开始会话监控
    startSessionMonitoring() {
        setInterval(() => {
            const currentTime = Date.now();
            if (currentTime - this.lastActivityTime > this.sessionTimeout) {
                console.log('会话超时，需要重新验证');
                // 这里可以添加会话超时后的处理逻辑
            }
        }, 60000); // 每分钟检查一次
    }
    
    // 检查设备连接状态
    async checkDeviceConnection() {
        try {
            // 这里是模拟的设备连接检查
            // 实际应用中应该调用真实的设备检测API
            console.log('检查ViKey设备连接...');
            this.updateActivity();
            
            // 模拟随机返回连接状态
            const isConnected = Math.random() > 0.5;
            
            if (isConnected) {
                return { code: VikeyError.VIKEY_SUCCESS, connected: true };
            } else {
                return { code: VikeyError.VIKEY_ERROR_NO_VIKEY, connected: false };
            }
        } catch (error) {
            console.error('检查设备连接失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH, connected: false };
        }
    }
    
    // 更新最后活动时间
    updateActivity() {
        this.lastActivityTime = Date.now();
    }
    
    // 查找ViKey设备
    async VikeyFind() {
        try {
            this.updateActivity();
            console.log('查找ViKey设备...');
            
            // 模拟查找设备，返回随机数量的设备
            const deviceCount = Math.floor(Math.random() * 3);
            
            if (deviceCount > 0) {
                return { code: VikeyError.VIKEY_SUCCESS, count: deviceCount };
            } else {
                return { code: VikeyError.VIKEY_ERROR_NO_VIKEY, count: 0 };
            }
        } catch (error) {
            console.error('查找设备失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH, count: 0 };
        }
    }
    
    // 扩展查找ViKey设备
    async VikeyFindEx() {
        try {
            this.updateActivity();
            const result = await this.VikeyFind();
            
            if (result.code === VikeyError.VIKEY_SUCCESS) {
                // 模拟返回设备详情
                const devices = [];
                for (let i = 0; i < result.count; i++) {
                    devices.push({
                        index: i,
                        type: VikeyType.ViKeySTD,
                        hid: `VIKEY${1000 + i}`
                    });
                }
                return { code: VikeyError.VIKEY_SUCCESS, devices: devices };
            }
            
            return result;
        } catch (error) {
            console.error('扩展查找设备失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH, devices: [] };
        }
    }
    
    // 卸载ViKey
    async VikeyUninitialization() {
        try {
            this.updateActivity();
            console.log('卸载ViKey...');
            // 模拟卸载操作
            return { code: VikeyError.VIKEY_SUCCESS };
        } catch (error) {
            console.error('卸载设备失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH };
        }
    }
    
    // 获取设备HID
    async VikeyGetHID(index) {
        try {
            this.updateActivity();
            console.log(`获取设备${index}的HID...`);
            
            // 模拟返回设备HID
            const hid = `VIKEY${1000 + index}`;
            return { code: VikeyError.VIKEY_SUCCESS, hid: hid };
        } catch (error) {
            console.error('获取设备HID失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH, hid: '' };
        }
    }
    
    // 获取设备类型
    async VikeyGetType(index) {
        try {
            this.updateActivity();
            console.log(`获取设备${index}的类型...`);
            
            // 模拟返回设备类型
            return { code: VikeyError.VIKEY_SUCCESS, type: VikeyType.ViKeySTD };
        } catch (error) {
            console.error('获取设备类型失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH, type: VikeyType.ViKeyInvalid };
        }
    }
    
    // 获取权限级别
    async VikeyGetLevel(index) {
        try {
            this.updateActivity();
            console.log(`获取设备${index}的权限级别...`);
            
            // 模拟返回权限级别
            return { code: VikeyError.VIKEY_SUCCESS, level: ViKeyUserLevel };
        } catch (error) {
            console.error('获取权限级别失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH, level: ViKeyNoLevel };
        }
    }
    
    // 设置产品名称
    async VikeySetPtroductName(index, name) {
        try {
            this.updateActivity();
            console.log(`设置设备${index}的产品名称: ${name}`);
            
            // 模拟设置产品名称
            if (name && name.length > 0 && name.length <= 32) {
                return { code: VikeyError.VIKEY_SUCCESS };
            } else {
                return { code: VikeyError.VIKEY_ERROR_INVALID_VALUE };
            }
        } catch (error) {
            console.error('设置产品名称失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH };
        }
    }
    
    // 获取产品名称
    async VikeyGetPtroductName(index) {
        try {
            this.updateActivity();
            console.log(`获取设备${index}的产品名称...`);
            
            // 模拟返回产品名称
            return { code: VikeyError.VIKEY_SUCCESS, name: 'MTSCOS系统' };
        } catch (error) {
            console.error('获取产品名称失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH, name: '' };
        }
    }
    
    // 用户登录
    async VikeyUserLogin(index, password) {
        try {
            this.updateActivity();
            console.log(`用户登录设备${index}...`);
            
            // 模拟密码验证（这里只是演示，实际应该使用安全的验证方式）
            if (password && password.length >= 6) {
                return { code: VikeyError.VIKEY_SUCCESS };
            } else {
                return { code: VikeyError.VIKEY_ERROR_INVALID_PASSWORD };
            }
        } catch (error) {
            console.error('用户登录失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH };
        }
    }
    
    // 管理员登录
    async VikeyAdminLogin(index, password) {
        try {
            this.updateActivity();
            console.log(`管理员登录设备${index}...`);
            
            // 模拟管理员密码验证
            if (password && password.length >= 8) {
                return { code: VikeyError.VIKEY_SUCCESS };
            } else {
                return { code: VikeyError.VIKEY_ERROR_INVALID_PASSWORD };
            }
        } catch (error) {
            console.error('管理员登录失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH };
        }
    }
    
    // 验证授权码
    async VikeyVerifyAuthCode(Vikey, index = 0) {
        try {
            this.updateActivity();
            console.log(`验证设备${index}的授权码...`);
            
            // 模拟授权码验证
            // 这里只是简单的模拟逻辑，实际应该实现真实的授权验证算法
            if (Vikey && Vikey.length > 0) {
                // 模拟生成一个简单的授权码进行比对
                const generatedCode = this.generateAuthToken(Vikey, `DEVICE${index}`);
                
                if (Vikey === generatedCode) {
                    return { code: VikeyError.VIKEY_SUCCESS, valid: true };
                } else {
                    return { code: VikeyError.VIKEY_ERROR_INVALID_PASSWORD, valid: false };
                }
            } else {
                return { code: VikeyError.VIKEY_ERROR_INVALID_VALUE, valid: false };
            }
        } catch (error) {
            console.error('验证授权码失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH, valid: false };
        }
    }
    
    // 生成授权令牌
    generateAuthToken(Vikey, deviceId) {
        try {
            // 模拟生成授权令牌
            // 实际应用中应该使用安全的加密算法
            const timestamp = Date.now().toString();
            const combined = `${Vikey}_${deviceId}_${timestamp}`;
            
            // 简单的模拟哈希（实际应用中应该使用安全的哈希算法）
            let hash = 0;
            for (let i = 0; i < combined.length; i++) {
                const char = combined.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash; // 转换为32位整数
            }
            
            return Math.abs(hash).toString(16).toUpperCase();
        } catch (error) {
            console.error('生成授权令牌失败:', error);
            return '';
        }
    }
    
    // 验证令牌
    async VikeyValidateToken(token) {
        try {
            this.updateActivity();
            console.log('验证令牌...');
            
            // 模拟令牌验证
            if (token && token.length >= 8) {
                return { code: VikeyError.VIKEY_SUCCESS, valid: true };
            } else {
                return { code: VikeyError.VIKEY_ERROR_INVALID_PASSWORD, valid: false };
            }
        } catch (error) {
            console.error('验证令牌失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH, valid: false };
        }
    }
    
    // 注销登录
    async VikeyLogoff(index) {
        try {
            this.updateActivity();
            console.log(`注销设备${index}的登录...`);
            
            // 模拟注销操作
            return { code: VikeyError.VIKEY_SUCCESS };
        } catch (error) {
            console.error('注销登录失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH };
        }
    }
    
    // 设置用户密码尝试次数
    async VikeySetUserPassWordAttempt(index, attempt) {
        try {
            this.updateActivity();
            console.log(`设置设备${index}的用户密码尝试次数: ${attempt}`);
            
            // 模拟设置尝试次数
            if (attempt >= 0 && attempt <= 10) {
                return { code: VikeyError.VIKEY_SUCCESS };
            } else {
                return { code: VikeyError.VIKEY_ERROR_INVALID_VALUE };
            }
        } catch (error) {
            console.error('设置密码尝试次数失败:', error);
            return { code: VikeyError.VIKEY_ERROR_CATCH };
        }
    }
    
    // 获取用户密码尝试次数
    async VikeyGetUserPassWordAttempt(index) {
        try {
            this.updateActivity();
            console.log(`获取设备${index}的用户密码尝试次数...`);
            
            // 模拟返回尝试次数
            return { code: VikeyError.VIKEY_SUCCESS, currentAttempt: 3, maxAttempt: 5 };
        } catch (error) {
            console.error('获取用户密码尝试次数失败:', error);
            return { code: VikeyError.VIKEY_ERROR_GET_VALUE, currentAttempt: 0, maxAttempt: 0 };
        }
    }
}

// 导出API
// 创建全局实例
window.VikeyAPI = new VikeyAPI();
// 暴露常量到全局
window.VikeyType = VikeyType;
window.ViKeyNoLevel = ViKeyNoLevel;
window.ViKeyUserLevel = ViKeyUserLevel;
window.ViKeyAdminLevel = ViKeyAdminLevel;
window.VikeyError = VikeyError;
window.LEDStatus = LEDStatus;