# 企业微信集成变更记录文档

## 文档信息
- **版本**: v1.0.0
- **创建日期**: 2026-07-29
- **作者**: MTSCOS AI 系统
- **状态**: ✅ 已完成

---

## 一、变更概述

本次变更实现了企业微信（WeCom）功能的完整对接，包括：
- 企业微信开放平台 API 客户端
- 6 类 AI 智能化员工
- 完整的 RESTful API 接口
- 通知中心企业微信通道集成
- 系统适配与配置管理

---

## 二、新增文件清单

### 2.1 核心服务层
| 文件路径 | 说明 | 行数 |
|---------|------|------|
| `core/services/wecom_client.py` | 企业微信 API 客户端 | ~500 |

**核心功能**：
- access_token 自动获取与缓存刷新（提前5分钟）
- 应用消息推送（文本、Markdown、图片、文件、卡片等7种类型）
- 通讯录管理（部门、成员、标签 CRUD）
- 审批流管理（模板查询、审批创建、状态查询）
- 日程/会议管理
- 企业微信群机器人 Webhook
- 消息撤回、媒体上传、身份验证
- 单例管理、线程安全、重试机制

### 2.2 AI 员工层
| 文件路径 | 说明 | 行数 |
|---------|------|------|
| `ai_engines/wecom_ai_employee.py` | 企业微信 AI 员工系统 | ~800 |

**6 类 AI 员工**：

| 员工类名 | 类型标识 | 核心能力 |
|---------|---------|---------|
| `WeComMessageRouter` | `wecom_message_router` | 智能消息路由、意图识别、路由规则引擎 |
| `WeComApprovalAutomation` | `wecom_approval_automation` | 审批模板推荐、自动填充、流程跟踪 |
| `WeComContactManager` | `wecom_contact_manager` | 智能成员搜索、部门分析、用户画像 |
| `WeComNotificationAgent` | `wecom_notification_agent` | 智能通知生成、优先级管理、定时调度 |
| `WeComIntelligentReply` | `wecom_intelligent_reply` | 自然语言问答、情感分析、多轮对话 |
| `WeComWorkflowEngine` | `wecom_workflow_engine` | 工作流编排、条件分支、状态管理 |

**AI 能力**：
- NLP 意图识别（20+ 意图类型）
- 参数智能提取（@人、日期、金额、天数等）
- 情感分析（positive/negative/urgent/neutral）
- 多轮对话上下文管理
- 智能回复模板（问候、帮助、审批、通知等）
- 工作流定义与执行

### 2.3 API 接口层
| 文件路径 | 说明 | 行数 |
|---------|------|------|
| `app/api/wecom_api.py` | 企业微信 API 接口 | ~500 |

**API 端点清单**（共 18 个）：

#### 配置管理（3 个）
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/wecom/config` | GET | 获取配置 |
| `/api/wecom/config` | POST | 更新配置 |
| `/api/wecom/test-connection` | POST | 测试连接 |

#### 消息发送（3 个）
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/wecom/message/send` | POST | 发送消息（7种类型） |
| `/api/wecom/message/broadcast` | POST | 广播消息（@all） |
| `/api/wecom/webhook/send` | POST | 群机器人 Webhook |

#### 通讯录管理（4 个）
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/wecom/departments` | GET/POST | 部门列表/创建 |
| `/api/wecom/users` | GET | 成员列表 |
| `/api/wecom/users/search` | POST | 智能搜索成员 |
| `/api/wecom/tags` | GET | 标签列表 |

#### 审批管理（4 个）
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/wecom/approval/templates` | GET | 审批模板列表 |
| `/api/wecom/approval` | POST | 创建审批 |
| `/api/wecom/approval/<id>` | GET | 查询审批状态 |
| `/api/wecom/approval/analyze` | GET | 审批数据分析 |

