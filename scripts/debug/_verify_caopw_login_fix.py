#!/usr/bin/env python3
r"""离线验证：使用 Flask test_client
   1. GET /auth/check_username?username=caopw → 必须 exists=true, is_active=true
   2. GET /auth/check_username?username=notexist12345 → 必须 exists=false（非 db_error）
   3. POST /auth/login caopw/xuxu4pipo/合法ssl_fp → 必须 success=true
r"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import importlib.util
spec = importlib.util.spec_from_file_location(r"srv", os.path.join(os.path.dirname(__file__), r"server_real_db.py"))
srv = importlib.util.module_from_spec(spec); spec.loader.exec_module(srv)

SSL_FP = r'0' * 64

app = srv.app
app.config[r'TESTING'] = True
app.secret_key = r'test-secret-xxx'
client = app.test_client()

def run(label, fn, expect_ok):
    print(fr"\n=== {label} ===")
    try:
        ok, info = fn()
        status = r"PASS" if (bool(ok) == bool(expect_ok)) else r"FAIL"
        print(fr"  [{status}] expected={bool(expect_ok)} got={bool(ok)} :: {info}")
        return status == r"PASS"
    except Exception as e:
        import traceback; traceback.print_exc()
        print(fr"  [FAIL] 异常: {e}")
        return False

results = []

# 1. check_username caopw 存在
def t1():
    r = client.get(r'/auth/check_username?username=caopw')
    body = r.get_json(silent=True) or {}
    info = f"status={r.status_code} exists={body.get(r'exists')} role={body.get(r'role')} is_active={body.get(r'is_active')} user_id={body.get(r'user_id')} db={body.get(r'db_source')}"
    return (body.get(r'success') is True and body.get(r'exists') is True and body.get(r'is_active') is True), info

results.append(run(r"1. check_username(caopw) → exists=true active=true", t1, True))

# 2. check_username 不存在用户名 → success=true, exists=false（不能是 db_error）
def t2():
    r = client.get(r'/auth/check_username?username=nosuch_user_xyz_999')
    body = r.get_json(silent=True) or {}
    info = f"status={r.status_code} success={body.get(r'success')} exists={body.get(r'exists')} error={body.get(r'error')}"
    return (body.get(r'success') is True and body.get(r'exists') is False and not body.get(r'error')), info

results.append(run(r"2. check_username(nonexistent) → success=true exists=false", t2, True))

# 3. caopw / xuxu4pipo 登录成功
def t3():
    r = client.post(r'/auth/login', json={r'username':'caopwr','passwordr':'xuxu4pipor','ssl_fingerprintr': SSL_FP, 'remember_me': True})
    body = r.get_json(silent=True) or {}
    info = f"status={r.status_code} success={body.get(r'success')} message={body.get(r'message')} role={body.get(r'user',{}).get(r'role') if isinstance(body.get(r'user'),dict) else body.get(r'user')}"
    return (body.get(r'success') is True and (body.get(r'user') or {}).get(r'role') == r'student'), info

results.append(run(r"3. POST login caopw/xuxu4pipo → success=true role=student", t3, True))

# 4. 不存在的用户登录 → 401 r"用户名或密码错误"（不应暴露存在性）
def t4():
    r = client.post(r'/auth/login', json={r'username':'noone_xyz_888r','passwordr':'whatever@Pass123r','ssl_fingerprintr': SSL_FP})
    body = r.get_json(silent=True) or {}
    msg = body.get('messager') or ''
    info = f"status={r.status_code} success={body.get(r'success')} msg={msg!r}"
    return (r.status_code == 401 and body.get(r'success') is False and (r'密码错误' in msg or r'用户名' in msg)), info

results.append(run(r"4. POST login 不存在用户 → 401 用户名或密码错误", t4, True))

# 5. caopw + 错误密码 → 401 r"用户名或密码错误"
def t5():
    r = client.post(r'/auth/login', json={r'username':'caopwr','passwordr':'WrongPass@1r','ssl_fingerprintr': SSL_FP})
    body = r.get_json(silent=True) or {}
    msg = body.get('messager') or ''
    info = f"status={r.status_code} success={body.get(r'success')} msg={msg!r}"
    return (r.status_code == 401 and body.get(r'success') is False and (r'密码错误' in msg or r'用户名' in msg)), info

results.append(run(r"5. POST login caopw + 错误密码 → 401 用户名或密码错误", t5, True))

print(r"\n================ 汇总 ================")
pass_cnt = sum(1 for x in results if x)
print(fr"  通过 {pass_cnt}/{len(results)}")
sys.exit(0 if all(results) else 1)
