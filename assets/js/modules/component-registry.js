// 组件注册中心 - 管理组件类型和实例，支持动态组件加载
class ComponentRegistry {
  constructor() {
    // 组件类型映射表
    this.componentTypes = new Map();
    
    // 组件实例缓存
    this.componentInstances = new Map();
    
    // 组件工厂函数
    this.componentFactories = new Map();
    
    // 异步加载队列
    this.loadingComponents = new Map();
    
    // 组件别名映射
    this.componentAliases = new Map();
    
    // 组件生命周期钩子注册器
    this.lifecycleHooks = {
      beforeRegister: [],
      afterRegister: [],
      beforeUnregister: [],
      afterUnregister: [],
      beforeInstantiate: [],
      afterInstantiate: []
    };
    
    // 错误处理器
    this.errorHandlers = [];
    
    // 默认组件
    this.defaultComponent = null;
    
    // 初始化状态
    this.isInitialized = false;
  }

  /**
   * 初始化组件注册中心
   */
  initialize() {
    if (this.isInitialized) {
      console.warn('组件注册中心已经初始化');
      return true;
    }
    
    try {
      console.log('初始化组件注册中心...');
      
      // 注册默认组件
      this.registerDefaultComponent();
      
      // 注册内置组件
      this.registerBuiltinComponents();
      
      // 加载组件配置
      this.loadComponentConfig();
      
      this.isInitialized = true;
      console.log('组件注册中心初始化完成');
      
      return true;
    } catch (error) {
      console.error('初始化组件注册中心失败:', error);
      this.handleError(error);
      return false;
    }
  }

  /**
   * 注册默认组件
   */
  registerDefaultComponent() {
    // 默认通用组件类
    class DefaultComponent {
      constructor(id, options = {}) {
        this.id = id;
        this.options = options;
        this.element = null;
        this.state = {};
        this.props = {};
      }

      async render(container, data = {}) {
        console.log(`渲染默认组件: ${this.id}`);
        
        // 创建组件元素
        this.element = document.createElement('div');
        this.element.className = `default-component ${this.id}`;
        this.element.setAttribute('data-component-id', this.id);
        
        // 设置基本内容
        this.element.innerHTML = `
          <div class="component-header">
            <h3>${this.id}</h3>
            <small>${this.options.type || 'default'}</small>
          </div>
          <div class="component-content">
            <p>这是默认组件渲染占位</p>
            ${this.options.html || ''}
          </div>
        `;
        
        // 添加自定义样式
        if (this.options.styles) {
          const style = document.createElement('style');
          style.textContent = this.options.styles;
          this.element.appendChild(style);
        }
        
        // 清空容器并添加元素
        container.appendChild(this.element);
        
        // 触发渲染完成事件
        this.emit('rendered', { container, data });
      }

      update(updates = {}) {
        console.log(`更新默认组件: ${this.id}`);
        
        // 合并更新选项
        this.options = { ...this.options, ...updates };
        
        // 重新渲染
        if (this.element && this.element.parentNode) {
          this.render(this.element.parentNode, this.options);
        }
      }

      destroy() {
        console.log(`销毁默认组件: ${this.id}`);
        
        // 移除元素
        if (this.element && this.element.parentNode) {
          this.element.parentNode.removeChild(this.element);
        }
        
        // 清理资源
        this.element = null;
        this.state = {};
        this.props = {};
      }

      setState(newState) {
        this.state = { ...this.state, ...newState };
        this.update();
      }

      setProps(newProps) {
        this.props = { ...this.props, ...newProps };
        this.update();
      }

      emit(event, data) {
        // 简单的事件发射
        if (this.options && this.options.on && typeof this.options.on === 'object') {
          const handler = this.options.on[event];
          if (typeof handler === 'function') {
            handler(data);
          }
        }
      }

      on(event, callback) {
        // 简单的事件监听
        if (!this.eventHandlers) {
          this.eventHandlers = {};
        }
        
        if (!this.eventHandlers[event]) {
          this.eventHandlers[event] = [];
        }
        
        this.eventHandlers[event].push(callback);
      }

      off(event, callback) {
        if (!this.eventHandlers || !this.eventHandlers[event]) {
          return;
        }
        
        this.eventHandlers[event] = this.eventHandlers[event].filter(cb => cb !== callback);
      }
    }
    
    this.defaultComponent = DefaultComponent;
    this.registerComponent('default', DefaultComponent);
  }

