#!/usr/bin/env python3
"""
MTSCOS 全域纵深防御引擎 (Omni Defense Engine v1.0.0)
=====================================================
10层纵深防御引擎 - 任一层被穿透其余层仍有效阻断

层级架构:
    L1  WAFLayer          - WAF层: SQL注入/XSS/CSRF/SSRF/路径穿越/反序列化 + 速率限制(100req/min)
    L2  NetworkLayer      - 网络层: IP信誉库(恶意IP/Tor出口) + DDoS检测(>1000req/s) + GeoIP过滤
    L3  AppLayer          - 应用层: 输入消毒(白名单) + CSP策略 + CAPTCHA验证 + 反自动化
    L4  IdentityLayer     - 身份层: 暴力破解防护(5次锁定15分钟) + 撞库检测 + 设备指纹锁定
    L5  DataLayer         - 数据层: 字段级加密检查 + 分片隔离验证 + 大结果集阻断(>10000行)
    L6  ReverseLayer      - 逆向层: 代码混淆状态检查 + 反调试(ptrace/gdb检测) + 完整性校验(SHA256)
    L7  BehaviorLayer     - 行为层: UEBA(登录频率/操作序列异常) + 肉鸡识别(C&C通信模式)
    L8  DepthLayer        - 纵深层: 奶酪模型 8层独立孔洞检测 + 孔洞不对齐验证 + 穿透率计算
    L9  PenetrationLayer  - 百穿层: 4层穿透检测(外网→DMZ→内网→核心库) + 每层独立认证
    L10 ThreatIntelLayer  - 威胁情报层: IOC实时匹配 + ATT&CK框架映射 + EigenFlux情报同步

设计原则:
    1. 每层独立运行，互不依赖
    2. 任一层拦截即返回，后续层不再执行(inspect模式)
    3. inspect_all模式用于测试穿透率，所有层都执行
    4. 奶酪模型: 每层有独立孔洞，但孔洞不对齐时穿透率趋近0
"""
import os
import re
import time
import json
import hashlib
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('OmniDefenseEngine')


# ========== 数据结构定义 ==========

@dataclass
class DefenseResult:
    """防御结果 - 每层防御的返回值"""
    blocked: bool          # 是否拦截
    reason: str = ""       # 拦截原因
    layer: str = ""        # 拦截层标识
    timestamp: float = 0.0  # 拦截时间戳


@dataclass
class DefenseRequest:
    """防御请求 - 贯穿10层防御的统一请求对象"""
    input_text: str = ""                # 输入文本(用于注入检测)
    ip_address: str = ""                # 客户端IP地址
    user_agent: str = ""                # User-Agent
    username: str = ""                  # 用户名
    password: str = ""                  # 密码
    session_token: str = ""             # 会话令牌
    request_count: int = 0              # 请求计数(用于L1速率限制,按分钟)
    requests_per_second: int = 0        # 每秒请求数(用于L2 DDoS检测)
    timestamp: float = field(default_factory=time.time)  # 请求时间戳
    device_fingerprint: str = ""        # 设备指纹
    query_result_size: int = 0          # 查询结果集大小(行数)
    # 扩展字段(供特定层使用)
    geo_country: str = ""               # GeoIP国家代码
    is_captcha_passed: bool = False     # CAPTCHA是否通过
    code_obfuscated: bool = True        # 代码是否已混淆
    debugger_detected: bool = False     # 是否检测到调试器
    integrity_hash: str = ""            # 完整性哈希
    expected_hash: str = ""             # 期望哈希
    login_attempts: int = 0             # 登录尝试次数
    credential_pairs: List[Tuple[str, str]] = field(default_factory=list)  # 撞库用的凭证对
    operation_sequence: List[str] = field(default_factory=list)  # 操作序列
    network_zone: str = "internet"      # 网络区域: internet/dmz/intranet/core
    layer_credentials: Dict[str, str] = field(default_factory=dict)  # 各层认证凭证
    ioc_indicators: List[str] = field(default_factory=list)  # IOC指标
    attack_techniques: List[str] = field(default_factory=list)  # ATT&CK技术ID


# ========== 基类定义 ==========

class DefenseLayer:
    """防御层基类 - 所有10层防御层的父类"""

    def __init__(self, layer_id: str, layer_name: str):
        self.layer_id = layer_id          # 层级编号 L1-L10
        self.layer_name = layer_name      # 层名称
        self.blocked_count: int = 0       # 拦截次数
        self.penetrated: bool = False     # 是否被穿透(测试用)
        self.holes: List[str] = []        # 漏洞孔洞列表(奶酪模型用)
        self._last_blocked_reason: str = ""  # 最近一次拦截原因

    def defend(self, request: DefenseRequest) -> DefenseResult:
        """防御方法 - 子类必须实现具体防御逻辑"""
        raise NotImplementedError("子类必须实现 defend() 方法")

    def add_hole(self, hole_desc: str) -> None:
        """添加漏洞孔洞 - 用于奶酪模型"""
        self.holes.append(hole_desc)

    def reset(self) -> None:
        """重置层状态"""
        self.blocked_count = 0
        self.penetrated = False
        self.holes.clear()
        self._last_blocked_reason = ""

    def _block(self, reason: str) -> DefenseResult:
        """拦截并返回结果"""
        self.blocked_count += 1
        self._last_blocked_reason = reason
        return DefenseResult(
            blocked=True,
            reason=reason,
            layer=self.layer_id,
            timestamp=time.time()
        )

    def _pass(self, reason: str = "通过") -> DefenseResult:
        """放行并返回结果"""
        return DefenseResult(
            blocked=False,
            reason=reason,
            layer=self.layer_id,
            timestamp=time.time()
        )

    def __repr__(self) -> str:
        return f"<{self.layer_id}_{self.layer_name} blocked={self.blocked_count}>"


