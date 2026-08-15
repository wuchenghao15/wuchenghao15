#!/usr/bin/env python3
import json
import sqlite3
import os
from datetime import datetime

VERSION_DATA = {
    '14.0.0': {
        'major': 14,
        'minor': 0,
        'patch': 0,
        'build_number': '20260718a',
        'build_date': '2026-07-18',
        'codename': 'AI Employee Orchestration & Integration Edition',
        'status': 'stable',
        'description': 'AI员工编排与集成版本，创建AI员工编排层连接专业角色→技能进化→独立思考→网络学习的自动化成长周期，实现14个子系统统一集成与仪表盘监控',
        'features': [
            'AI员工编排层（ai_orchestrator.py）- 连接专业角色→技能进化→独立思考→网络学习的完整成长周期',
            '统一AI仪表盘API（ai_dashboard_api.py）- 聚合14个子系统数据的统一监控端点',
            '数据库驱动代理系统（db_agent_base.py）- 所有参数自动保存数据库',
            'AgentFactory代理工厂（agent_factory.py）- 代理创建、管理和生命周期',
            'AgentManagementAPI（agent_management_api.py）- 完整的代理管理REST API',
            'AI员工仪表盘页面（ai_employee_dashboard.html）- 可视化员工管理界面',
            '语言角色专业知识扩展（关西腔/关东腔/美式英语/英式英语）',
            '数据库表自动创建（ai_employees/agent_registry/agent_state）',
            '全子系统数据聚合与监控',
            '系统扩展性增强与性能优化'
        ],
        'upgrade_notes': '从v13.1.0升级：新增数据库驱动代理系统，所有参数自动保存数据库，实现AgentFactory和AgentManagementAPI，创建AI员工仪表盘页面'
    }
}

CURRENT_VERSION = '14.0.0'

class VersionService:
    def __init__(self):
        self._db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'app.db'
        )
        self._create_tables()

    def _create_tables(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_key TEXT UNIQUE NOT NULL,
                fact_value TEXT,
                data_type TEXT DEFAULT 'string',
                description TEXT,
                category TEXT DEFAULT 'version',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                codename TEXT,
                status TEXT DEFAULT 'stable',
                description TEXT,
                build_date TEXT,
                build_number TEXT,
                upgrade_time TEXT DEFAULT CURRENT_TIMESTAMP,
                upgrade_type TEXT DEFAULT 'manual',
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_version_for_template(self):
        data = VERSION_DATA.get(CURRENT_VERSION, {})
        return {
            'version': CURRENT_VERSION,
            'codename': data.get('codename', ''),
            'build_number': data.get('build_number', ''),
            'build_date': data.get('build_date', ''),
            'status': data.get('status', 'stable'),
            'description': data.get('description', ''),
            'features': data.get('features', []),
            'upgrade_notes': data.get('upgrade_notes', '')
        }

    def get_version_facts(self, category=None):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('SELECT * FROM version_facts WHERE category = ?', (category,))
        else:
            cursor.execute('SELECT * FROM version_facts')
        
        facts = []
        for row in cursor.fetchall():
            facts.append({
                'id': row[0],
                'fact_key': row[1],
                'fact_value': row[2],
                'data_type': row[3],
                'description': row[4],
                'category': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            })
        
        conn.close()
        return facts

    def set_version_fact(self, fact_key, fact_value, data_type='string', description='', category='version'):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO version_facts
            (fact_key, fact_value, data_type, description, category, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (fact_key, str(fact_value), data_type, description, category, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True

    def get_version_history(self, limit=20):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM version_history ORDER BY upgrade_time DESC LIMIT ?', (limit,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'id': row[0],
                'version': row[1],
                'codename': row[2],
                'status': row[3],
                'description': row[4],
                'build_date': row[5],
                'build_number': row[6],
                'upgrade_time': row[7],
                'upgrade_type': row[8],
                'notes': row[9]
            })
        
        conn.close()
        return history

    def increment_version(self, level='patch'):
        global CURRENT_VERSION
        
        major, minor, patch = map(int, CURRENT_VERSION.split('.'))
        
        if level == 'major':
            major += 1
            minor = 0
            patch = 0
        elif level == 'minor':
            minor += 1
            patch = 0
        else:
            patch += 1
        
        new_version = f'{major}.{minor}.{patch}'
        
        VERSION_DATA[new_version] = {
            'major': major,
            'minor': minor,
            'patch': patch,
            'build_number': f'{datetime.now().strftime("%Y%m%d")}a',
            'build_date': datetime.now().strftime('%Y-%m-%d'),
            'codename': f'v{new_version} Edition',
            'status': 'stable',
            'description': f'版本升级至 {new_version}',
            'features': [],
            'upgrade_notes': f'从 {CURRENT_VERSION} 升级至 {new_version}'
        }
        
        CURRENT_VERSION = new_version
        
        self._record_upgrade(new_version, upgrade_type='auto')
        
        return new_version

    def _record_upgrade(self, version, upgrade_type='manual', notes=''):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        data = VERSION_DATA.get(version, {})
        cursor.execute('''
            INSERT INTO version_history 
            (version, codename, status, description, build_date, build_number, upgrade_time, upgrade_type, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            version,
            data.get('codename', ''),
            data.get('status', 'stable'),
            data.get('description', ''),
            data.get('build_date', datetime.now().isoformat()),
            data.get('build_number', ''),
            datetime.now().isoformat(),
            upgrade_type,
            notes
        ))
        
        conn.commit()
        conn.close()

version_service = VersionService()