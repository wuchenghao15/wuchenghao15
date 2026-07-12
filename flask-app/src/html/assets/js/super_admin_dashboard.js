var currentUserPage = 1;
var currentExamPage = 1;
var currentLogPage = 1;
var currentParamPage = 1;
var currentParamLogPage = 1;
var resourceChart = null;

function safeFetch(url, options) {
    return fetch(url, options).then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                try { return JSON.parse(text); } catch {
                    return { success: false, error: 'HTTP_ERROR', status: response.status, message: text || '请求失败' };
                }
            });
        }
        return response.text().then(text => {
            if (!text) return { success: false, error: 'EMPTY_RESPONSE', message: '响应为空' };
            try { return JSON.parse(text); } catch {
                return { success: false, error: 'INVALID_JSON', message: '无效的JSON响应', raw: text };
            }
        });
    }).catch(err => {
        console.error('Fetch error:', err);
        return { success: false, error: 'NETWORK_ERROR', message: '网络请求失败' };
    });
}

function switchTab(tabName) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    var navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(function(item) {
        if (item.getAttribute('onclick') && item.getAttribute('onclick').indexOf("switchTab('" + tabName + "')") !== -1) {
            item.classList.add('active');
        }
    });
    var tabEl = document.getElementById('tab-' + tabName);
    if (tabEl) tabEl.style.display = 'block';
    if (tabName === 'overview') loadOverview();
    if (tabName === 'users') loadUsers();
    if (tabName === 'exam') loadExams();
    if (tabName === 'routes') loadRoutes();
    if (tabName === 'engines') loadEngines();
    if (tabName === 'employees') loadEmployees();
    if (tabName === 'agent') loadAgentStatus();
    if (tabName === 'backup') loadBackups();
    if (tabName === 'settings') loadSettings();
    if (tabName === 'resources') loadResources();
    if (tabName === 'logs') loadLogs();
    if (tabName === 'params') loadParams();
    if (tabName === 'param-logs') loadParamLogs();
    if (tabName === 'param-backup') loadParamBackups();
}

function setResource(type, percent) {
    var pctEl = document.getElementById(type + '-percent');
    var barEl = document.getElementById(type + '-bar');
    if (pctEl) pctEl.textContent = percent.toFixed(1) + '%';
    if (barEl) barEl.style.width = percent + '%';
}

function loadOverview() {
    safeFetch('/api/super_admin/overview').then(function(data) {
        if (!data.success) return;
        var s = data.stats || {};
        var statUsers = document.getElementById('stat-users');
        if (statUsers) statUsers.textContent = s.total_users || '--';
        var statExams = document.getElementById('stat-exams');
        if (statExams) statExams.textContent = s.total_exams || '--';
        var statEmployees = document.getElementById('stat-employees');
        if (statEmployees) statEmployees.textContent = s.total_ai_employees || '--';
        var statRoutes = document.getElementById('stat-routes');
        if (statRoutes) statRoutes.textContent = s.total_routes || '--';
        var statAgent = document.getElementById('stat-agent');
        if (statAgent) statAgent.textContent = s.total_questions || '--';
        var activity = data.recent_activity || [];
        var tbody = document.getElementById('recent-activity');
        if (tbody && activity.length) {
            tbody.innerHTML = activity.map(function(a) {
                return '<tr><td>' + (a.created_at || '-') + '</td><td>' + (a.module || '-') + '</td><td>' + (a.message || '-') + '</td><td><span class="status-badge ' + (a.level || 'info') + '">' + (a.level || '-') + '</span></td></tr>';
            }).join('');
        }
    });
}

function loadResources() {
    safeFetch('/api/super_admin/resources').then(function(data) {
        if (!data.success) return;
        setResource('cpu', (data.cpu && data.cpu.percent) || 0);
        setResource('mem', (data.memory && data.memory.percent) || 0);
        setResource('disk', (data.disk && data.disk.percent) || 0);
        var cpuInfo = document.getElementById('cpu-info');
        var memInfo = document.getElementById('mem-info');
        if (cpuInfo && data.cpu) cpuInfo.innerHTML = '<div class="info-card-value">' + (data.cpu.cores || 0) + ' 核心</div><div class="info-card-title">CPU 核心数</div>';
        if (memInfo && data.memory) memInfo.innerHTML = '<div class="info-card-value">' + data.memory.used_gb + ' / ' + data.memory.total_gb + ' GB</div><div class="info-card-title">内存使用</div>';
    });
    initResourceChart();
}

