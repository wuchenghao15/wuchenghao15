#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓包(pcap)异常解析器 - 纯本地二进制解析, 无外部依赖
检测: 端口扫描 / RST 风暴 / 重传风暴 / 超大包 / 异常 TTL / HTTP 错误响应 / TLS 握手失败
输出异常特征供治理中枢入库 + 投喂脑库 + 触发自动修复
"""
from __future__ import annotations

import os
import struct
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("pcap_anomaly_parser")

# pcap 链路类型
LINKTYPE_ETHERNET = 1
LINKTYPE_NULL = 0
LINKTYPE_LINUX_SLL = 113

# IP 协议号
PROTO_TCP = 6
PROTO_UDP = 17


class PcapParseError(Exception):
    pass


def _read_pcap_header(fh) -> Tuple[int, int]:
    """读 pcap 全局头, 返回 (magic, linktype)."""
    hdr = fh.read(24)
    if len(hdr) < 24:
        raise PcapParseError("pcap 全局头不足 24 字节")
    magic = struct.unpack("<I", hdr[:4])[0]
    if magic == 0xA1B2C3D4:
        endian = "<"
    elif magic == 0xD4C3B2A1:
        endian = ">"
    else:
        raise PcapParseError(f"非 pcap magic: 0x{magic:08x}")
    linktype = struct.unpack(endian + "I", hdr[20:24])[0]
    return endian, linktype


def _iter_packets(fh, endian: str):
    """迭代 pcap 包: yield (ts_sec, pkt_data)."""
    while True:
        pkthdr = fh.read(16)
        if len(pkthdr) < 16:
            break
        ts_sec, ts_usec, incl_len, orig_len = struct.unpack(endian + "IIII", pkthdr)
        data = fh.read(incl_len)
        if len(data) < incl_len:
            break
        yield ts_sec, data


def _parse_l2(data: bytes, linktype: int) -> Optional[bytes]:
    """剥离链路层, 返回 IP 载荷. 仅支持 Ethernet/Null/LinuxSLL."""
    try:
        if linktype == LINKTYPE_ETHERNET:
            if len(data) < 14:
                return None
            ethertype = struct.unpack("!H", data[12:14])[0]
            if ethertype == 0x0800:  # IPv4
                return data[14:]
            return None
        if linktype == LINKTYPE_NULL:
            if len(data) < 4:
                return None
            fam = struct.unpack("<I", data[:4])[0]
            if fam == 2:  # AF_INET
                return data[4:]
            return None
        if linktype == LINKTYPE_LINUX_SLL:
            if len(data) < 16:
                return None
            proto = struct.unpack("!H", data[14:16])[0]
            if proto == 0x0800:
                return data[16:]
            return None
    except struct.error:
        return None
    return None


def _parse_ip(data: bytes) -> Optional[Dict[str, Any]]:
    """解析 IPv4 头, 返回 {src, dst, proto, ttl, payload}."""
    if len(data) < 20:
        return None
    ver_ihl = data[0]
    if (ver_ihl >> 4) != 4:
        return None
    ihl = (ver_ihl & 0x0F) * 4
    if ihl < 20 or len(data) < ihl:
        return None
    proto = data[9]
    ttl = data[8]
    src = ".".join(str(b) for b in data[12:16])
    dst = ".".join(str(b) for b in data[16:20])
    return {"src": src, "dst": dst, "proto": proto, "ttl": ttl, "payload": data[ihl:]}


def _parse_tcp(data: bytes) -> Optional[Dict[str, Any]]:
    if len(data) < 20:
        return None
    sport, dport = struct.unpack("!HH", data[:4])
    flags = data[13]
    return {
        "sport": sport, "dport": dport,
        "syn": bool(flags & 0x02), "ack": bool(flags & 0x10),
        "rst": bool(flags & 0x04), "fin": bool(flags & 0x01),
        "psh": bool(flags & 0x08),
    }


def _parse_udp(data: bytes) -> Optional[Dict[str, Any]]:
    if len(data) < 8:
        return None
    sport, dport, length = struct.unpack("!HHH", data[:6])
    return {"sport": sport, "dport": dport, "length": length, "payload": data[8:]}


def _detect_http_error(payload: bytes) -> Optional[int]:
    """检测 HTTP 响应错误码, 返回状态码或 None."""
    if not payload:
        return None
    try:
        head = payload[:64].decode("latin-1", errors="ignore")
    except Exception:
        return None
    if not head.startswith("HTTP/"):
        return None
    parts = head.split(" ", 2)
    if len(parts) < 2:
        return None
    try:
        code = int(parts[1])
    except ValueError:
        return None
    if code >= 400:
        return code
    return None


def parse_pcap(pcap_path: str) -> Dict[str, Any]:
    """解析 pcap 文件, 返回 {anomalies, stats}. 异常列表供中枢消费."""
    if not os.path.exists(pcap_path):
        return {"anomalies": [], "stats": {"error": "file not found"}, "path": pcap_path}

    anomalies: List[Dict[str, Any]] = []
    # 统计聚合容器
    port_scan_map: Dict[str, set] = defaultdict(set)       # src -> set(dport)
    rst_count: Dict[str, int] = defaultdict(int)            # src -> rst 数
    retrans_candidates: Dict[Tuple[str, str, int], int] = defaultdict(int)  # (src,dst,seq前缀) -> count
    big_packets = 0
    low_ttl_count = 0
    http_errors: Dict[int, int] = defaultdict(int)
    tls_alert_count = 0
    total_packets = 0
    tcp_packets = 0
    udp_packets = 0

    try:
        with open(pcap_path, "rb") as fh:
            endian, linktype = _read_pcap_header(fh)
            for ts_sec, pkt in _iter_packets(fh, endian):
                total_packets += 1
                if len(pkt) > 1500:
                    big_packets += 1
                ip = _parse_l2(pkt, linktype)
                if not ip:
                    continue
                ipp = _parse_ip(ip)
                if not ipp:
                    continue
                if ipp["ttl"] < 10:
                    low_ttl_count += 1
                if ipp["proto"] == PROTO_TCP:
                    tcp_packets += 1
                    tcp = _parse_tcp(ipp["payload"])
                    if not tcp:
                        continue
                    port_scan_map[ipp["src"]].add(tcp["dport"])
                    if tcp["rst"]:
                        rst_count[ipp["src"]] += 1
                    # 重传启发式: 同 (src,dst,dport) SYN 重发
                    if tcp["syn"] and not tcp["ack"]:
                        retrans_candidates[(ipp["src"], ipp["dst"], tcp["dport"])] += 1
                elif ipp["proto"] == PROTO_UDP:
                    udp_packets += 1
                    udp = _parse_udp(ipp["payload"])
                    if not udp:
                        continue
                    port_scan_map[ipp["src"]].add(udp["dport"])
                    code = _detect_http_error(udp["payload"])
                    if code:
                        http_errors[code] += 1
                # TCP 载荷 HTTP 检测
                if ipp["proto"] == PROTO_TCP and ipp["payload"]:
                    tcp = _parse_tcp(ipp["payload"])
                    if tcp and tcp["psh"]:
                        tcp_payload = ipp["payload"][20:]
                        code = _detect_http_error(tcp_payload)
                        if code:
                            http_errors[code] += 1
                        # TLS 握手失败启发式: 含 "alert" 或 0x15 内容类型
                        if len(tcp_payload) > 0 and tcp_payload[0] == 0x15:
                            tls_alert_count += 1
    except PcapParseError as e:
        return {"anomalies": [], "stats": {"error": str(e)}, "path": pcap_path}
    except Exception as e:
        logger.error("parse_pcap 异常: %s", e)
        return {"anomalies": [], "stats": {"error": str(e)}, "path": pcap_path}

    # 聚合异常
    for src, ports in port_scan_map.items():
        if len(ports) >= 20:  # 单源扫 >=20 端口
            anomalies.append({
                "type": "port_scan",
                "severity": "high",
                "signature": f"port_scan:{src}:{len(ports)}ports",
                "context": {"src": src, "port_count": len(ports), "ports": sorted(ports)[:50]},
            })
    for src, cnt in rst_count.items():
        if cnt >= 30:
            anomalies.append({
                "type": "rst_storm",
                "severity": "high",
                "signature": f"rst_storm:{src}:{cnt}",
                "context": {"src": src, "rst_count": cnt},
            })
    for (src, dst, dport), cnt in retrans_candidates.items():
        if cnt >= 10:
            anomalies.append({
                "type": "retrans_storm",
                "severity": "medium",
                "signature": f"retrans:{src}->{dst}:{dport}:{cnt}",
                "context": {"src": src, "dst": dst, "dport": dport, "count": cnt},
            })
    if big_packets > 50:
        anomalies.append({
            "type": "oversized_packets",
            "severity": "low",
            "signature": f"oversized:{big_packets}",
            "context": {"count": big_packets},
        })
    if low_ttl_count > 100:
        anomalies.append({
            "type": "low_ttl",
            "severity": "medium",
            "signature": f"low_ttl:{low_ttl_count}",
            "context": {"count": low_ttl_count},
        })
    for code, cnt in http_errors.items():
        if cnt >= 5:
            anomalies.append({
                "type": "http_error_burst",
                "severity": "high" if code >= 500 else "medium",
                "signature": f"http_{code}:{cnt}",
                "context": {"status_code": code, "count": cnt},
            })
    if tls_alert_count >= 5:
        anomalies.append({
            "type": "tls_alert_burst",
            "severity": "high",
            "signature": f"tls_alert:{tls_alert_count}",
            "context": {"count": tls_alert_count},
        })

    return {
        "anomalies": anomalies,
        "stats": {
            "total_packets": total_packets,
            "tcp_packets": tcp_packets,
            "udp_packets": udp_packets,
            "big_packets": big_packets,
            "low_ttl": low_ttl_count,
            "rst_total": sum(rst_count.values()),
            "http_errors": dict(http_errors),
            "tls_alerts": tls_alert_count,
            "anomaly_count": len(anomalies),
        },
        "path": pcap_path,
        "parsed_at": datetime.now().isoformat(),
    }


def scan_pcap_dir(pcap_dir: str) -> List[Dict[str, Any]]:
    """扫描目录下所有 .pcap/.pcapng 文件, 返回所有解析结果."""
    results = []
    if not os.path.isdir(pcap_dir):
        return results
    try:
        for name in sorted(os.listdir(pcap_dir)):
            if name.endswith((".pcap", ".pcapng", ".cap")):
                results.append(parse_pcap(os.path.join(pcap_dir, name)))
    except Exception as e:
        logger.error("scan_pcap_dir 失败: %s", e)
    return results
