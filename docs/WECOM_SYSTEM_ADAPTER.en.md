# WeCom System Adapter Document

## Document Info
- **Version**: v1.0.0
- **Created**: 2026-07-29
- **Type**: System Adapter Specification
- **Scope**: MTSCOS AI System ↔ WeCom

---

## I. Adapter Overview

This document details the integration and adaptation plan between the MTSCOS AI System and WeCom (WeChat Work), including:
- Feature adaptation scope
- Data flow adaptation
- API mapping relationships
- AI employee adaptation
- Notification channel adaptation
- Deployment and operations adaptation

---

## II. Feature Adaptation Matrix

### 2.1 WeCom Feature vs System Adapter

| WeCom Feature | System Adapter Module | Status | Description |
|---------------|---------------------|--------|-------------|
| Application Message Push | `wecom_client.py` | ✅ Done | Supports 7 message types |
| Contact Management | `wecom_client.py` + `wecom_ai_employee.py` | ✅ Done | Department/member/tag CRUD |
| Approval Workflow | `wecom_ai_employee.py` | ✅ Done | Template recommendation/creation/query |
| Schedule Management | `wecom_client.py` | ✅ Done | Create/query schedules |
| Meeting Management | `wecom_client.py` | ✅ Done | Create/query meetings |
| Webhook Robot | `wecom_client.py` | ✅ Done | Text/Markdown messages |
| Message Recall | `wecom_client.py` | ✅ Done | Recall application messages |
| Media Upload | `wecom_client.py` | ✅ Done | Image/file upload |
| Identity Verification | `wecom_client.py` | ✅ Done | code exchange for user info |
| Callback Reception | `wecom_api.py` | ✅ Done | URL verification/message reception |
| Smart Reply | `wecom_ai_employee.py` | ✅ Done | NLP + multi-turn dialogue |
| Intent Recognition | `wecom_ai_employee.py` | ✅ Done | 20+ intent types |
| Workflow | `wecom_ai_employee.py` | ✅ Done | Define/execute/monitor |

### 2.2 Adaptation Details

#### Message Push Adaptation
```
WeCom Message Type → System Adapter Type
├── text → send_text_message()
├── markdown → send_markdown_message()
├── image → send_image_message() [requires media_id]
├── file → send_file_message() [requires media_id]
├── textcard → send_textcard_message()
├── taskcard → send_taskcard_message()
└── template_card → send_template_card()
```

#### Contact Adaptation
```
WeCom API → System Adapter Method
├── /department/list → get_department_list()
├── /department/create → create_department()
├── /user/list → get_user_list()
├── /user/get → get_user_detail()
├── /tag/list → get_tag_list()
└── /tag/addtagusers → add_tag_users()
```

#### Approval Adaptation
```
WeCom API → System Adapter Method
├── /oa/template/list → get_approval_template_list()
├── /oa/applyevent → create_approval()
├── /oa/getapprovaldetail → get_approval_detail()
└── /oa/getapprovallist → get_approval_list()
```

---

## III. Data Flow Adaptation

### 3.1 Message Sending Flow
```
┌─────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────┐
│ User    │ → │ AI Intent    │ → │ Parameter    │ → │ WeComClient │ → │ WeCom   │
│ Request │    │ Recognition  │    │ Extraction   │    │ (API Call)  │    │ Server  │
│ (HTTP)   │    │ (NLP Engine) │    │ (Smart Parse)│    │             │    │         │
└─────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └─────────┘
```

### 3.2 Message Reception Flow
```
┌─────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────┐
│ WeCom   │ → │ Webhook      │ → │ AI Intent    │ → │ AI Smart     │ → │ User    │
│ Server  │    │ Callback     │    │ Recognition  │    │ Reply        │    │ (Push)  │
│         │    │ (Verify)     │    │ (NLP Engine) │    │ (Multi-turn) │    │         │
└─────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └─────────┘
```

### 3.3 Notification Center Integration
```
┌─────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────┐
│ System  │ → │ Notification │ → │ Channel      │ → │ WeCom        │ → │ User    │
│ Event   │    │ Center       │    │ Selection    │    │ Dispatch     │    │ (Push)  │
│ (Trigger)│   │              │    │ (Smart Route)│    │ (Markdown)   │    │         │
└─────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └─────────┘
     │                                        ↑
     └──────── Email Notification ────────────┤
     └──────── SMS Notification ──────────────┤
```

---

## IV. API Interface Mapping

### 4.1 WeCom Open Platform → System API

