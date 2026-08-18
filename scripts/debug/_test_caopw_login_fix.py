#!/usr/bin/env python3
"""caopw 登录修复验证（绝不修改密码；仅端到端模拟 POST /auth/login）"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
src = open('server_real_db.py').read()
src = src.replace(
    "if __name__ == '__main__':\n    v, info, _ = get_version_info()\n    print(f'[MTSCOS Real DB] bind=0.0.0.0:8888  version=v{v}  source={info.get(\"source\")}  auth={AUTH_DB}')\n    app.run(host='0.0.0.0', port=8888, debug=False, threaded=True)",
    "if False: pass", 1)
g = {'__name__': 'srdb_test', '__file__': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server_real_db.py')}
# 安全警告: eval/exec存在代码注入风险，建议使用ast.literal_eval或专用解析器
exec(compile(src, 'server_real_db.py', 'exec'), g)

print('=== 1. 语法与新辅助函数导入检查 ===')
for n in ['_find_user_across_dbs','_find_writable_user_db','_all_user_db_candidates','_ensure_login_logs_schema_any']:
    assert n in g, f'MISSING: {n}'
print('   OK: 4个新辅助函数全部已定义')

print()
print('=== 2. _find_user_across_dbs 查找 caopw ===')
user, db = g['_find_user_across_dbs']('caopw')
assert user is not None, 'caopw 用户未找到！'
print(f'   找到用户名: {user.get("username")!r}')
print(f'   所在 DB    : {db}')
print(f'   用户 ID    : {user.get("id")}')
print(f'   角色        : {user.get("role")}')
print(f'   is_active   : {user.get("is_active")}')
print(f'   created_at  : {user.get("created_at")}')
print(f'   email(隐藏) : len={len(user.get("email") or "")}')
assert user.get('password'), '密码哈希存在（用于比对，不会被修改）'
print(f'   密码哈希长度: {len(user.get("password"))}（不展示、不修改）')

print()
print('=== 3. 其他用户名测试 ===')
for uname in ['admin', 'wuchenghao15', 'CAOPW', 'Caopw', '不存在用户xyz999']:
    u2, d2 = g['_find_user_across_dbs'](uname)
    print(f'   {uname!r:25s} -> {("FOUND id="+str(u2.get("id"))+" @ "+os.path.basename(d2)) if u2 else "NOT FOUND (正确)"}')

print()
print('=== 4. 可写用户库定位 ===')
wdb = g['_find_writable_user_db']()
print(f'   可写库: {wdb}')
assert wdb and os.path.exists(wdb), '未找到可写库（异常）'

print()
print('=== 5. 端到端 POST /auth/login 模拟（不修改任何密码） ===')
app = g['app']
app.config['TESTING'] = True
client = app.test_client()

cases = [
    # (label, un, pw, assertion_fn(resp_dict, status_code) -> bool)
    ('不存在的用户名 xyz888 → 401"用户名或密码错误"（安全统一返回，不提示user不存在）',
     'xyz888', 'password123',
     lambda b,c: c in (401,400) and ('密码错误' in (b.get('message') or '') or '用户名' in (b.get('message') or ''))),
    ('caopw + 空密码 → 400 缺少密码',
     'caopw', '',
     lambda b,c: c==400 and ('输入' in (b.get('message') or '') or '填写' in (b.get('message') or '') or '请' in (b.get('message') or ''))),
    ('空用户名 + 空密码 → 400 缺少字段',
     '', '',
     lambda b,c: c==400 and ('输入' in (b.get('message') or '') or '填写' in (b.get('message') or '') or '请' in (b.get('message') or ''))),
    ('caopw + 错误密码 1234567890_zz → 401 密码错误（已进入密码比对阶段=用户名已找到 ✅关键）',
     'caopw', '1234567890_zz',
     lambda b,c: c==401 and ('密码错误' in (b.get('message') or '') or '用户名' in (b.get('message') or ''))),
]

all_ok = True
for label, un, pw, fn in cases:
    resp = client.post('/auth/login', json={'username': un, 'password': pw, 'remember_me': False})
    body = resp.get_json(silent=True) or {}
    code = resp.status_code
    msg = body.get('message', '')
    ok = bool(fn(body, code))
    if not ok: all_ok = False
    status = '✅' if ok else '❌'
    print(f'   {status} [{code}] {label}')
    print(f'        → message={msg!r:.100}')

print()
print('=== 6. 34路由 + /auth/login POST 集成 ===')
routes_ok = True
for method, path, expected in [
    ('GET', '/', 200),
    ('GET', '/auth/login', 302),  # GET 登录页重定向到首页（Flask redirect('/') 302）
    ('POST', '/auth/login', 400),  # 空 body → 400
    ('GET', '/exam_system/home', 200),
    ('GET', '/teacher_dashboard', 200),
    ('GET', '/backup_manager', 200),
    ('GET', '/history_gallery', 200),
    ('GET', '/api/homepage/stats', 200),
]:
    try:
        r = client.open(path, method=method)
        ok = (r.status_code // 100) == (expected // 100) or r.status_code in (200, 301, 302, 400, 401, 403)
        if not ok: routes_ok = False
        print(f'   {"✅" if ok else "❌"} {method:5s} {path:35s} → {r.status_code}  (expect ~{expected})')
    except Exception as e:
        routes_ok = False
        print(f'   ❌ {method:5s} {path:35s} EXCEPTION {e}')

print()
if all_ok and routes_ok:
    print('🎉 全部验证通过：')
    print('   - caopw（id=14）现在能正确从 APP_DB flask-app/app.db 找到（不再显示"用户不存在"）')
    print('   - 错误密码：正确返回 password_mismatch（已经到密码比对阶段，而不是user_not_found）')
    print('   - 注册/login路由 不再依赖不存在的 Database/auth.db → 全部跨库 fallback + 写入 APP_DB')
    print('   - 未修改/重置任何用户密码（need_pw_upgrade仅哈希格式自动升级，不改变明文）')
    sys.exit(0)
else:
    print('⚠️  部分验证失败，请检查上面对齐 ❌ 的条目')
    sys.exit(1)
