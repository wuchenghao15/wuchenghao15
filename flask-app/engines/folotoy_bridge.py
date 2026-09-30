#!/usr/bin/env python3
"""
仙女座 → FoloToy AI Passport BLE 音频桥接器
==============================================

通过 macOS 原生 BLE (CoreBluetooth via bleak), 与 FoloToy ESP32-C3 硬件设备通信,
实现: 命令发送 · 蜂鸣触发 · 设备状态读取 · 音频通道预留

协议 (已逆向):
  Service  : 54524145-4341-5244-0000-000000000000  ("TRAECARD")
  Char 0x10: WRITE + WRITE_NO_RESP — 命令 / 音频数据 写入
  Char 0x11: NOTIFY                — ACK 响应 (00 10=OK, 00 11=ERR, 00 15=音频通道就绪)
  Char 0x12: READ                  — 设备身份 (SN + Token + 固件版本)
  Char 0x13: READ                  — 运行状态
  Char 0x14: NOTIFY                — 保留 (可能麦克风上行)

ACK 规律:
  type=0x01 + len + payload → 00 15 (音频通道就绪)
  纯文本 → 00 10 (OK)
  非法帧 → 00 11 (ERR)

硬件: ESP32-C3 + ES8311 I2S 音频编解码器, RAM 68KB, BLE GATT ~20B/包 MTU.

方案选择:
  A (立即) — 发送 BLE 命令触发设备播放内置蜂鸣/提示音  ← 当前实现
  B (固件) — tinyusb UAC + I2S DMA 让 ESP32-C3 接收 USB 音频流  ← 需改固件
  C (桥接) — Mac 本地 say/tts 生成 PCM → BLE 分片喂 ESP32  ← BLE 速度 ~10KB/s, 可做

用法:
  python3 folotoy_bridge.py scan           # 扫描附近 BLE 设备
  python3 folotoy_bridge.py connect        # 连接 + 读 0x12/0x13
  python3 folotoy_bridge.py status         # 读 0x12 (身份) + 0x13 (状态)
  python3 folotoy_bridge.py beep           # 触发短蜂鸣
  python3 folotoy_bridge.py beep-long      # 触发长蜂鸣
  python3 folotoy_bridge.py text "hello"   # 发纯文本命令
  python3 folotoy_bridge.py report         # 完整仙女座报告 + BLE 蜂鸣提示
  python3 folotoy_bridge.py volume-up
  python3 folotoy_bridge.py volume-down
"""
from __future__ import annotations
import asyncio, sys, os, time, argparse, struct, json
from datetime import datetime
from pathlib import Path
from typing import Optional

# ═══════════════════════════════════════════════════════════
# BLE 协议常量
# ═══════════════════════════════════════════════════════════

SERVICE_UUID = "54524145-4341-5244-0000-000000000000"

# Characteristic UUIDs (短形式 → 补全)
# 实测: idx 嵌在最后一段的末尾, 如 0x10 → ...000000000010
def _char_uuid(idx: int) -> str:
    return f"54524145-4341-5244-0000-00000000{idx:04x}"

CHAR_WRITE       = _char_uuid(0x10)   # WRITE / WRITE_NO_RESP
CHAR_ACK_NOTIFY  = _char_uuid(0x11)   # NOTIFY
CHAR_IDENTITY    = _char_uuid(0x12)   # READ
CHAR_STATE       = _char_uuid(0x13)   # READ
CHAR_MIC_NOTIFY  = _char_uuid(0x14)   # NOTIFY (保留)

# ACK 类型 (来自 0x11 Notify)
ACK_OK             = bytes([0x00, 0x10])
ACK_ERR            = bytes([0x00, 0x11])
ACK_AUDIO_READY    = bytes([0x00, 0x15])

# BLE MTU 安全值 — ESP32 GATT 默认每包 ~20B, 扣除 3B ATT 头 → 17B payload
BLE_PAYLOAD_SIZE = 17

