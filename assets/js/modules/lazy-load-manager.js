// 懒加载组件管理器 - 实现组件的按需加载和动态导入，优化页面初始加载性能
class LazyLoadManager {
  constructor(options = {}) {
    // 配置选项
    this.config = {
      // 基础配置
      rootMargin: options.rootMargin || '100px 0px', // 根元素的边距
      threshold: options.threshold || 0.1, // 交叉比例阈值
      timeout: options.timeout || 30000, // 加载超时时间（毫秒）
      
      // 组件配置
      preloadDistance: options.preloadDistance || 500, // 预加载距离（像素）
      maxConcurrentLoads: options.maxConcurrentLoads || 3, // 最大并发加载数
      
      // 缓存配置
      cacheEnabled: options.cacheEnabled !== false, // 是否启用组件缓存
      useCacheManager: options.useCacheManager !== false, // 是否使用全局缓存管理器
      
      // 事件配置
      onLoadStart: options.onLoadStart || null, // 加载开始回调
      onLoadComplete: options.onLoadComplete || null, // 加载完成回调
      onLoadError: options.onLoadError || null, // 加载错误回调
      onPreload: options.onPreload || null, // 预加载回调
      
      // 调试配置
      debug: options.debug || false,
      
      ...options
    };
    
    // 状态管理
    this.state = {
      observers: new Map(), // 观察者映射
      loadingComponents: new Map(), // 正在加载的组件
      loadedComponents: new Map(), // 已加载的组件
      preloadedComponents: new Set(), // 已预加载的组件
      pendingLoads: new Map(), // 等待加载的组件
      concurrentLoadCount: 0, // 当前并发加载数
      
      // 统计信息
      stats: {
        loadedCount: 0,
        failedCount: 0,
        preloadedCount: 0,
        totalLoadTime: 0,
        averageLoadTime: 0
      }
    };
    
    // 交叉观察器实例
    this.intersectionObserver = null;
    
    // 预加载观察器实例
    this.preloadObserver = null;
    
    // 缓存引用
    this.cache = null;
    
    // 初始化
    this.initialize();
  }

  /**
   * 初始化懒加载管理器
   */
  initialize() {
    this.log('初始化懒加载管理器...');
    
    // 检查浏览器兼容性
    this.checkCompatibility();
    
    // 初始化缓存
    this.initializeCache();
    
    // 初始化观察器
    this.initializeObservers();
    
    // 注册全局事件监听器
    this.registerEventListeners();
    
    this.log('懒加载管理器初始化完成');
  }

  /**
   * 检查浏览器兼容性
   */
  checkCompatibility() {
    this.log('检查浏览器兼容性...');
    
    this.compatibility = {
      intersectionObserver: 'IntersectionObserver' in window,
      dynamicImport: typeof import === 'function',
      requestIdleCallback: 'requestIdleCallback' in window
    };
    
    // 如果不支持 IntersectionObserver，则降级为滚动监听
    if (!this.compatibility.intersectionObserver) {
      this.log('浏览器不支持 IntersectionObserver，将使用降级方案', 'warn');
      this.useFallback = true;
    }
  }

  /**
   * 初始化缓存
   */
  initializeCache() {
    this.log('初始化缓存系统...');
    
    if (this.config.cacheEnabled) {
      // 尝试使用全局缓存管理器
      if (this.config.useCacheManager && window.cacheManager) {
        this.cache = window.cacheManager;
        this.log('使用全局缓存管理器');
      } else {
        // 使用内部简单缓存
        this.internalCache = new Map();
        this.log('使用内部缓存');
      }
    }
  }

