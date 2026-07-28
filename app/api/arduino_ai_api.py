#!/usr/bin/env python3
from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.arduino_ai_engine import ArduinoAIEngine
from app.ai.arduino_simulator import ArduinoSimulator
from app.ai.arduino_code_interpreter import ArduinoCodeInterpreter

arduino_ai_api = Blueprint('arduino_ai_api', __name__)
_simulator = ArduinoSimulator()

@arduino_ai_api.route('/api/arduino/ai/generate-code', methods=['POST'])
def generate_code():
    """AI代码生成器 - 根据自然语言描述生成Arduino代码"""
    data = request.get_json() or {}
    description = data.get('description', '')
    
    if not description:
        return jsonify({
            'success': False,
            'error': '项目描述不能为空'
        }), 400
    
    try:
        engine = ArduinoAIEngine()
        result = engine.generate_code(description)
        engine.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/analyze-sensor', methods=['POST'])
def analyze_sensor_data():
    """AI传感器数据分析 - 异常检测、趋势预测、智能洞察"""
    data = request.get_json() or {}
    device_id = data.get('device_id', '')
    sensor_type = data.get('sensor_type')
    window_size = int(data.get('window_size', 20))
    
    if not device_id:
        return jsonify({
            'success': False,
            'error': '设备ID不能为空'
        }), 400
    
    try:
        engine = ArduinoAIEngine()
        result = engine.analyze_sensor_data(device_id, sensor_type, window_size)
        engine.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/debug-code', methods=['POST'])
def debug_code():
    """AI代码调试助手 - 分析代码并提供调试建议"""
    data = request.get_json() or {}
    code = data.get('code', '')
    
    if not code:
        return jsonify({
            'success': False,
            'error': '代码不能为空'
        }), 400
    
    try:
        engine = ArduinoAIEngine()
        result = engine.debug_code(code, data.get('simulation_result'))
        engine.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/recommend-components', methods=['POST'])
def recommend_components():
    """AI硬件推荐引擎 - 根据项目需求智能推荐组件"""
    data = request.get_json() or {}
    description = data.get('description', '')
    budget = data.get('budget')
    
    if not description:
        return jsonify({
            'success': False,
            'error': '项目描述不能为空'
        }), 400
    
    try:
        engine = ArduinoAIEngine()
        result = engine.recommend_components(description, budget)
        engine.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/assess-progress', methods=['GET'])
