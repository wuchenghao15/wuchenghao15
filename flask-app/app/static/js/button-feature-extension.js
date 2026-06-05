/**
 * 按钮功能扩展库 - Button Feature Extension Library
 * 为硬件管理系统提供丰富的按钮功能
 */

class ButtonFeatureExtension {
    constructor() {
        this.buttons = [];
        this.loadingStates = new Map();
        this.confirmDialogs = new Map();
        this.init();
    }

    /**
     * 初始化按钮功能扩展
     */
    init() {
        console.log('🔘 按钮功能扩展初始化中...');
        this.setupGlobalEventListeners();
        this.enhanceExistingButtons();
        console.log('✅ 按钮功能扩展初始化完成');
    }

    /**
     * 设置全局事件监听器
     */
    setupGlobalEventListeners() {
        document.addEventListener('click', (e) => {
            const button = e.target.closest('button, .btn, [data-btn-type]');
            if (button) {
                this.handleButtonClick(button, e);
            }
        });
    }

    /**
     * 处理按钮点击
     */
    handleButtonClick(button, event) {
        const btnType = button.dataset.btnType;
        
        switch(btnType) {
            case 'loading':
                this.handleLoadingButton(button);
                break;
            case 'confirm':
                event.preventDefault();
                this.handleConfirmButton(button);
                break;
            case 'toggle':
                this.handleToggleButton(button);
                break;
            case 'copy':
                this.handleCopyButton(button);
                break;
            case 'dropdown':
                this.handleDropdownButton(button);
                break;
            default:
                this.handleDefaultButton(button);
        }
    }

