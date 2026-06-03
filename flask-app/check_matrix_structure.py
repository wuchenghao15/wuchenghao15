# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据矩阵结构
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.ai.auto_upgrade_test_system import smart_auto_upgrade_test_system


def main():
    print("检查数据矩阵结构...")
    
    # 测试 generate_all_matrices
    print("\n1. 测试 generate_all_matrices...")
    matrices = smart_auto_upgrade_test_system.matrix_generator.generate_all_matrices()
    print(f"   返回类型: {type(matrices)}")
    print(f"   键: {list(matrices.keys())}")
    
    # 测试 get_data_matrices
    print("\n2. 测试 get_data_matrices...")
    result = smart_auto_upgrade_test_system.get_data_matrices()
    print(f"   返回类型: {type(result)}")
    print(f"   键: {list(result.keys())}")
    
    # 测试单个矩阵
    print("\n3. 测试单个矩阵...")
    for matrix_name in ['error_type', 'performance', 'correlation', 'trend', 'heatmap']:
        try:
            matrix = smart_auto_upgrade_test_system.get_data_matrices(matrix_name)
            print(f"   {matrix_name}: {type(matrix)}")
        except Exception as e:
            print(f"   {matrix_name}: 错误 - {str(e)}")
    
    print("\n✓ 结构检查完成")


if __name__ == "__main__":
    main()
