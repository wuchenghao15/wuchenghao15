// 路由集成器 - 整合路由系统与组件系统
class RouterIntegrator {
  constructor(options = {}) {
    // 路由系统引用
    this.router = options.router || null;
    
    // 导航管理器引用
    this.navigationManager = options.navigationManager || null;
    
    // 组件系统引用
    this.componentSystem = options.componentSystem || null;
    
    // 页面组件配置器引用
    this.pageComponentConfigurator = options.pageComponentConfigurator || null;
    
    // 智能规划整合器引用
    this.intelligentPlannerIntegrator = options.intelligentPlannerIntegrator || null;
    
    // 集成配置
    this.config = {
      autoInitialize: options.autoInitialize !== false,
      componentRegistryPath: options.componentRegistryPath || '/assets/js/modules/component-registry.js',
      routesConfigPath: options.routesConfigPath || '/assets/config/routes-config.json',
      pageComponentsConfigPath: options.pageComponentsConfigPath || '/assets/config/page-components-config.json',
      debug: options.debug || false,
      ...options.config
    };
    
    // 组件映射
    this.componentMap = new Map();
    
    // 路由中间件
    this.middlewares = [];
    
    // 初始化状态
    this.isInitialized = false;
    this.initializationPromise = null;
    
    // 组件加载缓存
    this.componentLoadCache = new Map();
    
    // 错误处理器
    this.errorHandlers = {
      componentNotFound: this.defaultComponentNotFoundHandler,
      routeError: this.defaultRouteErrorHandler,
      initializationError: this.defaultInitializationErrorHandler
    };
  }

  /**
   * 初始化路由集成器
   */
  async initialize() {
    if (this.isInitialized) {
      console.warn('路由集成器已经初始化');
      return true;
    }
    
    // 防止重复初始化
    if (this.initializationPromise) {
      return this.initializationPromise;
    }
    
    this.initializationPromise = this.performInitialization();
    return this.initializationPromise;
  }

  /**
   * 执行初始化
   */
  async performInitialization() {
    try {
      console.log('初始化路由集成器...');
      
      // 验证依赖
      await this.validateDependencies();
      
      // 加载配置
      await this.loadConfigurations();
      
      // 注册组件
      await this.registerComponents();
      
      // 设置路由中间件
      await this.setupMiddlewares();
      
      // 配置路由守卫
      await this.configureRouteGuards();
      
      // 初始化路由系统
      await this.initializeRouter();
      
      // 初始化导航管理器
      await this.initializeNavigationManager();
      
      // 连接系统组件
      await this.connectSystems();
      
      // 注册错误处理
      await this.registerErrorHandlers();
      
      // 设置调试模式
      if (this.config.debug) {
        this.enableDebugMode();
      }
      
      this.isInitialized = true;
      console.log('路由集成器初始化完成');
      
      return true;
    } catch (error) {
      console.error('初始化路由集成器失败:', error);
      this.handleInitializationError(error);
      return false;
    } finally {
      this.initializationPromise = null;
    }
  }

  /**
   * 验证依赖
   */
  async validateDependencies() {
    // 检查路由系统
    if (!this.router || typeof this.router.initialize !== 'function') {
      throw new Error('无效的路由系统引用');
    }
    
    // 检查导航管理器
    if (!this.navigationManager || typeof this.navigationManager.initialize !== 'function') {
      throw new Error('无效的导航管理器引用');
    }
    
    // 检查组件系统
    if (!this.componentSystem || typeof this.componentSystem.registerComponent !== 'function') {
      throw new Error('无效的组件系统引用');
    }
    
    console.log('依赖验证完成');
  }

  /**
   * 加载配置
   */
  async loadConfigurations() {
    try {
      // 设置路由配置路径
      if (this.config.routesConfigPath) {
        this.router.routesConfigPath = this.config.routesConfigPath;
      }
      
      // 加载组件配置
      if (this.pageComponentConfigurator && this.config.pageComponentsConfigPath) {
        await this.pageComponentConfigurator.loadConfig(this.config.pageComponentsConfigPath);
      }
      
      console.log('配置加载完成');
    } catch (error) {
      console.error('加载配置失败:', error);
      throw error;
    }
  }