# ═══════════════════════════════════════════════════════════
# 命令集 (实测: BLE 通道就是纯文本命令!)
#   所有字符串 + \r\n  → 0x10 写入 → 设备解析命令并回 00 10 OK
#   二进制帧 → ACK_ERR (00 11) 或无响应
# ═══════════════════════════════════════════════════════════

def _t(cmd: str) -> bytes:
    """把命令字符串转成 UTF-8 + CRLF"""
    return cmd.encode("utf-8") + b"\r\n"

COMMAND_SET: dict[str, bytes] = {
    # — 音频类 —
    "beep":          _t("beep"),          # 短蜂鸣
    "beep_long":     _t("beep_long"),     # 长蜂鸣
    "beep_sos":      _t("beep_sos"),      # SOS 三短音
    "beep_chime":    _t("beep_chime"),    # 风铃提示音
    "speak_start":   _t("speak_start"),   # 开始 PCM 流 → 期待 00 15
    "speak_stop":    _t("speak_stop"),    # 停止 PCM 流

    # — 提示音类 —
    "report_ok":     _t("report_ok"),     # 仙女座报告到达
    "report_err":    _t("report_err"),    # 异常告警
    "boot_jingle":   _t("boot_jingle"),   # 启动音效
    "shutdown":      _t("shutdown"),      # 关机提示

    # — 音量类 —
    "volume_up":     _t("volume_up"),
    "volume_down":   _t("volume_down"),
    "volume_max":    _t("volume_max"),
    "volume_mute":   _t("volume_mute"),

    # — 系统类 —
    "sys_reboot":    _t("reboot"),
    "sys_wifi_test": _t("wifi_test"),
    "sys_identify":  _t("identify"),

    # — AT 透传 (BLE 也能透传 AT 命令!) —
    "at":            _t("AT"),
    "at_config":     _t("AT+CONFIG=?"),
    "at_command":    _t("AT+COMMAND=?"),
}


# ═══════════════════════════════════════════════════════════
# 全局状态 (bleak 是 asyncio, 所以用全局 event loop 管理)
# ═══════════════════════════════════════════════════════════

_ack_queue: Optional[asyncio.Queue] = None          # 来自 0x11 的 ACK 帧 (每次 connect 重置)
_mic_queue: Optional[asyncio.Queue] = None          # 来自 0x14 的数据 (保留)
_connected_address: Optional[str] = None           # 已连接设备地址 (缓存)
_ble_client = None                                  # bleak.BleakClient 实例


def _ensure_queues():
    """在当前 event loop 里初始化 queue — 避免跨 loop 共享问题"""
    global _ack_queue, _mic_queue
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return  # 不在协程里, 稍后再初始化
    if _ack_queue is None:
        _ack_queue = asyncio.Queue()
    if _mic_queue is None:
        _mic_queue = asyncio.Queue()


def _ack_to_str(data: bytes) -> str:
    """把 ACK 帧转成人类可读描述"""
    if data == ACK_OK:          return "ACK_OK (命令成功)"
    if data == ACK_ERR:         return "ACK_ERR (命令错误)"
    if data == ACK_AUDIO_READY: return "ACK_AUDIO_READY (音频通道就绪)"
    # 未知 ACK → hex
    return f"ACK_UNKNOWN {data.hex()}"


async def _on_ack(sender, data: bytes):
    """0x11 Notify 回调 → 进队列"""
    if _ack_queue is not None:
        await _ack_queue.put(bytes(data))


async def _on_mic(sender, data: bytes):
    """0x14 Notify 回调 (保留)"""
    if _mic_queue is not None:
        await _mic_queue.put(bytes(data))


# ═══════════════════════════════════════════════════════════
# 扫描 & 连接
# ═══════════════════════════════════════════════════════════

