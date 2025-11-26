#!/usr/bin/env node

/**
 * MTSCOS AI 系统 - 安全机制配置页面
 * 统一管理系统中的所有安全机制配置，支持动态触发和响应
 */

const fs = require('fs');
const path = require('path');
const express = require('express');
const bodyParser = require('body-parser');
const EventEmitter = require('events');

// 引入安全机制模块
const { RollingCodeLock } = require('./rolling-code-lock');

class SecurityMechanismConfigManager extends EventEmitter {
  constructor(options = {}) {
    super();
    
    // 默认配置
    this.defaultOptions = {
      configPath: path.join(__dirname, '..', '..', 'Config', 'security-mechanisms.json'),
      logPath: path.join(__dirname, '..', '..', 'Logs', 'Security', 'mechanism-config.log'),
      port: 3003,
      host: '127.0.0.1',
      authRequired: true,
      enableAPI: true
    };
    
    // 合并配置
    this.options = { ...this.defaultOptions, ...options };
    
    // 初始化状态
    this.state = {
      mechanisms: new Map(), // 存储所有安全机制实例
      configs: {}, // 存储所有配置
      isInitialized: false,
      apiServer: null,
      activeSessions: new Map(),
      auditLog: []
    };
    
    // 初始化预定义的安全机制类型
    this.mechanismTypes = {
      rollingCodeLock: {
        name: '滚码锁机制',
        description: '防止数据传输被截留和篡改的滚码安全机制',
        factory: (config) => new RollingCodeLock(config),
        defaultConfig: {
          algorithm: 'aes-256-gcm',
          keyLength: 32,
          ivLength: 16,
          codeLength: 8,
          maxDrift: 1000,
          resyncThreshold: 10,
          replayWindowSize: 100,
          refreshInterval: 30000
        }
      },
      // 可以在这里添加更多安全机制类型
    };
    
    // 初始化
    this.initialize();
  }

  /**
   * 初始化配置管理器
   */
  initialize() {
    try {
      // 确保配置目录存在
      this.ensureDirectories();
      
      // 加载配置
      this.loadAllConfigurations();
      
      // 初始化安全机制实例
      this.initializeMechanisms();
      
      // 设置API服务器（如果启用）
      if (this.options.enableAPI) {
        this.setupAPIServer();
      }
      
      // 设置事件监听
      this.setupEventListeners();
      
      this.state.isInitialized = true;
      console.log('安全机制配置管理器初始化完成');
      
      // 触发初始化完成事件
      this.emit('initialized');
      
    } catch (error) {
      console.error('安全机制配置管理器初始化失败:', error.message);
      this.logError('初始化失败', error);
      throw error;
    }
  }

