#!/usr/bin/env python3
import json
import time
import socket
from datetime import datetime
from collections import defaultdict

class ArduinoIoTManager:
    """Arduino IoT管理器 - 管理Arduino设备的网络连接和通信"""
    
    def __init__(self):
        self.devices = {}
        self.connections = {}
        self.message_queue = defaultdict(list)
        self.subscribers = defaultdict(list)
        self.is_running = False
    
    def add_device(self, device_id, name, ip_address=None, port=80, protocol='http'):
        """添加设备"""
        self.devices[device_id] = {
            'id': device_id,
            'name': name,
            'ip_address': ip_address,
            'port': port,
            'protocol': protocol,
            'status': 'offline',
            'last_connection': None,
            'last_message': None,
            'data_points': []
        }
    
    def connect_device(self, device_id):
        """连接设备"""
        device = self.devices.get(device_id)
        if not device:
            return False
        
        try:
            if device['protocol'] == 'tcp':
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((device['ip_address'], device['port']))
                self.connections[device_id] = sock
                device['status'] = 'online'
                device['last_connection'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return True
            elif device['protocol'] == 'http':
                device['status'] = 'online'
                device['last_connection'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return True
        except Exception as e:
            device['status'] = 'offline'
            return False
    
    def disconnect_device(self, device_id):
        """断开设备连接"""
        if device_id in self.connections:
            try:
                self.connections[device_id].close()
            except:
                pass
            del self.connections[device_id]
        
        if device_id in self.devices:
            self.devices[device_id]['status'] = 'offline'
        
        return True
    
    def send_command(self, device_id, command, params=None):
        """发送命令到设备"""
        device = self.devices.get(device_id)
        if not device or device['status'] != 'online':
            return False
        
        message = {
            'command': command,
            'params': params or {},
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            if device_id in self.connections:
                sock = self.connections[device_id]
                sock.sendall(json.dumps(message).encode('utf-8'))
                
                response = sock.recv(1024).decode('utf-8')
                device['last_message'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._publish_message(device_id, json.loads(response))
                return json.loads(response)
            else:
                device['last_message'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._publish_message(device_id, {'status': 'sent', 'command': command})
                return {'status': 'sent', 'command': command}
        except Exception as e:
            device['status'] = 'offline'
            return False
    
    def receive_data(self, device_id, timeout=5):
        """接收设备数据"""
        device = self.devices.get(device_id)
        if not device or device['status'] != 'online':
            return None
        
        try:
            if device_id in self.connections:
                sock = self.connections[device_id]
                sock.settimeout(timeout)
                data = sock.recv(1024).decode('utf-8')
                
                if data:
                    parsed = json.loads(data)
                    device['data_points'].append(parsed)
                    device['last_message'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self._publish_message(device_id, parsed)
                    return parsed
        except socket.timeout:
            return None
        except Exception as e:
            device['status'] = 'offline'
            return None
        
        return None
    
    def _publish_message(self, device_id, message):
        """发布消息给订阅者"""
        for callback in self.subscribers.get(device_id, []):
            try:
                callback(device_id, message)
            except:
                pass
    
    def subscribe(self, device_id, callback):
        """订阅设备消息"""
        self.subscribers[device_id].append(callback)
    
    def unsubscribe(self, device_id, callback):
        """取消订阅"""
        if device_id in self.subscribers:
            self.subscribers[device_id].remove(callback)
    
    def get_device_status(self, device_id):
        """获取设备状态"""
        return self.devices.get(device_id)
    
    def get_all_devices(self):
        """获取所有设备"""
        return list(self.devices.values())
    
    def get_device_stats(self, device_id):
        """获取设备统计"""
        device = self.devices.get(device_id)
        if not device:
            return None
        
        return {
            'device_id': device_id,
            'name': device['name'],
            'status': device['status'],
            'data_points_count': len(device['data_points']),
            'last_connection': device['last_connection'],
            'last_message': device['last_message']
        }
    
    def set_device_property(self, device_id, property_name, value):
        """设置设备属性"""
        device = self.devices.get(device_id)
        if device and property_name in device:
            device[property_name] = value
            return True
        return False
    
    def start(self):
        """启动IoT管理器"""
        self.is_running = True
    
    def stop(self):
        """停止IoT管理器"""
        self.is_running = False
        for device_id in list(self.connections.keys()):
            self.disconnect_device(device_id)
    
    def scan_network(self, subnet='192.168.1.', start=1, end=254, timeout=1):
        """扫描网络中的Arduino设备"""
        found = []
        
        for i in range(start, min(end + 1, 255)):
            ip = f"{subnet}{i}"
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((ip, 80))
                
                if result == 0:
                    found.append({
                        'ip': ip,
                        'port': 80,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                sock.close()
            except:
                pass
        
        return found

if __name__ == '__main__':
    iot = ArduinoIoTManager()
    
    logger.info("=== Arduino IoT管理器 ===")
    
    iot.add_device('device_001', '智能传感器节点', '192.168.1.100', 80, 'http')
    iot.add_device('device_002', '远程控制模块', '192.168.1.101', 80, 'http')
    logger.info("\n添加设备成功")
    
    devices = iot.get_all_devices()
    logger.info(f"\n设备列表: {len(devices)}个")
    for device in devices:
        logger.info(f"  {device['id']}: {device['name']} ({device['ip_address']}) - {device['status']}")
    
    result = iot.connect_device('device_001')
    logger.info(f"\n连接设备 device_001: {'成功' if result else '失败'}")
    
    status = iot.get_device_status('device_001')
    logger.info(f"\n设备状态: {status['status']}")
    
    response = iot.send_command('device_001', 'read_sensors', {'sensors': ['temperature', 'humidity']})
    logger.info(f"\n发送命令: {response}")
    
    stats = iot.get_device_stats('device_001')
    logger.info(f"\n设备统计:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    iot.disconnect_device('device_001')
    status = iot.get_device_status('device_001')
    logger.info(f"\n断开后状态: {status['status']}")
    
    iot.stop()