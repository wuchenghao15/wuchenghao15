/**
 * MTSCOS AI System - 前端核心系统
 * 版本: 4.3.0
 * 描述: 多模块集成的智能云操作系统前端核心
 */

class MTSCOSSystem {
    constructor() {
        this.version = '4.3.0';
        this.config = null;
        this.modules = {};
        this.isInitialized = false;
        this.startTime = Date.now();
        
        // 模块注册表
        this.moduleRegistry = {
            database: DatabaseManager,
            sync: DataSyncService,
            dispatcher: AIDispatcher,
            orchestrator: SystemOrchestrator,
            data: DataManager,
            security: SecurityManager,
            middleware: MiddlewareManager,
            server: ServerManager,
            ai: AIManager,
            employees: window.AIEmployeeManager || null,
            version: VersionManager,
            rules: RulesEngine
        };
        
        this.init();
    }
    
    async init() {
        console.log(`🚀 MTSCOS AI System v${this.version} 初始化中...`);
        
        // 先初始化日志系统
        this.initLogger();
        
        try {
            // 加载系统配置
            await this.loadConfig();
            
            // 按优先级初始化模块
            await this.initializeModules();
            
            // 初始化UI管理器
            this.initUIManager();
            
            // 初始化路由系统
            this.initRouter();
            
            // 启动性能监控
            this.initPerformanceMonitor();
            
            // 初始化错误处理
            this.initErrorHandler();
            
            this.isInitialized = true;
            this.log('info', 'MTSCOS AI System 初始化完成', { 
                duration: Date.now() - this.startTime,
                modules: Object.keys(this.modules).length
            });
            
            // 触发系统就绪事件
            document.dispatchEvent(new CustomEvent('mtscos:ready', { 
                detail: { system: this } 
            }));
            
        } catch (error) {
            this.log('error', '系统初始化失败', { error: error.message });
            console.error('MTSCOS初始化错误:', error);
        }
    }
    
    async loadConfig() {
        try {
            const response = await fetch('config/system-config.json');
            if (!response.ok) throw new Error(`配置加载失败: ${response.status}`);
            
            this.config = await response.json();
            this.log('info', '系统配置加载成功', { 
                modules: Object.keys(this.config.modules).length 
            });
            
            return this.config;
        } catch (error) {
            this.log('warn', '使用默认配置', { error: error.message });
            this.config = this.getDefaultConfig();
            return this.config;
        }
    }
    
    getDefaultConfig() {
        return {
            system: {
                name: 'MTSCOS AI System',
                version: '4.3.0',
                status: 'stable'
            },
            modules: {
                data: { enabled: true, priority: 1 },
                security: { enabled: true, priority: 0 },
                middleware: { enabled: true, priority: 2 }
            },
            ui: {
                theme: { current: 'light' },
                layout: { sidebar: { enabled: false } }
            }
        };
    }
    
    initLogger() {
        this.logger = {
            logs: [],
            maxLogs: 1000,
            
            log(level, message, data = {}) {
                const entry = {
                    timestamp: new Date().toISOString(),
                    level,
                    message,
                    data,
                    source: 'MTSCOS'
                };
                
                this.logs.push(entry);
                if (this.logs.length > this.maxLogs) {
                    this.logs.shift();
                }
                
                // 根据级别输出
                const styles = {
                    debug: 'color: #94a3b8',
                    info: 'color: #3b82f6',
                    warn: 'color: #f59e0b',
                    error: 'color: #ef4444',
                    fatal: 'color: #dc2626; font-weight: bold'
                };
                
                console.log(`%c[${entry.timestamp}] [${level.toUpperCase()}] ${message}`, 
                    styles[level] || '', data);
                
                return entry;
            },
            
            getLogs(level = null) {
                if (level) {
                    return this.logs.filter(log => log.level === level);
                }
                return [...this.logs];
            },
            
            clearLogs() {
                this.logs = [];
            }
        };
        
        // 绑定到系统实例
        this.log = this.logger.log.bind(this.logger);
    }
    
