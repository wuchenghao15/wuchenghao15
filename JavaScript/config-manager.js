const fs = require('fs').promises;
const path = require('path');

/**
 * 配置管理器 - 通用配置处理模块
 * 提供配置加载、合并、环境变量替换等功能
 */
class ConfigManager {
    constructor() {
        this.configs = new Map();
    }

    /**
     * 加载配置 - 支持文件路径或配置对象
     * @param {string|object} configPathOrConfig - 配置文件路径或配置对象
     * @param {object} defaultConfig - 默认配置
     * @returns {object} 合并后的配置
     */
    async loadConfig(configPathOrConfig, defaultConfig = {}) {
        let config;

        if (typeof configPathOrConfig === 'string') {
            // 从文件加载配置
            config = await this._loadConfigFromFile(configPathOrConfig);
        } else if (typeof configPathOrConfig === 'object') {
            // 使用直接传递的配置对象
            config = configPathOrConfig;
        } else {
            // 无配置情况，使用默认配置
            config = {};
        }

        // 合并配置并替换环境变量
        const mergedConfig = this._mergeConfigs(defaultConfig, config);
        return this._replaceEnvironmentVariables(mergedConfig);
    }

    /**
     * 从文件加载配置
     * @param {string} configPath - 配置文件路径
     * @returns {object} 配置对象
     * @private
     */
    async _loadConfigFromFile(configPath) {
        try {
            const fullPath = path.isAbsolute(configPath) ? configPath : path.resolve(configPath);
            const configData = await fs.readFile(fullPath, 'utf8');
            return JSON.parse(configData);
        } catch (error) {
            console.error(`Failed to load config from file: ${configPath}`, error);
            return {};
        }
    }

    /**
     * 合并配置对象
     * @param {object} defaultConfig - 默认配置
     * @param {object} userConfig - 用户配置
     * @returns {object} 合并后的配置
     * @private
     */
    _mergeConfigs(defaultConfig, userConfig) {
        // 深度合并配置对象
        const merge = (target, source) => {
            for (const key in source) {
                if (source.hasOwnProperty(key)) {
                    if (typeof source[key] === 'object' && source[key] !== null && !Array.isArray(source[key])) {
                        if (!target.hasOwnProperty(key)) {
                            target[key] = {};
                        }
                        merge(target[key], source[key]);
                    } else {
                        target[key] = source[key];
                    }
                }
            }
            return target;
        };

        return merge(JSON.parse(JSON.stringify(defaultConfig)), userConfig);
    }

    /**
     * 替换配置中的环境变量
     * @param {object} config - 配置对象
     * @returns {object} 替换后的配置
     * @private
     */
    _replaceEnvironmentVariables(config) {
        // 创建深拷贝避免修改原始配置
        const configCopy = JSON.parse(JSON.stringify(config));
        
        // 递归替换配置中的环境变量
        const replaceInValue = (value) => {
            if (typeof value === 'string') {
                // 替换 ${ENV_VAR} 格式的环境变量
                return value.replace(/\$\{([^}]+)\}/g, (match, envVar) => {
                    return process.env[envVar] || match;
                });
            } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                // 直接处理对象，避免再次调用外部方法
                const result = {};
                for (const key in value) {
                    if (Object.prototype.hasOwnProperty.call(value, key)) {
                        result[key] = replaceInValue(value[key]);
                    }
                }
                return result;
            } else if (Array.isArray(value)) {
                return value.map(item => replaceInValue(item));
            }
            return value;
        };

        return replaceInValue(configCopy);
    }

    /**
     * 保存配置到文件
     * @param {string} configPath - 配置文件路径
     * @param {object} config - 配置对象
     * @returns {Promise<void>}
     */
    async saveConfig(configPath, config) {
        try {
            const fullPath = path.isAbsolute(configPath) ? configPath : path.resolve(configPath);
            await fs.writeFile(fullPath, JSON.stringify(config, null, 2), 'utf8');
        } catch (error) {
            console.error(`Failed to save config to file: ${configPath}`, error);
            throw error;
        }
    }

    /**
     * 注册配置
     * @param {string} name - 配置名称
     * @param {object} config - 配置对象
     */
    registerConfig(name, config) {
        this.configs.set(name, config);
    }

    /**
     * 获取注册的配置
     * @param {string} name - 配置名称
     * @returns {object|null} 配置对象
     */
    getConfig(name) {
        return this.configs.get(name) || null;
    }
}

// 导出单例实例
module.exports = new ConfigManager();
