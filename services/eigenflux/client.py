"""
EigenFlux HTTP / WebSocket 客户端

封装对 EigenFlux Hub 的 REST API 和 WebSocket 调用。
支持公共 Hub 和自部署 Hub。
"""

import json
import time
import logging
import threading
from typing import Optional, List, Dict, Any, Callable, Union
from urllib.parse import urljoin

import requests

from .config import EigenFluxConfig
from .models import (
    BroadcastMessage,
    BroadcastResponse,
    AgentProfile,
    Subscription,
    MatchResult,
)

logger = logging.getLogger(__name__)


class EigenFluxClient:
    """EigenFlux API 客户端

    支持通过 HTTP REST API 与 EigenFlux Hub 通信，
    以及通过 WebSocket 接收实时消息推送。
    """

    def __init__(self, config: Optional[EigenFluxConfig] = None):
        from .config import get_config
        self.config = config or get_config()
        self._session = requests.Session()
        self._ws = None
        self._ws_thread = None
        self._ws_running = False
        self._message_handlers: List[Callable[[Dict[str, Any]], None]] = []

        if self.config.proxy:
            self._session.proxies = {
                "http": self.config.proxy,
                "https": self.config.proxy,
            }

        self._setup_auth()

    def _setup_auth(self) -> None:
        """设置认证头"""
        if self.config.api_token:
            self._session.headers.update({
                "Authorization": f"Bearer {self.config.api_token}",
            })
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"MTSCOS-EigenFlux/1.0 (agent_id={self.config.agent_id})",
        })

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """发送 HTTP 请求（带重试）"""
        url = urljoin(self.config.hub_url + "/", path.lstrip("/"))
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                resp = self._session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    timeout=self.config.request_timeout,
                    stream=stream,
                )
                if resp.status_code == 401:
                    logger.warning("EigenFlux API unauthorized (401)")
                if resp.status_code >= 500:
                    raise requests.HTTPError(f"Server error {resp.status_code}")

                resp.raise_for_status()
                if stream:
                    return {"_stream": resp}
                if not resp.content:
                    return {}
                return resp.json()

            except (requests.RequestException, ValueError) as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    wait = self.config.retry_interval * (2 ** attempt)
                    logger.info(f"EigenFlux API request failed, retrying in {wait:.1f}s: {e}")
                    time.sleep(wait)
                continue

        raise RuntimeError(f"EigenFlux API request failed after {self.config.max_retries} attempts: {last_error}")

    # ========== 认证 API ==========

    def auth_request_login_code(self, email: str) -> Dict[str, Any]:
        """请求发送登录验证码到邮箱"""
        return self._request("POST", "/api/v1/auth/login-code", {"email": email})

    def auth_verify_login_code(self, email: str, code: str) -> Dict[str, Any]:
        """验证登录验证码并获取 token"""
        result = self._request(
            "POST", "/api/v1/auth/verify-login-code",
            {"email": email, "code": code},
        )
        token = result.get("token") or result.get("data", {}).get("token")
        if token:
            self.config.api_token = token
            self._setup_auth()
            self._save_token(token)
        return result

    def _save_token(self, token: str) -> None:
        """保存 token 到本地"""
        try:
            from pathlib import Path
            token_path = Path(self.config.home_dir) / "token"
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(token, encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save eigenflux token: {e}")

    def _load_token(self) -> Optional[str]:
        """从本地加载 token"""
        try:
            from pathlib import Path
            token_path = Path(self.config.home_dir) / "token"
            if token_path.exists():
                return token_path.read_text(encoding="utf-8").strip() or None
        except Exception as e:
            logger.warning(f"Failed to load eigenflux token: {e}")
        return None

    # ========== Agent Profile API ==========

    def register_agent(self, profile: Optional[AgentProfile] = None) -> Dict[str, Any]:
        """注册或更新 Agent 档案"""
        if profile is None:
            profile = AgentProfile(
                agent_id=self.config.agent_id,
                name=self.config.agent_name,
                description=self.config.agent_description,
                capabilities=self.config.agent_capabilities,
            )
        return self._request("POST", "/api/v1/agents/register", profile.to_dict())

    def get_agent_profile(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """获取 Agent 档案"""
        agent_id = agent_id or self.config.agent_id
        return self._request("GET", f"/api/v1/agents/{agent_id}")

    def list_agents(
        self,
        capability: Optional[str] = None,
        tag: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """列出 Agent"""
        params = {"page": page, "page_size": page_size}
        if capability:
            params["capability"] = capability
        if tag:
            params["tag"] = tag
        return self._request("GET", "/api/v1/agents", params=params)

    # ========== 广播 API ==========

    def send_broadcast(self, message: BroadcastMessage) -> BroadcastResponse:
        """发送广播"""
        try:
            data = message.to_dict()
            result = self._request("POST", "/api/v1/broadcasts", data)

            if self.config.log_broadcasts:
                logger.info(
                    f"[EigenFlux] Broadcast sent: id={message.broadcast_id} "
                    f"type={message.broadcast_type.value} summary={message.summary(60)!r}"
                )

            return BroadcastResponse(
                success=True,
                broadcast_id=result.get("broadcast_id", message.broadcast_id),
                message=result.get("message", "Broadcast sent"),
                matched_count=result.get("matched_count", 0),
                estimated_reach=result.get("estimated_reach", 0),
                metadata=result.get("metadata", {}),
            )
        except Exception as e:
            logger.error(f"[EigenFlux] Failed to send broadcast: {e}")
            return BroadcastResponse(
                success=False,
                broadcast_id=message.broadcast_id,
                message=str(e),
                errors=[str(e)],
            )

    def get_broadcast(self, broadcast_id: str) -> Dict[str, Any]:
        """获取单个广播详情"""
        return self._request("GET", f"/api/v1/broadcasts/{broadcast_id}")

    def list_broadcasts(
        self,
        broadcast_type: Optional[str] = None,
        tag: Optional[str] = None,
        agent_id: Optional[str] = None,
        since: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """列出广播"""
        params = {"page": page, "page_size": page_size}
        if broadcast_type:
            params["broadcast_type"] = broadcast_type
        if tag:
            params["tag"] = tag
        if agent_id:
            params["agent_id"] = agent_id
        if since:
            params["since"] = since
        return self._request("GET", "/api/v1/broadcasts", params=params)

    def reply_to_broadcast(
        self,
        broadcast_id: str,
        content: str,
        structured_data: Optional[Dict[str, Any]] = None,
    ) -> BroadcastResponse:
        """回复一条广播"""
        reply = BroadcastMessage(
            content=content,
            agent_id=self.config.agent_id,
            broadcast_type="discussion",
            reply_to=broadcast_id,
            structured_data=structured_data or {},
        )
        return self.send_broadcast(reply)

    # ========== 订阅 API ==========

    def create_subscription(self, subscription: Subscription) -> Dict[str, Any]:
        """创建订阅"""
        subscription.agent_id = self.config.agent_id
        return self._request("POST", "/api/v1/subscriptions", subscription.to_dict())

    def update_subscription(self, subscription: Subscription) -> Dict[str, Any]:
        """更新订阅"""
        return self._request(
            "PUT",
            f"/api/v1/subscriptions/{subscription.subscription_id}",
            subscription.to_dict(),
        )

    def delete_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """删除订阅"""
        return self._request("DELETE", f"/api/v1/subscriptions/{subscription_id}")

    def list_subscriptions(self) -> Dict[str, Any]:
        """列出当前 Agent 的所有订阅"""
        return self._request(
            "GET",
            "/api/v1/subscriptions",
            params={"agent_id": self.config.agent_id},
        )

    # ========== 收件箱 / 匹配 API ==========

    def get_inbox(
        self,
        read: Optional[bool] = None,
        since: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """获取收件箱（匹配到的广播）"""
        params = {"page": page, "page_size": page_size}
        if read is not None:
            params["read"] = read
        if since:
            params["since"] = since
        return self._request("GET", "/api/v1/inbox", params=params)

    def mark_inbox_read(self, message_id: str) -> Dict[str, Any]:
        """标记收件箱消息已读"""
        return self._request("POST", f"/api/v1/inbox/{message_id}/read", {})

    def search_broadcasts(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """搜索广播"""
        data = {
            "query": query,
            "tags": tags or [],
            "page": page,
            "page_size": page_size,
        }
        return self._request("POST", "/api/v1/broadcasts/search", data)

    # ========== 统计 & 健康检查 ==========

    def get_stats(self) -> Dict[str, Any]:
        """获取网络统计"""
        return self._request("GET", "/api/v1/stats/network")

    def get_my_stats(self) -> Dict[str, Any]:
        """获取当前 Agent 的统计"""
        return self._request(
            "GET",
            "/api/v1/stats/agent",
            params={"agent_id": self.config.agent_id},
        )

    def health_check(self) -> bool:
        """Hub 健康检查"""
        try:
            result = self._request("GET", "/api/v1/health")
            return result.get("status") == "ok" or result.get("healthy", False)
        except Exception as e:
            logger.warning(f"[EigenFlux] Health check failed: {e}")
            return False

    # ========== WebSocket 实时通信 ==========

    def add_message_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """添加 WebSocket 消息处理器"""
        self._message_handlers.append(handler)

    def remove_message_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """移除 WebSocket 消息处理器"""
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)

    def _dispatch_message(self, msg: Dict[str, Any]) -> None:
        """分发消息到处理器"""
        for handler in list(self._message_handlers):
            try:
                handler(msg)
            except Exception as e:
                logger.error(f"[EigenFlux] WS handler error: {e}")

    def start_websocket(self) -> bool:
        """启动 WebSocket 连接（异步线程）"""
        if self._ws_running:
            return True

        try:
            import websockets
            import asyncio
        except ImportError:
            logger.warning("[EigenFlux] websockets not installed, WS disabled")
            return False

        def _ws_loop():
            self._ws_running = True
            loop = asyncio.new_event_loop()

            async def _run():
                ws_url = self.config.get_ws_url()
                if self.config.api_token:
                    sep = "&" if "?" in ws_url else "?"
                    ws_url = f"{ws_url}{sep}token={self.config.api_token}"

                logger.info(f"[EigenFlux] Connecting WS: {ws_url}")

                try:
                    async with websockets.connect(
                        ws_url,
                        ping_interval=30,
                        close_timeout=10,
                    ) as ws:
                        self._ws = ws
                        await ws.send(json.dumps({
                            "type": "subscribe",
                            "agent_id": self.config.agent_id,
                            "interests": self.config.default_interests,
                        }))

                        while self._ws_running:
                            try:
                                raw = await ws.recv()
                                msg = json.loads(raw)
                                self._dispatch_message(msg)
                            except websockets.ConnectionClosed:
                                break
                            except json.JSONDecodeError:
                                continue
                            except Exception as e:
                                logger.error(f"[EigenFlux] WS error: {e}")
                except Exception as e:
                    logger.error(f"[EigenFlux] WS connection failed: {e}")
                finally:
                    self._ws_running = False
                    self._ws = None

            try:
                loop.run_until_complete(_run())
            finally:
                loop.close()

        self._ws_thread = threading.Thread(target=_ws_loop, daemon=True)
        self._ws_thread.start()
        return True

    def stop_websocket(self) -> None:
        """停止 WebSocket 连接"""
        self._ws_running = False
        if self._ws:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self._ws.close())
            except Exception:
                pass
            self._ws = None

    # ========== CLI 包装 ==========

    def cli_installed(self) -> bool:
        """检查 CLI 是否已安装"""
        import shutil
        if self.config.cli_path:
            import os
            return os.path.exists(self.config.cli_path)
        return shutil.which("eigenflux") is not None

    def cli_path_resolved(self) -> str:
        """获取 CLI 路径"""
        if self.config.cli_path:
            return self.config.cli_path
        return "eigenflux"

    def cli_run(self, *args: str) -> Dict[str, Any]:
        """运行 eigenflux CLI 命令"""
        import subprocess

        cmd = [self.cli_path_resolved(), *args]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.request_timeout,
                env={"EIGENFLUX_HOME": self.config.home_dir, **__import__("os").environ},
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "eigenflux CLI not found. Install via: "
                         "curl -fsSL https://www.eigenflux.ai/install.sh | bash",
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "CLI command timed out"}

    def cli_broadcast(self, content: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """通过 CLI 发送广播"""
        args = ["broadcast", "--content", content]
        if tags:
            for t in tags:
                args.extend(["--tag", t])
        return self.cli_run(*args)

    def cli_install(self) -> bool:
        """安装 CLI（通过官方安装脚本）"""
        import subprocess
        import platform
        import os

        if platform.system() == "Windows":
            cmd = [
                "powershell", "-Command",
                "irm https://eigenflux.ai/install.ps1 | iex",
            ]
        else:
            cmd = [
                "bash", "-c",
                "curl -fsSL https://www.eigenflux.ai/install.sh | bash",
            ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"[EigenFlux] CLI install failed: {e}")
            return False
