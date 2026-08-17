#!/usr/bin/env python3
import re
import os

_CODE_PATTERNS = {
    r'#include\s*<(\w+)\\.h>': {
        'category': 'include',
        'description': '引入{0}库',
        'detail': '加载{0}库，提供{0}功能',
        'library_info': {
            'DHT': '传感器',
            'Servo': '舵机控制',
            'LiquidCrystal': 'LCD显示',
            'Wire': 'I2C通信',
            'LiquidCrystal_I2C': 'I2C LCD显示',
            'ESP8266WiFi': 'WiFi通信',
            'EEPROM': '数据存储'
        }
    },
    r'#define\s+(\w+)\s+(.+)': {
        'category': 'define',
        'description': '定义常量{0} = {1}',
        'detail': '将{0}设置为{1}，方便后续使用'
    },
    r'int\s+(\w+)\s*=\s*(\d+|A\d+)': {
        'category': 'variable',
        'description': '定义整数变量{0} = {1}',
        'detail': '创建一个名为{0}的整数变量，初始值为{1}'
    },
    r'float\s+(\w+)\s*=\s*([\d.]+)': {
        'category': 'variable',
        'description': '定义浮点变量{0} = {1}',
        'detail': '创建一个名为{0}的浮点数变量，初始值为{1}'
    },
    r'void\s+setup\s*\(\s*\)': {
        'category': 'function',
        'description': 'setup()函数 - 初始化代码',
        'detail': 'setup函数在程序开始时执行一次，用于初始化引脚、串口、传感器等'
    },
    r'void\s+loop\s*\(\s*\)': {
        'category': 'function',
        'description': 'loop()函数 - 主循环代码',
        'detail': 'loop函数在setup执行后无限循环执行，包含程序的主要逻辑'
    },
    r'pinMode\s*\(\s*(\w+)\s*,\s*(INPUT|OUTPUT|INPUT_PULLUP)\s*\)': {
        'category': 'io',
        'description': '设置引脚{0}为{1}模式',
        'detail': {
            'INPUT': '将{0}引脚设置为输入模式，用于读取传感器数据或按钮状态',
            'OUTPUT': '将{0}引脚设置为输出模式，用于控制LED、电机等设备',
            'INPUT_PULLUP': '将{0}引脚设置为带内部上拉电阻的输入模式，无需外部上拉电阻'
        }
    },
    r'digitalWrite\s*\(\s*(\w+)\s*,\s*(HIGH|LOW)\s*\)': {
        'category': 'io',
        'description': '向引脚{0}写入{1}',
        'detail': {
            'HIGH': '将{0}引脚设置为高电平（约5V），点亮LED或开启设备',
            'LOW': '将{0}引脚设置为低电平（约0V），熄灭LED或关闭设备'
        }
    },
    r'digitalRead\s*\(\s*(\w+)\s*\)': {
        'category': 'io',
        'description': '读取引脚{0}的数字值',
        'detail': '读取{0}引脚的数字状态，返回HIGH(1)或LOW(0)'
    },
    r'analogWrite\s*\(\s*(\w+)\s*,\s*(\d+)\s*\)': {
        'category': 'io',
        'description': '向引脚{0}写入PWM值{1}',
        'detail': '通过PWM技术控制{0}引脚的输出强度，值范围0-255，0为关，255为全开'
    },
    r'analogRead\s*\(\s*(\w+)\s*\)': {
        'category': 'io',
        'description': '读取引脚{0}的模拟值',
        'detail': '读取{0}模拟引脚的电压值，返回0-1023（对应0-5V）'
    },
    r'Serial\.begin\s*\(\s*(\d+)\s*\)': {
        'category': 'serial',
        'description': '初始化串口通信，波特率{0}',
        'detail': '设置串口通信速率为{0}波特，用于与电脑或其他设备通信'
    },
    r'Serial\.print\s*\(\s*(.+?)\s*\)': {
        'category': 'serial',
        'description': '串口输出{0}',
        'detail': '通过串口发送{0}，不换行'
    },
    r'Serial\.println\s*\(\s*(.+?)\s*\)': {
        'category': 'serial',
        'description': '串口输出{0}并换行',
        'detail': '通过串口发送{0}，发送完成后自动换行'
    },
    r'delay\s*\(\s*(\d+)\s*\)': {
        'category': 'timing',
        'description': '延时{0}毫秒',
        'detail': '暂停程序执行{0}毫秒（1秒=1000毫秒）'
    },
    r'delayMicroseconds\s*\(\s*(\d+)\s*\)': {
        'category': 'timing',
        'description': '延时{0}微秒',
        'detail': '暂停程序执行{0}微秒（1毫秒=1000微秒）'
    },
    r'millis\s*\(\s*\)': {
        'category': 'timing',
        'description': '获取系统运行时间',
        'detail': '返回程序启动以来的毫秒数，用于非阻塞延时'
    },
    r'for\s*\(\s*int\s+(\w+)\s*=\s*(\d+)\s*;\s*\w+\s*(<|>|<=|>=)\s*(\d+)\s*;\s*\w+\s*([+-]+=)\s*(\d+)\s*\)': {
        'category': 'loop',
        'description': 'for循环：{0}从{1}到{3}，步长{5}',
        'detail': '创建一个循环，变量{0}从{1}开始，每次增加{5}，直到{2} {3}'
    },
    r'if\s*\(\s*([^)]+)\s*\)': {
        'category': 'condition',
        'description': '条件判断：如果{0}',
        'detail': '当条件{0}成立时，执行后面的代码块'
    },
    r'else': {
        'category': 'condition',
        'description': '否则',
        'detail': '当if条件不成立时，执行else后的代码块'
    },
    r'map\s*\(\s*(\w+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)': {
        'category': 'math',
        'description': '将{0}从范围{1}-{2}映射到{3}-{4}',
        'detail': '将变量{0}的值从{1}-{2}的范围线性转换到{3}-{4}的范围'
    },
    r'Servo\s+(\w+)': {
        'category': 'servo',
        'description': '创建舵机对象{0}',
        'detail': '创建一个名为{0}的Servo对象，用于控制舵机'
    },
    r'\.attach\s*\(\s*(\w+)\s*\)': {
        'category': 'servo',
        'description': '将舵机连接到引脚{0}',
        'detail': '将舵机连接到指定的{0}引脚，开始控制舵机'
    },
    r'\.write\s*\(\s*(\d+)\s*\)': {
        'category': 'servo',
        'description': '设置舵机角度为{0}度',
        'detail': '控制舵机转到{0}度位置（0-180度）'
    },
    r'DHT\s+(\w+)\s*\(\s*\w+\s*,\s*\w+\s*\)': {
        'category': 'sensor',
        'description': '创建DHT传感器对象{0}',
        'detail': '创建一个DHT传感器对象，用于读取温湿度数据'
    },
    r'\.begin\s*\(\s*\)': {
        'category': 'sensor',
        'description': '初始化传感器',
        'detail': '初始化传感器，准备开始读取数据'
    },
    r'\.readHumidity\s*\(\s*\)': {
        'category': 'sensor',
        'description': '读取湿度值',
        'detail': '从DHT传感器读取当前环境湿度百分比'
    },
    r'\.readTemperature\s*\(\s*\)': {
        'category': 'sensor',
        'description': '读取温度值',
        'detail': '从DHT传感器读取当前环境温度（摄氏度）'
    },
    r'LiquidCrystal\s+(\w+)\s*\(\s*[\d,\s]+\s*\)': {
        'category': 'display',
        'description': '创建LCD对象{0}',
        'detail': '创建一个LCD显示屏对象，用于显示文本信息'
    },
    r'\.print\s*\(\s*(.+?)\s*\)': {
        'category': 'display',
        'description': '在显示屏输出{0}',
        'detail': '在LCD屏幕上显示{0}内容'
    },
    r'\.setCursor\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)': {
        'category': 'display',
        'description': '设置光标位置到第{1}行第{0}列',
        'detail': '将LCD显示光标移动到第{1}行第{0}列的位置'
    },
    r'\.init\s*\(\s*\)': {
        'category': 'display',
        'description': '初始化LCD',
        'detail': '初始化I2C LCD显示屏'
    },
    r'\.backlight\s*\(\s*\)': {
        'category': 'display',
        'description': '开启LCD背光',
        'detail': '点亮LCD显示屏的背光'
    },
    r'WiFi\.begin\s*\(\s*[^)]+\s*\)': {
        'category': 'wifi',
        'description': '连接WiFi网络',
        'detail': '尝试连接到指定的WiFi网络'
    },
    r'WiFi\.status\s*\(\s*\)': {
        'category': 'wifi',
        'description': '获取WiFi连接状态',
        'detail': '检查当前WiFi连接状态'
    },
    r'WiFi\.localIP\s*\(\s*\)': {
        'category': 'wifi',
        'description': '获取本地IP地址',
        'detail': '获取设备连接WiFi后的本地IP地址'
    },
    r'tone\s*\(\s*(\w+)\s*,\s*(\d+)\s*(?:\s*,\s*(\d+))?\s*\)': {
        'category': 'sound',
        'description': '在引脚{0}播放{1}Hz频率的声音',
        'detail': '通过{0}引脚产生{1}Hz频率的方波声音'
    },
    r'noTone\s*\(\s*(\w+)\s*\)': {
        'category': 'sound',
        'description': '停止引脚{0}的声音',
        'detail': '停止{0}引脚上的方波输出'
    },
    r'pulseIn\s*\(\s*(\w+)\s*,\s*(HIGH|LOW)\s*\)': {
        'category': 'io',
        'description': '读取引脚{0}上{1}脉冲的持续时间',
        'detail': '测量{0}引脚上{1}脉冲的时间长度（微秒）'
    },
    r'const\s+(\w+)\s*=\s*(\d+)': {
        'category': 'define',
        'description': '定义常量{0} = {1}',
        'detail': '创建一个只读常量{0}，值为{1}'
    }
}

