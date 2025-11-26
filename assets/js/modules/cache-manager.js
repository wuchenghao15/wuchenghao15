// 缓存管理器 - 管理本地缓存策略，优化资源加载和数据访问
class CacheManager {
  constructor(options = {}) {
    // 缓存配置
    this.config = {
      // 存储类型配置
      storageTypes: {
        localStorage: true, // 是否启用 localStorage
        sessionStorage: true, // 是否启用 sessionStorage
        indexedDB: true, // 是否启用 IndexedDB
        memoryCache: true // 是否启用内存缓存
      },
      
      // 默认存储配置
      defaultStorageType: 'localStorage', // 默认存储类型
      memoryCacheMaxSize: 100, // 内存缓存最大条目数
      
      // 缓存策略配置
      defaultTTL: 3600000, // 默认缓存过期时间（毫秒），1小时
      staleWhileRevalidate: true, // 是否启用 stale-while-revalidate 策略
      revalidateTimeout: 5000, // 重新验证超时时间（毫秒）
      
      // 缓存版本管理
      cacheVersion: options.cacheVersion || '1.0.0', // 缓存版本
      enableVersioning: true, // 是否启用版本控制
      
      // 批量操作配置
      batchSizeLimit: 100, // 批量操作最大数量
      
      // 事件和回调
      onCacheUpdate: options.onCacheUpdate || null, // 缓存更新回调
      onCacheEvict: options.onCacheEvict || null, // 缓存驱逐回调
      onError: options.onError || null, // 错误处理回调
      
      // 调试选项
      debug: options.debug || false,
      
      ...options
    };
    
    // 存储引擎实例
    this.storageEngines = {};
    
    // 内存缓存
    this.memoryCache = new Map();
    
    // 缓存统计
    this.stats = {
      hits: 0,
      misses: 0,
      writes: 0,
      deletes: 0,
      evictions: 0,
      size: 0
    };
    
    // 初始化状态
    this.isInitialized = false;
    
    // 兼容性检查
    this.compatibility = {
      localStorage: typeof window !== 'undefined' && typeof localStorage !== 'undefined',
      sessionStorage: typeof window !== 'undefined' && typeof sessionStorage !== 'undefined',
      indexedDB: typeof window !== 'undefined' && typeof indexedDB !== 'undefined'
    };
    
    // 初始化
    this.initialize();
  }

  /**
   * 初始化缓存管理器
   */
  initialize() {
    if (this.isInitialized) {
      this.log('缓存管理器已经初始化');
      return this;
    }
    
    this.log('初始化缓存管理器...');
    
    // 检查兼容性
    this.checkCompatibility();
    
    // 初始化存储引擎
    this.initializeStorageEngines();
    
    // 清理过期缓存
    this.cleanupExpiredCache();
    
    // 初始化完成
    this.isInitialized = true;
    
    this.log('缓存管理器初始化完成');
    
    return this;
  }

  /**
   * 检查浏览器兼容性
   */
  checkCompatibility() {
    this.log('检查浏览器兼容性...');
    
    // 检查 localStorage
    if (this.config.storageTypes.localStorage && !this.compatibility.localStorage) {
      this.log('浏览器不支持 localStorage，将禁用此存储类型', 'warn');
      this.config.storageTypes.localStorage = false;
    }
    
    // 检查 sessionStorage
    if (this.config.storageTypes.sessionStorage && !this.compatibility.sessionStorage) {
      this.log('浏览器不支持 sessionStorage，将禁用此存储类型', 'warn');
      this.config.storageTypes.sessionStorage = false;
    }
    
    // 检查 IndexedDB
    if (this.config.storageTypes.indexedDB && !this.compatibility.indexedDB) {
      this.log('浏览器不支持 IndexedDB，将禁用此存储类型', 'warn');
      this.config.storageTypes.indexedDB = false;
    }
    
    // 确保至少有一种存储类型可用
    if (!this.config.storageTypes.localStorage && 
        !this.config.storageTypes.sessionStorage && 
        !this.config.storageTypes.indexedDB && 
        !this.config.storageTypes.memoryCache) {
      
      this.log('没有可用的存储类型，将启用内存缓存', 'warn');
      this.config.storageTypes.memoryCache = true;
    }
    
    // 确保默认存储类型可用
    if (!this.isStorageTypeAvailable(this.config.defaultStorageType)) {
      this.log(`默认存储类型 ${this.config.defaultStorageType} 不可用，将使用备选方案`, 'warn');
      this.config.defaultStorageType = this.getFirstAvailableStorageType();
    }
  }

  /**
   * 检查存储类型是否可用
   */
  isStorageTypeAvailable(type) {
    switch (type) {
      case 'localStorage':
        return this.config.storageTypes.localStorage && this.compatibility.localStorage;
      case 'sessionStorage':
        return this.config.storageTypes.sessionStorage && this.compatibility.sessionStorage;
      case 'indexedDB':
        return this.config.storageTypes.indexedDB && this.compatibility.indexedDB;
      case 'memoryCache':
        return this.config.storageTypes.memoryCache;
      default:
        return false;
    }
  }

