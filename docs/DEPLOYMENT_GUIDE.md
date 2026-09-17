# MTSCOS AI 部署指南 v22.1.0 · macOS Metal iGPU 原生部署

> **文档版本**: 22.1.0 | **更新日期**: 2026-09-17
> **目标平台**: macOS (Mac mini M4/M5 或 Apple Silicon 系列)
> **启动方式**: launch agent (开机自启) + 手动 CLI
> **Ollama 实例**: launch agent `com.mtscos.ollama-native` (端口 11435) · 零手动干预

---

## 1️⃣ 架构总览

```
┌──────────────────────────────────────────────────────────────────┐
│                     macOS Metal iGPU 24GB                         │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Ollama 11435 (launch agent · com.mtscos.ollama-native)   │     │
│  │   q8_0 KV cache · 5m keep-alive · Metal iGPU 推理        │     │
│  │                                                         │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │     │
│  │  │ qwen2.5:14b  │  │ qwen2.5-coder │  │ nomic-embed  │  │     │
│  │  │ 通用主力 🥇    │  │ :14b 代码 🆕  │  │ -text 向量  │  │     │
│  │  │ 8.4GB        │  │ 8.4GB         │  │ 0.3GB 0.3s  │  │     │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │     │
│  │         │ 自动 LRU 淘汰 ──┘                  │         │     │
│  │  qwen2.5:7b 🥈 兜底 · qwen2.5-coder:7b 代码兜底 │        │     │
│  └─────────────────────────────────────────────────────────┘     │
│                           │ HTTP :11435                           │
│                           ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ Flask :8888 (modular_start.py · 纯 HTTP server)          │     │
│  │                                                         │     │
│  │  Thread.__init__ patch (33 关键词拦截后台线程)            │     │
│  │  → Flask 不再启动守护线程 · 彻底解决 HTTP timeout         │     │
│  │                                                         │     │
│  │  db_path.py patch_sqlite3_connect                       │     │
│  │  → WAL + busy_timeout=60s + synchronous=NORMAL          │     │
│  │  → 候选目录首位 flask-app/database (396MB 真主库)        │     │
│  │                                                         │     │
│  │  核心路由 300+ · Neural Hub 41 路由 · 25 域              │     │
│  │  Ollama 直推理 · Volcengine ARK 🛡️ 云端兜底              │     │
│  └─────────────────────────────────────────────────────────┘     │
│                           │                                       │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ 守护进程 (由 smart_mount_engine 独立进程管理)              │     │
│  │  17 daemon: heartbeat / patrol / eigenflux_network /     │     │
│  │  auto_repair / local_inference / rule_enforcer / ...      │     │
│  │  🆕 sys_andromeda_autosync + sys_andromeda_auto_evolution│     │
│  └─────────────────────────────────────────────────────────┘     │
│                           │                                       │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │ 云端 Volcengine ARK (仅兜底 · 本地全挂时激活)               │     │
│  │  133 模型 · doubao-seed-2-0-lite 默认兜底 (3.6s)          │     │
│  │  _runtime/config/ai_secrets.json (gitignore)             │     │
│  └─────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
```

**启动时序（v22.1.0）**：
```
用户登录 macOS
  │
  ├─ launch agent: com.mtscos.ollama-native (RunAtLoad=true)
  │   → 加载 5 模型到 Metal iGPU
  │
  ├─ 手动启动: cd flask-app && python3 modular_start.py
  │   │
  │   ├─ patch_sqlite3_connect → WAL + busy_timeout + db_path 修正
  │   ├─ patch Thread.__init__ → 33 关键词拦截后台线程
  │   ├─ import server_real_db → 模块级单例同步初始化 (持锁建表)
  │   ├─ sleep(5) → 让建表事务 commit
  │   ├─ app.run() → listen :8888 纯 HTTP
  │   └─ 守护线程由 smart_mount_engine 独立进程管理
  │
  └─ autosync daemon (Mac mini ↔ 开发机)
      → Phase A mini→dev → Phase B dev→mini
      → trigger_evolution() → 仙女座 7 阶段演化
      → 产出反向驱动 eigenflux → 自举循环 🌀
```

---

## 2️⃣ 首次部署（Mac mini 新机）

### 2.1 预装检查

```bash
# Python
which python3                                    # 需 3.9+

# Ollama
ollama --version                                 # 需 0.4+

# Metal iGPU
system_profiler SPDisplaysDataType | grep Metal  # 需支持 Metal
```

