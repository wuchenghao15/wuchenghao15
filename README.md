# MTSCOS AI 项目

## 项目简介

MTSCOS (Multi-tenant System with Cloud and On-premises Support) 是一个多租户系统，支持云端和本地部署，集成了 AI 功能、规则管理、权限控制和路由管理等核心功能。

## 主要功能

- **AI 适配**：集成 AI 功能，支持服务器性能分析、负载预测、异常检测等
- **规则适配**：支持服务器注册、健康、资源使用、安全和性能规则的检查和管理
- **权限适配**：支持不同用户角色的权限管理，包括服务器访问、规则访问、权限访问和 AI 访问
- **路由适配**：支持路由的管理、权限检查和注册
- **Git 集成**：支持 Git 仓库的管理和系统版本记录
- **HTTPS 支持**：使用 HTTPS 协议，确保通信安全

## 技术栈

- **后端**：Python, Flask
- **数据库**：SQLite
- **AI**：自定义 AI 模块
- **网络**：HTTPS

## 项目结构

```
MTSCOS_AI_Project/
├── flask-app/             # 主应用目录
│   ├── app/               # 应用代码
│   │   ├── ai/            # AI 相关模块
│   │   ├── api/           # API 路由
│   │   ├── services/      # 服务模块
│   │   ├── utils/         # 工具模块
│   │   └── __init__.py    # 应用初始化
│   ├── templates/         # 模板文件
│   ├── static/            # 静态文件
│   ├── start_flask.py     # Flask 启动脚本
│   ├── start_server.py    # 服务器启动脚本
│   └── test_*.py          # 测试文件
├── .gitignore             # Git 忽略文件
└── README.md              # 项目说明
```

## 安装和运行

### 安装依赖

```bash
# 进入项目目录
cd MTSCOS_AI_Project

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 运行服务器

```bash
# 进入 flask-app 目录
cd flask-app

# 运行服务器
python start_server.py
```

服务器将在 `https://0.0.0.0:8443` 上运行。

## 测试

```bash
# 运行测试
python test_optimized_system.py
```

## 许可证

MIT
