/**
 * 备份管理页面功能模块
 * 实现备份管理页面的交互逻辑和数据处理
 * @author MTSCOS Team
 * @version 1.0.0
 */

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', async () => {
    // 页面加载遮罩
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    
    try {
        // 显示加载遮罩
        loadingOverlay.classList.remove('hidden');
        loadingText.textContent = '初始化备份管理系统...';
        
        // 检查用户权限
        await checkUserPermissions();
        
        // 初始化备份管理器
        if (typeof BackupManager !== 'undefined') {
            await BackupManager.init();
        } else {
            console.error('备份管理器模块未加载');
            showNotification('备份管理器初始化失败', 'error');
        }
        
        // 初始化UI组件
        initUIComponents();
        
        // 加载备份列表
        await loadBackupsList();
        
        // 加载备份统计数据
        await loadBackupStatistics();
        
        // 加载备份设置
        await loadBackupSettings();
        
        // 加载恢复历史
        await loadRestoreHistory();
        
    } catch (error) {
        console.error('页面初始化失败:', error);
        showNotification('页面初始化失败: ' + error.message, 'error');
    } finally {
        // 隐藏加载遮罩
        setTimeout(() => {
            loadingOverlay.classList.add('hidden');
        }, 500);
    }
});

// 检查用户权限
async function checkUserPermissions() {
    try {
        // 实际实现中会从服务器获取用户权限
        const userHasPermission = true; // 模拟有权限
        
        if (!userHasPermission) {
            const permissionWarning = document.getElementById('permission-warning');
            permissionWarning.classList.remove('hidden');
            
            // 禁用所有操作按钮
            document.querySelectorAll('.btn-primary, .btn-secondary, .btn-danger').forEach(btn => {
                btn.disabled = true;
            });
        }
        
        // 关闭权限警告的事件监听
        document.querySelector('.close-warning').addEventListener('click', () => {
            document.getElementById('permission-warning').classList.add('hidden');
        });
        
    } catch (error) {
        console.error('检查用户权限失败:', error);
    }
}

// 初始化UI组件
function initUIComponents() {
    try {
        // 初始化模态框
        initModals();
        
        // 初始化事件监听器
        initEventListeners();
        
        // 初始化分页控件
        initPagination();
        
        // 初始化侧边栏导航
        initSidebarNavigation();
        
    } catch (error) {
        console.error('初始化UI组件失败:', error);
    }
}

// 初始化模态框
function initModals() {
    // 所有关闭模态框的按钮
    document.querySelectorAll('.close-modal').forEach(button => {
        button.addEventListener('click', closeAllModals);
    });
    
    // 点击模态框外部关闭
    window.addEventListener('click', (event) => {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (event.target === modal) {
                closeAllModals();
            }
        });
    });
    
    // ESC键关闭模态框
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeAllModals();
        }
    });
}

// 关闭所有模态框
function closeAllModals() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.classList.remove('show');
    });
}

// 显示模态框
function showModal(modalId) {
    closeAllModals();
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
    }
}

// 初始化事件监听器
function initEventListeners() {
    // 创建备份按钮事件
    document.getElementById('create-full-backup').addEventListener('click', () => {
        document.getElementById('modal-backup-type').value = 'full';
        document.getElementById('modal-title').textContent = '创建完整备份';
        showModal('create-backup-modal');
    });
    
    document.getElementById('create-incremental-backup').addEventListener('click', () => {
        document.getElementById('modal-backup-type').value = 'incremental';
        document.getElementById('modal-title').textContent = '创建增量备份';
        showModal('create-backup-modal');
    });
    
    // 确认创建备份
    document.getElementById('confirm-create-backup').addEventListener('click', handleCreateBackup);
    
    // 导入备份
    document.getElementById('import-backup').addEventListener('click', () => {
        document.getElementById('backup-file-input').click();
    });
    
    document.getElementById('backup-file-input').addEventListener('change', handleImportBackup);
    
    // 搜索和筛选事件
    document.getElementById('backup-search').addEventListener('input', handleBackupSearch);
    document.getElementById('backup-filter').addEventListener('change', handleBackupFilter);
    
    // 保存设置
    document.getElementById('save-settings').addEventListener('click', handleSaveSettings);
    
    // 重置设置
    document.getElementById('reset-settings').addEventListener('click', handleResetSettings);
    
    // 确认恢复
    document.getElementById('confirm-restore').addEventListener('click', handleConfirmRestore);
    
    // 确认删除
    document.getElementById('confirm-delete').addEventListener('click', handleConfirmDelete);
    
    // 比较备份
    document.getElementById('compare-button').addEventListener('click', handleCompareBackups);
    
    // 退出登录
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
}

