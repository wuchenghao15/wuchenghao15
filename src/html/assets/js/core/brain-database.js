/**
 * MTSCOS AI System - 脑库数据库
 * 版本: 1.0.0
 * 描述: 专业AI知识库，存储修复案例、最佳实践和技术文档
 */
class BrainDatabase {
    constructor() {
        this.dbName = 'MTSCOS_BRAIN_DB';
        this.dbVersion = 1;
        this.db = null;
        this.isReady = false;
        this.collections = [
            { name: 'fix_cases', keyPath: 'id', autoIncrement: false },
            { name: 'best_practices', keyPath: 'id', autoIncrement: false },
            { name: 'tech_patterns', keyPath: 'id', autoIncrement: false },
            { name: 'error_solutions', keyPath: 'id', autoIncrement: false },
            { name: 'architecture_docs', keyPath: 'id', autoIncrement: false },
            { name: 'learning_materials', keyPath: 'id', autoIncrement: false }
        ];
        this.init();
    }
    async init() {
        try {
            this.db = await this.openDatabase();
            this.isReady = true;
            console.log('✅ 脑库数据库初始化成功');
            // 初始化默认数据
            await this.initBrainData();
            // 触发就绪事件
            document.dispatchEvent(new CustomEvent('mtscos:brain:ready'));
        } catch (error) {
            console.error('❌ 脑库数据库初始化失败:', error);
        }
    }
    async openDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                for (const collection of this.collections) {
                    if (!db.objectStoreNames.contains(collection.name)) {
                        db.createObjectStore(collection.name, {
                            keyPath: collection.keyPath,
                            autoIncrement: collection.autoIncrement
                        });
                    }
                }
            };
        });
    }
    async initBrainData() {
        // 检查是否已有数据
        const existingCases = await this.getAll('fix_cases');
        if (existingCases.length === 0) {
            await this.bulkAdd('fix_cases', this.getFixCases());
            console.log('📚 修复案例已导入脑库');
        }
        const existingPractices = await this.getAll('best_practices');
        if (existingPractices.length === 0) {
            // 初始化最佳实践
            await this.bulkAdd('best_practices', this.getBestPractices());
            console.log('💡 最佳实践已导入脑库');
        }
        const existingPatterns = await this.getAll('tech_patterns');
        if (existingPatterns.length === 0) {
            // 初始化技术模式
            await this.bulkAdd('tech_patterns', this.getTechPatterns());
            console.log('🔧 技术模式已导入脑库');
        }
        const existingErrors = await this.getAll('error_solutions');
        if (existingErrors.length === 0) {
            // 初始化错误解决方案
            await this.bulkAdd('error_solutions', this.getErrorSolutions());
            console.log('❌ 错误解决方案已导入脑库');
        }
        const existingArch = await this.getAll('architecture_docs');
        if (existingArch.length === 0) {
            // 初始化架构文档
            await this.bulkAdd('architecture_docs', this.getArchitectureDocs());
            console.log('📐 架构文档已导入脑库');
        }
        const existingMaterials = await this.getAll('learning_materials');
        if (existingMaterials.length === 0) {
            // 初始化学习材料
            await this.bulkAdd('learning_materials', this.getLearningMaterials());
            console.log('📖 学习材料已导入脑库');
        }
    }
    // ==================== 基础操作 ====================
    async add(collectionName, data) {
        return this.transaction(collectionName, 'readwrite', (store) => {
            return store.add(data);
        });
    }
    async put(collectionName, data) {
        return this.transaction(collectionName, 'readwrite', (store) => {
            return store.put(data);
        });
    }
    async bulkAdd(collectionName, dataArray) {
        return this.transaction(collectionName, 'readwrite', (store) => {
            const results = [];
            dataArray.forEach(data => {
                results.push(store.add(data));
            });
            return results;
        });
    }
    async get(collectionName, key) {
        return this.transaction(collectionName, 'readonly', (store) => {
            return store.get(key);
        });
    }
    async getAll(collectionName) {
        return this.transaction(collectionName, 'readonly', (store) => {
            return store.getAll();
        });
    }
    async delete(collectionName, key) {
        return this.transaction(collectionName, 'readwrite', (store) => {
            return store.delete(key);
        });
    }
    async clear(collectionName) {
        return this.transaction(collectionName, 'readwrite', (store) => {
            return store.clear();
        });
    }
    async search(collectionName, keyword) {
        const items = await this.getAll(collectionName);
        const lowerKeyword = keyword.toLowerCase();
        return items.filter(item => {
            const searchText = JSON.stringify(item).toLowerCase();
            return searchText.includes(lowerKeyword);
        });
    }
    async transaction(collectionName, mode, callback) {
        if (!this.db) {
            throw new Error('脑库数据库未初始化');
        }
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([collectionName], mode);
            const store = transaction.objectStore(collectionName);
            try {
                const request = callback(store);
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            } catch (error) {
                reject(error);
            }
        });
    }
    // ==================== 脑库数据定义 ====================
    getFixCases() {
        return [
            {
                id: 'FIX-001',
                title: '类重复定义问题修复',
                category: 'javascript',
                severity: 'high',
                description: 'Identifier已声明错误，类在多个文件中重复定义',
                rootCause: 'AIEmployeeManager类在mtscos-core.js和ai-employee-manager.js中都有定义',
                symptoms: [
                    'SyntaxError: Identifier has already been declared',
                    '页面无法加载',
                    'JavaScript运行时错误'
                ],
                solution: {
                    steps: [
                        '使用grep查找重复的类定义',
                        '删除重复的定义，保留一个源',
                        '验证语法正确性'
                    ],
                    code: {
                        before: 'class AIEmployeeManager { ... }',
                        after: '// 已移至 ai-employee-manager.js'
                    }
                },
                verification: [
                    'node --check 检查语法',
                    '刷新页面无错误',
                    '控制台无重复声明错误'
                ],
                relatedCases: ['FIX-002', 'FIX-003'],
                tags: ['javascript', 'class', 'duplicate', 'declaration'],
                createdAt: Date.now(),
                updatedAt: Date.now()
            },
            {
                id: 'FIX-002',
                title: '异步依赖管理问题修复',
                category: 'async',
                severity: 'critical',
                description: '模块初始化时数据库未就绪，但其他模块已尝试调用数据库方法',
                rootCause: '异步初始化顺序错误，缺少等待机制',
                symptoms: [
                    'TypeError: this.database.getAllAIEmployees is not a function',
                    'TypeError: this.database.addLog is not a function',
                    'TypeError: this.database.addSyncRecord is not a function'
                ],
                solution: {
                    steps: [
                        '在DatabaseManager中添加waitForReady()方法',
                        '在依赖模块的init()中调用waitForReady()',
                        '在MTSCOSSystem中使用setTimeout延迟初始化'
                    ],
                    code: {
                        database: `async waitForReady() {
    if (this.isReady) return true;
    if (this.initPromise) {
        await this.initPromise;
    }
    return this.isReady;
}`,
                        service: `async init() {
    await this.database.waitForReady();
    // ... 初始化逻辑
}`
                    }
                },
                verification: [
                    '页面正常加载',
                    '控制台显示所有模块初始化成功',
                    '数据库操作正常执行'
                ],
                relatedCases: ['FIX-001', 'FIX-003', 'FIX-004'],
                tags: ['async', 'await', 'promise', 'database', 'initialization'],
                createdAt: Date.now(),
                updatedAt: Date.now()
            },
            {
                id: 'FIX-003',
                title: 'setTimeout延迟初始化模式',
                category: 'pattern',
                severity: 'medium',
                description: '使用setTimeout解决模块初始化时序问题',
                rootCause: '同步执行导致依赖模块在数据库就绪前被创建',
                symptoms: [
                    '模块间依赖失败',
                    'this.database is undefined',
                    '初始化顺序混乱'
                ],
                solution: {
                    steps: [
                        '第一阶段立即创建数据库实例',
                        '使用setTimeout延迟100ms执行依赖模块初始化',
                        '在setTimeout回调中等待数据库就绪'
                    ],
                    code: {
                        pattern: `async initializeModules() {
    // 第一阶段
    this.modules.database = new DatabaseManager();
    // 第二阶段：延迟初始化
    setTimeout(() => this.initializeDependentModules(), 100);
}
async initializeDependentModules() {
    await this.modules.database.waitForReady();
    // 初始化依赖模块...
}`
                    }
                },
                verification: [
                    '数据库就绪后再初始化其他模块',
                    '无undefined错误',
                    '模块按正确顺序初始化'
                ],
                relatedCases: ['FIX-002', 'FIX-004'],
                tags: ['setTimeout', 'timing', 'initialization', 'pattern'],
                createdAt: Date.now(),
                updatedAt: Date.now()
            },
            {
                id: 'FIX-004',
                title: 'initPromise异步初始化模式',
                category: 'pattern',
                severity: 'medium',
                description: '使用initPromise模式确保模块完全初始化后再继续',
                rootCause: '异步init()方法未被正确等待',
                symptoms: [
                    '模块方法调用失败',
                    'isReady标志不准确',
                    '竞态条件'
                ],
                solution: {
                    steps: [
                        '在constructor中创建initPromise',
                        'init()方法返回Promise',
                        '在其他地方await initPromise'
                    ],
                    code: {
                        pattern: `class Module {
    constructor(dep) {
        this.dep = dep;
        this.initPromise = this.init();
        this.isReady = false;
    }
    async init() {
        await this.dep.waitForReady();
        // ... 初始化逻辑
        this.isReady = true;
        return true;
    }
}
// 使用
const module = new Module(dep);
await module.initPromise;`
                    }
                },
                verification: [
                    'initPromise正确解析',
                    'isReady标志准确',
                    '无竞态条件'
                ],
                relatedCases: ['FIX-002', 'FIX-003'],
                tags: ['promise', 'async', 'initialization', 'pattern'],
                createdAt: Date.now(),
                updatedAt: Date.now()
            },
            {
                id: 'FIX-005',
                title: 'net::ERR_ABORTED错误排查与修复',
                category: 'browser',
                severity: 'critical',
                description: '浏览器显示ERR_ABORTED，通常由JavaScript错误引起',
                rootCause: '多个JavaScript运行时错误导致页面加载失败',
                symptoms: [
                    '页面无法加载',
                    '控制台显示多个TypeError',
                    '浏览器显示ERR_ABORTED'
                ],
                solution: {
                    steps: [
                        '检查服务器状态是否正常',
                        '检查JavaScript语法错误',
                        '检查模块初始化顺序',
                        '修复所有运行时错误',
                        '清除浏览器缓存重试'
                    ],
                    commands: {
                        server: 'curl -I http://${config.host}:${config.port}/',
                        syntax: 'node --check *.js',
                        cache: '强制刷新 Ctrl+Shift+R / Cmd+Shift+R'
                    }
                },
                verification: [
                    'HTTP 200 OK响应',
                    '所有JS文件语法正确',
                    '页面正常加载无错误'
                ],
                relatedCases: ['FIX-001', 'FIX-002', 'FIX-003', 'FIX-004'],
                tags: ['browser', 'network', 'http', 'abort', 'loading'],
                createdAt: Date.now(),
                updatedAt: Date.now()
            }
        ];
    }
    getBestPractices() {
        return [
            {
                id: 'BP-001',
                title: '模块化依赖管理最佳实践',
                category: 'architecture',
                description: '如何正确管理模块间的依赖关系',
                practices: [
                    {
                        title: '分层初始化',
                        content: '按依赖层级从上到下初始化：核心层 → 数据层 → 服务层 → UI层',
                        example: `DatabaseManager (核心)
    ↓
DataSyncService (数据)
    ↓
AIDispatcher (服务)
    ↓
SystemOrchestrator (编排)`
                    },
                    {
                        title: '等待机制',
                        content: '每个模块应该提供waitForReady()或类似方法供外部调用',
                        example: `async waitForReady() {
    if (this.isReady) return true;
    if (this.initPromise) {
        await this.initPromise;
    }
    return this.isReady;
}`
                    },
                    {
                        title: '错误隔离',
                        content: '单个模块初始化失败不应影响其他模块',
                        example: `try {
    await module.init();
} catch (error) {
    console.error('模块初始化失败:', error);
    // 继续初始化其他模块
}`
                    },
                    {
                        title: '事件通知',
                        content: '使用CustomEvent通知模块就绪状态',
                        example: `document.dispatchEvent(
    new CustomEvent('mtscos:database:ready')
);`
                    }
                ],
                tags: ['architecture', 'dependency', 'module', 'initialization'],
                createdAt: Date.now()
            },
            {
                id: 'BP-002',
                title: 'JavaScript类定义最佳实践',
                category: 'javascript',
                description: '避免类重复定义和作用域问题',
                practices: [
                    {
                        title: '单一职责',
                        content: '每个类只负责一个功能，避免功能重叠'
                    },
                    {
                        title: '唯一来源',
                        content: '类只在一个文件中定义，其他文件引用',
                        example: `// 正确做法
// module-a.js
class MyClass { }
// module-b.js
// 不重复定义，直接使用
// import { MyClass } from './module-a.js'`
                    },
                    {
                        title: '命名空间',
                        content: '使用命名空间或模块模式避免全局污染',
                        example: `const MyNamespace = {
    MyClass: class { }
};`
                    },
                    {
                        title: 'ESLint规则',
                        content: '配置ESLint规则防止重复声明',
                        example: `"no-redeclare": "error"`
                    }
                ],
                tags: ['javascript', 'class', 'oop', 'naming'],
                createdAt: Date.now()
            },
            {
                id: 'BP-003',
                title: '异步编程最佳实践',
                category: 'async',
                description: '正确处理Promise和异步初始化',
                practices: [
                    {
                        title: '避免回调地狱',
                        content: '使用async/await代替多层嵌套回调'
                    },
                    {
                        title: '错误处理',
                        content: '每个await都应该有try-catch',
                        example: `try {
    await someAsyncOperation();
} catch (error) {
    console.error('操作失败:', error);
}`
                    },
                    {
                        title: 'Promise链',
                        content: '正确链接Promise，确保顺序执行',
                        example: `await step1();
await step2();
await step3();
// 全部完成`
                    },
                    {
                        title: '超时处理',
                        content: '为异步操作设置超时',
                        example: `Promise.race([
    asyncOperation(),
    new Promise((_, reject) => 
        setTimeout(() => reject('超时'), 5000)
    )
])`
                    }
                ],
                tags: ['async', 'promise', 'await', 'error-handling'],
                createdAt: Date.now()
            }
        ];
    }
    getTechPatterns() {
        return [
            {
                id: 'TP-001',
                title: '分层架构模式',
                category: 'architecture',
                description: '将系统分为核心层、数据层、服务层、UI层',
                layers: [
                    { name: '核心层', modules: ['DatabaseManager'], priority: 0 },
                    { name: '数据层', modules: ['DataSyncService'], priority: 1 },
                    { name: '服务层', modules: ['AIDispatcher', 'SecurityManager'], priority: 2 },
                    { name: '编排层', modules: ['SystemOrchestrator'], priority: 3 },
                    { name: 'UI层', modules: ['ThemeManager', 'LayoutManager'], priority: 4 }
                ],
                initialization: '从上到下逐层初始化，下层就绪后初始化上层',
                tags: ['architecture', 'layer', 'initialization'],
                createdAt: Date.now()
            },
            {
                id: 'TP-002',
                title: '依赖注入模式',
                category: 'pattern',
                description: '通过构造函数将依赖注入模块',
                example: `class AIDispatcher {
    constructor(database, syncService) {
        this.database = database;
        this.syncService = syncService;
    }
}
// 使用
const dispatcher = new AIDispatcher(
    database,
    syncService
);`,
                benefits: [
                    '提高模块独立性',
                    '便于单元测试',
                    '明确依赖关系'
                ],
                tags: ['pattern', 'di', 'dependency', 'injection'],
                createdAt: Date.now()
            },
            {
                id: 'TP-003',
                title: '观察者模式',
                category: 'pattern',
                description: '使用事件机制实现模块间通信',
                example: `// 发送事件
document.dispatchEvent(
    new CustomEvent('mtscos:database:ready')
);
// 监听事件
document.addEventListener(
    'mtscos:database:ready',
    () => console.log('数据库就绪')
);`,
                useCases: [
                    '模块就绪通知',
                    '状态变更通知',
                    '跨模块通信'
                ],
                tags: ['pattern', 'observer', 'event', 'communication'],
                createdAt: Date.now()
            },
            {
                id: 'TP-004',
                title: '工厂模式',
                category: 'pattern',
                description: '使用工厂函数创建模块实例',
                example: `const ModuleFactory = {
    createDatabase() {
        return new DatabaseManager();
    },
    createSync(db) {
        return new DataSyncService(db);
    },
    async createAll() {
        const db = this.createDatabase();
        await db.waitForReady();
        const sync = this.createSync(db);
        return { db, sync };
    }
};`,
                tags: ['pattern', 'factory', 'creation'],
                createdAt: Date.now()
            }
        ];
    }
    getErrorSolutions() {
        return [
            {
                id: 'ERR-001',
                error: 'SyntaxError: Identifier has already been declared',
                category: 'javascript',
                cause: '同一标识符在多个地方定义',
                solution: '删除重复定义，保留一个源',
                steps: [
                    '使用grep查找重复定义',
                    '确认保留的定义位置',
                    '删除其他位置的重复定义',
                    '验证语法'
                ]
            },
            {
                id: 'ERR-002',
                error: 'TypeError: Cannot read property of undefined',
                category: 'javascript',
                cause: '访问undefined对象的属性或方法',
                solution: '确保对象初始化后再访问',
                steps: [
                    '检查对象是否已定义',
                    '使用可选链?.操作符',
                    '添加空值检查',
                    '确保初始化顺序正确'
                ]
            },
            {
                id: 'ERR-003',
                error: 'TypeError: this.database.xxx is not a function',
                category: 'async',
                cause: '数据库未初始化完成就调用方法',
                solution: '使用waitForReady()等待数据库就绪',
                steps: [
                    '在调用前添加await db.waitForReady()',
                    '确保数据库initPromise存在',
                    '检查isReady标志'
                ]
            },
            {
                id: 'ERR-004',
                error: 'net::ERR_ABORTED',
                category: 'browser',
                cause: '页面加载过程中JavaScript错误',
                solution: '修复所有JavaScript运行时错误',
                steps: [
                    '检查浏览器控制台错误',
                    '修复所有TypeError',
                    '修复所有SyntaxError',
                    '清除缓存重试'
                ]
            },
            {
                id: 'ERR-005',
                error: 'Address already in use',
                category: 'server',
                cause: '端口被占用',
                solution: '终止占用端口的进程',
                steps: [
                    '使用lsof查找占用进程',
                    'kill -9终止进程',
                    '等待片刻后重新启动'
                ]
            }
        ];
    }
    getArchitectureDocs() {
        return [
            {
                id: 'ARCH-001',
                title: 'MTSCOS系统架构文档',
                version: '4.3.0',
                sections: [
                    {
                        name: '系统概览',
                        content: 'MTSCOS是一个多租户智能云操作系统，采用模块化架构设计'
                    },
                    {
                        name: '核心模块',
                        modules: [
                            { name: 'DatabaseManager', desc: '数据持久化' },
                            { name: 'DataSyncService', desc: '数据同步' },
                            { name: 'AIDispatcher', desc: 'AI任务调度' },
                            { name: 'SystemOrchestrator', desc: '系统编排' }
                        ]
                    },
                    {
                        name: '初始化流程',
                        content: 'DatabaseManager → DataSyncService → AIDispatcher → SystemOrchestrator → UI'
                    }
                ],
                tags: ['architecture', 'mtscos', 'system'],
                createdAt: Date.now()
            },
            {
                id: 'ARCH-002',
                title: '模块依赖关系图',
                description: '展示各模块间的依赖关系',
                dependencies: [
                    { from: 'DataSyncService', to: 'DatabaseManager' },
                    { from: 'AIDispatcher', to: 'DatabaseManager' },
                    { from: 'AIDispatcher', to: 'DataSyncService' },
                    { from: 'SystemOrchestrator', to: 'DatabaseManager' },
                    { from: 'SystemOrchestrator', to: 'AIDispatcher' },
                    { from: 'MTSCOSSystem', to: 'DatabaseManager' }
                ],
                tags: ['architecture', 'dependency', 'diagram'],
                createdAt: Date.now()
            }
        ];
    }
    getLearningMaterials() {
        return [
            {
                id: 'LEARN-001',
                title: 'JavaScript异步编程入门',
                category: 'tutorial',
                topics: [
                    'Promise基础',
                    'async/await用法',
                    '错误处理',
                    '并发控制'
                ],
                examples: [
                    {
                        title: 'async函数基础',
                        code: `async function fetchData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('获取数据失败:', error);
    }
}`
                    }
                ],
                tags: ['javascript', 'async', 'tutorial', 'beginner'],
                createdAt: Date.now()
            },
            {
                id: 'LEARN-002',
                title: 'IndexedDB数据库开发',
                category: 'tutorial',
                topics: [
                    '数据库打开和版本管理',
                    '对象存储创建',
                    'CRUD操作',
                    '索引和查询'
                ],
                examples: [
                    {
                        title: '基础数据库操作',
                        code: `const db = await openDatabase('MyDB', 1, (db) => {
    db.createObjectStore('items', { keyPath: 'id' });
});
// 添加数据
await db.add('items', { id: 1, name: 'item' });
// 获取数据
const item = await db.get('items', 1);`
                    }
                ],
                tags: ['indexedDB', 'database', 'storage', 'tutorial'],
                createdAt: Date.now()
            },
            {
                id: 'LEARN-003',
                title: '模块化JavaScript设计',
                category: 'tutorial',
                topics: [
                    '模块模式',
                    'ES6模块',
                    '依赖管理',
                    '最佳实践'
                ],
                tags: ['javascript', 'module', 'design', 'tutorial'],
                createdAt: Date.now()
            }
        ];
    }
    // ==================== 查询接口 ====================
    async getFixCase(id) {
        return await this.get('fix_cases', id);
    }
    async getAllFixCases() {
        return await this.getAll('fix_cases');
    }
    async getBestPractice(id) {
        return await this.get('best_practices', id);
    }
    async getAllBestPractices() {
        return await this.getAll('best_practices');
    }
    async getTechPattern(id) {
        return await this.get('tech_patterns', id);
    }
    async getAllTechPatterns() {
        return await this.getAll('tech_patterns');
    }
    async getErrorSolution(id) {
        return await this.get('error_solutions', id);
    }
    async getAllErrorSolutions() {
        return await this.getAll('error_solutions');
    }
    async searchBrain(keyword) {
        const results = {
            fixCases: await this.search('fix_cases', keyword),
            bestPractices: await this.search('best_practices', keyword),
            techPatterns: await this.search('tech_patterns', keyword),
            errorSolutions: await this.search('error_solutions', keyword),
            architectureDocs: await this.search('architecture_docs', keyword),
            learningMaterials: await this.search('learning_materials', keyword)
        };
        // 合并并添加来源标识
        const merged = [
            ...results.fixCases.map(item => ({ ...item, collection: 'fix_cases' })),
            ...results.bestPractices.map(item => ({ ...item, collection: 'best_practices' })),
            ...results.techPatterns.map(item => ({ ...item, collection: 'tech_patterns' })),
            ...results.errorSolutions.map(item => ({ ...item, collection: 'error_solutions' })),
            ...results.architectureDocs.map(item => ({ ...item, collection: 'architecture_docs' })),
            ...results.learningMaterials.map(item => ({ ...item, collection: 'learning_materials' }))
        ];
        return merged;
    }
    // ==================== 导出接口 ====================
    async exportBrain() {
        const data = {
            exportedAt: Date.now(),
            version: '1.0.0',
            fixCases: await this.getAll('fix_cases'),
            bestPractices: await this.getAll('best_practices'),
            techPatterns: await this.getAll('tech_patterns'),
            errorSolutions: await this.getAll('error_solutions'),
            architectureDocs: await this.getAll('architecture_docs'),
            learningMaterials: await this.getAll('learning_materials')
        };
        // 保存到本地存储
        localStorage.setItem('mtscos_brain_backup', JSON.stringify(data));
        return data;
    }
    async getStats() {
        return {
            totalItems: {
                fixCases: (await this.getAll('fix_cases')).length,
                bestPractices: (await this.getAll('best_practices')).length,
                techPatterns: (await this.getAll('tech_patterns')).length,
                errorSolutions: (await this.getAll('error_solutions')).length,
                architectureDocs: (await this.getAll('architecture_docs')).length,
                learningMaterials: (await this.getAll('learning_materials')).length
            },
            total: Object.values(await this.getStats()).reduce((a, b) => 
                typeof b === 'object' ? a + Object.values(b).reduce((x, y) => x + y, 0) : a + b, 0
            ),
            lastUpdated: Date.now()
        };
    }
    // ==================== 健康检查 ====================
    async healthCheck() {
        return {
            status: this.isReady ? 'ok' : 'error',
            database: this.dbName,
            version: this.dbVersion,
            collections: this.collections.map(c => c.name)
        };
    }
}
// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BrainDatabase;
}