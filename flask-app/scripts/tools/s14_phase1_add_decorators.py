#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
§14 Phase1 T3: 批量补齐路由权限装饰器 (FLOW_20260907_PERMS14_PHASE1)
用户权限.md v1.2.0 §14.1: 全部路由必须携带 @system_container

策略:
  - AST 定位无权限装饰器的路由函数, 在 def 行上方插入 @system_container()
  - 公开路由排除清单 (登录前流程/浏览器上报/健康检查)
  - arduino 路由文件 → require_auth='super_admin' (用户权限.md Arduino仅SA铁律)
  - 每文件先备份 → 写回 → py_compile 验证 → 失败自动还原
"""
import ast
import hashlib
import os
import py_compile
import shutil
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, 'engines'))
from deep_inspection_engine import DeepInspectionEngine  # noqa: E402

BACKUP_DIR = os.path.join(BASE, '_runtime', 'backups', 'perm_phase1')
IMPORT_LINE = 'from app.middlewares.system_container import system_container'

# 公开路由排除 (登录前流程/浏览器上报/健康检查, 与 dev_activity_preflight 口径一致)
EXCLUDE_SUBSTRINGS = (
    'temp-login', 'csp-report', '/logout', '/health', 'session_health',
    'forgot_password', 'reset_password', 'check_username', '/static/',
)


def main():
    engine = DeepInspectionEngine(scan_dir=BASE)
    items = engine.inspect_route_decorators(record_alert=False)
    print(f'[1/4] AST 分析完成: {len(items)} 处待补')

    # 过滤排除清单
    todo = [it for it in items if not any(s in it.route for s in EXCLUDE_SUBSTRINGS)]
    skipped = len(items) - len(todo)
    print(f'[2/4] 排除公开路由 {skipped} 处, 待补 {len(todo)} 处')

    # 按文件聚合, def 行号降序插入 (避免行号漂移)
    by_file = {}
    for it in todo:
        by_file.setdefault(it.file, []).append(it)

    os.makedirs(BACKUP_DIR, exist_ok=True)
    ok_files, failed_files = [], []
    for relpath, fitems in sorted(by_file.items()):
        fpath = os.path.join(BASE, relpath)
        if not os.path.exists(fpath):
            continue
        is_arduino = 'arduino' in relpath.lower()
        deco = ("@system_container(require_auth='super_admin')"
                if is_arduino else '@system_container()')
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            src = ''.join(lines)
            need_import = IMPORT_LINE not in src
            # AST 定位最后一个顶层 import 语句结束行 (1-based, 0=文件头)
            # 字符串字面量中的括号会欺骗文本计数, 必须用 AST
            import_pos = 0
            if need_import:
                try:
                    tree = ast.parse(src)
                    for node in tree.body:
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            import_pos = max(import_pos, node.end_lineno or 0)
                except SyntaxError:
                    pass
            # 备份
            backup = os.path.join(
                BACKUP_DIR, relpath.replace(os.sep, '__') + '.' +
                hashlib.md5(src.encode()).hexdigest()[:8] + '.bak')
            os.makedirs(os.path.dirname(backup), exist_ok=True)
            shutil.copy2(fpath, backup)
            # 统一插入清单: (0-based插入位, 文本), 按位置降序一次应用, 避免行号漂移
            insertions = []
            for it in fitems:
                idx = it.line - 1  # def 行 0-based
                if idx >= len(lines):
                    continue
                def_line = lines[idx]
                indent = def_line[:len(def_line) - len(def_line.lstrip())]
                insertions.append((idx, f'{indent}{deco}\n'))
            if need_import:
                insertions.append((import_pos, IMPORT_LINE + '\n\n' if import_pos == 0 else IMPORT_LINE + '\n'))
            for pos, text in sorted(insertions, key=lambda x: -x[0]):
                lines.insert(pos, text)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            # 编译验证, 失败还原
            try:
                py_compile.compile(fpath, doraise=True)
                ok_files.append((relpath, len(fitems), backup))
            except py_compile.PyCompileError as ce:
                shutil.copy2(backup, fpath)
                failed_files.append((relpath, str(ce)[:100]))
        except Exception as e:  # noqa: BLE001
            failed_files.append((relpath, str(e)[:100]))

    print(f'[3/4] 补齐完成: 成功 {len(ok_files)} 文件, 失败 {len(failed_files)} 文件')
    for (f, n, _) in ok_files[:5]:
        print(f'   ✅ {f} (+{n})')
    if len(ok_files) > 5:
        print(f'   ... 等 {len(ok_files)} 个文件')
    for (f, err) in failed_files[:10]:
        print(f'   ❌ {f}: {err}')

    # 复扫验收
    engine2 = DeepInspectionEngine(scan_dir=BASE)
    remain = engine2.inspect_route_decorators(record_alert=False)
    print(f'[4/4] 复扫验收: 剩余缺失 {len(remain)} 处 (应仅剩排除清单内公开路由)')
    stamp = datetime.now().isoformat()
    print(f'完成时间: {stamp} | 备份目录: {BACKUP_DIR}')
    return len(failed_files)


if __name__ == '__main__':
    sys.exit(0 if main() == 0 else 1)
