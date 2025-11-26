/**
 * vikey-monitor.js - 规则监测页面主模块
 * 处理规则监测页面的交互逻辑、数据加载和UI控制
 */

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 检查必要模块是否加载
    if (typeof Auth === 'undefined' || typeof Logging === 'undefined' || typeof Notification === 'undefined' || 
        typeof RulesMonitor === 'undefined' || typeof DeepSeekIntegration === 'undefined') {
        console.error('缺少必要的依赖模块，正在尝试重新加载...');
        setTimeout(() => {
            window.location.reload();
        }, 1000);
        return;
    }
    
    // 初始化页面
    initPage();
});

/**
 * 页面初始化
 */
function initPage() {
    // 验证用户权限
    checkUserPermission();
    
    // 初始化UI组件
    initUIComponents();
    
    // 加载规则列表
    loadRulesList();
    
    // 加载迭代历史和建议
    loadIterationsData();
    
    // 隐藏加载遮罩
    setTimeout(() => {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.opacity = '0';
            setTimeout(() => {
                loadingOverlay.style.display = 'none';
            }, 300);
        }
    }, 800);
}

/**
 * 检查用户权限
 */
function checkUserPermission() {
    // 获取当前用户信息
    const currentUser = Auth.getCurrentUser();
    
    // 更新当前用户显示
    if (currentUser) {
        document.getElementById('current-user').textContent = currentUser.username || '未知用户';
        document.getElementById('user-role').textContent = currentUser.role || '未知权限';
        
        // 检查用户是否有管理员或Vikey管理员权限
        const hasAdminPermission = Auth.hasPermission(['admin', 'vikey_admin']);
        
        // 如果没有足够权限，显示警告信息并禁用修改操作
        if (!hasAdminPermission) {
            const permissionWarning = document.getElementById('permission-warning');
            if (permissionWarning) {
                permissionWarning.classList.remove('hidden');
            }
            
            // 禁用修改操作按钮
            const adminButtons = document.querySelectorAll('.btn-primary, #auto-repair-toggle, #manual-repair-rule, #restart-rule');
            adminButtons.forEach(button => {
                if (button.tagName === 'INPUT' && button.type === 'checkbox') {
                    button.disabled = true;
                } else {
                    button.disabled = true;
                    button.classList.add('btn-disabled');
                }
            });
        }
    }
    
    // 绑定登出事件
    document.getElementById('logout-btn').addEventListener('click', () => {
        Auth.logout();
    });
}

/**
 * 初始化UI组件
 */
function initUIComponents() {
    // 初始化按钮事件
    initButtonEvents();
    
    // 初始化过滤和搜索
    initFilters();
    
    // 初始化分页控件
    initPagination();
    
    // 初始化模态框
    initModals();
    
    // 初始化标签页
    initTabs();
}

/**
 * 初始化按钮事件
 */
function initButtonEvents() {
    // 监控控制按钮
    document.getElementById('start-monitor').addEventListener('click', startMonitoring);
    document.getElementById('stop-monitor').addEventListener('click', stopMonitoring);
    document.getElementById('manual-check').addEventListener('click', manualCheck);
    
    // 自动修复开关
    document.getElementById('auto-repair-toggle').addEventListener('change', toggleAutoRepair);
    
    // 迭代刷新按钮
    document.getElementById('refresh-iterations').addEventListener('click', loadIterationsData);
}

/**
 * 初始化过滤和搜索
 */
function initFilters() {
    // 规则状态过滤
    document.getElementById('rule-filter').addEventListener('change', filterRules);
    
    // 规则类型过滤
    document.getElementById('rule-type-filter').addEventListener('change', filterRules);
    
    // 规则搜索
    document.getElementById('rule-search').addEventListener('input', searchRules);
    
    // 搜索按钮
    document.querySelector('.btn-search').addEventListener('click', () => {
        searchRules();
    });
}

/**
 * 初始化分页控件
 */
function initPagination() {
    document.getElementById('prev-page').addEventListener('click', goToPrevPage);
    document.getElementById('next-page').addEventListener('click', goToNextPage);
}

/**
 * 初始化模态框
 */
function initModals() {
    // 规则详情模态框
    const detailsModal = document.getElementById('rule-details-modal');
    document.getElementById('close-details-modal').addEventListener('click', () => {
        detailsModal.classList.remove('show');
    });
    
    document.getElementById('close-rule-details').addEventListener('click', () => {
        detailsModal.classList.remove('show');
    });
    
    // 规则修复确认模态框
    const repairModal = document.getElementById('repair-confirm-modal');
    document.getElementById('close-repair-modal').addEventListener('click', () => {
        repairModal.classList.remove('show');
    });
    
    document.getElementById('cancel-repair').addEventListener('click', () => {
        repairModal.classList.remove('show');
    });
    
    // 手动修复按钮
    document.getElementById('manual-repair-rule').addEventListener('click', showRepairConfirm);
    
    // 确认修复按钮
    document.getElementById('confirm-repair').addEventListener('click', confirmRepair);
    
    // 重启规则按钮
    document.getElementById('restart-rule').addEventListener('click', restartSelectedRule);
    
    // 点击模态框外部关闭
    window.addEventListener('click', (event) => {
        if (event.target === detailsModal) {
            detailsModal.classList.remove('show');
        } else if (event.target === repairModal) {
            repairModal.classList.remove('show');
        }
    });
}

