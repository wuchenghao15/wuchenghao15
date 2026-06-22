/**
 * MTSCOS AI System - 沙盒系统管理员AI员工
 * 版本: 4.4.0
 * 描述: 专注于沙盒环境管理、隔离测试、安全隔离和沙盒资源控制
 */

class SandboxManager {
    constructor() {
        this.id = 'sandbox-manager';
        this.name = '沙盒系统管理员';
        this.icon = 'fa-shield-alt';
        this.color = '#0ea5e9';
        this.gradient = 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)';
        this.role = '沙盒系统专家';
        this.description = '专注于沙盒环境管理、隔离测试、安全隔离和资源控制';
        this.abilities = [
            '沙盒管理',
            '隔离测试',
            '安全隔离',
            '资源控制',
            '沙盒恢复',
            '权限管理'
        ];
        this.status = 'active';
        this.workload = 15;
        this.efficiency = 98;
        this.sandboxes = new Map();
        this.sandboxCounter = 0;
        this.isolationRules = this.initIsolationRules();
    }

    // ==================== 隔离规则 ====================

    initIsolationRules() {
        return {
            network: {
                blocked: ['external-api.com', 'malicious-site.net'],
                allowed: ['localhost', '*.mtscos.com'],
                maxConnections: 10
            },
            storage: {
                maxLocalStorage: 5 * 1024 * 1024, // 5MB
                maxSessionStorage: 2 * 1024 * 1024, // 2MB
                allowIndexedDB: false,
                allowCookies: false
            },
            script: {
                allowEval: false,
                allowInlineScripts: false,
                allowDynamicCode: false,
                maxScriptSize: 1024 * 1024 // 1MB
            },
            dom: {
                maxElements: 1000,
                maxEventListeners: 100,
                allowIframes: false,
                allowPopups: false
            },
            resource: {
                maxCpuTime: 5000, // 5秒
                maxMemory: 100 * 1024 * 1024, // 100MB
                maxNetworkRequests: 20
            }
        };
    }

    // ==================== 沙盒创建 ====================

    // 创建沙盒
    createSandbox(config = {}) {
        const sandboxId = `sandbox_${++this.sandboxCounter}_${Date.now()}`;
        
        const sandbox = {
            id: sandboxId,
            name: config.name || `沙盒_${this.sandboxCounter}`,
            type: config.type || 'isolated', // isolated, restricted, full
            status: 'creating',
            createdAt: Date.now(),
            createdBy: config.userId || 'system',
            config: this.getSandboxConfig(config),
            state: {
                memory: 0,
                cpuTime: 0,
                networkRequests: 0,
                errors: []
            },
            resources: {
                limits: {
                    memory: config.memoryLimit || 100 * 1024 * 1024,
                    cpuTime: config.cpuLimit || 5000,
                    networkRequests: config.networkLimit || 20
                },
                usage: {
                    memory: 0,
                    cpuTime: 0,
                    networkRequests: 0
                }
            },
            permissions: this.getSandboxPermissions(config),
            isolation: this.applyIsolation(config),
            history: []
        };

        sandbox.status = 'ready';
        this.sandboxes.set(sandboxId, sandbox);

        this.logAction(sandboxId, 'create', { type: config.type });

        return sandbox;
    }

    // 获取沙盒配置
    getSandboxConfig(config) {
        const baseConfig = {
            debug: config.debug || false,
            verbose: config.verbose || false,
            autoCleanup: config.autoCleanup !== false,
            timeout: config.timeout || 60000, // 1分钟
            enableMonitoring: config.monitoring !== false
        };

        return { ...baseConfig, ...config };
    }

    // 获取沙盒权限
    getSandboxPermissions(config) {
        const type = config.type || 'isolated';
        
        const permissionSets = {
            isolated: {
                network: 'blocked',
                storage: 'local',
                scripts: 'restricted',
                dom: 'restricted',
                apis: ['console', 'setTimeout', 'setInterval']
            },
            restricted: {
                network: 'internal',
                storage: 'session',
                scripts: 'allowed',
                dom: 'sandboxed',
                apis: ['console', 'fetch', 'setTimeout', 'setInterval', 'localStorage']
            },
            full: {
                network: 'full',
                storage: 'full',
                scripts: 'full',
                dom: 'full',
                apis: ['*']
            }
        };

        return permissionSets[type] || permissionSets.isolated;
    }

    // 应用隔离
    applyIsolation(config) {
        const type = config.type || 'isolated';
        return {
            level: type === 'isolated' ? 'strict' : type === 'restricted' ? 'moderate' : 'minimal',
            rules: this.isolationRules,
            customRules: config.customRules || []
        };
    }

    // ==================== 沙盒执行 ====================

    // 在沙盒中执行代码
    async executeInSandbox(sandboxId, code, options = {}) {
        const sandbox = this.sandboxes.get(sandboxId);
        if (!sandbox) {
            return { success: false, error: '沙盒不存在' };
        }

        if (sandbox.status !== 'ready') {
            return { success: false, error: '沙盒未就绪' };
        }

        const execution = {
            id: `exec_${Date.now()}`,
            sandboxId,
            status: 'running',
            startedAt: Date.now(),
            code: options.showCode ? code : '[hidden]',
            result: null,
            error: null
        };

        try {
            // 检查资源限制
            if (!this.checkResourceLimits(sandbox, execution)) {
                throw new Error('资源使用超限');
            }

            // 创建沙盒上下文
            const context = this.createExecutionContext(sandbox, options);

            // 执行代码（模拟）
            execution.result = await this.simulateExecution(code, context);
            execution.status = 'completed';
            execution.completedAt = Date.now();
            execution.duration = execution.completedAt - execution.startedAt;

            this.logAction(sandboxId, 'execute', {
                duration: execution.duration,
                success: true
            });

        } catch (error) {
            execution.status = 'failed';
            execution.error = error.message;
            execution.completedAt = Date.now();

            sandbox.state.errors.push({
                error: error.message,
                timestamp: Date.now()
            });

            this.logAction(sandboxId, 'execute', {
                success: false,
                error: error.message
            });
        }

        return execution;
    }

    // 创建执行上下文
    createExecutionContext(sandbox, options) {
        return {
            console: {
                log: (...args) => options.verbose && console.log('[Sandbox]', ...args),
                warn: (...args) => console.warn('[Sandbox]', ...args),
                error: (...args) => console.error('[Sandbox]', ...args)
            },
            allowedAPIs: sandbox.permissions.apis,
            restrictions: sandbox.isolation.rules,
            timeout: sandbox.config.timeout
        };
    }

    // 模拟执行
    async simulateExecution(code, context) {
        // 模拟代码执行
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // 检查代码安全
        this.checkCodeSecurity(code, context.restrictions);

        return {
            output: '模拟执行成功',
            logs: context.console.log ? ['代码执行完成'] : []
        };
    }

    // 检查代码安全
    checkCodeSecurity(code, restrictions) {
        // 检查危险模式
        const dangerousPatterns = [
            /eval\s*\(/,
            /Function\s*\(/,
            /document\.write\s*\(/,
            /innerHTML\s*=/,
            /outerHTML\s*=/
        ];

        for (const pattern of dangerousPatterns) {
            if (pattern.test(code)) {
                if (!restrictions.script.allowEval && /eval/.test(pattern.source)) {
                    throw new Error('eval 被禁用');
                }
                if (!restrictions.script.allowInlineScripts && /document\.write/.test(pattern.source)) {
                    throw new Error('inline script 被禁用');
                }
            }
        }

        return true;
    }

    // 检查资源限制
    checkResourceLimits(sandbox, execution) {
        const { limits, usage } = sandbox.resources;

        if (usage.memory > limits.memory) return false;
        if (usage.cpuTime > limits.cpuTime) return false;
        if (usage.networkRequests > limits.networkRequests) return false;

        return true;
    }

    // ==================== 沙盒管理 ====================

    // 获取沙盒信息
    getSandboxInfo(sandboxId) {
        return this.sandboxes.get(sandboxId) || null;
    }

    // 列出所有沙盒
    listSandboxes(filter = {}) {
        let list = Array.from(this.sandboxes.values());

        if (filter.status) {
            list = list.filter(s => s.status === filter.status);
        }

        if (filter.type) {
            list = list.filter(s => s.type === filter.type);
        }

        if (filter.createdBy) {
            list = list.filter(s => s.createdBy === filter.createdBy);
        }

        return list;
    }

    // 暂停沙盒
    pauseSandbox(sandboxId) {
        const sandbox = this.sandboxes.get(sandboxId);
        if (!sandbox) return { success: false, error: '沙盒不存在' };

        sandbox.status = 'paused';
        this.logAction(sandboxId, 'pause');

        return { success: true };
    }

    // 恢复沙盒
    resumeSandbox(sandboxId) {
        const sandbox = this.sandboxes.get(sandboxId);
        if (!sandbox) return { success: false, error: '沙盒不存在' };

        sandbox.status = 'ready';
        this.logAction(sandboxId, 'resume');

        return { success: true };
    }

    // 销毁沙盒
    destroySandbox(sandboxId, options = {}) {
        const sandbox = this.sandboxes.get(sandboxId);
        if (!sandbox) return { success: false, error: '沙盒不存在' };

        // 备份状态（如果需要）
        if (options.backup) {
            this.backupSandboxState(sandboxId);
        }

        // 清理资源
        this.cleanupSandboxResources(sandbox);

        // 删除沙盒
        this.sandboxes.delete(sandboxId);

        this.logAction(sandboxId, 'destroy');

        return { success: true };
    }

    // 清理沙盒资源
    cleanupSandboxResources(sandbox) {
        sandbox.status = 'destroyed';
        sandbox.resources.usage = {
            memory: 0,
            cpuTime: 0,
            networkRequests: 0
        };
    }

    // ==================== 沙盒恢复 ====================

    // 备份沙盒状态
    backupSandboxState(sandboxId) {
        const sandbox = this.sandboxes.get(sandboxId);
        if (!sandbox) return null;

        const backup = {
            id: `backup_${Date.now()}`,
            sandboxId,
            state: JSON.parse(JSON.stringify(sandbox.state)),
            createdAt: Date.now()
        };

        const backups = JSON.parse(localStorage.getItem('mtscos_sandbox_backups') || '[]');
        backups.push(backup);
        localStorage.setItem('mtscos_sandbox_backups', JSON.stringify(backups));

        return backup;
    }

    // 恢复沙盒状态
    restoreSandboxState(sandboxId, backupId) {
        const backups = JSON.parse(localStorage.getItem('mtscos_sandbox_backups') || '[]');
        const backup = backups.find(b => b.id === backupId);

        if (!backup) return { success: false, error: '备份不存在' };

        const sandbox = this.sandboxes.get(sandboxId);
        if (!sandbox) return { success: false, error: '沙盒不存在' };

        sandbox.state = JSON.parse(JSON.stringify(backup.state));

        return { success: true };
    }

    // ==================== 辅助方法 ====================

    // 记录操作日志
    logAction(sandboxId, action, details) {
        const sandbox = this.sandboxes.get(sandboxId);
        if (!sandbox) return;

        sandbox.history.push({
            action,
            details,
            timestamp: Date.now()
        });

        // 只保留最近100条记录
        if (sandbox.history.length > 100) {
            sandbox.history.shift();
        }
    }

    // 获取沙盒历史
    getSandboxHistory(sandboxId, limit = 20) {
        const sandbox = this.sandboxes.get(sandboxId);
        if (!sandbox) return [];

        return sandbox.history.slice(-limit);
    }

    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            workload: this.workload,
            efficiency: this.efficiency,
            totalSandboxes: this.sandboxes.size,
            activeSandboxes: Array.from(this.sandboxes.values()).filter(s => s.status === 'ready').length
        };
    }
}

// 创建全局实例
window.sandboxManager = new SandboxManager();

// 导出
window.MTSCOS_SandboxManager = SandboxManager;