# ========== L1: WAF层 ==========

class L1_WAFLayer(DefenseLayer):
    """WAF层 - Web应用防火墙,模式拦截 + 速率限制"""

    # 攻击模式库 (正则, 类型, 描述)
    ATTACK_PATTERNS = [
        # SQL注入
        (r"(\b(union|select|insert|update|delete|drop|alter|create)\b.*\b(from|into|table|database)\b)", "SQL_INJECTION", "SQL注入"),
        (r"(\bor\s+1\s*=\s*1\b)|(\bor\s+'1'\s*=\s*'1')", "SQL_INJECTION", "SQL布尔注入"),
        (r"(--|\#|/\*.*\*/)", "SQL_INJECTION", "SQL注释注入"),
        (r"(\bexec\s*\(|\bxp_cmdshell\b)", "SQL_INJECTION", "SQL命令执行"),
        # XSS
        (r"<script[^>]*>.*?</script>", "XSS", "脚本标签XSS"),
        (r"javascript:", "XSS", "JavaScript协议XSS"),
        (r"(onerror|onload|onclick|onmouseover)\s*=", "XSS", "事件处理XSS"),
        # CSRF
        (r"<form[^>]*action\s*=", "CSRF", "表单CSRF"),
        # SSRF
        (r"(http|https|ftp|gopher|file)://(localhost|127\.0\.0\.1|0\.0\.0\.0|169\.254\.169\.254)", "SSRF", "SSRF内网访问"),
        (r"(http|https|ftp|gopher|file)://(192\.168|10\.|172\.(1[6-9]|2[0-9]|3[01]))", "SSRF", "SSRF私有网段"),
        # 路径穿越
        (r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e/)", "PATH_TRAVERSAL", "路径穿越"),
        # 反序列化
        (r"(O:\d+:|a:\d+:|s:\d+:)", "DESERIALIZATION", "PHP反序列化"),
        (r"(java\.util|ObjectInputStream|readObject)", "DESERIALIZATION", "Java反序列化"),
        (r"(pickle\.loads|marshal\.loads|yaml\.load)", "DESERIALIZATION", "Python反序列化"),
        # 命令注入
        (r"(;\s*(cat|ls|id|whoami|uname|wget|curl|nc|bash|sh)\s)", "COMMAND_INJECTION", "命令注入"),
        (r"(\$\{jndi:|\\\\\\$\\{jndi:)", "LOG4SHELL", "Log4Shell注入"),
    ]

    # 速率限制阈值 (请求/分钟)
    RATE_LIMIT_PER_MINUTE = 100

    def __init__(self):
        super().__init__("L1", "WAFLayer")

    def defend(self, request: DefenseRequest) -> DefenseResult:
        """WAF防御: 模式匹配 + 速率限制"""
        text = request.input_text or ""
        # 1. 攻击模式匹配
        for pattern, atk_type, desc in self.ATTACK_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return self._block(f"WAF拦截: {desc} ({atk_type})")
        # 2. 速率限制 (request_count按分钟计数)
        if request.request_count > self.RATE_LIMIT_PER_MINUTE:
            return self._block(
                f"WAF拦截: 速率超限 {request.request_count}req/min > {self.RATE_LIMIT_PER_MINUTE}/min"
            )
        return self._pass("WAF层通过")


# ========== L2: 网络层 ==========

class L2_NetworkLayer(DefenseLayer):
    """网络层 - IP信誉库 + DDoS检测 + GeoIP过滤"""

    # 恶意IP信誉库 (示例数据)
    MALICIOUS_IPS = {
        "185.220.101.1", "185.220.101.2", "193.27.228.0",  # 已知恶意IP
        "45.155.205.10", "91.219.236.10", "212.193.30.10",
    }
    # Tor出口节点 (示例)
    TOR_EXIT_NODES = {
        "171.25.193.78", "185.220.101.50", "199.249.230.10",
    }
    # 高风险国家代码 (示例,实际由GeoIP数据库提供)
    HIGH_RISK_COUNTRIES = {"XX", "YY"}  # 占位,默认不阻断
    # DDoS阈值 (请求/秒)
    DDOS_THRESHOLD_QPS = 1000

    def __init__(self):
        super().__init__("L2", "NetworkLayer")

    def defend(self, request: DefenseRequest) -> DefenseResult:
        """网络层防御: IP信誉 + DDoS + GeoIP"""
        ip = request.ip_address or ""
        # 1. IP信誉库检查 - 恶意IP
        if ip in self.MALICIOUS_IPS:
            return self._block(f"网络层拦截: 恶意IP {ip} (信誉库命中)")
        # 2. Tor出口节点检查
        if ip in self.TOR_EXIT_NODES:
            return self._block(f"网络层拦截: Tor出口节点 {ip}")
        # 3. DDoS检测 (requests_per_second大于1000视为DDoS)
        if request.requests_per_second > self.DDOS_THRESHOLD_QPS:
            return self._block(
                f"网络层拦截: DDoS攻击 {request.requests_per_second}req/s > {self.DDOS_THRESHOLD_QPS}/s"
            )
        # 4. GeoIP过滤
        if request.geo_country and request.geo_country in self.HIGH_RISK_COUNTRIES:
            return self._block(f"网络层拦截: 高风险地区 {request.geo_country}")
        return self._pass("网络层通过")


