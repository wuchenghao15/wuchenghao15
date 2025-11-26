/**
 * 安全机制集成模块
 * 整合所有安全机制，包括滚码锁、数据加密、访问控制等
 */

import rollingCodeSecurity from './rolling-code-security.js';

class SecurityMechanism {
  constructor() {
    // 初始化安全机制管理器
    this.securityModules = {
      rollingCode: rollingCodeSecurity,
      // 将来可以添加更多安全模块
      accessControl: null,
      auditLogger: null,
      threatDetection: null
    };
    
    // 安全配置
    this.config = {
      enabled: true,
      securityLevel: 'medium', // low, medium, high
      auditLogging: true,
      automaticResponse: true,
      alertThreshold: 3,
      lockoutDuration: 300000 // 5分钟
    };
    
    // 安全事件历史
    this.securityEvents = [];
    
    // 可疑活动计数器
    this.suspiciousActivityCount = new Map();
    
    // 初始化
    this.initialize();
  }
  
  /**
   * 初始化安全机制
   */
  initialize() {
    console.log('[安全机制] 初始化安全系统');
    
    // 加载配置
    this.loadConfig();
    
    // 注册事件监听器
    this.registerEventListeners();
    
    // 启动安全监控
    this.startSecurityMonitoring();
    
    // 加载其他安全模块
    this.loadSecurityModules();
  }
  
  /**
   * 加载安全配置
   */
  loadConfig() {
    try {
      // 尝试从localStorage加载配置
      const savedConfig = localStorage.getItem('securityMechanismConfig');
      if (savedConfig) {
        this.config = { ...this.config, ...JSON.parse(savedConfig) };
        console.log('[安全机制] 加载保存的配置');
      }
    } catch (error) {
      console.error('[安全机制] 加载配置失败:', error);
    }
  }
  
  /**
   * 保存安全配置
   */
  saveConfig() {
    try {
      localStorage.setItem('securityMechanismConfig', JSON.stringify(this.config));
      console.log('[安全机制] 保存配置');
    } catch (error) {
      console.error('[安全机制] 保存配置失败:', error);
    }
  }
  
  /**
   * 注册事件监听器
   */
  registerEventListeners() {
    // 监听安全措施触发事件
    window.addEventListener('securityMeasureTriggered', this.handleSecurityMeasure.bind(this));
    
    // 监听数据传输事件
    window.addEventListener('dataTransmission', this.handleDataTransmission.bind(this));
    
    // 监听用户活动事件
    window.addEventListener('userActivity', this.handleUserActivity.bind(this));
    
    // 监听系统状态变化事件
    window.addEventListener('systemStateChange', this.handleSystemStateChange.bind(this));
  }
  
  /**
   * 处理安全措施触发
   */
  handleSecurityMeasure(event) {
    const { measureType, data, timestamp } = event.detail;
    
    // 记录事件
    this.logSecurityEvent({
      type: 'security_measure_triggered',
      measureType,
      data,
      timestamp
    });
    
    // 根据安全级别执行不同响应
    if (this.config.automaticResponse) {
      this.executeSecurityResponse(measureType, data);
    }
  }
  
  /**
   * 处理数据传输事件
   */
  handleDataTransmission(event) {
    const { data, channelId, isSensitive, target } = event.detail;
    
    // 如果安全机制已启用
    if (this.config.enabled) {
      // 为敏感数据创建安全通道
      if (isSensitive && !this.securityModules.rollingCode.sessionKeys.has(channelId)) {
        this.securityModules.rollingCode.createSecureChannel(channelId, 'high');
      }
      
      // 记录数据传输事件
      this.logSecurityEvent({
        type: 'data_transmission',
        channelId,
        isSensitive,
        target,
        timestamp: Date.now()
      });
    }
  }
  
  /**
   * 处理用户活动事件
   */
  handleUserActivity(event) {
    const { activityType, userId, resource, timestamp } = event.detail;
    
    // 记录用户活动
    this.logSecurityEvent({
      type: 'user_activity',
      activityType,
      userId,
      resource,
      timestamp
    });
    
    // 检测可疑活动模式
    this.detectSuspiciousActivity({
      userId,
      activityType,
      timestamp
    });
  }
  
  /**
   * 处理系统状态变化
   */
  handleSystemStateChange(event) {
    const { newState, oldState, trigger } = event.detail;
    
    // 记录系统状态变化
    this.logSecurityEvent({
      type: 'system_state_change',
      newState,
      oldState,
      trigger,
      timestamp: Date.now()
    });
    
    // 根据系统状态调整安全级别
    if (newState === 'maintenance') {
      this.config.securityLevel = 'low';
    } else if (newState === 'normal') {
      this.config.securityLevel = 'medium';
    } else if (newState === 'high_alert') {
      this.config.securityLevel = 'high';
    }
  }
  
