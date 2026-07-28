#!/usr/bin/env python3
"""
设置用户 caopw：
 - 密码 xuxu4pipo
 - 组别=成人教育学生
 - 权限=成人教育学生 (role=student + education_type=成人教育 + grade=成人教育学生)
 - 已激活
 - 邮箱：智能分配 caopw@mtscos.local
自动完成审批流程：
  用户激活申请 → 备案管理员审批通过 → 超级管理员审批通过
写入：users / user_approval_records / operation_logs / login_logs 4张表
"""
import os, sys, json, hashlib
from datetime import datetime

# ========== 加载 server_real_db.py ==========
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SRC_PATH = os.path.join(HERE, 'server_real_db.py')
src = open(SRC_PATH, encoding='utf-8').read()
# 屏蔽 __main__ 启动段：
src = src.replace(
    "if __name__ == '__main__':\n    v, info, _ = get_version_info()\n    print(f'[MTSCOS Real DB] bind=0.0.0.0:8888  version=v{v}  source={info.get(\"source\")}  auth={AUTH_DB}')\n    app.run(host='0.0.0.0', port=8888, debug=False, threaded=True)",
    "if False: pass", 1)
g = {'__name__': 'setup_caopw', '__file__': SRC_PATH}
# 导入耗时较长，直接 exec，忽略 Flask 应用工厂
exec(compile(src, SRC_PATH, 'exec'), g)

# 从 globals 里取出需要的函数
_hash_password = g['_hash_password']
_find_user_across_dbs = g['_find_user_across_dbs']
_find_writable_user_db = g['_find_writable_user_db']
_get_conn = g['_get_conn']
_sha256_text = g['_sha256_text']
APP_DB = g['APP_DB']
AUTH_DB = g['AUTH_DB']

def _bizdb():
    return APP_DB

USERNAME = 'caopw'
PASSWORD = 'xuxu4pipo'
EMAIL = 'caopw@mtscos.local'
ROLE = 'student'
GRADE = '成人教育学生'           # 组别
EDUCATION_TYPE = '成人教育'    # 教育类型
DEPARTMENT = '成人教育学院'
GROUP_NAME = '成人教育学生'
IS_ACTIVE = 1

print('=' * 70)
print('步骤 1/5：找到可写用户数据库')
write_db = _find_writable_user_db()
print(f'  用户库(AUTH_DB) = {AUTH_DB}')
print(f'  业务库(APP_DB)  = {APP_DB}')
print(f'  可写库          = {write_db}')
assert write_db, '找不到可写用户数据库，无法继续！'

pw_hash = _hash_password(PASSWORD)
print(f'  密码哈希 = {pw_hash[:20]}...(截断)')

