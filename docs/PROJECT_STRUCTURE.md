# MTSCOS AI 项目目录规范

> 版本: v17.22.0 | 更新日期: 2026-07-26

## 项目根目录

```text
MTSCOS-AI-Project/
├── .project                  # HBuilderX 项目配置文件
├── .gitignore                # Git 忽略配置
├── README.md                 # 项目说明文档
├── CHANGELOG.md              # 变更日志
├── SECURITY.md               # 安全策略文档
├── CONTRIBUTING.md           # 贡献指南
├── CODE_OF_CONDUCT.md        # 行为准则
├── PROJECT_STRUCTURE.md      # 项目结构文档
├── ARCHITECTURE_REPORT.md    # 架构报告
├── SYSTEM_DOC.md             # 系统说明书
└── flask-app/                # Flask 应用主目录
```

## Flask 应用目录结构

```text
flask-app/
├── server_real_db.py                  # ✅ 生产入口（识别 MTS 架构+启动分片库）
├── server_preview.py                  # 🧪 预览入口
├── app.py                             # 历史兼容入口
├── requirements.txt                   # ✅ Python 依赖清单
├── .env                               # ✅ 环境变量配置（数据库、密钥等）
├── .flaskenv                          # Flask 环境配置
├── config.py                          # 应用配置文件
├── security_vulnerability_service.py  # ✅ 安全漏洞管理服务
├── code_security_scanner.py           # ✅ 代码安全扫描器
├── run_security_scan.py               # ✅ 安全扫描运行脚本
├── upload_vuln_fixes.py               # ✅ 漏洞修复上传脚本
├── curriculum_service.py              # ✅ 教学大纲管理服务
├── question_bank_sync_service.py       # ✅ 题库与大纲同步服务
├── learning_curriculum_service.py      # ✅ 学习与大纲追踪服务

├── app/                               # ✅ 应用核心代码目录
│   ├── __init__.py                    # 应用初始化（创建 Flask 实例）
│   ├── routes/                        # ✅ 路由定义
│   │   ├── __init__.py
│   │   ├── admin_api.py               # 管理员 API 路由
│   │   ├── auth.py                    # 认证路由（登录/注册）
│   │   ├── dashboard.py               # 仪表盘路由
│   │   └── exam.py                    # 考试系统路由
│   ├── api/                           # ✅ API 蓝图模块
│   │   ├── education_api.py           # 教育综合 API（大纲/同步/学习）
│   │   ├── security_vuln_api.py       # 安全漏洞管理 API
│   │   ├── adult_api.py               # 成人教育 API
│   │   └── k12_api.py                 # K12 教育 API
│   ├── models/                        # ✅ 数据模型（SQLAlchemy）
│   │   ├── __init__.py
│   │   ├── user.py                    # 用户模型
│   │   ├── exam.py                    # 考试模型
│   │   └── ...
│   ├── services/                      # ✅ 业务服务层
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── exam_service.py
│   │   └── ...
│   ├── exceptions/                    # ✅ 自定义异常体系
│   │   ├── __init__.py                # AppException 基类及具体异常
│   │   ├── handler.py                 # 统一异常处理中间件
│   │   └── ai_decision_engine.py      # AI 决策跳转引擎
│   ├── ai_engines/                    # ✅ AI 引擎模块（550+ 员工/引擎、47 Agent）
│   │   ├── __init__.py
│   │   └── ...
│   ├── utils/                         # ✅ 工具函数
│   │   ├── __init__.py
│   │   ├── decorators.py              # 装饰器（权限验证等）
│   │   └── helpers.py                 # 通用辅助函数
│   └── extensions.py                  # Flask 扩展初始化（SQLAlchemy 等）

├── templates/                         # ✅ Jinja2 模板目录
│   ├── base.html                      # 基础模板
│   ├── login.html                     # 登录页面
│   ├── register.html                  # 注册页面
│   ├── dashboard.html                 # 仪表盘页面
│   ├── admin_ui_login.html            # 管理端登录页面
│   ├── unified_error.html             # 统一错误页面
│   ├── admin_app/                     # 管理后台页面
│   │   ├── education_management.html  # ✅ 教育综合管理页面
│   │   └── ...
│   ├── mobile/                        # 移动端页面
│   ├── about/                         # 关于页面
│   ├── k12/                           # K12 相关页面
│   ├── contact/                       # 联系页面
│   ├── security/                      # 安全相关页面
│   └── includes/                     # 模板片段（侧边栏、头部等）

├── src/html/                          # ✅ 静态资源目录（设计系统）
│   └── assets/
│       ├── css/                       # 样式文件
│       │   ├── mtscos-design-system.css  # ✅ 设计系统（Element Plus 适配）
│       │   ├── theme.css              # 主题配置
│       │   ├── dashboard.css
│       │   ├── style.css
│       │   ├── preloader.css
│       │   └── page_styles/           # 页面特定样式
│       ├── js/                        # JavaScript 文件
│       │   ├── admin_app.js
│       │   ├── theme-manager.js
│       │   ├── chart.umd.min.js
│       │   └── ...
│       ├── images/                    # 图片资源
│       │   ├── logo.svg
│       │   └── mtscos_logo.svg
│       ├── font-awesome/             # Font Awesome 图标库（本地）
│       │   ├── css/
│       │   │   └── all.min.css
│       │   ├── js/
│       │   │   └── all.min.js
│       │   └── webfonts/
│       ├── audio/                     # 音频资源
│       └── admin_ui.css               # ✅ 管理端 UI 样式（Element Plus 适配）

├── static/                            # ✅ Flask 静态文件目录
│   ├── css/
│   ├── js/
│   ├── images/
│   └── favicon.ico

├── scripts/                           # ✅ 辅助脚本
│   ├── generate_adult_questions.py
│   └── ...

├── tests/                             # ✅ 测试目录
│   ├── __init__.py
│   ├── test_auth.py
│   └── ...

├── backups/                           # 备份目录（自动生成）
└── __pycache__/                       # Python 缓存（自动生成）
```

