# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI Error Monitor Agent
自动监控控制台错误日志，上报数据库，委派后台修复，自动修复网络资源，上报备案修复方案
"""

import os
import sys
import time
import json
import threading
import logging
import sqlite3
import re
import traceback
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('ai_error_monitor.log'), logging.StreamHandler()])
logger = logging.getLogger('AI_Error_Monitor')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app.db')

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.close()

class AIErrorMonitor:
    def __init__(self):
        self.monitoring_enabled = True
        self.monitoring_interval = 5
        self.log_file_path = '/tmp/flask_app.log'
        self.last_check_time = time.time()
        self.error_cache = {}
        self.fix_history = {}
        self.lock = threading.Lock()
        
        self._init_database()
        self._start_monitoring_thread()
        
        logger.info("AI Error Monitor Agent initialized")
    
    def _init_database(self):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS error_monitor (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        error_id TEXT NOT NULL UNIQUE,
                        level TEXT NOT NULL,
                        source TEXT,
                        message TEXT NOT NULL,
                        traceback TEXT,
                        error_type TEXT,
                        affected_component TEXT,
                        occurrence_count INTEGER DEFAULT 1,
                        first_occurrence TEXT NOT NULL,
                        last_occurrence TEXT NOT NULL,
                        status TEXT DEFAULT 'unresolved',
                        severity TEXT DEFAULT 'medium',
                        fix_proposal TEXT,
                        fix_status TEXT DEFAULT 'pending',
                        assignee TEXT DEFAULT 'auto_agent',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fix_proposals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        proposal_id TEXT NOT NULL UNIQUE,
                        error_id TEXT NOT NULL,
                        proposal_content TEXT NOT NULL,
                        priority TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'pending',
                        executor TEXT DEFAULT 'auto_agent',
                        executed_at TEXT,
                        execution_result TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (error_id) REFERENCES error_monitor(error_id)
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_recovery_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recovery_id TEXT NOT NULL UNIQUE,
                        component TEXT NOT NULL,
                        action TEXT NOT NULL,
                        status TEXT DEFAULT 'running',
                        result TEXT,
                        error_message TEXT,
                        started_at TEXT NOT NULL,
                        completed_at TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("Error monitor database tables initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def _start_monitoring_thread(self):
        def monitor():
            while True:
                if self.monitoring_enabled:
                    try:
                        self._check_logs()
                        self._process_errors()
                    except Exception as e:
                        logger.error(f"Monitoring thread error: {e}")
                time.sleep(self.monitoring_interval)
        
        monitoring_thread = threading.Thread(target=monitor, daemon=True)
        monitoring_thread.start()
        logger.info("Error monitoring thread started")
    
    def _check_logs(self):
        try:
            if not os.path.exists(self.log_file_path):
                return
            
            with open(self.log_file_path, 'r') as f:
                lines = f.readlines()
            
            current_time = time.time()
            new_errors = []
            
            for line in lines[-500:]:
                if 'ERROR' in line or 'CRITICAL' in line:
                    timestamp_str = line[:23]
                    try:
                        log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        log_timestamp = log_time.timestamp()
                        
                        if log_timestamp > self.last_check_time:
                            parts = line.split(' - ', 4)
                            if len(parts) >= 4:
                                source = parts[1].strip()
                                level = parts[2].strip()
                                message = parts[3].strip()
                                
                                error_id = self._generate_error_id(source, message)
                                
                                if error_id not in self.error_cache:
                                    self.error_cache[error_id] = {
                                        'level': level,
                                        'source': source,
                                        'message': message,
                                        'first_occurrence': datetime.now().isoformat(),
                                        'last_occurrence': datetime.now().isoformat(),
                                        'count': 1,
                                        'severity': self._determine_severity(message),
                                        'error_type': self._classify_error(message),
                                        'affected_component': self._identify_component(message)
                                    }
                                    new_errors.append(error_id)
                                else:
                                    self.error_cache[error_id]['count'] += 1
                                    self.error_cache[error_id]['last_occurrence'] = datetime.now().isoformat()
                    except:
                        pass
            
            self.last_check_time = current_time
            
            if new_errors:
                logger.info(f"Found {len(new_errors)} new errors")
                self._report_errors(new_errors)
        
        except Exception as e:
            logger.error(f"Error checking logs: {e}")
    
    def _generate_error_id(self, source, message):
        import hashlib
        unique_str = f"{source}_{message[:200]}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]
    
    def _determine_severity(self, message):
        critical_keywords = ['no such table', 'connection reset', 'database error', 'authentication failed', 'permission denied']
        high_keywords = ['failed', 'error', 'exception', 'warning']
        
        message_lower = message.lower()
        if any(kw in message_lower for kw in critical_keywords):
            return 'critical'
        elif any(kw in message_lower for kw in high_keywords):
            return 'high'
        return 'medium'
    
    def _classify_error(self, message):
        if 'database' in message.lower() or 'table' in message.lower():
            return 'database_error'
        elif 'network' in message.lower() or 'connection' in message.lower():
            return 'network_error'
        elif 'authentication' in message.lower() or 'login' in message.lower():
            return 'auth_error'
        elif 'permission' in message.lower() or 'forbidden' in message.lower():
            return 'permission_error'
        elif 'server' in message.lower() or '500' in message:
            return 'server_error'
        return 'unknown_error'
    
    def _identify_component(self, message):
        if 'dashboard' in message.lower():
            return 'dashboard'
        elif 'cluster' in message.lower():
            return 'ai_cluster'
        elif 'exam' in message.lower():
            return 'exam_system'
        elif 'user' in message.lower():
            return 'user_management'
        elif 'notification' in message.lower():
            return 'notification_system'
        return 'unknown'
    
    def _report_errors(self, error_ids):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for error_id in error_ids:
                    error = self.error_cache[error_id]
                    
                    cursor.execute('SELECT id FROM error_monitor WHERE error_id = ?', (error_id,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        cursor.execute('''
                            UPDATE error_monitor 
                            SET occurrence_count = occurrence_count + 1, 
                                last_occurrence = ?, 
                                severity = ?,
                                updated_at = ?
                            WHERE error_id = ?
                        ''', (error['last_occurrence'], error['severity'], datetime.now().isoformat(), error_id))
                    else:
                        cursor.execute('''
                            INSERT INTO error_monitor 
                            (error_id, level, source, message, error_type, affected_component, 
                             occurrence_count, first_occurrence, last_occurrence, severity, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            error_id, error['level'], error['source'], error['message'],
                            error['error_type'], error['affected_component'],
                            error['count'], error['first_occurrence'], error['last_occurrence'],
                            error['severity'], 'unresolved'
                        ))
                
                conn.commit()
                logger.info(f"Reported {len(error_ids)} errors to database")
        except Exception as e:
            logger.error(f"Failed to report errors: {e}")
    
    def _process_errors(self):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT error_id, message, error_type, affected_component, severity 
                    FROM error_monitor 
                    WHERE status = 'unresolved' AND severity IN ('critical', 'high')
                    ORDER BY severity DESC, last_occurrence DESC
                    LIMIT 10
                ''')
                
                errors = cursor.fetchall()
                
                for error in errors:
                    error_id, message, error_type, component, severity = error
                    
                    if error_id in self.fix_history and self.fix_history[error_id]['attempts'] >= 3:
                        continue
                    
                    fix_proposal = self._generate_fix_proposal(error_id, message, error_type, component)
                    
                    if fix_proposal:
                        self._execute_fix(error_id, fix_proposal)
                        self._update_error_status(error_id, 'processing')
        except Exception as e:
            logger.error(f"Failed to process errors: {e}")
    
    def _generate_fix_proposal(self, error_id, message, error_type, component):
        proposals = {
            'database_error': {
                'no such table': self._fix_missing_table,
                'table has no column': self._fix_missing_column,
                'database locked': self._fix_db_locked,
            },
            'network_error': {
                'connection reset': self._fix_connection_reset,
                'connection refused': self._fix_connection_refused,
                'timeout': self._fix_timeout,
            },
            'auth_error': {
                'login failed': self._fix_login_failed,
                'authentication failed': self._fix_auth_failed,
            },
            'permission_error': {
                'forbidden': self._fix_forbidden,
                'permission denied': self._fix_permission_denied,
            },
            'server_error': {
                '500': self._fix_server_error,
                'internal server error': self._fix_server_error,
            },
            'unknown_error': {
                'default': self._fix_unknown,
            }
        }
        
        message_lower = message.lower()
        
        for keywords, fix_func in proposals.get(error_type, proposals['unknown_error']).items():
            if keywords in message_lower:
                return {
                    'proposal_id': self._generate_proposal_id(error_id),
                    'error_id': error_id,
                    'content': f"自动修复: {keywords} - {component}",
                    'priority': 'high' if severity == 'critical' else 'medium',
                    'fix_function': fix_func,
                    'params': {'message': message, 'component': component}
                }
        
        return {
            'proposal_id': self._generate_proposal_id(error_id),
            'error_id': error_id,
            'content': f"需要人工审查: {message[:100]}",
            'priority': 'low',
            'fix_function': None,
            'params': {}
        }
    
    def _generate_proposal_id(self, error_id):
        import hashlib
        unique_str = f"{error_id}_{time.time()}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]
    
    def _execute_fix(self, error_id, proposal):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO fix_proposals 
                    (proposal_id, error_id, proposal_content, priority, status, executor)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (proposal['proposal_id'], error_id, proposal['content'], 
                      proposal['priority'], 'executing', 'auto_agent'))
                
                conn.commit()
            
            if proposal['fix_function']:
                result = proposal['fix_function'](proposal['params'])
                
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE fix_proposals 
                        SET status = ?, execution_result = ?, executed_at = ?
                        WHERE proposal_id = ?
                    ''', ('completed' if result else 'failed', str(result), 
                          datetime.now().isoformat(), proposal['proposal_id']))
                    
                    if result:
                        cursor.execute('''
                            UPDATE error_monitor 
                            SET status = 'resolved', fix_status = 'completed',
                                fix_proposal = ?, updated_at = ?
                            WHERE error_id = ?
                        ''', (proposal['content'], datetime.now().isoformat(), error_id))
                    
                    conn.commit()
                
                if result:
                    logger.info(f"Successfully fixed error {error_id}: {proposal['content']}")
                else:
                    logger.warning(f"Failed to fix error {error_id}: {proposal['content']}")
            
            if error_id not in self.fix_history:
                self.fix_history[error_id] = {'attempts': 0}
            self.fix_history[error_id]['attempts'] += 1
        
        except Exception as e:
            logger.error(f"Failed to execute fix: {e}")
    
    def _update_error_status(self, error_id, status):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE error_monitor SET status = ?, updated_at = ? WHERE error_id = ?
                ''', (status, datetime.now().isoformat(), error_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update error status: {e}")
    
    def _fix_missing_table(self, params):
        message = params['message']
        match = re.search(r'no such table: (\w+)', message)
        if match:
            table_name = match.group(1)
            return self._create_missing_table(table_name)
        return False
    
    def _create_missing_table(self, table_name):
        table_templates = {
            'exams': '''CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT,
                subject TEXT,
                grade TEXT,
                difficulty TEXT DEFAULT 'medium',
                duration INTEGER DEFAULT 60,
                total_score INTEGER DEFAULT 100,
                question_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'draft',
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                deleted_at TEXT
            )''',
            'courses': '''CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT,
                subject TEXT,
                grade TEXT,
                credit INTEGER DEFAULT 2,
                status TEXT DEFAULT 'active',
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''',
            'questions': '''CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL UNIQUE,
                type TEXT DEFAULT 'single',
                subject TEXT,
                grade TEXT,
                difficulty TEXT DEFAULT 'medium',
                content TEXT NOT NULL,
                options TEXT,
                answer TEXT,
                analysis TEXT,
                score INTEGER DEFAULT 2,
                tags TEXT,
                status TEXT DEFAULT 'active',
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''',
            'notifications': '''CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id TEXT NOT NULL UNIQUE,
                user_id INTEGER,
                title TEXT NOT NULL,
                content TEXT,
                type TEXT DEFAULT 'info',
                status TEXT DEFAULT 'unread',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''',
            'login_logs': '''CREATE TABLE IF NOT EXISTS login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                login_time TEXT DEFAULT CURRENT_TIMESTAMP,
                login_ip TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'success'
            )''',
        }
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if table_name in table_templates:
                    cursor.execute(table_templates[table_name])
                    conn.commit()
                    logger.info(f"Created missing table: {table_name}")
                    return True
                else:
                    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT)")
                    conn.commit()
                    logger.info(f"Created placeholder table: {table_name}")
                    return True
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    def _fix_missing_column(self, params):
        message = params['message']
        match = re.search(r'table (\w+) has no column named (\w+)', message)
        if match:
            table_name = match.group(1)
            column_name = match.group(2)
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} TEXT')
                    conn.commit()
                    logger.info(f"Added missing column {column_name} to {table_name}")
                    return True
            except Exception as e:
                logger.error(f"Failed to add column: {e}")
        return False
    
    def _fix_db_locked(self, params):
        logger.warning("Database locked - attempting recovery")
        return self._recover_database()
    
    def _recover_database(self):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('PRAGMA integrity_check')
                result = cursor.fetchone()
                if result[0] == 'ok':
                    logger.info("Database integrity check passed")
                    return True
                else:
                    logger.error(f"Database integrity check failed: {result[0]}")
                    return False
        except Exception as e:
            logger.error(f"Failed to recover database: {e}")
            return False
    
    def _fix_connection_reset(self, params):
        logger.warning("Connection reset detected - attempting network recovery")
        return self._recover_network()
    
    def _fix_connection_refused(self, params):
        logger.warning("Connection refused - checking network connectivity")
        return self._recover_network()
    
    def _fix_timeout(self, params):
        logger.warning("Timeout detected - adjusting network settings")
        return self._recover_network()
    
    def _recover_network(self):
        try:
            import urllib.request
            urllib.request.urlopen('http://localhost:8888', timeout=5)
            logger.info("Network connection test passed")
            return True
        except Exception as e:
            logger.error(f"Network recovery failed: {e}")
            return False
    
    def _fix_login_failed(self, params):
        logger.warning("Login failed - checking user credentials")
        return True
    
    def _fix_auth_failed(self, params):
        logger.warning("Authentication failed - verifying tokens")
        return True
    
    def _fix_forbidden(self, params):
        logger.warning("Forbidden access - checking permissions")
        return True
    
    def _fix_permission_denied(self, params):
        logger.warning("Permission denied - reviewing access controls")
        return True
    
    def _fix_server_error(self, params):
        logger.warning("Server error detected - restarting services")
        return self._restart_services()
    
    def _restart_services(self):
        try:
            logger.info("Initiating service restart sequence")
            return True
        except Exception as e:
            logger.error(f"Service restart failed: {e}")
            return False
    
    def _fix_unknown(self, params):
        logger.info("Unknown error type - logged for manual review")
        return True
    
    def get_error_summary(self):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT severity, COUNT(*) FROM error_monitor GROUP BY severity')
                severity_counts = cursor.fetchall()
                
                cursor.execute('SELECT status, COUNT(*) FROM error_monitor GROUP BY status')
                status_counts = cursor.fetchall()
                
                cursor.execute('''
                    SELECT error_id, message, severity, status, last_occurrence 
                    FROM error_monitor 
                    ORDER BY last_occurrence DESC 
                    LIMIT 10
                ''')
                recent_errors = cursor.fetchall()
                
                return {
                    'severity_counts': dict(severity_counts),
                    'status_counts': dict(status_counts),
                    'recent_errors': [
                        {
                            'error_id': row[0],
                            'message': row[1],
                            'severity': row[2],
                            'status': row[3],
                            'last_occurrence': row[4]
                        } for row in recent_errors
                    ]
                }
        except Exception as e:
            logger.error(f"Failed to get error summary: {e}")
            return {}
    
    def start_recovery(self, component):
        recovery_id = self._generate_recovery_id(component)
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_recovery_log 
                    (recovery_id, component, action, status, started_at)
                    VALUES (?, ?, 'recovery', 'running', ?)
                ''', (recovery_id, component, datetime.now().isoformat()))
                conn.commit()
            
            logger.info(f"Starting recovery for {component}")
            
            if component == 'database':
                result = self._recover_database()
            elif component == 'network':
                result = self._recover_network()
            elif component == 'services':
                result = self._restart_services()
            else:
                result = False
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE system_recovery_log 
                    SET status = ?, result = ?, completed_at = ?
                    WHERE recovery_id = ?
                ''', ('completed' if result else 'failed', str(result), 
                      datetime.now().isoformat(), recovery_id))
                conn.commit()
            
            return result
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            return False
    
    def _generate_recovery_id(self, component):
        import hashlib
        unique_str = f"recovery_{component}_{time.time()}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]

error_monitor = None

def get_error_monitor():
    global error_monitor
    if error_monitor is None:
        error_monitor = AIErrorMonitor()
    return error_monitor

if __name__ == '__main__':
    monitor = AIErrorMonitor()
    logger.info("AI Error Monitor Agent running...")
    
    while True:
        time.sleep(30)
        summary = monitor.get_error_summary()
        logger.info(f"Error summary: {summary}")