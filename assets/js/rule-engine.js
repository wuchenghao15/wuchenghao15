/**
 * MTSCOS 系统规则引擎
 * 负责规则的加载、绑定、执行和管理
 */

class RuleEngine {
    constructor() {
        this.rules = new Map();
        this.mechanisms = new Map();
        this.eventListeners = new Map();
        this.ruleExecutions = new Map();
        this.isLoaded = false;
        this.config = {
            rulesFile: '/config/system-rules.json',
            executionLog: true,
            debugMode: false
        };
    }

    /**
     * 初始化规则引擎
     */
    async initialize() {
        try {
            await this.loadRules();
            await this.loadMechanisms();
            this.setupEventListeners();
            this.isLoaded = true;
            console.log('规则引擎初始化完成');
            return true;
        } catch (error) {
            console.error('规则引擎初始化失败:', error);
            return false;
        }
    }

    /**
     * 加载系统规则
     */
    async loadRules() {
        try {
            const response = await fetch(this.config.rulesFile);
            if (!response.ok) {
                throw new Error(`无法加载规则文件: ${response.status}`);
            }
            
            const systemRules = await response.json();
            
            // 加载所有规则
            Object.values(systemRules.systemRules.categories).forEach(category => {
                category.rules.forEach(rule => {
                    this.rules.set(rule.id, {
                        ...rule,
                        category: category.name,
                        lastExecuted: null,
                        executionCount: 0,
                        enabled: rule.enabled !== false
                    });
                });
            });

            console.log(`已加载 ${this.rules.size} 条系统规则`);
        } catch (error) {
            console.error('加载规则失败:', error);
            throw error;
        }
    }

    /**
     * 加载执行机制
     */
    async loadMechanisms() {
        try {
            const response = await fetch(this.config.rulesFile);
            const systemRules = await response.json();
            
            // 加载所有机制
            Object.entries(systemRules.systemRules.mechanisms).forEach(([id, mechanism]) => {
                this.mechanisms.set(id, {
                    ...mechanism,
                    instance: this.createMechanismInstance(id, mechanism)
                });
            });

            console.log(`已加载 ${this.mechanisms.size} 个执行机制`);
        } catch (error) {
            console.error('加载机制失败:', error);
            throw error;
        }
    }

    /**
     * 创建机制实例
     */
    createMechanismInstance(id, mechanism) {
        const mechanismMap = {
            'password_validator': new PasswordValidator(),
            'account_security': new AccountSecurity(),
            'session_manager': new SessionManager(),
            'cache_manager': new CacheManager(),
            'log_manager': new LogManager(),
            'backup_manager': new BackupManager(),
            'system_monitor': new SystemMonitor(),
            'update_manager': new UpdateManager(),
            'cleanup_manager': new CleanupManager()
        };

        return mechanismMap[id] || new BaseMechanism(mechanism);
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 监听系统事件
        window.addEventListener('user_login', (event) => this.handleEvent('login', event));
        window.addEventListener('user_logout', (event) => this.handleEvent('logout', event));
        window.addEventListener('password_change', (event) => this.handleEvent('password_change', event));
        window.addEventListener('login_failed', (event) => this.handleEvent('login_failed', event));
        window.addEventListener('system_monitor', (event) => this.handleEvent('system_monitor', event));
        
        // 定时任务监听
        this.setupScheduledTasks();
        
        console.log('事件监听器设置完成');
    }

    /**
     * 设置定时任务
     */
    setupScheduledTasks() {
        // 每分钟检查一次规则
        setInterval(() => {
            this.handleEvent('scheduled_task', { type: 'minute_check' });
        }, 60000);

        // 每小时检查一次
        setInterval(() => {
            this.handleEvent('scheduled_task', { type: 'hourly_check' });
        }, 3600000);

        // 每天检查一次
        setInterval(() => {
            this.handleEvent('scheduled_task', { type: 'daily_check' });
        }, 86400000);
    }

    /**
     * 处理事件
     */
    async handleEvent(eventType, eventData) {
        if (!this.isLoaded) {
            console.warn('规则引擎未初始化，跳过事件处理');
            return;
        }

        const matchingRules = this.findMatchingRules(eventType, eventData);
        
        for (const rule of matchingRules) {
            if (rule.enabled) {
                await this.executeRule(rule, eventData);
            }
        }
    }

