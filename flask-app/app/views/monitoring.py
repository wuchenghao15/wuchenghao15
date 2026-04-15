from app.utils.network import network_optimizer
from app.ai.monitoring import ai_monitor
from app.utils.logging import logger, logging_manager
from app.utils.environment import environment_manager
from app.utils.error_handler import error_handler
import os, Blueprint
import sys
import time
import psutil

# 创建蓝图
monitoring_bp = Blueprint('monitoring', __name__)

# 健康检查端点
@monitoring_bp.route('/health')
def health_check():
    """健康检查端点，返回应用的基本健康状态"""
    try:
        # 基本健康检查
        health_status = {
            'status': 'UP',
            'timestamp': time.time(),
            'environment': environment_manager.get_current_environment(),
            'app_version': os.environ.get('APP_VERSION', 'unknown'),
            'checks': {
                'database': 'UP',  # 简单检查，实际项目中应该检查数据库连接
                'cache': 'UP',     # 简单检查，实际项目中应该检查缓存连接
                'ai_monitor': 'UP' if ai_monitor else 'DOWN'
            }
        }
        
        return jsonify(health_status), 200
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return jsonify({
            'status': 'DOWN',
            'timestamp': time.time(),
            'error': str(e)
        }), 500

# 详细指标端点
@monitoring_bp.route('/metrics')
def metrics():
    """详细的指标端点，返回应用的各种运行指标"""
    try:
        # 获取系统资源使用情况
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent(interval=0.1)
        
        # 获取性能指标
        performance_metrics = network_optimizer.get_performance_metrics()
        
        # 获取错误统计
        error_stats = ai_monitor.get_error_stats()
        
        # 获取日志统计
        log_stats = logging_manager.get_log_stats()
        
        # 获取错误处理器统计
        error_handler_stats = error_handler.get_error_stats()
        
        # 构建完整的指标响应
        metrics = {
            'timestamp': time.time(),
            'environment': environment_manager.get_current_environment(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_used_mb': round(memory_info.rss / (1024 * 1024), 2),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'python_version': sys.version,
                'uptime_seconds': time.time() - process.create_time()
            },
            'performance': performance_metrics,
            'errors': {
                'ai_monitor': error_stats,
                'error_handler': error_handler_stats
            },
            'logging': log_stats,
            'request': {
                'method': request.method,
                'path': request.path,
                'client_ip': request.remote_addr
            }
        }
        
        return jsonify(metrics), 200
    except Exception as e:
        logger.error(f"获取指标失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 应用信息端点
@monitoring_bp.route('/info')
def app_info():
    """应用信息端点，返回应用的基本信息"""
    try:
        # 获取环境信息
        env_info = environment_manager.get_environment_info()
        
        # 获取应用配置信息
        config = environment_manager.get_environment_config()
        
        # 构建应用信息响应
        app_info = {
            'name': 'MTSCOS AI System',
            'version': os.environ.get('APP_VERSION', 'unknown'),
            'description': 'MTSCOS AI Project System',
            'environment': env_info,
            'config': {
                'debug': getattr(config, 'DEBUG', False),
                'port': getattr(config, 'PORT', 8888),
                'log_level': getattr(config, 'LOG_LEVEL', 'INFO'),
                'session_timeout_minutes': getattr(config, 'PERMANENT_SESSION_LIFETIME', {}).total_seconds() / 60 if hasattr(config, 'PERMANENT_SESSION_LIFETIME') else 30
            },
            'features': {
                'ai_monitoring': True,
                'error_handling': True,
                'logging': True,
                'middleware': True,
                'environment_management': True
            }
        }
        
        return jsonify(app_info), 200
    except Exception as e:
        logger.error(f"获取应用信息失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 保留API路由，供主仪表盘调用
@monitoring_bp.route('/api/performance')
def api_performance():
    """获取性能指标API"""
    try:
        performance_metrics = network_optimizer.get_performance_metrics()
        return jsonify(performance_metrics)
    except Exception as e:
        logger.error(f"获取性能指标API时发生错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/errors')
def api_errors():
    """获取错误统计API"""
    try:
        error_stats = ai_monitor.get_error_stats()
        return jsonify(error_stats)
    except Exception as e:
        logger.error(f"获取错误统计API时发生错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/clear_cache')
def clear_cache():
    """清除缓存"""
    if 'logged_in' not in session:
        return redirect(url_for('main.index'))
    
    try:
        network_optimizer.clear_cache()
        logger.info("缓存已清除")
        flash('缓存已清除', 'success')
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        logger.error(f"清除缓存时发生错误: {str(e)}")
        flash('清除缓存时发生错误', 'danger')
        return redirect(url_for('main.dashboard'))
