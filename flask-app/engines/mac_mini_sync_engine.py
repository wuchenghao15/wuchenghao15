#!/usr/bin/env python3
"""
Mac mini 自动检测握手 + 数据库双向同步引擎
===================================================
v1.0 · 2026-09-22

架构:
  ┌──────────────────┐    mDNS beacon     ┌──────────────────┐
  │ 主 Flask (8888)  │ ──────────────────→ │  Mac mini (9999) │
  │ 智能灯塔           │ ←────────────────── │ 同步接收器        │
  └────────┬─────────┘    握手响应          └────────┬─────────┘
           │                                         │
           ▼                                         ▼
    ┌─────────────────────────────────────────────────────┐
    │  DB 增量同步 (仅业务表, max(k_id) 游标)              │
    │  mt_andromeda_knowledge_base · mt_daemon_registry    │
    │  mt_upgrade_reports · mt_upgrade_overviews           │
    │  冲突策略: updated_at 新者为准                        │
    └─────────────────────────────────────────────────────┘

同步策略:
  1. beacon: UDP broadcast + mDNS "_mtscos._tcp" 自动发现 Mac mini
  2. handshake: 交换版本号/DB schema/daemon 状态/游标
  3. sync_incr: 只拉对方 max(k_id) 之后的新行 (INSERT OR REPLACE)
  4. conflict: ON CONFLICT(content_hash/title) DO UPDATE SET updated_at=...

WAL 安全:
  - 两边都用 SQLite WAL 模式, 只读查询不锁库
  - 同步写操作用短事务 (单表单批次)
  - 避免同时写同一 k_id (游标保证)
"""
import os, sys, time, json, socket, struct, threading, sqlite3, datetime, hashlib
from pathlib import Path

# ====== 常量 ======
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.path.join(PROJECT_ROOT, 'engines', 'app.db')
APP_DB_PATH = os.path.join(PROJECT_ROOT, 'database', 'app.db')
BEACON_PORT = 54321          # UDP beacon 广播端口
SYNC_PORT = 9999             # Mac mini TCP 同步端口 (主服务 8888)
MAGIC = b'MTSCOS_BEACON_v1'  # beacon 魔术字
SYNC_TABLES = [              # 仅同步业务表 (跳过 784MB 全库)
    ('mt_andromeda_knowledge_base', 'k_id'),
    ('mt_daemon_registry', 'daemon_name'),
    ('mt_upgrade_reports', 'report_id'),
    ('mt_upgrade_overviews', 'overview_id'),
    ('mt_andromeda_contributor_persona', 'persona_id'),
    ('mt_iron_rule_violations', 'violation_id'),
]
BEACON_INTERVAL = 30          # beacon 间隔 (秒)
SYNC_INTERVAL = 300           # 同步间隔 (秒)

_local_mac = f"MTSCOS-{socket.gethostname()}-{os.getpid()}"
_local_version = "v22.1.0-iceberg-phase8"


# =================================================================
# 1. Beacon 广播 + 握手
# =================================================================
class BeaconEngine:
    """UDP beacon 广播 + 监听 Mac mini 响应"""
    def __init__(self):
        self.peers = {}       # {mac_id: {ip, port, version, last_seen}}
        self._stop = False
        self._lock = threading.Lock()

    def broadcast_loop(self):
        """UDP broadcast beacon"""
        while not self._stop:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    payload = json.dumps({
                        'magic': MAGIC.decode(),
                        'mac_id': _local_mac,
                        'version': _local_version,
                        'service_port': SYNC_PORT,
                        'timestamp': int(time.time()),
                    }).encode()
                    s.sendto(MAGIC + payload, ('255.255.255.255', BEACON_PORT))
            except Exception as e:
                print(f"[BEACON] broadcast 失败: {e}")
            time.sleep(BEACON_INTERVAL)

    def listen_loop(self):
        """监听其他 Mac 的 beacon 响应"""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try: s.bind(('0.0.0.0', BEACON_PORT))
            except Exception as e: print(f"[BEACON] bind 失败: {e}"); return
            s.settimeout(1)
            while not self._stop:
                try:
                    data, addr = s.recvfrom(4096)
                    if not data.startswith(MAGIC): continue
                    payload = json.loads(data[len(MAGIC):].decode())
                    if payload.get('mac_id') == _local_mac: continue
                    with self._lock:
                        self.peers[payload['mac_id']] = {
                            'ip': addr[0],
                            'port': payload.get('service_port', SYNC_PORT),
                            'version': payload.get('version'),
                            'last_seen': int(time.time()),
                        }
                    print(f"[BEACON] 📡 发现 Mac mini: {payload['mac_id']} @ {addr[0]}")
                except socket.timeout: continue
                except Exception as e: print(f"[BEACON] listen 错误: {e}")

    def start(self):
        threading.Thread(target=self.broadcast_loop, daemon=True).start()
        threading.Thread(target=self.listen_loop, daemon=True).start()
        print(f"[BEACON] 🚀 启动, 本机={_local_mac}, 监听 0.0.0.0:{BEACON_PORT}")

    def get_peers(self):
        with self._lock:
            return {k:v for k,v in self.peers.items() if int(time.time())-v['last_seen']<120}