  /**
   * 启动安全监控
   */
  startSecurityMonitoring() {
    console.log('[安全机制] 启动安全监控');
    
    // 设置定期安全检查
    this.securityCheckInterval = setInterval(() => {
      this.performSecurityCheck();
    }, 60000); // 每分钟检查一次
  }
  
  /**
   * 执行安全检查
   */
  performSecurityCheck() {
    console.log('[安全机制] 执行安全检查');
    
    // 检查各安全模块状态
    const securityStatus = {
      timestamp: Date.now(),
      modules: {}
    };
    
    // 检查滚码锁状态
    securityStatus.modules.rollingCode = this.securityModules.rollingCode.getSecurityStatus();
    
    // 检查可疑活动
    if (this.suspiciousActivityCount.size > 0) {
      securityStatus.suspiciousActivities = Array.from(this.suspiciousActivityCount.entries());
    }
    
    // 记录安全检查结果
    this.logSecurityEvent({
      type: 'security_check',
      status: securityStatus,
      timestamp: Date.now()
    });
    
    return securityStatus;
  }
  
  /**
   * 加载其他安全模块
   */
  loadSecurityModules() {
    // 动态加载其他安全模块
    // 这里预留接口，将来可以扩展
    console.log('[安全机制] 加载安全模块');
  }
  
  /**
   * 记录安全事件
   */
  logSecurityEvent(event) {
    // 添加事件到历史记录
    this.securityEvents.push(event);
    
    // 限制事件历史记录大小
    if (this.securityEvents.length > 1000) {
      this.securityEvents.shift(); // 移除最早的事件
    }
    
    // 如果启用了审计日志，发送到服务器
    if (this.config.auditLogging) {
      this.sendToAuditLog(event);
    }
    
    console.log(`[安全机制] 记录事件: ${event.type}`, event);
  }
  
  /**
   * 发送到审计日志
   */
  sendToAuditLog(event) {
    // 这里应该实现发送到服务器审计日志的逻辑
    // 简化处理，仅在控制台输出
    console.log('[安全机制] 发送到审计日志:', event);
  }
  
  /**
   * 检测可疑活动
   */
  detectSuspiciousActivity(activity) {
    const { userId, activityType, timestamp } = activity;
    const key = `${userId}:${activityType}`;
    
    // 获取或创建计数器
    let count = this.suspiciousActivityCount.get(key) || 0;
    count++;
    this.suspiciousActivityCount.set(key, count);
    
    // 检查是否超过阈值
    if (count >= this.config.alertThreshold) {
      // 触发可疑活动警报
      this.triggerSuspiciousActivityAlert({
        userId,
        activityType,
        count,
        timestamp
      });
      
      // 重置计数器
      this.suspiciousActivityCount.set(key, 0);
    }
  }
  
  /**
   * 触发可疑活动警报
   */
  triggerSuspiciousActivityAlert(alertData) {
    console.warn('[安全机制] 可疑活动警报:', alertData);
    
    // 发送警报事件
    const event = new CustomEvent('suspiciousActivityAlert', {
      detail: alertData
    });
    window.dispatchEvent(event);
    
    // 根据安全级别执行不同措施
    if (this.config.securityLevel === 'high') {
      this.lockoutUser(alertData.userId);
    }
  }
  
  /**
   * 锁定用户账户
   */
  lockoutUser(userId) {
    console.warn(`[安全机制] 锁定用户: ${userId}, 持续时间: ${this.config.lockoutDuration}ms`);
    
    // 发送锁定事件
    const event = new CustomEvent('userLockedOut', {
      detail: {
        userId,
        duration: this.config.lockoutDuration,
        timestamp: Date.now()
      }
    });
    window.dispatchEvent(event);
  }
  
  /**
   * 执行安全响应
   */
  executeSecurityResponse(measureType, data) {
    console.log(`[安全机制] 执行安全响应: ${measureType}`, data);
    
    switch(measureType) {
      case 'block_transmission':
        this.blockDataTransmission(data);
        break;
      case 'reject_data':
        this.rejectData(data);
        break;
      case 'lock_session':
        this.lockSession(data);
        break;
      default:
        console.warn(`[安全机制] 未知的安全响应类型: ${measureType}`);
    }
  }
  
  /**
   * 阻止数据传输
   */
  blockDataTransmission(data) {
    // 实现阻止数据传输的逻辑
    console.log('[安全机制] 阻止数据传输:', data);
  }
  
  /**
   * 拒绝数据
   */
  rejectData(data) {
    // 实现拒绝数据的逻辑
    console.log('[安全机制] 拒绝数据:', data);
  }
  
