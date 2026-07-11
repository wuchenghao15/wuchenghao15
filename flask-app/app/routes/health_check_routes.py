"""健康检查API路由 - MTSCOS AI项目"""

from flask import Blueprint
from app.services.health_check_service import HealthCheckService
from app.utils.response import success_response

health_api = Blueprint('health_api', __name__)


@health_api.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    summary = HealthCheckService.get_health_summary()
    return success_response(summary)


@health_api.route('/api/health/metrics', methods=['GET'])
def get_metrics():
    """获取详细监控指标"""
    metrics = HealthCheckService.get_metrics()
    return success_response(metrics)


@health_api.route('/api/health/cpu', methods=['GET'])
def get_cpu_info():
    """获取CPU信息"""
    cpu = HealthCheckService.get_cpu_info()
    return success_response(cpu)


@health_api.route('/api/health/memory', methods=['GET'])
def get_memory_info():
    """获取内存信息"""
    memory = HealthCheckService.get_memory_info()
    return success_response(memory)


@health_api.route('/api/health/disk', methods=['GET'])
def get_disk_info():
    """获取磁盘信息"""
    disk = HealthCheckService.get_disk_info()
    return success_response(disk)


@health_api.route('/api/health/network', methods=['GET'])
def get_network_info():
    """获取网络信息"""
    network = HealthCheckService.get_network_info()
    return success_response(network)


@health_api.route('/api/health/database', methods=['GET'])
def get_database_status():
    """获取数据库状态"""
    database = HealthCheckService.get_database_status()
    return success_response(database)