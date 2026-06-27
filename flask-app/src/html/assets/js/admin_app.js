// Admin App JavaScript Utilities

// Toast notification system
function showToast(message, duration) {
    if (duration === undefined) {
        duration = 2000;
    }
    var existing = document.querySelector('.toast-notification');
    if (existing) {
        existing.remove();
    }
    
    var toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.textContent = message;
    toast.style.cssText = 'position:fixed;top:80px;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:12px 24px;border-radius:8px;font-size:14px;z-index:10001;animation:fadeIn 0.3s ease;box-shadow:0 4px 12px rgba(0,0,0,0.15);';
    
    var style = document.createElement('style');
    style.textContent = '@keyframes fadeIn{from{opacity:0;transform:translateX(-50%) translateY(-10px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}';
    document.head.appendChild(style);
    document.body.appendChild(toast);
    
    setTimeout(function() {
        toast.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(function() {
            toast.remove();
        }, 300);
    }, duration);
}

// Modal system
function showModal(title, content, options) {
    var defaults = {
        showFooter: true,
        confirmText: '确定',
        cancelText: '取消',
        onConfirm: null,
        onCancel: null
    };
    var opts = defaults;
    if (options) {
        for (var key in options) {
            opts[key] = options[key];
        }
    }
    
    var overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);z-index:10000;display:flex;align-items:center;justify-content:center;animation:fadeIn 0.2s ease;';
    
    var modal = document.createElement('div');
    modal.style.cssText = 'background:var(--card-bg);border-radius:16px;width:90%;max-width:400px;max-height:80vh;overflow:hidden;animation:slideUp 0.3s ease;';
    
    var header = document.createElement('div');
    header.style.cssText = 'padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;';
    header.innerHTML = '<div style="font-size:16px;font-weight:600;">' + title + '</div>';
    
    var closeBtn = document.createElement('button');
    closeBtn.style.cssText = 'width:32px;height:32px;border:none;background:transparent;color:var(--text-secondary);cursor:pointer;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;';
    closeBtn.innerHTML = '<i class="fas fa-times"></i>';
    closeBtn.onclick = function() {
        document.body.removeChild(overlay);
        if (opts.onCancel) opts.onCancel();
    };
    header.appendChild(closeBtn);
    
    var body = document.createElement('div');
    body.style.cssText = 'padding:20px;max-height:50vh;overflow-y:auto;';
    body.innerHTML = content;
    
    var footer = '';
    if (opts.showFooter) {
        footer = '<div style="padding:16px 20px;border-top:1px solid var(--border);display:flex;gap:12px;justify-content:flex-end;">' +
            '<button onclick="document.body.removeChild(document.querySelector(\'.modal-overlay\'));" style="padding:10px 20px;border:1px solid var(--border);background:var(--card-bg);color:var(--text-primary);border-radius:8px;cursor:pointer;">' + opts.cancelText + '</button>' +
            '<button onclick="if(opts.onConfirm){opts.onConfirm();}document.body.removeChild(document.querySelector(\'.modal-overlay\'));" style="padding:10px 20px;border:none;background:var(--primary);color:#fff;border-radius:8px;cursor:pointer;">' + opts.confirmText + '</button>' +
            '</div>';
    }
    
    modal.appendChild(header);
    modal.appendChild(body);
    if (footer) modal.insertAdjacentHTML('beforeend', footer);
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            document.body.removeChild(overlay);
            if (opts.onCancel) opts.onCancel();
        }
    });
}

// Format date helper
function formatDate(dateStr) {
    if (!dateStr) return '-';
    
    var date = new Date(dateStr);
    var now = new Date();
    var diff = now - date;
    
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前';
    if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前';
    if (diff < 604800000) return Math.floor(diff / 86400000) + '天前';
    
    return dateStr.split('T')[0];
}

// Role utilities
function getRoleName(role) {
    var roles = {
        'super_admin': '超级管理员',
        'admin': '管理员',
        'hardware_admin': '硬件管理员',
        'teacher': '教师',
        'student': '学生',
        'designer': '设计师',
        'user': '普通用户',
        'guest': '访客'
    };
    return roles[role] || role;
}

function getRoleTagClass(role) {
    var classes = {
        'super_admin': 'tag-red',
        'admin': 'tag-purple',
        'hardware_admin': 'tag-blue',
        'teacher': 'tag-green',
        'student': 'tag-blue',
        'designer': 'tag-yellow',
        'user': 'tag-gray',
        'guest': 'tag-gray'
    };
    return classes[role] || 'tag-gray';
}

// API request helper
function apiRequest(url, options) {
    var defaults = {
        method: 'GET',
        headers: {},
        body: null
    };
    
    var opts = defaults;
    if (options) {
        for (var key in options) {
            opts[key] = options[key];
        }
    }
    
    var headers = opts.headers || {};
    headers['Content-Type'] = 'application/json';
    
    var fetchOptions = {
        method: opts.method,
        headers: headers
    };
    
    if (opts.body && opts.method !== 'GET') {
        fetchOptions.body = JSON.stringify(opts.body);
    }
    
    return fetch(url, fetchOptions)
        .then(function(response) {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        });
}

// Confirm dialog
function showConfirm(message, onConfirm, onCancel) {
    showModal('确认', '<div style="text-align:center;padding:20px 0;"><i class="fas fa-exclamation-triangle" style="font-size:48px;color:#f59e0b;margin-bottom:16px;"></i><div style="font-size:15px;">' + message + '</div></div>', {
        showFooter: true,
        confirmText: '确认',
        cancelText: '取消',
        onConfirm: onConfirm,
        onCancel: onCancel
    });
}

// Loading indicator
function showLoading() {
    var existing = document.querySelector('.loading-indicator');
    if (existing) return;
    
    var loading = document.createElement('div');
    loading.className = 'loading-indicator';
    loading.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(0,0,0,0.8);color:#fff;padding:20px 40px;border-radius:12px;z-index:10002;display:flex;align-items:center;gap:12px;';
    loading.innerHTML = '<i class="fas fa-spinner fa-spin" style="font-size:24px;"></i><span>加载中...</span>';
    document.body.appendChild(loading);
}

function hideLoading() {
    var loading = document.querySelector('.loading-indicator');
    if (loading) loading.remove();
}
