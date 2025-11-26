/**
 * logs-viewer.js - 日志查看页面功能实现
 */

// 全局日志查看器对象
const LogsViewer = {
    // 配置信息
    config: {
        pageSize: 10,
        currentPage: 1,
        totalCount: 0,
        logsData: [],
        filteredLogs: [],
        selectedLog: null
    },
    
    // 初始化函数
    init: function() {
        // 初始化UI组件
        this.initUI();
        
        // 检查用户权限
        this.checkUserPermissions();
        
        // 加载日志数据
        this.loadLogsData();
        
        // 注册事件监听器
        this.registerEventListeners();
    },
    
    // 初始化UI组件
    initUI: function() {
        // 初始化日期选择器
        this.initDatePickers();
        
        // 初始化模态框
        this.initModals();
        
        // 应用响应式调整
        this.applyResponsiveLayout();
    },
    
    // 初始化日期选择器
    initDatePickers: function() {
        // 设置默认日期范围（过去7天）
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 7);
        
        // 格式化日期为YYYY-MM-DD
        const formatDate = (date) => {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        };
        
        // 设置默认日期
        document.getElementById('date-from').value = formatDate(startDate);
        document.getElementById('date-to').value = formatDate(endDate);
    },
    
    // 初始化模态框
    initModals: function() {
        // 注册模态框关闭事件
        document.getElementById('close-details-modal').addEventListener('click', () => {
            this.hideModal('log-details-modal');
        });
        
        document.getElementById('close-clear-modal').addEventListener('click', () => {
            this.hideModal('clear-logs-modal');
        });
        
        document.getElementById('cancel-clear').addEventListener('click', () => {
            this.hideModal('clear-logs-modal');
        });
    },
    
    // 检查用户权限
    checkUserPermissions: async function() {
        try {
            // 检查是否已登录
            const isLoggedIn = await Auth.checkAuth();
            if (!isLoggedIn) {
                window.location.href = '/login.html';
                return;
            }
            
            // 获取用户角色
            const userRole = await Auth.getCurrentUserRole();
            
            // 检查是否为管理员或Vikey管理员
            if (userRole !== 'admin' && userRole !== 'vikey_admin') {
                document.getElementById('permission-warning').classList.remove('hidden');
                document.getElementById('logs-content').classList.add('hidden');
                
                // 记录未授权访问
                Logging.logError('日志查看', '未授权访问', { 
                    user: await Auth.getCurrentUser(),
                    role: userRole,
                    page: 'logs-viewer.html'
                });
            } else {
                // 记录授权访问
                Logging.logInfo('日志查看', '管理员访问', { 
                    user: await Auth.getCurrentUser(),
                    role: userRole
                });
            }
        } catch (error) {
            console.error('权限检查失败:', error);
            document.getElementById('permission-warning').textContent = '权限验证失败，请重新登录。';
            document.getElementById('permission-warning').classList.remove('hidden');
        }
    },
    
    // 加载日志数据
    loadLogsData: async function() {
        try {
            // 显示加载状态
            this.showLoading();
            
            // 模拟API请求获取日志数据
            // 在实际实现中，这里应该调用后端API
            this.config.logsData = this.getMockLogsData();
            this.config.totalCount = this.config.logsData.length;
            
            // 应用过滤器并渲染
            this.applyFilters();
            this.updateStats();
            
            // 隐藏加载状态
            this.hideLoading();
        } catch (error) {
            console.error('加载日志失败:', error);
            this.showError('加载日志数据失败，请稍后重试。');
            this.hideLoading();
        }
    },
    
    // 模拟日志数据
    getMockLogsData: function() {
        // 生成模拟数据，实际应该从后端获取
        const levels = ['debug', 'info', 'warning', 'error', 'critical'];
        const actions = [
            '用户登录', '用户登出', '用户创建', '用户修改', '用户删除', 
            '密码修改', '权限变更', '规则检测', '规则修复', '系统备份',
            '系统重启', '配置更新', '灰度测试', '日志清理', '审计报告'
        ];
        const users = ['admin', 'vikey_admin', 'password_admin_1', 'password_admin_2', 'system'];
        const results = ['成功', '失败', '部分成功'];
        
        const logs = [];
        const now = new Date();
        
        // 生成最近7天的日志
        for (let i = 0; i < 100; i++) {
            // 随机日期（过去7天内）
            const dateOffset = Math.floor(Math.random() * 7);
            const logDate = new Date(now);
            logDate.setDate(now.getDate() - dateOffset);
            
            // 随机时间
            logDate.setHours(Math.floor(Math.random() * 24));
            logDate.setMinutes(Math.floor(Math.random() * 60));
            logDate.setSeconds(Math.floor(Math.random() * 60));
            
            // 随机日志级别
            const level = levels[Math.floor(Math.random() * levels.length)];
            
            // 根据日志级别决定结果（error和critical更可能失败）
            let result;
            if (level === 'error' || level === 'critical') {
                result = Math.random() > 0.3 ? '失败' : '成功';
            } else {
                result = Math.random() > 0.1 ? '成功' : results[Math.floor(Math.random() * results.length)];
            }
            
            // 随机用户和操作
            const user = users[Math.floor(Math.random() * users.length)];
            const action = actions[Math.floor(Math.random() * actions.length)];
            
            // 生成详细信息
            let details = {};
            if (action.includes('用户')) {
                details = {
                    user_id: `user_${Math.floor(Math.random() * 1000)}`,
                    username: user,
                    ip_address: `192.168.1.${Math.floor(Math.random() * 255)}`,
                    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'
                };
            } else if (action.includes('规则')) {
                details = {
                    rule_id: `rule_${Math.floor(Math.random() * 100)}`,
                    rule_name: `规则 ${Math.floor(Math.random() * 100)}`,
                    status_before: ['正常', '异常', '部分异常'][Math.floor(Math.random() * 3)],
                    status_after: ['正常', '异常'][Math.floor(Math.random() * 2)]
                };
            } else if (action.includes('系统')) {
                details = {
                    system_component: ['认证服务', '数据服务', '监控服务', '日志服务'][Math.floor(Math.random() * 4)],
                    duration_ms: Math.floor(Math.random() * 5000)
                };
            }
            
            logs.push({
                id: `log_${i + 1}`,
                timestamp: logDate.toISOString(),
                level: level,
                action: action,
                user: user,
                result: result,
                details: details
            });
        }
        
        // 按时间降序排序
        return logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    },
    
    // 应用过滤器
    applyFilters: function() {
        // 获取过滤器值
        const searchTerm = document.getElementById('search-term').value.toLowerCase();
        const levelFilter = document.getElementById('level-filter').value;
        const userFilter = document.getElementById('user-filter').value;
        const dateFrom = document.getElementById('date-from').value;
        const dateTo = document.getElementById('date-to').value;
        
        // 过滤日志
        this.config.filteredLogs = this.config.logsData.filter(log => {
            // 搜索词过滤
            const matchesSearch = !searchTerm || 
                log.action.toLowerCase().includes(searchTerm) ||
                log.user.toLowerCase().includes(searchTerm) ||
                JSON.stringify(log.details).toLowerCase().includes(searchTerm);
            
            // 日志级别过滤
            const matchesLevel = !levelFilter || log.level === levelFilter;
            
            // 用户过滤
            const matchesUser = !userFilter || log.user === userFilter;
            
            // 日期过滤
            const logDate = new Date(log.timestamp).toISOString().split('T')[0];
            const matchesDate = 
                (!dateFrom || logDate >= dateFrom) && 
                (!dateTo || logDate <= dateTo);
            
            return matchesSearch && matchesLevel && matchesUser && matchesDate;
        });
        
        // 重置页码
        this.config.currentPage = 1;
        
        // 渲染日志列表
        this.renderLogList();
        
        // 更新分页信息
        this.updatePagination();
    },
    
    // 渲染日志列表
    renderLogList: function() {
        const logsTableBody = document.getElementById('logs-table-body');
        logsTableBody.innerHTML = '';
        
        // 如果没有数据，显示空状态
        if (this.config.filteredLogs.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.className = 'empty-row';
            emptyRow.innerHTML = `
                <td colspan="6" class="text-center">
                    没有找到符合条件的日志记录
                </td>
            `;
            logsTableBody.appendChild(emptyRow);
            return;
        }
        
        // 计算分页范围
        const startIndex = (this.config.currentPage - 1) * this.config.pageSize;
        const endIndex = startIndex + this.config.pageSize;
        const paginatedLogs = this.config.filteredLogs.slice(startIndex, endIndex);
        
        // 渲染日志行
        paginatedLogs.forEach(log => {
            const logRow = document.createElement('tr');
            
            // 格式化时间
            const formattedTime = this.formatTimestamp(log.timestamp);
            
            // 获取级别标签类名
            const levelClass = `level-badge ${log.level}`;
            
            logRow.innerHTML = `
                <td>${formattedTime}</td>
                <td>
                    <span class="${levelClass}">${this.capitalizeFirst(log.level)}</span>
                </td>
                <td>${log.action}</td>
                <td>${log.user}</td>
                <td>${log.result}</td>
                <td>
                    <button class="btn-view-details" data-log-id="${log.id}">
                        <i class="fas fa-eye"></i> 查看详情
                    </button>
                </td>
            `;
            
            logsTableBody.appendChild(logRow);
            
            // 添加详情按钮点击事件
            logRow.querySelector('.btn-view-details').addEventListener('click', () => {
                this.showLogDetails(log);
            });
        });
    },
    
    // 显示日志详情
    showLogDetails: function(log) {
        this.config.selectedLog = log;
        
        const detailsModal = document.getElementById('log-details-modal');
        const detailsContent = document.getElementById('log-details-content');
        
        // 清空并填充详情内容
        detailsContent.innerHTML = '';
        
        // 添加基本详情
        this.addDetailRow(detailsContent, '日志ID', log.id);
        this.addDetailRow(detailsContent, '时间戳', this.formatTimestamp(log.timestamp, true));
        this.addDetailRow(detailsContent, '日志级别', this.capitalizeFirst(log.level));
        this.addDetailRow(detailsContent, '操作', log.action);
        this.addDetailRow(detailsContent, '用户', log.user);
        this.addDetailRow(detailsContent, '结果', log.result);
        
        // 添加详细信息
        const detailsHtml = document.createElement('div');
        detailsHtml.className = 'detail-row';
        detailsHtml.innerHTML = `
            <div class="detail-label">详细信息</div>
            <div class="detail-value">
                <div class="code-block">
                    <pre>${JSON.stringify(log.details, null, 2)}</pre>
                </div>
            </div>
        `;
        detailsContent.appendChild(detailsHtml);
        
        // 显示模态框
        this.showModal('log-details-modal');
    },
    
    // 添加详情行
    addDetailRow: function(parent, label, value) {
        const row = document.createElement('div');
        row.className = 'detail-row';
        row.innerHTML = `
            <div class="detail-label">${label}</div>
            <div class="detail-value">${value}</div>
        `;
        parent.appendChild(row);
    },
    
    // 更新统计信息
    updateStats: function() {
        // 计算各级别日志数量
        const stats = {
            info: 0,
            warning: 0,
            error: 0,
            critical: 0
        };
        
        this.config.filteredLogs.forEach(log => {
            if (stats.hasOwnProperty(log.level)) {
                stats[log.level]++;
            }
        });
        
        // 更新统计卡片
        document.getElementById('total-logs').textContent = this.config.filteredLogs.length;
        document.getElementById('info-count').textContent = stats.info;
        document.getElementById('warning-count').textContent = stats.warning;
        document.getElementById('error-count').textContent = stats.error;
        document.getElementById('critical-count').textContent = stats.critical;
    },
    
    // 更新分页信息
    updatePagination: function() {
        const totalPages = Math.ceil(this.config.filteredLogs.length / this.config.pageSize);
        
        // 更新分页信息文本
        document.getElementById('pagination-info').textContent = 
            `显示 ${this.config.filteredLogs.length > 0 ? (this.config.currentPage - 1) * this.config.pageSize + 1 : 0} 到 ${Math.min(this.config.currentPage * this.config.pageSize, this.config.filteredLogs.length)} 条，共 ${this.config.filteredLogs.length} 条记录`;
        
        // 更新页码选择器
        const pageSelector = document.getElementById('page-selector');
        pageSelector.innerHTML = '';
        
        for (let i = 1; i <= totalPages; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = `第 ${i} 页`;
            if (i === this.config.currentPage) {
                option.selected = true;
            }
            pageSelector.appendChild(option);
        }
        
        // 更新分页按钮状态
        document.getElementById('prev-page').disabled = this.config.currentPage <= 1;
        document.getElementById('next-page').disabled = this.config.currentPage >= totalPages;
    },
    
    // 注册事件监听器
    registerEventListeners: function() {
        // 搜索按钮
        document.getElementById('search-button').addEventListener('click', () => {
            this.applyFilters();
        });
        
        // 搜索框回车事件
        document.getElementById('search-term').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.applyFilters();
            }
        });
        
        // 重置过滤条件
        document.getElementById('reset-filters').addEventListener('click', () => {
            this.resetFilters();
        });
        
        // 清除日志按钮
        document.getElementById('clear-logs-button').addEventListener('click', () => {
            this.showModal('clear-logs-modal');
        });
        
        // 确认清除日志
        document.getElementById('confirm-clear').addEventListener('click', () => {
            this.clearLogs();
        });
        
        // 导出日志按钮
        document.getElementById('export-logs-button').addEventListener('click', () => {
            this.exportLogs();
        });
        
        // 分页控制
        document.getElementById('prev-page').addEventListener('click', () => {
            if (this.config.currentPage > 1) {
                this.config.currentPage--;
                this.renderLogList();
                this.updatePagination();
            }
        });
        
        document.getElementById('next-page').addEventListener('click', () => {
            const totalPages = Math.ceil(this.config.filteredLogs.length / this.config.pageSize);
            if (this.config.currentPage < totalPages) {
                this.config.currentPage++;
                this.renderLogList();
                this.updatePagination();
            }
        });
        
        document.getElementById('page-selector').addEventListener('change', (e) => {
            this.config.currentPage = parseInt(e.target.value);
            this.renderLogList();
            this.updatePagination();
        });
        
        // 清除选项变更
        document.querySelectorAll('input[name="clear-option"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.updateClearDateInputs();
            });
        });
        
        // 初始更新清除日期输入框
        this.updateClearDateInputs();
    },
    
    // 重置过滤条件
    resetFilters: function() {
        document.getElementById('search-term').value = '';
        document.getElementById('level-filter').value = '';
        document.getElementById('user-filter').value = '';
        
        // 重新设置默认日期范围（过去7天）
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 7);
        
        // 格式化日期为YYYY-MM-DD
        const formatDate = (date) => {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        };
        
        document.getElementById('date-from').value = formatDate(startDate);
        document.getElementById('date-to').value = formatDate(endDate);
        
        // 应用过滤器
        this.applyFilters();
    },
    
    // 更新清除日期输入框状态
    updateClearDateInputs: function() {
        const option = document.querySelector('input[name="clear-option"]:checked').value;
        const dateFrom = document.getElementById('clear-date-from');
        const dateTo = document.getElementById('clear-date-to');
        
        if (option === 'date_range') {
            dateFrom.disabled = false;
            dateTo.disabled = false;
        } else {
            dateFrom.disabled = true;
            dateTo.disabled = true;
        }
    },
    
    // 清除日志
    clearLogs: async function() {
        try {
            // 获取清除选项
            const option = document.querySelector('input[name="clear-option"]:checked').value;
            
            // 记录清除操作
            Logging.logWarning('日志管理', '清除日志', { 
                option: option,
                user: await Auth.getCurrentUser(),
                timestamp: new Date().toISOString()
            });
            
            // 根据选项执行不同的清除逻辑
            switch (option) {
                case 'all':
                    // 清除所有日志（模拟）
                    this.config.logsData = [];
                    break;
                case 'one_week':
                    // 清除一周前的日志（模拟）
                    const oneWeekAgo = new Date();
                    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
                    this.config.logsData = this.config.logsData.filter(
                        log => new Date(log.timestamp) > oneWeekAgo
                    );
                    break;
                case 'one_month':
                    // 清除一月前的日志（模拟）
                    const oneMonthAgo = new Date();
                    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
                    this.config.logsData = this.config.logsData.filter(
                        log => new Date(log.timestamp) > oneMonthAgo
                    );
                    break;
                case 'date_range':
                    // 清除指定日期范围的日志（模拟）
                    const clearDateFrom = document.getElementById('clear-date-from').value;
                    const clearDateTo = document.getElementById('clear-date-to').value;
                    
                    this.config.logsData = this.config.logsData.filter(log => {
                        const logDate = new Date(log.timestamp).toISOString().split('T')[0];
                        return !(logDate >= clearDateFrom && logDate <= clearDateTo);
                    });
                    break;
            }
            
            // 应用过滤并重新渲染
            this.applyFilters();
            this.updateStats();
            
            // 隐藏模态框
            this.hideModal('clear-logs-modal');
            
            // 显示成功提示
            Notification.show('success', '日志清除成功');
            
            // 记录清除成功
            Logging.logInfo('日志管理', '日志清除成功', { 
                option: option,
                user: await Auth.getCurrentUser()
            });
        } catch (error) {
            console.error('清除日志失败:', error);
            this.showError('清除日志失败，请稍后重试。');
            
            // 记录清除失败
            Logging.logError('日志管理', '清除日志失败', { 
                error: error.message,
                user: await Auth.getCurrentUser()
            });
        }
    },
    
    // 导出日志
    exportLogs: function() {
        try {
            // 将过滤后的日志转换为JSON格式
            const logsJson = JSON.stringify(this.config.filteredLogs, null, 2);
            
            // 创建Blob对象
            const blob = new Blob([logsJson], { type: 'application/json' });
            
            // 创建下载链接
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `logs_export_${new Date().toISOString().split('T')[0]}.json`;
            
            // 触发下载
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            // 显示成功提示
            Notification.show('success', '日志导出成功');
            
            // 记录导出操作
            Logging.logInfo('日志管理', '导出日志', { 
                count: this.config.filteredLogs.length,
                user: Auth.getCurrentUser ? Auth.getCurrentUser() : 'unknown'
            });
        } catch (error) {
            console.error('导出日志失败:', error);
            this.showError('导出日志失败，请稍后重试。');
            
            // 记录导出失败
            Logging.logError('日志管理', '导出日志失败', { 
                error: error.message,
                user: Auth.getCurrentUser ? Auth.getCurrentUser() : 'unknown'
            });
        }
    },
    
    // 显示模态框
    showModal: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            // 阻止背景滚动
            document.body.style.overflow = 'hidden';
        }
    },
    
    // 隐藏模态框
    hideModal: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            // 恢复背景滚动
            document.body.style.overflow = '';
        }
    },
    
    // 显示加载状态
    showLoading: function() {
        const loadingIndicator = document.createElement('tr');
        loadingIndicator.id = 'loading-indicator';
        loadingIndicator.className = 'loading-row';
        loadingIndicator.innerHTML = `
            <td colspan="6" class="text-center">
                <div class="loading-spinner"></div>
                加载中...
            </td>
        `;
        
        const logsTableBody = document.getElementById('logs-table-body');
        logsTableBody.innerHTML = '';
        logsTableBody.appendChild(loadingIndicator);
    },
    
    // 隐藏加载状态
    hideLoading: function() {
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    },
    
    // 显示错误消息
    showError: function(message) {
        Notification.show('error', message);
    },
    
    // 应用响应式布局调整
    applyResponsiveLayout: function() {
        const handleResize = () => {
            const tableWrapper = document.querySelector('.table-wrapper');
            const isMobile = window.innerWidth < 768;
            
            if (isMobile) {
                tableWrapper.classList.add('mobile-table');
            } else {
                tableWrapper.classList.remove('mobile-table');
            }
        };
        
        // 初始调用
        handleResize();
        
        // 监听窗口大小变化
        window.addEventListener('resize', handleResize);
    },
    
    // 格式化时间戳
    formatTimestamp: function(timestamp, includeTimezone = false) {
        const date = new Date(timestamp);
        
        // 格式化日期
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        
        // 基本格式：YYYY-MM-DD HH:mm:ss
        let formatted = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        
        // 如果需要时区信息
        if (includeTimezone) {
            const timezone = date.toString().match(/([A-Z]+[\+\-][0-9]+)/)[1];
            formatted += ` ${timezone}`;
        }
        
        return formatted;
    },
    
    // 首字母大写
    capitalizeFirst: function(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
};

// 当DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 确保所需的外部模块已加载
    if (typeof Auth === 'undefined' || typeof Logging === 'undefined' || typeof Notification === 'undefined') {
        console.error('缺少必要的依赖模块');
        setTimeout(() => {
            window.location.reload();
        }, 1000);
        return;
    }
    
    // 初始化日志查看器
    LogsViewer.init();
});

// 暴露LogsViewer到全局作用域
window.LogsViewer = LogsViewer;