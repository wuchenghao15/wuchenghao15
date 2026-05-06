// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 模块管理器
 * 实现项目所有功能的模块化管理，支持AI、JS自定义方法和管理员手动统一智能管理
 */

class ModuleManager {
    constructor() {
        this.modules = new Map();
        this.moduleCategories = {
            AI: 'ai_modules',
            JS: 'js_modules',
            ADMIN: 'admin_modules',
            CORE: 'core_modules'
        };
        this.aiManager = null;
        this.adminManager = null;
        this.setupModuleDiscovery();
        this.initializeCoreModules();
    }

    // 设置模块发现机制
    setupModuleDiscovery() {
        // 监听模块注册事件
        window.addEventListener('module_register', (event) => {
            this.registerModule(event.detail);
        });

        // 定期扫描模块目录
        interval_z7mni8z7u = interval_wji00r1pg = setInterval(() => {
            this.scanForModules();
        }, 30000); // 每30秒扫描一次
    }

    // 初始化核心模块
    initializeCoreModules() {
        // 初始化AI管理器
        this.aiManager = new AIModuleManager(this);
        this.registerModule({
            id: 'ai_manager',
            name: 'AI模块管理器',
            category: this.moduleCategories.CORE,
            version: '1.0.0',
            instance: this.aiManager
        });

        // 初始化管理员管理器
        this.adminManager = new AdminModuleManager(this);
        this.registerModule({
            id: 'admin_manager',
            name: '管理员模块管理器',
            category: this.moduleCategories.CORE,
            version: '1.0.0',
            instance: this.adminManager
        });

        // 初始化JS模块管理器
        this.jsManager = new JSModuleManager(this);
        this.registerModule({
            id: 'js_manager',
            name: 'JS模块管理器',
            category: this.moduleCategories.CORE,
            version: '1.0.0',
            instance: this.jsManager
        });
    }

    // 注册模块
    registerModule(moduleConfig) {
        const { id, name, category, version, instance, dependencies = [] } = moduleConfig;

        if (!id || !name || !category) {
            console.warn('模块注册失败：缺少必要参数', moduleConfig);
            return false;
        }

        // 检查依赖
        const missingDependencies = dependencies.filter(depId => !this.modules.has(depId));
        if (missingDependencies.length > 0) {
            console.warn(`模块 ${name} 缺少依赖：`, missingDependencies);
            // 延迟注册
            setTimeout(() => this.registerModule(moduleConfig), 1000);
            return false;
        }

        // 注册模块
        this.modules.set(id, {
            id,
            name,
            category,
            version,
            instance,
            dependencies,
            status: 'active',
            registeredAt: new Date().toISOString()
        });

        console.log(`模块注册成功：${name} (${id})`);
        
        // 触发模块注册事件
        window.dispatchEvent(new CustomEvent('module_registered', {
            detail: moduleConfig
        }));

        return true;
    }

    // 扫描模块
    scanForModules() {
        console.log('开始扫描模块...');
        
        // 扫描AI模块
        this.aiManager.scanModules();
        
        // 扫描JS模块
        this.jsManager.scanModules();
        
        // 扫描管理员模块
        this.adminManager.scanModules();
        
        console.log('模块扫描完成');
    }

    // 获取模块
    getModule(moduleId) {
        return this.modules.get(moduleId);
    }

    // 获取所有模块
    getAllModules() {
        return Array.from(this.modules.values());
    }

    // 获取指定类别的模块
    getModulesByCategory(category) {
        return Array.from(this.modules.values()).filter(module => module.category === category);
    }

    // 启用模块
    enableModule(moduleId) {
        const module = this.modules.get(moduleId);
        if (module) {
            module.status = 'active';
            if (module.instance && module.instance.onEnable) {
                module.instance.onEnable();
            }
            console.log(`模块已启用：${module.name}`);
            return true;
        }
        return false;
    }

    // 禁用模块
    disableModule(moduleId) {
        const module = this.modules.get(moduleId);
        if (module) {
            module.status = 'inactive';
            if (module.instance && module.instance.onDisable) {
                module.instance.onDisable();
            }
            console.log(`模块已禁用：${module.name}`);
            return true;
        }
        return false;
    }

    // 重启模块
    restartModule(moduleId) {
        this.disableModule(moduleId);
        setTimeout(() => {
            this.enableModule(moduleId);
        }, 100);
    }

    // 智能管理模块
    smartManageModules() {
        console.log('开始智能管理模块...');
        
        // 1. 资源优化
        this.optimizeResources();
        
        // 2. 模块健康检查
        this.checkModuleHealth();
        
        // 3. AI智能调度
        this.aiManager.smartSchedule();
        
        console.log('智能管理完成');
    }

    // 优化资源
    optimizeResources() {
        const activeModules = Array.from(this.modules.values()).filter(module => module.status === 'active');
        console.log(`当前活跃模块数：${activeModules.length}`);
        
        // 根据系统负载调整模块状态
        if (navigator && navigator.hardwareConcurrency) {
            const cpuCount = navigator.hardwareConcurrency;
            const memoryInfo = navigator.deviceMemory || 4;
            
            console.log(`系统资源：CPU ${cpuCount}核，内存 ${memoryInfo}GB`);
            
            // 简单的资源调度逻辑
            if (activeModules.length > cpuCount * 2) {
                console.log('系统负载较高，考虑禁用部分非关键模块');
            }
        }
    }