// 初始化分页控件
function initPagination() {
    document.getElementById('prev-page').addEventListener('click', goToPrevPage);
    document.getElementById('next-page').addEventListener('click', goToNextPage);
}

// 初始化侧边栏导航
function initSidebarNavigation() {
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.addEventListener('click', (e) => {
            if (link.getAttribute('href').startsWith('#')) {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    // 平滑滚动到目标位置
                    window.scrollTo({
                        top: targetElement.offsetTop - 80,
                        behavior: 'smooth'
                    });
                    
                    // 更新活动状态
                    document.querySelectorAll('.sidebar-link').forEach(item => {
                        item.classList.remove('active');
                    });
                    link.classList.add('active');
                }
            }
        });
    });
}

// 加载备份列表
async function loadBackupsList() {
    try {
        const tableBody = document.getElementById('backups-table-body');
        tableBody.innerHTML = '<tr class="empty-row"><td colspan="7" class="empty-message">加载备份列表中...</td></tr>';
        
        // 从备份管理器获取备份列表
        const backups = await BackupManager.getAllBackups();
        
        if (backups.length === 0) {
            tableBody.innerHTML = '<tr class="empty-row"><td colspan="7" class="empty-message">暂无备份记录</td></tr>';
            return;
        }
        
        // 清空表格
        tableBody.innerHTML = '';
        
        // 填充表格数据
        backups.forEach(backup => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${backup.id}</td>
                <td>
                    <span class="backup-type-tag tag-${backup.type}">${backup.type === 'full' ? '完整备份' : '增量备份'}</span>
                </td>
                <td>${formatDate(backup.timestamp)}</td>
                <td>${backup.size}</td>
                <td>${backup.description || '-'}</td>
                <td>${backup.createdBy}</td>
                <td>
                    <div class="action-buttons-group">
                        <button class="action-btn btn-restore" data-id="${backup.id}" title="恢复">
                            <i class="icon-restore"></i>
                        </button>
                        <button class="action-btn btn-export" data-id="${backup.id}" title="导出">
                            <i class="icon-export"></i>
                        </button>
                        <button class="action-btn btn-details" data-id="${backup.id}" title="详情">
                            <i class="icon-info"></i>
                        </button>
                        <button class="action-btn btn-delete" data-id="${backup.id}" title="删除">
                            <i class="icon-danger"></i>
                        </button>
                    </div>
                </td>
            `;
            tableBody.appendChild(row);
        });
        
        // 添加行操作事件
        addBackupActionsListeners();
        
        // 更新分页信息
        updatePaginationInfo(backups.length);
        
    } catch (error) {
        console.error('加载备份列表失败:', error);
        document.getElementById('backups-table-body').innerHTML = 
            `<tr class="empty-row"><td colspan="7" class="empty-message">加载失败: ${error.message}</td></tr>`;
    }
}

// 添加备份操作事件监听器
function addBackupActionsListeners() {
    // 恢复按钮事件
    document.querySelectorAll('.btn-restore').forEach(button => {
        button.addEventListener('click', async (e) => {
            const backupId = e.currentTarget.getAttribute('data-id');
            await prepareRestoreBackup(backupId);
        });
    });
    
    // 导出按钮事件
    document.querySelectorAll('.btn-export').forEach(button => {
        button.addEventListener('click', async (e) => {
            const backupId = e.currentTarget.getAttribute('data-id');
            await handleExportBackup(backupId);
        });
    });
    
    // 详情按钮事件
    document.querySelectorAll('.btn-details').forEach(button => {
        button.addEventListener('click', async (e) => {
            const backupId = e.currentTarget.getAttribute('data-id');
            await showBackupDetails(backupId);
        });
    });
    
    // 删除按钮事件
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', async (e) => {
            const backupId = e.currentTarget.getAttribute('data-id');
            await prepareDeleteBackup(backupId);
        });
    });
}

// 准备恢复备份
async function prepareRestoreBackup(backupId) {
    try {
        // 获取备份信息
        const backup = await BackupManager.getBackupById(backupId);
        if (!backup) {
            showNotification('备份不存在', 'error');
            return;
        }
        
        // 填充恢复确认模态框
        const backupInfoElement = document.getElementById('restore-backup-info');
        backupInfoElement.innerHTML = `
            <div class="backup-info-item">
                <span class="backup-info-label">备份ID:</span>
                <span class="backup-info-value">${backup.id}</span>
            </div>
            <div class="backup-info-item">
                <span class="backup-info-label">类型:</span>
                <span class="backup-info-value">${backup.type === 'full' ? '完整备份' : '增量备份'}</span>
            </div>
            <div class="backup-info-item">
                <span class="backup-info-label">创建时间:</span>
                <span class="backup-info-value">${formatDate(backup.timestamp)}</span>
            </div>
            <div class="backup-info-item">
                <span class="backup-info-label">大小:</span>
                <span class="backup-info-value">${backup.size}</span>
            </div>
        `;
        
        // 保存备份ID到确认按钮
        document.getElementById('confirm-restore').setAttribute('data-id', backupId);
        
        // 清空恢复原因
        document.getElementById('restore-reason').value = '';
        
        // 显示确认模态框
        showModal('restore-confirm-modal');
        
    } catch (error) {
        console.error('准备恢复备份失败:', error);
        showNotification('准备恢复备份失败: ' + error.message, 'error');
    }
}

// 准备删除备份
async function prepareDeleteBackup(backupId) {
    try {
        // 获取备份信息
        const backup = await BackupManager.getBackupById(backupId);
        if (!backup) {
            showNotification('备份不存在', 'error');
            return;
        }
        
        // 填充删除确认模态框
        const backupInfoElement = document.getElementById('delete-backup-info');
        backupInfoElement.innerHTML = `
            <div class="backup-info-item">
                <span class="backup-info-label">备份ID:</span>
                <span class="backup-info-value">${backup.id}</span>
            </div>
            <div class="backup-info-item">
                <span class="backup-info-label">类型:</span>
                <span class="backup-info-value">${backup.type === 'full' ? '完整备份' : '增量备份'}</span>
            </div>
            <div class="backup-info-item">
                <span class="backup-info-label">创建时间:</span>
                <span class="backup-info-value">${formatDate(backup.timestamp)}</span>
            </div>
        `;
        
        // 保存备份ID到确认按钮
        document.getElementById('confirm-delete').setAttribute('data-id', backupId);
        
        // 显示确认模态框
        showModal('delete-confirm-modal');
        
    } catch (error) {
        console.error('准备删除备份失败:', error);
        showNotification('准备删除备份失败: ' + error.message, 'error');
    }
}

// 显示备份详情
async function showBackupDetails(backupId) {
    try {
        const detailsContent = document.getElementById('backup-details-content');
        detailsContent.innerHTML = '<p>加载备份详情中...</p>';
        
        // 获取备份信息
        const backup = await BackupManager.getBackupById(backupId);
        if (!backup) {
            showNotification('备份不存在', 'error');
            return;
        }
        
        // 填充详情内容
        detailsContent.innerHTML = `
            <div class="details-section">
                <h4>基本信息</h4>
                <div class="details-grid">
                    <div class="details-item">
                        <span class="details-item-label">备份ID</span>
                        <span class="details-item-value">${backup.id}</span>
                    </div>
                    <div class="details-item">
                        <span class="details-item-label">备份类型</span>
                        <span class="details-item-value">${backup.type === 'full' ? '完整备份' : '增量备份'}</span>
                    </div>
                    <div class="details-item">
                        <span class="details-item-label">创建时间</span>
                        <span class="details-item-value">${formatDate(backup.timestamp)}</span>
                    </div>
                    <div class="details-item">
                        <span class="details-item-label">大小</span>
                        <span class="details-item-value">${backup.size}</span>
                    </div>
                </div>
            </div>
            
            <div class="details-section">
                <h4>备份内容</h4>
                <div class="details-grid">
                    <div class="details-item">
                        <span class="details-item-label">配置文件</span>
                        <span class="details-item-value">已包含</span>
                    </div>
                    <div class="details-item">
                        <span class="details-item-label">数据库</span>
                        <span class="details-item-value">已包含</span>
                    </div>
                    <div class="details-item">
                        <span class="details-item-label">系统设置</span>
                        <span class="details-item-value">已包含</span>
                    </div>
                    <div class="details-item">
                        <span class="details-item-label">规则配置</span>
                        <span class="details-item-value">已包含</span>
                    </div>
                </div>
            </div>
        `;
        
        // 显示详情模态框
        showModal('backup-details-modal');
        
    } catch (error) {
        console.error('显示备份详情失败:', error);
        showNotification('显示备份详情失败: ' + error.message, 'error');
    }
}

// 处理创建备份
async function handleCreateBackup() {
    try {
        const backupName = document.getElementById('backup-name').value.trim();
        const backupDescription = document.getElementById('backup-description').value.trim();
        const backupType = document.getElementById('modal-backup-type').value;
        
        // 显示加载状态
        const confirmButton = document.getElementById('confirm-create-backup');
        const originalText = confirmButton.innerHTML;
        confirmButton.disabled = true;
        confirmButton.innerHTML = '<i class="icon-spinner"></i> 创建中...';
        
        // 调用备份管理器创建备份
        let result;
        if (backupType === 'full') {
            result = await BackupManager.createFullBackup(backupName);
        } else {
            result = await BackupManager.createIncrementalBackup(backupName);
        }
        
        if (result.success) {
            showNotification(`备份创建成功: ${result.backupId}`, 'success');
            closeAllModals();
            
            // 刷新备份列表和统计
            await loadBackupsList();
            await loadBackupStatistics();
            
        } else {
            showNotification(`备份创建失败: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error('创建备份失败:', error);
        showNotification('创建备份失败: ' + error.message, 'error');
    } finally {
        // 恢复按钮状态
        const confirmButton = document.getElementById('confirm-create-backup');
        confirmButton.disabled = false;
        confirmButton.innerHTML = '确认创建';
        
        // 清空表单
        document.getElementById('backup-name').value = '';
        document.getElementById('backup-description').value = '';
    }
}

// 处理导入备份
async function handleImportBackup(event) {
    try {
        const file = event.target.files[0];
        if (!file) return;
        
        // 显示加载状态
        const importButton = document.getElementById('import-backup');
        const originalText = importButton.innerHTML;
        importButton.disabled = true;
        importButton.innerHTML = '<i class="icon-spinner"></i> 导入中...';
        
        // 调用备份管理器导入备份
        const result = await BackupManager.importBackup(file);
        
        if (result.success) {
            showNotification(`备份导入成功: ${result.backupId}`, 'success');
            
            // 刷新备份列表和统计
            await loadBackupsList();
            await loadBackupStatistics();
            
        } else {
            showNotification(`备份导入失败: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error('导入备份失败:', error);
        showNotification('导入备份失败: ' + error.message, 'error');
    } finally {
        // 恢复按钮状态
        const importButton = document.getElementById('import-backup');
        importButton.disabled = false;
        importButton.innerHTML = '<i class="icon-import"></i> 导入备份';
        
        // 清空文件输入
        event.target.value = '';
    }
}

// 处理导出备份
async function handleExportBackup(backupId) {
    try {
        // 显示加载状态
        showNotification('正在准备导出...', 'info');
        
        // 调用备份管理器导出备份
        const result = await BackupManager.exportBackup(backupId);
        
        if (result.success) {
            // 创建下载链接
            const downloadLink = document.createElement('a');
            downloadLink.href = result.url;
            downloadLink.download = result.filename;
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
            
            showNotification(`备份导出成功: ${result.filename}`, 'success');
        } else {
            showNotification(`备份导出失败: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error('导出备份失败:', error);
        showNotification('导出备份失败: ' + error.message, 'error');
    }
}

// 处理确认恢复
async function handleConfirmRestore() {
    try {
        const backupId = document.getElementById('confirm-restore').getAttribute('data-id');
        const restoreReason = document.getElementById('restore-reason').value.trim();
        
        if (!restoreReason) {
            showNotification('请输入恢复原因', 'warning');
            return;
        }
        
        // 显示加载状态
        const confirmButton = document.getElementById('confirm-restore');
        confirmButton.disabled = true;
        confirmButton.innerHTML = '<i class="icon-spinner"></i> 恢复中...';
        
        // 调用备份管理器恢复备份
        const result = await BackupManager.restoreFromBackup(backupId);
        
        if (result.success) {
            showNotification(`备份恢复成功。回滚点: ${result.rollbackBackupId}`, 'success');
            closeAllModals();
            
            // 刷新备份列表、统计和恢复历史
            await loadBackupsList();
            await loadBackupStatistics();
            await loadRestoreHistory();
            
        } else {
            showNotification(`备份恢复失败: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error('恢复备份失败:', error);
        showNotification('恢复备份失败: ' + error.message, 'error');
    } finally {
        // 恢复按钮状态
        const confirmButton = document.getElementById('confirm-restore');
        confirmButton.disabled = false;
        confirmButton.innerHTML = '确认恢复';
    }
}

// 处理确认删除
async function handleConfirmDelete() {
    try {
        const backupId = document.getElementById('confirm-delete').getAttribute('data-id');
        
        // 显示加载状态
        const confirmButton = document.getElementById('confirm-delete');
        confirmButton.disabled = true;
        confirmButton.innerHTML = '<i class="icon-spinner"></i> 删除中...';
        
        // 调用备份管理器删除备份
        const success = await BackupManager.deleteBackup(backupId);
        
        if (success) {
            showNotification('备份删除成功', 'success');
            closeAllModals();
            
            // 刷新备份列表和统计
            await loadBackupsList();
            await loadBackupStatistics();
            
        } else {
            showNotification('备份删除失败', 'error');
        }
        
    } catch (error) {
        console.error('删除备份失败:', error);
        showNotification('删除备份失败: ' + error.message, 'error');
    } finally {
        // 恢复按钮状态
        const confirmButton = document.getElementById('confirm-delete');
        confirmButton.disabled = false;
        confirmButton.innerHTML = '确认删除';
    }
}

// 处理比较备份
async function handleCompareBackups() {
    try {
        const backup1Id = document.getElementById('backup-1-select').value;
        const backup2Id = document.getElementById('backup-2-select').value;
        
        if (!backup1Id || !backup2Id) {
            showNotification('请选择两个要比较的备份', 'warning');
            return;
        }
        
        if (backup1Id === backup2Id) {
            showNotification('请选择不同的备份进行比较', 'warning');
            return;
        }
        
        // 显示加载状态
        const compareButton = document.getElementById('compare-button');
        compareButton.disabled = true;
        compareButton.innerHTML = '<i class="icon-spinner"></i> 比较中...';
        
        // 调用备份管理器比较备份
        const result = await BackupManager.compareBackups(backup1Id, backup2Id);
        
        if (result.success) {
            const comparisonResults = document.getElementById('comparison-results');
            comparisonResults.classList.remove('hidden');
            
            // 填充比较结果
            comparisonResults.innerHTML = `
                <div class="comparison-header">
                    <h4>比较结果: ${backup1Id} vs ${backup2Id}</h4>
                </div>
                <div class="comparison-summary">
                    <div class="comparison-stat">
                        <span class="comparison-stat-number stat-added">${result.diff.added.length}</span>
                        <span class="comparison-stat-label">新增</span>
                    </div>
                    <div class="comparison-stat">
                        <span class="comparison-stat-number stat-modified">${result.diff.modified.length}</span>
                        <span class="comparison-stat-label">修改</span>
                    </div>
                    <div class="comparison-stat">
                        <span class="comparison-stat-number stat-deleted">${result.diff.deleted.length}</span>
                        <span class="comparison-stat-label">删除</span>
                    </div>
                </div>
            `;
            
        } else {
            showNotification(`备份比较失败: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error('比较备份失败:', error);
        showNotification('比较备份失败: ' + error.message, 'error');
    } finally {
        // 恢复按钮状态
        const compareButton = document.getElementById('compare-button');
        compareButton.disabled = false;
        compareButton.innerHTML = '执行比较';
    }
}

// 处理搜索备份
function handleBackupSearch() {
    const searchTerm = document.getElementById('backup-search').value.toLowerCase();
    const tableRows = document.querySelectorAll('#backups-table tbody tr');
    
    tableRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        let found = false;
        
        cells.forEach(cell => {
            if (cell.textContent.toLowerCase().includes(searchTerm)) {
                found = true;
            }
        });
        
        row.style.display = found ? '' : 'none';
    });
}

// 处理筛选备份
function handleBackupFilter() {
    const filterType = document.getElementById('backup-filter').value;
    const tableRows = document.querySelectorAll('#backups-table tbody tr');
    
    tableRows.forEach(row => {
        if (filterType === 'all') {
            row.style.display = '';
        } else {
            const typeCell = row.querySelector('td:nth-child(2)');
            if (typeCell) {
                const isMatch = typeCell.textContent.includes(filterType === 'full' ? '完整备份' : '增量备份');
                row.style.display = isMatch ? '' : 'none';
            }
        }
    });
}

// 处理保存设置
async function handleSaveSettings() {
    try {
        // 获取设置值
        const settings = {
            autoBackupEnabled: document.getElementById('auto-backup-enabled').checked,
            backupInterval: document.getElementById('backup-interval').value,
            backupType: document.getElementById('backup-type').value,
            maxBackupVersions: document.getElementById('max-backup-versions').value,
            fullBackupFrequency: document.getElementById('full-backup-frequency').value,
            backupConfigs: document.getElementById('backup-configs').checked,
            backupDatabase: document.getElementById('backup-database').checked,
            backupLogs: document.getElementById('backup-logs').checked
        };
        
        // 显示保存状态
        const saveButton = document.getElementById('save-settings');
        saveButton.disabled = true;
        saveButton.innerHTML = '<i class="icon-spinner"></i> 保存中...';
        
        // 实际实现中会保存到服务器或本地存储
        console.log('保存备份设置:', settings);
        
        // 模拟保存延迟
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        showNotification('备份设置保存成功', 'success');
        
    } catch (error) {
        console.error('保存设置失败:', error);
        showNotification('保存设置失败: ' + error.message, 'error');
    } finally {
        // 恢复按钮状态
        const saveButton = document.getElementById('save-settings');
        saveButton.disabled = false;
        saveButton.innerHTML = '保存设置';
    }
}

// 处理重置设置
function handleResetSettings() {
    if (confirm('确定要恢复默认设置吗？')) {
        // 恢复默认设置
        document.getElementById('auto-backup-enabled').checked = true;
        document.getElementById('backup-interval').value = '24';
        document.getElementById('backup-type').value = 'incremental';
        document.getElementById('max-backup-versions').value = '30';
        document.getElementById('full-backup-frequency').value = 'weekly';
        document.getElementById('backup-configs').checked = true;
        document.getElementById('backup-database').checked = true;
        document.getElementById('backup-logs').checked = false;
        
        showNotification('设置已恢复默认值', 'success');
    }
}

// 处理退出登录
function handleLogout() {
    if (confirm('确定要退出登录吗？')) {
        // 实际实现中会调用登出API
        console.log('用户退出登录');
        // 跳转到登录页
        window.location.href = 'login.html';
    }
}

// 加载备份统计数据
async function loadBackupStatistics() {
    try {
        // 获取所有备份
        const backups = await BackupManager.getAllBackups();
        
        // 计算统计数据
        const fullBackups = backups.filter(b => b.type === 'full');
        const incrementalBackups = backups.filter(b => b.type === 'incremental');
        
        // 更新统计显示
        document.getElementById('full-backups-count').textContent = fullBackups.length;
        document.getElementById('incremental-backups-count').textContent = incrementalBackups.length;
        
        // 更新最近备份信息
        if (fullBackups.length > 0) {
            const latestFull = fullBackups.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))[0];
            document.getElementById('last-full-backup').textContent = formatDate(latestFull.timestamp);
        } else {
            document.getElementById('last-full-backup').textContent = '无';
        }
        
        if (incrementalBackups.length > 0) {
            const latestIncremental = incrementalBackups.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))[0];
            document.getElementById('last-incremental-backup').textContent = formatDate(latestIncremental.timestamp);
        } else {
            document.getElementById('last-incremental-backup').textContent = '无';
        }
        
        // 更新存储使用情况（模拟数据）
        document.getElementById('storage-usage').textContent = '1.2 GB';
        document.getElementById('storage-percentage').textContent = '45%';
        
    } catch (error) {
        console.error('加载备份统计失败:', error);
    }
}

