#!/usr/bin/env python3
"""
手动升级系统版本
"""

from app.services.version_manager import version_manager

if __name__ == "__main__":
    print("=== 手动升级系统版本 ===")
    print(f"当前版本: {version_manager.get_current_version()}")
    
    # 升级到 1.1.1 版本
    new_version = "1.1.1"
    description = "系统例行维护升级，包含以下改进：\n- 数据库优化和缓存清理\n- 系统性能优化\n- 修复已知问题\n- 提升系统稳定性"
    
    print(f"准备升级到版本: {new_version}")
    print(f"版本描述: {description}")
    
    result = version_manager.upgrade_version(new_version, description)
    
    print(f"\n升级结果: {result['status']}")
    print(f"消息: {result['message']}")
    
    if result['status'] == 'success':
        print(f"\n升级成功！新版本: {result['version']}")
        print(f"版本描述: {result['description']}")
    else:
        print("\n升级失败，请检查日志。")
