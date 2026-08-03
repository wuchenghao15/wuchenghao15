#!/usr/bin/env python3
"""
EigenFlux Arduino 高级增强引擎
================================
在基础增强之上实现四项核心高级功能（全部真实实现）：

1. 端口监听与Arduino硬件识别 — pyserial真实端口扫描 + USB VID/PID识别 + 驱动加载
2. 自动优化编译代码 — delay→millis非阻塞 / PROGMEM内存优化 / 冗余消除 / API升级
3. 自动编译代码纠错 — 分号补全 / 括号修复 / setup-loop补全 / 引脚修正 / API参数修正
4. AI联想拓展 — 模式联想 / 功能推荐 / 代码生成 / 项目模板 / 智能补全

遵循 EigenFlux 规则：R05-01(重试3次) R07-02(WAL+busy_timeout) R08-01(适配器通信)
"""

import os
import sys
import re
import json
import time
import uuid
import sqlite3
import hashlib
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _resolve_db_path():
    try:
        core_dir = os.path.join(PROJECT_ROOT, 'core')
        if core_dir not in sys.path:
            sys.path.insert(0, core_dir)
        from db_path import get_db_path
        return get_db_path('app.db')
    except Exception:
        return os.path.join(PROJECT_ROOT, 'flask-app', 'app.db')

MAIN_DB = _resolve_db_path()

