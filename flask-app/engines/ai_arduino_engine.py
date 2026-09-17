#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Arduino编程自动同步引擎 (Arduino Programming Sync Engine)
================================================================
flow_id: flow_arduino_sync_20260819_001

功能:
  1. Arduino编程教学同步(基础语法→传感器→通信→项目实战)
  2. 代码模板/示例同步(LED/Buzzer/Servo/LCD/Ultrasonic/DHT等)
  3. 实验项目同步(连线图+代码+讲解)
  4. 通信协议同步(I2C/SPI/Serial/UART)
  5. 板卡支持同步(UNO/Mega/Nano/ESP32/ESP8266/Micro)
  6. 库管理同步(Wire/SPI/Servo/LiquidCrystal/DHT/EEPROM等)
  7. 永久化保存到数据库, 实时保持最新

集成现有系统:
  - 前端: /admin_app/arduino_ide (Arduino IDE页面)
  - API: /api/arduino/* (编译/仿真/上传/组件/库/板卡)
  - AI员工: arduino_ai_employees.py

CLI:
  python3 ai_arduino_engine.py sync    执行同步
  python3 ai_arduino_engine.py status  查看状态
  python3 ai_arduino_engine.py start   守护模式
"""
import json
import os
import signal
import sqlite3
import sys
import threading
import time
import uuid
from datetime import datetime
# [unused] from typing import Any, Dict, List, Optional
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_ENGINES_DIR = os.path.join(ROOT, "ai_engines")
APP_DB = os.path.join(AI_ENGINES_DIR, "app.db")
RUNTIME_DIR = os.path.join(ROOT, "..", "_runtime")
LOG_DIR = os.path.join(RUNTIME_DIR, "logs")
PID_DIR = os.path.join(RUNTIME_DIR, "pids")
PID_FILE = os.path.join(PID_DIR, "ai_arduino_engine.pid")
LOG_FILE = os.path.join(LOG_DIR, "ai_arduino_engine.log")

for _d in [LOG_DIR, PID_DIR]:
    os.makedirs(_d, exist_ok=True)

_LOCK = threading.Lock()
SYNC_INTERVAL = 600


def _now() -> str:
    return datetime.now().isoformat()


def _log(msg: str):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{_now()}] {msg}\n")


# ============================================================
# 1. 建表
# ============================================================
def ensure_arduino_tables():
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        c = conn.cursor()

        # Arduino教程内容表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_tutorials (
            tutorial_id    TEXT PRIMARY KEY,
            category       TEXT NOT NULL,
            title          TEXT NOT NULL,
            difficulty     TEXT DEFAULT 'beginner',
            board_type     TEXT DEFAULT 'UNO',
            content_body   TEXT,
            code_example    TEXT,
            wiring_pins     TEXT,
            libraries_req   TEXT,
            knowledge_tags  TEXT,
            version        TEXT DEFAULT 'v1.0',
            status         TEXT DEFAULT 'ACTIVE',
            created_at     TEXT NOT NULL,
            updated_at     TEXT NOT NULL,
            CHECK(category IN ('basics','sensors','actuators','communication',
                               'display','project','iot','robotics'))
        )""")

        # Arduino组件库表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_components (
            component_id   TEXT PRIMARY KEY,
            component_name TEXT NOT NULL,
            category       TEXT NOT NULL,
            pin_type       TEXT,
            voltage        TEXT DEFAULT '5V',
            description    TEXT,
            code_template   TEXT,
            libraries_req  TEXT,
            difficulty     TEXT DEFAULT 'easy',
            version        TEXT DEFAULT 'v1.0',
            status         TEXT DEFAULT 'ACTIVE',
            created_at     TEXT NOT NULL,
            updated_at     TEXT NOT NULL,
            CHECK(category IN ('led','sensor','actuator','display',
                               'communication','power','prototyping'))
        )""")

        # Arduino实验项目表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_experiments (
            experiment_id  TEXT PRIMARY KEY,
            experiment_name TEXT NOT NULL,
            difficulty     TEXT DEFAULT 'medium',
            board_type     TEXT DEFAULT 'UNO',
            objective      TEXT,
            components_req  TEXT,
            wiring_json     TEXT,
            code_complete   TEXT,
            explanation     TEXT,
            safety_notes    TEXT,
            version        TEXT DEFAULT 'v1.0',
            status         TEXT DEFAULT 'ACTIVE',
            created_at     TEXT NOT NULL,
            updated_at     TEXT NOT NULL
        )""")

        # Arduino板卡表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_boards (
            board_id       TEXT PRIMARY KEY,
            board_name     TEXT NOT NULL,
            manufacturer   TEXT,
            cpu            TEXT,
            clock_speed    TEXT,
            flash_memory   TEXT,
            digital_pins   TEXT,
            analog_pins    TEXT,
            pwm_pins       TEXT,
            communication  TEXT,
            features       TEXT,
            version        TEXT DEFAULT 'v1.0',
            status         TEXT DEFAULT 'ACTIVE',
            created_at     TEXT NOT NULL,
            updated_at     TEXT NOT NULL
        )""")

        # 同步日志表
        c.execute("""
        CREATE TABLE IF NOT EXISTS mt_arduino_sync_log (
            sync_id        TEXT PRIMARY KEY,
            items_synced   INTEGER DEFAULT 0,
            items_new      INTEGER DEFAULT 0,
            items_updated  INTEGER DEFAULT 0,
            details_json   TEXT,
            sync_status    TEXT DEFAULT 'SUCCESS',
            synced_at      TEXT NOT NULL
        )""")

        conn.commit()
        conn.close()


# ============================================================
# 2. 知识库数据
# ============================================================

TUTORIALS = [
    # 基础语法
    {"cat": "basics", "title": "Arduino基础语法: setup()与loop()",
     "diff": "beginner", "board": "UNO",
     "body": "每个Arduino程序(Sketch)必须包含setup()和loop()两个函数。setup()在通电或重启时执行一次,用于初始化。loop()在setup()之后反复执行,是主循环。",
     "code": "void setup() {\n  pinMode(13, OUTPUT);\n}\nvoid loop() {\n  digitalWrite(13, HIGH);\n  delay(1000);\n  digitalWrite(13, LOW);\n  delay(1000);\n}",
     "pins": "D13", "libs": "", "tags": "setup,loop,pinMode,digitalWrite,delay"},
    {"cat": "basics", "title": "变量与数据类型",
     "diff": "beginner", "board": "UNO",
     "body": "Arduino支持int(2字节),float(4字节),char(1字节),boolean(1字节),String,数组。const定义常量,#define宏定义。注意UNO的int为16位有符号(-32768~32767)。",
     "code": "int ledPin = 13;\nconst int buttonPin = 2;\nfloat temperature = 0.0;\nboolean isOn = false;\nchar buf[32];",
     "pins": "", "libs": "", "tags": "int,float,char,boolean,数组,const"},
    {"cat": "basics", "title": "digitalRead/digitalWrite数字IO",
     "diff": "beginner", "board": "UNO",
     "body": "digitalWrite(pin, HIGH/LOW)输出数字信号。digitalRead(pin)读取数字输入(需先用pinMode(pin, INPUT)或INPUT_PULLUP)。HIGH=5V,LOW=0V。",
     "code": "void setup() {\n  pinMode(2, INPUT_PULLUP);\n  pinMode(13, OUTPUT);\n}\nvoid loop() {\n  int btn = digitalRead(2);\n  if (btn == LOW) {\n    digitalWrite(13, HIGH);\n  } else {\n    digitalWrite(13, LOW);\n  }\n}",
     "pins": "D2,D13", "libs": "", "tags": "digitalRead,digitalWrite,INPUT_PULLUP,按钮"},
    {"cat": "basics", "title": "analogRead/analogWrite模拟IO与PWM",
     "diff": "beginner", "board": "UNO",
     "body": "analogRead(A0)读取0-1023(0-5V)。analogWrite(pin, 0-255)输出PWM波(0=0%,255=100%)。PWM引脚: 3,5,6,9,10,11(UNO)。用于LED调光/电机调速。",
     "code": "void setup() { pinMode(9, OUTPUT); }\nvoid loop() {\n  int val = analogRead(A0);\n  int pwm = map(val, 0, 1023, 0, 255);\n  analogWrite(9, pwm);\n}",
     "pins": "A0,D9", "libs": "", "tags": "analogRead,analogWrite,PWM,map,调光"},

    # 传感器
    {"cat": "sensors", "title": "DHT11/DHT22温湿度传感器",
     "diff": "medium", "board": "UNO",
     "body": "DHT11: 温度0-50°C(±2°C), 湿度20-90%(±5%)。DHT22: 温度-40~80°C(±0.5°C),湿度0-100%(±2%)。单总线数字接口,需4.7K上拉电阻。使用DHT库读取。",
     "code": "#include <DHT.h>\n#define DHTPIN 2\n#define DHTTYPE DHT11\nDHT dht(DHTPIN, DHTTYPE);\nvoid setup() {\n  Serial.begin(9600);\n  dht.begin();\n}\nvoid loop() {\n  float h = dht.readHumidity();\n  float t = dht.readTemperature();\n  Serial.print(\"Humidity: \"); Serial.print(h);\n  Serial.print(\"%  Temp: \"); Serial.print(t); Serial.println(\"C\");\n  delay(2000);\n}",
     "pins": "D2", "libs": "DHT.h", "tags": "DHT11,DHT22,温度,湿度,单总线"},
    {"cat": "sensors", "title": "HC-SR04超声波测距传感器",
     "diff": "medium", "board": "UNO",
     "body": "测量范围2cm-400cm,精度3mm。工作原理: TRIG发10us高电平→模块发8个40kHz脉冲→ECHO输出高电平,持续时间=超声波往返时间。距离=duration*0.034/2(cm)。",
     "code": "#define TRIG 9\n#define ECHO 10\nvoid setup() {\n  Serial.begin(9600);\n  pinMode(TRIG, OUTPUT);\n  pinMode(ECHO, INPUT);\n}\nvoid loop() {\n  digitalWrite(TRIG, LOW); delayMicroseconds(2);\n  digitalWrite(TRIG, HIGH); delayMicroseconds(10);\n  digitalWrite(TRIG, LOW);\n  long dur = pulseIn(ECHO, HIGH);\n  float dist = dur * 0.034 / 2;\n  Serial.print(\"Distance: \"); Serial.print(dist); Serial.println(\" cm\");\n  delay(100);\n}",
     "pins": "D9(TRIG),D10(ECHO)", "libs": "", "tags": "超声波,HC-SR04,测距,pulseIn"},
    {"cat": "sensors", "title": "光敏电阻(LDR)光线检测",
     "diff": "beginner", "board": "UNO",
     "body": "光敏电阻阻值随光照变化(亮→阻值小)。搭配10K电阻分压,接A0读取模拟值。值大=暗,值小=亮。可用于自动路灯/智能窗帘。",
     "code": "void setup() { Serial.begin(9600); }\nvoid loop() {\n  int light = analogRead(A0);\n  if (light < 500) {\n    Serial.println(\"Bright\");\n  } else {\n    Serial.println(\"Dark\");\n  }\n  delay(500);\n}",
     "pins": "A0", "libs": "", "tags": "光敏,LDR,分压,analogRead"},
    {"cat": "sensors", "title": "PIR人体红外感应传感器",
     "diff": "medium", "board": "UNO",
     "body": "检测人体红外辐射,检测距离7m,角度120°。输出高电平=检测到运动,低电平=无运动。有调节灵敏度(距离)和延时时间的电位器。常用于安防报警。",
     "code": "#define PIR 2\n#define LED 13\nvoid setup() {\n  pinMode(PIR, INPUT);\n  pinMode(LED, OUTPUT);\n  Serial.begin(9600);\n}\nvoid loop() {\n  int val = digitalRead(PIR);\n  if (val == HIGH) {\n    digitalWrite(LED, HIGH);\n    Serial.println(\"Motion detected!\");\n  } else {\n    digitalWrite(LED, LOW);\n  }\n}",
     "pins": "D2,D13", "libs": "", "tags": "PIR,红外,人体感应,安防"},
    {"cat": "sensors", "title": "MQ-2烟雾/可燃气体传感器",
     "diff": "medium", "board": "UNO",
     "body": "检测LPG/丙烷/氢气/甲烷等可燃气体。模拟输出(A0)和数字输出(D0,阈值可调)。加热后需预热2分钟稳定。用于火灾/燃气泄漏报警。",
     "code": "void setup() { Serial.begin(9600); }\nvoid loop() {\n  int gas = analogRead(A0);\n  if (gas > 400) {\n    Serial.println(\"Gas detected!\");\n  }\n  delay(1000);\n}",
     "pins": "A0", "libs": "", "tags": "MQ-2,烟雾,可燃气体,报警"},

    # 执行器
    {"cat": "actuators", "title": "SG90舵机控制",
     "diff": "medium", "board": "UNO",
     "body": "SG90: 0-180°,脉宽500-2500us。控制信号为PWM(50Hz),占空比决定角度。使用Servo库的write(degrees)。0°=500us,90°=1500us,180°=2500us。",
     "code": "#include <Servo.h>\nServo myservo;\nvoid setup() {\n  myservo.attach(9);\n}\nvoid loop() {\n  for (int pos = 0; pos <= 180; pos++) {\n    myservo.write(pos);\n    delay(15);\n  }\n  for (int pos = 180; pos >= 0; pos--) {\n    myservo.write(pos);\n    delay(15);\n  }\n}",
     "pins": "D9", "libs": "Servo.h", "tags": "舵机,SG90,PWM,角度控制,Servo"},
    {"cat": "actuators", "title": "L298N直流电机驱动",
     "diff": "medium", "board": "UNO",
     "body": "L298N双H桥电机驱动,可驱动2个直流电机或1个步进电机。IN1/IN2控制方向,ENA控制速度(PWM)。IN1=HIGH,IN2=LOW=正转;反之反转。ENA=0~255调速。",
     "code": "#define ENA 5\n#define IN1 6\n#define IN2 7\nvoid setup() {\n  pinMode(ENA, OUTPUT);\n  pinMode(IN1, OUTPUT);\n  pinMode(IN2, OUTPUT);\n}\nvoid loop() {\n  digitalWrite(IN1, HIGH);\n  digitalWrite(IN2, LOW);\n  analogWrite(ENA, 200);\n  delay(2000);\n  analogWrite(ENA, 0);\n  delay(1000);\n  digitalWrite(IN1, LOW);\n  digitalWrite(IN2, HIGH);\n  analogWrite(ENA, 150);\n  delay(2000);\n}",
     "pins": "D5,D6,D7", "libs": "", "tags": "L298N,电机,H桥,调速,方向"},

    # 显示
    {"cat": "display", "title": "LCD1602 I2C液晶显示",
     "diff": "medium", "board": "UNO",
     "body": "1602=16列×2行字符显示。I2C接口(SDA=A4,SCL=A5),地址通常0x27或0x3F。使用LiquidCrystal_I2C库。背光可调。",
     "code": "#include <Wire.h>\n#include <LiquidCrystal_I2C.h>\nLiquidCrystal_I2C lcd(0x27, 16, 2);\nvoid setup() {\n  lcd.init();\n  lcd.backlight();\n  lcd.setCursor(0, 0);\n  lcd.print(\"Hello, Arduino!\");\n  lcd.setCursor(0, 1);\n  lcd.print(\"MTSCOS AI\");\n}\nvoid loop() {\n}",
     "pins": "A4(SDA),A5(SCL)", "libs": "Wire.h,LiquidCrystal_I2C.h", "tags": "LCD1602,I2C,液晶,LiquidCrystal"},
    {"cat": "display", "title": "OLED 0.96寸 SSD1306显示",
     "diff": "medium", "board": "UNO",
     "body": "128×64像素,SSD1306驱动芯片,I2C接口。可显示文字/图形/位图。使用Adafruit_SSD1306+Adafruit_GFX库。适合做小型仪表盘。",
     "code": "#include <Wire.h>\n#include <Adafruit_GFX.h>\n#include <Adafruit_SSD1306.h>\n#define SCREEN_W 128\n#define SCREEN_H 64\nAdafruit_SSD1306 display(SCREEN_W, SCREEN_H, &Wire, -1);\nvoid setup() {\n  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);\n  display.clearDisplay();\n  display.setTextSize(1);\n  display.setTextColor(WHITE);\n  display.setCursor(0, 0);\n  display.println(\"Hello OLED!\");\n  display.display();\n}\nvoid loop() {\n}",
     "pins": "A4(SDA),A5(SCL)", "libs": "Wire.h,Adafruit_GFX.h,Adafruit_SSD1306.h", "tags": "OLED,SSD1306,I2C,图形显示"},

    # 通信
    {"cat": "communication", "title": "Serial串口通信基础",
     "diff": "beginner", "board": "UNO",
     "body": "Serial.begin(9600)初始化串口。Serial.print/println发送数据。Serial.available()检查缓冲区。Serial.readString()读取字符串。波特率常用9600/115200。",
     "code": "void setup() {\n  Serial.begin(9600);\n  Serial.println(\"Enter command:\");\n}\nvoid loop() {\n  if (Serial.available() > 0) {\n    String cmd = Serial.readStringUntil('\\n');\n    cmd.trim();\n    if (cmd == \"on\") {\n      digitalWrite(13, HIGH);\n      Serial.println(\"LED ON\");\n    } else if (cmd == \"off\") {\n      digitalWrite(13, LOW);\n      Serial.println(\"LED OFF\");\n    }\n  }\n}",
     "pins": "D13", "libs": "", "tags": "Serial,串口,通信,readStringUntil"},
    {"cat": "communication", "title": "I2C总线通信(Wire库)",
     "diff": "medium", "board": "UNO",
     "body": "I2C: 两线通信(SDA数据+SCL时钟)。支持多设备(地址区分)。UNO: SDA=A4,SCL=A5。Master发地址+数据,Slave响应。常用于连接传感器/LCD/EEPROM。",
     "code": "#include <Wire.h>\nvoid setup() {\n  Wire.begin();\n  Serial.begin(9600);\n}\nvoid loop() {\n  Wire.beginTransmission(0x27);\n  Wire.write(0x00);\n  Wire.endTransmission();\n  Wire.requestFrom(0x27, 1);\n  if (Wire.available()) {\n    int val = Wire.read();\n    Serial.println(val);\n  }\n  delay(500);\n}",
     "pins": "A4(SDA),A5(SCL)", "libs": "Wire.h", "tags": "I2C,Wire,SDA,SCL,总线"},
    {"cat": "communication", "title": "HC-05蓝牙模块通信",
     "diff": "medium", "board": "UNO",
     "body": "HC-05蓝牙串口模块。TX→RX,RX→TX(交叉连接)。AT模式设置名称/密码/波特率。默认9600。手机蓝牙串口APP可远程控制Arduino。",
     "code": "#include <SoftwareSerial.h>\nSoftwareSerial BT(2, 3);\nvoid setup() {\n  Serial.begin(9600);\n  BT.begin(9600);\n  pinMode(13, OUTPUT);\n}\nvoid loop() {\n  if (BT.available()) {\n    char c = BT.read();\n    if (c == '1') digitalWrite(13, HIGH);\n    if (c == '0') digitalWrite(13, LOW);\n    Serial.println(c);\n  }\n  if (Serial.available()) {\n    BT.write(Serial.read());\n  }\n}",
     "pins": "D2(RX),D3(TX),D13", "libs": "SoftwareSerial.h", "tags": "蓝牙,HC-05,SoftwareSerial,无线"},

    # IoT
    {"cat": "iot", "title": "ESP8266 WiFi物联网接入",
     "diff": "hard", "board": "ESP8266",
     "body": "ESP8266自带WiFi,可作Web Server/Client。连接路由器→HTTP请求→上传数据到云平台(ThingSpeak/Blynk/自建服务器)。实现远程监控/控制。",
     "code": "#include <ESP8266WiFi.h>\n#include <ESP8266HTTPClient.h>\nconst char* ssid = \"YourSSID\";\nconst char* password = \"YourPassword\";\nvoid setup() {\n  Serial.begin(115200);\n  WiFi.begin(ssid, password);\n  while (WiFi.status() != WL_CONNECTED) {\n    delay(500); Serial.print(\".\");\n  }\n  Serial.println(\"\");\n  Serial.print(\"IP: \"); Serial.println(WiFi.localIP());\n}\nvoid loop() {\n  HTTPClient http;\n  http.begin(\"http://api.example.com/data?key=xxx&field1=25\");\n  int code = http.GET();\n  if (code > 0) {\n    String payload = http.getString();\n    Serial.println(payload);\n  }\n  http.end();\n  delay(60000);\n}",
     "pins": "", "libs": "ESP8266WiFi.h,ESP8266HTTPClient.h", "tags": "ESP8266,WiFi,IoT,HTTP,物联网"},
    {"cat": "iot", "title": "ESP32 BLE低功耗蓝牙",
     "diff": "hard", "board": "ESP32",
     "body": "ESP32支持BLE 4.2。可作BLE Server广播数据,或Client扫描连接。功耗远低于WiFi,适合穿戴/传感器网络。使用BLEDevice库。",
     "code": "#include <BLEDevice.h>\n#include <BLEServer.h>\n#include <BLEUtils.h>\n#include <BLE2902.h>\nBLEServer* pServer;\nBLECharacteristic* pChar;\nbool deviceConnected = false;\nvoid setup() {\n  BLEDevice::init(\"MTSCOS-BLE\");\n  pServer = BLEDevice::createServer();\n  BLEService *pService = pServer->createService(BLEUUID(\"0000180F-0000-1000-8000-00805F9B34FB\"));\n  pChar = pService->createCharacteristic(\n    BLEUUID(\"00002A19-0000-1000-8000-00805F9B34FB\"),\n    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);\n  pChar->addDescriptor(new BLE2902());\n  pService->start();\n  pServer->getAdvertising()->start();\n}\nvoid loop() {\n  if (deviceConnected) {\n    pChar->setValue(\"90%\");\n    pChar->notify();\n    delay(3000);\n  }\n}",
     "pins": "", "libs": "BLEDevice.h,BLEServer.h,BLEUtils.h,BLE2902.h", "tags": "ESP32,BLE,低功耗蓝牙,物联网"},

    # 项目实战
    {"cat": "project", "title": "智能温湿度监控系统",
     "diff": "medium", "board": "UNO",
     "body": "综合项目: DHT11采集温湿度→LCD1602显示→超阈值蜂鸣器报警→串口上传数据。涉及传感器+显示+执行器+串口通信4大模块。",
     "code": "#include <DHT.h>\n#include <Wire.h>\n#include <LiquidCrystal_I2C.h>\n#define DHTPIN 2\n#define DHTTYPE DHT11\n#define BUZZER 8\nDHT dht(DHTPIN, DHTTYPE);\nLiquidCrystal_I2C lcd(0x27, 16, 2);\nfloat tempMax = 35.0;\nvoid setup() {\n  Serial.begin(9600);\n  dht.begin();\n  lcd.init(); lcd.backlight();\n  pinMode(BUZZER, OUTPUT);\n}\nvoid loop() {\n  float h = dht.readHumidity();\n  float t = dht.readTemperature();\n  lcd.setCursor(0,0); lcd.print(\"T:\"); lcd.print(t); lcd.print(\"C\");\n  lcd.setCursor(0,1); lcd.print(\"H:\"); lcd.print(h); lcd.print(\"%\");\n  Serial.print(t); Serial.print(\",\"); Serial.println(h);\n  if (t > tempMax) {\n    tone(BUZZER, 1000);\n  } else {\n    noTone(BUZZER);\n  }\n  delay(2000);\n}",
     "pins": "D2(DHT),D8(BUZZER),A4(SDA),A5(SCL)", "libs": "DHT.h,Wire.h,LiquidCrystal_I2C.h", "tags": "综合项目,温湿度,监控,LCD,报警"},
]

COMPONENTS = [
    {"name": "LED红5mm", "cat": "led", "pin": "Digital", "volt": "5V",
     "desc": "发光二极管,需串联220Ω电阻。HIGH亮LOW灭。", "diff": "easy",
     "code": "pinMode(13, OUTPUT);\ndigitalWrite(13, HIGH);",
     "libs": ""},
    {"name": "有源蜂鸣器", "cat": "actuator", "pin": "Digital", "volt": "5V",
     "desc": "有源蜂鸣器直接给电即响。无源需PWM驱动可调音调。tone()/noTone()控制。", "diff": "easy",
     "code": "tone(8, 1000); delay(500);\nnoTone(8);",
     "libs": ""},
    {"name": "SG90舵机", "cat": "actuator", "pin": "PWM", "volt": "5V",
     "desc": "0-180°微型舵机,适合小型项目。需Servo库控制。", "diff": "medium",
     "code": "#include <Servo.h>\nServo s; s.attach(9);\ns.write(90);",
     "libs": "Servo.h"},
    {"name": "DHT11温湿度", "cat": "sensor", "pin": "Digital", "volt": "3.3-5V",
     "desc": "数字温湿度传感器,单总线协议。温度0-50°C,湿度20-90%。", "diff": "medium",
     "code": "#include <DHT.h>\nDHT dht(2, DHT11);\ndht.begin();\nfloat t = dht.readTemperature();",
     "libs": "DHT.h"},
    {"name": "HC-SR04超声波", "cat": "sensor", "pin": "Digital×2", "volt": "5V",
     "desc": "超声波测距2-400cm,TRIG触发ECHO接收。精度3mm。", "diff": "medium",
     "code": "digitalWrite(9, HIGH);\ndelayMicroseconds(10);\ndigitalWrite(9, LOW);\nlong d = pulseIn(10, HIGH);\nfloat cm = d * 0.034 / 2;",
     "libs": ""},
    {"name": "光敏电阻LDR", "cat": "sensor", "pin": "Analog", "volt": "5V",
     "desc": "阻值随光照变化,搭配10K电阻分压接A0。", "diff": "easy",
     "code": "int v = analogRead(A0);\nif (v < 500) { /* bright */ }",
     "libs": ""},
    {"name": "PIR人体红外", "cat": "sensor", "pin": "Digital", "volt": "5V",
     "desc": "检测人体红外,输出HIGH=有人。检测距离7m。", "diff": "medium",
     "code": "pinMode(2, INPUT);\nint v = digitalRead(2);\nif (v == HIGH) { /* motion */ }",
     "libs": ""},
    {"name": "MQ-2烟雾", "cat": "sensor", "pin": "Analog+Digital", "volt": "5V",
     "desc": "可燃气体检测,LPG/甲烷。预热2分钟。", "diff": "medium",
     "code": "int v = analogRead(A0);\nif (v > 400) { /* gas */ }",
     "libs": ""},
    {"name": "LCD1602 I2C", "cat": "display", "pin": "I2C", "volt": "5V",
     "desc": "16×2字符液晶,I2C接口地址0x27。", "diff": "medium",
     "code": "#include <LiquidCrystal_I2C.h>\nLiquidCrystal_I2C lcd(0x27,16,2);\nlcd.init(); lcd.backlight();\nlcd.print(\"Hello\");",
     "libs": "Wire.h,LiquidCrystal_I2C.h"},
    {"name": "OLED SSD1306", "cat": "display", "pin": "I2C", "volt": "3.3-5V",
     "desc": "128×64 OLED,I2C地址0x3C。支持图形/文字。", "diff": "medium",
     "code": "#include <Adafruit_SSD1306.h>\nAdafruit_SSD1306 d(128,64,&Wire,-1);\nd.begin(SSD1306_SWITCHCAPVCC,0x3C);\nd.println(\"Hi\"); d.display();",
     "libs": "Adafruit_GFX.h,Adafruit_SSD1306.h"},
    {"name": "L298N电机驱动", "cat": "actuator", "pin": "Digital+PWM", "volt": "5-12V",
     "desc": "双H桥,可驱动2个直流电机。IN1/IN2方向,ENA速度。", "diff": "medium",
     "code": "digitalWrite(IN1,HIGH);\ndigitalWrite(IN2,LOW);\nanalogWrite(ENA,200);",
     "libs": ""},
    {"name": "HC-05蓝牙", "cat": "communication", "pin": "Serial", "volt": "5V",
     "desc": "蓝牙串口模块,TX→RX,RX→TX交叉连接。", "diff": "medium",
     "code": "#include <SoftwareSerial.h>\nSoftwareSerial BT(2,3);\nBT.begin(9600);\nif (BT.available()) BT.read();",
     "libs": "SoftwareSerial.h"},
    {"name": "ESP8266 WiFi", "cat": "communication", "pin": "Serial/WiFi", "volt": "3.3V",
     "desc": "WiFi模块,可做Web Server或HTTP Client。", "diff": "hard",
     "code": "#include <ESP8266WiFi.h>\nWiFi.begin(ssid,pwd);\nHTTPClient http;\nhttp.begin(url); http.GET();",
     "libs": "ESP8266WiFi.h,ESP8266HTTPClient.h"},
    {"name": "DS1307 RTC", "cat": "sensor", "pin": "I2C", "volt": "5V",
     "desc": "实时时钟模块,掉电后纽扣电池维持走时。", "diff": "medium",
     "code": "#include <RTClib.h>\nRTC_DS1307 rtc;\nDateTime now = rtc.now();\nSerial.print(now.hour());",
     "libs": "RTClib.h"},
    {"name": "继电器5V", "cat": "actuator", "pin": "Digital", "volt": "5V",
     "desc": "5V继电器模块,控制高压设备(220V)。LOW触发(低电平有效)。", "diff": "easy",
     "code": "pinMode(7, OUTPUT);\ndigitalWrite(7, LOW); // ON\ndigitalWrite(7, HIGH); // OFF",
     "libs": ""},
]

