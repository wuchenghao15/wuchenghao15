// 智能页面渲染引擎 - 重新设计的页面显示逻辑和父子组件层级关系管理
class IntelligentPageRenderer {
  constructor() {
    // 渲染状态
    this.isRendering = false;
    this.currentPageId = null;
    this.renderedComponents = new Map();
    this.componentInstances = new Map();
    
    // 渲染队列
    this.renderQueue = [];
    this.queuedComponents = new Set();
    
    // 生命周期钩子
    this.hooks = {
      beforePageRender: [],
      afterPageRender: [],
      beforeComponentRender: [],
      afterComponentRender: [],
      beforeComponentDestroy: [],
      afterComponentDestroy: [],
      onPageError: []
    };
    
    // 布局容器
    this.layoutContainers = {};
    
    // 响应式状态
    this.currentBreakpoint = null;
    this.lastWindowWidth = window.innerWidth;
    
    // 依赖注入
    this.dependencies = new Map();
    
    // 初始化状态
    this.isInitialized = false;
    
    // 性能监控
    this.performanceMetrics = {
      renderTimes: [],
      componentRenderTimes: new Map(),
      memoryUsage: []
    };
  }

  /**
   * 初始化渲染引擎
   */
  async initialize(dependencies = {}) {
    if (this.isInitialized) {
      console.warn('渲染引擎已经初始化');
      return true;
    }

    try {
      console.log('初始化智能页面渲染引擎...');
      
      // 注入依赖
      Object.entries(dependencies).forEach(([key, value]) => {
        this.dependencies.set(key, value);
      });
      
      // 验证必要依赖
      this.validateDependencies();
      
      // 初始化布局容器
      this.initializeLayoutContainers();
      
      // 设置响应式监听
      this.setupResponsiveListeners();
      
      // 触发初始响应式处理
      this.handleResponsiveChange();
      
      // 注册全局事件处理器
      this.registerGlobalEventHandlers();
      
      this.isInitialized = true;
      console.log('智能页面渲染引擎初始化完成');
      
      return true;
    } catch (error) {
      console.error('初始化智能页面渲染引擎失败:', error);
      this.triggerHook('onPageError', error);
      return false;
    }
  }

  /**
   * 验证依赖
   */
  validateDependencies() {
    const requiredDependencies = ['componentBus', 'hierarchyManager', 'componentConfigurator'];
    
    for (const dep of requiredDependencies) {
      if (!this.dependencies.has(dep)) {
        throw new Error(`缺少必要依赖: ${dep}`);
      }
    }
    
    // 检查依赖是否已初始化
    const hierarchyManager = this.dependencies.get('hierarchyManager');
    const componentConfigurator = this.dependencies.get('componentConfigurator');
    
    if (hierarchyManager && !hierarchyManager.isInitialized) {
      throw new Error('hierarchyManager 未初始化');
    }
    
    if (componentConfigurator && !componentConfigurator.isInitialized) {
      throw new Error('componentConfigurator 未初始化');
    }
  }

  /**
   * 初始化布局容器
   */
  initializeLayoutContainers() {
    // 标准布局容器
    const standardContainers = ['header', 'content', 'footer', 'sidebar', 'main', 'aside'];
    
    standardContainers.forEach(containerName => {
      const container = document.getElementById(containerName) || document.querySelector(`[data-container="${containerName}"]`);
      
      if (container) {
        this.layoutContainers[containerName] = container;
      }
    });
    
    // 自定义布局容器
    document.querySelectorAll('[data-layout-container]').forEach(element => {
      const containerName = element.getAttribute('data-layout-container');
      this.layoutContainers[containerName] = element;
    });
    
    console.log('布局容器初始化完成:', Object.keys(this.layoutContainers));
  }

