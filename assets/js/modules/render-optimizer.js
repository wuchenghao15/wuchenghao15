// 渲染性能优化器 - 提升页面渲染效率和动画性能
class RenderOptimizer {
  constructor(options = {}) {
    // 优化配置
    this.config = {
      useVirtualDom: options.useVirtualDom !== false, // 是否使用虚拟DOM
      enableRequestAnimationFrame: options.enableRequestAnimationFrame !== false, // 是否使用requestAnimationFrame
      batchUpdateThreshold: options.batchUpdateThreshold || 16, // 批量更新阈值（毫秒）
      debounceThreshold: options.debounceThreshold || 100, // 防抖阈值（毫秒）
      throttleThreshold: options.throttleThreshold || 16, // 节流阈值（毫秒）
      enablePassiveEvents: options.enablePassiveEvents !== false, // 是否启用被动事件
      enableCompositing: options.enableCompositing !== false, // 是否启用合成层优化
      enableIntersectionObserver: options.enableIntersectionObserver !== false, // 是否启用Intersection Observer
      debug: options.debug || false, // 是否启用调试
      ...options
    };
    
    // 渲染队列
    this.renderQueue = [];
    
    // 更新队列
    this.updateQueue = [];
    
    // 动画帧ID
    this.animationFrameId = null;
    
    // 批量更新定时器
    this.batchUpdateTimer = null;
    
    // 节流和防抖函数映射
    this.throttledFunctions = new Map();
    this.debouncedFunctions = new Map();
    
    // 虚拟DOM实例
    this.virtualDom = null;
    
    // 合成层元素
    this.compositedElements = new Set();
    
    // 观察器映射
    this.observers = new Map();
    
    // 性能指标
    this.performanceMetrics = {
      renderCount: 0,
      updateCount: 0,
      skippedFrames: 0,
      averageRenderTime: 0,
      totalRenderTime: 0
    };
    
    // 初始化状态
    this.isInitialized = false;
  }

  /**
   * 初始化渲染优化器
   */
  initialize() {
    if (this.isInitialized) {
      console.warn('渲染优化器已经初始化');
      return this;
    }
    
    console.log('初始化渲染优化器...');
    
    // 设置环境兼容性
    this.setupCompatibility();
    
    // 启用性能优化特性
    this.enableOptimizationFeatures();
    
    // 初始化虚拟DOM（如果启用）
    if (this.config.useVirtualDom) {
      this.initializeVirtualDom();
    }
    
    // 启用事件优化
    if (this.config.enablePassiveEvents) {
      this.setupPassiveEvents();
    }
    
    // 启用合成层优化
    if (this.config.enableCompositing) {
      this.setupCompositingOptimizations();
    }
    
    // 设置渲染策略
    this.setupRenderStrategies();
    
    // 启用调试
    if (this.config.debug) {
      this.enableDebugging();
    }
    
    this.isInitialized = true;
    console.log('渲染优化器初始化完成');
    
    return this;
  }

  /**
   * 设置环境兼容性
   */
  setupCompatibility() {
    // 检查浏览器兼容性
    this.compatibility = {
      requestAnimationFrame: typeof window.requestAnimationFrame === 'function',
      requestIdleCallback: typeof window.requestIdleCallback === 'function',
      passiveEvents: this.supportsPassiveEvents(),
      intersectionObserver: typeof window.IntersectionObserver === 'function',
      mutationObserver: typeof window.MutationObserver === 'function'
    };
    
    // 降级处理
    if (!this.compatibility.requestAnimationFrame) {
      window.requestAnimationFrame = this.polyfillRequestAnimationFrame();
    }
    
    if (!this.compatibility.requestIdleCallback) {
      window.requestIdleCallback = this.polyfillRequestIdleCallback();
    }
  }

  /**
   * 检查是否支持被动事件
   */
  supportsPassiveEvents() {
    let supportsPassive = false;
    
    try {
      const opts = Object.defineProperty({}, 'passive', {
        get: () => {
          supportsPassive = true;
        }
      });
      
      window.addEventListener('test', null, opts);
      window.removeEventListener('test', null, opts);
    } catch (e) {
      // 不支持被动事件
    }
    
    return supportsPassive;
  }

