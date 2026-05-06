// 设置页面交互逻辑

document.addEventListener('DOMContentLoaded', function() {
    initializeSettingsPage();
});

function initializeSettingsPage() {
    // 绑定面板切换事件
    bindPanelToggleEvents();
    
    // 绑定保存设置事件
    bindSaveSettingsEvents();
    
    // 绑定重置设置事件
    bindResetSettingsEvents();
    
    // 绑定其他特殊功能事件
    bindSpecialFunctionEvents();
    
    // 初始化通知系统
    initializeNotificationSystem();
    
    // 加载保存的设置
    loadSavedSettings();
    
    // 初始化Python版本检测
    initializePythonVersionDetection();
}

function bindPanelToggleEvents() {
    const menuItems = document.querySelectorAll('.menu-item');
    const panels = document.querySelectorAll('.settings-panel');
    
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            // 移除所有活动状态
            menuItems.forEach(menuItem => menuItem.classList.remove('active'));
            panels.forEach(panel => panel.classList.remove('active'));
            
            // 添加当前活动状态
            this.classList.add('active');
            const target = this.getAttribute('data-target');
            const targetPanel = document.getElementById(target);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        });
    });
}

function bindSaveSettingsEvents() {
    // 保存通用设置
    const saveGeneralBtn = document.getElementById('save-general-settings');
    if (saveGeneralBtn) {
        saveGeneralBtn.addEventListener('click', function() {
            saveGeneralSettings();
        });
    }
    
    // 保存数据库设置
    const saveDbBtn = document.getElementById('save-db-settings');
    if (saveDbBtn) {
        saveDbBtn.addEventListener('click', function() {
            saveDatabaseSettings();
        });
    }
    
    // 保存Python设置
    const savePythonBtn = document.getElementById('save-python-settings');
    if (savePythonBtn) {
        savePythonBtn.addEventListener('click', function() {
            savePythonSettings();
        });
    }
    
    // 保存安全设置
    const saveSecurityBtn = document.getElementById('save-security-settings');
    if (saveSecurityBtn) {
        saveSecurityBtn.addEventListener('click', function() {
            saveSecuritySettings();
        });
    }
    
    // 保存AI设置
    const saveAiBtn = document.getElementById('save-ai-settings');
    if (saveAiBtn) {
        saveAiBtn.addEventListener('click', function() {
            saveAiSettings();
        });
    }
    
    // 保存备份设置
    const saveBackupBtn = document.getElementById('save-backup-settings');
    if (saveBackupBtn) {
        saveBackupBtn.addEventListener('click', function() {
            saveBackupSettings();
        });
    }
}

function bindResetSettingsEvents() {
    // 重置通用设置
    const resetGeneralBtn = document.getElementById('reset-general-settings');
    if (resetGeneralBtn) {
        resetGeneralBtn.addEventListener('click', function() {
            if (confirm('确定要恢复通用设置的默认值吗？')) {
                resetGeneralSettings();
            }
        });
    }
    
    // 重置数据库设置
    const resetDbBtn = document.getElementById('reset-db-settings');
    if (resetDbBtn) {
        resetDbBtn.addEventListener('click', function() {
            if (confirm('确定要恢复数据库设置的默认值吗？')) {
                resetDatabaseSettings();
            }
        });
    }
    
    // 重置Python设置
    const resetPythonBtn = document.getElementById('reset-python-settings');
    if (resetPythonBtn) {
        resetPythonBtn.addEventListener('click', function() {
            if (confirm('确定要恢复Python设置的默认值吗？')) {
                resetPythonSettings();
            }
        });
    }
    
    // 重置安全设置
    const resetSecurityBtn = document.getElementById('reset-security-settings');
    if (resetSecurityBtn) {
        resetSecurityBtn.addEventListener('click', function() {
            if (confirm('确定要恢复安全设置的默认值吗？')) {
                resetSecuritySettings();
            }
        });
    }
    
    // 重置AI设置
    const resetAiBtn = document.getElementById('reset-ai-settings');
    if (resetAiBtn) {
        resetAiBtn.addEventListener('click', function() {
            if (confirm('确定要恢复AI设置的默认值吗？')) {
                resetAiSettings();
            }
        });
    }
    
    // 重置备份设置
    const resetBackupBtn = document.getElementById('reset-backup-settings');
    if (resetBackupBtn) {
        resetBackupBtn.addEventListener('click', function() {
            if (confirm('确定要恢复备份设置的默认值吗？')) {
                resetBackupSettings();
            }
        });
    }
}