## 目录职责说明

| 目录 | 职责 | 状态 |
|------|------|------|
| `app/` | 核心应用代码，包含路由、模型、服务、异常处理 | ✅ 规范 |
| `templates/` | Jinja2 模板文件，所有页面 HTML | ✅ 规范 |
| `src/html/assets/` | 设计系统和静态资源，统一使用 Element Plus 变量 | ✅ 规范 |
| `static/` | Flask 默认静态文件目录 | ✅ 规范 |
| `scripts/` | 辅助脚本（数据生成、迁移等） | ✅ 规范 |
| `tests/` | 单元测试和集成测试 | ✅ 规范 |
| `backups/` | 自动备份文件，不纳入版本控制 | ✅ 规范 |

## 设计系统规范

### 颜色变量（Element Plus 适配）

```css
:root {
    --el-color-primary: #409eff;      /* 主色调 */
    --el-color-success: #67c23a;      /* 成功色 */
    --el-color-warning: #e6a23c;      /* 警告色 */
    --el-color-danger: #f56c6c;       /* 危险色 */
    --el-color-info: #909399;         /* 信息色 */
}
```

### 字体规范

- 字体家族：`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- 基础字号：14px (`--el-font-size-base`)

### 间距规范

- 基准单位：8px
- 使用变量：`--spacing-1` ~ `--spacing-32`

## HBuilderX 配置说明

### 打开项目

1. 打开 HBuilderX
2. 文件 → 打开目录 → 选择 `MTSCOS-AI-Project` 目录

### 运行项目

1. 确保安装 Python 依赖：`pip install -r flask-app/requirements.txt`
2. 在 HBuilderX 中右键 `flask-app/server_real_db.py` → 运行
3. 访问：`http://localhost:8888`

### 代码格式化

- 缩进：4 个空格
- 编码：UTF-8
- 行尾：LF

## 新增文件规范

### 新增路由

1. 在 `app/routes/` 目录下创建新文件
2. 在 `app/routes/__init__.py` 中注册蓝图

### 新增模板

1. 在 `templates/` 目录下创建新 HTML 文件
2. 继承 `base.html` 或相关基础模板
3. 使用设计系统 CSS 变量，禁止硬编码颜色

### 新增样式

1. 在 `src/html/assets/css/` 目录下创建新 CSS 文件
2. 使用设计系统变量，遵循 Element Plus 规范

## Git 忽略规则

```text
# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# 环境变量
.env
.env.local

# 备份
backups/

# 日志
*.log

# 编辑器
.vscode/
.idea/
.DS_Store

# 构建产物
dist/
build/
```

## 注意事项

1. **禁止硬编码颜色**：所有颜色必须使用设计系统 CSS 变量
2. **禁止移动目录**：保持现有目录结构不变
3. **统一设计系统**：所有页面必须引入 `mtscos-design-system.css`
4. **API 规范**：后端 API 使用统一异常处理，返回标准 JSON 格式
5. **安全规范**：敏感信息（密钥、密码等）必须通过环境变量配置
