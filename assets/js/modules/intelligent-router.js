// 智能路由系统 - 实现声明式路由配置、路由守卫和组件集成
class IntelligentRouter {
  constructor(options = {}) {
    // 路由配置
    this.routes = [];
    
    // 当前路由状态
    this.currentRoute = null;
    
    // 路由历史记录
    this.historyStack = [];
    
    // 路由缓存
    this.routeCache = new Map();
    
    // 路由守卫
    this.guards = {
      beforeEach: [],
      afterEach: []
    };
    
    // 路由事件监听器
    this.listeners = new Map();
    
    // 路由模式 (hash 或 history)
    this.mode = options.mode || 'hash';
    
    // 根路径
    this.base = options.base || '';
    
    // 路由配置文件路径
    this.routesConfigPath = options.routesConfigPath || null;
    
    // 与组件系统集成的配置
    this.componentSystem = options.componentSystem || null;
    
    // 路由延迟加载配置
    this.lazyLoading = {
      enabled: options.lazyLoading !== false,
      preloadDistance: options.preloadDistance || 1
    };
    
    // 路由缓存配置
    this.caching = {
      enabled: options.caching !== false,
      maxCacheSize: options.maxCacheSize || 20
    };
    
    // 导航锁定（防止重复导航）
    this.navigating = false;
    
    // 路由匹配结果缓存
    this.matchCache = new Map();
    
    // 初始化状态
    this.isInitialized = false;
  }

  /**
   * 初始化路由系统
   */
  async initialize() {
    if (this.isInitialized) {
      console.warn('智能路由系统已经初始化');
      return true;
    }
    
    try {
      console.log('初始化智能路由系统...');
      
      // 设置基础路径
      if (this.base && !window.location.pathname.startsWith(this.base)) {
        const redirectUrl = this.base + window.location.pathname;
        console.warn(`重定向到基础路径: ${redirectUrl}`);
        window.location.href = redirectUrl;
        return false;
      }
      
      // 加载路由配置
      if (this.routesConfigPath) {
        await this.loadRoutesConfig();
      }
      
      // 设置路由监听
      this.setupRouteListener();
      
      // 处理初始路由
      this.handleInitialRoute();
      
      this.isInitialized = true;
      console.log('智能路由系统初始化完成');
      
      return true;
    } catch (error) {
      console.error('初始化智能路由系统失败:', error);
      this.emit('error', { error, type: 'initialization' });
      return false;
    }
  }

  /**
   * 加载路由配置文件
   */
  async loadRoutesConfig() {
    try {
      console.log(`加载路由配置文件: ${this.routesConfigPath}`);
      
      const response = await fetch(this.routesConfigPath);
      
      if (!response.ok) {
        throw new Error(`加载路由配置失败: ${response.status}`);
      }
      
      const config = await response.json();
      
      // 注册路由
      if (config.routes) {
        this.addRoutes(config.routes);
      }
      
      console.log(`路由配置加载成功，注册了 ${this.routes.length} 条路由`);
      
      return true;
    } catch (error) {
      console.error('加载路由配置失败:', error);
      this.emit('error', { error, type: 'config_load' });
      return false;
    }
  }

  /**
   * 设置路由监听器
   */
  setupRouteListener() {
    if (this.mode === 'hash') {
      // Hash模式
      window.addEventListener('hashchange', () => this.handleRouteChange());
    } else {
      // History模式
      window.addEventListener('popstate', () => this.handleRouteChange());
      
      // 拦截点击事件，处理内部链接
      document.addEventListener('click', (event) => {
        const target = event.target.closest('a');
        
        if (target && this.isInternalLink(target)) {
          event.preventDefault();
          this.push(target.getAttribute('href'));
        }
      });
    }
  }

  /**
   * 处理初始路由
   */
  handleInitialRoute() {
    const initialPath = this.getCurrentPath();
    this.handleRouteChange(initialPath);
  }

