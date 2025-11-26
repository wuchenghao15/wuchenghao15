/**
 * MTSCOS 登录API客户端
 * 连接真实后端API进行用户认证
 */

class LoginApiClient {
    constructor() {
        this.baseURL = 'http://localhost:3001/api';
        this.sessionId = this.generateSessionId();
        this.accessToken = localStorage.getItem('accessToken') || null;
        this.refreshToken = localStorage.getItem('refreshToken') || null;
        this.currentUser = null;
        
        // 初始化
        this.init().catch(error => console.error(`[login-api-client.js] this.init failed:`, error));
    }

    /**
     * 初始化API客户端
     */
    init() {
        console.log('[LOGIN_API] 初始化登录API客户端');
        
        // 检查现有登录状态
        if (this.accessToken) {
            this.verifyToken().catch(error => console.error(`[login-api-client.js] this.verifyToken failed:`, error));
        }
    }

    /**
     * 生成会话ID
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * 通用API请求方法
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': this.sessionId,
                ...options.headers
            },
            ...options
        };

        // 添加认证头
        if (this.accessToken) {
            config.headers.Authorization = `Bearer ${this.accessToken}`;
        }

        try {
            console.log(`[LOGIN_API] 请求: ${config.method || 'GET'} ${url}`);
            
            const response = await fetch(url, config);
            const data = await response.json();

            console.log(`[LOGIN_API] 响应: ${response.status}`, data);

            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`);
            }

            return data;
        } catch (error) {
            console.error(`[LOGIN_API] 请求失败:`, error);
            throw error;
        }
    }

    /**
     * 用户名密码登录
     */
    async loginWithPassword(username, password, captchaData = null) {
        try {
            const requestBody = {
                username,
                password,
                sessionId: this.sessionId
            };

            // 如果有验证码，添加到请求中
            if (captchaData) {
                requestBody.captchaId = captchaData.captchaId;
                requestBody.captchaText = captchaData.captchaText;
            }

            const response = await this.request('/login', {
                method: 'POST',
                body: JSON.stringify(requestBody)
            });

            // 保存令牌和用户信息
            if (response.success) {
                this.saveAuthData(response.data);
            }

            return response;
        } catch (error) {
            console.error('[LOGIN_API] 密码登录失败:', error);
            throw error;
        }
    }

    /**
     * 第三方登录
     */
    async loginWithThirdParty(provider, code, state) {
        try {
            const response = await this.request(`/auth/${provider}/callback`, {
                method: 'POST',
                body: JSON.stringify({
                    code,
                    state,
                    sessionId: this.sessionId
                })
            });

            // 保存令牌和用户信息
            if (response.success) {
                this.saveAuthData(response.data);
            }

            return response;
        } catch (error) {
            console.error(`[LOGIN_API] ${provider}登录失败:`, error);
            throw error;
        }
    }

    /**
     * 获取第三方登录授权URL
     */
    getThirdPartyAuthUrl(provider, redirectUrl = null) {
        const state = this.generateState();
        const params = new URLSearchParams({
            provider,
            state,
            redirect_url: redirectUrl || window.location.href
        });

        return `${this.baseURL}/auth/${provider}/authorize?${params.toString()}`;
    }

