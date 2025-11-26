/**
 * 用户管理系统 - JavaScript模块
 * 处理用户管理、权限验证和审批流程等功能
 */

// 用户管理模块
const UserManagement = {
    // 初始化函数
    init: function() {
        console.log('用户管理系统初始化中...');
        
        // 检查权限
        if (!AuthManager.checkPermission('user.manage')) {
            NotificationManager.showError('权限不足', '您没有足够的权限访问用户管理功能');
            return;
        }
        
        // 初始化UI
        this.initUI();
        
        // 初始化事件监听
        this.initEventListeners();
        
        // 加载用户数据
        this.loadUsers();
        
        // 加载待审批的密码修改
        this.loadPasswordApprovals();
        
        // 记录访问日志
        Logging.logAction('用户管理界面访问', { action: 'view', target: 'user_management' });
    },
    
    // 初始化UI
    initUI: function() {
        // 初始化模态框
        this.initModals();
        
        // 初始化分页控件
        this.initPagination();
        
        // 加载当前用户信息
        this.loadCurrentUserInfo();
    },
    
    // 初始化事件监听
    initEventListeners: function() {
        // 搜索框事件
        document.getElementById('user-search').addEventListener('input', this.handleSearch.bind(this));
        
        // 筛选器事件
        document.getElementById('role-filter').addEventListener('change', this.handleFilterChange.bind(this));
        document.getElementById('status-filter').addEventListener('change', this.handleFilterChange.bind(this));
        
        // 添加用户按钮
        document.getElementById('add-user-btn').addEventListener('click', this.openAddUserModal.bind(this));
        
        // 批量操作按钮
        document.getElementById('batch-delete-btn').addEventListener('click', this.handleBatchDelete.bind(this));
        document.getElementById('batch-export-btn').addEventListener('click', this.handleBatchExport.bind(this));
        
        // 表单提交事件
        document.getElementById('user-form').addEventListener('submit', this.handleUserFormSubmit.bind(this));
        
        // 密码审批事件
        document.getElementById('approve-all-btn').addEventListener('click', this.handleApproveAll.bind(this));
        
        // 关闭模态框事件
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', this.closeModal.bind(this));
        });
        
        // 模态框背景点击关闭
        document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
            backdrop.addEventListener('click', this.closeModal.bind(this));
        });
    },
    
    // 加载用户数据
    loadUsers: async function() {
        try {
            const tableBody = document.getElementById('users-table-body');
            tableBody.innerHTML = '<tr class="loading-row"><td colspan="10" class="loading-cell"><div class="loading-spinner"></div><p>加载用户数据中...</p></td></tr>';
            
            // 模拟API请求
            // 在实际应用中，这里应该调用真实的API
            const response = await this.simulateAPIRequest('/api/users', 'GET');
            
            if (response.success) {
                this.renderUserTable(response.data);
                this.updateTableStats(response.data.length);
            } else {
                NotificationManager.showError('加载失败', response.message || '无法加载用户数据');
                tableBody.innerHTML = '<tr><td colspan="10" class="loading-cell">加载用户数据失败</td></tr>';
            }
        } catch (error) {
            console.error('加载用户数据出错:', error);
            NotificationManager.showError('加载错误', '加载用户数据时发生错误');
            document.getElementById('users-table-body').innerHTML = '<tr><td colspan="10" class="loading-cell">加载用户数据失败</td></tr>';
        }
    },
    
    // 渲染用户表格
    renderUserTable: function(users) {
        const tableBody = document.getElementById('users-table-body');
        tableBody.innerHTML = '';
        
        if (users.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="10" class="loading-cell">没有找到用户数据</td></tr>';
            return;
        }
        
        users.forEach(user => {
            const row = document.createElement('tr');
            row.setAttribute('data-user-id', user.id);
            row.innerHTML = `
                <td class="select-column">
                    <input type="checkbox" class="user-select" value="${user.id}">
                </td>
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td>${user.email}</td>
                <td>${user.fullName}</td>
                <td>
                    <span class="role-badge ${user.role}">${this.getRoleName(user.role)}</span>
                </td>
                <td>
                    <div class="user-status ${user.status}">
                        <span class="status-indicator-dot"></span>
                        ${this.getStatusName(user.status)}
                    </div>
                </td>
                <td>${new Date(user.lastLogin).toLocaleString()}</td>
                <td>${new Date(user.createdAt).toLocaleString()}</td>
                <td>
                    <div class="table-actions">
                        <button class="action-btn view" data-user-id="${user.id}" title="查看详情">查看</button>
                        <button class="action-btn edit" data-user-id="${user.id}" title="编辑用户">编辑</button>
                        <button class="action-btn ${user.status === 'active' ? 'lock' : 'unlock'}" data-user-id="${user.id}" title="${user.status === 'active' ? '锁定用户' : '解锁用户'}">
                            ${user.status === 'active' ? '锁定' : '解锁'}
                        </button>
                        <button class="action-btn delete" data-user-id="${user.id}" title="删除用户">删除</button>
                    </div>
                </td>
            `;
            
            tableBody.appendChild(row);
        });
        
        // 添加行操作事件
        this.addRowActionEvents();
    },
    
    // 添加行操作事件
    addRowActionEvents: function() {
        // 查看详情
        document.querySelectorAll('.action-btn.view').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const userId = e.currentTarget.getAttribute('data-user-id');
                this.viewUserDetails(userId);
            });
        });
        
        // 编辑用户
        document.querySelectorAll('.action-btn.edit').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const userId = e.currentTarget.getAttribute('data-user-id');
                this.editUser(userId);
            });
        });
        
        // 锁定/解锁用户
        document.querySelectorAll('.action-btn.lock, .action-btn.unlock').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const userId = e.currentTarget.getAttribute('data-user-id');
                const action = e.currentTarget.textContent.trim();
                this.toggleUserStatus(userId, action);
            });
        });
        
        // 删除用户
        document.querySelectorAll('.action-btn.delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const userId = e.currentTarget.getAttribute('data-user-id');
                this.deleteUser(userId);
            });
        });
        
        // 全选复选框
        document.getElementById('select-all').addEventListener('change', (e) => {
            const checked = e.target.checked;
            document.querySelectorAll('.user-select').forEach(checkbox => {
                checkbox.checked = checked;
            });
        });
    },
    
    // 加载密码审批
    loadPasswordApprovals: async function() {
        try {
            const approvalList = document.getElementById('approval-list');
            approvalList.innerHTML = '<div class="loading-cell"><div class="loading-spinner"></div><p>加载审批数据中...</p></div>';
            
            // 模拟API请求
            const response = await this.simulateAPIRequest('/api/password-approvals', 'GET');
            
            if (response.success) {
                this.renderApprovalList(response.data);
                this.updateApprovalCount(response.data.length);
            } else {
                approvalList.innerHTML = '<div class="no-approvals-message">加载审批数据失败</div>';
            }
        } catch (error) {
            console.error('加载密码审批出错:', error);
            document.getElementById('approval-list').innerHTML = '<div class="no-approvals-message">加载审批数据失败</div>';
        }
    },
    
    // 渲染审批列表
    renderApprovalList: function(approvals) {
        const approvalList = document.getElementById('approval-list');
        
        if (approvals.length === 0) {
            approvalList.innerHTML = '<div class="no-approvals-message">当前没有待审批的密码修改请求</div>';
            return;
        }
        
        approvalList.innerHTML = '';
        
        approvals.forEach(approval => {
            const approvalCard = document.createElement('div');
            approvalCard.className = 'approval-card';
            approvalCard.innerHTML = `
                <div class="approval-header">
                    <div>
                        <h4>用户: ${approval.user.username} (${approval.user.id})</h4>
                        <p>提交时间: ${new Date(approval.submittedAt).toLocaleString()}</p>
                    </div>
                    <div class="approval-actions">
                        <button class="btn btn-success btn-sm" data-approval-id="${approval.id}">批准</button>
                        <button class="btn btn-danger btn-sm" data-approval-id="${approval.id}">拒绝</button>
                        <button class="btn btn-secondary btn-sm" data-approval-id="${approval.id}">详情</button>
                    </div>
                </div>
                <div class="approval-status">
                    <span>状态: 等待审批</span>
                    <span>已批准: ${approval.approvals.length}/${approval.requiredApprovals}</span>
                </div>
            `;
            
            approvalList.appendChild(approvalCard);
        });
        
        // 添加审批操作事件
        this.addApprovalActionEvents();
    },
    
    // 添加审批操作事件
    addApprovalActionEvents: function() {
        // 批准按钮
        document.querySelectorAll('.approval-actions .btn-success').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const approvalId = e.currentTarget.getAttribute('data-approval-id');
                this.approvePasswordChange(approvalId);
            });
        });
        
        // 拒绝按钮
        document.querySelectorAll('.approval-actions .btn-danger').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const approvalId = e.currentTarget.getAttribute('data-approval-id');
                this.rejectPasswordChange(approvalId);
            });
        });
        
        // 详情按钮
        document.querySelectorAll('.approval-actions .btn-secondary').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const approvalId = e.currentTarget.getAttribute('data-approval-id');
                this.viewApprovalDetails(approvalId);
            });
        });
    },
    
    // 打开添加用户模态框
    openAddUserModal: function() {
        this.resetUserForm();
        document.getElementById('modal-title').textContent = '添加新用户';
        this.showModal('user-modal');
    },
    
    // 编辑用户
    editUser: async function(userId) {
        try {
            // 模拟API请求获取用户数据
            const response = await this.simulateAPIRequest(`/api/users/${userId}`, 'GET');
            
            if (response.success) {
                this.fillUserForm(response.data);
                document.getElementById('modal-title').textContent = '编辑用户';
                this.showModal('user-modal');
            } else {
                NotificationManager.showError('操作失败', '无法获取用户数据');
            }
        } catch (error) {
            console.error('编辑用户出错:', error);
            NotificationManager.showError('操作错误', '编辑用户时发生错误');
        }
    },
    
    // 处理用户表单提交
    handleUserFormSubmit: async function(e) {
        e.preventDefault();
        
        const userId = document.getElementById('user-id').value;
        const isEdit = !!userId;
        
        const userData = {
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            fullName: document.getElementById('full-name').value,
            role: document.getElementById('user-role').value,
            status: document.getElementById('user-status').value,
            permissions: this.getSelectedPermissions()
        };
        
        // 如果是新建用户，添加密码
        if (!isEdit) {
            userData.password = document.getElementById('password').value;
            userData.confirmPassword = document.getElementById('confirm-password').value;
            
            // 验证密码
            if (userData.password !== userData.confirmPassword) {
                NotificationManager.showError('验证失败', '两次输入的密码不一致');
                return;
            }
        }
        
        try {
            const endpoint = isEdit ? `/api/users/${userId}` : '/api/users';
            const method = isEdit ? 'PUT' : 'POST';
            
            // 模拟API请求
            const response = await this.simulateAPIRequest(endpoint, method, userData);
            
            if (response.success) {
                NotificationManager.showSuccess('操作成功', isEdit ? '用户更新成功' : '用户创建成功');
                this.closeModal();
                this.loadUsers();
                
                // 记录操作日志
                Logging.logAction(isEdit ? '更新用户' : '创建用户', {
                    action: isEdit ? 'update' : 'create',
                    target: 'user',
                    targetId: userId || response.data.id,
                    details: userData
                });
            } else {
                NotificationManager.showError('操作失败', response.message || (isEdit ? '用户更新失败' : '用户创建失败'));
            }
        } catch (error) {
            console.error('保存用户数据出错:', error);
            NotificationManager.showError('操作错误', '保存用户数据时发生错误');
        }
    },
    
    // 处理密码修改审批
    approvePasswordChange: async function(approvalId) {
        if (!AuthManager.checkPermission('password.approve')) {
            NotificationManager.showError('权限不足', '您没有密码审批权限');
            return;
        }
        
        try {
            // 模拟API请求
            const response = await this.simulateAPIRequest(`/api/password-approvals/${approvalId}/approve`, 'POST', {
                approverId: AuthManager.getCurrentUser().id,
                comments: prompt('请输入审批意见（可选）：') || ''
            });
            
            if (response.success) {
                NotificationManager.showSuccess('审批成功', '密码修改已批准');
                this.loadPasswordApprovals();
                
                // 记录审批日志
                Logging.logAction('批准密码修改', {
                    action: 'approve',
                    target: 'password_approval',
                    targetId: approvalId
                });
            } else {
                NotificationManager.showError('审批失败', response.message || '密码修改批准失败');
            }
        } catch (error) {
            console.error('批准密码修改出错:', error);
            NotificationManager.showError('操作错误', '批准密码修改时发生错误');
        }
    },
    
    // 拒绝密码修改
    rejectPasswordChange: async function(approvalId) {
        if (!AuthManager.checkPermission('password.approve')) {
            NotificationManager.showError('权限不足', '您没有密码审批权限');
            return;
        }
        
        const comments = prompt('请输入拒绝理由：');
        if (comments === null) return;
        
        try {
            // 模拟API请求
            const response = await this.simulateAPIRequest(`/api/password-approvals/${approvalId}/reject`, 'POST', {
                approverId: AuthManager.getCurrentUser().id,
                comments: comments
            });
            
            if (response.success) {
                NotificationManager.showSuccess('操作成功', '密码修改已拒绝');
                this.loadPasswordApprovals();
                
                // 记录拒绝日志
                Logging.logAction('拒绝密码修改', {
                    action: 'reject',
                    target: 'password_approval',
                    targetId: approvalId,
                    comments: comments
                });
            } else {
                NotificationManager.showError('操作失败', response.message || '密码修改拒绝失败');
            }
        } catch (error) {
            console.error('拒绝密码修改出错:', error);
            NotificationManager.showError('操作错误', '拒绝密码修改时发生错误');
        }
    },
    
    // 处理批量删除
    handleBatchDelete: function() {
        const selectedUsers = this.getSelectedUsers();
        
        if (selectedUsers.length === 0) {
            NotificationManager.showWarning('提示', '请先选择要删除的用户');
            return;
        }
        
        if (confirm(`确定要删除选中的 ${selectedUsers.length} 个用户吗？此操作不可恢复！`)) {
            this.batchDeleteUsers(selectedUsers);
        }
    },
    
    // 批量删除用户
    batchDeleteUsers: async function(userIds) {
        try {
            // 模拟API请求
            const response = await this.simulateAPIRequest('/api/users/batch-delete', 'POST', {
                userIds: userIds
            });
            
            if (response.success) {
                NotificationManager.showSuccess('操作成功', `${response.data.deleted} 个用户已成功删除`);
                this.loadUsers();
                
                // 记录批量操作日志
                Logging.logAction('批量删除用户', {
                    action: 'batch_delete',
                    target: 'user',
                    targetIds: userIds
                });
            } else {
                NotificationManager.showError('操作失败', response.message || '批量删除用户失败');
            }
        } catch (error) {
            console.error('批量删除用户出错:', error);
            NotificationManager.showError('操作错误', '批量删除用户时发生错误');
        }
    },
    
    // 辅助函数：获取角色名称
    getRoleName: function(roleKey) {
        const roleMap = {
            'user': '普通用户',
            'password_manager': '密码管理员',
            'admin': '管理员',
            'vikey_admin': 'Vikey管理员'
        };
        return roleMap[roleKey] || roleKey;
    },
    
    // 辅助函数：获取状态名称
    getStatusName: function(statusKey) {
        const statusMap = {
            'active': '活跃',
            'inactive': '禁用',
            'pending': '待激活'
        };
        return statusMap[statusKey] || statusKey;
    },
    
    // 辅助函数：获取选中的用户
    getSelectedUsers: function() {
        const selectedUsers = [];
        document.querySelectorAll('.user-select:checked').forEach(checkbox => {
            selectedUsers.push(checkbox.value);
        });
        return selectedUsers;
    },
    
    // 辅助函数：模拟API请求
    simulateAPIRequest: function(endpoint, method, data = null) {
        return new Promise((resolve) => {
            // 模拟网络延迟
            setTimeout(() => {
                // 根据不同的端点返回模拟数据
                if (endpoint === '/api/users' && method === 'GET') {
                    resolve({
                        success: true,
                        data: this.generateMockUsers(50)
                    });
                } else if (endpoint.startsWith('/api/users/') && method === 'GET') {
                    const userId = endpoint.split('/')[3];
                    resolve({
                        success: true,
                        data: this.generateMockUser(userId)
                    });
                } else if (endpoint === '/api/users' && method === 'POST') {
                    resolve({
                        success: true,
                        data: { ...data, id: Date.now().toString() }
                    });
                } else if (endpoint.startsWith('/api/users/') && endpoint.includes('/batch-delete') === false && method === 'PUT') {
                    resolve({
                        success: true,
                        data: data
                    });
                } else if (endpoint === '/api/users/batch-delete' && method === 'POST') {
                    resolve({
                        success: true,
                        data: { deleted: data.userIds.length }
                    });
                } else if (endpoint === '/api/password-approvals' && method === 'GET') {
                    resolve({
                        success: true,
                        data: this.generateMockApprovals(3)
                    });
                } else if (endpoint.includes('/password-approvals/') && endpoint.includes('/approve')) {
                    resolve({
                        success: true
                    });
                } else if (endpoint.includes('/password-approvals/') && endpoint.includes('/reject')) {
                    resolve({
                        success: true
                    });
                } else {
                    resolve({
                        success: false,
                        message: '未知端点或方法'
                    });
                }
            }, 800);
        });
    },
    
    // 生成模拟用户数据
    generateMockUsers: function(count) {
        const users = [];
        const roles = ['user', 'password_manager', 'admin', 'vikey_admin'];
        const statuses = ['active', 'inactive', 'pending'];
        
        for (let i = 1; i <= count; i++) {
            users.push({
                id: i.toString(),
                username: `user${i}`,
                email: `user${i}@example.com`,
                fullName: `用户 ${i}`,
                role: roles[Math.floor(Math.random() * roles.length)],
                status: statuses[Math.floor(Math.random() * statuses.length)],
                lastLogin: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
                createdAt: new Date(Date.now() - Math.random() * 90 * 24 * 60 * 60 * 1000).toISOString()
            });
        }
        
        return users;
    },
    
    // 生成单个模拟用户
    generateMockUser: function(id) {
        return {
            id: id,
            username: `user${id}`,
            email: `user${id}@example.com`,
            fullName: `用户 ${id}`,
            role: 'admin',
            status: 'active',
            permissions: ['user.view', 'user.manage', 'password.approve'],
            lastLogin: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
            createdAt: new Date(Date.now() - Math.random() * 90 * 24 * 60 * 60 * 1000).toISOString()
        };
    },
    
    // 生成模拟审批数据
    generateMockApprovals: function(count) {
        const approvals = [];
        
        for (let i = 1; i <= count; i++) {
            approvals.push({
                id: i.toString(),
                user: {
                    id: (100 + i).toString(),
                    username: `user${100 + i}`,
                    email: `user${100 + i}@example.com`
                },
                submittedAt: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString(),
                requiredApprovals: 3,
                approvals: [
                    {
                        approverId: '1',
                        approverName: '管理员1',
                        approvedAt: new Date(Date.now() - Math.random() * 12 * 60 * 60 * 1000).toISOString(),
                        comments: '批准'
                    }
                ],
                status: 'pending'
            });
        }
        
        return approvals;
    },
    
    // 其他辅助方法...
    
    // 初始化分页
    initPagination: function() {
        // 简单的分页实现
        const pageSize = 10;
        this.currentPage = 1;
    },
    
    // 初始化模态框
    initModals: function() {
        // 初始化所有模态框
        this.modals = {
            'user-modal': document.getElementById('user-modal'),
            'approval-modal': document.getElementById('approval-modal'),
            'batch-operation-modal': document.getElementById('batch-operation-modal')
        };
    },
    
    // 显示模态框
    showModal: function(modalId) {
        const modal = this.modals[modalId];
        if (modal) {
            modal.style.display = 'flex';
            // 防止背景滚动
            document.body.style.overflow = 'hidden';
        }
    },
    
    // 关闭模态框
    closeModal: function() {
        Object.values(this.modals).forEach(modal => {
            if (modal) {
                modal.style.display = 'none';
            }
        });
        // 恢复背景滚动
        document.body.style.overflow = '';
    },
    
    // 重置用户表单
    resetUserForm: function() {
        document.getElementById('user-form').reset();
        document.getElementById('user-id').value = '';
        document.getElementById('password-section').style.display = 'block';
        this.resetPermissionCheckboxes();
    },
    
    // 填充用户表单
    fillUserForm: function(userData) {
        document.getElementById('user-id').value = userData.id || '';
        document.getElementById('username').value = userData.username || '';
        document.getElementById('email').value = userData.email || '';
        document.getElementById('full-name').value = userData.fullName || '';
        document.getElementById('user-role').value = userData.role || 'user';
        document.getElementById('user-status').value = userData.status || 'active';
        
        // 隐藏密码字段
        document.getElementById('password-section').style.display = 'none';
        
        // 设置权限
        this.setPermissionCheckboxes(userData.permissions || []);
    },
    
    // 重置权限复选框
    resetPermissionCheckboxes: function() {
        document.querySelectorAll('input[name="permissions"]').forEach(checkbox => {
            checkbox.checked = false;
        });
    },
    
    // 设置权限复选框
    setPermissionCheckboxes: function(permissions) {
        this.resetPermissionCheckboxes();
        permissions.forEach(permission => {
            const checkbox = document.querySelector(`input[name="permissions"][value="${permission}"]`);
            if (checkbox) {
                checkbox.checked = true;
            }
        });
    },
    
    // 获取选中的权限
    getSelectedPermissions: function() {
        const permissions = [];
        document.querySelectorAll('input[name="permissions"]:checked').forEach(checkbox => {
            permissions.push(checkbox.value);
        });
        return permissions;
    },
    
    // 加载当前用户信息
    loadCurrentUserInfo: function() {
        const currentUser = AuthManager.getCurrentUser();
        if (currentUser) {
            document.getElementById('current-username').textContent = currentUser.username;
            document.getElementById('current-role').textContent = this.getRoleName(currentUser.role);
        }
    },
    
    // 更新表格统计信息
    updateTableStats: function(totalUsers) {
        document.getElementById('total-users').textContent = totalUsers;
    },
    
    // 更新审批计数
    updateApprovalCount: function(count) {
        document.getElementById('approval-count').textContent = count;
    },
    
    // 处理搜索
    handleSearch: function() {
        const searchTerm = document.getElementById('user-search').value.toLowerCase();
        // 实现搜索逻辑
        this.filterUsers({ searchTerm: searchTerm });
    },
    
    // 处理筛选器变化
    handleFilterChange: function() {
        const roleFilter = document.getElementById('role-filter').value;
        const statusFilter = document.getElementById('status-filter').value;
        // 实现筛选逻辑
        this.filterUsers({ role: roleFilter, status: statusFilter });
    },
    
    // 筛选用户
    filterUsers: function(filters) {
        // 在实际应用中，这里应该调用API进行筛选
        // 这里简单模拟筛选功能
        this.loadUsers();
    },
    
    // 切换用户状态
    toggleUserStatus: async function(userId, action) {
        try {
            const newStatus = action === '锁定' ? 'inactive' : 'active';
            
            // 模拟API请求
            const response = await this.simulateAPIRequest(`/api/users/${userId}/status`, 'PUT', {
                status: newStatus
            });
            
            if (response.success) {
                NotificationManager.showSuccess('操作成功', `用户已${action}`);
                this.loadUsers();
                
                // 记录状态变更日志
                Logging.logAction(`用户${action}`, {
                    action: action === '锁定' ? 'lock' : 'unlock',
                    target: 'user',
                    targetId: userId
                });
            } else {
                NotificationManager.showError('操作失败', `用户${action}失败`);
            }
        } catch (error) {
            console.error(`${action}用户出错:`, error);
            NotificationManager.showError('操作错误', `${action}用户时发生错误`);
        }
    },
    
    // 删除用户
    deleteUser: async function(userId) {
        if (!confirm('确定要删除此用户吗？此操作不可恢复！')) {
            return;
        }
        
        try {
            // 模拟API请求
            const response = await this.simulateAPIRequest(`/api/users/${userId}`, 'DELETE');
            
            if (response.success) {
                NotificationManager.showSuccess('操作成功', '用户已成功删除');
                this.loadUsers();
                
                // 记录删除日志
                Logging.logAction('删除用户', {
                    action: 'delete',
                    target: 'user',
                    targetId: userId
                });
            } else {
                NotificationManager.showError('操作失败', '用户删除失败');
            }
        } catch (error) {
            console.error('删除用户出错:', error);
            NotificationManager.showError('操作错误', '删除用户时发生错误');
        }
    },
    
    // 查看用户详情
    viewUserDetails: async function(userId) {
        try {
            // 模拟API请求获取用户数据
            const response = await this.simulateAPIRequest(`/api/users/${userId}`, 'GET');
            
            if (response.success) {
                this.fillUserDetails(response.data);
                this.showModal('user-details-modal');
            } else {
                NotificationManager.showError('操作失败', '无法获取用户详情');
            }
        } catch (error) {
            console.error('查看用户详情出错:', error);
            NotificationManager.showError('操作错误', '查看用户详情时发生错误');
        }
    },
    
    // 查看审批详情
    viewApprovalDetails: async function(approvalId) {
        try {
            // 模拟API请求获取审批数据
            const response = await this.simulateAPIRequest(`/api/password-approvals/${approvalId}`, 'GET');
            
            if (response.success) {
                this.fillApprovalDetails(response.data);
                this.showModal('approval-modal');
            } else {
                NotificationManager.showError('操作失败', '无法获取审批详情');
            }
        } catch (error) {
            console.error('查看审批详情出错:', error);
            NotificationManager.showError('操作错误', '查看审批详情时发生错误');
        }
    },
    
    // 处理全部审批
    handleApproveAll: function() {
        if (!AuthManager.checkPermission('password.approve')) {
            NotificationManager.showError('权限不足', '您没有密码审批权限');
            return;
        }
        
        if (confirm('确定要批准所有待审批的密码修改请求吗？')) {
            this.approveAllPasswordChanges();
        }
    },
    
    // 批准所有密码修改
    approveAllPasswordChanges: async function() {
        try {
            // 模拟API请求
            const response = await this.simulateAPIRequest('/api/password-approvals/approve-all', 'POST', {
                approverId: AuthManager.getCurrentUser().id
            });
            
            if (response.success) {
                NotificationManager.showSuccess('操作成功', `${response.data.approved} 个密码修改已批准`);
                this.loadPasswordApprovals();
            } else {
                NotificationManager.showError('操作失败', '批量批准密码修改失败');
            }
        } catch (error) {
            console.error('批量批准密码修改出错:', error);
            NotificationManager.showError('操作错误', '批量批准密码修改时发生错误');
        }
    },
    
    // 处理批量导出
    handleBatchExport: function() {
        const selectedUsers = this.getSelectedUsers();
        
        if (selectedUsers.length === 0) {
            // 导出全部用户
            this.exportUsers('all');
        } else {
            // 导出选中的用户
            this.exportUsers('selected', selectedUsers);
        }
    },
    
    // 导出用户数据
    exportUsers: async function(type, userIds = []) {
        try {
            // 模拟API请求
            const response = await this.simulateAPIRequest('/api/users/export', 'POST', {
                type: type,
                userIds: userIds,
                format: 'csv'
            });
            
            if (response.success) {
                NotificationManager.showSuccess('导出成功', '用户数据已成功导出');
                // 在实际应用中，这里应该处理文件下载
            } else {
                NotificationManager.showError('导出失败', '用户数据导出失败');
            }
        } catch (error) {
            console.error('导出用户数据出错:', error);
            NotificationManager.showError('导出错误', '导出用户数据时发生错误');
        }
    }
};

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', function() {
    UserManagement.init();
});

// 暴露模块到全局（如果需要）
window.UserManagement = UserManagement;