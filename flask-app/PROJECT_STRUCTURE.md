# MTSCOS AI 项目目录规范

## 项目根目录

```
MTSCOS_AI_Project/
├── .project                  # HBuilderX项目配置文件
├── .gitignore               # Git忽略配置
├── README.md                # 项目说明文档
└── flask-app/              # Flask应用主目录
```

## Flask应用目录结构

```
flask-app/
├── app.py                  # ✅ Flask应用主入口
├── requirements.txt        # ✅ Python依赖清单
├── .env                    # ✅ 环境变量配置（数据库、密钥等）
├── .flaskenv               # Flask环境配置
├── config.py               # 应用配置文件

├── app/                    # ✅ 应用核心代码目录
│   ├── __init__.py         # 应用初始化（创建Flask实例）
│   ├── routes/             # ✅ 路由定义
│   │   ├── __init__.py
│   │   ├── admin_api.py    # 管理员API路由
│   │   ├── auth.py         # 认证路由（登录/注册）
│   │   ├── dashboard.py    # 仪表盘路由
│   │   └── exam.py         # 考试系统路由
│   ├── models/             # ✅ 数据模型（SQLAlchemy）
│   │   ├── __init__.py
│   │   ├── user.py         # 用户模型
│   │   ├── exam.py         # 考试模型
│   │   └── ...
│   ├── services/           # ✅ 业务服务层
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── exam_service.py
│   │   └── ...
│   ├── exceptions/         # ✅ 自定义异常体系
│   │   ├── __init__.py     # AppException基类及具体异常
│   │   ├── handler.py      # 统一异常处理中间件
│   │   └── ai_decision_engine.py  # AI决策跳转引擎
│   ├── ai_engines/         # ✅ AI引擎模块
│   │   ├── __init__.py
│   │   └── ...
│   ├── utils/              # ✅ 工具函数
│   │   ├── __init__.py
│   │   ├── decorators.py   # 装饰器（权限验证等）
│   │   └── helpers.py      # 通用辅助函数
│   └── extensions.py       # Flask扩展初始化（SQLAlchemy等）

├── templates/              # ✅ Jinja2模板目录
│   ├── base.html           # 基础模板
│   ├── login.html          # 登录页面
│   ├── register.html       # 注册页面
│   ├── dashboard.html      # 仪表盘页面
│   ├── admin_ui_login.html # 管理端登录页面
│   ├── unified_error.html  # 统一错误页面
│   ├── admin_app/          # 管理后台页面
│   ├── mobile/             # 移动端页面
│   ├── about/              # 关于页面
│   ├── k12/                # K12相关页面
│   ├── contact/            # 联系页面
│   ├── security/           # 安全相关页面
│   └── includes/           # 模板片段（侧边栏、头部等）

├── src/html/               # ✅ 静态资源目录（设计系统）
│   └── assets/
│       ├── css/            # 样式文件
│       │   ├── mtscos-design-system.css  # ✅ 设计系统（Element Plus适配）
│       │   ├── theme.css   # 主题配置
│       │   ├── dashboard.css
│       │   ├── style.css
│       │   ├── preloader.css
│       │   └── page_styles/ # 页面特定样式
│       ├── js/             # JavaScript文件
│       │   ├── admin_app.js
│       │   ├── theme-manager.js
│       │   ├── chart.umd.min.js
│       │   └── ...
│       ├── images/         # 图片资源
│       │   ├── logo.svg
│       │   └── mtscos_logo.svg
│       ├── font-awesome/   # Font Awesome图标库（本地）
│       │   ├── css/
│       │   │   └── all.min.css
│       │   ├── js/
│       │   │   └── all.min.js
│       │   └── webfonts/
│       ├── audio/          # 音频资源
│       └── admin_ui.css    # ✅ 管理端UI样式（Element Plus适配）

├── static/                 # ✅ Flask静态文件目录
│   ├── css/
│   ├── js/
│   ├── images/
│   └── favicon.ico

├── scripts/                # ✅ 辅助脚本
│   ├── generate_adult_questions.py
│   └── ...

├── tests/                  # ✅ 测试目录
│   ├── __init__.py
│   ├── test_auth.py
│   └── ...

├── backups/                # 备份目录（自动生成）
└── __pycache__/            # Python缓存（自动生成）
```

## 目录职责说明

| 目录 | 职责 | 状态 |
|------|------|------|
| `app/` | 核心应用代码，包含路由、模型、服务、异常处理 | ✅ 规范 |
| `templates/` | Jinja2模板文件，所有页面HTML | ✅ 规范 |
| `src/html/assets/` | 设计系统和静态资源，统一使用Element Plus变量 | ✅ 规范 |
| `static/` | Flask默认静态文件目录 | ✅ 规范 |
| `scripts/` | 辅助脚本（数据生成、迁移等） | ✅ 规范 |
| `tests/` | 单元测试和集成测试 | ✅ 规范 |
| `backups/` | 自动备份文件，不纳入版本控制 | ✅ 规范 |

## 设计系统规范

### 颜色变量（Element Plus适配）

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

## HBuilderX配置说明

### 打开项目

1. 打开HBuilderX
2. 文件 → 打开目录 → 选择 `MTSCOS_AI_Project` 目录

### 运行项目

1. 确保安装Python依赖：`pip install -r flask-app/requirements.txt`
2. 在HBuilderX中右键 `flask-app/app.py` → 运行
3. 访问：`http://localhost:8888`

### 代码格式化

- 缩进：4个空格
- 编码：UTF-8
- 行尾：LF

## 新增文件规范

### 新增路由

1. 在 `app/routes/` 目录下创建新文件
2. 在 `app/routes/__init__.py` 中注册蓝图

### 新增模板

1. 在 `templates/` 目录下创建新HTML文件
2. 继承 `base.html` 或相关基础模板
3. 使用设计系统CSS变量，禁止硬编码颜色

### 新增样式

1. 在 `src/html/assets/css/` 目录下创建新CSS文件
2. 使用设计系统变量，遵循Element Plus规范

## Git忽略规则

```
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

1. **禁止硬编码颜色**：所有颜色必须使用设计系统CSS变量
2. **禁止移动目录**：保持现有目录结构不变
3. **统一设计系统**：所有页面必须引入 `mtscos-design-system.css`
4. **API规范**：后端API使用统一异常处理，返回标准JSON格式
5. **安全规范**：敏感信息（密钥、密码等）必须通过环境变量配置