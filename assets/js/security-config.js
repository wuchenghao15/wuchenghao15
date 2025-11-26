/**
 * 安全机制配置页面交互逻辑
 * 处理安全设置的加载、保存、动态更新和响应
 */

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 获取安全机制实例
    const securityMechanism = window.SecurityMechanism;
    const rollingCodeSecurity = window.RollingCodeSecurity;
    
    // 初始化页面
    initPage();
    
    // 初始化标签页切换
    initTabs();
    
    // 初始化表单事件监听
    initFormListeners();
    
    // 初始化按钮事件监听
    initButtonListeners();
    
    // 加载当前安全配置
    loadSecurityConfig();
    
    // 加载安全状态
    loadSecurityStatus();
    
    // 加载安全事件
    loadSecurityEvents();
    
    // 加载安全通道
    loadSecurityChannels();
});

/**
 * 初始化页面
 */
function initPage() {
    // 设置滑块值显示
    setupSliders();
    
    // 设置模态框
    setupModals();
    
    // 设置定期刷新
    setupPeriodicRefresh();
}

/**
 * 初始化标签页切换
 */
function initTabs() {
    const tabs = document.querySelectorAll('.config-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // 移除所有活动标签
            tabs.forEach(t => t.classList.remove('active'));
            
            // 添加活动状态到当前标签
            this.classList.add('active');
            
            // 隐藏所有内容
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => content.classList.remove('active'));
            
            // 显示对应内容
            const tabId = this.getAttribute('data-tab');
            document.getElementById(`tab-${tabId}`).classList.add('active');
            
            // 根据标签刷新数据
            if (tabId === 'security-events') {
                loadSecurityEvents();
            } else if (tabId === 'security-channels') {
                loadSecurityChannels();
            } else if (tabId === 'security-report') {
                loadSecurityStatus();
            }
        });
    });
}

/**
 * 设置滑块值显示
 */
function setupSliders() {
    const sliders = [
        { id: 'alert-threshold', default: 5 },
        { id: 'code-length', default: 16 },
        { id: 'rotation-interval', default: 30 },
        { id: 'max-code-age', default: 60 },
        { id: 'rekey-threshold', default: 1000 },
        { id: 'lockout-duration', default: 300 }
    ];
    
    sliders.forEach(sliderConfig => {
        const slider = document.getElementById(sliderConfig.id);
        const valueDisplay = document.getElementById(`${sliderConfig.id}-value`);
        
        if (slider && valueDisplay) {
            // 设置默认值
            slider.value = sliderConfig.default;
            valueDisplay.textContent = slider.value;
            
            // 添加事件监听
            slider.addEventListener('input', function() {
                valueDisplay.textContent = this.value;
            });
        }
    });
}

/**
 * 设置模态框
 */
function setupModals() {
    // 关闭按钮事件
    const closeButtons = document.querySelectorAll('.close-modal');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    // 点击模态框外部关闭
    window.addEventListener('click', function(event) {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
}

/**
 * 设置定期刷新
 */
function setupPeriodicRefresh() {
    // 每30秒刷新一次安全状态
    setInterval(() => {
        loadSecurityStatus();
    }, 30000);
    
    // 每60秒刷新一次安全事件
    setInterval(() => {
        loadSecurityEvents();
    }, 60000);
    
    // 每120秒刷新一次安全通道
    setInterval(() => {
        loadSecurityChannels();
    }, 120000);
}

/**
 * 初始化表单事件监听
 */
function initFormListeners() {
    // 安全级别单选按钮事件
    const securityLevelRadios = document.querySelectorAll('input[name="security-level"]');
    securityLevelRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            updateSecurityLevelBadge(this.value);
        });
    });
}

/**
 * 初始化按钮事件监听
 */
