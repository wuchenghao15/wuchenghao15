
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

        // 用户操作记录（内存存储）
        let userActions = [];

        // 初始化页面
        document.addEventListener('DOMContentLoaded', function() {
            // 初始化选项卡
            initTabs();
            
            // 加载数据
            loadSystemStats();
            loadUsers();
            loadAISettings();
            
            // 设置AI提示
            updateAIPrompt();
            
            // 监听风险阈值变化
            document.getElementById('aiRiskThreshold').addEventListener('input', function() {
                document.getElementById('riskThresholdValue').textContent = this.value;
            });
        });

        // 初始化选项卡
        function initTabs() {
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    // 移除所有活动状态
                    tabs.forEach(t => t.classList.remove('active'));
                    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                    
                    // 添加当前活动状态
                    this.classList.add('active');
                    const tabId = this.getAttribute('data-tab');
                    document.getElementById(tabId).classList.add('active');
                });
            });
        }

        // 更新AI提示
        function updateAIPrompt() {
            // 从localStorage获取设置
            const aiSettings = JSON.parse(localStorage.getItem('aiSettings') || '{}');
            const enabled = aiSettings.enabled !== false;
            const message = aiSettings.message || 'AI正在管理此操作，将提供智能优化建议';
            
            const aiPrompt = document.getElementById('aiPrompt');
            const aiPromptMessage = document.getElementById('aiPromptMessage');
            
            aiPrompt.style.display = enabled ? 'block' : 'none';
            aiPromptMessage.textContent = message;
        }

        // 加载系统统计
        async function loadSystemStats() {
            try {
                // 模拟获取系统统计
                const stats = {
                    totalUsers: Math.floor(Math.random() * 100) + 10,
                    activeUsers: Math.floor(Math.random() * 20) + 5,
                    highRiskActions: Math.floor(Math.random() * 5),
                    aiOptimizedTasks: Math.floor(Math.random() * 15) + 5
                };
                
                const container = document.getElementById('systemStats');
                container.innerHTML = `
                    <div class="stat-item">
                        <div class="stat-value">${stats.totalUsers}</div>
                        <div class="stat-label">总用户数</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.activeUsers}</div>
                        <div class="stat-label">活跃用户</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.highRiskActions}</div>
                        <div class="stat-label">高风险操作</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.aiOptimizedTasks}</div>
                        <div class="stat-label">AI优化任务</div>
                    </div>
                `;
            } catch (error) {
                console.error('加载系统统计失败:', error);
            }
        }

        // 加载用户列表
        async function loadUsers() {
            try {
                const response = await fetch('https://localhost:8080/api/users', { method: 'GET', mode: 'cors' });
                const data = await response.json();
                if (data.success) {
                    const users = data.users;
                    const tbody = document.querySelector('#usersTable tbody');
                    tbody.innerHTML = users.map(user => `
                        <tr>
                            <td>${user.username}</td>
                            <td>${user.email}</td>
                            <td>${user.role}</td>
                            <td>${new Date(user.created_at).toLocaleString()}</td>
                            <td>
                                <button class="btn btn-danger btn-sm" onclick="deleteUser('${user.username}')">删除</button>
                            </td>
                        </tr>
                    `).join('');
                }
            } catch (error) {
                console.error('加载用户列表失败:', error);
                // 显示模拟数据
                const tbody = document.querySelector('#usersTable tbody');
                tbody.innerHTML = `
                    <tr>
                        <td>admin</td>
                        <td>admin@example.com</td>
                        <td>admin</td>
                        <td>${new Date().toLocaleString()}</td>
                        <td>
                            <button class="btn btn-danger btn-sm" onclick="deleteUser('admin')">删除</button>
                        </td>
                    </tr>
                    <tr>
                        <td>user</td>
                        <td>user@example.com</td>
                        <td>user</td>
                        <td>${new Date().toLocaleString()}</td>
                        <td>
                            <button class="btn btn-danger btn-sm" onclick="deleteUser('user')">删除</button>
                        </td>
                    </tr>
                `;
            }
        }

        // 刷新用户列表
        function refreshUsers() {
            loadUsers();
        }

        // 删除用户
        function deleteUser(username) {
            if (confirm(`确定要删除用户 ${username} 吗？`)) {
                // 这里可以添加实际的删除逻辑
                alert(`用户 ${username} 已删除`);
                loadUsers();
            }
        }

        // 执行登录
        async function performLogin() {
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;
            const resultDiv = document.getElementById('loginResult');
            
            if (!username || !password) {
                resultDiv.innerHTML = '<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 6px;">用户名和密码不能为空</div>';
                return;
            }
            
            resultDiv.innerHTML = '<div class="loading">正在登录...</div>';
            
            try {
                const response = await fetch('https://localhost:8080/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                let html = '';
                if (data.success) {
                    html += '<div style="background: #d4edda; color: #155724; padding: 15px; border-radius: 6px;">';
                    html += `<h3>登录成功！</h3>`;
                    html += `<p>欢迎，${data.user.username}！</p>`;
                    
                    // 添加AI增强信息
                    if (data.ai_enhancement) {
                        html += '<div style="margin-top: 10px;">';
                        html += '<h4>AI增强信息：</h4>';
                        if (data.ai_enhancement.verification) {
                            const riskScore = data.ai_enhancement.verification.riskScore;
                            let riskLevel = 'low';
                            if (riskScore > 0.7) riskLevel = 'high';
                            else if (riskScore > 0.4) riskLevel = 'medium';
                            
                            html += `<p>风险评分：<span class="risk-score risk-${riskLevel}">${riskScore.toFixed(2)}</span></p>`;
                        }
                        
                        if (data.ai_enhancement.suggestions && data.ai_enhancement.suggestions.length > 0) {
                            html += '<h4>AI建议：</h4>';
                            data.ai_enhancement.suggestions.forEach(suggestion => {
                                html += `<div class="ai-suggestion">${suggestion}</div>`;
                            });
                        }
                        html += '</div>';
                    }
                    html += '</div>';
                } else {
                    html += '<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 6px;">';
                    html += `<h3>登录失败！</h3>`;
                    html += `<p>${data.message}</p>`;
                    html += '</div>';
                }
                
                // 添加AI提示
                if (data.ai_prompt) {
                    html += `<div class="ai-prompt">
                        <strong>AI提示：</strong> ${data.ai_prompt.message}
                    </div>`;
                }
                
                resultDiv.innerHTML = html;
                
                // 记录操作
                logUserAction(username, 'login', data.success, data);
                refreshUserActions();
                
            } catch (error) {
                console.error('登录失败:', error);
                resultDiv.innerHTML = '<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 6px;">登录失败，请检查网络连接</div>';
            }
        }

        // 执行注册
        async function performRegister() {
            const username = document.getElementById('registerUsername').value;
            const email = document.getElementById('registerEmail').value;
            const password = document.getElementById('registerPassword').value;
            const resultDiv = document.getElementById('registerResult');
            
            if (!username || !email || !password) {
                resultDiv.innerHTML = '<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 6px;">用户名、邮箱和密码不能为空</div>';
                return;
            }
            
            resultDiv.innerHTML = '<div class="loading">正在注册...</div>';
            
            try {
                const response = await fetch('https://localhost:8080/api/auth/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, email, password })
                });
                
                const data = await response.json();
                
                let html = '';
                if (data.success) {
                    html += '<div style="background: #d4edda; color: #155724; padding: 15px; border-radius: 6px;">';
                    html += `<h3>注册成功！</h3>`;
                    html += `<p>${data.message}</p>`;
                    
                    // 添加AI增强信息
                    if (data.ai_enhancement) {
                        html += '<div style="margin-top: 10px;">';
                        html += '<h4>AI增强信息：</h4>';
                        if (data.ai_enhancement.approval) {
                            const riskScore = data.ai_enhancement.approval.riskScore;
                            let riskLevel = 'low';
                            if (riskScore > 0.7) riskLevel = 'high';
                            else if (riskScore > 0.4) riskLevel = 'medium';
                            
                            html += `<p>风险评分：<span class="risk-score risk-${riskLevel}">${riskScore.toFixed(2)}</span></p>`;
                        }
                        
                        if (data.ai_enhancement.suggestions && data.ai_enhancement.suggestions.length > 0) {
                            html += '<h4>AI建议：</h4>';
                            data.ai_enhancement.suggestions.forEach(suggestion => {
                                html += `<div class="ai-suggestion">${suggestion}</div>`;
                            });
                        }
                        html += '</div>';
                    }
                    html += '</div>';
                } else {
                    html += '<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 6px;">';
                    html += `<h3>注册失败！</h3>`;
                    html += `<p>${data.message}</p>`;
                    
                    // 添加AI增强信息
                    if (data.ai_enhancement) {
                        html += '<div style="margin-top: 10px;">';
                        html += '<h4>AI拒绝原因：</h4>';
                        if (data.ai_enhancement.riskScore) {
                            const riskScore = data.ai_enhancement.riskScore;
                            let riskLevel = 'low';
                            if (riskScore > 0.7) riskLevel = 'high';
                            else if (riskScore > 0.4) riskLevel = 'medium';
                            
                            html += `<p>风险评分：<span class="risk-score risk-${riskLevel}">${riskScore.toFixed(2)}</span></p>`;
                        }
                        
                        if (data.ai_enhancement.aiSuggestions && data.ai_enhancement.aiSuggestions.length > 0) {
                            html += '<h4>AI建议：</h4>';
                            data.ai_enhancement.aiSuggestions.forEach(suggestion => {
                                html += `<div class="ai-suggestion">${suggestion}</div>`;
                            });
                        }
                        html += '</div>';
                    }
                    html += '</div>';
                }
                
                // 添加AI提示
                if (data.ai_prompt) {
                    html += `<div class="ai-prompt">
                        <strong>AI提示：</strong> ${data.ai_prompt.message}
                    </div>`;
                }
                
                resultDiv.innerHTML = html;
                
                // 记录操作
                logUserAction(username, 'register', data.success, data);
                refreshUserActions();
                
            } catch (error) {
                console.error('注册失败:', error);
                resultDiv.innerHTML = '<div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 6px;">注册失败，请检查网络连接</div>';
            }
        }

        // 记录用户操作
        function logUserAction(username, action, success, details = {}) {
            const actionLog = {
                username,
                action,
                success,
                timestamp: new Date().toISOString(),
                details
            };
            
            userActions.unshift(actionLog);
            
            // 限制最多保存100条记录
            if (userActions.length > 100) {
                userActions = userActions.slice(0, 100);
            }
            
            // 保存到localStorage
            localStorage.setItem('userActions', JSON.stringify(userActions));
            
            // 更新显示
            updateUserActionsDisplay();
        }

        // 更新用户操作显示
        function updateUserActionsDisplay() {
            const container = document.getElementById('userActions');
            
            if (userActions.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #7f8c8d;">暂无用户操作记录</p>';
                return;
            }
            
            const html = userActions.map(action => {
                const statusClass = action.success ? 'success' : 'error';
                return `
                    <div class="action-log">
                        <strong>${new Date(action.timestamp).toLocaleString()}</strong> - 
                        <strong>${action.username}</strong> - 
                        <span style="color: ${action.success ? '#27ae60' : '#e74c3c'}">${action.action} ${action.success ? '成功' : '失败'}</span>
                        <div style="margin-top: 5px; padding-left: 20px;">
                            ${JSON.stringify(action.details, null, 2)}
                        </div>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = html;
        }

        // 刷新用户操作记录
        function refreshUserActions() {
            // 从localStorage加载
            const savedActions = localStorage.getItem('userActions');
            if (savedActions) {
                userActions = JSON.parse(savedActions);
            }
            updateUserActionsDisplay();
        }

        // 清除用户操作记录
        function clearUserActions() {
            if (confirm('确定要清除所有操作记录吗？')) {
                userActions = [];
                localStorage.removeItem('userActions');
                updateUserActionsDisplay();
            }
        }

        // 加载AI设置
        function loadAISettings() {
            const aiSettings = JSON.parse(localStorage.getItem('aiSettings') || '{}');
            
            document.getElementById('aiTakeoverEnabled').value = aiSettings.enabled !== false ? 'true' : 'false';
            document.getElementById('aiTakeoverMessage').value = aiSettings.message || 'AI正在管理此操作，将提供智能优化建议';
            document.getElementById('aiRiskThreshold').value = aiSettings.riskThreshold || 0.7;
            document.getElementById('riskThresholdValue').textContent = aiSettings.riskThreshold || 0.7;
        }

        // 保存AI设置
        function saveAISettings() {
            const aiSettings = {
                enabled: document.getElementById('aiTakeoverEnabled').value === 'true',
                message: document.getElementById('aiTakeoverMessage').value,
                riskThreshold: parseFloat(document.getElementById('aiRiskThreshold').value)
            };
            
            localStorage.setItem('aiSettings', JSON.stringify(aiSettings));
            updateAIPrompt();
            alert('AI设置已保存');
        }

        // 初始加载用户操作记录
        refreshUserActions();
    