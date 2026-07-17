#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS邮件服务模块
支持SMTP邮件发送、模板渲染、邮件队列
"""

import smtplib
import ssl
import os
import json
import time
import threading
import queue
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class EmailService:
    """邮件服务"""
    
    def __init__(self):
        self.config = self._load_config()
        self.queue = queue.Queue()
        self.is_running = False
        self._start_worker()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'email_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'smtp': {
                'host': 'smtp.qq.com',
                'port': 587,
                'username': '',
                'password': '',
                'use_tls': True
            },
            'default_sender': {
                'name': 'MTSCOS AI系统',
                'email': ''
            },
            'template_dir': 'email_templates',
            'queue_enabled': True,
            'max_retries': 3,
            'retry_delay': 60
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'email_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _start_worker(self):
        """启动邮件发送工作线程"""
        if not self.config['queue_enabled']:
            return
        
        self.is_running = True
        worker = threading.Thread(target=self._worker_loop, daemon=True)
        worker.start()
        logger(f"[邮件服务] 邮件队列工作线程已启动")
    
    def _worker_loop(self):
        """工作线程循环"""
        while self.is_running:
            try:
                task = self.queue.get(timeout=10)
                try:
                    self._send_email_direct(
                        to_email=task['to_email'],
                        subject=task['subject'],
                        content=task['content'],
                        is_html=task['is_html'],
                        from_name=task.get('from_name'),
                        from_email=task.get('from_email')
                    )
                    logger(f"[邮件服务] 邮件发送成功: {task['to_email']}")
                except Exception as e:
                    logger(f"[邮件服务] 邮件发送失败: {e}")
                    if task.get('retry_count', 0) < self.config['max_retries']:
                        task['retry_count'] = task.get('retry_count', 0) + 1
                        time.sleep(self.config['retry_delay'])
                        self.queue.put(task)
                finally:
                    self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger(f"[邮件服务] 工作线程错误: {e}")
    
    def _send_email_direct(self, to_email: str, subject: str, content: str, 
                          is_html: bool = False, from_name: str = None, 
                          from_email: str = None) -> bool:
        """直接发送邮件"""
        smtp_config = self.config['smtp']
        
        if not smtp_config['username'] or not smtp_config['password']:
            logger(f"[邮件服务] SMTP配置未完成")
            return False
        
        sender_name = from_name or self.config['default_sender']['name']
        sender_email = from_email or self.config['default_sender']['email'] or smtp_config['username']
        
        msg = MIMEMultipart()
        msg['From'] = formataddr((sender_name, sender_email))
        msg['To'] = to_email
        msg['Subject'] = subject
        
        body = MIMEText(content, 'html' if is_html else 'plain', 'utf-8')
        msg.attach(body)
        
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
                if smtp_config['use_tls']:
                    server.starttls(context=context)
                server.login(smtp_config['username'], smtp_config['password'])
                server.sendmail(sender_email, to_email, msg.as_string())
            return True
        except Exception as e:
            logger(f"[邮件服务] 发送失败: {e}")
            return False
    
    def send_email(self, to_email: str, subject: str, content: str, 
                   is_html: bool = False, from_name: str = None, 
                   from_email: str = None, async_send: bool = True) -> bool:
        """发送邮件"""
        if async_send and self.config['queue_enabled']:
            self.queue.put({
                'to_email': to_email,
                'subject': subject,
                'content': content,
                'is_html': is_html,
                'from_name': from_name,
                'from_email': from_email,
                'retry_count': 0
            })
            return True
        else:
            return self._send_email_direct(to_email, subject, content, is_html, from_name, from_email)
    
    def send_template_email(self, to_email: str, template_name: str, 
                           template_data: Dict[str, Any], subject: str = None,
                           from_name: str = None, from_email: str = None,
                           async_send: bool = True) -> bool:
        """发送模板邮件"""
        template_path = os.path.join(self.config['template_dir'], f"{template_name}.html")
        
        if not os.path.exists(template_path):
            logger(f"[邮件服务] 模板文件不存在: {template_path}")
            return False
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        for key, value in template_data.items():
            template_content = template_content.replace(f"{{{{{key}}}}}", str(value))
        
        if not subject:
            subject = self._extract_subject(template_content)
        
        return self.send_email(to_email, subject, template_content, is_html=True,
                              from_name=from_name, from_email=from_email, async_send=async_send)
    
    def _extract_subject(self, html_content: str) -> str:
        """从HTML中提取主题"""
        import re
        match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
        if match:
            return match.group(1)
        return "MTSCOS系统通知"
    
    def send_activation_email(self, to_email: str, activation_code: str, 
                             username: str = '', async_send: bool = True) -> bool:
        """发送激活邮件"""
        content = f"""
        <html>
        <body>
        <h2>欢迎注册MTSCOS AI系统</h2>
        <p>尊敬的 {username or '用户'}：</p>
        <p>请点击下方链接激活您的账户：</p>
        <p><a href="http://your-domain.com/activate?code={activation_code}">激活账户</a></p>
        <p>或者使用激活码：<strong>{activation_code}</strong></p>
        <p>如果您没有注册，请忽略此邮件。</p>
        <p>MTSCOS AI系统</p>
        </body>
        </html>
        """
        return self.send_email(to_email, "账户激活", content, is_html=True, async_send=async_send)
    
    def send_reset_password_email(self, to_email: str, reset_code: str, 
                                  username: str = '', async_send: bool = True) -> bool:
        """发送重置密码邮件"""
        content = f"""
        <html>
        <body>
        <h2>重置密码</h2>
        <p>尊敬的 {username or '用户'}：</p>
        <p>请点击下方链接重置您的密码：</p>
        <p><a href="http://your-domain.com/reset-password?code={reset_code}">重置密码</a></p>
        <p>重置码：<strong>{reset_code}</strong></p>
        <p>如果您没有请求重置密码，请忽略此邮件。</p>
        <p>MTSCOS AI系统</p>
        </body>
        </html>
        """
        return self.send_email(to_email, "重置密码", content, is_html=True, async_send=async_send)
    
    def send_notification_email(self, to_email: str, title: str, message: str, 
                                async_send: bool = True) -> bool:
        """发送通知邮件"""
        content = f"""
        <html>
        <body>
        <h2>{title}</h2>
        <p>{message}</p>
        <p>MTSCOS AI系统</p>
        </body>
        </html>
        """
        return self.send_email(to_email, title, content, is_html=True, async_send=async_send)
    
    def configure_smtp(self, host: str, port: int, username: str, password: str, use_tls: bool = True):
        """配置SMTP"""
        self.config['smtp'] = {
            'host': host,
            'port': port,
            'username': username,
            'password': password,
            'use_tls': use_tls
        }
        self._save_config()
        logger(f"[邮件服务] SMTP配置已更新")
    
    def set_default_sender(self, name: str, email: str):
        """设置默认发件人"""
        self.config['default_sender'] = {
            'name': name,
            'email': email
        }
        self._save_config()
        logger(f"[邮件服务] 默认发件人已更新")
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'status': 'running' if self.is_running else 'stopped',
            'queue_size': self.queue.qsize(),
            'smtp_configured': bool(self.config['smtp']['username'] and self.config['smtp']['password']),
            'max_retries': self.config['max_retries'],
            'retry_delay': self.config['retry_delay']
        }
    
    def stop(self):
        """停止服务"""
        self.is_running = False
        logger(f"[邮件服务] 邮件服务已停止")

email_service = EmailService()