function initButtonListeners() {
    // 保存设置按钮
    document.getElementById('save-settings').addEventListener('click', saveSecuritySettings);
    
    // 取消按钮
    document.getElementById('cancel-changes').addEventListener('click', loadSecurityConfig);
    
    // 生成新滚码按钮
    document.getElementById('generate-new-code').addEventListener('click', generateNewCode);
    
    // 重置滚码状态按钮
    document.getElementById('reset-rolling-code-state').addEventListener('click', resetRollingCodeState);
    
    // 重置默认按钮
    document.getElementById('reset-general-settings').addEventListener('click', resetGeneralSettings);
    document.getElementById('reset-rolling-code-settings').addEventListener('click', resetRollingCodeSettings);
    document.getElementById('reset-advanced-settings').addEventListener('click', resetAdvancedSettings);
    
    // 创建新通道按钮
    document.getElementById('create-new-channel').addEventListener('click', function() {
        document.getElementById('create-channel-modal').style.display = 'block';
    });
    
    // 确认创建通道按钮
    document.getElementById('confirm-create-channel').addEventListener('click', createNewChannel);
    
    // 刷新事件按钮
    document.getElementById('refresh-events').addEventListener('click', loadSecurityEvents);
    
    // 清空事件按钮
    document.getElementById('clear-events').addEventListener('click', clearSecurityEvents);
    
    // 生成安全报告按钮
    document.getElementById('generate-security-report').addEventListener('click', generateSecurityReport);
    
    // 重置所有安全状态按钮
    document.getElementById('reset-all-security').addEventListener('click', function() {
        if (confirm('确定要重置所有安全状态吗？这将清除所有安全事件和通道配置。')) {
            resetAllSecurityState();
        }
    });
    
    // 测试安全措施按钮
    document.getElementById('test-security-measures').addEventListener('click', testSecurityMeasures);
}

/**
 * 加载安全配置
 */
function loadSecurityConfig() {
    showLoading();
    
    try {
        // 从安全机制获取当前配置
        const config = window.SecurityMechanism.config;
        
        // 设置基本设置
        document.getElementById('security-enabled').checked = config.enabled;
        
        // 设置安全级别
        const securityLevelRadio = document.getElementById(`level-${config.securityLevel}`);
        if (securityLevelRadio) {
            securityLevelRadio.checked = true;
            updateSecurityLevelBadge(config.securityLevel);
        }
        
        // 设置审计日志和自动响应
        document.getElementById('audit-logging').checked = config.auditLogging;
        document.getElementById('automatic-response').checked = config.automaticResponse;
        
        // 设置警报阈值
        document.getElementById('alert-threshold').value = config.alertThreshold;
        document.getElementById('alert-threshold-value').textContent = config.alertThreshold;
        
        // 获取滚码锁配置
        const rollingConfig = window.RollingCodeSecurity.config;
        
        // 设置滚码锁配置
        document.getElementById('code-length').value = rollingConfig.codeLength;
        document.getElementById('code-length-value').textContent = rollingConfig.codeLength;
        
        document.getElementById('rotation-interval').value = rollingConfig.rotationInterval / 1000; // 转换为秒
        document.getElementById('rotation-interval-value').textContent = rollingConfig.rotationInterval / 1000;
        
        document.getElementById('max-code-age').value = rollingConfig.maxCodeAge / 1000; // 转换为秒
        document.getElementById('max-code-age-value').textContent = rollingConfig.maxCodeAge / 1000;
        
        // 设置加密算法
        document.getElementById('encryption-algorithm').value = rollingConfig.encryptionAlgorithm;
        document.getElementById('signature-algorithm').value = rollingConfig.signatureAlgorithm;
        
        // 设置高级配置
        document.getElementById('key-exchange-method').value = rollingConfig.keyExchangeMethod;
        
        document.getElementById('rekey-threshold').value = rollingConfig.rekeyThreshold;
        document.getElementById('rekey-threshold-value').textContent = rollingConfig.rekeyThreshold;
        
        document.getElementById('fallback-mechanism').checked = rollingConfig.fallbackMechanism;
        
        document.getElementById('lockout-duration').value = config.lockoutDuration / 1000; // 转换为秒
        document.getElementById('lockout-duration-value').textContent = config.lockoutDuration / 1000;
        
        hideLoading();
    } catch (error) {
        console.error('加载安全配置失败:', error);
        hideLoading();
        showToast('加载安全配置失败', 'error');
    }
}

