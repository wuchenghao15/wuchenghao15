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
                try { 
                    var result = JSON.parse(text);
                    result.success = result.code === 200;
                    return result; 
                } catch {
                    return { success: false, error: 'HTTP_ERROR', status: response.status, message: text || '请求失败', code: 500 };
                }
            });
        }
        return response.text().then(text => {
            if (!text) return { success: false, error: 'EMPTY_RESPONSE', message: '响应为空', code: 500 };
            try { 
                var result = JSON.parse(text);
                result.success = result.code === 200 || result.success === true;
                return result; 
            } catch {
                return { success: false, error: 'INVALID_JSON', message: '无效的JSON响应', raw: text, code: 500 };
            }
        });
    }).catch(err => {
        console.error('Fetch error:', err);
        return { success: false, error: 'NETWORK_ERROR', message: '网络请求失败', code: 500 };
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
    if (tabName === 'security') { loadSecurityStats(); loadSecurityAuditLogs(); }
    if (tabName === 'ai-analytics') { loadLearningAnalytics(); loadExamAnalytics(); loadBehaviorAnalytics(); }
    if (tabName === 'notifications') loadNotifications();
        if (tabName === 'announcements') loadAnnouncements();
        if (tabName === 'health') { runHealthCheck(); loadHealthHistory(); }
        if (tabName === 'tasks') { loadTasks(); loadTaskLogs(); }
        if (tabName === 'sessions') loadSessions();
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
        var d = data.data || {};
        var s = d.stats || {};
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
        var activity = d.recent_activity || [];
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
        var d = data.data || {};
        setResource('cpu', (d.cpu && d.cpu.percent) || 0);
        setResource('mem', (d.memory && d.memory.percent) || 0);
        setResource('disk', (d.disk && d.disk.percent) || 0);
        var cpuInfo = document.getElementById('cpu-info');
        var memInfo = document.getElementById('mem-info');
        if (cpuInfo && d.cpu) cpuInfo.innerHTML = '<div class="info-card-value">' + (d.cpu.cores || 0) + ' 核心</div><div class="info-card-title">CPU 核心数</div>';
        if (memInfo && d.memory) memInfo.innerHTML = '<div class="info-card-value">' + d.memory.used_gb + ' / ' + d.memory.total_gb + ' GB</div><div class="info-card-title">内存使用</div>';
    });
    initResourceChart();
}

function loadLogs() {
    var keyword = document.getElementById('log-search').value;
    var level = document.getElementById('log-level-filter').value;
    safeFetch('/api/super_admin/logs?page=' + currentLogPage + '&keyword=' + encodeURIComponent(keyword) + '&level=' + level).then(function(data) {
        var tbody = document.querySelector('#log-table tbody');
        if (!data.success) { tbody.innerHTML = '<tr><td colspan="4" class="empty-state">加载失败</td></tr>'; return; }
        var d = data.data || {};
        tbody.innerHTML = (d.logs || []).map(function(l) {
            return '<tr><td>' + (l.created_at || '-') + '</td><td><span class="status-badge ' + (l.level || 'info') + '">' + (l.level || '-') + '</span></td><td>' + (l.module || '-') + '</td><td>' + l.message + '</td></tr>';
        }).join('');
        renderPagination('log-pagination', d.total || 0, d.page || 1, d.per_page || 20, function(p) { currentLogPage = p; loadLogs(); });
    });
}

