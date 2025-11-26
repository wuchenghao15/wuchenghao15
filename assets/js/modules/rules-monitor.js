/**
 * 系统规则监测与管理模块
 * 功能：监测系统规则运行状态，支持管理员进行规则管理、自动修复等操作
 */

// 全局变量
const appState = {
    currentUser: null,
    userPermissions: [],
    isMonitoring: false,
    systemRules: [],
    monitoringStartTime: null,
    activeTab: 'rules-overview',
    deepseekConnected: false,
    autoRepairEnabled: true,
    deepseekRepairEnabled: true,
    requireApprovalForRepair: true,
    grayTestingEnabled: false
};

// 模拟规则数据
const mockRules = [
    {
        id: 'RULE-001',
        name: '前端页面资源外联规则',
        type: 'system',
        status: 'active',
        priority: 'high',
        description: '所有新建页面包括动态页面和静态页面都必须外联javascript和stylesheet',
        conditions: '检查HTML文件是否直接包含<script>或<style>标签内容',
        actions: '标记违规页面，生成修复建议',
        lastCheckTime: new Date().toISOString(),
        createdTime: '2024-01-01T00:00:00Z',
        createdBy: 'SYSTEM',
        lastModifiedTime: new Date().toISOString(),
        lastModifiedBy: 'admin'
    },
    {
        id: 'RULE-002',
        name: '管理员权限验证规则',
        type: 'security',
        status: 'active',
        priority: 'critical',
        description: '只有管理员用户和Vikey管理员用户才能查看和修改系统规则',
        conditions: '检查用户权限级别',
        actions: '拒绝低权限用户访问，记录访问日志',
        lastCheckTime: new Date().toISOString(),
        createdTime: '2024-01-01T00:00:00Z',
        createdBy: 'SYSTEM',
        lastModifiedTime: new Date().toISOString(),
        lastModifiedBy: 'admin'
    },
    {
        id: 'RULE-003',
        name: '自动修复规则',
        type: 'system',
        status: 'warning',
        priority: 'medium',
        description: '规则或机制一旦在系统能异常或失效不许可以通过脚本或者是DeepSeek模型自我修复并重启',
        conditions: '监控规则执行状态，检测异常',
        actions: '调用修复脚本或DeepSeek模型进行修复',
        lastCheckTime: new Date().toISOString(),
        createdTime: '2024-01-01T00:00:00Z',
        createdBy: 'SYSTEM',
        lastModifiedTime: new Date().toISOString(),
        lastModifiedBy: 'admin'
    },
    {
        id: 'RULE-004',
        name: '灰度测试规则',
        type: 'system',
        status: 'active',
        priority: 'medium',
        description: '所有配置都必须配置灰度测试环境测试，才能应用到系统',
        conditions: '检查配置变更是否经过灰度测试',
        actions: '阻止未经过灰度测试的配置直接应用到生产环境',
        lastCheckTime: new Date().toISOString(),
        createdTime: '2024-01-01T00:00:00Z',
        createdBy: 'SYSTEM',
        lastModifiedTime: new Date().toISOString(),
        lastModifiedBy: 'admin'
    },
    {
        id: 'RULE-005',
        name: '操作日志记录规则',
        type: 'security',
        status: 'error',
        priority: 'high',
        description: '所有操作和拐点必须记录到日志',
        conditions: '监控系统关键操作',
        actions: '记录操作日志，包括操作人、时间、操作内容等',
        lastCheckTime: new Date().toISOString(),
        createdTime: '2024-01-01T00:00:00Z',
        createdBy: 'SYSTEM',
        lastModifiedTime: new Date().toISOString(),
        lastModifiedBy: 'admin'
    }
];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // 初始化应用状态
        appState.systemRules = [...mockRules];
        appState.monitoringStartTime = new Date();
        
        // 初始化UI
        initializeUI();
        
        // 检查用户权限
        await checkUserPermissions();
        
        // 加载规则数据
        loadRulesData();
        
        // 启动系统监控
        startSystemMonitoring();
        
        // 设置时间更新间隔
        setInterval(updateDateTimeDisplay, 1000);
        
    } catch (error) {
        console.error('初始化错误:', error);
        addNotification('初始化失败，请刷新页面重试', 'error');
        logOperation('初始化失败', 'SYSTEM', 'error');
    }
});

/**
 * 初始化用户界面
 */
function initializeUI() {
    // 设置选项卡切换事件
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabId = item.getAttribute('data-tab');
            switchTab(tabId);
        });
    });
    
    // 更新日期时间显示
    updateDateTimeDisplay();
    
    // 初始化设置开关状态
    document.getElementById('enable-auto-repair').checked = appState.autoRepairEnabled;
    document.getElementById('enable-deepseek-repair').checked = appState.deepseekRepairEnabled;
    document.getElementById('require-approval').checked = appState.requireApprovalForRepair;
    
    // 设置状态指示器初始状态
    updateSystemStatusIndicator('normal');
}

/**
 * 检查用户权限
 */
async function checkUserPermissions() {
    try {
        // 模拟用户登录（实际应用中应该调用认证API）
        const mockUser = {
            username: 'admin',
            role: 'administrator',
            permissions: ['view_rules', 'edit_rules', 'manage_system', 'repair_system']
        };
        
        // 模拟延迟
        await new Promise(resolve => setTimeout(resolve, 500));
        
        appState.currentUser = mockUser;
        appState.userPermissions = mockUser.permissions;
        
        // 更新用户信息显示
        updateUserInfoDisplay();
        
        // 检查权限并控制UI访问
        controlUIByPermissions();
        
        addNotification(`欢迎回来，${mockUser.username}`, 'success');
        logOperation('用户登录成功', mockUser.username, 'info');
        
    } catch (error) {
        console.error('权限检查失败:', error);
        addNotification('权限验证失败，请重新登录', 'error');
        
        // 限制UI访问
        restrictUIAccess();
    }
}

