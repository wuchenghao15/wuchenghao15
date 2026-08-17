#!/usr/bin/env python3
import sqlite3
import json
import os
import re
import math
from datetime import datetime
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

_COMPONENT_LIBRARY = {
    'arduino_uno': {'name': 'Arduino Uno', 'category': 'controller', 'price': 99, 'pins': 14, 'analog_pins': 6},
    'arduino_nano': {'name': 'Arduino Nano', 'category': 'controller', 'price': 69, 'pins': 14, 'analog_pins': 8},
    'arduino_mega': {'name': 'Arduino Mega', 'category': 'controller', 'price': 199, 'pins': 54, 'analog_pins': 16},
    'dht11': {'name': 'DHT11温湿度传感器', 'category': 'sensor', 'price': 15, 'interface': 'digital', 'power': 3.3},
    'dht22': {'name': 'DHT22温湿度传感器', 'category': 'sensor', 'price': 35, 'interface': 'digital', 'power': 3.3},
    'lcd1602': {'name': 'LCD 1602显示屏', 'category': 'display', 'price': 25, 'interface': 'parallel', 'power': 5},
    'lcd_i2c': {'name': 'LCD 1602 I2C显示屏', 'category': 'display', 'price': 35, 'interface': 'i2c', 'power': 5},
    'servo': {'name': 'SG90舵机', 'category': 'actuator', 'price': 25, 'interface': 'pwm', 'power': 4.8},
    'ultrasonic': {'name': 'HC-SR04超声波传感器', 'category': 'sensor', 'price': 20, 'interface': 'digital', 'power': 5},
    'led': {'name': 'LED灯', 'category': 'actuator', 'price': 2, 'interface': 'digital', 'power': 2},
    'button': {'name': '按钮开关', 'category': 'input', 'price': 1, 'interface': 'digital', 'power': 5},
    'potentiometer': {'name': '10k电位器', 'category': 'sensor', 'price': 3, 'interface': 'analog', 'power': 5},
    'buzzer': {'name': '有源蜂鸣器', 'category': 'actuator', 'price': 5, 'interface': 'digital', 'power': 5},
    'relay': {'name': '继电器模块', 'category': 'actuator', 'price': 15, 'interface': 'digital', 'power': 5},
    'rgb_led': {'name': 'RGB LED模块', 'category': 'actuator', 'price': 8, 'interface': 'pwm', 'power': 5},
    'ldr': {'name': '光敏电阻', 'category': 'sensor', 'price': 3, 'interface': 'analog', 'power': 5},
    'motion': {'name': 'HC-SR501人体红外传感器', 'category': 'sensor', 'price': 15, 'interface': 'digital', 'power': 5},
    'soil': {'name': '土壤湿度传感器', 'category': 'sensor', 'price': 12, 'interface': 'analog', 'power': 5},
    'ds18b20': {'name': 'DS18B20温度传感器', 'category': 'sensor', 'price': 18, 'interface': '1wire', 'power': 3.3},
    'esp8266': {'name': 'ESP8266 WiFi模块', 'category': 'communication', 'price': 35, 'interface': 'uart', 'power': 3.3},
    'bluetooth': {'name': 'HC-05蓝牙模块', 'category': 'communication', 'price': 25, 'interface': 'uart', 'power': 3.3},
}

_CODE_TEMPLATES = {
    'led_blink': {
        'template': '''int ledPin = {{pin}};

void setup() {
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  digitalWrite(ledPin, HIGH);
  Serial.println("LED ON");
  delay({{delay_ms}});
  digitalWrite(ledPin, LOW);
  Serial.println("LED OFF");
  delay({{delay_ms}});
}''',
        'params': {'pin': 13, 'delay_ms': 1000}
    },
    'dht11_read': {
        'template': '''#include <DHT.h>

#define DHTPIN {{pin}}
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  
  Serial.print("Humidity: ");
  Serial.print(h);
  Serial.print("%\\t");
  Serial.print("Temperature: ");
  Serial.print(t);
  Serial.println("°C");
  
  delay({{delay_ms}});
}''',
        'params': {'pin': 2, 'delay_ms': 2000}
    },
    'servo_control': {
        'template': '''#include <Servo.h>

Servo myservo;
int servoPin = {{pin}};

void setup() {
  myservo.attach(servoPin);
  Serial.begin(9600);
}

void loop() {
  for (int pos = 0; pos <= 180; pos += 1) {
    myservo.write(pos);
    Serial.print("Servo: ");
    Serial.println(pos);
    delay(15);
  }
  for (int pos = 180; pos >= 0; pos -= 1) {
    myservo.write(pos);
    Serial.print("Servo: ");
    Serial.println(pos);
    delay(15);
  }
}''',
        'params': {'pin': 9}
    },
    'ultrasonic': {
        'template': '''#define TRIG_PIN {{trig_pin}}
#define ECHO_PIN {{echo_pin}}

void setup() {
  Serial.begin(9600);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
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

void loop() {
  float dist = getDistance();
  Serial.print("Distance: ");
  Serial.print(dist);
  Serial.println(" cm");
  delay({{delay_ms}});
}''',
        'params': {'trig_pin': 9, 'echo_pin': 10, 'delay_ms': 500}
    },
    'lcd_display': {
        'template': '''#include <LiquidCrystal.h>

LiquidCrystal lcd({{rs}}, {{en}}, {{d4}}, {{d5}}, {{d6}}, {{d7}});

void setup() {
  lcd.begin(16, 2);
  lcd.logger.info("{{text1}}");
  Serial.begin(9600);
}

void loop() {
  lcd.setCursor(0, 1);
  lcd.logger.info(millis() / 1000);
  lcd.logger.info(" seconds");
  delay(1000);
}''',
        'params': {'rs': 12, 'en': 11, 'd4': 5, 'd5': 4, 'd6': 3, 'd7': 2, 'text1': 'Hello, Arduino!'}
    },
    'pwm_fade': {
        'template': '''int ledPin = {{pin}};
int brightness = 0;
int fadeAmount = {{fade_amount}};

void setup() {
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  analogWrite(ledPin, brightness);
  brightness = brightness + fadeAmount;
  
  if (brightness <= 0 || brightness >= 255) {
    fadeAmount = -fadeAmount;
  }
  
  Serial.print("Brightness: ");
  Serial.println(brightness);
  delay({{delay_ms}});
}''',
        'params': {'pin': 9, 'fade_amount': 5, 'delay_ms': 30}
    },
    'button_control': {
        'template': '''int buttonPin = {{button_pin}};
int ledPin = {{led_pin}};
int buttonState = 0;

void setup() {
  pinMode(buttonPin, INPUT);
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  buttonState = digitalRead(buttonPin);
  Serial.print("Button: ");
  Serial.println(buttonState);
  
  if (buttonState == HIGH) {
    digitalWrite(ledPin, HIGH);
  } else {
    digitalWrite(ledPin, LOW);
  }
}''',
        'params': {'button_pin': 2, 'led_pin': 13}
    },
    'analog_read': {
        'template': '''int potPin = {{pin}};
int sensorValue = 0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  sensorValue = analogRead(potPin);
  Serial.print("Sensor Value: ");
  Serial.println(sensorValue);
  delay({{delay_ms}});
}''',
        'params': {'pin': 'A0', 'delay_ms': 100}
    }
}