### 2.2 下载模型（~26GB）

```bash
ollama pull qwen2.5:14b
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:14b
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text

# 验证
ollama list
# 应输出 5 模型 · 共 ~25.7GB
```

### 2.3 配置 Ollama launch agent（Metal iGPU 优化）

```bash
# 创建 launch agent
cat > ~/Library/LaunchAgents/com.mtscos.ollama-native.plist << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.mtscos.ollama-native</string>
    <key>ProgramArguments</key>
    <array><string>/usr/local/bin/ollama</string><string>serve</string><string>--host</string><string>127.0.0.1:11435</string></array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>OLLAMA_KEEP_ALIVE</key><string>5m</string>
        <key>OLLAMA_NUM_GPU</key><string>999</string>
    </dict>
</dict>
</plist>

launchctl load ~/Library/LaunchAgents/com.mtscos.ollama-native.plist
sleep 3

# 验证端口
curl -s http://localhost:11435/api/tags | python3 -m json.tool | grep name
```

### 2.4 拉取项目

```bash
cd ~/Documents
git clone <your-repo-url> MTSCOS_AI_Project
cd MTSCOS_AI_Project/flask-app

# 安装依赖 (系统 Python 3.9 或更高)
pip3 install -r requirements.txt
```

### 2.5 （可选）Mac mini 端配 autosync

autosync 需要开发机的 SSH 访问权限和双向同步配置。详见 `autosync_andromeda.py` 源码注释。

---

## 3️⃣ 日常启动 / 停止

### 3.1 完整启动

```bash
cd ~/Documents/MTSCOS_AI_Project/flask-app

# 1) 确认 Ollama 活着
curl -s http://localhost:11435/api/tags > /dev/null && echo "Ollama OK" || echo "Ollama DOWN"

# 2) 清干净旧进程 + WAL reset
pkill -f "modular_start|smart_mount" 2>/dev/null || true
find . -name "*.db-wal" -o -name "*.db-shm" | xargs rm -f 2>/dev/null || true

# 3) 启动 Flask + smart_mount
PYTHON="/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3"
nohup $PYTHON -u modular_start.py >> /tmp/flask_solo.log 2>&1 &

sleep 6
curl -s --max-time 5 http://127.0.0.1:8888/api/autosync/health | head -c 200
# 应返回 {"status":"ok",...}
```

### 3.2 停止

```bash
pkill -f "modular_start.py"        # Flask
pkill -f "ai_smart_mount_engine"    # smart_mount
launchctl stop com.mtscos.ollama-native  # Ollama (通常不关)
```

### 3.3 一键脚本（推荐）

项目根 `_entry_wrappers/mtscos.py` 提供了统一启动器：

```bash
python3 mtscos.py start     # 启动全套
python3 mtscos.py health    # 健康检查 (Flask + Ollama + daemon)
python3 mtscos.py stop      # 停止
python3 mtscos.py restart   # 重启
```

---

## 4️⃣ 健康检查清单

```bash
# ① Flask HTTP
curl -s --max-time 5 http://127.0.0.1:8888/api/autosync/health

# ② Ollama 11435 (直推理)
curl -s http://localhost:11435/api/tags | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f'  {m["name"]}') for m in d['models']]"

# ③ 真实 AI 推理测试
python3 -c "
import sys; sys.path.insert(0,'flask-app')
from engines.andromeda_auto_evolution import _ollama_chat, DERIVE_MODEL
r = _ollama_chat('说一个字: OK')
print(f'{DERIVE_MODEL}: {r!r}')
"

# ④ 守护进程
pgrep -fa "smart_mount|andromeda|autosync"

# ⑤ DB 状态
python3 -c "
import sqlite3
c = sqlite3.connect('flask-app/database/app.db', timeout=3)
print('WAL:', c.execute('PRAGMA journal_mode').fetchone()[0])
print('busy_timeout:', c.execute('PRAGMA busy_timeout').fetchone()[0])
print('tables:', c.execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table"').fetchone()[0])
c.close()
"
```

---

## 5️⃣ 三层 AI 降级链路（永不宕机）

