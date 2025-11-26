// 智能规划整合器 - 整合所有智能优化模块，提供统一的优化入口和管理
class IntelligentPlannerIntegrator {
  constructor() {
    // 模块实例引用
    this.componentBus = null;
    this.componentManager = null;
    this.layoutManager = null;
    this.hierarchyPlanner = null;
    this.pageOptimizer = null;
    
    // 配置
    this.config = {
      enableIntelligentPlanning: true,
      enablePerformanceOptimization: true,
      enableDynamicLoading: true,
      enableAdaptiveLayout: true,
      optimizationLevel: 'balanced' // 'aggressive', 'balanced', 'conservative'
    };
    
    this.isInitialized = false;
    this.modulesLoaded = {};
    
    // 初始化整合器
    this.initialize();
  }

  /**
   * 初始化整合器
   */
  async initialize() {
    if (this.isInitialized) return;
    
    console.log('开始初始化智能规划整合器...');
    
    // 按顺序加载并初始化各个模块
    await this.loadCoreModules();
    await this.initializeModules();
    
    // 设置模块间的关联
    this.setupModuleConnections();
    
    // 注册事件监听
    this.setupGlobalEventListeners();
    
    // 应用初始配置
    this.applyConfig(this.config);
    
    this.isInitialized = true;
    console.log('智能规划整合器初始化完成');
    
    // 触发初始化完成事件
    this.emit('intelligent-planner:initialized', {
      modules: this.modulesLoaded
    });
  }

  /**
   * 加载核心模块
   */
  async loadCoreModules() {
    console.log('加载核心模块...');
    
    try {
      // 优先加载组件总线，因为它是基础通信层
      if (window.componentBus) {
        this.componentBus = window.componentBus;
        this.modulesLoaded.componentBus = true;
        console.log('组件总线已加载');
      }
      
      // 加载组件管理器
      if (window.componentManager) {
        this.componentManager = window.componentManager;
        this.modulesLoaded.componentManager = true;
        console.log('组件管理器已加载');
      }
      
      // 加载布局管理器
      if (window.layoutManager) {
        this.layoutManager = window.layoutManager;
        this.modulesLoaded.layoutManager = true;
        console.log('布局管理器已加载');
      }
      
      // 加载智能层级规划器
      if (window.intelligentHierarchyPlanner) {
        this.hierarchyPlanner = window.intelligentHierarchyPlanner;
        this.modulesLoaded.hierarchyPlanner = true;
        console.log('智能层级规划器已加载');
      }
      
      // 加载页面优化器
      if (window.pageOptimizer) {
        this.pageOptimizer = window.pageOptimizer;
        this.modulesLoaded.pageOptimizer = true;
        console.log('页面优化器已加载');
      }
    } catch (error) {
      console.error('加载核心模块失败:', error);
    }
  }

  /**
   * 初始化各个模块
   */
  async initializeModules() {
    console.log('初始化各个模块...');
    
    try {
      // 确保组件总线已初始化
      if (this.componentBus && !this.componentBus.isInitialized) {
        this.componentBus.initialize();
      }
      
      // 确保布局管理器已初始化
      if (this.layoutManager && !this.layoutManager.isInitialized) {
        this.layoutManager.initialize();
      }
      
      // 确保智能层级规划器已初始化
      if (this.hierarchyPlanner && !this.hierarchyPlanner.isInitialized) {
        this.hierarchyPlanner.initialize();
      }
      
      // 确保页面优化器已初始化
      if (this.pageOptimizer && !this.pageOptimizer.isInitialized) {
        this.pageOptimizer.initialize();
      }
    } catch (error) {
      console.error('初始化模块失败:', error);
    }
  }

  /**
   * 设置模块间的关联
   */
  setupModuleConnections() {
    console.log('设置模块间关联...');
    
    // 为智能层级规划器关联组件管理器和布局管理器
    if (this.hierarchyPlanner) {
      if (this.componentManager) {
        this.hierarchyPlanner.componentManager = this.componentManager;
      }
      if (this.layoutManager) {
        this.hierarchyPlanner.layoutManager = this.layoutManager;
      }
    }
    
    // 为页面优化器关联组件管理器和层级规划器
    if (this.pageOptimizer) {
      if (this.componentManager) {
        this.pageOptimizer.componentManager = this.componentManager;
      }
      if (this.hierarchyPlanner) {
        this.pageOptimizer.hierarchyPlanner = this.hierarchyPlanner;
      }
    }
    
    // 为组件管理器关联智能层级规划器
    if (this.componentManager) {
      this.componentManager.intelligentPlanner = this.hierarchyPlanner;
    }
  }