  /**
   * 注册内置组件
   */
  registerBuiltinComponents() {
    // 注册一些基础内置组件
    
    // 按钮组件
    class ButtonComponent extends this.defaultComponent {
      render(container, data = {}) {
        const { text = 'Button', variant = 'default', size = 'medium', disabled = false } = data;
        
        this.element = document.createElement('button');
        this.element.className = `button-component ${this.id} btn btn-${variant} btn-${size}`;
        this.element.setAttribute('data-component-id', this.id);
        this.element.disabled = disabled;
        this.element.textContent = text;
        
        // 添加点击事件
        if (data.onClick) {
          this.element.addEventListener('click', data.onClick);
        }
        
        container.appendChild(this.element);
      }
      
      destroy() {
        super.destroy();
        // 清理事件监听器
        if (this.element) {
          this.element.removeEventListener('click', this.options.onClick);
        }
      }
    }
    
    // 卡片组件
    class CardComponent extends this.defaultComponent {
      render(container, data = {}) {
        const { title, content, footer, noPadding = false } = data;
        
        this.element = document.createElement('div');
        this.element.className = `card-component ${this.id} card ${noPadding ? 'card-no-padding' : ''}`;
        this.element.setAttribute('data-component-id', this.id);
        
        // 构建卡片结构
        let cardHtml = '';
        
        if (title) {
          cardHtml += `<div class="card-header">${title}</div>`;
        }
        
        if (content) {
          cardHtml += `<div class="card-body">${content}</div>`;
        }
        
        if (footer) {
          cardHtml += `<div class="card-footer">${footer}</div>`;
        }
        
        this.element.innerHTML = cardHtml;
        container.appendChild(this.element);
      }
    }
    
    // 面板组件
    class PanelComponent extends this.defaultComponent {
      render(container, data = {}) {
        const { title, collapsible = false, collapsed = false } = data;
        
        this.element = document.createElement('div');
        this.element.className = `panel-component ${this.id} panel ${collapsed ? 'panel-collapsed' : ''}`;
        this.element.setAttribute('data-component-id', this.id);
        
        // 构建面板结构
        let panelHtml = '';
        
        if (title) {
          panelHtml += `
            <div class="panel-header">
              <h3>${title}</h3>
              ${collapsible ? '<button class="panel-toggle">▼</button>' : ''}
            </div>
          `;
        }
        
        panelHtml += `<div class="panel-body">${data.content || ''}</div>`;
        
        this.element.innerHTML = panelHtml;
        container.appendChild(this.element);
        
        // 添加折叠功能
        if (collapsible) {
          const toggleBtn = this.element.querySelector('.panel-toggle');
          const panelBody = this.element.querySelector('.panel-body');
          
          if (toggleBtn && panelBody) {
            toggleBtn.addEventListener('click', () => {
              this.element.classList.toggle('panel-collapsed');
              panelBody.style.display = this.element.classList.contains('panel-collapsed') ? 'none' : 'block';
              toggleBtn.textContent = this.element.classList.contains('panel-collapsed') ? '▶' : '▼';
            });
            
            // 初始状态
            if (collapsed) {
              panelBody.style.display = 'none';
              toggleBtn.textContent = '▶';
            }
          }
        }
      }
    }
    
    // 注册这些内置组件
    this.registerComponent('button', ButtonComponent);
    this.registerComponent('card', CardComponent);
    this.registerComponent('panel', PanelComponent);
    
    console.log('内置组件注册完成');
  }