  /**
   * 获取第一个可用的存储类型
   */
  getFirstAvailableStorageType() {
    const types = ['localStorage', 'sessionStorage', 'indexedDB', 'memoryCache'];
    
    for (const type of types) {
      if (this.isStorageTypeAvailable(type)) {
        return type;
      }
    }
    
    return 'memoryCache'; // 最后回退到内存缓存
  }

  /**
   * 初始化存储引擎
   */
  initializeStorageEngines() {
    this.log('初始化存储引擎...');
    
    // 初始化 localStorage 引擎
    if (this.config.storageTypes.localStorage && this.compatibility.localStorage) {
      this.storageEngines.localStorage = new LocalStorageEngine(this.config, this);
    }
    
    // 初始化 sessionStorage 引擎
    if (this.config.storageTypes.sessionStorage && this.compatibility.sessionStorage) {
      this.storageEngines.sessionStorage = new SessionStorageEngine(this.config, this);
    }
    
    // 初始化 IndexedDB 引擎
    if (this.config.storageTypes.indexedDB && this.compatibility.indexedDB) {
      this.storageEngines.indexedDB = new IndexedDBEngine(this.config, this);
    }
    
    // 内存缓存引擎总是可用
    if (this.config.storageTypes.memoryCache) {
      this.storageEngines.memoryCache = new MemoryCacheEngine(this.config, this);
    }
  }

  /**
   * 清理过期缓存
   */
  cleanupExpiredCache() {
    this.log('清理过期缓存...');
    
    // 清理所有启用的存储引擎中的过期缓存
    for (const [type, engine] of Object.entries(this.storageEngines)) {
      if (engine && typeof engine.cleanupExpired === 'function') {
        try {
          engine.cleanupExpired();
        } catch (error) {
          this.handleError(`清理 ${type} 过期缓存失败:`, error);
        }
      }
    }
  }

  /**
   * 获取缓存项
   * @param {string} key - 缓存键
   * @param {Object} options - 选项
   * @returns {Promise<any>} 缓存的值
   */
  async get(key, options = {}) {
    this.validateKey(key);
    
    // 确定使用的存储类型
    const storageType = options.storageType || this.config.defaultStorageType;
    
    // 检查存储类型是否可用
    if (!this.isStorageTypeAvailable(storageType)) {
      throw new Error(`存储类型 ${storageType} 不可用`);
    }
    
    try {
      // 从存储引擎获取数据
      const engine = this.storageEngines[storageType];
      const cachedItem = await engine.get(key);
      
      // 检查缓存是否存在
      if (cachedItem === null) {
        this.stats.misses++;
        this.log(`缓存未命中: ${key} (${storageType})`);
        return null;
      }
      
      // 检查缓存是否过期
      if (this.isExpired(cachedItem)) {
        this.stats.misses++;
        this.log(`缓存已过期: ${key} (${storageType})`);
        
        // 处理 stale-while-revalidate 策略
        if (options.staleWhileRevalidate !== false && this.config.staleWhileRevalidate) {
          this.log(`使用过期缓存并重新验证: ${key} (${storageType})`);
          
          // 在后台重新验证缓存
          if (options.revalidator) {
            this.revalidateInBackground(key, options.revalidator, options);
          }
          
          // 返回过期的数据
          return cachedItem.value;
        } else {
          // 删除过期缓存
          await this.delete(key, { storageType });
          return null;
        }
      }
      
      // 缓存命中
      this.stats.hits++;
      this.log(`缓存命中: ${key} (${storageType})`);
      
      // 更新访问时间（如果启用）
      if (options.updateAccessTime !== false) {
        cachedItem.lastAccessTime = Date.now();
        await engine.set(key, cachedItem);
      }
      
      return cachedItem.value;
    } catch (error) {
      this.handleError(`获取缓存项失败: ${key}`, error);
      return null;
    }
  }

  /**
   * 设置缓存项
   * @param {string} key - 缓存键
   * @param {any} value - 要缓存的值
   * @param {Object} options - 选项
   * @returns {Promise<boolean>} 是否成功
   */
  async set(key, value, options = {}) {
    this.validateKey(key);
    
    // 确定使用的存储类型
    const storageType = options.storageType || this.config.defaultStorageType;
    
    // 检查存储类型是否可用
    if (!this.isStorageTypeAvailable(storageType)) {
      throw new Error(`存储类型 ${storageType} 不可用`);
    }
    
    try {
      // 准备缓存项
      const ttl = options.ttl !== undefined ? options.ttl : this.config.defaultTTL;
      const expiresAt = ttl > 0 ? Date.now() + ttl : 0; // 0 表示永不过期
      
      const cacheItem = {
        value,
        key,
        storageType,
        createdAt: Date.now(),
        lastAccessTime: Date.now(),
        expiresAt,
        ttl,
        version: this.config.enableVersioning ? this.config.cacheVersion : null
      };
      
      // 检查值是否可序列化
      this.validateValue(value);
      
      // 使用存储引擎设置缓存
      const engine = this.storageEngines[storageType];
      const success = await engine.set(key, cacheItem);
      
      if (success) {
        this.stats.writes++;
        this.stats.size++;
        this.log(`缓存设置成功: ${key} (${storageType})`);
        
        // 触发缓存更新事件
        this.notifyCacheUpdate(key, value, 'set', storageType);
      }
      
      return success;
    } catch (error) {
      this.handleError(`设置缓存项失败: ${key}`, error);
      return false;
    }
  }

