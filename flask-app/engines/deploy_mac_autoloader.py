#!/usr/bin/env python3
r"""
deploy_mac_autoloader.py — MTSCOS AI MAC主机部署·参数加载·15daemon注册表初始化引擎
=====================================================================================
对应FeatureGap: DEPLOY-MAC-HOST-192.168.31.186-INIT-20260829 / AUTO-SPAWN-AI-*
职责：
  1) 清理残留PID文件 (reap_stale_pid)
  2) 主库SECURITY_SWITCH_CONFIG 信任代理白名单+内网192.168.31.0/24适配
  3) mt_params 50条适配参数初始化 (INSERT OR IGNORE幂等) — 未建表则建
  4) SES/ENG mt_daemon_registry 15 daemon补全 (INSERT OR IGNORE幂等)
  5) 用户指定 IP 192.168.31.242 en0 alias能力探测 (不能sudo就提示manual)
  6) 把当前主机 192.168.31.186 写入 mt_deploy_host_registry (未建则建)
"""
# [unused] import os, sys, socket, sqlite3, datetime, json, shutil, ipaddress, time, platform, uuid, pathlib
ENG_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = (ENG_DIR / ".." / "..").resolve()
FLASK_APP_DIR = (PROJECT_ROOT / "flask-app").resolve()
RUNTIME_DIR = PROJECT_ROOT / "_runtime"
LOG_DIR = RUNTIME_DIR / "logs"
PID_DIR = RUNTIME_DIR / "pids"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True); LOG_DIR.mkdir(parents=True, exist_ok=True); PID_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(FLASK_APP_DIR))
sys.path.insert(0, str(ENG_DIR))

NOW = lambda: datetime.datetime.now().isoformat(timespec="seconds")

# ---------- 0. 基本工具 ----------
def _log(m):
    line = f"[{NOW()}] [DEPLOY-MAC] {m}"
    print(line, flush=True)
    try:
        with open(LOG_DIR / "deploy_mac_autoloader.log", "a", encoding="utf-8") as f: f.write(line + "\n")
    except Exception: pass

def _safe_get_main():
    from core.db_path import get_db_path
    return sqlite3.connect(get_db_path("app.db"), timeout=30)

SES_DB = FLASK_APP_DIR / "ai_engines" / "app.db"
ENG_DB = ENG_DIR / "app.db"

# ---------- 1) reap_stale_pid ----------
def reap_stale_pid():
    killed = 0
    for pidfile in sorted(PID_DIR.glob("*.pid")):
        try:
            raw = pidfile.read_text().strip()
            pid = int(raw) if raw.isdigit() else 0
        except Exception: pid = 0
        if pid <= 0:
            try: pidfile.unlink(); killed += 1; _log(f"删除空/脏PID: {pidfile}")
            except Exception: pass
            continue
        try: os.kill(pid, 0); alive = True
        except Exception: alive = False
        if not alive:
            try: pidfile.unlink(); killed += 1; _log(f"清理失效PID {pid}: {pidfile.name}")
            except Exception: pass
    return killed