function loadLogs() {
    var keyword = document.getElementById('log-search').value;
    var level = document.getElementById('log-level-filter').value;
    safeFetch('/api/super_admin/logs?page=' + currentLogPage + '&keyword=' + encodeURIComponent(keyword) + '&level=' + level).then(function(data) {
        var tbody = document.querySelector('#log-table tbody');
        if (!data.success) { tbody.innerHTML = '<tr><td colspan="4" class="empty-state">加载失败</td></tr>'; return; }
        tbody.innerHTML = data.logs.map(function(l) {
            return '<tr><td>' + (l.created_at || '-') + '</td><td><span class="status-badge ' + (l.level || 'info') + '">' + (l.level || '-') + '</span></td><td>' + (l.module || '-') + '</td><td>' + l.message + '</td></tr>';
        }).join('');
        renderPagination('log-pagination', data.total, data.page, data.per_page, function(p) { currentLogPage = p; loadLogs(); });
    });
}

function loadUsers() {
    var search = document.getElementById('user-search').value;
    var role = document.getElementById('user-role-filter').value;
    safeFetch('/api/super_admin/users?page=' + currentUserPage + '&keyword=' + encodeURIComponent(search) + '&role=' + role).then(function(data) {
        var tbody = document.querySelector('#user-table tbody');
        if (!data.success) { tbody.innerHTML = '<tr><td colspan="7" class="empty-state">加载失败</td></tr>'; return; }
        tbody.innerHTML = data.users.map(function(u) {
            return '<tr><td>' + u.id + '</td><td>' + u.username + '</td><td>' + (u.email || '-') + '</td><td>' + u.role + '</td><td><span class="status-badge ' + (u.is_active ? 'active' : 'pending') + '">' + (u.is_active ? '活跃' : '禁用') + '</span></td><td>' + (u.created_at ? u.created_at.slice(0,10) : '-') + '</td><td><button class="btn-secondary" style="width:auto;display:inline;padding:4px 10px;margin-right:4px;" onclick="editUser(' + u.id + ')">编辑</button><button class="btn-secondary" style="width:auto;display:inline;padding:4px 10px;margin-right:4px;" onclick="toggleUserStatus(' + u.id + ', ' + (u.is_active ? 0 : 1) + ')">' + (u.is_active ? '禁用' : '启用') + '</button><button class="btn-secondary" style="width:auto;display:inline;padding:4px 10px;" onclick="deleteUser(' + u.id + ')">删除</button></td></tr>';
        }).join('');
        renderPagination('user-pagination', data.total, data.page, data.per_page, function(p) { currentUserPage = p; loadUsers(); });
    });
}

function editUser(id) {
    var newRole = prompt('请输入用户角色（super_admin/admin/teacher/student）：');
    if (!newRole) return;
    safeFetch('/api/super_admin/users/' + id, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: newRole })
    }).then(function(data) {
        if (data.success) {
            alert('用户更新成功');
            loadUsers();
        } else {
            alert('更新失败: ' + (data.error || '未知错误'));
        }
    });
}

function toggleUserStatus(id, isActive) {
    if (!confirm('确定要' + (isActive ? '启用' : '禁用') + '该用户吗？')) return;
    safeFetch('/api/super_admin/users/' + id, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: isActive })
    }).then(function(data) {
        if (data.success) {
            loadUsers();
        } else {
            alert('操作失败: ' + (data.error || '未知错误'));
        }
    });
}

function deleteUser(id) {
    if (!confirm('确定删除用户？此操作不可恢复！')) return;
    safeFetch('/api/super_admin/users/' + id, { method: 'DELETE' }).then(function(data) {
        if (data.success) {
            alert('用户删除成功');
            loadUsers();
        } else {
            alert('删除失败: ' + (data.error || '未知错误'));
        }
    });
}