EXPERIMENTS = [
    {"name": "LED呼吸灯(PWM调光)", "diff": "easy", "board": "UNO",
     "obj": "使用PWM实现LED从暗到亮再从亮到暗的呼吸效果",
     "comps": "LED红×1, 220Ω电阻×1, 面包板×1",
     "wiring": "{\"LED+\":\"D9(PWM)\",\"LED-\":\"GND via 220Ω\"}",
     "code": "void setup() { pinMode(9, OUTPUT); }\nvoid loop() {\n  for (int b = 0; b <= 255; b++) {\n    analogWrite(9, b); delay(10);\n  }\n  for (int b = 255; b >= 0; b--) {\n    analogWrite(9, b); delay(10);\n  }\n}",
     "exp": "analogWrite输出PWM波,占空比0-255对应0-100%亮度。呼吸效果通过渐增渐减实现。",
     "safety": "LED必须串联电阻限流,否则烧毁LED"},
    {"name": "超声波避障小车", "diff": "hard", "board": "UNO",
     "obj": "搭建自动避障小车: HC-SR04检测障碍→L298N控制电机→转向避障",
     "comps": "HC-SR04×1, L298N×1, 直流电机×2, 底盘, 电池盒",
     "wiring": "{\"TRIG\":\"D9\",\"ECHO\":\"D10\",\"ENA\":\"D5\",\"IN1\":\"D6\",\"IN2\":\"D7\",\"ENB\":\"D5\",\"IN3\":\"D8\",\"IN4\":\"D11\"}",
     "code": "#define TRIG 9\n#define ECHO 10\n#define ENA 5\n#define IN1 6\n#define IN2 7\nvoid setup() {\n  pinMode(TRIG,OUTPUT);\n  pinMode(ECHO,INPUT);\n  pinMode(ENA,OUTPUT);\n  pinMode(IN1,OUTPUT);\n  pinMode(IN2,OUTPUT);\n}\nfloat getDist() {\n  digitalWrite(TRIG,LOW);delayMicroseconds(2);\n  digitalWrite(TRIG,HIGH);delayMicroseconds(10);\n  digitalWrite(TRIG,LOW);\n  return pulseIn(ECHO,HIGH)*0.034/2;\n}\nvoid forward() {\n  digitalWrite(IN1,HIGH);\n  digitalWrite(IN2,LOW);\n  analogWrite(ENA,200);\n}\nvoid stop() {\n  analogWrite(ENA,0);\n}\nvoid loop() {\n  float d = getDist();\n  if (d < 20) { stop(); delay(500); }\n  else { forward(); }\n  delay(100);\n}",
     "exp": "超声波测距原理: 声波往返时间×声速/2。检测距离<20cm时停车避障,否则前进。",
     "safety": "电机电源和Arduino电源分开供电,避免电机启动时电压骤降导致重启"},
    {"name": "WiFi气象站(ESP8266)", "diff": "hard", "board": "ESP8266",
     "obj": "使用ESP8266+DHT11采集温湿度→WiFi上传到云平台→网页查看",
     "comps": "ESP8266×1, DHT11×1, 面包板, 跳线",
     "wiring": "{\"DHT_DATA\":\"D2\",\"VCC\":\"3.3V\"}",
     "code": "#include <ESP8266WiFi.h>\n#include <ESP8266HTTPClient.h>\n#include <DHT.h>\n#define DHTPIN 2\n#define DHTTYPE DHT11\nDHT dht(DHTPIN, DHTTYPE);\nconst char* ssid = \"YourSSID\";\nconst char* pwd = \"YourPassword\";\nvoid setup() {\n  Serial.begin(115200);\n  dht.begin();\n  WiFi.begin(ssid, pwd);\n  while (WiFi.status() != WL_CONNECTED) { delay(500); }\n  Serial.println(WiFi.localIP());\n}\nvoid loop() {\n  float t = dht.readTemperature();\n  float h = dht.readHumidity();\n  if (isnan(t) || isnan(h)) return;\n  HTTPClient http;\n  String url = \"http://api.thingspeak.com/update?api_key=XXX&field1=\" + String(t) + \"&field2=\" + String(h);\n  http.begin(url);\n  http.GET();\n  http.end();\n  delay(60000);\n}",
     "exp": "ESP8266连接WiFi后作为HTTP Client,将传感器数据通过GET请求上传到ThingSpeak云平台,实现远程实时监控。",
     "safety": "ESP8266供电必须3.3V,5V会烧毁。WiFi连接需等待稳定后再读取数据"},
]