    async initializeModules() {
        this.log('info', '开始初始化模块');
        
        try {
            // 1. 先初始化数据库（核心依赖）- 同步方式
            if (this.moduleRegistry.database) {
                this.modules.database = new DatabaseManager();
                this.log('info', '模块 database 初始化成功 (异步)');
            }
            
            // 2. 延迟初始化依赖数据库的服务
            setTimeout(() => this.initializeDependentModules(), 100);
            
        } catch (error) {
            this.log('error', '模块初始化失败', { error: error.message });
        }
        
        return this.modules;
    }
    
    async initializeDependentModules() {
        try {
            // 等待数据库就绪
            if (this.modules.database) {
                await this.modules.database.waitForReady();
            }
            
            // 2. 初始化数据同步服务
            if (this.moduleRegistry.sync && this.modules.database) {
                this.modules.sync = new DataSyncService(this.modules.database);
                this.log('info', '模块 sync 初始化成功');
            }
            
            // 3. 初始化AI调度员
            if (this.moduleRegistry.dispatcher && this.modules.database) {
                this.modules.dispatcher = new AIDispatcher(
                    this.modules.database,
                    this.modules.sync || null
                );
                this.log('info', '模块 dispatcher 初始化成功');
            }
            
            // 4. 初始化系统编排器
            if (this.moduleRegistry.orchestrator && this.modules.database) {
                this.modules.orchestrator = new SystemOrchestrator(
                    this.modules.database,
                    this.modules.dispatcher || null
                );
                this.log('info', '模块 orchestrator 初始化成功');
            }
            
            // 5. 初始化其他模块
            const otherModules = Object.entries(this.config.modules)
                .filter(([name, config]) => 
                    config.enabled && 
                    !['database', 'sync', 'dispatcher', 'orchestrator'].includes(name) &&
                    this.moduleRegistry[name]
                );
            
            for (const [name, config] of otherModules) {
                try {
                    this.modules[name] = new this.moduleRegistry[name](this.config.modules[name]);
                    this.log('info', `模块 ${name} 初始化成功`);
                } catch (error) {
                    this.log('error', `模块 ${name} 初始化失败`, { error: error.message });
                }
            }
            
            // 上报数据库状态
            this.reportDatabaseStatus();
            
        } catch (error) {
            this.log('error', '依赖模块初始化失败', { error: error.message });
        }
    }
    
    // 上报数据库状态
    async reportDatabaseStatus() {
        if (this.modules.database) {
            const health = await this.modules.database.healthCheck();
            console.log('📊 数据库状态上报:', health);
            document.dispatchEvent(new CustomEvent('mtscos:database:health', { detail: health }));
        }
    }
    
    initUIManager() {
        this.ui = {
            theme: window.themeManager || null, // 使用system-core.js中的ThemeManager
            layout: new LayoutManager(this.config?.ui?.layout),
            components: new ComponentManager(),
            animations: new AnimationManager(this.config?.ui?.effects?.animations)
        };
        
        this.log('info', 'UI管理器初始化完成');
    }
    
    initRouter() {
        this.router = {
            routes: new Map(),
            currentRoute: null,
            
            register(path, handler, meta = {}) {
                this.routes.set(path, { handler, meta });
            },
            
            async navigate(path) {
                const route = this.routes.get(path);
                if (!route) {
                    console.warn(`路由 ${path} 未找到`);
                    return false;
                }
                
                this.currentRoute = path;
                await route.handler();
                return true;
            },
            
            getCurrentPath() {
                return window.location.pathname;
            }
        };
        
        this.log('info', '路由系统初始化完成');
    }
    
    initPerformanceMonitor() {
        if (!this.config?.performance?.monitoring?.enabled) return;
        
        this.performance = {
            metrics: {},
            observers: [],
            
            measure(name, callback) {
                const start = performance.now();
                const result = callback();
                const duration = performance.now() - start;
                
                this.metrics[name] = {
                    duration,
                    timestamp: Date.now()
                };
                
                return result;
            },
            
            getMetrics() {
                return { ...this.metrics };
            },
            
            report() {
                console.table(this.metrics);
                return this.metrics;
            }
        };
        
        // 监控核心Web指标
        if ('PerformanceObserver' in window) {
            try {
                const observer = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        this.performance.metrics[entry.name] = {
                            value: entry.value,
                            timestamp: Date.now()
                        };
                    }
                });
                