  /**
   * 填充 requestAnimationFrame
   */
  polyfillRequestAnimationFrame() {
    let lastTime = 0;
    const vendors = ['webkit', 'moz', 'ms', 'o'];
    
    // 尝试使用 vendor-prefixed 版本
    for (let x = 0; x < vendors.length && !window.requestAnimationFrame; ++x) {
      window.requestAnimationFrame = window[vendors[x] + 'RequestAnimationFrame'];
      window.cancelAnimationFrame = window[vendors[x] + 'CancelAnimationFrame'] || 
        window[vendors[x] + 'CancelRequestAnimationFrame'];
    }
    
    if (!window.requestAnimationFrame) {
      window.requestAnimationFrame = (callback) => {
        const currTime = new Date().getTime();
        const timeToCall = Math.max(0, 16 - (currTime - lastTime));
        const id = window.setTimeout(() => callback(currTime + timeToCall), timeToCall);
        lastTime = currTime + timeToCall;
        return id;
      };
    }
    
    return window.requestAnimationFrame;
  }

  /**
   * 填充 requestIdleCallback
   */
  polyfillRequestIdleCallback() {
    return (callback, options) => {
      const opts = options || {};
      const timeout = opts.timeout || 3000;
      const start = Date.now();
      
      return window.setTimeout(() => {
        callback({
          didTimeout: false,
          timeRemaining: () => Math.max(0, 50 - (Date.now() - start))
        });
      }, 1);
    };
  }

  /**
   * 启用优化特性
   */
  enableOptimizationFeatures() {
    // 启用 CSS 性能优化
    this.enableCssOptimizations();
    
    // 启用内存管理优化
    this.enableMemoryOptimizations();
    
    // 启用渲染阻塞优化
    this.enableRenderBlockingOptimizations();
  }

  /**
   * 启用 CSS 优化
   */
  enableCssOptimizations() {
    // 这里可以添加 CSS 优化代码
    // 例如，优化选择器、合并样式等
  }

  /**
   * 启用内存管理优化
   */
  enableMemoryOptimizations() {
    // 监听页面卸载事件，清理资源
    window.addEventListener('beforeunload', () => {
      this.cleanupResources();
    });
  }

  /**
   * 启用渲染阻塞优化
   */
  enableRenderBlockingOptimizations() {
    // 异步加载非关键 CSS
    this.asyncLoadNonCriticalCss();
    
    // 延迟加载非关键 JavaScript
    this.deferNonCriticalJs();
  }

  /**
   * 异步加载非关键 CSS
   */
  asyncLoadNonCriticalCss() {
    // 查找带有 data-async-css 属性的链接
    const cssLinks = document.querySelectorAll('link[data-async-css]');
    
    cssLinks.forEach(link => {
      setTimeout(() => {
        const href = link.getAttribute('href');
        const newLink = document.createElement('link');
        
        newLink.rel = 'stylesheet';
        newLink.href = href;
        
        // 复制其他属性
        Array.from(link.attributes).forEach(attr => {
          if (attr.name !== 'data-async-css') {
            newLink.setAttribute(attr.name, attr.value);
          }
        });
        
        // 替换原链接
        link.parentNode.replaceChild(newLink, link);
      }, 0);
    });
  }

  /**
   * 延迟加载非关键 JavaScript
   */
  deferNonCriticalJs() {
    // 查找带有 data-defer-js 属性的脚本
    const scripts = document.querySelectorAll('script[data-defer-js]');
    
    scripts.forEach(script => {
      if ('requestIdleCallback' in window) {
        requestIdleCallback(() => {
          this.loadScriptAsync(script);
        });
      } else {
        setTimeout(() => {
          this.loadScriptAsync(script);
        }, 0);
      }
    });
  }

  /**
   * 异步加载脚本
   */
  loadScriptAsync(script) {
    const src = script.getAttribute('src');
    const newScript = document.createElement('script');
    
    newScript.src = src;
    newScript.async = true;
    
    // 复制其他属性
    Array.from(script.attributes).forEach(attr => {
      if (attr.name !== 'src' && attr.name !== 'data-defer-js') {
        newScript.setAttribute(attr.name, attr.value);
      }
    });
    
    // 替换原脚本
    script.parentNode.replaceChild(newScript, script);
  }

