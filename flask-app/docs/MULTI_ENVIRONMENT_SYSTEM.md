# 多环境管理系统 - 使用指南

## 概述

多环境管理系统（MEMS）是一个完整的环境隔离和测试管理平台，整合了：
- **开发环境** (Development) - 本地开发
- **测试环境** (Testing) - 功能测试
- **公测环境** (Staging) - 预发布
- **生产环境** (Production) - 正式环境

以及三大子系统：
- **沙盒系统** (Sandbox) - 隔离执行环境
- **影子系统** (Shadow) - 数据隔离副本
- **测试系统** (Test) - 自动化测试

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│              Multi-Environment Manager               │
├─────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────┐ │
│  │   Dev    │  │   Test   │  │ Staging  │  │ Prod│ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──┬──┘ │
│       │             │             │            │     │
│       └─────────────┼─────────────┼────────────┘     │
│                     ▼                              │
│            ┌───────────────┐                       │
│            │   数据隔离层   │                       │
│            └───────┬───────┘                       │
│        ┌───────────┼───────────┐                   │
│        ▼           ▼           ▼                   │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│   │ Sandbox │ │ Shadow  │ │  Test   │            │
│   │   沙盒   │ │  影子   │ │  测试   │            │
│   └─────────┘ └─────────┘ └─────────┘            │
└─────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 导入系统

```python
from app.ai.multi_environment_manager import (
    multi_env_manager,
    EnvironmentType,
    SystemType
)
```

### 2. 切换环境

```python
# 切换到开发环境
result = multi_env_manager.activate_environment('dev')

# 切换到测试环境
result = multi_env_manager.switch_environment('test')

# 切换到公测环境
result = multi_env_manager.switch_environment('staging')

# 切换到生产环境
result = multi_env_manager.switch_environment('prod')
```

### 3. 获取当前环境

```python
current = multi_env_manager.get_current_environment()
print(f"当前环境: {current['name']}")
print(f"环境类型: {current['type']}")
print(f"环境状态: {current['status']}")
```

### 4. 列出所有环境

```python
environments = multi_env_manager.list_environments()
for env in environments:
    print(f"{env['id']}: {env['name']} - {env['status']}")
```

## 环境配置

### 查看环境配置

```python
config = multi_env_manager.get_environment_config('test')
print(f"API地址: {config['api_base']}")
print(f"调试模式: {config['debug']}")
print(f"日志级别: {config['log_level']}")
```

### 更新环境配置

```python
# 启用测试环境的沙盒
multi_env_manager.update_environment_config('test', {
    'use_sandbox': True,
    'memory_limit': '1GB'
})

# 禁用生产环境的速率限制
multi_env_manager.update_environment_config('prod', {
    'rate_limiting': False
})
```

### 导出/导入配置

```python
# 导出配置
config_json = multi_env_manager.export_environment_config('test')

# 导入配置
multi_env_manager.import_environment_config(config_json)
```

## 沙盒系统

### 创建沙盒

```python
success = multi_env_manager.sandbox_manager.create_sandbox(
    'my_sandbox',
    {
        'allow_execution': True,
        'memory_limit': '512MB',
        'cpu_limit': 2,
        'network_isolated': True
    }
)
```

### 激活沙盒

```python
# 为当前环境激活沙盒
sandbox_name = 'test_sandbox'
multi_env_manager.sandbox_manager.activate_sandbox(sandbox_name)
```

### 在沙盒中执行代码

```python
result = multi_env_manager.sandbox_manager.execute_in_sandbox(
    'test_sandbox',
    'print("Hello from sandbox!")',
    timeout=30
)
print(result['output'])
```

### 在环境中执行代码

```python
result = multi_env_manager.execute_in_environment(
    'test',
    'def test_function():\n    return "test passed"',
    timeout=60
)
```

### 列出沙盒

```python
sandboxes = multi_env_manager.sandbox_manager.list_sandboxes()
for sandbox in sandboxes:
    print(f"{sandbox['id']}: {sandbox['status']}")
```

## 影子系统

### 创建影子系统

```python
success = multi_env_manager.shadow_system.create_shadow(
    source='production',
    shadow_id='test_shadow',
    config={
        'sync_interval': 3600,
        'anonymize': True,
        'sync_fields': ['users', 'products']
    }
)
```

### 同步影子数据

```python
data = {
    'users': [...],
    'products': [...],
    'orders': [...]
}

success = multi_env_manager.shadow_system.sync_shadow('test_shadow', data)
```

### 获取影子数据

```python
data = multi_env_manager.shadow_system.get_shadow_data('test_shadow')
if data:
    print(f"影子数据: {data}")
```

### 列出影子系统

```python
shadows = multi_env_manager.shadow_system.list_shadows()
for shadow in shadows:
    print(f"{shadow['id']} <- {shadow['source']} (上次同步: {shadow['last_sync']})")
```

## 测试系统

### 注册测试套件

