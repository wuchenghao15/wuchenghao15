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
        // 全局变量
        let engineLockInfo = null;
        let availableEngines = [];
        let statusCheckInterval = null;
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', async function() {
            try {
                // 初始化主题
                await initializeTheme();
                // 加载锁定信息
                await loadLockInfo();
                // 加载其他引擎状态
                await loadAvailableEngines();
                // 设置状态检查间隔
                statusCheckInterval = setInterval(checkEngineStatus, 30000); // 每30秒检查一次
                // 隐藏加载动画
                setTimeout(() => {
                    document.getElementById('page-loader').style.display = config.display  ;
                }, 500);
            } catch (error) {
                console.error('初始化锁定页面失败:', error);
                showError('初始化失败: ' + error.message);
            }
        });
        /**
         * 加载锁定信息
         */
        async function loadLockInfo() {
            try {
                // 模拟加载锁定信息
                // 实际项目中应该从API获取
                engineLockInfo = {
                    engineId: 'engine_123',
                    status: 'locked',
                    lockedAt: new Date().toISOString(),
                    lockedBy: 'admin@mtscos.com',
                    reason: '系统维护',
                    estimatedUnlockTime: new Date(Date.now() + 3600000).toISOString() // 1小时后
                };
                updateLockInfoDisplay();
            } catch (error) {
                console.error('加载锁定信息失败:', error);
                showError('加载锁定信息失败: ' + error.message);
            }
        }
        /**
         * 更新锁定信息显示
         */
        function updateLockInfoDisplay() {
            if (!engineLockInfo) return;
            // 更新锁定时间
            const lockTimeElement = document.getElementById('lock-time');
            const lockDate = new Date(engineLockInfo.lockedAt);
            lockTimeElement.textContent = lockDate.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            // 更新锁定原因
            const lockReasonElement = document.getElementById('lock-reason');
            lockReasonElement.textContent = engineLockInfo.reason;
            // 更新锁定管理员
            const lockAdminElement = document.getElementById('lock-admin');
            lockAdminElement.textContent = engineLockInfo.lockedBy;
            // 更新预计解锁时间
            const unlockEtaElement = document.getElementById('unlock-eta');
            const unlockDate = new Date(engineLockInfo.estimatedUnlockTime);
            unlockEtaElement.textContent = unlockDate.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
        /**
         * 加载其他可用引擎
         */
        async function loadAvailableEngines() {
            try {
                // 模拟加载其他引擎
                // 实际项目中应该从API获取
                availableEngines = [
                    {
                        id: 'engine_456',
                        name: '通用AI引擎 v2.0',
                        status: 'active',
                        type: 'general',
                        version: '2.0.0',
                        load: '45%'
                    },
                    {
                        id: 'engine_789',
                        name: '视觉识别引擎 v1.5',
                        status: 'active',
                        type: 'vision',
                        version: '1.5.0',
                        load: '30%'
                    },
                    {
                        id: 'engine_012',
                        name: '自然语言引擎 v3.0',
                        status: 'active',
                        type: 'nlp',
                        version: '3.0.0',
                        load: '60%'
                    }
                ];
                updateEngineListDisplay();
            } catch (error) {
                console.error('加载引擎列表失败:', error);
                showError('加载引擎列表失败: ' + error.message);
            }
        }
        /**
         * 更新引擎列表显示
         */
        function updateEngineListDisplay() {
            const engineListContent = document.getElementById('engine-list-content');
            if (availableEngines.length === 0) {
                engineListContent.innerHTML = `<div class="text-center text-muted py-4">
                        <i class="fas fa-lock"></i> 暂无其他可用引擎
                    </div>
                `;
                return;
            }
            let engineHtml = config.engineHtml  ;
            availableEngines.forEach(engine => {
                const isLocked = engine.status === 'locked';
                const cardClass = isLocked ? 'locked' : 'active';
                const statusBadge = isLocked ? 
                    '<span class = config.class  >已锁定</span>' : 
                    '<span class = config.class  >可用</span>';
                engineHtml += `
                    <div class = config.class  >
                        <div class = config.class  >
                            <div>
                                <h3 class = config.class  >${engine.name}</h3>
                                <div class = config.class  >
                                    <span><i class = config.class  ></i> ${engine.type}</span>
                                    <span><i class = config.class  ></i> v${engine.version}</span>
                                    <span><i class = config.class  ></i> 负载: ${engine.load}</span>
                                </div>
                            </div>
                            ${statusBadge}
                        </div>
                        <div class = config.class  >
                            ${!isLocked ? `
                                <button class = config.class   onclick = config.onclick  ${engine.id}')">
                                    <i class = config.class  ></i>
                                    切换到此引擎
                                </button>
                            ` : ''}
                            <button class = config.class   onclick = config.onclick  ${engine.id}')">
                                <i class = config.class  ></i>
                                查看详情
                            </button>
                        </div>
                    </div>
                `;
            });
            engineListContent.innerHTML = engineHtml;
        }
        /**
         * 检查引擎状态
         */
        async function checkEngineStatus() {
            const checkStatusBtn = document.getElementById('check-status-btn');
            const originalText = checkStatusBtn.innerHTML;
            try {
                checkStatusBtn.disabled = true;
                checkStatusBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 检查中...';
                // 模拟检查状态
                await new Promise(resolve => setTimeout(resolve, 1000));
                // 模拟状态检查结果
                const isUnlocked = Math.random() > 0.8; // 20% 概率解锁
                if (isUnlocked) {
                    showSuccess('引擎已解锁，正在跳转...');
                    setTimeout(() => {
                        window.location.href = config.href  ;
                    }, 2000);
                } else {
                    showInfo('引擎仍处于锁定状态，请稍后再试');
                    updateLockInfoDisplay();
                }
            } catch (error) {
                console.error('检查引擎状态失败:', error);
                showError('检查状态失败: ' + error.message);
            } finally {
                checkStatusBtn.disabled = false;
                checkStatusBtn.innerHTML = originalText;
            }
        }
        /**
         * 返回控制台
         */
        function goBack() {
            window.location.href = config.href  ;
        }
        /**
         * 联系管理员
         */
        function contactAdmin() {
            const subject = encodeURIComponent('引擎锁定通知');
            const body = encodeURIComponent(`引擎ID: ${engineLockInfo?.engineId || '未知'}\n锁定时间: ${engineLockInfo?.lockedAt || '未知'}\n锁定原因: ${engineLockInfo?.reason || '未知'}\n\n请尽快处理，谢谢！`);
            window.location.href = `mailto:admin@mtscos.com?subject=${subject}&body=${body}`;
        }
        /**
         * 切换到其他引擎
         */
        function switchToEngine(engineId) {
            showLoading('正在切换引擎...');
            setTimeout(() => {
                hideLoading();
                showSuccess('引擎切换成功，正在跳转...');
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 2000);
            }, 1500);
        }
        /**
         * 显示加载状态
         */
        function showLoading(message) {
            const overlay = document.getElementById('loading-overlay');
            const loadingText = document.getElementById('loading-text');
            loadingText.textContent = message;
            overlay.style.display = 'flex';
        }
        /**
         * 隐藏加载状态
         */
        function hideLoading() {
            const overlay = document.getElementById('loading-overlay');
            overlay.style.display = 'none';
        }
        /**
         * 显示错误信息
         */
        function showError(message) {
            // 这里可以实现更复杂的错误提示
            alert('错误: ' + message);
        }
        /**
         * 显示成功信息
         */
        function showSuccess(message) {
            // 这里可以实现更复杂的成功提示
            alert('成功: ' + message);
        }
        /**
         * 显示信息
         */
        function showInfo(message) {
            // 这里可以实现更复杂的信息提示
            alert('信息: ' + message);
        }
        /**
         * 初始化主题
         */
        async function initializeTheme() {
            // 主题初始化逻辑
            if (typeof ThemeManager !== 'undefined') {
                const themeManager = new ThemeManager();
                await themeManager.init();
            }
        }
        // 防止页面被缓存
        window.addEventListener('pageshow', function(event) {
            if (event.persisted) {
                window.location.reload();
            }
        });
        // 清理定时器
        window.addEventListener('beforeunload', function() {
            if (statusCheckInterval) {
                clearInterval(statusCheckInterval);
            }
        });