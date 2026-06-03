/**
 * MTSCOS AI 系统 - 权限路由系统
 * Permission-Based Routing System
 * 集成权限优先级判定法则的前端路由系统
 */

// 路由权限级别定义
const RoutePermissionLevel = {
    DENY: 0,           // 拒绝（最高优先级）
    ADMIN_OVERRIDE: 1, // 管理员覆盖
    EXPLICIT_ALLOW: 2, // 显式允许
    ROLE_BASED: 3,     // 角色基础权限
    GROUP_BASED: 4,    // 组基础权限
    INHERITED: 5,      // 继承权限
    IMPLICIT: 6,       // 隐式权限
    DEFAULT: 7         // 默认权限（最低优先级）
};

// 用户角色定义
const UserRoles = {
    SUPER_ADMIN: 'super_admin',
    ADMIN: 'admin',
    HARDWARE_ADMIN: 'hardware_admin',
    TEACHER: 'teacher',
    STUDENT: 'student',
    GUEST: 'guest'
};

// 权限类型
const PermissionType = {
    VIEW: 'view',
    EDIT: 'edit',
    CREATE: 'create',
    DELETE: 'delete',
    ADMIN: 'admin',
    EXPORT: 'export',
    IMPORT: 'import'
};

/**
 * 路由配置类
 */
class RouteConfig {
    constructor(path, name, component, options = {}) {
        this.path = path;
        this.name = name;
        this.component = component;
        this.options = {
            requiresAuth: options.requiresAuth || false,
            allowedRoles: options.allowedRoles || [],
            requiredPermissions: options.requiredPermissions || [],
            priorityLevel: options.priorityLevel || RoutePermissionLevel.ROLE_BASED,
            redirectUnauthorized: options.redirectUnauthorized || '/unauthorized',
            meta: options.meta || {}
        };
    }
}

/**
 * 权限路由管理器
 */
class PermissionRouter {
    constructor() {
        this.routes = new Map();
        this.currentRoute = null;
        this.userState = this._getUserState();
        this.routeHistory = [];
        this.permissionCache = new Map();
        this._init();
    }

    _init() {
        // 监听页面加载
        window.addEventListener('load', () => {
            this._handleRoute();
        });

        // 监听历史变化
        window.addEventListener('popstate', () => {
            this._handleRoute();
        });

        // 拦截链接点击
        document.addEventListener('click', (e) => {
            const target = e.target.closest('a[data-route]');
            if (target) {
                e.preventDefault();
                this.navigate(target.getAttribute('href'));
            }
        });

        console.log('🔐 权限路由系统初始化完成');
    }

    /**
     * 获取用户状态
     */
    _getUserState() {
        try {
            const stored = localStorage.getItem('mtcos_user');
            if (stored) {
                return JSON.parse(stored);
            }
        } catch (e) {
            console.warn('读取用户状态失败:', e);
        }
        return {
            isAuthenticated: false,
            role: UserRoles.GUEST,
            permissions: [],
            username: 'guest'
        };
    }

    /**
     * 设置用户状态
     */
    setUserState(userState) {
        this.userState = { ...this.userState, ...userState };
        localStorage.setItem('mtcos_user', JSON.stringify(this.userState));
        this.permissionCache.clear(); // 清除缓存
        console.log('👤 用户状态已更新:', this.userState);
    }

    /**
     * 注册路由
     */
    registerRoute(path, name, component, options = {}) {
        const route = new RouteConfig(path, name, component, options);
        this.routes.set(path, route);
        console.log(`📍 路由已注册: ${path} -> ${name}`);
    }

    /**
     * 批量注册路由
     */
    registerRoutes(routes) {
        routes.forEach(route => {
            this.registerRoute(
                route.path,
                route.name,
                route.component,
                route.options
            );
        });
    }

    /**
     * 检查用户是否有角色权限
     */
    _checkRolePermission(route) {
        if (!route.options.allowedRoles || route.options.allowedRoles.length === 0) {
            return true; // 无角色限制
        }

        return route.options.allowedRoles.includes(this.userState.role);
    }

    /**
     * 检查用户是否有特定权限
     */
    _checkPermissions(route) {
        if (!route.options.requiredPermissions || route.options.requiredPermissions.length === 0) {
            return true; // 无权限限制
        }

        return route.options.requiredPermissions.every(perm =>
            this.userState.permissions.includes(perm)
        );
    }