function loadUsers() {
    var search = document.getElementById('user-search').value;
    var role = document.getElementById('user-role-filter').value;
    safeFetch('/api/super_admin/users?page=' + currentUserPage + '&keyword=' + encodeURIComponent(search) + '&role=' + role).then(function(data) {
        var tbody = document.querySelector('#user-table tbody');
        if (!data.success) { tbody.innerHTML = '<tr><td colspan="7" class="empty-state">加载失败</td></tr>'; return; }
        var d = data.data || {};
        tbody.innerHTML = (d.users || []).map(function(u) {
            return '<tr><td>' + u.id + '</td><td>' + u.username + '</td><td>' + (u.email || '-') + '</td><td>' + u.role + '</td><td><span class="status-badge ' + (u.is_active ? 'active' : 'pending') + '">' + (u.is_active ? '活跃' : '禁用') + '</span></td><td>' + (u.created_at ? u.created_at.slice(0,10) : '-') + '</td><td><button class="btn-secondary" style="width:auto;display:inline;padding:4px 10px;margin-right:4px;" onclick="editUser(' + u.id + ')">编辑</button><button class="btn-secondary" style="width:auto;display:inline;padding:4px 10px;margin-right:4px;" onclick="toggleUserStatus(' + u.id + ', ' + (u.is_active ? 0 : 1) + ')">' + (u.is_active ? '禁用' : '启用') + '</button><button class="btn-secondary" style="width:auto;display:inline;padding:4px 10px;" onclick="deleteUser(' + u.id + ')">删除</button></td></tr>';
        }).join('');
        renderPagination('user-pagination', d.total || 0, d.page || 1, d.per_page || 20, function(p) { currentUserPage = p; loadUsers(); });
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
        var d = data.data || {};
        
        var stats = d.stats || {};
        var examTotal = document.getElementById('exam-total');
        var examActive = document.getElementById('exam-active');
        var examCompleted = document.getElementById('exam-completed');
        var examAvg = document.getElementById('exam-avg');
        if (examTotal) examTotal.textContent = stats.total || '--';
        if (examActive) examActive.textContent = stats.active || '--';
        if (examCompleted) examCompleted.textContent = stats.completed || '--';
        if (examAvg) examAvg.textContent = stats.avg_score || '--';
        
        tbody.innerHTML = (d.exams || []).map(function(e) {
            return '<tr><td>' + e.id + '</td><td>' + e.title + '</td><td>' + (e.subject || '-') + '</td><td>' + (e.duration || '-') + '分钟</td><td>' + (e.question_count || '-') + '</td><td><span class="status-badge ' + (e.status === 'active' ? 'active' : 'completed') + '">' + (e.status === 'active' ? '进行中' : '已完成') + '</span></td><td>' + (e.created_at ? e.created_at.slice(0,10) : '-') + '</td></tr>';
        }).join('');
        renderPagination('exam-pagination', d.total || 0, d.page || 1, d.per_page || 20, function(p) { currentExamPage = p; loadExams(); });
    });
}

function loadRoutes() {
    var search = document.getElementById('route-search').value;
    safeFetch('/api/super_admin/routes').then(function(data) {
        var tbody = document.querySelector('#route-table tbody');
        var d = data.data || {};
        var routes = d.routes || [];
        if (search) routes = routes.filter(function(r) { return r.path.indexOf(search) !== -1; });
        tbody.innerHTML = routes.map(function(r) {
            return '<tr><td>' + r.path + '</td><td>' + r.endpoint + '</td><td>' + r.methods + '</td></tr>';
        }).join('');
        var routeCount = document.getElementById('route-count');
        if (routeCount) routeCount.textContent = d.total || 0;
    });
}

function loadEngines() {
    safeFetch('/api/super_admin/engines').then(function(data) {
        var grid = document.getElementById('engine-grid');
        var d = data.data || {};
        grid.innerHTML = (d.engines || []).map(function(e) {
            return '<div class="engine-card"><div class="engine-header"><div class="engine-dot ' + (e.status === 'active' ? '' : 'inactive') + '"></div><div class="engine-name">' + (e.icon || '⚙️') + ' ' + e.name + '</div></div><div class="engine-desc">' + e.desc + '</div></div>';
        }).join('');
    });
}

function loadEmployees() {
    safeFetch('/api/super_admin/employees').then(function(data) {
        var tbody = document.querySelector('#employee-table tbody');
        if (!data.success) { tbody.innerHTML = '<tr><td colspan="6" class="empty-state">加载失败</td></tr>'; return; }
        var d = data.data || {};
        tbody.innerHTML = (d.employees || []).map(function(e) {
            return '<tr><td>' + e.id + '</td><td>' + e.name + '</td><td>' + (e.employee_code || '-') + '</td><td>' + (e.accuracy || '-') + '%</td><td>' + (e.total_tasks || 0) + '</td><td><span class="status-badge ' + (e.status === 'active' ? 'active' : 'pending') + '">' + (e.status === 'active' ? '活跃' : '离线') + '</span></td></tr>';
        }).join('');
    });
}