  /**
   * 初始化虚拟DOM
   */
  initializeVirtualDom() {
    // 简单的虚拟DOM实现
    this.virtualDom = {
      // 虚拟DOM树
      tree: null,
      
      // 创建虚拟节点
      createElement: (tag, props = {}, children = []) => ({
        tag,
        props,
        children
      }),
      
      // 渲染虚拟DOM
      render: (vnode, container) => {
        if (!vnode) return;
        
        // 保存虚拟DOM树
        this.virtualDom.tree = vnode;
        
        // 渲染到真实DOM
        this.renderVirtualNode(vnode, container);
      },
      
      // 更新虚拟DOM
      update: (newVnode, oldVnode = this.virtualDom.tree) => {
        if (!newVnode || !oldVnode) return;
        
        // 执行差异比较
        const patches = this.diff(oldVnode, newVnode);
        
        // 应用补丁
        this.applyPatches(document.body, patches);
        
        // 更新虚拟DOM树
        this.virtualDom.tree = newVnode;
      }
    };
  }

  /**
   * 渲染虚拟节点
   */
  renderVirtualNode(vnode, container) {
    // 如果是文本节点
    if (typeof vnode === 'string' || typeof vnode === 'number') {
      const textNode = document.createTextNode(vnode);
      container.appendChild(textNode);
      return textNode;
    }
    
    // 创建元素节点
    const element = document.createElement(vnode.tag);
    
    // 设置属性
    if (vnode.props) {
      Object.entries(vnode.props).forEach(([key, value]) => {
        this.setElementProp(element, key, value);
      });
    }
    
    // 渲染子节点
    if (vnode.children && Array.isArray(vnode.children)) {
      vnode.children.forEach(child => {
        this.renderVirtualNode(child, element);
      });
    }
    
    // 添加到容器
    container.appendChild(element);
    
    return element;
  }

  /**
   * 设置元素属性
   */
  setElementProp(element, key, value) {
    // 处理事件
    if (key.startsWith('on')) {
      const eventName = key.slice(2).toLowerCase();
      element.addEventListener(eventName, value);
      return;
    }
    
    // 处理样式
    if (key === 'style') {
      Object.entries(value).forEach(([prop, val]) => {
        element.style[prop] = val;
      });
      return;
    }
    
    // 其他属性
    element.setAttribute(key, value);
  }

  /**
   * 差异比较
   */
  diff(oldVnode, newVnode) {
    const patches = [];
    
    // 递归比较
    this.diffNodes(oldVnode, newVnode, patches);
    
    return patches;
  }

  /**
   * 比较节点
   */
  diffNodes(oldVnode, newVnode, patches, path = []) {
    // 节点类型不同
    if (typeof oldVnode !== typeof newVnode ||
        (typeof oldVnode !== 'string' && oldVnode.tag !== newVnode.tag)) {
      patches.push({
        path,
        type: 'REPLACE',
        node: newVnode
      });
      return;
    }
    
    // 文本节点
    if (typeof oldVnode === 'string' || typeof oldVnode === 'number') {
      if (oldVnode !== newVnode) {
        patches.push({
          path,
          type: 'TEXT',
          text: newVnode
        });
      }
      return;
    }
    
    // 比较属性
    this.diffProps(oldVnode.props, newVnode.props, patches, path);
    
    // 比较子节点
    this.diffChildren(oldVnode.children, newVnode.children, patches, path);
  }

  /**
   * 比较属性
   */
  diffProps(oldProps, newProps, patches, path) {
    const oldKeys = Object.keys(oldProps || {});
    const newKeys = Object.keys(newProps || {});
    
    // 移除旧属性
    oldKeys.forEach(key => {
      if (!(key in newProps)) {
        patches.push({
          path,
          type: 'REMOVE_PROP',
          key
        });
      }
    });
    
    // 添加或更新属性
    newKeys.forEach(key => {
      if (oldProps[key] !== newProps[key]) {
        patches.push({
          path,
          type: 'SET_PROP',
          key,
          value: newProps[key]
        });
      }
    });
  }

  /**
   * 比较子节点
   */
  diffChildren(oldChildren, newChildren, patches, path) {
    const maxLength = Math.max(
      oldChildren ? oldChildren.length : 0,
      newChildren ? newChildren.length : 0
    );
    
    // 简单的子节点比较算法
    for (let i = 0; i < maxLength; i++) {
      const oldChild = oldChildren ? oldChildren[i] : null;
      const newChild = newChildren ? newChildren[i] : null;
      const childPath = [...path, i];
      
      if (!oldChild && newChild) {
        // 添加新节点
        patches.push({
          path: path,
          type: 'APPEND_CHILD',
          child: newChild,
          index: i
        });
      } else if (oldChild && !newChild) {
        // 删除节点
        patches.push({
          path: childPath,
          type: 'REMOVE_CHILD'
        });
      } else if (oldChild && newChild) {
        // 递归比较
        this.diffNodes(oldChild, newChild, patches, childPath);
      }
    }
  }

