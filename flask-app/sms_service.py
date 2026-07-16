#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS短信服务模块
支持多种短信服务商接口
"""

import os
import json
import time
import threading
import queue
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class SmsService:
    """短信服务"""
    
    def __init__(self):
        self.config = self._load_config()
        self.queue = queue.Queue()
        self.is_running = False
        self._start_worker()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'sms_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'provider': 'aliyun',
            'providers': {
                'aliyun': {
                    'access_key_id': '',
                    'access_key_secret': '',
                    'sign_name': 'MTSCOS',
                    'endpoint': 'dysmsapi.aliyuncs.com'
                },
                'tencent': {
                    'secret_id': '',
                    'secret_key': '',
                    'sdk_app_id': '',
                    'sign_name': 'MTSCOS'
                },
                'huawei': {
                    'app_key': '',
                    'app_secret': '',
                    'sign_name': 'MTSCOS',
                    'sender': ''
                }
            },
            'queue_enabled': True,
            'max_retries': 3,
            'retry_delay': 60,
            'rate_limit': 10,
            'rate_limit_window': 60
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'sms_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _start_worker(self):
        """启动短信发送工作线程"""
        if not self.config['queue_enabled']:
            return
        
        self.is_running = True
        worker = threading.Thread(target=self._worker_loop, daemon=True)
        worker.start()
        logger(f"[短信服务] 短信队列工作线程已启动")
    
    def _worker_loop(self):
        """工作线程循环"""
        last_send_time = 0
        sent_count = 0
        
        while self.is_running:
            try:
                task = self.queue.get(timeout=10)
                
                now = time.time()
                if now - last_send_time >= self.config['rate_limit_window']:
                    sent_count = 0
                    last_send_time = now
                
                if sent_count >= self.config['rate_limit']:
                    time.sleep(self.config['rate_limit_window'] - (now - last_send_time))
                    sent_count = 0
                
                try:
                    success = self._send_sms_direct(
                        phone=task['phone'],
                        message=task['message'],
                        template_id=task.get('template_id'),
                        template_params=task.get('template_params')
                    )
                    if success:
                        logger(f"[短信服务] 短信发送成功: {task['phone']}")
                    else:
                        raise Exception("发送失败")
                except Exception as e:
                    logger(f"[短信服务] 短信发送失败: {e}")
                    if task.get('retry_count', 0) < self.config['max_retries']:
                        task['retry_count'] = task.get('retry_count', 0) + 1
                        time.sleep(self.config['retry_delay'])
                        self.queue.put(task)
                finally:
                    sent_count += 1
                    self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger(f"[短信服务] 工作线程错误: {e}")
    
    def _send_sms_direct(self, phone: str, message: str, 
                        template_id: str = None, 
                        template_params: Dict[str, str] = None) -> bool:
        """直接发送短信"""
        provider = self.config['provider']
        config = self.config['providers'].get(provider, {})
        
        if provider == 'aliyun':
            return self._send_aliyun_sms(phone, message, template_id, template_params, config)
        elif provider == 'tencent':
            return self._send_tencent_sms(phone, message, template_id, template_params, config)
        elif provider == 'huawei':
            return self._send_huawei_sms(phone, message, template_id, template_params, config)
        
        logger(f"[短信服务] 不支持的服务商: {provider}")
        return False
    
    def _send_aliyun_sms(self, phone: str, message: str, 
                         template_id: str = None, 
                         template_params: Dict[str, str] = None,
                         config: Dict[str, str] = {}) -> bool:
        """发送阿里云短信"""
        try:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcore.request import CommonRequest
            
            client = AcsClient(
                config.get('access_key_id'),
                config.get('access_key_secret'),
                'cn-hangzhou'
            )
            
            request = CommonRequest()
            request.set_accept_format('json')
            request.set_domain(config.get('endpoint', 'dysmsapi.aliyuncs.com'))
            request.set_method('POST')
            request.set_protocol_type('https')
            request.set_version('2017-05-25')
            request.set_action_name('SendSms')
            
            request.add_query_param('PhoneNumbers', phone)
            request.add_query_param('SignName', config.get('sign_name', 'MTSCOS'))
            
            if template_id:
                request.add_query_param('TemplateCode', template_id)
                if template_params:
                    import json as json_lib
                    request.add_query_param('TemplateParam', json_lib.dumps(template_params))
            else:
                request.add_query_param('TemplateCode', 'SMS_123456789')
                request.add_query_param('TemplateParam', json.dumps({'code': message}))
            
            response = client.do_action_with_exception(request)
            result = json.loads(response.decode('utf-8'))
            return result.get('Code') == 'OK'
        except ImportError:
            logger(f"[短信服务] 未安装阿里云SDK")
            return False
        except Exception as e:
            logger(f"[短信服务] 阿里云短信发送失败: {e}")
            return False
    
    def _send_tencent_sms(self, phone: str, message: str,
                          template_id: str = None,
                          template_params: Dict[str, str] = None,
                          config: Dict[str, str] = {}) -> bool:
        """发送腾讯云短信"""
        try:
            from tencentcloud.common import credential
            from tencentcloud.sms.v20210111 import sms_client, models
            
            cred = credential.Credential(
                config.get('secret_id'),
                config.get('secret_key')
            )
            
            client = sms_client.SmsClient(cred, "ap-beijing")
            
            req = models.SendSmsRequest()
            req.SmsSdkAppId = config.get('sdk_app_id')
            req.SignName = config.get('sign_name', 'MTSCOS')
            req.PhoneNumberSet = [phone]
            
            if template_id:
                req.TemplateId = template_id
                if template_params:
                    req.TemplateParamSet = list(template_params.values())
            else:
                req.TemplateId = "123456"
                req.TemplateParamSet = [message]
            
            resp = client.SendSms(req)
            return resp.SendStatusSet[0].Code == 'Ok'
        except ImportError:
            logger(f"[短信服务] 未安装腾讯云SDK")
            return False
        except Exception as e:
            logger(f"[短信服务] 腾讯云短信发送失败: {e}")
            return False
    
    def _send_huawei_sms(self, phone: str, message: str,
                         template_id: str = None,
                         template_params: Dict[str, str] = None,
                         config: Dict[str, str] = {}) -> bool:
        """发送华为云短信"""
        try:
            url = "https://api.wap-cn.rcsapi.huawei.com:443/sms/batchSendSms/v1"
            
            headers = {
                'Authorization': f'Bearer {config.get("app_key")}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'from': config.get('sender', 'MTSCOS'),
                'to': [phone],
                'text': message,
                'signature': config.get('sign_name', 'MTSCOS')
            }
            
            response = requests.post(url, headers=headers, json=data)
            return response.status_code == 200
        except Exception as e:
            logger(f"[短信服务] 华为云短信发送失败: {e}")
            return False
    
    def send_sms(self, phone: str, message: str, 
                 template_id: str = None, 
                 template_params: Dict[str, str] = None,
                 async_send: bool = True) -> bool:
        """发送短信"""
        if async_send and self.config['queue_enabled']:
            self.queue.put({
                'phone': phone,
                'message': message,
                'template_id': template_id,
                'template_params': template_params,
                'retry_count': 0
            })
            return True
        else:
            return self._send_sms_direct(phone, message, template_id, template_params)
    
    def send_verification_code(self, phone: str, code: str, 
                               async_send: bool = True) -> bool:
        """发送验证码"""
        message = f"【MTSCOS】您的验证码是{code}，5分钟内有效。"
        return self.send_sms(phone, message, async_send=async_send)
    
    def send_notification(self, phone: str, title: str, message: str,
                          async_send: bool = True) -> bool:
        """发送通知短信"""
        msg = f"【MTSCOS】{title}：{message}"
        return self.send_sms(phone, msg, async_send=async_send)
    
    def configure_provider(self, provider: str, config: Dict[str, str]):
        """配置服务商"""
        if provider in self.config['providers']:
            self.config['providers'][provider] = config
            self.config['provider'] = provider
            self._save_config()
            logger(f"[短信服务] 服务商配置已更新: {provider}")
        else:
            logger(f"[短信服务] 不支持的服务商: {provider}")
    
    def set_rate_limit(self, limit: int, window: int):
        """设置发送速率限制"""
        self.config['rate_limit'] = limit
        self.config['rate_limit_window'] = window
        self._save_config()
        logger(f"[短信服务] 速率限制已更新")
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'status': 'running' if self.is_running else 'stopped',
            'provider': self.config['provider'],
            'queue_size': self.queue.qsize(),
            'rate_limit': self.config['rate_limit'],
            'rate_limit_window': self.config['rate_limit_window'],
            'max_retries': self.config['max_retries'],
            'configured': bool(self.config['providers'].get(self.config['provider'], {}).get('access_key_id') or 
                               self.config['providers'].get(self.config['provider'], {}).get('secret_id') or
                               self.config['providers'].get(self.config['provider'], {}).get('app_key'))
        }
    
    def stop(self):
        """停止服务"""
        self.is_running = False
        logger(f"[短信服务] 短信服务已停止")

sms_service = SmsService()
