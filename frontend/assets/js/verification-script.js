// MTSCOS 验证脚本 - 版本: 1.0.0
// 功能：提供用户验证功能，包括用户信息检查、验证模态框管理等

// 验证模块对象
const MTSCOS_Verification = {
    // 存储键名常量
    STORAGE_KEYS: {
        SESSION_USER: 'mtscos_user_session',
        CURRENT_USER: 'mtscos_current_user',
        VERIFIED_USER: 'mtscos_verified_user'
    },

    // 初始化验证模块
    init: function() {
        // 检查是否需要显示验证模态框
        if (!this.isUserVerified()) {
            this.showVerificationModal();
        }
        
        // 添加事件监听器
        document.addEventListener('DOMContentLoaded', () => {
            this.addEventListeners();
        });
    },

    // 检查用户是否已验证
    isUserVerified: function() {
        try {
            // 检查必要的用户信息是否存在
            const sessionUser = sessionStorage.getItem(this.STORAGE_KEYS.SESSION_USER);
            const currentUser = localStorage.getItem(this.STORAGE_KEYS.CURRENT_USER);
            const verifiedUser = localStorage.getItem(this.STORAGE_KEYS.VERIFIED_USER);
            
            // 用户必须同时拥有会话和验证信息才视为已验证
            return !!sessionUser && !!verifiedUser;
        } catch (error) {
            console.error('验证状态检查失败:', error);
            return false;
        }
    },

    // 显示验证模态框
    showVerificationModal: function() {
        // 检查模态框是否已存在，不存在则创建
        let modal = document.getElementById('verificationModal');
        if (!modal) {
            modal = this.createVerificationModal();
            document.body.appendChild(modal);
        }
        
        // 显示模态框
        modal.classList.remove('hidden');
        
        // 禁用背景滚动
        document.body.style.overflow = 'hidden';
    },

    // 创建验证模态框
    createVerificationModal: function() {
        const modalDiv = document.createElement('div');
        modalDiv.id = 'verificationModal';
        modalDiv.className = 'modal';
        modalDiv.innerHTML = `
            <div class="modal-overlay">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 class="modal-title">
                            <i class="fas fa-shield-alt"></i> 用户验证
                        </h3>
                        <button type="button" id="closeVerificationModal" class="modal-close">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="modal-body">
                        <p class="verification-message">请输入用户名进行验证，以访问完整功能。</p>
                        
                        <form id="verificationForm" class="verification-form">
                            <div class="form-group">
                                <label for="verificationUsername" class="form-label">用户名</label>
                                <div class="input-group">
                                    <i class="fas fa-user input-icon"></i>
                                    <input 
                                        type="text" 
                                        id="verificationUsername" 
                                        class="form-input" 
                                        placeholder="请输入用户名" 
                                        required
                                    >
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="rememberVerification">
                                    <span>记住验证状态</span>
                                </label>
                            </div>
                            
                            <div id="verificationError" class="error-message hidden"></div>
                            
                            <button type="submit" class="btn btn-primary btn-block">
                                <i class="fas fa-check"></i> 验证
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        `;
        
        // 添加基本样式
        const style = document.createElement('style');
        style.textContent = `
            /* 验证模态框样式 */
            .modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 1000;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .modal-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
            }
            
            .modal-content {
                position: relative;
                background-color: white;
                border-radius: 8px;
                width: 90%;
                max-width: 400px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
                z-index: 1001;
            }
            
            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                border-bottom: 1px solid #e5e7eb;
            }
            
            .modal-title {
                margin: 0;
                font-size: 18px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .modal-close {
                background: none;
                border: none;
                font-size: 18px;
                cursor: pointer;
                color: #6b7280;
                padding: 5px;
                border-radius: 4px;
                transition: all 0.2s;
            }
            
            .modal-close:hover {
                background-color: #f3f4f6;
                color: #374151;
            }
            
            .modal-body {
                padding: 20px;
            }
            
            .verification-message {
                margin-bottom: 20px;
                color: #4b5563;
                font-size: 14px;
            }
            
            .verification-form .form-group {
                margin-bottom: 15px;
            }
            
            .form-label {
                display: block;
                margin-bottom: 5px;
                font-weight: 500;
                color: #374151;
            }
            
            .input-group {
                position: relative;
            }
            
            .input-icon {
                position: absolute;
                left: 12px;
                top: 50%;
                transform: translateY(-50%);
                color: #9ca3af;
            }
            
            .form-input {
                width: 100%;
                padding: 10px 12px 10px 36px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                transition: border-color 0.2s;
            }
            
            .form-input:focus {
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            
            .checkbox-label {
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
                font-size: 14px;
                color: #4b5563;
            }
            
            .error-message {
                background-color: #fee2e2;
                color: #991b1b;
                padding: 10px;
                border-radius: 4px;
                font-size: 14px;
                margin-bottom: 15px;
            }
            
            .btn {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .btn-primary {
                background-color: #3b82f6;
                color: white;
            }
            
            .btn-primary:hover {
                background-color: #2563eb;
            }
            
            .btn-block {
                width: 100%;
            }
            
            .hidden {
                display: none;
            }
        `;
        document.head.appendChild(style);
        
        return modalDiv;
    },

    // 添加事件监听器
    addEventListeners: function() {
        // 验证表单提交
        const form = document.getElementById('verificationForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleVerification();
            });
        }
        
        // 关闭按钮
        const closeBtn = document.getElementById('closeVerificationModal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                // 可以选择重定向到登录页或其他操作
                this.handleClose();
            });
        }
        
        // 点击模态框外部关闭
        const modal = document.getElementById('verificationModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal || e.target.classList.contains('modal-overlay')) {
                    this.handleClose();
                }
            });
        }
    },

    // 处理验证提交
    handleVerification: function() {
        const usernameInput = document.getElementById('verificationUsername');
        const rememberCheckbox = document.getElementById('rememberVerification');
        const errorElement = document.getElementById('verificationError');
        
        if (!usernameInput) return;
        
        const username = usernameInput.value.trim();
        
        // 验证用户名
        if (!username) {
            this.showError(errorElement, '请输入用户名');
            return;
        }
        
        try {
            // 保存验证信息
            const userInfo = {
                username: username,
                verifiedAt: new Date().toISOString(),
                verificationId: this.generateVerificationId()
            };
            
            // 根据记住选项选择存储方式
            if (rememberCheckbox && rememberCheckbox.checked) {
                localStorage.setItem(this.STORAGE_KEYS.VERIFIED_USER, JSON.stringify(userInfo));
            } else {
                sessionStorage.setItem(this.STORAGE_KEYS.VERIFIED_USER, JSON.stringify(userInfo));
            }
            
            // 清除错误信息
            this.hideError(errorElement);
            
            // 关闭模态框
            this.hideVerificationModal();
            
            // 可以在这里添加验证成功后的回调
            this.onVerificationSuccess(userInfo);
            
        } catch (error) {
            console.error('验证过程失败:', error);
            this.showError(errorElement, '验证失败，请重试');
        }
    },

    // 处理关闭模态框
    handleClose: function() {
        // 这里可以根据需求决定是否允许用户不验证就离开
        // 例如可以重定向到登录页
        if (confirm('验证未完成，您将无法访问完整功能。确定要继续吗？')) {
            // 可以选择跳转到其他页面或执行其他操作
            // window.location.href = 'login.html';
        }
    },

    // 隐藏验证模态框
    hideVerificationModal: function() {
        const modal = document.getElementById('verificationModal');
        if (modal) {
            modal.classList.add('hidden');
        }
        
        // 恢复背景滚动
        document.body.style.overflow = '';
    },

    // 显示错误信息
    showError: function(element, message) {
        if (element) {
            element.textContent = message;
            element.classList.remove('hidden');
        }
    },

    // 隐藏错误信息
    hideError: function(element) {
        if (element) {
            element.classList.add('hidden');
        }
    },

    // 生成验证ID
    generateVerificationId: function() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },

    // 验证成功回调
    onVerificationSuccess: function(userInfo) {
        console.log('用户验证成功:', userInfo);
        // 可以在这里添加验证成功后的自定义逻辑
    },

    // 清除验证信息
    clearVerification: function() {
        try {
            localStorage.removeItem(this.STORAGE_KEYS.VERIFIED_USER);
            sessionStorage.removeItem(this.STORAGE_KEYS.VERIFIED_USER);
            return true;
        } catch (error) {
            console.error('清除验证信息失败:', error);
            return false;
        }
    },

    // 获取当前验证状态
    getVerificationStatus: function() {
        try {
            const verifiedUser = localStorage.getItem(this.STORAGE_KEYS.VERIFIED_USER) || 
                               sessionStorage.getItem(this.STORAGE_KEYS.VERIFIED_USER);
            
            return verifiedUser ? JSON.parse(verifiedUser) : null;
        } catch (error) {
            console.error('获取验证状态失败:', error);
            return null;
        }
    },

    // 更新验证状态显示（用于测试页面）
    updateVerificationStatusDisplay: function(elementId) {
        const statusElement = document.getElementById(elementId);
        if (!statusElement) return;
        
        const status = this.getVerificationStatus();
        
        if (status) {
            statusElement.innerHTML = `
                <div class="success">
                    <p><strong>验证状态:</strong> 已验证</p>
                    <p><strong>用户名:</strong> ${status.username}</p>
                    <p><strong>验证时间:</strong> ${new Date(status.verifiedAt).toLocaleString()}</p>
                </div>
            `;
        } else {
            statusElement.innerHTML = `
                <div class="error">
                    <p><strong>验证状态:</strong> 未验证</p>
                </div>
            `;
        }
    }
};

// 初始化验证模块
// 注意：在使用时，可以根据需要调用 MTSCOS_Verification.init()
// 例如：在需要验证的页面中添加 window.addEventListener('DOMContentLoaded', () => MTSCOS_Verification.init());

// 导出模块（如果支持模块化）
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = MTSCOS_Verification;
} else if (typeof window !== 'undefined') {
    window.MTSCOS_Verification = MTSCOS_Verification;
}