#!/usr/bin/env python3
import os
import json
import time
import sqlite3
import threading
import importlib
import inspect
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.middlewares.access_control import require_login, require_admin

system_extension_api = Bluelogger.info('extension_api', __name__)

class SystemExtensionManager:
    EXTENSION_TYPES = ['plugin', 'middleware', 'api', 'service', 'ui_component', 'data_processor']
    
    def __init__(self):
        self.extensions = {}
        self.active_extensions = set()
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('system_extensions.db')
            cursor = conn.cursor()
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS extensions ( id INTEGER PRIMARY KEY AUTOINCREMENT, extension_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL, type TEXT NOT NULL, version TEXT DEFAULT '1.0.0', description TEXT, author TEXT, status TEXT DEFAULT 'inactive', install_path TEXT, entry_point TEXT, dependencies TEXT, settings TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, installed_at TEXT, enabled_at TEXT ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS extension_settings ( id INTEGER PRIMARY KEY AUTOINCREMENT, extension_id TEXT NOT NULL, setting_key TEXT NOT NULL, setting_value TEXT, setting_type TEXT DEFAULT 'string', description TEXT, is_required INTEGER DEFAULT 0, UNIQUE(extension_id, setting_key) ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS extension_history ( id INTEGER PRIMARY KEY AUTOINCREMENT, extension_id TEXT NOT NULL, action_type TEXT NOT NULL, action_content TEXT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP, operator TEXT ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS extension_dependencies ( id INTEGER PRIMARY KEY AUTOINCREMENT, extension_id TEXT NOT NULL, dependency_id TEXT NOT NULL, min_version TEXT DEFAULT '0.0.0' ) ''')
            
            conn.commit()
            conn.close()
            logger.info("[System Extension API] 数据库表创建完成")
        except Exception as e:
            logger.info(f"[System Extension API] 创建表失败: {e}")
    
    def register_extension(self, extension_id, name, extension_type, description='', 
                          author='system', install_path='', entry_point='', dependencies=None):
        try:
            conn = sqlite3.connect('system_extensions.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM extensions WHERE extension_id = ?', (extension_id,))
            if cursor.fetchone()[0] > 0:
                conn.close()
                return {'error': '扩展已存在'}
            
            cursor.execute(''' INSERT INTO extensions (extension_id, name, type, description, author, install_path, entry_point, dependencies) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (
                extension_id,
                name,
                extension_type,
                description,
                author,
                install_path,
                entry_point,
                json.dumps(dependencies or [])
            ))
            
            cursor.execute(''' INSERT INTO extension_history (extension_id, action_type, action_content, operator) VALUES (?, ?, ?, ?) ''', (extension_id, 'registered', f'注册扩展: {name}', author))
            
            conn.commit()
            conn.close()
            
            self.extensions[extension_id] = {
                'name': name,
                'type': extension_type,
                'status': 'inactive',
                'description': description,
                'version': '1.0.0'
            }
            
            return {'success': True, 'extension_id': extension_id, 'name': name}
        except Exception as e:
            logger.info(f"[System Extension API] 注册扩展失败: {e}")
            return {'error': str(e)}
    
    def install_extension(self, extension_id):
        try:
            conn = sqlite3.connect('system_extensions.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM extensions WHERE extension_id = ?', (extension_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return {'error': '扩展不存在'}
            
            if row[6] == 'active':
                conn.close()
                return {'error': '扩展已激活'}
            
            entry_point = row[9]
            if entry_point:
                try:
                    module_path = entry_point.replace('.py', '').replace('/', '.')
                    module = importlib.import_module(module_path)
                    
                    if hasattr(module, 'install'):
                        module.install()
                except Exception as e:
                    logger.info(f"[System Extension API] 执行安装脚本失败: {e}")
            
            cursor.execute(''' UPDATE extensions SET status = ?, installed_at = ?, updated_at = ? WHERE extension_id = ? ''', ('installed', datetime.now().isoformat(), datetime.now().isoformat(), extension_id))
            
            cursor.execute(''' INSERT INTO extension_history (extension_id, action_type, action_content, operator) VALUES (?, ?, ?, ?) ''', (extension_id, 'installed', '安装扩展', 'system'))
            
            conn.commit()
            conn.close()
            
            if extension_id in self.extensions:
                self.extensions[extension_id]['status'] = 'installed'
            
            return {'success': True, 'extension_id': extension_id, 'status': 'installed'}
        except Exception as e:
            logger.info(f"[System Extension API] 安装扩展失败: {e}")
            return {'error': str(e)}
    
    def enable_extension(self, extension_id):
        try:
            conn = sqlite3.connect('system_extensions.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM extensions WHERE extension_id = ?', (extension_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return {'error': '扩展不存在'}
            
            if row[6] == 'active':
                conn.close()
                return {'error': '扩展已启用'}
            
            if row[6] == 'inactive':
                return {'error': '扩展未安装，请先安装'}
            
            entry_point = row[9]
            if entry_point:
                try:
                    module_path = entry_point.replace('.py', '').replace('/', '.')
                    module = importlib.import_module(module_path)
                    
                    if hasattr(module, 'enable'):
                        module.enable()
                except Exception as e:
                    logger.info(f"[System Extension API] 执行启用脚本失败: {e}")
            
            cursor.execute(''' UPDATE extensions SET status = ?, enabled_at = ?, updated_at = ? WHERE extension_id = ? ''', ('active', datetime.now().isoformat(), datetime.now().isoformat(), extension_id))
            
            cursor.execute(''' INSERT INTO extension_history (extension_id, action_type, action_content, operator) VALUES (?, ?, ?, ?) ''', (extension_id, 'enabled', '启用扩展', 'system'))
            
            conn.commit()
            conn.close()
            
            self.extensions[extension_id]['status'] = 'active'
            self.active_extensions.add(extension_id)
            
            return {'success': True, 'extension_id': extension_id, 'status': 'active'}
        except Exception as e:
            logger.info(f"[System Extension API] 启用扩展失败: {e}")
            return {'error': str(e)}
    
    def disable_extension(self, extension_id):
        try:
            conn = sqlite3.connect('system_extensions.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM extensions WHERE extension_id = ?', (extension_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return {'error': '扩展不存在'}
            
            if row[6] != 'active':
                conn.close()
                return {'error': '扩展未启用'}
            
            entry_point = row[9]
            if entry_point:
                try:
                    module_path = entry_point.replace('.py', '').replace('/', '.')
                    module = importlib.import_module(module_path)
                    
                    if hasattr(module, 'disable'):
                        module.disable()
                except Exception as e:
                    logger.info(f"[System Extension API] 执行禁用脚本失败: {e}")
            
            cursor.execute(''' UPDATE extensions SET status = ?, updated_at = ? WHERE extension_id = ? ''', ('installed', datetime.now().isoformat(), extension_id))
            
            cursor.execute(''' INSERT INTO extension_history (extension_id, action_type, action_content, operator) VALUES (?, ?, ?, ?) ''', (extension_id, 'disabled', '禁用扩展', 'system'))
            
            conn.commit()
            conn.close()
            
            if extension_id in self.extensions:
                self.extensions[extension_id]['status'] = 'installed'
            self.active_extensions.discard(extension_id)
            
            return {'success': True, 'extension_id': extension_id, 'status': 'installed'}
        except Exception as e:
            logger.info(f"[System Extension API] 禁用扩展失败: {e}")
            return {'error': str(e)}
    
    def uninstall_extension(self, extension_id):
        try:
            conn = sqlite3.connect('system_extensions.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM extensions WHERE extension_id = ?', (extension_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return {'error': '扩展不存在'}
            
            if row[6] == 'active':
                return {'error': '扩展正在运行，请先禁用'}
            
            entry_point = row[9]
            if entry_point:
                try:
                    module_path = entry_point.replace('.py', '').replace('/', '.')
                    module = importlib.import_module(module_path)
                    
                    if hasattr(module, 'uninstall'):
                        module.uninstall()
                except Exception as e:
                    logger.info(f"[System Extension API] 执行卸载脚本失败: {e}")
            
            cursor.execute('DELETE FROM extensions WHERE extension_id = ?', (extension_id,))
            cursor.execute('DELETE FROM extension_settings WHERE extension_id = ?', (extension_id,))
            cursor.execute('DELETE FROM extension_dependencies WHERE extension_id = ?', (extension_id,))
            
            cursor.execute(''' INSERT INTO extension_history (extension_id, action_type, action_content, operator) VALUES (?, ?, ?, ?) ''', (extension_id, 'uninstalled', '卸载扩展', 'system'))
            
            conn.commit()
            conn.close()
            
            if extension_id in self.extensions:
                del self.extensions[extension_id]
            self.active_extensions.discard(extension_id)
            
            return {'success': True, 'extension_id': extension_id}
        except Exception as e:
            logger.info(f"[System Extension API] 卸载扩展失败: {e}")
            return {'error': str(e)}
    
    def get_all_extensions(self):
        try:
            conn = sqlite3.connect('system_extensions.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM extensions ORDER BY name')
            rows = cursor.fetchall()
            conn.close()
            
            extensions = []
            for row in rows:
                extensions.append({
                    'extension_id': row[1],
                    'name': row[2],
                    'type': row[3],
                    'version': row[4],
                    'description': row[5],
                    'author': row[6],
                    'status': row[7],
                    'install_path': row[8],
                    'entry_point': row[9],
                    'dependencies': json.loads(row[10]) if row[10] else [],
                    'settings': json.loads(row[11]) if row[11] else {},
                    'created_at': row[12],
                    'updated_at': row[13],
                    'installed_at': row[14],
                    'enabled_at': row[15]
                })
            
            return extensions
        except Exception as e:
            logger.info(f"[System Extension API] 获取所有扩展失败: {e}")
            return []
    
    def get_extension(self, extension_id):
        try:
            conn = sqlite3.connect('system_extensions.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM extensions WHERE extension_id = ?', (extension_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'extension_id': row[1],
                    'name': row[2],
                    'type': row[3],
                    'version': row[4],
                    'description': row[5],
                    'author': row[6],
                    'status': row[7],
                    'install_path': row[8],
                    'entry_point': row[9],
                    'dependencies': json.loads(row[10]) if row[10] else [],
                    'settings': json.loads(row[11]) if row[11] else {},
                    'created_at': row[12],
                    'updated_at': row[13],
                    'installed_at': row[14],
                    'enabled_at': row[15]
                }
            return None
        except Exception as e:
            logger.info(f"[System Extension API] 获取扩展失败: {e}")
            return None
    
    def set_extension_settings(self, extension_id, settings):
        try:
            conn = sqlite3.connect('system_extensions.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM extensions WHERE extension_id = ?', (extension_id,))
            if cursor.fetchone()[0] == 0:
                conn.close()
                return {'error': '扩展不存在'}
            
            for key, value in settings.items():
                cursor.execute(''' INSERT OR REPLACE INTO extension_settings (extension_id, setting_key, setting_value) VALUES (?, ?, ?) ''', (extension_id, key, str(value)))
            
            cursor.execute(''' UPDATE extensions SET settings = ?, updated_at = ? WHERE extension_id = ? ''', (json.dumps(settings), datetime.now().isoformat(), extension_id))
            
            conn.commit()
            conn.close()
            
            if extension_id in self.extensions:
                self.extensions[extension_id]['settings'] = settings
            
            return {'success': True, 'extension_id': extension_id, 'settings': settings}
        except Exception as e:
            logger.info(f"[System Extension API] 设置扩展配置失败: {e}")
            return {'error': str(e)}
    
    def get_extension_settings(self, extension_id):
        try:
            conn = sqlite3.connect('system_extensions.db')
            cursor = conn.cursor()
            cursor.execute('SELECT setting_key, setting_value, setting_type, description FROM extension_settings WHERE extension_id = ?', (extension_id,))
            rows = cursor.fetchall()
            conn.close()
            
            settings = {}
            for row in rows:
                settings[row[0]] = {
                    'value': row[1],
                    'type': row[2],
                    'description': row[3]
                }
            
            return settings
        except Exception as e:
            logger.info(f"[System Extension API] 获取扩展配置失败: {e}")
            return {}
    
    def get_extension_history(self, extension_id):
        try:
            conn = sqlite3.connect('system_extensions.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM extension_history WHERE extension_id = ? ORDER BY timestamp DESC',
            (extension_id,))
            rows = cursor.fetchall()
            conn.close()
            
            history = []
            for row in rows:
                history.append({
                    'action_type': row[2],
                    'action_content': row[3],
                    'timestamp': row[4],
                    'operator': row[5]
                })
            
            return history
        except Exception as e:
            logger.info(f"[System Extension API] 获取扩展历史失败: {e}")
            return []
    
    def get_extension_summary(self):
        try:
            conn = sqlite3.connect('system_extensions.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM extensions')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM extensions WHERE status = "active"')
            active = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM extensions WHERE status = "installed"')
            installed = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM extensions WHERE status = "inactive"')
            inactive = cursor.fetchone()[0]
            
            cursor.execute('SELECT type, COUNT(*) FROM extensions GROUP BY type')
            type_counts = {}
            for row in cursor.fetchall():
                type_counts[row[0]] = row[1]
            
            conn.close()
            
            return {
                'total_extensions': total,
                'active_extensions': active,
                'installed_extensions': installed,
                'inactive_extensions': inactive,
                'type_distribution': type_counts,
                'active_rate': (active / total * 100) if total > 0 else 0
            }
        except Exception as e:
            logger.info(f"[System Extension API] 获取扩展摘要失败: {e}")
            return {}
    
    def scan_and_register_plugins(self, plugin_dir='extensions'):
        if not os.path.exists(plugin_dir):
            return {'success': True, 'scanned': 0, 'registered': 0}
        
        scanned = 0
        registered = 0
        
        for item in os.listdir(plugin_dir):
            item_path = os.path.join(plugin_dir, item)
            if os.path.isdir(item_path):
                manifest_file = os.path.join(item_path, 'manifest.json')
                if os.path.exists(manifest_file):
                    scanned += 1
                    try:
                        with open(manifest_file, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                        
                        result = self.register_extension(
                            manifest.get('extension_id', item),
                            manifest.get('name', item),
                            manifest.get('type', 'plugin'),
                            manifest.get('description', ''),
                            manifest.get('author', 'unknown'),
                            item_path,
                            manifest.get('entry_point', '')
                        )
                        
                        if result.get('success'):
                            registered += 1
                    except Exception as e:
                        logger.info(f"[System Extension API] 扫描插件 {item} 失败: {e}")
        
        return {'success': True, 'scanned': scanned, 'registered': registered}

extension_manager = SystemExtensionManager()

@system_extension_api.route('/api/extensions', methods=['GET'])
@require_login
def get_extensions():
    result = extension_manager.get_all_extensions()
    return jsonify({'success': True, 'data': result})

@system_extension_api.route('/api/extensions/<extension_id>', methods=['GET'])
@require_login
def get_extension(extension_id):
    result = extension_manager.get_extension(extension_id)
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': '扩展不存在'}), 404

@system_extension_api.route('/api/extensions', methods=['POST'])
@require_admin
def register_extension():
    data = request.get_json() or {}
    extension_id = data.get('extension_id')
    name = data.get('name')
    extension_type = data.get('type')
    
    if not extension_id or not name or not extension_type:
        return jsonify({'success': False, 'error': '扩展ID、名称和类型不能为空'}), 400
    
    result = extension_manager.register_extension(
        extension_id,
        name,
        extension_type,
        data.get('description', ''),
        data.get('author', 'system'),
        data.get('install_path', ''),
        data.get('entry_point', ''),
        data.get('dependencies')
    )
    
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@system_extension_api.route('/api/extensions/<extension_id>/install', methods=['POST'])
@require_admin
def install_extension(extension_id):
    result = extension_manager.install_extension(extension_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@system_extension_api.route('/api/extensions/<extension_id>/enable', methods=['POST'])
@require_admin
def enable_extension(extension_id):
    result = extension_manager.enable_extension(extension_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@system_extension_api.route('/api/extensions/<extension_id>/disable', methods=['POST'])
@require_admin
def disable_extension(extension_id):
    result = extension_manager.disable_extension(extension_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@system_extension_api.route('/api/extensions/<extension_id>/uninstall', methods=['POST'])
@require_admin
def uninstall_extension(extension_id):
    result = extension_manager.uninstall_extension(extension_id)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@system_extension_api.route('/api/extensions/<extension_id>/settings', methods=['GET'])
@require_login
def get_settings(extension_id):
    result = extension_manager.get_extension_settings(extension_id)
    return jsonify({'success': True, 'data': result})

@system_extension_api.route('/api/extensions/<extension_id>/settings', methods=['POST'])
@require_admin
def set_settings(extension_id):
    data = request.get_json() or {}
    settings = data.get('settings', {})
    
    if not settings:
        return jsonify({'success': False, 'error': '配置项不能为空'}), 400
    
    result = extension_manager.set_extension_settings(extension_id, settings)
    if result.get('success'):
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': result.get('error')}), 400

@system_extension_api.route('/api/extensions/<extension_id>/history', methods=['GET'])
@require_login
def get_history(extension_id):
    result = extension_manager.get_extension_history(extension_id)
    return jsonify({'success': True, 'data': result})

@system_extension_api.route('/api/extensions/summary', methods=['GET'])
@require_login
def get_summary():
    result = extension_manager.get_extension_summary()
    return jsonify({'success': True, 'data': result})

@system_extension_api.route('/api/extensions/scan', methods=['POST'])
@require_admin
def scan_plugins():
    data = request.get_json() or {}
    plugin_dir = data.get('plugin_dir', 'extensions')
    result = extension_manager.scan_and_register_plugins(plugin_dir)
    return jsonify({'success': True, 'data': result})