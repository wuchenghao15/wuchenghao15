# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI系统 - 预览和初始化脚本
"""

import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

def print_success(message):
    """打印成功消息"""
    print(f"   ✓ {message}")

def print_info(message):
    """打印信息"""
    print(f"   • {message}")

def print_error(message):
    """打印错误消息"""
    print(f"   ✗ {message}")

def initialize_systems():
    """初始化所有系统"""
    systems = []
    
    # 1. AI服务中枢
    print_section("🔧 初始化AI服务中枢")
    try:
        from app.ai.ai_service_hub import ai_service_hub
        systems.append(('AI服务中枢', True, '服务注册、事件总线、依赖管理'))
        print_success("AI服务中枢初始化完成")
    except Exception as e:
        systems.append(('AI服务中枢', False, str(e)))
        print_error(f"AI服务中枢初始化失败: {e}")
    
    # 2. 多环境管理器
    print_section("🌐 初始化多环境管理器")
    try:
        from app.ai.multi_environment_manager import multi_env_manager
        systems.append(('多环境管理器', True, '开发/测试/公测/生产环境管理'))
        print_success("多环境管理器初始化完成")
    except Exception as e:
        systems.append(('多环境管理器', False, str(e)))
        print_error(f"多环境管理器初始化失败: {e}")
    
    # 3. 自动升级测试系统
    print_section("🔄 初始化自动升级测试系统")
    try:
        from app.ai.auto_upgrade_test_system import smart_auto_upgrade_test_system
        systems.append(('自动升级测试系统', True, '自动升级、异常检测、自动修复'))
        print_success("自动升级测试系统初始化完成")
    except Exception as e:
        systems.append(('自动升级测试系统', False, str(e)))
        print_error(f"自动升级测试系统初始化失败: {e}")
    
    # 4. 系统整合中心
    print_section("🔗 初始化系统整合中心")
    try:
        from app.ai.system_integration import system_integration_hub
        systems.append(('系统整合中心', True, '跨系统数据整合、数据库上报'))
        print_success("系统整合中心初始化完成")
    except Exception as e:
        systems.append(('系统整合中心', False, str(e)))
        print_error(f"系统整合中心初始化失败: {e}")
    
    # 5. 备份系统
    print_section("💾 初始化备份系统")
    try:
        from app.ai.enhanced_backup_system import enhanced_backup_system
        systems.append(('备份系统', True, '常规备份、应急备份、双备份'))
        print_success("备份系统初始化完成")
    except Exception as e:
        systems.append(('备份系统', False, str(e)))
        print_error(f"备份系统初始化失败: {e}")
    
    # 6. 恢复镜像系统
    print_section("🔙 初始化恢复镜像系统")
    try:
        from app.ai.incremental_recovery_system import incremental_recovery_system
        systems.append(('恢复镜像系统', True, '完整备份、增量备份、镜像恢复'))
        print_success("恢复镜像系统初始化完成")
    except Exception as e:
        systems.append(('恢复镜像系统', False, str(e)))
        print_error(f"恢复镜像系统初始化失败: {e}")
    
    # 7. 证书管理系统
    print_section("📜 初始化证书管理系统")
    try:
        from app.ai.client_certificate_manager import client_certificate_manager
        systems.append(('证书管理系统', True, '数字证书、会话管理、打包上传'))
        print_success("证书管理系统初始化完成")
    except Exception as e:
        systems.append(('证书管理系统', False, str(e)))
        print_error(f"证书管理系统初始化失败: {e}")
    
    # 8. 专业技能AI系统
    print_section("🎯 初始化专业技能AI系统")
    try:
        from app.ai.skill_ai_system import skill_ai_system
        systems.append(('专业技能AI系统', True, '技能定义、技能执行、技能推荐'))
        print_success("专业技能AI系统初始化完成")
    except Exception as e:
        systems.append(('专业技能AI系统', False, str(e)))
        print_error(f"专业技能AI系统初始化失败: {e}")
    
    # 9. 任务中心系统
    print_section("📋 初始化任务中心系统")
    try:
        from app.ai.task_center import task_center
        systems.append(('任务中心系统', True, '任务管理、AI管家、智能分配'))
        print_success("任务中心系统初始化完成")
    except Exception as e:
        systems.append(('任务中心系统', False, str(e)))
        print_error(f"任务中心系统初始化失败: {e}")
    
    # 10. 设置管理系统
    print_section("⚙️ 初始化设置管理系统")
    try:
        from app.ai.settings_manager import settings_manager
        systems.append(('设置管理系统', True, 'AI匹配、数据库同步、一致性检查'))
        print_success("设置管理系统初始化完成")
    except Exception as e:
        systems.append(('设置管理系统', False, str(e)))
        print_error(f"设置管理系统初始化失败: {e}")
    
    # 11. 统一配置存储系统
    print_section("🔐 初始化统一配置存储系统")
    try:
        from app.ai.unified_config_storage import config_storage
        systems.append(('统一配置存储系统', True, '数据库存储、API动态调取、AI智能适配'))
        print_success("统一配置存储系统初始化完成")
    except Exception as e:
        systems.append(('统一配置存储系统', False, str(e)))
        print_error(f"统一配置存储系统初始化失败: {e}")
    
    return systems

def show_system_overview(systems):
    """显示系统概览"""
    print_section("📊 系统概览")
    
    total = len(systems)
    success = sum(1 for _, status, _ in systems if status)
    failed = total - success
    
    print(f"   系统总数: {total}")
    print(f"   成功初始化: {success}")
    print(f"   失败: {failed}")
    print(f"   成功率: {(success / total * 100):.1f}%")
    
    print("\n   系统列表:")
    for name, status, desc in systems:
        icon = "✅" if status else "❌"
        print(f"   {icon} {name}")
        print(f"      描述: {desc}")

def show_core_features():
    """展示核心功能"""
    print_section("✨ 核心功能模块")
    
    features = [
        ('AI服务中枢', '服务注册与发现、事件总线、依赖管理、健康检查'),
        ('数据矩阵系统', '错误类型矩阵、性能指标矩阵、相关性矩阵、趋势矩阵、热图矩阵'),
        ('自动升级测试', '自动检查升级、异常检测、自动修复、数据库上报'),
        ('系统整合中心', '跨系统数据整合、数据库上报、AI异常学习'),
        ('备份系统', '常规备份、应急备份、双备份机制、处罚规则'),
        ('恢复镜像系统', '完整备份、增量备份、镜像恢复、恢复链'),
        ('证书管理系统', '数字证书、会话管理、退出处理、打包上传'),
        ('专业技能AI', '技能定义、技能执行、技能推荐、技能学习'),
        ('任务中心系统', '任务管理、AI管家、智能分配、负载均衡'),
        ('设置管理系统', 'AI深度匹配、数据库同步、一致性检查'),
        ('统一配置存储', '数据库持久化、API动态调取、AI智能适配、配置版本管理'),
    ]
    
    for name, desc in features:
        print(f"   🚀 {name}")
        print(f"      {desc}")

def show_api_endpoints():
    """展示API端点"""
    print_section("🌐 API端点概览")
    
    endpoints = [
        ('/api/auto-upgrade/', '自动升级相关接口'),
        ('/api/integration/', '系统整合接口'),
        ('/api/backup/', '备份系统接口'),
        ('/api/recovery/', '恢复镜像接口'),
        ('/api/certificate/', '证书管理接口'),
        ('/api/skills/', '专业技能AI接口'),
        ('/api/tasks/', '任务中心接口'),
        ('/api/settings/', '设置管理接口'),
        ('/api/maintenance/', '例行维护接口'),
        ('/api/ai/', 'AI服务接口'),
        ('/api/config/', '统一配置存储接口'),
    ]
    
    for path, desc in endpoints:
        print(f"   {path} - {desc}")

def show_ai_workers():
    """展示AI工作者"""
    print_section("🤖 AI工作者团队")
    
    workers = [
        ('数据分析AI', '数据分析、性能分析'),
        ('备份专家AI', '数据备份、数据恢复'),
        ('维护工程师AI', '系统维护、健康检查'),
        ('安全专家AI', '安全扫描、异常检测'),
        ('报告生成AI', '报告生成'),
        ('集成大师AI', '系统集成'),
    ]
    
    for name, specialties in workers:
        print(f"   {name}")
        print(f"      专业领域: {specialties}")

def show_database_tables():
    """展示数据库表结构"""
    print_section("🗄️ 数据库表结构")
    
    tables = [
        ('系统配置表', 'system_config'),
        ('用户表', 'users'),
        ('会话表', 'sessions'),
        ('技能表', 'skills'),
        ('任务表', 'tasks'),
        ('备份记录表', 'backups'),
        ('证书表', 'certificates'),
        ('镜像表', 'mirrors'),
        ('执行记录表', 'executions'),
        ('设置表', 'settings'),
        ('升级记录表', 'upgrade_records'),
        ('异常记录表', 'anomaly_records'),
        ('告警记录表', 'alert_records'),
        ('AI脑库表', 'ai_brain_knowledge'),
        ('学习记录表', 'learning_records'),
    ]
    
    for desc, name in tables:
        print(f"   • {desc} (`{name}`)")

def run_demo():
    """运行演示"""
    print_section("🎬 功能演示")
    
    # 演示1: 创建任务
    try:
        from app.ai.task_center import task_center, TaskType, TaskPriority
        task_id = task_center.create_task(
            name="演示任务",
            task_type=TaskType.DATA_ANALYSIS,
            priority=TaskPriority.HIGH,
            inputs={'data_source': 'demo'}
        )
        print_success(f"创建演示任务: {task_id}")
    except Exception as e:
        print_error(f"创建任务失败: {e}")
    
    # 演示2: 获取AI推荐
    try:
        from app.ai.settings_manager import settings_manager
        recommendations = settings_manager.get_ai_recommendations()
        if recommendations:
            print_success(f"获取AI推荐: {len(recommendations)} 条")
        else:
            print_info("当前无AI推荐")
    except Exception as e:
        print_error(f"获取AI推荐失败: {e}")
    
    # 演示3: 执行技能
    try:
        from app.ai.skill_ai_system import skill_ai_system
        result = skill_ai_system.execute_skill('skill_health_check')
        if result.get('success'):
            print_success(f"执行健康检查技能: 健康评分 {result['result'].get('health_score')}")
        else:
            print_error(f"技能执行失败: {result.get('error')}")
    except Exception as e:
        print_error(f"执行技能失败: {e}")
    
    # 演示4: 统一配置存储系统
    try:
        from app.ai.unified_config_storage import config_storage
        
        # 获取配置
        ai_enabled = config_storage.get_config_value('ai.service_enabled')
        print_success(f"获取配置: ai.service_enabled = {ai_enabled}")
        
        # 更新配置
        success = config_storage.set_config('ai.auto_learning_enabled', True)
        if success:
            print_success("更新配置: ai.auto_learning_enabled = True")
        
        # 获取AI推荐配置
        recommendations = config_storage.get_ai_recommendations()
        if recommendations:
            print_success(f"AI配置推荐: {len(recommendations)} 项")
            for key, rec in recommendations.items():
                print_info(f"  {key}: {rec['reason']} (评分: {rec['score']})")
        
        # 获取系统状态
        status = config_storage.get_system_status()
        print_success(f"系统配置状态: {status['total_configs']} 个配置, {status['ai_recommended']} 个AI推荐")
        
    except Exception as e:
        print_error(f"统一配置存储演示失败: {e}")

def main():
    """主函数"""
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "🚀 MTSCOS AI系统预览与初始化" + " " * 8 + "║")
    print("╚" + "=" * 68 + "╝")
    print(f"\n   日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   版本: 2.0.0")
    
    # 初始化系统
    systems = initialize_systems()
    
    # 显示概览
    show_system_overview(systems)
    
    # 显示核心功能
    show_core_features()
    
    # 显示API端点
    show_api_endpoints()
    
    # 显示AI工作者
    show_ai_workers()
    
    # 显示数据库表
    show_database_tables()
    
    # 运行演示
    run_demo()
    
    # 总结
    print_section("🎉 系统预览完成")
    
    success_count = sum(1 for _, status, _ in systems if status)
    total_count = len(systems)
    
    if success_count == total_count:
        print("   ✅ 所有系统初始化成功!")
        print("   🚀 系统已准备就绪,可以开始使用!")
    else:
        print(f"   ⚠️  {success_count}/{total_count} 系统初始化成功")
        print("   📝 部分系统需要进一步配置")
    
    print("\n" + "=" * 70)
    print("启动命令:")
    print("   python3 app.py        # 启动Flask应用")
    print("   python3 run_routine_maintenance.py  # 执行例行维护")
    print("=" * 70)

if __name__ == "__main__":
    main()
