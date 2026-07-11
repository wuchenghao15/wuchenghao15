/**
 * MTSCOS AI System - 前端权限控制管理器
 * 版本: 4.4.0
 * 描述: 根据用户角色和权限动态控制页面元素显示和操作
 */

class PermissionController {
    constructor() {
        this.currentRole = 'guest';
        this.currentUser = null;
        this.permissions = new Map();
        this.init();
    }

    init() {
        // 从存储或全局变量获取用户信息
        this.loadCurrentUser();
        
        // 监听用户登录状态变化
        document.addEventListener('mtscos:user:login', (e) => {
            this.setUser(e.detail?.user || e.detail);
        });
        
        document.addEventListener('mtscos:user:logout', () => {
            this.clearUser();
        });
        
        // 页面加载完成后应用权限
        document.addEventListener('DOMContentLoaded', () => {
            this.applyAllPermissions();
        });
    }

    // ==================== 用户管理 ====================

    loadCurrentUser() {
        // 优先从全局变量获取
        if (window.currentUser) {
            this.setUser(window.currentUser);
            return;
        }
        
        // 从localStorage获取
        try {
            const userData = localStorage.getItem('mtscos_user');
            if (userData) {
                const user = JSON.parse(userData);
                this.setUser(user);
            }
        } catch (e) {
            console.warn('加载用户信息失败:', e);
        }
    }

    setUser(user) {
        if (!user) return;
        
        this.currentUser = user;
        this.currentRole = user.role || user.permissionLevel || 'guest';
        
        // 存储到localStorage
        try {
            localStorage.setItem('mtscos_user', JSON.stringify(user));
        } catch (e) {
            console.warn('保存用户信息失败:', e);
        }
        
        // 触发权限更新事件
        document.dispatchEvent(new CustomEvent('mtscos:permission:changed', {
            detail: { role: this.currentRole, user: user }
        }));
    }

    clearUser() {
        this.currentUser = null;
        this.currentRole = 'guest';
        this.permissions.clear();
        
        localStorage.removeItem('mtscos_user');
        
        document.dispatchEvent(new CustomEvent('mtscos:permission:cleared'));
    }

    getUser() {
        return this.currentUser;
    }

    getRole() {
        return this.currentRole;
    }

    // ==================== 角色权限配置 ====================

