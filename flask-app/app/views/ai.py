# -*- coding: utf-8 -*-
import time
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from app.ai.instances import ai_instance_manager
from app.ai.monitoring import ai_monitor
from app.ai.learning import ai_learning
from app.ai.ai_ensemble import AIEnsemble
from app.models.ai import AIInstance
from app.utils.logging import logger

# 导入用户状态检查装饰器
from app.views.main import check_user_status

# 创建蓝图
ai_bp = Blueprint('ai', __name__)

# 初始化AI集
ai_ensemble = AIEnsemble()

@ai_bp.route('/instances')
@check_user_status
def instances():
    """AI实例管理视图"""
    try:
        # 获取所有AI实例
        instances = ai_instance_manager.ai_instances
        instance_stats = ai_instance_manager.get_instance_stats()

        return render_template('ai_instances.html', instances=instances, stats=instance_stats)
    except Exception as e:
        logger.error(f"获取AI实例列表时发生错误: {str(e)}")
        flash('获取AI实例列表时发生错误', 'danger')
        return redirect(url_for('main.index'))

@ai_bp.route('/create_instance', methods=['POST'])
def create_instance():
    """创建AI实例"""
    try:
        ai_type = request.form.get('ai_type', 'general')

        # 创建AI实例
        ai_instance = ai_instance_manager.create_ai_instance(instance_id, ai_type)

        # 保存到数据库
        db_instance = AIInstance(
            instance_id=instance_id,
            ai_type=ai_type,
            status='active',
            config={}
        )
        db_instance.save()

        logger.info(f"创建AI实例成功: {instance_id}")
        flash('AI实例创建成功', 'success')
        return redirect(url_for('ai.instances'))
    except Exception as e:
        logger.error(f"创建AI实例时发生错误: {str(e)}")
        flash(f'创建AI实例时发生错误: {str(e)}', 'danger')
        return redirect(url_for('ai.instances'))

def delete_instance(instance_id):
    """删除AI实例"""
    try:
        # 从内存中删除

        # 从数据库中删除
        db_instance = AIInstance.get_by_id(instance_id)
        if db_instance:
            db_instance.delete()

        logger.info(f"删除AI实例成功: {instance_id}")
        flash('AI实例删除成功', 'success')
        return redirect(url_for('ai.instances'))
    except Exception as e:
        logger.error(f"删除AI实例时发生错误: {str(e)}")
        flash(f'删除AI实例时发生错误: {str(e)}', 'danger')

@ai_bp.route('/bind_instance/<instance_id>/<user_id>')
def bind_instance(instance_id, user_id):
    try:
        # 绑定实例
        ai_instance_manager.bind_ai_instance(user_id, instance_id)
        # 更新数据库
        db_instance = AIInstance.get_by_id(instance_id)
        if db_instance:
            db_instance.bind_to_user(int(user_id))

        logger.info(f"AI实例 {instance_id} 绑定到用户 {user_id} 成功")
        flash('AI实例绑定成功', 'success')
        return redirect(url_for('ai.instances'))
    except Exception as e:
        logger.error(f"绑定AI实例时发生错误: {str(e)}")
        return redirect(url_for('ai.instances'))

@ai_bp.route('/add_learning_data', methods=['POST'])
def add_learning_data():
    try:
        data = request.get_json()
        ai_learning.add_learning_data(data)

        return jsonify({'success': True, 'message': '学习数据添加成功'})
    except Exception as e:
        logger.error(f"添加学习数据时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'添加学习数据时发生错误: {str(e)}'}), 500

@ai_bp.route('/update_learning_config', methods=['POST'])
def update_learning_config():
    """更新学习配置"""
    try:
        config = request.get_json()
        ai_learning.update_learning_config(config)

        logger.info(f"更新学习配置成功")
    except Exception as e:
        logger.error(f"更新学习配置时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'更新学习配置时发生错误: {str(e)}'}), 500

@ai_bp.route('/upgrade_instances', methods=['POST'])
def upgrade_instances():
    """升级所有AI实例"""
    try:
        # 检查用户权限，只有管理员可以升级AI实例
        user_role = session.get('user_level')
        if user_role not in ['hardware_vikey_admin', 'super_admin', 'admin']:
            return jsonify({'success': False, 'message': '权限不足，只有管理员可以升级AI实例'}), 403


        # 1. 获取所有数据库中的AI实例
        db_instances = AIInstance.get_all_instances()
        upgraded_count = 0
        upgrade_failed = 0

        for instance in db_instances:
            try:
                # 2. 更新AI实例配置
                # 这里可以根据需要添加具体的升级逻辑
                # 例如：更新模型版本、添加新功能配置、优化现有参数等

                # 示例升级逻辑：添加升级标记和版本信息
                updated_config['upgrade_time'] = request.json.get('upgrade_time', time.time())
                updated_config['version'] = request.json.get('version', '1.0.0')
                updated_config['last_upgraded'] = time.strftime("%Y-%m-%d %H:%M:%S")

                # 添加新的配置项
                if 'enhanced_features' not in updated_config:
                    updated_config['enhanced_features'] = {
                        'auto_learning': True,
                        'real_time_monitoring': True,
                        'adaptive_optimization': True,
                        'intelligent_analysis': True
                    }

                # 3. 更新数据库中的AI实例
                instance.config = updated_config
                instance.save()

                # 4. 更新内存中的AI实例
                ai_instance_manager.update_ai_instance(
                    instance.instance_id,
                    {
                        'config': updated_config,
                        'last_used': time.time()
                    }
                )

                upgraded_count += 1
                logger.info(f"成功升级AI实例: {instance.instance_id}")
            except Exception as e:
                upgrade_failed += 1
                logger.error(f"升级AI实例 {instance.instance_id} 失败: {str(e)}")

        # 5. 更新AI监控配置
        ai_monitor.upgrade_monitoring_config()

        logger.info(f"AI实例升级完成: 成功 {upgraded_count} 个, 失败 {upgrade_failed} 个")

            'success': True,
            'message': f'AI实例升级完成',
            'upgraded_count': upgraded_count,
            'upgrade_failed': upgrade_failed
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'升级AI实例时发生错误: {str(e)}'}), 500

