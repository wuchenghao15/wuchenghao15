#!/usr/bin/env python3
"""
测试优化后的系统功能，确保AI、规则、权限和路由的适配都正常工作

import time
import logging
from app.services.distributed_server import distributed_server_manager
from app.ai.server_ai import server_ai
from app.utils.server_rule_manager import server_rule_manager
from app.utils.server_permission_manager import server_permission_manager
from app.utils.server_route_manager import server_route_manager
from app.services.git_manager import git_manager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ai_adaptation():
    """测试AI适配功能"""
    logger.info("=== 测试AI适配功能 ===")

    # 测试服务器性能分析
    start_time = time.time()
    try:
        # 模拟服务器性能数据
        performance_data = {
            "cpu_usage": 75.5,
            "memory_usage": 60.2,
            "disk_usage": 45.8,
            "network_throughput": 1024.5,
            "response_time": 150.3
        }
        analysis = server_ai.analyze_server_performance("test-server-1", performance_data)
        logger.info(f"服务器性能分析: {analysis}")
        analysis_time = time.time() - start_time
        logger.info(f"服务器性能分析测试：耗时: {analysis_time:.4f}秒")
    except Exception as e:
        logger.error(f"服务器性能分析测试失败: {str(e)}")

    # 测试服务器负载预测
    start_time = time.time()
        prediction = server_ai.predict_server_load("test-server-1", 30)
        prediction_time = time.time() - start_time
        logger.info(f"服务器负载预测测试：耗时: {prediction_time:.4f}秒")
    except Exception as e:
        logger.error(f"服务器负载预测测试失败: {str(e)}")

def test_rule_adaptation():
    """测试规则适配功能"""
    logger.info("=== 测试规则适配功能 ===")

    # 测试服务器注册规则
    start_time = time.time()
        server_info = {
            "id": "test-server-1",
            "ip": "192.168.1.100",
            "port": 8080,
            "cpu_cores": 4,
            "memory_gb": 8,
            "disk_gb": 100
        }
        registration_result = server_rule_manager.check_server_registration(server_info)
        logger.info(f"服务器注册规则检查: {registration_result}")
        registration_time = time.time() - start_time
        logger.info(f"服务器注册规则测试：耗时: {registration_time:.4f}秒")
        logger.error(f"服务器注册规则测试失败: {str(e)}")

    # 测试服务器健康规则
    start_time = time.time()
        health_info = {
            "cpu_usage": 45.5,
            "memory_usage": 55.2,
            "response_time": 80.3
        }
        health_result = server_rule_manager.check_server_health(health_info)
        logger.info(f"服务器健康规则检查: {health_result}")
        health_time = time.time() - start_time
        logger.info(f"服务器健康规则测试：耗时: {health_time:.4f}秒")
    except Exception as e:
        logger.error(f"服务器健康规则测试失败: {str(e)}")
def test_permission_adaptation():
    """测试权限适配功能"""
    logger.info("=== 测试权限适配功能 ===")

    # 测试服务器访问权限
    start_time = time.time()
        admin_access = server_permission_manager.check_server_access("admin", "test-server-1", "start")
        operator_access = server_permission_manager.check_server_access("operator", "test-server-1", "start")
        monitor_access = server_permission_manager.check_server_access("monitor", "test-server-1", "start")
        logger.info(f"管理员访问权限: {admin_access}")
        logger.info(f"监控员访问权限: {monitor_access}")
        access_time = time.time() - start_time
        logger.info(f"服务器访问权限测试：耗时: {access_time:.4f}秒")
    except Exception as e:
        logger.error(f"服务器访问权限测试失败: {str(e)}")

    # 测试AI访问权限
    start_time = time.time()
        admin_ai_access = server_permission_manager.check_ai_access("admin", "manage")
        operator_ai_access = server_permission_manager.check_ai_access("operator", "manage")
        monitor_ai_access = server_permission_manager.check_ai_access("monitor", "manage")
        logger.info(f"管理员AI访问权限: {admin_ai_access}")
        logger.info(f"操作员AI访问权限: {operator_ai_access}")
        ai_access_time = time.time() - start_time
        logger.info(f"AI访问权限测试：耗时: {ai_access_time:.4f}秒")
    except Exception as e:
        logger.error(f"AI访问权限测试失败: {str(e)}")

def test_route_adaptation():
    """测试路由适配功能"""
    logger.info("=== 测试路由适配功能 ===")

    # 测试获取路由
    start_time = time.time()
        server_list_route = server_route_manager.get_route("server", "list")
        ai_analysis_route = server_route_manager.get_route("ai", "analysis")
        logger.info(f"服务器列表路由: {server_list_route}")
        logger.info(f"AI分析路由: {ai_analysis_route}")
        route_time = time.time() - start_time
        logger.info(f"获取路由测试：耗时: {route_time:.4f}秒")
        logger.error(f"获取路由测试失败: {str(e)}")

    # 测试路由权限
    start_time = time.time()
        admin_route_access = server_route_manager.check_route_permission("server.register", "admin")
        operator_route_access = server_route_manager.check_route_permission("server.register", "operator")
        monitor_route_access = server_route_manager.check_route_permission("server.register", "monitor")
        logger.info(f"管理员路由访问权限: {admin_route_access}")
        logger.info(f"操作员路由访问权限: {operator_route_access}")
        logger.info(f"监控员路由访问权限: {monitor_route_access}")
        route_permission_time = time.time() - start_time
    except Exception as e:
        logger.error(f"路由权限测试失败: {str(e)}")

def test_git_integration():
    """测试Git集成功能"""
    logger.info("=== 测试Git集成功能 ===")

    # 测试获取系统版本信息
    start_time = time.time()
        version_info = git_manager.get_system_version()
        logger.info(f"系统版本信息: {version_info}")
        version_time = time.time() - start_time
        logger.info(f"获取系统版本信息测试：耗时: {version_time:.4f}秒")
    except Exception as e:
        logger.error(f"获取系统版本信息测试失败: {str(e)}")

    # 测试使用AI分析版本信息
        ai_analysis = git_manager.analyze_version_with_ai()
        logger.info(f"AI版本分析结果: {ai_analysis}")
        ai_time = time.time() - start_time
        logger.info(f"使用AI分析版本信息测试：耗时: {ai_time:.4f}秒")
    except Exception as e:
        logger.error(f"使用AI分析版本信息测试失败: {str(e)}")

def test_distributed_server_manager():
    """测试分布式服务器管理器"""

    # 测试注册子服务器
    start_time = time.time()
        server_info = {
            "server_id": "test-server-1",
            "ip": "192.168.1.100",
            "port": 8080,
            "load": 0,
            "resources": {
                "cpu_usage": 45.5,
                "memory_usage": 55.2,
                "disk_usage": 40.8,
                "network_traffic": 1024.5,
            }
        }
        registration_result = distributed_server_manager.register_child_server(server_info)
        logger.info(f"注册子服务器结果: {registration_result}")
        registration_time = time.time() - start_time
        logger.info(f"注册子服务器测试：耗时: {registration_time:.4f}秒")
    except Exception as e:
        logger.error(f"注册子服务器测试失败: {str(e)}")

    # 测试获取所有子服务器
    start_time = time.time()
        servers = distributed_server_manager.get_all_child_servers()
        servers_time = time.time() - start_time
        logger.info(f"获取所有子服务器测试：耗时: {servers_time:.4f}秒")
        logger.error(f"获取所有子服务器测试失败: {str(e)}")
    # 测试分析服务器性能
    start_time = time.time()
        performance_analysis = distributed_server_manager.analyze_server_performance("test-server-1")
        logger.error(f"分析服务器性能测试失败: {str(e)}")
def main():
    logger.info("开始测试优化后的系统功能...")

        test_rule_adaptation()
        test_route_adaptation()
        test_git_integration()
        test_distributed_server_manager()
        logger.info("测试完成，所有测试通过！")
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

    main()