  /**
   * 设置全局事件监听器
   */
  setupGlobalEventListeners() {
    // 监听页面加载完成事件
    window.addEventListener('load', this.handleWindowLoad.bind(this));
    
    // 监听文档加载完成事件
    document.addEventListener('DOMContentLoaded', this.handleDomContentLoaded.bind(this));
    
    // 使用组件总线监听关键事件
    if (this.componentBus) {
      // 监听页面渲染前事件
      this.componentBus.on('page:beforerender', this.prepareForPageRender.bind(this));
      
      // 监听页面渲染完成事件
      this.componentBus.on('page:rendered', this.afterPageRender.bind(this));
      
      // 监听布局变化事件
      this.componentBus.on('layout:changed', this.handleLayoutChange.bind(this));
      
      // 监听断点变化事件
      this.componentBus.on('breakpoint:change', this.handleBreakpointChange.bind(this));
    }
  }

  /**
   * 应用配置
   * @param {Object} config - 配置对象
   */
  applyConfig(config) {
    console.log('应用配置:', config);
    
    // 更新配置
    this.config = { ...this.config, ...config };
    
    // 根据配置启用或禁用功能
    if (this.hierarchyPlanner) {
      this.hierarchyPlanner.optimizationEnabled = this.config.enableIntelligentPlanning;
    }
    
    if (this.pageOptimizer) {
      this.pageOptimizer.optimizationEnabled = this.config.enablePerformanceOptimization;
    }
    
    // 根据优化级别调整设置
    this.adjustSettingsForOptimizationLevel();
  }

  /**
   * 根据优化级别调整设置
   */
  adjustSettingsForOptimizationLevel() {
    const level = this.config.optimizationLevel;
    
    switch (level) {
      case 'aggressive':
        // 激进模式：最大程度优化性能
        this.applyAggressiveOptimizations();
        break;
      case 'balanced':
        // 平衡模式：在性能和兼容性之间取得平衡
        this.applyBalancedOptimizations();
        break;
      case 'conservative':
        // 保守模式：优先考虑兼容性和稳定性
        this.applyConservativeOptimizations();
        break;
    }
  }

  /**
   * 应用激进优化
   */
  applyAggressiveOptimizations() {
    // 启用所有优化功能
    this.config.enableDynamicLoading = true;
    this.config.enableAdaptiveLayout = true;
    
    // 配置页面优化器
    if (this.pageOptimizer) {
      // 启用所有性能优化选项
      this.pageOptimizer.enable();
    }
    
    // 配置层级规划器
    if (this.hierarchyPlanner) {
      // 使用更激进的优化策略
    }
  }

  /**
   * 应用平衡优化
   */
  applyBalancedOptimizations() {
    // 平衡的优化设置
    this.config.enableDynamicLoading = true;
    this.config.enableAdaptiveLayout = true;
    
    // 适度配置各个优化器
  }

  /**
   * 应用保守优化
   */
  applyConservativeOptimizations() {
    // 保守的优化设置，优先考虑兼容性
    this.config.enableDynamicLoading = false;
    this.config.enableAdaptiveLayout = true;
    
    // 禁用可能引起兼容性问题的优化
  }

  /**
   * 处理窗口加载完成事件
   */
  handleWindowLoad() {
    console.log('窗口加载完成，执行全局优化...');
    
    // 执行全局优化
    this.performGlobalOptimizations();
  }

  /**
   * 处理DOM加载完成事件
   */
  handleDomContentLoaded() {
    console.log('DOM加载完成，准备智能规划...');
    
    // 如果启用了智能规划，执行初始规划
    if (this.config.enableIntelligentPlanning && this.hierarchyPlanner) {
      this.hierarchyPlanner.planHierarchy();
    }
    
    // 如果启用了性能优化，执行页面优化
    if (this.config.enablePerformanceOptimization && this.pageOptimizer) {
      this.pageOptimizer.optimizePageLoad();
    }
  }

  /**
   * 准备页面渲染
   */
  prepareForPageRender() {
    console.log('准备页面渲染，优化渲染顺序...');
    
    // 获取优化后的渲染顺序
    let optimizedOrder = [];
    
    if (this.hierarchyPlanner) {
      optimizedOrder = this.hierarchyPlanner.getRenderOrder();
    }
    
    // 如果有优化后的渲染顺序，应用到组件管理器
    if (optimizedOrder.length > 0 && this.componentManager) {
      // 通知组件管理器使用优化后的渲染顺序
      this.emit('render:order-optimized', {
        renderOrder: optimizedOrder
      });
    }
  }