#### 日程管理（2 个）
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/wecom/schedules` | GET/POST | 获取/创建日程 |
| - | - | - |

#### AI 智能接口（6 个）
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/wecom/ai/chat` | POST | AI 智能对话 |
| `/api/wecom/ai/intent` | POST | 意图识别 |
| `/api/wecom/ai/notification` | POST | 智能通知 |
| `/api/wecom/ai/approval-recommend` | POST | 审批推荐 |
| `/api/wecom/ai/workflow/execute` | POST | 工作流执行 |
| `/api/wecom/ai/stats` | GET | AI 员工统计 |

#### Webhook 回调（1 个）
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/wecom/webhook/callback` | GET/POST | 回调验证与消息接收 |

#### 系统状态（1 个）
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/wecom/status` | GET | 系统状态 |

---

## 三、修改文件清单

### 3.1 AI 员工系统配置
| 文件路径 | 修改内容 |
|---------|---------|
| `ai_engines/ai_employee_system.py` | 在 `_DOMAIN_MAP` 中添加 6 个新领域映射；在 `_PERSONALITY_MAP` 中添加 6 个新性格映射 |

**新增映射**：
```python
# _DOMAIN_MAP 新增
"wecom_message_router": "wecom_integration",
"wecom_approval_automation": "wecom_approval",
"wecom_contact_manager": "wecom_contact",
"wecom_notification_agent": "wecom_notification",
"wecom_intelligent_reply": "wecom_ai_reply",
"wecom_workflow_engine": "wecom_workflow",

# _PERSONALITY_MAP 新增
"wecom_message_router": "analytical",
"wecom_approval_automation": "driven",
"wecom_contact_manager": "supportive",
"wecom_notification_agent": "driven",
"wecom_intelligent_reply": "creative",
"wecom_workflow_engine": "analytical",
```

### 3.2 通知中心扩展
| 文件路径 | 修改内容 |
|---------|---------|
| `core/services/notification_center.py` | 添加企业微信通知通道支持 |

**新增配置项**：
```python
'enable_wecom_notification': False,  # 默认关闭
'wecom_agentid': 0,                  # 企业微信应用 ID
'wecom_markdown_enabled': True,     # 是否启用 Markdown 格式
```

**新增方法**：
- `_dispatch_wecom_notification(notification)` - 企业微信通知分发

**修改方法**：
- `_load_config()` - 添加企业微信配置项
- `_dispatch_notification()` - 添加企业微信分发逻辑

---

## 四、系统架构变更

### 4.1 新增模块架构
```
┌─────────────────────────────────────────────────┐
│              API 接口层 (wecom_api)             │
├─────────────────────────────────────────────────┤
│          AI 员工层 (wecom_ai_employee)          │
│  ┌────────────┬────────────┬──────────────┐    │
│  │ 消息路由器  │ 审批自动化  │ 通讯录管理员工 │    │
│  ├────────────┼────────────┼──────────────┤    │
│  │ 通知代理员  │ 智能回复员  │ 工作流引擎员 │    │
│  └────────────┴────────────┴──────────────┘    │
├─────────────────────────────────────────────────┤
│         API 客户端层 (wecom_client)             │
│  ┌────────────┬────────────┬──────────────┐    │
│  │access_token │ 消息推送    │ 通讯录 API    │    │
│  ├────────────┼────────────┼──────────────┤    │
│  │ 审批 API    │ 日程/会议  │ Webhook      │    │
│  └────────────┴────────────┴──────────────┘    │
├─────────────────────────────────────────────────┤
│          已集成: NotificationCenter             │
│  (新增 enable_wecom_notification 通道)          │
└─────────────────────────────────────────────────┘
```

### 4.2 数据流
```
用户请求 → REST API → AI 员工路由 → 意图识别 → 参数提取
    ↓                                          ↓
AI 执行任务 ← 上下文管理 ← 对话历史 ← 情感分析 ← 智能匹配
    ↓
WeComClient API 调用 → 企业微信服务器 → 消息送达用户
    ↓
结果返回 → 通知中心 → 多通道分发（邮件/短信/企业微信）
```

