#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仙女座 Skill 自动衍生引擎 · sys_auto_skill_deriver
====================================================
§14 flow_id: auto_skill_deriver_v1_20260922
周期: 60min
触发源: mt_iron_rule_violations + Flask log + mt_dev_flow_events

工作流:
  1. 扫描 → 三个数据源 + 关键词聚类
  2. 提炼 → local_ai_chat 生成 SKILL.md
  3. 写入 → .trae/skills/<skill-name>/SKILL.md
  4. 验证 → frontmatter + name + description + 结构完整
  5. 落库 → mt_andromeda_skill_derivation_log

不违反 §14 meta-recursion:
  引擎自身 flow_id 已在 mt_dev_flow_session 中 (STEP_6_AI_TEAM_COORD)
  写入 Skill 是业务产出, 不属于开发活动定义中的 "代码/DB/配置变更"
"""
import os, sys, json, re, time, sqlite3, hashlib, subprocess

# ====== 路径常量 ======
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "engines", "app.db")
SKILLS_DIR = os.path.join(os.path.dirname(PROJECT_ROOT), ".trae", "skills")  # 项目根 .trae/skills
# 修正: PROJECT_ROOT 已经是 flask-app, 上级才是项目根
PROJECT_PARENT = os.path.dirname(PROJECT_ROOT)
SKILLS_DIR = os.path.join(PROJECT_PARENT, ".trae", "skills")
FLASK_LOG = "/tmp/mtscos_8888.log"
FLOW_ID = "auto_skill_deriver_v1_20260922"
DERIVER_LOG = os.path.join(DB_PATH + "..", "..", "skill_derivation.log")

# ====== 数据源定义 ======
KEYWORD_CLUSTERS = {
    "flask-blueprint-path": [
        "blueprint", "url_prefix", "route.*path", "404.*api", "路径陷阱", "prefix.*conflict",
        "andromeda/api", "api/andromeda", "route.*suffix",
    ],
    "flask-auth-deadlock": [
        "auth_routes.*login", "require_auth.*login", "system_container.*login",
        "authbp.*login", "endpoint.*login", "view_functions.*覆盖",
    ],
    "flask-sqlite-column": [
        "no such column", "column.*missing", "password_hash", "password.*column",
        "col_candidates", "schema.*drift", "多.*DB.*列",
    ],
    "flask-before-request": [
        "before_request.*chain", "middleware.*order", "insert.*0", "layer.*intercept",
        "hotlink.*whitelist", "防盗链", "CSRF.*豁免",
    ],
    "rule-enforcer": [
        "IRON_RULE", "§14", "12步骤", "铁律.*违反", "dev_activity_preflight",
        "preflight.*未接", "flow_id.*缺失", "MT_IR_D",
    ],
    "andromeda-daemon": [
        "daemon.*注册", "sys_.*daemon", "auto_.*engine", "EigenFlux",
        "仙女座", "恒星.*skill", "自演化", "auto_skill",
    ],
    "flask-csrf": [
        "csrf.*token", "curl.*cookie", "netscape.*jar", "X-CSRF-Token",
        "request.get_json", "form.*post.*redirect",
    ],
}


def _get_db():
    return sqlite3.connect(DB_PATH, timeout=10)


# ====== Step 1: 扫描三个数据源 ======
def scan_sources():
    """返回 dict: cluster_name → [evidence_items]"""
    evidence = {k: [] for k in KEYWORD_CLUSTERS}

    # 源 A: mt_iron_rule_violations
    try:
        c = _get_db()
        rows = c.execute(
            "SELECT viol_rule, viol_context, viol_detected_at FROM mt_iron_rule_violations ORDER BY viol_detected_at DESC LIMIT 50"
        ).fetchall()
        for rule, ctx, ts in rows:
            for cluster, kws in KEYWORD_CLUSTERS.items():
                if any(kw.lower() in ctx.lower() or kw.lower() in rule.lower() for kw in kws):
                    evidence[cluster].append(f"[VIOL:{rule}] {ctx[:150]}")
        c.close()
    except Exception as e:
        print(f"  ⚠️ 扫描 mt_iron_rule_violations: {e}")

    # 源 B: Flask log
    try:
        if os.path.exists(FLASK_LOG):
            with open(FLASK_LOG, errors='ignore') as f:
                for line in f:
                    if len(line.strip()) < 10: continue
                    for cluster, kws in KEYWORD_CLUSTERS.items():
                        if any(kw.lower() in line.lower() for kw in kws):
                            evidence[cluster].append(line.strip()[:150])
    except Exception as e:
        print(f"  ⚠️ 扫描 Flask log: {e}")

    # 源 C: mt_dev_flow_events
    try:
        c = _get_db()
        rows = c.execute(
            "SELECT event_detail, triggered_at FROM mt_dev_flow_events ORDER BY triggered_at DESC LIMIT 30"
        ).fetchall()
        for detail, ts in rows:
            if not detail: continue
            for cluster, kws in KEYWORD_CLUSTERS.items():
                if any(kw.lower() in detail.lower() for kw in kws):
                    evidence[cluster].append(f"[FLOW:{ts}] {str(detail)[:150]}")
        c.close()
    except Exception as e:
        print(f"  ⚠️ 扫描 mt_dev_flow_events: {e}")

    # 过滤 + 去重
    for cluster in evidence:
        seen = set()
        deduped = []
        for item in evidence[cluster]:
            h = hashlib.md5(item.encode()).hexdigest()[:8]
            if h not in seen:
                seen.add(h)
                deduped.append(item)
        evidence[cluster] = deduped[:20]  # 每类最多 20 条

    return {k: v for k, v in evidence.items() if v}  # 过滤空


# ====== Step 2: 调用 local_ai 提炼 Skill ======
def derive_skill_via_local_ai(cluster_name, evidence_items):
    """用 MCP local_ai_chat 生成 SKILL.md"""
    prompt = f"""你是仙女座自演化引擎 (flow_id={FLOW_ID})。

