
// 兼容性检查和回退方案
(function() {
    'use strict';
    
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();

        // 用户状态管理 - 简化版，仅从主入口同步状态
        class JapanesePageAuthManager {
            constructor() {
                this.isLoggedIn = false;
                this.userInfo = null;
                this.checkExistingSession();
                this.setupSessionMonitoring();
            }

            // 检查现有会话
            checkExistingSession() {
                const authToken = sessionStorage.getItem('auth_token');
                const userInfo = sessionStorage.getItem('current_user');
                
                if (authToken && userInfo) {
                    this.isLoggedIn = true;
                    this.userInfo = JSON.parse(userInfo);
                    this.updateUI();
                }
            }

            // 设置会话监控
            setupSessionMonitoring() {
                // 监听其他页面的认证状态变化
                window.addEventListener('storage', (event) => {
                    if (event.key === 'auth_state_changed') {
                        this.checkExistingSession();
                    }
                });

                // 页面可见性变化时检查会话
                document.addEventListener('visibilitychange', () => {
                    if (!document.hidden) {
                        this.checkExistingSession();
                    }
                });
            }

            // 更新UI
            updateUI() {
                const userInfoDiv = document.getElementById('user-info');
                const userName = document.getElementById('user-name');
                const userAvatar = document.getElementById('user-avatar');

                if (this.isLoggedIn && this.userInfo) {
                    userInfoDiv.style.display = 'flex';
                    userName.textContent = this.userInfo.name;
                    userAvatar.textContent = this.userInfo.avatar;
                } else {
                    userInfoDiv.style.display = 'none';
                }
            }
        }

        // 初始化认证管理器
        const authManager = new JapanesePageAuthManager();

        // 游客组自动跳转检查
        function checkGuestAccess() {
            const authToken = sessionStorage.getItem('auth_token');
            if (!authToken) {
                // 游客组，保持在日语界面
                console.log('游客组访问，保持在日语界面');
            }
        }

        // 注册日语评估模块到模块管理器
        function registerJapaneseAssessmentModule() {
            if (window.moduleManager) {
                window.moduleManager.registerModule({
                    id: 'japanese_level_assessment',
                    name: '日语水平评估模块',
                    category: window.moduleManager.moduleCategories.JS,
                    version: '1.0.0',
                    dependencies: [],
                    instance: {
                        startAssessment: function() {
                            console.log('开始日语水平评估');
                        },
                        checkHealth: function() {
                            return 'healthy';
                        }
                    }
                });
                console.log('日语水平评估模块已注册');
            }
        }

        // 页面加载时初始化
        window.addEventListener('DOMContentLoaded', function() {
            checkGuestAccess();
            registerJapaneseAssessmentModule();
        });
    