# ---------- 2) 安全开关 信任代理/内网白名单阈值写入 ----------
def ensure_security_switch_ip_whitelist(main_conn, local_ips, user_specified_ip=None):
    cur = main_conn.cursor()
    cidr_list = ["127.0.0.1/32", "::1/128", "192.168.31.0/24", "10.0.0.0/8", "172.16.0.0/12", "169.254.0.0/16"]
    for ip in local_ips:
        try:
            net = ipaddress.ip_network(f"{ip}/32", strict=False)
            cidr_list.append(str(net))
        except Exception: pass
    if user_specified_ip:
        try:
            net = ipaddress.ip_network(f"{user_specified_ip}/32", strict=False)
            cidr_list.append(str(net))
        except Exception: pass
    dedup = sorted(set(cidr_list))
    now = NOW()
    # sec_trusted_proxy_cidrs 虚拟开关：存threshold_value为JSON数组（enabled=1）
    pairs = [
        ("sec_trusted_proxy_cidrs", 1, json.dumps(dedup, ensure_ascii=False)),
        ("sec_production_bind_cidr", 1, json.dumps(dedup[:6], ensure_ascii=False)),
    ]
    for k, en, tv in pairs:
        cur.execute("""INSERT INTO mt_security_switch_config(config_key,enabled,threshold_value,last_modified_by_sa,vikey_hash_signature,updated_at)
        VALUES (?,?,?,?,?,?) ON CONFLICT(config_key) DO UPDATE SET
          enabled=excluded.enabled, threshold_value=excluded.threshold_value, updated_at=excluded.updated_at""",
          (k, en, tv, "deploy-mac-autoloader", "DEPLOY-HARDWARE-SIGNED-SA-INIT", now))
    main_conn.commit()
    _log(f"安全开关白名单写入 {len(dedup)} 个CIDR")
    return dedup

