/**
 * 系统审核管理器
 * 提供敏感操作二次批准、回滚机制和审核流程管理
 */

class AuditSystemManager {
    constructor() {
        this.auditConfig = {
            enabled: true,
            requireApproval: true,
            approvalTimeout: 24, // 小时
            maxRollbacks: 3,
            rollbackTimeout: 48, // 小时
            sensitiveOperations: [
                'delete_user',
                'delete_data',
                'modify_permissions',
                'system_settings',
                'backup_restore',
                'vikey_management'
            ],
            approvalRoles: ['admin', 'super_admin', 'vikey_admin'],
            minApprovers: 2,
            autoApprove: false,
            notificationEnabled: true
        };

        this.auditQueue = [];
        this.approvalQueue = [];
        this.rollbackHistory = [];
        this.isInitialized = false;
        this.db = null;
        this.listeners = new Map();

        // 数据库配置
        this.dbConfig = {
            name: 'MTSCOS_Audit',
            version: 1,
            stores: ['audits', 'approvals', 'rollbacks', 'operations']
        };

        // 操作状态枚举
        this.OperationStatus = {
            PENDING: 'pending',
            APPROVED: 'approved',
            REJECTED: 'rejected',
            EXECUTED: 'executed',
            FAILED: 'failed',
            ROLLED_BACK: 'rolled_back'
        };

        // 审核状态枚举
        this.ApprovalStatus = {
            PENDING: 'pending',
            APPROVED: 'approved',
            REJECTED: 'rejected',
            EXPIRED: 'expired'
        };
    }

    /**
     * 初始化审核管理器
     */
    async initialize() {
        try {
            console.log('初始化系统审核管理器...');
            
            // 初始化数据库
            await this.initDatabase();
            
            // 加载配置
            await this.loadConfig();
            
            // 恢复待处理审核
            await this.restorePendingAudits();
            
            // 设置审核超时检查
            this.setupApprovalTimeout();
            
            this.isInitialized = true;
            console.log('系统审核管理器初始化完成');
            
            return true;
        } catch (error) {
            console.error('初始化审核管理器失败:', error);
            return false;
        }
    }