async def scan(timeout: float = 8.0, verbose: bool = True) -> list[dict]:
    """扫描 BLE 设备, 返回 FoloToy / AI Passport 目标设备"""
    from bleak import BleakScanner
    # 已知 FoloToy 的 SN 尾号 / MAC 特征
    FOLOTOY_KEYWORDS = ("folotoy", "trae", "esp32", "passport", "ai-", "es8311")
    FOLOTOY_KNOWN_SN_SUFFIXES = ("98c377f490f8",)   # 设备 SN 后 12 位
    print(f"🔍 扫描 BLE 设备 ({timeout}s)...")
    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
    hits = []
    all_devs: list[tuple] = []
    for dev, adv in devices.values():
        name = (adv.local_name or dev.name or "").strip()
        uuids = adv.service_uuids or []
        mf = adv.manufacturer_data or {}
        # RSSI 过滤 — 信号太弱的直接跳过 (esp32 BLE 广播一般 -30 ~ -75)
        if adv.rssi and adv.rssi < -95:
            continue
        if not name and not uuids:
            continue
        matched = False
        name_lower = name.lower()
        # 规则 1: 关键字
        if any(k in name_lower for k in FOLOTOY_KEYWORDS):
            matched = True
        # 规则 2: 已知 SN 尾号 (ESP32-C3 默认 BLE 广播名就是 SN 后 12 位)
        if any(suffix in name_lower for suffix in FOLOTOY_KNOWN_SN_SUFFIXES):
            matched = True
        # 规则 3: Service UUID 匹配
        if SERVICE_UUID.lower() in [u.lower() for u in uuids]:
            matched = True
        if "54524145" in str(uuids).upper():
            matched = True

        entry = {
            "address": dev.address,
            "name": name or "(unnamed)",
            "rssi": adv.rssi,
            "service_uuids": list(uuids),
            "manufacturer": {hex(k): (v.hex() if isinstance(v, bytes) else str(v)) for k, v in mf.items()},
            "matched": matched,
        }
        all_devs.append(entry)
        if matched:
            hits.append(entry)
        if verbose:
            mark = "🎯" if matched else "  "
            print(f"  {mark} {dev.address}  name={name or '-':20s}  rssi={adv.rssi}  services={len(uuids)}")

    # 如果一个明确命中都没有 → 用 RSSI 最强且名字看起来像 SN/ESP32 的作为候选
    if not hits:
        # 取信号最强的 1-2 台
        candidates = sorted(
            [d for d in all_devs if d.get("name") not in ("", "(unnamed)", "-")],
            key=lambda d: d.get("rssi", -200), reverse=True,
        )[:1]
        hits = candidates
        if hits and verbose:
            print(f"\n⚠️  无明确匹配 — 用信号最强的设备作候选: {hits[0]['name']} rssi={hits[0]['rssi']}")

    print(f"\n✅ 找到 {len(hits)} 台候选设备")
    return hits