function bindSpecialFunctionEvents() {
    // 测试数据库连接
    const testDbBtn = document.getElementById('test-db-connection');
    if (testDbBtn) {
        testDbBtn.addEventListener('click', function() {
            testDatabaseConnection();
        });
    }
    
    // 检查Python更新
    const checkPythonUpdateBtn = document.getElementById('check-python-update');
    if (checkPythonUpdateBtn) {
        checkPythonUpdateBtn.addEventListener('click', function() {
            checkPythonUpdate();
        });
    }
    
    // 升级Python
    const updatePythonBtn = document.getElementById('update-python-version');
    if (updatePythonBtn) {
        updatePythonBtn.addEventListener('click', function() {
            if (confirm('确定要升级Python版本吗？升级过程可能需要一段时间。')) {
                updatePythonVersion();
            }
        });
    }
    
    // 立即更新AI模型
    const updateAiModelBtn = document.getElementById('update-ai-model');
    if (updateAiModelBtn) {
        updateAiModelBtn.addEventListener('click', function() {
            if (confirm('确定要立即更新AI模型吗？更新过程可能需要一段时间。')) {
                updateAiModel();
            }
        });
    }
    
    // 立即创建备份
    const createBackupNowBtn = document.getElementById('create-backup-now');
    if (createBackupNowBtn) {
        createBackupNowBtn.addEventListener('click', function() {
            if (confirm('确定要立即创建系统备份吗？备份过程可能需要一段时间。')) {
                createBackupNow();
            }
        });
    }
    
    // 恢复备份
    const restoreBackupBtn = document.getElementById('restore-backup');
    if (restoreBackupBtn) {
        restoreBackupBtn.addEventListener('click', function() {
            if (confirm('确定要恢复备份吗？此操作将覆盖当前系统数据，不可恢复！')) {
                restoreBackup();
            }
        });
    }
}

function initializeNotificationSystem() {
    const notification = document.getElementById('notification');
    if (notification) {
        const closeBtn = notification.querySelector('.notification-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                hideNotification();
            });
        }
    }
}

function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    const messageElement = document.getElementById('notification-message');
    
    if (notification && messageElement) {
        // 设置通知内容
        messageElement.textContent = message;
        
        // 设置通知类型
        notification.className = `notification ${type}`;
        
        // 显示通知
        notification.classList.add('show');
        
        // 3秒后自动隐藏
        setTimeout(hideNotification, 3000);
    }
}

function hideNotification() {
    const notification = document.getElementById('notification');
    if (notification) {
        notification.classList.remove('show');
    }
}

function loadSavedSettings() {
    // 从localStorage加载保存的设置
    const savedSettings = JSON.parse(localStorage.getItem('mtscos_settings')) || {};
    
    // 应用保存的设置到表单
    applySavedSettings(savedSettings);
    
    showNotification('设置已加载', 'success');
}

