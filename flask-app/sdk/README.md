# MTSCOS AI SDK

MTSCOS AI系统Python SDK，提供统一的API接口，方便外部应用集成。

## 🚀 功能特性

- **AI服务** - 数据矩阵、健康状态、异常检测、风险预测
- **备份系统** - 常规备份、应急备份、双备份机制、处罚规则
- **证书管理** - 数字证书发放、会话管理、退出处理、打包上传
- **恢复镜像** - 完整备份、增量备份、镜像恢复、恢复链
- **自动升级** - 版本检查、自动升级
- **例行维护** - 维护任务、调度器、维护窗口
- **系统整合** - 跨系统数据整合、数据库上报

## 📦 安装

```bash
# 安装SDK
pip install mtscos-sdk

# 或者从源码安装
cd sdk
pip install .
```

## 🔧 快速开始

```python
from mtscos import MTSCOSSDK, SDKConfig

# 初始化SDK
config = SDKConfig(
    base_url="http://localhost:5000",
    api_key="your_api_key"
)

sdk = MTSCOSSDK(config)

# 获取SDK版本
print(f"SDK版本: {sdk.get_version()}")

# 示例1: 获取AI服务状态
status = sdk.ai.get_status()
print(f"AI服务状态: {status}")

# 示例2: 创建备份计划
backup_plan = sdk.backup.create_plan(
    plan_type="daily",
    name="每日备份",
    source_paths=["/data"],
    destination="/backups"
)
print(f"备份计划创建成功: {backup_plan}")

# 示例3: 发放证书
cert = sdk.certificate.issue_certificate("client_001")
print(f"证书发放成功: {cert}")

# 示例4: 创建会话
session = sdk.certificate.create_session("client_001")
print(f"会话创建成功: {session}")

# 示例5: 创建恢复镜像
mirror = sdk.recovery.create_full_backup(
    source_paths=["/data"],
    description="完整备份"
)
print(f"镜像创建成功: {mirror}")
```

## 📚 API模块

### 1. AI服务模块

```python
# 获取数据矩阵
matrix = sdk.ai.get_data_matrices()

# 获取系统健康状态
health = sdk.ai.get_system_health()

# 获取异常检测
anomalies = sdk.ai.get_anomalies()

# 获取风险预测
risks = sdk.ai.get_risk_predictions()

# 获取洞察报告
insights = sdk.ai.get_insights()
```

### 2. 备份系统模块

```python
# 创建备份计划
plan = sdk.backup.create_plan(
    plan_type="daily",
    name="每日备份",
    source_paths=["/data"],
    destination="/backups",
    dual_backup_enabled=True
)

# 执行备份计划
result = sdk.backup.execute_plan(plan_id)

# 应急备份
emergency = sdk.backup.emergency_backup(
    source_paths=["/critical_data"],
    reason="系统异常"
)

# 倒查备份
investigation = sdk.backup.investigate_backup(backup_id)
```

### 3. 证书管理模块

```python
# 发放证书
cert = sdk.certificate.issue_certificate("client_001")

# 创建会话
session = sdk.certificate.create_session("client_001")

# 添加日志
sdk.certificate.add_log(session_id, "info", "用户登录")

# 记录操作
sdk.certificate.record_operation(session_id, "login")

# 正常退出
package = sdk.certificate.close_session(session_id, "normal", "用户退出")

# 意外退出
package = sdk.certificate.close_session(session_id, "unexpected", "系统崩溃")
```

### 4. 恢复镜像模块

```python
# 创建完整备份
mirror = sdk.recovery.create_full_backup(
    source_paths=["/data"],
    description="完整备份"
)

# 创建增量备份
incremental = sdk.recovery.create_incremental_backup(
    source_paths=["/data"],
    base_mirror_id=mirror_id
)

# 恢复镜像
result = sdk.recovery.restore_mirror(mirror_id, "/restore/path")

# 验证镜像完整性
validation = sdk.recovery.validate_mirror(mirror_id)
```

### 5. 例行维护模块

```python
# 获取维护状态
status = sdk.maintenance.get_status()

# 执行维护窗口
result = sdk.maintenance.execute_maintenance_window("daily")

# 检查升级
upgrade = sdk.maintenance.check_upgrade()

# 获取任务统计
stats = sdk.maintenance.get_statistics()
```

### 6. 系统整合模块

```python
# 获取整合状态
status = sdk.integration.get_status()

# 注册子系统
subsystem = sdk.integration.register_subsystem("my_subsystem")

# 获取综合状态
comprehensive = sdk.integration.get_comprehensive_status()

# 上报异常
sdk.integration.report_anomaly({
    'type': 'error',
    'message': '系统异常',
    'severity': 'high'
})
```

## 📖 详细文档

### SDK配置

```python
from mtscos import SDKConfig

config = SDKConfig(
    base_url="http://localhost:5000",  # MTSCOS系统地址
    api_key="your_api_key",            # API密钥（可选）
    timeout=30,                        # 请求超时时间（秒）
    debug=False                        # 调试模式
)
```

### 退出类型

| 类型 | 值 | 说明 |
|------|-----|------|
| 正常退出 | `normal` | 用户主动退出系统 |
| 意外退出 | `unexpected` | 程序崩溃、网络中断 |
| 临时挂单 | `temporary` | 用户暂时离开 |

### 备份类型

| 类型 | 值 | 说明 |
|------|-----|------|
| 完整备份 | `full` | 备份所有文件 |
| 增量备份 | `incremental` | 仅备份变更的文件 |

### 操作类型

| 类型 | 值 | 说明 |
|------|-----|------|
| 登录 | `login` | 用户登录 |
| 登出 | `logout` | 用户登出 |
| 创建 | `create` | 创建资源 |
| 读取 | `read` | 读取资源 |
| 更新 | `update` | 更新资源 |
| 删除 | `delete` | 删除资源 |
| 查询 | `query` | 查询操作 |
| 执行 | `execute` | 执行操作 |
| 上传 | `upload` | 上传文件 |
| 下载 | `download` | 下载文件 |

## 🔒 安全注意事项

1. **API密钥管理**: 妥善保管API密钥，不要硬编码在代码中
2. **HTTPS**: 生产环境建议使用HTTPS连接
3. **超时设置**: 根据网络情况合理设置超时时间
4. **错误处理**: 妥善处理API调用异常

## 📝 版本历史

- **v2.0.0** - 完整功能版本
  - AI服务模块
  - 备份系统模块
  - 证书管理模块
  - 恢复镜像模块
  - 自动升级模块
  - 例行维护模块
  - 系统整合模块

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📧 联系方式

- 邮箱: support@mtscos.com
- 文档: https://docs.mtscos.com/sdk
- GitHub: https://github.com/mtscos/mtscos-sdk
