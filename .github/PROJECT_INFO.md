# 项目描述文件
# 用于 GitHub 项目页面展示

## 项目名称
MTSCOS AI 智能管理系统

## 项目描述
AI驱动的智能管理平台，融合机器学习、知识图谱和自动化运维技术。支持**33,525+ AI员工**协作、知识脑库自学习、仙女座 7 阶段自演化引擎、三层 AI 降级链路 (本地 14b→7b→Volcengine ARK)。覆盖 K12、高等教育、职业教育、继续教育全学段。

## 核心特性

### 🤖 AI原生运维 · 仙女座 v22.1.0 升级
- **33,525+ AI员工** (比 v21.6 增 3x) · 25 恒星 · 41 Neural Hub 路由
- **55+ AI引擎**覆盖全场景 · 17 daemon · 300+ API 路由
- 深度巡检引擎自动修复 99.8% 问题 · 自动开发团队 94.5% 完成率
- 🆕 **仙女座 7 阶段自演化引擎** (26.9s/cycle · qwen2.5:14b AI 推理衍生新知识)
- 🆕 **三层 AI 降级链路** (本地 14b → 本地 7b → Volcengine ARK 云端 · 永不宕机)
- 🆕 **macOS Metal iGPU 原生推理** (24GB 共享 · q8_0 KV cache · 零 token 本地优先)

### 🔒 安全纵深防御
- L0-L4五级加密体系
- VIKEY硬件加密狗双钥匙认证
- §14 IRON RULE 12步骤强制开发流程
- 🆕 Flask Thread patch (33 关键词拦截后台守护线程 · 纯 HTTP · 彻底解决 HTTP timeout)
- 8分片数据库系统

### 📊 数据库架构
- 双引擎架构：WAL模式 + 热切换
- 8分片横向打散：L0极密到L7分析
- **370+张数据库表** (370 全库 · flask-app/database 241 演化库 · 396MB)
- 透明加解密

### 🌐 EigenFlux 广播网络 + 仙女座自举循环 🆕
- 278,920+ 条 comm_messages · 33,525+ AI 员工
- 84 名 AI 专家加权评分共识
- 知识共享与协作 → **反向驱动仙女座 auto_derive → 脑库 +205/cycle → 下一轮 eigenflux_ingest 🌀 自举循环**

### 🎓 教育全场景
- K12教育：中小学课程管理
- 高等教育：大学课程与学术研究
- 职业教育：技能培训与证书考试
- 继续教育：在线学习与远程培训

## 技术栈

- **后端**: Flask 3.1.3+ / Python 3.9+
- **数据库**: SQLite (WAL + busy_timeout=60s) · 8 分片 (L0极密→L7分析) · 规则治理 3 表 · 仙女座演化 241 表
- **AI/ML**: Ollama 11435 (Metal iGPU · qwen2.5:14b 🥇 通用主力 · qwen2.5-coder:14b 🆕 代码主力 · nomic-embed-text 768维) + Volcengine ARK 火山方舟 云端兜底 (133 模型)
- **安全**: bcrypt / cryptography / VIKEY USB
- **前端**: HTML5 + CSS3 + JavaScript + Element Plus
- **部署**: macOS Metal iGPU 原生 · Ollama launch agent (11435 · q8_0 KV cache · 5m keep-alive) · Flask Thread patch 纯 HTTP · smart_mount_engine 独立进程管守护

## 系统规模

| 指标 | 数值 |
|------|------|
| 系统版本 | **v22.1.0** (2026-09-17 · 仙女座自演化激活) |
| 数据库表 | 352+ 张 |
| AI员工 | **33,525+ 人** |
| API路由 | 300+ 条 |
| 前端页面 | 38+ 页 |
| Python文件 | 500+ 个 |
| daemon线程 | **17 个** (含仙女座 autosync + auto_evolution) |
| 安全级别 | L0-L4 五级 |
| 数据库分片 | 8 个 |

## 主页
https://github.com/wuchenghao15/MTSCOS

## 文档
- 系统说明书: https://github.com/wuchenghao15/MTSCOS/blob/main/docs/SYSTEM_MANUAL.md
- Code Wiki: https://github.com/wuchenghao15/MTSCOS/tree/main/docs/code-wiki
- API文档: https://github.com/wuchenghao15/MTSCOS/wiki

## 话题标签
ai machine-learning deep-learning flask python web-app rest-api education edtech k12 learning-management-system automation devops monitoring intelligent-systems knowledge-graph self-hosted open-source mit-license backend full-stack online-learning exam-system multi-agent distributed-systems security encryption database-sharding

## 许可协议
MIT License © 2026 wuchenghao15 / MTSCOS AI

## 联系方式
- GitHub: https://github.com/wuchenghao15
- Email: contact@mtscos.com
