# MTSCOS AI 项目 - 数据容器化方案

## 项目简介

本项目实现了一个基于Docker的数据容器化方案，用于管理MTSCOS AI项目的数据，确保数据安全和保真性。

## 系统架构

1. **主数据库服务**：PostgreSQL主数据库，存储核心业务数据
2. **备份数据库服务**：PostgreSQL备用数据库，提供数据冗余
3. **应用服务**：Flask应用，处理业务逻辑
4. **备份服务**：定期备份数据库数据到本地文件系统

## 目录结构

```
MTSCOS_AI_Project/
├── Dockerfile              # 应用服务Dockerfile
├── docker-compose.yml      # Docker Compose配置文件
├── .env                    # 环境变量配置
├── init.sql                # 数据库初始化脚本
├── backup-script.sh        # 数据库备份脚本
├── requirements.txt        # Python依赖列表
├── README.md               # 项目说明文档
└── flask-app/              # 应用代码目录
```

## 环境要求

1. Docker 20.10+  
2. Docker Compose 1.29+  
3. Python 3.10+ (用于本地开发)

## 快速开始

### 1. 安装Docker和Docker Compose

请参考官方文档安装Docker和Docker Compose：
- [Docker安装](https://docs.docker.com/get-docker/)
- [Docker Compose安装](https://docs.docker.com/compose/install/)

### 2. 配置环境变量

复制并修改.env.example文件（如果存在），或直接编辑.env文件：

```bash
# 数据库配置
DB_NAME=mtscos_db
DB_USER=mtscos_user
DB_PASSWORD=SecurePassword123!
DB_HOST=db-primary
DB_PORT=5432

# Flask配置
SECRET_KEY=SuperSecretKeyForMTSCOSApplication

# 备份配置
BACKUP_DIR=/backups
BACKUP_INTERVAL=86400

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log
```

### 3. 启动服务

在项目根目录下执行：

```bash
docker-compose up -d
```

这将启动所有服务：
- 主数据库服务：5432端口
- 备份数据库服务：5433端口
- 应用服务：8888端口

### 4. 访问应用

应用将运行在 http://localhost:8888

### 5. 管理服务

- 查看服务状态：`docker-compose ps`
- 查看日志：`docker-compose logs -f`
- 停止服务：`docker-compose down`
- 重启服务：`docker-compose restart`

## 数据安全与保真性

### 1. 密码加密

- 使用PBKDF2-SHA256算法加密密码
- 每个密码使用随机生成的16字节盐值
- 迭代次数：100,000次

### 2. 数据备份机制

- **双数据库备份**：主数据库和备用数据库实时同步
- **定期文件备份**：每天自动备份数据库到文件系统
- **备份保留策略**：保留最近7天的备份文件
- **备份日志**：记录所有备份操作，便于审计

### 3. 访问控制

- 数据库用户权限最小化
- 应用使用连接池管理数据库连接
- 所有敏感操作都有日志记录

### 4. 数据恢复机制

- 支持从备份文件恢复数据库
- 支持从备用数据库恢复主数据库
- 提供数据恢复脚本（后续版本）

## 数据库表结构

### 用户表 (user)
- 存储系统用户信息
- 包含用户名、邮箱、加密密码、角色等字段

### 用户备份表 (user_backup)
- 用户数据的冗余备份
- 与用户表结构相同

### 子服务器表 (servers)
- 存储子服务器信息
- 包含名称、IP地址、端口、状态等字段

### 角色表 (roles)
- 存储系统角色信息

### 权限表 (permissions)
- 存储系统权限信息

### 角色权限关联表 (role_permissions)
- 关联角色和权限

### 用户角色关联表 (user_roles)
- 关联用户和角色

### 备份日志表 (backup_logs)
- 记录备份操作日志

### 数据迁移日志表 (migration_logs)
- 记录数据迁移操作日志

## 应用配置

### 数据库连接

应用使用环境变量配置数据库连接：

```python
# 数据库连接配置
DB_HOST = os.environ.get('DB_HOST', 'db-primary')
DB_PORT = os.environ.get('DB_PORT', 5432)
DB_NAME = os.environ.get('DB_NAME', 'mtscos_db')
DB_USER = os.environ.get('DB_USER', 'mtscos_user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'SecurePassword123!')
```

### 连接池配置

- 最小连接数：1
- 最大连接数：10
- 自动回收空闲连接

## 开发指南

### 本地开发

1. 安装Python依赖：

```bash
pip install -r requirements.txt
```

2. 配置环境变量：

```bash
export FLASK_APP=flask-app/app.py
export FLASK_ENV=development
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=mtscos_db
export DB_USER=mtscos_user
export DB_PASSWORD=SecurePassword123!
export SECRET_KEY=SuperSecretKeyForMTSCOSApplication
```

3. 启动应用：

```bash
python -m flask run --host=0.0.0.0 --port=8888
```

### 测试

运行测试脚本：

```bash
python flask-app/test_password.py
```

更新用户信息：

```bash
python flask-app/update_users.py
```

## 部署建议

1. **生产环境**：
   - 使用独立的数据库服务器
   - 配置SSL加密连接
   - 定期备份到外部存储
   - 监控数据库性能和状态

2. **开发环境**：
   - 使用Docker Compose快速部署
   - 开启调试模式
   - 定期清理测试数据

## 安全最佳实践

1. **密码管理**：
   - 使用强密码
   - 定期更换密码
   - 启用多因素认证（后续版本）

2. **网络安全**：
   - 配置防火墙规则
   - 限制数据库访问IP
   - 使用VPN连接数据库（生产环境）

3. **日志管理**：
   - 定期备份日志
   - 监控异常日志
   - 配置日志轮转

## 故障排除

### 1. 数据库连接失败

- 检查数据库服务是否运行：`docker-compose ps`
- 检查环境变量配置：`.env`文件
- 检查数据库日志：`docker-compose logs db-primary`

### 2. 应用启动失败

- 检查应用日志：`docker-compose logs app`
- 检查依赖是否安装：`requirements.txt`
- 检查端口是否被占用：`lsof -i :8888`

### 3. 备份失败

- 检查备份服务日志：`docker-compose logs backup-service`
- 检查备份目录权限：`ls -la /backups`
- 检查数据库连接配置

## 版本历史

- v1.0.0 (2026-03-10)
  - 初始版本
  - 实现数据容器化方案
  - 支持PostgreSQL数据库
  - 实现数据备份机制
  - 实现密码加密功能

## 贡献指南

1. Fork本项目
2. 创建功能分支
3. 提交代码
4. 发起Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系项目团队。