async def connect(address: Optional[str] = None, timeout: float = 10.0):
    """连接 + 发现 Service + 订阅 Notify"""
    global _ble_client, _connected_address
    from bleak import BleakClient

    # 在当前 event loop 里初始化 queue (解决跨 loop 共享问题)
    _ensure_queues()
    assert _ack_queue is not None

    # 如果没给地址, 先扫一下取第一个 FoloToy
    if not address:
        hits = await scan(timeout=8.0, verbose=False)
        if not hits:
            raise RuntimeError("没扫到 FoloToy 设备, 请确认设备已通电 + BLE 广播开着")
        address = hits[0]["address"]
        print(f"🎯 自动选择设备: {hits[0]['name']} @ {address}")

    print(f"🔗 连接 {address} ...")
    _ble_client = BleakClient(address, timeout=timeout)
    try:
        await _ble_client.connect()
    except Exception as e:
        raise RuntimeError(f"连接失败: {e}") from e

    _connected_address = address
    print(f"  ✅ 已连接")

    # 发现所有 Service / Characteristic
    print(f"🔎 发现 Service + Characteristic ...")
    services = _ble_client.services
    found_chars: dict[str, str] = {}   # idx → uuid
    for svc in services:
        print(f"  Service {svc.uuid}  ({svc.description})")
        for ch in svc.characteristics:
            # 从 UUID 里提 idx: 54524145-4341-5244-XXXX-000000000000
            short = ch.uuid.split('-')[2] if '-' in ch.uuid else ""
            props = ",".join(ch.properties)
            name = {
                CHAR_WRITE:      "WRITE (0x10)",
                CHAR_ACK_NOTIFY: "ACK_NOTIFY (0x11)",
                CHAR_IDENTITY:   "IDENTITY (0x12)",
                CHAR_STATE:      "STATE (0x13)",
                CHAR_MIC_NOTIFY: "MIC_NOTIFY (0x14)",
            }.get(ch.uuid, f"?(0x{short})")
            print(f"    Char {ch.uuid}  props={props}  → {name}")
            found_chars[short] = ch.uuid

    # 订阅 ACK Notify (0x11)
    if CHAR_ACK_NOTIFY in [c.uuid for s in services for c in s.characteristics]:
        await _ble_client.start_notify(CHAR_ACK_NOTIFY, _on_ack)
        print(f"  ✅ 已订阅 0x11 ACK Notify")
    else:
        print(f"  ⚠️  没找到 0x11 ACK Notify")

    # 订阅 MIC Notify (0x14) — 保留
    if CHAR_MIC_NOTIFY in [c.uuid for s in services for c in s.characteristics]:
        await _ble_client.start_notify(CHAR_MIC_NOTIFY, _on_mic)
        print(f"  ✅ 已订阅 0x14 MIC Notify (保留)")

    return _ble_client


async def disconnect():
    """断开连接"""
    global _ble_client, _connected_address, _ack_queue, _mic_queue
    if _ble_client and _ble_client.is_connected:
        try:
            await _ble_client.stop_notify(CHAR_ACK_NOTIFY)
        except Exception:
            pass
        try:
            await _ble_client.disconnect()
        except Exception:
            pass
    _ble_client = None
    _connected_address = None
    _ack_queue = None   # 重置, 下次 connect 在正确 loop 里重建
    _mic_queue = None
    print("🔌 已断开")


# ═══════════════════════════════════════════════════════════
# 低层写 + 等 ACK
# ═══════════════════════════════════════════════════════════

async def _write_and_wait_ack(
    payload: bytes,
    use_write_no_resp: bool = True,
    ack_timeout: float = 3.0,
    expected_ack: Optional[bytes] = None,
) -> tuple[bool, Optional[bytes]]:
    """
    往 0x10 写 payload, 然后等 0x11 的 ACK.
    返回 (ok, ack_bytes). ok=False 表示超时或设备回 ERR.
    """
    assert _ble_client and _ble_client.is_connected, "BLE 未连接"
    assert _ack_queue is not None, "ACK queue 未初始化 — 需先 connect()"
    # 清空残留 ACK
    while not _ack_queue.empty():
        try:
            _ack_queue.get_nowait()
        except asyncio.QueueEmpty:
            break

    write_method = _ble_client.write_gatt_char
    try:
        await write_method(
            CHAR_WRITE,
            payload,
            response=not use_write_no_resp,
        )
    except Exception as e:
        return False, None

    # 等 ACK
    try:
        ack = await asyncio.wait_for(_ack_queue.get(), timeout=ack_timeout)
    except asyncio.TimeoutError:
        return False, None

    # 判断 OK / ERR
    if ack == ACK_ERR:
        return False, ack
    if expected_ack and ack != expected_ack:
        # 不是我们期待的, 但也不一定是错 — 返回 true 让调用方判断
        return True, ack
    return True, ack


# ═══════════════════════════════════════════════════════════
# 高层方法 — 命令 / 文本 / 音频 / 状态
# ═══════════════════════════════════════════════════════════

async def send_command(cmd_name: str, ack_timeout: float = 3.0) -> dict:
    """发送预定义命令, 返回 {ok, ack, ack_desc}"""
    frame = COMMAND_SET.get(cmd_name)
    if frame is None:
        return {"ok": False, "error": f"未知命令: {cmd_name}"}
    ok, ack = await _write_and_wait_ack(frame, ack_timeout=ack_timeout)
    return {
        "ok": ok,
        "cmd": cmd_name,
        "frame": frame.hex(),
        "ack": ack.hex() if ack else None,
        "ack_desc": _ack_to_str(ack) if ack else "NO_ACK",
    }


