#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试exam_enhancement_api导入和蓝图注册"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger.info("=" * 60)
logger.info("测试exam_enhancement_api导入")
logger.info("=" * 60)

try:
    # 导入蓝图
    from app.api.exam_enhancement_api import exam_enhancement_api
    logger.info(f"✓ Blueprint导入成功")
    logger.info(f"  - 名称: {exam_enhancement_api.name}")
    logger.info(f"  - URL前缀: {exam_enhancement_api.url_prefix}")
    logger.info(f"  - 注册的函数数: {len(exam_enhancement_api.deferred_functions)}")
    
    # 测试Flask应用注册
    from flask import Flask
    app = Flask(__name__)
    app.register_bluelogger.info(exam_enhancement_api)
    
    logger.info(f"\n✓ Blueprint注册成功")
    logger.info(f"  - Flask应用中的路由数: {len(list(app.url_map.iter_rules()))}")
    
    # 检查路由
    routes = []
    for rule in app.url_map.iter_rules():
        if 'enhanced' in str(rule):
            routes.append(str(rule))
    
    logger.info(f"\n✓ 检查exam_enhanced路由:")
    if routes:
        for route in routes:
            logger.info(f"  - {route}")
        logger.info(f"\n✓ 找到 {len(routes)} 个exam_enhanced路由")
    else:
        logger.info(f"  ✗ 未找到exam_enhanced路由")
    
except Exception as e:
    logger.info(f"✗ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

logger.info("\n" + "=" * 60)
logger.info("测试完成")
logger.info("=" * 60)