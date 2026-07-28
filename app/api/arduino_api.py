#!/usr/bin/env python3
from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.arduino_project_manager import ArduinoProjectManager
from app.ai.arduino_simulator import ArduinoSimulator
from app.ai.arduino_tutorial import ArduinoTutorialManager
from app.ai.arduino_data_collector import ArduinoDataCollector
from app.ai.arduino_iot import ArduinoIoTManager

arduino_api = Bluelogger.info('arduino_api', __name__)

_simulator = ArduinoSimulator()
_iot_manager = ArduinoIoTManager()

@arduino_api.route('/api/arduino/projects', methods=['GET'])
def get_projects():
    """获取项目列表"""
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    category = request.args.get('category')
    difficulty = request.args.get('difficulty')
    user_id = request.args.get('user_id')
    
    try:
        manager = ArduinoProjectManager()
        projects = manager.get_projects(page, page_size, category, difficulty, user_id)
        manager.close()
        
        return jsonify({
            'success': True,
            'data': projects,
            'count': len(projects),
            'page': page,
            'page_size': page_size
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/projects', methods=['POST'])
def create_project():
    """创建项目"""
    data = request.get_json() or {}
    user_id = data.get('user_id', 1)
    name = data.get('name', '')
    description = data.get('description', '')
    category = data.get('category', 'other')
    difficulty = data.get('difficulty', 'beginner')
    
    if not name:
        return jsonify({
            'success': False,
            'error': '项目名称不能为空'
        }), 400
    
    try:
        manager = ArduinoProjectManager()
        project_id = manager.create_project(user_id, name, description, category, difficulty)
        
        if data.get('files'):
            for file_data in data['files']:
                manager.add_file(
                    project_id,
                    file_data.get('filename', ''),
                    file_data.get('content', ''),
                    file_data.get('file_type', 'cpp'),
                    file_data.get('is_main', False)
                )
        
        if data.get('components'):
            for comp in data['components']:
                manager.add_component(
                    project_id,
                    comp.get('component_name', ''),
                    comp.get('quantity', 1),
                    comp.get('category', '')
                )
        
        if data.get('tags'):
            for tag in data['tags']:
                manager.add_tag(project_id, tag)
        
        manager.close()
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'message': '项目创建成功'
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """获取项目详情"""
    try:
        manager = ArduinoProjectManager()
        project = manager.get_project(project_id)
        manager.close()
        
        if not project:
            return jsonify({
                'success': False,
                'error': '项目不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': project
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """更新项目"""
    data = request.get_json() or {}
    
    try:
        manager = ArduinoProjectManager()
        success = manager.update_project(project_id, **data)
        manager.close()
        
        if not success:
            return jsonify({
                'success': False,
                'error': '项目更新失败'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '项目更新成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """删除项目"""
    try:
        manager = ArduinoProjectManager()
        success = manager.delete_project(project_id)
        manager.close()
        
        if not success:
            return jsonify({
                'success': False,
                'error': '项目删除失败'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '项目删除成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/projects/<project_id>/like', methods=['POST'])
def like_project(project_id):
    """点赞项目"""
    data = request.get_json() or {}
    user_id = data.get('user_id', 1)
    
    try:
        manager = ArduinoProjectManager()
        success = manager.like_project(user_id, project_id)
        project = manager.get_project(project_id)
        manager.close()
        
        if not success:
            return jsonify({
                'success': False,
                'error': '点赞失败，可能已点赞过'
            }), 400
        
        return jsonify({
            'success': True,
            'likes': project.get('likes', 0),
            'message': '点赞成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/projects/search', methods=['GET'])
def search_projects():
    """搜索项目"""
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    
    if not keyword:
        return jsonify({
            'success': False,
            'error': '搜索关键词不能为空'
        }), 400
    
    try:
        manager = ArduinoProjectManager()
        projects = manager.search_projects(keyword, page, page_size)
        manager.close()
        
        return jsonify({
            'success': True,
            'data': projects,
            'count': len(projects)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/projects/categories', methods=['GET'])
def get_project_categories():
    """获取项目分类"""
    try:
        manager = ArduinoProjectManager()
        categories = manager.get_project_categories()
        manager.close()
        
        return jsonify({
            'success': True,
            'data': categories
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/simulate', methods=['POST'])
def simulate_code():
    """模拟执行Arduino代码"""
    data = request.get_json() or {}
    code = data.get('code', '')
    iterations = int(data.get('iterations', 5))
    speed = float(data.get('speed', 1.0))
    
    if not code:
        return jsonify({
            'success': False,
            'error': '代码不能为空'
        }), 400
    
    try:
        _simulator.reset()
        
        if data.get('analog_inputs'):
            for pin, value in data['analog_inputs'].items():
                _simulator.set_analog_input(pin, value)
        
        if data.get('digital_inputs'):
            for pin, value in data['digital_inputs'].items():
                _simulator.set_digital_input(pin, value)
        
        result = _simulator.simulate(code, iterations, speed)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/simulate/result', methods=['GET'])
def get_simulation_result():
    """获取当前模拟结果"""
    try:
        result = _simulator.get_simulation_result()
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/simulate/stop', methods=['POST'])
def stop_simulation():
    """停止模拟"""
    try:
        _simulator.stop()
        
        return jsonify({
            'success': True,
            'message': '模拟已停止'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/tutorials', methods=['GET'])
def get_tutorials():
    """获取教程列表"""
    difficulty = request.args.get('difficulty')
    
    try:
        tutor = ArduinoTutorialManager()
        tutorials = tutor.get_tutorials(difficulty)
        
        return jsonify({
            'success': True,
            'data': tutorials,
            'count': len(tutorials)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/tutorials/<tutorial_id>', methods=['GET'])
def get_tutorial(tutorial_id):
    """获取单个教程"""
    try:
        tutor = ArduinoTutorialManager()
        tutorial = tutor.get_tutorial(tutorial_id)
        
        if not tutorial:
            return jsonify({
                'success': False,
                'error': '教程不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': tutorial
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/tutorials/categories', methods=['GET'])
def get_tutorial_categories():
    """获取教程分类"""
    try:
        tutor = ArduinoTutorialManager()
        categories = tutor.get_tutorial_categories()
        
        return jsonify({
            'success': True,
            'data': categories
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/tutorials/search', methods=['GET'])
def search_tutorials():
    """搜索教程"""
    keyword = request.args.get('keyword', '')
    
    if not keyword:
        return jsonify({
            'success': False,
            'error': '搜索关键词不能为空'
        }), 400
    
    try:
        tutor = ArduinoTutorialManager()
        tutorials = tutor.search_tutorials(keyword)
        
        return jsonify({
            'success': True,
            'data': tutorials,
            'count': len(tutorials)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/tutorials/learning-path', methods=['GET'])
def get_learning_path():
    """获取学习路径"""
    level = request.args.get('level', 'beginner')
    
    try:
        tutor = ArduinoTutorialManager()
        path = tutor.get_learning_path(level)
        
        return jsonify({
            'success': True,
            'data': path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/devices', methods=['GET'])
def get_devices():
    """获取设备列表"""
    try:
        collector = ArduinoDataCollector()
        devices = collector.get_device_list()
        collector.close()
        
        return jsonify({
            'success': True,
            'data': devices,
            'count': len(devices)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/devices', methods=['POST'])
def add_device():
    """添加设备"""
    data = request.get_json() or {}
    device_id = data.get('device_id', '')
    name = data.get('name', '')
    type = data.get('type', 'arduino_uno')
    
    if not device_id or not name:
        return jsonify({
            'success': False,
            'error': '设备ID和名称不能为空'
        }), 400
    
    try:
        collector = ArduinoDataCollector()
        success = collector.add_device(device_id, name, type)
        collector.close()
        
        if not success:
            return jsonify({
                'success': False,
                'error': '设备ID已存在'
            }), 400
        
        return jsonify({
            'success': True,
            'message': '设备添加成功'
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/devices/<device_id>/data', methods=['GET'])
def get_device_data(device_id):
    """获取设备传感器数据"""
    sensor_type = request.args.get('sensor_type')
    limit = int(request.args.get('limit', 100))
    
    try:
        collector = ArduinoDataCollector()
        data = collector.get_device_data(device_id, sensor_type, limit)
        collector.close()
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/devices/<device_id>/data', methods=['POST'])
def record_sensor_data(device_id):
    """记录传感器数据"""
    data = request.get_json() or {}
    sensor_type = data.get('sensor_type', '')
    value = data.get('value', 0)
    unit = data.get('unit')
    
    if not sensor_type:
        return jsonify({
            'success': False,
            'error': '传感器类型不能为空'
        }), 400
    
    try:
        collector = ArduinoDataCollector()
        collector.record_sensor_data(device_id, sensor_type, value, unit)
        collector.close()
        
        return jsonify({
            'success': True,
            'message': '数据记录成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/devices/<device_id>/summary', methods=['GET'])
def get_device_summary(device_id):
    """获取设备数据摘要"""
    try:
        collector = ArduinoDataCollector()
        summary = collector.get_sensor_summary(device_id)
        collector.close()
        
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/sensors/types', methods=['GET'])
def get_sensor_types():
    """获取支持的传感器类型"""
    try:
        collector = ArduinoDataCollector()
        types = collector.get_sensor_types()
        collector.close()
        
        return jsonify({
            'success': True,
            'data': types
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/alerts', methods=['GET'])
def get_alerts():
    """获取最近告警"""
    limit = int(request.args.get('limit', 20))
    
    try:
        collector = ArduinoDataCollector()
        alerts = collector.get_recent_alerts(limit)
        collector.close()
        
        return jsonify({
            'success': True,
            'data': alerts,
            'count': len(alerts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/devices/<device_id>/export', methods=['GET'])
def export_device_data(device_id):
    """导出设备数据"""
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    try:
        collector = ArduinoDataCollector()
        data = collector.export_data(device_id, start_time, end_time)
        collector.close()
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/iot/devices', methods=['GET'])
def get_iot_devices():
    """获取IoT设备列表"""
    try:
        devices = _iot_manager.get_all_devices()
        
        return jsonify({
            'success': True,
            'data': devices,
            'count': len(devices)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/iot/devices', methods=['POST'])
def add_iot_device():
    """添加IoT设备"""
    data = request.get_json() or {}
    device_id = data.get('device_id', '')
    name = data.get('name', '')
    ip_address = data.get('ip_address')
    port = int(data.get('port', 80))
    protocol = data.get('protocol', 'http')
    
    if not device_id or not name:
        return jsonify({
            'success': False,
            'error': '设备ID和名称不能为空'
        }), 400
    
    try:
        _iot_manager.add_device(device_id, name, ip_address, port, protocol)
        
        return jsonify({
            'success': True,
            'message': 'IoT设备添加成功'
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/iot/devices/<device_id>/connect', methods=['POST'])
def connect_iot_device(device_id):
    """连接IoT设备"""
    try:
        success = _iot_manager.connect_device(device_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': '设备连接失败'
            }), 500
        
        return jsonify({
            'success': True,
            'message': '设备连接成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/iot/devices/<device_id>/disconnect', methods=['POST'])
def disconnect_iot_device(device_id):
    """断开IoT设备连接"""
    try:
        _iot_manager.disconnect_device(device_id)
        
        return jsonify({
            'success': True,
            'message': '设备已断开连接'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/iot/devices/<device_id>/command', methods=['POST'])
def send_iot_command(device_id):
    """发送命令到IoT设备"""
    data = request.get_json() or {}
    command = data.get('command', '')
    params = data.get('params', {})
    
    if not command:
        return jsonify({
            'success': False,
            'error': '命令不能为空'
        }), 400
    
    try:
        response = _iot_manager.send_command(device_id, command, params)
        
        if response is False:
            return jsonify({
                'success': False,
                'error': '命令发送失败，设备可能离线'
            }), 500
        
        return jsonify({
            'success': True,
            'data': response
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/iot/devices/<device_id>/status', methods=['GET'])
def get_iot_device_status(device_id):
    """获取IoT设备状态"""
    try:
        status = _iot_manager.get_device_status(device_id)
        
        if not status:
            return jsonify({
                'success': False,
                'error': '设备不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/iot/devices/<device_id>/stats', methods=['GET'])
def get_iot_device_stats(device_id):
    """获取IoT设备统计"""
    try:
        stats = _iot_manager.get_device_stats(device_id)
        
        if not stats:
            return jsonify({
                'success': False,
                'error': '设备不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@arduino_api.route('/api/arduino/iot/scan', methods=['GET'])
def scan_network():
    """扫描网络中的设备"""
    subnet = request.args.get('subnet', '192.168.1.')
    start = int(request.args.get('start', 1))
    end = int(request.args.get('end', 50))
    
    try:
        found = _iot_manager.scan_network(subnet, start, end)
        
        return jsonify({
            'success': True,
            'data': found,
            'count': len(found),
            'message': f'在 {subnet}{start}-{subnet}{end} 范围内发现 {len(found)} 个设备'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500