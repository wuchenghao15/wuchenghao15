#!/usr/bin/env python3
"""
简单测试碎片化临时缓存系统
"""

import os
import sys
import time
import hashlib
import base64
from cryptography.fernet import Fernet

class SimpleFragmentedCache:
    """简单的碎片化临时缓存系统，用于测试核心功能"""
    
    def __init__(self, cache_dir='.cache_test'):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 生成加密密钥
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        print("✅ 简单碎片化临时缓存系统初始化完成")
    
    def _get_cache_file_path(self, cache_key):
        """获取缓存文件路径"""
        key_hash = hashlib.sha256(cache_key.encode()).hexdigest()
        subdir = key_hash[:2]
        subdir_path = os.path.join(self.cache_dir, subdir)
        os.makedirs(subdir_path, exist_ok=True)
        return os.path.join(subdir_path, f"{key_hash}.cache")
    
    def _encrypt_data(self, data):
        """加密数据"""
        import json
        if isinstance(data, dict):
            data_str = json.dumps(data)
        elif isinstance(data, str):
            data_str = data
        else:
            data_str = str(data)
        
        encrypted = self.cipher.encrypt(data_str.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def _decrypt_data(self, encrypted_data):
        """解密数据"""
        import json
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes).decode()
        try:
            return json.loads(decrypted)
        except json.JSONDecodeError:
            return decrypted
    
    def set(self, cache_key, data):
        """设置缓存"""
        try:
            encrypted_data = self._encrypt_data(data)
            cache_file = self._get_cache_file_path(cache_key)
            with open(cache_file, 'w') as f:
                f.write(encrypted_data)
            # 设置文件权限，只有当前用户可访问
            os.chmod(cache_file, 0o600)
            return True
        except Exception as e:
            print(f"❌ 缓存设置失败: {str(e)}")
            return False
    
    def get(self, cache_key):
        """获取缓存"""
        try:
            cache_file = self._get_cache_file_path(cache_key)
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r') as f:
                encrypted_data = f.read()
            
            return self._decrypt_data(encrypted_data)
        except Exception as e:
            print(f"❌ 缓存获取失败: {str(e)}")
            return None
    
    def delete(self, cache_key):
        """删除缓存"""
        try:
            cache_file = self._get_cache_file_path(cache_key)
            if os.path.exists(cache_file):
                os.remove(cache_file)
                return True
            return False
        except Exception as e:
            print(f"❌ 缓存删除失败: {str(e)}")
            return False
    
    def cleanup(self):
        """清理所有缓存文件"""
        try:
            import shutil
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                print(f"✅ 清理缓存目录: {self.cache_dir}")
            return True
        except Exception as e:
            print(f"❌ 清理缓存失败: {str(e)}")
            return False

def test_simple_cache():
    """测试简单的碎片化临时缓存系统"""
    print("=== 测试简单的碎片化临时缓存系统 ===")
    
    # 创建缓存实例
    cache = SimpleFragmentedCache()
    
    # 测试1: 设置缓存
    print("\n1. 测试设置缓存...")
    test_data = {
        "name": "测试数据",
        "value": 123,
        "timestamp": time.time(),
        "details": {
            "status": "active",
            "priority": "high"
        }
    }
    
    success = cache.set("test_key_1", test_data)
    if success:
        print("✅ 缓存设置成功")
    else:
        print("❌ 缓存设置失败")
        return False
    
    # 测试2: 获取缓存
    print("\n2. 测试获取缓存...")
    cached_data = cache.get("test_key_1")
    if cached_data:
        print("✅ 缓存获取成功")
        print(f"   缓存内容: {cached_data}")
    else:
        print("❌ 缓存获取失败")
        return False
    
    # 测试3: 缓存未命中
    print("\n3. 测试缓存未命中...")
    non_existent = cache.get("non_existent_key")
    if non_existent is None:
        print("✅ 缓存未命中处理正常")
    else:
        print("❌ 缓存未命中处理异常")
        return False
    
    # 测试4: 删除缓存
    print("\n4. 测试删除缓存...")
    success = cache.delete("test_key_1")
    if success:
        print("✅ 缓存删除成功")
    else:
        print("❌ 缓存删除失败")
        return False
    
    # 验证缓存已删除
    deleted_data = cache.get("test_key_1")
    if deleted_data is None:
        print("✅ 缓存已成功删除")
    else:
        print("❌ 缓存删除未生效")
        return False
    
    # 测试5: 清理缓存
    print("\n5. 测试清理缓存...")
    success = cache.cleanup()
    if success:
        print("✅ 缓存清理成功")
    else:
        print("❌ 缓存清理失败")
        return False
    
    print("\n=== 简单碎片化临时缓存系统测试完成 ===")
    print("✅ 所有测试通过")
    return True

if __name__ == "__main__":
    success = test_simple_cache()
    sys.exit(0 if success else 1)
