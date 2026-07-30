"""
EigenFlux 配置管理模块

支持从环境变量、配置文件和代码中读取配置。
"""

import os
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path


@dataclass
class EigenFluxConfig:
    """EigenFlux 配置类"""

    # ========== 基础配置 ==========
    # 是否启用 EigenFlux
    enabled: bool = True

    # Hub 地址：公共 Hub 为 https://api.eigenflux.ai
    # 自部署 Hub 可以填自己的地址，如 http://localhost:8080
    hub_url: str = "https://api.eigenflux.ai"

    # WebSocket 地址（用于实时通信）
    ws_url: Optional[str] = None

    # CLI 安装路径（如果使用 CLI 模式）
    cli_path: Optional[str] = None

    # EigenFlux 主目录（存放 token、缓存等）
    home_dir: str = field(default_factory=lambda: str(Path.home() / ".eigenflux"))

    # ========== 认证配置 ==========
    # API Token（从 eigenflux auth login 获取）
    api_token: Optional[str] = None

    # 邮箱（用于 passwordless 登录）
    email: Optional[str] = None

    # ========== Agent 配置 ==========
    # 当前 Agent 的唯一标识
    agent_id: str = field(default_factory=lambda: f"mtscos-agent-{os.getpid()}")

    # Agent 名称
    agent_name: str = "MTSCOS AI Agent"

    # Agent 描述
    agent_description: str = "MTSCOS 教育 AI 系统集成智能体"

    # Agent 能力标签
    agent_capabilities: List[str] = field(default_factory=lambda: [
        "education", "tutoring", "question_generation",
        "learning_analysis", "exam_management",
    ])

    # ========== 广播配置 ==========
    # 默认广播的可见性：public / private / friends
    default_visibility: str = "public"

    # 广播时是否需要用户确认（隐私保护）
    require_user_confirmation: bool = True

    # 禁止广播的敏感字段（隐私保护）
    sensitive_fields: List[str] = field(default_factory=lambda: [
        "password", "token", "cookie", "session",
        "phone", "email", "id_card", "address",
    ])

    # ========== 订阅配置 ==========
    # 默认订阅的兴趣标签
    default_interests: List[str] = field(default_factory=lambda: [
        "ai_education", "edtech", "learning_science",
        "educational_technology", "k12",
    ])

    # 订阅轮询间隔（秒），不使用 WebSocket 时生效
    poll_interval: int = 30

    # 最大缓存的消息数
    max_cached_messages: int = 1000

    # ========== 匹配配置 ==========
    # 匹配阈值（0-1，分数高于此值才推送）
    match_threshold: float = 0.6

    # 是否启用本地匹配（降低网络请求）
    enable_local_matching: bool = True

    # ========== 网络配置 ==========
    # 请求超时（秒）
    request_timeout: int = 30

    # 重试次数
    max_retries: int = 3

    # 重试间隔（秒）
    retry_interval: float = 1.0

    # 代理设置
    proxy: Optional[str] = None

    # ========== 日志配置 ==========
    # 日志级别
    log_level: str = "INFO"

    # 是否记录广播内容
    log_broadcasts: bool = True

    # 是否记录匹配过程
    log_matching: bool = False

    # ========== Hub 自部署配置 ==========
    # 是否以本地 Hub 模式运行
    local_hub_mode: bool = False

    # 本地 Hub 端口
    local_hub_port: int = 8080

    # 本地 Hub 数据目录
    local_hub_data_dir: str = field(
        default_factory=lambda: str(Path.home() / ".eigenflux" / "hub-data")
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EigenFluxConfig":
        valid_fields = {f for f in cls.__dataclass_fields__.keys()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    @classmethod
    def from_env(cls) -> "EigenFluxConfig":
        """从环境变量加载配置"""
        config = cls()

        env_mappings = {
            "EIGENFLUX_ENABLED": ("enabled", lambda v: v.lower() in ("1", "true", "yes")),
            "EIGENFLUX_HUB_URL": ("hub_url", str),
            "EIGENFLUX_WS_URL": ("ws_url", str),
            "EIGENFLUX_CLI_PATH": ("cli_path", str),
            "EIGENFLUX_HOME": ("home_dir", str),
            "EIGENFLUX_API_TOKEN": ("api_token", str),
            "EIGENFLUX_EMAIL": ("email", str),
            "EIGENFLUX_AGENT_ID": ("agent_id", str),
            "EIGENFLUX_AGENT_NAME": ("agent_name", str),
            "EIGENFLUX_AGENT_DESC": ("agent_description", str),
            "EIGENFLUX_VISIBILITY": ("default_visibility", str),
            "EIGENFLUX_REQUIRE_CONFIRM": ("require_user_confirmation", lambda v: v.lower() in ("1", "true", "yes")),
            "EIGENFLUX_POLL_INTERVAL": ("poll_interval", int),
            "EIGENFLUX_MATCH_THRESHOLD": ("match_threshold", float),
            "EIGENFLUX_LOCAL_MATCH": ("enable_local_matching", lambda v: v.lower() in ("1", "true", "yes")),
            "EIGENFLUX_TIMEOUT": ("request_timeout", int),
            "EIGENFLUX_PROXY": ("proxy", str),
            "EIGENFLUX_LOG_LEVEL": ("log_level", str),
            "EIGENFLUX_LOCAL_HUB": ("local_hub_mode", lambda v: v.lower() in ("1", "true", "yes")),
            "EIGENFLUX_LOCAL_HUB_PORT": ("local_hub_port", int),
            "EIGENFLUX_LOCAL_HUB_DATA": ("local_hub_data_dir", str),
        }

        for env_key, (attr, converter) in env_mappings.items():
            value = os.environ.get(env_key)
            if value is not None:
                try:
                    setattr(config, attr, converter(value))
                except (ValueError, TypeError):
                    pass

        # 解析列表类型
        list_fields = {
            "EIGENFLUX_CAPABILITIES": "agent_capabilities",
            "EIGENFLUX_INTERESTS": "default_interests",
            "EIGENFLUX_SENSITIVE_FIELDS": "sensitive_fields",
        }
        for env_key, attr in list_fields.items():
            value = os.environ.get(env_key)
            if value:
                items = [s.strip() for s in value.split(",") if s.strip()]
                if items:
                    setattr(config, attr, items)

        return config

    @classmethod
    def from_file(cls, path: str) -> "EigenFluxConfig":
        """从 JSON 配置文件加载"""
        file_path = Path(path)
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        return cls()

    def save_to_file(self, path: str) -> None:
        """保存配置到 JSON 文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def ensure_dirs(self) -> None:
        """确保需要的目录存在"""
        Path(self.home_dir).mkdir(parents=True, exist_ok=True)
        if self.local_hub_mode:
            Path(self.local_hub_data_dir).mkdir(parents=True, exist_ok=True)

    def get_ws_url(self) -> str:
        """获取 WebSocket 地址"""
        if self.ws_url:
            return self.ws_url
        # 根据 hub_url 推断
        if self.hub_url.startswith("https://"):
            return "wss://" + self.hub_url[8:] + "/ws"
        elif self.hub_url.startswith("http://"):
            return "ws://" + self.hub_url[7:] + "/ws"
        return self.hub_url + "/ws"


# 全局单例
_config_instance: Optional[EigenFluxConfig] = None


def get_config(**overrides) -> EigenFluxConfig:
    """获取全局配置单例

    Args:
        **overrides: 覆盖的配置项
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = EigenFluxConfig.from_env()

    if overrides:
        for k, v in overrides.items():
            if hasattr(_config_instance, k):
                setattr(_config_instance, k, v)

    _config_instance.ensure_dirs()
    return _config_instance