function loadExams() {
    var search = document.getElementById('exam-search').value;
    var status = document.getElementById('exam-status-filter').value;
    safeFetch('/api/super_admin/exams?page=' + currentExamPage + '&keyword=' + encodeURIComponent(search) + '&status=' + status).then(function(data) {
        var tbody = document.querySelector('#exam-table tbody');
        if (!data.success) { tbody.innerHTML = '<tr><td colspan="7" class="empty-state">加载失败</td></tr>'; return; }
        
        var stats = data.stats || {};
        var examTotal = document.getElementById('exam-total');
        var examActive = document.getElementById('exam-active');
        var examCompleted = document.getElementById('exam-completed');
        var examAvg = document.getElementById('exam-avg');
        if (examTotal) examTotal.textContent = stats.total || '--';
        if (examActive) examActive.textContent = stats.active || '--';
        if (examCompleted) examCompleted.textContent = stats.completed || '--';
        if (examAvg) examAvg.textContent = stats.avg_score || '--';
        
        tbody.innerHTML = data.exams.map(function(e) {
            return '<tr><td>' + e.id + '</td><td>' + e.title + '</td><td>' + (e.subject || '-') + '</td><td>' + (e.duration || '-') + '分钟</td><td>' + (e.question_count || '-') + '</td><td><span class="status-badge ' + (e.status === 'active' ? 'active' : 'completed') + '">' + (e.status === 'active' ? '进行中' : '已完成') + '</span></td><td>' + (e.created_at ? e.created_at.slice(0,10) : '-') + '</td></tr>';
        }).join('');
        renderPagination('exam-pagination', data.total, data.page, data.per_page, function(p) { currentExamPage = p; loadExams(); });
    });
}

function loadRoutes() {
    var search = document.getElementById('route-search').value;
    safeFetch('/api/super_admin/routes').then(function(data) {
        var tbody = document.querySelector('#route-table tbody');
        var routes = data.routes || [];
        if (search) routes = routes.filter(function(r) { return r.path.indexOf(search) !== -1; });
        tbody.innerHTML = routes.map(function(r) {
            return '<tr><td>' + r.path + '</td><td>' + r.endpoint + '</td><td>' + r.methods + '</td></tr>';
        }).join('');
        var routeCount = document.getElementById('route-count');
        if (routeCount) routeCount.textContent = data.total || 0;
    });
}

function loadEngines() {
    safeFetch('/api/super_admin/engines').then(function(data) {
        var grid = document.getElementById('engine-grid');
        grid.innerHTML = (data.engines || []).map(function(e) {
            return '<div class="engine-card"><div class="engine-header"><div class="engine-dot ' + (e.status === 'active' ? '' : 'inactive') + '"></div><div class="engine-name">' + (e.icon || '⚙️') + ' ' + e.name + '</div></div><div class="engine-desc">' + e.desc + '</div></div>';
        }).join('');
    });
}

function loadEmployees() {
    safeFetch('/api/super_admin/employees').then(function(data) {
        var tbody = document.querySelector('#employee-table tbody');
        if (!data.success) { tbody.innerHTML = '<tr><td colspan="6" class="empty-state">加载失败</td></tr>'; return; }
        tbody.innerHTML = data.employees.map(function(e) {
            return '<tr><td>' + e.id + '</td><td>' + e.name + '</td><td>' + (e.employee_code || '-') + '</td><td>' + (e.accuracy || '-') + '%</td><td>' + (e.total_tasks || 0) + '</td><td><span class="status-badge ' + (e.status === 'active' ? 'active' : 'pending') + '">' + (e.status === 'active' ? '活跃' : '离线') + '</span></td></tr>';
        }).join('');
    });
}

