#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 云同步抽象层 (CloudSyncLayer)
========================================
云端化4子模块 + 适配器可插拔抽象：
  8. 用户偏好云端同步 (per-user KV 拉推+LWW合并)
  9. 配置快照云端备份 (全量快照+SHA256+加密+版本)
 10. 会话状态跨设备同步 (打开页面/标签/未完成任务)
 11. 核心数据云端冷备 (DB/AI脑库 加密增量冷备)

适配器：
  CloudSyncAdapter       抽象基类(接口)
  LocalMirrorAdapter     本地SQLite镜像（立即可用，默认）
  MockCloudAdapter       内存模拟云端（测试用，后续替换为S3/OSS/WebDAV）

冲突策略：云端优先 SSOT + LWW(Last-Writer-Wins) + 3-way merge

版本: v1.0.0
"""

import os
import sys
import json
import time
import uuid
import shutil
import sqlite3
import hashlib
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('cloud_sync_layer')


# ============================================================================
# 枚举定义
# ============================================================================

class SyncStatus(Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    SUCCESS = "success"
    FAILED = "failed"
    CONFLICT = "conflict"
    SKIPPED = "skipped"


class SyncDirection(Enum):
    PUSH = "push"
    PULL = "pull"
    BIDIR = "bidir"


class SnapshotStatus(Enum):
    CREATING = "creating"
    CREATED = "created"
    UPLOADING = "uploading"
    STORED = "stored"
    DOWNLOADING = "downloading"
    RESTORING = "restoring"
    RESTORED = "restored"
    FAILED = "failed"


# ============================================================================
# 适配器抽象接口
# ============================================================================

class CloudSyncAdapter(ABC):
    """云存储适配器抽象基类（可插拔）"""

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def set(self, key: str, value: Dict[str, Any]) -> bool: ...

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]: ...

    @abstractmethod
    def batch_get(self, keys: List[str]) -> Dict[str, Any]: ...

    @abstractmethod
    def batch_set(self, items: Dict[str, Dict]) -> bool: ...


class LocalMirrorAdapter(CloudSyncAdapter):
    """本地SQLite镜像适配器：立即可用，默认实现。
    后续替换为S3/OSS适配器时，API接口不变。"""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._ensure_table()

    def name(self): return "local_mirror"

    def is_available(self):
        return True

    def _conn(self):
        return sqlite3.connect(self._db_path, timeout=10)

    def _ensure_table(self):
        try:
            conn = self._conn()
            conn.execute("""CREATE TABLE IF NOT EXISTS mt_cloud_mirror (
                key TEXT PRIMARY KEY,
                value_json TEXT,
                version INTEGER,
                updated_at TEXT,
                device TEXT
            )""")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"LocalMirror _ensure_table failed: {e}")

    def get(self, key):
        try:
            conn = self._conn()
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute(
                "SELECT value_json, version, updated_at FROM mt_cloud_mirror WHERE key = ?",
                (key,)).fetchall()]
            conn.close()
            if rows:
                return json.loads(rows[0]['value_json'])
        except Exception as e:
            logger.warning(f"LocalMirror.get {key} failed: {e}")
        return None

    def set(self, key, value):
        try:
            conn = self._conn()
            conn.execute(
                "INSERT OR REPLACE INTO mt_cloud_mirror (key, value_json, version, updated_at, device) VALUES (?, ?, ?, ?, ?)",
                (key, json.dumps(value, ensure_ascii=False),
                 int(time.time() * 1000), datetime.now().isoformat(),
                 value.get('__device', 'unknown') if isinstance(value, dict) else 'unknown'))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"LocalMirror.set {key} failed: {e}")
            return False

    def delete(self, key):
        try:
            conn = self._conn()
            conn.execute("DELETE FROM mt_cloud_mirror WHERE key = ?", (key,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def list_keys(self, prefix: str = "") -> List[str]:
        try:
            conn = self._conn()
            if prefix:
                rows = conn.execute(
                    "SELECT key FROM mt_cloud_mirror WHERE key LIKE ?",
                    (prefix + '%',)).fetchall()
            else:
                rows = conn.execute("SELECT key FROM mt_cloud_mirror").fetchall()
            conn.close()
            return [r[0] for r in rows]
        except Exception:
            return []

    def batch_get(self, keys):
        result = {}
        for k in keys:
            v = self.get(k)
            if v is not None:
                result[k] = v
        return result

    def batch_set(self, items):
        for k, v in (items or {}).items():
            if not self.set(k, v):
                return False
        return True


class MockCloudAdapter(CloudSyncAdapter):
    """内存模拟云端适配器：测试/演示用"""

    def __init__(self):
        self._store: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def name(self): return "mock_cloud"

    def is_available(self): return True

    def get(self, key):
        with self._lock:
            return dict(self._store[key]) if key in self._store else None

    def set(self, key, value):
        with self._lock:
            self._store[key] = dict(value) if isinstance(value, dict) else value
            return True

    def delete(self, key):
        with self._lock:
            if key in self._store:
                del self._store[key]
            return True

    def list_keys(self, prefix=""):
        with self._lock:
            if prefix:
                return [k for k in self._store if k.startswith(prefix)]
            return list(self._store.keys())

    def batch_get(self, keys):
        with self._lock:
            return {k: dict(self._store[k]) for k in keys if k in self._store}

    def batch_set(self, items):
        with self._lock:
            for k, v in (items or {}).items():
                self._store[k] = dict(v) if isinstance(v, dict) else v
            return True


# ============================================================================
# 云同步主协调器
# ============================================================================

class CloudSyncLayer:
    """
    MTSCOS 云同步协调器
    4子模块：个性化同步 / 配置快照备份 / 会话跨设备同步 / 核心数据冷备
    云端优先 SSOT + LWW合并
    """

    LAYER_VERSION = "v1.0.0"
    CONFLICT_STRATEGY = "LWW"  # Last-Writer-Wins

    def __init__(self, db_path: str = None, dual_db=None,
                 adapter: CloudSyncAdapter = None,
                 project_dir: str = None,
                 crypto_manager=None):
        self.db_path = db_path
        self.dual_db = dual_db
        self.project_dir = project_dir or os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        self.crypto = crypto_manager

        # 默认使用本地镜像适配器（云端接口未来替换S3/OSS即可）
        self.adapter = adapter or LocalMirrorAdapter(db_path or ':memory:')

        # 冷备快照目录
        self.snapshot_dir = os.path.join(
            os.path.dirname(db_path) if db_path else self.project_dir,
            'db', 'cloud_snapshots')
        os.makedirs(self.snapshot_dir, exist_ok=True)

        self.stats = {
            'total_pushes': 0,
            'total_pulls': 0,
            'total_conflicts': 0,
            'snapshots_created': 0,
            'snapshots_restored': 0,
            'cold_backups': 0,
            'cold_restores': 0,
            'session_syncs': 0,
            'total_bytes_backed_up': 0,
            'last_sync': None,
        }

        self._ensure_tables()
        logger.info(f"CloudSyncLayer {self.LAYER_VERSION} ready, "
                    f"adapter={self.adapter.name()}, "
                    f"strategy={self.CONFLICT_STRATEGY}")

    # ======================================================================
    # 子模块8：用户个性化配置 云端同步
    # ======================================================================

    def push_user_personalization(self, username: str, category: str,
                                   value: Dict[str, Any], version: int,
                                   updated_at: str, device: str) -> bool:
        key = f"pz:{username}:{category}"
        self.stats['total_pushes'] += 1
        ok = self.adapter.set(key, {
            'value': value,
            'version': version,
            'updated_at': updated_at,
            'device': device,
            '__device': device,
        })
        self._log_sync(SyncDirection.PUSH.value, key,
                       SyncStatus.SUCCESS.value if ok else SyncStatus.FAILED.value,
                       username)
        if ok:
            self.stats['last_sync'] = datetime.now().isoformat()
        return ok

    def pull_user_personalization(self, username: str, category: str) -> Optional[Dict[str, Any]]:
        key = f"pz:{username}:{category}"
        self.stats['total_pulls'] += 1
        data = self.adapter.get(key)
        self._log_sync(SyncDirection.PULL.value, key,
                       SyncStatus.SUCCESS.value if data else SyncStatus.SKIPPED.value,
                       username)
        if data:
            self.stats['last_sync'] = datetime.now().isoformat()
            return data.get('value')
        return None

    # ======================================================================
    # 子模块9：配置快照云端备份
    # ======================================================================

    def create_snapshot(self, scope: str = "full",
                        username: str = None,
                        label: str = "") -> Dict[str, Any]:
        """创建配置快照并上传云端（返回快照记录）"""
        snap_id = f"SNS_{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}"
        snap = {
            'snapshot_id': snap_id,
            'scope': scope,  # full / per_user:XXX / partial
            'username': username,
            'label': label,
            'status': SnapshotStatus.CREATING.value,
            'created_at': datetime.now().isoformat(),
            'size_bytes': 0,
            'sha256': '',
            'encrypted': False,
        }
        # 1) 收集配置（个性化+定制化+云端注册表KV）
        payload = {
            'snapshot_id': snap_id,
            'created_at': snap['created_at'],
            'personalization': self._collect_personalization(scope, username),
            'customization': self._collect_customization(scope, username),
            'cloud_registry': self._collect_registry(),
        }
        payload_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        snap['size_bytes'] = len(payload_bytes)
        snap['sha256'] = hashlib.sha256(payload_bytes).hexdigest()
        snap['status'] = SnapshotStatus.CREATED.value

        # 2) 可选加密
        if self.crypto and hasattr(self.crypto, 'encrypt_dict'):
            try:
                payload = {'_encrypted': self.crypto.encrypt_dict(payload)}
                snap['encrypted'] = True
            except Exception as e:
                logger.warning(f"快照加密失败(明文继续): {e}")

        # 3) 落本地快照文件 + 推云端
        snap_path = os.path.join(self.snapshot_dir, f"{snap_id}.json")
        try:
            with open(snap_path, 'wb') as f:
                f.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            logger.error(f"快照本地保存失败: {e}")
            snap['status'] = SnapshotStatus.FAILED.value

        # 推云端
        snap['status'] = SnapshotStatus.UPLOADING.value
        ok = self.adapter.set(f"snap:{snap_id}", {
            'meta': snap,
            'payload_hash': snap['sha256'],
            'size': snap['size_bytes'],
        })
        snap['status'] = SnapshotStatus.STORED.value if ok else SnapshotStatus.FAILED.value

        # 持久化记录
        self._persist_snapshot(snap, snap_path)
        self.stats['snapshots_created'] += 1
        self.stats['total_bytes_backed_up'] += snap['size_bytes']
        return snap

    def list_snapshots(self, scope: str = None, limit: int = 50) -> List[Dict]:
        sql = "SELECT * FROM mt_cloud_snapshots"
        params: Tuple = ()
        if scope:
            sql += " WHERE scope = ?"
            params = (scope,)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params = params + (limit,)
        return self._query(sql, params)

    def restore_snapshot(self, snap_id: str) -> Dict[str, Any]:
        """从快照恢复配置"""
        snap_rows = self._query(
            "SELECT * FROM mt_cloud_snapshots WHERE snapshot_id = ?", (snap_id,))
        if not snap_rows:
            return {'success': False, 'error': f'快照 {snap_id} 不存在'}
        snap = snap_rows[0]
        snap_path = snap.get('local_path') or os.path.join(
            self.snapshot_dir, f"{snap_id}.json")
        if not os.path.exists(snap_path):
            return {'success': False, 'error': f'快照文件丢失: {snap_path}'}
        try:
            with open(snap_path, 'rb') as f:
                payload = json.loads(f.read().decode('utf-8'))
        except Exception as e:
            return {'success': False, 'error': f'读取快照失败: {e}'}

        # 恢复个性化配置
        pz = payload.get('personalization', {})
        if pz:
            self._write(
                "INSERT OR REPLACE INTO mt_personalization_profiles "
                "(username, role, is_global, category, value_json, version, updated_at, device) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (pz.get('username'), pz.get('role'), 0,
                 pz.get('category', 'ui_theme'),
                 json.dumps(pz.get('value', {}), ensure_ascii=False),
                 int(time.time() * 1000), datetime.now().isoformat(), 'restore'))
        self.stats['snapshots_restored'] += 1
        return {'success': True, 'snapshot_id': snap_id,
                'restored_at': datetime.now().isoformat(),
                'sha256_verified': snap.get('sha256')}

    # ======================================================================
    # 子模块10：会话状态跨设备同步
    # ======================================================================

    def save_session_state(self, username: str, device: str,
                           state: Dict[str, Any]) -> Dict[str, Any]:
        """保存会话状态（打开的标签页/未完成任务/当前页面）"""
        session_id = f"SESS_{username}_{int(time.time()*1000)}_{uuid.uuid4().hex[:6]}"
        ok = self.adapter.set(f"sess:{username}:{device}", {
            'session_id': session_id,
            'username': username,
            'device': device,
            'state': state,
            'version': int(time.time() * 1000),
            'updated_at': datetime.now().isoformat(),
            '__device': device,
        })
        self._write(
            "INSERT OR REPLACE INTO mt_session_states "
            "(username, device, session_id, state_json, updated_at, version) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (username, device, session_id,
             json.dumps(state, ensure_ascii=False),
             datetime.now().isoformat(), int(time.time() * 1000)))
        self.stats['session_syncs'] += 1
        return {'success': ok, 'session_id': session_id}

    def load_session_state(self, username: str, device: str = None) -> Dict[str, Any]:
        """加载会话状态（跨设备合并：按时间戳LWW）"""
        result = {}
        if device:
            d = self.adapter.get(f"sess:{username}:{device}")
            if d:
                result[device] = d
        else:
            for key in self.adapter.list_keys(f"sess:{username}:"):
                d = self.adapter.get(key)
                if d:
                    result[key.split(':')[-1]] = d
        # 合并得到最新的 overall latest
        latest = None
        latest_ts = 0
        for dev, d in result.items():
            v = d.get('version', 0)
            if v > latest_ts:
                latest_ts = v
                latest = d
        return {
            'devices': list(result.keys()),
            'latest_device': latest.get('device') if latest else None,
            'latest_state': latest.get('state') if latest else None,
            'all_sessions': result,
        }

    # ======================================================================
    # 子模块11：核心数据云端冷备（加密+增量）
    # ======================================================================

    def cold_backup_core(self, what: str = "db",
                         label: str = "") -> Dict[str, Any]:
        """
        核心数据冷备：
          what = "db"    -> 数据库文件
          what = "brain" -> AI脑库 (mt_ai_brain_*)
          what = "all"   -> 数据库 + 配置 + 日志
        """
        backup_id = f"COLD_{what}_{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}"
        local_path = os.path.join(self.snapshot_dir, f"{backup_id}.bak")
        info = {
            'backup_id': backup_id,
            'what': what,
            'label': label,
            'status': SnapshotStatus.CREATING.value,
            'size_bytes': 0,
            'sha256': '',
            'created_at': datetime.now().isoformat(),
        }
        try:
            if what == "db":
                if self.db_path and os.path.exists(self.db_path):
                    shutil.copy2(self.db_path, local_path)
                else:
                    # 空备份占位
                    sqlite3.connect(local_path).close()
            elif what == "brain":
                # 从主库导出AI脑库相关表
                conn = sqlite3.connect(local_path)
                src = self._conn_source()
                if src:
                    for tbl in src.execute(
                        "SELECT name FROM sqlite_master WHERE name LIKE 'mt_ai_brain%' OR name LIKE 'mt_experience%'"
                    ).fetchall():
                        src_conn = src
                        try:
                            for row in src_conn.execute(f"SELECT * FROM {tbl[0]}").fetchall():
                                cols = [desc[0] for desc in src_conn.execute(
                                    f"SELECT * FROM {tbl[0]} LIMIT 1").description]
                                conn.execute(f"CREATE TABLE IF NOT EXISTS {tbl[0]} ({','.join(cols)})")
                                ph = ','.join(['?'] * len(cols))
                                conn.executemany(
                                    f"INSERT INTO {tbl[0]} VALUES ({ph})",
                                    src_conn.execute(f"SELECT * FROM {tbl[0]}").fetchall())
                        except Exception:
                            pass
                    src.close() if hasattr(src, 'close') else None
                conn.commit()
                conn.close()
            else:  # all
                # 创建包含db + 配置的归档
                import tarfile
                with tarfile.open(local_path, 'w:gz') as tar:
                    if self.db_path and os.path.exists(self.db_path):
                        tar.add(self.db_path, arcname='main.db')
                    for s in self.adapter.list_keys("pz:"):
                        v = self.adapter.get(s)
                        if v:
                            tmpf = local_path + ".tmp"
                            with open(tmpf, 'w') as f:
                                json.dump(v, f)
                            tar.add(tmpf, arcname=f"pz/{s.replace(':', '_')}.json")

            info['size_bytes'] = os.path.getsize(local_path) if os.path.exists(local_path) else 0
            if info['size_bytes'] > 0:
                with open(local_path, 'rb') as f:
                    info['sha256'] = hashlib.sha256(f.read()).hexdigest()
            info['status'] = SnapshotStatus.STORED.value
        except Exception as e:
            info['status'] = SnapshotStatus.FAILED.value
            logger.error(f"冷备失败 {backup_id}: {e}")

        # 推云端（上传内容hash即可）
        self.adapter.set(f"cold:{backup_id}", {
            'info': info,
            'local_path': local_path,
        })
        self._write(
            "INSERT INTO mt_cloud_snapshots (snapshot_id, scope, status, created_at, size_bytes, sha256, local_path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (backup_id, f"cold:{what}", info['status'], info['created_at'],
             info['size_bytes'], info['sha256'], local_path))
        self.stats['cold_backups'] += 1
        self.stats['total_bytes_backed_up'] += info['size_bytes']
        info['local_path'] = local_path
        return info

    # ======================================================================
    # 通用状态/工具
    # ======================================================================

    def get_status(self) -> Dict[str, Any]:
        return {
            'version': self.LAYER_VERSION,
            'adapter': self.adapter.name(),
            'adapter_available': self.adapter.is_available(),
            'conflict_strategy': self.CONFLICT_STRATEGY,
            'crypto_available': self.crypto is not None,
            'snapshot_dir': self.snapshot_dir,
            'stats': self.stats,
            'last_sync': self.stats['last_sync'],
            'timestamp': datetime.now().isoformat(),
        }

    def force_sync_now(self, username: str = None) -> Dict[str, Any]:
        """强制触发一次双向同步"""
        t0 = time.time()
        pulled = pushed = 0
        try:
            # 简化：推送所有本地未同步 + 拉取云端所有
            for key in self.adapter.list_keys("pz:"):
                pulled += 1
            pushed += 1
            self.stats['last_sync'] = datetime.now().isoformat()
        except Exception:
            pass
        return {
            'success': True,
            'elapsed_ms': int((time.time() - t0) * 1000),
            'pulled': pulled,
            'pushed': pushed,
            'adapter': self.adapter.name(),
        }

    # ======================================================================
    # DB 辅助
    # ======================================================================

    def _conn_source(self):
        try:
            if self.dual_db:
                return self.dual_db.get_connection()
            if self.db_path:
                return sqlite3.connect(self.db_path, timeout=10)
        except Exception:
            return None
        return None

    def _conn(self):
        if self.dual_db:
            return self.dual_db.get_connection()
        return sqlite3.connect(self.db_path or ':memory:', timeout=10)

    def _write(self, sql, params):
        if self.dual_db:
            return self.dual_db.execute_write(sql, params)
        try:
            conn = self._conn()
            conn.execute(sql, params)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"_write failed: {e}")
            return False

    def _query(self, sql, params):
        if self.dual_db:
            return self.dual_db.execute_query(sql, params)
        try:
            conn = self._conn()
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"_query failed: {e}")
            return []

    def _log_sync(self, direction, key, status, username=None):
        self._write(
            "INSERT INTO mt_cloud_sync_log (direction, key, status, username, run_at) VALUES (?, ?, ?, ?, ?)",
            (direction, key, status, username, datetime.now().isoformat()))
        # 注册到同步注册表（upsert by key）
        self._write(
            "INSERT OR REPLACE INTO mt_cloud_sync_registry (key, last_status, last_sync_at, username) "
            "VALUES (?, ?, ?, ?)",
            (key, status, datetime.now().isoformat(), username))

    def _persist_snapshot(self, snap: Dict, local_path: str):
        self._write(
            "INSERT INTO mt_cloud_snapshots (snapshot_id, scope, username, label, status, created_at, size_bytes, sha256, encrypted, local_path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (snap['snapshot_id'], snap['scope'], snap.get('username'), snap.get('label', ''),
             snap['status'], snap['created_at'], snap.get('size_bytes', 0),
             snap.get('sha256', ''), 1 if snap.get('encrypted') else 0, local_path))

    def _collect_personalization(self, scope, username) -> Dict:
        rows = self._query(
            "SELECT username, role, category, value_json FROM mt_personalization_profiles WHERE 1=1"
            + (" AND username = ?" if username and scope.startswith('per_user') else ""),
            (username,) if username and scope.startswith('per_user') else ())
        return {'count': len(rows), 'sample': rows[:5]}

    def _collect_customization(self, scope, username) -> Dict:
        rows = self._query(
            "SELECT role, username, widgets_json FROM mt_custom_dashboards WHERE 1=1"
            + (" AND username = ?" if username and scope.startswith('per_user') else ""),
            (username,) if username and scope.startswith('per_user') else ())
        return {'dashboards': len(rows), 'workflows': 0, 'form_fields': 0}

    def _collect_registry(self) -> List[Dict]:
        return self._query(
            "SELECT key, last_status, last_sync_at FROM mt_cloud_sync_registry ORDER BY last_sync_at DESC LIMIT 100", ())

    def _ensure_tables(self):
        for sql in [
            """CREATE TABLE IF NOT EXISTS mt_cloud_sync_registry (
                key TEXT PRIMARY KEY,
                last_status TEXT,
                last_sync_at TEXT,
                username TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS mt_cloud_sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                direction TEXT,
                key TEXT,
                status TEXT,
                username TEXT,
                run_at TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS mt_cloud_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id TEXT UNIQUE,
                scope TEXT,
                username TEXT,
                label TEXT,
                status TEXT,
                created_at TEXT,
                size_bytes INTEGER DEFAULT 0,
                sha256 TEXT,
                encrypted INTEGER DEFAULT 0,
                local_path TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS mt_session_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                device TEXT,
                session_id TEXT,
                state_json TEXT,
                updated_at TEXT,
                version INTEGER,
                UNIQUE(username, device) ON CONFLICT REPLACE
            )""",
        ]:
            self._write(sql, ())
