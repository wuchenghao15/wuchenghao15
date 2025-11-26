// 智能层级规划器 - 负责页面组件的智能分析、层级优化和渲染规划
class IntelligentHierarchyPlanner {
  constructor(componentManager = null, layoutManager = null) {
    this.componentManager = componentManager || window.componentManager;
    this.layoutManager = layoutManager || window.layoutManager;
    this.componentDependencies = {};
    this.renderOrder = [];
    this.optimizationMetrics = {
      renderTime: 0,
      componentCount: 0,
      dependencyDepth: 0,
      performanceScore: 0
    };
    this.analysisResults = {};
    this.isInitialized = false;
    
    // 初始化智能层级规划器
    this.initialize();
  }

  /**
   * 初始化智能层级规划器
   */
  initialize() {
    if (this.isInitialized) return;
    
    // 注册事件监听
    this.setupEventListeners();
    
    this.isInitialized = true;
    console.log('智能层级规划器初始化完成');
  }

  /**
   * 设置事件监听器
   */
  setupEventListeners() {
    // 监听组件加载完成事件
    window.componentBus?.on('component:loaded', this.handleComponentLoaded.bind(this));
    
    // 监听页面渲染前事件
    window.componentBus?.on('page:beforerender', this.planHierarchy.bind(this));
    
    // 监听布局变化事件
    window.componentBus?.on('layout:changed', this.replanHierarchy.bind(this));
    
    // 监听断点变化事件
    window.componentBus?.on('breakpoint:change', this.adjustForBreakpoint.bind(this));
  }

  /**
   * 分析组件关系和依赖
   * @param {Object} componentsConfig - 组件配置对象
   * @returns {Object} 分析结果
   */
  analyzeComponentRelationships(componentsConfig) {
    const analysis = {
      dependencies: {},
      componentsByType: {},
      criticalPath: [],
      componentCount: 0,
      dependencyGraph: {}
    };
    
    // 收集所有组件
    const allComponents = this.collectAllComponents(componentsConfig);
    analysis.componentCount = Object.keys(allComponents).length;
    
    // 分析组件类型
    for (const [componentId, component] of Object.entries(allComponents)) {
      const type = component.type || 'unknown';
      if (!analysis.componentsByType[type]) {
        analysis.componentsByType[type] = [];
      }
      analysis.componentsByType[type].push(componentId);
      
      // 初始化依赖图
      analysis.dependencyGraph[componentId] = {
        dependsOn: component.dependsOn || [],
        usedBy: []
      };
    }
    
    // 构建依赖关系
    for (const [componentId, graphNode] of Object.entries(analysis.dependencyGraph)) {
      graphNode.dependsOn.forEach(depId => {
        if (analysis.dependencyGraph[depId]) {
          analysis.dependencyGraph[depId].usedBy.push(componentId);
        }
      });
    }
    
    // 计算关键路径
    analysis.criticalPath = this.calculateCriticalPath(analysis.dependencyGraph);
    
    this.analysisResults = analysis;
    this.componentDependencies = analysis.dependencyGraph;
    
    return analysis;
  }

  /**
   * 收集所有组件
   * @param {Object} componentsConfig - 组件配置
   * @returns {Object} 所有组件的映射
   */
  collectAllComponents(componentsConfig) {
    const components = {};
    
    // 收集全局组件
    if (componentsConfig.components?.global) {
      Object.entries(componentsConfig.components.global).forEach(([id, config]) => {
        components[id] = { ...config, id };
      });
    }
    
    // 收集页面特定组件
    if (componentsConfig.components?.['page-specific']) {
      Object.entries(componentsConfig.components['page-specific']).forEach(([id, config]) => {
        components[id] = { ...config, id };
      });
    }
    
    // 收集可复用组件
    if (componentsConfig.components?.reusable) {
      Object.entries(componentsConfig.components.reusable).forEach(([id, config]) => {
        components[id] = { ...config, id };
      });
    }
    
    return components;
  }