  /**
   * 页面渲染完成后处理
   */
  afterPageRender() {
    console.log('页面渲染完成，执行后续优化...');
    
    // 执行渲染后的优化
    this.performPostRenderOptimizations();
    
    // 收集并报告优化效果
    this.reportOptimizationResults();
  }

  /**
   * 处理布局变化
   */
  handleLayoutChange() {
    console.log('布局变化，重新规划层级...');
    
    // 如果启用了智能规划，重新规划层级
    if (this.config.enableIntelligentPlanning && this.hierarchyPlanner) {
      this.hierarchyPlanner.replanHierarchy();
    }
  }

  /**
   * 处理断点变化
   */
  handleBreakpointChange(breakpointInfo) {
    console.log(`断点变化: ${breakpointInfo.previous} -> ${breakpointInfo.current}`);
    
    // 应用响应式优化
    this.applyResponsiveOptimizations(breakpointInfo);
  }

  /**
   * 执行全局优化
   */
  performGlobalOptimizations() {
    // 优化全局资源使用
    this.optimizeGlobalResources();
    
    // 预加载下一个可能访问的页面
    this.prefetchNextPages();
    
    // 优化内存使用
    this.optimizeMemory();
  }

  /**
   * 优化全局资源
   */
  optimizeGlobalResources() {
    // 这里可以添加全局资源优化逻辑
  }

  /**
   * 预加载下一个页面
   */
  prefetchNextPages() {
    if (this.pageOptimizer) {
      this.pageOptimizer.predictAndPreloadNextPage();
    }
  }

  /**
   * 优化内存使用
   */
  optimizeMemory() {
    // 这里可以添加内存优化逻辑
  }

  /**
   * 执行渲染后的优化
   */
  performPostRenderOptimizations() {
    // 延迟加载非关键内容
    this.deferLoadNonCriticalContent();
    
    // 优化已渲染的组件
    this.optimizeRenderedComponents();
  }

  /**
   * 延迟加载非关键内容
   */
  deferLoadNonCriticalContent() {
    // 这里可以添加延迟加载逻辑
  }

  /**
   * 优化已渲染的组件
   */
  optimizeRenderedComponents() {
    // 优化每个已渲染的组件
    if (this.componentManager && this.componentManager.loadedComponents) {
      Object.keys(this.componentManager.loadedComponents).forEach(componentId => {
        if (this.pageOptimizer) {
          this.pageOptimizer.optimizeComponent(componentId);
        }
      });
    }
  }

  /**
   * 应用响应式优化
   * @param {Object} breakpointInfo - 断点信息
   */
  applyResponsiveOptimizations(breakpointInfo) {
    const { current: breakpoint } = breakpointInfo;
    
    // 根据断点调整优化策略
    if (breakpoint === 'xs' || breakpoint === 'sm') {
      // 移动设备优化
      this.applyMobileOptimizations();
    } else {
      // 桌面设备优化
      this.applyDesktopOptimizations();
    }
  }

  /**
   * 应用移动设备优化
   */
  applyMobileOptimizations() {
    // 移动设备上的特定优化
    
    // 禁用某些可能影响移动设备性能的功能
    if (this.config.optimizationLevel === 'aggressive') {
      // 更激进地优化移动体验
    }
  }

  /**
   * 应用桌面设备优化
   */
  applyDesktopOptimizations() {
    // 桌面设备上的特定优化
  }

  /**
   * 报告优化结果
   */
  reportOptimizationResults() {
    const results = {
      hierarchy: null,
      performance: null,
      overallScore: 0
    };
    
    // 收集层级规划结果
    if (this.hierarchyPlanner) {
      results.hierarchy = this.hierarchyPlanner.getOptimizationMetrics();
    }
    
    // 收集性能优化结果
    if (this.pageOptimizer) {
      results.performance = this.pageOptimizer.getPerformanceData();
    }
    
    // 计算总体优化分数
    results.overallScore = this.calculateOverallScore(results);
    
    console.log('优化结果报告:', results);
    
    // 触发优化完成事件
    this.emit('intelligent-planner:optimization-complete', results);
    
    return results;
  }

