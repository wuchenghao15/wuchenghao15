/**
 * 系统设置管理核心模块
 * 统一管理所有系统配置和参数
 */

class SystemSettingsManager {
    constructor() {
        this.settings = {
            system: {
                name: 'MTSCOS安全系统',
                version: '1.0.0',
                autoLockTime: 30,
                maintenanceMode: false,
                debugMode: false
            },
            security: {
                minPasswordLength: 8,
                passwordComplexity: true,
                passwordExpiry: 90,
                loginFailLock: 5,
                accountLockTime: 30,
                ipWhitelist: false,
                sessionTimeout: 60
            },
            vikey: {
                enabled: true,
                timeout: 30,
                adminException: true,
                requireForAdmin: false,
                allowMultipleDevices: false
            },
            users: {
                defaultRole: 'USER',
                allowRegistration: false,
                requireEmailVerification: true,
                multiAdminApproval: true,
                maxLoginAttempts: 3
            },
            database: {
                type: 'IndexedDB',
                autoBackup: true,
                backupInterval: 24,
                maxBackups: 30,
                compression: true,
                encryption: true
            },
            backup: {
                autoBackup: true,
                interval: 24,
                retention: 30,
                compression: true,
                encryption: true,
                remoteBackup: false,
                remotePath: ''
            },
            logs: {
                level: 'INFO',
                retention: 30,
                maxSize: '100MB',
                rotateDaily: true,
                syncToDatabase: true,
                includeStackTrace: false
            },
            ui: {
                themeMode: 'auto',
                themeColor: '#667eea',
                language: 'zh-CN',
                animations: true,
                compactMode: false,
                showNotifications: true
            },
            advanced: {
                envSecurityScan: true,
                highRiskRegionBlock: true,
                allowAdminVikeyBypass: true,
                strictValidation: true,
                performanceMonitoring: true,
                autoCleanup: true,
                cleanupInterval: 7
            }
        };

        this.listeners = new Map();
        this.isInitialized = false;
        this.hasUnsavedChanges = false;
    }

    /**
     * 初始化设置管理器
     */
    async initialize() {
        try {
            console.log('初始化系统设置管理器...');
            
            // 加载保存的设置
            await this.loadSettings();
            
            // 验证设置完整性
            this.validateSettings();
            
            // 应用设置到系统
            await this.applySettings();
            
            // 设置自动保存
            this.setupAutoSave();
            
            this.isInitialized = true;
            console.log('系统设置管理器初始化完成');
            
            return true;
        } catch (error) {
            console.error('初始化设置管理器失败:', error);
            return false;
        }
    }

    /**
     * 加载设置数据
     */
    async loadSettings() {
        try {
            // 从localStorage加载
            const localSettings = localStorage.getItem('systemSettings');
            if (localSettings) {
                const parsed = JSON.parse(localSettings);
                this.mergeSettings(parsed);
            }

            // 从IndexedDB加载
            const dbSettings = await this.loadFromDatabase();
            if (dbSettings) {
                this.mergeSettings(dbSettings);
            }

            // 从服务器加载（如果在线）
            if (navigator.onLine) {
                try {
                    const serverSettings = await this.loadFromServer();
                    if (serverSettings) {
                        this.mergeSettings(serverSettings);
                    }
                } catch (error) {
                    console.warn('从服务器加载设置失败:', error);
                }
            }

            console.log('设置数据加载完成');
        } catch (error) {
            console.error('加载设置失败:', error);
            throw error;
        }
    }

    /**
     * 合并设置数据
     */
    mergeSettings(newSettings) {
        const mergeDeep = (target, source) => {
            for (const key in source) {
                if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                    target[key] = target[key] || {};
                    mergeDeep(target[key], source[key]);
                } else {
                    target[key] = source[key];
                }
            }
        };