  /**
   * 确保必要的目录存在
   */
  ensureDirectories() {
    try {
      // 确保配置目录存在
      const configDir = path.dirname(this.options.configPath);
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }
      
      // 确保日志目录存在
      const logDir = path.dirname(this.options.logPath);
      if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
      }
      
    } catch (error) {
      console.error('创建必要目录失败:', error.message);
      throw error;
    }
  }

  /**
   * 加载所有配置
   */
  loadAllConfigurations() {
    try {
      if (fs.existsSync(this.options.configPath)) {
        const configContent = fs.readFileSync(this.options.configPath, 'utf8');
        this.state.configs = JSON.parse(configContent);
        console.log(`已加载 ${Object.keys(this.state.configs).length} 个安全机制配置`);
      } else {
        // 创建默认配置文件
        this.state.configs = this.createDefaultConfigurations();
        this.saveAllConfigurations();
        console.log('已创建默认安全机制配置');
      }
      
    } catch (error) {
      console.error('加载配置失败:', error.message);
      // 使用默认配置
      this.state.configs = this.createDefaultConfigurations();
    }
  }

  /**
   * 创建默认配置
   */
  createDefaultConfigurations() {
    const defaultConfigs = {};
    
    // 为每种机制类型创建默认配置
    for (const [type, info] of Object.entries(this.mechanismTypes)) {
      defaultConfigs[`${type}_default`] = {
        type: type,
        name: `${info.name} (默认)`,
        description: `${info.description} - 默认配置`,
        config: info.defaultConfig,
        enabled: true,
        priority: 100,
        lastModified: Date.now(),
        created: Date.now(),
        version: '1.0'
      };
    }
    
    return defaultConfigs;
  }

  /**
   * 保存所有配置
   */
  saveAllConfigurations() {
    try {
      fs.writeFileSync(
        this.options.configPath,
        JSON.stringify(this.state.configs, null, 2),
        'utf8'
      );
      console.log('安全机制配置已保存');
      
    } catch (error) {
      console.error('保存配置失败:', error.message);
      this.logError('保存配置失败', error);
      throw error;
    }
  }

  /**
   * 初始化安全机制实例
   */
  initializeMechanisms() {
    try {
      // 清除现有实例
      this.state.mechanisms.clear();
      
      // 初始化每个启用的机制
      for (const [mechanismId, config] of Object.entries(this.state.configs)) {
        if (config.enabled && this.mechanismTypes[config.type]) {
          try {
            const mechanismFactory = this.mechanismTypes[config.type].factory;
            const mechanism = mechanismFactory(config.config);
            
            // 设置机制ID
            mechanism.id = mechanismId;
            
            // 保存实例
            this.state.mechanisms.set(mechanismId, mechanism);
            
            console.log(`已初始化安全机制: ${mechanismId} (${config.type})`);
            
            // 监听机制事件
            this.setupMechanismEventListeners(mechanismId, mechanism);
            
          } catch (error) {
            console.error(`初始化安全机制失败 [${mechanismId}]:`, error.message);
            this.logError(`初始化机制失败 [${mechanismId}]`, error);
          }
        }
      }
      
    } catch (error) {
      console.error('初始化安全机制失败:', error.message);
      throw error;
    }
  }

  /**
   * 设置机制事件监听
   */
  setupMechanismEventListeners(mechanismId, mechanism) {
    // 监听错误事件
    mechanism.on('error', (error) => {
      console.error(`安全机制错误 [${mechanismId}]:`, error.message);
      this.logError(`机制错误 [${mechanismId}]`, error);
      
      // 转发事件
      this.emit(`mechanism:${mechanismId}:error`, { mechanismId, error });
    });
    
    // 监听安全事件
    mechanism.on('security_breach', (breachInfo) => {
      console.error(`安全入侵检测 [${mechanismId}]:`, breachInfo);
      this.logSecurityIncident(mechanismId, breachInfo);
      
      // 转发事件
      this.emit(`mechanism:${mechanismId}:security_breach`, { mechanismId, breachInfo });
      this.emit('security_breach', { mechanismId, breachInfo });
    });
    
    // 监听配置更新事件
    mechanism.on('configUpdated', (updateInfo) => {
      console.log(`机制配置已更新 [${mechanismId}]:`, updateInfo);
      this.logAuditEvent('config_updated', { mechanismId, updates: updateInfo.updates });
    });
    
    // 监听加密解密事件
    if (mechanism.on) {
      mechanism.on('encrypted', (encryptInfo) => {
        this.logAuditEvent('data_encrypted', { mechanismId, ...encryptInfo });
      });
      
      mechanism.on('decrypted', (decryptInfo) => {
        this.logAuditEvent('data_decrypted', { mechanismId, ...decryptInfo });
      });
    }
  }

  /**
   * 设置全局事件监听
   */
  setupEventListeners() {
    // 监听安全入侵事件
    this.on('security_breach', (breachInfo) => {
      // 触发安全响应机制
      this.triggerSecurityResponse(breachInfo);
    });
    
    // 监听配置更新事件
    this.on('configUpdated', (updateInfo) => {
      // 重新初始化受影响的机制
      if (updateInfo.mechanismId) {
        this.restartMechanism(updateInfo.mechanismId);
      }
    });
  }

  /**
   * 设置API服务器
   */
  setupAPIServer() {
    try {
      const app = express();
      
      // 中间件
      app.use(bodyParser.json({ limit: '10mb' }));
      app.use(bodyParser.urlencoded({ extended: true }));
      
      // 安全头部
      app.use((req, res, next) => {
        res.setHeader('X-Content-Type-Options', 'nosniff');
        res.setHeader('X-Frame-Options', 'DENY');
        res.setHeader('X-XSS-Protection', '1; mode=block');
        res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
        next();
      });
      
      // 认证中间件（简化版）
      if (this.options.authRequired) {
        app.use((req, res, next) => {
          const authHeader = req.headers.authorization;
          
          // 简单的API密钥认证（实际应使用更安全的认证方式）
          if (authHeader && authHeader.startsWith('Bearer ') && authHeader.split(' ')[1] === 'admin123') {
            next();
          } else {
            res.status(401).json({ error: '未授权访问' });
          }
        });
      }
      
      // API路由
      this.setupAPIRoutes(app);
      
      // 启动服务器
      this.state.apiServer = app.listen(this.options.port, this.options.host, () => {
        console.log(`安全机制配置API服务器运行在 http://${this.options.host}:${this.options.port}`);
      });
      
      // 处理服务器错误
      this.state.apiServer.on('error', (error) => {
        console.error('API服务器错误:', error.message);
        this.logError('API服务器错误', error);
      });
      
    } catch (error) {
      console.error('设置API服务器失败:', error.message);
      throw error;
    }
  }

  /**
   * 设置API路由
   */
  setupAPIRoutes(app) {
    // 获取所有机制配置
    app.get('/api/mechanisms', (req, res) => {
      try {
        res.json({
          success: true,
          mechanisms: this.state.configs,
          activeCount: this.state.mechanisms.size
        });
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });
    
    // 获取单个机制配置
    app.get('/api/mechanisms/:mechanismId', (req, res) => {
      try {
        const { mechanismId } = req.params;
        const config = this.state.configs[mechanismId];
        
        if (!config) {
          return res.status(404).json({ success: false, error: '机制配置不存在' });
        }
        
        // 获取机制状态
        const mechanism = this.state.mechanisms.get(mechanismId);
        const status = mechanism ? mechanism.getSecurityStatus() : null;
        
        res.json({
          success: true,
          config: config,
          status: status,
          active: !!mechanism
        });
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });
    
    // 创建新机制配置
    app.post('/api/mechanisms', (req, res) => {
      try {
        const { type, name, description, config } = req.body;
        
        // 验证类型
        if (!this.mechanismTypes[type]) {
          return res.status(400).json({ success: false, error: '不支持的机制类型' });
        }
        
        // 生成唯一ID
        const mechanismId = `${type}_${Date.now()}`;
        
        // 创建配置
        const newConfig = {
          id: mechanismId,
          type: type,
          name: name || `${this.mechanismTypes[type].name} (${mechanismId})`,
          description: description || this.mechanismTypes[type].description,
          config: { ...this.mechanismTypes[type].defaultConfig, ...config },
          enabled: true,
          priority: 100,
          lastModified: Date.now(),
          created: Date.now(),
          version: '1.0'
        };
        
        // 保存配置
        this.state.configs[mechanismId] = newConfig;
        this.saveAllConfigurations();
        
        // 初始化机制
        this.initializeMechanism(mechanismId, newConfig);
        
        res.status(201).json({
          success: true,
          message: '机制配置创建成功',
          mechanismId: mechanismId,
          config: newConfig
        });
        
        // 记录审计日志
        this.logAuditEvent('mechanism_created', { mechanismId, type, name });
        
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });
    
    // 更新机制配置
    app.put('/api/mechanisms/:mechanismId', (req, res) => {
      try {
        const { mechanismId } = req.params;
        const updates = req.body;
        
        // 检查机制是否存在
        if (!this.state.configs[mechanismId]) {
          return res.status(404).json({ success: false, error: '机制配置不存在' });
        }
        
        // 更新配置
        const config = this.state.configs[mechanismId];
        
        // 合并配置更新
        if (updates.config) {
          config.config = { ...config.config, ...updates.config };
          delete updates.config;
        }
        
        // 更新其他字段
        Object.assign(config, updates, { lastModified: Date.now() });
        
        // 保存配置
        this.saveAllConfigurations();
        
        // 重新初始化机制
        this.restartMechanism(mechanismId);
        
        res.json({
          success: true,
          message: '机制配置更新成功',
          mechanismId: mechanismId,
          config: config
        });
        
        // 记录审计日志
        this.logAuditEvent('mechanism_updated', { mechanismId, updates: Object.keys(updates) });
        
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });
    
    // 删除机制配置
    app.delete('/api/mechanisms/:mechanismId', (req, res) => {
      try {
        const { mechanismId } = req.params;
        
        // 检查机制是否存在
        if (!this.state.configs[mechanismId]) {
          return res.status(404).json({ success: false, error: '机制配置不存在' });
        }
        
        // 停止机制
        this.stopMechanism(mechanismId);
        
        // 删除配置
        delete this.state.configs[mechanismId];
        this.saveAllConfigurations();
        
        res.json({
          success: true,
          message: '机制配置删除成功',
          mechanismId: mechanismId
        });
        
        // 记录审计日志
        this.logAuditEvent('mechanism_deleted', { mechanismId });
        
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });
    
    // 触发机制动作
    app.post('/api/mechanisms/:mechanismId/trigger', (req, res) => {
      try {
        const { mechanismId } = req.params;
        const { action, params } = req.body;
        
        // 检查机制是否存在且激活
        const mechanism = this.state.mechanisms.get(mechanismId);
        if (!mechanism) {
          return res.status(404).json({ success: false, error: '机制不存在或未激活' });
        }
        
        // 触发动作
        const result = this.triggerMechanismAction(mechanismId, action, params);
        
        res.json({
          success: true,
          message: '机制动作触发成功',
          mechanismId: mechanismId,
          action: action,
          result: result
        });
        
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });
    
    // 获取机制状态
    app.get('/api/mechanisms/:mechanismId/status', (req, res) => {
      try {
        const { mechanismId } = req.params;
        
        // 检查机制是否存在且激活
        const mechanism = this.state.mechanisms.get(mechanismId);
        if (!mechanism) {
          return res.status(404).json({ success: false, error: '机制不存在或未激活' });
        }
        
        // 获取状态
        const status = mechanism.getSecurityStatus();
        
        res.json({
          success: true,
          mechanismId: mechanismId,
          status: status
        });
        
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });
    
    // 获取安全报告
    app.get('/api/reports/security', (req, res) => {
      try {
        const report = this.generateSecurityReport();
        
        res.json({
          success: true,
          report: report
        });
        
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });
    
    // 批量操作
    app.post('/api/mechanisms/batch', (req, res) => {
      try {
        const { operation, mechanismIds, params } = req.body;
        const results = [];
        
        if (!Array.isArray(mechanismIds)) {
          return res.status(400).json({ success: false, error: 'mechanismIds必须是数组' });
        }
        
        switch (operation) {
          case 'enable':
            mechanismIds.forEach(id => {
              if (this.state.configs[id]) {
                this.state.configs[id].enabled = true;
                this.initializeMechanism(id, this.state.configs[id]);
                results.push({ id, success: true });
              } else {
                results.push({ id, success: false, error: '不存在' });
              }
            });
            break;
            
          case 'disable':
            mechanismIds.forEach(id => {
              if (this.state.configs[id]) {
                this.state.configs[id].enabled = false;
                this.stopMechanism(id);
                results.push({ id, success: true });
              } else {
                results.push({ id, success: false, error: '不存在' });
              }
            });
            break;
            
          case 'restart':
            mechanismIds.forEach(id => {
              try {
                this.restartMechanism(id);
                results.push({ id, success: true });
              } catch (error) {
                results.push({ id, success: false, error: error.message });
              }
            });
            break;
            
          default:
            return res.status(400).json({ success: false, error: '不支持的批量操作' });
        }
        
        // 如果有配置更改，保存
        if (operation === 'enable' || operation === 'disable') {
          this.saveAllConfigurations();
        }
        
        res.json({
          success: true,
          operation: operation,
          results: results
        });
        
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });
    
    // 健康检查
    app.get('/api/health', (req, res) => {
      res.json({
        success: true,
        status: 'healthy',
        timestamp: Date.now(),
        mechanisms: this.state.mechanisms.size,
        serverTime: new Date().toISOString()
      });
    });
    
    // 前端页面路由
    app.get('/config', (req, res) => {
      res.send(this.getConfigPageHTML());
    });
  }

  /**
   * 初始化单个机制
   */
  initializeMechanism(mechanismId, config) {
    try {
      // 如果已存在实例，先停止
      this.stopMechanism(mechanismId);
      
      // 检查机制类型
      if (!this.mechanismTypes[config.type]) {
        throw new Error(`不支持的机制类型: ${config.type}`);
      }
      
      // 只有启用的机制才初始化
      if (config.enabled) {
        const mechanismFactory = this.mechanismTypes[config.type].factory;
        const mechanism = mechanismFactory(config.config);
        
        // 设置机制ID
        mechanism.id = mechanismId;
        
        // 保存实例
        this.state.mechanisms.set(mechanismId, mechanism);
        
        console.log(`已初始化安全机制: ${mechanismId} (${config.type})`);
        
        // 监听机制事件
        this.setupMechanismEventListeners(mechanismId, mechanism);
        
        return mechanism;
      }
      
    } catch (error) {
      console.error(`初始化安全机制失败 [${mechanismId}]:`, error.message);
      this.logError(`初始化机制失败 [${mechanismId}]`, error);
      throw error;
    }
  }

  /**
   * 停止单个机制
   */
  stopMechanism(mechanismId) {
    try {
      const mechanism = this.state.mechanisms.get(mechanismId);
      if (mechanism) {
        // 调用机制的shutdown方法（如果存在）
        if (typeof mechanism.shutdown === 'function') {
          mechanism.shutdown();
        }
        
        // 移除实例
        this.state.mechanisms.delete(mechanismId);
        
        console.log(`已停止安全机制: ${mechanismId}`);
        
        return true;
      }
      
      return false;
      
    } catch (error) {
      console.error(`停止安全机制失败 [${mechanismId}]:`, error.message);
      return false;
    }
  }

  /**
   * 重启单个机制
   */
  restartMechanism(mechanismId) {
    try {
      const config = this.state.configs[mechanismId];
      if (!config) {
        throw new Error(`机制配置不存在: ${mechanismId}`);
      }
      
      console.log(`重启安全机制: ${mechanismId}`);
      
      // 重新初始化
      return this.initializeMechanism(mechanismId, config);
      
    } catch (error) {
      console.error(`重启安全机制失败 [${mechanismId}]:`, error.message);
      throw error;
    }
  }

  /**
   * 触发机制动作
   */
  triggerMechanismAction(mechanismId, action, params = {}) {
    try {
      const mechanism = this.state.mechanisms.get(mechanismId);
      if (!mechanism) {
        throw new Error(`机制不存在或未激活: ${mechanismId}`);
      }
      
      console.log(`触发机制动作: ${mechanismId}.${action}`);
      
      // 如果机制有trigger方法，使用它
      if (typeof mechanism.triggerSecurityMechanism === 'function') {
        return mechanism.triggerSecurityMechanism(mechanismId, action, params);
      }
      
      // 尝试直接调用方法
      if (typeof mechanism[action] === 'function') {
        return mechanism[action](params);
      }
      
      // 触发事件
      this.emit(`mechanism:${mechanismId}:${action}`, { params });
      
      return { success: true, message: `事件已触发: ${action}` };
      
    } catch (error) {
      console.error(`触发机制动作失败 [${mechanismId}.${action}]:`, error.message);
      throw error;
    }
  }

  /**
   * 触发安全响应
   */
  triggerSecurityResponse(breachInfo) {
    try {
      console.log('触发安全响应机制:', breachInfo);
      
      // 根据入侵类型采取不同的响应措施
      switch (breachInfo.breachInfo.type) {
        case 'invalid_rolling_code':
        case 'replay_attack':
          // 临时提高安全级别
          this.adjustSecurityLevel('high', 300000); // 5分钟
          break;
          
        case 'handshake_failed':
          // 拒绝连接尝试
          this.trackFailedAttempts(breachInfo.breachInfo.senderId);
          break;
          
        case 'invalid_signature':
          // 紧急重置密钥
          this.emergencyReset();
          break;
      }
      
    } catch (error) {
      console.error('触发安全响应失败:', error.message);
      this.logError('安全响应失败', error);
    }
  }

  /**
   * 调整安全级别
   */
  adjustSecurityLevel(level, duration) {
    console.log(`调整安全级别为: ${level}，持续时间: ${duration}ms`);
    
    // 更新所有机制的配置
    for (const [mechanismId, mechanism] of this.state.mechanisms.entries()) {
      if (mechanism.config && mechanism.config.maxDrift !== undefined) {
        // 保存原始配置
        this.state.originalConfigs = this.state.originalConfigs || {};
        if (!this.state.originalConfigs[mechanismId]) {
          this.state.originalConfigs[mechanismId] = {
            maxDrift: mechanism.config.maxDrift,
            replayWindowSize: mechanism.config.replayWindowSize
          };
        }
        
        // 调整安全参数
        mechanism.config.maxDrift = level === 'high' ? 500 : 1000;
        mechanism.config.replayWindowSize = level === 'high' ? 200 : 100;
        
        console.log(`已调整机制 [${mechanismId}] 的安全参数`);
      }
    }
    
    // 设置定时器恢复原始配置
    setTimeout(() => {
      this.restoreOriginalSecuritySettings();
    }, duration);
  }

  /**
   * 恢复原始安全设置
   */
  restoreOriginalSecuritySettings() {
    console.log('恢复原始安全设置');
    
    if (this.state.originalConfigs) {
      for (const [mechanismId, originalConfig] of Object.entries(this.state.originalConfigs)) {
        const mechanism = this.state.mechanisms.get(mechanismId);
        if (mechanism && mechanism.config) {
          mechanism.config.maxDrift = originalConfig.maxDrift;
          mechanism.config.replayWindowSize = originalConfig.replayWindowSize;
        }
      }
      
      // 清除原始配置缓存
      this.state.originalConfigs = null;
    }
  }

  /**
   * 跟踪失败尝试
   */
  trackFailedAttempts(sourceId) {
    // 简单的失败尝试跟踪
    this.state.failedAttempts = this.state.failedAttempts || new Map();
    
    const currentCount = this.state.failedAttempts.get(sourceId) || 0;
    const newCount = currentCount + 1;
    
    this.state.failedAttempts.set(sourceId, newCount);
    
    console.log(`来源 [${sourceId}] 的失败尝试次数: ${newCount}`);
    
    // 如果失败次数过多，可能需要采取更严格的措施
    if (newCount >= 5) {
      console.warn(`来源 [${sourceId}] 失败尝试次数过多，可能存在攻击`);
      // 这里可以实现IP封禁等措施
    }
  }

  /**
   * 紧急重置
   */
  emergencyReset() {
    console.log('执行安全紧急重置');
    
    // 重置所有机制
    for (const [mechanismId, mechanism] of this.state.mechanisms.entries()) {
      if (typeof mechanism.emergencyShutdown === 'function') {
        mechanism.emergencyShutdown('security_breach');
      }
    }
    
    // 重新初始化所有机制
    this.initializeMechanisms();
    
    // 记录紧急事件
    this.logSecurityIncident('system', { type: 'emergency_reset', reason: 'security_breach' });
  }

  /**
   * 生成安全报告
   */
  generateSecurityReport() {
    const report = {
      timestamp: Date.now(),
      summary: {
        totalMechanisms: Object.keys(this.state.configs).length,
        activeMechanisms: this.state.mechanisms.size,
        securityLevel: 'normal',
        lastIncident: null
      },
      mechanisms: {},
      incidents: this.getRecentSecurityIncidents(),
      version: '1.0'
    };
    
    // 收集每个机制的状态
    for (const [mechanismId, mechanism] of this.state.mechanisms.entries()) {
      try {
        if (typeof mechanism.getSecurityStatus === 'function') {
          report.mechanisms[mechanismId] = mechanism.getSecurityStatus();
        }
      } catch (error) {
        console.error(`获取机制状态失败 [${mechanismId}]:`, error.message);
      }
    }
    
    // 分析安全事件确定安全级别
    if (report.incidents && report.incidents.length > 0) {
      const recentIncidents = report.incidents.filter(inc => {
        return Date.now() - inc.timestamp < 3600000; // 1小时内
      });
      
      if (recentIncidents.length > 0) {
        report.summary.securityLevel = 'high';
        report.summary.lastIncident = recentIncidents[0].timestamp;
      }
    }
    
    return report;
  }

  /**
   * 获取最近的安全事件
   */
  getRecentSecurityIncidents(limit = 10) {
    // 从日志文件中读取最近的安全事件
    try {
      const incidentLogPath = path.join(path.dirname(this.options.logPath), 'security-incidents.log');
      
      if (fs.existsSync(incidentLogPath)) {
        const logs = fs.readFileSync(incidentLogPath, 'utf8')
          .split('\n')
          .filter(line => line.trim())
          .map(line => JSON.parse(line))
          .sort((a, b) => b.timestamp - a.timestamp)
          .slice(0, limit);
        
        return logs;
      }
      
    } catch (error) {
      console.error('读取安全事件日志失败:', error.message);
    }
    
    return [];
  }

  /**
   * 记录安全事件
   */
  logSecurityIncident(mechanismId, incidentInfo) {
    try {
      const incidentLogPath = path.join(path.dirname(this.options.logPath), 'security-incidents.log');
      
      const incident = {
        timestamp: Date.now(),
        mechanismId: mechanismId,
        type: incidentInfo.type,
        details: incidentInfo,
        severity: this.determineSeverity(incidentInfo.type)
      };
      
      fs.appendFileSync(incidentLogPath, JSON.stringify(incident) + '\n', 'utf8');
      
      // 只保留最近的审计日志
      this.state.auditLog.unshift(incident);
      if (this.state.auditLog.length > 1000) {
        this.state.auditLog = this.state.auditLog.slice(0, 1000);
      }
      
    } catch (error) {
      console.error('记录安全事件失败:', error.message);
    }
  }

  /**
   * 确定事件严重程度
   */
  determineSeverity(type) {
    const severityMap = {
      'replay_attack': 'high',
      'invalid_signature': 'high',
      'handshake_failed': 'medium',
      'invalid_rolling_code': 'medium',
      'timestamp_drift': 'low'
    };
    
    return severityMap[type] || 'unknown';
  }

  /**
   * 记录审计事件
   */
  logAuditEvent(action, details) {
    try {
      const auditLogPath = path.join(path.dirname(this.options.logPath), 'audit.log');
      
      const auditEvent = {
        timestamp: Date.now(),
        action: action,
        details: details
      };
      
      fs.appendFileSync(auditLogPath, JSON.stringify(auditEvent) + '\n', 'utf8');
      
    } catch (error) {
      console.error('记录审计事件失败:', error.message);
    }
  }

  /**
   * 记录错误日志
   */
  logError(message, error) {
    try {
      const logEntry = {
        timestamp: Date.now(),
        message: message,
        error: error.message,
        stack: error.stack
      };
      
      fs.appendFileSync(this.options.logPath, JSON.stringify(logEntry) + '\n', 'utf8');
      
    } catch (err) {
      console.error('写入错误日志失败:', err.message);
    }
  }

  /**
   * 获取配置页面HTML
   */
  getConfigPageHTML() {
    return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MTSCOS AI - 安全机制配置管理</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
      background-color: #1a1a1a;
      color: #e0e0e0;
      line-height: 1.6;
    }
    
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
    }
    
    header {
      background: linear-gradient(135deg, #2c3e50, #34495e);
      padding: 20px;
      border-radius: 10px;
      margin-bottom: 20px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    h1 {
      font-size: 24px;
      margin-bottom: 10px;
      color: #fff;
    }
    
    .subtitle {
      color: #bdc3c7;
      font-size: 14px;
    }
    
    .dashboard {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }
    
    .card {
      background: #2d2d2d;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
      transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    }
    
    .card h3 {
      font-size: 18px;
      margin-bottom: 10px;
      color: #3498db;
    }
    
    .card .value {
      font-size: 28px;
      font-weight: bold;
      color: #2ecc71;
    }
    
    .card .status {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      margin-top: 10px;
    }
    
    .status.normal {
      background-color: #27ae60;
      color: white;
    }
    
    .status.high {
      background-color: #e74c3c;
      color: white;
    }
    
    .tabs {
      display: flex;
      gap: 10px;
      margin-bottom: 20px;
      border-bottom: 2px solid #34495e;
      padding-bottom: 10px;
    }
    
    .tab {
      padding: 10px 20px;
      background: #34495e;
      border: none;
      border-radius: 6px;
      color: white;
      cursor: pointer;
      transition: background-color 0.3s;
    }
    
    .tab.active {
      background: #3498db;
    }
    
    .tab:hover:not(.active) {
      background: #4a6572;
    }
    
    .content {
      background: #2d2d2d;
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
    }
    
    th, td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid #444;
    }
    
    th {
      background: #34495e;
      color: #fff;
      font-weight: 600;
    }
    
    tr:hover {
      background: #3a3a3a;
    }
    
    .btn {
      padding: 8px 16px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
      transition: background-color 0.3s;
    }
    
    .btn-primary {
      background: #3498db;
      color: white;
    }
    
    .btn-primary:hover {
      background: #2980b9;
    }
    
    .btn-success {
      background: #27ae60;
      color: white;
    }
    
    .btn-success:hover {
      background: #229954;
    }
    
    .btn-danger {
      background: #e74c3c;
      color: white;
    }
    
    .btn-danger:hover {
      background: #c0392b;
    }
    
    .btn-warning {
      background: #f39c12;
      color: white;
    }
    
    .btn-warning:hover {
      background: #e67e22;
    }
    
    .form-group {
      margin-bottom: 15px;
    }
    
    label {
      display: block;
      margin-bottom: 5px;
      color: #bdc3c7;
      font-size: 14px;
    }
    
    input, select, textarea {
      width: 100%;
      padding: 10px;
      background: #3a3a3a;
      border: 1px solid #555;
      border-radius: 4px;
      color: #e0e0e0;
      font-size: 14px;
    }
    
    input:focus, select:focus, textarea:focus {
      outline: none;
      border-color: #3498db;
    }
    
    .modal {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.7);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
    }
    
    .modal-content {
      background: #2d2d2d;
      padding: 30px;
      border-radius: 10px;
      width: 90%;
      max-width: 600px;
      max-height: 80vh;
      overflow-y: auto;
    }
    
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }
    
    .modal-header h2 {
      color: #3498db;
      font-size: 20px;
    }
    
    .modal-close {
      background: none;
      border: none;
      color: #95a5a6;
      font-size: 24px;
      cursor: pointer;
    }
    
    .modal-close:hover {
      color: #e0e0e0;
    }
    
    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      margin-top: 20px;
    }
    
    .mechanism-actions {
      display: flex;
      gap: 5px;
    }
    
    .mechanism-status {
      padding: 2px 8px;
      border-radius: 3px;
      font-size: 12px;
      font-weight: 500;
    }
    
    .status-active {
      background: #27ae60;
      color: white;
    }
    
    .status-inactive {
      background: #7f8c8d;
      color: white;
    }
    
    .incident-severity {
      padding: 2px 8px;
      border-radius: 3px;
      font-size: 12px;
      font-weight: 500;
    }
    
    .severity-high {
      background: #e74c3c;
      color: white;
    }
    
    .severity-medium {
      background: #f39c12;
      color: white;
    }
    
    .severity-low {
      background: #2980b9;
      color: white;
    }
    
    .refresh-indicator {
      display: inline-block;
      width: 16px;
      height: 16px;
      border: 2px solid #3498db;
      border-top: 2px solid transparent;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-left: 10px;
    }
    
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    
    @media (max-width: 768px) {
      .dashboard {
        grid-template-columns: 1fr;
      }
      
      .tabs {
        flex-wrap: wrap;
      }
      
      .tab {
        flex: 1;
        min-width: 120px;
      }
      
      table {
        font-size: 14px;
      }
      
      th, td {
        padding: 8px;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>MTSCOS AI 安全机制配置管理系统</h1>
      <div class="subtitle">统一管理、监控和配置所有安全机制</div>
    </header>
    
    <div class="dashboard">
      <div class="card">
        <h3>安全机制总数</h3>
        <div class="value" id="total-mechanisms">0</div>
      </div>
      <div class="card">
        <h3>活跃机制</h3>
        <div class="value" id="active-mechanisms">0</div>
      </div>
      <div class="card">
        <h3>安全级别</h3>
        <div class="status" id="security-level">normal</div>
      </div>
      <div class="card">
        <h3>最近安全事件</h3>
        <div class="value" id="recent-incidents">0</div>
      </div>
    </div>
    
    <div class="tabs">
      <button class="tab active" data-tab="mechanisms">安全机制</button>
      <button class="tab" data-tab="security-incidents">安全事件</button>
      <button class="tab" data-tab="audit-log">审计日志</button>
      <button class="tab" data-tab="reports">安全报告</button>
      <button class="tab" data-tab="settings">系统设置</button>
    </div>
    
    <div class="content">
      <div id="tab-mechanisms" class="tab-content">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
          <h2>安全机制管理</h2>
          <button class="btn btn-primary" id="add-mechanism-btn">添加安全机制</button>
        </div>
        <table id="mechanisms-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>类型</th>
              <th>状态</th>
              <th>优先级</th>
              <th>最后修改</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <!-- 机制列表将通过JS动态生成 -->
          </tbody>
        </table>
      </div>
      
      <div id="tab-security-incidents" class="tab-content" style="display: none;">
        <h2>安全事件记录</h2>
        <table id="incidents-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>机制ID</th>
              <th>类型</th>
              <th>严重程度</th>
              <th>详情</th>
            </tr>
          </thead>
          <tbody>
            <!-- 事件列表将通过JS动态生成 -->
          </tbody>
        </table>
      </div>
      
      <div id="tab-audit-log" class="tab-content" style="display: none;">
        <h2>审计日志</h2>
        <table id="audit-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>操作</th>
              <th>详情</th>
            </tr>
          </thead>
          <tbody>
            <!-- 审计日志将通过JS动态生成 -->
          </tbody>
        </table>
      </div>
      
      <div id="tab-reports" class="tab-content" style="display: none;">
        <h2>安全报告</h2>
        <div id="security-report">
          <!-- 安全报告将通过JS动态生成 -->
        </div>
      </div>
      
      <div id="tab-settings" class="tab-content" style="display: none;">
        <h2>系统设置</h2>
        <form id="system-settings-form">
          <div class="form-group">
            <label for="api-port">API端口</label>
            <input type="number" id="api-port" value="3003" min="1" max="65535">
          </div>
          <div class="form-group">
            <label for="auth-required">启用认证</label>
            <select id="auth-required">
              <option value="true">是</option>
              <option value="false">否</option>
            </select>
          </div>
          <div class="form-group">
            <label for="log-level">日志级别</label>
            <select id="log-level">
              <option value="error">错误</option>
              <option value="warn">警告</option>
              <option value="info">信息</option>
              <option value="debug">调试</option>
            </select>
          </div>
          <div class="form-group">
            <label for="security-level">全局安全级别</label>
            <select id="global-security-level">
              <option value="normal">正常</option>
              <option value="high">高级</option>
              <option value="critical">最高</option>
            </select>
          </div>
          <button type="submit" class="btn btn-primary">保存设置</button>
        </form>
      </div>
    </div>
  </div>
  
  <!-- 添加机制模态框 -->
  <div id="add-mechanism-modal" class="modal" style="display: none;">
    <div class="modal-content">
      <div class="modal-header">
        <h2>添加安全机制</h2>
        <button class="modal-close" onclick="closeAddModal()">&times;</button>
      </div>
      <form id="add-mechanism-form">
        <div class="form-group">
          <label for="mechanism-type">机制类型</label>
          <select id="mechanism-type">
            <option value="rollingCodeLock">滚码锁机制</option>
            <!-- 其他机制类型将在这里添加 -->
          </select>
        </div>
        <div class="form-group">
          <label for="mechanism-name">名称</label>
          <input type="text" id="mechanism-name" placeholder="输入机制名称">
        </div>
        <div class="form-group">
          <label for="mechanism-description">描述</label>
          <textarea id="mechanism-description" rows="3" placeholder="输入机制描述"></textarea>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn" onclick="closeAddModal()">取消</button>
          <button type="submit" class="btn btn-primary">创建</button>
        </div>
      </form>
    </div>
  </div>
  
  <!-- 配置机制模态框 -->
  <div id="configure-mechanism-modal" class="modal" style="display: none;">
    <div class="modal-content">
      <div class="modal-header">
        <h2>配置安全机制</h2>
        <button class="modal-close" onclick="closeConfigureModal()">&times;</button>
      </div>
      <form id="configure-mechanism-form">
        <input type="hidden" id="configure-mechanism-id">
        <div class="form-group">
          <label for="configure-mechanism-name">名称</label>
          <input type="text" id="configure-mechanism-name">
        </div>
        <div class="form-group">
          <label for="configure-mechanism-description">描述</label>
          <textarea id="configure-mechanism-description" rows="3"></textarea>
        </div>
        <div class="form-group">
          <label for="configure-mechanism-enabled">启用</label>
          <select id="configure-mechanism-enabled">
            <option value="true">是</option>
            <option value="false">否</option>
          </select>
        </div>
        <div class="form-group">
          <label for="configure-mechanism-priority">优先级</label>
          <input type="number" id="configure-mechanism-priority" min="1" max="1000" value="100">
        </div>
        <!-- 机制特定配置将通过JS动态生成 -->
        <div class="modal-footer">
          <button type="button" class="btn" onclick="closeConfigureModal()">取消</button>
          <button type="submit" class="btn btn-primary">保存</button>
        </div>
      </form>
    </div>
  </div>
  
  <script>
    // API基础URL
    const API_BASE = '/api';
    
    // 当前活动标签
    let activeTab = 'mechanisms';
    
    // 页面加载时初始化
    document.addEventListener('DOMContentLoaded', () => {
      // 设置标签切换
      setupTabs();
      
      // 加载初始数据
      loadDashboardStats();
      loadMechanisms();
      
      // 设置表单事件
      setupForms();
    });
    
    // 设置标签切换
    function setupTabs() {
      const tabs = document.querySelectorAll('.tab');
      tabs.forEach(tab => {
        tab.addEventListener('click', () => {
          // 移除所有活动标签
          tabs.forEach(t => t.classList.remove('active'));
          
          // 隐藏所有内容
          document.querySelectorAll('.tab-content').forEach(content => {
            content.style.display = 'none';
          });
          
          // 激活当前标签
          tab.classList.add('active');
          activeTab = tab.dataset.tab;
          
          // 显示对应内容
          document.getElementById(`tab-${activeTab}`).style.display = 'block';
          
          // 加载对应数据
          loadTabData(activeTab);
        });
      });
    }
    
    // 加载标签数据
    function loadTabData(tab) {
      switch(tab) {
        case 'mechanisms':
          loadMechanisms();
          break;
        case 'security-incidents':
          loadSecurityIncidents();
          break;
        case 'audit-log':
          loadAuditLog();
          break;
        case 'reports':
          loadSecurityReport();
          break;
      }
    }
    
    // 加载仪表板统计
    async function loadDashboardStats() {
      try {
        const response = await fetch(`${API_BASE}/mechanisms`);
        const data = await response.json();
        
        if (data.success) {
          document.getElementById('total-mechanisms').textContent = Object.keys(data.mechanisms).length;
          document.getElementById('active-mechanisms').textContent = data.activeCount;
        }
        
        // 获取安全报告以更新安全级别
        const reportResponse = await fetch(`${API_BASE}/reports/security`);
        const reportData = await reportResponse.json();
        
        if (reportData.success) {
          const securityLevel = reportData.report.summary.securityLevel;
          const securityLevelEl = document.getElementById('security-level');
          securityLevelEl.textContent = securityLevel;
          securityLevelEl.className = `status ${securityLevel}`;
          
          const recentIncidents = reportData.report.incidents ? reportData.report.incidents.length : 0;
          document.getElementById('recent-incidents').textContent = recentIncidents;
        }
        
      } catch (error) {
        console.error('加载仪表板统计失败:', error);
      }
    }
    
    // 加载机制列表
    async function loadMechanisms() {
      try {
        const response = await fetch(`${API_BASE}/mechanisms`);
        const data = await response.json();
        
        if (data.success) {
          const tbody = document.querySelector('#mechanisms-table tbody');
          tbody.innerHTML = '';
          
          Object.entries(data.mechanisms).forEach(([id, config]) => {
            const row = document.createElement('tr');
            
            row.innerHTML = `
              <td>${id}</td>
              <td>${config.name}</td>
              <td>${config.type}</td>
              <td>
                <span class="mechanism-status status-${config.enabled ? 'active' : 'inactive'}">
                  ${config.enabled ? '活跃' : '非活跃'}
                </span>
              </td>
              <td>${config.priority}</td>
              <td>${new Date(config.lastModified).toLocaleString()}</td>
              <td>
                <div class="mechanism-actions">
                  <button class="btn btn-primary" onclick="showConfigureModal('${id}')">配置</button>
                  <button class="btn ${config.enabled ? 'btn-warning' : 'btn-success'}" onclick="toggleMechanism('${id}', ${!config.enabled})">
                    ${config.enabled ? '禁用' : '启用'}
                  </button>
                  <button class="btn btn-danger" onclick="deleteMechanism('${id}')">删除</button>
                  <button class="btn btn-secondary" onclick="viewMechanismStatus('${id}')">状态</button>
                </div>
              </td>
            `;
            
            tbody.appendChild(row);
          });
        }
        
      } catch (error) {
        console.error('加载机制列表失败:', error);
        showError('加载机制列表失败');
      }
    }
    
    // 加载安全事件
    async function loadSecurityIncidents() {
      try {
        const response = await fetch(`${API_BASE}/reports/security`);
        const data = await response.json();
        
        if (data.success && data.report.incidents) {
          const tbody = document.querySelector('#incidents-table tbody');
          tbody.innerHTML = '';
          
          data.report.incidents.forEach(incident => {
            const row = document.createElement('tr');
            
            row.innerHTML = `
              <td>${new Date(incident.timestamp).toLocaleString()}</td>
              <td>${incident.mechanismId}</td>
              <td>${incident.type}</td>
              <td>
                <span class="incident-severity severity-${incident.severity}">
                  ${getSeverityText(incident.severity)}
                </span>
              </td>
              <td>${JSON.stringify(incident.details)}</td>
            `;
            
            tbody.appendChild(row);
          });
        }
        
      } catch (error) {
        console.error('加载安全事件失败:', error);
        showError('加载安全事件失败');
      }
    }
    
    // 加载审计日志
    async function loadAuditLog() {
      // 这里应该从服务器获取审计日志
      const tbody = document.querySelector('#audit-table tbody');
      tbody.innerHTML = '<tr><td colspan="3">审计日志加载中...</td></tr>';
      
      // 模拟数据
      setTimeout(() => {
        tbody.innerHTML = `
          <tr>
            <td>${new Date().toLocaleString()}</td>
            <td>系统初始化</td>
            <td>安全机制配置管理器已启动</td>
          </tr>
        `;
      }, 1000);
    }
    
    // 加载安全报告
    async function loadSecurityReport() {
      try {
        const response = await fetch(`${API_BASE}/reports/security`);
        const data = await response.json();
        
        if (data.success) {
          const report = data.report;
          const reportEl = document.getElementById('security-report');
          
          reportEl.innerHTML = `
            <div class="card">
              <h3>安全摘要</h3>
              <p>报告生成时间: ${new Date(report.timestamp).toLocaleString()}</p>
              <p>总机制数: ${report.summary.totalMechanisms}</p>
              <p>活跃机制: ${report.summary.activeMechanisms}</p>
              <p>安全级别: <span class="status ${report.summary.securityLevel}">${getSecurityLevelText(report.summary.securityLevel)}</span></p>
            </div>
            
            <h3 style="margin-top: 20px;">机制状态详情</h3>
            <pre style="background: #1a1a1a; padding: 15px; border-radius: 5px; overflow-x: auto;">
              ${JSON.stringify(report.mechanisms, null, 2)}
            </pre>
          `;
        }
        
      } catch (error) {
        console.error('加载安全报告失败:', error);
        showError('加载安全报告失败');
      }
    }
    
    // 设置表单事件
    function setupForms() {
      // 添加机制表单
      document.getElementById('add-mechanism-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await submitAddMechanism();
      });
      
      // 配置机制表单
      document.getElementById('configure-mechanism-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await submitConfigureMechanism();
      });
      
      // 系统设置表单
      document.getElementById('system-settings-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        submitSystemSettings();
      });
      
      // 添加机制按钮
      document.getElementById('add-mechanism-btn').addEventListener('click', showAddModal);
    }
    
    // 显示添加机制模态框
    function showAddModal() {
      document.getElementById('add-mechanism-modal').style.display = 'flex';
    }
    
    // 关闭添加机制模态框
    function closeAddModal() {
      document.getElementById('add-mechanism-modal').style.display = 'none';
      document.getElementById('add-mechanism-form').reset();
    }
    
    // 提交添加机制
    async function submitAddMechanism() {
      try {
        const type = document.getElementById('mechanism-type').value;
        const name = document.getElementById('mechanism-name').value;
        const description = document.getElementById('mechanism-description').value;
        
        const response = await fetch(`${API_BASE}/mechanisms`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ type, name, description })
        });
        
        const data = await response.json();
        
        if (data.success) {
          closeAddModal();
          loadMechanisms();
          loadDashboardStats();
          showSuccess('机制创建成功');
        } else {
          showError(data.error || '创建机制失败');
        }
        
      } catch (error) {
        console.error('提交添加机制失败:', error);
        showError('创建机制失败');
      }
    }
    
    // 显示配置机制模态框
    function showConfigureModal(mechanismId) {
      const modal = document.getElementById('configure-mechanism-modal');
      modal.style.display = 'flex';
      
      // 加载机制配置
      loadMechanismConfig(mechanismId);
    }
    
    // 关闭配置机制模态框
    function closeConfigureModal() {
      document.getElementById('configure-mechanism-modal').style.display = 'none';
    }
    
    // 加载机制配置
    async function loadMechanismConfig(mechanismId) {
      try {
        const response = await fetch(`${API_BASE}/mechanisms/${mechanismId}`);
        const data = await response.json();
        
        if (data.success) {
          const config = data.config;
          
          document.getElementById('configure-mechanism-id').value = mechanismId;
          document.getElementById('configure-mechanism-name').value = config.name;
          document.getElementById('configure-mechanism-description').value = config.description;
          document.getElementById('configure-mechanism-enabled').value = config.enabled.toString();
          document.getElementById('configure-mechanism-priority').value = config.priority;
          
          // 动态生成机制特定配置（简化版）
          const configContainer = document.createElement('div');
          configContainer.id = 'mechanism-specific-config';
          configContainer.innerHTML = `
            <h3>机制特定配置</h3>
            <pre style="background: #1a1a1a; padding: 15px; border-radius: 5px; overflow-x: auto;">
              ${JSON.stringify(config.config, null, 2)}
            </pre>
          `;
          
          // 替换或添加到表单中
          const existing = document.getElementById('mechanism-specific-config');
          if (existing) {
            existing.replaceWith(configContainer);
          } else {
            const footer = document.querySelector('#configure-mechanism-form .modal-footer');
            document.getElementById('configure-mechanism-form').insertBefore(configContainer, footer);
          }
        }
        
      } catch (error) {
        console.error('加载机制配置失败:', error);
        showError('加载机制配置失败');
      }
    }
    
    // 提交配置机制
    async function submitConfigureMechanism() {
      try {
        const mechanismId = document.getElementById('configure-mechanism-id').value;
        const name = document.getElementById('configure-mechanism-name').value;
        const description = document.getElementById('configure-mechanism-description').value;
        const enabled = document.getElementById('configure-mechanism-enabled').value === 'true';
        const priority = parseInt(document.getElementById('configure-mechanism-priority').value);
        
        const response = await fetch(`${API_BASE}/mechanisms/${mechanismId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ name, description, enabled, priority })
        });
        
        const data = await response.json();
        
        if (data.success) {
          closeConfigureModal();
          loadMechanisms();
          loadDashboardStats();
          showSuccess('机制配置已更新');
        } else {
          showError(data.error || '更新配置失败');
        }
        
      } catch (error) {
        console.error('提交配置失败:', error);
        showError('更新配置失败');
      }
    }
    
    // 切换机制状态
    async function toggleMechanism(mechanismId, enable) {
      try {
        const response = await fetch(`${API_BASE}/mechanisms/${mechanismId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ enabled: enable })
        });
        
        const data = await response.json();
        
        if (data.success) {
          loadMechanisms();
          loadDashboardStats();
          showSuccess(enable ? '机制已启用' : '机制已禁用');
        } else {
          showError(data.error || '操作失败');
        }
        
      } catch (error) {
        console.error('切换机制状态失败:', error);
        showError('操作失败');
      }
    }
    
    // 删除机制
    async function deleteMechanism(mechanismId) {
      if (!confirm(`确定要删除机制 ${mechanismId} 吗？`)) {
        return;
      }
      
      try {
        const response = await fetch(`${API_BASE}/mechanisms/${mechanismId}`, {
          method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
          loadMechanisms();
          loadDashboardStats();
          showSuccess('机制已删除');
        } else {
          showError(data.error || '删除失败');
        }
        
      } catch (error) {
        console.error('删除机制失败:', error);
        showError('删除失败');
      }
    }
    
    // 查看机制状态
    async function viewMechanismStatus(mechanismId) {
      try {
        const response = await fetch(`${API_BASE}/mechanisms/${mechanismId}/status`);
        const data = await response.json();
        
        if (data.success) {
          alert(`机制 ${mechanismId} 状态:\n${JSON.stringify(data.status, null, 2)}`);
        } else {
          showError(data.error || '获取状态失败');
        }
        
      } catch (error) {
        console.error('获取机制状态失败:', error);
        showError('获取状态失败');
      }
    }
    
    // 提交系统设置
    function submitSystemSettings() {
      // 在实际应用中，这里应该将设置保存到服务器
      showSuccess('系统设置已保存');
    }
    
    // 显示成功消息
    function showSuccess(message) {
      alert(message);
    }
    
    // 显示错误消息
    function showError(message) {
      alert('错误: ' + message);
    }
    
    // 获取安全级别文本
    function getSecurityLevelText(level) {
      const levels = {
        normal: '正常',
        high: '高级',
        critical: '最高'
      };
      return levels[level] || level;
    }
    
    // 获取严重程度文本
    function getSeverityText(severity) {
      const severities = {
        high: '高',
        medium: '中',
        low: '低'
      };
      return severities[severity] || severity;
    }
  </script>
</body>
</html>
`;
  }

  /**
   * 关闭配置管理器
   */
  shutdown() {
    try {
      console.log('正在关闭安全机制配置管理器...');
      
      // 停止所有机制
      for (const mechanismId of this.state.mechanisms.keys()) {
        this.stopMechanism(mechanismId);
      }
      
      // 关闭API服务器
      if (this.state.apiServer) {
        this.state.apiServer.close(() => {
          console.log('API服务器已关闭');
        });
      }
      
      // 保存配置
      this.saveAllConfigurations();
      
      console.log('安全机制配置管理器已关闭');
      
    } catch (error) {
      console.error('关闭配置管理器失败:', error.message);
    }
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  console.log('启动 MTSCOS AI 安全机制配置管理器...');
  
  // 创建配置管理器实例
  const configManager = new SecurityMechanismConfigManager();
  
  // 处理退出信号
  process.on('SIGINT', () => {
    console.log('接收到退出信号，正在关闭...');
    configManager.shutdown();
    process.exit(0);
  });
  
  process.on('SIGTERM', () => {
    console.log('接收到终止信号，正在关闭...');
    configManager.shutdown();
    process.exit(0);
  });
}

// 导出模块
module.exports = {
  SecurityMechanismConfigManager
};