/**
 * 初始化标签页
 */
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // 移除所有活动状态
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // 设置当前活动状态
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(`${tabId}-content`).classList.add('active');
        });
    });
}

/**
 * 加载规则列表
 */
function loadRulesList() {
    // 显示加载状态
    const tableBody = document.getElementById('rules-table-body');
    tableBody.innerHTML = `
        <tr class="loading-row">
            <td colspan="7">
                <div class="loading-spinner small"></div>
                <span>加载规则列表中...</span>
            </td>
        </tr>
    `;
    
    // 模拟API请求获取规则数据
    // 在实际应用中，这里应该调用后端API
    setTimeout(() => {
        // 模拟规则数据
        const rules = getMockRulesData();
        
        // 渲染规则列表
        renderRulesTable(rules);
        
        // 更新监控统计
        updateMonitoringStats(rules);
        
    }, 1200);
}

/**
 * 渲染规则表格
 */
function renderRulesTable(rules) {
    const tableBody = document.getElementById('rules-table-body');
    tableBody.innerHTML = '';
    
    if (rules.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 2rem; color: #6c757d;">
                    没有找到匹配的规则
                </td>
            </tr>
        `;
        return;
    }
    
    // 渲染规则行
    rules.forEach(rule => {
        const row = document.createElement('tr');
        row.dataset.ruleId = rule.id;
        
        // 获取状态样式
        const statusClass = rule.status === 'healthy' ? 'healthy' : 
                            rule.status === 'error' ? 'error' : 'warning';
        
        // 获取类型显示名称
        const typeName = getRuleTypeName(rule.type);
        
        // 获取优先级显示名称
        const priorityName = getRulePriorityName(rule.priority);
        
        row.innerHTML = `
            <td>${rule.id}</td>
            <td>${rule.name}</td>
            <td>${typeName}</td>
            <td>${priorityName}</td>
            <td>
                <span class="status-badge ${statusClass}">${rule.status === 'healthy' ? '正常' : 
                                                                    rule.status === 'error' ? '异常' : '警告'}</span>
            </td>
            <td>${formatDate(rule.lastChecked)}</td>
            <td>
                <button class="btn btn-secondary btn-sm view-rule-details">
                    <i class="fas fa-eye"></i>
                    详情
                </button>
                ${rule.status !== 'healthy' ? `
                    <button class="btn btn-primary btn-sm repair-rule">
                        <i class="fas fa-wrench"></i>
                        修复
                    </button>
                    <button class="btn btn-success btn-sm restart-rule">
                        <i class="fas fa-sync-alt"></i>
                        重启
                    </button>
                ` : `
                    <button class="btn btn-success btn-sm restart-rule">
                        <i class="fas fa-sync-alt"></i>
                        重启
                    </button>
                `}
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // 绑定行内按钮事件
    bindRowButtonEvents();
}

/**
 * 绑定行内按钮事件
 */
function bindRowButtonEvents() {
    // 查看详情按钮
    document.querySelectorAll('.view-rule-details').forEach(button => {
        button.addEventListener('click', function() {
            const ruleId = this.closest('tr').dataset.ruleId;
            showRuleDetails(ruleId);
        });
    });
    
    // 修复按钮
    document.querySelectorAll('.repair-rule').forEach(button => {
        button.addEventListener('click', function() {
            const ruleId = this.closest('tr').dataset.ruleId;
            const ruleName = this.closest('tr').querySelector('td:nth-child(2)').textContent;
            showRepairConfirm(ruleId, ruleName);
        });
    });
    
    // 重启按钮
    document.querySelectorAll('.restart-rule').forEach(button => {
        button.addEventListener('click', function() {
            const ruleId = this.closest('tr').dataset.ruleId;
            restartRule(ruleId);
        });
    });
}

/**
 * 显示规则详情
 */
function showRuleDetails(ruleId) {
    // 获取规则数据
    const rules = getMockRulesData();
    const rule = rules.find(r => r.id === ruleId);
    
    if (!rule) {
        Notification.show('错误', '找不到规则信息', 'error');
        return;
    }
    
    // 填充规则详情
    document.getElementById('detail-rule-id').textContent = rule.id;
    document.getElementById('detail-rule-name').textContent = rule.name;
    document.getElementById('detail-rule-type').textContent = getRuleTypeName(rule.type);
    document.getElementById('detail-rule-priority').textContent = getRulePriorityName(rule.priority);
    document.getElementById('detail-rule-description').textContent = rule.description || '无';
    document.getElementById('detail-rule-created').textContent = formatDate(rule.created);
    document.getElementById('detail-rule-updated').textContent = formatDate(rule.updated);
    document.getElementById('detail-rule-enabled').textContent = rule.enabled ? '已启用' : '已禁用';
    document.getElementById('detail-rule-status').textContent = rule.status === 'healthy' ? '正常' : 
                                                               rule.status === 'error' ? '异常' : '警告';
    document.getElementById('detail-rule-error').textContent = rule.errorMessage || '无';
    document.getElementById('detail-rule-checked').textContent = formatDate(rule.lastChecked);
    
    // 填充规则详情内容
    document.getElementById('rule-details-content').textContent = rule.details || '无详细信息';
    
    // 填充操作历史
    const historyList = document.getElementById('rule-history-list');
    historyList.innerHTML = '';
    
    if (rule.history && rule.history.length > 0) {
        rule.history.forEach(historyItem => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.innerHTML = `
                <div class="history-item-time">${formatDate(historyItem.timestamp)}</div>
                <div class="history-item-action">${historyItem.action}</div>
                <div class="history-item-user">操作人: ${historyItem.user}</div>
            `;
            historyList.appendChild(item);
        });
    } else {
        historyList.innerHTML = '<div style="padding: 1rem; text-align: center; color: #6c757d;">暂无操作历史</div>';
    }
    
    // 保存当前选中的规则ID到模态框
    document.getElementById('rule-details-modal').dataset.selectedRuleId = ruleId;
    
    // 显示模态框
    document.getElementById('rule-details-modal').classList.add('show');
}

