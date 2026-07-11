#!/usr/bin/env python3
"""
AI日志分析系统 - 自动识别和分类系统日志
"""

import logging
logger = logging.getLogger(__name__)
import re
import os
from datetime import datetime
import sqlite3
from collections import defaultdict, Counter


class AILogAnalyzer:
    """AI日志分析器,实现日志的自动识别、分类和异常检测"""

    def __init__(self, db_path='ai_logs.db'):
        """初始化AI日志分析器

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self._init_db()

        self.log_level_patterns = {
            'DEBUG': re.compile(r'\bDEBUG\b', re.IGNORECASE),
            'INFO': re.compile(r'\bINFO\b', re.IGNORECASE),
            'WARN': re.compile(r'\bWARN(?:ING)?\b', re.IGNORECASE),
            'ERROR': re.compile(r'\bERROR\b', re.IGNORECASE),
            'CRITICAL': re.compile(r'\bCRITICAL|FATAL\b', re.IGNORECASE),
            'EXCEPTION': re.compile(r'\bEXCEPTION\b|Traceback', re.IGNORECASE)
        }

        self.anomaly_patterns = {
            'database_error': re.compile(r'\bdatabase|sql|sqlite|mysql|postgres\b.*\berror|failed', re.IGNORECASE),
            'network_error': re.compile(r'\bnetwork|connection|timeout|http|socket\b.*\berror|failed', re.IGNORECASE),
            'permission_error': re.compile(r'\bpermission|denied|access\b.*\berror', re.IGNORECASE),
            'file_error': re.compile(r'\bfile|directory|path\b.*\bnot found|error|failed', re.IGNORECASE),
            'memory_error': re.compile(r'\bmemory|out of memory|oom\b', re.IGNORECASE),
            'cpu_error': re.compile(r'\bcpu|processor\b.*\boverload|error', re.IGNORECASE),
            'disk_error': re.compile(r'\bdisk|storage|space\b.*\berror|full', re.IGNORECASE),
            'authentication_error': re.compile(r'\bauth|login|password|token\b.*\berror|failed', re.IGNORECASE),
            'validation_error': re.compile(r'\bvalidation|invalid|format\b.*\berror', re.IGNORECASE),
            'system_error': re.compile(r'\bsystem|kernel|os\b.*\berror|panic', re.IGNORECASE)
        }

        self.recent_errors = defaultdict(list)
        self.error_window = 60

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP NOT NULL,
            level TEXT NOT NULL,
            source TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT,
            is_anomalous INTEGER DEFAULT 0,
            anomaly_type TEXT,
            anomaly_score REAL DEFAULT 0.0,
            metadata TEXT
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT UNIQUE,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            total_entries INTEGER NOT NULL,
            entries_by_level TEXT NOT NULL,
            anomalies_count INTEGER NOT NULL,
            anomalies_by_type TEXT NOT NULL,
            top_errors TEXT NOT NULL,
            summary TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_timestamp ON log_entries(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_anomalous ON log_entries(is_anomalous)')

            conn.commit()

    def _detect_log_level(self, log_line):
        """检测日志级别

        Args:
            log_line: 日志行

        Returns:
            str: 日志级别
        """
        for level, pattern in self.log_level_patterns.items():
            if pattern.search(log_line):
                return level
        return 'INFO'

    def _detect_anomaly(self, log_line, level):
        """检测异常

        Args:
            log_line: 日志行
            level: 日志级别

        Returns:
            tuple: (是否异常, 异常类型, 异常分数)
        """
        if level in ['ERROR', 'CRITICAL', 'EXCEPTION']:
            for anomaly_type, pattern in self.anomaly_patterns.items():
                if pattern.search(log_line):
                    return True, anomaly_type, 0.9
            return True, 'general_error', 0.8

        if level == 'WARN':
            return True, 'warning', 0.6

        return False, None, 0.0

    def _detect_repeated_errors(self, log_line, timestamp):
        """检测重复错误

        Args:
            log_line: 日志行
            timestamp: 日志时间戳

        Returns:
            tuple: (是否重复, 重复次数, 重复时间窗口)
        """
        error_key = log_line[:100]
        current_time = timestamp.timestamp()

        self.recent_errors[error_key] = [
            t for t in self.recent_errors[error_key]
            if current_time - t < self.error_window
        ]

        self.recent_errors[error_key].append(current_time)

        repeat_count = len(self.recent_errors[error_key])
        return repeat_count > 1, repeat_count, self.error_window

    def _detect_category(self, log_line):
        """检测日志分类

        Args:
            log_line: 日志行

        Returns:
            str: 日志分类
        """
        categories = {
            'database': re.compile(r'\bdb|database|sql|query|table|record\b', re.IGNORECASE),
            'network': re.compile(r'\bhttp|https|request|response|api|endpoint|socket\b', re.IGNORECASE),
            'file': re.compile(r'\bfile|upload|download|path|directory\b', re.IGNORECASE),
            'system': re.compile(r'\bsystem|os|kernel|cpu|memory|disk\b', re.IGNORECASE),
            'application': re.compile(r'\bapp|service|module|function\b', re.IGNORECASE),
            'security': re.compile(r'\bsecurity|firewall|blacklist|whitelist|anomaly\b', re.IGNORECASE),
            'performance': re.compile(r'\bperformance|latency|response time|throughput\b', re.IGNORECASE),
            'configuration': re.compile(r'\bconfig|setting|parameter|environment\b', re.IGNORECASE),
            'logging': re.compile(r'\blog|logger|logging\b', re.IGNORECASE)
        }

        for category, pattern in categories.items():
            if pattern.search(log_line):
                return category

        return 'general'

    def parse_log_line(self, log_line, source='unknown'):
        """解析单条日志

        Args:
            log_line: 日志行
            source: 日志来源

        Returns:
            dict: 解析结果
        """
        timestamp_patterns = [
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)',
            r'(\d{2}/\w+/\d{4}:\d{2}:\d{2}:\d{2} \S+)',
            r'(\w+ \d{2} \d{2}:\d{2}:\d{2})',
        ]

        timestamp = datetime.now()
        for pattern in timestamp_patterns:
            match = re.search(pattern, log_line)
            if match:
                try:
                    timestamp_str = match.group(1)
                    for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S',
                               '%d/%b/%Y:%H:%M:%S %z', '%b %d %H:%M:%S']:
                        try:
                            timestamp = datetime.strptime(timestamp_str, fmt)
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass
                break

        level = self._detect_log_level(log_line)
        is_anomalous, anomaly_type, anomaly_score = self._detect_anomaly(log_line, level)
        is_repeated, repeat_count, repeat_window = self._detect_repeated_errors(log_line, timestamp)
        category = self._detect_category(log_line)

        if is_repeated:
            is_anomalous = True
            anomaly_score = min(0.95, anomaly_score + 0.1)

        return {
            'timestamp': timestamp,
            'level': level,
            'source': source,
            'content': log_line.strip(),
            'category': category,
            'is_anomalous': is_anomalous,
            'anomaly_type': anomaly_type,
            'anomaly_score': anomaly_score,
            'is_repeated': is_repeated,
            'repeat_count': repeat_count,
            'metadata': {
                'raw_line': log_line,
                'detected_at': datetime.now().isoformat()
            }
        }

    def analyze_log_file(self, file_path):
        """分析日志文件

        Args:
            file_path: 日志文件路径

        Returns:
            dict: 分析结果
        """
        if not os.path.exists(file_path):
            return {
                'success': False,
                'message': f'日志文件不存在: {file_path}',
                'details': {
                    'file_path': file_path
                }
            }

        entries = []
        source = os.path.basename(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.strip():
                        entry = self.parse_log_line(line, source)
                        entries.append(entry)
                        self.save_log_entry(entry)
        except Exception as e:
            return {
                'success': False,
                'message': f'分析日志文件失败: {str(e)}',
                'details': {
                    'file_path': file_path,
                    'error': str(e)
                }
            }

        return {
            'success': True,
            'message': f'成功分析 {len(entries)} 条日志',
            'details': {
                'file_path': file_path,
                'total_entries': len(entries),
                'source': source
            }
        }

    def save_log_entry(self, entry):
        """保存日志条目

        Args:
            entry: 日志条目

        Returns:
            bool: 是否保存成功
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                INSERT INTO log_entries
                (timestamp, level, source, content, category, is_anomalous, anomaly_type, anomaly_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry['timestamp'].isoformat(),
                    entry['level'],
                    entry['source'],
                    entry['content'],
                    entry['category'],
                    1 if entry['is_anomalous'] else 0,
                    entry['anomaly_type'],
                    entry['anomaly_score'],
                    str(entry['metadata'])
                ))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error saving log entry: {str(e)}")
                return False

    def generate_report(self, start_time=None, end_time=None, source=None):
        """生成日志分析报告

        Args:
            start_time: 开始时间
            end_time: 结束时间
            source: 日志来源

        Returns:
            dict: 分析报告
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                query = "SELECT * FROM log_entries WHERE 1=1"
                params = []

                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time.isoformat())

                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time.isoformat())

                if source:
                    query += " AND source = ?"
                    params.append(source)

                cursor.execute(query, params)
                entries = []
                for row in cursor.fetchall():
                    entries.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'level': row[2],
                        'source': row[3],
                        'content': row[4],
                        'category': row[5],
                        'is_anomalous': row[6],
                        'anomaly_type': row[7],
                        'anomaly_score': row[8],
                        'metadata': eval(row[9]) if row[9] else {}
                    })

                report = self._generate_report_from_entries(entries, start_time, end_time, source)
                self._save_report(report)

                return report
            except Exception as e:
                logger.error(f"Error generating report: {str(e)}")
                return {
                    'success': False,
                    'message': f'生成报告失败: {str(e)}',
                    'details': {}
                }

    def _generate_report_from_entries(self, entries, start_time, end_time, source):
        """从日志条目生成报告

        Args:
            entries: 日志条目列表
            start_time: 开始时间
            end_time: 结束时间
            source: 日志来源

        Returns:
            dict: 分析报告
        """
        if not entries:
            return {
                'success': True,
                'start_time': start_time.isoformat() if start_time else None,
                'end_time': end_time.isoformat() if end_time else None,
                'source': source,
                'total_entries': 0,
                'anomalies_count': 0,
                'anomalies_by_type': {},
                'top_errors': [],
                'categories_count': {},
                'summary': '没有找到日志条目',
                'created_at': datetime.now().isoformat()
            }

        level_counter = Counter(entry['level'] for entry in entries)
        anomalies = [entry for entry in entries if entry['is_anomalous']]
        anomaly_counter = Counter(entry['anomaly_type'] for entry in anomalies if entry['anomaly_type'])
        category_counter = Counter(entry['category'] for entry in entries)

        error_entries = [entry for entry in entries if entry['level'] in ['ERROR', 'CRITICAL', 'EXCEPTION']]
        error_counter = Counter(entry['content'][:200] for entry in error_entries)
        top_errors = [{'error': error, 'count': count} for error, count in error_counter.most_common(10)]

        summary = self._generate_summary(entries, anomalies, level_counter)

        return {
            'success': True,
            'message': f'成功生成报告,包含 {len(entries)} 条日志',
            'report_id': f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'start_time': start_time.isoformat() if start_time else entries[0]['timestamp'],
            'end_time': end_time.isoformat() if end_time else entries[-1]['timestamp'],
            'source': source,
            'total_entries': len(entries),
            'entries_by_level': dict(level_counter),
            'anomalies_count': len(anomalies),
            'anomalies_by_type': dict(anomaly_counter),
            'top_errors': top_errors,
            'categories_count': dict(category_counter),
            'summary': summary,
            'created_at': datetime.now().isoformat()
        }

    def _generate_summary(self, entries, anomalies, level_counter):
        """生成报告摘要

        Args:
            entries: 日志条目列表
            anomalies: 异常列表
            level_counter: 日志级别计数器

        Returns:
            str: 报告摘要
        """
        summary = "日志分析报告摘要:\n"
        summary += f"- 总日志条目数: {len(entries)}\n"
        summary += f"- 异常事件数: {len(anomalies)}\n"

        total_errors = level_counter.get('ERROR', 0) + level_counter.get('CRITICAL', 0) + level_counter.get('EXCEPTION', 0)
        summary += f"- 严重错误数: {total_errors}\n"

        if total_errors > 0:
            summary += f"- 发现 {total_errors} 个严重错误,建议优先处理\n"

        if len(anomalies) > 0:
            summary += f"- 检测到 {len(anomalies)} 个异常事件,建议进一步分析\n"

        if len(entries) > 1000:
            summary += f"- 日志量较大,建议优化日志记录策略\n"

        return summary

    def _save_report(self, report):
        """保存报告到数据库

        Args:
            report: 报告数据

        Returns:
            bool: 是否保存成功
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                INSERT OR REPLACE INTO log_reports
                (report_id, start_time, end_time, total_entries, entries_by_level,
                anomalies_count, anomalies_by_type, top_errors, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report.get('report_id', ''),
                    report['start_time'],
                    report['end_time'],
                    report['total_entries'],
                    str(report['entries_by_level']),
                    report['anomalies_count'],
                    str(report['anomalies_by_type']),
                    str(report['top_errors']),
                    report['summary']
                ))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error saving report: {str(e)}")
                conn.rollback()
                return False

    def get_recent_anomalies(self, limit=50):
        """获取最近的异常

        Args:
            limit: 返回数量限制

        Returns:
            list: 最近的异常列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                SELECT * FROM log_entries
                WHERE is_anomalous = 1
                ORDER BY timestamp DESC
                LIMIT ?
                ''', (limit,))

                anomalies = []
                for row in cursor.fetchall():
                    anomalies.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'level': row[2],
                        'source': row[3],
                        'content': row[4],
                        'category': row[5],
                        'is_anomalous': row[6],
                        'anomaly_type': row[7],
                        'anomaly_score': row[8],
                        'metadata': eval(row[9]) if row[9] else {}
                    })

                return anomalies
            except Exception as e:
                logger.error(f"Error getting recent anomalies: {str(e)}")
                return []

    def get_total_logs(self):
        """获取日志总数

        Returns:
            int: 日志总数
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT COUNT(*) FROM log_entries')
                result = cursor.fetchone()
                return result[0] if result else 0
            except Exception as e:
                logger.error(f"Error getting total logs: {str(e)}")
                return 0

    def analyze_directory(self, directory_path, pattern='*.log'):
        """分析日志目录

        Args:
            directory_path: 日志目录路径
            pattern: 日志文件匹配模式

        Returns:
            dict: 分析结果
        """
        import glob

        if not os.path.exists(directory_path):
            return {
                'success': False,
                'message': f'日志目录不存在: {directory_path}',
                'details': {
                    'directory_path': directory_path
                }
            }

        log_files = glob.glob(os.path.join(directory_path, pattern))

        if not log_files:
            return {
                'success': False,
                'message': '未找到匹配的日志文件',
                'details': {
                    'pattern': pattern
                }
            }

        results = []
        total_entries = 0
        for log_file in log_files:
            result = self.analyze_log_file(log_file)
            results.append({
                'file_path': log_file,
                'result': result
            })
            if result['success'] and 'total_entries' in result.get('details', {}):
                total_entries += result['details']['total_entries']

        return {
            'success': True,
            'message': f'成功分析 {len(log_files)} 个日志文件',
            'details': {
                'directory_path': directory_path,
                'pattern': pattern,
                'log_files': log_files,
                'total_files': len(log_files),
                'total_entries': total_entries,
                'results': results
            }
        }