/**
 * 更新用户信息显示
 */
function updateUserInfoDisplay() {
    if (appState.currentUser) {
        document.getElementById('current-user').textContent = appState.currentUser.username;
        
        const permissionBadge = document.getElementById('permission-level');
        let roleName = '访客';
        
        switch (appState.currentUser.role) {
            case 'vikey_admin':
                roleName = 'Vikey管理员';
                permissionBadge.style.backgroundColor = '#667eea';
                break;
            case 'administrator':
                roleName = '管理员';
                permissionBadge.style.backgroundColor = '#4CAF50';
                break;
            case 'password_admin':
                roleName = '密码管理员';
                permissionBadge.style.backgroundColor = '#ff9800';
                break;
            case 'user':
                roleName = '普通用户';
                permissionBadge.style.backgroundColor = '#9e9e9e';
                break;
        }
        
        permissionBadge.textContent = roleName;
    }
}

/**
 * 根据权限控制UI访问
 */
function controlUIByPermissions() {
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    // 隐藏权限提示（如果有权限）
    const permissionAlert = document.getElementById('permission-alert');
    if (isAdminOrVikeyAdmin) {
        permissionAlert.classList.add('hidden');
    }
    
    // 禁用编辑功能（如果没有权限）
    const editButtons = document.querySelectorAll('.btn.primary, .btn.danger');
    editButtons.forEach(button => {
        if (!isAdminOrVikeyAdmin) {
            button.disabled = true;
            button.title = '需要管理员权限';
        }
    });
    
    // 禁用表单输入（如果没有权限）
    const formInputs = document.querySelectorAll('.rule-editor input, .rule-editor textarea, .rule-editor select');
    formInputs.forEach(input => {
        if (!isAdminOrVikeyAdmin) {
            input.disabled = true;
        }
    });
}

/**
 * 限制UI访问（权限不足时）
 */
function restrictUIAccess() {
    // 显示权限提示
    const permissionAlert = document.getElementById('permission-alert');
    permissionAlert.classList.remove('hidden');
    
    // 禁用所有编辑按钮
    const allButtons = document.querySelectorAll('button');
    allButtons.forEach(button => {
        button.disabled = true;
    });
    
    // 禁用表单输入
    const formInputs = document.querySelectorAll('input, textarea, select');
    formInputs.forEach(input => {
        input.disabled = true;
    });
    
    // 设置只读模式提示
    const readOnlyOverlay = document.createElement('div');
    readOnlyOverlay.style.position = 'fixed';
    readOnlyOverlay.style.top = '0';
    readOnlyOverlay.style.left = '0';
    readOnlyOverlay.style.width = '100%';
    readOnlyOverlay.style.height = '100%';
    readOnlyOverlay.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
    readOnlyOverlay.style.display = 'flex';
    readOnlyOverlay.style.justifyContent = 'center';
    readOnlyOverlay.style.alignItems = 'center';
    readOnlyOverlay.style.zIndex = '9999';
    readOnlyOverlay.style.fontSize = '18px';
    readOnlyOverlay.style.color = '#666';
    readOnlyOverlay.textContent = '您没有足够的权限访问此页面';
    
    // document.body.appendChild(readOnlyOverlay);
}

/**
 * 加载规则数据
 */
function loadRulesData() {
    // 更新规则列表
    updateRulesList();
    
    // 更新统计数据
    updateRulesStatistics();
}

/**
 * 更新规则列表显示
 */
function updateRulesList() {
    const rulesListBody = document.getElementById('rules-list');
    rulesListBody.innerHTML = '';
    
    appState.systemRules.forEach(rule => {
        const row = document.createElement('tr');
        
        // 状态样式类
        let statusClass = '';
        let statusText = '';
        
        switch (rule.status) {
            case 'active':
                statusClass = 'status-active';
                statusText = '活跃';
                break;
            case 'warning':
                statusClass = 'status-warning';
                statusText = '警告';
                break;
            case 'error':
                statusClass = 'status-error';
                statusText = '错误';
                break;
            case 'inactive':
                statusClass = 'status-inactive';
                statusText = '未激活';
                break;
        }
        
        // 优先级样式类
        let priorityClass = '';
        let priorityText = '';
        
        switch (rule.priority) {
            case 'low':
                priorityClass = 'priority-low';
                priorityText = '低';
                break;
            case 'medium':
                priorityClass = 'priority-medium';
                priorityText = '中';
                break;
            case 'high':
                priorityClass = 'priority-high';
                priorityText = '高';
                break;
            case 'critical':
                priorityClass = 'priority-critical';
                priorityText = '关键';
                break;
        }
        
        row.innerHTML = `
            <td>${rule.id}</td>
            <td>${rule.name}</td>
            <td>${rule.type}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td><span class="priority-badge ${priorityClass}">${priorityText}</span></td>
            <td>${new Date(rule.lastCheckTime).toLocaleString()}</td>
            <td>
                <button class="btn small secondary" onclick="viewRuleDetails('${rule.id}')">查看</button>
                <button class="btn small primary" onclick="editRule('${rule.id}')">编辑</button>
                <button class="btn small danger" onclick="deleteRule('${rule.id}')">删除</button>
            </td>
        `;
        
        rulesListBody.appendChild(row);
    });
}

/**
 * 更新规则统计数据
 */
