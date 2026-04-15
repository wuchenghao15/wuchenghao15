# HardwareKey监控系统集成指南

## 概述

HardwareKey监控系统为Web应用提供完整的HardwareKey USB设备插拔状态监控功能。系统能够智能区分HardwareKey登录用户和密码登录用户，只对HardwareKey用户进行安全监控。

## 核心功能

### 🔍 实时监控

- 通过WebSocket连接实时检测HardwareKey设备状态
- 自动重连机制确保服务持续可用
- 支持多页面同时监控

### 👤 智能识别

- 自动识别用户登录类型（HardwareKey登录 vs 密码登录）
- 只对HardwareKey登录用户启用监控
- 密码登录用户不受HardwareKey监控影响

### ⚠️ 安全响应

- HardwareKey被拔出时立即显示警告对话框
- 自动清除登录状态和用户信息
- 详细记录操作日志
- 强制跳转到首页

### 📊 状态显示

- 页面右上角显示HardwareKey连接状态指示器
- 实时更新设备状态信息
- 支持键盘快捷键查看详细状态

## 快速集成

### 1. 文件结构

确保以下文件位于正确的目录中：

```
/assets/
├── css/
│   └── hardwareKey-monitor.css          # HardwareKey监控样式
└── js/
    ├── login-state-manager.js     # 登录状态管理
    ├── hardwareKey-monitor.js          # HardwareKey监控核心
    ├── hardwareKey-removal-handler.js  # 拔出处理机制
    └── hardwareKey-integration.js       # 集成脚本（主要文件）
```

### 2. 页面集成

在需要监控的HTML页面的 `<head>` 标签中添加：

```html
<!-- HardwareKey集成脚本 - 只需要引入这一个文件 -->
<script src="/assets/js/hardwareKey-integration.js"></script>
```

### 3. 服务器要求

确保HardwareKey WebSocket服务器正在运行：

- 默认地址：`ws://localhost:8084`
- HTTP服务器：`http://localhost:8083`

## 详细配置

### 排除页面

某些页面不需要HardwareKey监控，可以在 `hardwareKey-integration.js` 中配置：

```javascript
const VIKEY_CONFIG = {
    excludedPages: [
        '/login.html',
        '/register.html',
        '/404.html',
        '/403.html'
    ]
};
```

### 自定义事件监听

```javascript
// 监听HardwareKey状态变化
window.addEventListener('hardwareKeyStatusChange', function(event) {
    console.log('HardwareKey状态变化:', event.detail);
    // 自定义处理逻辑
});

// 监听认证状态变化
window.addEventListener('authChange', function(event) {
    console.log('认证状态变化:', event.detail);
    // 自定义处理逻辑
});

// 监听会话过期
window.addEventListener('sessionExpired', function(event) {
    console.log('会话过期:', event.detail);
    // 自定义处理逻辑
});
```

### 登录状态管理

在用户登录时设置登录状态：

```javascript
// HardwareKey登录
if (window.loginStateManager) {
    window.loginStateManager.setAuthState('hardwareKey', userId, {
        username: '用户名',
        deviceId: 'HardwareKey设备ID',
        loginTime: new Date().toISOString()
    });
}

// 密码登录
if (window.loginStateManager) {
    window.loginStateManager.setAuthState('password', userId, {
        username: '用户名',
        loginTime: new Date().toISOString()
    });
}
```

## 用户交互

### 键盘快捷键

- `Ctrl + Shift + V`：显示HardwareKey状态对话框
- `Ctrl + Shift + L`：显示登录状态对话框
- `Ctrl + 右键`：显示HardwareKey上下文菜单

### 状态指示器

- 🔑 绿色：HardwareKey已连接
- ⚠️ 橙色：HardwareKey未连接（仅HardwareKey登录用户）
- 🔴 红色：WebSocket连接断开

### 警告对话框

当HardwareKey被拔出时，系统会：

1. 显示警告对话框（包含倒计时）
2. 播放提示音（可选）
3. 记录操作日志
4. 清除登录状态
5. 强制跳转到首页

## 安全特性

### 数据保护

- 自动清除敏感登录信息
- 删除本地存储的认证数据
- 终止活跃会话

### 日志记录

- 详细记录所有HardwareKey操作
- 记录状态变化时间戳
- 支持服务器和本地双重日志

### 防篡改

- 监控页面可见性变化
- 检测开发者工具打开
- 防止恶意脚本注入

## 故障排除

### 常见问题

#### 1. HardwareKey监控未加载

**症状**：页面没有显示HardwareKey状态指示器
**解决方案**：

- 检查文件路径是否正确
- 确保通过HTTP服务器访问页面
- 查看浏览器控制台错误信息

#### 2. WebSocket连接失败

**症状**：状态指示器显示红色
**解决方案**：

- 确认HardwareKey WebSocket服务器正在运行
- 检查防火墙设置
- 验证端口8084是否可用

#### 3. 登录状态不正确

**症状**：HardwareKey拔出时没有触发警告
**解决方案**：

- 确认正确设置了登录状态
- 检查登录类型是否为'hardwareKey'
- 验证用户ID是否有效

### 调试模式

启用详细日志输出：

```javascript
// 在浏览器控制台中执行
localStorage.setItem('hardwareKey_debug', 'true');
```

## 性能优化

### 延迟加载

系统采用延迟加载策略：

- 只在需要时加载组件
- 智能重试机制
- 资源缓存优化

### 内存管理

- 自动清理过期数据
- 优化事件监听器
- 减少DOM操作频率

## 浏览器兼容性

### 支持的浏览器

- Chrome 60+
- Firefox 55+
- Safari 11+
- Edge 79+

### 所需功能

- WebSocket API
- LocalStorage
- CustomEvent
- ES6 Classes

## 示例代码

### 完整页面示例

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的应用</title>
    
    <!-- HardwareKey集成脚本 -->
    <script src="/assets/js/hardwareKey-integration.js"></script>
    
    <!-- 自定义样式 -->
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }
        
        .content {
            max-width: 1200px;
            margin: 0 auto;
        }
    </style>
</head>
<body>
    <div class="content">
        <h1>欢迎来到我的应用</h1>
        <p>这是一个受HardwareKey保护的页面。</p>
        
        <!-- 页面内容 -->
        <div id="app">
            <!-- 应用内容 -->
        </div>
    </div>
    
    <script>
        // 页面加载完成后的初始化
        document.addEventListener('DOMContentLoaded', function() {
            // 自定义HardwareKey状态变化处理
            window.addEventListener('hardwareKeyStatusChange', function(event) {
                console.log('HardwareKey状态:', event.detail);
                
                // 可以在这里添加自定义UI更新逻辑
                if (!event.detail.isHardwareKeyConnected) {
                    console.warn('HardwareKey设备已断开连接');
                }
            });
            
            // 自定义认证状态变化处理
            window.addEventListener('authChange', function(event) {
                console.log('认证状态:', event.detail);
                
                if (!event.detail.isValid) {
                    console.log('用户已登出');
                }
            });
        });
    </script>
</body>
</html>
```

## 部署建议

### 生产环境配置

1. 使用HTTPS协议
2. 配置WebSocket安全连接（wss://）
3. 设置适当的CORS策略
4. 启用日志记录和监控

### 安全建议

1. 定期更新HardwareKey驱动程序
2. 监控异常拔出事件
3. 实施多因素认证
4. 定期审查访问日志

## 技术支持

如需技术支持或报告问题，请联系开发团队。

---

**注意**：本系统需要配合HardwareKey硬件设备和相应的WebSocket服务器使用。在部署前请确保所有依赖组件都已正确配置。