  /**
   * 应用补丁
   */
  applyPatches(element, patches) {
    patches.forEach(patch => {
      const target = this.findNodeByPath(element, patch.path);
      
      if (!target) return;
      
      switch (patch.type) {
        case 'REPLACE':
          this.replaceNode(target, patch.node);
          break;
        case 'TEXT':
          this.updateTextNode(target, patch.text);
          break;
        case 'SET_PROP':
          this.setElementProp(target, patch.key, patch.value);
          break;
        case 'REMOVE_PROP':
          target.removeAttribute(patch.key);
          break;
        case 'APPEND_CHILD':
          this.appendChild(target, patch.child, patch.index);
          break;
        case 'REMOVE_CHILD':
          if (target.parentNode) {
            target.parentNode.removeChild(target);
          }
          break;
      }
    });
  }

  /**
   * 查找节点
   */
  findNodeByPath(element, path) {
    let current = element;
    
    path.forEach(index => {
      if (current && current.childNodes[index]) {
        current = current.childNodes[index];
      } else {
        current = null;
      }
    });
    
    return current;
  }

  /**
   * 替换节点
   */
  replaceNode(oldNode, newVnode) {
    const newNode = this.createNodeFromVnode(newVnode);
    oldNode.parentNode.replaceChild(newNode, oldNode);
  }

  /**
   * 创建节点
   */
  createNodeFromVnode(vnode) {
    if (typeof vnode === 'string' || typeof vnode === 'number') {
      return document.createTextNode(vnode);
    }
    
    const element = document.createElement(vnode.tag);
    
    if (vnode.props) {
      Object.entries(vnode.props).forEach(([key, value]) => {
        this.setElementProp(element, key, value);
      });
    }
    
    if (vnode.children) {
      vnode.children.forEach(child => {
        const childNode = this.createNodeFromVnode(child);
        element.appendChild(childNode);
      });
    }
    
    return element;
  }

  /**
   * 更新文本节点
   */
  updateTextNode(node, text) {
    node.nodeValue = text;
  }

  /**
   * 添加子节点
   */
  appendChild(parent, childVnode, index) {
    const childNode = this.createNodeFromVnode(childVnode);
    const children = parent.childNodes;
    
    if (index < children.length) {
      parent.insertBefore(childNode, children[index]);
    } else {
      parent.appendChild(childNode);
    }
  }

  /**
   * 设置被动事件
   */
  setupPassiveEvents() {
    // 优化滚动和触摸事件
    const events = ['scroll', 'touchstart', 'touchmove', 'wheel'];
    
    events.forEach(event => {
      this.optimizeEventListeners(event, { passive: true });
    });
  }

  /**
   * 优化事件监听器
   */
  optimizeEventListeners(eventName, options) {
    // 这里可以实现事件监听器的优化
    // 例如，使用事件委托或优化现有监听器
  }

  /**
   * 设置合成层优化
   */
  setupCompositingOptimizations() {
    // 查找需要提升到合成层的元素
    const elements = document.querySelectorAll('[data-composite-layer]');
    
    elements.forEach(element => {
      this.promoteToCompositingLayer(element);
    });
  }

  /**
   * 提升到合成层
   */
  promoteToCompositingLayer(element) {
    // 使用 CSS transform 属性提升到合成层
    const existingTransform = element.style.transform || '';
    const existingWillChange = element.style.willChange || '';
    
    // 应用 transform
    element.style.transform = existingTransform || 'translateZ(0)';
    
    // 应用 will-change
    element.style.willChange = existingWillChange || 'transform';
    
    // 添加到合成层集合
    this.compositedElements.add(element);
  }

  /**
   * 设置渲染策略
   */
  setupRenderStrategies() {
    // 启用批量更新
    this.enableBatchUpdates();
    
    // 启用渲染节流
    this.enableRenderThrottling();
  }

  /**
   * 启用批量更新
   */
  enableBatchUpdates() {
    // 替换原生方法以启用批量更新
    this.patchDomMethods();
  }

  /**
   * 修补 DOM 方法
   */
  patchDomMethods() {
    // 这里可以修补原生 DOM 方法以启用批量更新
    // 例如，重写 appendChild、removeChild 等方法
  }