  /**
   * 初始化观察器
   */
  initializeObservers() {
    this.log('初始化观察器...');
    
    // 如果支持 IntersectionObserver
    if (this.compatibility.intersectionObserver) {
      // 加载观察器配置
      const loadObserverOptions = {
        root: null, // 使用视口作为根
        rootMargin: this.config.rootMargin,
        threshold: this.config.threshold
      };
      
      // 创建加载观察器
      this.intersectionObserver = new IntersectionObserver(
        this.handleIntersection.bind(this),
        loadObserverOptions
      );
      
      // 预加载观察器配置
      const preloadObserverOptions = {
        root: null,
        rootMargin: `${this.config.preloadDistance}px 0px`,
        threshold: 0.01 // 只要有一点可见就触发
      };
      
      // 创建预加载观察器
      this.preloadObserver = new IntersectionObserver(
        this.handlePreloadIntersection.bind(this),
        preloadObserverOptions
      );
    }
  }

  /**
   * 注册全局事件监听器
   */
  registerEventListeners() {
    this.log('注册事件监听器...');
    
    // 窗口滚动事件（降级方案）
    if (this.useFallback) {
      this.debouncedCheck = this.debounce(this.checkElements.bind(this), 100);
      window.addEventListener('scroll', this.debouncedCheck);
      window.addEventListener('resize', this.debouncedCheck);
      window.addEventListener('orientationchange', this.debouncedCheck);
    }
    
    // 页面可见性变化事件
    document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    
    // 网络状态变化事件
    window.addEventListener('online', this.handleNetworkChange.bind(this));
    window.addEventListener('offline', this.handleNetworkChange.bind(this));
  }

  /**
   * 处理交叉观察器回调
   */
  handleIntersection(entries, observer) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const componentData = this.state.observers.get(entry.target);
        
