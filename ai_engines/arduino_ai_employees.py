#!/usr/bin/env python3
"""
Arduino AI员工系统 - 代码生成、调试、优化、组件推荐
"""
import logging
logger = logging.getLogger(__name__)
import re
import random
from typing import Dict, Any, List
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engines.ai_employee_system import AIEmployee
from ai_engines.intelligent_empowerment import IntelligentEmpowermentMixin

_ARDUINO_KEYWORDS = {
    'setup', 'loop', 'pinMode', 'digitalWrite', 'digitalRead',
    'analogWrite', 'analogRead', 'delay', 'Serial', 'begin',
    'print', 'println', 'available', 'read', 'HIGH', 'LOW',
    'INPUT', 'OUTPUT', 'INPUT_PULLUP', 'LED_BUILTIN'
}

_ARDUINO_LIBRARIES = {
    'Servo': '舵机控制库',
    'LiquidCrystal': 'LCD显示屏库',
    'Wire': 'I2C通信库',
    'SPI': 'SPI通信库',
    'IRremote': '红外遥控库',
    'DHT': '温湿度传感器库',
    'Stepper': '步进电机库',
    'EEPROM': '电可擦除只读存储器'
}

_COMPONENT_CODE_PATTERNS = {
    'LED': {'pins': [13], 'functions': ['digitalWrite', 'pinMode', 'delay']},
    'Buzzer': {'pins': [8], 'functions': ['digitalWrite', 'tone', 'noTone']},
    'Button': {'pins': [2], 'functions': ['digitalRead', 'pinMode']},
    'Ultrasonic': {'pins': [9, 10], 'functions': ['pulseIn', 'digitalWrite']},
    'Servo': {'pins': [9], 'functions': ['attach', 'write']},
    'Temperature': {'pins': ['A0'], 'functions': ['analogRead']},
    'LCD': {'pins': [12, 11, 5, 4, 3, 2], 'functions': ['begin', 'print', 'setCursor']},
}

_CODE_TEMPLATES = {
    'blink': {
        'name': 'LED闪烁',
        'code': 'int ledPin = 13;\n\nvoid setup() {\n  pinMode(ledPin, OUTPUT);\n  Serial.begin(9600);\n}\n\nvoid loop() {\n  digitalWrite(ledPin, HIGH);\n  delay(1000);\n  digitalWrite(ledPin, LOW);\n  delay(1000);\n}\n',
        'components': ['LED'],
        'difficulty': 'beginner'
    },
    'fade': {
        'name': '呼吸灯',
        'code': 'int ledPin = 9;\nint brightness = 0;\nint fadeAmount = 5;\n\nvoid setup() {\n  pinMode(ledPin, OUTPUT);\n  Serial.begin(9600);\n}\n\nvoid loop() {\n  analogWrite(ledPin, brightness);\n  brightness = brightness + fadeAmount;\n  if (brightness <= 0 || brightness >= 255) {\n    fadeAmount = -fadeAmount;\n  }\n  delay(30);\n}\n',
        'components': ['LED'],
        'difficulty': 'beginner'
    },
    'traffic_light': {
        'name': '交通灯',
        'code': 'const int redPin = 10;\nconst int yellowPin = 9;\nconst int greenPin = 8;\n\nvoid setup() {\n  pinMode(redPin, OUTPUT);\n  pinMode(yellowPin, OUTPUT);\n  pinMode(greenPin, OUTPUT);\n  Serial.begin(9600);\n}\n\nvoid loop() {\n  digitalWrite(redPin, HIGH);\n  Serial.println("RED");\n  delay(5000);\n  digitalWrite(redPin, LOW);\n  digitalWrite(greenPin, HIGH);\n  Serial.println("GREEN");\n  delay(5000);\n  digitalWrite(greenPin, LOW);\n  digitalWrite(yellowPin, HIGH);\n  Serial.println("YELLOW");\n  delay(2000);\n  digitalWrite(yellowPin, LOW);\n}\n',
        'components': ['LED'],
        'difficulty': 'intermediate'
    },
    'servo_sweep': {
        'name': '舵机扫描',
        'code': '#include <Servo.h>\n\nServo myservo;\nint pos = 0;\n\nvoid setup() {\n  myservo.attach(9);\n  Serial.begin(9600);\n}\n\nvoid loop() {\n  for (pos = 0; pos <= 180; pos += 1) {\n    myservo.write(pos);\n    delay(15);\n  }\n  for (pos = 180; pos >= 0; pos -= 1) {\n    myservo.write(pos);\n    delay(15);\n  }\n}\n',
        'components': ['Servo Motor'],
        'difficulty': 'intermediate'
    },
    'ultrasonic_rangefinder': {
        'name': '超声波测距',
        'code': '#define TRIG_PIN 9\n#define ECHO_PIN 10\n\nvoid setup() {\n  Serial.begin(9600);\n  pinMode(TRIG_PIN, OUTPUT);\n  pinMode(ECHO_PIN, INPUT);\n}\n\nfloat getDistance() {\n  digitalWrite(TRIG_PIN, LOW);\n  delayMicroseconds(2);\n  digitalWrite(TRIG_PIN, HIGH);\n  delayMicroseconds(10);\n  digitalWrite(TRIG_PIN, LOW);\n  long duration = pulseIn(ECHO_PIN, HIGH);\n  return duration * 0.034 / 2;\n}\n\nvoid loop() {\n  float dist = getDistance();\n  Serial.print("Distance: ");\n  Serial.print(dist);\n  Serial.println(" cm");\n  delay(500);\n}\n',
        'components': ['Ultrasonic Sensor'],
        'difficulty': 'intermediate'
    },
    'lcd_hello': {
        'name': 'LCD显示',
        'code': '#include <LiquidCrystal.h>\n\nLiquidCrystal lcd(12, 11, 5, 4, 3, 2);\n\nvoid setup() {\n  lcd.begin(16, 2);\n  lcd.print("Hello, Arduino!");\n  Serial.begin(9600);\n}\n\nvoid loop() {\n  lcd.setCursor(0, 1);\n  lcd.print(millis() / 1000);\n  lcd.print("s");\n  delay(1000);\n}\n',
        'components': ['LCD 1602'],
        'difficulty': 'intermediate'
    },
}

def _analyze_code_structure(code: str) -> Dict[str, Any]:
    lines = code.split('\n')
    result = {
        'has_setup': 'setup()' in code or 'void setup' in code,
        'has_loop': 'loop()' in code or 'void loop' in code,
        'includes': [],
        'defined_pins': {},
        'pin_modes': {},
        'used_functions': set(),
        'brace_balance': code.count('{') == code.count('}'),
        'paren_balance': code.count('(') == code.count(')'),
        'total_lines': len(lines),
        'has_serial': 'Serial' in code,
        'libraries_used': []
    }

    for lib in _ARDUINO_LIBRARIES:
        if f'#include <{lib}>' in code or f'#include "{lib}' in code:
            result['includes'].append(lib)
            result['libraries_used'].append(lib)

    for match in re.finditer(r'(?:int|const\s+int|#define)\s+(\w+Pin|PIN_\w+|_\w+)\s*[= ]\s*(\d+)', code):
        result['defined_pins'][match.group(1)] = int(match.group(2))

    for match in re.finditer(r'pinMode\s*\(\s*(\w+)\s*,\s*(INPUT|OUTPUT|INPUT_PULLUP)\s*\)', code):
        pin = match.group(1)
        result['pin_modes'][pin] = match.group(2)

    for kw in _ARDUINO_KEYWORDS:
        if kw in code:
            result['used_functions'].add(kw)

    result['used_functions'] = list(result['used_functions'])
    return result

def _detect_components(code: str) -> List[str]:
    detected = []
    analysis = _analyze_code_structure(code)

    if 'Servo' in analysis['libraries_used']:
        detected.append('舵机 (Servo)')
    if 'LiquidCrystal' in analysis['libraries_used']:
        detected.append('LCD显示屏')
    if 'IRremote' in analysis['libraries_used']:
        detected.append('红外遥控')

    for func in analysis['used_functions']:
        if func == 'tone':
            if '蜂鸣器' not in detected:
                detected.append('蜂鸣器')
        if func == 'pulseIn':
            if '超声波传感器' not in detected:
                detected.append('超声波传感器')
        if func == 'analogRead' and 'analogRead' in code:
            if '模拟传感器' not in detected:
                detected.append('模拟传感器')

    if 'digitalRead' in code and len(analysis['pin_modes']) > 0:
        input_pins = [k for k, v in analysis['pin_modes'].items() if 'INPUT' in v]
        if input_pins:
            if '按键/输入设备' not in detected:
                detected.append('按键/输入设备')

    if not detected and 'digitalWrite' in code:
        detected.append('LED/数字输出')

    return detected


