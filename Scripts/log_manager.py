#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MTSCOS 日志管理服务
用于处理和存储动作拐点日志数据
"""

import os
import json
import time
import datetime
import threading
import argparse
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler

class LogManager:
    """日志管理器"""
    
    def __init__(self, log_dir="/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/Logs/actions"):
        self.log_dir = log_dir
        self.log_file_prefix = "action_log"
        self.max_log_size = 5 * 1024 * 1024  # 5MB
        self.lock = threading.Lock()
        
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)
    
    def get_log_file_path(self):
        """获取当前日志文件路径"""
        today = datetime.datetime.now().strftime("%Y%m%d")
        return os.path.join(self.log_dir, f"{self.log_file_prefix}_{today}.json")
    
    def should_rotate_log(self, file_path):
        """检查是否需要轮转日志"""
        if not os.path.exists(file_path):
            return False
        
        return os.path.getsize(file_path) >= self.max_log_size
    
    def rotate_log(self, file_path):
        """轮转日志文件"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.{timestamp}.bak"
        
        # 重命名当前日志文件
        try:
            os.rename(file_path, backup_path)
            print(f"[LOG MANAGER] 日志已轮转: {file_path} -> {backup_path}")
        except Exception as e:
            print(f"[LOG MANAGER] 日志轮转失败: {e}")
    
    def save_log(self, log_entry):
        """保存单条日志"""
        with self.lock:
            log_file_path = self.get_log_file_path()
            
            # 检查是否需要轮转日志
            if self.should_rotate_log(log_file_path):
                self.rotate_log(log_file_path)
            
            # 确保时间戳存在
            if 'timestamp' not in log_entry:
                log_entry['timestamp'] = datetime.datetime.now().isoformat()
            
            # 添加处理时间戳
            log_entry['processed_at'] = datetime.datetime.now().isoformat()
            
            # 保存日志到文件
            try:
                with open(log_file_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                return True
            except Exception as e:
                print(f"[LOG MANAGER] 保存日志失败: {e}")
                return False
    
    def save_batch_logs(self, log_entries):
        """批量保存日志"""
        success_count = 0
        for log_entry in log_entries:
            if self.save_log(log_entry):
                success_count += 1
        
        print(f"[LOG MANAGER] 批量保存日志完成: {success_count}/{len(log_entries)} 条成功")
        return success_count
    
    def get_logs(self, start_time=None, end_time=None, action_type=None, limit=1000):
        """获取日志"""
        logs = []
        
        # 获取所有日志文件
        log_files = sorted([f for f in os.listdir(self.log_dir) 
                           if f.startswith(self.log_file_prefix) and f.endswith('.json')], 
                          reverse=True)
        
        for log_file in log_files:
            file_path = os.path.join(self.log_dir, log_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            log = json.loads(line.strip())
                            
                            # 过滤条件
                            if start_time and log.get('timestamp', '') < start_time:
                                continue
                            if end_time and log.get('timestamp', '') > end_time:
                                continue
                            if action_type and log.get('actionType', '') != action_type:
                                continue
                            
                            logs.append(log)
                            
                            # 限制数量
                            if len(logs) >= limit:
                                return logs
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"[LOG MANAGER] 读取日志文件失败 {file_path}: {e}")
        
        return logs
    
    def get_log_summary(self):
        """获取日志统计信息"""
        summary = {
            'total_logs': 0,
            'log_files': [],
            'action_types': {},
            'first_log_time': None,
            'last_log_time': None
        }
        
        # 获取所有日志文件
        log_files = sorted([f for f in os.listdir(self.log_dir) 
                           if f.startswith(self.log_file_prefix) and f.endswith('.json')])
        
        summary['log_files'] = log_files
        
        for log_file in log_files:
            file_path = os.path.join(self.log_dir, log_file)
            file_size = os.path.getsize(file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            log = json.loads(line.strip())
                            summary['total_logs'] += 1
                            
                            # 统计动作类型
                            action_type = log.get('actionType', 'unknown')
                            summary['action_types'][action_type] = summary['action_types'].get(action_type, 0) + 1
                            
                            # 更新时间范围
                            log_time = log.get('timestamp', '')
                            if log_time:
                                if not summary['first_log_time'] or log_time < summary['first_log_time']:
                                    summary['first_log_time'] = log_time
                                if not summary['last_log_time'] or log_time > summary['last_log_time']:
                                    summary['last_log_time'] = log_time
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"[LOG MANAGER] 读取日志文件失败 {file_path}: {e}")
        
        return summary

class LogHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    log_manager = None
    
    @classmethod
    def initialize(cls, log_manager):
        cls.log_manager = log_manager
    
    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers(204)
    
    def do_POST(self):
        if not self.log_manager:
            self._set_headers(500)
            self.wfile.write(json.dumps({'error': 'Log manager not initialized'}).encode())
            return
        
        try:
            # 读取请求体
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # 处理日志数据
            if isinstance(data, list):
                # 批量日志
                success_count = self.log_manager.save_batch_logs(data)
                response = {
                    'status': 'success',
                    'message': f'Batch logs saved: {success_count}/{len(data)}',
                    'timestamp': datetime.datetime.now().isoformat()
                }
            else:
                # 单条日志
                success = self.log_manager.save_log(data)
                response = {
                    'status': 'success' if success else 'error',
                    'message': 'Log saved' if success else 'Failed to save log',
                    'timestamp': datetime.datetime.now().isoformat()
                }
            
            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"[LOG HANDLER] Error processing POST request: {e}")
            print(traceback.format_exc())
            self._set_headers(500)
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def do_GET(self):
        if not self.log_manager:
            self._set_headers(500)
            self.wfile.write(json.dumps({'error': 'Log manager not initialized'}).encode())
            return
        
        try:
            # 解析查询参数
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # 处理不同的端点
            if parsed_url.path == '/logs':
                # 获取日志列表
                start_time = query_params.get('start_time', [None])[0]
                end_time = query_params.get('end_time', [None])[0]
                action_type = query_params.get('action_type', [None])[0]
                limit = int(query_params.get('limit', [100])[0])
                
                logs = self.log_manager.get_logs(start_time, end_time, action_type, limit)
                
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    'status': 'success',
                    'data': logs,
                    'count': len(logs),
                    'timestamp': datetime.datetime.now().isoformat()
                }).encode())
                
            elif parsed_url.path == '/summary':
                # 获取日志统计信息
                summary = self.log_manager.get_log_summary()
                
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    'status': 'success',
                    'data': summary,
                    'timestamp': datetime.datetime.now().isoformat()
                }).encode())
                
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'Not found'}).encode())
                
        except Exception as e:
            print(f"[LOG HANDLER] Error processing GET request: {e}")
            print(traceback.format_exc())
            self._set_headers(500)
            self.wfile.write(json.dumps({'error': str(e)}).encode())

class LogServer:
    """日志服务器"""
    
    def __init__(self, host='localhost', port=8082):
        self.host = host
        self.port = port
        self.log_manager = LogManager()
        self.server = None
    
    def start(self):
        """启动服务器"""
        LogHandler.initialize(self.log_manager)
        
        self.server = HTTPServer((self.host, self.port), LogHandler)
        print(f"[LOG SERVER] 启动日志服务器: http://{self.host}:{self.port}")
        print(f"[LOG SERVER] 日志存储目录: {self.log_manager.log_dir}")
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\n[LOG SERVER] 正在关闭服务器...")
        finally:
            if self.server:
                self.server.server_close()
                print("[LOG SERVER] 服务器已关闭")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MTSCOS 日志管理服务')
    parser.add_argument('--host', type=str, default='localhost', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=8082, help='服务器端口')
    args = parser.parse_args()
    
    server = LogServer(args.host, args.port)
    server.start()

if __name__ == '__main__':
    main()