  /**
   * 注册组件
   */
  async registerComponents() {
    try {
      // 获取路由配置
      const routes = this.router.getRoutes();
      
      // 注册路由组件
      await this.registerRouteComponents(routes);
      
      // 如果有组件配置器，从配置中注册组件
      if (this.pageComponentConfigurator) {
        await this.registerComponentsFromConfig();
      }
      
      console.log(`组件注册完成，共注册 ${this.componentMap.size} 个组件`);
    } catch (error) {
      console.error('注册组件失败:', error);
      throw error;
    }
  }

  /**
   * 注册路由组件
   */
  async registerRouteComponents(routes) {
    const promises = [];
    
    // 遍历所有路由
    routes.forEach(route => {
      // 注册组件
      if (route.component && typeof route.component === 'string') {
        promises.push(this.registerComponentByName(route.component));
      }
      
      // 递归处理子路由
      if (route.children && route.children.length > 0) {
        promises.push(this.registerRouteComponents(route.children));
      }
    });
    
    await Promise.all(promises);
  }

  /**
   * 根据名称注册组件
   */
  async registerComponentByName(componentName) {
    // 检查缓存
    if (this.componentLoadCache.has(componentName)) {
      return this.componentLoadCache.get(componentName);
    }
    
    try {
      // 尝试加载组件
      const component = await this.loadComponent(componentName);
      
      if (component) {
        // 注册到组件系统
        this.componentSystem.registerComponent(componentName, component);
        
        // 添加到组件映射
        this.componentMap.set(componentName, component);
        
        // 缓存加载结果
        this.componentLoadCache.set(componentName, component);
        
        console.log(`组件 ${componentName} 注册成功`);
      }
      
      return component;
    } catch (error) {
      console.error(`注册组件 ${componentName} 失败:`, error);
      return null;
    }
  }

  /**
   * 加载组件
   */
  async loadComponent(componentName) {
    try {
      // 检查全局组件
      if (window[componentName]) {
        return window[componentName];
      }
      
      // 尝试动态导入
      const modulePath = `/assets/js/components/${componentName.toLowerCase()}.js`;
      const response = await fetch(modulePath);
      
      if (response.ok) {
        const script = await response.text();
        
        // 创建动态脚本
        const moduleFn = new Function('exports', 'require', script);
        const module = { exports: {} };
        
        // 执行脚本
        moduleFn(module.exports, this.requireModule.bind(this));
        
        return module.exports.default || module.exports;
      }
      
      // 组件未找到
      this.handleComponentNotFound(componentName);
      
      return null;
    } catch (error) {
      console.error(`加载组件 ${componentName} 失败:`, error);
      return null;
    }
  }

  /**
   * 模块导入函数
   */
  requireModule(modulePath) {
    // 简单的模块导入实现
    // 在实际项目中可能需要更复杂的模块系统
    
    // 检查是否是内置模块
    if (modulePath === 'core' || modulePath === 'utils' || modulePath === 'components') {
      return window[modulePath] || {};
    }
    
    // 检查是否是相对路径
    if (modulePath.startsWith('./') || modulePath.startsWith('../')) {
      // 这里可以实现相对路径解析
      // 为简化，返回空对象
      return {};
    }
    
    // 默认返回空对象
    return {};
  }

  /**
   * 从配置注册组件
   */
  async registerComponentsFromConfig() {
    try {
      const components = this.pageComponentConfigurator.getComponents();
      
      for (const [name, config] of Object.entries(components)) {
        await this.registerComponentByName(name);
      }
    } catch (error) {
      console.error('从配置注册组件失败:', error);
    }
  }

  /**
   * 设置中间件
   */
  async setupMiddlewares() {
    try {
      // 注册默认中间件
      this.registerDefaultMiddlewares();
      
      // 从路由配置中设置中间件
      await this.setupMiddlewaresFromConfig();
      
      console.log(`中间件设置完成，共注册 ${this.middlewares.length} 个中间件`);
    } catch (error) {
      console.error('设置中间件失败:', error);
    }
  }

  /**
   * 注册默认中间件
   */
  registerDefaultMiddlewares() {
    // 身份验证中间件
    this.registerMiddleware('auth', this.authMiddleware.bind(this));
    
    // 面包屑中间件
    this.registerMiddleware('breadcrumb', this.breadcrumbMiddleware.bind(this));
    
    // 页面标题中间件
    this.registerMiddleware('title', this.titleMiddleware.bind(this));
  }

