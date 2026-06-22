/**
 * MTSCOS AI System - 密码管理AI员工
 * 版本: 4.4.0
 * 描述: 专业处理密码重置、账户安全、身份验证等任务
 */

class PasswordManagerAI {
    constructor() {
        this.currentStep = 1;
        this.captchaCode = '';
        this.userData = {};
        
        this.init();
    }

    init() {
        this.generateCaptcha();
        this.setupEventListeners();
        this.initParticles();
    }

    setupEventListeners() {
        const captchaDisplay = document.getElementById('captcha-display');
        if (captchaDisplay) {
            captchaDisplay.addEventListener('click', () => this.generateCaptcha());
        }

        const newPasswordInput = document.getElementById('new-password');
        if (newPasswordInput) {
            newPasswordInput.addEventListener('input', (e) => this.checkPasswordStrength(e.target.value));
        }

        const confirmPasswordInput = document.getElementById('confirm-password');
        if (confirmPasswordInput) {
            confirmPasswordInput.addEventListener('input', (e) => this.validateConfirmPassword(e.target.value));
        }
    }

    initParticles() {
        const container = document.getElementById('particles');
        if (!container) return;
        
        const colors = ['primary', 'secondary', 'accent'];
        for (let i = 0; i < 30; i++) {
            const particle = document.createElement('div');
            particle.className = `particle ${colors[Math.floor(Math.random() * colors.length)]}`;
            particle.style.left = Math.random() * 100 + '%';
            particle.style.width = (Math.random() * 4 + 2) + 'px';
            particle.style.height = particle.style.width;
            particle.style.animationDelay = Math.random() * 20 + 's';
            particle.style.animationDuration = (Math.random() * 10 + 15) + 's';
            container.appendChild(particle);
        }
    }