function applySavedSettings(settings) {
    // 应用通用设置
    if (settings.general) {
        const sessionTimeout = document.getElementById('session-timeout');
        const pageAutoRefresh = document.getElementById('page-auto-refresh');
        const themeSelect = document.getElementById('theme-select');
        const autoLogout = document.getElementById('auto-logout');
        
        if (sessionTimeout) sessionTimeout.value = settings.general.sessionTimeout || 30;
        if (pageAutoRefresh) pageAutoRefresh.value = settings.general.pageAutoRefresh || 0;
        if (themeSelect) themeSelect.value = settings.general.theme || 'light';
        if (autoLogout) autoLogout.checked = settings.general.autoLogout || false;
    }
    
    // 应用安全设置
    if (settings.security) {
        const passwordPolicy = document.getElementById('password-policy');
        const failedLoginAttempts = document.getElementById('failed-login-attempts');
        const accountLockoutTime = document.getElementById('account-lockout-time');
        const enable2fa = document.getElementById('enable-2fa');
        const enableIpRestriction = document.getElementById('enable-ip-restriction');
        const enableLoginAlert = document.getElementById('enable-login-alert');
        
        if (passwordPolicy) passwordPolicy.value = settings.security.passwordPolicy || 'medium';
        if (failedLoginAttempts) failedLoginAttempts.value = settings.security.failedLoginAttempts || 5;
        if (accountLockoutTime) accountLockoutTime.value = settings.security.accountLockoutTime || 15;
        if (enable2fa) enable2fa.checked = settings.security.enable2fa || false;
        if (enableIpRestriction) enableIpRestriction.checked = settings.security.enableIpRestriction || false;
        if (enableLoginAlert) enableLoginAlert.checked = settings.security.enableLoginAlert || false;
    }
    
    // 应用AI设置
    if (settings.ai) {
        const enableAiAssistant = document.getElementById('enable-ai-assistant');
        const enableAiLearning = document.getElementById('enable-ai-learning');
        const aiUpdateFrequency = document.getElementById('ai-update-frequency');
        const aiConfidenceThreshold = document.getElementById('ai-confidence-threshold');
        const enableAiLogging = document.getElementById('enable-ai-logging');
        
        if (enableAiAssistant) enableAiAssistant.checked = settings.ai.enableAiAssistant || false;
        if (enableAiLearning) enableAiLearning.checked = settings.ai.enableAiLearning || false;
        if (aiUpdateFrequency) aiUpdateFrequency.value = settings.ai.aiUpdateFrequency || 7;
        if (aiConfidenceThreshold) aiConfidenceThreshold.value = settings.ai.aiConfidenceThreshold || 80;
        if (enableAiLogging) enableAiLogging.checked = settings.ai.enableAiLogging || false;
    }
    
    // 应用备份设置
    if (settings.backup) {
        const enableAutoBackup = document.getElementById('enable-auto-backup');
        const backupFrequency = document.getElementById('backup-frequency');
        const backupTime = document.getElementById('backup-time');
        const backupRetention = document.getElementById('backup-retention');
        const backupStorage = document.getElementById('backup-storage');
        const enableBackupNotification = document.getElementById('enable-backup-notification');
        
        if (enableAutoBackup) enableAutoBackup.checked = settings.backup.enableAutoBackup || false;
        if (backupFrequency) backupFrequency.value = settings.backup.backupFrequency || 'weekly';
        if (backupTime) backupTime.value = settings.backup.backupTime || '02:00';
        if (backupRetention) backupRetention.value = settings.backup.backupRetention || 7;
        if (backupStorage) backupStorage.value = settings.backup.backupStorage || '/backup/mtscos';
        if (enableBackupNotification) enableBackupNotification.checked = settings.backup.enableBackupNotification || false;
    }
    
    // 应用数据库设置
    if (settings.database) {
        const dbHost = document.getElementById('db-host');
        const dbPort = document.getElementById('db-port');
        const dbName = document.getElementById('db-name');
        const dbUser = document.getElementById('db-user');
        const dbPassword = document.getElementById('db-password');
        const saveCredentials = document.getElementById('save-credentials');
        
        if (dbHost) dbHost.value = settings.database.host || '';
        if (dbPort) dbPort.value = settings.database.port || '';
        if (dbName) dbName.value = settings.database.name || '';
        if (dbUser) dbUser.value = settings.database.user || '';
        if (dbPassword && settings.database.password) dbPassword.value = settings.database.password || '';
        if (saveCredentials) saveCredentials.checked = settings.database.saveCredentials || false;
    }
    
    // 应用Python设置
    if (settings.python) {
        const pythonPath = document.getElementById('python-path');
        if (pythonPath) pythonPath.value = settings.python.pythonPath || '';
    }
}

