#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库存储功能是否正常工作
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask-app/app'))

from data_storage_manager import storage_manager
from datetime import datetime, timedelta

def test_storage_manager():
    """测试存储管理器"""
    print("="*60)
    print("  测试数据库存储管理器")
    print("="*60)
    
    # 测试存储任务
    print("\n1. 测试任务存储...")
    task_id = storage_manager.store_task('test_task_001', 'test_type', 1, '{"test": "data"}')
    assert task_id == True, "任务存储失败"
    task = storage_manager.get_task('test_task_001')
    assert task is not None, "任务获取失败"
    assert task['task_id'] == 'test_task_001', "任务ID不匹配"
    print("   ✓ 任务存储测试通过")
    
    # 测试配置存储
    print("\n2. 测试配置存储...")
    config_id = storage_manager.store_config('test_config', 'test', 'test_value')
    assert config_id == True, "配置存储失败"
    config = storage_manager.get_config('test_config')
    assert config == 'test_value', "配置获取失败"
    print("   ✓ 配置存储测试通过")
    
    # 测试权限存储
    print("\n3. 测试权限存储...")
    perm_id = storage_manager.store_permission('test_perm_001', 1, 'read,write', (datetime.now() + timedelta(days=1)).isoformat())
    assert perm_id == True, "权限存储失败"
    perm = storage_manager.get_permission('test_perm_001')
    assert perm is not None, "权限获取失败"
    assert perm['user_id'] == 1, "用户ID不匹配"
    print("   ✓ 权限存储测试通过")
    
    # 测试证书存储
    print("\n4. 测试证书存储...")
    cert_id = storage_manager.store_certificate(
        'test_cert_001', 1, 'digital', 'cert_data', 
        'fingerprint_001', 'MTSCOS CA', 
        datetime.now().isoformat(),
        (datetime.now() + timedelta(days=365)).isoformat(),
        'active'
    )
    assert cert_id == True, "证书存储失败"
    cert = storage_manager.get_certificate('test_cert_001')
    assert cert is not None, "证书获取失败"
    assert cert['certificate_type'] == 'digital', "证书类型不匹配"
    print("   ✓ 证书存储测试通过")
    
    # 测试AI能力存储
    print("\n5. 测试AI能力存储...")
    ai_id = storage_manager.store_ai_capability(
        'test_ai_001', 'Test AI', 'test_role', 'Test Description',
        'test_domain', 'active', ['cap1', 'cap2'],
        {'cap1': 'expert', 'cap2': 'intermediate'},
        ['specialty1', 'specialty2'],
        0.95
    )
    assert ai_id == True, "AI能力存储失败"
    ai = storage_manager.get_ai_capability('test_ai_001')
    assert ai is not None, "AI能力获取失败"
    assert ai['name'] == 'Test AI', "AI名称不匹配"
    assert 'cap1' in ai['capabilities'], "能力列表不匹配"
    print("   ✓ AI能力存储测试通过")
    
    # 测试会话存储
    print("\n6. 测试会话存储...")
    sess_id = storage_manager.store_session(
        'test_session_001', 1, 'csrf_token_001', 
        'refresh_token_001', (datetime.now() + timedelta(hours=1)).isoformat()
    )
    assert sess_id == True, "会话存储失败"
    sess = storage_manager.get_session('test_session_001')
    assert sess is not None, "会话获取失败"
    assert sess['user_id'] == 1, "会话用户ID不匹配"
    print("   ✓ 会话存储测试通过")
    
    # 测试键生成
    print("\n7. 测试唯一键生成...")
    key1 = storage_manager.generate_key('test')
    import time
    time.sleep(0.001)  # 确保时间戳不同
    key2 = storage_manager.generate_key('test')
    assert key1 != key2, "键生成不唯一"
    assert key1.startswith('test_'), "键格式不正确"
    print("   ✓ 唯一键生成测试通过")
    
    print("\n" + "="*60)
    print("  所有测试通过！数据库存储功能正常")
    print("="*60)

if __name__ == "__main__":
    test_storage_manager()