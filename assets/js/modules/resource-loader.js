// 资源加载管理器 - 优化页面资源加载性能
class ResourceLoader {
  constructor(options = {}) {
    // 加载配置
    this.config = {
      preloadThreshold: options.preloadThreshold || 1000, // 预加载阈值（毫秒）
      lazyLoadDistance: options.lazyLoadDistance || 300, // 延迟加载触发距离（像素）
      resourceTimeout: options.resourceTimeout || 10000, // 资源加载超时（毫秒）
      maxConcurrentLoads: options.maxConcurrentLoads || 5, // 最大并发加载数
      retryAttempts: options.retryAttempts || 2, // 重试次数
      retryDelay: options.retryDelay || 1000, // 重试延迟（毫秒）
      cacheEnabled: options.cacheEnabled !== false, // 是否启用缓存
      debug: options.debug || false, // 是否启用调试
      ...options
    };
    
    // 资源类型配置
    this.resourceTypes = {
      image: {
        extensions: ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico'],
        test: (url) => this.testResourceType(url, 'image'),
        loader: this.loadImage.bind(this)
      },
      script: {
        extensions: ['.js'],
        test: (url) => this.testResourceType(url, 'script'),
        loader: this.loadScript.bind(this)
      },
      style: {
        extensions: ['.css'],
        test: (url) => this.testResourceType(url, 'style'),
        loader: this.loadStyle.bind(this)
      },
      font: {
        extensions: ['.woff', '.woff2', '.ttf', '.otf', '.eot'],
        test: (url) => this.testResourceType(url, 'font'),
        loader: this.loadFont.bind(this)
      },
      audio: {
        extensions: ['.mp3', '.wav', '.ogg', '.aac'],
        test: (url) => this.testResourceType(url, 'audio'),
        loader: this.loadAudio.bind(this)
      },
      video: {
        extensions: ['.mp4', '.webm', '.ogg'],
        test: (url) => this.testResourceType(url, 'video'),
        loader: this.loadVideo.bind(this)
      },
      json: {
        extensions: ['.json'],
        test: (url) => this.testResourceType(url, 'json'),
        loader: this.loadJson.bind(this)
      }
    };
    
    // 资源状态跟踪
    this.loadedResources = new Map(); // 已加载资源
    this.loadingResources = new Set(); // 正在加载资源
    this.failedResources = new Map(); // 加载失败资源
    
    // 加载队列
    this.loadQueue = [];
    
    // 当前并发加载数
    this.concurrentLoads = 0;
    
    // 事件监听器
    this.listeners = new Map();
    
    // 资源预加载映射
    this.preloadMap = new Map();
    
    // 缓存
    this.resourceCache = new Map();
    
    // 初始化状态
    this.isInitialized = false;
    
    // 性能指标
    this.performanceMetrics = {
      resourcesLoaded: 0,
      resourcesFailed: 0,
      totalLoadTime: 0,
      averageLoadTime: 0
    };
  }

  /**
   * 初始化资源加载管理器
   */
  initialize() {
    if (this.isInitialized) {
      console.warn('资源加载管理器已经初始化');
      return this;
    }
    
    console.log('初始化资源加载管理器...');
    
    // 设置事件监听
    this.setupEventListeners();
    
    // 扫描页面资源
    this.scanPageResources();
    
    // 设置延迟加载
    this.setupLazyLoading();
    
    // 启用调试
    if (this.config.debug) {
      this.enableDebugging();
    }
    
    this.isInitialized = true;
    console.log('资源加载管理器初始化完成');
    
    return this;
  }

