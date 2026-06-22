// MTSCOS 引擎锁定管理
(function() {
    'use strict';

    let availableEngines = [];
    let engineLockInfo = null;
    let statusCheckInterval = null;

    /**
     * 更新引擎列表显示
     */
    function updateEngineListDisplay() {
        const engineListContent = document.getElementById('engine-list-content');
        if (!engineListContent) return;

        if (availableEngines.length === 0) {
            engineListContent.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-info-circle"></i> 暂无其他可用引擎
                </div>
            `;
            return;
        }

        let engineHtml = '';
        availableEngines.forEach(engine => {
            const isLocked = engine.status === 'locked';
            const cardClass = isLocked ? 'locked' : 'active';
            const statusBadge = isLocked ?
                '<span class="badge badge-danger">已锁定</span>' :
                '<span class="badge badge-success">可用</span>';

            engineHtml += `
                <div class="engine-card ${cardClass}">
                    <div class="engine-header">
                        <div>
                            <h3 class="engine-name">${engine.name || ''}</h3>
                            <div class="engine-meta">
                                <span><i class="fas fa-cog"></i> ${engine.type || ''}</span>
                                <span><i class="fas fa-code-branch"></i> v${engine.version || ''}</span>
                                <span><i class="fas fa-tachometer-alt"></i> 负载: ${engine.load || 0}%</span>
                            </div>
                        </div>
                        ${statusBadge}
                    </div>
                    <div class="engine-actions">
                        ${!isLocked ? `
                            <button class="btn btn-primary" onclick="switchEngine('${engine.id}')">
                                <i class="fas fa-exchange-alt"></i> 切换到此引擎
                            </button>
                        ` : ''}
                        <button class="btn btn-secondary" onclick="viewEngineDetail('${engine.id}')">
                            <i class="fas fa-info-circle"></i> 查看详情
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
        if (!checkStatusBtn) return;
        const originalText = checkStatusBtn.innerHTML;

        try {
            checkStatusBtn.disabled = true;
            checkStatusBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 检查中...';

            await new Promise(resolve => setTimeout(resolve, 1000));

            const isUnlocked = Math.random() > 0.8;

            if (isUnlocked) {
                showSuccess('引擎已解锁，正在跳转...');
                setTimeout(() => {
                    window.location.href = '/dashboard.html';
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
        window.location.href = '/dashboard.html';
    }

    /**
     * 联系管理员
     */
    function contactAdmin() {
        const lockInfo = engineLockInfo || {};
        const subject = encodeURIComponent('引擎锁定请求');
        const body = encodeURIComponent(
            `引擎ID: ${lockInfo.id || '未知'}\n` +
            `锁定时间: ${lockInfo.lockedAt || '未知'}\n` +
            `锁定原因: ${lockInfo.reason || '未知'}\n\n` +
            `请尽快处理，谢谢！`
        );
        window.location.href = `mailto:admin@mtscos.com?subject=${subject}&body=${body}`;
    }

    /**
     * 更新锁定信息显示
     */
    function updateLockInfoDisplay() {
        const lockInfoEl = document.getElementById('lock-info');
        if (lockInfoEl && engineLockInfo) {
            lockInfoEl.innerHTML = `
                <div class="lock-detail">
                    <p><strong>锁定时间:</strong> ${engineLockInfo.lockedAt || '未知'}</p>
                    <p><strong>锁定原因:</strong> ${engineLockInfo.reason || '未知'}</p>
                    <p><strong>解锁条件:</strong> ${engineLockInfo.unlockCondition || '未知'}</p>
                </div>
            `;
        }
    }

    // 全局函数
    window.switchEngine = function(engineId) {
        if (typeof showInfo === 'function') showInfo('正在切换引擎: ' + engineId);
    };

    window.viewEngineDetail = function(engineId) {
        const engine = availableEngines.find(e => e.id === engineId);
        if (engine) {
            if (typeof showInfo === 'function') showInfo('引擎详情: ' + JSON.stringify(engine));
        }
    };

    window.checkEngineStatus = checkEngineStatus;
    window.goBack = goBack;
    window.contactAdmin = contactAdmin;
    window.updateEngineListDisplay = updateEngineListDisplay;
    window.updateLockInfoDisplay = updateLockInfoDisplay;

    // 清理定时器
    window.addEventListener('beforeunload', function() {
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
        }
    });

    // 工具函数
    function showSuccess(msg) { console.log('✅', msg); }
    function showInfo(msg) { console.log('ℹ️', msg); }
    function showError(msg) { console.error('❌', msg); }

    window.showSuccess = showSuccess;
    window.showInfo = showInfo;
    window.showError = showError;
})();