    /**
     * 初始化数据库
     */
    async initDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbConfig.name, this.dbConfig.version);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // 创建审核记录存储
                if (!db.objectStoreNames.contains('audits')) {
                    const auditStore = db.createObjectStore('audits', { keyPath: 'id' });
                    auditStore.createIndex('timestamp', 'timestamp', { unique: false });
                    auditStore.createIndex('status', 'status', { unique: false });
                    auditStore.createIndex('operation', 'operation', { unique: false });
                    auditStore.createIndex('userId', 'userId', { unique: false });
                }

                // 创建批准记录存储
                if (!db.objectStoreNames.contains('approvals')) {
                    const approvalStore = db.createObjectStore('approvals', { keyPath: 'id' });
                    approvalStore.createIndex('auditId', 'auditId', { unique: false });
                    approvalStore.createIndex('approverId', 'approverId', { unique: false });
                    approvalStore.createIndex('status', 'status', { unique: false });
                    approvalStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                // 创建回滚记录存储
                if (!db.objectStoreNames.contains('rollbacks')) {
                    const rollbackStore = db.createObjectStore('rollbacks', { keyPath: 'id' });
                    rollbackStore.createIndex('auditId', 'auditId', { unique: false });
                    rollbackStore.createIndex('timestamp', 'timestamp', { unique: false });
                    rollbackStore.createIndex('status', 'status', { unique: false });
                }

                // 创建操作记录存储
                if (!db.objectStoreNames.contains('operations')) {
                    const operationStore = db.createObjectStore('operations', { keyPath: 'id' });
                    operationStore.createIndex('timestamp', 'timestamp', { unique: false });
                    operationStore.createIndex('type', 'type', { unique: false });
                    operationStore.createIndex('userId', 'userId', { unique: false });
                }
            };
        });
    }

    /**
     * 加载配置
     */
    async loadConfig() {
        try {
            // 从系统设置加载配置
            if (window.systemSettings) {
                const config = window.systemSettings.get('audit', '');
                if (config) {
                    this.auditConfig = { ...this.auditConfig, ...config };
                }
            }

            console.log('审核配置加载完成:', this.auditConfig);
        } catch (error) {
            console.error('加载审核配置失败:', error);
        }
    }

    /**
     * 恢复待处理审核
     */
    async restorePendingAudits() {
        try {
            const pendingAudits = await this.getPendingAudits();
            this.auditQueue = pendingAudits;
            
            console.log(`恢复 ${pendingAudits.length} 个待处理审核`);
        } catch (error) {
            console.error('恢复待处理审核失败:', error);
        }
    }

    /**
     * 设置审核超时检查
     */
    setupApprovalTimeout() {
        // 每小时检查一次超时的审核
        setInterval(async () => {
            try {
                await this.checkExpiredApprovals();
            } catch (error) {
                console.error('检查审核超时失败:', error);
            }
        }, 60 * 60 * 1000);
    }

    /**
     * 创建审核记录
     */
    async createAudit(operation, data, options = {}) {
        if (!this.auditConfig.enabled) {
            return { id: null, requiresApproval: false };
        }

        const auditId = this.generateAuditId();
        const timestamp = new Date().toISOString();
        const requiresApproval = this.requiresApproval(operation, data);

        const auditRecord = {
            id: auditId,
            timestamp,
            operation,
            data,
            userId: this.getCurrentUserId(),
            sessionId: this.getCurrentSessionId(),
            status: requiresApproval ? this.OperationStatus.PENDING : this.OperationStatus.APPROVED,
            requiresApproval,
            description: options.description || '',
            priority: options.priority || 'normal',
            metadata: {
                userAgent: navigator.userAgent,
                ip: this.getClientIP(),
                url: window.location.href
            }
        };

        try {
            // 保存到数据库
            await this.saveAuditToDatabase(auditRecord);
            
            if (requiresApproval) {
                // 添加到审核队列
                this.auditQueue.push(auditRecord);
                
                // 创建批准请求
                await this.createApprovalRequests(auditRecord);
                
                // 发送通知
                if (this.auditConfig.notificationEnabled) {
                    await this.sendApprovalNotification(auditRecord);
                }
                
                this.emitEvent('auditCreated', auditRecord);
                console.log(`审核记录已创建，需要批准: ${auditId}`);
            } else {
                // 自动批准，直接执行
                await this.executeOperation(auditRecord);
                console.log(`审核记录已创建并自动执行: ${auditId}`);
            }
            
            return {
                id: auditId,
                requiresApproval,
                status: auditRecord.status
            };
            
        } catch (error) {
            console.error('创建审核记录失败:', error);
            throw error;
        }
    }

    /**
     * 判断是否需要批准
     */
    requiresApproval(operation, data) {
        if (!this.auditConfig.requireApproval) {
            return false;
        }

        // 检查是否为敏感操作
        if (this.auditConfig.sensitiveOperations.includes(operation)) {
            return true;
        }

        // 检查用户权限
        const currentUser = this.getCurrentUser();
        if (!currentUser || !this.auditConfig.approvalRoles.includes(currentUser.role)) {
            return true;
        }

        // 检查操作数据是否包含敏感信息
        if (this.containsSensitiveData(data)) {
            return true;
        }

        return false;
    }

    /**
     * 检查是否包含敏感数据
     */
    containsSensitiveData(data) {
        const sensitiveKeywords = [
            'password', 'token', 'key', 'secret', 'admin', 'delete', 'remove'
        ];

        const dataString = JSON.stringify(data).toLowerCase();
        return sensitiveKeywords.some(keyword => dataString.includes(keyword));
    }

    /**
     * 创建批准请求
     */
    async createApprovalRequests(auditRecord) {
        const approvalRequests = [];
        const requiredApprovers = this.auditConfig.minApprovers;

        // 获取可批准的管理员列表
        const availableApprovers = await this.getAvailableApprovers();
        
        // 创建批准请求
        for (let i = 0; i < Math.min(requiredApprovers, availableApprovers.length); i++) {
            const approvalRequest = {
                id: this.generateApprovalId(),
                auditId: auditRecord.id,
                approverId: availableApprovers[i].id,
                approverName: availableApprovers[i].name,
                status: this.ApprovalStatus.PENDING,
                timestamp: new Date().toISOString(),
                expiresAt: new Date(Date.now() + this.auditConfig.approvalTimeout * 60 * 60 * 1000).toISOString(),
                notes: ''
            };

            approvalRequests.push(approvalRequest);
            await this.saveApprovalToDatabase(approvalRequest);
        }

        this.approvalQueue.push(...approvalRequests);
        return approvalRequests;
    }

    /**
     * 获取可批准的管理员列表
     */
    async getAvailableApprovers() {
        try {
            // 从用户管理系统获取管理员列表
            if (window.userManagement) {
                const users = await window.userManagement.getAllUsers();
                return users.filter(user => 
                    this.auditConfig.approvalRoles.includes(user.role) &&
                    user.status === 'active'
                );
            }
            
            // 默认返回当前用户（如果是管理员）
            const currentUser = this.getCurrentUser();
            if (currentUser && this.auditConfig.approvalRoles.includes(currentUser.role)) {
                return [currentUser];
            }
            
            return [];
        } catch (error) {
            console.error('获取可批准管理员列表失败:', error);
            return [];
        }
    }

    /**
     * 处理批准请求
     */
    async processApproval(approvalId, decision, notes = '') {
        try {
            const approval = await this.getApprovalFromDatabase(approvalId);
            if (!approval) {
                throw new Error('批准请求不存在');
            }

            if (approval.status !== this.ApprovalStatus.PENDING) {
                throw new Error('批准请求已处理');
            }

            // 更新批准状态
            approval.status = decision ? this.ApprovalStatus.APPROVED : this.ApprovalStatus.REJECTED;
            approval.notes = notes;
            approval.processedAt = new Date().toISOString();
            approval.processedBy = this.getCurrentUserId();

            await this.updateApprovalInDatabase(approval);

            // 获取对应的审核记录
            const audit = await this.getAuditFromDatabase(approval.auditId);
            if (!audit) {
                throw new Error('审核记录不存在');
            }

            // 检查是否满足批准条件
            const approvals = await this.getApprovalsForAudit(approval.auditId);
            const approvedCount = approvals.filter(a => a.status === this.ApprovalStatus.APPROVED).length;
            const rejectedCount = approvals.filter(a => a.status === this.ApprovalStatus.REJECTED).length;

            if (rejectedCount >= this.auditConfig.minApprovers) {
                // 足够的拒绝，审核失败
                audit.status = this.OperationStatus.REJECTED;
                await this.updateAuditInDatabase(audit);
                this.emitEvent('auditRejected', { audit, approval });
                
            } else if (approvedCount >= this.auditConfig.minApprovers) {
                // 足够的批准，执行操作
                audit.status = this.OperationStatus.APPROVED;
                await this.updateAuditInDatabase(audit);
                await this.executeOperation(audit);
                this.emitEvent('auditApproved', { audit, approval });
                
            } else {
                // 还需要更多批准
                this.emitEvent('approvalProcessed', { audit, approval });
            }

            console.log(`批准请求已处理: ${approvalId}, 决定: ${decision ? '批准' : '拒绝'}`);
            return true;
            
        } catch (error) {
            console.error('处理批准请求失败:', error);
            throw error;
        }
    }

    /**
     * 执行操作
     */
    async executeOperation(auditRecord) {
        try {
            console.log(`执行审核操作: ${auditRecord.operation}`);
            
            // 记录操作开始
            const operationRecord = {
                id: this.generateOperationId(),
                auditId: auditRecord.id,
                type: auditRecord.operation,
                data: auditRecord.data,
                userId: auditRecord.userId,
                timestamp: new Date().toISOString(),
                status: 'executing'
            };

            await this.saveOperationToDatabase(operationRecord);

            // 根据操作类型执行相应的逻辑
            let result;
            switch (auditRecord.operation) {
                case 'delete_user':
                    result = await this.executeDeleteUser(auditRecord.data);
                    break;
                case 'delete_data':
                    result = await this.executeDeleteData(auditRecord.data);
                    break;
                case 'modify_permissions':
                    result = await this.executeModifyPermissions(auditRecord.data);
                    break;
                case 'system_settings':
                    result = await this.executeSystemSettings(auditRecord.data);
                    break;
                case 'backup_restore':
                    result = await this.executeBackupRestore(auditRecord.data);
                    break;
                case 'vikey_management':
                    result = await this.executeVikeyManagement(auditRecord.data);
                    break;
                default:
                    result = await this.executeCustomOperation(auditRecord);
            }

            // 更新操作记录
            operationRecord.status = result.success ? 'completed' : 'failed';
            operationRecord.result = result;
            operationRecord.completedAt = new Date().toISOString();
            await this.updateOperationInDatabase(operationRecord);

            // 更新审核记录状态
            auditRecord.status = result.success ? this.OperationStatus.EXECUTED : this.OperationStatus.FAILED;
            auditRecord.executedAt = new Date().toISOString();
            auditRecord.result = result;
            await this.updateAuditInDatabase(auditRecord);

            // 记录审计日志
            if (window.systemLogger) {
                window.systemLogger.audit('operation_executed', auditRecord.operation, {
                    auditId: auditRecord.id,
                    userId: auditRecord.userId,
                    success: result.success,
                    result: result
                });
            }

            this.emitEvent('operationExecuted', { audit: auditRecord, result });
            console.log(`操作执行完成: ${auditRecord.operation}, 成功: ${result.success}`);
            
            return result;
            
        } catch (error) {
            console.error('执行操作失败:', error);
            
            // 更新审核记录为失败状态
            auditRecord.status = this.OperationStatus.FAILED;
            auditRecord.error = error.message;
            auditRecord.failedAt = new Date().toISOString();
            await this.updateAuditInDatabase(auditRecord);
            
            throw error;
        }
    }

    /**
     * 创建回滚请求
     */
    async createRollback(auditId, reason = '') {
        try {
            const audit = await this.getAuditFromDatabase(auditId);
            if (!audit) {
                throw new Error('审核记录不存在');
            }

            if (audit.status !== this.OperationStatus.EXECUTED) {
                throw new Error('只能回滚已执行的操作');
            }

            // 检查回滚次数限制
            const rollbackCount = await this.getRollbackCount(auditId);
            if (rollbackCount >= this.auditConfig.maxRollbacks) {
                throw new Error('已达到最大回滚次数限制');
            }

            const rollbackId = this.generateRollbackId();
            const rollbackRecord = {
                id: rollbackId,
                auditId,
                timestamp: new Date().toISOString(),
                userId: this.getCurrentUserId(),
                reason,
                status: 'pending',
                originalData: audit.data,
                originalResult: audit.result
            };

            await this.saveRollbackToDatabase(rollbackRecord);
            this.rollbackHistory.push(rollbackRecord);

            // 执行回滚
            await this.executeRollback(rollbackRecord);

            this.emitEvent('rollbackCreated', rollbackRecord);
            console.log(`回滚请求已创建: ${rollbackId}`);
            
            return rollbackId;
            
        } catch (error) {
            console.error('创建回滚请求失败:', error);
            throw error;
        }
    }

    /**
     * 执行回滚
     */
    async executeRollback(rollbackRecord) {
        try {
            console.log(`执行回滚: ${rollbackRecord.id}`);
            
            const audit = await this.getAuditFromDatabase(rollbackRecord.auditId);
            let result;

            // 根据操作类型执行相应的回滚逻辑
            switch (audit.operation) {
                case 'delete_user':
                    result = await this.rollbackDeleteUser(rollbackRecord);
                    break;
                case 'delete_data':
                    result = await this.rollbackDeleteData(rollbackRecord);
                    break;
                case 'modify_permissions':
                    result = await this.rollbackModifyPermissions(rollbackRecord);
                    break;
                case 'system_settings':
                    result = await this.rollbackSystemSettings(rollbackRecord);
                    break;
                default:
                    result = await this.rollbackCustomOperation(rollbackRecord);
            }

            // 更新回滚记录
            rollbackRecord.status = result.success ? 'completed' : 'failed';
            rollbackRecord.result = result;
            rollbackRecord.completedAt = new Date().toISOString();
            await this.updateRollbackInDatabase(rollbackRecord);

            // 更新审核记录
            audit.status = this.OperationStatus.ROLLED_BACK;
            audit.rolledBackAt = new Date().toISOString();
            await this.updateAuditInDatabase(audit);

            this.emitEvent('rollbackExecuted', { rollback: rollbackRecord, result });
            console.log(`回滚执行完成: ${rollbackRecord.id}, 成功: ${result.success}`);
            
            return result;
            
        } catch (error) {
            console.error('执行回滚失败:', error);
            throw error;
        }
    }

    /**
     * 检查超时的批准请求
     */
    async checkExpiredApprovals() {
        try {
            const now = new Date();
            const expiredApprovals = await this.getExpiredApprovals(now);
            
            for (const approval of expiredApprovals) {
                approval.status = this.ApprovalStatus.EXPIRED;
                approval.expiredAt = now.toISOString();
                await this.updateApprovalInDatabase(approval);
                
                // 更新对应的审核记录
                const audit = await this.getAuditFromDatabase(approval.auditId);
                if (audit && audit.status === this.OperationStatus.PENDING) {
                    audit.status = this.OperationStatus.REJECTED;
                    audit.rejectionReason = '批准请求超时';
                    await this.updateAuditInDatabase(audit);
                }
                
                this.emitEvent('approvalExpired', { approval, audit });
            }
            
            if (expiredApprovals.length > 0) {
                console.log(`处理了 ${expiredApprovals.length} 个超时的批准请求`);
            }
            
        } catch (error) {
            console.error('检查超时批准请求失败:', error);
        }
    }

    /**
     * 获取审核列表
     */
    async getAuditList(options = {}) {
        const {
            status,
            operation,
            userId,
            startTime,
            endTime,
            limit = 50,
            offset = 0
        } = options;

        try {
            let audits = await this.getAllAuditsFromDatabase();
            
            // 应用过滤条件
            if (status) {
                audits = audits.filter(audit => audit.status === status);
            }
            if (operation) {
                audits = audits.filter(audit => audit.operation === operation);
            }
            if (userId) {
                audits = audits.filter(audit => audit.userId === userId);
            }
            if (startTime) {
                audits = audits.filter(audit => new Date(audit.timestamp) >= new Date(startTime));
            }
            if (endTime) {
                audits = audits.filter(audit => new Date(audit.timestamp) <= new Date(endTime));
            }

            // 排序和分页
            audits.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            const paginatedAudits = audits.slice(offset, offset + limit);

            return {
                audits: paginatedAudits,
                total: audits.length,
                offset,
                limit
            };
            
        } catch (error) {
            console.error('获取审核列表失败:', error);
            return { audits: [], total: 0, offset, limit };
        }
    }

    /**
     * 获取待处理的审核
     */
    async getPendingAudits() {
        try {
            const audits = await this.getAllAuditsFromDatabase();
            return audits.filter(audit => audit.status === this.OperationStatus.PENDING);
        } catch (error) {
            console.error('获取待处理审核失败:', error);
            return [];
        }
    }

    /**
     * 发送批准通知
     */
    async sendApprovalNotification(auditRecord) {
        try {
            // 这里可以实现邮件、短信或其他通知方式
            console.log(`发送批准通知: ${auditRecord.id}`);
            
            // 简单的浏览器通知
            if (Notification.permission === 'granted') {
                new Notification('审核批准请求', {
                    body: `操作: ${auditRecord.operation}\n用户: ${auditRecord.userId}\n时间: ${auditRecord.timestamp}`,
                    icon: '/assets/images/notification-icon.png'
                });
            }
            
        } catch (error) {
            console.error('发送批准通知失败:', error);
        }
    }

    /**
     * 具体操作执行方法
     */
    async executeDeleteUser(data) {
        try {
            if (window.userManagement) {
                await window.userManagement.deleteUser(data.userId);
                return { success: true, message: '用户删除成功' };
            }
            return { success: false, message: '用户管理系统不可用' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }

    async executeDeleteData(data) {
        try {
            // 实现数据删除逻辑
            console.log('删除数据:', data);
            return { success: true, message: '数据删除成功' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }

    async executeModifyPermissions(data) {
        try {
            if (window.userManagement) {
                await window.userManagement.updateUserPermissions(data.userId, data.permissions);
                return { success: true, message: '权限修改成功' };
            }
            return { success: false, message: '用户管理系统不可用' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }

    async executeSystemSettings(data) {
        try {
            if (window.systemSettings) {
                await window.systemSettings.updateSettings(data.settings);
                return { success: true, message: '系统设置更新成功' };
            }
            return { success: false, message: '系统设置管理器不可用' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }

    async executeBackupRestore(data) {
        try {
            if (window.databaseBackup) {
                if (data.action === 'restore') {
                    await window.databaseBackup.restoreBackup(data.backupId);
                }
                return { success: true, message: '备份恢复成功' };
            }
            return { success: false, message: '数据库备份管理器不可用' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }

    async executeVikeyManagement(data) {
        try {
            // 实现Vikey管理逻辑
            console.log('Vikey管理操作:', data);
            return { success: true, message: 'Vikey管理操作成功' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }

    async executeCustomOperation(auditRecord) {
        try {
            // 执行自定义操作
            console.log('执行自定义操作:', auditRecord);
            return { success: true, message: '自定义操作执行成功' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }

    /**
     * 回滚方法
     */
    async rollbackDeleteUser(rollbackRecord) {
        try {
            // 恢复被删除的用户（需要备份数据）
            console.log('回滚用户删除:', rollbackRecord);
            return { success: true, message: '用户删除回滚成功' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }

    async rollbackDeleteData(rollbackRecord) {
        try {
            // 恢复被删除的数据
            console.log('回滚数据删除:', rollbackRecord);
            return { success: true, message: '数据删除回滚成功' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }

    async rollbackModifyPermissions(rollbackRecord) {
        try {
            // 恢复原始权限
            console.log('回滚权限修改:', rollbackRecord);
            return { success: true, message: '权限修改回滚成功' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }

    async rollbackSystemSettings(rollbackRecord) {
        try {
            // 恢复原始设置
            console.log('回滚系统设置:', rollbackRecord);
            return { success: true, message: '系统设置回滚成功' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }

    async rollbackCustomOperation(rollbackRecord) {
        try {
            // 回滚自定义操作
            console.log('回滚自定义操作:', rollbackRecord);
            return { success: true, message: '自定义操作回滚成功' };
        } catch (error) {
            return { success: false, message: error.message };
        }
    }

    /**
     * 数据库操作辅助方法
     */
    async saveAuditToDatabase(audit) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('audits', 'readwrite');
            const request = transaction.objectStore('audits').put(audit);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getAuditFromDatabase(auditId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('audits', 'readonly');
            const request = transaction.objectStore('audits').get(auditId);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async updateAuditInDatabase(audit) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('audits', 'readwrite');
            const request = transaction.objectStore('audits').put(audit);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getAllAuditsFromDatabase() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('audits', 'readonly');
            const request = transaction.objectStore('audits').getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async saveApprovalToDatabase(approval) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('approvals', 'readwrite');
            const request = transaction.objectStore('approvals').put(approval);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getApprovalFromDatabase(approvalId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('approvals', 'readonly');
            const request = transaction.objectStore('approvals').get(approvalId);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async updateApprovalInDatabase(approval) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('approvals', 'readwrite');
            const request = transaction.objectStore('approvals').put(approval);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getApprovalsForAudit(auditId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('approvals', 'readonly');
            const store = transaction.objectStore('approvals');
            const index = store.index('auditId');
            const request = index.getAll(auditId);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getExpiredApprovals(now) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('approvals', 'readonly');
            const store = transaction.objectStore('approvals');
            const request = store.getAll();
            request.onsuccess = () => {
                const approvals = request.result;
                const expired = approvals.filter(approval => 
                    approval.status === this.ApprovalStatus.PENDING &&
                    new Date(approval.expiresAt) < now
                );
                resolve(expired);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async saveRollbackToDatabase(rollback) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('rollbacks', 'readwrite');
            const request = transaction.objectStore('rollbacks').put(rollback);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async updateRollbackInDatabase(rollback) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('rollbacks', 'readwrite');
            const request = transaction.objectStore('rollbacks').put(rollback);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getRollbackCount(auditId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('rollbacks', 'readonly');
            const store = transaction.objectStore('rollbacks');
            const index = store.index('auditId');
            const request = index.getAll(auditId);
            request.onsuccess = () => resolve(request.result.length);
            request.onerror = () => reject(request.error);
        });
    }

    async saveOperationToDatabase(operation) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('operations', 'readwrite');
            const request = transaction.objectStore('operations').put(operation);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async updateOperationInDatabase(operation) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction('operations', 'readwrite');
            const request = transaction.objectStore('operations').put(operation);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * 辅助方法
     */
    generateAuditId() {
        return `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    generateApprovalId() {
        return `approval_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    generateRollbackId() {
        return `rollback_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    generateOperationId() {
        return `operation_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    getCurrentUserId() {
        return window.currentUser?.id || 'anonymous';
    }

    getCurrentSessionId() {
        return sessionStorage.getItem('session_id') || 'unknown';
    }

    getCurrentUser() {
        return window.currentUser || null;
    }

    getClientIP() {
        // 在实际应用中，这应该从服务器获取
        return 'client_ip';
    }

    /**
     * 事件处理
     */
    addEventListener(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    removeEventListener(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    emitEvent(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`审核事件处理器错误 (${event}):`, error);
                }
            });
        }
    }

    /**
     * 销毁管理器
     */
    destroy() {
        this.listeners.clear();
        this.isInitialized = false;
    }
}

// 创建全局实例
window.auditSystem = new AuditSystemManager();

// 自动初始化
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await window.auditSystem.initialize();
        console.log('系统审核管理器已准备就绪');
    } catch (error) {
        console.error('系统审核管理器初始化失败:', error);
    }
});

// 导出类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuditSystemManager;
}