  /**
   * 处理路由变化
   */
  async handleRouteChange(path = null) {
    if (this.navigating) {
      console.warn('正在导航中，忽略路由变化');
      return;
    }
    
    try {
      // 获取当前路径
      const currentPath = path || this.getCurrentPath();
      
      // 匹配路由
      const matchedRoute = this.matchRoute(currentPath);
      
      if (!matchedRoute) {
        console.warn(`未找到匹配的路由: ${currentPath}`);
        this.handleNotFound(currentPath);
        return;
      }
      
      // 提取路由参数
      const params = this.extractParams(matchedRoute, currentPath);
      const query = this.extractQuery(currentPath);
      
      // 准备路由信息
      const routeInfo = {
        path: currentPath,
        matchedRoute,
        params,
        query,
        name: matchedRoute.name,
        meta: matchedRoute.meta || {}
      };
      
      // 执行导航
      await this.navigateTo(routeInfo);
    } catch (error) {
      console.error('处理路由变化失败:', error);
      this.emit('error', { error, type: 'route_change' });
    }
  }

  /**
   * 执行导航
   */
  async navigateTo(routeInfo) {
    try {
      this.navigating = true;
      
      // 保存旧路由
      const from = this.currentRoute;
      
      // 执行前置守卫
      const shouldContinue = await this.runBeforeGuards(from, routeInfo);
      
      if (!shouldContinue) {
        console.warn('导航被前置守卫阻止');
        return false;
      }
      
      // 更新路由状态
      this.currentRoute = routeInfo;
      
      // 更新历史记录
      this.updateHistoryStack(routeInfo);
      
      // 处理组件渲染
      await this.renderRouteComponent(routeInfo);
      
      // 执行后置守卫
      await this.runAfterGuards(from, routeInfo);
      
      // 触发路由变化事件
      this.emit('routeChanged', { from, to: routeInfo });
      
      // 预加载邻近路由
      this.preloadNearbyRoutes(routeInfo);
      
      console.log(`路由导航成功: ${routeInfo.path}`);
      
      return true;
    } catch (error) {
      console.error('导航失败:', error);
      this.emit('error', { error, type: 'navigation' });
      return false;
    } finally {
      this.navigating = false;
    }
  }

  /**
   * 运行前置守卫
   */
  async runBeforeGuards(from, to) {
    for (const guard of this.guards.beforeEach) {
      try {
        const result = await guard(from, to);
        
        // 如果返回false，阻止导航
        if (result === false) {
          return false;
        }
        
        // 如果返回字符串，重定向到该路径
        if (typeof result === 'string') {
          this.push(result);
          return false;
        }
      } catch (error) {
        console.error('前置守卫执行失败:', error);
        return false;
      }
    }
    
    return true;
  }

  /**
   * 运行后置守卫
   */
  async runAfterGuards(from, to) {
    for (const guard of this.guards.afterEach) {
      try {
        await guard(from, to);
      } catch (error) {
        console.error('后置守卫执行失败:', error);
      }
    }
  }

  /**
   * 渲染路由组件
   */
  async renderRouteComponent(routeInfo) {
    try {
      const { matchedRoute, params, query } = routeInfo;
      
      // 获取路由缓存
      const cacheKey = this.getCacheKey(matchedRoute.path, params, query);
      let component = this.getFromCache(cacheKey);
      
      // 如果组件不在缓存中，创建新组件
      if (!component) {
        // 检查是否需要延迟加载
        if (matchedRoute.lazy && typeof matchedRoute.lazy === 'function') {
          console.log(`延迟加载组件: ${matchedRoute.path}`);
          component = await matchedRoute.lazy();
        } else if (matchedRoute.component) {
          component = matchedRoute.component;
        }
        
        // 渲染组件
        if (component) {
          // 使用组件系统渲染
          if (this.componentSystem && typeof this.componentSystem.render === 'function') {
            await this.componentSystem.render({
              component,
              container: matchedRoute.container || '#app',
              props: {
                route: routeInfo,
                params,
                query,
                router: this
              }
            });
          } else if (typeof component === 'function') {
            // 直接调用组件函数
            await component({
              route: routeInfo,
              params,
              query,
              router: this
            });
          }
          
          // 缓存组件
          if (this.caching.enabled && matchedRoute.meta && matchedRoute.meta.cacheable !== false) {
            this.cacheRoute(cacheKey, component);
          }
        }
      } else {
        console.log(`使用缓存的组件: ${matchedRoute.path}`);
        // 重新激活缓存的组件
        if (typeof component.activate === 'function') {
          component.activate(routeInfo);
        }
      }
    } catch (error) {
      console.error('渲染路由组件失败:', error);
      this.emit('error', { error, type: 'render' });
      
      // 渲染错误组件
      this.renderErrorComponent(routeInfo, error);
    }
  }

