# MTSCOS AI 项目结构文档

## 项目概述
MTSCOS AI 是一个智能管理系统，包含前端界面、后端服务和AI功能模块。本文档描述了项目的目录结构和文件组织方式，以便于团队成员理解和维护项目。

## 目录结构

```
MTSCOS_AI_Project/
├── frontend/                  # 前端文件
│   ├── assets/                # 静态资源
│   │   ├── css/               # CSS样式文件
│   │   │   ├── common_styles/  # 通用样式
│   │   │   ├── component_styles/ # 组件样式
│   │   │   ├── page_styles/    # 页面样式
│   │   │   └── third_party/    # 第三方样式
│   │   ├── js/                # JavaScript文件
│   │   └── images/            # 图片资源
│   ├── components/            # 前端组件
│   └── pages/                 # 前端页面
├── backend/                   # 后端服务
│   ├── api/                   # API接口
│   ├── models/                # 数据模型
│   └── services/              # 后端服务
├── flask-app/                 # Flask应用
│   ├── app/                   # 应用核心
│   └── docs/                  # 文档
├── data/                      # 数据文件
├── docs/                      # 项目文档
│   ├── architecture/          # 架构文档
│   ├── changelogs/            # 更新日志
│   ├── config/                # 配置文档
│   └── guides/                # 使用指南
├── scripts/                   # 脚本文件
├── .env                       # 环境变量
├── .env.example               # 环境变量示例
├── .gitignore                 # Git忽略文件
├── README.md                  # 项目说明
└── VERSION                    # 版本信息
```

## 目录说明

### frontend/ 前端文件
- **assets/css/**: 存放所有CSS样式文件
  - **common_styles/**: 通用样式，如字体、主题等
  - **component_styles/**: 组件样式
  - **page_styles/**: 页面特定样式
  - **third_party/**: 第三方CSS库
- **assets/js/**: 存放所有JavaScript文件
  - 按功能分类，如登录、监控、设计器等
- **assets/images/**: 图片资源
- **components/**: 前端组件
- **pages/**: 前端页面文件

### backend/ 后端服务
- **api/**: API接口定义
- **models/**: 数据模型
- **services/**: 后端服务逻辑

### flask-app/ Flask应用
- **app/**: Flask应用核心代码
- **docs/**: 应用文档

### data/ 数据文件
- 存放数据库初始化脚本、配置文件等

### docs/ 项目文档
- **architecture/**: 架构设计文档
- **changelogs/**: 版本更新日志
- **config/**: 配置相关文档
- **guides/**: 使用指南和部署文档

## 核心文件说明

### 前端核心文件
- **frontend/pages/index.html**: 登录页面
- **frontend/pages/system_monitor.html**: 系统监控页面
- **frontend/pages/designer_ai.html**: 前端设计师AI页面
- **frontend/assets/js/login-script.js**: 登录功能脚本
- **frontend/assets/js/system_monitor.js**: 系统监控脚本
- **frontend/assets/js/designer_ai.js**: 设计师AI脚本

### 后端核心文件
- **flask-app/app.py**: Flask应用入口
- **flask-app/ai_service.py**: AI服务

### 配置文件
- **.env**: 环境变量配置
- **docker-compose.yml**: Docker配置

## 开发指南

### 前端开发
1. 所有前端文件放在 `frontend/` 目录中
2. 页面文件放在 `frontend/pages/`
3. 样式文件放在 `frontend/assets/css/` 相应子目录
4. JavaScript文件放在 `frontend/assets/js/`

### 后端开发
1. 后端服务放在 `backend/` 目录
2. Flask应用放在 `flask-app/` 目录

### 文档管理
1. 架构文档放在 `docs/architecture/`
2. 更新日志放在 `docs/changelogs/`
3. 配置文档放在 `docs/config/`
4. 使用指南放在 `docs/guides/`

## 版本控制
- 使用Git进行版本控制
- 遵循GitFlow工作流
- 每次更新后更新 `VERSION` 文件

## 部署说明
- 参考 `docs/guides/DEPLOYMENT_GUIDE.md`
- 可使用Docker容器化部署

## 维护指南
- 定期更新依赖
- 保持代码结构清晰
- 遵循命名规范
- 及时更新文档

## 总结
本项目采用模块化、分层的目录结构，便于团队协作和代码维护。前端和后端分离，文档和代码分离，使得项目更加清晰易读。