// HardwareKey 配置文件
// 版本: 1.0
// 最后更新: 2025-11-24

const hardwareKey_config = {
    // 硬件密钥类型配置
    deviceTypes: {
        APP: 0,              // 应用型加密狗
        STD: 1,              // 标准型加密狗
        NET: 2,              // 网络型加密狗
        PRO: 3,              // 专业型加密狗
        WEB: 4,              // 网页验证型加密狗
        TIME: 5              // 时间型加密狗
    },
    
    // WebSocket 配置
    webSocket: {
        url: 'ws://localhost:8765',  // WebSocket 服务器地址
        reconnectInterval: 3000,     // 重连间隔 (毫秒)
        maxReconnectAttempts: 5      // 最大重连尝试次数
    },
    
    // 认证配置
    authentication: {
        timeout: 10000,              // 认证超时时间 (毫秒)
        retryAttempts: 3,            // 认证重试次数
        maxSignatureLength: 1024     // 最大签名长度
    },
    
    // 设备检测配置
    deviceDetection: {
        scanInterval: 2000,          // 设备扫描间隔 (毫秒)
        maxDevices: 10,              // 最大支持设备数
        detectionTimeout: 5000       // 设备检测超时时间 (毫秒)
    },
    
    // 加密配置
    encryption: {
        algorithm: 'AES-256-CBC',    // 加密算法
        keyLength: 32,               // 密钥长度 (字节)
        ivLength: 16,                // 初始向量长度 (字节)
        padding: 'PKCS5Padding'      // 填充方式
    },
    
    // 日志配置
    logging: {
        enabled: true,               // 是否启用日志
        level: 'INFO',               // 日志级别 (DEBUG, INFO, WARN, ERROR)
        maxLogSize: 1024 * 1024      // 最大日志大小 (字节)
    },
    
    // 应用配置
    application: {
        name: 'MTSCOS',              // 应用名称
        version: '1.0.0',            // 应用版本
        vendor: 'MTSCOS Team',       // 应用供应商
        productId: 'MTSCOS-001'      // 产品 ID
    },
    
    // 兼容性配置
    compatibility: {
        legacyMode: false,           // 是否启用遗留模式
        viKeyCompatibility: true,    // 是否兼容 ViKey API
        autoDetect: true             // 是否自动检测兼容性
    },
    
    // 安全配置
    security: {
        antiReplay: true,            // 是否启用防重放攻击
        integrityCheck: true,        // 是否启用完整性检查
        secureMode: true             // 是否启用安全模式
    }
};

// 导出配置 (如果支持 ES6 模块)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = hardwareKey_config;
}