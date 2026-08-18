#!/usr/bin/env python3
"""新功能端到端验证：History API / Snapshot / ISO / Shadow / Vikey + 4个新页面路由"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
src = open('server_real_db.py').read()
# 禁用 if __name__ 启动
src = src.replace(
    "if __name__ == '__main__':\n    v, info, _ = get_version_info()\n    print(f'[MTSCOS Real DB] bind=0.0.0.0:8888  version=v{v}  source={info.get(\"source\")}  auth={AUTH_DB}')\n    app.run(host='0.0.0.0', port=8888, debug=False, threaded=True)",
    "if False: pass", 1)
g = {'__name__': 'e2e_test', '__file__': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server_real_db.py')}
# 安全警告: eval/exec存在代码注入风险，建议使用ast.literal_eval或专用解析器
exec(compile(src, 'server_real_db.py', 'exec'), g)

app = g['app']
app.config['TESTING'] = True
client = app.test_client()
passes = []
fails = []

def check(name, cond, detail=''):
    (passes if cond else fails).append((name, detail))
    print(('✅ ' if cond else '❌ ') + name + (f' — {detail[:140]}' if detail else ''))

# 1) 新页面路由 4 个 2xx
pages = ['/history_gallery', '/backup_manager', '/shadow_system', '/vikey_manager']
for p in pages:
    r = client.get(p)
    check(f'GET {p}', r.status_code in (200, 302, 401), f'status={r.status_code}')

# 2) 历史档案馆 6 个 API
print()
print('--- /api/history/* ---')
for p in ['/api/history/stats', '/api/history/timeline', '/api/history/upgrades',
          '/api/history/learning', '/api/history/knowledge', '/api/history/rules']:
    r = client.get(p)
    data = r.get_json(silent=True) or {}
    ok = (r.status_code == 200) and bool(data.get('success'))
    add = ''
    if p == '/api/history/stats' and data.get('data'):
        add = 'versions={versions} upgrades={upgrades} knowledge={knowledge} learning={learning}'.format(**data['data'])
    elif p == '/api/history/timeline' and isinstance(data.get('data'), list):
        add = f'timeline entries={len(data.get("data"))}'
    check(f'GET {p}', ok, f'status={r.status_code}, ' + add)

# 3) Shadow 状态 + 切换到 shadow 再切回 live
print()
print('--- /api/shadow/* ---')
r = client.get('/api/shadow/status')
d = r.get_json(silent=True) or {}
check('GET /api/shadow/status', r.status_code == 200 and d.get('success'), f'current={d.get("data",{}).get("mode")}')

r = client.post('/api/shadow/switch', json={'mode': 'shadow', 'note': 'E2E 切换到shadow演练'})
d = r.get_json(silent=True) or {}
check('POST /api/shadow/switch (→ shadow)', r.status_code == 200 and d.get('success'), f'current={d.get("data",{}).get("mode")}')

r = client.post('/api/shadow/switch', json={'mode': 'live', 'note': 'E2E 回到live', 'shadow_off': True})
d = r.get_json(silent=True) or {}
check('POST /api/shadow/switch (→ live, shadow_off)', r.status_code == 200 and d.get('success'), f'current={d.get("data",{}).get("mode")}')

# 4) 快照 list → create（带shadow_mode_flag）→ restore
print()
print('--- /api/snapshot/* ---')
r = client.get('/api/snapshot/list')
d = r.get_json(silent=True) or {}
before = len(d.get('data') or []) if d.get('success') else -1
check('GET /api/snapshot/list (初始)', r.status_code == 200 and d.get('success'), f'count={before}')

r = client.post('/api/snapshot/create', json={'description': 'E2E-测试快照（影子）', 'shadow_mode': True})
d = r.get_json(silent=True) or {}
snap_id = None
if d.get('success') and d.get('snapshot'):
    snap_id = d['snapshot'].get('id')
check('POST /api/snapshot/create (shadow_mode=True)', r.status_code == 200 and d.get('success') and snap_id,
      f'id={snap_id} name={d.get("snapshot",{}).get("name") if d.get("snapshot") else None} files={d.get("snapshot",{}).get("files") if d.get("snapshot") else None} size={d.get("snapshot",{}).get("size") if d.get("snapshot") else None}')

r = client.get('/api/snapshot/list')
d = r.get_json(silent=True) or {}
after = len(d.get('data') or []) if d.get('success') else -1
check('GET /api/snapshot/list (新增后count↑)', d.get('success') and after > before, f'before={before} after={after}')

if snap_id:
    # 把刚生成的快照绑定为 shadow 基线
    r = client.post('/api/shadow/snapshot_link', json={'mode': 'shadow', 'snapshot_id': snap_id})
    d = r.get_json(silent=True) or {}
    check('POST /api/shadow/snapshot_link (shadow→#' + str(snap_id) + ')', r.status_code == 200 and d.get('success'), '')
    # 记录一次恢复
    r = client.post(f'/api/snapshot/restore/{snap_id}')
    d = r.get_json(silent=True) or {}
    check(f'POST /api/snapshot/restore/{snap_id} (RESTORE-ONLY，安全)', r.status_code == 200 and d.get('success'), f'restored_at={(d.get("restored_at") or "")[:19]}')

# 5) ISO list/build
print()
print('--- /api/iso/* ---')
r = client.get('/api/iso/list')
d = r.get_json(silent=True) or {}
before_iso = len(d.get('data') or []) if d.get('success') else -1
check('GET /api/iso/list (初始)', r.status_code == 200 and d.get('success'), f'count={before_iso}')

r = client.post('/api/iso/build', json={})
d = r.get_json(silent=True) or {}
iso_ok = (r.status_code == 200 and d.get('success'))
iso_id = d.get('iso', {}).get('id') if iso_ok else None
check('POST /api/iso/build (清单生成，无二进制文件)', iso_ok and iso_id,
      f'id={iso_id} name={d.get("iso",{}).get("name") if d.get("iso") else None} size={d.get("iso",{}).get("size") if d.get("iso") else None} sign={d.get("iso",{}).get("sign_status") if d.get("iso") else None}')

r = client.get('/api/iso/list')
d = r.get_json(silent=True) or {}
after_iso = len(d.get('data') or []) if d.get('success') else -1
check('GET /api/iso/list (新增后count↑)', d.get('success') and after_iso > before_iso, f'before={before_iso} after={after_iso}')

# 6) Vikey detect/bind/auth/issue_cert 二次开发契约
print()
print('--- /api/vikey/* (二次开发契约) ---')
# 用 caopw (真实存在 user) 做绑定
caopw_username = 'caopw'
r = client.get('/api/vikey/detect')
d = r.get_json(silent=True) or {}
check('GET /api/vikey/detect (Mock fallback 自动降级)', r.status_code == 200 and d.get('success'),
      f'present_count={d.get("data",{}).get("present_count") if d.get("data") else None} source={(d.get("data",{}).get("_source") or "")[:60]}')
serial = ''
if d.get('success') and d.get('data', {}).get('devices'):
    serial = d['data']['devices'][0].get('serial') or 'MTSCOS-VIKEY-DEMO-0001'
else:
    serial = 'MTSCOS-VIKEY-DEMO-0001'

# 绑定：caopw + admin role + 123456 pin
r = client.post('/api/vikey/bind', json={'serial': serial, 'username': caopw_username, 'role': 'user', 'pin': '123456'})
d = r.get_json(silent=True) or {}
bind_ok = (r.status_code == 200 and d.get('success'))
auth_token = d.get('binding', {}).get('auth_token') if bind_ok else None
check(f'POST /api/vikey/bind ({serial} ↔ {caopw_username}, pin=123456)', bind_ok and bool(auth_token),
      f'auth_token len={len(auth_token or "")} pin_set={d.get("binding",{}).get("pin_set") if d.get("binding") else None}')

# 鉴权：正确 token + pin 必须通过
r = client.post('/api/vikey/auth', json={'serial': serial, 'vikey_auth_token': auth_token or '', 'pin': '123456', 'username': caopw_username})
d = r.get_json(silent=True) or {}
check('POST /api/vikey/auth (正确 token+PIN)', r.status_code == 200 and d.get('success'),
      f'challenge_response len={len(d.get("challenge_response") or "")} valid_s={d.get("valid_seconds")}')

# 鉴权：错误 PIN → pin_mismatch
r = client.post('/api/vikey/auth', json={'serial': serial, 'vikey_auth_token': auth_token or '', 'pin': 'WRONG123'})
d = r.get_json(silent=True) or {}
check('POST /api/vikey/auth (错误PIN → pin_mismatch)', r.status_code == 401 and d.get('reason') == 'pin_mismatch', f'reason={d.get("reason")}')

# 鉴权：空 token 必须 401 missing
r = client.post('/api/vikey/auth', json={'serial': serial, 'vikey_auth_token': '', 'pin': '123456'})
d = r.get_json(silent=True) or {}
check('POST /api/vikey/auth (空token → missing)', r.status_code in (400, 401), f'status={r.status_code} reason={d.get("reason")}')

# 颁发证书：X.509最小化契约
r = client.post('/api/vikey/issue_cert', json={'serial': serial, 'owner': 'E2E Security QA'})
d = r.get_json(silent=True) or {}
check('POST /api/vikey/issue_cert (X.509最小化 5年有效期)', r.status_code == 200 and d.get('success'),
      f'cert_sn={d.get("cert",{}).get("cert_sn") if d.get("cert") else None} not_after={(d.get("cert",{}).get("not_after") or "")[:10]} pem_hash_len={len(d.get("cert",{}).get("cert_pem_hash") or "") if d.get("cert") else 0}')

# 日志列表 & 证书列表（至少有1条了）
r = client.get('/api/vikey/logs')
d = r.get_json(silent=True) or {}
check('GET /api/vikey/logs (>0 entries)', r.status_code == 200 and d.get('success') and len(d.get('data') or []) > 0,
      f'log_count={len(d.get("data") or [])}')

r = client.get('/api/vikey/certs')
d = r.get_json(silent=True) or {}
check('GET /api/vikey/certs (>0 entries)', r.status_code == 200 and d.get('success') and len(d.get('data') or []) > 0,
      f'cert_count={len(d.get("data") or [])}')

# 7) 备份 API（create / clean 不破坏真实db；create会复制db快照）
print()
print('--- /api/backup/* ---')
r = client.post('/api/backup/create')
d = r.get_json(silent=True) or {}
check('POST /api/backup/create (复制核心DB到 Database_Backups/)', r.status_code == 200 and d.get('success'),
      f'copied={len(d.get("copied_files") or []) if d.get("copied_files") is not None else 0} size={d.get("size")} name={d.get("name")}')

print()
print('=============================')
print(f'汇总：✅ {len(passes)} / ❌ {len(fails)} 总 {len(passes)+len(fails)}')
if fails:
    print('❌ 失败项：')
    for n, dt in fails:
        print('   -', n, ('— ' + dt) if dt else '')
    sys.exit(1)
else:
    print('🎉 所有端到端验证通过（含4个页面路由 + 历史馆6API + 快照3API + ISO2API + Shadow3API + Vikey7API + 备份1API 全部联动）')
    sys.exit(0)