                observer.observe({ entryTypes: ['measure', 'navigation', 'paint'] });
                this.performance.observers.push(observer);
            } catch (e) {
                console.warn('性能观察器初始化失败:', e);
            }
        }
        
        this.log('info', '性能监控系统启动');
    }
    
    initErrorHandler() {
        window.addEventListener('error', (event) => {
            this.log('error', '未捕获的JavaScript错误', {
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.log('error', '未处理的Promise拒绝', {
                reason: event.reason?.message || event.reason
            });
        });
        
        this.log('info', '全局错误处理器已启动');
    }
    
    // 系统控制方法
    getModule(name) {
        return this.modules[name] || null;
    }
    
    hasModule(name) {
        return name in this.modules;
    }
    
    getConfig(path = null) {
        if (!path) return this.config;
        
        return path.split('.').reduce((obj, key) => obj?.[key], this.config);
    }
    
    updateConfig(path, value) {
        const keys = path.split('.');
        let current = this.config;
        
        for (let i = 0; i < keys.length - 1; i++) {
            if (!(keys[i] in current)) {
                current[keys[i]] = {};
            }
            current = current[keys[i]];
        }
        
        current[keys[keys.length - 1]] = value;
        this.log('info', `配置更新: ${path}`, { value });
    }
    
    getSystemInfo() {
        return {
            name: this.config?.system?.name || 'MTSCOS AI System',
            version: this.version,
            status: this.isInitialized ? 'ready' : 'initializing',
            uptime: Date.now() - this.startTime,
            modules: Object.keys(this.modules),
            config: {
                theme: this.config?.ui?.theme?.current,
                performance: this.config?.performance?.monitoring?.enabled
            }
        };
    }
    
    // 状态管理
    getState(key) {
        return this.state?.[key];
    }
    
    setState(key, value) {
        if (!this.state) this.state = {};
        this.state[key] = value;
        document.dispatchEvent(new CustomEvent(`mtscos:state:${key}`, { detail: value }));
    }
    
    // 事件系统
    on(event, handler) {
        document.addEventListener(`mtscos:${event}`, handler);
    }
    
    off(event, handler) {
        document.removeEventListener(`mtscos:${event}`, handler);
    }
    
    emit(event, detail = {}) {
        document.dispatchEvent(new CustomEvent(`mtscos:${event}`, { detail }));
    }
    
    // 系统健康检查
    async healthCheck() {
        const health = {
            status: 'healthy',
            timestamp: Date.now(),
            modules: {},
            performance: this.performance?.getMetrics() || {}
        };
        
        for (const [name, module] of Object.entries(this.modules)) {
            try {
                if (typeof module.healthCheck === 'function') {
                    health.modules[name] = await module.healthCheck();
                } else {
                    health.modules[name] = { status: 'ok' };
                }
            } catch (error) {
                health.modules[name] = { status: 'error', error: error.message };
                health.status = 'degraded';
            }
        }
        
        return health;
    }
    
    // 销毁系统
    destroy() {
        // 清理所有模块
        for (const [name, module] of Object.entries(this.modules)) {
            if (typeof module.destroy === 'function') {
                module.destroy();
            }
        }
        
        // 清理性能观察器
        if (this.performance?.observers) {
            this.performance.observers.forEach(obs => obs.disconnect());
        }
        
        // 清理状态
        this.state = {};
        
        this.isInitialized = false;
        this.log('info', 'MTSCOS AI System 已销毁');
    }
}

// ==================== 子模块定义 ====================

class DataManager {
    constructor(config = {}) {
        this.config = config || { storage: { type: 'indexedDB' }, cache: {} };
        this.storage = new DataStorage(this.config.storage || { type: 'indexedDB' });
        this.cache = new DataCache(this.config.cache || {});
        this.isReady = false;
        this.init();
    }
    
    async init() {
        try {
            await this.storage.init();
            this.isReady = true;
        } catch (error) {
            console.error('数据管理器初始化失败:', error);
        }
    }
    
    async set(key, value, options = {}) {
        // 先更新缓存
        this.cache.set(key, value);
        // 再持久化
        return await this.storage.set(key, value, options);
    }
    
    async get(key, defaultValue = null) {
        // 先查缓存
        if (this.cache.has(key)) {
            return this.cache.get(key);
        }
        // 再查存储
        const value = await this.storage.get(key, defaultValue);
        // 更新缓存
        if (value !== defaultValue) {
            this.cache.set(key, value);
        }
        return value;
    }
    
    async delete(key) {
        this.cache.delete(key);
        return await this.storage.delete(key);
    }
    
    async clear() {
        this.cache.clear();
        return await this.storage.clear();
    }
    
    healthCheck() {
        return {
            status: this.isReady ? 'ok' : 'error',
            storage: this.storage.isReady,
            cache: {
                size: this.cache.size,
                hits: this.cache.hits,
                misses: this.cache.misses
            }
        };
    }
}

class DataStorage {
    constructor(config) {
        this.config = config || { type: 'indexedDB' };
        this.isReady = false;
        this.db = null;
    }
    
    async init() {
        if (!this.config) {
            this.config = { type: 'indexedDB' };
        }
        if (this.config.type === 'indexedDB') {
            try {
                await this.initIndexedDB();
            } catch (e) {
                console.warn('IndexedDB初始化失败:', e.message);
            }
        }
        this.isReady = true;
    }
    
    async initIndexedDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('MTSCOS_DB', 1);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('data')) {
                    db.createObjectStore('data', { keyPath: 'key' });
                }
            };
        });
    }
    
    async set(key, value, options = {}) {
        if (this.config.encrypt) {
            value = this.encrypt(value);
        }
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['data'], 'readwrite');
            const store = transaction.objectStore('data');
            const request = store.put({ key, value, timestamp: Date.now() });
            
            request.onsuccess = () => resolve(true);
            request.onerror = () => reject(request.error);
        });
    }
    
    async get(key, defaultValue = null) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['data'], 'readonly');
            const store = transaction.objectStore('data');
            const request = store.get(key);
            
            request.onsuccess = () => {
                const result = request.result;
                if (result) {
                    let value = result.value;
                    if (this.config.encrypt) {
                        value = this.decrypt(value);
                    }
                    resolve(value);
                } else {
                    resolve(defaultValue);
                }
            };
            request.onerror = () => reject(request.error);
        });
    }
    
    async delete(key) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['data'], 'readwrite');
            const store = transaction.objectStore('data');
            const request = store.delete(key);
            
            request.onsuccess = () => resolve(true);
            request.onerror = () => reject(request.error);
        });
    }
    
    async clear() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['data'], 'readwrite');
            const store = transaction.objectStore('data');
            const request = store.clear();
            
            request.onsuccess = () => resolve(true);
            request.onerror = () => reject(request.error);
        });
    }
    
    encrypt(data) {
        // 简单的加密实现
        return btoa(JSON.stringify(data));
    }
    
    decrypt(data) {
        try {
            return JSON.parse(atob(data));
        } catch {
            return data;
        }
    }
}