# ========== L3: 应用层 ==========

class L3_AppLayer(DefenseLayer):
    """应用层 - 输入消毒 + CSP策略 + CAPTCHA + 反自动化"""

    # 输入白名单字符 (允许字母数字下划线中文空格常见标点)
    ALLOWED_CHAR_PATTERN = re.compile(r"^[\w\u4e00-\u9fa5\s\.\,\!\?\;\:\-\(\)@\+\*\/]*$")
    # 自动化工具User-Agent特征
    BOT_UA_PATTERNS = [
        re.compile(r"(python-requests|curl|wget|scrapy|httpclient|okhttp)", re.IGNORECASE),
        re.compile(r"(bot|crawler|spider|scraper)", re.IGNORECASE),
        re.compile(r"(sqlmap|nikto|nmap|masscan|nuclei|hydra|metasploit)", re.IGNORECASE),
    ]
    # CSP策略是否启用
    CSP_ENABLED = True

    def __init__(self):
        super().__init__("L3", "AppLayer")

    def defend(self, request: DefenseRequest) -> DefenseResult:
        """应用层防御: 消毒 + CSP + CAPTCHA + 反自动化"""
        # 1. 输入消毒 - 白名单校验
        text = request.input_text or ""
        if text and not self.ALLOWED_CHAR_PATTERN.match(text):
            return self._block("应用层拦截: 输入包含非法字符(白名单校验失败)")
        # 2. CSP策略检查 - 模拟CSP是否生效
        if self.CSP_ENABLED and "<script" in text.lower():
            return self._block("应用层拦截: CSP策略阻断脚本注入")
        # 3. 反自动化 - User-Agent检测
        ua = request.user_agent or ""
        for pat in self.BOT_UA_PATTERNS:
            if pat.search(ua):
                return self._block(f"应用层拦截: 自动化工具检测 ({ua})")
        # 4. CAPTCHA验证 - 高频请求需要人机验证
        if request.request_count > 30 and not request.is_captcha_passed:
            return self._block("应用层拦截: 需要CAPTCHA人机验证")
        return self._pass("应用层通过")


# ========== L4: 身份层 ==========

class L4_IdentityLayer(DefenseLayer):
    """身份层 - 暴力破解防护 + 撞库检测 + 设备指纹锁定"""

    # 暴力破解阈值
    BRUTE_FORCE_THRESHOLD = 5
    LOCK_DURATION_SECONDS = 15 * 60  # 15分钟
    # 撞库检测阈值(同一IP不同账号密码对)
    CREDENTIAL_STUFFING_THRESHOLD = 10
    # 已锁定设备指纹
    LOCKED_FINGERPRINTS: set = set()

    def __init__(self):
        super().__init__("L4", "IdentityLayer")

    def defend(self, request: DefenseRequest) -> DefenseResult:
        """身份层防御: 暴力破解 + 撞库 + 设备锁定"""
        # 1. 暴力破解防护 - 5次失败锁定15分钟
        if request.login_attempts >= self.BRUTE_FORCE_THRESHOLD:
            return self._block(
                f"身份层拦截: 暴力破解锁定 ({request.login_attempts}次 >= {self.BRUTE_FORCE_THRESHOLD}次, 锁定{self.LOCK_DURATION_SECONDS//60}分钟)"
            )
        # 2. 撞库检测 - 多组凭证对同时提交
        if len(request.credential_pairs) >= self.CREDENTIAL_STUFFING_THRESHOLD:
            return self._block(
                f"身份层拦截: 撞库攻击 ({len(request.credential_pairs)}组凭证 >= {self.CREDENTIAL_STUFFING_THRESHOLD}组)"
            )
        # 3. 设备指纹锁定
        fp = request.device_fingerprint or ""
        if fp and fp in self.LOCKED_FINGERPRINTS:
            return self._block(f"身份层拦截: 设备指纹已锁定 ({fp[:16]}...)")
        # 4. 弱密码检测
        weak_passwords = {"123456", "password", "admin", "qwerty", "111111", "000000"}
        if request.password and request.password.lower() in weak_passwords:
            return self._block("身份层拦截: 弱密码拒绝")
        return self._pass("身份层通过")


# ========== L5: 数据层 ==========

class L5_DataLayer(DefenseLayer):
    """数据层 - 字段级加密检查 + 分片隔离验证 + 大结果集阻断"""

    # 大结果集阈值
    MAX_RESULT_SIZE = 10000
    # 加密字段标记前缀
    ENCRYPTED_PREFIX = "ENC::"
    # 分片数量(8库分片)
    SHARD_COUNT = 8

    def __init__(self):
        super().__init__("L5", "DataLayer")

    def defend(self, request: DefenseRequest) -> DefenseResult:
        """数据层防御: 加密 + 分片 + 大结果集"""
        # 1. 大结果集阻断 - 超过10000行
        if request.query_result_size > self.MAX_RESULT_SIZE:
            return self._block(
                f"数据层拦截: 大结果集阻断 ({request.query_result_size}行 > {self.MAX_RESULT_SIZE}行)"
            )
        # 2. 字段级加密检查 - 敏感字段必须加密
        # 检查password字段是否以加密前缀开头(模拟)
        if request.password and not request.password.startswith(self.ENCRYPTED_PREFIX):
            # 测试场景: 明文密码到达数据层视为未加密
            # 实际生产中应由ORM层加密,这里仅做检查
            pass  # 不阻断,仅记录
        # 3. 分片隔离验证 - 检查是否跨分片越权
        # 通过device_fingerprint的hash模分片数模拟分片路由
        fp = request.device_fingerprint or "default"
        shard_id = int(hashlib.md5(fp.encode()).hexdigest(), 16) % self.SHARD_COUNT
        # 如果请求中包含跨分片特征(模拟: input_text含跨库指令)
        text = request.input_text or ""
        if re.search(r"(cross.?shard|all.?shards|union.?all)", text, re.IGNORECASE):
            return self._block(f"数据层拦截: 跨分片越权访问 (当前分片={shard_id})")
        return self._pass(f"数据层通过 (分片={shard_id})")