        if (componentData && !componentData.loaded && !componentData.loading) {
          this.log(`元素进入视口: ${componentData.name}`);
          
          // 停止观察该元素
          this.stopObserving(entry.target);
          
          // 加载组件
          this.loadComponent(componentData);
        }
      }
    });
  }

  /**
   * 处理预加载交叉观察器回调
   */
  handlePreloadIntersection(entries, observer) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const componentData = this.state.observers.get(entry.target);
        
        if (componentData && !componentData.preloaded && !componentData.loading) {
          this.log(`元素进入预加载区域: ${componentData.name}`);
          
          // 标记为已预加载
          componentData.preloaded = true;
          this.state.preloadedComponents.add(componentData.name);
          
          // 触发预加载回调
          this.triggerCallback('onPreload', componentData.name, entry.target);
          
          // 预加载组件
          this.preloadComponent(componentData);
        }
      }
    });
  }

  /**
   * 观察懒加载元素
   * @param {HTMLElement} element - 要观察的元素
   * @param {Object} options - 组件选项
   */
  observe(element, options = {}) {
    if (!element) {
      this.log('观察元素为空', 'error');
      return false;
    }
    
    // 确保 options 是对象
    options = typeof options === 'object' && options !== null ? options : {};
    
    // 组件配置
    const componentData = {
      element,
      name: options.name || `component_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      importFn: options.importFn,
      loadFn: options.loadFn,
      placeholder: options.placeholder,
      errorComponent: options.errorComponent,
      delay: options.delay || 0,
      timeout: options.timeout || this.config.timeout,
      priority: options.priority || 'normal',
      preload: options.preload !== false,
      preloaded: false,
      loading: false,
      loaded: false,
      error: null,
      loadStartTime: 0,
      loadEndTime: 0,
      container: options.container || null
    };
    
    // 验证必要的加载函数
    if (!componentData.importFn && !componentData.loadFn) {
      this.log('组件必须提供 importFn 或 loadFn', 'error');
      return false;
    }
    
    // 存储组件数据
    this.state.observers.set(element, componentData);
    
    // 设置占位符
    this.setupPlaceholder(componentData);
    
    // 使用观察器观察元素
    if (this.compatibility.intersectionObserver) {
      this.intersectionObserver.observe(element);
      
      // 如果启用预加载，也添加到预加载观察器
      if (componentData.preload) {
        this.preloadObserver.observe(element);
      }
    } else {
      // 降级方案：立即检查元素是否在视口内
      this.checkElementInViewport(componentData);
    }
    
    this.log(`开始观察组件: ${componentData.name}`);
    
    return true;
  }

  /**
   * 停止观察元素
   * @param {HTMLElement} element - 要停止观察的元素
   */
  stopObserving(element) {
    if (!element) return;
    
    // 从观察器中移除
    if (this.compatibility.intersectionObserver) {
      this.intersectionObserver.unobserve(element);
      this.preloadObserver.unobserve(element);
    }
    
    // 从状态中移除
    this.state.observers.delete(element);
  }

  /**
   * 设置占位符
   */
  setupPlaceholder(componentData) {
    const { element, placeholder } = componentData;
    
    if (!placeholder) return;
    
    // 保存原始内容
    componentData.originalContent = element.innerHTML;
    
    // 设置占位符
    if (typeof placeholder === 'string') {
      element.innerHTML = placeholder;
    } else if (placeholder instanceof Element) {
      element.innerHTML = '';
      element.appendChild(placeholder);
    } else if (typeof placeholder === 'function') {
      const placeholderElement = placeholder();
      if (placeholderElement instanceof Element) {
        element.innerHTML = '';
        element.appendChild(placeholderElement);
      }
    }
  }

  /**
   * 恢复原始内容
   */
  restoreOriginalContent(componentData) {
    const { element, originalContent } = componentData;
    
    if (originalContent !== undefined) {
      element.innerHTML = originalContent;
    }
  }

  /**
   * 加载组件
   */
  async loadComponent(componentData) {
    const { name } = componentData;
    
    // 检查缓存
    if (this.config.cacheEnabled) {
      const cachedComponent = await this.getFromCache(name);
      if (cachedComponent) {
        this.log(`从缓存加载组件: ${name}`);
        this.renderComponent(componentData, cachedComponent);
        return;
      }
    }
    
    // 检查是否可以立即加载
    if (this.state.concurrentLoadCount >= this.config.maxConcurrentLoads) {
      // 将组件添加到等待队列
      this.state.pendingLoads.set(name, componentData);
      this.log(`组件 ${name} 加入等待队列`);
      return;
    }
    
    // 开始加载
    componentData.loading = true;
    componentData.loadStartTime = Date.now();
    this.state.loadingComponents.set(name, componentData);
    this.state.concurrentLoadCount++;
    
    // 触发加载开始回调
    this.triggerCallback('onLoadStart', name, componentData.element);
    
    try {
      // 设置加载超时
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('组件加载超时')), componentData.timeout);
      });
      
      // 执行加载
      let component;
      
      if (componentData.delay > 0) {
        // 延迟加载
        await new Promise(resolve => setTimeout(resolve, componentData.delay));
      }
      
      // 优先使用 importFn（动态导入）
      if (componentData.importFn && this.compatibility.dynamicImport) {
        const result = await Promise.race([componentData.importFn(), timeoutPromise]);
        component = result.default || result;
      } else if (componentData.loadFn) {
        // 回退到 loadFn
        component = await Promise.race([componentData.loadFn(), timeoutPromise]);
      }
      
      // 加载完成
      componentData.loadEndTime = Date.now();
      componentData.loaded = true;
      componentData.loading = false;
      
      // 更新统计
      this.updateStats(componentData);
      
      // 缓存组件
      if (this.config.cacheEnabled) {
        await this.saveToCache(name, component);
      }
      
      // 渲染组件
      this.renderComponent(componentData, component);
      
      // 触发加载完成回调
      this.triggerCallback('onLoadComplete', name, componentData.element, component);
    } catch (error) {
      // 加载错误
      this.handleLoadError(componentData, error);
    } finally {
      // 清理
      this.state.loadingComponents.delete(name);
      this.state.concurrentLoadCount = Math.max(0, this.state.concurrentLoadCount - 1);
      
      // 处理等待队列
      this.processPendingLoads();
    }
  }

  /**
   * 预加载组件
   */
  async preloadComponent(componentData) {
    const { name } = componentData;
    
    // 检查是否已加载或正在加载
    if (this.state.loadedComponents.has(name) || this.state.loadingComponents.has(name)) {
      return;
    }
    
    // 检查缓存
    if (this.config.cacheEnabled) {
      const cached = await this.getFromCache(name);
      if (cached) {
        return; // 已经在缓存中
      }
    }
    
    try {
      // 执行预加载
      let component;
      
      if (componentData.importFn && this.compatibility.dynamicImport) {
        const result = await componentData.importFn();
        component = result.default || result;
      }
      
      // 缓存预加载的组件
      if (this.config.cacheEnabled && component) {
        await this.saveToCache(name, component);
      }
      
      this.state.preloadedComponents.add(name);
      this.state.stats.preloadedCount++;
      
      this.log(`组件预加载完成: ${name}`);
    } catch (error) {
      this.log(`组件预加载失败: ${name}`, 'error');
      // 预加载失败不影响正常流程
    }
  }

  /**
   * 渲染组件
   */
  renderComponent(componentData, component) {
    const { element } = componentData;
    
    // 恢复原始内容
    this.restoreOriginalContent(componentData);
    
    // 渲染组件
    if (typeof component === 'function') {
      // 如果是函数，执行它
      try {
        const result = component(element, componentData);
        
        // 如果返回的是元素，添加到容器
        if (result instanceof Element) {
          element.appendChild(result);
        }
      } catch (error) {
        this.handleRenderError(componentData, error);
      }
    } else if (component instanceof Element) {
      // 如果是元素，替换内容
      element.innerHTML = '';
      element.appendChild(component);
    } else if (typeof component === 'object' && component !== null) {
      // 尝试渲染对象
      this.renderComponentObject(element, component);
    } else if (typeof component === 'string') {
      // 如果是字符串，设置为 HTML
      element.innerHTML = component;
    }
    
    // 存储已加载的组件
    this.state.loadedComponents.set(componentData.name, component);
  }

  /**
   * 渲染组件对象
   */
  renderComponentObject(element, component) {
    // 检查是否有 render 方法
    if (typeof component.render === 'function') {
      const result = component.render();
      if (result instanceof Element) {
        element.appendChild(result);
      } else if (typeof result === 'string') {
        element.innerHTML = result;
      }
    } else if (component.html) {
      // 如果有 html 属性
      element.innerHTML = component.html;
      
      // 如果有 css
      if (component.css) {
        this.injectComponentStyles(element, component.css);
      }
      
      // 如果有 script
      if (component.script) {
        this.executeComponentScript(element, component.script);
      }
    }
  }

  /**
   * 注入组件样式
   */
  injectComponentStyles(element, css) {
    const styleElement = document.createElement('style');
    styleElement.textContent = css;
    element.appendChild(styleElement);
  }

  /**
   * 执行组件脚本
   */
  executeComponentScript(element, script) {
    try {
      // 创建脚本元素
      const scriptElement = document.createElement('script');
      scriptElement.textContent = `(function(element) { ${script} })(document.currentScript.parentNode);`;
      element.appendChild(scriptElement);
    } catch (error) {
      this.log('执行组件脚本失败', 'error');
    }
  }

  /**
   * 处理加载错误
   */
  handleLoadError(componentData, error) {
    const { name, element, errorComponent } = componentData;
    
    componentData.error = error;
    componentData.loading = false;
    componentData.loadEndTime = Date.now();
    
    // 更新统计
    this.state.stats.failedCount++;
    
    this.log(`组件加载失败: ${name} - ${error.message}`, 'error');
    
    // 渲染错误组件
    if (errorComponent) {
      if (typeof errorComponent === 'function') {
        const result = errorComponent(error, componentData);
        if (result instanceof Element) {
          element.innerHTML = '';
          element.appendChild(result);
        } else if (typeof result === 'string') {
          element.innerHTML = result;
        }
      } else if (typeof errorComponent === 'string') {
        element.innerHTML = errorComponent;
      }
    } else {
      // 默认错误信息
      element.innerHTML = `
        <div class="lazy-load-error">
          <p>组件加载失败</p>
          <button class="retry-button" data-component="${name}">重试</button>
        </div>
      `;
      
      // 添加重试事件
      const retryButton = element.querySelector('.retry-button');
      if (retryButton) {
        retryButton.addEventListener('click', () => {
          this.retryLoad(componentData);
        });
      }
    }
    
    // 触发错误回调
    this.triggerCallback('onLoadError', name, componentData.element, error);
  }

  /**
   * 处理渲染错误
   */
  handleRenderError(componentData, error) {
    const { name, element } = componentData;
    
    this.log(`组件渲染失败: ${name} - ${error.message}`, 'error');
    
    // 显示渲染错误
    element.innerHTML = `
      <div class="lazy-render-error">
        <p>组件渲染失败</p>
        <small>${error.message}</small>
      </div>
    `;
  }

  /**
   * 重试加载组件
   */
  retryLoad(componentData) {
    // 重置状态
    componentData.error = null;
    componentData.loaded = false;
    
    // 重新加载
    this.loadComponent(componentData);
  }

  /**
   * 处理等待队列
   */
  processPendingLoads() {
    // 如果还有并发加载槽位
    const availableSlots = this.config.maxConcurrentLoads - this.state.concurrentLoadCount;
    
    if (availableSlots > 0 && this.state.pendingLoads.size > 0) {
      // 按优先级排序
      const sortedPending = Array.from(this.state.pendingLoads.values()).sort((a, b) => {
        const priorityMap = { high: 0, normal: 1, low: 2 };
        return priorityMap[a.priority] - priorityMap[b.priority];
      });
      
      // 加载可用数量的组件
      for (let i = 0; i < Math.min(availableSlots, sortedPending.length); i++) {
        const componentData = sortedPending[i];
        this.state.pendingLoads.delete(componentData.name);
        this.loadComponent(componentData);
      }
    }
  }

  /**
   * 检查元素是否在视口内（降级方案）
   */
  checkElementInViewport(componentData) {
    const { element } = componentData;
    const rect = element.getBoundingClientRect();
    
    // 简化的视口检查
    const isInViewport = (
      rect.top <= (window.innerHeight || document.documentElement.clientHeight) + parseInt(this.config.rootMargin)
    );
    
    if (isInViewport) {
      this.loadComponent(componentData);
    }
  }

  /**
   * 检查所有元素（降级方案）
   */
  checkElements() {
    for (const componentData of this.state.observers.values()) {
      if (!componentData.loaded && !componentData.loading) {
        this.checkElementInViewport(componentData);
      }
    }
  }

  /**
   * 从缓存获取组件
   */
  async getFromCache(key) {
    if (this.cache) {
      // 使用全局缓存管理器
      return await this.cache.get(`lazy_component_${key}`);
    } else if (this.internalCache) {
      // 使用内部缓存
      return this.internalCache.get(key);
    }
    
    return null;
  }

  /**
   * 保存组件到缓存
   */
  async saveToCache(key, component) {
    if (this.cache) {
      // 使用全局缓存管理器
      await this.cache.set(`lazy_component_${key}`, component, {
        ttl: 3600000, // 缓存1小时
        storageType: 'memoryCache' // 组件优先存储在内存中
      });
    } else if (this.internalCache) {
      // 使用内部缓存
      this.internalCache.set(key, component);
    }
  }

  /**
   * 更新统计信息
   */
  updateStats(componentData) {
    const loadTime = componentData.loadEndTime - componentData.loadStartTime;
    
    this.state.stats.loadedCount++;
    this.state.stats.totalLoadTime += loadTime;
    this.state.stats.averageLoadTime = 
      this.state.stats.totalLoadTime / this.state.stats.loadedCount;
  }

  /**
   * 获取统计信息
   */
  getStats() {
    return { ...this.state.stats };
  }

  /**
   * 触发回调
   */
  triggerCallback(callbackName, ...args) {
    const callback = this.config[callbackName];
    
    if (typeof callback === 'function') {
      try {
        callback(...args);
      } catch (error) {
        this.log(`${callbackName} 回调执行失败`, 'error');
      }
    }
  }

  /**
   * 手动触发加载
   */
  loadByName(name) {
    // 查找组件数据
    for (const componentData of this.state.observers.values()) {
      if (componentData.name === name && !componentData.loaded && !componentData.loading) {
        this.loadComponent(componentData);
        return true;
      }
    }
    
    return false;
  }

  /**
   * 预加载多个组件
   */
  async preloadMultiple(components) {
    if (!Array.isArray(components)) {
      return;
    }
    
    const promises = components.map(component => {
      if (typeof component === 'function') {
        return this.preloadComponent({
          name: `preload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          importFn: component
        });
      }
      return Promise.resolve();
    });
    
    await Promise.all(promises);
  }

  /**
   * 处理可见性变化
   */
  handleVisibilityChange() {
    // 当页面隐藏时，可以暂停某些加载
    if (document.hidden) {
      this.log('页面隐藏，暂停非关键加载');
      // 实现暂停逻辑...
    } else {
      this.log('页面显示，恢复加载');
      // 实现恢复逻辑...
    }
  }

  /**
   * 处理网络状态变化
   */
  handleNetworkChange() {
    if (navigator.onLine) {
      this.log('网络连接恢复，重试失败的加载');
      // 重试失败的加载...
    } else {
      this.log('网络连接断开，暂停加载');
      // 暂停加载...
    }
  }

  /**
   * 清除特定组件
   */
  clearComponent(name) {
    // 从缓存中移除
    if (this.cache) {
      this.cache.delete(`lazy_component_${name}`);
    } else if (this.internalCache) {
      this.internalCache.delete(name);
    }
    
    // 从状态中移除
    this.state.loadedComponents.delete(name);
    this.state.preloadedComponents.delete(name);
    
    this.log(`组件已清除: ${name}`);
  }

  /**
   * 清除所有缓存
   */
  async clearCache() {
    if (this.cache) {
      // 使用缓存管理器清除所有懒加载组件缓存
      const keys = await this.cache.keys();
      for (const key of keys) {
        if (key.startsWith('lazy_component_')) {
          await this.cache.delete(key);
        }
      }
    } else if (this.internalCache) {
      this.internalCache.clear();
    }
    
    // 清空状态
    this.state.loadedComponents.clear();
    this.state.preloadedComponents.clear();
    
    this.log('缓存已清空');
  }

  /**
   * 重置懒加载管理器
   */
  reset() {
    // 停止所有观察
    for (const element of this.state.observers.keys()) {
      this.stopObserving(element);
    }
    
    // 清空状态
    this.state.observers.clear();
    this.state.loadingComponents.clear();
    this.state.loadedComponents.clear();
    this.state.preloadedComponents.clear();
    this.state.pendingLoads.clear();
    this.state.concurrentLoadCount = 0;
    
    // 重置统计
    this.state.stats = {
      loadedCount: 0,
      failedCount: 0,
      preloadedCount: 0,
      totalLoadTime: 0,
      averageLoadTime: 0
    };
    
    this.log('懒加载管理器已重置');
  }

  /**
   * 销毁懒加载管理器
   */
  destroy() {
    this.log('销毁懒加载管理器...');
    
    // 清除观察器
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect();
    }
    
    if (this.preloadObserver) {
      this.preloadObserver.disconnect();
    }
    
    // 移除事件监听器
    if (this.useFallback && this.debouncedCheck) {
      window.removeEventListener('scroll', this.debouncedCheck);
      window.removeEventListener('resize', this.debouncedCheck);
      window.removeEventListener('orientationchange', this.debouncedCheck);
    }
    
    document.removeEventListener('visibilitychange', this.handleVisibilityChange);
    window.removeEventListener('online', this.handleNetworkChange);
    window.removeEventListener('offline', this.handleNetworkChange);
    
    // 重置
    this.reset();
    
    this.log('懒加载管理器已销毁');
  }

  /**
   * 日志记录
   */
  log(message, level = 'log') {
    if (!this.config.debug) {
      return;
    }
    
    const timestamp = new Date().toISOString();
    const logMessage = `[LazyLoadManager] ${timestamp} ${message}`;
    
    switch (level) {
      case 'log':
        console.log(logMessage);
        break;
      case 'warn':
        console.warn(logMessage);
        break;
      case 'error':
        console.error(logMessage);
        break;
      case 'info':
        console.info(logMessage);
        break;
      default:
        console.log(logMessage);
    }
  }

  /**
   * 防抖函数
   */
  debounce(func, wait) {
    let timeout;
    
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  /**
   * 节流函数
   */
  throttle(func, limit) {
    let inThrottle;
    
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }
}