// 加载备份设置
async function loadBackupSettings() {
    try {
        // 实际实现中会从服务器或本地存储加载设置
        // 这里使用默认值
        document.getElementById('auto-backup-enabled').checked = true;
        document.getElementById('backup-interval').value = '24';
        document.getElementById('backup-type').value = 'incremental';
        document.getElementById('max-backup-versions').value = '30';
        document.getElementById('full-backup-frequency').value = 'weekly';
        document.getElementById('backup-configs').checked = true;
        document.getElementById('backup-database').checked = true;
        document.getElementById('backup-logs').checked = false;
        
    } catch (error) {
        console.error('加载备份设置失败:', error);
    }
}

// 加载恢复历史
async function loadRestoreHistory() {
    try {
        const tableBody = document.getElementById('restore-history-body');
        
        // 模拟恢复历史数据
        const restoreHistory = [
            {
                timestamp: '2025-11-16T10:30:00Z',
                backupId: 'full-2025-11-15T08:00:00Z',
                operator: 'admin',
                status: 'success',
                reason: '系统配置错误，恢复到前一天的备份'
            },
            {
                timestamp: '2025-11-10T14:15:00Z',
                backupId: 'full-2025-11-09T08:00:00Z',
                operator: 'system',
                status: 'success',
                reason: '自动恢复操作'
            }
        ];
        
        if (restoreHistory.length === 0) {
            tableBody.innerHTML = '<tr class="empty-row"><td colspan="6" class="empty-message">暂无恢复历史记录</td></tr>';
            return;
        }
        
        // 清空表格
        tableBody.innerHTML = '';
        
        // 填充表格数据
        restoreHistory.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${formatDate(record.timestamp)}</td>
                <td>${record.backupId}</td>
                <td>${record.operator}</td>
                <td>
                    <span class="backup-type-tag tag-${record.status}">${record.status === 'success' ? '成功' : '失败'}</span>
                </td>
                <td>${record.reason}</td>
                <td>
                    <div class="action-buttons-group">
                        <button class="action-btn btn-details" data-id="${record.backupId}" title="查看备份详情">
                            <i class="icon-info"></i>
                        </button>
                    </div>
                </td>
            `;
            tableBody.appendChild(row);
        });
        
        // 更新恢复计数
        document.getElementById('restore-count').textContent = restoreHistory.length;
        
        if (restoreHistory.length > 0) {
            const latestRestore = restoreHistory.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))[0];
            document.getElementById('last-restore').textContent = formatDate(latestRestore.timestamp);
        }
        
    } catch (error) {
        console.error('加载恢复历史失败:', error);
    }
}

// 更新分页信息
function updatePaginationInfo(totalItems) {
    document.getElementById('total-items').textContent = totalItems;
    document.getElementById('showing-range').textContent = totalItems > 0 ? '1-' + Math.min(totalItems, 10) : '0-0';
    
    // 更新分页按钮状态
    document.getElementById('prev-page').disabled = true;
    document.getElementById('next-page').disabled = totalItems <= 10;
}

// 上一页
function goToPrevPage() {
    // 实际实现中会加载上一页数据
    console.log('上一页');
}

// 下一页
function goToNextPage() {
    // 实际实现中会加载下一页数据
    console.log('下一页');
}

// 显示通知
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    const notificationMessage = document.getElementById('notification-message');
    const notificationIcon = document.getElementById('notification-icon');
    
    // 设置消息和类型
    notificationMessage.textContent = message;
    notification.className = 'notification show ' + type;
    
    // 设置图标
    notificationIcon.className = 'notification-icon';
    if (type === 'success') notificationIcon.classList.add('icon-success');
    else if (type === 'error') notificationIcon.classList.add('icon-danger');
    else if (type === 'warning') notificationIcon.classList.add('icon-warning');
    else notificationIcon.classList.add('icon-info');
    
    // 自动关闭
    setTimeout(() => {
        notification.classList.remove('show');
    }, 5000);
    
    // 关闭按钮事件
    document.querySelector('.close-notification').addEventListener('click', () => {
        notification.classList.remove('show');
    });
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        loadBackupsList,
        handleCreateBackup,
        handleRestoreBackup: handleConfirmRestore,
        handleDeleteBackup: handleConfirmDelete,
        showNotification
    };
}
