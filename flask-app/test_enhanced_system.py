#!/usr/bin/env python3
"""
测试增强系统功能，包括蓝图、沙盒和快照增强
"""

import time
import logging
import sys
import os

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

# 导入测试模块
from app.ai.enhanced_system import enhanced_system
from app.ai.sandbox_manager import sandbox_manager
from app.models.user_snapshots import UserSnapshot

def test_enhanced_system_initialization():
    """测试增强系统初始化"""
    logger.info("测试增强系统初始化...")
    try:
        assert enhanced_system is not None
        logger.info("✓ 增强系统初始化成功")
        return True
    except Exception as e:
        logger.error(f"✗ 增强系统初始化失败: {str(e)}")
        return False

def test_blueprint_enhancement():
    """测试蓝图增强功能"""
    logger.info("测试蓝图增强功能...")
    try:
        # 添加蓝图使用数据
        blueprint_data = {
            'blueprint': 'integrated_design',
            'usage_count': 100,
            'response_time': 0.5
        }
        enhanced_system.add_blueprint_usage_data(blueprint_data)
        
        # 验证数据已添加
        blueprint_usage_data = enhanced_system.get_enhanced_learning_data('blueprint_usage')
        assert len(blueprint_usage_data) > 0
        logger.info("✓ 蓝图使用数据添加成功")
        
        # 测试蓝图分析
        analysis = enhanced_system._analyze_blueprint_usage()
        assert isinstance(analysis, dict)
        logger.info("✓ 蓝图分析功能正常")
        
        return True
    except Exception as e:
        logger.error(f"✗ 蓝图增强功能测试失败: {str(e)}")
        return False

def test_sandbox_enhancement():
    """测试沙盒增强功能"""
    logger.info("测试沙盒增强功能...")
    try:
        # 测试沙盒预温功能
        sandbox_manager.prewarm_sandboxes(count=2)
        
        # 验证沙盒已预温
        all_sandboxes = sandbox_manager.get_all_sandboxes()
        prewarmed_sandboxes = [sb for sb in all_sandboxes if sb.get('prewarmed', False)]
        logger.info(f"✓ 沙盒预温成功，当前预温沙盒数量: {len(prewarmed_sandboxes)}")
        
        # 测试获取预温沙盒
        prewarmed_sandbox = sandbox_manager.get_prewarmed_sandbox()
        assert prewarmed_sandbox is not None
        logger.info("✓ 成功获取预温沙盒")
        
        # 添加沙盒性能数据
        sandbox_performance_data = {
            'sandbox_id': prewarmed_sandbox['sandbox_id'],
            'startup_time': 0.3,
            'resource_usage': {
                'cpu': 30.0,
                'memory': 200.0
            }
        }
        enhanced_system.add_sandbox_performance_data(sandbox_performance_data)
        
        # 验证数据已添加
        sandbox_performance_data_list = enhanced_system.get_enhanced_learning_data('sandbox_performance')
        assert len(sandbox_performance_data_list) > 0
        logger.info("✓ 沙盒性能数据添加成功")
        
        return True
    except Exception as e:
        logger.error(f"✗ 沙盒增强功能测试失败: {str(e)}")
        return False

def test_snapshot_enhancement():
    """测试快照增强功能"""
    logger.info("测试快照增强功能...")
    try:
        # 创建测试快照
        snapshot = UserSnapshot.create(
            user_id="test_user",
            session_id="test_session",
            snapshot_type="test_snapshot",
            data={"test_key": "test_value"}
        )
        
        assert snapshot is not None
        logger.info("✓ 快照创建成功")
        
        # 添加快照管理数据
        snapshot_data = {
            'snapshot_id': snapshot.snapshot_id,
            'type': 'test_snapshot',
            'size': 1024,
            'created_at': time.time()
        }
        enhanced_system.add_snapshot_management_data(snapshot_data)
        
        # 验证数据已添加
        snapshot_management_data = enhanced_system.get_enhanced_learning_data('snapshot_management')
        assert len(snapshot_management_data) > 0
        logger.info("✓ 快照管理数据添加成功")
        
        # 测试快照分析
        analysis = enhanced_system._analyze_snapshot_management()
        assert isinstance(analysis, dict)
        logger.info("✓ 快照分析功能正常")
        
        # 清理测试快照
        snapshot.delete()
        logger.info("✓ 测试快照清理成功")
        
        return True
    except Exception as e:
        logger.error(f"✗ 快照增强功能测试失败: {str(e)}")
        return False

def test_enhanced_suggestions():
    """测试增强建议生成"""
    logger.info("测试增强建议生成...")
    try:
        # 运行增强学习
        enhanced_system._learn_enhanced_patterns()
        logger.info("✓ 增强学习运行成功")
        
        # 保存增强模型
        enhanced_system.save_enhanced_model()
        logger.info("✓ 增强模型保存成功")
        
        return True
    except Exception as e:
        logger.error(f"✗ 增强建议生成测试失败: {str(e)}")
        return False