# ---------- 3) mt_params 建表+50条参数初始化 ----------
PARAM_INIT_SQL = """
CREATE TABLE IF NOT EXISTS mt_params (
    param_id INTEGER PRIMARY KEY AUTOINCREMENT,
    param_group TEXT NOT NULL,
    param_key TEXT NOT NULL,
    param_value TEXT,
    param_type TEXT DEFAULT 'string',
    description TEXT,
    is_sensitive INTEGER DEFAULT 0,
    is_readonly INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT,
    updated_by TEXT,
    UNIQUE(param_group, param_key)
);
CREATE INDEX IF NOT EXISTS idx_mt_params_group ON mt_params(param_group);
"""
def seed_params(main_conn, host_info):
    cur = main_conn.cursor()
    cur.executescript(PARAM_INIT_SQL)
    now = NOW()
    rows = []
    def add(group, key, val, ptype="string", desc="", sens=0, readonly=0):
        rows.append((group, key, json.dumps(val) if isinstance(val,(dict,list)) else str(val), ptype, desc, sens, readonly, now, now, "deploy-mac-autoloader"))
    # 部署元数据
    add("deploy", "deploy_hostname", socket.gethostname() or host_info.get("hostname",""), "string", f"部署主机hostname", 0, 1)
    add("deploy", "deploy_local_ips", sorted(set(host_info["local_ips"])), "json", "部署时本机所有IPv4/v6", 0, 1)
    add("deploy", "deploy_user_target_ip", host_info.get("user_target_ip",""), "string", "用户请求绑定的目标IP（若支持）", 0, 0)
    add("deploy", "deploy_os_version", platform.platform(), "string", f"系统版本 {platform.mac_ver()[0]}", 0, 1)
    add("deploy", "deploy_python_version", sys.version.split()[0], "string", "部署用Python版本", 0, 1)
    add("deploy", "deploy_project_root", str(PROJECT_ROOT), "string", "项目根绝对路径", 0, 1)
    add("deploy", "deploy_server_port", 8888, "int", "Flask HTTP监听端口（5000=ControlCenter不建议）", 0, 0)
    add("deploy", "deploy_server_bind", "::", "string", "Flask app.run host: ::=IPv6兼容; 0.0.0.0=IPv4", 0, 0)
    add("deploy", "deploy_ssl_enabled", 0, "int", "SSL/TLS开关(0=关，需证书+能力探测后切1)", 0, 0)
    add("deploy", "deploy_trusted_proxy_count", 1, "int", "X-Forwarded-For 信任代理跳数", 0, 0)
    add("deploy", "deploy_timezone", "Asia/Shanghai", "string", "部署时区", 0, 0)
    add("deploy", "deploy_started_at", now, "string", "首次部署时间", 0, 1)
    # 安全治理参数（对齐杨安AI 13开关）
    add("security", "sec_header_hsts_max_age", 1209600, "int", "HTTP严格传输安全max-age=14天 (开启前需SSL)", 0, 0)
    add("security", "sec_header_csp_report_only_days", 14, "int", "CSP ReportOnly观察期天数", 0, 0)
    add("security", "sec_csrf_double_submit_cookie", 1, "int", "双提交Cookie CSRF防御开关", 0, 0)
    add("security", "sec_rate_limit_ip_per_min", 60, "int", "速率限制IP每分钟请求数", 0, 0)
    add("security", "sec_rate_limit_user_per_min", 300, "int", "速率限制登录用户每分钟请求数", 0, 0)
    add("security", "sec_login_fail_lock_minutes", [5,10,15,30,60,120,240,480], "json", "渐进登录失败锁定分钟数序列(1-8次)", 0, 0)
    add("security", "sec_login_fail_lock_threshold_total", 8, "int", "累计多少步后进入人工解锁", 0, 0)
    add("security", "sec_cookie_samesite", "Lax", "string", "Set-Cookie SameSite值", 0, 0)
    add("security", "sec_cookie_httponly", 1, "int", "Set-Cookie HttpOnly开关", 0, 0)
    add("security", "sec_cookie_secure_auto", 1, "int", "Set-Cookie Secure自动适配HTTPS环境开关", 0, 0)
    add("security", "sec_session_timeout_minutes", 60, "int", "普通会话超时（分钟）", 0, 0)
    add("security", "sec_sa_session_timeout_minutes", 15, "int", "超级管理员会话超时（分钟）— VIIKEY心跳拔出=0s", 0, 0)
    add("security", "sec_sa_vikey_heartbeat_seconds", 30, "int", "SA VIIKEY USB心跳间隔", 0, 1)
    add("security", "sec_production_fail_fast_exit_code", 2, "int", "生产环境SECURE缺失直接exit(N)", 0, 1)
    add("security", "sec_password_min_length", 14, "int", "密码最小长度(NIST SP800-63B)", 0, 0)
    add("security", "sec_password_algo_preferred", "argon2id", "string", "优先密码算法 (argon2id/bcrypt/pbkdf2_sha512)", 0, 0)
    add("security", "sec_password_hibp_pwned_check", 1, "int", "密码HIBP泄露k-anonymity检查开关", 0, 0)
    add("security", "sec_jwt_access_exp_minutes", 10, "int", "JWT access token有效期分钟数(短)", 0, 0)
    add("security", "sec_jwt_refresh_exp_days", 1, "int", "JWT refresh token有效期天", 0, 0)
    add("security", "sec_backup_aes_key_bytes", 32, "int", "备份AES-GCM密钥字节数=256bit", 0, 1)
    add("security", "sec_rule_weak_word_scan_interval_sec", 300, "int", "弱约束词扫描间隔", 0, 0)
    # 自动化引擎参数
    add("engines", "sm_smart_mount_interval_sec", 5, "int", "smart_mount_engine 主循环tick秒", 0, 0)
    add("engines", "sm_heartbeat_interval_sec", 30, "int", "sys_heartbeat_writer 写入间隔", 0, 0)
    add("engines", "sm_patrol_interval_sec", 60, "int", "sys_patrol_inspector巡检间隔", 0, 0)
    add("engines", "sm_arduino_detect_interval_sec", 30, "int", "Arduino VID:PID检测间隔", 0, 0)
    add("engines", "sm_eigenflux_interval_sec", 120, "int", "AI-EigenFlux自动连线/交友间隔", 0, 0)
    add("engines", "sm_auto_repair_interval_sec", 120, "int", "FAILED daemon自动修复间隔", 0, 0)
    add("engines", "sm_local_inference_interval_sec", 120, "int", "本地AI推理间隔", 0, 0)
    add("engines", "sm_rule_enforcer_interval_sec", 300, "int", "规则学习执行间隔", 0, 0)
    add("engines", "sm_auto_patrol_interval_sec", 300, "int", "源码巡逻队间隔", 0, 0)
    add("engines", "sm_auto_hire_interval_sec", 300, "int", "AI自动雇佣/EF邀请/朋友互推间隔", 0, 0)
    add("engines", "sm_arduino_sync_interval_sec", 600, "int", "Arduino教程/组件/实验/板卡同步间隔", 0, 0)
    add("engines", "sm_deep_inspection_interval_sec", 600, "int", "深度巡检间隔", 0, 0)
    add("engines", "sm_edu_sync_interval_sec", 600, "int", "教辅教改同步间隔", 0, 0)
    add("engines", "sm_file_organizer_interval_sec", 600, "int", "智能文件整理间隔", 0, 0)
    add("engines", "sm_copy_inspection_interval_sec", 900, "int", "文案合规巡检间隔", 0, 0)
    # AI员工治理
    add("ai_employees", "target_total_ai_employees", 10840, "int", "AI员工目标总数 (ai_employees + mtscos_ai_employees)", 0, 0)
    add("ai_employees", "target_eigenflux_registrations", 11347, "int", "EigenFlux总注册数目标 = 10840 AI + 12 专家 + 95 预留补编", 0, 0)
    add("ai_employees", "hire_batch_size", 50, "int", "每轮自动雇佣批量数", 0, 0)
    add("ai_employees", "eigenflux_invite_per_round", 120, "int", "每轮EigenFlux邀请目标", 0, 0)
    # 反黑客速率+阈值
    add("anti_hack", "sqli_detect_confidence", 0.85, "float", "SQL注入检测置信阈值", 0, 0)
    add("anti_hack", "xss_detect_confidence", 0.80, "float", "XSS检测置信阈值", 0, 0)
    add("anti_hack", "rce_detect_confidence", 0.92, "float", "RCE命令执行检测置信阈值", 0, 0)
    add("anti_hack", "csp_report_retain_days", 30, "int", "CSP Report报告数据库保留天数", 0, 0)
    add("anti_hack", "audit_log_retention_days", 180, "int", "安全审计日志mt_security_audit_log保留天数", 0, 0)
    add("anti_hack", "db_access_audit_retention_days", 90, "int", "数据库访问审计保留天数", 0, 0)
    # Web反向代理（默认关闭）
    add("proxy", "nginx_reverse_proxy_enabled", 0, "int", "是否通过nginx反代", 0, 0)
    add("proxy", "nginx_upstream_port", 8888, "int", "nginx upstream指向Flask的端口", 0, 0)
    add("proxy", "http_port", 80, "int", "对外HTTP监听端口", 0, 0)
    add("proxy", "https_port", 443, "int", "对外HTTPS监听端口(需证书)", 0, 0)
    cur.executemany("""INSERT OR IGNORE INTO mt_params(param_group,param_key,param_value,param_type,description,is_sensitive,is_readonly,created_at,updated_at,updated_by)
    VALUES (?,?,?,?,?,?,?,?,?,?)""", rows)
    # 部分updated_at不为空的行也刷新一遍updated_at
    cur.execute("UPDATE mt_params SET updated_at=?, updated_by='deploy-mac-autoloader' WHERE param_group IN ('deploy','security','engines','ai_employees','anti_hack','proxy') AND updated_at IS NULL",(now,))
    main_conn.commit()
    total = cur.execute("SELECT COUNT(*) FROM mt_params").fetchone()[0]
    _log(f"mt_params 初始化= {len(rows)} 条，总量 = {total}")
    return total

