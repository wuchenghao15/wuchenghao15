#!/usr/bin/env python3
"""
配置管理AI员工 - 负责管理AI集群和员工的配置数据
统一管理数据库中的ai_cluster_config和ai_employee_config表
"""

import logging
logger = logging.getLogger(__name__)
import json
import os
import sys
import time
import uuid
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

sys.path = [p for p in sys.path if p]
try:
    from ai_engines.ai_employee_system import AIEmployee
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from ai_engines.ai_employee_system import AIEmployee

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

class ConfigManagerEmployee(AIEmployee):
    """配置管理AI员工"""

    def __init__(self, employee_id: str, name: str, employee_type: str = "config_manager", level: int = 8):
        super().__init__(employee_id, name, employee_type, level)
        self.status = "active"
        self.last_heartbeat = time.time()
        self._running = False
        self._lock = __import__('threading').RLock()
        self._initialize_tables()
        logger.info(f"配置管理AI员工初始化完成: {employee_id}")

    def _initialize_tables(self):
        """初始化配置管理相关数据库表"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_cluster_config (
                        cluster_id TEXT PRIMARY KEY,
                        cluster_type TEXT NOT NULL,
                        config TEXT DEFAULT '{}',
                        status TEXT DEFAULT 'active',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_employee_config (
                        employee_id TEXT PRIMARY KEY,
                        employee_type TEXT NOT NULL,
                        capabilities TEXT DEFAULT '[]',
                        config TEXT DEFAULT '{}',
                        assigned_cluster TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_cluster_employee (
                        cluster_id TEXT,
                        employee_id TEXT,
                        FOREIGN KEY (cluster_id) REFERENCES ai_cluster_config(cluster_id),
                        FOREIGN KEY (employee_id) REFERENCES ai_employee_config(employee_id),
                        PRIMARY KEY (cluster_id, employee_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_config_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        config_type TEXT NOT NULL,
                        config_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        old_value TEXT,
                        new_value TEXT,
                        operator TEXT DEFAULT 'system',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_config_snapshot (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        snapshot_name TEXT NOT NULL,
                        snapshot_data TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        operator TEXT DEFAULT 'system'
                    )
                ''')

                conn.commit()
                logger.info("配置管理数据库表初始化完成")
        except Exception as e:
            logger.error(f"初始化配置管理数据库失败: {str(e)}")

    def _log_history(self, config_type: str, config_id: str, action: str, 
                     old_value: Any = None, new_value: Any = None, operator: str = 'system'):
        """记录配置变更历史"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_config_history 
                    (config_type, config_id, action, old_value, new_value, operator)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    config_type,
                    config_id,
                    action,
                    json.dumps(old_value) if old_value else None,
                    json.dumps(new_value) if new_value else None,
                    operator
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"记录配置变更历史失败: {str(e)}")

    def start(self):
        """启动配置管理员工"""
        self._running = True
        self.status = "active"
        logger.info(f"配置管理AI员工已启动: {self.employee_id}")

    def stop(self):
        """停止配置管理员工"""
        self._running = False
        self.status = "inactive"
        logger.info(f"配置管理AI员工已停止: {self.employee_id}")

    def get_status(self):
        """获取员工状态"""
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.employee_type,
            "level": self.level,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat,
            "capabilities": [
                "cluster_config_management",
                "employee_config_management",
                "config_history",
                "config_validation",
                "config_import_export",
                "config_snapshot",
                "config_sync"
            ]
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行配置管理任务"""
        self.last_heartbeat = time.time()
        task_type = task_data.get("task_type")
        
        handlers = {
            "get_cluster_config": self.get_cluster_config,
            "update_cluster_config": self.update_cluster_config,
            "delete_cluster_config": self.delete_cluster_config,
            "get_employee_config": self.get_employee_config,
            "update_employee_config": self.update_employee_config,
            "delete_employee_config": self.delete_employee_config,
            "get_config_history": self.get_config_history,
            "create_snapshot": self.create_snapshot,
            "restore_snapshot": self.restore_snapshot,
            "export_config": self.export_config,
            "import_config": self.import_config,
            "validate_config": self.validate_config,
            "sync_config": self.sync_config
        }

        if task_type in handlers:
            try:
                result = handlers[task_type](task_data)
                return {"success": True, "data": result}
            except Exception as e:
                logger.error(f"执行任务失败 {task_type}: {str(e)}")
                return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": f"未知的任务类型: {task_type}"}

    def get_cluster_config(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取集群配置"""
        cluster_id = task_data.get("cluster_id")
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if cluster_id:
                    cursor.execute('SELECT * FROM ai_cluster_config WHERE cluster_id = ?', (cluster_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {"success": False, "error": f"集群 {cluster_id} 不存在"}
                    return self._row_to_cluster_dict(row)
                else:
                    cursor.execute('SELECT * FROM ai_cluster_config')
                    rows = cursor.fetchall()
                    return {"success": True, "clusters": [self._row_to_cluster_dict(row) for row in rows]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_cluster_config(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新集群配置"""
        cluster_id = task_data.get("cluster_id")
        cluster_type = task_data.get("cluster_type")
        config = task_data.get("config", {})
        status = task_data.get("status")
        operator = task_data.get("operator", "system")

        if not cluster_id:
            return {"success": False, "error": "cluster_id为必填项"}

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM ai_cluster_config WHERE cluster_id = ?', (cluster_id,))
                old_row = cursor.fetchone()
                old_value = self._row_to_cluster_dict(old_row) if old_row else None

                update_data = {"updated_at": datetime.now().isoformat()}
                if cluster_type:
                    update_data["cluster_type"] = cluster_type
                if config:
                    update_data["config"] = json.dumps(config)
                if status:
                    update_data["status"] = status

                if old_row:
                    set_clause = ", ".join(f"{k} = ?" for k in update_data.keys())
                    params = list(update_data.values()) + [cluster_id]
                    cursor.execute(f'UPDATE ai_cluster_config SET {set_clause} WHERE cluster_id = ?', params)
                    action = "update"
                else:
                    update_data["cluster_id"] = cluster_id
                    if "cluster_type" not in update_data:
                        update_data["cluster_type"] = "general"
                    if "config" not in update_data:
                        update_data["config"] = "{}"
                    if "status" not in update_data:
                        update_data["status"] = "active"
                    update_data["created_at"] = datetime.now().isoformat()
                    placeholders = ", ".join("?" * len(update_data))
                    columns = ", ".join(update_data.keys())
                    cursor.execute(f'INSERT INTO ai_cluster_config ({columns}) VALUES ({placeholders})', 
                                  list(update_data.values()))
                    action = "create"

                conn.commit()

                cursor.execute('SELECT * FROM ai_cluster_config WHERE cluster_id = ?', (cluster_id,))
                new_row = cursor.fetchone()
                new_value = self._row_to_cluster_dict(new_row) if new_row else None

                self._log_history('cluster', cluster_id, action, old_value, new_value, operator)

                return {"success": True, "message": f"集群配置{'更新' if old_row else '创建'}成功", "data": new_value}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_cluster_config(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """删除集群配置"""
        cluster_id = task_data.get("cluster_id")
        operator = task_data.get("operator", "system")

        if not cluster_id:
            return {"success": False, "error": "cluster_id为必填项"}

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM ai_cluster_config WHERE cluster_id = ?', (cluster_id,))
                old_row = cursor.fetchone()
                if not old_row:
                    return {"success": False, "error": f"集群 {cluster_id} 不存在"}

                old_value = self._row_to_cluster_dict(old_row)

                cursor.execute('DELETE FROM ai_cluster_employee WHERE cluster_id = ?', (cluster_id,))
                cursor.execute('DELETE FROM ai_cluster_config WHERE cluster_id = ?', (cluster_id,))
                conn.commit()

                self._log_history('cluster', cluster_id, 'delete', old_value, None, operator)

                return {"success": True, "message": f"集群 {cluster_id} 已删除"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_employee_config(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取员工配置"""
        employee_id = task_data.get("employee_id")
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if employee_id:
                    cursor.execute('SELECT * FROM ai_employee_config WHERE employee_id = ?', (employee_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {"success": False, "error": f"员工 {employee_id} 不存在"}
                    return self._row_to_employee_dict(row)
                else:
                    cursor.execute('SELECT * FROM ai_employee_config')
                    rows = cursor.fetchall()
                    return {"success": True, "employees": [self._row_to_employee_dict(row) for row in rows]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_employee_config(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新员工配置"""
        employee_id = task_data.get("employee_id")
        employee_type = task_data.get("employee_type")
        capabilities = task_data.get("capabilities")
        config = task_data.get("config")
        assigned_cluster = task_data.get("assigned_cluster")
        status = task_data.get("status")
        operator = task_data.get("operator", "system")

        if not employee_id:
            return {"success": False, "error": "employee_id为必填项"}

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM ai_employee_config WHERE employee_id = ?', (employee_id,))
                old_row = cursor.fetchone()
                old_value = self._row_to_employee_dict(old_row) if old_row else None

                update_data = {"updated_at": datetime.now().isoformat()}
                if employee_type:
                    update_data["employee_type"] = employee_type
                if capabilities is not None:
                    update_data["capabilities"] = json.dumps(capabilities)
                if config:
                    update_data["config"] = json.dumps(config)
                if assigned_cluster:
                    update_data["assigned_cluster"] = assigned_cluster
                if status:
                    update_data["status"] = status

                if old_row:
                    set_clause = ", ".join(f"{k} = ?" for k in update_data.keys())
                    params = list(update_data.values()) + [employee_id]
                    cursor.execute(f'UPDATE ai_employee_config SET {set_clause} WHERE employee_id = ?', params)
                    action = "update"
                else:
                    update_data["employee_id"] = employee_id
                    if "employee_type" not in update_data:
                        update_data["employee_type"] = "general"
                    if "capabilities" not in update_data:
                        update_data["capabilities"] = "[]"
                    if "config" not in update_data:
                        update_data["config"] = "{}"
                    update_data["created_at"] = datetime.now().isoformat()
                    placeholders = ", ".join("?" * len(update_data))
                    columns = ", ".join(update_data.keys())
                    cursor.execute(f'INSERT INTO ai_employee_config ({columns}) VALUES ({placeholders})', 
                                  list(update_data.values()))
                    action = "create"

                if assigned_cluster:
                    cursor.execute('DELETE FROM ai_cluster_employee WHERE employee_id = ?', (employee_id,))
                    cursor.execute('INSERT OR IGNORE INTO ai_cluster_employee (cluster_id, employee_id) VALUES (?, ?)',
                                  (assigned_cluster, employee_id))

                conn.commit()

                cursor.execute('SELECT * FROM ai_employee_config WHERE employee_id = ?', (employee_id,))
                new_row = cursor.fetchone()
                new_value = self._row_to_employee_dict(new_row) if new_row else None

                self._log_history('employee', employee_id, action, old_value, new_value, operator)

                return {"success": True, "message": f"员工配置{'更新' if old_row else '创建'}成功", "data": new_value}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_employee_config(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """删除员工配置"""
        employee_id = task_data.get("employee_id")
        operator = task_data.get("operator", "system")

        if not employee_id:
            return {"success": False, "error": "employee_id为必填项"}

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM ai_employee_config WHERE employee_id = ?', (employee_id,))
                old_row = cursor.fetchone()
                if not old_row:
                    return {"success": False, "error": f"员工 {employee_id} 不存在"}

                old_value = self._row_to_employee_dict(old_row)

                cursor.execute('DELETE FROM ai_cluster_employee WHERE employee_id = ?', (employee_id,))
                cursor.execute('DELETE FROM ai_employee_config WHERE employee_id = ?', (employee_id,))
                conn.commit()

                self._log_history('employee', employee_id, 'delete', old_value, None, operator)

                return {"success": True, "message": f"员工 {employee_id} 已删除"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_config_history(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取配置变更历史"""
        config_type = task_data.get("config_type")
        config_id = task_data.get("config_id")
        limit = task_data.get("limit", 50)

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                query = 'SELECT * FROM ai_config_history WHERE 1=1'
                params = []

                if config_type:
                    query += ' AND config_type = ?'
                    params.append(config_type)

                if config_id:
                    query += ' AND config_id = ?'
                    params.append(config_id)

                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                history = []
                for row in rows:
                    history.append({
                        "id": row["id"],
                        "config_type": row["config_type"],
                        "config_id": row["config_id"],
                        "action": row["action"],
                        "old_value": json.loads(row["old_value"]) if row["old_value"] else None,
                        "new_value": json.loads(row["new_value"]) if row["new_value"] else None,
                        "operator": row["operator"],
                        "created_at": row["created_at"]
                    })

                return {"success": True, "history": history}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_snapshot(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建配置快照"""
        snapshot_name = task_data.get("snapshot_name", f"snapshot_{int(time.time())}")
        operator = task_data.get("operator", "system")

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM ai_cluster_config')
                clusters = [dict(row) for row in cursor.fetchall()]

                cursor.execute('SELECT * FROM ai_employee_config')
                employees = [dict(row) for row in cursor.fetchall()]

                cursor.execute('SELECT * FROM ai_cluster_employee')
                relationships = [dict(row) for row in cursor.fetchall()]

                snapshot_data = {
                    "snapshot_name": snapshot_name,
                    "created_at": datetime.now().isoformat(),
                    "clusters": clusters,
                    "employees": employees,
                    "relationships": relationships
                }

                cursor.execute('''
                    INSERT INTO ai_config_snapshot 
                    (snapshot_name, snapshot_data, operator)
                    VALUES (?, ?, ?)
                ''', (snapshot_name, json.dumps(snapshot_data), operator))

                conn.commit()

                return {"success": True, "message": f"配置快照 '{snapshot_name}' 创建成功", "data": snapshot_data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restore_snapshot(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """恢复配置快照"""
        snapshot_id = task_data.get("snapshot_id")
        snapshot_name = task_data.get("snapshot_name")
        operator = task_data.get("operator", "system")

        if not snapshot_id and not snapshot_name:
            return {"success": False, "error": "snapshot_id或snapshot_name为必填项"}

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                if snapshot_id:
                    cursor.execute('SELECT * FROM ai_config_snapshot WHERE id = ?', (snapshot_id,))
                else:
                    cursor.execute('SELECT * FROM ai_config_snapshot WHERE snapshot_name = ?', (snapshot_name,))

                row = cursor.fetchone()
                if not row:
                    return {"success": False, "error": "快照不存在"}

                snapshot_data = json.loads(row["snapshot_data"])

                cursor.execute('DELETE FROM ai_cluster_employee')
                cursor.execute('DELETE FROM ai_employee_config')
                cursor.execute('DELETE FROM ai_cluster_config')

                for cluster in snapshot_data.get("clusters", []):
                    cursor.execute('''
                        INSERT INTO ai_cluster_config 
                        (cluster_id, cluster_type, config, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        cluster["cluster_id"],
                        cluster["cluster_type"],
                        cluster["config"],
                        cluster["status"],
                        cluster["created_at"],
                        cluster["updated_at"]
                    ))

                for employee in snapshot_data.get("employees", []):
                    cursor.execute('''
                        INSERT INTO ai_employee_config 
                        (employee_id, employee_type, capabilities, config, assigned_cluster, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        employee["employee_id"],
                        employee["employee_type"],
                        employee["capabilities"],
                        employee["config"],
                        employee["assigned_cluster"],
                        employee["status"],
                        employee["created_at"],
                        employee["updated_at"]
                    ))

                for rel in snapshot_data.get("relationships", []):
                    cursor.execute('''
                        INSERT INTO ai_cluster_employee (cluster_id, employee_id) VALUES (?, ?)
                    ''', (rel["cluster_id"], rel["employee_id"]))

                conn.commit()

                self._log_history('system', 'snapshot', 'restore', 
                                 old_value=None, 
                                 new_value={"snapshot_id": snapshot_id, "snapshot_name": snapshot_name},
                                 operator=operator)

                return {"success": True, "message": f"配置快照 '{snapshot_name}' 恢复成功"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def export_config(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """导出配置"""
        export_type = task_data.get("export_type", "all")

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                export_data = {}

                if export_type in ["all", "clusters"]:
                    cursor.execute('SELECT * FROM ai_cluster_config')
                    export_data["clusters"] = [self._row_to_cluster_dict(row) for row in cursor.fetchall()]

                if export_type in ["all", "employees"]:
                    cursor.execute('SELECT * FROM ai_employee_config')
                    export_data["employees"] = [self._row_to_employee_dict(row) for row in cursor.fetchall()]

                if export_type in ["all", "relationships"]:
                    cursor.execute('SELECT * FROM ai_cluster_employee')
                    export_data["relationships"] = [dict(row) for row in cursor.fetchall()]

                export_data["export_time"] = datetime.now().isoformat()

                return {"success": True, "data": export_data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def import_config(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """导入配置"""
        config_data = task_data.get("config_data")
        overwrite = task_data.get("overwrite", False)
        operator = task_data.get("operator", "system")

        if not config_data:
            return {"success": False, "error": "config_data为必填项"}

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                if overwrite:
                    cursor.execute('DELETE FROM ai_cluster_employee')
                    cursor.execute('DELETE FROM ai_employee_config')
                    cursor.execute('DELETE FROM ai_cluster_config')

                clusters_created = 0
                clusters_updated = 0
                employees_created = 0
                employees_updated = 0
                relationships_created = 0

                for cluster in config_data.get("clusters", []):
                    cursor.execute('SELECT * FROM ai_cluster_config WHERE cluster_id = ?', (cluster["cluster_id"],))
                    if cursor.fetchone():
                        cursor.execute('''
                            UPDATE ai_cluster_config 
                            SET cluster_type = ?, config = ?, status = ?, updated_at = ?
                            WHERE cluster_id = ?
                        ''', (
                            cluster.get("cluster_type", "general"),
                            cluster.get("config", "{}"),
                            cluster.get("status", "active"),
                            datetime.now().isoformat(),
                            cluster["cluster_id"]
                        ))
                        clusters_updated += 1
                    else:
                        cursor.execute('''
                            INSERT INTO ai_cluster_config 
                            (cluster_id, cluster_type, config, status, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            cluster["cluster_id"],
                            cluster.get("cluster_type", "general"),
                            cluster.get("config", "{}"),
                            cluster.get("status", "active"),
                            datetime.now().isoformat(),
                            datetime.now().isoformat()
                        ))
                        clusters_created += 1

                for employee in config_data.get("employees", []):
                    cursor.execute('SELECT * FROM ai_employee_config WHERE employee_id = ?', (employee["employee_id"],))
                    if cursor.fetchone():
                        cursor.execute('''
                            UPDATE ai_employee_config 
                            SET employee_type = ?, capabilities = ?, config = ?, assigned_cluster = ?, status = ?, updated_at = ?
                            WHERE employee_id = ?
                        ''', (
                            employee.get("employee_type", "general"),
                            employee.get("capabilities", "[]"),
                            employee.get("config", "{}"),
                            employee.get("assigned_cluster"),
                            employee.get("status", "active"),
                            datetime.now().isoformat(),
                            employee["employee_id"]
                        ))
                        employees_updated += 1
                    else:
                        cursor.execute('''
                            INSERT INTO ai_employee_config 
                            (employee_id, employee_type, capabilities, config, assigned_cluster, status, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            employee["employee_id"],
                            employee.get("employee_type", "general"),
                            employee.get("capabilities", "[]"),
                            employee.get("config", "{}"),
                            employee.get("assigned_cluster"),
                            employee.get("status", "active"),
                            datetime.now().isoformat(),
                            datetime.now().isoformat()
                        ))
                        employees_created += 1

                for rel in config_data.get("relationships", []):
                    cursor.execute('''
                        INSERT OR IGNORE INTO ai_cluster_employee (cluster_id, employee_id) VALUES (?, ?)
                    ''', (rel["cluster_id"], rel["employee_id"]))
                    relationships_created += 1

                conn.commit()

                self._log_history('system', 'import', 'import',
                                 old_value=None,
                                 new_value={"clusters_created": clusters_created, "clusters_updated": clusters_updated,
                                            "employees_created": employees_created, "employees_updated": employees_updated},
                                 operator=operator)

                return {
                    "success": True,
                    "message": "配置导入成功",
                    "data": {
                        "clusters_created": clusters_created,
                        "clusters_updated": clusters_updated,
                        "employees_created": employees_created,
                        "employees_updated": employees_updated,
                        "relationships_created": relationships_created
                    }
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate_config(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置"""
        config_data = task_data.get("config_data")
        
        if not config_data:
            return {"success": False, "error": "config_data为必填项"}

        errors = []
        warnings = []

        clusters = config_data.get("clusters", [])
        employees = config_data.get("employees", [])

        for cluster in clusters:
            if not cluster.get("cluster_id"):
                errors.append(f"集群缺少cluster_id")
            if not cluster.get("cluster_type"):
                warnings.append(f"集群 {cluster.get('cluster_id', 'unknown')} 缺少cluster_type，将使用默认值")

        for employee in employees:
            if not employee.get("employee_id"):
                errors.append(f"员工缺少employee_id")
            if not employee.get("employee_type"):
                warnings.append(f"员工 {employee.get('employee_id', 'unknown')} 缺少employee_type，将使用默认值")
            if employee.get("assigned_cluster"):
                cluster_ids = [c["cluster_id"] for c in clusters]
                if employee["assigned_cluster"] not in cluster_ids:
                    errors.append(f"员工 {employee.get('employee_id', 'unknown')} 分配的集群 {employee['assigned_cluster']} 不存在")

        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "valid": len(errors) == 0
        }

    def sync_config(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """同步配置"""
        source_type = task_data.get("source_type", "database")
        
        try:
            from ai_engines.ai_cluster_manager import ai_cluster_manager
            
            if source_type == "database":
                ai_cluster_manager._load_from_database()
                return {"success": True, "message": "配置已从数据库同步到内存"}
            elif source_type == "memory":
                ai_cluster_manager._save_to_database()
                return {"success": True, "message": "配置已从内存同步到数据库"}
            else:
                return {"success": False, "error": f"未知的同步源类型: {source_type}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _row_to_cluster_dict(self, row) -> Dict[str, Any]:
        """将数据库行转换为集群字典"""
        return {
            "cluster_id": row["cluster_id"],
            "cluster_type": row["cluster_type"],
            "config": json.loads(row["config"]) if row["config"] else {},
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }

    def _row_to_employee_dict(self, row) -> Dict[str, Any]:
        """将数据库行转换为员工字典"""
        return {
            "employee_id": row["employee_id"],
            "employee_type": row["employee_type"],
            "capabilities": json.loads(row["capabilities"]) if row["capabilities"] else [],
            "config": json.loads(row["config"]) if row["config"] else {},
            "assigned_cluster": row["assigned_cluster"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }

config_manager_employee = ConfigManagerEmployee("config_mgr_001", "配置管理AI", "config_manager", 8)

if __name__ == "__main__":
    logger.info("配置管理AI员工测试启动")
    
    config_manager_employee.start()
    
    result = config_manager_employee.execute_task({
        "task_type": "update_cluster_config",
        "cluster_id": "test_cluster",
        "cluster_type": "test",
        "config": {"test_param": "test_value"}
    })
    print(f"创建集群: {result}")
    
    result = config_manager_employee.execute_task({"task_type": "get_cluster_config"})
    print(f"集群列表: {result}")
    
    result = config_manager_employee.execute_task({
        "task_type": "update_employee_config",
        "employee_id": "test_employee",
        "employee_type": "test",
        "capabilities": ["test_cap"],
        "assigned_cluster": "test_cluster"
    })
    print(f"创建员工: {result}")
    
    result = config_manager_employee.execute_task({"task_type": "get_employee_config"})
    print(f"员工列表: {result}")
    
    result = config_manager_employee.execute_task({"task_type": "get_config_history"})
    print(f"配置历史: {result}")
    
    result = config_manager_employee.execute_task({"task_type": "create_snapshot", "snapshot_name": "test_snapshot"})
    print(f"创建快照: {result}")
    
    result = config_manager_employee.execute_task({"task_type": "export_config"})
    print(f"导出配置: {result}")
    
    result = config_manager_employee.execute_task({"task_type": "validate_config", "config_data": {"clusters": [], "employees": []}})
    print(f"验证配置: {result}")
    
    result = config_manager_employee.execute_task({"task_type": "delete_cluster_config", "cluster_id": "test_cluster"})
    print(f"删除集群: {result}")
    
    result = config_manager_employee.execute_task({"task_type": "delete_employee_config", "employee_id": "test_employee"})
    print(f"删除员工: {result}")
    
    logger.info("配置管理AI员工测试完成")