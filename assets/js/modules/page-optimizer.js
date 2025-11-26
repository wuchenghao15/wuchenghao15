// 页面优化器 - 负责页面加载优化、资源预加载、渲染性能优化等
class PageOptimizer {
  constructor(componentManager = null, hierarchyPlanner = null) {
    this.componentManager = componentManager || window.componentManager;
    this.hierarchyPlanner = hierarchyPlanner || window.intelligentHierarchyPlanner;
    this.performanceData = {
      pageLoadTime: 0,
      domInteractiveTime: 0,
      domCompleteTime: 0,
      resourcesLoaded: 0,
      totalResources: 0,
      renderTime: 0
    };
    this.preloadResources = [];
    this.resourceCache = {};
    this.lazyLoadElements = [];
    this.isInitialized = false;
    this.optimizationEnabled = true;
    
    // 初始化页面优化器
    this.initialize();
  }

  /**
   * 初始化页面优化器
   */
  initialize() {
    if (this.isInitialized) return;
    
    // 开始性能监控
    this.startPerformanceMonitoring();
    
    // 设置事件监听
    this.setupEventListeners();
    
    // 检测浏览器支持的优化特性
    this.detectOptimizationFeatures();
    
    this.isInitialized = true;
    console.log('页面优化器初始化完成');
  }

  /**
   * 开始性能监控
   */
  startPerformanceMonitoring() {
    // 记录页面加载开始时间
    this.performanceData.startTime = performance.now();
    
    // 监听页面加载事件
    window.addEventListener('load', this.handlePageLoad.bind(this));
    document.addEventListener('DOMContentLoaded', this.handleDomContentLoaded.bind(this));
    
    // 定期收集性能数据
    setInterval(() => this.collectPerformanceData(), 5000);
  }

  /**
   * 设置事件监听器
   */
  setupEventListeners() {
    // 监听组件加载完成事件
    window.componentBus?.on('component:loaded', this.handleComponentLoaded.bind(this));
    
    // 监听页面渲染完成事件
    window.componentBus?.on('page:rendered', this.handlePageRendered.bind(this));
    
    // 监听层级重新规划事件
    window.componentBus?.on('hierarchy:replanned', this.optimizeForNewHierarchy.bind(this));
    
    // 监听滚动事件，用于懒加载
    window.addEventListener('scroll', this.handleScroll.bind(this), { passive: true });
    
    // 监听调整大小事件
    window.addEventListener('resize', this.handleResize.bind(this), { passive: true });
  }

  /**
   * 检测浏览器支持的优化特性
   */
  detectOptimizationFeatures() {
    this.supportedFeatures = {
      requestIdleCallback: 'requestIdleCallback' in window,
      intersectionObserver: 'IntersectionObserver' in window,
      performanceObserver: 'PerformanceObserver' in window,
      prefetch: 'prefetch' in document.createElement('link'),
      preload: 'preload' in document.createElement('link'),
      asyncFunctions: typeof asyncFunction === 'function'
    };
    
    console.log('浏览器支持的优化特性:', this.supportedFeatures);
  }

  /**
   * 优化页面加载
   */
  optimizePageLoad() {
    if (!this.optimizationEnabled) return;
    
    // 优化资源加载顺序
    this.optimizeResourceLoading();
    
    // 设置懒加载
    this.setupLazyLoading();
    
    // 优化DOM
    this.optimizeDom();
    
    // 优化CSS加载
    this.optimizeCssLoading();
    
    // 优化JavaScript执行
    this.optimizeJavaScriptExecution();
  }

  /**
   * 优化资源加载顺序
   */
  optimizeResourceLoading() {
    // 识别关键资源
    const criticalResources = this.identifyCriticalResources();
    
    // 预加载关键资源
    criticalResources.forEach(resource => this.preloadResource(resource));
    
    // 对非关键资源进行延迟加载
    const nonCriticalResources = this.identifyNonCriticalResources();
    nonCriticalResources.forEach(resource => this.deferResource(resource));
  }

