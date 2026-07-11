/**
 * MTSCOS AI System - AI调度员
 * 版本: 4.3.0
 * 描述: 智能调度所有系统功能和AI员工的核心调度员
 */

class AIDispatcher {
    constructor(database, syncService) {
        this.database = database;
        this.syncService = syncService;
        this.employees = [];
        this.tasks = new Map();
        this.taskQueue = [];
        this.isRunning = false;
        this.schedulingInterval = 5000;
        this.workloadThreshold = 80;
        this.isReady = false;
        this.initPromise = this.init();
    }
    
    async init() {
        // 等待数据库就绪
        await this.database.waitForReady();
        
        // 加载AI员工
        await this.loadEmployees();
        
        // 启动调度循环
        this.startScheduling();
        
        // 初始化默认任务
        await this.initDefaultTasks();
        
        this.isReady = true;
        console.log('✅ AI调度员初始化成功');
    }
    
    async loadEmployees() {
        const employees = await this.database.getAllAIEmployees();
        if (employees.length === 0) {
            // 如果数据库中没有员工，使用配置中的默认员工
            this.employees = this.getDefaultEmployees();
            // 保存到数据库
            for (const employee of this.employees) {
                await this.database.saveAIEmployee(employee);
            }
        } else {
            this.employees = employees;
        }
    }
    
    getDefaultEmployees() {
        return [
            {
                id: 'art-designer',
                name: '艺术设计师',
                role: 'visual_designer',
                color: '#ec4899',
                icon: 'fa-palette',
                abilities: ['ui_design', 'color_scheme', 'animation', 'brand'],
                status: 'active',
                workload: 75,
                efficiency: 92,
                lastTask: null,
                taskCount: 0,
                completedTasks: 0
            },
            {
                id: 'code-developer',
                name: '代码开发师',
                role: 'fullstack_developer',
                color: '#3b82f6',
                icon: 'fa-code',
                abilities: ['frontend', 'backend', 'api_design', 'optimization'],
                status: 'active',
                workload: 60,
                efficiency: 95,
                lastTask: null,
                taskCount: 0,
                completedTasks: 0
            },
            {
                id: 'data-analyst',
                name: '数据分析师',
                role: 'data_analyst',
                color: '#10b981',
                icon: 'fa-chart-line',
                abilities: ['analysis', 'prediction', 'visualization', 'reporting'],
                status: 'active',
                workload: 45,
                efficiency: 88,
                lastTask: null,
                taskCount: 0,
                completedTasks: 0
            },
            {
                id: 'security-expert',
                name: '安全专家',
                role: 'security_engineer',
                color: '#ef4444',
                icon: 'fa-shield-alt',
                abilities: ['audit', 'vulnerability', 'permissions', 'response'],
                status: 'active',
                workload: 30,
                efficiency: 97,
                lastTask: null,
                taskCount: 0,
                completedTasks: 0
            },
            {
                id: 'product-manager',
                name: '产品经理',
                role: 'product_manager',
                color: '#8b5cf6',
                icon: 'fa-tasks',
                abilities: ['requirements', 'project', 'research', 'iteration'],
                status: 'active',
                workload: 55,
                efficiency: 90,
                lastTask: null,
                taskCount: 0,
                completedTasks: 0
            },
            {
                id: 'qa-tester',
                name: '测试工程师',
                role: 'qa_engineer',
                color: '#f59e0b',
                icon: 'fa-bug',
                abilities: ['testing', 'automation', 'performance', 'tracking'],
                status: 'active',
                workload: 40,
                efficiency: 93,
                lastTask: null,
                taskCount: 0,
                completedTasks: 0
            },
            {
                id: 'devops-engineer',
                name: '运维工程师',
                role: 'devops_engineer',
                color: '#06b6d4',
                icon: 'fa-server',
                abilities: ['servers', 'containers', 'ci_cd', 'monitoring'],
                status: 'active',
                workload: 35,
                efficiency: 91,
                lastTask: null,
                taskCount: 0,
                completedTasks: 0
            },
            {
                id: 'ux-researcher',
                name: '用户体验研究员',
                role: 'ux_researcher',
                color: '#14b8a6',
                icon: 'fa-user-check',
                abilities: ['research', 'testing', 'analysis', 'optimization'],
                status: 'active',
                workload: 50,
                efficiency: 89,
                lastTask: null,
                taskCount: 0,
                completedTasks: 0
            },
            {
                id: 'system-dispatcher',
                name: '系统调度员',
                role: 'system_dispatcher',
                color: '#f43f5e',
                icon: 'fa-cogs',
                abilities: ['scheduling', 'orchestration', 'monitoring', 'optimization'],
                status: 'active',
                workload: 20,
                efficiency: 99,
                lastTask: null,
                taskCount: 0,
                completedTasks: 0
            }
        ];
    }
    
