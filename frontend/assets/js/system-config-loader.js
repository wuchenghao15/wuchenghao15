/**
 * MTSCOS AI 前端配置加载器
 * System Configuration Loader for Frontend
 */

class SystemConfigLoader {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5分钟缓存
        this.cacheTimestamp = new Map();
        this.useFallback = true; // 是否使用备用配置（当API不可用时）
        this.fallbackConfig = this.getFallbackConfig();
    }

    getFallbackConfig() {
        return {
            system: {
                name: 'MTSCOS AI',
                version: '3.2.0',
                port: '8888',
                httpPort: '8080',
                maxLoginAttempts: 5,
                sessionTimeout: 3600,
                allowGuestAccess: false
            },
            exam: {
                maxDuration: 120,
                passingScore: 60,
                allowReview: true
            },
            student: {
                nineYearEnabled: true,
                adultEnabled: true
            },
            ui: {
                theme: 'cybertech',
                particlesEnabled: true,
                language: 'zh-CN'
            },
            permission: {
                enableAutoDetect: true,
                defaultGroup: 'student'
            }
        };
    }

    async fetchConfig(endpoint) {
        const cacheKey = endpoint;
        const now = Date.now();
        
        // 检查缓存
        if (this.cache.has(cacheKey)) {
            const timestamp = this.cacheTimestamp.get(cacheKey);
            if (now - timestamp < this.cacheTimeout) {
                return this.cache.get(cacheKey);
            }
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // 更新缓存
                this.cache.set(cacheKey, data.data || data);
                this.cacheTimestamp.set(cacheKey, now);
                return data.data || data;
            } else {
                throw new Error(data.error || '获取配置失败');
            }
        } catch (error) {
            console.warn(`配置加载失败 (${endpoint}):`, error.message);
            
            // 返回备用配置
            if (this.useFallback) {
                return this.getFallbackForEndpoint(endpoint);
            }
            return null;
        }
    }

    getFallbackForEndpoint(endpoint) {
        const fallbacks = {
            '/system/info': this.fallbackConfig.system,
            '/exam/config': this.fallbackConfig.exam,
            '/student/config': this.fallbackConfig.student,
            '/ui/config': this.fallbackConfig.ui,
            '/permission/config': this.fallbackConfig.permission,
            '/config': this.fallbackConfig
        };
        
        return fallbacks[endpoint] || null;
    }

    async getSystemInfo() {
        return await this.fetchConfig('/system/info');
    }

    async getExamConfig() {
        return await this.fetchConfig('/exam/config');
    }

    async getStudentConfig() {
        return await this.fetchConfig('/student/config');
    }

    async getUIConfig() {
        return await this.fetchConfig('/ui/config');
    }

    async getPermissionConfig() {
        return await this.fetchConfig('/permission/config');
    }

    async getAllConfigs() {
        return await this.fetchConfig('/config');
    }

    async initializeApp() {
        console.log('🚀 正在加载系统配置...');
        
        try {
            const [systemInfo, examConfig, studentConfig, uiConfig, permissionConfig] = await Promise.all([
                this.getSystemInfo(),
                this.getExamConfig(),
                this.getStudentConfig(),
                this.getUIConfig(),
                this.getPermissionConfig()
            ]);
            
            const appConfig = {
                system: systemInfo,
                exam: examConfig,
                student: studentConfig,
                ui: uiConfig,
                permission: permissionConfig
            };
            
            // 存储到 localStorage
            localStorage.setItem('mtcos_app_config', JSON.stringify(appConfig));
            localStorage.setItem('mtcos_config_loaded', Date.now().toString());
            
            console.log('✅ 系统配置加载完成', appConfig);
            return appConfig;
        } catch (error) {
            console.error('❌ 配置加载失败:', error);
            return this.fallbackConfig;
        }
    }

    getConfigFromStorage() {
        try {
            const configStr = localStorage.getItem('mtcos_app_config');
            const loadedTime = localStorage.getItem('mtcos_config_loaded');
            
            if (configStr && loadedTime) {
                const loaded = parseInt(loadedTime);
                
                // 检查配置是否过期
                if (Date.now() - loaded < this.cacheTimeout) {
                    return JSON.parse(configStr);
                }
            }
            
            return null;
        } catch (error) {
            return null;
        }
    }

    async ensureConfig() {
        // 先尝试从 localStorage 获取
        let config = this.getConfigFromStorage();
        
        // 如果没有或已过期，重新加载
        if (!config) {
            config = await this.initializeApp();
        }
        
        return config;
    }

    // 应用UI配置
    applyUIConfig(config) {
        if (!config || !config.ui) return;
        
        const { theme, particlesEnabled, language } = config.ui;
        
        // 应用主题
        if (theme) {
            document.documentElement.setAttribute('data-theme', theme);
        }
        
        // 应用粒子效果
        if (particlesEnabled === false) {
            const particlesContainer = document.getElementById('particles');
            if (particlesContainer) {
                particlesContainer.style.display = 'none';
            }
        }
        
        // 应用语言
        if (language) {
            document.documentElement.setAttribute('lang', language);
        }
    }

    // 获取考试配置
    getExamSettings() {
        const config = this.getConfigFromStorage() || this.fallbackConfig;
        return config.exam || this.fallbackConfig.exam;
    }

    // 获取学生配置
    getStudentSettings() {
        const config = this.getConfigFromStorage() || this.fallbackConfig;
        return config.student || this.fallbackConfig.student;
    }

    // 获取权限配置
    getPermissionSettings() {
        const config = this.getConfigFromStorage() || this.fallbackConfig;
        return config.permission || this.fallbackConfig.permission;
    }

    // 清除缓存
    clearCache() {
        this.cache.clear();
        this.cacheTimestamp.clear();
        localStorage.removeItem('mtcos_app_config');
        localStorage.removeItem('mtcos_config_loaded');
    }

    // 刷新配置
    async refreshConfig() {
        this.clearCache();
        return await this.initializeApp();
    }
}

// 创建全局实例
const systemConfig = new SystemConfigLoader();

// 页面加载时自动初始化配置
if (typeof window !== 'undefined') {
    window.addEventListener('load', async () => {
        await systemConfig.ensureConfig();
    });
}

// 导出配置加载器
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SystemConfigLoader, systemConfig };
}