_COMPONENT_MODULES = {
    'dht11': {
        'includes': ['#include <DHT.h>'],
        'defines': ['#define DHTPIN {{dht_pin}}', '#define DHTTYPE DHT11'],
        'declarations': ['DHT dht(DHTPIN, DHTTYPE);'],
        'setup': ['dht.begin();'],
        'loop': [
            'float h = dht.readHumidity();',
            'float t = dht.readTemperature();',
            'Serial.print("Humidity: ");',
            'Serial.print(h);',
            'Serial.print("%\\t");',
            'Serial.print("Temperature: ");',
            'Serial.print(t);',
            'Serial.println("°C");'
        ],
        'params': {'dht_pin': 2},
        'variables': ['h', 't'],
        'variable_types': {'h': 'float', 't': 'float'}
    },
    'dht22': {
        'includes': ['#include <DHT.h>'],
        'defines': ['#define DHTPIN {{dht_pin}}', '#define DHTTYPE DHT22'],
        'declarations': ['DHT dht(DHTPIN, DHTTYPE);'],
        'setup': ['dht.begin();'],
        'loop': [
            'float h = dht.readHumidity();',
            'float t = dht.readTemperature();',
            'Serial.print("Humidity: ");',
            'Serial.print(h);',
            'Serial.print("%\\t");',
            'Serial.print("Temperature: ");',
            'Serial.print(t);',
            'Serial.println("°C");'
        ],
        'params': {'dht_pin': 2},
        'variables': ['h', 't'],
        'variable_types': {'h': 'float', 't': 'float'}
    },
    'lcd1602': {
        'includes': ['#include <LiquidCrystal.h>'],
        'defines': [],
        'declarations': ['LiquidCrystal lcd({{lcd_rs}}, {{lcd_en}}, {{lcd_d4}}, {{lcd_d5}}, {{lcd_d6}}, {{lcd_d7}});'],
        'setup': ['lcd.begin(16, 2);', 'lcd.logger.info("Arduino System");'],
        'loop': [],
        'params': {'lcd_rs': 12, 'lcd_en': 11, 'lcd_d4': 5, 'lcd_d5': 4, 'lcd_d6': 3, 'lcd_d7': 2},
        'variables': [],
        'variable_types': {}
    },
    'lcd_i2c': {
        'includes': ['#include <Wire.h>', '#include <LiquidCrystal_I2C.h>'],
        'defines': [],
        'declarations': ['LiquidCrystal_I2C lcd(0x27, 16, 2);'],
        'setup': ['lcd.init();', 'lcd.backlight();', 'lcd.logger.info("Arduino System");'],
        'loop': [],
        'params': {},
        'variables': [],
        'variable_types': {}
    },
    'led': {
        'includes': [],
        'defines': [],
        'declarations': ['int ledPin = {{led_pin}};'],
        'setup': ['pinMode(ledPin, OUTPUT);'],
        'loop': [],
        'params': {'led_pin': 13},
        'variables': [],
        'variable_types': {}
    },
    'servo': {
        'includes': ['#include <Servo.h>'],
        'defines': [],
        'declarations': ['Servo myservo;', 'int servoPin = {{servo_pin}};'],
        'setup': ['myservo.attach(servoPin);'],
        'loop': [],
        'params': {'servo_pin': 9},
        'variables': [],
        'variable_types': {}
    },
    'ultrasonic': {
        'includes': [],
        'defines': ['#define TRIG_PIN {{trig_pin}}', '#define ECHO_PIN {{echo_pin}}'],
        'declarations': [],
        'setup': ['pinMode(TRIG_PIN, OUTPUT);', 'pinMode(ECHO_PIN, INPUT);'],
        'loop': [],
        'params': {'trig_pin': 9, 'echo_pin': 10},
        'functions': ['''float getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH);
  return duration * 0.034 / 2;
}'''],
        'variables': [],
        'variable_types': {}
    },
    'button': {
        'includes': [],
        'defines': [],
        'declarations': ['int buttonPin = {{button_pin}};', 'int buttonState = 0;'],
        'setup': ['pinMode(buttonPin, INPUT);'],
        'loop': [],
        'params': {'button_pin': 2},
        'variables': ['buttonState'],
        'variable_types': {'buttonState': 'int'}
    },
    'potentiometer': {
        'includes': [],
        'defines': [],
        'declarations': ['int potPin = {{pot_pin}};', 'int sensorValue = 0;'],
        'setup': [],
        'loop': [],
        'params': {'pot_pin': 'A0'},
        'variables': ['sensorValue'],
        'variable_types': {'sensorValue': 'int'}
    },
    'buzzer': {
        'includes': [],
        'defines': [],
        'declarations': ['int buzzerPin = {{buzzer_pin}};'],
        'setup': ['pinMode(buzzerPin, OUTPUT);'],
        'loop': [],
        'params': {'buzzer_pin': 8},
        'variables': [],
        'variable_types': {}
    },
    'esp8266': {
        'includes': ['#include <ESP8266WiFi.h>'],
        'defines': ['#define WiFi_SSID "{{wifi_ssid}}"', '#define WiFi_PASS "{{wifi_pass}}"'],
        'declarations': ['WiFiClient client;'],
        'setup': [
            'WiFi.begin(WiFi_SSID, WiFi_PASS);',
            'while (WiFi.status() != WL_CONNECTED) {',
            '  delay(500);',
            '  Serial.print(".");',
            '}',
            'Serial.println("");',
            'Serial.println("WiFi connected");',
            'Serial.println(WiFi.localIP());'
        ],
        'loop': [],
        'params': {'wifi_ssid': 'YOUR_SSID', 'wifi_pass': 'YOUR_PASSWORD'},
        'variables': [],
        'variable_types': {}
    },
    'bluetooth': {
        'includes': [],
        'defines': [],
        'declarations': [],
        'setup': ['Serial.begin(9600);', 'Serial1.begin(9600);'],
        'loop': [],
        'params': {},
        'variables': [],
        'variable_types': {}
    }
}