global_log_analyzer = None


def get_log_analyzer():
    """获取全局日志分析器实例

    Returns:
        AILogAnalyzer: 日志分析器实例
    """
    global global_log_analyzer
    if global_log_analyzer is None:
        global_log_analyzer = AILogAnalyzer()
    return global_log_analyzer


if __name__ == '__main__':
    log_analyzer = AILogAnalyzer()

    test_logs = [
        '2023-10-01 12:00:00 INFO [app] Application started successfully',
        '2023-10-01 12:00:10 ERROR [auth] Failed login attempt from 192.168.1.1',
        '2023-10-01 12:00:20 CRITICAL [system] Out of memory error',
        '2023-10-01 12:00:45 ERROR [auth] Invalid token for user: admin'
    ]

    entries = []
    for log_line in test_logs:
        parsed = log_analyzer.parse_log_line(log_line, 'test')
        entries.append(parsed)
        print(f"\n原始日志: {log_line}")
        print(f"解析结果: 级别={parsed['level']}, 异常={parsed['is_anomalous']}, 异常类型={parsed['anomaly_type']}, 重复={parsed['is_repeated']}, 分类={parsed['category']}")

    print("\n\n测试生成报告:")
    report = log_analyzer._generate_report_from_entries(entries, None, None, 'test')
    print(str(report))
