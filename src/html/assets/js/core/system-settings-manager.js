/**
 * MTSCOS AI System - 系统设置管理师AI员工
 * 版本: 4.4.0
 * 描述: 专注于系统设置管理、配置管理、参数验证和设置同步
 */

class SystemSettingsManager {
    constructor() {
        this.id = 'system-settings-manager';
        this.name = '系统设置管理师';
        this.icon = 'fa-cogs';
        this.color = '#64748b';
        this.gradient = 'linear-gradient(135deg, #64748b 0%, #475569 100%)';
        this.role = '系统设置专家';
        this.description = '专注于系统设置管理、配置验证、参数管理和跨设备同步';
        this.abilities = [
            '设置管理',
            '配置验证',
            '参数校验',
            '设置同步',
            '默认值管理',
            '设置导入导出'
        ];
        this.status = 'active';
        this.workload = 20;
        this.efficiency = 97;
        this.settingsSchema = this.initSettingsSchema();
        this.settingsCache = new Map();
    }

    // ==================== 设置架构 ====================

    initSettingsSchema() {
        return {
            general: {
                name: '通用设置',
                icon: 'fa-sliders-h',
                fields: {
                    language: { type: 'select', default: 'zh-CN', options: ['zh-CN', 'en-US', 'ja-JP'] },
                    theme: { type: 'select', default: 'auto', options: ['auto', 'light', 'dark'] },
                    timezone: { type: 'select', default: 'Asia/Shanghai', options: [] },
                    dateFormat: { type: 'select', default: 'YYYY-MM-DD', options: ['YYYY-MM-DD', 'DD/MM/YYYY', 'MM/DD/YYYY'] },
                    timeFormat: { type: 'select', default: '24h', options: ['12h', '24h'] }
                }
            },
            display: {
                name: '显示设置',
                icon: 'fa-desktop',
                fields: {
                    fontSize: { type: 'range', min: 12, max: 24, default: 14 },
                    fontFamily: { type: 'select', default: 'system-ui', options: ['system-ui', 'sans-serif', 'monospace'] },
                    density: { type: 'select', default: 'normal', options: ['compact', 'normal', 'comfortable'] },
                    animations: { type: 'boolean', default: true },
                    reducedMotion: { type: 'boolean', default: false }
                }
            },
            notification: {
                name: '通知设置',
                icon: 'fa-bell',
                fields: {
                    enabled: { type: 'boolean', default: true },
                    sound: { type: 'boolean', default: true },
                    desktop: { type: 'boolean', default: true },
                    email: { type: 'boolean', default: false },
                    frequency: { type: 'select', default: 'immediate', options: ['immediate', 'daily', 'weekly'] }
                }
            },
            privacy: {
                name: '隐私设置',
                icon: 'fa-shield-alt',
                fields: {
                    analytics: { type: 'boolean', default: false },
                    crashReports: { type: 'boolean', default: true },
                    autoLogin: { type: 'boolean', default: false },
                    rememberHistory: { type: 'boolean', default: true },
                    clearOnExit: { type: 'boolean', default: false }
                }
            },
            security: {
                name: '安全设置',
                icon: 'fa-lock',
                fields: {
                    twoFactor: { type: 'boolean', default: false },
                    sessionTimeout: { type: 'number', default: 30, min: 5, max: 1440 },
                    passwordExpiry: { type: 'number', default: 90, min: 0, max: 365 },
                    loginAlerts: { type: 'boolean', default: true },
                    encryptionLevel: { type: 'select', default: 'standard', options: ['basic', 'standard', 'high'] }
                }
            },
            performance: {
                name: '性能设置',
                icon: 'fa-tachometer-alt',
                fields: {
                    cacheSize: { type: 'number', default: 100, min: 10, max: 1000 },
                    preloadContent: { type: 'boolean', default: true },
                    lazyLoad: { type: 'boolean', default: true },
                    compression: { type: 'boolean', default: true },
                    parallelLoading: { type: 'boolean', default: true }
                }
            }
        };
    }

    // ==================== 设置管理 ====================