_FUNCTION_EXPLANATIONS = {
    'getDistance': '超声波测距函数',
    'readSensors': '读取传感器数据函数',
    'blinkLED': 'LED闪烁函数',
    'controlServo': '舵机控制函数'
}

class ArduinoCodeInterpreter:
    """Arduino代码解释器 - 将代码逐行翻译为自然语言解释"""
    
    def __init__(self):
        self.variables = {}
        self.pin_modes = {}
        self.function_context = None
    
    def interpret(self, code):
        """解释完整代码"""
        lines = code.split('\n')
        explanations = []
        
        self.variables = {}
        self.pin_modes = {}
        self.function_context = None
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('/*'):
                continue
            
            explanation = self._interpret_line(line, line_num)
            if explanation:
                explanations.append(explanation)
            
            self._extract_context(line)
        
        return {
            'success': True,
            'explanations': explanations,
            'line_count': len(explanations),
            'variables': self.variables,
            'pin_modes': self.pin_modes,
            'summary': self._generate_summary(explanations)
        }
    
    def _interpret_line(self, line, line_num):
        """解释单行代码"""
        for pattern, info in _CODE_PATTERNS.items():
            match = re.match(pattern, line)
            if match:
                category = info['category']
                description = info['description'].format(*match.groups())
                
                detail = info.get('detail', '')
                if isinstance(detail, dict):
                    for group in match.groups():
                        if group in detail:
                            detail = detail[group]
                            break
                else:
                    library_info = info.get('library_info', {})
                    if library_info and len(match.groups()) >= 1:
                        lib_name = match.group(1)
                        lib_desc = library_info.get(lib_name, '未知')
                        detail = info['detail'].format(*match.groups(), lib_desc)
                    else:
                        detail = detail.format(*match.groups())
                
                return {
                    'line': line_num,
                    'code': line,
                    'category': category,
                    'description': description,
                    'detail': detail
                }
        
        if '=' in line and not line.startswith('#'):
            parts = line.split('=')
            var_name = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ''
            
            if var_name.endswith('++') or var_name.endswith('--'):
                return {
                    'line': line_num,
                    'code': line,
                    'category': 'variable',
                    'description': f'变量{var_name}自增/自减',
                    'detail': f'将变量{var_name}的值增加或减少1'
                }
            
            if re.match(r'^\w+\s*=\s*\w+\s*[+\-*/%]\s*\w+', line):
                return {
                    'line': line_num,
                    'code': line,
                    'category': 'math',
                    'description': f'变量{var_name}进行运算赋值',
                    'detail': f'将{value}的计算结果赋值给{var_name}'
                }
            
            return {
                'line': line_num,
                'code': line,
                'category': 'variable',
                'description': f'变量{var_name}赋值为{value}',
                'detail': f'将{value}的值赋给变量{var_name}'
            }
        
        return None
    
    def _extract_context(self, line):
        """提取代码上下文信息"""
        match = re.match(r'int\s+(\w+)\s*=\s*(\d+|A\d+)', line)
        if match:
            self.variables[match.group(1)] = {'type': 'int', 'value': match.group(2)}
        
        match = re.match(r'float\s+(\w+)\s*=\s*([\d.]+)', line)
        if match:
            self.variables[match.group(1)] = {'type': 'float', 'value': match.group(2)}
        
        match = re.match(r'pinMode\s*\(\s*(\w+)\s*,\s*(INPUT|OUTPUT|INPUT_PULLUP)\s*\)', line)
        if match:
            self.pin_modes[match.group(1)] = match.group(2)
        
        match = re.match(r'void\s+(\w+)\s*\(\s*\)', line)
        if match:
            self.function_context = match.group(1)
    
    def _generate_summary(self, explanations):
        """生成代码总结"""
        categories = defaultdict(list)
        for exp in explanations:
            categories[exp['category']].append(exp)
        
        summary = {
            'total_lines': len(explanations),
            'categories': {},
            'key_features': [],
            'complexity': 'simple'
        }
        
        category_names = {
            'include': '库引入',
            'define': '常量定义',
            'variable': '变量声明',
            'function': '函数定义',
            'io': 'I/O操作',
            'serial': '串口通信',
            'timing': '时间控制',
            'loop': '循环结构',
            'condition': '条件判断',
            'math': '数学运算',
            'servo': '舵机控制',
            'sensor': '传感器操作',
            'display': '显示操作',
            'wifi': '网络操作',
            'sound': '声音控制'
        }
        
        for cat, items in categories.items():
            summary['categories'][category_names.get(cat, cat)] = len(items)
        
        if len(categories) >= 5:
            summary['complexity'] = 'medium'
        if len(categories) >= 8:
            summary['complexity'] = 'advanced'
        
        if 'sensor' in categories:
            summary['key_features'].append('传感器数据采集')
        if 'display' in categories:
            summary['key_features'].append('数据显示')
        if 'servo' in categories:
            summary['key_features'].append('舵机控制')
        if 'wifi' in categories:
            summary['key_features'].append('网络通信')
        if 'condition' in categories and len(categories['condition']) > 2:
            summary['key_features'].append('复杂逻辑控制')
        if 'loop' in categories and len(categories['loop']) > 1:
            summary['key_features'].append('嵌套循环')
        
        if not summary['key_features']:
            summary['key_features'].append('基础I/O操作')
        
        return summary
    
    def explain_code_structure(self, code):
        """解释代码整体结构"""
        lines = code.split('\n')
        structure = {
            'includes': [],
            'defines': [],
            'declarations': [],
            'functions': [],
            'setup_lines': [],
            'loop_lines': [],
            'total_lines': len(lines)
        }
        
        current_section = 'declarations'
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            if line.startswith('#include'):
                structure['includes'].append(line)
            elif line.startswith('#define'):
                structure['defines'].append(line)
            elif line.startswith('void setup'):
                current_section = 'setup_lines'
            elif line.startswith('void loop'):
                current_section = 'loop_lines'
            elif line.startswith('void ') or line.startswith('float ') or line.startswith('int ') or line.startswith(
            'Servo ') or line.startswith('DHT ') or line.startswith('LiquidCrystal '):
                if current_section == 'declarations':
                    structure['declarations'].append(line)
                else:
                    structure['functions'].append(line)
            elif current_section == 'setup_lines':
                if line != '{' and line != '}':
                    structure['setup_lines'].append(line)
            elif current_section == 'loop_lines':
                if line != '{' and line != '}':
                    structure['loop_lines'].append(line)
            elif current_section == 'declarations':
                structure['declarations'].append(line)
        
        return structure
    
    def compare_with_tutorial(self, code, tutorial_name):
        """将代码与教程内容关联"""
        tutorial_map = {
            'LED闪烁入门': {
                'expected_components': ['led'],
                'expected_functions': ['pinMode', 'digitalWrite', 'delay'],
                'learning_objectives': ['掌握数字输出基础', '理解setup和loop函数', '学习delay延时函数']
            },
            '按钮控制LED': {
                'expected_components': ['button', 'led'],
                'expected_functions': ['pinMode', 'digitalRead', 'digitalWrite'],
                'learning_objectives': ['掌握数字输入基础', '理解按钮工作原理', '学习条件判断']
            },
            '模拟输入读取': {
                'expected_components': ['potentiometer'],
                'expected_functions': ['analogRead', 'Serial.print'],
                'learning_objectives': ['掌握模拟输入基础', '理解ADC转换', '学习串口输出']
            },
            '呼吸灯效果': {
                'expected_components': ['led'],
                'expected_functions': ['analogWrite', 'for循环'],
                'learning_objectives': ['掌握PWM输出', '理解模拟信号', '学习循环结构']
            },
            '舵机控制': {
                'expected_components': ['servo'],
                'expected_functions': ['Servo', 'attach', 'write'],
                'learning_objectives': ['掌握舵机控制', '理解PWM信号', '学习角度控制']
            },
            '超声波测距': {
                'expected_components': ['ultrasonic'],
                'expected_functions': ['pulseIn', 'getDistance'],
                'learning_objectives': ['掌握超声波传感器', '理解脉冲测量', '学习距离计算']
            },
            'LCD显示': {
                'expected_components': ['lcd1602'],
                'expected_functions': ['LiquidCrystal', 'print', 'setCursor'],
                'learning_objectives': ['掌握LCD显示', '理解并行通信', '学习文本输出']
            },
            '温湿度传感器': {
                'expected_components': ['dht11'],
                'expected_functions': ['DHT', 'readHumidity', 'readTemperature'],
                'learning_objectives': ['掌握DHT传感器', '理解单总线通信', '学习环境数据采集']
            }
        }
        
        if tutorial_name not in tutorial_map:
            return {
                'success': False,
                'error': f'未找到教程"{tutorial_name}"的关联信息'
            }
        
        tutorial = tutorial_map[tutorial_name]
        found_components = []
        found_functions = []
        
        for comp in tutorial['expected_components']:
            if comp in _COMPONENT_KEYWORDS:
                for keyword in _COMPONENT_KEYWORDS[comp]:
                    if keyword.lower() in code.lower():
                        found_components.append(comp)
                        break
        
        for func in tutorial['expected_functions']:
            if func in code:
                found_functions.append(func)
        
        return {
            'success': True,
            'tutorial_name': tutorial_name,
            'expected_components': tutorial['expected_components'],
            'found_components': found_components,
            'expected_functions': tutorial['expected_functions'],
            'found_functions': found_functions,
            'component_match': len(found_components) / len(tutorial['expected_components']),
            'function_match': len(found_functions) / len(tutorial['expected_functions']),
            'learning_objectives': tutorial['learning_objectives'],
            'recommendations': self._get_learning_recommendations(tutorial, found_components, found_functions)
        }
    
    def _get_learning_recommendations(self, tutorial, found_components, found_functions):
        """获取学习建议"""
        recommendations = []
        
        missing_components = set(tutorial['expected_components']) - set(found_components)
        if missing_components:
            recommendations.append(f'建议添加{", ".join(missing_components)}组件相关代码')
        
        missing_functions = set(tutorial['expected_functions']) - set(found_functions)
        if missing_functions:
            recommendations.append(f'建议使用{", ".join(missing_functions)}函数')
        
        if not missing_components and not missing_functions:
            recommendations.append('代码已包含教程所需的所有组件和函数')
            recommendations.append('建议运行仿真验证功能正确性')
        
        return recommendations

