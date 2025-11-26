/**
 * 规则监测与自动修复核心模块
 * 负责系统规则的状态监测、异常检测、自动修复和重启功能
 */

const RulesMonitorCore = {
    // 初始化
    init: function() {
        console.log('规则监测与自动修复核心模块初始化中...');
        
        // 检查权限
        if (!AuthManager.checkPermission('rules.monitor')) {
            NotificationManager.showError('权限不足', '您没有足够的权限访问规则监测功能');
            return;
        }
        
        // 初始化状态
        this.rulesStatus = {};
        this.monitoringActive = false;
        this.monitoringInterval = null;
        this.autoRepairEnabled = true;
        
        // 从配置获取参数
        this.config = {
            monitoringInterval: CONFIG.rulesMonitor?.interval || 60000, // 默认1分钟
            repairTimeout: CONFIG.rulesMonitor?.repairTimeout || 30000, // 修复超时时间
            maxRepairAttempts: CONFIG.rulesMonitor?.maxRepairAttempts || 3, // 最大修复尝试次数
            deepSeekTimeout: CONFIG.deepSeek?.timeout || 60000 // DeepSeek模型超时时间
        };
        
        // 记录初始化日志
        Logging.logAction('规则监测模块初始化', { action: 'init', target: 'rules_monitor' });
        
        // 启动监测
        this.startMonitoring();
    },
    
    // 启动规则监测
    startMonitoring: function() {
        if (this.monitoringActive) {
            console.warn('规则监测已在运行中');
            return;
        }
        
        this.monitoringActive = true;
        
        // 立即执行一次监测
        this.performMonitoring();
        
        // 设置定时监测
        this.monitoringInterval = setInterval(() => {
            this.performMonitoring();
        }, this.config.monitoringInterval);
        
        console.log(`规则监测已启动，监测间隔: ${this.config.monitoringInterval}ms`);
        NotificationManager.showSuccess('监测启动', '规则自动监测功能已成功启动');
    },
    
    // 停止规则监测
    stopMonitoring: function() {
        if (!this.monitoringActive) {
            console.warn('规则监测未在运行中');
            return;
        }
        
        clearInterval(this.monitoringInterval);
        this.monitoringInterval = null;
        this.monitoringActive = false;
        
        console.log('规则监测已停止');
        NotificationManager.showInfo('监测停止', '规则自动监测功能已停止');
    },
    
    // 执行规则监测
    performMonitoring: async function() {
        try {
            console.log('开始规则监测...');
            
            // 获取所有规则
            const rules = await this.fetchAllRules();
            
            // 并行检查每个规则的状态
            const checkPromises = rules.map(rule => this.checkRuleStatus(rule));
            const results = await Promise.allSettled(checkPromises);
            
            // 处理检查结果
            let healthyCount = 0;
            let errorCount = 0;
            
            results.forEach((result, index) => {
                const rule = rules[index];
                
                if (result.status === 'fulfilled') {
                    const status = result.value;
                    this.rulesStatus[rule.id] = status;
                    
                    if (status.healthy) {
                        healthyCount++;
                    } else {
                        errorCount++;
                        // 发现异常，尝试修复
                        if (this.autoRepairEnabled) {
                            this.attemptRepair(rule, status);
                        }
                    }
                } else {
                    errorCount++;
                    this.rulesStatus[rule.id] = {
                        healthy: false,
                        error: '检查失败',
                        timestamp: new Date().toISOString(),
                        checkAttempts: 0
                    };
                }
            });
            
            // 更新状态UI
            this.updateMonitoringStats(healthyCount, rules.length - healthyCount - errorCount, errorCount);
            
            // 记录监测日志
            Logging.logAction('规则监测完成', {
                action: 'monitor',
                total: rules.length,
                healthy: healthyCount,
                warning: rules.length - healthyCount - errorCount,
                error: errorCount
            });
            
            console.log(`规则监测完成: 正常=${healthyCount}, 异常=${errorCount}`);
        } catch (error) {
            console.error('规则监测过程出错:', error);
            Logging.logError('规则监测失败', error);
            NotificationManager.showError('监测错误', '规则监测过程中发生错误');
        }
    },
    
    // 获取所有规则
    fetchAllRules: async function() {
        try {
            // 在实际应用中，这里应该调用API获取规则列表
            // 模拟API调用
            const response = await this.simulateAPIRequest('/api/rules', 'GET');
            
            if (response.success) {
                return response.data;
            } else {
                throw new Error('获取规则列表失败');
            }
        } catch (error) {
            console.error('获取规则列表出错:', error);
            // 返回模拟数据以便演示
            return this.generateMockRules();
        }
    },
    
    // 检查单个规则状态
    checkRuleStatus: async function(rule) {
        try {
            // 根据规则类型选择不同的检查方法
            let status;
            
            switch (rule.type) {
                case 'system':
                    status = await this.checkSystemRule(rule);
                    break;
                case 'business':
                    status = await this.checkBusinessRule(rule);
                    break;
                case 'security':
                    status = await this.checkSecurityRule(rule);
                    break;
                case 'performance':
                    status = await this.checkPerformanceRule(rule);
                    break;
                default:
                    status = await this.checkGenericRule(rule);
            }
            
            return status;
        } catch (error) {
            console.error(`检查规则 ${rule.id} 状态出错:`, error);
            return {
                healthy: false,
                error: error.message || '未知错误',
                timestamp: new Date().toISOString(),
                checkAttempts: (this.rulesStatus[rule.id]?.checkAttempts || 0) + 1
            };
        }
    },
    
    // 检查系统规则
    checkSystemRule: async function(rule) {
        // 模拟系统规则检查
        // 在实际应用中，这里应该执行实际的系统检查逻辑
        return new Promise((resolve) => {
            setTimeout(() => {
                // 模拟70%的规则正常，30%的规则异常
                const isHealthy = Math.random() > 0.3;
                
                resolve({
                    healthy: isHealthy,
                    error: isHealthy ? null : this.getRandomSystemError(),
                    timestamp: new Date().toISOString(),
                    details: isHealthy ? {
                        responseTime: Math.random() * 100 + 50,
                        memoryUsage: Math.random() * 50 + 20,
                        cpuUsage: Math.random() * 30 + 10
                    } : null,
                    checkAttempts: (this.rulesStatus[rule.id]?.checkAttempts || 0) + 1
                });
            }, 1000);
        });
    },
    
    // 检查业务规则
    checkBusinessRule: async function(rule) {
        // 模拟业务规则检查
        return new Promise((resolve) => {
            setTimeout(() => {
                const isHealthy = Math.random() > 0.25;
                
                resolve({
                    healthy: isHealthy,
                    error: isHealthy ? null : this.getRandomBusinessError(),
                    timestamp: new Date().toISOString(),
                    details: isHealthy ? {
                        dataConsistency: 'consistent',
                        ruleCoverage: Math.random() * 30 + 70
                    } : null,
                    checkAttempts: (this.rulesStatus[rule.id]?.checkAttempts || 0) + 1
                });
            }, 800);
        });
    },
    
    // 检查安全规则
    checkSecurityRule: async function(rule) {
        // 模拟安全规则检查
        return new Promise((resolve) => {
            setTimeout(() => {
                const isHealthy = Math.random() > 0.2;
                
                resolve({
                    healthy: isHealthy,
                    error: isHealthy ? null : this.getRandomSecurityError(),
                    timestamp: new Date().toISOString(),
                    details: isHealthy ? {
                        vulnerabilityScan: 'passed',
                        complianceStatus: 'compliant'
                    } : null,
                    checkAttempts: (this.rulesStatus[rule.id]?.checkAttempts || 0) + 1
                });
            }, 1200);
        });
    },
    
    // 检查性能规则
    checkPerformanceRule: async function(rule) {
        // 模拟性能规则检查
        return new Promise((resolve) => {
            setTimeout(() => {
                const responseTime = Math.random() * 200 + 50;
                const isHealthy = responseTime < 150;
                
                resolve({
                    healthy: isHealthy,
                    error: isHealthy ? null : `响应时间过长: ${responseTime.toFixed(2)}ms`,
                    timestamp: new Date().toISOString(),
                    details: {
                        responseTime: responseTime,
                        throughput: Math.random() * 1000 + 500,
                        errorRate: Math.random() * 2
                    },
                    checkAttempts: (this.rulesStatus[rule.id]?.checkAttempts || 0) + 1
                });
            }, 900);
        });
    },
    
    // 检查通用规则
    checkGenericRule: async function(rule) {
        // 模拟通用规则检查
        return new Promise((resolve) => {
            setTimeout(() => {
                const isHealthy = Math.random() > 0.3;
                
                resolve({
                    healthy: isHealthy,
                    error: isHealthy ? null : '规则执行失败',
                    timestamp: new Date().toISOString(),
                    checkAttempts: (this.rulesStatus[rule.id]?.checkAttempts || 0) + 1
                });
            }, 500);
        });
    },
    
    // 尝试修复规则
    attemptRepair: async function(rule, status) {
        console.log(`尝试修复规则 ${rule.id}: ${status.error}`);
        
        // 记录修复尝试
        Logging.logAction('开始规则修复', {
            action: 'repair_start',
            target: 'rule',
            targetId: rule.id,
            error: status.error
        });
        
        try {
            // 检查是否已经达到最大修复尝试次数
            const attemptCount = status.checkAttempts || 0;
            if (attemptCount >= this.config.maxRepairAttempts) {
                console.warn(`规则 ${rule.id} 已达到最大修复尝试次数: ${this.config.maxRepairAttempts}`);
                Logging.logAction('修复失败-达到最大尝试次数', {
                    action: 'repair_failed',
                    target: 'rule',
                    targetId: rule.id,
                    reason: 'max_attempts_reached'
                });
                NotificationManager.showWarning('修复失败', `规则 ${rule.id} 已达到最大修复尝试次数，需要人工干预`);
                return;
            }
            
            // 执行修复
            const repairResult = await this.executeRepair(rule, status);
            
            if (repairResult.success) {
                console.log(`规则 ${rule.id} 修复成功`);
                
                // 修复成功后，重启规则
                await this.restartRule(rule);
                
                // 记录成功日志
                Logging.logAction('规则修复成功', {
                    action: 'repair_success',
                    target: 'rule',
                    targetId: rule.id,
                    method: repairResult.method
                });
                
                NotificationManager.showSuccess('修复成功', `规则 ${rule.id} 已成功修复并重启`);
            } else {
                console.error(`规则 ${rule.id} 修复失败:`, repairResult.error);
                
                // 记录失败日志
                Logging.logAction('规则修复失败', {
                    action: 'repair_failed',
                    target: 'rule',
                    targetId: rule.id,
                    error: repairResult.error
                });
                
                // 尝试使用DeepSeek模型进行高级修复
                if (CONFIG.deepSeek?.enabled) {
                    await this.attemptDeepSeekRepair(rule, status);
                } else {
                    NotificationManager.showError('修复失败', `规则 ${rule.id} 修复失败: ${repairResult.error}`);
                }
            }
        } catch (error) {
            console.error(`规则 ${rule.id} 修复过程出错:`, error);
            Logging.logError('规则修复异常', error);
        }
    },
    
    // 执行修复
    executeRepair: async function(rule, status) {
        // 根据规则类型和错误类型选择修复方法
        switch (rule.type) {
            case 'system':
                return this.repairSystemRule(rule, status);
            case 'business':
                return this.repairBusinessRule(rule, status);
            case 'security':
                return this.repairSecurityRule(rule, status);
            case 'performance':
                return this.repairPerformanceRule(rule, status);
            default:
                return this.repairGenericRule(rule, status);
        }
    },
    
    // 修复系统规则
    repairSystemRule: async function(rule, status) {
        return new Promise((resolve) => {
            setTimeout(() => {
                // 模拟80%的修复成功率
                const success = Math.random() > 0.2;
                
                resolve({
                    success: success,
                    method: success ? 'service_restart' : null,
                    error: success ? null : '服务重启失败'
                });
            }, 2000);
        });
    },
    
    // 修复业务规则
    repairBusinessRule: async function(rule, status) {
        return new Promise((resolve) => {
            setTimeout(() => {
                // 模拟75%的修复成功率
                const success = Math.random() > 0.25;
                
                resolve({
                    success: success,
                    method: success ? 'data_validation_fix' : null,
                    error: success ? null : '数据验证修复失败'
                });
            }, 1500);
        });
    },
    
    // 修复安全规则
    repairSecurityRule: async function(rule, status) {
        return new Promise((resolve) => {
            setTimeout(() => {
                // 模拟70%的修复成功率
                const success = Math.random() > 0.3;
                
                resolve({
                    success: success,
                    method: success ? 'configuration_update' : null,
                    error: success ? null : '安全配置更新失败'
                });
            }, 2500);
        });
    },
    
    // 修复性能规则
    repairPerformanceRule: async function(rule, status) {
        return new Promise((resolve) => {
            setTimeout(() => {
                // 模拟85%的修复成功率
                const success = Math.random() > 0.15;
                
                resolve({
                    success: success,
                    method: success ? 'cache_clear' : null,
                    error: success ? null : '缓存清理失败'
                });
            }, 1800);
        });
    },
    
    // 修复通用规则
    repairGenericRule: async function(rule, status) {
        return new Promise((resolve) => {
            setTimeout(() => {
                // 模拟75%的修复成功率
                const success = Math.random() > 0.25;
                
                resolve({
                    success: success,
                    method: success ? 'rule_reset' : null,
                    error: success ? null : '规则重置失败'
                });
            }, 1200);
        });
    },
    
    // 尝试使用DeepSeek模型进行修复
    attemptDeepSeekRepair: async function(rule, status) {
        console.log(`尝试使用DeepSeek模型修复规则 ${rule.id}`);
        
        try {
            // 准备DeepSeek请求参数
            const deepSeekRequest = {
                rule: rule,
                error: status.error,
                context: {
                    systemInfo: await this.getSystemInfo(),
                    ruleHistory: await this.getRuleHistory(rule.id),
                    recentErrors: await this.getRecentErrors(rule.id, 5)
                },
                requestType: 'rule_repair'
            };
            
            // 调用DeepSeek模型
            const repairSolution = await this.callDeepSeekModel(deepSeekRequest);
            
            if (repairSolution && repairSolution.action) {
                // 执行DeepSeek建议的修复动作
                const executionResult = await this.executeDeepSeekAction(rule, repairSolution.action);
                
                if (executionResult.success) {
                    // 修复成功后重启规则
                    await this.restartRule(rule);
                    
                    Logging.logAction('DeepSeek模型修复成功', {
                        action: 'deepseek_repair_success',
                        target: 'rule',
                        targetId: rule.id,
                        solution: repairSolution.action
                    });
                    
                    NotificationManager.showSuccess('修复成功', `规则 ${rule.id} 已通过DeepSeek模型成功修复`);
                    
                    return { success: true };
                } else {
                    Logging.logAction('DeepSeek模型修复执行失败', {
                        action: 'deepseek_repair_failed',
                        target: 'rule',
                        targetId: rule.id,
                        error: executionResult.error
                    });
                    
                    NotificationManager.showError('修复失败', `DeepSeek模型修复执行失败: ${executionResult.error}`);
                }
            } else {
                Logging.logAction('DeepSeek模型未提供有效解决方案', {
                    action: 'deepseek_no_solution',
                    target: 'rule',
                    targetId: rule.id
                });
            }
        } catch (error) {
            console.error(`DeepSeek模型修复出错:`, error);
            Logging.logError('DeepSeek模型修复异常', error);
        }
        
        return { success: false };
    },
    
    // 调用DeepSeek模型
    callDeepSeekModel: async function(request) {
        try {
            // 模拟DeepSeek模型调用
            // 在实际应用中，这里应该调用真实的DeepSeek API
            return new Promise((resolve) => {
                setTimeout(() => {
                    // 模拟70%的成功率
                    const success = Math.random() > 0.3;
                    
                    if (success) {
                        resolve({
                            action: {
                                type: ['configuration_update', 'service_restart', 'cache_clear', 'code_fix'][Math.floor(Math.random() * 4)],
                                parameters: {
                                    timeout: 30000,
                                    retryCount: 2
                                },
                                explanation: `分析了规则 ${request.rule.id} 的错误 ${request.error}，建议执行此修复操作。`
                            },
                            confidence: Math.random() * 30 + 70,
                            alternativeSolutions: []
                        });
                    } else {
                        resolve(null);
                    }
                }, 3000);
            });
        } catch (error) {
            console.error('调用DeepSeek模型出错:', error);
            return null;
        }
    },
    
    // 执行DeepSeek建议的操作
    executeDeepSeekAction: async function(rule, action) {
        console.log(`执行DeepSeek建议的操作: ${action.type} 规则: ${rule.id}`);
        
        try {
            // 模拟执行动作
            return new Promise((resolve) => {
                setTimeout(() => {
                    // 模拟85%的执行成功率
                    const success = Math.random() > 0.15;
                    
                    resolve({
                        success: success,
                        error: success ? null : `执行 ${action.type} 失败`
                    });
                }, 2000);
            });
        } catch (error) {
            console.error('执行DeepSeek动作出错:', error);
            return { success: false, error: error.message };
        }
    },
    
    // 重启规则
    restartRule: async function(rule) {
        try {
            console.log(`重启规则: ${rule.id}`);
            
            // 模拟规则重启
            return new Promise((resolve) => {
                setTimeout(() => {
                    resolve({ success: true });
                }, 1000);
            });
        } catch (error) {
            console.error(`重启规则 ${rule.id} 出错:`, error);
            throw error;
        }
    },
    
    // 手动触发规则检查
    triggerRuleCheck: async function(ruleId) {
        try {
            // 获取特定规则
            const rule = await this.fetchRuleById(ruleId);
            
            if (rule) {
                // 检查规则状态
                const status = await this.checkRuleStatus(rule);
                this.rulesStatus[ruleId] = status;
                
                // 如果规则异常且开启了自动修复，尝试修复
                if (!status.healthy && this.autoRepairEnabled) {
                    await this.attemptRepair(rule, status);
                }
                
                return status;
            }
            
            return null;
        } catch (error) {
            console.error(`手动检查规则 ${ruleId} 出错:`, error);
            return { healthy: false, error: error.message };
        }
    },
    
    // 手动触发规则修复
    triggerRuleRepair: async function(ruleId) {
        try {
            // 获取规则
            const rule = await this.fetchRuleById(ruleId);
            
            if (rule) {
                // 检查当前状态
                const status = this.rulesStatus[ruleId] || { healthy: false, error: '未知错误' };
                
                // 强制修复
                await this.attemptRepair(rule, status);
                
                // 重新检查状态
                return this.triggerRuleCheck(ruleId);
            }
            
            return null;
        } catch (error) {
            console.error(`手动修复规则 ${ruleId} 出错:`, error);
            return { healthy: false, error: error.message };
        }
    },
    
    // 获取规则详情
    fetchRuleById: async function(ruleId) {
        try {
            // 模拟API调用
            const response = await this.simulateAPIRequest(`/api/rules/${ruleId}`, 'GET');
            
            if (response.success) {
                return response.data;
            }
            
            // 如果API调用失败，从模拟数据中查找
            const rules = this.generateMockRules();
            return rules.find(rule => rule.id === ruleId) || null;
        } catch (error) {
            console.error(`获取规则 ${ruleId} 详情出错:`, error);
            return null;
        }
    },
    
    // 生成模拟规则数据
    generateMockRules: function() {
        return [
            {
                id: 'rule-001',
                name: '系统资源监控规则',
                type: 'system',
                description: '监控系统CPU、内存和磁盘使用率',
                priority: 'high',
                createdAt: '2024-01-01T00:00:00Z',
                lastUpdated: '2024-01-15T00:00:00Z',
                enabled: true
            },
            {
                id: 'rule-002',
                name: '用户登录安全规则',
                type: 'security',
                description: '检测异常登录行为和安全风险',
                priority: 'high',
                createdAt: '2024-01-02T00:00:00Z',
                lastUpdated: '2024-01-10T00:00:00Z',
                enabled: true
            },
            {
                id: 'rule-003',
                name: '数据一致性规则',
                type: 'business',
                description: '确保业务数据的一致性和完整性',
                priority: 'medium',
                createdAt: '2024-01-03T00:00:00Z',
                lastUpdated: '2024-01-20T00:00:00Z',
                enabled: true
            },
            {
                id: 'rule-004',
                name: 'API响应时间监控',
                type: 'performance',
                description: '监控关键API的响应时间和性能指标',
                priority: 'high',
                createdAt: '2024-01-04T00:00:00Z',
                lastUpdated: '2024-01-25T00:00:00Z',
                enabled: true
            },
            {
                id: 'rule-005',
                name: '数据库连接池监控',
                type: 'system',
                description: '监控数据库连接池状态和性能',
                priority: 'medium',
                createdAt: '2024-01-05T00:00:00Z',
                lastUpdated: '2024-01-30T00:00:00Z',
                enabled: true
            },
            {
                id: 'rule-006',
                name: '密码强度验证规则',
                type: 'security',
                description: '验证用户密码强度和合规性',
                priority: 'medium',
                createdAt: '2024-01-06T00:00:00Z',
                lastUpdated: '2024-02-05T00:00:00Z',
                enabled: true
            },
            {
                id: 'rule-007',
                name: '业务流程完整性规则',
                type: 'business',
                description: '确保关键业务流程的完整性',
                priority: 'high',
                createdAt: '2024-01-07T00:00:00Z',
                lastUpdated: '2024-02-10T00:00:00Z',
                enabled: true
            },
            {
                id: 'rule-008',
                name: '缓存命中率监控',
                type: 'performance',
                description: '监控系统缓存的命中率和效率',
                priority: 'medium',
                createdAt: '2024-01-08T00:00:00Z',
                lastUpdated: '2024-02-15T00:00:00Z',
                enabled: true
            }
        ];
    },
    
    // 获取随机系统错误
    getRandomSystemError: function() {
        const errors = [
            '系统资源占用过高',
            '服务连接超时',
            '配置文件错误',
            '依赖服务不可用',
            '权限不足',
            '内存溢出',
            '磁盘空间不足'
        ];
        return errors[Math.floor(Math.random() * errors.length)];
    },
    
    // 获取随机业务错误
    getRandomBusinessError: function() {
        const errors = [
            '数据验证失败',
            '业务规则冲突',
            '依赖数据缺失',
            '状态转换异常',
            '业务逻辑错误',
            '数据一致性校验失败'
        ];
        return errors[Math.floor(Math.random() * errors.length)];
    },
    
    // 获取随机安全错误
    getRandomSecurityError: function() {
        const errors = [
            '安全配置过期',
            '未授权访问尝试',
            '安全漏洞检测',
            '加密算法过时',
            '安全策略违规',
            '异常访问模式检测'
        ];
        return errors[Math.floor(Math.random() * errors.length)];
    },
    
    // 获取系统信息
    getSystemInfo: async function() {
        // 模拟系统信息
        return {
            os: 'Linux',
            version: 'Ubuntu 20.04 LTS',
            uptime: '168h 30m',
            cpuLoad: [0.85, 0.72, 0.91],
            memoryUsage: {
                total: 32768,
                used: 18432,
                free: 14336
            },
            diskUsage: {
                total: 1024,
                used: 685,
                free: 339
            }
        };
    },
    
    // 获取规则历史
    getRuleHistory: async function(ruleId) {
        // 模拟规则历史
        return [
            {
                timestamp: new Date(Date.now() - 86400000).toISOString(),
                action: 'repair',
                result: 'success',
                details: '自动修复成功'
            },
            {
                timestamp: new Date(Date.now() - 172800000).toISOString(),
                action: 'update',
                result: 'success',
                details: '规则配置更新'
            },
            {
                timestamp: new Date(Date.now() - 259200000).toISOString(),
                action: 'check',
                result: 'warning',
                details: '性能警告'
            }
        ];
    },
    
    // 获取最近错误
    getRecentErrors: async function(ruleId, count = 5) {
        // 模拟最近错误
        const errors = [];
        for (let i = 0; i < count; i++) {
            errors.push({
                timestamp: new Date(Date.now() - i * 3600000).toISOString(),
                error: this.getRandomSystemError(),
                severity: ['warning', 'error', 'critical'][Math.floor(Math.random() * 3)]
            });
        }
        return errors;
    },
    
    // 更新监测统计信息
    updateMonitoringStats: function(healthy, warning, error) {
        // 更新UI统计信息
        const statsElement = document.getElementById('rules-monitoring-stats');
        if (statsElement) {
            statsElement.innerHTML = `
                <div class="stat-item healthy">
                    <span class="stat-number">${healthy}</span>
                    <span class="stat-label">正常</span>
                </div>
                <div class="stat-item warning">
                    <span class="stat-number">${warning}</span>
                    <span class="stat-label">警告</span>
                </div>
                <div class="stat-item error">
                    <span class="stat-number">${error}</span>
                    <span class="stat-label">异常</span>
                </div>
                <div class="stat-item total">
                    <span class="stat-number">${healthy + warning + error}</span>
                    <span class="stat-label">总计</span>
                </div>
            `;
        }
    },
    
    // 切换自动修复功能
    toggleAutoRepair: function(enabled) {
        this.autoRepairEnabled = enabled;
        
        Logging.logAction('自动修复功能状态变更', {
            action: 'toggle_auto_repair',
            enabled: enabled
        });
        
        NotificationManager.showInfo('设置已更新', `自动修复功能已${enabled ? '启用' : '禁用'}`);
    },
    
    // 获取当前监测状态
    getMonitoringStatus: function() {
        return {
            active: this.monitoringActive,
            interval: this.config.monitoringInterval,
            autoRepairEnabled: this.autoRepairEnabled,
            lastUpdate: new Date().toISOString(),
            rulesCount: Object.keys(this.rulesStatus).length
        };
    },
    
    // 获取规则状态报告
    generateStatusReport: function() {
        const report = {
            generatedAt: new Date().toISOString(),
            summary: {
                total: Object.keys(this.rulesStatus).length,
                healthy: 0,
                error: 0
            },
            rules: []
        };
        
        // 统计状态
        Object.entries(this.rulesStatus).forEach(([ruleId, status]) => {
            if (status.healthy) {
                report.summary.healthy++;
            } else {
                report.summary.error++;
            }
            
            report.rules.push({
                ruleId: ruleId,
                healthy: status.healthy,
                error: status.error,
                lastChecked: status.timestamp
            });
        });
        
        return report;
    },
    
    // 模拟API请求
    simulateAPIRequest: function(endpoint, method, data = null) {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    success: true,
                    data: this.generateMockRules()
                });
            }, 500);
        });
    }
};

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', function() {
    // 确保AuthManager已经加载
    if (typeof AuthManager !== 'undefined') {
        RulesMonitorCore.init();
    } else {
        console.warn('AuthManager未加载，延迟初始化RulesMonitorCore');
        setTimeout(() => {
            if (typeof AuthManager !== 'undefined') {
                RulesMonitorCore.init();
            }
        }, 1000);
    }
});

// 暴露模块到全局
window.RulesMonitorCore = RulesMonitorCore;