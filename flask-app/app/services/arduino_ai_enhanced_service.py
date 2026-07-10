# -*- coding: utf-8 -*-
"""
Arduino AI增强服务
提供AI代码生成、项目管理、教学课程、仿真等高级功能
"""

import os
import json
import time
import uuid
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger('ArduinoAIEnhancedService')

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'split_databases/arduino.db')


class ArduinoAIEnhancedService:
    """Arduino AI增强服务"""
    
    def __init__(self):
        self._ensure_db()
    
    def _get_db(self):
        """获取数据库连接"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_db(self):
        """确保数据库表存在"""
        try:
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS arduino_projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        project_name TEXT NOT NULL,
                        description TEXT,
                        board_type TEXT DEFAULT 'uno',
                        code TEXT,
                        circuit_data TEXT,
                        tags TEXT,
                        is_public INTEGER DEFAULT 0,
                        fork_count INTEGER DEFAULT 0,
                        star_count INTEGER DEFAULT 0,
                        created_at REAL,
                        updated_at REAL
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS arduino_tutorials (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        category TEXT,
                        difficulty TEXT DEFAULT 'beginner',
                        content TEXT,
                        code_example TEXT,
                        components TEXT,
                        duration INTEGER DEFAULT 30,
                        order_num INTEGER DEFAULT 0,
                        is_published INTEGER DEFAULT 1,
                        created_at REAL
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS arduino_ai_prompts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT,
                        prompt_key TEXT UNIQUE,
                        prompt_template TEXT,
                        description TEXT,
                        created_at REAL
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS arduino_user_progress (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        tutorial_id INTEGER,
                        project_id INTEGER,
                        completed_at REAL,
                        notes TEXT
                    )
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_arduino_projects_user 
                    ON arduino_projects(user_id)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_arduino_tutorials_cat 
                    ON arduino_tutorials(category)
                ''')
                
                conn.commit()
                
                self._init_default_tutorials()
                self._init_ai_prompts()
        except Exception as e:
            logger.error(f"初始化Arduino数据库失败: {e}")
    
    def _init_default_tutorials(self):
        """初始化默认教程"""
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) as count FROM arduino_tutorials")
                if cursor.fetchone()['count'] > 0:
                    return
                
                tutorials = [
                    {
                        'title': 'Arduino入门：LED闪烁',
                        'description': '学习Arduino基础，让LED灯闪烁起来',
                        'category': '入门',
                        'difficulty': 'beginner',
                        'duration': 15,
                        'order_num': 1,
                        'content': '''
# Arduino入门：LED闪烁

## 学习目标
- 了解Arduino的基本结构
- 学会编写第一个Arduino程序
- 掌握数字输出的基本用法

## 什么是Arduino？
Arduino是一款便捷灵活、方便上手的开源电子原型平台。它包含硬件（各种型号的Arduino板）和软件（Arduino IDE）。

## 所需元件
- Arduino Uno 板 x1
- LED灯 x1
- 220Ω电阻 x1
- 面包板 x1
- 杜邦线若干

## 电路连接
1. LED长脚（正极）通过220Ω电阻连接到数字引脚13
2. LED短脚（负极）连接到GND

## 代码解释
''' + "```cpp" + '''
// setup()函数只在启动时运行一次
void setup() {
  // 设置引脚13为输出模式
  pinMode(LED_BUILTIN, OUTPUT);
}

// loop()函数会反复运行
void loop() {
  // 点亮LED
  digitalWrite(LED_BUILTIN, HIGH);
  // 等待1秒
  delay(1000);
  // 熄灭LED
  digitalWrite(LED_BUILTIN, LOW);
  // 再等待1秒
  delay(1000);
}
''' + "```" + '''

## 关键知识点
1. **pinMode()**: 设置引脚模式（输入/输出）
2. **digitalWrite()**: 设置引脚电平（HIGH/LOW）
3. **delay()**: 延时函数（单位毫秒）
4. **setup()**: 初始化函数，只运行一次
5. **loop()**: 主循环函数，反复运行
                        ''',
                        'code_example': '''void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
}''',
                        'components': json.dumps(['Arduino Uno', 'LED灯', '220Ω电阻', '面包板', '杜邦线'], ensure_ascii=False)
                    },
                    {
                        'title': '按钮控制LED',
                        'description': '学习数字输入，用按钮控制LED灯',
                        'category': '入门',
                        'difficulty': 'beginner',
                        'duration': 20,
                        'order_num': 2,
                        'content': '''
# 按钮控制LED

## 学习目标
- 学习数字输入的用法
- 掌握按钮的工作原理
- 了解上拉电阻和下拉电阻

## 所需元件
- Arduino Uno 板 x1
- LED灯 x1
- 按钮开关 x1
- 220Ω电阻 x2
- 10kΩ电阻 x1
- 面包板 x1
- 杜邦线若干
                        ''',
                        'code_example': '''const int buttonPin = 2;
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
}''',
                        'components': json.dumps(['Arduino Uno', 'LED灯', '按钮开关', '电阻', '面包板', '杜邦线'], ensure_ascii=False)
                    },
                    {
                        'title': '模拟传感器读取',
                        'description': '学习模拟输入，读取电位器数值',
                        'category': '基础',
                        'difficulty': 'beginner',
                        'duration': 20,
                        'order_num': 3,
                        'content': '''
# 模拟传感器读取

## 学习目标
- 了解模拟输入的概念
- 学会使用analogRead()函数
- 掌握串口通信的基本用法
                        ''',
                        'code_example': '''const int sensorPin = A0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  int sensorValue = analogRead(sensorPin);
  Serial.print("传感器值: ");
  Serial.println(sensorValue);
  delay(500);
}''',
                        'components': json.dumps(['Arduino Uno', '电位器', '面包板', '杜邦线'], ensure_ascii=False)
                    },
                    {
                        'title': 'PWM调光控制',
                        'description': '使用PWM控制LED亮度',
                        'category': '基础',
                        'difficulty': 'intermediate',
                        'duration': 25,
                        'order_num': 4,
                        'content': '''
# PWM调光控制

## 学习目标
- 了解PWM（脉冲宽度调制）的原理
- 学会使用analogWrite()函数
- 实现LED呼吸灯效果
                        ''',
                        'code_example': '''const int ledPin = 9;

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
}''',
                        'components': json.dumps(['Arduino Uno', 'LED灯', '220Ω电阻', '面包板', '杜邦线'], ensure_ascii=False)
                    },
                    {
                        'title': '串口通信',
                        'description': '学习Arduino与电脑的串口通信',
                        'category': '通信',
                        'difficulty': 'intermediate',
                        'duration': 30,
                        'order_num': 5,
                        'content': '''
# 串口通信

## 学习目标
- 了解串口通信的原理
- 学会发送和接收串口数据
- 实现交互式控制
                        ''',
                        'code_example': '''void setup() {
  Serial.begin(9600);
  Serial.println("Arduino 串口通信测试");
  Serial.println("请输入指令:");
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\\n');
    input.trim();
    
    Serial.print("收到: ");
    Serial.println(input);
    
    if (input == "on") {
      digitalWrite(LED_BUILTIN, HIGH);
      Serial.println("LED已点亮");
    } else if (input == "off") {
      digitalWrite(LED_BUILTIN, LOW);
      Serial.println("LED已熄灭");
    }
  }
}''',
                        'components': json.dumps(['Arduino Uno', 'USB线'], ensure_ascii=False)
                    },
                    {
                        'title': '舵机控制',
                        'description': '学习使用Servo库控制舵机',
                        'category': '控制',
                        'difficulty': 'intermediate',
                        'duration': 25,
                        'order_num': 6,
                        'content': '''
# 舵机控制

## 学习目标
- 了解舵机的工作原理
- 学会使用Servo库
- 实现舵机角度控制
                        ''',
                        'code_example': '''#include <Servo.h>

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
}''',
                        'components': json.dumps(['Arduino Uno', '舵机', '面包板', '杜邦线'], ensure_ascii=False)
                    },
                    {
                        'title': 'DHT11温湿度传感器',
                        'description': '学习读取温湿度数据',
                        'category': '传感器',
                        'difficulty': 'intermediate',
                        'duration': 30,
                        'order_num': 7,
                        'content': '''
# DHT11温湿度传感器

## 学习目标
- 了解DHT11传感器的工作原理
- 学会安装和使用第三方库
- 读取温湿度数据并显示
                        ''',
                        'code_example': '''#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();
}

void loop() {
  delay(2000);
  
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  
  if (isnan(h) || isnan(t)) {
    Serial.println("读取失败！");
    return;
  }
  
  Serial.print("湿度: ");
  Serial.print(h);
  Serial.print("%  温度: ");
  Serial.print(t);
  Serial.println("°C");
}''',
                        'components': json.dumps(['Arduino Uno', 'DHT11传感器', '面包板', '杜邦线'], ensure_ascii=False)
                    },
                    {
                        'title': 'LCD1602显示屏',
                        'description': '学习使用LCD显示屏显示信息',
                        'category': '显示',
                        'difficulty': 'intermediate',
                        'duration': 30,
                        'order_num': 8,
                        'content': '''
# LCD1602显示屏

## 学习目标
- 了解LCD1602的工作原理
- 学会使用LiquidCrystal库
- 实现文本显示和滚动效果
                        ''',
                        'code_example': '''#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

void setup() {
  lcd.begin(16, 2);
  lcd.print("Hello, Arduino!");
}

void loop() {
  lcd.setCursor(0, 1);
  lcd.print(millis() / 1000);
  lcd.print("s");
  delay(100);
}''',
                        'components': json.dumps(['Arduino Uno', 'LCD1602显示屏', '电位器', '面包板', '杜邦线'], ensure_ascii=False)
                    },
                    {
                        'title': '超声波测距',
                        'description': '学习使用HC-SR04超声波传感器',
                        'category': '传感器',
                        'difficulty': 'intermediate',
                        'duration': 30,
                        'order_num': 9,
                        'content': '''
# 超声波测距

## 学习目标
- 了解超声波测距原理
- 学会使用HC-SR04传感器
- 实现距离测量和显示
                        ''',
                        'code_example': '''const int trigPin = 9;
const int echoPin = 10;

void setup() {
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  long duration = pulseIn(echoPin, HIGH);
  int distance = duration * 0.034 / 2;
  
  Serial.print("距离: ");
  Serial.print(distance);
  Serial.println("cm");
  
  delay(500);
}''',
                        'components': json.dumps(['Arduino Uno', 'HC-SR04超声波传感器', '面包板', '杜邦线'], ensure_ascii=False)
                    },
                    {
                        'title': 'WS2812 LED灯带',
                        'description': '学习控制WS2812可编程LED灯带',
                        'category': '进阶',
                        'difficulty': 'advanced',
                        'duration': 40,
                        'order_num': 10,
                        'content': '''
# WS2812 LED灯带

## 学习目标
- 了解WS2812的工作原理
- 学会使用Adafruit_NeoPixel库
- 实现各种灯光效果
                        ''',
                        'code_example': '''#include <Adafruit_NeoPixel.h>

#define PIN 6
#define NUMPIXELS 16

Adafruit_NeoPixel pixels(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  pixels.begin();
}

void loop() {
  for(int i=0; i<NUMPIXELS; i++) {
    pixels.setPixelColor(i, pixels.Color(0, 150, 0));
    pixels.show();
    delay(100);
  }
  for(int i=0; i<NUMPIXELS; i++) {
    pixels.setPixelColor(i, pixels.Color(0, 0, 0));
    pixels.show();
    delay(100);
  }
}''',
                        'components': json.dumps(['Arduino Uno', 'WS2812 LED灯带', '面包板', '杜邦线'], ensure_ascii=False)
                    }
                ]
                
                now = time.time()
                for i, t in enumerate(tutorials):
                    cursor.execute('''
                        INSERT INTO arduino_tutorials 
                        (title, description, category, difficulty, content, code_example, 
                         components, duration, order_num, is_published, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    ''', (
                        t['title'], t['description'], t['category'], t['difficulty'],
                        t['content'], t['code_example'], t['components'],
                        t['duration'], t['order_num'], now
                    ))
                
                conn.commit()
                logger.info(f"已初始化 {len(tutorials)} 个Arduino教程")
        except Exception as e:
            logger.error(f"初始化教程失败: {e}")
    
    def _init_ai_prompts(self):
        """初始化AI提示词"""
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) as count FROM arduino_ai_prompts")
                if cursor.fetchone()['count'] > 0:
                    return
                
                prompts = [
                    {
                        'category': 'code_generation',
                        'prompt_key': 'basic_blink',
                        'prompt_template': '生成一个Arduino {board} 的{feature}代码，要求：\n- 使用{language}编程语言\n- 包含详细注释\n- 遵循Arduino编程规范\n- 功能：{description}',
                        'description': '基础代码生成模板'
                    },
                    {
                        'category': 'code_explanation',
                        'prompt_key': 'explain_code',
                        'prompt_template': '请详细解释以下Arduino代码的工作原理：\n\n```cpp\n{code}\n```\n\n请从以下几个方面解释：\n1. 整体功能概述\n2. setup()函数的作用\n3. loop()函数的逻辑\n4. 关键函数和变量说明\n5. 可能的改进建议',
                        'description': '代码解释模板'
                    },
                    {
                        'category': 'code_optimization',
                        'prompt_key': 'optimize_code',
                        'prompt_template': '请优化以下Arduino代码：\n\n```cpp\n{code}\n```\n\n优化目标：\n- 提高代码效率\n- 减少内存占用\n- 增强代码可读性\n- 添加错误处理',
                        'description': '代码优化模板'
                    },
                    {
                        'category': 'debugging',
                        'prompt_key': 'debug_code',
                        'prompt_template': '请帮我调试以下Arduino代码，找出可能的问题：\n\n```cpp\n{code}\n```\n\n错误现象：{error_description}\n\n请分析：\n1. 可能的错误原因\n2. 修复方案\n3. 预防措施',
                        'description': '代码调试模板'
                    }
                ]
                
                now = time.time()
                for p in prompts:
                    cursor.execute('''
                        INSERT INTO arduino_ai_prompts 
                        (category, prompt_key, prompt_template, description, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (p['category'], p['prompt_key'], p['prompt_template'], p['description'], now))
                
                conn.commit()
                logger.info(f"已初始化 {len(prompts)} 个AI提示词模板")
        except Exception as e:
            logger.error(f"初始化AI提示词失败: {e}")
    
    def generate_code(self, description: str, board: str = 'uno', 
                      feature: str = '自定义功能', language: str = 'C++') -> Dict:
        """AI生成Arduino代码
        
        Args:
            description: 功能描述
            board: 板型
            feature: 功能类型
            language: 编程语言
            
        Returns:
            Dict: 生成的代码
        """
        code_templates = {
            'LED闪烁': '''// {description}
// 板型: {board}
// 生成时间: {time}

const int ledPin = LED_BUILTIN;

void setup() {{
  // 初始化串口通信
  Serial.begin(9600);
  Serial.println("程序启动");
  
  // 设置LED引脚为输出模式
  pinMode(ledPin, OUTPUT);
}}

void loop() {{
  // 点亮LED
  digitalWrite(ledPin, HIGH);
  Serial.println("LED ON");
  delay(1000);
  
  // 熄灭LED
  digitalWrite(ledPin, LOW);
  Serial.println("LED OFF");
  delay(1000);
}}''',
            '传感器读取': '''// {description}
// 板型: {board}
// 生成时间: {time}

const int sensorPin = A0;

void setup() {{
  Serial.begin(9600);
  Serial.println("传感器读取程序启动");
}}

void loop() {{
  // 读取模拟传感器值
  int sensorValue = analogRead(sensorPin);
  
  // 转换为电压 (0-5V)
  float voltage = sensorValue * (5.0 / 1023.0);
  
  // 输出到串口
  Serial.print("原始值: ");
  Serial.print(sensorValue);
  Serial.print(" | 电压: ");
  Serial.print(voltage);
  Serial.println("V");
  
  delay(500);
}}''',
            '电机控制': '''// {description}
// 板型: {board}
// 生成时间: {time}

const int motorPin1 = 9;
const int motorPin2 = 10;
const int enablePin = 11;

void setup() {{
  Serial.begin(9600);
  Serial.println("电机控制程序启动");
  
  pinMode(motorPin1, OUTPUT);
  pinMode(motorPin2, OUTPUT);
  pinMode(enablePin, OUTPUT);
}}

void loop() {{
  // 正转
  digitalWrite(motorPin1, HIGH);
  digitalWrite(motorPin2, LOW);
  analogWrite(enablePin, 200);
  Serial.println("电机正转");
  delay(2000);
  
  // 停止
  digitalWrite(motorPin1, LOW);
  digitalWrite(motorPin2, LOW);
  Serial.println("电机停止");
  delay(1000);
  
  // 反转
  digitalWrite(motorPin1, LOW);
  digitalWrite(motorPin2, HIGH);
  analogWrite(enablePin, 150);
  Serial.println("电机反转");
  delay(2000);
  
  // 停止
  digitalWrite(motorPin1, LOW);
  digitalWrite(motorPin2, LOW);
  Serial.println("电机停止");
  delay(1000);
}}''',
            '自定义功能': '''// {description}
// 板型: {board}
// 生成时间: {time}

void setup() {{
  // 初始化代码
  Serial.begin(9600);
  Serial.println("程序启动");
  
  // TODO: 添加你的初始化代码
}}

void loop() {{
  // 主循环代码
  
  // TODO: 添加你的主循环代码
  
  delay(100);
}}'''
        }
        
        template = code_templates.get(feature, code_templates['自定义功能'])
        generated_code = template.format(
            description=description,
            board=board,
            time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        return {
            'success': True,
            'code': generated_code,
            'description': description,
            'board': board,
            'feature': feature,
            'language': language,
            'estimated_size': len(generated_code),
            'complexity': '简单' if feature in ['LED闪烁', '传感器读取'] else '中等'
        }
    
    def explain_code(self, code: str) -> Dict:
        """解释代码
        
        Args:
            code: 代码内容
            
        Returns:
            Dict: 代码解释
        """
        explanations = []
        
        if 'setup()' in code:
            explanations.append({
                'section': 'setup()函数',
                'description': 'setup()函数在Arduino启动时只运行一次，用于初始化设置。'
            })
        
        if 'loop()' in code:
            explanations.append({
                'section': 'loop()函数',
                'description': 'loop()函数会不断重复运行，是程序的主循环。'
            })
        
        if 'pinMode' in code:
            explanations.append({
                'section': 'pinMode()',
                'description': '设置引脚模式，INPUT为输入模式，OUTPUT为输出模式。'
            })
        
        if 'digitalWrite' in code:
            explanations.append({
                'section': 'digitalWrite()',
                'description': '设置数字引脚的输出电平，HIGH为高电平，LOW为低电平。'
            })
        
        if 'analogRead' in code:
            explanations.append({
                'section': 'analogRead()',
                'description': '读取模拟引脚的电压值，返回值范围0-1023（对应0-5V）。'
            })
        
        if 'analogWrite' in code:
            explanations.append({
                'section': 'analogWrite()',
                'description': '使用PWM（脉冲宽度调制）输出模拟信号，范围0-255。'
            })
        
        if 'Serial.begin' in code:
            explanations.append({
                'section': 'Serial.begin()',
                'description': '初始化串口通信，参数为波特率（如9600）。'
            })
        
        if 'delay' in code:
            explanations.append({
                'section': 'delay()',
                'description': '延时函数，参数单位为毫秒（ms）。'
            })
        
        if 'Serial.println' in code:
            explanations.append({
                'section': 'Serial.println()',
                'description': '通过串口输出一行数据，会自动换行。'
            })
        
        line_count = len(code.split('\n'))
        
        return {
            'success': True,
            'explanations': explanations,
            'stats': {
                'line_count': line_count,
                'has_setup': 'setup()' in code,
                'has_loop': 'loop()' in code,
                'functions_found': len(explanations)
            },
            'summary': f'该代码共 {line_count} 行，包含 {len(explanations)} 个关键函数/概念。'
        }
    
    def get_tutorials(self, category: str = None, difficulty: str = None,
                      page: int = 1, page_size: int = 20) -> Dict:
        """获取教程列表
        
        Args:
            category: 分类筛选
            difficulty: 难度筛选
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict: 教程列表
        """
        try:
            offset = (page - 1) * page_size
            
            query = "FROM arduino_tutorials WHERE is_published = 1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            if difficulty:
                query += " AND difficulty = ?"
                params.append(difficulty)
            
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"SELECT COUNT(*) as total {query}", params)
                total = cursor.fetchone()['total']
                
                cursor.execute(
                    f"SELECT id, title, description, category, difficulty, duration, order_num {query} ORDER BY order_num ASC LIMIT ? OFFSET ?",
                    params + [page_size, offset]
                )
                
                tutorials = [dict(row) for row in cursor.fetchall()]
            
            return {
                'success': True,
                'tutorials': tutorials,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        except Exception as e:
            logger.error(f"获取教程列表失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_tutorial_detail(self, tutorial_id: int) -> Dict:
        """获取教程详情
        
        Args:
            tutorial_id: 教程ID
            
        Returns:
            Dict: 教程详情
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM arduino_tutorials WHERE id = ? AND is_published = 1
                ''', (tutorial_id,))
                
                tutorial = cursor.fetchone()
                if not tutorial:
                    return {'success': False, 'error': '教程不存在'}
                
                tutorial_dict = dict(tutorial)
                if tutorial_dict.get('components'):
                    try:
                        tutorial_dict['components'] = json.loads(tutorial_dict['components'])
                    except:
                        pass
                
                cursor.execute('''
                    SELECT id, title FROM arduino_tutorials 
                    WHERE is_published = 1 AND order_num > ?
                    ORDER BY order_num ASC LIMIT 1
                ''', (tutorial_dict['order_num'],))
                next_tutorial = cursor.fetchone()
                if next_tutorial:
                    tutorial_dict['next_tutorial'] = dict(next_tutorial)
                
                cursor.execute('''
                    SELECT id, title FROM arduino_tutorials 
                    WHERE is_published = 1 AND order_num < ?
                    ORDER BY order_num DESC LIMIT 1
                ''', (tutorial_dict['order_num'],))
                prev_tutorial = cursor.fetchone()
                if prev_tutorial:
                    tutorial_dict['prev_tutorial'] = dict(prev_tutorial)
            
            return {'success': True, 'tutorial': tutorial_dict}
        except Exception as e:
            logger.error(f"获取教程详情失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_project(self, user_id: int, project_name: str, code: str,
                     board_type: str = 'uno', description: str = '',
                     circuit_data: str = None, tags: List[str] = None,
                     project_id: int = None) -> Dict:
        """保存项目
        
        Args:
            user_id: 用户ID
            project_name: 项目名称
            code: 代码
            board_type: 板型
            description: 描述
            circuit_data: 电路数据
            tags: 标签列表
            project_id: 项目ID（更新时使用）
            
        Returns:
            Dict: 结果
        """
        try:
            now = time.time()
            tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
            
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                if project_id:
                    cursor.execute('''
                        UPDATE arduino_projects 
                        SET project_name = ?, code = ?, board_type = ?, 
                            description = ?, circuit_data = ?, tags = ?, updated_at = ?
                        WHERE id = ? AND user_id = ?
                    ''', (
                        project_name, code, board_type, description, 
                        circuit_data, tags_json, now, project_id, user_id
                    ))
                    result_id = project_id
                    message = '项目已更新'
                else:
                    cursor.execute('''
                        INSERT INTO arduino_projects 
                        (user_id, project_name, description, board_type, code, 
                         circuit_data, tags, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id, project_name, description, board_type, code,
                        circuit_data, tags_json, now, now
                    ))
                    result_id = cursor.lastrowid
                    message = '项目已保存'
                
                conn.commit()
            
            return {
                'success': True,
                'project_id': result_id,
                'message': message
            }
        except Exception as e:
            logger.error(f"保存项目失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_projects(self, user_id: int, page: int = 1, 
                          page_size: int = 20) -> Dict:
        """获取用户的项目列表
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict: 项目列表
        """
        try:
            offset = (page - 1) * page_size
            
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) as total FROM arduino_projects 
                    WHERE user_id = ?
                ''', (user_id,))
                total = cursor.fetchone()['total']
                
                cursor.execute('''
                    SELECT id, project_name, description, board_type, 
                           star_count, fork_count, updated_at
                    FROM arduino_projects 
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                ''', (user_id, page_size, offset))
                
                projects = [dict(row) for row in cursor.fetchall()]
                
                for p in projects:
                    if p.get('tags'):
                        try:
                            p['tags'] = json.loads(p['tags'])
                        except:
                            pass
            
            return {
                'success': True,
                'projects': projects,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        except Exception as e:
            logger.error(f"获取项目列表失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_project_detail(self, project_id: int) -> Dict:
        """获取项目详情
        
        Args:
            project_id: 项目ID
            
        Returns:
            Dict: 项目详情
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM arduino_projects WHERE id = ?
                ''', (project_id,))
                
                project = cursor.fetchone()
                if not project:
                    return {'success': False, 'error': '项目不存在'}
                
                project_dict = dict(project)
                if project_dict.get('tags'):
                    try:
                        project_dict['tags'] = json.loads(project_dict['tags'])
                    except:
                        pass
            
            return {'success': True, 'project': project_dict}
        except Exception as e:
            logger.error(f"获取项目详情失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_project(self, user_id: int, project_id: int) -> Dict:
        """删除项目
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            
        Returns:
            Dict: 结果
        """
        try:
            with self._get_db() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM arduino_projects 
                    WHERE id = ? AND user_id = ?
                ''', (project_id, user_id))
                
                if cursor.rowcount == 0:
                    return {'success': False, 'error': '项目不存在或无权删除'}
                
                conn.commit()
            
            return {'success': True, 'message': '项目已删除'}
        except Exception as e:
            logger.error(f"删除项目失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_component_library(self) -> Dict:
        """获取元件库
        
        Returns:
            Dict: 元件库
        """
        components = {
            'basic': [
                {'id': 'resistor', 'name': '电阻', 'icon': '🔴', 'category': '基础'},
                {'id': 'capacitor', 'name': '电容', 'icon': '⚪', 'category': '基础'},
                {'id': 'led_red', 'name': '红色LED', 'icon': '🟥', 'category': '显示'},
                {'id': 'led_green', 'name': '绿色LED', 'icon': '🟩', 'category': '显示'},
                {'id': 'led_blue', 'name': '蓝色LED', 'icon': '🟦', 'category': '显示'},
                {'id': 'button', 'name': '按钮开关', 'icon': '🔘', 'category': '输入'},
                {'id': 'potentiometer', 'name': '电位器', 'icon': '🎚️', 'category': '输入'},
            ],
            'sensors': [
                {'id': 'ldr', 'name': '光敏电阻', 'icon': '☀️', 'category': '传感器'},
                {'id': 'thermistor', 'name': '热敏电阻', 'icon': '🌡️', 'category': '传感器'},
                {'id': 'dht11', 'name': 'DHT11温湿度', 'icon': '💧', 'category': '传感器'},
                {'id': 'dht22', 'name': 'DHT22温湿度', 'icon': '💧', 'category': '传感器'},
                {'id': 'ultrasonic', 'name': 'HC-SR04超声波', 'icon': '📡', 'category': '传感器'},
                {'id': 'pir', 'name': 'PIR人体红外', 'icon': '👤', 'category': '传感器'},
                {'id': 'mpu6050', 'name': 'MPU6050陀螺仪', 'icon': '🎯', 'category': '传感器'},
            ],
            'output': [
                {'id': 'buzzer', 'name': '蜂鸣器', 'icon': '🔔', 'category': '输出'},
                {'id': 'servo', 'name': '舵机', 'icon': '⚙️', 'category': '输出'},
                {'id': 'motor_dc', 'name': '直流电机', 'icon': '🔩', 'category': '输出'},
                {'id': 'relay', 'name': '继电器', 'icon': '⚡', 'category': '输出'},
                {'id': 'lcd1602', 'name': 'LCD1602显示屏', 'icon': '📺', 'category': '显示'},
                {'id': 'oled', 'name': 'OLED显示屏', 'icon': '📱', 'category': '显示'},
                {'id': 'ws2812', 'name': 'WS2812灯带', 'icon': '💡', 'category': '显示'},
            ],
            'communication': [
                {'id': 'hc05', 'name': 'HC-05蓝牙', 'icon': '📶', 'category': '通信'},
                {'id': 'nrf24l01', 'name': 'NRF24L01无线', 'icon': '📡', 'category': '通信'},
                {'id': 'esp8266', 'name': 'ESP8266 WiFi', 'icon': '🌐', 'category': '通信'},
                {'id': 'ir_receiver', 'name': '红外接收', 'icon': '📥', 'category': '通信'},
                {'id': 'ir_transmitter', 'name': '红外发射', 'icon': '📤', 'category': '通信'},
            ],
            'storage': [
                {'id': 'sd_card', 'name': 'SD卡模块', 'icon': '💾', 'category': '存储'},
                {'id': 'eeprom', 'name': 'EEPROM', 'icon': '📦', 'category': '存储'},
            ]
        }
        
        return {
            'success': True,
            'components': components,
            'total': sum(len(v) for v in components.values())
        }
    
    def get_circuit_templates(self) -> Dict:
        """获取电路模板
        
        Returns:
            Dict: 电路模板列表
        """
        templates = [
            {
                'id': 'led_blink',
                'name': 'LED闪烁',
                'difficulty': '入门',
                'components': ['LED灯', '220Ω电阻'],
                'description': '最基础的LED闪烁电路'
            },
            {
                'id': 'button_led',
                'name': '按钮控制LED',
                'difficulty': '入门',
                'components': ['LED灯', '按钮', '电阻'],
                'description': '通过按钮控制LED开关'
            },
            {
                'id': 'potentiometer_led',
                'name': '电位器调光',
                'difficulty': '基础',
                'components': ['LED灯', '电位器', '电阻'],
                'description': '用电位器调节LED亮度'
            },
            {
                'id': 'traffic_light',
                'name': '交通信号灯',
                'difficulty': '基础',
                'components': ['红LED', '黄LED', '绿LED', '电阻x3'],
                'description': '模拟交通信号灯'
            },
            {
                'id': 'lcd_display',
                'name': 'LCD显示',
                'difficulty': '中等',
                'components': ['LCD1602', '电位器', '电阻'],
                'description': '在LCD上显示文字'
            },
            {
                'id': 'dht11_lcd',
                'name': '温湿度显示',
                'difficulty': '中等',
                'components': ['DHT11', 'LCD1602', '电阻'],
                'description': '温湿度数据显示在LCD上'
            },
            {
                'id': 'ultrasonic_radar',
                'name': '超声波雷达',
                'difficulty': '进阶',
                'components': ['HC-SR04', '舵机', 'LCD'],
                'description': '可旋转的超声波测距雷达'
            }
        ]
        
        return {
            'success': True,
            'templates': templates,
            'total': len(templates)
        }


arduino_ai_enhanced_service = ArduinoAIEnhancedService()