function updateRulesStatistics() {
    const totalRules = appState.systemRules.length;
    const activeRules = appState.systemRules.filter(r => r.status === 'active').length;
    const warningRules = appState.systemRules.filter(r => r.status === 'warning').length;
    const errorRules = appState.systemRules.filter(r => r.status === 'error').length;
    
    document.getElementById('total-rules').textContent = totalRules;
    document.getElementById('active-rules').textContent = activeRules;
    document.getElementById('warning-rules').textContent = warningRules;
    document.getElementById('error-rules').textContent = errorRules;
    
    // 根据错误规则数量更新系统状态指示器
    if (errorRules > 0) {
        updateSystemStatusIndicator('error');
    } else if (warningRules > 0) {
        updateSystemStatusIndicator('warning');
    } else {
        updateSystemStatusIndicator('normal');
    }
}

/**
 * 更新系统状态指示器
 */
function updateSystemStatusIndicator(status) {
    const indicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    
    // 移除所有状态类
    indicator.className = 'status-indicator';
    
    switch (status) {
        case 'normal':
            indicator.classList.add('status-normal');
            statusText.textContent = '系统状态: 正常';
            break;
        case 'warning':
            indicator.classList.add('status-warning');
            statusText.textContent = '系统状态: 警告';
            break;
        case 'error':
            indicator.classList.add('status-error');
            statusText.textContent = '系统状态: 错误';
            break;
        case 'maintenance':
            indicator.classList.add('status-maintenance');
            statusText.textContent = '系统状态: 维护中';
            break;
    }
}

/**
 * 切换选项卡
 */
function switchTab(tabId) {
    // 隐藏所有内容面板
    const allTabs = document.querySelectorAll('.tab-content');
    allTabs.forEach(tab => tab.classList.remove('active'));
    
    // 移除所有导航项的激活状态
    const allNavItems = document.querySelectorAll('.nav-item');
    allNavItems.forEach(item => item.classList.remove('active'));
    
    // 显示选中的内容面板
    const selectedTab = document.getElementById(tabId);
    selectedTab.classList.add('active');
    
    // 设置导航项为激活状态
    const selectedNavItem = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
    selectedNavItem.classList.add('active');
    
    // 更新当前激活的选项卡
    appState.activeTab = tabId;
    
    // 记录操作日志
    if (appState.currentUser) {
        logOperation(`切换到${selectedNavItem.textContent}选项卡`, appState.currentUser.username, 'info');
    }
    
    // 特定选项卡初始化
    switch (tabId) {
        case 'history':
            loadHistoryData();
            break;
        case 'backup':
            loadBackupsList();
            break;
        case 'deepseek':
            updateDeepSeekStatus();
            break;
    }
}

/**
 * 更新日期时间显示
 */
function updateDateTimeDisplay() {
    // 更新当前时间
    const now = new Date();
    const timeString = now.toLocaleTimeString('zh-CN');
    document.getElementById('current-time').textContent = timeString;
    
    // 更新运行时长
    if (appState.monitoringStartTime) {
        const uptimeMs = now - appState.monitoringStartTime;
        const hours = Math.floor(uptimeMs / 3600000);
        const minutes = Math.floor((uptimeMs % 3600000) / 60000);
        const seconds = Math.floor((uptimeMs % 60000) / 1000);
        
        const uptimeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        document.getElementById('uptime').textContent = uptimeString;
    }
}

/**
 * 开始系统监控
 */
function startSystemMonitoring() {
    appState.isMonitoring = true;
    
    // 定期检查规则状态
    setInterval(checkRulesStatus, 30000); // 每30秒检查一次
    
    addNotification('系统监控已启动', 'info');
    logOperation('系统监控启动', 'SYSTEM', 'info');
}

/**
 * 检查规则状态
 */
function checkRulesStatus() {
    // 模拟规则状态检查
    appState.systemRules.forEach(rule => {
        // 随机更新规则状态（实际应用中应该有真实的检查逻辑）
        const rand = Math.random();
        if (rand > 0.95) {
            rule.status = 'error';
            rule.lastCheckTime = new Date().toISOString();
            addNotification(`规则 ${rule.name} 检测到错误`, 'error');
            
            // 自动修复
            if (appState.autoRepairEnabled) {
                triggerAutoRepair(rule.id);
            }
        } else if (rand > 0.85) {
            rule.status = 'warning';
            rule.lastCheckTime = new Date().toISOString();
            addNotification(`规则 ${rule.name} 检测到警告`, 'warning');
        } else {
            rule.status = 'active';
            rule.lastCheckTime = new Date().toISOString();
        }
    });
    
    // 更新UI
    updateRulesList();
    updateRulesStatistics();
}

/**
 * 触发自动修复
 */
async function triggerAutoRepair(ruleId) {
    try {
        const rule = appState.systemRules.find(r => r.id === ruleId);
        if (!rule) return;
        
        addNotification(`开始修复规则: ${rule.name}`, 'info');
        logOperation(`开始修复规则: ${ruleId}`, 'SYSTEM', 'info');
        
        // 模拟修复过程
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 检查是否需要批准
        if (appState.requireApprovalForRepair) {
            // 这里应该显示批准对话框
            // 模拟自动批准
            addNotification(`规则 ${rule.name} 修复需要管理员批准`, 'warning');
            
            // 模拟管理员批准
            setTimeout(() => {
                completeAutoRepair(ruleId);
            }, 3000);
        } else {
            completeAutoRepair(ruleId);
        }
        
    } catch (error) {
        console.error('自动修复失败:', error);
        addNotification(`规则修复失败: ${error.message}`, 'error');
        logOperation(`规则修复失败: ${ruleId}`, 'SYSTEM', 'error');
    }
}

/**
 * 完成自动修复
 */
