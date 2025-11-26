/**
 * MTSCOS 动作拐点记录系统
 * 用于捕获和记录系统中的关键操作和状态变化
 */

class ActionTracker {
    constructor() {
        this.logs = [];
        this.isSending = false;
        this.bufferSize = 10; // 缓冲区大小
        this.sendInterval = 5000; // 自动发送间隔(ms)
        this.lastSendTime = Date.now();
        
        // 初始化事件监听
        this.initEventListeners();
        
        // 设置自动发送定时器
        setInterval(() => this.autoSendLogs(), this.sendInterval);
    }
    
    /**
     * 初始化事件监听器
     */
    initEventListeners() {
        // 捕获页面加载事件
        window.addEventListener('load', () => {
            this.logAction('PAGE_LOADED', {
                url: window.location.href,
                title: document.title
            });
        });
        
        // 捕获页面卸载事件
        window.addEventListener('beforeunload', () => {
            this.logAction('PAGE_UNLOADED', {
                url: window.location.href,
                title: document.title
            });
            this.flushLogs();
        });
        
        // 捕获错误事件
        window.addEventListener('error', (event) => {
            this.logAction('JAVASCRIPT_ERROR', {
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error: event.error ? event.error.stack : null
            });
        });
        
        // 捕获资源加载错误
        window.addEventListener('resourceerror', (event) => {
            this.logAction('RESOURCE_ERROR', {
                target: event.target.src || event.target.href || 'unknown',
                tagName: event.target.tagName
            });
        });
        
        // 捕获用户交互 - 点击事件
        document.addEventListener('click', (event) => {
            // 过滤不重要的点击
            if (this.shouldLogClick(event)) {
                this.logAction('USER_CLICK', {
                    element: this.getElementInfo(event.target),
                    x: event.clientX,
                    y: event.clientY
                });
            }
        }, true);
        
        // 捕获表单提交
        document.addEventListener('submit', (event) => {
            this.logAction('FORM_SUBMIT', {
                formId: event.target.id || 'unknown',
                formAction: event.target.action || 'unknown',
                formMethod: event.target.method || 'get'
            });
        }, true);
    }
    
    /**
     * 检查是否应该记录点击事件
     */
    shouldLogClick(event) {
        const target = event.target;
        
        // 忽略一些不重要的元素点击
        const ignoreTags = ['BODY', 'HTML', 'DIV'];
        if (ignoreTags.includes(target.tagName)) {
            // 如果是容器元素，但没有ID或class，可能不重要
            if (!target.id && !target.className) {
                return false;
            }
        }
        
        // 忽略一些可能频繁触发的点击
        if (target.closest('.no-track-click')) {
            return false;
        }
        
        return true;
    }
    
    /**
     * 获取元素的信息
     */
    getElementInfo(element) {
        return {
            tagName: element.tagName,
            id: element.id || null,
            className: element.className || null,
            text: element.textContent ? element.textContent.trim().substring(0, 100) : null,
            value: element.value || null,
            href: element.href || null,
            name: element.name || null
        };
    }
    
    /**
     * 记录动作拐点
     */
    logAction(actionType, data = {}) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            actionType,
            userAgent: navigator.userAgent,
            sessionId: this.getSessionId(),
            userId: this.getUserId(),
            data
        };
        
        this.logs.push(logEntry);
        
        // 控制台输出用于调试
        console.log('[ACTION TRACKER]', logEntry);
        
        // 检查是否需要发送日志
        if (this.logs.length >= this.bufferSize) {
            this.sendLogs();
        }
        
        // 同时保存到本地存储
        this.saveToLocalStorage();
        
        // 直接保存到local logs文件（通过特殊API）
        this.saveToLocalLogFile(logEntry);
        
        return logEntry;
    }
    
    /**
     * 获取会话ID
     */
    getSessionId() {
        if (!localStorage.getItem('sessionId')) {
            localStorage.setItem('sessionId', this.generateUUID());
        }
        return localStorage.getItem('sessionId');
    }
    
    /**
     * 获取用户ID（如果有）
     */
    getUserId() {
        // 尝试从localStorage或sessionStorage获取用户ID
        return localStorage.getItem('userId') || sessionStorage.getItem('userId') || 'anonymous';
    }
    
    /**
     * 生成UUID
     */
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0,
                  v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    /**
     * 自动发送日志
     */
    autoSendLogs() {
        const now = Date.now();
        if (this.logs.length > 0 && (now - this.lastSendTime) >= this.sendInterval) {
            this.sendLogs();
        }
    }
    
    /**
     * 发送日志到服务器
     */
    sendLogs() {
        if (this.isSending || this.logs.length === 0) {
            return;
        }
        
        this.isSending = true;
        const logsToSend = [...this.logs];
        
        // 在实际环境中，这里应该发送到服务器
        // 由于是本地演示，我们模拟发送过程
        setTimeout(() => {
            console.log('[ACTION TRACKER] 发送日志完成:', logsToSend.length, '条记录');
            
            // 发送成功后清空已发送的日志
            this.logs = [];
            this.lastSendTime = Date.now();
            this.isSending = false;
            
            // 清除本地存储
            this.clearLocalStorage();
        }, 500);
    }
    
    /**
     * 保存日志到本地存储
     */
    saveToLocalStorage() {
        try {
            localStorage.setItem('actionLogs', JSON.stringify(this.logs));
        } catch (e) {
            console.error('[ACTION TRACKER] 保存到本地存储失败:', e);
        }
    }
    
    /**
     * 从本地存储恢复日志
     */
    restoreFromLocalStorage() {
        try {
            const savedLogs = localStorage.getItem('actionLogs');
            if (savedLogs) {
                this.logs = JSON.parse(savedLogs);
                console.log('[ACTION TRACKER] 从本地存储恢复日志:', this.logs.length, '条');
            }
        } catch (e) {
            console.error('[ACTION TRACKER] 从本地存储恢复日志失败:', e);
        }
    }
    
    /**
     * 清除本地存储
     */
    clearLocalStorage() {
        localStorage.removeItem('actionLogs');
    }
    
    /**
     * 保存日志到本地文件（通过特殊API或后端调用）
     */
    saveToLocalLogFile(logEntry) {
        // 在实际环境中，这里应该通过API调用后端保存到日志文件
        // 由于是本地演示，我们使用一种模拟方式
        
        // 创建一个隐藏的iframe来触发日志保存
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.src = `data:text/html,<html><script>
            try {
                // 这里只是模拟，实际环境需要后端支持
                console.log('保存日志到本地文件:', ${JSON.stringify(logEntry).replace(/\\/g, '\\\\')});
            } catch(e) {}
            window.frameElement.remove();
        </script></html>`;
        document.body.appendChild(iframe);
    }
    
    /**
     * 立即刷新所有日志
     */
    flushLogs() {
        this.sendLogs();
    }
    
    /**
     * 手动记录自定义动作
     */
    recordCustomAction(actionType, details = {}) {
        return this.logAction('CUSTOM_ACTION_' + actionType, details);
    }
    
    /**
     * 记录系统状态变更
     */
    recordStateChange(stateType, oldState, newState) {
        return this.logAction('STATE_CHANGE', {
            stateType,
            oldState,
            newState
        });
    }
    
    /**
     * 获取当前日志数量
     */
    getLogCount() {
        return this.logs.length;
    }
}

// 初始化并导出单例
const actionTracker = new ActionTracker();

// 暴露给全局作用域，方便其他脚本使用
window.ActionTracker = actionTracker;

// 提供模块导出
try {
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = actionTracker;
    }
} catch (e) {
    // 忽略模块导出错误，在浏览器环境中正常工作
}