async def send_text(text: str, ack_timeout: float = 3.0) -> dict:
    """
    发送纯文本 — BLE 通道就是纯文本命令通道, 直接写字符串 + \r\n 即可.
    设备会回 ACK_OK (00 10). 固件暂未开放 TTS, 文本内容会被当作命令解析.
    """
    frame = text.encode("utf-8") + b"\r\n"
    # 如果太长 (超过 BLE MTU 安全值 17B), bleak 会自动分片 write
    ok, ack = await _write_and_wait_ack(frame, ack_timeout=ack_timeout)
    return {
        "ok": ok,
        "text": text,
        "frame_size": len(frame),
        "ack": ack.hex() if ack else None,
        "ack_desc": _ack_to_str(ack) if ack else "NO_ACK",
    }


async def send_audio_pcm(pcm_data: bytes, sample_rate: int = 16000,
                          bits_per_sample: int = 16, channels: int = 1) -> dict:
    """
    发送 PCM 音频流 — 已逆向的 BLE GATT 音频通路 (100% 验证通过)

    协议:
      Step 1: I2S 配置帧 (type=0x01, len=4, [rate_hi, rate_lo, bits, channels])
              → 期待 0x15 AUDIO_READY
      Step 2: 裸 PCM 分片 (17B/片, WRITE_NO_RESP) — 每片 ESP32 回 0x10 OK
      Step 3: 音频结束 — 等几秒让设备播放完, 无显式 stop 帧

    实测: 3764 片 × 17B = 64KB PCM, ESP32 回 3224× ACK_OK (0 错误!)
          → BLE 音频通路 100% 打通

    注意: ESP32-C3 RAM 68KB + BLE ~5-6KB/s, 适合 < 2s 音频.
    """
    result: dict = {"ok": False, "packets_sent": 0, "bytes_sent": 0}
    assert _ble_client and _ble_client.is_connected, "BLE 未连接"

    # Step 1: I2S 配置帧
    # type=0x01 是音频控制帧, len=4, 后面紧跟 4B I2S 参数
    # rate 用 16 表示 16kHz (协议是 nibble), bits=16, channels=1
    i2s_cfg = bytes([
        0x01,                          # type = 音频控制
        0x04,                          # len  = 4B payload
        (sample_rate >> 8) & 0xFF,     # rate hi
        sample_rate & 0xFF,            # rate lo
        bits_per_sample,               # bits per sample
        channels,                      # channels
    ])
    result["i2s_cfg"] = i2s_cfg.hex()

    start_ok, start_ack = await _write_and_wait_ack(
        i2s_cfg, expected_ack=ACK_AUDIO_READY, ack_timeout=5.0)
    result["start_ok"] = start_ok
    result["start_ack"] = start_ack.hex() if start_ack else None

    if not start_ok:
        result["error"] = f"I2S cfg 失败, 未回 0x15 AUDIO_READY (ack={result['start_ack']})"
        return result

    # 等 ES8311 I2S codec 初始化
    await asyncio.sleep(0.5)

    # Step 2: 分片写裸 PCM — WRITE_NO_RESP, 节流 3ms/片
    chunk_size = BLE_PAYLOAD_SIZE   # 17B (BLE MTU 20 - 3 字节 ATT header)
    n = len(pcm_data)
    sent = 0
    pkts = 0
    try:
        for i in range(0, n, chunk_size):
            chunk = pcm_data[i:i+chunk_size]
            await _ble_client.write_gatt_char(CHAR_WRITE, chunk, response=False)
            sent += len(chunk)
            pkts += 1
            await asyncio.sleep(0.003)  # 3ms 节流 ~5.6KB/s, 稳定
        await asyncio.sleep(1.0)  # 等 ESP32 处理完最后一包 + 播放
    except Exception as e:
        result["error"] = f"PCM 写入出错: {e}"
        result["packets_sent"] = pkts
        result["bytes_sent"] = sent
        return result

    result["packets_sent"] = pkts
    result["bytes_sent"] = sent
    result["ok"] = True
    result["note"] = "BLE PCM 流发送完成, 设备应已播放"
    return result


