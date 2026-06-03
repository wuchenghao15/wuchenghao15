# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Arduino 高级设计系统服务
提供电路设计、仿真、代码生成、项目管理等高级功能
"""

import os
import sys
import json
import uuid
import tempfile
import subprocess
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# 设置日志
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'arduino_advanced_{datetime.now().strftime("%Y-%m-%d")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ArduinoAdvancedService')

class ArduinoAdvancedService:
    """Arduino高级设计系统核心服务"""
    
    # 元件库
    COMPONENTS = {
        'resistor': {'name': '电阻', 'units': ['Ω', 'kΩ', 'MΩ'], 'default': '220'},
        'capacitor': {'name': '电容', 'units': ['pF', 'nF', 'µF'], 'default': '100nF'},
        'led_red': {'name': '红色LED', 'current': '20mA', 'voltage': '2.0V'},
        'led_green': {'name': '绿色LED', 'current': '20mA', 'voltage': '2.2V'},
        'led_blue': {'name': '蓝色LED', 'current': '20mA', 'voltage': '3.2V'},
        'button': {'name': '按钮开关', 'type': 'momentary'},
        'switch': {'name': '拨动开关', 'type': 'toggle'},
        'potentiometer': {'name': '电位器', 'range': '10kΩ'},
        'ldr': {'name': '光敏电阻', 'type': 'photoresistor'},
        'buzzer': {'name': '蜂鸣器', 'type': 'piezo'},
        'motor_dc': {'name': '直流电机', 'voltage': '5-12V'},
        'servo': {'name': '舵机', 'range': '0-180°'},
        'ultrasonic': {'name': '超声波传感器', 'range': '2-400cm'},
        'dht11': {'name': 'DHT11温湿度', 'temperature': '0-50°C', 'humidity': '20-90%'},
        'dht22': {'name': 'DHT22温湿度', 'temperature': '-40-80°C', 'humidity': '0-100%'},
        'lcd1602': {'name': 'LCD1602显示屏', 'columns': 16, 'rows': 2},
        'oled12864': {'name': 'OLED12864显示屏', 'width': 128, 'height': 64},
        'relay_1ch': {'name': '1通道继电器', 'voltage': '5V'},
        'relay_4ch': {'name': '4通道继电器', 'voltage': '5V'},
        'ws2812': {'name': 'WS2812 LED灯带', 'type': 'addressable'},
        'mpu6050': {'name': 'MPU6050陀螺仪', 'type': '6-axis'},
        'nrf24l01': {'name': 'NRF24L01无线模块', 'type': '2.4GHz'},
        'hc05': {'name': 'HC-05蓝牙模块', 'type': 'serial'},
        'esp8266': {'name': 'ESP8266 WiFi模块', 'type': 'WiFi'},
        'ds18b20': {'name': 'DS18B20温度传感器', 'type': 'onewire'},
        'ir_receiver': {'name': '红外接收器', 'type': 'IR'},
        'ir_transmitter': {'name': '红外发射器', 'type': 'IR'}
    }
    
    # 高级代码模板
    ADVANCED_TEMPLATES = {
        'traffic_light': {
            'name': '交通信号灯',
            'description': '模拟交通信号灯控制系统',
            'difficulty': '初级',
            'category': '控制',
            'code': '''const int redLed = 9;
const int yellowLed = 10;
const int greenLed = 11;

void setup() {
  pinMode(redLed, OUTPUT);
  pinMode(yellowLed, OUTPUT);
  pinMode(greenLed, OUTPUT);
}

void loop() {
  digitalWrite(redLed, HIGH);
  delay(5000);
  digitalWrite(redLed, LOW);
  
  digitalWrite(yellowLed, HIGH);
  delay(2000);
  digitalWrite(yellowLed, LOW);
  
  digitalWrite(greenLed, HIGH);
  delay(5000);
  digitalWrite(greenLed, LOW);
  
  digitalWrite(yellowLed, HIGH);
  delay(2000);
  digitalWrite(yellowLed, LOW);
}'''
        },
        'alarm_system': {
            'name': '报警系统',
            'description': '使用PIR传感器和蜂鸣器的安全报警系统',
            'difficulty': '中级',
            'category': '安全',
            'code': '''const int pirSensor = 2;
const int buzzer = 9;
const int ledPin = 13;

void setup() {
  pinMode(pirSensor, INPUT);
  pinMode(buzzer, OUTPUT);
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  int pirState = digitalRead(pirSensor);
  
  if (pirState == HIGH) {
    Serial.println("检测到运动!");
    digitalWrite(ledPin, HIGH);
    tone(buzzer, 1000, 100);
    delay(500);
    tone(buzzer, 2000, 100);
  } else {
    digitalWrite(ledPin, LOW);
  }
  delay(100);
}'''
        },
        'weather_station': {
            'name': '气象站',
            'description': '使用DHT11的温湿度监测站',
            'difficulty': '中级',
            'category': '传感器',
            'code': '''#include <DHT.h>
#include <LiquidCrystal.h>

#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

void setup() {
  dht.begin();
  lcd.begin(16, 2);
  lcd.print("气象站初始化...");
  delay(2000);
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("温度: ");
  lcd.print(t);
  lcd.print("°C");
  
  lcd.setCursor(0, 1);
  lcd.print("湿度: ");
  lcd.print(h);
  lcd.print("%");
  
  delay(2000);
}'''
        },
        'servo_controller': {
            'name': '舵机控制器',
            'description': '使用电位器控制舵机角度',
            'difficulty': '中级',
            'category': '控制',
            'code': '''#include <Servo.h>

Servo myservo;
const int potPin = A0;
int val = 0;
int angle = 0;

void setup() {
  myservo.attach(9);
  Serial.begin(9600);
}

void loop() {
  val = analogRead(potPin);
  angle = map(val, 0, 1023, 0, 180);
  myservo.write(angle);
  
  Serial.print("角度: ");
  Serial.println(angle);
  delay(15);
}'''
        },
        'rgb_controller': {
            'name': 'RGB灯控制器',
            'description': '使用PWM控制RGB LED颜色',
            'difficulty': '中级',
            'category': 'LED',
            'code': '''const int redPin = 9;
const int greenPin = 10;
const int bluePin = 11;

void setup() {
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
}

void loop() {
  setColor(255, 0, 0);
  delay(1000);
  
  setColor(0, 255, 0);
  delay(1000);
  
  setColor(0, 0, 255);
  delay(1000);
  
  setColor(255, 255, 0);
  delay(1000);
  
  rainbowEffect();
}

void setColor(int red, int green, int blue) {
  analogWrite(redPin, red);
  analogWrite(greenPin, green);
  analogWrite(bluePin, blue);
}

void rainbowEffect() {
  for (int i = 0; i < 256; i++) {
    setColor(i, 255 - i, 0);
    delay(10);
  }
}'''
        },
        'digital_clock': {
            'name': '数字时钟',
            'description': '使用LCD显示的电子时钟',
            'difficulty': '高级',
            'category': '显示',
            'code': '''#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

int hours = 0;
int minutes = 0;
int seconds = 0;
unsigned long previousMillis = 0;
const long interval = 1000;

void setup() {
  lcd.begin(16, 2);
  lcd.print("Arduino 时钟");
  delay(2000);
}

void loop() {
  unsigned long currentMillis = millis();
  
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    seconds++;
    
    if (seconds >= 60) {
      seconds = 0;
      minutes++;
      if (minutes >= 60) {
        minutes = 0;
        hours++;
        if (hours >= 24) {
          hours = 0;
        }
      }
    }
    
    updateDisplay();
  }
}

void updateDisplay() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("时间: ");
  lcd.print(hours < 10 ? "0" : "");
  lcd.print(hours);
  lcd.print(":");
  lcd.print(minutes < 10 ? "0" : "");
  lcd.print(minutes);
  lcd.print(":");
  lcd.print(seconds < 10 ? "0" : "");
  lcd.print(seconds);
}'''
        },
        'ultrasonic_radar': {
            'name': '超声波雷达',
            'description': '超声波距离传感器加舵机的雷达扫描系统',
            'difficulty': '高级',
            'category': '传感器',
            'code': '''#include <Servo.h>

Servo radarServo;
const int trigPin = 9;
const int echoPin = 10;

int angle = 0;
int direction = 1;

void setup() {
  radarServo.attach(11);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  Serial.begin(9600);
}

void loop() {
  int distance = measureDistance();
  
  Serial.print(angle);
  Serial.print(",");
  Serial.println(distance);
  
  angle += direction;
  if (angle >= 180 || angle <= 0) {
    direction = -direction;
  }
  
  radarServo.write(angle);
  delay(50);
}

int measureDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  long duration = pulseIn(echoPin, HIGH);
  int distance = duration * 0.034 / 2;
  
  return distance;
}'''
        },
        'keypad_lock': {
            'name': '电子密码锁',
            'description': '使用4x4矩阵键盘的电子锁',
            'difficulty': '高级',
            'category': '安全',
            'code': '''#include <Keypad.h>

const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

byte rowPins[ROWS] = {9, 8, 7, 6};
byte colPins[COLS] = {5, 4, 3, 2};

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

String password = "1234";
String input = "";
const int lockPin = 13;
const int greenLed = 11;
const int redLed = 12;

void setup() {
  pinMode(lockPin, OUTPUT);
  pinMode(greenLed, OUTPUT);
  pinMode(redLed, OUTPUT);
  digitalWrite(lockPin, LOW);
  digitalWrite(greenLed, LOW);
  digitalWrite(redLed, HIGH);
  Serial.begin(9600);
  Serial.println("请输入密码:");
}

void loop() {
  char key = keypad.getKey();
  
  if (key) {
    if (key == '#') {
      checkPassword();
    } else if (key == '*') {
      input = "";
      Serial.println("已清除");
    } else {
      input += key;
      Serial.print("*");
    }
  }
}

void checkPassword() {
  if (input == password) {
    Serial.println("\n密码正确!");
    digitalWrite(greenLed, HIGH);
    digitalWrite(redLed, LOW);
    digitalWrite(lockPin, HIGH);
    delay(3000);
    digitalWrite(lockPin, LOW);
    digitalWrite(greenLed, LOW);
    digitalWrite(redLed, HIGH);
  } else {
    Serial.println("\n密码错误!");
    digitalWrite(redLed, HIGH);
    delay(1000);
  }
  input = "";
}'''
        }
    }
    
    # 电路原理图模板
    SCHEMATIC_TEMPLATES = {
        'basic_led': {
            'name': '基础LED电路',
            'components': ['led_red', 'resistor'],
            'connections': 'Anode -> 220Ω -> Digital Pin, Cathode -> GND',
            'description': '最基础的LED控制电路'
        },
        'button_input': {
            'name': '按钮输入电路',
            'components': ['button', 'resistor'],
            'connections': 'Button -> 10kΩ -> 5V, Button -> Digital Pin',
            'description': '按钮输入检测电路'
        },
        'rgb_led': {
            'name': 'RGB LED电路',
            'components': ['led_red', 'led_green', 'led_blue', 'resistor', 'resistor', 'resistor'],
            'connections': 'Each LED -> 220Ω -> PWM Pin',
            'description': '三色RGB LED控制电路'
        },
        'servo_motor': {
            'name': '舵机控制电路',
            'components': ['servo', 'capacitor'],
            'connections': 'Signal -> Digital Pin, VCC -> 5V, GND -> GND',
            'description': '舵机控制电路'
        },
        'ultrasonic': {
            'name': '超声波传感器电路',
            'components': ['ultrasonic'],
            'connections': 'Trig -> Digital, Echo -> Digital',
            'description': '超声波测距电路'
        }
    }
    
    def __init__(self):
        self.temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.projects_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'arduino_projects')
        os.makedirs(self.projects_dir, exist_ok=True)
    
    def get_components(self) -> Dict[str, Any]:
        """获取元件库列表"""
        return {
            'success': True,
            'components': self.COMPONENTS
        }
    
    def get_advanced_templates(self) -> Dict[str, Any]:
        """获取高级代码模板列表"""
        return {
            'success': True,
            'templates': self.ADVANCED_TEMPLATES
        }
    
    def get_schematic_templates(self) -> Dict[str, Any]:
        """获取电路原理图模板列表"""
        return {
            'success': True,
            'schematics': self.SCHEMATIC_TEMPLATES
        }
    
    def generate_code_from_components(self, components: List[Dict], board: str = 'uno') -> Dict[str, Any]:
        """根据元件配置生成代码"""
        try:
            code_lines = []
            pin_definitions = []
            setup_lines = []
            loop_lines = []
            
            for comp in components:
                comp_type = comp.get('type')
                pin = comp.get('pin', 13)
                
                if comp_type.startswith('led'):
                    var_name = f'led_{pin}'
                    pin_definitions.append(f'const int {var_name} = {pin};')
                    setup_lines.append(f'  pinMode({var_name}, OUTPUT);')
                    loop_lines.append(f'  digitalWrite({var_name}, HIGH);')
                    loop_lines.append(f'  delay(500);')
                    loop_lines.append(f'  digitalWrite({var_name}, LOW);')
                    loop_lines.append(f'  delay(500);')
                
                elif comp_type == 'button':
                    var_name = f'button_{pin}'
                    pin_definitions.append(f'const int {var_name} = {pin};')
                    setup_lines.append(f'  pinMode({var_name}, INPUT_PULLUP);')
                    loop_lines.append(f'  int buttonState = digitalRead({var_name});')
                    loop_lines.append(f'  if (buttonState == LOW) {{')
                    loop_lines.append(f'    Serial.println("按钮按下");')
                    loop_lines.append(f'  }}')
                
                elif comp_type == 'potentiometer':
                    var_name = f'pot_{pin}'
                    pin_definitions.append(f'const int {var_name} = {pin};')
                    loop_lines.append(f'  int potValue = analogRead({var_name});')
                    loop_lines.append(f'  Serial.println(potValue);')
                
                elif comp_type == 'servo':
                    pin_definitions.append('#include <Servo.h>')
                    pin_definitions.append(f'Servo servo_{pin};')
                    setup_lines.append(f'  servo_{pin}.attach({pin});')
                    loop_lines.append(f'  for (int i = 0; i <= 180; i++) {{')
                    loop_lines.append(f'    servo_{pin}.write(i);')
                    loop_lines.append(f'    delay(15);')
                    loop_lines.append(f'  }}')
                
                elif comp_type == 'ultrasonic':
                    trig_pin = pin
                    echo_pin = pin + 1
                    pin_definitions.append(f'const int trigPin = {trig_pin};')
                    pin_definitions.append(f'const int echoPin = {echo_pin};')
                    setup_lines.append(f'  pinMode(trigPin, OUTPUT);')
                    setup_lines.append(f'  pinMode(echoPin, INPUT);')
                    loop_lines.append(f'  long duration = measureDistance(trigPin, echoPin);')
                    loop_lines.append(f'  int distance = duration * 0.034 / 2;')
                    loop_lines.append(f'  Serial.print("距离: ");')
                    loop_lines.append(f'  Serial.println(distance);')
            
            code = ''
            
            if pin_definitions:
                code += '\n'.join(pin_definitions)
                code += '\n\n'
            
            code += 'void setup() {\n'
            if not setup_lines:
                setup_lines.append('  Serial.begin(9600);')
            code += '\n'.join(setup_lines)
            code += '\n}\n\n'
            
            code += 'void loop() {\n'
            code += '\n'.join(loop_lines)
            code += '\n  delay(100);\n}\n'
            
            if any(comp.get('type') == 'ultrasonic' for comp in components):
                code += '\nlong measureDistance(int trig, int echo) {\n'
                code += '  digitalWrite(trig, LOW);\n'
                code += '  delayMicroseconds(2);\n'
                code += '  digitalWrite(trig, HIGH);\n'
                code += '  delayMicroseconds(10);\n'
                code += '  digitalWrite(trig, LOW);\n'
                code += '  return pulseIn(echo, HIGH);\n}\n'
            
            return {
                'success': True,
                'code': code,
                'board': board,
                'components_used': len(components)
            }
        except Exception as e:
            return {
                'success': False,
                'message': '代码生成失败',
                'error': str(e)
            }
    
    def create_project(self, project_name: str, code: str, board: str = 'uno', 
                       description: str = '', tags: List[str] = None) -> Dict[str, Any]:
        """创建新的Arduino项目"""
        try:
            project_id = str(uuid.uuid4())[:8]
            project_dir = os.path.join(self.projects_dir, project_id)
            os.makedirs(project_dir, exist_ok=True)
            
            ino_file = os.path.join(project_dir, f'{project_name}.ino')
            with open(ino_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            config_file = os.path.join(project_dir, 'config.json')
            config_data = {
                'project_id': project_id,
                'name': project_name,
                'description': description,
                'board': board,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'tags': tags or [],
                'version': '1.0.0'
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'message': '项目创建成功',
                'project_id': project_id,
                'project_name': project_name,
                'project_path': project_dir,
                'board': board
            }
        except Exception as e:
            return {
                'success': False,
                'message': '项目创建失败',
                'error': str(e)
            }
    
    def list_projects(self) -> Dict[str, Any]:
        """列出所有项目"""
        try:
            projects = []
            
            if not os.path.exists(self.projects_dir):
                return {
                    'success': True,
                    'projects': [],
                    'count': 0
                }
            
            for item in os.listdir(self.projects_dir):
                item_path = os.path.join(self.projects_dir, item)
                if os.path.isdir(item_path):
                    config_file = os.path.join(item_path, 'config.json')
                    if os.path.exists(config_file):
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        projects.append(config)
            
            return {
                'success': True,
                'projects': projects,
                'count': len(projects)
            }
        except Exception as e:
            return {
                'success': False,
                'message': '获取项目列表失败',
                'error': str(e)
            }
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """获取项目详情"""
        try:
            project_dir = os.path.join(self.projects_dir, project_id)
            
            if not os.path.exists(project_dir):
                return {
                    'success': False,
                    'message': '项目不存在'
                }
            
            config_file = os.path.join(project_dir, 'config.json')
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            code_files = []
            for item in os.listdir(project_dir):
                if item.endswith('.ino'):
                    ino_file = os.path.join(project_dir, item)
                    with open(ino_file, 'r', encoding='utf-8') as f:
                        code = f.read()
                    code_files.append({
                        'filename': item,
                        'code': code
                    })
            
            return {
                'success': True,
                'config': config,
                'code_files': code_files,
                'project_path': project_dir
            }
        except Exception as e:
            return {
                'success': False,
                'message': '获取项目失败',
                'error': str(e)
            }
    
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """分析代码质量"""
        try:
            issues = []
            suggestions = []
            
            if 'setup()' not in code:
                issues.append('缺少必要的setup()函数')
            
            if 'loop()' not in code:
                issues.append('缺少必要的loop()函数')
            
            open_braces = code.count('{')
            close_braces = code.count('}')
            if open_braces != close_braces:
                issues.append(f'括号不匹配: {open_braces}个开括号, {close_braces}个闭括号')
            
            lines = code.split('\n')
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and not stripped.startswith('//'):
                    if not stripped.endswith(';') and not stripped.endswith('{') and not stripped.endswith('}'):
                        if 'void ' not in stripped and 'if(' not in stripped and 'for(' not in stripped:
                            suggestions.append(f'第{i+1}行可能缺少分号')
            
            if 'delay(' in code and code.count('delay(') > 5:
                suggestions.append('建议考虑使用millis()代替delay()实现非阻塞代码')
            
            if 'digitalRead' in code or 'analogRead' in code:
                suggestions.append('建议添加输入滤波处理')
            
            return {
                'success': True,
                'has_issues': len(issues) > 0,
                'issues': issues,
                'suggestions': suggestions,
                'quality_score': max(0, 100 - len(issues) * 10)
            }
        except Exception as e:
            return {
                'success': False,
                'message': '代码分析失败',
                'error': str(e)
            }
    
    def format_code(self, code: str) -> Dict[str, Any]:
        """格式化代码"""
        try:
            lines = code.split('\n')
            formatted_lines = []
            indent_level = 0
            
            for line in lines:
                stripped_line = line.strip()
                
                if stripped_line.startswith('}'):
                    indent_level = max(0, indent_level - 1)
                
                if stripped_line:
                    formatted_line = '  ' * indent_level + stripped_line
                    formatted_lines.append(formatted_line)
                else:
                    formatted_lines.append('')
                
                if stripped_line.endswith('{'):
                    indent_level += 1
            
            formatted_code = '\n'.join(formatted_lines)
            
            return {
                'success': True,
                'formatted_code': formatted_code,
                'lines_formatted': len(lines)
            }
        except Exception as e:
            return {
                'success': False,
                'message': '代码格式化失败',
                'error': str(e)
            }
    
    def generate_documentation(self, code: str, project_name: str) -> Dict[str, Any]:
        """生成项目文档"""
        try:
            lines = code.split('\n')
            include_lines = [line for line in lines if line.strip().startswith('#include')]
            pin_definitions = [line for line in lines if line.strip().startswith('const int')]
            
            include_text = '\n'.join(f'- {lib}' for lib in include_lines) if include_lines else '无特殊依赖'
            pin_text = '\n'.join(f'- {pin}' for pin in pin_definitions) if pin_definitions else '无特殊引脚定义'
            time_text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            documentation = f'''# {project_name}

## 项目概述
Arduino项目,使用以下组件:

## 依赖库
{include_text}

## 引脚定义
{pin_text}

## 使用说明
1. 上传代码到Arduino板
2. 打开串口监视器(波特率9600)
3. 观察运行效果

## 生成时间
{time_text}
'''
            
            return {
                'success': True,
                'documentation': documentation,
                'include_count': len(include_lines),
                'pin_count': len(pin_definitions)
            }
        except Exception as e:
            return {
                'success': False,
                'message': '文档生成失败',
                'error': str(e)
            }

if __name__ == '__main__':
    service = ArduinoAdvancedService()
    
    print("=== Arduino 高级设计系统测试 ===\n")
    
    print("1. 获取元件库:")
    components = service.get_components()
    print(f"   元件数量: {len(components['components'])}")
    
    print("\n2. 获取高级模板:")
    templates = service.get_advanced_templates()
    print(f"   模板数量: {len(templates['templates'])}")
    for key, info in templates['templates'].items():
        print(f"   - {key}: {info['name']} ({info['difficulty']})")
    
    print("\n3. 获取电路图模板:")
    schematics = service.get_schematic_templates()
    print(f"   电路图数量: {len(schematics['schematics'])}")
    
    print("\n4. 从元件生成代码:")
    test_components = [
        {'type': 'led_red', 'pin': 13},
        {'type': 'button', 'pin': 2}
    ]
    code_result = service.generate_code_from_components(test_components)
    if code_result['success']:
        print(f"   代码生成成功,使用{code_result['components_used']}个元件")
        print(f"   代码长度: {len(code_result['code'])}字符")
    
    print("\n5. 创建测试项目:")
    test_code = '''void setup() {
  pinMode(13, OUTPUT);
}

void loop() {
  digitalWrite(13, HIGH);
  delay(1000);
  digitalWrite(13, LOW);
  delay(1000);
}'''
    project_result = service.create_project('测试项目', test_code, 'uno', '这是一个测试项目', ['LED', '测试'])
    if project_result['success']:
        print(f"   项目创建成功: {project_result['project_name']}")
    
    print("\n6. 代码分析:")
    analysis_result = service.analyze_code(test_code)
    if analysis_result['success']:
        print(f"   代码质量得分: {analysis_result['quality_score']}")
        print(f"   问题数: {len(analysis_result['issues'])}")
        print(f"   建议数: {len(analysis_result['suggestions'])}")
    
    print("\n7. 代码格式化:")
    format_result = service.format_code(test_code)
    if format_result['success']:
        print(f"   格式化成功,处理{format_result['lines_formatted']}行")
    
    print("\n8. 生成文档:")
    doc_result = service.generate_documentation(test_code, '测试项目')
    if doc_result['success']:
        print(f"   文档生成成功,包含{doc_result['include_count']}个库,{doc_result['pin_count']}个引脚定义")
    
    print("\n9. 列出项目:")
    projects_result = service.list_projects()
    if projects_result['success']:
        print(f"   现有项目数: {projects_result['count']}")
    
    print("\n == 测试完成 ===")