  /**
   * 识别关键资源
   * @returns {Array} 关键资源列表
   */
  identifyCriticalResources() {
    const resources = [];
    
    // 识别关键CSS
    const criticalCss = Array.from(document.querySelectorAll('link[rel="stylesheet"]')).filter(link => 
      !link.hasAttribute('media') || link.getAttribute('media') === 'all'
    ).map(link => link.href);
    resources.push(...criticalCss);
    
    // 识别关键JavaScript
    const criticalJs = Array.from(document.querySelectorAll('script:not([defer]):not([async])')).map(
      script => script.src
    ).filter(src => src);
    resources.push(...criticalJs);
    
    // 识别首屏图片
    const aboveTheFoldImages = this.findAboveTheFoldImages();
    resources.push(...aboveTheFoldImages.map(img => img.src));
    
    return [...new Set(resources)];
  }

  /**
   * 识别非关键资源
   * @returns {Array} 非关键资源列表
   */
  identifyNonCriticalResources() {
    const resources = [];
    
    // 识别非关键图片
    const belowTheFoldImages = this.findBelowTheFoldImages();
    resources.push(...belowTheFoldImages);
    
    return resources;
  }

  /**
   * 预加载资源
   * @param {String} resourceUrl - 资源URL
   * @param {String} resourceType - 资源类型
   */
  preloadResource(resourceUrl, resourceType = null) {
    if (!resourceUrl || this.preloadResources.includes(resourceUrl)) return;
    
    // 确定资源类型
    if (!resourceType) {
      const extension = resourceUrl.split('.').pop().toLowerCase();
      if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(extension)) {
        resourceType = 'image';
      } else if (['js'].includes(extension)) {
        resourceType = 'script';
      } else if (['css'].includes(extension)) {
        resourceType = 'style';
      }
    }
    
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = resourceUrl;
    
    if (resourceType) {
      link.as = resourceType;
    }
    
    link.onload = () => {
      console.log(`资源预加载完成: ${resourceUrl}`);
      this.performanceData.resourcesLoaded++;
    };
    
    link.onerror = () => {
      console.error(`资源预加载失败: ${resourceUrl}`);
    };
    
