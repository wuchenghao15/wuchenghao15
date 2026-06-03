# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Arduino 设计系统服务
提供在线编辑,编译,上传和仿真功能
"""

import os
import sys
import json
import uuid
import tempfile
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# 设置日志
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'arduino_{datetime.now().strftime("%Y-%m-%d")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ArduinoService')

class ArduinoService:
    """Arduino设计系统核心服务"""
    
    # 支持的Arduino板型
    BOARDS = {
        'uno': {'name': 'Arduino Uno', 'fqbn': 'arduino:avr:uno'},
        'nano': {'name': 'Arduino Nano', 'fqbn': 'arduino:avr:nano'},
        'mega': {'name': 'Arduino Mega', 'fqbn': 'arduino:avr:mega'},
        'leonardo': {'name': 'Arduino Leonardo', 'fqbn': 'arduino:avr:leonardo'},
        'esp8266': {'name': 'NodeMCU ESP8266', 'fqbn': 'esp8266:esp8266:nodemcuv2'},
        'esp32': {'name': 'ESP32 DevKit', 'fqbn': 'esp32:esp32:esp32'},
        'nano33ble': {'name': 'Arduino Nano 33 BLE', 'fqbn': 'arduino:nrf52:nano33ble'},
        'micro': {'name': 'Arduino Micro', 'fqbn': 'arduino:avr:micro'}
    }
    
    # 常用传感器模块
    SENSORS = {
        'led': {'name': 'LED灯', 'pins': ['digital'], 'code': 'digitalWrite(pin, HIGH);'},
        'button': {'name': '按钮', 'pins': ['digital'], 'code': 'digitalRead(pin);'},
        'potentiometer': {'name': '电位器', 'pins': ['analog'], 'code': 'analogRead(pin);'},
        'ldr': {'name': '光敏电阻', 'pins': ['analog'], 'code': 'analogRead(pin);'},
        'dht11': {'name': 'DHT11温湿度传感器', 'pins': ['digital'], 'code': '#include <DHT.h>'},
        'ultrasonic': {'name': '超声波传感器', 'pins': ['digital'], 'code': 'digitalWrite(trigPin, HIGH);'},
        'servo': {'name': '舵机', 'pins': ['digital'], 'code': '#include <Servo.h>'},
        'lcd1602': {'name': 'LCD1602显示屏', 'pins': ['digital'], 'code': '#include <LiquidCrystal.h>'},
        'buzzer': {'name': '蜂鸣器', 'pins': ['digital'], 'code': 'tone(pin, frequency);'},
        'relay': {'name': '继电器模块', 'pins': ['digital'], 'code': 'digitalWrite(pin, HIGH);'},
        'motor': {'name': '直流电机', 'pins': ['digital', 'pwm'], 'code': 'analogWrite(pin, speed);'},
        'ws2812': {'name': 'WS2812 LED灯带', 'pins': ['digital'], 'code': '#include <Adafruit_NeoPixel.h>'}
    }
    
    # 代码模板
    CODE_TEMPLATES = {
        'blink': {
            'name': 'LED闪烁',
            'description': '让LED灯以1秒间隔闪烁',
            'code': '''void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
}'''
        },
        'button': {
            'name': '按钮控制LED',
            'description': '通过按钮控制LED灯的开关',
            'code': '''const int buttonPin = 2;
const int ledPin = LED_BUILTIN;

int buttonState = 0;

void setup() {
  pinMode(ledPin, OUTPUT);
  pinMode(buttonPin, INPUT_PULLUP);
}

void loop() {
  buttonState = digitalRead(buttonPin);
  
  if (buttonState == LOW) {
    digitalWrite(ledPin, HIGH);
  } else {
    digitalWrite(ledPin, LOW);
  }
}'''
        },
        'serial': {
            'name': '串口通信',
            'description': '通过串口发送和接收数据',
            'code': '''void setup() {
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\\n');
    Serial.print("收到: ");
    Serial.println(input);
  }
  delay(10);
}'''
        },
        'pwm': {
            'name': 'PWM调光',
            'description': '使用PWM控制LED亮度',
            'code': '''const int ledPin = 9;

void setup() {
  pinMode(ledPin, OUTPUT);
}

void loop() {
  for (int brightness = 0; brightness <= 255; brightness++) {
    analogWrite(ledPin, brightness);
    delay(10);
  }
  for (int brightness = 255; brightness >= 0; brightness--) {
    analogWrite(ledPin, brightness);
    delay(10);
  }
}'''
        },
        'sensor': {
            'name': '模拟传感器读取',
            'description': '读取模拟传感器数值',
            'code': '''const int sensorPin = A0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  int sensorValue = analogRead(sensorPin);
  Serial.print("传感器值: ");
  Serial.println(sensorValue);
  delay(500);
}'''
        },
        'servo': {
            'name': '舵机控制',
            'description': '控制舵机旋转',
            'code': '''#include <Servo.h>

Servo myservo;
int pos = 0;

void setup() {
  myservo.attach(9);
}

void loop() {
  for (pos = 0; pos <= 180; pos += 1) {
    myservo.write(pos);
    delay(15);
  }
  for (pos = 180; pos >= 0; pos -= 1) {
    myservo.write(pos);
    delay(15);
  }
}'''
        },
        'lcd': {
            'name': 'LCD显示',
            'description': '在LCD1602上显示文本',
            'code': '''#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

void setup() {
  lcd.begin(16, 2);
  lcd.print("Hello, World!");
}

void loop() {
  lcd.setCursor(0, 1);
  lcd.print(millis() / 1000);
  delay(100);
}'''
        },
        'dht': {
            'name': 'DHT温湿度',
            'description': '读取温湿度传感器数据',
            'code': '''#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  
  Serial.print("湿度: ");
  Serial.print(h);
  Serial.print("%\\t温度: ");
  Serial.print(t);
  Serial.println("°C");
  
  delay(2000);
}'''
        }
    }
    
    def __init__(self):
        self.temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        self._check_arduino_cli()
    
    def _check_arduino_cli(self) -> bool:
        """检查arduino-cli是否安装"""
        try:
            result = subprocess.run(['arduino-cli', '--version'], capture_output=True, text=True)
            self.has_cli = result.returncode == 0
            if self.has_cli:
                logger.info(f"arduino-cli版本: {result.stdout.strip()}")
            else:
                logger.warning("arduino-cli未安装,将使用模拟模式")
            return self.has_cli
        except FileNotFoundError:
            self.has_cli = False
            logger.warning("arduino-cli未安装,将使用模拟模式")
            return False
    
    def get_boards(self) -> Dict[str, Any]:
        """获取支持的板型列表"""
        return {
            'success': True,
            'boards': self.BOARDS
        }
    
    def get_templates(self) -> Dict[str, Any]:
        """获取代码模板列表"""
        return {
            'success': True,
            'templates': self.CODE_TEMPLATES
        }
    
    def get_sensors(self) -> Dict[str, Any]:
        """获取传感器模块列表"""
        return {
            'success': True,
            'sensors': self.SENSORS
        }
    
    def _create_temp_sketch(self, code: str) -> str:
        """创建临时sketch文件"""
        sketch_id = str(uuid.uuid4())[:8]
        sketch_dir = os.path.join(self.temp_dir, f'sketch_{sketch_id}')
        os.makedirs(sketch_dir, exist_ok=True)
        
        ino_file = os.path.join(sketch_dir, f'sketch_{sketch_id}.ino')
        with open(ino_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        return ino_file
    
    def compile_code(self, code: str, board: str = 'uno') -> Dict[str, Any]:
        """编译Arduino代码"""
        if board not in self.BOARDS:
            return {
                'success': False,
                'message': f'不支持的板型: {board}',
                'error': f'可用板型: {list(self.BOARDS.keys())}'
            }
        
        try:
            ino_file = self._create_temp_sketch(code)
            sketch_dir = os.path.dirname(ino_file)
            fqbn = self.BOARDS[board]['fqbn']
            
            if self.has_cli:
                cmd = ['arduino-cli', 'compile', '--fqbn', fqbn, sketch_dir]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    return {
                        'success': True,
                        'message': '编译成功',
                        'output': result.stdout,
                        'board': self.BOARDS[board]['name']
                    }
                else:
                    return {
                        'success': False,
                        'message': '编译失败',
                        'error': result.stderr,
                        'board': self.BOARDS[board]['name']
                    }
            else:
                return self._simulate_compile(code, board)
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': '编译超时',
                'error': '编译时间超过限制'
            }
        except Exception as e:
            return {
                'success': False,
                'message': '编译过程中发生错误',
                'error': str(e)
            }
    
    def _simulate_compile(self, code: str, board: str) -> Dict[str, Any]:
        """模拟编译(无arduino-cli时使用)"""
        errors = []
        warnings = []
        
        if 'setup()' not in code:
            errors.append('缺少必要的setup()函数')
        if 'loop()' not in code:
            errors.append('缺少必要的loop()函数')
        
        open_brackets = code.count('{')
        close_brackets = code.count('}')
        if open_brackets != close_brackets:
            errors.append(f'括号不匹配:{open_brackets}个开括号,{close_brackets}个闭括号')
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('//'):
                if not stripped.endswith(';') and not stripped.endswith('{') and not stripped.endswith('}'):
                    if 'void ' not in stripped and 'if(' not in stripped and 'for(' not in stripped and 'while(' not in stripped:
                        if '=' in stripped and not stripped.endswith('{'):
                            warnings.append(f'第{i+1}行:语句可能缺少分号')
        
        if '/*' in code and '*/' not in code.split('/*')[-1]:
            errors.append('存在未闭合的多行注释')
        
        if errors:
            return {
                'success': False,
                'message': '编译失败(模拟模式)',
                'errors': errors,
                'warnings': warnings,
                'board': self.BOARDS[board]['name'],
                'mode': 'simulated'
            }
        
        return {
            'success': True,
            'message': '编译成功(模拟模式)',
            'output': '注意:arduino-cli未安装,使用模拟编译模式',
            'board': self.BOARDS[board]['name'],
            'mode': 'simulated',
            'warnings': warnings
        }
    
    def verify_code(self, code: str) -> Dict[str, Any]:
        """验证代码语法"""
        errors = []
        warnings = []
        
        if 'setup()' not in code:
            errors.append('缺少必要的setup()函数')
        if 'loop()' not in code:
            errors.append('缺少必要的loop()函数')
        
        open_brackets = code.count('{')
        close_brackets = code.count('}')
        if open_brackets != close_brackets:
            errors.append(f'括号不匹配:{open_brackets}个开括号,{close_brackets}个闭括号')
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('//') and \
               not stripped.endswith(';') and not stripped.endswith('{') and not stripped.endswith('}') and \
               not stripped.endswith(':') and not 'void ' in stripped and not 'if(' in stripped and \
               not 'for(' in stripped and not 'while(' in stripped and not 'switch(' in stripped:
                if '=' in stripped or stripped.isidentifier():
                    warnings.append(f'第{i+1}行:语句可能缺少分号')
        
        if '/*' in code and '*/' not in code.split('/*')[-1]:
            errors.append('存在未闭合的多行注释')
        
        return {
            'success': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def upload_code(self, code: str, board: str = 'uno', port: str = '') -> Dict[str, Any]:
        """上传代码到Arduino板"""
        compile_result = self.compile_code(code, board)
        if not compile_result['success']:
            return compile_result
        
        if board not in self.BOARDS:
            return {
                'success': False,
                'message': f'不支持的板型: {board}'
            }
        
        try:
            ino_file = self._create_temp_sketch(code)
            sketch_dir = os.path.dirname(ino_file)
            fqbn = self.BOARDS[board]['fqbn']
            
            if self.has_cli and port:
                cmd = ['arduino-cli', 'upload', '--fqbn', fqbn, '--port', port, sketch_dir]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    return {
                        'success': True,
                        'message': '上传成功',
                        'board': self.BOARDS[board]['name'],
                        'port': port
                    }
                else:
                    return {
                        'success': False,
                        'message': '上传失败',
                        'error': result.stderr,
                        'board': self.BOARDS[board]['name']
                    }
            else:
                return {
                    'success': True,
                    'message': '上传成功(模拟模式)',
                    'board': self.BOARDS[board]['name'],
                    'port': port if port else '未指定',
                    'mode': 'simulated',
                    'output': '注意:arduino-cli未安装或未指定端口,使用模拟上传模式'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': '上传超时',
                'error': '上传时间超过限制'
            }
        except Exception as e:
            return {
                'success': False,
                'message': '上传过程中发生错误',
                'error': str(e)
            }
    
    def list_serial_ports(self) -> Dict[str, Any]:
        """列出可用的串口"""
        ports = []
        
        try:
            if sys.platform.startswith('win'):
                import serial.tools.list_ports
                ports = [port.device for port in serial.tools.list_ports.comports()]
            elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
                import glob
                ports = glob.glob('/dev/tty[A-Za-z]*')
            elif sys.platform.startswith('darwin'):
                import glob
                ports = glob.glob('/dev/tty.*') + glob.glob('/dev/cu.*')
            
            filtered_ports = []
            for port in ports:
                if 'Bluetooth' not in port and 'BLTH' not in port:
                    filtered_ports.append(port)
            
            return {
                'success': True,
                'ports': filtered_ports
            }
        except ImportError:
            return {
                'success': False,
                'message': '需要安装pyserial库',
                'error': '未安装serial模块'
            }
        except Exception as e:
            return {
                'success': False,
                'message': '获取串口列表失败',
                'error': str(e)
            }
    
    def generate_project(self, project_name: str, code: str, board: str = 'uno') -> Dict[str, Any]:
        """生成完整的Arduino项目"""
        try:
            project_dir = os.path.join(self.temp_dir, project_name)
            os.makedirs(project_dir, exist_ok=True)
            
            ino_file = os.path.join(project_dir, f'{project_name}.ino')
            with open(ino_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            config_file = os.path.join(project_dir, 'project.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'name': project_name,
                    'board': board,
                    'board_name': self.BOARDS[board]['name'],
                    'created_at': datetime.now().isoformat(),
                    'version': '1.0.0'
                }, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'message': '项目生成成功',
                'project_path': project_dir,
                'files': [f'{project_name}.ino', 'project.json']
            }
        except Exception as e:
            return {
                'success': False,
                'message': '项目生成失败',
                'error': str(e)
            }

if __name__ == '__main__':
    service = ArduinoService()
    
    print("=== Arduino 设计系统测试 ===\n")
    
    print("1. 获取支持的板型:")
    boards = service.get_boards()
    print(f"   支持 {len(boards['boards'])} 种板型")
    for key, info in boards['boards'].items():
        print(f"   - {key}: {info['name']}")
    
    print("\n2. 获取代码模板:")
    templates = service.get_templates()
    print(f"   有 {len(templates['templates'])} 个模板")
    for key, info in templates['templates'].items():
        print(f"   - {key}: {info['name']}")
    
    print("\n3. 编译测试代码:")
    result = service.compile_code(service.CODE_TEMPLATES['blink']['code'], 'uno')
    print(f"   结果: {'成功' if result['success'] else '失败'}")
    print(f"   消息: {result['message']}")
    
    print("\n4. 验证代码语法:")
    verify_result = service.verify_code(service.CODE_TEMPLATES['blink']['code'])
    print(f"   结果: {'通过' if verify_result['success'] else '失败'}")
    if verify_result['errors']:
        print(f"   错误: {verify_result['errors']}")
    if verify_result['warnings']:
        print(f"   警告: {verify_result['warnings']}")
    
    print("\n5. 获取串口列表:")
    ports = service.list_serial_ports()
    print(f"   状态: {'成功' if ports['success'] else '失败'}")
    if ports['success']:
        print(f"   可用串口: {ports['ports']}")
    
    print("\n == 测试完成 ===")
