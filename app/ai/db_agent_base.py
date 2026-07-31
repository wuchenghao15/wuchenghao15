#!/usr/bin/env python3
import json
import sqlite3
import os
from datetime import datetime

class DatabaseBackedAgent:
    _RESERVED_ATTRS = {'agent_id', 'agent_type', '_db_path', '_registry_data', '_state_cache', '_initialized'}
    _JSON_TYPES = (dict, list)

    def __new__(cls, agent_id=None, **kwargs):
        instance = super().__new__(cls)
        instance._initialized = False
        instance._state_cache = {}
        return instance

    def __init__(self, agent_id=None, agent_type='base', name=None, config=None):
        if getattr(self, '_initialized', False):
            return
        
        self._db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'app.db'
        )
        self._state_cache = {}
        
        if agent_id:
            self.agent_id = agent_id
        else:
            self.agent_id = f"agent_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
        
        self.agent_type = agent_type
        self.name = name or f"{agent_type}_agent"
        
        if config:
            for key, value in config.items():
                setattr(self, key, value)
        
        self._create_tables()
        self._sync_from_db()
        self._save_registry()
        
        object.__setattr__(self, '_initialized', True)

    def _create_tables(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_registry (
                agent_id TEXT PRIMARY KEY,
                agent_type TEXT NOT NULL,
                name TEXT,
                config_json TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_state (
                agent_id TEXT NOT NULL,
                state_key TEXT NOT NULL,
                state_value_json TEXT NOT NULL,
                state_type TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (agent_id, state_key),
                FOREIGN KEY (agent_id) REFERENCES agent_registry(agent_id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_agent_state_id ON agent_state(agent_id)
        ''')
        
        conn.commit()
        conn.close()

    def _save_registry(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        config_data = {}
        for key, value in self.__dict__.items():
            if key not in self._RESERVED_ATTRS:
                config_data[key] = value
        
        cursor.execute('''
            INSERT OR REPLACE INTO agent_registry
            (agent_id, agent_type, name, config_json, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            self.agent_id,
            self.agent_type,
            self.name,
            json.dumps(config_data),
            'active',
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()

    def _sync_from_db(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT config_json FROM agent_registry WHERE agent_id = ?', (self.agent_id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            try:
                config_data = json.loads(result[0])
                for key, value in config_data.items():
                    if key not in self._RESERVED_ATTRS:
                        object.__setattr__(self, key, value)
                        self._state_cache[key] = value
            except json.JSONDecodeError:
                pass
        
        cursor.execute('SELECT state_key, state_value_json, state_type FROM agent_state WHERE agent_id = ?',
        (self.agent_id,))
        for row in cursor.fetchall():
            key, value_json, value_type = row
            try:
                value = json.loads(value_json)
                if isinstance(value, dict) and '__value__' in value:
                    value = value['__value__']
                object.__setattr__(self, key, value)
                self._state_cache[key] = value
            except json.JSONDecodeError:
                object.__setattr__(self, key, value_json)
                self._state_cache[key] = value_json
        
        conn.close()

    def _save_state(self, key, value):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        value_type = type(value).__name__
        if isinstance(value, self._JSON_TYPES):
            value_json = json.dumps(value)
        else:
            value_json = json.dumps({'__value__': value, '__type__': value_type})
        
        cursor.execute('''
            INSERT OR REPLACE INTO agent_state
            (agent_id, state_key, state_value_json, state_type, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            self.agent_id,
            key,
            value_json,
            value_type,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()

    def __setattr__(self, key, value):
        if key in self._RESERVED_ATTRS:
            object.__setattr__(self, key, value)
            return
        
        object.__setattr__(self, key, value)
        
        if getattr(self, '_initialized', False):
            self._state_cache[key] = value
            self._save_state(key, value)
            self._save_registry()

    def __getattr__(self, key):
        if key in self._RESERVED_ATTRS:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")
        
        if key in self.__dict__:
            return self.__dict__[key]
        
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT state_value_json, state_type FROM agent_state WHERE agent_id = ? AND state_key = ?',
        (self.agent_id, key))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            value_json, value_type = result
            try:
                parsed = json.loads(value_json)
                if isinstance(parsed, dict) and '__value__' in parsed:
                    value = parsed['__value__']
                else:
                    value = parsed
                object.__setattr__(self, key, value)
                self._state_cache[key] = value
                return value
            except json.JSONDecodeError:
                object.__setattr__(self, key, value_json)
                self._state_cache[key] = value_json
                return value_json
        
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")

    def __delattr__(self, key):
        if key in self._RESERVED_ATTRS:
            raise AttributeError(f"Cannot delete reserved attribute '{key}'")
        
        if key in self.__dict__:
            object.__delattr__(self, key)
            
            if getattr(self, '_initialized', False):
                conn = sqlite3.connect(self._db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM agent_state WHERE agent_id = ? AND state_key = ?', (self.agent_id, key))
                conn.commit()
                conn.close()
                
                if key in self._state_cache:
                    del self._state_cache[key]
                
                self._save_registry()

    def get_all_state(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT state_key, state_value_json, state_type FROM agent_state WHERE agent_id = ?',
        (self.agent_id,))
        results = {}
        
        for row in cursor.fetchall():
            key, value_json, value_type = row
            try:
                parsed = json.loads(value_json)
                if isinstance(parsed, dict) and '__value__' in parsed:
                    results[key] = parsed['__value__']
                else:
                    results[key] = parsed
            except json.JSONDecodeError:
                results[key] = value_json
        
        conn.close()
        
        for key, value in self.__dict__.items():
            if key not in self._RESERVED_ATTRS and key not in results:
                results[key] = value
        
        return results

    def set_state_bulk(self, state_dict):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        for key, value in state_dict.items():
            if key in self._RESERVED_ATTRS:
                continue
            
            object.__setattr__(self, key, value)
            self._state_cache[key] = value
            
            value_type = type(value).__name__
            if isinstance(value, self._JSON_TYPES):
                value_json = json.dumps(value)
            else:
                value_json = json.dumps({'__value__': value, '__type__': value_type})
            
            cursor.execute('''
                INSERT OR REPLACE INTO agent_state
                (agent_id, state_key, state_value_json, state_type, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                self.agent_id,
                key,
                value_json,
                value_type,
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        self._save_registry()

    def clear_state(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM agent_state WHERE agent_id = ?', (self.agent_id,))
        conn.commit()
        conn.close()
        
        for key in list(self._state_cache.keys()):
            if key in self.__dict__:
                del self.__dict__[key]
            del self._state_cache[key]
        
        self._save_registry()

    def delete_agent(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM agent_state WHERE agent_id = ?', (self.agent_id,))
        cursor.execute('DELETE FROM agent_registry WHERE agent_id = ?', (self.agent_id,))
        conn.commit()
        conn.close()

    def get_registry_info(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM agent_registry WHERE agent_id = ?', (self.agent_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return {
                'agent_id': result[0],
                'agent_type': result[1],
                'name': result[2],
                'config_json': json.loads(result[3]) if result[3] else {},
                'status': result[4],
                'created_at': result[5],
                'updated_at': result[6]
            }
        return None

    def update_status(self, status):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE agent_registry SET status = ?, updated_at = ? WHERE agent_id = ?
        ''', (status, datetime.now().isoformat(), self.agent_id))
        
        conn.commit()
        conn.close()
        
        object.__setattr__(self, 'status', status)