    // 获取所有设置
    getAllSettings() {
        const settings = {};
        Object.entries(this.settingsSchema).forEach(([category, config]) => {
            settings[category] = {};
            Object.entries(config.fields).forEach(([key, field]) => {
                settings[category][key] = field.default;
            });
        });
        return settings;
    }

    // 获取分类设置
    getCategorySettings(category) {
        const schema = this.settingsSchema[category];
        if (!schema) return null;

        const settings = {};
        Object.entries(schema.fields).forEach(([key, field]) => {
            settings[key] = localStorage.getItem(`mtscos_${category}_${key}`) ?? field.default;
        });
        return settings;
    }

    // 获取单个设置
    getSetting(category, key) {
        const schema = this.settingsSchema[category];
        if (!schema || !schema.fields[key]) return null;

        const value = localStorage.getItem(`mtscos_${category}_${key}`);
        return value !== null ? this.parseValue(value, schema.fields[key].type) : schema.fields[key].default;
    }

    // 设置值
    setSetting(category, key, value) {
        const schema = this.settingsSchema[category];
        if (!schema || !schema.fields[key]) {
            return { success: false, error: '无效的设置项' };
        }

        // 验证值
        const validation = this.validateValue(key, value, schema.fields[key]);
        if (!validation.valid) {
            return { success: false, error: validation.error };
        }

        // 保存设置
        const storageKey = `mtscos_${category}_${key}`;
        localStorage.setItem(storageKey, this.serializeValue(value, schema.fields[key].type));

        // 更新缓存
        this.settingsCache.set(`${category}_${key}`, value);

        return { success: true, key: `${category}_${key}`, value };
    }

    // 批量设置
    batchSetSettings(settings) {
        const results = { success: 0, failed: 0, errors: [] };

        Object.entries(settings).forEach(([key, value]) => {
            const [category, settingKey] = key.split('_');
            const result = this.setSetting(category, settingKey, value);
            if (result.success) {
                results.success++;
            } else {
                results.failed++;
                results.errors.push({ key, error: result.error });
            }
        });

        return results;
    }

    // ==================== 验证管理 ====================

    // 验证值
    validateValue(key, value, field) {
        switch (field.type) {
            case 'boolean':
                if (typeof value !== 'boolean') {
                    return { valid: false, error: '值必须是布尔类型' };
                }
                break;

            case 'number':
                if (typeof value !== 'number' || isNaN(value)) {
                    return { valid: false, error: '值必须是数字类型' };
                }
                if (field.min !== undefined && value < field.min) {
                    return { valid: false, error: `值不能小于 ${field.min}` };
                }
                if (field.max !== undefined && value > field.max) {
                    return { valid: false, error: `值不能大于 ${field.max}` };
                }
                break;

            case 'select':
                if (!field.options.includes(value)) {
                    return { valid: false, error: `值必须是 ${field.options.join(', ')} 之一` };
                }
                break;

            case 'string':
                if (typeof value !== 'string') {
                    return { valid: false, error: '值必须是字符串类型' };
                }
                if (field.minLength && value.length < field.minLength) {
                    return { valid: false, error: `值长度不能小于 ${field.minLength}` };
                }
                if (field.maxLength && value.length > field.maxLength) {
                    return { valid: false, error: `值长度不能大于 ${field.maxLength}` };
                }
                if (field.pattern && !field.pattern.test(value)) {
                    return { valid: false, error: '值格式不正确' };
                }
                break;
        }

        return { valid: true };
    }

    // 解析值
    parseValue(value, type) {
        switch (type) {
            case 'boolean':
                return value === 'true';
            case 'number':
                return parseFloat(value);
            default:
                return value;
        }
    }

    // 序列化值
    serializeValue(value, type) {
        if (type === 'boolean' || type === 'number') {
            return String(value);
        }
        return value;
    }

    // ==================== 设置同步 ====================