    async initDefaultTasks() {
        // 初始化定时任务
        this.scheduleRecurringTask({
            id: 'health-check',
            name: '系统健康检查',
            type: 'system',
            interval: 60000,
            lastRun: 0,
            enabled: true,
            targetEmployee: 'security-expert'
        });
        
        this.scheduleRecurringTask({
            id: 'sync-data',
            name: '数据同步',
            type: 'data',
            interval: 30000,
            lastRun: 0,
            enabled: true,
            targetEmployee: 'data-analyst'
        });
        
        this.scheduleRecurringTask({
            id: 'performance-monitor',
            name: '性能监控',
            type: 'performance',
            interval: 15000,
            lastRun: 0,
            enabled: true,
            targetEmployee: 'devops-engineer'
        });
        
        this.scheduleRecurringTask({
            id: 'cleanup',
            name: '系统清理',
            type: 'system',
            interval: 3600000,
            lastRun: 0,
            enabled: true,
            targetEmployee: 'devops-engineer'
        });
        
        this.scheduleRecurringTask({
            id: 'backup',
            name: '数据备份',
            type: 'data',
            interval: 7200000,
            lastRun: 0,
            enabled: true,
            targetEmployee: 'data-analyst'
        });
    }
    
    // ==================== 调度循环 ====================
    
    startScheduling() {
        this.isRunning = true;
        
        this.schedulingLoop = setInterval(() => {
            this.processTaskQueue();
            this.runRecurringTasks();
            this.balanceWorkload();
        }, this.schedulingInterval);
        
        console.log('🔄 AI调度循环已启动');
    }
    
    stopScheduling() {
        this.isRunning = false;
        if (this.schedulingLoop) {
            clearInterval(this.schedulingLoop);
        }
        console.log('⏹️ AI调度循环已停止');
    }
    
    // ==================== 任务队列处理 ====================
    
    async processTaskQueue() {
        while (this.taskQueue.length > 0) {
            const task = this.taskQueue.shift();
            await this.assignTask(task);
        }
    }
    
    async assignTask(task) {
        // 找到最适合的员工
        const employee = this.findBestEmployee(task);
        
        if (employee) {
            // 更新员工状态
            await this.updateEmployeeTask(employee, task);
            
            // 执行任务
            await this.executeTask(task, employee);
            
            // 更新任务状态
            task.status = 'completed';
            task.completedAt = Date.now();
            
            // 更新员工完成计数
            await this.updateEmployeeCompletion(employee);
        } else {
            task.status = 'failed';
            task.error = '没有可用的员工';
            
            // 重新放入队列
            this.taskQueue.push(task);
        }
        
        // 记录任务到数据库
        await this.database.addLog(`任务 ${task.name} ${task.status}`, 'info', 'dispatcher', {
            taskId: task.id,
            employee: employee?.name,
            duration: task.completedAt - task.startedAt
        });
        
        // 触发任务完成事件
        document.dispatchEvent(new CustomEvent('mtscos:task:completed', {
            detail: { task, employee }
        }));
    }
    