  /**
   * 计算总体优化分数
   * @param {Object} results - 优化结果
   * @returns {Number} 总体分数
   */
  calculateOverallScore(results) {
    let score = 0;
    let weight = 0;
    
    // 考虑层级规划分数
    if (results.hierarchy && results.hierarchy.performanceScore) {
      score += results.hierarchy.performanceScore * 0.4;
      weight += 0.4;
    }
    
    // 考虑性能数据
    if (results.performance) {
      // 基于页面加载时间计算分数
      const loadTimeScore = this.calculateLoadTimeScore(results.performance.pageLoadTime || 0);
      score += loadTimeScore * 0.6;
      weight += 0.6;
    }
    
    // 计算加权平均分
    return weight > 0 ? Math.round(score / weight) : 0;
  }

  /**
   * 计算加载时间分数
   * @param {Number} loadTime - 加载时间（毫秒）
   * @returns {Number} 分数（0-100）
   */
  calculateLoadTimeScore(loadTime) {
    // 1000ms以内得满分，超过3000ms得最低分
    if (loadTime <= 1000) return 100;
    if (loadTime >= 3000) return 40;
    
    // 线性计分
    return Math.round(100 - ((loadTime - 1000) / 20));
  }

  /**
   * 重新优化整个页面
   */
  reoptimize() {
    console.log('重新执行全面优化...');
    
    // 重新规划层级
    if (this.hierarchyPlanner) {
      this.hierarchyPlanner.replanHierarchy();
    }
    
    // 重新优化性能
    if (this.pageOptimizer) {
      this.pageOptimizer.optimizePageLoad();
    }
    
    // 报告新的优化结果
    return this.reportOptimizationResults();
  }

  /**
   * 智能分析当前页面并提出优化建议
   * @returns {Object} 优化建议
   */
  analyzeAndSuggest() {
    const suggestions = {
      critical: [],
      recommendations: [],
      potentialImprovements: []
    };
    
    // 分析页面结构
    this.analyzePageStructure(suggestions);
    
    // 分析性能数据
    this.analyzePerformanceData(suggestions);
    
    // 分析组件层级
    this.analyzeComponentHierarchy(suggestions);
    
    console.log('优化建议:', suggestions);
    
    return suggestions;
  }

  /**
   * 分析页面结构
   */
  analyzePageStructure(suggestions) {
    // 这里可以添加页面结构分析逻辑
  }

  /**
   * 分析性能数据
   */
  analyzePerformanceData(suggestions) {
    // 这里可以添加性能数据分析逻辑
  }

  /**
   * 分析组件层级
   */
  analyzeComponentHierarchy(suggestions) {
    // 这里可以添加组件层级分析逻辑
  }

  /**
   * 触发事件
   * @param {String} event - 事件名称
   * @param {*} data - 事件数据
   */
  emit(event, data) {
    if (this.componentBus) {
      this.componentBus.emit(event, data);
    } else {
      // 如果组件总线不可用，使用自定义事件作为后备
      const customEvent = new CustomEvent(event, {
        detail: data,
        bubbles: true,
        cancelable: true
      });
      document.dispatchEvent(customEvent);
    }
  }

  /**
   * 获取配置
   * @returns {Object} 配置对象
   */
  getConfig() {
    return { ...this.config };
  }

  /**
   * 获取模块状态
   * @returns {Object} 模块状态
   */
  getModuleStatus() {
    return {
      isInitialized: this.isInitialized,
      modulesLoaded: { ...this.modulesLoaded },
      config: { ...this.config }
    };
  }

  /**
   * 销毁整合器
   */
  destroy() {
    console.log('销毁智能规划整合器...');
    
    // 清理事件监听
    window.removeEventListener('load', this.handleWindowLoad);
    document.removeEventListener('DOMContentLoaded', this.handleDomContentLoaded);
    
    // 销毁各个模块
    if (this.hierarchyPlanner) {
      this.hierarchyPlanner.destroy();
    }
    
    if (this.pageOptimizer) {
      this.pageOptimizer.destroy();
    }
    
    if (this.componentBus) {
      // 移除组件总线上的事件监听
      // 注意：不要销毁组件总线，因为它可能被其他模块使用
    }
    
    this.isInitialized = false;
    console.log('智能规划整合器已销毁');
  }
}

// 创建智能规划整合器实例
const intelligentPlanner = new IntelligentPlannerIntegrator();

// 导出
if (typeof window !== 'undefined') {
  window.IntelligentPlannerIntegrator = IntelligentPlannerIntegrator;
  window.intelligentPlanner = intelligentPlanner;
}

export { IntelligentPlannerIntegrator, intelligentPlanner };