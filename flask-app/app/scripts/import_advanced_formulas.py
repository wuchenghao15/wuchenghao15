# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""导入诱导公式和推导公式到数据库"""
import os
import sys
import json
import logging

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_induction_and_derivation_formulas():
    """导入诱导公式和推导公式"""
    from app.services.math_formula_service import formula_service
    
    logger.info("开始导入诱导公式和推导公式...")
    
    # 导入诱导公式
    induction_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'induction_formulas.json')
    if os.path.exists(induction_path):
        logger.info(f"导入诱导公式: {induction_path}")
        induction_count = formula_service.import_formulas_from_json(induction_path)
        logger.info(f"成功导入 {induction_count} 个诱导公式")
    else:
        logger.warning(f"诱导公式文件不存在: {induction_path}")
        induction_count = 0
    
    # 导入推导公式
    derivation_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'derivation_formulas.json')
    if os.path.exists(derivation_path):
        logger.info(f"导入推导公式: {derivation_path}")
        derivation_count = formula_service.import_formulas_from_json(derivation_path)
        logger.info(f"成功导入 {derivation_count} 个推导公式")
    else:
        logger.warning(f"推导公式文件不存在: {derivation_path}")
        derivation_count = 0
    
    # 统计数据库中的公式数量
    total_count = formula_service.get_formula_count()
    induction_total = len(formula_service.search_formulas(formula_type='induction'))
    derivation_total = len(formula_service.search_formulas(formula_type='derivation'))
    basic_total = len(formula_service.search_formulas(formula_type='basic'))
    
    logger.info("=" * 60)
    logger.info("数学公式数据库导入完成")
    logger.info("=" * 60)
    logger.info(f"基础公式: {basic_total} 个")
    logger.info(f"诱导公式: {induction_total} 个")
    logger.info(f"推导公式: {derivation_total} 个")
    logger.info(f"公式总数: {total_count} 个")
    logger.info("=" * 60)
    
    return total_count

if __name__ == '__main__':
    import_induction_and_derivation_formulas()