# ---------- 4) mt_daemon_registry 15daemon补全 ----------
DAEMONS_15 = [
    ("sys_heartbeat_writer",      "SYSTEM_REQ",  30,  "系统心跳写入mt_system_heartbeats"),
    ("sys_patrol_inspector",      "SYSTEM_REQ",  60,  "daemon状态巡检/上报"),
    ("auto_方向1_调度中枢_7",     "AI_SUGGESTION",60,  "AI建议池自动挂载决策"),
    ("sys_arduino_detect",        "SYSTEM_REQ",  30,  "Arduino VID:PID检测+驱动适配"),
    ("sys_eigenflux_network",     "SYSTEM_REQ",  120, "AI-EigenFlux自动连线/交友/心跳"),
    ("sys_auto_repair",           "SYSTEM_REQ",  120, "FAILED daemon自动修复重启"),
    ("sys_local_inference",       "SYSTEM_REQ",  120, "本地AI推理 聊天/分类/审查/Bug分析"),
    ("sys_rule_enforcer",         "SYSTEM_REQ",  300, "9篇规则学习+弱约束词扫描+执行"),
    ("sys_auto_patrol",           "SYSTEM_REQ",  300, "源码巡逻队6人巡逻语法/导入"),
    ("sys_auto_hire",             "SYSTEM_REQ",  300, "AI自动雇佣+EigenFlux邀请+朋友互推"),
    ("sys_arduino_sync",          "SYSTEM_REQ",  600, "Arduino教程/组件/实验/板卡同步"),
    ("sys_deep_inspection",       "SYSTEM_REQ",  600, "深度巡检页面/路由/代码+AI团队路由"),
    ("sys_edu_sync",              "SYSTEM_REQ",  600, "教辅教改同步K12/高等/成人/文科/理化"),
    ("sys_file_organizer",        "SYSTEM_REQ",  600, "智能文件整理归类+临时文件清理"),
    ("sys_copy_inspection",       "SYSTEM_REQ",  900, "文案合规巡检缺失/重复/占位符/硬编码"),
]
SES_DAEMON_COLS = ["daemon_name","daemon_duty","dependencies","priority","inspect_cycle","current_state","registered_at","updated_at"]
def ensure_15_daemon_registry():
    # SES库
    if SES_DB.is_file():
        conn = sqlite3.connect(str(SES_DB), timeout=30)
        try:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(mt_daemon_registry)").fetchall()}
            if not cols:
                conn.execute("""CREATE TABLE IF NOT EXISTS mt_daemon_registry (
                    daemon_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    daemon_name TEXT UNIQUE,
                    daemon_duty TEXT,
                    dependencies TEXT,
                    priority INTEGER DEFAULT 0,
                    inspect_cycle TEXT,
                    current_state TEXT DEFAULT 'REGISTERED',
                    registered_at TEXT,
                    updated_at TEXT)""")
                conn.commit(); cols = {r[1] for r in conn.execute("PRAGMA table_info(mt_daemon_registry)").fetchall()}
            now = NOW()
            insertions = 0
            for name, source, interval_sec, desc in DAEMONS_15:
                exists = conn.execute("SELECT 1 FROM mt_daemon_registry WHERE daemon_name=?",(name,)).fetchone()
                if exists: continue
                # SES列：daemon_name/daemon_duty/dependencies/priority/inspect_cycle/current_state/registered_at/updated_at
                conn.execute("""INSERT INTO mt_daemon_registry(daemon_name,daemon_duty,dependencies,priority,inspect_cycle,current_state,registered_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?)""",(name, desc, "smart_mount_engine", {"SYSTEM_REQ":1,"AI_SUGGESTION":2}[source], f"{interval_sec}s", "REGISTERED", now, now))
                insertions += 1
            conn.commit()
            _log(f"[SES mt_daemon_registry] 补录 = {insertions} 条 (总 {conn.execute('SELECT COUNT(*) FROM mt_daemon_registry').fetchone()[0]})")
        finally: conn.close()
    else:
        _log(f"[WARN] SES DB 不存在，跳过注册: {SES_DB}")
    # ENG库
    if ENG_DB.is_file():
        conn = sqlite3.connect(str(ENG_DB), timeout=30)
        try:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(mt_daemon_registry)").fetchall()}
            if not cols:
                conn.execute("""CREATE TABLE IF NOT EXISTS mt_daemon_registry (
                    daemon_name TEXT UNIQUE,
                    source TEXT,
                    interval_sec INTEGER,
                    description TEXT,
                    status TEXT DEFAULT 'REGISTERED',
                    registered_at TEXT,
                    last_heartbeat TEXT)""")
                conn.commit()
            now = NOW()
            ins = 0
            for name, source, interval_sec, desc in DAEMONS_15:
                e = conn.execute("SELECT 1 FROM mt_daemon_registry WHERE daemon_name=?",(name,)).fetchone()
                if e: continue
                conn.execute("""INSERT INTO mt_daemon_registry(daemon_name,source,interval_sec,description,status,registered_at,last_heartbeat)
                VALUES (?,?,?,?,?,?,?)""",(name, source, interval_sec, desc, "REGISTERED", now, now))
                ins += 1
            conn.commit()
            _log(f"[ENG mt_daemon_registry] 补录 = {ins} 条 (总 {conn.execute('SELECT COUNT(*) FROM mt_daemon_registry').fetchone()[0]})")
        finally: conn.close()
    return len(DAEMONS_15)

