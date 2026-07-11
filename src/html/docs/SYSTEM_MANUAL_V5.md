# MTSCOS AI 智能管理系统 - 系统说明书

## 📋 系统信息

| 项目 | 信息 |
|------|------|
| **系统名称** | MTSCOS AI 智能管理系统 |
| **当前版本** | 5.0.0 |
| **开发代号** | 智能系统优化版 |
| **构建日期** | 2026.06.23 |
| **技术栈** | Python Flask 2.3.0 + SQLite + MongoDB + 原生JavaScript |
| **前端框架** | Tailwind CSS 2.2.19 + Font Awesome 6.4.0 |
| **服务地址** | HTTPS https://0.0.0.0:8443 / HTTP http://0.0.0.0:8888 |

---

## 🚀 版本历史

### 5.0.0 - 智能系统优化版 (2026.06.23)

#### 新增AI员工（5个）
1. **客户端监控员** (`emp_monitor_client_access`)
2. **代码修复员** (`emp_code_repair_ai`)
3. **端口监控员** (`emp_port_monitor_ai`)
4. **行为监控员** (`emp_behavior_monitor_ai`)
5. **系统优化员** (`emp_system_optimizer_ai`)

#### 核心特性
- ✅ 客户端接入实时监控
- ✅ 代码错误自动检测与修复
- ✅ 端口异常监控与自动修复
- ✅ 用户行为记录与异常警报
- ✅ 系统自动优化与功能拓展
- ✅ SSL/TLS加密通信
- ✅ 数据库性能优化
- ✅ 系统版本自动升级

### 4.4.0 - 智能教育大数据版
- 理科公式库（89条公式）
- 大规模题库系统（122500题）
- MongoSQL双数据库同步
- 题库大数据专家AI员工

---

## 👥 AI员工团队

### 1. 客户端监控员
- **员工ID**: `emp_monitor_client_access`
- **类别**: 安全监控
- **效率**: 100%
- **API端点**:
  - `GET /api/monitor/stats` - 监控统计
  - `GET /api/monitor/anomalies` - 异常列表
  - `GET /api/monitor/access` - 接入记录

### 2. 代码修复员
- **员工ID**: `emp_code_repair_ai`
- **类别**: 开发运维
- **效率**: 95%
- **支持文件类型**: .py, .js, .css, .json, .sql, .html, .bak, .tar
- **API端点**:
  - `GET /api/repair/employee` - 员工信息
  - `POST /api/repair/scan` - 扫描错误
  - `POST /api/repair/repair` - 修复文件
  - `GET /api/repair/stats` - 修复统计

### 3. 端口监控员
- **员工ID**: `emp_port_monitor_ai`
- **类别**: 系统运维
- **效率**: 98%
- **监控端口**: 8888, 8443, 5000, 3306, 27017, 6379, 80, 443
- **API端点**:
  - `GET /api/port-monitor/stats` - 端口统计
  - `POST /api/port-monitor/scan` - 扫描端口
  - `POST /api/port-monitor/fix/auto` - 自动修复

### 4. 行为监控员
- **员工ID**: `emp_behavior_monitor_ai`
- **类别**: 安全监控
- **效率**: 97%
- **监控模式**:
  - 登录失败次数过多（5次/5分钟）
  - 请求频率超限（1000次/小时）
  - 批量数据访问（100次/分钟）
  - 敏感操作频繁（10次/10分钟）
  - 异地登录检测
  - 异常时间访问
  - API滥用检测
  - 数据导出频繁
- **API端点**:
  - `GET /api/behavior/stats` - 行为统计
  - `GET /api/behavior/alerts` - 警报列表
  - `POST /api/behavior/log` - 记录行为

### 5. 系统优化员
- **员工ID**: `emp_system_optimizer_ai`
- **类别**: 开发运维
- **效率**: 99%
- **优化能力**:
  - 系统性能优化
  - 数据库优化
  - 安全性优化
  - API性能优化
  - 功能自动拓展
  - 系统版本升级
- **API端点**:
  - `GET /api/optimizer/version` - 当前版本
  - `POST /api/optimizer/version/upgrade` - 升级版本
  - `POST /api/optimizer/optimize` - 自动优化
  - `POST /api/optimizer/features/expand` - 拓展功能

---

## 📊 系统统计

| 项目 | 数量 |
|------|------|
| AI员工总数 | 46个 |
| 新增AI员工 | 5个 |
| 题库数量 | 34个 |
| 题目总数 | 122,500题 |
| 理科公式 | 89条 |
| 数据库表 | 55个 |
| 索引数量 | 122个 |
| 计划新功能 | 15个 |
| 优化项目 | 14个 |

---

## 🗄️ 数据库结构

### 监控相关表
- `client_access_logs` - 客户端接入日志
- `client_anomalies` - 客户端异常记录
- `client_sessions` - 客户端会话记录