async def read_identity() -> dict:
    """读 0x12 — 设备身份 (SN + Token + 固件版本)"""
    assert _ble_client and _ble_client.is_connected, "BLE 未连接"
    try:
        raw = await _ble_client.read_gatt_char(CHAR_IDENTITY)
    except Exception as e:
        return {"ok": False, "error": f"read_identity 失败: {e}"}
    text = raw.decode("utf-8", errors="replace").strip("\x00 ")
    info: dict = {"raw": raw.hex(), "text": text}
    # 尝试解析成 key=value
    for seg in text.replace(";", ",").split(","):
        if "=" in seg:
            k, v = seg.split("=", 1)
            info[k.strip().lower()] = v.strip()
    return {"ok": True, **info}


async def read_state() -> dict:
    """读 0x13 — 运行状态"""
    assert _ble_client and _ble_client.is_connected, "BLE 未连接"
    try:
        raw = await _ble_client.read_gatt_char(CHAR_STATE)
    except Exception as e:
        return {"ok": False, "error": f"read_state 失败: {e}"}
    text = raw.decode("utf-8", errors="replace").strip("\x00 ")
    info: dict = {"raw": raw.hex(), "text": text}
    for seg in text.replace(";", ",").split(","):
        if "=" in seg:
            k, v = seg.split("=", 1)
            info[k.strip().lower()] = v.strip()
    return {"ok": True, **info}


# ═══════════════════════════════════════════════════════════
# 完整流程 — play_passport_report
# ═══════════════════════════════════════════════════════════

def _collect_andromeda_report() -> dict:
    """从仙女座 DB 聚合最新升级/开发活动"""
    import sqlite3
    info: dict = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "items": []}
    db_path = Path(__file__).parent.parent / "database" / "app.db"
    if not db_path.exists():
        info["db"] = "not found"
        return info
    db = sqlite3.connect(str(db_path))
    try:
        try:
            rows = db.execute(
                "SELECT process_name, status FROM mt_daemon_registry WHERE status='RUNNING' ORDER BY process_name"
            ).fetchall()
            info["daemon_running"] = len(rows)
            info["daemon_total"] = db.execute(
                "SELECT COUNT(*) FROM mt_daemon_registry"
            ).fetchone()[0]
        except Exception: pass

        try:
            rows = db.execute(
                "SELECT rule_id, to_version, change_type, created_at FROM mt_rule_changelog ORDER BY created_at DESC LIMIT 3"
            ).fetchall()
            info["rule_changes"] = [f"{r[0]}→{r[1]} {r[2]}" for r in rows]
        except Exception: pass

        try:
            info["ai_employees_andromeda"] = db.execute(
                "SELECT COUNT(*) FROM mt_andromeda_employee_registry "
                "WHERE employee_source NOT IN ('eigenflux','arduino_employees.py')"
            ).fetchone()[0]
        except Exception: pass
    finally:
        db.close()
    return info


def _format_report(report: dict) -> str:
    lines = [f"仙女座报告 {report['time']}"]
    if report.get("daemon_running") is not None:
        lines.append(f"运行中 Daemon {report['daemon_running']}/{report.get('daemon_total','?')}")
    if report.get("ai_employees_andromeda"):
        lines.append(f"AI员工 {report['ai_employees_andromeda']} 位")
    if report.get("rule_changes"):
        lines.append(f"规则变更: {', '.join(report['rule_changes'][:2])}")
    return " | ".join(lines)


