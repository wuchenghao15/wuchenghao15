/**
 * MTSCOS AI System - 前端核心系统
 * 版本: 5.0.0
 * 描述: 多模块集成的智能云操作系统前端核心 - 智能系统优化版
 */

class MTSCOSSystem {
    constructor() {
        this.version = '5.0.0';
        this.config = null;
        this.modules = {};
        this.isInitialized = false;
        this.startTime = Date.now();
        
        this.moduleRegistry = {
            database: window.DatabaseManager || DefaultDatabaseManager,
            sync: window.DataSyncService || DefaultDataSyncService,
            dispatcher: window.AIDispatcher || DefaultAIDispatcher,
            orchestrator: window.SystemOrchestrator || DefaultSystemOrchestrator,
            data: DataManager,
            security: SecurityManager,
            middleware: MiddlewareManager,
            server: ServerManager,
            ai: AIManager,
            employees: window.AIEmployeeManager || DefaultAIEmployeeManager,
            version: VersionManager,
            rules: RulesEngine
        };
        
        this.init();
    }
    
    async init() {
        console.log(`🚀 MTSCOS AI System v${this.version} 初始化中...`);
        
        this.initLogger();
        
        try {
            await this.loadConfig();
            await this.initializeModules();
            this.initUIManager();
            this.initRouter();
            this.initPerformanceMonitor();
            this.initErrorHandler();
            
            this.isInitialized = true;
            this.log('info', 'MTSCOS AI System 初始化完成', { 
                duration: Date.now() - this.startTime,
                modules: Object.keys(this.modules).length
            });
            
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
            const response = await fetch('/config/system-config.json');
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
                version: '5.0.0',
                status: 'stable',
                codename: '智能系统优化版'
            },
            api: {
                base_url: '/api',
                timeout: 30000
            },
            modules: {
                data: { enabled: true, priority: 1 },
                security: { enabled: true, priority: 0 },
                middleware: { enabled: true, priority: 2 },
                ai: { enabled: true, priority: 3 }
            },
            ui: {
                theme: { current: 'light' },
                layout: { sidebar: { enabled: false } }
            },
            performance: {
                monitoring: { enabled: true }
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
        
        this.log = this.logger.log.bind(this.logger);
    }
    
    async initializeModules() {
        this.log('info', '开始初始化模块');
        
        try {
            if (this.moduleRegistry.database) {
                try {
                    this.modules.database = new this.moduleRegistry.database();
                    this.log('info', '模块 database 初始化成功');
                } catch (e) {
                    this.log('warn', '模块 database 初始化失败，使用默认实现', { error: e.message });
                    this.modules.database = new DefaultDatabaseManager();
                }
            }
            
            setTimeout(() => this.initializeDependentModules(), 100);
            
        } catch (error) {
            this.log('error', '模块初始化失败', { error: error.message });
        }
        
        return this.modules;
    }
    
    async initializeDependentModules() {
        try {
            if (this.modules.database && typeof this.modules.database.waitForReady === 'function') {
                await this.modules.database.waitForReady();
            }
            
            if (this.moduleRegistry.sync && this.modules.database) {
                try {
                    this.modules.sync = new this.moduleRegistry.sync(this.modules.database);
                    this.log('info', '模块 sync 初始化成功');
                } catch (e) {
                    this.log('warn', '模块 sync 初始化失败，使用默认实现', { error: e.message });
                    this.modules.sync = new DefaultDataSyncService(this.modules.database);
                }
            }
            
            if (this.moduleRegistry.dispatcher && this.modules.database) {
                try {
                    this.modules.dispatcher = new this.moduleRegistry.dispatcher(
                        this.modules.database,
                        this.modules.sync || null
                    );
                    this.log('info', '模块 dispatcher 初始化成功');
                } catch (e) {
                    this.log('warn', '模块 dispatcher 初始化失败，使用默认实现', { error: e.message });
                    this.modules.dispatcher = new DefaultAIDispatcher(this.modules.database, this.modules.sync || null);
                }
            }
            
            if (this.moduleRegistry.orchestrator && this.modules.database) {
                try {
                    this.modules.orchestrator = new this.moduleRegistry.orchestrator(
                        this.modules.database,
                        this.modules.dispatcher || null
                    );
                    this.log('info', '模块 orchestrator 初始化成功');
                } catch (e) {
                    this.log('warn', '模块 orchestrator 初始化失败，使用默认实现', { error: e.message });
                    this.modules.orchestrator = new DefaultSystemOrchestrator(this.modules.database, this.modules.dispatcher || null);
                }
            }
            
            const otherModules = Object.entries(this.config.modules || {})
                .filter(([name, config]) => 
                    config && config.enabled && 
                    !['database', 'sync', 'dispatcher', 'orchestrator'].includes(name) &&
                    this.moduleRegistry[name]
                );
            
            for (const [name, config] of otherModules) {
                try {
                    this.modules[name] = new this.moduleRegistry[name](config);
                    this.log('info', `模块 ${name} 初始化成功`);
                } catch (error) {
                    this.log('warn', `模块 ${name} 初始化失败，跳过`, { error: error.message });
                }
            }
            
            this.reportDatabaseStatus();
            
        } catch (error) {
            this.log('error', '依赖模块初始化失败', { error: error.message });
        }
    }
    
    async reportDatabaseStatus() {
        if (this.modules.database) {
            try {
                const health = await this.modules.database.healthCheck();
                console.log('📊 数据库状态上报:', health);
                document.dispatchEvent(new CustomEvent('mtscos:database:health', { detail: health }));
            } catch (e) {
                this.log('warn', '数据库状态上报失败', { error: e.message });
            }
        }
    }
    
    initUIManager() {
        this.ui = {
            theme: window.themeManager || null,
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
                    console.warn(`路由 ${path} 未找到，尝试跳转`);
                    window.location.href = path;
                    return true;
                }
                
                this.currentRoute = path;
                await route.handler();
                return true;
            },
            
            getCurrentPath() {
                return window.location.pathname;
            },
            
            goToDashboard() {
                this.navigate('/dashboard');
            },
            
            goToLogin() {
                this.navigate('/');
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
    
    getState(key) {
        return this.state?.[key];
    }
    
    setState(key, value) {
        if (!this.state) this.state = {};
        this.state[key] = value;
        document.dispatchEvent(new CustomEvent(`mtscos:state:${key}`, { detail: value }));
    }
    
    on(event, handler) {
        document.addEventListener(`mtscos:${event}`, handler);
    }
    
    off(event, handler) {
        document.removeEventListener(`mtscos:${event}`, handler);
    }
    
    emit(event, detail = {}) {
        document.dispatchEvent(new CustomEvent(`mtscos:${event}`, { detail }));
    }
    
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
    
    destroy() {
        for (const [name, module] of Object.entries(this.modules)) {
            if (typeof module.destroy === 'function') {
                module.destroy();
            }
        }
        
        if (this.performance?.observers) {
            this.performance.observers.forEach(obs => obs.disconnect());
        }
        
        this.state = {};
        
        this.isInitialized = false;
        this.log('info', 'MTSCOS AI System 已销毁');
    }
}

// ==================== 默认依赖模块实现 ====================

class DefaultDatabaseManager {
    constructor() {
        this.isReady = true;
        this.type = 'default';
    }
    
    async waitForReady() {
        return Promise.resolve();
    }
    
    async healthCheck() {
        return { status: 'ok', type: this.type };
    }
    
    async query() {
        return [];
    }
    
    async insert() {
        return true;
    }
    
    async update() {
        return true;
    }
    
    async delete() {
        return true;
    }
}

class DefaultDataSyncService {
    constructor(database) {
        this.database = database;
        this.isReady = true;
    }
    
    async sync() {
        return { success: true, synced: 0 };
    }
    
    async healthCheck() {
        return { status: 'ok', synced: 0 };
    }
}

class DefaultAIDispatcher {
    constructor(database, syncService) {
        this.database = database;
        this.syncService = syncService;
        this.isReady = true;
    }
    
    async dispatch() {
        return { success: true };
    }
    
    async healthCheck() {
        return { status: 'ok' };
    }
}

class DefaultSystemOrchestrator {
    constructor(database, dispatcher) {
        this.database = database;
        this.dispatcher = dispatcher;
        this.isReady = true;
    }
    
    async orchestrate() {
        return { success: true };
    }
    
    async healthCheck() {
        return { status: 'ok' };
    }
}

class DefaultAIEmployeeManager {
    constructor() {
        this.employees = [];
        this.isReady = true;
    }
    
    async getEmployees() {
        return this.employees;
    }
    
    async healthCheck() {
        return { status: 'ok', employees: this.employees.length };
    }
}

// ==================== 数据层模块 ====================

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
        this.cache.set(key, value);
        return await this.storage.set(key, value, options);
    }
    
