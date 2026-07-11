/**
 * MTSCOS AI System - 参数存储管理师AI员工
 * 版本: 4.4.0
 * 描述: 专注于参数存储管理、参数验证、参数生命周期管理和跨模块参数共享
 */

class ParameterStorageManager {
    constructor() {
        this.id = 'parameter-storage-manager';
        this.name = '参数存储管理师';
        this.icon = 'fa-database';
        this.color = '#0284c7';
        this.gradient = 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)';
        this.role = '参数存储专家';
        this.description = '专注于参数存储、参数验证、生命周期管理和跨模块共享';
        this.abilities = [
            '参数存储',
            '参数验证',
            '参数共享',
            '生命周期管理',
            '参数模板',
            '参数迁移'
        ];
        this.status = 'active';
        this.workload = 15;
        this.efficiency = 98;
        this.parameters = new Map();
        this.templates = new Map();
        this.listeners = new Map();
    }

    // ==================== 参数存储 ====================

    // 存储参数
    store(config) {
        const param = {
            id: config.id || `param_${Date.now()}`,
            key: config.key,
            value: config.value,
            type: config.type || this.inferType(config.value),
            category: config.category || 'general',
            metadata: {
                description: config.description || '',
                unit: config.unit || null,
                min: config.min ?? null,
                max: config.max ?? null,
                default: config.default ?? config.value,
                options: config.options || null
            },
            validation: {
                required: config.required ?? false,
                pattern: config.pattern || null,
                custom: config.validator || null
            },
            lifecycle: {
                createdAt: Date.now(),
                updatedAt: Date.now(),
                version: 1,
                expiresAt: config.expiresAt || null,
                deprecated: false
            },
            access: {
                readable: config.readable ?? true,
                writable: config.writable ?? true,
                scope: config.scope || 'private' // private, shared, public
            }
        };

        // 验证参数
        const validation = this.validate(param);
        if (!validation.valid) {
            return { success: false, error: validation.error };
        }

        this.parameters.set(param.key, param);
        this.notifyListeners(param.key, 'store', param.value);

        return { success: true, param };
    }

    // 推断类型
    inferType(value) {
        if (typeof value === 'boolean') return 'boolean';
        if (typeof value === 'number') return Number.isInteger(value) ? 'integer' : 'float';
        if (Array.isArray(value)) return 'array';
        if (typeof value === 'object' && value !== null) return 'object';
        return 'string';
    }

    // 批量存储
    batchStore(params) {
        const results = { success: 0, failed: 0, errors: [] };

        params.forEach(param => {
            const result = this.store(param);
            if (result.success) {
                results.success++;
            } else {
                results.failed++;
                results.errors.push({ key: param.key, error: result.error });
            }
        });

        return results;
    }

    // 获取参数
    get(key, options = {}) {
        const param = this.parameters.get(key);

        if (!param) {
            if (options.required) {
                throw new Error(`参数 ${key} 不存在`);
            }
            return options.default ?? null;
        }

        // 检查过期
        if (param.lifecycle.expiresAt && Date.now() > param.lifecycle.expiresAt) {
            if (options.autoDelete) {
                this.delete(key);
            }
            return options.default ?? null;
        }

        // 检查废弃
        if (param.lifecycle.deprecated && !options.includeDeprecated) {
            console.warn(`参数 ${key} 已废弃`);
        }

        return options.raw ? param : param.value;
    }

    // 获取多个参数
    getMultiple(keys) {
        const results = {};
        keys.forEach(key => {
            results[key] = this.get(key);
        });
        return results;
    }

    // 获取分类参数
    getByCategory(category) {
        const params = [];
        this.parameters.forEach((param, key) => {
            if (param.category === category) {
                params.push({ key, ...param });
            }
        });
        return params;
    }

    // ==================== 参数更新 ====================

    // 更新参数
    update(key, value, options = {}) {
        const param = this.parameters.get(key);

        if (!param) {
            return { success: false, error: '参数不存在' };
        }

        if (!param.access.writable) {
            return { success: false, error: '参数不可写' };
        }

        // 验证新值
        const oldValue = param.value;
        param.value = value;
        const validation = this.validate(param);

        if (!validation.valid) {
            param.value = oldValue;
            return { success: false, error: validation.error };
        }

        // 更新元数据
        param.lifecycle.updatedAt = Date.now();
        param.lifecycle.version++;

        this.notifyListeners(key, 'update', value, oldValue);

        return { success: true, param };
    }

    // 删除参数
    delete(key, options = {}) {
        const param = this.parameters.get(key);

        if (!param) {
            return { success: false, error: '参数不存在' };
        }

        if (!param.access.writable) {
            return { success: false, error: '参数不可删除' };
        }

        this.parameters.delete(key);
        this.notifyListeners(key, 'delete', null, param.value);

        if (options.archive) {
            param.deletedAt = Date.now();
            param.deletedBy = options.deletedBy || 'system';
        }

        return { success: true };
    }

    // 批量删除
    batchDelete(keys) {
        const results = { success: 0, failed: 0, errors: [] };

        keys.forEach(key => {
            const result = this.delete(key);
            if (result.success) {
                results.success++;
            } else {
                results.failed++;
                results.errors.push({ key, error: result.error });
            }
        });

        return results;
    }

    // ==================== 参数验证 ====================

    // 验证参数
    validate(param) {
        const { value, type, metadata, validation } = param;

        // 必填验证
        if (validation.required && (value === undefined || value === null || value === '')) {
            return { valid: false, error: '参数不能为空' };
        }

        // 类型验证
        if (value !== undefined && value !== null) {
            const actualType = this.inferType(value);
            if (actualType !== type) {
                return { valid: false, error: `类型错误: 期望 ${type}, 实际 ${actualType}` };
            }
        }

        // 范围验证
        if (typeof value === 'number') {
            if (metadata.min !== null && value < metadata.min) {
                return { valid: false, error: `值不能小于 ${metadata.min}` };
            }
            if (metadata.max !== null && value > metadata.max) {
                return { valid: false, error: `值不能大于 ${metadata.max}` };
            }
        }

        // 选项验证
        if (metadata.options && !metadata.options.includes(value)) {
            return { valid: false, error: `值必须是 ${metadata.options.join(', ')} 之一` };
        }

        // 正则验证
        if (validation.pattern && typeof value === 'string') {
            const regex = new RegExp(validation.pattern);
            if (!regex.test(value)) {
                return { valid: false, error: '格式不正确' };
            }
        }

        // 自定义验证
        if (validation.custom) {
            try {
                const result = validation.custom(value);
                if (result !== true) {
                    return { valid: false, error: result || '验证失败' };
                }
            } catch (error) {
                return { valid: false, error: error.message };
            }
        }

        return { valid: true };
    }

    // 批量验证
    validateAll() {
        const results = [];
        this.parameters.forEach((param, key) => {
            const validation = this.validate(param);
            results.push({ key, ...validation });
        });
        return results;
    }

    // ==================== 生命周期管理 ====================

    // 设置过期时间
    setExpiry(key, expiresAt) {
        const param = this.parameters.get(key);
        if (!param) {
            return { success: false, error: '参数不存在' };
        }

        param.lifecycle.expiresAt = expiresAt;
        param.lifecycle.updatedAt = Date.now();

        return { success: true, expiresAt };
    }

    // 废弃参数
    deprecate(key, reason = '') {
        const param = this.parameters.get(key);
        if (!param) {
            return { success: false, error: '参数不存在' };
        }

        param.lifecycle.deprecated = true;
        param.lifecycle.deprecatedAt = Date.now();
        param.lifecycle.deprecationReason = reason;
        param.lifecycle.updatedAt = Date.now();

        this.notifyListeners(key, 'deprecate', null, null, { reason });

        return { success: true };
    }

    // 清理过期参数
    cleanupExpired() {
        const now = Date.now();
        const expired = [];

        this.parameters.forEach((param, key) => {
            if (param.lifecycle.expiresAt && now > param.lifecycle.expiresAt) {
                expired.push(key);
                this.delete(key);
            }
        });

        return { deleted: expired.length, keys: expired };
    }

    // 获取生命周期信息
    getLifecycleInfo(key) {
        const param = this.parameters.get(key);
        if (!param) return null;

        return {
            createdAt: param.lifecycle.createdAt,
            updatedAt: param.lifecycle.updatedAt,
            version: param.lifecycle.version,
            expiresAt: param.lifecycle.expiresAt,
            isExpired: param.lifecycle.expiresAt ? Date.now() > param.lifecycle.expiresAt : false,
            deprecated: param.lifecycle.deprecated
        };
    }

    // ==================== 参数模板 ====================

    // 创建模板
    createTemplate(config) {
        const template = {
            id: config.id || `template_${Date.now()}`,
            name: config.name,
            description: config.description || '',
            params: config.params || [],
            createdAt: Date.now(),
            usedCount: 0
        };

        this.templates.set(template.id, template);
        return template;
    }

    // 应用模板
    applyTemplate(templateId, values = {}) {
        const template = this.templates.get(templateId);
        if (!template) {
            return { success: false, error: '模板不存在' };
        }

        const results = { success: 0, failed: 0, applied: [] };

        template.params.forEach(param => {
            const value = values[param.key] ?? param.default ?? param.value;
            const result = this.store({
                ...param,
                value
            });

            if (result.success) {
                results.success++;
                results.applied.push(param.key);
            } else {
                results.failed++;
            }
        });

        template.usedCount++;
        return results;
    }

    // 获取模板列表
    getTemplates() {
        return Array.from(this.templates.values());
    }

    // ==================== 参数监听 ====================

    // 监听参数变化
    watch(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, new Set());
        }
        this.listeners.get(key).add(callback);

        // 返回取消监听函数
        return () => {
            this.listeners.get(key)?.delete(callback);
        };
    }

    // 通知监听器
    notifyListeners(key, action, newValue, oldValue, extra = {}) {
        const callbacks = this.listeners.get(key);
        if (callbacks) {
            callbacks.forEach(callback => {
                try {
                    callback({ key, action, newValue, oldValue, ...extra });
                } catch (error) {
                    console.error(`监听器执行错误: ${error.message}`);
                }
            });
        }
    }

    // ==================== 参数导入导出 ====================

    // 导出参数
    export(params = {}, options = {}) {
        const exported = {};
        const keys = params.length ? params : Array.from(this.parameters.keys());

        keys.forEach(key => {
            const param = this.parameters.get(key);
            if (param && (!options.includePrivate || param.access.scope !== 'private')) {
                exported[key] = {
                    value: param.value,
                    type: param.type,
                    category: param.category,
                    metadata: param.metadata,
                    lifecycle: {
                        version: param.lifecycle.version,
                        createdAt: param.lifecycle.createdAt
                    }
                };
            }
        });

        return JSON.stringify({
            version: '1.0',
            exportedAt: Date.now(),
            params: exported
        }, null, 2);
    }

    // 导入参数
    import(jsonString, options = {}) {
        try {
            const data = JSON.parse(jsonString);
            const results = { success: 0, failed: 0, skipped: 0, errors: [] };

            Object.entries(data.params).forEach(([key, param]) => {
                // 检查是否覆盖
                if (options.skipExisting && this.parameters.has(key)) {
                    results.skipped++;
                    return;
                }

                const result = this.store({
                    key,
                    ...param
                });

                if (result.success) {
                    results.success++;
                } else {
                    results.failed++;
                    results.errors.push({ key, error: result.error });
                }
            });

            return results;
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // ==================== 辅助方法 ====================

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            totalParams: this.parameters.size,
            templatesCount: this.templates.size,
            listenersCount: this.listeners.size
        };
    }

    // 获取统计信息
    getStatistics() {
        const stats = {
            total: this.parameters.size,
            byType: {},
            byCategory: {},
            byScope: { private: 0, shared: 0, public: 0 },
            deprecated: 0,
            expired: 0
        };

        const now = Date.now();
        this.parameters.forEach(param => {
            stats.byType[param.type] = (stats.byType[param.type] || 0) + 1;
            stats.byCategory[param.category] = (stats.byCategory[param.category] || 0) + 1;
            stats.byScope[param.access.scope]++;
            if (param.lifecycle.deprecated) stats.deprecated++;
            if (param.lifecycle.expiresAt && now > param.lifecycle.expiresAt) stats.expired++;
        });

        return stats;
    }

    // 列出所有参数
    list(options = {}) {
        let params = Array.from(this.parameters.entries());

        if (options.category) {
            params = params.filter(([, p]) => p.category === options.category);
        }

        if (options.scope) {
            params = params.filter(([, p]) => p.access.scope === options.scope);
        }

        if (options.includeDeprecated === false) {
            params = params.filter(([, p]) => !p.lifecycle.deprecated);
        }

        if (options.search) {
            const search = options.search.toLowerCase();
            params = params.filter(([key, p]) => 
                key.toLowerCase().includes(search) ||
                p.metadata.description.toLowerCase().includes(search)
            );
        }

        return params.map(([key, param]) => ({ key, ...param }));
    }
}

// 创建全局实例
window.parameterStorageManager = new ParameterStorageManager();

// 导出
window.MTSCOS_ParameterStorageManager = ParameterStorageManager;
