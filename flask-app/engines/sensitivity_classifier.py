#!/usr/bin/env python3
"""
敏感度分类器 — sensitivity_classifier.py
===========================================

所有开发活动自动分为 3 级:
  routine   → 全自动放行, 零人工 (95% 的日常开发)
  sensitive → 需人工审批 (敏感数据/密钥/权限变更)
  major     → 需重大决策 (版本 major bump / 架构变更 / 数据库 schema DDL)

分类规则:
  major    触发词: VERSION major bump (vX.0.0) / CREATE TABLE / ALTER TABLE / DROP TABLE /
                  新功能.*架构 / 系统重构 / 迁移 / 升级.*v2 / deprecate / 废弃
  sensitive 触发词: password / secret / token / api_key / VIKEY / 权限变更 / role.*change /
                   .env 修改 / 生产数据库 / 用户.*删除 / 导出.*用户数据 / 解密 / 加密密钥
  routine   其他所有

用法:
  python3 sensitivity_classifier.py classify "硬编码颜色值修复"
  python3 sensitivity_classifier.py classify "新增 API Key 存储"
  python3 sensitivity_classifier.py classify "数据库 schema ALTER TABLE"
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ── 触发词定义 ──────────────────────────────────────────────────────────────

MAJOR_TRIGGERS = [
    # 版本 major bump
    re.compile(r'version.*bump.*major', re.IGNORECASE),
    re.compile(r'major\.bump', re.IGNORECASE),
    re.compile(r'v\d+\.0\.0', re.IGNORECASE),
    # 数据库 DDL
    re.compile(r'CREATE\s+TABLE', re.IGNORECASE),
    re.compile(r'ALTER\s+TABLE', re.IGNORECASE),
    re.compile(r'DROP\s+TABLE', re.IGNORECASE),
    re.compile(r'DROP\s+COLUMN', re.IGNORECASE),
    re.compile(r'ADD\s+COLUMN', re.IGNORECASE),
    re.compile(r'CREATE\s+INDEX', re.IGNORECASE),
    re.compile(r'DROP\s+INDEX', re.IGNORECASE),
    # 架构/重构
    re.compile(r'架构重构|系统重构|全面重构|全新架构', re.IGNORECASE),
    re.compile(r'migration|迁移|deprecate|废弃|remove.*v1|replace.*legacy', re.IGNORECASE),
    re.compile(r'new.*framework|新.*框架|改.*引擎', re.IGNORECASE),
    # 重大功能
    re.compile(r'新增.*模块|新增.*引擎|新增.*系统|新增.*平台|新增.*服务', re.IGNORECASE),
    re.compile(r'全新.*|彻底.*重写|from\s*scratch', re.IGNORECASE),
]

SENSITIVE_TRIGGERS = [
    # 密钥/凭证 (中英文)
    re.compile(r'password|passwd|secret|api[_-]?key|access[_-]?key|private[_-]?key|API.*Key.*存储', re.IGNORECASE),
    re.compile(r'新增.*api[_-]?key|add.*api[_-]?key|create.*api[_-]?key', re.IGNORECASE),
    re.compile(r'VIKEY|vikey|szu100|加密狗|硬件密钥|密钥|密码|token|令牌', re.IGNORECASE),
    # 密码策略
    re.compile(r'密码策略|password.*policy|密码.*强度|密码.*升级', re.IGNORECASE),
    # 权限/角色变更
    re.compile(r'permission.*change|role.*change|权限.*变更|角色.*变更|修改.*角色', re.IGNORECASE),
    re.compile(r'super_admin.*create|super_admin.*delete|新增.*管理员|删除.*管理员', re.IGNORECASE),
    re.compile(r'token.*(issue|revoke|rotate|invalidat)', re.IGNORECASE),
    # 生产数据
    re.compile(r'生产.*数据库|production.*db|prod.*db', re.IGNORECASE),
    re.compile(r'用户.*删除|delete.*user|清空.*数据|truncate', re.IGNORECASE),
    re.compile(r'导出.*用户|export.*user.*data|用户.*隐私', re.IGNORECASE),
    # .env / 配置密钥
    re.compile(r'\.env|环境变量.*密钥|配置.*密钥|config.*secret', re.IGNORECASE),
    # 加密操作
    re.compile(r'encrypt|decrypt|加密|解密|密钥.*生成|证书.*生成', re.IGNORECASE),
    # 机密等级变更
    re.compile(r'classification.*change|机密.*降级|降级.*公开', re.IGNORECASE),
]


def classify(task_title: str = "", changed_files: list = None, changed_content: str = "") -> dict:
    """
    分类开发活动敏感度。
    返回: {level, reason, need_human, auto_allowed}
    """
    text = f"{task_title}\n{' '.join(changed_files or [])}\n{changed_content}".lower()
    
    major_hits = []
    sens_hits = []
    
    for pat in MAJOR_TRIGGERS:
        hits = pat.findall(text)
        if hits:
            major_hits.append({"pattern": pat.pattern[:40], "match": hits[:2]})
    
    for pat in SENSITIVE_TRIGGERS:
        hits = pat.findall(text)
        if hits:
            sens_hits.append({"pattern": pat.pattern[:40], "match": hits[:2]})
    
    if major_hits:
        level = "major"
        need_human = True
        auto_allowed = False
        reason = f"命中 major 触发词: {[h['match'] for h in major_hits[:3]]}"
    elif sens_hits:
        level = "sensitive"
        need_human = True
        auto_allowed = False
        reason = f"命中 sensitive 触发词: {[h['match'] for h in sens_hits[:3]]}"
    else:
        level = "routine"
        need_human = False
        auto_allowed = True
        reason = "未命中任何敏感/重大触发词 → routine, 全自动放行"
    
    return {
        "level": level,
        "reason": reason,
        "need_human": need_human,
        "auto_allowed": auto_allowed,
        "major_hits": major_hits,
        "sensitive_hits": sens_hits,
        "task_title": task_title[:80],
    }


def classify_files(file_paths: list) -> dict:
    """批量 classify 文件列表"""
    routines = []; sensitives = []; majors = []
    for fp in file_paths:
        name = Path(fp).name
        result = classify(task_title=name, changed_files=[fp])
        if result["level"] == "routine":
            routines.append(fp)
        elif result["level"] == "sensitive":
            sensitives.append(fp)
        else:
            majors.append(fp)
    return {
        "routine": routines,
        "sensitive": sensitives,
        "major": majors,
        "total": len(file_paths),
        "summary": f"{len(routines)} routine / {len(sensitives)} sensitive / {len(majors)} major"
    }


# ═════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("""
敏感度分类器 — sensitivity_classifier.py
===========================================

