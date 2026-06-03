# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
串口监视器服务
提供COM口监听,数据读取,实时通信功能
"""

import os
import sys
import json
import time
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

try:
    import serial
    import serial.tools.list_ports
    HAS_PYSERIAL = True
except ImportError:
    HAS_PYSERIAL = False
    logging.warning("未安装pyserial库,串口功能将受限")

# 设置日志
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'serial_monitor_{datetime.now().strftime("%Y-%m-%d")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SerialMonitor')

class SerialMonitor:
    """串口监视器核心服务"""
    
    def __init__(self):
        self.serial_port = None
        self.baud_rate = 9600
        self.is_running = False
        self.is_monitoring = False
        self.read_thread = None
        self.callbacks = []
        self.received_data = []
        self.max_data_length = 1000
        self.lock = threading.Lock()
    
    def list_ports(self) -> Dict[str, Any]:
        """列出所有可用的串口"""
        if not HAS_PYSERIAL:
            return {
                'success': False,
                'message': '需要安装pyserial库',
                'error': '未安装serial模块'
            }
        
        try:
            ports = []
            if sys.platform.startswith('win'):
                com_ports = serial.tools.list_ports.comports()
                for port in com_ports:
                    ports.append({
                        'port': port.device,
                        'name': port.name,
                        'description': port.description,
                        'manufacturer': port.manufacturer,
                        'hwid': port.hwid
                    })
            elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
                import glob
                port_list = glob.glob('/dev/tty[A-Za-z]*')
                for port in port_list:
                    if 'Bluetooth' not in port and 'BLTH' not in port:
                        ports.append({
                            'port': port,
                            'name': port.split('/')[-1],
                            'description': 'Linux Serial Port',
                            'manufacturer': None,
                            'hwid': None
                        })
            elif sys.platform.startswith('darwin'):
                import glob
                port_list = glob.glob('/dev/tty.*') + glob.glob('/dev/cu.*')
                for port in port_list:
                    if 'Bluetooth' not in port and 'BLTH' not in port:
                        ports.append({
                            'port': port,
                            'name': port.split('/')[-1],
                            'description': 'macOS Serial Port',
                            'manufacturer': None,
                            'hwid': None
                        })
            
            return {
                'success': True,
                'ports': ports,
                'count': len(ports)
            }
        except Exception as e:
            return {
                'success': False,
                'message': '获取串口列表失败',
                'error': str(e)
            }
    
    def connect(self, port: str, baud_rate: int = 9600, timeout: float = 1.0) -> Dict[str, Any]:
        """连接到指定串口"""
        if not HAS_PYSERIAL:
            return {
                'success': False,
                'message': '需要安装pyserial库',
                'error': '未安装serial模块'
            }
        
        try:
            if self.serial_port and self.serial_port.is_open:
                self.disconnect()
            
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baud_rate,
                timeout=timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            self.baud_rate = baud_rate
            self.is_running = True
            
            logger.info(f"已连接到串口: {port}, 波特率: {baud_rate}")
            
            return {
                'success': True,
                'message': f'成功连接到 {port}',
                'port': port,
                'baud_rate': baud_rate
            }
        except serial.SerialException as e:
            return {
                'success': False,
                'message': f'连接串口失败',
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'message': '连接过程中发生错误',
                'error': str(e)
            }
    
    def disconnect(self) -> Dict[str, Any]:
        """断开串口连接"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                logger.info("串口已断开")
            
            self.is_running = False
            self.is_monitoring = False
            
            return {
                'success': True,
                'message': '串口已断开'
            }
        except Exception as e:
            return {
                'success': False,
                'message': '断开连接失败',
                'error': str(e)
            }
    
    def send_data(self, data: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """发送数据到串口"""
        if not HAS_PYSERIAL:
            return {
                'success': False,
                'message': '需要安装pyserial库'
            }
        
        if not self.serial_port or not self.serial_port.is_open:
            return {
                'success': False,
                'message': '串口未连接'
            }
        
        try:
            if isinstance(data, str):
                data = data.encode(encoding)
            
            self.serial_port.write(data)
            
            return {
                'success': True,
                'message': f'已发送 {len(data)} 字节',
                'data_sent': data.decode(encoding) if isinstance(data, bytes) else str(data)
            }
        except Exception as e:
            return {
                'success': False,
                'message': '发送数据失败',
                'error': str(e)
            }
    
    def send_line(self, line: str) -> Dict[str, Any]:
        """发送一行数据(自动添加换行符)"""
        return self.send_data(line + '\n')
    
    def read_line(self, timeout: float = None) -> Optional[str]:
        """读取一行数据"""
        if not HAS_PYSERIAL:
            return None
        
        if not self.serial_port or not self.serial_port.is_open:
            return None
        
        try:
            original_timeout = self.serial_port.timeout
            if timeout is not None:
                self.serial_port.timeout = timeout
            
            data = self.serial_port.readline()
            
            if timeout is not None:
                self.serial_port.timeout = original_timeout
            
            if data:
                return data.decode('utf-8', errors='replace').strip()
            return None
        except Exception as e:
            logger.error(f"读取数据失败: {e}")
            return None
    
    def read_bytes(self, size: int = 1024) -> Optional[bytes]:
        """读取指定字节数的数据"""
        if not HAS_PYSERIAL:
            return None
        
        if not self.serial_port or not self.serial_port.is_open:
            return None
        
        try:
            data = self.serial_port.read(size)
            return data
        except Exception as e:
            logger.error(f"读取字节失败: {e}")
            return None
    
    def add_callback(self, callback: Callable[[str, Dict], None]) -> None:
        """添加数据接收回调函数"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[str, Dict], None]) -> None:
        """移除数据接收回调函数"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _notify_callbacks(self, data: str, metadata: Dict) -> None:
        """通知所有回调函数"""
        for callback in self.callbacks:
            try:
                callback(data, metadata)
            except Exception as e:
                logger.error(f"回调函数执行失败: {e}")
    
    def _monitor_loop(self) -> None:
        """监听循环"""
        logger.info("开始监听串口数据...")
        
        while self.is_monitoring and self.serial_port and self.serial_port.is_open:
            try:
                line = self.read_line()
                if line:
                    timestamp = datetime.now().isoformat()
                    metadata = {
                        'timestamp': timestamp,
                        'port': self.serial_port.port,
                        'baud_rate': self.baud_rate,
                        'length': len(line)
                    }
                    
                    with self.lock:
                        self.received_data.append({
                            'data': line,
                            'timestamp': timestamp
                        })
                        if len(self.received_data) > self.max_data_length:
                            self.received_data = self.received_data[-self.max_data_length:]
                    
                    self._notify_callbacks(line, metadata)
                    logger.debug(f"接收数据: {line}")
                
                time.sleep(0.01)
            except Exception as e:
                if self.is_monitoring:
                    logger.error(f"监听循环错误: {e}")
                break
        
        logger.info("监听循环已停止")
    
    def start_monitoring(self) -> Dict[str, Any]:
        """开始监听串口"""
        if not HAS_PYSERIAL:
            return {
                'success': False,
                'message': '需要安装pyserial库'
            }
        
        if not self.serial_port or not self.serial_port.is_open:
            return {
                'success': False,
                'message': '串口未连接'
            }
        
        if self.is_monitoring:
            return {
                'success': False,
                'message': '已经在监听中'
            }
        
        self.is_monitoring = True
        self.read_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.read_thread.start()
        
        return {
            'success': True,
            'message': '开始监听串口数据',
            'port': self.serial_port.port,
            'baud_rate': self.baud_rate
        }
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """停止监听串口"""
        self.is_monitoring = False
        
        if self.read_thread:
            self.read_thread.join(timeout=1.0)
        
        return {
            'success': True,
            'message': '停止监听串口数据'
        }
    
    def get_received_data(self, limit: int = 100) -> List[Dict]:
        """获取接收到的数据"""
        with self.lock:
            return self.received_data[-limit:]
    
    def clear_data(self) -> None:
        """清空接收的数据"""
        with self.lock:
            self.received_data = []
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        if not HAS_PYSERIAL:
            return {
                'connected': False,
                'monitoring': False,
                'port': None,
                'baud_rate': self.baud_rate,
                'data_count': len(self.received_data),
                'has_pyserial': False,
                'message': '未安装pyserial库'
            }
        
        return {
            'connected': self.serial_port is not None and self.serial_port.is_open,
            'monitoring': self.is_monitoring,
            'port': self.serial_port.port if self.serial_port else None,
            'baud_rate': self.baud_rate,
            'data_count': len(self.received_data),
            'has_pyserial': True
        }

class SerialDataParser:
    """串口数据解析器"""
    
    @staticmethod
    def parse_json(data: str) -> Optional[Dict]:
        """解析JSON格式数据"""
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None
    
    @staticmethod
    def parse_key_value(data: str, separator: str = ':') -> Optional[Dict]:
        """解析键值对格式数据"""
        try:
            result = {}
            pairs = data.split(',')
            for pair in pairs:
                if separator in pair:
                    key, value = pair.split(separator, 1)
                    result[key.strip()] = value.strip()
            return result if result else None
        except Exception:
            return None
    
    @staticmethod
    def parse_csv(data: str, delimiter: str = ',') -> Optional[List[str]]:
        """解析CSV格式数据"""
        try:
            return [item.strip() for item in data.split(delimiter)]
        except Exception:
            return None
    
    @staticmethod
    def parse_numeric(data: str) -> Optional[float]:
        """解析数值数据"""
        try:
            return float(data)
        except ValueError:
            return None
    
    @staticmethod
    def parse_sensor_data(data: str) -> Optional[Dict]:
        """解析传感器数据(多种格式)"""
        # 尝试JSON格式
        json_result = SerialDataParser.parse_json(data)
        if json_result:
            return {'type': 'json', 'data': json_result}
        
        # 尝试键值对格式
        kv_result = SerialDataParser.parse_key_value(data)
        if kv_result:
            return {'type': 'key_value', 'data': kv_result}
        
        # 尝试数值格式
        num_result = SerialDataParser.parse_numeric(data)
        if num_result is not None:
            return {'type': 'numeric', 'data': num_result}
        
        return {'type': 'text', 'data': data}

if __name__ == '__main__':
    monitor = SerialMonitor()
    
    print("=== 串口监视器测试 ===\n")
    
    print("1. 列出可用串口:")
    ports_result = monitor.list_ports()
    if ports_result['success']:
        print(f"   发现 {ports_result['count']} 个串口")
        for port in ports_result['ports']:
            print(f"   - {port['port']}: {port.get('description', 'Unknown')}")
    else:
        print(f"   错误: {ports_result.get('message', '未知错误')}")
    
    print("\n2. 获取状态:")
    status = monitor.get_status()
    print(f"   已连接: {status['connected']}")
    print(f"   正在监听: {status['monitoring']}")
    print(f"   pyserial可用: {status['has_pyserial']}")
    
    print("\n == 测试完成 ===")