  /**
   * 删除缓存项
   * @param {string} key - 缓存键
   * @param {Object} options - 选项
   * @returns {Promise<boolean>} 是否成功
   */
  async delete(key, options = {}) {
    this.validateKey(key);
    
    // 确定使用的存储类型
    const storageType = options.storageType || this.config.defaultStorageType;
    
    // 检查存储类型是否可用
    if (!this.isStorageTypeAvailable(storageType)) {
      throw new Error(`存储类型 ${storageType} 不可用`);
    }
    
    try {
      // 使用存储引擎删除缓存
      const engine = this.storageEngines[storageType];
      const success = await engine.delete(key);
      
      if (success) {
        this.stats.deletes++;
        if (this.stats.size > 0) this.stats.size--;
        this.log(`缓存删除成功: ${key} (${storageType})`);
        
        // 触发缓存删除事件
        this.notifyCacheEvict(key, 'delete', storageType);
      }
      
      return success;
    } catch (error) {
      this.handleError(`删除缓存项失败: ${key}`, error);
      return false;
    }
  }

  /**
   * 检查缓存项是否存在且有效
   * @param {string} key - 缓存键
   * @param {Object} options - 选项
   * @returns {Promise<boolean>} 是否存在且有效
   */
  async has(key, options = {}) {
    try {
      const value = await this.get(key, options);
      return value !== null;
    } catch (error) {
      this.handleError(`检查缓存项失败: ${key}`, error);
      return false;
    }
  }

  /**
   * 清空缓存
   * @param {Object} options - 选项
   * @returns {Promise<boolean>} 是否成功
   */
  async clear(options = {}) {
    try {
      // 确定要清空的存储类型
      const storageTypes = options.storageTypes || Object.keys(this.storageEngines);
      
      let allSuccess = true;
      
      for (const type of storageTypes) {
        if (this.storageEngines[type]) {
          const success = await this.storageEngines[type].clear();
          allSuccess = allSuccess && success;
          
          if (success) {
            this.log(`缓存已清空: ${type}`);
          }
        }
      }
      
      // 重置统计
      if (allSuccess) {
        this.stats.size = 0;
        this.stats.evictions = 0;
        // 保留 hits, misses, writes, deletes 统计
      }
      
      return allSuccess;
    } catch (error) {
      this.handleError('清空缓存失败:', error);
      return false;
    }
  }

  /**
   * 获取所有缓存键
   * @param {Object} options - 选项
   * @returns {Promise<string[]>} 缓存键数组
   */
  async keys(options = {}) {
    try {
      // 确定要获取键的存储类型
      const storageType = options.storageType || this.config.defaultStorageType;
      
      // 检查存储类型是否可用
      if (!this.isStorageTypeAvailable(storageType)) {
        throw new Error(`存储类型 ${storageType} 不可用`);
      }
      
      // 使用存储引擎获取键
      const engine = this.storageEngines[storageType];
      return await engine.keys();
    } catch (error) {
      this.handleError('获取缓存键失败:', error);
      return [];
    }
  }

  /**
   * 获取缓存项数量
   * @param {Object} options - 选项
   * @returns {Promise<number>} 缓存项数量
   */
  async size(options = {}) {
    try {
      // 确定要获取数量的存储类型
      const storageType = options.storageType || this.config.defaultStorageType;
      
      // 检查存储类型是否可用
      if (!this.isStorageTypeAvailable(storageType)) {
        throw new Error(`存储类型 ${storageType} 不可用`);
      }
      
      // 使用存储引擎获取数量
      const engine = this.storageEngines[storageType];
      return await engine.size();
    } catch (error) {
      this.handleError('获取缓存大小失败:', error);
      return 0;
    }
  }

  /**
   * 批量获取缓存项
   * @param {string[]} keys - 缓存键数组
   * @param {Object} options - 选项
   * @returns {Promise<Object>} 键值对对象
   */
  async batchGet(keys, options = {}) {
    // 验证参数
    if (!Array.isArray(keys)) {
      throw new Error('keys 必须是数组');
    }
    
    // 限制批量操作数量
    if (keys.length > this.config.batchSizeLimit) {
      throw new Error(`批量操作数量超过限制: ${keys.length} > ${this.config.batchSizeLimit}`);
    }
    
    const results = {};
    
    // 并行获取所有键
    const promises = keys.map(async (key) => {
      try {
        const value = await this.get(key, options);
        results[key] = value;
      } catch (error) {
        this.handleError(`批量获取失败: ${key}`, error);
        results[key] = null;
      }
    });
    
    await Promise.all(promises);
    return results;
  }

