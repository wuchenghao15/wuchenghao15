/**
 * auth-requests.js - 授权请求页面模块
 * 处理授权请求页面的交互逻辑和数据加载
 */

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 检查必要模块是否加载
    if (typeof Auth === 'undefined' || typeof Notification === 'undefined' || 
        typeof Logging === 'undefined' || typeof AdminAuthSystem === 'undefined') {
        console.error('缺少必要的依赖模块，正在尝试重新加载...');
        setTimeout(() => {
            window.location.reload();
        }, 1000);
        return;
    }
    
    // 初始化页面
    initAuthRequestsPage();
});

/**
 * 初始化授权请求页面
 */
function initAuthRequestsPage() {
    // 页面加载完成后隐藏加载遮罩
    setTimeout(() => {
        document.getElementById('page-loading').style.display = 'none';
    }, 500);
    
    // 检查用户权限
    checkUserPermissions();
    
    // 设置用户信息
    setCurrentUserInfo();
    
    // 初始化事件监听器
    initEventListeners();
    
    // 加载授权请求数据
    loadAuthRequests();
    
    // 加载用户列表（用于创建新请求）
    loadUserList();
}

/**
 * 检查用户权限
 */
function checkUserPermissions() {
    // 验证用户是否有权限访问此页面
    if (!Auth.hasPermission(['admin', 'vikey_admin', 'super_admin', 'password_admin'])) {
        // 显示权限警告
        document.getElementById('permission-warning').style.display = 'block';
        
        // 隐藏其他内容
        const contentElements = document.querySelectorAll('.page-header, .action-buttons, .stats-cards, .auth-requests-container');
        contentElements.forEach(el => el.style.display = 'none');
        
        // 记录未授权访问尝试
        Logging.logAction('unauthorized_access', '尝试访问管理员授权管理页面但权限不足', 'warning');
        
        // 显示通知
        Notification.show('权限不足', '您没有权限访问此页面', 'error');
        
        return false;
    }
    
    return true;
}

/**
 * 设置当前用户信息
 */
function setCurrentUserInfo() {
    const currentUser = Auth.getCurrentUser();
    if (currentUser) {
        document.getElementById('current-user-name').textContent = currentUser.username || '管理员';
    }
}

/**
 * 初始化事件监听器
 */
function initEventListeners() {
    // 退出按钮
    document.getElementById('logout-btn').addEventListener('click', function() {
        Auth.logout();
        window.location.href = 'login.html';
    });
    
    // 创建新请求按钮
    document.getElementById('create-request-btn').addEventListener('click', function() {
        if (!Auth.hasPermission(['admin', 'vikey_admin', 'super_admin', 'password_admin'])) {
            Notification.show('权限不足', '您没有权限创建授权请求', 'error');
            return;
        }
        
        // 显示创建请求模态框
        showModal('create-request-modal');
    });
    
    // 提交请求按钮
    document.getElementById('submit-request-btn').addEventListener('click', function() {
        submitAuthRequest();
    });
    
    // 确认拒绝按钮
    document.getElementById('confirm-reject-btn').addEventListener('click', function() {
        confirmRejection();
    });
    
    // 历史过滤选择器
    document.getElementById('history-filter').addEventListener('change', function() {
        filterHistoryRequests();
    });
    
    // 关闭模态框事件
    const closeModalButtons = document.querySelectorAll('.close-modal');
    closeModalButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modalId = this.closest('.modal').id;
            hideModal(modalId);
        });
    });
    
    // 点击模态框外部关闭
    window.addEventListener('click', function(event) {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (event.target === modal) {
                hideModal(modal.id);
            }
        });
    });
    
    // ESC键关闭模态框
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                hideModal(modal.id);
            });
        }
    });
}

/**
 * 加载授权请求数据
 */
function loadAuthRequests() {
    // 确保AdminAuthSystem已经初始化
    if (typeof AdminAuthSystem !== 'undefined') {
        // 渲染授权请求列表
        AdminAuthSystem.renderAuthRequestsList();
        
        // 更新统计数据
        updateStatsCount();
    } else {
        console.error('AdminAuthSystem模块未加载');
        setTimeout(loadAuthRequests, 500);
    }
}

/**
 * 加载用户列表
 */