  /**
   * 启用渲染节流
   */
  enableRenderThrottling() {
    // 这里可以实现渲染节流逻辑
  }

  /**
   * 渲染管理
   */
  scheduleRender(callback) {
    if (!this.config.enableRequestAnimationFrame) {
      callback();
      return;
    }
    
    this.renderQueue.push(callback);
    
    if (!this.animationFrameId) {
      this.animationFrameId = requestAnimationFrame(() => {
        this.processRenderQueue();
      });
    }
  }

  /**
   * 处理渲染队列
   */
  processRenderQueue() {
    const startTime = performance.now();
    
    // 处理渲染队列中的所有回调
    while (this.renderQueue.length > 0) {
      try {
        const callback = this.renderQueue.shift();
        callback();
      } catch (error) {
        console.error('渲染回调执行失败:', error);
      }
      
      // 检查是否超过时间限制
      if (performance.now() - startTime > this.config.batchUpdateThreshold) {
        // 剩余回调放到下一帧
        this.scheduleNextRender();
        break;
      }
    }
    
    // 更新性能指标
    this.updateRenderMetrics(performance.now() - startTime);
    
    // 重置动画帧ID
    this.animationFrameId = null;
  }

  /**
   * 安排下一帧渲染
   */
  scheduleNextRender() {
    if (!this.animationFrameId) {
      this.animationFrameId = requestAnimationFrame(() => {
        this.processRenderQueue();
      });
    }
  }

  /**
   * 批量更新
   */
  scheduleBatchUpdate(callback) {
    this.updateQueue.push(callback);
    
    if (!this.batchUpdateTimer) {
      this.batchUpdateTimer = setTimeout(() => {
        this.processUpdateQueue();
      }, this.config.batchUpdateThreshold);
    }
  }

  /**
   * 处理更新队列
   */
  processUpdateQueue() {
    // 执行批量更新
    this.updateQueue.forEach(callback => {
      try {
        callback();
      } catch (error) {
        console.error('更新回调执行失败:', error);
      }
    });
    
    // 清空队列
    this.updateQueue = [];
    this.batchUpdateTimer = null;
  }

  /**
   * 节流函数
   */
  throttle(fn, threshold = this.config.throttleThreshold) {
    const key = fn.toString();
    
    if (this.throttledFunctions.has(key)) {
      return this.throttledFunctions.get(key);
    }
    
    let lastCall = 0;
    const throttled = (...args) => {
      const now = Date.now();
      
      if (now - lastCall >= threshold) {
        lastCall = now;
        return fn.apply(this, args);
      }
    };
    
    this.throttledFunctions.set(key, throttled);
    return throttled;
  }

  /**
   * 防抖函数
   */
  debounce(fn, threshold = this.config.debounceThreshold) {
    const key = fn.toString();
    
    if (this.debouncedFunctions.has(key)) {
      return this.debouncedFunctions.get(key);
    }
    
    let timeout;
    const debounced = (...args) => {
      clearTimeout(timeout);
      
      timeout = setTimeout(() => {
        fn.apply(this, args);
      }, threshold);
    };
    
    this.debouncedFunctions.set(key, debounced);
    return debounced;
  }

  /**
   * 创建 Intersection Observer
   */
  createIntersectionObserver(options, callback) {
    if (!this.compatibility.intersectionObserver) {
      // 降级处理
      return this.createFallbackIntersectionObserver(options, callback);
    }
    
    const observer = new IntersectionObserver(callback, options);
    
    // 保存观察者
    const id = Symbol('observer');
    this.observers.set(id, observer);
    
    return {
      id,
      observe: (element) => observer.observe(element),
      unobserve: (element) => observer.unobserve(element),
      disconnect: () => {
        observer.disconnect();
        this.observers.delete(id);
      }
    };
  }