function saveGeneralSettings() {
    const sessionTimeout = document.getElementById('session-timeout');
    const pageAutoRefresh = document.getElementById('page-auto-refresh');
    const themeSelect = document.getElementById('theme-select');
    const autoLogout = document.getElementById('auto-logout');
    
    const settings = {
        general: {
            sessionTimeout: parseInt(sessionTimeout.value),
            pageAutoRefresh: parseInt(pageAutoRefresh.value),
            theme: themeSelect.value,
            autoLogout: autoLogout.checked
        }
    };
    
    saveSettings(settings);
    showNotification('通用设置已保存', 'success');
}

function saveSecuritySettings() {
    const passwordPolicy = document.getElementById('password-policy');
    const failedLoginAttempts = document.getElementById('failed-login-attempts');
    const accountLockoutTime = document.getElementById('account-lockout-time');
    const enable2fa = document.getElementById('enable-2fa');
    const enableIpRestriction = document.getElementById('enable-ip-restriction');
    const enableLoginAlert = document.getElementById('enable-login-alert');
    
    const settings = {
        security: {
            passwordPolicy: passwordPolicy.value,
            failedLoginAttempts: parseInt(failedLoginAttempts.value),
            accountLockoutTime: parseInt(accountLockoutTime.value),
            enable2fa: enable2fa.checked,
            enableIpRestriction: enableIpRestriction.checked,
            enableLoginAlert: enableLoginAlert.checked
        }
    };
    
    saveSettings(settings);
    showNotification('安全设置已保存', 'success');
}

function saveAiSettings() {
    const enableAiAssistant = document.getElementById('enable-ai-assistant');
    const enableAiLearning = document.getElementById('enable-ai-learning');
    const aiUpdateFrequency = document.getElementById('ai-update-frequency');
    const aiConfidenceThreshold = document.getElementById('ai-confidence-threshold');
    const enableAiLogging = document.getElementById('enable-ai-logging');
    
    const settings = {
        ai: {
            enableAiAssistant: enableAiAssistant.checked,
            enableAiLearning: enableAiLearning.checked,
            aiUpdateFrequency: parseInt(aiUpdateFrequency.value),
            aiConfidenceThreshold: parseInt(aiConfidenceThreshold.value),
            enableAiLogging: enableAiLogging.checked
        }
    };
    
    saveSettings(settings);
    showNotification('AI设置已保存', 'success');
}

function saveBackupSettings() {
    const enableAutoBackup = document.getElementById('enable-auto-backup');
    const backupFrequency = document.getElementById('backup-frequency');
    const backupTime = document.getElementById('backup-time');
    const backupRetention = document.getElementById('backup-retention');
    const backupStorage = document.getElementById('backup-storage');
    const enableBackupNotification = document.getElementById('enable-backup-notification');
    
    const settings = {
        backup: {
            enableAutoBackup: enableAutoBackup.checked,
            backupFrequency: backupFrequency.value,
            backupTime: backupTime.value,
            backupRetention: parseInt(backupRetention.value),
            backupStorage: backupStorage.value,
            enableBackupNotification: enableBackupNotification.checked
        }
    };
    
    saveSettings(settings);
    showNotification('备份设置已保存', 'success');
}

function saveSettings(newSettings) {
    // 获取当前保存的设置
    const currentSettings = JSON.parse(localStorage.getItem('mtscos_settings')) || {};
    
    // 合并新设置
    const updatedSettings = {
        ...currentSettings,
        ...newSettings
    };
    
    // 保存到localStorage
    localStorage.setItem('mtscos_settings', JSON.stringify(updatedSettings));
    
    // 这里可以添加向服务器发送设置的逻辑
    // sendSettingsToServer(updatedSettings);
}

function resetGeneralSettings() {
    if (confirm('确定要恢复通用设置的默认值吗？')) {
        const defaultSettings = {
            general: {
                sessionTimeout: 30,
                pageAutoRefresh: 0,
                theme: 'light',
                autoLogout: false
            }
        };
        
        saveSettings(defaultSettings);
        applySavedSettings(defaultSettings);
        showNotification('通用设置已恢复默认值', 'success');
    }
}

