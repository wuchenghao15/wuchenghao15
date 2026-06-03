# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS SDK 使用示例
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mtscos import MTSCOSSDK, SDKConfig


def test_sdk_basic():
    """测试SDK基本功能"""
    print("=" * 70)
    print("测试SDK基本功能")
    print("=" * 70)
    
    # 初始化SDK
    config = SDKConfig(
        base_url="http://localhost:5000",
        debug=True
    )
    sdk = MTSCOSSDK(config)
    
    print(f"\n📦 SDK版本: {sdk.get_version()}")
    print(f"🔗 服务地址: {sdk.config.base_url}")
    
    return True


def test_ai_sdk():
    """测试AI服务SDK"""
    print("\n" + "=" * 70)
    print("测试AI服务SDK")
    print("=" * 70)
    
    config = SDKConfig(base_url="http://localhost:5000")
    sdk = MTSCOSSDK(config)
    
    print("\n🔍 获取数据矩阵...")
    matrices = sdk.ai.get_data_matrices()
    print(f"   ✓ 数据矩阵获取成功")
    
    print("\n🏥 获取系统健康...")
    health = sdk.ai.get_system_health()
    print(f"   ✓ 系统健康获取成功")
    
    print("\n⚠️ 获取异常检测...")
    anomalies = sdk.ai.get_anomalies()
    print(f"   ✓ 异常检测获取成功")
    
    print("\n📊 获取风险预测...")
    risks = sdk.ai.get_risk_predictions()
    print(f"   ✓ 风险预测获取成功")
    
    print("\n📝 获取洞察报告...")
    insights = sdk.ai.get_insights()
    print(f"   ✓ 洞察报告获取成功")
    
    print("\n✓ AI服务SDK测试通过")
    return True


def test_backup_sdk():
    """测试备份系统SDK"""
    print("\n" + "=" * 70)
    print("测试备份系统SDK")
    print("=" * 70)
    
    config = SDKConfig(base_url="http://localhost:5000")
    sdk = MTSCOSSDK(config)
    
    print("\n📊 获取备份系统状态...")
    status = sdk.backup.get_status()
    print(f"   ✓ 状态获取成功")
    
    print("\n📋 列出备份计划...")
    plans = sdk.backup.list_plans()
    print(f"   ✓ 计划列表获取成功")
    
    print("\n✓ 备份系统SDK测试通过")
    return True


def test_certificate_sdk():
    """测试证书管理SDK"""
    print("\n" + "=" * 70)
    print("测试证书管理SDK")
    print("=" * 70)
    
    config = SDKConfig(base_url="http://localhost:5000")
    sdk = MTSCOSSDK(config)
    
    print("\n📊 获取证书系统状态...")
    status = sdk.certificate.get_status()
    print(f"   ✓ 状态获取成功")
    
    print("\n📋 列出证书...")
    certs = sdk.certificate.list_certificates()
    print(f"   ✓ 证书列表获取成功")
    
    print("\n✓ 证书管理SDK测试通过")
    return True


def test_recovery_sdk():
    """测试恢复镜像SDK"""
    print("\n" + "=" * 70)
    print("测试恢复镜像SDK")
    print("=" * 70)
    
    config = SDKConfig(base_url="http://localhost:5000")
    sdk = MTSCOSSDK(config)
    
    print("\n📊 获取恢复系统状态...")
    status = sdk.recovery.get_status()
    print(f"   ✓ 状态获取成功")
    
    print("\n📋 列出镜像...")
    mirrors = sdk.recovery.list_mirrors()
    print(f"   ✓ 镜像列表获取成功")
    
    print("\n✓ 恢复镜像SDK测试通过")
    return True


def test_maintenance_sdk():
    """测试例行维护SDK"""
    print("\n" + "=" * 70)
    print("测试例行维护SDK")
    print("=" * 70)
    
    config = SDKConfig(base_url="http://localhost:5000")
    sdk = MTSCOSSDK(config)
    
    print("\n📊 获取维护状态...")
    status = sdk.maintenance.get_status()
    print(f"   ✓ 状态获取成功")
    
    print("\n📋 获取维护策略...")
    policies = sdk.maintenance.get_policies()
    print(f"   ✓ 策略获取成功")
    
    print("\n✓ 例行维护SDK测试通过")
    return True


def test_integration_sdk():
    """测试系统整合SDK"""
    print("\n" + "=" * 70)
    print("测试系统整合SDK")
    print("=" * 70)
    
    config = SDKConfig(base_url="http://localhost:5000")
    sdk = MTSCOSSDK(config)
    
    print("\n📊 获取整合状态...")
    status = sdk.integration.get_status()
    print(f"   ✓ 状态获取成功")
    
    print("\n📋 获取子系统列表...")
    subsystems = sdk.integration.list_subsystems()
    print(f"   ✓ 子系统列表获取成功")
    
    print("\n✓ 系统整合SDK测试通过")
    return True


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "🚀 MTSCOS AI SDK 测试" + " " * 22 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = []
    
    try:
        # 测试SDK基本功能
        results.append(('SDK基本功能', test_sdk_basic()))
        
        # 测试AI服务SDK
        results.append(('AI服务SDK', test_ai_sdk()))
        
        # 测试备份系统SDK
        results.append(('备份系统SDK', test_backup_sdk()))
        
        # 测试证书管理SDK
        results.append(('证书管理SDK', test_certificate_sdk()))
        
        # 测试恢复镜像SDK
        results.append(('恢复镜像SDK', test_recovery_sdk()))
        
        # 测试例行维护SDK
        results.append(('例行维护SDK', test_maintenance_sdk()))
        
        # 测试系统整合SDK
        results.append(('系统整合SDK', test_integration_sdk()))
        
        # 显示测试结果
        print("\n" + "=" * 70)
        print("测试结果汇总")
        print("=" * 70)
        
        all_passed = True
        for test_name, passed in results:
            status = "✓ 通过" if passed else "✗ 失败"
            print(f"   {test_name}: {status}")
            if not passed:
                all_passed = False
        
        print("\n" + "=" * 70)
        if all_passed:
            print("🎉 所有SDK测试通过!")
        else:
            print("⚠️  部分测试失败")
        print("=" * 70)
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