function loadAgentStatus() {
    safeFetch('/api/super_admin/agents').then(function(data) {
        var d = data.data || {};
        var agents = d.agents || [];
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
        var d = data.data || [];
        if (!data.success || !d.length) {
            list.innerHTML = '<div class="empty-state">暂无备份</div>';
            return;
        }
        list.innerHTML = d.map(function(b) {
            var size = (b.backup_size || 0) > 1024 * 1024 ? (b.backup_size / (1024 * 1024)).toFixed(2) + ' MB' : 
                       (b.backup_size || 0) > 1024 ? (b.backup_size / 1024).toFixed(2) + ' KB' : (b.backup_size || 0) + ' B';
            return '<div class="backup-item"><div class="backup-info"><p class="backup-name">备份 ' + (b.backup_id || '-') + '</p><p class="backup-meta">' + size + ' · ' + (b.backup_time || '-') + '</p></div><div class="backup-actions"><button class="btn-icon primary" onclick="restoreBackup(\'' + b.backup_id + '\')" title="恢复"><i class="fas fa-download"></i></button><button class="btn-icon danger" onclick="deleteBackup(\'' + b.backup_id + '\')" title="删除"><i class="fas fa-trash"></i></button></div></div>';
        }).join('');
    });
}

function loadSettings() {
    safeFetch('/api/super_admin/settings').then(function(data) {
        var content = document.getElementById('settings-content');
        var d = data.data || {};
        var s = d.settings || {};
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

function startLocalAgent() {
    safeFetch('/api/super_admin/agents').then(function(data) {
        var agents = data.data ? data.data.agents : [];
        var stoppedAgent = agents.find(function(a) { return a.status === 'stopped'; });
        if (stoppedAgent) {
            agentAction(stoppedAgent.id, 'start');
        } else {
            alert('没有可启动的Agent');
        }
    });
}
function startKnowledgeScan() { alert('知识扫描功能开发中'); }
function checkRoutes() {
    safeFetch('/api/super_admin/health').then(function(data) {
        if (data.success) {
            alert('健康检查完成: ' + data.message);
        } else {
            alert('健康检查失败');
        }
    });
}

function createBackup() {
    safeFetch('/api/super_admin/backup', { method: 'POST' }).then(function(data) {
        if (data.success) {
            alert('备份创建成功');
            loadBackups();
        } else {
            alert('备份创建失败: ' + (data.error || '未知错误'));
        }
    });
}

function restoreBackup(backupId) {
    if (!confirm('确定恢复此备份？此操作将覆盖当前数据！')) return;
    safeFetch('/api/super_admin/backup/' + backupId + '/restore', { method: 'POST' }).then(function(data) {
        if (data.success) {
            alert('备份恢复成功');
            loadBackups();
        } else {
            alert('恢复失败: ' + (data.error || '未知错误'));
        }
    });
}

function deleteBackup(backupId) {
    if (!confirm('确定删除此备份？')) return;
    safeFetch('/api/super_admin/backup/' + backupId + '/delete', { method: 'DELETE' }).then(function(data) {
        if (data.success) {
            alert('备份删除成功');
            loadBackups();
        } else {
            alert('删除失败: ' + (data.error || '未知错误'));
        }
    });
}

function reloadRoutes() {
    safeFetch('/api/super_admin/reload_routes', { method: 'POST' }).then(function(data) {
        if (data.success) {
            alert('路由刷新成功');
            loadRoutes();
        } else {
            alert('路由刷新失败');
        }
    });
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

function loadSecurityStats() {
    safeFetch('/api/super_admin/security/intrusion_stats').then(function(data) {
        if (!data.success) return;
        var d = data.data || {};
        document.getElementById('security-sql-injection').textContent = d.sql_injection_count || 0;
        document.getElementById('security-access-denied').textContent = d.access_denied_count || 0;
        document.getElementById('security-failed-login').textContent = d.failed_login_today || 0;
        document.getElementById('security-suspicious-ips').textContent = (d.suspicious_ips || []).length;
    });
}

function loadSecurityAuditLogs() {
    safeFetch('/api/super_admin/security/audit_logs').then(function(data) {
        if (!data.success) return;
        var d = data.data || {};
        var logs = d.logs || [];
        var tbody = document.querySelector('#security-audit-table tbody');
        tbody.innerHTML = logs.length ? logs.map(function(log) {
            return '<tr><td>' + (log.timestamp || '-') + '</td><td>' + (log.operation || '-') + '</td><td>' + (log.target || '-') + '</td><td>' + (log.operator || '-') + '</td><td>' + (log.ip_address || '-') + '</td><td>' + (log.status || '-') + '</td></tr>';
        }).join('') : '<tr><td colspan="6" class="empty-state">暂无审计日志</td></tr>';
    });
}

function loadLearningAnalytics() {
    safeFetch('/api/super_admin/ai_analytics/learning').then(function(data) {
        if (!data.success) return;
        var d = data.data || {};
        var container = document.getElementById('learning-analytics');
        container.innerHTML = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;"><div><h4>学习趋势（最近7天）</h4><ul>' + (d.learning_trend || []).map(function(t) {
            return '<li>' + t.date + ': ' + t.count + '次学习</li>';
        }).join('') + '</ul></div><div><h4>活跃学习者TOP10</h4><ul>' + (d.active_learners || []).map(function(l) {
            return '<li>' + l.username + ': ' + l.learning_count + '次学习</li>';
        }).join('') + '</ul></div></div><div style="margin-top:16px;"><strong>总学习记录:</strong> ' + (d.total_learning_records || 0) + '</div>';
    });
}

function loadExamAnalytics() {
    safeFetch('/api/super_admin/ai_analytics/exam').then(function(data) {
        if (!data.success) return;
        var d = data.data || {};
        var container = document.getElementById('exam-analytics');
        container.innerHTML = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;"><div><h4>考试趋势（最近7天）</h4><ul>' + (d.exam_trend || []).map(function(t) {
            return '<li>' + t.date + ': ' + t.count + '场考试</li>';
        }).join('') + '</ul></div><div><h4>科目统计TOP5</h4><ul>' + (d.subject_stats || []).map(function(s) {
            return '<li>' + s.subject + ': ' + s.exam_count + '场考试，平均分 ' + s.avg_score + '</li>';
        }).join('') + '</ul></div></div><div style="margin-top:16px;"><strong>平均分:</strong> ' + d.avg_score + ' | <strong>通过率:</strong> ' + d.pass_rate + '% | <strong>总考试记录:</strong> ' + d.total_results + '</div>';
    });
}