    get rolePermissions() {
        return {
            superadmin: {
                // 仪表盘
                'dashboard:view': true,
                'dashboard:stats': true,
                'dashboard:refresh': true,
                
                // 通用设置
                'settings:general:view': true,
                'settings:general:edit': true,
                'settings:theme:view': true,
                'settings:theme:edit': true,
                'settings:language:view': true,
                'settings:language:edit': true,
                
                // 安全设置
                'settings:security:view': true,
                'settings:security:edit': true,
                'settings:password:view': true,
                'settings:password:edit': true,
                'settings:mfa:view': true,
                'settings:mfa:edit': true,
                
                // 数据库设置
                'settings:database:view': true,
                'settings:database:edit': true,
                'settings:database:backup': true,
                'settings:database:restore': true,
                'settings:database:clear': true,
                
                // AI设置
                'settings:ai:view': true,
                'settings:ai:edit': true,
                'settings:ai:model:view': true,
                'settings:ai:model:edit': true,
                
                // 用户管理
                'users:view': true,
                'users:create': true,
                'users:edit': true,
                'users:delete': true,
                'users:export': true,
                
                // 权限管理
                'permissions:view': true,
                'permissions:edit': true,
                
                // 角色管理
                'roles:view': true,
                'roles:create': true,
                'roles:edit': true,
                'roles:delete': true,
                
                // 审计日志
                'audit:view': true,
                'audit:export': true,
                
                // 系统工具
                'logs:view': true,
                'logs:clear': true,
                'logs:export': true,
                'backup:view': true,
                'backup:create': true,
                'backup:restore': true,
                'backup:delete': true,
                'maintenance:view': true,
                'maintenance:execute': true,
                
                // 系统设置
                'system:config:view': true,
                'system:config:edit': true,
                'system:version:view': true,
                'system:version:upgrade': true,
                
                // 高级功能
                'advanced:cache:clear': true,
                'advanced:optimize': true,
                'advanced:debug': true,
                'advanced:developer': true
            },
            
            admin: {
                'dashboard:view': true,
                'dashboard:stats': true,
                'dashboard:refresh': true,
                
                'settings:general:view': true,
                'settings:general:edit': true,
                'settings:theme:view': true,
                'settings:theme:edit': true,
                'settings:language:view': true,
                'settings:language:edit': true,
                
                'settings:security:view': true,
                'settings:security:edit': false,
                'settings:password:view': true,
                'settings:password:edit': true,
                'settings:mfa:view': true,
                'settings:mfa:edit': false,
                
                'settings:database:view': true,
                'settings:database:edit': false,
                'settings:database:backup': true,
                'settings:database:restore': false,
                'settings:database:clear': false,
                
                'settings:ai:view': true,
                'settings:ai:edit': true,
                'settings:ai:model:view': true,
                'settings:ai:model:edit': false,
                
                'users:view': true,
                'users:create': true,
                'users:edit': true,
                'users:delete': false,
                'users:export': true,
                
                'permissions:view': true,
                'permissions:edit': false,
                
                'roles:view': true,
                'roles:create': false,
                'roles:edit': false,
                'roles:delete': false,
                
                'audit:view': true,
                'audit:export': true,
                
                'logs:view': true,
                'logs:clear': false,
                'logs:export': true,
                'backup:view': true,
                'backup:create': true,
                'backup:restore': true,
                'backup:delete': false,
                'maintenance:view': true,
                'maintenance:execute': false,
                
                'system:config:view': true,
                'system:config:edit': false,
                'system:version:view': true,
                'system:version:upgrade': false,
                
                'advanced:cache:clear': false,
                'advanced:optimize': false,
                'advanced:debug': false,
                'advanced:developer': false
            },
            
            vikey_admin: {
                'dashboard:view': true,
                'dashboard:stats': true,
                'dashboard:refresh': true,
                
                'settings:general:view': true,
                'settings:general:edit': true,
                'settings:theme:view': true,
                'settings:theme:edit': true,
                'settings:language:view': true,
                'settings:language:edit': true,
                
                'settings:security:view': true,
                'settings:security:edit': true,
                'settings:password:view': true,
                'settings:password:edit': true,
                'settings:mfa:view': true,
                'settings:mfa:edit': true,
                
                'settings:database:view': true,
                'settings:database:edit': true,
                'settings:database:backup': true,
                'settings:database:restore': true,
                'settings:database:clear': true,
                
                'settings:ai:view': true,
                'settings:ai:edit': true,
                'settings:ai:model:view': true,
                'settings:ai:model:edit': true,
                
                'users:view': true,
                'users:create': true,
                'users:edit': true,
                'users:delete': true,
                'users:export': true,
                
                'permissions:view': true,
                'permissions:edit': true,
                
                'roles:view': true,
                'roles:create': true,
                'roles:edit': true,
                'roles:delete': true,
                
                'audit:view': true,
                'audit:export': true,
                
                'logs:view': true,
                'logs:clear': true,
                'logs:export': true,
                'backup:view': true,
                'backup:create': true,
                'backup:restore': true,
                'backup:delete': true,
                'maintenance:view': true,
                'maintenance:execute': true,
                
                'system:config:view': true,
                'system:config:edit': true,
                'system:version:view': true,
                'system:version:upgrade': true,
                
                'advanced:cache:clear': true,
                'advanced:optimize': true,
                'advanced:debug': true,
                'advanced:developer': true
            },
            
            user: {
                'dashboard:view': true,
                'dashboard:stats': false,
                'dashboard:refresh': false,
                
                'settings:general:view': true,
                'settings:general:edit': true,
                'settings:theme:view': true,
                'settings:theme:edit': true,
                'settings:language:view': true,
                'settings:language:edit': true,
                
                'settings:security:view': true,
                'settings:security:edit': false,
                'settings:password:view': true,
                'settings:password:edit': true,
                'settings:mfa:view': true,
                'settings:mfa:edit': false,
                
                'settings:database:view': false,
                'settings:database:edit': false,
                'settings:database:backup': false,
                'settings:database:restore': false,
                'settings:database:clear': false,
                
                'settings:ai:view': true,
                'settings:ai:edit': false,
                'settings:ai:model:view': true,
                'settings:ai:model:edit': false,
                
                'users:view': false,
                'users:create': false,
                'users:edit': false,
                'users:delete': false,
                'users:export': false,
                
                'permissions:view': false,
                'permissions:edit': false,
                
                'roles:view': false,
                'roles:create': false,
                'roles:edit': false,
                'roles:delete': false,
                
                'audit:view': false,
                'audit:export': false,
                
                'logs:view': false,
                'logs:clear': false,
                'logs:export': false,
                'backup:view': false,
                'backup:create': false,
                'backup:restore': false,
                'backup:delete': false,
                'maintenance:view': false,
                'maintenance:execute': false,
                
                'system:config:view': false,
                'system:config:edit': false,
                'system:version:view': true,
                'system:version:upgrade': false,
                
                'advanced:cache:clear': false,
                'advanced:optimize': false,
                'advanced:debug': false,
                'advanced:developer': false
            },
            
            guest: {
                'dashboard:view': false,
                'dashboard:stats': false,
                'dashboard:refresh': false,
                
                'settings:general:view': false,
                'settings:general:edit': false,
                'settings:theme:view': false,
                'settings:theme:edit': false,
                'settings:language:view': false,
                'settings:language:edit': false,
                
                'settings:security:view': false,
                'settings:security:edit': false,
                'settings:password:view': false,
                'settings:password:edit': false,
                'settings:mfa:view': false,
                'settings:mfa:edit': false,
                
                'settings:database:view': false,
                'settings:database:edit': false,
                'settings:database:backup': false,
                'settings:database:restore': false,
                'settings:database:clear': false,
                
                'settings:ai:view': false,
                'settings:ai:edit': false,
                'settings:ai:model:view': false,
                'settings:ai:model:edit': false,
                
                'users:view': false,
                'users:create': false,
                'users:edit': false,
                'users:delete': false,
                'users:export': false,
                
                'permissions:view': false,
                'permissions:edit': false,
                
                'roles:view': false,
                'roles:create': false,
                'roles:edit': false,
                'roles:delete': false,
                
                'audit:view': false,
                'audit:export': false,
                
                'logs:view': false,
                'logs:clear': false,
                'logs:export': false,
                'backup:view': false,
                'backup:create': false,
                'backup:restore': false,
                'backup:delete': false,
                'maintenance:view': false,
                'maintenance:execute': false,
                
                'system:config:view': false,
                'system:config:edit': false,
                'system:version:view': false,
                'system:version:upgrade': false,
                
                'advanced:cache:clear': false,
                'advanced:optimize': false,
                'advanced:debug': false,
                'advanced:developer': false
            }
        };
    }