function loadUserList() {
    // 在实际环境中，这里会从API获取用户列表
    const userSelect = document.getElementById('user-select');
    
    // 清空现有选项
    userSelect.innerHTML = '';
    
    // 添加占位符选项
    const placeholderOption = document.createElement('option');
    placeholderOption.value = '';
    placeholderOption.textContent = '请选择用户';
    placeholderOption.disabled = true;
    placeholderOption.selected = true;
    userSelect.appendChild(placeholderOption);
    
    // 获取模拟用户数据
    const users = getMockUsers();
    
    // 添加用户选项
    users.forEach(user => {
        const option = document.createElement('option');
        option.value = JSON.stringify(user);
        option.textContent = `${user.username} (${user.role})`;
        userSelect.appendChild(option);
    });
}

/**
 * 提交授权请求
 */
function submitAuthRequest() {
    const userSelect = document.getElementById('user-select');
    const reasonTextarea = document.getElementById('reason');
    
    // 验证表单
    if (!userSelect.value) {
        Notification.show('错误', '请选择要修改密码的用户', 'error');
        return;
    }
    
    if (!reasonTextarea.value.trim()) {
        Notification.show('错误', '请输入修改原因', 'error');
        return;
    }
    
    // 解析用户数据
    const userToModify = JSON.parse(userSelect.value);
    const currentUser = Auth.getCurrentUser();
    
    // 创建授权请求
    const result = AdminAuthSystem.createPasswordChangeRequest(userToModify, currentUser);
    
    if (result.success) {
        // 请求创建成功
        Notification.show('成功', '授权请求已创建', 'success');
        
        // 隐藏模态框
        hideModal('create-request-modal');
        
        // 重置表单
        document.getElementById('create-request-form').reset();
        
        // 重新加载请求列表
        loadAuthRequests();
        
        // 记录操作
        Logging.logAction('submit_auth_request', `提交了密码修改授权请求: ${userToModify.username}`);
    } else {
        // 请求创建失败
        Notification.show('错误', result.error, 'error');
    }
}

/**
 * 显示拒绝对话框
 */
function showRejectDialog(requestId) {
    const rejectRequestIdInput = document.getElementById('reject-request-id');
    rejectRequestIdInput.value = requestId;
    
    // 清空拒绝原因
    document.getElementById('reject-reason').value = '';
    
    // 显示模态框
    showModal('reject-request-modal');
}

/**
 * 确认拒绝
 */
function confirmRejection() {
    const requestId = document.getElementById('reject-request-id').value;
    const reason = document.getElementById('reject-reason').value.trim();
    
    if (!reason) {
        Notification.show('错误', '请输入拒绝原因', 'error');
        return;
    }
    
    // 拒绝请求
    const result = AdminAuthSystem.rejectRequest(requestId, Auth.getCurrentUser(), reason);
    
    if (result.success) {
        // 拒绝成功
        Notification.show('成功', '已拒绝授权请求', 'success');
        
        // 隐藏模态框
        hideModal('reject-request-modal');
        
        // 重新加载请求列表
        loadAuthRequests();
        
        // 记录操作
        Logging.logAction('confirm_rejection', `拒绝了授权请求 ${requestId}，原因: ${reason}`);
    } else {
        // 拒绝失败
        Notification.show('错误', result.error, 'error');
    }
}

/**
 * 显示请求详情
 */
function showRequestDetails(requestId) {
    // 获取请求数据
    const allRequests = [
        ...AdminAuthSystem.getPendingRequests(),
        ...AdminAuthSystem.getHistoryRequests()
    ];
    
    const request = allRequests.find(r => r.id === requestId);
    
    if (!request) {
        Notification.show('错误', '未找到请求信息', 'error');
        return;
    }
    
    // 生成详情HTML
    const detailContent = generateRequestDetailHTML(request);
    
    // 设置详情内容
    document.getElementById('request-detail-content').innerHTML = detailContent;
    
    // 显示模态框
    showModal('request-detail-modal');
}

/**
 * 生成请求详情HTML
 */