function loadBehaviorAnalytics() {
    safeFetch('/api/super_admin/ai_analytics/user_behavior').then(function(data) {
        if (!data.success) return;
        var d = data.data || {};
        var container = document.getElementById('behavior-analytics');
        container.innerHTML = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;"><div><h4>活跃用户趋势（最近7天）</h4><ul>' + (d.active_user_trend || []).map(function(t) {
            return '<li>' + t.date + ': ' + t.count + '位活跃用户</li>';
        }).join('') + '</ul></div><div><h4>角色分布</h4><ul>' + (d.role_distribution || []).map(function(r) {
            return '<li>' + r.role + ': ' + r.count + '人</li>';
        }).join('') + '</ul></div></div><div style="margin-top:16px;"><h4>热门页面TOP10</h4><ul>' + (d.top_pages || []).map(function(p) {
            return '<li>' + p.path + ': ' + p.count + '次访问</li>';
        }).join('') + '</ul></div>';
    });
}

var currentNotificationPage = 1;
function loadNotifications() {
    safeFetch('/api/super_admin/notifications?page=' + currentNotificationPage).then(function(data) {
        if (!data.success) return;
        var d = data.data || {};
        var notifications = d.notifications || [];
        var tbody = document.querySelector('#notification-table tbody');
        tbody.innerHTML = notifications.length ? notifications.map(function(n) {
            var typeClass = { 'info': 'badge-gray', 'success': 'badge-success', 'warning': 'badge-warning', 'error': 'badge-danger' }[n.type] || 'badge-gray';
            var typeText = { 'info': '信息', 'success': '成功', 'warning': '警告', 'error': '错误' }[n.type] || n.type;
            var statusClass = n.status === 'read' ? 'badge-gray' : 'badge-primary';
            return '<tr><td>' + n.id + '</td><td>' + (n.title || '-') + '</td><td><span class="badge ' + typeClass + '">' + typeText + '</span></td><td><span class="badge ' + statusClass + '">' + (n.status === 'read' ? '已读' : '未读') + '</span></td><td>' + (n.created_at || '-') + '</td><td><button class="btn-sm btn-primary" onclick="deleteNotification(' + n.id + ')">删除</button></td></tr>';
        }).join('') : '<tr><td colspan="6" class="empty-state">暂无通知</td></tr>';
    });
}