  /**
   * 从配置设置中间件
   */
  async setupMiddlewaresFromConfig() {
    try {
      // 尝试从路由配置中获取中间件配置
      // 这里假设路由配置中有middleware字段
      const response = await fetch(this.config.routesConfigPath);
      
      if (response.ok) {
        const config = await response.json();
        
        if (config.middleware && Array.isArray(config.middleware)) {
          for (const middleware of config.middleware) {
            this.registerMiddleware(middleware.name, this.createMiddlewareHandler(middleware));
          }
        }
      }
    } catch (error) {
      console.error('从配置设置中间件失败:', error);
    }
  }

  /**
   * 注册中间件
   */
  registerMiddleware(name, handler) {
    this.middlewares.push({ name, handler });
  }

  /**
   * 创建中间件处理器
   */
  createMiddlewareHandler(middlewareConfig) {
    return async (to, from, next) => {
      try {
        // 检查是否匹配路径
        if (!this.matchesMiddlewarePath(middlewareConfig, to.path)) {
          return next();
        }
        
        // 检查是否排除路径
        if (this.isExcludedPath(middlewareConfig, to.path)) {
          return next();
        }
        
        // 执行中间件处理器
        if (middlewareConfig.handler && typeof window[middlewareConfig.handler] === 'function') {
          return await window[middlewareConfig.handler](to, from, next);
        }
        
        return next();
      } catch (error) {
        console.error(`中间件 ${middlewareConfig.name} 执行失败:`, error);
        return next(error);
      }
    };
  }

  /**
   * 检查路径是否匹配中间件
   */
  matchesMiddlewarePath(middlewareConfig, path) {
    if (!middlewareConfig.paths) return true;
    
    if (Array.isArray(middlewareConfig.paths)) {
      return middlewareConfig.paths.some(p => 
        p === '*' || path === p || path.startsWith(`${p}/`)
      );
    }
    
    return true;
  }

  /**
   * 检查路径是否被排除
   */
  isExcludedPath(middlewareConfig, path) {
    if (!middlewareConfig.exclude) return false;
    
    if (Array.isArray(middlewareConfig.exclude)) {
      return middlewareConfig.exclude.some(p => 
        p === path || path.startsWith(`${p}/`)
      );
    }
    
    return false;
  }

  /**
   * 配置路由守卫
   */
  async configureRouteGuards() {
    try {
      // 配置前置守卫
      this.router.beforeEach(this.createBeforeEachGuard.bind(this));
      
      // 配置后置守卫
      this.router.afterEach(this.createAfterEachGuard.bind(this));
      
      console.log('路由守卫配置完成');
    } catch (error) {
      console.error('配置路由守卫失败:', error);
    }
  }

  /**
   * 创建前置守卫
   */
  async createBeforeEachGuard(from, to, next) {
    try {
      // 执行所有中间件
      for (const middleware of this.middlewares) {
        const result = await middleware.handler(to, from, () => true);
        
        if (result === false) {
          console.warn(`中间件 ${middleware.name} 阻止了导航`);
          return false;
        }
        
        if (typeof result === 'string') {
          console.warn(`中间件 ${middleware.name} 重定向到: ${result}`);
          this.router.push(result);
          return false;
        }
      }
      
      // 触发导航开始事件
      this.emit('navigationStart', { from, to });
      
      return true;
    } catch (error) {
      console.error('前置守卫执行失败:', error);
      this.handleRouteError(error);
      return false;
    }
  }

  /**
   * 创建后置守卫
   */
  async createAfterEachGuard(from, to) {
    try {
      // 触发导航完成事件
      this.emit('navigationComplete', { from, to });
      
      // 如果有智能规划整合器，通知它路由已变更
      if (this.intelligentPlannerIntegrator && typeof this.intelligentPlannerIntegrator.onRouteChange === 'function') {
        this.intelligentPlannerIntegrator.onRouteChange(from, to);
      }
    } catch (error) {
      console.error('后置守卫执行失败:', error);
    }
  }

  /**
   * 初始化路由系统
   */
  async initializeRouter() {
    try {
      // 配置路由系统
      this.router.componentSystem = this.componentSystem;
      
      // 初始化路由
      await this.router.initialize();
      
      console.log('路由系统初始化完成');
    } catch (error) {
      console.error('初始化路由系统失败:', error);
      throw error;
    }
  }