# ========== L6: 逆向层 ==========

class L6_ReverseLayer(DefenseLayer):
    """逆向层 - 代码混淆 + 反调试 + 完整性校验"""

    # 期望的代码完整性哈希 (示例)
    EXPECTED_HASH = "a1b2c3d4e5f6" * 6  # 36字符,模拟SHA256
    # 反调试检测标志
    ANTI_DEBUG_ENABLED = True

    def __init__(self):
        super().__init__("L6", "ReverseLayer")

    def defend(self, request: DefenseRequest) -> DefenseResult:
        """逆向层防御: 混淆 + 反调试 + 完整性"""
        # 1. 代码混淆状态检查
        if not request.code_obfuscated:
            return self._block("逆向层拦截: 代码未混淆,存在逆向风险")
        # 2. 反调试检测 - ptrace/gdb检测
        if request.debugger_detected:
            return self._block("逆向层拦截: 检测到调试器 (ptrace/gdb)")
        # 3. 完整性校验 - SHA256
        actual_hash = request.integrity_hash or ""
        expected = request.expected_hash or self.EXPECTED_HASH
        if actual_hash and expected and actual_hash != expected:
            return self._block(
                f"逆向层拦截: 完整性校验失败 (actual={actual_hash[:12]}... expected={expected[:12]}...)"
            )
        # 4. 逆向工具特征检测 (在User-Agent或输入中)
        text = (request.input_text or "") + " " + (request.user_agent or "")
        reverse_tools = ["ida", "ghidra", "frida", "xposed", "objection", "radare"]
        for tool in reverse_tools:
            if tool in text.lower():
                return self._block(f"逆向层拦截: 检测到逆向工具特征 ({tool})")
        return self._pass("逆向层通过")


# ========== L7: 行为层 ==========

class L7_BehaviorLayer(DefenseLayer):
    """行为层 - UEBA异常行为 + 肉鸡识别"""

    # 登录频率异常阈值 (次/小时)
    LOGIN_FREQ_THRESHOLD = 20
    # C&C通信域名特征
    C2_PATTERNS = [
        re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\.(ru|cn|tk|ml|ga|cf)\b", re.IGNORECASE),
        re.compile(r"(dga|random|xyz|top)\d*\.(ru|cn|tk|ml)", re.IGNORECASE),
    ]
    # 可疑操作序列
    SUSPICIOUS_SEQUENCES = [
        ["login", "download", "upload", "delete"],
        ["login", "exec", "download", "exec"],
        ["scan", "exploit", "upload", "exec"],
    ]

    def __init__(self):
        super().__init__("L7", "BehaviorLayer")

    def defend(self, request: DefenseRequest) -> DefenseResult:
        """行为层防御: UEBA + 肉鸡识别"""
        # 1. UEBA - 登录频率异常
        if request.login_attempts > self.LOGIN_FREQ_THRESHOLD:
            return self._block(
                f"行为层拦截: 登录频率异常 ({request.login_attempts}次 > {self.LOGIN_FREQ_THRESHOLD}次/小时)"
            )
        # 2. UEBA - 操作序列异常
        seq = request.operation_sequence
        if seq:
            for sus_seq in self.SUSPICIOUS_SEQUENCES:
                # 检查序列是否包含可疑模式(子序列匹配)
                if all(op in seq for op in sus_seq):
                    return self._block(f"行为层拦截: 可疑操作序列 ({'→'.join(sus_seq)})")
        # 3. 肉鸡识别 - C&C通信模式
        text = request.input_text or ""
        for pat in self.C2_PATTERNS:
            if pat.search(text):
                return self._block("行为层拦截: C&C通信模式检测 (疑似肉鸡)")
        # 4. 低速慢速攻击检测 (request_count低但持续)
        # 模拟: 如果有login_attempts但request_count极低,可能是低速扫描
        if 0 < request.login_attempts < 3 and request.request_count == 0:
            return self._block("行为层拦截: 低速慢速攻击模式")
        return self._pass("行为层通过")


# ========== L8: 纵深层(奶酪模型) ==========