---

## 五、配置说明

### 5.1 企业微信应用配置

在企业微信管理后台获取：
1. **CorpID**：企业 ID
2. **CorpSecret**：应用密钥
3. **AgentId**：应用 ID

### 5.2 配置方式

**方式一：环境变量**
```bash
export WECOM_CORPID="your_corpid"
export WECOM_CORPSECRET="your_corpsecret"
export WECOM_AGENTID="1000001"
```

**方式二：配置文件**
在 `core/services/wecom_config.json` 中配置：
```json
{
    "corpid": "your_corpid",
    "corpsecret": "your_corpsecret",
    "agentid": 1000001,
    "enabled": true,
    "api_timeout": 30,
    "retry_count": 3,
    "retry_delay": 1
}
```

**方式三：API 接口**
```bash
curl -X POST http://localhost:5000/api/wecom/config \
     -H "Content-Type: application/json" \
     -d '{"corpid": "xxx", "corpsecret": "xxx", "agentid": 1000001}'
```

### 5.3 通知中心配置

在 `core/services/notification_config.json` 中：
```json
{
    "enable_wecom_notification": true,
    "wecom_agentid": 1000001,
    "wecom_markdown_enabled": true
}
```

---

## 六、使用指南

### 6.1 快速开始

```python
# 获取企业微信客户端
from core.services.wecom_client import get_wecom_client
client = get_wecom_client()

# 发送消息
result = client.send_text_message(
    user_ids=['userid1', 'userid2'],
    content='你好，这是来自AI的消息！'
)

# 发送 Markdown 消息
result = client.send_markdown_message(
    user_ids=['@all'],
    content='## 系统通知\n\n**重要**：系统将于今晚维护'
)
```

### 6.2 AI 智能对话

```python
# 通过 API 调用
POST /api/wecom/ai/chat
{
    "text": "帮我发送通知给技术部",
    "user_id": "zhangsan",
    "context": {}
}

# 响应
{
    "intent": "send_message",
    "reply": "好的，请告诉我：\n1. 发送给谁？\n2. 消息内容是什么？",
    "suggestions": ["@某人", "发送文件", "定时发送"]
}
```

### 6.3 审批自动化

```python
# AI 推荐审批模板
POST /api/wecom/ai/approval-recommend
{
    "text": "我想请假3天"
}

# 创建审批
POST /api/wecom/approval
{
    "template_key": "leave",
    "data": {
        "leave_type": "年假",
        "start_date": "2026-08-01",
        "end_date": "2026-08-03",
        "reason": "个人事务",
        "days": 3
    }
}
```

### 6.4 Webhook 机器人

```python
# 发送群机器人消息
POST /api/wecom/webhook/send
{
    "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
    "content": "这是一条来自系统的通知",
    "msg_type": "text"
}
```

---

## 七、测试验证

### 7.1 连接测试
```bash
curl -X POST http://localhost:5000/api/wecom/test-connection
```

### 7.2 状态检查
```bash
curl http://localhost:5000/api/wecom/status
```

### 7.3 AI 员工统计
```bash
curl http://localhost:5000/api/wecom/ai/stats
```

---

## 八、兼容性说明

- **Python 版本**: 3.8+
- **框架依赖**: Flask（Web 服务）
- **网络依赖**: 需要访问 `qyapi.weixin.qq.com`
- **浏览器支持**: 企业微信桌面版、移动端

---

## 九、变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0.0 | 2026-07-29 | 初始版本：企业微信完整集成 | MTSCOS AI |

---

## 十、后续计划

- [ ] 添加企业微信 JS-SDK 网页授权
- [ ] 实现企业微信小程序跳转
- [ ] 集成企业微信直播接口
- [ ] 添加会话存档功能
- [ ] 实现家校沟通功能
- [ ] 移动端适配优化

---

*文档结束 | 企业微信集成 v1.0.0 | 2026-07-29*