_COMPONENT_KEYWORDS = {
    'dht11': ['温湿度', '湿度', 'dht11'],
    'dht22': ['dht22', '高精度温湿度'],
    'lcd1602': ['lcd', '显示屏', '显示', '屏幕'],
    'lcd_i2c': ['i2c lcd', 'lcd i2c'],
    'led': ['led', '灯', '发光', '闪烁'],
    'servo': ['舵机', '电机', '转动'],
    'ultrasonic': ['距离', '超声波', '测距'],
    'button': ['按钮', '按键', '开关'],
    'potentiometer': ['电位器', '旋钮', '模拟'],
    'buzzer': ['蜂鸣器', '声音', '报警'],
    'esp8266': ['wifi', '联网', '网络上传', 'esp8266'],
    'bluetooth': ['蓝牙', '无线']
}

_COMPOSITION_RULES = {
    'dht11+lcd1602': {
        'description': '温湿度检测+LCD显示',
        'loop': [
            'float h = dht.readHumidity();',
            'float t = dht.readTemperature();',
            'lcd.setCursor(0, 0);',
            'lcd.logger.info("Temp: ");',
            'lcd.logger.info(t);',
            'lcd.logger.info("C");',
            'lcd.setCursor(0, 1);',
            'lcd.logger.info("Hum: ");',
            'lcd.logger.info(h);',
            'lcd.logger.info("%");',
            'delay(1000);'
        ]
    },
    'dht11+led': {
        'description': '温湿度检测+LED报警',
        'loop': [
            'float h = dht.readHumidity();',
            'float t = dht.readTemperature();',
            'if (t > 30) {',
            '  digitalWrite(ledPin, HIGH);',
            '} else {',
            '  digitalWrite(ledPin, LOW);',
            '}',
            'delay(500);'
        ]
    },
    'dht11+esp8266': {
        'description': '温湿度检测+WiFi上传',
        'loop': [
            'float h = dht.readHumidity();',
            'float t = dht.readTemperature();',
            'Serial.print("T:");',
            'Serial.print(t);',
            'Serial.print(",H:");',
            'Serial.println(h);',
            'delay(2000);'
        ]
    },
    'ultrasonic+servo': {
        'description': '超声波测距+舵机控制',
        'loop': [
            'float dist = getDistance();',
            'int angle = map(dist, 0, 100, 0, 180);',
            'myservo.write(angle);',
            'delay(100);'
        ]
    },
    'button+led': {
        'description': '按钮控制LED',
        'loop': [
            'buttonState = digitalRead(buttonPin);',
            'digitalWrite(ledPin, buttonState);',
            'delay(50);'
        ]
    },
    'potentiometer+led': {
        'description': '电位器控制LED亮度',
        'loop': [
            'sensorValue = analogRead(potPin);',
            'analogWrite(ledPin, map(sensorValue, 0, 1023, 0, 255));',
            'delay(50);'
        ]
    },
    'dht11+lcd1602+led': {
        'description': '温湿度检测+LCD显示+LED报警',
        'loop': [
            'float h = dht.readHumidity();',
            'float t = dht.readTemperature();',
            'lcd.setCursor(0, 0);',
            'lcd.logger.info("Temp: ");',
            'lcd.logger.info(t);',
            'lcd.logger.info("C");',
            'lcd.setCursor(0, 1);',
            'lcd.logger.info("Hum: ");',
            'lcd.logger.info(h);',
            'lcd.logger.info("%");',
            'digitalWrite(ledPin, (t > 30) ? HIGH : LOW);',
            'delay(1000);'
        ]
    },
    'dht11+lcd1602+esp8266': {
        'description': '温湿度检测+LCD显示+WiFi上传',
        'loop': [
            'float h = dht.readHumidity();',
            'float t = dht.readTemperature();',
            'lcd.setCursor(0, 0);',
            'lcd.logger.info("Temp: ");',
            'lcd.logger.info(t);',
            'lcd.logger.info("C");',
            'lcd.setCursor(0, 1);',
            'lcd.logger.info("Hum: ");',
            'lcd.logger.info(h);',
            'lcd.logger.info("%");',
            'Serial.print("T:");',
            'Serial.print(t);',
            'Serial.print(",H:");',
            'Serial.println(h);',
            'delay(2000);'
        ]
    }
}

