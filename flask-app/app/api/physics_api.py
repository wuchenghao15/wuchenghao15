# -*- coding: utf-8 -*-
"""物理引擎和数学模型API路由"""
from flask import Blueprint, request, jsonify
import json
import logging

from app.services.physics_engine_service import physics_engine_service
from app.services.particle_engine_service import particle_engine_service
from app.services.render_engine_service import render_engine_service

logger = logging.getLogger(__name__)

physics_api_bp = Blueprint('physics_api', __name__, url_prefix='/api/physics')

@physics_api_bp.route('/formulas', methods=['GET'])
def get_physics_formulas():
    """获取物理公式列表"""
    try:
        keyword = request.args.get('keyword', '')
        category = request.args.get('category', '')
        physics_type = request.args.get('type', '')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        formulas = physics_engine_service.search_physics_formulas(
            keyword, category, physics_type, limit, offset
        )
        
        return jsonify({
            'success': True,
            'data': formulas,
            'count': len(formulas),
            'message': '获取物理公式列表成功'
        })
    except Exception as e:
        logger.error(f"获取物理公式列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/formulas/<int:formula_id>', methods=['GET'])
def get_physics_formula(formula_id):
    """获取单个物理公式"""
    try:
        formula = physics_engine_service.get_physical_formula(formula_id)
        if formula:
            return jsonify({'success': True, 'data': formula})
        return jsonify({'success': False, 'message': '公式不存在'}), 404
    except Exception as e:
        logger.error(f"获取物理公式失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/formulas', methods=['POST'])
def add_physics_formula():
    """添加物理公式"""
    try:
        data = request.get_json()
        
        if 'name' not in data or 'formula' not in data:
            return jsonify({'success': False, 'message': '缺少必要字段: name, formula'}), 400
        
        formula_id = physics_engine_service.add_physical_formula(
            name=data['name'],
            formula=data['formula'],
            latex=data.get('latex', ''),
            category=data.get('category', ''),
            physics_type=data.get('physics_type', 'mechanics'),
            description=data.get('description', ''),
            variables=data.get('variables'),
            constants=data.get('constants'),
            examples=data.get('examples'),
            derivation_steps=data.get('derivation_steps'),
            units=data.get('units'),
            difficulty_level=data.get('difficulty_level', 1),
            source=data.get('source', '')
        )
        
        return jsonify({
            'success': True,
            'data': {'id': formula_id},
            'message': '物理公式添加成功'
        }), 201
    except Exception as e:
        logger.error(f"添加物理公式失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/formulas/<int:formula_id>/calculate', methods=['POST'])
def calculate_physics_formula(formula_id):
    """计算物理公式"""
    try:
        data = request.get_json()
        inputs = data.get('inputs', {})
        
        if not inputs:
            return jsonify({'success': False, 'message': '请提供输入参数'}), 400
        
        result = physics_engine_service.calculate_formula(formula_id, inputs)
        
        if result.get('success'):
            return jsonify(result)
        return jsonify(result), 400
    except Exception as e:
        logger.error(f"计算物理公式失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/constants', methods=['GET'])
def get_physics_constants():
    """获取物理常数列表"""
    try:
        category = request.args.get('category', '')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        constants = physics_engine_service.get_constants(category, limit, offset)
        
        return jsonify({
            'success': True,
            'data': constants,
            'count': len(constants),
            'message': '获取物理常数列表成功'
        })
    except Exception as e:
        logger.error(f"获取物理常数列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/constants/<name>', methods=['GET'])
def get_physics_constant(name):
    """获取单个物理常数"""
    try:
        constant = physics_engine_service.get_constant_by_name(name)
        if constant:
            return jsonify({'success': True, 'data': constant})
        return jsonify({'success': False, 'message': '常数不存在'}), 404
    except Exception as e:
        logger.error(f"获取物理常数失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/simulate/pendulum', methods=['POST'])
def simulate_pendulum():
    """单摆模拟"""
    try:
        data = request.get_json()
        
        length = float(data.get('length', 1.0))
        initial_angle = float(data.get('initial_angle', 30.0))
        duration = float(data.get('duration', 10.0))
        time_step = float(data.get('time_step', 0.01))
        gravity = float(data.get('gravity', 9.81))
        
        if length <= 0:
            return jsonify({'success': False, 'message': '摆长必须大于0'}), 400
        
        result = physics_engine_service.simulate_simple_pendulum(
            length, initial_angle, duration, time_step, gravity
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"单摆模拟失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/simulate/projectile', methods=['POST'])
def simulate_projectile():
    """抛体运动模拟"""
    try:
        data = request.get_json()
        
        v0 = float(data.get('v0', 10.0))
        angle = float(data.get('angle', 45.0))
        height = float(data.get('height', 0.0))
        gravity = float(data.get('gravity', 9.81))
        time_step = float(data.get('time_step', 0.01))
        
        if v0 <= 0:
            return jsonify({'success': False, 'message': '初速度必须大于0'}), 400
        
        result = physics_engine_service.simulate_projectile_motion(
            v0, angle, height, gravity, time_step
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"抛体运动模拟失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/math-models', methods=['GET'])
def get_math_models():
    """获取数学模型列表"""
    try:
        keyword = request.args.get('keyword', '')
        category = request.args.get('category', '')
        model_type = request.args.get('type', '')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        models = physics_engine_service.search_math_models(
            keyword, category, model_type, limit, offset
        )
        
        return jsonify({
            'success': True,
            'data': models,
            'count': len(models),
            'message': '获取数学模型列表成功'
        })
    except Exception as e:
        logger.error(f"获取数学模型列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/math-models/<int:model_id>', methods=['GET'])
def get_math_model(model_id):
    """获取单个数学模型"""
    try:
        model = physics_engine_service.get_math_model(model_id)
        if model:
            return jsonify({'success': True, 'data': model})
        return jsonify({'success': False, 'message': '数学模型不存在'}), 404
    except Exception as e:
        logger.error(f"获取数学模型失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/math-models', methods=['POST'])
def add_math_model():
    """添加数学模型"""
    try:
        data = request.get_json()
        
        if 'name' not in data:
            return jsonify({'success': False, 'message': '缺少必要字段: name'}), 400
        
        model_id = physics_engine_service.add_math_model(
            name=data['name'],
            model_type=data.get('model_type', 'equation'),
            description=data.get('description', ''),
            equations=data.get('equations'),
            variables=data.get('variables'),
            parameters=data.get('parameters'),
            category=data.get('category', ''),
            difficulty_level=data.get('difficulty_level', 1),
            source=data.get('source', ''),
            examples=data.get('examples')
        )
        
        return jsonify({
            'success': True,
            'data': {'id': model_id},
            'message': '数学模型添加成功'
        }), 201
    except Exception as e:
        logger.error(f"添加数学模型失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/stats', methods=['GET'])
def get_physics_stats():
    """获取物理引擎统计信息"""
    try:
        stats = physics_engine_service.get_physics_stats()
        
        return jsonify({
            'success': True,
            'data': stats,
            'message': '获取统计信息成功'
        })
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/particles/types', methods=['GET'])
def get_particle_types():
    """获取粒子类型列表"""
    try:
        types = particle_engine_service.get_particle_types()
        
        return jsonify({
            'success': True,
            'data': types,
            'count': len(types),
            'message': '获取粒子类型列表成功'
        })
    except Exception as e:
        logger.error(f"获取粒子类型列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/particles/systems', methods=['GET'])
def get_particle_systems():
    """获取粒子系统列表"""
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        systems = particle_engine_service.get_particle_systems(limit, offset)
        
        return jsonify({
            'success': True,
            'data': systems,
            'count': len(systems),
            'message': '获取粒子系统列表成功'
        })
    except Exception as e:
        logger.error(f"获取粒子系统列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/particles/systems/<int:system_id>', methods=['GET'])
def get_particle_system(system_id):
    """获取单个粒子系统"""
    try:
        system = particle_engine_service.get_particle_system(system_id)
        if system:
            particles = particle_engine_service.get_particles(system_id)
            system['particles'] = particles
            return jsonify({'success': True, 'data': system})
        return jsonify({'success': False, 'message': '粒子系统不存在'}), 404
    except Exception as e:
        logger.error(f"获取粒子系统失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/particles/systems', methods=['POST'])
def create_particle_system():
    """创建粒子系统"""
    try:
        data = request.get_json()
        
        if 'name' not in data:
            return jsonify({'success': False, 'message': '缺少必要字段: name'}), 400
        
        system_id = particle_engine_service.create_particle_system(
            name=data['name'],
            description=data.get('description', ''),
            integration_method=data.get('integration_method', 'euler'),
            time_step=data.get('time_step', 0.001),
            duration=data.get('duration', 1.0),
            boundary_type=data.get('boundary_type', 'none'),
            boundary_x_min=data.get('boundary_x_min', -10.0),
            boundary_x_max=data.get('boundary_x_max', 10.0),
            boundary_y_min=data.get('boundary_y_min', -10.0),
            boundary_y_max=data.get('boundary_y_max', 10.0),
            gravity=data.get('gravity', 0.0),
            damping=data.get('damping', 0.0)
        )
        
        return jsonify({
            'success': True,
            'data': {'id': system_id},
            'message': '粒子系统创建成功'
        }), 201
    except Exception as e:
        logger.error(f"创建粒子系统失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/particles/systems/<int:system_id>/particles', methods=['POST'])
def add_particle():
    """添加粒子"""
    try:
        data = request.get_json()
        system_id = int(request.view_args['system_id'])
        
        x = float(data.get('x', 0.0))
        y = float(data.get('y', 0.0))
        z = float(data.get('z', 0.0))
        vx = float(data.get('vx', 0.0))
        vy = float(data.get('vy', 0.0))
        vz = float(data.get('vz', 0.0))
        
        particle_id = particle_engine_service.add_particle(
            system_id=system_id,
            x=x,
            y=y,
            z=z,
            vx=vx,
            vy=vy,
            vz=vz,
            mass=data.get('mass', 1.0),
            charge=data.get('charge', 0.0),
            radius=data.get('radius', 0.5),
            lifetime=data.get('lifetime', 0.0),
            color=data.get('color', '#FF5722'),
            type_id=data.get('type_id'),
            name=data.get('name', '')
        )
        
        return jsonify({
            'success': True,
            'data': {'id': particle_id},
            'message': '粒子添加成功'
        }), 201
    except Exception as e:
        logger.error(f"添加粒子失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/particles/systems/<int:system_id>/force-fields', methods=['POST'])
def add_force_field():
    """添加力场"""
    try:
        data = request.get_json()
        system_id = int(request.view_args['system_id'])
        
        field_id = particle_engine_service.add_force_field(
            system_id=system_id,
            name=data.get('name', '力场'),
            field_type=data.get('field_type', 'gravity'),
            magnitude=data.get('magnitude', 9.81),
            direction=data.get('direction', [0, -1, 0]),
            origin=data.get('origin', [0, 0, 0]),
            parameters=data.get('parameters', {})
        )
        
        return jsonify({
            'success': True,
            'data': {'id': field_id},
            'message': '力场添加成功'
        }), 201
    except Exception as e:
        logger.error(f"添加力场失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/particles/systems/<int:system_id>/run', methods=['POST'])
def run_particle_simulation():
    """运行粒子模拟"""
    try:
        system_id = int(request.view_args['system_id'])
        
        result = particle_engine_service.run_simulation(system_id)
        
        if result.get('success'):
            return jsonify(result)
        return jsonify(result), 400
    except Exception as e:
        logger.error(f"运行粒子模拟失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/particles/systems/<int:system_id>', methods=['DELETE'])
def delete_particle_system(system_id):
    """删除粒子系统"""
    try:
        success = particle_engine_service.delete_particle_system(system_id)
        
        if success:
            return jsonify({'success': True, 'message': '粒子系统删除成功'})
        return jsonify({'success': False, 'message': '删除失败'}), 400
    except Exception as e:
        logger.error(f"删除粒子系统失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/particles/presets/solar-system', methods=['POST'])
def create_preset_solar_system():
    """创建太阳系预设场景"""
    try:
        data = request.get_json()
        name = data.get('name', '太阳系')
        duration = float(data.get('duration', 1000.0))
        
        system_id = particle_engine_service.create_preset_solar_system(name, duration)
        
        return jsonify({
            'success': True,
            'data': {'id': system_id},
            'message': '太阳系场景创建成功'
        }), 201
    except Exception as e:
        logger.error(f"创建太阳系场景失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/particles/presets/gas-molecules', methods=['POST'])
def create_preset_gas_molecules():
    """创建气体分子预设场景"""
    try:
        data = request.get_json()
        name = data.get('name', '气体分子')
        count = int(data.get('count', 50))
        duration = float(data.get('duration', 1.0))
        
        system_id = particle_engine_service.create_preset_gas_molecules(name, count, duration)
        
        return jsonify({
            'success': True,
            'data': {'id': system_id},
            'message': '气体分子场景创建成功'
        }), 201
    except Exception as e:
        logger.error(f"创建气体分子场景失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/particles/presets/electric-field', methods=['POST'])
def create_preset_electric_field():
    """创建电场预设场景"""
    try:
        data = request.get_json()
        name = data.get('name', '电场中的带电粒子')
        duration = float(data.get('duration', 1.0))
        
        system_id = particle_engine_service.create_preset_electric_field(name, duration)
        
        return jsonify({
            'success': True,
            'data': {'id': system_id},
            'message': '电场场景创建成功'
        }), 201
    except Exception as e:
        logger.error(f"创建电场场景失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/particles/presets/magnetic-field', methods=['POST'])
def create_preset_magnetic_field():
    """创建磁场预设场景"""
    try:
        data = request.get_json()
        name = data.get('name', '磁场中的带电粒子')
        duration = float(data.get('duration', 1.0))
        
        system_id = particle_engine_service.create_preset_magnetic_field(name, duration)
        
        return jsonify({
            'success': True,
            'data': {'id': system_id},
            'message': '磁场场景创建成功'
        }), 201
    except Exception as e:
        logger.error(f"创建磁场场景失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/particles/presets/brownian-motion', methods=['POST'])
def create_preset_brownian_motion():
    """创建布朗运动预设场景"""
    try:
        data = request.get_json()
        name = data.get('name', '布朗运动')
        count = int(data.get('count', 20))
        duration = float(data.get('duration', 1.0))
        
        system_id = particle_engine_service.create_preset_brownian_motion(name, count, duration)
        
        return jsonify({
            'success': True,
            'data': {'id': system_id},
            'message': '布朗运动场景创建成功'
        }), 201
    except Exception as e:
        logger.error(f"创建布朗运动场景失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/particles/stats', methods=['GET'])
def get_particle_stats():
    """获取粒子引擎统计信息"""
    try:
        stats = particle_engine_service.get_particle_stats()
        
        return jsonify({
            'success': True,
            'data': stats,
            'message': '获取粒子引擎统计信息成功'
        })
    except Exception as e:
        logger.error(f"获取粒子引擎统计信息失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/render/particles', methods=['POST'])
def render_particles():
    """渲染粒子系统"""
    try:
        data = request.get_json()
        particles = data.get('particles', [])
        width = int(data.get('width', 800))
        height = int(data.get('height', 600))
        background = data.get('background')
        scale = float(data.get('scale', 1.0))
        show_grid = data.get('show_grid', True)
        show_labels = data.get('show_labels', True)
        trails = data.get('trails')
        return_svg = data.get('return_svg', True)
        return_data_uri = data.get('return_data_uri', False)
        
        svg = render_engine_service.render_particles(
            particles, width, height, background,
            scale, show_grid=show_grid,
            show_labels=show_labels, trails=trails
        )
        
        result = {'success': True, 'width': width, 'height': height}
        
        if return_svg:
            result['svg'] = svg
        if return_data_uri:
            result['data_uri'] = render_engine_service.render_svg_to_data_uri(svg)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"渲染粒子系统失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/render/particles/<int:system_id>', methods=['GET'])
def render_particle_system(system_id):
    """渲染粒子系统（从数据库读取）"""
    try:
        width = int(request.args.get('width', 800))
        height = int(request.args.get('height', 600))
        scale = float(request.args.get('scale', 1.0))
        show_grid = request.args.get('show_grid', 'true').lower() == 'true'
        show_labels = request.args.get('show_labels', 'true').lower() == 'true'
        
        system = particle_engine_service.get_particle_system(system_id)
        if not system:
            return jsonify({'success': False, 'message': '粒子系统不存在'}), 404
        
        particles = particle_engine_service.get_particles(system_id)
        
        svg = render_engine_service.render_particles(
            particles, width, height,
            scale=scale, show_grid=show_grid, show_labels=show_labels
        )
        
        result = {
            'success': True,
            'svg': svg,
            'width': width,
            'height': height,
            'system_id': system_id,
            'system_name': system.get('name', '')
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"渲染粒子系统失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/render/pendulum', methods=['POST'])
def render_pendulum():
    """渲染单摆"""
    try:
        data = request.get_json()
        length = float(data.get('length', 1.0))
        angle = float(data.get('angle', 30.0))
        width = int(data.get('width', 400))
        height = int(data.get('height', 500))
        scale = float(data.get('scale', 100.0))
        background = data.get('background')
        
        svg = render_engine_service.render_pendulum(
            length, angle, width, height, background, scale
        )
        
        return jsonify({
            'success': True,
            'svg': svg,
            'width': width,
            'height': height
        })
    except Exception as e:
        logger.error(f"渲染单摆失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/render/projectile', methods=['POST'])
def render_projectile():
    """渲染抛体运动"""
    try:
        data = request.get_json()
        v0 = float(data.get('v0', 10.0))
        angle = float(data.get('angle', 45.0))
        height = float(data.get('height', 0.0))
        gravity = float(data.get('gravity', 9.81))
        width = int(data.get('width', 800))
        height_px = int(data.get('height', 500))
        scale = float(data.get('scale', 5.0))
        background = data.get('background')
        show_trajectory = data.get('show_trajectory', True)
        show_vectors = data.get('show_vectors', True)
        
        svg = render_engine_service.render_projectile(
            v0, angle, height, gravity,
            width, height_px, background, scale,
            show_trajectory, show_vectors
        )
        
        return jsonify({
            'success': True,
            'svg': svg,
            'width': width,
            'height': height_px
        })
    except Exception as e:
        logger.error(f"渲染抛体运动失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/render/chart', methods=['POST'])
def render_chart():
    """渲染图表"""
    try:
        data = request.get_json()
        chart_data = data.get('data', {})
        chart_type = data.get('chart_type', 'line')
        width = int(data.get('width', 800))
        height = int(data.get('height', 500))
        background = data.get('background')
        title = data.get('title', '')
        x_label = data.get('x_label', '')
        y_label = data.get('y_label', '')
        show_legend = data.get('show_legend', True)
        colors = data.get('colors')
        
        svg = render_engine_service.render_chart(
            chart_data, chart_type, width, height, background,
            title, x_label, y_label, show_legend, colors
        )
        
        return jsonify({
            'success': True,
            'svg': svg,
            'width': width,
            'height': height,
            'chart_type': chart_type
        })
    except Exception as e:
        logger.error(f"渲染图表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/render/energy-chart/<int:system_id>', methods=['GET'])
def render_energy_chart(system_id):
    """渲染能量图表"""
    try:
        width = int(request.args.get('width', 800))
        height = int(request.args.get('height', 400))
        
        system = particle_engine_service.get_particle_system(system_id)
        if not system:
            return jsonify({'success': False, 'message': '粒子系统不存在'}), 404
        
        result = particle_engine_service.run_simulation(system_id)
        if not result.get('success'):
            return jsonify({'success': False, 'message': result.get('error', '模拟失败')}), 400
        
        energy_history = result.get('energy_history', [])
        
        svg = render_engine_service.render_energy_chart(
            energy_history, width, height
        )
        
        return jsonify({
            'success': True,
            'svg': svg,
            'width': width,
            'height': height,
            'data_points': len(energy_history)
        })
    except Exception as e:
        logger.error(f"渲染能量图表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@physics_api_bp.route('/render/svg-to-data-uri', methods=['POST'])
def svg_to_data_uri():
    """SVG转Data URI"""
    try:
        data = request.get_json()
        svg = data.get('svg', '')
        
        data_uri = render_engine_service.render_svg_to_data_uri(svg)
        
        return jsonify({
            'success': True,
            'data_uri': data_uri
        })
    except Exception as e:
        logger.error(f"SVG转Data URI失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