async function completeAutoRepair(ruleId) {
    try {
        const rule = appState.systemRules.find(r => r.id === ruleId);
        if (!rule) return;
        
        // 检查是否使用DeepSeek修复
        if (appState.deepseekRepairEnabled && appState.deepseekConnected) {
            // 调用DeepSeek API进行智能修复
            await useDeepSeekForRepair(ruleId);
        } else {
            // 使用标准修复方法
            rule.status = 'active';
            rule.lastModifiedTime = new Date().toISOString();
            rule.lastModifiedBy = 'AUTO_REPAIR';
        }
        
        addNotification(`规则 ${rule.name} 修复成功`, 'success');
        logOperation(`规则修复成功: ${ruleId}`, 'SYSTEM', 'success');
        
        // 更新UI
        updateRulesList();
        updateRulesStatistics();
        
    } catch (error) {
        console.error('完成自动修复失败:', error);
        addNotification(`规则修复完成失败: ${error.message}`, 'error');
    }
}

/**
 * 使用DeepSeek进行智能修复
 */
async function useDeepSeekForRepair(ruleId) {
    try {
        // 模拟DeepSeek API调用
        console.log(`使用DeepSeek模型修复规则: ${ruleId}`);
        
        // 模拟延迟
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        return true;
        
    } catch (error) {
        console.error('DeepSeek修复失败:', error);
        throw error;
    }
}

/**
 * 添加通知
 */
function addNotification(message, type = 'info', duration = 5000) {
    const notificationsContainer = document.getElementById('notifications-container');
    
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // 设置通知内容
    notification.innerHTML = `
        <div class="notification-header">
            <span class="notification-title">
                ${type === 'success' ? '成功' : 
                  type === 'error' ? '错误' : 
                  type === 'warning' ? '警告' : '信息'}
            </span>
            <button class="notification-close" onclick="this.closest('.notification').remove()">×</button>
        </div>
        <div class="notification-message">${message}</div>
    `;
    
    // 添加到容器
    notificationsContainer.appendChild(notification);
    
    // 自动关闭
    setTimeout(() => {
        if (notification.parentNode === notificationsContainer) {
            notificationsContainer.removeChild(notification);
        }
    }, duration);
}

/**
 * 记录操作日志
 */
function logOperation(action, user, type = 'info') {
    const logContent = document.getElementById('operations-log-content');
    const now = new Date();
    const timeString = now.toLocaleTimeString('zh-CN');
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.innerHTML = `
        <span class="log-time">[${timeString}]</span>
        <span class="log-action">${action}</span>
        <span class="log-user">by ${user}</span>
    `;
    
    // 添加到日志内容的开头
    if (logContent.firstChild) {
        logContent.insertBefore(logEntry, logContent.firstChild);
    } else {
        logContent.appendChild(logEntry);
    }
    
    // 限制日志条目数量
    if (logContent.children.length > 50) {
        logContent.removeChild(logContent.lastChild);
    }
    
    // 实际应用中应该发送到服务器保存
    console.log(`[${timeString}] ${type.toUpperCase()} - ${action} by ${user}`);
}

/**
 * 清空日志
 */
function clearLogs() {
    const logContent = document.getElementById('operations-log-content');
    logContent.innerHTML = '';
    
    addNotification('操作日志已清空', 'info');
    if (appState.currentUser) {
        logOperation('清空操作日志', appState.currentUser.username, 'info');
    }
}

/**
 * 查看规则详情
 */
function viewRuleDetails(ruleId) {
    const rule = appState.systemRules.find(r => r.id === ruleId);
    if (!rule) return;
    
    // 切换到规则详情选项卡
    switchTab('rule-details');
    
    // 填充表单
    document.getElementById('rule-id-input').value = rule.id;
    document.getElementById('rule-name-input').value = rule.name;
    document.getElementById('rule-type-select').value = rule.type;
    document.getElementById('rule-description').value = rule.description;
    document.getElementById('rule-priority').value = rule.priority;
    document.getElementById('rule-conditions').value = rule.conditions;
    document.getElementById('rule-actions').value = rule.actions;
    
    // 更新状态标签
    const statusBadge = document.getElementById('editor-rule-status');
    statusBadge.textContent = rule.status;
    statusBadge.className = 'rule-status-badge';
    
    switch (rule.status) {
        case 'active':
            statusBadge.classList.add('status-active');
            break;
        case 'warning':
            statusBadge.classList.add('status-warning');
            break;
        case 'error':
            statusBadge.classList.add('status-error');
            break;
    }
    
    addNotification(`查看规则详情: ${rule.name}`, 'info');
    if (appState.currentUser) {
        logOperation(`查看规则详情: ${ruleId}`, appState.currentUser.username, 'info');
    }
}

/**
 * 编辑规则
 */
function editRule(ruleId) {
    viewRuleDetails(ruleId);
    
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限编辑规则', 'error');
        return;
    }
    
    addNotification(`开始编辑规则: ${ruleId}`, 'info');
    if (appState.currentUser) {
        logOperation(`编辑规则: ${ruleId}`, appState.currentUser.username, 'info');
    }
}

/**
 * 删除规则
 */
function deleteRule(ruleId) {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限删除规则', 'error');
        return;
    }
    
    if (confirm('确定要删除这条规则吗？此操作不可撤销。')) {
        const ruleIndex = appState.systemRules.findIndex(r => r.id === ruleId);
        if (ruleIndex !== -1) {
            const ruleName = appState.systemRules[ruleIndex].name;
            appState.systemRules.splice(ruleIndex, 1);
            
            // 更新UI
            updateRulesList();
            updateRulesStatistics();
            
            addNotification(`规则 ${ruleName} 已删除`, 'success');
            if (appState.currentUser) {
                logOperation(`删除规则: ${ruleId}`, appState.currentUser.username, 'info');
            }
        }
    }
}

