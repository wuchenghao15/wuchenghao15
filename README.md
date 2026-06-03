# MTSCOS AI Project v2.1.0

## 项目信息
- **版本**: 2.1.0
- **最后更新**: 2026-05-26
- **状态**: 🚀 升级完成 - 增强版

## 项目规则
1. ❌ 不使用JSON功能 - 一律由数据库代替
2. ✅ 使用数据库统一存储
3. ✅ 使用Redis哨兵模式（高可用）
4. ✅ 主从读写分离

## 🆕 v2.1.0 新功能

### 核心模块升级 (Core v2.0)
- ✨ **增强的配置管理** - ConfigManager 支持合并、保存、重载
- 🤖 **多AI提供商支持** - OpenAI、Anthropic、Ollama 三家可选
- 💾 **AI响应缓存** - 内置缓存机制，提升响应速度
- 🌊 **流式输出支持** - 支持实时流式AI响应
- 📊 **性能监控** - 后台自动记录CPU/内存/磁盘历史数据
- 🔧 **系统健康监控** - 全面的系统状态检查
- 🌐 **网络接口监控** - 详细网络接口信息
- 💽 **磁盘分区信息** - 完整的磁盘使用情况
- 🕵️ **进程管理** - 支持获取Top N进程列表

### API 增强端点
- `GET /api` - API根端点
- `GET /api/version` - 版本信息
- `GET /api/system/performance` - 性能报告
- `GET /api/system/network` - 网络接口
- `GET /api/system/disks` - 磁盘分区
- `GET /api/system/processes` - 进程列表
- `POST /api/config/reload` - 重载配置
- `POST /api/ai/chat` - AI对话
- `POST /api/ai/analyze` - 代码分析
- `POST /api/ai/summarize` - 文本摘要
- `POST /api/ai/translate` - 文本翻译
- `GET /api/ai/providers` - AI提供商列表
- `POST /api/ai/cache/clear` - 清除缓存

## 快速开始

### 方式一: 使用 Makefile (推荐)
```bash
make install
make run
# 访问 http://localhost:5000
```

### 方式二: 直接运行
```bash
pip install -e .
python main.py
# 访问 http://localhost:5000
```

### 健康检查
```bash
make health-check
```

### 数据库备份
```bash
make backup-db
```

## 功能模块
- 智能登录系统
- 用户管理
- 题库管理
- AI员工系统
- AI管家系统
- 硬件管理
- 🆕 多AI提供商支持
- 🆕 系统性能监控
- 🆕 增强API服务

## 项目结构
```
MTSCOS_AI_Project/
├── core/              # 核心模块 v2.0
│   ├── __init__.py
│   ├── config.py      # 配置管理
│   ├── database.py  # 数据库管理
│   ├── logging.py   # 日志系统
│   ├── system.py    # 系统监控
│   ├── ai.py        # AI服务
│   ├── utils.py     # 工具函数
│   └── exceptions.py
├── api/               # API路由
├── tests/             # 测试模块
├── main.py          # 主程序
├── setup.py         # 安装脚本
└── Makefile        # 构建工具
```

## 版本记录

### v2.1.0 (2026-05-26)
- ✨ 升级核心模块到v2.0
- 🤖 添加多AI提供商支持 (OpenAI/Anthropic/Ollama)
- 💾 添加AI响应缓存
- 📊 性能监控系统
- 🔧 增强的健康检查
- 🌐 网络/磁盘/进程监控API
- 📝 完整的API文档
- ⚡ 响应式API端点

### v1.0.0 (2026-05-01)
- 基础版本
- 数据库双备份
- ISO恢复镜像创建
