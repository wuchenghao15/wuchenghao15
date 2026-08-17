#!/usr/bin/env python3
import os
import json
from datetime import datetime

_TUTORIALS = {
    'beginner': [
        {
            'id': 'led_blink',
            'title': 'LED闪烁入门',
            'description': '学习控制LED灯闪烁，了解数字输出的基本概念',
            'duration': '15分钟',
            'difficulty': 'beginner',
            'steps': [
                {'step': 1, 'title': '硬件连接', 'content': '将LED灯正极通过220Ω电阻连接到数字引脚13，负极连接到GND'},
                {'step': 2, 'title': '理解setup()', 'content': 'setup()函数在程序开始时执行一次，用于初始化引脚模式'},
                {'step': 3, 'title': '理解loop()', 'content': 'loop()函数会无限循环执行，用于主程序逻辑'},
                {'step': 4, 'title': '数字输出', 'content': '使用digitalWrite()函数控制引脚输出高电平(HIGH)或低电平(LOW)'},
                {'step': 5, 'title': '延时函数', 'content': '使用delay()函数设置延时时间，单位为毫秒'}
            ],
            'code': '''int ledPin = 13;

void setup() {
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  digitalWrite(ledPin, HIGH);
  Serial.println("LED ON");
  delay(1000);
  digitalWrite(ledPin, LOW);
  Serial.println("LED OFF");
  delay(1000);
}''',
            'components': ['LED灯', '220Ω电阻', '面包板', '杜邦线']
        },
        {
            'id': 'button_control',
            'title': '按钮控制LED',
            'description': '学习使用按钮控制LED，了解数字输入的基本概念',
            'duration': '20分钟',
            'difficulty': 'beginner',
            'steps': [
                {'step': 1, 'title': '硬件连接', 'content': '将按钮一端连接到数字引脚2，另一端连接到5V。引脚2通过10kΩ下拉电阻连接到GND'},
                {'step': 2, 'title': '输入模式', 'content': '使用pinMode()将引脚设置为INPUT模式'},
                {'step': 3, 'title': '读取输入', 'content': '使用digitalRead()读取引脚状态，返回HIGH或LOW'},
                {'step': 4, 'title': '条件判断', 'content': '使用if语句判断按钮状态，控制LED亮灭'}
            ],
            'code': '''int buttonPin = 2;
int ledPin = 13;
int buttonState = 0;

void setup() {
  pinMode(buttonPin, INPUT);
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  buttonState = digitalRead(buttonPin);
  Serial.logger.info("Button: ");
  Serial.println(buttonState);
  
  if (buttonState == HIGH) {
    digitalWrite(ledPin, HIGH);
  } else {
    digitalWrite(ledPin, LOW);
  }
}''',
            'components': ['LED灯', '按钮', '10kΩ电阻', '220Ω电阻', '面包板', '杜邦线']
        },
        {
            'id': 'analog_read',
            'title': '模拟输入读取',
            'description': '学习读取模拟传感器数据，了解模拟输入的基本概念',
            'duration': '20分钟',
            'difficulty': 'beginner',
            'steps': [
                {'step': 1, 'title': '硬件连接', 'content': '将电位器一端连接到5V，另一端连接到GND，中间引脚连接到模拟引脚A0'},
                {'step': 2, 'title': '模拟引脚', 'content': 'Arduino有6个模拟引脚(A0-A5)，用于读取模拟信号(0-1023)'},
                {'step': 3, 'title': 'analogRead()', 'content': '使用analogRead()读取模拟值，返回0-1023之间的整数'},
                {'step': 4, 'title': '串口调试', 'content': '使用Serial.println()输出传感器数据到串口监视器'}
            ],
            'code': '''int potPin = A0;
int sensorValue = 0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  sensorValue = analogRead(potPin);
  Serial.logger.info("Sensor Value: ");
  Serial.println(sensorValue);
  delay(100);
}''',
            'components': ['电位器', '面包板', '杜邦线']
        }
    ],
    'intermediate': [
        {
            'id': 'pwm_fade',
            'title': '呼吸灯效果',
            'description': '学习使用PWM实现LED渐亮渐灭效果',
            'duration': '25分钟',
            'difficulty': 'intermediate',
            'steps': [
                {'step': 1, 'title': 'PWM引脚', 'content': 'Arduino Uno有6个PWM引脚(3,5,6,9,10,11)，支持模拟输出'},
                {'step': 2, 'title': 'analogWrite()', 'content': '使用analogWrite()输出PWM信号，参数范围0-255'},
                {'step': 3, 'title': '亮度变化', 'content': '使用变量控制亮度值，从0渐增到255，再从255渐减到0'},
                {'step': 4, 'title': '呼吸效果', 'content': '通过调整亮度变化速度，实现平滑的呼吸灯效果'}
            ],
            'code': '''int ledPin = 9;
int brightness = 0;
int fadeAmount = 5;

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
  
  Serial.logger.info("Brightness: ");
  Serial.println(brightness);
  delay(30);
}''',
            'components': ['LED灯', '220Ω电阻', '面包板', '杜邦线']
        },
        {
            'id': 'servo_control',
            'title': '舵机控制',
            'description': '学习控制舵机转动到指定角度',
            'duration': '30分钟',
            'difficulty': 'intermediate',
            'steps': [
                {'step': 1, 'title': '引入Servo库', 'content': '使用#include <Servo.h>引入舵机控制库'},
                {'step': 2, 'title': '创建Servo对象', 'content': '使用Servo myservo;创建舵机对象'},
                {'step': 3, 'title': '连接舵机', 'content': '使用myservo.attach(pin)将舵机连接到指定引脚'},
                {'step': 4, 'title': '控制角度', 'content': '使用myservo.write(angle)控制舵机转动到指定角度(0-180度)'},
                {'step': 5, 'title': '角度扫描', 'content': '使用for循环实现舵机从0度到180度的扫描'}
            ],
            'code': '''#include <Servo.h>

Servo myservo;
int pos = 0;

void setup() {
  myservo.attach(9);
  Serial.begin(9600);
}

void loop() {
  for (pos = 0; pos <= 180; pos += 1) {
    myservo.write(pos);
    Serial.logger.info("Servo: ");
    Serial.println(pos);
    delay(15);
  }
  for (pos = 180; pos >= 0; pos -= 1) {
    myservo.write(pos);
    Serial.logger.info("Servo: ");
    Serial.println(pos);
    delay(15);
  }
}''',
            'components': ['舵机', '面包板', '杜邦线']
        },
        {
            'id': 'ultrasonic',
            'title': '超声波测距',
            'description': '学习使用超声波传感器测量距离',
            'duration': '30分钟',
            'difficulty': 'intermediate',
            'steps': [
                {'step': 1, 'title': '传感器原理', 'content': '超声波传感器通过发射超声波并测量回波时间来计算距离'},
                {'step': 2, 'title': '硬件连接', 'content': 'Trig引脚连接到数字引脚9，Echo引脚连接到数字引脚10'},
                {'step': 3, 'title': '发送触发信号', 'content': '向Trig引脚发送10微秒的高电平触发信号'},
                {'step': 4, 'title': '测量回波时间', 'content': '使用pulseIn()测量Echo引脚高电平持续时间'},
                {'step': 5, 'title': '计算距离', 'content': '距离(cm) = 时间(μs) × 0.034 / 2'}
            ],
            'code': '''#define TRIG_PIN 9
#define ECHO_PIN 10

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
  Serial.logger.info("Distance: ");
  Serial.logger.info(dist);
  Serial.println(" cm");
  delay(500);
}''',
            'components': ['HC-SR04超声波传感器', '面包板', '杜邦线']
        }
    ],
    'advanced': [
        {
            'id': 'lcd_display',
            'title': 'LCD显示屏',
            'description': '学习使用LCD 1602显示信息',
            'duration': '35分钟',
            'difficulty': 'advanced',
            'steps': [
                {'step': 1, 'title': '引入LiquidCrystal库', 'content': '使用#include <LiquidCrystal.h>引入LCD库'},
                {'step': 2, 'title': '初始化LCD', 'content': '使用LiquidCrystal lcd(rs, en, d4, d5, d6, d7)初始化LCD对象'},
                {'step': 3, 'title': '设置显示', 'content': '使用lcd.begin(cols, rows)设置显示行列数'},
                {'step': 4, 'title': '显示文本', 'content': '使用lcd.logger.info()显示文本，lcd.setCursor()设置光标位置'},
                {'step': 5, 'title': '动态显示', 'content': '在第二行显示系统运行时间'}
            ],
            'code': '''#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

void setup() {
  lcd.begin(16, 2);
  lcd.logger.info("Hello, Arduino!");
  Serial.begin(9600);
}

void loop() {
  lcd.setCursor(0, 1);
  lcd.logger.info(millis() / 1000);
  lcd.logger.info(" seconds");
  delay(1000);
}''',
            'components': ['LCD 1602显示屏', '面包板', '杜邦线']
        },
        {
            'id': 'dht_sensor',
            'title': '温湿度传感器',
            'description': '学习使用DHT系列传感器读取温湿度数据',
            'duration': '40分钟',
            'difficulty': 'advanced',
            'steps': [
                {'step': 1, 'title': '安装DHT库', 'content': '在Arduino库管理器中搜索并安装DHT库'},
                {'step': 2, 'title': '引入DHT库', 'content': '使用#include <DHT.h>引入DHT库'},
                {'step': 3, 'title': '初始化传感器', 'content': '使用DHT dht(pin, type)创建传感器对象'},
                {'step': 4, 'title': '读取数据', 'content': '使用dht.readHumidity()和dht.readTemperature()读取数据'},
                {'step': 5, 'title': '数据处理', 'content': '将温湿度数据通过串口输出'}
            ],
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
  
  Serial.logger.info("Humidity: ");
  Serial.logger.info(h);
  Serial.logger.info("%\t");
  Serial.logger.info("Temperature: ");
  Serial.logger.info(t);
  Serial.println("°C");
  
  delay(2000);
}''',
            'components': ['DHT11/DHT22温湿度传感器', '面包板', '杜邦线']
        }
    ]
}

class ArduinoTutorialManager:
    """Arduino教学助手 - 提供Arduino学习教程和指导"""
    
    def __init__(self):
        self.tutorials = _TUTORIALS
    
    def get_tutorials(self, difficulty=None):
        """获取教程列表"""
        if difficulty and difficulty in self.tutorials:
            return self.tutorials[difficulty]
        all_tutorials = []
        for level, tutorials in self.tutorials.items():
            all_tutorials.extend(tutorials)
        return all_tutorials
    
    def get_tutorial(self, tutorial_id):
        """获取单个教程"""
        for level in self.tutorials.values():
            for tutorial in level:
                if tutorial['id'] == tutorial_id:
                    return tutorial
        return None
    
    def get_tutorial_by_level(self, level):
        """按难度等级获取教程"""
        levels = {
            '入门': 'beginner',
            '初级': 'beginner',
            '中级': 'intermediate',
            '高级': 'advanced'
        }
        key = levels.get(level, level)
        return self.tutorials.get(key, [])
    
    def get_tutorial_categories(self):
        """获取教程分类"""
        categories = []
        for level, tutorials in self.tutorials.items():
            categories.append({
                'level': level,
                'level_name': {'beginner': '入门', 'intermediate': '中级', 'advanced': '高级'}[level],
                'count': len(tutorials)
            })
        return categories
    
    def search_tutorials(self, keyword):
        """搜索教程"""
        results = []
        keyword = keyword.lower()
        for level in self.tutorials.values():
            for tutorial in level:
                if keyword in tutorial['title'].lower() or keyword in tutorial['description'].lower():
                    results.append(tutorial)
        return results
    
    def get_learning_path(self, level='beginner'):
        """获取学习路径"""
        paths = {
            'beginner': [
                {'step': 1, 'tutorial_id': 'led_blink', 'title': 'LED闪烁入门', 'description': '掌握数字输出基础'},
                {'step': 2, 'tutorial_id': 'button_control', 'title': '按钮控制LED', 'description': '掌握数字输入基础'},
                {'step': 3, 'tutorial_id': 'analog_read', 'title': '模拟输入读取', 'description': '掌握模拟输入基础'}
            ],
            'intermediate': [
                {'step': 1, 'tutorial_id': 'pwm_fade', 'title': '呼吸灯效果', 'description': '掌握PWM输出'},
                {'step': 2, 'tutorial_id': 'servo_control', 'title': '舵机控制', 'description': '掌握舵机控制'},
                {'step': 3, 'tutorial_id': 'ultrasonic', 'title': '超声波测距', 'description': '掌握传感器使用'}
            ],
            'advanced': [
                {'step': 1, 'tutorial_id': 'lcd_display', 'title': 'LCD显示屏', 'description': '掌握显示模块'},
                {'step': 2, 'tutorial_id': 'dht_sensor', 'title': '温湿度传感器', 'description': '掌握环境传感器'}
            ]
        }
        return paths.get(level, [])

if __name__ == '__main__':
    tutor = ArduinoTutorialManager()
    
    logger.info("=== Arduino教学助手 ===")
    
    categories = tutor.get_tutorial_categories()
    logger.info("\n教程分类:")
    for cat in categories:
        logger.info(f"  {cat['level_name']}: {cat['count']}个教程")
    
    beginner = tutor.get_tutorial_by_level('beginner')
    logger.info(f"\n入门教程: {len(beginner)}个")
    for t in beginner:
        logger.info(f"  - {t['title']} ({t['duration']})")
    
    tutorial = tutor.get_tutorial('led_blink')
    logger.info(f"\n教程详情: {tutorial['title']}")
    logger.info(f"描述: {tutorial['description']}")
    logger.info(f"步骤数: {len(tutorial['steps'])}")
    
    path = tutor.get_learning_path('beginner')
    logger.info("\n学习路径:")
    for p in path:
        logger.info(f"  {p['step']}. {p['title']} - {p['description']}")
    
    results = tutor.search_tutorials('LED')
    logger.info(f"\n搜索'LED': {len(results)}个结果")
    for r in results:
        logger.info(f"  - {r['title']}")