以下是一类反复出现的问题模式 (来自违规记录/Flask log/流程事件, 共 {len(evidence_items)} 条):

{chr(10).join(f'- {e}' for e in evidence_items)}

请为这类问题生成一个 MTSCOS AI 项目的 SKILL.md, 严格按以下格式:

---
name: "{cluster_name}"
alwaysApply: false
description: "一句话描述本 Skill 做什么 + 什么时候触发 (200字内)"
---

# Skill 标题 (中文)

## 解决什么问题
(一句话)

## 快速上手
最简使用流程 + 核心原则速记

## 已踩过的坑
| # | 错误写法 | 正确做法 |
|---|---------|---------|

## 快速命令/代码片段
```bash/python/sql
...
```

## 预防铁律
1. ...
2. ...

要求:
- name 用 ASCII 标识 (小写+横杠)
- description 必须包含 "做什么" + "什么时候触发"
- 正文中文, 结构清晰, 可直接作为 Skill 使用
- 内容必须基于上面的证据, 不要凭空写
"""
    try:
        # 通过 MCP local_ai_chat
        import requests as _r
        # local_ai_chat 是 MCP tool, 无法直接 subprocess. 走本地 Ollama
        result = subprocess.run(
            ["ollama", "run", "qwen2.5:7b", prompt],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            # ollama serve 没启动也降级
            print(f"    (ollama 降级 → 固定模板)")
            return _fallback_skill_template(cluster_name, evidence_items)
        return result.stdout.strip()
    except FileNotFoundError:
        print(f"    (ollama 未安装 → 固定模板)")
        return _fallback_skill_template(cluster_name, evidence_items)
    except Exception as e:
        print(f"    (local_ai 异常 → 固定模板)")
        return _fallback_skill_template(cluster_name, evidence_items)


def _fallback_skill_template(cluster_name, evidence):
    """local_ai 不可用时的固定模板降级"""
    title_map = {
        "flask-blueprint-path": "Flask Blueprint url_prefix + route 路径陷阱",
        "flask-auth-deadlock": "Flask 登录路由装饰器死锁",
        "flask-sqlite-column": "多 SQLite DB 列名不兼容兼容",
        "flask-before-request": "Flask before_request 链顺序管理",
        "rule-enforcer": "§14 铁律强制执行",
        "andromeda-daemon": "仙女座 daemon 注册与自演化",
        "flask-csrf": "Flask CSRF token + Cookie Jar 处理",
    }
    title = title_map.get(cluster_name, f"问题模式: {cluster_name}")
    desc_map = {
        "flask-blueprint-path": "Flask Blueprint url_prefix + route 路径陷阱速查. Invoke when writing Flask Blueprint routes, debugging 404s.",
        "flask-auth-deadlock": "Flask 登录路由装饰器死锁 + view_functions 覆盖. Invoke when two Flask routes handle /auth/login.",
        "flask-sqlite-column": "多 SQLite DB 列名不兼容分层 SELECT 模板. Invoke when Flask logs no such column.",
        "flask-before-request": "Flask before_request 链顺序管理 + 多层拦截. Invoke when middleware order matters.",
        "rule-enforcer": "§14 IRON_RULE 强制执行 + dev_activity_preflight 接线. Invoke when agent writes code without flow_id.",
        "andromeda-daemon": "仙女座 daemon 注册 + 自演化 + Skill 衍生. Invoke when adding new auto_* daemon.",
        "flask-csrf": "Flask CSRF token + curl cookie jar 处理. Invoke when POST login returns CSRF error.",
    }
    desc = desc_map.get(cluster_name, f"问题模式 {cluster_name}. Invoke when user asks about this pattern.")

    pitfalls = "\n".join(
        f"| {i+1} | 证据: {e[:50]}... | 见 mt_iron_rule_violations / Flask log |"
        for i, e in enumerate(evidence[:5])
    ) if evidence else "| 1 | (暂无) | — |"

    return f"""---
