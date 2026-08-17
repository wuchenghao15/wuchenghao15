---
alwaysApply: true
description: MTSCOS AI系统操作规范 - AI员工、AI引擎、AI集群、AI阵列、AI神经元网络、AI脑库的升级、维护、修改规则
---
# MTSCOS AI 系统操作规范

## 1. 概述

### 1.1 文档目的
本文档定义MTSCOS AI系统中所有AI组件（AI员工、AI引擎、AI集群、AI阵列、AI神经元网络、AI脑库）的操作规则，包括创建、升级、维护、修改的标准流程和约束条件。所有AI相关操作必须优先参考并严格执行本规范。

### 1.2 AI系统架构

```text
MTSCOS AI系统
├── AI员工层 (AI Employees)
│   ├── AIEmployee 基类
│   ├── 专业AI员工（题库维护、诊断修复、Arduino开发等）
│   └── 智能赋能系统（性格模拟+网络学习）
├── AI引擎层 (AI Engines)
│   ├── LLM引擎
│   ├── TTS引擎
│   ├── 诊断修复引擎
│   └── 规则引擎
├── AI集群层 (AI Cluster)
│   ├── 集群管理器
│   ├── 员工分配调度
│   └── 集群配置持久化
├── AI阵列层 (AI Array)
│   ├── 阵列API
│   ├── 矩阵管理器
│   └── 分布式部署
├── AI神经元网络 (AI Neural Network)
│   ├── 深度学习模型
│   ├── 特征提取
│   └── 模型训练与推理
└── AI脑库 (AI Brain)
    ├── 知识存储
    ├── 知识检索
    ├── 知识验证
    └── 知识增强
```

### 1.3 核心原则

| 原则 | 说明 |
|------|------|
| **数据持久化优先** | 所有AI配置、状态、知识必须持久化到数据库 |
| **写穿机制** | 操作后立即同步到数据库，确保数据一致性 |
| **智能赋能统一** | 所有AI员工必须启用智能赋能（性格模拟+网络学习） |
| **权限控制** | AI操作必须遵循用户权限规则 |
| **日志记录** | 所有AI操作必须记录详细日志 |
| **向后兼容** | 修改必须保持向后兼容，不破坏现有功能 |
| **安全优先** | AI操作必须遵循VIKEY强制认证规则，确保系统安全 |
| **巡检驱动** | 所有系统操作必须纳入AI巡检闭环，支持自动检测和修复 |
| **法律准则合规** | 所有AI操作必须严格遵循法律准则文件规定，巡检引擎定期检查合规性 |
| **自动修复闭环** | 发现问题自动触发修复流程，修复结果记录到数据库并投喂脑库 |

---

## 2. AI员工操作规范

### 2.1 AI员工分类

| 类别 | 说明 | 示例 |
|------|------|------|
| **系统服务型** | 管理系统配置和监控 | 验证员工、路由员工、配置管理员工 |
| **业务专业型** | 处理特定业务领域 | 题库维护员工、政治题库员工、Arduino开发员工 |
| **诊断修复型** | 系统诊断和自动修复 | 诊断修复员工、规则库维护员工 |
| **学习支持型** | 辅助用户学习 | 听力报读员工、学习分析员工 |

### 2.2 AI员工创建规则

#### 2.2.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| employee_id | UUID格式 | `emp_001`、`emp_arduino_gen_001` |
| name | 中文描述性名称 | Arduino代码生成员工 |
| employee_type | 小写，下划线分隔 | `arduino_code_generator` |

#### 2.2.2 必须属性

| 属性 | 类型 | 说明 | 必填 |
|------|------|------|------|
| employee_id | str | 员工唯一标识 | ✅ |
| name | str | 员工名称 | ✅ |
| employee_type | str | 员工类型 | ✅ |
| level | int | 员工等级(1-10) | ✅ |
| status | str | 状态(active/idle/error) | ✅ |
| last_active | datetime | 最后活跃时间 | ✅ |

#### 2.2.3 智能赋能要求

所有AI员工必须启用智能赋能：

```python
def __init__(self, employee_id, name, employee_type="general", level=1):
    # ...基础属性初始化...
    
    # 智能赋能初始化 - 必须执行
    if EMPOWERMENT_AVAILABLE:
        from ai_engines.intelligent_empowerment import PersonalitySystem, NetworkLearningEngine
        
        ptype = _PERSONALITY_MAP.get(employee_type, 'analytical')
        domain = _DOMAIN_MAP.get(employee_type, 'general_programming')
        
        self.personality = PersonalitySystem(ptype)
        self.learning_engine = NetworkLearningEngine(employee_id, domain)
        self.empowerment_enabled = True
```

#### 2.2.4 注册流程

```text
1. 创建AI员工实例
2. 启用智能赋能
3. 注册到AIEmployeeManager
4. 持久化到数据库(ai_employees表)
5. 记录创建日志
```

### 2.3 AI员工升级规则

#### 2.3.1 升级触发条件

| 条件 | 说明 | 触发动作 |
|------|------|---------|
| 任务完成数达标 | 累计完成指定数量任务 | 等级提升 |
| 成功率达标 | 任务成功率达到阈值 | 等级提升 |
| 网络学习完成 | 完成指定学习周期 | 技能提升 |
| 管理员手动升级 | 管理员主动操作 | 等级提升 |

#### 2.3.2 升级流程

```text
1. 触发升级检查
2. 验证升级条件
3. 执行升级（等级+1，技能提升）
4. 更新数据库记录
5. 记录升级日志
6. 触发学习周期（可选）
```

#### 2.3.3 升级限制

| 限制项 | 规则 |
|--------|------|
| 最高等级 | 10级 |
| 每日升级次数 | 最多1次 |
| 等级差距 | 单次最多提升1级 |
| 降级保护 | 不会自动降级 |

### 2.4 AI员工维护规则

#### 2.4.1 状态管理

| 状态 | 说明 | 转换条件 |
|------|------|---------|
| active | 正常运行 | 初始化成功 |
| idle | 空闲等待 | 无任务时自动切换 |
| paused | 暂停 | 管理员操作 |
| error | 出错 | 任务失败超过阈值 |
| disabled | 禁用 | 管理员操作 |

#### 2.4.2 定期维护

| 维护项 | 频率 | 内容 |
|--------|------|------|
| 状态检查 | 每30分钟 | 检查所有员工状态 |
| 学习触发 | 每2小时 | 触发空闲员工学习 |
| 性能评估 | 每日 | 评估员工绩效 |
| 日志清理 | 每周 | 清理过期日志 |

#### 2.4.3 异常处理

```python
def handle_employee_error(employee, error):
    """处理AI员工异常"""
    # 1. 记录错误日志
    logger.error(f"AI员工 {employee.name} 异常: {error}")
    
    # 2. 更新状态
    employee.status = "error"
    employee.last_error = str(error)
    
    # 3. 尝试自动恢复
    if auto_recover_enabled:
        recovery_result = employee.recover()
        if recovery_result:
            employee.status = "active"
        else:
            # 4. 通知管理员
            notify_admin(f"AI员工 {employee.name} 恢复失败")
```

### 2.5 AI员工修改规则

#### 2.5.1 修改类型

| 修改类型 | 说明 | 需要审批 |
|----------|------|---------|
| 属性修改 | 修改名称、等级、配置 | ✅ |
| 技能修改 | 添加/删除技能 | ✅ |
| 类型修改 | 修改员工类型 | ❌（不允许） |
| ID修改 | 修改员工ID | ❌（不允许） |
| 删除 | 删除员工 | ✅ |

#### 2.5.2 修改流程

```text
1. 验证权限（必须super_admin或admin）
2. 备份当前配置
3. 执行修改
4. 同步到数据库
5. 记录修改日志
6. 验证修改结果
```

#### 2.5.3 修改限制

| 限制项 | 规则 |
|--------|------|
| ID不可修改 | employee_id一旦创建不可更改 |
| 类型不可修改 | employee_type不可更改，需重新创建 |
| 删除需确认 | 删除前必须确认并备份数据 |
| 级联影响 | 修改可能影响关联的集群配置 |

---

## 3. AI引擎操作规范

### 3.1 AI引擎分类

| 引擎类型 | 说明 | 文件位置 |
|----------|------|---------|
| LLM引擎 | 大语言模型调用 | ai_engines/llm_engine.py |
| TTS引擎 | 语音合成 | ai_engines/tts_engine.py |
| 诊断引擎 | 系统诊断 | ai_engines/diagnostics_engine.py |
| 规则引擎 | 规则匹配执行 | ai_engines/rule_engine.py |
| 学习引擎 | 网络自动学习 | ai_engines/intelligent_empowerment.py |
| 自动同步升级服务 | Git/GitHub自动同步与系统升级 | ai_engines/auto_sync_upgrade_service.py |
| 自动阅卷引擎 | 作业/考试自动批改 | ai_engines/homework_grading_engine.py |
| 考试组卷引擎 | AI自动组卷系统 | exam_generator.py |

### 3.2 AI引擎配置规则

#### 3.2.1 配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| model_type | 模型类型(local/remote) | local |
| model_name | 模型名称 | deepseek |
| temperature | 温度参数 | 0.7 |
| max_tokens | 最大生成token数 | 2000 |
| timeout | 请求超时(秒) | 30 |
| cache_enabled | 缓存启用 | True |
| rate_limit | 调用频率限制 | 100/分钟 |

#### 3.2.2 配置持久化

所有引擎配置必须存储到数据库：

```python
def save_engine_config(engine_type, config):
    """保存引擎配置到数据库"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO ai_engine_config 
            (engine_type, config, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (engine_type, json.dumps(config)))
        conn.commit()
```

### 3.3 AI引擎升级规则

#### 3.3.1 升级类型

| 升级类型 | 说明 | 示例 |
|----------|------|------|
| 模型升级 | 更新LLM模型版本 | deepseek-v1 → deepseek-v2 |
| 参数调优 | 调整引擎参数 | temperature调整 |
| 功能扩展 | 添加新功能 | 支持多语言TTS |
| 性能优化 | 优化执行效率 | 添加缓存机制 |

#### 3.3.2 升级流程

```text
1. 备份当前配置
2. 测试环境验证升级
3. 执行升级
4. 生产环境灰度发布
5. 监控运行状态
6. 记录升级日志
```

#### 3.3.3 回滚机制

```python
def rollback_engine(engine_type, version):
    """回滚引擎到指定版本"""
    # 1. 读取历史配置
    config = get_history_config(engine_type, version)
    
    # 2. 应用历史配置
    apply_engine_config(engine_type, config)
    
    # 3. 验证回滚结果
    if not verify_engine(engine_type):
        # 回滚失败，继续回滚到上一版本
        rollback_engine(engine_type, version - 1)
```

### 3.4 自动同步升级服务规范

#### 3.4.1 服务职责

| 职责 | 说明 |
|------|------|
| Git同步 | 自动同步本地代码与GitHub仓库 |
| 升级检测 | 检测远程仓库更新并触发升级 |
| 数据库迁移 | 执行数据库schema升级和数据迁移 |
| AI员工升级 | 自动升级AI员工等级和技能 |
| 同步记录 | 记录所有同步和升级操作历史 |

#### 3.4.2 同步规则

| 规则 | 说明 |
|------|------|
| 同步频率 | 默认每30分钟自动同步一次 |
| 强制同步 | 支持手动触发强制同步 |
| 冲突处理 | 自动提交本地更改后拉取远程更新 |
| 分支管理 | 默认使用main分支进行同步 |
| 升级互斥 | 升级进行中禁止同步操作 |

#### 3.4.3 升级触发条件

| 条件 | 说明 | 触发动作 |
|------|------|---------|
| 远程有新提交 | GitHub仓库有新的commit | 自动拉取并升级 |
| 版本号变更 | 检测到版本号增加 | 执行完整升级流程 |
| 数据库迁移脚本 | 存在新的迁移脚本 | 执行数据库迁移 |
| 管理员手动触发 | 管理员执行升级命令 | 立即执行升级 |

#### 3.4.4 升级流程

```text
1. 检测远程更新
2. 备份当前代码和数据库
3. 拉取远程代码
4. 执行数据库迁移
5. 升级AI员工配置
6. 更新系统版本号
7. 验证升级结果
8. 记录升级日志
```

### 3.5 AI引擎维护规则

#### 3.5.1 健康检查

| 检查项 | 频率 | 检查内容 |
|--------|------|---------|
| 连接状态 | 每1分钟 | LLM/TTS服务可达性 |
| 响应时间 | 每5分钟 | 平均响应时间监控 |
| 错误率 | 每10分钟 | 错误率统计 |
| 资源使用 | 每30分钟 | CPU/内存/GPU使用率 |

#### 3.4.2 日志记录

所有引擎调用必须记录日志：

```python
def log_engine_call(engine_type, prompt, response, latency):
    """记录引擎调用日志"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ai_engine_logs 
            (engine_type, prompt_hash, response_status, latency, timestamp)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (engine_type, hash(prompt)[:16], response.status_code, latency))
        conn.commit()
```

---

## 4. AI集群操作规范

### 4.1 AI集群架构

```text
AI集群
├── 集群配置 (ai_cluster_config)
│   ├── cluster_id
│   ├── cluster_type
│   ├── config (JSON)
│   └── status
├── 员工配置 (ai_employee_config)
│   ├── employee_id
│   ├── employee_type
│   ├── capabilities
│   └── assigned_cluster
└── 集群-员工关联 (ai_cluster_employee)
    ├── cluster_id
    └── employee_id
```

### 4.2 AI集群创建规则

#### 4.2.1 集群类型

| 类型 | 说明 | 适用场景 |
|------|------|---------|
| system | 系统集群 | 系统管理任务 |
| business | 业务集群 | 业务处理任务 |
| learning | 学习集群 | AI学习任务 |
| monitoring | 监控集群 | 系统监控任务 |

#### 4.2.2 创建流程

```text
1. 验证权限（必须super_admin）
2. 生成cluster_id
3. 设置集群配置
4. 保存到数据库
5. 分配初始员工
6. 启动集群监控
```

### 4.3 AI集群升级规则

#### 4.3.1 升级内容

| 升级项 | 说明 |
|--------|------|
| 配置升级 | 更新集群配置参数 |
| 员工扩容 | 添加新员工到集群 |
| 员工升级 | 升级集群内员工等级 |
| 架构升级 | 改变集群拓扑结构 |

#### 4.3.2 升级流程

```text
1. 评估集群状态
2. 制定升级计划
3. 备份当前配置
4. 执行升级操作
5. 验证升级结果
6. 记录升级日志
```

### 4.4 AI集群维护规则

#### 4.4.1 集群状态监控

| 监控项 | 频率 | 告警条件 |
|--------|------|---------|
| 员工在线率 | 每5分钟 | <90%告警 |
| 任务成功率 | 每10分钟 | <95%告警 |
| 响应时间 | 每15分钟 | >5秒告警 |
| 资源使用率 | 每30分钟 | CPU>80%告警 |

#### 4.4.2 故障处理

```python
def handle_cluster_failure(cluster_id, employee_id):
    """处理集群故障"""
    # 1. 标记员工状态为error
    update_employee_status(employee_id, "error")
    
    # 2. 查找备用员工
    backup_employee = find_backup_employee(cluster_id, get_employee_type(employee_id))
    
    # 3. 切换到备用员工
    if backup_employee:
        assign_employee_to_cluster(backup_employee.id, cluster_id)
        logger.info(f"集群 {cluster_id} 故障切换完成")
    else:
        # 4. 通知管理员
        notify_admin(f"集群 {cluster_id} 无备用员工")
```

### 4.5 AI集群修改规则

#### 4.5.1 修改类型

| 修改类型 | 说明 | 需要审批 |
|----------|------|---------|
| 配置修改 | 修改集群配置 | ✅ |
| 员工分配 | 添加/移除员工 | ✅ |
| 状态修改 | 启动/停止集群 | ✅ |
| 删除集群 | 删除整个集群 | ✅ |

#### 4.5.2 修改限制

| 限制项 | 规则 |
|--------|------|
| 系统集群保护 | system类型集群不可删除 |
| 员工依赖检查 | 删除员工前检查是否有任务依赖 |
| 级联操作 | 删除集群会解除员工关联但不删除员工 |

---

## 5. AI阵列操作规范

### 5.1 AI阵列架构

```text
AI阵列
├── 阵列矩阵 (Cluster Matrix)
│   ├── 阵列节点
│   ├── 节点状态
│   └── 节点通信
├── 阵列API
│   ├── 阵列管理接口
│   ├── 节点控制接口
│   └── 状态查询接口
└── 分布式部署
    ├── 多节点协同
    ├── 负载均衡
    └── 故障转移
```

### 5.2 AI阵列创建规则

#### 5.2.1 阵列配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| array_size | 阵列节点数 | 4 |
| redundancy_level | 冗余级别 | 2 |
| load_balancing | 负载均衡策略 | round_robin |
| communication_protocol | 通信协议 | http |

#### 5.2.2 创建流程

```text
1. 验证硬件资源
2. 配置阵列节点
3. 建立节点通信
4. 初始化负载均衡
5. 验证阵列状态
6. 记录创建日志
```

### 5.3 AI阵列升级规则

#### 5.3.1 升级类型

| 升级类型 | 说明 |
|----------|------|
| 扩容 | 增加阵列节点数 |
| 缩容 | 减少阵列节点数 |
| 节点升级 | 升级单个节点配置 |
| 协议升级 | 更新通信协议 |

#### 5.3.2 滚动升级

```python
def rolling_upgrade(array_id):
    """滚动升级阵列节点"""
    nodes = get_array_nodes(array_id)
    
    for node in nodes:
        # 1. 标记节点为维护状态
        set_node_status(node.id, "maintenance")
        
        # 2. 转移节点负载
        transfer_load(node.id)
        
        # 3. 执行升级
        upgrade_node(node.id)
        
        # 4. 验证节点状态
        if verify_node(node.id):
            set_node_status(node.id, "active")
        else:
            # 回滚并告警
            rollback_node(node.id)
            notify_admin(f"节点 {node.id} 升级失败")
```

### 5.4 AI阵列维护规则

#### 5.4.1 节点健康检查

| 检查项 | 频率 | 检查内容 |
|--------|------|---------|
| 节点存活 | 每30秒 | 心跳检测 |
| 通信延迟 | 每1分钟 | 节点间通信延迟 |
| 负载状态 | 每5分钟 | CPU/内存/网络使用率 |
| 同步状态 | 每10分钟 | 数据同步状态 |

#### 5.4.2 故障转移

```python
def failover(array_id, failed_node_id):
    """阵列故障转移"""
    # 1. 检测故障节点
    if not is_node_alive(failed_node_id):
        # 2. 标记节点为故障
        set_node_status(failed_node_id, "failed")
        
        # 3. 选择备用节点
        backup_node = select_backup_node(array_id, failed_node_id)
        
        # 4. 转移服务
        transfer_services(failed_node_id, backup_node.id)
        
        # 5. 更新路由
        update_route(failed_node_id, backup_node.id)
        
        # 6. 通知管理员
        notify_admin(f"节点 {failed_node_id} 故障转移到 {backup_node.id}")
```

---

## 6. AI神经元网络操作规范

### 6.1 神经元网络架构

```text
AI神经元网络
├── 模型层
│   ├── 深度学习模型定义
│   ├── 预训练权重
│   └── 模型版本管理
├── 训练层
│   ├── 训练数据准备
│   ├── 训练过程监控
│   └── 训练结果评估
├── 推理层
│   ├── 推理接口
│   ├── 批处理支持
│   └── 推理缓存
└── 特征层
    ├── 特征提取
    ├── 特征存储
    └── 特征更新
```

### 6.2 模型管理规则

#### 6.2.1 模型版本控制

| 版本类型 | 说明 | 示例 |
|----------|------|------|
| 开发版 | 开发中的模型 | v0.1-dev |
| 测试版 | 测试验证中的模型 | v0.1-beta |
| 稳定版 | 生产环境使用 | v0.1 |
| 升级版本 | 迭代升级 | v0.2 |

#### 6.2.2 模型存储

```python
def save_model(model_name, model, version, metadata):
    """保存模型到存储"""
    # 1. 创建版本目录
    version_dir = f"models/{model_name}/{version}"
    os.makedirs(version_dir, exist_ok=True)
    
    # 2. 保存模型权重
    model.save(f"{version_dir}/model.h5")
    
    # 3. 保存元数据
    with open(f"{version_dir}/metadata.json", "w") as f:
        json.dump(metadata, f)
    
    # 4. 更新数据库记录
    update_model_version(model_name, version, metadata)
```

### 6.3 训练规则

#### 6.3.1 训练流程

```text
1. 数据准备（清洗、标注、划分）
2. 模型初始化（加载预训练权重）
3. 训练执行（监控损失、精度）
4. 验证评估（验证集评估）
5. 模型保存（保存最佳权重）
6. 部署上线（测试后部署）
```

#### 6.3.2 训练监控

| 监控项 | 说明 | 告警条件 |
|--------|------|---------|
| 损失值 | 训练损失变化 | 损失激增告警 |
| 精度 | 验证精度 | 精度下降告警 |
| 过拟合 | 训练/验证差距 | 差距>20%告警 |
| 资源使用 | GPU/内存 | 使用率>90%告警 |

### 6.4 推理规则

#### 6.4.1 推理接口

```python
@app.route('/api/ai/inference', methods=['POST'])
def inference():
    """AI推理接口"""
    data = request.json
    model_name = data.get('model_name')
    input_data = data.get('input')
    
    # 1. 验证权限
    if not has_permission('ai_inference'):
        return jsonify({'error': '权限不足'}), 403
    
    # 2. 加载模型
    model = load_model(model_name)
    
    # 3. 执行推理
    result = model.predict(input_data)
    
    # 4. 记录推理日志
    log_inference(model_name, input_data, result)
    
    return jsonify({'result': result})
```

#### 6.4.2 推理缓存

| 缓存策略 | 说明 | 适用场景 |
|----------|------|---------|
| 输入缓存 | 缓存相同输入的结果 | 高频重复查询 |
| 批次缓存 | 缓存批次处理结果 | 批量推理 |
| 时间缓存 | 缓存一段时间内结果 | 实时性要求低 |

---

## 7. AI脑库操作规范

### 7.1 AI脑库架构

```text
AI脑库
├── 知识库 (Knowledge Base)
│   ├── 知识条目
│   ├── 知识分类
│   └── 知识标签
├── 知识服务
│   ├── 知识添加
│   ├── 知识检索
│   └── 知识验证
├── 知识增强
│   ├── 知识关联
│   ├── 知识更新
│   └── 知识质量评估
└── 知识统计
    ├── 知识数量统计
    ├── 知识使用统计
    └── 知识增长统计
```

### 7.2 知识管理规则

#### 7.2.1 知识分类

| 分类 | 说明 | 示例 |
|------|------|------|
| system | 系统知识 | 系统配置、操作规范 |
| business | 业务知识 | 题库数据、课程内容 |
| technical | 技术知识 | 编程知识、算法知识 |
| learning | 学习知识 | 学习方法、教育理论 |
| domain | 领域知识 | 政治知识、日语知识 |

#### 7.2.2 知识格式

```json
{
    "knowledge_id": "kb_001",
    "title": "马克思主义基本原理",
    "content": "马克思主义哲学认为，物质是世界的本原...",
    "knowledge_type": "domain",
    "source": "system",
    "tags": ["政治", "马克思主义", "哲学"],
    "priority": 1,
    "status": "validated",
    "created_at": "2026-07-15T09:00:00",
    "updated_at": "2026-07-15T09:00:00"
}
```

#### 7.2.3 知识添加流程

```text
1. 验证知识格式
2. 检查知识重复
3. 添加到知识库
4. 触发知识验证
5. 更新知识统计
6. 记录操作日志
```

### 7.3 知识验证规则

#### 7.3.1 验证类型

| 验证类型 | 说明 | 方法 |
|----------|------|------|
| 格式验证 | 检查知识格式正确性 | 自动验证 |
| 内容验证 | 检查内容准确性 | AI验证 |
| 重复验证 | 检查是否重复 | 相似度比对 |
| 质量验证 | 评估知识质量 | 质量评分 |

#### 7.3.2 验证流程

```python
def validate_knowledge(knowledge_id):
    """验证知识"""
    knowledge = get_knowledge(knowledge_id)
    
    # 1. 格式验证
    if not validate_format(knowledge):
        return {"status": "invalid", "reason": "格式错误"}
    
    # 2. 重复验证
    if check_duplicate(knowledge):
        return {"status": "duplicate", "reason": "内容重复"}
    
    # 3. AI内容验证
    ai_result = ai_validate_content(knowledge.content)
    if not ai_result["valid"]:
        return {"status": "invalid", "reason": ai_result["reason"]}
    
    # 4. 更新状态
    update_knowledge_status(knowledge_id, "validated")
    
    return {"status": "validated"}
```

### 7.4 知识检索规则

#### 7.4.1 检索方式

| 方式 | 说明 | 适用场景 |
|------|------|---------|
| 关键词检索 | 按关键词搜索 | 精确匹配 |
| 语义检索 | 语义相似度匹配 | 模糊匹配 |
| 分类检索 | 按分类筛选 | 分类浏览 |
| 标签检索 | 按标签筛选 | 标签过滤 |

#### 7.4.2 检索接口

```python
@app.route('/api/ai/brain/search', methods=['GET'])
def search_knowledge():
    """知识检索接口"""
    query = request.args.get('query')
    category = request.args.get('category')
    tags = request.args.getlist('tags')
    
    # 1. 构建检索条件
    conditions = []
    if query:
        conditions.append(f"content LIKE '%{query}%'")
    if category:
        conditions.append(f"knowledge_type = '{category}'")
    if tags:
        conditions.append(f"tags IN ({','.join(tags)})")
    
    # 2. 执行检索
    results = execute_search(conditions)
    
    # 3. 记录检索日志
    log_search(query, results)
    
    return jsonify(results)
```

### 7.5 知识增强规则

#### 7.5.1 增强类型

| 增强类型 | 说明 | 触发条件 |
|----------|------|---------|
| 自动更新 | 定期更新过期知识 | 知识超过有效期 |
| 知识关联 | 建立知识间关联 | 新增知识时 |
| 质量提升 | 提升低质量知识 | 质量评分低于阈值 |
| 知识扩展 | 扩展知识内容 | 用户请求扩展 |

#### 7.5.2 增强流程

```python
def enhance_knowledge(knowledge_id):
    """增强知识"""
    knowledge = get_knowledge(knowledge_id)
    
    # 1. 检查是否需要更新
    if is_expired(knowledge):
        updated_content = ai_update_content(knowledge.content)
        update_knowledge(knowledge_id, updated_content)
    
    # 2. 建立知识关联
    related_knowledge = find_related(knowledge)
    for rel in related_knowledge:
        add_knowledge_link(knowledge_id, rel["knowledge_id"])
    
    # 3. 质量评估与提升
    quality_score = evaluate_quality(knowledge)
    if quality_score < 0.6:
        enhanced_content = ai_enhance_content(knowledge.content)
        update_knowledge(knowledge_id, enhanced_content)
```

---

## 8. 例行维护规则

### 8.1 维护规则总览

系统例行维护规则统一存储在 `system_rules` 表中，规则类型为 `maintenance`，所有维护操作必须严格遵循以下规则执行。

### 8.2 AI员工维护规则

| 规则代码 | 规则名称 | 默认值(秒) | 说明 |
|----------|----------|-----------|------|
| MAINT_EMPLOYEE_STATUS_CHECK | AI员工状态检查频率 | 1800 | 每30分钟检查所有员工状态 |
| MAINT_EMPLOYEE_LEARNING_TRIGGER | AI员工学习触发频率 | 7200 | 每2小时触发空闲员工学习 |
| MAINT_EMPLOYEE_PERFORMANCE_EVAL | AI员工性能评估频率 | 86400 | 每日评估员工绩效 |
| MAINT_EMPLOYEE_LOG_CLEANUP | AI员工日志清理频率 | 604800 | 每周清理过期日志 |

### 8.3 AI引擎维护规则

| 规则代码 | 规则名称 | 默认值(秒) | 说明 |
|----------|----------|-----------|------|
| MAINT_ENGINE_HEALTH_CHECK | AI引擎健康检查频率 | 60 | 每1分钟检查LLM/TTS服务可达性 |
| MAINT_ENGINE_RESPONSE_TIME | AI引擎响应时间监控频率 | 300 | 每5分钟监控平均响应时间 |
| MAINT_ENGINE_ERROR_RATE | AI引擎错误率监控频率 | 600 | 每10分钟统计错误率 |
| MAINT_ENGINE_RESOURCE_USAGE | AI引擎资源使用监控频率 | 1800 | 每30分钟监控CPU/内存/GPU使用率 |

### 8.4 AI集群维护规则