function showAddNotificationModal() {
    var title = prompt('请输入通知标题：');
    if (!title) return;
    var content = prompt('请输入通知内容：');
    if (!content) return;
    var type = prompt('请输入通知类型（info/success/warning/error）：', 'info');
    safeFetch('/api/super_admin/notifications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title, content: content, type: type })
    }).then(function(data) {
        if (data.success) {
            alert('通知创建成功');
            loadNotifications();
        } else {
            alert('创建失败: ' + (data.message || '未知错误'));
        }
    });
}

function deleteNotification(id) {
    if (!confirm('确定删除此通知？')) return;
    safeFetch('/api/super_admin/notifications/' + id, { method: 'DELETE' }).then(function(data) {
        if (data.success) {
            alert('通知删除成功');
            loadNotifications();
        } else {
            alert('删除失败: ' + (data.message || '未知错误'));
        }
    });
}

var currentAnnouncementPage = 1;
function loadAnnouncements() {
    safeFetch('/api/super_admin/announcements?page=' + currentAnnouncementPage).then(function(data) {
        if (!data.success) return;
        var d = data.data || {};
        var announcements = d.announcements || [];
        var tbody = document.querySelector('#announcement-table tbody');
        tbody.innerHTML = announcements.length ? announcements.map(function(a) {
            var statusClass = a.is_published ? 'badge-success' : 'badge-gray';
            return '<tr><td>' + a.id + '</td><td>' + (a.title || '-') + '</td><td><span class="badge ' + statusClass + '">' + (a.is_published ? '已发布' : '草稿') + '</span></td><td>' + (a.publish_time || '-') + '</td><td>' + (a.created_at || '-') + '</td><td><button class="btn-sm btn-primary" onclick="deleteAnnouncement(' + a.id + ')">删除</button></td></tr>';
        }).join('') : '<tr><td colspan="6" class="empty-state">暂无公告</td></tr>';
    });
}

function showAddAnnouncementModal() {
    var title = prompt('请输入公告标题：');
    if (!title) return;
    var content = prompt('请输入公告内容：');
    if (!content) return;
    var isPublished = confirm('是否立即发布？');
    safeFetch('/api/super_admin/announcements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title, content: content, is_published: isPublished })
    }).then(function(data) {
        if (data.success) {
            alert('公告创建成功');
            loadAnnouncements();
        } else {
            alert('创建失败: ' + (data.message || '未知错误'));
        }
    });
}

function deleteAnnouncement(id) {
    if (!confirm('确定删除此公告？')) return;
    safeFetch('/api/super_admin/announcements/' + id, { method: 'DELETE' }).then(function(data) {
        if (data.success) {
            alert('公告删除成功');
            loadAnnouncements();
        } else {
            alert('删除失败: ' + (data.message || '未知错误'));
        }
    });
}

function exportUsers() {
    window.open('/api/super_admin/export/users', '_blank');
}

function exportExams() {
    window.open('/api/super_admin/export/exams', '_blank');
}

function exportLogs() {
    window.open('/api/super_admin/export/logs', '_blank');
}

