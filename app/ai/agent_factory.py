#!/usr/bin/env python3
import json
import sqlite3
import os
from datetime import datetime
from app.ai.db_agent_base import DatabaseBackedAgent

class AgentFactory:
    def __init__(self):
        self._db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'app.db'
        )
        self._agent_classes = {}
        self._instances = {}
        self._create_tables()

    def _create_tables(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS agent_registry ( agent_id TEXT PRIMARY KEY, agent_type TEXT NOT NULL, name TEXT, config_json TEXT, status TEXT DEFAULT 'active', created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS agent_state ( agent_id TEXT NOT NULL, state_key TEXT NOT NULL, state_value_json TEXT NOT NULL, state_type TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (agent_id, state_key), FOREIGN KEY (agent_id) REFERENCES agent_registry(agent_id) ON DELETE CASCADE ) ''')
        
        cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_agent_state_id ON agent_state(agent_id) ''')
        
        cursor.execute(''' CREATE INDEX IF NOT EXISTS idx_agent_type ON agent_registry(agent_type) ''')
        
        conn.commit()
        conn.close()

    def register_agent_class(self, agent_type, agent_class):
        self._agent_classes[agent_type] = agent_class

    def create_agent(self, agent_type, name=None, config=None, agent_id=None):
        if agent_type in self._agent_classes:
            agent_class = self._agent_classes[agent_type]
        else:
            agent_class = DatabaseBackedAgent
        
        agent = agent_class(agent_id=agent_id, agent_type=agent_type, name=name, config=config)
        
        if agent_id:
            self._instances[agent_id] = agent
        else:
            self._instances[agent.agent_id] = agent
        
        return agent

    def get_agent(self, agent_id):
        if agent_id in self._instances:
            return self._instances[agent_id]
        
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT agent_type, name, config_json FROM agent_registry WHERE agent_id = ?', (agent_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            agent_type, name, config_json = result
            config = json.loads(config_json) if config_json else {}
            
            if agent_type in self._agent_classes:
                agent_class = self._agent_classes[agent_type]
            else:
                agent_class = DatabaseBackedAgent
            
            agent = agent_class(agent_id=agent_id, agent_type=agent_type, name=name, config=config)
            self._instances[agent_id] = agent
            return agent
        
        return None

    def list_agents(self, agent_type=None):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        if agent_type:
            cursor.execute('SELECT agent_id, agent_type, name, status, created_at, updated_at FROM agent_registry WHERE agent_type = ?', (agent_type,))
        else:
            cursor.execute('SELECT agent_id, agent_type, name, status, created_at, updated_at FROM agent_registry')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'agent_id': row[0],
                'agent_type': row[1],
                'name': row[2],
                'status': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            })
        
        conn.close()
        return results

    def delete_agent(self, agent_id):
        if agent_id in self._instances:
            del self._instances[agent_id]
        
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM agent_state WHERE agent_id = ?', (agent_id,))
        cursor.execute('DELETE FROM agent_registry WHERE agent_id = ?', (agent_id,))
        
        conn.commit()
        conn.close()

    def update_agent_config(self, agent_id, config):
        agent = self.get_agent(agent_id)
        if agent:
            for key, value in config.items():
                setattr(agent, key, value)
            return True
        return False

    def get_agent_state(self, agent_id):
        agent = self.get_agent(agent_id)
        if agent:
            return agent.get_all_state()
        return None

    def set_agent_state(self, agent_id, state_dict):
        agent = self.get_agent(agent_id)
        if agent:
            agent.set_state_bulk(state_dict)
            return True
        return False

    def count_agents(self, agent_type=None):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        if agent_type:
            cursor.execute('SELECT COUNT(*) FROM agent_registry WHERE agent_type = ?', (agent_type,))
        else:
            cursor.execute('SELECT COUNT(*) FROM agent_registry')
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0

    def get_agent_types(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT agent_type FROM agent_registry')
        results = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return results

    def create_or_get_agent(self, agent_type, name, config=None):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT agent_id FROM agent_registry WHERE agent_type = ? AND name = ?', (agent_type, name))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return self.get_agent(result[0])
        else:
            return self.create_agent(agent_type, name, config)

    def bulk_create_agents(self, agents_data):
        created_agents = []
        for data in agents_data:
            agent_type = data.get('agent_type', 'base')
            name = data.get('name')
            config = data.get('config', {})
            
            if name:
                agent = self.create_agent(agent_type, name, config)
                created_agents.append({
                    'agent_id': agent.agent_id,
                    'name': agent.name,
                    'agent_type': agent.agent_type
                })
        
        return created_agents

    def clear_all_agents(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM agent_state')
        cursor.execute('DELETE FROM agent_registry')
        
        conn.commit()
        conn.close()
        
        self._instances.clear()

agent_factory = AgentFactory()