function resetSecuritySettings() {
    if (confirm('确定要恢复安全设置的默认值吗？')) {
        const defaultSettings = {
            security: {
                passwordPolicy: 'medium',
                failedLoginAttempts: 5,
                accountLockoutTime: 15,
                enable2fa: false,
                enableIpRestriction: false,
                enableLoginAlert: false
            }
        };
        
        saveSettings(defaultSettings);
        applySavedSettings(defaultSettings);
        showNotification('安全设置已恢复默认值', 'success');
    }
}

function resetAiSettings() {
    if (confirm('确定要恢复AI设置的默认值吗？')) {
        const defaultSettings = {
            ai: {
                enableAiAssistant: false,
                enableAiLearning: false,
                aiUpdateFrequency: 7,
                aiConfidenceThreshold: 80,
                enableAiLogging: false
            }
        };
        
        saveSettings(defaultSettings);
        applySavedSettings(defaultSettings);
        showNotification('AI设置已恢复默认值', 'success');
    }
}

function resetBackupSettings() {
    if (confirm('确定要恢复备份设置的默认值吗？')) {
        const defaultSettings = {
            backup: {
                enableAutoBackup: false,
                backupFrequency: 'weekly',
                backupTime: '02:00',
                backupRetention: 7,
                backupStorage: '/backup/mtscos',
                enableBackupNotification: false
            }
        };
        
        saveSettings(defaultSettings);
        applySavedSettings(defaultSettings);
        showNotification('备份设置已恢复默认值', 'success');
    }
}

function testDatabaseConnection() {
    // 显示加载状态
    const btn = document.getElementById('test-db-connection');
    const originalText = btn.textContent;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在测试...';
    btn.disabled = true;
    
    // 模拟数据库连接测试
    setTimeout(() => {
        // 这里可以添加实际的数据库连接测试逻辑
        showNotification('数据库连接测试成功', 'success');
        
        // 恢复按钮状态
        btn.innerHTML = originalText;
        btn.disabled = false;
    }, 1500);
}

function initializePythonVersionDetection() {
    const currentVersionElement = document.getElementById('current-python-version');
    const availableVersionsElement = document.getElementById('available-python-versions');
    
    if (currentVersionElement) {
        // 模拟检测当前Python版本
        setTimeout(() => {
            currentVersionElement.innerHTML = 'Python 3.10.12';
        }, 1000);
    }
    
    if (availableVersionsElement) {
        // 模拟检测可用Python版本
        setTimeout(() => {
            availableVersionsElement.innerHTML = `
                <div class="version-item current">Python 3.10.12 (当前版本)</div>
                <div class="version-item">Python 3.11.6</div>
                <div class="version-item">Python 3.12.3</div>
            `;
            
            // 绑定版本选择事件
            const versionItems = availableVersionsElement.querySelectorAll('.version-item');
            versionItems.forEach(item => {
                if (!item.classList.contains('current')) {
                    item.addEventListener('click', function() {
                        const pythonPathInput = document.getElementById('python-path');
                        if (pythonPathInput) {
                            const version = this.textContent.trim().split(' ')[1];
                            pythonPathInput.value = `/usr/bin/python${version.split('.')[0]}.${version.split('.')[1]}`;
                            showNotification(`已选择Python版本: ${version}`, 'info');
                        }
                    });
                }
            });
        }, 1500);
    }
}

function checkPythonUpdate() {
    // 显示加载状态
    const btn = document.getElementById('check-python-update');
    const originalText = btn.textContent;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在检查...';
    btn.disabled = true;
    
    // 模拟检查Python更新
    setTimeout(() => {
        showNotification('发现新版本: Python 3.12.3', 'warning');
        
        // 恢复按钮状态
        btn.innerHTML = originalText;
        btn.disabled = false;
    }, 1500);
}

function updatePythonVersion() {
    // 显示加载状态
    const btn = document.getElementById('update-python-version');
    const originalText = btn.textContent;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在升级...';
    btn.disabled = true;
    
    // 模拟升级Python版本
    setTimeout(() => {
        showNotification('Python版本升级成功', 'success');
        
        // 更新显示的Python版本
        const currentVersionElement = document.getElementById('current-python-version');
        if (currentVersionElement) {
            currentVersionElement.innerHTML = 'Python 3.12.3';
        }
        
        // 恢复按钮状态
        btn.innerHTML = originalText;
        btn.disabled = false;
    }, 3000);
}