function loadAgentStatus() {
    safeFetch('/api/super_admin/agents').then(function(data) {
        var agents = data.agents || [];
        var running = agents.filter(function(a) { return a.status === 'running'; }).length;
        var stopped = agents.filter(function(a) { return a.status === 'stopped'; }).length;
        var agentTotal = document.getElementById('agent-total');
        var agentRunning = document.getElementById('agent-running');
        var agentStopped = document.getElementById('agent-stopped');
        if (agentTotal) agentTotal.textContent = agents.length;
        if (agentRunning) agentRunning.textContent = running;
        if (agentStopped) agentStopped.textContent = stopped;
        var tbody = document.querySelector('#agent-table tbody');
        if (tbody) {
            tbody.innerHTML = agents.map(function(a) {
                var statusClass = a.status === 'running' ? 'active' : (a.status === 'paused' ? 'warning' : 'pending');
                var statusText = a.status === 'running' ? '运行中' : (a.status === 'paused' ? '已暂停' : '已停止');
                var actions = '';
                if (a.status === 'stopped') {
                    actions = '<button class="btn-sm btn-success" onclick="agentAction(' + a.id + ', \'start\')">启动</button>';
                } else if (a.status === 'running') {
                    actions = '<button class="btn-sm btn-warning" onclick="agentAction(' + a.id + ', \'pause\')">暂停</button> ' +
                              '<button class="btn-sm btn-danger" onclick="agentAction(' + a.id + ', \'stop\')">终止</button>';
                } else if (a.status === 'paused') {
                    actions = '<button class="btn-sm btn-success" onclick="agentAction(' + a.id + ', \'start\')">恢复</button> ' +
                              '<button class="btn-sm btn-danger" onclick="agentAction(' + a.id + ', \'stop\')">终止</button>';
                }
                return '<tr><td>' + a.id + '</td><td>' + a.name + '</td><td>' + (a.role || '-') + '</td><td><span class="status-badge ' + statusClass + '">' + statusText + '</span></td><td>' + actions + '</td></tr>';
            }).join('');
        }
    }).catch(function() {
        var agentTotal = document.getElementById('agent-total');
        if (agentTotal) agentTotal.textContent = '0';
    });
}

function agentAction(agentId, action) {
    var actionText = action === 'start' ? '启动' : (action === 'pause' ? '暂停' : '终止');
    safeFetch('/api/super_admin/agents/' + agentId + '/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action })
    }).then(function(data) {
        if (data.success) {
            alert(data.message);
            loadAgentStatus();
        } else {
            alert('操作失败: ' + (data.error || '未知错误'));
        }
    }).catch(function() {
        alert('操作失败: 网络错误');
    });
}

function loadBackups() {
    safeFetch('/api/super_admin/backups').then(function(data) {
        var list = document.getElementById('backup-list');
        var backups = data.backups || [];
        if (!backups.length) {
            list.innerHTML = '<div class="empty-state">暂无备份</div>';
            return;
        }
        list.innerHTML = backups.map(function(b) {
            return '<div class="backup-item"><div class="backup-info"><p class="backup-name">' + b.name + '</p><p class="backup-meta">' + b.size + ' · ' + (b.created || '-') + '</p></div><div class="backup-actions"><button class="btn-icon primary" title="下载"><i class="fas fa-download"></i></button><button class="btn-icon danger" title="删除"><i class="fas fa-trash"></i></button></div></div>';
        }).join('');
    });
}

function loadSettings() {
    safeFetch('/api/super_admin/settings').then(function(data) {
        var content = document.getElementById('settings-content');
        var s = data.settings || {};
        var settingsHtml = '<div class="settings-grid">';
        settingsHtml += '<div class="settings-card"><h4>系统设置</h4>';
        var entries = Object.entries(s);
        for (var i = 0; i < Math.min(entries.length, 8); i++) {
            var k = entries[i][0];
            var v = entries[i][1];
            var displayValue = typeof v === 'object' ? v.value : v;
            var desc = typeof v === 'object' ? v.description : '';
            settingsHtml += '<div class="setting-item"><span class="setting-key">' + k + (desc ? ' - ' + desc : '') + '</span><span class="setting-value">' + displayValue + '</span></div>';
        }
        settingsHtml += '</div>';
        settingsHtml += '<div class="settings-card"><h4>快捷操作</h4>';
        settingsHtml += '<div style="display:flex;flex-direction:column;gap:10px;">';
        settingsHtml += '<button class="btn-secondary" onclick="alert(\'系统维护功能开发中\')">系统维护</button>';
        settingsHtml += '<button class="btn-secondary" onclick="alert(\'缓存清理功能开发中\')">清理缓存</button>';
        settingsHtml += '<button class="btn-secondary" onclick="alert(\'数据库优化功能开发中\')">优化数据库</button>';
        settingsHtml += '<button class="btn-secondary" onclick="alert(\'日志清理功能开发中\')">清理日志</button>';
        settingsHtml += '</div></div></div>';
        content.innerHTML = settingsHtml;
    });
}