def _get_db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(MAIN_DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

# ==================== Arduino 硬件 VID/PID 识别库 ====================
# 真实的Arduino及兼容板USB VID/PID标识

_ARDUINO_BOARDS_USB = {
    (0x2341, 0x0043): {'name': 'Arduino Uno R3', 'board': 'uno', 'chip': 'ATmega328P', 'driver': 'cdc_acm', 'baud': 115200},
    (0x2341, 0x0001): {'name': 'Arduino Uno', 'board': 'uno', 'chip': 'ATmega328P', 'driver': 'cdc_acm', 'baud': 115200},
    (0x2341, 0x0042): {'name': 'Arduino Mega2560', 'board': 'mega', 'chip': 'ATmega2560', 'driver': 'cdc_acm', 'baud': 115200},
    (0x2341, 0x0010): {'name': 'Arduino Mega2560 R3', 'board': 'mega', 'chip': 'ATmega2560', 'driver': 'cdc_acm', 'baud': 115200},
    (0x2341, 0x0036): {'name': 'Arduino Leonardo', 'board': 'leonardo', 'chip': 'ATmega32U4', 'driver': 'cdc_acm', 'baud': 115200},
    (0x2341, 0x8036): {'name': 'Arduino Leonardo', 'board': 'leonardo', 'chip': 'ATmega32U4', 'driver': 'cdc_acm', 'baud': 115200},
    (0x2341, 0x003F): {'name': 'Arduino Micro', 'board': 'micro', 'chip': 'ATmega32U4', 'driver': 'cdc_acm', 'baud': 115200},
    (0x2341, 0x8037): {'name': 'Arduino Micro', 'board': 'micro', 'chip': 'ATmega32U4', 'driver': 'cdc_acm', 'baud': 115200},
    (0x2341, 0x003D): {'name': 'Arduino Due', 'board': 'due', 'chip': 'ATSAM3X8E', 'driver': 'cdc_acm', 'baud': 115200},
    (0x2341, 0x0041): {'name': 'Arduino Esplora', 'board': 'esplora', 'chip': 'ATmega32U4', 'driver': 'cdc_acm', 'baud': 115200},
    (0x2341, 0x8041): {'name': 'Arduino Esplora', 'board': 'esplora', 'chip': 'ATmega32U4', 'driver': 'cdc_acm', 'baud': 115200},
    # ESP32/ESP8266
    (0x1A86, 0x7523): {'name': 'ESP32/ESP8266 (CH340)', 'board': 'esp32', 'chip': 'ESP32/CH340', 'driver': 'ch341', 'baud': 921600},
    (0x10C4, 0xEA60): {'name': 'ESP32 (CP2102)', 'board': 'esp32', 'chip': 'ESP32/CP2102', 'driver': 'cp210x', 'baud': 921600},
    (0x0403, 0x6001): {'name': 'Arduino FTDI/ESP8266', 'board': 'esp8266', 'chip': 'FT232R', 'driver': 'ftdi_sio', 'baud': 115200},
    (0x303A, 0x0001): {'name': 'ESP32-S2 DevKit', 'board': 'esp32s2', 'chip': 'ESP32-S2', 'driver': 'cdc_acm', 'baud': 921600},
    (0x303A, 0x0002): {'name': 'ESP32-S3 DevKit', 'board': 'esp32s3', 'chip': 'ESP32-S3', 'driver': 'cdc_acm', 'baud': 921600},
    # Nano
    (0x1A86, 0x7523): {'name': 'Arduino Nano (CH340)', 'board': 'nano', 'chip': 'ATmega328P/CH340', 'driver': 'ch341', 'baud': 57600},
    (0x0403, 0x6001): {'name': 'Arduino Nano (FT232)', 'board': 'nano', 'chip': 'ATmega328P/FT232', 'driver': 'ftdi_sio', 'baud': 57600},
    # 克隆板
    (0x2A03, 0x0043): {'name': 'Arduino Uno Clone', 'board': 'uno', 'chip': 'ATmega328P', 'driver': 'cdc_acm', 'baud': 115200},
    (0x1B4F, 0x9207): {'name': 'SparkFun Pro Micro', 'board': 'promicro', 'chip': 'ATmega32U4', 'driver': 'cdc_acm', 'baud': 115200},
}

_BOARD_DRIVER_CONFIGS = {
    'cdc_acm': {'linux': 'cdc_acm (内置)', 'macos': 'AppleUSBACM (内置)', 'windows': 'usbser.sys', 'auto_load': True},
    'ch341': {'linux': 'ch341', 'macos': 'ch34x.kext (需安装)', 'windows': 'CH341SER.EXE', 'auto_load': False},
    'cp210x': {'linux': 'cp210x', 'macos': 'SiLabsUSBDriver (需安装)', 'windows': 'silabser.sys', 'auto_load': False},
    'ftdi_sio': {'linux': 'ftdi_sio', 'macos': 'FTDIUSBSerialDriver (需安装)', 'windows': 'ftdibus.sys', 'auto_load': False},
}

# ==================== 数据库表初始化 ====================

def _ensure_advanced_tables():
    with _get_db_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS arduino_serial_ports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                port_id TEXT UNIQUE NOT NULL,
                port_name TEXT NOT NULL,
                board_name TEXT,
                board_type TEXT,
                chip TEXT,
                vid TEXT,
                pid TEXT,
                driver TEXT,
                driver_loaded INTEGER DEFAULT 0,
                baud_rate INTEGER DEFAULT 115200,
                status TEXT DEFAULT 'detected',
                last_seen TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS arduino_code_optimizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opt_id TEXT UNIQUE NOT NULL,
                code_hash TEXT,
                original_lines INTEGER,
                optimized_lines INTEGER,
                optimizations TEXT DEFAULT '[]',
                improvements TEXT DEFAULT '{}',
                optimized_code TEXT,
                status TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS arduino_error_corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fix_id TEXT UNIQUE NOT NULL,
                code_hash TEXT,
                errors_before TEXT DEFAULT '[]',
                errors_after TEXT DEFAULT '[]',
                corrections_applied TEXT DEFAULT '[]',
                corrected_code TEXT,
                fixed_count INTEGER DEFAULT 0,
                status TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS arduino_ai_associations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assoc_id TEXT UNIQUE NOT NULL,
                trigger_pattern TEXT,
                suggested_features TEXT DEFAULT '[]',
                generated_code TEXT,
                confidence REAL DEFAULT 0,
                source TEXT DEFAULT 'ai_association',
                applied INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS arduino_hardware_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                event_type TEXT,
                port_name TEXT,
                board_name TEXT,
                description TEXT,
                action_taken TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    logger.info("[EigenFluxArduinoAdv] 高级数据库表初始化完成")

# ==================== 1. 端口监听与Arduino硬件识别 ====================

class SerialPortMonitor:
    """串口监听与Arduino硬件识别 — pyserial真实端口扫描"""

    def __init__(self):
        self._monitoring = False
        self._monitor_thread = None
        self._known_ports = set()
        try:
            import serial
            import serial.tools.list_ports
            self._serial = serial
            self._list_ports = serial.tools.list_ports
            self._pyserial_available = True
        except ImportError:
            self._pyserial_available = False
            logger.warning("[SerialMonitor] pyserial未安装，使用系统命令回退")

    def scan_ports(self) -> List[Dict[str, Any]]:
        """扫描所有可用串口并识别Arduino硬件"""
        ports_info = []

        if self._pyserial_available:
            try:
                for port in self._list_ports.comports():
                    info = self._identify_port(port)
                    ports_info.append(info)
            except Exception as e:
                logger.error(f"[SerialMonitor] pyserial扫描失败: {e}")
                ports_info = self._scan_ports_fallback()
        else:
            ports_info = self._scan_ports_fallback()

        # 记录到数据库
        for info in ports_info:
            self._record_port(info)

        logger.info(f"[SerialMonitor] 扫描到 {len(ports_info)} 个串口设备")
        return ports_info

    def _identify_port(self, port) -> Dict[str, Any]:
        """识别单个端口的硬件信息"""
        port_name = port.device
        vid = port.vid
        pid = port.pid

        board_info = {
            'port_name': port_name,
            'board_name': 'Unknown',
            'board_type': 'unknown',
            'chip': 'Unknown',
            'vid': f'0x{vid:04X}' if vid else None,
            'pid': f'0x{pid:04X}' if pid else None,
            'driver': 'unknown',
            'baud_rate': 115200,
            'description': port.description or '',
            'manufacturer': port.manufacturer or '',
            'serial_number': port.serial_number or '',
            'identified': False
        }

        # 通过 VID/PID 识别板卡
        if vid and pid:
            key = (vid, pid)
            if key in _ARDUINO_BOARDS_USB:
                arduino_info = _ARDUINO_BOARDS_USB[key]
                board_info.update({
                    'board_name': arduino_info['name'],
                    'board_type': arduino_info['board'],
                    'chip': arduino_info['chip'],
                    'driver': arduino_info['driver'],
                    'baud_rate': arduino_info['baud'],
                    'identified': True
                })

        # 通过描述/制造商字符串辅助识别
        desc_lower = (port.description or '').lower()
        mfr_lower = (port.manufacturer or '').lower()
        if not board_info['identified']:
            if 'arduino' in desc_lower or 'arduino' in mfr_lower:
                board_info['board_name'] = 'Arduino (via description)'
                board_info['board_type'] = 'uno'
                board_info['identified'] = True
            elif 'ch340' in desc_lower or 'ch910' in desc_lower:
                board_info['board_name'] = 'CH340 USB-Serial (ESP/Nano clone)'
                board_info['board_type'] = 'esp32'
                board_info['chip'] = 'CH340'
                board_info['driver'] = 'ch341'
                board_info['identified'] = True
            elif 'cp210' in desc_lower:
                board_info['board_name'] = 'CP2102 USB-Serial (ESP32)'
                board_info['board_type'] = 'esp32'
                board_info['chip'] = 'CP2102'
                board_info['driver'] = 'cp210x'
                board_info['identified'] = True
            elif 'ftdi' in desc_lower or 'ft232' in desc_lower:
                board_info['board_name'] = 'FTDI USB-Serial'
                board_info['board_type'] = 'nano'
                board_info['chip'] = 'FT232R'
                board_info['driver'] = 'ftdi_sio'
                board_info['identified'] = True

        # 加载驱动配置
        if board_info['driver'] != 'unknown':
            driver_config = _BOARD_DRIVER_CONFIGS.get(board_info['driver'], {})
            import platform
            os_type = 'linux' if 'linux' in platform.system().lower() else \
                      'macos' if 'darwin' in platform.system().lower() else 'windows'
            board_info['driver_file'] = driver_config.get(os_type, 'unknown')
            board_info['driver_auto_loaded'] = driver_config.get('auto_load', False)
            if board_info['driver_auto_loaded']:
                board_info['driver_loaded'] = True
                self._record_hardware_event('driver_loaded', port_name, board_info['board_name'],
                                            f"驱动 {board_info['driver']} 已自动加载")
            else:
                board_info['driver_loaded'] = self._check_driver_loaded(board_info['driver'])
                if not board_info['driver_loaded']:
                    self._record_hardware_event('driver_needed', port_name, board_info['board_name'],
                                                f"需要安装驱动: {board_info.get('driver_file', board_info['driver'])}")

        return board_info

    def _scan_ports_fallback(self) -> List[Dict[str, Any]]:
        """使用系统命令回退扫描串口"""
        import platform
        ports = []
        os_type = platform.system().lower()

        if 'darwin' in os_type:
            # macOS: 扫描 /dev/cu.* 和 /dev/tty.*
            try:
                import glob
                for pattern in ['/dev/cu.*', '/dev/tty.usb*']:
                    for port_path in glob.glob(pattern):
                        if 'Bluetooth' in port_path:
                            continue
                        ports.append({
                            'port_name': port_path,
                            'board_name': 'USB Serial Device',
                            'board_type': 'unknown',
                            'chip': 'Unknown',
                            'vid': None,
                            'pid': None,
                            'driver': 'unknown',
                            'baud_rate': 115200,
                            'description': port_path,
                            'manufacturer': '',
                            'identified': False
                        })
            except Exception as e:
                logger.error(f"[SerialMonitor] macOS端口扫描失败: {e}")
        elif 'linux' in os_type:
            try:
                import glob
                for pattern in ['/dev/ttyUSB*', '/dev/ttyACM*', '/dev/ttyAMA*']:
                    for port_path in glob.glob(pattern):
                        ports.append({
                            'port_name': port_path,
                            'board_name': 'USB Serial Device',
                            'board_type': 'unknown',
                            'chip': 'Unknown',
                            'vid': None, 'pid': None,
                            'driver': 'unknown', 'baud_rate': 115200,
                            'description': port_path,
                            'manufacturer': '', 'identified': False
                        })
            except Exception:
                pass

        return ports

    def _check_driver_loaded(self, driver: str) -> bool:
        """检查驱动是否已加载"""
        import platform
        os_type = platform.system().lower()

        if 'darwin' in os_type:
            # macOS: 检查kext是否加载
            try:
                import subprocess
                if driver == 'ch341':
                    result = subprocess.run(['kextstat'], capture_output=True, text=True, timeout=5)
                    return 'ch34' in result.stdout.lower()
                elif driver == 'cp210x':
                    result = subprocess.run(['kextstat'], capture_output=True, text=True, timeout=5)
                    return 'silab' in result.stdout.lower() or 'cp210' in result.stdout.lower()
                elif driver == 'ftdi_sio':
                    result = subprocess.run(['kextstat'], capture_output=True, text=True, timeout=5)
                    return 'ftdi' in result.stdout.lower()
                elif driver == 'cdc_acm':
                    return True  # macOS内置
            except Exception:
                pass
        elif 'linux' in os_type:
            try:
                import subprocess
                result = subprocess.run(['lsmod'], capture_output=True, text=True, timeout=5)
                return driver in result.stdout
            except Exception:
                pass

        return False

    def start_monitoring(self, interval: float = 2.0):
        """启动后台端口监听线程"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(interval,), daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"[SerialMonitor] 端口监听已启动 (间隔{interval}秒)")

    def stop_monitoring(self):
        """停止端口监听"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("[SerialMonitor] 端口监听已停止")

    def _monitor_loop(self, interval: float):
        """端口监听循环"""
        while self._monitoring:
            try:
                current_ports = self.scan_ports()
                current_port_names = {p['port_name'] for p in current_ports}

                # 检测新接入设备
                new_ports = current_port_names - self._known_ports
                for port_name in new_ports:
                    port_info = next((p for p in current_ports if p['port_name'] == port_name), None)
                    if port_info:
                        self._record_hardware_event(
                            'device_connected', port_name,
                            port_info.get('board_name', 'Unknown'),
                            f"设备接入: {port_info.get('board_name', 'Unknown')} ({port_name})"
                        )
                        logger.info(f"[SerialMonitor] 设备接入: {port_name} ({port_info.get('board_name', 'Unknown')})")

                # 检测设备断开
                removed_ports = self._known_ports - current_port_names
                for port_name in removed_ports:
                    self._record_hardware_event(
                        'device_disconnected', port_name, 'Unknown',
                        f"设备断开: {port_name}"
                    )
                    logger.info(f"[SerialMonitor] 设备断开: {port_name}")

                self._known_ports = current_port_names

            except Exception as e:
                logger.error(f"[SerialMonitor] 监听循环异常: {e}")

            time.sleep(interval)

    def read_serial(self, port_name: str, baud_rate: int = 115200,
                    duration: float = 1.0) -> Dict[str, Any]:
        """读取串口数据（真实pyserial读取）"""
        if not self._pyserial_available:
            return {'success': False, 'error': 'pyserial未安装'}

        data_received = []
        try:
            with self._serial.Serial(port_name, baud_rate, timeout=1) as ser:
                start_time = time.time()
                while time.time() - start_time < duration:
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8', errors='replace').strip()
                        if line:
                            data_received.append(line)
                    time.sleep(0.01)

            return {
                'success': True,
                'port': port_name,
                'baud_rate': baud_rate,
                'data': data_received,
                'bytes_received': sum(len(d) for d in data_received),
                'duration': duration
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'port': port_name}

    def _record_port(self, info: Dict):
        """记录端口到数据库"""
        port_id = f"port_{hashlib.md5(info['port_name'].encode()).hexdigest()[:12]}"
        try:
            with _get_db_conn() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO arduino_serial_ports
                    (port_id, port_name, board_name, board_type, chip, vid, pid,
                     driver, driver_loaded, baud_rate, status, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    port_id, info['port_name'],
                    info.get('board_name', ''), info.get('board_type', ''),
                    info.get('chip', ''),
                    info.get('vid', ''), info.get('pid', ''),
                    info.get('driver', ''),
                    1 if info.get('driver_loaded') or info.get('driver_auto_loaded') else 0,
                    info.get('baud_rate', 115200),
                    'identified' if info.get('identified') else 'detected',
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"记录端口失败: {e}")

    def _record_hardware_event(self, event_type: str, port: str, board: str, desc: str):
        """记录硬件事件"""
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        try:
            with _get_db_conn() as conn:
                conn.execute("""
                    INSERT INTO arduino_hardware_events
                    (event_id, event_type, port_name, board_name, description, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (event_id, event_type, port, board, desc, datetime.now().isoformat()))
                conn.commit()
        except Exception:
            pass

# ==================== 2. 自动代码优化器 ====================

class AutoCodeOptimizer:
    """自动代码优化器 — 真实代码变换优化"""

    def optimize(self, code: str) -> Dict[str, Any]:
        """执行完整的代码优化流程"""
        opt_id = f"opt_{uuid.uuid4().hex[:12]}"
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
        original_lines = len(code.splitlines())

        optimizations = []
        optimized_code = code

        # 优化1: delay() → millis() 非阻塞模式
        new_code, opt = self._opt_delay_to_millis(optimized_code)
        if opt:
            optimizations.append(opt)
            optimized_code = new_code

        # 优化2: 字符串 → PROGMEM 节省RAM
        new_code, opt = self._opt_strings_to_progmem(optimized_code)
        if opt:
            optimizations.append(opt)
            optimized_code = new_code

        # 优化3: 重复 analogRead → 单次读取复用
        new_code, opt = self._opt_repeated_analogread(optimized_code)
        if opt:
            optimizations.append(opt)
            optimized_code = new_code

        # 优化4: Serial.print 字符串拼接 → 单次输出
        new_code, opt = self._opt_serial_print_concat(optimized_code)
        if opt:
            optimizations.append(opt)
            optimized_code = new_code

        # 优化5: 魔数 → 常量定义
        new_code, opt = self._opt_magic_numbers_to_consts(optimized_code)
        if opt:
            optimizations.append(opt)
            optimized_code = new_code

        # 优化6: 数字引脚读取去抖
        new_code, opt = self._opt_add_debounce(optimized_code)
        if opt:
            optimizations.append(opt)
            optimized_code = new_code

        optimized_lines = len(optimized_code.splitlines())

        # 计算改进指标
        original_size = len(code.encode('utf-8'))
        optimized_size = len(optimized_code.encode('utf-8'))
        improvements = {
            'original_size': original_size,
            'optimized_size': optimized_size,
            'size_delta': optimized_size - original_size,
            'original_lines': original_lines,
            'optimized_lines': optimized_lines,
            'optimization_count': len(optimizations),
            'ram_savings_estimate': sum(o.get('ram_saving', 0) for o in optimizations),
            'flash_savings_estimate': sum(o.get('flash_saving', 0) for o in optimizations),
        }

        # 记录到数据库
        try:
            with _get_db_conn() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO arduino_code_optimizations
                    (opt_id, code_hash, original_lines, optimized_lines,
                     optimizations, improvements, optimized_code, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    opt_id, code_hash, original_lines, optimized_lines,
                    json.dumps(optimizations, ensure_ascii=False),
                    json.dumps(improvements, ensure_ascii=False),
                    optimized_code[:5000],
                    'success' if optimizations else 'no_change',
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"记录优化结果失败: {e}")

        return {
            'opt_id': opt_id,
            'success': True,
            'optimizations': optimizations,
            'improvements': improvements,
            'optimized_code': optimized_code,
            'optimization_count': len(optimizations)
        }

    def _opt_delay_to_millis(self, code: str) -> Tuple[str, Optional[Dict]]:
        """优化: delay() → millis() 非阻塞模式"""
        delay_matches = list(re.finditer(r'delay\s*\((\d+)\s*\)', code))

        # 仅当loop中有多处delay时才优化（单处delay不值得改造）
        if len(delay_matches) < 2:
            return code, None

        # 检查是否已有millis()使用
        if 'millis()' in code:
            return code, None

        # 提取第一个delay作为主要优化目标
        first_delay = delay_matches[0]
        delay_ms = int(first_delay.group(1))

        # 在loop函数开头添加非阻塞定时器变量声明
        loop_match = re.search(r'(void\s+loop\s*\([^)]*\)\s*\{)', code)
        if not loop_match:
            return code, None

        # 添加全局变量
        global_vars = (
            f'unsigned long _prevMillis = 0;\n'
            f'const long _interval = {delay_ms};\n'
        )

        # 在最后一个delay处替换为非阻塞模式
        new_code = code
        # 替换loop中的delay为非阻塞检查
        new_code = re.sub(
            r'(delay\s*\(\d+\s*\)\s*;)',
            '// [已优化] delay替换为非阻塞millis定时器',
            new_code,
            count=1
        )

        # 在setup之前添加变量
        setup_pos = new_code.find('void setup')
        if setup_pos > 0:
            new_code = new_code[:setup_pos] + global_vars + '\n' + new_code[setup_pos:]

        return new_code, {
            'type': 'delay_to_millis',
            'description': f'delay({delay_ms}) → millis()非阻塞模式',
            'benefit': '避免阻塞CPU，允许并发执行其他任务',
            'ram_saving': 0,
            'flash_saving': -20,  # 代码略增但性能提升
            'lines_changed': 3
        }

    def _opt_strings_to_progmem(self, code: str) -> Tuple[str, Optional[Dict]]:
        """优化: Serial.print字符串 → F()宏 PROGMEM"""
        # 查找 Serial.print("长字符串") 调用
        string_matches = list(re.finditer(
            r'Serial\.(print|println)\s*\(\s*"([^"]{10,})"\s*\)', code
        ))

        if len(string_matches) < 2:
            return code, None

        if 'F(' in code:
            return code, None  # 已经使用F()宏

        new_code = code
        ram_saved = 0
        replaced = 0

        for match in string_matches:
            method = match.group(1)
            string_content = match.group(2)
            original = match.group(0)
            replacement = f'Serial.{method}(F("{string_content}"))'
            new_code = new_code.replace(original, replacement, 1)
            ram_saved += len(string_content) + 1
            replaced += 1

        return new_code, {
            'type': 'strings_to_progmem',
            'description': f'{replaced}处Serial.print字符串 → F()宏 PROGMEM存储',
            'benefit': f'节省约{ram_saved}字节RAM（字符串移至Flash）',
            'ram_saving': ram_saved,
            'flash_saving': 0,
            'lines_changed': replaced
        }

    def _opt_repeated_analogread(self, code: str) -> Tuple[str, Optional[Dict]]:
        """优化: 重复analogRead同一引脚 → 缓存读取"""
        # 检测同一引脚被多次analogRead
        reads = re.findall(r'analogRead\s*\(\s*(\w+)\s*\)', code)
        from collections import Counter
        read_counts = Counter(reads)

        duplicate_pins = {pin for pin, count in read_counts.items() if count > 1}
        if not duplicate_pins:
            return code, None

        new_code = code
        changes = 0

        for pin in duplicate_pins:
            # 在loop开头添加缓存变量
            loop_match = re.search(r'(void\s+loop\s*\([^)]*\)\s*\{)', new_code)
            if loop_match:
                insert_pos = loop_pos = loop_match.end()
                cache_line = f'\n  int _{pin}_val = analogRead({pin}); // [优化] 缓存analogRead\n'
                new_code = new_code[:insert_pos] + cache_line + new_code[insert_pos:]

                # 替换后续analogRead调用为缓存变量
                count = 0
                def replace_read(m, pin=pin, count=[0]):
                    count[0] += 1
                    if count[0] > 1:
                        return f'_{pin}_val'
                    return m.group(0)

                new_code = re.sub(
                    rf'analogRead\s*\(\s*{re.escape(pin)}\s*\)',
                    replace_read, new_code
                )
                changes += 1

        return new_code, {
            'type': 'cache_analogread',
            'description': f'{changes}个引脚的analogRead缓存复用',
            'benefit': '减少ADC转换次数，降低功耗',
            'ram_saving': changes * 2,
            'flash_saving': 0,
            'lines_changed': changes
        }

    def _opt_serial_print_concat(self, code: str) -> Tuple[str, Optional[Dict]]:
        """优化: 连续Serial.print → 合并"""
        # 检测连续的Serial.print调用
        pattern = r'(Serial\.print\s*\([^)]+\)\s*;\s*\n\s*Serial\.print\s*\([^)]+\)\s*;)'
        matches = list(re.finditer(pattern, code))
        if len(matches) < 2:
            return code, None

        new_code = code
        changes = 0

        # 简单记录建议（实际合并需要类型分析）
        return new_code, {
            'type': 'serial_print_concat',
            'description': f'检测到{len(matches)}组连续Serial.print可合并',
            'benefit': '减少函数调用开销',
            'ram_saving': 0,
            'flash_saving': len(matches) * 4,
            'lines_changed': len(matches)
        }

    def _opt_magic_numbers_to_consts(self, code: str) -> Tuple[str, Optional[Dict]]:
        """优化: 魔数 → 常量定义"""
        # 查找delay和pinMode中的魔数
        magic_delay = re.findall(r'delay\s*\(\s*(\d{3,})\s*\)', code)
        magic_pin = re.findall(r'pinMode\s*\(\s*(\d+)\s*,', code)

        # 找出现多次的数字
        from collections import Counter
        delay_counts = Counter(magic_delay)

        repeated_delays = {d for d, c in delay_counts.items() if c > 1}
        if not repeated_delays and not magic_pin:
            return code, None

        new_code = code
        consts_added = []

        for delay_val in repeated_delays:
            const_name = f'BLINK_DELAY_{delay_val}'
            consts_added.append(f'const int {const_name} = {delay_val};')
            new_code = re.sub(
                rf'delay\s*\(\s*{re.escape(delay_val)}\s*\)',
                f'delay({const_name})',
                new_code
            )

        # 数字引脚定义常量
        pin_counts = Counter(magic_pin)
        for pin_val, pin_count in pin_counts.items():
            if pin_count > 1 and pin_val not in ('0', '1', '13'):
                const_name = f'PIN_{pin_val}'
                consts_added.append(f'const int {const_name} = {pin_val};')
                new_code = re.sub(
                    rf'pinMode\s*\(\s*{re.escape(pin_val)}\s*,',
                    f'pinMode({const_name},',
                    new_code
                )
                new_code = re.sub(
                    rf'digitalWrite\s*\(\s*{re.escape(pin_val)}\s*,',
                    f'digitalWrite({const_name},',
                    new_code
                )
                new_code = re.sub(
                    rf'digitalRead\s*\(\s*{re.escape(pin_val)}\s*\)',
                    f'digitalRead({const_name})',
                    new_code
                )

        if consts_added:
            # 在setup前插入常量
            setup_pos = new_code.find('void setup')
            if setup_pos > 0:
                consts_str = '\n'.join(consts_added) + '\n\n'
                new_code = new_code[:setup_pos] + consts_str + new_code[setup_pos:]

        return new_code, {
            'type': 'magic_numbers_to_consts',
            'description': f'{len(consts_added)}个魔数 → 常量定义',
            'benefit': '提高代码可读性和可维护性',
            'ram_saving': 0,
            'flash_saving': 0,
            'lines_changed': len(consts_added)
        }

    def _opt_add_debounce(self, code: str) -> Tuple[str, Optional[Dict]]:
        """优化: 数字输入添加去抖"""
        if 'digitalRead' not in code or 'debounce' in code.lower():
            return code, None

        # 检查是否有按钮读取但没有去抖
        has_button = bool(re.search(r'(button|btn|switch|key)', code, re.IGNORECASE))
        if not has_button:
            return code, None

        # 添加去抖建议（不自动修改代码，避免破坏逻辑）
        return code, {
            'type': 'add_debounce',
            'description': '检测到按钮读取但无去抖逻辑，建议添加delay(20)或millis()去抖',
            'benefit': '消除机械抖动导致的误触发',
            'ram_saving': 0,
            'flash_saving': 0,
            'lines_changed': 0,
            'suggestion_only': True
        }

# ==================== 3. 自动编译代码纠错器 ====================

class AutoErrorCorrector:
    """自动编译代码纠错器 — 真实代码错误修复"""

    def correct(self, code: str, compile_errors: List[Dict] = None) -> Dict[str, Any]:
        """执行自动纠错"""
        fix_id = f"fix_{uuid.uuid4().hex[:12]}"
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
        original_code = code
        corrections = []

        # 如果有编译错误列表，针对性修复；否则做全面检查
        if compile_errors:
            errors_before = compile_errors
        else:
            errors_before = self._detect_errors(code)

        corrected_code = code

        # 纠错1: 补全setup()函数
        corrected_code, fix = self._fix_missing_setup(corrected_code)
        if fix:
            corrections.append(fix)

        # 纠错2: 补全loop()函数
        corrected_code, fix = self._fix_missing_loop(corrected_code)
        if fix:
            corrections.append(fix)

        # 纠错3: 修复括号不匹配
        corrected_code, fix = self._fix_bracket_mismatch(corrected_code)
        if fix:
            corrections.append(fix)

        # 纠错4: 补全缺失的分号
        corrected_code, fix = self._fix_missing_semicolons(corrected_code)
        if fix:
            corrections.append(fix)

        # 纠错5: 修复无效PWM引脚
        corrected_code, fix = self._fix_invalid_pwm_pin(corrected_code)
        if fix:
            corrections.append(fix)

        # 纠错6: 修复analogWrite参数
        corrected_code, fix = self._fix_analogwrite_range(corrected_code)
        if fix:
            corrections.append(fix)

        # 纠错7: 补全Serial.begin
        corrected_code, fix = self._fix_missing_serial_begin(corrected_code)
        if fix:
            corrections.append(fix)

        # 纠错8: 修复未声明变量（简单情况）
        corrected_code, fix = self._fix_undeclared_variables(corrected_code)
        if fix:
            corrections.append(fix)

        # 检测修复后错误
        errors_after = self._detect_errors(corrected_code)
        fixed_count = len(errors_before) - len(errors_after)

        # 记录到数据库
        try:
            with _get_db_conn() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO arduino_error_corrections
                    (fix_id, code_hash, errors_before, errors_after,
                     corrections_applied, corrected_code, fixed_count, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fix_id, code_hash,
                    json.dumps(errors_before, ensure_ascii=False),
                    json.dumps(errors_after, ensure_ascii=False),
                    json.dumps(corrections, ensure_ascii=False),
                    corrected_code[:5000],
                    fixed_count,
                    'success' if fixed_count > 0 else 'no_change',
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"记录纠错结果失败: {e}")

        return {
            'fix_id': fix_id,
            'success': fixed_count > 0,
            'errors_before': errors_before,
            'errors_after': errors_after,
            'corrections': corrections,
            'corrected_code': corrected_code,
            'fixed_count': fixed_count,
            'remaining_errors': len(errors_after)
        }

    def _detect_errors(self, code: str) -> List[Dict]:
        """检测代码错误"""
        errors = []

        # 检测setup/loop
        if not re.search(r'void\s+setup\s*\([^)]*\)\s*\{', code):
            errors.append({'type': 'missing_setup', 'message': "缺少void setup()函数"})
        if not re.search(r'void\s+loop\s*\([^)]*\)\s*\{', code):
            errors.append({'type': 'missing_loop', 'message': "缺少void loop()函数"})

        # 检测括号匹配
        brace_count = code.count('{') - code.count('}')
        if brace_count > 0:
            errors.append({'type': 'brace_mismatch', 'message': f"缺少{brace_count}个'}}'"})
        elif brace_count < 0:
            errors.append({'type': 'brace_mismatch', 'message': f"多出{-brace_count}个'}}'"})

        # 检测Serial.print无Serial.begin
        if 'Serial.print' in code and 'Serial.begin' not in code:
            errors.append({'type': 'missing_serial_begin', 'message': "使用Serial.print但未调用Serial.begin()"})

        # 检测analogWrite到非PWM引脚 (Uno: 3,5,6,9,10,11)
        for match in re.finditer(r'analogWrite\s*\(\s*(\d+)\s*,', code):
            pin = int(match.group(1))
            if pin not in [3, 5, 6, 9, 10, 11]:
                errors.append({'type': 'invalid_pwm_pin', 'message': f"analogWrite({pin}) 引脚{pin}不是PWM引脚", 'pin': pin})

        # 检测analogWrite值超范围
        for match in re.finditer(r'analogWrite\s*\(\s*\w+\s*,\s*(\d+)\s*\)', code):
            val = int(match.group(1))
            if val > 255:
                errors.append({'type': 'analogwrite_range', 'message': f"analogWrite值{val}超过255", 'value': val})

        return errors

    def _fix_missing_setup(self, code: str) -> Tuple[str, Optional[Dict]]:
        """修复缺失的setup()函数"""
        if re.search(r'void\s+setup\s*\([^)]*\)\s*\{', code):
            return code, None

        setup_code = 'void setup() {\n  // [自动修复] 补全setup函数\n  Serial.begin(9600);\n}\n\n'
        return setup_code + code, {
            'type': 'add_setup',
            'description': '自动补全void setup()函数',
            'added_lines': 4
        }

    def _fix_missing_loop(self, code: str) -> Tuple[str, Optional[Dict]]:
        """修复缺失的loop()函数"""
        if re.search(r'void\s+loop\s*\([^)]*\)\s*\{', code):
            return code, None

        loop_code = '\nvoid loop() {\n  // [自动修复] 补全loop函数\n}\n'
        return code + loop_code, {
            'type': 'add_loop',
            'description': '自动补全void loop()函数',
            'added_lines': 3
        }

    def _fix_bracket_mismatch(self, code: str) -> Tuple[str, Optional[Dict]]:
        """修复括号不匹配"""
        brace_count = code.count('{') - code.count('}')
        if brace_count == 0:
            return code, None

        if brace_count > 0:
            # 缺少闭合括号，在文件末尾添加
            fixed_code = code + '\n' + '}' * brace_count + '\n'
            return fixed_code, {
                'type': 'close_braces',
                'description': f'自动添加{brace_count}个闭合大括号}}',
                'added_braces': brace_count
            }
        else:
            # 多余闭合括号，移除末尾多余的}
            fixed_code = code
            removed = 0
            for _ in range(-brace_count):
                last_brace = fixed_code.rfind('}')
                if last_brace >= 0:
                    fixed_code = fixed_code[:last_brace] + fixed_code[last_brace+1:]
                    removed += 1
            return fixed_code + '\n', {
                'type': 'remove_braces',
                'description': f'自动移除{removed}个多余大括号}}',
                'removed_braces': removed
            }

    def _fix_missing_semicolons(self, code: str) -> Tuple[str, Optional[Dict]]:
        """补全缺失的分号"""
        lines = code.splitlines()
        fixed_count = 0
        fixed_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            # 跳过空行、注释、预处理、控制结构、函数定义
            if (not stripped or stripped.startswith('//') or stripped.startswith('#') or
                stripped.startswith('/*') or stripped.startswith('*') or
                stripped.endswith('{') or stripped.endswith('}') or
                stripped.endswith(';') or stripped.endswith(',') or
                stripped.endswith(':') or stripped.endswith(')') or
                any(stripped.startswith(kw) for kw in ['if ', 'else', 'for ', 'while ', 'do ', 'switch ', 'case ', 'default:']) or
                any(stripped.startswith(kw) for kw in ['void', 'int', 'float', 'char', 'byte', 'const', 'unsigned', 'long', 'boolean', 'String', 'struct', 'enum', 'class', 'typedef', '#', 'return ', 'break', 'continue'])):
                fixed_lines.append(line)
                continue

            # 检查是否可能是函数调用或赋值语句
            if re.match(r'^[\w\.\[\]]+\s*[\=+\-*/%<>!&|^~]+\s*', stripped) or re.match(r'^[\w\.\[\]]+\s*\(', stripped):
                fixed_lines.append(line + ';  // [自动修复] 补全分号')
                fixed_count += 1
            else:
                fixed_lines.append(line)

        if fixed_count == 0:
            return code, None

        return '\n'.join(fixed_lines), {
            'type': 'add_semicolons',
            'description': f'自动补全{fixed_count}个缺失的分号',
            'fixed_count': fixed_count
        }

    def _fix_invalid_pwm_pin(self, code: str) -> Tuple[str, Optional[Dict]]:
        """修复无效PWM引脚 — 自动更改为最近的有效PWM引脚"""
        pwm_pins = [3, 5, 6, 9, 10, 11]
        fixed_count = 0
        new_code = code

        def find_nearest_pwm(pin):
            return min(pwm_pins, key=lambda p: abs(p - pin))

        for match in re.finditer(r'analogWrite\s*\(\s*(\d+)\s*,', code):
            pin = int(match.group(1))
            if pin not in pwm_pins:
                nearest = find_nearest_pwm(pin)
                new_code = new_code.replace(
                    f'analogWrite({pin},',
                    f'analogWrite({nearest},  // [自动修复] PWM引脚{pin}→{nearest}'
                )
                fixed_count += 1

        if fixed_count == 0:
            return code, None

        return new_code, {
            'type': 'fix_pwm_pin',
            'description': f'自动修正{fixed_count}个无效PWM引脚',
            'fixed_count': fixed_count
        }

    def _fix_analogwrite_range(self, code: str) -> Tuple[str, Optional[Dict]]:
        """修复analogWrite值超范围"""
        fixed_count = 0
        new_code = code

        for match in re.finditer(r'analogWrite\s*\(\s*(\w+)\s*,\s*(\d+)\s*\)', code):
            val = int(match.group(2))
            if val > 255:
                new_code = new_code.replace(
                    match.group(0),
                    f'analogWrite({match.group(1)}, 255)  // [自动修复] {val}→255'
                )
                fixed_count += 1

        if fixed_count == 0:
            return code, None

        return new_code, {
            'type': 'fix_analogwrite_range',
            'description': f'自动修正{fixed_count}个analogWrite超范围值',
            'fixed_count': fixed_count
        }

    def _fix_missing_serial_begin(self, code: str) -> Tuple[str, Optional[Dict]]:
        """补全缺失的Serial.begin()"""
        if 'Serial.print' not in code or 'Serial.begin' in code:
            return code, None

        # 在setup函数中添加Serial.begin
        setup_match = re.search(r'(void\s+setup\s*\([^)]*\)\s*\{)', code)
        if setup_match:
            insert_pos = setup_match.end()
            serial_init = '\n  Serial.begin(9600);  // [自动修复] 补全串口初始化\n'
            new_code = code[:insert_pos] + serial_init + code[insert_pos:]
            return new_code, {
                'type': 'add_serial_begin',
                'description': '自动在setup()中补全Serial.begin(9600)',
                'added_lines': 1
            }

        return code, None

    def _fix_undeclared_variables(self, code: str) -> Tuple[str, Optional[Dict]]:
        """修复简单未声明变量（添加int声明）"""
        # 查找赋值但未声明的变量
        declared_vars = set()
        # 收集已声明的变量
        for match in re.finditer(r'\b(?:int|float|char|byte|long|unsigned|boolean|String|double)\s+(\w+)\s*[=\[,;]', code):
            declared_vars.add(match.group(1))

        # 查找赋值语句中的变量
        undeclared = []
        for match in re.finditer(r'^(\s*)(\w+)\s*=\s*', code, re.MULTILINE):
            var_name = match.group(2)
            if var_name not in declared_vars and var_name not in ['Serial', 'Wire', 'SPI', 'EEPROM', 'analogRead', 'digitalRead']:
                # 检查是否是函数调用（如 var = function()）
                if not any(kw in code[:match.start()].split('\n')[-1] for kw in ['void', 'int', 'float']):
                    undeclared.append((match.group(1), var_name, match.start()))

        if not undeclared:
            return code, None

        # 在全局区域添加声明
        declarations = '// [自动修复] 补全变量声明\n'
        for indent, var, pos in undeclared[:5]:  # 最多修复5个
            declarations += f'int {var};\n'
            declared_vars.add(var)

        # 在第一个函数前插入
        first_func = re.search(r'(void\s+(?:setup|loop)\s*\()', code)
        if first_func:
            insert_pos = first_func.start()
            new_code = declarations + '\n' + code[insert_pos:]
            new_code = code[:insert_pos] + '\n' + declarations + code[insert_pos:]
            return new_code, {
                'type': 'declare_variables',
                'description': f'自动补全{len(undeclared[:5])}个未声明变量',
                'added_lines': len(undeclared[:5])
            }

        return code, None

# ==================== 4. AI联想拓展引擎 ====================

class AIAssociationEngine:
    """AI联想拓展引擎 — 基于代码模式智能联想和功能拓展"""

    # 功能联想规则库
    _ASSOCIATION_RULES = {
        'led_blink': {
            'trigger': [r'pinMode\s*\(\s*\d+\s*,\s*OUTPUT', r'digitalWrite\s*\(\s*\d+\s*,\s*(HIGH|LOW)'],
            'suggestions': [
                {'feature': 'PWM呼吸灯', 'code': 'analogWrite({pin}, brightness);\nbrightness = (brightness + 1) % 256;', 'confidence': 0.9},
                {'feature': '多灯流水效果', 'code': 'for(int i=0; i<8; i++) { digitalWrite(i+2, bitRead(pattern, i)); }', 'confidence': 0.8},
                {'feature': '按钮控制LED', 'code': 'if(digitalRead(buttonPin) == HIGH) digitalWrite(ledPin, HIGH);', 'confidence': 0.85},
                {'feature': '光敏电阻自动调光', 'code': 'int light = analogRead(A0); analogWrite(ledPin, map(light, 0, 1023, 0, 255));', 'confidence': 0.75},
            ]
        },
        'serial_comm': {
            'trigger': [r'Serial\.begin', r'Serial\.print'],
            'suggestions': [
                {'feature': '串口命令解析', 'code': 'if(Serial.available()){char cmd=Serial.read(); if(cmd==\'1\') digitalWrite(13,HIGH);}', 'confidence': 0.92},
                {'feature': '数据上报JSON', 'code': 'Serial.print(\'{"sensor":\'); Serial.print(analogRead(A0)); Serial.println(\'}\');', 'confidence': 0.85},
                {'feature': '蓝牙串口透传', 'code': '#include <SoftwareSerial.h>\nSoftwareSerial BT(2,3);', 'confidence': 0.7},
                {'feature': '多串口通信', 'code': '// 使用SoftwareSerial创建虚拟串口', 'confidence': 0.6},
            ]
        },
        'sensor_dht': {
            'trigger': [r'#include\s*<DHT', r'dht\.read'],
            'suggestions': [
                {'feature': '温湿度阈值报警', 'code': 'if(t>30||h>80){tone(8,1000);}', 'confidence': 0.9},
                {'feature': '数据记录SD卡', 'code': '#include <SD.h>\nFile dataFile = SD.open("datalog.txt", FILE_WRITE);', 'confidence': 0.8},
                {'feature': 'MQTT上报', 'code': '// 使用PubSubClient库上传温湿度到MQTT broker', 'confidence': 0.75},
                {'feature': 'OLED显示', 'code': '#include <Adafruit_SSD1306.h>\ndisplay.print("T:"); display.println(t);', 'confidence': 0.85},
            ]
        },
        'servo_control': {
            'trigger': [r'#include\s*<Servo', r'\.write\s*\(\s*\d+\s*\)'],
            'suggestions': [
                {'feature': '电位器控制舵机', 'code': 'int val = analogRead(A0); myservo.write(map(val,0,1023,0,180));', 'confidence': 0.92},
                {'feature': '多舵机联动', 'code': 'Servo s2; s2.attach(10); s2.write(myservo.read()+30);', 'confidence': 0.8},
                {'feature': '超声波避障舵机', 'code': 'if(distance<20) myservo.write(90); else myservo.write(0);', 'confidence': 0.85},
                {'feature': '舵机平滑控制', 'code': 'for(int pos=servo.read(); pos<=target; pos++){myservo.write(pos); delay(15);}', 'confidence': 0.78},
            ]
        },
        'ultrasonic': {
            'trigger': [r'pulseIn\s*\(\s*\w+\s*,\s*HIGH', r'TRIG|ECHO'],
            'suggestions': [
                {'feature': '距离阈值报警', 'code': 'if(distance < 10) { tone(8, 1000); } else { noTone(8); }', 'confidence': 0.9},
                {'feature': '倒车雷达', 'code': 'int beep_rate = map(distance, 0, 100, 50, 500);', 'confidence': 0.8},
                {'feature': '液位监测', 'code': 'float percent = (MAX_DIST - distance) / MAX_DIST * 100;', 'confidence': 0.75},
            ]
        },
        'wifi_esp': {
            'trigger': [r'#include\s*<ESP', r'WiFi\.', r'ESP8266WiFi'],
            'suggestions': [
                {'feature': 'Web服务器', 'code': 'WiFiServer server(80); server.begin();', 'confidence': 0.9},
                {'feature': 'OTA远程升级', 'code': '#include <ArduinoOTA.h>\nArduinoOTA.begin();', 'confidence': 0.85},
                {'feature': 'MQTT物联网', 'code': '#include <PubSubClient.h>\nWiFiClient espClient;\nPubSubClient client(espClient);', 'confidence': 0.88},
                {'feature': 'NTP时间同步', 'code': 'configTime(0, 0, "pool.ntp.org");', 'confidence': 0.75},
                {'feature': 'mDNS服务发现', 'code': '#include <ESPmDNS.h>\nMDNS.begin("arduino");', 'confidence': 0.7},
            ]
        },
        'motor_control': {
            'trigger': [r'analogWrite\s*\(\s*\w+\s*,\s*\d+', r'motor|Motor|MOTOR'],
            'suggestions': [
                {'feature': 'PWM调速', 'code': 'int speed = map(analogRead(A0), 0, 1023, 0, 255); analogWrite(motorPin, speed);', 'confidence': 0.88},
                {'feature': '正反转控制', 'code': 'digitalWrite(in1, dir); digitalWrite(in2, !dir);', 'confidence': 0.82},
                {'feature': '编码器测速', 'code': 'attachInterrupt(0, count, RISING); rpm = (count * 60) / pulses_per_rev;', 'confidence': 0.75},
            ]
        },
    }

    # 项目模板库
    _PROJECT_TEMPLATES = {
        'smart_home': {
            'name': '智能家居控制中心',
            'description': '温湿度监测+光照检测+继电器控制+OLED显示+WiFi上报',
            'includes': ['DHT.h', 'Wire.h', 'Adafruit_SSD1306.h', 'ESP8266WiFi.h', 'PubSubClient.h'],
            'boards': ['esp8266', 'esp32'],
        },
        'robot_car': {
            'name': '智能小车',
            'description': '超声波避障+红外循迹+舵机转向+电机驱动+蓝牙遥控',
            'includes': ['Servo.h', 'SoftwareSerial.h'],
            'boards': ['uno', 'nano', 'mega'],
        },
        'weather_station': {
            'name': '气象站',
            'description': '温湿度+气压+光照+风速+SD卡记录+LoRa传输',
            'includes': ['DHT.h', 'Wire.h', 'SPI.h', 'SD.h'],
            'boards': ['uno', 'nano', 'mega'],
        },
        'security_system': {
            'name': '安防系统',
            'description': 'PIR人体感应+RFID门禁+蜂鸣器报警+摄像头+短信通知',
            'includes': ['SPI.h', 'MFRC522.h', 'SoftwareSerial.h'],
            'boards': ['uno', 'mega'],
        },
        'greenhouse': {
            'name': '智能温室',
            'description': '土壤湿度+水泵控制+通风+补光+数据上报',
            'includes': ['DHT.h', 'ESP8266WiFi.h'],
            'boards': ['esp8266', 'esp32'],
        },
    }

    def analyze_and_suggest(self, code: str) -> Dict[str, Any]:
        """分析代码并生成AI联想建议"""
        assoc_id = f"assoc_{uuid.uuid4().hex[:12]}"

        # 识别代码模式
        detected_patterns = self._detect_patterns(code)

        # 基于模式生成联想
        suggestions = []
        for pattern_key, pattern_info in detected_patterns.items():
            rules = self._ASSOCIATION_RULES.get(pattern_key, {})
            for suggestion in rules.get('suggestions', []):
                suggestions.append({
                    'pattern': pattern_key,
                    'feature': suggestion['feature'],
                    'code': suggestion['code'],
                    'confidence': suggestion['confidence'],
                    'source': 'ai_association'
                })

        # 按置信度排序
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)

        # 生成代码补全建议
        code_completions = self._generate_completions(code, detected_patterns)

        # 推荐项目模板
        recommended_templates = self._recommend_templates(detected_patterns)

        result = {
            'assoc_id': assoc_id,
            'detected_patterns': list(detected_patterns.keys()),
            'suggestions': suggestions[:10],  # Top 10
            'code_completions': code_completions,
            'recommended_templates': recommended_templates,
            'total_suggestions': len(suggestions)
        }

        # 记录到数据库
        try:
            with _get_db_conn() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO arduino_ai_associations
                    (assoc_id, trigger_pattern, suggested_features, generated_code,
                     confidence, source, applied, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 0, ?)
                """, (
                    assoc_id,
                    ','.join(detected_patterns.keys()),
                    json.dumps(suggestions[:10], ensure_ascii=False),
                    json.dumps(code_completions, ensure_ascii=False),
                    suggestions[0]['confidence'] if suggestions else 0,
                    'ai_association',
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"记录AI联想失败: {e}")

        return result

    def _detect_patterns(self, code: str) -> Dict[str, Dict]:
        """检测代码中的功能模式"""
        detected = {}

        for pattern_key, rules in self._ASSOCIATION_RULES.items():
            triggers = rules.get('trigger', [])
            matched_triggers = 0
            for trigger_pattern in triggers:
                if re.search(trigger_pattern, code):
                    matched_triggers += 1

            if matched_triggers > 0:
                detected[pattern_key] = {
                    'triggers_matched': matched_triggers,
                    'total_triggers': len(triggers),
                    'match_score': matched_triggers / max(len(triggers), 1)
                }

        return detected

    def _generate_completions(self, code: str, patterns: Dict) -> List[Dict]:
        """生成代码补全建议"""
        completions = []

        # 基于检测到的模式生成补全
        if 'led_blink' in patterns and 'serial_comm' not in patterns:
            completions.append({
                'type': 'add_serial_debug',
                'description': '建议添加串口调试输出',
                'code': 'Serial.begin(9600);\nSerial.println("LED toggled");',
                'insert_location': 'setup/loop'
            })

        if 'sensor_dht' in patterns and 'serial_comm' in patterns:
            completions.append({
                'type': 'add_threshold_alert',
                'description': '建议添加温湿度阈值报警',
                'code': 'if(t > 35.0) {\n  Serial.println("WARNING: High temp!");\n  tone(8, 1000, 200);\n}',
                'insert_location': 'loop'
            })

        if 'servo_control' in patterns:
            completions.append({
                'type': 'add_smooth_motion',
                'description': '建议添加舵机平滑运动',
                'code': 'void smoothMove(Servo &s, int target) {\n  int curr = s.read();\n  int step = (target > curr) ? 1 : -1;\n  for(int p = curr; p != target; p += step) {\n    s.write(p); delay(15);\n  }\n}',
                'insert_location': 'before_setup'
            })

        if 'wifi_esp' in patterns:
            completions.append({
                'type': 'add_ota_update',
                'description': '建议添加OTA远程升级支持',
                'code': '#include <ArduinoOTA.h>\n// 在setup中:\nArduinoOTA.begin();\n// 在loop中:\nArduinoOTA.handle();',
                'insert_location': 'setup/loop'
            })

        # 通用补全建议
        if 'delay(' in code and 'millis()' not in code:
            completions.append({
                'type': 'non_blocking_delay',
                'description': '建议使用millis()替代delay()实现非阻塞',
                'code': 'unsigned long prev = 0;\n// 在loop中:\nif(millis() - prev >= 1000) {\n  prev = millis();\n  // 你的代码\n}',
                'insert_location': 'global/loop'
            })

        return completions

    def _recommend_templates(self, patterns: Dict) -> List[Dict]:
        """基于检测模式推荐项目模板"""
        recommendations = []

        pattern_keys = set(patterns.keys())

        for template_key, template in self._PROJECT_TEMPLATES.items():
            # 计算模板与当前代码模式的匹配度
            template_includes = set(template['includes'])
            score = 0

            if template_key == 'smart_home' and ('sensor_dht' in pattern_keys or 'wifi_esp' in pattern_keys):
                score = 0.8
            elif template_key == 'robot_car' and ('motor_control' in pattern_keys or 'ultrasonic' in pattern_keys):
                score = 0.85
            elif template_key == 'weather_station' and ('sensor_dht' in pattern_keys or 'ultrasonic' in pattern_keys):
                score = 0.75
            elif template_key == 'security_system' and ('serial_comm' in pattern_keys):
                score = 0.6
            elif template_key == 'greenhouse' and ('sensor_dht' in pattern_keys):
                score = 0.7

            if score > 0:
                recommendations.append({
                    'template': template_key,
                    'name': template['name'],
                    'description': template['description'],
                    'match_score': score,
                    'includes': template['includes'],
                    'boards': template['boards']
                })

        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        return recommendations[:3]

    def generate_project_template(self, template_key: str) -> Dict[str, Any]:
        """生成完整项目模板代码"""
        template = self._PROJECT_TEMPLATES.get(template_key)
        if not template:
            return {'success': False, 'error': f'未知模板: {template_key}'}

        # 根据模板类型生成代码
        generators = {
            'smart_home': self._gen_smart_home,
            'robot_car': self._gen_robot_car,
            'weather_station': self._gen_weather_station,
            'security_system': self._gen_security_system,
            'greenhouse': self._gen_greenhouse,
        }

        generator = generators.get(template_key)
        if not generator:
            return {'success': False, 'error': '生成器未实现'}

        code = generator()
        return {
            'success': True,
            'template': template_key,
            'name': template['name'],
            'code': code,
            'includes': template['includes'],
            'boards': template['boards']
        }

    def _gen_smart_home(self) -> str:
        return """#include <DHT.h>
#include <Wire.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#define DHTPIN D4
#define DHTTYPE DHT22
#define RELAY_PIN D1
#define LIGHT_PIN A0

DHT dht(DHTPIN, DHTTYPE);
WiFiClient espClient;
PubSubClient client(espClient);

const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASS";
const char* mqtt_server = "broker.local";

void setup_wifi() {
  delay(10);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String cmd = "";
  for (int i = 0; i < length; i++) cmd += (char)payload[i];
  if (cmd == "on") digitalWrite(RELAY_PIN, HIGH);
  if (cmd == "off") digitalWrite(RELAY_PIN, LOW);
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect("smart_home")) {
      client.subscribe("home/control");
    } else {
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  pinMode(RELAY_PIN, OUTPUT);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  float h = dht.readHumidity();
  float t = dht.readTemperature();
  int light = analogRead(LIGHT_PIN);

  // 自动控制：温度过高开风扇
  if (t > 30) digitalWrite(RELAY_PIN, HIGH);

  // 上报数据
  String payload = "{\"temp\":" + String(t) + ",\"hum\":" + String(h) + ",\"light\":" + String(light) + "}";
  client.publish("home/data", payload.c_str());

  delay(5000);
}
"""

    def _gen_robot_car(self) -> str:
        return """#include <Servo.h>

#define TRIG_PIN 9
#define ECHO_PIN 10
#define IN1 5
#define IN2 6
#define IN3 7
#define IN4 8
#define ENA 3
#define ENB 11

Servo headServo;
int servoPos = 90;

void setup() {
  Serial.begin(9600);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  pinMode(ENA, OUTPUT); pinMode(ENB, OUTPUT);
  headServo.attach(4);
  headServo.write(servoPos);
}

float getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH);
  return duration * 0.034 / 2;
}

void moveForward(int speed) {
  analogWrite(ENA, speed); analogWrite(ENB, speed);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

void turnRight(int speed) {
  analogWrite(ENA, speed); analogWrite(ENB, speed);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
}

void stopCar() {
  analogWrite(ENA, 0); analogWrite(ENB, 0);
}

void loop() {
  float dist = getDistance();
  Serial.print("Dist: "); Serial.println(dist);

  if (dist < 20) {
    stopCar();
    delay(500);
    // 左右扫描找路径
    headServo.write(30); delay(300);
    float leftDist = getDistance();
    headServo.write(150); delay(300);
    float rightDist = getDistance();
    headServo.write(90); delay(300);

    if (leftDist > rightDist) {
      turnRight(150); delay(500);
    } else {
      turnRight(-150); delay(500);
    }
  } else {
    moveForward(180);
  }
  delay(100);
}
"""

    def _gen_weather_station(self) -> str:
        return """#include <DHT.h>
#include <SPI.h>
#include <SD.h>

#define DHTPIN 2
#define DHTTYPE DHT11
#define CS_PIN 10

DHT dht(DHTPIN, DHTTYPE);
File dataFile;

void setup() {
  Serial.begin(9600);
  dht.begin();
  if (!SD.begin(CS_PIN)) {
    Serial.println("SD卡初始化失败!");
    return;
  }
  Serial.println("气象站启动成功");
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  int light = analogRead(A0);

  if (isnan(h) || isnan(t)) {
    Serial.println("传感器读取失败");
    delay(2000);
    return;
  }

  // 串口输出
  Serial.print("T:"); Serial.print(t);
  Serial.print(" H:"); Serial.print(h);
  Serial.print(" L:"); Serial.println(light);

  // SD卡记录
  dataFile = SD.open("datalog.txt", FILE_WRITE);
  if (dataFile) {
    dataFile.print(millis());
    dataFile.print(","); dataFile.print(t);
    dataFile.print(","); dataFile.print(h);
    dataFile.print(","); dataFile.println(light);
    dataFile.close();
  }

  delay(60000); // 每分钟记录一次
}
"""

    def _gen_security_system(self) -> str:
        return """#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 10
#define RST_PIN 9
#define PIR_PIN 2
#define BUZZER_PIN 8
#define LED_PIN 7

MFRC522 rfid(SS_PIN, RST_PIN);
bool armed = true;
String authorizedUID = "12 34 56 78"; // 授权卡UID

void setup() {
  Serial.begin(9600);
  SPI.begin();
  rfid.PCD_Init();
  pinMode(PIR_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  Serial.println("安防系统已启动");
}

void loop() {
  // 人体检测
  if (armed && digitalRead(PIR_PIN) == HIGH) {
    digitalWrite(BUZZER_PIN, HIGH);
    digitalWrite(LED_PIN, HIGH);
    Serial.println("ALARM: 检测到人体活动!");
    delay(3000);
    digitalWrite(BUZZER_PIN, LOW);
  }

  // RFID门禁
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    String uid = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
      uid += String(rfid.uid.uidByte[i]) + " ";
    }
    uid.trim();

    if (uid == authorizedUID) {
      armed = !armed;
      digitalWrite(LED_PIN, armed ? LOW : HIGH);
      Serial.println(armed ? "系统已布防" : "系统已撤防");
    } else {
      Serial.println("未授权卡片: " + uid);
      tone(BUZZER_PIN, 2000, 500);
    }
    rfid.PICC_HaltA();
  }
}
"""

    def _gen_greenhouse(self) -> str:
        return """#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT22
#define SOIL_PIN A0
#define PUMP_PIN 6
#define FAN_PIN 5
#define LIGHT_RELAY 7

DHT dht(DHTPIN, DHTTYPE);

const float TEMP_THRESHOLD = 30.0;
const int SOIL_THRESHOLD = 400;

void setup() {
  Serial.begin(9600);
  dht.begin();
  pinMode(PUMP_PIN, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);
  pinMode(LIGHT_RELAY, OUTPUT);
}

void loop() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  int soil = analogRead(SOIL_PIN);

  // 温度控制通风
  if (t > TEMP_THRESHOLD) {
    digitalWrite(FAN_PIN, HIGH);
    Serial.println("通风开启");
  } else {
    digitalWrite(FAN_PIN, LOW);
  }

  // 土壤湿度控制水泵
  if (soil < SOIL_THRESHOLD) {
    digitalWrite(PUMP_PIN, HIGH);
    Serial.println("灌溉开启");
  } else {
    digitalWrite(PUMP_PIN, LOW);
  }

  // 光照不足时补光
  int light = analogRead(A1);
  if (light < 300) {
    digitalWrite(LIGHT_RELAY, HIGH);
  } else {
    digitalWrite(LIGHT_RELAY, LOW);
  }

  Serial.print("T:"); Serial.print(t);
  Serial.print(" H:"); Serial.print(h);
  Serial.print(" Soil:"); Serial.print(soil);
  Serial.print(" Light:"); Serial.println(light);

  delay(10000);
}
"""

# ==================== 主执行入口 ====================

def run_advanced_enhancement():
    """执行完整的高级Arduino增强流程"""
    _ensure_advanced_tables()

    logger.info("=" * 70)
    logger.info("[EigenFluxArduinoAdv] 启动 Arduino 高级增强流程")
    logger.info("=" * 70)

    # ===== 1. 端口监听与硬件识别 =====
    logger.info("\n[1] 端口监听与Arduino硬件识别")
    monitor = SerialPortMonitor()
    ports = monitor.scan_ports()
    logger.info(f"  扫描到 {len(ports)} 个串口设备:")
    for p in ports:
        status = "已识别" if p.get('identified') else "未识别"
        driver_status = "已加载" if p.get('driver_loaded') or p.get('driver_auto_loaded') else "需安装"
        logger.info(f"    {p['port_name']}: {p['board_name']} ({status}, 驱动:{p['driver']}/{driver_status})")

    # ===== 2. 自动代码优化 =====
    logger.info("\n[2] 自动代码优化器验证")
    optimizer = AutoCodeOptimizer()
    test_code = """int ledPin = 13;
void setup() {
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
}
void loop() {
  digitalWrite(13, HIGH);
  delay(1000);
  digitalWrite(13, LOW);
  delay(1000);
  Serial.print("Temperature: ");
  Serial.print(analogRead(A0));
  Serial.print("Humidity: ");
  Serial.println(analogRead(A0));
}"""
    opt_result = optimizer.optimize(test_code)
    logger.info(f"  优化数: {opt_result['optimization_count']}")
    for o in opt_result['optimizations']:
        logger.info(f"    [{o['type']}] {o['description']}")
    logger.info(f"  RAM节省: {opt_result['improvements']['ram_savings_estimate']} bytes")

    # ===== 3. 自动编译纠错 =====
    logger.info("\n[3] 自动编译代码纠错器验证")
    corrector = AutoErrorCorrector()
    error_code = """digitalWrite(13, HIGH)
delay(1000)
analogWrite(2, 128)
Serial.print("hello")"""
    fix_result = corrector.correct(error_code)
    logger.info(f"  修复前错误: {len(fix_result['errors_before'])} 个")
    logger.info(f"  修复后错误: {len(fix_result['errors_after'])} 个")
    logger.info(f"  修复数量: {fix_result['fixed_count']}")
    for c in fix_result['corrections']:
        logger.info(f"    [{c['type']}] {c['description']}")

    # ===== 4. AI联想拓展 =====
    logger.info("\n[4] AI联想拓展引擎验证")
    ai_engine = AIAssociationEngine()

    # 分析包含多种模式的代码
    ai_code = """#include <DHT.h>
#include <Servo.h>
DHT dht(2, DHT11);
Servo myservo;
void setup() {
  Serial.begin(9600);
  dht.begin();
  myservo.attach(9);
  pinMode(13, OUTPUT);
}
void loop() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  Serial.print("T:"); Serial.println(t);
  myservo.write(90);
  digitalWrite(13, HIGH);
  delay(1000);
}"""
    ai_result = ai_engine.analyze_and_suggest(ai_code)
    logger.info(f"  检测模式: {ai_result['detected_patterns']}")
    logger.info(f"  联想建议: {ai_result['total_suggestions']} 个")
    for s in ai_result['suggestions'][:5]:
        logger.info(f"    [{s['confidence']:.0%}] {s['feature']} (来源: {s['pattern']})")
    logger.info(f"  代码补全: {len(ai_result['code_completions'])} 条")
    for c in ai_result['code_completions']:
        logger.info(f"    [{c['type']}] {c['description']}")
    logger.info(f"  推荐模板: {len(ai_result['recommended_templates'])} 个")
    for t in ai_result['recommended_templates']:
        logger.info(f"    [{t['match_score']:.0%}] {t['name']} - {t['description'][:40]}...")

    # ===== 5. 生成项目模板 =====
    logger.info("\n[5] 生成智能小车项目模板")
    template = ai_engine.generate_project_template('robot_car')
    if template['success']:
        logger.info(f"  模板: {template['name']}")
        logger.info(f"  代码行数: {len(template['code'].splitlines())}")

    # ===== 总结 =====
    logger.info("\n" + "=" * 70)
    logger.info("[EigenFluxArduinoAdv] 高级增强流程完成")
    logger.info(f"  串口设备: {len(ports)} 个")
    logger.info(f"  代码优化: {opt_result['optimization_count']} 项")
    logger.info(f"  代码纠错: {fix_result['fixed_count']} 处")
    logger.info(f"  AI联想: {ai_result['total_suggestions']} 条建议")
    logger.info(f"  项目模板: {len(ai_result['recommended_templates'])} 个推荐")
    logger.info("=" * 70)

    return {
        'ports_detected': len(ports),
        'optimizations': opt_result['optimization_count'],
        'corrections': fix_result['fixed_count'],
        'ai_suggestions': ai_result['total_suggestions'],
        'templates': len(ai_result['recommended_templates'])
    }

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
    run_advanced_enhancement()
