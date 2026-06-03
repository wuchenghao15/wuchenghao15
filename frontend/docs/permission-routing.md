# 🔐 MTSCOS 权限路由系统

## 概述

MTSCOS 权限路由系统是一个基于角色和权限的前端路由系统，完全集成了系统权限优先判定法则。

## 📁 文件结构

```
frontend/
├── assets/
│   └── js/
│       └── permission-routing.js    # 核心路由系统
├── pages/
│   └── routing-demo.html            # 路由系统演示页面
└── docs/
    └── permission-routing.md        # 本文档
```

## 🚀 快速开始

### 1. 引入路由系统

```html
<script src="assets/js/permission-routing.js"></script>
```

### 2. 基础使用

```javascript
// 设置用户状态
router.setUserState({
    isAuthenticated: true,
    role: UserRoles.ADMIN,
    permissions: [PermissionType.VIEW, PermissionType.EDIT],
    username: 'admin'
});

// 导航到路径
router.navigate('/dashboard');
```

### 3. 注册自定义路由

```javascript
router.registerRoute(
    '/custom',
    '自定义页面',
    () => '<div>自定义内容</div>',
    {
        requiresAuth: true,
        allowedRoles: [UserRoles.ADMIN],
        requiredPermissions: [PermissionType.VIEW]
    }
);
```

## 👥 用户角色

| 角色 | 常量 | 描述 | 权限 |
|------|------|------|------|
| 访客 | GUEST | 未登录用户 | 无 |
| 学生 | STUDENT | 普通学生 | view |
| 教师 | TEACHER | 教师用户 | view, create, edit |
| 管理员 | ADMIN | 系统管理员 | view, create, edit, delete, admin |
| 硬件管理员 | HARDWARE_ADMIN | 硬件管理专员 | view, create, edit, delete |
| 超级管理员 | SUPER_ADMIN | 最高权限 | 所有权限 |

## 🔑 权限类型

| 权限 | 常量 | 描述 |
|------|------|------|
| 查看 | VIEW | 查看资源 |
| 编辑 | EDIT | 修改资源 |
| 创建 | CREATE | 创建新资源 |
| 删除 | DELETE | 删除资源 |
| 管理 | ADMIN | 系统管理 |
| 导出 | EXPORT | 导出数据 |
| 导入 | IMPORT | 导入数据 |

## ⚖️ 权限优先级

| 级别 | 优先级 | 说明 |
|------|--------|------|
| DENY | 0 | 显式拒绝（最高优先级） |
| ADMIN_OVERRIDE | 1 | 管理员覆盖 |
| EXPLICIT_ALLOW | 2 | 显式允许 |
| ROLE_BASED | 3 | 角色基础权限 |
| GROUP_BASED | 4 | 组基础权限 |
| INHERITED | 5 | 继承权限 |
| IMPLICIT | 6 | 隐式权限 |
| DEFAULT | 7 | 默认权限（最低） |

## 📋 预定义路由

| 路径 | 名称 | 权限要求 |
|------|------|----------|
| / | 首页 | 无 |
| /login | 登录页 | 无 |
| /dashboard | 仪表板 | 需要登录，教师/管理员 |
| /admin | 管理中心 | 需要登录，管理员 |
| /exams | 考试管理 | 需要登录，教师/管理员 |
| /hardware | 硬件管理 | 需要登录，硬件管理员 |
| /unauthorized | 权限不足 | 无 |
| * | 404页面 | 无 |

## 🎯 API 参考

### PermissionRouter 类

#### 属性

| 属性 | 类型 | 描述 |
|------|------|------|
| routes | Map | 注册的路由 |
| currentRoute | RouteConfig | 当前路由 |
| userState | Object | 用户状态 |
| routeHistory | Array | 路由历史 |

#### 方法

##### `registerRoute(path, name, component, options)`

注册单个路由

```javascript
router.registerRoute(
    '/path',
    '页面名称',
    () => '<div>内容</div>',
    {
        requiresAuth: true,
        allowedRoles: [UserRoles.ADMIN],
        requiredPermissions: [PermissionType.VIEW],
        priorityLevel: RoutePermissionLevel.ROLE_BASED,
        meta: { icon: '📋' }
    }
);
```

##### `registerRoutes(routes)`

批量注册路由

```javascript
router.registerRoutes([
    { path: '/a', name: 'A', component: ..., options: ... },
    { path: '/b', name: 'B', component: ..., options: ... }
]);
```

##### `navigate(path, options)`

导航到路径

```javascript
router.navigate('/dashboard', { replace: true });
```

##### `back()`

返回上一页

```javascript
router.back();
```

##### `refresh()`

刷新当前路由

```javascript
router.refresh();
```

##### `getCurrentRoute()`

获取当前路由

```javascript
const route = router.getCurrentRoute();
console.log(route.name);
```

##### `getAccessibleRoutes()`

获取用户可访问的路由

```javascript
const routes = router.getAccessibleRoutes();
// 返回当前用户可访问的路由列表
```

##### `setUserState(userState)`

设置用户状态

```javascript
router.setUserState({
    isAuthenticated: true,
    role: UserRoles.TEACHER,
    permissions: [PermissionType.VIEW, PermissionType.CREATE],
    username: 'teacher1'
});
```

##### `_checkRoutePermission(route)`

检查路由权限（内部方法）

```javascript
const result = router._checkRoutePermission(route);
console.log(result.allowed); // true/false
console.log(result.reason); // 权限解释
```

### RouteConfig 类

路由配置对象

| 属性 | 类型 | 描述 |
|------|------|------|
| path | string | 路由路径 |
| name | string | 路由名称 |
| component | function | 渲染函数 |
| options | object | 配置选项 |

