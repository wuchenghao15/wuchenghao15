/**
 * MTSCOS UI交互模块
 * 处理用户界面交互和DOM操作
 */
class MTSCOSUI {
    constructor() {
        this.currentTab = 'chat';
        this.notificationQueue = [];
        this.maxNotifications = 5;
        this.init();
    }

    /**
     * 初始化UI模块
     */
    init() {
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        this.setupTextareaAutoResize();
        this.addLog('info', 'UI模块', 'UI交互模块初始化完成');
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 标签页切换
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.target.getAttribute('data-tab') || 
                               e.target.getAttribute('onclick')?.match(/switchTab\('(.+?)'\)/)?.[1];
                if (tabName) {
                    this.switchTab(tabName);
                }
            });
        });

        // AI建议按钮
        const suggestBtn = document.querySelector('.ai-suggest-btn');
        if (suggestBtn) {
            suggestBtn.addEventListener('click', () => this.getAISuggestion());
        }

        // 页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseMonitoring();
            } else {
                this.resumeMonitoring();
            }
        });

        // 页面卸载前清理
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }

    /**
     * 设置键盘快捷键
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case '1':
                        e.preventDefault();
                        this.switchTab('chat');
                        break;
                    case '2':
                        e.preventDefault();
                        this.switchTab('code');
                        break;
                    case '3':
                        e.preventDefault();
                        this.switchTab('analyze');
                        break;
                    case '4':
                        e.preventDefault();
                        this.switchTab('translate');
                        break;
                    case '5':
                        e.preventDefault();
                        this.switchTab('summarize');
                        break;
                    case 'Enter':
                        e.preventDefault();
                        this.executeCurrentTabAction();
                        break;
                }
            }
        });
    }

    /**
     * 设置文本框自动调整高度
     */
    setupTextareaAutoResize() {
        const textareas = document.querySelectorAll('textarea');
        textareas.forEach(textarea => {
            textarea.addEventListener('input', () => {
                this.autoResizeTextarea(textarea);
            });
            
            // 初始调整
            this.autoResizeTextarea(textarea);
        });
    }

    /**
     * 自动调整文本框高度
     */
    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.max(140, textarea.scrollHeight) + 'px';
    }

    /**
     * 切换标签页
     */
    switchTab(tabName) {
        // 更新标签状态
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[onclick="switchTab('${tabName}')"]`)?.classList.add('active');

        // 更新内容区域
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}Tab`)?.classList.add('active');

        // 隐藏响应区域
        const responseSection = document.getElementById('responseSection');
        if (responseSection) {
            responseSection.style.display = 'none';
        }

        this.currentTab = tabName;
        this.addLog('info', 'UI模块', `切换到${tabName}标签页`);
    }

    /**
     * 执行当前标签页的操作
     */
    executeCurrentTabAction() {
        const actions = {
            'chat': () => this.sendChatMessage(),
            'code': () => this.generateCode(),
            'analyze': () => this.analyzeText(),
            'translate': () => this.translateText(),
            'summarize': () => this.summarizeText()
        };

        const action = actions[this.currentTab];
        if (action) {
            action();
        }
    }

    /**
     * 设置聊天提示
     */
    setChatPrompt(prompt) {
        const chatMessage = document.getElementById('chatMessage');
        if (chatMessage) {
            chatMessage.value = prompt;
            chatMessage.focus();
        }
    }

    /**
     * 设置代码提示
     */
    setCodePrompt(prompt) {
        const codeDescription = document.getElementById('codeDescription');
        if (codeDescription) {
            codeDescription.value = prompt;
            codeDescription.focus();
        }
    }

    /**
     * 清空当前输入
     */
    clearCurrentInput() {
        const activeTab = document.querySelector('.tab-content.active');
        const textarea = activeTab?.querySelector('textarea');
        if (textarea) {
            textarea.value = '';
            textarea.focus();
        }
    }

    /**
     * 显示加载状态
     */
    showLoading(loadingId) {
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) {
            loadingElement.classList.add('show');
        }
    }

    /**
     * 隐藏加载状态
     */
    hideLoading(loadingId) {
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) {
            loadingElement.classList.remove('show');
        }
    }

    /**
     * 显示响应结果
     */
    showResponse(responseId, content, isError = false) {
        const responseDiv = document.getElementById(responseId);
        if (!responseDiv) return;

        const className = isError ? 'error' : 'response-section';
        const title = isError ? '❌ 错误' : '✅ 响应结果';
        
        responseDiv.innerHTML = `
            <div class="${className}">
                <h4>${title}:</h4>
                <div class="response-content">${content}</div>
                <div style="margin-top: 12px;">
                    <button class="btn" onclick="window.mtscosUI.copyToClipboard('${responseId}')" style="padding: 6px 12px; font-size: 0.9em;">
                        <i class="fas fa-copy"></i> 复制
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * 复制到剪贴板
     */
    async copyToClipboard(responseId) {
        const contentElement = document.querySelector(`#${responseId} .response-content`);
        if (!contentElement) return;

        const content = contentElement.textContent;
        
        try {
            await navigator.clipboard.writeText(content);
            this.showNotification('内容已复制到剪贴板', 'success');
        } catch (err) {
            this.showNotification('复制失败: ' + err.message, 'error');
        }
    }

    /**
     * 显示通知
     */
    showNotification(message, type = 'info', duration = 3000) {
        // 检查通知队列
        if (this.notificationQueue.length >= this.maxNotifications) {
            this.removeOldestNotification();
        }

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)}"></i>
            <span>${message}</span>
        `;
        
        // 添加样式
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: this.getNotificationColor(type),
            color: 'white',
            padding: '16px 20px',
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            zIndex: '10000',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            maxWidth: '300px',
            animation: 'slideInRight 0.3s ease'
        });
        
        document.body.appendChild(notification);
        this.notificationQueue.push(notification);
        
        // 自动移除
        setTimeout(() => {
            this.removeNotification(notification);
        }, duration);
    }

    /**
     * 移除通知
     */
    removeNotification(notification) {
        if (notification && notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
                const index = this.notificationQueue.indexOf(notification);
                if (index > -1) {
                    this.notificationQueue.splice(index, 1);
                }
            }, 300);
        }
    }

    /**
     * 移除最旧的通知
     */
    removeOldestNotification() {
        if (this.notificationQueue.length > 0) {
            this.removeNotification(this.notificationQueue[0]);
        }
    }

    /**
     * 获取通知图标
     */
    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    /**
     * 获取通知颜色
     */
    getNotificationColor(type) {
        const colors = {
            success: 'var(--success-color)',
            error: 'var(--error-color)',
            warning: 'var(--warning-color)',
            info: '#667eea'
        };
        return colors[type] || '#667eea';
    }

    /**
     * 添加日志条目
     */
    addLog(level, module, message) {
        const logsContainer = document.getElementById('logsContainer');
        if (!logsContainer) return;

        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${level}`;
        
        const timestamp = new Date().toLocaleTimeString('zh-CN');
        
        logEntry.innerHTML = `
            <div class="log-timestamp">${timestamp} [${module}]</div>
            <div class="log-message">${message}</div>
        `;
        
        // 添加到顶部
        logsContainer.insertBefore(logEntry, logsContainer.firstChild);
        
        // 限制日志条目数量
        const logEntries = logsContainer.querySelectorAll('.log-entry');
        if (logEntries.length > 20) {
            logsContainer.removeChild(logEntries[logEntries.length - 1]);
        }
    }

    /**
     * 暂停监控
     */
    pauseMonitoring() {
        if (window.deepseekMonitor) {
            window.deepseekMonitor.stop();
        }
    }

    /**
     * 恢复监控
     */
    resumeMonitoring() {
        if (window.deepseekMonitor) {
            window.deepseekMonitor.start();
        }
    }

    /**
     * 清理资源
     */
    cleanup() {
        this.pauseMonitoring();
        this.notificationQueue.forEach(notification => {
            if (notification.parentNode) {
                document.body.removeChild(notification);
            }
        });
        this.notificationQueue = [];
    }

    // API调用方法（将在后续实现中连接到apiService）
    async sendChatMessage() {
        const message = document.getElementById('chatMessage')?.value.trim();
        if (!message) {
            this.showNotification('请输入消息内容', 'warning');
            return;
        }

        this.showLoading('chatLoading');
        
        try {
            const data = await window.apiService.chat(message);
            if (data.success) {
                this.showResponse('chatResponse', data.response);
            } else {
                this.showResponse('chatResponse', data.error || data.message, true);
            }
        } catch (error) {
            this.showResponse('chatResponse', error.message, true);
        } finally {
            this.hideLoading('chatLoading');
        }
    }

    async generateCode() {
        const description = document.getElementById('codeDescription')?.value.trim();
        const language = document.getElementById('codeLanguage')?.value || 'javascript';
        
        if (!description) {
            this.showNotification('请输入代码描述', 'warning');
            return;
        }

        this.showLoading('codeLoading');
        
        try {
            const data = await window.apiService.generateCode(description, language);
            if (data.success) {
                this.showResponse('codeResponse', `// 语言: ${language}\n\n${data.code}`);
            } else {
                this.showResponse('codeResponse', data.error || data.message, true);
            }
        } catch (error) {
            this.showResponse('codeResponse', error.message, true);
        } finally {
            this.hideLoading('codeLoading');
        }
    }

    async analyzeText() {
        const text = document.getElementById('analyzeText')?.value.trim();
        
        if (!text) {
            this.showNotification('请输入要分析的文本', 'warning');
            return;
        }

        this.showLoading('analyzeLoading');
        
        try {
            const data = await window.apiService.analyzeText(text);
            if (data.success) {
                this.showResponse('analyzeResponse', data.analysis);
            } else {
                this.showResponse('analyzeResponse', data.error || data.message, true);
            }
        } catch (error) {
            this.showResponse('analyzeResponse', error.message, true);
        } finally {
            this.hideLoading('analyzeLoading');
        }
    }

    async translateText() {
        const text = document.getElementById('translateText')?.value.trim();
        const targetLanguage = document.getElementById('targetLanguage')?.value.trim();
        
        if (!text || !targetLanguage) {
            this.showNotification('请输入要翻译的文本和目标语言', 'warning');
            return;
        }

        this.showLoading('translateLoading');
        
        try {
            const data = await window.apiService.translateText(text, targetLanguage);
            if (data.success) {
                this.showResponse('translateResponse', 
                    `原文 (${data.originalText?.substring(0, 100)}...):\n\n${data.translatedText}\n\n目标语言: ${data.targetLanguage}`);
            } else {
                this.showResponse('translateResponse', data.error || data.message, true);
            }
        } catch (error) {
            this.showResponse('translateResponse', error.message, true);
        } finally {
            this.hideLoading('translateLoading');
        }
    }

    async summarizeText() {
        const text = document.getElementById('summarizeText')?.value.trim();
        const maxLength = parseInt(document.getElementById('maxLength')?.value) || 200;
        
        if (!text) {
            this.showNotification('请输入要摘要的文本', 'warning');
            return;
        }

        this.showLoading('summarizeLoading');
        
        try {
            const data = await window.apiService.summarizeText(text, maxLength);
            if (data.success) {
                this.showResponse('summarizeResponse', 
                    `摘要 (${data.summary?.length || 0}/${maxLength} 字符):\n\n${data.summary}`);
            } else {
                this.showResponse('summarizeResponse', data.error || data.message, true);
            }
        } catch (error) {
            this.showResponse('summarizeResponse', error.message, true);
        } finally {
            this.hideLoading('summarizeLoading');
        }
    }

    async getAISuggestion() {
        const suggestBtn = document.querySelector('.ai-suggest-btn');
        if (suggestBtn) {
            suggestBtn.classList.remove('pulse');
        }
        
        this.showNotification('AI正在分析您的使用习惯...', 'info');

        try {
            const data = await window.apiService.getAISuggestion(this.currentTab);
            if (data.success) {
                this.showNotification(data.suggestion, 'success');
                
                if (data.action) {
                    this.executeAIAction(data.action);
                }
            } else {
                throw new Error(data.error || '获取建议失败');
            }
        } catch (error) {
            this.showNotification('暂时无法获取AI建议: ' + error.message, 'error');
        } finally {
            setTimeout(() => {
                if (suggestBtn) {
                    suggestBtn.classList.add('pulse');
                }
            }, 5000);
        }
    }

    executeAIAction(action) {
        switch(action.type) {
            case 'switch_tab':
                this.switchTab(action.tab);
                break;
            case 'set_prompt':
                if (action.tab === 'chat') this.setChatPrompt(action.prompt);
                else if (action.tab === 'code') this.setCodePrompt(action.prompt);
                break;
            case 'optimize_ui':
                this.optimizeUI(action.suggestions);
                break;
        }
    }

    optimizeUI(suggestions) {
        suggestions.forEach(suggestion => {
            switch(suggestion) {
                case 'increase_font_size':
                    document.documentElement.style.fontSize = '18px';
                    break;
                case 'dark_mode':
                    document.body.classList.add('dark-mode');
                    break;
                case 'compact_layout':
                    document.querySelector('.container')?.setAttribute('style', 'max-width: 1000px');
                    break;
            }
        });
        this.showNotification('UI已根据AI建议优化', 'success');
    }
}

// 创建全局实例
const mtscosUI = new MTSCOSUI();

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MTSCOSUI, mtscosUI };
} else {
    window.MTSCOSUI = MTSCOSUI;
    window.mtscosUI = mtscosUI;
}