    document.head.appendChild(link);
    this.preloadResources.push(resourceUrl);
  }

  /**
   * 延迟加载资源
   * @param {Object} resource - 资源对象
   */
  deferResource(resource) {
    // 对于图片，设置data-src属性，移除src属性
    if (resource.tagName === 'IMG') {
      resource.setAttribute('data-src', resource.src);
      resource.removeAttribute('src');
      this.lazyLoadElements.push(resource);
    }
    
    // 对于其他资源，可以添加到懒加载队列
  }

  /**
   * 设置懒加载
   */
  setupLazyLoading() {
    if (!this.supportedFeatures.intersectionObserver) {
      // 使用传统的滚动监听作为后备
      this.setupScrollBasedLazyLoading();
      return;
    }
    
    // 使用IntersectionObserver进行懒加载
    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const element = entry.target;
          
          // 处理图片懒加载
          if (element.tagName === 'IMG' && element.hasAttribute('data-src')) {
            element.src = element.getAttribute('data-src');
            element.removeAttribute('data-src');
            this.observer.unobserve(element);
          }
          
          // 处理其他元素的懒加载
          if (element.hasAttribute('data-lazy-load')) {
            const lazyLoadType = element.getAttribute('data-lazy-load');
            this.loadLazyElement(element, lazyLoadType);
          }
        }
      });
    }, {
      rootMargin: '200px',
      threshold: 0.01
    });
    
    // 观察所有需要懒加载的元素
    this.lazyLoadElements.forEach(element => this.observer.observe(element));
  }

  /**
   * 设置基于滚动的懒加载（作为后备方案）
   */
  setupScrollBasedLazyLoading() {
    // 初始检查
    this.checkLazyLoadElements();
  }

  /**
   * 检查懒加载元素
   */
  checkLazyLoadElements() {
    this.lazyLoadElements.forEach((element, index) => {
      if (this.isElementInViewport(element)) {
        // 加载元素
        if (element.tagName === 'IMG' && element.hasAttribute('data-src')) {
          element.src = element.getAttribute('data-src');
          element.removeAttribute('data-src');
          this.lazyLoadElements.splice(index, 1);
        }
      }
    });
    
    // 如果所有元素都加载完成，移除滚动监听
    if (this.lazyLoadElements.length === 0 && this.scrollHandler) {
      window.removeEventListener('scroll', this.scrollHandler);
    }
  }

  /**
   * 优化DOM
   */
  optimizeDom() {
    // 减少DOM深度
    this.reduceDomDepth();
    
    // 移除不必要的元素
    this.removeUnnecessaryElements();
    
    // 优化事件监听
    this.optimizeEventListeners();
  }

  /**
   * 减少DOM深度
   */
  reduceDomDepth() {
    // 这里可以添加逻辑来减少嵌套过深的DOM结构
    // 这是一个复杂的任务，需要根据具体页面结构进行优化
  }

  /**
   * 移除不必要的元素
   */
  removeUnnecessaryElements() {
    // 移除隐藏的元素
    const hiddenElements = document.querySelectorAll('body *[style*="display: none"], body *[hidden]');
    hiddenElements.forEach(element => {
      if (!element.hasAttribute('data-keep-hidden')) {
        element.remove();
      }
    });
  }

  /**
   * 优化事件监听
   */
  optimizeEventListeners() {
    // 对于大量相似元素，建议使用事件委托
    // 这里可以添加自动检测和优化的逻辑
  }

  /**
   * 优化CSS加载
   */
  optimizeCssLoading() {
    // 识别阻塞渲染的CSS
    const blockingCss = document.querySelectorAll('link[rel="stylesheet"]:not([media="print"])');
    
    blockingCss.forEach(link => {
      // 对于非关键CSS，可以使用media="print"并在加载后改为media="all"
      if (!link.hasAttribute('data-critical')) {
        const originalMedia = link.getAttribute('media') || 'all';
        link.setAttribute('media', 'print');
        link.onload = () => {
          link.setAttribute('media', originalMedia);
        };
      }
    });
  }

  /**
   * 优化JavaScript执行
   */
  optimizeJavaScriptExecution() {
    // 确保关键脚本优先执行
    this.prioritizeCriticalScripts();
    
    // 延迟非关键脚本
    this.deferNonCriticalScripts();
  }

  /**
   * 优先执行关键脚本
   */
  prioritizeCriticalScripts() {
    // 这里可以添加逻辑来确保关键脚本优先加载和执行
  }

  /**
   * 延迟非关键脚本
   */
  deferNonCriticalScripts() {
    const nonCriticalScripts = document.querySelectorAll('script:not([defer]):not([async]):not([data-critical])');
    
    nonCriticalScripts.forEach(script => {
      // 对于非内联脚本，可以添加defer属性
      if (script.src && !script.hasAttribute('defer') && !script.hasAttribute('async')) {
        script.setAttribute('defer', '');
      }
    });
  }

  /**
   * 处理页面加载完成事件
   */
  handlePageLoad() {
    this.performanceData.pageLoadTime = performance.now() - this.performanceData.startTime;
    console.log(`页面完全加载耗时: ${this.performanceData.pageLoadTime.toFixed(2)}ms`);
    
    // 页面加载完成后执行优化
    this.postLoadOptimizations();
  }

  /**
   * 处理DOMContentLoaded事件
   */
  handleDomContentLoaded() {
    this.performanceData.domInteractiveTime = performance.now() - this.performanceData.startTime;
    console.log(`DOM加载完成耗时: ${this.performanceData.domInteractiveTime.toFixed(2)}ms`);
    
    // DOM加载完成后执行优化
    this.domReadyOptimizations();
  }

  /**
   * 页面加载后的优化
   */
  postLoadOptimizations() {
    // 预加载下一个可能访问的页面资源
    this.predictAndPreloadNextPage();
    
    // 优化渲染性能
    this.optimizeRendering();
  }

  /**
   * DOM准备好后的优化
   */
  domReadyOptimizations() {
    // 初始化懒加载
    this.setupLazyLoading();
    
    // 优化初始渲染
    this.optimizeInitialRender();
  }

  /**
   * 预测并预加载下一个可能访问的页面资源
   */
  predictAndPreloadNextPage() {
    // 基于用户行为和导航模式预测下一个页面
    const nextPageLinks = this.identifyLikelyNextPages();
    
    nextPageLinks.forEach(link => {
      this.prefetchPage(link);
    });
  }

  /**
   * 识别可能的下一个页面
   * @returns {Array} 可能的下一个页面链接
   */
  identifyLikelyNextPages() {
    // 简单策略：预加载主要导航链接
    const mainNavLinks = Array.from(document.querySelectorAll('nav a, .main-navigation a')).slice(0, 3);
    return mainNavLinks.map(link => link.href);
  }

  /**
   * 预取页面
   * @param {String} pageUrl - 页面URL
   */
  prefetchPage(pageUrl) {
    if (!this.supportedFeatures.prefetch) return;
    
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = pageUrl;
    
    link.onload = () => {
      console.log(`页面预取完成: ${pageUrl}`);
    };
    
    link.onerror = () => {
      console.error(`页面预取失败: ${pageUrl}`);
    };
    
    document.head.appendChild(link);
  }

  /**
   * 优化渲染性能
   */
  optimizeRendering() {
    // 减少重绘和回流
    this.reduceRepaintsAndReflows();
    
    // 使用CSS硬件加速
    this.enableHardwareAcceleration();
  }

  /**
   * 减少重绘和回流
   */
  reduceRepaintsAndReflows() {
    // 这里可以添加逻辑来减少DOM操作导致的重绘和回流
  }

  /**
   * 启用CSS硬件加速
   */
  enableHardwareAcceleration() {
    // 为关键动画元素添加硬件加速
    const animatedElements = document.querySelectorAll('.animated, .transition, [data-animate]');
    animatedElements.forEach(element => {
      element.style.transform = element.style.transform || 'translateZ(0)';
      element.style.willChange = element.style.willChange || 'transform';
    });
  }

  /**
   * 优化初始渲染
   */
  optimizeInitialRender() {
    // 确保首屏内容优先渲染
    this.prioritizeAboveTheFoldContent();
  }

  /**
   * 优先渲染首屏内容
   */
  prioritizeAboveTheFoldContent() {
    // 识别首屏内容
    const aboveTheFoldElements = this.findAboveTheFoldElements();
    
    // 为这些元素添加优先渲染的标记
    aboveTheFoldElements.forEach(element => {
      element.setAttribute('data-above-fold', 'true');
    });
  }

  /**
   * 查找首屏元素
   * @returns {Array} 首屏元素列表
   */
  findAboveTheFoldElements() {
    const elements = [];
    const viewportHeight = window.innerHeight;
    
    // 简单策略：获取在视口内的元素
    document.querySelectorAll('section, div.content, header, footer').forEach(element => {
      const rect = element.getBoundingClientRect();
      if (rect.top < viewportHeight && rect.bottom > 0) {
        elements.push(element);
      }
    });
    
    return elements;
  }

  /**
   * 查找首屏图片
   * @returns {Array} 首屏图片列表
   */
  findAboveTheFoldImages() {
    const images = [];
    const viewportHeight = window.innerHeight;
    
    document.querySelectorAll('img').forEach(img => {
      const rect = img.getBoundingClientRect();
      if (rect.top < viewportHeight * 1.5 && rect.bottom > 0) {
        images.push(img);
      }
    });
    
    return images;
  }

  /**
   * 查找首屏外图片
   * @returns {Array} 首屏外图片列表
   */
  findBelowTheFoldImages() {
    const images = [];
    const viewportHeight = window.innerHeight;
    
    document.querySelectorAll('img').forEach(img => {
      const rect = img.getBoundingClientRect();
      if (rect.top > viewportHeight * 1.5) {
        images.push(img);
      }
    });
    
    return images;
  }

  /**
   * 检查元素是否在视口内
   * @param {HTMLElement} element - 要检查的元素
   * @returns {Boolean} 是否在视口内
   */
  isElementInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
      rect.top <= window.innerHeight + 200 &&
      rect.left <= window.innerWidth &&
      rect.bottom >= 0 &&
      rect.right >= 0
    );
  }

  /**
   * 加载懒加载元素
   * @param {HTMLElement} element - 要加载的元素
   * @param {String} loadType - 加载类型
   */
  loadLazyElement(element, loadType) {
    switch (loadType) {
      case 'component':
        // 延迟加载组件
        const componentId = element.getAttribute('data-component-id');
        if (componentId && this.componentManager) {
          this.componentManager.loadComponent('reusable', componentId);
        }
        break;
      
      case 'content':
        // 延迟加载内容
        const contentUrl = element.getAttribute('data-content-url');
        if (contentUrl) {
          this.loadLazyContent(element, contentUrl);
        }
        break;
    }
    
    element.removeAttribute('data-lazy-load');
  }

  /**
   * 加载懒加载内容
   * @param {HTMLElement} element - 目标元素
   * @param {String} url - 内容URL
   */
  async loadLazyContent(element, url) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        const content = await response.text();
        element.innerHTML = content;
        
        // 触发内容加载完成事件
        window.componentBus?.emit('lazy:content-loaded', {
          element,
          url
        });
      }
    } catch (error) {
      console.error(`加载懒加载内容失败: ${url}`, error);
    }
  }

  /**
   * 处理组件加载完成事件
   * @param {Object} eventData - 事件数据
   */
  handleComponentLoaded(eventData) {
    const { componentId, loadTime } = eventData;
    
    // 更新渲染时间统计
    this.performanceData.renderTime += loadTime || 0;
    
    // 对刚加载的组件进行优化
    this.optimizeComponent(componentId);
  }

  /**
   * 优化组件
   * @param {String} componentId - 组件ID
   */
  optimizeComponent(componentId) {
    const component = this.componentManager?.getComponent(componentId);
    if (!component || !component.element) return;
    
    // 优化组件的DOM
    this.optimizeComponentDom(component.element);
    
    // 为组件添加硬件加速（如果需要动画）
    if (component.hasAnimation) {
      this.enableHardwareAccelerationForElement(component.element);
    }
  }

  /**
   * 优化组件DOM
   * @param {HTMLElement} element - 组件根元素
   */
  optimizeComponentDom(element) {
    // 这里可以添加针对组件DOM的特定优化
  }

  /**
   * 为元素启用硬件加速
   * @param {HTMLElement} element - 目标元素
   */
  enableHardwareAccelerationForElement(element) {
    element.style.transform = element.style.transform || 'translateZ(0)';
    element.style.willChange = element.style.willChange || 'transform';
  }

  /**
   * 处理页面渲染完成事件
   */
  handlePageRendered() {
    this.performanceData.domCompleteTime = performance.now() - this.performanceData.startTime;
    console.log(`页面渲染完成耗时: ${this.performanceData.domCompleteTime.toFixed(2)}ms`);
    
    // 渲染完成后执行最终优化
    this.finalOptimizations();
  }

  /**
   * 执行最终优化
   */
  finalOptimizations() {
    // 清理未使用的资源
    this.cleanupUnusedResources();
    
    // 优化内存使用
    this.optimizeMemoryUsage();
  }

  /**
   * 清理未使用的资源
   */
  cleanupUnusedResources() {
    // 移除未使用的预加载资源
    // 清理未使用的事件监听器
  }

  /**
   * 优化内存使用
   */
  optimizeMemoryUsage() {
    // 释放不再需要的大型对象
    // 移除未使用的DOM引用
  }

  /**
   * 根据新的层级结构进行优化
   * @param {Object} hierarchyData - 层级数据
   */
  optimizeForNewHierarchy(hierarchyData) {
    const { renderOrder } = hierarchyData;
    
    // 根据新的渲染顺序优化资源加载
    this.prioritizeResourcesForRenderOrder(renderOrder);
  }

  /**
   * 根据渲染顺序优先加载资源
   * @param {Array} renderOrder - 渲染顺序
   */
  prioritizeResourcesForRenderOrder(renderOrder) {
    // 优先预加载渲染顺序靠前的组件的资源
    renderOrder.slice(0, 5).forEach(componentId => {
      const component = this.componentManager?.getComponent(componentId);
      if (component && component.resources) {
        component.resources.forEach(resource => {
          this.preloadResource(resource.url, resource.type);
        });
      }
    });
  }

  /**
   * 处理滚动事件
   */
  handleScroll() {
    // 触发懒加载检查
    this.checkLazyLoadElements();
    
    // 滚动时优化
    this.optimizeDuringScroll();
  }

  /**
   * 滚动时的优化
   */
  optimizeDuringScroll() {
    // 可以添加滚动时暂停动画等优化
  }

  /**
   * 处理调整大小事件
   */
  handleResize() {
    // 调整大小时重新检查懒加载元素
    this.checkLazyLoadElements();
  }

  /**
   * 收集性能数据
   */
  collectPerformanceData() {
    if (performance && performance.timing) {
      const timing = performance.timing;
      
      // 更新性能指标
      if (!this.performanceData.domInteractiveTime && timing.domInteractive) {
        this.performanceData.domInteractiveTime = timing.domInteractive - timing.navigationStart;
      }
      
      if (!this.performanceData.domCompleteTime && timing.domComplete) {
        this.performanceData.domCompleteTime = timing.domComplete - timing.navigationStart;
      }
    }
    
    // 可以将性能数据发送到服务器进行分析
    // this.reportPerformanceData();
  }

  /**
   * 报告性能数据
   */
  reportPerformanceData() {
    // 这里可以添加性能数据上报逻辑
    console.log('当前性能数据:', this.performanceData);
  }

  /**
   * 获取性能数据
   * @returns {Object} 性能数据
   */
  getPerformanceData() {
    return { ...this.performanceData };
  }

  /**
   * 启用优化
   */
  enable() {
    this.optimizationEnabled = true;
    console.log('页面优化已启用');
  }

  /**
   * 禁用优化
   */
  disable() {
    this.optimizationEnabled = false;
    console.log('页面优化已禁用');
  }

  /**
   * 销毁优化器
   */
  destroy() {
    // 移除事件监听
    window.removeEventListener('load', this.handlePageLoad);
    document.removeEventListener('DOMContentLoaded', this.handleDomContentLoaded);
    window.removeEventListener('scroll', this.handleScroll);
    window.removeEventListener('resize', this.handleResize);
    
    // 清理观察者
    if (this.observer) {
      this.observer.disconnect();
    }
    
    this.isInitialized = false;
    console.log('页面优化器已销毁');
  }
}

// 创建页面优化器实例
const pageOptimizer = new PageOptimizer();

// 导出
if (typeof window !== 'undefined') {
  window.PageOptimizer = PageOptimizer;
  window.pageOptimizer = pageOptimizer;
}

export { PageOptimizer, pageOptimizer };