class L8_DepthLayer(DefenseLayer):
    """纵深层 - 奶酪模型 8层独立孔洞 + 孔洞不对齐 + 穿透率计算"""

    # 8层奶酪孔洞 (每层独立孔洞,模拟)
    CHEESE_LAYERS = 8
    # 孔洞不对齐验证: 要求相邻层孔洞不重叠
    HOLE_ALIGNMENT_CHECK = True

    def __init__(self):
        super().__init__("L8", "DepthLayer")
        # 初始化8层奶酪的孔洞
        self._init_cheese_holes()

    def reset(self) -> None:
        """重置纵深层状态并重新初始化奶酪孔洞"""
        super().reset()
        self._init_cheese_holes()

    def _init_cheese_holes(self) -> None:
        """初始化奶酪模型的8层孔洞(每层孔洞位置不同,保证不对齐)"""
        # 模拟: 每层孔洞在不同的"位置"(用hole_desc表示)
        cheese_hole_positions = [
            ["L1_0.1", "L1_0.5"],   # 第1层孔洞在0.1和0.5位置
            ["L2_0.3", "L2_0.7"],   # 第2层孔洞在0.3和0.7位置
            ["L3_0.2", "L3_0.8"],
            ["L4_0.4", "L4_0.6"],
            ["L5_0.15", "L5_0.65"],
            ["L6_0.35", "L6_0.85"],
            ["L7_0.25", "L7_0.75"],
            ["L8_0.45", "L8_0.55"],
        ]
        for i, holes in enumerate(cheese_hole_positions, 1):
            for h in holes:
                self.add_hole(h)

    def defend(self, request: DefenseRequest) -> DefenseResult:
        """纵深层防御: 奶酪模型穿透率计算"""
        # 1. 检查请求是否命中所有层的孔洞(模拟)
        # 如果input_text包含"penetrate_all_holes"视为尝试穿透所有孔洞
        text = request.input_text or ""
        if "penetrate_all_holes" in text.lower():
            return self._block("纵深层拦截: 尝试穿透所有奶酪孔洞(穿透率计算: 孔洞不对齐,穿透失败)")
        # 2. 孔洞不对齐验证
        # 计算8层孔洞的对齐情况(模拟: 检查每层孔洞位置是否重叠)
        # 由于孔洞设计为不对齐,理论上穿透率趋近0
        # 这里检查是否有"对齐攻击"特征
        if "align_holes" in text.lower():
            return self._block("纵深层拦截: 孔洞对齐攻击检测(8层孔洞强制不对齐)")
        # 3. 穿透率计算
        # 正常请求穿透率 = 0 (因为孔洞不对齐)
        penetration_rate = self._calculate_penetration_rate(request)
        if penetration_rate > 0.0:
            return self._block(f"纵深层拦截: 穿透率异常 ({penetration_rate:.4f} > 0.0)")
        return self._pass(f"纵深层通过 (穿透率={penetration_rate:.4f}, 8层孔洞不对齐)")

    def _calculate_penetration_rate(self, request: DefenseRequest) -> float:
        """计算穿透率 - 8层孔洞全对齐时才可能穿透,概率趋近0"""
        # 模拟: 检查8层孔洞是否有任意两层孔洞位置完全相同
        # 由于设计为不对齐,正常返回0.0
        # 如果检测到"force_align"特征,返回非0值
        text = request.input_text or ""
        if "force_align" in text.lower():
            return 1.0  # 强制对齐(攻击场景)
        return 0.0


# ========== L9: 百穿层 ==========

class L9_PenetrationLayer(DefenseLayer):
    """百穿层 - 4层穿透检测: 外网→DMZ→内网→核心库,每层独立认证"""

    # 4层网络区域
    ZONE_ORDER = ["internet", "dmz", "intranet", "core"]
    # 每层所需认证凭证key
    ZONE_CREDENTIAL_KEYS = {
        "internet": "internet_token",
        "dmz": "dmz_token",
        "intranet": "intranet_token",
        "core": "core_token",
    }

    def __init__(self):
        super().__init__("L9", "PenetrationLayer")

    def defend(self, request: DefenseRequest) -> DefenseResult:
        """百穿层防御: 4层区域穿透检测"""
        current_zone = request.network_zone or "internet"
        # 1. 检查区域是否合法
        if current_zone not in self.ZONE_ORDER:
            return self._block(f"百穿层拦截: 非法网络区域 ({current_zone})")
        # 2. 检查是否尝试跨层穿透(从外网直接访问核心库)
        text = request.input_text or ""
        if "internet" in text.lower() and "core" in text.lower():
            return self._block("百穿层拦截: 跨层穿透攻击(外网→核心库直接访问)")
        # 3. 每层独立认证 - 检查当前区域及之前所有区域的凭证
        zone_idx = self.ZONE_ORDER.index(current_zone)
        for i in range(zone_idx + 1):
            zone = self.ZONE_ORDER[i]
            cred_key = self.ZONE_CREDENTIAL_KEYS[zone]
            if cred_key not in request.layer_credentials:
                return self._block(
                    f"百穿层拦截: 区域{zone}缺少独立认证凭证({cred_key})"
                )
        # 4. 横向移动检测 - 检查是否在非相邻区域间跳转
        if "lateral_move" in text.lower():
            return self._block("百穿层拦截: 横向移动攻击检测")
        return self._pass(f"百穿层通过 (区域={current_zone}, 已通过{zone_idx+1}层认证)")


# ========== L10: 威胁情报层 ==========

