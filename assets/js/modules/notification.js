/**
 * 系统通知模块
 * 功能：处理各种系统通知、消息提示、告警等
 */

const NotificationModule = {
    // 通知容器
    container: null,
    
    // 通知配置
    config: {
        timeout: 5000, // 默认通知显示时间
        maxVisible: 5, // 最多同时显示的通知数量
        position: 'top-right' // 通知位置：top-right, top-left, bottom-right, bottom-left, top-center, bottom-center
    },
    
    // 活跃的通知列表
    activeNotifications: [],
    
    // 通知类型和对应的样式
    notificationTypes: {
        info: 'notification-info',
        success: 'notification-success',
        warning: 'notification-warning',
        error: 'notification-error',
        system: 'notification-system'
    },
    
    // 初始化通知模块
    initialize() {
        // 创建通知容器
        this.createContainer();
        
        // 从配置加载设置
        this.loadConfig();
        
        console.log('通知模块初始化完成');
    },
    
    // 创建通知容器
    createContainer() {
        // 检查是否已存在容器
        if (document.getElementById('notification-container')) {
            this.container = document.getElementById('notification-container');
            return;
        }
        
        // 创建新容器
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.className = `notification-container ${this.config.position}`;
        document.body.appendChild(this.container);
        
        // 添加必要的CSS样式
        this.addStyles();
    },
    
    // 添加通知样式
    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* 通知容器样式 */
            .notification-container {
                position: fixed;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 12px;
                padding: 16px;
                max-width: 400px;
                width: 100%;
            }
            
            /* 位置样式 */
            .notification-container.top-right {
                top: 0;
                right: 0;
                align-items: flex-end;
            }
            
            .notification-container.top-left {
                top: 0;
                left: 0;
                align-items: flex-start;
            }
            
            .notification-container.bottom-right {
                bottom: 0;
                right: 0;
                align-items: flex-end;
            }
            
            .notification-container.bottom-left {
                bottom: 0;
                left: 0;
                align-items: flex-start;
            }
            
            .notification-container.top-center {
                top: 0;
                left: 50%;
                transform: translateX(-50%);
                align-items: center;
            }
            
            .notification-container.bottom-center {
                bottom: 0;
                left: 50%;
                transform: translateX(-50%);
                align-items: center;
            }
            
            /* 通知项样式 */
            .notification {
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                padding: 16px 20px;
                min-width: 300px;
                max-width: 100%;
                display: flex;
                align-items: flex-start;
                gap: 12px;
                animation: notificationSlideIn 0.3s ease-out forwards;
                border-left: 4px solid #ccc;
                position: relative;
                opacity: 0;
                transform: translateX(100%);
            }
            
            @keyframes notificationSlideIn {
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            /* 通知滑出动画 */
            .notification.slide-out {
                animation: notificationSlideOut 0.3s ease-in forwards;
            }
            
            @keyframes notificationSlideOut {
                from {
                    opacity: 1;
                    transform: translateX(0);
                }
                to {
                    opacity: 0;
                    transform: translateX(100%);
                }
            }
            
            /* 通知类型样式 */
            .notification.notification-info {
                border-left-color: #3b82f6;
            }
            
            .notification.notification-success {
                border-left-color: #10b981;
            }
            
            .notification.notification-warning {
                border-left-color: #f59e0b;
            }
            
            .notification.notification-error {
                border-left-color: #ef4444;
            }
            
            .notification.notification-system {
                border-left-color: #8b5cf6;
            }
            
            /* 通知内容样式 */
            .notification-content {
                flex: 1;
                overflow: hidden;
            }
            
            .notification-title {
                font-weight: 600;
                margin-bottom: 4px;
                font-size: 14px;
                color: #1f2937;
            }
            
            .notification-message {
                font-size: 14px;
                color: #6b7280;
                line-height: 1.4;
                word-break: break-word;
            }
            
            /* 图标样式 */
            .notification-icon {
                font-size: 20px;
                flex-shrink: 0;
                margin-top: 2px;
            }
            
            .notification-icon.info {
                color: #3b82f6;
            }
            
            .notification-icon.success {
                color: #10b981;
            }
            
            .notification-icon.warning {
                color: #f59e0b;
            }
            
            .notification-icon.error {
                color: #ef4444;
            }
            
            .notification-icon.system {
                color: #8b5cf6;
            }
            
            /* 关闭按钮样式 */
            .notification-close {
                background: none;
                border: none;
                font-size: 16px;
                cursor: pointer;
                color: #9ca3af;
                padding: 4px;
                border-radius: 4px;
                flex-shrink: 0;
                transition: all 0.2s;
            }
            
            .notification-close:hover {
                background-color: #f3f4f6;
                color: #6b7280;
            }
            
            /* 进度条样式 */
            .notification-progress {
                position: absolute;
                bottom: 0;
                left: 0;
                height: 3px;
                background-color: rgba(0, 0, 0, 0.1);
                width: 100%;
                border-radius: 0 0 8px 8px;
            }
            
            .notification-progress-bar {
                height: 100%;
                background-color: #3b82f6;
                transition: width 0.1s linear;
            }
            
            .notification.notification-success .notification-progress-bar {
                background-color: #10b981;
            }
            
            .notification.notification-warning .notification-progress-bar {
                background-color: #f59e0b;
            }
            
            .notification.notification-error .notification-progress-bar {
                background-color: #ef4444;
            }
            
            .notification.notification-system .notification-progress-bar {
                background-color: #8b5cf6;
            }
            
            /* 响应式设计 */
            @media (max-width: 768px) {
                .notification-container {
                    max-width: 100%;
                    width: calc(100% - 32px);
                    padding: 16px;
                }
                
                .notification-container.top-right,
                .notification-container.top-left,
                .notification-container.bottom-right,
                .notification-container.bottom-left,
                .notification-container.top-center,
                .notification-container.bottom-center {
                    left: 0;
                    transform: none;
                    right: 0;
                    align-items: stretch;
                }
                
                .notification {
                    min-width: auto;
                    width: 100%;
                }
            }
        `;
        document.head.appendChild(style);
    },
    
    // 加载配置
    loadConfig() {
        try {
            // 尝试从系统配置获取设置
            if (window.getConfig) {
                const timeout = window.getConfig('ui.notificationTimeout', 5000);
                if (timeout) {
                    this.config.timeout = timeout;
                }
            }
            
            // 从本地存储加载用户自定义设置
            const savedConfig = localStorage.getItem('notification_config');
            if (savedConfig) {
                const parsedConfig = JSON.parse(savedConfig);
                Object.assign(this.config, parsedConfig);
            }
        } catch (error) {
            console.error('加载通知配置失败:', error);
        }
    },
    
    // 保存配置
    saveConfig() {
        try {
            localStorage.setItem('notification_config', JSON.stringify(this.config));
        } catch (error) {
            console.error('保存通知配置失败:', error);
        }
    },
    
    // 获取通知图标
    getNotificationIcon(type) {
        const icons = {
            info: 'ℹ️',
            success: '✅',
            warning: '⚠️',
            error: '❌',
            system: '🔔'
        };
        
        return icons[type] || icons.info;
    },
    
    // 获取通知标题
    getNotificationTitle(type) {
        const titles = {
            info: '信息',
            success: '成功',
            warning: '警告',
            error: '错误',
            system: '系统通知'
        };
        
        return titles[type] || titles.info;
    },
    
    // 添加通知
    addNotification(message, type = 'info', options = {}) {
        try {
            // 确保容器存在
            if (!this.container) {
                this.createContainer();
            }
            
            // 生成唯一ID
            const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            
            // 合并选项
            const notificationOptions = {
                timeout: this.config.timeout,
                title: options.title || this.getNotificationTitle(type),
                persistent: options.persistent || false,
                onClose: options.onClose || null,
                ...options
            };
            
            // 创建通知元素
            const notification = this.createNotificationElement(id, message, type, notificationOptions);
            
            // 添加到容器
            this.container.appendChild(notification);
            
            // 添加到活跃列表
            this.activeNotifications.push({
                id,
                element: notification,
                timeoutId: null
            });
            
            // 管理通知数量
            this.manageNotificationCount();
            
            // 设置自动关闭（如果不是持久通知）
            if (!notificationOptions.persistent && notificationOptions.timeout > 0) {
                this.scheduleNotificationClose(id, notificationOptions.timeout);
                
                // 添加进度条动画
                if (notificationOptions.showProgress !== false) {
                    this.addProgressAnimation(notification, notificationOptions.timeout);
                }
            }
            
            // 记录通知事件
            this.logNotification(id, message, type);
            
            return id;
        } catch (error) {
            console.error('添加通知失败:', error);
            return null;
        }
    },
    
    // 创建通知元素
    createNotificationElement(id, message, type, options) {
        const notification = document.createElement('div');
        notification.id = id;
        notification.className = `notification ${this.notificationTypes[type] || ''}`;
        
        // 创建内容结构
        notification.innerHTML = `
            <div class="notification-icon ${type}">${this.getNotificationIcon(type)}</div>
            <div class="notification-content">
                <div class="notification-title">${options.title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" title="关闭">×</button>
            ${options.showProgress !== false ? '<div class="notification-progress"><div class="notification-progress-bar" style="width: 100%"></div></div>' : ''}
        `;
        
        // 添加关闭按钮事件
        const closeButton = notification.querySelector('.notification-close');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                this.removeNotification(id);
            });
        }
        
        // 添加点击事件
        if (options.onClick) {
            notification.addEventListener('click', (e) => {
                // 排除关闭按钮的点击
                if (!e.target.closest('.notification-close')) {
                    options.onClick();
                }
            });
        }
        
        return notification;
    },
    
    // 管理通知数量
    manageNotificationCount() {
        if (this.activeNotifications.length <= this.config.maxVisible) {
            return;
        }
        
        // 移除最旧的通知
        const notificationsToRemove = this.activeNotifications.length - this.config.maxVisible;
        for (let i = 0; i < notificationsToRemove; i++) {
            const oldNotification = this.activeNotifications[i];
            if (oldNotification && oldNotification.id) {
                this.removeNotification(oldNotification.id);
            }
        }
    },
    
    // 设置通知自动关闭
    scheduleNotificationClose(id, timeout) {
        const timeoutId = setTimeout(() => {
            this.removeNotification(id);
        }, timeout);
        
        // 更新活跃通知列表中的timeoutId
        const notificationIndex = this.activeNotifications.findIndex(n => n.id === id);
        if (notificationIndex !== -1) {
            this.activeNotifications[notificationIndex].timeoutId = timeoutId;
        }
    },
    
    // 添加进度条动画
    addProgressAnimation(notification, duration) {
        const progressBar = notification.querySelector('.notification-progress-bar');
        if (!progressBar) return;
        
        // 使用requestAnimationFrame进行平滑动画
        const startTime = performance.now();
        
        function updateProgress(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.max(0, 1 - (elapsed / duration));
            
            progressBar.style.width = `${progress * 100}%`;
            
            if (progress > 0 && !notification.classList.contains('slide-out')) {
                requestAnimationFrame(updateProgress);
            }
        }
        
        requestAnimationFrame(updateProgress);
    },
    
    // 移除通知
    removeNotification(id) {
        const notificationIndex = this.activeNotifications.findIndex(n => n.id === id);
        if (notificationIndex === -1) return;
        
        const notificationData = this.activeNotifications[notificationIndex];
        
        // 清除定时器
        if (notificationData.timeoutId) {
            clearTimeout(notificationData.timeoutId);
        }
        
        // 添加滑出动画
        const notification = notificationData.element;
        if (notification) {
            notification.classList.add('slide-out');
            
            // 等待动画完成后移除元素
            setTimeout(() => {
                if (notification.parentNode === this.container) {
                    this.container.removeChild(notification);
                }
            }, 300);
        }
        
        // 从活跃列表中移除
        this.activeNotifications.splice(notificationIndex, 1);
        
        // 调用关闭回调
        if (notificationData.options && typeof notificationData.options.onClose === 'function') {
            notificationData.options.onClose(id);
        }
    },
    
    // 清除所有通知
    clearAllNotifications() {
        this.activeNotifications.forEach(notification => {
            if (notification.timeoutId) {
                clearTimeout(notification.timeoutId);
            }
            
            if (notification.element && notification.element.parentNode === this.container) {
                this.container.removeChild(notification.element);
            }
        });
        
        this.activeNotifications = [];
    },
    
    // 获取活跃通知数量
    getActiveNotificationsCount() {
        return this.activeNotifications.length;
    },
    
    // 记录通知事件
    logNotification(id, message, type) {
        try {
            const logEntry = {
                timestamp: new Date().toISOString(),
                notificationId: id,
                type: type,
                message: message,
                userAgent: navigator.userAgent
            };
            
            console.log('通知:', logEntry);
            
            // 实际应用中应该发送到服务器记录
            // this.sendNotificationLog(logEntry);
        } catch (error) {
            console.error('记录通知日志失败:', error);
        }
    },
    
    // 发送通知日志到服务器（模拟）
    sendNotificationLog(logEntry) {
        // 实际应用中应该实现真实的日志发送
        if (window.getApiEndpoint) {
            const endpoint = window.getApiEndpoint('logs.user');
            if (endpoint) {
                // 使用fetch或其他API发送日志
                // fetch(endpoint, {
                //     method: 'POST',
                //     headers: {
                //         'Content-Type': 'application/json'
                //     },
                //     body: JSON.stringify(logEntry)
                // });
            }
        }
    },
    
    // 显示成功通知
    showSuccess(message, options = {}) {
        return this.addNotification(message, 'success', options);
    },
    
    // 显示错误通知
    showError(message, options = {}) {
        // 错误通知默认显示时间更长
        options.timeout = options.timeout || 8000;
        return this.addNotification(message, 'error', options);
    },
    
    // 显示警告通知
    showWarning(message, options = {}) {
        options.timeout = options.timeout || 6000;
        return this.addNotification(message, 'warning', options);
    },
    
    // 显示信息通知
    showInfo(message, options = {}) {
        return this.addNotification(message, 'info', options);
    },
    
    // 显示系统通知
    showSystem(message, options = {}) {
        options.persistent = options.persistent !== undefined ? options.persistent : true;
        return this.addNotification(message, 'system', options);
    },
    
    // 更改通知位置
    setPosition(position) {
        const validPositions = ['top-right', 'top-left', 'bottom-right', 'bottom-left', 'top-center', 'bottom-center'];
        
        if (validPositions.includes(position)) {
            // 移除旧的位置类
            this.validPositions.forEach(pos => {
                this.container.classList.remove(pos);
            });
            
            // 添加新的位置类
            this.container.classList.add(position);
            this.config.position = position;
            this.saveConfig();
            
            return true;
        }
        
        return false;
    },
    
    // 设置默认超时时间
    setDefaultTimeout(timeout) {
        if (typeof timeout === 'number' && timeout >= 0) {
            this.config.timeout = timeout;
            this.saveConfig();
            return true;
        }
        return false;
    },
    
    // 设置最大可见通知数
    setMaxVisible(max) {
        if (typeof max === 'number' && max >= 1 && max <= 20) {
            this.config.maxVisible = max;
            this.manageNotificationCount();
            this.saveConfig();
            return true;
        }
        return false;
    }
};

// 初始化函数
function initializeNotifications() {
    NotificationModule.initialize();
}

// 导出全局方法
function addNotification(message, type = 'info', options = {}) {
    return NotificationModule.addNotification(message, type, options);
}

function showSuccessNotification(message, options = {}) {
    return NotificationModule.showSuccess(message, options);
}

function showErrorNotification(message, options = {}) {
    return NotificationModule.showError(message, options);
}

function showWarningNotification(message, options = {}) {
    return NotificationModule.showWarning(message, options);
}

function showInfoNotification(message, options = {}) {
    return NotificationModule.showInfo(message, options);
}

function showSystemNotification(message, options = {}) {
    return NotificationModule.showSystem(message, options);
}

function clearAllNotifications() {
    return NotificationModule.clearAllNotifications();
}

// 暴露API到全局
window.NotificationModule = NotificationModule;
window.initializeNotifications = initializeNotifications;
window.addNotification = addNotification;
window.showSuccessNotification = showSuccessNotification;
window.showErrorNotification = showErrorNotification;
window.showWarningNotification = showWarningNotification;
window.showInfoNotification = showInfoNotification;
window.showSystemNotification = showSystemNotification;
window.clearAllNotifications = clearAllNotifications;

// 当文档加载完成时初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeNotifications);
} else {
    initializeNotifications();
}