from collections import defaultdict

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

if __name__ == '__main__':
    interpreter = ArduinoCodeInterpreter()
    
    test_code = '''#include <DHT.h>
#include <LiquidCrystal.h>

#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

void setup() {
  Serial.begin(9600);
  dht.begin();
  lcd.begin(16, 2);
  lcd.logger.info("Hello World");
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  
  lcd.setCursor(0, 0);
  lcd.logger.info("Temp: ");
  lcd.logger.info(t);
  
  lcd.setCursor(0, 1);
  lcd.logger.info("Hum: ");
  lcd.logger.info(h);
  
  delay(1000);
}'''
    
    logger.info("=== Arduino代码解释器测试 ===")
    logger.info("\n1. 代码逐行解释:")
    result = interpreter.interpret(test_code)
    logger.info(f"   解释行数: {result['line_count']}")
    for exp in result['explanations'][:5]:
        logger.info(f"   第{exp['line']}行: [{exp['category']}] {exp['description']}")
    
    logger.info("\n2. 代码结构分析:")
    structure = interpreter.explain_code_structure(test_code)
    logger.info(f"   库引入: {len(structure['includes'])}个")
    logger.info(f"   常量定义: {len(structure['defines'])}个")
    logger.info(f"   变量声明: {len(structure['declarations'])}个")
    logger.info(f"   setup代码: {len(structure['setup_lines'])}行")
    logger.info(f"   loop代码: {len(structure['loop_lines'])}行")
    
    logger.info("\n3. 代码总结:")
    summary = result['summary']
    logger.info(f"   复杂度: {summary['complexity']}")
    logger.info(f"   关键特性: {summary['key_features']}")
    logger.info(f"   分类统计: {summary['categories']}")
    
    logger.info("\n4. 与教程关联:")
    tutorial_result = interpreter.compare_with_tutorial(test_code, '温湿度传感器')
    logger.info(f"   成功: {tutorial_result['success']}")
    logger.info(f"   组件匹配: {tutorial_result['component_match']*100:.0f}%")
    logger.info(f"   函数匹配: {tutorial_result['function_match']*100:.0f}%")
    logger.info(f"   学习目标: {tutorial_result['learning_objectives']}")