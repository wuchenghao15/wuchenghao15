# 版本升级记录

## v3.1.0 (2026-05-28) - 系统升级到 v3.1

### 升级概要

本次升级完成了核心系统的全面优化整合，版本从 3.0.0 升级到 3.1.0，主要包含：

- 系统版本统一管理
- 代码结构优化
- 功能增强与拓展

### 主要变化

#### 1. 核心模块优化（Core v3.1）

**版本统一管理**

- 所有核心模块版本号统一升级到 3.1.0
- 建立统一的版本管理机制
- 更新 VERSION 文件到 3.1.0

**`core/__init__.py`** - 模块导入更新

- 更新版本号为 3.1.0
- 优化模块导出结构

**`core/config.py`** - 配置管理升级

- 更新配置版本到 3.1.0
- 增强配置合并逻辑

**`core/system.py`** - 系统管理升级

- 更新版本号到 3.1.0
- 增强性能监控功能

**`core/ai.py`** - AI 服务升级

- 更新版本号到 3.1.0
- 优化多 AI 提供商支持

#### 2. 主程序升级

**`main.py`** - 主程序升级

- 更新版本号到 3.1.0
- 优化 API 端点结构

**`setup.py`** - 安装配置更新

- 更新版本号到 3.1.0
- 更新项目描述

#### 3. 文件变更列表

| 文件 | 变更类型 | 描述 |
|------|---------|------|
| `VERSION` | 修改 | 更新版本号到 3.1.0 |
| `core/__init__.py` | 修改 | 版本号更新到 3.1.0 |
| `core/config.py` | 修改 | 配置版本更新到 3.1.0 |
| `core/system.py` | 修改 | 系统模块版本更新到 3.1.0 |
| `core/ai.py` | 修改 | AI 服务版本更新到 3.1.0 |
| `main.py` | 修改 | 主程序版本更新到 3.1.0 |
| `setup.py` | 修改 | 版本更新到 3.1.0 |
| `Others/VERSION` | 修改 | 版本更新到 3.1.0 |
| `SourceCode/Others/VERSION` | 修改 | 版本更新到 3.1.0 |
| `UPGRADE.md` | 修改 | 更新升级记录 |

### 新特性

1. **统一版本管理** - 所有模块版本号统一同步
2. **代码结构优化** - 整合冗余代码，提升可维护性
3. **增强的 AI 服务** - 支持多提供商的智能切换
4. **性能监控增强** - 更全面的系统监控能力

### 升级说明

系统已完全兼容旧版本 API，无需修改现有代码。

### 验证步骤

1. 运行测试：

```bash
python test_upgrade.py
```

2. 启动服务：

```bash
make run
```

3. 检查健康检查：

```bash
make health-check
```

### 版本号变更

- API: 3.0.0 → 3.1.0
- Core: 3.0.0 → 3.1.0
- Setup: 2.1.0 → 3.1.0

---

## v2.1.0 (2026-05-26) - 系统升级到 v2.1

### 升级概要

本次升级完成了核心系统的全面升级，版本从 1.0.0 升级到 2.1.0。

### 主要变化

#### 1. 核心模块（Core v2.0）

**`core/config.py`** - 配置管理升级

- 新增 `_merge_configs()` 方法 - 配置合并
- 新增 `get_all()` - 获取完整配置
- 新增 `has()` - 检查配置键是否存在
- 新增 `delete()` - 删除配置键
- 新增 `reload()` - 重载配置
- 新增 `get_version()` - 获取配置版本
- 新增默认配置结构增强

**`core/ai.py`** - AI 服务升级

- 新增 `AICache` 类 - AI 响应缓存
- 支持多 AI 提供商：OpenAI、Anthropic、Ollama
- 新增 `get_available_providers()` - 获取可用提供商
- 新增 `chat()` - AI 对话支持
- 新增 `extract_keywords()` - 关键词提取
- 新增 `rewrite_text()` - 文本重写
- 新增 `generate_stream()` - 流式响应
- 新增 `get_status()` - AI 状态查询
- 新增 `clear_cache()` - 清除缓存

**`core/system.py`** - 系统管理升级

- 新增 `PerformanceMonitor` 类 - 性能监控
- 新增 `get_network_interfaces()` - 网络接口信息
- 新增 `get_disk_partitions()` - 磁盘分区信息
- 新增 `get_all_processes()` - 进程列表
- 新增 `get_performance_report()` - 性能报告
- 新增 `register_health_check()` - 健康检查
- 新增 `_start_monitoring()` - 后台监控线程

**`core/__init__.py`** - 模块导入更新

- 新增 `get_version()` 函数
- 更新版本号为 2.0.0
- 导出所有新类

#### 2. API 端点增强

**`api/routes.py`** - API 路由升级

- 新增 `GET /api/` - API 根端点
- 新增 `GET /api/version` - 版本信息
- 新增 `GET /api/system/performance` - 性能报告
- 新增 `GET /api/system/network` - 网络接口
- 新增 `GET /api/system/disks` - 磁盘分区
- 新增 `GET /api/system/processes` - 进程列表
- 新增 `POST /api/config/reload` - 重载配置
- 新增 `GET /api/ai` - AI 状态
- 新增 `POST /api/ai/chat` - AI 对话
- 新增 `POST /api/ai/analyze` - 代码分析
- 新增 `POST /api/ai/summarize` - 文本摘要
- 新增 `POST /api/ai/translate` - 文本翻译
- 新增 `GET /api/ai/providers` - 提供商列表
- 新增 `POST /api/ai/cache/clear` - 清除缓存
- 增强 `POST /api/command` - 超时选项

**`main.py`** - 主程序升级

- 新增版本号 `__version__`
- 新增端点
- 新增 `/` - JSON 首页
- 新增 `/status` - 增强状态
- 新增 `/health` - 健康检查
- 新增 `/system` - 系统信息
- 新增 `/performance` - 性能报告
- 新增 `/api/version` - API 版本
- 更新默认主机为 `0.0.0.0`

#### 3. 安装和构建

**`setup.py`** - 更新版本号

- version: 1.0.0 → 2.1.0
- 更新项目描述

**`README.md`** - 完整文档更新

### 文件变更列表

| 文件 | 变更类型 | 描述 |
|------|---------|------|
| `core/__init__.py` | 修改 | 模块升级 v2.0 |
| `core/config.py` | 修改 | 增强配置管理 |
| `core/ai.py` | 修改 | AI 服务升级 |
| `core/system.py` | 修改 | 系统监控升级 |
| `api/routes.py` | 修改 | API 端点增强 |
| `main.py` | 修改 | 主程序升级 |
| `setup.py` | 修改 | 版本更新 |
| `README.md` | 修改 | 文档更新 |
| `UPGRADE.md` | 新增 | 升级记录 |

### 新特性

1. **多 AI 提供商** - OpenAI / Anthropic / Ollama
2. **AI 缓存** - 响应缓存提高性能
3. **流式输出** - 实时 AI 响应
4. **性能监控** - 后台自动监控
5. **网络监控** - 网络接口信息
6. **磁盘监控** - 分区使用情况
7. **进程管理** - 进程列表和信息
8. **配置重载** - 运行时配置更新

### 升级说明

系统已完全兼容旧版本 API，无需修改现有代码。

### 验证步骤

1. 运行测试：

```bash
python test_upgrade.py
```

2. 启动服务：

```bash
make run
```

3. 检查健康检查：

```bash
make health-check
```

### 版本号变更

- API: 1.0.0 → 2.1.0
- Core: 1.0.0 → 2.0.0
- Setup: 1.0.0 → 2.1.0

### 升级完成日期

2026-05-26