  /**
   * 批量设置缓存项
   * @param {Object} keyValuePairs - 键值对对象
   * @param {Object} options - 选项
   * @returns {Promise<Object>} 操作结果
   */
  async batchSet(keyValuePairs, options = {}) {
    // 验证参数
    if (typeof keyValuePairs !== 'object' || keyValuePairs === null) {
      throw new Error('keyValuePairs 必须是对象');
    }
    
    const keys = Object.keys(keyValuePairs);
    
    // 限制批量操作数量
    if (keys.length > this.config.batchSizeLimit) {
      throw new Error(`批量操作数量超过限制: ${keys.length} > ${this.config.batchSizeLimit}`);
    }
    
    const results = {};
    
    // 并行设置所有键
    const promises = keys.map(async (key) => {
      try {
        const value = keyValuePairs[key];
        const success = await this.set(key, value, options);
        results[key] = success;
      } catch (error) {
        this.handleError(`批量设置失败: ${key}`, error);
        results[key] = false;
      }
    });
    
    await Promise.all(promises);
    return results;
  }

  /**
   * 批量删除缓存项
   * @param {string[]} keys - 缓存键数组
   * @param {Object} options - 选项
   * @returns {Promise<Object>} 操作结果
   */
  async batchDelete(keys, options = {}) {
    // 验证参数
    if (!Array.isArray(keys)) {
      throw new Error('keys 必须是数组');
    }
    
    // 限制批量操作数量
    if (keys.length > this.config.batchSizeLimit) {
      throw new Error(`批量操作数量超过限制: ${keys.length} > ${this.config.batchSizeLimit}`);
    }
    
    const results = {};
    
    // 并行删除所有键
    const promises = keys.map(async (key) => {
      try {
        const success = await this.delete(key, options);
        results[key] = success;
      } catch (error) {
        this.handleError(`批量删除失败: ${key}`, error);
        results[key] = false;
      }
    });
    
    await Promise.all(promises);
    return results;
  }

  /**
   * 使用缓存装饰器包装函数
   * @param {Function} fn - 要包装的函数
   * @param {Object} options - 缓存选项
   * @returns {Function} 包装后的函数
   */
  cached(fn, options = {}) {
    const cacheKeyPrefix = options.keyPrefix || fn.name || 'cached_fn';
    const ttl = options.ttl || this.config.defaultTTL;
    const storageType = options.storageType || this.config.defaultStorageType;
    
    return async function(...args) {
      // 生成缓存键
      const cacheKey = `${cacheKeyPrefix}_${this._generateCacheKey(args)}`;
      
      try {
        // 尝试从缓存获取
        const cachedResult = await this.get(cacheKey, { storageType });
        
        if (cachedResult !== null) {
          return cachedResult;
        }
        
        // 执行原函数
        const result = await fn.apply(this, args);
        
        // 缓存结果
        await this.set(cacheKey, result, { ttl, storageType });
        
        return result;
      } catch (error) {
        this.handleError('缓存装饰器执行失败:', error);
        
        // 出错时仍尝试执行原函数
        return fn.apply(this, args);
      }
    }.bind(this);
  }

  /**
   * 生成缓存键
   * @param {any[]} args - 函数参数
   * @returns {string} 缓存键
   */
  _generateCacheKey(args) {
    try {
      return JSON.stringify(args);
    } catch (error) {
      // 如果参数无法序列化，使用简单的字符串表示
      return String(args.join('_'));
    }
  }

