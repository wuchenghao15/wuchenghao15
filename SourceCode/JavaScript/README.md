# JavaScript 文件文档

本文档统一说明MTSCOS项目中所有JavaScript文件的功能、用途和使用方法。

## 文件结构

```
JavaScript/
├── MyScript/          # 包含各页面的核心功能脚本（加密版）
├── check_links.js     # 链接有效性检查工具
├── decrypt_helper.js  # 解密辅助工具
├── load_footer.js     # 动态加载页脚组件
└── save_connection_string_encrypted.js  # 保存连接字符串（加密）
```

## 核心功能文件说明

### check_links.js

**功能**：链接有效性检查工具，用于检测页面中所有链接的状态。

**主要特性**：
- 自动检测页面中所有链接
- 区分有效和无效链接并高亮显示
- 在控制台和页面上显示检查结果
- 支持跳过锚点和JavaScript链接
- 设置5秒超时机制

**使用方法**：
在浏览器控制台中输入 `checkLinks()` 即可开始检查当前页面的所有链接。

### load_footer.js

**功能**：动态加载页脚组件，确保所有页面使用统一的页脚。

**主要特性**：
- 异步加载footer.html文件
- 自动将页脚内容添加到页面底部
- 支持页脚中的脚本加载
- 页面加载完成后自动执行
- 提供模块化导出功能

**使用方法**：
以module方式引入该脚本：
```html
<script src="../JavaScript/load_footer.js" type="module"></script>
```

### decrypt_helper.js

**功能**：提供解密功能，用于解密加密的JavaScript文件。

**使用方法**：
由其他脚本自动调用，通常不需要手动使用。

### save_connection_string_encrypted.js

**功能**：加密保存连接字符串，保护敏感数据。

**使用方法**：
由系统自动调用，通常不需要手动使用。

## MyScript 目录文件说明

MyScript目录包含各个页面的核心功能脚本，这些文件都是加密版本，需要通过decrypt_helper.js进行解密后使用。

### 主要文件：

- **anti_hotlink.js** - 防盗链保护
- **auth.js** - 认证相关功能
- **dashboard.js** - 仪表盘页面功能
- **index.js** - 主页功能
- **password_reset.js** - 密码重置功能
- **register.js** - 注册功能
- **server.js** - 服务器管理功能
- **service_monitor.js** - 服务监控功能
- **session_timeout.js** - 会话超时处理
- **settings.js** - 设置页面功能
- **user_profile.js** - 用户资料管理

## 最佳实践

1. 所有页面统一使用load_footer.js加载页脚
2. 页面脚本应按以下顺序引入：
   - MyScript目录下的功能脚本
   - load_footer.js（使用type="module"）
   - check_links.js

3. 定期使用check_links.js检查页面链接有效性
4. 保护好加密脚本，避免泄露

## 版本信息

- 最后更新：2024-01-18
- 版本：1.1.202401181500