class DataCache {
    constructor(config) {
        this.config = config;
        this.cache = new Map();
        this.timestamps = new Map();
        this.hits = 0;
        this.misses = 0;
    }
    
    get size() {
        return this.cache.size;
    }
    
    set(key, value) {
        if (this.cache.size >= this.config.max_entries) {
            this.evict();
        }
        
        this.cache.set(key, value);
        this.timestamps.set(key, Date.now());
    }
    
    get(key) {
        if (!this.has(key)) {
            this.misses++;
            return undefined;
        }
        
        this.hits++;
        return this.cache.get(key);
    }
    
    has(key) {
        if (!this.cache.has(key)) return false;
        
        const age = Date.now() - this.timestamps.get(key);
        if (age > this.config.ttl) {
            this.delete(key);
            return false;
        }
        
        return true;
    }
    
    delete(key) {
        this.cache.delete(key);
        this.timestamps.delete(key);
    }
    
    clear() {
        this.cache.clear();
        this.timestamps.clear();
    }
    
    evict() {
        // LRU策略
        let oldest = null;
        let oldestTime = Infinity;
        
        for (const [key, time] of this.timestamps) {
            if (time < oldestTime) {
                oldestTime = time;
                oldest = key;
            }
        }
        
        if (oldest) {
            this.delete(oldest);
        }
    }
}