/**
 * 显示修复确认模态框
 */
function showRepairConfirm(ruleId, ruleName) {
    if (!ruleId) {
        // 从规则详情模态框获取
        ruleId = document.getElementById('rule-details-modal').dataset.selectedRuleId;
    }
    
    if (!ruleName) {
        // 获取规则名称
        const rule = getMockRulesData().find(r => r.id === ruleId);
        ruleName = rule ? rule.name : '未知规则';
    }
    
    // 填充规则名称
    document.getElementById('repair-rule-name').textContent = ruleName;
    
    // 保存当前选中的规则ID
    document.getElementById('repair-confirm-modal').dataset.selectedRuleId = ruleId;
    
    // 显示模态框
    document.getElementById('repair-confirm-modal').classList.add('show');
}

/**
 * 确认修复
 */
function confirmRepair() {
    const ruleId = document.getElementById('repair-confirm-modal').dataset.selectedRuleId;
    const useDeepSeek = document.getElementById('use-deepseek-repair').checked;
    
    // 关闭模态框
    document.getElementById('repair-confirm-modal').classList.remove('show');
    
    // 显示修复中状态
    Notification.show('修复中', '正在修复规则，请稍候...', 'info');
    
    // 获取规则信息
    const rule = getMockRulesData().find(r => r.id === ruleId);
    const ruleName = rule ? rule.name : '未知规则';
    
    // 如果选择了DeepSeek修复，直接调用DeepSeek集成模块
    if (useDeepSeek) {
        DeepSeekIntegration.analyzeAndFixRule(rule).then(result => {
            if (result.success) {
                // DeepSeek修复成功
                Notification.show('成功', `规则 ${ruleName} AI修复成功`, 'success');
                
                // 记录日志
                Logging.logAction('repair_rule_ai', `使用DeepSeek模型修复规则 ${ruleId} ${ruleName}`);
                
                // 显示AI修复详情
                showAIFixDetails(ruleId, result);
                
                // 重新加载规则列表
                loadRulesList();
            } else {
                // DeepSeek修复失败，尝试传统修复
                fallbackToTraditionalRepair(ruleId, ruleName);
            }
        }).catch(error => {
            console.error('DeepSeek修复失败:', error);
            // 失败时回退到传统修复
            fallbackToTraditionalRepair(ruleId, ruleName);
        });
    } else {
        // 直接使用传统修复
        fallbackToTraditionalRepair(ruleId, ruleName);
    }
}

/**
 * 传统修复回退方法
 */
function fallbackToTraditionalRepair(ruleId, ruleName) {
    // 调用规则监测核心模块进行修复
    RulesMonitor.repairRule(ruleId).then(result => {
        if (result.success) {
            // 修复成功
            Notification.show('成功', `规则 ${ruleName} 修复成功`, 'success');
            
            // 记录日志
            Logging.logAction('repair_rule', `修复规则 ${ruleId} ${ruleName}`);
            
            // 重新加载规则列表
            loadRulesList();
        } else {
            // 修复失败
            Notification.show('错误', `规则修复失败: ${result.error}`, 'error');
        }
    }).catch(error => {
        Notification.show('错误', `修复过程中发生错误: ${error.message}`, 'error');
    });
}

/**
 * 显示AI修复详情
 */