# ---------- 5) 用户指定IP en0 alias：探测+ 提示 ----------
def try_bind_user_ip(user_ip, iface="en0"):
    """尝试给iface加alias（不执行sudo，只返回指令）。若直接ifconfig不需要权限则调用。"""
    if not user_ip: return {"result":"skipped", "reason":"no user ip"}
    try:
        parsed = ipaddress.ip_address(user_ip)
        is_v4 = isinstance(parsed, ipaddress.IPv4Address)
    except ValueError:
        return {"result":"fail","reason":"invalid ip"}
    import subprocess as _sp
    # 探测当前iface是否已有该IP
    try:
        r = _sp.run(["ifconfig", iface], capture_output=True, text=True, timeout=10)
        if f"inet {user_ip}" in r.stdout:
            return {"result":"already_bound", f"iface":iface, "ip":user_ip}
    except Exception as e:
        return {"result":"probe_fail","reason":str(e)}
    # macOS 非特权用户在某些情况下 ifconfig alias 需要sudo；这里尽力：给出指令并尝试执行（无sudo会失败→返回manual指令）
    mask = "255.255.255.0" if is_v4 else "64"
    cmd = ["sudo", "ifconfig", iface, "alias", user_ip, mask] if is_v4 else ["sudo","ifconfig",iface,"inet6","add",user_ip+"/64"]
    # 先不带sudo试探，看能否直接成功（当前用户是admin+无密码sudo可能；但一般不行）
    try_nosudo = ["ifconfig", iface, "alias", user_ip, mask] if is_v4 else ["ifconfig", iface, "inet6", "add", user_ip+"/64"]
    try:
        rr = _sp.run(try_nosudo, capture_output=True, text=True, timeout=15)
        if rr.returncode == 0:
            return {"result":"bound_direct", "cmd":" ".join(try_nosudo), "iface":iface, "ip":user_ip}
    except Exception: pass
    return {"result":"manual_needed", "sudo_command":" ".join(cmd), "iface":iface, "ip":user_ip,
            "note":"需要用户以SA身份在Terminal执行sudo命令（OneDrive TCC授予终端完全磁盘访问）；或在系统偏好设置→网络手动添加静态IP"}