  /**
   * 在后台重新验证缓存
   */
  async revalidateInBackground(key, revalidator, options) {
    if (typeof revalidator !== 'function') {
      return;
    }
    
    try {
      // 设置超时
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('重新验证超时')), this.config.revalidateTimeout);
      });
      
      // 执行重新验证
      const newData = await Promise.race([revalidator(), timeoutPromise]);
      
      // 更新缓存
      await this.set(key, newData, options);
      
      this.log(`缓存重新验证成功: ${key}`);
    } catch (error) {
      this.handleError(`缓存重新验证失败: ${key}`, error);
    }
  }

  /**
   * 缓存预加载
   * @param {Object[]} items - 要预加载的项目数组
   * @returns {Promise<void>}
   */
  async preload(items) {
    if (!Array.isArray(items)) {
      throw new Error('items 必须是数组');
    }
    
    const promises = items.map(async (item) => {
      try {
        const { key, value, options = {} } = item;
        await this.set(key, value, options);
      } catch (error) {
        this.handleError(`预加载失败: ${item.key}`, error);
      }
    });
    
    await Promise.all(promises);
  }

  /**
   * 导出缓存数据
   * @param {Object} options - 选项
   * @returns {Promise<Object>} 导出的数据
   */
  async exportData(options = {}) {
    try {
      // 确定要导出的存储类型
      const storageTypes = options.storageTypes || Object.keys(this.storageEngines);
      const exportData = {};
      
      for (const type of storageTypes) {
        if (this.storageEngines[type]) {
          exportData[type] = await this.storageEngines[type].exportData();
        }
      }
      
      return {
        version: this.config.cacheVersion,
        exportTime: Date.now(),
        data: exportData
      };
    } catch (error) {
      this.handleError('导出缓存数据失败:', error);
      return null;
    }
  }

  /**
   * 导入缓存数据
   * @param {Object} data - 要导入的数据
   * @param {Object} options - 选项
   * @returns {Promise<boolean>} 是否成功
   */
  async importData(data, options = {}) {
    try {
      if (!data || !data.data) {
        throw new Error('无效的导入数据格式');
      }
      
      // 检查版本（如果启用版本控制）
      if (this.config.enableVersioning && data.version && data.version !== this.config.cacheVersion) {
        this.log(`导入数据版本不匹配: ${data.version} vs ${this.config.cacheVersion}`, 'warn');
        
        if (options.strictVersioning !== false) {
          throw new Error('版本不匹配，导入失败');
        }
      }
      
      let allSuccess = true;
      
      // 导入每种存储类型的数据
      for (const [type, typeData] of Object.entries(data.data)) {
        if (this.storageEngines[type]) {
          const success = await this.storageEngines[type].importData(typeData, options);
          allSuccess = allSuccess && success;
        }
      }
      
      return allSuccess;
    } catch (error) {
      this.handleError('导入缓存数据失败:', error);
      return false;
    }
  }

  /**
   * 检查缓存项是否过期
   */
  isExpired(cacheItem) {
    if (!cacheItem || !cacheItem.expiresAt) {
      return false;
    }
    
    // 如果过期时间为 0，表示永不过期
    if (cacheItem.expiresAt === 0) {
      return false;
    }
    
    return Date.now() > cacheItem.expiresAt;
  }

  /**
   * 验证缓存键
   */
  validateKey(key) {
    if (!key || typeof key !== 'string' || key.trim() === '') {
      throw new Error('缓存键必须是非空字符串');
    }
    
    // 限制键的长度
    if (key.length > 500) {
      throw new Error('缓存键长度超过限制（500个字符）');
    }
  }

  /**
   * 验证缓存值
   */
  validateValue(value) {
    try {
      // 检查值是否可序列化
      JSON.stringify(value);
      return true;
    } catch (error) {
      throw new Error('缓存值必须是可序列化的');
    }
  }

  /**
   * 获取缓存统计信息
   */
  getStats() {
    return { ...this.stats };
  }

  /**
   * 重置缓存统计信息
   */
  resetStats() {
    this.stats = {
      hits: 0,
      misses: 0,
      writes: 0,
      deletes: 0,
      evictions: 0,
      size: this.stats.size // 保留大小统计
    };
  }

  /**
   * 获取缓存管理器状态
   */
  getState() {
    return {
      initialized: this.isInitialized,
      storageTypes: this.config.storageTypes,
      compatibility: this.compatibility,
      defaultStorageType: this.config.defaultStorageType,
      cacheVersion: this.config.cacheVersion,
      stats: this.getStats()
    };
  }

  /**
   * 触发缓存更新通知
   */
  notifyCacheUpdate(key, value, operation, storageType) {
    if (typeof this.config.onCacheUpdate === 'function') {
      try {
        this.config.onCacheUpdate(key, value, operation, storageType);
      } catch (error) {
        this.handleError('缓存更新回调执行失败:', error);
      }
    }
  }

  /**
   * 触发缓存驱逐通知
   */
  notifyCacheEvict(key, reason, storageType) {
    this.stats.evictions++;
    
    if (typeof this.config.onCacheEvict === 'function') {
      try {
        this.config.onCacheEvict(key, reason, storageType);
      } catch (error) {
        this.handleError('缓存驱逐回调执行失败:', error);
      }
    }
  }

  /**
   * 错误处理
   */
  handleError(message, error) {
    const errorMessage = `${message}: ${error.message}`;
    
    if (this.config.debug) {
      console.error(errorMessage, error);
    }
    
    if (typeof this.config.onError === 'function') {
      try {
        this.config.onError(message, error);
      } catch (callbackError) {
        console.error('错误处理回调执行失败:', callbackError);
      }
    }
  }

  /**
   * 日志记录
   */
  log(message, level = 'log') {
    if (!this.config.debug) {
      return;
    }
    
    const timestamp = new Date().toISOString();
    const logMessage = `[CacheManager] ${timestamp} ${message}`;
    
    switch (level) {
      case 'log':
        console.log(logMessage);
        break;
      case 'warn':
        console.warn(logMessage);
        break;
      case 'error':
        console.error(logMessage);
        break;
      case 'info':
        console.info(logMessage);
        break;
      default:
        console.log(logMessage);
    }
  }

  /**
   * 更新配置
   */
  updateConfig(newConfig) {
    if (typeof newConfig === 'object' && newConfig !== null) {
      this.config = { ...this.config, ...newConfig };
      this.log('配置已更新');
    }
    
    return this;
  }

  /**
   * 销毁缓存管理器
   */
  destroy() {
    this.log('销毁缓存管理器...');
    
    // 清空所有缓存
    this.clear();
    
    // 重置存储引擎
    this.storageEngines = {};
    
    // 重置内存缓存
    this.memoryCache.clear();
    
    // 重置状态
    this.isInitialized = false;
    this.resetStats();
    
    this.log('缓存管理器已销毁');
  }
}