function updateAiModel() {
    // 显示加载状态
    const btn = document.getElementById('update-ai-model');
    const originalText = btn.textContent;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在更新...';
    btn.disabled = true;
    
    // 模拟更新AI模型
    setTimeout(() => {
        showNotification('AI模型更新成功', 'success');
        
        // 恢复按钮状态
        btn.innerHTML = originalText;
        btn.disabled = false;
    }, 2500);
}

function createBackupNow() {
    // 显示加载状态
    const btn = document.getElementById('create-backup-now');
    const originalText = btn.textContent;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在创建备份...';
    btn.disabled = true;
    
    // 模拟创建备份
    setTimeout(() => {
        showNotification('备份创建成功', 'success');
        
        // 恢复按钮状态
        btn.innerHTML = originalText;
        btn.disabled = false;
    }, 3000);
}

function restoreBackup() {
    // 显示加载状态
    const btn = document.getElementById('restore-backup');
    const originalText = btn.textContent;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在恢复...';
    btn.disabled = true;
    
    // 模拟恢复备份
    setTimeout(() => {
        showNotification('备份恢复成功', 'success');
        
        // 恢复按钮状态
        btn.innerHTML = originalText;
        btn.disabled = false;
    }, 3000);
}

// 保存Python设置
function savePythonSettings() {
    const pythonPath = document.getElementById('python-path');
    
    const settings = {
        python: {
            pythonPath: pythonPath.value
        }
    };
    
    saveSettings(settings);
    showNotification('Python设置已保存', 'success');
}

// 重置Python设置
function resetPythonSettings() {
    if (confirm('确定要恢复Python设置的默认值吗？')) {
        const defaultSettings = {
            python: {
                pythonPath: '/usr/bin/python3'
            }
        };
        
        saveSettings(defaultSettings);
        applySavedSettings(defaultSettings);
        showNotification('Python设置已恢复默认值', 'success');
    }
}

// 保存数据库设置
function saveDatabaseSettings() {
    const dbHost = document.getElementById('db-host');
    const dbPort = document.getElementById('db-port');
    const dbName = document.getElementById('db-name');
    const dbUser = document.getElementById('db-user');
    const dbPassword = document.getElementById('db-password');
    const saveCredentials = document.getElementById('save-credentials');
    
    const settings = {
        database: {
            host: dbHost.value,
            port: parseInt(dbPort.value),
            name: dbName.value,
            user: dbUser.value,
            saveCredentials: saveCredentials.checked
        }
    };
    
    // 只有在勾选保存凭证时才保存密码
    if (saveCredentials.checked) {
        settings.database.password = dbPassword.value;
    }
    
    saveSettings(settings);
    showNotification('数据库设置已保存', 'success');
}

// 重置数据库设置
function resetDatabaseSettings() {
    if (confirm('确定要恢复数据库设置的默认值吗？')) {
        const defaultSettings = {
            database: {
                host: 'localhost',
                port: 1433,
                name: 'MTSCOS',
                user: 'sa',
                password: '',
                saveCredentials: false
            }
        };
        
        saveSettings(defaultSettings);
        applySavedSettings(defaultSettings);
        
        // 清空密码输入框
        const dbPassword = document.getElementById('db-password');
        if (dbPassword) {
            dbPassword.value = '';
        }
        
        showNotification('数据库设置已恢复默认值', 'success');
    }
}

// 向服务器发送设置的函数（示例）
function sendSettingsToServer(settings) {
    // 这里可以添加实际的AJAX请求，将设置发送到服务器
    console.log('向服务器发送设置:', settings);
    // 示例：
    /*
    fetch('/api/settings/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('设置已成功保存到服务器');
        } else {
            console.error('设置保存到服务器失败:', data.error);
        }
    })
    .catch(error => {
        console.error('保存设置到服务器时发生错误:', error);
    });
    */
}