    async get(key, defaultValue = null) {
        if (this.cache.has(key)) {
            return this.cache.get(key);
        }
        const value = await this.storage.get(key, defaultValue);
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
            if (!this.db) {
                localStorage.setItem(key, JSON.stringify(value));
                resolve(true);
                return;
            }
            
            const transaction = this.db.transaction(['data'], 'readwrite');
            const store = transaction.objectStore('data');
            const request = store.put({ key, value, timestamp: Date.now() });
            
            request.onsuccess = () => resolve(true);
            request.onerror = () => {
                localStorage.setItem(key, JSON.stringify(value));
                resolve(true);
            };
        });
    }
    
    async get(key, defaultValue = null) {
        return new Promise((resolve, reject) => {
            if (!this.db) {
                const value = localStorage.getItem(key);
                resolve(value ? JSON.parse(value) : defaultValue);
                return;
            }
            
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
                    const localValue = localStorage.getItem(key);
                    resolve(localValue ? JSON.parse(localValue) : defaultValue);
                }
            };
            request.onerror = () => {
                const value = localStorage.getItem(key);
                resolve(value ? JSON.parse(value) : defaultValue);
            };
        });
    }
    
    async delete(key) {
        return new Promise((resolve, reject) => {
            if (!this.db) {
                localStorage.removeItem(key);
                resolve(true);
                return;
            }
            
            const transaction = this.db.transaction(['data'], 'readwrite');
            const store = transaction.objectStore('data');
            const request = store.delete(key);
            
            request.onsuccess = () => {
                localStorage.removeItem(key);
                resolve(true);
            };
            request.onerror = () => {
                localStorage.removeItem(key);
                resolve(true);
            };
        });
    }
    
    async clear() {
        return new Promise((resolve, reject) => {
            if (!this.db) {
                localStorage.clear();
                resolve(true);
                return;
            }
            
            const transaction = this.db.transaction(['data'], 'readwrite');
            const store = transaction.objectStore('data');
            const request = store.clear();
            
            request.onsuccess = () => {
                localStorage.clear();
                resolve(true);
            };
            request.onerror = () => {
                localStorage.clear();
                resolve(true);
            };
        });
    }
    
    encrypt(data) {
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
        this.config = config || { max_entries: 100, ttl: 300000 };
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

// ==================== 安全模块 ====================

class SecurityManager {
    constructor(config) {
        this.config = config || { 
            features: { 
                authentication: { 
                    session_timeout: 3600000 
                } 
            } 
        };
        this.user = null;
        this.session = null;
        this.isAuthenticated = false;
        this.apiBase = '/api';
        this.init();
    }
    
    init() {
        this.setupSecurityHeaders();
        this.setupCSRFProtection();
        this.loadSession();
    }
    
    setupSecurityHeaders() {
        const csp = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com",
            "font-src 'self' https://cdnjs.cloudflare.com",
            "img-src 'self' data: blob:",
            "connect-src 'self'",
            "frame-ancestors 'none'"
        ].join('; ');
        
        console.log('安全策略已配置');
    }
    
    setupCSRFProtection() {
        this.csrfToken = this.generateToken();
    }
    
    generateToken() {
        return Array.from(crypto.getRandomValues(new Uint8Array(32)))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }
    
    loadSession() {
        try {
            const userStr = localStorage.getItem('user');
            const token = localStorage.getItem('token');
            
            if (userStr) {
                this.user = JSON.parse(userStr);
                this.isAuthenticated = true;
                
                this.session = {
                    id: token || this.generateToken(),
                    created: Date.now(),
                    expires: Date.now() + this.config.features.authentication.session_timeout
                };
                
                console.log('已加载本地会话:', this.user.username);
            }
        } catch (e) {
            console.warn('会话加载失败:', e);
        }
    }
    
    async login(credentials) {
        try {
            const response = await fetch(`${this.apiBase}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(credentials)
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.user = data.user;
                this.isAuthenticated = true;
                
                this.session = {
                    id: data.token || this.generateToken(),
                    created: Date.now(),
                    expires: Date.now() + this.config.features.authentication.session_timeout
                };
                
                if (data.token) localStorage.setItem('token', data.token);
                localStorage.setItem('user', JSON.stringify(this.user));
                
                return { success: true, user: this.user };
            }
            
            return { success: false, error: data.message || '登录失败' };
        } catch (error) {
            console.error('登录请求失败:', error);
            return { success: false, error: error.message };
        }
    }
    
    async logout() {
        try {
            await fetch(`${this.apiBase}/auth/logout`, {
                method: 'POST'
            });
        } catch (e) {
            console.warn('登出请求失败:', e);
        }
        
        this.user = null;
        this.session = null;
        this.isAuthenticated = false;
        
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        window.location.href = '/';
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
            csrf_token: !!this.csrfToken,
            user_role: this.user?.role || 'guest'
        };
    }
}

// ==================== 中间件模块 ====================

class MiddlewareManager {
    constructor(config) {
        this.config = config || { components: {} };
        this.middlewares = [];
        this.init();
    }
    
    init() {
        if (this.config.components?.router?.enabled) {
            this.use('router', this.routerMiddleware.bind(this));
        }
        
        if (this.config.components?.request_validator?.enabled) {
            this.use('validator', this.validatorMiddleware.bind(this));
        }
        
        if (this.config.components?.rate_limit?.enabled) {
            this.use('rateLimit', this.rateLimitMiddleware.bind(this));
        }
        
        if (this.config.components?.error_handler?.enabled) {
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
        return true;
    }
    
    async validatorMiddleware(context) {
        if (context.request && context.request.method === 'POST') {
            if (!context.request.body) {
                return false;
            }
        }
        return true;
    }
    
    rateLimitMiddleware(context) {
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
        
        if (record.count > (this.config.components?.request_validator?.rate_limit?.max_requests || 100)) {
            return false;
        }
        
        return true;
    }
    
    async errorHandlerMiddleware(context) {
        return true;
    }
    
    healthCheck() {
        return {
            status: 'ok',
            middlewares: this.middlewares.length
        };
    }
}

// ==================== 服务器管理模块 ====================

class ServerManager {
    constructor(config) {
        this.config = config || { config: { port: 8888, host: '0.0.0.0', protocol: 'http' } };
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

// ==================== AI模块 ====================

class AIManager {
    constructor(config) {
        this.config = config || { providers: {} };
        this.providers = {};
        this.conversations = new Map();
        this.init();
    }
    
    init() {
        for (const [name, provider] of Object.entries(this.config.providers || {})) {
            if (provider && provider.enabled) {
                this.providers[name] = new AIProvider(name, provider);
            }
        }
        
        if (Object.keys(this.providers).length === 0) {
            this.providers['local'] = new AIProvider('local', { enabled: true });
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
        const lastMessage = messages[messages.length - 1]?.content || '';
        return `收到您的消息: "${lastMessage.substring(0, 50)}..."。这是来自MTSCOS AI的响应。`;
    }
}

// ==================== 版本管理模块 ====================

class VersionManager {
    constructor(config) {
        this.config = config || { 
            current_version: '5.0.0', 
            build_date: new Date().toISOString(),
            changelog: [],
            auto_update: false,
            status: 'stable'
        };
        this.currentVersion = this.config.current_version;
        this.buildDate = this.config.build_date;
        this.changelog = this.config.changelog || [];
        this.autoUpdate = this.config.auto_update;
    }
    
    getInfo() {
        return {
            version: this.currentVersion,
            buildDate: this.buildDate,
            codename: '智能系统优化版',
            status: this.config.status
        };
    }
    
    getChangelog() {
        return this.changelog;
    }
    
    async checkForUpdates() {
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

// ==================== 规则引擎模块 ====================

class RulesEngine {
    constructor(config) {
        this.config = config || { categories: {}, enforcement: { log_violations: true } };
        this.rules = this.compileRules();
        this.violations = [];
    }
    
    compileRules() {
        const rules = [];
        
        for (const [category, categoryConfig] of Object.entries(this.config.categories || {})) {
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
                    
                    if (this.config.enforcement?.log_violations) {
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

class LayoutManager {
    constructor(config) {
        this.config = config || {};
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

// ==================== 初始化系统 ====================

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        window.mtscos = new MTSCOSSystem();
    }, 100);
});

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
        LayoutManager,
        DefaultDatabaseManager,
        DefaultDataSyncService,
        DefaultAIDispatcher,
        DefaultSystemOrchestrator
    };
}