function initResourceChart() {
    if (resourceChart) return;
    var canvas = document.getElementById('resourceChart');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    if (!ctx) return;
    resourceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['10分钟前', '8分钟前', '6分钟前', '4分钟前', '2分钟前', '现在'],
            datasets: [
                { label: 'CPU', data: [30, 45, 35, 50, 40, 35], borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', tension: 0.4, fill: true, borderWidth: 2, pointRadius: 0 },
                { label: '内存', data: [60, 65, 62, 68, 64, 66], borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', tension: 0.4, fill: true, borderWidth: 2, pointRadius: 0 },
                { label: '磁盘', data: [45, 45, 45, 46, 46, 46], borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', tension: 0.4, fill: true, borderWidth: 2, pointRadius: 0 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#94a3b8', font: { size: 12 }, padding: 20 }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { color: '#64748b', font: { size: 11 } },
                    grid: { color: 'rgba(59, 130, 246, 0.1)' }
                },
                x: {
                    ticks: { color: '#64748b', font: { size: 11 } },
                    grid: { color: 'rgba(59, 130, 246, 0.1)' }
                }
            }
        }
    });
}

function startLocalAgent() { alert('Agent启动功能开发中'); }
function startKnowledgeScan() { alert('知识扫描功能开发中'); }
function checkRoutes() { alert('健康检查功能开发中'); }

function createBackup() {
    safeFetch('/api/super_admin/backups', { method: 'POST' }).then(function(data) {
        if (data.success) {
            alert('备份创建成功');
            loadBackups();
        } else {
            alert('备份创建失败: ' + (data.error || '未知错误'));
        }
    });
}

function reloadRoutes() {
    alert('路由刷新功能开发中');
    loadRoutes();
}

function renderPagination(containerId, total, page, pageSize, callback) {
    var pages = Math.ceil(total / pageSize);
    var container = document.getElementById(containerId);
    if (!container) return;
    if (pages <= 1) { container.innerHTML = ''; return; }
    var html = '<button onclick="window.__pageCallback_' + containerId + '(' + (page - 1) + ')" ' + (page <= 1 ? 'disabled' : '') + '>上一页</button>';
    for (var i = 1; i <= pages; i++) {
        if (i === 1 || i === pages || (i >= page - 1 && i <= page + 1)) {
            html += '<button onclick="window.__pageCallback_' + containerId + '(' + i + ')" ' + (i === page ? 'class="active"' : '') + '>' + i + '</button>';
        } else if (i === 2 && page > 3) {
            html += '<span>...</span>';
        }
    }
    html += '<button onclick="window.__pageCallback_' + containerId + '(' + (page + 1) + ')" ' + (page >= pages ? 'disabled' : '') + '>下一页</button>';
    html += '<span style="margin-left:8px;">共 ' + total + ' 条</span>';
    container.innerHTML = html;
    window['__pageCallback_' + containerId] = callback;
}

var paramCategories = [];
var paramScopes = [];

function loadParams() {
    var search = document.getElementById('param-search').value;
    var category = document.getElementById('param-category-filter').value;
    var scope = document.getElementById('param-scope-filter').value;
    
    safeFetch('/api/system_params/list?page=' + currentParamPage + '&keyword=' + encodeURIComponent(search) + 
              '&category=' + category + '&scope=' + scope).then(function(data) {
        if (data.code !== 200) {
            document.querySelector('#param-table tbody').innerHTML = '<tr><td colspan="7" class="empty-state">加载失败</td></tr>';
            return;
        }
        
        var params = data.data ? data.data.params : [];
        var tbody = document.querySelector('#param-table tbody');
        
        tbody.innerHTML = params.map(function(p) {
            var valueDisplay = typeof p.value === 'object' ? JSON.stringify(p.value) : String(p.value);
            if (valueDisplay.length > 50) valueDisplay = valueDisplay.substring(0, 50) + '...';
            
            return '<tr><td>' + p.setting_key + '</td><td>' + valueDisplay + '</td><td>' + 
                   (p.category || '-') + '</td><td>' + (p.data_type || '-') + '</td><td>' + 
                   (p.scope || '-') + '</td><td>' + (p.description || '-') + '</td><td>' +
                   '<button class="btn-sm btn-secondary" onclick="editParam(\'' + p.setting_key + '\')">编辑</button> ' +
                   '<button class="btn-sm btn-danger" onclick="deleteParam(\'' + p.setting_key + '\')">删除</button></td></tr>';
        }).join('');
        
        var total = data.data ? data.data.total : 0;
        var perPage = data.data ? data.data.per_page : 20;
        renderPagination('param-pagination', total, currentParamPage, perPage, function(p) { 
            currentParamPage = p; 
            loadParams(); 
        });
        
        loadParamFilters();
    });
}

