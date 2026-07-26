<div align="center">

# MTSCOS AI

**M**ulti-**T**enant **S**mart **C**onfiguration **O**perating **S**ystem · AI Platform

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)]()
[![Flask](https://img.shields.io/badge/Flask-2.0+-000000?style=for-the-badge&logo=flask&logoColor=white)]()
[![SQLite](https://img.shields.io/badge/SQLite-3.x-003B57?style=for-the-badge&logo=sqlite&logoColor=white)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)]()
[![GitHub stars](https://img.shields.io/github/stars/wuchenghao15/MTSCOS?style=for-the-badge)]()
[![GitHub forks](https://img.shields.io/github/forks/wuchenghao15/MTSCOS?style=for-the-badge)]()
[![GitHub issues](https://img.shields.io/github/issues/wuchenghao15/MTSCOS?style=for-the-badge)]()

</div>

## 📖 项目简介

MTSCOS AI 是一个多租户智能配置操作系统，集成了AI引擎、学习系统、权限管理、备份恢复、影子系统等核心功能。基于Flask框架构建，支持多角色权限控制，具备完整的安全防护体系。

### ✨ 核心特性

- 🔐 **企业级安全** - 超级管理员唯一性、CSRF防护、越权访问拦截、注册速率限制
- 🤖 **AI引擎系统** - AI员工管理、智能调度、自动运维、日志分析
- 📚 **智能学习** - 学习进度追踪、知识库管理、课程体系
- 🔄 **备份恢复** - 快照管理、ISO构建、影子系统切换
- 👥 **多租户架构** - 多角色权限、用户管理、审计日志
- 🎨 **主题系统** - 多主题切换、公祭日自动切换
- ⚡ **性能优化** - 数据库连接池、缓存机制、异步任务

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        MTSCOS AI                            │
├─────────────┬───────────────┬────────────────┬──────────────┤
│   表现层     │   业务逻辑层   │   数据访问层    │   基础设施   │
├─────────────┼───────────────┼────────────────┼──────────────┤
│  Web界面     │  AI引擎       │  SQLite        │  Flask       │
│  API接口     │  学习系统     │  缓存系统       │  Session     │
│  主题系统    │  备份恢复     │  文件存储       │  安全框架    │
│  管理后台    │  权限控制     │  审计日志       │  调度系统    │
└─────────────┴───────────────┴────────────────┴──────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.9+
- SQLite 3.x
- 512MB+ 可用内存
- 1GB+ 可用磁盘空间

### 安装部署

```bash
# 1. 克隆仓库
git clone https://github.com/wuchenghao15/MTSCOS.git
cd MTSCOS

# 2. 安装依赖
pip install flask

# 3. 启动服务
python server_real_db.py

# 4. 访问系统
# 打开浏览器访问 http://localhost:8888
```

### 默认账号

| 用户名 | 角色 | 说明 |
|--------|------|------|
| wuchenghao15 | 超级管理员 | 系统唯一超级管理员 |
| admin | 管理员 | 系统管理 |
| teacher001 | 教师 | 教学管理 |
| student001 | 学生 | 学习使用 |

> **安全提示**：首次登录后请立即修改默认密码！

## 📁 项目结构

```
MTSCOS/
├── server_real_db.py          # 主服务入口
├── flask-app/
│   ├── app.db                 # SQLite数据库
│   ├── scripts/
│   │   └── tools/
│   │       └── mtscos_system_test_engine.py  # 系统测试引擎
│   ├── templates/             # HTML模板
│   ├── static/                # 静态资源
│   └── backups/               # 备份目录
├── ai_engines/                # AI引擎模块
├── core/                      # 核心服务
├── backup_db.py               # 数据库备份工具
├── SECURITY.md                # 安全文档
├── CONTRIBUTING.md            # 贡献指南
├── CODE_OF_CONDUCT.md         # 行为准则
├── LICENSE                    # 开源协议
└── README.md                  # 项目说明
```

## 🔧 功能模块

### 安全系统
- ✅ 超级管理员唯一性（仅wuchenghao15）
- ✅ CSRF跨站请求伪造防护
- ✅ API权限控制（越权访问防护）
- ✅ 注册速率限制（防暴力注册）
- ✅ SQL注入防护
- ✅ 密码强度验证
- ✅ Session安全管理
- ✅ Vikey硬件密钥支持

### AI引擎
- 🤖 AI员工系统
- 📊 智能调度器
- 📝 日志分析器
- 🔧 自动运维
- 🎯 学习进度分析

### 学习系统
- 📚 课程管理
- 📝 题库系统
- 📊 学习进度
- 🏆 考试中心
- 📈 知识图谱

### 系统管理
- 💾 快照备份
- 📀 ISO构建
- 👤 用户管理
- 📋 审计日志
- 🌓 影子系统
- 🎨 主题切换

## 🧪 测试

运行系统测试引擎：

```bash
cd flask-app
python scripts/tools/mtscos_system_test_engine.py
```

测试覆盖：
- ✅ 用户认证测试
- ✅ API权限测试
- ✅ 页面访问测试
- ✅ 安全漏洞扫描
- ✅ 性能基准测试

## 📈 GitHub 高曝光优化

### 项目元数据

本项目已按照GitHub官方最佳实践配置，提升搜索排名和曝光度：

- ✅ 清晰的项目名称和描述
- ✅ 完整的README文档
- ✅ 开源协议（MIT）
- ✅ 贡献指南
- ✅ 行为准则
- ✅ Issue/PR模板
- ✅ GitHub Actions CI/CD
- ✅ 安全策略文档
- ✅ 项目标签（Topics）

### GitHub Actions 徽章

| 工作流 | 状态 |
|--------|------|
| CI 构建 | ![CI](https://img.shields.io/badge/CI-passing-brightgreen) |
| 安全扫描 | ![Security](https://img.shields.io/badge/security-passing-brightgreen) |
| 代码质量 | ![Quality](https://img.shields.io/badge/code%20quality-A-brightgreen) |

## 🤝 贡献指南

我们欢迎各种形式的贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 贡献方式

1. ⭐ Star 本项目
2. 🐛 提交 Issue 反馈问题
3. 💡 提出新功能建议
4. 🔧 提交 PR 修复问题或添加功能
5. 📝 完善文档

### 开发流程

```bash
# Fork 本仓库
# 克隆你的 Fork
git clone https://github.com/你的用户名/MTSCOS.git

# 创建功能分支
git checkout -b feature/AmazingFeature

# 提交更改
git commit -m 'Add some AmazingFeature'

# 推送到分支
git push origin feature/AmazingFeature

# 发起 Pull Request
```

## 🛡️ 安全

请阅读 [SECURITY.md](SECURITY.md) 了解我们的安全政策和漏洞报告流程。

**安全红线**：超级管理员有且仅有一人就是 `wuchenghao15`，这是不可突破的铁律。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

感谢所有为这个项目做出贡献的人！

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！**

Made with ❤️ by wuchenghao15

</div>
