#!/usr/bin/env python3
import os
from datetime import datetime

class VersionService:
    def __init__(self):
        self._db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'app.db'
        )
        self._init_db_service()

    def _init_db_service(self):
        try:
            from app.services.system_version_db import system_version_db
            self.db = system_version_db
        except ImportError:
            self.db = None

    def get_version_for_template(self):
        if self.db:
            version_data = self.db.get_current_version()
            if version_data:
                return version_data
        
        return {
            'version': 'v15.6.1',
            'codename': 'System Upgrade Center Enhancement',
            'build_number': '20260720a',
            'build_date': '2026-07-20',
            'status': 'stable',
            'description': '系统升级中心全面完善，版本管理API，系统维护功能',
            'features': [
                '系统升级中心页面全面完善',
                '版本管理API完善',
                '系统维护功能',
                '数据库版本存储',
                '历史记录管理'
            ],
            'upgrade_notes': '从v15.6.0升级：系统升级中心页面完善、数据库版本存储、历史记录管理'
        }

    def get_current_version(self):
        if self.db:
            return self.db.get_current_version()
        return None

    def get_all_versions(self):
        if self.db:
            return self.db.get_all_versions()
        return []

    def get_version_by_number(self, version):
        if self.db:
            return self.db.get_version_by_number(version)
        return None

    def increment_version(self, level='patch'):
        if self.db:
            current = self.db.get_current_version()
            if current:
                major = current['major']
                minor = current['minor']
                patch = current['patch']
                
                if level == 'major':
                    major += 1
                    minor = 0
                    patch = 0
                elif level == 'minor':
                    minor += 1
                    patch = 0
                else:
                    patch += 1
                
                new_version = f'v{major}.{minor}.{patch}'
                
                version_data = {
                    'version': new_version,
                    'major': major,
                    'minor': minor,
                    'patch': patch,
                    'build_number': f'{datetime.now().strftime("%Y%m%d")}a',
                    'build_date': datetime.now().strftime('%Y-%m-%d'),
                    'codename': f'{new_version} Edition',
                    'status': 'stable',
                    'description': f'版本升级至 {new_version}',
                    'upgrade_notes': f'从 {current["version"]} 升级至 {new_version}',
                    'features': []
                }
                
                self.db.add_version(version_data)
                return new_version
        
        return None

    def get_changelog(self, version=None, limit=20):
        if self.db:
            return self.db.get_changelog(version, limit)
        return []

    def get_history(self, event_type=None, event_category=None, limit=50):
        if self.db:
            return self.db.get_history(event_type, event_category, limit)
        return []

    def get_upgrade_records(self, limit=20):
        if self.db:
            return self.db.get_upgrade_records(limit)
        return []

    def record_upgrade(self, upgrade_id, version_from, version_to, status='pending', 
                       operator='system', error_message='', log_text=''):
        if self.db:
            return self.db.record_upgrade(upgrade_id, version_from, version_to, status, 
                                          operator, error_message, log_text)
        return None

    def update_upgrade_status(self, upgrade_id, status, completed_at=None, error_message='', log_text=''):
        if self.db:
            return self.db.update_upgrade_status(upgrade_id, status, completed_at, error_message, log_text)
        return None

    def add_history(self, event_type, event_category, event_title, event_description,
                    related_version='', operator='system', details=None):
        if self.db:
            return self.db.add_history(event_type, event_category, event_title, 
                                      event_description, related_version, operator, details)
        return None

    def set_metric(self, metric_key, metric_value, metric_type='integer', category='system'):
        if self.db:
            return self.db.set_metric(metric_key, metric_value, metric_type, category)
        return False

    def get_metric(self, metric_key):
        if self.db:
            return self.db.get_metric(metric_key)
        return None

    def get_all_metrics(self, category=None):
        if self.db:
            return self.db.get_all_metrics(category)
        return []

version_service = VersionService()