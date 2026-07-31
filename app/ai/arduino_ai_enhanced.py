#!/usr/bin/env python3
"""
Arduino AI增强引擎 - 利用AI技术Agent增强Arduino开发功能
集成数据科学、数字孪生、知识图谱、DevOps、图像处理等AI能力
"""
import sqlite3
import json
import os
import sys
import re
import math
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai_engines.ai_data_science_agent import AIDataScienceAgent
from ai_engines.ai_digital_twin_agent import AIDigitalTwinAgent
from ai_engines.ai_knowledge_graph_agent import AIKnowledgeGraphAgent
from ai_engines.ai_devops_agent import AIDevOpsAgent
from ai_engines.ai_image_processing_agent import AIImageProcessingAgent

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'app.db')

class ArduinoAIEnhanced:
    """Arduino AI增强引擎 - 将AI技术能力深度集成到Arduino开发流程"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        self.data_science_agent = AIDataScienceAgent("arduino_ds_001", "Arduino数据科学AI", 9)
        self.digital_twin_agent = AIDigitalTwinAgent("arduino_dt_001", "Arduino数字孪生AI", 8)
        self.knowledge_graph_agent = AIKnowledgeGraphAgent("arduino_kg_001", "Arduino知识图谱AI", 8)
        self.devops_agent = AIDevOpsAgent("arduino_devops_001", "Arduino DevOps AI", 8)
        self.image_processing_agent = AIImageProcessingAgent("arduino_img_001", "Arduino图像处理AI", 8)
        
        self._init_knowledge_graph()
    
    def _init_knowledge_graph(self):
        """初始化Arduino组件知识图谱"""
        entities = [
            {"name": "Arduino Uno", "type": "controller", "properties": {"pins": 14, "analog_pins": 6, "memory": "32KB"}},
            {"name": "Arduino Nano", "type": "controller", "properties": {"pins": 14, "analog_pins": 8, "memory": "32KB"}},
            {"name": "Arduino Mega", "type": "controller", "properties": {"pins": 54, "analog_pins": 16, "memory": "256KB"}},
            {"name": "ESP32", "type": "controller", "properties": {"pins": 36, "wifi": True, "bluetooth": True}},
            {"name": "DHT11", "type": "sensor", "properties": {"interface": "digital", "accuracy": "±5%"}},
            {"name": "DHT22", "type": "sensor", "properties": {"interface": "digital", "accuracy": "±2%"}},
            {"name": "HC-SR04", "type": "sensor", "properties": {"interface": "digital", "range": "2-400cm"}},
            {"name": "SG90", "type": "actuator", "properties": {"interface": "pwm", "angle": "0-180°"}},
            {"name": "LCD 1602", "type": "display", "properties": {"interface": "parallel/i2c", "columns": 16, "rows": 2}},
            {"name": "ESP8266", "type": "communication", "properties": {"interface": "uart", "protocol": "WiFi"}},
            {"name": "HC-05", "type": "communication", "properties": {"interface": "uart", "protocol": "Bluetooth"}}
        ]
        
        relationships = [
            {"source": "Arduino Uno", "target": "DHT11", "relation": "compatible_with", "details": {"pin": "D2", "voltage": "5V"}},
            {"source": "Arduino Uno", "target": "HC-SR04", "relation": "compatible_with", "details": {"trig_pin": "D9", "echo_pin": "D10", "voltage": "5V"}},
            {"source": "Arduino Uno", "target": "SG90", "relation": "compatible_with", "details": {"pin": "D9(PWM)", "voltage": "4.8-6V"}},
            {"source": "Arduino Uno", "target": "LCD 1602", "relation": "compatible_with", "details": {"pins": "D12,D11,D5,D4,D3,D2", "voltage": "5V"}},
            {"source": "Arduino Uno", "target": "ESP8266", "relation": "compatible_with", "details": {"pins": "D0,D1", "voltage": "3.3V"}},
            {"source": "DHT11", "target": "DHT22", "relation": "alternative_to", "details": {"upgrade": "higher accuracy"}},
            {"source": "ESP32", "target": "Arduino Uno", "relation": "alternative_to", "details": {"upgrade": "built-in WiFi/Bluetooth"}},
            {"source": "LCD 1602", "target": "LCD 1602 I2C", "relation": "alternative_to", "details": {"upgrade": "fewer pins"}},
            {"source": "HC-SR04", "target": "SG90", "relation": "commonly_used_with", "details": {"project": "obstacle avoidance"}},
            {"source": "DHT11", "target": "LCD 1602", "relation": "commonly_used_with", "details": {"project": "environment monitor"}},
            {"source": "DHT11", "target": "ESP8266", "relation": "commonly_used_with", "details": {"project": "IoT sensor"}},
            {"source": "ESP32", "target": "Camera", "relation": "compatible_with", "details": {"interface": "MIPI", "model": "OV2640"}}
        ]
        
        self.knowledge_graph_agent.create_graph("arduino_components")
        for entity in entities:
            self.knowledge_graph_agent.add_entity("arduino_components", entity)
        for relation in relationships:
            self.knowledge_graph_agent.add_relationship("arduino_components", relation)
    
    def predict_sensor_failure(self, device_id, sensor_type=None, window_size=50):
        """AI传感器故障预测 - 使用数据科学Agent进行ML-based预测"""
        self.cursor.execute('''
            SELECT value, timestamp FROM sensor_data 
            WHERE device_id = ?
            ''' + (f'AND sensor_type = ?' if sensor_type else '') + '''
            ORDER BY timestamp DESC LIMIT ?
        ''', ([device_id, sensor_type, window_size] if sensor_type else [device_id, window_size]))
        
        data = [dict(row) for row in self.cursor.fetchall()]
        
        if len(data) < 10:
            return {
                'success': False,
                'error': '数据量不足，至少需要10条数据进行预测'
            }
        
        values = [float(d['value']) for d in data]
        
        prediction_result = self.data_science_agent.predict(
            model_type='linear_regression',
            data=values,
            forecast_steps=5
        )
        
        anomaly_result = self.data_science_agent.anomaly_detection(
            data=values,
            method='z_score',
            threshold=3.0
        )
        
        failure_score = self._calculate_failure_score(values, prediction_result, anomaly_result)
        
        return {
            'success': True,
            'device_id': device_id,
            'sensor_type': sensor_type,
            'data_count': len(data),
            'prediction': prediction_result,
            'anomalies': anomaly_result.get('anomalies', []),
            'anomaly_count': anomaly_result.get('anomaly_count', 0),
            'failure_risk': {
                'score': round(failure_score, 2),
                'level': self._get_risk_level(failure_score),
                'recommendation': self._get_failure_recommendation(failure_score)
            },
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _calculate_failure_score(self, values, prediction, anomaly_result):
        """计算故障风险分数"""
        score = 0.0
        
        if len(values) >= 10:
            mean_val = sum(values) / len(values)
            std_dev = math.sqrt(sum((v - mean_val) ** 2 for v in values) / len(values))
            
            if std_dev > mean_val * 0.3:
                score += 0.3
            
            if prediction and 'trend' in prediction:
                trend = prediction['trend']
                if trend == 'decreasing' and mean_val > 0:
                    score += 0.2
                if trend == 'increasing' and mean_val > 0:
                    score += 0.1
        
        anomaly_count = anomaly_result.get('anomaly_count', 0)
        if anomaly_count > 0:
            score += min(anomaly_count * 0.15, 0.4)
        
        return min(score, 1.0)
    
    def _get_risk_level(self, score):
        """获取风险等级"""
        if score < 0.3:
            return 'low'
        elif score < 0.6:
            return 'medium'
        else:
            return 'high'
    
    def _get_failure_recommendation(self, score):
        """获取故障推荐"""
        if score < 0.3:
            return '传感器工作正常，建议继续监控'
        elif score < 0.6:
            return '检测到轻微异常，建议关注传感器状态，考虑预防性维护'
        else:
            return '检测到高风险，建议尽快更换传感器或检查硬件连接'
    
    def digital_twin_simulate(self, project_description, components=None, iterations=10):
        """数字孪生模拟 - 模拟Arduino项目在虚拟环境中的运行"""
        if components is None:
            components = []
        
        twin_model = {
            'name': project_description,
            'components': components,
            'environment': {
                'temperature': 25.0,
                'humidity': 50.0,
                'noise_level': 0.0
            },
            'initial_state': {
                'digital_pins': {i: False for i in range(14)},
                'analog_pins': {f'A{i}': 0 for i in range(6)},
                'pwm_pins': {i: 0 for i in [3, 5, 6, 9, 10, 11]}
            }
        }
        
        simulation_result = self.digital_twin_agent.simulate(
            model=twin_model,
            steps=iterations,
            parameters={
                'time_step': 1.0,
                'sensor_noise': 0.05,
                'actuator_delay': 0.1
            }
        )
        
        scenario_result = self.digital_twin_agent.scenario_simulation(
            model=twin_model,
            scenarios=[
                {'name': 'normal_operation', 'description': '正常运行场景'},
                {'name': 'sensor_failure', 'description': '传感器故障场景'},
                {'name': 'power_fluctuation', 'description': '电源波动场景'}
            ]
        )
        
        optimization_result = self.digital_twin_agent.optimize(
            model=twin_model,
            objective='minimize_power',
            constraints={
                'min_sensor_update_rate': 1.0,
                'max_actuator_power': 5.0
            }
        )
        
        return {
            'success': True,
            'project_description': project_description,
            'components': components,
            'twin_model': twin_model,
            'simulation': simulation_result,
            'scenarios': scenario_result,
            'optimization': optimization_result,
            'recommendations': self._generate_twin_recommendations(simulation_result, optimization_result)
        }
    
    def _generate_twin_recommendations(self, simulation, optimization):
        """生成数字孪生建议"""
        recommendations = []
        
        if simulation and 'results' in simulation:
            results = simulation['results']
            for step in results:
                if 'warnings' in step:
                    recommendations.extend(step['warnings'])
        
        if optimization and 'suggestions' in optimization:
            recommendations.extend(optimization['suggestions'])
        
        return recommendations[:5]
    
    def get_component_compatibility(self, components):
        """查询组件兼容性 - 使用知识图谱Agent"""
        results = []
        
        for i, comp1 in enumerate(components):
            for j, comp2 in enumerate(components):
                if i >= j:
                    continue
                
                query_result = self.knowledge_graph_agent.query_relationships(
                    graph_name="arduino_components",
                    source=comp1,
                    target=comp2
                )
                
                if query_result['relationships']:
                    for rel in query_result['relationships']:
                        results.append({
                            'component1': comp1,
                            'component2': comp2,
                            'relation': rel.get('relation', 'unknown'),
                            'details': rel.get('details', {})
                        })
        
        for comp in components:
            related_components = self.knowledge_graph_agent.find_related_entities(
                graph_name="arduino_components",
                entity_name=comp,
                relation_type="compatible_with"
            )
            
            if related_components['entities']:
                for entity in related_components['entities']:
                    if entity not in components:
                        results.append({
                            'component1': comp,
                            'component2': entity,
                            'relation': 'recommended_accessory',
                            'details': {'suggested': True}
                        })
        
        return {
            'success': True,
            'components': components,
            'relationships': results,
            'relationship_count': len(results),
            'compatible': len(results) > 0 or len(components) <= 1
        }
    
    def analyze_component_troubleshooting(self, component_name, issue_description):
        """组件故障排除 - 使用知识图谱进行推理"""
        related_entities = self.knowledge_graph_agent.find_related_entities(
            graph_name="arduino_components",
            entity_name=component_name,
            relation_type=None
        )
        
        reasoning_result = self.knowledge_graph_agent.knowledge_reasoning(
            graph_name="arduino_components",
            query=f"{component_name} {issue_description}",
            max_results=5
        )
        
        troubleshooting_guide = self._generate_troubleshooting_guide(component_name, issue_description)
        
        return {
            'success': True,
            'component': component_name,
            'issue': issue_description,
            'related_components': related_entities.get('entities', []),
            'reasoning_results': reasoning_result.get('results', []),
            'troubleshooting_guide': troubleshooting_guide
        }
    
    def _generate_troubleshooting_guide(self, component, issue):
        """生成故障排除指南"""
        guides = {
            'DHT11': {
                'no_reading': [
                    {'step': '检查接线是否正确', 'action': '确认VCC接5V, GND接地, DATA接指定数字引脚'},
                    {'step': '检查传感器是否损坏', 'action': '尝试更换传感器或用万用表测试'},
                    {'step': '检查代码', 'action': '确认使用dht.begin()初始化，引脚定义正确'}
                ],
                'inaccurate': [
                    {'step': '检查工作环境', 'action': 'DHT11不适用于极端温度环境(-20~60°C)'},
                    {'step': '校准传感器', 'action': '与标准温度计对比校准'},
                    {'step': '考虑升级', 'action': 'DHT22精度更高，建议考虑升级'}
                ]
            },
            'HC-SR04': {
                'no_reading': [
                    {'step': '检查接线', 'action': '确认TRIG和ECHO引脚连接正确'},
                    {'step': '检查供电', 'action': '确保使用5V供电，避免3.3V'},
                    {'step': '检查障碍物', 'action': '传感器前方需有障碍物(2cm-4m范围内)'}
                ],
                'inaccurate': [
                    {'step': '检查测量角度', 'action': '确保传感器垂直对准目标'},
                    {'step': '检查环境', 'action': '避免在高温/高湿度环境使用'},
                    {'step': '增加采样次数', 'action': '多次测量取平均值'}
                ]
            },
            'SG90': {
                'no_movement': [
                    {'step': '检查接线', 'action': '确认红(5V)、棕(GND)、橙(信号)线连接正确'},
                    {'step': '检查信号引脚', 'action': '确保使用PWM引脚(3,5,6,9,10,11)'},
                    {'step': '检查代码', 'action': '确认使用servo.attach()和servo.write()'}
                ],
                'jitter': [
                    {'step': '增加供电', 'action': '舵机可能需要外部电源'},
                    {'step': '降低转速', 'action': '增加delay()时间，平滑转动'},
                    {'step': '检查机械结构', 'action': '确保舵机负载适中'}
                ]
            },
            'LCD 1602': {
                'no_display': [
                    {'step': '检查背光', 'action': '确认A引脚接5V, K引脚接地'},
                    {'step': '检查对比度', 'action': '调整电位器旋钮'},
                    {'step': '检查接线', 'action': '确认RS,EN,D4-D7引脚连接正确'}
                ],
                'garbled_text': [
                    {'step': '检查初始化', 'action': '确认使用lcd.begin(16,2)'},
                    {'step': '检查波特率', 'action': '确保串口波特率一致'},
                    {'step': '检查库版本', 'action': '使用最新版本的LiquidCrystal库'}
                ]
            },
            'ESP8266': {
                'no_connection': [
                    {'step': '检查WiFi密码', 'action': '确认SSID和密码正确'},
                    {'step': '检查供电', 'action': '使用稳定的3.3V供电'},
                    {'step': '检查串口', 'action': '确认串口连接正确，波特率115200'}
                ],
                'disconnects': [
                    {'step': '增加电源稳定性', 'action': '使用大电容滤波'},
                    {'step': '检查信号强度', 'action': '靠近路由器或使用外置天线'},
                    {'step': '设置保活', 'action': '添加WiFi保活机制'}
                ]
            }
        }
        
        component_lower = component.lower()
        issue_lower = issue.lower()
        
        for comp_name, issues in guides.items():
            if comp_name.lower() in component_lower:
                for issue_key, steps in issues.items():
                    if issue_key in issue_lower:
                        return steps
        
        return [
            {'step': '检查硬件连接', 'action': '确认所有引脚连接正确'},
            {'step': '检查电源', 'action': '确保供电稳定且电压正确'},
            {'step': '检查代码', 'action': '审查代码逻辑和引脚定义'},
            {'step': '查阅文档', 'action': '参考组件官方文档'}
        ]
    
    def create_build_pipeline(self, project_id, code):
        """创建Arduino构建流水线 - 使用DevOps Agent"""
        pipeline_config = {
            'project_id': project_id,
            'stages': [
                {'name': 'syntax_check', 'type': 'validation'},
                {'name': 'compile', 'type': 'build'},
                {'name': 'simulate', 'type': 'test'},
                {'name': 'deploy', 'type': 'deploy'}
            ],
            'arduino_board': 'uno',
            'port': '/dev/tty.usbmodem14101',
            'baud_rate': 9600
        }
        
        pipeline_result = self.devops_agent.ci_cd_pipeline(
            pipeline_config=pipeline_config,
            code=code
        )
        
        validation_result = self.devops_agent.validate_code(code)
        
        return {
            'success': True,
            'project_id': project_id,
            'pipeline_config': pipeline_config,
            'pipeline_result': pipeline_result,
            'validation': validation_result,
            'status': 'completed' if pipeline_result.get('success') else 'failed'
        }
    
    def analyze_camera_image(self, image_data, processing_type='object_detection'):
        """分析摄像头图像 - 使用图像处理Agent（支持ESP32-CAM）"""
        processing_result = self.image_processing_agent.process_image(
            image_data=image_data,
            operation=processing_type
        )
        
        return {
            'success': True,
            'processing_type': processing_type,
            'result': processing_result,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def vision_based_control(self, image_data, target_color=None, target_object=None):
        """视觉控制 - 根据图像分析结果生成Arduino控制代码"""
        analysis_result = self.image_processing_agent.process_image(
            image_data=image_data,
            operation='object_detection'
        )
        
        control_code = self._generate_vision_control_code(analysis_result, target_color, target_object)
        
        return {
            'success': True,
            'analysis': analysis_result,
            'control_code': control_code,
            'recommendations': self._generate_vision_recommendations(analysis_result)
        }
    
    def _generate_vision_control_code(self, analysis, target_color, target_object):
        """生成视觉控制代码"""
        detected_objects = analysis.get('objects', [])
        
        code_parts = []
        code_parts.append('#include <Servo.h>')
        code_parts.append('')
        code_parts.append('Servo panServo;')
        code_parts.append('Servo tiltServo;')
        code_parts.append('')
        code_parts.append('int panPin = 9;')
        code_parts.append('int tiltPin = 10;')
        code_parts.append('int ledPin = 13;')
        code_parts.append('')
        code_parts.append('void setup() {')
        code_parts.append('  panServo.attach(panPin);')
        code_parts.append('  tiltServo.attach(tiltPin);')
        code_parts.append('  pinMode(ledPin, OUTPUT);')
        code_parts.append('  Serial.begin(9600);')
        code_parts.append('}')
        code_parts.append('')
        code_parts.append('void loop() {')
        
        if detected_objects:
            for obj in detected_objects[:3]:
                obj_name = obj.get('name', 'unknown')
                confidence = obj.get('confidence', 0)
                if confidence > 0.5:
                    code_parts.append(f'  // 检测到 {obj_name} (置信度: {confidence:.2f})')
                    code_parts.append('  digitalWrite(ledPin, HIGH);')
                    code_parts.append('  delay(500);')
                    code_parts.append('  digitalWrite(ledPin, LOW);')
        
        code_parts.append('  delay(1000);')
        code_parts.append('}')
        
        return '\n'.join(code_parts)
    
    def _generate_vision_recommendations(self, analysis):
        """生成视觉项目建议"""
        recommendations = []
        
        objects = analysis.get('objects', [])
        if not objects:
            recommendations.append('未检测到物体，建议调整摄像头位置或光线条件')
        elif len(objects) > 5:
            recommendations.append('检测到多个物体，建议增加过滤逻辑')
        
        return recommendations
    
    def get_enhanced_learning_path(self, user_id):
        """增强版学习路径 - 结合AI能力推荐学习内容"""
        self.cursor.execute('''
            SELECT * FROM arduino_projects WHERE user_id = ?
        ''', (user_id,))
        projects = [dict(row) for row in self.cursor.fetchall()]
        
        completed_projects = [p for p in projects if p.get('status') == 'completed']
        
        skill_assessment = {
            'digital_io': {'score': 0, 'level': 'beginner'},
            'analog_io': {'score': 0, 'level': 'beginner'},
            'sensors': {'score': 0, 'level': 'beginner'},
            'actuators': {'score': 0, 'level': 'beginner'},
            'displays': {'score': 0, 'level': 'beginner'},
            'communication': {'score': 0, 'level': 'beginner'},
            'ai_integration': {'score': 0, 'level': 'beginner'}
        }
        
        for project in projects:
            desc = (project.get('name', '') + ' ' + project.get('description', '')).lower()
            if any(k in desc for k in ['led', 'button', 'digital']):
                skill_assessment['digital_io']['score'] += 1
            if any(k in desc for k in ['potentiometer', 'analog']):
                skill_assessment['analog_io']['score'] += 1
            if any(k in desc for k in ['dht', '温湿度', '超声波']):
                skill_assessment['sensors']['score'] += 1
            if any(k in desc for k in ['servo', '舵机', '蜂鸣器']):
                skill_assessment['actuators']['score'] += 1
            if any(k in desc for k in ['lcd', '显示']):
                skill_assessment['displays']['score'] += 1
            if any(k in desc for k in ['wifi', '蓝牙', 'esp']):
                skill_assessment['communication']['score'] += 1
            if any(k in desc for k in ['ai', '智能', '预测', '识别']):
                skill_assessment['ai_integration']['score'] += 1
        
        for skill in skill_assessment:
            score = skill_assessment[skill]['score']
            if score == 0:
                skill_assessment[skill]['level'] = 'beginner'
            elif score == 1:
                skill_assessment[skill]['level'] = 'basic'
            elif score == 2:
                skill_assessment[skill]['level'] = 'intermediate'
            else:
                skill_assessment[skill]['level'] = 'advanced'
        
        ai_projects = [
            {
                'name': 'AI传感器故障预测',
                'description': '使用机器学习预测传感器故障',
                'difficulty': 'advanced',
                'skills': ['sensors', 'ai_integration'],
                'agent': 'data_science',
                'estimated_time': '45分钟'
            },
            {
                'name': '数字孪生模拟',
                'description': '在虚拟环境中模拟Arduino项目',
                'difficulty': 'advanced',
                'skills': ['digital_io', 'ai_integration'],
                'agent': 'digital_twin',
                'estimated_time': '40分钟'
            },
            {
                'name': '视觉识别小车',
                'description': '使用ESP32-CAM实现物体识别',
                'difficulty': 'expert',
                'skills': ['actuators', 'communication', 'ai_integration'],
                'agent': 'image_processing',
                'estimated_time': '60分钟'
            },
            {
                'name': '智能组件推荐系统',
                'description': '使用知识图谱推荐硬件组件',
                'difficulty': 'intermediate',
                'skills': ['digital_io', 'ai_integration'],
                'agent': 'knowledge_graph',
                'estimated_time': '30分钟'
            },
            {
                'name': '自动化构建部署',
                'description': '自动化Arduino项目构建和上传',
                'difficulty': 'intermediate',
                'skills': ['communication', 'ai_integration'],
                'agent': 'devops',
                'estimated_time': '35分钟'
            }
        ]
        
        weak_skills = [s for s in skill_assessment if skill_assessment[s]['level'] == 'beginner']
        recommended_projects = []
        
        for project in ai_projects:
            required_skills = project['skills']
            if all(skill_assessment[s]['level'] != 'beginner' or s == 'ai_integration' for s in required_skills):
                recommended_projects.append(project)
        
        return {
            'success': True,
            'user_id': user_id,
            'total_projects': len(projects),
            'completed_projects': len(completed_projects),
            'skill_assessment': skill_assessment,
            'weak_skills': weak_skills,
            'ai_projects': ai_projects,
            'recommended_projects': recommended_projects[:3],
            'learning_stage': self._determine_learning_stage(skill_assessment)
        }
    
    def _determine_learning_stage(self, skills):
        """确定学习阶段"""
        ai_score = skills['ai_integration']['score']
        
        if ai_score == 0:
            return 'foundation'
        elif ai_score == 1:
            return 'exploring_ai'
        elif ai_score == 2:
            return 'ai_practitioner'
        else:
            return 'ai_expert'
    
    def close(self):
        """关闭连接"""
        self.conn.close()
