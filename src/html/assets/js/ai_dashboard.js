
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

        // 初始化页面
        document.addEventListener('DOMContentLoaded', function() {
            // 初始化选项卡
            initTabs();
            
            // 加载数据
            loadSystemStats();
            loadAIInstances();
            loadTasks();
            loadOptimizationHistory();
            loadSupervisionTree();
            loadSupervisionStats();
            
            // 定期刷新数据（每30秒）
            setInterval(() => {
                loadSystemStats();
                loadAIInstances();
                loadTasks();
                loadSupervisionTree();
                loadSupervisionStats();
            }, 30000);
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

        // 加载系统统计数据
        async function loadSystemStats() {
            try {
                const response = await fetch('/api/ai/status');
                const data = await response.json();
                if (data.success) {
                    const stats = data.data;
                    const statsHTML = `
                        <div class="stat-item">
                            <div class="stat-value">${stats.totalAI}</div>
                            <div class="stat-label">总AI数</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${stats.idleAI}</div>
                            <div class="stat-label">空闲AI</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${stats.busyAI}</div>
                            <div class="stat-label">忙碌AI</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${stats.totalTasks}</div>
                            <div class="stat-label">总任务数</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${stats.pendingTasks}</div>
                            <div class="stat-label">待处理任务</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${stats.inProgressTasks}</div>
                            <div class="stat-label">进行中任务</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${stats.completedTasks}</div>
                            <div class="stat-label">已完成任务</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${stats.optimizationHistoryCount}</div>
                            <div class="stat-label">优化历史数</div>
                        </div>
                    `;
                    document.getElementById('systemStats').innerHTML = statsHTML;
                }
            } catch (error) {
                console.error('加载系统统计失败:', error);
            }
        }

        // 加载AI实例数据
        async function loadAIInstances() {
            try {
                const response = await fetch('/api/ai/instances');
                const data = await response.json();
                if (data.success) {
                    const instances = data.data;
                    const tbody = document.querySelector('#aiInstancesTable tbody');
                    tbody.innerHTML = instances.map(ai => `
                        <tr>
                            <td>${ai.id}</td>
                            <td>${ai.name}</td>
                            <td>${ai.role}</td>
                            <td>${ai.group}</td>
                            <td><span class="status-badge status-${ai.status}">${ai.status}</span></td>
                            <td>${ai.isMainAI ? '是' : '否'}</td>
                            <td>${ai.supervisorId || '-'}</td>
                            <td>${ai.subordinateIds.length}</td>
                            <td>${ai.currentTask ? ai.currentTask.name : '-'}</td>
                            <td>
                                <button class="btn btn-danger btn-sm" onclick="removeAIInstance('${ai.id}')">移除</button>
                            </td>
                        </tr>
                    `).join('');
                }
            } catch (error) {
                console.error('加载AI实例失败:', error);
            }
        }

        // 刷新监管关系
        async function refreshSupervision() {
            await loadAIInstances();
            loadSupervisionTree();
            loadSupervisionStats();
        }

        // 重新分配监管
        async function reassignSupervision() {
            if (confirm('确定要重新分配监管关系吗？')) {
                try {
                    // 这里可以添加重新分配监管的API调用
                    await loadAIInstances();
                    loadSupervisionTree();
                    loadSupervisionStats();
                    alert('监管关系已重新分配');
                } catch (error) {
                    console.error('重新分配监管失败:', error);
                    alert('重新分配监管失败: ' + error.message);
                }
            }
        }

        // 加载监管关系树
        async function loadSupervisionTree() {
            try {
                const response = await fetch('/api/ai/instances');
                const data = await response.json();
                if (data.success) {
                    const instances = data.data;
                    const container = document.getElementById('supervisionTree');
                    
                    // 构建监管关系树
                    const mainAIs = instances.filter(ai => ai.isMainAI);
                    const aIsById = instances.reduce((map, ai) => {
                        map[ai.id] = ai;
                        return map;
                    }, {});
                    
                    let treeHTML = '<h3>监管关系树</h3>';
                    mainAIs.forEach(mainAI => {
                        treeHTML += `
                            <div style="margin-bottom: 15px; padding: 15px; background: white; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                                <div style="font-weight: bold; color: #3498db; margin-bottom: 10px;">
                                    主AI: ${mainAI.name} (${mainAI.role})
                                </div>
                                <div style="margin-left: 20px;">
                        `;
                        
                        // 添加子AI
                        if (mainAI.subordinateIds.length > 0) {
                            treeHTML += '<h4>子AI列表:</h4>';
                            mainAI.subordinateIds.forEach(subAIId => {
                                const subAI = aIsById[subAIId];
                                if (subAI) {
                                    treeHTML += `
                                        <div style="margin: 5px 0; padding: 5px; background: #f8f9fa; border-radius: 4px;">
                                            子AI: ${subAI.name} (${subAI.role}) - 状态: <span class="status-badge status-${subAI.status}">${subAI.status}</span>
                                        </div>
                                    `;
                                }
                            });
                        } else {
                            treeHTML += '<p>暂无子AI</p>';
                        }
                        
                        treeHTML += `
                                </div>
                            </div>
                        `;
                    });
                    
                    container.innerHTML = treeHTML;
                }
            } catch (error) {
                console.error('加载监管关系树失败:', error);
            }
        }

        // 加载监管统计
        async function loadSupervisionStats() {
            try {
                const response = await fetch('/api/ai/instances');
                const data = await response.json();
                if (data.success) {
                    const instances = data.data;
                    const container = document.getElementById('supervisionStats');
                    
                    // 计算统计数据
                    const totalAIs = instances.length;
                    const mainAIs = instances.filter(ai => ai.isMainAI).length;
                    const subAIs = instances.filter(ai => !ai.isMainAI).length;
                    const supervisedAIs = instances.filter(ai => ai.supervisorId).length;
                    const unsupervisedAIs = instances.filter(ai => !ai.supervisorId && !ai.isMainAI).length;
                    
                    container.innerHTML = `
                        <div class="stat-item">
                            <div class="stat-value">${totalAIs}</div>
                            <div class="stat-label">总AI数</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${mainAIs}</div>
                            <div class="stat-label">主AI数</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${subAIs}</div>
                            <div class="stat-label">子AI数</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${supervisedAIs}</div>
                            <div class="stat-label">已监管AI数</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${unsupervisedAIs}</div>
                            <div class="stat-label">未监管AI数</div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('加载监管统计失败:', error);
            }
        }

        // 加载任务数据
        async function loadTasks() {
            try {
                const response = await fetch('/api/ai/tasks');
                const data = await response.json();
                if (data.success) {
                    const tasks = data.data;
                    const tbody = document.querySelector('#tasksTable tbody');
                    tbody.innerHTML = tasks.map(task => `
                        <tr>
                            <td>${task.id}</td>
                            <td>${task.name}</td>
                            <td>${task.type}</td>
                            <td><span class="priority-${task.priority}">${task.priority}</span></td>
                            <td><span class="task-status-${task.status}">${task.status}</span></td>
                            <td>${task.assignedTo || '-'}</td>
                            <td>${new Date(task.createdAt).toLocaleString()}</td>
                            <td>${task.completedAt ? new Date(task.completedAt).toLocaleString() : '-'}</td>
                        </tr>
                    `).join('');
                }
            } catch (error) {
                console.error('加载任务失败:', error);
            }
        }

        // 加载优化历史
        async function loadOptimizationHistory() {
            try {
                const response = await fetch('/api/ai/history');
                const data = await response.json();
                if (data.success) {
                    const history = data.data;
                    const container = document.getElementById('optimizationHistory');
                    if (history.length === 0) {
                        container.innerHTML = '<p style="text-align: center; color: #7f8c8d;">暂无优化历史记录</p>';
                        return;
                    }
                    container.innerHTML = history.map(item => `
                        <div style="border: 1px solid #ecf0f1; border-radius: 6px; padding: 15px; margin-bottom: 15px;">
                            <h3>${item.task.name} (${item.task.type})</h3>
                            <p><strong>执行AI:</strong> ${item.ai.name} (${item.ai.role})</p>
                            <p><strong>状态:</strong> ${item.task.status}</p>
                            <p><strong>优先级:</strong> ${item.task.priority}</p>
                            <p><strong>执行时间:</strong> ${new Date(item.timestamp).toLocaleString()}</p>
                            ${item.task.result ? `<p><strong>结果:</strong> ${JSON.stringify(item.task.result)}</p>` : ''}
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('加载优化历史失败:', error);
            }
        }

        // 打开添加AI实例模态框
        function openAddAIModal() {
            document.getElementById('addAIModal').style.display = 'block';
        }

        // 关闭添加AI实例模态框
        function closeAddAIModal() {
            document.getElementById('addAIModal').style.display = 'none';
            // 重置表单
            document.getElementById('aiName').value = '';
            document.getElementById('aiRole').value = 'functional';
            document.getElementById('aiGroup').value = 'core';
        }

        // 添加AI实例
        async function addAIInstance() {
            const name = document.getElementById('aiName').value.trim();
            const role = document.getElementById('aiRole').value;
            const group = document.getElementById('aiGroup').value;
            
            if (!name) {
                alert('请输入AI名称');
                return;
            }
            
            try {
                const response = await fetch('/api/ai/add-instance', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name, role, group })
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('添加AI实例成功');
                    closeAddAIModal();
                    loadAIInstances();
                    loadSystemStats();
                } else {
                    alert('添加AI实例失败: ' + data.message);
                }
            } catch (error) {
                console.error('添加AI实例失败:', error);
                alert('添加AI实例失败: ' + error.message);
            }
        }

        // 移除AI实例
        async function removeAIInstance(aiId) {
            if (confirm('确定要移除这个AI实例吗？')) {
                try {
                    const response = await fetch(`/api/ai/remove-instance/${aiId}`, {
                        method: 'DELETE'
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        alert('移除AI实例成功');
                        loadAIInstances();
                        loadSystemStats();
                    } else {
                        alert('移除AI实例失败: ' + data.message);
                    }
                } catch (error) {
                    console.error('移除AI实例失败:', error);
                    alert('移除AI实例失败: ' + error.message);
                }
            }
        }

        // 生成任务
        async function generateTasks() {
            const functionalModules = document.getElementById('functionalModules').value.trim();
            const performanceMetrics = document.getElementById('performanceMetrics').value.trim();
            const managementProcesses = document.getElementById('managementProcesses').value.trim();
            const securityVulnerabilities = document.getElementById('securityVulnerabilities').value.trim();
            
            const project需求 = {};
            if (functionalModules) project需求.功能优化 = functionalModules.split(',');
            if (performanceMetrics) project需求.性能优化 = performanceMetrics.split(',');
            if (managementProcesses) project需求.管理优化 = managementProcesses.split(',');
            if (securityVulnerabilities) project需求.安全优化 = securityVulnerabilities.split(',');
            
            if (Object.keys(project需求).length === 0) {
                alert('请至少填写一项需求');
                return;
            }
            
            try {
                const response = await fetch('/api/ai/generate-tasks', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(project需求)
                });
                
                const data = await response.json();
                const resultDiv = document.getElementById('generateTasksResult');
                if (data.success) {
                    resultDiv.innerHTML = `
                        <div style="background: #d4edda; color: #155724; padding: 15px; border-radius: 6px;">
                            <h3>任务生成成功！</h3>
                            <p>共生成 ${data.data.length} 个任务，已添加到任务队列。</p>
                            <button class="btn btn-primary" onclick="loadTasks()">查看任务</button>
                        </div>
                    `;
                    // 清空表单
                    document.getElementById('functionalModules').value = '';
                    document.getElementById('performanceMetrics').value = '';
                    document.getElementById('managementProcesses').value = '';
                    document.getElementById('securityVulnerabilities').value = '';
                } else {
                    resultDiv.innerHTML = `
                        <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 6px;">
                            <h3>任务生成失败！</h3>
                            <p>${data.message}</p>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('生成任务失败:', error);
                alert('生成任务失败: ' + error.message);
            }
        }
    