  /**
   * 渲染错误组件
   */
  async renderErrorComponent(routeInfo, error) {
    try {
      // 查找错误路由
      const errorRoute = this.routes.find(route => route.name === 'error' || route.path === '/error');
      
      if (errorRoute) {
        // 渲染错误页面
        await this.renderRouteComponent({
          ...routeInfo,
          matchedRoute: errorRoute,
          params: { code: 500, message: error.message },
          error
        });
      } else {
        // 显示默认错误信息
        const container = document.querySelector('#app') || document.body;
        container.innerHTML = `
          <div class="error-container">
            <h1>500 内部服务器错误</h1>
            <p>${error.message}</p>
            <button onclick="window.location.reload()">重试</button>
          </div>
        `;
      }
    } catch (renderError) {
      console.error('渲染错误组件失败:', renderError);
    }
  }

  /**
   * 处理未找到的路由
   */
  async handleNotFound(path) {
    try {
      // 查找404路由
      const notFoundRoute = this.routes.find(route => route.name === '404' || route.path === '*');
      
      if (notFoundRoute) {
        // 渲染404页面
        await this.renderRouteComponent({
          path,
          matchedRoute: notFoundRoute,
          params: { path },
          meta: notFoundRoute.meta || {}
        });
      } else {
        // 显示默认404页面
        const container = document.querySelector('#app') || document.body;
        container.innerHTML = `
          <div class="not-found-container">
            <h1>404 页面未找到</h1>
            <p>请求的路径 "${path}" 不存在</p>
            <button onclick="window.router.push('/')">返回首页</button>
          </div>
        `;
      }
      
      // 触发404事件
      this.emit('notFound', { path });
    } catch (error) {
      console.error('处理404路由失败:', error);
    }
  }

  /**
   * 添加路由
   */
  addRoute(route) {
    try {
      // 验证路由配置
      if (!this.isValidRoute(route)) {
        throw new Error('无效的路由配置');
      }
      
      // 添加路由到路由表
      this.routes.push(route);
      
      // 清除匹配缓存
      this.clearMatchCache();
      
      console.log(`路由添加成功: ${route.path}`);
      
      return true;
    } catch (error) {
      console.error('添加路由失败:', error);
      this.emit('error', { error, type: 'add_route' });
      return false;
    }
  }

  /**
   * 批量添加路由
   */
  addRoutes(routes) {
    try {
      let successCount = 0;
      let failCount = 0;
      
      routes.forEach(route => {
        if (this.addRoute(route)) {
          successCount++;
        } else {
          failCount++;
        }
      });
      
      console.log(`批量添加路由完成: 成功 ${successCount} 条, 失败 ${failCount} 条`);
      
      return {
        success: successCount,
        fail: failCount,
        total: successCount + failCount
      };
    } catch (error) {
      console.error('批量添加路由失败:', error);
      this.emit('error', { error, type: 'add_routes' });
      return { success: 0, fail: 0, total: 0 };
    }
  }