class SecurityManager {
    constructor(config) {
        this.config = config;
        this.user = null;
        this.session = null;
        this.isAuthenticated = false;
        this.init();
    }
    
    init() {
        // 初始化安全检查
        this.setupSecurityHeaders();
        this.setupCSRFProtection();
    }
    
    setupSecurityHeaders() {
        // 内容安全策略
        const csp = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com",
            "font-src 'self' https://cdnjs.cloudflare.com",
            "img-src 'self' data: blob:",
            "connect-src 'self'",
            "frame-ancestors 'none'"
        ].join('; ');
        
        // 可以通过服务器设置这些头
        console.log('安全策略已配置');
    }
    
    setupCSRFProtection() {
        // CSRF令牌管理
        this.csrfToken = this.generateToken();
    }
    
    generateToken() {
        return Array.from(crypto.getRandomValues(new Uint8Array(32)))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }
    
    async login(credentials) {
        // 模拟登录验证
        if (credentials.username && credentials.password) {
            this.user = {
                id: 'user_' + Date.now(),
                username: credentials.username,
                role: 'admin',
                permissions: ['read', 'write', 'delete', 'admin']
            };
            
            this.session = {
                id: this.generateToken(),
                created: Date.now(),
                expires: Date.now() + this.config.features.authentication.session_timeout
            };
            
            this.isAuthenticated = true;
            return { success: true, user: this.user };
        }
        
        return { success: false, error: 'Invalid credentials' };
    }
    
    logout() {
        this.user = null;
        this.session = null;
        this.isAuthenticated = false;
    }
    
    hasPermission(permission) {
        return this.user?.permissions?.includes(permission) || false;
    }
    
    checkAuth() {
        if (!this.isAuthenticated) return false;
        if (!this.session) return false;
        return Date.now() < this.session.expires;
    }
    
    healthCheck() {
        return {
            status: 'ok',
            authenticated: this.isAuthenticated,
            csrf_token: !!this.csrfToken
        };
    }
}

class MiddlewareManager {
    constructor(config) {
        this.config = config;
        this.middlewares = [];
        this.init();
    }
    
    init() {
        // 注册中间件
        if (this.config.components.router?.enabled) {
            this.use('router', this.routerMiddleware.bind(this));
        }
        
        if (this.config.components.request_validator?.enabled) {
            this.use('validator', this.validatorMiddleware.bind(this));
        }
        
        if (this.config.components.rate_limit?.enabled) {
            this.use('rateLimit', this.rateLimitMiddleware.bind(this));
        }
        
        if (this.config.components.error_handler?.enabled) {
            this.use('errorHandler', this.errorHandlerMiddleware.bind(this));
        }
    }
    
    use(name, fn) {
        this.middlewares.push({ name, fn });
    }
    
    async execute(context) {
        for (const middleware of this.middlewares) {
            const result = await middleware.fn(context);
            if (result === false) {
                return { success: false, blocked: middleware.name };
            }
        }
        return { success: true };
    }
    
    async routerMiddleware(context) {
        // 路由中间件
        return true;
    }
    
    async validatorMiddleware(context) {
        // 请求验证中间件
        if (context.request && context.request.method === 'POST') {
            // 简单的输入验证
            if (!context.request.body) {
                return false;
            }
        }
        return true;
    }
    
