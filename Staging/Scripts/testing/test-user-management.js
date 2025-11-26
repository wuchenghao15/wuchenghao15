#!/usr/bin/env node

/**
 * MTSCOS AI 测试用户管理模块
 * 模拟创建测试用户信息组并设置有效期和操作监控
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');

class TestUserManagement {
  constructor(configPath) {
    this.configPath = configPath;
    this.config = null;
    this.users = new Map();
    this.userGroups = new Map();
    this.activityLog = [];
    this.monitoringInterval = null;
    this.isMonitoring = false;
    
    // 初始化测试用户管理模块
    this.initialize();
  }

  /**
   * 初始化测试用户管理模块
   */
  initialize() {
    try {
      // 加载配置文件
      this.config = this.loadConfig();
      
      // 设置日志目录
      this.logDir = path.join(this.config.basePath, 'Logs', 'Testing');
      this.ensureLogDirExists();
      
      // 加载用户和用户组数据
      this.loadUserData();
      
      // 初始化监控配置
      this.initializeMonitoring();
      
      console.log('MTSCOS AI 测试用户管理模块初始化完成');
      console.log(`已加载 ${this.users.size} 个测试用户，${this.userGroups.size} 个用户组`);
      
    } catch (error) {
      console.error('初始化测试用户管理模块失败:', error.message);
      this.logError('初始化失败', error);
      throw error;
    }
  }

  /**
   * 加载配置文件
   */
  loadConfig() {
    try {
      const configContent = fs.readFileSync(this.configPath, 'utf8');
      return JSON.parse(configContent).stagingEnvironment;
    } catch (error) {
      throw new Error(`无法加载配置文件: ${error.message}`);
    }
  }

  /**
   * 确保日志目录存在
   */
  ensureLogDirExists() {
    try {
      if (!fs.existsSync(this.logDir)) {
        fs.mkdirSync(this.logDir, { recursive: true });
        console.log(`创建日志目录: ${this.logDir}`);
      }
    } catch (error) {
      console.error(`创建日志目录失败: ${error.message}`);
    }
  }

  /**
   * 加载用户数据
   */
  loadUserData() {
    try {
      const userDataPath = path.join(this.config.basePath, 'Staging', 'Data', 'test-users.json');
      
      if (fs.existsSync(userDataPath)) {
        const userData = JSON.parse(fs.readFileSync(userDataPath, 'utf8'));
        
        // 加载用户
        if (userData.users) {
          userData.users.forEach(user => {
            this.users.set(user.userId, user);
          });
        }
        
        // 加载用户组
        if (userData.userGroups) {
          userData.userGroups.forEach(group => {
            this.userGroups.set(group.groupId, group);
          });
        }
        
        console.log(`从 ${userDataPath} 加载用户数据`);
      } else {
        console.log('用户数据文件不存在，将使用默认配置');
        
        // 如果没有用户数据，使用配置中的测试用户配置
        if (this.config.testUsers) {
          this.createUsersFromConfig();
        }
      }
    } catch (error) {
      console.error('加载用户数据失败:', error.message);
      this.logError('加载用户数据失败', error);
    }
  }

  /**
   * 从配置创建用户
   */
  createUsersFromConfig() {
    try {
      const testUsersConfig = this.config.testUsers;
      
      // 创建默认用户组
      const defaultGroup = this.createUserGroup({
        name: '默认测试组',
        description: '系统默认测试用户组',
        expiresAt: this.calculateExpiryTime(testUsersConfig.defaultExpiryDays || 30)
      });
      
      // 创建测试用户
      if (testUsersConfig.users && Array.isArray(testUsersConfig.users)) {
        testUsersConfig.users.forEach(userConfig => {
          const user = this.createUser({
            username: userConfig.username,
            email: userConfig.email,
            role: userConfig.role || 'tester',
            permissions: userConfig.permissions || ['read', 'write', 'test'],
            groupId: defaultGroup.groupId,
            expiresAt: userConfig.expiresAt || this.calculateExpiryTime(testUsersConfig.defaultExpiryDays || 30)
          });
          
          console.log(`创建测试用户: ${user.username} (${user.userId})`);
        });
      } else {
        // 创建示例测试用户
        this.createSampleUsers(defaultGroup.groupId);
      }
      
      // 保存用户数据
      this.saveUserData();
      
    } catch (error) {
      console.error('从配置创建用户失败:', error.message);
      this.logError('创建用户失败', error);
    }
  }

  /**
   * 创建示例测试用户
   */
  createSampleUsers(groupId) {
    const sampleUsers = [
      {
        username: 'test_user_1',
        email: 'test1@example.com',
        role: 'admin_tester',
        permissions: ['read', 'write', 'test', 'admin']
      },
      {
        username: 'test_user_2',
        email: 'test2@example.com',
        role: 'function_tester',
        permissions: ['read', 'write', 'test']
      },
      {
        username: 'test_user_3',
        email: 'test3@example.com',
        role: 'performance_tester',
        permissions: ['read', 'test']
      },
      {
        username: 'test_user_4',
        email: 'test4@example.com',
        role: 'security_tester',
        permissions: ['read', 'test']
      },
      {
        username: 'test_user_5',
        email: 'test5@example.com',
        role: 'ui_tester',
        permissions: ['read', 'write', 'test']
      }
    ];
    
    sampleUsers.forEach(userData => {
      const user = this.createUser({
        ...userData,
        groupId: groupId,
        expiresAt: this.calculateExpiryTime(14) // 14天有效期
      });
      
      console.log(`创建示例测试用户: ${user.username}`);
    });
  }

  /**
   * 计算过期时间
   */
  calculateExpiryTime(days) {
    const expiryDate = new Date();
    expiryDate.setDate(expiryDate.getDate() + days);
    return expiryDate.toISOString();
  }

  /**
   * 创建用户组
   */
  createUserGroup(groupData) {
    const groupId = crypto.randomUUID();
    const now = new Date().toISOString();
    
    const group = {
      groupId: groupId,
      name: groupData.name || '新测试组',
      description: groupData.description || '',
      createdAt: now,
      updatedAt: now,
      expiresAt: groupData.expiresAt || this.calculateExpiryTime(30),
      members: [],
      permissions: groupData.permissions || ['read', 'write', 'test'],
      isActive: true
    };
    
    this.userGroups.set(groupId, group);
    return group;
  }

  /**
   * 创建测试用户
   */
  createUser(userData) {
    const userId = crypto.randomUUID();
    const now = new Date().toISOString();
    
    // 生成随机密码
    const password = this.generateRandomPassword();
    
    const user = {
      userId: userId,
      username: userData.username,
      email: userData.email,
      password: password, // 在实际系统中应该加密存储
      role: userData.role || 'tester',
      permissions: userData.permissions || ['read', 'write', 'test'],
      groupId: userData.groupId,
      createdAt: now,
      updatedAt: now,
      expiresAt: userData.expiresAt || this.calculateExpiryTime(30),
      lastLogin: null,
      loginCount: 0,
      isActive: true,
      metadata: userData.metadata || {}
    };
    
    this.users.set(userId, user);
    
    // 将用户添加到用户组
    if (userData.groupId && this.userGroups.has(userData.groupId)) {
      const group = this.userGroups.get(userData.groupId);
      if (!group.members.includes(userId)) {
        group.members.push(userId);
        group.updatedAt = now;
      }
    }
    
    // 记录创建用户事件
    this.logUserActivity(userId, 'user_created', {
      username: user.username,
      role: user.role,
      groupId: user.groupId
    });
    
    return user;
  }

  /**
   * 生成随机密码
   */
  generateRandomPassword(length = 12) {
    const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+';
    let password = '';
    for (let i = 0; i < length; i++) {
      const randomIndex = Math.floor(Math.random() * charset.length);
      password += charset[randomIndex];
    }
    return password;
  }

  /**
   * 保存用户数据
   */
  saveUserData() {
    try {
      const userDataPath = path.join(this.config.basePath, 'Staging', 'Data');
      
      // 确保数据目录存在
      if (!fs.existsSync(userDataPath)) {
        fs.mkdirSync(userDataPath, { recursive: true });
      }
      
      const userData = {
        users: Array.from(this.users.values()),
        userGroups: Array.from(this.userGroups.values()),
        lastUpdated: new Date().toISOString()
      };
      
      fs.writeFileSync(
        path.join(userDataPath, 'test-users.json'),
        JSON.stringify(userData, null, 2),
        'utf8'
      );
      
      console.log('用户数据已保存');
    } catch (error) {
      console.error('保存用户数据失败:', error.message);
      this.logError('保存用户数据失败', error);
    }
  }

  /**
   * 初始化监控
   */
  initializeMonitoring() {
    this.monitoringConfig = {
      checkInterval: this.config.testUsers?.monitoringInterval || 60000, // 默认1分钟
      expiryWarningDays: this.config.testUsers?.expiryWarningDays || 3, // 提前3天警告
      logLevel: this.config.testUsers?.logLevel || 'info',
      alertOnExpiry: this.config.testUsers?.alertOnExpiry !== false, // 默认开启过期提醒
      alertOnSuspiciousActivity: this.config.testUsers?.alertOnSuspiciousActivity !== false // 默认开启可疑活动提醒
    };
  }

  /**
   * 启动用户活动监控
   */
  startMonitoring() {
    if (this.isMonitoring) {
      console.log('用户活动监控已经在运行中');
      return;
    }
    
    this.isMonitoring = true;
    console.log('启动用户活动监控');
    
    // 设置监控间隔
    this.monitoringInterval = setInterval(() => {
      this.runMonitoringCycle();
    }, this.monitoringConfig.checkInterval);
    
    // 立即执行一次监控
    this.runMonitoringCycle();
  }

  /**
   * 运行监控周期
   */
  runMonitoringCycle() {
    if (!this.isMonitoring) return;
    
    console.log(`\n--- 开始用户活动监控周期 (${new Date().toISOString()}) ---`);
    
    try {
      // 1. 检查用户过期情况
      this.checkUserExpiry();
      
      // 2. 检查用户组过期情况
      this.checkGroupExpiry();
      
      // 3. 检查可疑活动
      this.checkSuspiciousActivity();
      
      // 4. 清理过期用户
      this.cleanupExpiredUsers();
      
      // 5. 清理过期用户组
      this.cleanupExpiredGroups();
      
      // 6. 保存用户数据（如果有变更）
      this.saveUserData();
      
      console.log(`--- 用户活动监控周期结束 (${new Date().toISOString()}) ---\n`);
      
    } catch (error) {
      console.error('运行监控周期失败:', error.message);
      this.logError('监控周期失败', error);
    }
  }

  /**
   * 检查用户过期情况
   */
  checkUserExpiry() {
    const now = new Date();
    const warningThreshold = new Date(now.getTime() + this.monitoringConfig.expiryWarningDays * 24 * 60 * 60 * 1000);
    
    this.users.forEach(user => {
      const expiryDate = new Date(user.expiresAt);
      
      if (user.isActive) {
        // 检查是否已过期
        if (expiryDate < now) {
          console.warn(`用户已过期: ${user.username} (${user.userId})`);
          user.isActive = false;
          
          this.logUserActivity(user.userId, 'user_expired', {
            username: user.username,
            expiryDate: user.expiresAt
          });
          
          if (this.monitoringConfig.alertOnExpiry) {
            this.triggerAlert('user_expired', {
              userId: user.userId,
              username: user.username,
              expiryDate: user.expiresAt,
              message: `测试用户 ${user.username} 已过期`
            });
          }
        }
        // 检查是否即将过期（提前警告）
        else if (expiryDate <= warningThreshold) {
          const daysUntilExpiry = Math.ceil((expiryDate - now) / (1000 * 60 * 60 * 24));
          console.log(`用户即将过期: ${user.username} (${daysUntilExpiry}天后)`);
          
          if (this.monitoringConfig.alertOnExpiry) {
            this.triggerAlert('user_expiry_warning', {
              userId: user.userId,
              username: user.username,
              expiryDate: user.expiresAt,
              daysUntilExpiry: daysUntilExpiry,
              message: `测试用户 ${user.username} 将在 ${daysUntilExpiry} 天后过期`
            });
          }
        }
      }
    });
  }

  /**
   * 检查用户组过期情况
   */
  checkGroupExpiry() {
    const now = new Date();
    const warningThreshold = new Date(now.getTime() + this.monitoringConfig.expiryWarningDays * 24 * 60 * 60 * 1000);
    
    this.userGroups.forEach(group => {
      const expiryDate = new Date(group.expiresAt);
      
      if (group.isActive) {
        // 检查是否已过期
        if (expiryDate < now) {
          console.warn(`用户组已过期: ${group.name} (${group.groupId})`);
          group.isActive = false;
          
          // 禁用用户组中的所有用户
          group.members.forEach(userId => {
            const user = this.users.get(userId);
            if (user && user.isActive) {
              user.isActive = false;
              this.logUserActivity(userId, 'user_deactivated_by_group_expiry', {
                groupId: group.groupId,
                groupName: group.name
              });
            }
          });
          
          if (this.monitoringConfig.alertOnExpiry) {
            this.triggerAlert('group_expired', {
              groupId: group.groupId,
              groupName: group.name,
              expiryDate: group.expiresAt,
              memberCount: group.members.length,
              message: `测试用户组 ${group.name} 已过期，${group.members.length} 个用户已被禁用`
            });
          }
        }
        // 检查是否即将过期（提前警告）
        else if (expiryDate <= warningThreshold) {
          const daysUntilExpiry = Math.ceil((expiryDate - now) / (1000 * 60 * 60 * 24));
          console.log(`用户组即将过期: ${group.name} (${daysUntilExpiry}天后)`);
          
          if (this.monitoringConfig.alertOnExpiry) {
            this.triggerAlert('group_expiry_warning', {
              groupId: group.groupId,
              groupName: group.name,
              expiryDate: group.expiresAt,
              daysUntilExpiry: daysUntilExpiry,
              memberCount: group.members.length,
              message: `测试用户组 ${group.name} 将在 ${daysUntilExpiry} 天后过期，包含 ${group.members.length} 个用户`
            });
          }
        }
      }
    });
  }

  /**
   * 检查可疑活动
   */
  checkSuspiciousActivity() {
    // 分析最近的用户活动日志
    const recentActivities = this.getRecentActivities(60); // 最近60分钟的活动
    
    // 检查快速多次登录
    this.checkRapidLogins(recentActivities);
    
    // 检查权限提升活动
    this.checkPermissionElevation(recentActivities);
    
    // 检查敏感操作
    this.checkSensitiveOperations(recentActivities);
    
    // 检查异常时间活动
    this.checkUnusualTimeActivities(recentActivities);
  }

  /**
   * 获取最近的用户活动
   */
  getRecentActivities(minutes = 60) {
    const cutoffTime = new Date(Date.now() - minutes * 60 * 1000);
    return this.activityLog.filter(activity => 
      new Date(activity.timestamp) >= cutoffTime
    );
  }

  /**
   * 检查快速多次登录
   */
  checkRapidLogins(activities) {
    const loginActivities = activities.filter(a => a.activityType === 'user_login');
    const loginCounts = new Map();
    
    // 按用户统计登录次数
    loginActivities.forEach(activity => {
      const userId = activity.userId;
      loginCounts.set(userId, (loginCounts.get(userId) || 0) + 1);
    });
    
    // 检查是否有异常登录
    loginCounts.forEach((count, userId) => {
      if (count > 5) { // 5次以上视为可疑
        const user = this.users.get(userId);
        if (user) {
          console.warn(`检测到可疑的快速登录: ${user.username} (${count}次)`);
          
          this.logUserActivity(userId, 'suspicious_login_activity', {
            loginCount: count,
            message: `检测到 ${count} 次快速登录尝试`
          });
          
          if (this.monitoringConfig.alertOnSuspiciousActivity) {
            this.triggerAlert('suspicious_login', {
              userId: userId,
              username: user.username,
              loginCount: count,
              message: `检测到用户 ${user.username} 的可疑快速登录活动 (${count}次)`
            });
          }
        }
      }
    });
  }

  /**
   * 检查权限提升活动
   */
  checkPermissionElevation(activities) {
    const permissionActivities = activities.filter(a => 
      a.activityType === 'permissions_changed' || 
      a.activityType === 'role_changed'
    );
    
    permissionActivities.forEach(activity => {
      const user = this.users.get(activity.userId);
      if (user) {
        // 检查是否提升到管理员权限
        if (activity.details.newRole === 'admin' || activity.details.newRole === 'admin_tester') {
          console.warn(`检测到权限提升: ${user.username} -> ${activity.details.newRole}`);
          
          this.logUserActivity(activity.userId, 'permission_elevation', {
            oldRole: activity.details.oldRole,
            newRole: activity.details.newRole,
            changedBy: activity.details.changedBy || 'system'
          });
          
          if (this.monitoringConfig.alertOnSuspiciousActivity) {
            this.triggerAlert('permission_elevation', {
              userId: activity.userId,
              username: user.username,
              oldRole: activity.details.oldRole,
              newRole: activity.details.newRole,
              message: `用户 ${user.username} 的权限从 ${activity.details.oldRole} 提升到 ${activity.details.newRole}`
            });
          }
        }
      }
    });
  }

  /**
   * 检查敏感操作
   */
  checkSensitiveOperations(activities) {
    const sensitiveActivities = activities.filter(a => 
      ['user_created', 'user_deleted', 'group_created', 'group_deleted', 'permissions_changed', 'system_config_changed'].includes(a.activityType)
    );
    
    sensitiveActivities.forEach(activity => {
      const user = this.users.get(activity.userId);
      if (user) {
        console.log(`检测到敏感操作: ${user.username} - ${activity.activityType}`);
        
        if (this.monitoringConfig.alertOnSuspiciousActivity && 
            (user.role !== 'admin' && user.role !== 'admin_tester')) {
          // 非管理员执行敏感操作
          this.triggerAlert('unauthorized_sensitive_operation', {
            userId: activity.userId,
            username: user.username,
            userRole: user.role,
            operation: activity.activityType,
            operationDetails: activity.details,
            message: `检测到非管理员用户 ${user.username} 执行敏感操作: ${activity.activityType}`
          });
        }
      }
    });
  }

  /**
   * 检查异常时间活动
   */
  checkUnusualTimeActivities(activities) {
    const now = new Date();
    const currentHour = now.getHours();
    
    // 定义工作时间 (9:00 - 18:00)
    const isWorkHour = currentHour >= 9 && currentHour < 18;
    
    if (!isWorkHour) {
      // 非工作时间，检查所有活动
      const nonWorkHourActivities = activities.filter(a => 
        ['user_login', 'data_modified', 'configuration_changed'].includes(a.activityType)
      );
      
      nonWorkHourActivities.forEach(activity => {
        const user = this.users.get(activity.userId);
        if (user) {
          console.log(`检测到非工作时间活动: ${user.username} - ${activity.activityType}`);
          
          // 检查用户是否被授权在非工作时间活动
          const authorizedAfterHours = user.permissions?.includes('after_hours_access') || 
                                      user.role === 'admin' || 
                                      user.role === 'admin_tester';
          
          if (!authorizedAfterHours && this.monitoringConfig.alertOnSuspiciousActivity) {
            this.triggerAlert('after_hours_activity', {
              userId: activity.userId,
              username: user.username,
              activity: activity.activityType,
              timestamp: activity.timestamp,
              message: `检测到未授权用户 ${user.username} 在非工作时间的活动: ${activity.activityType}`
            });
          }
        }
      });
    }
  }

  /**
   * 清理过期用户
   */
  cleanupExpiredUsers() {
    const now = new Date();
    const expiryThreshold = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000); // 过期7天后清理
    
    let cleanedCount = 0;
    
    for (const [userId, user] of this.users.entries()) {
      const expiryDate = new Date(user.expiresAt);
      
      if (!user.isActive && expiryDate < expiryThreshold) {
        // 从用户组中移除
        if (user.groupId && this.userGroups.has(user.groupId)) {
          const group = this.userGroups.get(user.groupId);
          group.members = group.members.filter(id => id !== userId);
        }
        
        this.users.delete(userId);
        cleanedCount++;
        
        console.log(`清理过期用户: ${user.username} (${userId})`);
      }
    }
    
    if (cleanedCount > 0) {
      console.log(`已清理 ${cleanedCount} 个过期用户`);
    }
  }

  /**
   * 清理过期用户组
   */
  cleanupExpiredGroups() {
    const now = new Date();
    const expiryThreshold = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000); // 过期7天后清理
    
    let cleanedCount = 0;
    
    for (const [groupId, group] of this.userGroups.entries()) {
      const expiryDate = new Date(group.expiresAt);
      
      if (!group.isActive && expiryDate < expiryThreshold && group.members.length === 0) {
        this.userGroups.delete(groupId);
        cleanedCount++;
        
        console.log(`清理过期用户组: ${group.name} (${groupId})`);
      }
    }
    
    if (cleanedCount > 0) {
      console.log(`已清理 ${cleanedCount} 个过期用户组`);
    }
  }

  /**
   * 记录用户活动
   */
  logUserActivity(userId, activityType, details = {}) {
    const activity = {
      activityId: crypto.randomUUID(),
      userId: userId,
      activityType: activityType,
      timestamp: new Date().toISOString(),
      details: details
    };
    
    // 添加到内存日志
    this.activityLog.push(activity);
    
    // 限制内存日志大小
    if (this.activityLog.length > 10000) {
      this.activityLog = this.activityLog.slice(-10000);
    }
    
    // 写入日志文件
    this.writeActivityLog(activity);
    
    // 如果是重要活动，发送通知
    if (this.isImportantActivity(activityType)) {
      this.notifyImportantActivity(activity);
    }
  }

  /**
   * 写入活动日志到文件
   */
  writeActivityLog(activity) {
    try {
      const logDate = new Date(activity.timestamp).toISOString().split('T')[0];
      const logFilePath = path.join(this.logDir, `user-activity-${logDate}.log`);
      
      fs.appendFileSync(logFilePath, JSON.stringify(activity) + '\n', 'utf8');
    } catch (error) {
      console.error('写入活动日志失败:', error.message);
    }
  }

  /**
   * 检查是否为重要活动
   */
  isImportantActivity(activityType) {
    const importantActivities = [
      'user_created',
      'user_deleted',
      'permissions_changed',
      'role_changed',
      'suspicious_login_activity',
      'permission_elevation',
      'unauthorized_sensitive_operation',
      'user_expired',
      'system_config_changed'
    ];
    
    return importantActivities.includes(activityType);
  }

  /**
   * 通知重要活动
   */
  notifyImportantActivity(activity) {
    // 这里可以实现通知机制，如发送邮件、消息等
    console.log(`[重要] 用户活动: ${activity.activityType} - 用户ID: ${activity.userId}`);
  }

  /**
   * 触发警报
   */
  triggerAlert(alertType, details) {
    const alert = {
      alertId: crypto.randomUUID(),
      type: alertType,
      timestamp: new Date().toISOString(),
      severity: this.getAlertSeverity(alertType),
      details: details
    };
    
    // 记录警报
    this.logAlert(alert);
    
    // 显示警报
    this.displayAlert(alert);
  }

  /**
   * 获取警报严重程度
   */
  getAlertSeverity(alertType) {
    const severityMap = {
      // 严重级别
      'suspicious_login': 'critical',
      'unauthorized_sensitive_operation': 'critical',
      'permission_elevation': 'critical',
      
      // 警告级别
      'user_expired': 'warning',
      'group_expired': 'warning',
      'after_hours_activity': 'warning',
      
      // 信息级别
      'user_expiry_warning': 'info',
      'group_expiry_warning': 'info'
    };
    
    return severityMap[alertType] || 'info';
  }

  /**
   * 记录警报
   */
  logAlert(alert) {
    try {
      const alertLogPath = path.join(this.logDir, 'user-alerts.log');
      fs.appendFileSync(alertLogPath, JSON.stringify(alert) + '\n', 'utf8');
    } catch (error) {
      console.error('记录警报失败:', error.message);
    }
  }

  /**
   * 显示警报
   */
  displayAlert(alert) {
    const severityColor = {
      critical: '\x1b[31m', // 红色
      warning: '\x1b[33m',  // 黄色
      info: '\x1b[32m'      // 绿色
    };
    
    const resetColor = '\x1b[0m';
    const color = severityColor[alert.severity] || resetColor;
    
    console.log(`${color}[${alert.severity.toUpperCase()}] ${alert.timestamp} - ${alert.details.message}${resetColor}`);
  }

  /**
   * 获取用户信息
   */
  getUser(userId) {
    return this.users.get(userId) || null;
  }

  /**
   * 获取用户组信息
   */
  getUserGroup(groupId) {
    return this.userGroups.get(groupId) || null;
  }

  /**
   * 获取所有用户
   */
  getAllUsers(activeOnly = false) {
    const users = Array.from(this.users.values());
    return activeOnly ? users.filter(user => user.isActive) : users;
  }

  /**
   * 获取所有用户组
   */
  getAllUserGroups(activeOnly = false) {
    const groups = Array.from(this.userGroups.values());
    return activeOnly ? groups.filter(group => group.isActive) : groups;
  }

  /**
   * 获取用户组成员
   */
  getGroupMembers(groupId) {
    const group = this.userGroups.get(groupId);
    if (!group) return [];
    
    return group.members
      .map(userId => this.users.get(userId))
      .filter(user => user !== undefined);
  }

  /**
   * 延长用户有效期
   */
  extendUserExpiry(userId, days) {
    const user = this.users.get(userId);
    if (!user) {
      throw new Error(`用户不存在: ${userId}`);
    }
    
    const newExpiryDate = this.calculateExpiryTime(days);
    const oldExpiryDate = user.expiresAt;
    
    user.expiresAt = newExpiryDate;
    user.updatedAt = new Date().toISOString();
    
    if (!user.isActive) {
      user.isActive = true;
    }
    
    console.log(`延长用户有效期: ${user.username} - 从 ${oldExpiryDate} 到 ${newExpiryDate}`);
    
    this.logUserActivity(userId, 'expiry_extended', {
      oldExpiryDate: oldExpiryDate,
      newExpiryDate: newExpiryDate,
      extendedDays: days
    });
    
    this.saveUserData();
    return user;
  }

  /**
   * 延长用户组有效期
   */
  extendGroupExpiry(groupId, days) {
    const group = this.userGroups.get(groupId);
    if (!group) {
      throw new Error(`用户组不存在: ${groupId}`);
    }
    
    const newExpiryDate = this.calculateExpiryTime(days);
    const oldExpiryDate = group.expiresAt;
    
    group.expiresAt = newExpiryDate;
    group.updatedAt = new Date().toISOString();
    
    if (!group.isActive) {
      group.isActive = true;
      
      // 重新激活用户组中的所有用户
      group.members.forEach(userId => {
        const user = this.users.get(userId);
        if (user) {
          user.isActive = true;
          this.logUserActivity(userId, 'user_reactivated_by_group', {
            groupId: groupId,
            groupName: group.name
          });
        }
      });
    }
    
    console.log(`延长用户组有效期: ${group.name} - 从 ${oldExpiryDate} 到 ${newExpiryDate}`);
    
    this.saveUserData();
    return group;
  }

  /**
   * 禁用用户
   */
  deactivateUser(userId, reason = '管理员操作') {
    const user = this.users.get(userId);
    if (!user) {
      throw new Error(`用户不存在: ${userId}`);
    }
    
    if (user.isActive) {
      user.isActive = false;
      user.updatedAt = new Date().toISOString();
      
      console.log(`禁用用户: ${user.username} - ${reason}`);
      
      this.logUserActivity(userId, 'user_deactivated', {
        reason: reason
      });
      
      this.saveUserData();
      
      this.triggerAlert('user_deactivated', {
        userId: userId,
        username: user.username,
        reason: reason,
        message: `测试用户 ${user.username} 已被禁用 - ${reason}`
      });
    }
    
    return user;
  }

  /**
   * 重新激活用户
   */
  reactivateUser(userId) {
    const user = this.users.get(userId);
    if (!user) {
      throw new Error(`用户不存在: ${userId}`);
    }
    
    const now = new Date();
    const expiryDate = new Date(user.expiresAt);
    
    if (expiryDate < now) {
      // 延长过期用户的有效期
      return this.extendUserExpiry(userId, 7); // 默认延长7天
    } else if (!user.isActive) {
      user.isActive = true;
      user.updatedAt = new Date().toISOString();
      
      console.log(`重新激活用户: ${user.username}`);
      
      this.logUserActivity(userId, 'user_reactivated', {});
      this.saveUserData();
    }
    
    return user;
  }

  /**
   * 记录用户登录
   */
  recordUserLogin(userId, ipAddress = 'unknown') {
    const user = this.users.get(userId);
    if (!user) {
      throw new Error(`用户不存在: ${userId}`);
    }
    
    // 检查用户是否有效
    if (!user.isActive) {
      throw new Error(`用户已禁用或过期: ${user.username}`);
    }
    
    const now = new Date().toISOString();
    user.lastLogin = now;
    user.loginCount += 1;
    
    console.log(`用户登录: ${user.username} 来自 ${ipAddress}`);
    
    this.logUserActivity(userId, 'user_login', {
      ipAddress: ipAddress,
      loginCount: user.loginCount
    });
    
    // 异步保存用户数据
    setTimeout(() => this.saveUserData(), 0);
    
    return user;
  }

  /**
   * 生成用户活动报告
   */
  generateActivityReport(startDate, endDate, userId = null) {
    try {
      const reportData = {
        generatedAt: new Date().toISOString(),
        period: {
          start: startDate,
          end: endDate
        },
        summary: {
          totalActivities: 0,
          byType: {}
        },
        activities: []
      };
      
      // 读取活动日志文件
      const startDateObj = new Date(startDate);
      const endDateObj = new Date(endDate);
      const currentDate = new Date(startDateObj);
      
      while (currentDate <= endDateObj) {
        const dateStr = currentDate.toISOString().split('T')[0];
        const logFilePath = path.join(this.logDir, `user-activity-${dateStr}.log`);
        
        if (fs.existsSync(logFilePath)) {
          const logContent = fs.readFileSync(logFilePath, 'utf8');
          const lines = logContent.trim().split('\n');
          
          lines.forEach(line => {
            try {
              const activity = JSON.parse(line);
              const activityDate = new Date(activity.timestamp);
              
              // 检查日期范围和用户ID（如果指定）
              if (activityDate >= startDateObj && 
                  activityDate <= endDateObj && 
                  (!userId || activity.userId === userId)) {
                
                reportData.activities.push(activity);
                reportData.summary.totalActivities++;
                
                // 按类型统计
                const type = activity.activityType;
                reportData.summary.byType[type] = (reportData.summary.byType[type] || 0) + 1;
              }
            } catch (error) {
              // 忽略无效的日志行
            }
          });
        }
        
        // 前进一天
        currentDate.setDate(currentDate.getDate() + 1);
      }
      
      // 保存报告
      const reportId = crypto.randomUUID();
      const reportDir = path.join(this.logDir, 'Reports');
      if (!fs.existsSync(reportDir)) {
        fs.mkdirSync(reportDir, { recursive: true });
      }
      
      const reportFileName = `activity-report-${reportId}.json`;
      const reportPath = path.join(reportDir, reportFileName);
      
      fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2), 'utf8');
      
      console.log(`活动报告已生成: ${reportPath}`);
      return {
        reportId: reportId,
        reportPath: reportPath,
        data: reportData
      };
      
    } catch (error) {
      console.error('生成活动报告失败:', error.message);
      this.logError('生成活动报告失败', error);
      throw error;
    }
  }

  /**
   * 停止监控
   */
  stopMonitoring() {
    if (!this.isMonitoring) {
      console.log('用户活动监控未在运行');
      return;
    }
    
    this.isMonitoring = false;
    
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }
    
    console.log('用户活动监控已停止');
  }

  /**
   * 记录错误日志
   */
  logError(message, error) {
    try {
      const logEntry = {
        timestamp: new Date().toISOString(),
        message: message,
        error: error.message,
        stack: error.stack
      };
      
      const errorLogPath = path.join(this.logDir, 'user-management-errors.log');
      fs.appendFileSync(errorLogPath, JSON.stringify(logEntry) + '\n', 'utf8');
    } catch (error) {
      console.error('写入错误日志失败:', error.message);
    }
  }

  /**
   * 创建一组测试用户
   */
  createTestUserGroup(prefix, count = 5, expiryDays = 14) {
    try {
      // 创建用户组
      const testGroup = this.createUserGroup({
        name: `${prefix}测试组`,
        description: `${count}个自动生成的测试用户`,
        expiresAt: this.calculateExpiryTime(expiryDays)
      });
      
      console.log(`创建测试用户组: ${testGroup.name} (${testGroup.groupId})`);
      
      // 创建测试用户
      const createdUsers = [];
      
      for (let i = 1; i <= count; i++) {
        const user = this.createUser({
          username: `${prefix.toLowerCase()}_user_${i}`,
          email: `${prefix.toLowerCase()}_user_${i}@example.com`,
          role: 'tester',
          permissions: ['read', 'write', 'test'],
          groupId: testGroup.groupId,
          expiresAt: testGroup.expiresAt,
          metadata: {
            createdBy: 'test_user_management',
            batchId: testGroup.groupId,
            index: i
          }
        });
        
        createdUsers.push(user);
        console.log(`创建测试用户 ${i}/${count}: ${user.username}`);
      }
      
      // 保存用户数据
      this.saveUserData();
      
      console.log(`成功创建 ${count} 个测试用户，属于组 ${testGroup.name}`);
      
      return {
        groupId: testGroup.groupId,
        group: testGroup,
        users: createdUsers,
        userCredentials: createdUsers.map(user => ({
          username: user.username,
          email: user.email,
          password: user.password,
          userId: user.userId
        }))
      };
      
    } catch (error) {
      console.error('创建测试用户组失败:', error.message);
      this.logError('创建测试用户组失败', error);
      throw error;
    }
  }

  /**
   * 设置用户对系统模拟修改测试的监控
   */
  setupUserModificationMonitoring(userId, enabled = true) {
    const user = this.users.get(userId);
    if (!user) {
      throw new Error(`用户不存在: ${userId}`);
    }
    
    // 添加或更新监控标志
    if (!user.metadata) {
      user.metadata = {};
    }
    
    user.metadata.modificationMonitoringEnabled = enabled;
    user.metadata.modificationMonitoringSetupAt = new Date().toISOString();
    
    console.log(`设置用户修改监控: ${user.username} - ${enabled ? '已启用' : '已禁用'}`);
    
    this.logUserActivity(userId, 'modification_monitoring_set', {
      enabled: enabled
    });
    
    this.saveUserData();
    return user;
  }

  /**
   * 记录用户修改操作
   */
  recordUserModification(userId, resourceType, resourceId, action, details = {}) {
    // 检查用户是否启用了修改监控
    const user = this.users.get(userId);
    if (!user || 
        !user.isActive || 
        (!user.metadata || !user.metadata.modificationMonitoringEnabled)) {
      return;
    }
    
    const modificationRecord = {
      modificationId: crypto.randomUUID(),
      userId: userId,
      username: user.username,
      resourceType: resourceType,
      resourceId: resourceId,
      action: action,
      timestamp: new Date().toISOString(),
      details: details
    };
    
    // 记录修改操作
    this.logUserActivity(userId, 'resource_modified', modificationRecord);
    
    // 写入修改监控日志
    this.writeModificationLog(modificationRecord);
    
    console.log(`监控到用户修改: ${user.username} 修改了 ${resourceType} ${resourceId}`);
    
    // 检查是否需要发出警报
    if (this.isSensitiveModification(resourceType, action)) {
      this.triggerAlert('sensitive_modification', {
        userId: userId,
        username: user.username,
        resourceType: resourceType,
        resourceId: resourceId,
        action: action,
        message: `用户 ${user.username} 执行了敏感修改操作: ${action} ${resourceType}`
      });
    }
  }

  /**
   * 写入修改日志
   */
  writeModificationLog(modification) {
    try {
      const logDate = new Date(modification.timestamp).toISOString().split('T')[0];
      const logFilePath = path.join(this.logDir, `user-modifications-${logDate}.log`);
      
      fs.appendFileSync(logFilePath, JSON.stringify(modification) + '\n', 'utf8');
    } catch (error) {
      console.error('写入修改日志失败:', error.message);
    }
  }

  /**
   * 检查是否为敏感修改
   */
  isSensitiveModification(resourceType, action) {
    const sensitiveResources = ['configuration', 'system_setting', 'security', 'permission', 'user_group'];
    const sensitiveActions = ['delete', 'modify', 'update', 'create', 'grant', 'revoke'];
    
    return sensitiveResources.includes(resourceType) && 
           sensitiveActions.includes(action);
  }
}

// 主程序入口
if (require.main === module) {
  const configPath = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/config/staging-environment.json';
  
  try {
    const testUserManager = new TestUserManagement(configPath);
    
    // 创建一组测试用户
    const testGroup = testUserManager.createTestUserGroup('SimTest', 10, 7);
    console.log('\n测试用户创建完成:');
    console.log(`用户组ID: ${testGroup.groupId}`);
    console.log('用户凭证:');
    testGroup.userCredentials.forEach(cred => {
      console.log(`- ${cred.username}: ${cred.password}`);
    });
    
    // 为所有用户启用修改监控
    testGroup.users.forEach(user => {
      testUserManager.setupUserModificationMonitoring(user.userId, true);
    });
    
    // 启动监控
    testUserManager.startMonitoring();
    console.log('\n测试用户监控已启动');
    
    // 处理信号
    process.on('SIGINT', () => {
      console.log('收到终止信号，正在停止测试用户管理模块...');
      testUserManager.stopMonitoring();
      process.exit(0);
    });
    
  } catch (error) {
    console.error('启动测试用户管理模块失败:', error.message);
    process.exit(1);
  }
}

module.exports = TestUserManagement;