  /**
   * 验证路由配置
   */
  isValidRoute(route) {
    // 基本验证
    if (!route || typeof route !== 'object') {
      return false;
    }
    
    // 必须有路径
    if (!route.path || typeof route.path !== 'string') {
      return false;
    }
    
    // 必须有组件或重定向
    if (!route.component && !route.redirect && !route.lazy) {
      return false;
    }
    
    // 检查子路由
    if (route.children && Array.isArray(route.children)) {
      return route.children.every(child => this.isValidRoute(child));
    }
    
    return true;
  }

  /**
   * 匹配路由
   */
  matchRoute(path) {
    // 检查缓存
    const cachedMatch = this.matchCache.get(path);
    if (cachedMatch) {
      return cachedMatch;
    }
    
    // 尝试直接匹配
    let matchedRoute = this.routes.find(route => this.isExactMatch(route.path, path));
    
    // 如果没有直接匹配，尝试参数化路由
    if (!matchedRoute) {
      matchedRoute = this.findParametrizedRoute(path);
    }
    
    // 如果没有匹配，尝试通配符路由
    if (!matchedRoute) {
      matchedRoute = this.routes.find(route => route.path === '*' || route.path === '/:pathMatch(.*)*');
    }
    
    // 缓存匹配结果
    if (matchedRoute) {
      this.matchCache.set(path, matchedRoute);
    }
    
    return matchedRoute;
  }

  /**
   * 精确匹配路由
   */
  isExactMatch(routePath, currentPath) {
    return routePath === currentPath;
  }

  /**
   * 查找参数化路由
   */
  findParametrizedRoute(path) {
    const pathSegments = path.split('/').filter(Boolean);
    
    for (const route of this.routes) {
      const routeSegments = route.path.split('/').filter(Boolean);
      
      // 路径段数量必须一致
      if (routeSegments.length !== pathSegments.length) {
        continue;
      }
      
      let matches = true;
      
      for (let i = 0; i < routeSegments.length; i++) {
        const routeSegment = routeSegments[i];
        const pathSegment = pathSegments[i];
        
        // 检查是否是参数段
        if (routeSegment.startsWith(':') || routeSegment.includes('*')) {
          continue;
        }
        
        // 普通段必须完全匹配
        if (routeSegment !== pathSegment) {
          matches = false;
          break;
        }
      }
      
      if (matches) {
        return route;
      }
    }
    
    return null;
  }

  /**
   * 提取路由参数
   */
  extractParams(route, path) {
    const params = {};
    const routeSegments = route.path.split('/').filter(Boolean);
    const pathSegments = path.split('/').filter(Boolean);
    
    for (let i = 0; i < routeSegments.length; i++) {
      const routeSegment = routeSegments[i];
      
      // 检查是否是参数段
      if (routeSegment.startsWith(':')) {
        // 提取参数名
        const paramName = routeSegment.slice(1).split('(')[0];
        params[paramName] = pathSegments[i];
      } else if (routeSegment.includes('*')) {
        // 处理通配符参数
        const paramName = routeSegment.split('*').pop() || 'pathMatch';
        params[paramName] = pathSegments.slice(i).join('/');
      }
    }
    
    return params;
  }

  /**
   * 提取查询参数
   */
  extractQuery(path) {
    const query = {};
    const queryString = path.includes('?') ? path.split('?')[1] : '';
    
    if (queryString) {
      queryString.split('&').forEach(param => {
        const [key, value] = param.split('=').map(decodeURIComponent);
        if (key) {
          query[key] = value || true;
        }
      });
    }
    
    return query;
  }

  /**
   * 导航到指定路径
   */
  push(path, replace = false) {
    if (!this.isInitialized) {
      console.warn('路由系统尚未初始化');
      return false;
    }
    
    try {
      // 格式化路径
      const formattedPath = this.formatPath(path);
      
      // 更新URL
      if (this.mode === 'hash') {
        if (replace) {
          window.location.replace(`#${formattedPath}`);
        } else {
          window.location.hash = formattedPath;
        }
      } else {
        // History模式
        const url = this.base + formattedPath;
        
        if (replace) {
          window.history.replaceState(null, '', url);
        } else {
          window.history.pushState(null, '', url);
        }
        
        // 手动触发路由变化
        this.handleRouteChange(formattedPath);
      }
      
      return true;
    } catch (error) {
      console.error('导航失败:', error);
      this.emit('error', { error, type: 'push' });
      return false;
    }
  }