    /**
     * 查找匹配的规则
     */
    findMatchingRules(eventType, eventData) {
        const matchingRules = [];
        
        this.rules.forEach(rule => {
            if (this.evaluateConditions(rule.conditions, eventType, eventData)) {
                matchingRules.push(rule);
            }
        });
        
        // 按优先级排序
        return matchingRules.sort((a, b) => {
            const priorityOrder = { high: 3, medium: 2, low: 1 };
            return priorityOrder[b.priority] - priorityOrder[a.priority];
        });
    }

    /**
     * 评估规则条件
     */
    evaluateConditions(conditions, eventType, eventData) {
        // 检查事件类型
        if (conditions.eventType && conditions.eventType !== eventType) {
            return false;
        }

        // 检查其他条件
        for (const [key, value] of Object.entries(conditions)) {
            if (key === 'eventType') continue;
            
            if (!this.evaluateCondition(key, value, eventData)) {
                return false;
            }
        }
        
        return true;
    }

    /**
     * 评估单个条件
     */
    evaluateCondition(key, expectedValue, eventData) {
        const actualValue = this.getEventDataValue(eventData, key);
        
        if (Array.isArray(expectedValue)) {
            return expectedValue.includes(actualValue);
        }
        
        if (typeof expectedValue === 'object' && expectedValue.operator) {
            return this.compareValues(actualValue, expectedValue.operator, expectedValue.value);
        }
        
        return actualValue === expectedValue;
    }

    /**
     * 获取事件数据值
     */
    getEventDataValue(eventData, key) {
        return eventData[key] || eventData.data?.[key] || null;
    }

    /**
     * 比较值
     */
    compareValues(actual, operator, expected) {
        switch (operator) {
            case '>': return actual > expected;
            case '<': return actual < expected;
            case '>=': return actual >= expected;
            case '<=': return actual <= expected;
            case '==': return actual == expected;
            case '!=': return actual != expected;
            case 'in': return Array.isArray(expected) && expected.includes(actual);
            default: return actual === expected;
        }
    }

    /**
     * 执行规则
     */
    async executeRule(rule, eventData) {
        try {
            console.log(`执行规则: ${rule.name} (${rule.id})`);
            
            const mechanism = this.mechanisms.get(rule.mechanism);
            if (!mechanism) {
                console.error(`未找到机制: ${rule.mechanism}`);
                return false;
            }

            // 记录执行信息
            this.recordExecution(rule.id);
            
            // 执行所有动作
            for (const action of rule.actions) {
                await this.executeAction(action, eventData, mechanism.instance);
            }
            
            // 更新规则执行信息
            rule.lastExecuted = new Date().toISOString();
            rule.executionCount++;
            
            console.log(`规则执行完成: ${rule.name}`);
            return true;
            
        } catch (error) {
            console.error(`规则执行失败 ${rule.id}:`, error);
            this.logError(rule.id, error);
            return false;
        }
    }

    /**
     * 执行动作
     */
    async executeAction(action, eventData, mechanismInstance) {
        switch (action.type) {
            case 'validate':
                return await this.executeValidation(action.parameters, eventData);
            case 'log':
                return this.executeLog(action.parameters);
            case 'alert':
                return await this.executeAlert(action.parameters);
            case 'notify':
                return await this.executeNotification(action.parameters);
            case 'backup':
                return await mechanismInstance.backup(action.parameters);
            case 'cleanup':
                return await mechanismInstance.cleanup(action.parameters);
            case 'lock_account':
                return await mechanismInstance.lockAccount(action.parameters);
            case 'logout':
                return await mechanismInstance.logout(action.parameters);
            case 'clean_cache':
                return await mechanismInstance.cleanCache(action.parameters);
            case 'rotate_log':
                return await mechanismInstance.rotateLog(action.parameters);
            case 'check_updates':
                return await mechanismInstance.checkUpdates(action.parameters);
            case 'restart_heavy_processes':
                return await mechanismInstance.restartHeavyProcesses(action.parameters);
            default:
                console.warn(`未知动作类型: ${action.type}`);
        }
    }

    /**
     * 执行验证
     */
    async executeValidation(parameters, eventData) {
        // 密码验证逻辑
        if (parameters.minLength) {
            const password = eventData.password || eventData.data?.password;
            if (!password || password.length < parameters.minLength) {
                throw new Error(`密码长度至少需要 ${parameters.minLength} 位`);
            }
        }
        
        // 其他验证逻辑...
        return true;
    }

    /**
     * 执行日志记录
     */
    executeLog(parameters) {
        const { level, message } = parameters;
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
        
        console.log(logMessage);
        
        // 发送到日志系统
        this.sendToLogSystem(level, logMessage);
    }

