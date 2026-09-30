# -*- coding: utf-8 -*-
"""
攻击模式数据库 (Attack Pattern Database)
========================================
全方位攻击防御系统测试用攻击模式库，定义100种攻击模式，分为10类，每类10种。

类别清单:
    1. injection            注入类攻击
    2. authentication       认证类攻击
    3. network              网络类攻击
    4. reverse_engineering  逆向工程类攻击
    5. botnet               僵尸网络类攻击
    6. penetration          渗透类攻击
    7. cheese_model         芝士模型孔洞类攻击
    8. data_attack          数据类攻击
    9. ai_attack            AI类攻击
    10. social_engineering  社会工程类攻击
"""

from __future__ import annotations

import re
# [unused] from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ============================================================
# 严重性等级枚举
# ============================================================
class Severity(Enum):
    """攻击严重性等级"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ============================================================
# 攻击模式数据类
# ============================================================
@dataclass
class AttackPattern:
    """攻击模式定义

    Attributes:
        id: 攻击模式唯一标识 (格式: <类别缩写>-<序号>, 如 INJ-01)
        name: 攻击名称
        category: 所属类别
        severity: 严重性等级 (LOW/MEDIUM/HIGH/CRITICAL)
        description: 攻击描述
        payload_example: 攻击载荷示例
        detection_regex: 检测正则表达式
        mitre_attack_id: MITRE ATT&CK 技术编号
    """
    id: str
    name: str
    category: str
    severity: Severity
    description: str
    payload_example: str
    detection_regex: str
    mitre_attack_id: str

    def matches(self, input_string: str) -> bool:
        """判断输入字符串是否匹配本攻击模式的检测正则

        Args:
            input_string: 待检测的输入字符串

        Returns:
            是否匹配
        """
        try:
            return re.search(self.detection_regex, input_string, re.IGNORECASE) is not None
        except re.error:
            return False


# ============================================================
# 攻击模式数据库
# ============================================================
class AttackPatternDB:
    """攻击模式数据库

    提供100种攻击模式的查询、匹配功能，用于全方位攻击防御系统测试。
    """

    # ------------------------------------------------------------
    # 100种攻击模式定义
    # ------------------------------------------------------------
    PATTERNS: List[AttackPattern] = [
        # ====================================================
        # 类别 1: injection (注入类攻击) INJ-01 ~ INJ-10
        # ====================================================
        AttackPattern(
            id="INJ-01",
            name="SQL注入",
            category="injection",
            severity=Severity.CRITICAL,
            description="通过构造恶意SQL语句绕过应用验证，非法操作数据库。",
            payload_example="' OR '1'='1' --",
            detection_regex=r"(?i)(\bunion\b\s+\bselect\b|\bor\b\s+['\"]?1['\"]?\s*=\s*['\"]?1|--\s*$|;\s*drop\s+table)",
            mitre_attack_id="T1190",
        ),
        AttackPattern(
            id="INJ-02",
            name="XSS跨站脚本",
            category="injection",
            severity=Severity.HIGH,
            description="向网页注入恶意客户端脚本，窃取用户数据或劫持会话。",
            payload_example="<script>alert('XSS')</script>",
            detection_regex=r"(?i)(<script[^>]*>|javascript:|on(error|load|click|mouseover)\s*=|<img[^>]+src\s*=\s*['\"]?javascript:)",
            mitre_attack_id="T1059.007",
        ),
        AttackPattern(
            id="INJ-03",
            name="命令注入",
            category="injection",
            severity=Severity.CRITICAL,
            description="通过应用接口执行任意操作系统命令。",
            payload_example="; cat /etc/passwd",
            detection_regex=r"(?i)([;&|`$(){}]\s*(cat|ls|id|whoami|uname|wget|curl|nc|bash|sh|cmd|powershell)\b)",
            mitre_attack_id="T1059",
        ),
        AttackPattern(
            id="INJ-04",
            name="LDAP注入",
            category="injection",
            severity=Severity.HIGH,
            description="构造恶意LDAP查询绕过目录服务认证。",
            payload_example="*)(uid=*))(|(uid=*",
            detection_regex=r"(?i)(\*\)\s*\(|\)\(\|\(|\buid=\*\b|\bobjectClass=\*\b)",
            mitre_attack_id="T1190",
        ),
        AttackPattern(
            id="INJ-05",
            name="XPath注入",
            category="injection",
            severity=Severity.HIGH,
            description="通过构造恶意XPath表达式绕过XML数据查询。",
            payload_example="' or '1'='1",
            detection_regex=r"(?i)(\bor\b\s+'?1'?\s*=\s*'?1|//\*|\bcount\(/|/text\(\))",
            mitre_attack_id="T1190",
        ),
        AttackPattern(
            id="INJ-06",
            name="模板注入",
            category="injection",
            severity=Severity.CRITICAL,
            description="利用模板引擎执行任意代码 (SSTI)。",
            payload_example="{{7*7}}",
            detection_regex=r"(?i)(\{\{.*\}\}|\{%.*%\}|\$\{.*\}|#\{.*\})",
            mitre_attack_id="T1190",
        ),
        AttackPattern(
            id="INJ-07",
            name="代码注入",
            category="injection",
            severity=Severity.CRITICAL,
            description="通过eval/exec等函数执行任意代码。",
            payload_example="eval($_GET['cmd'])",
            detection_regex=r"(?i)(\beval\s*\(|\bexec\s*\(|\bsystem\s*\(|\bassert\s*\(|\bpassthru\s*\(|\bshell_exec\s*\()",
            mitre_attack_id="T1059",
        ),
        AttackPattern(
            id="INJ-08",
            name="表达式注入",
            category="injection",
            severity=Severity.CRITICAL,
            description="利用SpEL/OGNL/EL表达式执行任意代码。",
            payload_example="${T(java.lang.Runtime).getRuntime().exec('id')}",
            detection_regex=r"(?i)(\$\{.*Runtime.*\}|\#\{.*\}|\bT\(java\.|@java\.)",
            mitre_attack_id="T1190",
        ),
        AttackPattern(
            id="INJ-09",
            name="Header注入",
            category="injection",
            severity=Severity.HIGH,
            description="通过HTTP头字段注入CRLF或恶意数据。",
            payload_example="User-Agent: test\r\nSet-Cookie: evil=1",
            detection_regex=r"(?i)(%0d%0a|\r\n|set-cookie:|x-forwarded-for:.*,\s*\d)",
            mitre_attack_id="T1190",
        ),
        AttackPattern(
            id="INJ-10",
            name="ORM注入",
            category="injection",
            severity=Severity.HIGH,
            description="利用ORM框架查询接口构造恶意条件。",
            payload_example="User.objects.filter(name__contains='')",
            detection_regex=r"(?i)(__contains|__startswith|__regex|__gt|__lt|raw\s*\(|extra\s*\()",
            mitre_attack_id="T1190",
        ),

        # ====================================================
        # 类别 2: authentication (认证类攻击) AUTH-01 ~ AUTH-10
        # ====================================================
        AttackPattern(
            id="AUTH-01",
            name="暴力破解",
            category="authentication",
            severity=Severity.HIGH,
            description="穷举所有可能密码尝试登录。",
            payload_example="password=aaaa, aaab, aaac...",
            detection_regex=r"(?i)(password\s*=\s*\w{4,}).*\1{5,}|brute|burpsuite|hydra",
            mitre_attack_id="T1110.001",
        ),
        AttackPattern(
            id="AUTH-02",
            name="字典攻击",
            category="authentication",
            severity=Severity.HIGH,
            description="使用预置字典尝试常见密码登录。",
            payload_example="rockyou.txt",
            detection_regex=r"(?i)(rockyou\.txt|password\.lst|wordlist|john\s+--wordlist)",
            mitre_attack_id="T1110.002",
        ),
        AttackPattern(
            id="AUTH-03",
            name="撞库",
            category="authentication",
            severity=Severity.HIGH,
            description="使用其他网站泄露的账号密码尝试登录。",
            payload_example="email:pass from breach",
            detection_regex=r"(?i)(credential\s*stuffing|breach|leaked\s*password|combo\s*list)",
            mitre_attack_id="T1110.004",
        ),
        AttackPattern(
            id="AUTH-04",
            name="会话固定",
            category="authentication",
            severity=Severity.MEDIUM,
            description="强制用户使用攻击者预设的会话ID。",
            payload_example="Set-Cookie: PHPSESSID=fixed123",
            detection_regex=r"(?i)(PHPSESSID|JSESSIONID|ASP\.NET_SessionId)\s*=\s*\w{8,}",
            mitre_attack_id="T1550",
        ),
        AttackPattern(
            id="AUTH-05",
            name="JWT伪造",
            category="authentication",
            severity=Severity.CRITICAL,
            description="伪造或篡改JWT Token冒充身份。",
            payload_example="eyJhbGciOiJub25lIn0.eyJ1c2VyIjoiYWRtaW4ifQ.",
            detection_regex=r"(?i)(eyJhbGciOiJub25l|alg['\"]?\s*[:=]\s*['\"]?none|eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.)",
            mitre_attack_id="T1550",
        ),
        AttackPattern(
            id="AUTH-06",
            name="密码喷洒",
            category="authentication",
            severity=Severity.HIGH,
            description="用少量常见密码尝试大量账号，规避账号锁定。",
            payload_example="Winter2024! for all users",
            detection_regex=r"(?i)(password\s*spray|spray\s*attack|one\s*password\s*many\s*accounts)",
            mitre_attack_id="T1110.003",
        ),
        AttackPattern(
            id="AUTH-07",
            name="Token重放",
            category="authentication",
            severity=Severity.HIGH,
            description="截获并重放有效Token冒充用户。",
            payload_example="Authorization: Bearer <replayed>",
            detection_regex=r"(?i)(bearer\s+[A-Za-z0-9_\.-]{20,}|replay\s*token|token\s*reuse)",
            mitre_attack_id="T1550",
        ),
        AttackPattern(
            id="AUTH-08",
            name="锁定绕过",
            category="authentication",
            severity=Severity.MEDIUM,
            description="通过IP轮换或时间间隔规避账号锁定机制。",
            payload_example="rotate IP after 5 attempts",
            detection_regex=r"(?i)(lockout\s*bypass|account\s*lockout|max\s*attempts\s*bypass|rotate\s*ip)",
            mitre_attack_id="T1110",
        ),
        AttackPattern(
            id="AUTH-09",
            name="MFA绕过",
            category="authentication",
            severity=Severity.CRITICAL,
            description="通过社会工程或漏洞绕过多因素认证。",
            payload_example="intercept MFA OTP via phishing",
            detection_regex=r"(?i)(mfa\s*bypass|2fa\s*bypass|otp\s*intercept|push\s*bombing)",
            mitre_attack_id="T1621",
        ),
        AttackPattern(
            id="AUTH-10",
            name="OAuth劫持",
            category="authentication",
            severity=Severity.CRITICAL,
            description="劫持OAuth授权流程窃取访问令牌。",
            payload_example="redirect_uri=https://evil.com/callback",
            detection_regex=r"(?i)(redirect_uri\s*=\s*https?://(?!.*\byourdomain\b)|oauth\s*hijack|code\s*intercept)",
            mitre_attack_id="T1550",
        ),

        # ====================================================
        # 类别 3: network (网络类攻击) NET-01 ~ NET-10
        # ====================================================
        AttackPattern(
            id="NET-01",
            name="DDoS分布式拒绝服务",
            category="network",
            severity=Severity.CRITICAL,
            description="利用大量节点同时发起请求耗尽目标资源。",
            payload_example="10000 req/s from botnet",
            detection_regex=r"(?i)(ddos|distributed\s*denial|hping3|loic|hoic)",
            mitre_attack_id="T1498",
        ),
        AttackPattern(
            id="NET-02",
            name="SYN Flood",
            category="network",
            severity=Severity.HIGH,
            description="发送大量SYN包半开连接耗尽服务端资源。",
            payload_example="hping3 -S -p 80 --flood",
            detection_regex=r"(?i)(syn\s*flood|hping3\s+-S|--flood|syn\s*cookies)",
            mitre_attack_id="T1498.001",
        ),
        AttackPattern(
            id="NET-03",
            name="CC攻击",
            category="network",
            severity=Severity.HIGH,
            description="模拟真实用户频繁请求耗尽应用层资源。",
            payload_example="GET /search?q=a HTTP/1.1 x1000",
            detection_regex=r"(?i)(cc\s*attack|challenge\s*collapsar|slow\s*http|http\s*flood)",
            mitre_attack_id="T1499",
        ),
        AttackPattern(
            id="NET-04",
            name="中间人攻击",
            category="network",
            severity=Severity.CRITICAL,
            description="攻击者冒充双方进行通信转发窃听篡改。",
            payload_example="ettercap -T -M arp",
            detection_regex=r"(?i)(mitm|man[-\s]*in[-\s]*the[-\s]*middle|ettercap|arpspoof|bettercap)",
            mitre_attack_id="T1557",
        ),
        AttackPattern(
            id="NET-05",
            name="DNS投毒",
            category="network",
            severity=Severity.CRITICAL,
            description="篡改DNS缓存将域名指向恶意IP。",
            payload_example="spoof DNS response",
            detection_regex=r"(?i)(dns\s*poison|dns\s*spoof|cache\s*poison|dnssec\s*bypass)",
            mitre_attack_id="T1557.002",
        ),
        AttackPattern(
            id="NET-06",
            name="端口扫描",
            category="network",
            severity=Severity.MEDIUM,
            description="扫描目标开放端口寻找攻击面。",
            payload_example="nmap -sS 192.168.1.0/24",
            detection_regex=r"(?i)(nmap\s+-s|masscan|port\s*scan|syn\s*scan|\bfin\s*scan)",
            mitre_attack_id="T1046",
        ),
        AttackPattern(
            id="NET-07",
            name="网络嗅探",
            category="network",
            severity=Severity.HIGH,
            description="监听网络流量窃取敏感信息。",
            payload_example="tcpdump -i eth0 -w cap.pcap",
            detection_regex=r"(?i)(tcpdump|wireshark|tshark|sniff|pcap)",
            mitre_attack_id="T1040",
        ),
        AttackPattern(
            id="NET-08",
            name="重放攻击",
            category="network",
            severity=Severity.HIGH,
            description="截获并重新发送合法通信数据。",
            payload_example="replay captured request",
            detection_regex=r"(?i)(replay\s*attack|nonce\s*reuse|capture\s*and\s*replay)",
            mitre_attack_id="T1550",
        ),
        AttackPattern(
            id="NET-09",
            name="包注入",
            category="network",
            severity=Severity.HIGH,
            description="向网络流量注入恶意数据包。",
            payload_example="scapy send(IP()/TCP())",
            detection_regex=r"(?i)(packet\s*injection|scapy|aireplay|inject\s*packet)",
            mitre_attack_id="T1557",
        ),
        AttackPattern(
            id="NET-10",
            name="WiFi入侵",
            category="network",
            severity=Severity.HIGH,
            description="破解或绕过WiFi认证入侵无线网络。",
            payload_example="aircrack-ng wpa.cap",
            detection_regex=r"(?i)(aircrack|wpa\s*crack|wep\s*crack|evil\s*twin|deauth\s*attack)",
            mitre_attack_id="T1557",
        ),

        # ====================================================
        # 类别 4: reverse_engineering (逆向工程类攻击) RE-01 ~ RE-10
        # ====================================================
        AttackPattern(
            id="RE-01",
            name="反编译",
            category="reverse_engineering",
            severity=Severity.MEDIUM,
            description="将编译后的二进制还原为源代码分析逻辑。",
            payload_example="jadx-gui app.apk",
            detection_regex=r"(?i)(jadx|jd-gui|ilspy|dnspy|ghidra|ida\s*pro|decompile)",
            mitre_attack_id="T1589",
        ),
        AttackPattern(
            id="RE-02",
            name="动态调试",
            category="reverse_engineering",
            severity=Severity.MEDIUM,
            description="运行时附加调试器分析程序行为。",
            payload_example="gdb ./binary",
            detection_regex=r"(?i)(gdb|lldb|x64dbg|ollydbg|windbg|ptrace|frida)",
            mitre_attack_id="T1055",
        ),
        AttackPattern(
            id="RE-03",
            name="内存转储",
            category="reverse_engineering",
            severity=Severity.HIGH,
            description="导出进程内存分析敏感数据或密钥。",
            payload_example="procdump -ma 1234",
            detection_regex=r"(?i)(procdump|dd\s+if=/dev/mem|volatility|mem\s*dump|minidump)",
            mitre_attack_id="T1003",
        ),
        AttackPattern(
            id="RE-04",
            name="字符串提取",
            category="reverse_engineering",
            severity=Severity.LOW,
            description="提取二进制中的明文字符串寻找线索。",
            payload_example="strings binary | grep pass",
            detection_regex=r"(?i)(\bstrings\b\s+.*\|.*grep|strings\s+-a|binwalk)",
            mitre_attack_id="T1589",
        ),
        AttackPattern(
            id="RE-05",
            name="控制流分析",
            category="reverse_engineering",
            severity=Severity.MEDIUM,
            description="分析程序控制流图理解执行逻辑。",
            payload_example="CFG analysis via angr",
            detection_regex=r"(?i)(control\s*flow|cfg\s*analysis|angr|radare2|r2\s+-A)",
            mitre_attack_id="T1589",
        ),
        AttackPattern(
            id="RE-06",
            name="Patch修改",
            category="reverse_engineering",
            severity=Severity.HIGH,
            description="修改二进制字节绕过授权或验证。",
            payload_example="patch JE -> JMP at 0x401000",
            detection_regex=r"(?i)(patch\s*binary|nop\s*out|je\s*->\s*jmp|byte\s*patch|hex\s*edit)",
            mitre_attack_id="T1625",
        ),
        AttackPattern(
            id="RE-07",
            name="Hook注入",
            category="reverse_engineering",
            severity=Severity.HIGH,
            description="通过Hook劫持函数调用流程。",
            payload_example="frida -U -l hook.js",
            detection_regex=r"(?i)(frida\s+hook|detour|inline\s*hook|iat\s*hook|ssdt\s*hook)",
            mitre_attack_id="T1055",
        ),
        AttackPattern(
            id="RE-08",
            name="符号执行",
            category="reverse_engineering",
            severity=Severity.MEDIUM,
            description="通过符号执行自动探索程序路径。",
            payload_example="angr symbolic execution",
            detection_regex=r"(?i)(symbolic\s*execution|angr|klee|smt\s*solver|z3\s*solve)",
            mitre_attack_id="T1589",
        ),
        AttackPattern(
            id="RE-09",
            name="Fuzz模糊测试",
            category="reverse_engineering",
            severity=Severity.HIGH,
            description="向程序输入随机数据发现漏洞。",
            payload_example="afl-fuzz -i in -o out ./target",
            detection_regex=r"(?i)(afl-fuzz|libfuzzer|honggfuzz|fuzzing|fuzz\s*target|radamsa)",
            mitre_attack_id="T1589",
        ),
        AttackPattern(
            id="RE-10",
            name="模拟执行",
            category="reverse_engineering",
            severity=Severity.MEDIUM,
            description="使用模拟器运行分析二进制行为。",
            payload_example="qemu-arm ./binary",
            detection_regex=r"(?i)(qemu-\w+|unicorn\s*engine|emu\s*code|emulated\s*execution)",
            mitre_attack_id="T1589",
        ),

        # ====================================================
        # 类别 5: botnet (僵尸网络类攻击) BOT-01 ~ BOT-10
        # ====================================================
        AttackPattern(
            id="BOT-01",
            name="C&C通信",
            category="botnet",
            severity=Severity.CRITICAL,
            description="僵尸节点与命令控制服务器通信接收指令。",
            payload_example="beacon to c2.evil.com",
            detection_regex=r"(?i)(c2\s*server|c&c|command\s*and\s*control|beacon\s*interval|cobalt\s*strike)",
            mitre_attack_id="T1071",
        ),
        AttackPattern(
            id="BOT-02",
            name="DGA域名",
            category="botnet",
            severity=Severity.HIGH,
            description="算法生成大量域名规避封锁定位C&C。",
            payload_example="xkqjw7t8.xyz",
            detection_regex=r"(?i)(dga|domain\s*generation\s*algorithm|[a-z0-9]{8,12}\.(xyz|top|tk|ml|ga|cf))",
            mitre_attack_id="T1568.002",
        ),
        AttackPattern(
            id="BOT-03",
            name="Slowloris",
            category="botnet",
            severity=Severity.HIGH,
            description="慢速发送HTTP请求耗尽Web服务器连接池。",
            payload_example="slowloris.py -p 80",
            detection_regex=r"(?i)(slowloris|slow\s*http|slowris|incomplete\s*header)",
            mitre_attack_id="T1499",
        ),
        AttackPattern(
            id="BOT-04",
            name="HTTP Flood",
            category="botnet",
            severity=Severity.HIGH,
            description="发送大量HTTP请求耗尽应用层资源。",
            payload_example="GET / HTTP/1.1 x100000",
            detection_regex=r"(?i)(http\s*flood|layer7\s*ddos|goldeneye|hulk\s*attack)",
            mitre_attack_id="T1499",
        ),
        AttackPattern(
            id="BOT-05",
            name="P2P僵尸网络",
            category="botnet",
            severity=Severity.CRITICAL,
            description="去中心化P2P结构僵尸网络难以关停。",
            payload_example="P2P botnet like Storm",
            detection_regex=r"(?i)(p2p\s*botnet|peer[-\s]*to[-\s]*peer\s*bot|decentralized\s*botnet)",
            mitre_attack_id="T1071",
        ),
        AttackPattern(
            id="BOT-06",
            name="木马",
            category="botnet",
            severity=Severity.CRITICAL,
            description="伪装成合法程序潜伏控制受害者主机。",
            payload_example="trojan.exe backdoor",
            detection_regex=r"(?i)(trojan|backdoor|rat\s*\(remote|remote\s*access\s*trojan)",
            mitre_attack_id="T1059",
        ),
        AttackPattern(
            id="BOT-07",
            name="蠕虫",
            category="botnet",
            severity=Severity.CRITICAL,
            description="自我复制传播的恶意程序。",
            payload_example="worm spreading via SMB",
            detection_regex=r"(?i)(worm\s*propagation|self\s*replicating|smb\s*worm|wanna*cry)",
            mitre_attack_id="T1021",
        ),
        AttackPattern(
            id="BOT-08",
            name="垃圾邮件",
            category="botnet",
            severity=Severity.MEDIUM,
            description="利用僵尸网络大规模发送垃圾邮件。",
            payload_example="spam campaign from botnet",
            detection_regex=r"(?i)(spam\s*campaign|bulk\s*email|spam\s*bot|mail\s*relay\s*abuse)",
            mitre_attack_id="T1566",
        ),
        AttackPattern(
            id="BOT-09",
            name="点击欺诈",
            category="botnet",
            severity=Severity.MEDIUM,
            description="模拟点击广告骗取广告费用。",
            payload_example="click fraud botnet",
            detection_regex=r"(?i)(click\s*fraud|ad\s*fraud|fake\s*click|ppc\s*fraud)",
            mitre_attack_id="T1499",
        ),
        AttackPattern(
            id="BOT-10",
            name="挖矿木马",
            category="botnet",
            severity=Severity.HIGH,
            description="劫持主机算力挖掘加密货币。",
            payload_example="xmrig --url pool.evil.com",
            detection_regex=r"(?i)(xmrig|coinhive|cryptojacking|miner\s*botnet|stratum\+tcp)",
            mitre_attack_id="T1496",
        ),

        # ====================================================
        # 类别 6: penetration (渗透类攻击) PEN-01 ~ PEN-10
        # ====================================================
        AttackPattern(
            id="PEN-01",
            name="横向移动",
            category="penetration",
            severity=Severity.CRITICAL,
            description="在内网中从一台主机移动到另一台主机。",
            payload_example="lateral movement via SMB",
            detection_regex=r"(?i)(lateral\s*movement|pass\s*the\s*hash|psexec|wmiexec|smbexec)",
            mitre_attack_id="T1021",
        ),
        AttackPattern(
            id="PEN-02",
            name="权限提升",
            category="penetration",
            severity=Severity.CRITICAL,
            description="从普通用户权限提升到管理员或root。",
            payload_example="sudo -l; find suid",
            detection_regex=r"(?i)(privilege\s*escal|privesc|sudo\s*-l|suid\s*find|kernel\s*exploit|dirty\s*cow)",
            mitre_attack_id="T1068",
        ),
        AttackPattern(
            id="PEN-03",
            name="单层穿透",
            category="penetration",
            severity=Severity.HIGH,
            description="攻破单一防御层进入内网。",
            payload_example="breach DMZ firewall",
            detection_regex=r"(?i)(single\s*layer\s*penetrat|breach\s*dmz|one\s*layer\s*bypass)",
            mitre_attack_id="T1190",
        ),
        AttackPattern(
            id="PEN-04",
            name="双层穿透",
            category="penetration",
            severity=Severity.HIGH,
            description="连续攻破两层防御进入核心网络。",
            payload_example="DMZ -> App -> DB",
            detection_regex=r"(?i)(dual\s*layer\s*penetrat|two\s*layer\s*bypass|double\s*hop)",
            mitre_attack_id="T1190",
        ),
        AttackPattern(
            id="PEN-05",
            name="三层穿透",
            category="penetration",
            severity=Severity.CRITICAL,
            description="连续攻破三层防御进入核心数据区。",
            payload_example="Web -> App -> DB -> Internal",
            detection_regex=r"(?i)(triple\s*layer\s*penetrat|three\s*layer\s*bypass|multi[-\s]*hop\s*3)",
            mitre_attack_id="T1190",
        ),
        AttackPattern(
            id="PEN-06",
            name="四层穿透",
            category="penetration",
            severity=Severity.CRITICAL,
            description="连续攻破四层防御直达核心资产。",
            payload_example="Edge -> Web -> App -> DB -> Core",
            detection_regex=r"(?i)(quad\s*layer\s*penetrat|four\s*layer\s*bypass|multi[-\s]*hop\s*4)",
            mitre_attack_id="T1190",
        ),
        AttackPattern(
            id="PEN-07",
            name="Pass-the-Hash",
            category="penetration",
            severity=Severity.CRITICAL,
            description="使用NTLM哈希直接认证无需破解密码。",
            payload_example="pth-winexe -H aad3b435 NTLM",
            detection_regex=r"(?i)(pass\s*the\s*hash|pth-winexe|pth-net|ntlm\s*hash\s*pass)",
            mitre_attack_id="T1550.002",
        ),
        AttackPattern(
            id="PEN-08",
            name="Pass-the-Ticket",
            category="penetration",
            severity=Severity.CRITICAL,
            description="使用窃取的Kerberos票据直接认证。",
            payload_example="Rubeus.exe ptt /ticket:",
            detection_regex=r"(?i)(pass\s*the\s*ticket|ptt\s*ticket|rubeus\s*ptt|kerberos\s*ticket\s*reuse)",
            mitre_attack_id="T1550.003",
        ),
        AttackPattern(
            id="PEN-09",
            name="Golden Ticket",
            category="penetration",
            severity=Severity.CRITICAL,
            description="利用krbtgt账户哈希伪造任意用户TGT。",
            payload_example="forge TGT with krbtgt hash",
            detection_regex=r"(?i)(golden\s*ticket|krbtgt|forge\s*tgt|domain\s*admin\s*ticket)",
            mitre_attack_id="T1558.001",
        ),
        AttackPattern(
            id="PEN-10",
            name="Silver Ticket",
            category="penetration",
            severity=Severity.CRITICAL,
            description="利用服务账户哈希伪造特定服务TGS。",
            payload_example="forge TGS for CIFS service",
            detection_regex=r"(?i)(silver\s*ticket|forge\s*tgs|service\s*account\s*hash\s*ticket)",
            mitre_attack_id="T1558.002",
        ),

        # ====================================================
        # 类别 7: cheese_model (芝士模型孔洞类攻击) CHS-01 ~ CHS-10
        # ====================================================
        AttackPattern(
            id="CHS-01",
            name="L1孔洞",
            category="cheese_model",
            severity=Severity.MEDIUM,
            description="攻破第1层防御(边界防护)形成孔洞。",
            payload_example="breach L1 perimeter",
            detection_regex=r"(?i)(L1\s*hole|L1\s*breach|layer\s*1\s*perimeter\s*bypass)",
            mitre_attack_id="T1190",
        ),
        AttackPattern(
            id="CHS-02",
            name="L2孔洞",
            category="cheese_model",
            severity=Severity.MEDIUM,
            description="攻破第2层防御(网络防护)形成孔洞。",
            payload_example="breach L2 network",
            detection_regex=r"(?i)(L2\s*hole|L2\s*breach|layer\s*2\s*network\s*bypass)",
            mitre_attack_id="T1190",
        ),
        AttackPattern(
            id="CHS-03",
            name="L3孔洞",
            category="cheese_model",
            severity=Severity.HIGH,
            description="攻破第3层防御(主机防护)形成孔洞。",
            payload_example="breach L3 host",
            detection_regex=r"(?i)(L3\s*hole|L3\s*breach|layer\s*3\s*host\s*bypass)",
            mitre_attack_id="T1210",
        ),
        AttackPattern(
            id="CHS-04",
            name="L4孔洞",
            category="cheese_model",
            severity=Severity.HIGH,
            description="攻破第4层防御(应用防护)形成孔洞。",
            payload_example="breach L4 application",
            detection_regex=r"(?i)(L4\s*hole|L4\s*breach|layer\s*4\s*app\s*bypass)",
            mitre_attack_id="T1210",
        ),
        AttackPattern(
            id="CHS-05",
            name="L5孔洞",
            category="cheese_model",
            severity=Severity.HIGH,
            description="攻破第5层防御(数据防护)形成孔洞。",
            payload_example="breach L5 data",
            detection_regex=r"(?i)(L5\s*hole|L5\s*breach|layer\s*5\s*data\s*bypass)",
            mitre_attack_id="T1213",
        ),
        AttackPattern(
            id="CHS-06",
            name="L6孔洞",
            category="cheese_model",
            severity=Severity.HIGH,
            description="攻破第6层防御(身份防护)形成孔洞。",
            payload_example="breach L6 identity",
            detection_regex=r"(?i)(L6\s*hole|L6\s*breach|layer\s*6\s*identity\s*bypass)",
            mitre_attack_id="T1078",
        ),
        AttackPattern(
            id="CHS-07",
            name="L7孔洞",
            category="cheese_model",
            severity=Severity.HIGH,
            description="攻破第7层防御(行为防护)形成孔洞。",
            payload_example="breach L7 behavior",
            detection_regex=r"(?i)(L7\s*hole|L7\s*breach|layer\s*7\s*behavior\s*bypass)",
            mitre_attack_id="T1078",
        ),
        AttackPattern(
            id="CHS-08",
            name="L8孔洞",
            category="cheese_model",
            severity=Severity.CRITICAL,
            description="攻破第8层防御(核心资产防护)形成孔洞。",
            payload_example="breach L8 core asset",
            detection_regex=r"(?i)(L8\s*hole|L8\s*breach|layer\s*8\s*core\s*bypass)",
            mitre_attack_id="T1213",
        ),
        AttackPattern(
            id="CHS-09",
            name="孔洞对齐",
            category="cheese_model",
            severity=Severity.CRITICAL,
            description="多层防御孔洞同时对齐形成穿透通道。",
            payload_example="aligned holes across layers",
            detection_regex=r"(?i)(hole\s*alignment|aligned\s*holes|layer\s*alignment\s*attack|swiss\s*cheese\s*align)",
            mitre_attack_id="T1210",
        ),
        AttackPattern(
            id="CHS-10",
            name="孔洞错位",
            category="cheese_model",
            severity=Severity.LOW,
            description="孔洞错位时被其他层拦截，攻击失败。",
            payload_example="misaligned holes blocked",
            detection_regex=r"(?i)(hole\s*misalign|misaligned\s*holes|offset\s*holes|swiss\s*cheese\s*block)",
            mitre_attack_id="T1210",
        ),

        # ====================================================
        # 类别 8: data_attack (数据类攻击) DATA-01 ~ DATA-10
        # ====================================================
        AttackPattern(
            id="DATA-01",
            name="SQL脱库",
            category="data_attack",
            severity=Severity.CRITICAL,
            description="通过SQL注入导出整个数据库内容。",
            payload_example="sqlmap --dump-all",
            detection_regex=r"(?i)(sqlmap\s+--dump|mysqldump\s+-u|pg_dump|database\s*dump|脱库)",
            mitre_attack_id="T1005",
        ),
        AttackPattern(
            id="DATA-02",
            name="备份窃取",
            category="data_attack",
            severity=Severity.CRITICAL,
            description="窃取系统备份文件获取全部数据。",
            payload_example="download /backup/db.sql.gz",
            detection_regex=r"(?i)(backup\s*theft|steal\s*backup|\.bak\b|\.sql\.gz\b|\.dump\b)",
            mitre_attack_id="T1005",
        ),
        AttackPattern(
            id="DATA-03",
            name="明文数据",
            category="data_attack",
            severity=Severity.HIGH,
            description="窃取未加密存储的敏感数据。",
            payload_example="read plaintext passwords",
            detection_regex=r"(?i)(plaintext\s*password|unencrypted\s*data|cleartext\s*secret|plain\s*text\s*data)",
            mitre_attack_id="T1552",
        ),
        AttackPattern(
            id="DATA-04",
            name="PII泄露",
            category="data_attack",
            severity=Severity.CRITICAL,
            description="个人身份信息泄露事件。",
            payload_example="leak customer PII data",
            detection_regex=r"(?i)(pii\s*leak|personal\s*data\s*leak|identity\s*data\s*expos|个人身份信息泄露)",
            mitre_attack_id="T1567",
        ),
        AttackPattern(
            id="DATA-05",
            name="PCI泄露",
            category="data_attack",
            severity=Severity.CRITICAL,
            description="支付卡行业数据泄露事件。",
            payload_example="leak credit card numbers",
            detection_regex=r"(?i)(pci\s*leak|credit\s*card\s*leak|card\s*data\s*breach|\b\d{16}\b\s+cvv)",
            mitre_attack_id="T1567",
        ),
        AttackPattern(
            id="DATA-06",
            name="PHI泄露",
            category="data_attack",
            severity=Severity.CRITICAL,
            description="受保护健康信息泄露事件。",
            payload_example="leak medical records PHI",
            detection_regex=r"(?i)(phi\s*leak|health\s*data\s*leak|medical\s*record\s*breach|hipaa\s*violation)",
            mitre_attack_id="T1567",
        ),
        AttackPattern(
            id="DATA-07",
            name="IP窃取",
            category="data_attack",
            severity=Severity.HIGH,
            description="窃取知识产权、源代码或商业机密。",
            payload_example="exfiltrate source code",
            detection_regex=r"(?i)(ip\s*theft|intellectual\s*property\s*theft|source\s*code\s*exfiltrat|trade\s*secret\s*steal)",
            mitre_attack_id="T1567",
        ),
        AttackPattern(
            id="DATA-08",
            name="数据投毒",
            category="data_attack",
            severity=Severity.HIGH,
            description="向训练数据注入恶意样本破坏模型。",
            payload_example="poison training dataset",
            detection_regex=r"(?i)(data\s*poison|poison\s*dataset|label\s*flip|backdoor\s*data\s*inject)",
            mitre_attack_id="T1565",
        ),
        AttackPattern(
            id="DATA-09",
            name="数据篡改",
            category="data_attack",
            severity=Severity.HIGH,
            description="非法修改数据破坏完整性。",
            payload_example="UPDATE accounts SET balance=9999",
            detection_regex=r"(?i)(data\s*tamper|unauthorized\s*modif|data\s*manipulat|UPDATE\s+\w+\s+SET)",
            mitre_attack_id="T1565.001",
        ),
        AttackPattern(
            id="DATA-10",
            name="数据删除",
            category="data_attack",
            severity=Severity.CRITICAL,
            description="恶意删除数据造成破坏。",
            payload_example="DROP TABLE users; rm -rf /",
            detection_regex=r"(?i)(data\s*delet|DROP\s+TABLE|rm\s+-rf|DELETE\s+FROM\s+\w+\s+WHERE\s+1|wipe\s*data)",
            mitre_attack_id="T1565.002",
        ),

        # ====================================================
        # 类别 9: ai_attack (AI类攻击) AI-01 ~ AI-10
        # ====================================================
        AttackPattern(
            id="AI-01",
            name="对抗样本",
            category="ai_attack",
            severity=Severity.HIGH,
            description="构造细微扰动样本欺骗AI模型。",
            payload_example="FGSM perturbation",
            detection_regex=r"(?i)(adversarial\s*sample|fgsm|pgd\s*attack|carlini\s*wagner|evasion\s*attack)",
            mitre_attack_id="T1499",
        ),
        AttackPattern(
            id="AI-02",
            name="模型窃取",
            category="ai_attack",
            severity=Severity.HIGH,
            description="通过查询API复制目标模型能力。",
            payload_example="extract model via queries",
            detection_regex=r"(?i)(model\s*steal|model\s*extract|knockoff\s*model|copycat\s*attack)",
            mitre_attack_id="T1499",
        ),
        AttackPattern(
            id="AI-03",
            name="AI数据投毒",
            category="ai_attack",
            severity=Severity.HIGH,
            description="污染AI训练数据影响模型输出。",
            payload_example="inject poisoned samples",
            detection_regex=r"(?i)(ai\s*poison|training\s*data\s*poison|poison\s*attack\s*model|label\s*manipulat)",
            mitre_attack_id="T1565",
        ),
        AttackPattern(
            id="AI-04",
            name="模型逆推",
            category="ai_attack",
            severity=Severity.HIGH,
            description="逆向推断模型训练数据内容。",
            payload_example="model inversion attack",
            detection_regex=r"(?i)(model\s*inversion|invert\s*model|reconstruct\s*training\s*data)",
            mitre_attack_id="T1499",
        ),
        AttackPattern(
            id="AI-05",
            name="成员推理",
            category="ai_attack",
            severity=Severity.MEDIUM,
            description="推断特定数据是否在训练集中。",
            payload_example="membership inference query",
            detection_regex=r"(?i)(membership\s*inference|inference\s*attack|in\s*or\s*out\s*of\s*training)",
            mitre_attack_id="T1499",
        ),
        AttackPattern(
            id="AI-06",
            name="后门攻击",
            category="ai_attack",
            severity=Severity.CRITICAL,
            description="在模型中植入触发器后门。",
            payload_example="backdoor trigger patch",
            detection_regex=r"(?i)(backdoor\s*attack|trojan\s*neural|trigger\s*patch|badnet)",
            mitre_attack_id="T1499",
        ),
        AttackPattern(
            id="AI-07",
            name="规避攻击",
            category="ai_attack",
            severity=Severity.HIGH,
            description="修改输入规避AI检测。",
            payload_example="evade malware classifier",
            detection_regex=r"(?i)(evasion\s*attack|evade\s*classifier|classifier\s*bypass|adversarial\s*evade)",
            mitre_attack_id="T1499",
        ),
        AttackPattern(
            id="AI-08",
            name="投毒攻击",
            category="ai_attack",
            severity=Severity.HIGH,
            description="向在线学习模型注入恶意数据。",
            payload_example="online poisoning stream",
            detection_regex=r"(?i)(poisoning\s*attack|online\s*poison|clean[-\s]*label\s*poison)",
            mitre_attack_id="T1565",
        ),
        AttackPattern(
            id="AI-09",
            name="模型抽取",
            category="ai_attack",
            severity=Severity.HIGH,
            description="通过大量查询抽取模型参数。",
            payload_example="extract model weights",
            detection_regex=r"(?i)(model\s*extraction|extract\s*weights|equivalent\s*model\s*extract|hyperparameter\s*steal)",
            mitre_attack_id="T1499",
        ),
        AttackPattern(
            id="AI-10",
            name="对抗注入",
            category="ai_attack",
            severity=Severity.HIGH,
            description="向LLM输入注入对抗指令。",
            payload_example="Ignore previous instructions",
            detection_regex=r"(?i)(prompt\s*inject|ignore\s*previous\s*instruction|jailbreak\s*llm|adversarial\s*prompt)",
            mitre_attack_id="T1499",
        ),

        # ====================================================
        # 类别 10: social_engineering (社会工程类攻击) SE-01 ~ SE-10
        # ====================================================
        AttackPattern(
            id="SE-01",
            name="钓鱼",
            category="social_engineering",
            severity=Severity.HIGH,
            description="伪造可信机构诱骗用户泄露信息。",
            payload_example="fake bank login page",
            detection_regex=r"(?i)(phishing|fake\s*login|spoof\s*email|verify\s*your\s*account\s*click\s*here)",
            mitre_attack_id="T1566.002",
        ),
        AttackPattern(
            id="SE-02",
            name="鱼叉攻击",
            category="social_engineering",
            severity=Severity.HIGH,
            description="针对特定人员定制钓鱼攻击。",
            payload_example="spear phishing CEO email",
            detection_regex=r"(?i)(spear\s*phish|targeted\s*phish|customized\s*phish\s*email)",
            mitre_attack_id="T1566.001",
        ),
        AttackPattern(
            id="SE-03",
            name="鲸鱼攻击",
            category="social_engineering",
            severity=Severity.CRITICAL,
            description="针对高管人员的钓鱼攻击。",
            payload_example="whaling attack on CFO",
            detection_regex=r"(?i)(whaling|ceo\s*fraud|executive\s*phish|cfo\s*target)",
            mitre_attack_id="T1566.001",
        ),
        AttackPattern(
            id="SE-04",
            name="水坑攻击",
            category="social_engineering",
            severity=Severity.HIGH,
            description="攻击目标常访问的合法网站植入恶意代码。",
            payload_example="infect trusted forum",
            detection_regex=r"(?i)(watering\s*hole|watering\s*hole\s*attack|infect\s*trusted\s*site)",
            mitre_attack_id="T1185",
        ),
        AttackPattern(
            id="SE-05",
            name="Pretexting",
            category="social_engineering",
            severity=Severity.MEDIUM,
            description="编造借口场景骗取信任获取信息。",
            payload_example="fake IT support call",
            detection_regex=r"(?i)(pretexting|pretext\s*call|impersonat\w+\s*(support|it|hr)|fake\s*identity\s*call)",
            mitre_attack_id="T1566",
        ),
        AttackPattern(
            id="SE-06",
            name="诱饵",
            category="social_engineering",
            severity=Severity.MEDIUM,
            description="利用好奇心或贪婪投放诱饵载体。",
            payload_example="free USB stick dropped",
            detection_regex=r"(?i)(baiting|free\s*usb|lost\s*usb|free\s*movie\s*download|tempting\s*bait)",
            mitre_attack_id="T1098",
        ),
        AttackPattern(
            id="SE-07",
            name="尾随",
            category="social_engineering",
            severity=Severity.MEDIUM,
            description="紧随授权人员进入受限物理区域。",
            payload_example="tailgate through door",
            detection_regex=r"(?i)(tailgat|piggyback|follow\s*through\s*door|unauthorized\s*physical\s*entry)",
            mitre_attack_id="T1190",
        ),
        AttackPattern(
            id="SE-08",
            name="肩窥",
            category="social_engineering",
            severity=Severity.LOW,
            description="偷窥他人输入密码等敏感信息。",
            payload_example="shoulder surf password",
            detection_regex=r"(?i)(shoulder\s*surf|over\s*the\s*shoulder|peek\s*password|observe\s*input)",
            mitre_attack_id="T1552",
        ),
        AttackPattern(
            id="SE-09",
            name="USB投放",
            category="social_engineering",
            severity=Severity.HIGH,
            description="投放恶意USB设备等待用户插入。",
            payload_example="rubber ducky USB",
            detection_regex=r"(?i)(usb\s*drop|rubber\s*ducky|badusb|usb\s*dropping\s*attack|malicious\s*usb)",
            mitre_attack_id="T1091",
        ),
        AttackPattern(
            id="SE-10",
            name="语音钓鱼",
            category="social_engineering",
            severity=Severity.HIGH,
            description="通过电话语音诱骗受害者。",
            payload_example="vishing call from fake bank",
            detection_regex=r"(?i)(vishing|voice\s*phish|phone\s*scam|robocall\s*fraud|fake\s*caller\s*id)",
            mitre_attack_id="T1566",
        ),
    ]

    # ------------------------------------------------------------
    # 类别索引缓存 (首次查询时构建，加速后续查询)
    # ------------------------------------------------------------
    _category_index: dict = {}
    _id_index: dict = {}
    _compiled_patterns: list = []

    def __init__(self) -> None:
        """初始化数据库并构建索引"""
        self._build_indexes()

    @classmethod
    def _build_indexes(cls) -> None:
        """构建类别和ID的索引缓存"""
        cls._category_index = {}
        cls._id_index = {}
        cls._compiled_patterns = []
        for pattern in cls.PATTERNS:
            # ID 索引
            cls._id_index[pattern.id] = pattern
            # 类别索引
            cls._category_index.setdefault(pattern.category, []).append(pattern)
            # 预编译正则
            try:
                compiled = re.compile(pattern.detection_regex, re.IGNORECASE)
            except re.error:
                compiled = None
            cls._compiled_patterns.append((pattern, compiled))

    # ------------------------------------------------------------
    # 查询接口
    # ------------------------------------------------------------
    @classmethod
    def get_by_category(cls, category: str) -> List[AttackPattern]:
        """按类别获取攻击模式列表

        Args:
            category: 类别名称

        Returns:
            该类别下所有攻击模式
        """
        if not cls._category_index:
            cls._build_indexes()
        return list(cls._category_index.get(category, []))

    @classmethod
    def get_by_id(cls, pattern_id: str) -> Optional[AttackPattern]:
        """按ID获取攻击模式

        Args:
            pattern_id: 攻击模式ID

        Returns:
            匹配的攻击模式，未找到返回None
        """
        if not cls._id_index:
            cls._build_indexes()
        return cls._id_index.get(pattern_id)

    @classmethod
    def get_all(cls) -> List[AttackPattern]:
        """获取全部攻击模式

        Returns:
            全部100种攻击模式列表
        """
        return list(cls.PATTERNS)

    @classmethod
    def count(cls) -> int:
        """返回攻击模式总数

        Returns:
            攻击模式总数
        """
        return len(cls.PATTERNS)

    @classmethod
    def match(cls, input_string: str) -> List[AttackPattern]:
        """匹配输入字符串，返回匹配的攻击模式列表

        Args:
            input_string: 待检测的输入字符串

        Returns:
            所有检测正则匹配成功的攻击模式列表
        """
        if not cls._compiled_patterns:
            cls._build_indexes()
        matched: List[AttackPattern] = []
        for pattern, compiled in cls._compiled_patterns:
            if compiled is not None and compiled.search(input_string):
                matched.append(pattern)
        return matched

    @classmethod
    def get_categories(cls) -> List[str]:
        """获取所有类别名称

        Returns:
            类别名称列表
        """
        if not cls._category_index:
            cls._build_indexes()
        return list(cls._category_index.keys())

    @classmethod
    def count_by_category(cls, category: str) -> int:
        """统计指定类别攻击模式数量

        Args:
            category: 类别名称

        Returns:
            该类别攻击模式数量
        """
        return len(cls.get_by_category(category))


# ============================================================
# 自检入口
# ============================================================
def _main() -> None:
    """自检主函数：验证攻击模式数据库完整性"""
    db = AttackPatternDB()

    print("=" * 70)
    print(" 攻击模式数据库 (Attack Pattern Database) 自检报告")
    print("=" * 70)

    # 1. 总数校验
    total = db.count()
    print(f"\n[1] 攻击模式总数: {total}")
    assert total == 100, f"攻击模式总数应为100，实际为 {total}"
    print("    -> 校验通过 (应为100)")

    # 2. 类别校验
    expected_categories = [
        "injection", "authentication", "network", "reverse_engineering",
        "botnet", "penetration", "cheese_model", "data_attack",
        "ai_attack", "social_engineering",
    ]
    categories = db.get_categories()
    print(f"\n[2] 类别总数: {len(categories)}")
    assert len(categories) == 10, f"类别总数应为10，实际为 {len(categories)}"
    print("    -> 校验通过 (应为10)")

    print("\n[3] 各类别攻击模式明细:")
    print("-" * 70)
    for cat in expected_categories:
        patterns = db.get_by_category(cat)
        assert len(patterns) == 10, f"类别 {cat} 应有10种，实际 {len(patterns)}"
        # 统计严重性分布
        severity_dist = {}
        for p in patterns:
            severity_dist[p.severity.value] = severity_dist.get(p.severity.value, 0) + 1
        sev_str = " / ".join(f"{k}:{v}" for k, v in sorted(severity_dist.items()))
        print(f"  [{cat:<22}] 数量: {len(patterns):>2}  严重性分布: {sev_str}")
        for p in patterns:
            print(f"      - {p.id:<8} {p.severity.value:<8} {p.name}")
    print("-" * 70)

    # 3. ID唯一性校验
    all_patterns = db.get_all()
    all_ids = [p.id for p in all_patterns]
    assert len(set(all_ids)) == 100, "存在重复ID"
    print(f"\n[4] ID唯一性校验: 通过 (100个ID全部唯一)")

    # 4. 正则有效性校验
    invalid_regex = []
    for p in all_patterns:
        try:
            re.compile(p.detection_regex)
        except re.error as e:
            invalid_regex.append((p.id, str(e)))
    print(f"\n[5] 正则表达式有效性校验: ", end="")
    if invalid_regex:
        print(f"失败 ({len(invalid_regex)}个无效)")
        for pid, err in invalid_regex:
            print(f"      - {pid}: {err}")
    else:
        print("通过 (100个正则全部有效)")

    # 5. 匹配功能测试
    print("\n[6] 匹配功能测试:")
    test_cases = [
        ("' OR '1'='1' --", "SQL注入测试"),
        ("<script>alert(1)</script>", "XSS测试"),
        ("; cat /etc/passwd", "命令注入测试"),
        ("{{7*7}}", "模板注入测试"),
        ("eyJhbGciOiJub25lIn0.eyJ1c2VyIjoiYWRtaW4ifQ.", "JWT伪造测试"),
        ("nmap -sS 192.168.1.0/24", "端口扫描测试"),
        ("sqlmap --dump-all", "SQL脱库测试"),
        ("Ignore previous instructions", "对抗注入测试"),
        ("free USB stick dropped in parking", "诱饵攻击测试"),
        ("DROP TABLE users; rm -rf /", "数据删除测试"),
    ]
    for test_input, desc in test_cases:
        matched = db.match(test_input)
        matched_names = [m.name for m in matched[:3]]
        more = f" ...(+{len(matched)-3})" if len(matched) > 3 else ""
        print(f"    [{desc:<14}] 匹配 {len(matched):>2} 项: {', '.join(matched_names)}{more}")

    # 6. 按ID查询测试
    print("\n[7] 按ID查询测试:")
    test_ids = ["INJ-01", "AUTH-05", "NET-01", "PEN-09", "CHS-09", "AI-10", "SE-03"]
    for pid in test_ids:
        p = db.get_by_id(pid)
        if p:
            print(f"    {pid}: {p.name} [{p.category}] 严重性={p.severity.value} MITRE={p.mitre_attack_id}")
        else:
            print(f"    {pid}: 未找到")

    print("\n" + "=" * 70)
    print(f" 自检完成: {db.count()} 种攻击模式，{len(db.get_categories())} 个类别，全部校验通过")
    print("=" * 70)


if __name__ == "__main__":
    _main()