    generateCaptcha() {
        const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789';
        let code = '';
        for (let i = 0; i < 4; i++) {
            code += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        
        this.captchaCode = code;
        const captchaDisplay = document.getElementById('captcha-display');
        if (captchaDisplay) {
            captchaDisplay.textContent = code;
        }
    }

    nextStep(step) {
        if (!this.validateStep(step)) return;
        
        this.currentStep = step + 1;
        this.showStep(this.currentStep);
        this.updateProgress();
    }

    prevStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.showStep(this.currentStep);
            this.updateProgress();
        }
    }

    showStep(step) {
        document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
        document.querySelectorAll('.step-dot').forEach(d => d.classList.remove('active'));
        
        const stepElement = document.getElementById(`step${step}`);
        const dotElement = document.getElementById(`step-dot-${step}`);
        
        if (stepElement) stepElement.classList.add('active');
        if (dotElement) dotElement.classList.add('active');
        
        for (let i = 1; i < step; i++) {
            const prevDot = document.getElementById(`step-dot-${i}`);
            if (prevDot) prevDot.classList.add('active');
        }
    }

    updateProgress() {
        const progressText = document.getElementById('progress-text');
        if (progressText) {
            progressText.textContent = `步骤 ${this.currentStep}/3`;
        }
    }

    validateStep(step) {
        let isValid = true;
        
        switch (step) {
            case 1:
                isValid = this.validateStep1();
                break;
            case 2:
                isValid = this.validateStep2();
                break;
            case 3:
                isValid = this.validateStep3();
                break;
        }
        
        return isValid;
    }

    validateStep1() {
        const username = document.getElementById('username').value.trim();
        const email = document.getElementById('email').value.trim();
        const captcha = document.getElementById('captcha').value.trim().toUpperCase();
        
        this.hideError('username-error');
        this.hideError('email-error');
        this.hideError('captcha-error');
        
        if (!username) {
            this.showError('username-error', '请输入用户名');
            return false;
        }
        
        if (!email) {
            this.showError('email-error', '请输入电子邮箱');
            return false;
        }
        
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            this.showError('email-error', '请输入有效的电子邮箱');
            return false;
        }
        
        if (!captcha) {
            this.showError('captcha-error', '请输入验证码');
            return false;
        }
        
        if (captcha !== this.captchaCode) {
            this.showError('captcha-error', '验证码错误，请重试');
            this.generateCaptcha();
            return false;
        }
        
        this.userData = { username, email };
        return true;
    }

    validateStep2() {
        const question = document.getElementById('security-question').value;
        const answer = document.getElementById('security-answer').value.trim();
        
        this.hideError('security-question-error');
        this.hideError('security-answer-error');
        
        if (!question) {
            this.showError('security-question-error', '请选择安全问题');
            return false;
        }
        
        if (!answer) {
            this.showError('security-answer-error', '请输入安全问题答案');
            return false;
        }
        
        this.userData.securityQuestion = question;
        this.userData.securityAnswer = answer;
        return true;
    }

    validateStep3() {
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        
        this.hideError('new-password-error');
        this.hideError('confirm-password-error');
        
        if (!newPassword) {
            this.showError('new-password-error', '请输入新密码');
            return false;
        }
        
        if (newPassword.length < 6) {
            this.showError('new-password-error', '密码长度至少6位');
            return false;
        }
        
        const hasLetter = /[a-zA-Z]/.test(newPassword);
        const hasNumber = /\d/.test(newPassword);
        
        if (!hasLetter || !hasNumber) {
            this.showError('new-password-error', '密码需包含字母和数字');
            return false;
        }
        
        if (!confirmPassword) {
            this.showError('confirm-password-error', '请确认新密码');
            return false;
        }
        
        if (newPassword !== confirmPassword) {
            this.showError('confirm-password-error', '两次输入的密码不一致');
            return false;
        }
        
        this.userData.newPassword = newPassword;
        return true;
    }

    checkPasswordStrength(password) {
        let strength = 0;
        const textElement = document.getElementById('strength-text');
        const segments = document.querySelectorAll('.strength-segment');
        
        segments.forEach(s => s.className = 'strength-segment');
        
        if (!password) {
            if (textElement) textElement.textContent = '';
            return;
        }
        
        if (password.length >= 6) strength++;
        if (password.length >= 10) strength++;
        if (/[a-zA-Z]/.test(password) && /\d/.test(password)) strength++;
        if (/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)) strength++;
        
        segments.forEach((s, i) => {
            if (i < strength) {
                if (strength === 1) s.classList.add('weak');
                else if (strength === 2) s.classList.add('fair');
                else if (strength === 3) s.classList.add('good');
                else s.classList.add('strong');
            }
        });
        
        const messages = ['', '密码较弱', '密码一般', '密码良好', '密码强度高'];
        if (textElement) textElement.textContent = messages[strength];
    }

    validateConfirmPassword(confirmPassword) {
        const newPassword = document.getElementById('new-password').value;
        
        if (confirmPassword && newPassword && confirmPassword !== newPassword) {
            this.showError('confirm-password-error', '两次输入的密码不一致');
        } else {
            this.hideError('confirm-password-error');
        }
    }

    async resetPassword(e) {
        e.preventDefault();
        
        if (!this.validateStep3()) return;
        
        try {
            document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
            document.getElementById('success-message').classList.add('active');
            
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 3000);
        } catch (error) {
            console.error('重置密码失败:', error);
            alert('重置密码失败，请稍后重试');
        }
    }

    showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.classList.add('show');
        }
    }

    hideError(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.remove('show');
        }
    }

    getStatus() {
        return {
            currentStep: this.currentStep,
            userData: this.userData,
            captchaCode: this.captchaCode,
            isReady: true
        };
    }
}

function togglePassword(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.type = field.type === 'password' ? 'text' : 'password';
    }
}

function nextStep(step) {
    if (window.passwordManagerAI) {
        window.passwordManagerAI.nextStep(step);
    }
}

function prevStep() {
    if (window.passwordManagerAI) {
        window.passwordManagerAI.prevStep();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.passwordManagerAI = new PasswordManagerAI();
});

window.PasswordManagerAI = PasswordManagerAI;