def test_dynamic_resource_allocation():
    """测试动态资源分配"""
    logger.info("测试动态资源分配...")
    try:
        # 获取当前沙盒配置
        sandbox_config = sandbox_manager.sandbox_config.copy()
        
        # 更新配置，启用动态资源分配
        sandbox_config['dynamic_resource_allocation'] = True
        sandbox_manager.save_sandbox_config(sandbox_config)
        logger.info("✓ 动态资源分配已启用")
        
        # 验证配置已更新
        updated_config = sandbox_manager.sandbox_config
        assert updated_config.get('dynamic_resource_allocation', False) is True
        logger.info("✓ 动态资源分配配置更新成功")
        
        return True
    except Exception as e:
        logger.error(f"✗ 动态资源分配测试失败: {str(e)}")
        return False

def test_smart_sandbox_prewarming():
    """测试智能沙盒预温功能"""
    logger.info("测试智能沙盒预温功能...")
    try:
        # 测试智能预温数量计算
        optimal_count = sandbox_manager._calculate_optimal_prewarm_count(base_count=5)
        assert isinstance(optimal_count, int)
        assert optimal_count >= 1
        logger.info(f"✓ 智能预温数量计算成功: {optimal_count}")
        
        # 测试获取最佳沙盒配置
        optimal_config = sandbox_manager._get_optimal_sandbox_config()
        assert isinstance(optimal_config, dict)
        assert 'resource_limits' in optimal_config
        logger.info("✓ 获取最佳沙盒配置成功")
        
        return True
    except Exception as e:
        logger.error(f"✗ 智能沙盒预温功能测试失败: {str(e)}")
        return False

def test_enhanced_suggestion_generation():
    """测试增强建议生成"""
    logger.info("测试增强建议生成...")
    try:
        # 创建模拟分析数据
        blueprint_analysis = {
            'total_usage': 1500,
            'blueprint_popularity': {
                'integrated_design': 500,
                'arduino_design': 300,
                'pcb_design': 200
            },
            'top_blueprints': [('integrated_design', 500), ('arduino_design', 300)]
        }
        
        sandbox_analysis = {
            'total_sandboxes': 20,
            'avg_startup_time': 1.2,
            'avg_resource_usage': {
                'cpu': 75.0,
                'memory': 65.0
            }
        }
        
        snapshot_analysis = {
            'total_snapshots': 600,
            'avg_snapshot_size': 2 * 1024 * 1024,  # 2MB
            'snapshot_types': {
                'user_state': 300,
                'design_state': 200,
                'system_state': 100
            }
        }
        
        # 生成增强建议
        suggestions = enhanced_system._generate_enhanced_suggestions(
            blueprint_analysis, sandbox_analysis, snapshot_analysis
        )
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        logger.info(f"✓ 成功生成 {len(suggestions)} 条增强建议")
        
        # 验证建议类型
        suggestion_types = [s['type'] for s in suggestions]
        assert 'blueprint_enhancement' in suggestion_types
        assert 'sandbox_enhancement' in suggestion_types
        assert 'snapshot_enhancement' in suggestion_types
        logger.info("✓ 生成了所有类型的增强建议")
        
        return True
    except Exception as e:
        logger.error(f"✗ 增强建议生成测试失败: {str(e)}")
        return False

def test_blueprint_management_enhancement():
    """测试蓝图管理增强功能"""
    logger.info("测试蓝图管理增强功能...")
    try:
        # 测试蓝图管理增强方法
        parameters = {
            'blueprint_name': 'test_blueprint',
            'add_dynamic_loading': True,
            'add_versioning': True
        }
        
        enhanced_system._enhance_blueprint_management(parameters)
        logger.info("✓ 蓝图管理增强功能测试成功")
        
        return True
    except Exception as e:
        logger.error(f"✗ 蓝图管理增强功能测试失败: {str(e)}")
        return False

def test_snapshot_management_enhancement():
    """测试快照管理增强功能"""
    logger.info("测试快照管理增强功能...")
    try:
        # 测试快照管理增强方法
        parameters = {
            'enable_auto_cleanup': True,
            'retention_days': 7
        }
        
        enhanced_system._enhance_snapshot_management(parameters)
        logger.info("✓ 快照管理增强功能测试成功")
        
        return True
    except Exception as e:
        logger.error(f"✗ 快照管理增强功能测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    logger.info("开始测试AI增强系统...")
    
    tests = [
        test_enhanced_system_initialization,
        test_blueprint_enhancement,
        test_sandbox_enhancement,
        test_snapshot_enhancement,
        test_enhanced_suggestions,
        test_dynamic_resource_allocation,
        test_smart_sandbox_prewarming,
        test_enhanced_suggestion_generation,
        test_blueprint_management_enhancement,
        test_snapshot_management_enhancement
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        logger.info("=" * 50)
    
    logger.info(f"测试完成: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！AI增强系统功能正常")
        return 0
    else:
        logger.error("❌ 部分测试失败，请检查日志")
        return 1

if __name__ == "__main__":
    sys.exit(main())