    /**
     * 处理加载按钮
     */
    handleLoadingButton(button) {
        if (this.loadingStates.get(button)) return;
        
        const originalText = button.innerHTML;
        const loadingText = button.dataset.loadingText || '加载中...';
        
        this.loadingStates.set(button, true);
        button.disabled = true;
        button.classList.add('btn-loading');
        
        const loadingIcon = this.createLoadingIcon();
        button.innerHTML = '';
        button.appendChild(loadingIcon);
        button.appendChild(document.createTextNode(' ' + loadingText));
        
        const duration = parseInt(button.dataset.loadingDuration) || 2000;
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
            button.classList.remove('btn-loading');
            this.loadingStates.delete(button);
            
            if (button.dataset.onComplete) {
                const callback = new Function(button.dataset.onComplete);
                callback.call(button);
            }
        }, duration);
    }

    /**
     * 处理确认按钮
     */
    handleConfirmButton(button) {
        const confirmMessage = button.dataset.confirmMessage || '确定要执行此操作吗？';
        const confirmTitle = button.dataset.confirmTitle || '确认操作';
        const confirmYes = button.dataset.confirmYes || '确定';
        const confirmNo = button.dataset.confirmNo || '取消';
        
        this.showConfirmDialog({
            title: confirmTitle,
            message: confirmMessage,
            yesText: confirmYes,
            noText: confirmNo,
            onYes: () => {
                if (button.dataset.href) {
                    window.location.href = button.dataset.href;
                }
                if (button.dataset.callback) {
                    const callback = new Function(button.dataset.callback);
                    callback.call(button);
                }
            }
        });
    }

    /**
     * 处理切换按钮
     */
    handleToggleButton(button) {
        const isActive = button.classList.toggle('btn-toggled');
        const toggleGroup = button.dataset.toggleGroup;
        
        if (toggleGroup) {
            document.querySelectorAll(`[data-toggle-group="${toggleGroup}"]`).forEach(btn => {
                if (btn !== button) {
                    btn.classList.remove('btn-toggled');
                }
            });
        }
        
        button.dataset.state = isActive ? 'on' : 'off';
        
        if (button.dataset.onToggle) {
            const callback = new Function('state', button.dataset.onToggle);
            callback.call(button, isActive);
        }
    }

    /**
     * 处理复制按钮
     */
    handleCopyButton(button) {
        const textToCopy = button.dataset.copyText || 
                          document.querySelector(button.dataset.copyTarget)?.textContent ||
                          '';
        
        if (!textToCopy) {
            this.showToast('没有可复制的内容', 'error');
            return;
        }
        
        navigator.clipboard.writeText(textToCopy).then(() => {
            const originalText = button.innerHTML;
            button.innerHTML = this.createCheckIcon() + ' 已复制';
            button.classList.add('btn-success');
            
            setTimeout(() => {
                button.innerHTML = originalText;
                button.classList.remove('btn-success');
            }, 2000);
        }).catch(() => {
            this.showToast('复制失败', 'error');
        });
    }

    /**
     * 处理下拉按钮
     */
    handleDropdownButton(button) {
        const dropdown = button.nextElementSibling;
        if (dropdown && dropdown.classList.contains('btn-dropdown-menu')) {
            dropdown.classList.toggle('show');
            
            document.addEventListener('click', (e) => {
                if (!button.contains(e.target) && !dropdown.contains(e.target)) {
                    dropdown.classList.remove('show');
                }
            }, { once: true });
        }
    }

    /**
     * 处理默认按钮
     */
    handleDefaultButton(button) {
        button.classList.add('btn-clicked');
        setTimeout(() => {
            button.classList.remove('btn-clicked');
        }, 150);
    }

    /**
     * 显示确认对话框
     */
    showConfirmDialog(options) {
        const dialogId = 'confirm-dialog-' + Date.now();
        
        const dialogHTML = `
            <div id="${dialogId}" class="confirm-dialog-overlay">
                <div class="confirm-dialog">
                    <div class="confirm-dialog-header">
                        <h4>${options.title}</h4>
                        <button class="confirm-dialog-close" onclick="ButtonExt.closeDialog('${dialogId}')">
                            ${this.createCloseIcon()}
                        </button>
                    </div>
                    <div class="confirm-dialog-body">
                        <p>${options.message}</p>
                    </div>
                    <div class="confirm-dialog-footer">
                        <button class="btn btn-secondary" onclick="ButtonExt.closeDialog('${dialogId}')">
                            ${options.noText}
                        </button>
                        <button class="btn btn-primary" onclick="ButtonExt.confirmAction('${dialogId}')">
                            ${options.yesText}
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', dialogHTML);
        
        const dialog = document.getElementById(dialogId);
        this.confirmDialogs.set(dialogId, {
            element: dialog,
            onYes: options.onYes
        });
        
        requestAnimationFrame(() => {
            dialog.classList.add('show');
        });
    }

    /**
     * 关闭对话框
     */
    closeDialog(dialogId) {
        const dialogData = this.confirmDialogs.get(dialogId);
        if (dialogData) {
            dialogData.element.classList.remove('show');
            setTimeout(() => {
                dialogData.element.remove();
                this.confirmDialogs.delete(dialogId);
            }, 300);
        }
    }

    /**
     * 确认操作
     */
    confirmAction(dialogId) {
        const dialogData = this.confirmDialogs.get(dialogId);
        if (dialogData && dialogData.onYes) {
            dialogData.onYes();
        }
        this.closeDialog(dialogId);
    }

    /**
     * 增强现有按钮
     */
    enhanceExistingButtons() {
        document.querySelectorAll('.btn, button').forEach(btn => {
            if (!btn.dataset.btnEnhanced) {
                btn.dataset.btnEnhanced = 'true';
                this.addRippleEffect(btn);
            }
        });
    }

    /**
     * 添加涟漪效果
     */
    addRippleEffect(button) {
        button.addEventListener('click', (e) => {
            const rect = button.getBoundingClientRect();
            const ripple = document.createElement('span');
            const size = Math.max(rect.width, rect.height);
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
            ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
            ripple.classList.add('btn-ripple');
            
            button.style.position = 'relative';
            button.style.overflow = 'hidden';
            button.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    }

    /**
     * 创建加载图标
     */
    createLoadingIcon() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '16');
        svg.setAttribute('height', '16');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', 'currentColor');
        svg.setAttribute('stroke-width', '2');
        svg.classList.add('spinner');
        
        svg.innerHTML = '<circle cx="12" cy="12" r="10" stroke-opacity="0.25"/><path d="M12 2a10 10 0 0 1 10 10" stroke-opacity="1"/>';
        
        return svg;
    }

    /**
     * 创建勾选图标
     */
    createCheckIcon() {
        return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>';
    }

    /**
     * 创建关闭图标
     */
    createCloseIcon() {
        return '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
    }

    /**
     * 显示提示消息
     */
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 30px;
            right: 30px;
            padding: 12px 24px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s ease;
            background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#22c55e' : '#3b82f6'};
        `;
        
        document.body.appendChild(toast);
        
        requestAnimationFrame(() => {
            toast.style.transform = 'translateY(0)';
            toast.style.opacity = '1';
        });
        
        setTimeout(() => {
            toast.style.transform = 'translateY(100px)';
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * 创建新按钮
     */
    createButton(options) {
        const button = document.createElement('button');
        button.className = `btn ${options.variant || 'btn-primary'}`;
        
        if (options.type) {
            button.dataset.btnType = options.type;
        }
        
        if (options.text) {
            button.textContent = options.text;
        }
        
        if (options.icon) {
            button.innerHTML = options.icon + ' ' + (options.text || '');
        }
        
        Object.keys(options || {}).forEach(key => {
            if (key.startsWith('data-')) {
                button.setAttribute(key, options[key]);
            }
        });
        
        if (options.onClick) {
            button.addEventListener('click', options.onClick);
        }
        
        this.addRippleEffect(button);
        return button;
    }

    /**
     * 创建按钮组
     */
    createButtonGroup(buttons, options = {}) {
        const group = document.createElement('div');
        group.className = `btn-group ${options.orientation || 'horizontal'}`;
        
        buttons.forEach(btnConfig => {
            const button = this.createButton(btnConfig);
            group.appendChild(button);
        });
        
        return group;
    }
}

// 全局实例
window.ButtonExt = new ButtonFeatureExtension();

// 样式注入
const buttonStyles = `
    /* 按钮功能扩展样式 */
    .btn-loading {
        pointer-events: none;
        opacity: 0.7;
    }
    
    .spinner {
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    .btn-toggled {
        background: var(--primary-color) !important;
        color: white !important;
    }
    
    .btn-clicked {
        transform: scale(0.95);
    }
    
    .btn-ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .btn-dropdown {
        position: relative;
    }
    
    .btn-dropdown-menu {
        position: absolute;
        top: 100%;
        left: 0;
        margin-top: 8px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        min-width: 160px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
        opacity: 0;
        visibility: hidden;
        transform: translateY(-10px);
        transition: all 0.2s ease;
        z-index: 1000;
    }
    
    .btn-dropdown-menu.show {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
    }
    
    .btn-dropdown-item {
        display: block;
        padding: 10px 16px;
        color: var(--text-primary);
        text-decoration: none;
        cursor: pointer;
        transition: background 0.2s;
    }
    
    .btn-dropdown-item:hover {
        background: var(--bg-card-hover);
    }
    
    .btn-group {
        display: flex;
        gap: 0;
    }
    
    .btn-group.horizontal {
        flex-direction: row;
    }
    
    .btn-group.vertical {
        flex-direction: column;
    }
    
    .btn-group .btn {
        border-radius: 0;
    }
    
    .btn-group .btn:first-child {
        border-radius: 8px 0 0 8px;
    }
    
    .btn-group .btn:last-child {
        border-radius: 0 8px 8px 0;
    }
    
    .btn-group.vertical .btn:first-child {
        border-radius: 8px 8px 0 0;
    }
    
    .btn-group.vertical .btn:last-child {
        border-radius: 0 0 8px 8px;
    }
    
    .confirm-dialog-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
    }
    
    .confirm-dialog-overlay.show {
        opacity: 1;
        visibility: visible;
    }
    
    .confirm-dialog {
        background: var(--bg-card);
        border-radius: 16px;
        width: 90%;
        max-width: 400px;
        transform: scale(0.9);
        transition: transform 0.3s ease;
    }
    
    .confirm-dialog-overlay.show .confirm-dialog {
        transform: scale(1);
    }
    
    .confirm-dialog-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px;
        border-bottom: 1px solid var(--border-color);
    }
    
    .confirm-dialog-header h4 {
        margin: 0;
        font-size: 18px;
    }
    
    .confirm-dialog-close {
        background: none;
        border: none;
        cursor: pointer;
        color: var(--text-secondary);
        padding: 4px;
    }
    
    .confirm-dialog-body {
        padding: 20px;
    }
    
    .confirm-dialog-body p {
        margin: 0;
        color: var(--text-secondary);
    }
    
    .confirm-dialog-footer {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
        padding: 20px;
        border-top: 1px solid var(--border-color);
    }
    
    .btn-success {
        background: linear-gradient(135deg, #22c55e, #16a34a) !important;
    }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = buttonStyles;
document.head.appendChild(styleSheet);