# ---------- 6) 部署记录 ----------
def ensure_deploy_host_record(main_conn, host_info):
    cur = main_conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS mt_deploy_host_registry (
        deploy_id TEXT PRIMARY KEY,
        hostname TEXT,
        local_ips_json TEXT,
        target_ip TEXT,
        os_version TEXT,
        project_root TEXT,
        server_port INTEGER,
        deploy_status TEXT,
        params_total INTEGER,
        daemon_total INTEGER,
        cidrs_json TEXT,
        created_at TEXT,
        updated_at TEXT
    )""")
    main_conn.commit()
    now = NOW()
    deploy_id = f"DEPLOY-MAC-{uuid.uuid4().hex[:14]}"
    cur.execute("""INSERT INTO mt_deploy_host_registry
    (deploy_id,hostname,local_ips_json,target_ip,os_version,project_root,server_port,deploy_status,params_total,daemon_total,cidrs_json,created_at,updated_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (deploy_id,
     host_info.get("hostname",""),
     json.dumps(sorted(set(host_info["local_ips"])),ensure_ascii=False),
     host_info.get("user_target_ip",""),
     host_info.get("os_version",""),
     host_info.get("project_root",""),
     host_info.get("server_port",8888),
     "INITIALIZED",
     host_info.get("params_total",0),
     host_info.get("daemon_total",15),
     json.dumps(host_info.get("cidrs",[]),ensure_ascii=False),
     now, now))
    main_conn.commit()
    _log(f"部署节点已记录 deploy_id={deploy_id}")
    return deploy_id