    /**
     * 生成状态参数
     */
    generateState() {
        return 'state_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * 获取验证码
     */
    async getCaptcha(type = 'image') {
        try {
            const response = await this.request('/captcha', {
                method: 'GET'
            });

            return response.data;
        } catch (error) {
            console.error('[LOGIN_API] 获取验证码失败:', error);
            throw error;
        }
    }

    /**
     * 验证验证码
     */
    async verifyCaptcha(captchaId, userInput) {
        try {
            const response = await this.request('/captcha/verify', {
                method: 'POST',
                body: JSON.stringify({
                    captchaId,
                    userInput,
                    sessionId: this.sessionId
                })
            });

            return response.success;
        } catch (error) {
            console.error('[LOGIN_API] 验证验证码失败:', error);
            return false;
        }
    }

    /**
     * 检查是否需要验证码
     */
    async checkCaptchaRequired() {
        try {
            const response = await this.request('/captcha/check-required', {
                method: 'POST',
                body: JSON.stringify({
                    sessionId: this.sessionId,
                    ipAddress: await this.getClientIP()
                })
            });

            return response.data.required;
        } catch (error) {
            console.error('[LOGIN_API] 检查验证码需求失败:', error);
            // 出错时默认需要验证码
            return true;
        }
    }

    /**
     * 获取客户端IP（模拟）
     */
    async getClientIP() {
        try {
            // 在实际项目中，可以通过API获取真实IP
            const response = await fetch('https://api.ipify.org?format=json');
            const data = await response.json();
            return data.ip;
        } catch (error) {
            console.warn('[LOGIN_API] 获取客户端IP失败，使用默认值');
            return '127.0.0.1';
        }
    }

    /**
     * 保存认证数据
     */
    saveAuthData(authData) {
        try {
            const { user, accessToken, refreshToken, expiresIn } = authData;

            // 保存令牌
            this.accessToken = accessToken;
            this.refreshToken = refreshToken;
            this.currentUser = user;

            localStorage.setItem('accessToken', accessToken);
            if (refreshToken) {
                localStorage.setItem('refreshToken', refreshToken);
            }

            // 保存用户信息
            localStorage.setItem('currentUser', JSON.stringify(user));

            // 设置令牌过期时间
            if (expiresIn) {
                const expiresAt =  + (expiresIn * 1000);
                localStorage.setItem('tokenExpiresAt', expiresAt.toString());
            }

            console.log('[LOGIN_API] 认证数据已保存');
        } catch (error) {
            console.error('[LOGIN_API] 保存认证数据失败:', error);
        }
    }

    /**
     * 清除认证数据
     */
    clearAuthData() {
        try {
            this.accessToken = null;
            this.refreshToken = null;
            this.currentUser = null;

            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('currentUser');
            localStorage.removeItem('tokenExpiresAt');

            console.log('[LOGIN_API] 认证数据已清除');
        } catch (error) {
            console.error('[LOGIN_API] 清除认证数据失败:', error);
        }
    }

    /**
     * 验证令牌有效性
     */
    async verifyToken() {
        try {
            if (!this.accessToken) {
                return false;
            }

            const response = await this.request('/auth/verify', {
                method: 'GET'
            });

            if (response.success) {
                this.currentUser = response.data.user;
                return true;
            } else {
                this.clearAuthData().catch(error => console.error(`[login-api-client.js] this.clearAuthData failed:`, error));
                return false;
            }
        } catch (error) {
            console.error('[LOGIN_API] 令牌验证失败:', error);
            this.clearAuthData().catch(error => console.error(`[login-api-client.js] this.clearAuthData failed:`, error));
            return false;
        }
    }

    /**
     * 刷新访问令牌
     */
    async refreshAccessToken() {
        try {
            if (!this.refreshToken) {
                throw new Error('没有刷新令牌');
            }

            const response = await this.request('/auth/refresh', {
                method: 'POST',
                body: JSON.stringify({
                    refreshToken: this.refreshToken
                })
            });

            if (response.success) {
                this.saveAuthData(response.data);
                return true;
            } else {
                this.clearAuthData().catch(error => console.error(`[login-api-client.js] this.clearAuthData failed:`, error));
                return false;
            }
        } catch (error) {
            console.error('[LOGIN_API] 刷新令牌失败:', error);
            this.clearAuthData().catch(error => console.error(`[login-api-client.js] this.clearAuthData failed:`, error));
            return false;
        }
    }

    /**
     * 登出
     */
    async logout() {
        try {
            if (this.accessToken) {
                await this.request('/auth/logout', {
                    method: 'POST'
                });
            }
        } catch (error) {
            console.error('[LOGIN_API] 登出请求失败:', error);
        } finally {
            this.clearAuthData().catch(error => console.error(`[login-api-client.js] this.clearAuthData failed:`, error));
        }
    }

    /**
     * 获取当前用户信息
     */
    getCurrentUser() {
        if (this.currentUser) {
            return this.currentUser;
        }

        try {
            const savedUser = localStorage.getItem('currentUser');
            if (savedUser) {
                this.currentUser = JSON.parse(savedUser);
                return this.currentUser;
            }
        } catch (error) {
            console.error('[LOGIN_API] 获取当前用户失败:', error);
        }

        return null;
    }

    /**
     * 检查是否已登录
     */
    isLoggedIn() {
        return !!this.accessToken && !!this.getCurrentUser();
    }

    /**
     * 检查令牌是否即将过期
     */
    isTokenExpiringSoon(thresholdMinutes = 5) {
        try {
            const expiresAt = localStorage.getItem('tokenExpiresAt');
            if (!expiresAt) {
                return true;
            }

            const threshold = thresholdMinutes * 60 * 1000; // 转换为毫秒
            return Date.now() >= (parseInt(expiresAt) - threshold);
        } catch (error) {
            console.error('[LOGIN_API] 检查令牌过期时间失败:', error);
            return true;
        }
    }

    /**
     * 自动刷新令牌（如果需要）
     */
    async autoRefreshTokenIfNeeded() {
        if (this.isLoggedIn().catch(error => console.error(`[login-api-client.js] this.isLoggedIn failed:`, error)) && this.isTokenExpiringSoon()) {
            console.log('[LOGIN_API] 令牌即将过期，自动刷新');
            return await this.refreshAccessToken();
        }
        return true;
    }

    /**
     * 获取服务器状态
     */
    async getServerStatus() {
        try {
            const response = await this.request('/health', {
                method: 'GET'
            });
            return response;
        } catch (error) {
            console.error('[LOGIN_API] 获取服务器状态失败:', error);
            throw error;
        }
    }

    /**
     * 发送心跳包
     */
    async sendHeartbeat() {
        try {
            const response = await this.request('/auth/heartbeat', {
                method: 'POST'
            });
            return response.success;
        } catch (error) {
            console.error('[LOGIN_API] 发送心跳包失败:', error);
            return false;
        }
    }

    /**
     * 获取登录历史
     */
    async getLoginHistory(page = 1, limit = 10) {
        try {
            const response = await this.request(`/auth/login-history?page=${page}&limit=${limit}`, {
                method: 'GET'
            });
            return response.data;
        } catch (error) {
            console.error('[LOGIN_API] 获取登录历史失败:', error);
            throw error;
        }
    }

    /**
     * 修改密码
     */
    async changePassword(oldPassword, newPassword) {
        try {
            const response = await this.request('/auth/change-password', {
                method: 'POST',
                body: JSON.stringify({
                    oldPassword,
                    newPassword
                })
            });
            return response.success;
        } catch (error) {
            console.error('[LOGIN_API] 修改密码失败:', error);
            throw error;
        }
    }

    /**
     * 忘记密码
     */
    async forgotPassword(email) {
        try {
            const response = await this.request('/auth/forgot-password', {
                method: 'POST',
                body: JSON.stringify({
                    email
                })
            });
            return response.success;
        } catch (error) {
            console.error('[LOGIN_API] 忘记密码请求失败:', error);
            throw error;
        }
    }

    /**
     * 重置密码
     */
    async resetPassword(token, newPassword) {
        try {
            const response = await this.request('/auth/reset-password', {
                method: 'POST',
                body: JSON.stringify({
                    token,
                    newPassword
                })
            });
            return response.success;
        } catch (error) {
            console.error('[LOGIN_API] 重置密码失败:', error);
            throw error;
        }
    }
}

// 创建全局API客户端实例
const loginApiClient = new LoginApiClient();

// 暴露到全局
window.loginApiClient = loginApiClient;

// 导出模块（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoginApiClient;
}