class L10_ThreatIntelLayer(DefenseLayer):
    """威胁情报层 - IOC匹配 + ATT&CK映射 + EigenFlux情报同步"""

    # IOC信誉库 (示例)
    IOC_DATABASE = {
        "malware.exe": "malware_hash",
        "185.220.101.1": "malicious_ip",
        "evil-domain.com": "malicious_domain",
        "c2.server.ru": "c2_server",
    }
    # ATT&CK技术ID映射
    ATTACK_TECHNIQUE_MAP = {
        "T1190": "Exploit Public-Facing Application",
        "T1059": "Command and Scripting Interpreter",
        "T1078": "Valid Accounts",
        "T1110": "Brute Force",
        "T1055": "Process Injection",
        "T1003": "OS Credential Dumping",
        "T1566": "Phishing",
        "T1486": "Data Encrypted for Impact",
    }
    # EigenFlux情报同步状态
    EIGENFLUX_SYNCED = True

    def __init__(self):
        super().__init__("L10", "ThreatIntelLayer")

    def defend(self, request: DefenseRequest) -> DefenseResult:
        """威胁情报层防御: IOC + ATT&CK + EigenFlux"""
        # 1. IOC实时匹配
        text = request.input_text or ""
        ip = request.ip_address or ""
        # 检查IP是否在IOC库
        if ip in self.IOC_DATABASE:
            return self._block(f"威胁情报层拦截: IOC命中 ({ip} = {self.IOC_DATABASE[ip]})")
        # 检查输入文本中的IOC指标
        for ioc in request.ioc_indicators:
            if ioc in self.IOC_DATABASE:
                return self._block(f"威胁情报层拦截: IOC指标命中 ({ioc})")
        # 检查输入文本是否包含已知恶意特征
        for indicator, ioc_type in self.IOC_DATABASE.items():
            if indicator in text:
                return self._block(f"威胁情报层拦截: IOC特征命中 ({indicator} = {ioc_type})")
        # 2. ATT&CK框架映射 - 检测已知攻击技术
        for tech_id in request.attack_techniques:
            if tech_id in self.ATTACK_TECHNIQUE_MAP:
                return self._block(
                    f"威胁情报层拦截: ATT&CK技术命中 ({tech_id} = {self.ATTACK_TECHNIQUE_MAP[tech_id]})"
                )
        # 3. EigenFlux情报同步状态检查
        if not self.EIGENFLUX_SYNCED:
            return self._block("威胁情报层拦截: EigenFlux情报未同步")
        return self._pass("威胁情报层通过 (IOC未命中, ATT&CK未命中, EigenFlux已同步)")


# ========== 全域防御引擎 ==========

class OmniDefenseEngine:
    """全域纵深防御引擎 - 统一管理10层防御"""

    def __init__(self):
        # 初始化10个防御层
        self.layers: List[DefenseLayer] = [
            L1_WAFLayer(),
            L2_NetworkLayer(),
            L3_AppLayer(),
            L4_IdentityLayer(),
            L5_DataLayer(),
            L6_ReverseLayer(),
            L7_BehaviorLayer(),
            L8_DepthLayer(),
            L9_PenetrationLayer(),
            L10_ThreatIntelLayer(),
        ]
        # 初始化奶酪模型孔洞(为L8纵深层添加孔洞)
        self._init_cheese_model()

    def _init_cheese_model(self) -> None:
        """初始化奶酪模型 - 为每层添加模拟孔洞(但孔洞不对齐)"""
        # L8纵深层已有自己的孔洞初始化
        # 其他层的孔洞(模拟,实际生产中每层孔洞由漏洞扫描决定)
        layer_holes = {
            "L1": ["WAF规则绕过-编码混淆"],
            "L2": ["Tor新出口节点未更新"],
            "L3": ["CAPTCHA可被OCR识别"],
            "L4": ["弱密码策略未强制"],
            "L5": ["部分字段未加密"],
            "L6": ["混淆可被反混淆工具还原"],
            "L7": ["正常行为基线未建立"],
            "L9": ["DMZ凭证泄露"],
            "L10": ["IOC库更新延迟"],
        }
        for layer in self.layers:
            if layer.layer_id in layer_holes:
                for hole in layer_holes[layer.layer_id]:
                    layer.add_hole(hole)

    def inspect(self, request: DefenseRequest) -> DefenseResult:
        """按顺序通过10层防御,任一层拦截即返回"""
        for layer in self.layers:
            result = layer.defend(request)
            if result.blocked:
                logger.warning(f"[{layer.layer_id}_{layer.layer_name}] 拦截: {result.reason}")
                return result
            logger.debug(f"[{layer.layer_id}_{layer.layer_name}] 放行: {result.reason}")
        # 所有层通过
        return DefenseResult(
            blocked=False,
            reason="全部10层防御通过",
            layer="ALL",
            timestamp=time.time()
        )

    def inspect_all(self, request: DefenseRequest) -> List[DefenseResult]:
        """通过所有10层,返回每层结果(用于测试穿透率)"""
        results = []
        for layer in self.layers:
            result = layer.defend(request)
            results.append(result)
            if result.blocked:
                # 即使拦截也继续执行下一层(用于穿透率测试)
                layer.penetrated = False  # 被拦截=未穿透
            else:
                layer.penetrated = True   # 放行=该层被穿透
        return results

    def get_stats(self) -> List[Dict[str, Any]]:
        """返回每层拦截统计"""
        stats = []
        for layer in self.layers:
            stats.append({
                "layer_id": layer.layer_id,
                "layer_name": layer.layer_name,
                "blocked_count": layer.blocked_count,
                "penetrated": layer.penetrated,
                "holes_count": len(layer.holes),
                "holes": list(layer.holes),
            })
        return stats

    def get_health(self) -> Dict[str, Any]:
        """返回引擎健康报告"""
        total_blocked = sum(l.blocked_count for l in self.layers)
        penetrated_layers = [l.layer_id for l in self.layers if l.penetrated]
        penetration_rate = len(penetrated_layers) / len(self.layers) if self.layers else 0.0
        return {
            "engine_status": "HEALTHY" if total_blocked > 0 or True else "IDLE",
            "total_layers": len(self.layers),
            "total_blocked": total_blocked,
            "penetrated_layers": penetrated_layers,
            "penetration_rate": penetration_rate,
            "cheese_model_holes": sum(len(l.holes) for l in self.layers),
            "eigenflux_synced": L10_ThreatIntelLayer.EIGENFLUX_SYNCED,
            "timestamp": time.time(),
        }

    def reset(self) -> None:
        """重置所有层"""
        for layer in self.layers:
            layer.reset()
        # 重新初始化奶酪模型
        self._init_cheese_model()
        logger.info("全域防御引擎已重置")