  /**
   * 加载组件配置
   */
  loadComponentConfig() {
    // 尝试加载组件配置文件
    try {
      if (window && window.componentConfig) {
        const config = window.componentConfig;
        
        // 注册组件别名
        if (config.aliases) {
          Object.entries(config.aliases).forEach(([alias, componentType]) => {
            this.registerAlias(alias, componentType);
          });
        }
        
        // 预注册组件
        if (config.components) {
          // 这里可以根据配置预注册组件
        }
      }
    } catch (error) {
      console.warn('加载组件配置失败:', error);
    }
  }

  /**
   * 注册组件
   */
  registerComponent(type, componentClass) {
    try {
      // 触发注册前钩子
      this.triggerHook('beforeRegister', { type, componentClass });
      
      // 验证组件类
      if (!this.isValidComponentClass(componentClass)) {
        throw new Error(`无效的组件类: ${type}`);
      }
      
      // 检查是否已注册
      const isUpdating = this.componentTypes.has(type);
      
      // 注册组件类型
      this.componentTypes.set(type, componentClass);
      
      // 清除相关实例缓存
      this.clearInstanceCache(type);
      
      // 触发注册后钩子
      this.triggerHook('afterRegister', { type, componentClass, isUpdating });
      
      console.log(`组件注册成功: ${type}${isUpdating ? ' (更新)' : ''}`);
      
      return true;
    } catch (error) {
      console.error(`注册组件失败: ${type}`, error);
      this.handleError(error);
      return false;
    }
  }

  /**
   * 验证组件类
   */
  isValidComponentClass(componentClass) {
    // 基本验证：必须是函数或类
    if (typeof componentClass !== 'function') {
      return false;
    }
    
    // 检查是否有必要的方法
    const prototype = componentClass.prototype;
    
    // 至少需要render方法
    return typeof prototype.render === 'function';
  }

  /**
   * 注销组件
   */
  unregisterComponent(type) {
    try {
      // 检查组件是否存在
      if (!this.componentTypes.has(type)) {
        console.warn(`要注销的组件不存在: ${type}`);
        return false;
      }
      
      // 触发注销前钩子
      this.triggerHook('beforeUnregister', { type });
      
      // 获取组件类（用于事件传递）
      const componentClass = this.componentTypes.get(type);
      
      // 移除组件类型
      this.componentTypes.delete(type);
      
      // 移除相关别名
      this.removeAliasesForType(type);
      
      // 清理所有实例
      this.clearInstanceCache(type);
      
      // 触发注销后钩子
      this.triggerHook('afterUnregister', { type, componentClass });
      
      console.log(`组件注销成功: ${type}`);
      
      return true;
    } catch (error) {
      console.error(`注销组件失败: ${type}`, error);
      this.handleError(error);
      return false;
    }
  }

  /**
   * 注册组件别名
   */
  registerAlias(alias, componentType) {
    try {
      // 存储别名映射
      this.componentAliases.set(alias, componentType);
      
      console.log(`组件别名注册成功: ${alias} -> ${componentType}`);
      
      return true;
    } catch (error) {
      console.error(`注册组件别名失败: ${alias} -> ${componentType}`, error);
      return false;
    }
  }

  /**
   * 移除组件别名
   */
  removeAlias(alias) {
    try {
      this.componentAliases.delete(alias);
      console.log(`组件别名移除成功: ${alias}`);
      return true;
    } catch (error) {
      console.error(`移除组件别名失败: ${alias}`, error);
      return false;
    }
  }

  /**
   * 移除指定类型的所有别名
   */
  removeAliasesForType(componentType) {
    try {
      const aliasesToRemove = [];
      
      // 找出所有映射到该类型的别名
      this.componentAliases.forEach((type, alias) => {
        if (type === componentType) {
          aliasesToRemove.push(alias);
        }
      });
      
      // 移除这些别名
      aliasesToRemove.forEach(alias => {
        this.componentAliases.delete(alias);
      });
      
      if (aliasesToRemove.length > 0) {
        console.log(`移除了 ${aliasesToRemove.length} 个组件别名`);
      }
      
      return true;
    } catch (error) {
      console.error(`移除组件别名失败`, error);
      return false;
    }
  }

