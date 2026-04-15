# MTSCOS 脚本架构说明

## 脚本结构概述

经过重构，MTSCOS启动脚本已分为三个主要脚本，各自负责不同的功能领域：

1. **start_all.sh** - 入口脚本（兼容性层）
   - 作为主入口点，保持向后兼容性
   - 将命令委托给专用脚本处理
   - 检查依赖脚本的存在性

2. **start_main.sh** - 基础功能脚本
   - 环境检测（终端类型、操作系统、Node.js）
   - 初始化和修复功能
   - 重命名包含Vikey的文件和目录
   - 错误检测和清理管理

3. **service_manager.sh** - 服务管理脚本
   - 服务生命周期管理（启动、停止、状态检查）
   - 支持单个服务和批量服务操作
   - 提供更细粒度的服务控制

## 命令参考

### 基础命令（所有脚本通用）

```bash
# 启动所有服务（先执行修复，再启动服务）
./start_all.sh start

# 停止所有服务
./start_all.sh stop

# 重启所有服务
./start_all.sh restart

# 检查所有服务状态
./start_all.sh status

# 执行初始化检测和修复
./start_all.sh fix

# 重命名包含Vikey的文件和目录
./start_all.sh rename-Vikey
```

### 新增命令（通过start_all.sh访问）

```bash
# 显示环境信息
./start_all.sh env

# 启动单个服务
./start_all.sh start-service <service_name> <js_file_path>

# 停止单个服务
./start_all.sh stop-service <service_name>

# 检查单个服务状态
./start_all.sh check-service <service_name>
```

### 直接使用专用脚本

```bash
# 使用基础脚本执行环境检测
./start_main.sh env

# 使用服务管理脚本直接控制服务
./service_manager.sh start
./service_manager.sh stop
./service_manager.sh status
```

## 日志文件

- **Logs/start_all.log** - 入口脚本操作日志
- **Logs/start_main.log** - 基础功能脚本日志
- **Logs/service_manager.log** - 服务管理操作日志
- **Logs/error.log** - 错误日志（所有脚本共享）
- **Logs/*.log** - 各服务的独立日志文件

## 依赖关系

- **start_all.sh** 依赖于 **start_main.sh** 和 **service_manager.sh**
- 所有脚本都依赖于Node.js环境
- 服务管理依赖于JavaScript目录中的各个服务脚本

## 故障排除

1. **脚本执行权限问题**：使用 `chmod +x *.sh` 确保所有脚本具有执行权限
2. **依赖脚本缺失**：检查三个主脚本是否都存在于项目根目录
3. **Node.js环境问题**：确保已安装Node.js并添加到系统路径
4. **日志分析**：检查Logs目录下的日志文件以获取详细错误信息

## 示例用法

```bash
# 启动整个系统
./start_all.sh start

# 检查系统状态
./start_all.sh status

# 执行环境检查
./start_all.sh env

# 重启特定服务
./start_all.sh stop-service version-checker
./start_all.sh start-service version-checker JavaScript/version_checker.js

# 执行修复操作
./start_all.sh fix
```