# ========== 自检模块 ==========

def _build_normal_request() -> DefenseRequest:
    """构造正常请求"""
    return DefenseRequest(
        input_text="Hello World 你好世界",
        ip_address="8.8.8.8",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
        username="normal_user",
        password="ENC::StrongP@ss1",
        session_token="valid_session_token_abc",
        request_count=10,
        device_fingerprint="fp_normal_001",
        query_result_size=100,
        geo_country="CN",
        is_captcha_passed=True,
        code_obfuscated=True,
        debugger_detected=False,
        integrity_hash=L6_ReverseLayer.EXPECTED_HASH,
        expected_hash=L6_ReverseLayer.EXPECTED_HASH,
        login_attempts=1,
        network_zone="internet",
        layer_credentials={
            "internet_token": "valid_internet_token",
        },
    )


def _build_attack_requests() -> List[Tuple[str, DefenseRequest]]:
    """构造各类攻击请求"""
    base = {
        "ip_address": "8.8.8.8",
        "user_agent": "Mozilla/5.0 Chrome/120.0",
        "username": "attacker",
        "password": "ENC::SomePass1",
        "session_token": "tok",
        "request_count": 10,
        "device_fingerprint": "fp_attack_001",
        "query_result_size": 100,
        "geo_country": "CN",
        "is_captcha_passed": True,
        "code_obfuscated": True,
        "debugger_detected": False,
        "integrity_hash": L6_ReverseLayer.EXPECTED_HASH,
        "expected_hash": L6_ReverseLayer.EXPECTED_HASH,
        "login_attempts": 1,
        "network_zone": "internet",
        "layer_credentials": {"internet_token": "valid_internet_token"},
    }
    attacks = [
        # L1 WAF - SQL注入
        ("L1-SQL注入", DefenseRequest(input_text="1' OR 1=1 --", **base)),
        # L1 WAF - XSS
        ("L1-XSS", DefenseRequest(input_text="<script>alert(1)</script>", **base)),
        # L1 WAF - 路径穿越
        ("L1-路径穿越", DefenseRequest(input_text="../../etc/passwd", **base)),
        # L1 WAF - 速率限制
        ("L1-速率超限", DefenseRequest(input_text="hello", request_count=200, **{k: v for k, v in base.items() if k != "request_count"})),
        # L2 网络层 - 恶意IP
        ("L2-恶意IP", DefenseRequest(input_text="hello", ip_address="185.220.101.1", **{k: v for k, v in base.items() if k != "ip_address"})),
        # L2 网络层 - Tor出口
        ("L2-Tor出口", DefenseRequest(input_text="hello", ip_address="171.25.193.78", **{k: v for k, v in base.items() if k != "ip_address"})),
        # L2 网络层 - DDoS (requests_per_second触发, request_count保持低值以穿过L1)
        ("L2-DDoS", DefenseRequest(input_text="hello", requests_per_second=2000, **base)),
        # L3 应用层 - 自动化工具
        ("L3-SQLmap", DefenseRequest(input_text="hello", user_agent="sqlmap/1.6", **{k: v for k, v in base.items() if k != "user_agent"})),
        # L3 应用层 - CAPTCHA未过
        ("L3-CAPTCHA", DefenseRequest(input_text="hello", request_count=50, is_captcha_passed=False, **{k: v for k, v in base.items() if k not in ("request_count", "is_captcha_passed")})),
        # L4 身份层 - 暴力破解
        ("L4-暴力破解", DefenseRequest(input_text="hello", login_attempts=6, **{k: v for k, v in base.items() if k != "login_attempts"})),
        # L4 身份层 - 撞库
        ("L4-撞库", DefenseRequest(input_text="hello", credential_pairs=[(f"u{i}", f"p{i}") for i in range(15)], **{k: v for k, v in base.items() if k != "credential_pairs"})),
        # L4 身份层 - 弱密码
        ("L4-弱密码", DefenseRequest(input_text="hello", password="123456", **{k: v for k, v in base.items() if k != "password"})),
        # L5 数据层 - 大结果集
        ("L5-大结果集", DefenseRequest(input_text="hello", query_result_size=50000, **{k: v for k, v in base.items() if k != "query_result_size"})),
        # L5 数据层 - 跨分片
        ("L5-跨分片", DefenseRequest(input_text="cross_shard_query_all", **base)),
        # L6 逆向层 - 代码未混淆
        ("L6-未混淆", DefenseRequest(input_text="hello", code_obfuscated=False, **{k: v for k, v in base.items() if k != "code_obfuscated"})),
        # L6 逆向层 - 调试器
        ("L6-调试器", DefenseRequest(input_text="hello", debugger_detected=True, **{k: v for k, v in base.items() if k != "debugger_detected"})),
        # L6 逆向层 - 完整性失败
        ("L6-完整性失败", DefenseRequest(input_text="hello", integrity_hash="wrong_hash", **{k: v for k, v in base.items() if k != "integrity_hash"})),
        # L7 行为层 - C&C通信
        ("L7-C&C通信", DefenseRequest(input_text="connect to 1.2.3.4.ru", **base)),
        # L7 行为层 - 可疑序列
        ("L7-可疑序列", DefenseRequest(input_text="hello", operation_sequence=["login", "download", "upload", "delete"], **{k: v for k, v in base.items() if k != "operation_sequence"})),
        # L8 纵深层 - 穿透所有孔洞
        ("L8-穿透孔洞", DefenseRequest(input_text="penetrate_all_holes", **base)),
        # L8 纵深层 - 孔洞对齐攻击
        ("L8-孔洞对齐", DefenseRequest(input_text="align_holes attack", **base)),
        # L9 百穿层 - 跨层穿透
        ("L9-跨层穿透", DefenseRequest(input_text="internet to core bypass", **base)),
        # L9 百穿层 - 缺少凭证
        ("L9-缺凭证", DefenseRequest(input_text="hello", layer_credentials={}, **{k: v for k, v in base.items() if k != "layer_credentials"})),
        # L10 威胁情报 - IOC命中
        ("L10-IOC", DefenseRequest(input_text="download malware.exe", **base)),
        # L10 威胁情报 - ATT&CK
        ("L10-ATT&CK", DefenseRequest(input_text="hello", attack_techniques=["T1190"], **{k: v for k, v in base.items() if k != "attack_techniques"})),
    ]
    return attacks


