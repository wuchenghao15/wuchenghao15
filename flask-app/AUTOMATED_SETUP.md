# MTSCOS AI Project - 自动化初始化流程

## 📋 概述

`automated_setup.py` 是一个统一的自动化初始化脚本，用于简化项目的初始化过程，减少手动交互，提高开发效率。

## ✨ 功能特性

1. **环境检查**：检查Python版本、pip安装状态和目录结构
2. **依赖安装**：自动安装项目依赖
3. **目录创建**：创建必要的目录结构
4. **数据库初始化**：自动初始化数据库表
5. **AI系统初始化**：初始化AI集和AI实例管理器
6. **应用启动**：可选的应用启动功能

## 🚀 使用方法

### 基本用法

```bash
# 完整初始化流程（推荐首次使用）
python3 automated_setup.py

# 查看帮助信息
python3 automated_setup.py --help
```

### 选项说明

| 选项 | 描述 |
|------|------|
| `--skip-deps` | 跳过依赖安装 |
| `--skip-db` | 跳过数据库初始化 |
| `--skip-ai` | 跳过AI系统初始化 |
| `--start-app` | 初始化完成后启动应用 |
| `--help` | 显示帮助信息 |

### 常用场景

```bash
# 首次初始化（完整流程）
python3 automated_setup.py

# 跳过依赖安装（已安装过依赖）
python3 automated_setup.py --skip-deps

# 仅检查环境
python3 automated_setup.py --skip-deps --skip-db --skip-ai

# 初始化后启动应用
python3 automated_setup.py --start-app

# 快速重启应用（跳过所有初始化步骤）
python3 automated_setup.py --skip-deps --skip-db --skip-ai --start-app
```

## 📁 目录结构

初始化过程中会创建以下目录：

```
.
├── data/                # 数据文件目录
├── logs/                # 日志文件目录
├── backups/             # 备份文件目录
├── static/avatars/      # 头像存储目录
├── static/css/          # CSS文件目录
├── static/js/           # JavaScript文件目录
├── static/js/vikey/     # Vikey相关JavaScript
├── static/js/utils/     # 工具JavaScript
├── templates/           # HTML模板目录
├── instance/            # 实例配置目录
└── docs/                # 文档目录
```

## 🗄️ 数据库初始化

脚本会自动：

1. 运行现有的数据库初始化脚本 `init_and_update_db.py`
2. 如果没有初始化脚本，直接创建所有必要的数据库表
3. 运行数据库更新脚本 `update_database.py`

## 🤖 AI系统初始化

脚本会初始化：

1. AI集管理器 `AIEnsemble`
2. AI实例管理器 `ai_instance_manager`
3. 检测项目功能并自动实例化所需的AI类型

## 📊 日志记录

初始化过程会生成日志文件 `setup.log`，包含详细的初始化信息，便于调试和问题排查。

## 🔧 自定义配置

### 跳过特定步骤

可以通过命令行选项跳过不需要的初始化步骤，例如：

```bash
# 跳过依赖安装和AI初始化
python3 automated_setup.py --skip-deps --skip-ai
```

### 手动配置

如果需要手动配置某些部分，可以在初始化完成后进行：

1. **依赖管理**：手动编辑 `requirements.txt` 后运行 `pip install -r requirements.txt`
2. **数据库配置**：修改 `app/config.py` 中的数据库配置
3. **AI配置**：修改AI实例的配置参数

## 📝 注意事项

1. **首次使用**：推荐使用完整初始化流程
2. **权限要求**：确保有足够的权限创建目录和文件
3. **依赖管理**：如果使用虚拟环境，请先激活虚拟环境
4. **数据库配置**：确保数据库配置正确，否则初始化会失败
5. **日志查看**：如果初始化失败，请查看 `setup.log` 获取详细信息

## 🐛 故障排除

### 常见错误

1. **依赖安装失败**：检查网络连接和 `requirements.txt` 文件
2. **数据库初始化失败**：检查数据库配置和权限
3. **目录创建失败**：检查目录权限
4. **AI初始化失败**：检查AI模块的依赖和配置

### 解决方法

1. 查看 `setup.log` 获取详细错误信息
2. 检查相关配置文件
3. 尝试跳过失败的步骤，手动解决问题后继续
4. 如果问题持续存在，请联系开发团队

## 🔄 更新日志

### v1.0.0
- 首次发布
- 实现完整的自动化初始化流程
- 支持环境检查、依赖安装、数据库初始化、AI系统初始化和应用启动
- 支持命令行选项定制初始化流程

## 📄 许可证

MIT License
