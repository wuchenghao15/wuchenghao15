#!/usr/bin/env node

/**
 * MTSCOS AI 系统 - 滚码锁安全机制
 * 实现数据流、信道和敏感数据交互的滚码锁机制，防止数据传输被截留和篡改
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const EventEmitter = require('events');

class RollingCodeLock extends EventEmitter {
  constructor(config = {}) {
    super();
    
    // 默认配置
    this.defaultConfig = {
      algorithm: 'aes-256-gcm',
      keyLength: 32, // 256位
      ivLength: 16,  // 128位
      codeLength: 8, // 滚码长度
      maxDrift: 1000, // 最大时间偏差（毫秒）
      resyncThreshold: 10, // 重新同步阈值
      replayWindowSize: 100, // 防重放窗口大小
      refreshInterval: 30000, // 密钥刷新间隔（毫秒）
      signatureAlgorithm: 'sha256',
      criticalDataPatterns: [
        /password/i,
        /secret/i,
        /token/i,
        /key/i,
        /credit.*card/i,
        /ssn/i,
        /身份证/i,
        /密码/i,
        /密钥/i
      ]
    };
    
    // 合并配置
    this.config = { ...this.defaultConfig, ...config };
    
    // 初始化状态
    this.state = {
      lastCode: 0,
      replayWindow: new Set(),
      currentKey: null,
      nextKey: null,
      keyExpiry: null,
      sessionNonces: new Map(),
      isInitialized: false,
      channels: new Map(),
      pendingAcks: new Map()
    };
    
    // 初始化
    this.initialize();
  }

  /**
   * 初始化滚码锁系统
   */
  initialize() {
    try {
      // 生成初始密钥
      this.state.currentKey = this.generateKey();
      this.state.nextKey = this.generateKey();
      this.state.keyExpiry = Date.now() + this.config.refreshInterval;
      
      // 设置密钥自动刷新
      this.setupKeyRefresh();
      
      // 初始化防重放窗口
      this.state.replayWindow = new Set();
      
      this.state.isInitialized = true;
      console.log('滚码锁安全机制初始化成功');
      
      // 触发初始化完成事件
      this.emit('initialized');
      
    } catch (error) {
      console.error('滚码锁初始化失败:', error.message);
      this.emit('error', error);
      throw error;
    }
  }

  /**
   * 生成加密密钥
   */
  generateKey() {
    return crypto.randomBytes(this.config.keyLength);
  }

  /**
   * 设置密钥自动刷新
   */
  setupKeyRefresh() {
    if (this.keyRefreshTimer) {
      clearInterval(this.keyRefreshTimer);
    }
    
    this.keyRefreshTimer = setInterval(() => {
      this.refreshKeys();
    }, this.config.refreshInterval);
  }

  /**
   * 刷新密钥
   */
  refreshKeys() {
    try {
      // 更新密钥
      this.state.currentKey = this.state.nextKey;
      this.state.nextKey = this.generateKey();
      this.state.keyExpiry = Date.now() + this.config.refreshInterval;
      
      console.log('滚码锁密钥已刷新');
      
      // 触发密钥刷新事件
      this.emit('keysRefreshed', {
        timestamp: Date.now(),
        nextKeyHint: this.state.nextKey.slice(0, 4).toString('hex') // 发送部分作为提示
      });
      
    } catch (error) {
      console.error('密钥刷新失败:', error.message);
      this.emit('error', error);
    }
  }

  /**
   * 获取下一个滚码
   */
  getNextRollingCode() {
    // 原子操作更新滚码
    const code = ++this.state.lastCode;
    return code;
  }

  /**
   * 检查并更新滚码
   */
  validateRollingCode(receivedCode, senderId = 'default') {
    // 获取发送方的会话信息
    let sessionInfo = this.state.sessionNonces.get(senderId);
    if (!sessionInfo) {
      sessionInfo = {
        lastValidCode: 0,
        driftAdjustment: 0
      };
      this.state.sessionNonces.set(senderId, sessionInfo);
    }
    
    // 检查是否为重放攻击
    const codeKey = `${senderId}:${receivedCode}`;
    if (this.state.replayWindow.has(codeKey)) {
      return { valid: false, reason: 'replay_attack' };
    }
    
    // 添加到防重放窗口
    this.state.replayWindow.add(codeKey);
    
    // 如果窗口太大，移除旧条目
    if (this.state.replayWindow.size > this.config.replayWindowSize) {
      const oldestEntry = this.state.replayWindow.keys().next().value;
      this.state.replayWindow.delete(oldestEntry);
    }
    
    // 检查滚码是否有效
    const expectedCode = sessionInfo.lastValidCode + 1;
    const codeDiff = receivedCode - expectedCode;
    
    if (receivedCode <= sessionInfo.lastValidCode) {
      return { valid: false, reason: 'invalid_sequence' };
    }
    
    // 允许一定程度的漂移
    if (Math.abs(codeDiff) > this.config.resyncThreshold) {
      return { valid: false, reason: 'sequence_too_far' };
    }
    
    // 更新会话信息
    sessionInfo.lastValidCode = receivedCode;
    
    return { valid: true, codeDiff };
  }

  /**
   * 创建安全通道
   */
  createSecureChannel(channelId, channelConfig = {}) {
    try {
      const channel = {
        id: channelId,
        config: { ...this.defaultConfig, ...channelConfig },
        created: Date.now(),
        lastUsed: Date.now(),
        messageCount: 0,
        encryptionKeys: {
          current: this.generateKey(),
          next: this.generateKey()
        }
      };
      
      this.state.channels.set(channelId, channel);
      console.log(`已创建安全通道: ${channelId}`);
      
      return channel;
    } catch (error) {
      console.error(`创建安全通道失败 [${channelId}]:`, error.message);
      throw error;
    }
  }

  /**
   * 获取安全通道
   */
  getSecureChannel(channelId) {
    const channel = this.state.channels.get(channelId);
    if (!channel) {
      throw new Error(`安全通道不存在: ${channelId}`);
    }
    
    // 更新最后使用时间
    channel.lastUsed = Date.now();
    
    return channel;
  }

  /**
   * 加密数据
   */
  encrypt(data, channelId = null, metadata = {}) {
    try {
      // 确定使用的密钥和配置
      let encryptionKey = this.state.currentKey;
      let config = this.config;
      
      if (channelId) {
        const channel = this.getSecureChannel(channelId);
        encryptionKey = channel.encryptionKeys.current;
        config = channel.config;
      }
      
      // 生成IV
      const iv = crypto.randomBytes(config.ivLength);
      
      // 生成滚码
      const rollingCode = this.getNextRollingCode();
      
      // 创建加密器
      const cipher = crypto.createCipheriv(config.algorithm, encryptionKey, iv);
      
      // 创建消息对象
      const message = {
        data: typeof data === 'string' ? data : JSON.stringify(data),
        timestamp: Date.now(),
        rollingCode: rollingCode,
        nonce: crypto.randomBytes(16).toString('hex'),
        metadata: metadata,
        version: '1.0'
      };
      
      // 添加敏感数据标记
      if (this.containsSensitiveData(message.data)) {
        message.sensitive = true;
        message.protectionLevel = 'high';
      }
      
      // 转换为字符串
      const messageStr = JSON.stringify(message);
      
      // 加密
      let encrypted = cipher.update(messageStr, 'utf8', 'base64');
      encrypted += cipher.final('base64');
      
      // 获取认证标签
      const authTag = cipher.getAuthTag();
      
      // 构建安全包
      const securePackage = {
        encrypted: encrypted,
        iv: iv.toString('base64'),
        authTag: authTag.toString('base64'),
        rollingCode: rollingCode,
        channelId: channelId,
        timestamp: message.timestamp,
        signature: this.signMessage(messageStr, encryptionKey)
      };
      
      // 如果使用通道，更新消息计数
      if (channelId) {
        const channel = this.state.channels.get(channelId);
        channel.messageCount++;
      }
      
      // 触发加密完成事件
      this.emit('encrypted', {
        channelId: channelId,
        rollingCode: rollingCode,
        sensitive: message.sensitive || false
      });
      
      return securePackage;
      
    } catch (error) {
      console.error('数据加密失败:', error.message);
      this.emit('error', error);
      throw error;
    }
  }

  /**
   * 解密数据
   */
  decrypt(securePackage, senderId = 'default') {
    try {
      // 验证必要字段
      if (!securePackage.encrypted || !securePackage.iv || !securePackage.authTag) {
        throw new Error('安全包格式无效');
      }
      
      // 确定使用的密钥和配置
      let decryptionKey = this.state.currentKey;
      let config = this.config;
      
      if (securePackage.channelId) {
        const channel = this.getSecureChannel(securePackage.channelId);
        decryptionKey = channel.encryptionKeys.current;
        config = channel.config;
      }
      
      // 检查滚码
      const codeValidation = this.validateRollingCode(securePackage.rollingCode, senderId);
      if (!codeValidation.valid) {
        this.emit('security_breach', {
          type: 'invalid_rolling_code',
          reason: codeValidation.reason,
          rollingCode: securePackage.rollingCode,
          senderId: senderId,
          timestamp: Date.now()
        });
        throw new Error(`滚码验证失败: ${codeValidation.reason}`);
      }
      
      // 检查时间戳，防止延迟攻击
      const timeDiff = Math.abs(Date.now() - securePackage.timestamp);
      if (timeDiff > this.config.maxDrift) {
        this.emit('security_warning', {
          type: 'timestamp_drift',
          timeDiff: timeDiff,
          maxAllowed: this.config.maxDrift,
          senderId: senderId
        });
        // 警告但不阻止解密，允许一定程度的网络延迟
      }
      
      // 创建解密器
      const decipher = crypto.createDecipheriv(
        config.algorithm,
        decryptionKey,
        Buffer.from(securePackage.iv, 'base64')
      );
      
      // 设置认证标签
      decipher.setAuthTag(Buffer.from(securePackage.authTag, 'base64'));
      
      // 解密
      let decrypted = decipher.update(securePackage.encrypted, 'base64', 'utf8');
      decrypted += decipher.final('utf8');
      
      // 解析消息
      const message = JSON.parse(decrypted);
      
      // 验证签名
      if (!this.verifySignature(decrypted, securePackage.signature, decryptionKey)) {
        this.emit('security_breach', {
          type: 'invalid_signature',
          senderId: senderId,
          timestamp: Date.now()
        });
        throw new Error('消息签名验证失败');
      }
      
      // 触发解密完成事件
      this.emit('decrypted', {
        channelId: securePackage.channelId,
        rollingCode: securePackage.rollingCode,
        sensitive: message.sensitive || false
      });
      
      return message;
      
    } catch (error) {
      console.error('数据解密失败:', error.message);
      this.emit('error', error);
      throw error;
    }
  }

  /**
   * 签名消息
   */
  signMessage(message, key) {
    const hmac = crypto.createHmac(this.config.signatureAlgorithm, key);
    hmac.update(message);
    return hmac.digest('base64');
  }

  /**
   * 验证签名
   */
  verifySignature(message, signature, key) {
    const hmac = crypto.createHmac(this.config.signatureAlgorithm, key);
    hmac.update(message);
    const expectedSignature = hmac.digest('base64');
    
    // 使用安全的比较方法防止时序攻击
    return crypto.timingSafeEqual(
      Buffer.from(signature, 'base64'),
      Buffer.from(expectedSignature, 'base64')
    );
  }

  /**
   * 检查是否包含敏感数据
   */
  containsSensitiveData(data) {
    const dataStr = typeof data === 'string' ? data : JSON.stringify(data);
    
    return this.config.criticalDataPatterns.some(pattern => {
      return pattern.test(dataStr);
    });
  }

  /**
   * 安全传输敏感数据
   */
  secureTransmitSensitiveData(data, channelId = null, additionalProtection = true) {
    try {
      // 额外的敏感数据保护
      if (additionalProtection) {
        // 对敏感字段进行特殊处理
        data = this.applyEnhancedProtection(data);
      }
      
      // 使用高保护级别加密
      return this.encrypt(data, channelId, {
        sensitivity: 'high',
        protectionLevel: 'enhanced',
        requiresAck: true
      });
      
    } catch (error) {
      console.error('敏感数据安全传输失败:', error.message);
      throw error;
    }
  }

  /**
   * 应用增强保护
   */
  applyEnhancedProtection(data) {
    if (typeof data !== 'object') {
      return data;
    }
    
    // 深度复制数据
    const protectedData = JSON.parse(JSON.stringify(data));
    
    // 递归处理对象
    const processObject = (obj) => {
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
          // 检查键名是否包含敏感信息
          const isKeySensitive = this.config.criticalDataPatterns.some(pattern => {
            return pattern.test(key);
          });
          
          if (isKeySensitive && typeof obj[key] === 'string') {
            // 对敏感字段值进行额外加密
            obj[key] = this.additionalFieldEncryption(obj[key]);
          } else if (typeof obj[key] === 'object' && obj[key] !== null) {
            // 递归处理嵌套对象
            processObject(obj[key]);
          }
        }
      }
    };
    
    processObject(protectedData);
    return protectedData;
  }

  /**
   * 字段级额外加密
   */
  additionalFieldEncryption(value) {
    // 使用临时密钥进行额外的字段级加密
    const fieldKey = crypto.scryptSync(this.state.currentKey, 'field_encryption', 32);
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-cbc', fieldKey, iv);
    
    let encrypted = cipher.update(value, 'utf8', 'base64');
    encrypted += cipher.final('base64');
    
    return {
      encrypted: true,
      value: encrypted,
      iv: iv.toString('base64'),
      method: 'aes-256-cbc'
    };
  }

  /**
   * 字段级解密
   */
  additionalFieldDecryption(encryptedValue) {
    if (!encryptedValue.encrypted || !encryptedValue.value || !encryptedValue.iv) {
      throw new Error('无效的加密字段格式');
    }
    
    // 使用临时密钥进行字段级解密
    const fieldKey = crypto.scryptSync(this.state.currentKey, 'field_encryption', 32);
    const decipher = crypto.createDecipheriv(
      'aes-256-cbc',
      fieldKey,
      Buffer.from(encryptedValue.iv, 'base64')
    );
    
    let decrypted = decipher.update(encryptedValue.value, 'base64', 'utf8');
    decrypted += decipher.final('utf8');
    
    return decrypted;
  }

  /**
   * 建立安全握手
   */
  initiateSecureHandshake() {
    try {
      // 生成握手挑战
      const challenge = crypto.randomBytes(32).toString('hex');
      const timestamp = Date.now();
      
      // 创建握手请求
      const handshakeRequest = {
        type: 'handshake_request',
        challenge: challenge,
        timestamp: timestamp,
        supportedAlgorithms: ['aes-256-gcm', 'aes-256-cbc'],
        publicKeyHint: this.state.currentKey.slice(0, 8).toString('hex'),
        version: '1.0'
      };
      
      // 签名握手请求
      const signature = this.signMessage(JSON.stringify(handshakeRequest), this.state.currentKey);
      
      return {
        request: handshakeRequest,
        signature: signature
      };
      
    } catch (error) {
      console.error('安全握手初始化失败:', error.message);
      throw error;
    }
  }

  /**
   * 验证握手响应
   */
  verifyHandshakeResponse(handshakeRequest, handshakeResponse, signature) {
    try {
      // 验证响应格式
      if (!handshakeResponse || !handshakeResponse.response || !handshakeResponse.timestamp) {
        throw new Error('无效的握手响应格式');
      }
      
      // 验证时间戳
      const timeDiff = Math.abs(Date.now() - handshakeResponse.timestamp);
      if (timeDiff > this.config.maxDrift) {
        throw new Error('握手响应时间戳超出允许范围');
      }
      
      // 验证挑战响应
      const expectedResponse = this.generateHandshakeResponse(handshakeRequest.challenge);
      if (handshakeResponse.response !== expectedResponse) {
        this.emit('security_breach', {
          type: 'handshake_failed',
          reason: 'invalid_challenge_response',
          timestamp: Date.now()
        });
        throw new Error('挑战响应验证失败');
      }
      
      // 验证签名
      if (!this.verifySignature(JSON.stringify(handshakeResponse), signature, this.state.currentKey)) {
        this.emit('security_breach', {
          type: 'handshake_failed',
          reason: 'invalid_signature',
          timestamp: Date.now()
        });
        throw new Error('握手响应签名验证失败');
      }
      
      // 握手成功，生成会话密钥
      const sessionKey = this.generateSessionKey(handshakeRequest, handshakeResponse);
      
      return {
        success: true,
        sessionKey: sessionKey,
        timestamp: handshakeResponse.timestamp
      };
      
    } catch (error) {
      console.error('握手响应验证失败:', error.message);
      throw error;
    }
  }

  /**
   * 生成握手响应
   */
  generateHandshakeResponse(challenge) {
    const hmac = crypto.createHmac(this.config.signatureAlgorithm, this.state.currentKey);
    hmac.update(challenge + Date.now().toString());
    return hmac.digest('hex');
  }

  /**
   * 生成会话密钥
   */
  generateSessionKey(handshakeRequest, handshakeResponse) {
    const combined = handshakeRequest.challenge + handshakeResponse.response + this.state.currentKey.toString('hex');
    const hmac = crypto.createHmac(this.config.signatureAlgorithm, combined);
    hmac.update(Date.now().toString());
    return hmac.digest();
  }

  /**
   * 注册安全机制配置
   */
  registerSecurityMechanismConfig(mechanismId, config) {
    try {
      // 验证配置
      if (!mechanismId || typeof config !== 'object') {
        throw new Error('无效的机制ID或配置');
      }
      
      // 合并默认配置
      const mergedConfig = { ...this.defaultConfig, ...config };
      
      // 保存配置
      const configPath = path.join(__dirname, '..', '..', 'Config', 'security-mechanisms.json');
      
      let mechanismsConfig;
      if (fs.existsSync(configPath)) {
        mechanismsConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      } else {
        mechanismsConfig = {};
      }
      
      mechanismsConfig[mechanismId] = {
        config: mergedConfig,
        lastModified: Date.now(),
        version: '1.0'
      };
      
      // 确保目录存在
      const configDir = path.dirname(configPath);
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }
      
      // 保存到文件
      fs.writeFileSync(configPath, JSON.stringify(mechanismsConfig, null, 2), 'utf8');
      
      console.log(`已注册安全机制配置: ${mechanismId}`);
      
      return true;
      
    } catch (error) {
      console.error(`注册安全机制配置失败 [${mechanismId}]:`, error.message);
      throw error;
    }
  }

  /**
   * 获取安全机制配置
   */
  getSecurityMechanismConfig(mechanismId) {
    try {
      const configPath = path.join(__dirname, '..', '..', 'Config', 'security-mechanisms.json');
      
      if (!fs.existsSync(configPath)) {
        throw new Error('安全机制配置文件不存在');
      }
      
      const mechanismsConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      
      if (!mechanismsConfig[mechanismId]) {
        throw new Error(`安全机制配置不存在: ${mechanismId}`);
      }
      
      return mechanismsConfig[mechanismId];
      
    } catch (error) {
      console.error(`获取安全机制配置失败 [${mechanismId}]:`, error.message);
      throw error;
    }
  }

  /**
   * 更新安全机制配置
   */
  updateSecurityMechanismConfig(mechanismId, updates) {
    try {
      const currentConfig = this.getSecurityMechanismConfig(mechanismId);
      
      // 合并更新
      const updatedConfig = {
        ...currentConfig,
        config: { ...currentConfig.config, ...updates },
        lastModified: Date.now()
      };
      
      // 保存到文件
      const configPath = path.join(__dirname, '..', '..', 'Config', 'security-mechanisms.json');
      const mechanismsConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      
      mechanismsConfig[mechanismId] = updatedConfig;
      fs.writeFileSync(configPath, JSON.stringify(mechanismsConfig, null, 2), 'utf8');
      
      console.log(`已更新安全机制配置: ${mechanismId}`);
      
      // 触发配置更新事件
      this.emit('configUpdated', { mechanismId, updates });
      
      return true;
      
    } catch (error) {
      console.error(`更新安全机制配置失败 [${mechanismId}]:`, error.message);
      throw error;
    }
  }

  /**
   * 动态触发安全机制
   */
  triggerSecurityMechanism(mechanismId, action, params = {}) {
    try {
      // 记录触发事件
      const triggerEvent = {
        mechanismId: mechanismId,
        action: action,
        params: params,
        timestamp: Date.now(),
        triggeredBy: 'system' // 可以是用户ID或系统
      };
      
      console.log(`触发安全机制: ${mechanismId}.${action}`);
      
      // 触发相应的事件
      this.emit(`mechanism:${mechanismId}:${action}`, triggerEvent);
      
      // 特殊处理预定义的机制
      if (mechanismId === 'rolling_code_lock') {
        switch (action) {
          case 'force_refresh':
            this.refreshKeys();
            break;
          case 'reset_replay_protection':
            this.state.replayWindow.clear();
            break;
          case 'emergency_shutdown':
            this.emergencyShutdown(params.reason);
            break;
        }
      }
      
      // 记录到审计日志
      this.logSecurityEvent(triggerEvent);
      
      return true;
      
    } catch (error) {
      console.error(`触发安全机制失败 [${mechanismId}.${action}]:`, error.message);
      throw error;
    }
  }

  /**
   * 紧急关闭
   */
  emergencyShutdown(reason = 'unknown') {
    try {
      console.log(`执行紧急关闭: ${reason}`);
      
      // 清除所有会话
      this.state.sessionNonces.clear();
      this.state.channels.clear();
      
      // 清除防重放窗口
      this.state.replayWindow.clear();
      
      // 生成新的密钥
      this.state.currentKey = this.generateKey();
      this.state.nextKey = this.generateKey();
      
      // 触发紧急关闭事件
      this.emit('emergency_shutdown', { reason: reason, timestamp: Date.now() });
      
    } catch (error) {
      console.error('紧急关闭失败:', error.message);
    }
  }

  /**
   * 记录安全事件
   */
  logSecurityEvent(event) {
    try {
      const logPath = path.join(__dirname, '..', '..', 'Logs', 'Security', 'security-events.log');
      
      // 确保日志目录存在
      const logDir = path.dirname(logPath);
      if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
      }
      
      // 写入日志
      fs.appendFileSync(logPath, JSON.stringify(event) + '\n', 'utf8');
      
    } catch (error) {
      console.error('记录安全事件失败:', error.message);
    }
  }

  /**
   * 获取安全状态
   */
  getSecurityStatus() {
    return {
      initialized: this.state.isInitialized,
      lastKeyRefresh: this.state.keyExpiry - this.config.refreshInterval,
      nextKeyRefresh: this.state.keyExpiry,
      replayProtection: {
        enabled: true,
        windowSize: this.state.replayWindow.size,
        maxSize: this.config.replayWindowSize
      },
      activeChannels: this.state.channels.size,
      secureSessions: this.state.sessionNonces.size,
      lastRollingCode: this.state.lastCode
    };
  }

  /**
   * 生成安全报告
   */
  generateSecurityReport() {
    const report = {
      timestamp: Date.now(),
      status: this.getSecurityStatus(),
      channelStats: [],
      replayAttempts: 0, // 可以从日志中统计
      encryptionStats: {
        messagesEncrypted: 0,
        messagesDecrypted: 0,
        sensitiveDataTransmissions: 0
      },
      version: '1.0'
    };
    
    // 添加通道统计信息
    this.state.channels.forEach((channel, channelId) => {
      report.channelStats.push({
        channelId: channelId,
        messageCount: channel.messageCount,
        lastUsed: channel.lastUsed,
        created: channel.created
      });
    });
    
    return report;
  }

  /**
   * 关闭滚码锁系统
   */
  shutdown() {
    try {
      // 清除定时器
      if (this.keyRefreshTimer) {
        clearInterval(this.keyRefreshTimer);
      }
      
      // 清除所有状态
      this.state = {
        lastCode: 0,
        replayWindow: new Set(),
        currentKey: null,
        nextKey: null,
        keyExpiry: null,
        sessionNonces: new Map(),
        isInitialized: false,
        channels: new Map(),
        pendingAcks: new Map()
      };
      
      console.log('滚码锁安全机制已关闭');
      
    } catch (error) {
      console.error('滚码锁关闭失败:', error.message);
    }
  }
}