class ArduinoAIEngine:
    """Arduino AI智能引擎 - 将AI能力与Arduino系统深度融合"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def generate_code(self, description, components=None):
        """AI代码生成器 - 根据自然语言描述生成Arduino代码（支持多组件组合）"""
        description = description.lower()
        
        if components is None:
            components = self._detect_components(description)
        
        if len(components) >= 2:
            composite_result = self._generate_composite_code(description, components)
            if composite_result['success']:
                return composite_result
        
        keywords = {
            'led_blink': ['led', '灯', '发光', '闪烁'],
            'dht11_read': ['温湿度', '湿度', 'dht11', 'dht22'],
            'servo_control': ['舵机', '电机', '转动'],
            'ultrasonic': ['距离', '超声波', '测距'],
            'lcd_display': ['显示屏', '显示', '屏幕'],
            'button_control': ['按钮', '按键', '开关'],
            'analog_read': ['电位器', '旋钮', '模拟'],
            'pwm_fade': ['呼吸灯', '渐亮', '渐灭'],
        }
        
        matched_template = None
        params = {}
        
        for template_key, template_keywords in keywords.items():
            for keyword in template_keywords:
                if keyword in description:
                    matched_template = template_key
                    break
            if matched_template:
                break
        
        if matched_template and matched_template in _CODE_TEMPLATES:
            template = _CODE_TEMPLATES[matched_template]
            code = template['template']
            params = template['params'].copy()
            
            if 'pin' in params and '引脚' in description:
                match = re.search(r'引脚\s*(\d+)', description)
                if match:
                    params['pin'] = int(match.group(1))
            
            for key, value in params.items():
                code = code.replace(f'{{{{{key}}}}}', str(value))
            
            return {
                'success': True,
                'code': code,
                'template': matched_template,
                'params': params,
                'description': description,
                'suggested_components': self._suggest_components(matched_template),
                'detected_components': components,
                'is_composite': False
            }
        
        return {
            'success': False,
            'code': '',
            'error': '无法识别的项目描述，请使用更具体的描述，如：LED闪烁、温湿度检测、舵机控制等',
            'suggestions': [
                'LED闪烁代码',
                '温湿度传感器读取',
                '舵机控制',
                '超声波测距',
                'LCD显示屏显示',
                '按钮控制LED',
                '模拟输入读取',
                '呼吸灯效果',
                '温湿度检测+LCD显示',
                '温湿度检测+WiFi上传'
            ],
            'detected_components': components
        }
    
    def _detect_components(self, description):
        """从描述中检测组件"""
        detected = []
        for component, keywords in _COMPONENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in description:
                    detected.append(component)
                    break
        return detected
    
    def _generate_composite_code(self, description, components):
        """生成多组件组合代码"""
        sorted_components = sorted(components)
        composition_key = '+'.join(sorted_components)
        
        if composition_key in _COMPOSITION_RULES:
            return self._build_composite_code_from_rule(composition_key, components)
        
        return self._build_composite_code_dynamically(components)
    
    def _build_composite_code_from_rule(self, composition_key, components):
        """根据组合规则生成代码"""
        rule = _COMPOSITION_RULES[composition_key]
        
        includes = []
        defines = []
        declarations = []
        functions = []
        setup_lines = []
        loop_lines = rule['loop']
        
        all_params = {}
        
        for comp in components:
            if comp in _COMPONENT_MODULES:
                module = _COMPONENT_MODULES[comp]
                includes.extend(module.get('includes', []))
                defines.extend(module.get('defines', []))
                declarations.extend(module.get('declarations', []))
                functions.extend(module.get('functions', []))
                setup_lines.extend(module.get('setup', []))
                all_params.update(module.get('params', {}))
        
        includes = list(dict.fromkeys(includes))
        defines = list(dict.fromkeys(defines))
        declarations = list(dict.fromkeys(declarations))
        functions = list(dict.fromkeys(functions))
        setup_lines = list(dict.fromkeys(setup_lines))
        
        if 'Serial.begin(9600);' not in setup_lines:
            setup_lines.insert(0, 'Serial.begin(9600);')
        
        code_lines = []
        code_lines.extend(includes)
        code_lines.append('')
        code_lines.extend(defines)
        code_lines.append('')
        code_lines.extend(declarations)
        code_lines.append('')
        code_lines.extend(functions)
        if functions:
            code_lines.append('')
        
        code_lines.append('void setup() {')
        for line in setup_lines:
            code_lines.append('  ' + line)
        code_lines.append('}')
        code_lines.append('')
        
        code_lines.append('void loop() {')
        for line in loop_lines:
            code_lines.append('  ' + line)
        code_lines.append('}')
        
        final_code = '\n'.join(code_lines)
        
        for key, value in all_params.items():
            final_code = final_code.replace(f'{{{{{key}}}}}', str(value))
        
        return {
            'success': True,
            'code': final_code,
            'template': 'composite',
            'composition_key': composition_key,
            'description': rule['description'],
            'params': all_params,
            'suggested_components': ['arduino_uno'] + components,
            'detected_components': components,
            'is_composite': True
        }
    
    def _build_composite_code_dynamically(self, components):
        """动态构建组合代码（当没有预定义规则时）"""
        includes = []
        defines = []
        declarations = []
        functions = []
        setup_lines = []
        loop_lines = []
        
        all_params = {}
        used_variables = []
        
        for comp in components:
            if comp in _COMPONENT_MODULES:
                module = _COMPONENT_MODULES[comp]
                includes.extend(module.get('includes', []))
                defines.extend(module.get('defines', []))
                declarations.extend(module.get('declarations', []))
                functions.extend(module.get('functions', []))
                setup_lines.extend(module.get('setup', []))
                all_params.update(module.get('params', {}))
                used_variables.extend(module.get('variables', []))
        
        includes = list(dict.fromkeys(includes))
        defines = list(dict.fromkeys(defines))
        declarations = list(dict.fromkeys(declarations))
        functions = list(dict.fromkeys(functions))
        setup_lines = list(dict.fromkeys(setup_lines))
        
        if 'Serial.begin(9600);' not in setup_lines:
            setup_lines.insert(0, 'Serial.begin(9600);')
        
        for comp in components:
            if comp in _COMPONENT_MODULES:
                module = _COMPONENT_MODULES[comp]
                loop_lines.extend(module.get('loop', []))
        
        if not loop_lines:
            loop_lines.append('delay(1000);')
        
        code_lines = []
        code_lines.extend(includes)
        code_lines.append('')
        code_lines.extend(defines)
        code_lines.append('')
        code_lines.extend(declarations)
        code_lines.append('')
        code_lines.extend(functions)
        if functions:
            code_lines.append('')
        
        code_lines.append('void setup() {')
        for line in setup_lines:
            code_lines.append('  ' + line)
        code_lines.append('}')
        code_lines.append('')
        
        code_lines.append('void loop() {')
        for line in loop_lines:
            code_lines.append('  ' + line)
        code_lines.append('}')
        
        final_code = '\n'.join(code_lines)
        
        for key, value in all_params.items():
            final_code = final_code.replace(f'{{{{{key}}}}}', str(value))
        
        return {
            'success': True,
            'code': final_code,
            'template': 'composite_dynamic',
            'composition_key': '+'.join(sorted(components)),
            'description': '多组件组合项目',
            'params': all_params,
            'suggested_components': ['arduino_uno'] + components,
            'detected_components': components,
            'is_composite': True
        }
    
    def _suggest_components(self, template_key):
        """根据模板建议组件"""
        suggestions = {
            'led_blink': ['arduino_uno', 'led'],
            'dht11_read': ['arduino_uno', 'dht11'],
            'servo_control': ['arduino_uno', 'servo'],
            'ultrasonic': ['arduino_uno', 'ultrasonic'],
            'lcd_display': ['arduino_uno', 'lcd1602'],
            'pwm_fade': ['arduino_uno', 'led'],
            'button_control': ['arduino_uno', 'button', 'led'],
            'analog_read': ['arduino_uno', 'potentiometer']
        }
        return suggestions.get(template_key, [])
    
    def analyze_sensor_data(self, device_id, sensor_type=None, window_size=20):
        """AI传感器数据分析 - 异常检测、趋势预测、智能洞察"""
        self.cursor.execute('''
            SELECT value, timestamp FROM sensor_data 
            WHERE device_id = ?
            ''' + (f'AND sensor_type = ?' if sensor_type else '') + '''
            ORDER BY timestamp DESC LIMIT ?
        ''', ([device_id, sensor_type, window_size] if sensor_type else [device_id, window_size]))
        
        data = [dict(row) for row in self.cursor.fetchall()]
        
        if len(data) < 3:
            return {
                'success': False,
                'error': '数据量不足，至少需要3条数据进行分析'
            }
        
        values = [float(d['value']) for d in data]
        timestamps = [d['timestamp'] for d in data]
        
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance)
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val
        
        anomalies = []
        for i, val in enumerate(values):
            z_score = abs((val - mean_val) / std_dev) if std_dev > 0 else 0
            if z_score > 2.5:
                anomalies.append({
                    'index': i,
                    'value': val,
                    'timestamp': timestamps[i],
                    'z_score': round(z_score, 2),
                    'deviation': round(abs(val - mean_val), 2)
                })
        
        trend = 'stable'
        if len(values) >= 5:
            recent = values[:5]
            older = values[-5:]
            recent_mean = sum(recent) / len(recent)
            older_mean = sum(older) / len(older)
            change = (recent_mean - older_mean)
            
            if abs(change) > mean_val * 0.1:
                trend = 'increasing' if change > 0 else 'decreasing'
        
        insights = []
        if len(anomalies) > 0:
            insights.append(f"检测到 {len(anomalies)} 个异常数据点，建议检查传感器是否正常工作")
        if trend == 'increasing':
            insights.append("数据呈上升趋势，建议关注数值变化")
        if trend == 'decreasing':
            insights.append("数据呈下降趋势，建议关注数值变化")
        if std_dev > mean_val * 0.2:
            insights.append("数据波动较大，建议增加采样频率")
        
        prediction = None
        if len(values) >= 10:
            prediction = self._simple_prediction(values)
        
        return {
            'success': True,
            'device_id': device_id,
            'sensor_type': sensor_type,
            'data_count': len(data),
            'statistics': {
                'mean': round(mean_val, 2),
                'std_dev': round(std_dev, 2),
                'min': round(min_val, 2),
                'max': round(max_val, 2),
                'range': round(range_val, 2),
                'variance': round(variance, 2)
            },
            'anomalies': anomalies,
            'trend': trend,
            'insights': insights,
            'prediction': prediction,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _simple_prediction(self, values):
        """简单线性预测下一个值"""
        n = len(values)
        if n < 3:
            return None
        
        x = list(range(n))
        y = values
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        next_val = y[-1] + slope
        return {
            'next_value': round(next_val, 2),
            'slope': round(slope, 4),
            'confidence': min(0.8, 0.3 + len(values) * 0.05)
        }
    
    def debug_code(self, code, simulation_result=None):
        """AI代码调试助手 - 分析代码并提供调试建议"""
        issues = []
        suggestions = []
        
        if 'pinMode(' not in code:
            issues.append({
                'severity': 'warning',
                'message': '未发现pinMode()调用',
                'suggestion': '建议在setup()中使用pinMode()设置引脚模式'
            })
        
        if 'digitalWrite(' in code and 'pinMode(' not in code:
            issues.append({
                'severity': 'error',
                'message': '使用digitalWrite()但未设置引脚模式',
                'suggestion': '在setup()中添加pinMode(pin, OUTPUT)'
            })
        
        if 'analogRead(' in code and 'Serial.begin(' not in code:
            issues.append({
                'severity': 'info',
                'message': '使用analogRead()但未初始化串口',
                'suggestion': '建议添加Serial.begin(9600)并使用Serial.println()输出数据'
            })
        
        if '#include <DHT.h>' in code and ('dht.begin()' not in code):
            issues.append({
                'severity': 'error',
                'message': '引入DHT库但未初始化',
                'suggestion': '在setup()中添加dht.begin()'
            })
        
        if '#include <Servo.h>' in code and ('.attach(' not in code):
            issues.append({
                'severity': 'error',
                'message': '引入Servo库但未连接舵机',
                'suggestion': '在setup()中添加myservo.attach(pin)'
            })
        
        delay_match = re.search(r'delay\s*\(\s*(\d+)\s*\)', code)
        if delay_match and int(delay_match.group(1)) > 5000:
            issues.append({
                'severity': 'warning',
                'message': '发现长时间delay()调用',
                'suggestion': '建议使用非阻塞方式替代长延时'
            })
        
        if simulation_result:
            if 'LED' in code and not simulation_result.get('led_states'):
                issues.append({
                    'severity': 'warning',
                    'message': '代码中有LED操作但模拟结果未显示LED状态',
                    'suggestion': '检查LED引脚是否正确设置为OUTPUT模式'
                })
            
            if 'Serial' in code and not simulation_result.get('serial_output'):
                issues.append({
                    'severity': 'warning',
                    'message': '代码中有串口输出但模拟结果无串口数据',
                    'suggestion': '检查Serial.begin()是否在setup()中调用'
                })
        
        if not issues:
            suggestions.append('代码结构良好，未发现明显问题')
            suggestions.append('建议通过仿真验证功能正确性')
            suggestions.append('考虑添加错误处理和边界检查')
        
        return {
            'success': True,
            'issues': issues,
            'suggestions': suggestions,
            'issue_count': len(issues),
            'has_errors': any(i['severity'] == 'error' for i in issues),
            'has_warnings': any(i['severity'] == 'warning' for i in issues)
        }
    
    def recommend_components(self, project_description, budget=None):
        """AI硬件推荐引擎 - 根据项目需求智能推荐组件"""
        description = project_description.lower()
        
        required_components = []
        recommended_components = []
        
        if any(k in description for k in ['led', '灯', '发光']):
            required_components.append('led')
        if any(k in description for k in ['温湿度', '湿度', 'dht']):
            required_components.append('dht11')
        if any(k in description for k in ['舵机', '电机', '转动']):
            required_components.append('servo')
        if any(k in description for k in ['距离', '超声波']):
            required_components.append('ultrasonic')
        if any(k in description for k in ['显示', '屏幕']):
            required_components.append('lcd1602')
        if any(k in description for k in ['按钮', '按键']):
            required_components.append('button')
        if any(k in description for k in ['电位器', '旋钮']):
            required_components.append('potentiometer')
        if any(k in description for k in ['蜂鸣器', '声音']):
            required_components.append('buzzer')
        
        if any(k in description for k in ['wifi', '联网', '网络']):
            recommended_components.append('esp8266')
        if any(k in description for k in ['蓝牙', '无线']):
            recommended_components.append('bluetooth')
        
        controller = 'arduino_uno'
        if len(required_components) > 5:
            controller = 'arduino_mega'
        
        all_components = [controller] + required_components + recommended_components
        
        total_price = sum(_COMPONENT_LIBRARY.get(c, {}).get('price', 0) for c in all_components)
        
        if budget and total_price > budget:
            alternatives = []
            if 'arduino_mega' in all_components and budget < 200:
                alternatives.append(('arduino_mega', 'arduino_nano', '使用Arduino Nano替代Arduino Mega，节省成本'))
            if 'dht22' in all_components and budget < total_price:
                alternatives.append(('dht22', 'dht11', '使用DHT11替代DHT22，降低成本'))
            if 'lcd1602' in all_components and budget < total_price:
                alternatives.append(('lcd1602', None, '考虑使用串口输出代替LCD显示'))
            
            return {
                'success': True,
                'components': [_COMPONENT_LIBRARY.get(c) for c in all_components],
                'total_price': total_price,
                'budget': budget,
                'over_budget': total_price - budget,
                'alternatives': alternatives,
                'recommendation': '建议调整方案或增加预算'
            }
        
        wiring_guide = self._generate_wiring_guide(all_components)
        
        return {
            'success': True,
            'components': [_COMPONENT_LIBRARY.get(c) for c in all_components],
            'total_price': total_price,
            'budget': budget,
            'controller': controller,
            'wiring_guide': wiring_guide,
            'recommendation': '方案推荐'
        }
    
    def _generate_wiring_guide(self, components):
        """生成接线指南"""
        guides = []
        
        if 'dht11' in components:
            guides.append({
                'component': 'DHT11',
                'connections': [
                    {'pin': 'VCC', 'connect_to': '5V'},
                    {'pin': 'GND', 'connect_to': 'GND'},
                    {'pin': 'DATA', 'connect_to': '数字引脚2'}
                ]
            })
        
        if 'servo' in components:
            guides.append({
                'component': 'SG90舵机',
                'connections': [
                    {'pin': 'VCC', 'connect_to': '5V'},
                    {'pin': 'GND', 'connect_to': 'GND'},
                    {'pin': 'SIGNAL', 'connect_to': 'PWM引脚9'}
                ]
            })
        
        if 'ultrasonic' in components:
            guides.append({
                'component': 'HC-SR04',
                'connections': [
                    {'pin': 'VCC', 'connect_to': '5V'},
                    {'pin': 'GND', 'connect_to': 'GND'},
                    {'pin': 'TRIG', 'connect_to': '数字引脚9'},
                    {'pin': 'ECHO', 'connect_to': '数字引脚10'}
                ]
            })
        
        if 'lcd1602' in components:
            guides.append({
                'component': 'LCD 1602',
                'connections': [
                    {'pin': 'VSS', 'connect_to': 'GND'},
                    {'pin': 'VDD', 'connect_to': '5V'},
                    {'pin': 'VO', 'connect_to': '电位器中间引脚'},
                    {'pin': 'RS', 'connect_to': '数字引脚12'},
                    {'pin': 'EN', 'connect_to': '数字引脚11'},
                    {'pin': 'D4', 'connect_to': '数字引脚5'},
                    {'pin': 'D5', 'connect_to': '数字引脚4'},
                    {'pin': 'D6', 'connect_to': '数字引脚3'},
                    {'pin': 'D7', 'connect_to': '数字引脚2'},
                    {'pin': 'A', 'connect_to': '5V'},
                    {'pin': 'K', 'connect_to': 'GND'}
                ]
            })
        
        if 'led' in components:
            guides.append({
                'component': 'LED',
                'connections': [
                    {'pin': '阳极(长脚)', 'connect_to': '数字引脚13(经220Ω电阻)'},
                    {'pin': '阴极(短脚)', 'connect_to': 'GND'}
                ]
            })
        
        return guides
    
    def assess_learning_progress(self, user_id):
        """评估用户Arduino学习进度"""
        self.cursor.execute('''
            SELECT * FROM arduino_projects WHERE user_id = ?
        ''', (user_id,))
        projects = [dict(row) for row in self.cursor.fetchall()]
        
        completed_projects = [p for p in projects if p.get('status') == 'completed']
        
        progress = {
            'user_id': user_id,
            'total_projects': len(projects),
            'completed_projects': len(completed_projects),
            'progress_percentage': round(len(completed_projects) / max(len(projects), 1) * 100, 2),
            'skills': [],
            'recommendations': []
        }
        
        skill_keywords = {
            'digital_io': ['led', 'button', 'digital'],
            'analog_io': ['potentiometer', 'analog', '光敏'],
            'sensors': ['dht', '温湿度', '超声波', '距离', '传感器'],
            'actuators': ['servo', '舵机', '蜂鸣器', '继电器'],
            'displays': ['lcd', '显示', '屏幕'],
            'communication': ['wifi', '蓝牙', '串口', 'esp']
        }
        
        for skill, keywords in skill_keywords.items():
            score = 0
            for project in projects:
                desc = (project.get('name', '') + ' ' + project.get('description', '')).lower()
                if any(k in desc for k in keywords):
                    score += 1
            progress['skills'].append({
                'skill': skill,
                'name': {
                    'digital_io': '数字I/O',
                    'analog_io': '模拟I/O',
                    'sensors': '传感器应用',
                    'actuators': '执行器控制',
                    'displays': '显示模块',
                    'communication': '通信模块'
                }.get(skill, skill),
                'score': score,
                'level': self._get_skill_level(score)
            })
        
        if len(completed_projects) == 0:
            progress['recommendations'].append('建议从简单项目开始，如LED闪烁')
        elif len(completed_projects) < 3:
            progress['recommendations'].append('继续完成更多项目以提升技能')
        else:
            progress['recommendations'].append('尝试更复杂的项目，如IoT集成')
        
        weak_skills = [s for s in progress['skills'] if s['score'] == 0]
        for skill in weak_skills:
            progress['recommendations'].append(f"建议学习{skill['name']}相关内容")
        
        return progress
    
    def _get_skill_level(self, score):
        """获取技能等级"""
        if score == 0:
            return '入门'
        elif score == 1:
            return '基础'
        elif score == 2:
            return '熟练'
        else:
            return '精通'
    
    def get_adaptive_learning_path(self, user_id):
        """AI自适应学习路径 - 根据学习进度动态推荐教程和项目"""
        progress = self.assess_learning_progress(user_id)
        
        learning_path = {
            'user_id': user_id,
            'current_progress': progress['progress_percentage'],
            'current_level': self._determine_level(progress),
            'recommended_tutorial': None,
            'recommended_project': None,
            'skill_gaps': [],
            'learning_plan': []
        }
        
        weak_skills = [s for s in progress['skills'] if s['score'] <= 1]
        strong_skills = [s for s in progress['skills'] if s['score'] >= 2]
        
        for skill in weak_skills:
            learning_path['skill_gaps'].append({
                'skill': skill['skill'],
                'name': skill['name'],
                'current_level': skill['level'],
                'target_level': '熟练',
                'priority': self._get_skill_priority(skill['skill'])
            })
        
        learning_path['skill_gaps'].sort(key=lambda x: x['priority'], reverse=True)
        
        learning_path['recommended_tutorial'] = self._recommend_tutorial(progress, weak_skills)
        learning_path['recommended_project'] = self._recommend_project(progress, weak_skills, strong_skills)
        
        learning_path['learning_plan'] = self._generate_learning_plan(learning_path)
        
        return learning_path
    
    def _determine_level(self, progress):
        """根据进度确定学习等级"""
        percentage = progress['progress_percentage']
        if percentage == 0:
            return '初学者'
        elif percentage < 30:
            return '入门学习者'
        elif percentage < 60:
            return '中级学习者'
        elif percentage < 90:
            return '高级学习者'
        else:
            return '专家'
    
    def _get_skill_priority(self, skill):
        """获取技能优先级"""
        priorities = {
            'digital_io': 10,
            'analog_io': 9,
            'sensors': 8,
            'actuators': 7,
            'displays': 6,
            'communication': 5
        }
        return priorities.get(skill, 5)
    
    def _recommend_tutorial(self, progress, weak_skills):
        """推荐教程"""
        tutorial_recommendations = []
        
        skill_tutorial_map = {
            'digital_io': [
                {'name': 'LED闪烁入门', 'difficulty': 'beginner', 'skill': 'digital_io'},
                {'name': '按钮控制LED', 'difficulty': 'beginner', 'skill': 'digital_io'}
            ],
            'analog_io': [
                {'name': '模拟输入读取', 'difficulty': 'beginner', 'skill': 'analog_io'},
                {'name': '呼吸灯效果', 'difficulty': 'intermediate', 'skill': 'analog_io'}
            ],
            'sensors': [
                {'name': '温湿度传感器', 'difficulty': 'intermediate', 'skill': 'sensors'},
                {'name': '超声波测距', 'difficulty': 'intermediate', 'skill': 'sensors'}
            ],
            'actuators': [
                {'name': '舵机控制', 'difficulty': 'intermediate', 'skill': 'actuators'}
            ],
            'displays': [
                {'name': 'LCD显示', 'difficulty': 'intermediate', 'skill': 'displays'}
            ],
            'communication': [
                {'name': 'WiFi模块数据上传', 'difficulty': 'advanced', 'skill': 'communication'}
            ]
        }
        
        if weak_skills:
            for skill in weak_skills[:2]:
                if skill['skill'] in skill_tutorial_map:
                    tutorials = skill_tutorial_map[skill['skill']]
                    for tutorial in tutorials[:1]:
                        tutorial_recommendations.append({
                            'name': tutorial['name'],
                            'difficulty': tutorial['difficulty'],
                            'skill': skill['name'],
                            'reason': f"您的{skill['name']}技能需要提升，建议学习此教程",
                            'estimated_time': '20分钟'
                        })
        else:
            tutorial_recommendations.append({
                'name': 'WiFi模块数据上传',
                'difficulty': 'advanced',
                'skill': '通信模块',
                'reason': '您已掌握基础技能，建议学习高级内容',
                'estimated_time': '30分钟'
            })
        
        return tutorial_recommendations
    
    def _recommend_project(self, progress, weak_skills, strong_skills):
        """推荐项目"""
        project_recommendations = []
        
        if progress['total_projects'] == 0:
            project_recommendations.append({
                'name': 'LED闪烁',
                'difficulty': 'beginner',
                'description': '学习控制LED灯闪烁，了解数字输出的基本概念',
                'skills': ['digital_io'],
                'estimated_time': '15分钟',
                'reason': '作为入门项目，帮助您熟悉Arduino开发流程'
            })
            return project_recommendations
        
        if weak_skills:
            first_weak_skill = weak_skills[0]
            weak_skill_projects = {
                'digital_io': {'name': '按钮控制LED', 'description': '学习数字输入和条件判断', 'difficulty': 'beginner'},
                'analog_io': {'name': '电位器控制LED亮度', 'description': '学习模拟输入和PWM输出', 'difficulty': 'beginner'},
                'sensors': {'name': '温湿度监控系统', 'description': '学习传感器数据采集', 'difficulty': 'intermediate'},
                'actuators': {'name': '舵机角度控制', 'description': '学习舵机控制', 'difficulty': 'intermediate'},
                'displays': {'name': 'LCD信息显示', 'description': '学习LCD显示', 'difficulty': 'intermediate'},
                'communication': {'name': 'WiFi数据上传', 'description': '学习网络通信', 'difficulty': 'advanced'}
            }
            
            if first_weak_skill['skill'] in weak_skill_projects:
                proj = weak_skill_projects[first_weak_skill['skill']]
                project_recommendations.append({
                    'name': proj['name'],
                    'difficulty': proj['difficulty'],
                    'description': proj['description'],
                    'skills': [first_weak_skill['skill']],
                    'estimated_time': '20分钟',
                    'reason': f"通过此项目提升{first_weak_skill['name']}技能"
                })
        
        if strong_skills and len(project_recommendations) < 2:
            first_strong_skill = strong_skills[0]
            composite_projects = {
                'digital_io': {'name': '智能灯光控制系统', 'description': '结合按钮和LED实现智能控制', 'difficulty': 'intermediate',
                'skills': ['digital_io', 'sensors']},
                'sensors': {'name': '环境监测站', 'description': '结合多种传感器', 'difficulty': 'advanced', 'skills': ['sensors',
                'displays']},
                'actuators': {'name': '智能小车', 'description': '结合舵机和传感器', 'difficulty': 'advanced',
                'skills': ['actuators', 'sensors']},
                'displays': {'name': '多功能信息显示', 'description': '结合LCD和传感器', 'difficulty': 'intermediate',
                'skills': ['displays', 'sensors']}
            }
            
            if first_strong_skill['skill'] in composite_projects:
                proj = composite_projects[first_strong_skill['skill']]
                project_recommendations.append({
                    'name': proj['name'],
                    'difficulty': proj['difficulty'],
                    'description': proj['description'],
                    'skills': proj['skills'],
                    'estimated_time': '30分钟',
                    'reason': f"利用已掌握的{first_strong_skill['name']}技能，挑战更复杂的组合项目"
                })
        
        return project_recommendations
    
    def _generate_learning_plan(self, learning_path):
        """生成学习计划"""
        plan = []
        
        current_week = 1
        
        if learning_path['recommended_tutorial']:
            for tutorial in learning_path['recommended_tutorial'][:2]:
                plan.append({
                    'week': current_week,
                    'type': 'tutorial',
                    'name': tutorial['name'],
                    'difficulty': tutorial['difficulty'],
                    'estimated_time': tutorial['estimated_time'],
                    'goal': tutorial['reason']
                })
                current_week += 1
        
        if learning_path['recommended_project']:
            for project in learning_path['recommended_project'][:2]:
                plan.append({
                    'week': current_week,
                    'type': 'project',
                    'name': project['name'],
                    'difficulty': project['difficulty'],
                    'estimated_time': project['estimated_time'],
                    'goal': project['reason']
                })
                current_week += 1
        
        plan.append({
            'week': current_week,
            'type': 'review',
            'name': '知识回顾与巩固',
            'difficulty': 'beginner',
            'estimated_time': '30分钟',
            'goal': '回顾已学内容，巩固知识'
        })
        
        return plan
    
    def get_component_library(self):
        """获取组件库"""
        return _COMPONENT_LIBRARY
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == '__main__':
    engine = ArduinoAIEngine()
    
    logger.info("=== Arduino AI智能引擎 ===")
    
    logger.info("\n1. AI代码生成器测试:")
    result = engine.generate_code("LED闪烁，使用引脚13")
    logger.info(f"   成功: {result['success']}")
    if result['success']:
        logger.info("   生成的代码:")
        logger.info(result['code'])
        logger.info(f"   建议组件: {result['suggested_components']}")
    
    logger.info("\n2. AI传感器数据分析测试:")
    result = engine.analyze_sensor_data('device_001', 'temperature')
    logger.info(f"   成功: {result['success']}")
    if result['success']:
        logger.info(f"   统计数据: {result['statistics']}")
        logger.info(f"   异常数量: {len(result['anomalies'])}")
        logger.info(f"   趋势: {result['trend']}")
        logger.info(f"   洞察: {result['insights']}")
    
    logger.info("\n3. AI代码调试助手测试:")
    test_code = '''int ledPin = 13;
void setup() {
  // 缺少pinMode
}
void loop() {
  digitalWrite(ledPin, HIGH);
  delay(1000);
}'''
    result = engine.debug_code(test_code)
    logger.info(f"   问题数量: {result['issue_count']}")
    logger.info(f"   有错误: {result['has_errors']}")
    for issue in result['issues']:
        logger.info(f"   - [{issue['severity']}] {issue['message']}")
    
    logger.info("\n4. AI硬件推荐引擎测试:")
    result = engine.recommend_components("温湿度检测系统，带LCD显示", budget=150)
    logger.info(f"   成功: {result['success']}")
    logger.info(f"   总价格: {result['total_price']}元")
    logger.info(f"   组件列表:")
    for comp in result['components']:
        logger.info(f"     - {comp['name']}: {comp['price']}元")
    if result.get('wiring_guide'):
        logger.info(f"   接线指南: {len(result['wiring_guide'])}个组件")
    
    logger.info("\n5. Arduino学习进度评估测试:")
    result = engine.assess_learning_progress(1)
    logger.info(f"   总项目数: {result['total_projects']}")
    logger.info(f"   完成项目数: {result['completed_projects']}")
    logger.info(f"   进度百分比: {result['progress_percentage']}%")
    logger.info(f"   技能掌握:")
    for skill in result['skills']:
        logger.info(f"     - {skill['name']}: {skill['level']}")
    logger.info(f"   建议: {result['recommendations']}")
    
    engine.close()