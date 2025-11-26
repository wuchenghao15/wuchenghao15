// 组件总线 - 负责系统内各组件和模块之间的通信与事件传递
class ComponentBus {
  constructor() {
    this.events = {};
    this.listeners = {};
    this.isInitialized = false;
    this.messageQueue = [];
    this.isProcessingQueue = false;
    this.eventHistory = [];
    this.maxHistorySize = 100;
    
    // 初始化组件总线
    this.initialize();
  }

  /**
   * 初始化组件总线
   */
  initialize() {
    if (this.isInitialized) return;
    
    // 设置全局错误处理
    this.setupErrorHandling();
    
    // 初始化事件系统
    this.initializeEvents();
    
    this.isInitialized = true;
    console.log('组件总线初始化完成');
  }

  /**
   * 设置错误处理
   */
  setupErrorHandling() {
    this.on('error', (errorData) => {
      console.error('组件总线错误:', errorData);
      // 这里可以添加错误上报逻辑
    });
  }

  /**
   * 初始化内置事件
   */
  initializeEvents() {
    // 预定义一些核心事件
    const coreEvents = [
      'component:loaded',
      'component:rendered', 
      'component:updated',
      'component:destroyed',
      'page:beforerender',
      'page:rendered',
      'page:unloaded',
      'layout:changed',
      'layout:resized',
      'breakpoint:change',
      'theme:changed',
      'auth:login',
      'auth:logout',
      'auth:session_expired',
      'hierarchy:replanned',
      'hierarchy:breakpoint-adjusted',
      'error',
      'success',
      'warning',
      'info'
    ];
    
    coreEvents.forEach(event => {
      this.events[event] = true;
      this.listeners[event] = [];
    });
  }

  /**
   * 注册事件监听器
   * @param {String} event - 事件名称
   * @param {Function} callback - 回调函数
   * @param {Object} options - 选项
   * @returns {String} 监听器ID
   */
  on(event, callback, options = {}) {
    if (typeof callback !== 'function') {
      console.error(`事件 ${event} 的监听器必须是函数`);
      return null;
    }
    
    // 如果事件不存在，初始化它
    if (!this.listeners[event]) {
      this.listeners[event] = [];
      this.events[event] = true;
    }
    
    // 生成唯一监听器ID
    const listenerId = this.generateListenerId(event);
    
    // 添加监听器
    this.listeners[event].push({
      id: listenerId,
      callback,
      once: options.once || false,
      priority: options.priority || 0,
      context: options.context || null,
      debounce: options.debounce || 0,
      throttle: options.throttle || 0
    });
    
    // 根据优先级排序
    this.listeners[event].sort((a, b) => b.priority - a.priority);
    
    console.log(`事件监听器已注册: ${event} (ID: ${listenerId})`);
    return listenerId;
  }

  /**
   * 注册一次性事件监听器
   * @param {String} event - 事件名称
   * @param {Function} callback - 回调函数
   * @param {Object} options - 选项
   * @returns {String} 监听器ID
   */
  once(event, callback, options = {}) {
    options.once = true;
    return this.on(event, callback, options);
  }

  /**
   * 移除事件监听器
   * @param {String} event - 事件名称
   * @param {Function|String} callbackOrId - 回调函数或监听器ID
   * @returns {Boolean} 是否成功移除
   */
  off(event, callbackOrId) {
    if (!this.listeners[event]) {
      return false;
    }
    
    let removed = false;
    
    if (typeof callbackOrId === 'string') {
      // 通过ID移除
      const initialLength = this.listeners[event].length;
      this.listeners[event] = this.listeners[event].filter(
        listener => listener.id !== callbackOrId
      );
      removed = this.listeners[event].length < initialLength;
    } else if (typeof callbackOrId === 'function') {
      // 通过回调函数移除
      const initialLength = this.listeners[event].length;
      this.listeners[event] = this.listeners[event].filter(
        listener => listener.callback !== callbackOrId
      );
      removed = this.listeners[event].length < initialLength;
    }
    
    if (removed) {
      console.log(`事件监听器已移除: ${event}`);
    }
    
    // 如果没有监听器了，清理事件
    if (this.listeners[event].length === 0) {
      delete this.listeners[event];
      delete this.events[event];
    }
    
    return removed;
  }

  /**
   * 移除指定事件的所有监听器
   * @param {String} event - 事件名称
   * @returns {Boolean} 是否成功移除
   */
  offAll(event) {
    if (!this.listeners[event]) {
      return false;
    }
    
    delete this.listeners[event];
    delete this.events[event];
    console.log(`事件 ${event} 的所有监听器已移除`);
    return true;
  }

  /**
   * 触发事件
   * @param {String} event - 事件名称
   * @param {*} data - 事件数据
   * @param {Boolean} async - 是否异步触发
   */
  emit(event, data = null, async = false) {
    if (!this.events[event]) {
      console.warn(`尝试触发未注册的事件: ${event}`);
      // 自动创建未注册的事件
      this.listeners[event] = [];
      this.events[event] = true;
    }
    
    const eventData = {
      event,
      data,
      timestamp: Date.now()
    };
    
    // 记录事件历史
    this.recordEventHistory(eventData);
    
    if (async) {
      // 异步触发 - 添加到消息队列
      this.messageQueue.push(eventData);
      this.processMessageQueue();
    } else {
      // 同步触发
      this.processEvent(eventData);
    }
    
    return this;
  }