/**
 * 创建新规则
 */
function createNewRule() {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限创建规则', 'error');
        return;
    }
    
    // 切换到规则详情选项卡
    switchTab('rule-details');
    
    // 重置表单
    resetEditor();
    
    // 生成新规则ID
    const newId = `RULE-${(appState.systemRules.length + 1).toString().padStart(3, '0')}`;
    document.getElementById('rule-id-input').value = newId;
    
    addNotification('创建新规则', 'info');
    if (appState.currentUser) {
        logOperation('创建新规则', appState.currentUser.username, 'info');
    }
}

/**
 * 重置编辑器
 */
function resetEditor() {
    document.getElementById('rule-id-input').value = '';
    document.getElementById('rule-name-input').value = '';
    document.getElementById('rule-type-select').value = 'system';
    document.getElementById('rule-description').value = '';
    document.getElementById('rule-priority').value = 'medium';
    document.getElementById('rule-conditions').value = '';
    document.getElementById('rule-actions').value = '';
    
    const statusBadge = document.getElementById('editor-rule-status');
    statusBadge.textContent = '未保存';
    statusBadge.className = 'rule-status-badge';
}

/**
 * 保存规则更改
 */
function saveRuleChanges() {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限保存规则', 'error');
        return;
    }
    
    // 获取表单数据
    const ruleId = document.getElementById('rule-id-input').value;
    const ruleName = document.getElementById('rule-name-input').value;
    const ruleType = document.getElementById('rule-type-select').value;
    const ruleDescription = document.getElementById('rule-description').value;
    const rulePriority = document.getElementById('rule-priority').value;
    const ruleConditions = document.getElementById('rule-conditions').value;
    const ruleActions = document.getElementById('rule-actions').value;
    
    // 验证必填字段
    if (!ruleName || !ruleDescription || !ruleConditions || !ruleActions) {
        addNotification('请填写所有必填字段', 'error');
        return;
    }
    
    // 检查是新增还是更新
    const existingRuleIndex = appState.systemRules.findIndex(r => r.id === ruleId);
    const now = new Date().toISOString();
    
    if (existingRuleIndex !== -1) {
        // 更新现有规则
        appState.systemRules[existingRuleIndex] = {
            ...appState.systemRules[existingRuleIndex],
            name: ruleName,
            type: ruleType,
            description: ruleDescription,
            priority: rulePriority,
            conditions: ruleConditions,
            actions: ruleActions,
            lastModifiedTime: now,
            lastModifiedBy: appState.currentUser.username
        };
        
        addNotification(`规则 ${ruleName} 已更新`, 'success');
        logOperation(`更新规则: ${ruleId}`, appState.currentUser.username, 'success');
        
    } else {
        // 创建新规则
        const newRule = {
            id: ruleId,
            name: ruleName,
            type: ruleType,
            status: 'active',
            priority: rulePriority,
            description: ruleDescription,
            conditions: ruleConditions,
            actions: ruleActions,
            lastCheckTime: now,
            createdTime: now,
            createdBy: appState.currentUser.username,
            lastModifiedTime: now,
            lastModifiedBy: appState.currentUser.username
        };
        
        appState.systemRules.push(newRule);
        
        addNotification(`新规则 ${ruleName} 已创建`, 'success');
        logOperation(`创建规则: ${ruleId}`, appState.currentUser.username, 'success');
    }
    
    // 更新UI
    updateRulesList();
    updateRulesStatistics();
}

/**
 * 测试规则
 */
function testRule() {
    // 模拟规则测试
    addNotification('规则测试已启动...', 'info');
    
    setTimeout(() => {
        addNotification('规则测试通过', 'success');
        logOperation('规则测试执行', appState.currentUser?.username || 'SYSTEM', 'info');
    }, 2000);
}

/**
 * 删除选中规则
 */
function deleteSelectedRule() {
    const ruleId = document.getElementById('rule-id-input').value;
    if (ruleId) {
        deleteRule(ruleId);
    } else {
        addNotification('请先选择或创建一条规则', 'error');
    }
}

/**
 * 刷新规则
 */
function refreshRules() {
    addNotification('正在刷新规则...', 'info');
    
    // 模拟刷新过程
    setTimeout(() => {
        checkRulesStatus();
        addNotification('规则已刷新', 'success');
        logOperation('刷新规则列表', appState.currentUser?.username || 'SYSTEM', 'info');
    }, 1000);
}

/**
 * 导出规则
 */
function exportRules() {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限导出规则', 'error');
        return;
    }
    
    // 模拟导出
    addNotification('正在导出规则...', 'info');
    
    setTimeout(() => {
        addNotification('规则导出成功', 'success');
        logOperation('导出规则', appState.currentUser.username, 'info');
    }, 1500);
}

/**
 * 导入规则
 */
function importRules() {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限导入规则', 'error');
        return;
    }
    
    // 模拟文件选择
    addNotification('请选择规则文件进行导入', 'info');
    
    // 实际应用中应该实现文件选择和解析逻辑
    setTimeout(() => {
        addNotification('规则导入成功', 'success');
        logOperation('导入规则', appState.currentUser.username, 'info');
    }, 2000);
}

/**
 * 开始自动修复扫描
 */