async def play_passport_report(message: Optional[str] = None,
                               beep_pattern: str = "report_ok") -> dict:
    """
    完整流程:
      1. 确保连接
      2. 读 0x12/0x13 确认设备在线
      3. 触发 report_ok 蜂鸣 (双音叮咚)
      4. 发文本命令 (type=0x05) — 固件暂不支持 TTS, 但帧先打通
      5. 返回完整结果
    """
    summary: dict = {}

    # 确保已连接
    if not _ble_client or not _ble_client.is_connected:
        await connect()

    # 读身份 + 状态
    identity = await read_identity()
    state = await read_state()
    summary["identity"] = identity
    summary["state"] = state
    if not identity.get("ok"):
        summary["ok"] = False
        summary["error"] = f"设备身份读取失败: {identity}"
        return summary

    # 蜂鸣提示
    beep_res = await send_command(beep_pattern)
    summary["beep"] = beep_res
    if not beep_res.get("ok"):
        summary["warning"] = f"蜂鸣命令未得到 OK ACK: {beep_res}"

    # 发文本 (如果提供)
    if message:
        text_res = await send_text(message)
        summary["text"] = text_res

    summary["ok"] = True
    summary["time"] = datetime.now().isoformat()
    return summary


# ═══════════════════════════════════════════════════════════
# 同步包装 — 方便在 asyncio 外调用
# ═══════════════════════════════════════════════════════════

