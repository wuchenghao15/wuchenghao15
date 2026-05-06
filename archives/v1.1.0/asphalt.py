# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from app.models.asphalt import AsphaltType, AsphaltPerformance, AsphaltMaintenance, AsphaltUpgrade, init_asphalt_tables
from app.utils.logging import logger

# 创建沥青维护和升级系统蓝图
asphalt_bp = Blueprint('asphalt', __name__, url_prefix='/asphalt')

@asphalt_bp.route('/init')
def init_asphalt_system():
    """初始化沥青维护和升级系统，创建相关表"""
    try:
        init_asphalt_tables()
        return jsonify({'success': True, 'message': '沥青维护和升级系统初始化完成'}), 200
    except Exception as e:
        logger.error(f"初始化沥青系统失败: {str(e)}")
        return jsonify({'success': False, 'message': f'初始化失败: {str(e)}}), 500'

# 沥青类型管理路由
@asphalt_bp.route('/types', methods=['GET'])
def get_asphalt_types():
    """获取所有沥青类型"""
        asphalt_types = AsphaltType.get_all()
        return jsonify({
            'success': True,
            'data': [type.to_dict() for type in asphalt_types]
        }), 200
    except Exception as e:
        logger.error(f"获取沥青类型失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}}), 500

@asphalt_bp.route('/types/<string:type_id>', methods=['GET'])
def get_asphalt_type(type_id):
    """获取特定沥青类型"""
        asphalt_type = AsphaltType.get_by_id(type_id)
        if asphalt_type:
            return jsonify({'success': True, 'data': asphalt_type.to_dict()}), 200
        else:
            return jsonify({'success': False, 'message': '沥青类型不存在'}), 404
    except Exception as e:
        logger.error(f"获取沥青类型 {type_id} 失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}}), 500

@asphalt_bp.route('/types', methods=['POST'])
def create_asphalt_type():
    """创建新的沥青类型"""
        data = request.get_json()
        asphalt_type = AsphaltType(
            type_id=data.get('type_id'),
            name=data.get('name'),
            description=data.get('description'),
            properties=data.get('properties'),
            status=data.get('status', 'active')
        )
        result = asphalt_type.save()
        if result:
            return jsonify({'success': True, 'data': result.to_dict()}), 201
        else:
            return jsonify({'success': False, 'message': '创建失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}}), 500

@asphalt_bp.route('/types/<string:type_id>', methods=['PUT'])
def update_asphalt_type(type_id):
    """更新沥青类型"""
        asphalt_type = AsphaltType.get_by_id(type_id)
        if not asphalt_type:
            return jsonify({'success': False, 'message': '沥青类型不存在'}), 404

        asphalt_type.name = data.get('name', asphalt_type.name)
        asphalt_type.description = data.get('description', asphalt_type.description)
        asphalt_type.properties = data.get('properties', asphalt_type.properties)

        result = asphalt_type.save()
    except Exception as e:
        logger.error(f"更新沥青类型 {type_id} 失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}}), 500

@asphalt_bp.route('/types/<string:type_id>', methods=['DELETE'])
def delete_asphalt_type(type_id):
        asphalt_type = AsphaltType.get_by_id(type_id)
        if not asphalt_type:
            return jsonify({'success': False, 'message': '沥青类型不存在'}), 404

        asphalt_type.delete()
    except Exception as e:
        logger.error(f"删除沥青类型 {type_id} 失败: {str(e)}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}}), 500

@asphalt_bp.route('/performance', methods=['GET'])
def get_asphalt_performance():
        asphalt_type_id = request.args.get('asphalt_type_id')
        if asphalt_type_id:
            performance_data = AsphaltPerformance.get_by_type(asphalt_type_id)
        else:
            # 暂时不支持获取所有性能数据，需要按类型过滤
            return jsonify({'success': False, 'message': '必须提供asphalt_type_id参数'}), 400

        return jsonify({
            'success': True,
            'data': [data.to_dict() for data in performance_data]
        }), 200
        logger.error(f"获取沥青性能数据失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}}), 500

@asphalt_bp.route('/performance/latest/<string:asphalt_type_id>', methods=['GET'])
def get_latest_asphalt_performance(asphalt_type_id):
    """获取特定沥青类型的最新性能数据"""
        performance_data = AsphaltPerformance.get_latest_by_type(asphalt_type_id)
        if performance_data:
            return jsonify({'success': True, 'data': performance_data.to_dict()}), 200
        else:
            return jsonify({'success': False, 'message': '没有找到性能数据'}), 404
    except Exception as e:
        logger.error(f"获取最新沥青性能数据失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}}), 500

@asphalt_bp.route('/performance', methods=['POST'])
def create_asphalt_performance():
    """创建沥青性能数据"""
        from app.ai.self_learning_system import self_learning_system
        from app.ai.monitoring import ai_monitor

        data = request.get_json()
        performance_id = f"perf_{uuid.uuid4().hex[:8]}"
        asphalt_performance = AsphaltPerformance(
            performance_id=performance_id,
            asphalt_type_id=data.get('asphalt_type_id'),
            performance_data=data.get('performance_data'),
            location=data.get('location'),
            sample_id=data.get('sample_id')
        )

        result = asphalt_performance.save()

        # 将数据传递给自学习系统
        self_learning_system.add_asphalt_performance_data({
            'asphalt_type_id': data.get('asphalt_type_id'),
            'location': data.get('location'),
            'sample_id': data.get('sample_id')
        })

        # 将数据传递给监控系统
        ai_monitor.log_asphalt_performance_data(
            asphalt_type_id=data.get('asphalt_type_id'),
            performance_data=data.get('performance_data'),
            location=data.get('location'),
        )

        return jsonify({'success': True, 'data': result.to_dict()}), 201
    except Exception as e:
        logger.error(f"创建沥青性能数据失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}}), 500

# 沥青维护记录管理路由
@asphalt_bp.route('/maintenance', methods=['GET'])
def get_asphalt_maintenance():
    """获取沥青维护记录"""
        asphalt_type_id = request.args.get('asphalt_type_id')
        if asphalt_type_id:
            maintenance_records = AsphaltMaintenance.get_by_type(asphalt_type_id)
        else:
            # 暂时不支持获取所有维护记录，需要按类型过滤
        return jsonify({
            'data': [record.to_dict() for record in maintenance_records]
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}}), 500
@asphalt_bp.route('/maintenance', methods=['POST'])
def create_asphalt_maintenance():
    """创建沥青维护记录"""
        import uuid
        from app.ai.self_learning_system import self_learning_system

        data = request.get_json()
        maintenance_id = f"maint_{uuid.uuid4().hex[:8]}"
            maintenance_id=maintenance_id,
            maintenance_type=data.get('maintenance_type'),
            description=data.get('description'),
            performed_by=data.get('performed_by'),
            result=data.get('result'),
        )

        result = asphalt_maintenance.save()

        # 将数据传递给自学习系统
        self_learning_system.add_asphalt_maintenance_data({
            'asphalt_type_id': data.get('asphalt_type_id'),
            'maintenance_type': data.get('maintenance_type'),
            'performed_by': data.get('performed_by'),
            'result': data.get('result'),
            'cost': data.get('cost')
        })

        return jsonify({'success': True, 'data': result.to_dict()}), 201
        logger.error(f"创建沥青维护记录失败: {str(e)}")
# 沥青升级记录管理路由
@asphalt_bp.route('/upgrades', methods=['GET'])
def get_asphalt_upgrades():
        asphalt_type_id = request.args.get('asphalt_type_id')
        if asphalt_type_id:
            upgrade_records = AsphaltUpgrade.get_by_type(asphalt_type_id)
            # 暂时不支持获取所有升级记录，需要按类型过滤
            return jsonify({'success': False, 'message': '必须提供asphalt_type_id参数'}), 400

        return jsonify({
            'success': True,
            'data': [record.to_dict() for record in upgrade_records]
        }), 200
    except Exception as e:
        logger.error(f"获取沥青升级记录失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}}), 500

@asphalt_bp.route('/upgrades', methods=['POST'])
    """创建沥青升级记录"""
        import uuid
        from app.ai.self_learning_system import self_learning_system

        data = request.get_json()
        upgrade_id = f"upgrade_{uuid.uuid4().hex[:8]}"
        asphalt_upgrade = AsphaltUpgrade(
            upgrade_id=upgrade_id,
            asphalt_type_id=data.get('asphalt_type_id'),
            upgrade_type=data.get('upgrade_type'),
            description=data.get('description'),
            performed_by=data.get('performed_by'),
            cost=data.get('cost'),
            before_version=data.get('before_version'),
        )

        result = asphalt_upgrade.save()

        # 将数据传递给自学习系统
            'asphalt_type_id': data.get('asphalt_type_id'),
            'upgrade_type': data.get('upgrade_type'),
            'description': data.get('description'),
            'result': data.get('result'),
            'cost': data.get('cost'),
            'before_version': data.get('before_version'),
            'after_version': data.get('after_version')
        })

        return jsonify({'success': True, 'data': result.to_dict()}), 201
    except Exception as e:
        logger.error(f"创建沥青升级记录失败: {str(e)}")

# 沥青性能报告路由
@asphalt_bp.route('/reports/performance', methods=['GET'])
    """获取沥青性能报告"""
        from app.ai.monitoring import ai_monitor
        # 暂时返回监控指标
        performance_metrics = ai_monitor.asphalt_performance_metrics
        return jsonify({
            'success': True,
            'data': performance_metrics
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}}), 500

# 沥青维护和升级系统主页
@asphalt_bp.route('/')
def asphalt_home():
    """沥青维护和升级系统主页"""
    return render_template('asphalt/index.html')