BOARDS = [
    {"name": "Arduino UNO R3", "mfr": "Arduino", "cpu": "ATmega328P", "clk": "16MHz",
     "flash": "32KB", "d_pins": "14(6 PWM)", "a_pins": "6", "pwm": "6", "comm": "Serial, I2C, SPI",
     "feat": "最经典入门板,USB-B,DIP封装可换芯片"},
    {"name": "Arduino Mega 2560", "mfr": "Arduino", "cpu": "ATmega2560", "clk": "16MHz",
     "flash": "256KB", "d_pins": "54(15 PWM)", "a_pins": "16", "pwm": "15", "comm": "4×Serial, I2C, SPI",
     "feat": "多IO,4个硬件串口,适合复杂项目"},
    {"name": "Arduino Nano", "mfr": "Arduino", "cpu": "ATmega328P", "clk": "16MHz",
     "flash": "32KB", "d_pins": "14(6 PWM)", "a_pins": "8", "pwm": "6", "comm": "Serial, I2C, SPI",
     "feat": "Mini-USB,面包板友好,同UNO性能"},
    {"name": "Arduino Micro", "mfr": "Arduino", "cpu": "ATmega32U4", "clk": "16MHz",
     "flash": "32KB", "d_pins": "20(7 PWM)", "a_pins": "12", "pwm": "7", "comm": "USB HID, Serial, I2C, SPI",
     "feat": "内置USB,可作键盘/鼠标HID设备"},
    {"name": "ESP32 DevKit", "mfr": "Espressif", "cpu": "ESP32", "clk": "240MHz",
     "flash": "4MB", "d_pins": "34", "a_pins": "12", "pwm": "16", "comm": "WiFi, BLE, Serial, I2C, SPI",
     "feat": "双核240MHz,WiFi+BLE,4MB Flash,适合IoT"},
    {"name": "ESP8266 NodeMCU", "mfr": "Espressif", "cpu": "ESP8266", "clk": "80MHz",
     "flash": "4MB", "d_pins": "11", "a_pins": "1", "pwm": "10", "comm": "WiFi, Serial, I2C, SPI",
     "feat": "WiFi模块,Lua/Arduino IDE,适合IoT入门"},
    {"name": "Arduino Due", "mfr": "Arduino", "cpu": "AT91SAM3X8E", "clk": "84MHz",
     "flash": "512KB", "d_pins": "54(12 PWM)", "a_pins": "12", "pwm": "12", "comm": "2×USB, 4×Serial, I2C, SPI",
     "feat": "32位ARM,84MHz,3.3V IO(注意不兼容5V)"},
]