用法:
  python3 sensitivity_classifier.py classify "<任务标题>" [文件1,文件2...]
  python3 sensitivity_classifier.py files <file1> <file2> ...
  python3 sensitivity_classifier.py test

返回 JSON: {level: routine|sensitive|major, need_human: bool, reason: str}
""")
        sys.exit(1)

    cmd = sys.argv[1]
    
    if cmd == "classify":
        title = sys.argv[2] if len(sys.argv) > 2 else ""
        files = sys.argv[3:] if len(sys.argv) > 3 else []
        result = classify(title, files)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "files":
        files = sys.argv[2:]
        result = classify_files(files)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "test":
        print("══ sensitivity_classifier 10 条测试 ══")
        tests = [
            ("硬编码颜色值修复", ["app.py"]),
            ("新增 API Key 存储功能", ["auth.py", "config.py"]),
            ("数据库 ALTER TABLE 加字段", ["migration.sql"]),
            ("修复 daemon 重启逻辑", ["engines/smart_mount.py"]),
            ("密码策略强度升级", ["auth.py", "password.py"]),
            ("新增全新聊天引擎模块", ["new_engine.py"]),
            ("用户表数据导出", ["export_user.py"]),
            ("日志清理脚本", ["cleanup_logs.py"]),
            ("v24.0.0 系统架构重构", ["arch.py", "refactor.py"]),
            (".env 修改", [".env"]),
        ]
        for title, files in tests:
            r = classify(title, files)
            icon = {"routine": "🟢", "sensitive": "🟡", "major": "🔴"}[r["level"]]
            print(f"  {icon} {title:30s} → {r['level']:10s} need_human={r['need_human']}")

if __name__ == "__main__":
    main()