  /**
   * 计算组件渲染的关键路径
   * @param {Object} dependencyGraph - 依赖图
   * @returns {Array} 关键路径上的组件ID列表
   */
  calculateCriticalPath(dependencyGraph) {
    // 使用拓扑排序找出依赖最深的路径
    const visited = new Set();
    const pathLengths = {};
    const paths = {};
    
    // 初始化路径长度
    Object.keys(dependencyGraph).forEach(node => {
      pathLengths[node] = 0;
      paths[node] = [node];
    });
    
    // 深度优先搜索计算最长路径
    const dfs = (node) => {
      if (visited.has(node)) return;
      visited.add(node);
      
      dependencyGraph[node].dependsOn.forEach(dep => {
        dfs(dep);
        const newLength = pathLengths[dep] + 1;
        if (newLength > pathLengths[node]) {
          pathLengths[node] = newLength;
          paths[node] = [...paths[dep], node];
        }
      });
    };
    
    // 对所有节点执行DFS
    Object.keys(dependencyGraph).forEach(node => {
      if (!visited.has(node)) {
        dfs(node);
      }
    });
    
    // 找出最长路径
    let maxLength = 0;
    let criticalPath = [];
    
    Object.entries(pathLengths).forEach(([node, length]) => {
      if (length > maxLength) {
        maxLength = length;
        criticalPath = paths[node];
      }
    });
    
    return criticalPath;
  }

  /**
   * 规划组件层级和渲染顺序
   * @param {Object} componentsConfig - 组件配置
   * @returns {Array} 优化后的渲染顺序
   */
  planHierarchy(componentsConfig) {
    const config = componentsConfig || this.componentManager?.componentsConfig;
    if (!config) {
      console.error('无法获取组件配置，规划失败');
      return [];
    }
    
    // 分析组件关系
    const analysis = this.analyzeComponentRelationships(config);
    
    // 根据依赖关系计算渲染顺序
    const renderOrder = this.calculateOptimalRenderOrder(analysis.dependencyGraph);
    
    // 应用智能优化
    const optimizedOrder = this.applyIntelligentOptimizations(renderOrder, analysis);
    
    this.renderOrder = optimizedOrder;
    
    // 记录优化指标
    this.updateOptimizationMetrics(analysis, renderOrder);
    
    console.log('组件层级规划完成，优化后的渲染顺序:', optimizedOrder);
    
    return optimizedOrder;
  }

  /**
   * 计算最优渲染顺序
   * @param {Object} dependencyGraph - 依赖图
   * @returns {Array} 渲染顺序
   */
  calculateOptimalRenderOrder(dependencyGraph) {
    // 使用拓扑排序算法
    const inDegree = {};
    const queue = [];
    const order = [];
    
    // 初始化入度
    Object.keys(dependencyGraph).forEach(node => {
      inDegree[node] = dependencyGraph[node].dependsOn.length;
      if (inDegree[node] === 0) {
        queue.push(node);
      }
    });
    
    // 拓扑排序
    while (queue.length > 0) {
      // 优先处理全局组件
      const globalComponents = queue.filter(id => 
        this.analysisResults.componentsByType.global?.includes(id)
      );
      
      let nextNode;
      if (globalComponents.length > 0) {
        nextNode = globalComponents[0];
        const index = queue.indexOf(nextNode);
        queue.splice(index, 1);
      } else {
        nextNode = queue.shift();
      }
      
      order.push(nextNode);
      
      // 更新依赖节点的入度
      dependencyGraph[nextNode].usedBy.forEach(dep => {
        inDegree[dep]--;
        if (inDegree[dep] === 0) {
          queue.push(dep);
        }
      });
    }
    
    return order;
  }