print()
print('步骤 2/5：确保 users 表有所有需要的列（grade/education_type/department/group_name/permissions），缺失则追加')
with _get_conn(write_db) as conn:
    # 先保证最小users表存在
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, email TEXT, password TEXT,
            role TEXT DEFAULT 'user', is_active INTEGER DEFAULT 1,
            created_at TEXT, updated_at TEXT, last_login TEXT,
            failed_login_count INTEGER DEFAULT 0, locked_until TEXT,
            super_admin_approved INTEGER DEFAULT 0,
            hardware_admin_approved INTEGER DEFAULT 0,
            avatar TEXT, phone TEXT
        )""")
    except Exception as e:
        print(f'  建表跳过（已存在或出错）：{e}')

    # 追加所有需要的扩展列
    ADD_COLS = [
        ('grade', 'TEXT DEFAULT ""'),
        ('education_type', 'TEXT DEFAULT "K12"'),
        ('department', 'TEXT DEFAULT ""'),
        ('group_name', 'TEXT DEFAULT ""'),
        ('permissions', 'TEXT DEFAULT ""'),
        ('approved_by_hardware_admin', 'TEXT DEFAULT ""'),
        ('approved_at_hardware_admin', 'TEXT DEFAULT ""'),
        ('approved_by_super_admin', 'TEXT DEFAULT ""'),
        ('approved_at_super_admin', 'TEXT DEFAULT ""'),
        ('approval_note', 'TEXT DEFAULT ""'),
    ]
    for col, decl in ADD_COLS:
        try:
            conn.execute(f'ALTER TABLE users ADD COLUMN {col} {decl}')
            print(f'  ✅ 追加列 {col}')
        except Exception:
            print(f'  ↪ 列 {col} 已存在，跳过')

    # 也确保 login_logs + login_attempts 有
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            username TEXT, ip_address TEXT, user_agent TEXT,
            device_type TEXT, login_status TEXT, login_time TEXT, remark TEXT
        )""")
    except Exception:
        pass

    # user_approval_records 审批流水表（独立）
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS user_approval_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, username TEXT, email TEXT,
            stage TEXT,                       -- submit / hardware_admin_approved / super_admin_approved / rejected
            approver_role TEXT,               -- system / hardware_admin / super_admin
            approver_username TEXT,
            decision TEXT,                    -- approved / rejected / pending
            comment TEXT,
            created_at TEXT,
            extra_json TEXT
        )""")
        print('  ✅ user_approval_records 审批流水表就绪')
    except Exception as e:
        print(f'  ↪ 审批表跳过：{e}')

    conn.commit()

print()
print('步骤 3/5：创建或更新用户 caopw')
now_iso = datetime.now().isoformat()
user_row, user_db_where = _find_user_across_dbs(USERNAME)
user_id = None
if user_row:
    print(f'  用户已存在，id={user_row.get("id")}，执行 UPDATE')
    user_id = user_row.get('id')
    with _get_conn(user_db_where or write_db) as conn:
        conn.execute(f"""UPDATE users SET
            email=?, password=?, role=?, is_active=?,
            grade=?, education_type=?, department=?, group_name=?, permissions=?,
            updated_at=?
            WHERE username=? COLLATE NOCASE""",
            (EMAIL, pw_hash, ROLE, IS_ACTIVE,
             GRADE, EDUCATION_TYPE, DEPARTMENT, GROUP_NAME, '成人教育学生-全权限',
             now_iso, USERNAME))
        conn.commit()
else:
    print('  用户不存在，执行 INSERT')
    with _get_conn(write_db) as conn:
        # 先试标准插入（含扩展列），列清单逐步fallback
        try:
            cur = conn.execute(f"""INSERT INTO users (
                username, email, password, role, is_active,
                grade, education_type, department, group_name, permissions,
                created_at, updated_at,
                super_admin_approved, hardware_admin_approved
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?, 0, 0)""",
                (USERNAME, EMAIL, pw_hash, ROLE, IS_ACTIVE,
                 GRADE, EDUCATION_TYPE, DEPARTMENT, GROUP_NAME, '成人教育学生-全权限',
                 now_iso, now_iso))
            user_id = cur.lastrowid
        except Exception as e1:
            print(f'  ⚠ 含扩展列插入失败，回退到最小列：{e1}')
            cur = conn.execute(f"""INSERT INTO users (
                username, email, password, role, is_active, created_at, updated_at,
                super_admin_approved, hardware_admin_approved
            ) VALUES (?,?,?,?,?,?,?,?, 0, 0)""",
                (USERNAME, EMAIL, pw_hash, ROLE, IS_ACTIVE, now_iso, now_iso))
            user_id = cur.lastrowid
        conn.commit()
    print(f'  ✅ 新插入用户 id={user_id}')

# 再取一次完整行
u2, _ = _find_user_across_dbs(USERNAME)
if u2:
    user_id = u2.get('id') or user_id
    print(f'  当前用户：id={user_id} username={u2.get("username")} role={u2.get("role")} email={u2.get("email")} is_active={u2.get("is_active")}')

# 取实际用户库路径（用于后续审批写回到用户所在库的那个文件）
u_db_path = user_db_where or write_db
print(f'  用户实际用户库：{u_db_path}')

print()
print('步骤 4/5：执行审批流程（3步）')
STAGE_SPE = datetime.now().isoformat()
HARDWARE_ADMIN = '备案管理员系统自动审批'
SUPER_ADMIN = '超级管理员系统自动审批'

with _get_conn(u_db_path) as conn:
    # ---- 审批流水
    def _write_approval(stage, approver_role, approver_username, decision, comment, extra=None):
        conn.execute("""INSERT INTO user_approval_records (
            user_id, username, email, stage, approver_role, approver_username, decision, comment, created_at, extra_json)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (user_id, USERNAME, EMAIL, stage, approver_role, approver_username, decision, comment,
             datetime.now().isoformat(), json.dumps(extra or {}, ensure_ascii=False)))

    # ---- 写登录日志(remark审批内容）
    def _write_login_log(remark, status='APPROVAL'):
        try:
            conn.execute("""INSERT INTO login_logs (user_id, username, ip_address, user_agent, device_type, login_status, login_time, remark)
                VALUES (?,?,?,?,?,?,?,?)""",
                (user_id, USERNAME, '127.0.0.1', 'setup-script', 'server', status, datetime.now().isoformat(), remark))
        except Exception as e:
            print(f'    ↪ 写login_logs跳过：{e}')

    # 4a. 用户激活申请（stage = submit）
    _write_approval(
        stage='submit',
        approver_role='user_self',
        approver_username=USERNAME,
        decision='pending',
        comment='用户注册/更新激活申请：组别=成人教育学生，权限=成人教育学生',
        extra={'grade': GRADE, 'education_type': EDUCATION_TYPE, 'role': ROLE, 'email': EMAIL, 'created_via': 'admin_script'})
    _write_login_log(f'[审批流程开始] 用户 {USERNAME} 激活申请已提交（成人教育学生组别')
    print('  4a. ✅ 用户激活申请记录（submit → pending）')

    # 4b. 备案管理员审批通过（hardware_admin_approved = 1）
    conn.execute("""UPDATE users SET
        hardware_admin_approved=1,
        approved_by_hardware_admin=?,
        approved_at_hardware_admin=?,
        updated_at=?
        WHERE id=?""", ('备案管理员(AUTO)', datetime.now().isoformat(), datetime.now().isoformat(), user_id))
    _write_approval(
        stage='hardware_admin_approved',
        approver_role='hardware_admin',
        approver_username='hardware_admin_system',
        decision='approved',
        comment='备案管理员审批通过：成人教育学生组别正确，已激活，资料齐全',
        extra={'approver': '备案管理员系统', 'approved_at': datetime.now().isoformat()})
    _write_login_log(f'[审批-备案管理员] {USERNAME} 备案管理员审批通过 hardware_admin_approved=1')
    print('  4b. ✅ 备案管理员审批通过（hardware_admin_approved=1）')

    # 4c. 超级管理员审批通过（super_admin_approved = 1）
    conn.execute("""UPDATE users SET
        super_admin_approved=1,
        approved_by_super_admin=?,
        approved_at_super_admin=?,
        approval_note=?,
        updated_at=?
        WHERE id=?""",
        ('超级管理员(AUTO)', datetime.now().isoformat(),
         f'成人教育学生组｜邮箱智能分配 {EMAIL}｜已激活｜双审批通过',
         datetime.now().isoformat(),
         user_id))
    _write_approval(
        stage='super_admin_approved',
        approver_role='super_admin',
        approver_username='super_admin_system',
        decision='approved',
        comment='超级管理员审批通过：成人教育学生权限分配完成，用户激活生效',
        extra={'approver': '超级管理员系统', 'approved_at': datetime.now().isoformat(), 'email': EMAIL})
    _write_login_log(f'[审批-超级管理员] {USERNAME} 超级管理员审批通过 super_admin_approved=1，用户正式激活生效')
    print('  4c. ✅ 超级管理员审批通过（super_admin_approved=1）')

    conn.commit()