function startAutoRepairScan() {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限执行自动修复', 'error');
        return;
    }
    
    addNotification('开始扫描需要修复的规则...', 'info');
    logOperation('开始自动修复扫描', appState.currentUser.username, 'info');
    
    // 模拟扫描过程
    setTimeout(() => {
        // 查找错误和警告的规则
        const rulesToRepair = appState.systemRules.filter(r => r.status === 'error' || r.status === 'warning');
        
        if (rulesToRepair.length > 0) {
            addNotification(`发现 ${rulesToRepair.length} 个需要修复的规则`, 'warning');
            
            // 开始修复
            rulesToRepair.forEach(rule => {
                triggerAutoRepair(rule.id);
            });
        } else {
            addNotification('没有发现需要修复的规则', 'info');
        }
        
    }, 3000);
}

/**
 * 停止自动修复扫描
 */
function stopAutoRepairScan() {
    // 模拟停止扫描
    addNotification('自动修复扫描已停止', 'info');
    logOperation('停止自动修复扫描', appState.currentUser?.username || 'SYSTEM', 'info');
}

/**
 * 部署到灰度环境
 */
function deployToGray() {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限部署到灰度环境', 'error');
        return;
    }
    
    addNotification('正在部署到灰度测试环境...', 'info');
    logOperation('部署到灰度环境', appState.currentUser.username, 'info');
    
    // 模拟部署过程
    setTimeout(() => {
        // 更新灰度环境信息
        document.getElementById('gray-status').textContent = '运行中';
        document.getElementById('gray-version').textContent = '1.0.0';
        document.getElementById('gray-user-percentage').textContent = '10%';
        document.getElementById('gray-deploy-time').textContent = new Date().toLocaleString();
        
        appState.grayTestingEnabled = true;
        
        addNotification('成功部署到灰度测试环境', 'success');
        logOperation('灰度环境部署成功', appState.currentUser.username, 'success');
        
        // 生成测试结果
        generateTestResults();
        
    }, 3000);
}

/**
 * 推广到生产环境
 */
function promoteToProduction() {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限推广到生产环境', 'error');
        return;
    }
    
    // 检查灰度环境是否可用
    if (!appState.grayTestingEnabled) {
        addNotification('请先在灰度环境测试', 'error');
        return;
    }
    
    // 确认对话框
    if (!confirm('确定要将当前版本推广到生产环境吗？请确保灰度测试已通过。')) {
        return;
    }
    
    addNotification('正在推广到生产环境...', 'info');
    logOperation('推广到生产环境', appState.currentUser.username, 'info');
    
    // 模拟推广过程
    setTimeout(() => {
        // 创建备份
        createBackup();
        
        addNotification('成功推广到生产环境', 'success');
        logOperation('生产环境更新成功', appState.currentUser.username, 'success');
        
        // 发送通知给所有相关人员
        sendPromotionNotification();
        
    }, 4000);
}

/**
 * 生成测试结果
 */
function generateTestResults() {
    const testResultsList = document.getElementById('test-results-list');
    testResultsList.innerHTML = '';
    
    const mockResults = [
        { name: '功能测试', result: '通过', details: '所有功能正常运行' },
        { name: '性能测试', result: '通过', details: '响应时间<200ms' },
        { name: '安全测试', result: '通过', details: '未发现安全漏洞' },
        { name: '兼容性测试', result: '通过', details: '兼容主流浏览器' }
    ];
    
    mockResults.forEach(result => {
        const resultItem = document.createElement('div');
        resultItem.className = `test-result ${result.result === '通过' ? 'passed' : 'failed'}`;
        resultItem.innerHTML = `
            <div class="result-header">
                <span class="result-name">${result.name}</span>
                <span class="result-status">${result.result}</span>
            </div>
            <div class="result-details">${result.details}</div>
        `;
        testResultsList.appendChild(resultItem);
    });
}

/**
 * 发送推广通知
 */
function sendPromotionNotification() {
    // 模拟发送通知给所有相关人员
    addNotification('已通知所有相关人员关于生产环境更新', 'info');
    
    // 这里应该实现实际的通知发送逻辑
    console.log('发送通知给所有相关人员和vikey管理员');
}

/**
 * 加载历史数据
 */
function loadHistoryData() {
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '';
    
    // 模拟历史迭代记录
    const mockHistory = [
        {
            version: '1.0.3',
            date: '2024-01-20',
            description: '优化DeepSeek模型集成，提高自动修复成功率',
            by: 'admin'
        },
        {
            version: '1.0.2', 
            date: '2024-01-15',
            description: '添加灰度测试环境，支持配置的安全部署',
            by: 'vikey_admin'
        },
        {
            version: '1.0.1',
            date: '2024-01-10',
            description: '修复操作日志记录问题，完善权限验证机制',
            by: 'admin'
        },
        {
            version: '1.0.0',
            date: '2024-01-01',
            description: '系统规则监测与管理模块正式上线',
            by: 'SYSTEM'
        }
    ];
    
    mockHistory.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.innerHTML = `
            <div class="history-timeline-dot"></div>
            <div class="history-content">
                <div class="history-header">
                    <span class="history-version">${item.version}</span>
                    <span class="history-date">${item.date}</span>
                </div>
                <div class="history-description">${item.description}</div>
                <div class="history-author">by ${item.by}</div>
            </div>
        `;
        historyList.appendChild(historyItem);
    });
}

/**
 * 生成迭代建议
 */