  /**
   * 获取组件类
   */
  getComponent(type) {
    // 首先尝试直接获取
    let componentClass = this.componentTypes.get(type);
    
    // 如果找不到，尝试通过别名查找
    if (!componentClass) {
      const actualType = this.componentAliases.get(type);
      if (actualType) {
        componentClass = this.componentTypes.get(actualType);
      }
    }
    
    // 如果还是找不到，返回默认组件
    if (!componentClass && this.defaultComponent) {
      console.warn(`使用默认组件替代不存在的组件类型: ${type}`);
      componentClass = this.defaultComponent;
    }
    
    return componentClass;
  }

  /**
   * 创建组件实例
   */
  createInstance(componentId, type, options = {}) {
    try {
      // 触发实例化前钩子
      this.triggerHook('beforeInstantiate', { componentId, type, options });
      
      // 获取组件类
      const componentClass = this.getComponent(type);
      
      if (!componentClass) {
        throw new Error(`无法获取组件类: ${type}`);
      }
      
      // 创建实例
      const instance = new componentClass(componentId, options);
      
      // 注入组件信息
      instance.componentType = type;
      instance.registry = this;
      
      // 保存实例
      this.cacheInstance(componentId, instance);
      
      // 触发实例化后钩子
      this.triggerHook('afterInstantiate', { componentId, type, instance, options });
      
      console.log(`组件实例创建成功: ${componentId} (${type})`);
      
      return instance;
    } catch (error) {
      console.error(`创建组件实例失败: ${componentId} (${type})`, error);
      this.handleError(error);
      
      // 尝试返回默认组件实例作为后备
      if (this.defaultComponent) {
        try {
          const fallbackInstance = new this.defaultComponent(componentId, { ...options, error: error.message });
          this.cacheInstance(componentId, fallbackInstance);
          return fallbackInstance;
        } catch (fallbackError) {
          console.error('创建后备组件实例也失败了:', fallbackError);
        }
      }
      
      return null;
    }
  }

  /**
   * 获取组件实例
   */
  getInstance(componentId) {
    return this.componentInstances.get(componentId);
  }

  /**
   * 缓存组件实例
   */
  cacheInstance(componentId, instance) {
    this.componentInstances.set(componentId, instance);
  }

  /**
   * 清除实例缓存
   */
  clearInstanceCache(type) {
    if (type) {
      // 只清除特定类型的实例
      const instancesToRemove = [];
      
      this.componentInstances.forEach((instance, id) => {
        if (instance.componentType === type) {
          instancesToRemove.push(id);
        }
      });
      
      instancesToRemove.forEach(id => {
        this.componentInstances.delete(id);
      });
      
      console.log(`清除了 ${instancesToRemove.length} 个 ${type} 类型的组件实例缓存`);
    } else {
      // 清除所有实例缓存
      const count = this.componentInstances.size;
      this.componentInstances.clear();
      console.log(`清除了所有 ${count} 个组件实例缓存`);
    }
  }

  /**
   * 销毁组件实例
   */
  destroyInstance(componentId) {
    try {
      const instance = this.componentInstances.get(componentId);
      
      if (!instance) {
        console.warn(`要销毁的组件实例不存在: ${componentId}`);
        return false;
      }
      
      // 调用实例的destroy方法
      if (typeof instance.destroy === 'function') {
        instance.destroy();
      }
      
      // 从缓存中移除
      this.componentInstances.delete(componentId);
      
      console.log(`组件实例销毁成功: ${componentId}`);
      
      return true;
    } catch (error) {
      console.error(`销毁组件实例失败: ${componentId}`, error);
      this.handleError(error);
      return false;
    }
  }

