#!/usr/bin/env python3
import re
import time
from datetime import datetime
from collections import defaultdict

class ArduinoSimulator:
    """Arduino仿真模拟器 - 模拟Arduino代码执行"""
    
    def __init__(self):
        self.pins = defaultdict(lambda: {'mode': 'INPUT', 'value': 0})
        self.serial_buffer = []
        self.serial_baud = 9600
        self.millis_count = 0
        self.micros_count = 0
        self.last_time = time.time()
        self.variables = {}
        self.servo_angles = {}
        self.analog_values = defaultdict(int)
        self.digital_values = defaultdict(int)
        self.led_states = defaultdict(bool)
        self.simulation_log = []
        self.is_running = False
    
    def _log(self, level, message):
        """记录模拟日志"""
        self.simulation_log.append({
            'timestamp': datetime.now().strftime('%H:%M:%S.%f'),
            'level': level,
            'message': message
        })
    
    def _parse_code(self, code):
        """解析代码结构"""
        lines = code.split('\n')
        setup_lines = []
        loop_lines = []
        in_setup = False
        in_loop = False
        
        for line in lines:
            stripped = line.strip()
            
            if 'void setup()' in stripped or 'void setup (' in stripped:
                in_setup = True
                in_loop = False
                continue
            
            if 'void loop()' in stripped or 'void loop (' in stripped:
                in_setup = False
                in_loop = True
                continue
            
            if '}' in stripped and (in_setup or in_loop):
                brace_count = stripped.count('}')
                for _ in range(brace_count):
                    if in_setup:
                        in_setup = False
                    elif in_loop:
                        in_loop = False
                continue
            
            if in_setup:
                setup_lines.append(line)
            elif in_loop:
                loop_lines.append(line)
        
        return {
            'setup': setup_lines,
            'loop': loop_lines,
            'total_lines': len(lines)
        }
    
    def _execute_statement(self, line):
        """执行单条语句"""
        line = line.strip()
        if not line or line.startswith('//'):
            return
        
        if 'pinMode(' in line:
            match = re.search(r'pinMode\s*\(\s*(\w+)\s*,\s*(INPUT|OUTPUT|INPUT_PULLUP)\s*\)', line)
            if match:
                pin = match.group(1)
                mode = match.group(2)
                self.pins[pin]['mode'] = mode
                self._log('info', f"设置引脚 {pin} 模式为 {mode}")
        
        elif 'digitalWrite(' in line:
            match = re.search(r'digitalWrite\s*\(\s*(\w+)\s*,\s*(HIGH|LOW)\s*\)', line)
            if match:
                pin = match.group(1)
                value = 1 if match.group(2) == 'HIGH' else 0
                self.pins[pin]['value'] = value
                self.digital_values[pin] = value
                
                if pin.isdigit():
                    pin_num = int(pin)
                    if pin_num == 13 or pin_num in [3, 5, 6, 9, 10, 11]:
                        self.led_states[pin] = value == 1
                        state = 'ON' if value == 1 else 'OFF'
                        self._log('info', f"LED[{pin}] -> {state}")
                else:
                    self._log('info', f"数字输出 {pin} -> {'HIGH' if value == 1 else 'LOW'}")
        
        elif 'analogWrite(' in line:
            match = re.search(r'analogWrite\s*\(\s*(\w+)\s*,\s*(\d+)\s*\)', line)
            if match:
                pin = match.group(1)
                value = int(match.group(2))
                self.pins[pin]['value'] = value
                self.analog_values[pin] = value
                
                if pin.isdigit() and int(pin) in [3, 5, 6, 9, 10, 11]:
                    brightness = value / 255 * 100
                    self._log('info', f"PWM输出 [{pin}] -> {value} ({brightness:.1f}%)")
                else:
                    self._log('info', f"模拟输出 [{pin}] -> {value}")
        
        elif 'digitalRead(' in line:
            match = re.search(r'digitalRead\s*\(\s*(\w+)\s*\)', line)
            if match:
                pin = match.group(1)
                value = self.pins[pin]['value']
                self._log('debug', f"读取数字输入 [{pin}] -> {value}")
        
        elif 'analogRead(' in line:
            match = re.search(r'analogRead\s*\(\s*(\w+)\s*\)', line)
            if match:
                pin = match.group(1)
                value = self.analog_values.get(pin, 0)
                self._log('debug', f"读取模拟输入 [{pin}] -> {value}")
        
        elif 'Serial.begin(' in line:
            match = re.search(r'Serial\.begin\s*\(\s*(\d+)\s*\)', line)
            if match:
                self.serial_baud = int(match.group(1))
                self._log('info', f"初始化串口, 波特率: {self.serial_baud}")
        
        elif 'Serial.logger.info(' in line:
            match = re.search(r'Serial\.print\s*\(\s*(.+?)\s*\)', line)
            if match:
                content = match.group(1).strip('"\'')
                self.serial_buffer.append(content)
                self._log('serial', f"串口输出: {content}")
        
        elif 'Serial.println(' in line:
            match = re.search(r'Serial\.println\s*\(\s*(.+?)\s*\)', line)
            if match:
                content = match.group(1).strip('"\'')
                self.serial_buffer.append(content + '\n')
                self._log('serial', f"串口输出(换行): {content}")
        
        elif 'delay(' in line:
            match = re.search(r'delay\s*\(\s*(\d+)\s*\)', line)
            if match:
                ms = int(match.group(1))
                self.millis_count += ms
                self._log('debug', f"延时 {ms}ms")
        
        elif 'Servo' in line and 'attach(' in line:
            match = re.search(r'Servo\s+(\w+).*attach\s*\(\s*(\w+)\s*\)', line)
            if match:
                servo_name = match.group(1)
                pin = match.group(2)
                self.servo_angles[servo_name] = 90
                self._log('info', f"舵机 [{servo_name}] 连接到引脚 {pin}, 初始角度 90°")
        
        elif '.write(' in line:
            match = re.search(r'(\w+)\.write\s*\(\s*(\d+)\s*\)', line)
            if match:
                servo_name = match.group(1)
                angle = int(match.group(2))
                if servo_name in self.servo_angles:
                    self.servo_angles[servo_name] = angle
                    self._log('info', f"舵机 [{servo_name}] 转动到 {angle}°")
        
        elif 'tone(' in line:
            match = re.search(r'tone\s*\(\s*(\w+)\s*,\s*(\d+)\s*(?:,\s*(\d+))?\s*\)', line)
            if match:
                pin = match.group(1)
                freq = int(match.group(2))
                duration = match.group(3)
                if duration:
                    self._log('info', f"蜂鸣器 [{pin}] 播放 {freq}Hz, 持续 {duration}ms")
                else:
                    self._log('info', f"蜂鸣器 [{pin}] 播放 {freq}Hz")
        
        elif 'noTone(' in line:
            match = re.search(r'noTone\s*\(\s*(\w+)\s*\)', line)
            if match:
                pin = match.group(1)
                self._log('info', f"蜂鸣器 [{pin}] 停止播放")
    
    def simulate(self, code, iterations=5, speed=1.0):
        """模拟执行Arduino代码"""
        self.simulation_log = []
        self.is_running = True
        
        parsed = self._parse_code(code)
        self._log('info', f"开始模拟, setup: {len(parsed['setup'])}行, loop: {len(parsed['loop'])}行")
        
        self._log('info', "=== 执行 setup() ===")
        for line in parsed['setup']:
            if not self.is_running:
                break
            self._execute_statement(line)
        
        self._log('info', "=== 执行 loop() ===")
        for iteration in range(iterations):
            if not self.is_running:
                break
            
            self._log('info', f"--- Loop 迭代 {iteration + 1} ---")
            for line in parsed['loop']:
                if not self.is_running:
                    break
                self._execute_statement(line)
            
            if iteration < iterations - 1:
                time.sleep(0.1 / speed)
        
        self.is_running = False
        self._log('info', "模拟结束")
        
        return self.get_simulation_result()
    
    def get_simulation_result(self):
        """获取模拟结果"""
        return {
            'log': self.simulation_log,
            'pin_states': {k: dict(v) for k, v in self.pins.items()},
            'serial_output': ''.join(self.serial_buffer),
            'led_states': dict(self.led_states),
            'servo_angles': dict(self.servo_angles),
            'analog_values': dict(self.analog_values),
            'digital_values': dict(self.digital_values),
            'millis': self.millis_count,
            'total_log_entries': len(self.simulation_log)
        }
    
    def set_analog_input(self, pin, value):
        """设置模拟输入值"""
        if 0 <= value <= 1023:
            self.analog_values[pin] = value
            self._log('debug', f"设置模拟输入 [{pin}] = {value}")
    
    def set_digital_input(self, pin, value):
        """设置数字输入值"""
        self.digital_values[pin] = value
        self.pins[pin]['value'] = value
        self.pins[pin]['mode'] = 'INPUT'
        self._log('debug', f"设置数字输入 [{pin}] = {'HIGH' if value == 1 else 'LOW'}")
    
    def stop(self):
        """停止模拟"""
        self.is_running = False
    
    def reset(self):
        """重置模拟器状态"""
        self.pins = defaultdict(lambda: {'mode': 'INPUT', 'value': 0})
        self.serial_buffer = []
        self.millis_count = 0
        self.micros_count = 0
        self.variables = {}
        self.servo_angles = {}
        self.analog_values = defaultdict(int)
        self.digital_values = defaultdict(int)
        self.led_states = defaultdict(bool)
        self.simulation_log = []
        self.is_running = False

