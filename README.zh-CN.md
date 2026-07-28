# MTSCOS AI 教育平台

> **MTSCOS** = **M**ulti-Agent **T**win-Track **S**elf-evolving **C**ollaborative **O**perating **S**ystem

基于 MTS 架构 v2.0 的分布式多智能体智能教育与考试平台。统一集成 AI 自动命题、智能组卷、薄弱诊断、个性化学习路径与企业级 RBAC + ABAC 治理，覆盖 K12、成人教育与高等教育全场景。

[![版本](https://img.shields.io/badge/版本-v17.22.0-purple)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![许可证](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

> 完整文档已迁入 [`docs/`](docs/) 目录：
> - 中文主文档：[docs/README.zh-CN.md](docs/README.zh-CN.md)
> - 英文文档：[README.md](README.md) · [docs/README.md](docs/README.md)

---

## 项目亮点

| 维度 | 核心能力 |
| :--- | :--- |
| **MTS 架构 v2.0 双引擎** | 规划引擎负责策略，执行 AI 员工阵列负责落地；8 阶段配置加载 + 6 阶段模块加载 |
| **550+ AI 员工 / 引擎** | 47 个 Agent，覆盖命题、组卷、批改、诊断、学习规划、安全审计、Git 运维、DevOps、布局修复、代码修复——技能可进化、故障可自愈 |
| **87 张数据库表** | 9+ 业务域分片 SQLite 数据库（auth / exam / question / learning / user / system / admin / log / ai），透明路由、开箱零配置 |
| **教育考试系统** | 11 学科 × 7 题型 × 3 Bloom 层级，37,000+ 题目，AI 智能组卷，防作弊监考，IRT + RL 自适应学习路径 |
| **农历服务** | 内置农历日历服务（[`core/services/lunar_calendar_service.py`](core/services/lunar_calendar_service.py)），适配按学期 / 节气排课的教育场景 |
| **企业级 RBAC + ABAC** | 16 级角色、50+ 权限规则、全链路不可篡改审计、超管 VIKEY USB 硬件密钥登录 |
| **AI 防火墙与应用安全** | WAF（SQLi/XSS/RCE/SSRF/LFI/目录穿越/限流）+ CI 全矩阵 pip-audit / Trivy / Bandit / CodeQL，Dependabot 日更 |

---

## 环境要求

| 依赖 | 最低版本 | 必选/可选 |
| :--- | :---: | :---: |
| Python | **3.9+**（建议 3.10+） | 必选 |
| SQLite | 3.30+ | 必选 |
| pip | 20.0+ | 必选 |
| Git | latest | 必选 |
| Redis | 7.0+ | 可选（无则降级为内存缓存） |
| 大模型 Key | 任意 | 可选（无 Key 亦可运行非 AI 功能） |

---

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/wuchenghao15/MTSCOS-AI-Project.git
cd MTSCOS-AI-Project

# 2. 创建虚拟环境并安装依赖
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 启动生产入口
python3 server_real_db.py --host 0.0.0.0 --port 8888
```

浏览器访问 <http://localhost:8888/>。

**命令行参数：**

| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `--host` | 绑定地址 | `127.0.0.1` |
| `--port` | HTTP 端口 | `8888` |
| `--ssl` | 启用 HTTPS | `False` |
| `--ssl-port` | HTTPS 端口 | `8443` |
| `--debug` | 调试模式 | `False` |

### Docker 部署

```bash
docker build -t mtscos-ai:v17.22.0 .
docker run -d -p 8888:8888 --name mtscos-ai \
  -v $(pwd)/split_databases:/app/split_databases:rw \
  -v $(pwd)/data:/app/data:rw \
  mtscos-ai:v17.22.0
```

### 入口说明

- **生产入口**：`server_real_db.py` —— 正确启动分片数据库、版本管理器、VIKEY 驱动及解耦的启动模块。
- **预览入口**：`server_preview.py` —— 用于本地调试。
- **历史兼容入口**：`app.py` —— 保留以兼容旧代码。

---

## 演示账号

预置 10+ 角色账号，统一密码：`Test@2026`。

| 用户名 | 角色 | 权限等级 |
| :--- | :--- | :---: |
| `test_student` | 学生 | 1 |
| `test_parent` | 家长 | 1 |
| `test_designer` | 设计师 | 1 |
| `test_teacher` | 教师 | 2 |
| `test_proctor` | 监考员 | 2 |
| `test_qm` | 题库管理员 | 3 |
| `test_aim` | AI 管理员 | 3 |
| `test_cm` | 集群管理员 | 3 |
| `test_admin` | 系统管理员 | 4 |
| `test_hwadmin` | 硬件管理员 | 5 |
| `wuchenghao15` | **超级管理员** | 9 · **需 VIKEY 硬件密钥** |

---

## 文档导航

| 文档 | 用途 |
| :--- | :--- |
| [MTS 架构 v2.0 白皮书](docs/MT_ARCHITECTURE.md) | 47 个 AI Agent 双引擎流水线详解 |
| [系统完整说明书](docs/SYSTEM_DOC.md) | 系统规范、开发约束、对外能力、安全合规 |
| [部署指南](docs/DEPLOYMENT_GUIDE.md) | 生产 / Docker / K8s / TLS / 高可用 |
| [安全策略](SECURITY.md) · [docs/SECURITY.md](docs/SECURITY.md) | 漏洞上报流程、WAF 规则、CI 扫描矩阵 |
| [贡献者指南](CONTRIBUTING.md) | 代码规范、提交格式、PR 流程 |
| [项目结构详解](docs/PROJECT_STRUCTURE.md) | 完整目录树、模块归属 |
| [变更日志](CHANGELOG.md) · [docs/CHANGELOG.md](docs/CHANGELOG.md) | v1.0 至 v17.22.0 全量变更 |
| [AI 引擎架构](ai_engines/AI_ENGINE_ARCHITECTURE.md) | 550+ AI 员工 / 引擎矩阵 |

---

## 许可协议

MIT License © 2026 wuchenghao15 / MTSCOS AI —— 全文见 [`LICENSE`](LICENSE)。

- 本平台自动生成的题库内容须本着学术诚信合理使用，禁止一切作弊与违规用途。
- **非商业 / 教育场景**：免费使用，超出 MIT 的额外署名不做要求。
- **商业 / 机构客户**：请先在 GitHub Discussions 发帖沟通，或邮件 `contact@mtscos.com`。