// 创建懒加载管理器实例
const lazyLoadManager = new LazyLoadManager({
  rootMargin: '100px 0px',
  threshold: 0.1,
  preloadDistance: 500,
  maxConcurrentLoads: 3,
  cacheEnabled: true,
  useCacheManager: true,
  timeout: 30000,
  debug: false
});

// 定义常用的组件加载辅助函数
LazyLoadManager.prototype.loadImage = function(element, src, options = {}) {
  return this.observe(element, {
    name: options.name || `image_${Date.now()}`,
    loadFn: async () => {
      return new Promise((resolve, reject) => {
        const img = new Image();
        
        if (options.crossOrigin) {
          img.crossOrigin = options.crossOrigin;
        }
        
        img.onload = () => resolve(img);
        img.onerror = reject;
        
        // 设置图片属性
        if (options.width) img.width = options.width;
        if (options.height) img.height = options.height;
        
        // 支持图片加载优先级
        if (options.priority && 'fetchPriority' in img) {
          img.fetchPriority = options.priority; // high, low, auto
        }
        
        // 设置图片源
        if (options.srcset) {
          img.srcset = options.srcset;
        }
        
        if (options.sizes) {
          img.sizes = options.sizes;
        }
        
        img.src = src;
      });
    },
    placeholder: options.placeholder || '<div class="image-placeholder"></div>',
    errorComponent: options.errorComponent || '<div class="image-error">图片加载失败</div>',
    priority: options.priority || 'normal'
  });
};