    // 检查模块健康状态
    checkModuleHealth() {
        this.modules.forEach((module, moduleId) => {
            if (module.instance && module.instance.checkHealth) {
                const healthStatus = module.instance.checkHealth();
                console.log(`${module.name} 健康状态：${healthStatus}`);
                
                if (healthStatus === 'unhealthy') {
                    console.warn(`模块 ${module.name} 状态异常，正在重启...`);
                    this.restartModule(moduleId);
                }
            }
        });
    }

    // 导出模块配置
    exportModuleConfig() {
        const config = {
            modules: Array.from(this.modules.values()),
            exportTime: new Date().toISOString(),
            version: '1.0.0'
        };
        
        localStorage.setItem('module_config', JSON.stringify(config));
        console.log('模块配置已导出');
        return config;
    }

    // 导入模块配置
    importModuleConfig(config) {
        if (config && config.modules) {
            config.modules.forEach(moduleConfig => {
                this.registerModule(moduleConfig);
            });
            console.log('模块配置已导入');
            return true;
        }
        return false;
    }
}

/**
 * AI模块管理器
 */
class AIModuleManager {
    constructor(moduleManager) {
        this.moduleManager = moduleManager;
        this.aiModules = [];
        this.setupAISystem();
    }

    // 设置AI系统
    setupAISystem() {
        console.log('初始化AI模块系统');
        
        // 注册默认AI模块
        this.registerAIModule({
            id: 'ai_optimizer',
            name: 'AI优化器',
            version: '1.0.0',
            capabilities: ['resource_optimization', 'performance_tuning']
        });

        this.registerAIModule({
            id: 'ai_monitor',
            name: 'AI监控器',
            version: '1.0.0',
            capabilities: ['health_monitoring', 'error_detection']
        });
    }

    // 注册AI模块
    registerAIModule(moduleConfig) {
        this.aiModules.push(moduleConfig);
        this.moduleManager.registerModule({
            ...moduleConfig,
            category: this.moduleManager.moduleCategories.AI,
            instance: this
        });
    }

    // 扫描AI模块
    scanModules() {
        console.log('扫描AI模块');
        // 这里可以添加实际的模块扫描逻辑
    }

    // 智能调度
    smartSchedule() {
        console.log('AI智能调度');
        // 基于系统状态和模块需求进行智能调度
    }

    // 检查健康状态
    checkHealth() {
        return 'healthy';
    }
}

/**
 * JS模块管理器
 */
class JSModuleManager {
    constructor(moduleManager) {
        this.moduleManager = moduleManager;
        this.jsModules = [];
        this.setupJSModules();
    }

    // 设置JS模块
    setupJSModules() {
        console.log('初始化JS模块系统');
        
        // 注册默认JS模块
        this.registerJSModule({
            id: 'japanese_assessment',
            name: '日语水平评估',
            version: '1.0.0',
            dependencies: ['core_ui']
        });

        this.registerJSModule({
            id: 'japanese_exam',
            name: '日语考试系统',
            version: '1.0.0',
            dependencies: ['core_ui']
        });
    }

    // 注册JS模块
    registerJSModule(moduleConfig) {
        this.jsModules.push(moduleConfig);
        this.moduleManager.registerModule({
            ...moduleConfig,
            category: this.moduleManager.moduleCategories.JS,
            instance: this
        });
    }

    // 扫描JS模块
    scanModules() {
        console.log('扫描JS模块');
        // 这里可以添加实际的模块扫描逻辑
    }

    // 检查健康状态
    checkHealth() {
        return 'healthy';
    }
}

/**
 * 管理员模块管理器
 */
class AdminModuleManager {
    constructor(moduleManager) {
        this.moduleManager = moduleManager;
        this.adminModules = [];
        this.setupAdminModules();
    }

    // 设置管理员模块
    setupAdminModules() {
        console.log('初始化管理员模块系统');
        
        // 注册默认管理员模块
        this.registerAdminModule({
            id: 'admin_panel',
            name: '管理员面板',
            version: '1.0.0',
            permissions: ['manage_modules', 'view_stats']
        });

        this.registerAdminModule({
            id: 'system_monitor',
            name: '系统监控',
            version: '1.0.0',
            permissions: ['view_system', 'view_logs']
        });
    }

    // 注册管理员模块
    registerAdminModule(moduleConfig) {
        this.adminModules.push(moduleConfig);
        this.moduleManager.registerModule({
            ...moduleConfig,
            category: this.moduleManager.moduleCategories.ADMIN,
            instance: this
        });
    }

    // 扫描管理员模块
    scanModules() {
        console.log('扫描管理员模块');
        // 这里可以添加实际的模块扫描逻辑
    }

    // 检查健康状态
    checkHealth() {
        return 'healthy';
    }
}

// 导出模块管理器
export default ModuleManager;

// 全局模块管理器实例
if (typeof window !== 'undefined') {
    window.ModuleManager = ModuleManager;
    window.moduleManager = new ModuleManager();
    
    // 定期智能管理
    setInterval(() => {
        window.moduleManager.smartManageModules();
    }, 60000); // 每分钟智能管理一次
}


// 清理定时器
window.onunload = function() {
    clearInterval(interval_z7mni8z7u);
    clearInterval(interval_wji00r1pg);
};