    /**
     * 执行权限检查
     */
    _checkRoutePermission(route) {
        // 生成缓存键
        const cacheKey = `${this.userState.username}:${route.path}`;

        // 检查缓存
        if (this.permissionCache.has(cacheKey)) {
            return this.permissionCache.get(cacheKey);
        }

        let result = {
            allowed: true,
            level: RoutePermissionLevel.DEFAULT,
            reason: '默认允许'
        };

        // 检查是否需要登录
        if (route.options.requiresAuth && !this.userState.isAuthenticated) {
            result = {
                allowed: false,
                level: RoutePermissionLevel.DENY,
                reason: '需要登录'
            };
        }
        // 检查角色权限
        else if (!this._checkRolePermission(route)) {
            result = {
                allowed: false,
                level: RoutePermissionLevel.ROLE_BASED,
                reason: '角色权限不足'
            };
        }
        // 检查具体权限
        else if (!this._checkPermissions(route)) {
            result = {
                allowed: false,
                level: RoutePermissionLevel.EXPLICIT_ALLOW,
                reason: '权限不足'
            };
        }

        // 超级管理员权限覆盖
        if (this.userState.role === UserRoles.SUPER_ADMIN) {
            result = {
                allowed: true,
                level: RoutePermissionLevel.ADMIN_OVERRIDE,
                reason: '超级管理员权限'
            };
        }

        // 缓存结果
        this.permissionCache.set(cacheKey, result);

        return result;
    }

    /**
     * 导航到路径
     */
    navigate(path, options = {}) {
        const route = this.routes.get(path);

        if (!route) {
            console.warn(`⚠️ 路由未找到: ${path}`);
            // 尝试匹配通配符路由
            const wildcardRoute = this.routes.get('*');
            if (wildcardRoute) {
                this._executeRoute(wildcardRoute, options);
            }
            return;
        }

        // 检查权限
        const permissionResult = this._checkRoutePermission(route);

        if (!permissionResult.allowed) {
            console.warn(`🚫 权限拒绝: ${path} - ${permissionResult.reason}`);
            this._handlePermissionDenied(route, permissionResult);
            return;
        }

        // 执行路由
        this._executeRoute(route, options);
    }

    /**
     * 执行路由
     */
    _executeRoute(route, options) {
        // 更新历史记录
        if (this.currentRoute) {
            this.routeHistory.push(this.currentRoute.path);
        }

        // 更新当前路由
        this.currentRoute = route;

        // 更新URL
        if (options.replace) {
            window.history.replaceState({}, '', route.path);
        } else {
            window.history.pushState({}, '', route.path);
        }

        // 渲染组件
        this._renderRoute(route);

        console.log(`✅ 导航成功: ${route.path}`);
    }

    /**
     * 渲染路由
     */
    _renderRoute(route) {
        const container = document.querySelector('[data-route-container]');
        if (!container) {
            console.warn('⚠️ 未找到路由容器');
            return;
        }

        // 执行组件函数
        if (typeof route.component === 'function') {
            try {
                const content = route.component(route.options.meta);
                if (typeof content === 'string') {
                    container.innerHTML = content;
                } else if (content instanceof HTMLElement) {
                    container.innerHTML = '';
                    container.appendChild(content);
                }
            } catch (e) {
                console.error('❌ 渲染路由失败:', e);
                container.innerHTML = `
                    <div class="error-page">
                        <h2>页面加载失败</h2>
                        <p>${e.message}</p>
                    </div>
                `;
            }
        }
    }

    /**
     * 处理权限拒绝
     */
    _handlePermissionDenied(route, permissionResult) {
        // 检查是否有自定义的重定向
        if (route.options.redirectUnauthorized) {
            const unauthRoute = this.routes.get(route.options.redirectUnauthorized);
            if (unauthRoute) {
                this._executeRoute(unauthRoute, { replace: true });
                return;
            }
        }

        // 显示权限错误
        const container = document.querySelector('[data-route-container]');
        if (container) {
            container.innerHTML = `
                <div class="permission-denied" style="
                    padding: 40px;
                    text-align: center;
                    color: white;
                ">
                    <div style="font-size: 48px; margin-bottom: 16px;">🚫</div>
                    <h2 style="margin-bottom: 16px;">权限不足</h2>
                    <p style="opacity: 0.8; margin-bottom: 24px;">${permissionResult.reason}</p>
                    <button onclick="window.router.navigate('/')" style="
                        padding: 12px 24px;
                        background: linear-gradient(135deg, #6366f1, #8b5cf6);
                        border: none;
                        border-radius: 8px;
                        color: white;
                        cursor: pointer;
                        font-size: 16px;
                    ">返回首页</button>
                </div>
            `;
        }
    }

    /**
     * 处理当前路由
     */
    _handleRoute() {
        const path = window.location.pathname || '/';
        this.navigate(path, { replace: true });
    }

    /**
     * 返回上一页
     */
    back() {
        if (this.routeHistory.length > 0) {
            const prevPath = this.routeHistory.pop();
            this.navigate(prevPath, { replace: true });
        } else {
            this.navigate('/');
        }
    }

    /**
     * 刷新当前路由
     */
    refresh() {
        if (this.currentRoute) {
            this._renderRoute(this.currentRoute);
        }
    }

    /**
     * 获取当前路由
     */
    getCurrentRoute() {
        return this.currentRoute;
    }