| WeCom Interface | System API | Adaptation Notes |
|----------------|-----------|------------------|
| Send Application Message | `POST /api/wecom/message/send` | Encapsulates 7 message types |
| Broadcast Message | `POST /api/wecom/message/broadcast` | Auto-sets @all |
| Get Department List | `GET /api/wecom/departments` | Supports pagination |
| Create Department | `POST /api/wecom/departments` | Parameter validation |
| Get Member List | `GET /api/wecom/users` | Supports keyword search |
| Smart Search Members | `POST /api/wecom/users/search` | AI-enhanced search |
| Create Approval | `POST /api/wecom/approval` | Template-based creation |
| Query Approval | `GET /api/wecom/approval/<id>` | Status tracking |
| Create Schedule | `POST /api/wecom/schedules` | Formatted data |
| Callback Verification | `GET /api/wecom/webhook/callback` | Signature verification |
| Message Reception | `POST /api/wecom/webhook/callback` | AI processing |

### 4.2 System Internal Call Mapping

| Caller | Callee | Call Method |
|--------|--------|-------------|
| `wecom_api.py` | `wecom_client.py` | Direct call |
| `wecom_api.py` | `wecom_ai_employee.py` | Direct call |
| `notification_center.py` | `wecom_client.py` | Conditional call |
| `wecom_ai_employee.py` | `wecom_client.py` | Indirect call |

---

## V. AI Employee Adaptation

### 5.1 Employee Type Mapping

| System Employee Type | WeCom Adaptation | Primary Responsibilities |
|---------------------|------------------|------------------------|
| `wecom_message_router` | Message Routing | Intent recognition, message classification, routing decisions |
| `wecom_approval_automation` | Approval Automation | Template recommendation, auto-fill, workflow tracking |
| `wecom_contact_manager` | Contact Management | Smart search, department analysis, user profiling |
| `wecom_notification_agent` | Notification Agent | Notification generation, priority management, scheduled dispatch |
| `wecom_intelligent_reply` | Smart Reply | Q&A, sentiment analysis, multi-turn dialogue |
| `wecom_workflow_engine` | Workflow Engine | Process orchestration, state management, exception handling |

### 5.2 Employee Capability Adaptation

#### Smart Reply Capability
```
User Input → NLP Intent Recognition → Sentiment Analysis → Context Understanding
    ↓
Template Matching → Personalized Generation → Suggested Actions → Return Result
```

#### Intent Recognition Adaptation
```
20+ Intent Types:
├── send_message
├── create_approval
├── query_contact
├── create_schedule
├── push_notification
├── greeting
├── help
├── ... (more)
```

---

## VI. Notification Channel Adaptation

### 6.1 Channel Selection Logic
```python
if enable_wecom_notification:
    # WeCom priority (strong real-time)
    _dispatch_wecom_notification()
if enable_email_notification:
    # Email notification (high reach)
    _dispatch_email_notification()
if enable_sms_notification:
    # SMS notification (urgent cases)
    _dispatch_sms_notification()
```

### 6.2 Message Format Adaptation
```
Notification Type → WeCom Format
├── critical → 🔴 Markdown (urgent style)
├── high → 🟠 Markdown (warning style)
├── normal → 🔵 Markdown (info style)
└── low → 🟡 Markdown (tip style)
```

---

## VII. Deployment Adaptation

### 7.1 Prerequisites
| Condition | Description | Check Method |
|-----------|-------------|-------------|
| Python 3.8+ | Runtime environment | `python3 --version` |
| Flask | Web framework | `pip list \| grep flask` |
| Network connectivity | Access WeCom API | `ping qyapi.weixin.qq.com` |
| WeCom account | Development configuration | Admin console |

### 7.2 Configuration Steps
1. **Get WeCom Credentials**
   - Login to WeCom admin console
   - Create self-built application
   - Record CorpID, CorpSecret, AgentId

2. **Configure System**
   ```bash
   # Method 1: Environment variables
   export WECOM_CORPID="your_corpid"
   export WECOM_CORPSECRET="your_corpsecret"
   export WECOM_AGENTID="1000001"
   
   # Method 2: Configuration file
   cp core/services/wecom_config.example.json core/services/wecom_config.json
   # Edit wecom_config.json
   ```

3. **Enable Notification Channel**
   ```python
   # core/services/notification_config.json
   {
     "enable_wecom_notification": true,
     "wecom_agentid": 1000001
   }
   ```

4. **Register Callback URL**
   - Configure message receiving URL in WeCom admin console
   - URL should point to: `https://your-domain/api/wecom/webhook/callback`

5. **Test Connection**
   ```bash
   curl -X POST http://localhost:5000/api/wecom/test-connection
   ```

