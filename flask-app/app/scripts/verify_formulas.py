#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证数学公式导入结果"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app.services.math_formula_service import formula_service

print("=" * 60)
print("数学公式数据库验证")
print("=" * 60)

# 查询诱导公式
induction_formulas = formula_service.search_formulas(formula_type='induction', limit=100)
print(f"\n诱导公式数量: {len(induction_formulas)}")
print("-" * 60)
for i, f in enumerate(induction_formulas, 1):
    print(f"{i}. {f['name']}")
    print(f"   公式: {f['formula']}")
    if f.get('derivation_steps'):
        print(f"   推导步骤: {len(f['derivation_steps'])}步")

# 查询推导公式
derivation_formulas = formula_service.search_formulas(formula_type='derivation', limit=100)
print(f"\n推导公式数量: {len(derivation_formulas)}")
print("-" * 60)
for i, f in enumerate(derivation_formulas, 1):
    print(f"{i}. {f['name']}")
    print(f"   公式: {f['formula']}")
    if f.get('derivation_steps'):
        print(f"   推导步骤: {len(f['derivation_steps'])}步")

# 查询所有公式
all_formulas = formula_service.search_formulas(limit=1000)
print(f"\n总公式数量: {len(all_formulas)}")

# 按类型统计
from collections import Counter
type_count = Counter(f['formula_type'] for f in all_formulas)
print("\n按类型统计:")
for formula_type, count in type_count.items():
    print(f"  {formula_type}: {count}个")

print("\n" + "=" * 60)
print("验证完成!")
print("=" * 60)