  /**
   * 应用智能优化
   * @param {Array} renderOrder - 渲染顺序
   * @param {Object} analysis - 分析结果
   * @returns {Array} 优化后的渲染顺序
   */
  applyIntelligentOptimizations(renderOrder, analysis) {
    // 复制渲染顺序
    const optimizedOrder = [...renderOrder];
    
    // 根据当前断点进行优化
    if (this.layoutManager?.currentBreakpoint) {
      this.optimizeForCurrentBreakpoint(optimizedOrder);
    }
    
    // 优先渲染可视区域内的组件
    this.prioritizeVisibleComponents(optimizedOrder);
    
    // 延迟加载非关键组件
    this.deferNonCriticalComponents(optimizedOrder, analysis.criticalPath);
    
    return optimizedOrder;
  }

  /**
   * 为当前断点优化渲染顺序
   * @param {Array} renderOrder - 渲染顺序
   */
  optimizeForCurrentBreakpoint(renderOrder) {
    const breakpoint = this.layoutManager.currentBreakpoint;
    const isMobile = this.layoutManager.isMobile;
    
    // 移动设备上优先加载核心功能组件
    if (isMobile) {
      const mobilePriorityComponents = ['header', 'content', 'footer'];
      
      // 将核心组件移到前面
      mobilePriorityComponents.forEach(comp => {
        const index = renderOrder.indexOf(comp);
        if (index > 0) {
          renderOrder.splice(index, 1);
          renderOrder.unshift(comp);
        }
      });
    }
  }

  /**
   * 优先渲染可视区域内的组件
   * @param {Array} renderOrder - 渲染顺序
   */
  prioritizeVisibleComponents(renderOrder) {
    // 检查组件是否在可视区域内
    const visibleComponents = [];
    const nonVisibleComponents = [];
    
    renderOrder.forEach(componentId => {
      // 这里可以添加逻辑来判断组件是否在可视区域内
      // 简化版本：认为header、content相关组件总是可见的
      if (componentId.includes('header') || componentId.includes('content') || 
          ['main-content', 'dashboard', 'navigation'].includes(componentId)) {
        visibleComponents.push(componentId);
      } else {
        nonVisibleComponents.push(componentId);
      }
    });
    
    // 重新排序：可视组件在前，非可视组件在后
    renderOrder.length = 0;
    renderOrder.push(...visibleComponents, ...nonVisibleComponents);
  }

  /**
   * 延迟加载非关键组件
   * @param {Array} renderOrder - 渲染顺序
   * @param {Array} criticalPath - 关键路径
   */
  deferNonCriticalComponents(renderOrder, criticalPath) {
    // 非关键组件移到后面
    const nonCritical = renderOrder.filter(id => !criticalPath.includes(id));
    const critical = renderOrder.filter(id => criticalPath.includes(id));
    
    renderOrder.length = 0;
    renderOrder.push(...critical, ...nonCritical);
  }

  /**
   * 更新优化指标
   * @param {Object} analysis - 分析结果
   * @param {Array} renderOrder - 渲染顺序
   */
  updateOptimizationMetrics(analysis, renderOrder) {
    this.optimizationMetrics = {
      renderTime: 0, // 将在实际渲染时更新
      componentCount: analysis.componentCount,
      dependencyDepth: analysis.criticalPath.length,
      performanceScore: this.calculatePerformanceScore(analysis, renderOrder)
    };
  }

  /**
   * 计算性能分数
   * @param {Object} analysis - 分析结果
   * @param {Array} renderOrder - 渲染顺序
   * @returns {Number} 性能分数
   */
  calculatePerformanceScore(analysis, renderOrder) {
    let score = 100;
    
    // 基于组件数量的扣分
    if (analysis.componentCount > 20) {
      score -= (analysis.componentCount - 20) * 0.5;
    }
    
    // 基于依赖深度的扣分
    if (analysis.dependencyDepth > 5) {
      score -= (analysis.dependencyDepth - 5) * 2;
    }
    
    // 确保分数在0-100之间
    return Math.max(0, Math.min(100, score));
  }

  /**
   * 重新规划层级
   */
  replanHierarchy() {
    console.log('重新规划组件层级...');
    this.planHierarchy();
    
    // 通知组件管理器使用新的渲染顺序
    window.componentBus?.emit('hierarchy:replanned', {
      renderOrder: this.renderOrder,
      metrics: this.optimizationMetrics
    });
  }

