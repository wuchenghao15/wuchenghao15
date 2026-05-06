# MTSCOS AI Web 应用

MTSCOS AI Web 是一个基于 Flask 框架开发的智能管理系统，提供了多设备登录管理、会话管理、多因素认证等功能。

## 项目结构

```
flask-app/
├── app/                    # 主应用目录
│   ├── ai/                 # AI 相关功能
│   ├── config.py           # 配置文件
│   ├── models/             # 数据模型
│   ├── services/           # 服务层
│   ├── utils/              # 工具类
│   │   ├── db.py           # 数据库管理
│   │   ├── logging.py      # 日志管理
│   │   ├── session_manager.py  # 会话管理
│   │   └── verification.py     # 验证工具
│   └── views/              # 视图层
│       ├── auth.py         # 认证相关路由
│       ├── main.py         # 主页路由
│       ├── session_management.py  # 会话管理路由
│       └── __init__.py     # 蓝图注册
├── templates/              # HTML 模板
├── static/                 # 静态资源
├── venv/                   # Python 虚拟环境
├── app.py                  # 应用入口
├── requirements.txt        # 依赖列表
├── start.sh                # 启动脚本
├── Dockerfile              # Docker 构建文件
├── docker-compose.yml      # Docker Compose 配置
└── README.md               # 项目说明
```

## 功能特性

### 1. 多设备登录管理
- 支持用户在多个设备上同时登录
- 可配置设备数量限制
- 会话实时验证和管理

### 2. 多因素认证
- 密码验证
- 滚码验证
- 唯一码验证
- 防伪码验证
- 数据库 ID 验证
- Vikey 硬件码验证

### 3. 会话管理
- 会话创建、验证和更新
- 会话失效和清理
- 设备限制检查
- 会话列表查看和管理

### 4. 白名单 Token 验证
- 支持基于 Token 的白名单验证
- 可配置白名单 Token

### 5. 智能仪表盘
- 系统监控
- 用户管理
- 权限管理

## 运行环境要求

- Python 3.9+
- Flask 2.0+
- SQLite 3
- 支持 Docker (可选，用于容器化部署)

## 安装和运行

### 方法一：使用启动脚本

1. 确保已安装 Python 3.9+。
2. 运行启动脚本：

```bash
./start.sh
```

3. 访问 http://localhost:8080

### 方法二：手动安装和运行

1. 确保已安装 Python 3.9+。
2. 创建并激活虚拟环境：

```bash
python3 -m venv venv
source venv/bin/activate
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

4. 运行应用：

```bash
python app.py
```

5. 访问 http://localhost:8080

## Docker 部署

### 方法一：使用 Docker Build

1. 确保已安装 Docker。
2. 构建 Docker 镜像：

```bash
docker build -t mtscos-ai-web .
```

3. 运行 Docker 容器：

```bash
docker run -p 8080:8080 --name mtscos-ai-web -d mtscos-ai-web
```

### 方法二：使用 Docker Compose

1. 确保已安装 Docker 和 Docker Compose。
2. 运行：

```bash
docker-compose up -d
```

3. 访问 http://localhost:8080

## 主要文件说明

- `app.py`：应用入口文件，创建 Flask 应用实例。
- `app/views/auth.py`：处理用户认证相关路由，包括登录、登出等。
- `app/views/session_management.py`：处理会话管理相关路由。
- `app/utils/session_manager.py`：会话管理核心逻辑。
- `app/utils/verification.py`：多因素认证核心逻辑。
- `templates/session_management.html`：会话管理页面。

## 配置说明

### 环境变量

- `FLASK_ENV`：运行环境，可选值为 `development`、`testing`、`production`。
- `FLASK_APP`：应用入口文件，默认值为 `app.py`。
- `SECRET_KEY`：用于加密会话数据的密钥。

### 数据库配置

应用使用 SQLite 数据库，数据库文件为 `mtscos.db`。

## 注意事项

1. 首次运行时，系统会自动创建必要的数据库表。
2. 建议在生产环境中使用强密码和安全的 SECRET_KEY。
3. 定期备份数据库文件 `mtscos.db`。
4. 如需修改端口，可在 `app.py` 中修改 `port` 变量。

## 开发说明

### 代码结构

- 采用蓝图架构，便于模块化开发和扩展。
- 视图层（views）负责处理 HTTP 请求和响应。
- 服务层（services）包含业务逻辑。
- 工具类（utils）提供通用功能支持。

### 添加新功能

1. 在 `app/views/` 目录下创建新的视图文件。
2. 在 `app/views/__init__.py` 中注册蓝图。
3. 在 `templates/` 目录下创建相应的 HTML 模板。
4. 在 `app/utils/` 目录下添加必要的工具类。

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系项目维护人员。