def assess_progress():
    """评估用户Arduino学习进度"""
    user_id = int(request.args.get('user_id', 1))
    
    try:
        engine = ArduinoAIEngine()
        result = engine.assess_learning_progress(user_id)
        engine.close()
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/component-library', methods=['GET'])
def get_component_library():
    """获取组件库"""
    try:
        engine = ArduinoAIEngine()
        library = engine.get_component_library()
        engine.close()
        
        return jsonify({
            'success': True,
            'data': library,
            'count': len(library)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/suggest-projects', methods=['GET'])
def suggest_projects():
    """根据学习进度推荐项目"""
    user_id = int(request.args.get('user_id', 1))
    
    try:
        engine = ArduinoAIEngine()
        progress = engine.assess_learning_progress(user_id)
        engine.close()
        
        weak_skills = [s for s in progress['skills'] if s['score'] == 0]
        
        suggestions = []
        if not weak_skills:
            suggestions = [
                {'name': 'IoT温湿度监控系统', 'difficulty': 'advanced', 'skills': ['sensors', 'communication']},
                {'name': '智能小车控制系统', 'difficulty': 'advanced', 'skills': ['actuators', 'communication']},
                {'name': '环境监测站', 'difficulty': 'advanced', 'skills': ['sensors', 'displays']}
            ]
        else:
            for skill in weak_skills:
                skill_map = {
                    'digital_io': {'name': 'LED闪烁与按钮控制', 'difficulty': 'beginner'},
                    'analog_io': {'name': '模拟输入与电位器控制', 'difficulty': 'beginner'},
                    'sensors': {'name': '温湿度传感器读取', 'difficulty': 'intermediate'},
                    'actuators': {'name': '舵机与蜂鸣器控制', 'difficulty': 'intermediate'},
                    'displays': {'name': 'LCD显示屏显示', 'difficulty': 'intermediate'},
                    'communication': {'name': 'WiFi模块数据上传', 'difficulty': 'advanced'}
                }
                if skill['skill'] in skill_map:
                    suggestions.append({
                        'name': skill_map[skill['skill']]['name'],
                        'difficulty': skill_map[skill['skill']]['difficulty'],
                        'skills': [skill['skill']],
                        'reason': f"您的{skill['name']}技能需要提升"
                    })
        
        return jsonify({
            'success': True,
            'data': suggestions,
            'count': len(suggestions),
            'current_progress': progress['progress_percentage']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/optimize-code', methods=['POST'])
def optimize_code():
    """AI代码优化建议"""
    data = request.get_json() or {}
    code = data.get('code', '')
    
    if not code:
        return jsonify({
            'success': False,
            'error': '代码不能为空'
        }), 400
    
    try:
        engine = ArduinoAIEngine()
        debug_result = engine.debug_code(code)
        engine.close()
        
        optimizations = []
        
        if 'delay(' in code:
            optimizations.append({
                'type': 'performance',
                'message': '使用非阻塞方式替代delay()',
                'suggestion': '使用millis()实现非阻塞延迟，提高代码响应性',
                'example': '''unsigned long previousMillis = 0;
const long interval = 1000;

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    // 执行周期性任务
  }
}'''
            })
        
        if 'analogRead(' in code and 'map(' not in code:
            optimizations.append({
                'type': 'readability',
                'message': '建议使用map()函数进行数值转换',
                'suggestion': '使用map(value, fromLow, fromHigh, toLow, toHigh)简化数值映射',
                'example': 'int brightness = map(sensorValue, 0, 1023, 0, 255);'
            })
        
        if '#include <Servo.h>' in code and 'detach(' not in code:
            optimizations.append({
                'type': 'best_practice',
                'message': '建议在不需要舵机时调用detach()释放引脚',
                'suggestion': '使用myservo.detach()释放PWM引脚供其他用途',
                'example': 'myservo.detach(); // 释放舵机引脚'
            })
        
        if 'digitalRead(' in code and 'INPUT_PULLUP' not in code:
            optimizations.append({
                'type': 'hardware',
                'message': '建议使用INPUT_PULLUP模式',
                'suggestion': '使用pinMode(pin, INPUT_PULLUP)启用内部上拉电阻，减少外部元件',
                'example': 'pinMode(buttonPin, INPUT_PULLUP);'
            })
        
        return jsonify({
            'success': True,
            'optimizations': optimizations,
            'optimization_count': len(optimizations),
            'debug_issues': debug_result['issues']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/complete-workflow', methods=['POST'])
def complete_workflow():
    """完整工作流闭环 - 自然语言描述→AI代码生成→仿真执行→AI调试分析"""
    data = request.get_json() or {}
    description = data.get('description', '')
    iterations = int(data.get('iterations', 3))
    speed = float(data.get('speed', 1.0))
    
    if not description:
        return jsonify({
            'success': False,
            'error': '项目描述不能为空'
        }), 400
    
    result = {
        'success': True,
        'description': description,
        'workflow': []
    }
    
    try:
        engine = ArduinoAIEngine()
        
        result['workflow'].append({
            'step': '1',
            'name': 'AI代码生成',
            'status': 'running'
        })
        
        gen_result = engine.generate_code(description)
        if not gen_result['success']:
            result['success'] = False
            result['error'] = gen_result['error']
            result['workflow'][-1]['status'] = 'failed'
            engine.close()
            return jsonify(result), 400
        
        result['code'] = gen_result['code']
        result['template'] = gen_result['template']
        result['suggested_components'] = gen_result['suggested_components']
        result['workflow'][-1]['status'] = 'success'
        result['workflow'][-1]['details'] = {'template': gen_result['template']}
        
        result['workflow'].append({
            'step': '2',
            'name': '代码仿真',
            'status': 'running'
        })
        
        _simulator.reset()
        sim_result = _simulator.simulate(gen_result['code'], iterations, speed)
        result['simulation'] = sim_result
        result['workflow'][-1]['status'] = 'success'
        result['workflow'][-1]['details'] = {
            'log_entries': len(sim_result.get('log', [])),
            'serial_output_length': len(sim_result.get('serial_output', ''))
        }
        
        result['workflow'].append({
            'step': '3',
            'name': 'AI代码调试',
            'status': 'running'
        })
        
        debug_result = engine.debug_code(gen_result['code'], sim_result)
        result['debug'] = debug_result
        result['workflow'][-1]['status'] = 'success'
        result['workflow'][-1]['details'] = {
            'issue_count': debug_result['issue_count'],
            'has_errors': debug_result['has_errors'],
            'has_warnings': debug_result['has_warnings']
        }
        
        result['workflow'].append({
            'step': '4',
            'name': 'AI硬件推荐',
            'status': 'running'
        })
        
        recommend_result = engine.recommend_components(description)
        result['hardware_recommendation'] = recommend_result
        result['workflow'][-1]['status'] = 'success'
        result['workflow'][-1]['details'] = {
            'component_count': len(recommend_result.get('components', [])),
            'total_price': recommend_result.get('total_price', 0)
        }
        
        engine.close()
        
        result['summary'] = {
            'code_generated': True,
            'simulation_completed': True,
            'debug_analyzed': True,
            'hardware_recommended': True,
            'has_errors': debug_result['has_errors'],
            'has_warnings': debug_result['has_warnings'],
            'total_issues': debug_result['issue_count'],
            'suggested_components_count': len(gen_result['suggested_components']),
            'recommended_hardware_cost': recommend_result.get('total_price', 0)
        }
        
        return jsonify(result)
    
    except Exception as e:
        result['success'] = False
        result['error'] = str(e)
        if result['workflow']:
            result['workflow'][-1]['status'] = 'failed'
            result['workflow'][-1]['error'] = str(e)
        return jsonify(result), 500

@arduino_ai_api.route('/api/arduino/ai/interpret-code', methods=['POST'])
def interpret_code():
    """AI代码解释器 - 将Arduino代码逐行翻译为自然语言解释"""
    data = request.get_json() or {}
    code = data.get('code', '')
    
    if not code:
        return jsonify({
            'success': False,
            'error': '代码不能为空'
        }), 400
    
    try:
        interpreter = ArduinoCodeInterpreter()
        result = interpreter.interpret(code)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/explain-structure', methods=['POST'])
def explain_structure():
    """解释代码整体结构"""
    data = request.get_json() or {}
    code = data.get('code', '')
    
    if not code:
        return jsonify({
            'success': False,
            'error': '代码不能为空'
        }), 400
    
    try:
        interpreter = ArduinoCodeInterpreter()
        structure = interpreter.explain_code_structure(code)
        
        return jsonify({
            'success': True,
            'data': structure
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/compare-with-tutorial', methods=['POST'])
def compare_with_tutorial():
    """将代码与教程内容关联"""
    data = request.get_json() or {}
    code = data.get('code', '')
    tutorial_name = data.get('tutorial_name', '')
    
    if not code:
        return jsonify({
            'success': False,
            'error': '代码不能为空'
        }), 400
    
    if not tutorial_name:
        return jsonify({
            'success': False,
            'error': '教程名称不能为空'
        }), 400
    
    try:
        interpreter = ArduinoCodeInterpreter()
        result = interpreter.compare_with_tutorial(code, tutorial_name)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/learning-path', methods=['GET'])
def get_learning_path():
    """AI自适应学习路径 - 根据学习进度动态推荐教程和项目"""
    user_id = int(request.args.get('user_id', 1))
    
    try:
        engine = ArduinoAIEngine()
        result = engine.get_adaptive_learning_path(user_id)
        engine.close()
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

from app.ai.arduino_ai_enhanced import ArduinoAIEnhanced

@arduino_ai_api.route('/api/arduino/ai/predict-sensor-failure', methods=['POST'])
def predict_sensor_failure():
    """AI传感器故障预测 - 使用数据科学Agent进行ML-based预测"""
    data = request.get_json() or {}
    device_id = data.get('device_id', '')
    sensor_type = data.get('sensor_type')
    window_size = int(data.get('window_size', 50))
    
    if not device_id:
        return jsonify({
            'success': False,
            'error': '设备ID不能为空'
        }), 400
    
    try:
        engine = ArduinoAIEnhanced()
        result = engine.predict_sensor_failure(device_id, sensor_type, window_size)
        engine.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/digital-twin-simulate', methods=['POST'])
def digital_twin_simulate():
    """数字孪生模拟 - 模拟Arduino项目在虚拟环境中的运行"""
    data = request.get_json() or {}
    project_description = data.get('description', '')
    components = data.get('components', [])
    iterations = int(data.get('iterations', 10))
    
    if not project_description:
        return jsonify({
            'success': False,
            'error': '项目描述不能为空'
        }), 400
    
    try:
        engine = ArduinoAIEnhanced()
        result = engine.digital_twin_simulate(project_description, components, iterations)
        engine.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/component-compatibility', methods=['POST'])
def component_compatibility():
    """查询组件兼容性 - 使用知识图谱Agent"""
    data = request.get_json() or {}
    components = data.get('components', [])
    
    if not components:
        return jsonify({
            'success': False,
            'error': '组件列表不能为空'
        }), 400
    
    try:
        engine = ArduinoAIEnhanced()
        result = engine.get_component_compatibility(components)
        engine.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/troubleshoot-component', methods=['POST'])
def troubleshoot_component():
    """组件故障排除 - 使用知识图谱进行推理"""
    data = request.get_json() or {}
    component_name = data.get('component', '')
    issue_description = data.get('issue', '')
    
    if not component_name:
        return jsonify({
            'success': False,
            'error': '组件名称不能为空'
        }), 400
    
    try:
        engine = ArduinoAIEnhanced()
        result = engine.analyze_component_troubleshooting(component_name, issue_description)
        engine.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/build-pipeline', methods=['POST'])
def build_pipeline():
    """创建Arduino构建流水线 - 使用DevOps Agent"""
    data = request.get_json() or {}
    project_id = data.get('project_id', '')
    code = data.get('code', '')
    
    if not project_id or not code:
        return jsonify({
            'success': False,
            'error': '项目ID和代码不能为空'
        }), 400
    
    try:
        engine = ArduinoAIEnhanced()
        result = engine.create_build_pipeline(project_id, code)
        engine.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/analyze-camera-image', methods=['POST'])
def analyze_camera_image():
    """分析摄像头图像 - 使用图像处理Agent（支持ESP32-CAM）"""
    data = request.get_json() or {}
    image_data = data.get('image_data', '')
    processing_type = data.get('processing_type', 'object_detection')
    
    if not image_data:
        return jsonify({
            'success': False,
            'error': '图像数据不能为空'
        }), 400
    
    try:
        engine = ArduinoAIEnhanced()
        result = engine.analyze_camera_image(image_data, processing_type)
        engine.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/vision-control', methods=['POST'])
def vision_control():
    """视觉控制 - 根据图像分析结果生成Arduino控制代码"""
    data = request.get_json() or {}
    image_data = data.get('image_data', '')
    target_color = data.get('target_color')
    target_object = data.get('target_object')
    
    if not image_data:
        return jsonify({
            'success': False,
            'error': '图像数据不能为空'
        }), 400
    
    try:
        engine = ArduinoAIEnhanced()
        result = engine.vision_based_control(image_data, target_color, target_object)
        engine.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_ai_api.route('/api/arduino/ai/enhanced-learning-path', methods=['GET'])
def enhanced_learning_path():
    """增强版学习路径 - 结合AI能力推荐学习内容"""
    user_id = int(request.args.get('user_id', 1))
    
    try:
        engine = ArduinoAIEnhanced()
        result = engine.get_enhanced_learning_path(user_id)
        engine.close()
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500