if __name__ == '__main__':
    simulator = ArduinoSimulator()
    
    test_code = '''
int ledPin = 13;

void setup() {
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
  Serial.println("LED Blink Test");
}

void loop() {
  digitalWrite(ledPin, HIGH);
  Serial.println("LED ON");
  delay(1000);
  digitalWrite(ledPin, LOW);
  Serial.println("LED OFF");
  delay(1000);
}
'''
    
    logger.info("=== Arduino仿真模拟器 ===")
    logger.info("\n测试代码: LED闪烁")
    logger.info("=" * 50)
    
    result = simulator.simulate(test_code, iterations=3)
    
    logger.info("\n模拟日志:")
    for entry in result['log']:
        if entry['level'] in ['info', 'serial']:
            logger.info(f"  [{entry['level']}] {entry['message']}")
    
    logger.info("\nLED状态:")
    for pin, state in result['led_states'].items():
        logger.info(f"  LED[{pin}]: {'亮' if state else '灭'}")
    
    logger.info("\n串口输出:")
    logger.info(result['serial_output'])
    
    logger.info("\n引脚状态:")
    for pin, state in result['pin_states'].items():
        logger.info(f"  {pin}: mode={state['mode']}, value={state['value']}")
    
    logger.info("\n=== 测试舵机代码 ===")
    simulator.reset()
    
    servo_code = '''
#include <Servo.h>

Servo myservo;

void setup() {
  myservo.attach(9);
  Serial.begin(9600);
}

void loop() {
  myservo.write(0);
  Serial.println("Servo: 0°");
  delay(500);
  myservo.write(90);
  Serial.println("Servo: 90°");
  delay(500);
  myservo.write(180);
  Serial.println("Servo: 180°");
  delay(500);
}
'''
    
    result = simulator.simulate(servo_code, iterations=1)
    
    logger.info("\n舵机角度:")
    for servo, angle in result['servo_angles'].items():
        logger.info(f"  {servo}: {angle}°")
    
    logger.info("\n串口输出:")
    logger.info(result['serial_output'])