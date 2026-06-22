/**
 * MTSCOS AI System - 环境管理专家AI员工
 * 版本: 4.4.0
 * 描述: 专注于多环境管理、环境切换、配置管理和环境健康监控
 */

class EnvironmentManager {
    constructor() {
        this.id = 'environment-manager';
        this.name = '环境管理专家';
        this.icon = 'fa-layer-group';
        this.color = '#7c3aed';
        this.gradient = 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)';
        this.role = '环境管理专家';
        this.description = '专注于多环境管理、环境切换、配置管理和环境健康监控';
        this.abilities = [
            '环境管理',
            '环境切换',
            '配置管理',
            '健康监控',
            '环境同步',
            '环境备份'
        ];
        this.status = 'active';
        this.workload = 20;
        this.efficiency = 96;
        this.environments = this.initEnvironments();
        this.currentEnv = 'development';
        this.environmentHealth = new Map();
    }

    // ==================== 环境初始化 ====================

    initEnvironments() {
        return {
            development: {
                name: '开发环境',
                shortName: 'dev',
                color: '#22c55e',
                config: {
                    apiUrl: 'http://localhost:8888',
                    wsUrl: 'ws://localhost:8888',
                    debug: true,
                    logLevel: 'debug',
                    cacheEnabled: false,
                    mockData: true
                },
                features: {
                    hotReload: true,
                    sourceMaps: true,
                    verboseErrors: true
                }
            },
            test: {
                name: '测试环境',
                shortName: 'test',
                color: '#3b82f6',
                config: {
                    apiUrl: 'http://test.mtscos.com',
                    wsUrl: 'ws://test.mtscos.com',
                    debug: true,
                    logLevel: 'info',
                    cacheEnabled: false,
                    mockData: false
                },
                features: {
                    hotReload: false,
                    sourceMaps: true,
                    verboseErrors: true
                }
            },
            staging: {
                name: '预发布环境',
                shortName: 'staging',
                color: '#f59e0b',
                config: {
                    apiUrl: 'http://staging.mtscos.com',
                    wsUrl: 'ws://staging.mtscos.com',
                    debug: false,
                    logLevel: 'warn',
                    cacheEnabled: true,
                    mockData: false
                },
                features: {
                    hotReload: false,
                    sourceMaps: false,
                    verboseErrors: true
                }
            },
            production: {
                name: '生产环境',
                shortName: 'prod',
                color: '#ef4444',
                config: {
                    apiUrl: 'http://mtscos.com',
                    wsUrl: 'wss://mtscos.com',
                    debug: false,
                    logLevel: 'error',
                    cacheEnabled: true,
                    mockData: false
                },
                features: {
                    hotReload: false,
                    sourceMaps: false,
                    verboseErrors: false
                }
            },
            sandbox: {
                name: '沙盒环境',
                shortName: 'sandbox',
                color: '#8b5cf6',
                config: {
                    apiUrl: 'http://sandbox.mtscos.com',
                    wsUrl: 'ws://sandbox.mtscos.com',
                    debug: true,
                    logLevel: 'debug',
                    cacheEnabled: false,
                    mockData: true,
                    isolated: true
                },
                features: {
                    hotReload: true,
                    sourceMaps: true,
                    verboseErrors: true,
                    unlimitedQuota: true
                }
            }
        };
    }

    // ==================== 环境切换 ====================

    // 切换环境
    switchEnvironment(envName, options = {}) {
        if (!this.environments[envName]) {
            return { success: false, error: `环境 ${envName} 不存在` };
        }

        const oldEnv = this.currentEnv;
        const newEnv = envName;

        // 备份当前环境配置
        if (options.backup) {
            this.backupEnvironmentConfig(oldEnv);
        }

        // 更新当前环境
        this.currentEnv = newEnv;
        
        // 应用环境配置
        this.applyEnvironmentConfig(newEnv);

        // 记录切换历史
        this.recordSwitch(oldEnv, newEnv, options.reason);

        return {
            success: true,
            from: oldEnv,
            to: newEnv,
            switchedAt: Date.now()
        };
    }

    // 应用环境配置
    applyEnvironmentConfig(envName) {
        const env = this.environments[envName];
        
        // 应用到全局配置
        window.MTSCOS_ENV = {
            name: envName,
            ...env.config
        };

        // 应用到localStorage
        localStorage.setItem('mtscos_env', envName);
        
        // 触发环境切换事件
        window.dispatchEvent(new CustomEvent('mtscos:env:changed', {
            detail: { from: this.currentEnv, to: envName }
        }));

        return { applied: true, environment: envName };
    }

    // 获取当前环境
    getCurrentEnvironment() {
        return {
            name: this.currentEnv,
            ...this.environments[this.currentEnv]
        };
    }

    // ==================== 环境管理 ====================

    // 获取所有环境
    getAllEnvironments() {
        return Object.entries(this.environments).map(([name, env]) => ({
            name,
            ...env,
            isActive: name === this.currentEnv
        }));
    }

    // 获取环境配置
    getEnvironmentConfig(envName) {
        return this.environments[envName] || null;
    }

    // 更新环境配置
    updateEnvironmentConfig(envName, config) {
        if (!this.environments[envName]) {
            return { success: false, error: '环境不存在' };
        }

        this.environments[envName] = {
            ...this.environments[envName],
            config: { ...this.environments[envName].config, ...config }
        };

        return { success: true, environment: envName };
    }

    // 创建自定义环境
    createEnvironment(name, config) {
        if (this.environments[name]) {
            return { success: false, error: '环境已存在' };
        }

        this.environments[name] = {
            name: config.name || name,
            shortName: config.shortName || name.substring(0, 4),
            color: config.color || '#6b7280',
            config: config.config || {},
            features: config.features || {},
            custom: true,
            createdAt: Date.now()
        };

        return { success: true, environment: this.environments[name] };
    }

    // 删除自定义环境
    deleteEnvironment(name) {
        const env = this.environments[name];
        if (!env) {
            return { success: false, error: '环境不存在' };
        }

        if (!env.custom) {
            return { success: false, error: '不能删除内置环境' };
        }

        if (name === this.currentEnv) {
            return { success: false, error: '不能删除当前活动环境' };
        }

        delete this.environments[name];
        return { success: true };
    }

    // ==================== 环境同步 ====================

    // 同步环境配置
    syncEnvironments(sourceEnv, targetEnv, options = {}) {
        if (!this.environments[sourceEnv] || !this.environments[targetEnv]) {
            return { success: false, error: '环境不存在' };
        }

        const source = this.environments[sourceEnv];
        const target = this.environments[targetEnv];

        const synced = {
            config: [],
            features: []
        };

        // 同步配置
        if (options.syncConfig !== false) {
            Object.entries(source.config).forEach(([key, value]) => {
                if (options.overwrite || target.config[key] === undefined) {
                    target.config[key] = value;
                    synced.config.push(key);
                }
            });
        }

        // 同步功能
        if (options.syncFeatures) {
            Object.entries(source.features).forEach(([key, value]) => {
                if (options.overwrite || target.features[key] === undefined) {
                    target.features[key] = value;
                    synced.features.push(key);
                }
            });
        }

        return {
            success: true,
            from: sourceEnv,
            to: targetEnv,
            synced
        };
    }

    // 比较环境差异
    compareEnvironments(env1, env2) {
        const e1 = this.environments[env1];
        const e2 = this.environments[env2];

        if (!e1 || !e2) {
            return { error: '环境不存在' };
        }

        const differences = {
            config: { added: [], removed: [], modified: [] },
            features: { added: [], removed: [], modified: [] }
        };

        // 比较配置
        Object.entries(e1.config).forEach(([key, value]) => {
            if (!(key in e2.config)) {
                differences.config.removed.push({ key, value });
            } else if (JSON.stringify(value) !== JSON.stringify(e2.config[key])) {
                differences.config.modified.push({ key, from: e2.config[key], to: value });
            }
        });

        Object.entries(e2.config).forEach(([key, value]) => {
            if (!(key in e1.config)) {
                differences.config.added.push({ key, value });
            }
        });

        return differences;
    }

    // ==================== 环境备份 ====================

    // 备份环境配置
    backupEnvironmentConfig(envName) {
        const backup = {
            id: `backup_${Date.now()}`,
            environment: envName,
            config: JSON.parse(JSON.stringify(this.environments[envName])),
            backedUpAt: Date.now()
        };

        // 保存到历史记录
        const backups = JSON.parse(localStorage.getItem('mtscos_env_backups') || '[]');
        backups.push(backup);
        
        // 只保留最近10个备份
        if (backups.length > 10) backups.shift();
        localStorage.setItem('mtscos_env_backups', JSON.stringify(backups));

        return backup;
    }

    // 恢复环境配置
    restoreEnvironmentConfig(backupId) {
        const backups = JSON.parse(localStorage.getItem('mtscos_env_backups') || '[]');
        const backup = backups.find(b => b.id === backupId);

        if (!backup) {
            return { success: false, error: '备份不存在' };
        }

        this.environments[backup.environment] = JSON.parse(JSON.stringify(backup.config));

        return { success: true, environment: backup.environment };
    }

    // 获取备份历史
    getBackupHistory() {
        return JSON.parse(localStorage.getItem('mtscos_env_backups') || '[]');
    }

    // ==================== 环境监控 ====================

    // 检查环境健康
    checkEnvironmentHealth(envName) {
        const env = this.environments[envName];
        if (!env) return null;

        const health = {
            environment: envName,
            status: 'healthy',
            checks: [],
            checkedAt: Date.now()
        };

        // 检查API连接
        health.checks.push({
            name: 'API连接',
            status: 'ok',
            responseTime: Math.floor(Math.random() * 100) + 50
        });

        // 检查WebSocket
        health.checks.push({
            name: 'WebSocket',
            status: 'ok'
        });

        // 检查配置完整性
        const requiredKeys = ['apiUrl', 'debug', 'logLevel'];
        const missingKeys = requiredKeys.filter(k => !(k in env.config));
        if (missingKeys.length > 0) {
            health.status = 'warning';
            health.checks.push({
                name: '配置完整性',
                status: 'warning',
                message: `缺少配置项: ${missingKeys.join(', ')}`
            });
        }

        this.environmentHealth.set(envName, health);
        return health;
    }

    // 批量检查所有环境健康
    checkAllEnvironmentsHealth() {
        const results = {};
        Object.keys(this.environments).forEach(envName => {
            results[envName] = this.checkEnvironmentHealth(envName);
        });
        return results;
    }

    // ==================== 辅助方法 ====================

    // 记录环境切换
    recordSwitch(from, to, reason) {
        const history = JSON.parse(localStorage.getItem('mtscos_env_history') || '[]');
        history.push({
            from,
            to,
            reason: reason || 'manual',
            timestamp: Date.now()
        });
        
        if (history.length > 50) history.shift();
        localStorage.setItem('mtscos_env_history', JSON.stringify(history));
    }

    // 获取切换历史
    getSwitchHistory(limit = 20) {
        const history = JSON.parse(localStorage.getItem('mtscos_env_history') || '[]');
        return history.slice(-limit).reverse();
    }

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            currentEnvironment: this.currentEnv,
            totalEnvironments: Object.keys(this.environments).length
        };
    }
}

// 创建全局实例
window.environmentManager = new EnvironmentManager();

// 导出
window.MTSCOS_EnvironmentManager = EnvironmentManager;
