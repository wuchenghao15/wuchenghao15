# MTSCOS AI Project

## 项目概述

MTSCOS AI Project 是一个基于Flask的AI应用框架，提供了AI实例管理、监控、学习等功能。

## 功能特性

- AI实例管理
- 自动错误监控和修复
- AI自我学习和优化
- 用户认证和授权
- 基于角色的访问控制
- 完善的日志记录

## 技术栈

- Python 3.8+
- Flask 2.0+
- SQLite
- HTML/CSS/JavaScript

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
python app.py
```

应用将在 http://localhost:8888 启动。

## 项目结构

```
flask-app/
├── app.py              # 应用入口
├── app/                # 应用包
│   ├── __init__.py     # 应用初始化
│   ├── config.py       # 配置文件
│   ├── models/         # 数据模型
│   ├── views/          # 视图函数
│   ├── utils/          # 工具函数
│   └── ai/             # AI相关功能
├── templates/          # HTML模板
├── static/             # 静态资源
└── requirements.txt    # 依赖列表
```

## API文档

### 认证API

- `POST /auth/login` - 用户登录
- `GET /auth/logout` - 用户登出
- `POST /auth/register` - 用户注册

### AI API

- `GET /ai/instances` - 获取AI实例列表
- `POST /ai/create_instance` - 创建AI实例
- `GET /ai/delete_instance/<instance_id>` - 删除AI实例
- `GET /ai/bind_instance/<instance_id>/<user_id>` - 绑定AI实例到用户

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

MIT
