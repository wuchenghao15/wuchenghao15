from app.utils.logging import logger
from app.config import Config
from app.ai.instances import ai_instance_manager
from app.ai.monitoring import ai_monitor
from app.utils.network import network_optimizer
from app.services.rule_management import rule_management_service
from app.services.butler_system import butler_system

# 导入用户状态检查装饰器
from app.views.main import check_user_status

# 创建系统管理蓝图
system_bp = Blueprint('system', __name__)

@system_bp.route('/')
@check_user_status
def system_dashboard():
    """系统管理仪表盘"""
    try:
        # 准备系统信息
        system_info = {
            'system_name': 'MTSCOS AI Project',
            'version': '1.0.0',
            'config': Config,
            'ai_instances': len(ai_instance_manager.ai_instances),
            'active_instances': len([inst for inst in ai_instance_manager.ai_instances.values() if inst['status'] == 'active']),
            'instance_types': ai_instance_manager.get_instance_stats()['instance_types']
        }
        
        # 准备用户信息
        user = {
            'username': session.get('username', 'Guest'),
            'role': session.get('user_level', 'guest')
        }
        
        return render_template('system_dashboard.html', 
                           user=user,
                           system_info=system_info)
    except Exception as e:
        logger.error(f"访问系统管理仪表盘时发生错误: {str(e)}")
        return f"访问系统管理仪表盘时发生错误: {str(e)}", 500

@system_bp.route('/rules')
@check_user_status
def system_rules():
    """系统规则管理"""
    try:
        # 获取所有规则
        rules = rule_management_service.get_rules()
        
        # 准备用户信息
        user = {
            'username': session.get('username', 'Guest'),
            'role': session.get('user_level', 'guest')
        }
        
        return render_template('system_rules.html', 
                           user=user,
                           rules=rules)
    except Exception as e:
        logger.error(f"访问系统规则管理时发生错误: {str(e)}")
        return f"访问系统规则管理时发生错误: {str(e)}", 500

@system_bp.route('/ai_instances')
@check_user_status
def system_ai_instances():
    """AI实例管理"""
    try:
        # 获取AI实例信息
        ai_instances = ai_instance_manager.ai_instances
        instance_stats = ai_instance_manager.get_instance_stats()
        
        # 准备用户信息
        user = {
            'username': session.get('username', 'Guest'),
            'role': session.get('user_level', 'guest')
        }
        
        return render_template('system_ai_instances.html', 
                           user=user,
                           ai_instances=ai_instances,
                           instance_stats=instance_stats)
    except Exception as e:
        logger.error(f"访问AI实例管理时发生错误: {str(e)}")
        return f"访问AI实例管理时发生错误: {str(e)}", 500

@system_bp.route('/monitoring')
@check_user_status
def system_monitoring():
    """系统监控"""
    try:
        # 获取监控数据
        performance_metrics = network_optimizer.get_performance_metrics()
        error_stats = ai_monitor.get_error_stats()
        ai_instances = ai_instance_manager.ai_instances
        
        # 准备监控数据
        monitoring_data = {
            'performance': performance_metrics,
            'error_stats': error_stats,
            'ai_instances': ai_instances
        }
        
        # 准备用户信息
        user = {
            'username': session.get('username', 'Guest'),
            'role': session.get('user_level', 'guest')
        }
        
        return render_template('system_monitoring.html', 
                           user=user,
                           monitoring_data=monitoring_data)
    except Exception as e:
        logger.error(f"访问系统监控时发生错误: {str(e)}")
        return f"访问系统监控时发生错误: {str(e)}", 500

@system_bp.route('/settings')
@check_user_status
def system_settings():
    """系统设置"""
    try:
        # 准备系统设置选项
        system_settings = {
            'ai_learning_enabled': Config.AI_CONFIG['LEARNING_ENABLED'],
            'ai_monitoring_enabled': Config.AI_CONFIG['MONITORING_ENABLED'],
            'self_optimization_enabled': Config.AI_CONFIG['SELF_OPTIMIZATION'],
            'rule_auto_update_enabled': True,
            'rule_monitoring_enabled': True
        }
        
        # 准备用户信息
        user = {
            'username': session.get('username', 'Guest'),
            'role': session.get('user_level', 'guest')
        }
        
        return render_template('system_settings.html', 
                           user=user,
                           system_settings=system_settings)
    except Exception as e:
        logger.error(f"访问系统设置时发生错误: {str(e)}")
        return f"访问系统设置时发生错误: {str(e)}", 500

@system_bp.route('/backup')
@check_user_status
def system_backup():
    """系统备份"""
    try:
        # 准备备份信息
        backup_info = {
            'last_backup': '2026-02-24 15:00:00',
            'backup_count': 5,
            'backup_size': '100 MB'
        }
        
        # 准备用户信息
        user = {
            'username': session.get('username', 'Guest'),
            'role': session.get('user_level', 'guest')
        }
        
        return render_template('system_backup.html', 
                           user=user,
                           backup_info=backup_info)
    except Exception as e:
        logger.error(f"访问系统备份时发生错误: {str(e)}")
        return f"访问系统备份时发生错误: {str(e)}", 500

@system_bp.route('/notification')
@check_user_status
def system_notification():
    """系统通知"""
    try:
        # 准备通知信息
        notifications = [
            {
                'id': 1,
                'title': '系统更新提醒',
                'content': '系统已成功更新到版本 1.1.0',
                'time': '2026-02-24 14:30:00',
                'read': False
            },
            {
                'id': 2,
                'title': 'AI规则更新',
                'content': '系统规则已自动优化和拓展',
                'time': '2026-02-24 14:00:00',
                'read': True
            },
            {
                'id': 3,
                'title': '数据库备份成功',
                'content': '数据库备份已完成，文件大小: 20 MB',
                'time': '2026-02-24 13:00:00',
                'read': True
            }
        ]
        
        # 准备用户信息
        user = {
            'username': session.get('username', 'Guest'),
            'role': session.get('user_level', 'guest')
        }
        
        return render_template('system_notification.html', 
                           user=user,
                           notifications=notifications)
    except Exception as e:
        logger.error(f"访问系统通知时发生错误: {str(e)}")
        return f"访问系统通知时发生错误: {str(e)}", 500

@system_bp.route('/ai_settings')
@check_user_status
def system_ai_settings():
    """AI增强设置"""
    try:
        # 获取AI智能建议
        recommendations_response = butler_system.get_smart_recommendations()
        recommendations = []
        if recommendations_response.get('status') == 'success':
            recommendations = recommendations_response.get('result', {}).get('recommendations', [])
        
        # 获取系统健康状态
        system_health_response = butler_system.get_system_health()
        system_health = {
            'cpu': 0,
            'memory': 0,
            'disk': 0
        }
        if system_health_response.get('status') == 'success':
            system_health = system_health_response.get('health', system_health)
        
        # 获取AI实例数量
        ai_instances_count = len(ai_instance_manager.ai_instances)
        
        # 准备用户信息
        user = {
            'username': session.get('username', 'Guest'),
            'role': session.get('user_level', 'guest'),
            'user_id': session.get('user_id', 'unknown'),
            'email': session.get('email', 'unknown')
        }
        
        return render_template('ai_enhanced_settings.html', 
                           username=user['username'],
                           role=user['role'],
                           user_id=user['user_id'],
                           email=user['email'],
                           recommendations=recommendations,
                           system_health=system_health,
                           ai_instances_count=ai_instances_count)
    except Exception as e:
        logger.error(f"访问AI增强设置时发生错误: {str(e)}")
        return f"访问AI增强设置时发生错误: {str(e)}", 500