### 7.3 Health Check
| Check Item | Command | Expected Result |
|-----------|---------|-----------------|
| Client status | `GET /api/wecom/status` | `configured: true` |
| Token valid | `GET /api/wecom/status` | `token_valid: true` |
| AI employee ready | `GET /api/wecom/ai/stats` | Complete employee list |
| Notification channel | Send test notification | WeCom receives message |

---

## VIII. Operations Adaptation

### 8.1 Log Standards
```
[WeComAPI] Initialization successful
[WeComAPI] Configuration updated
[WeComClient] access_token refreshed successfully
[WeComClient] Message sent successfully: userid1
[WeComAI] Intent recognition result: send_message
[WeComAI] Reply generation completed
[Notification] WeCom notification sent
```

### 8.2 Error Handling
| Error Scenario | Handling Method | User Prompt |
|---------------|----------------|-------------|
| access_token expired | Auto-refresh (5 min early) | Transparent |
| Network timeout | Retry 3 times (exponential backoff) | Temporary connection issue, please try later |
| WeCom service exception | Degraded handling | WeCom service temporarily unavailable |
| Missing configuration | Return error | Please complete WeCom configuration first |

### 8.3 Performance Metrics
| Metric | Target | Monitoring Method |
|--------|--------|-------------------|
| API response time | < 500ms | APM monitoring |
| AI intent recognition | < 200ms | Log analysis |
| Message delivery rate | > 99.9% | WeCom backend |
| Token refresh | 5 minutes early | Log alert |

---

## IX. Security Adaptation

### 9.1 Credential Management
- **CorpSecret**: Stored in config file or environment variable, not written to logs
- **access_token**: Memory cache, not persisted
- **API keys**: Transmitted via HTTPS, not exposed to frontend

### 9.2 Communication Security
- WeCom API: HTTPS encrypted transmission
- Webhook callback: Signature verification
- Message content: WeCom end-to-end encryption

### 9.3 Data Privacy
- Message content not recorded in logs (configurable)
- Member data only used for contact features
- Compliant with WeCom data processing standards

---

## X. Troubleshooting

### 10.1 Common Issues

| Problem | Possible Cause | Solution |
|---------|---------------|----------|
| Message sending failed | CorpSecret error | Check configuration |
| Token retrieval failed | Network issue | Check network connection |
| No callback response | URL configuration error | Check callback URL |
| AI reply exception | Employee not initialized | Check initialization logs |
| Notification not delivered | Channel not enabled | Check enable_wecom_notification |

### 10.2 Debug Commands
```bash
# Check system status
curl http://localhost:5000/api/wecom/status

# Test AI employee
curl -X POST http://localhost:5000/api/wecom/ai/chat \
     -H "Content-Type: application/json" \
     -d '{"text": "Test"}'

# Test message sending
curl -X POST http://localhost:5000/api/wecom/message/send \
     -H "Content-Type: application/json" \
     -d '{"user_ids":["test"],"content":"Test message"}'
```

---

## Appendix

### A. File Structure
```
MTSCOS_AI_Project/
├── core/services/
│   ├── wecom_client.py           # [NEW] WeCom API Client
│   ├── notification_center.py    # [MODIFIED] Added WeCom channel
│   └── wecom_config.json         # [NEW] WeCom configuration
├── ai_engines/
│   ├── wecom_ai_employee.py      # [NEW] WeCom AI Employee
│   └── ai_employee_system.py     # [MODIFIED] Registered new employee types
├── app/api/
│   └── wecom_api.py              # [NEW] WeCom API Interfaces
└── docs/
    ├── WECOM_INTEGRATION_CHANGELOG.md      # [NEW] Change log
    ├── WECOM_INTEGRATION_CHANGELOG.en.md   # [NEW] Change log (EN)
    └── WECOM_SYSTEM_ADAPTER.md             # [THIS] System adapter
```

### B. Configuration Template
```json
// wecom_config.json
{
    "corpid": "Please fill in enterprise ID",
    "corpsecret": "Please fill in application secret",
    "agentid": 0,
    "enabled": true,
    "api_timeout": 30,
    "retry_count": 3,
    "retry_delay": 1
}
```

### C. Test Checklist
- [x] WeCom credentials configured
- [x] Client connection test passed
- [x] access_token auto-refresh works
- [x] Message sending works
- [x] AI intent recognition accurate
- [x] AI smart reply works smoothly
- [x] Notification center WeCom channel enabled
- [x] Callback URL correctly configured
- [x] Contact API works
- [x] Approval function works

---

*End of Document | System Adapter v1.0.0 | 2026-07-29*
