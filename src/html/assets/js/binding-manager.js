
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

        // 切换标签
        function switchTab(tabId) {
            // 移除所有标签的活动状态
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // 移除所有内容的活动状态
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // 激活选中的标签和内容
            document.querySelector(`[onclick="switchTab('${tabId}')"]`).classList.add('active');
            document.getElementById(tabId).classList.add('active');
            
            // 加载对应标签的内容
            if (tabId === 'config-management') {
                loadConfigList();
            } else if (tabId === 'page-binding') {
                loadPageList();
            } else if (tabId === 'usage-monitoring') {
                loadUsageStats();
            }
        }

        // 显示加载状态
        function showLoading(elementId) {
            document.getElementById(elementId).innerHTML = '<div class="loading">加载中...</div>';
        }

        // 显示成功消息
        function showSuccess(elementId, message) {
            document.getElementById(elementId).innerHTML = `<div class="alert alert-success">${message}</div>`;
        }

        // 显示错误消息
        function showError(elementId, message) {
            document.getElementById(elementId).innerHTML = `<div class="alert alert-error">${message}</div>`;
        }

        // 加载配置列表
        async function loadConfigList() {
            showLoading('config-list');
            try {
                const response = await fetch('/api/binding/config/all');
                const data = await response.json();
                if (data.success) {
                    const configList = document.getElementById('config-list');
                    let html = '';
                    Object.keys(data.data).forEach(configName => {
                        html += `
                            <div class="config-item">
                                <span class="config-name">${configName}</span>
                                <div class="config-actions">
                                    <button class="btn btn-secondary" onclick="viewConfig('${configName}')">查看</button>
                                    <button class="btn" onclick="editConfig('${configName}')">编辑</button>
                                </div>
                            </div>
                        `;
                    });
                    configList.innerHTML = html;
                } else {
                    showError('config-list', data.error);
                }
            } catch (error) {
                showError('config-list', '加载配置列表失败: ' + error.message);
            }
        }

        // 查看配置详情
        async function viewConfig(configName) {
            showLoading('config-detail');
            try {
                const response = await fetch('/api/binding/config/get', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ configName })
                });
                const data = await response.json();
                if (data.success) {
                    const configDetail = document.getElementById('config-detail');
                    configDetail.innerHTML = `
                        <div class="card">
                            <h3>${configName}</h3>
                            <pre>${JSON.stringify(data.data, null, 2)}</pre>
                        </div>
                    `;
                } else {
                    showError('config-detail', data.error);
                }
            } catch (error) {
                showError('config-detail', '加载配置详情失败: ' + error.message);
            }
        }

        // 编辑配置
        async function editConfig(configName) {
            showLoading('config-detail');
            try {
                const response = await fetch('/api/binding/config/get', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ configName })
                });
                const data = await response.json();
                if (data.success) {
                    const configDetail = document.getElementById('config-detail');
                    configDetail.innerHTML = `
                        <div class="card">
                            <h3>编辑 ${configName}</h3>
                            <div class="form-group">
                                <label for="config-data">配置内容</label>
                                <textarea id="config-data">${JSON.stringify(data.data, null, 2)}</textarea>
                            </div>
                            <button class="btn" onclick="updateConfig('${configName}')">保存更改</button>
                        </div>
                    `;
                } else {
                    showError('config-detail', data.error);
                }
            } catch (error) {
                showError('config-detail', '加载配置详情失败: ' + error.message);
            }
        }

        // 更新配置
        async function updateConfig(configName) {
            const configData = document.getElementById('config-data').value;
            try {
                const parsedData = JSON.parse(configData);
                const response = await fetch('/api/binding/config/update', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ configName, configData: parsedData })
                });
                const data = await response.json();
                if (data.success) {
                    showSuccess('config-detail', '配置更新成功');
                    loadConfigList();
                } else {
                    showError('config-detail', data.error);
                }
            } catch (error) {
                showError('config-detail', '更新配置失败: ' + error.message);
            }
        }

        // 加载页面列表
        async function loadPageList() {
            showLoading('page-list');
            try {
                const response = await fetch('/api/binding/pages/scan');
                const data = await response.json();
                if (data.success) {
                    const pageList = document.getElementById('page-list');
                    let html = '';
                    data.data.forEach(pageUrl => {
                        html += `
                            <div class="page-item">
                                <span class="page-url">${pageUrl}</span>
                                <div class="page-actions">
                                    <button class="btn btn-secondary" onclick="viewPageConfig('${pageUrl}')">查看配置</button>
                                </div>
                            </div>
                        `;
                    });
                    pageList.innerHTML = html;
                } else {
                    showError('page-list', data.error);
                }
            } catch (error) {
                showError('page-list', '加载页面列表失败: ' + error.message);
            }
        }

        // 查看页面配置
        async function viewPageConfig(pageUrl) {
            showLoading('page-config-detail');
            try {
                const response = await fetch('/api/binding/page/get', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ pageUrl })
                });
                const data = await response.json();
                if (data.success) {
                    const pageConfigDetail = document.getElementById('page-config-detail');
                    let html = '<div class="card">';
                    html += `<h3>${pageUrl} 的配置</h3>`;
                    if (Object.keys(data.data).length > 0) {
                        Object.keys(data.data).forEach(configName => {
                            html += `
                                <h4>${configName}</h4>
                                <pre>${JSON.stringify(data.data[configName], null, 2)}</pre>
                                <hr>
                            `;
                        });
                    } else {
                        html += '<p>该页面未绑定任何配置</p>';
                    }
                    html += '</div>';
                    pageConfigDetail.innerHTML = html;
                } else {
                    showError('page-config-detail', data.error);
                }
            } catch (error) {
                showError('page-config-detail', '加载页面配置失败: ' + error.message);
            }
        }

        // 绑定配置到页面
        async function bindConfigToPage() {
            const pageUrl = document.getElementById('page-url').value;
            const configNames = document.getElementById('config-names').value.split(',').map(name => name.trim());
            try {
                const response = await fetch('/api/binding/page/bind', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ pageUrl, configNames })
                });
                const data = await response.json();
                if (data.success) {
                    showSuccess('page-list', '配置绑定成功');
                    loadPageList();
                } else {
                    showError('page-list', data.error);
                }
            } catch (error) {
                showError('page-list', '绑定配置失败: ' + error.message);
            }
        }

        // 绑定所有配置到页面
        async function bindAllConfigsToPage() {
            const pageUrl = document.getElementById('page-url').value;
            try {
                const response = await fetch('/api/binding/page/bind-all', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ pageUrl })
                });
                const data = await response.json();
                if (data.success) {
                    showSuccess('page-list', '所有配置绑定成功');
                    loadPageList();
                } else {
                    showError('page-list', data.error);
                }
            } catch (error) {
                showError('page-list', '绑定所有配置失败: ' + error.message);
            }
        }

        // 加载使用统计
        async function loadUsageStats() {
            showLoading('usage-stats');
            try {
                const response = await fetch('/api/binding/usage/stats');
                const data = await response.json();
                if (data.success) {
                    const usageStats = document.getElementById('usage-stats');
                    let html = '';
                    if (data.data && typeof data.data === 'object') {
                        Object.keys(data.data).forEach(configName => {
                            const stats = data.data[configName] || { totalUsage: 0, lastUsed: null, usagePatterns: [] };
                            html += `
                                <div class="stats-item">
                                    <span class="stats-name">${configName}</span>
                                    <span class="stats-value">使用次数: ${stats.totalUsage}, 最后使用: ${stats.lastUsed}</span>
                                </div>
                            `;
                        });
                    }
                    if (html === '') {
                        html = '<div class="stats-item"><span class="stats-name">暂无使用统计数据</span></div>';
                    }
                    usageStats.innerHTML = html;
                } else {
                    showError('usage-stats', data.error);
                }
            } catch (error) {
                showError('usage-stats', '加载使用统计失败: ' + error.message);
            }
        }

        // 记录配置使用
        async function recordConfigUsage() {
            const configName = document.getElementById('usage-config-name').value;
            const usageData = document.getElementById('usage-data').value;
            try {
                const parsedData = JSON.parse(usageData);
                const response = await fetch('/api/binding/usage/record', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ configName, usageData: parsedData })
                });
                const data = await response.json();
                if (data.success) {
                    showSuccess('usage-stats', '使用记录成功');
                    loadUsageStats();
                } else {
                    showError('usage-stats', data.error);
                }
            } catch (error) {
                showError('usage-stats', '记录使用失败: ' + error.message);
            }
        }

        // 扫描页面
        async function scanPages() {
            showLoading('scan-result');
            try {
                const response = await fetch('/api/binding/pages/scan');
                const data = await response.json();
                if (data.success) {
                    const scanResult = document.getElementById('scan-result');
                    let html = '<div class="card">';
                    html += '<h3>扫描结果</h3>';
                    html += `<p>找到 ${data.data.length} 个页面</p>`;
                    html += '<ul>';
                    data.data.forEach(pageUrl => {
                        html += `<li>${pageUrl}</li>`;
                    });
                    html += '</ul>';
                    html += '</div>';
                    scanResult.innerHTML = html;
                } else {
                    showError('scan-result', data.error);
                }
            } catch (error) {
                showError('scan-result', '扫描页面失败: ' + error.message);
            }
        }

        // 自动绑定配置
        async function autoBindConfigs() {
            try {
                const response = await fetch('/api/binding/auto-bind', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({})
                });
                const data = await response.json();
                if (data.success) {
                    showSuccess('auto-binding', data.message);
                    scanPages();
                } else {
                    showError('auto-binding', data.error);
                }
            } catch (error) {
                showError('auto-binding', '自动绑定失败: ' + error.message);
            }
        }

        // 刷新所有配置
        async function refreshAll() {
            try {
                await loadConfigList();
                await loadPageList();
                await loadUsageStats();
                showSuccess('config-list', '所有配置已刷新');
                // 延迟一秒后重新加载页面
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } catch (error) {
                showError('config-list', '刷新配置失败: ' + error.message);
            }
        }

        // 初始化加载
        window.onload = function() {
            loadConfigList();
        };
    