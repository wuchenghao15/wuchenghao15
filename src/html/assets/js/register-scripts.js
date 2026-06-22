// 注册页面脚本 - 协议验证

class RegisterValidator {
    constructor() {
        this.form = document.getElementById('register-form');
        this.terms = {
            'agree-terms': document.getElementById('agree-terms'),
            'agree-security': document.getElementById('agree-security'),
            'agree-authorization': document.getElementById('agree-authorization')
        };
        
        this.init();
    }

    init() {
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }
        
        Object.values(this.terms).forEach(checkbox => {
            if (checkbox) {
                checkbox.addEventListener('change', () => this.updateSubmitButton());
            }
        });
        
        this.updateSubmitButton();
    }

    handleSubmit(e) {
        if (!this.validateTerms()) {
            e.preventDefault();
            this.showTermsError();
        }
    }

    validateTerms() {
        return Object.values(this.terms).every(checkbox => checkbox && checkbox.checked);
    }

    updateSubmitButton() {
        const submitBtn = this.form?.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = !this.validateTerms();
            if (!this.validateTerms()) {
                submitBtn.style.opacity = '0.6';
                submitBtn.style.cursor = 'not-allowed';
            } else {
                submitBtn.style.opacity = '1';
                submitBtn.style.cursor = 'pointer';
            }
        }
    }

    showTermsError() {
        let errorMsg = '请阅读并同意以下协议：\n';
        
        if (!this.terms['agree-terms']?.checked) {
            errorMsg += '• 《系统使用说明协议》\n';
        }
        if (!this.terms['agree-security']?.checked) {
            errorMsg += '• 《安全信息保障协议》\n';
        }
        if (!this.terms['agree-authorization']?.checked) {
            errorMsg += '• 《系统使用授权协议》\n';
        }
        
        alert(errorMsg);
    }

    getTermsStatus() {
        return {
            systemUsage: this.terms['agree-terms']?.checked || false,
            security: this.terms['agree-security']?.checked || false,
            authorization: this.terms['agree-authorization']?.checked || false,
            allAgreed: this.validateTerms()
        };
    }
}

// 初始化验证器
document.addEventListener('DOMContentLoaded', () => {
    window.registerValidator = new RegisterValidator();
});

// 导出
window.MTSCOS_RegisterValidator = RegisterValidator;