LazyLoadManager.prototype.loadScript = function(element, src, options = {}) {
  return this.observe(element, {
    name: options.name || `script_${Date.now()}`,
    loadFn: async () => {
      return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        
        if (options.type) script.type = options.type;
        if (options.async !== undefined) script.async = options.async;
        if (options.defer !== undefined) script.defer = options.defer;
        if (options.crossOrigin) script.crossOrigin = options.crossOrigin;
        if (options.integrity) script.integrity = options.integrity;
        
        script.onload = () => resolve({ script, loaded: true });
        script.onerror = reject;
        
        script.src = src;
        document.head.appendChild(script);
      });
    },
    priority: options.priority || 'low'
  });
};

LazyLoadManager.prototype.loadStyle = function(element, href, options = {}) {
  return this.observe(element, {
    name: options.name || `style_${Date.now()}`,
    loadFn: async () => {
      return new Promise((resolve, reject) => {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.type = 'text/css';
        
        if (options.media) link.media = options.media;
        if (options.crossOrigin) link.crossOrigin = options.crossOrigin;
        if (options.integrity) link.integrity = options.integrity;
        
        link.onload = () => resolve({ link, loaded: true });
        link.onerror = reject;
        
        link.href = href;
        document.head.appendChild(link);
      });
    },
    priority: options.priority || 'low'
  });
};

// 导出
if (typeof window !== 'undefined') {
  window.LazyLoadManager = LazyLoadManager;
  window.lazyLoadManager = lazyLoadManager;
}

export { LazyLoadManager, lazyLoadManager };