// localStorage 存储引擎
class LocalStorageEngine {
  constructor(config, cacheManager) {
    this.config = config;
    this.cacheManager = cacheManager;
    this.storage = localStorage;
    this.prefix = `${config.enableVersioning ? config.cacheVersion + '_' : ''}cache_`;
  }

  async get(key) {
    try {
      const fullKey = this.prefix + key;
      const item = this.storage.getItem(fullKey);
      
      if (item === null) {
        return null;
      }
      
      return JSON.parse(item);
    } catch (error) {
      this.cacheManager.handleError(`localStorage get 失败: ${key}`, error);
      return null;
    }
  }

  async set(key, value) {
    try {
      const fullKey = this.prefix + key;
      const serializedValue = JSON.stringify(value);
      
      // 检查存储容量限制
      this.checkStorageCapacity(serializedValue);
      
      this.storage.setItem(fullKey, serializedValue);
      return true;
    } catch (error) {
      this.cacheManager.handleError(`localStorage set 失败: ${key}`, error);
      return false;
    }
  }

  async delete(key) {
    try {
      const fullKey = this.prefix + key;
      this.storage.removeItem(fullKey);
      return true;
    } catch (error) {
      this.cacheManager.handleError(`localStorage delete 失败: ${key}`, error);
      return false;
    }
  }

  async clear() {
    try {
      // 只清除以 prefix 开头的键
      const keysToRemove = [];
      
      for (let i = 0; i < this.storage.length; i++) {
        const key = this.storage.key(i);
        if (key && key.startsWith(this.prefix)) {
          keysToRemove.push(key);
        }
      }
      
      for (const key of keysToRemove) {
        this.storage.removeItem(key);
      }
      
      return true;
    } catch (error) {
      this.cacheManager.handleError('localStorage clear 失败', error);
      return false;
    }
  }

  async keys() {
    try {
      const keys = [];
      
      for (let i = 0; i < this.storage.length; i++) {
        const key = this.storage.key(i);
        if (key && key.startsWith(this.prefix)) {
          // 移除前缀
          keys.push(key.substring(this.prefix.length));
        }
      }
      
      return keys;
    } catch (error) {
      this.cacheManager.handleError('localStorage keys 失败', error);
      return [];
    }
  }

  async size() {
    return this.keys().length;
  }

  async cleanupExpired() {
    try {
      const keys = await this.keys();
      
      for (const key of keys) {
        const item = await this.get(key);
        
        if (item && this.cacheManager.isExpired(item)) {
          await this.delete(key);
          this.cacheManager.notifyCacheEvict(key, 'expired', 'localStorage');
        }
      }
    } catch (error) {
      this.cacheManager.handleError('localStorage 清理过期缓存失败', error);
    }
  }

  async exportData() {
    try {
      const data = {};
      const keys = await this.keys();
      
      for (const key of keys) {
        const value = await this.get(key);
        if (value !== null) {
          data[key] = value;
        }
      }
      
      return data;
    } catch (error) {
      this.cacheManager.handleError('localStorage 导出失败', error);
      return {};
    }
  }

  async importData(data, options = {}) {
    try {
      // 如果 options.overwrite 为 true，则先清空现有数据
      if (options.overwrite) {
        await this.clear();
      }
      
      for (const [key, value] of Object.entries(data)) {
        await this.set(key, value);
      }
      
      return true;
    } catch (error) {
      this.cacheManager.handleError('localStorage 导入失败', error);
      return false;
    }
  }

  checkStorageCapacity(data) {
    // localStorage 通常有约 5-10MB 的限制
    // 这里做一个简单的检查
    if (data.length > 5 * 1024 * 1024) { // 5MB
      throw new Error('数据大小超过 localStorage 限制');
    }
  }
}

// sessionStorage 存储引擎
class SessionStorageEngine extends LocalStorageEngine {
  constructor(config, cacheManager) {
    super(config, cacheManager);
    this.storage = sessionStorage;
  }
}

// IndexedDB 存储引擎
class IndexedDBEngine {
  constructor(config, cacheManager) {
    this.config = config;
    this.cacheManager = cacheManager;
    this.dbName = `${config.enableVersioning ? config.cacheVersion + '_' : ''}cache_db`;
    this.storeName = 'cache_store';
    this.dbVersion = 1;
    this.db = null;
    
    // 初始化数据库连接
    this.initDB();
  }

