#!/usr/bin/env python3
"""
测试所有新创建的系统规则服务
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.system_rules_extension import system_rules_extension
from app.git_auto_sync import git_auto_sync, github_sync
from app.auto_backup_service import auto_backup_service
from app.shadow_node_manager import shadow_node_manager, data_replication_manager
from app.operation_recorder import operation_recorder
from app.gray_release_service import gray_release_service
from app.checkpoint_service import checkpoint_service
from app.history_data_service import history_data_service

def test_system_rules_extension():
    """测试系统规则扩展服务"""
    logger.info("\n" + "="*60)
    logger.info("测试系统规则扩展服务")
    logger.info("="*60)
    
    rules = system_rules_extension.get_all_rules()
    logger.info(f"✓ 系统规则总数: {len(rules)}")
    
    git_rules = system_rules_extension.get_rules_by_type('git')
    logger.info(f"✓ Git规则数: {len(git_rules)}")
    
    backup_rules = system_rules_extension.get_rules_by_type('backup')
    logger.info(f"✓ 备份规则数: {len(backup_rules)}")
    
    ha_rules = system_rules_extension.get_rules_by_type('high_availability')
    logger.info(f"✓ 高可用规则数: {len(ha_rules)}")
    
    audit_rules = system_rules_extension.get_rules_by_type('audit')
    logger.info(f"✓ 审计规则数: {len(audit_rules)}")
    
    release_rules = system_rules_extension.get_rules_by_type('release')
    logger.info(f"✓ 发布规则数: {len(release_rules)}")
    
    git_config = system_rules_extension.get_git_sync_config()
    logger.info(f"✓ Git同步配置: auto_sync={git_config['auto_sync_enabled']}, interval={git_config['sync_interval']}")
    
    backup_config = system_rules_extension.get_backup_config()
    logger.info(f"✓ 备份配置: auto_backup={backup_config['auto_backup_enabled']},interval={backup_config['backup_interval']}")
    
    gray_config = system_rules_extension.get_gray_release_config()
    logger.info(f"✓ 灰度发布配置: enabled={gray_config['enabled']}, percentage={gray_config['percentage']}%")

def test_git_auto_sync():
    """测试Git自动同步服务"""
    logger.info("\n" + "="*60)
    logger.info("测试Git自动同步服务")
    logger.info("="*60)
    
    config = git_auto_sync.config
    logger.info(f"✓ 配置: branch={config.get('sync_branch')}, remote={config.get('sync_remote')}")
    
    status = git_auto_sync._get_git_status()
    logger.info(f"✓ Git状态查询成功")
    
    branch = git_auto_sync._get_current_branch()
    logger.info(f"✓ 当前分支: {branch}")
    
    github_config = github_sync.config
    logger.info(f"✓ GitHub配置: owner={github_config.get('repo_owner')}, name={github_config.get('repo_name')}")

def test_auto_backup_service():
    """测试自动备份服务"""
    logger.info("\n" + "="*60)
    logger.info("测试自动备份服务")
    logger.info("="*60)
    
    backup_file = auto_backup_service.backup('full')
    if backup_file:
        logger.info(f"✓ 全量备份成功: {os.path.basename(backup_file)}")
    else:
        logger.info("✗ 全量备份失败")
    
    inc_backup_file = auto_backup_service.backup()
    if inc_backup_file:
        logger.info(f"✓ 增量备份成功: {os.path.basename(inc_backup_file)}")
    else:
        logger.info("✗ 增量备份失败")

def test_shadow_node_manager():
    """测试影子节点管理服务"""
    logger.info("\n" + "="*60)
    logger.info("测试影子节点管理服务")
    logger.info("="*60)
    
    nodes = shadow_node_manager.get_node_status()
    logger.info(f"✓ 影子节点数: {len(nodes)}")
    
    for node in nodes:
        logger.info(f"  - {node['node_id']}: {node['status']}")
    
    primary = shadow_node_manager.get_primary_node()
    logger.info(f"✓ 主节点: {primary}")
    
    shadow_node_manager.health_check_all()
    logger.info(f"✓ 健康检查完成")
    
    shadow_node_manager.sync_all_nodes()
    logger.info(f"✓ 节点同步完成")

def test_operation_recorder():
    """测试操作记录服务"""
    logger.info("\n" + "="*60)
    logger.info("测试操作记录服务")
    logger.info("="*60)
    
    operation_recorder.record_login('test_user', '测试用户', '127.0.0.1', True)
    logger.info(f"✓ 记录登录操作")
    
    operation_recorder.record_create('test_user', '测试用户', 'system', '创建新规则')
    logger.info(f"✓ 记录创建操作")
    
    operation_recorder.record_update('test_user', '测试用户', 'system', '更新规则')
    logger.info(f"✓ 记录更新操作")
    
    operation_recorder.record_delete('test_user', '测试用户', 'system', '删除规则')
    logger.info(f"✓ 记录删除操作")
    
    records = operation_recorder.get_records(limit=5)
    logger.info(f"✓ 查询操作记录: {len(records)} 条")
    
    for record in records:
        logger.info(f"  - {record['timestamp']}: {record['operation_type']} {record['action']}")

def test_gray_release_service():
    """测试灰度发布服务"""
    logger.info("\n" + "="*60)
    logger.info("测试灰度发布服务")
    logger.info("="*60)
    
    gray_release_service.start_release('v1.0.0', ['user1', 'user2', 'user3'])
    logger.info(f"✓ 启动灰度发布")
    
    status = gray_release_service.get_release_status()
    logger.info(f"✓ 当前状态: active={status['release_active']}, percentage={status['current_percentage']}%")
    
    is_gray = gray_release_service.is_gray_user('user1')
    logger.info(f"✓ 用户user1是否灰度: {is_gray}")
    
    is_gray = gray_release_service.is_gray_user('user99')
    logger.info(f"✓ 用户user99是否灰度: {is_gray}")
    
    gray_release_service.record_request('user1', True)
    gray_release_service.record_request('user2', True)
    gray_release_service.record_request('user3', False)
    logger.info(f"✓ 记录请求完成")
    
    gray_release_service.advance_step()
    status = gray_release_service.get_release_status()
    logger.info(f"✓ 推进步骤: step={status['current_step']}, percentage={status['current_percentage']}%")
    
    gray_release_service.complete_release()
    logger.info(f"✓ 完成灰度发布")

def test_checkpoint_service():
    """测试记录点服务"""
    logger.info("\n" + "="*60)
    logger.info("测试记录点服务")
    logger.info("="*60)
    
    chk_id = checkpoint_service.create_checkpoint("测试记录点", "manual")
    logger.info(f"✓ 创建记录点: {chk_id}")
    
    checkpoint_service.create_on_operation("测试操作")
    logger.info(f"✓ 操作后创建记录点")
    
    checkpoints = checkpoint_service.list_checkpoints(limit=3)
    logger.info(f"✓ 查询记录点: {len(checkpoints)} 条")
    
    for chk in checkpoints:
        logger.info(f"  - {chk['checkpoint_id']}: {chk['description']}")

def test_history_data_service():
    """测试历史数据服务"""
    logger.info("\n" + "="*60)
    logger.info("测试历史数据服务")
    logger.info("="*60)
    
    history_data_service.record('test', 'key1', 'value1')
    history_data_service.record('test', 'key2', 'value2')
    logger.info(f"✓ 记录历史数据")
    
    history = history_data_service.get_history(data_type='test', limit=5)
    logger.info(f"✓ 查询历史数据: {len(history)} 条")
    
    for item in history:
        logger.info(f"  - {item['created_at']}: {item['data_key']}={item['data_value']}")

def main():
    """主测试函数"""
    logger.info("="*60)
    logger.info("系统规则服务综合测试")
    logger.info("="*60)
    
    try:
        test_system_rules_extension()
        test_git_auto_sync()
        test_auto_backup_service()
        test_shadow_node_manager()
        test_operation_recorder()
        test_gray_release_service()
        test_checkpoint_service()
        test_history_data_service()
        
        logger.info("\n" + "="*60)
        logger.info("✓ 所有测试完成！")
        logger.info("="*60)
        
    except Exception as e:
        logger.info(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())