    /**
     * 执行告警
     */
    async executeAlert(parameters) {
        const { level, message, channels } = parameters;
        
        if (channels.includes('system')) {
            this.showSystemAlert(level, message);
        }
        
        if (channels.includes('email')) {
            await this.sendEmailAlert(message, level);
        }
        
        if (channels.includes('sms')) {
            await this.sendSMSAlert(message, level);
        }
    }

    /**
     * 执行通知
     */
    async executeNotification(parameters) {
        const { method, message } = parameters;
        
        if (method.includes('system')) {
            this.showSystemNotification(message);
        }
        
        if (method.includes('email')) {
            await this.sendEmailNotification(message);
        }
    }

    /**
     * 记录执行信息
     */
    recordExecution(ruleId) {
        if (!this.ruleExecutions.has(ruleId)) {
            this.ruleExecutions.set(ruleId, []);
        }
        
        this.ruleExecutions.get(ruleId).push({
            timestamp: new Date().toISOString(),
            success: true
        });
    }

    /**
     * 记录错误
     */
    logError(ruleId, error) {
        if (!this.ruleExecutions.has(ruleId)) {
            this.ruleExecutions.set(ruleId, []);
        }
        
        this.ruleExecutions.get(ruleId).push({
            timestamp: new Date().toISOString(),
            success: false,
            error: error.message
        });
    }

    /**
     * 获取所有规则
     */
    getAllRules() {
        return Array.from(this.rules.values());
    }

    /**
     * 获取规则
     */
    getRule(ruleId) {
        return this.rules.get(ruleId);
    }

    /**
     * 更新规则
     */
    updateRule(ruleId, updates) {
        const rule = this.rules.get(ruleId);
        if (rule) {
            Object.assign(rule, updates);
            return true;
        }
        return false;
    }

    /**
     * 添加新规则
     */
    addRule(rule) {
        if (!rule.id) {
            throw new Error('规则必须包含ID');
        }
        
        this.rules.set(rule.id, {
            ...rule,
            lastExecuted: null,
            executionCount: 0,
            enabled: rule.enabled !== false
        });
        
        return true;
    }

    /**
     * 删除规则
     */
    removeRule(ruleId) {
        return this.rules.delete(ruleId);
    }

    /**
     * 启用/禁用规则
     */
    toggleRule(ruleId, enabled) {
        const rule = this.rules.get(ruleId);
        if (rule) {
            rule.enabled = enabled;
            return true;
        }
        return false;
    }

    /**
     * 获取规则执行统计
     */
    getRuleStatistics(ruleId) {
        const rule = this.rules.get(ruleId);
        const executions = this.ruleExecutions.get(ruleId) || [];
        
        return {
            rule: rule,
            executionCount: executions.length,
            successCount: executions.filter(e => e.success).length,
            failureCount: executions.filter(e => !e.success).length,
            lastExecuted: rule?.lastExecuted,
            recentExecutions: executions.slice(-10)
        };
    }

    /**
     * 系统告警显示
     */
    showSystemAlert(level, message) {
        // 实现系统告警显示逻辑
        if (window.showAlert) {
            window.showAlert(message, level);
        } else {
            alert(`[${level.toUpperCase()}] ${message}`);
        }
    }

    /**
     * 系统通知显示
     */
    showSystemNotification(message) {
        // 实现系统通知显示逻辑
        if (window.showNotification) {
            window.showNotification(message);
        } else {
            console.log(`通知: ${message}`);
        }
    }

    /**
     * 发送到日志系统
     */
    sendToLogSystem(level, message) {
        // 发送到日志系统
        if (window.logToSystem) {
            window.logToSystem(level, message);
        }
    }

    /**
     * 发送邮件告警
     */
    async sendEmailAlert(message, level) {
        // 实现邮件告警逻辑
        console.log(`邮件告警 [${level}]: ${message}`);
    }

    /**
     * 发送短信告警
     */
    async sendSMSAlert(message, level) {
        // 实现短信告警逻辑
        console.log(`短信告警 [${level}]: ${message}`);
    }

    /**
     * 发送邮件通知
     */
    async sendEmailNotification(message) {
        // 实现邮件通知逻辑
        console.log(`邮件通知: ${message}`);
    }
}

// 基础机制类
class BaseMechanism {
    constructor(config) {
        this.config = config;
        this.name = config.name;
        this.description = config.description;
        this.type = config.type;
        this.enabled = config.enabled !== false;
    }