function generateSuggestions() {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限生成迭代建议', 'error');
        return;
    }
    
    addNotification('正在生成迭代建议...', 'info');
    logOperation('生成迭代建议', appState.currentUser.username, 'info');
    
    // 模拟生成建议过程
    setTimeout(() => {
        const suggestionsList = document.getElementById('suggestions-list');
        suggestionsList.innerHTML = '';
        
        const mockSuggestions = [
            {
                title: '增强自动修复能力',
                description: '建议进一步优化DeepSeek模型，使其能够处理更复杂的规则修复场景',
                priority: 'high',
                impact: '提高系统稳定性和维护效率'
            },
            {
                title: '添加规则版本控制系统',
                description: '建议实现规则的版本控制，支持多版本并行和历史版本回滚',
                priority: 'medium',
                impact: '提高规则管理的灵活性和安全性'
            },
            {
                title: '优化用户界面',
                description: '基于用户反馈，建议改进规则编辑界面，提供更直观的配置体验',
                priority: 'low',
                impact: '提升用户体验和操作效率'
            }
        ];
        
        mockSuggestions.forEach(suggestion => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'suggestion-item';
            suggestionItem.innerHTML = `
                <div class="suggestion-header">
                    <span class="suggestion-title">${suggestion.title}</span>
                    <span class="suggestion-priority ${suggestion.priority}">${suggestion.priority}</span>
                </div>
                <div class="suggestion-description">${suggestion.description}</div>
                <div class="suggestion-impact">影响: ${suggestion.impact}</div>
                <button class="btn small secondary" onclick="implementSuggestion('${suggestion.title}')">采纳</button>
            </div>
            `;
            suggestionsList.appendChild(suggestionItem);
        });
        
        addNotification('迭代建议生成完成', 'success');
        
    }, 2500);
}

/**
 * 采纳迭代建议
 */
function implementSuggestion(title) {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限采纳迭代建议', 'error');
        return;
    }
    
    addNotification(`采纳建议: ${title}`, 'info');
    logOperation(`采纳迭代建议: ${title}`, appState.currentUser.username, 'info');
    
    // 模拟采纳过程
    setTimeout(() => {
        addNotification(`建议 "${title}" 已安排实施`, 'success');
    }, 1000);
}

/**
 * 连接DeepSeek模型
 */
function connectDeepSeek() {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限连接DeepSeek模型', 'error');
        return;
    }
    
    addNotification('正在连接DeepSeek模型...', 'info');
    logOperation('连接DeepSeek模型', appState.currentUser.username, 'info');
    
    // 模拟连接过程
    setTimeout(() => {
        appState.deepseekConnected = true;
        updateDeepSeekStatus();
        
        addNotification('DeepSeek模型连接成功', 'success');
        logOperation('DeepSeek模型连接成功', appState.currentUser.username, 'success');
        
    }, 3000);
}

/**
 * 更新DeepSeek模型
 */
function updateDeepSeekModel() {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限更新DeepSeek模型', 'error');
        return;
    }
    
    addNotification('正在更新DeepSeek模型...', 'info');
    logOperation('更新DeepSeek模型', appState.currentUser.username, 'info');
    
    // 模拟更新过程
    setTimeout(() => {
        updateDeepSeekStatus(true);
        
        addNotification('DeepSeek模型更新成功', 'success');
        logOperation('DeepSeek模型更新成功', appState.currentUser.username, 'success');
        
    }, 5000);
}

/**
 * 更新DeepSeek状态显示
 */
function updateDeepSeekStatus(isUpdated = false) {
    const connectionStatus = document.getElementById('deepseek-connection');
    const versionElement = document.getElementById('deepseek-version');
    const lastUpdateElement = document.getElementById('deepseek-last-update');
    
    connectionStatus.textContent = appState.deepseekConnected ? '已连接' : '未连接';
    connectionStatus.className = appState.deepseekConnected ? 'status-value connected' : 'status-value disconnected';
    
    if (appState.deepseekConnected) {
        versionElement.textContent = isUpdated ? '1.2.0' : '1.1.0';
        lastUpdateElement.textContent = new Date().toLocaleString();
    } else {
        versionElement.textContent = '未知';
        lastUpdateElement.textContent = '--';
    }
}

/**
 * 使用DeepSeek分析系统问题
 */
function analyzeSystemWithDeepseek() {
    if (!appState.deepseekConnected) {
        addNotification('请先连接DeepSeek模型', 'error');
        return;
    }
    
    addNotification('DeepSeek正在分析系统问题...', 'info');
    logOperation('使用DeepSeek分析系统问题', appState.currentUser?.username || 'SYSTEM', 'info');
    
    // 模拟分析过程
    setTimeout(() => {
        addNotification('DeepSeek分析完成，未发现严重问题', 'success');
    }, 4000);
}

/**
 * 使用DeepSeek优化规则配置
 */
function optimizeRulesWithDeepseek() {
    if (!appState.deepseekConnected) {
        addNotification('请先连接DeepSeek模型', 'error');
        return;
    }
    
    addNotification('DeepSeek正在优化规则配置...', 'info');
    logOperation('使用DeepSeek优化规则配置', appState.currentUser?.username || 'SYSTEM', 'info');
    
    // 模拟优化过程
    setTimeout(() => {
        addNotification('规则配置优化完成，已生成优化建议', 'success');
    }, 5000);
}

/**
 * 使用DeepSeek生成修复代码
 */
function generateCodeWithDeepseek() {
    if (!appState.deepseekConnected) {
        addNotification('请先连接DeepSeek模型', 'error');
        return;
    }
    
    addNotification('DeepSeek正在生成修复代码...', 'info');
    logOperation('使用DeepSeek生成修复代码', appState.currentUser?.username || 'SYSTEM', 'info');
    
    // 模拟生成过程
    setTimeout(() => {
        addNotification('修复代码生成完成，请在灰度环境测试', 'success');
    }, 6000);
}

/**
 * 创建备份
 */
