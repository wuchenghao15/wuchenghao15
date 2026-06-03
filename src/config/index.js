/**
 * 统一配置管理
 * 管理所有服务的端口、路径和配置信息
 */

const dotenv = require('dotenv');

// 加载环境变量
dotenv.config();

/**
 * 服务配置
 */
const services = {
    // 主服务器配置
    main: {
        port: process.env.PORT || 8080,
        host: '0.0.0.0',
        baseUrl: `http://localhost:${process.env.PORT || 8080}`,
        routes: {
            health: '/api/health',
            auth: '/api/auth',
            static: '/html',
            index: '/html/index.html'
        }
    },
    
    // Python服务器配置
    python: {
        port: process.env.PYTHON_PORT || 8082,
        host: '0.0.0.0',
        baseUrl: `http://localhost:${process.env.PYTHON_PORT || 8082}`,
        routes: {
            health: '/python/api/health',
            auth: '/python/api/auth',
            action: '/python/api/action',
            ai: '/python/api/ai',
            dashboard: '/python/dashboard',
            login: '/python/auth/login',
            register: '/python/auth/register'
        }
    },
    
    // 监控服务配置
    monitor: {
        port: process.env.MONITOR_PORT || 8083,
        host: '0.0.0.0',
        baseUrl: `http://localhost:${process.env.MONITOR_PORT || 8083}`,
        routes: {
            health: '/api/health',
            clients: '/api/monitor/clients'
        }
    }
};

/**
 * 统一入口管理
 */
const entryPoints = {
    // 维护入口
    maintenance: services.main.baseUrl + services.main.routes.health,
    
    // 后台入口
    backend: services.python.baseUrl + services.python.routes.dashboard,
    
    // 检测入口
    monitoring: services.monitor.baseUrl + services.monitor.routes.health,
    
    // 调试入口
    debug: services.main.baseUrl + services.main.routes.health,
    
    // API接入入口
    api: services.main.baseUrl + services.main.routes.auth,
    
    // AI入口
    ai: services.python.baseUrl + services.python.routes.ai
};

/**
 * 导出配置
 */
module.exports = {
    services,
    entryPoints,
    getServiceConfig: (serviceName) => services[serviceName],
    getEntryPoint: (entryName) => entryPoints[entryName],
    getAllServices: () => Object.keys(services),
    getAllEntryPoints: () => Object.keys(entryPoints)
};


// 初始化机制
const init = () => {
    console.log("Initializing module...");
    // 在这里添加初始化逻辑
    // 例如：加载配置、初始化依赖、设置事件监听等
    
    // 示例：加载配置
    // const config = loadConfig();
    
    // 示例：初始化依赖
    // initializeDependencies();
    
    // 示例：设置事件监听
    // setupEventListeners();
    
    console.log("Module initialized successfully!");
};

// 自动初始化
if (typeof window !== 'undefined') {
    // 浏览器环境：DOM加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
} else {
    // Node.js环境：导出初始化函数
    if (typeof module !== 'undefined' && module.exports) {
        module.exports.init = init;
    }
}