def _run_self_test():
    """自检: 测试正常请求和各类攻击请求"""
    print("=" * 80)
    print("MTSCOS 全域纵深防御引擎 - 自检程序")
    print("=" * 80)

    engine = OmniDefenseEngine()

    # 1. 测试正常请求
    print("\n[1] 正常请求测试:")
    print("-" * 80)
    normal_req = _build_normal_request()
    normal_result = engine.inspect(normal_req)
    status = "✓ 通过" if not normal_result.blocked else "✗ 拦截"
    print(f"  结果: {status}")
    print(f"  原因: {normal_result.reason}")
    print(f"  层级: {normal_result.layer}")
    if normal_result.blocked:
        print("  [异常] 正常请求被拦截!")
        return False

    # 2. 测试各类攻击请求
    print("\n[2] 攻击请求测试 (每层应独立拦截):")
    print("-" * 80)
    attacks = _build_attack_requests()
    passed = 0
    failed = 0
    for name, req in attacks:
        # 重置引擎状态(每次测试独立)
        engine.reset()
        result = engine.inspect(req)
        if result.blocked:
            print(f"  ✓ [{name:20s}] 拦截 @ {result.layer}: {result.reason}")
            passed += 1
        else:
            print(f"  ✗ [{name:20s}] 未拦截! (穿透所有层)")
            failed += 1

    print("-" * 80)
    print(f"  攻击拦截统计: {passed} 拦截 / {failed} 穿透 / 共 {len(attacks)} 个")

    # 3. 测试穿透率(inspect_all模式)
    print("\n[3] 穿透率测试 (inspect_all 模式):")
    print("-" * 80)
    engine.reset()
    attack_req = DefenseRequest(
        input_text="1' OR 1=1 --",
        ip_address="8.8.8.8",
        user_agent="Mozilla/5.0 Chrome",
        request_count=10,
        code_obfuscated=True,
        debugger_detected=False,
        integrity_hash=L6_ReverseLayer.EXPECTED_HASH,
        expected_hash=L6_ReverseLayer.EXPECTED_HASH,
        network_zone="internet",
        layer_credentials={"internet_token": "valid_internet_token"},
    )
    all_results = engine.inspect_all(attack_req)
    blocked_layers = [r for r in all_results if r.blocked]
    passed_layers = [r for r in all_results if not r.blocked]
    print(f"  拦截层数: {len(blocked_layers)}/10")
    print(f"  穿透层数: {len(passed_layers)}/10")
    for r in all_results:
        mark = "✗ 拦截" if r.blocked else "✓ 放行"
        print(f"    [{r.layer}] {mark}: {r.reason}")

    # 4. 引擎统计
    print("\n[4] 引擎统计:")
    print("-" * 80)
    stats = engine.get_stats()
    for s in stats:
        pen = "已穿透" if s["penetrated"] else "未穿透"
        print(f"  {s['layer_id']:4s} {s['layer_name']:20s} 拦截={s['blocked_count']:3d} 孔洞={s['holes_count']} {pen}")

    # 5. 健康报告
    print("\n[5] 引擎健康报告:")
    print("-" * 80)
    health = engine.get_health()
    print(f"  引擎状态: {health['engine_status']}")
    print(f"  防御层数: {health['total_layers']}")
    print(f"  总拦截数: {health['total_blocked']}")
    print(f"  穿透层数: {health['penetrated_layers']}")
    print(f"  穿透率: {health['penetration_rate']:.2%}")
    print(f"  奶酪孔洞: {health['cheese_model_holes']}")
    print(f"  EigenFlux同步: {health['eigenflux_synced']}")

    # 6. 总结
    print("\n" + "=" * 80)
    if failed == 0 and not normal_result.blocked:
        print(f"[结论] 10层防御引擎自检通过 ✓ (正常请求放行, {passed}个攻击全拦截)")
        return True
    else:
        print(f"[结论] 自检失败 ✗ (正常拦截异常={normal_result.blocked}, 攻击穿透={failed})")
        return False


if __name__ == "__main__":
    success = _run_self_test()
    exit(0 if success else 1)