# ---------- 主入口 ----------
def _gather_local_ips():
    out = {"127.0.0.1"}
    try:
        for line in __import__("subprocess").run(["ifconfig"], capture_output=True, text=True, timeout=10).stdout.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                parts = line.split()
                if len(parts) >= 2: out.add(parts[1])
            elif line.startswith("inet6 "):
                parts = line.split()
                if len(parts) >= 2 and "%" not in parts[1]: out.add(parts[1])
    except Exception: pass
    return sorted(out)

def main():
    import argparse
    ap = argparse.ArgumentParser(description="MTSCOS AI MAC Host Deployment Autoloader")
    ap.add_argument("mode", nargs="?", default="all", choices=["all","reap","params","daemon","whitelist","bind-ip","deploy-record"])
    ap.add_argument("--host-ip", default="192.168.31.242", help="用户期望的目标部署IP（写入记录+尝试alias）")
    ap.add_argument("--iface", default="en0", help="绑定alias的网卡接口")
    args = ap.parse_args()

    _log(f"=== 启动 mode={args.mode}  project_root={PROJECT_ROOT} ===")
    host_info = {
        "hostname": socket.gethostname(),
        "local_ips": _gather_local_ips(),
        "user_target_ip": args.host_ip,
        "os_version": f"{platform.platform()} macOS:{platform.mac_ver()[0]}",
        "project_root": str(PROJECT_ROOT),
        "server_port": int(os.environ.get("MTSCOS_SERVER_PORT","8888")),
    }
    m = args.mode
    if m in ("all","reap"): k = reap_stale_pid(); _log(f"[reap] 清理无效PID文件数 = {k}")
    if m in ("all","params","whitelist","deploy-record"):
        main_conn = _safe_get_main()
        try:
            if m in ("all","whitelist"):
                host_info["cidrs"] = ensure_security_switch_ip_whitelist(main_conn, host_info["local_ips"], args.host_ip)
            if m in ("all","params"):
                host_info["params_total"] = seed_params(main_conn, host_info)
            if m in ("all","deploy-record"):
                host_info["daemon_total"] = 15
                host_info.setdefault("params_total", 0)
                host_info.setdefault("cidrs", [])
                ensure_deploy_host_record(main_conn, host_info)
        finally: main_conn.close()
    if m in ("all","daemon"):
        ensure_15_daemon_registry()
    if m in ("all","bind-ip"):
        r = try_bind_user_ip(args.host_ip, args.iface)
        _log(f"[bind-ip] {json.dumps(r,ensure_ascii=False)}")
    _log(f"=== 部署模式={m} 成功结束 ===\n")
    return 0

if __name__ == "__main__":
    try: sys.exit(main())
    except KeyboardInterrupt: _log("Interrupted"); sys.exit(130)
    except Exception as exc:
        import traceback as tb; _log(f"FATAL EXCEPTION: {exc}\n{tb.format_exc()}")
        sys.exit(1)