  /**
   * 根据断点调整层级
   * @param {Object} breakpointInfo - 断点信息
   */
  adjustForBreakpoint(breakpointInfo) {
    console.log(`断点变化: ${breakpointInfo.previous} -> ${breakpointInfo.current}`);
    
    // 根据新断点重新优化渲染顺序
    const optimizedOrder = this.applyIntelligentOptimizations([...this.renderOrder], this.analysisResults);
    
    if (JSON.stringify(optimizedOrder) !== JSON.stringify(this.renderOrder)) {
      this.renderOrder = optimizedOrder;
      
      // 通知组件管理器使用新的渲染顺序
      window.componentBus?.emit('hierarchy:breakpoint-adjusted', {
        renderOrder: this.renderOrder,
        breakpoint: breakpointInfo.current
      });
    }
  }

  /**
   * 处理组件加载完成事件
   * @param {Object} eventData - 事件数据
   */
  handleComponentLoaded(eventData) {
    const { componentId, loadTime } = eventData;
    
    // 更新优化指标中的渲染时间
    if (loadTime) {
      this.optimizationMetrics.renderTime += loadTime;
    }
    
    // 记录组件加载信息
    console.log(`组件 ${componentId} 加载完成，耗时: ${loadTime || '未知'}ms`);
  }

  /**
   * 获取组件依赖关系
   * @param {String} componentId - 组件ID
   * @returns {Object} 依赖关系
   */
  getComponentDependencies(componentId) {
    return this.componentDependencies[componentId] || { dependsOn: [], usedBy: [] };
  }

  /**
   * 获取优化后的渲染顺序
   * @returns {Array} 渲染顺序
   */
  getRenderOrder() {
    return this.renderOrder;
  }

  /**
   * 获取优化指标
   * @returns {Object} 优化指标
   */
  getOptimizationMetrics() {
    return { ...this.optimizationMetrics };
  }

  /**
   * 获取分析结果
   * @returns {Object} 分析结果
   */
  getAnalysisResults() {
    return { ...this.analysisResults };
  }

  /**
   * 为组件添加依赖
   * @param {String} componentId - 组件ID
   * @param {Array} dependencies - 依赖组件ID列表
   */
  addComponentDependencies(componentId, dependencies) {
    if (!this.componentDependencies[componentId]) {
      this.componentDependencies[componentId] = { dependsOn: [], usedBy: [] };
    }
    
    dependencies.forEach(depId => {
      if (!this.componentDependencies[componentId].dependsOn.includes(depId)) {
        this.componentDependencies[componentId].dependsOn.push(depId);
        
        // 更新被依赖组件的usedBy列表
        if (!this.componentDependencies[depId]) {
          this.componentDependencies[depId] = { dependsOn: [], usedBy: [] };
        }
        if (!this.componentDependencies[depId].usedBy.includes(componentId)) {
          this.componentDependencies[depId].usedBy.push(componentId);
        }
      }
    });
    
    // 重新规划层级
    this.replanHierarchy();
  }

  /**
   * 销毁规划器
   */
  destroy() {
    // 移除事件监听
    window.componentBus?.off('component:loaded', this.handleComponentLoaded);
    window.componentBus?.off('page:beforerender', this.planHierarchy);
    window.componentBus?.off('layout:changed', this.replanHierarchy);
    window.componentBus?.off('breakpoint:change', this.adjustForBreakpoint);
    
    this.isInitialized = false;
  }
}

// 创建单例实例
const intelligentHierarchyPlanner = new IntelligentHierarchyPlanner();

// 导出
if (typeof window !== 'undefined') {
  window.IntelligentHierarchyPlanner = IntelligentHierarchyPlanner;
  window.intelligentHierarchyPlanner = intelligentHierarchyPlanner;
}

export { IntelligentHierarchyPlanner, intelligentHierarchyPlanner };