        mergeDeep(this.settings, newSettings);
    }

    /**
     * 从数据库加载设置
     */
    async loadFromDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('MTSCOS_Settings', 1);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                const db = request.result;
                const transaction = db.transaction(['settings'], 'readonly');
                const store = transaction.objectStore('settings');
                const getRequest = store.get('system_settings');

                getRequest.onerror = () => reject(getRequest.error);
                getRequest.onsuccess = () => resolve(getRequest.result?.data);
            };

            request.onupgradeneeded = () => {
                const db = request.result;
                if (!db.objectStoreNames.contains('settings')) {
                    db.createObjectStore('settings');
                }
            };
        });
    }

    /**
     * 从服务器加载设置
     */
    async loadFromServer() {
        try {
            const response = await fetch('/api/settings', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.warn('服务器设置加载失败:', error);
        }
        return null;
    }

    /**
     * 验证设置完整性
     */
    validateSettings() {
        const validators = {
            system: {
                name: (value) => typeof value === 'string' && value.length > 0,
                autoLockTime: (value) => Number.isInteger(value) && value >= 1 && value <= 240,
                maintenanceMode: (value) => typeof value === 'boolean'
            },
            security: {
                minPasswordLength: (value) => Number.isInteger(value) && value >= 6 && value <= 32,
                passwordComplexity: (value) => typeof value === 'boolean',
                loginFailLock: (value) => Number.isInteger(value) && value >= 3 && value <= 10
            },
            vikey: {
                timeout: (value) => Number.isInteger(value) && value >= 10 && value <= 120,
                enabled: (value) => typeof value === 'boolean'
            }
            // 添加更多验证规则...
        };

        let isValid = true;
        const errors = [];

        for (const [category, rules] of Object.entries(validators)) {
            if (!this.settings[category]) continue;

            for (const [key, validator] of Object.entries(rules)) {
                if (this.settings[category][key] !== undefined && !validator(this.settings[category][key])) {
                    isValid = false;
                    errors.push(`Invalid ${category}.${key}: ${this.settings[category][key]}`);
                }
            }
        }

        if (!isValid) {
            console.error('设置验证失败:', errors);
            // 使用默认值修复无效设置
            this.fixInvalidSettings();
        }

        return isValid;
    }

    /**
     * 修复无效设置
     */
    fixInvalidSettings() {
        const defaults = {
            system: {
                name: 'MTSCOS安全系统',
                autoLockTime: 30,
                maintenanceMode: false
            },
            security: {
                minPasswordLength: 8,
                passwordComplexity: true,
                loginFailLock: 5
            },
            vikey: {
                timeout: 30,
                enabled: true
            }
        };

        for (const [category, defaultValues] of Object.entries(defaults)) {
            if (!this.settings[category]) {
                this.settings[category] = {};
            }

            for (const [key, defaultValue] of Object.entries(defaultValues)) {
                if (this.settings[category][key] === undefined || 
                    (typeof defaultValue === 'number' && !Number.isInteger(this.settings[category][key])) ||
                    (typeof defaultValue === 'boolean' && typeof this.settings[category][key] !== 'boolean')) {
                    this.settings[category][key] = defaultValue;
                    console.log(`修复设置: ${category}.${key} = ${defaultValue}`);
                }
            }
        }
    }

    /**
     * 应用设置到系统
     */
    async applySettings() {
        try {
            // 应用UI主题设置
            this.applyThemeSettings();
            
            // 应用安全设置
            this.applySecuritySettings();
            
            // 应用Vikey设置
            this.applyVikeySettings();
            
            // 应用其他设置...
            
            console.log('设置应用完成');
        } catch (error) {
            console.error('应用设置失败:', error);
            throw error;
        }
    }

    /**
     * 应用主题设置
     */
    applyThemeSettings() {
        const { themeMode, themeColor } = this.settings.ui;
        
        // 设置主题模式
        if (themeMode === 'dark') {
            document.body.classList.add('dark-theme');
        } else if (themeMode === 'light') {
            document.body.classList.remove('dark-theme');
        } else {
            // 跟随系统
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                document.body.classList.add('dark-theme');
            } else {
                document.body.classList.remove('dark-theme');
            }
        }

        // 设置主题颜色
        if (themeColor) {
            document.documentElement.style.setProperty('--primary-color', themeColor);
        }
    }

    /**
     * 应用安全设置
     */
    applySecuritySettings() {
        const { sessionTimeout, loginFailLock } = this.settings.security;
        
        // 设置会话超时
        if (sessionTimeout && window.sessionManager) {
            window.sessionManager.setTimeout(sessionTimeout * 60 * 1000);
        }

        // 设置登录失败锁定
        if (loginFailLock && window.loginManager) {
            window.loginManager.setMaxAttempts(loginFailLock);
        }
    }

    /**
     * 应用Vikey设置
     */
    applyVikeySettings() {
        const { enabled, timeout, adminException } = this.settings.vikey;
        
        if (window.vikeyManager) {
            window.vikeyManager.setEnabled(enabled);
            window.vikeyManager.setTimeout(timeout * 1000);
            window.vikeyManager.setAdminException(adminException);
        }
    }

    /**
     * 设置自动保存
     */
    setupAutoSave() {
        // 监听设置变化
        this.addEventListener('settingsChanged', () => {
            this.hasUnsavedChanges = true;
            
            // 延迟自动保存
            clearTimeout(this.autoSaveTimer);
            this.autoSaveTimer = setTimeout(() => {
                this.saveSettings();
            }, 2000);
        });
    }

    /**
     * 保存设置
     */
    async saveSettings() {
        try {
            console.log('保存系统设置...');
            
            // 更新时间戳
            this.settings.lastUpdated = new Date().toISOString();
            this.settings.lastUpdatedBy = this.getCurrentUser();

            // 保存到localStorage
            localStorage.setItem('systemSettings', JSON.stringify(this.settings));

            // 保存到IndexedDB
            await this.saveToDatabase();

            // 保存到服务器
            if (navigator.onLine) {
                try {
                    await this.saveToServer();
                } catch (error) {
                    console.warn('保存到服务器失败:', error);
                }
            }

            this.hasUnsavedChanges = false;
            this.emitEvent('settingsSaved', this.settings);
            
            console.log('设置保存完成');
            return true;
        } catch (error) {
            console.error('保存设置失败:', error);
            this.emitEvent('settingsSaveError', error);
            return false;
        }
    }

    /**
     * 保存到数据库
     */
    async saveToDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('MTSCOS_Settings', 1);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                const db = request.result;
                const transaction = db.transaction(['settings'], 'readwrite');
                const store = transaction.objectStore('settings');
                
                const putRequest = store.put({
                    id: 'system_settings',
                    data: this.settings,
                    timestamp: new Date().toISOString()
                });

                putRequest.onerror = () => reject(putRequest.error);
                putRequest.onsuccess = () => resolve();
            };
        });
    }

    /**
     * 保存到服务器
     */
    async saveToServer() {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getAuthToken()}`
            },
            body: JSON.stringify(this.settings)
        });

        if (!response.ok) {
            throw new Error(`保存失败: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * 获取设置值
     */
    get(category, key, defaultValue = null) {
        try {
            const keys = key.split('.');
            let value = this.settings[category];
            
            for (const k of keys) {
                if (value && typeof value === 'object' && k in value) {
                    value = value[k];
                } else {
                    return defaultValue;
                }
            }
            
            return value;
        } catch (error) {
            console.error(`获取设置失败 ${category}.${key}:`, error);
            return defaultValue;
        }
    }

    /**
     * 设置值
     */
    set(category, key, value) {
        try {
            const keys = key.split('.');
            let target = this.settings[category];
            
            if (!target) {
                this.settings[category] = {};
                target = this.settings[category];
            }
            
            for (let i = 0; i < keys.length - 1; i++) {
                const k = keys[i];
                if (!target[k] || typeof target[k] !== 'object') {
                    target[k] = {};
                }
                target = target[k];
            }
            
            const lastKey = keys[keys.length - 1];
            const oldValue = target[lastKey];
            target[lastKey] = value;
            
            // 触发变化事件
            this.emitEvent('settingsChanged', {
                category,
                key,
                oldValue,
                newValue: value
            });
            
            return true;
        } catch (error) {
            console.error(`设置值失败 ${category}.${key}:`, error);
            return false;
        }
    }

    /**
     * 重置设置
     */
    async reset(category = null) {
        try {
            if (category) {
                // 重置特定类别
                const defaults = this.getDefaultSettings();
                if (defaults[category]) {
                    this.settings[category] = { ...defaults[category] };
                }
            } else {
                // 重置所有设置
                this.settings = this.getDefaultSettings();
            }

            await this.saveSettings();
            await this.applySettings();
            
            this.emitEvent('settingsReset', { category });
            return true;
        } catch (error) {
            console.error('重置设置失败:', error);
            return false;
        }
    }

    /**
     * 获取默认设置
     */
    getDefaultSettings() {
        return {
            system: {
                name: 'MTSCOS安全系统',
                version: '1.0.0',
                autoLockTime: 30,
                maintenanceMode: false,
                debugMode: false
            },
            security: {
                minPasswordLength: 8,
                passwordComplexity: true,
                passwordExpiry: 90,
                loginFailLock: 5,
                accountLockTime: 30,
                ipWhitelist: false,
                sessionTimeout: 60
            },
            vikey: {
                enabled: true,
                timeout: 30,
                adminException: true,
                requireForAdmin: false,
                allowMultipleDevices: false
            },
            // ... 其他默认设置
        };
    }

    /**
     * 导出设置
     */
    exportSettings() {
        const exportData = {
            settings: this.settings,
            exportTime: new Date().toISOString(),
            version: this.settings.system.version,
            systemInfo: {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language
            }
        };

        return JSON.stringify(exportData, null, 2);
    }

    /**
     * 导入设置
     */
    async importSettings(importData) {
        try {
            let data;
            
            if (typeof importData === 'string') {
                data = JSON.parse(importData);
            } else {
                data = importData;
            }

            // 验证导入数据
            if (!data.settings) {
                throw new Error('无效的导入数据格式');
            }

            // 合并设置
            this.mergeSettings(data.settings);
            
            // 验证和修复
            this.validateSettings();
            
            // 保存和应用
            await this.saveSettings();
            await this.applySettings();
            
            this.emitEvent('settingsImported', data);
            return true;
        } catch (error) {
            console.error('导入设置失败:', error);
            throw error;
        }
    }

    /**
     * 添加事件监听器
     */
    addEventListener(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    /**
     * 移除事件监听器
     */
    removeEventListener(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    /**
     * 触发事件
     */
    emitEvent(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`事件处理器错误 (${event}):`, error);
                }
            });
        }
    }

    /**
     * 获取当前用户
     */
    getCurrentUser() {
        // 从会话管理器获取当前用户
        if (window.sessionManager && window.sessionManager.getCurrentUser) {
            return window.sessionManager.getCurrentUser();
        }
        return 'system';
    }

    /**
     * 获取认证令牌
     */
    getAuthToken() {
        // 从会话管理器获取认证令牌
        if (window.sessionManager && window.sessionManager.getAuthToken) {
            return window.sessionManager.getAuthToken();
        }
        return localStorage.getItem('authToken');
    }

    /**
     * 销毁管理器
     */
    destroy() {
        clearTimeout(this.autoSaveTimer);
        this.listeners.clear();
        this.isInitialized = false;
    }
}

// 创建全局实例
window.systemSettings = new SystemSettingsManager();

// 自动初始化
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await window.systemSettings.initialize();
        console.log('系统设置管理器已准备就绪');
    } catch (error) {
        console.error('系统设置管理器初始化失败:', error);
    }
});

// 导出类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SystemSettingsManager;
}