  /**
   * 初始化导航管理器
   */
  async initializeNavigationManager() {
    try {
      // 配置导航管理器
      this.navigationManager.router = this.router;
      
      // 初始化导航管理器
      await this.navigationManager.initialize();
      
      console.log('导航管理器初始化完成');
    } catch (error) {
      console.error('初始化导航管理器失败:', error);
      throw error;
    }
  }

  /**
   * 连接系统组件
   */
  async connectSystems() {
    try {
      // 连接组件系统与路由系统
      this.connectComponentSystem();
      
      // 连接智能规划系统
      this.connectIntelligentSystems();
      
      // 设置全局引用
      this.setupGlobalReferences();
      
      console.log('系统组件连接完成');
    } catch (error) {
      console.error('连接系统组件失败:', error);
    }
  }

  /**
   * 连接组件系统
   */
  connectComponentSystem() {
    if (this.componentSystem && this.router) {
      // 为组件系统提供路由访问能力
      this.componentSystem.router = this.router;
      this.componentSystem.navigationManager = this.navigationManager;
    }
  }

  /**
   * 连接智能规划系统
   */
  connectIntelligentSystems() {
    if (this.intelligentPlannerIntegrator) {
      // 提供路由信息给智能规划系统
      this.intelligentPlannerIntegrator.router = this.router;
      this.intelligentPlannerIntegrator.navigationManager = this.navigationManager;
    }
  }

  /**
   * 设置全局引用
   */
  setupGlobalReferences() {
    if (typeof window !== 'undefined') {
      window.routerIntegrator = this;
      window.$router = this.router;
      window.$navigation = this.navigationManager;
      window.$components = this.componentSystem;
    }
  }

  /**
   * 注册错误处理器
   */
  async registerErrorHandlers() {
    // 注册路由错误处理器
    this.router.on('error', (error) => this.handleRouteError(error));
    
    // 注册导航错误处理器
    this.navigationManager.on('error', (error) => this.handleNavigationError(error));
    
    // 注册组件系统错误处理器
    if (this.componentSystem && typeof this.componentSystem.on === 'function') {
      this.componentSystem.on('error', (error) => this.handleComponentError(error));
    }
  }

  /**
   * 启用调试模式
   */
  enableDebugMode() {
    console.log('启用路由集成器调试模式');
    
    // 添加调试信息
    this.router.on('routeChanged', ({ from, to }) => {
      console.log('路由变更:', { from: from?.path, to: to?.path });
    });
    
    this.navigationManager.on('navigationCompleted', ({ from, to }) => {
      console.log('导航完成:', { from: from?.path, to: to?.path });
    });
  }

  /**
   * 默认中间件实现
   */
  async authMiddleware(to, from, next) {
    // 检查路由是否需要认证
    if (to.meta && to.meta.requiresAuth) {
      // 这里应该检查用户是否已登录
      // 为简化，假设用户已登录
      const isAuthenticated = true;
      
      if (!isAuthenticated) {
        // 未登录，重定向到登录页
        return '/login';
      }
    }
    
    return next();
  }

  /**
   * 面包屑中间件
   */
  async breadcrumbMiddleware(to, from, next) {
    // 面包屑生成由导航管理器处理
    return next();
  }

  /**
   * 页面标题中间件
   */
  async titleMiddleware(to, from, next) {
    // 页面标题设置由导航管理器处理
    return next();
  }

  /**
   * 错误处理
   */
  handleComponentNotFound(componentName) {
    if (this.errorHandlers.componentNotFound) {
      this.errorHandlers.componentNotFound(componentName);
    }
  }

  /**
   * 默认组件未找到处理器
   */
  defaultComponentNotFoundHandler(componentName) {
    console.warn(`组件 ${componentName} 未找到`);
    
    // 注册默认组件
    const defaultComponent = () => {
      return {
        render: () => `<div class="component-not-found">组件 ${componentName} 未找到</div>`
      };
    };
    
    if (this.componentSystem) {
      this.componentSystem.registerComponent(componentName, defaultComponent);
    }
  }

  /**
   * 处理路由错误
   */
  handleRouteError(error) {
    if (this.errorHandlers.routeError) {
      this.errorHandlers.routeError(error);
    }
  }