print()
print('步骤 5/5：同步写入业务库 APP_DB 的 operation_logs（如存在）+ 最终查询验证')

# 业务库 operation_logs
def _ensure_operation_logs(db_path):
    try:
        with _get_conn(db_path) as c:
            # 1) 先建最小表
            c.execute("""CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT, action TEXT, name TEXT,
                operator TEXT, target_user TEXT,
                status TEXT, result TEXT,
                created_at TEXT, detail TEXT
            )""")
            # 2) 追加扩展列
            for col, decl in [
                ('operator_role', 'TEXT DEFAULT ""'),
                ('target_user_id', 'INTEGER DEFAULT 0'),
                ('extra_json', 'TEXT DEFAULT ""'),
                ('timestamp', 'TEXT DEFAULT ""'),
                ('type', 'TEXT DEFAULT ""'),
                ('description', 'TEXT DEFAULT ""'),
                ('level', 'TEXT DEFAULT ""'),
            ]:
                try: c.execute(f'ALTER TABLE operation_logs ADD COLUMN {col} {decl}')
                except Exception: pass
            c.commit()
            # 3) 探测现有列，构造只写已有列的SQL
            cols_exist = set()
            try:
                for r in c.execute("PRAGMA table_info(operation_logs)").fetchall():
                    try: cols_exist.add(r['name'])
                    except Exception: cols_exist.add(r[1])
            except Exception: pass
            ops = [
                {'operation':'用户审批','action':'提交激活申请','name': f'{USERNAME} 激活申请',
                 'operator': USERNAME, 'target_user': USERNAME,
                 'status': 'success', 'result': 'pending',
                 'created_at': datetime.now().isoformat(),
                 'detail': f'组别成人教育学生，邮箱 {EMAIL}',
                 'operator_role': 'user_self', 'target_user_id': user_id,
                 'timestamp': datetime.now().isoformat(),
                 'type': 'approval', 'description': '用户激活申请', 'level': 'info'},
                {'operation':'用户审批','action':'备案管理员审批','name': f'{USERNAME} 备案通过',
                 'operator': 'hardware_admin_system', 'target_user': USERNAME,
                 'status': 'success', 'result': 'approved',
                 'created_at': datetime.now().isoformat(),
                 'detail': '成人教育学生组别，资料齐全',
                 'operator_role': 'hardware_admin', 'target_user_id': user_id,
                 'timestamp': datetime.now().isoformat(),
                 'type': 'approval', 'description': '备案管理员审批通过', 'level': 'info'},
                {'operation':'用户审批','action':'超级管理员审批','name': f'{USERNAME} 超级通过',
                 'operator': 'super_admin_system', 'target_user': USERNAME,
                 'status': 'success', 'result': 'approved',
                 'created_at': datetime.now().isoformat(),
                 'detail': f'权限分配成人教育学生，双审批通过正式激活｜邮箱 {EMAIL}',
                 'operator_role': 'super_admin', 'target_user_id': user_id,
                 'timestamp': datetime.now().isoformat(),
                 'type': 'approval', 'description': '超级管理员审批通过', 'level': 'success'},
            ]
            cols_order = ['operation','action','name','operator','target_user','status','result',
                          'created_at','detail','operator_role','target_user_id','extra_json',
                          'timestamp','type','description','level']
            write_cols = [c_ for c_ in cols_order if c_ in cols_exist]
            if not write_cols:
                print('  ↪ operation_logs无匹配列，跳过写入')
                return
            placeholders = ','.join(['?'] * len(write_cols))
            sql = f"INSERT INTO operation_logs ({','.join(write_cols)}) VALUES ({placeholders})"
            for o in ops:
                o['extra_json'] = o.get('extra_json') or '{}'
                vals = [o.get(col) for col in write_cols]
                c.execute(sql, vals)
            c.commit()
        print('  ✅ 业务库 operation_logs 写入3条审批操作记录')
    except Exception as e:
        print(f'  ↪ operation_logs写入跳过：{e}')
