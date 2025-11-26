// 层级关系管理器 - 管理组件间的父子关系和依赖关系
class HierarchyRelationshipManager {
  constructor() {
    // 组件关系图
    this.relationshipGraph = {
      components: new Map(), // 组件ID -> 组件信息
      relationships: new Map(), // 组件ID -> 关联组件映射
      hierarchyLevels: new Map() // 层级 -> 组件ID列表
    };
    
    // 依赖关系图
    this.dependencyGraph = {
      dependencies: new Map(), // 组件ID -> 依赖组件列表
      dependents: new Map() // 组件ID -> 依赖于该组件的组件列表
    };
    
    // 页面组件映射
    this.pageComponents = new Map(); // 页面ID -> 组件ID列表
    
    // 分析结果缓存
    this.analysisCache = new Map();
    
    // 配置
    this.config = {
      autoDetectRelationships: true,
      maxHierarchyDepth: 10,
      dependencyValidation: true
    };
    
    this.isInitialized = false;
  }

  /**
   * 初始化管理器
   */
  initialize() {
    if (this.isInitialized) return;
    
    console.log('初始化层级关系管理器...');
    
    // 初始化解组件
    this.initializeComponents();
    
    // 如果启用了自动检测关系，执行初始检测
    if (this.config.autoDetectRelationships) {
      this.detectInitialRelationships();
    }
    
    // 构建初始层级
    this.buildInitialHierarchy();
    
    this.isInitialized = true;
    console.log('层级关系管理器初始化完成');
  }

  /**
   * 初始化解组件
   */
  initializeComponents() {
    // 从页面中收集组件信息
    this.collectComponentsFromDOM();
    
    // 从组件管理器（如果存在）获取组件信息
    this.collectComponentsFromManager();
  }

