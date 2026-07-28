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


def create_arduino_ai_employees():
    """创建所有Arduino AI员工"""
    employees = {
        "arduino_code_gen_001": ArduinoCodeGeneratorEmployee("arduino_code_gen_001", "Arduino代码生成AI", 7),
        "arduino_debug_001": ArduinoCodeDebuggerEmployee("arduino_debug_001", "Arduino代码调试AI", 8),
        "arduino_opt_001": ArduinoCodeOptimizerEmployee("arduino_opt_001", "Arduino代码优化AI", 7),
        "arduino_comp_001": ArduinoComponentAdvisorEmployee("arduino_comp_001", "Arduino组件推荐AI", 6),
    }
    return employees
