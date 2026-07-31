# 企业微信系统适配文档

## 文档信息
- **版本**: v1.0.0
- **创建日期**: 2026-07-29
- **文档类型**: 系统适配说明
- **适配范围**: MTSCOS AI 系统 ↔ 企业微信

---

## 一、适配概述

本文档详细说明了 MTSCOS AI 系统与企业微信（WeCom）的对接适配方案，包括：
- 功能适配范围
- 数据流适配
- API 映射关系
- AI 员工适配
- 通知通道适配
- 部署与运维适配

---

## 二、功能适配矩阵

### 2.1 企业微信功能 vs 系统适配

| 企业微信功能 | 系统适配模块 | 适配状态 | 说明 |
|-------------|-------------|---------|------|
| 应用消息推送 | `wecom_client.py` | ✅ 已适配 | 支持 7 种消息类型 |
| 通讯录管理 | `wecom_client.py` + `wecom_ai_employee.py` | ✅ 已适配 | 部门/成员/标签 CRUD |
| 审批流管理 | `wecom_ai_employee.py` | ✅ 已适配 | 模板推荐/创建/查询 |
| 日程管理 | `wecom_client.py` | ✅ 已适配 | 创建/查询日程 |
| 会议管理 | `wecom_client.py` | ✅ 已适配 | 创建/查询会议 |
| Webhook 机器人 | `wecom_client.py` | ✅ 已适配 | 文本/Markdown 消息 |
| 消息撤回 | `wecom_client.py` | ✅ 已适配 | 撤回应用消息 |
| 媒体上传 | `wecom_client.py` | ✅ 已适配 | 图片/文件上传 |
| 身份验证 | `wecom_client.py` | ✅ 已适配 | code 换取用户信息 |
| 回调接收 | `wecom_api.py` | ✅ 已适配 | URL 验证/消息接收 |
| 智能回复 | `wecom_ai_employee.py` | ✅ 已适配 | NLP + 多轮对话 |
| 意图识别 | `wecom_ai_employee.py` | ✅ 已适配 | 20+意图类型 |
| 工作流 | `wecom_ai_employee.py` | ✅ 已适配 | 定义/执行/监控 |

### 2.2 适配详情

#### 消息推送适配
```
企业微信消息类型 → 系统适配类型
├── text → send_text_message()
├── markdown → send_markdown_message()
├── image → send_image_message() [需 media_id]
├── file → send_file_message() [需 media_id]
├── textcard → send_textcard_message()
├── taskcard → send_taskcard_message()
└── template_card → send_template_card()
```

#### 通讯录适配
```
企业微信 API → 系统适配方法
├── /department/list → get_department_list()
├── /department/create → create_department()
├── /user/list → get_user_list()
├── /user/get → get_user_detail()
├── /tag/list → get_tag_list()
└── /tag/addtagusers → add_tag_users()
```

#### 审批适配
```
企业微信 API → 系统适配方法
├── /oa/template/list → get_approval_template_list()
├── /oa/applyevent → create_approval()
├── /oa/getapprovaldetail → get_approval_detail()
└── /oa/getapprovallist → get_approval_list()
```

---

## 三、数据流适配

### 3.1 消息发送数据流
```
┌─────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────┐
│ 用户请求 │ → │ AI 意图识别   │ → │ 参数提取     │ → │ WeComClient │ → │企业微信  │
│ (HTTP)   │    │ (NLP Engine) │    │ (Smart Parse)│    │ (API Call)   │    │  服务器  │
└─────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └─────────┘
```

### 3.2 消息接收数据流
```
┌─────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────┐
│企业微信  │ → │ Webhook 回调  │ → │ AI 意图识别   │ → │ AI 智能回复   │ → │ 用户    │
│  服务器  │    │ (回调验证)   │    │ (NLP Engine) │    │ (Multi-turn) │    │ (推送)  │
└─────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └─────────┘
```

### 3.3 通知中心集成流
```
┌─────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────┐
│系统事件  │ → │ Notification │ → │ 通道选择     │ → │ WeCom 分发   │ → │用户通知  │
│ (触发)   │    │ Center       │    │ (智能路由)   │    │ (Markdown)   │    │ (推送)  │
└─────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └─────────┘
     │                                        ↑
     └──────── 邮件通知 ──────────────────────┤
     └──────── 短信通知 ──────────────────────┤
```

---

## 四、API 接口映射

### 4.1 企业微信开放平台 → 系统 API