    /**
     * 获取当前用户可访问的路由
     */
    getAccessibleRoutes() {
        const accessible = [];
        this.routes.forEach((route, path) => {
            const result = this._checkRoutePermission(route);
            if (result.allowed) {
                accessible.push({
                    path,
                    name: route.name,
                    meta: route.options.meta
                });
            }
        });
        return accessible;
    }
}

/**
 * 预定义路由配置
 */
const DefaultRoutes = [
    {
        path: '/',
        name: '首页',
        component: () => `
            <div class="home-page" style="padding: 40px;">
                <h1 style="color: white; margin-bottom: 24px;">🏠 MTSCOS 智能管理系统</h1>
                <p style="color: rgba(255,255,255,0.8);">欢迎使用 MTSCOS AI 系统</p>
            </div>
        `,
        options: {
            requiresAuth: false,
            meta: { icon: '🏠' }
        }
    },
    {
        path: '/login',
        name: '登录',
        component: () => `
            <div class="login-page" style="padding: 40px;">
                <h1 style="color: white; margin-bottom: 24px;">🔐 登录</h1>
                <p style="color: rgba(255,255,255,0.8);">请登录您的账户</p>
            </div>
        `,
        options: {
            requiresAuth: false,
            meta: { icon: '🔐' }
        }
    },
    {
        path: '/dashboard',
        name: '仪表板',
        component: () => `
            <div class="dashboard-page" style="padding: 40px;">
                <h1 style="color: white; margin-bottom: 24px;">📊 仪表板</h1>
                <p style="color: rgba(255,255,255,0.8);">系统监控和数据分析</p>
            </div>
        `,
        options: {
            requiresAuth: true,
            allowedRoles: [UserRoles.ADMIN, UserRoles.SUPER_ADMIN, UserRoles.TEACHER],
            requiredPermissions: [PermissionType.VIEW],
            meta: { icon: '📊' }
        }
    },
    {
        path: '/admin',
        name: '管理中心',
        component: () => `
            <div class="admin-page" style="padding: 40px;">
                <h1 style="color: white; margin-bottom: 24px;">⚙️ 管理中心</h1>
                <p style="color: rgba(255,255,255,0.8);">系统管理和配置</p>
            </div>
        `,
        options: {
            requiresAuth: true,
            allowedRoles: [UserRoles.ADMIN, UserRoles.SUPER_ADMIN],
            requiredPermissions: [PermissionType.ADMIN],
            priorityLevel: RoutePermissionLevel.ADMIN_OVERRIDE,
            meta: { icon: '⚙️' }
        }
    },
    {
        path: '/exams',
        name: '考试管理',
        component: () => `
            <div class="exams-page" style="padding: 40px;">
                <h1 style="color: white; margin-bottom: 24px;">📝 考试管理</h1>
                <p style="color: rgba(255,255,255,0.8);">管理考试和题库</p>
            </div>
        `,
        options: {
            requiresAuth: true,
            allowedRoles: [UserRoles.TEACHER, UserRoles.ADMIN, UserRoles.SUPER_ADMIN],
            requiredPermissions: [PermissionType.VIEW, PermissionType.CREATE],
            meta: { icon: '📝' }
        }
    },
    {
        path: '/hardware',
        name: '硬件管理',
        component: () => `
            <div class="hardware-page" style="padding: 40px;">
                <h1 style="color: white; margin-bottom: 24px;">🔧 硬件管理</h1>
                <p style="color: rgba(255,255,255,0.8);">硬件设备管理</p>
            </div>
        `,
        options: {
            requiresAuth: true,
            allowedRoles: [UserRoles.HARDWARE_ADMIN, UserRoles.SUPER_ADMIN],
            meta: { icon: '🔧' }
        }
    },
    {
        path: '/unauthorized',
        name: '权限不足',
        component: () => `
            <div class="unauthorized-page" style="padding: 40px; text-align: center;">
                <h1 style="color: white; margin-bottom: 24px;">🚫 权限不足</h1>
                <p style="color: rgba(255,255,255,0.8);">您没有权限访问此页面</p>
            </div>
        `,
        options: {
            requiresAuth: false,
            meta: { icon: '🚫' }
        }
    },
    {
        path: '*',
        name: '404',
        component: () => `
            <div class="not-found-page" style="padding: 40px; text-align: center;">
                <h1 style="color: white; margin-bottom: 24px;">404</h1>
                <p style="color: rgba(255,255,255,0.8);">页面未找到</p>
            </div>
        `,
        options: {
            requiresAuth: false,
            meta: { icon: '❓' }
        }
    }
];

// 初始化路由系统
const router = new PermissionRouter();
router.registerRoutes(DefaultRoutes);

// 暴露到全局
window.router = router;
window.UserRoles = UserRoles;
window.PermissionType = PermissionType;
window.RoutePermissionLevel = RoutePermissionLevel;

console.log('✅ 权限路由系统已加载');

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        PermissionRouter,
        RouteConfig,
        UserRoles,
        PermissionType,
        RoutePermissionLevel,
        DefaultRoutes,
        router
    };
}