  async initDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // 创建存储对象
        if (!db.objectStoreNames.contains(this.storeName)) {
          const store = db.createObjectStore(this.storeName, { keyPath: 'key' });
          
          // 创建索引以提高查询性能
          store.createIndex('expiresAt', 'expiresAt', { unique: false });
          store.createIndex('createdAt', 'createdAt', { unique: false });
          store.createIndex('lastAccessTime', 'lastAccessTime', { unique: false });
        }
      };
      
      request.onsuccess = (event) => {
        this.db = event.target.result;
        resolve(this.db);
      };
      
      request.onerror = (event) => {
        reject(event.target.error);
      };
    });
  }

  async getDB() {
    if (!this.db) {
      await this.initDB();
    }
    return this.db;
  }

  async get(key) {
    try {
      const db = await this.getDB();
      
      return new Promise((resolve, reject) => {
        const transaction = db.transaction([this.storeName], 'readonly');
        const store = transaction.objectStore(this.storeName);
        const request = store.get(key);
        
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      this.cacheManager.handleError(`IndexedDB get 失败: ${key}`, error);
      return null;
    }
  }

  async set(key, value) {
    try {
      const db = await this.getDB();
      
      return new Promise((resolve, reject) => {
        const transaction = db.transaction([this.storeName], 'readwrite');
        const store = transaction.objectStore(this.storeName);
        const request = store.put(value);
        
        request.onsuccess = () => resolve(true);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      this.cacheManager.handleError(`IndexedDB set 失败: ${key}`, error);
      return false;
    }
  }

  async delete(key) {
    try {
      const db = await this.getDB();
      
      return new Promise((resolve, reject) => {
        const transaction = db.transaction([this.storeName], 'readwrite');
        const store = transaction.objectStore(this.storeName);
        const request = store.delete(key);
        
        request.onsuccess = () => resolve(true);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      this.cacheManager.handleError(`IndexedDB delete 失败: ${key}`, error);
      return false;
    }
  }

  async clear() {
    try {
      const db = await this.getDB();
      
      return new Promise((resolve, reject) => {
        const transaction = db.transaction([this.storeName], 'readwrite');
        const store = transaction.objectStore(this.storeName);
        const request = store.clear();
        
        request.onsuccess = () => resolve(true);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      this.cacheManager.handleError('IndexedDB clear 失败', error);
      return false;
    }
  }

  async keys() {
    try {
      const db = await this.getDB();
      
      return new Promise((resolve, reject) => {
        const transaction = db.transaction([this.storeName], 'readonly');
        const store = transaction.objectStore(this.storeName);
        const request = store.getAllKeys();
        
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      this.cacheManager.handleError('IndexedDB keys 失败', error);
      return [];
    }
  }

  async size() {
    try {
      const db = await this.getDB();
      
      return new Promise((resolve, reject) => {
        const transaction = db.transaction([this.storeName], 'readonly');
        const store = transaction.objectStore(this.storeName);
        const request = store.count();
        
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      this.cacheManager.handleError('IndexedDB size 失败', error);
      return 0;
    }
  }

  async cleanupExpired() {
    try {
      const db = await this.getDB();
      const now = Date.now();
      
      return new Promise((resolve, reject) => {
        const transaction = db.transaction([this.storeName], 'readwrite');
        const store = transaction.objectStore(this.storeName);
        const index = store.index('expiresAt');
        
        // 查询所有已过期的条目 (expiresAt > 0 且 expiresAt < now)
        const range = IDBKeyRange.bound(1, now);
        const request = index.openCursor(range);
        const deletedKeys = [];
        
        request.onsuccess = (event) => {
          const cursor = event.target.result;
          
          if (cursor) {
            deletedKeys.push(cursor.value.key);
            cursor.delete();
            cursor.continue();
          } else {
            // 通知所有被删除的键
            for (const key of deletedKeys) {
              this.cacheManager.notifyCacheEvict(key, 'expired', 'indexedDB');
            }
            
            resolve();
          }
        };
        
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      this.cacheManager.handleError('IndexedDB 清理过期缓存失败', error);
    }
  }

  async exportData() {
    try {
      const db = await this.getDB();
      
      return new Promise((resolve, reject) => {
        const transaction = db.transaction([this.storeName], 'readonly');
        const store = transaction.objectStore(this.storeName);
        const request = store.getAll();
        
        request.onsuccess = () => {
          const data = {};
          request.result.forEach(item => {
            data[item.key] = item;
          });
          resolve(data);
        };
        
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      this.cacheManager.handleError('IndexedDB 导出失败', error);
      return {};
    }
  }

  async importData(data, options = {}) {
    try {
      const db = await this.getDB();
      
      return new Promise((resolve, reject) => {
        const transaction = db.transaction([this.storeName], 'readwrite');
        const store = transaction.objectStore(this.storeName);
        
        // 如果 options.overwrite 为 true，则先清空现有数据
        if (options.overwrite) {
          const clearRequest = store.clear();
          
          clearRequest.onsuccess = () => {
            this.importDataEntries(store, data, resolve, reject);
          };
          
          clearRequest.onerror = () => reject(clearRequest.error);
        } else {
          this.importDataEntries(store, data, resolve, reject);
        }
      });
    } catch (error) {
      this.cacheManager.handleError('IndexedDB 导入失败', error);
      return false;
    }
  }

  importDataEntries(store, data, resolve, reject) {
    let count = 0;
    const total = Object.keys(data).length;
    
    if (total === 0) {
      resolve(true);
      return;
    }
    
    for (const [key, value] of Object.entries(data)) {
      const request = store.put(value);
      
      request.onsuccess = () => {
        count++;
        if (count === total) {
          resolve(true);
        }
      };
      
      request.onerror = () => {
        reject(request.error);
      };
    }
  }
}

// 内存缓存引擎
class MemoryCacheEngine {
  constructor(config, cacheManager) {
    this.config = config;
    this.cacheManager = cacheManager;
    this.cache = new Map();
    this.maxSize = config.memoryCacheMaxSize;
  }

  async get(key) {
    try {
      const item = this.cache.get(key);
      
      if (!item) {
        return null;
      }
      
      return item;
    } catch (error) {
      this.cacheManager.handleError(`MemoryCache get 失败: ${key}`, error);
      return null;
    }
  }

  async set(key, value) {
    try {
      // 检查是否需要执行缓存淘汰
      if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
        this.evictItem();
      }
      
      this.cache.set(key, value);
      return true;
    } catch (error) {
      this.cacheManager.handleError(`MemoryCache set 失败: ${key}`, error);
      return false;
    }
  }

  async delete(key) {
    try {
      return this.cache.delete(key);
    } catch (error) {
      this.cacheManager.handleError(`MemoryCache delete 失败: ${key}`, error);
      return false;
    }
  }

  async clear() {
    try {
      this.cache.clear();
      return true;
    } catch (error) {
      this.cacheManager.handleError('MemoryCache clear 失败', error);
      return false;
    }
  }

  async keys() {
    try {
      return Array.from(this.cache.keys());
    } catch (error) {
      this.cacheManager.handleError('MemoryCache keys 失败', error);
      return [];
    }
  }

  async size() {
    return this.cache.size;
  }

  async cleanupExpired() {
    try {
      const now = Date.now();
      const expiredKeys = [];
      
      this.cache.forEach((value, key) => {
        if (value && value.expiresAt && value.expiresAt > 0 && now > value.expiresAt) {
          expiredKeys.push(key);
        }
      });
      
      for (const key of expiredKeys) {
        this.cache.delete(key);
        this.cacheManager.notifyCacheEvict(key, 'expired', 'memoryCache');
      }
    } catch (error) {
      this.cacheManager.handleError('MemoryCache 清理过期缓存失败', error);
    }
  }

  async exportData() {
    try {
      const data = {};
      this.cache.forEach((value, key) => {
        data[key] = value;
      });
      return data;
    } catch (error) {
      this.cacheManager.handleError('MemoryCache 导出失败', error);
      return {};
    }
  }

  async importData(data, options = {}) {
    try {
      // 如果 options.overwrite 为 true，则先清空现有数据
      if (options.overwrite) {
        this.cache.clear();
      }
      
      // 检查是否会超过最大容量
      const totalSize = this.cache.size + Object.keys(data).length;
      if (totalSize > this.maxSize) {
        // 计算需要淘汰的项目数量
        const itemsToEvict = totalSize - this.maxSize;
        
        // 执行淘汰
        for (let i = 0; i < itemsToEvict; i++) {
          this.evictItem();
        }
      }
      
      // 导入数据
      for (const [key, value] of Object.entries(data)) {
        this.cache.set(key, value);
      }
      
      return true;
    } catch (error) {
      this.cacheManager.handleError('MemoryCache 导入失败', error);
      return false;
    }
  }

  /**
   * 使用 LRU 策略淘汰项目
   */
  evictItem() {
    // 找到最早访问的项目
    let oldestKey = null;
    let oldestTime = Infinity;
    
    this.cache.forEach((value, key) => {
      if (value && value.lastAccessTime < oldestTime) {
        oldestTime = value.lastAccessTime;
        oldestKey = key;
      }
    });
    
    // 删除最早访问的项目
    if (oldestKey !== null) {
      this.cache.delete(oldestKey);
      this.cacheManager.notifyCacheEvict(oldestKey, 'evicted', 'memoryCache');
    }
  }
}

// 创建缓存管理器实例
const cacheManager = new CacheManager({
  storageTypes: {
    localStorage: true,
    sessionStorage: true,
    indexedDB: true,
    memoryCache: true
  },
  defaultStorageType: 'localStorage',
  memoryCacheMaxSize: 100,
  defaultTTL: 3600000,
  staleWhileRevalidate: true,
  cacheVersion: '1.0.0',
  enableVersioning: true,
  debug: false
});

// 导出
if (typeof window !== 'undefined') {
  window.CacheManager = CacheManager;
  window.cacheManager = cacheManager;
}

export { CacheManager, cacheManager };