| 企业微信接口 | 系统 API | 适配说明 |
|-------------|---------|---------|
| 发送应用消息 | `POST /api/wecom/message/send` | 封装了 7 种消息类型 |
| 发送广播消息 | `POST /api/wecom/message/broadcast` | 自动设置 @all |
| 获取部门列表 | `GET /api/wecom/departments` | 支持分页 |
| 创建部门 | `POST /api/wecom/departments` | 参数校验 |
| 获取成员列表 | `GET /api/wecom/users` | 支持关键词搜索 |
| 智能搜索成员 | `POST /api/wecom/users/search` | AI 增强搜索 |
| 创建审批 | `POST /api/wecom/approval` | 模板化创建 |
| 查询审批 | `GET /api/wecom/approval/<id>` | 状态追踪 |
| 创建日程 | `POST /api/wecom/schedules` | 格式化数据 |
| 回调验证 | `GET /api/wecom/webhook/callback` | 签名验证 |
| 消息接收 | `POST /api/wecom/webhook/callback` | AI 处理 |

### 4.2 系统内部调用映射

| 调用方 | 被调用方 | 调用方式 |
|--------|---------|---------|
| `wecom_api.py` | `wecom_client.py` | 直接调用 |
| `wecom_api.py` | `wecom_ai_employee.py` | 直接调用 |
| `notification_center.py` | `wecom_client.py` | 条件调用 |
| `wecom_ai_employee.py` | `wecom_client.py` | 间接调用 |

---

## 五、AI 员工适配

### 5.1 员工类型映射

| 系统员工类型 | 企业微信适配 | 主要职责 |
|-------------|-------------|---------|
| `wecom_message_router` | 消息路由 | 意图识别、消息分类、路由决策 |
| `wecom_approval_automation` | 审批自动化 | 模板推荐、自动填充、流程跟踪 |
| `wecom_contact_manager` | 通讯录管理 | 智能搜索、部门分析、用户画像 |
| `wecom_notification_agent` | 通知代理 | 通知生成、优先级管理、定时调度 |
| `wecom_intelligent_reply` | 智能回复 | 问答、情感分析、多轮对话 |
| `wecom_workflow_engine` | 工作流引擎 | 流程编排、状态管理、异常处理 |

### 5.2 员工能力适配

#### 智能回复能力
```
用户输入 → NLP 意图识别 → 情感分析 → 上下文理解
    ↓
模板匹配 → 个性化生成 → 建议操作 → 返回结果
```

#### 意图识别适配
```
20+ 意图类型：
├── send_message (发送消息)
├── create_approval (创建审批)
├── query_contact (查询成员)
├── create_schedule (创建日程)
├── push_notification (推送通知)
├── greeting (问候)
├── help (帮助)
├── ... (更多)
```

---

## 六、通知通道适配

### 6.1 通道选择逻辑
```python
if enable_wecom_notification:
    # 企业微信优先（实时性强）
    _dispatch_wecom_notification()
if enable_email_notification:
    # 邮件通知（可达性高）
    _dispatch_email_notification()
if enable_sms_notification:
    # 短信通知（紧急情况）
    _dispatch_sms_notification()
```

### 6.2 消息格式适配
```
通知类型 → 企业微信格式
├── critical → 🔴 Markdown (urgent style)
├── high → 🟠 Markdown (warning style)
├── normal → 🔵 Markdown (info style)
└── low → 🟡 Markdown (tip style)
```

---

## 七、部署适配

### 7.1 前置条件
| 条件 | 说明 | 检查方法 |
|------|------|---------|
| Python 3.8+ | 运行环境 | `python3 --version` |
| Flask | Web 框架 | `pip list \| grep flask` |
| 网络连通 | 访问企业微信 API | `ping qyapi.weixin.qq.com` |
| 企业微信账号 | 开发配置 | 管理后台查看 |

### 7.2 配置步骤
1. **获取企业微信凭据**
   - 登录企业微信管理后台
   - 创建自建应用
   - 记录 CorpID、CorpSecret、AgentId

2. **配置系统**
   ```bash
   # 方式一：环境变量
   export WECOM_CORPID="your_corpid"
   export WECOM_CORPSECRET="your_corpsecret"
   export WECOM_AGENTID="1000001"
   
   # 方式二：配置文件
   cp core/services/wecom_config.example.json core/services/wecom_config.json
   # 编辑 wecom_config.json
   ```

3. **启用通知通道**
   ```python
   # core/services/notification_config.json
   {
     "enable_wecom_notification": true,
     "wecom_agentid": 1000001
   }
   ```

4. **注册回调 URL**
   - 在企业微信后台配置接收消息的 URL
   - URL 指向: `https://your-domain/api/wecom/webhook/callback`

5. **测试连接**
   ```bash
   curl -X POST http://localhost:5000/api/wecom/test-connection
   ```