  /**
   * 从DOM中收集组件信息
   */
  collectComponentsFromDOM() {
    // 查找所有带有component属性或data-component属性的元素
    const componentElements = document.querySelectorAll('[component], [data-component]');
    
    componentElements.forEach(element => {
      const componentId = element.id || `component-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const componentType = element.getAttribute('component') || element.getAttribute('data-component') || 'generic';
      
      // 确保元素有ID
      if (!element.id) {
        element.id = componentId;
      }
      
      // 注册组件
      this.registerComponent({
        id: componentId,
        type: componentType,
        element,
        containerId: this.getContainerId(element),
        parentId: this.findParentComponentId(element),
        position: this.getComponentPosition(element),
        visible: element.offsetParent !== null,
        loaded: true
      });
    });
  }

  /**
   * 从组件管理器收集组件信息
   */
  collectComponentsFromManager() {
    // 如果存在组件管理器，从中获取组件信息
    if (window.componentManager && window.componentManager.loadedComponents) {
      const managerComponents = window.componentManager.loadedComponents;
      
      Object.keys(managerComponents).forEach(componentId => {
        const component = managerComponents[componentId];
        
        // 如果组件已经存在，更新信息
        // 否则，注册新组件
        const existingComponent = this.relationshipGraph.components.get(componentId);
        
        if (existingComponent) {
          this.updateComponent(componentId, component);
        } else {
          this.registerComponent({
            id: componentId,
            type: component.type || 'unknown',
            element: component.element || null,
            containerId: component.containerId || null,
            parentId: component.parentId || null,
            position: component.position || { top: 0, left: 0, width: 0, height: 0 },
            visible: component.visible !== false,
            loaded: component.loaded !== false
          });
        }
      });
    }
  }

  /**
   * 获取容器ID
   */
  getContainerId(element) {
    // 查找最近的容器元素
    const container = element.closest('.container, .component-container');
    return container ? container.id : null;
  }

  /**
   * 查找父组件ID
   */
  findParentComponentId(element) {
    // 查找最近的组件元素
    const parentComponent = element.parentElement?.closest('[component], [data-component]');
    return parentComponent ? parentComponent.id : null;
  }

  /**
   * 获取组件位置信息
   */
  getComponentPosition(element) {
    if (!element) return { top: 0, left: 0, width: 0, height: 0 };
    
    const rect = element.getBoundingClientRect();
    return {
      top: rect.top,
      left: rect.left,
      width: rect.width,
      height: rect.height
    };
  }

  /**
   * 检测初始关系
   */
  detectInitialRelationships() {
    console.log('检测组件初始关系...');
    
    // 为每个组件检测关系
    this.relationshipGraph.components.forEach(component => {
      if (component.parentId) {
        // 建立父子关系
        this.addParentChildRelationship(component.parentId, component.id);
      }
      
      // 检测兄弟关系
      this.detectSiblingRelationships(component);
    });
  }

  /**
   * 检测兄弟关系
   */
  detectSiblingRelationships(component) {
    if (!component.element || !component.parentId) return;
    
    const parentComponent = this.relationshipGraph.components.get(component.parentId);
    if (!parentComponent || !parentComponent.element) return;
    
    // 查找同一父组件下的其他组件
    const siblingElements = parentComponent.element.querySelectorAll('[component], [data-component]');
    
    siblingElements.forEach(siblingElement => {
      const siblingId = siblingElement.id;
      
      if (siblingId && siblingId !== component.id) {
        // 检查是否已经添加了这种关系
        const relationships = this.relationshipGraph.relationships.get(component.id) || new Map();
        
        if (!relationships.has(siblingId)) {
          // 添加兄弟关系
          this.addRelationship(component.id, siblingId, 'sibling');
          this.addRelationship(siblingId, component.id, 'sibling');
        }
      }
    });
  }

  /**
   * 构建初始层级
   */
  buildInitialHierarchy() {
    console.log('构建初始组件层级...');
    
    // 使用广度优先搜索建立层级
    const visited = new Set();
    const queue = [];
    
    // 找出所有顶级组件（没有父组件的组件）
    this.relationshipGraph.components.forEach(component => {
      if (!component.parentId) {
        queue.push({ componentId: component.id, level: 0 });
        visited.add(component.id);
      }
    });
    
    // 广度优先遍历构建层级
    while (queue.length > 0) {
      const { componentId, level } = queue.shift();
      
      // 更新层级
      this.updateComponentLevel(componentId, level);
      
      // 添加子组件到队列
      const childComponents = this.getChildComponents(componentId);
      childComponents.forEach(childId => {
        if (!visited.has(childId)) {
          visited.add(childId);
          queue.push({ componentId: childId, level: level + 1 });
        }
      });
    }
    
    console.log('组件层级构建完成:', this.relationshipGraph.hierarchyLevels);
  }

  /**
   * 注册组件
   */
  registerComponent(componentInfo) {
    const { id, type, element, containerId, parentId, position, visible, loaded } = componentInfo;
    
    // 确保ID唯一
    if (this.relationshipGraph.components.has(id)) {
      console.warn(`组件ID ${id} 已存在，更新组件信息`);
      this.updateComponent(id, componentInfo);
      return;
    }
    
    // 注册组件
    this.relationshipGraph.components.set(id, {
      id,
      type,
      element,
      containerId,
      parentId,
      position,
      visible,
      loaded,
      level: -1, // 初始层级为-1
      children: new Set(),
      siblings: new Set(),
      dependsOn: new Set(),
      dependencies: new Set(),
      properties: {},
      createdAt: Date.now(),
      lastUpdated: Date.now()
    });
    
    // 初始化关系映射
    this.relationshipGraph.relationships.set(id, new Map());
    
    // 初始化依赖映射
    this.dependencyGraph.dependencies.set(id, new Set());
    this.dependencyGraph.dependents.set(id, new Set());
    
    console.log(`组件 ${id} (${type}) 已注册`);
    
    // 如果有父组件，建立关系
    if (parentId) {
      this.addParentChildRelationship(parentId, id);
    }
    
    return id;
  }

  /**
   * 更新组件信息
   */
  updateComponent(componentId, updateInfo) {
    const component = this.relationshipGraph.components.get(componentId);
    
    if (!component) {
      console.warn(`无法更新组件 ${componentId}: 组件不存在`);
      return false;
    }
    
    // 更新组件信息
    Object.assign(component, updateInfo, { lastUpdated: Date.now() });
    
    // 如果更新了父组件，更新关系
    if (updateInfo.parentId !== undefined) {
      // 移除旧的父子关系
      if (component.parentId && component.parentId !== updateInfo.parentId) {
        this.removeParentChildRelationship(component.parentId, componentId);
      }
      
      // 添加新的父子关系
      if (updateInfo.parentId) {
        this.addParentChildRelationship(updateInfo.parentId, componentId);
      }
    }
    
    // 清除分析缓存
    this.clearAnalysisCache(componentId);
    
    console.log(`组件 ${componentId} 已更新`);
    return true;
  }

  /**
   * 注销组件
   */
  unregisterComponent(componentId) {
    const component = this.relationshipGraph.components.get(componentId);
    
    if (!component) {
      console.warn(`无法注销组件 ${componentId}: 组件不存在`);
      return false;
    }
    
    // 移除所有关系
    this.removeAllRelationships(componentId);
    
    // 移除所有依赖
    this.removeAllDependencies(componentId);
    
    // 从层级中移除
    this.removeFromHierarchy(componentId);
    
    // 移除组件
    this.relationshipGraph.components.delete(componentId);
    this.relationshipGraph.relationships.delete(componentId);
    
    this.dependencyGraph.dependencies.delete(componentId);
    this.dependencyGraph.dependents.delete(componentId);
    
    // 从页面组件映射中移除
    this.removeFromPageComponents(componentId);
    
    // 清除缓存
    this.clearAnalysisCache(componentId);
    
    console.log(`组件 ${componentId} 已注销`);
    return true;
  }

  /**
   * 添加父子关系
   */
  addParentChildRelationship(parentId, childId) {
    const parentComponent = this.relationshipGraph.components.get(parentId);
    const childComponent = this.relationshipGraph.components.get(childId);
    
    if (!parentComponent || !childComponent) {
      console.warn(`无法添加父子关系: 父组件 ${parentId} 或子组件 ${childId} 不存在`);
      return false;
    }
    
    // 更新父组件的子组件列表
    parentComponent.children.add(childId);
    
    // 更新子组件的父组件ID
    childComponent.parentId = parentId;
    
    // 添加关系
    this.addRelationship(parentId, childId, 'parent');
    this.addRelationship(childId, parentId, 'child');
    
    // 更新层级
    const parentLevel = parentComponent.level;
    if (parentLevel >= 0) {
      this.updateComponentLevel(childId, parentLevel + 1);
    }
    
    console.log(`已添加父子关系: ${parentId} -> ${childId}`);
    
    // 清除缓存
    this.clearAnalysisCache(parentId, childId);
    
    return true;
  }

  /**
   * 移除父子关系
   */
  removeParentChildRelationship(parentId, childId) {
    const parentComponent = this.relationshipGraph.components.get(parentId);
    const childComponent = this.relationshipGraph.components.get(childId);
    
    if (!parentComponent || !childComponent) {
      console.warn(`无法移除父子关系: 父组件 ${parentId} 或子组件 ${childId} 不存在`);
      return false;
    }
    
    // 移除父组件的子组件列表
    parentComponent.children.delete(childId);
    
    // 移除子组件的父组件ID
    if (childComponent.parentId === parentId) {
      childComponent.parentId = null;
    }
    
    // 移除关系
    this.removeRelationship(parentId, childId, 'parent');
    this.removeRelationship(childId, parentId, 'child');
    
    // 重新计算层级
    this.recalculateComponentLevel(childId);
    
    console.log(`已移除父子关系: ${parentId} -> ${childId}`);
    
    // 清除缓存
    this.clearAnalysisCache(parentId, childId);
    
    return true;
  }

  /**
   * 添加关系
   */
  addRelationship(sourceId, targetId, relationshipType) {
    if (!this.relationshipGraph.relationships.has(sourceId)) {
      this.relationshipGraph.relationships.set(sourceId, new Map());
    }
    
    const relationships = this.relationshipGraph.relationships.get(sourceId);
    relationships.set(targetId, relationshipType);
    
    // 记录关系类型到组件信息
    const sourceComponent = this.relationshipGraph.components.get(sourceId);
    if (sourceComponent) {
      switch (relationshipType) {
        case 'child':
          sourceComponent.siblings.add(targetId);
          break;
        case 'sibling':
          sourceComponent.siblings.add(targetId);
          break;
      }
    }
  }

  /**
   * 移除关系
   */
  removeRelationship(sourceId, targetId, relationshipType) {
    if (!this.relationshipGraph.relationships.has(sourceId)) return;
    
    const relationships = this.relationshipGraph.relationships.get(sourceId);
    
    // 如果指定了关系类型，只移除特定类型的关系
    if (relationshipType) {
      const currentType = relationships.get(targetId);
      if (currentType === relationshipType) {
        relationships.delete(targetId);
      }
    } else {
      // 如果没有指定关系类型，移除所有关系
      relationships.delete(targetId);
    }
    
    // 从组件信息中移除
    const sourceComponent = this.relationshipGraph.components.get(sourceId);
    if (sourceComponent) {
      if (relationshipType === 'sibling' || relationshipType === 'child') {
        sourceComponent.siblings.delete(targetId);
      }
    }
  }

  /**
   * 移除所有关系
   */
  removeAllRelationships(componentId) {
    // 移除与其他组件的所有关系
    if (this.relationshipGraph.relationships.has(componentId)) {
      const relationships = this.relationshipGraph.relationships.get(componentId);
      
      relationships.forEach((relationshipType, targetId) => {
        this.removeRelationship(targetId, componentId, this.getInverseRelationship(relationshipType));
      });
      
      this.relationshipGraph.relationships.delete(componentId);
    }
  }

  /**
   * 获取反向关系类型
   */
  getInverseRelationship(relationshipType) {
    const inverseMap = {
      'parent': 'child',
      'child': 'parent',
      'sibling': 'sibling',
      'dependent': 'dependency'
    };
    
    return inverseMap[relationshipType] || relationshipType;
  }

  /**
   * 添加依赖关系
   */
  addDependency(dependentId, dependencyId) {
    const dependentComponent = this.relationshipGraph.components.get(dependentId);
    const dependencyComponent = this.relationshipGraph.components.get(dependencyId);
    
    if (!dependentComponent || !dependencyComponent) {
      console.warn(`无法添加依赖关系: 依赖组件 ${dependentId} 或被依赖组件 ${dependencyId} 不存在`);
      return false;
    }
    
    // 检查循环依赖
    if (this.config.dependencyValidation && this.wouldCreateCycle(dependentId, dependencyId)) {
      console.error(`检测到潜在的循环依赖: ${dependentId} -> ${dependencyId}`);
      return false;
    }
    
    // 更新依赖映射
    this.dependencyGraph.dependencies.get(dependentId).add(dependencyId);
    this.dependencyGraph.dependents.get(dependencyId).add(dependentId);
    
    // 更新组件信息
    dependentComponent.dependsOn.add(dependencyId);
    dependencyComponent.dependencies.add(dependentId);
    
    // 添加关系
    this.addRelationship(dependentId, dependencyId, 'dependency');
    this.addRelationship(dependencyId, dependentId, 'dependent');
    
    console.log(`已添加依赖关系: ${dependentId} 依赖于 ${dependencyId}`);
    
    // 清除缓存
    this.clearAnalysisCache(dependentId, dependencyId);
    
    return true;
  }

  /**
   * 移除依赖关系
   */
  removeDependency(dependentId, dependencyId) {
    // 移除依赖映射
    this.dependencyGraph.dependencies.get(dependentId).delete(dependencyId);
    this.dependencyGraph.dependents.get(dependencyId).delete(dependentId);
    
    // 更新组件信息
    const dependentComponent = this.relationshipGraph.components.get(dependentId);
    const dependencyComponent = this.relationshipGraph.components.get(dependencyId);
    
    if (dependentComponent) {
      dependentComponent.dependsOn.delete(dependencyId);
    }
    
    if (dependencyComponent) {
      dependencyComponent.dependencies.delete(dependentId);
    }
    
    // 移除关系
    this.removeRelationship(dependentId, dependencyId, 'dependency');
    this.removeRelationship(dependencyId, dependentId, 'dependent');
    
    console.log(`已移除依赖关系: ${dependentId} 不再依赖于 ${dependencyId}`);
    
    // 清除缓存
    this.clearAnalysisCache(dependentId, dependencyId);
    
    return true;
  }

  /**
   * 移除所有依赖
   */
  removeAllDependencies(componentId) {
    // 移除作为依赖者的关系
    const dependencies = Array.from(this.dependencyGraph.dependencies.get(componentId) || []);
    dependencies.forEach(dependencyId => {
      this.removeDependency(componentId, dependencyId);
    });
    
    // 移除作为被依赖者的关系
    const dependents = Array.from(this.dependencyGraph.dependents.get(componentId) || []);
    dependents.forEach(dependentId => {
      this.removeDependency(dependentId, componentId);
    });
  }

  /**
   * 检查是否会创建循环依赖
   */
  wouldCreateCycle(dependentId, dependencyId) {
    // 如果已经是同一组件，直接返回true
    if (dependentId === dependencyId) return true;
    
    // 使用深度优先搜索检查循环
    const visited = new Set();
    
    function dfs(currentId, targetId) {
      if (currentId === targetId) return true;
      if (visited.has(currentId)) return false;
      
      visited.add(currentId);
      
      const dependencies = Array.from((this.dependencyGraph.dependencies.get(currentId) || new Set()));
      for (const depId of dependencies) {
        if (dfs.call(this, depId, targetId)) return true;
      }
      
      return false;
    }
    
    // 检查从依赖组件到依赖者组件是否存在路径
    return dfs.call(this, dependencyId, dependentId);
  }

  /**
   * 更新组件层级
   */
  updateComponentLevel(componentId, level) {
    const component = this.relationshipGraph.components.get(componentId);
    
    if (!component) {
      console.warn(`无法更新组件 ${componentId} 的层级: 组件不存在`);
      return false;
    }
    
    // 检查层级是否超出最大深度
    if (level > this.config.maxHierarchyDepth) {
      console.warn(`组件 ${componentId} 的层级 ${level} 超出最大深度 ${this.config.maxHierarchyDepth}`);
      return false;
    }
    
    // 从旧层级中移除
    if (component.level >= 0) {
      this.removeFromLevel(componentId, component.level);
    }
    
    // 更新层级
    component.level = level;
    
    // 添加到新层级
    this.addToLevel(componentId, level);
    
    // 更新子组件的层级
    this.updateChildComponentLevels(componentId);
    
    return true;
  }

  /**
   * 重新计算组件层级
   */
  recalculateComponentLevel(componentId) {
    const component = this.relationshipGraph.components.get(componentId);
    
    if (!component) return false;
    
    let newLevel = -1;
    
    if (component.parentId) {
      const parentComponent = this.relationshipGraph.components.get(component.parentId);
      if (parentComponent && parentComponent.level >= 0) {
        newLevel = parentComponent.level + 1;
      }
    }
    
    // 如果没有父组件或父组件没有层级，检查是否有依赖关系可以推断层级
    if (newLevel === -1 && component.dependsOn.size > 0) {
      // 从依赖组件推断层级
      let maxDependencyLevel = -1;
      
      component.dependsOn.forEach(dependencyId => {
        const dependencyComponent = this.relationshipGraph.components.get(dependencyId);
        if (dependencyComponent && dependencyComponent.level > maxDependencyLevel) {
          maxDependencyLevel = dependencyComponent.level;
        }
      });
      
      if (maxDependencyLevel >= 0) {
        newLevel = maxDependencyLevel + 1;
      }
    }
    
    // 更新层级
    this.updateComponentLevel(componentId, newLevel);
    
    return true;
  }

  /**
   * 更新子组件的层级
   */
  updateChildComponentLevels(parentId) {
    const parentComponent = this.relationshipGraph.components.get(parentId);
    
    if (!parentComponent || parentComponent.level < 0) return;
    
    const childLevel = parentComponent.level + 1;
    
    parentComponent.children.forEach(childId => {
      const childComponent = this.relationshipGraph.components.get(childId);
      if (childComponent && childComponent.level !== childLevel) {
        this.updateComponentLevel(childId, childLevel);
      }
    });
  }

  /**
   * 添加到层级
   */
  addToLevel(componentId, level) {
    if (!this.relationshipGraph.hierarchyLevels.has(level)) {
      this.relationshipGraph.hierarchyLevels.set(level, new Set());
    }
    
    this.relationshipGraph.hierarchyLevels.get(level).add(componentId);
  }

  /**
   * 从层级中移除
   */
  removeFromLevel(componentId, level) {
    if (this.relationshipGraph.hierarchyLevels.has(level)) {
      this.relationshipGraph.hierarchyLevels.get(level).delete(componentId);
      
      // 如果层级为空，删除层级
      if (this.relationshipGraph.hierarchyLevels.get(level).size === 0) {
        this.relationshipGraph.hierarchyLevels.delete(level);
      }
    }
  }

  /**
   * 从层级中移除组件
   */
  removeFromHierarchy(componentId) {
    const component = this.relationshipGraph.components.get(componentId);
    
    if (!component || component.level < 0) return;
    
    this.removeFromLevel(componentId, component.level);
    component.level = -1;
  }

  /**
   * 添加页面组件映射
   */
  addPageComponent(pageId, componentId) {
    if (!this.pageComponents.has(pageId)) {
      this.pageComponents.set(pageId, new Set());
    }
    
    this.pageComponents.get(pageId).add(componentId);
    console.log(`已将组件 ${componentId} 添加到页面 ${pageId}`);
  }

  /**
   * 从页面组件映射中移除
   */
  removeFromPageComponents(componentId) {
    this.pageComponents.forEach((components, pageId) => {
      if (components.has(componentId)) {
        components.delete(componentId);
        console.log(`已从页面 ${pageId} 移除组件 ${componentId}`);
      }
    });
  }

  /**
   * 获取组件
   */
  getComponent(componentId) {
    return this.relationshipGraph.components.get(componentId) || null;
  }

  /**
   * 获取所有组件
   */
  getAllComponents() {
    return Array.from(this.relationshipGraph.components.values());
  }

  /**
   * 获取父组件
   */
  getParentComponent(componentId) {
    const component = this.relationshipGraph.components.get(componentId);
    
    if (!component || !component.parentId) {
      return null;
    }
    
    return this.relationshipGraph.components.get(component.parentId) || null;
  }

  /**
   * 获取子组件
   */
  getChildComponents(componentId) {
    const component = this.relationshipGraph.components.get(componentId);
    
    if (!component) {
      return [];
    }
    
    return Array.from(component.children);
  }

  /**
   * 获取兄弟组件
   */
  getSiblingComponents(componentId) {
    const component = this.relationshipGraph.components.get(componentId);
    
    if (!component || !component.parentId) {
      return [];
    }
    
    const parentComponent = this.relationshipGraph.components.get(component.parentId);
    if (!parentComponent) {
      return [];
    }
    
    // 返回除了自己之外的所有子组件
    return Array.from(parentComponent.children).filter(id => id !== componentId);
  }

  /**
   * 获取依赖组件
   */
  getDependencies(componentId) {
    const component = this.relationshipGraph.components.get(componentId);
    
    if (!component) {
      return [];
    }
    
    return Array.from(component.dependsOn);
  }

  /**
   * 获取依赖于该组件的组件
   */
  getDependents(componentId) {
    const component = this.relationshipGraph.components.get(componentId);
    
    if (!component) {
      return [];
    }
    
    return Array.from(component.dependencies);
  }

  /**
   * 获取指定层级的组件
   */
  getComponentsByLevel(level) {
    if (!this.relationshipGraph.hierarchyLevels.has(level)) {
      return [];
    }
    
    return Array.from(this.relationshipGraph.hierarchyLevels.get(level));
  }

  /**
   * 获取页面的组件
   */
  getPageComponents(pageId) {
    if (!this.pageComponents.has(pageId)) {
      return [];
    }
    
    return Array.from(this.pageComponents.get(pageId));
  }

  /**
   * 获取组件的所有后代
   */
  getAllDescendants(componentId) {
    const descendants = [];
    const queue = [componentId];
    
    while (queue.length > 0) {
      const currentId = queue.shift();
      const childIds = this.getChildComponents(currentId);
      
      childIds.forEach(childId => {
        descendants.push(childId);
        queue.push(childId);
      });
    }
    
    return descendants;
  }

  /**
   * 获取组件的所有祖先
   */
  getAllAncestors(componentId) {
    const ancestors = [];
    let currentId = componentId;
    
    while (true) {
      const component = this.relationshipGraph.components.get(currentId);
      if (!component || !component.parentId) {
        break;
      }
      
      ancestors.push(component.parentId);
      currentId = component.parentId;
    }
    
    return ancestors;
  }

  /**
   * 分析组件关系
   */
  analyzeComponentRelationships(componentId) {
    // 检查缓存
    const cacheKey = `analysis_${componentId}`;
    if (this.analysisCache.has(cacheKey)) {
      return this.analysisCache.get(cacheKey);
    }
    
    const component = this.relationshipGraph.components.get(componentId);
    if (!component) {
      return null;
    }
    
    // 构建关系分析
    const analysis = {
      componentId,
      componentType: component.type,
      hierarchyLevel: component.level,
      parentId: component.parentId,
      childCount: component.children.size,
      siblingCount: component.siblings.size,
      dependencyCount: component.dependsOn.size,
      dependentCount: component.dependencies.size,
      descendantsCount: this.getAllDescendants(componentId).length,
      ancestorsCount: this.getAllAncestors(componentId).length,
      isTopLevel: component.parentId === null,
      isLeaf: component.children.size === 0,
      hasDependencies: component.dependsOn.size > 0,
      hasDependents: component.dependencies.size > 0,
      relationships: this.getComponentRelationships(componentId),
      createdAt: component.createdAt,
      lastUpdated: component.lastUpdated,
      analysisTime: Date.now()
    };
    
    // 缓存结果
    this.analysisCache.set(cacheKey, analysis);
    
    return analysis;
  }

  /**
   * 获取组件关系
   */
  getComponentRelationships(componentId) {
    const relationships = this.relationshipGraph.relationships.get(componentId) || new Map();
    
    const result = {};
    
    relationships.forEach((relationshipType, targetId) => {
      if (!result[relationshipType]) {
        result[relationshipType] = [];
      }
      
      result[relationshipType].push(targetId);
    });
    
    return result;
  }

  /**
   * 分析层级结构
   */
  analyzeHierarchy() {
    // 检查缓存
    const cacheKey = 'hierarchy_analysis';
    if (this.analysisCache.has(cacheKey)) {
      return this.analysisCache.get(cacheKey);
    }
    
    const analysis = {
      totalComponents: this.relationshipGraph.components.size,
      hierarchyDepth: this.getHierarchyDepth(),
      componentsByLevel: {},
      orphanedComponents: this.findOrphanedComponents(),
      topLevelComponents: this.findTopLevelComponents(),
      leafComponents: this.findLeafComponents(),
      componentsWithCircularDependencies: this.findCircularDependencies(),
      componentTypes: this.getComponentTypes(),
      analysisTime: Date.now()
    };
    
    // 获取各级别的组件数量
    this.relationshipGraph.hierarchyLevels.forEach((components, level) => {
      analysis.componentsByLevel[level] = components.size;
    });
    
    // 缓存结果
    this.analysisCache.set(cacheKey, analysis);
    
    return analysis;
  }

  /**
   * 获取层级深度
   */
  getHierarchyDepth() {
    let maxDepth = 0;
    
    this.relationshipGraph.hierarchyLevels.forEach((components, level) => {
      if (level > maxDepth) {
        maxDepth = level;
      }
    });
    
    return maxDepth + 1; // +1 是因为层级从0开始
  }

  /**
   * 查找孤立组件（没有父组件也没有子组件的组件）
   */
  findOrphanedComponents() {
    const orphans = [];
    
    this.relationshipGraph.components.forEach(component => {
      if (component.parentId === null && component.children.size === 0) {
        orphans.push(component.id);
      }
    });
    
    return orphans;
  }

  /**
   * 查找顶级组件（没有父组件的组件）
   */
  findTopLevelComponents() {
    const topLevel = [];
    
    this.relationshipGraph.components.forEach(component => {
      if (component.parentId === null) {
        topLevel.push(component.id);
      }
    });
    
    return topLevel;
  }

  /**
   * 查找叶子组件（没有子组件的组件）
   */
  findLeafComponents() {
    const leaves = [];
    
    this.relationshipGraph.components.forEach(component => {
      if (component.children.size === 0) {
        leaves.push(component.id);
      }
    });
    
    return leaves;
  }

  /**
   * 查找循环依赖
   */
  findCircularDependencies() {
    const circular = [];
    const visited = new Set();
    const recStack = new Set();
    const path = [];
    
    function dfs(currentId, startId) {
      if (!visited.has(currentId)) {
        visited.add(currentId);
        recStack.add(currentId);
        path.push(currentId);
        
        const dependencies = Array.from((this.dependencyGraph.dependencies.get(currentId) || new Set()));
        
        for (const dependencyId of dependencies) {
          if (dependencyId === startId) {
            // 找到循环依赖
            const cycleStartIndex = path.indexOf(startId);
            if (cycleStartIndex !== -1) {
              const cycle = path.slice(cycleStartIndex);
              circular.push([...cycle, startId]);
            }
          } else if (!visited.has(dependencyId) && dfs.call(this, dependencyId, startId)) {
            return true;
          } else if (recStack.has(dependencyId)) {
            // 找到循环依赖
            const cycleStartIndex = path.indexOf(dependencyId);
            if (cycleStartIndex !== -1) {
              const cycle = path.slice(cycleStartIndex);
              circular.push([...cycle, dependencyId]);
            }
          }
        }
      }
      
      recStack.delete(currentId);
      path.pop();
      return false;
    }
    
    // 对每个组件执行DFS
    this.relationshipGraph.components.forEach(component => {
      if (!visited.has(component.id)) {
        dfs.call(this, component.id, component.id);
      }
    });
    
    return circular;
  }

  /**
   * 获取组件类型统计
   */
  getComponentTypes() {
    const typeCount = {};
    
    this.relationshipGraph.components.forEach(component => {
      const type = component.type;
      if (!typeCount[type]) {
        typeCount[type] = 0;
      }
      typeCount[type]++;
    });
    
    return typeCount;
  }

  /**
   * 生成优化建议
   */
  generateOptimizationSuggestions() {
    const suggestions = [];
    const hierarchyAnalysis = this.analyzeHierarchy();
    
    // 分析层级深度
    if (hierarchyAnalysis.hierarchyDepth > this.config.maxHierarchyDepth * 0.8) {
      suggestions.push({
        type: 'hierarchy',
        severity: 'warning',
        message: `层级深度 ${hierarchyAnalysis.hierarchyDepth} 接近最大限制 ${this.config.maxHierarchyDepth}，建议考虑重构减少嵌套层级`,
        affectedComponents: hierarchyAnalysis.topLevelComponents.slice(0, 5)
      });
    }
    
    // 分析循环依赖
    if (hierarchyAnalysis.componentsWithCircularDependencies.length > 0) {
      suggestions.push({
        type: 'dependency',
        severity: 'error',
        message: `发现 ${hierarchyAnalysis.componentsWithCircularDependencies.length} 个循环依赖，这可能导致渲染和更新问题`,
        affectedComponents: hierarchyAnalysis.componentsWithCircularDependencies.flat().slice(0, 10)
      });
    }
    
    // 分析孤立组件
    if (hierarchyAnalysis.orphanedComponents.length > 0) {
      suggestions.push({
        type: 'relationship',
        severity: 'info',
        message: `发现 ${hierarchyAnalysis.orphanedComponents.length} 个孤立组件，这些组件可能需要重组或删除`,
        affectedComponents: hierarchyAnalysis.orphanedComponents.slice(0, 5)
      });
    }
    
    // 分析组件依赖数量
    this.relationshipGraph.components.forEach(component => {
      if (component.dependsOn.size > 10) {
        suggestions.push({
          type: 'dependency',
          severity: 'warning',
          message: `组件 ${component.id} (${component.type}) 依赖了 ${component.dependsOn.size} 个其他组件，这可能导致性能问题和难以维护`,
          affectedComponents: [component.id]
        });
      }
      
      if (component.dependencies.size > 20) {
        suggestions.push({
          type: 'dependency',
          severity: 'warning',
          message: `组件 ${component.id} (${component.type}) 被 ${component.dependencies.size} 个其他组件依赖，这可能导致紧耦合`,
          affectedComponents: [component.id]
        });
      }
    });
    
    return suggestions;
  }

  /**
   * 获取组件加载顺序
   */
  getComponentLoadOrder(componentIds = null) {
    // 如果没有指定组件，使用所有组件
    if (!componentIds) {
      componentIds = Array.from(this.relationshipGraph.components.keys());
    }
    
    const orderedComponents = [];
    const visited = new Set();
    const tempVisited = new Set();
    
    function visit(componentId) {
      // 检测循环依赖
      if (tempVisited.has(componentId)) {
        throw new Error(`检测到循环依赖: ${componentId} 可能参与了循环依赖`);
      }
      
      if (!visited.has(componentId)) {
        tempVisited.add(componentId);
        
        // 先访问所有依赖
        const dependencies = this.getDependencies(componentId);
        dependencies.forEach(depId => {
          if (componentIds.includes(depId)) {
            visit.call(this, depId);
          }
        });
        
        // 再访问组件本身
        tempVisited.delete(componentId);
        visited.add(componentId);
        orderedComponents.push(componentId);
      }
    }
    
    // 对每个组件执行访问
    componentIds.forEach(componentId => {
      if (!visited.has(componentId)) {
        visit.call(this, componentId);
      }
    });
    
    return orderedComponents;
  }

  /**
   * 导出关系图
   */
  exportRelationshipGraph() {
    const graph = {
      components: {},
      relationships: {},
      dependencies: {},
      hierarchy: {}
    };
    
    // 导出组件信息
    this.relationshipGraph.components.forEach(component => {
      graph.components[component.id] = {
        type: component.type,
        parentId: component.parentId,
        level: component.level,
        visible: component.visible,
        loaded: component.loaded
      };
    });
    
    // 导出关系
    this.relationshipGraph.relationships.forEach((targets, sourceId) => {
      graph.relationships[sourceId] = {};
      targets.forEach((relationshipType, targetId) => {
        graph.relationships[sourceId][targetId] = relationshipType;
      });
    });
    
    // 导出依赖
    this.dependencyGraph.dependencies.forEach((dependencies, componentId) => {
      graph.dependencies[componentId] = Array.from(dependencies);
    });
    
    // 导出层级
    this.relationshipGraph.hierarchyLevels.forEach((components, level) => {
      graph.hierarchy[level] = Array.from(components);
    });
    
    return graph;
  }

  /**
   * 导入关系图
   */
  importRelationshipGraph(graph) {
    // 重置当前状态
    this.reset();
    
    // 导入组件
    if (graph.components) {
      Object.entries(graph.components).forEach(([componentId, componentInfo]) => {
        this.registerComponent({
          id: componentId,
          type: componentInfo.type || 'unknown',
          parentId: componentInfo.parentId || null,
          visible: componentInfo.visible !== false,
          loaded: componentInfo.loaded !== false,
          level: componentInfo.level || -1
        });
      });
    }
    
    // 导入关系
    if (graph.relationships) {
      Object.entries(graph.relationships).forEach(([sourceId, targets]) => {
        Object.entries(targets).forEach(([targetId, relationshipType]) => {
          this.addRelationship(sourceId, targetId, relationshipType);
        });
      });
    }
    
    // 导入依赖
    if (graph.dependencies) {
      Object.entries(graph.dependencies).forEach(([dependentId, dependencies]) => {
        dependencies.forEach(dependencyId => {
          this.addDependency(dependentId, dependencyId);
        });
      });
    }
    
    // 导入层级
    if (graph.hierarchy) {
      Object.entries(graph.hierarchy).forEach(([level, components]) => {
        components.forEach(componentId => {
          this.addToLevel(componentId, parseInt(level, 10));
          
          // 更新组件层级
          const component = this.relationshipGraph.components.get(componentId);
          if (component) {
            component.level = parseInt(level, 10);
          }
        });
      });
    }
    
    console.log('关系图导入完成');
    return true;
  }

  /**
   * 清除分析缓存
   */
  clearAnalysisCache(...componentIds) {
    // 如果指定了组件ID，只清除相关缓存
    if (componentIds.length > 0) {
      componentIds.forEach(componentId => {
        const cacheKey = `analysis_${componentId}`;
        this.analysisCache.delete(cacheKey);
      });
    } else {
      // 否则清除所有缓存
      this.analysisCache.clear();
    }
    
    // 清除层级分析缓存
    this.analysisCache.delete('hierarchy_analysis');
  }

  /**
   * 更新配置
   */
  updateConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };
    console.log('配置已更新:', this.config);
    
    // 如果更新了最大层级深度，可能需要重新计算层级
    if (newConfig.maxHierarchyDepth !== undefined) {
      this.validateHierarchyDepth();
    }
    
    // 清除缓存
    this.clearAnalysisCache();
  }

  /**
   * 验证层级深度
   */
  validateHierarchyDepth() {
    const maxDepth = this.config.maxHierarchyDepth;
    
    this.relationshipGraph.components.forEach(component => {
      if (component.level > maxDepth) {
        console.warn(`组件 ${component.id} 的层级 ${component.level} 超出最大深度 ${maxDepth}`);
        // 可以选择自动调整层级，或者只是记录警告
      }
    });
  }

  /**
   * 重置管理器
   */
  reset() {
    this.relationshipGraph = {
      components: new Map(),
      relationships: new Map(),
      hierarchyLevels: new Map()
    };
    
    this.dependencyGraph = {
      dependencies: new Map(),
      dependents: new Map()
    };
    
    this.pageComponents = new Map();
    this.analysisCache = new Map();
    
    this.isInitialized = false;
    
    console.log('层级关系管理器已重置');
  }

  /**
   * 获取状态
   */
  getStatus() {
    return {
      isInitialized: this.isInitialized,
      componentCount: this.relationshipGraph.components.size,
      hierarchyDepth: this.getHierarchyDepth(),
      circularDependencies: this.findCircularDependencies().length,
      config: { ...this.config }
    };
  }
}

// 创建层级关系管理器实例
const hierarchyManager = new HierarchyRelationshipManager();

// 导出
if (typeof window !== 'undefined') {
  window.HierarchyRelationshipManager = HierarchyRelationshipManager;
  window.hierarchyManager = hierarchyManager;
}

export { HierarchyRelationshipManager, hierarchyManager };