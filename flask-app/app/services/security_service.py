#!/usr/bin/env python3
"""
安全服务模块
负责项目的数字安全、数据库安全、本地缓存数据安全和项目后门漏洞安全
"""

import os
import sys
import sqlite3
import json
import time
import hashlib
import hmac
import base64
import re
import socket
import threading
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SecurityService:
    """安全服务类"""
    
    def __init__(self, db_path="app.db"):
        """初始化安全服务"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.encryption_key = None
        self.scanning_interval = 300  # 5分钟
        self.is_running = False
        self.scan_thread = None
        
        # DDoS防御配置
        self.ddos_protection = {
            "enabled": True,
            "rate_limit": 100,  # 请求/分钟/IP
            "block_duration": 300,  # 秒
            "request_history": {},  # IP -> [timestamp1, timestamp2, ...]
            "blocked_ips": {},  # IP -> block_until_timestamp
        }
        
        # 内存监控配置
        self.memory_monitoring = {
            "enabled": True,
            "threshold": 80,  # 内存使用率阈值(%)
            "check_interval": 60,  # 秒
            "last_check": 0
        }
        
        # 加载安全配置
        self.load_config()
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"连接数据库失败: {str(e)}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def load_config(self):
        """加载安全配置"""
        if not self.connect():
            return
        
        try:
            # 获取加密密钥
            self.cursor.execute("SELECT config_value FROM security_configs WHERE config_key = 'encryption_key'")
            result = self.cursor.fetchone()
            if result:
                self.encryption_key = result[0].encode()
            
            # 获取扫描间隔
            self.cursor.execute("SELECT config_value FROM security_configs WHERE config_key = 'scan_interval'")
            result = self.cursor.fetchone()
            if result:
                self.scanning_interval = int(result[0])
                
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
        finally:
            self.close()
    
    def add_security_event(self, event_type, severity, message, source=None, ip_address=None, user_agent=None, details=None):
        """添加安全事件"""
        if not self.connect():
            return False
        
        try:
            sql = """
            INSERT INTO security_events (event_type, severity, message, source, ip_address, user_agent, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(sql, (event_type, severity, message, source, ip_address, user_agent, json.dumps(details) if details else None))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"添加安全事件失败: {str(e)}")
            return False
        finally:
            self.close()
    
    def start_scan(self, scan_type, target):
        """开始安全扫描"""
        if not self.connect():
            return None
        
        try:
            # 添加扫描记录
            sql = """
            INSERT INTO security_scans (scan_type, target, status)
            VALUES (?, ?, ?)
            """
            self.cursor.execute(sql, (scan_type, target, 'running'))
            scan_id = self.cursor.lastrowid
            self.conn.commit()
            
            # 执行扫描
            threading.Thread(target=self._perform_scan, args=(scan_id, scan_type, target)).start()
            return scan_id
        except Exception as e:
            print(f"开始扫描失败: {str(e)}")
            return None
        finally:
            self.close()
    
    def _perform_scan(self, scan_id, scan_type, target):
        """执行安全扫描"""
        findings = []
        severity = "low"
        
        try:
            if scan_type == "vulnerability":
                # 漏洞扫描
                findings = self._scan_vulnerabilities(target)
            elif scan_type == "database":
                # 数据库安全扫描
                findings = self._scan_database(target)
            elif scan_type == "cache":
                # 缓存安全扫描
                findings = self._scan_cache(target)
            
            # 确定严重程度
            if findings:
                severity = "high" if any(f.get("critical", False) for f in findings) else "medium"
                
            # 更新扫描结果
            self._update_scan_result(scan_id, findings, severity)
            
        except Exception as e:
            print(f"执行扫描失败: {str(e)}")
            self._update_scan_result(scan_id, [f"扫描失败: {str(e)}"], "error")
    
    def _scan_vulnerabilities(self, target):
        """扫描漏洞"""
        findings = []
        
        # 模拟漏洞扫描
        if target == "app":
            # 检查常见漏洞
            if not self._check_csrf_protection():
                findings.append({
                    "type": "CSRF",
                    "description": "CSRF保护未启用",
                    "severity": "medium",
                    "critical": False
                })
            
            if not self._check_xss_protection():
                findings.append({
                    "type": "XSS",
                    "description": "XSS保护未启用",
                    "severity": "medium",
                    "critical": False
                })
        
        return findings
    
    def _scan_database(self, target):
        """扫描数据库安全"""
        findings = []
        
        # 检查数据库连接
        if not self.connect():
            findings.append({
                "type": "database",
                "description": "数据库连接失败",
                "severity": "high",
                "critical": True
            })
        else:
            # 检查敏感表权限
            try:
                self.cursor.execute("PRAGMA table_info(ai_instances)")
                findings.append({
                    "type": "database",
                    "description": "数据库连接正常",
                    "severity": "low",
                    "critical": False
                })
            except Exception as e:
                findings.append({
                    "type": "database",
                    "description": f"数据库权限问题: {str(e)}",
                    "severity": "high",
                    "critical": True
                })
            finally:
                self.close()
        
        return findings
    
    def _scan_cache(self, target):
        """扫描缓存安全"""
        findings = []
        
        # 检查缓存目录权限
        cache_dir = "app/cache"
        if os.path.exists(cache_dir):
            if not os.access(cache_dir, os.W_OK):
                findings.append({
                    "type": "cache",
                    "description": "缓存目录无写入权限",
                    "severity": "medium",
                    "critical": False
                })
        else:
            findings.append({
                "type": "cache",
                "description": "缓存目录不存在",
                "severity": "low",
                "critical": False
            })
        
        return findings
    
    def _update_scan_result(self, scan_id, findings, severity):
        """更新扫描结果"""
        if not self.connect():
            return
        
        try:
            sql = """
            UPDATE security_scans 
            SET end_time = CURRENT_TIMESTAMP, status = 'completed', findings = ?, severity = ?
            WHERE id = ?
            """
            self.cursor.execute(sql, (json.dumps(findings), severity, scan_id))
            self.conn.commit()
            
            # 添加安全事件
            if findings:
                message = f"安全扫描发现 {len(findings)} 个问题"
                self.add_security_event(
                    "scan", 
                    severity, 
                    message, 
                    source="security_service",
                    details={"findings": findings}
                )
                
        except Exception as e:
            print(f"更新扫描结果失败: {str(e)}")
        finally:
            self.close()
    
    def _check_csrf_protection(self):
        """检查CSRF保护"""
        if not self.connect():
            return False
        
        try:
            self.cursor.execute("SELECT config_value FROM security_configs WHERE config_key = 'enable_csrf_protection'")
            result = self.cursor.fetchone()
            return result and result[0].lower() == "true"
        except Exception as e:
            print(f"检查CSRF保护失败: {str(e)}")
            return False
        finally:
            self.close()
    
    def _check_xss_protection(self):
        """检查XSS保护"""
        if not self.connect():
            return False
        
        try:
            self.cursor.execute("SELECT config_value FROM security_configs WHERE config_key = 'enable_xss_protection'")
            result = self.cursor.fetchone()
            return result and result[0].lower() == "true"
        except Exception as e:
            print(f"检查XSS保护失败: {str(e)}")
            return False
        finally:
            self.close()
    
    def encrypt_data(self, data):
        """加密数据"""
        try:
            import hashlib
            import hmac
            
            if not self.encryption_key:
                self.load_config()
            
            # 使用HMAC SHA256进行加密
            if isinstance(data, dict) or isinstance(data, list):
                data = json.dumps(data)
            
            if isinstance(data, str):
                data = data.encode()
            
            hashed = hmac.new(self.encryption_key, data, hashlib.sha256)
            return base64.b64encode(hashed.digest()).decode()
        except Exception as e:
            print(f"加密数据失败: {str(e)}")
            return None
    
    def verify_data(self, data, signature):
        """验证数据"""
        try:
            if not self.encryption_key:
                self.load_config()
            
            if isinstance(data, dict) or isinstance(data, list):
                data = json.dumps(data)
            
            if isinstance(data, str):
                data = data.encode()
            
            hashed = hmac.new(self.encryption_key, data, hashlib.sha256)
            expected_signature = base64.b64encode(hashed.digest()).decode()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            print(f"验证数据失败: {str(e)}")
            return False
    
    def sanitize_input(self, input_str):
        """清理输入数据，防止XSS攻击"""
        if not input_str:
            return input_str
        
        # 转义HTML特殊字符
        sanitized = str(input_str)
        sanitized = sanitized.replace('&', '&amp;')
        sanitized = sanitized.replace('<', '&lt;')
        sanitized = sanitized.replace('>', '&gt;')
        sanitized = sanitized.replace('"', '&quot;')
        sanitized = sanitized.replace("'", '&#x27;')
        sanitized = sanitized.replace('/', '&#x2F;')
        
        return sanitized
    
    def detect_sql_injection(self, query):
        """检测SQL注入攻击"""
        if not query:
            return False
        
        # 常见SQL注入模式
        patterns = [
            r'\b(OR|AND)\b.*\b(1=1|1=0)\b',
            r'\bUNION\b.*\bSELECT\b',
            r'\bDROP\b.*\bTABLE\b',
            r'\bINSERT\b.*\bINTO\b',
            r'\bDELETE\b.*\bFROM\b',
            r'--',
            r';',
            r'\bEXEC\b',
            r'\bxp_',
            r'\bsp_'
        ]
        
        query_lower = query.lower()
        for pattern in patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return True
        
        return False
    
    def check_ddos_attack(self, ip_address):
        """检查DDoS攻击"""
        if not self.ddos_protection["enabled"]:
            return False, "DDoS保护已禁用"
        
        current_time = time.time()
        
        # 检查是否被阻塞
        if ip_address in self.ddos_protection["blocked_ips"]:
            block_until = self.ddos_protection["blocked_ips"][ip_address]
            if current_time < block_until:
                return True, f"IP已被临时阻塞，剩余时间: {int(block_until - current_time)}秒"
            else:
                # 解除阻塞
                del self.ddos_protection["blocked_ips"][ip_address]
        
        # 清理过期的请求记录
        if ip_address in self.ddos_protection["request_history"]:
            # 只保留最近60秒的请求
            self.ddos_protection["request_history"][ip_address] = [
                t for t in self.ddos_protection["request_history"][ip_address] 
                if current_time - t < 60
            ]
        else:
            self.ddos_protection["request_history"][ip_address] = []
        
        # 记录当前请求
        self.ddos_protection["request_history"][ip_address].append(current_time)
        
        # 检查请求频率
        request_count = len(self.ddos_protection["request_history"][ip_address])
        if request_count > self.ddos_protection["rate_limit"]:
            # 触发DDoS保护
            block_until = current_time + self.ddos_protection["block_duration"]
            self.ddos_protection["blocked_ips"][ip_address] = block_until
            
            # 记录安全事件
            self.add_security_event(
                "ddos",
                "high",
                f"检测到DDoS攻击，IP: {ip_address}，请求数: {request_count}",
                source="security_service",
                ip_address=ip_address,
                details={
                    "request_count": request_count,
                    "rate_limit": self.ddos_protection["rate_limit"],
                    "block_duration": self.ddos_protection["block_duration"]
                }
            )
            
            return True, f"检测到DDoS攻击，IP已被阻塞 {self.ddos_protection['block_duration']} 秒"
        
        return False, "正常请求"
    
    def check_memory_overflow(self):
        """检查内存溢出"""
        if not self.memory_monitoring["enabled"]:
            return False, "内存监控已禁用"
        
        current_time = time.time()
        if current_time - self.memory_monitoring["last_check"] < self.memory_monitoring["check_interval"]:
            return False, "检查间隔未到"
        
        self.memory_monitoring["last_check"] = current_time
        
        try:
            import psutil
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            if memory_usage > self.memory_monitoring["threshold"]:
                # 记录安全事件
                self.add_security_event(
                    "memory",
                    "high",
                    f"内存使用率过高: {memory_usage:.2f}%",
                    source="security_service",
                    details={
                        "memory_usage": memory_usage,
                        "threshold": self.memory_monitoring["threshold"],
                        "total_memory": memory.total,
                        "available_memory": memory.available
                    }
                )
                
                return True, f"内存使用率过高: {memory_usage:.2f}%"
            
            return False, f"内存使用率正常: {memory_usage:.2f}%"
        except Exception as e:
            print(f"检查内存失败: {str(e)}")
            return False, f"检查内存失败: {str(e)}"
    
    def start_monitoring(self):
        """启动安全监控"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scan_thread = threading.Thread(target=self._monitoring_loop)
        self.scan_thread.daemon = True
        self.scan_thread.start()
        print("安全监控服务已启动")
    
    def stop_monitoring(self):
        """停止安全监控"""
        self.is_running = False
        if self.scan_thread:
            self.scan_thread.join(timeout=5)
        print("安全监控服务已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                # 执行定期扫描
                self.start_scan("vulnerability", "app")
                self.start_scan("database", "app.db")
                self.start_scan("cache", "app/cache")
                
                # 检查系统状态
                self._check_system_status()
                
                # 检查内存溢出
                self.check_memory_overflow()
                
            except Exception as e:
                print(f"监控循环错误: {str(e)}")
            
            # 等待下一次扫描
            for _ in range(self.scanning_interval):
                if not self.is_running:
                    break
                time.sleep(1)
    
    def _check_system_status(self):
        """检查系统状态"""
        # 检查磁盘空间
        disk_usage = os.statvfs('.')
        free_space = disk_usage.f_bavail * disk_usage.f_frsize / (1024 * 1024 * 1024)
        
        if free_space < 10:  # 小于10GB
            self.add_security_event(
                "system",
                "warning",
                f"磁盘空间不足: {free_space:.2f} GB",
                source="security_service"
            )
        
        # 检查系统负载
        try:
            with open('/proc/loadavg', 'r') as f:
                load_avg = f.read().split()[0]
                if float(load_avg) > 5.0:
                    self.add_security_event(
                        "system",
                        "warning",
                        f"系统负载过高: {load_avg}",
                        source="security_service"
                    )
        except Exception:
            pass  # 在非Linux系统上忽略
    
    def get_security_events(self, limit=50, offset=0):
        """获取安全事件"""
        if not self.connect():
            return []
        
        try:
            sql = """
            SELECT id, event_type, severity, message, source, ip_address, user_agent, timestamp, status, details
            FROM security_events
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
            """
            self.cursor.execute(sql, (limit, offset))
            events = []
            for row in self.cursor.fetchall():
                event = {
                    "id": row[0],
                    "event_type": row[1],
                    "severity": row[2],
                    "message": row[3],
                    "source": row[4],
                    "ip_address": row[5],
                    "user_agent": row[6],
                    "timestamp": row[7],
                    "status": row[8],
                    "details": json.loads(row[9]) if row[9] else None
                }
                events.append(event)
            return events
        except Exception as e:
            print(f"获取安全事件失败: {str(e)}")
            return []
        finally:
            self.close()
    
    def get_security_scans(self, limit=50, offset=0):
        """获取安全扫描记录"""
        if not self.connect():
            return []
        
        try:
            sql = """
            SELECT id, scan_type, target, start_time, end_time, status, findings, severity
            FROM security_scans
            ORDER BY start_time DESC
            LIMIT ? OFFSET ?
            """
            self.cursor.execute(sql, (limit, offset))
            scans = []
            for row in self.cursor.fetchall():
                scan = {
                    "id": row[0],
                    "scan_type": row[1],
                    "target": row[2],
                    "start_time": row[3],
                    "end_time": row[4],
                    "status": row[5],
                    "findings": json.loads(row[6]) if row[6] else None,
                    "severity": row[7]
                }
                scans.append(scan)
            return scans
        except Exception as e:
            print(f"获取安全扫描记录失败: {str(e)}")
            return []
        finally:
            self.close()

# 全局安全服务实例
security_service = None

def get_security_service():
    """获取安全服务实例"""
    global security_service
    if security_service is None:
        security_service = SecurityService()
    return security_service

if __name__ == "__main__":
    # 测试安全服务
    service = SecurityService()
    
    # 启动监控
    service.start_monitoring()
    
    # 执行一次扫描
    scan_id = service.start_scan("vulnerability", "app")
    print(f"启动漏洞扫描，ID: {scan_id}")
    
    # 等待扫描完成
    time.sleep(2)
    
    # 获取扫描结果
    scans = service.get_security_scans(limit=1)
    if scans:
        print("扫描结果:")
        print(json.dumps(scans[0], indent=2, ensure_ascii=False))
    
    # 测试加密功能
    test_data = "测试数据"
    encrypted = service.encrypt_data(test_data)
    print(f"\n加密测试:")
    print(f"原始数据: {test_data}")
    print(f"加密后: {encrypted}")
    
    # 测试输入清理
    test_input = "<script>alert('XSS')</script>"
    sanitized = service.sanitize_input(test_input)
    print(f"\n输入清理测试:")
    print(f"原始输入: {test_input}")
    print(f"清理后: {sanitized}")
    
    # 测试SQL注入检测
    test_query = "SELECT * FROM users WHERE id = 1 OR 1=1"
    is_injection = service.detect_sql_injection(test_query)
    print(f"\nSQL注入检测测试:")
    print(f"查询: {test_query}")
    print(f"是否为SQL注入: {is_injection}")
    
    # 停止监控
    service.stop_monitoring()
