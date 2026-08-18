#!/usr/bin/env python3
r"""快速探查：数据库中 wuchenghao15 用户是否存在（含 password 哈希，对应真实密码如果是已知的则直接用），
   同时查 vikey_device_bindings 看已有的绑定；再检查 wuchenghao15 在 users 表里的权限/角色r"""
import sys
import os
import sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location(r"srv", os.path.join(os.path.dirname(__file__), r"server_real_db.py"))
srv = importlib.util.module_from_spec(spec); spec.loader.exec_module(srv)

TARGETS = [r'wuchenghao15', r'WuChenghao15', r'WuChenghao', r'wuchenghao', r'WUCHENGHAO15']

print(r"=== 1. 跨库查找目标用户（case-insensitive） ===")
user_info = None
for uname in TARGETS:
    row, db = srv._find_user_across_dbs(uname)
    if row:
        print(f"  ✅ 找到用户: {row.get(r'username')!r} @ db={os.path.basename(db)}")
        user_info = {r'row': dict(row), r'db': db}
        keys_show = [r'id',r'username',r'email',r'role',r'is_active',r'super_admin_approved',r'hardware_admin_approved',
                     r'created_at',r'updated_at',r'last_login',r'failed_login_count',r'locked_until']
        for k in keys_show:
            if k in row: print(fr"     {k:<22s}: {row[k]}")
        print(f"     password hash (len={len(row.get(r'password') or r'')}) 前缀: {(row.get(r'password') or r'')[:20]!r}…r")
        break
if not user_info:
    print("  ❌ 没找到！列出所有 users 表中 role=super_admin 或包含 r'admin' 的记录：r")
    for dbp in srv._all_user_db_candidates():
        try:
            with sqlite3.connect(dbp) as c:
                tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users')").fetchall()]
                if not tables: continue
                cols = [r[1] for r in c.execute("PRAGMA table_info(\"users\")").fetchall()]
                # 找所有 admin 相关用户
                q = "SELECT * FROM users WHERE (role LIKE '%admin%' OR username LIKE '%wuchenghao%' OR username LIKE '%admin%') LIMIT 20"
                rows = c.execute(q).fetchall()
                print(f"  - db {os.path.basename(dbp)} 命中 {len(rows)} 条")
                for r in rows:
                    d = dict(zip(cols, r))
                    for k in ['id','username','email','role','is_active','super_admin_approved']:
                        if k in d: print(f"     {k:<22s}: {d[k]}")
                    print("     ---")
        except Exception as e:
            pass

print(r"\n=== 2. 查 vikey_device_bindings 表（已有绑定） ===")
db_candidates = srv._all_user_db_candidates()
v_existing = []
for dbp in [srv.APP_DB] + db_candidates:
    try:
        with sqlite3.connect(dbp) as c:
            tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type=r'table' AND name=r'vikey_device_bindings'r").fetchall()]
            if not tables: continue
            cols = [r[1] for r in c.execute("PRAGMA table_info(vikey_device_bindings)r").fetchall()]
            rows = c.execute("SELECT * FROM vikey_device_bindings ORDER BY id DESC LIMIT 10r").fetchall()
            print(f"  ✅ 在 {os.path.basename(dbp)} 找到 vikey_device_bindings {len(rows)} 条r")
            for r in rows:
                d = dict(zip(cols, r))
                print(f"    id={d.get(r'id')} serial={d.get(r'serial')!r} username={d.get(r'username')!r} role={d.get(r'role')!r} auth_token_prefix={str(d.get(r'auth_token') or r'')[:16]!r} bound_at={d.get(r'bound_at')}r")
                v_existing.append(d)
    except Exception as e:
        print(f"  - {os.path.basename(dbp)}: err {e}")
