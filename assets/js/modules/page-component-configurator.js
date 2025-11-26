// 页面组件配置器 - 管理页面组件配置和关系配置文件
class PageComponentConfigurator {
  constructor() {
    // 页面配置存储
    this.pageConfigs = new Map();
    
    // 组件默认配置
    this.componentDefaults = new Map();
    
    // 配置版本控制
    this.configVersions = new Map();
    
    // 配置验证规则
    this.validationRules = {
      component: this.validateComponentConfig,
      page: this.validatePageConfig,
      relationship: this.validateRelationshipConfig
    };
    
    // 配置文件路径
    this.configPaths = {
      pageConfigs: '/assets/config/pages/',
      componentConfigs: '/assets/config/components/',
      relationshipConfigs: '/assets/config/relationships/',
      defaultConfig: '/assets/config/defaults.json'
    };
    
    // 初始化状态
    this.isInitialized = false;
    this.isLoading = false;
    this.loadErrors = [];
  }

  /**
   * 初始化配置器
   */
  async initialize() {
    if (this.isInitialized) return true;
    
    try {
      this.isLoading = true;
      this.loadErrors = [];
      
      console.log('初始化页面组件配置器...');
      
      // 加载默认配置
      await this.loadDefaultConfig();
      
      // 加载组件默认配置
      await this.loadComponentDefaults();
      
      // 加载页面配置
      await this.loadPageConfigs();
      
      // 加载关系配置
      await this.loadRelationshipConfigs();
      
      this.isInitialized = true;
      console.log('页面组件配置器初始化完成');
      
      return true;
    } catch (error) {
      console.error('初始化页面组件配置器失败:', error);
      this.loadErrors.push({ type: 'initialization', error: error.message });
      return false;
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * 加载默认配置
   */
  async loadDefaultConfig() {
    try {
      const response = await fetch(this.configPaths.defaultConfig);
      
      if (!response.ok) {
        throw new Error(`加载默认配置失败: HTTP ${response.status}`);
      }
      
      const defaultConfig = await response.json();
      
      // 应用默认配置
      if (defaultConfig.configPaths) {
        this.configPaths = { ...this.configPaths, ...defaultConfig.configPaths };
      }
      
      if (defaultConfig.validationRules) {
        this.validationRules = { ...this.validationRules, ...defaultConfig.validationRules };
      }
      
      if (defaultConfig.componentDefaults) {
        Object.entries(defaultConfig.componentDefaults).forEach(([componentType, defaults]) => {
          this.componentDefaults.set(componentType, defaults);
        });
      }
      
      console.log('默认配置加载完成');
      return true;
    } catch (error) {
      console.warn('无法加载默认配置文件，使用内置默认值:', error.message);
      return false;
    }
  }

  /**
   * 加载组件默认配置
   */
  async loadComponentDefaults() {
    try {
      const response = await fetch(`${this.configPaths.componentConfigs}index.json`);
      
      if (!response.ok) {
        console.warn(`无法加载组件配置索引: HTTP ${response.status}`);
        return false;
      }
      
      const componentTypes = await response.json();
      
      // 加载每种组件类型的默认配置
      const loadPromises = componentTypes.map(async (componentType) => {
        try {
          const configResponse = await fetch(`${this.configPaths.componentConfigs}${componentType}.json`);
          
          if (configResponse.ok) {
            const config = await configResponse.json();
            this.componentDefaults.set(componentType, config);
            console.log(`组件默认配置加载完成: ${componentType}`);
          }
        } catch (error) {
          console.warn(`无法加载组件默认配置: ${componentType}`, error.message);
        }
      });
      
      await Promise.all(loadPromises);
      return true;
    } catch (error) {
      console.warn('无法加载组件默认配置', error.message);
      return false;
    }
  }

  /**
   * 加载页面配置
   */
  async loadPageConfigs() {
    try {
      const response = await fetch(`${this.configPaths.pageConfigs}index.json`);
      
      if (!response.ok) {
        console.warn(`无法加载页面配置索引: HTTP ${response.status}`);
        return false;
      }
      
      const pageIds = await response.json();
      
      // 加载每个页面的配置
      const loadPromises = pageIds.map(async (pageId) => {
        try {
          const configResponse = await fetch(`${this.configPaths.pageConfigs}${pageId}.json`);
          
          if (configResponse.ok) {
            const config = await configResponse.json();
            const validationResult = this.validatePageConfig(config);
            
            if (validationResult.isValid) {
              this.pageConfigs.set(pageId, config);
              this.recordConfigVersion(pageId, config);
              console.log(`页面配置加载完成: ${pageId}`);
            } else {
              console.error(`页面配置验证失败: ${pageId}`, validationResult.errors);
              this.loadErrors.push({ type: 'page_config', pageId, errors: validationResult.errors });
            }
          }
        } catch (error) {
          console.warn(`无法加载页面配置: ${pageId}`, error.message);
          this.loadErrors.push({ type: 'page_config', pageId, error: error.message });
        }
      });
      
      await Promise.all(loadPromises);
      return true;
    } catch (error) {
      console.warn('无法加载页面配置', error.message);
      return false;
    }
  }

  /**
   * 加载关系配置
   */
  async loadRelationshipConfigs() {
    try {
      const response = await fetch(`${this.configPaths.relationshipConfigs}index.json`);
      
      if (!response.ok) {
        console.warn(`无法加载关系配置索引: HTTP ${response.status}`);
        return false;
      }
      
      const relationshipFiles = await response.json();
      
      // 加载每个关系配置文件
      const loadPromises = relationshipFiles.map(async (filename) => {
        try {
          const configResponse = await fetch(`${this.configPaths.relationshipConfigs}${filename}`);
          
          if (configResponse.ok) {
            const config = await configResponse.json();
            const validationResult = this.validateRelationshipConfig(config);
            
            if (validationResult.isValid) {
              // 应用关系配置到页面配置中
              this.applyRelationshipConfig(config);
              console.log(`关系配置加载完成: ${filename}`);
            } else {
              console.error(`关系配置验证失败: ${filename}`, validationResult.errors);
              this.loadErrors.push({ type: 'relationship_config', filename, errors: validationResult.errors });
            }
          }
        } catch (error) {
          console.warn(`无法加载关系配置: ${filename}`, error.message);
          this.loadErrors.push({ type: 'relationship_config', filename, error: error.message });
        }
      });
      
      await Promise.all(loadPromises);
      return true;
    } catch (error) {
      console.warn('无法加载关系配置', error.message);
      return false;
    }
  }

  /**
   * 记录配置版本
   */
  recordConfigVersion(pageId, config) {
    const version = config.version || Date.now().toString();
    const timestamp = config.lastModified || Date.now();
    
    if (!this.configVersions.has(pageId)) {
      this.configVersions.set(pageId, []);
    }
    
    const versions = this.configVersions.get(pageId);
    
    // 检查是否已存在相同版本
    const existingVersionIndex = versions.findIndex(v => v.version === version);
    
    if (existingVersionIndex === -1) {
      versions.unshift({ version, timestamp });
      
      // 限制版本历史记录数量
      if (versions.length > 10) {
        versions.pop();
      }
    }
  }

  /**
   * 应用关系配置
   */
  applyRelationshipConfig(config) {
    // 根据配置类型应用不同的关系配置
    if (config.type === 'page_components') {
      // 页面组件关系配置
      if (config.pageId && config.components) {
        const pageConfig = this.pageConfigs.get(config.pageId);
        
        if (pageConfig) {
          pageConfig.components = { ...(pageConfig.components || {}), ...config.components };
        } else {
          // 如果页面配置不存在，创建新的
          this.pageConfigs.set(config.pageId, {
            pageId: config.pageId,
            components: config.components,
            relationships: {},
            version: Date.now().toString(),
            lastModified: Date.now()
          });
        }
      }
    } else if (config.type === 'component_relationships') {
      // 组件间关系配置
      if (config.relationships) {
        Object.entries(config.relationships).forEach(([sourceComponent, targets]) => {
          Object.entries(targets).forEach(([targetComponent, relationship]) => {
            // 查找包含这些组件的页面配置并更新关系
            this.pageConfigs.forEach(pageConfig => {
              if (pageConfig.components && 
                  (pageConfig.components[sourceComponent] || pageConfig.components[targetComponent])) {
                
                if (!pageConfig.relationships) {
                  pageConfig.relationships = {};
                }
                
                if (!pageConfig.relationships[sourceComponent]) {
                  pageConfig.relationships[sourceComponent] = {};
                }
                
                pageConfig.relationships[sourceComponent][targetComponent] = relationship;
              }
            });
          });
        });
      }
    }
  }

  /**
   * 获取页面配置
   */
  getPageConfig(pageId) {
    const config = this.pageConfigs.get(pageId);
    
    if (!config) {
      // 如果没有找到配置，创建默认配置
      const defaultConfig = this.createDefaultPageConfig(pageId);
      this.pageConfigs.set(pageId, defaultConfig);
      return defaultConfig;
    }
    
    return { ...config };
  }

  /**
   * 创建默认页面配置
   */
  createDefaultPageConfig(pageId) {
    return {
      pageId,
      components: {},
      relationships: {},
      layout: {
        type: 'default',
        regions: ['header', 'content', 'footer']
      },
      responsive: {
        breakpoints: {
          xs: 0,
          sm: 576,
          md: 768,
          lg: 992,
          xl: 1200,
          xxl: 1400
        },
        layouts: {}
      },
      version: '1.0.0',
      lastModified: Date.now(),
      created: Date.now()
    };
  }

  /**
   * 保存页面配置
   */
  async savePageConfig(pageConfig) {
    // 验证配置
    const validationResult = this.validatePageConfig(pageConfig);
    
    if (!validationResult.isValid) {
      throw new Error(`配置验证失败: ${validationResult.errors.join(', ')}`);
    }
    
    // 更新最后修改时间
    pageConfig.lastModified = Date.now();
    
    // 如果没有版本，生成版本
    if (!pageConfig.version) {
      pageConfig.version = '1.0.0';
    } else {
      // 更新版本号（简单的补丁版本递增）
      const versionParts = pageConfig.version.split('.');
      versionParts[2] = parseInt(versionParts[2], 10) + 1;
      pageConfig.version = versionParts.join('.');
    }
    
    // 保存到内存中
    this.pageConfigs.set(pageConfig.pageId, { ...pageConfig });
    
    // 记录版本
    this.recordConfigVersion(pageConfig.pageId, pageConfig);
    
    try {
      // 尝试保存到服务器（在实际环境中）
      // await this.saveConfigToServer(pageConfig.pageId, pageConfig);
      console.log(`页面配置已保存: ${pageConfig.pageId} (v${pageConfig.version})`);
      return true;
    } catch (error) {
      console.error(`保存页面配置失败: ${pageConfig.pageId}`, error.message);
      throw error;
    }
  }

  /**
   * 添加组件配置到页面
   */
  addComponentToPage(pageId, componentId, componentConfig) {
    const pageConfig = this.getPageConfig(pageId);
    
    // 应用组件默认配置
    const componentType = componentConfig.type || 'generic';
    const defaults = this.componentDefaults.get(componentType) || {};
    
    // 合并默认配置和用户配置
    const mergedConfig = {
      ...defaults,
      id: componentId,
      ...componentConfig,
      lastModified: Date.now()
    };
    
    // 验证组件配置
    const validationResult = this.validateComponentConfig(mergedConfig);
    
    if (!validationResult.isValid) {
      throw new Error(`组件配置验证失败: ${validationResult.errors.join(', ')}`);
    }
    
    // 添加到页面配置
    pageConfig.components[componentId] = mergedConfig;
    
    return true;
  }

  /**
   * 更新页面中的组件配置
   */
  updateComponentInPage(pageId, componentId, updates) {
    const pageConfig = this.getPageConfig(pageId);
    
    if (!pageConfig.components || !pageConfig.components[componentId]) {
      throw new Error(`组件 ${componentId} 不在页面 ${pageId} 的配置中`);
    }
    
    // 更新组件配置
    const updatedConfig = {
      ...pageConfig.components[componentId],
      ...updates,
      lastModified: Date.now()
    };
    
    // 验证更新后的配置
    const validationResult = this.validateComponentConfig(updatedConfig);
    
    if (!validationResult.isValid) {
      throw new Error(`更新后的组件配置验证失败: ${validationResult.errors.join(', ')}`);
    }
    
    // 保存更新
    pageConfig.components[componentId] = updatedConfig;
    
    return true;
  }

  /**
   * 从页面中移除组件
   */
  removeComponentFromPage(pageId, componentId) {
    const pageConfig = this.getPageConfig(pageId);
    
    if (!pageConfig.components || !pageConfig.components[componentId]) {
      console.warn(`组件 ${componentId} 不在页面 ${pageId} 的配置中`);
      return false;
    }
    
    // 移除组件配置
    delete pageConfig.components[componentId];
    
    // 移除相关关系
    if (pageConfig.relationships) {
      // 移除作为源组件的关系
      if (pageConfig.relationships[componentId]) {
        delete pageConfig.relationships[componentId];
      }
      
      // 移除作为目标组件的关系
      Object.keys(pageConfig.relationships).forEach(sourceId => {
        if (pageConfig.relationships[sourceId][componentId]) {
          delete pageConfig.relationships[sourceId][componentId];
        }
      });
    }
    
    return true;
  }

  /**
   * 添加组件关系
   */
  addComponentRelationship(pageId, sourceComponentId, targetComponentId, relationship) {
    const pageConfig = this.getPageConfig(pageId);
    
    // 验证组件是否存在
    if (!pageConfig.components || 
        !pageConfig.components[sourceComponentId] || 
        !pageConfig.components[targetComponentId]) {
      throw new Error('源组件或目标组件不存在于页面配置中');
    }
    
    // 验证关系配置
    const relationshipConfig = {
      source: sourceComponentId,
      target: targetComponentId,
      ...relationship
    };
    
    const validationResult = this.validateRelationshipConfig(relationshipConfig);
    
    if (!validationResult.isValid) {
      throw new Error(`关系配置验证失败: ${validationResult.errors.join(', ')}`);
    }
    
    // 初始化关系对象
    if (!pageConfig.relationships) {
      pageConfig.relationships = {};
    }
    
    if (!pageConfig.relationships[sourceComponentId]) {
      pageConfig.relationships[sourceComponentId] = {};
    }
    
    // 添加关系
    pageConfig.relationships[sourceComponentId][targetComponentId] = {
      ...relationship,
      lastModified: Date.now()
    };
    
    return true;
  }

  /**
   * 更新组件关系
   */
  updateComponentRelationship(pageId, sourceComponentId, targetComponentId, updates) {
    const pageConfig = this.getPageConfig(pageId);
    
    if (!pageConfig.relationships || 
        !pageConfig.relationships[sourceComponentId] || 
        !pageConfig.relationships[sourceComponentId][targetComponentId]) {
      throw new Error('组件关系不存在');
    }
    
    // 更新关系
    const updatedRelationship = {
      ...pageConfig.relationships[sourceComponentId][targetComponentId],
      ...updates,
      lastModified: Date.now()
    };
    
    // 验证更新后的关系
    const relationshipConfig = {
      source: sourceComponentId,
      target: targetComponentId,
      ...updatedRelationship
    };
    
    const validationResult = this.validateRelationshipConfig(relationshipConfig);
    
    if (!validationResult.isValid) {
      throw new Error(`更新后的关系配置验证失败: ${validationResult.errors.join(', ')}`);
    }
    
    // 保存更新
    pageConfig.relationships[sourceComponentId][targetComponentId] = updatedRelationship;
    
    return true;
  }

  /**
   * 移除组件关系
   */
  removeComponentRelationship(pageId, sourceComponentId, targetComponentId) {
    const pageConfig = this.getPageConfig(pageId);
    
    if (!pageConfig.relationships || 
        !pageConfig.relationships[sourceComponentId] || 
        !pageConfig.relationships[sourceComponentId][targetComponentId]) {
      console.warn('组件关系不存在');
      return false;
    }
    
    // 移除关系
    delete pageConfig.relationships[sourceComponentId][targetComponentId];
    
    // 如果源组件没有更多关系，移除整个源组件关系对象
    if (Object.keys(pageConfig.relationships[sourceComponentId]).length === 0) {
      delete pageConfig.relationships[sourceComponentId];
    }
    
    return true;
  }

  /**
   * 配置页面布局
   */
  configurePageLayout(pageId, layoutConfig) {
    const pageConfig = this.getPageConfig(pageId);
    
    // 合并布局配置
    pageConfig.layout = { ...pageConfig.layout, ...layoutConfig };
    
    return true;
  }

  /**
   * 配置页面响应式设置
   */
  configureResponsive(pageId, responsiveConfig) {
    const pageConfig = this.getPageConfig(pageId);
    
    // 合并响应式配置
    pageConfig.responsive = { ...pageConfig.responsive, ...responsiveConfig };
    
    return true;
  }

  /**
   * 验证页面配置
   */
  validatePageConfig(config) {
    const errors = [];
    
    // 检查必需字段
    if (!config.pageId) {
      errors.push('缺少必需字段 pageId');
    }
    
    // 检查组件配置
    if (config.components) {
      Object.entries(config.components).forEach(([componentId, componentConfig]) => {
        const validationResult = this.validateComponentConfig(componentConfig);
        if (!validationResult.isValid) {
          errors.push(`组件 ${componentId} 配置错误: ${validationResult.errors.join(', ')}`);
        }
      });
    }
    
    // 检查关系配置
    if (config.relationships) {
      Object.entries(config.relationships).forEach(([sourceId, targets]) => {
        Object.entries(targets).forEach(([targetId, relationship]) => {
          const relationshipConfig = {
            source: sourceId,
            target: targetId,
            ...relationship
          };
          
          const validationResult = this.validateRelationshipConfig(relationshipConfig);
          if (!validationResult.isValid) {
            errors.push(`关系 ${sourceId} -> ${targetId} 配置错误: ${validationResult.errors.join(', ')}`);
          }
        });
      });
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * 验证组件配置
   */
  validateComponentConfig(config) {
    const errors = [];
    
    // 检查必需字段
    if (!config.id) {
      errors.push('缺少必需字段 id');
    }
    
    // 检查类型
    if (!config.type) {
      errors.push('缺少必需字段 type');
    }
    
    // 检查层级
    if (config.level !== undefined && (typeof config.level !== 'number' || config.level < 0)) {
      errors.push('level 必须是非负整数');
    }
    
    // 检查区域
    if (config.region && typeof config.region !== 'string') {
      errors.push('region 必须是字符串');
    }
    
    // 检查可见性
    if (config.visible !== undefined && typeof config.visible !== 'boolean') {
      errors.push('visible 必须是布尔值');
    }
    
    // 检查条件
    if (config.conditions && !Array.isArray(config.conditions)) {
      errors.push('conditions 必须是数组');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * 验证关系配置
   */
  validateRelationshipConfig(config) {
    const errors = [];
    
    // 检查必需字段
    if (!config.source) {
      errors.push('缺少必需字段 source');
    }
    
    if (!config.target) {
      errors.push('缺少必需字段 target');
    }
    
    // 检查关系类型
    const validTypes = ['parent', 'child', 'sibling', 'dependency', 'dependent', 'trigger', 'observe'];
    if (config.type && !validTypes.includes(config.type)) {
      errors.push(`无效的关系类型: ${config.type}，有效类型: ${validTypes.join(', ')}`);
    }
    
    // 检查循环依赖
    if (config.source === config.target && config.type === 'dependency') {
      errors.push('组件不能依赖自身');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * 导出页面配置
   */
  exportPageConfig(pageId) {
    const config = this.pageConfigs.get(pageId);
    
    if (!config) {
      throw new Error(`页面配置不存在: ${pageId}`);
    }
    
    return JSON.stringify(config, null, 2);
  }

  /**
   * 导入页面配置
   */
  async importPageConfig(jsonConfig) {
    try {
      const config = typeof jsonConfig === 'string' ? JSON.parse(jsonConfig) : jsonConfig;
      
      // 验证配置
      const validationResult = this.validatePageConfig(config);
      
      if (!validationResult.isValid) {
        throw new Error(`导入的配置验证失败: ${validationResult.errors.join(', ')}`);
      }
      
      // 保存配置
      await this.savePageConfig(config);
      
      console.log(`页面配置已导入: ${config.pageId}`);
      return true;
    } catch (error) {
      console.error('导入页面配置失败:', error.message);
      throw error;
    }
  }

  /**
   * 生成页面组件关系配置文件
   */
  generateRelationshipConfig(pageId) {
    const pageConfig = this.getPageConfig(pageId);
    
    const relationshipConfig = {
      type: 'page_components',
      pageId,
      components: {},
      relationships: {},
      generatedAt: Date.now()
    };
    
    // 提取组件配置
    if (pageConfig.components) {
      Object.entries(pageConfig.components).forEach(([componentId, component]) => {
        relationshipConfig.components[componentId] = {
          type: component.type,
          level: component.level,
          region: component.region,
          visible: component.visible,
          dependsOn: component.dependsOn || []
        };
      });
    }
    
    // 提取关系配置
    if (pageConfig.relationships) {
      relationshipConfig.relationships = { ...pageConfig.relationships };
    }
    
    return relationshipConfig;
  }

  /**
   * 应用智能规划建议
   */
  applyIntelligentPlanning(pageId, planningResult) {
    const pageConfig = this.getPageConfig(pageId);
    
    // 应用优化后的渲染顺序
    if (planningResult.renderOrder) {
      pageConfig.renderOrder = planningResult.renderOrder;
    }
    
    // 应用优化后的组件层级
    if (planningResult.hierarchy) {
      // 更新组件层级
      Object.entries(planningResult.hierarchy).forEach(([componentId, levelInfo]) => {
        if (pageConfig.components && pageConfig.components[componentId]) {
          pageConfig.components[componentId].level = levelInfo.level;
          pageConfig.components[componentId].parentId = levelInfo.parentId;
        }
      });
    }
    
    // 应用优化后的依赖关系
    if (planningResult.dependencies) {
      Object.entries(planningResult.dependencies).forEach(([componentId, dependencies]) => {
        if (pageConfig.components && pageConfig.components[componentId]) {
          pageConfig.components[componentId].dependsOn = dependencies;
        }
      });
    }
    
    // 标记为智能优化
    pageConfig.intelligentlyOptimized = true;
    pageConfig.optimizationDate = Date.now();
    pageConfig.optimizationScore = planningResult.score || 0;
    
    return true;
  }

  /**
   * 比较两个页面配置
   */
  comparePageConfigs(oldConfig, newConfig) {
    const differences = {
      addedComponents: [],
      removedComponents: [],
      modifiedComponents: [],
      addedRelationships: [],
      removedRelationships: [],
      modifiedRelationships: [],
      layoutChanges: {},
      responsiveChanges: {}
    };
    
    // 比较组件
    const oldComponents = oldConfig.components || {};
    const newComponents = newConfig.components || {};
    
    // 查找添加的组件
    Object.keys(newComponents).forEach(componentId => {
      if (!oldComponents[componentId]) {
        differences.addedComponents.push(componentId);
      }
    });
    
    // 查找移除的组件
    Object.keys(oldComponents).forEach(componentId => {
      if (!newComponents[componentId]) {
        differences.removedComponents.push(componentId);
      }
    });
    
    // 查找修改的组件
    Object.keys(newComponents).forEach(componentId => {
      if (oldComponents[componentId]) {
        const oldComponent = oldComponents[componentId];
        const newComponent = newComponents[componentId];
        
        const componentDifferences = this.compareObjects(oldComponent, newComponent);
        
        if (Object.keys(componentDifferences).length > 0) {
          differences.modifiedComponents.push({
            id: componentId,
            changes: componentDifferences
          });
        }
      }
    });
    
    // 比较关系
    const oldRelationships = oldConfig.relationships || {};
    const newRelationships = newConfig.relationships || {};
    
    // 比较关系变化（略）
    
    // 比较布局
    if (oldConfig.layout || newConfig.layout) {
      differences.layoutChanges = this.compareObjects(oldConfig.layout || {}, newConfig.layout || {});
    }
    
    // 比较响应式设置
    if (oldConfig.responsive || newConfig.responsive) {
      differences.responsiveChanges = this.compareObjects(oldConfig.responsive || {}, newConfig.responsive || {});
    }
    
    return differences;
  }

  /**
   * 比较两个对象
   */
  compareObjects(oldObj, newObj) {
    const differences = {};
    
    // 合并所有键
    const allKeys = new Set([...Object.keys(oldObj), ...Object.keys(newObj)]);
    
    allKeys.forEach(key => {
      if (!oldObj.hasOwnProperty(key)) {
        differences[key] = {
          added: true,
          value: newObj[key]
        };
      } else if (!newObj.hasOwnProperty(key)) {
        differences[key] = {
          removed: true,
          value: oldObj[key]
        };
      } else if (JSON.stringify(oldObj[key]) !== JSON.stringify(newObj[key])) {
        differences[key] = {
          changed: true,
          oldValue: oldObj[key],
          newValue: newObj[key]
        };
      }
    });
    
    return differences;
  }

  /**
   * 获取所有页面ID
   */
  getAllPageIds() {
    return Array.from(this.pageConfigs.keys());
  }

  /**
   * 获取所有组件类型
   */
  getAllComponentTypes() {
    const types = new Set();
    
    // 从组件默认配置中获取类型
    this.componentDefaults.forEach((config, type) => {
      types.add(type);
    });
    
    // 从页面配置中获取类型
    this.pageConfigs.forEach(pageConfig => {
      if (pageConfig.components) {
        Object.values(pageConfig.components).forEach(component => {
          if (component.type) {
            types.add(component.type);
          }
        });
      }
    });
    
    return Array.from(types);
  }

  /**
   * 获取配置错误
   */
  getLoadErrors() {
    return [...this.loadErrors];
  }

  /**
   * 清除配置错误
   */
  clearLoadErrors() {
    this.loadErrors = [];
  }

  /**
   * 重置配置器
   */
  reset() {
    this.pageConfigs.clear();
    this.componentDefaults.clear();
    this.configVersions.clear();
    this.loadErrors = [];
    this.isInitialized = false;
    
    console.log('页面组件配置器已重置');
  }

  /**
   * 获取状态
   */
  getStatus() {
    return {
      isInitialized: this.isInitialized,
      isLoading: this.isLoading,
      pageCount: this.pageConfigs.size,
      componentTypeCount: this.componentDefaults.size,
      loadErrors: this.loadErrors.length,
      configPaths: { ...this.configPaths }
    };
  }
}

// 创建页面组件配置器实例
const componentConfigurator = new PageComponentConfigurator();

// 导出
if (typeof window !== 'undefined') {
  window.PageComponentConfigurator = PageComponentConfigurator;
  window.componentConfigurator = componentConfigurator;
}

export { PageComponentConfigurator, componentConfigurator };