@ai_bp.route('/dispatch_task', methods=['POST'])
def dispatch_task():
    """AI任务调度API"""
    try:
        # 获取任务数据
        task_data = request.get_json()
        task_type = task_data.get('task_type')
        task_payload = task_data.get('task_payload', {})

        if not task_type:

        logger.info(f"收到AI任务: {task_type}")

        # 使用AI集调度任务
        result = ai_ensemble.dispatch_task(task_type, task_payload)

        return jsonify({
            'success': True,
            'result': result,
            'message': f'任务 {task_type} 执行成功'
        }), 200
    except Exception as e:
        logger.error(f"执行AI任务时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'执行AI任务时发生错误: {str(e)}'}), 500

@ai_bp.route('/ai_status', methods=['GET'])
def ai_status():
    """获取AI系统状态"""
    try:
        # 获取AI集状态
        ai_ensemble_status = {
            'status': ai_ensemble.status,
            'sub_ais': ai_ensemble.get_all_sub_ais(),
            'project_features': ai_ensemble.project_features,
            'required_ai_types': ai_ensemble.required_ai_types

        # 获取AI实例状态
        instance_stats = ai_instance_manager.get_instance_stats()

        return jsonify({
            'success': True,
            'ai_ensemble': ai_ensemble_status,
            'instance_stats': instance_stats
        }), 200
    except Exception as e:
        logger.error(f"获取AI状态时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取AI状态时发生错误: {str(e)}'}), 500

@ai_bp.route('/ai_performance', methods=['GET'])
def ai_performance():
    """获取AI系统性能数据"""
    try:
        # 获取AI监控数据
        performance_data = ai_monitor.get_performance_data()

        return jsonify({
            'success': True,
            'performance_data': performance_data
        logger.error(f"获取AI性能数据时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取AI性能数据时发生错误: {str(e)}'}), 500

@ai_bp.route('/get_ai_types', methods=['GET'])
def get_ai_types():
    """获取可用的AI类型"""
    try:
        # 获取所有可用的AI类型
        ai_types = ai_ensemble.required_ai_types

        return jsonify({
            'success': True,
            'ai_types': ai_types
    except Exception as e:
        logger.error(f"获取AI类型时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取AI类型时发生错误: {str(e)}'}), 500

@ai_bp.route('/get_ai_instance/<instance_id>', methods=['GET'])
def get_ai_instance(instance_id):
    """获取指定AI实例的详细信息"""
    try:
        # 从数据库获取AI实例
        db_instance = AIInstance.get_by_id(instance_id)
        if not db_instance:
            return jsonify({'success': False, 'message': f'未找到ID为 {instance_id} 的AI实例'}), 404

        # 从内存获取AI实例
        memory_instance = ai_instance_manager.get_ai_instance(instance_id)
        return jsonify({
            'success': True,
            'db_instance': db_instance.to_dict(),
            'memory_instance': memory_instance
        }), 200
    except Exception as e:
        logger.error(f"获取AI实例详情时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'获取AI实例详情时发生错误: {str(e)}'}), 500

@ai_bp.route('/management')
def ai_management():
    """AI管理页面"""
    try:
        # 检查用户权限
        user_role = session.get('user_level')
        if user_role not in ['admin', 'super_admin', 'hardware_vikey_admin']:
            flash('没有权限访问AI管理页面', 'error')
            return redirect(url_for('main.smart_redirect'))

        instances = ai_instance_manager.ai_instances

        return render_template('ai_management.html', instances=instances, stats=instance_stats)
    except Exception as e:
        logger.error(f"访问AI管理页面时发生错误: {str(e)}")
        return f"访问AI管理页面时发生错误: {str(e)}", 500