function loadParamFilters() {
    if (paramCategories.length === 0) {
        safeFetch('/api/system_params/categories').then(function(data) {
            if (data.code === 200 && data.data) {
                paramCategories = data.data.categories || [];
                var categorySelect = document.getElementById('param-category-filter');
                categorySelect.innerHTML = '<option value="">全部分类</option>' + 
                    paramCategories.map(function(c) { 
                        return '<option value="' + c + '">' + c + '</option>'; 
                    }).join('');
            }
        });
    }
    
    if (paramScopes.length === 0) {
        safeFetch('/api/system_params/scopes').then(function(data) {
            if (data.code === 200 && data.data) {
                paramScopes = data.data.scopes || [];
                var scopeSelect = document.getElementById('param-scope-filter');
                scopeSelect.innerHTML = '<option value="">全部作用域</option>' + 
                    paramScopes.map(function(s) { 
                        return '<option value="' + s.value + '">' + s.name + '</option>'; 
                    }).join('');
            }
        });
    }
}

function showAddParamModal() {
    var key = prompt('请输入参数键（格式：category.name）：');
    if (!key) return;
    
    var value = prompt('请输入参数值：');
    if (value === null) return;
    
    var category = key.split('.')[0] || 'general';
    var description = prompt('请输入参数描述：', '');
    var dataType = prompt('请输入数据类型（string/integer/float/boolean/json/list/datetime）：', 'string');
    
    safeFetch('/api/system_params/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            key: key,
            value: value,
            category: category,
            description: description || '',
            data_type: dataType || 'string',
            scope: 'global'
        })
    }).then(function(data) {
        if (data.code === 200 || data.code === 201) {
            alert('参数创建成功');
            loadParams();
        } else {
            alert('创建失败: ' + (data.message || '未知错误'));
        }
    });
}

function editParam(key) {
    safeFetch('/api/system_params/get?key=' + encodeURIComponent(key)).then(function(data) {
        if (data.code !== 200) {
            alert('获取参数失败');
            return;
        }
        
        var param = data.data;
        var currentValue = typeof param.value === 'object' ? JSON.stringify(param.value) : String(param.value);
        var newValue = prompt('请输入新的参数值：', currentValue);
        
        if (newValue === null) return;
        
        var parsedValue = newValue;
        try {
            parsedValue = JSON.parse(newValue);
        } catch(e) {}
        
        safeFetch('/api/system_params/set', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                key: key,
                value: parsedValue
            })
        }).then(function(data) {
            if (data.code === 200) {
                alert('参数更新成功');
                loadParams();
            } else {
                alert('更新失败: ' + (data.message || '未知错误'));
            }
        });
    });
}

function deleteParam(key) {
    if (!confirm('确定删除参数 "' + key + '"？此操作不可恢复！')) return;
    
    safeFetch('/api/system_params/delete', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: key })
    }).then(function(data) {
        if (data.code === 200) {
            alert('参数删除成功');
            loadParams();
        } else {
            alert('删除失败: ' + (data.message || '未知错误'));
        }
    });
}

function resetParamModal() {
    var key = prompt('请输入要重置的参数键：');
    if (!key) return;
    
    safeFetch('/api/system_params/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: key })
    }).then(function(data) {
        if (data.code === 200) {
            alert('参数已重置为默认值');
            loadParams();
        } else {
            alert('重置失败: ' + (data.message || '未知错误'));
        }
    });
}

