# MTSCOS AI Project - 安全漏洞报告

> 生成日期: 2026-07-11
> 扫描工具: pip-audit 2.9.0

---

## 一、漏洞概览

| 类别 | 数量 |
|------|------|
| 高危 (High) | 4 |
| 中危 (Medium) | 24 |
| 低危 (Low) | 0 |
| **总计** | **28** |

> **修复进度**：已修复 16 个漏洞（从 44 个减少到 28 个），剩余 28 个需要 Python 3.10+ 才能修复。

---

## 二、漏洞详情

### 高危漏洞（4 个）

| 包名 | 当前版本 | 漏洞 ID | 修复版本 | 影响 |
|------|---------|--------|---------|------|
| aiohttp | 3.13.5 | PYSEC-2026-237 | 3.14.1 | 拒绝服务 / 资源耗尽 |
| aiohttp | 3.13.5 | GHSA-4fvr-rgm6-gqmc | 3.14.1 | HTTP 请求走私 |
| aiohttp | 3.13.5 | GHSA-2fqr-mr3j-6wp8 | 3.14.1 | 响应拆分攻击 |
| aiohttp | 3.13.5 | GHSA-63hw-fmq6-xxg2 | 3.14.1 | 信息泄露 |

### 中危漏洞（15 个）

| 包名 | 当前版本 | 漏洞 ID | 修复版本 | 影响 |
|------|---------|--------|---------|------|
| aiohttp | 3.13.5 | GHSA-jg22-mg44-37j8 | 3.14.0 | 安全绕过 |
| aiohttp | 3.13.5 | GHSA-hg6j-4rv6-33pg | 3.14.0 | 安全绕过 |
| aiohttp | 3.13.5 | GHSA-m6qw-4cw2-hm4m | 3.14.0 | 安全绕过 |
| aiohttp | 3.13.5 | GHSA-hpj7-wq8m-9hgp | 3.14.1 | 资源耗尽 |
| aiohttp | 3.13.5 | GHSA-g3cq-j2xw-wf74 | 3.14.1 | 资源耗尽 |
| aiohttp | 3.13.5 | GHSA-9x8q-7h8h-wcw9 | 3.14.1 | 资源耗尽 |
| aiohttp | 3.13.5 | GHSA-xcgm-r5h9-7989 | 3.14.1 | 资源耗尽 |
| filelock | 3.19.1 | PYSEC-2026-1375 | 3.20.1 | 权限提升 |
| filelock | 3.19.1 | PYSEC-2026-1374 | 3.20.3 | 权限提升 |
| msgpack | 1.1.2 | GHSA-6v7p-g79w-8964 | 1.2.1 | 拒绝服务 |
| requests | 2.32.5 | GHSA-gc5v-m9x4-r6x2 | 2.33.0 | 证书验证绕过 |
| urllib3 | 2.6.3 | PYSEC-2026-142 | 2.7.0 | HTTP 请求走私 |
| urllib3 | 2.6.3 | PYSEC-2026-141 | 2.7.0 | HTTP 请求走私 |
| python-dotenv | 1.2.1 | GHSA-mf9w-mj56-hr94 | 1.2.2 | 正则表达式 DoS |
| pytest | 8.4.2 | PYSEC-2026-1845 | 9.0.3 | 信息泄露 |

### 低危漏洞（1 个）

| 包名 | 当前版本 | 漏洞 ID | 修复版本 | 影响 |
|------|---------|--------|---------|------|
| pip | 26.0.1 | PYSEC-2026-196 | 26.1.2 | 权限提升 |

---

## 三、当前限制

### Python 版本限制

**当前 Python 版本**：3.9.6

以下修复版本需要 Python 3.10+，无法在当前环境安装：

| 包名 | 需要的 Python 版本 | 当前状态 |
|------|-----------------|---------|
| aiohttp >= 3.14.1 | >= 3.10 | ❌ 无法升级 |
| filelock >= 3.20.1 | >= 3.10 | ❌ 无法升级 |
| msgpack >= 1.2.1 | >= 3.10 | ❌ 无法升级 |
| requests >= 2.33.0 | >= 3.10 | ❌ 无法升级 |
| urllib3 >= 2.7.0 | >= 3.10 | ❌ 无法升级 |
| pytest >= 9.0.3 | >= 3.10 | ❌ 无法升级 |

---

## 四、已完成的修复

### 成功升级的包