```python
multi_env_manager.test_system.register_test_suite(
    'api_tests',
    [
        {'id': 'api_001', 'name': '用户登录API'},
        {'id': 'api_002', 'name': '数据查询API'},
        {'id': 'api_003', 'name': '用户注册API'},
        {'id': 'api_004', 'name': '密码重置API'}
    ]
)
```

### 运行测试

```python
# 运行所有测试
result = multi_env_manager.test_system.run_test('api_tests')

print(f"通过: {result['passed']}")
print(f"失败: {result['failed']}")
print(f"通过率: {result['pass_rate']:.2f}%")
```

### 运行特定测试

```python
result = multi_env_manager.test_system.run_test(
    'api_tests',
    test_id='api_001'
)
```

### 获取测试统计

```python
stats = multi_env_manager.test_system.get_test_stats()
print(f"总测试套件: {stats['total_suites']}")
print(f"总测试数: {stats['total_tests']}")
print(f"总体通过率: {stats['overall_pass_rate']:.2f}%")
```

### 在环境中运行测试

```python
result = multi_env_manager.run_tests_in_environment('test', 'api_tests')
```

## API接口

### 环境管理API

```bash
# 获取所有环境
GET /api/environments/

# 获取当前环境
GET /api/environments/current

# 激活环境
POST /api/environments/{env_id}/activate

# 获取环境配置
GET /api/environments/{env_id}/config

# 更新环境配置
PUT /api/environments/{env_id}/config

# 验证环境
POST /api/environments/{env_id}/validate

# 在环境中执行代码
POST /api/environments/{env_id}/execute

# 在环境中运行测试
POST /api/environments/{env_id}/test
```

### 沙盒API

```bash
# 列出所有沙盒
GET /api/environments/sandbox

# 激活沙盒
POST /api/environments/sandbox/{sandbox_id}/activate
```

### 影子系统API

```bash
# 列出所有影子系统
GET /api/environments/shadow
```

### 测试API

```bash
# 列出测试套件
GET /api/environments/test/suites

# 运行测试套件
POST /api/environments/test/{suite_id}/run

# 获取测试统计
GET /api/environments/test/stats
```

### 仪表板

```bash
# 获取完整仪表板
GET /api/environments/dashboard

# 导出环境配置
GET /api/environments/export/{env_id}

# 导入环境配置
POST /api/environments/import
```

## 数据隔离

### 隔离规则

```python
from app.ai.multi_environment_manager import DataIsolation

isolation = DataIsolation()

# 添加表隔离规则
isolation.add_isolation_rule('users', {
    'type': 'env_prefix',
    'prefix': 'users',
    'columns': ['email', 'phone']
})

# 应用隔离到查询
query = "SELECT * FROM users WHERE active = 1"
isolated_query = isolation.apply_isolation(
    'users',
    query,
    {'environment': 'test'}
)
print(isolated_query)
# 输出: SELECT * FROM users_test_ WHERE active = 1
```

### 数据映射

```python
# 设置数据映射
isolation.set_data_mapping('prod', 'test', {
    'email': 'test_email',
    'phone': 'test_phone'
})

# 获取映射后的数据
original_data = {
    'name': '张三',
    'email': 'zhangsan@example.com',
    'phone': '13800138000'
}

mapped_data = isolation.get_mapped_data('prod', 'test', original_data)
print(mapped_data)
# 输出: {'name': '张三', 'test_email': 'zhangsan@example.com', 'test_phone': '13800138000'}
```

## 最佳实践

### 1. 环境切换前备份

```python
# 确保开启备份
multi_env_manager.config['backup_on_switch'] = True

# 切换环境（自动备份）
multi_env_manager.switch_environment('staging')
```

### 2. 验证环境再使用

```python
# 使用前验证
validation = multi_env_manager.validate_environment('test')
if validation['valid']:
    print("环境验证通过，可以安全使用")
else:
    print("环境存在问题:", validation['issues'])
```

### 3. 统一的工作流

```python
def deploy_to_staging():
    # 1. 切换到测试环境
    multi_env_manager.activate_environment('test')

    # 2. 在测试环境运行测试
    test_result = multi_env_manager.run_tests_in_environment('test', 'api_tests')

    # 3. 验证测试通过
    if test_result['pass_rate'] >= 95:
        # 4. 切换到公测环境
        multi_env_manager.activate_environment('staging')

        # 5. 在公测环境再次测试
        staging_result = multi_env_manager.run_tests_in_environment('staging', 'integration_tests')

        if staging_result['pass_rate'] >= 95:
            print("部署到生产环境")
        else:
            print("公测失败，停留在测试环境")
    else:
        print("测试未通过，保持在测试环境")

deploy_to_staging()
```

### 4. 沙盒隔离测试