function runHealthCheck() {
    safeFetch('/api/super_admin/health/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    }).then(function(data) {
        if (!data.success) {
            document.getElementById('health-status-summary').innerHTML = '<div style="color:var(--color-danger);">健康检查失败</div>';
            return;
        }
        var d = data.data || {};
        var summaryEl = document.getElementById('health-status-summary');
        var statusClass = d.overall_status === 'healthy' ? 'badge-success' : 'badge-danger';
        var statusText = d.overall_status === 'healthy' ? '健康' : '异常';
        summaryEl.innerHTML = '<div><span class="badge ' + statusClass + '">' + statusText + '</span> <strong>整体状态</strong>: ' + d.healthy_count + '/' + d.total_modules + ' 模块健康</div>';
        
        var tbody = document.querySelector('#health-check-results tbody');
        tbody.innerHTML = (d.check_results || []).map(function(r) {
            var statusClass = r.status === 'healthy' ? 'badge-success' : 'badge-danger';
            var statusText = r.status === 'healthy' ? '健康' : '异常';
            return '<tr><td>' + r.module_name + '</td><td><span class="badge ' + statusClass + '">' + statusText + '</span></td><td>' + r.response_time + '</td><td>' + (r.error_message || '-') + '</td><td>' + (r.checked_at || '-') + '</td></tr>';
        }).join('');
    });
}

function loadHealthHistory() {
    safeFetch('/api/super_admin/health/history').then(function(data) {
        if (!data.success) return;
        var d = data.data || {};
        var tbody = document.querySelector('#health-history-table tbody');
        tbody.innerHTML = (d.history || []).slice(0, 20).map(function(h) {
            var statusClass = h.status === 'healthy' ? 'badge-success' : 'badge-danger';
            var statusText = h.status === 'healthy' ? '健康' : '异常';
            return '<tr><td>' + h.module_name + '</td><td><span class="badge ' + statusClass + '">' + statusText + '</span></td><td>' + h.response_time + '</td><td>' + (h.checked_at || '-') + '</td></tr>';
        }).join('');
    });
}

function loadTasks() {
    safeFetch('/api/super_admin/tasks').then(function(data) {
        if (!data.success) return;
        var d = data.data || {};
        var tbody = document.querySelector('#task-table tbody');
        tbody.innerHTML = (d.tasks || []).map(function(t) {
            var statusClass = t.status === 'enabled' ? 'badge-success' : 'badge-warning';
            var statusText = t.status === 'enabled' ? '启用' : '禁用';
            var actions = '';
            if (t.status === 'enabled') {
                actions = '<button class="btn-sm btn-primary" onclick="runTask(' + t.id + ')">执行</button> ' +
                          '<button class="btn-sm btn-warning" onclick="toggleTaskStatus(' + t.id + ', \'disabled\')">禁用</button> ' +
                          '<button class="btn-sm btn-danger" onclick="deleteTask(' + t.id + ')">删除</button>';
            } else {
                actions = '<button class="btn-sm btn-success" onclick="toggleTaskStatus(' + t.id + ', \'enabled\')">启用</button> ' +
                          '<button class="btn-sm btn-danger" onclick="deleteTask(' + t.id + ')">删除</button>';
            }
            return '<tr><td>' + t.id + '</td><td>' + t.task_name + '</td><td>' + (t.task_type || '-') + '</td><td>' + (t.cron_expression || '-') + '</td><td><span class="badge ' + statusClass + '">' + statusText + '</span></td><td>' + (t.last_run_at || '-') + '</td><td>' + actions + '</td></tr>';
        }).join('');
    });
}

function showAddTaskModal() {
    var taskName = prompt('请输入任务名称：');
    if (!taskName) return;
    var taskType = prompt('请输入任务类型（periodic/cron）：', 'periodic');
    var cronExpr = prompt('请输入Cron表达式（留空则使用间隔）：');
    var interval = prompt('请输入间隔秒数（0表示不使用）：', '3600');
    
    safeFetch('/api/super_admin/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            task_name: taskName,
            task_type: taskType,
            cron_expression: cronExpr,
            interval_seconds: parseInt(interval) || 0
        })
    }).then(function(data) {
        if (data.success) {
            alert('任务创建成功');
            loadTasks();
        } else {
            alert('创建失败: ' + (data.message || '未知错误'));
        }
    });
}