  /**
   * 创建降级版本的 Intersection Observer
   */
  createFallbackIntersectionObserver(options, callback) {
    // 使用滚动事件模拟 Intersection Observer
    const observer = {
      elements: new Set(),
      options: { ...options },
      callback,
      
      observe: function(element) {
        this.elements.add(element);
        this.startWatching();
      },
      
      unobserve: function(element) {
        this.elements.delete(element);
        if (this.elements.size === 0) {
          this.stopWatching();
        }
      },
      
      disconnect: function() {
        this.elements.clear();
        this.stopWatching();
      },
      
      startWatching: function() {
        if (!this.watching) {
          window.addEventListener('scroll', this.checkElements.bind(this), { passive: true });
          window.addEventListener('resize', this.checkElements.bind(this), { passive: true });
          this.watching = true;
          // 初始检查
          this.checkElements();
        }
      },
      
      stopWatching: function() {
        if (this.watching) {
          window.removeEventListener('scroll', this.checkElements.bind(this));
          window.removeEventListener('resize', this.checkElements.bind(this));
          this.watching = false;
        }
      },
      
      checkElements: function() {
        const entries = [];
        
        this.elements.forEach(element => {
          const rect = element.getBoundingClientRect();
          const isIntersecting = this.isElementVisible(element);
          
          entries.push({
            target: element,
            isIntersecting,
            intersectionRatio: isIntersecting ? 1 : 0,
            intersectionRect: rect,
            boundingClientRect: rect,
            rootBounds: this.getRootBounds()
          });
        });
        
        if (entries.length > 0) {
          this.callback(entries);
        }
      },
      
      isElementVisible: function(element) {
        const rect = element.getBoundingClientRect();
        return (
          rect.top < window.innerHeight &&
          rect.bottom > 0 &&
          rect.left < window.innerWidth &&
          rect.right > 0
        );
      },
      
      getRootBounds: function() {
        return {
          top: 0,
          left: 0,
          right: window.innerWidth,
          bottom: window.innerHeight
        };
      }
    };
    
    return observer;
  }

  /**
   * 性能监控
   */
  updateRenderMetrics(renderTime) {
    this.performanceMetrics.renderCount++;
    this.performanceMetrics.totalRenderTime += renderTime;
    this.performanceMetrics.averageRenderTime = 
      this.performanceMetrics.totalRenderTime / this.performanceMetrics.renderCount;
  }

  /**
   * 获取性能指标
   */
  getPerformanceMetrics() {
    return { ...this.performanceMetrics };
  }

  /**
   * 启用调试
   */
  enableDebugging() {
    console.log('启用渲染优化器调试模式');
    
    // 添加性能监控
    this.setupPerformanceMonitoring();
    
    // 添加渲染统计
    this.addRenderStats();
  }

  /**
   * 设置性能监控
   */
  setupPerformanceMonitoring() {
    // 监控渲染时间
    if ('performance' in window && 'mark' in window.performance) {
      // 可以添加性能标记和测量
    }
  }

  /**
   * 添加渲染统计
   */
  addRenderStats() {
    // 定期输出渲染统计
    setInterval(() => {
      console.log('渲染统计:', this.getPerformanceMetrics());
    }, 5000);
  }

  /**
   * 获取状态
   */
  getState() {
    return {
      initialized: this.isInitialized,
      renderQueueLength: this.renderQueue.length,
      updateQueueLength: this.updateQueue.length,
      compositedElementsCount: this.compositedElements.size,
      observersCount: this.observers.size,
      performance: this.getPerformanceMetrics(),
      compatibility: this.compatibility
    };
  }

  /**
   * 清理资源
   */
  cleanupResources() {
    // 取消动画帧
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
    
    // 清除定时器
    if (this.batchUpdateTimer) {
      clearTimeout(this.batchUpdateTimer);
    }
    
    // 断开所有观察者
    this.observers.forEach(observer => {
      if (observer.disconnect) {
        observer.disconnect();
      }
    });
    
    // 清空队列
    this.renderQueue = [];
    this.updateQueue = [];
    
    // 重置状态
    this.isInitialized = false;
    
    console.log('渲染优化器资源已清理');
  }

  /**
   * 销毁渲染优化器
   */
  destroy() {
    this.cleanupResources();
    console.log('渲染优化器已销毁');
  }
}

// 创建渲染优化器实例
const renderOptimizer = new RenderOptimizer({
  useVirtualDom: true,
  enableRequestAnimationFrame: true,
  batchUpdateThreshold: 16,
  debounceThreshold: 100,
  throttleThreshold: 16,
  enablePassiveEvents: true,
  enableCompositing: true,
  enableIntersectionObserver: true,
  debug: false
});

// 导出
if (typeof window !== 'undefined') {
  window.RenderOptimizer = RenderOptimizer;
  window.renderOptimizer = renderOptimizer;
}

export { RenderOptimizer, renderOptimizer };