    // ==================== 权限检查 ====================

    hasPermission(permission) {
        const permissions = this.rolePermissions[this.currentRole] || {};
        return permissions[permission] === true;
    }

    canView(permission) {
        return this.hasPermission(permission);
    }

    canEdit(permission) {
        return this.hasPermission(permission.replace(':view', ':edit'));
    }

    canExecute(permission) {
        return this.hasPermission(permission);
    }

    // 检查多个权限（需要全部满足）
    hasAllPermissions(...permissions) {
        return permissions.every(p => this.hasPermission(p));
    }

    // 检查多个权限（满足任一即可）
    hasAnyPermission(...permissions) {
        return permissions.some(p => this.hasPermission(p));
    }

    // ==================== 元素权限控制 ====================

    // 应用所有权限
    applyAllPermissions() {
        // 隐藏无权限的元素
        this.hideUnauthorizedElements();
        
        // 禁用无权限的按钮和输入框
        this.disableUnauthorizedControls();
        
        // 移除无权限的操作按钮
        this.removeUnauthorizedActions();
        
        // 应用菜单权限
        this.applyMenuPermissions();
        
        // 应用面板权限
        this.applyPanelPermissions();
        
        console.log(`✅ 权限控制已应用，当前角色: ${this.currentRole}`);
    }