    findBestEmployee(task) {
        const requiredAbility = task.ability;
        
        // 找到具备对应能力且工作负载最低的员工
        const candidates = this.employees.filter(e => 
            e.status === 'active' && 
            e.workload < this.workloadThreshold &&
            (!requiredAbility || e.abilities.includes(requiredAbility))
        );
        
        if (candidates.length === 0) {
            return null;
        }
        
        // 按效率和工作负载排序
        candidates.sort((a, b) => {
            const scoreA = a.efficiency - a.workload;
            const scoreB = b.efficiency - b.workload;
            return scoreB - scoreA;
        });
        
        return candidates[0];
    }
    
    async executeTask(task, employee) {
        task.startedAt = Date.now();
        
        try {
            // 根据任务类型执行不同的逻辑
            switch (task.type) {
                case 'system':
                    await this.executeSystemTask(task);
                    break;
                case 'data':
                    await this.executeDataTask(task);
                    break;
                case 'ai':
                    await this.executeAITask(task);
                    break;
                case 'security':
                    await this.executeSecurityTask(task);
                    break;
                case 'performance':
                    await this.executePerformanceTask(task);
                    break;
                default:
                    await this.executeGenericTask(task);
                    break;
            }
        } catch (error) {
            task.error = error.message;
            task.status = 'failed';
        }
    }
    
    async executeSystemTask(task) {
        switch (task.id) {
            case 'health-check':
                await this.performHealthCheck();
                break;
            case 'cleanup':
                await this.performCleanup();
                break;
        }
    }
    
    async executeDataTask(task) {
        switch (task.id) {
            case 'sync-data':
                await this.syncService.performSync();
                break;
            case 'backup':
                await this.performBackup();
                break;
        }
    }
    
    async executeAITask(task) {
        // AI任务执行
    }
    
    async executeSecurityTask(task) {
        // 安全任务执行
    }
    
    async executePerformanceTask(task) {
        switch (task.id) {
            case 'performance-monitor':
                await this.performPerformanceMonitoring();
                break;
        }
    }
    