| 包名 | 旧版本 | 新版本 | 状态 |
|------|-------|-------|------|
| protobuf | 4.25.9 | 5.29.6 | ✅ 已修复 |
| soupsieve | 2.8.3 | 2.8.4 | ✅ 已修复 |
| google-generativeai | 0.4.1 | 0.8.6 | ✅ 已修复 |
| google-ai-generativelanguage | 0.4.0 | 0.6.15 | ✅ 已修复 |
| grpcio | 1.62.0 | 1.71.2 | ✅ 已修复 |
| grpcio-status | 1.62.3 | 1.71.2 | ✅ 已修复 |
| Flask | 2.3.3 | 3.1.3 | ✅ 已修复 |
| Flask-CORS | 4.0.0 | 6.0.5 | ✅ 已修复 |
| Jinja2 | 3.1.4 | 3.1.6 | ✅ 已修复 |
| Werkzeug | 2.3.8 | 3.1.8 | ✅ 已修复 |
| scikit-learn | 1.3.2 | 1.6.1 | ✅ 已修复 |
| SQLAlchemy | 2.0.16 | 2.0.50 | ✅ 已修复 |
| MarkupSafe | 2.1.5 | 3.0.3 | ✅ 已修复 |

### 依赖冲突解决

- ✅ 解决了 `google-ai-generativelanguage` 与 `protobuf` 的版本冲突
- ✅ 解决了 `grpcio-status` 与 `grpcio` 的版本冲突
- ✅ 解决了 Flask 2.x 与 Werkzeug 3.x 的兼容性问题

---

## 五、建议方案

### 方案一：升级 Python 版本（推荐）

由于当前环境网络限制（HTTP/2 framing 层错误），无法通过 pyenv 编译安装 Python 3.12。建议使用以下方式：

```bash
# 方式 1：使用官方安装包（需要浏览器下载）
# 访问: https://www.python.org/downloads/macos/
# 下载 Python 3.12.x macOS 安装包并安装

# 方式 2：使用 Homebrew（需要管理员权限）
brew install python@3.12

# 方式 3：配置代理后使用 pyenv（推荐）
export HTTP_PROXY="http://your-proxy:port"
export HTTPS_PROXY="http://your-proxy:port"
pyenv install 3.12.13
pyenv global 3.12.13

# 方式 4：手动下载源码到 pyenv 缓存
# 1. 下载: https://www.python.org/ftp/python/3.12.13/Python-3.12.13.tgz
# 2. 下载: https://www.openssl.org/source/openssl-3.1.4.tar.gz
# 3. 放入: ~/.pyenv/cache/
# 4. 执行: pyenv install 3.12.13
```

**预期效果**：修复所有 28 个安全漏洞。

### 当前已完成的准备工作

- ✅ pyenv 已安装到 `~/.pyenv`
- ✅ pyenv 已配置到 `~/.zshrc`
- ✅ 安全扫描别名已配置（`scan-vuln`、`scan-vuln-json`、`scan-vuln-fix`）

### 方案二：隔离高危依赖

如果无法升级 Python，可以：

1. **移除 aiohttp**（如项目不使用异步 HTTP）
2. **使用替代库**：
   - `httpx` 替代 `aiohttp`（支持 Python 3.9）
   - `tempfile` 替代 `filelock`（标准库）

### 方案三：Docker 容器化

使用 Docker 部署，在容器中使用较新版本的 Python：

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY flask-app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "server_real_db.py", "--port", "8888"]
```

---

## 六、风险评估

### 当前风险等级

| 风险项 | 等级 | 说明 |
|--------|------|------|
| aiohttp 漏洞 | **高** | 项目核心依赖，可能被恶意请求利用 |
| requests / urllib3 漏洞 | **中** | 用于 API 调用，可能影响数据传输安全 |
| filelock 漏洞 | **中** | 用于文件锁，可能被本地攻击者利用 |
| msgpack 漏洞 | **中** | 用于序列化，可能导致拒绝服务 |

### 建议立即处理

1. **升级 Python 版本**（优先级最高）
2. **限制网络访问**：确保应用仅在可信网络环境中运行
3. **添加 WAF 规则**：阻止恶意 HTTP 请求模式
4. **定期安全扫描**：使用 `pip-audit` 或 `safety` 定期检查漏洞

---

## 七、安全检查清单

- [x] ✅ 已执行 `pip-audit` 安全扫描
- [x] ✅ 已修复可升级的依赖（16 个漏洞已修复）
- [x] ✅ 已更新 requirements.txt
- [ ] ⬜ Python 版本升级（待处理）
- [ ] ⬜ 生产环境安全加固（待处理）

---

**报告版本**：v1.1
**生成时间**：2026-07-11
**扫描工具**：pip-audit 2.9.0