#### options 配置

| 属性 | 类型 | 默认 | 描述 |
|------|------|------|------|
| requiresAuth | boolean | false | 是否需要登录 |
| allowedRoles | array | [] | 允许的角色列表 |
| requiredPermissions | array | [] | 必需的权限列表 |
| priorityLevel | number | ROLE_BASED | 权限优先级 |
| redirectUnauthorized | string | /unauthorized | 未授权跳转路径 |
| meta | object | {} | 附加元数据 |

## 🎨 使用示例

### 示例1：基础导航

```html
<nav>
    <a href="/" data-route>首页</a>
    <a href="/dashboard" data-route>仪表板</a>
    <a href="/admin" data-route>管理中心</a>
</nav>
<div data-route-container></div>

<script src="permission-routing.js"></script>
<script>
    // 点击链接会自动路由
</script>
```

### 示例2：角色切换

```javascript
// 切换到学生角色
router.setUserState({
    isAuthenticated: true,
    role: UserRoles.STUDENT,
    permissions: [PermissionType.VIEW],
    username: 'student1'
});

// 学生只能访问首页和仪表板
router.navigate('/dashboard'); // 允许
router.navigate('/admin'); // 权限不足，重定向
```

### 示例3：管理员操作

```javascript
// 超级管理员
router.setUserState({
    isAuthenticated: true,
    role: UserRoles.SUPER_ADMIN,
    permissions: [PermissionType.VIEW, PermissionType.CREATE,
                  PermissionType.EDIT, PermissionType.DELETE,
                  PermissionType.ADMIN],
    username: 'superadmin'
});

// 可以访问所有路由
router.navigate('/admin'); // 允许
router.navigate('/hardware'); // 允许（管理员覆盖）
```

### 示例4：动态权限管理

```javascript
// 注册一个需要特定权限的页面
router.registerRoute(
    '/reports',
    '报表中心',
    () => '<h1>报表中心</h1>',
    {
        requiresAuth: true,
        requiredPermissions: [PermissionType.VIEW, PermissionType.EXPORT],
        allowedRoles: [UserRoles.TEACHER, UserRoles.ADMIN]
    }
);
```

### 示例5：获取可访问路由

```javascript
// 根据当前用户角色显示导航
const accessible = router.getAccessibleRoutes();

accessible.forEach(route => {
    console.log(`${route.meta.icon} ${route.name} - ${route.path}`);
});
```

## 🔒 权限判定流程

```
1. 检查是否需要登录
   ↓
2. 检查用户角色是否在允许列表中
   ↓
3. 检查用户是否拥有所有必需权限
   ↓
4. 检查是否是超级管理员（覆盖所有权限）
   ↓
5. 返回判定结果
```

## 📊 性能优化

- **权限缓存**: 相同用户对同一路由的权限检查会被缓存
- **批量注册**: 使用 `registerRoutes` 批量注册路由比逐个注册更高效
- **路由容器**: 单个容器进行内容切换，减少 DOM 操作

## 🎯 最佳实践

### 1. 组织路由配置

```javascript
// 路由配置放在单独文件中
const AppRoutes = [
    { path: '/', name: '首页', component: Home, options: {} },
    { path: '/about', name: '关于', component: About, options: {} }
];

// 在应用启动时注册
router.registerRoutes(AppRoutes);
```

### 2. 用户状态管理

```javascript
// 登录成功后设置状态
function handleLogin(userData) {
    router.setUserState({
        isAuthenticated: true,
        role: userData.role,
        permissions: userData.permissions,
        username: userData.username
    });
    
    // 跳转到目标页面
    const redirectPath = sessionStorage.getItem('redirectPath') || '/dashboard';
    router.navigate(redirectPath);
}

// 登出时清除状态
function handleLogout() {
    router.setUserState({
        isAuthenticated: false,
        role: UserRoles.GUEST,
        permissions: [],
        username: 'guest'
    });
    router.navigate('/');
}
```

### 3. 权限感知导航

```javascript
// 只显示用户可访问的导航项
function renderNav() {
    const nav = document.getElementById('nav');
    const accessible = router.getAccessibleRoutes();
    
    nav.innerHTML = accessible.map(route => `
        <a href="${route.path}" data-route>
            ${route.meta.icon} ${route.name}
        </a>
    `).join('');
}
```

### 4. 中间件模式

```javascript
// 包装导航方法
const originalNavigate = router.navigate.bind(router);

router.navigate = (path, options) => {
    // 导航前逻辑
    console.log(`导航到: ${path}`);
    
    const result = originalNavigate(path, options);
    
    // 导航后逻辑
    analytics.track('page_view', { path });
    
    return result;
};
```

## 🔍 调试技巧

### 开启日志

```javascript
// 路由系统会自动输出调试信息
// 在浏览器控制台可以看到导航和权限检查日志
```

### 检查用户状态

```javascript
console.log('当前用户:', router.userState);
```

### 检查可访问路由

```javascript
console.log('可访问路由:', router.getAccessibleRoutes());
```

### 测试权限

```javascript
// 手动测试路由权限
const route = router.routes.get('/admin');
const result = router._checkRoutePermission(route);
console.log('权限检查结果:', result);
```

## 🔗 相关资源

- [系统权限优先判定法则](../../permission_priority_rules.py)
- [数据安全法则](../../data_security.py)
- [系统适配管理器](../../system_adaptation_manager.py)

## 📞 技术支持

如有问题，请检查：

1. 浏览器控制台日志
2. 用户状态是否正确设置
3. 路由路径是否正确
4. 权限配置是否合理

---

**版本**: 1.0.0  
**最后更新**: 2026-05-29  
**维护者**: MTSCOS AI Team
