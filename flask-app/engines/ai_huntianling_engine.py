#!/usr/bin/env python3
"""
🌀 混天绫 (HUNTIANLING) — 仙女座 API 网关层
==========================================

仙女座 25 域星中的【中枢域】专属子系统.
统一 API 网关 · RESTful 设计 · OpenAPI 规范 · Mock 数据 · 限流 · 鉴权.
本地 Ollama 推理生成 JSON 规范, 零 token 消耗 · 7 种 API 模式.

┌──────────────────────────────────────────────────────────┐
│   🌀 design  API 设计     (RESTful, 路径/方法/参数/响应)    │
│   📋 spec    OpenAPI 规范  (生成 JSON OpenAPI 3.0 spec)   │
│   🎭 mock    Mock 数据    (生成假数据 JSON)                │
│   🧪 test    测试用例     (生成 pytest 风格 API 测试)       │
│   📖 doc     文档生成     (生成 API 文档 Markdown)          │
│   ⏱️ rate    限流策略     (QPS/令牌桶/漏桶配置)             │
│   🔐 auth    鉴权方案     (JWT/OAuth2/API Key)             │
└──────────────────────────────────────────────────────────┘

AI 员工: 架构师(L9 API 设计) · 文档(L8 文档) · 安全(L7 鉴权)
"""