  /**
   * 替换当前路径
   */
  replace(path) {
    return this.push(path, true);
  }

  /**
   * 返回上一页
   */
  back() {
    window.history.back();
  }

  /**
   * 前进到下一页
   */
  forward() {
    window.history.forward();
  }

  /**
   * 格式化路径
   */
  formatPath(path) {
    let formattedPath = path;
    
    // 确保以/开头
    if (!formattedPath.startsWith('/')) {
      formattedPath = '/' + formattedPath;
    }
    
    // 移除末尾的/
    if (formattedPath.length > 1 && formattedPath.endsWith('/')) {
      formattedPath = formattedPath.slice(0, -1);
    }
    
    return formattedPath;
  }

  /**
   * 获取当前路径
   */
  getCurrentPath() {
    let path = '';
    
    if (this.mode === 'hash') {
      // Hash模式
      path = window.location.hash.slice(1);
    } else {
      // History模式
      path = window.location.pathname;
      
      // 移除基础路径
      if (this.base && path.startsWith(this.base)) {
        path = path.slice(this.base.length);
      }
    }
    
    // 添加查询参数
    if (window.location.search) {
      path += window.location.search;
    }
    
    // 格式化路径
    return this.formatPath(path);
  }

  /**
   * 检查是否是内部链接
   */
  isInternalLink(element) {
    // 检查是否是锚点链接
    if (element.getAttribute('href')?.startsWith('#')) {
      return false;
    }
    
    // 检查是否是外部链接
    if (element.getAttribute('target') === '_blank' || element.hostname !== window.location.hostname) {
      return false;
    }
    
    return true;
  }

  /**
   * 更新历史记录栈
   */
  updateHistoryStack(routeInfo) {
    // 添加到历史栈
    this.historyStack.push(routeInfo);
    
    // 限制历史栈大小
    const maxHistorySize = 50;
    if (this.historyStack.length > maxHistorySize) {
      this.historyStack.shift();
    }
  }

  /**
   * 预加载邻近路由
   */
  async preloadNearbyRoutes(currentRoute) {
    if (!this.lazyLoading.enabled || !this.lazyLoading.preloadDistance) {
      return;
    }
    
    try {
      // 查找邻近路由
      const nearbyRoutes = this.findNearbyRoutes(currentRoute, this.lazyLoading.preloadDistance);
      
      // 预加载延迟加载的组件
      for (const route of nearbyRoutes) {
        if (route.lazy && typeof route.lazy === 'function' && route.meta && route.meta.preload !== false) {
          console.log(`预加载路由: ${route.path}`);
          
          // 异步预加载，不阻塞当前导航
          setTimeout(async () => {
            try {
              await route.lazy();
              console.log(`预加载完成: ${route.path}`);
            } catch (error) {
              console.warn(`预加载失败: ${route.path}`, error);
            }
          }, 0);
        }
      }
    } catch (error) {
      console.error('预加载邻近路由失败:', error);
    }
  }

  /**
   * 查找邻近路由
   */
  findNearbyRoutes(currentRoute, distance) {
    const nearbyRoutes = [];
    const currentIndex = this.routes.findIndex(r => r.path === currentRoute.matchedRoute.path);
    
    if (currentIndex !== -1) {
      // 向前查找
      for (let i = 1; i <= distance && currentIndex - i >= 0; i++) {
        nearbyRoutes.push(this.routes[currentIndex - i]);
      }
      
      // 向后查找
      for (let i = 1; i <= distance && currentIndex + i < this.routes.length; i++) {
        nearbyRoutes.push(this.routes[currentIndex + i]);
      }
    }
    
    return nearbyRoutes;
  }

