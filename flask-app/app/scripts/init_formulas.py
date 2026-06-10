# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""数学公式数据库初始化脚本"""
import os
import sys
import json
import logging

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_math_formula_database():
    """初始化数学公式数据库"""
    from app.services.math_formula_service import formula_service, init_math_formulas
    
    logger.info("开始初始化数学公式数据库...")
    
    # 初始化分类和标签
    init_math_formulas()
    
    # 导入示例公式
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'math_formulas.json')
    if os.path.exists(json_path):
        logger.info(f"导入示例公式: {json_path}")
        count = formula_service.import_formulas_from_json(json_path)
        logger.info(f"成功导入 {count} 个数学公式")
    else:
        logger.warning(f"示例公式文件不存在: {json_path}")
        logger.info(f"当前目录: {os.getcwd()}")
        logger.info(f"文件列表: {os.listdir('.')}")
    
    # 统计数据库中的公式数量
    total_count = formula_service.get_formula_count()
    categories = formula_service.get_all_categories()
    
    logger.info(f"数学公式数据库初始化完成")
    logger.info(f"公式总数: {total_count}")
    logger.info(f"分类数量: {len(categories)}")
    
    return total_count

if __name__ == '__main__':
    init_math_formula_database()