from __future__ import annotations
import json, os, sys, time, uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class HuntianlingEngine(BaseAndromedaSubsystem):
    """🌀 混天绫 — 仙女座 API 网关层"""

    SUBSYSTEM_NAME = "混天绫"
    SUBSYSTEM_ICON = "🌀"
    SUBSYSTEM_DESC = "API 网关 · RESTful 设计 · OpenAPI 规范 · Mock · 限流 · 鉴权"
    DB_TABLE = "mt_huntianling_calls"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS mt_huntianling_routes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id        TEXT UNIQUE,
    path            TEXT NOT NULL,
    http_method     TEXT NOT NULL,
    handler         TEXT,
    auth_required   INTEGER DEFAULT 0,
    rate_limit_qps  INTEGER DEFAULT 100,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS mt_huntianling_calls (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT,
    mode            TEXT NOT NULL,
    endpoint        TEXT,
    http_method     TEXT DEFAULT 'GET',
    request_json    TEXT,
    response_json   TEXT,
    status_code     INTEGER DEFAULT 0,
    latency_ms      INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_htl_calls_mode  ON mt_huntianling_calls(mode);
CREATE INDEX IF NOT EXISTS idx_htl_routes_path ON mt_huntianling_routes(path);
"""
    ARTIFACT_DIR = "huntianling_artifacts"
    ARTIFACT_EXT = "json"
    PREFERRED_MODELS = ["qwen2.5:14b-q5", "qwen2.5:14b"]
    DAEMON_NAME = "sys_huntianling"
    DAEMON_DUTY = "🌀 混天绫 API 网关层"

    AI_EMPLOYEES = [
        ("htl_arch",    "架构师", "api_architect",  9, "API 架构师. RESTful/GraphQL/gRPC 设计. 接口规范最佳实践."),
        ("htl_doc",     "文档",   "api_docs",       8, "API 文档工程师. OpenAPI/Swagger. 清晰的参数/响应/错误码."),
        ("htl_security","安全",   "api_security",   7, "API 安全专家. JWT/OAuth2/API Key. 限流/防刷/审计."),
    ]

    # ── 7 种 API 模式 ────────────────────────────────────
    MODES = {
        "design": {
            "name": "API 设计", "icon": "🌀",
            "desc": "RESTful, 路径/方法/参数/响应",
            "prompt": lambda t: f"""# 混天绫 · API 设计 (design)

## 需求
{t}

## 输出 JSON
```json
{{
  "endpoint": "/api/v1/资源名",
  "method": "GET|POST|PUT|DELETE",
  "description": "接口说明",
  "request": {{
    "path_params":   {{"name": "type", "required": true, "desc": "..."}},
    "query_params":  {{...}},
    "body_schema":   {{...}}
  }},
  "response": {{
    "success":  {{"code": 200, "data": {{...}}, "message": "ok"}},
    "errors": [
      {{"code": 400, "message": "参数错误"}},
      {{"code": 404, "message": "资源不存在"}}
    ]
  }},
  "auth_required": true,
  "rate_limit": "100 QPS"
}}
```
"""
        },
        "spec": {
            "name": "OpenAPI 规范", "icon": "📋",
            "desc": "生成 JSON OpenAPI 3.0 spec",
            "prompt": lambda t: f"""# 混天绫 · OpenAPI 规范 (spec)

## 需求
{t}

## 输出完整 OpenAPI 3.0 JSON
以标准 `openapi: 3.0.3` 开头, 包含 info/servers/paths/components.
生成一个可直接导入 Swagger UI 的完整 spec.
"""
        },
        "mock": {
            "name": "Mock 数据", "icon": "🎭",
            "desc": "生成假数据 JSON",
            "prompt": lambda t: f"""# 混天绫 · Mock 数据 (mock)

## 需求
{t}

## 输出 JSON
生成符合该 API 响应结构的 3-5 条真实感假数据.
要求:
- 字段类型正确 (string/number/boolean/array/object)
- 日期用 ISO8601
- ID 用 uuid 风格
- 中文数据, 有真实感 (姓名/地址/手机等)
"""
        },
        "test": {
            "name": "测试用例", "icon": "🧪",
            "desc": "生成 pytest 风格 API 测试",
            "prompt": lambda t: f"""# 混天绫 · 测试用例 (test)

## 需求
{t}

## 输出 Python pytest 代码
生成完整的测试文件:
```python
import pytest, requests

BASE_URL = "http://localhost:5000"

class TestResourceName:
    def test_list_success(self):
        ...
    def test_create_validation_error(self):
        ...
    def test_unauthorized(self):
        ...
    def test_rate_limit(self):
        ...
```
至少覆盖: 成功/参数错误/未授权/404/边界值.
"""
        },
        "doc": {
            "name": "文档生成", "icon": "📖",
            "desc": "生成 API 文档 Markdown",
            "prompt": lambda t: f"""# 混天绫 · 文档生成 (doc)

## 需求
{t}

## 输出 Markdown API 文档
```markdown
# API 名称

## 概述
...

## 端点列表
| 方法 | 路径 | 说明 |
|------|------|------|

## 详细端点

### GET /api/v1/xxx
- **描述**: ...
- **认证**: Bearer Token
- **请求参数**: ...
- **成功响应**: ...
- **错误码**: ...
- **示例**: curl / Python / JavaScript
```
"""
        },
        "rate": {
            "name": "限流策略", "icon": "⏱️",
            "desc": "QPS/令牌桶/漏桶配置",
            "prompt": lambda t: f"""# 混天绫 · 限流策略 (rate)

## 需求
{t}

## 输出 JSON
```json
{{
  "strategy": "token_bucket|leaky_bucket|fixed_window",
  "global_qps": 1000,
  "per_user_qps": 100,
  "per_ip_qps": 50,
  "burst_size": 200,
  "window_size_sec": 60,
  "retry_after_header": true,
  "custom_rules": [
    {{"path": "/api/v1/upload", "max_qps": 10}},
    {{"path": "/api/v1/search",  "max_qps": 200}}
  ]
}}
```
"""
        },
        "auth": {
            "name": "鉴权方案", "icon": "🔐",
            "desc": "JWT/OAuth2/API Key",
            "prompt": lambda t: f"""# 混天绫 · 鉴权方案 (auth)

## 需求
{t}

## 输出 JSON
```json
{{
  "scheme": "JWT|OAuth2|APIKey|Session",
  "jwt_config": {{
    "algorithm": "RS256",
    "issuer": "mtscos",
    "audience": "api.mtscos.cn",
    "access_token_ttl_sec": 3600,
    "refresh_token_ttl_sec": 604800
  }},
  "oauth2_flows": ["authorization_code", "client_credentials", "refresh_token"],
  "api_key_header": "X-API-Key",
  "roles": ["admin", "user", "guest"],
  "permission_model": "RBAC with resource-level ACL",
  "endpoints": {{
    "login":     "/api/v1/auth/login",
    "refresh":   "/api/v1/auth/refresh",
    "register":  "/api/v1/auth/register",
    "introspect":"/api/v1/auth/introspect"
  }}
}}
```
"""
        },
    }

    # ────────────────────────────────────────────────────────
    # 提取第一个 JSON 块
    # ────────────────────────────────────────────────────────
    @staticmethod
    def _extract_first_json(text: str) -> dict | None:
        import re
        # 先找 ```json ... ``` 块
        blocks = re.findall(r'```json\s*(.*?)```', text, re.DOTALL)
        for b in blocks:
            try: return json.loads(b)
            except Exception: pass
        # 再找第一个 { ... }
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try: return json.loads(text[start:end+1])
            except Exception: pass
        return None

    # ═══════════════════════════════════════════════════════
    def write(self, mode: str, topic: str, endpoint: str = "",
              http_method: str = "GET", **kwargs) -> str:
        """混天绫生成入口"""
        m = self.MODES.get(mode)
        if not m:
            print(f"[{self.SUBSYSTEM_ICON}] ❌ 未知模式 {mode}, 可用: {list(self.MODES.keys())}")
            return ""

        task_id = self.new_task_id("htl")
        start = time.time()

        print(f"\n{'═'*56}")
        print(f"{self.SUBSYSTEM_ICON} 混天绫 · {m['icon']} {m['name']}")
        print(f"   task_id: {task_id}")
        print(f"   需求: {topic[:50]}")
        print(f"   端点: {endpoint or '/api/v1/...'} [{http_method}]")
        print(f"{'═'*56}")

        self.db_insert_task(task_id, mode=mode, endpoint=endpoint,
            http_method=http_method, status_code=0, latency_ms=0)

        try:
            prompt = m["prompt"](topic)
            print(f"  ⏳ Ollama 生成 API 规范中...")
            t0 = time.time()
            draft = self.ollama_generate(prompt, max_tokens=2048)
            latency = int((time.time() - t0) * 1000)
            duration = int(time.time() - start)

            # 尝试解析 JSON
            parsed = self._extract_first_json(draft)
            artifact_content = json.dumps(parsed, ensure_ascii=False, indent=2) if parsed else draft

            # 保存 artifact
            art_path = self.artifact_path / f"{task_id}.{self.ARTIFACT_EXT}"
            art_path.write_text(artifact_content, encoding="utf-8")

            # 同时保存 Markdown 说明
            md_path = self.artifact_path / f"{task_id}_README.md"
            md_path.write_text(
                f"# 混天绫 · {m['icon']} {m['name']}\n\n"
                f"> task_id: {task_id}\n> 模式: {mode}\n> 端点: {endpoint or 'N/A'}\n"
                f"> 方法: {http_method}\n> 耗时: {duration}s\n\n"
                f"## 原始输出\n\n```\n{draft[:3000]}\n```\n", encoding="utf-8")

            self.db.execute(
                "UPDATE mt_huntianling_calls SET response_json=?, status_code=200, "
                "latency_ms=? WHERE task_id=?",
                (artifact_content[:5000], latency, task_id))
            self.db.commit()

            print(f"  ✅ 完成: {duration}s · 解析={'✅' if parsed else '⚠️ 纯文本'}")
            print(f"  📄 Artifact: {art_path}")
            if parsed:
                print(f"  📊 JSON keys: {list(parsed.keys())[:6]}")

        except Exception as e:
            self.db.execute(
                "UPDATE mt_huntianling_calls SET status_code=500, response_json=? WHERE task_id=?",
                (str(e)[:500], task_id))
            self.db.commit()
            print(f"  💥 失败: {e}")
            raise

        return task_id


def _SELF_TEST():
    print("\n" + "=" * 56)
    print("🌀 混天绫 (HUNTIANLING) — 自检测")
    print("=" * 56)
    try:
        e = HuntianlingEngine()
        print(f"  ✅ 引擎实例化成功")
        print(f"  ✅ DB_TABLE: {e.DB_TABLE}")
        print(f"  ✅ MODES: {list(e.MODES.keys())}")
        print(f"  ✅ AI_EMPLOYEES: {len(e.AI_EMPLOYEES)} 位")
        e.register_daemon()
        e.register_ai_employees()
        print(f"  ✅ _SELF_TEST PASSED\n")
        return True
    except Exception as ex:
        print(f"  ❌ _SELF_TEST FAILED: {ex}\n")
        return False


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="🌀 混天绫 · 仙女座 API 网关层")
    ap.add_argument("mode", nargs="?", default="design",
                    help="模式: design/spec/mock/test/doc/rate/auth")
    ap.add_argument("topic", nargs="?", help="API 需求描述")
    ap.add_argument("--endpoint", "-e", default="", help="目标端点")
    ap.add_argument("--method", "-m", default="GET", help="HTTP 方法")
    ap.add_argument("--modes", action="store_true", help="列出模式")
    ap.add_argument("--list", "-l", type=int, const=10, nargs="?", help="最近 N 个 task")
    ap.add_argument("--self-test", action="store_true", help="自检测")
    args = ap.parse_args()

    if args.self_test:
        _SELF_TEST()
    else:
        eng = HuntianlingEngine()
        if args.modes:
            print("🌀 混天绫 · 7 种 API 模式:")
            for k, v in eng.MODES.items():
                print(f"  {v['icon']} {k:8s} → {v['name']:12s} · {v['desc']}")
        elif args.list:
            tasks = eng.db.execute(
                "SELECT * FROM mt_huntianling_calls ORDER BY id DESC LIMIT ?",
                (args.list,)).fetchall()
            cols = [c[1] for c in eng.db.execute(
                "PRAGMA table_info(mt_huntianling_calls)").fetchall()]
            for t in tasks:
                d = dict(zip(cols, t))
                print(f"  {d.get('task_id','?')}  [{d.get('mode','?'):8s}] "
                      f"{d.get('status_code','?')}  {d.get('endpoint','')[:40]}")
        elif args.topic:
            task_id = eng.write(args.mode, args.topic, args.endpoint, args.method)
            print(f"\n🎯 task_id={task_id}")
        else:
            ap.print_help()