function showAIFixDetails(ruleId, fixDetails) {
    // 创建或获取详情模态框
    let modal = document.getElementById('ai-fix-details-modal');
    
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'ai-fix-details-modal';
        modal.className = 'modal';
        document.body.appendChild(modal);
    }
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>AI修复详情</h3>
                <button class="close-modal" onclick="document.getElementById('ai-fix-details-modal').classList.remove('show')">×</button>
            </div>
            <div class="modal-body">
                <div class="ai-fix-detail">
                    <h4>问题分析</h4>
                    <p>${fixDetails.analysis || '无详细分析'}</p>
                </div>
                <div class="ai-fix-detail">
                    <h4>修复方案</h4>
                    <p>${fixDetails.suggestedFix || '无详细方案'}</p>
                </div>
                <div class="ai-fix-detail">
                    <h4>置信度</h4>
                    <div class="confidence-bar">
                        <div class="confidence-level confidence-${fixDetails.confidence >= 80 ? 'high' : fixDetails.confidence >= 50 ? 'medium' : 'low'}" 
                             style="width: ${fixDetails.confidence || 0}%"></div>
                    </div>
                    <span class="confidence-value">${fixDetails.confidence || 0}%</span>
                </div>
                ${fixDetails.fixedConfig ? `
                <div class="ai-fix-detail">
                    <h4>修复后配置</h4>
                    <pre class="code-block">${JSON.stringify(fixDetails.fixedConfig, null, 2)}</pre>
                </div>
                ` : ''}
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="document.getElementById('ai-fix-details-modal').classList.remove('show')">关闭</button>
            </div>
        </div>
    `;
    
    // 显示模态框
    modal.classList.add('show');
}

/**
 * 应用迭代建议
 */
function applyIterationSuggestion(suggestionId) {
    // 确认操作
    if (!confirm('确定要应用此迭代建议吗？')) {
        return;
    }
    
    // 获取当前用户
    const currentUser = Auth.getCurrentUser();
    
    // 使用DeepSeek集成模块应用建议
    DeepSeekIntegration.applyIterationSuggestion(suggestionId, currentUser).then(success => {
        if (success) {
            Notification.show('成功', '迭代建议应用成功', 'success');
            
            // 记录操作
            Logging.logAction('apply_iteration', `应用迭代建议 ${suggestionId}`);
            
            // 重新加载迭代数据
            loadIterationsData();
        } else {
            Notification.show('错误', '迭代建议应用失败', 'error');
        }
    }).catch(error => {
        console.error('应用迭代建议失败:', error);
        Notification.show('错误', `迭代建议应用失败: ${error.message}`, 'error');
    });
}

/**
 * 拒绝迭代建议
 */
function rejectIterationSuggestion(suggestionId) {
    // 获取拒绝原因
    const reason = prompt('请输入拒绝此迭代建议的原因：');
    if (reason === null) return; // 用户取消
    
    // 使用DeepSeek集成模块拒绝建议
    DeepSeekIntegration.rejectIterationSuggestion(suggestionId, reason).then(success => {
        if (success) {
            Notification.show('成功', '迭代建议已拒绝', 'success');
            
            // 记录操作
            Logging.logAction('reject_iteration', `拒绝迭代建议 ${suggestionId}，原因: ${reason}`);
            
            // 重新加载迭代数据
            loadIterationsData();
        } else {
            Notification.show('错误', '迭代建议拒绝失败', 'error');
        }
    }).catch(error => {
        console.error('拒绝迭代建议失败:', error);
        Notification.show('错误', `迭代建议拒绝失败: ${error.message}`, 'error');
    });
}

/**
 * 重启规则
 */
function restartRule(ruleId) {
    // 获取规则名称
    const rule = getMockRulesData().find(r => r.id === ruleId);
    const ruleName = rule ? rule.name : '未知规则';
    
    // 显示重启中状态
    Notification.show('重启中', `正在重启规则 ${ruleName}，请稍候...`, 'info');
    
    // 调用规则监测核心模块重启规则
    RulesMonitor.restartRule(ruleId).then(result => {
        if (result.success) {
            // 重启成功
            Notification.show('成功', `规则 ${ruleName} 重启成功`, 'success');
            
            // 记录日志
            Logging.logAction('restart_rule', `重启规则 ${ruleId} ${ruleName}`);
            
            // 重新加载规则列表
            loadRulesList();
        } else {
            // 重启失败
            Notification.show('错误', `规则重启失败: ${result.error}`, 'error');
        }
    }).catch(error => {
        Notification.show('错误', `重启过程中发生错误: ${error.message}`, 'error');
    });
}

/**
 * 从规则详情模态框重启规则
 */
function restartSelectedRule() {
    const ruleId = document.getElementById('rule-details-modal').dataset.selectedRuleId;
    if (ruleId) {
        // 关闭模态框
        document.getElementById('rule-details-modal').classList.remove('show');
        // 重启规则
        restartRule(ruleId);
    }
}

/**
 * 开始监控
 */
function startMonitoring() {
    // 调用规则监测核心模块开始监控
    RulesMonitor.startMonitoring();
    
    // 更新UI状态
    updateMonitorStatus(true);
    
    // 记录日志
    Logging.logAction('start_monitoring', '启动系统规则监控');
}

/**
 * 停止监控
 */
function stopMonitoring() {
    // 调用规则监测核心模块停止监控
    RulesMonitor.stopMonitoring();
    
    // 更新UI状态
    updateMonitorStatus(false);
    
    // 记录日志
    Logging.logAction('stop_monitoring', '停止系统规则监控');
}

/**
 * 手动检查
 */
function manualCheck() {
    // 显示检查中状态
    Notification.show('检查中', '正在手动检查规则状态，请稍候...', 'info');
    
    // 调用规则监测核心模块进行手动检查
    RulesMonitor.manualCheck().then(result => {
        if (result.success) {
            // 检查完成
            Notification.show('成功', '手动检查完成', 'success');
            
            // 重新加载规则列表
            loadRulesList();
            
            // 更新最后检查时间
            document.getElementById('last-check-time').textContent = formatDate(new Date());
            
            // 记录日志
            Logging.logAction('manual_check', '执行手动规则检查');
        } else {
            // 检查失败
            Notification.show('错误', `手动检查失败: ${result.error}`, 'error');
        }
    }).catch(error => {
        Notification.show('错误', `检查过程中发生错误: ${error.message}`, 'error');
    });
}

/**
 * 切换自动修复功能
 */
function toggleAutoRepair() {
    const enabled = document.getElementById('auto-repair-toggle').checked;
    
    // 更新规则监测核心模块的自动修复设置
    RulesMonitor.setAutoRepairEnabled(enabled);
    
    // 记录日志
    Logging.logAction('toggle_auto_repair', `自动修复功能已${enabled ? '启用' : '禁用'}`);
    
    // 显示通知
    Notification.show('设置已更新', `自动修复功能已${enabled ? '启用' : '禁用'}`, 'info');
}

/**
 * 更新监控状态UI
 */
function updateMonitorStatus(isActive) {
    const statusIndicator = document.getElementById('monitor-status-indicator');
    const statusText = document.getElementById('monitor-status-text');
    const startButton = document.getElementById('start-monitor');
    const stopButton = document.getElementById('stop-monitor');
    
    if (isActive) {
        // 监控已启动
        statusIndicator.className = 'fas fa-circle status-indicator active';
        statusText.textContent = '监控运行中';
        startButton.disabled = true;
        stopButton.disabled = false;
        
        // 设置下次检查时间
        const nextCheckTime = new Date(Date.now() + RulesMonitor.getCheckInterval());
        document.getElementById('next-check-time').textContent = formatDate(nextCheckTime);
    } else {
        // 监控已停止
        statusIndicator.className = 'fas fa-circle status-indicator inactive';
        statusText.textContent = '监控未启动';
        startButton.disabled = false;
        stopButton.disabled = true;
        document.getElementById('next-check-time').textContent = '--';
    }
}

/**
 * 更新监控统计信息
 */
function updateMonitoringStats(rules) {
    const statsContainer = document.getElementById('rules-monitoring-stats');
    const statItems = statsContainer.querySelectorAll('.stat-item');
    
    // 计算统计数据
    const healthyCount = rules.filter(r => r.status === 'healthy').length;
    const warningCount = rules.filter(r => r.status === 'warning').length;
    const errorCount = rules.filter(r => r.status === 'error').length;
    const totalCount = rules.length;
    
    // 更新统计显示
    if (statItems.length >= 1) {
        statItems[0].querySelector('.stat-number').textContent = healthyCount;
        statItems[0].classList.remove('loading');
    }
    if (statItems.length >= 2) {
        statItems[1].querySelector('.stat-number').textContent = warningCount;
        statItems[1].classList.remove('loading');
    }
    if (statItems.length >= 3) {
        statItems[2].querySelector('.stat-number').textContent = errorCount;
        statItems[2].classList.remove('loading');
    }
    if (statItems.length >= 4) {
        statItems[3].querySelector('.stat-number').textContent = totalCount;
        statItems[3].classList.remove('loading');
    }
    
    // 更新最后检查时间
    if (totalCount > 0) {
        const latestCheck = new Date(Math.max(...rules.map(r => new Date(r.lastChecked))));
        document.getElementById('last-check-time').textContent = formatDate(latestCheck);
    }
}

/**
 * 过滤规则列表
 */
function filterRules() {
    const statusFilter = document.getElementById('rule-filter').value;
    const typeFilter = document.getElementById('rule-type-filter').value;
    const searchTerm = document.getElementById('rule-search').value.toLowerCase().trim();
    
    // 获取所有规则
    const allRules = getMockRulesData();
    
    // 应用过滤
    let filteredRules = allRules;
    
    if (statusFilter !== 'all') {
        filteredRules = filteredRules.filter(r => r.status === statusFilter);
    }
    
    if (typeFilter !== 'all') {
        filteredRules = filteredRules.filter(r => r.type === typeFilter);
    }
    
    if (searchTerm) {
        filteredRules = filteredRules.filter(r => 
            r.name.toLowerCase().includes(searchTerm) || 
            r.id.toLowerCase().includes(searchTerm) ||
            (r.description && r.description.toLowerCase().includes(searchTerm))
        );
    }
    
    // 重新渲染表格
    renderRulesTable(filteredRules);
    
    // 更新分页信息
    updatePagination(filteredRules.length);
}

/**
 * 搜索规则
 */
function searchRules() {
    filterRules();
}

/**
 * 跳转到上一页
 */
function goToPrevPage() {
    // 分页逻辑，实际应用中需要实现
    Notification.show('提示', '分页功能待实现', 'info');
}

/**
 * 跳转到下一页
 */
function goToNextPage() {
    // 分页逻辑，实际应用中需要实现
    Notification.show('提示', '分页功能待实现', 'info');
}

/**
 * 更新分页信息
 */
function updatePagination(totalItems) {
    // 实际应用中需要实现分页逻辑
    document.getElementById('total-pages').textContent = '1';
    document.getElementById('current-page').textContent = '1';
    
    // 禁用分页按钮
    document.getElementById('prev-page').disabled = true;
    document.getElementById('next-page').disabled = true;
}

/**
 * 加载迭代历史和建议
 */
function loadIterationsData() {
    // 显示加载状态
    const historyContainer = document.getElementById('iterations-history');
    const suggestionsContainer = document.getElementById('iterations-suggestions');
    
    historyContainer.innerHTML = `
        <div style="padding: 2rem; text-align: center;">
            <div class="loading-spinner small"></div>
            <span>加载迭代历史中...</span>
        </div>
    `;
    
    suggestionsContainer.innerHTML = `
        <div style="padding: 2rem; text-align: center;">
            <div class="loading-spinner small"></div>
            <span>加载迭代建议中...</span>
        </div>
    `;
    
    // 使用DeepSeek集成模块获取迭代历史和建议
    Promise.all([
        DeepSeekIntegration.getIterationHistory(),
        DeepSeekIntegration.getIterationSuggestions()
    ]).then(([historyData, suggestionsData]) => {
        // 渲染迭代历史，优先使用DeepSeek数据，如果没有则使用模拟数据
        renderIterationsHistory(historyData.length > 0 ? historyData : null);
        
        // 渲染迭代建议，优先使用DeepSeek数据，如果没有则使用模拟数据
        renderIterationsSuggestions(suggestionsData.length > 0 ? suggestionsData : null);
    }).catch(error => {
        console.error('加载迭代数据失败:', error);
        // 发生错误时使用模拟数据
        renderIterationsHistory();
        renderIterationsSuggestions();
    });
}

/**
 * 渲染迭代历史
 */
function renderIterationsHistory(historyData = null) {
    const historyContainer = document.getElementById('iterations-history');
    const iterations = historyData || getMockIterationsHistory();
    
    if (iterations.length === 0) {
        historyContainer.innerHTML = '<div style="padding: 2rem; text-align: center; color: #6c757d;">暂无迭代历史</div>';
        return;
    }
    
    historyContainer.innerHTML = '';
    
    iterations.forEach(iteration => {
        const item = document.createElement('div');
        item.className = 'history-item';
        
        // 构建历史条目内容，适配DeepSeek数据结构
        let actionText = iteration.action || (iteration.status === 'applied' ? '规则迭代已应用' : '规则迭代操作');
        let versionText = iteration.version || '系统自动生成';
        let statusClass = '';
        let statusText = '';
        
        // 添加状态信息（如果有）
        if (iteration.status) {
            statusClass = `status-${iteration.status}`;
            statusText = `<span class="status-badge ${statusClass}">${iteration.status === 'applied' ? '已应用' : iteration.status === 'rejected' ? '已拒绝' : '待处理'}</span>`;
        }
        
        item.innerHTML = `
            <div class="history-item-header">
                <div class="history-item-time">${formatDate(iteration.timestamp)}</div>
                ${statusText}
            </div>
            <div class="history-item-action">${actionText}${iteration.ruleName ? ` - ${iteration.ruleName}` : ''}</div>
            <div class="history-item-user">版本: ${versionText}</div>
            ${iteration.suggestion ? `<div class="history-item-description">${iteration.suggestion}</div>` : ''}
        `;
        
        // 如果有操作按钮，则添加
        if (iteration.status === 'pending' && Auth.hasPermission(['admin', 'vikey_admin'])) {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'history-item-actions';
            actionsDiv.innerHTML = `
                <button class="btn btn-sm btn-primary" onclick="applyIterationSuggestion(${iteration.timestamp || iteration.id})")>应用</button>
                <button class="btn btn-sm btn-secondary" onclick="rejectIterationSuggestion(${iteration.timestamp || iteration.id})")>拒绝</button>
            `;
            item.appendChild(actionsDiv);
        }
        
        historyContainer.appendChild(item);
    });
}

/**
 * 渲染迭代建议
 */
function renderIterationsSuggestions(suggestionsData = null) {
    const suggestionsContainer = document.getElementById('iterations-suggestions');
    const suggestions = suggestionsData || getMockIterationsSuggestions();
    
    if (suggestions.length === 0) {
        suggestionsContainer.innerHTML = '<div style="padding: 2rem; text-align: center; color: #6c757d;">暂无迭代建议</div>';
        return;
    }
    
    suggestionsContainer.innerHTML = '';
    
    suggestions.forEach(suggestion => {
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        
        // 适配DeepSeek数据结构
        const title = suggestion.title || suggestion.name || '规则优化建议';
        const description = suggestion.description || suggestion.suggestion || '无详细描述';
        const impact = suggestion.impact || suggestion.affectedRules || '系统规则';
        const confidence = suggestion.confidence || 0;
        
        // 计算置信度颜色
        let confidenceColor = 'low';
        if (confidence >= 80) confidenceColor = 'high';
        else if (confidence >= 50) confidenceColor = 'medium';
        
        item.innerHTML = `
            <div class="suggestion-header">
                <span class="suggestion-title">${title}</span>
                <span class="suggestion-date">${formatDate(suggestion.timestamp)}</span>
            </div>
            <div class="suggestion-description">${description}</div>
            <div class="suggestion-impact">
                <div class="suggestion-impact-label">影响范围:</div>
                <div>${impact}</div>
            </div>
            <div class="suggestion-confidence">
                <div class="suggestion-confidence-label">置信度:</div>
                <div class="confidence-bar">
                    <div class="confidence-level confidence-${confidenceColor}" style="width: ${confidence}%"></div>
                </div>
                <span class="confidence-value">${confidence}%</span>
            </div>
            ${Auth.hasPermission(['admin', 'vikey_admin']) ? `
            <div class="suggestion-actions">
                <button class="btn btn-sm btn-primary" onclick="applyIterationSuggestion(${suggestion.timestamp || suggestion.id})")>应用建议</button>
            </div>
            ` : ''}
        `;
        
        suggestionsContainer.appendChild(item);
    });
}

/**
 * 格式化日期
 */
function formatDate(date) {
    if (!date) return '--';
    
    const d = new Date(date);
    if (isNaN(d.getTime())) return '--';
    
    return d.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * 获取规则类型显示名称
 */
function getRuleTypeName(type) {
    const typeMap = {
        'system': '系统规则',
        'business': '业务规则',
        'security': '安全规则',
        'performance': '性能规则'
    };
    return typeMap[type] || type;
}

/**
 * 获取规则优先级显示名称
 */
function getRulePriorityName(priority) {
    const priorityMap = {
        'high': '高',
        'medium': '中',
        'low': '低'
    };
    return priorityMap[priority] || priority;
}

/**
 * 获取模拟规则数据
 */
function getMockRulesData() {
    // 模拟规则数据
    return [
        {
            id: 'RULE-001',
            name: '系统权限验证规则',
            type: 'security',
            priority: 'high',
            status: 'healthy',
            description: '验证用户访问系统的权限',
            created: '2024-01-15T09:00:00Z',
            updated: '2024-01-20T14:30:00Z',
            enabled: true,
            lastChecked: new Date().toISOString(),
            details: '此规则用于验证用户访问系统各功能模块的权限级别，确保用户只能访问其权限范围内的功能。',
            history: [
                { timestamp: '2024-01-20T14:30:00Z', action: '更新规则配置', user: 'admin' },
                { timestamp: '2024-01-15T09:00:00Z', action: '创建规则', user: 'system' }
            ]
        },
        {
            id: 'RULE-002',
            name: '数据完整性检查规则',
            type: 'business',
            priority: 'high',
            status: 'warning',
            description: '确保业务数据的完整性和一致性',
            created: '2024-01-10T10:15:00Z',
            updated: '2024-01-22T11:45:00Z',
            enabled: true,
            lastChecked: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5分钟前
            errorMessage: '检测到部分数据字段为空',
            details: '此规则用于检查业务数据的完整性，确保所有必要字段都有值，并且数据格式符合要求。',
            history: [
                { timestamp: '2024-01-22T11:45:00Z', action: '规则警告', user: 'system' },
                { timestamp: '2024-01-10T10:15:00Z', action: '创建规则', user: 'admin' }
            ]
        },
        {
            id: 'RULE-003',
            name: '系统性能监控规则',
            type: 'performance',
            priority: 'medium',
            status: 'error',
            description: '监控系统关键指标，确保性能达标',
            created: '2024-01-05T16:20:00Z',
            updated: '2024-01-23T09:30:00Z',
            enabled: true,
            lastChecked: new Date(Date.now() - 10 * 60 * 1000).toISOString(), // 10分钟前
            errorMessage: '系统响应时间超过阈值',
            details: '此规则用于监控系统的关键性能指标，包括响应时间、CPU使用率、内存占用等，确保系统性能符合要求。',
            history: [
                { timestamp: '2024-01-23T09:30:00Z', action: '规则错误', user: 'system' },
                { timestamp: '2024-01-05T16:20:00Z', action: '创建规则', user: 'admin' }
            ]
        },
        {
            id: 'RULE-004',
            name: '日志记录完整性规则',
            type: 'system',
            priority: 'low',
            status: 'healthy',
            description: '确保系统操作日志的完整性',
            created: '2023-12-28T14:45:00Z',
            updated: '2024-01-18T13:20:00Z',
            enabled: true,
            lastChecked: new Date(Date.now() - 2 * 60 * 1000).toISOString(), // 2分钟前
            details: '此规则用于检查系统操作日志的完整性，确保所有关键操作都有相应的日志记录。',
            history: [
                { timestamp: '2024-01-18T13:20:00Z', action: '更新规则配置', user: 'admin' },
                { timestamp: '2023-12-28T14:45:00Z', action: '创建规则', user: 'system' }
            ]
        },
        {
            id: 'RULE-005',
            name: '安全漏洞扫描规则',
            type: 'security',
            priority: 'high',
            status: 'warning',
            description: '定期扫描系统安全漏洞',
            created: '2023-12-20T11:10:00Z',
            updated: '2024-01-21T15:50:00Z',
            enabled: true,
            lastChecked: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30分钟前
            errorMessage: '发现潜在安全风险',
            details: '此规则用于定期扫描系统中的安全漏洞，确保系统的安全性。',
            history: [
                { timestamp: '2024-01-21T15:50:00Z', action: '规则警告', user: 'system' },
                { timestamp: '2023-12-20T11:10:00Z', action: '创建规则', user: 'admin' }
            ]
        },
        {
            id: 'RULE-006',
            name: '数据备份验证规则',
            type: 'system',
            priority: 'high',
            status: 'healthy',
            description: '验证数据备份的完整性和可恢复性',
            created: '2023-12-15T09:30:00Z',
            updated: '2024-01-19T10:40:00Z',
            enabled: true,
            lastChecked: new Date(Date.now() - 1 * 60 * 1000).toISOString(), // 1分钟前
            details: '此规则用于验证数据备份的完整性和可恢复性，确保在系统故障时能够快速恢复数据。',
            history: [
                { timestamp: '2024-01-19T10:40:00Z', action: '更新规则配置', user: 'admin' },
                { timestamp: '2023-12-15T09:30:00Z', action: '创建规则', user: 'system' }
            ]
        }
    ];
}

/**
 * 获取模拟迭代历史数据
 */
function getMockIterationsHistory() {
    return [
        {
            timestamp: '2024-01-23T10:30:00Z',
            action: '系统自动修复RULE-003性能问题',
            version: 'v1.2.4'
        },
        {
            timestamp: '2024-01-22T16:45:00Z',
            action: '系统更新规则监测算法，提高检测准确率',
            version: 'v1.2.3'
        },
        {
            timestamp: '2024-01-20T09:15:00Z',
            action: 'DeepSeek模型自我训练完成，优化修复逻辑',
            version: 'v1.2.2'
        },
        {
            timestamp: '2024-01-18T14:20:00Z',
            action: '系统自动修复RULE-002数据完整性问题',
            version: 'v1.2.1'
        },
        {
            timestamp: '2024-01-15T11:30:00Z',
            action: '系统规则引擎升级',
            version: 'v1.2.0'
        }
    ];
}

/**
 * 获取模拟迭代建议数据
 */
function getMockIterationsSuggestions() {
    return [
        {
            title: '优化规则执行效率',
            description: '基于历史数据分析，建议优化规则执行调度算法，减少系统资源占用，提高规则检查效率。',
            timestamp: '2024-01-23T08:45:00Z',
            impact: '系统性能、规则执行速度'
        },
        {
            title: '增强异常检测能力',
            description: '建议引入机器学习模型，提高系统对异常模式的识别能力，减少误报和漏报。',
            timestamp: '2024-01-22T11:20:00Z',
            impact: '安全规则、异常检测准确率'
        },
        {
            title: '优化DeepSeek模型集成',
            description: '建议优化DeepSeek模型与规则修复模块的集成，提高自动修复成功率。',
            timestamp: '2024-01-20T15:30:00Z',
            impact: '自动修复功能、模型性能'
        },
        {
            title: '添加预测性维护功能',
            description: '基于历史数据趋势分析，建议添加预测性维护功能，提前发现并解决潜在问题。',
            timestamp: '2024-01-19T09:10:00Z',
            impact: '系统稳定性、维护效率'
        }
    ];
}