    // 隐藏无权限元素
    hideUnauthorizedElements() {
        document.querySelectorAll('[data-permission]').forEach(el => {
            const permission = el.getAttribute('data-permission');
            if (!this.hasPermission(permission)) {
                el.style.display = 'none';
                el.setAttribute('data-permission-hidden', 'true');
            }
        });
    }

    // 禁用无权限控件
    disableUnauthorizedControls() {
        document.querySelectorAll('[data-permission-view]').forEach(el => {
            const permission = el.getAttribute('data-permission-view');
            if (!this.hasPermission(permission)) {
                el.disabled = true;
                el.setAttribute('data-permission-disabled', 'true');
            }
        });
        
        document.querySelectorAll('[data-permission-edit]').forEach(el => {
            const permission = el.getAttribute('data-permission-edit');
            if (!this.canEdit(permission)) {
                el.disabled = true;
                el.readOnly = true;
                el.setAttribute('data-permission-disabled', 'true');
            }
        });
    }

    // 移除无权限操作
    removeUnauthorizedActions() {
        document.querySelectorAll('[data-permission-action]').forEach(el => {
            const permission = el.getAttribute('data-permission-action');
            if (!this.hasPermission(permission)) {
                el.remove();
            }
        });
    }

    // 应用菜单权限
    applyMenuPermissions() {
        document.querySelectorAll('.menu-item[data-panel]').forEach(menu => {
            const panel = menu.getAttribute('data-panel');
            const permission = this.getPanelPermission(panel);
            
            if (permission && !this.hasPermission(permission)) {
                menu.style.display = 'none';
                menu.setAttribute('data-menu-hidden', 'true');
            }
        });
    }