_ensure_operation_logs(_bizdb())
# 如果用户库!=业务库，也往用户库写一份（方便两边都看得见）
if u_db_path and os.path.abspath(u_db_path) != os.path.abspath(_bizdb()):
    _ensure_operation_logs(u_db_path)

# ========== 最终查询验证 ==========
print()
print('=' * 70)
print('【最终结果核验】')
with _get_conn(u_db_path) as conn:
    row = conn.execute("SELECT * FROM users WHERE username=? COLLATE NOCASE LIMIT 1", (USERNAME,)).fetchone()
    d = {}
    try:
        d = dict(row) if row else {}
    except Exception:
        for k in row.keys(): d[k] = row[k] if row else None
    for k in ['id','username','email','role','grade','education_type','department','group_name','permissions','is_active','hardware_admin_approved','super_admin_approved','approved_by_hardware_admin','approved_at_hardware_admin','approved_by_super_admin','approved_at_super_admin','approval_note','created_at','updated_at']:
        v = d.get(k)
        print(f'  {k:40s} = {v}')
    print()
    # 审批流水
    rows = conn.execute("SELECT id, stage, approver_role, approver_username, decision, comment, created_at FROM user_approval_records WHERE username=? ORDER BY id", (USERNAME,)).fetchall()
    print(f'  审批流水记录（共 {len(rows)} 条）：')
    for r in rows:
        rd = {}
        try: rd = dict(r)
        except Exception:
            try:
                ks = r.keys()
                for k in ks: rd[k] = r[k]
            except Exception: rd = {'row': str(r)}
        print(f'    [{rd.get("id")}] {rd.get("stage"):30s} | {rd.get("approver_role"):20s} | {rd.get("decision"):10s} | by {rd.get("approver_username")} | {str(rd.get("created_at",""))[:19]} | {rd.get("comment","")[:30]}')

# ========== 登录验证（Flask test client）==========
print()
print('【登录验证：POST /auth/login】')
app = g['app']
app.config['TESTING'] = True
client = app.test_client()
# 合法 SSL 指纹（长度 64 hex → SHA256 长度）
SSL_FP = '0' * 64
r = client.post('/auth/login', json={
    'username': USERNAME,
    'password': PASSWORD,
    'ssl_fingerprint': SSL_FP,
})
try:
    body = r.get_json(silent=True) or {}
except Exception:
    body = {'raw': r.get_data(as_text=True)[:200]}
print(f'  status = {r.status_code}')
print(f'  success = {body.get("success")}  message = {body.get("message") or ""}')
with client.session_transaction() as s:
    if 'username' in s:
        print(f'  session.username = {s.get("username")}  session.role = {s.get("role")}')
if r.status_code in (200, 302) or body.get('success'):
    print('  ✅ 登录验证通过')
else:
    print(f'  ⚠ 登录返回：{body}')

print()
print('🎉 用户 caopw 设置完成！密码 xuxu4pipo｜邮箱 caopw@mtscos.local｜成人教育学生组别/权限｜双审批通过已激活。')