| 规则代码 | 规则名称 | 默认值(秒) | 说明 |
|----------|----------|-----------|------|
| MAINT_CLUSTER_ONLINE_RATE | AI集群员工在线率监控频率 | 300 | 每5分钟检查在线率，<90%告警 |
| MAINT_CLUSTER_TASK_SUCCESS_RATE | AI集群任务成功率监控频率 | 600 | 每10分钟检查成功率，<95%告警 |
| MAINT_CLUSTER_RESPONSE_TIME | AI集群响应时间监控频率 | 900 | 每15分钟监控响应时间，>5秒告警 |
| MAINT_CLUSTER_RESOURCE_USAGE | AI集群资源使用率监控频率 | 1800 | 每30分钟监控资源使用率，CPU>80%告警 |

### 8.5 AI阵列维护规则

| 规则代码 | 规则名称 | 默认值(秒) | 说明 |
|----------|----------|-----------|------|
| MAINT_ARRAY_NODE_ALIVE | AI阵列节点存活检测频率 | 30 | 每30秒心跳检测 |
| MAINT_ARRAY_COMMUNICATION_DELAY | AI阵列通信延迟检测频率 | 60 | 每1分钟检测节点间通信延迟 |
| MAINT_ARRAY_LOAD_STATUS | AI阵列负载状态检测频率 | 300 | 每5分钟检测CPU/内存/网络使用率 |
| MAINT_ARRAY_SYNC_STATUS | AI阵列同步状态检测频率 | 600 | 每10分钟检测数据同步状态 |

### 8.6 系统级维护规则

| 规则代码 | 规则名称 | 默认值(秒) | 说明 |
|----------|----------|-----------|------|
| MAINT_GIT_SYNC_INTERVAL | Git自动同步频率 | 1800 | 每30分钟自动同步Git和GitHub |
| MAINT_DATABASE_BACKUP | 数据库备份频率 | 86400 | 每日备份数据库 |
| MAINT_LOG_CLEANUP | 系统日志清理频率 | 604800 | 每周清理过期日志 |
| MAINT_PERFORMANCE_REPORT | 性能报告生成频率 | 2592000 | 每月生成性能报告 |

### 8.7 维护功能开关

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| MAINT_AUTO_RECOVER_ENABLED | 自动恢复启用 | 1 | 是否启用自动恢复功能 |
| MAINT_AUTO_REPAIR_ENABLED | 自动修复启用 | 1 | 是否启用自动修复功能 |
| MAINT_PERFORMANCE_TUNING_ENABLED | 性能调优启用 | 1 | 是否启用性能调优功能 |
| MAINT_AUDIT_LOG_ENABLED | 审计日志启用 | 1 | 是否启用审计日志 |

### 8.8 维护执行流程

```text
1. AI管家定时检查维护规则配置
2. 根据规则频率触发对应维护任务
3. 执行维护操作（状态检查、日志清理、性能评估等）
4. 记录维护操作日志到 system_maintenance_logs 表
5. 发现异常触发自动恢复或通知管理员
6. 生成维护报告
```

### 8.9 维护日志记录

所有维护操作必须记录日志：

```python
def log_maintenance_operation(operation_type, target, result, details):
    """记录维护操作日志"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO system_maintenance_logs 
            (operation_type, target, result, details, timestamp)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (operation_type, target, result, json.dumps(details)))
        conn.commit()
```

### 8.10 版本号更新规则

#### 8.10.1 版本号格式规范

系统采用语义化版本号（Semantic Versioning）格式：

```text
{major}.{minor}.{patch}
```

| 字段 | 说明 | 递增条件 |
|------|------|---------|
| major | 主版本号 | 重大架构变更、不兼容升级 |
| minor | 次版本号 | 新增功能、向后兼容升级 |
| patch | 修订版本号 | Bug修复、例行维护升级 |

#### 8.10.2 版本号维护规则

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| MAINT_VERSION_CHECK_INTERVAL | 版本号检查频率 | 3600 | 版本号检查间隔(秒) |
| MAINT_VERSION_AUTO_INCREMENT_ENABLED | 版本号自动递增启用 | 1 | 是否启用版本号自动递增 |
| MAINT_VERSION_FORMAT | 版本号格式 | major.minor.patch | 版本号格式规范 |
| MAINT_VERSION_INCREMENT_ON_UPGRADE | 升级时版本递增 | 1 | 升级成功后是否自动递增版本号 |
| MAINT_VERSION_INCREMENT_TYPE | 版本递增类型 | patch | 默认版本递增类型 |
| MAINT_VERSION_HISTORY_ENABLED | 版本历史记录启用 | 1 | 是否启用版本历史记录 |

#### 8.10.3 版本号递增触发条件

| 触发条件 | 递增类型 | 示例 |
|----------|---------|------|
| 重大架构变更 | major | 10.0.0 → 11.0.0 |
| 新增功能模块 | minor | 10.0.0 → 10.1.0 |
| 修复Bug | patch | 10.0.0 → 10.0.1 |
| 例行维护升级 | patch | 10.0.1 → 10.0.2 |
| Git同步检测到新提交 | patch | 10.0.2 → 10.0.3 |

#### 8.10.4 版本号获取优先级

版本号获取遵循以下优先级顺序：

```text
1. 从 system_rules 表读取 SYS_VERSION 规则值
2. 从 Git commit hash 获取（作为fallback）
3. 返回 'unknown'（兜底）
```

#### 8.10.5 版本号更新流程

```text
1. 升级流程执行完成并验证成功
2. 检查 MAINT_VERSION_AUTO_INCREMENT_ENABLED 是否启用
3. 读取 MAINT_VERSION_INCREMENT_TYPE 获取递增类型
4. 解析当前版本号，按类型递增对应位
5. 更新 system_rules 表中的 SYS_VERSION 规则值
6. 记录升级历史到 upgrade_history 表
7. 记录维护日志到 system_maintenance_logs 表
```

#### 8.10.6 版本号递增代码示例

```python
def _increment_version(self, increment_type='patch'):
    """递增版本号"""
    current_version = self._get_current_version()
    
    parts = current_version.split('.')
    if len(parts) >= 3:
        major, minor, patch = map(int, parts[:3])
        
        if increment_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif increment_type == 'minor':
            minor += 1
            patch = 0
        else:
            patch += 1
        
        new_version = f"{major}.{minor}.{patch}"
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE system_rules 
                SET rule_value = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE rule_code = ?
            ''', (new_version, 'SYS_VERSION'))
            conn.commit()
        ```
        return new_version
```text

### 8.11 灰度发布规则

#### 8.11.1 灰度发布概述

灰度发布（Gray Release）是一种渐进式发布策略，将新版本先部署到一小部分用户进行验证，确认稳定后再逐步扩大范围，最终全量发布。这种方式可以有效降低新版本发布带来的风险。

#### 8.11.2 灰度发布规则配置

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| GRAY_RELEASE_ENABLED | 灰度发布启用 | 1 | 是否启用灰度发布功能 |
| GRAY_RELEASE_PERCENTAGE | 初始灰度比例 | 10 | 初始灰度发布用户比例(%) |
| GRAY_HEALTH_CHECK_INTERVAL | 健康检查间隔 | 60 | 灰度环境健康检查间隔(秒) |
| GRAY_HEALTH_CHECK_DURATION | 健康检查持续时间 | 300 | 灰度健康检查持续时间(秒) |
| GRAY_AUTO_ROLLBACK_THRESHOLD | 自动回滚错误率阈值 | 5 | 错误率超过此阈值自动回滚(%) |
| GRAY_AUTO_ROLLBACK_LATENCY | 自动回滚延迟阈值 | 5000 | 响应时间超过此阈值自动回滚(毫秒) |
| GRAY_DURATION | 灰度发布持续时间 | 3600 | 单次灰度发布持续时间(秒) |
| GRAY_PROMOTE_INTERVAL | 放量检查间隔 | 1800 | 灰度放量检查间隔(秒) |
| GRAY_PROMOTE_STEPS | 放量步骤 | 10,30,50,70,100 | 灰度放量步骤百分比列表 |
| GRAY_ENVIRONMENT_URL | 灰度环境URL | - | 灰度测试环境访问地址 |
| GRAY_NOTIFY_ADMIN_ENABLED | 通知管理员 | 1 | 灰度发布时是否通知管理员 |
| GRAY_ROLLBACK_ON_FAILURE | 失败时自动回滚 | 1 | 灰度发布失败时是否自动回滚 |

#### 8.11.3 灰度发布流程

```
1. 升级准备（数据库迁移、AI员工升级、配置更新、缓存清理）
2. 检查GRAY_RELEASE_ENABLED是否启用
3. 部署到灰度环境
4. 灰度健康检查（错误率、延迟监控）
   - 错误率超过阈值 → 自动回滚
   - 延迟超过阈值 → 自动回滚
5. 灰度放量（按步骤逐步扩大用户范围）
   - 10% → 30% → 50% → 70% → 100%
   - 每步检查错误率，异常则回滚
6. 全量发布到生产环境
7. 服务重启
8. 版本号递增（仅在灰度发布成功后）
9. 记录升级历史和维护日志
```text

#### 8.11.4 灰度健康检查标准

| 检查项 | 阈值 | 处理方式 |
|--------|------|---------|
| 错误率 | >5% | 自动回滚 |
| 平均响应时间 | >5000ms | 自动回滚 |
| 服务可用性 | <99% | 自动回滚 |
| CPU使用率 | >80% | 告警 |
| 内存使用率 | >85% | 告警 |

#### 8.11.5 灰度放量策略

| 步骤 | 用户比例 | 间隔时间 | 说明 |
|------|---------|---------|------|
| Step 1 | 10% | 30分钟 | 初始验证 |
| Step 2 | 30% | 30分钟 | 小规模验证 |
| Step 3 | 50% | 30分钟 | 中等规模验证 |
| Step 4 | 70% | 30分钟 | 大规模验证 |
| Step 5 | 100% | - | 全量发布 |

#### 8.11.6 灰度发布与版本号联动规则

| 场景 | 版本号处理 |
|------|-----------|
| 灰度发布成功 | 版本号自动递增 |
| 灰度发布失败但未回滚 | 版本号保持不变 |
| 灰度发布失败并自动回滚 | 版本号保持不变，记录回滚日志 |
| 灰度发布被手动终止 | 版本号保持不变 |

#### 8.11.7 灰度发布代码示例

```python
def _perform_gray_release(self):
    """执行灰度发布"""
    gray_steps = [
        ('部署到灰度环境', self._deploy_to_gray),
        ('灰度健康检查', self._check_gray_health),
        ('灰度放量', self._promote_gray),
        ('全量发布', self._promote_to_production)
    ]
    
    for step_name, step_func in gray_steps:
        step_result = step_func()
        if not step_result['success']:
            auto_rollback = self.get_setting('GRAY_ROLLBACK_ON_FAILURE')
            if auto_rollback in ('true', '1'):
                self._rollback_gray()
                return {'success': False, 'auto_rollback': True}
            return {'success': False, 'auto_rollback': False}
    
    return {'success': True}
```text

### 8.12 用户权限规则

#### 8.12.1 角色等级定义

| 角色 | 等级 | 说明 |
|------|------|------|
| super_admin | 100 | 超级管理员，拥有所有权限 |
| system_admin | 90 | 系统管理员，管理系统配置 |
| admin | 80 | 管理员，管理用户和内容 |
| hardware_admin | 75 | 硬件管理员，调试环境访问 |
| hardware_vikey_admin | 75 | 硬件Vikey管理员，调试环境访问 |
| designer | 70 | 设计师，课程设计 |
| teacher | 60 | 教师，教学管理 |
| student_vip | 50 | VIP学生，高级学习功能 |
| student | 40 | 普通学生，基础学习功能 |
| user | 20 | 普通用户，基本访问 |
| guest | 0 | 访客，无权限 |

#### 8.12.2 角色权限矩阵

| 权限 | super_admin | system_admin | admin | hardware_admin | hardware_vikey_admin | designer | teacher | student_vip | student | user | guest |
|------|------------|-------------|-------|----------------|---------------------|----------|---------|-------------|---------|------|-------|
| * (全部) | ✓ | | | | | | | | | | |
| manage_users | ✓ | ✓ | ✓ | | | | | | | | |
| manage_exams | ✓ | ✓ | ✓ | | | | ✓ | | | | |
| manage_courses | ✓ | ✓ | ✓ | | | ✓ | | | | | |
| manage_settings | ✓ | ✓ | ✓ | | | | | | | | |
| view_users | ✓ | ✓ | ✓ | | | | | | | | |
| view_exams | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | |
| view_courses | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | |
| view_settings | ✓ | ✓ | ✓ | | | | | | | | |
| view_notifications | ✓ | ✓ | ✓ | | | | ✓ | | | | |
| view_data_analysis | ✓ | ✓ | ✓ | | | | | | | | |
| view_ai_center | ✓ | ✓ | ✓ | | | | | | | | |
| view_resource_manager | ✓ | | ✓ | | | | | | | | |
| view_monitor | ✓ | | ✓ | ✓ | ✓ | | | | | | |
| view_health_monitor | ✓ | | ✓ | | | | | | | | |
| view_profile | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| view_students | ✓ | ✓ | ✓ | | | | ✓ | | | | |
| view_ai_tutor | ✓ | ✓ | ✓ | | | | | ✓ | | | |

#### 8.12.3 权限维护规则

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| PERM_CHECK_INTERVAL | 权限检查间隔 | 3600 | 权限缓存检查间隔(秒) |
| PERM_CACHE_REFRESH_ENABLED | 权限缓存刷新启用 | 1 | 是否启用权限缓存自动刷新 |
| PERM_ROLE_HIERARCHY_ENABLED | 角色层级启用 | 1 | 是否启用角色层级继承 |
| PERM_AUDIT_ENABLED | 权限审计启用 | 1 | 是否启用权限操作审计 |
| PERM_AUTO_SYNC_ENABLED | 权限自动同步启用 | 1 | 是否启用权限规则自动同步 |
| PERM_EDUCATION_TYPE_FILTER_ENABLED | 教育类型权限过滤启用 | 1 | 是否启用按教育类型过滤考试权限 |
| PERM_K12_RESTRICTION_ENABLED | K12权限限制启用 | 1 | 是否启用K12学生考试权限限制 |
| PERM_HARDWARE_ADMIN_DEBUG_ENABLED | 硬件管理员调试权限启用 | 1 | 是否启用硬件管理员调试环境权限 |
| PERM_MAX_LOGIN_ATTEMPTS | 最大登录尝试次数 | 5 | 允许的最大登录尝试次数 |
| PERM_LOCKOUT_DURATION | 账户锁定时长 | 900 | 账户锁定时长(秒) |
| PERM_PASSWORD_MIN_LENGTH | 密码最小长度 | 8 | 密码最小长度 |
| PERM_PASSWORD_COMPLEXITY_ENABLED | 密码复杂度启用 | 1 | 是否启用密码复杂度要求 |
| PERM_SUPER_ADMIN_UNIQUE_USER | 超级管理员唯一用户 | wuchenghao15 | 系统超级管理员唯一用户，有且仅有此用户拥有super_admin角色 |

#### 8.12.4 考试准入条件

| 角色 | 可参加的考试科目 | 特殊权限 |
|------|-----------------|---------|
| student (K12) | 数学、语文、英语、物理、化学、政治 | 仅能参加K12相关考试 |
| student_vip (K12) | 数学、语文、英语、物理、化学、政治 | 仅能参加K12相关考试，VIP特权 |
| student (成人) | 所有科目（含日语、职业资格等） | 无限制 |
| teacher | 所有科目 | 可查看考试结果 |
| admin | 所有科目 | 可管理考试 |
| hardware_admin | 所有科目 | 调试环境访问权限 |
| hardware_vikey_admin | 所有科目 | 调试环境访问权限 |

#### 8.12.5 权限检查流程

```
1. 用户登录时验证身份
2. 根据用户角色加载权限列表
3. 权限列表缓存到session
4. 访问资源时检查权限缓存
5. 权限变更时刷新缓存
6. 记录权限操作审计日志
```text

#### 8.12.6 权限缓存策略

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| Session缓存 | 权限缓存到用户session | 登录用户 |
| 全局缓存 | 权限规则缓存到内存 | 频繁访问的权限检查 |
| 数据库查询 | 每次查询数据库 | 权限变更频繁场景 |

#### 8.12.7 权限审计规则

所有权限相关操作必须记录审计日志：

```python
def audit_permission_operation(operation_type, target, operator, role, details):
    """记录权限操作审计日志"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO permission_audit_logs 
            (operation_type, target, operator, role, details, timestamp)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (operation_type, target, operator, role, json.dumps(details)))
        conn.commit()
```text

### 8.13 自动修复后台代码规则

#### 8.13.1 自动修复维护规则

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| AUTOFIX_ENABLED | 自动修复启用 | 1 | 是否启用自动修复功能 |
| AUTOFIX_CODE_BACKUP_ENABLED | 修复代码备份启用 | 1 | 是否启用修复前代码备份 |
| AUTOFIX_DB_RECORD_ENABLED | 修复数据库留底启用 | 1 | 是否启用修复记录数据库留底 |
| AUTOFIX_DB_RECORD_RETENTION_DAYS | 修复记录保留天数 | 90 | 修复记录在数据库中的保留天数 |
| AUTOFIX_VALIDATION_ENABLED | 修复验证启用 | 1 | 是否启用修复后验证 |
| AUTOFIX_ROLLBACK_ON_FAILURE_ENABLED | 修复失败回滚启用 | 1 | 修复失败时是否自动回滚 |
| AUTOFIX_MAX_CONCURRENT_OPERATIONS | 最大并发修复数 | 5 | 同时进行的最大修复操作数 |
| AUTOFIX_CONFIDENCE_THRESHOLD | 修复置信度阈值 | 0.8 | 自动修复的最低置信度阈值 |
| AUTOFIX_RETRY_COUNT | 修复重试次数 | 3 | 修复失败后的重试次数 |
| AUTOFIX_TIMEOUT | 修复超时时间 | 300 | 单次修复操作的超时时间(秒) |
| AUTOFIX_SELF_LEARNING_ENABLED | 修复自学习启用 | 1 | 是否启用修复系统自学习能力 |
| AUTOFIX_MONITORING_INTERVAL | 修复监控间隔 | 60 | 自动修复监控检查间隔(秒) |
| AUTOFIX_NOTIFICATION_ENABLED | 修复通知启用 | 1 | 是否启用修复通知功能 |
| AUTOFIX_ADMIN_EMAIL | 修复通知邮箱 | - | 接收修复通知的管理员邮箱 |
| AUTOFIX_LOG_LEVEL | 修复日志级别 | INFO | 自动修复系统的日志级别 |

#### 8.13.2 修复代码留底表结构

自动修复的所有代码变更必须留底记录到 `auto_fix_code_records` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| fix_id | TEXT | 修复ID(唯一) | ✅ |
| file_path | TEXT | 修改的文件路径 | ✅ |
| original_code | TEXT | 修复前的原始代码 | ✅ |
| fixed_code | TEXT | 修复后的代码 | ✅ |
| error_type | TEXT | 错误类型 | ✅ |
| error_message | TEXT | 错误信息 | ❌ |
| fix_strategy | TEXT | 修复策略 | ✅ |
| confidence | REAL | 修复置信度(0-1) | ❌ |
| executed_by | TEXT | 执行修复的AI员工ID | ✅ |
| executed_at | TEXT | 修复执行时间 | ✅ |
| status | TEXT | 修复状态(pending/success/failed/rolled_back) | ✅ |
| rollback_available | INTEGER | 是否可回滚(1=可回滚) | ❌ |
| rollback_code | TEXT | 回滚代码 | ❌ |
| validation_result | TEXT | 验证结果(JSON) | ❌ |
| description | TEXT | 修复描述 | ❌ |

#### 8.13.3 自动修复流程

```
1. 错误检测（通过异常捕获、日志分析、健康检查）
2. 错误分析（分类错误类型，提取错误信息）
3. 解决方案生成（从脑库查找或自动生成）
4. 代码备份（保存修复前的原始代码到数据库）
5. 执行修复（应用修复代码到目标文件）
6. 修复记录（将修复详情写入auto_fix_code_records表）
7. 修复验证（验证修复后代码是否正常运行）
8. 学习增强（将成功修复经验写入脑库）
9. 通知告警（发送修复结果通知）
```text

#### 8.13.4 数据库留底策略

| 策略项 | 规则 |
|--------|------|
| 留底时机 | 每次自动修复执行前必须留底 |
| 留底内容 | 文件路径、原始代码、修复代码、错误信息、修复策略 |
| 保留期限 | 默认90天，可通过AUTOFIX_DB_RECORD_RETENTION_DAYS配置 |
| 自动清理 | 定期清理超过保留期限的记录 |
| 回滚支持 | 保留原始代码，支持一键回滚 |

#### 8.13.5 回滚机制

```python
def rollback_fix(fix_id):
    """回滚指定修复"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. 查询修复记录
        cursor.execute('''
            SELECT file_path, original_code, rollback_available 
            FROM auto_fix_code_records 
            WHERE fix_id = ? AND status = 'success'
        ''', (fix_id,))
        record = cursor.fetchone()
        
        if not record:
            return {'success': False, 'reason': '未找到可回滚的修复记录'}
        
        file_path, original_code, rollback_available = record
        
        if rollback_available != 1:
            return {'success': False, 'reason': '该修复不支持回滚'}
        
        # 2. 恢复原始代码
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(original_code)
        
        # 3. 更新状态
        cursor.execute('''
            UPDATE auto_fix_code_records 
            SET status = 'rolled_back' 
            WHERE fix_id = ?
        ''', (fix_id,))
        conn.commit()
        
        return {'success': True, 'message': '回滚成功'}