function generateRequestDetailHTML(request) {
    // 状态文本和类
    let statusText = '';
    let statusClass = '';
    
    switch (request.status) {
        case 'pending':
            statusText = '待批准';
            statusClass = 'status-pending';
            break;
        case 'approved':
            statusText = '已批准';
            statusClass = 'status-approved';
            break;
        case 'rejected':
            statusText = '已拒绝';
            statusClass = 'status-rejected';
            break;
        case 'completed':
            statusText = '已完成';
            statusClass = 'status-completed';
            break;
    }
    
    // 格式化日期
    const formatDate = (dateString) => {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };
    
    // 生成批准列表HTML
    let approvalsHTML = `
        <table class="approvals-table">
            <thead>
                <tr>
                    <th>管理员</th>
                    <th>角色</th>
                    <th>批准时间</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    if (request.approvals && request.approvals.length > 0) {
        request.approvals.forEach(approval => {
            approvalsHTML += `
                <tr>
                    <td>${approval.adminName}</td>
                    <td>${approval.adminRole}</td>
                    <td>${formatDate(approval.approvedAt)}</td>
                </tr>
            `;
        });
    } else {
        approvalsHTML += `
            <tr>
                <td colspan="3" style="text-align: center; color: #6c757d;">暂无批准记录</td>
            </tr>
        `;
    }
    
    approvalsHTML += `
            </tbody>
        </table>
    `;
    
    // 组装详情HTML
    return `
        <div class="detail-section">
            <h4>基本信息</h4>
            <div class="detail-grid">
                <div class="detail-item"><strong>请求ID:</strong> ${request.id}</div>
                <div class="detail-item"><strong>请求类型:</strong> 密码修改</div>
                <div class="detail-item"><strong>状态:</strong> <span class="status-badge ${statusClass}">${statusText}</span></div>
                <div class="detail-item"><strong>创建时间:</strong> ${formatDate(request.createdAt)}</div>
                ${request.completedAt ? `<div class="detail-item"><strong>完成时间:</strong> ${formatDate(request.completedAt)}</div>` : ''}
            </div>
        </div>
        
        <div class="detail-section">
            <h4>用户信息</h4>
            <div class="detail-grid">
                <div class="detail-item"><strong>目标用户:</strong> ${request.userToModify.username}</div>
                ${request.userToModify.role ? `<div class="detail-item"><strong>用户角色:</strong> ${request.userToModify.role}</div>` : ''}
                <div class="detail-item"><strong>请求者:</strong> ${request.requestedBy.username}</div>
                ${request.requestedBy.role ? `<div class="detail-item"><strong>请求者角色:</strong> ${request.requestedBy.role}</div>` : ''}
            </div>
        </div>
        
        <div class="detail-section">
            <h4>审批进度</h4>
            <div class="approval-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(request.approvals.length / request.requiredApprovals) * 100}%"></div>
                </div>
                <div class="progress-text">
                    ${request.approvals.length}/${request.requiredApprovals} 批准
                </div>
            </div>
        </div>
        
        <div class="detail-section">
            <h4>批准记录</h4>
            ${approvalsHTML}
        </div>
        
        ${request.rejectionReason ? `
        <div class="detail-section">
            <h4>拒绝原因</h4>
            <div class="rejection-reason">${request.rejectionReason}</div>
        </div>
        ` : ''}
    `;
}

/**
 * 过滤历史请求
 */
function filterHistoryRequests() {
    const filterValue = document.getElementById('history-filter').value;
    const historyRequests = document.querySelectorAll('#history-requests .auth-request');
    
    historyRequests.forEach(request => {
        if (filterValue === 'all' || request.classList.contains(filterValue)) {
            request.style.display = '';
        } else {
            request.style.display = 'none';
        }
    });
}

/**
 * 更新统计计数
 */
function updateStatsCount() {
    const pendingRequests = AdminAuthSystem.getPendingRequests();
    const historyRequests = AdminAuthSystem.getHistoryRequests();
    
    const approvedCount = historyRequests.filter(r => r.status === 'approved' || r.status === 'completed').length;
    const rejectedCount = historyRequests.filter(r => r.status === 'rejected').length;
    const totalCount = pendingRequests.length + historyRequests.length;
    
    // 更新计数显示
    document.getElementById('pending-count').textContent = pendingRequests.length;
    document.getElementById('approved-count').textContent = approvedCount;
    document.getElementById('rejected-count').textContent = rejectedCount;
    document.getElementById('total-count').textContent = totalCount;
}

/**
 * 显示模态框
 */
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden'; // 防止背景滚动
    }
}

/**
 * 隐藏模态框
 */
function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = ''; // 恢复背景滚动
    }
}

/**
 * 获取模拟用户数据
 */
function getMockUsers() {
    return [
        { id: 'user_001', username: 'test_user', role: 'user' },
        { id: 'user_002', username: 'another_user', role: 'user' },
        { id: 'user_003', username: 'system_user', role: 'user' },
        { id: 'admin_001', username: 'admin1', role: 'admin' },
        { id: 'admin_002', username: 'admin2', role: 'admin' },
        { id: 'vikey_001', username: 'vikey_admin', role: 'vikey_admin' }
    ];
}

// 扩展AdminAuthSystem，添加UI相关方法
AdminAuthSystem.showRejectDialog = showRejectDialog;
AdminAuthSystem.showRequestDetails = showRequestDetails;