    // 导出设置
    exportSettings(config = {}) {
        const exportData = {
            version: '1.0',
            exportedAt: Date.now(),
            settings: {}
        };

        // 按类别导出
        if (config.categories && config.categories.length > 0) {
            config.categories.forEach(category => {
                exportData.settings[category] = this.getCategorySettings(category);
            });
        } else {
            exportData.settings = this.getAllSettings();
        }

        // 应用过滤器
        if (config.include && config.include.length > 0) {
            const filtered = {};
            Object.entries(exportData.settings).forEach(([category, fields]) => {
                filtered[category] = {};
                config.include.forEach(key => {
                    if (fields[key] !== undefined) {
                        filtered[category][key] = fields[key];
                    }
                });
            });
            exportData.settings = filtered;
        }

        // 应用加密
        if (config.encrypt) {
            exportData.encrypted = true;
            exportData.data = btoa(JSON.stringify(exportData.settings));
            exportData.settings = undefined;
        }

        return JSON.stringify(exportData, null, 2);
    }

    // 导入设置
    importSettings(jsonString, options = {}) {
        try {
            const importData = JSON.parse(jsonString);

            // 解密
            if (importData.encrypted && importData.data) {
                importData.settings = JSON.parse(atob(importData.data));
            }

            // 验证版本
            if (importData.version !== '1.0') {
                return { success: false, error: '不支持的设置版本' };
            }

            const results = { success: 0, failed: 0, skipped: 0, errors: [] };

            // 导入设置
            Object.entries(importData.settings).forEach(([category, fields]) => {
                Object.entries(fields).forEach(([key, value]) => {
                    // 检查是否覆盖
                    if (options.skipExisting) {
                        const existing = this.getSetting(category, key);
                        if (existing !== null) {
                            results.skipped++;
                            return;
                        }
                    }

                    const result = this.setSetting(category, key, value);
                    if (result.success) {
                        results.success++;
                    } else {
                        results.failed++;
                        results.errors.push({ key: `${category}_${key}`, error: result.error });
                    }
                });
            });

            return results;
        } catch (error) {
            return { success: false, error: `导入失败: ${error.message}` };
        }
    }

    // 同步到服务器
    async syncToServer(serverUrl) {
        try {
            const settings = this.getAllSettings();
            const response = await fetch(serverUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });

            if (!response.ok) {
                throw new Error(`服务器返回错误: ${response.status}`);
            }

            return { success: true, syncedAt: Date.now() };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // 从服务器同步
    async syncFromServer(serverUrl) {
        try {
            const response = await fetch(serverUrl);
            if (!response.ok) {
                throw new Error(`服务器返回错误: ${response.status}`);
            }

            const settings = await response.json();
            const results = this.batchSetSettings(settings);

            return { success: true, results, syncedAt: Date.now() };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // ==================== 默认值管理 ====================

    // 重置为默认值
    resetToDefaults(category = null) {
        if (category) {
            const schema = this.settingsSchema[category];
            if (!schema) return { success: false, error: '无效的类别' };

            Object.entries(schema.fields).forEach(([key, field]) => {
                localStorage.setItem(`mtscos_${category}_${key}`, this.serializeValue(field.default, field.type));
            });

            return { success: true, category };
        } else {
            Object.entries(this.settingsSchema).forEach(([cat, config]) => {
                Object.entries(config.fields).forEach(([key, field]) => {
                    localStorage.setItem(`mtscos_${cat}_${key}`, this.serializeValue(field.default, field.type));
                });
            });

            return { success: true, reset: 'all' };
        }
    }

    // 获取默认值
    getDefaultValue(category, key) {
        const schema = this.settingsSchema[category];
        return schema?.fields[key]?.default ?? null;
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            categories: Object.keys(this.settingsSchema).length
        };
    }

    // 获取设置架构
    getSettingsSchema() {
        return this.settingsSchema;
    }

    // 检查是否有未保存更改
    hasUnsavedChanges() {
        return this.settingsCache.size > 0;
    }
}

// 创建全局实例
window.systemSettingsManager = new SystemSettingsManager();

// 导出
window.MTSCOS_SystemSettingsManager = SystemSettingsManager;