  /**
   * 锁定会话
   */
  lockSession(data) {
    // 实现锁定会话的逻辑
    console.log('[安全机制] 锁定会话:', data);
    
    // 发送会话锁定事件
    const event = new CustomEvent('sessionLocked', {
      detail: {
        sessionId: data.sessionId || 'unknown',
        reason: data.reason || 'security_violation',
        timestamp: Date.now()
      }
    });
    window.dispatchEvent(event);
  }
  
  /**
   * 保护数据流
   */
  secureData(data, options = {}) {
    const { channelId = 'default', isSensitive = false } = options;
    
    // 如果安全机制未启用，直接返回原始数据
    if (!this.config.enabled) {
      return data;
    }
    
    // 为敏感数据创建安全通道
    if (isSensitive && !this.securityModules.rollingCode.sessionKeys.has(channelId)) {
      this.securityModules.rollingCode.createSecureChannel(channelId, 'high');
    }
    
    // 使用滚码锁安全机制保护数据
    if (isSensitive) {
      return this.securityModules.rollingCode.transmitSensitiveData(data, channelId);
    } else {
      return this.securityModules.rollingCode.secureData(data, channelId);
    }
  }
  
  /**
   * 验证受保护的数据
   */
  verifyData(encryptedData) {
    // 如果安全机制未启用，直接返回解密后的数据
    if (!this.config.enabled) {
      try {
        return JSON.parse(atob(encryptedData));
      } catch (error) {
        return encryptedData;
      }
    }
    
    // 使用滚码锁安全机制验证数据
    return this.securityModules.rollingCode.verifyData(encryptedData);
  }
  
  /**
   * 更新安全配置
   */
  updateConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };
    this.saveConfig();
    
    // 更新各安全模块的配置
    if (newConfig.codeLength || newConfig.rotationInterval) {
      this.securityModules.rollingCode.updateConfig({
        codeLength: newConfig.codeLength,
        rotationInterval: newConfig.rotationInterval
      });
    }
    
    console.log('[安全机制] 更新全局安全配置:', this.config);
    
    // 发送配置更新事件
    const event = new CustomEvent('securityConfigUpdated', {
      detail: { config: this.config, timestamp: Date.now() }
    });
    window.dispatchEvent(event);
  }
  
  /**
   * 获取安全状态报告
   */
  getSecurityReport() {
    const report = {
      timestamp: Date.now(),
      config: this.config,
      moduleStatus: {},
      recentEvents: this.securityEvents.slice(-50), // 获取最近50个事件
      suspiciousActivities: Array.from(this.suspiciousActivityCount.entries())
    };
    
    // 获取各模块状态
    report.moduleStatus.rollingCode = this.securityModules.rollingCode.getSecurityStatus();
    
    return report;
  }
  
  /**
   * 重置安全状态
   */
  resetSecurityState() {
    console.log('[安全机制] 重置安全状态');
    
    // 重置各安全模块
    this.securityModules.rollingCode.resetSecurityState();
    
    // 清空事件历史和可疑活动计数
    this.securityEvents = [];
    this.suspiciousActivityCount.clear();
    
    // 发送重置事件
    const event = new CustomEvent('securityStateReset', {
      detail: { timestamp: Date.now() }
    });
    window.dispatchEvent(event);
  }
  
  /**
   * 启用安全机制
   */
  enable() {
    this.config.enabled = true;
    this.saveConfig();
    console.log('[安全机制] 启用安全系统');
  }
  
  /**
   * 禁用安全机制
   */
  disable() {
    this.config.enabled = false;
    this.saveConfig();
    console.log('[安全机制] 禁用安全系统');
  }
  
  /**
   * 设置安全级别
   */
  setSecurityLevel(level) {
    if (['low', 'medium', 'high'].includes(level)) {
      this.config.securityLevel = level;
      this.saveConfig();
      console.log(`[安全机制] 设置安全级别: ${level}`);
      
      // 根据安全级别调整其他配置
      this.adjustSettingsForSecurityLevel(level);
      
      return true;
    }
    return false;
  }
  
  /**
   * 根据安全级别调整设置
   */
  adjustSettingsForSecurityLevel(level) {
    switch(level) {
      case 'low':
        this.updateConfig({
          alertThreshold: 10,
          rotationInterval: 60000,
          maxCodeAge: 120000
        });
        break;
      case 'medium':
        this.updateConfig({
          alertThreshold: 5,
          rotationInterval: 30000,
          maxCodeAge: 60000
        });
        break;
      case 'high':
        this.updateConfig({
          alertThreshold: 3,
          rotationInterval: 15000,
          maxCodeAge: 30000
        });
        break;
    }
  }
}

// 导出单例实例
const securityMechanism = new SecurityMechanism();
export default securityMechanism;

// 将实例挂载到全局对象
window.SecurityMechanism = securityMechanism;