function runTask(taskId) {
    if (!confirm('确定执行此任务？')) return;
    safeFetch('/api/super_admin/tasks/' + taskId + '/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    }).then(function(data) {
        if (data.success) {
            alert('任务执行完成');
            loadTasks();
            loadTaskLogs();
        } else {
            alert('执行失败: ' + (data.message || '未知错误'));
        }
    });
}

function toggleTaskStatus(taskId, status) {
    safeFetch('/api/super_admin/tasks/' + taskId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: status })
    }).then(function(data) {
        if (data.success) {
            loadTasks();
        } else {
            alert('操作失败: ' + (data.message || '未知错误'));
        }
    });
}

function deleteTask(taskId) {
    if (!confirm('确定删除此任务？')) return;
    safeFetch('/api/super_admin/tasks/' + taskId, { method: 'DELETE' }).then(function(data) {
        if (data.success) {
            alert('任务删除成功');
            loadTasks();
        } else {
            alert('删除失败: ' + (data.message || '未知错误'));
        }
    });
}

function loadTaskLogs() {
    safeFetch('/api/super_admin/tasks/logs').then(function(data) {
        if (!data.success) return;
        var d = data.data || {};
        var tbody = document.querySelector('#task-log-table tbody');
        tbody.innerHTML = (d.logs || []).slice(0, 20).map(function(l) {
            var statusClass = l.status === 'success' ? 'badge-success' : (l.status === 'failed' ? 'badge-danger' : 'badge-warning');
            var statusText = l.status === 'success' ? '成功' : (l.status === 'failed' ? '失败' : '运行中');
            return '<tr><td>' + l.id + '</td><td>' + l.task_name + '</td><td><span class="badge ' + statusClass + '">' + statusText + '</span></td><td>' + (l.started_at || '-') + '</td><td>' + (l.completed_at || '-') + '</td><td>' + (l.error_message || '-') + '</td></tr>';
        }).join('');
    });
}

function loadSessions() {
    var search = document.getElementById('session-search').value;
    safeFetch('/api/super_admin/sessions?username=' + encodeURIComponent(search)).then(function(data) {
        if (!data.success) return;
        var d = data.data || {};
        var stats = d.stats || {};
        var activeEl = document.getElementById('session-active');
        var expiredEl = document.getElementById('session-expired');
        if (activeEl) activeEl.textContent = stats.active_count || 0;
        if (expiredEl) expiredEl.textContent = stats.expired_count || 0;
        
        var tbody = document.querySelector('#session-table tbody');
        tbody.innerHTML = (d.sessions || []).map(function(s) {
            var statusClass = s.status === 'active' ? 'badge-success' : 'badge-gray';
            var statusText = s.status === 'active' ? '活跃' : '已过期';
            return '<tr><td>' + s.id + '</td><td>' + s.username + '</td><td>' + s.role + '</td><td>' + (s.login_time || '-') + '</td><td>' + (s.last_activity || '-') + '</td><td>' + (s.ip_address || '-') + '</td><td><span class="badge ' + statusClass + '">' + statusText + '</span></td><td><button class="btn-sm btn-danger" onclick="terminateSession(' + s.id + ')">终止</button></td></tr>';
        }).join('');
    });
}

function terminateSession(sessionId) {
    if (!confirm('确定终止此会话？用户将被强制退出登录。')) return;
    safeFetch('/api/super_admin/sessions/' + sessionId, { method: 'DELETE' }).then(function(data) {
        if (data.success) {
            alert('会话已终止');
            loadSessions();
        } else {
            alert('操作失败: ' + (data.message || '未知错误'));
        }
    });
}

function terminateAllSessions() {
    if (!confirm('确定终止所有活跃会话？所有用户将被强制退出登录！')) return;
    safeFetch('/api/super_admin/sessions/terminate_all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    }).then(function(data) {
        if (data.success) {
            alert(data.message);
            loadSessions();
        } else {
            alert('操作失败: ' + (data.message || '未知错误'));
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    loadOverview();
    setInterval(loadResources, 5000);
});
