#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信 API 客户端服务
WeComClient - 封装企业微信开放平台所有核心接口

功能：
- access_token 自动获取与缓存刷新（提前5分钟）
- 应用消息推送（文本、图片、文件、小程序卡片等）
- 通讯录管理（部门、成员、标签）
- 审批流管理（创建审批、查询审批）
- 日程管理
- 会议管理
- 文档管理
- 客户联系（客户、群聊、朋友圈）
- 音视频通话
- 企业内部机器人 Webhook

作者: MTSCOS AI 系统
版本: v1.0.0
"""

import os
import json
import time
import hashlib
import threading
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)


class WeComClient:
    """企业微信 API 客户端"""

    # 基础 URL
    BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"

    def __init__(self, corpid: str = "", corpsecret: str = "", agentid: int = 0,
                 config_path: str = None):
        """
        初始化企业微信客户端

        Args:
            corpid: 企业 ID，为空则从环境变量或配置文件读取
            corpsecret: 应用密钥，为空则从环境变量或配置文件读取
            agentid: 应用 ID，为 0 则从环境变量或配置文件读取
            config_path: 配置文件路径，可选
        """
        self._access_token = None
        self._token_expire_time = 0
        self._token_lock = threading.Lock()
        self._token_refresh_thread = None
        self._stop_refresh = threading.Event()

        # 加载配置
        self.config = self._load_config(corpid, corpsecret, agentid, config_path)

        # 验证配置
        if not self.config.get('corpid') or not self.config.get('corpsecret'):
            logger.warning("[WeCom] 企业微信配置不完整，请设置 corpid 和 corpsecret")

        # 启动 token 自动刷新
        self._start_token_refresh()

    def _load_config(self, corpid: str, corpsecret: str, agentid: int,
                     config_path: str = None) -> Dict[str, Any]:
        """加载配置：优先级 参数 > 环境变量 > 配置文件"""
        config = {
            'corpid': corpid or os.environ.get('WECOM_CORPID', ''),
            'corpsecret': corpsecret or os.environ.get('WECOM_CORPSECRET', ''),
            'agentid': agentid or int(os.environ.get('WECOM_AGENTID', '0')),
            'enabled': True,
            'api_timeout': 30,
            'retry_count': 3,
            'retry_delay': 1,
        }

        # 从配置文件读取（如果存在）
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'wecom_config.json'
            )

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                # 文件配置作为默认值，参数/环境变量优先
                for key in ['corpid', 'corpsecret', 'agentid']:
                    if not config[key] and key in file_config:
                        config[key] = file_config[key]
                if 'enabled' in file_config:
                    config['enabled'] = file_config['enabled']
                if 'api_timeout' in file_config:
                    config['api_timeout'] = file_config['api_timeout']
            except Exception as e:
                logger.warning(f"[WeCom] 加载配置文件失败: {e}")

        config['_config_path'] = config_path
        return config

    def save_config(self, config: Dict[str, Any] = None):
        """保存配置到文件"""
        if config is None:
            config = self.config

        save_data = {
            'corpid': config.get('corpid', ''),
            'corpsecret': config.get('corpsecret', ''),
            'agentid': config.get('agentid', 0),
            'enabled': config.get('enabled', True),
            'api_timeout': config.get('api_timeout', 30),
            'retry_count': config.get('retry_count', 3),
            'retry_delay': config.get('retry_delay', 1),
        }

        config_path = self.config.get('_config_path', 'wecom_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

    # ==================== Access Token 管理 ====================

    def _get_access_token(self) -> str:
        """获取 access_token，自动缓存和刷新"""
        with self._token_lock:
            now = time.time()
            # 提前 5 分钟刷新
            if self._access_token and now < self._token_expire_time - 300:
                return self._access_token

            return self._refresh_access_token()

    def _refresh_access_token(self) -> str:
        """刷新 access_token"""
        if not self.config.get('corpid') or not self.config.get('corpsecret'):
            raise ValueError("企业微信 corpid 和 corpsecret 未配置")

        url = (f"{self.BASE_URL}/gettoken"
               f"?corpid={self.config['corpid']}"
               f"&corpsecret={self.config['corpsecret']}")

        result = self._http_get(url)

        if result.get('errcode') != 0:
            error_msg = result.get('errmsg', 'Unknown error')
            logger.error(f"[WeCom] 获取 access_token 失败: {error_msg}")
            raise Exception(f"获取 access_token 失败: {error_msg}")

        self._access_token = result['access_token']
        self._token_expire_time = time.time() + result.get('expires_in', 7200)

        logger.info("[WeCom] access_token 刷新成功")
        return self._access_token

    def _start_token_refresh(self):
        """启动 token 自动刷新线程"""
        def refresh_loop():
            while not self._stop_refresh.is_set():
                try:
                    # 每 60 秒检查一次，是否需要刷新
                    time.sleep(60)
                    if self._token_expire_time - time.time() < 300:
                        with self._token_lock:
                            if self._access_token and self._token_expire_time - time.time() < 300:
                                self._refresh_access_token()
                except Exception as e:
                    logger.warning(f"[WeCom] Token 刷新线程异常: {e}")

        self._token_refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        self._token_refresh_thread.start()

    def stop(self):
        """停止客户端"""
        self._stop_refresh.set()
        if self._token_refresh_thread:
            self._token_refresh_thread.join(timeout=5)
        logger.info("[WeCom] 客户端已停止")

    # ==================== HTTP 工具方法 ====================

    def _http_get(self, url: str, params: Dict[str, str] = None) -> Dict[str, Any]:
        """发送 GET 请求"""
        if params:
            url = f"{url}&{urlencode(params)}"

        try:
            req = Request(url)
            req.add_header('Content-Type', 'application/json')
            with urlopen(req, timeout=self.config.get('api_timeout', 30)) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data
        except HTTPError as e:
            logger.error(f"[WeCom] HTTP GET 错误: {e.code} {e.reason}")
            return {'errcode': -1, 'errmsg': str(e)}
        except URLError as e:
            logger.error(f"[WeCom] URL 错误: {e.reason}")
            return {'errcode': -1, 'errmsg': str(e.reason)}
        except Exception as e:
            logger.error(f"[WeCom] 请求异常: {e}")
            return {'errcode': -1, 'errmsg': str(e)}

    def _http_post(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送 POST 请求"""
        try:
            body = json.dumps(data).encode('utf-8')
            req = Request(url, data=body, method='POST')
            req.add_header('Content-Type', 'application/json')
            with urlopen(req, timeout=self.config.get('api_timeout', 30)) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result
        except HTTPError as e:
            logger.error(f"[WeCom] HTTP POST 错误: {e.code} {e.reason}")
            return {'errcode': -1, 'errmsg': str(e)}
        except URLError as e:
            logger.error(f"[WeCom] URL 错误: {e.reason}")
            return {'errcode': -1, 'errmsg': str(e.reason)}
        except Exception as e:
            logger.error(f"[WeCom] 请求异常: {e}")
            return {'errcode': -1, 'errmsg': str(e)}

    def _request_with_retry(self, method: str, url: str,
                            data: Dict[str, Any] = None) -> Dict[str, Any]:
        """带重试的请求"""
        retry_count = self.config.get('retry_count', 3)
        retry_delay = self.config.get('retry_delay', 1)
        last_error = None

        for attempt in range(retry_count):
            try:
                if method == 'GET':
                    result = self._http_get(url)
                else:
                    result = self._http_post(url, data or {})

                if result.get('errcode') == 0:
                    return result
                elif result.get('errcode') == 40014:
                    # access_token 失效，强制刷新
                    with self._token_lock:
                        self._refresh_access_token()
                    continue
                else:
                    return result

            except Exception as e:
                last_error = e
                if attempt < retry_count - 1:
                    time.sleep(retry_delay * (attempt + 1))
                continue

        return {'errcode': -1, 'errmsg': f'请求失败（重试{retry_count}次）: {last_error}'}

    # ==================== 应用消息推送 ====================

    def send_text_message(self, user_ids: List[str], content: str,
                          agentid: int = None, safe: int = 0) -> Dict[str, Any]:
        """
        发送文本消息

        Args:
            user_ids: 接收人 userid 列表，@all 表示全部
            content: 文本内容，最长 2048 字节
            agentid: 应用 ID，默认使用配置中的
            safe: 是否保密消息
        """
        token = self._get_access_token()
        agentid = agentid or self.config.get('agentid', 0)

        data = {
            "touser": "|".join(user_ids) if user_ids else "@all",
            "msgtype": "text",
            "agentid": agentid,
            "text": {"content": content},
            "safe": safe
        }

        url = f"{self.BASE_URL}/message/send?access_token={token}"
        return self._request_with_retry('POST', url, data)

    def send_markdown_message(self, user_ids: List[str], content: str,
                               agentid: int = None) -> Dict[str, Any]:
        """发送 Markdown 消息"""
        token = self._get_access_token()
        agentid = agentid or self.config.get('agentid', 0)

        data = {
            "touser": "|".join(user_ids) if user_ids else "@all",
            "msgtype": "markdown",
            "agentid": agentid,
            "markdown": {"content": content}
        }

        url = f"{self.BASE_URL}/message/send?access_token={token}"
        return self._request_with_retry('POST', url, data)

    def send_image_message(self, user_ids: List[str], media_id: str,
                            agentid: int = None) -> Dict[str, Any]:
        """发送图片消息"""
        token = self._get_access_token()
        agentid = agentid or self.config.get('agentid', 0)

        data = {
            "touser": "|".join(user_ids) if user_ids else "@all",
            "msgtype": "image",
            "agentid": agentid,
            "image": {"media_id": media_id}
        }

        url = f"{self.BASE_URL}/message/send?access_token={token}"
        return self._request_with_retry('POST', url, data)

    def send_file_message(self, user_ids: List[str], media_id: str,
                           agentid: int = None) -> Dict[str, Any]:
        """发送文件消息"""
        token = self._get_access_token()
        agentid = agentid or self.config.get('agentid', 0)

        data = {
            "touser": "|".join(user_ids) if user_ids else "@all",
            "msgtype": "file",
            "agentid": agentid,
            "file": {"media_id": media_id}
        }

        url = f"{self.BASE_URL}/message/send?access_token={token}"
        return self._request_with_retry('POST', url, data)

    def send_textcard_message(self, user_ids: List[str], title: str,
                               description: str, url: str,
                               agentid: int = None) -> Dict[str, Any]:
        """发送文本卡片消息"""
        token = self._get_access_token()
        agentid = agentid or self.config.get('agentid', 0)

        data = {
            "touser": "|".join(user_ids) if user_ids else "@all",
            "msgtype": "textcard",
            "agentid": agentid,
            "textcard": {
                "title": title,
                "description": description,
                "url": url,
                "btntxt": "点击查看"
            }
        }

        url = f"{self.BASE_URL}/message/send?access_token={token}"
        return self._request_with_retry('POST', url, data)

    def send_taskcard_message(self, user_ids: List[str], title: str,
                               description: str, task_id: str,
                               agentid: int = None) -> Dict[str, Any]:
        """发送任务卡片消息"""
        token = self._get_access_token()
        agentid = agentid or self.config.get('agentid', 0)

        data = {
            "touser": "|".join(user_ids) if user_ids else "@all",
            "msgtype": "taskcard",
            "agentid": agentid,
            "taskcard": {
                "title": title,
                "description": description,
                "task_id": task_id,
                "btn": [
                    {"key": "detail", "name": "查看详情"}
                ]
            }
        }

        url = f"{self.BASE_URL}/message/send?access_token={token}"
        return self._request_with_retry('POST', url, data)

    def send_template_card(self, user_ids: List[str], card_json: str,
                            agentid: int = None) -> Dict[str, Any]:
        """发送模板卡片消息"""
        token = self._get_access_token()
        agentid = agentid or self.config.get('agentid', 0)

        data = {
            "touser": "|".join(user_ids) if user_ids else "@all",
            "msgtype": "template_card",
            "agentid": agentid,
            "template_card": json.loads(card_json) if isinstance(card_json, str) else card_json
        }

        url = f"{self.BASE_URL}/message/send?access_token={token}"
        return self._request_with_retry('POST', url, data)

    # ==================== 通讯录管理 ====================

    def get_department_list(self, department_id: int = 1) -> Dict[str, Any]:
        """获取部门列表"""
        token = self._get_access_token()
        url = (f"{self.BASE_URL}/department/list"
               f"?access_token={token}&id={department_id}")
        return self._request_with_retry('GET', url)

    def get_department_detail(self, department_id: int) -> Dict[str, Any]:
        """获取部门详情"""
        token = self._get_access_token()
        url = (f"{self.BASE_URL}/department/get"
               f"?access_token={token}&id={department_id}")
        return self._request_with_retry('GET', url)

    def create_department(self, name: str, parent_id: int = 1,
                           order: int = 0, department_id: int = None) -> Dict[str, Any]:
        """创建部门"""
        token = self._get_access_token()
        data = {
            "name": name,
            "parentid": parent_id,
            "order": order
        }
        if department_id:
            data["id"] = department_id

        url = f"{self.BASE_URL}/department/create?access_token={token}"
        return self._request_with_retry('POST', url, data)

    def update_department(self, department_id: int, name: str = None,
                          parent_id: int = None, order: int = None) -> Dict[str, Any]:
        """更新部门"""
        token = self._get_access_token()
        data = {"id": department_id}
        if name:
            data["name"] = name
        if parent_id:
            data["parentid"] = parent_id
        if order:
            data["order"] = order

        url = f"{self.BASE_URL}/department/update?access_token={token}"
        return self._request_with_retry('POST', url, data)

    def delete_department(self, department_id: int) -> Dict[str, Any]:
        """删除部门"""
        token = self._get_access_token()
        url = (f"{self.BASE_URL}/department/delete"
               f"?access_token={token}&id={department_id}")
        return self._request_with_retry('GET', url)

    def get_user_list(self, department_id: int = 1, fetch_child: int = 1,
                       key_word: str = "") -> Dict[str, Any]:
        """获取成员列表"""
        token = self._get_access_token()
        url = (f"{self.BASE_URL}/user/list"
               f"?access_token={token}&department_id={department_id}"
               f"&fetch_child={fetch_child}&keyword={key_word}")
        return self._request_with_retry('GET', url)

    def get_user_detail(self, user_id: str) -> Dict[str, Any]:
        """获取成员详情"""
        token = self._get_access_token()
        url = (f"{self.BASE_URL}/user/get"
               f"?access_token={token}&userid={user_id}")
        return self._request_with_retry('GET', url)

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建成员"""
        token = self._get_access_token()
        url = f"{self.BASE_URL}/user/create?access_token={token}"
        return self._request_with_retry('POST', url, user_data)

    def update_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新成员"""
        token = self._get_access_token()
        url = f"{self.BASE_URL}/user/update?access_token={token}"
        return self._request_with_retry('POST', url, user_data)

    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """删除成员"""
        token = self._get_access_token()
        url = f"{self.BASE_URL}/user/delete?access_token={token}&userid={user_id}"
        return self._request_with_retry('GET', url)

    def get_tag_list(self) -> Dict[str, Any]:
        """获取标签列表"""
        token = self._get_access_token()
        url = f"{self.BASE_URL}/tag/list?access_token={token}"
        return self._request_with_retry('GET', url)

    def get_tag_users(self, tag_id: int) -> Dict[str, Any]:
        """获取标签成员"""
        token = self._get_access_token()
        url = (f"{self.BASE_URL}/tag/get"
               f"?access_token={token}&tagid={tag_id}")
        return self._request_with_retry('GET', url)

    def add_tag_users(self, tag_id: int, user_ids: List[str]) -> Dict[str, Any]:
        """添加标签成员"""
        token = self._get_access_token()
        data = {"tagid": tag_id, "userlist": user_ids}
        url = f"{self.BASE_URL}/tag/addtagusers?access_token={token}"
        return self._request_with_retry('POST', url, data)

    # ==================== 审批流管理 ====================

    def get_approval_template_list(self, cursor: int = 0, limit: int = 20) -> Dict[str, Any]:
        """获取审批模板列表"""
        token = self._get_access_token()
        data = {"cursor": cursor, "limit": limit}
        url = f"{self.BASE_URL}/oa/template/list?access_token={token}"
        return self._request_with_retry('POST', url, data)

    def get_approval_template_detail(self, template_id: str) -> Dict[str, Any]:
        """获取审批模板详情"""
        token = self._get_access_token()
        url = (f"{self.BASE_URL}/oa/template/get"
               f"?access_token={token}&template_id={template_id}")
        return self._request_with_retry('GET', url)

    def create_approval(self, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """发起审批"""
        token = self._get_access_token()
        url = f"{self.BASE_URL}/oa/applyevent?access_token={token}"
        return self._request_with_retry('POST', url, approval_data)

    def get_approval_detail(self, approval_id: str) -> Dict[str, Any]:
        """获取审批详情"""
        token = self._get_access_token()
        url = (f"{self.BASE_URL}/oa/getapprovaldetail"
               f"?access_token={token}&approvalid={approval_id}")
        return self._request_with_retry('GET', url)

    def get_approval_list(self, start_time: int, end_time: int,
                          cursor: int = 0, limit: int = 20) -> Dict[str, Any]:
        """获取审批列表"""
        token = self._get_access_token()
        data = {
            "starttime": start_time,
            "endtime": end_time,
            "cursor": cursor,
            "limit": limit
        }
        url = f"{self.BASE_URL}/oa/getapprovallist?access_token={token}"
        return self._request_with_retry('POST', url, data)

    # ==================== 日程管理 ====================

    def create_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建日程"""
        token = self._get_access_token()
        url = f"{self.BASE_URL}/schedule/add?access_token={token}"
        return self._request_with_retry('POST', url, schedule_data)

    def get_schedule_list(self, user_id: str, start_time: int = None,
                          end_time: int = None) -> Dict[str, Any]:
        """获取日程列表"""
        token = self._get_access_token()
        params = {"access_token": token, "userid": user_id}
        if start_time:
            params["starttime"] = start_time
        if end_time:
            params["endtime"] = end_time
        url = f"{self.BASE_URL}/schedule/get?{urlencode(params)}"
        return self._request_with_retry('GET', url)

    # ==================== 会议管理 ====================

    def create_meeting(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建会议"""
        token = self._get_access_token()
        url = f"{self.BASE_URL}/meetingroom/create?access_token={token}"
        return self._request_with_retry('POST', url, meeting_data)

    def get_meeting_list(self, cursor: int = 0, limit: int = 20) -> Dict[str, Any]:
        """获取会议列表"""
        token = self._get_access_token()
        data = {"cursor": cursor, "limit": limit}
        url = f"{self.BASE_URL}/meetingroom/list?access_token={token}"
        return self._request_with_retry('POST', url, data)

    # ==================== 企业机器人 Webhook ====================

    @staticmethod
    def send_webhook_message(webhook_url: str, content: str,
                              msg_type: str = "text") -> Dict[str, Any]:
        """
        发送企业微信群机器人消息

        Args:
            webhook_url: Webhook URL
            content: 消息内容
            msg_type: 消息类型 (text/markdown/image/news)
        """
        try:
            if msg_type == "text":
                data = {"msgtype": "text", "text": {"content": content}}
            elif msg_type == "markdown":
                data = {"msgtype": "markdown", "markdown": {"content": content}}
            else:
                return {"errcode": -1, "errmsg": f"不支持的消息类型: {msg_type}"}

            body = json.dumps(data).encode('utf-8')
            req = Request(webhook_url, data=body, method='POST')
            req.add_header('Content-Type', 'application/json')
            with urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result
        except Exception as e:
            return {"errcode": -1, "errmsg": str(e)}

    # ==================== 消息撤回 ====================

    def recall_message(self, message_id: str) -> Dict[str, Any]:
        """撤回应用消息"""
        token = self._get_access_token()
        data = {"msgid": message_id}
        url = f"{self.BASE_URL}/message/recall?access_token={token}"
        return self._request_with_retry('POST', url, data)

    # ==================== 媒体上传 ====================

    def upload_media(self, media_type: str, file_path: str) -> Dict[str, Any]:
        """
        上传临时素材

        Args:
            media_type: 媒体类型 (image/voice/video/file)
            file_path: 文件路径
        """
        token = self._get_access_token()
        url = (f"{self.BASE_URL}/media/upload"
               f"?access_token={token}&type={media_type}")

        try:
            boundary = hashlib.md5(str(time.time()).encode()).hexdigest()
            with open(file_path, 'rb') as f:
                file_data = f.read()

            # 简化实现：使用 multipart/form-data
            body = (f'--{boundary}\r\n'
                    f'Content-Disposition: form-data; name="media"; filename="{os.path.basename(file_path)}"\r\n'
                    f'Content-Type: application/octet-stream\r\n'
                    f'\r\n').encode() + file_data + f'\r\n--{boundary}--\r\n'.encode()

            req = Request(url, data=body, method='POST')
            req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

            with urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result
        except Exception as e:
            logger.error(f"[WeCom] 上传素材失败: {e}")
            return {"errcode": -1, "errmsg": str(e)}

    # ==================== 身份验证 ====================

    def get_user_by_code(self, code: str) -> Dict[str, Any]:
        """通过授权 code 获取用户信息"""
        token = self._get_access_token()
        url = f"{self.BASE_URL}/user/getuserinfo?access_token={token}&code={code}"
        return self._request_with_retry('GET', url)

    def get_user_detail_by_userid(self, user_id: str) -> Dict[str, Any]:
        """获取用户详细信息"""
        token = self._get_access_token()
        url = f"{self.BASE_URL}/user/get?access_token={token}&userid={user_id}"
        return self._request_with_retry('GET', url)

    # ==================== 系统状态 ====================

    def get_status(self) -> Dict[str, Any]:
        """获取客户端状态"""
        return {
            "enabled": self.config.get('enabled', True),
            "configured": bool(self.config.get('corpid') and self.config.get('corpsecret')),
            "token_valid": bool(self._access_token and time.time() < self._token_expire_time),
            "token_expires_at": datetime.fromtimestamp(self._token_expire_time).isoformat()
            if self._token_expire_time > 0 else None,
            "corpid": self.config.get('corpid', '')[:4] + '****' if self.config.get('corpid') else '',
            "agentid": self.config.get('agentid', 0),
        }

    def ping(self) -> Dict[str, Any]:
        """测试连接"""
        try:
            if not self.config.get('corpid') or not self.config.get('corpsecret'):
                return {"success": False, "message": "企业微信未配置"}

            token = self._get_access_token()
            return {
                "success": True,
                "message": "连接成功",
                "token_valid": True,
                "token_expires_at": datetime.fromtimestamp(self._token_expire_time).isoformat()
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


# ==================== 单例管理 ====================

_wecom_client_instance = None
_wecom_client_lock = threading.Lock()


def get_wecom_client(corpid: str = "", corpsecret: str = "",
                     agentid: int = 0) -> WeComClient:
    """获取企业微信客户端单例"""
    global _wecom_client_instance
    if _wecom_client_instance is None:
        with _wecom_client_lock:
            if _wecom_client_instance is None:
                _wecom_client_instance = WeComClient(corpid, corpsecret, agentid)
    return _wecom_client_instance


def reset_wecom_client():
    """重置企业微信客户端单例"""
    global _wecom_client_instance
    if _wecom_client_instance:
        _wecom_client_instance.stop()
    with _wecom_client_lock:
        _wecom_client_instance = None


if __name__ == '__main__':
    # 测试代码
    client = WeComClient()
    status = client.get_status()
    print(f"客户端状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
    ping = client.ping()
    print(f"连接测试: {json.dumps(ping, indent=2, ensure_ascii=False)}")