    async initialize() {
        console.log(`初始化机制: ${this.name}`);
    }

    async execute(parameters) {
        console.log(`执行机制: ${this.name}`, parameters);
    }
}

// 密码验证器
class PasswordValidator extends BaseMechanism {
    async validatePassword(password, requirements) {
        const errors = [];
        
        if (requirements.minLength && password.length < requirements.minLength) {
            errors.push(`密码长度至少需要 ${requirements.minLength} 位`);
        }
        
        if (requirements.requireUppercase && !/[A-Z]/.test(password)) {
            errors.push('密码必须包含大写字母');
        }
        
        if (requirements.requireLowercase && !/[a-z]/.test(password)) {
            errors.push('密码必须包含小写字母');
        }
        
        if (requirements.requireNumbers && !/\d/.test(password)) {
            errors.push('密码必须包含数字');
        }
        
        if (requirements.requireSpecialChars && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
            errors.push('密码必须包含特殊字符');
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
    }
}

// 账户安全机制
class AccountSecurity extends BaseMechanism {
    async lockAccount(parameters) {
        console.log('锁定账户:', parameters);
        // 实现账户锁定逻辑
        return true;
    }

    async unlockAccount(userId) {
        console.log('解锁账户:', userId);
        // 实现账户解锁逻辑
        return true;
    }
}

// 会话管理器
class SessionManager extends BaseMechanism {
    async logout(parameters) {
        console.log('用户登出:', parameters);
        // 实现登出逻辑
        if (window.logout) {
            window.logout();
        }
        return true;
    }

    extendSession(sessionId) {
        console.log('延长会话:', sessionId);
        // 实现会话延长逻辑
        return true;
    }
}

// 缓存管理器
class CacheManager extends BaseMechanism {
    async cleanCache(parameters) {
        console.log('清理缓存:', parameters);
        // 实现缓存清理逻辑
        if (window.clearCache) {
            window.clearCache(parameters.target);
        }
        return true;
    }

    getCacheSize() {
        // 实现获取缓存大小逻辑
        return Math.random() * 100; // 模拟值
    }
}

// 日志管理器
class LogManager extends BaseMechanism {
    async rotateLog(parameters) {
        console.log('轮转日志:', parameters);
        // 实现日志轮转逻辑
        return true;
    }

    getLogSize() {
        // 实现获取日志大小逻辑
        return Math.random() * 50; // 模拟值
    }
}

// 备份管理器
class BackupManager extends BaseMechanism {
    async backup(parameters) {
        console.log('执行备份:', parameters);
        // 实现备份逻辑
        return {
            success: true,
            backupPath: `/Backups/backup_${Date.now()}.zip`,
            size: Math.random() * 1000 // 模拟大小
        };
    }

    async cleanup(parameters) {
        console.log('清理备份:', parameters);
        // 实现备份清理逻辑
        return true;
    }
}

// 系统监控器
class SystemMonitor extends BaseMechanism {
    async getSystemMetrics() {
        // 模拟系统指标
        return {
            cpu_usage: Math.random() * 100,
            memory_usage: Math.random() * 100,
            disk_usage: Math.random() * 100,
            network_usage: Math.random() * 100
        };
    }

    async restartHeavyProcesses(parameters) {
        console.log('重启重型进程:', parameters);
        // 实现重启进程逻辑
        return true;
    }
}

// 更新管理器
class UpdateManager extends BaseMechanism {
    async checkUpdates(parameters) {
        console.log('检查更新:', parameters);
        // 实现更新检查逻辑
        return {
            available: Math.random() > 0.5,
            version: '1.0.1',
            description: '系统更新'
        };
    }

    async installUpdate() {
        console.log('安装更新');
        // 实现更新安装逻辑
        return true;
    }
}

// 清理管理器
class CleanupManager extends BaseMechanism {
    async cleanup(parameters) {
        console.log('执行清理:', parameters);
        // 实现清理逻辑
        return {
            success: true,
            cleanedItems: Math.floor(Math.random() * 100),
            freedSpace: Math.random() * 1000
        };
    }
}

// 创建全局规则引擎实例
window.ruleEngine = new RuleEngine();

// 自动初始化
document.addEventListener('DOMContentLoaded', async () => {
    await window.ruleEngine.initialize();
});

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        RuleEngine,
        BaseMechanism,
        PasswordValidator,
        AccountSecurity,
        SessionManager,
        CacheManager,
        LogManager,
        BackupManager,
        SystemMonitor,
        UpdateManager,
        CleanupManager
    };
}