function createBackup() {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限创建备份', 'error');
        return;
    }
    
    addNotification('正在创建系统备份...', 'info');
    logOperation('创建系统备份', appState.currentUser.username, 'info');
    
    // 模拟备份过程
    setTimeout(() => {
        addNotification('系统备份创建成功', 'success');
        logOperation('系统备份成功', appState.currentUser.username, 'success');
        
        // 更新备份列表
        loadBackupsList();
        
    }, 3500);
}

/**
 * 恢复备份
 */
function restoreBackup() {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限恢复备份', 'error');
        return;
    }
    
    // 确认对话框
    if (!confirm('确定要恢复备份吗？这将覆盖当前配置，建议先创建新的备份。')) {
        return;
    }
    
    addNotification('正在恢复系统备份...', 'info');
    logOperation('恢复系统备份', appState.currentUser.username, 'info');
    
    // 模拟恢复过程
    setTimeout(() => {
        addNotification('系统备份恢复成功', 'success');
        logOperation('系统备份恢复成功', appState.currentUser.username, 'success');
        
        // 模拟系统重启
        setTimeout(() => {
            location.reload();
        }, 2000);
        
    }, 4000);
}

/**
 * 加载备份列表
 */
function loadBackupsList() {
    const backupsListBody = document.getElementById('backups-list-body');
    backupsListBody.innerHTML = '';
    
    // 模拟备份数据
    const mockBackups = [
        {
            id: 'BACKUP-20240120-1500',
            time: '2024-01-20 15:00:00',
            size: '15.2 MB',
            status: 'valid',
            description: '系统更新前备份'
        },
        {
            id: 'BACKUP-20240119-1830',
            time: '2024-01-19 18:30:00',
            size: '14.8 MB',
            status: 'valid',
            description: '每日自动备份'
        },
        {
            id: 'BACKUP-20240118-0915',
            time: '2024-01-18 09:15:00',
            size: '14.5 MB',
            status: 'valid',
            description: '规则修改前备份'
        },
        {
            id: 'BACKUP-20240117-1200', 
            time: '2024-01-17 12:00:00',
            size: '14.3 MB',
            status: 'valid',
            description: '每日自动备份'
        }
    ];
    
    mockBackups.forEach(backup => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${backup.id}</td>
            <td>${backup.time}</td>
            <td>${backup.size}</td>
            <td><span class="backup-status ${backup.status}">${backup.status === 'valid' ? '有效' : '无效'}</span></td>
            <td>
                <button class="btn small secondary" onclick="viewBackupDetails('${backup.id}')">查看</button>
                <button class="btn small primary" onclick="restoreFromBackup('${backup.id}')">恢复</button>
                <button class="btn small danger" onclick="deleteBackup('${backup.id}')">删除</button>
            </td>
        `;
        
        backupsListBody.appendChild(row);
    });
}

/**
 * 查看备份详情
 */
function viewBackupDetails(backupId) {
    addNotification(`查看备份详情: ${backupId}`, 'info');
    // 实际应用中应该显示详细的备份信息
}

/**
 * 从备份恢复
 */
function restoreFromBackup(backupId) {
    if (confirm(`确定要从备份 ${backupId} 恢复吗？`)) {
        addNotification(`正在从备份 ${backupId} 恢复...`, 'info');
        
        // 模拟恢复过程
        setTimeout(() => {
            addNotification(`备份 ${backupId} 恢复成功`, 'success');
            logOperation(`从备份恢复: ${backupId}`, appState.currentUser?.username || 'SYSTEM', 'info');
        }, 3000);
    }
}

/**
 * 删除备份
 */
function deleteBackup(backupId) {
    // 检查权限
    const isAdminOrVikeyAdmin = appState.currentUser && 
                              (appState.currentUser.role === 'administrator' || 
                               appState.currentUser.role === 'vikey_admin');
    
    if (!isAdminOrVikeyAdmin) {
        addNotification('您没有权限删除备份', 'error');
        return;
    }
    
    if (confirm(`确定要删除备份 ${backupId} 吗？`)) {
        addNotification(`正在删除备份 ${backupId}...`, 'info');
        
        // 模拟删除过程
        setTimeout(() => {
            addNotification(`备份 ${backupId} 删除成功`, 'success');
            logOperation(`删除备份: ${backupId}`, appState.currentUser.username, 'info');
            
            // 更新备份列表
            loadBackupsList();
            
        }, 2000);
    }
}

// 暴露全局方法
window.refreshRules = refreshRules;
window.exportRules = exportRules;
window.importRules = importRules;
window.viewRuleDetails = viewRuleDetails;
window.editRule = editRule;
window.deleteRule = deleteRule;
window.createNewRule = createNewRule;
window.resetEditor = resetEditor;
window.saveRuleChanges = saveRuleChanges;
window.testRule = testRule;
window.deleteSelectedRule = deleteSelectedRule;
window.startAutoRepairScan = startAutoRepairScan;
window.stopAutoRepairScan = stopAutoRepairScan;
window.deployToGray = deployToGray;
window.promoteToProduction = promoteToProduction;
window.generateSuggestions = generateSuggestions;
window.implementSuggestion = implementSuggestion;
window.connectDeepSeek = connectDeepSeek;
window.updateDeepSeekModel = updateDeepSeekModel;
window.analyzeSystemWithDeepseek = analyzeSystemWithDeepseek;
window.optimizeRulesWithDeepseek = optimizeRulesWithDeepseek;
window.generateCodeWithDeepseek = generateCodeWithDeepseek;
window.createBackup = createBackup;
window.restoreBackup = restoreBackup;
window.viewBackupDetails = viewBackupDetails;
window.restoreFromBackup = restoreFromBackup;
window.deleteBackup = deleteBackup;
window.clearLogs = clearLogs;