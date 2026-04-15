#!/usr/bin/env python3
"""
简化版系统版本升级脚本
不依赖完整的Flask应用程序，直接实现版本升级功能
"""

import json
import os
import re

def get_current_version():
    """获取当前系统版本号"""
    version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VERSION')
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'config.py')
    
    current_versions = {
        'system_version': '1.0.0',
        'internal_version': '1.0.0.0',
        'test_version': '1.0.0-beta',
        'api_version': '1.0'
    }
    
    # 1. 尝试从VERSION文件读取
    if os.path.exists(version_file):
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
                current_versions.update(version_data)
                print(f"📄 从VERSION文件加载版本信息: {current_versions}")
                return current_versions
        except Exception as e:
            print(f"❌ 从VERSION文件加载版本信息失败: {str(e)}")
    
    # 2. 尝试从配置文件中提取版本信息
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 尝试匹配版本号模式
                system_version_match = re.search(r'SYSTEM_VERSION\s*=\s*["\'](.*?)["\']', content)
                if system_version_match:
                    current_versions['system_version'] = system_version_match.group(1)
                
                internal_version_match = re.search(r'INTERNAL_VERSION\s*=\s*["\'](.*?)["\']', content)
                if internal_version_match:
                    current_versions['internal_version'] = internal_version_match.group(1)
                
                test_version_match = re.search(r'TEST_VERSION\s*=\s*["\'](.*?)["\']', content)
                if test_version_match:
                    current_versions['test_version'] = test_version_match.group(1)
                
                print(f"📄 从配置文件提取版本信息: {current_versions}")
                return current_versions
        except Exception as e:
            print(f"❌ 从配置文件提取版本信息失败: {str(e)}")
    
    # 3. 如果都失败，使用默认版本
    print(f"📄 使用默认版本信息: {current_versions}")
    return current_versions

def save_version_file(versions):
    """保存版本信息到VERSION文件"""
    version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VERSION')
    try:
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(versions, f, ensure_ascii=False, indent=2)
        print(f"✅ 版本信息已保存到文件: {version_file}")
        return True
    except Exception as e:
        print(f"❌ 保存版本信息到文件失败: {str(e)}")
        return False

def validate_version_format(version):
    """验证版本号格式"""
    version_pattern = r'^\d+(\.\d+)*(?:-(alpha|beta|rc)\d*)?$'
    return bool(re.match(version_pattern, version))

def upgrade_system_version(current_versions):
    """升级系统版本号"""
    print("📈 开始升级系统版本...")
    
    # 1. 升级系统版本号
    system_version = current_versions['system_version']
    parts = system_version.split('.')
    parts = list(map(int, parts))
    
    # 递增小版本号
    parts[-1] += 1
    new_system_version = '.'.join(map(str, parts))
    
    # 2. 升级内部版本号
    internal_version = current_versions['internal_version']
    internal_parts = internal_version.split('.')
    internal_parts = list(map(int, internal_parts))
    internal_parts[-1] += 1
    new_internal_version = '.'.join(map(str, internal_parts))
    
    # 3. 更新测试版本
    new_test_version = f"{new_system_version}-beta"
    
    # 4. 更新所有版本
    new_versions = {
        'system_version': new_system_version,
        'internal_version': new_internal_version,
        'test_version': new_test_version,
        'api_version': current_versions['api_version']
    }
    
    print(f"🎉 系统版本升级成功！")
    print(f"   系统版本: {current_versions['system_version']} → {new_system_version}")
    print(f"   内部版本: {current_versions['internal_version']} → {new_internal_version}")
    print(f"   测试版本: {current_versions['test_version']} → {new_test_version}")
    
    return new_versions

def main():
    """主函数"""
    print("=" * 80)
    print("简化版系统版本升级脚本")
    print("=" * 80)
    
    try:
        # 1. 获取当前版本
        current_versions = get_current_version()
        
        # 2. 升级系统版本
        new_versions = upgrade_system_version(current_versions)
        
        # 3. 保存新版本到文件
        if save_version_file(new_versions):
            print("\n✅ 系统版本升级完成！")
            print(f"📦 新版本信息: {new_versions}")
            print("💡 建议重启系统以应用所有更改")
        else:
            print("\n❌ 保存新版本失败！")
        
        print("=" * 80)
        return 0
        
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 80)
        return 1

if __name__ == "__main__":
    exit(main())