    rateLimitMiddleware(context) {
        // 速率限制中间件
        const key = context.ip || 'unknown';
        const now = Date.now();
        
        if (!this.requests) this.requests = new Map();
        
        const record = this.requests.get(key) || { count: 0, reset: now + 60000 };
        
        if (now > record.reset) {
            record.count = 0;
            record.reset = now + 60000;
        }
        
        record.count++;
        this.requests.set(key, record);
        
        if (record.count > (this.config.components.request_validator?.rate_limit?.max_requests || 100)) {
            return false;
        }
        
        return true;
    }
    
    async errorHandlerMiddleware(context) {
        // 错误处理中间件
        return true;
    }
    
    healthCheck() {
        return {
            status: 'ok',
            middlewares: this.middlewares.length
        };
    }
}

class ServerManager {
    constructor(config) {
        this.config = config;
        this.connections = new Map();
        this.stats = {
            requests: 0,
            errors: 0,
            bytes_sent: 0,
            bytes_received: 0
        };
    }
    
    getStatus() {
        return {
            status: 'running',
            port: this.config.config.port,
            host: this.config.config.host,
            protocol: this.config.config.protocol,
            stats: this.stats
        };
    }
    
    recordRequest(bytesReceived, bytesSent) {
        this.stats.requests++;
        this.stats.bytes_received += bytesReceived || 0;
        this.stats.bytes_sent += bytesSent || 0;
    }
    
    recordError() {
        this.stats.errors++;
    }
    
    healthCheck() {
        return {
            status: 'ok',
            ...this.getStatus()
        };
    }
}

class AIManager {
    constructor(config) {
        this.config = config;
        this.providers = {};
        this.conversations = new Map();
        this.init();
    }
    
    init() {
        // 初始化AI提供商
        for (const [name, provider] of Object.entries(this.config.providers)) {
            if (provider.enabled) {
                this.providers[name] = new AIProvider(name, provider);
            }
        }
    }
    
