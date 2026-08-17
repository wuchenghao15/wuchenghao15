#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS报表生成服务
提供数据可视化和报表导出功能
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class Report:
    """报表"""
    
    def __init__(self, report_id: str, name: str, description: str = '',
                 data_source: str = '', query: str = '',
                 report_type: str = 'table', layout: Dict[str, Any] = None,
                 filters: Dict[str, Any] = None, created_at: str = None):
        self.report_id = report_id
        self.name = name
        self.description = description
        self.data_source = data_source
        self.query = query
        self.report_type = report_type
        self.layout = layout or {}
        self.filters = filters or {}
        self.created_at = created_at or datetime.now().isoformat()
        self.last_generated = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'report_id': self.report_id,
            'name': self.name,
            'description': self.description,
            'data_source': self.data_source,
            'query': self.query,
            'report_type': self.report_type,
            'layout': self.layout,
            'filters': self.filters,
            'created_at': self.created_at,
            'last_generated': self.last_generated
        }

class ReportGenerator:
    """报表生成器"""
    
    def __init__(self):
        self.reports: Dict[str, Report] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'report_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'output_dir': 'reports',
            'default_format': 'html',
            'supported_formats': ['html', 'pdf', 'csv', 'xlsx', 'json'],
            'auto_generate_interval': 3600
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'report_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    data_source TEXT,
                    query TEXT,
                    report_type TEXT DEFAULT 'table',
                    layout TEXT,
                    filters TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS report_generations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    output_format TEXT,
                    file_path TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    duration REAL,
                    record_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_reports_id ON reports(report_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_report_gens_report ON report_generations(report_id)
            ''')
            
            conn.commit()
            conn.close()
            
            os.makedirs(self.config['output_dir'], exist_ok=True)
        except Exception as e:
            logger(f"[报表] 初始化数据库失败: {e}")
    
    def _generate_report_id(self) -> str:
        """生成报表ID"""
        return f"report_{int(time.time())}_{hash(os.urandom(16))}"
    
    def create_report(self, name: str, data_source: str = '', query: str = '',
                     report_type: str = 'table', description: str = '',
                     layout: Dict[str, Any] = None, filters: Dict[str, Any] = None) -> str:
        """创建报表"""
        report_id = self._generate_report_id()
        
        report = Report(
            report_id=report_id,
            name=name,
            description=description,
            data_source=data_source,
            query=query,
            report_type=report_type,
            layout=layout or {},
            filters=filters or {}
        )
        
        with self.lock:
            self.reports[report_id] = report
        
        self._save_report_to_db(report)
        logger(f"[报表] 创建报表: {name}")
        
        return report_id
    
    def _save_report_to_db(self, report: Report):
        """保存报表到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO reports 
                (report_id, name, description, data_source, query, report_type, layout, filters)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report.report_id, report.name, report.description,
                report.data_source, report.query, report.report_type,
                json.dumps(report.layout),
                json.dumps(report.filters)
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[报表] 保存报表失败: {e}")
    
    def update_report(self, report_id: str, **kwargs) -> bool:
        """更新报表"""
        with self.lock:
            if report_id not in self.reports:
                logger(f"[报表] 报表不存在: {report_id}")
                return False
            
            report = self.reports[report_id]
            
            if 'name' in kwargs:
                report.name = kwargs['name']
            if 'description' in kwargs:
                report.description = kwargs['description']
            if 'data_source' in kwargs:
                report.data_source = kwargs['data_source']
            if 'query' in kwargs:
                report.query = kwargs['query']
            if 'report_type' in kwargs:
                report.report_type = kwargs['report_type']
            if 'layout' in kwargs:
                report.layout = kwargs['layout']
            if 'filters' in kwargs:
                report.filters = kwargs['filters']
        
        self._update_report_in_db(report_id, kwargs)
        logger(f"[报表] 更新报表: {report_id}")
        
        return True
    
    def _update_report_in_db(self, report_id: str, updates: Dict[str, Any]):
        """更新数据库中的报表"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            set_clause = []
            params = []
            
            for key, value in updates.items():
                if key in ['layout', 'filters']:
                    set_clause.append(f"{key} = ?")
                    params.append(json.dumps(value))
                else:
                    set_clause.append(f"{key} = ?")
                    params.append(value)
            
            params.append(report_id)
            
            cursor.execute(f'UPDATE reports SET {", ".join(set_clause)} WHERE report_id = ?', params)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[报表] 更新报表失败: {e}")
    
    def delete_report(self, report_id: str) -> bool:
        """删除报表"""
        with self.lock:
            if report_id not in self.reports:
                logger(f"[报表] 报表不存在: {report_id}")
                return False
            
            del self.reports[report_id]
        
        self._delete_report_from_db(report_id)
        logger(f"[报表] 删除报表: {report_id}")
        
        return True
    
    def _delete_report_from_db(self, report_id: str):
        """从数据库删除报表"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM reports WHERE report_id = ?', (report_id,))
            cursor.execute('DELETE FROM report_generations WHERE report_id = ?', (report_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[报表] 删除报表失败: {e}")
    
    def generate_report(self, report_id: str, output_format: str = None) -> Optional[str]:
        """生成报表"""
        output_format = output_format or self.config['default_format']
        
        if output_format not in self.config['supported_formats']:
            logger(f"[报表] 不支持的格式: {output_format}")
            return None
        
        with self.lock:
            if report_id not in self.reports:
                logger(f"[报表] 报表不存在: {report_id}")
                return None
            
            report = self.reports[report_id]
        
        started_at = datetime.now()
        generation_id = None
        
        try:
            generation_id = self._start_generation(report_id, output_format, started_at)
            
            data = self._fetch_data(report)
            
            if not data:
                data = []
            
            output_path = self._render_report(report, data, output_format)
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            with self.lock:
                report.last_generated = completed_at.isoformat()
            
            self._end_generation(generation_id, 'success', completed_at, duration, len(data), output_path)
            logger(f"[报表] 报表生成成功: {report.name}")
            
            return output_path
        except Exception as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            if generation_id:
                self._end_generation(generation_id, 'failed', completed_at, duration, error_message=str(e))
            
            logger(f"[报表] 报表生成失败: {report.name} - {e}")
            return None
    
    def _fetch_data(self, report: Report) -> List[Dict[str, Any]]:
        """获取数据"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            if report.query:
                cursor.execute(report.query)
            elif report.data_source:
                cursor.execute(f'SELECT * FROM {report.data_source}')
            else:
                cursor.execute('SELECT * FROM system_rules LIMIT 100')
            
            columns = [desc[0] for desc in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return data
        except Exception as e:
            logger(f"[报表] 获取数据失败: {e}")
            return []
    
    def _render_report(self, report: Report, data: List[Dict[str, Any]], 
                      output_format: str) -> str:
        """渲染报表"""
        filename = f"{report.report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{output_format}"
        output_path = os.path.join(self.config['output_dir'], filename)
        
        if output_format == 'json':
            self._render_json(data, output_path)
        elif output_format == 'csv':
            self._render_csv(data, output_path)
        elif output_format == 'html':
            self._render_html(report, data, output_path)
        else:
            self._render_json(data, output_path)
        
        return output_path
    
    def _render_json(self, data: List[Dict[str, Any]], output_path: str):
        """渲染JSON格式"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _render_csv(self, data: List[Dict[str, Any]], output_path: str):
        """渲染CSV格式"""
        if not data:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('')
            return
        
        headers = list(data[0].keys())
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(','.join(headers) + '\n')
            
            for row in data:
                row_data = []
                for header in headers:
                    value = row.get(header, '')
                    if isinstance(value, str) and ',' in value:
                        row_data.append(f'"{value}"')
                    else:
                        row_data.append(str(value))
                f.write(','.join(row_data) + '\n')
    
    def _render_html(self, report: Report, data: List[Dict[str, Any]], output_path: str):
        """渲染HTML格式"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
        sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; margin-top: 0; }}
        .description {{ color: #666; margin-bottom: 20px; }}
        .meta {{ font-size: 12px; color: #999; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #333; }}
        tr:hover {{ background: #f8f9fa; }}
        .summary {{ margin-bottom: 20px; padding: 15px; background: #e8f5e9; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{report.name}</h1>
        <div class="description">{report.description}</div>
        <div class="meta">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 数据行数: {len(data)}</div>
        <div class="summary">共 {len(data)} 条记录</div>
        <table>
            <thead>
                <tr>
                    {''.join('<th>' + h + '</th>' for h in (data[0].keys() if data else []))}
                </tr>
            </thead>
            <tbody>
                {''.join('<tr>' + ''.join('<td>' + str(v) + '</td>' for v in row.values()) + '</tr>' for row in data)}
            </tbody>
        </table>
    </div>
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def _start_generation(self, report_id: str, output_format: str, started_at: datetime) -> int:
        """开始生成记录"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO report_generations (report_id, status, output_format, started_at)
                VALUES (?, ?, ?, ?)
            ''', (report_id, 'running', output_format, started_at.isoformat()))
            
            generation_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return generation_id
        except Exception as e:
            logger(f"[报表] 开始生成记录失败: {e}")
            return 0
    
    def _end_generation(self, generation_id: int, status: str, completed_at: datetime,
                       duration: float, record_count: int = 0, file_path: str = None,
                       error_message: str = None):
        """结束生成记录"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE report_generations 
                SET status = ?, completed_at = ?, duration = ?, record_count = ?, file_path = ?, error_message = ?
                WHERE id = ?
            ''', (status, completed_at.isoformat(), duration, record_count, file_path, error_message, generation_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[报表] 结束生成记录失败: {e}")
    
    def get_report(self, report_id: str) -> Optional[Report]:
        """获取报表"""
        return self.reports.get(report_id)
    
    def get_reports(self) -> List[Report]:
        """获取报表列表"""
        with self.lock:
            return list(self.reports.values())
    
    def get_generation_history(self, report_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取生成历史"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM report_generations WHERE 1=1'
            params = []
            
            if report_id:
                query += ' AND report_id = ?'
                params.append(report_id)
            
            query += ' ORDER BY started_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            history = []
            
            for row in cursor.fetchall():
                history.append(dict(zip(columns, row)))
            
            conn.close()
            return history
        except Exception as e:
            logger(f"[报表] 获取生成历史失败: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_reports': len(self.reports),
                'output_dir': self.config['output_dir'],
                'supported_formats': self.config['supported_formats'],
                'default_format': self.config['default_format'],
                'auto_generate_interval': self.config['auto_generate_interval']
            }
    
    def start(self):
        """启动报表服务"""
        if self.is_running:
            return
        
        self.is_running = True
        logger(f"[报表] 报表生成服务已启动")
    
    def stop(self):
        """停止报表服务"""
        self.is_running = False
        logger(f"[报表] 报表生成服务已停止")

report_generator = ReportGenerator()