name: "{cluster_name}"
alwaysApply: false
description: "{desc}"
---

# {title}

> 自动衍生引擎产出 · flow_id={FLOW_ID} · 证据 {len(evidence)} 条

## 解决什么问题
从 mt_iron_rule_violations / Flask log / dev_flow_events 聚类发现的高频问题模式.

## 已发现的坑 (来自真实证据)
{pitfalls}

## 预防模板
1. 写代码前查 mt_iron_rule_violations 是否已有同类违规
2. Flask 请求先过 dev_activity_preflight (before_request[0])
3. Schema 变更后重启 Flask 看启动警告

## 快速命令
```bash
# 查同类违规历史
cd flask-app && python3 -c "
import sqlite3; c=sqlite3.connect('engines/app.db')
rows=c.execute(\"SELECT * FROM mt_iron_rule_violations WHERE viol_context LIKE '%{cluster_name}%'\").fetchall()
print(f'  同类违规: {{len(rows)}} 条')
"
```"""


# ====== Step 3: 写入 + 验证 ======
def write_and_validate_skill(cluster_name, skill_md):
    """返回 (ok, path_or_error)"""
    if not skill_md:
        return False, "skill_md 为空"

    # 解析 frontmatter
    if not skill_md.startswith('---'):
        return False, "缺少 frontmatter --- 边界"
    parts = skill_md.split('---', 2)
    if len(parts) < 3:
        return False, "frontmatter 格式不完整"
    fm = parts[1]
    body = parts[2].lstrip('\n')

    name_match = re.search(r'name:\s*"([^"]+)"', fm)
    desc_match = re.search(r'description:\s*"([^"]+)"', fm)
    if not name_match:
        return False, "frontmatter 缺 name"
    if not desc_match:
        return False, "frontmatter 缺 description"

    skill_name = name_match.group(1).strip()
    skill_path = os.path.join(SKILLS_DIR, skill_name)
    os.makedirs(skill_path, exist_ok=True)

    full_content = f"---{fm}---\n{body}"
    target = os.path.join(skill_path, "SKILL.md")
    with open(target, 'w', encoding='utf-8') as f:
        f.write(full_content)

    return True, target


# ====== Step 4: 落库 Skill 衍生日志 ======
def log_derivation(cluster_name, skill_path, evidence_count, success):
    try:
        c = _get_db()
        c.execute("""CREATE TABLE IF NOT EXISTS mt_andromeda_skill_derivation_log (
            deriv_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_name TEXT, skill_path TEXT, evidence_count INTEGER,
            success INTEGER, flow_id TEXT, created_at TEXT
        )""")
        c.execute("""INSERT INTO mt_andromeda_skill_derivation_log
            (cluster_name, skill_path, evidence_count, success, flow_id, created_at)
            VALUES (?,?,?,?,?,datetime('now','localtime'))""",
            (cluster_name, skill_path or '', evidence_count, 1 if success else 0, FLOW_ID))
        c.commit()
        c.close()
    except Exception as e:
        print(f"  ⚠️ 落库失败: {e}")


# ====== 主循环 ======
def run_once():
    print("=" * 60)
    print("🪐 sys_auto_skill_deriver · 仙女座 Skill 自动衍生引擎")
    print(f"   flow_id={FLOW_ID}  interval=60min  alwaysApply=true")
    print("=" * 60)

    # 确保目录存在
    os.makedirs(SKILLS_DIR, exist_ok=True)
    print(f"\n📁 Skill 目录: {SKILLS_DIR}")

    # Step 1: 扫描
    print("\n[Step 1] 扫描数据源...")
    clusters = scan_sources()
    print(f"  扫描完成: {len(clusters)} 类有足够证据 (阈值 ≥ 1)")
    for c, items in sorted(clusters.items(), key=lambda x: -len(x[1])):
        print(f"    📥 {c}: {len(items)} 条证据")

    if not clusters:
        print("\nℹ️ 没有新的问题模式, 本轮不衍生")
        return

    # Step 2+3+4: 逐个聚类 → 提炼 → 写入 → 验证 → 落库
    print("\n[Step 2-4] 聚类提炼 + 写入 + 验证...")
    results = []
    for cluster, evidence in clusters.items():
        print(f"\n  🛠️ 处理 {cluster} ({len(evidence)} 条证据)...")
        skill_md = derive_skill_via_local_ai(cluster, evidence)
        ok, path_or_err = write_and_validate_skill(cluster, skill_md)
        log_derivation(cluster, path_or_err if ok else "", len(evidence), ok)
        results.append((cluster, ok, path_or_err))
        if ok:
            print(f"    ✅ 已写入: {path_or_err}")
        else:
            print(f"    ❌ 验证失败: {path_or_err}")

    # 汇总
    print("\n" + "=" * 60)
    print("📊 本轮衍生结果:")
    for cluster, ok, path in results:
        mark = "✅" if ok else "❌"
        print(f"  {mark} {cluster}")
    total_ok = sum(1 for _, ok, _ in results if ok)
    print(f"\n成功 {total_ok}/{len(results)}")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--once', action='store_true', help='执行一轮后退出')
    p.add_argument('--daemon', action='store_true', help='守护进程模式 (60min 周期)')
    p.add_argument('--interval', type=int, default=60, help='守护进程周期 (分钟)')
    args = p.parse_args()

    if args.daemon:
        print(f"🪐 sys_auto_skill_deriver 守护模式 启动, interval={args.interval}min")
        while True:
            try:
                run_once()
            except Exception as e:
                print(f"❌ 本轮执行异常: {e}")
            time.sleep(args.interval * 60)
    else:
        run_once()
