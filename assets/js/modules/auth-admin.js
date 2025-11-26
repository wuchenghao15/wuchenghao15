/**
 * auth-admin.js - 管理员授权系统模块
 * 实现多管理员授权密码修改机制，支持3名管理员或1名超级管理员授权
 */

// 管理员授权系统模块
const AdminAuthSystem = {
    // 授权请求存储
    pendingRequests: [],
    
    // 角色常量定义
    ROLES: {
        SUPER_ADMIN: 'super_admin',
        ADMIN: 'admin',
        VIKEY_ADMIN: 'vikey_admin',
        PASSWORD_ADMIN: 'password_admin'
    },
    
    // 授权状态定义
    STATUS: {
        PENDING: 'pending',
        APPROVED: 'approved',
        REJECTED: 'rejected',
        COMPLETED: 'completed'
    },
    
    // 初始化模块
    init() {
        console.log('管理员授权系统初始化...');
        this.loadPendingRequests();
        this.setupEventListeners();
    },
    
    // 加载待处理的授权请求
    loadPendingRequests() {
        // 从localStorage加载或使用模拟数据
        try {
            const savedRequests = localStorage.getItem('adminAuthRequests');
            if (savedRequests) {
                this.pendingRequests = JSON.parse(savedRequests);
            } else {
                // 使用模拟数据
                this.pendingRequests = this.getMockPendingRequests();
            }
        } catch (error) {
            console.error('加载授权请求失败:', error);
            this.pendingRequests = [];
        }
    },
    
    // 保存授权请求到localStorage
    saveRequests() {
        try {
            localStorage.setItem('adminAuthRequests', JSON.stringify(this.pendingRequests));
        } catch (error) {
            console.error('保存授权请求失败:', error);
        }
    },
    
    // 设置事件监听器
    setupEventListeners() {
        // 监听授权请求相关事件
        document.addEventListener('DOMContentLoaded', () => {
            // 授权请求列表页面初始化
            if (document.getElementById('auth-requests-container')) {
                this.renderAuthRequestsList();
            }
        });
    },
    
    // 创建新的密码修改授权请求
    createPasswordChangeRequest(userToModify, requestedBy) {
        // 验证请求者权限
        if (!Auth.hasPermission(['super_admin', 'admin', 'vikey_admin', 'password_admin'])) {
            return { success: false, error: '权限不足，无法创建授权请求' };
        }
        
        // 生成唯一请求ID
        const requestId = 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        // 创建新请求
        const newRequest = {
            id: requestId,
            type: 'password_change',
            userToModify,
            requestedBy,
            createdAt: new Date().toISOString(),
            status: this.STATUS.PENDING,
            approvals: [],
            requiredApprovals: 3, // 默认需要3名管理员批准
            completedAt: null,
            processedBy: null,
            notificationSent: false
        };
        
        // 如果是超级管理员请求，可直接设置为已批准
        if (Auth.getCurrentUser() && Auth.getCurrentUser().role === this.ROLES.SUPER_ADMIN) {
            newRequest.requiredApprovals = 1;
        }
        
        // 添加到待处理列表
        this.pendingRequests.push(newRequest);
        
        // 保存并通知相关管理员
        this.saveRequests();
        this.notifyAdminsAboutNewRequest(newRequest);
        
        // 记录日志
        if (typeof Logging !== 'undefined') {
            Logging.logAction('create_auth_request', 
                `创建密码修改授权请求 ${requestId}，目标用户: ${userToModify.username}`);
        }
        
        return { success: true, requestId };
    },
    
    // 批准授权请求
    approveRequest(requestId, adminUser) {
        const request = this.pendingRequests.find(r => r.id === requestId);
        
        if (!request) {
            return { success: false, error: '授权请求不存在' };
        }
        
        if (request.status !== this.STATUS.PENDING) {
            return { success: false, error: '该请求已处理完毕' };
        }
        
        // 检查是否已经批准过
        const hasApproved = request.approvals.some(a => a.adminId === adminUser.id);
        if (hasApproved) {
            return { success: false, error: '您已经批准过此请求' };
        }
        
        // 添加批准记录
        request.approvals.push({
            adminId: adminUser.id,
            adminName: adminUser.username,
            adminRole: adminUser.role,
            approvedAt: new Date().toISOString()
        });
        
        // 检查是否达到所需批准数量
        let canProceed = false;
        
        // 检查是否有超级管理员批准
        const hasSuperAdminApproval = request.approvals.some(a => a.adminRole === this.ROLES.SUPER_ADMIN);
        
        if (hasSuperAdminApproval) {
            // 超级管理员一锤定音
            canProceed = true;
        } else if (request.approvals.length >= request.requiredApprovals) {
            // 满足所需管理员数量
            canProceed = true;
        }
        
        if (canProceed) {
            request.status = this.STATUS.APPROVED;
            request.completedAt = new Date().toISOString();
            request.processedBy = adminUser.id;
            
            // 执行密码修改操作（这里是模拟，实际会调用相应API）
            this.executePasswordChange(request);
        }
        
        // 保存更新
        this.saveRequests();
        
        // 发送通知给相关人员
        this.notifyApprovalUpdate(request);
        
        // 记录日志
        if (typeof Logging !== 'undefined') {
            Logging.logAction('approve_auth_request', 
                `管理员 ${adminUser.username} 批准了授权请求 ${requestId}`);
        }
        
        return { success: true, request };
    },
    
    // 拒绝授权请求
    rejectRequest(requestId, adminUser, reason) {
        const request = this.pendingRequests.find(r => r.id === requestId);
        
        if (!request) {
            return { success: false, error: '授权请求不存在' };
        }
        
        if (request.status !== this.STATUS.PENDING) {
            return { success: false, error: '该请求已处理完毕' };
        }
        
        // 更新请求状态
        request.status = this.STATUS.REJECTED;
        request.rejectionReason = reason || '未提供原因';
        request.completedAt = new Date().toISOString();
        request.processedBy = adminUser.id;
        
        // 保存更新
        this.saveRequests();
        
        // 发送通知给相关人员
        this.notifyRejection(request);
        
        // 记录日志
        if (typeof Logging !== 'undefined') {
            Logging.logAction('reject_auth_request', 
                `管理员 ${adminUser.username} 拒绝了授权请求 ${requestId}，原因: ${reason}`);
        }
        
        return { success: true };
    },
    
    // 执行密码修改（实际环境中会调用API）
    executePasswordChange(request) {
        // 这里是模拟实现，实际环境中会调用后端API
        console.log(`执行密码修改操作 for ${request.userToModify.username}`);
        
        // 标记为已完成
        request.status = this.STATUS.COMPLETED;
        
        // 记录操作日志
        if (typeof Logging !== 'undefined') {
            Logging.logAction('password_change_executed', 
                `成功执行密码修改: ${request.userToModify.username}`);
        }
    },
    
    // 获取待处理的授权请求
    getPendingRequests() {
        return this.pendingRequests.filter(r => r.status === this.STATUS.PENDING);
    },
    
    // 获取历史授权请求
    getHistoryRequests() {
        return this.pendingRequests.filter(r => 
            r.status === this.STATUS.APPROVED || 
            r.status === this.STATUS.REJECTED || 
            r.status === this.STATUS.COMPLETED
        ).sort((a, b) => new Date(b.completedAt) - new Date(a.completedAt));
    },
    
    // 通知管理员关于新请求
    notifyAdminsAboutNewRequest(request) {
        // 获取所有管理员（这里是模拟，实际会从API获取）
        const admins = this.getMockAdmins();
        
        // 排除请求者自己
        const adminsToNotify = admins.filter(admin => admin.id !== request.requestedBy.id);
        
        // 发送通知
        if (typeof Notification !== 'undefined') {
            adminsToNotify.forEach(admin => {
                // 在实际环境中，这里会通过WebSocket或其他方式发送给特定管理员
                console.log(`通知管理员 ${admin.username} 关于新的授权请求 ${request.id}`);
                
                // 如果当前用户是目标管理员，显示通知
                if (Auth.getCurrentUser() && Auth.getCurrentUser().id === admin.id) {
                    Notification.show(
                        '新授权请求',
                        `需要您批准密码修改请求`,
                        'info',
                        'auth-requests.html'
                    );
                }
            });
        }
    },
    
    // 通知批准更新
    notifyApprovalUpdate(request) {
        // 通知所有相关人员（请求者和已批准的管理员）
        const userIdsToNotify = [
            request.requestedBy.id, 
            ...request.approvals.map(a => a.adminId)
        ].filter((value, index, self) => self.indexOf(value) === index);
        
        // 发送通知
        if (typeof Notification !== 'undefined') {
            userIdsToNotify.forEach(userId => {
                // 模拟通知发送
                if (Auth.getCurrentUser() && Auth.getCurrentUser().id === userId) {
                    if (request.status === this.STATUS.APPROVED) {
                        Notification.show(
                            '授权请求已批准',
                            `密码修改请求已获得足够批准，将立即执行`,
                            'success',
                            'auth-requests.html'
                        );
                    } else {
                        Notification.show(
                            '授权请求更新',
                            `密码修改请求有新的批准，当前已获得 ${request.approvals.length}/${request.requiredApprovals} 批准`,
                            'info',
                            'auth-requests.html'
                        );
                    }
                }
            });
        }
    },
    
    // 通知拒绝
    notifyRejection(request) {
        // 通知请求者
        if (typeof Notification !== 'undefined') {
            if (Auth.getCurrentUser() && Auth.getCurrentUser().id === request.requestedBy.id) {
                Notification.show(
                    '授权请求已拒绝',
                    `您的密码修改请求已被拒绝: ${request.rejectionReason}`,
                    'error',
                    'auth-requests.html'
                );
            }
        }
    },
    
    // 渲染授权请求列表
    renderAuthRequestsList() {
        const container = document.getElementById('auth-requests-container');
        const pendingRequests = this.getPendingRequests();
        const historyRequests = this.getHistoryRequests();
        
        // 渲染待处理请求
        const pendingContainer = document.getElementById('pending-requests');
        pendingContainer.innerHTML = '';
        
        if (pendingRequests.length === 0) {
            pendingContainer.innerHTML = '<div class="no-data">暂无待处理的授权请求</div>';
        } else {
            pendingRequests.forEach(request => {
                pendingContainer.appendChild(this.createRequestElement(request, true));
            });
        }
        
        // 渲染历史请求
        const historyContainer = document.getElementById('history-requests');
        historyContainer.innerHTML = '';
        
        if (historyRequests.length === 0) {
            historyContainer.innerHTML = '<div class="no-data">暂无历史授权请求</div>';
        } else {
            historyRequests.forEach(request => {
                historyContainer.appendChild(this.createRequestElement(request, false));
            });
        }
    },
    
    // 创建请求元素
    createRequestElement(request, isPending) {
        const element = document.createElement('div');
        element.className = `auth-request ${request.status}`;
        
        const currentUser = Auth.getCurrentUser();
        const hasApproved = request.approvals.some(a => a.adminId === currentUser.id);
        const isRequestOwner = currentUser.id === request.requestedBy.id;
        
        let statusText = '';
        let statusClass = '';
        
        switch (request.status) {
            case this.STATUS.PENDING:
                statusText = '待批准';
                statusClass = 'status-pending';
                break;
            case this.STATUS.APPROVED:
                statusText = '已批准';
                statusClass = 'status-approved';
                break;
            case this.STATUS.REJECTED:
                statusText = '已拒绝';
                statusClass = 'status-rejected';
                break;
            case this.STATUS.COMPLETED:
                statusText = '已完成';
                statusClass = 'status-completed';
                break;
        }
        
        let actionsHtml = '';
        
        // 添加操作按钮（仅对pending且有权限的用户显示）
        if (isPending && !isRequestOwner && !hasApproved && 
            Auth.hasPermission(['admin', 'vikey_admin', 'password_admin', 'super_admin'])) {
            actionsHtml = `
                <div class="request-actions">
                    <button class="btn btn-sm btn-primary" onclick="AdminAuthSystem.approveRequest('${request.id}', Auth.getCurrentUser())">批准</button>
                    <button class="btn btn-sm btn-danger" onclick="AdminAuthSystem.showRejectDialog('${request.id}')">拒绝</button>
                </div>
            `;
        }
        
        // 生成批准列表
        let approvalsHtml = '';
        if (request.approvals.length > 0) {
            approvalsHtml = '<div class="approvals-list">';
            request.approvals.forEach(approval => {
                approvalsHtml += `
                    <div class="approval-item">
                        <span class="admin-name">${approval.adminName}</span>
                        <span class="admin-role">(${approval.adminRole})</span>
                        <span class="approval-time">${this.formatDate(approval.approvedAt)}</span>
                    </div>
                `;
            });
            approvalsHtml += '</div>';
        }
        
        // 拒绝原因
        let rejectionHtml = '';
        if (request.status === this.STATUS.REJECTED && request.rejectionReason) {
            rejectionHtml = `
                <div class="rejection-reason">
                    <strong>拒绝原因:</strong> ${request.rejectionReason}
                </div>
            `;
        }
        
        element.innerHTML = `
            <div class="request-header">
                <div class="request-type">密码修改请求</div>
                <div class="request-status">
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
            </div>
            <div class="request-body">
                <div class="request-info">
                    <div><strong>请求ID:</strong> ${request.id}</div>
                    <div><strong>目标用户:</strong> ${request.userToModify.username}</div>
                    <div><strong>请求者:</strong> ${request.requestedBy.username}</div>
                    <div><strong>创建时间:</strong> ${this.formatDate(request.createdAt)}</div>
                    ${request.completedAt ? `<div><strong>完成时间:</strong> ${this.formatDate(request.completedAt)}</div>` : ''}
                </div>
                <div class="approval-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${(request.approvals.length / request.requiredApprovals) * 100}%"></div>
                    </div>
                    <div class="progress-text">
                        ${request.approvals.length}/${request.requiredApprovals} 批准
                    </div>
                </div>
                ${approvalsHtml}
                ${rejectionHtml}
            </div>
            ${actionsHtml}
        `;
        
        return element;
    },
    
    // 显示拒绝对话框
    showRejectDialog(requestId) {
        const reason = prompt('请输入拒绝此授权请求的原因:');
        if (reason !== null) {
            const result = this.rejectRequest(requestId, Auth.getCurrentUser(), reason);
            if (result.success) {
                this.renderAuthRequestsList();
                if (typeof Notification !== 'undefined') {
                    Notification.show('成功', '已拒绝授权请求', 'success');
                }
            } else {
                if (typeof Notification !== 'undefined') {
                    Notification.show('错误', result.error, 'error');
                }
            }
        }
    },
    
    // 格式化日期
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    },
    
    // 模拟数据生成函数
    getMockPendingRequests() {
        return [
            {
                id: 'req_1627890123_abc123',
                type: 'password_change',
                userToModify: { id: 'user_001', username: 'test_user' },
                requestedBy: { id: 'admin_001', username: 'admin1' },
                createdAt: '2023-08-02T10:30:00Z',
                status: this.STATUS.PENDING,
                approvals: [
                    {
                        adminId: 'admin_002',
                        adminName: 'admin2',
                        adminRole: 'admin',
                        approvedAt: '2023-08-02T11:00:00Z'
                    }
                ],
                requiredApprovals: 3,
                completedAt: null,
                processedBy: null
            },
            {
                id: 'req_1627890456_def456',
                type: 'password_change',
                userToModify: { id: 'user_002', username: 'another_user' },
                requestedBy: { id: 'vikey_001', username: 'vikey_admin' },
                createdAt: '2023-08-02T14:20:00Z',
                status: this.STATUS.PENDING,
                approvals: [],
                requiredApprovals: 3,
                completedAt: null,
                processedBy: null
            }
        ];
    },
    
    // 模拟管理员数据
    getMockAdmins() {
        return [
            { id: 'admin_001', username: 'admin1', role: 'admin' },
            { id: 'admin_002', username: 'admin2', role: 'admin' },
            { id: 'admin_003', username: 'admin3', role: 'admin' },
            { id: 'vikey_001', username: 'vikey_admin', role: 'vikey_admin' },
            { id: 'super_001', username: 'super_admin', role: 'super_admin' }
        ];
    }
};

// 暴露模块到全局
window.AdminAuthSystem = AdminAuthSystem;

// 初始化
if (typeof Auth !== 'undefined' && Auth.isLoggedIn()) {
    AdminAuthSystem.init();
}