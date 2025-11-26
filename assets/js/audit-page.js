/**
 * 审核管理页面脚本
 */

class AuditManagementPage {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 20;
        this.currentTab = 'pending';
        this.filters = {
            operation: '',
            priority: '',
            user: '',
            status: '',
            startTime: '',
            endTime: '',
            rollbackStatus: ''
        };
        
        this.init();
    }

    /**
     * 初始化页面
     */
    async init() {
        try {
            console.log('初始化审核管理页面...');
            
            // 等待审核系统初始化
            await this.waitForAuditSystem();
            
            // 绑定事件监听器
            this.bindEventListeners();
            
            // 加载统计数据
            await this.loadStatistics();
            
            // 加载当前标签页内容
            await this.loadCurrentTab();
            
            // 设置自动刷新
            this.setupAutoRefresh();
            
            console.log('审核管理页面初始化完成');
            
        } catch (error) {
            console.error('审核管理页面初始化失败:', error);
            this.showError('页面初始化失败: ' + error.message);
        }
    }

    /**
     * 等待审核系统初始化
     */
    async waitForAuditSystem() {
        const maxWaitTime = 10000; // 10秒
        const startTime = Date.now();
        
        while (!window.auditSystem || !window.auditSystem.isInitialized) {
            if (Date.now() - startTime > maxWaitTime) {
                throw new Error('审核系统初始化超时');
            }
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }

    /**
     * 绑定事件监听器
     */
    bindEventListeners() {
        // 标签页切换
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // 筛选器事件
        document.getElementById('filterOperation')?.addEventListener('change', (e) => {
            this.filters.operation = e.target.value;
            this.loadCurrentTab();
        });

        document.getElementById('filterPriority')?.addEventListener('change', (e) => {
            this.filters.priority = e.target.value;
            this.loadCurrentTab();
        });

        document.getElementById('filterUser')?.addEventListener('input', (e) => {
            this.filters.user = e.target.value;
            this.debounceLoad();
        });

        document.getElementById('filterStatus')?.addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.loadCurrentTab();
        });

        document.getElementById('filterStartTime')?.addEventListener('change', (e) => {
            this.filters.startTime = e.target.value;
            this.loadCurrentTab();
        });

        document.getElementById('filterEndTime')?.addEventListener('change', (e) => {
            this.filters.endTime = e.target.value;
            this.loadCurrentTab();
        });

        document.getElementById('filterRollbackStatus')?.addEventListener('change', (e) => {
            this.filters.rollbackStatus = e.target.value;
            this.loadCurrentTab();
        });

        // 设置表单提交
        document.getElementById('auditSettingsForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveAuditSettings();
        });

        // 审核系统事件监听
        if (window.auditSystem) {
            window.auditSystem.addEventListener('auditCreated', () => {
                this.loadStatistics();
                if (this.currentTab === 'pending') {
                    this.loadPendingAudits();
                }
            });

            window.auditSystem.addEventListener('auditApproved', () => {
                this.loadStatistics();
                this.loadCurrentTab();
            });

            window.auditSystem.addEventListener('auditRejected', () => {
                this.loadStatistics();
                this.loadCurrentTab();
            });

            window.auditSystem.addEventListener('rollbackCreated', () => {
                this.loadStatistics();
                if (this.currentTab === 'rollbacks') {
                    this.loadRollbacks();
                }
            });
        }
    }

    /**
     * 切换标签页
     */
    switchTab(tabName) {
        // 更新标签按钮状态
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // 更新内容面板
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        this.currentTab = tabName;
        this.currentPage = 1;
        this.loadCurrentTab();
    }

    /**
     * 加载当前标签页内容
     */
    async loadCurrentTab() {
        try {
            switch (this.currentTab) {
                case 'pending':
                    await this.loadPendingAudits();
                    break;
                case 'history':
                    await this.loadAuditHistory();
                    break;
                case 'approvals':
                    await this.loadApprovals();
                    break;
                case 'rollbacks':
                    await this.loadRollbacks();
                    break;
                case 'settings':
                    await this.loadSettings();
                    break;
            }
        } catch (error) {
            console.error('加载标签页内容失败:', error);
            this.showError('加载内容失败: ' + error.message);
        }
    }

    /**
     * 加载统计数据
     */
    async loadStatistics() {
        try {
            const stats = await this.getAuditStatistics();
            
            document.getElementById('pendingCount').textContent = stats.pendingCount || 0;
            document.getElementById('todayCount').textContent = stats.todayCount || 0;
            document.getElementById('approvalRate').textContent = stats.approvalRate || '0%';
            document.getElementById('rollbackCount').textContent = stats.rollbackCount || 0;
            
        } catch (error) {
            console.error('加载统计数据失败:', error);
        }
    }

    /**
     * 获取审核统计信息
     */
    async getAuditStatistics() {
        try {
            const pendingAudits = await window.auditSystem.getPendingAudits();
            const allAudits = await window.auditSystem.getAuditList({ limit: 1000 });
            
            const today = new Date().toDateString();
            const todayAudits = allAudits.audits.filter(audit => 
                new Date(audit.timestamp).toDateString() === today
            );
            
            const approvedCount = allAudits.audits.filter(audit => 
                audit.status === 'approved' || audit.status === 'executed'
            ).length;
            
            const approvalRate = allAudits.audits.length > 0 
                ? Math.round((approvedCount / allAudits.audits.length) * 100) + '%'
                : '0%';

            // 获取本月回滚次数
            const thisMonth = new Date().getMonth();
            const thisYear = new Date().getFullYear();
            const rollbackCount = await this.getRollbackCount(thisMonth, thisYear);

            return {
                pendingCount: pendingAudits.length,
                todayCount: todayAudits.length,
                approvalRate,
                rollbackCount
            };
            
        } catch (error) {
            console.error('获取统计信息失败:', error);
            return {
                pendingCount: 0,
                todayCount: 0,
                approvalRate: '0%',
                rollbackCount: 0
            };
        }
    }

    /**
     * 加载待处理审核
     */
    async loadPendingAudits() {
        const container = document.getElementById('pendingAuditsList');
        
        try {
            this.showLoading(container);
            
            const audits = await window.auditSystem.getPendingAudits();
            
            // 应用筛选器
            const filteredAudits = this.applyFilters(audits);
            
            if (filteredAudits.length === 0) {
                this.showEmptyState(container, '没有待处理的审核');
                return;
            }

            const html = this.renderPendingAuditsTable(filteredAudits);
            container.innerHTML = html;
            
        } catch (error) {
            console.error('加载待处理审核失败:', error);
            this.showError(container, '加载失败: ' + error.message);
        }
    }

    /**
     * 加载审核历史
     */
    async loadAuditHistory() {
        const container = document.getElementById('auditHistoryList');
        
        try {
            this.showLoading(container);
            
            const options = {
                limit: this.pageSize,
                offset: (this.currentPage - 1) * this.pageSize,
                status: this.filters.status || undefined,
                startTime: this.filters.startTime || undefined,
                endTime: this.filters.endTime || undefined
            };

            const result = await window.auditSystem.getAuditList(options);
            
            if (result.audits.length === 0) {
                this.showEmptyState(container, '没有审核历史记录');
                return;
            }

            const html = this.renderAuditHistoryTable(result.audits);
            container.innerHTML = html;
            
            // 添加分页
            this.renderPagination(container, result.total);
            
        } catch (error) {
            console.error('加载审核历史失败:', error);
            this.showError(container, '加载失败: ' + error.message);
        }
    }

    /**
     * 加载批准管理
     */
    async loadApprovals() {
        const container = document.getElementById('approvalsList');
        
        try {
            this.showLoading(container);
            
            const approvals = await this.getAllApprovals();
            
            if (approvals.length === 0) {
                this.showEmptyState(container, '没有批准记录');
                return;
            }

            const html = this.renderApprovalsTable(approvals);
            container.innerHTML = html;
            
        } catch (error) {
            console.error('加载批准管理失败:', error);
            this.showError(container, '加载失败: ' + error.message);
        }
    }

    /**
     * 加载回滚管理
     */
    async loadRollbacks() {
        const container = document.getElementById('rollbacksList');
        
        try {
            this.showLoading(container);
            
            const rollbacks = await this.getAllRollbacks();
            
            // 应用筛选器
            const filteredRollbacks = this.applyRollbackFilters(rollbacks);
            
            if (filteredRollbacks.length === 0) {
                this.showEmptyState(container, '没有回滚记录');
                return;
            }

            const html = this.renderRollbacksTable(filteredRollbacks);
            container.innerHTML = html;
            
        } catch (error) {
            console.error('加载回滚管理失败:', error);
            this.showError(container, '加载失败: ' + error.message);
        }
    }

    /**
     * 加载设置
     */
    async loadSettings() {
        try {
            const config = window.auditSystem.auditConfig;
            
            document.getElementById('auditEnabled').checked = config.enabled;
            document.getElementById('requireApproval').checked = config.requireApproval;
            document.getElementById('approvalTimeout').value = config.approvalTimeout;
            document.getElementById('minApprovers').value = config.minApprovers;
            document.getElementById('maxRollbacks').value = config.maxRollbacks;
            document.getElementById('notificationEnabled').checked = config.notificationEnabled;
            
        } catch (error) {
            console.error('加载设置失败:', error);
            this.showError('加载设置失败: ' + error.message);
        }
    }

    /**
     * 应用筛选器
     */
    applyFilters(audits) {
        return audits.filter(audit => {
            if (this.filters.operation && audit.operation !== this.filters.operation) {
                return false;
            }
            if (this.filters.priority && audit.priority !== this.filters.priority) {
                return false;
            }
            if (this.filters.user && !audit.userId.includes(this.filters.user)) {
                return false;
            }
            return true;
        });
    }

    /**
     * 应用回滚筛选器
     */
    applyRollbackFilters(rollbacks) {
        return rollbacks.filter(rollback => {
            if (this.filters.rollbackStatus && rollback.status !== this.filters.rollbackStatus) {
                return false;
            }
            return true;
        });
    }

    /**
     * 渲染待处理审核表格
     */
    renderPendingAuditsTable(audits) {
        let html = `
            <table class="audit-table">
                <thead>
                    <tr>
                        <th>操作类型</th>
                        <th>提交用户</th>
                        <th>优先级</th>
                        <th>提交时间</th>
                        <th>描述</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
        `;

        audits.forEach(audit => {
            html += `
                <tr>
                    <td>${this.getOperationName(audit.operation)}</td>
                    <td>${audit.userId}</td>
                    <td><span class="priority-badge priority-${audit.priority}">${this.getPriorityName(audit.priority)}</span></td>
                    <td>${this.formatDateTime(audit.timestamp)}</td>
                    <td>${audit.description || '-'}</td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn btn-primary btn-sm" onclick="auditPage.showAuditDetails('${audit.id}')">详情</button>
                            <button class="btn btn-success btn-sm" onclick="auditPage.showApprovalModal('${audit.id}')">批准</button>
                            <button class="btn btn-danger btn-sm" onclick="auditPage.rejectAudit('${audit.id}')">拒绝</button>
                        </div>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        return html;
    }

    /**
     * 渲染审核历史表格
     */
    renderAuditHistoryTable(audits) {
        let html = `
            <table class="audit-table">
                <thead>
                    <tr>
                        <th>操作类型</th>
                        <th>提交用户</th>
                        <th>状态</th>
                        <th>提交时间</th>
                        <th>处理时间</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
        `;

        audits.forEach(audit => {
            html += `
                <tr>
                    <td>${this.getOperationName(audit.operation)}</td>
                    <td>${audit.userId}</td>
                    <td><span class="status-badge status-${audit.status}">${this.getStatusName(audit.status)}</span></td>
                    <td>${this.formatDateTime(audit.timestamp)}</td>
                    <td>${audit.executedAt ? this.formatDateTime(audit.executedAt) : '-'}</td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn btn-primary btn-sm" onclick="auditPage.showAuditDetails('${audit.id}')">详情</button>
                            ${audit.status === 'executed' ? `<button class="btn btn-warning btn-sm" onclick="auditPage.createRollback('${audit.id}')">回滚</button>` : ''}
                        </div>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        return html;
    }

    /**
     * 渲染批准表格
     */
    renderApprovalsTable(approvals) {
        let html = `
            <table class="audit-table">
                <thead>
                    <tr>
                        <th>审核ID</th>
                        <th>批准人</th>
                        <th>状态</th>
                        <th>请求时间</th>
                        <th>处理时间</th>
                        <th>备注</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
        `;

        approvals.forEach(approval => {
            html += `
                <tr>
                    <td>${approval.auditId}</td>
                    <td>${approval.approverName}</td>
                    <td><span class="status-badge status-${approval.status}">${this.getApprovalStatusName(approval.status)}</span></td>
                    <td>${this.formatDateTime(approval.timestamp)}</td>
                    <td>${approval.processedAt ? this.formatDateTime(approval.processedAt) : '-'}</td>
                    <td>${approval.notes || '-'}</td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn btn-primary btn-sm" onclick="auditPage.showApprovalDetails('${approval.id}')">详情</button>
                        </div>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        return html;
    }

    /**
     * 渲染回滚表格
     */
    renderRollbacksTable(rollbacks) {
        let html = `
            <table class="audit-table">
                <thead>
                    <tr>
                        <th>回滚ID</th>
                        <th>原审核ID</th>
                        <th>发起用户</th>
                        <th>状态</th>
                        <th>创建时间</th>
                        <th>完成时间</th>
                        <th>原因</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
        `;

        rollbacks.forEach(rollback => {
            html += `
                <tr>
                    <td>${rollback.id}</td>
                    <td>${rollback.auditId}</td>
                    <td>${rollback.userId}</td>
                    <td><span class="status-badge status-${rollback.status}">${this.getRollbackStatusName(rollback.status)}</span></td>
                    <td>${this.formatDateTime(rollback.timestamp)}</td>
                    <td>${rollback.completedAt ? this.formatDateTime(rollback.completedAt) : '-'}</td>
                    <td>${rollback.reason || '-'}</td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn btn-primary btn-sm" onclick="auditPage.showRollbackDetails('${rollback.id}')">详情</button>
                        </div>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        return html;
    }

    /**
     * 显示审核详情
     */
    async showAuditDetails(auditId) {
        try {
            const audit = await window.auditSystem.getAuditFromDatabase(auditId);
            if (!audit) {
                this.showError('审核记录不存在');
                return;
            }

            const modal = document.getElementById('auditModal');
            const modalBody = document.getElementById('auditModalBody');

            modalBody.innerHTML = `
                <div class="audit-details">
                    <div class="detail-row">
                        <span class="detail-label">审核ID:</span>
                        <span class="detail-value">${audit.id}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">操作类型:</span>
                        <span class="detail-value">${this.getOperationName(audit.operation)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">提交用户:</span>
                        <span class="detail-value">${audit.userId}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">状态:</span>
                        <span class="detail-value"><span class="status-badge status-${audit.status}">${this.getStatusName(audit.status)}</span></span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">优先级:</span>
                        <span class="detail-value"><span class="priority-badge priority-${audit.priority}">${this.getPriorityName(audit.priority)}</span></span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">提交时间:</span>
                        <span class="detail-value">${this.formatDateTime(audit.timestamp)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">描述:</span>
                        <span class="detail-value">${audit.description || '-'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">操作数据:</span>
                        <span class="detail-value"><pre>${JSON.stringify(audit.data, null, 2)}</pre></span>
                    </div>
                    ${audit.result ? `
                    <div class="detail-row">
                        <span class="detail-label">执行结果:</span>
                        <span class="detail-value"><pre>${JSON.stringify(audit.result, null, 2)}</pre></span>
                    </div>
                    ` : ''}
                </div>
            `;

            modal.classList.add('active');
            
        } catch (error) {
            console.error('显示审核详情失败:', error);
            this.showError('显示详情失败: ' + error.message);
        }
    }

    /**
     * 显示批准模态框
     */
    async showApprovalModal(auditId) {
        try {
            const audit = await window.auditSystem.getAuditFromDatabase(auditId);
            if (!audit) {
                this.showError('审核记录不存在');
                return;
            }

            const modal = document.getElementById('approvalModal');
            const modalBody = document.getElementById('approvalModalBody');

            modalBody.innerHTML = `
                <div class="approval-section">
                    <div class="approval-header">
                        <h3>批准审核</h3>
                        <span class="status-badge status-${audit.status}">${this.getStatusName(audit.status)}</span>
                    </div>
                    
                    <div class="audit-details">
                        <div class="detail-row">
                            <span class="detail-label">操作类型:</span>
                            <span class="detail-value">${this.getOperationName(audit.operation)}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">提交用户:</span>
                            <span class="detail-value">${audit.userId}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">提交时间:</span>
                            <span class="detail-value">${this.formatDateTime(audit.timestamp)}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">描述:</span>
                            <span class="detail-value">${audit.description || '-'}</span>
                        </div>
                    </div>
                    
                    <div class="approval-actions">
                        <h4>批准意见</h4>
                        <textarea id="approvalNotes" class="notes-textarea" placeholder="请输入批准或拒绝的理由..."></textarea>
                        <div class="action-buttons">
                            <button class="btn btn-success" onclick="auditPage.processApproval('${auditId}', true)">批准</button>
                            <button class="btn btn-danger" onclick="auditPage.processApproval('${auditId}', false)">拒绝</button>
                            <button class="btn btn-secondary" onclick="auditPage.closeApprovalModal()">取消</button>
                        </div>
                    </div>
                </div>
            `;

            modal.classList.add('active');
            
        } catch (error) {
            console.error('显示批准模态框失败:', error);
            this.showError('显示批准界面失败: ' + error.message);
        }
    }

    /**
     * 处理批准
     */
    async processApproval(auditId, decision) {
        try {
            const notes = document.getElementById('approvalNotes').value;
            
            // 获取当前用户的批准请求
            const approvals = await window.auditSystem.getApprovalsForAudit(auditId);
            const userApproval = approvals.find(approval => 
                approval.approverId === window.currentUser?.id && 
                approval.status === 'pending'
            );

            if (!userApproval) {
                this.showError('没有找到待处理的批准请求');
                return;
            }

            await window.auditSystem.processApproval(userApproval.id, decision, notes);
            
            this.closeApprovalModal();
            this.showSuccess(decision ? '批准成功' : '拒绝成功');
            this.loadCurrentTab();
            
        } catch (error) {
            console.error('处理批准失败:', error);
            this.showError('处理失败: ' + error.message);
        }
    }

    /**
     * 拒绝审核
     */
    async rejectAudit(auditId) {
        if (!confirm('确定要拒绝这个审核请求吗？')) {
            return;
        }

        try {
            const approvals = await window.auditSystem.getApprovalsForAudit(auditId);
            const userApproval = approvals.find(approval => 
                approval.approverId === window.currentUser?.id && 
                approval.status === 'pending'
            );

            if (userApproval) {
                await window.auditSystem.processApproval(userApproval.id, false, '管理员拒绝');
            }

            this.showSuccess('拒绝成功');
            this.loadCurrentTab();
            
        } catch (error) {
            console.error('拒绝审核失败:', error);
            this.showError('拒绝失败: ' + error.message);
        }
    }

    /**
     * 创建回滚
     */
    async createRollback(auditId) {
        const reason = prompt('请输入回滚原因:');
        if (!reason) {
            return;
        }

        try {
            await window.auditSystem.createRollback(auditId, reason);
            this.showSuccess('回滚请求已创建');
            this.loadCurrentTab();
            
        } catch (error) {
            console.error('创建回滚失败:', error);
            this.showError('创建回滚失败: ' + error.message);
        }
    }

    /**
     * 保存审核设置
     */
    async saveAuditSettings() {
        try {
            const config = {
                enabled: document.getElementById('auditEnabled').checked,
                requireApproval: document.getElementById('requireApproval').checked,
                approvalTimeout: parseInt(document.getElementById('approvalTimeout').value),
                minApprovers: parseInt(document.getElementById('minApprovers').value),
                maxRollbacks: parseInt(document.getElementById('maxRollbacks').value),
                notificationEnabled: document.getElementById('notificationEnabled').checked
            };

            // 更新审核系统配置
            Object.assign(window.auditSystem.auditConfig, config);

            // 保存到系统设置
            if (window.systemSettings) {
                await window.systemSettings.updateSettings({ audit: config });
            }

            this.showSuccess('设置保存成功');
            
        } catch (error) {
            console.error('保存设置失败:', error);
            this.showError('保存失败: ' + error.message);
        }
    }

    /**
     * 设置自动刷新
     */
    setupAutoRefresh() {
        // 每30秒自动刷新统计数据
        setInterval(() => {
            this.loadStatistics();
        }, 30000);

        // 每60秒自动刷新待处理审核
        setInterval(() => {
            if (this.currentTab === 'pending') {
                this.loadPendingAudits();
            }
        }, 60000);
    }

    /**
     * 防抖加载
     */
    debounceLoad() {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.loadCurrentTab();
        }, 500);
    }

    /**
     * 辅助方法
     */
    getOperationName(operation) {
        const names = {
            delete_user: '删除用户',
            delete_data: '删除数据',
            modify_permissions: '修改权限',
            system_settings: '系统设置',
            backup_restore: '备份恢复',
            vikey_management: 'Vikey管理'
        };
        return names[operation] || operation;
    }

    getStatusName(status) {
        const names = {
            pending: '待处理',
            approved: '已批准',
            rejected: '已拒绝',
            executed: '已执行',
            failed: '执行失败',
            rolled_back: '已回滚'
        };
        return names[status] || status;
    }

    getPriorityName(priority) {
        const names = {
            high: '高',
            medium: '中',
            low: '低'
        };
        return names[priority] || priority;
    }

    getApprovalStatusName(status) {
        const names = {
            pending: '待处理',
            approved: '已批准',
            rejected: '已拒绝',
            expired: '已过期'
        };
        return names[status] || status;
    }

    getRollbackStatusName(status) {
        const names = {
            pending: '待处理',
            completed: '已完成',
            failed: '失败'
        };
        return names[status] || status;
    }

    formatDateTime(timestamp) {
        return new Date(timestamp).toLocaleString('zh-CN');
    }

    showLoading(container) {
        container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>加载中...</p>
            </div>
        `;
    }

    showEmptyState(container, message) {
        container.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <h3>${message}</h3>
            </div>
        `;
    }

    showError(container, message) {
        if (typeof container === 'string') {
            alert(message);
        } else {
            container.innerHTML = `
                <div class="error-state">
                    <h3>错误</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    showSuccess(message) {
        // 创建成功提示
        const toast = document.createElement('div');
        toast.className = 'toast success';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 15px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }

    /**
     * 数据库操作方法
     */
    async getAllApprovals() {
        return new Promise((resolve, reject) => {
            const transaction = window.auditSystem.db.transaction('approvals', 'readonly');
            const request = transaction.objectStore('approvals').getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getAllRollbacks() {
        return new Promise((resolve, reject) => {
            const transaction = window.auditSystem.db.transaction('rollbacks', 'readonly');
            const request = transaction.objectStore('rollbacks').getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getRollbackCount(month, year) {
        // 简化实现，返回模拟数据
        return 3;
    }

    /**
     * 模态框控制
     */
    closeAuditModal() {
        document.getElementById('auditModal').classList.remove('active');
    }

    closeApprovalModal() {
        document.getElementById('approvalModal').classList.remove('active');
    }

    /**
     * 渲染分页
     */
    renderPagination(container, total) {
        const totalPages = Math.ceil(total / this.pageSize);
        if (totalPages <= 1) return;

        let paginationHtml = '<div class="pagination">';
        
        // 上一页
        paginationHtml += `
            <button ${this.currentPage === 1 ? 'disabled' : ''} 
                    onclick="auditPage.goToPage(${this.currentPage - 1})">
                上一页
            </button>
        `;

        // 页码
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= this.currentPage - 2 && i <= this.currentPage + 2)) {
                paginationHtml += `
                    <button class="${i === this.currentPage ? 'active' : ''}" 
                            onclick="auditPage.goToPage(${i})">
                        ${i}
                    </button>
                `;
            } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
                paginationHtml += '<span>...</span>';
            }
        }

        // 下一页
        paginationHtml += `
            <button ${this.currentPage === totalPages ? 'disabled' : ''} 
                    onclick="auditPage.goToPage(${this.currentPage + 1})">
                下一页
            </button>
        `;

        paginationHtml += '</div>';
        container.insertAdjacentHTML('beforeend', paginationHtml);
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadCurrentTab();
    }
}

// 全局函数
window.refreshPendingAudits = () => auditPage.loadPendingAudits();
window.refreshAuditHistory = () => auditPage.loadAuditHistory();
window.refreshRollbacks = () => auditPage.loadRollbacks();
window.clearFilters = () => {
    auditPage.filters = {
        operation: '',
        priority: '',
        user: '',
        status: '',
        startTime: '',
        endTime: '',
        rollbackStatus: ''
    };
    // 重置筛选器UI
    document.querySelectorAll('select, input[type="text"], input[type="datetime-local"]').forEach(input => {
        if (input.id.startsWith('filter')) {
            input.value = '';
        }
    });
    auditPage.loadCurrentTab();
};
window.clearHistoryFilters = window.clearFilters;
window.clearRollbackFilters = window.clearFilters;
window.resetAuditSettings = () => auditPage.loadSettings();

// 初始化页面
let auditPage;
document.addEventListener('DOMContentLoaded', () => {
    auditPage = new AuditManagementPage();
});

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);