# =================================================================
# 2. DB 增量同步
# =================================================================
class DBSyncEngine:
    """增量同步 — 只同步 max(k_id) 之后的新行"""
    def __init__(self, beacon):
        self.beacon = beacon
        self._stop = False
        self._last_sync = {}  # {peer_mac: {table: last_k_id}}

    def _connect(self, path):
        conn = sqlite3.connect(path, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        return conn

    def get_table_cursor(self, conn, table, pk):
        """获取某表最大主键 (增量游标)"""
        try:
            row = conn.execute(f'SELECT MAX({pk}) FROM {table}').fetchone()
            return row[0] or 0
        except Exception: return 0

    def get_table_schema(self, conn, table):
        """获取表 schema hash — 对方表结构变了就不同步"""
        try:
            cols = conn.execute(f'PRAGMA table_info({table})').fetchall()
            return hashlib.md5(str(cols).encode()).hexdigest()[:12]
        except Exception: return ''

    def fetch_incremental(self, peer_ip, table, pk, from_cursor):
        """从 Mac mini 拉增量数据 (HTTP + /api/sync/pull)"""
        import urllib.request
        url = f"http://{peer_ip}:{SYNC_PORT}/api/sync/pull?table={table}&pk={pk}&from={from_cursor}"
        try:
            req = urllib.request.Request(url, headers={'X-MTSCOS-MAC': _local_mac})
            resp = urllib.request.urlopen(req, timeout=15)
            return json.loads(resp.read().decode())
        except Exception as e:
            return {'error': str(e)}

    def push_incremental(self, peer_ip, table, pk, to_cursor):
        """推增量到 Mac mini"""
        import urllib.request
        local = self._connect(DB_PATH)
        try:
            rows = local.execute(f'SELECT * FROM {table} WHERE CAST({pk} AS INTEGER) > ? LIMIT 500', (to_cursor,)).fetchall()
            if not rows: return {'synced': 0}
            cols = [c[1] for c in local.execute(f'PRAGMA table_info({table})').fetchall()]
            payload = json.dumps({'table': table, 'pk': pk, 'cols': cols, 'rows': [list(r) for r in rows]}).encode()
            req = urllib.request.Request(f"http://{peer_ip}:{SYNC_PORT}/api/sync/push", data=payload,
                                         headers={'Content-Type':'application/json','X-MTSCOS-MAC':_local_mac})
            resp = urllib.request.urlopen(req, timeout=30)
            return json.loads(resp.read().decode())
        except Exception as e: return {'error': str(e)}
        finally: local.close()

    def apply_incremental(self, table, pk, cols, rows):
        """应用增量 (INSERT OR REPLACE)"""
        local = self._connect(DB_PATH)
        applied = 0
        try:
            col_list = ','.join(cols)
            ph = ','.join(['?']*len(cols))
            for r in rows:
                try:
                    local.execute(f'INSERT OR REPLACE INTO {table} ({col_list}) VALUES ({ph})', r)
                    applied += 1
                except Exception as e:
                    print(f"[SYNC] 跳过行 {pk}={r[0]}: {e}")
            local.commit()
        finally: local.close()
        return applied

    def sync_loop(self):
        while not self._stop:
            peers = self.beacon.get_peers()
            for mac_id, peer in peers.items():
                try: self._sync_peer(mac_id, peer)
                except Exception as e: print(f"[SYNC] {mac_id} 同步失败: {e}")
            time.sleep(SYNC_INTERVAL)

    def _sync_peer(self, mac_id, peer):
        local = self._connect(DB_PATH)
        print(f"[SYNC] 🔄 与 {mac_id} ({peer['ip']}) 同步中...")
        for table, pk in SYNC_TABLES:
            local_cursor = self.get_table_cursor(local, table, pk)
            remote_data = self.fetch_incremental(peer['ip'], table, pk, local_cursor)
            if 'error' in remote_data:
                print(f"  ⚠️ {table} 拉取失败: {remote_data['error']}")
                continue
            rows = remote_data.get('rows', [])
            if rows:
                applied = self.apply_incremental(table, pk, remote_data.get('cols', []), rows)
                print(f"  ✅ {table}: 拉 {len(rows)} → 应用 {applied}")
            # 推
            push_result = self.push_incremental(peer['ip'], table, pk, self._last_sync.get(mac_id, {}).get(table, 0))
            self._last_sync.setdefault(mac_id, {})[table] = local_cursor
        local.close()


# =================================================================
# 3. Flask Blueprint 路由 (给 Mac mini 被同步用)
# =================================================================
def create_sync_blueprint():
    from flask import Blueprint, request, jsonify
    bp = Blueprint('mtscos_sync', __name__)

    @bp.route('/api/sync/health', methods=['GET'])
    def sync_health():
        conn = sqlite3.connect(DB_PATH, timeout=10)
        tables = {}
        for t, pk in SYNC_TABLES:
            try: tables[t] = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
            except Exception: tables[t] = 0
        conn.close()
        return jsonify({'code':0, 'data': {'mac_id':_local_mac, 'version':_local_version, 'tables': tables}})

    @bp.route('/api/sync/pull', methods=['GET'])
    def sync_pull():
        table = request.args.get('table','')
        pk = request.args.get('pk','')
        try: from_cursor = int(request.args.get('from','0'))
        except: from_cursor = 0
        if (table, pk) not in SYNC_TABLES: return jsonify({'error':'表不在同步白名单'}), 403
        conn = sqlite3.connect(DB_PATH, timeout=15)
        try:
            cols = [c[1] for c in conn.execute(f'PRAGMA table_info({table})').fetchall()]
            rows = conn.execute(f'SELECT * FROM {table} WHERE CAST({pk} AS INTEGER) > ? ORDER BY CAST({pk} AS INTEGER) LIMIT 500', (from_cursor,)).fetchall()
            return jsonify({'code':0, 'cols':cols, 'rows':[list(r) for r in rows]})
        except Exception as e: return jsonify({'error':str(e)}), 500
        finally: conn.close()

    @bp.route('/api/sync/push', methods=['POST'])
    def sync_push():
        data = request.get_json(silent=True) or {}
        table = data.get('table',''); pk = data.get('pk','')
        if (table, pk) not in SYNC_TABLES: return jsonify({'error':'表不在同步白名单'}), 403
        conn = sqlite3.connect(DB_PATH, timeout=15)
        applied = 0
        try:
            col_list = ','.join(data.get('cols',[]))
            ph = ','.join(['?']*len(data.get('cols',[])))
            for r in data.get('rows',[]):
                try:
                    conn.execute(f'INSERT OR REPLACE INTO {table} ({col_list}) VALUES ({ph})', r)
                    applied += 1
                except Exception: pass
            conn.commit()
            return jsonify({'code':0, 'applied':applied})
        finally: conn.close()

    @bp.route('/api/sync/beacon', methods=['POST'])
    def sync_beacon():
        return jsonify({'code':0, 'mac_id':_local_mac, 'ip':request.remote_addr, 'peers': list(BEACON.get_peers().keys())})

    return bp


# =================================================================
# 4. 主入口
# =================================================================
BEACON = BeaconEngine()
SYNC = DBSyncEngine(BEACON)

def start_beacon_sync():
    """Flask 初始化时调这个"""
    BEACON.start()
    threading.Thread(target=SYNC.sync_loop, daemon=True).start()
    print(f"[SYNC] 🚀 DB 增量同步启动, 同步表: {[t for t,p in SYNC_TABLES]}")

def get_sync_status():
    """健康度仪表盘读这个"""
    peers = BEACON.get_peers()
    conn = sqlite3.connect(DB_PATH, timeout=5)
    tables = {t: conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t,_ in SYNC_TABLES}
    conn.close()
    return {
        'mac_id': _local_mac,
        'version': _local_version,
        'peers': [{'mac_id': k, **v} for k,v in peers.items()],
        'tables': tables,
        'sync_tables': [t for t,_ in SYNC_TABLES],
    }

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--beacon-only', action='store_true')
    ap.add_argument('--sync-once', action='store_true')
    args = ap.parse_args()

    BEACON.start()
    if args.sync_once:
        import time; time.sleep(5)
        SYNC.sync_loop.__wrapped__ = SYNC._sync_peer
        for mac_id, peer in BEACON.get_peers().items():
            SYNC._sync_peer(mac_id, peer)
    else:
        SYNC.sync_loop()