    async chat(message, options = {}) {
        const provider = options.provider || 'local';
        const conversationId = options.conversationId || 'default';
        
        if (!this.conversations.has(conversationId)) {
            this.conversations.set(conversationId, []);
        }
        
        const conversation = this.conversations.get(conversationId);
        conversation.push({ role: 'user', content: message });
        
        try {
            const response = await this.providers[provider]?.chat(conversation);
            
            if (response) {
                conversation.push({ role: 'assistant', content: response });
                return { success: true, response, conversationId };
            }
            
            return { success: false, error: 'Provider not available' };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    getConversations() {
        return Array.from(this.conversations.keys());
    }
    
    healthCheck() {
        return {
            status: 'ok',
            providers: Object.keys(this.providers),
            conversations: this.conversations.size
        };
    }
}

class AIProvider {
    constructor(name, config) {
        this.name = name;
        this.config = config;
    }
    
    async chat(messages) {
        if (this.name === 'local') {
            return await this.chatLocal(messages);
        }
        return null;
    }
    
    async chatLocal(messages) {
        // 本地AI聊天
        const lastMessage = messages[messages.length - 1]?.content || '';
        
        // 简单的响应
        return `收到您的消息: "${lastMessage.substring(0, 50)}..."。这是来自MTSCOS AI的响应。`;
    }
}

class VersionManager {
    constructor(config) {
        this.config = config;
        this.currentVersion = config.current_version;
        this.buildDate = config.build_date;
        this.changelog = config.changelog || [];
        this.autoUpdate = config.auto_update;
    }
    
    getInfo() {
        return {
            version: this.currentVersion,
            buildDate: this.buildDate,
            codename: '智能教育版',
            status: this.config.status
        };
    }
    
    getChangelog() {
        return this.changelog;
    }
    
    async checkForUpdates() {
        // 模拟检查更新
        return {
            hasUpdate: false,
            currentVersion: this.currentVersion,
            latestVersion: this.currentVersion
        };
    }
    
    healthCheck() {
        return {
            status: 'ok',
            version: this.currentVersion,
            buildDate: this.buildDate
        };
    }
}

class RulesEngine {
    constructor(config) {
        this.config = config;
        this.rules = this.compileRules();
        this.violations = [];
    }
    
    compileRules() {
        const rules = [];
        
        for (const [category, categoryConfig] of Object.entries(this.config.categories)) {
            if (!categoryConfig.enabled) continue;
            
            for (const rule of categoryConfig.rules || []) {
                rules.push({
                    ...rule,
                    category,
                    compiledCondition: this.compileCondition(rule.condition)
                });
            }
        }
        
        return rules;
    }
    
    compileCondition(condition) {
        // 简单的条件编译
        return new Function('context', `return ${condition}`);
    }
    
    async evaluate(context) {
        const results = [];
        
        for (const rule of this.rules) {
            try {
                const result = rule.compiledCondition(context);
                
                if (result) {
                    const violation = {
                        rule: rule.id,
                        category: rule.category,
                        action: rule.action,
                        severity: rule.severity,
                        timestamp: Date.now()
                    };
                    
                    results.push(violation);
                    
                    if (this.config.enforcement.log_violations) {
                        this.violations.push(violation);
                    }
                }
            } catch (error) {
                console.error(`规则评估错误: ${rule.id}`, error);
            }
        }
        
        return results;
    }
    
    getViolations() {
        return [...this.violations];
    }
    
    healthCheck() {
        return {
            status: 'ok',
            rules: this.rules.length,
            violations: this.violations.length
        };
    }
}

// ==================== UI子模块 ====================

// ThemeManager已在system-core.js中定义，此处不再重复定义

class LayoutManager {
    constructor(config) {
        this.config = config;
        this.state = {
            sidebarOpen: config?.sidebar?.enabled ?? false,
            headerFixed: config?.header?.fixed ?? true
        };
    }
    
    toggleSidebar() {
        this.state.sidebarOpen = !this.state.sidebarOpen;
        document.body.classList.toggle('sidebar-open', this.state.sidebarOpen);
    }
    
    getLayout() {
        return this.state;
    }
}

class ComponentManager {
    constructor() {
        this.components = new Map();
    }
    
    register(name, component) {
        this.components.set(name, component);
    }
    
    get(name) {
        return this.components.get(name);
    }
    
    render(name, container) {
        const component = this.components.get(name);
        if (component && typeof component.render === 'function') {
            return component.render(container);
        }
        return null;
    }
}

class AnimationManager {
    constructor(config) {
        this.config = config || {};
        this.enabled = this.config.enabled ?? true;
        this.duration = {
            fast: this.parseDuration(this.config.duration?.fast || '150ms'),
            base: this.parseDuration(this.config.duration?.base || '300ms'),
            slow: this.parseDuration(this.config.duration?.slow || '500ms')
        };
        this.easing = this.config.easing || 'cubic-bezier(0.4, 0, 0.2, 1)';
    }
    
    parseDuration(duration) {
        if (typeof duration === 'number') return duration;
        return parseInt(duration) || 300;
    }
    
    animate(element, properties, duration = 'base') {
        if (!this.enabled || !element) return Promise.resolve();
        
        const ms = typeof duration === 'string' ? this.duration[duration] : duration;
        
        return new Promise(resolve => {
            element.style.transition = `all ${ms}ms ${this.easing}`;
            Object.assign(element.style, properties);
            
            setTimeout(() => {
                element.style.transition = '';
                resolve();
            }, ms);
        });
    }
}

// ==================== AI员工管理器（已移至 ai-employee-manager.js）================

// ==================== 初始化系统 ====================

// 当DOM加载完成后初始化系统
document.addEventListener('DOMContentLoaded', () => {
    // 延迟初始化，确保所有依赖加载完成
    setTimeout(() => {
        window.mtscos = new MTSCOSSystem();
    }, 100);
});

// 导出类供外部使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        MTSCOSSystem,
        DataManager,
        SecurityManager,
        MiddlewareManager,
        ServerManager,
        AIManager,
        VersionManager,
        RulesEngine,
        ThemeManager,
        LayoutManager
    };
}