```
请求进来
  │
  ├─ qwen2.5:14b / qwen2.5-coder:14b  🥇 主力
  │   │
  │   ├─ 成功 → 返回 (零 token, 2.2s/字)
  │   └─ 失败 (OOM/超时/404) → 自动降级
  │
  ├─ qwen2.5:7b / qwen2.5-coder:7b   🥈 本地兜底
  │   │
  │   ├─ 成功 → 返回 (零 token, 1.5s/字, fallback_note 标注)
  │   └─ 失败 → 自动降级
  │
  └─ Volcengine ARK 🛡️ 云端兜底
      │
      ├─ 默认: doubao-seed-2-0-lite (3.6s · 消耗少量 token)
      ├─ deepseek-v4-pro (数学/逻辑)
      ├─ doubao-1-5-pro-256k (长上下文, 需 endpoint)
      └─ doubao-1-5-thinking-pro (深度思考, 需 endpoint)

配置来源: _runtime/config/ai_secrets.json (gitignore, 不入库)
         API key: ark-xxx 格式
```

---

## 6️⃣ 仙女座演化状态确认

```bash
# 演化循环是否跑过 (查 mt_ai_self_evolution_log)
python3 -c "
import sqlite3
c = sqlite3.connect('flask-app/database/app.db', timeout=5)
rows = c.execute('SELECT trigger_type, target_task, triggered_at FROM mt_ai_self_evolution_log ORDER BY rowid DESC LIMIT 5').fetchall()
for t, task, at in rows:
    print(f'{at} {t:20s} {task}')
c.close()
"

# 脑库 AI 衍生产出 (Stage 4 auto_derive 的真实产出)
python3 -c "
import sqlite3
c = sqlite3.connect('flask-app/database/app.db', timeout=5)
print('auto_derive 产出样例:')
for r in c.execute("""
    SELECT knowledge_id, title, confidence_score 
    FROM ai_brain_enhanced_knowledge 
    WHERE category='auto_derive' 
    ORDER BY rowid DESC LIMIT 5
""").fetchall():
    print(f'  {r[0][:12]} conf={r[2]} {r[1]!r}')
c.close()
"

# 手动触发一次演化 cycle
python3 flask-app/engines/andromeda_auto_evolution.py --cycle
# 26.9s 完整 7 阶段
```

---

## 7️⃣ 端口 / 路径 / 依赖速查

| 项 | 值 | 来源 |
|----|-----|------|
| Flask HTTP | `:8888` | `modular_start.py` |
| Ollama (业务层) | `localhost:11435` | `launch agent com.mtscos.ollama-native` |
| Ollama (CLI 实例) | `localhost:11434` | `ollama serve` (备用, 业务层不直连) |
| DB 主库 | `flask-app/database/app.db` (396MB, 241 表) | `db_path.py` + patch_sqlite3_connect |
| autosync checkpoint | `~/Library/Application Support/MTSCOS AI/autosync_checkpoint.json` | OneDrive 云盘冲突规避 |
| 守护进程管理 | `smart_mount_engine` 独立进程 | 17 daemon (含仙女座 2) |
| Python | `/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3` | 系统 Python 3.9 |

---

## 8️⃣ 已知限制

| 限制 | 原因 | 规避 |
|------|------|------|
| doubao-1-5-pro/thinking/vision 需 endpoint_id | 火山引擎账号未创建 endpoint | 自动降级 doubao-seed-lite；需 endpoint 时去方舟控制台创建 |
| coder:14b + qwen2.5:14b 不同驻留 | Metal iGPU 24GB · MAX_LOADED_MODELS=1 | Ollama 自动 LRU 淘汰，冷切换 ~2s |
| Flask 是纯 HTTP (无守护线程) | Thread.__init__ patch 拦截 33 关键词 | 守护任务必须由 smart_mount_engine 独立进程启动 |
| OneDrive 下 autosync 冲突 | 云盘双向同步 | checkpoint 挪本地路径 |

---

## 📚 相关文档

- `docs/SYSTEM.md` — 系统说明书 (v22.1.0)
- `docs/MT_ARCHITECTURE.md` — 架构白皮书 (v22.1.0)
- `README.md` — 项目总入口
- `CHANGELOG.md` — 版本变更日志 (v22.1.0 仙女座自举循环激活)
- `.trae/skills/local-ai-cli/SKILL.md` — 本地 AI CLI 操作手册
- `.trae/rules/00-规则总索引.md` — 12 篇规则总索引

---

> **v22.1.0 部署要点**：Ollama 11435 Metal iGPU launch agent · Flask Thread patch · db_path 重定向 + WAL 强制 · 三层 AI 降级链路 · 仙女座 7 阶段演化已验证跑通 · autosync checkpoint 本地化。