  /**
   * 设置事件监听
   */
  setupEventListeners() {
    // 监听页面可见性变化
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        this.resumeLoading();
      } else {
        this.pauseLoading();
      }
    });
    
    // 监听页面滚动，用于延迟加载
    window.addEventListener('scroll', this.handleScroll.bind(this), { passive: true });
    
    // 监听页面调整大小，用于延迟加载
    window.addEventListener('resize', this.handleResize.bind(this), { passive: true });
  }

  /**
   * 扫描页面资源
   */
  scanPageResources() {
    console.log('扫描页面资源...');
    
    // 扫描图片
    this.scanImages();
    
    // 扫描脚本
    this.scanScripts();
    
    // 扫描样式
    this.scanStyles();
    
    // 扫描字体
    this.scanFonts();
    
    console.log('页面资源扫描完成');
  }

  /**
   * 扫描图片
   */
  scanImages() {
    const images = document.querySelectorAll('img:not([data-loaded])');
    
    images.forEach(img => {
      const src = img.getAttribute('src');
      if (src) {
        this.registerResource(src, 'image');
        img.setAttribute('data-loaded', 'true');
      }
    });
  }

  /**
   * 扫描脚本
   */
  scanScripts() {
    const scripts = document.querySelectorAll('script:not([data-loaded])');
    
    scripts.forEach(script => {
      const src = script.getAttribute('src');
      if (src) {
        this.registerResource(src, 'script');
        script.setAttribute('data-loaded', 'true');
      }
    });
  }

  /**
   * 扫描样式
   */
  scanStyles() {
    const links = document.querySelectorAll('link[rel="stylesheet"]:not([data-loaded])');
    
    links.forEach(link => {
      const href = link.getAttribute('href');
      if (href) {
        this.registerResource(href, 'style');
        link.setAttribute('data-loaded', 'true');
      }
    });
  }

  /**
   * 扫描字体
   */
  scanFonts() {
    // 从字体加载事件监听字体
    document.fonts.forEach(fontFace => {
      const family = fontFace.family;
      this.registerResource(family, 'font');
    });
  }

  /**
   * 设置延迟加载
   */
  setupLazyLoading() {
    console.log('设置延迟加载...');
    
    // 查找所有带有 data-src 属性的元素
    const lazyElements = document.querySelectorAll('[data-src]');
    
    lazyElements.forEach(element => {
      this.registerLazyResource(element);
    });
    
    // 初始检查
    this.checkLazyElements();
    
    console.log('延迟加载设置完成');
  }

  /**
   * 注册延迟加载资源
   */
  registerLazyResource(element) {
    const src = element.getAttribute('data-src');
    if (!src) return;
    
    // 确定资源类型
    const type = this.detectResourceType(src);
    
    // 存储元素和资源信息
    element._lazyResourceInfo = { src, type, loaded: false };
    
    // 对于图片，使用 Intersection Observer
    if (type === 'image') {
      this.setupIntersectionObserver(element);
    }
  }

  /**
   * 设置 Intersection Observer
   */
  setupIntersectionObserver(element) {
    if (!('IntersectionObserver' in window)) {
      // 降级处理
      this.loadLazyResource(element);
      return;
    }
    
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            this.loadLazyResource(element);
            observer.unobserve(element);
          }
        });
      },
      {
        rootMargin: `${this.config.lazyLoadDistance}px`,
        threshold: 0.01
      }
    );
    
    observer.observe(element);
  }

  /**
   * 加载延迟资源
   */
  async loadLazyResource(element) {
    const info = element._lazyResourceInfo;
    if (!info || info.loaded) return;
    
    try {
      // 加载资源
      await this.loadResource(info.src, info.type);
      
      // 更新元素
      if (element.tagName.toLowerCase() === 'img') {
        element.src = info.src;
      } else {
        // 其他类型元素的处理
        element.style.backgroundImage = `url(${info.src})`;
      }
      
      // 标记为已加载
      info.loaded = true;
      element.classList.add('lazy-loaded');
      
      // 移除 data-src 属性
      element.removeAttribute('data-src');
    } catch (error) {
      console.error(`加载延迟资源失败: ${info.src}`, error);
      this.handleResourceError(info.src, error);
    }
  }

  /**
   * 检查延迟加载元素
   */
  checkLazyElements() {
    const lazyElements = document.querySelectorAll('[data-src]:not(.lazy-loaded)');
    
    lazyElements.forEach(element => {
      if (this.isElementInViewport(element)) {
        this.loadLazyResource(element);
      }
    });
  }

  /**
   * 检查元素是否在视口中
   */
  isElementInViewport(element) {
    const rect = element.getBoundingClientRect();
    const offset = this.config.lazyLoadDistance;
    
    return (
      rect.top - offset < window.innerHeight &&
      rect.bottom + offset > 0 &&
      rect.left - offset < window.innerWidth &&
      rect.right + offset > 0
    );
  }

  /**
   * 处理滚动事件
   */
  handleScroll() {
    this.checkLazyElements();
  }

  /**
   * 处理调整大小事件
   */
  handleResize() {
    this.checkLazyElements();
  }

  /**
   * 预加载资源
   */
  preload(url, type) {
    if (this.isResourceLoaded(url)) {
      return Promise.resolve(this.loadedResources.get(url));
    }
    
    // 检测资源类型
    if (!type) {
      type = this.detectResourceType(url);
    }
    
    // 添加到预加载映射
    this.preloadMap.set(url, type);
    
    // 使用 Link Preload
    this.useLinkPreload(url, type);
    
    // 返回加载 Promise
    return this.loadResource(url, type);
  }

  /**
   * 使用 Link Preload
   */
  useLinkPreload(url, type) {
    if (!('requestIdleCallback' in window)) {
      this.createPreloadLink(url, type);
      return;
    }
    
    // 使用 requestIdleCallback 在空闲时预加载
    requestIdleCallback(() => {
      this.createPreloadLink(url, type);
    });
  }

  /**
   * 创建预加载链接
   */
  createPreloadLink(url, type) {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = url;
    link.as = this.getResourceTypeAs(type);
    
    // 添加到 head
    document.head.appendChild(link);
  }

  /**
   * 获取资源类型对应的 as 属性
   */
  getResourceTypeAs(type) {
    const typeMap = {
      image: 'image',
      script: 'script',
      style: 'style',
      font: 'font',
      audio: 'audio',
      video: 'video',
      json: 'fetch'
    };
    
    return typeMap[type] || 'fetch';
  }

  /**
   * 加载资源
   */
  loadResource(url, type) {
    // 检查缓存
    if (this.config.cacheEnabled && this.isResourceCached(url)) {
      return Promise.resolve(this.getCachedResource(url));
    }
    
    // 检查是否正在加载
    if (this.isResourceLoading(url)) {
      return new Promise((resolve, reject) => {
        this.once(`${url}:loaded`, resolve);
        this.once(`${url}:failed`, reject);
      });
    }
    
    // 标记为正在加载
    this.loadingResources.add(url);
    
    // 检测资源类型
    if (!type) {
      type = this.detectResourceType(url);
    }
    
    // 记录开始时间
    const startTime = performance.now();
    
    // 创建加载 Promise
    const loadPromise = this.createLoadPromise(url, type, startTime);
    
    // 添加到队列
    this.addToLoadQueue(url, loadPromise);
    
    return loadPromise;
  }

  /**
   * 创建加载 Promise
   */
  createLoadPromise(url, type, startTime) {
    return new Promise((resolve, reject) => {
      // 获取资源加载器
      const resourceType = this.resourceTypes[type];
      if (!resourceType) {
        reject(new Error(`未知的资源类型: ${type}`));
        return;
      }
      
      // 设置超时
      const timeout = setTimeout(() => {
        reject(new Error(`资源加载超时: ${url}`));
      }, this.config.resourceTimeout);
      
      // 执行加载
      resourceType.loader(url)
        .then(data => {
          clearTimeout(timeout);
          
          // 记录加载时间
          const loadTime = performance.now() - startTime;
          
          // 更新性能指标
          this.updatePerformanceMetrics(loadTime, true);
          
          // 记录加载状态
          this.recordResourceLoaded(url, data, loadTime);
          
          // 触发事件
          this.emit(`${url}:loaded`, { url, type, data, loadTime });
          this.emit('resourceLoaded', { url, type, data, loadTime });
          
          resolve(data);
        })
        .catch(error => {
          clearTimeout(timeout);
          
          // 处理错误和重试
          this.handleResourceError(url, error, resolve, reject);
        });
    });
  }

  /**
   * 添加到加载队列
   */
  addToLoadQueue(url, promise) {
    this.loadQueue.push({ url, promise });
    this.processLoadQueue();
  }

  /**
   * 处理加载队列
   */
  async processLoadQueue() {
    // 检查并发限制
    if (this.concurrentLoads >= this.config.maxConcurrentLoads) {
      return;
    }
    
    // 获取下一个待加载的资源
    const nextLoad = this.loadQueue.shift();
    if (!nextLoad) {
      return;
    }
    
    // 增加并发计数
    this.concurrentLoads++;
    
    try {
      // 等待加载完成
      await nextLoad.promise;
    } finally {
      // 减少并发计数
      this.concurrentLoads--;
      
      // 继续处理队列
      this.processLoadQueue();
    }
  }

  /**
   * 处理资源加载错误
   */
  handleResourceError(url, error, resolve, reject) {
    // 增加失败计数
    let failCount = 0;
    if (this.failedResources.has(url)) {
      failCount = this.failedResources.get(url).count + 1;
    }
    
    // 记录失败信息
    this.failedResources.set(url, {
      url,
      error: error.message,
      count: failCount,
      timestamp: Date.now()
    });
    
    // 更新性能指标
    this.updatePerformanceMetrics(0, false);
    
    // 触发事件
    this.emit(`${url}:failed`, { url, error });
    this.emit('resourceFailed', { url, error });
    
    // 判断是否重试
    if (failCount < this.config.retryAttempts) {
      console.warn(`重试加载资源: ${url} (${failCount + 1}/${this.config.retryAttempts})`);
      
      // 延迟重试
      setTimeout(() => {
        this.loadResource(url)
          .then(resolve)
          .catch(reject);
      }, this.config.retryDelay);
    } else {
      // 达到最大重试次数
      reject(error);
    }
  }

  /**
   * 资源加载器实现
   */
  loadImage(url) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error(`图片加载失败: ${url}`));
      
      // 设置跨域属性
      if (this.isCrossOrigin(url)) {
        img.crossOrigin = 'anonymous';
      }
      
      img.src = url;
    });
  }

  /**
   * 加载脚本
   */
  loadScript(url) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      
      script.onload = () => resolve(script);
      script.onerror = () => reject(new Error(`脚本加载失败: ${url}`));
      
      // 设置属性
      script.src = url;
      script.async = true;
      script.defer = true;
      
      // 添加到文档
      document.body.appendChild(script);
    });
  }

  /**
   * 加载样式
   */
  loadStyle(url) {
    return new Promise((resolve, reject) => {
      const link = document.createElement('link');
      
      link.onload = () => resolve(link);
      link.onerror = () => reject(new Error(`样式加载失败: ${url}`));
      
      // 设置属性
      link.rel = 'stylesheet';
      link.href = url;
      
      // 添加到文档
      document.head.appendChild(link);
    });
  }

  /**
   * 加载字体
   */
  loadFont(url) {
    return new Promise((resolve, reject) => {
      // 创建 FontFace
      const fontName = this.extractFontName(url);
      const fontFace = new FontFace(fontName, `url(${url})`);
      
      fontFace.load()
        .then(() => {
          // 添加到文档字体集合
          document.fonts.add(fontFace);
          resolve(fontFace);
        })
        .catch(error => reject(new Error(`字体加载失败: ${url}`, { cause: error })));
    });
  }

  /**
   * 加载音频
   */
  loadAudio(url) {
    return new Promise((resolve, reject) => {
      const audio = new Audio();
      
      audio.addEventListener('canplaythrough', () => resolve(audio));
      audio.addEventListener('error', () => reject(new Error(`音频加载失败: ${url}`)));
      
      audio.src = url;
      audio.preload = 'auto';
    });
  }

  /**
   * 加载视频
   */
  loadVideo(url) {
    return new Promise((resolve, reject) => {
      const video = document.createElement('video');
      
      video.addEventListener('canplaythrough', () => resolve(video));
      video.addEventListener('error', () => reject(new Error(`视频加载失败: ${url}`)));
      
      video.src = url;
      video.preload = 'auto';
    });
  }

  /**
   * 加载 JSON
   */
  loadJson(url) {
    return fetch(url)
      .then(response => {
        if (!response.ok) {
          throw new Error(`JSON 加载失败: ${response.status} ${response.statusText}`);
        }
        return response.json();
      });
  }

  /**
   * 资源工具方法
   */
  registerResource(url, type) {
    // 检测资源类型
    if (!type) {
      type = this.detectResourceType(url);
    }
    
    // 记录资源
    this.loadedResources.set(url, { url, type, loaded: true });
  }

  /**
   * 检测资源类型
   */
  detectResourceType(url) {
    for (const [type, config] of Object.entries(this.resourceTypes)) {
      if (config.test(url)) {
        return type;
      }
    }
    
    return 'unknown';
  }

  /**
   * 测试资源类型
   */
  testResourceType(url, type) {
    const config = this.resourceTypes[type];
    if (!config) return false;
    
    const lowerUrl = url.toLowerCase();
    return config.extensions.some(ext => lowerUrl.endsWith(ext));
  }

  /**
   * 提取字体名称
   */
  extractFontName(url) {
    // 从 URL 中提取字体名称
    const parts = url.split('/');
    const fileName = parts[parts.length - 1];
    const nameParts = fileName.split('.');
    nameParts.pop(); // 移除扩展名
    
    return nameParts.join('.');
  }

  /**
   * 检查是否为跨域 URL
   */
  isCrossOrigin(url) {
    try {
      const urlObj = new URL(url);
      return urlObj.origin !== window.location.origin;
    } catch (error) {
      return false;
    }
  }

  /**
   * 检查资源是否已加载
   */
  isResourceLoaded(url) {
    return this.loadedResources.has(url);
  }

  /**
   * 检查资源是否正在加载
   */
  isResourceLoading(url) {
    return this.loadingResources.has(url);
  }

  /**
   * 记录资源加载完成
   */
  recordResourceLoaded(url, data, loadTime) {
    // 从加载集合中移除
    this.loadingResources.delete(url);
    
    // 添加到已加载集合
    this.loadedResources.set(url, {
      url,
      data,
      loadTime,
      loadedAt: Date.now()
    });
    
    // 添加到缓存
    if (this.config.cacheEnabled) {
      this.cacheResource(url, data);
    }
  }

  /**
   * 缓存管理
   */
  cacheResource(url, data) {
    this.resourceCache.set(url, {
      data,
      timestamp: Date.now()
    });
  }

  /**
   * 检查资源是否已缓存
   */
  isResourceCached(url) {
    return this.resourceCache.has(url);
  }

  /**
   * 获取缓存的资源
   */
  getCachedResource(url) {
    const cached = this.resourceCache.get(url);
    if (cached) {
      return cached.data;
    }
    return null;
  }

  /**
   * 清除资源缓存
   */
  clearCache(url) {
    if (url) {
      this.resourceCache.delete(url);
    } else {
      this.resourceCache.clear();
    }
  }

  /**
   * 性能监控
   */
  updatePerformanceMetrics(loadTime, success) {
    if (success) {
      this.performanceMetrics.resourcesLoaded++;
      this.performanceMetrics.totalLoadTime += loadTime;
      this.performanceMetrics.averageLoadTime = 
        this.performanceMetrics.totalLoadTime / this.performanceMetrics.resourcesLoaded;
    } else {
      this.performanceMetrics.resourcesFailed++;
    }
  }

  /**
   * 获取性能指标
   */
  getPerformanceMetrics() {
    return { ...this.performanceMetrics };
  }

  /**
   * 事件系统
   */
  on(event, listener) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    
    this.listeners.get(event).push(listener);
    return this;
  }

  /**
   * 一次性事件监听
   */
  once(event, listener) {
    const onceWrapper = (...args) => {
      listener(...args);
      this.off(event, onceWrapper);
    };
    
    this.on(event, onceWrapper);
    return this;
  }

  /**
   * 移除事件监听
   */
  off(event, listener) {
    if (!this.listeners.has(event)) return this;
    
    const listeners = this.listeners.get(event);
    const index = listeners.indexOf(listener);
    
    if (index !== -1) {
      listeners.splice(index, 1);
    }
    
    return this;
  }

  /**
   * 触发事件
   */
  emit(event, data) {
    if (!this.listeners.has(event)) return this;
    
    const listeners = this.listeners.get(event);
    listeners.forEach(listener => {
      try {
        listener(data);
      } catch (error) {
        console.error(`事件处理器错误: ${event}`, error);
      }
    });
    
    return this;
  }

  /**
   * 加载控制
   */
  pauseLoading() {
    // 暂停加载队列处理
    this.isPaused = true;
    this.emit('loadingPaused');
  }

  /**
   * 恢复加载
   */
  resumeLoading() {
    if (this.isPaused) {
      this.isPaused = false;
      this.processLoadQueue();
      this.emit('loadingResumed');
    }
  }

  /**
   * 取消资源加载
   */
  cancelLoad(url) {
    // 从加载队列中移除
    this.loadQueue = this.loadQueue.filter(load => load.url !== url);
    
    // 从加载集合中移除
    this.loadingResources.delete(url);
    
    // 触发取消事件
    this.emit(`${url}:cancelled`);
    
    return true;
  }

  /**
   * 批量预加载
   */
  preloadBatch(resources) {
    const promises = resources.map(resource => {
      if (typeof resource === 'string') {
        return this.preload(resource);
      } else if (resource && resource.url) {
        return this.preload(resource.url, resource.type);
      }
      return Promise.resolve();
    });
    
    return Promise.all(promises);
  }

  /**
   * 启用调试
   */
  enableDebugging() {
    console.log('启用资源加载调试模式');
    
    // 添加调试事件监听
    this.on('resourceLoaded', (data) => {
      console.log(`[资源加载器] 已加载: ${data.url} (${data.loadTime.toFixed(2)}ms)`);
    });
    
    this.on('resourceFailed', (data) => {
      console.error(`[资源加载器] 加载失败: ${data.url}`, data.error);
    });
  }

  /**
   * 获取状态
   */
  getState() {
    return {
      initialized: this.isInitialized,
      resourcesLoaded: this.loadedResources.size,
      resourcesLoading: this.loadingResources.size,
      resourcesFailed: this.failedResources.size,
      queueLength: this.loadQueue.length,
      concurrentLoads: this.concurrentLoads,
      performance: this.getPerformanceMetrics()
    };
  }

  /**
   * 清理资源加载管理器
   */
  destroy() {
    // 清除事件监听
    window.removeEventListener('scroll', this.handleScroll);
    window.removeEventListener('resize', this.handleResize);
    
    // 清空队列和状态
    this.loadQueue = [];
    this.loadingResources.clear();
    
    // 重置状态
    this.isInitialized = false;
    this.isPaused = false;
    
    console.log('资源加载管理器已销毁');
  }
}

// 创建资源加载管理器实例
const resourceLoader = new ResourceLoader({
  preloadThreshold: 500,
  lazyLoadDistance: 300,
  maxConcurrentLoads: 5,
  retryAttempts: 2,
  debug: false
});

// 导出
if (typeof window !== 'undefined') {
  window.ResourceLoader = ResourceLoader;
  window.resourceLoader = resourceLoader;
}

export { ResourceLoader, resourceLoader };