```text

#### 8.13.6 修复验证规则

| 验证项 | 规则 |
|--------|------|
| 语法验证 | 使用py_compile验证修复后代码语法正确 |
| 逻辑验证 | 执行单元测试或集成测试验证功能正常 |
| 性能验证 | 检查修复后系统性能未下降 |
| 回滚条件 | 验证失败时自动回滚到原始代码 |
| 验证超时 | 验证超时时间不超过修复超时时间的50% |

#### 8.13.7 修复安全规则

| 安全项 | 规则 |
|--------|------|
| 权限检查 | 仅super_admin和admin角色可触发自动修复 |
| 代码审查 | 高风险修复（核心文件）需人工审查确认 |
| 置信度门槛 | 置信度低于0.8的修复不自动执行 |
| 备份优先 | 修复前必须备份原始代码 |
| 增量修复 | 仅修改受影响的最小代码块 |
| 隔离测试 | 修复先在隔离环境测试通过后再应用 |

### 8.14 常驻服务规则

#### 8.14.1 常驻服务维护规则

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| RESIDENT_ENABLED | 常驻服务启用 | 1 | 是否启用系统常驻服务 |
| RESIDENT_HEARTBEAT_INTERVAL | 常驻服务心跳间隔 | 30 | 常驻服务心跳发送间隔(秒) |
| RESIDENT_HEALTH_CHECK_INTERVAL | 常驻服务健康检查间隔 | 60 | 常驻服务健康检查间隔(秒) |
| RESIDENT_AUTO_RESTART_ENABLED | 常驻服务自动重启启用 | 1 | 是否启用常驻服务自动重启 |
| RESIDENT_MAX_RESTART_COUNT | 常驻服务最大重启次数 | 5 | 单个常驻服务最大自动重启次数 |
| RESIDENT_RESTART_DELAY | 常驻服务重启延迟 | 60 | 常驻服务重启间隔(秒) |
| RESIDENT_SERVICE_TIMEOUT | 常驻服务超时时间 | 300 | 常驻服务启动/执行超时时间(秒) |
| RESIDENT_LOG_RETENTION_DAYS | 常驻服务日志保留天数 | 30 | 常驻服务日志保留天数 |
| RESIDENT_CONCURRENT_LIMIT | 常驻服务并发数限制 | 10 | 同时运行的常驻服务最大数量 |
| RESIDENT_SHUTDOWN_GRACE_PERIOD | 常驻服务优雅关闭等待时间 | 10 | 常驻服务关闭时等待任务完成的时间(秒) |
| RESIDENT_STARTUP_TIMEOUT | 常驻服务启动超时时间 | 120 | 常驻服务启动超时时间(秒) |
| RESIDENT_WATCHDOG_ENABLED | 常驻服务看门狗启用 | 1 | 是否启用常驻服务看门狗监控 |
| RESIDENT_NOTIFICATION_ENABLED | 常驻服务通知启用 | 1 | 是否启用常驻服务异常通知 |
| RESIDENT_PRIORITY_ORDER | 常驻服务启动优先级 | core,scheduler,ai,task,maintenance | 常驻服务启动顺序 |
| RESIDENT_AUTO_START_ENABLED | 常驻服务自动启动启用 | 1 | 系统启动时是否自动启动所有常驻服务 |

#### 8.14.2 常驻服务清单

| 服务ID | 服务名称 | 服务类型 | 启动优先级 | 说明 |
|--------|----------|----------|-----------|------|
| core_scheduler | 核心调度器 | scheduler | core | 系统核心任务调度 |
| auto_scheduler | 自动计划调度器 | scheduler | scheduler | 自动化任务计划调度 |
| ai_task_scheduler | AI任务调度器 | scheduler | ai | AI任务调度与执行 |
| collaborative_scheduler | 协作任务调度器 | scheduler | task | 多AI协作任务调度 |
| maintenance_scheduler | 自动维护调度器 | scheduler | maintenance | 系统维护计划调度 |
| ai_question_maintenance | AI题库维护系统 | service | maintenance | 题库自动维护服务 |

#### 8.14.3 常驻服务状态表结构

常驻服务状态统一记录到 `resident_service_status` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| service_id | TEXT | 服务ID(唯一) | ✅ |
| service_name | TEXT | 服务名称 | ✅ |
| service_type | TEXT | 服务类型(scheduler/service) | ✅ |
| status | TEXT | 服务状态(stopped/running/error/restarting) | ✅ |
| is_running | INTEGER | 是否运行中(1=运行) | ✅ |
| pid | INTEGER | 进程ID | ❌ |
| start_time | TEXT | 启动时间 | ❌ |
| last_heartbeat | TEXT | 最后心跳时间 | ❌ |
| last_status_change | TEXT | 最后状态变更时间 | ❌ |
| restart_count | INTEGER | 重启次数 | ❌ |
| max_restart_count | INTEGER | 最大重启次数 | ❌ |
| health_score | REAL | 健康评分(0-100) | ❌ |
| error_message | TEXT | 错误信息 | ❌ |
| metadata | TEXT | 元数据(JSON) | ❌ |
| created_at | TEXT | 创建时间 | ✅ |
| updated_at | TEXT | 更新时间 | ✅ |

#### 8.14.4 常驻服务状态转换

| 当前状态 | 触发条件 | 目标状态 |
|----------|---------|---------|
| stopped | 启动命令 | running |
| running | 停止命令 | stopped |
| running | 心跳超时 | error |
| running | 健康检查失败 | error |
| error | 自动重启 | restarting |
| restarting | 启动成功 | running |
| restarting | 启动失败 | error |
| error | 手动修复 | running |

#### 8.14.5 自动重启机制

```python
def handle_service_failure(service_id):
    """处理常驻服务故障"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT restart_count, max_restart_count FROM resident_service_status WHERE service_id = ?', (service_id,))
        row = cursor.fetchone()
        
        if not row:
            return False
        
        restart_count, max_restart_count = row
        
        if restart_count >= max_restart_count:
            notify_admin(f"服务 {service_id} 已达最大重启次数，停止自动重启")
            return False
        
        time.sleep(get_setting('RESIDENT_RESTART_DELAY'))
        
        start_service(service_id)
        
        cursor.execute('''
            UPDATE resident_service_status 
            SET restart_count = restart_count + 1, status = 'restarting' 
            WHERE service_id = ?
        ''', (service_id,))
        conn.commit()
        
        return True
```text

#### 8.14.6 健康检查规则

| 检查项 | 规则 | 告警条件 |
|--------|------|---------|
| 心跳检测 | 每30秒检查一次心跳 | 心跳超时>60秒告警 |
| 进程存活 | 检查进程PID是否存在 | 进程不存在告警 |
| 响应时间 | 检查服务响应时间 | 响应时间>10秒告警 |
| 错误率 | 统计服务错误率 | 错误率>5%告警 |
| 健康评分 | 综合评估服务健康度 | 评分<60告警 |

#### 8.14.7 启动优先级规则

常驻服务按以下顺序启动：

| 优先级 | 服务类型 | 说明 |
|--------|----------|------|
| 1 | core | 核心调度器，系统基础服务 |
| 2 | scheduler | 任务调度器，依赖核心服务 |
| 3 | ai | AI相关服务，依赖调度器 |
| 4 | task | 业务任务服务，依赖AI服务 |
| 5 | maintenance | 维护服务，最后启动 |

### 8.15 沙盒规则

#### 8.15.1 沙盒概述

沙盒（Sandbox）是一种基于资源限制的安全执行环境，用于隔离AI实例的运行环境，防止单个实例的异常影响整个系统。沙盒支持不同隔离级别，并实现动态扩缩容、预温机制和自动清理功能。

#### 8.15.2 沙盒规则配置

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| SANDBOX_ENABLED | 沙盒启用 | 1 | 是否启用沙盒隔离环境 |
| SANDBOX_ISOLATION_LEVEL | 沙盒隔离级别 | medium | 沙盒隔离级别(low/medium/high) |
| SANDBOX_MAX_INSTANCES | 沙盒最大实例数 | 50 | 同时运行的最大沙盒实例数 |
| SANDBOX_MIN_INSTANCES | 沙盒最小实例数 | 5 | 保持运行的最小沙盒实例数 |
| SANDBOX_RESOURCE_LIMIT_CPU | 沙盒CPU资源限制 | 50 | 单个沙盒CPU使用率上限(%) |
| SANDBOX_RESOURCE_LIMIT_MEMORY | 沙盒内存资源限制 | 1024 | 单个沙盒内存上限(MB) |
| SANDBOX_RESOURCE_LIMIT_DISK | 沙盒磁盘资源限制 | 10240 | 单个沙盒磁盘使用上限(MB) |
| SANDBOX_RESOURCE_LIMIT_PROCESSES | 沙盒进程数限制 | 10 | 单个沙盒最大进程数 |
| SANDBOX_DYNAMIC_SCALING_ENABLED | 沙盒动态扩缩容启用 | 1 | 是否启用沙盒动态扩缩容 |
| SANDBOX_PREWARM_ENABLED | 沙盒预温启用 | 1 | 是否启用沙盒预温机制 |
| SANDBOX_HEALTH_CHECK_INTERVAL | 沙盒健康检查间隔 | 60 | 沙盒健康检查间隔(秒) |
| SANDBOX_AUTO_CLEANUP_ENABLED | 沙盒自动清理启用 | 1 | 是否启用沙盒自动清理 |
| SANDBOX_CLEANUP_INTERVAL | 沙盒清理间隔 | 3600 | 沙盒自动清理间隔(秒) |
| SANDBOX_TIMEOUT | 沙盒超时时间 | 3600 | 沙盒最长运行时间(秒) |
| SANDBOX_NETWORK_ISOLATION_ENABLED | 沙盒网络隔离启用 | 1 | 是否启用沙盒网络隔离 |
| SANDBOX_FILE_SYSTEM_ACCESS | 沙盒文件系统访问 | 1 | 是否允许沙盒访问文件系统 |
| SANDBOX_CLIPBOARD_ACCESS | 沙盒剪贴板访问 | 0 | 是否允许沙盒访问剪贴板 |
| SANDBOX_GPU_ACCESS | 沙盒GPU访问 | 0 | 是否允许沙盒访问GPU |

#### 8.15.3 隔离级别定义

| 级别 | CPU限制 | 内存限制 | 网络访问 | 文件系统 | 说明 |
|------|---------|---------|---------|---------|------|
| low | 80% | 2048MB | 允许 | 完整访问 | 低隔离，适用于信任任务 |
| medium | 50% | 1024MB | 限制 | 只读访问 | 中隔离，适用于常规任务 |
| high | 20% | 512MB | 禁止 | 禁止 | 高隔离，适用于高危任务 |

#### 8.15.4 沙盒实例表结构

沙盒实例状态统一记录到 `sandbox_instances` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| sandbox_id | TEXT | 沙盒ID(唯一) | ✅ |
| instance_id | TEXT | 关联的实例ID | ✅ |
| status | TEXT | 沙盒状态(created/running/stopped/error) | ✅ |
| isolation_level | TEXT | 隔离级别 | ❌ |
| resource_limits | TEXT | 资源限制(JSON) | ❌ |
| file_system_access | INTEGER | 是否允许文件系统访问(1=允许) | ❌ |
| network_isolation | INTEGER | 是否启用网络隔离(1=启用) | ❌ |
| clipboard_access | INTEGER | 是否允许剪贴板访问(1=允许) | ❌ |
| gpu_access | INTEGER | 是否允许GPU访问(1=允许) | ❌ |
| created_at | TEXT | 创建时间 | ✅ |
| started_at | TEXT | 启动时间 | ❌ |
| stopped_at | TEXT | 停止时间 | ❌ |
| last_health_check | TEXT | 最后健康检查时间 | ❌ |
| health_score | REAL | 健康评分(0-100) | ❌ |
| error_message | TEXT | 错误信息 | ❌ |
| prewarmed | INTEGER | 是否为预温沙盒(1=是) | ❌ |
| usage_count | INTEGER | 使用次数 | ❌ |
| metadata | TEXT | 元数据(JSON) | ❌ |
| updated_at | TEXT | 更新时间 | ✅ |

#### 8.15.5 沙盒状态转换规则

| 当前状态 | 触发条件 | 目标状态 |
|----------|---------|---------|
| created | 启动命令 | running |
| running | 停止命令 | stopped |
| running | 超时 | stopped |
| running | 健康检查失败 | error |
| running | 资源超限 | error |
| error | 自动修复成功 | running |
| error | 自动修复失败 | stopped |
| stopped | 删除命令 | - (记录保留) |

#### 8.15.6 资源限制策略

| 资源类型 | 限制方式 | 超限处理 |
|----------|---------|---------|
| CPU | 使用率上限 | 限制CPU分配，记录警告 |
| 内存 | 最大分配量 | 自动终止沙盒，记录错误 |
| 磁盘 | 最大使用量 | 拒绝写操作，记录警告 |
| 进程数 | 最大进程数 | 拒绝新进程创建，记录警告 |

#### 8.15.7 动态扩缩容机制

```python
def adjust_sandbox_limit():
    """根据资源使用情况动态调整沙盒上限"""
    if not dynamic_scaling_enabled:
        return
    
    system_resources = get_system_resource_usage()
    
    new_max = current_max_sandboxes
    
    if all(usage < 70 for usage in system_resources.values()):
        new_max = min(current_max_sandboxes + 5, max_sandboxes)
    elif any(usage > 85 for usage in system_resources.values()):
        new_max = max(current_max_sandboxes - 5, min_sandboxes)
    
    if new_max != current_max_sandboxes:
        update_max_sandboxes(new_max)
        log_maintenance_operation('sandbox_scaling', 'sandbox_manager', 'success', 
                                   {'old_max': current_max_sandboxes, 'new_max': new_max})
```text

#### 8.15.8 预温机制

| 机制项 | 规则 |
|--------|------|
| 预温数量 | 保持SANDBOX_MIN_INSTANCES数量的预温沙盒 |
| 预温状态 | 预温沙盒状态为running，标记prewarmed=1 |
| 使用策略 | 请求到达时优先使用预温沙盒，使用后清除prewarmed标记 |
| 补充策略 | 使用后立即补充新的预温沙盒 |
| 超时回收 | 预温沙盒超过SANDBOX_TIMEOUT未使用则回收 |

#### 8.15.9 健康检查规则

| 检查项 | 频率 | 检查内容 | 告警条件 |
|--------|------|---------|---------|
| 进程存活 | 每60秒 | 检查沙盒进程是否存在 | 进程不存在告警 |
| 资源使用 | 每60秒 | CPU/内存/磁盘使用率 | 任一超过90%告警 |
| 响应时间 | 每60秒 | 沙盒响应延迟 | 延迟>10秒告警 |
| 错误率 | 每60秒 | 沙盒执行错误率 | 错误率>5%告警 |
| 健康评分 | 每60秒 | 综合健康评估 | 评分<60告警 |

#### 8.15.10 自动清理规则

| 清理项 | 规则 |
|--------|------|
| 超时沙盒 | 运行时间超过SANDBOX_TIMEOUT的沙盒自动清理 |
| 异常沙盒 | 状态为error且超过重试次数的沙盒自动清理 |
| 预温沙盒 | 超过SANDBOX_TIMEOUT未使用的预温沙盒自动清理 |
| 清理频率 | 每SANDBOX_CLEANUP_INTERVAL执行一次清理 |
| 清理日志 | 清理操作记录到system_maintenance_logs表 |

### 8.16 网络规则

#### 8.16.1 网络规则概述

网络规则用于管理系统的网络配置，包括端口映射、防火墙规则和网络地址转换(NAT)规则。所有网络规则必须实现幂等同步机制，避免重复添加规则导致网络配置混乱。

#### 8.16.2 网络规则配置

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| NETWORK_ENABLED | 网络规则启用 | 1 | 是否启用网络规则管理 |
| NETWORK_PORT_MAPPING_ENABLED | 端口映射启用 | 1 | 是否启用端口映射功能 |
| NETWORK_FIREWALL_ENABLED | 防火墙规则启用 | 1 | 是否启用防火墙规则管理 |
| NETWORK_IDEMPOTENT_SYNC_ENABLED | 幂等同步启用 | 1 | 是否启用网络规则幂等同步，避免重复添加规则 |
| NETWORK_SYNC_INTERVAL | 网络规则同步间隔 | 60 | 网络规则同步检查间隔(秒) |
| NETWORK_MAX_PORT_RULES | 最大端口规则数 | 100 | 允许的最大端口映射规则数 |
| NETWORK_MAX_FIREWALL_RULES | 最大防火墙规则数 | 500 | 允许的最大防火墙规则数 |
| NETWORK_ALLOWED_PROTOCOLS | 允许的协议 | tcp,udp | 允许使用的网络协议列表 |
| NETWORK_ALLOWED_CHAINS | 允许的链 | INPUT,OUTPUT,FORWARD,PREROUTING,POSTROUTING | 允许配置的iptables链 |
| NETWORK_EXTERNAL_INTERFACE | 外部网络接口 | eth0 | 对外服务的网络接口名称 |
| NETWORK_INTERNAL_INTERFACE | 内部网络接口 | lo | 内部服务的网络接口名称 |
| NETWORK_DEFAULT_INTERNAL_IP | 默认内部IP | 127.0.0.1 | 端口映射的默认内部IP地址 |
| NETWORK_DNAT_ENABLED | DNAT规则启用 | 1 | 是否启用DNAT端口转发规则 |
| NETWORK_SNAT_ENABLED | SNAT规则启用 | 1 | 是否启用SNAT源地址转换规则 |
| NETWORK_MASQUERADE_ENABLED | MASQUERADE启用 | 1 | 是否启用MASQUERADE地址伪装 |
| NETWORK_PERSISTENT_ENABLED | 网络规则持久化启用 | 1 | 是否启用网络规则持久化，重启后自动恢复 |
| NETWORK_AUTO_CLEANUP_ENABLED | 网络规则自动清理启用 | 1 | 是否启用无效网络规则自动清理 |
| NETWORK_CLEANUP_INTERVAL | 网络规则清理间隔 | 3600 | 网络规则自动清理间隔(秒) |
| NETWORK_HEALTH_CHECK_INTERVAL | 网络健康检查间隔 | 60 | 网络连通性检查间隔(秒) |
| NETWORK_ALERT_ON_FAILURE | 网络故障告警 | 1 | 网络规则应用失败时是否发送告警 |

#### 8.16.3 端口映射规则表结构

端口映射规则统一记录到 `network_port_rules` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| rule_id | TEXT | 规则ID(唯一) | ✅ |
| rule_name | TEXT | 规则名称 | ✅ |
| protocol | TEXT | 协议(tcp/udp) | ❌ |
| external_port | INTEGER | 外部端口 | ✅ |
| internal_port | INTEGER | 内部端口 | ✅ |
| internal_ip | TEXT | 内部IP地址 | ❌ |
| rule_type | TEXT | 规则类型(dnat/snat/masquerade) | ❌ |
| comment | TEXT | 规则注释 | ❌ |
| enabled | INTEGER | 是否启用(1=启用) | ❌ |
| created_at | TEXT | 创建时间 | ✅ |
| updated_at | TEXT | 更新时间 | ✅ |

#### 8.16.4 防火墙规则表结构

防火墙规则统一记录到 `network_firewall_rules` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| rule_id | TEXT | 规则ID(唯一) | ✅ |
| rule_name | TEXT | 规则名称 | ✅ |
| chain | TEXT | iptables链(INPUT/OUTPUT/FORWARD/PREROUTING/POSTROUTING) | ❌ |
| protocol | TEXT | 协议(tcp/udp/icmp/all) | ❌ |
| src_ip | TEXT | 源IP地址 | ❌ |
| dst_ip | TEXT | 目的IP地址 | ❌ |
| src_port | INTEGER | 源端口 | ❌ |
| dst_port | INTEGER | 目的端口 | ❌ |
| action | TEXT | 动作(ACCEPT/DROP/REJECT) | ❌ |
| comment | TEXT | 规则注释 | ❌ |
| enabled | INTEGER | 是否启用(1=启用) | ❌ |
| priority | INTEGER | 优先级(数值越小越优先) | ❌ |
| created_at | TEXT | 创建时间 | ✅ |
| updated_at | TEXT | 更新时间 | ✅ |

#### 8.16.5 幂等同步机制

基于经验总结，网络规则同步必须实现幂等机制，避免重复添加规则：

```python
def sync_port_rule(rule):
    """幂等同步端口规则"""
    # 1. 检查规则是否已存在
    if rule_exists(rule):
        # 检查规则内容是否一致
        if rule_content_matches(rule):
            return {'success': True, 'action': 'skipped', 'reason': '规则已存在且一致'}
        else:
            # 先删除旧规则再添加新规则
            delete_rule(rule['rule_id'])
    
    # 2. 添加新规则
    add_rule(rule)
    
    return {'success': True, 'action': 'added'}

def rule_exists(rule):
    """检查规则是否已存在"""
    # 使用 iptables -C 检查规则是否存在
    # 或解析 iptables -S / iptables-save 输出
    # 按 comment(rule_id) 精确匹配
    return check_iptables_rule_exists(rule)

def delete_rule(rule_id):
    """按规则ID删除规则"""
    # 按 comment(rule_id) 精准匹配规则行号
    # 倒序执行 iptables -D 删除
    delete_iptables_rule_by_comment(rule_id)
```text

#### 8.16.6 同步策略

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| 增量幂等 | 逐条检查规则，存在则跳过，不一致则删除后重新添加 | 频繁同步场景 |
| 全量对齐 | 先删除该规则ID相关的所有规则，再按下发集合添加 | 首次同步或大规模变更 |
| 混合模式 | 日常使用增量幂等，定期执行全量对齐校验 | 生产环境推荐 |

#### 8.16.7 NAT规则类型

| 规则类型 | 说明 | 适用场景 |
|----------|------|---------|
| DNAT | 目标地址转换 | 端口映射，外部访问内部服务 |
| SNAT | 源地址转换 | 内网访问外网，隐藏真实IP |
| MASQUERADE | 地址伪装 | 动态IP场景的SNAT |
| REDIRECT | 端口重定向 | 同一主机内部端口转发 |

#### 8.16.8 规则清理策略

| 清理项 | 规则 |
|--------|------|
| 无效规则 | 内部IP不可达或端口未监听的规则自动清理 |
| 重复规则 | 检测到重复规则时保留最新的一条 |
| 过期规则 | 超过有效期的规则自动清理 |
| 清理频率 | 每NETWORK_CLEANUP_INTERVAL执行一次清理 |
| 清理日志 | 清理操作记录到system_maintenance_logs表 |

#### 8.16.9 网络健康检查规则

| 检查项 | 频率 | 检查内容 | 告警条件 |
|--------|------|---------|---------|
| 端口监听 | 每60秒 | 检查配置的端口是否正常监听 | 端口未监听告警 |
| 规则生效 | 每60秒 | 检查iptables规则是否正确应用 | 规则缺失告警 |
| 连通性 | 每60秒 | 检查内部服务连通性 | 连通失败告警 |
| NAT转换 | 每60秒 | 检查NAT规则是否正常工作 | 转换失败告警 |
| 防火墙状态 | 每60秒 | 检查防火墙服务状态 | 服务停止告警 |

#### 8.16.10 网络规则持久化

| 持久化项 | 规则 |
|----------|------|
| 规则存储 | 所有网络规则存储到network_port_rules和network_firewall_rules表 |
| 配置保存 | 使用iptables-save保存规则到文件 |
| 自动恢复 | 系统启动时自动加载保存的规则 |
| 备份策略 | 定期备份规则配置文件 |

### 8.17 协议规则

#### 8.17.1 协议规则概述

协议规则用于管理系统支持的通信协议，包括HTTP/HTTPS、WebSocket、gRPC、MQTT、AMQP等。协议规则定义了协议的连接参数、认证要求、限流策略和加密配置。

#### 8.17.2 协议规则配置

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| PROTOCOL_ENABLED | 协议管理启用 | 1 | 是否启用协议管理功能 |
| PROTOCOL_DEFAULT_ENCODING | 默认编码 | utf-8 | 协议通信默认编码格式 |
| PROTOCOL_DEFAULT_TIMEOUT | 默认超时时间 | 300 | 协议连接默认超时时间(秒) |
| PROTOCOL_DEFAULT_RETRY_COUNT | 默认重试次数 | 3 | 协议操作默认重试次数 |
| PROTOCOL_MAX_CONNECTIONS | 最大连接数 | 1000 | 协议服务最大并发连接数 |
| PROTOCOL_KEEP_ALIVE_ENABLED | 长连接启用 | 1 | 是否启用协议长连接 |
| PROTOCOL_COMPRESSION_ENABLED | 压缩启用 | 0 | 是否启用协议数据压缩 |
| PROTOCOL_ENCRYPTION_ENABLED | 加密启用 | 1 | 是否启用协议加密传输 |
| PROTOCOL_SSL_CERTIFICATE_PATH | SSL证书路径 | - | SSL证书文件路径 |
| PROTOCOL_SSL_KEY_PATH | SSL密钥路径 | - | SSL密钥文件路径 |
| PROTOCOL_SUPPORTED_TYPES | 支持的协议类型 | http,https,grpc,websocket,mqtt,amqp | 系统支持的协议类型列表 |
| PROTOCOL_API_RATE_LIMIT | API限流 | 100 | 协议API默认限流阈值(次/分钟) |
| PROTOCOL_API_RATE_LIMIT_WINDOW | API限流窗口 | 1minute | 协议API限流时间窗口 |
| PROTOCOL_AUTH_REQUIRED | 认证要求 | 1 | 协议接口是否默认需要认证 |
| PROTOCOL_AUTH_TOKEN_EXPIRY | 认证令牌过期时间 | 3600 | 协议认证令牌过期时间(秒) |
| PROTOCOL_WEBSOCKET_ENABLED | WebSocket启用 | 1 | 是否启用WebSocket协议支持 |
| PROTOCOL_WEBSOCKET_PING_INTERVAL | WebSocket心跳间隔 | 30 | WebSocket连接心跳检测间隔(秒) |
| PROTOCOL_GRPC_ENABLED | gRPC启用 | 1 | 是否启用gRPC协议支持 |
| PROTOCOL_MQTT_ENABLED | MQTT启用 | 1 | 是否启用MQTT协议支持 |
| PROTOCOL_MQTT_BROKER_URL | MQTT Broker地址 | - | MQTT Broker连接地址 |
| PROTOCOL_MQTT_KEEP_ALIVE | MQTT心跳间隔 | 60 | MQTT连接心跳间隔(秒) |
| PROTOCOL_EVENT_STREAMING_ENABLED | 事件流启用 | 1 | 是否启用事件流协议支持 |
| PROTOCOL_EVENT_BATCH_SIZE | 事件批处理大小 | 100 | 事件流批处理最大条数 |
| PROTOCOL_EVENT_FLUSH_INTERVAL | 事件刷新间隔 | 1 | 事件流缓冲区刷新间隔(秒) |

#### 8.17.3 协议配置表结构

协议配置统一记录到 `protocol_rules` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| protocol_id | TEXT | 协议ID(唯一) | ✅ |
| protocol_name | TEXT | 协议名称 | ✅ |
| protocol_type | TEXT | 协议类型(http/https/grpc/websocket/mqtt/amqp) | ✅ |
| protocol_version | TEXT | 协议版本 | ❌ |
| connection_type | TEXT | 连接类型(tcp/udp) | ❌ |
| default_port | INTEGER | 默认端口 | ❌ |
| encoding | TEXT | 编码格式 | ❌ |
| timeout | INTEGER | 超时时间(秒) | ❌ |
| max_connections | INTEGER | 最大连接数 | ❌ |
| retry_count | INTEGER | 重试次数 | ❌ |
| keep_alive_enabled | INTEGER | 是否启用长连接(1=启用) | ❌ |
| compression_enabled | INTEGER | 是否启用压缩(1=启用) | ❌ |
| encryption_enabled | INTEGER | 是否启用加密(1=启用) | ❌ |
| certificate_path | TEXT | SSL证书路径 | ❌ |
| enabled | INTEGER | 是否启用(1=启用) | ❌ |
| created_at | TEXT | 创建时间 | ✅ |
| updated_at | TEXT | 更新时间 | ✅ |

#### 8.17.4 协议端点表结构

协议端点配置统一记录到 `protocol_endpoints` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| endpoint_id | TEXT | 端点ID(唯一) | ✅ |
| protocol_id | TEXT | 关联的协议ID | ✅ |
| endpoint_name | TEXT | 端点名称 | ✅ |
| endpoint_type | TEXT | 端点类型(rest/grpc/websocket/event) | ❌ |
| url | TEXT | 端点URL | ✅ |
| method | TEXT | HTTP方法(GET/POST/PUT/DELETE) | ❌ |
| auth_required | INTEGER | 是否需要认证(1=需要) | ❌ |
| rate_limit | INTEGER | 限流阈值(次/窗口) | ❌ |
| rate_limit_window | TEXT | 限流时间窗口 | ❌ |
| timeout | INTEGER | 请求超时时间(秒) | ❌ |
| enabled | INTEGER | 是否启用(1=启用) | ❌ |
| created_at | TEXT | 创建时间 | ✅ |
| updated_at | TEXT | 更新时间 | ✅ |

#### 8.17.5 支持的协议类型

| 协议类型 | 说明 | 默认端口 | 适用场景 |
|----------|------|---------|---------|
| HTTP | 超文本传输协议 | 80 | 常规API访问 |
| HTTPS | 加密HTTP协议 | 443 | 安全API访问 |
| gRPC | 高性能RPC框架 | 50051 | 微服务通信 |
| WebSocket | 双向实时通信 | 80/443 | 实时通知、聊天 |
| MQTT | 消息队列遥测传输 | 1883/8883 | IoT设备通信 |
| AMQP | 高级消息队列协议 | 5672/5671 | 消息队列 |

#### 8.17.6 协议认证规则

| 认证方式 | 说明 | 适用协议 |
|----------|------|---------|
| Token认证 | JWT/OAuth2令牌 | HTTP/HTTPS/gRPC |
| API Key | API密钥认证 | HTTP/HTTPS |
| Certificate | SSL证书认证 | HTTPS/gRPC |
| Basic Auth | 基础认证 | HTTP/HTTPS |
| MQTT Username/Password | MQTT用户名密码认证 | MQTT |

#### 8.17.7 协议限流规则

| 限流策略 | 说明 | 配置方式 |
|----------|------|---------|
| 固定窗口 | 固定时间窗口内限制请求数 | rate_limit + rate_limit_window |
| 滑动窗口 | 滑动时间窗口内限制请求数 | 基于令牌桶算法 |
| 并发限制 | 限制同时处理的请求数 | max_connections |
| 优先级限流 | 根据请求优先级限流 | 优先级队列 |

#### 8.17.8 协议健康检查规则

| 检查项 | 频率 | 检查内容 | 告警条件 |
|--------|------|---------|---------|
| 协议可用性 | 每60秒 | 检查协议服务是否可用 | 服务不可用告警 |
| 连接状态 | 每60秒 | 检查连接数是否正常 | 连接数超限告警 |
| 响应时间 | 每60秒 | 检查协议响应时间 | 响应时间>5秒告警 |
| 错误率 | 每60秒 | 检查协议请求错误率 | 错误率>5%告警 |
| 认证状态 | 每300秒 | 检查认证令牌有效性 | 令牌过期告警 |

#### 8.17.9 WebSocket协议规则

| 规则项 | 说明 | 默认值 |
|--------|------|--------|
| 启用状态 | 是否启用WebSocket支持 | 启用 |
| 心跳间隔 | WebSocket Ping/Pong间隔 | 30秒 |
| 最大帧大小 | 单帧最大数据量 | 10MB |
| 连接超时 | 连接建立超时时间 | 60秒 |
| 消息队列长度 | 消息缓冲队列最大长度 | 1000 |

#### 8.17.10 MQTT协议规则

| 规则项 | 说明 | 默认值 |
|--------|------|--------|
| 启用状态 | 是否启用MQTT支持 | 启用 |
| Broker地址 | MQTT服务器地址 | - |
| 心跳间隔 | MQTT Keep Alive间隔 | 60秒 |
| 连接超时 | MQTT连接超时 | 30秒 |
| 重连间隔 | 断开后重连间隔 | 5秒 |
| QoS级别 | 默认消息服务质量 | 1 |

### 8.18 端口规则

#### 8.18.1 端口规则概述

端口规则用于管理系统的端口配置，包括端口绑定、限流、连接控制、TLS加密和端口映射。所有端口规则必须实现幂等同步机制，避免重复添加iptables规则导致网络配置混乱。

#### 8.18.2 端口规则配置

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| PORT_ENABLED | 端口管理启用 | 1 | 是否启用端口管理功能 |
| PORT_DEFAULT_PROTOCOL | 默认协议 | tcp | 端口默认使用的协议 |
| PORT_DEFAULT_BINDING_IP | 默认绑定IP | 0.0.0.0 | 端口默认绑定的IP地址 |
| PORT_MIN_NUMBER | 最小端口号 | 1024 | 允许使用的最小端口号 |
| PORT_MAX_NUMBER | 最大端口号 | 65535 | 允许使用的最大端口号 |
| PORT_DEFAULT_RATE_LIMIT | 默认限流 | 0 | 端口默认限流阈值(0=不限) |
| PORT_DEFAULT_RATE_LIMIT_WINDOW | 默认限流窗口 | 1minute | 端口默认限流时间窗口 |
| PORT_DEFAULT_CONNECTION_LIMIT | 默认连接数限制 | 0 | 端口默认最大连接数(0=不限) |
| PORT_DEFAULT_TIMEOUT | 默认超时时间 | 0 | 端口默认连接超时时间(秒)(0=不限) |
| PORT_TLS_ENABLED | TLS启用 | 0 | 是否默认启用TLS加密 |
| PORT_TLS_CERTIFICATE_PATH | TLS证书路径 | - | TLS证书文件路径 |
| PORT_TLS_KEY_PATH | TLS密钥路径 | - | TLS密钥文件路径 |
| PORT_IDEMPOTENT_SYNC_ENABLED | 幂等同步启用 | 1 | 是否启用端口规则幂等同步，避免重复添加 |
| PORT_SYNC_INTERVAL | 端口规则同步间隔 | 60 | 端口规则同步检查间隔(秒) |
| PORT_MAX_RULES | 最大端口规则数 | 200 | 允许的最大端口规则数 |
| PORT_MAX_MAPPING_RULES | 最大映射规则数 | 100 | 允许的最大端口映射规则数 |
| PORT_AUTO_CLEANUP_ENABLED | 自动清理启用 | 1 | 是否启用无效端口规则自动清理 |
| PORT_CLEANUP_INTERVAL | 清理间隔 | 3600 | 端口规则自动清理间隔(秒) |
| PORT_HEALTH_CHECK_INTERVAL | 健康检查间隔 | 60 | 端口健康检查间隔(秒) |
| PORT_ALERT_ON_FAILURE | 故障告警 | 1 | 端口规则应用失败时是否发送告警 |
| PORT_RESERVED_START | 保留端口起始 | 1 | 系统保留端口起始号 |
| PORT_RESERVED_END | 保留端口结束 | 1023 | 系统保留端口结束号 |
| PORT_SYSTEM_START | 系统端口起始 | 8000 | 系统服务端口起始号 |
| PORT_SYSTEM_END | 系统端口结束 | 9000 | 系统服务端口结束号 |
| PORT_USER_START | 用户端口起始 | 9000 | 用户自定义端口起始号 |
| PORT_USER_END | 用户端口结束 | 65535 | 用户自定义端口结束号 |

#### 8.18.3 端口配置表结构

端口配置统一记录到 `port_rules` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| port_id | TEXT | 端口ID(唯一) | ✅ |
| port_name | TEXT | 端口名称 | ✅ |
| port_number | INTEGER | 端口号 | ✅ |
| protocol | TEXT | 协议(tcp/udp) | ❌ |
| service_name | TEXT | 关联服务名称 | ❌ |
| binding_ip | TEXT | 绑定IP地址 | ❌ |
| allowed_ips | TEXT | 允许访问的IP列表(JSON) | ❌ |
| blocked_ips | TEXT | 禁止访问的IP列表(JSON) | ❌ |
| rate_limit | INTEGER | 限流阈值(次/窗口) | ❌ |
| rate_limit_window | TEXT | 限流时间窗口 | ❌ |
| connection_limit | INTEGER | 最大连接数 | ❌ |
| timeout | INTEGER | 连接超时时间(秒) | ❌ |
| tls_enabled | INTEGER | 是否启用TLS(1=启用) | ❌ |
| tls_certificate_path | TEXT | TLS证书路径 | ❌ |
| enabled | INTEGER | 是否启用(1=启用) | ❌ |
| description | TEXT | 端口描述 | ❌ |
| created_at | TEXT | 创建时间 | ✅ |
| updated_at | TEXT | 更新时间 | ✅ |

#### 8.18.4 端口映射表结构

端口映射规则统一记录到 `port_mapping_rules` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| mapping_id | TEXT | 映射ID(唯一) | ✅ |
| mapping_name | TEXT | 映射名称 | ✅ |
| external_port | INTEGER | 外部端口 | ✅ |
| internal_port | INTEGER | 内部端口 | ✅ |
| internal_ip | TEXT | 内部IP地址 | ❌ |
| protocol | TEXT | 协议(tcp/udp) | ❌ |
| enabled | INTEGER | 是否启用(1=启用) | ❌ |
| description | TEXT | 映射描述 | ❌ |
| created_at | TEXT | 创建时间 | ✅ |
| updated_at | TEXT | 更新时间 | ✅ |

#### 8.18.5 端口分类规则

| 端口范围 | 分类 | 说明 |
|----------|------|------|
| 1-1023 | 保留端口 | 系统服务使用，需root权限 |
| 1024-49151 | 注册端口 | 互联网服务使用 |
| 49152-65535 | 动态端口 | 临时端口 |
| 8000-9000 | 系统端口 | 本系统服务使用 |
| 9000-65535 | 用户端口 | 用户自定义服务使用 |

#### 8.18.6 幂等同步机制

基于经验总结，端口规则同步必须实现幂等机制，避免重复添加iptables规则：

```python
def sync_port_rule(rule):
    """幂等同步端口规则"""
    # 1. 检查规则是否已存在
    if port_rule_exists(rule):
        # 检查规则内容是否一致
        if port_rule_content_matches(rule):
            return {'success': True, 'action': 'skipped', 'reason': '规则已存在且一致'}
        else:
            # 先删除旧规则再添加新规则
            delete_port_rule(rule['port_id'])
    
    # 2. 添加新规则
    add_port_rule(rule)
    
    return {'success': True, 'action': 'added'}

def port_rule_exists(rule):
    """检查端口规则是否已存在"""
    # 使用 iptables -C 检查规则是否存在
    # 或解析 iptables -S / iptables-save 输出
    # 按 comment(port_id) 精确匹配
    return check_iptables_rule_exists(rule)

def delete_port_rule(port_id):
    """按端口ID删除规则"""
    # 按 comment(port_id) 精准匹配规则行号
    # 倒序执行 iptables -D 删除
    delete_iptables_rule_by_comment(port_id)
```text

#### 8.18.7 端口映射规则

| 映射类型 | 说明 | iptables实现 |
|----------|------|-------------|
| DNAT | 目标地址转换 | iptables -t nat -A PREROUTING |
| SNAT | 源地址转换 | iptables -t nat -A POSTROUTING |
| MASQUERADE | 地址伪装 | iptables -t nat -A POSTROUTING -j MASQUERADE |
| REDIRECT | 端口重定向 | iptables -t nat -A PREROUTING -j REDIRECT |

#### 8.18.8 端口清理策略

| 清理项 | 规则 |
|--------|------|
| 无效规则 | 端口未监听或服务不存在的规则自动清理 |
| 重复规则 | 检测到重复规则时保留最新的一条 |
| 过期规则 | 超过有效期的规则自动清理 |
| 清理频率 | 每PORT_CLEANUP_INTERVAL执行一次清理 |
| 清理日志 | 清理操作记录到system_maintenance_logs表 |

#### 8.18.9 端口健康检查规则

| 检查项 | 频率 | 检查内容 | 告警条件 |
|--------|------|---------|---------|
| 端口监听 | 每60秒 | 检查配置的端口是否正常监听 | 端口未监听告警 |
| 规则生效 | 每60秒 | 检查iptables规则是否正确应用 | 规则缺失告警 |
| 连接数 | 每60秒 | 检查端口连接数是否正常 | 连接数超限告警 |
| 响应时间 | 每60秒 | 检查端口响应时间 | 响应时间>5秒告警 |
| TLS状态 | 每300秒 | 检查TLS证书有效性 | 证书过期告警 |

#### 8.18.10 端口安全规则

| 安全项 | 规则 |
|--------|------|
| 保留端口保护 | 1-1023端口仅允许系统服务使用 |
| IP白名单 | 支持配置允许访问的IP列表 |
| IP黑名单 | 支持配置禁止访问的IP列表 |
| 限流保护 | 支持配置请求限流 |
| 连接限制 | 支持配置最大连接数 |
| TLS加密 | 支持HTTPS/TLS加密传输 |

### 8.19 文档规则

#### 8.19.1 文档规则概述

文档规则用于管理系统的文档管理功能，包括文档创建、版本控制、访问权限、搜索索引和自动清理。所有文档内容必须加密存储，确保数据安全。

#### 8.19.2 文档规则配置

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| DOCUMENT_ENABLED | 文档管理启用 | 1 | 是否启用文档管理功能 |
| DOCUMENT_DEFAULT_TYPE | 默认文档类型 | markdown | 文档默认类型 |
| DOCUMENT_DEFAULT_CATEGORY | 默认文档分类 | system | 文档默认分类 |
| DOCUMENT_DEFAULT_ACCESS_LEVEL | 默认访问级别 | public | 文档默认访问级别(public/internal/private) |
| DOCUMENT_MAX_SIZE | 最大文档大小 | 10485760 | 单个文档最大大小(字节) |
| DOCUMENT_MAX_COUNT | 最大文档数量 | 1000 | 系统允许的最大文档数量 |
| DOCUMENT_VERSION_HISTORY_ENABLED | 版本历史启用 | 1 | 是否启用文档版本历史 |
| DOCUMENT_VERSION_MAX_COUNT | 最大版本数量 | 10 | 单个文档保留的最大版本数 |
| DOCUMENT_AUTO_SAVE_ENABLED | 自动保存启用 | 1 | 是否启用文档自动保存 |
| DOCUMENT_AUTO_SAVE_INTERVAL | 自动保存间隔 | 300 | 文档自动保存间隔(秒) |
| DOCUMENT_SEARCH_ENABLED | 文档搜索启用 | 1 | 是否启用文档全文搜索 |
| DOCUMENT_SEARCH_INDEX_INTERVAL | 搜索索引间隔 | 3600 | 文档搜索索引更新间隔(秒) |
| DOCUMENT_EXPORT_ENABLED | 文档导出启用 | 1 | 是否启用文档导出功能 |
| DOCUMENT_EXPORT_FORMATS | 支持的导出格式 | markdown,pdf,html | 文档支持的导出格式列表 |
| DOCUMENT_IMPORT_ENABLED | 文档导入启用 | 1 | 是否启用文档导入功能 |
| DOCUMENT_IMPORT_FORMATS | 支持的导入格式 | markdown,html,txt | 文档支持的导入格式列表 |
| DOCUMENT_AUTO_CLEANUP_ENABLED | 自动清理启用 | 1 | 是否启用过期文档自动清理 |
| DOCUMENT_CLEANUP_INTERVAL | 清理间隔 | 86400 | 文档自动清理间隔(秒) |
| DOCUMENT_RETENTION_DAYS | 文档保留天数 | 90 | 过期文档保留天数(天) |
| DOCUMENT_ALERT_ON_FAILURE | 故障告警 | 1 | 文档操作失败时是否发送告警 |
| DOCUMENT_ENCRYPTION_ENABLED | 文档加密启用 | 1 | 是否启用文档内容加密存储 |
| DOCUMENT_COMPRESSION_ENABLED | 文档压缩启用 | 1 | 是否启用文档压缩存储 |
| DOCUMENT_CACHE_ENABLED | 文档缓存启用 | 1 | 是否启用文档缓存 |
| DOCUMENT_CACHE_TTL | 文档缓存TTL | 3600 | 文档缓存有效期(秒) |

#### 8.19.3 文档配置表结构

文档配置统一记录到 `document_rules` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| document_id | TEXT | 文档ID(唯一) | ✅ |
| document_name | TEXT | 文档名称 | ✅ |
| document_type | TEXT | 文档类型(markdown/html/pdf) | ❌ |
| document_category | TEXT | 文档分类(system/user/knowledge) | ❌ |
| document_path | TEXT | 文档存储路径 | ❌ |
| document_content | TEXT | 文档内容 | ❌ |
| version | TEXT | 文档版本 | ❌ |
| author | TEXT | 文档作者 | ❌ |
| status | TEXT | 文档状态(draft/published/archived) | ❌ |
| publish_date | TEXT | 发布日期 | ❌ |
| expiry_date | TEXT | 过期日期 | ❌ |
| access_level | TEXT | 访问级别(public/internal/private) | ❌ |
| tags | TEXT | 标签(JSON数组) | ❌ |
| enabled | INTEGER | 是否启用(1=启用) | ❌ |
| created_at | TEXT | 创建时间 | ✅ |
| updated_at | TEXT | 更新时间 | ✅ |

#### 8.19.4 文档版本表结构

文档版本记录统一存储到 `document_versions` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| document_id | TEXT | 关联的文档ID | ✅ |
| version | TEXT | 版本号 | ✅ |
| version_number | INTEGER | 版本序号 | ❌ |
| change_log | TEXT | 变更日志 | ❌ |
| content_hash | TEXT | 内容哈希值 | ❌ |
| created_at | TEXT | 创建时间 | ✅ |

#### 8.19.5 文档类型定义

| 类型 | 说明 | 支持的操作 |
|------|------|-----------|
| markdown | Markdown格式文档 | 编辑、预览、导出 |
| html | HTML格式文档 | 编辑、预览、导出 |
| pdf | PDF格式文档 | 预览、导出 |
| txt | 纯文本文档 | 编辑、预览、导出 |
| doc | Word文档 | 预览、导出 |

#### 8.19.6 文档分类定义

| 分类 | 说明 | 示例 |
|------|------|------|
| system | 系统文档 | 操作规范、API文档、配置指南 |
| user | 用户文档 | 用户手册、帮助文档、FAQ |
| knowledge | 知识库文档 | AI知识、经验总结、最佳实践 |
| project | 项目文档 | 项目计划、进度报告、技术方案 |
| training | 培训文档 | 培训材料、课程讲义、考试大纲 |

#### 8.19.7 文档访问级别

| 级别 | 说明 | 访问权限 |
|------|------|---------|
| public | 公开文档 | 所有用户可访问 |
| internal | 内部文档 | 登录用户可访问 |
| private | 私有文档 | 仅文档所有者和管理员可访问 |
| restricted | 受限文档 | 指定用户组可访问 |

#### 8.19.8 文档状态转换规则

| 当前状态 | 触发条件 | 目标状态 |
|----------|---------|---------|
| draft | 发布操作 | published |
| draft | 删除操作 | archived |
| published | 编辑操作 | draft |
| published | 归档操作 | archived |
| published | 过期时间到达 | archived |
| archived | 恢复操作 | draft |
| archived | 清理操作 | - (记录保留) |

#### 8.19.9 文档版本管理规则

| 管理项 | 规则 |
|--------|------|
| 版本号格式 | 语义化版本号(MAJOR.MINOR.PATCH) |
| 版本保留 | 保留DOCUMENT_VERSION_MAX_COUNT个版本 |
| 版本对比 | 支持相邻版本内容对比 |
| 版本恢复 | 支持从历史版本恢复 |
| 内容哈希 | 每次保存计算内容哈希，检测重复 |

#### 8.19.10 文档搜索规则

| 搜索项 | 规则 |
|--------|------|
| 全文搜索 | 支持文档内容全文搜索 |
| 关键词搜索 | 支持关键词精确匹配 |
| 分类搜索 | 支持按文档分类筛选 |
| 标签搜索 | 支持按标签筛选 |
| 索引更新 | 每DOCUMENT_SEARCH_INDEX_INTERVAL更新索引 |
| 搜索结果排序 | 按相关性、时间、访问量排序 |

#### 8.19.11 文档导出规则

| 导出格式 | 说明 | 支持的源类型 |
|----------|------|-------------|
| markdown | 导出为Markdown文件 | markdown,txt |
| pdf | 导出为PDF文件 | markdown,html,txt |
| html | 导出为HTML文件 | markdown,html |
| docx | 导出为Word文档 | markdown,html,txt |

#### 8.19.12 文档清理规则

| 清理项 | 规则 |
|--------|------|
| 过期文档 | 超过expiry_date的文档自动归档 |
| 归档文档 | 归档超过DOCUMENT_RETENTION_DAYS天的文档自动清理 |
| 重复文档 | 内容哈希相同的重复文档仅保留一份 |
| 清理频率 | 每DOCUMENT_CLEANUP_INTERVAL执行一次清理 |
| 清理日志 | 清理操作记录到system_maintenance_logs表 |

#### 8.19.13 文档安全规则

| 安全项 | 规则 |
|--------|------|
| 内容加密 | 所有文档内容加密存储 |
| 访问控制 | 基于access_level的访问控制 |
| 操作审计 | 文档操作记录到ai_operation_logs表 |
| 备份策略 | 定期备份文档数据 |
| 防篡改 | 内容哈希校验防止篡改 |

### 8.20 前端规则

#### 8.20.1 前端规则概述

前端规则用于统一管理系统的前端样式规范，包括倒角、间距、透明度、字体大小、对齐方式等视觉元素。所有前端组件必须遵循统一的样式规范，确保系统界面一致性和美观性。

#### 8.20.2 前端样式规则配置

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| FRONTEND_ENABLED | 前端样式规范启用 | 1 | 是否启用前端样式规范 |
| FRONTEND_BORDER_RADIUS_SMALL | 小倒角 | 4px | 小尺寸元素圆角 |
| FRONTEND_BORDER_RADIUS_MEDIUM | 中等倒角 | 8px | 中等尺寸元素圆角 |
| FRONTEND_BORDER_RADIUS_LARGE | 大倒角 | 12px | 大尺寸元素圆角 |
| FRONTEND_BORDER_RADIUS_EXTRA_LARGE | 超大倒角 | 16px | 超大尺寸元素圆角 |
| FRONTEND_BORDER_RADIUS_FULL | 完全圆角 | 9999px | 圆形元素圆角 |
| FRONTEND_PADDING_SMALL | 小内边距 | 8px | 小尺寸元素内边距 |
| FRONTEND_PADDING_MEDIUM | 中等内边距 | 12px | 中等尺寸元素内边距 |
| FRONTEND_PADDING_LARGE | 大内边距 | 16px | 大尺寸元素内边距 |
| FRONTEND_MARGIN_SMALL | 小外边距 | 8px | 小尺寸元素外边距 |
| FRONTEND_MARGIN_MEDIUM | 中等外边距 | 12px | 中等尺寸元素外边距 |
| FRONTEND_MARGIN_LARGE | 大外边距 | 16px | 大尺寸元素外边距 |
| FRONTEND_MARGIN_EXTRA_LARGE | 超大外边距 | 24px | 超大尺寸元素外边距 |
| FRONTEND_OPACITY_DISABLED | 禁用透明度 | 0.5 | 禁用状态元素透明度 |
| FRONTEND_OPACITY_HOVER | 悬停透明度 | 0.85 | 悬停状态元素透明度 |
| FRONTEND_OPACITY_FOCUS | 聚焦透明度 | 0.9 | 聚焦状态元素透明度 |
| FRONTEND_OPACITY_ACTIVE | 激活透明度 | 0.95 | 激活状态元素透明度 |
| FRONTEND_FONT_SIZE_XS | 特小号字体 | 12px | 特小号字体大小 |
| FRONTEND_FONT_SIZE_SMALL | 小号字体 | 13px | 小号字体大小 |
| FRONTEND_FONT_SIZE_NORMAL | 正常字体 | 14px | 正常字体大小 |
| FRONTEND_FONT_SIZE_LARGE | 大号字体 | 16px | 大号字体大小 |
| FRONTEND_FONT_SIZE_XL | 特大号字体 | 18px | 特大号字体大小 |
| FRONTEND_FONT_SIZE_XXL | 超大号字体 | 24px | 超大号字体大小 |
| FRONTEND_FONT_SIZE_HEADING_1 | 一级标题字体 | 32px | 一级标题字体大小 |
| FRONTEND_FONT_SIZE_HEADING_2 | 二级标题字体 | 24px | 二级标题字体大小 |
| FRONTEND_FONT_SIZE_HEADING_3 | 三级标题字体 | 20px | 三级标题字体大小 |
| FRONTEND_FONT_SIZE_HEADING_4 | 四级标题字体 | 18px | 四级标题字体大小 |
| FRONTEND_TEXT_ALIGN_DEFAULT | 默认对齐 | left | 文本默认对齐方式 |
| FRONTEND_TEXT_ALIGN_CENTER | 居中对齐 | center | 文本居中对齐方式 |
| FRONTEND_TEXT_ALIGN_RIGHT | 右对齐 | right | 文本右对齐方式 |
| FRONTEND_TEXT_ALIGN_JUSTIFY | 两端对齐 | justify | 文本两端对齐方式 |
| FRONTEND_LINE_HEIGHT_DEFAULT | 默认行高 | 1.5 | 默认行高倍数 |
| FRONTEND_LINE_HEIGHT_TIGHT | 紧凑行高 | 1.25 | 紧凑行高倍数 |
| FRONTEND_LINE_HEIGHT_LOOSE | 宽松行高 | 1.75 | 宽松行高倍数 |
| FRONTEND_SPACING_ICON_TEXT | 图标文字间距 | 8px | 图标与文字之间的间距 |
| FRONTEND_SPACING_ELEMENTS | 元素间距 | 16px | 同级元素之间的间距 |
| FRONTEND_SPACING_SECTIONS | 区块间距 | 24px | 区块之间的间距 |
| FRONTEND_SHADOW_SMALL | 小阴影 | 0 2px 4px rgba(0,0,0,0.1) | 小尺寸元素阴影 |
| FRONTEND_SHADOW_MEDIUM | 中等阴影 | 0 4px 12px rgba(0,0,0,0.12) | 中等尺寸元素阴影 |
| FRONTEND_SHADOW_LARGE | 大阴影 | 0 8px 24px rgba(0,0,0,0.15) | 大尺寸元素阴影 |
| FRONTEND_BORDER_WIDTH_DEFAULT | 默认边框宽度 | 1px | 默认边框宽度 |
| FRONTEND_BORDER_STYLE_DEFAULT | 默认边框样式 | solid | 默认边框样式 |
| FRONTEND_TRANSITION_DURATION | 过渡动画时长 | 0.2s | 元素过渡动画时长 |
| FRONTEND_ANIMATION_DURATION | 动画时长 | 0.3s | 元素动画时长 |

#### 8.20.3 前端规则表结构

前端样式规则统一记录到 `frontend_rules` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| rule_id | TEXT | 规则ID(唯一) | ✅ |
| rule_name | TEXT | 规则名称 | ✅ |
| rule_category | TEXT | 规则分类(spacing/border/font/layout/animation) | ❌ |
| rule_property | TEXT | CSS属性名 | ✅ |
| rule_value | TEXT | CSS属性值 | ✅ |
| rule_unit | TEXT | 单位(px/em/rem/%/s) | ❌ |
| description | TEXT | 规则描述 | ❌ |
| enabled | INTEGER | 是否启用(1=启用) | ❌ |
| created_at | TEXT | 创建时间 | ✅ |
| updated_at | TEXT | 更新时间 | ✅ |

#### 8.20.4 前端组件规则表结构

前端组件样式规则统一记录到 `frontend_component_rules` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| component_id | TEXT | 组件ID(唯一) | ✅ |
| component_name | TEXT | 组件名称 | ✅ |
| component_type | TEXT | 组件类型(button/input/card/modal/table) | ✅ |
| border_radius | TEXT | 圆角 | ❌ |
| padding | TEXT | 内边距 | ❌ |
| margin | TEXT | 外边距 | ❌ |
| opacity | TEXT | 透明度 | ❌ |
| font_size | TEXT | 字体大小 | ❌ |
| text_align | TEXT | 文本对齐 | ❌ |
| line_height | TEXT | 行高 | ❌ |
| background_color | TEXT | 背景颜色 | ❌ |
| text_color | TEXT | 文字颜色 | ❌ |
| border_color | TEXT | 边框颜色 | ❌ |
| shadow | TEXT | 阴影 | ❌ |
| enabled | INTEGER | 是否启用(1=启用) | ❌ |
| description | TEXT | 组件描述 | ❌ |
| created_at | TEXT | 创建时间 | ✅ |
| updated_at | TEXT | 更新时间 | ✅ |

#### 8.20.5 倒角规范

| 尺寸 | 圆角值 | 适用场景 |
|------|--------|---------|
| 小倒角 | 4px | 小按钮、输入框、标签、徽章 |
| 中等倒角 | 8px | 卡片、弹窗、表单、普通按钮 |
| 大倒角 | 12px | 大卡片、模态框、面板 |
| 超大倒角 | 16px | 大面板、导航栏、头部区域 |
| 完全圆角 | 9999px | 圆形按钮、头像、圆形图标 |

#### 8.20.6 间距规范

| 间距类型 | 尺寸 | 适用场景 |
|----------|------|---------|
| 小内边距 | 8px | 小按钮、标签、徽章 |
| 中等内边距 | 12px | 普通按钮、输入框 |
| 大内边距 | 16px | 卡片、表单、大按钮 |
| 小外边距 | 8px | 小元素间距、行内元素 |
| 中等外边距 | 12px | 普通元素间距 |
| 大外边距 | 16px | 模块间距 |
| 超大外边距 | 24px | 区块间距、页面分隔 |
| 图标文字间距 | 8px | 图标与相邻文字之间 |
| 元素间距 | 16px | 同级元素之间 |
| 区块间距 | 24px | 页面区块之间 |

#### 8.20.7 透明度规范

| 状态 | 透明度 | 适用场景 |
|------|--------|---------|
| 正常状态 | 1.0 | 默认状态 |
| 禁用状态 | 0.5 | 禁用的按钮、输入框、链接 |
| 悬停状态 | 0.85 | 鼠标悬停时的交互反馈 |
| 聚焦状态 | 0.9 | 键盘聚焦时的交互反馈 |
| 激活状态 | 0.95 | 点击激活时的交互反馈 |

#### 8.20.8 字体大小规范

| 尺寸 | 字体大小 | 适用场景 |
|------|---------|---------|
| 特小号 | 12px | 辅助文字、提示信息、表格内容 |
| 小号 | 13px | 次要文字、表单标签 |
| 正常 | 14px | 正文、按钮文字、表单输入 |
| 大号 | 16px | 重要标题、表单标签 |
| 特大号 | 18px | 子标题、卡片标题 |
| 超大号 | 24px | 主标题、页面标题 |
| 一级标题 | 32px | 页面主标题 |
| 二级标题 | 24px | 区块标题 |
| 三级标题 | 20px | 模块标题 |
| 四级标题 | 18px | 子模块标题 |

#### 8.20.9 对齐方式规范

| 对齐方式 | CSS值 | 适用场景 |
|----------|-------|---------|
| 默认对齐 | left | 正文、表单、列表 |
| 居中对齐 | center | 标题、按钮组、卡片内容 |
| 右对齐 | right | 数值、时间、操作按钮 |
| 两端对齐 | justify | 长文本段落 |

#### 8.20.10 行高规范

| 类型 | 行高倍数 | 适用场景 |
|------|---------|---------|
| 紧凑行高 | 1.25 | 标题、按钮、标签 |
| 默认行高 | 1.5 | 正文、表单、普通文本 |
| 宽松行高 | 1.75 | 长段落、说明文字 |

#### 8.20.11 阴影规范

| 尺寸 | 阴影值 | 适用场景 |
|------|--------|---------|
| 小阴影 | 0 2px 4px rgba(0,0,0,0.1) | 小卡片、按钮悬停 |
| 中等阴影 | 0 4px 12px rgba(0,0,0,0.12) | 卡片、弹窗 |
| 大阴影 | 0 8px 24px rgba(0,0,0,0.15) | 模态框、下拉菜单 |

#### 8.20.12 边框规范

| 属性 | 值 | 说明 |
|------|-----|------|
| 默认宽度 | 1px | 标准边框宽度 |
| 默认样式 | solid | 实线边框 |
| 默认颜色 | #e0e0e0 | 浅灰色边框 |

#### 8.20.13 动画规范

| 类型 | 时长 | 适用场景 |
|------|------|---------|
| 过渡动画 | 0.2s | 悬停效果、状态切换 |
| 标准动画 | 0.3s | 弹出动画、淡入淡出 |

#### 8.20.14 组件样式规范

| 组件类型 | 默认样式 |
|----------|---------|
| button | 圆角8px、内边距12px 16px、字体14px、居中对齐 |
| input | 圆角8px、内边距8px 12px、字体14px、左对齐 |
| card | 圆角8px、内边距16px、外边距0、阴影中等 |
| modal | 圆角12px、内边距24px、居中对齐、阴影大 |
| table | 圆角8px、内边距8px、字体14px、左对齐 |
| badge | 圆角9999px、内边距4px 8px、字体12px |
| tag | 圆角4px、内边距4px 8px、字体12px |

### 8.21 弹窗文档规则

#### 8.21.1 弹窗文档规则概述

弹窗文档规则用于管理系统的前端弹窗显示文档，包括欢迎文档、说明文档、通知文档等。所有弹窗文档内容必须从数据库同步读取，确保与数据库数据一致。

#### 8.21.2 弹窗文档规则配置

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| DIALOG_ENABLED | 弹窗功能启用 | 1 | 是否启用弹窗功能 |
| DIALOG_DEFAULT_TYPE | 默认弹窗类型 | modal | 弹窗默认类型(modal/toast/notification/confirm) |
| DIALOG_DEFAULT_SIZE | 默认弹窗大小 | medium | 弹窗默认大小(small/medium/large/full) |
| DIALOG_DEFAULT_POSITION | 默认弹窗位置 | center | 弹窗默认位置(center/top/top-right/bottom/bottom-right) |
| DIALOG_SHOW_HEADER | 显示头部 | 1 | 弹窗默认是否显示头部 |
| DIALOG_SHOW_FOOTER | 显示底部 | 1 | 弹窗默认是否显示底部 |
| DIALOG_SHOW_CLOSE_BUTTON | 显示关闭按钮 | 1 | 弹窗默认是否显示关闭按钮 |
| DIALOG_SHOW_CONFIRM_BUTTON | 显示确认按钮 | 1 | 弹窗默认是否显示确认按钮 |
| DIALOG_CONFIRM_BUTTON_TEXT | 确认按钮文字 | 确定 | 弹窗确认按钮默认文字 |
| DIALOG_CANCEL_BUTTON_TEXT | 取消按钮文字 | 取消 | 弹窗取消按钮默认文字 |
| DIALOG_AUTO_CLOSE | 自动关闭 | 0 | 弹窗默认是否自动关闭 |
| DIALOG_AUTO_CLOSE_DELAY | 自动关闭延迟 | 3000 | 弹窗自动关闭延迟时间(毫秒) |
| DIALOG_BACKDROP | 遮罩层 | 1 | 弹窗默认是否显示遮罩层 |
| DIALOG_KEYBOARD | 键盘关闭 | 1 | 弹窗默认是否支持键盘ESC关闭 |
| DIALOG_DRAGGABLE | 可拖拽 | 0 | 弹窗默认是否可拖拽 |
| DIALOG_RESIZABLE | 可调整大小 | 0 | 弹窗默认是否可调整大小 |
| DIALOG_ANIMATION_ENABLED | 动画启用 | 1 | 弹窗默认是否启用动画 |
| DIALOG_ANIMATION_TYPE | 动画类型 | fade | 弹窗动画类型(fade/zoom/slide-up/slide-down/slide-left/slide-right) |
| DIALOG_MAX_WIDTH | 最大宽度 | 600px | 弹窗最大宽度 |
| DIALOG_MIN_WIDTH | 最小宽度 | 300px | 弹窗最小宽度 |
| DIALOG_MAX_HEIGHT | 最大高度 | 80vh | 弹窗最大高度 |
| DIALOG_MIN_HEIGHT | 最小高度 | 200px | 弹窗最小高度 |
| DIALOG_WELCOME_ENABLED | 欢迎文档启用 | 1 | 是否启用欢迎弹窗文档 |
| DIALOG_WELCOME_DISPLAY_ONCE | 欢迎文档只显示一次 | 1 | 欢迎文档是否只在首次登录显示 |
| DIALOG_WELCOME_DISPLAY_INTERVAL | 欢迎文档显示间隔 | 0 | 欢迎文档重复显示间隔(天)(0=只显示一次) |
| DIALOG_INSTRUCTION_ENABLED | 说明文档启用 | 1 | 是否启用说明弹窗文档 |
| DIALOG_INSTRUCTION_DISPLAY_ONCE | 说明文档只显示一次 | 1 | 说明文档是否只显示一次 |
| DIALOG_INSTRUCTION_DISPLAY_INTERVAL | 说明文档显示间隔 | 0 | 说明文档重复显示间隔(天)(0=只显示一次) |
| DIALOG_NOTIFICATION_ENABLED | 通知文档启用 | 1 | 是否启用通知弹窗文档 |
| DIALOG_NOTIFICATION_AUTO_CLOSE | 通知自动关闭 | 1 | 通知弹窗是否自动关闭 |
| DIALOG_NOTIFICATION_AUTO_CLOSE_DELAY | 通知自动关闭延迟 | 5000 | 通知弹窗自动关闭延迟时间(毫秒) |
| DIALOG_MAX_DOCUMENTS | 最大文档数量 | 50 | 弹窗文档最大数量 |
| DIALOG_DEFAULT_LANGUAGE | 默认语言 | zh-CN | 弹窗文档默认语言 |

#### 8.21.3 弹窗规则表结构

弹窗配置统一记录到 `dialog_rules` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| dialog_id | TEXT | 弹窗ID(唯一) | ✅ |
| dialog_name | TEXT | 弹窗名称 | ✅ |
| dialog_type | TEXT | 弹窗类型(modal/toast/notification/confirm) | ❌ |
| dialog_title | TEXT | 弹窗标题 | ❌ |
| dialog_content | TEXT | 弹窗内容 | ❌ |
| dialog_size | TEXT | 弹窗大小(small/medium/large/full) | ❌ |
| show_header | INTEGER | 是否显示头部(1=显示) | ❌ |
| show_footer | INTEGER | 是否显示底部(1=显示) | ❌ |
| show_close_button | INTEGER | 是否显示关闭按钮(1=显示) | ❌ |
| show_confirm_button | INTEGER | 是否显示确认按钮(1=显示) | ❌ |
| confirm_button_text | TEXT | 确认按钮文字 | ❌ |
| cancel_button_text | TEXT | 取消按钮文字 | ❌ |
| auto_close | INTEGER | 是否自动关闭(1=自动关闭) | ❌ |
| auto_close_delay | INTEGER | 自动关闭延迟(毫秒) | ❌ |
| backdrop | INTEGER | 是否显示遮罩层(1=显示) | ❌ |
| keyboard | INTEGER | 是否支持键盘关闭(1=支持) | ❌ |
| draggable | INTEGER | 是否可拖拽(1=可拖拽) | ❌ |
| resizable | INTEGER | 是否可调整大小(1=可调整) | ❌ |
| position | TEXT | 弹窗位置(center/top/top-right/bottom/bottom-right) | ❌ |
| animation_enabled | INTEGER | 是否启用动画(1=启用) | ❌ |
| animation_type | TEXT | 动画类型(fade/zoom/slide-up/slide-down/slide-left/slide-right) | ❌ |
| enabled | INTEGER | 是否启用(1=启用) | ❌ |
| description | TEXT | 弹窗描述 | ❌ |
| created_at | TEXT | 创建时间 | ✅ |
| updated_at | TEXT | 更新时间 | ✅ |

#### 8.21.4 弹窗文档表结构

弹窗文档内容统一记录到 `dialog_documents` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| document_id | TEXT | 文档ID(唯一) | ✅ |
| document_name | TEXT | 文档名称 | ✅ |
| document_type | TEXT | 文档类型(welcome/instruction/notification/guide) | ❌ |
| dialog_id | TEXT | 关联的弹窗ID | ❌ |
| content | TEXT | 文档内容 | ❌ |
| version | TEXT | 文档版本 | ❌ |
| language | TEXT | 文档语言(zh-CN/en-US) | ❌ |
| target_users | TEXT | 目标用户(all/student/teacher/admin) | ❌ |
| display_condition | TEXT | 显示条件(JSON) | ❌ |
| display_order | INTEGER | 显示顺序 | ❌ |
| enabled | INTEGER | 是否启用(1=启用) | ❌ |
| created_at | TEXT | 创建时间 | ✅ |
| updated_at | TEXT | 更新时间 | ✅ |

#### 8.21.5 弹窗类型定义

| 类型 | 说明 | 适用场景 | 默认大小 |
|------|------|---------|---------|
| modal | 模态弹窗 | 表单、确认操作、详情展示 | medium |
| toast | 轻提示 | 操作成功/失败提示 | small |
| notification | 通知弹窗 | 系统通知、消息提醒 | medium |
| confirm | 确认弹窗 | 确认操作、删除确认 | small |

#### 8.21.6 弹窗大小定义

| 大小 | 宽度范围 | 适用场景 |
|------|---------|---------|
| small | 300-400px | 确认对话框、简单提示 |
| medium | 400-600px | 表单、详情、说明文档 |
| large | 600-800px | 长文档、复杂表单 |
| full | 100% | 全屏展示、引导页面 |

#### 8.21.7 弹窗位置定义

| 位置 | 说明 | 适用场景 |
|------|------|---------|
| center | 居中显示 | 模态框、确认框、表单 |
| top | 顶部居中 | 通知、欢迎提示 |
| top-right | 右上角 | 通知、消息提醒 |
| bottom | 底部居中 | 操作提示、Toast |
| bottom-right | 右下角 | 通知、消息提醒 |

#### 8.21.8 弹窗动画类型

| 类型 | 说明 | 适用场景 |
|------|------|---------|
| fade | 淡入淡出 | 通用弹窗 |
| zoom | 缩放显示 | 模态框、详情 |
| slide-up | 从下向上滑入 | 底部弹窗 |
| slide-down | 从上向下滑入 | 顶部弹窗 |
| slide-left | 从右向左滑入 | 侧边栏 |
| slide-right | 从左向右滑入 | 侧边栏 |

#### 8.21.9 弹窗文档类型

| 类型 | 说明 | 显示时机 |
|------|------|---------|
| welcome | 欢迎文档 | 用户首次登录、系统更新后 |
| instruction | 说明文档 | 用户进入特定功能模块时 |
| notification | 通知文档 | 系统有重要通知时 |
| guide | 引导文档 | 新功能上线、操作引导 |

#### 8.21.10 弹窗显示规则

| 规则项 | 说明 | 默认值 |
|--------|------|--------|
| 欢迎文档显示 | 是否显示欢迎文档 | 启用 |
| 欢迎文档只显示一次 | 是否只在首次登录显示 | 是 |
| 欢迎文档显示间隔 | 重复显示间隔(天) | 0(只显示一次) |
| 说明文档显示 | 是否显示说明文档 | 启用 |
| 说明文档只显示一次 | 是否只显示一次 | 是 |
| 说明文档显示间隔 | 重复显示间隔(天) | 0(只显示一次) |
| 通知文档显示 | 是否显示通知文档 | 启用 |
| 通知自动关闭 | 通知弹窗是否自动关闭 | 是 |
| 通知自动关闭延迟 | 通知自动关闭延迟(毫秒) | 5000 |

#### 8.21.11 弹窗文档显示条件

| 条件类型 | 说明 | 示例 |
|----------|------|------|
| 用户角色 | 按用户角色过滤 | student/teacher/admin |
| 用户组别 | 按用户组别过滤 | adult/k12 |
| 登录次数 | 按登录次数过滤 | login_count <= 1 |
| 时间条件 | 按时间过滤 | show_start <= now <= show_end |
| 功能模块 | 按功能模块过滤 | exam_system/math_training |
| 系统版本 | 按系统版本过滤 | version >= '10.0.0' |

#### 8.21.12 弹窗文档加载规则

基于经验总结，前端调取弹窗文档数据必须从数据库同步读取：

```python
def load_dialog_document(document_id):
    """从数据库加载弹窗文档"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT document_name, document_type, content, version, language, 
                       target_users, display_condition, display_order, enabled
                FROM dialog_documents 
                WHERE document_id = ? AND enabled = 1
            ''', (document_id,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'document_id': document_id,
                    'document_name': result[0],
                    'document_type': result[1],
                    'content': result[2],
                    'version': result[3],
                    'language': result[4],
                    'target_users': result[5],
                    'display_condition': result[6],
                    'display_order': result[7],
                    'enabled': result[8],
                    'source': 'database'
                }
            return None
    except Exception as e:
        logger.error(f"加载弹窗文档失败: {str(e)}")
        return None
```text

#### 8.21.13 弹窗文档同步规则

| 同步项 | 规则 |
|--------|------|
| 数据来源 | 必须从database读取，禁止硬编码 |
| 同步时机 | 每次前端加载弹窗时 |
| 数据一致性 | 确保与数据库数据一致 |
| 写穿机制 | 文档修改后立即同步到数据库 |
| 版本管理 | 支持文档版本记录 |
| 缓存策略 | 可配置文档缓存，缓存有效期从system_rules读取 |

### 8.22 版本历史规则

#### 8.22.1 版本历史概述

版本历史规则用于管理系统的版本升级记录和历史追溯。系统每次升级必须记录到`system_version_history`表，包含版本号、代号、状态、描述、特性、升级说明等信息。

#### 8.22.2 版本历史表结构

版本历史统一记录到 `system_version_history` 表：

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ |
| version | TEXT | 版本号(语义化) | ✅ |
| major | INTEGER | 主版本号 | ✅ |
| minor | INTEGER | 次版本号 | ✅ |
| patch | INTEGER | 补丁版本号 | ✅ |
| build_number | TEXT | 构建编号 | ❌ |
| build_date | TEXT | 构建日期 | ❌ |
| codename | TEXT | 版本代号 | ❌ |
| status | TEXT | 版本状态(stable/beta/alpha/dev) | ❌ |
| description | TEXT | 版本描述 | ❌ |
| features | TEXT | 新增特性(JSON数组) | ❌ |
| upgrade_notes | TEXT | 升级说明 | ❌ |
| upgrade_time | TEXT | 升级时间 | ❌ |
| upgrade_type | TEXT | 升级类型(manual/automatic) | ❌ |
| applied_by | TEXT | 升级执行者 | ❌ |
| notes | TEXT | 备注 | ❌ |
| previous_version | TEXT | 前一版本号 | ❌ |
| schema_version | INTEGER | 数据库架构版本 | ❌ |
| created_at | TEXT | 创建时间 | ✅ |

#### 8.22.3 版本号规则

| 版本类型 | 格式 | 说明 | 示例 |
|----------|------|------|------|
| 主版本 | X.0.0 | 重大功能变更，可能不兼容 | 2.0.0 |
| 次版本 | X.Y.0 | 新增功能，向后兼容 | 2.1.0 |
| 补丁版本 | X.Y.Z | Bug修复，向后兼容 | 2.1.1 |
| 预发布 | X.Y.Z-alpha.N | 预发布版本 | 2.0.0-alpha.1 |

#### 8.22.4 版本状态规则

| 状态 | 说明 | 适用场景 |
|------|------|---------|
| stable | 稳定版 | 正式发布，经过充分测试 |
| beta | 测试版 | 功能完整，公开测试 |
| alpha | 内测版 | 功能开发中，内部测试 |
| dev | 开发版 | 开发中，不对外发布 |

#### 8.22.5 系统版本演进历史

| 版本 | 代号 | 发布日期 | 核心特性 |
|------|------|---------|---------|
| 1.0.0 | Initial Release | 2026-01-01 | 用户认证系统、基础考试系统、数据库架构 |
| 2.0.0 | AI Integration Edition | 2026-02-15 | AI引擎系统、AI员工基础架构、AI学习能力 |
| 3.0.0 | Knowledge Brain Edition | 2026-03-01 | AI脑库系统、知识管理、知识检索、知识增强 |
| 4.0.0 | Security Enhancement Edition | 2026-04-01 | 数据库加密、安全中间件、权限管理、会话超时 |
| 5.0.0 | Exam System Enhancement | 2026-05-01 | 听力题支持、自动阅卷、AI组卷、科目分类 |
| 6.0.0 | Git Sync Edition | 2026-05-15 | Git自动同步、远程更新检测、数据库迁移、AI配置升级 |
| 7.0.0 | Maintenance Rules Edition | 2026-06-01 | system_rules表、自动修复系统、权限同步、灰度发布 |
| 8.0.0 | AI Employee Empowerment Edition | 2026-06-15 | 智能赋能系统、性格模拟、网络学习、技能升级 |
| 9.0.0 | Data Sync Edition | 2026-07-01 | 数据同步机制、写穿机制、前端数据同步、缓存策略 |
| 10.0.0 | Comprehensive Rules Edition | 2026-07-15 | 沙盒规则系统、网络规则系统、协议规则系统、端口规则系统、文档规则系统、前端样式规范、弹窗文档规则、例行维护规则 |

#### 8.22.6 例行维护任务规则

| 维护项 | 规则 | 频率 |
|--------|------|------|
| 清理过期会话 | 删除expires_at过期的会话记录 | 每次维护 |
| 更新规则状态 | 将is_active为NULL的规则设为1 | 每次维护 |
| 统计规则数量 | 统计总规则数和启用规则数 | 每次维护 |
| 数据库完整性检查 | 执行PRAGMA integrity_check | 每次维护 |
| 清理旧日志 | 删除超过90天的维护日志 | 每日 |
| 更新版本号 | 同步system_rules中的版本号 | 版本升级时 |
| 记录维护日志 | 将维护操作记录到system_maintenance_logs | 每次维护 |

#### 8.22.7 版本升级流程

```
1. 准备阶段
   - 备份数据库
   - 检查当前版本
   - 确认目标版本

2. 执行阶段
   - 更新system_version_history表
   - 更新system_rules中的版本号
   - 执行数据库迁移
   - 更新AI员工配置

3. 验证阶段
   - 检查数据库完整性
   - 验证规则数量
   - 测试核心功能

4. 记录阶段
   - 记录维护日志
   - 记录升级时间
   - 更新previous_version
```text

#### 8.22.8 版本回滚规则

| 回滚条件 | 规则 |
|----------|------|
| 升级失败 | 自动回滚到previous_version |
| 数据库损坏 | 恢复最近备份 |
| 规则冲突 | 回滚并记录冲突原因 |
| 用户反馈 | 人工评估后决定是否回滚 |

### 8.23 自动化调度规则

#### 8.23.1 自动化调度概述

自动化调度引擎（auto_scheduler.py）根据system_rules表中的规则配置，后台自动执行维护、检查、清理、同步等任务。所有任务的执行间隔和启用状态均从数据库动态读取。

#### 8.23.2 调度引擎规则配置

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| AUTO_SCHEDULER_ENABLED | 自动化调度引擎启用 | 1 | 是否启用自动化调度引擎 |
| AUTO_SCHEDULER_LOOP_INTERVAL | 调度轮次间隔 | 30 | 调度引擎轮次间隔(秒) |
| AUTO_SCHEDULER_LOG_LEVEL | 调度日志级别 | INFO | 调度引擎日志级别 |
| AUTO_SCHEDULER_MAX_TASKS | 最大任务数 | 50 | 调度引擎最大任务数 |
| AUTO_SCHEDULER_TASK_TIMEOUT | 任务超时时间 | 300 | 单个任务最大执行时间(秒) |
| AUTO_SCHEDULER_FAILURE_ALERT | 失败告警启用 | 1 | 任务失败时是否发送告警 |
| AUTO_SCHEDULER_FAILURE_THRESHOLD | 连续失败告警阈值 | 3 | 连续失败多少次后告警 |
| AUTO_SCHEDULER_HEARTBEAT_INTERVAL | 心跳间隔 | 60 | 调度引擎心跳间隔(秒) |
| AUTO_SCHEDULER_STATS_REPORT | 统计报告间隔 | 3600 | 调度统计报告间隔(秒) |
| AUTO_SCHEDULER_AUTO_RESTART | 自动重启启用 | 1 | 调度引擎异常退出后自动重启 |
| AUTO_SCHEDULER_RESTART_DELAY | 重启延迟 | 10 | 调度引擎重启延迟(秒) |
| AUTO_SCHEDULER_DB_LOG_ENABLED | 数据库日志记录启用 | 1 | 调度任务结果是否记录到数据库 |

#### 8.23.3 自动化任务配置

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| AUTO_TASK_DB_HEALTH_CHECK | 数据库健康检查 | 1 | 数据库完整性检查(每60秒) |
| AUTO_TASK_RULE_STATUS_SYNC | 规则状态同步 | 1 | 规则is_active状态同步(每3600秒) |
| AUTO_TASK_LOG_CLEANUP | 日志清理 | 1 | 过期维护日志清理(每604800秒) |
| AUTO_TASK_VERSION_CHECK | 版本号检查 | 1 | 版本号一致性检查(每3600秒) |
| AUTO_TASK_AI_EMPLOYEE_CHECK | AI员工检查 | 1 | AI员工状态统计(每1800秒) |
| AUTO_TASK_GIT_SYNC | Git同步检查 | 1 | Git未提交变更检查(每1800秒) |
| AUTO_TASK_PERMISSION_SYNC | 权限同步 | 1 | 权限自动同步(每3600秒) |
| AUTO_TASK_SANDBOX_HEALTH | 沙盒健康检查 | 1 | 沙盒实例状态检查(每60秒) |
| AUTO_TASK_DOCUMENT_CLEANUP | 文档清理 | 1 | 过期文档归档(每86400秒) |
| AUTO_TASK_AUTOFIX_MONITOR | 自动修复监控 | 1 | 修复记录状态监控(每60秒) |
| AUTO_TASK_ARRAY_SYNC | 阵列同步检查 | 1 | AI集群员工状态(每600秒) |
| AUTO_TASK_ENGINE_HEALTH | 引擎健康检查 | 1 | AI引擎状态检查(每60秒) |
| AUTO_TASK_EMPLOYEE_LOG_CLEANUP | 员工日志清理 | 1 | AI任务日志清理(每604800秒) |

#### 8.23.4 任务执行规则

| 规则 | 说明 |
|------|------|
| 间隔驱动 | 每个任务从system_rules读取自己的间隔配置 |
| 首次立即执行 | 调度引擎启动时立即执行一轮所有任务 |
| 幂等执行 | 任务可重复执行不会产生副作用 |
| 异常隔离 | 单个任务失败不影响其他任务 |
| 日志记录 | 所有任务结果记录到system_maintenance_logs表 |
| 统计追踪 | 记录总执行次数、成功数、失败数 |

#### 8.23.5 调度引擎架构

```
AutoScheduler
├── _get_rule_value()        # 从system_rules读取配置
├── _should_run()            # 判断任务是否到达执行时间
├── _log_maintenance()       # 记录到system_maintenance_logs
├── _update_stats()          # 更新执行统计
├── task_*()                 # 13个维护任务
├── run_once()               # 执行一轮所有任务
├── run_forever()            # 持续后台运行
└── get_status()             # 获取引擎状态
```text

#### 8.23.6 启动和停止

```bash
# 后台启动调度引擎（推荐使用控制脚本）
python3 scheduler_control.py start

# 单次执行（用于验证）
python3 auto_scheduler.py --once

# 停止调度引擎（带警告框和原因确认）
python3 scheduler_control.py stop

# 重启调度引擎
python3 scheduler_control.py restart

# 查看调度引擎状态
python3 scheduler_control.py status

# 查看操作日志
python3 scheduler_control.py logs

# 直接后台启动（不使用控制脚本）
nohup python3 auto_scheduler.py > /dev/null 2>&1 &
```text

#### 8.23.7 进程保护规则

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| AUTO_SCHEDULER_PROTECTION_ENABLED | 进程保护启用 | 1 | 是否启用调度引擎进程保护 |
| AUTO_SCHEDULER_PREVENT_ACCIDENTAL_KILL | 防止意外终止 | 1 | 拦截SIGTERM/SIGINT信号，防止意外kill |
| AUTO_SCHEDULER_TERMINATION_WARNING_ENABLED | 终止警告启用 | 1 | 人工终止时显示macOS原生警告框 |
| AUTO_SCHEDULER_TERMINATION_REQUIRE_CONFIRM | 终止需确认 | 1 | 终止需要二次确认 |
| AUTO_SCHEDULER_TERMINATION_REQUIRE_REASON | 终止需填写原因 | 1 | 终止需要填写原因 |
| AUTO_SCHEDULER_TERMINATION_REASON_MIN_LENGTH | 终止原因最小长度 | 10 | 终止原因最少字符数 |
| AUTO_SCHEDULER_AUTO_RESTART_ON_KILL | 被kill后自动重启 | 1 | 被意外kill后自动重启 |
| AUTO_SCHEDULER_RESTART_MAX_RETRIES | 重启最大重试次数 | 5 | 自动重启最大重试次数 |
| AUTO_SCHEDULER_RESTART_BACKOFF | 重启退避时间 | 30 | 重启退避等待时间(秒) |
| AUTO_SCHEDULER_HEARTBEAT_TIMEOUT | 心跳超时 | 120 | 心跳超时判定进程死亡(秒) |
| AUTO_SCHEDULER_WATCHDOG_ENABLED | 看门狗启用 | 1 | 看门狗监控调度引擎 |
| AUTO_SCHEDULER_WATCHDOG_INTERVAL | 看门狗检查间隔 | 30 | 看门狗检查间隔(秒) |
| AUTO_SCHEDULER_LOG_ALL_OPERATIONS | 记录所有操作 | 1 | 所有操作记录到数据库 |
| AUTO_SCHEDULER_ALERT_ON_TERMINATION | 终止告警 | 1 | 进程被终止时发送告警 |
| AUTO_SCHEDULER_ALERT_ADMIN_USERS | 告警管理员 | wuchenghao15 | 接收告警的管理员用户名 |

#### 8.23.8 进程保护机制

```
┌─────────────────────────────────────────────────────────┐
│                   调度引擎进程保护架构                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐    SIGTERM/SIGINT    ┌──────────────┐ │
│  │  外部信号    │ ──────────────────→ │  信号拦截器   │ │
│  │  (kill/Ctrl+C)│                    │  (signal)    │ │
│  └─────────────┘                      └──────┬───────┘ │
│                                              │         │
│                                    PREVENT_ACCIDENTAL   │
│                                      _KILL == 1?       │
│                                              │         │
│                           ┌──────────────────┼─────┐   │
│                           │ 是               │ 否  │   │
│                           ▼                  ▼     │   │
│                    ┌──────────┐      ┌──────────┐  │   │
│                    │ 忽略信号  │      │ 正常停止  │  │   │
│                    │ 更新心跳  │      │          │  │   │
│                    │ 记录日志  │      │          │  │   │
│                    └──────────┘      └──────────┘  │   │
│                                                  │   │   │
│  ┌─────────────────────────────────────────────┐ │   │   │
│  │          人工终止流程 (scheduler_control.py)  │ │   │   │
│  │                                             │ │   │   │
│  │  1. 显示macOS原生警告框(列出受影响任务)       │ │   │   │
│  │  2. 用户确认终止                             │ │   │   │
│  │  3. 填写终止原因(≥10字符)                    │ │   │   │
│  │  4. 记录操作日志到数据库                      │ │   │   │
│  │  5. 发送SIGTERM信号                          │ │   │   │
│  │  6. 等待10秒，超时则SIGKILL                   │ │   │   │
│  │  7. 清理PID文件                              │ │   │   │
│  │  8. 显示终止成功对话框                        │ │   │   │
│  └─────────────────────────────────────────────┘ │   │   │
│                                                  │   │   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │   │   │
│  │心跳文件   │  │PID文件    │  │数据库日志     │   │   │   │
│  │.scheduler│  │.scheduler │  │system_       │   │   │   │
│  │_heartbeat│  │_pid       │  │maintenance_  │   │   │   │
│  │          │  │           │  │logs          │   │   │   │
│  └──────────┘  └──────────┘  └──────────────┘   │   │   │
└─────────────────────────────────────────────────────────┘
```text

#### 8.23.9 操作日志记录规则

| 操作类型 | 记录内容 | 触发时机 |
|----------|----------|----------|
| engine_start | 引擎启动(PID、任务数) | 调度引擎启动时 |
| engine_stop | 引擎停止(PID、总执行数) | 调度引擎正常停止时 |
| engine_crash | 异常退出(错误信息) | 调度引擎异常退出时 |
| engine_error | 轮次异常(错误信息) | 调度轮次执行失败时 |
| signal_received | 收到信号(信号类型、PID) | 收到SIGTERM/SIGINT信号时 |
| start | 人工启动(PID、操作者) | 通过控制脚本启动时 |
| stop | 人工终止(PID、操作者、原因) | 通过控制脚本终止时 |
| stop_cancelled | 取消终止(原因) | 用户取消终止操作时 |
| stop_success | 终止成功(PID、操作者、原因) | 终止操作成功时 |
| stop_failed | 终止失败(PID) | 终止操作失败时 |
| force_stop | 强制终止(PID、操作者) | SIGKILL强制终止时 |
| restart | 重启请求(操作者) | 重启调度引擎时 |
| status_query | 状态查询(运行状态) | 查询引擎状态时 |

#### 8.23.10 日志文件

| 日志文件 | 说明 |
|----------|------|
| auto_scheduler.log | 调度引擎运行日志 |
| scheduler_control.log | 控制脚本操作日志 |
| .scheduler_pid | PID文件(进程标识) |
| .scheduler_heartbeat | 心跳文件(进程存活) |
| system_maintenance_logs表 | 维护操作数据库日志 |

### 8.24 系统黑匣子规则

#### 8.24.1 黑匣子概述

系统黑匣子类似飞机黑匣子记录器，在系统发生灾难级事件时完整记录上下文信息，包括：
- 灾难发生前的所有操作动作（前50条/1小时内）
- 灾难发生时的系统状态快照（内存、CPU、磁盘、网络、数据库、AI引擎）
- 灾难发生后的恢复操作和后续动作
- 相关日志记录（最近100条维护日志）
- 堆栈跟踪、进程信息、线程信息
- 所有数据一并上报数据库，永久保存

#### 8.24.2 黑匣子规则配置

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| BLACKBOX_ENABLED | 黑匣子启用 | 1 | 是否启用系统黑匣子 |
| BLACKBOX_DISASTER_LEVEL_ENABLED | 灾难级记录 | 1 | 记录灾难级事件(系统崩溃/数据丢失) |
| BLACKBOX_CRITICAL_LEVEL_ENABLED | 严重级记录 | 1 | 记录严重级事件(服务中断/异常退出) |
| BLACKBOX_WARNING_LEVEL_ENABLED | 警告级记录 | 1 | 记录警告级事件(性能下降/资源不足) |
| BLACKBOX_INFO_LEVEL_ENABLED | 信息级记录 | 0 | 记录信息级事件(常规操作) |
| BLACKBOX_CAPTURE_BEFORE_ACTIONS | 捕获前置操作 | 1 | 捕获灾难前的操作记录 |
| BLACKBOX_BEFORE_ACTION_COUNT | 前置操作数量 | 50 | 捕获灾难前多少条操作 |
| BLACKBOX_BEFORE_ACTION_TIME_WINDOW | 前置时间窗口 | 3600 | 捕获灾难前多少秒的操作 |
| BLACKBOX_CAPTURE_AFTER_ACTIONS | 捕获后置操作 | 1 | 捕获灾难后的操作记录 |
| BLACKBOX_AFTER_ACTION_COUNT | 后置操作数量 | 50 | 捕获灾难后多少条操作 |
| BLACKBOX_CAPTURE_SYSTEM_SNAPSHOT | 系统快照 | 1 | 灾难时捕获系统状态 |
| BLACKBOX_CAPTURE_STACK_TRACE | 堆栈跟踪 | 1 | 捕获异常堆栈跟踪 |
| BLACKBOX_CAPTURE_MEMORY_STATE | 内存状态 | 1 | 捕获内存使用状态 |
| BLACKBOX_CAPTURE_PROCESS_STATE | 进程状态 | 1 | 捕获进程运行状态 |
| BLACKBOX_CAPTURE_NETWORK_STATE | 网络状态 | 1 | 捕获网络连接状态 |
| BLACKBOX_CAPTURE_DB_STATE | 数据库状态 | 1 | 捕获数据库状态 |
| BLACKBOX_CAPTURE_AI_STATE | AI状态 | 1 | 捕获AI引擎和员工状态 |
| BLACKBOX_AUTO_RECOVERY_ENABLED | 自动恢复 | 1 | 灾难后自动尝试恢复 |
| BLACKBOX_AUTO_RECOVERY_MAX_RETRIES | 恢复最大重试 | 3 | 自动恢复最大重试次数 |
| BLACKBOX_ALERT_ON_DISASTER | 灾难告警 | 1 | 灾难时发送告警 |
| BLACKBOX_RETENTION_DAYS | 保留天数 | 365 | 黑匣子记录保留天数 |
| BLACKBOX_LOG_ALL_OPERATIONS | 记录所有操作 | 1 | 所有操作记录到黑匣子 |
| BLACKBOX_REAL_TIME_MONITORING | 实时监控 | 1 | 实时监控系统异常 |
| BLACKBOX_DB_LOG_ENABLED | 数据库日志 | 1 | 黑匣子记录上报数据库 |

#### 8.24.3 黑匣子数据表结构

**system_blackbox（灾难事件主表）** - 42个字段：

| 字段类别 | 关键字段 | 说明 |
|----------|----------|------|
| 事件标识 | event_id, event_type, severity | 事件ID、类型、级别 |
| 事件信息 | title, description, source_module | 标题、描述、来源模块 |
| 代码定位 | source_file, source_line, stack_trace | 文件、行号、堆栈跟踪 |
| 前后操作 | before_actions, after_actions, related_logs | 前置/后置操作、相关日志 |
| 系统状态 | system_state, database_state, memory_usage | 系统/数据库/内存状态 |
| 进程信息 | process_id, thread_id, user_session | 进程/线程/会话 |
| 恢复信息 | recovery_actions, recovery_status, recovered_at | 恢复动作/状态/时间 |
| 影响评估 | impact_scope, impact_users, data_loss_estimated | 影响范围/用户/数据丢失 |
| 解决信息 | resolved, resolved_at, resolved_by, resolution_notes | 解决状态/时间/人员/备注 |

**blackbox_action_log（操作动作记录表）** - 15个字段
**blackbox_system_snapshot（系统快照表）** - 14个字段

#### 8.24.4 灾难级别定义

| 级别 | 说明 | 示例 |
|------|------|------|
| disaster | 灾难级 | 系统崩溃、数据库损坏、数据丢失 |
| critical | 严重级 | 服务中断、调度引擎异常退出、安全漏洞 |
| warning | 警告级 | 性能下降、资源不足、连接超时 |
| info | 信息级 | 常规操作、配置变更、状态变更 |

#### 8.24.5 灾难事件类型

| 事件类型 | 说明 | 自动恢复策略 |
|----------|------|-------------|
| database_corruption | 数据库损坏 | PRAGMA integrity_check + VACUUM |
| scheduler_crash | 调度引擎崩溃 | 尝试重启调度引擎 |
| memory_exhaustion | 内存耗尽 | 清理内存缓存 |
| disk_full | 磁盘空间满 | 清理临时文件 |
| security_breach | 安全违规 | 记录并告警 |
| service_outage | 服务中断 | 尝试重启服务 |
| data_loss | 数据丢失 | 从备份恢复 |
| network_failure | 网络故障 | 检查网络连接 |
| ai_engine_failure | AI引擎故障 | 重启AI引擎 |
| scheduler_round_error | 调度轮次异常 | 记录并继续 |

#### 8.24.6 黑匣子记录流程

```
┌──────────────────────────────────────────────────────────┐
│                   黑匣子记录流程                           │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  持续运行阶段:                                            │
│  ┌──────────────┐                                        │
│  │ 操作缓冲区    │ ← record_action() 持续滚动记录          │
│  │ (500条环形)   │   用户登录/页面访问/API调用/数据库操作   │
│  └──────────────┘                                        │
│                                                          │
│  灾难发生时刻:                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │ record_disaster() 被调用                          │    │
│  ├──────────────────────────────────────────────────┤    │
│  │ 1. 采集系统状态 (内存/CPU/磁盘/线程)               │    │
│  │ 2. 采集数据库状态 (完整性/规则数/版本)              │    │
│  │ 3. 采集调度引擎状态 (PID/心跳)                     │    │
│  │ 4. 采集AI系统状态 (员工数/引擎数/任务数)            │    │
│  │ 5. 采集网络状态 (监听端口/连接数)                   │    │
│  │ 6. 获取堆栈跟踪                                  │    │
│  │ 7. 提取前置操作 (缓冲区最近50条/1小时内)            │    │
│  │ 8. 提取相关日志 (最近100条维护日志)                │    │
│  │ 9. 写入system_blackbox表                         │    │
│  │ 10. 写入blackbox_system_snapshot表               │    │
│  │ 11. 写入blackbox_action_log表(前置操作)           │    │
│  │ 12. 尝试自动恢复                                 │    │
│  │ 13. 记录恢复操作到blackbox_action_log             │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  灾难后持续阶段:                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │ record_after_action() 持续记录恢复操作             │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  数据库持久化:                                            │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │system_   │  │blackbox_     │  │blackbox_system_  │   │
│  │blackbox  │  │action_log    │  │snapshot          │   │
│  └──────────┘  └──────────────┘  └──────────────────┘   │
└──────────────────────────────────────────────────────────┘
```text

#### 8.24.7 自动恢复机制

| 恢复策略 | 触发条件 | 恢复动作 |
|----------|----------|----------|
| 数据库修复 | database_corruption | PRAGMA integrity_check + VACUUM |
| 调度引擎重启 | scheduler_crash | 尝试重启auto_scheduler.py |
| 内存清理 | memory_exhaustion | 清理内存缓存 |
| 磁盘清理 | disk_full | 清理临时文件和旧日志 |
| 通用恢复 | 其他类型 | 数据库连接检查 |

自动恢复最多重试3次，每次间隔5秒。恢复成功后自动标记事件为已解决。

#### 8.24.8 API接口

```python
from blackbox_recorder import record_disaster, record_action, get_blackbox

# 记录操作（持续滚动记录）
record_action('user_login', action_details='用户登录', action_user='wuchenghao15')

# 记录灾难事件
event_id = record_disaster(
    event_type='database_corruption',
    title='数据库完整性检查失败',
    description='PRAGMA integrity_check返回错误',
    severity='disaster',
    source_module='database_service',
    impact_scope='全部数据库功能'
)

# 获取灾难列表
bb = get_blackbox()
disasters = bb.get_disasters(limit=20, resolved=False)

# 获取事件详情（含前置操作、后置操作、系统快照）
detail = bb.get_event_detail(event_id)

# 标记事件已解决
bb.resolve_event(event_id, resolved_by='admin', notes='手动修复完成')

# 使用装饰器自动捕获异常
@disaster_handler('api_error', 'API接口异常')
def api_function():
    ...
```text

#### 8.24.9 日志文件

| 日志文件 | 说明 |
|----------|------|
| blackbox.log | 黑匣子引擎运行日志 |
| system_blackbox表 | 灾难事件主表(42字段) |
| blackbox_action_log表 | 操作动作记录表(15字段) |
| blackbox_system_snapshot表 | 系统快照表(14字段) |

### 8.25 脑库数据投喂规则

#### 8.25.1 投喂机制概述

AI脑库数据投喂引擎定时向脑库注入知识数据，驱动AI员工学习、升级、神经网络训练和集群统筹，形成完整的AI自进化闭环：

```
知识投喂 → AI学习 → AI升级 → 神经网络训练 → 集群统筹 → 统计报告
    ↑                                                    │
    └────────────────── 反馈优化 ←────────────────────────┘
```text

#### 8.25.2 投喂机制规则配置

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| BRAIN_FEEDING_ENABLED | 脑库投喂启用 | 1 | 是否启用AI脑库数据投喂 |
| BRAIN_FEEDING_INTERVAL | 投喂间隔 | 300 | 脑库数据投喂间隔(秒) |
| BRAIN_LEARNING_ENABLED | AI学习启用 | 1 | 是否启用AI定时学习 |
| BRAIN_LEARNING_INTERVAL | 学习间隔 | 600 | AI定时学习间隔(秒) |
| BRAIN_UPGRADE_ENABLED | AI升级启用 | 1 | 是否启用AI定时升级 |
| BRAIN_UPGRADE_INTERVAL | 升级间隔 | 1800 | AI定时升级间隔(秒) |
| BRAIN_UPGRADE_THRESHOLD | 升级阈值 | 0.8 | AI升级置信度阈值 |
| BRAIN_NEURAL_NETWORK_ENABLED | 神经网络启用 | 1 | 是否启用AI神经元网络 |
| BRAIN_NEURAL_TRAINING_INTERVAL | 神经网络训练间隔 | 900 | 神经网络训练间隔(秒) |
| BRAIN_NEURAL_MAX_NODES | 最大节点数 | 200 | 神经网络最大节点数 |
| BRAIN_NEURAL_MAX_CONNECTIONS | 最大连接数 | 1000 | 神经网络最大连接数 |
| BRAIN_NEURAL_LEARNING_RATE | 学习率 | 0.01 | 神经网络学习率 |
| BRAIN_NEURAL_AUTO_EXPAND | 自动扩展 | 1 | 神经网络自动扩展节点 |
| BRAIN_NEURAL_PRUNE_ENABLED | 修剪启用 | 1 | 修剪低权重连接 |
| BRAIN_NEURAL_PRUNE_THRESHOLD | 修剪阈值 | 0.1 | 连接权重低于此值则修剪 |
| BRAIN_CLUSTER_COORDINATION_ENABLED | 集群统筹启用 | 1 | 是否启用AI集群统筹 |
| BRAIN_CLUSTER_COORDINATION_INTERVAL | 集群统筹间隔 | 1200 | AI集群统筹间隔(秒) |
| BRAIN_FEEDING_BATCH_SIZE | 投喂批量 | 10 | 每次投喂的数据批量 |
| BRAIN_LEARNING_MASTERY_THRESHOLD | 掌握阈值 | 0.85 | 学习掌握度阈值 |
| BRAIN_UPGRADE_MAX_LEVEL | 最大等级 | 10 | AI员工最大升级等级 |

#### 8.25.3 投喂机制数据表

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| brain_feeding_queue | 投喂队列表 | feed_id, feed_type, feed_data, status |
| brain_learning_records | 学习记录表 | record_id, employee_id, proficiency_before/after |
| neural_network_nodes | 神经网络节点表 | node_id, node_type, node_layer, weight, bias, accuracy |
| neural_network_connections | 神经网络连接表 | connection_id, source/target_node_id, weight |
| ai_upgrade_records | AI升级记录表 | upgrade_id, employee_id, before/after_level |
| cluster_coordination_records | 集群统筹记录表 | coordination_id, cluster_id, efficiency_score |
| brain_feeding_stats | 投喂统计表 | stat_date, total_feeds, knowledge_count |

#### 8.25.4 神经网络架构

```
┌────────────────────────────────────────────────────┐
│              AI神经元网络架构                        │
├────────────────────────────────────────────────────┤
│                                                    │
│  输入层(Layer 0)                                   │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │数据  │ │知识  │ │任务  │ │信号  │              │
│  │采集  │ │输入  │ │接收  │ │感知  │              │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘              │
│     │        │        │        │                   │
│  隐藏层1(Layer 1) - 特征提取                      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │特征  │ │模式  │ │知识  │ │意图  │              │
│  │分析  │ │识别  │ │匹配  │ │理解  │              │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘              │
│     │        │        │        │                   │
│  隐藏层2(Layer 2) - 决策推理                      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │策略  │ │风险  │ │资源  │ │任务  │              │
│  │选择  │ │评估  │ │规划  │ │分解  │              │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘              │
│     │        │        │        │                   │
│  隐藏层3(Layer 3) - 执行控制                      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │执行  │ │监控  │ │异常  │ │结果  │              │
│  │调度  │ │反馈  │ │处理  │ │验证  │              │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘              │
│     │        │        │        │                   │
│  输出层(Layer 4)                                  │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │任务  │ │知识  │ │决策  │ │状态  │              │
│  │输出  │ │输出  │ │输出  │ │上报  │              │
│  └──────┘ └──────┘ └──────┘ └──────┘              │
│                                                    │
│  + 自动扩展节点(自适应/动态学习/协同处理/模式优化)  │
│  + 连接权重自动训练(学习率0.01)                     │
│  + 低权重连接自动修剪(阈值0.1)                      │
└────────────────────────────────────────────────────┘
```text

#### 8.25.5 调度任务集成

脑库投喂引擎已集成到自动化调度引擎(auto_scheduler.py)，新增5个定时任务：

| 任务名称 | 间隔规则 | 默认间隔 | 功能 |
|----------|----------|----------|------|
| brain_feeding | BRAIN_FEEDING_INTERVAL | 300秒 | 知识投喂到脑库 |
| brain_learning | BRAIN_LEARNING_INTERVAL | 600秒 | AI员工学习 |
| brain_upgrade | BRAIN_UPGRADE_INTERVAL | 1800秒 | AI员工升级 |
| neural_training | BRAIN_NEURAL_TRAINING_INTERVAL | 900秒 | 神经网络训练 |
| cluster_coordination | BRAIN_CLUSTER_COORDINATION_INTERVAL | 1200秒 | 集群统筹协调 |

#### 8.25.6 知识类型

| 类型 | 说明 | 示例 |
|------|------|------|
| system | 系统知识 | 架构设计、安全防护、AI架构 |
| technical | 技术知识 | Python、前端、数据库 |
| business | 业务知识 | 教育系统、考试评价、K12分类 |
| training | 培训知识 | AI运维、日志分析、容器化 |
| experience | 经验知识 | 数据同步、权限控制、性能优化 |

#### 8.25.7 学习掌握度等级

| 等级 | 熟练度范围 | 说明 |
|------|-----------|------|
| beginner | < 0.3 | 初学者 |
| intermediate | 0.3 - 0.6 | 中级 |
| advanced | 0.6 - 0.85 | 高级 |
| master | >= 0.85 | 专家 |

#### 8.25.8 日志文件

| 日志文件 | 说明 |
|----------|------|
| brain_feeding.log | 投喂引擎运行日志 |
| system_maintenance_logs表 | 维护操作数据库日志 |
| brain_feeding_stats表 | 投喂统计表 |

### 8.26 自动修复规则

#### 8.26.1 自动修复机制概述

自动修复引擎定时扫描项目异常和错误，自动匹配修复方案并执行修复，将修复方案和案例上报到数据库和日志，同时投喂脑库供AI学习，形成完整的"扫描→匹配→修复→记录→学习"闭环：

```
错误扫描 → 方案匹配 → 执行修复 → 记录案例 → 投喂脑库 → 自学习
   ↑                                              │
   └──────────────── 新方案反馈 ←──────────────────┘
```text

错误来源覆盖4个渠道：
- error_logs表（后端未解决错误）
- error_reports表（前端错误上报）
- system_maintenance_logs表（维护失败操作）
- 日志文件（Traceback/Error/Exception/CRITICAL/FATAL）

#### 8.26.2 自动修复规则配置

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| AUTO_REPAIR_ENABLED | 自动修复启用 | 1 | 是否启用自动修复引擎 |
| AUTO_REPAIR_SCAN_INTERVAL | 修复扫描间隔 | 60 | 错误扫描间隔(秒) |
| AUTO_REPAIR_AUTO_EXECUTE | 自动执行修复 | 1 | 匹配到方案后是否自动执行 |
| AUTO_REPAIR_CONFIDENCE_THRESHOLD | 修复置信度阈值 | 0.7 | 方案置信度低于此值不执行 |
| AUTO_REPAIR_MAX_RETRIES | 修复最大重试 | 3 | 单个错误修复重试次数 |
| AUTO_REPAIR_MAX_CONCURRENT | 最大并发修复 | 5 | 同时修复的最大错误数 |
| AUTO_REPAIR_TIMEOUT | 修复超时 | 300 | 单次修复超时(秒) |
| AUTO_REPAIR_BACKUP_BEFORE | 修复前备份 | 1 | 修复前备份原始状态 |
| AUTO_REPAIR_ROLLBACK_ON_FAIL | 失败回滚 | 1 | 修复失败时回滚 |
| AUTO_REPAIR_SCAN_ERROR_LOGS | 扫描error_logs表 | 1 | 扫描后端错误日志 |
| AUTO_REPAIR_SCAN_ERROR_REPORTS | 扫描error_reports表 | 1 | 扫描前端错误上报 |
| AUTO_REPAIR_SCAN_MAINTENANCE_LOGS | 扫描维护日志 | 1 | 扫描维护失败操作 |
| AUTO_REPAIR_SCAN_LOG_FILES | 扫描日志文件 | 1 | 扫描.log文件中的错误 |
| AUTO_REPAIR_SCAN_BLACKBOX | 扫描黑匣子事件 | 1 | 扫描黑匣子灾难事件 |
| AUTO_REPAIR_LOG_FILE_PATTERNS | 日志文件匹配模式 | *.log | 日志文件glob模式 |
| AUTO_REPAIR_LOG_LEVEL | 修复日志级别 | INFO | 日志输出级别 |
| AUTO_REPAIR_RECORD_SOLUTION | 记录修复方案 | 1 | 是否记录修复方案 |
| AUTO_REPAIR_RECORD_CASE | 记录修复案例 | 1 | 是否记录修复案例 |
| AUTO_REPAIR_REPORT_DATABASE | 上报数据库 | 1 | 修复结果上报数据库 |
| AUTO_REPAIR_REPORT_BLACKBOX | 上报黑匣子 | 1 | 修复失败上报黑匣子 |
| AUTO_REPAIR_FEED_BRAIN | 投喂脑库 | 1 | 修复案例投喂脑库 |
| AUTO_REPAIR_SELF_LEARNING | 自学习启用 | 1 | 从修复记录提取新方案 |
| AUTO_REPAIR_NOTIFICATION | 修复通知 | 1 | 修复完成通知 |
| AUTO_REPAIR_SCAN_SOURCE_CODE | 扫描源代码 | 1 | 是否扫描Python/JS/HTML等源代码文件 |
| AUTO_REPAIR_SCAN_SCRIPTS | 扫描脚本文件 | 1 | 是否扫描Shell/Bat脚本文件 |
| AUTO_REPAIR_SCAN_TEXT_FILES | 扫描文本文件 | 1 | 是否扫描TXT/MD/JSON/YAML文本文件 |
| AUTO_REPAIR_SOURCE_CODE_EXTENSIONS | 源代码扩展名 | .py,.js,.jsx,.ts,.tsx,.html,.css,.vue | 源代码文件扩展名列表 |
| AUTO_REPAIR_SCRIPT_EXTENSIONS | 脚本扩展名 | .sh,.bat,.cmd,.ps1 | 脚本文件扩展名列表 |
| AUTO_REPAIR_TEXT_EXTENSIONS | 文本扩展名 | .txt,.md,.json,.yaml,.yml,.xml,.ini,.conf,.cfg | 文本文件扩展名列表 |
| AUTO_REPAIR_MAX_FILE_SIZE | 最大文件大小 | 512 | 扫描文件最大大小(KB) |
| AUTO_REPAIR_SYNTAX_CHECK | 语法检查启用 | 1 | 是否对源代码执行语法检查 |
| AUTO_REPAIR_STATIC_ANALYSIS | 静态分析启用 | 1 | 是否对源代码执行静态分析 |
| AUTO_REPAIR_SCAN_EXCLUDE_DIRS | 排除目录 | node_modules,.git,__pycache__,venv,env,.venv,backups | 扫描时排除的目录 |
| AUTO_REPAIR_MAX_FILES_PER_SCAN | 单次最大扫描文件数 | 200 | 单次扫描最大文件数量 |
| AUTO_REPAIR_AUTO_FIX_SYNTAX | 自动修复语法 | 1 | 是否自动修复简单语法错误 |
| AUTO_REPAIR_AUTO_FIX_ENCODING | 自动修复编码 | 1 | 是否自动修复文件编码问题 |
| AUTO_REPAIR_BACKUP_FILE_BEFORE_FIX | 修复前备份文件 | 1 | 修复源代码前备份原文件 |
| ERROR_PAGE_AUTO_LOG | 错误页面自动记录 | 1 | 是否自动记录所有错误页面访问到数据库 |
| ERROR_PAGE_REPORT_TO_DB | 错误页面上报数据库 | 1 | 是否将错误页面访问上报到error_logs表 |
| ERROR_PAGE_SCAN_INTERVAL | 错误页面扫描间隔 | 60 | 错误页面扫描间隔(秒) |
| ERROR_PAGE_AUTO_REPAIR | 错误页面自动修复 | 1 | 是否自动修复错误页面相关问题 |
| ERROR_PAGE_400_ENABLE | 400错误记录 | 1 | 是否记录400错误 |
| ERROR_PAGE_401_ENABLE | 401错误记录 | 1 | 是否记录401错误 |
| ERROR_PAGE_403_ENABLE | 403错误记录 | 1 | 是否记录403错误 |
| ERROR_PAGE_500_ENABLE | 500错误记录 | 1 | 是否记录500错误 |
| ERROR_PAGE_MAX_RECORDS_PER_DAY | 每日最大记录数 | 1000 | 每日每个错误类型最大记录数 |
| ERROR_PAGE_RETRY_ON_500 | 500错误重试 | 1 | 是否对500错误尝试自动重试 |

#### 8.26.3 自动修复数据表

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| repair_solutions | 修复方案库 | solution_id, error_pattern, fix_strategy, confidence_score, success_count, success_rate |
| auto_repair_executions | 修复执行记录 | execution_id, error_source, matched_solution_id, repair_result, repair_duration, validation_result |
| repair_cases | 修复案例库 | case_id, execution_id, root_cause, fix_approach, lessons_learned, prevention_measures, feeding_to_brain |

**repair_solutions（修复方案库）字段明细：**

| 字段 | 类型 | 说明 |
|------|------|------|
| solution_id | TEXT | 方案ID（唯一） |
| error_pattern | TEXT | 错误正则匹配模式 |
| error_type | TEXT | 错误类型 |
| error_category | TEXT | 错误分类 |
| solution_title | TEXT | 方案标题 |
| solution_description | TEXT | 方案描述 |
| solution_steps | TEXT | 修复步骤(JSON) |
| solution_code | TEXT | 修复代码示例 |
| fix_strategy | TEXT | 修复策略标识 |
| confidence_score | REAL | 置信度(0.0-1.0) |
| success_count | INTEGER | 成功次数 |
| failure_count | INTEGER | 失败次数 |
| total_attempts | INTEGER | 总尝试次数 |
| success_rate | REAL | 成功率 |
| avg_fix_duration | REAL | 平均修复耗时(秒) |
| applicable_modules | TEXT | 适用模块 |
| severity_level | TEXT | 严重级别 |
| tags | TEXT | 标签 |
| case_examples | TEXT | 案例示例 |
| status | TEXT | 状态(active/inactive) |
| created_by | TEXT | 创建者 |

**auto_repair_executions（修复执行记录）字段明细：**

| 字段 | 类型 | 说明 |
|------|------|------|
| execution_id | TEXT | 执行ID（唯一） |
| error_source | TEXT | 错误来源(error_logs/error_reports/maintenance_logs/log_file) |
| error_id | TEXT | 原始错误ID |
| error_type | TEXT | 错误类型 |
| error_message | TEXT | 错误消息 |
| error_stack_trace | TEXT | 错误堆栈 |
| error_file | TEXT | 错误文件 |
| error_line | TEXT | 错误行号 |
| matched_solution_id | TEXT | 匹配的方案ID |
| match_confidence | REAL | 匹配置信度 |
| repair_strategy | TEXT | 修复策略 |
| repair_actions | TEXT | 修复动作(JSON) |
| repair_result | TEXT | 修复结果(success/failed/unmatched) |
| repair_duration | REAL | 修复耗时(秒) |
| before_state | TEXT | 修复前状态 |
| after_state | TEXT | 修复后状态 |
| validation_result | TEXT | 验证结果 |
| rollback_performed | INTEGER | 是否回滚 |
| rollback_reason | TEXT | 回滚原因 |
| reported_to_blackbox | INTEGER | 是否上报黑匣子 |
| blackbox_event_id | TEXT | 黑匣子事件ID |
| reported_to_database | INTEGER | 是否上报数据库 |
| ai_employee_assigned | TEXT | 分配的AI员工 |
| neural_nodes_activated | TEXT | 激活的神经元节点 |
| learning_extracted | TEXT | 提取的学习内容 |
| case_recorded | INTEGER | 是否记录案例 |

**repair_cases（修复案例库）字段明细：**

| 字段 | 类型 | 说明 |
|------|------|------|
| case_id | TEXT | 案例ID（唯一） |
| execution_id | TEXT | 关联执行ID |
| solution_id | TEXT | 关联方案ID |
| error_summary | TEXT | 错误摘要 |
| error_category | TEXT | 错误分类 |
| error_severity | TEXT | 严重级别 |
| root_cause | TEXT | 根本原因分析 |
| fix_approach | TEXT | 修复方法 |
| fix_steps | TEXT | 修复步骤 |
| fix_code | TEXT | 修复代码 |
| verification_method | TEXT | 验证方法 |
| outcome | TEXT | 修复结果 |
| lessons_learned | TEXT | 经验教训 |
| prevention_measures | TEXT | 预防措施 |
| similar_errors | TEXT | 相似错误 |
| ai_knowledge_tags | TEXT | AI知识标签 |
| brain_knowledge_id | TEXT | 脑库知识ID |
| feeding_to_brain | INTEGER | 是否已投喂脑库 |

#### 8.26.4 错误扫描规则

| 扫描源 | 扫描规则 | 数据来源 | 时间范围 |
|--------|----------|----------|----------|
| error_logs表 | 扫描status为open/unresolved的错误 | error_logs | 全部未解决 |
| error_reports表 | 扫描前端上报错误 | error_reports | 最近24小时 |
| maintenance_logs表 | 扫描result为failure的维护操作 | system_maintenance_logs | 最近1小时 |
| 日志文件 | 扫描Traceback/Error/Exception/CRITICAL/FATAL | *.log文件 | 最新内容 |
| 源代码文件 | py_compile语法检查+静态分析(Tab混用等) | .py/.js/.html/.css/.vue | 全部文件 |
| 脚本文件 | Shell语法检查(if/fi匹配等) | .sh/.bat/.cmd/.ps1 | 全部文件 |
| 文本文件 | JSON格式校验+编码检测 | .txt/.md/.json/.yaml/.xml | 全部文件 |
| 404错误 | HTTP 404错误扫描 | error_logs表(error_type=http_404) | 全部未解决 |
| HTTP错误页面 | HTTP 400/401/403/500错误扫描 | error_logs表(error_type=http_400/http_401/http_403/http_500) | 全部未解决 |

每次扫描每个来源最多取20条，单次扫描最多200个文件，单次修复循环最多处理140条错误。

**源代码扫描规则：**
- 扫描扩展名：.py, .js, .jsx, .ts, .tsx, .html, .css, .vue
- 脚本扩展名：.sh, .bat, .cmd, .ps1
- 文本扩展名：.txt, .md, .json, .yaml, .yml, .xml, .ini, .conf, .cfg
- 排除目录：node_modules, .git, __pycache__, venv, env, .venv, backups
- 最大文件大小：512KB
- 单次最大扫描文件数：200
- Python检查：py_compile语法检查 + Tab/空格混用静态分析
- HTML检查：未闭合标签检测（排除br/hr/img/input/meta/link自闭合标签）
- JSON检查：json.loads格式校验 + 编码检测
- Shell检查：if/fi语法匹配检测
- 文本检查：UTF-8编码可读性检测

#### 8.26.5 修复策略

| 策略标识 | 适用错误 | 修复动作 |
|----------|----------|----------|
| db_wal_mode | 数据库锁定 | 设置数据库WAL模式 |
| create_table | 表不存在 | 检查并创建缺失的表 |
| insert_or_ignore | 唯一约束冲突 | 建议使用INSERT OR IGNORE |
| alter_table_add_column | 列不存在 | 检查并添加缺失的列 |
| check_create_file | 文件不存在 | 检查文件路径 |
| optional_import | 模块导入失败 | 建议try/except包裹import |
| dict_get_default | KeyError | 建议使用dict.get(key, default) |
| null_check | NoneType属性错误 | 建议添加None值检查 |
| retry_connection | 网络连接失败 | 建议添加重试机制 |
| increase_timeout | 超时错误 | 建议增加超时时间 |
| fix_permissions | 权限错误 | 检查并修复文件权限 |
| fix_syntax | 语法错误 | 检查代码语法 |
| integrity_check | 数据库完整性错误 | 执行PRAGMA integrity_check |
| memory_cleanup | 内存不足 | 建议清理大对象和垃圾回收 |
| check_template_path | 模板未找到 | 检查模板路径配置 |
| fix_python_syntax | Python语法错误 | 检查语法错误，备份文件后修复 |
| fix_indentation | Python缩进错误 | 备份文件，将Tab转换为4空格 |
| fix_missing_colon | Python缺失冒号 | 建议在语句末尾添加冒号 |
| fix_unclosed_bracket | Python括号未闭合 | 建议检查括号闭合 |
| fix_import_error | Python导入错误 | 建议try/except包裹import |
| fix_encoding | 文件编码错误 | 备份文件，尝试多编码读取并转为UTF-8 |
| fix_bom | BOM头问题 | 备份文件，移除UTF-8/UTF-16 BOM头 |
| fix_line_ending | 行尾符不一致 | 备份文件，统一CRLF/CR为LF |
| fix_tab_spaces | Tab空格混用 | 备份文件，将Tab转换为4空格 |
| fix_html_tag | HTML标签未闭合 | 建议检查HTML标签闭合 |
| fix_json_format | JSON格式错误 | 备份文件，移除尾部逗号并验证 |
| fix_undefined_var | 未定义变量 | 建议检查变量定义和拼写 |
| fix_type_error | 类型错误 | 建议检查变量类型并添加类型转换 |
| fix_attribute_error | 属性错误 | 建议检查对象属性是否存在 |
| fix_shell_syntax | Shell脚本语法错误 | 建议检查Shell脚本语法 |
| fix_404_route_missing | 404路由缺失 | 分析请求路径，检查路由定义，建议添加缺失路由 |
| fix_404_static_file | 404静态文件缺失 | 检查static目录，确认文件存在，建议修复引用路径 |
| fix_404_api_missing | 404API接口缺失 | 检查API蓝图注册，确认路由定义，建议添加API端点 |
| fix_404_template | 404模板缺失 | 检查templates目录，确认模板文件存在，建议修复render_template调用 |
| fix_404_redirect | 404重定向错误 | 检查重定向目标路径，确认目标路由存在，建议修复重定向URL |
| fix_400_bad_request | 400请求格式错误 | 检查请求参数格式，验证参数类型，建议添加参数校验 |
| fix_401_unauthorized | 401未授权错误 | 检查用户登录状态，验证token有效性，建议添加会话超时处理 |
| fix_403_forbidden | 403权限不足错误 | 检查用户角色配置，验证权限规则，建议优化权限提示 |
| fix_500_internal_error | 500服务器内部错误 | 分析错误堆栈，定位问题代码，建议修复代码bug |
| fix_500_db_error | 500数据库错误 | 检查数据库连接，验证SQL语句，建议修复数据问题 |
| fix_500_template_error | 500模板错误 | 检查模板路径，确认模板文件存在，建议修复render_template调用 |
| fix_500_import_error | 500导入错误 | 检查模块安装，验证导入路径，建议修复依赖问题 |
| fix_500_permission_error | 500权限错误 | 检查文件/目录权限，建议修复权限配置 |
| fix_error_template_missing | 错误页面模板缺失 | 检查templates目录，确认模板文件存在，建议创建缺失模板 |
| fix_error_static_missing | 错误页面静态资源缺失 | 检查static目录，确认资源文件存在，建议修复资源引用路径 |

**错误页面自动记录机制：**

Flask错误处理器已增强，所有HTTP错误页面访问自动记录到error_logs表：

| 错误类型 | 处理器 | error_type | error_message格式 |
|----------|--------|------------|-------------------|
| 400 | handle_400_error | 'http_400' | '400 Bad Request: {request.path}' |
| 401 | handle_401_error | 'http_401' | '401 Unauthorized: {request.path}' |
| 403 | handle_403_error | 'http_403' | '403 Forbidden: {request.path} (role:{role})' |
| 404 | handle_404_error | 'http_404' | '404 Not Found: {request.path}' |
| 500 | handle_500_error | 'http_500' | '500 Internal Server Error: {request.path}' |

**500错误特殊处理：**
- 自动捕获完整堆栈跟踪(traceback.format_exc())
- 记录到stack_trace字段，便于问题定位

**文件修复辅助方法：**

| 方法 | 功能 | 说明 |
|------|------|------|
| _backup_file | 文件备份 | 修复前创建.bak备份文件 |
| _fix_tab_to_spaces | Tab转空格 | 将Tab转换为4个空格 |
| _fix_file_encoding | 编码修复 | 尝试gbk/gb2312/latin-1/shift_jis解码后转为UTF-8 |
| _remove_bom | BOM移除 | 移除UTF-8/UTF-16 BOM头 |
| _fix_line_endings | 行尾统一 | CRLF/CR统一为LF |
| _fix_json_file | JSON修复 | 移除尾部逗号并验证JSON有效性 |

#### 8.26.6 方案匹配规则

```
1. 从repair_solutions表读取所有status='active'的方案
2. 对每个错误，用error_pattern正则匹配错误文本(类型+消息+堆栈)
3. 取置信度(confidence_score)最高的方案
4. 若最高置信度 >= AUTO_REPAIR_CONFIDENCE_THRESHOLD(0.7)则执行修复
5. 否则标记为unmatched，进入自学习队列
```text

匹配优先级：置信度高的方案优先，同置信度按success_rate排序。

#### 8.26.7 自学习机制

| 学习场景 | 处理方式 |
|----------|----------|
| 修复成功但无匹配方案 | 从修复记录提取新方案，置信度0.6，标记auto_learned |
| 未匹配的错误 | 记录到auto_repair_executions(result=unmatched) |
| 方案统计反馈 | 更新success_count/failure_count/success_rate/avg_fix_duration |

自学习流程：
1. 查询repair_result='success'且matched_solution_id为空的记录
2. 按error_type和repair_strategy分组
3. 为每组创建新方案（solution_id以SOL-AUTO-开头）
4. 新方案置信度0.6，状态active，创建者auto_repair_engine

#### 8.26.8 脑库投喂规则

修复成功后，将修复案例投喂到ai_brain_knowledge表：

| 投喂字段 | 内容 |
|----------|------|
| knowledge_id | RK-时间戳-PID |
| title | "修复案例: {方案标题}" |
| content | 错误+方案+策略+步骤 |
| knowledge_type | experience |
| source | auto_repair_engine |
| tags | repair,{error_type},{strategy} |
| priority | 8 |

投喂后更新repair_cases.feeding_to_brain=1并记录brain_knowledge_id。

#### 8.26.9 调度任务集成

自动修复已集成到自动化调度引擎(auto_scheduler.py)，新增定时任务：

| 任务名称 | 间隔规则 | 默认间隔 | 功能 |
|----------|----------|----------|------|
| auto_repair | AUTO_REPAIR_SCAN_INTERVAL | 60秒 | 扫描错误并自动修复 |

任务执行流程：
1. 检查AUTO_REPAIR_ENABLED是否启用
2. 检查AUTO_REPAIR_SCAN_INTERVAL间隔是否到达
3. 创建AutoRepairEngine实例
4. 调用run_repair_cycle()执行完整修复循环
5. 更新任务统计(成功/失败)

#### 8.26.10 黑匣子上报规则

| 上报场景 | 事件类型 | 说明 |
|----------|----------|------|
| 修复失败 | auto_repair_failure | 修复执行异常时上报 |
| 修复异常 | auto_repair_error | 引擎内部异常时上报 |

黑匣子上报内容包含：事件类型、标题、描述、来源模块(auto_repair_engine)、影响范围、堆栈跟踪。

#### 8.26.11 日志文件

| 日志文件 | 说明 |
|----------|------|
| auto_repair.log | 自动修复引擎运行日志 |
| system_maintenance_logs表 | 修复操作数据库日志 |
| auto_repair_executions表 | 修复执行记录 |
| repair_cases表 | 修复案例库 |

#### 8.26.12 自查清单

- [ ] AUTO_REPAIR_ENABLED已启用
- [ ] AUTO_REPAIR_SCAN_INTERVAL设置为60秒
- [ ] AUTO_REPAIR_CONFIDENCE_THRESHOLD设置为0.7
- [ ] repair_solutions表已预置45个常见修复方案(含15个源代码修复方案+5个404修复方案+10个错误页面修复方案)
- [ ] 9个错误扫描源均已启用(error_logs/error_reports/maintenance_logs/log_files/http_error/http_404/source_code/scripts/text_files)
- [ ] 45种修复策略均已实现(含15种源代码修复策略+5种404修复策略+10种错误页面修复策略)
- [ ] 源代码扫描已启用(.py/.js/.html/.css/.vue)
- [ ] 脚本扫描已启用(.sh/.bat/.cmd/.ps1)
- [ ] 文本文件扫描已启用(.txt/.md/.json/.yaml/.xml)
- [ ] Python语法检查(py_compile)已启用
- [ ] ERROR_PAGE规则已写入(10条)
- [ ] 所有错误页面模板已存在(400.html/401.html/403.html/404.html/500.html/error.html)
- [ ] 400/401/403/500错误处理器已增强(自动记录到数据库)
- [ ] 500错误堆栈自动捕获(traceback.format_exc())
- [ ] HTTP错误扫描(scan_http_errors)已启用
- [ ] 错误页面修复策略已实现(fix_400_bad_request/fix_401_unauthorized/fix_403_forbidden/fix_500_internal_error等)
- [ ] 静态分析(Tab混用检测)已启用
- [ ] 排除目录配置正确(node_modules/.git/__pycache__/venv等)
- [ ] 文件修复前自动备份(.bak文件)
- [ ] 文件修复辅助方法已实现(编码/BOM/行尾/Tab/JSON)
- [ ] 修复执行记录写入auto_repair_executions表
- [ ] 修复案例写入repair_cases表
- [ ] 修复案例投喂ai_brain_knowledge表
- [ ] 自学习机制可提取新方案
- [ ] 修复失败上报黑匣子
- [ ] 修复操作记录到system_maintenance_logs表
- [ ] auto_repair任务已集成到auto_scheduler.py
- [ ] 方案统计自动更新(success_count/success_rate/avg_fix_duration)
- [ ] 修复成功后error_logs状态更新为resolved

### 8.27 安全基线规则

**优先级**：本规则优先级高于其他开发规则，安全相关操作必须优先遵循本规范。

#### 8.27.1 安全规则配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| SECURITY_SQL_INJECTION_PROTECT | SQL注入防护 | 1 | 使用参数化查询，禁止SQL拼接 |
| SECURITY_XSS_PROTECT | XSS防护 | 1 | 对用户输入进行HTML转义 |
| SECURITY_CSRF_PROTECT | CSARF防护 | 1 | 启用CSRF令牌验证 |
| SECURITY_PASSWORD_MIN_LENGTH | 密码最小长度 | 8 | 密码最小字符数 |
| SECURITY_PASSWORD_COMPLEXITY | 密码复杂度 | 1 | 要求大小写+数字+特殊字符 |
| SECURITY_SESSION_TIMEOUT | 会话超时 | 1800 | 会话超时时间(秒) |
| SECURITY_MAX_LOGIN_ATTEMPTS | 最大登录尝试 | 5 | 失败锁定阈值 |
| SECURITY_ACCOUNT_LOCK_DURATION | 锁定时长 | 900 | 账户锁定时长(秒) |
| SECURITY_RATE_LIMIT_ENABLED | 速率限制 | 1 | API速率限制 |
| SECURITY_RATE_LIMIT_PER_MINUTE | 速率阈值 | 60 | 每分钟请求数 |
| SECURITY_SENSITIVE_DATA_ENCRYPT | 敏感数据加密 | 1 | 加密存储敏感信息 |
| SECURITY_FILE_UPLOAD_CHECK | 上传检查 | 1 | 检查文件类型和大小 |
| SECURITY_MAX_UPLOAD_SIZE | 最大上传大小 | 10 | MB |
| SECURITY_ALLOWED_FILE_TYPES | 允许文件类型 | .jpg,.png,.pdf,.doc | 逗号分隔 |

#### 8.27.2 安全检查清单

- [ ] 所有数据库查询使用参数化
- [ ] 所有用户输入已HTML转义
- [ ] CSRF令牌已添加到所有表单
- [ ] 密码长度≥8且包含复杂度
- [ ] 会话超时已配置(30分钟)
- [ ] 登录失败5次后锁定账户
- [ ] API速率限制已启用
- [ ] 敏感数据已加密存储
- [ ] 文件上传已做类型和大小检查
- [ ] 安全响应头已添加(X-XSS-Protection/X-Frame-Options)

---

### 8.28 数据备份规则

#### 8.28.1 备份规则配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| BACKUP_ENABLED | 备份启用 | 1 | 是否启用自动备份 |
| BACKUP_INTERVAL_HOURS | 备份间隔 | 24 | 自动备份间隔(小时) |
| BACKUP_RETENTION_DAYS | 保留天数 | 90 | 备份文件保留天数 |
| BACKUP_MAX_COUNT | 最大数量 | 100 | 最大保留备份数量 |
| BACKUP_COMPRESS | 压缩备份 | 1 | 是否压缩备份文件 |
| BACKUP_VERIFY_ENABLED | 备份验证 | 1 | 验证备份文件完整性 |
| BACKUP_INCREMENTAL_ENABLED | 增量备份 | 1 | 是否启用增量备份 |
| BACKUP_FULL_INTERVAL_DAYS | 全量备份间隔 | 7 | 全量备份间隔(天) |
| BACKUP_ON_UPGRADE | 升级前备份 | 1 | 系统升级前自动备份 |
| BACKUP_BEFORE_DDL | DDL前备份 | 1 | 数据库结构变更前备份 |
| BACKUP_ENCRYPTION_ENABLED | 备份加密 | 1 | 加密备份文件 |
| BACKUP_ALERT_ON_FAIL | 失败告警 | 1 | 备份失败发送告警 |

#### 8.28.2 备份策略

**全量备份**：每周日03:00执行
**增量备份**：每日03:00执行
**DDL前备份**：数据库结构变更前自动执行
**升级前备份**：系统版本升级前自动执行

#### 8.28.3 备份检查清单

- [ ] 自动备份已启用
- [ ] 备份间隔已配置(24小时)
- [ ] 备份保留期已设置(90天)
- [ ] 备份压缩已启用
- [ ] 备份验证已启用
- [ ] 增量备份已启用
- [ ] 升级前自动备份已启用
- [ ] 备份加密已启用
- [ ] 备份失败告警已启用

---

### 8.29 性能监控规则

#### 8.29.1 性能监控配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| PERF_MONITOR_ENABLED | 性能监控启用 | 1 | 是否启用性能监控 |
| PERF_CHECK_INTERVAL | 检查间隔 | 60 | 性能检查间隔(秒) |
| PERF_CPU_THRESHOLD | CPU阈值 | 80 | CPU使用率告警阈值(%) |
| PERF_MEMORY_THRESHOLD | 内存阈值 | 80 | 内存使用率告警阈值(%) |
| PERF_DISK_THRESHOLD | 磁盘阈值 | 90 | 磁盘使用率告警阈值(%) |
| PERF_RESPONSE_TIME_THRESHOLD | 响应时间阈值 | 2000 | 接口响应时间告警 |
| PERF_SLOW_QUERY_THRESHOLD | 慢查询阈值 | 1000 | 慢查询告警阈值 |
| PERF_ERROR_RATE_THRESHOLD | 错误率阈值 | 5 | 错误率告警阈值(%) |
| PERF_ALERT_ENABLED | 性能告警 | 1 | 是否启用性能告警 |
| PERF_LOG_SLOW_REQUEST | 记录慢请求 | 1 | 记录慢请求日志 |

#### 8.29.2 性能监控检查清单

- [ ] 性能监控已启用
- [ ] CPU阈值已配置(80%)
- [ ] 内存阈值已配置(80%)
- [ ] 磁盘阈值已配置(90%)
- [ ] 响应时间阈值已配置(2000ms)
- [ ] 慢查询阈值已配置(1000ms)
- [ ] 性能告警已启用
- [ ] 慢请求日志已启用

---

### 8.30 API接口规范

#### 8.30.1 API规范配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| API_VERSION | API版本 | v1 | 当前API版本 |
| API_PREFIX | API前缀 | /api | API路由前缀 |
| API_RATE_LIMIT_DEFAULT | 默认速率限制 | 60 | 每分钟请求数 |
| API_TIMEOUT_DEFAULT | 默认超时 | 30 | 接口超时时间(秒) |
| API_MAX_PAGE_SIZE | 最大分页 | 100 | 最大分页大小 |
| API_DEFAULT_PAGE_SIZE | 默认分页 | 20 | 默认分页大小 |
| API_RESPONSE_FORMAT | 响应格式 | json | API响应格式 |
| API_ERROR_CODE_ENABLED | 错误码启用 | 1 | 使用统一错误码 |
| API_DOCS_ENABLED | API文档启用 | 1 | 启用API文档 |
| API_AUTH_REQUIRED | API认证 | 1 | 要求API认证 |

#### 8.30.2 API响应格式

```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {},
  "timestamp": "2026-07-16T12:00:00Z"
}
```text

#### 8.30.3 API检查清单

- [ ] API前缀统一(/api)
- [ ] 速率限制已启用
- [ ] 超时时间已配置(30秒)
- [ ] 分页大小已限制(最大100)
- [ ] 统一响应格式已使用
- [ ] 统一错误码已启用
- [ ] API文档已启用
- [ ] API认证已要求

---

### 8.31 日志管理规则

#### 8.31.1 日志配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| LOG_LEVEL_DEFAULT | 默认日志级别 | INFO | DEBUG/INFO/WARNING/ERROR |
| LOG_FILE_ENABLED | 文件日志 | 1 | 启用文件日志 |
| LOG_FILE_PATH | 日志路径 | logs/ | 日志文件存储路径 |
| LOG_FILE_MAX_SIZE | 文件最大大小 | 10 | 单个日志文件最大大小(MB) |
| LOG_FILE_BACKUP_COUNT | 备份数量 | 10 | 日志文件备份数量 |
| LOG_ROTATION_ENABLED | 日志轮转 | 1 | 启用日志轮转 |
| LOG_RETENTION_DAYS | 保留天数 | 90 | 日志保留天数 |
| LOG_SENSITIVE_FILTER | 敏感信息过滤 | 1 | 过滤敏感信息 |
| LOG_ERROR_STACKTRACE | 错误堆栈 | 1 | 记录错误堆栈 |

#### 8.31.2 日志级别定义

| 级别 | 用途 |
|------|------|
| DEBUG | 调试信息 |
| INFO | 常规信息 |
| WARNING | 警告信息 |
| ERROR | 错误信息 |
| CRITICAL | 严重错误 |

#### 8.31.3 日志检查清单

- [ ] 默认日志级别已配置(INFO)
- [ ] 文件日志已启用
- [ ] 日志轮转已启用
- [ ] 日志保留期已设置(90天)
- [ ] 敏感信息过滤已启用
- [ ] 错误堆栈记录已启用

---

### 8.32 数据库管理规则

#### 8.32.1 数据库配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| DB_POOL_SIZE | 连接池大小 | 10 | 数据库连接池大小 |
| DB_POOL_TIMEOUT | 连接池超时 | 30 | 连接池超时(秒) |
| DB_WAL_MODE | WAL模式 | 1 | 启用WAL模式 |
| DB_FOREIGN_KEYS | 外键约束 | 1 | 启用外键约束 |
| DB_AUTO_VACUUM | 自动VACUUM | 1 | 启用自动VACUUM |
| DB_VACUUM_INTERVAL | VACUUM间隔 | 168 | VACUUM间隔(小时) |
| DB_BACKUP_BEFORE_DDL | DDL前备份 | 1 | DDL前自动备份 |
| DB_SLOW_QUERY_LOG | 慢查询日志 | 1 | 记录慢查询 |
| DB_SLOW_QUERY_THRESHOLD | 慢查询阈值 | 1000 | 慢查询阈值 |
| DB_INDEX_AUTO_CREATE | 自动索引 | 1 | 自动创建索引 |

#### 8.32.2 数据库检查清单

- [ ] 连接池大小已配置(10)
- [ ] WAL模式已启用
- [ ] 外键约束已启用
- [ ] 自动VACUUM已启用
- [ ] DDL前备份已启用
- [ ] 慢查询日志已启用
- [ ] 表命名规范已统一(snake_case)
- [ ] 列命名规范已统一(snake_case)

---

### 8.33 任务调度规范

#### 8.33.1 任务调度配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| SCHED_ENABLED | 任务调度启用 | 1 | 是否启用任务调度 |
| SCHED_HEARTBEAT_INTERVAL | 心跳间隔 | 60 | 调度器心跳间隔(秒) |
| SCHED_MAX_CONCURRENT | 最大并发数 | 5 | 最大并发执行任务数 |
| SCHED_RETRY_COUNT | 重试次数 | 3 | 任务失败重试次数 |
| SCHED_RETRY_DELAY | 重试延迟 | 60 | 重试间隔(秒) |
| SCHED_TIMEOUT | 任务超时 | 300 | 任务超时时间(秒) |
| SCHED_LOG_ENABLED | 调度日志 | 1 | 是否记录调度日志 |
| SCHED_ALERT_ENABLED | 调度告警 | 1 | 是否发送调度告警 |
| SCHED_METRICS_ENABLED | 调度指标 | 1 | 是否收集调度指标 |
| SCHED_STORAGE_TYPE | 存储类型 | database | 任务存储类型 |

#### 8.33.2 调度策略

**调度间隔**：每60秒检查一次任务队列
**并发控制**：最大5个任务同时执行
**重试策略**：失败重试3次，间隔60秒
**超时处理**：任务执行超过300秒强制终止

#### 8.33.3 任务调度检查清单

- [ ] 任务调度已启用
- [ ] 心跳间隔已配置(60秒)
- [ ] 最大并发数已配置(5)
- [ ] 重试次数已配置(3)
- [ ] 任务超时已配置(300秒)
- [ ] 调度日志已启用
- [ ] 调度告警已启用
- [ ] 调度指标已收集

---

### 8.34 用户管理规范

#### 8.34.1 用户管理配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| USER_REGISTRATION_ENABLED | 注册启用 | 1 | 是否允许用户注册 |
| USER_ACTIVATION_REQUIRED | 激活要求 | 1 | 是否需要邮箱激活 |
| USER_PROFILE_COMPLETE | 资料完整 | 1 | 是否要求完善资料 |
| USER_AVATAR_SIZE | 头像大小 | 2 | 头像最大大小(MB) |
| USER_NICKNAME_MAX_LENGTH | 昵称最大长度 | 20 | 昵称最大长度 |
| USER_BIO_MAX_LENGTH | 简介最大长度 | 200 | 个人简介最大长度 |
| USER_EMAIL_UNIQUE | 邮箱唯一 | 1 | 邮箱是否唯一 |
| USER_PHONE_UNIQUE | 手机号唯一 | 1 | 手机号是否唯一 |
| USER_DELETE_ENABLED | 删除启用 | 1 | 是否允许用户删除 |
| USER_SOFT_DELETE | 软删除 | 1 | 是否使用软删除 |
| USER_DATA_EXPORT_ENABLED | 数据导出 | 1 | 是否允许数据导出 |
| USER_DATA_RETENTION | 数据保留 | 365 | 用户数据保留天数 |

#### 8.34.2 用户管理检查清单

- [ ] 用户注册已启用
- [ ] 邮箱激活已启用
- [ ] 资料完善已要求
- [ ] 头像大小已限制(2MB)
- [ ] 昵称长度已限制(20字符)
- [ ] 邮箱唯一性已验证
- [ ] 手机号唯一性已验证
- [ ] 软删除已启用
- [ ] 数据导出已启用
- [ ] 数据保留期已设置(365天)

---

### 8.35 通知系统规范

#### 8.35.1 通知配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| NOTIFY_ENABLED | 通知启用 | 1 | 是否启用通知系统 |
| NOTIFY_EMAIL_ENABLED | 邮件通知 | 1 | 是否启用邮件通知 |
| NOTIFY_SMS_ENABLED | 短信通知 | 0 | 是否启用短信通知 |
| NOTIFY_PUSH_ENABLED | 推送通知 | 1 | 是否启用推送通知 |
| NOTIFY_IN_APP_ENABLED | 站内通知 | 1 | 是否启用站内通知 |
| NOTIFY_MAX_PER_USER | 用户最大通知 | 1000 | 用户最大通知数 |
| NOTIFY_RETENTION_DAYS | 通知保留 | 30 | 通知保留天数 |
| NOTIFY_UNREAD_LIMIT | 未读限制 | 100 | 未读通知上限 |
| NOTIFY_ALERT_LEVEL | 告警级别 | warning | 告警级别 |
| NOTIFY_BATCH_SIZE | 批量大小 | 100 | 批量发送大小 |

#### 8.35.2 通知类型

| 类型 | 说明 | 启用状态 |
|------|------|----------|
| 邮件通知 | 通过邮件发送通知 | 启用 |
| 短信通知 | 通过短信发送通知 | 禁用 |
| 推送通知 | 浏览器推送通知 | 启用 |
| 站内通知 | 系统内通知 | 启用 |

#### 8.35.3 通知检查清单

- [ ] 通知系统已启用
- [ ] 邮件通知已启用
- [ ] 推送通知已启用
- [ ] 站内通知已启用
- [ ] 用户通知上限已设置(1000)
- [ ] 通知保留期已设置(30天)
- [ ] 未读通知上限已设置(100)

---

### 8.36 缓存管理规范

#### 8.36.1 缓存配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| CACHE_ENABLED | 缓存启用 | 1 | 是否启用缓存 |
| CACHE_TYPE | 缓存类型 | redis | 缓存类型(redis/memory) |
| CACHE_TTL_DEFAULT | 默认TTL | 3600 | 默认缓存过期时间(秒) |
| CACHE_MAX_SIZE | 最大大小 | 1024 | 最大缓存大小(MB) |
| CACHE_COMPRESSION | 压缩启用 | 1 | 是否压缩缓存数据 |
| CACHE_FLUSH_ON_UPGRADE | 升级刷新 | 1 | 升级时是否刷新缓存 |
| CACHE_STATS_ENABLED | 统计启用 | 1 | 是否收集缓存统计 |
| CACHE_WARMUP_ENABLED | 预热启用 | 1 | 是否启用缓存预热 |
| CACHE_INVALIDATION_ENABLED | 失效启用 | 1 | 是否启用缓存失效 |
| CACHE_KEY_PREFIX | 键前缀 | mtscos: | 缓存键前缀 |

#### 8.36.2 缓存策略

**缓存类型**：Redis（优先）/ 内存（备用）
**过期策略**：默认3600秒(1小时)，可按业务调整
**压缩策略**：启用数据压缩，减少内存占用
**预热策略**：系统启动时预加载热点数据

#### 8.36.3 缓存检查清单

- [ ] 缓存已启用
- [ ] 默认TTL已配置(3600秒)
- [ ] 最大缓存大小已配置(1024MB)
- [ ] 缓存压缩已启用
- [ ] 升级刷新已启用
- [ ] 缓存统计已收集
- [ ] 缓存预热已启用
- [ ] 缓存失效已启用

---

### 8.37 文件管理规范

#### 8.37.1 文件管理配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| FILE_UPLOAD_ENABLED | 上传启用 | 1 | 是否启用文件上传 |
| FILE_STORAGE_TYPE | 存储类型 | local | 存储类型(local/cloud) |
| FILE_MAX_SIZE | 最大大小 | 50 | 单文件最大大小(MB) |
| FILE_ALLOWED_EXTENSIONS | 允许扩展名 | .jpg,.png,.pdf,.doc等 | 允许的文件扩展名 |
| FILE_ALLOWED_MIME_TYPES | 允许MIME类型 | image/jpeg,image/png等 | 允许的MIME类型 |
| FILE_STORAGE_PATH | 存储路径 | uploads/ | 本地存储路径 |
| FILE_URL_PREFIX | URL前缀 | /uploads/ | 文件访问URL前缀 |
| FILE_VERSIONING | 版本管理 | 0 | 是否启用文件版本管理 |
| FILE_AUTO_DELETE | 自动删除 | 0 | 是否自动删除过期文件 |
| FILE_RETENTION_DAYS | 保留天数 | 365 | 文件保留天数 |
| FILE_THUMBNAIL_ENABLED | 缩略图 | 1 | 是否生成缩略图 |
| FILE_ENCRYPTION_ENABLED | 文件加密 | 0 | 是否加密文件 |

#### 8.37.2 文件检查清单

- [ ] 文件上传已启用
- [ ] 单文件大小已限制(50MB)
- [ ] 允许扩展名已配置
- [ ] 存储路径已配置(uploads/)
- [ ] URL前缀已配置(/uploads/)
- [ ] 缩略图已启用
- [ ] 文件保留期已设置(365天)

---

### 8.38 消息队列规范

#### 8.38.1 消息队列配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| MQ_ENABLED | 消息队列启用 | 0 | 是否启用消息队列 |
| MQ_TYPE | 队列类型 | redis | 队列类型(redis/rabbitmq/kafka) |
| MQ_MAX_RETRY | 最大重试 | 3 | 消息最大重试次数 |
| MQ_DEAD_LETTER_ENABLED | 死信队列 | 1 | 是否启用死信队列 |
| MQ_BATCH_SIZE | 批量大小 | 10 | 批量处理大小 |
| MQ_CONCURRENT_WORKERS | 并发工作数 | 4 | 并发消费者数量 |
| MQ_HEARTBEAT_INTERVAL | 心跳间隔 | 30 | 消费者心跳间隔(秒) |
| MQ_MESSAGE_TTL | 消息TTL | 86400 | 消息过期时间(秒) |
| MQ_PERSISTENCE | 持久化 | 1 | 是否持久化消息 |
| MQ_LOG_ENABLED | 日志启用 | 1 | 是否记录队列日志 |

#### 8.38.2 消息队列检查清单

- [ ] 消息队列状态已确认
- [ ] 最大重试已配置(3)
- [ ] 死信队列已启用
- [ ] 并发工作数已配置(4)
- [ ] 消息TTL已配置(86400秒)
- [ ] 消息持久化已启用
- [ ] 队列日志已启用

---

### 8.39 例行维护规则

**优先级**：本规则优先级高于其他开发规则，例行维护操作必须优先遵循本规范。

#### 8.39.1 系统级维护配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| MAINT_SYSTEM_HEALTH_CHECK | 系统健康检查 | 60 | 系统健康检查间隔(秒) |
| MAINT_SYSTEM_RESOURCE_ALERT | 资源告警启用 | 1 | 是否启用系统资源告警 |
| MAINT_SYSTEM_PERFORMANCE_LOG | 性能日志记录 | 1 | 是否记录系统性能日志 |
| MAINT_SYSTEM_UPDATE_CHECK | 系统更新检查 | 3600 | 系统更新检查间隔(秒) |

#### 8.39.2 硬件资源维护配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| MAINT_CPU_CHECK_INTERVAL | CPU检查间隔 | 60 | CPU使用检查间隔(秒) |
| MAINT_CPU_WARNING_THRESHOLD | CPU警告阈值 | 80 | CPU使用率警告阈值(%) |
| MAINT_CPU_CRITICAL_THRESHOLD | CPU危险阈值 | 95 | CPU使用率危险阈值(%) |
| MAINT_MEMORY_CHECK_INTERVAL | 内存检查间隔 | 60 | 内存使用检查间隔(秒) |
| MAINT_MEMORY_WARNING_THRESHOLD | 内存警告阈值 | 80 | 内存使用率警告阈值(%) |
| MAINT_DISK_CHECK_INTERVAL | 磁盘检查间隔 | 3600 | 磁盘空间检查间隔(秒) |
| MAINT_DISK_WARNING_THRESHOLD | 磁盘警告阈值 | 80 | 磁盘使用率警告阈值(%) |
| MAINT_DISK_CRITICAL_THRESHOLD | 磁盘危险阈值 | 95 | 磁盘使用率危险阈值(%) |

#### 8.39.3 数据库维护配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| MAINT_DB_OPTIMIZE_INTERVAL | 数据库优化间隔 | 86400 | 数据库优化间隔(秒) |
| MAINT_DB_VACUUM_ENABLED | 数据库VACUUM启用 | 1 | 是否启用数据库VACUUM |
| MAINT_DB_INDEX_REBUILD | 索引重建间隔 | 604800 | 数据库索引重建间隔(秒) |
| MAINT_DB_STATS_UPDATE | 统计信息更新 | 86400 | 数据库统计信息更新间隔(秒) |

#### 8.39.4 日志维护配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| MAINT_LOG_ROTATE_ENABLED | 日志轮转启用 | 1 | 是否启用日志轮转 |
| MAINT_LOG_CLEANUP_INTERVAL | 日志清理间隔 | 604800 | 日志清理间隔(秒) |
| MAINT_LOG_RETENTION_DAYS | 日志保留天数 | 90 | 日志保留天数 |

#### 8.39.5 安全维护配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| MAINT_SECURITY_SCAN_ENABLED | 安全扫描启用 | 1 | 是否启用安全扫描 |
| MAINT_SECURITY_SCAN_INTERVAL | 安全扫描间隔 | 86400 | 安全扫描间隔(秒) |
| MAINT_SECURITY_VULNERABILITY_CHECK | 漏洞检测 | 604800 | 漏洞检测间隔(秒) |
| MAINT_SECURITY_LOG_REVIEW | 安全日志审查 | 86400 | 安全日志审查间隔(秒) |

#### 8.39.6 备份维护配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| MAINT_BACKUP_VERIFY_INTERVAL | 备份验证间隔 | 86400 | 备份验证间隔(秒) |
| MAINT_BACKUP_CLEANUP_ENABLED | 备份清理启用 | 1 | 是否启用备份清理 |
| MAINT_BACKUP_CLEANUP_INTERVAL | 备份清理间隔 | 604800 | 备份清理间隔(秒) |
| MAINT_BACKUP_RETENTION_DAYS | 备份保留天数 | 90 | 备份保留天数 |

#### 8.39.7 网络维护配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| MAINT_NETWORK_CHECK_INTERVAL | 网络检查间隔 | 60 | 网络连通性检查间隔(秒) |
| MAINT_NETWORK_FIREWALL_CHECK | 防火墙检查 | 3600 | 防火墙规则检查间隔(秒) |
| MAINT_NETWORK_PORT_SCAN | 端口扫描 | 86400 | 端口扫描间隔(秒) |

#### 8.39.8 服务维护配置表

| 规则代码 | 规则名称 | 默认值 | 说明 |
|----------|----------|--------|------|
| MAINT_SERVICE_HEALTH_CHECK | 服务健康检查 | 30 | 服务健康检查间隔(秒) |
| MAINT_SERVICE_AUTO_RESTART | 服务自动重启 | 1 | 服务异常时是否自动重启 |
| MAINT_SERVICE_STATUS_LOG | 服务状态日志 | 1 | 是否记录服务状态日志 |

#### 8.39.9 例行维护执行策略

**每日维护**：03:00执行
- 数据库VACUUM
- 日志清理
- 缓存清理
- 备份验证
- 安全扫描

**每周维护**：周日02:00执行
- 数据库索引重建
- 文件完整性检查
- 漏洞检测
- 安全日志审查

**每月维护**：每月1日01:00执行
- 性能报告生成
- 系统更新检查
- 用户活动审查

#### 8.39.10 例行维护检查清单

- [ ] 系统健康检查已配置(60秒)
- [ ] CPU阈值已配置(80%警告/95%危险)
- [ ] 内存阈值已配置(80%警告)
- [ ] 磁盘阈值已配置(80%警告/95%危险)
- [ ] 数据库VACUUM已启用
- [ ] 日志轮转已启用
- [ ] 安全扫描已启用(每日)
- [ ] 备份验证已启用(每日)
- [ ] 服务自动重启已启用
- [ ] 每日维护任务已配置
- [ ] 每周维护任务已配置
- [ ] 每月维护任务已配置

---

## 9. AI管家操作规范

### 9.1 AI管家职责

| 职责 | 说明 | 执行频率 |
|------|------|---------|
| 系统监控 | 监控所有AI组件状态 | 实时 |
| 自动维护 | 执行定期维护任务 | 每日 |
| 异常处理 | 处理AI组件异常 | 实时 |
| 性能优化 | 优化AI组件性能 | 每周 |
| 报告生成 | 生成AI系统报告 | 每月 |

### 9.2 管家配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| monitoring_enabled | 监控启用 | True |
| auto_repair_enabled | 自动修复启用 | True |
| performance_tuning_enabled | 性能调优启用 | True |
| report_enabled | 报告生成启用 | True |
| alert_threshold | 告警阈值 | 0.9 |

### 9.3 管家操作流程

```
1. 定期检查所有AI组件状态
2. 发现异常触发自动修复
3. 评估组件性能并优化
4. 生成定期报告
5. 通知管理员异常情况
```text

---

## 10. 考试系统操作规范

### 10.1 AI自动组卷参数规范

#### 10.1.1 题型比例配置

| 题型 | 比例 | 说明 |
|------|------|------|
| 词汇题 | 25% | 词汇理解与应用 |
| 语法题 | 25% | 语法知识与运用 |
| 阅读题 | 30% | 阅读理解与分析 |
| 听力题 | 20% | 听力理解（默认启用） |

#### 10.1.2 听力题配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| listening_enabled | 是否启用听力题 | True |
| listening_ratio | 听力题占比 | 20% |
| listening_languages | 支持的语言 | ['japanese', 'english', 'chinese'] |

#### 10.1.3 组卷规则

| 规则 | 说明 |
|------|------|
| 难度分布 | 简单:中等:困难 = 3:5:2 |
| 最大重复题数 | 10题 |
| 默认题目数 | 20题 |
| 默认考试时长 | 60分钟 |

### 10.2 考试准入条件规范

#### 10.2.1 角色权限

| 角色 | 权限 |
|------|------|
| student | 可参加考试和测试 |
| student_vip | 可参加考试和测试 |
| teacher | 可进入考试系统 |
| admin | 可进入考试系统 |
| super_admin | 可进入考试系统 |
| system_admin | 可进入考试系统 |
| hardware_admin | 可进入考试系统（调试权限） |
| hardware_vikey_admin | 可进入考试系统（调试权限） |

#### 10.2.2 教育类型限制

| 教育类型 | 可参加的考试科目 |
|----------|-----------------|
| nine_year (K12) | 数学、语文、英语、物理、化学、政治 |
| adult | 所有科目（含日语、职业资格等） |
| general | 所有科目 |

#### 10.2.3 科目分类归属

| 科目 | 归属教育类型 |
|------|-------------|
| 数学、语文、英语、物理、化学、政治 | nine_year + adult + general |
| 日语、日语听力 | adult + general |
| 英语听力、语文听力 | nine_year + adult + general |
| 职业资格（交通法规、电工等） | adult |
| 高等教育（高等数学等） | adult |

### 10.3 自动阅卷规则规范

#### 10.3.1 题型批改类型

| 题型 | 批改类型 | 说明 |
|------|---------|------|
| single_choice | 自动批改 | 精确匹配 |
| multiple_choice | 自动批改 | 精确匹配 |
| true_false | 自动批改 | 精确匹配 |
| fill_blank | 自动批改 | 精确匹配 |
| listening | 听力自动批改 | 语义相似度+关键词匹配 |
| short_answer | AI辅助批改 | 关键词+篇幅+结构评分 |
| essay | AI辅助批改 | AI评分+人工复核 |
| composition | AI辅助批改 | AI评分+人工复核 |

#### 10.3.2 听力题判错规则

| 匹配模式 | 规则 | 适用场景 |
|----------|------|---------|
| exact | 完全匹配正确答案 | 听力单选题 |
| keyword | 按关键词匹配计分 | 听力填空题 |
| semantic | 语义相似度评分 | 听力简答题 |

#### 10.3.3 语义相似度评分标准

| 相似度 | 评分比例 | 结果判定 |
|--------|---------|---------|
| ≥85% | 100% | 答案正确 |
| 60%-84% | 按相似度 | 答案基本正确 |
| 30%-59% | 相似度×50% | 答案部分正确 |
| <30% | 0% | 答案错误 |

---

## 11. AI操作安全规范

### 11.1 权限控制

| 操作 | 最低权限 |
|------|---------|
| 查看AI员工列表 | student |
| 创建AI员工 | admin |
| 修改AI员工 | admin |
| 删除AI员工 | super_admin |
| 修改AI引擎配置 | super_admin |
| 升级AI集群 | super_admin |
| 访问AI脑库 | student |
| 修改AI脑库知识 | admin |

### 11.2 数据加密

| 数据类型 | 加密方式 |
|----------|---------|
| 知识内容 | AES-256 |
| 员工配置 | AES-256 |
| 引擎密钥 | 环境变量 |
| 日志数据 | 脱敏处理 |

### 11.3 操作审计

所有AI操作必须记录审计日志：

```python
def audit_ai_operation(operation_type, target, operator, details):
    """记录AI操作审计日志"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ai_operation_logs 
            (operation_type, target, operator, details, timestamp)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (operation_type, target, operator, json.dumps(details)))
        conn.commit()
```text

---

## 🔍 AI操作自查清单

### AI员工操作
- [ ] AI员工已启用智能赋能
- [ ] 员工配置已持久化到数据库
- [ ] 员工创建/修改/删除已记录日志
- [ ] 员工升级符合升级规则
- [ ] 员工异常已正确处理

### AI引擎操作
- [ ] 引擎配置已持久化到数据库
- [ ] 引擎调用已记录日志
- [ ] 引擎升级已备份配置
- [ ] 引擎健康检查已配置
- [ ] 回滚机制已验证

### AI集群操作
- [ ] 集群配置已持久化到数据库
- [ ] 集群状态监控已配置
- [ ] 故障转移机制已验证
- [ ] 员工分配符合规则
- [ ] 集群升级已记录日志

### AI阵列操作
- [ ] 阵列节点健康检查已配置
- [ ] 故障转移机制已验证
- [ ] 负载均衡已配置
- [ ] 滚动升级已测试
- [ ] 节点通信已验证

### AI神经元网络操作
- [ ] 模型版本已管理
- [ ] 训练过程已监控
- [ ] 推理接口已验证
- [ ] 推理缓存已配置
- [ ] 模型部署已测试

### AI脑库操作
- [ ] 知识格式已验证
- [ ] 知识已加密存储
- [ ] 知识验证已执行
- [ ] 知识检索已测试
- [ ] 知识增强已配置

### AI管家操作
- [ ] 监控已启用
- [ ] 自动修复已启用
- [ ] 性能调优已配置
- [ ] 报告生成已启用
- [ ] 告警机制已配置

### 例行维护操作
- [ ] AI员工状态检查频率已配置
- [ ] AI引擎健康检查频率已配置
- [ ] AI集群监控频率已配置
- [ ] AI阵列节点存活检测已配置
- [ ] Git自动同步频率已配置
- [ ] 数据库备份频率已配置
- [ ] 系统日志清理频率已配置
- [ ] 自动恢复功能已启用
- [ ] 自动修复功能已启用
- [ ] 性能调优功能已启用

### 版本号更新操作
- [ ] 版本号检查频率已配置
- [ ] 版本号自动递增已启用
- [ ] 版本号格式规范已配置
- [ ] 升级时版本递增已启用
- [ ] 版本递增类型已配置
- [ ] 版本历史记录已启用
- [ ] 版本号获取优先级已正确配置
- [ ] 版本号更新流程已验证

### 灰度发布操作
- [ ] 灰度发布功能已启用
- [ ] 初始灰度比例已配置
- [ ] 灰度健康检查间隔已配置
- [ ] 自动回滚阈值已配置
- [ ] 灰度放量步骤已配置
- [ ] 灰度环境URL已配置
- [ ] 失败时自动回滚已启用
- [ ] 灰度发布与版本号联动已验证
- [ ] 灰度健康检查标准已配置
- [ ] 灰度发布流程已测试

### 用户权限操作
- [ ] 角色等级已配置
- [ ] 权限矩阵已统一
- [ ] 权限缓存已启用
- [ ] 权限审计已启用
- [ ] 权限自动同步已启用
- [ ] K12权限限制已启用
- [ ] 硬件管理员调试权限已启用
- [ ] 密码复杂度要求已配置
- [ ] 账户锁定策略已配置
- [ ] 权限检查流程已验证

### 自动修复操作
- [ ] 自动修复功能已启用
- [ ] 修复代码备份已启用
- [ ] 修复数据库留底已启用
- [ ] 修复验证已启用
- [ ] 修复失败回滚已启用
- [ ] 修复置信度阈值已配置
- [ ] 修复重试次数已配置
- [ ] 修复记录保留天数已配置
- [ ] 修复自学习已启用
- [ ] 修复安全规则已配置

### 常驻服务操作
- [ ] 常驻服务启用已配置
- [ ] 常驻服务心跳间隔已配置
- [ ] 常驻服务健康检查已配置
- [ ] 常驻服务自动重启已启用
- [ ] 常驻服务最大重启次数已配置
- [ ] 常驻服务看门狗已启用
- [ ] 常驻服务通知已启用
- [ ] 常驻服务启动优先级已配置
- [ ] 常驻服务自动启动已启用
- [ ] 常驻服务状态监控已配置

### 沙盒规则操作
- [ ] 沙盒启用已配置
- [ ] 沙盒隔离级别已配置
- [ ] 沙盒最大/最小实例数已配置
- [ ] 沙盒资源限制已配置(CPU/内存/磁盘/进程数)
- [ ] 沙盒动态扩缩容已启用
- [ ] 沙盒预温机制已启用
- [ ] 沙盒健康检查间隔已配置
- [ ] 沙盒自动清理已启用
- [ ] 沙盒超时时间已配置
- [ ] 沙盒网络隔离已配置
- [ ] 沙盒实例数据库持久化已配置
- [ ] 沙盒配置从system_rules读取已实现

### 网络规则操作
- [ ] 网络规则启用已配置
- [ ] 端口映射功能已启用
- [ ] 防火墙规则启用已配置
- [ ] 幂等同步机制已启用
- [ ] 网络规则同步间隔已配置
- [ ] 端口映射规则表已创建(network_port_rules)
- [ ] 防火墙规则表已创建(network_firewall_rules)
- [ ] NAT规则类型已配置(DNAT/SNAT/MASQUERADE)
- [ ] 网络规则持久化已启用
- [ ] 网络规则自动清理已启用
- [ ] 网络健康检查间隔已配置
- [ ] 网络故障告警已启用

### 协议规则操作
- [ ] 协议管理启用已配置
- [ ] 默认编码已配置(utf-8)
- [ ] 默认超时时间已配置(300秒)
- [ ] 默认重试次数已配置(3次)
- [ ] 最大连接数已配置(1000)
- [ ] 协议配置表已创建(protocol_rules)
- [ ] 协议端点表已创建(protocol_endpoints)
- [ ] 支持的协议类型已配置(http,https,grpc,websocket,mqtt,amqp)
- [ ] 协议加密已启用
- [ ] WebSocket协议支持已启用
- [ ] gRPC协议支持已启用
- [ ] MQTT协议支持已启用
- [ ] API限流已配置
- [ ] 协议认证要求已配置

### 端口规则操作
- [ ] 端口管理启用已配置
- [ ] 默认协议已配置(tcp)
- [ ] 默认绑定IP已配置(0.0.0.0)
- [ ] 端口号范围已配置(1024-65535)
- [ ] 幂等同步机制已启用
- [ ] 端口配置表已创建(port_rules)
- [ ] 端口映射表已创建(port_mapping_rules)
- [ ] TLS加密已配置
- [ ] 端口限流已配置
- [ ] 端口连接数限制已配置
- [ ] 端口健康检查间隔已配置
- [ ] 端口故障告警已启用
- [ ] 端口分类规则已配置(保留/系统/用户端口)
- [ ] 端口安全规则已配置(IP白名单/黑名单)

### 文档规则操作
- [ ] 文档管理启用已配置
- [ ] 默认文档类型已配置(markdown)
- [ ] 默认文档分类已配置(system)
- [ ] 默认访问级别已配置(public)
- [ ] 文档配置表已创建(document_rules)
- [ ] 文档版本表已创建(document_versions)
- [ ] 版本历史功能已启用
- [ ] 自动保存功能已启用
- [ ] 文档搜索功能已启用
- [ ] 文档导出功能已启用
- [ ] 文档导入功能已启用
- [ ] 文档加密已启用
- [ ] 文档缓存已配置
- [ ] 文档自动清理已启用

### 前端规则操作
- [ ] 前端样式规范启用已配置
- [ ] 倒角规范已配置(4px/8px/12px/16px/9999px)
- [ ] 间距规范已配置(内边距/外边距/元素间距/区块间距)
- [ ] 透明度规范已配置(禁用/悬停/聚焦/激活)
- [ ] 字体大小规范已配置(12px-32px)
- [ ] 对齐方式规范已配置(left/center/right/justify)
- [ ] 行高规范已配置(1.25/1.5/1.75)
- [ ] 阴影规范已配置(小/中/大)
- [ ] 边框规范已配置(宽度/样式/颜色)
- [ ] 动画规范已配置(过渡/标准)
- [ ] 前端规则表已创建(frontend_rules)
- [ ] 前端组件规则表已创建(frontend_component_rules)

### 弹窗文档规则操作
- [ ] 弹窗功能启用已配置
- [ ] 默认弹窗类型已配置(modal)
- [ ] 默认弹窗大小已配置(medium)
- [ ] 默认弹窗位置已配置(center)
- [ ] 弹窗规则表已创建(dialog_rules)
- [ ] 弹窗文档表已创建(dialog_documents)
- [ ] 欢迎文档功能已启用
- [ ] 欢迎文档只显示一次已配置
- [ ] 说明文档功能已启用
- [ ] 通知文档功能已启用
- [ ] 通知弹窗自动关闭已配置
- [ ] 弹窗动画已启用
- [ ] 弹窗文档从数据库读取已实现
- [ ] 弹窗文档写穿同步已实现

### 版本历史规则操作
- [ ] 版本历史表已创建(system_version_history)
- [ ] 系统版本号已更新(SYS_VERSION)
- [ ] 历史版本记录已写入(1.0.0-10.0.0)
- [ ] 版本号规则已配置(语义化版本)
- [ ] 版本状态规则已配置(stable/beta/alpha/dev)
- [ ] 版本升级流程已记录
- [ ] 版本回滚规则已配置
- [ ] 例行维护脚本已创建(routine_maintenance.py)
- [ ] 数据库完整性检查已配置
- [ ] 维护日志记录已配置

### 自动化调度规则操作
- [ ] 自动化调度引擎已创建(auto_scheduler.py)
- [ ] 调度引擎规则已配置(12条AUTO_SCHEDULER_规则)
- [ ] 任务规则已配置(13条AUTO_TASK_规则)
- [ ] 调度轮次间隔已配置(30秒)
- [ ] 数据库健康检查任务已启用
- [ ] 规则状态同步任务已启用
- [ ] 日志清理任务已启用
- [ ] 版本号检查任务已启用
- [ ] AI员工检查任务已启用
- [ ] Git同步检查任务已启用
- [ ] 权限同步任务已启用
- [ ] 沙盒健康检查任务已启用
- [ ] 文档清理任务已启用
- [ ] 自动修复监控任务已启用
- [ ] 阵列同步检查任务已启用
- [ ] 引擎健康检查任务已启用
- [ ] 员工日志清理任务已启用
- [ ] 调度引擎已后台启动
- [ ] 维护日志记录到数据库已实现
- [ ] 进程保护规则已配置(15条)
- [ ] SIGTERM/SIGINT信号拦截已实现
- [ ] 终止警告框(macOS原生对话框)已实现
- [ ] 终止二次确认已实现
- [ ] 终止原因填写(≥10字符)已实现
- [ ] 控制脚本(scheduler_control.py)已创建
- [ ] 启动/停止/重启/状态查询命令已实现
- [ ] 所有操作记录到system_maintenance_logs已实现
- [ ] 心跳文件(.scheduler_heartbeat)已实现
- [ ] PID文件(.scheduler_pid)已实现
- [ ] 进程保护验证通过(SIGTERM被拦截)

### 系统黑匣子规则操作
- [ ] 黑匣子引擎已创建(blackbox_recorder.py)
- [ ] 黑匣子规则已配置(28条BLACKBOX_规则)
- [ ] 灾难事件主表已创建(system_blackbox, 42字段)
- [ ] 操作动作记录表已创建(blackbox_action_log, 15字段)
- [ ] 系统快照表已创建(blackbox_system_snapshot, 14字段)
- [ ] 前置操作捕获已实现(50条/1小时窗口)
- [ ] 后置操作记录已实现
- [ ] 系统状态快照已实现(内存/CPU/磁盘/网络)
- [ ] 数据库状态采集已实现
- [ ] 调度引擎状态采集已实现
- [ ] AI系统状态采集已实现
- [ ] 堆栈跟踪捕获已实现
- [ ] 相关日志采集已实现(100条)
- [ ] 自动恢复机制已实现(3次重试)
- [ ] 灾难事件类型已定义(10种)
- [ ] 灾难级别已定义(disaster/critical/warning/info)
- [ ] 黑匣子已集成到调度引擎(auto_scheduler.py)
- [ ] 所有操作上报数据库已实现
- [ ] 黑匣子功能验证通过

---

## 12. 附录

### 12.1 数据库表结构

#### ai_employees 表
| 字段 | 类型 | 说明 |
|------|------|------|
| employee_id | TEXT | 员工ID(主键) |
| name | TEXT | 员工名称 |
| employee_type | TEXT | 员工类型 |
| level | INTEGER | 员工等级 |
| status | TEXT | 员工状态 |
| capabilities | TEXT | 能力列表(JSON) |
| personality | TEXT | 性格属性(JSON) |
| learning_progress | REAL | 学习进度 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

#### ai_engine_config 表
| 字段 | 类型 | 说明 |
|------|------|------|
| engine_type | TEXT | 引擎类型(主键) |
| config | TEXT | 配置(JSON) |
| version | TEXT | 版本号 |
| updated_at | TEXT | 更新时间 |

#### ai_cluster_config 表
| 字段 | 类型 | 说明 |
|------|------|------|
| cluster_id | TEXT | 集群ID(主键) |
| cluster_type | TEXT | 集群类型 |
| config | TEXT | 配置(JSON) |
| status | TEXT | 集群状态 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

#### ai_brain_knowledge 表
| 字段 | 类型 | 说明 |
|------|------|------|
| knowledge_id | TEXT | 知识ID(主键) |
| title | TEXT | 知识标题 |
| content | TEXT | 知识内容(加密) |
| knowledge_type | TEXT | 知识类型 |
| source | TEXT | 知识来源 |
| tags | TEXT | 标签列表(JSON) |
| priority | INTEGER | 优先级 |
| status | TEXT | 状态 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

### 12.2 错误码

| 错误码 | 说明 |
|--------|------|
| AI_EMPLOYEE_NOT_FOUND | AI员工不存在 |
| AI_EMPLOYEE_DISABLED | AI员工已禁用 |
| AI_ENGINE_UNAVAILABLE | AI引擎不可用 |
| AI_CLUSTER_ERROR | AI集群错误 |
| AI_KNOWLEDGE_INVALID | 知识验证失败 |
| AI_PERMISSION_DENIED | 权限不足 |

### 12.3 代码文件映射表

#### 权威基类定义

| 组件 | 权威文件 | 说明 |
|------|---------|------|
| AIEmployee基类 | `ai_engines/ai_employee_system.py` | **权威基类**，定义AI员工核心能力和智能赋能接口 |
| 分布式AI员工 | `ai_engines/distributed_ai_employee_manager.py` | 分布式部署扩展，继承权威基类 |

#### AI员工管理器

| 文件 | 说明 |
|------|------|
| `ai_engines/ai_employee_manager.py` | AI员工管理器，负责员工创建、注册、调度 |
| `app/ai/ai_orchestrator.py` | AI员工编排器，负责员工成长周期管理 |

#### AI引擎组件

| 文件 | 说明 |
|------|------|
| `ai_engines/intelligent_empowerment.py` | 智能赋能系统（性格模拟+网络学习引擎） |
| `ai_engines/ai_brain_service.py` | AI脑库服务 |
| `ai_engines/ai_brain_api.py` | AI脑库API接口 |
| `ai_engines/ai_brain_enhancer.py` | AI脑库增强器 |
| `ai_engines/deep_learning.py` | 深度学习引擎 |
| `ai_engines/ai_learning.py` | AI学习系统 |
| `ai_engines/auto_sync_upgrade_service.py` | 自动同步升级服务（Git/GitHub同步+系统升级） |
| `ai_engines/homework_grading_engine.py` | 自动阅卷引擎（作业/考试批改） |
| `exam_generator.py` | AI自动组卷系统 |

#### AI集群组件

| 文件 | 说明 |
|------|------|
| `ai_engines/ai_cluster_manager.py` | AI集群管理器 |
| `ai_engines/ai_cluster_api.py` | AI集群API接口 |
| `ai_engines/cluster_matrix_manager.py` | 集群矩阵管理器 |
| `ai_engines/cluster_array_api.py` | 集群阵列API接口 |

#### AI专业员工

| 文件 | 说明 |
|------|------|
| `ai_engines/ai_employees.py` | 通用AI员工 |
| `ai_engines/arduino_ai_employees.py` | Arduino开发AI员工 |
| `ai_engines/diagnostics_repair_employee.py` | 诊断修复AI员工 |
| `ai_engines/politics_question_employee.py` | 政治题库AI员工 |
| `ai_engines/listening_question_employee.py` | 听力题库AI员工 |
| `ai_engines/question_bank_maintenance_employee.py` | 题库维护AI员工 |

#### 数据同步

| 文件 | 说明 |
|------|------|
| `ai_engines/data_sync.py` | 数据同步模块（写穿机制） |

---

**规则版本**：v10.0.0  
**生效日期**：2026-07-28  
**适用范围**：MTSCOS AI系统所有AI相关操作  
**优先级**：本规则优先级高于其他开发规则，AI操作必须优先遵循本规范