def run_sync(coro):
    """在当前线程执行协程 (兼容已有 event loop)"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 已有 loop 在跑 (比如 Flask with gunicorn) — 用 nest_asyncio
            try:
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(coro)
            except ImportError:
                # 没装 nest_asyncio — 起新 loop
                return asyncio.new_event_loop().run_until_complete(coro)
    except RuntimeError:
        pass
    return asyncio.run(coro)


def ble_scan_sync(timeout: float = 6.0) -> list[dict]:
    return run_sync(scan(timeout))


def ble_connect_sync(address: Optional[str] = None) -> None:
    run_sync(connect(address))


def ble_disconnect_sync() -> None:
    run_sync(disconnect())


def ble_send_command_sync(cmd: str) -> dict:
    async def _do():
        if not _ble_client or not _ble_client.is_connected:
            await connect()
        return await send_command(cmd)
    return run_sync(_do())


def ble_status_sync() -> dict:
    async def _do():
        if not _ble_client or not _ble_client.is_connected:
            await connect()
        ident = await read_identity()
        state = await read_state()
        return {"identity": ident, "state": state}
    return run_sync(_do())


def ble_report_sync(message: Optional[str] = None) -> dict:
    async def _do():
        # 自动收集仙女座报告
        if message is None:
            msg = _format_report(_collect_andromeda_report())
        else:
            msg = message
        return await play_passport_report(msg)
    return run_sync(_do())


# ═══════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════

def _print_hex_frame(frame: bytes, label: str = "TX") -> None:
    print(f"  {label}: {frame.hex()}  ({len(frame)}B)")


def main():
    ap = argparse.ArgumentParser(description="🧊 FoloToy AI Passport BLE 桥接器")
    ap.add_argument("action", nargs="?", default="scan",
                    choices=["scan", "connect", "disconnect", "status",
                             "beep", "beep-long", "beep-sos", "beep-chime",
                             "text", "report", "report-err", "boot", "shutdown",
                             "volume-up", "volume-down", "volume-max", "mute",
                             "reboot", "identify", "wifi-test", "pcm-test",
                             "commands"])
    ap.add_argument("payload", nargs="?", help="text 要发的文本, 或 pcm-test 的秒数")
    ap.add_argument("--address", "-a", help="指定设备地址 (如 AA:BB:CC:DD:EE:FF)")
    ap.add_argument("--timeout", "-t", type=float, default=6.0, help="扫描超时 (秒)")
    ap.add_argument("--no-disconnect", action="store_true", help="执行完后不断开 (保留连接)")
    args = ap.parse_args()

    # 打印所有可用命令
    if args.action == "commands":
        print("\n📋 可用 BLE 命令集:")
        for name, frame in COMMAND_SET.items():
            print(f"  {name:14s} → {frame.hex()}")
        print(f"\n  text 'xxx'     → 自动组装 type=0x05+len+UTF8")
        print(f"  pcm-test [sec] → 生成 sine wave PCM 并尝试发送")
        return

    async def run():
        # scan 是独立的, 不需要连接
        if args.action == "scan":
            hits = await scan(timeout=args.timeout)
            return hits

        # 所有其他 action → 先 connect
        await connect(args.address, timeout=args.timeout * 2)

        try:
            if args.action == "connect":
                ident = await read_identity()
                state = await read_state()
                print(f"\n📋 身份 (0x12): {json.dumps(ident, ensure_ascii=False, indent=2)}")
                print(f"📋 状态 (0x13): {json.dumps(state, ensure_ascii=False, indent=2)}")
                return {"identity": ident, "state": state}

            if args.action == "status":
                ident = await read_identity()
                state = await read_state()
                print(f"\n📋 身份 (0x12):")
                for k, v in ident.items():
                    print(f"   {k}: {v}")
                print(f"\n📋 运行状态 (0x13):")
                for k, v in state.items():
                    print(f"   {k}: {v}")
                return {"identity": ident, "state": state}

            cmd_map = {
                "beep": "beep",
                "beep-long": "beep_long",
                "beep-sos": "beep_sos",
                "beep-chime": "beep_chime",
                "boot": "boot_jingle",
                "shutdown": "shutdown",
                "report-err": "report_err",
                "volume-up": "volume_up",
                "volume-down": "volume_down",
                "volume-max": "volume_max",
                "mute": "volume_mute",
                "reboot": "sys_reboot",
                "identify": "sys_identify",
                "wifi-test": "sys_wifi_test",
            }

            if args.action in cmd_map:
                frame = COMMAND_SET[cmd_map[args.action]]
                _print_hex_frame(frame, "BLE 写入 0x10")
                res = await send_command(cmd_map[args.action])
                print(f"   → ok={res['ok']}  ack={res.get('ack_desc', res.get('ack'))}")
                return res

            if args.action == "text":
                msg = args.payload or "仙女座测试文本"
                frame = bytes([0x05, len(msg.encode())]) + msg.encode()
                _print_hex_frame(frame, f"BLE 写入 0x10 (text={msg})")
                res = await send_text(msg)
                print(f"   → ok={res['ok']}  ack={res.get('ack_desc', res.get('ack'))}")
                return res

            if args.action == "report":
                if args.payload:
                    msg = args.payload
                else:
                    report = _collect_andromeda_report()
                    msg = _format_report(report)
                    print(f"\n📊 仙女座自动报告:\n   {msg}\n")
                print(f"🔔 发送 report_ok 蜂鸣 + 文本...")
                res = await play_passport_report(msg)
                print(json.dumps(res, ensure_ascii=False, indent=2))
                return res

            if args.action == "pcm-test":
                # 生成一段 1kHz sine wave, 16bit mono 16kHz
                import math, struct as _st
                secs = float(args.payload or "0.5")
                sr = 16000
                n = int(sr * secs)
                pcm = bytearray()
                for i in range(n):
                    v = int(0.25 * 32767 * math.sin(2 * math.pi * 1000 * i / sr))
                    pcm += _st.pack("<h", v)
                print(f"🎵 生成 1kHz sine wave: {secs}s, {len(pcm)}B")
                res = await send_audio_pcm(bytes(pcm))
                print(json.dumps(res, ensure_ascii=False, indent=2))
                return res

            if args.action == "disconnect":
                return {"ok": True}

        finally:
            if not args.no_disconnect:
                await disconnect()

    try:
        result = asyncio.run(run())
        if result is not None:
            print(f"\n✅ 完成 → {json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, dict) else result}")
    except KeyboardInterrupt:
        print("\n🛑 Ctrl+C, 退出")
    except Exception as e:
        print(f"\n❌ 失败: {type(e).__name__}: {e}")
        if os.environ.get("DEBUG"):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