  /**
   * 异步触发事件
   * @param {String} event - 事件名称
   * @param {*} data - 事件数据
   */
  emitAsync(event, data = null) {
    return this.emit(event, data, true);
  }

  /**
   * 处理事件
   * @param {Object} eventData - 事件数据
   */
  processEvent(eventData) {
    const { event, data } = eventData;
    const eventListeners = this.listeners[event] || [];
    
    // 收集一次性监听器ID，以便稍后移除
    const oneTimeListeners = [];
    
    eventListeners.forEach(listener => {
      try {
        const context = listener.context || window;
        listener.callback.call(context, data);
        
        // 标记一次性监听器
        if (listener.once) {
          oneTimeListeners.push(listener.id);
        }
      } catch (error) {
        console.error(`执行事件 ${event} 的监听器时出错:`, error);
        // 触发错误事件
        this.emit('error', {
          event,
          error,
          listenerId: listener.id
        });
      }
    });
    
    // 移除一次性监听器
    oneTimeListeners.forEach(id => this.off(event, id));
  }

  /**
   * 处理消息队列
   */
  processMessageQueue() {
    if (this.isProcessingQueue) return;
    
    this.isProcessingQueue = true;
    
    // 使用requestAnimationFrame来异步处理消息队列
    requestAnimationFrame(() => {
      while (this.messageQueue.length > 0) {
        const eventData = this.messageQueue.shift();
        this.processEvent(eventData);
      }
      
      this.isProcessingQueue = false;
    });
  }

  /**
   * 生成唯一监听器ID
   * @param {String} event - 事件名称
   * @returns {String} 监听器ID
   */
  generateListenerId(event) {
    return `${event}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 记录事件历史
   * @param {Object} eventData - 事件数据
   */
  recordEventHistory(eventData) {
    this.eventHistory.push(eventData);
    
    // 限制历史记录大小
    if (this.eventHistory.length > this.maxHistorySize) {
      this.eventHistory.shift();
    }
  }

  /**
   * 获取事件历史
   * @param {Number} limit - 限制返回的历史记录数量
   * @returns {Array} 事件历史
   */
  getEventHistory(limit = null) {
    if (limit !== null) {
      return this.eventHistory.slice(-limit);
    }
    return [...this.eventHistory];
  }

  /**
   * 清除事件历史
   */
  clearEventHistory() {
    this.eventHistory = [];
  }

  /**
   * 获取已注册的事件列表
   * @returns {Array} 事件列表
   */
  getRegisteredEvents() {
    return Object.keys(this.events);
  }

  /**
   * 获取事件的监听器数量
   * @param {String} event - 事件名称
   * @returns {Number} 监听器数量
   */
  getListenerCount(event) {
    return this.listeners[event] ? this.listeners[event].length : 0;
  }

  /**
   * 检查事件是否存在
   * @param {String} event - 事件名称
   * @returns {Boolean} 是否存在
   */
  hasEvent(event) {
    return !!this.events[event];
  }

  /**
   * 暂停事件触发
   * @param {String} event - 事件名称，如果不指定则暂停所有事件
   */
  pause(event = null) {
    if (event) {
      if (this.events[event]) {
        this.events[event] = false;
        console.log(`事件已暂停: ${event}`);
      }
    } else {
      // 暂停所有事件
      Object.keys(this.events).forEach(e => {
        this.events[e] = false;
      });
      console.log('所有事件已暂停');
    }
  }

  /**
   * 恢复事件触发
   * @param {String} event - 事件名称，如果不指定则恢复所有事件
   */
  resume(event = null) {
    if (event) {
      if (this.listeners[event]) {
        this.events[event] = true;
        console.log(`事件已恢复: ${event}`);
      }
    } else {
      // 恢复所有事件
      Object.keys(this.listeners).forEach(e => {
        this.events[e] = true;
      });
      console.log('所有事件已恢复');
    }
  }

  /**
   * 创建事件命名空间
   * @param {String} namespace - 命名空间
   * @returns {Object} 命名空间的事件方法
   */
  namespace(namespace) {
    const ns = namespace + ':';
    
    return {
      on: (event, callback, options) => this.on(ns + event, callback, options),
      once: (event, callback, options) => this.once(ns + event, callback, options),
      off: (event, callbackOrId) => this.off(ns + event, callbackOrId),
      offAll: () => {
        const events = this.getRegisteredEvents().filter(e => e.startsWith(ns));
        events.forEach(event => this.offAll(event));
        return this;
      },
      emit: (event, data, async) => this.emit(ns + event, data, async),
      emitAsync: (event, data) => this.emitAsync(ns + event, data),
      getListenerCount: (event) => this.getListenerCount(ns + event),
      hasEvent: (event) => this.hasEvent(ns + event),
      pause: (event) => this.pause(ns + event),
      resume: (event) => this.resume(ns + event)
    };
  }

  /**
   * 销毁组件总线
   */
  destroy() {
    // 清除所有监听器
    Object.keys(this.listeners).forEach(event => {
      this.offAll(event);
    });
    
    // 清空消息队列和事件历史
    this.messageQueue = [];
    this.eventHistory = [];
    
    this.isInitialized = false;
    console.log('组件总线已销毁');
  }
}

// 创建全局组件总线实例
const componentBus = new ComponentBus();

// 导出
if (typeof window !== 'undefined') {
  window.ComponentBus = ComponentBus;
  window.componentBus = componentBus;
}

export { ComponentBus, componentBus };