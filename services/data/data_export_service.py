#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS数据导出服务
支持多种格式的数据导出
"""

import os
import sys
import json
import csv
import sqlite3
import time
import threading
import zipfile
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class DataExportService:
    """数据导出服务"""
    
    def __init__(self):
        self.export_queue = []
        self.is_running = False
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._ensure_export_dir()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'export_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'export_dir': 'exports',
            'allowed_formats': ['json', 'csv', 'xlsx', 'xml', 'sql'],
            'max_file_size': 1073741824,
            'retention_days': 7,
            'compression_enabled': True
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'export_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _ensure_export_dir(self):
        """确保导出目录存在"""
        export_dir = self.config['export_dir']
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
            logger(f"[导出服务] 创建导出目录: {export_dir}")
    
    def _clean_old_exports(self):
        """清理过期导出文件"""
        export_dir = self.config['export_dir']
        retention_days = self.config['retention_days']
        now = time.time()
        
        for filename in os.listdir(export_dir):
            filepath = os.path.join(export_dir, filename)
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > retention_days * 24 * 60 * 60:
                    os.remove(filepath)
                    logger(f"[导出服务] 删除过期文件: {filename}")
    
    def export_to_json(self, data: Any, filename: str) -> str:
        """导出为JSON格式"""
        filepath = os.path.join(self.config['export_dir'], f"{filename}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def export_to_csv(self, data: List[Dict[str, Any]], filename: str) -> str:
        """导出为CSV格式"""
        filepath = os.path.join(self.config['export_dir'], f"{filename}.csv")
        
        if not data:
            return filepath
        
        keys = data[0].keys()
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        
        return filepath
    
    def export_to_xlsx(self, data: List[Dict[str, Any]], filename: str) -> str:
        """导出为XLSX格式"""
        try:
            import openpyxl
            from openpyxl import Workbook
            
            filepath = os.path.join(self.config['export_dir'], f"{filename}.xlsx")
            wb = Workbook()
            ws = wb.active
            
            if data:
                keys = list(data[0].keys())
                ws.append(keys)
                
                for row in data:
                    ws.append([row.get(key, '') for key in keys])
            
            wb.save(filepath)
            return filepath
        except ImportError:
            logger(f"[导出服务] 未安装openpyxl，改用CSV格式")
            return self.export_to_csv(data, filename)
    
    def export_to_xml(self, data: Any, filename: str) -> str:
        """导出为XML格式"""
        filepath = os.path.join(self.config['export_dir'], f"{filename}.xml")
        
        def dict_to_xml(d, indent=0):
            xml = ""
            for key, value in d.items():
                xml += "  " * indent + f"<{key}>"
                if isinstance(value, dict):
                    xml += "\n" + dict_to_xml(value, indent + 1) + "  " * indent
                elif isinstance(value, list):
                    xml += "\n"
                    for item in value:
                        xml += "  " * (indent + 1) + f"<item>"
                        if isinstance(item, dict):
                            xml += "\n" + dict_to_xml(item, indent + 2) + "  " * (indent + 1)
                        else:
                            xml += str(item)
                        xml += "</item>\n"
                    xml += "  " * indent
                else:
                    xml += str(value)
                xml += f"</{key}>\n"
            return xml
        
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<export>\n'
        xml_content += dict_to_xml({'data': data}, 1)
        xml_content += '</export>'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        return filepath
    
    def export_to_sql(self, data: List[Dict[str, Any]], table_name: str, filename: str) -> str:
        """导出为SQL格式"""
        filepath = os.path.join(self.config['export_dir'], f"{filename}.sql")
        
        sql_content = f"-- 导出时间: {datetime.now().isoformat()}\n"
        sql_content += f"-- 表名: {table_name}\n"
        sql_content += f"-- 记录数: {len(data)}\n\n"
        
        if data:
            columns = ', '.join(data[0].keys())
            sql_content += f"INSERT INTO {table_name} ({columns}) VALUES\n"
            
            for i, row in enumerate(data):
                values = []
                for key in row.keys():
                    value = row[key]
                    if value is None:
                        values.append('NULL')
                    elif isinstance(value, str):
                        escaped = value.replace('\\', '\\\\').replace("'", "''")
                        values.append(f"'{escaped}'")
                    else:
                        values.append(str(value))
                
                sql_content += f"  ({', '.join(values)})"
                sql_content += ',\n' if i < len(data) - 1 else ';\n'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(sql_content)
        
        return filepath
    
    def export_data(self, data: Any, filename: str, format_type: str = 'json', 
                   table_name: str = 'export') -> str:
        """导出数据"""
        if format_type not in self.config['allowed_formats']:
            format_type = 'json'
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"{filename}_{timestamp}"
        
        if format_type == 'json':
            filepath = self.export_to_json(data, base_filename)
        elif format_type == 'csv':
            filepath = self.export_to_csv(data, base_filename)
        elif format_type == 'xlsx':
            filepath = self.export_to_xlsx(data, base_filename)
        elif format_type == 'xml':
            filepath = self.export_to_xml(data, base_filename)
        elif format_type == 'sql':
            filepath = self.export_to_sql(data, table_name, base_filename)
        else:
            filepath = self.export_to_json(data, base_filename)
        
        if self.config['compression_enabled'] and os.path.exists(filepath):
            zip_filepath = filepath + '.zip'
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(filepath, os.path.basename(filepath))
            os.remove(filepath)
            filepath = zip_filepath
        
        self._clean_old_exports()
        
        logger(f"[导出服务] 导出完成: {filepath}")
        return filepath
    
    def export_database_table(self, table_name: str, format_type: str = 'json') -> str:
        """导出数据库表"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute(f'SELECT * FROM {table_name}')
            rows = cursor.fetchall()
            
            cursor.execute(f'PRAGMA table_info({table_name})')
            columns = [col[1] for col in cursor.fetchall()]
            
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            conn.close()
            
            return self.export_data(data, f"table_{table_name}", format_type, table_name)
        except Exception as e:
            logger(f"[导出服务] 导出数据库表失败: {e}")
            return None
    
    def export_system_rules(self, format_type: str = 'json') -> str:
        """导出系统规则"""
        return self.export_database_table('system_rules', format_type)
    
    def export_user_data(self, user_id: int = None, format_type: str = 'json') -> str:
        """导出用户数据"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            else:
                cursor.execute('SELECT * FROM users')
            
            rows = cursor.fetchall()
            
            cursor.execute('PRAGMA table_info(users)')
            columns = [col[1] for col in cursor.fetchall()]
            
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            conn.close()
            
            filename = f"user_{user_id}" if user_id else "users"
            return self.export_data(data, filename, format_type, 'users')
        except Exception as e:
            logger(f"[导出服务] 导出用户数据失败: {e}")
            return None
    
    def get_export_list(self) -> List[Dict[str, Any]]:
        """获取导出文件列表"""
        export_dir = self.config['export_dir']
        exports = []
        
        for filename in sorted(os.listdir(export_dir)):
            filepath = os.path.join(export_dir, filename)
            if os.path.isfile(filepath):
                exports.append({
                    'filename': filename,
                    'path': filepath,
                    'size': os.path.getsize(filepath),
                    'created_at': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                })
        
        return exports
    
    def delete_export(self, filename: str) -> bool:
        """删除导出文件"""
        export_dir = self.config['export_dir']
        filepath = os.path.join(export_dir, filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            logger(f"[导出服务] 删除导出文件: {filename}")
            return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'status': 'running' if self.is_running else 'stopped',
            'export_dir': self.config['export_dir'],
            'allowed_formats': self.config['allowed_formats'],
            'max_file_size': self.config['max_file_size'],
            'retention_days': self.config['retention_days'],
            'compression_enabled': self.config['compression_enabled'],
            'export_count': len(self.get_export_list())
        }

data_export_service = DataExportService()