  /**
   * 设置响应式监听
   */
  setupResponsiveListeners() {
    // 防抖处理
    let resizeTimer = null;
    
    const handleResize = () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        this.handleResponsiveChange();
      }, 100); // 100ms 防抖延迟
    };
    
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleResize);
    
    // 保存清理函数
    this.cleanupFunctions = [
      () => window.removeEventListener('resize', handleResize),
      () => window.removeEventListener('orientationchange', handleResize)
    ];
  }

  /**
   * 处理响应式变化
   */
  handleResponsiveChange() {
    const windowWidth = window.innerWidth;
    
    // 获取配置的断点
    const componentConfigurator = this.dependencies.get('componentConfigurator');
    let breakpoints = {
      xs: 0,
      sm: 576,
      md: 768,
      lg: 992,
      xl: 1200,
      xxl: 1400
    };
    
    // 如果配置器提供了断点，使用配置的断点
    if (componentConfigurator && this.currentPageId) {
      const pageConfig = componentConfigurator.getPageConfig(this.currentPageId);
      if (pageConfig && pageConfig.responsive && pageConfig.responsive.breakpoints) {
        breakpoints = { ...breakpoints, ...pageConfig.responsive.breakpoints };
      }
    }
    
    // 确定当前断点
    let newBreakpoint = 'xs';
    
    Object.entries(breakpoints)
      .sort(([, a], [, b]) => b - a) // 从大到小排序
      .forEach(([breakpoint, width]) => {
        if (windowWidth >= width) {
          newBreakpoint = breakpoint;
        }
      });
    
    // 如果断点变化了，更新组件显示
    if (newBreakpoint !== this.currentBreakpoint) {
      const oldBreakpoint = this.currentBreakpoint;
      this.currentBreakpoint = newBreakpoint;
      
      console.log(`响应式断点变化: ${oldBreakpoint} -> ${newBreakpoint} (${windowWidth}px)`);
      
      // 触发断点变化事件
      this.triggerBreakpointChange(oldBreakpoint, newBreakpoint);
      
      // 更新组件显示
      if (this.currentPageId) {
        this.updateComponentsForBreakpoint(newBreakpoint);
      }
    }
    
    this.lastWindowWidth = windowWidth;
  }

  /**
   * 触发断点变化
   */
  triggerBreakpointChange(oldBreakpoint, newBreakpoint) {
    const componentBus = this.dependencies.get('componentBus');
    
    if (componentBus) {
      componentBus.trigger('responsive.breakpointChange', {
        oldBreakpoint,
        newBreakpoint,
        width: window.innerWidth,
        height: window.innerHeight
      });
    }
  }

  /**
   * 为断点更新组件
   */
  updateComponentsForBreakpoint(breakpoint) {
    // 获取页面的响应式配置
    const componentConfigurator = this.dependencies.get('componentConfigurator');
    
    if (!componentConfigurator || !this.currentPageId) {
      return;
    }
    
    const pageConfig = componentConfigurator.getPageConfig(this.currentPageId);
    
    if (!pageConfig || !pageConfig.responsive || !pageConfig.responsive.layouts) {
      return;
    }
    
    // 获取当前断点的布局配置
    const breakpointLayout = pageConfig.responsive.layouts[breakpoint];
    
    if (!breakpointLayout) {
      return;
    }
    
    // 更新组件显示
    if (breakpointLayout.components) {
      Object.entries(breakpointLayout.components).forEach(([componentId, config]) => {
        const component = this.componentInstances.get(componentId);
        
        if (component) {
          // 更新组件配置
          this.updateComponent(componentId, config);
        }
      });
    }
    
    // 更新布局
    if (breakpointLayout.layout) {
      this.updateLayoutForBreakpoint(breakpointLayout.layout);
    }
  }

  /**
   * 更新断点布局
   */
  updateLayoutForBreakpoint(layoutConfig) {
    // 更新容器类和样式
    if (layoutConfig.containers) {
      Object.entries(layoutConfig.containers).forEach(([containerName, containerConfig]) => {
        const container = this.layoutContainers[containerName];
        
        if (container) {
          // 更新类
          if (containerConfig.classes) {
            // 移除旧的断点类
            const oldClasses = Array.from(container.classList).filter(cls => cls.startsWith('bp-'));
            oldClasses.forEach(cls => container.classList.remove(cls));
            
            // 添加新的断点类
            containerConfig.classes.forEach(cls => container.classList.add(cls));
          }
          
          // 更新样式
          if (containerConfig.styles) {
            Object.entries(containerConfig.styles).forEach(([prop, value]) => {
              container.style[prop] = value;
            });
          }
        }
      });
    }
  }

  /**
   * 注册全局事件处理器
   */
  registerGlobalEventHandlers() {
    const componentBus = this.dependencies.get('componentBus');
    
    if (!componentBus) {
      return;
    }
    
    // 注册组件事件监听
    componentBus.on('component.register', this.handleComponentRegister.bind(this));
    componentBus.on('component.unregister', this.handleComponentUnregister.bind(this));
    componentBus.on('component.update', this.handleComponentUpdate.bind(this));
    
    // 注册页面事件监听
    componentBus.on('page.load', this.handlePageLoad.bind(this));
    componentBus.on('page.unload', this.handlePageUnload.bind(this));
    componentBus.on('page.refresh', this.handlePageRefresh.bind(this));
  }

  /**
   * 处理组件注册
   */
  handleComponentRegister(event) {
    const { componentId, componentClass, options } = event;
    
    console.log(`组件注册: ${componentId}`);
    
    // 如果组件已注册，不做处理
    if (this.componentInstances.has(componentId)) {
      console.warn(`组件 ${componentId} 已经注册`);
      return;
    }
    
    try {
      // 创建组件实例
      const componentInstance = this.createComponentInstance(componentId, componentClass, options);
      
      // 保存组件实例
      this.componentInstances.set(componentId, componentInstance);
      
      // 如果当前正在渲染页面，将组件加入渲染队列
      if (this.isRendering && this.currentPageId) {
        this.queueComponentForRender(componentId);
      }
    } catch (error) {
      console.error(`组件 ${componentId} 注册失败:`, error);
      this.triggerHook('onPageError', error);
    }
  }

  /**
   * 处理组件注销
   */
  handleComponentUnregister(event) {
    const { componentId } = event;
    
    console.log(`组件注销: ${componentId}`);
    
    // 销毁组件
    this.destroyComponent(componentId);
  }

  /**
   * 处理组件更新
   */
  handleComponentUpdate(event) {
    const { componentId, updates } = event;
    
    console.log(`组件更新: ${componentId}`);
    
    // 更新组件
    this.updateComponent(componentId, updates);
  }

  /**
   * 处理页面加载
   */
  handlePageLoad(event) {
    const { pageId, options } = event;
    
    console.log(`页面加载: ${pageId}`);
    
    // 渲染页面
    this.renderPage(pageId, options);
  }

  /**
   * 处理页面卸载
   */
  handlePageUnload(event) {
    const { pageId } = event;
    
    console.log(`页面卸载: ${pageId}`);
    
    // 如果是当前页面，清理
    if (pageId === this.currentPageId) {
      this.cleanupPage();
    }
  }

  /**
   * 处理页面刷新
   */
  handlePageRefresh(event) {
    const { pageId } = event;
    
    console.log(`页面刷新: ${pageId}`);
    
    // 如果是当前页面，重新渲染
    if (pageId === this.currentPageId) {
      this.renderPage(pageId);
    }
  }

  /**
   * 渲染页面
   */
  async renderPage(pageId, options = {}) {
    if (this.isRendering) {
      console.warn('当前正在渲染中，请等待完成');
      return false;
    }

    try {
      const startTime = performance.now();
      this.isRendering = true;
      this.currentPageId = pageId;
      
      console.log(`开始渲染页面: ${pageId}`);
      
      // 触发页面渲染前钩子
      this.triggerHook('beforePageRender', { pageId, options });
      
      // 清理之前的页面
      this.cleanupPage();
      
      // 获取页面配置
      const pageConfig = this.getPageConfig(pageId);
      
      if (!pageConfig) {
        throw new Error(`页面配置不存在: ${pageId}`);
      }
      
      // 分析组件关系
      const relationshipAnalysis = await this.analyzeComponentRelationships(pageConfig);
      
      // 确定渲染顺序
      const renderOrder = this.determineRenderOrder(relationshipAnalysis);
      
      // 渲染组件
      await this.renderComponentsInOrder(renderOrder, pageConfig);
      
      // 应用页面布局
      this.applyPageLayout(pageConfig);
      
      // 触发页面渲染后钩子
      this.triggerHook('afterPageRender', { pageId, renderedComponents: this.renderedComponents.size });
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      // 记录性能指标
      this.recordRenderPerformance(renderTime);
      
      console.log(`页面渲染完成: ${pageId} (耗时: ${renderTime.toFixed(2)}ms, 组件: ${this.renderedComponents.size}个)`);
      
      return true;
    } catch (error) {
      console.error(`页面渲染失败: ${pageId}`, error);
      this.triggerHook('onPageError', error);
      return false;
    } finally {
      this.isRendering = false;
    }
  }

  /**
   * 获取页面配置
   */
  getPageConfig(pageId) {
    const componentConfigurator = this.dependencies.get('componentConfigurator');
    
    if (!componentConfigurator) {
      return null;
    }
    
    return componentConfigurator.getPageConfig(pageId);
  }

  /**
   * 分析组件关系
   */
  async analyzeComponentRelationships(pageConfig) {
    const hierarchyManager = this.dependencies.get('hierarchyManager');
    
    if (!hierarchyManager || !pageConfig.components) {
      return { components: [], relationships: [] };
    }
    
    // 准备组件数据
    const components = Object.entries(pageConfig.components).map(([componentId, config]) => ({
      id: componentId,
      ...config
    }));
    
    // 分析关系
    const analysis = await hierarchyManager.analyzeComponentRelationships(components, pageConfig.relationships || {});
    
    return analysis;
  }

  /**
   * 确定渲染顺序
   */
  determineRenderOrder(relationshipAnalysis) {
    // 获取智能层级规划器
    const hierarchyManager = this.dependencies.get('hierarchyManager');
    
    if (!hierarchyManager) {
      // 如果没有智能规划器，使用简单的层级排序
      return this.sortComponentsByLevel(relationshipAnalysis.components);
    }
    
    // 使用智能规划器优化渲染顺序
    const optimizedOrder = hierarchyManager.optimizeRenderOrder(relationshipAnalysis);
    
    return optimizedOrder;
  }

  /**
   * 按层级排序组件
   */
  sortComponentsByLevel(components) {
    // 先按层级排序，层级相同的按ID排序
    return [...components].sort((a, b) => {
      const levelA = a.level || 0;
      const levelB = b.level || 0;
      
      if (levelA !== levelB) {
        return levelA - levelB;
      }
      
      return a.id.localeCompare(b.id);
    });
  }

  /**
   * 按顺序渲染组件
   */
  async renderComponentsInOrder(renderOrder, pageConfig) {
    const renderPromises = renderOrder.map(async (componentInfo) => {
      const componentId = componentInfo.id;
      
      try {
        // 检查组件是否应该渲染
        if (!this.shouldRenderComponent(componentId, pageConfig)) {
          console.log(`组件跳过渲染: ${componentId}`);
          return false;
        }
        
        // 渲染组件
        await this.renderComponent(componentId, pageConfig.components[componentId]);
        
        return true;
      } catch (error) {
        console.error(`渲染组件失败: ${componentId}`, error);
        this.triggerHook('onPageError', error);
        return false;
      }
    });
    
    // 使用并发控制进行渲染
    const results = await this.concurrentRender(renderPromises, 3); // 最多3个并发渲染
    
    const successfulRenders = results.filter(result => result).length;
    console.log(`组件渲染完成: ${successfulRenders}/${renderOrder.length}个组件渲染成功`);
  }

  /**
   * 并发渲染控制
   */
  async concurrentRender(promises, concurrencyLimit) {
    const results = [];
    const executing = new Set();
    const queue = [...promises];
    
    while (queue.length > 0 || executing.size > 0) {
      // 执行队列中的promise，直到达到并发限制
      while (queue.length > 0 && executing.size < concurrencyLimit) {
        const promise = queue.shift();
        
        // 添加到执行集合
        executing.add(promise);
        
        try {
          const result = await promise;
          results.push(result);
        } catch (error) {
          results.push(false);
        } finally {
          // 从执行集合中移除
          executing.delete(promise);
        }
      }
      
      // 如果还有正在执行的promise，等待一下
      if (executing.size > 0) {
        await new Promise(resolve => setTimeout(resolve, 50));
      }
    }
    
    return results;
  }

  /**
   * 检查组件是否应该渲染
   */
  shouldRenderComponent(componentId, pageConfig) {
    const componentConfig = pageConfig.components[componentId];
    
    if (!componentConfig) {
      return false;
    }
    
    // 检查可见性
    if (componentConfig.visible === false) {
      return false;
    }
    
    // 检查条件
    if (componentConfig.conditions && componentConfig.conditions.length > 0) {
      const allConditionsMet = componentConfig.conditions.every(condition => {
        return this.evaluateCondition(condition);
      });
      
      if (!allConditionsMet) {
        return false;
      }
    }
    
    // 检查权限
    if (componentConfig.permissions && componentConfig.permissions.length > 0) {
      // 这里可以添加权限检查逻辑
      // 暂时返回true，实际应用中需要实现权限验证
    }
    
    return true;
  }

  /**
   * 评估条件
   */
  evaluateCondition(condition) {
    try {
      // 支持不同类型的条件
      if (typeof condition === 'function') {
        return condition();
      } else if (typeof condition === 'object') {
        // 条件对象格式: { type: 'visibility', value: true }
        switch (condition.type) {
          case 'visibility':
            return condition.value !== false;
          case 'responsive':
            // 响应式条件: { type: 'responsive', breakpoints: ['md', 'lg'] }
            if (condition.breakpoints && Array.isArray(condition.breakpoints)) {
              return condition.breakpoints.includes(this.currentBreakpoint);
            }
            return true;
          case 'user':
            // 用户相关条件，这里简化处理
            return true;
          default:
            return true;
        }
      }
      
      return Boolean(condition);
    } catch (error) {
      console.error('条件评估失败:', error);
      return false;
    }
  }

  /**
   * 渲染组件
   */
  async renderComponent(componentId, componentConfig) {
    // 触发组件渲染前钩子
    this.triggerHook('beforeComponentRender', { componentId, componentConfig });
    
    // 开始性能计时
    const startTime = performance.now();
    
    try {
      // 获取组件实例
      let component = this.componentInstances.get(componentId);
      
      // 如果没有实例，创建一个
      if (!component) {
        component = await this.createComponent(componentId, componentConfig);
      }
      
      if (!component) {
        throw new Error(`无法创建或获取组件实例: ${componentId}`);
      }
      
      // 获取容器
      const container = this.getComponentContainer(componentConfig);
      
      if (!container) {
        console.warn(`组件容器不存在: ${componentConfig.region || 'unknown'}`);
        return;
      }
      
      // 准备渲染数据
      const renderData = this.prepareRenderData(componentId, componentConfig);
      
      // 渲染组件
      await component.render(container, renderData);
      
      // 记录渲染状态
      this.renderedComponents.set(componentId, {
        component,
        config: { ...componentConfig },
        container,
        renderTime: performance.now() - startTime,
        renderedAt: Date.now()
      });
      
      // 触发组件渲染后钩子
      this.triggerHook('afterComponentRender', { componentId, component, container });
      
      // 记录性能指标
      this.recordComponentRenderPerformance(componentId, performance.now() - startTime);
      
      console.log(`组件渲染成功: ${componentId} (耗时: ${(performance.now() - startTime).toFixed(2)}ms)`);
      
      // 渲染子组件
      await this.renderChildComponents(componentId, componentConfig);
    } catch (error) {
      console.error(`渲染组件失败: ${componentId}`, error);
      this.triggerHook('onPageError', error);
      throw error;
    }
  }

  /**
   * 创建组件
   */
  async createComponent(componentId, componentConfig) {
    const componentType = componentConfig.type || 'generic';
    
    // 获取组件类
    const componentClass = this.getComponentClass(componentType);
    
    if (!componentClass) {
      console.warn(`未知的组件类型: ${componentType}`);
      // 使用通用组件类作为后备
      return this.createGenericComponent(componentId, componentConfig);
    }
    
    try {
      // 创建组件实例
      const component = this.createComponentInstance(componentId, componentClass, componentConfig);
      
      // 保存实例
      this.componentInstances.set(componentId, component);
      
      return component;
    } catch (error) {
      console.error(`创建组件失败: ${componentId}`, error);
      return null;
    }
  }

  /**
   * 获取组件类
   */
  getComponentClass(componentType) {
    // 从全局注册表获取
    if (window && window.ComponentRegistry) {
      return window.ComponentRegistry.getComponent(componentType);
    }
    
    // 尝试动态导入（如果支持）
    // 这里简化处理，实际应用中可以实现动态导入
    
    return null;
  }

  /**
   * 创建组件实例
   */
  createComponentInstance(componentId, componentClass, options = {}) {
    // 创建实例
    const instance = new componentClass(componentId, options);
    
    // 注入依赖
    if (instance.injectDependencies) {
      instance.injectDependencies(this.dependencies);
    }
    
    // 设置组件引用
    instance.renderer = this;
    
    return instance;
  }

  /**
   * 创建通用组件
   */
  createGenericComponent(componentId, componentConfig) {
    // 创建一个简单的通用组件
    const genericComponent = {
      id: componentId,
      config: componentConfig,
      
      async render(container, data) {
        const element = document.createElement('div');
        element.className = `generic-component ${componentId}`;
        element.setAttribute('data-component-id', componentId);
        
        // 基本内容
        element.innerHTML = `
          <div class="component-header">
            <h3>${componentId}</h3>
            <small>${componentConfig.type || 'generic'}</small>
          </div>
          <div class="component-content">
            <p>通用组件渲染占位</p>
            ${componentConfig.html || ''}
          </div>
        `;
        
        // 添加样式
        if (componentConfig.styles) {
          const style = document.createElement('style');
          style.textContent = componentConfig.styles;
          element.appendChild(style);
        }
        
        // 清空容器并添加元素
        container.appendChild(element);
      },
      
      update(updates) {
        // 更新配置
        this.config = { ...this.config, ...updates };
        
        // 重新渲染
        const element = document.querySelector(`[data-component-id="${componentId}"]`);
        if (element && element.parentNode) {
          this.render(element.parentNode, this.config);
        }
      },
      
      destroy() {
        // 清理资源
        const element = document.querySelector(`[data-component-id="${componentId}"]`);
        if (element && element.parentNode) {
          element.parentNode.removeChild(element);
        }
      }
    };
    
    return genericComponent;
  }

  /**
   * 获取组件容器
   */
  getComponentContainer(componentConfig) {
    const region = componentConfig.region || 'content';
    
    // 首先检查配置的容器
    if (componentConfig.containerId) {
      const container = document.getElementById(componentConfig.containerId);
      if (container) {
        return container;
      }
    }
    
    // 使用布局容器
    if (this.layoutContainers[region]) {
      return this.layoutContainers[region];
    }
    
    // 查找默认容器
    const defaultContainer = document.getElementById('content') || document.body;
    
    return defaultContainer;
  }

  /**
   * 准备渲染数据
   */
  prepareRenderData(componentId, componentConfig) {
    return {
      componentId,
      componentConfig,
      pageId: this.currentPageId,
      breakpoint: this.currentBreakpoint,
      dependencies: {}, // 可以添加组件依赖的数据
      parentData: {}, // 父组件传递的数据
      // 其他渲染相关数据
    };
  }

  /**
   * 渲染子组件
   */
  async renderChildComponents(componentId, componentConfig) {
    if (!componentConfig.children || componentConfig.children.length === 0) {
      return;
    }
    
    // 渲染所有子组件
    for (const childComponentId of componentConfig.children) {
      // 查找子组件配置
      const pageConfig = this.getPageConfig(this.currentPageId);
      const childConfig = pageConfig && pageConfig.components ? pageConfig.components[childComponentId] : null;
      
      if (childConfig) {
        try {
          await this.renderComponent(childComponentId, childConfig);
        } catch (error) {
          console.error(`渲染子组件失败: ${childComponentId}`, error);
        }
      }
    }
  }

  /**
   * 应用页面布局
   */
  applyPageLayout(pageConfig) {
    if (!pageConfig.layout) {
      return;
    }
    
    const layout = pageConfig.layout;
    
    // 应用布局类
    if (layout.type) {
      document.body.setAttribute('data-layout-type', layout.type);
    }
    
    // 显示/隐藏区域
    if (layout.regions) {
      // 隐藏所有未配置的区域
      Object.keys(this.layoutContainers).forEach(region => {
        if (!layout.regions.includes(region)) {
          this.layoutContainers[region].style.display = 'none';
        } else {
          this.layoutContainers[region].style.display = '';
        }
      });
    }
    
    // 应用自定义布局样式
    if (layout.styles) {
      // 创建或更新布局样式
      let styleElement = document.getElementById('layout-styles');
      
      if (!styleElement) {
        styleElement = document.createElement('style');
        styleElement.id = 'layout-styles';
        document.head.appendChild(styleElement);
      }
      
      styleElement.textContent = layout.styles;
    }
  }

  /**
   * 更新组件
   */
  async updateComponent(componentId, updates) {
    const renderedComponent = this.renderedComponents.get(componentId);
    const component = this.componentInstances.get(componentId);
    
    if (!renderedComponent || !component) {
      console.warn(`组件不存在或未渲染: ${componentId}`);
      return false;
    }
    
    try {
      // 更新配置
      const updatedConfig = { ...renderedComponent.config, ...updates };
      
      // 验证更新后的配置
      if (!this.validateComponentConfig(updatedConfig)) {
        throw new Error('组件配置验证失败');
      }
      
      // 检查组件是否应该继续渲染
      if (!this.shouldRenderComponent(componentId, { components: { [componentId]: updatedConfig } })) {
        // 如果不应该渲染，销毁组件
        this.destroyComponent(componentId);
        return true;
      }
      
      // 更新组件
      if (component.update) {
        await component.update(updatedConfig);
      } else {
        // 如果没有update方法，重新渲染
        await this.renderComponent(componentId, updatedConfig);
      }
      
      // 更新渲染记录
      renderedComponent.config = updatedConfig;
      
      console.log(`组件更新成功: ${componentId}`);
      
      return true;
    } catch (error) {
      console.error(`更新组件失败: ${componentId}`, error);
      this.triggerHook('onPageError', error);
      return false;
    }
  }

  /**
   * 验证组件配置
   */
  validateComponentConfig(config) {
    // 基本验证逻辑
    if (!config || !config.id) {
      return false;
    }
    
    return true;
  }

  /**
   * 销毁组件
   */
  destroyComponent(componentId) {
    // 触发组件销毁前钩子
    this.triggerHook('beforeComponentDestroy', { componentId });
    
    try {
      const component = this.componentInstances.get(componentId);
      const renderedComponent = this.renderedComponents.get(componentId);
      
      // 调用组件的销毁方法
      if (component && component.destroy) {
        component.destroy();
      }
      
      // 清理渲染记录
      this.renderedComponents.delete(componentId);
      this.componentInstances.delete(componentId);
      
      // 清理队列中的组件
      this.queuedComponents.delete(componentId);
      this.renderQueue = this.renderQueue.filter(id => id !== componentId);
      
      // 触发组件销毁后钩子
      this.triggerHook('afterComponentDestroy', { componentId });
      
      console.log(`组件销毁成功: ${componentId}`);
      
      return true;
    } catch (error) {
      console.error(`销毁组件失败: ${componentId}`, error);
      return false;
    }
  }

  /**
   * 将组件加入渲染队列
   */
  queueComponentForRender(componentId) {
    if (this.queuedComponents.has(componentId)) {
      return;
    }
    
    this.renderQueue.push(componentId);
    this.queuedComponents.add(componentId);
    
    // 触发队列处理
    this.processRenderQueue();
  }

  /**
   * 处理渲染队列
   */
  async processRenderQueue() {
    if (this.isProcessingQueue) {
      return;
    }
    
    this.isProcessingQueue = true;
    
    try {
      while (this.renderQueue.length > 0) {
        const componentId = this.renderQueue.shift();
        this.queuedComponents.delete(componentId);
        
        // 获取组件配置
        const pageConfig = this.getPageConfig(this.currentPageId);
        const componentConfig = pageConfig && pageConfig.components ? pageConfig.components[componentId] : null;
        
        if (componentConfig) {
          try {
            await this.renderComponent(componentId, componentConfig);
          } catch (error) {
            console.error(`渲染队列中的组件失败: ${componentId}`, error);
          }
        }
      }
    } finally {
      this.isProcessingQueue = false;
    }
  }

  /**
   * 清理页面
   */
  cleanupPage() {
    // 销毁所有渲染的组件
    const componentIds = Array.from(this.renderedComponents.keys());
    
    componentIds.forEach(componentId => {
      this.destroyComponent(componentId);
    });
    
    // 清空渲染状态
    this.renderedComponents.clear();
    this.renderQueue = [];
    this.queuedComponents.clear();
    
    // 清理布局样式
    const styleElement = document.getElementById('layout-styles');
    if (styleElement) {
      styleElement.remove();
    }
  }

  /**
   * 触发钩子
   */
  triggerHook(hookName, data) {
    if (!this.hooks[hookName]) {
      return;
    }
    
    this.hooks[hookName].forEach(hook => {
      try {
        hook(data);
      } catch (error) {
        console.error(`钩子执行失败: ${hookName}`, error);
      }
    });
  }

  /**
   * 注册钩子
   */
  on(hookName, callback) {
    if (!this.hooks[hookName]) {
      console.warn(`未知的钩子: ${hookName}`);
      return false;
    }
    
    this.hooks[hookName].push(callback);
    return true;
  }

  /**
   * 取消注册钩子
   */
  off(hookName, callback) {
    if (!this.hooks[hookName]) {
      return false;
    }
    
    this.hooks[hookName] = this.hooks[hookName].filter(hook => hook !== callback);
    return true;
  }

  /**
   * 记录渲染性能
   */
  recordRenderPerformance(renderTime) {
    this.performanceMetrics.renderTimes.push({
      pageId: this.currentPageId,
      time: renderTime,
      timestamp: Date.now()
    });
    
    // 限制记录数量
    if (this.performanceMetrics.renderTimes.length > 100) {
      this.performanceMetrics.renderTimes.shift();
    }
  }

  /**
   * 记录组件渲染性能
   */
  recordComponentRenderPerformance(componentId, renderTime) {
    if (!this.performanceMetrics.componentRenderTimes.has(componentId)) {
      this.performanceMetrics.componentRenderTimes.set(componentId, []);
    }
    
    const times = this.performanceMetrics.componentRenderTimes.get(componentId);
    times.push({
      time: renderTime,
      timestamp: Date.now()
    });
    
    // 限制记录数量
    if (times.length > 50) {
      times.shift();
    }
  }

  /**
   * 获取性能指标
   */
  getPerformanceMetrics() {
    return { ...this.performanceMetrics };
  }

  /**
   * 重置性能指标
   */
  resetPerformanceMetrics() {
    this.performanceMetrics = {
      renderTimes: [],
      componentRenderTimes: new Map(),
      memoryUsage: []
    };
  }

  /**
   * 获取渲染状态
   */
  getRenderStatus() {
    return {
      isRendering: this.isRendering,
      currentPageId: this.currentPageId,
      renderedComponentsCount: this.renderedComponents.size,
      queuedComponentsCount: this.renderQueue.length,
      currentBreakpoint: this.currentBreakpoint,
      windowDimensions: {
        width: window.innerWidth,
        height: window.innerHeight
      }
    };
  }

  /**
   * 销毁渲染引擎
   */
  destroy() {
    // 清理页面
    this.cleanupPage();
    
    // 执行清理函数
    if (this.cleanupFunctions) {
      this.cleanupFunctions.forEach(cleanup => {
        try {
          cleanup();
        } catch (error) {
          console.error('清理函数执行失败:', error);
        }
      });
    }
    
    // 清空所有数据
    this.dependencies.clear();
    this.hooks = {
      beforePageRender: [],
      afterPageRender: [],
      beforeComponentRender: [],
      afterComponentRender: [],
      beforeComponentDestroy: [],
      afterComponentDestroy: [],
      onPageError: []
    };
    
    this.isInitialized = false;
    this.currentPageId = null;
    
    console.log('智能页面渲染引擎已销毁');
  }
}

// 创建智能页面渲染引擎实例
const intelligentRenderer = new IntelligentPageRenderer();

// 导出
if (typeof window !== 'undefined') {
  window.IntelligentPageRenderer = IntelligentPageRenderer;
  window.intelligentRenderer = intelligentRenderer;
}

export { IntelligentPageRenderer, intelligentRenderer };