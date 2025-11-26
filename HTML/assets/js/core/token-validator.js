// Token验证模块
// 自动生成以解决404错误
console.log('Token validator module loaded');

// Token验证器对象
const TokenValidator = {
    // 初始化Token验证器
    init() {
        console.log('Token validator initialized');
        this.setupEventListeners();
        this.validateExistingToken();
        return this;
    },
    
    // 设置事件监听器
    setupEventListeners() {
        console.log('Setting up token validation event listeners');
        
        // 监听Token相关事件
        document.addEventListener('auth:token_received', this.handleTokenReceived.bind(this));
        document.addEventListener('auth:token_refreshed', this.handleTokenRefreshed.bind(this));
        document.addEventListener('auth:token_expired', this.handleTokenExpired.bind(this));
    },
    
    // 验证现有Token
    validateExistingToken() {
        console.log('Validating existing token');
        
        // 获取存储的Token
        const token = this.getToken();
        
        if (token) {
            // 验证Token
            const isValid = this.validateToken(token);
            
            if (isValid) {
                this.handleValidToken(token);
            } else {
                this.handleInvalidToken(token);
            }
        }
    },
    
    // 获取Token
    getToken() {
        // 从localStorage或sessionStorage获取Token
        return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    },
    
    // 设置Token
    setToken(token, rememberMe = false) {
        console.log('Setting token');
        
        // 根据rememberMe标志选择存储位置
        if (rememberMe) {
            localStorage.setItem('auth_token', token);
        } else {
            sessionStorage.setItem('auth_token', token);
        }
        
        // 验证并处理Token
        this.validateToken(token);
    },
    
    // 移除Token
    removeToken() {
        console.log('Removing token');
        localStorage.removeItem('auth_token');
        sessionStorage.removeItem('auth_token');
    },
    
    // 验证Token
    validateToken(token) {
        console.log('Validating token:', token ? 'Token exists' : 'No token');
        
        if (!token) {
            return false;
        }
        
        try {
            // 解析Token（简化版，实际应使用JWT库）
            const tokenParts = token.split('.');
            if (tokenParts.length !== 3) {
                return false;
            }
            
            // 解码Payload
            const payload = JSON.parse(atob(tokenParts[1]));
            
            // 检查Token是否过期
            const now = Math.floor(Date.now() / 1000);
            if (payload.exp && payload.exp < now) {
                this.handleTokenExpired();
                return false;
            }
            
            // 检查Token是否有效
            if (payload.iat && payload.sub) {
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('Token validation error:', error);
            return false;
        }
    },
    
    // 处理接收到的Token
    handleTokenReceived(event) {
        console.log('Token received:', event.detail);
        const { token, rememberMe } = event.detail;
        this.setToken(token, rememberMe);
    },
    
    // 处理Token刷新
    handleTokenRefreshed(event) {
        console.log('Token refreshed:', event.detail);
        const { newToken } = event.detail;
        const rememberMe = !!localStorage.getItem('auth_token');
        this.setToken(newToken, rememberMe);
    },
    
    // 处理有效的Token
    handleValidToken(token) {
        console.log('Token is valid');
        
        // 触发Token有效事件
        const event = new CustomEvent('auth:token_valid', {
            detail: { token }
        });
        document.dispatchEvent(event);
    },
    
    // 处理无效的Token
    handleInvalidToken(token) {
        console.log('Token is invalid');
        this.removeToken();
        
        // 触发Token无效事件
        const event = new CustomEvent('auth:token_invalid', {
            detail: { token }
        });
        document.dispatchEvent(event);
    },
    
    // 处理Token过期
    handleTokenExpired() {
        console.log('Token has expired');
        this.removeToken();
        
        // 触发Token过期事件
        const event = new CustomEvent('auth:token_expired');
        document.dispatchEvent(event);
    },
    
    // 获取Token中的用户信息
    getUserInfoFromToken(token) {
        try {
            if (!token) {
                token = this.getToken();
            }
            
            if (token) {
                const payload = JSON.parse(atob(token.split('.')[1]));
                return {
                    userId: payload.sub,
                    username: payload.username,
                    roles: payload.roles || [],
                    permissions: payload.permissions || []
                };
            }
            
            return null;
        } catch (error) {
            console.error('Error extracting user info from token:', error);
            return null;
        }
    }
};

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TokenValidator;
} else if (typeof window !== 'undefined') {
    window.TokenValidator = TokenValidator;
}