# ============================================================
# 3. 同步逻辑
# ============================================================
def _sync_tutorials(conn):
    r = {"synced": 0, "new": 0, "updated": 0}
    now = _now()
    for item in TUTORIALS:
        tid = "ARD-TUT-%s" % uuid.uuid4().hex[:10]
        existing = conn.execute(
            "SELECT tutorial_id FROM mt_arduino_tutorials WHERE title=?",
            (item["title"],)).fetchone()
        if existing:
            conn.execute("""UPDATE mt_arduino_tutorials SET
                category=?, difficulty=?, board_type=?, content_body=?,
                code_example=?, wiring_pins=?, libraries_req=?,
                knowledge_tags=?, updated_at=? WHERE tutorial_id=?""",
                (item["cat"], item["diff"], item["board"], item["body"],
                 item["code"], item["pins"], item["libs"],
                 item["tags"], now, existing[0]))
            r["updated"] += 1
        else:
            conn.execute("""INSERT INTO mt_arduino_tutorials
                (tutorial_id, category, title, difficulty, board_type,
                 content_body, code_example, wiring_pins, libraries_req,
                 knowledge_tags, version, status, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (tid, item["cat"], item["title"], item["diff"], item["board"],
                 item["body"], item["code"], item["pins"], item["libs"],
                 item["tags"], "v1.0", "ACTIVE", now, now))
            r["new"] += 1
        r["synced"] += 1
    return r


def _sync_components(conn):
    r = {"synced": 0, "new": 0, "updated": 0}
    now = _now()
    for item in COMPONENTS:
        cid = "ARD-COMP-%s" % uuid.uuid4().hex[:10]
        existing = conn.execute(
            "SELECT component_id FROM mt_arduino_components WHERE component_name=?",
            (item["name"],)).fetchone()
        if existing:
            conn.execute("""UPDATE mt_arduino_components SET
                category=?, pin_type=?, voltage=?, description=?,
                code_template=?, libraries_req=?, difficulty=?, updated_at=?
                WHERE component_id=?""",
                (item["cat"], item["pin"], item["volt"], item["desc"],
                 item["code"], item["libs"], item["diff"], now, existing[0]))
            r["updated"] += 1
        else:
            conn.execute("""INSERT INTO mt_arduino_components
                (component_id, component_name, category, pin_type, voltage,
                 description, code_template, libraries_req, difficulty,
                 version, status, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (cid, item["name"], item["cat"], item["pin"], item["volt"],
                 item["desc"], item["code"], item["libs"], item["diff"],
                 "v1.0", "ACTIVE", now, now))
            r["new"] += 1
        r["synced"] += 1
    return r


def _sync_experiments(conn):
    r = {"synced": 0, "new": 0, "updated": 0}
    now = _now()
    for item in EXPERIMENTS:
        eid = "ARD-EXP-%s" % uuid.uuid4().hex[:10]
        existing = conn.execute(
            "SELECT experiment_id FROM mt_arduino_experiments WHERE experiment_name=?",
            (item["name"],)).fetchone()
        if existing:
            conn.execute("""UPDATE mt_arduino_experiments SET
                difficulty=?, board_type=?, objective=?, components_req=?,
                wiring_json=?, code_complete=?, explanation=?, safety_notes=?,
                updated_at=? WHERE experiment_id=?""",
                (item["diff"], item["board"], item["obj"], item["comps"],
                 item["wiring"], item["code"], item["exp"], item.get("safety", ""),
                 now, existing[0]))
            r["updated"] += 1
        else:
            conn.execute("""INSERT INTO mt_arduino_experiments
                (experiment_id, experiment_name, difficulty, board_type,
                 objective, components_req, wiring_json, code_complete,
                 explanation, safety_notes, version, status,
                 created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (eid, item["name"], item["diff"], item["board"],
                 item["obj"], item["comps"], item["wiring"], item["code"],
                 item["exp"], item.get("safety", ""), "v1.0", "ACTIVE", now, now))
            r["new"] += 1
        r["synced"] += 1
    return r


def _sync_boards(conn):
    r = {"synced": 0, "new": 0, "updated": 0}
    now = _now()
    for item in BOARDS:
        bid = "ARD-BOARD-%s" % uuid.uuid4().hex[:10]
        existing = conn.execute(
            "SELECT board_id FROM mt_arduino_boards WHERE board_name=?",
            (item["name"],)).fetchone()
        if existing:
            conn.execute("""UPDATE mt_arduino_boards SET
                manufacturer=?, cpu=?, clock_speed=?, flash_memory=?,
                digital_pins=?, analog_pins=?, pwm_pins=?, communication=?,
                features=?, updated_at=? WHERE board_id=?""",
                (item["mfr"], item["cpu"], item["clk"], item["flash"],
                 item["d_pins"], item["a_pins"], item["pwm"], item["comm"],
                 item["feat"], now, existing[0]))
            r["updated"] += 1
        else:
            conn.execute("""INSERT INTO mt_arduino_boards
                (board_id, board_name, manufacturer, cpu, clock_speed,
                 flash_memory, digital_pins, analog_pins, pwm_pins,
                 communication, features, version, status,
                 created_at, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (bid, item["name"], item["mfr"], item["cpu"], item["clk"],
                 item["flash"], item["d_pins"], item["a_pins"], item["pwm"],
                 item["comm"], item["feat"], "v1.0", "ACTIVE", now, now))
            r["new"] += 1
        r["synced"] += 1
    return r


def sync_all():
    ensure_arduino_tables()
    results = {}
    now = _now()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        results["tutorials"] = _sync_tutorials(conn)
        results["components"] = _sync_components(conn)
        results["experiments"] = _sync_experiments(conn)
        results["boards"] = _sync_boards(conn)
        total_synced = sum(r["synced"] for r in results.values())
        total_new = sum(r["new"] for r in results.values())
        total_updated = sum(r["updated"] for r in results.values())
        sid = "ARD-SYNC-%s" % uuid.uuid4().hex[:10]
        conn.execute("""INSERT INTO mt_arduino_sync_log
            (sync_id, items_synced, items_new, items_updated,
             details_json, sync_status, synced_at)
            VALUES(?,?,?,?,?,?,?)""",
            (sid, total_synced, total_new, total_updated,
             json.dumps(results, ensure_ascii=False)[:2000],
             "SUCCESS", now))
        conn.commit()
        conn.close()
    _log(f"[SYNC] synced={total_synced} new={total_new} updated={total_updated}")
    return results


def get_status():
    ensure_arduino_tables()
    with _LOCK:
        conn = sqlite3.connect(APP_DB, timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        tuts = c.execute("SELECT COUNT(*) FROM mt_arduino_tutorials WHERE status='ACTIVE'").fetchone()[0]
        comps = c.execute("SELECT COUNT(*) FROM mt_arduino_components WHERE status='ACTIVE'").fetchone()[0]
        exps = c.execute("SELECT COUNT(*) FROM mt_arduino_experiments WHERE status='ACTIVE'").fetchone()[0]
        boards = c.execute("SELECT COUNT(*) FROM mt_arduino_boards WHERE status='ACTIVE'").fetchone()[0]
        syncs = c.execute("SELECT COUNT(*) FROM mt_arduino_sync_log").fetchone()[0]
        last = c.execute("SELECT * FROM mt_arduino_sync_log ORDER BY synced_at DESC LIMIT 1").fetchone()
        # 按分类统计
        tut_cats = {}
        for row in c.execute("SELECT category, COUNT(*) as cnt FROM mt_arduino_tutorials WHERE status='ACTIVE' GROUP BY category").fetchall():
            tut_cats[row["category"]] = row["cnt"]
        conn.close()
    return {"tutorials": tuts, "components": comps, "experiments": exps,
            "boards": boards, "sync_count": syncs,
            "tut_categories": tut_cats, "last_sync": dict(last) if last else None}


# ============================================================
# 4. CLI
# ============================================================
class ArduinoDaemon:
    @staticmethod
    def read_pid():
        if not os.path.exists(PID_FILE):
            return None
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return pid
        except (ValueError, OSError):
            return None

    @staticmethod
    def clear_pid():
        try:
            os.remove(PID_FILE)
        except OSError:
            pass

    @staticmethod
    def start():
        existing = ArduinoDaemon.read_pid()
        if existing:
            print(f"[STATUS] RUNNING pid={existing}")
            return
        ensure_arduino_tables()
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        def _term(signum, frame):
            _log("[DAEMON] SIGTERM")
            ArduinoDaemon.clear_pid()
            sys.exit(0)
        signal.signal(signal.SIGTERM, _term)
        signal.signal(signal.SIGINT, _term)
        _log(f"[DAEMON] START pid={os.getpid()} interval={SYNC_INTERVAL}s")
        sync_all()
        while True:
            time.sleep(SYNC_INTERVAL)
            try:
                _log("[DAEMON] sync cycle...")
                sync_all()
            except Exception as e:
                _log(f"[DAEMON] ERROR: {e}")

    @staticmethod
    def stop():
        pid = ArduinoDaemon.read_pid()
        if not pid:
            print("[STATUS] STOPPED")
            return
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        ArduinoDaemon.clear_pid()
        print("[STATUS] STOPPED")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1].lower()
    if cmd == "start":
        ArduinoDaemon.start()
    elif cmd == "stop":
        ArduinoDaemon.stop()
    elif cmd == "sync":
        r = sync_all()
        print(f"{'='*60}")
        print(f"  Arduino Sync Result")
        print(f"{'='*60}")
        for k, v in r.items():
            print(f"  {k:15s}: synced={v['synced']} new={v['new']} updated={v['updated']}")
    elif cmd == "status":
        s = get_status()
        print(f"{'='*60}")
        print(f"  Arduino Programming Sync Engine")
        print(f"{'='*60}")
        pid = ArduinoDaemon.read_pid()
        print(f"  Daemon: {'RUNNING' if pid else 'STOPPED'}  pid={pid or '-'}")
        print(f"  Tutorials:  {s['tutorials']}")
        print(f"  Components: {s['components']}")
        print(f"  Experiments:{s['experiments']}")
        print(f"  Boards:     {s['boards']}")
        print(f"  Sync Count: {s['sync_count']}")
        print(f"{'='*60}")
        print(f"  Tutorials by Category:")
        for cat, cnt in s["tut_categories"].items():
            print(f"    {cat:15s}: {cnt}")
        if s["last_sync"]:
            ls = s["last_sync"]
            print(f"{'='*60}")
            print(f"  Last Sync: {ls['synced_at']}")
            print(f"  Items: synced={ls['items_synced']} new={ls['items_new']} updated={ls['items_updated']}")
    else:
        print(f"  未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