/**
 * 保存安全设置
 */
function saveSecuritySettings() {
    showLoading();
    
    try {
        // 收集基本设置
        const basicConfig = {
            enabled: document.getElementById('security-enabled').checked,
            securityLevel: document.querySelector('input[name="security-level"]:checked').value,
            auditLogging: document.getElementById('audit-logging').checked,
            automaticResponse: document.getElementById('automatic-response').checked,
            alertThreshold: parseInt(document.getElementById('alert-threshold').value),
            lockoutDuration: parseInt(document.getElementById('lockout-duration').value) * 1000 // 转换为毫秒
        };
        
        // 收集滚码锁设置
        const rollingConfig = {
            codeLength: parseInt(document.getElementById('code-length').value),
            rotationInterval: parseInt(document.getElementById('rotation-interval').value) * 1000, // 转换为毫秒
            maxCodeAge: parseInt(document.getElementById('max-code-age').value) * 1000, // 转换为毫秒
            encryptionAlgorithm: document.getElementById('encryption-algorithm').value,
            signatureAlgorithm: document.getElementById('signature-algorithm').value,
            keyExchangeMethod: document.getElementById('key-exchange-method').value,
            rekeyThreshold: parseInt(document.getElementById('rekey-threshold').value),
            fallbackMechanism: document.getElementById('fallback-mechanism').checked
        };
        
        // 更新全局安全配置
        window.SecurityMechanism.updateConfig(basicConfig);
        
        // 更新滚码锁配置
        window.RollingCodeSecurity.updateConfig(rollingConfig);
        
        // 更新安全级别显示
        updateSecurityLevelBadge(basicConfig.securityLevel);
        
        // 刷新安全状态
        loadSecurityStatus();
        
        hideLoading();
        showToast('安全设置保存成功', 'success');
        
        // 记录配置更改事件
        logSecurityEvent('security_config_saved', {
            basicConfig,
            rollingConfig
        });
    } catch (error) {
        console.error('保存安全设置失败:', error);
        hideLoading();
        showToast('保存安全设置失败', 'error');
    }
}

/**
 * 加载安全状态
 */
function loadSecurityStatus() {
    try {
        // 获取安全报告
        const report = window.SecurityMechanism.getSecurityReport();
        
        // 更新安全状态指示器
        const statusIndicator = document.getElementById('security-status-indicator');
        const statusText = document.getElementById('security-status-text');
        const levelBadge = document.getElementById('security-level-badge');
        
        if (report.config.enabled) {
            statusIndicator.className = 'status-indicator active';
            statusText.textContent = '已启用';
        } else {
            statusIndicator.className = 'status-indicator inactive';
            statusText.textContent = '已禁用';
        }
        
        // 更新安全级别徽章
        updateSecurityLevelBadge(report.config.securityLevel, levelBadge);
        
        // 更新安全报告页面
        document.getElementById('status-enabled').textContent = report.config.enabled ? '已启用' : '已禁用';
        document.getElementById('status-level').textContent = report.config.securityLevel;
        
        // 更新滚码锁状态
        const rollingCodeStatus = report.moduleStatus.rollingCode;
        document.getElementById('status-rolling-code').textContent = rollingCodeStatus.isActive ? '正常' : '异常';
        
        // 更新活跃通道数
        document.getElementById('status-active-channels').textContent = rollingCodeStatus.activeChannels;
        
        // 更新未处理事件数
        document.getElementById('status-pending-events').textContent = report.suspiciousActivities.length;
        
        // 更新最近检查时间
        const lastCheckTime = new Date(report.timestamp).toLocaleString();
        document.getElementById('status-last-check').textContent = lastCheckTime;
    } catch (error) {
        console.error('加载安全状态失败:', error);
    }
}

/**
 * 加载安全事件
 */