// 导出模块，用于集成到安全机制页面
module.exports = {
  RollingCodeLock,
  createSecurityMechanism: (config) => new RollingCodeLock(config)
};

// 命令行模式
if (require.main === module) {
  // 示例用法
  const rollingCodeLock = new RollingCodeLock();
  
  console.log('MTSCOS AI 滚码锁安全机制演示');
  console.log('============================');
  
  // 监听事件
  rollingCodeLock.on('initialized', () => {
    console.log('滚码锁已初始化');
    
    // 演示加密解密
    const testData = {
      username: 'test_user',
      password: 'sensitive_password_123',
      token: 'abcdef123456',
      timestamp: Date.now()
    };
    
    console.log('\n原始数据:', JSON.stringify(testData));
    
    // 加密
    const encryptedPackage = rollingCodeLock.encrypt(testData);
    console.log('\n加密后的数据包:');
    console.log('滚码:', encryptedPackage.rollingCode);
    console.log('加密数据长度:', encryptedPackage.encrypted.length, '字符');
    
    // 解密
    try {
      const decryptedData = rollingCodeLock.decrypt(encryptedPackage);
      console.log('\n解密后的数据:', JSON.stringify(decryptedData.data));
    } catch (error) {
      console.error('解密失败:', error.message);
    }
    
    // 尝试重放攻击
    console.log('\n尝试重放攻击...');
    try {
      rollingCodeLock.decrypt(encryptedPackage);
      console.log('重放攻击检测失败!');
    } catch (error) {
      console.log('重放攻击成功检测:', error.message);
    }
    
    // 注册安全机制配置
    console.log('\n注册安全机制配置...');
    rollingCodeLock.registerSecurityMechanismConfig('data_channel_protection', {
      algorithm: 'aes-256-gcm',
      replayWindowSize: 200,
      refreshInterval: 60000
    });
    
    console.log('\n安全报告:');
    console.log(JSON.stringify(rollingCodeLock.generateSecurityReport(), null, 2));
    
    // 关闭
    setTimeout(() => {
      rollingCodeLock.shutdown();
      console.log('\n演示完成');
    }, 1000);
  });
}