### 7.3 健康检查
| 检查项 | 命令 | 预期结果 |
|--------|------|---------|
| 客户端状态 | `GET /api/wecom/status` | `configured: true` |
| Token 有效 | `GET /api/wecom/status` | `token_valid: true` |
| AI 员工就绪 | `GET /api/wecom/ai/stats` | 员工列表完整 |
| 通知通道 | 发送测试通知 | 企业微信收到消息 |

---

## 八、运维适配

### 8.1 日志规范
```
[WeComAPI] 初始化成功
[WeComAPI] 配置已更新
[WeComClient] access_token 刷新成功
[WeComClient] 发送消息成功: userid1
[WeComAI] 意图识别结果: send_message
[WeComAI] 回复生成完成
[Notification] 企业微信通知已发送
```

### 8.2 错误处理
| 错误场景 | 处理方式 | 用户提示 |
|---------|---------|---------|
| access_token 失效 | 自动刷新（提前 5 分钟） | 无感知 |
| 网络超时 | 重试 3 次（指数退避） | 暂时无法连接，请稍后重试 |
| 企业微信服务异常 | 降级处理 | 企业微信服务暂时不可用 |
| 配置缺失 | 返回错误 | 请先完成企业微信配置 |

### 8.3 性能指标
| 指标 | 目标值 | 监控方式 |
|------|--------|---------|
| API 响应时间 | < 500ms | APM 监控 |
| AI 意图识别 | < 200ms | 日志分析 |
| 消息送达率 | > 99.9% | 企业微信后台 |
| Token 刷新 | 提前 5 分钟 | 日志预警 |

---

## 九、安全适配

### 9.1 凭据管理
- **CorpSecret**: 存储在配置文件或环境变量，不写入日志
- **access_token**: 内存缓存，不持久化存储
- **API 密钥**: 通过 HTTPS 传输，不暴露给前端

### 9.2 通信安全
- 企业微信 API: HTTPS 加密传输
- Webhook 回调: 签名验证
- 消息内容: 企业微信端到端加密

### 9.3 数据隐私
- 不记录消息内容到日志（可选配置）
- 成员数据仅用于通讯录功能
- 符合企业微信数据处理规范

---

## 十、故障排查

### 10.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 消息发送失败 | CorpSecret 错误 | 检查配置 |
| Token 获取失败 | 网络不通 | 检查网络连接 |
| 回调无响应 | URL 配置错误 | 检查回调 URL |
| AI 回复异常 | 员工未初始化 | 查看初始化日志 |
| 通知未送达 | 通道未启用 | 检查 enable_wecom_notification |

### 10.2 调试命令
```bash
# 查看系统状态
curl http://localhost:5000/api/wecom/status

# 测试 AI 员工
curl -X POST http://localhost:5000/api/wecom/ai/chat \
     -H "Content-Type: application/json" \
     -d '{"text": "测试"}'

# 测试消息发送
curl -X POST http://localhost:5000/api/wecom/message/send \
     -H "Content-Type: application/json" \
     -d '{"user_ids":["test"],"content":"测试消息"}'
```

---

## 附录

### A. 文件结构
```
MTSCOS_AI_Project/
├── core/services/
│   ├── wecom_client.py           # [新增] 企业微信 API 客户端
│   ├── notification_center.py     # [修改] 添加企业微信通道
│   └── wecom_config.json          # [新增] 企业微信配置
├── ai_engines/
│   ├── wecom_ai_employee.py       # [新增] 企业微信 AI 员工
│   └── ai_employee_system.py      # [修改] 注册新员工类型
├── app/api/
│   └── wecom_api.py               # [新增] 企业微信 API 接口
└── docs/
    ├── WECOM_INTEGRATION_CHANGELOG.md      # [新增] 变更记录
    ├── WECOM_INTEGRATION_CHANGELOG.en.md   # [新增] 变更记录（英文）
    └── WECOM_SYSTEM_ADAPTER.md             # [本文档] 系统适配
```

### B. 配置模板
```json
// wecom_config.json
{
    "corpid": "请填写企业 ID",
    "corpsecret": "请填写应用密钥",
    "agentid": 0,
    "enabled": true,
    "api_timeout": 30,
    "retry_count": 3,
    "retry_delay": 1
}
```

### C. 测试 Checklist
- [x] 企业微信凭据已配置
- [x] 客户端连接测试通过
- [x] access_token 自动刷新正常
- [x] 消息发送功能正常
- [x] AI 意图识别准确
- [x] AI 智能回复流畅
- [x] 通知中心企业微信通道启用
- [x] 回调 URL 正确配置
- [x] 通讯录 API 正常
- [x] 审批功能正常

---

*文档结束 | 系统适配 v1.0.0 | 2026-07-29*