function loadSecurityEvents() {
    try {
        const report = window.SecurityMechanism.getSecurityReport();
        const eventsList = document.getElementById('events-list');
        
        // 清空事件列表
        eventsList.innerHTML = '';
        
        if (report.recentEvents.length === 0) {
            eventsList.innerHTML = `
                <div class="event-item">
                    <div class="event-header">
                        <span class="event-type">无安全事件</span>
                    </div>
                    <div class="event-details">当前没有安全事件记录</div>
                </div>
            `;
            return;
        }
        
        // 按时间倒序排序事件
        const sortedEvents = [...report.recentEvents].sort((a, b) => b.timestamp - a.timestamp);
        
        // 添加事件到列表
        sortedEvents.forEach(event => {
            const eventItem = document.createElement('div');
            eventItem.className = 'event-item';
            
            // 根据事件类型设置样式
            if (event.type.includes('attempt') || event.type.includes('alert')) {
                eventItem.classList.add('event-highlight');
            }
            if (event.type.includes('critical') || event.type.includes('unauthorized')) {
                eventItem.classList.add('event-critical');
            }
            
            const eventTime = new Date(event.timestamp).toLocaleString();
            const eventDetails = JSON.stringify(event.data || {}, null, 2).replace(/[{}]/g, '').replace(/"/g, '');
            
            eventItem.innerHTML = `
                <div class="event-header">
                    <span class="event-type">${formatEventType(event.type)}</span>
                    <span class="event-time">${eventTime}</span>
                </div>
                <div class="event-details">${eventDetails || '无详细信息'}</div>
            `;
            
            eventsList.appendChild(eventItem);
        });
    } catch (error) {
        console.error('加载安全事件失败:', error);
        showToast('加载安全事件失败', 'error');
    }
}

/**
 * 加载安全通道
 */
function loadSecurityChannels() {
    try {
        const channelsList = document.getElementById('channels-list');
        const sessionKeys = window.RollingCodeSecurity.sessionKeys;
        
        // 清空通道列表
        channelsList.innerHTML = '';
        
        if (sessionKeys.size === 0) {
            channelsList.innerHTML = `
                <div class="status-card">
                    <div class="status-row">
                        <span class="status-label">无安全通道</span>
                    </div>
                    <div class="section-description">当前没有活跃的安全通道，请点击上方按钮创建新通道</div>
                </div>
            `;
            return;
        }
        
        // 添加通道到列表
        sessionKeys.forEach((channelInfo, channelId) => {
            const channelItem = document.createElement('div');
            channelItem.className = 'channel-item';
            
            const createdTime = new Date(channelInfo.created).toLocaleString();
            
            channelItem.innerHTML = `
                <div class="channel-info">
                    <div class="channel-id">${channelId}</div>
                    <div class="channel-meta">
                        安全级别: ${channelInfo.securityLevel} | 
                        创建时间: ${createdTime} | 
                        消息数: ${channelInfo.messageCount}
                    </div>
                </div>
                <div class="channel-actions">
                    <button class="btn btn-secondary small-btn" onclick="closeSecurityChannel('${channelId}')">关闭</button>
                </div>
            `;
            
            channelsList.appendChild(channelItem);
        });
    } catch (error) {
        console.error('加载安全通道失败:', error);
        showToast('加载安全通道失败', 'error');
    }
}

/**
 * 创建新安全通道
 */
function createNewChannel() {
    const channelId = document.getElementById('channel-id-input').value.trim();
    const securityLevel = document.getElementById('channel-security-level').value;
    
    if (!channelId) {
        showToast('请输入通道ID', 'warning');
        return;
    }
    
    try {
        // 创建新通道
        window.RollingCodeSecurity.createSecureChannel(channelId, securityLevel);
        
        // 关闭模态框
        document.getElementById('create-channel-modal').style.display = 'none';
        
        // 清空输入
        document.getElementById('channel-id-input').value = '';
        
        // 刷新通道列表
        loadSecurityChannels();
        
        showToast('安全通道创建成功', 'success');
        
        // 记录事件
        logSecurityEvent('security_channel_created', {
            channelId,
            securityLevel
        });
    } catch (error) {
        console.error('创建安全通道失败:', error);
        showToast('创建安全通道失败', 'error');
    }
}

/**
 * 关闭安全通道
 */
function closeSecurityChannel(channelId) {
    try {
        const success = window.RollingCodeSecurity.closeSecureChannel(channelId);
        
        if (success) {
            // 刷新通道列表
            loadSecurityChannels();
            showToast('安全通道已关闭', 'success');
            
            // 记录事件
            logSecurityEvent('security_channel_closed', {
                channelId
            });
        } else {
            showToast('关闭安全通道失败：通道不存在', 'error');
        }
    } catch (error) {
        console.error('关闭安全通道失败:', error);
        showToast('关闭安全通道失败', 'error');
    }
}

/**
 * 生成新滚码
 */
function generateNewCode() {
    try {
        window.RollingCodeSecurity.generateNewCode();
        showToast('新滚码已生成', 'success');
        
        // 记录事件
        logSecurityEvent('new_rolling_code_generated', {});
    } catch (error) {
        console.error('生成新滚码失败:', error);
        showToast('生成新滚码失败', 'error');
    }
}

/**
 * 重置滚码状态
 */
function resetRollingCodeState() {
    if (confirm('确定要重置滚码状态吗？这将清除所有已使用的滚码记录。')) {
        try {
            window.RollingCodeSecurity.resetSecurityState();
            showToast('滚码状态已重置', 'success');
            
            // 刷新安全状态和通道
            loadSecurityStatus();
            loadSecurityChannels();
            
            // 记录事件
            logSecurityEvent('rolling_code_state_reset', {});
        } catch (error) {
            console.error('重置滚码状态失败:', error);
            showToast('重置滚码状态失败', 'error');
        }
    }
}

/**
 * 重置所有安全状态
 */
function resetAllSecurityState() {
    try {
        window.SecurityMechanism.resetSecurityState();
        showToast('所有安全状态已重置', 'success');
        
        // 刷新页面数据
        loadSecurityConfig();
        loadSecurityStatus();
        loadSecurityEvents();
        loadSecurityChannels();
        
        // 记录事件
        logSecurityEvent('all_security_state_reset', {});
    } catch (error) {
        console.error('重置所有安全状态失败:', error);
        showToast('重置所有安全状态失败', 'error');
    }
}

/**
 * 测试安全措施
 */
function testSecurityMeasures() {
    try {
        // 模拟安全事件
        const testEvent = new CustomEvent('securityEvent', {
            detail: {
                type: 'tampering_attempt',
                data: {
                    test: true,
                    source: 'security_config_page',
                    message: '这是一个安全措施测试事件'
                }
            }
        });
        
        window.dispatchEvent(testEvent);
        showToast('安全措施测试已触发，请检查安全事件日志', 'info');
        
        // 延迟刷新事件列表
        setTimeout(() => {
            loadSecurityEvents();
        }, 1000);
    } catch (error) {
        console.error('测试安全措施失败:', error);
        showToast('测试安全措施失败', 'error');
    }
}

/**
 * 清除安全事件
 */
function clearSecurityEvents() {
    if (confirm('确定要清空所有安全事件吗？此操作不可恢复。')) {
        // 注意：实际实现中需要在SecurityMechanism类中添加清除事件的方法
        try {
            // 这里只是模拟清除，实际需要在后端实现
            showToast('安全事件已清空', 'success');
            loadSecurityEvents();
            
            // 记录事件
            logSecurityEvent('security_events_cleared', {});
        } catch (error) {
            console.error('清空安全事件失败:', error);
            showToast('清空安全事件失败', 'error');
        }
    }
}

/**
 * 生成安全报告
 */
function generateSecurityReport() {
    try {
        const report = window.SecurityMechanism.getSecurityReport();
        
        // 将报告转换为JSON字符串
        const reportJson = JSON.stringify(report, null, 2);
        
        // 创建Blob对象
        const blob = new Blob([reportJson], { type: 'application/json' });
        
        // 创建下载链接
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `security-report-${new Date().toISOString().split('T')[0]}.json`;
        
        // 触发下载
        document.body.appendChild(a);
        a.click();
        
        // 清理
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showToast('安全报告已生成', 'success');
        
        // 记录事件
        logSecurityEvent('security_report_generated', {});
    } catch (error) {
        console.error('生成安全报告失败:', error);
        showToast('生成安全报告失败', 'error');
    }
}

/**
 * 重置基本设置
 */
function resetGeneralSettings() {
    if (confirm('确定要重置基本设置到默认值吗？')) {
        document.getElementById('security-enabled').checked = true;
        document.getElementById('level-medium').checked = true;
        document.getElementById('audit-logging').checked = true;
        document.getElementById('automatic-response').checked = true;
        document.getElementById('alert-threshold').value = 5;
        document.getElementById('alert-threshold-value').textContent = 5;
        
        updateSecurityLevelBadge('medium');
        showToast('基本设置已重置', 'success');
    }
}

/**
 * 重置滚码锁设置
 */
function resetRollingCodeSettings() {
    if (confirm('确定要重置滚码锁设置到默认值吗？')) {
        document.getElementById('code-length').value = 16;
        document.getElementById('code-length-value').textContent = 16;
        document.getElementById('rotation-interval').value = 30;
        document.getElementById('rotation-interval-value').textContent = 30;
        document.getElementById('max-code-age').value = 60;
        document.getElementById('max-code-age-value').textContent = 60;
        document.getElementById('encryption-algorithm').value = 'AES-256-GCM';
        document.getElementById('signature-algorithm').value = 'HMAC-SHA256';
        
        showToast('滚码锁设置已重置', 'success');
    }
}

/**
 * 重置高级设置
 */
function resetAdvancedSettings() {
    if (confirm('确定要重置高级设置到默认值吗？')) {
        document.getElementById('key-exchange-method').value = 'ECDHE';
        document.getElementById('rekey-threshold').value = 1000;
        document.getElementById('rekey-threshold-value').textContent = 1000;
        document.getElementById('fallback-mechanism').checked = true;
        document.getElementById('lockout-duration').value = 300;
        document.getElementById('lockout-duration-value').textContent = 300;
        
        showToast('高级设置已重置', 'success');
    }
}

/**
 * 更新安全级别徽章
 */
function updateSecurityLevelBadge(level, element = null) {
    const badgeElement = element || document.getElementById('security-level-badge');
    
    // 移除所有级别类
    badgeElement.classList.remove('badge-low', 'badge-medium', 'badge-high');
    
    // 添加对应级别类
    switch(level) {
        case 'low':
            badgeElement.className = 'security-badge badge-low';
            badgeElement.textContent = '低';
            break;
        case 'medium':
            badgeElement.className = 'security-badge badge-medium';
            badgeElement.textContent = '中';
            break;
        case 'high':
            badgeElement.className = 'security-badge badge-high';
            badgeElement.textContent = '高';
            break;
    }
}

/**
 * 格式化事件类型
 */
function formatEventType(type) {
    // 将下划线转换为空格，首字母大写
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * 记录安全事件
 */
function logSecurityEvent(eventType, eventData = {}) {
    try {
        const securityEvent = new CustomEvent('securityEvent', {
            detail: {
                type: eventType,
                data: eventData
            }
        });
        window.dispatchEvent(securityEvent);
    } catch (error) {
        console.error('记录安全事件失败:', error);
    }
}

/**
 * 显示加载覆盖层
 */
function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
}

/**
 * 隐藏加载覆盖层
 */
function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

/**
 * 显示通知提示
 */
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast-notification');
    
    // 设置消息和类型
    toast.textContent = message;
    
    // 移除所有类型类
    toast.classList.remove('toast-success', 'toast-error', 'toast-warning', 'toast-info');
    
    // 添加对应类型类
    toast.classList.add(`toast-${type}`);
    
    // 显示通知
    toast.classList.add('show');
    
    // 自动隐藏
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 将必要的函数挂载到window对象，使其可在HTML中直接调用
window.closeSecurityChannel = closeSecurityChannel;