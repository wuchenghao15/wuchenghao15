#!/usr/bin/env python3
import sqlite3
import os
import json
from datetime import datetime

class SystemVersionDatabase:
    def __init__(self):
        self._db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'app.db'
        )
        self._create_tables()
        self._init_initial_data()

    def _create_tables(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS system_version ( id INTEGER PRIMARY KEY AUTOINCREMENT, version TEXT UNIQUE NOT NULL, major INTEGER NOT NULL, minor INTEGER NOT NULL, patch INTEGER NOT NULL, build_number TEXT, build_date TEXT, codename TEXT, status TEXT DEFAULT 'stable', description TEXT, upgrade_notes TEXT, is_current INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS system_version_features ( id INTEGER PRIMARY KEY AUTOINCREMENT, version_id INTEGER NOT NULL, feature_text TEXT NOT NULL, feature_type TEXT DEFAULT 'feature', sort_order INTEGER DEFAULT 0, FOREIGN KEY (version_id) REFERENCES system_version(id) ) ''')
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS system_upgrade_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, upgrade_id TEXT UNIQUE NOT NULL, version_from TEXT NOT NULL, version_to TEXT NOT NULL, status TEXT DEFAULT 'pending', started_at TEXT DEFAULT CURRENT_TIMESTAMP, completed_at TEXT, upgrade_type TEXT DEFAULT 'manual', operator TEXT, error_message TEXT, log_text TEXT ) ''')
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS system_changelog ( id INTEGER PRIMARY KEY AUTOINCREMENT, version TEXT NOT NULL, codename TEXT, release_date TEXT, change_type TEXT DEFAULT 'feature', change_title TEXT NOT NULL, change_description TEXT, sort_order INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS system_history ( id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL, event_category TEXT DEFAULT 'system', event_title TEXT NOT NULL, event_description TEXT, related_version TEXT, operator TEXT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP, details TEXT ) ''')
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS system_metrics ( id INTEGER PRIMARY KEY AUTOINCREMENT, metric_key TEXT UNIQUE NOT NULL, metric_value TEXT NOT NULL, metric_type TEXT DEFAULT 'integer', category TEXT DEFAULT 'system', recorded_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_version_version ON system_version(version)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_upgrade_status ON system_upgrade_records(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_upgrade_started ON system_upgrade_records(started_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_changelog_version ON system_changelog(version)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_history_type ON system_history(event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_history_timestamp ON system_history(timestamp)')
        
        conn.commit()
        conn.close()

    def _init_initial_data(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM system_version')
        if cursor.fetchone()[0] == 0:
            versions = [
                {
                    'version': 'v15.6.1',
                    'major': 15,
                    'minor': 6,
                    'patch': 1,
                    'build_number': '20260720a',
                    'build_date': '2026-07-20',
                    'codename': 'System Upgrade Center Enhancement',
                    'status': 'stable',
                    'description': '系统升级中心全面完善，版本管理API，系统维护功能',
                    'upgrade_notes': '从v15.6.0升级：系统升级中心页面完善、数据库版本存储、历史记录管理',
                    'is_current': 1
                },
                {
                    'version': 'v15.6.0',
                    'major': 15,
                    'minor': 6,
                    'patch': 0,
                    'build_number': '20260719a',
                    'build_date': '2026-07-19',
                    'codename': 'System Comprehensive Enhancement Suite',
                    'status': 'stable',
                    'description': '完善所有系统页面（AI自动扩展、GitHub同步、系统升级中心、备份管理、布局管理、错题本）',
                    'upgrade_notes': '从v15.5.0升级：完善所有系统页面、更新系统文档、同步Git和GitHub',
                    'is_current': 0
                },
                {
                    'version': 'v15.5.0',
                    'major': 15,
                    'minor': 5,
                    'patch': 0,
                    'build_number': '20260719b',
                    'build_date': '2026-07-19',
                    'codename': 'Exam System Enhancement Suite',
                    'status': 'stable',
                    'description': '考试系统首页、自定义练习、积分商城、学生门户路由修复',
                    'upgrade_notes': '从v7.7.0升级：考试系统首页完善、自定义练习页面完善、积分商城页面完善',
                    'is_current': 0
                },
                {
                    'version': 'v7.7.0',
                    'major': 7,
                    'minor': 7,
                    'patch': 0,
                    'build_number': '20260713a',
                    'build_date': '2026-07-13',
                    'codename': 'AI-Powered Comprehensive Enhancement Suite',
                    'status': 'stable',
                    'description': '防火墙系统升级、AI脑库知识完善、错题智能诊断、自动修复引擎、预防式维护、UI组件库增强',
                    'upgrade_notes': '从v7.6.0升级：防火墙系统升级、AI脑库知识完善',
                    'is_current': 0
                },
                {
                    'version': 'v7.6.0',
                    'major': 7,
                    'minor': 6,
                    'patch': 0,
                    'build_number': '20260710a',
                    'build_date': '2026-07-10',
                    'codename': 'Comprehensive System Upgrade Suite',
                    'status': 'stable',
                    'description': '全面系统升级套件',
                    'upgrade_notes': '从v7.3.0升级：全面系统升级',
                    'is_current': 0
                }
            ]
            
            for v in versions:
                cursor.execute(''' INSERT INTO system_version (version, major, minor, patch, build_number, build_date, codename, status, description, upgrade_notes, is_current) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (v['version'], v['major'], v['minor'], v['patch'], v['build_number'],
                      v['build_date'], v['codename'], v['status'], v['description'],
                      v['upgrade_notes'], v['is_current']))
                
                version_id = cursor.lastrowid
                
                features_map = {
                    'v15.6.1': [
                        '系统升级中心页面全面完善',
                        '版本管理API完善',
                        '系统维护功能',
                        '数据库版本存储',
                        '历史记录管理'
                    ],
                    'v15.6.0': [
                        'AI自动扩展页面完善',
                        'GitHub同步页面完善',
                        '系统升级中心完善',
                        '备份管理页面完善',
                        '布局管理页面完善',
                        '错题本页面完善'
                    ],
                    'v15.5.0': [
                        '考试系统首页完善',
                        '自定义练习页面完善',
                        '积分商城页面完善',
                        '学生门户路由修复'
                    ],
                    'v7.7.0': [
                        '防火墙系统升级',
                        'AI脑库知识完善',
                        '错题智能诊断',
                        '自动修复引擎',
                        '预防式维护',
                        'UI组件库增强'
                    ]
                }
                
                features = features_map.get(v['version'], [])
                for idx, feature in enumerate(features):
                    cursor.execute(''' INSERT INTO system_version_features (version_id, feature_text, sort_order) VALUES (?, ?, ?) ''', (version_id, feature, idx))
        
        cursor.execute('SELECT COUNT(*) FROM system_changelog')
        if cursor.fetchone()[0] == 0:
            changelog_entries = [
                ('v15.6.1', 'System Upgrade Center Enhancement', '2026-07-20', 'feature', '系统升级中心页面全面完善',
                '升级统计、检查更新、执行升级、升级历史、系统维护、实时日志面板'),
                ('v15.6.1', 'System Upgrade Center Enhancement', '2026-07-20', 'feature', '版本管理API完善',
                '检查更新、执行升级、版本历史、版本统计、更新日志接口'),
                ('v15.6.1', 'System Upgrade Center Enhancement', '2026-07-20', 'improvement', '升级中心响应式设计', '适配桌面端和移动端'),
                ('v15.6.0', 'System Comprehensive Enhancement Suite', '2026-07-19', 'feature', 'AI自动扩展页面完善',
                '统计卡片、扩展控制、扩展历史、实时日志面板'),
                ('v15.6.0', 'System Comprehensive Enhancement Suite', '2026-07-19', 'feature', 'GitHub同步页面完善',
                '同步状态、仓库信息、分支选择、同步操作面板'),
                ('v15.6.0', 'System Comprehensive Enhancement Suite', '2026-07-19', 'feature', '备份管理页面完善',
                '备份操作、自动备份计划、备份历史记录'),
                ('v15.5.0', 'Exam System Enhancement Suite', '2026-07-19', 'feature', '考试系统首页完善', '整合所有考试功能入口'),
                ('v15.5.0', 'Exam System Enhancement Suite', '2026-07-19', 'feature', '自定义练习页面完善', '完整的练习创建表单'),
                ('v15.5.0', 'Exam System Enhancement Suite', '2026-07-19', 'feature', '积分商城页面完善', '商品网格展示和兑换功能'),
                ('v7.7.0', 'AI-Powered Comprehensive Enhancement Suite', '2026-07-13', 'feature', '防火墙系统升级',
                'SQL注入/XSS/命令注入/SSRF防护'),
                ('v7.7.0', 'AI-Powered Comprehensive Enhancement Suite', '2026-07-13', 'feature', 'AI脑库知识完善',
                '90+知识分类，知识关联网络'),
                ('v7.7.0', 'AI-Powered Comprehensive Enhancement Suite', '2026-07-13', 'feature', '自动修复引擎',
                '8种修复能力，100%修复成功率')
            ]
            
            for idx, entry in enumerate(changelog_entries):
                cursor.execute(''' INSERT INTO system_changelog (version, codename, release_date, change_type, change_title, change_description, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (*entry, idx))
        
        cursor.execute('SELECT COUNT(*) FROM system_history')
        if cursor.fetchone()[0] == 0:
            history_events = [
                ('system_init', 'system', '系统初始化完成', 'MTSCOS AI系统启动完成', 'v15.6.1', 'system', datetime.now().isoformat(),
                '{"status": "success"}'),
                ('database_create', 'system', '数据库表创建完成', '系统版本相关数据表创建完成', 'v15.6.1', 'system',
                datetime.now().isoformat(), '{"tables": ["system_version", "system_version_features", "system_upgrade_records", "system_changelog", "system_history", "system_metrics"]}'),
                ('data_init', 'system', '初始数据导入完成', '版本数据、更新日志、历史记录导入完成', 'v15.6.1', 'system',
                datetime.now().isoformat(), '{"versions": 5, "features": 20, "changelog": 12, "history": 3}'),
                ('version_set', 'system', '当前版本设置', '设置当前版本为v15.6.1', 'v15.6.1', 'system', datetime.now().isoformat(),
                '{"version": "v15.6.1", "codename": "System Upgrade Center Enhancement"}')
            ]
            
            for event in history_events:
                cursor.execute(''' INSERT INTO system_history (event_type, event_category, event_title, event_description, related_version, operator, timestamp, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', event)
        
        conn.commit()
        conn.close()

    def get_current_version(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM system_version WHERE is_current = 1 LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_version_dict(row)
        return None

    def get_version_by_number(self, version):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM system_version WHERE version = ?', (version,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_version_dict(row)
        return None

    def get_all_versions(self):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM system_version ORDER BY major DESC, minor DESC, patch DESC')
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_version_dict(row) for row in rows]

    def _row_to_version_dict(self, row):
        version_dict = {
            'id': row[0],
            'version': row[1],
            'major': row[2],
            'minor': row[3],
            'patch': row[4],
            'build_number': row[5],
            'build_date': row[6],
            'codename': row[7],
            'status': row[8],
            'description': row[9],
            'upgrade_notes': row[10],
            'is_current': bool(row[11]),
            'created_at': row[12],
            'updated_at': row[13]
        }
        
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT feature_text FROM system_version_features WHERE version_id = ? ORDER BY sort_order',
        (row[0],))
        version_dict['features'] = [r[0] for r in cursor.fetchall()]
        conn.close()
        
        return version_dict

    def add_version(self, version_data):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE system_version SET is_current = 0 WHERE is_current = 1')
        
        cursor.execute(''' INSERT INTO system_version (version, major, minor, patch, build_number, build_date, codename, status, description, upgrade_notes, is_current) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (version_data['version'], version_data['major'], version_data['minor'],
              version_data['patch'], version_data.get('build_number', ''), 
              version_data.get('build_date', ''), version_data.get('codename', ''),
              version_data.get('status', 'stable'), version_data.get('description', ''),
              version_data.get('upgrade_notes', ''), 1))
        
        version_id = cursor.lastrowid
        
        for idx, feature in enumerate(version_data.get('features', [])):
            cursor.execute(''' INSERT INTO system_version_features (version_id, feature_text, sort_order) VALUES (?, ?, ?) ''', (version_id, feature, idx))
        
        conn.commit()
        conn.close()
        
        self.add_history('version_add', 'system', '版本添加', 
                        f'添加新版本 {version_data["version"]}', 
                        version_data['version'], 'system')
        
        return version_id

    def record_upgrade(self, upgrade_id, version_from, version_to, status='pending', 
                       operator='system', error_message='', log_text=''):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute(''' INSERT INTO system_upgrade_records (upgrade_id, version_from, version_to, status, operator) VALUES (?, ?, ?, ?, ?) ''', (upgrade_id, version_from, version_to, status, operator))
        
        conn.commit()
        conn.close()
        
        self.add_history('upgrade_start', 'system', '升级开始', 
                        f'从 {version_from} 升级到 {version_to}', 
                        version_to, operator)
        
        return cursor.lastrowid

    def update_upgrade_status(self, upgrade_id, status, completed_at=None, error_message='', log_text=''):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        if completed_at is None:
            completed_at = datetime.now().isoformat()
        
        cursor.execute(''' UPDATE system_upgrade_records SET status = ?, completed_at = ?, error_message = ?, log_text = ? WHERE upgrade_id = ? ''', (status, completed_at, error_message, log_text, upgrade_id))
        
        conn.commit()
        conn.close()
        
        if status == 'success':
            self.add_history('upgrade_success', 'system', '升级成功', 
                            f'升级完成: {upgrade_id}', '', 'system')
        elif status == 'failed':
            self.add_history('upgrade_failed', 'system', '升级失败', 
                            f'升级失败: {upgrade_id}, 错误: {error_message}', '', 'system')

    def get_upgrade_records(self, limit=20):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM system_upgrade_records ORDER BY started_at DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_upgrade_dict(row) for row in rows]

    def _row_to_upgrade_dict(self, row):
        return {
            'id': row[0],
            'upgrade_id': row[1],
            'version_from': row[2],
            'version_to': row[3],
            'status': row[4],
            'started_at': row[5],
            'completed_at': row[6],
            'upgrade_type': row[7],
            'operator': row[8],
            'error_message': row[9],
            'log_text': row[10]
        }

    def get_changelog(self, version=None, limit=20):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        if version:
            cursor.execute('SELECT * FROM system_changelog WHERE version = ? ORDER BY sort_order', (version,))
        else:
            cursor.execute('SELECT * FROM system_changelog ORDER BY release_date DESC, sort_order LIMIT ?', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_changelog_dict(row) for row in rows]

    def _row_to_changelog_dict(self, row):
        return {
            'id': row[0],
            'version': row[1],
            'codename': row[2],
            'release_date': row[3],
            'change_type': row[4],
            'change_title': row[5],
            'change_description': row[6],
            'sort_order': row[7],
            'created_at': row[8]
        }

    def add_changelog_entry(self, version, codename, release_date, change_type, 
                           change_title, change_description):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COALESCE(MAX(sort_order), 0) FROM system_changelog WHERE version = ?', (version,))
        max_order = cursor.fetchone()[0]
        
        cursor.execute(''' INSERT INTO system_changelog (version, codename, release_date, change_type, change_title, change_description, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (version, codename, release_date, change_type, change_title, change_description, max_order + 1))
        
        conn.commit()
        conn.close()
        
        return cursor.lastrowid

    def add_history(self, event_type, event_category, event_title, event_description,
                    related_version='', operator='system', details=None):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        details_json = json.dumps(details) if details else '{}'
        
        cursor.execute(''' INSERT INTO system_history (event_type, event_category, event_title, event_description, related_version, operator, timestamp, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (event_type, event_category, event_title, event_description,
              related_version, operator, datetime.now().isoformat(), details_json))
        
        conn.commit()
        conn.close()
        
        return cursor.lastrowid

    def get_history(self, event_type=None, event_category=None, limit=50):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM system_history WHERE 1=1'
        params = []
        
        if event_type:
            query += ' AND event_type = ?'
            params.append(event_type)
        
        if event_category:
            query += ' AND event_category = ?'
            params.append(event_category)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_history_dict(row) for row in rows]

    def _row_to_history_dict(self, row):
        try:
            details = json.loads(row[7]) if row[7] else {}
        except Exception as e:
            details = {}
        
        return {
            'id': row[0],
            'event_type': row[1],
            'event_category': row[2],
            'event_title': row[3],
            'event_description': row[4],
            'related_version': row[5],
            'operator': row[6],
            'timestamp': row[7],
            'details': details
        }

    def set_metric(self, metric_key, metric_value, metric_type='integer', category='system'):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        cursor.execute(''' INSERT OR REPLACE INTO system_metrics (metric_key, metric_value, metric_type, category, recorded_at) VALUES (?, ?, ?, ?, ?) ''', (metric_key, str(metric_value), metric_type, category, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True

    def get_metric(self, metric_key):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM system_metrics WHERE metric_key = ?', (metric_key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'metric_key': row[1],
                'metric_value': row[2],
                'metric_type': row[3],
                'category': row[4],
                'recorded_at': row[5]
            }
        return None

    def get_all_metrics(self, category=None):
        conn = sqlite3.connect(self._db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('SELECT * FROM system_metrics WHERE category = ?', (category,))
        else:
            cursor.execute('SELECT * FROM system_metrics')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'metric_key': row[1],
            'metric_value': row[2],
            'metric_type': row[3],
            'category': row[4],
            'recorded_at': row[5]
        } for row in rows]

system_version_db = SystemVersionDatabase()