  /**
   * 注册组件工厂函数
   */
  registerFactory(type, factoryFunction) {
    try {
      if (typeof factoryFunction !== 'function') {
        throw new Error('工厂函数必须是函数类型');
      }
      
      this.componentFactories.set(type, factoryFunction);
      console.log(`组件工厂注册成功: ${type}`);
      
      return true;
    } catch (error) {
      console.error(`注册组件工厂失败: ${type}`, error);
      this.handleError(error);
      return false;
    }
  }

  /**
   * 通过工厂创建组件实例
   */
  createInstanceFromFactory(componentId, type, options = {}) {
    try {
      const factory = this.componentFactories.get(type);
      
      if (!factory) {
        throw new Error(`找不到组件工厂: ${type}`);
      }
      
      // 使用工厂创建实例
      const instance = factory(componentId, options);
      
      // 验证实例
      if (!this.isValidComponentInstance(instance)) {
        throw new Error(`工厂创建的实例无效: ${type}`);
      }
      
      // 注入组件信息
      instance.componentType = type;
      instance.registry = this;
      
      // 保存实例
      this.cacheInstance(componentId, instance);
      
      console.log(`通过工厂创建组件实例成功: ${componentId} (${type})`);
      
      return instance;
    } catch (error) {
      console.error(`通过工厂创建组件实例失败: ${componentId} (${type})`, error);
      this.handleError(error);
      return null;
    }
  }

  /**
   * 验证组件实例
   */
  isValidComponentInstance(instance) {
    if (!instance) {
      return false;
    }
    
    // 至少需要render方法
    return typeof instance.render === 'function';
  }

  /**
   * 异步加载组件
   */
  async loadComponent(type, loadFunction) {
    try {
      // 如果组件已存在，直接返回
      if (this.componentTypes.has(type)) {
        return this.componentTypes.get(type);
      }
      
      // 检查是否已经在加载中
      if (this.loadingComponents.has(type)) {
        console.log(`组件 ${type} 正在加载中，等待完成...`);
        return this.loadingComponents.get(type);
      }
      
      console.log(`开始异步加载组件: ${type}`);
      
      // 创建加载promise
      const loadingPromise = Promise.resolve().then(async () => {
        try {
          // 执行加载函数
          const componentClass = await loadFunction();
          
          // 验证并注册组件
          if (this.isValidComponentClass(componentClass)) {
            this.registerComponent(type, componentClass);
            return componentClass;
          } else {
            throw new Error(`加载的组件无效: ${type}`);
          }
        } finally {
          // 无论成功失败，都从加载队列中移除
          this.loadingComponents.delete(type);
        }
      });
      
      // 保存加载promise
      this.loadingComponents.set(type, loadingPromise);
      
      return loadingPromise;
    } catch (error) {
      console.error(`异步加载组件失败: ${type}`, error);
      this.handleError(error);
      
      // 从加载队列中移除
      this.loadingComponents.delete(type);
      
      throw error;
    }
  }

  /**
   * 批量注册组件
   */
  registerComponents(components) {
    try {
      let successCount = 0;
      let failCount = 0;
      
      Object.entries(components).forEach(([type, componentClass]) => {
        if (this.registerComponent(type, componentClass)) {
          successCount++;
        } else {
          failCount++;
        }
      });
      
      console.log(`批量注册组件完成: 成功 ${successCount} 个, 失败 ${failCount} 个`);
      
      return {
        success: successCount,
        fail: failCount,
        total: successCount + failCount
      };
    } catch (error) {
      console.error('批量注册组件失败:', error);
      this.handleError(error);
      return { success: 0, fail: 0, total: 0 };
    }
  }

  /**
   * 触发钩子
   */
  triggerHook(hookName, data) {
    if (!this.lifecycleHooks[hookName]) {
      return;
    }
    
    this.lifecycleHooks[hookName].forEach(hook => {
      try {
        hook(data);
      } catch (error) {
        console.error(`钩子执行失败: ${hookName}`, error);
        this.handleError(error);
      }
    });
  }