    async executeGenericTask(task) {
        // 通用任务执行
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // ==================== 系统任务 ====================
    
    async performHealthCheck() {
        const health = await this.database.healthCheck();
        
        // 检查各模块状态
        for (const [name, status] of Object.entries(health.collections)) {
            if (status.status !== 'ok') {
                await this.database.addLog(`数据库集合 ${name} 异常`, 'warning', 'dispatcher');
            }
        }
        
        await this.database.addLog('系统健康检查完成', 'info', 'dispatcher', health);
    }
    
    async performCleanup() {
        // 清理过期日志
        await this.database.trimLogs();
        
        // 清理过期性能指标
        await this.database.trimPerformanceMetrics();
        
        // 清理过期同步记录
        await this.database.trimSyncHistory();
        
        await this.database.addLog('系统清理完成', 'info', 'dispatcher');
    }
    
    async performBackup() {
        const exportData = await this.database.exportData();
        
        // 保存备份到本地存储
        localStorage.setItem('mtscos_backup', JSON.stringify(exportData));
        
        await this.database.addLog('数据备份完成', 'info', 'dispatcher', {
            size: JSON.stringify(exportData).length
        });
    }
    
    async performPerformanceMonitoring() {
        // 记录性能指标
        if (performance && performance.mark) {
            // 获取性能数据
            const metrics = {
                memory: performance.memory?.usedJSHeapSize || 0,
                timeOrigin: performance.timeOrigin
            };
            
            await this.database.addPerformanceMetric('system', metrics);
        }
    }
    
    // ==================== 定时任务 ====================
    
    scheduleRecurringTask(task) {
        this.tasks.set(task.id, task);
    }
    
    async runRecurringTasks() {
        const now = Date.now();
        
        for (const [taskId, task] of this.tasks) {
            if (task.enabled && now - task.lastRun >= task.interval) {
                task.lastRun = now;
                task.startedAt = now;
                task.status = 'running';
                
                // 添加到任务队列
                this.taskQueue.push({ ...task });
                
                await this.database.addLog(`定时任务启动: ${task.name}`, 'info', 'dispatcher');
            }
        }
    }
    
    // ==================== 工作负载均衡 ====================
    
    async balanceWorkload() {
        const avgWorkload = this.employees.reduce((sum, e) => sum + e.workload, 0) / this.employees.length;
        
        // 如果某个员工工作负载过高，尝试分配其他员工
        for (const employee of this.employees) {
            if (employee.workload > this.workloadThreshold) {
                // 找到空闲员工
                const freeEmployee = this.employees.find(e => 
                    e.status === 'active' && e.workload < avgWorkload && e.id !== employee.id
                );
                
                if (freeEmployee) {
                    await this.database.addLog(`工作负载均衡: ${employee.name} -> ${freeEmployee.name}`, 'info', 'dispatcher');
                }
            }
        }
    }
    
    // ==================== 员工管理 ====================
    
    async updateEmployeeTask(employee, task) {
        employee.lastTask = task.id;
        employee.workload = Math.min(100, employee.workload + 10);
        employee.taskCount++;
        employee.updatedAt = Date.now();

        // 捕获数据库错误，避免未处理的Promise拒绝
        try {
            await this.database.saveAIEmployee(employee);
        } catch (e) {
            console.warn('⚠️ updateEmployeeTask 保存失败:', e.message);
        }
    }
    
    async updateEmployeeCompletion(employee) {
        employee.workload = Math.max(0, employee.workload - 10);
        employee.completedTasks++;
        employee.updatedAt = Date.now();
        
        await this.database.saveAIEmployee(employee);
    }
    
    async getEmployeeStatus(employeeId) {
        return this.employees.find(e => e.id === employeeId);
    }
    
    async updateEmployeeStatus(employeeId, status) {
        const employee = this.employees.find(e => e.id === employeeId);
        if (employee) {
            employee.status = status;
            employee.updatedAt = Date.now();
            await this.database.saveAIEmployee(employee);
        }
    }
    
    // ==================== 添加任务 ====================
    
    addTask(task) {
        const newTask = {
            id: task.id || `task_${Date.now()}`,
            name: task.name,
            type: task.type || 'generic',
            ability: task.ability,
            priority: task.priority || 'normal',
            data: task.data || {},
            status: 'pending',
            createdAt: Date.now(),
            startedAt: null,
            completedAt: null,
            error: null
        };
        
        this.taskQueue.push(newTask);
        
        // 触发任务添加事件
        document.dispatchEvent(new CustomEvent('mtscos:task:added', {
            detail: newTask
        }));
        
        return newTask;
    }
    
    // ==================== 获取状态 ====================
    
    getStatus() {
        return {
            isRunning: this.isRunning,
            employees: this.employees.map(e => ({
                id: e.id,
                name: e.name,
                status: e.status,
                workload: e.workload,
                efficiency: e.efficiency,
                taskCount: e.taskCount,
                completedTasks: e.completedTasks
            })),
            pendingTasks: this.taskQueue.length,
            scheduledTasks: this.tasks.size,
            lastScheduledAt: Date.now()
        };
    }
    
    // ==================== 健康检查 ====================
    
    async healthCheck() {
        return {
            status: this.isRunning ? 'ok' : 'stopped',
            employees: this.employees.length,
            activeEmployees: this.employees.filter(e => e.status === 'active').length,
            pendingTasks: this.taskQueue.length,
            scheduledTasks: this.tasks.size
        };
    }
    
    // ==================== 销毁 ====================
    
    destroy() {
        this.stopScheduling();
        this.tasks.clear();
        this.taskQueue = [];
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIDispatcher;
}