```python
def test_new_feature():
    # 1. 创建专用沙盒
    sandbox_name = 'feature_test_sandbox'
    multi_env_manager.sandbox_manager.create_sandbox(sandbox_name, {
        'allow_execution': True,
        'memory_limit': '1GB',
        'network_isolated': True
    })

    # 2. 激活沙盒
    multi_env_manager.sandbox_manager.activate_sandbox(sandbox_name)

    # 3. 在沙盒中执行测试代码
    result = multi_env_manager.sandbox_manager.execute_in_sandbox(
        sandbox_name,
        '''
import sys
sys.path.insert(0, './app')

from app.ai.feature import new_feature
result = new_feature()
print(f"Feature test result: {result}")
        ''',
        timeout=60
    )

    # 4. 检查结果
    if result['success']:
        print("新功能测试通过！")
    else:
        print(f"测试失败: {result.get('error')}")

    # 5. 清理沙盒
    multi_env_manager.sandbox_manager.delete_sandbox(sandbox_name)
```

### 5. 数据影子同步

```python
def sync_production_to_test():
    # 1. 创建生产数据影子
    multi_env_manager.shadow_system.create_shadow(
        source='production',
        shadow_id='prod_to_test',
        config={
            'sync_interval': 3600,
            'anonymize': True,
            'sync_fields': ['users', 'products']
        }
    )

    # 2. 从影子获取数据
    prod_data = multi_env_manager.shadow_system.get_shadow_data('prod_to_test')

    # 3. 在测试环境使用
    multi_env_manager.activate_environment('test')

    # 4. 同步到测试影子
    multi_env_manager.shadow_system.sync_shadow('test_shadow', prod_data)

    print("数据已同步到测试环境")
```

## 仪表板

### 获取完整状态

```python
dashboard = multi_env_manager.get_dashboard()

print("当前环境:", dashboard['current_environment']['name'])
print("\n所有环境:")
for env in dashboard['environments']:
    status = "✓" if env['is_active'] else "○"
    print(f"  {status} {env['name']} ({env['id']})")

print("\n沙盒状态:")
print(f"  活跃沙盒: {dashboard['systems']['sandbox']['active_sandbox']}")

print("\n测试统计:")
stats = dashboard['systems']['test']['stats']
print(f"  总测试数: {stats['total_tests']}")
print(f"  通过率: {stats['overall_pass_rate']:.2f}%")
```

## 故障排除

### 问题1: 环境激活失败

```python
# 检查环境是否存在
if 'test' not in multi_env_manager.environments:
    print("环境不存在，需要注册")

# 检查环境配置
config = multi_env_manager.get_environment_config('test')
if not config:
    print("配置缺失")
```

### 问题2: 沙盒执行超时

```python
# 增加超时时间
result = multi_env_manager.sandbox_manager.execute_in_sandbox(
    'my_sandbox',
    'long_running_task()',
    timeout=120  # 增加到2分钟
)
```

### 问题3: 测试失败率高

```python
# 查看详细的测试结果
result = multi_env_manager.test_system.run_test('my_suite')

for test_result in result['results']:
    if test_result['status'] == 'failed':
        print(f"失败测试: {test_result['name']}")
        print(f"错误信息: {test_result.get('message', 'N/A')}")
```

## 性能优化

### 1. 禁用不必要的沙盒

```python
# 测试环境不需要沙盒
multi_env_manager.update_environment_config('test', {
    'use_sandbox': False
})
```

### 2. 缓存环境配置

```python
# 导出配置供快速加载
config_json = multi_env_manager.export_environment_config('prod')

# 以后可以快速导入
multi_env_manager.import_environment_config(config_json)
```

### 3. 定期清理旧沙盒

```python
# 清理所有非活跃沙盒
for sandbox in multi_env_manager.sandbox_manager.list_sandboxes():
    if sandbox['status'] != 'active':
        multi_env_manager.sandbox_manager.delete_sandbox(sandbox['id'])
```

## 安全考虑

### 1. 生产环境隔离

```python
# 确保生产环境配置
multi_env_manager.update_environment_config('prod', {
    'use_sandbox': False,
    'use_shadow': False,
    'allow_dev_tools': False,
    'ssl_required': True,
    'rate_limiting': True
})
```

### 2. 沙盒权限控制

```python
# 创建受限沙盒
multi_env_manager.sandbox_manager.create_sandbox('restricted_sandbox', {
    'allow_execution': False,  # 禁止代码执行
    'allow_network': False,     # 禁止网络访问
    'memory_limit': '256MB'     # 严格限制内存
})
```

### 3. 数据脱敏

```python
# 影子系统数据脱敏
multi_env_manager.shadow_system.create_shadow(
    source='prod',
    shadow_id='test_shadow',
    config={
        'anonymize': True,
        'fields_to_anonymize': ['email', 'phone', 'address']
    }
)
```

## 总结

多环境管理系统提供了：
- ✅ 统一的环境管理
- ✅ 完整的系统隔离
- ✅ 自动化测试集成
- ✅ 数据安全保障
- ✅ 灵活的配置管理
- ✅ 完整的API支持

通过合理使用这些功能，可以大大提高开发、测试和部署的效率与安全性。