  /**
   * 注册生命周期钩子
   */
  on(hookName, callback) {
    if (!this.lifecycleHooks[hookName]) {
      console.warn(`未知的生命周期钩子: ${hookName}`);
      return false;
    }
    
    this.lifecycleHooks[hookName].push(callback);
    return true;
  }

  /**
   * 移除生命周期钩子
   */
  off(hookName, callback) {
    if (!this.lifecycleHooks[hookName]) {
      return false;
    }
    
    this.lifecycleHooks[hookName] = this.lifecycleHooks[hookName].filter(hook => hook !== callback);
    return true;
  }

  /**
   * 添加错误处理器
   */
  addErrorHandler(handler) {
    if (typeof handler !== 'function') {
      console.error('错误处理器必须是函数类型');
      return false;
    }
    
    this.errorHandlers.push(handler);
    return true;
  }

  /**
   * 移除错误处理器
   */
  removeErrorHandler(handler) {
    this.errorHandlers = this.errorHandlers.filter(h => h !== handler);
    return true;
  }

  /**
   * 处理错误
   */
  handleError(error) {
    // 执行所有错误处理器
    this.errorHandlers.forEach(handler => {
      try {
        handler(error);
      } catch (handlerError) {
        console.error('错误处理器执行失败:', handlerError);
      }
    });
  }

  /**
   * 获取所有注册的组件类型
   */
  getRegisteredTypes() {
    return Array.from(this.componentTypes.keys());
  }

  /**
   * 获取所有组件别名
   */
  getRegisteredAliases() {
    const aliases = {};
    this.componentAliases.forEach((type, alias) => {
      aliases[alias] = type;
    });
    return aliases;
  }

  /**
   * 获取所有活跃的组件实例
   */
  getActiveInstances() {
    return Array.from(this.componentInstances.values());
  }

  /**
   * 获取组件实例数量
   */
  getInstanceCount() {
    return this.componentInstances.size;
  }

  /**
   * 获取加载中的组件
   */
  getLoadingComponents() {
    return Array.from(this.loadingComponents.keys());
  }

  /**
   * 检查组件是否已注册
   */
  isComponentRegistered(type) {
    // 直接检查或通过别名检查
    return this.componentTypes.has(type) || this.componentAliases.has(type);
  }

  /**
   * 重置注册中心
   */
  reset() {
    try {
      // 销毁所有实例
      const instanceIds = Array.from(this.componentInstances.keys());
      instanceIds.forEach(id => this.destroyInstance(id));
      
      // 清除所有数据
      this.componentTypes.clear();
      this.componentInstances.clear();
      this.componentFactories.clear();
      this.componentAliases.clear();
      this.loadingComponents.clear();
      
      // 重置钩子
      this.lifecycleHooks = {
        beforeRegister: [],
        afterRegister: [],
        beforeUnregister: [],
        afterUnregister: [],
        beforeInstantiate: [],
        afterInstantiate: []
      };
      
      // 重新初始化
      this.isInitialized = false;
      this.initialize();
      
      console.log('组件注册中心已重置');
      
      return true;
    } catch (error) {
      console.error('重置组件注册中心失败:', error);
      this.handleError(error);
      return false;
    }
  }

  /**
   * 获取注册中心状态
   */
  getStatus() {
    return {
      isInitialized: this.isInitialized,
      componentTypes: this.componentTypes.size,
      componentInstances: this.componentInstances.size,
      componentAliases: this.componentAliases.size,
      componentFactories: this.componentFactories.size,
      loadingComponents: this.loadingComponents.size
    };
  }
}

// 创建组件注册中心实例
const componentRegistry = new ComponentRegistry();

// 自动初始化（当脚本加载完成时）
if (typeof window !== 'undefined') {
  // 注册全局对象
  window.ComponentRegistry = ComponentRegistry;
  window.componentRegistry = componentRegistry;
  
  // 监听DOM加载完成事件，自动初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      componentRegistry.initialize();
    });
  } else {
    // 如果DOM已经加载完成，直接初始化
    componentRegistry.initialize();
  }
}

export { ComponentRegistry, componentRegistry };