    // 应用面板权限
    applyPanelPermissions() {
        document.querySelectorAll('.panel[id]').forEach(panel => {
            const panelId = panel.id;
            const permission = this.getPanelPermission(panelId);
            
            if (permission && !this.hasPermission(permission)) {
                panel.style.display = 'none';
                panel.setAttribute('data-panel-hidden', 'true');
                
                // 如果当前显示的是无权限面板，切换到第一个有权限的面板
                if (panel.classList.contains('active')) {
                    const firstVisible = document.querySelector('.panel:not([data-panel-hidden="true"])');
                    if (firstVisible) {
                        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
                        firstVisible.classList.add('active');
                        
                        document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));
                        const menu = document.querySelector(`.menu-item[data-panel="${firstVisible.id}"]`);
                        if (menu) menu.classList.add('active');
                    }
                }
            }
        });
    }

    // 获取面板对应的权限
    getPanelPermission(panelId) {
        const panelPermissions = {
            'dashboard': 'dashboard:view',
            'project-info': 'dashboard:view',
            'system-status': 'dashboard:view',
            'general-settings': 'settings:general:view',
            'security-settings': 'settings:security:view',
            'database-settings': 'settings:database:view',
            'ai-settings': 'settings:ai:view',
            'users': 'users:view',
            'permissions': 'permissions:view',
            'roles': 'roles:view',
            'audit': 'audit:view',
            'logs': 'logs:view',
            'backup': 'backup:view',
            'maintenance': 'maintenance:view'
        };
        
        return panelPermissions[panelId];
    }

    // ==================== 动态权限显示 ====================

    // 根据权限显示/隐藏元素
    showIfPermission(element, permission, show = true) {
        const has = this.hasPermission(permission);
        if (element) {
            element.style.display = (has === show) ? '' : 'none';
        }
        return has;
    }

    // 根据权限启用/禁用元素
    enableIfPermission(element, permission, enable = true) {
        const has = this.hasPermission(permission);
        if (element) {
            element.disabled = (has !== enable);
        }
        return has;
    }

    // 根据权限添加/移除类
    toggleClassIfPermission(element, permission, className, addIfHas = true) {
        const has = this.hasPermission(permission);
        if (element) {
            if (has === addIfHas) {
                element.classList.add(className);
            } else {
                element.classList.remove(className);
            }
        }
        return has;
    }

    // 根据权限显示工具提示
    updateTooltip(element, permission) {
        if (!element) return;
        
        if (!this.hasPermission(permission)) {
            element.title = '您没有此权限';
            element.setAttribute('data-tooltip-locked', 'true');
        }
    }

    // ==================== 快捷方法 ====================

    // 检查是否是管理员
    isAdmin() {
        return ['superadmin', 'admin', 'vikey_admin'].includes(this.currentRole);
    }

    // 检查是否是超级管理员
    isSuperAdmin() {
        return this.currentRole === 'superadmin' || this.currentRole === 'vikey_admin';
    }

    // 检查是否可以管理用户
    canManageUsers() {
        return this.hasAnyPermission('users:create', 'users:edit', 'users:delete');
    }

    // 检查是否可以查看敏感数据
    canViewSensitiveData() {
        return this.isAdmin();
    }

    // 获取用户可用的菜单
    getAvailableMenus() {
        const menus = [];
        document.querySelectorAll('.menu-item[data-panel]').forEach(menu => {
            if (!menu.hasAttribute('data-menu-hidden')) {
                menus.push({
                    id: menu.getAttribute('data-panel'),
                    text: menu.querySelector('span')?.textContent || '',
                    icon: menu.querySelector('i')?.className || ''
                });
            }
        });
        return menus;
    }

    // ==================== 事件 ====================

    // 触发权限检查事件
    checkPermission(permission) {
        const has = this.hasPermission(permission);
        document.dispatchEvent(new CustomEvent('mtscos:permission:check', {
            detail: { permission, has }
        }));
        return has;
    }

    // 重新应用权限
    refresh() {
        // 恢复所有被隐藏的元素
        document.querySelectorAll('[data-permission-hidden="true"]').forEach(el => {
            el.style.display = '';
            el.removeAttribute('data-permission-hidden');
        });
        
        document.querySelectorAll('[data-permission-disabled="true"]').forEach(el => {
            el.disabled = false;
            el.readOnly = false;
            el.removeAttribute('data-permission-disabled');
        });
        
        document.querySelectorAll('[data-menu-hidden="true"]').forEach(el => {
            el.style.display = '';
            el.removeAttribute('data-menu-hidden');
        });
        
        document.querySelectorAll('[data-panel-hidden="true"]').forEach(el => {
            el.style.display = '';
            el.removeAttribute('data-panel-hidden');
        });
        
        // 重新应用权限
        this.applyAllPermissions();
    }
}

// 创建全局实例
window.permissionController = new PermissionController();

// 便捷方法
window.Permission = {
    has: (perm) => window.permissionController.hasPermission(perm),
    can: (perm) => window.permissionController.hasPermission(perm),
    isAdmin: () => window.permissionController.isAdmin(),
    isSuperAdmin: () => window.permissionController.isSuperAdmin(),
    refresh: () => window.permissionController.refresh()
};

// 手动设置用户角色（用于测试或开发）
window.setUserRole = (role) => {
    window.permissionController.setUser({ role });
    window.permissionController.refresh();
};

// 获取当前权限信息
window.getPermissionInfo = () => {
    const pc = window.permissionController;
    return {
        role: pc.getRole(),
        isAdmin: pc.isAdmin(),
        isSuperAdmin: pc.isSuperAdmin(),
        availableMenus: pc.getAvailableMenus()
    };
};