  /**
   * 路由缓存管理
   */
  getCacheKey(path, params, query) {
    // 生成缓存键
    const paramsStr = JSON.stringify(params);
    const queryStr = JSON.stringify(query);
    return `${path}_${paramsStr}_${queryStr}`;
  }

  cacheRoute(key, component) {
    // 检查缓存大小
    if (this.routeCache.size >= this.caching.maxCacheSize) {
      // 删除最早的缓存
      const firstKey = this.routeCache.keys().next().value;
      this.routeCache.delete(firstKey);
    }
    
    // 缓存组件
    this.routeCache.set(key, component);
  }

  getFromCache(key) {
    return this.routeCache.get(key);
  }

  clearCache() {
    this.routeCache.clear();
    console.log('路由缓存已清空');
  }

  clearMatchCache() {
    this.matchCache.clear();
  }

  /**
   * 路由守卫注册
   */
  beforeEach(guard) {
    if (typeof guard === 'function') {
      this.guards.beforeEach.push(guard);
      return true;
    }
    return false;
  }

  afterEach(guard) {
    if (typeof guard === 'function') {
      this.guards.afterEach.push(guard);
      return true;
    }
    return false;
  }

  /**
   * 事件监听
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    
    this.listeners.get(event).push(callback);
    return true;
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      
      if (index !== -1) {
        callbacks.splice(index, 1);
        return true;
      }
    }
    
    return false;
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`事件监听器执行失败: ${event}`, error);
        }
      });
    }
  }

  /**
   * 获取路由信息
   */
  getCurrentRoute() {
    return this.currentRoute;
  }

  getRoutes() {
    return this.routes;
  }

  getRouteByName(name) {
    return this.routes.find(route => route.name === name);
  }

  /**
   * 生成URL
   */
  generateUrl(routeName, params = {}, query = {}) {
    const route = this.getRouteByName(routeName);
    
    if (!route) {
      console.warn(`找不到路由: ${routeName}`);
      return '';
    }
    
    // 替换路由参数
    let url = route.path;
    
    Object.entries(params).forEach(([key, value]) => {
      const regex = new RegExp(`:${key}`, 'g');
      url = url.replace(regex, encodeURIComponent(value));
    });
    
    // 添加查询参数
    const queryParams = Object.entries(query)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
      .join('&');
    
    if (queryParams) {
      url += `?${queryParams}`;
    }
    
    return url;
  }

  /**
   * 重置路由系统
   */
  reset() {
    try {
      // 清除路由
      this.routes = [];
      this.currentRoute = null;
      this.historyStack = [];
      this.routeCache.clear();
      this.matchCache.clear();
      
      // 重置守卫和监听器
      this.guards = {
        beforeEach: [],
        afterEach: []
      };
      
      this.listeners.clear();
      
      console.log('路由系统已重置');
      
      return true;
    } catch (error) {
      console.error('重置路由系统失败:', error);
      this.emit('error', { error, type: 'reset' });
      return false;
    }
  }

  /**
   * 获取路由状态
   */
  getStatus() {
    return {
      isInitialized: this.isInitialized,
      mode: this.mode,
      currentPath: this.getCurrentPath(),
      routeCount: this.routes.length,
      historyLength: this.historyStack.length,
      cacheSize: this.routeCache.size,
      matchCacheSize: this.matchCache.size,
      navigating: this.navigating
    };
  }
}

// 创建智能路由系统实例
const intelligentRouter = new IntelligentRouter({
  mode: 'hash',
  lazyLoading: {
    enabled: true,
    preloadDistance: 1
  },
  caching: {
    enabled: true,
    maxCacheSize: 10
  }
});

// 导出
if (typeof window !== 'undefined') {
  window.IntelligentRouter = IntelligentRouter;
  window.router = intelligentRouter;
}

export { IntelligentRouter, intelligentRouter };