  /**
   * 默认路由错误处理器
   */
  defaultRouteErrorHandler(error) {
    console.error('路由错误:', error);
    
    // 重定向到错误页面
    if (this.router) {
      this.router.push(`/error?code=500&message=${encodeURIComponent(error.message)}`);
    }
  }

  /**
   * 处理初始化错误
   */
  handleInitializationError(error) {
    if (this.errorHandlers.initializationError) {
      this.errorHandlers.initializationError(error);
    }
  }

  /**
   * 默认初始化错误处理器
   */
  defaultInitializationErrorHandler(error) {
    console.error('初始化错误:', error);
    
    // 显示错误信息
    const appContainer = document.querySelector('#app') || document.body;
    appContainer.innerHTML = `
      <div class="initialization-error">
        <h1>系统初始化失败</h1>
        <p>${error.message}</p>
        <button onclick="window.location.reload()">重试</button>
      </div>
    `;
  }

  /**
   * 处理导航错误
   */
  handleNavigationError(error) {
    console.error('导航错误:', error);
    this.emit('error', { error, type: 'navigation' });
  }

  /**
   * 处理组件错误
   */
  handleComponentError(error) {
    console.error('组件错误:', error);
    this.emit('error', { error, type: 'component' });
  }

  /**
   * 注册错误处理器
   */
  registerErrorHandler(type, handler) {
    if (this.errorHandlers[type]) {
      this.errorHandlers[type] = handler;
      return true;
    }
    return false;
  }

  /**
   * 导航到指定路径
   */
  navigate(path, options = {}) {
    if (!this.router) {
      console.error('路由系统未初始化');
      return false;
    }
    
    return this.router.push(path);
  }

  /**
   * 获取当前路由
   */
  getCurrentRoute() {
    if (!this.router) {
      return null;
    }
    
    return this.router.getCurrentRoute();
  }

  /**
   * 获取组件
   */
  getComponent(name) {
    return this.componentMap.get(name);
  }

  /**
   * 获取所有注册的组件
   */
  getRegisteredComponents() {
    return Array.from(this.componentMap.keys());
  }

  /**
   * 获取中间件
   */
  getMiddlewares() {
    return [...this.middlewares];
  }

  /**
   * 获取状态
   */
  getStatus() {
    return {
      isInitialized: this.isInitialized,
      componentCount: this.componentMap.size,
      middlewareCount: this.middlewares.length,
      routerStatus: this.router ? this.router.getStatus() : null,
      navigationStatus: this.navigationManager ? this.navigationManager.getState() : null
    };
  }

  /**
   * 事件监听
   */
  on(event, callback) {
    // 这里可以实现事件系统
    // 为简化，暂时使用空实现
    return true;
  }

  /**
   * 触发事件
   */
  emit(event, data) {
    // 这里可以实现事件系统
    // 为简化，暂时使用空实现
    console.log(`事件 ${event} 触发:`, data);
  }

  /**
   * 重置路由集成器
   */
  async reset() {
    try {
      // 重置组件映射
      this.componentMap.clear();
      
      // 重置中间件
      this.middlewares = [];
      
      // 重置状态
      this.isInitialized = false;
      
      console.log('路由集成器已重置');
      
      return true;
    } catch (error) {
      console.error('重置路由集成器失败:', error);
      return false;
    }
  }

  /**
   * 销毁路由集成器
   */
  async destroy() {
    try {
      // 清理组件映射
      this.componentMap.clear();
      
      // 清理中间件
      this.middlewares = [];
      
      // 清理缓存
      this.componentLoadCache.clear();
      
      // 重置状态
      this.isInitialized = false;
      
      console.log('路由集成器已销毁');
      
      return true;
    } catch (error) {
      console.error('销毁路由集成器失败:', error);
      return false;
    }
  }
}

// 创建路由集成器实例
const routerIntegrator = new RouterIntegrator({
  debug: true,
  routesConfigPath: '/assets/config/routes-config.json',
  pageComponentsConfigPath: '/assets/config/page-components-config.json'
});

// 导出
if (typeof window !== 'undefined') {
  window.RouterIntegrator = RouterIntegrator;
  window.routerIntegrator = routerIntegrator;
}

export { RouterIntegrator, routerIntegrator };