function loadParamLogs() {
    var search = document.getElementById('param-log-search').value;
    var operation = document.getElementById('param-log-operation').value;
    
    safeFetch('/api/system_params/logs?page=' + currentParamLogPage + '&setting_key=' + encodeURIComponent(search) + '&operation=' + operation).then(function(data) {
        if (data.code !== 200) {
            document.querySelector('#param-log-table tbody').innerHTML = '<tr><td colspan="8" class="empty-state">加载失败</td></tr>';
            return;
        }
        
        var logs = data.data ? data.data.logs : [];
        var tbody = document.querySelector('#param-log-table tbody');
        
        tbody.innerHTML = logs.map(function(log) {
            var oldValue = log.old_value !== null ? (typeof log.old_value === 'object' ? JSON.stringify(log.old_value) : String(log.old_value)) : '-';
            var newValue = log.new_value !== null ? (typeof log.new_value === 'object' ? JSON.stringify(log.new_value) : String(log.new_value)) : '-';
            if (oldValue.length > 30) oldValue = oldValue.substring(0, 30) + '...';
            if (newValue.length > 30) newValue = newValue.substring(0, 30) + '...';
            
            var opClass = { 'create': 'badge-success', 'update': 'badge-primary', 'delete': 'badge-danger', 'reset': 'badge-warning' }[log.operation] || 'badge-gray';
            var opText = { 'create': '创建', 'update': '修改', 'delete': '删除', 'reset': '重置' }[log.operation] || log.operation;
            
            return '<tr><td>' + (log.timestamp || '-') + '</td><td><span class="badge ' + opClass + '">' + opText + '</span></td><td>' + (log.setting_key || '-') + '</td><td>' + oldValue + '</td><td>' + newValue + '</td><td>' + (log.operator || '-') + '</td><td>' + (log.operator_role || '-') + '</td><td>' + (log.ip_address || '-') + '</td></tr>';
        }).join('');
        
        var total = data.data ? data.data.total : 0;
        var perPage = data.data ? data.data.per_page : 20;
        renderPagination('param-log-pagination', total, currentParamLogPage, perPage, function(p) { 
            currentParamLogPage = p; 
            loadParamLogs(); 
        });
    });
}

function loadParamBackups() {
    safeFetch('/api/system_params/backups').then(function(data) {
        var container = document.getElementById('param-backup-list');
        
        if (data.code !== 200 || !data.data || data.data.length === 0) {
            container.innerHTML = '<div class="empty-state">暂无备份记录</div>';
            return;
        }
        
        var backups = data.data;
        container.innerHTML = backups.map(function(b) {
            return '<div class="backup-item"><div class="backup-info"><p><strong>备份ID:</strong> ' + b.backup_id + '</p><p><strong>备份时间:</strong> ' + b.backup_time + '</p><p><strong>参数数量:</strong> ' + b.param_count + '</p></div><div class="backup-actions"><button class="btn-sm btn-primary" onclick="restoreParamBackup(\'' + b.backup_id + '\')">恢复</button><button class="btn-sm btn-danger" onclick="deleteParamBackup(\'' + b.backup_id + '\')">删除</button></div></div>';
        }).join('');
    }).catch(function() {
        document.getElementById('param-backup-list').innerHTML = '<div class="empty-state">加载失败</div>';
    });
}

function createParamBackup() {
    safeFetch('/api/system_params/backup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    }).then(function(data) {
        if (data.code === 200) {
            alert('参数备份成功，备份ID: ' + data.data.backup_id);
            loadParamBackups();
        } else {
            alert('备份失败: ' + (data.message || '未知错误'));
        }
    });
}

function restoreParamBackup(backupId) {
    if (!confirm('确定恢复此备份？此操作将覆盖当前参数设置！')) return;
    
    safeFetch('/api/system_params/restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backup_id: backupId })
    }).then(function(data) {
        if (data.code === 200) {
            alert('参数恢复成功，已恢复 ' + data.data.restored_count + ' 个参数');
            loadParamBackups();
            loadParams();
        } else {
            alert('恢复失败: ' + (data.message || '未知错误'));
        }
    });
}

function deleteParamBackup(backupId) {
    if (!confirm('确定删除此备份？')) return;
    
    safeFetch('/api/system_params/delete_backup', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backup_id: backupId })
    }).then(function(data) {
        if (data.code === 200) {
            alert('备份删除成功');
            loadParamBackups();
        } else {
            alert('删除失败: ' + (data.message || '未知错误'));
        }
    });
}

function logout() { window.location.href = '/logout'; }

document.addEventListener('DOMContentLoaded', function() {
    loadOverview();
    setInterval(loadResources, 5000);
});