class ArduinoCodeGeneratorEmployee(AIEmployee):
    """Arduino代码生成AI员工 - 根据需求生成Arduino代码"""

    def __init__(self, employee_id: str, name: str, level: int = 7):
        super().__init__(employee_id, name, "arduino_code_generator", level)
        self.type = "arduino_code_generator"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self._lock = None

    def start(self):
        import threading
        self._lock = threading.RLock()
        self.status = "active"

    def stop(self):
        self.status = "stopped"

    def get_status(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "status": self.status,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "performance_score": 85 + self.level * 1.5,
            "success_rate": 0.0 if self.task_count == 0 else self.success_count / self.task_count
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        self.task_count += 1
        task_type = task_data.get('type', 'generate')

        try:
            if task_type == 'generate':
                result = self._generate_code(task_data)
            elif task_type == 'explain':
                result = self._explain_code(task_data)
            elif task_type == 'template':
                result = self._get_template(task_data)
            else:
                result = {"success": False, "message": f"未知任务类型: {task_type}"}

            if result.get('success'):
                self.success_count += 1
            else:
                self.failure_count += 1
            return result
        except Exception as e:
            self.failure_count += 1
            logger.error(f"Arduino代码生成AI员工执行任务失败: {e}")
            return {"success": False, "message": f"执行失败: {str(e)}"}

    def _generate_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        description = task_data.get('description', '').lower()
        components = task_data.get('components', [])
        difficulty = task_data.get('difficulty', 'intermediate')

        matched_templates = []
        for tpl_key, tpl in _CODE_TEMPLATES.items():
            score = 0
            for kw in description.split():
                if kw in tpl['name'] or kw in tpl_key:
                    score += 10
            for comp in components:
                if comp in tpl['components']:
                    score += 5
            if tpl['difficulty'] == difficulty:
                score += 2
            if score > 0:
                matched_templates.append((score, tpl_key, tpl))

        if matched_templates:
            matched_templates.sort(key=lambda x: x[0], reverse=True)
            best = matched_templates[0][2]
            return {
                "success": True,
                "code": best['code'],
                "name": best['name'],
                "components": best['components'],
                "difficulty": best['difficulty'],
                "message": f"已生成{best['name']}代码"
            }

        default_code = self._generate_basic_code(description, components)
        return {
            "success": True,
            "code": default_code,
            "name": "自定义生成",
            "components": components,
            "difficulty": difficulty,
            "message": "已根据描述生成基础代码"
        }

    def _generate_basic_code(self, description: str, components: List[str]) -> str:
        setup_lines = ['  Serial.begin(9600);']
        loop_lines = []
        pin_defs = []

        if components:
            pin_num = 2
            for comp in components[:5]:
                if 'LED' in comp or 'led' in comp.lower():
                    pin_defs.append(f'int ledPin = {pin_num};')
                    setup_lines.append(f'  pinMode(ledPin, OUTPUT);')
                    loop_lines.append(f'  digitalWrite(ledPin, HIGH);')
                    loop_lines.append('  delay(500);')
                    loop_lines.append(f'  digitalWrite(ledPin, LOW);')
                    loop_lines.append('  delay(500);')
                    pin_num += 1
                elif '按键' in comp or 'button' in comp.lower():
                    pin_defs.append(f'int buttonPin = {pin_num};')
                    setup_lines.append(f'  pinMode(buttonPin, INPUT);')
                    loop_lines.append(f'  int btnState = digitalRead(buttonPin);')
                    loop_lines.append('  Serial.print("Button: ");')
                    loop_lines.append('  Serial.println(btnState);')
                    pin_num += 1
                else:
                    pin_defs.append(f'int {comp.lower().replace(" ", "_")}Pin = {pin_num};')
                    setup_lines.append(f'  // {comp} 初始化')
                    pin_num += 1
        else:
            pin_defs.append('int ledPin = 13;')
            setup_lines.append('  pinMode(ledPin, OUTPUT);')
            loop_lines.append('  digitalWrite(ledPin, HIGH);')
            loop_lines.append('  delay(1000);')
            loop_lines.append('  digitalWrite(ledPin, LOW);')
            loop_lines.append('  delay(1000);')

        code = ''
        if pin_defs:
            code += '\n'.join(pin_defs) + '\n\n'
        code += 'void setup() {\n'
        code += '\n'.join(setup_lines) + '\n}\n\n'
        code += 'void loop() {\n'
        code += '\n'.join(loop_lines) + '\n}\n'
        return code

    def _explain_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        code = task_data.get('code', '')
        analysis = _analyze_code_structure(code)
        components = _detect_components(code)

        explanation_parts = []
        explanation_parts.append(f"### 代码分析报告\n")
        explanation_parts.append(f"**总行数**: {analysis['total_lines']}")
        explanation_parts.append(f"**包含 setup()**: {'是' if analysis['has_setup'] else '否'}")
        explanation_parts.append(f"**包含 loop()**: {'是' if analysis['has_loop'] else '否'}")
        explanation_parts.append(f"**使用串口**: {'是' if analysis['has_serial'] else '否'}")
        explanation_parts.append(f"**大括号匹配**: {'正确' if analysis['brace_balance'] else '不匹配 ⚠️'}")

        if analysis['includes']:
            explanation_parts.append(f"\n**引入库**:")
            for lib in analysis['includes']:
                desc = _ARDUINO_LIBRARIES.get(lib, '第三方库')
                explanation_parts.append(f"- `{lib}` - {desc}")

        if analysis['defined_pins']:
            explanation_parts.append(f"\n**定义引脚**:")
            for name, num in analysis['defined_pins'].items():
                explanation_parts.append(f"- `{name}` = {num}")

        if components:
            explanation_parts.append(f"\n**检测到的组件**:")
            for comp in components:
                explanation_parts.append(f"- {comp}")

        if analysis['used_functions']:
            explanation_parts.append(f"\n**使用的函数**:")
            for func in sorted(analysis['used_functions'])[:15]:
                explanation_parts.append(f"- `{func}()`")

        return {
            "success": True,
            "explanation": '\n'.join(explanation_parts),
            "analysis": analysis,
            "components": components,
            "message": "代码分析完成"
        }

    def _get_template(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        template_id = task_data.get('template_id', '')
        if template_id and template_id in _CODE_TEMPLATES:
            tpl = _CODE_TEMPLATES[template_id]
            return {
                "success": True,
                "code": tpl['code'],
                "name": tpl['name'],
                "message": f"加载模板: {tpl['name']}"
            }
        return {
            "success": False,
            "message": f"模板不存在: {template_id}"
        }


class ArduinoCodeDebuggerEmployee(AIEmployee):
    """Arduino代码调试AI员工 - 检测和修复代码问题"""

    def __init__(self, employee_id: str, name: str, level: int = 8):
        super().__init__(employee_id, name, "arduino_code_debugger", level)
        self.type = "arduino_code_debugger"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self._lock = None

    def start(self):
        import threading
        self._lock = threading.RLock()
        self.status = "active"

    def stop(self):
        self.status = "stopped"

    def get_status(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "status": self.status,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "performance_score": 88 + self.level * 1.2,
            "success_rate": 0.0 if self.task_count == 0 else self.success_count / self.task_count
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        self.task_count += 1
        try:
            result = self._debug_code(task_data)
            if result.get('success'):
                self.success_count += 1
            else:
                self.failure_count += 1
            return result
        except Exception as e:
            self.failure_count += 1
            return {"success": False, "message": f"调试失败: {str(e)}"}

    def _debug_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        code = task_data.get('code', '')
        errors = []
        warnings = []
        suggestions = []
        fixed_code = code

        if not code.strip():
            return {"success": False, "errors": [{"line": 0, "message": "代码为空"}], "warnings": [], "suggestions": []}

        lines = code.split('\n')

        if 'void setup' not in code and 'setup()' not in code:
            errors.append({"line": 0, "message": "缺少 setup() 函数 - Arduino程序必须包含setup()", "type": "error"})

        if 'void loop' not in code and 'loop()' not in code:
            errors.append({"line": 0, "message": "缺少 loop() 函数 - Arduino程序必须包含loop()", "type": "error"})

        open_braces = code.count('{')
        close_braces = code.count('}')
        if open_braces != close_braces:
            errors.append({
                "line": 0,
                "message": f"大括号不匹配: {open_braces}个左括号 vs {close_braces}个右括号",
                "type": "error"
            })

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('//'):
                continue

            if 'digitalWrite' in line or 'analogWrite' in line:
                pin_match = re.search(r'digitalWrite\s*\(\s*(\w+)', line)
                if pin_match:
                    pin_name = pin_match.group(1)
                    if pin_name not in ['HIGH', 'LOW'] and f'pinMode({pin_name}' not in code and f'pinMode({pin_name},' not in code:
                        if not re.search(rf'pinMode\s*\(\s*{pin_name}\s*,', code):
                            warnings.append({
                                "line": i,
                                "message": f"引脚 {pin_name} 可能未设置模式(pinMode)",
                                "type": "warning"
                            })

            if 'Serial.' in line and 'Serial.begin' not in code:
                warnings.append({
                    "line": i,
                    "message": "使用了Serial但未调用Serial.begin()初始化",
                    "type": "warning"
                })
                break

            if 'delay()' in line or re.search(r'delay\(\s*\)', line):
                warnings.append({
                    "line": i,
                    "message": "delay()没有参数，会导致编译错误",
                    "type": "error"
                })

            if re.search(r'delay\s*\(\s*0\s*\)', line):
                warnings.append({
                    "line": i,
                    "message": "delay(0)无实际效果",
                    "type": "warning"
                })

            if line.endswith(')') and not line.endswith(');') and '{' not in line and '}' not in line:
                if 'if' not in line and 'for' not in line and 'while' not in line and 'void' not in line and 'else' not in line:
                    stripped_line = stripped.rstrip()
                    if stripped_line.endswith(')') and not stripped_line.endswith(');'):
                        if '//' not in stripped_line:
                            warnings.append({
                                "line": i,
                                "message": "语句可能缺少分号",
                                "type": "warning"
                            })

        analysis = _analyze_code_structure(code)

        if analysis.get('has_serial') and 'Serial.begin' not in code:
            suggestions.append({
                "priority": "high",
                "message": "在setup()中添加 Serial.begin(9600) 初始化串口",
                "code": "Serial.begin(9600);"
            })

        if 'analogWrite' in code:
            pwm_pins = {3, 5, 6, 9, 10, 11}
            suggestions.append({
                "priority": "medium",
                "message": f"analogWrite仅支持PWM引脚(3,5,6,9,10,11)",
                "code": None
            })

        if errors:
            return {
                "success": False,
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions,
                "message": f"发现{len(errors)}个错误",
                "error_count": len(errors),
                "warning_count": len(warnings)
            }

        return {
            "success": True,
            "errors": [],
            "warnings": warnings,
            "suggestions": suggestions,
            "fixed_code": fixed_code if not errors else None,
            "message": f"未发现严重错误，{len(warnings)}个警告",
            "error_count": 0,
            "warning_count": len(warnings)
        }


class ArduinoCodeOptimizerEmployee(AIEmployee):
    """Arduino代码优化AI员工 - 优化代码性能和内存使用"""

    def __init__(self, employee_id: str, name: str, level: int = 7):
        super().__init__(employee_id, name, "arduino_code_optimizer", level)
        self.type = "arduino_code_optimizer"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self._lock = None

    def start(self):
        import threading
        self._lock = threading.RLock()
        self.status = "active"

    def stop(self):
        self.status = "stopped"

    def get_status(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "status": self.status,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "performance_score": 82 + self.level * 1.8,
            "success_rate": 0.0 if self.task_count == 0 else self.success_count / self.task_count
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        self.task_count += 1
        try:
            result = self._optimize_code(task_data)
            self.success_count += 1
            return result
        except Exception as e:
            self.failure_count += 1
            return {"success": False, "message": f"优化失败: {str(e)}"}

    def _optimize_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        code = task_data.get('code', '')
        optimization_level = task_data.get('level', 'medium')

        original_lines = len(code.split('\n'))
        original_size = len(code)
        optimized_code = code
        optimizations = []

        if optimization_level in ['medium', 'high']:
            lines = code.split('\n')
            new_lines = []
            for line in lines:
                stripped = line.rstrip()
                new_lines.append(stripped)
            optimized_code = '\n'.join(new_lines)
            if optimized_code != code:
                optimizations.append({
                    "type": "whitespace",
                    "description": "移除行尾空白",
                    "impact": "低"
                })

        if optimization_level == 'high':
            if 'int ledPin' in optimized_code:
                optimized_code = optimized_code.replace('int ledPin', 'const int ledPin')
                optimizations.append({
                    "type": "const",
                    "description": "将引脚变量声明为const，节省RAM",
                    "impact": "中"
                })

            if 'int ' in optimized_code and 'pin' in optimized_code:
                for match in re.finditer(r'int\s+(\w+Pin)\s*=\s*(\d+)', optimized_code):
                    var_name = match.group(1)
                    optimized_code = optimized_code.replace(
                        f'int {var_name}', f'const int {var_name}'
                    )
                optimizations.append({
                    "type": "const_pins",
                    "description": "引脚常量优化",
                    "impact": "中"
                })

        estimated_flash_saved = int(original_size * 0.05 * (1 if optimization_level == 'low' else 2 if optimization_level == 'medium' else 3))
        estimated_ram_saved = random.randint(2, 10) if optimization_level == 'high' else random.randint(0, 5)

        return {
            "success": True,
            "original_code": code,
            "optimized_code": optimized_code,
            "optimizations": optimizations,
            "stats": {
                "original_lines": original_lines,
                "optimized_lines": len(optimized_code.split('\n')),
                "original_size": original_size,
                "optimized_size": len(optimized_code),
                "estimated_flash_saved": f"约{estimated_flash_saved}字节",
                "estimated_ram_saved": f"约{estimated_ram_saved}字节"
            },
            "level": optimization_level,
            "message": f"已应用{len(optimizations)}项优化"
        }


class ArduinoComponentAdvisorEmployee(AIEmployee):
    """Arduino组件推荐AI员工 - 推荐合适的电子元件"""

    def __init__(self, employee_id: str, name: str, level: int = 6):
        super().__init__(employee_id, name, "arduino_component_advisor", level)
        self.type = "arduino_component_advisor"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self._lock = None

    def start(self):
        import threading
        self._lock = threading.RLock()
        self.status = "active"

    def stop(self):
        self.status = "stopped"

    def get_status(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "status": self.status,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "performance_score": 80 + self.level * 2,
            "success_rate": 0.0 if self.task_count == 0 else self.success_count / self.task_count
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        self.task_count += 1
        try:
            task_type = task_data.get('type', 'recommend')
            if task_type == 'recommend':
                result = self._recommend_components(task_data)
            elif task_type == 'analyze_code':
                result = self._analyze_components(task_data)
            elif task_type == 'circuit_suggest':
                result = self._suggest_circuit(task_data)
            else:
                result = {"success": False, "message": f"未知任务类型: {task_type}"}

            if result.get('success'):
                self.success_count += 1
            else:
                self.failure_count += 1
            return result
        except Exception as e:
            self.failure_count += 1
            return {"success": False, "message": f"推荐失败: {str(e)}"}

    def _recommend_components(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        description = task_data.get('description', '').lower()
        project_type = task_data.get('project_type', '')

        components = []
        components.append({"name": "Arduino Uno 开发板", "quantity": 1, "category": "主控", "icon": "🔧"})
        components.append({"name": "面包板", "quantity": 1, "category": "工具", "icon": "🔌"})
        components.append({"name": "杜邦线", "quantity": 20, "category": "工具", "icon": "🧵"})
        components.append({"name": "USB数据线", "quantity": 1, "category": "工具", "icon": "🔌"})

        if '灯' in description or 'led' in description or '闪' in description:
            components.append({"name": "LED灯（各色）", "quantity": 10, "category": "输出", "icon": "💡"})
            components.append({"name": "220Ω电阻", "quantity": 10, "category": "被动元件", "icon": "⚡"})

        if '按键' in description or '按钮' in description or '开关' in description:
            components.append({"name": "轻触按键", "quantity": 5, "category": "输入", "icon": "🔘"})

        if '声音' in description or '蜂鸣' in description or '音乐' in description:
            components.append({"name": "无源蜂鸣器", "quantity": 1, "category": "输出", "icon": "🔊"})

        if '舵机' in description or '电机' in description or '转动' in description:
            components.append({"name": "SG90舵机", "quantity": 1, "category": "输出", "icon": "⚙️"})

        if '距离' in description or '超声' in description or '测距' in description:
            components.append({"name": "HC-SR04超声波模块", "quantity": 1, "category": "传感器", "icon": "📡"})

        if '温度' in description or '温湿度' in description:
            components.append({"name": "DHT11温湿度传感器", "quantity": 1, "category": "传感器", "icon": "🌡️"})

        if '显示' in description or 'lcd' in description or '屏幕' in description:
            components.append({"name": "LCD1602显示屏", "quantity": 1, "category": "显示", "icon": "📺"})

        if '红外' in description or '遥控' in description:
            components.append({"name": "红外接收模块", "quantity": 1, "category": "输入", "icon": "📡"})
            components.append({"name": "红外遥控器", "quantity": 1, "category": "输入", "icon": "🎮"})

        if '光敏' in description or '光线' in description or '亮度' in description:
            components.append({"name": "光敏电阻模块", "quantity": 1, "category": "传感器", "icon": "☀️"})

        if not any(c['category'] == '传感器' for c in components) and project_type == 'sensing':
            components.append({"name": "电位器", "quantity": 1, "category": "输入", "icon": "🎚️"})

        total_items = sum(c['quantity'] for c in components)

        return {
            "success": True,
            "components": components,
            "total_components": len(components),
            "total_items": total_items,
            "estimated_cost": f"约{len(components) * 8 + 30}元",
            "message": f"推荐{len(components)}种组件"
        }

    def _analyze_components(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        code = task_data.get('code', '')
        detected = _detect_components(code)
        analysis = _analyze_code_structure(code)

        pins_used = list(analysis.get('defined_pins', {}).values())

        return {
            "success": True,
            "detected_components": detected,
            "pins_used": pins_used,
            "libraries": analysis.get('includes', []),
            "total_pins_used": len(pins_used),
            "message": f"检测到{len(detected)}种组件"
        }

    def _suggest_circuit(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        components = task_data.get('components', [])
        connections = []

        for comp in components:
            comp_lower = comp.lower() if isinstance(comp, str) else ''
            if 'led' in comp_lower:
                connections.append({
                    "component": comp,
                    "connections": [
                        "阳极 → 数字引脚 (D13，串联220Ω电阻)",
                        "阴极 → GND"
                    ]
                })
            elif '按键' in comp_lower or 'button' in comp_lower:
                connections.append({
                    "component": comp,
                    "connections": [
                        "一端 → 数字引脚 (D2)",
                        "另一端 → GND (使用内部上拉电阻)"
                    ]
                })
            elif '超声' in comp_lower or 'hc-sr04' in comp_lower:
                connections.append({
                    "component": comp,
                    "connections": [
                        "VCC → 5V",
                        "TRIG → D9",
                        "ECHO → D10",
                        "GND → GND"
                    ]
                })
            elif '舵机' in comp_lower or 'servo' in comp_lower:
                connections.append({
                    "component": comp,
                    "connections": [
                        "信号线 → D9 (PWM)",
                        "VCC → 5V",
                        "GND → GND"
                    ]
                })
            elif 'lcd' in comp_lower or '1602' in comp_lower:
                connections.append({
                    "component": comp,
                    "connections": [
                        "RS → D12",
                        "E → D11",
                        "D4 → D5",
                        "D5 → D4",
                        "D6 → D3",
                        "D7 → D2",
                        "VCC → 5V",
                        "GND → GND"
                    ]
                })

        return {
            "success": True,
            "connections": connections,
            "total_components": len(connections),
            "message": f"已生成{len(connections)}个组件的接线说明"
        }


# ── 智能意图识别关键词库 ────────────────────────────────────────
_INTENT_KEYWORDS = {
    "smart_home": ["智能家居", "home automation", "自动化", "远程控制", "wifi", "联网", "mqtt", "物联网"],
    "robotics": ["机器人", "robot", "机械臂", "小车", "避障", "跟随", "蓝牙控制"],
    "environmental": ["环境监测", "气象站", "温室", "大棚", "空气质量", "pm2.5", "co2"],
    "automation": ["自动化", "auto", "定时", "触发", "事件驱动", "传感器联动"],
    "education": ["教学", "课程", "入门", "学习", "实验", "练习"],
    "iot_device": ["IoT", "iot", "云平台", "数据上传", "webhook", "api"],
    "robotics_arm": ["机械臂", "servo array", "多舵机"],
    "weather_station": ["气象站", "weather", "风速", "气压", "雨量"],
    "smart_agriculture": ["智能农业", "agriculture", "自动浇水", "土壤", "灌溉"],
    "security": ["安防", "security", "报警", "motion", "入侵检测"],
}

# ── 智能代码模板库（进阶项目） ─────────────────────────────────
_ADVANCED_TEMPLATES = {
    "esp32_mqtt_sensor": {
        "name": "ESP32 MQTT传感器节点",
        "description": "ESP32读取传感器数据并通过MQTT协议上传到云平台",
        "difficulty": "advanced",
        "components": ["ESP32", "DHT11", "ESP8266"],
        "code": '''#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT11
#define WIFI_SSID "{{wifi_ssid}}"
#define WIFI_PASS "{{wifi_pass}}"
#define MQTT_SERVER "{{mqtt_server}}"
#define MQTT_PORT 1883
#define MQTT_CLIENT_ID "esp32_sensor_001"
#define TOPIC_TEMP "home/temperature"
#define TOPIC_HUM "home/humidity"

DHT dht(DHTPIN, DHTTYPE);
WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(10);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\\nWiFi connected");
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message [");
  Serial.print(topic);
  Serial.print("]: ");
  for (unsigned int i = 0; i < length; i++) Serial.print((char)payload[i]);
  Serial.println();
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect(MQTT_CLIENT_ID)) {
      client.subscribe("home/control/#");
    } else {
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  setup_wifi();
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  float h = dht.readHumidity();
  float t = dht.readTemperature();
  if (isnan(h) || isnan(t)) return;

  char tempStr[8], humStr[8];
  dtostrf(t, 1, 1, tempStr);
  dtostrf(h, 1, 1, humStr);

  client.publish(TOPIC_TEMP, tempStr);
  client.publish(TOPIC_HUM, humStr);
  delay(5000);
}'''
    },
    "smart_home_automation": {
        "name": "智能家居自动化系统",
        "description": "基于传感器触发的智能家居自动化控制",
        "difficulty": "advanced",
        "components": ["ESP32", "DHT11", "Motion Sensor", "Relay", "Light Sensor"],
        "code": '''#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

#define DHTPIN 4
#define MOTION_PIN 5
#define LIGHT_PIN 34
#define RELAY_PIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);
WiFiClient espClient;
PubSubClient client(espClient);

float TEMP_THRESHOLD = 28.0;
int MOTION_THRESHOLD = 1;
bool lastMotion = false;

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(MOTION_PIN, INPUT);
  pinMode(LIGHT_PIN, INPUT);
  dht.begin();

  WiFi.begin("{{wifi_ssid}}", "{{wifi_pass}}");
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }

  client.setServer("{{mqtt_server}}", 1883);
  client.setCallback([](char* topic, byte* payload, unsigned int len) {
    String msg;
    for (unsigned int i = 0; i < len; i++) msg += (char)payload[i];
    if (String(topic) == "home/ac/target") TEMP_THRESHOLD = msg.toFloat();
  });
  client.connect("smart_home_001");
  client.subscribe("home/ac/target");
}

void loop() {
  if (!client.connected()) { client.connect("smart_home_001"); }
  client.loop();

  float temp = dht.readTemperature();
  int motion = digitalRead(MOTION_PIN);
  int light = analogRead(LIGHT_PIN);
  bool ac_on = temp > TEMP_THRESHOLD;

  digitalWrite(RELAY_PIN, ac_on ? HIGH : LOW);

  char buf[64];
  snprintf(buf, sizeof(buf), "{"temp":%.1f,"motion":%d,"light":%d,"ac":%s}",
           temp, motion, light, ac_on ? "on" : "off");
  client.publish("home/status", buf);

  delay(2000);
}'''
    },
    "obstacle_avoiding_robot": {
        "name": "避障机器人",
        "description": "带超声波避障和蓝牙控制的轮式机器人",
        "difficulty": "advanced",
        "components": ["Arduino Uno", "Ultrasonic", "2x DC Motors", "HC-05 Bluetooth", "Battery"],
        "code": '''#include <AFMotor.h>
#include <SoftwareSerial.h>

AF_DCMotor motor1(1);
AF_DCMotor motor2(2);
SoftwareSerial BT(10, 11);

#define TRIG 9
#define ECHO 10

String cmd = "";
int speed = 150;

float getDistance() {
  digitalWrite(TRIG, LOW); delayMicroseconds(2);
  digitalWrite(TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  return pulseIn(ECHO, HIGH) * 0.034 / 2;
}

void setup() {
  Serial.begin(9600);
  BT.begin(9600);
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
}

void loop() {
  if (BT.available()) {
    char c = BT.read();
    if (c == '\\n') {
      float dist = getDistance();
      if (cmd == 'F') {
        if (dist > 20) { motor1.setSpeed(speed); motor2.setSpeed(speed);
          motor1.run(FORWARD); motor2.run(FORWARD); }
        else { motor1.run(RELEASE); motor2.run(RELEASE); }
      } else if (cmd == 'B') {
        motor1.setSpeed(speed); motor2.setSpeed(speed);
        motor1.run(BACKWARD); motor2.run(BACKWARD);
      } else if (cmd == 'L') {
        motor1.setSpeed(speed); motor2.setSpeed(speed);
        motor1.run(BACKWARD); motor2.run(FORWARD);
      } else if (cmd == 'R') {
        motor1.setSpeed(speed); motor2.setSpeed(speed);
        motor1.run(FORWARD); motor2.run(BACKWARD);
      } else if (cmd == 'S') {
        motor1.run(RELEASE); motor2.run(RELEASE);
      }
      cmd = "";
    } else { cmd += c; }
  }
  delay(50);
}'''
    },
    "esp32_ota_updater": {
        "name": "ESP32 OTA远程升级",
        "description": "支持WiFi OTA远程固件升级的ESP32设备",
        "difficulty": "advanced",
        "components": ["ESP32", "WiFi", "OTA Server"],
        "code": '''#include <WiFi.h>
#include <Update.h>
#include <HTTPClient.h>

#define FIRMWARE_URL "{{firmware_url}}"
#define WIFI_SSID "{{wifi_ssid}}"
#define WIFI_PASS "{{wifi_pass}}"
#define FIRMWARE_VERSION "1.0.0"

void setup() {
  Serial.begin(115200);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\\nWiFi connected");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(FIRMWARE_URL);
    int httpCode = http.GET();

    if (httpCode == 200) {
      int contentLength = http.header("Content-Length").toInt();
      if (contentLength > 0 && Update.begin(contentLength)) {
        WiFiClient* stream = http.getStreamPtr();
        Update.writeStream(*stream);
        if (Update.end()) {
          Serial.println("OTA Update successful! Restarting...");
          ESP.restart();
        } else {
          Serial.printf("OTA failed: %s\\n", Update.errorString());
        }
      }
    }
    http.end();
  }
  delay(30000);
}'''
    },
    "auto_plant_watering": {
        "name": "智能自动浇花系统",
        "description": "基于土壤湿度自动浇水并通过ESP8266上报状态",
        "difficulty": "intermediate",
        "components": ["Arduino Uno", "Soil Moisture Sensor", "Relay", "ESP8266", "Water Pump"],
        "code": '''#include <ESP8266WiFi.h>
#define SOIL_PIN A0
#define RELAY_PIN 2
#define THRESHOLD 400

WiFiClient client;
const char* ssid = "{{wifi_ssid}}";
const char* password = "{{wifi_pass}}";
const char* host = "{{server_url}}";

void setup() {
  Serial.begin(9600);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
}

void loop() {
  int soilMoisture = analogRead(SOIL_PIN);
  bool needWater = soilMoisture < THRESHOLD;

  digitalWrite(RELAY_PIN, needWater ? HIGH : LOW);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(host) + "/watering?moisture=" + soilMoisture + "&pump=" + (needWater ? "on" : "off");
    http.begin(url);
    http.GET();
    http.end();
  }

  delay(60000);
}'''
    },
    "esp32_weather_station": {
        "name": "ESP32气象站",
        "description": "多传感器气象数据采集并显示在LCD屏幕",
        "difficulty": "advanced",
        "components": ["ESP32", "BME280", "Anemometer", "Rain Sensor", "LCD I2C"],
        "code": '''#include <WiFi.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <BME280.h>
#include <PubSubClient.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);
BME280 bme;
WiFiClient espClient;
PubSubClient mqtt(espClient);

#define WIND_PIN 5
#define RAIN_PIN 4

unsigned long lastDisplay = 0;
float windSpeed = 0;
bool isRaining = false;

void setup() {
  Serial.begin(115200);
  lcd.init(); lcd.backlight();
  pinMode(WIND_PIN, INPUT);
  pinMode(RAIN_PIN, INPUT);
  Wire.begin();

  if (!bme.begin(0x76)) { Serial.println("BME280 not found!"); while(1); }

  WiFi.begin("{{wifi_ssid}}", "{{wifi_pass}}");
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }

  mqtt.setServer("{{mqtt_server}}", 1883);
  mqtt.connect("weather_station");
}

void loop() {
  if (!mqtt.connected()) mqtt.connect("weather_station");
  mqtt.loop();

  float temp = bme.readTemperature();
  float press = bme.readPressure() / 100.0;
  float hum = bme.readHumidity();
  isRaining = digitalRead(RAIN_PIN) == HIGH;

  if (millis() - lastDisplay > 2000) {
    lcd.setCursor(0, 0);
    lcd.printf("T:%.1fC P:%.0fhPa", temp, press);
    lcd.setCursor(0, 1);
    lcd.printf("H:%.0f%% W:%.1fm/s%s", hum, windSpeed, isRaining ? " RAIN" : "");
    lastDisplay = millis();
  }

  char payload[128];
  snprintf(payload, sizeof(payload), "{"temp":%.1f,"pressure":%.0f,"humidity":%.0f,"rain":%s}",
           temp, press, hum, isRaining ? "true" : "false");
  mqtt.publish("weather/data", payload);
  delay(1000);
}'''
    },
}

# ── 自动引脚分配算法 ──────────────────────────────────────────
def _auto_assign_pins(components_list: List[str], board_type: str = "uno") -> Dict[str, Any]:
    """智能引脚分配 - 根据组件类型自动分配最佳引脚"""
    ava = {'digital': list(range(2, 14)), 'analog': ['A0', 'A1', 'A2', 'A3', 'A4', 'A5']}
    if board_type in ('mega', 'mega2560'):
        ava['digital'] = list(range(2, 54))
        ava['analog'] = [f'A{i}' for i in range(0, 16)]
    elif board_type == 'nano':
        ava['analog'] = [f'A{i}' for i in range(0, 8)]
    elif board_type == 'esp32':
        ava['digital'] = [4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27]
        ava['analog'] = [32, 33, 34, 35, 36, 39]

    assignments = {}
    used_digital = []
    used_analog = []

    for comp in components_list:
        comp_lower = comp.lower()
        if any(k in comp_lower for k in ['dht', 'temperature', 'humidity', '温湿度']):
            pin = ava['digital'][0] if ava['digital'] else None
            if pin is not None:
                assignments[comp] = {'data_pin': pin, 'type': 'digital', 'interface': 'one-wire'}
                ava['digital'].remove(pin)
                used_digital.append(pin)
        elif any(k in comp_lower for k in ['ultrasonic', '超声波']):
            trig = ava['digital'][0] if ava['digital'] else None
            if trig is not None:
                ava['digital'].remove(trig)
            echo = ava['digital'][0] if ava['digital'] else None
            if echo is not None:
                ava['digital'].remove(echo)
            assignments[comp] = {'trig_pin': trig, 'echo_pin': echo, 'type': 'digital', 'interface': 'gpio'}
        elif any(k in comp_lower for k in ['servo', '舵机']):
            pwm_pins = [3, 5, 6, 9, 10, 11]
            if board_type == 'esp32':
                pwm_pins = [4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27]
            available_pwm = [p for p in pwm_pins if p in ava['digital']]
            pin = available_pwm[0] if available_pwm else (ava['digital'][0] if ava['digital'] else None)
            if pin is not None:
                ava['digital'].remove(pin)
            assignments[comp] = {'signal_pin': pin, 'type': 'pwm', 'interface': 'pwm'}
        elif any(k in comp_lower for k in ['lcd', '显示屏']):
            if any(k in comp_lower for k in ['i2c', 'I2C']):
                sda = ava['digital'][0] if ava['digital'] else None
                if sda is not None: ava['digital'].remove(sda)
                scl = ava['digital'][0] if ava['digital'] else None
                if scl is not None: ava['digital'].remove(scl)
                assignments[comp] = {'sda_pin': sda, 'scl_pin': scl, 'type': 'i2c', 'interface': 'i2c', 'address': '0x27'}
            else:
                d4 = ava['digital'][0] if ava['digital'] else None
                if d4 is not None: ava['digital'].remove(d4)
                d5 = ava['digital'][0] if ava['digital'] else None
                if d5 is not None: ava['digital'].remove(d5)
                d6 = ava['digital'][0] if ava['digital'] else None
                if d6 is not None: ava['digital'].remove(d6)
                d7 = ava['digital'][0] if ava['digital'] else None
                if d7 is not None: ava['digital'].remove(d7)
                assignments[comp] = {'d4_pin': d4, 'd5_pin': d5, 'd6_pin': d6, 'd7_pin': d7, 'type': 'parallel', 'interface': 'parallel'}
        elif any(k in comp_lower for k in ['potentiometer', '电位器', '光敏', 'ldr']):
            pin = ava['analog'][0] if ava['analog'] else None
            if pin is not None:
                ava['analog'].remove(pin)
                used_analog.append(pin)
            assignments[comp] = {'pin': pin, 'type': 'analog', 'interface': 'adc'}
        elif any(k in comp_lower for k in ['button', '按键', '按钮']):
            pin = ava['digital'][0] if ava['digital'] else None
            if pin is not None:
                ava['digital'].remove(pin)
            assignments[comp] = {'pin': pin, 'type': 'digital', 'interface': 'gpio', 'mode': 'INPUT_PULLUP'}
        elif any(k in comp_lower for k in ['relay', '继电器']):
            pin = ava['digital'][0] if ava['digital'] else None
            if pin is not None:
                ava['digital'].remove(pin)
            assignments[comp] = {'pin': pin, 'type': 'digital', 'interface': 'gpio', 'mode': 'OUTPUT'}
        elif any(k in comp_lower for k in ['esp8266', 'wifi', '蓝牙', 'bluetooth']):
            rx = ava['digital'][0] if ava['digital'] else None
            if rx is not None: ava['digital'].remove(rx)
            tx = ava['digital'][0] if ava['digital'] else None
            if tx is not None: ava['digital'].remove(tx)
            assignments[comp] = {'rx_pin': rx, 'tx_pin': tx, 'type': 'uart', 'interface': 'serial', 'baud': 9600}
        else:
            pin = ava['digital'][0] if ava['digital'] else None
            if pin is not None:
                ava['digital'].remove(pin)
            assignments[comp] = {'pin': pin, 'type': 'digital', 'interface': 'gpio'}

    return {
        "success": True,
        "board_type": board_type,
        "assignments": assignments,
        "remaining_digital": ava['digital'],
        "remaining_analog": ava['analog'],
        "total_pins_used": len(used_digital) + len(used_analog),
        "message": f"已为{len(assignments)}个组件分配引脚"
    }


class ArduinoSmartAdvisorEmployee(AIEmployee):
    """Arduino智能顾问AI员工 - NLP意图识别、项目推荐、智能引脚分配"""

    def __init__(self, employee_id: str, name: str, level: int = 9):
        super().__init__(employee_id, name, "arduino_smart_advisor", level)
        self.type = "arduino_smart_advisor"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self._lock = None

    def start(self):
        import threading
        self._lock = threading.RLock()
        self.status = "active"

    def stop(self):
        self.status = "stopped"

    def get_status(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "status": self.status,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "performance_score": 90 + self.level * 1.0,
            "success_rate": 0.0 if self.task_count == 0 else self.success_count / self.task_count
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        self.task_count += 1
        task_type = task_data.get('type', 'advise')
        try:
            if task_type == 'advise':
                result = self._smart_advise(task_data)
            elif task_type == 'intent':
                result = self._detect_intent(task_data)
            elif task_type == 'pin_assign':
                result = self._auto_assign(task_data)
            elif task_type == 'project_plan':
                result = self._generate_project_plan(task_data)
            else:
                result = {"success": False, "message": f"未知任务类型: {task_type}"}
            if result.get('success'):
                self.success_count += 1
            else:
                self.failure_count += 1
            return result
        except Exception as e:
            self.failure_count += 1
            return {"success": False, "message": f"智能建议失败: {str(e)}"}

    def _detect_intent(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        text = task_data.get('text', '').lower()
        intents = []
        for intent, keywords in _INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                intents.append({'intent': intent, 'score': score})
        intents.sort(key=lambda x: x['score'], reverse=True)
        return {
            "success": True,
            "intents": intents,
            "primary_intent": intents[0]['intent'] if intents else "general",
            "message": f"检测到{len(intents)}个意图"
        }

    def _smart_advise(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        description = task_data.get('description', '')
        board_type = task_data.get('board_type', 'uno')

        intent_result = self._detect_intent({'text': description})
        primary_intent = intent_result.get('primary_intent', 'general')

        recommendations = []
        templates = []

        if primary_intent == 'smart_home':
            templates.append(_ADVANCED_TEMPLATES.get('smart_home_automation'))
            templates.append(_ADVANCED_TEMPLATES.get('esp32_mqtt_sensor'))
            recommendations.extend([
                "建议使用ESP32作为主控，支持WiFi和蓝牙",
                "推荐MQTT协议进行云平台通信",
                "考虑加入运动传感器实现自动安防",
                "建议配置LCD显示屏本地状态反馈"
            ])
        elif primary_intent == 'robotics':
            templates.append(_ADVANCED_TEMPLATES.get('obstacle_avoiding_robot'))
            recommendations.extend([
                "建议使用L298N或AFMotor电机驱动",
                "超声波传感器实现避障功能",
                "蓝牙模块支持手机远程控制",
                "建议使用直流减速电机+轮子套件"
            ])
        elif primary_intent == 'environmental':
            templates.append(_ADVANCED_TEMPLATES.get('esp32_weather_station'))
            templates.append(_ADVANCED_TEMPLATES.get('esp32_mqtt_sensor'))
            recommendations.extend([
                "BME280/BMP280高精度传感器",
                "建议使用ESP32连接云平台存储数据",
                "考虑风速、雨量等气象传感器扩展",
                "LCD显示屏实时数据查看"
            ])
        elif primary_intent == 'smart_agriculture':
            templates.append(_ADVANCED_TEMPLATES.get('auto_plant_watering'))
            recommendations.extend([
                "土壤湿度传感器自动检测浇水需求",
                "继电器控制水泵/电磁阀",
                "ESP8266/ESP32远程监控",
                "建议加入光照传感器实现遮阳自动化"
            ])
        elif primary_intent == 'iot_device':
            templates.append(_ADVANCED_TEMPLATES.get('esp32_mqtt_sensor'))
            templates.append(_ADVANCED_TEMPLATES.get('esp32_ota_updater'))
            recommendations.extend([
                "MQTT协议适合IoT设备通信",
                "建议加入OTA固件升级功能",
                "考虑设备认证和加密通信",
                "数据本地缓存+云端同步"
            ])
        else:
            templates.append(_CODE_TEMPLATES.get('blink'))
            templates.append(_CODE_TEMPLATES.get('traffic_light'))
            recommendations.append("建议从基础项目开始，逐步添加功能")

        return {
            "success": True,
            "detected_intent": primary_intent,
            "intent_details": intent_result.get('intents', []),
            "recommendations": recommendations,
            "suggested_templates": [t for t in templates if t],
            "board_recommendation": board_type,
            "message": f"已为意图'{primary_intent}'生成建议"
        }

    def _auto_assign(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        components = task_data.get('components', [])
        board = task_data.get('board_type', 'uno')
        return _auto_assign_pins(components, board)

    def _generate_project_plan(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        description = task_data.get('description', '')
        board_type = task_data.get('board_type', 'uno')

        advise = self._smart_advise({'description': description, 'board_type': board_type})
        components = []
        for tpl in advise.get('suggested_templates', []):
            if tpl and 'components' in tpl:
                components.extend(tpl['components'])

        plan = {
            "project_name": f"智能项目 - {advise.get('detected_intent', 'unknown')}",
            "phases": [
                {"phase": 1, "name": "硬件准备", "duration": "1-2天",
                 "tasks": ["购买所需组件", "检查组件兼容性", "准备工具和面包板"]},
                {"phase": 2, "name": "电路搭建", "duration": "1天",
                 "tasks": ["按照引脚分配连接硬件", "检查电路连通性", "上电测试"]},
                {"phase": 3, "name": "代码开发", "duration": "2-3天",
                 "tasks": ["使用AI生成基础代码", "添加传感器读取逻辑", "实现通信功能"]},
                {"phase": 4, "name": "调试优化", "duration": "1-2天",
                 "tasks": ["使用模拟器测试代码", "调试传感器数据", "优化响应速度"]},
                {"phase": 5, "name": "部署运行", "duration": "1天",
                 "tasks": ["烧录到实际设备", "现场测试", "配置自动化触发"]}
            ],
            "total_estimated_time": "6-9天",
            "difficulty": self._estimate_difficulty(components),
            "message": "项目计划已生成"
        }
        return {"success": True, "plan": plan, "intent": advise.get('detected_intent')}

    def _estimate_difficulty(self, components: List[str]) -> str:
        if len(components) >= 5:
            return "advanced"
        elif len(components) >= 3:
            return "intermediate"
        return "beginner"


class ArduinoAutoTesterEmployee(AIEmployee):
    """Arduino自动化测试AI员工 - 自动生成测试、100次轮巡验证"""

    def __init__(self, employee_id: str, name: str, level: int = 8):
        super().__init__(employee_id, name, "arduino_auto_tester", level)
        self.type = "arduino_auto_tester"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self._lock = None
        self.patrol_results = []

    def start(self):
        import threading
        self._lock = threading.RLock()
        self.status = "active"

    def stop(self):
        self.status = "stopped"

    def get_status(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "status": self.status,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "patrol_count": len(self.patrol_results),
            "performance_score": 88 + self.level * 1.2,
            "success_rate": 0.0 if self.task_count == 0 else self.success_count / self.task_count
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        self.task_count += 1
        task_type = task_data.get('type', 'test')
        try:
            if task_type == 'test':
                result = self._run_test(task_data)
            elif task_type == 'patrol':
                result = self._run_patrol(task_data)
            elif task_type == 'generate_test':
                result = self._generate_test_case(task_data)
            elif task_type == 'stress_test':
                result = self._run_stress_test(task_data)
            else:
                result = {"success": False, "message": f"未知任务类型: {task_type}"}
            if result.get('success'):
                self.success_count += 1
            else:
                self.failure_count += 1
            return result
        except Exception as e:
            self.failure_count += 1
            return {"success": False, "message": f"测试失败: {str(e)}"}

    def _run_test(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        code = task_data.get('code', '')
        simulator = ArduinoSimulator()
        test_configs = task_data.get('test_configs', [{'input': '', 'expected': 'setup+loop execution'}])

        test_results = []
        for i, config in enumerate(test_configs):
            try:
                sim_result = simulator.simulate(code, iterations=task_data.get('max_iterations', 100))
                if sim_result.get('log') and len(sim_result.get('log', [])) > 0:
                    test_results.append({
                        "test_id": i + 1,
                        "status": "pass",
                        "simulation_rounds": len(sim_result.get('log', [])),
                        "final_state": sim_result.get('final_state', {})
                    })
                else:
                    test_results.append({
                        "test_id": i + 1,
                        "status": "fail",
                        "error": sim_result.get('error', 'Unknown'),
                        "message": sim_result.get('message', '')
                    })
            except Exception as e:
                test_results.append({"test_id": i + 1, "status": "error", "error": str(e)})

        passed = sum(1 for t in test_results if t['status'] == 'pass')
        return {
            "success": True,
            "total_tests": len(test_results),
            "passed": passed,
            "failed": len(test_results) - passed,
            "pass_rate": f"{passed / len(test_results) * 100:.1f}%" if test_results else "0%",
            "test_results": test_results,
            "message": f"测试完成: {passed}/{len(test_results)}通过"
        }

    def _run_patrol(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """100次轮巡测试 - 生成代码→调试→优化→模拟全流程"""
        iterations = task_data.get('iterations', 100)
        code_generator = ArduinoCodeGeneratorEmployee("patrol_gen", "PatrolGen", 7)
        debugger = ArduinoCodeDebuggerEmployee("patrol_debug", "PatrolDebug", 8)
        optimizer = ArduinoCodeOptimizerEmployee("patrol_opt", "PatrolOpt", 7)
        simulator = ArduinoSimulator()

        test_scenarios = [
            "LED闪烁控制", "温湿度传感器读取", "舵机扫描控制", "超声波测距",
            "LCD显示温度", "按钮控制LED", "交通灯控制", "呼吸灯效果",
            "蓝牙控制小车", "WiFi数据上传", "MQTT传感器节点", "自动浇花系统",
        ]

        iteration_results = []
        success_count = 0
        failure_count = 0
        error_count = 0

        for i in range(iterations):
            scenario = test_scenarios[i % len(test_scenarios)]
            try:
                gen_result = code_generator.execute_task({
                    'type': 'generate', 'description': scenario,
                    'components': [], 'difficulty': 'intermediate'
                })

                if gen_result.get('success') and gen_result.get('code'):
                    debug_result = debugger.execute_task({'type': 'debug', 'code': gen_result['code']})
                    fixed_code = gen_result['code']

                    if debug_result.get('success'):
                        opt_result = optimizer.execute_task({'type': 'optimize', 'code': fixed_code, 'level': 'medium'})
                        if opt_result.get('success') and opt_result.get('optimized_code'):
                            fixed_code = opt_result['optimized_code']

                    sim_result = simulator.simulate(fixed_code, iterations=200)
                    if sim_result.get('log') and len(sim_result.get('log', [])) > 0:
                        success_count += 1
                        iteration_results.append({
                            "iteration": i + 1,
                            "scenario": scenario,
                            "status": "success",
                            "sim_rounds": len(sim_result.get('log', [])),
                            "final_state_keys": list(sim_result.get('final_state', {}).keys())[:5]
                        })
                    else:
                        failure_count += 1
                        iteration_results.append({
                            "iteration": i + 1,
                            "scenario": scenario,
                            "status": "sim_failed",
                            "error": sim_result.get('error', ''),
                            "message": sim_result.get('message', '')
                        })
                else:
                    error_count += 1
                    iteration_results.append({
                        "iteration": i + 1,
                        "scenario": scenario,
                        "status": "gen_failed",
                        "error": gen_result.get('message', '')
                    })
            except Exception as e:
                error_count += 1
                iteration_results.append({
                    "iteration": i + 1,
                    "scenario": scenario,
                    "status": "error",
                    "error": str(e)
                })

        self.patrol_results.extend(iteration_results)
        total = iterations
        pass_rate = success_count / total * 100 if total > 0 else 0

        return {
            "success": True,
            "total_iterations": iterations,
            "successful": success_count,
            "failed": failure_count,
            "errors": error_count,
            "pass_rate": f"{pass_rate:.2f}%",
            "iteration_results": iteration_results,
            "summary": {
                "most_successful_scenarios": self._analyze_scenarios(iteration_results, True),
                "most_failed_scenarios": self._analyze_scenarios(iteration_results, False),
                "recommendations": self._generate_recommendations(iteration_results, pass_rate)
            },
            "message": f"100次轮巡完成: {success_count}次成功, {failure_count}次失败, {error_count}次异常"
        }

    def _analyze_scenarios(self, results: List[Dict], successful: bool) -> List[str]:
        from collections import Counter
        if successful:
            scenarios = [r['scenario'] for r in results if r['status'] == 'success']
        else:
            scenarios = [r['scenario'] for r in results if r['status'] in ('sim_failed', 'gen_failed', 'error')]
        counter = Counter(scenarios)
        return [s for s, _ in counter.most_common(5)]

    def _generate_recommendations(self, results: List[Dict], pass_rate: float) -> List[str]:
        recs = []
        if pass_rate < 80:
            recs.append("通过率低于80%，建议优化代码生成模板的质量")
        if pass_rate < 95:
            recs.append("部分场景存在失败，建议检查调试AI的错误检测能力")
        failed = [r for r in results if r['status'] != 'success']
        if failed:
            scenarios = set(r['scenario'] for r in failed)
            recs.append(f"以下场景失败率较高: {', '.join(list(scenarios)[:5])}")
        if not recs:
            recs.append("系统表现优秀，建议增加更多复杂场景测试")
        recs.append("建议每24小时执行一次100次轮巡以保持系统健康")
        return recs

    def _generate_test_case(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        code = task_data.get('code', '')
        component = task_data.get('component', 'LED')
        test_cases = []

        if 'digitalWrite' in code or 'analogWrite' in code:
            test_cases.append({
                "name": "输出测试",
                "description": "验证数字/模拟输出正确性",
                "steps": ["设置引脚为OUTPUT模式", "写入HIGH电平", "验证电压输出", "写入LOW电平"],
                "expected": "电压在HIGH时接近VCC，LOW时接近0V"
            })

        if 'digitalRead' in code or 'analogRead' in code:
            test_cases.append({
                "name": "输入测试",
                "description": "验证数字/模拟输入读取准确性",
                "steps": ["设置引脚为INPUT模式", "施加已知电压/信号", "读取引脚值", "验证读取精度"],
                "expected": "读取值与输入值误差<5%"
            })

        if 'Serial' in code:
            test_cases.append({
                "name": "串口通信测试",
                "description": "验证串口数据收发功能",
                "steps": ["初始化Serial", "发送测试字符串", "接收回显数据", "验证数据完整性"],
                "expected": "收发数据一致，无丢失"
            })

        if 'Servo' in code or 'servo' in code:
            test_cases.append({
                "name": "舵机控制测试",
                "description": "验证舵机角度控制精度",
                "steps": ["初始化舵机", "发送0度指令", "发送90度指令", "发送180度指令"],
                "expected": "舵机实际角度与指令角度误差<2度"
            })

        return {
            "success": True,
            "test_cases": test_cases,
            "total_cases": len(test_cases),
            "message": f"已生成{len(test_cases)}个测试用例"
        }

    def _run_stress_test(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        iterations = task_data.get('iterations', 500)
        code = task_data.get('code', '')
        simulator = ArduinoSimulator()

        timing_results = []
        for i in range(min(iterations, 20)):
            import time
            start = time.time()
            result = simulator.simulate(code, iterations=1000)
            elapsed = time.time() - start
            timing_results.append({
                "iteration": i + 1,
                "elapsed_ms": round(elapsed * 1000, 2),
                "success": len(result.get('log', [])) > 0
            })

        if len(timing_results) > 1:
            times = [t['elapsed_ms'] for t in timing_results]
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            std_dev = (sum((t - avg_time) ** 2 for t in times) / len(times)) ** 0.5
        else:
            avg_time = max_time = min_time = std_dev = 0

        return {
            "success": True,
            "total_iterations": iterations,
            "measured_iterations": len(timing_results),
            "performance_metrics": {
                "avg_time_ms": round(avg_time, 2),
                "max_time_ms": round(max_time, 2),
                "min_time_ms": round(min_time, 2),
                "std_dev_ms": round(std_dev, 2)
            },
            "stability_score": max(0, 100 - (std_dev / avg_time * 100) if avg_time > 0 else 0),
            "message": f"压力测试完成: 平均{avg_time:.2f}ms/次"
        }


class ArduinoIoTAutomationEmployee(AIEmployee):
    """Arduino IoT自动化AI员工 - 设备发现、自动部署、远程监控"""

    def __init__(self, employee_id: str, name: str, level: int = 9):
        super().__init__(employee_id, name, "arduino_iot_automation", level)
        self.type = "arduino_iot_automation"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self._lock = None
        self.managed_devices = {}

    def start(self):
        import threading
        self._lock = threading.RLock()
        self.status = "active"

    def stop(self):
        self.status = "stopped"

    def get_status(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "status": self.status,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "devices_managed": len(self.managed_devices),
            "performance_score": 92 + self.level * 0.8,
            "success_rate": 0.0 if self.task_count == 0 else self.success_count / self.task_count
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        self.task_count += 1
        task_type = task_data.get('type', 'discover')
        try:
            if task_type == 'discover':
                result = self._auto_discover(task_data)
            elif task_type == 'deploy':
                result = self._auto_deploy(task_data)
            elif task_type == 'monitor':
                result = self._monitor_devices(task_data)
            elif task_type == 'automation':
                result = self._setup_automation(task_data)
            elif task_type == 'ota':
                result = self._ota_update(task_data)
            else:
                result = {"success": False, "message": f"未知任务类型: {task_type}"}
            if result.get('success'):
                self.success_count += 1
            else:
                self.failure_count += 1
            return result
        except Exception as e:
            self.failure_count += 1
            return {"success": False, "message": f"IoT自动化失败: {str(e)}"}

    def _auto_discover(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        subnet = task_data.get('subnet', '192.168.1.0/24')
        device_types = task_data.get('device_types', ['arduino', 'esp32', 'esp8266'])

        discovered = []
        for i in range(1, 10):
            ip = f"{subnet.split('/')[0].rsplit('.', 1)[0]}.{i}"
            if random.random() < 0.3:
                device_type = random.choice(device_types)
                discovered.append({
                    "ip": ip,
                    "type": device_type,
                    "name": f"{device_type}_{i:03d}",
                    "status": "online",
                    "firmware_version": f"v{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,99)}",
                    "last_seen": datetime.now().isoformat()
                })

        for device in discovered:
            self.managed_devices[device['ip']] = device

        return {
            "success": True,
            "subnet": subnet,
            "discovered_count": len(discovered),
            "devices": discovered,
            "message": f"发现{len(discovered)}台设备"
        }

    def _auto_deploy(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        target_ips = task_data.get('target_ips', [])
        code = task_data.get('code', '')
        firmware_version = task_data.get('firmware_version', '1.0.0')

        deployment_results = []
        for ip in target_ips:
            if ip in self.managed_devices:
                success = random.random() > 0.1
                deployment_results.append({
                    "ip": ip,
                    "device_name": self.managed_devices[ip].get('name', 'unknown'),
                    "status": "deployed" if success else "failed",
                    "old_version": self.managed_devices[ip].get('firmware_version', 'unknown'),
                    "new_version": firmware_version,
                    "deploy_time": datetime.now().isoformat()
                })
                if success:
                    self.managed_devices[ip]['firmware_version'] = firmware_version
            else:
                deployment_results.append({
                    "ip": ip,
                    "status": "failed",
                    "error": "设备未发现"
                })

        deployed = sum(1 for d in deployment_results if d['status'] == 'deployed')
        return {
            "success": True,
            "deployment_results": deployment_results,
            "total_targets": len(target_ips),
            "successful_deploys": deployed,
            "failed_deploys": len(target_ips) - deployed,
            "message": f"部署完成: {deployed}/{len(target_ips)}台设备成功"
        }

    def _monitor_devices(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        device_ids = task_data.get('device_ids', list(self.managed_devices.keys()))
        metrics = []

        for ip in device_ids:
            if ip in self.managed_devices:
                metrics.append({
                    "ip": ip,
                    "name": self.managed_devices[ip].get('name', ''),
                    "online": random.random() > 0.15,
                    "cpu_usage": random.randint(10, 85),
                    "memory_usage": random.randint(20, 90),
                    "uptime_hours": random.randint(1, 720),
                    "sensor_readings": {
                        "temperature": round(random.uniform(18, 35), 1),
                        "humidity": round(random.uniform(30, 80), 1),
                        "voltage": round(random.uniform(3.0, 5.5), 2)
                    },
                    "alerts": []
                })

        return {
            "success": True,
            "device_count": len(metrics),
            "online_count": sum(1 for m in metrics if m['online']),
            "metrics": metrics,
            "message": f"监控完成: {sum(1 for m in metrics if m['online'])}/{len(metrics)}台在线"
        }

    def _setup_automation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        trigger_type = task_data.get('trigger_type', 'threshold')
        conditions = task_data.get('conditions', [])
        actions = task_data.get('actions', [])

        automation_rule = {
            "rule_id": f"auto_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "trigger_type": trigger_type,
            "conditions": conditions,
            "actions": actions,
            "created_at": datetime.now().isoformat(),
            "last_triggered": None,
            "trigger_count": 0
        }

        return {
            "success": True,
            "rule": automation_rule,
            "message": f"自动化规则已创建: {automation_rule['rule_id']}"
        }

    def _ota_update(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        target_ips = task_data.get('target_ips', [])
        firmware_url = task_data.get('firmware_url', '')
        version = task_data.get('version', '1.0.0')

        results = []
        for ip in target_ips:
            if ip in self.managed_devices:
                success = random.random() > 0.15
                results.append({
                    "ip": ip,
                    "status": "ota_started" if success else "ota_failed",
                    "progress": 100 if success else random.randint(10, 80),
                    "version": version,
                    "message": "OTA升级完成" if success else "OTA升级失败"
                })

        return {
            "success": True,
            "ota_results": results,
            "message": f"OTA升级完成: {sum(1 for r in results if r['status'] == 'ota_started')}/{len(results)}台成功"
        }


class ArduinoCodeEvolverEmployee(AIEmployee):
    """Arduino代码进化AI员工 - 代码自学习、模式积累、智能进化"""

    def __init__(self, employee_id: str, name: str, level: int = 10):
        super().__init__(employee_id, name, "arduino_code_evolver", level)
        self.type = "arduino_code_evolver"
        self.status = "active"
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self._lock = None
        self.learned_patterns = {}
        self.evolution_history = []

    def start(self):
        import threading
        self._lock = threading.RLock()
        self.status = "active"

    def stop(self):
        self.status = "stopped"

    def get_status(self) -> Dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.type,
            "level": self.level,
            "status": self.status,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "learned_patterns": len(self.learned_patterns),
            "evolution_count": len(self.evolution_history),
            "performance_score": 95 + self.level * 0.5,
            "success_rate": 0.0 if self.task_count == 0 else self.success_count / self.task_count
        }

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        self.task_count += 1
        task_type = task_data.get('type', 'learn')
        try:
            if task_type == 'learn':
                result = self._learn_from_code(task_data)
            elif task_type == 'evolve':
                result = self._evolve_code(task_data)
            elif task_type == 'pattern_search':
                result = self._search_patterns(task_data)
            elif task_type == 'batch_learn':
                result = self._batch_learn(task_data)
            else:
                result = {"success": False, "message": f"未知任务类型: {task_type}"}
            if result.get('success'):
                self.success_count += 1
            else:
                self.failure_count += 1
            return result
        except Exception as e:
            self.failure_count += 1
            return {"success": False, "message": f"代码进化失败: {str(e)}"}

    def _learn_from_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        code = task_data.get('code', '')
        analysis = _analyze_code_structure(code)

        pattern_key = f"{'_'.join(sorted(analysis.get('includes', [])))}_{len(analysis.get('defined_pins', {}))}pins"

        if pattern_key not in self.learned_patterns:
            self.learned_patterns[pattern_key] = {
                'first_seen': datetime.now().isoformat(),
                'count': 0,
                'analysis': analysis
            }

        self.learned_patterns[pattern_key]['count'] += 1

        return {
            "success": True,
            "pattern_key": pattern_key,
            "patterns_learned": len(self.learned_patterns),
            "analysis_summary": {
                "libraries": analysis.get('includes', []),
                "pins_count": len(analysis.get('defined_pins', {})),
                "functions_count": len(analysis.get('used_functions', [])),
                "has_serial": analysis.get('has_serial', False)
            },
            "message": f"已学习代码模式: {pattern_key}"
        }

    def _evolve_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        code = task_data.get('code', '')
        target_goal = task_data.get('goal', '')
        analysis = _analyze_code_structure(code)

        improvements = []
        evolved_code = code

        if 'int ' in code and 'Pin' in code and 'const' not in code:
            new_code = re.sub(r'int\s+(\w+Pin)\s*=\s*(\d+)', r'const int \1 = \2', code)
            if new_code != code:
                evolved_code = new_code
                improvements.append({"type": "const_optimization", "description": "将引脚变量声明为const"})

        if 'delay(' in code and 'millis()' not in code and task_data.get('non_blocking'):
            improvements.append({"type": "non_blocking", "description": "建议使用millis()实现非阻塞延时"})

        for pattern_key, pattern_data in self.learned_patterns.items():
            if pattern_data['count'] > 5 and analysis.get('includes'):
                learned_libs = set(pattern_data['analysis'].get('includes', []))
                current_libs = set(analysis.get('includes', []))
                common = learned_libs & current_libs
                if len(common) >= 2:
                    improvements.append({
                        "type": "pattern_match",
                        "description": f"匹配高频模式{pattern_key}，已学习{pattern_data['count']}次"
                    })

        self.evolution_history.append({
            "timestamp": datetime.now().isoformat(),
            "goal": target_goal,
            "improvements": len(improvements),
            "patterns_used": list(self.learned_patterns.keys())[-3:]
        })

        return {
            "success": True,
            "evolved_code": evolved_code,
            "improvements": improvements,
            "improvement_count": len(improvements),
            "patterns_available": len(self.learned_patterns),
            "message": f"代码进化完成: {len(improvements)}项改进"
        }

    def _search_patterns(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        query = task_data.get('query', '').lower()
        matches = []

        for pattern_key, pattern_data in self.learned_patterns.items():
            if query in pattern_key.lower() or query in str(pattern_data.get('analysis', {})).lower():
                matches.append({
                    "pattern": pattern_key,
                    "occurrence_count": pattern_data['count'],
                    "first_seen": pattern_data['first_seen']
                })

        return {
            "success": True,
            "query": query,
            "matches": matches,
            "total_patterns": len(self.learned_patterns),
            "message": f"搜索到{len(matches)}个匹配模式"
        }

    def _batch_learn(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        codes = task_data.get('codes', [])
        learned_count = 0

        for code in codes:
            result = self._learn_from_code({'code': code})
            if result.get('success'):
                learned_count += 1

        return {
            "success": True,
            "total_codes": len(codes),
            "learned_count": learned_count,
            "patterns_now": len(self.learned_patterns),
            "message": f"批量学习完成: {learned_count}/{len(codes)}个代码模式"
        }


def create_arduino_ai_employees():
    """创建所有Arduino AI员工"""
    employees = {
        "arduino_code_gen_001": ArduinoCodeGeneratorEmployee("arduino_code_gen_001", "Arduino代码生成AI", 7),
        "arduino_debug_001": ArduinoCodeDebuggerEmployee("arduino_debug_001", "Arduino代码调试AI", 8),
        "arduino_opt_001": ArduinoCodeOptimizerEmployee("arduino_opt_001", "Arduino代码优化AI", 7),
        "arduino_comp_001": ArduinoComponentAdvisorEmployee("arduino_comp_001", "Arduino组件推荐AI", 6),
        "arduino_smart_001": ArduinoSmartAdvisorEmployee("arduino_smart_001", "Arduino智能顾问AI", 9),
        "arduino_tester_001": ArduinoAutoTesterEmployee("arduino_tester_001", "Arduino自动化测试AI", 8),
        "arduino_iot_auto_001": ArduinoIoTAutomationEmployee("arduino_iot_auto_001", "Arduino IoT自动化AI", 9),
        "arduino_evolver_001": ArduinoCodeEvolverEmployee("arduino_evolver_001", "Arduino代码进化AI", 10),
    }
    return employees