### 代码修复相关表
- `code_repair_logs` - 代码修复日志
- `code_errors` - 代码错误记录

### 端口监控相关表
- `port_status` - 端口状态
- `port_fix_logs` - 端口修复日志
- `port_config_params` - 端口配置参数

### 用户行为相关表
- `user_behavior` - 用户行为记录
- `behavior_alerts` - 行为警报
- `behavior_patterns` - 行为监控模式
- `blocked_ips` - 封禁IP列表

### 系统优化相关表
- `system_optimizations` - 系统优化记录
- `feature_expansions` - 功能拓展记录
- `system_performance` - 系统性能指标

### 教育内容表
- `poems` - 古诗词
- `classical_chinese` - 文言文
- `textbook_segments` - 课文选段
- `idioms` - 成语
- `xiehouyu` - 歇后语
- `literature_segments` - 文学选段
- `reading_comprehension` - 阅读理解
- `famous_quotes` - 经典语录
- `science_formulas` - 理科公式

### 系统核心表
- `ai_employees` - AI员工表
- `system_status_log` - 系统状态日志
- `system_config` - 系统配置

---

## 🔧 启动服务

### 启动SSL加密服务（推荐）
```bash
cd "/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app"
python3 app.py --ssl
```

### 启动HTTP服务
```bash
python3 app.py
```

### 指定端口启动
```bash
python3 app.py --port 9000
python3 app.py --ssl --ssl-port 9443
```

---

## 📝 计划中的新功能（P1优先级）

1. **智能数据分析报表** - 基于用户行为数据生成智能分析报表
2. **实时通知推送系统** - 支持邮件、短信、WebSocket实时通知
3. **性能监控仪表盘** - 实时性能监控和可视化仪表盘
4. **缓存优化系统** - 多级缓存策略优化系统响应速度
5. **备份恢复系统** - 自动备份和一键恢复系统
6. **权限细粒度控制** - 基于RBAC的细粒度权限控制
7. **数据加密存储** - 敏感数据加密存储和传输
8. **智能搜索系统** - 全文搜索和智能推荐

## 📝 计划中的新功能（P2优先级）

9. **多语言国际化支持** - 支持中英文切换的多语言系统
10. **API文档自动生成** - 基于代码自动生成API文档
11. **自动化测试框架** - API自动化测试和回归测试框架
12. **日志分析系统** - 集中式日志收集和分析系统
13. **移动端适配** - 响应式设计和移动端优化
14. **数据导入导出** - 支持多种格式的数据导入导出
15. **工作流引擎** - 可配置的业务工作流引擎

---

## 🖥️ 前端页面

### 主要页面
- `index.html` - 系统首页
- `ai-employee-console.html` - **AI员工管理控制台**（5.0.0新增）
- `ai_dashboard.html` - AI仪表盘
- `service_monitor.html` - 服务监控
- `database-manager.html` - 数据库管理
- `settings.html` - 系统设置
- `admin.html` - 管理后台
- `security-management.html` - 安全管理

### AI员工管理控制台功能
- ✅ AI员工列表展示（5个新员工）
- ✅ 实时监控面板
- ✅ 警报中心
- ✅ 系统优化操作
- ✅ 功能拓展展示
- ✅ 自动数据刷新（30秒）

---

## 🔐 安全特性

- 🔒 SSL/TLS加密通信
- 🛡️ SQL注入防护中间件
- 🛡️ XSS防护
- 🛡️ CSRF防护
- 🛡️ CORS保护
- 🛡️ 自动IP封禁系统
- 🛡️ 用户行为异常检测
- 🛡️ 登录失败次数限制
- 🛡️ 请求频率限制

---

## 📈 性能优化

- ⚡ 响应压缩
- ⚡ 数据库查询缓存
- ⚡ 请求限流
- ⚡ 静态资源加载优化
- ⚡ 数据库表分析（ANALYZE）
- ⚡ 索引优化

---

## 📞 技术支持

- **邮箱**: admin@mtscos.com
- **电话**: +86 123 4567 8910
- **文档**: https://docs.mtscos.com
- **GitHub**: https://github.com/wuchenghao15/wuchenghao15

---

## 📜 更新日志

### 2026.06.23 - v5.0.0 智能系统优化版
- 🎉 新增5个AI员工
- 🎉 客户端接入监控系统
- 🎉 代码自动修复系统
- 🎉 端口异常监控修复系统
- 🎉 用户行为记录与异常警报系统
- 🎉 系统自动优化与功能拓展系统
- 🎉 SSL/TLS加密通信
- 🎉 AI员工管理控制台前端
- 🎉 首页布局升级
- 🎉 15个新功能规划

### 2026.06.23 - v4.4.0 智能教育大数据版
- 理科公式库（89条公式）
- 大规模题库系统（122500题）
- MongoSQL双数据库同步
- 题库大数据专家AI员工
